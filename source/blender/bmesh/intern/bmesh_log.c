/*
 * ***** BEGIN GPL LICENSE BLOCK *****
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software Foundation,
 * Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#include "MEM_guardedalloc.h"

#include "BLI_utildefines.h"
#include "BLI_ghash.h"
#include "BLI_listbase.h"
#include "BLI_math.h"
#include "BLI_mempool.h"

#include "BKE_customdata.h"

#include "bmesh.h"
#include "bmesh_log.h"
#include "range_tree_c_api.h"

struct BMLogEntry {
	struct BMLogEntry *next, *prev;

	/* The following GHashes map from an element ID to one of the log
	 * types above */

	/* Elements that were in the previous entry, but have been
	 * deleted */
	GHash *deleted_verts;
	GHash *deleted_faces;
	/* Elements that were not in the previous entry, but are in the
	 * result of this entry */
	GHash *added_verts;
	GHash *added_faces;

	/* Vertices whose coordinates, mask value, or hflag have changed */
	GHash *modified_verts;

	BLI_mempool *pool_verts;
	BLI_mempool *pool_faces;

	/* This is only needed for dropping BMLogEntries while still in
	 * dynamic-topology mode, as that should release vert/face IDs
	 * back to the BMLog but no BMLog pointer is available at that
	 * time.
	 *
	 * This field is not guaranteed to be valid, any use of it should
	 * check for NULL. */
	BMLog *log;
};

struct BMLog {
	/* Tree of free IDs */
	struct RangeTreeUInt *unused_ids;

	/* Mapping from unique IDs to vertices and faces
	 *
	 * Each vertex and face in the log gets a unique unsigned integer
	 * assigned. That ID is taken from the set managed by the
	 * unused_ids range tree.
	 *
	 * The ID is needed because element pointers will change as they
	 * are created and deleted.
	 */
	GHash *id_to_elem;
	GHash *elem_to_id;

	/* All BMLogEntrys, ordered from earliest to most recent */
	ListBase entries;

	/* The current log entry from entries list
	 *
	 * If null, then the original mesh from before any of the log
	 * entries is current (i.e. there is nothing left to undo.)
	 *
	 * If equal to the last entry in the entries list, then all log
	 * entries have been applied (i.e. there is nothing left to redo.)
	 */
	BMLogEntry *current_entry;
};

typedef struct {
	float co[3];
	short no[3];
	float mask;
	char hflag;
} BMLogVert;

typedef struct {
	unsigned int v_ids[3];
} BMLogFace;

/************************* Get/set element IDs ************************/

/* Get the vertex's unique ID from the log */
static unsigned int bm_log_vert_id_get(BMLog *log, BMVert *v)
{
	BLI_assert(BLI_ghash_haskey(log->elem_to_id, v));
	return GET_INT_FROM_POINTER(BLI_ghash_lookup(log->elem_to_id, v));
}

/* Set the vertex's unique ID in the log */
static void bm_log_vert_id_set(BMLog *log, BMVert *v, unsigned int id)
{
	void *vid = SET_INT_IN_POINTER(id);
	
	BLI_ghash_assign(log->id_to_elem, vid, v, NULL, NULL);
	BLI_ghash_assign(log->elem_to_id, v, vid, NULL, NULL);
}

/* Get a vertex from its unique ID */
static BMVert *bm_log_vert_from_id(BMLog *log, unsigned int id)
{
	void *key = SET_INT_IN_POINTER(id);
	BLI_assert(BLI_ghash_haskey(log->id_to_elem, key));
	return BLI_ghash_lookup(log->id_to_elem, key);
}

/* Get the face's unique ID from the log */
static unsigned int bm_log_face_id_get(BMLog *log, BMFace *f)
{
	BLI_assert(BLI_ghash_haskey(log->elem_to_id, f));
	return GET_INT_FROM_POINTER(BLI_ghash_lookup(log->elem_to_id, f));
}

/* Set the face's unique ID in the log */
static void bm_log_face_id_set(BMLog *log, BMFace *f, unsigned int id)
{
	void *fid = SET_INT_IN_POINTER(id);

	BLI_ghash_assign(log->id_to_elem, fid, f, NULL, NULL);
	BLI_ghash_assign(log->elem_to_id, f, fid, NULL, NULL);
}

/* Get a face from its unique ID */
static BMFace *bm_log_face_from_id(BMLog *log, unsigned int id)
{
	void *key = SET_INT_IN_POINTER(id);
	BLI_assert(BLI_ghash_haskey(log->id_to_elem, key));
	return BLI_ghash_lookup(log->id_to_elem, key);
}


/************************ BMLogVert / BMLogFace ***********************/

/* Get a vertex's paint-mask value
 *
 * Returns zero if no paint-mask layer is present */
static float vert_mask_get(BMesh *bm, BMVert *v)
{
	float *mask = CustomData_bmesh_get(&bm->vdata, v->head.data, CD_PAINT_MASK);
	BLI_assert((CustomData_has_layer(&bm->vdata, CD_PAINT_MASK) == 0) == (mask == NULL));
	if (mask) {
		return *mask;
	}
	else {
		return 0.0f;
	}
}

/* Set a vertex's paint-mask value
 *
 * Has no effect is no paint-mask layer is present */
static void vert_mask_set(BMesh *bm, BMVert *v, float new_mask)
{
	float *mask = CustomData_bmesh_get(&bm->vdata, v->head.data, CD_PAINT_MASK);
	BLI_assert((CustomData_has_layer(&bm->vdata, CD_PAINT_MASK) == 0) == (mask == NULL));
	if (*mask) {
		*mask = new_mask;
	}
}

/* Update a BMLogVert with data from a BMVert */
static void bm_log_vert_bmvert_copy(BMesh *bm, BMLogVert *lv, BMVert *v)
{
	copy_v3_v3(lv->co, v->co);
	normal_float_to_short_v3(lv->no, v->no);
	lv->mask = vert_mask_get(bm, v);
	lv->hflag = v->head.hflag;
}

/* Allocate and initialize a BMLogVert */
static BMLogVert *bm_log_vert_alloc(BMesh *bm, BMLog *log, BMVert *v)
{
	BMLogEntry *entry = log->current_entry;
	BMLogVert *lv = BLI_mempool_alloc(entry->pool_verts);

	bm_log_vert_bmvert_copy(bm, lv, v);

	return lv;
}

/* Allocate and initialize a BMLogFace */
static BMLogFace *bm_log_face_alloc(BMLog *log, BMFace *f)
{
	BMLogEntry *entry = log->current_entry;
	BMLogFace *lf = BLI_mempool_alloc(entry->pool_faces);
	BMVert *v[3];

	BLI_assert(f->len == 3);

	// BM_iter_as_array(NULL, BM_VERTS_OF_FACE, f, (void **)v, 3);
	BM_face_as_array_vert_tri(f, v);

	lf->v_ids[0] = bm_log_vert_id_get(log, v[0]);
	lf->v_ids[1] = bm_log_vert_id_get(log, v[1]);
	lf->v_ids[2] = bm_log_vert_id_get(log, v[2]);

	return lf;
}


/************************ Helpers for undo/redo ***********************/

static void bm_log_verts_unmake(BMesh *bm, BMLog *log, GHash *verts)
{
	GHashIterator gh_iter;
	GHASH_ITER (gh_iter, verts) {
		void *key = BLI_ghashIterator_getKey(&gh_iter);
		BMLogVert *lv = BLI_ghashIterator_getValue(&gh_iter);
		unsigned int id = GET_INT_FROM_POINTER(key);
		BMVert *v = bm_log_vert_from_id(log, id);

		/* Ensure the log has the final values of the vertex before
		 * deleting it */
		bm_log_vert_bmvert_copy(bm, lv, v);

		BM_vert_kill(bm, v);
	}
}

static void bm_log_faces_unmake(BMesh *bm, BMLog *log, GHash *faces)
{
	GHashIterator gh_iter;
	GHASH_ITER (gh_iter, faces) {
		void *key = BLI_ghashIterator_getKey(&gh_iter);
		unsigned int id = GET_INT_FROM_POINTER(key);
		BMFace *f = bm_log_face_from_id(log, id);
		BMEdge *e_tri[3];
		BMLoop *l_iter;
		int i;

		l_iter = BM_FACE_FIRST_LOOP(f);
		for (i = 0; i < 3; i++, l_iter = l_iter->next) {
			e_tri[i] = l_iter->e;
		}

		/* Remove any unused edges */
		BM_face_kill(bm, f);
		for (i = 0; i < 3; i++) {
			if (BM_edge_is_wire(e_tri[i])) {
				BM_edge_kill(bm, e_tri[i]);
			}
		}
	}
}

static void bm_log_verts_restore(BMesh *bm, BMLog *log, GHash *verts)
{
	GHashIterator gh_iter;
	GHASH_ITER (gh_iter, verts) {
		void *key = BLI_ghashIterator_getKey(&gh_iter);
		BMLogVert *lv = BLI_ghashIterator_getValue(&gh_iter);
		BMVert *v = BM_vert_create(bm, lv->co, NULL, BM_CREATE_NOP);
		v->head.hflag = lv->hflag;
		vert_mask_set(bm, v, lv->mask);
		normal_short_to_float_v3(v->no, lv->no);
		bm_log_vert_id_set(log, v, GET_INT_FROM_POINTER(key));
	}
}

static void bm_log_faces_restore(BMesh *bm, BMLog *log, GHash *faces)
{
	GHashIterator gh_iter;
	GHASH_ITER (gh_iter, faces) {
		void *key = BLI_ghashIterator_getKey(&gh_iter);
		BMLogFace *lf = BLI_ghashIterator_getValue(&gh_iter);
		BMVert *v[3] = {bm_log_vert_from_id(log, lf->v_ids[0]),
		                bm_log_vert_from_id(log, lf->v_ids[1]),
		                bm_log_vert_from_id(log, lf->v_ids[2])};
		BMFace *f;

		f = BM_face_create_quad_tri_v(bm, v, 3, NULL, false);
		bm_log_face_id_set(log, f, GET_INT_FROM_POINTER(key));
	}
}

static void bm_log_vert_values_swap(BMesh *bm, BMLog *log, GHash *verts)
{
	GHashIterator gh_iter;
	GHASH_ITER (gh_iter, verts) {
		void *key = BLI_ghashIterator_getKey(&gh_iter);
		BMLogVert *lv = BLI_ghashIterator_getValue(&gh_iter);
		unsigned int id = GET_INT_FROM_POINTER(key);
		BMVert *v = bm_log_vert_from_id(log, id);
		float mask;
		short normal[3];

		swap_v3_v3(v->co, lv->co);
		copy_v3_v3_short(normal, lv->no);
		normal_float_to_short_v3(lv->no, v->no);
		normal_short_to_float_v3(v->no, normal);
		SWAP(char, v->head.hflag, lv->hflag);
		mask = lv->mask;
		lv->mask = vert_mask_get(bm, v);
		vert_mask_set(bm, v, mask);
	}
}


/**********************************************************************/

/* Assign unique IDs to all vertices and faces already in the BMesh */
static void bm_log_assign_ids(BMesh *bm, BMLog *log)
{
	BMIter iter;
	BMVert *v;
	BMFace *f;

	/* Generate vertex IDs */
	BM_ITER_MESH (v, &iter, bm, BM_VERTS_OF_MESH) {
		unsigned int id = range_tree_uint_take_any(log->unused_ids);
		bm_log_vert_id_set(log, v, id);
	}

	/* Generate face IDs */
	BM_ITER_MESH (f, &iter, bm, BM_FACES_OF_MESH) {
		unsigned int id = range_tree_uint_take_any(log->unused_ids);
		bm_log_face_id_set(log, f, id);
	}
}

/* Allocate an empty log entry */
static BMLogEntry *bm_log_entry_create(void)
{
	BMLogEntry *entry = MEM_callocN(sizeof(BMLogEntry), AT);

	entry->deleted_verts = BLI_ghash_ptr_new(AT);
	entry->deleted_faces = BLI_ghash_ptr_new(AT);
	entry->added_verts = BLI_ghash_ptr_new(AT);
	entry->added_faces = BLI_ghash_ptr_new(AT);
	entry->modified_verts = BLI_ghash_ptr_new(AT);

	entry->pool_verts = BLI_mempool_create(sizeof(BMLogVert), 1, 64, 0);
	entry->pool_faces = BLI_mempool_create(sizeof(BMLogFace), 1, 64, 0);

	return entry;
}

/* Free the data in a log entry
 *
 * Note: does not free the log entry itself */
static void bm_log_entry_free(BMLogEntry *entry)
{
	BLI_ghash_free(entry->deleted_verts, NULL, NULL);
	BLI_ghash_free(entry->deleted_faces, NULL, NULL);
	BLI_ghash_free(entry->added_verts, NULL, NULL);
	BLI_ghash_free(entry->added_faces, NULL, NULL);
	BLI_ghash_free(entry->modified_verts, NULL, NULL);

	BLI_mempool_destroy(entry->pool_verts);
	BLI_mempool_destroy(entry->pool_faces);
}

static void bm_log_id_ghash_retake(RangeTreeUInt *unused_ids, GHash *id_ghash)
{
	GHashIterator gh_iter;

	GHASH_ITER (gh_iter, id_ghash) {
		void *key = BLI_ghashIterator_getKey(&gh_iter);
		unsigned int id = GET_INT_FROM_POINTER(key);

		if (range_tree_uint_has(unused_ids, id)) {
			range_tree_uint_take(unused_ids, id);
		}
	}
}

static int uint_compare(const void *a_v, const void *b_v)
{
	const unsigned int *a = a_v;
	const unsigned int *b = b_v;
	return (*a) < (*b);
}

/* Remap IDs to contiguous indices
 *
 * E.g. if the vertex IDs are (4, 1, 10, 3), the mapping will be:
 *    4 -> 2
 *    1 -> 0
 *   10 -> 3
 *    3 -> 1
 */
static GHash *bm_log_compress_ids_to_indices(unsigned int *ids, int totid)
{
	GHash *map = BLI_ghash_int_new(AT);
	int i;

	qsort(ids, totid, sizeof(*ids), uint_compare);

	for (i = 0; i < totid; i++) {
		void *key = SET_INT_IN_POINTER(ids[i]);
		void *val = SET_INT_IN_POINTER(i);
		BLI_ghash_insert(map, key, val);
	}

	return map;
}

/* Release all ID keys in id_ghash */
static void bm_log_id_ghash_release(BMLog *log, GHash *id_ghash)
{
	GHashIterator gh_iter;

	GHASH_ITER (gh_iter, id_ghash) {
		void *key = BLI_ghashIterator_getKey(&gh_iter);
		unsigned int id = GET_INT_FROM_POINTER(key);
		range_tree_uint_release(log->unused_ids, id);
	}
}

/***************************** Public API *****************************/

/* Allocate, initialize, and assign a new BMLog */
BMLog *BM_log_create(BMesh *bm)
{
	BMLog *log = MEM_callocN(sizeof(*log), AT);

	log->unused_ids = range_tree_uint_alloc(0, (unsigned)-1);
	log->id_to_elem = BLI_ghash_ptr_new(AT);
	log->elem_to_id = BLI_ghash_ptr_new(AT);

	/* Assign IDs to all existing vertices and faces */
	bm_log_assign_ids(bm, log);

	return log;
}

/* Allocate and initialize a new BMLog using existing BMLogEntries
 *
 * The 'entry' should be the last entry in the BMLog. Its prev pointer
 * will be followed back to find the first entry.
 *
 * The unused IDs field of the log will be initialized by taking all
 * keys from all GHashes in the log entry.
 */
BMLog *BM_log_from_existing_entries_create(BMesh *bm, BMLogEntry *entry)
{
	BMLog *log = BM_log_create(bm);

	if (entry->prev)
		log->current_entry = entry;
	else
		log->current_entry = NULL;

	/* Let BMLog manage the entry list again */
	log->entries.first = log->entries.last = entry;

	{
		while (entry->prev) {
			entry = entry->prev;
			log->entries.first = entry;
		}
		entry = log->entries.last;
		while (entry->next) {
			entry = entry->next;
			log->entries.last = entry;
		}
	}

	for (entry = log->entries.first; entry; entry = entry->next) {
		entry->log = log;

		/* Take all used IDs */
		bm_log_id_ghash_retake(log->unused_ids, entry->deleted_verts);
		bm_log_id_ghash_retake(log->unused_ids, entry->deleted_faces);
		bm_log_id_ghash_retake(log->unused_ids, entry->added_verts);
		bm_log_id_ghash_retake(log->unused_ids, entry->added_faces);
		bm_log_id_ghash_retake(log->unused_ids, entry->modified_verts);
	}

	return log;
}

/* Free all the data in a BMLog including the log itself */
void BM_log_free(BMLog *log)
{
	BMLogEntry *entry;

	if (log->unused_ids)
		range_tree_uint_free(log->unused_ids);

	if (log->id_to_elem)
		BLI_ghash_free(log->id_to_elem, NULL, NULL);

	if (log->elem_to_id)
		BLI_ghash_free(log->elem_to_id, NULL, NULL);

	/* Clear the BMLog references within each entry, but do not free
	 * the entries themselves */
	for (entry = log->entries.first; entry; entry = entry->next)
		entry->log = NULL;

	MEM_freeN(log);
}

/* Get the number of log entries */
int BM_log_length(const BMLog *log)
{
	return BLI_countlist(&log->entries);
}

/* Apply a consistent ordering to BMesh vertices */
void BM_log_mesh_elems_reorder(BMesh *bm, BMLog *log)
{
	void *varr;
	void *farr;

	GHash *id_to_idx;

	BMIter bm_iter;
	BMVert *v;
	BMFace *f;

	int i;

	/* Put all vertex IDs into an array */
	i = 0;
	varr = MEM_mallocN(sizeof(int) * bm->totvert, AT);
	BM_ITER_MESH (v, &bm_iter, bm, BM_VERTS_OF_MESH) {
		((unsigned int *)varr)[i++] = bm_log_vert_id_get(log, v);
	}

	/* Put all face IDs into an array */
	i = 0;
	farr = MEM_mallocN(sizeof(int) * bm->totface, AT);
	BM_ITER_MESH (f, &bm_iter, bm, BM_FACES_OF_MESH) {
		((unsigned int *)farr)[i++] = bm_log_face_id_get(log, f);
	}

	/* Create BMVert index remap array */
	id_to_idx = bm_log_compress_ids_to_indices(varr, bm->totvert);
	i = 0;
	BM_ITER_MESH (v, &bm_iter, bm, BM_VERTS_OF_MESH) {
		const unsigned id = bm_log_vert_id_get(log, v);
		const void *key = SET_INT_IN_POINTER(id);
		const void *val = BLI_ghash_lookup(id_to_idx, key);
		((int *)varr)[i++] = GET_INT_FROM_POINTER(val);
	}
	BLI_ghash_free(id_to_idx, NULL, NULL);

	/* Create BMFace index remap array */
	id_to_idx = bm_log_compress_ids_to_indices(farr, bm->totface);
	i = 0;
	BM_ITER_MESH (f, &bm_iter, bm, BM_FACES_OF_MESH) {
		const unsigned id = bm_log_face_id_get(log, f);
		const void *key = SET_INT_IN_POINTER(id);
		const void *val = BLI_ghash_lookup(id_to_idx, key);
		((int *)farr)[i++] = GET_INT_FROM_POINTER(val);
	}
	BLI_ghash_free(id_to_idx, NULL, NULL);

	BM_mesh_remap(bm, varr, NULL, farr);

	MEM_freeN(varr);
	MEM_freeN(farr);
}

/* Start a new log entry and update the log entry list
 *
 * If the log entry list is empty, or if the current log entry is the
 * last entry, the new entry is simply appended to the end.
 *
 * Otherwise, the new entry is added after the current entry and all
 * following entries are deleted.
 *
 * In either case, the new entry is set as the current log entry.
 */
BMLogEntry *BM_log_entry_add(BMLog *log)
{
	BMLogEntry *entry, *next;

	/* Delete any entries after the current one */
	entry = log->current_entry;
	if (entry) {
		for (entry = entry->next; entry; entry = next) {
			next = entry->next;
			bm_log_entry_free(entry);
			BLI_freelinkN(&log->entries, entry);
		}
	}

	/* Create and append the new entry */
	entry = bm_log_entry_create();
	BLI_addtail(&log->entries, entry);
	entry->log = log;
	log->current_entry = entry;

	return entry;
}

/* Remove an entry from the log
 *
 * Uses entry->log as the log. If the log is NULL, the entry will be
 * free'd but not removed from any list, nor shall its IDs be
 * released.
 *
 * This operation is only valid on the first and last entries in the
 * log. Deleting from the middle will assert.
 */
void BM_log_entry_drop(BMLogEntry *entry)
{
	BMLog *log = entry->log;

	if (!log) {
		/* Unlink */
		BLI_assert(!(entry->prev && entry->next));
		if (entry->prev)
			entry->prev->next = NULL;
		else if (entry->next)
			entry->next->prev = NULL;

		bm_log_entry_free(entry);
		MEM_freeN(entry);
		return;
	}

	if (!entry->prev) {
		/* Release IDs of elements that are deleted by this
		 * entry. Since the entry is at the beginning of the undo
		 * stack, and it's being deleted, those elements can never be
		 * restored. Their IDs can go back into the pool. */
		bm_log_id_ghash_release(log, entry->deleted_faces);
		bm_log_id_ghash_release(log, entry->deleted_verts);
	}
	else if (!entry->next) {
		/* Release IDs of elements that are added by this entry. Since
		 * the entry is at the end of the undo stack, and it's being
		 * deleted, those elements can never be restored. Their IDs
		 * can go back into the pool. */
		bm_log_id_ghash_release(log, entry->added_faces);
		bm_log_id_ghash_release(log, entry->added_verts);
	}
	else {
		BLI_assert(!"Cannot drop BMLogEntry from middle");
	}

	if (log->current_entry == entry)
		log->current_entry = entry->prev;

	bm_log_entry_free(entry);
	BLI_freelinkN(&log->entries, entry);
}

/* Undo one BMLogEntry
 *
 * Has no effect if there's nothing left to undo */
void BM_log_undo(BMesh *bm, BMLog *log)
{
	BMLogEntry *entry = log->current_entry;

	if (entry) {
		log->current_entry = entry->prev;

		/* Delete added faces and verts */
		bm_log_faces_unmake(bm, log, entry->added_faces);
		bm_log_verts_unmake(bm, log, entry->added_verts);

		/* Restore deleted verts and faces */
		bm_log_verts_restore(bm, log, entry->deleted_verts);
		bm_log_faces_restore(bm, log, entry->deleted_faces);

		/* Restore vertex coordinates, mask, and hflag */
		bm_log_vert_values_swap(bm, log, entry->modified_verts);
	}
}

/* Redo one BMLogEntry
 *
 * Has no effect if there's nothing left to redo */
void BM_log_redo(BMesh *bm, BMLog *log)
{
	BMLogEntry *entry = log->current_entry;

	if (!entry) {
		/* Currently at the beginning of the undo stack, move to first entry */
		entry = log->entries.first;
	}
	else if (entry && entry->next) {
		/* Move to next undo entry */
		entry = entry->next;
	}
	else {
		/* Currently at the end of the undo stack, nothing left to redo */
		return;
	}

	log->current_entry = entry;

	if (entry) {
		/* Re-delete previously deleted faces and verts */
		bm_log_faces_unmake(bm, log, entry->deleted_faces);
		bm_log_verts_unmake(bm, log, entry->deleted_verts);

		/* Restore previously added verts and faces */
		bm_log_verts_restore(bm, log, entry->added_verts);
		bm_log_faces_restore(bm, log, entry->added_faces);

		/* Restore vertex coordinates, mask, and hflag */
		bm_log_vert_values_swap(bm, log, entry->modified_verts);
	}
}

/* Log a vertex before it is modified
 *
 * Before modifying vertex coordinates, masks, or hflags, call this
 * function to log it's current values. This is better than logging
 * after the coordinates have been modified, because only those
 * vertices that are modified need to have their original values
 * stored.
 *
 * Handles two separate cases:
 *
 * If the vertex was added in the current log entry, update the
 * vertex in the map of added vertices.
 *
 * If the vertex already existed prior to the current log entry, a
 * separate key/value map of modified vertices is used (using the
 * vertex's ID as the key). The values stored in that case are
 * the vertex's original state so that an undo can restore the
 * previous state.
 *
 * On undo, the current vertex state will be swapped with the stored
 * state so that a subsequent redo operation will restore the newer
 * vertex state.
 */
void BM_log_vert_before_modified(BMesh *bm, BMLog *log, BMVert *v)
{
	BMLogEntry *entry = log->current_entry;
	BMLogVert *lv;
	unsigned int v_id = bm_log_vert_id_get(log, v);
	void *key = SET_INT_IN_POINTER(v_id);

	/* Find or create the BMLogVert entry */
	if ((lv = BLI_ghash_lookup(entry->added_verts, key))) {
		bm_log_vert_bmvert_copy(bm, lv, v);
	}
	else if (!BLI_ghash_haskey(entry->modified_verts, key)) {
		lv = bm_log_vert_alloc(bm, log, v);
		BLI_ghash_insert(entry->modified_verts, key, lv);
	}
}

/* Log a new vertex as added to the BMesh
 *
 * The new vertex gets a unique ID assigned. It is then added to a map
 * of added vertices, with the key being its ID and the value
 * containing everything needed to reconstruct that vertex.
 */
void BM_log_vert_added(BMesh *bm, BMLog *log, BMVert *v)
{
	BMLogVert *lv;
	unsigned int v_id = range_tree_uint_take_any(log->unused_ids);
	void *key = SET_INT_IN_POINTER(v_id);

	bm_log_vert_id_set(log, v, v_id);
	lv = bm_log_vert_alloc(bm, log, v);
	BLI_ghash_insert(log->current_entry->added_verts, key, lv);
}

/* Log a new face as added to the BMesh
 *
 * The new face gets a unique ID assigned. It is then added to a map
 * of added faces, with the key being its ID and the value containing
 * everything needed to reconstruct that face.
 */
void BM_log_face_added(BMLog *log, BMFace *f)
{
	BMLogFace *lf;
	unsigned int f_id = range_tree_uint_take_any(log->unused_ids);
	void *key = SET_INT_IN_POINTER(f_id);

	/* Only triangles are supported for now */
	BLI_assert(f->len == 3);

	bm_log_face_id_set(log, f, f_id);
	lf = bm_log_face_alloc(log, f);
	BLI_ghash_insert(log->current_entry->added_faces, key, lf);
}

/* Log a vertex as removed from the BMesh
 *
 * A couple things can happen here:
 * 
 * If the vertex was added as part of the current log entry, then it's
 * deleted and forgotten about entirely. Its unique ID is returned to
 * the unused pool.
 *
 * If the vertex was already part of the BMesh before the current log
 * entry, it is added to a map of deleted vertices, with the key being
 * its ID and the value containing everything needed to reconstruct
 * that vertex.
 *
 * If there's a move record for the vertex, that's used as the
 * vertices original location, then the move record is deleted.
 */
void BM_log_vert_removed(BMesh *bm, BMLog *log, BMVert *v)
{
	BMLogEntry *entry = log->current_entry;
	unsigned int v_id = bm_log_vert_id_get(log, v);
	void *key = SET_INT_IN_POINTER(v_id);

	/* if it has a key, it shouldn't be NULL */
	BLI_assert(!!BLI_ghash_lookup(entry->added_verts, key) ==
	           !!BLI_ghash_haskey(entry->added_verts, key));

	if (BLI_ghash_remove(entry->added_verts, key, NULL, NULL)) {
		range_tree_uint_release(log->unused_ids, v_id);
	}
	else {
		BMLogVert *lv, *lv_mod;

		lv = bm_log_vert_alloc(bm, log, v);
		BLI_ghash_insert(entry->deleted_verts, key, lv);

		/* If the vertex was modified before deletion, ensure that the
		 * original vertex values are stored */
		if ((lv_mod = BLI_ghash_lookup(entry->modified_verts, key))) {
			(*lv) = (*lv_mod);
			BLI_ghash_remove(entry->modified_verts, key, NULL, NULL);
		}
	}
}

/* Log a face as removed from the BMesh
 *
 * A couple things can happen here:
 * 
 * If the face was added as part of the current log entry, then it's
 * deleted and forgotten about entirely. Its unique ID is returned to
 * the unused pool.
 *
 * If the face was already part of the BMesh before the current log
 * entry, it is added to a map of deleted faces, with the key being
 * its ID and the value containing everything needed to reconstruct
 * that face.
 */
void BM_log_face_removed(BMLog *log, BMFace *f)
{
	BMLogEntry *entry = log->current_entry;
	unsigned int f_id = bm_log_face_id_get(log, f);
	void *key = SET_INT_IN_POINTER(f_id);

	/* if it has a key, it shouldn't be NULL */
	BLI_assert(!!BLI_ghash_lookup(entry->added_faces, key) ==
	           !!BLI_ghash_haskey(entry->added_faces, key));

	if (BLI_ghash_remove(entry->added_faces, key, NULL, NULL)) {
		range_tree_uint_release(log->unused_ids, f_id);
	}
	else {
		BMLogFace *lf;

		lf = bm_log_face_alloc(log, f);
		BLI_ghash_insert(entry->deleted_faces, key, lf);
	}
}

/* Log all vertices/faces in the BMesh as added */
void BM_log_all_added(BMesh *bm, BMLog *log)
{
	BMIter bm_iter;
	BMVert *v;
	BMFace *f;

	/* Log all vertices as newly created */
	BM_ITER_MESH (v, &bm_iter, bm, BM_VERTS_OF_MESH) {
		BM_log_vert_added(bm, log, v);
	}

	/* Log all faces as newly created */
	BM_ITER_MESH (f, &bm_iter, bm, BM_FACES_OF_MESH) {
		BM_log_face_added(log, f);
	}
}

/* Log all vertices/faces in the BMesh as removed */
void BM_log_before_all_removed(BMesh *bm, BMLog *log)
{
	BMIter bm_iter;
	BMVert *v;
	BMFace *f;

	/* Log deletion of all faces */
	BM_ITER_MESH (f, &bm_iter, bm, BM_FACES_OF_MESH) {
		BM_log_face_removed(log, f);
	}

	/* Log deletion of all vertices */
	BM_ITER_MESH (v, &bm_iter, bm, BM_VERTS_OF_MESH) {
		BM_log_vert_removed(bm, log, v);
	}
}

/* Get the logged coordinates of a vertex
 *
 * Does not modify the log or the vertex */
const float *BM_log_original_vert_co(BMLog *log, BMVert *v)
{
	BMLogEntry *entry = log->current_entry;
	const BMLogVert *lv;
	unsigned v_id = bm_log_vert_id_get(log, v);
	void *key = SET_INT_IN_POINTER(v_id);

	BLI_assert(entry);

	BLI_assert(BLI_ghash_haskey(entry->modified_verts, key));

	lv = BLI_ghash_lookup(entry->modified_verts, key);
	return lv->co;
}

/* Get the logged normal of a vertex
 *
 * Does not modify the log or the vertex */
const short *BM_log_original_vert_no(BMLog *log, BMVert *v)
{
	BMLogEntry *entry = log->current_entry;
	const BMLogVert *lv;
	unsigned v_id = bm_log_vert_id_get(log, v);
	void *key = SET_INT_IN_POINTER(v_id);

	BLI_assert(entry);

	BLI_assert(BLI_ghash_haskey(entry->modified_verts, key));

	lv = BLI_ghash_lookup(entry->modified_verts, key);
	return lv->no;
}

/* Get the logged mask of a vertex
 *
 * Does not modify the log or the vertex */
float BM_log_original_mask(BMLog *log, BMVert *v)
{
	BMLogEntry *entry = log->current_entry;
	const BMLogVert *lv;
	unsigned v_id = bm_log_vert_id_get(log, v);
	void *key = SET_INT_IN_POINTER(v_id);

	BLI_assert(entry);

	BLI_assert(BLI_ghash_haskey(entry->modified_verts, key));

	lv = BLI_ghash_lookup(entry->modified_verts, key);
	return lv->mask;
}

/************************ Debugging and Testing ***********************/

/* For internal use only (unit testing) */
BMLogEntry *BM_log_current_entry(BMLog *log)
{
	return log->current_entry;
}

/* For internal use only (unit testing) */
RangeTreeUInt *BM_log_unused_ids(BMLog *log)
{
	return log->unused_ids;
}

#if 0
/* Print the list of entries, marking the current one
 *
 * Keep around for debugging */
void bm_log_print(const BMLog *log, const char *description)
{
	const BMLogEntry *entry;
	const char *current = " <-- current";
	int i;

	printf("%s:\n", description);
	printf("    % 2d: [ initial ]%s\n", 0,
		   (!log->current_entry) ? current : "");
	for (entry = log->entries.first, i = 1; entry; entry = entry->next, i++) {
		printf("    % 2d: [%p]%s\n", i, entry,
			   (entry == log->current_entry) ? current : "");
	}
}
#endif

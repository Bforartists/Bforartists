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
#include "BLI_buffer.h"
#include "BLI_ghash.h"
#include "BLI_heap.h"
#include "BLI_math.h"

#include "BKE_ccg.h"
#include "BKE_DerivedMesh.h"
#include "BKE_global.h"
#include "BKE_paint.h"
#include "BKE_pbvh.h"

#include "GPU_buffers.h"

#include "bmesh.h"
#include "pbvh_intern.h"

#include <assert.h>

/****************************** Building ******************************/

/* Update node data after splitting */
static void pbvh_bmesh_node_finalize(PBVH *bvh, int node_index)
{
	GHashIterator gh_iter;
	PBVHNode *n = &bvh->nodes[node_index];

	/* Create vert hash sets */
	n->bm_unique_verts = BLI_gset_ptr_new("bm_unique_verts");
	n->bm_other_verts = BLI_gset_ptr_new("bm_other_verts");

	BB_reset(&n->vb);

	GHASH_ITER (gh_iter, n->bm_faces) {
		BMFace *f = BLI_ghashIterator_getKey(&gh_iter);
		BMLoop *l_iter;
		BMLoop *l_first;
		BMVert *v;
		void *node_val = SET_INT_IN_POINTER(node_index);

		/* Update ownership of faces */
		BLI_ghash_insert(bvh->bm_face_to_node, f, node_val);

		/* Update vertices */
		l_iter = l_first = BM_FACE_FIRST_LOOP(f);
		do {
			v = l_iter->v;
			if (!BLI_gset_haskey(n->bm_unique_verts, v)) {
				if (BLI_ghash_haskey(bvh->bm_vert_to_node, v)) {
					BLI_gset_reinsert(n->bm_other_verts, v, NULL);
				}
				else {
					BLI_gset_insert(n->bm_unique_verts, v);
					BLI_ghash_insert(bvh->bm_vert_to_node, v, node_val);
				}
			}
			/* Update node bounding box */
			BB_expand(&n->vb, v->co);
		} while ((l_iter = l_iter->next) != l_first);
	}

	BLI_assert(n->vb.bmin[0] <= n->vb.bmax[0] &&
	           n->vb.bmin[1] <= n->vb.bmax[1] &&
	           n->vb.bmin[2] <= n->vb.bmax[2]);

	n->orig_vb = n->vb;

	/* Build GPU buffers */
	if (!G.background) {
		int smooth = bvh->flags & PBVH_DYNTOPO_SMOOTH_SHADING;
		n->draw_buffers = GPU_build_bmesh_buffers(smooth);
		n->flag |= PBVH_UpdateDrawBuffers | PBVH_UpdateNormals;
	}
}

/* Recursively split the node if it exceeds the leaf_limit */
static void pbvh_bmesh_node_split(PBVH *bvh, GHash *prim_bbc, int node_index)
{
	GHash *empty, *other;
	GHashIterator gh_iter;
	GSetIterator gs_iter;
	PBVHNode *n, *c1, *c2;
	BB cb;
	float mid;
	int axis, children;

	n = &bvh->nodes[node_index];

	if (BLI_ghash_size(n->bm_faces) <= bvh->leaf_limit) {
		/* Node limit not exceeded */
		pbvh_bmesh_node_finalize(bvh, node_index);
		return;
	}

	/* Calculate bounding box around primitive centroids */
	BB_reset(&cb);
	GHASH_ITER (gh_iter, n->bm_faces) {
		const BMFace *f = BLI_ghashIterator_getKey(&gh_iter);
		const BBC *bbc = BLI_ghash_lookup(prim_bbc, f);

		BB_expand(&cb, bbc->bcentroid);
	}

	/* Find widest axis and its midpoint */
	axis = BB_widest_axis(&cb);
	mid = (cb.bmax[axis] + cb.bmin[axis]) * 0.5f;

	/* Add two new child nodes */
	children = bvh->totnode;
	n->children_offset = children;
	pbvh_grow_nodes(bvh, bvh->totnode + 2);

	/* Array reallocated, update current node pointer */
	n = &bvh->nodes[node_index];

	/* Initialize children */
	c1 = &bvh->nodes[children];
	c2 = &bvh->nodes[children + 1];
	c1->flag |= PBVH_Leaf;
	c2->flag |= PBVH_Leaf;
	c1->bm_faces = BLI_ghash_ptr_new_ex("bm_faces", BLI_ghash_size(n->bm_faces) / 2);
	c2->bm_faces = BLI_ghash_ptr_new_ex("bm_faces", BLI_ghash_size(n->bm_faces) / 2);

	/* Partition the parent node's faces between the two children */
	GHASH_ITER (gh_iter, n->bm_faces) {
		BMFace *f = BLI_ghashIterator_getKey(&gh_iter);
		const BBC *bbc = BLI_ghash_lookup(prim_bbc, f);

		if (bbc->bcentroid[axis] < mid)
			BLI_ghash_insert(c1->bm_faces, f, NULL);
		else
			BLI_ghash_insert(c2->bm_faces, f, NULL);
	}

	/* Enforce at least one primitive in each node */
	empty = NULL;
	if (BLI_ghash_size(c1->bm_faces) == 0) {
		empty = c1->bm_faces;
		other = c2->bm_faces;
	}
	else if (BLI_ghash_size(c2->bm_faces) == 0) {
		empty = c2->bm_faces;
		other = c1->bm_faces;
	}
	if (empty) {
		GHASH_ITER (gh_iter, other) {
			void *key = BLI_ghashIterator_getKey(&gh_iter);
			BLI_ghash_insert(empty, key, NULL);
			BLI_ghash_remove(other, key, NULL, NULL);
			break;
		}
	}
	
	/* Clear this node */

	/* Mark this node's unique verts as unclaimed */
	if (n->bm_unique_verts) {
		GSET_ITER (gs_iter, n->bm_unique_verts) {
			BMVert *v = BLI_gsetIterator_getKey(&gs_iter);
			BLI_ghash_remove(bvh->bm_vert_to_node, v, NULL, NULL);
		}
		BLI_gset_free(n->bm_unique_verts, NULL);
	}

	/* Unclaim faces */
	GHASH_ITER (gh_iter, n->bm_faces) {
		BMFace *f = BLI_ghashIterator_getKey(&gh_iter);
		BLI_ghash_remove(bvh->bm_face_to_node, f, NULL, NULL);
	}
	BLI_ghash_free(n->bm_faces, NULL, NULL);

	if (n->bm_other_verts)
		BLI_gset_free(n->bm_other_verts, NULL);

	if (n->layer_disp)
		MEM_freeN(n->layer_disp);
	
	n->bm_faces = NULL;
	n->bm_unique_verts = NULL;
	n->bm_other_verts = NULL;
	n->layer_disp = NULL;
	
	if (n->draw_buffers) {
		GPU_free_buffers(n->draw_buffers);
		n->draw_buffers = NULL;
	}
	n->flag &= ~PBVH_Leaf;
	
	/* Recurse */
	c1 = c2 = NULL;
	pbvh_bmesh_node_split(bvh, prim_bbc, children);
	pbvh_bmesh_node_split(bvh, prim_bbc, children + 1);

	/* Array maybe reallocated, update current node pointer */
	n = &bvh->nodes[node_index];

	/* Update bounding box */
	BB_reset(&n->vb);
	BB_expand_with_bb(&n->vb, &bvh->nodes[n->children_offset].vb);
	BB_expand_with_bb(&n->vb, &bvh->nodes[n->children_offset + 1].vb);
	n->orig_vb = n->vb;
}

/* Recursively split the node if it exceeds the leaf_limit */
static int pbvh_bmesh_node_limit_ensure(PBVH *bvh, int node_index)
{
	GHash *prim_bbc;
	GHash *bm_faces;
	int bm_faces_size;
	GHashIterator gh_iter;
	BBC *bbc_array;
	unsigned int i;

	bm_faces = bvh->nodes[node_index].bm_faces;
	bm_faces_size = BLI_ghash_size(bm_faces);
	if (bm_faces_size <= bvh->leaf_limit) {
		/* Node limit not exceeded */
		return FALSE;
	}

	/* For each BMFace, store the AABB and AABB centroid */
	prim_bbc = BLI_ghash_ptr_new_ex("prim_bbc", bm_faces_size);
	bbc_array = MEM_callocN(sizeof(BBC) * bm_faces_size, "BBC");

	GHASH_ITER_INDEX (gh_iter, bm_faces, i) {
		BMFace *f = BLI_ghashIterator_getKey(&gh_iter);
		BBC *bbc = &bbc_array[i];
		BMLoop *l_iter;
		BMLoop *l_first;

		BB_reset((BB *)bbc);
		l_iter = l_first = BM_FACE_FIRST_LOOP(f);
		do {
			BB_expand((BB *)bbc, l_iter->v->co);
		} while ((l_iter = l_iter->next) != l_first);
		BBC_update_centroid(bbc);

		BLI_ghash_insert(prim_bbc, f, bbc);
	}

	pbvh_bmesh_node_split(bvh, prim_bbc, node_index);

	BLI_ghash_free(prim_bbc, NULL, NULL);
	MEM_freeN(bbc_array);

	return TRUE;
}

/**********************************************************************/

static PBVHNode *pbvh_bmesh_node_lookup(PBVH *bvh, GHash *map, void *key)
{
	int node_index;

	BLI_assert(BLI_ghash_haskey(map, key));

	node_index = GET_INT_FROM_POINTER(BLI_ghash_lookup(map, key));
	BLI_assert(node_index < bvh->totnode);

	return &bvh->nodes[node_index];
}

static BMVert *pbvh_bmesh_vert_create(PBVH *bvh, int node_index,
                                      const float co[3],
                                      const BMVert *example)
{
	BMVert *v = BM_vert_create(bvh->bm, co, example, BM_CREATE_NOP);
	void *val = SET_INT_IN_POINTER(node_index);

	BLI_assert((bvh->totnode == 1 || node_index) && node_index <= bvh->totnode);

	BLI_gset_insert(bvh->nodes[node_index].bm_unique_verts, v);
	BLI_ghash_insert(bvh->bm_vert_to_node, v, val);

	/* Log the new vertex */
	BM_log_vert_added(bvh->bm, bvh->bm_log, v);

	return v;
}

static BMFace *pbvh_bmesh_face_create(PBVH *bvh, int node_index,
                                      BMVert *v_tri[3], BMEdge *e_tri[3],
                                      const BMFace *f_example)
{
	BMFace *f;
	void *val = SET_INT_IN_POINTER(node_index);

	/* ensure we never add existing face */
	BLI_assert(BM_face_exists(v_tri, 3, NULL) == false);

	f = BM_face_create(bvh->bm, v_tri, e_tri, 3, f_example, BM_CREATE_NOP);

	if (!BLI_ghash_haskey(bvh->bm_face_to_node, f)) {

		BLI_ghash_insert(bvh->nodes[node_index].bm_faces, f, NULL);
		BLI_ghash_insert(bvh->bm_face_to_node, f, val);

		/* Log the new face */
		BM_log_face_added(bvh->bm_log, f);
	}

	return f;
}

/* Return the number of faces in 'node' that use vertex 'v' */
static int pbvh_bmesh_node_vert_use_count(PBVH *bvh, PBVHNode *node, BMVert *v)
{
	BMIter bm_iter;
	BMFace *f;
	int count = 0;

	BM_ITER_ELEM (f, &bm_iter, v, BM_FACES_OF_VERT) {
		PBVHNode *f_node;

		f_node = pbvh_bmesh_node_lookup(bvh, bvh->bm_face_to_node, f);

		if (f_node == node)
			count++;
	}

	return count;
}

/* Return a node that uses vertex 'v' other than its current owner */
static PBVHNode *pbvh_bmesh_vert_other_node_find(PBVH *bvh, BMVert *v)
{
	BMIter bm_iter;
	BMFace *f;
	PBVHNode *current_node;

	current_node = pbvh_bmesh_node_lookup(bvh, bvh->bm_vert_to_node, v);

	BM_ITER_ELEM (f, &bm_iter, v, BM_FACES_OF_VERT) {
		PBVHNode *f_node;

		f_node = pbvh_bmesh_node_lookup(bvh, bvh->bm_face_to_node, f);

		if (f_node != current_node)
			return f_node;
	}

	return NULL;
}

static void pbvh_bmesh_vert_ownership_transfer(PBVH *bvh, PBVHNode *new_owner,
                                               BMVert *v)
{
	PBVHNode *current_owner;

	current_owner = pbvh_bmesh_node_lookup(bvh, bvh->bm_vert_to_node, v);
	BLI_assert(current_owner != new_owner);

	/* Remove current ownership */
	BLI_gset_remove(current_owner->bm_unique_verts, v, NULL);

	/* Set new ownership */
	BLI_ghash_reinsert(bvh->bm_vert_to_node, v,
	                   SET_INT_IN_POINTER(new_owner - bvh->nodes), NULL, NULL);
	BLI_gset_insert(new_owner->bm_unique_verts, v);
	BLI_gset_remove(new_owner->bm_other_verts, v, NULL);
	BLI_assert(!BLI_gset_haskey(new_owner->bm_other_verts, v));
}

static void pbvh_bmesh_vert_remove(PBVH *bvh, BMVert *v)
{
	PBVHNode *v_node;
	BMIter bm_iter;
	BMFace *f;

	BLI_assert(BLI_ghash_haskey(bvh->bm_vert_to_node, v));
	v_node = pbvh_bmesh_node_lookup(bvh, bvh->bm_vert_to_node, v);
	BLI_gset_remove(v_node->bm_unique_verts, v, NULL);
	BLI_ghash_remove(bvh->bm_vert_to_node, v, NULL, NULL);

	/* Have to check each neighboring face's node */
	BM_ITER_ELEM (f, &bm_iter, v, BM_FACES_OF_VERT) {
		PBVHNode *f_node = pbvh_bmesh_node_lookup(bvh, bvh->bm_face_to_node, f);

		/* Remove current ownership */
		/* Should be handled above by vert_to_node removal, leaving just in case - psy-fi */
		//BLI_ghash_remove(f_node->bm_unique_verts, v, NULL, NULL);
		BLI_gset_remove(f_node->bm_other_verts, v, NULL);

		BLI_assert(!BLI_gset_haskey(f_node->bm_unique_verts, v));
		BLI_assert(!BLI_gset_haskey(f_node->bm_other_verts, v));
	}
}

static void pbvh_bmesh_face_remove(PBVH *bvh, BMFace *f)
{
	PBVHNode *f_node;
	BMVert *v;

	BMLoop *l_iter;
	BMLoop *l_first;

	f_node = pbvh_bmesh_node_lookup(bvh, bvh->bm_face_to_node, f);

	/* Check if any of this face's vertices need to be removed
	 * from the node */
	l_iter = l_first = BM_FACE_FIRST_LOOP(f);
	do {
		v = l_iter->v;
		if (pbvh_bmesh_node_vert_use_count(bvh, f_node, v) == 1) {
			if (BLI_gset_haskey(f_node->bm_unique_verts, v)) {
				/* Find a different node that uses 'v' */
				PBVHNode *new_node;

				new_node = pbvh_bmesh_vert_other_node_find(bvh, v);
				BLI_assert(new_node || BM_vert_face_count(v) == 1);

				if (new_node) {
					pbvh_bmesh_vert_ownership_transfer(bvh, new_node, v);
				}
				else {
					BLI_gset_remove(f_node->bm_unique_verts, v, NULL);
					BLI_ghash_remove(bvh->bm_vert_to_node, v, NULL, NULL);
				}
			}
			else {
				/* Remove from other verts */
				BLI_gset_remove(f_node->bm_other_verts, v, NULL);
			}
		}
	} while ((l_iter = l_iter->next) != l_first);

	/* Remove face from node and top level */
	BLI_ghash_remove(f_node->bm_faces, f, NULL, NULL);
	BLI_ghash_remove(bvh->bm_face_to_node, f, NULL, NULL);

	/* Log removed face */
	BM_log_face_removed(bvh->bm_log, f);
}

static void pbvh_bmesh_edge_loops(BLI_Buffer *buf, BMEdge *e)
{
	/* fast-path for most common case where an edge has 2 faces,
	 * no need to iterate twice.
	 * This assumes that the buffer */
	BMLoop **data = buf->data;
	BLI_assert(buf->alloc_count >= 2);
	if (LIKELY(BM_edge_loop_pair(e, &data[0], &data[1]))) {
		buf->count = 2;
	}
	else {
		BLI_buffer_resize(buf, BM_edge_face_count(e));
		BM_iter_as_array(NULL, BM_LOOPS_OF_EDGE, e, buf->data, buf->count);
	}
}

static void pbvh_bmesh_node_drop_orig(PBVHNode *node)
{
	if (node->bm_orco)
		MEM_freeN(node->bm_orco);
	if (node->bm_ortri)
		MEM_freeN(node->bm_ortri);
	node->bm_orco = NULL;
	node->bm_ortri = NULL;
	node->bm_tot_ortri = 0;
}

/****************************** EdgeQueue *****************************/

typedef struct {
	Heap *heap;
	const float *center;
	float radius_squared;
	float limit_len_squared;
} EdgeQueue;

typedef struct {
	EdgeQueue *q;
	BLI_mempool *pool;
	BMesh *bm;
	int cd_vert_mask_offset;
} EdgeQueueContext;

static int edge_queue_tri_in_sphere(const EdgeQueue *q, BMFace *f)
{
	BMVert *v_tri[3];
	float c[3];

	/* Get closest point in triangle to sphere center */
	// BM_iter_as_array(NULL, BM_VERTS_OF_FACE, f, (void **)v_tri, 3);
	BM_face_as_array_vert_tri(f, v_tri);

	closest_on_tri_to_point_v3(c, q->center, v_tri[0]->co, v_tri[1]->co, v_tri[2]->co);

	/* Check if triangle intersects the sphere */
	return ((len_squared_v3v3(q->center, c) <= q->radius_squared));
}

/* Return true if the vertex mask is less than 0.5, false otherwise */
static bool check_mask_half(EdgeQueueContext *eq_ctx, BMVert *v)
{
	return (BM_ELEM_CD_GET_FLOAT(v, eq_ctx->cd_vert_mask_offset) < 0.5f);
}

static void edge_queue_insert(EdgeQueueContext *eq_ctx, BMEdge *e,
                              float priority)
{
	BMVert **pair;

	/* Don't let topology update affect masked vertices. Unlike with
	 * displacements, can't do 50% topology update, so instead set
	 * (arbitrary) cutoff: if both vertices' masks are less than 50%,
	 * topology update can happen. */
	if (check_mask_half(eq_ctx, e->v1) && check_mask_half(eq_ctx, e->v2)) {
		pair = BLI_mempool_alloc(eq_ctx->pool);
		pair[0] = e->v1;
		pair[1] = e->v2;
		BLI_heap_insert(eq_ctx->q->heap, priority, pair);
	}
}

static void long_edge_queue_edge_add(EdgeQueueContext *eq_ctx,
                                     BMEdge *e)
{
	const float len_sq = BM_edge_calc_length_squared(e);
	if (len_sq > eq_ctx->q->limit_len_squared)
		edge_queue_insert(eq_ctx, e, 1.0f / len_sq);
}

static void short_edge_queue_edge_add(EdgeQueueContext *eq_ctx,
                                      BMEdge *e)
{
	const float len_sq = BM_edge_calc_length_squared(e);
	if (len_sq < eq_ctx->q->limit_len_squared)
		edge_queue_insert(eq_ctx, e, len_sq);
}

static void long_edge_queue_face_add(EdgeQueueContext *eq_ctx,
                                     BMFace *f)
{
	if (edge_queue_tri_in_sphere(eq_ctx->q, f)) {
		BMLoop *l_iter;
		BMLoop *l_first;

		/* Check each edge of the face */
		l_iter = l_first = BM_FACE_FIRST_LOOP(f);
		do {
			long_edge_queue_edge_add(eq_ctx, l_iter->e);
		} while ((l_iter = l_iter->next) != l_first);
	}
}

static void short_edge_queue_face_add(EdgeQueueContext *eq_ctx,
                                      BMFace *f)
{
	if (edge_queue_tri_in_sphere(eq_ctx->q, f)) {
		BMLoop *l_iter;
		BMLoop *l_first;

		/* Check each edge of the face */
		l_iter = l_first = BM_FACE_FIRST_LOOP(f);
		do {
			short_edge_queue_edge_add(eq_ctx, l_iter->e);
		} while ((l_iter = l_iter->next) != l_first);
	}
}

/* Create a priority queue containing vertex pairs connected by a long
 * edge as defined by PBVH.bm_max_edge_len.
 *
 * Only nodes marked for topology update are checked, and in those
 * nodes only edges used by a face intersecting the (center, radius)
 * sphere are checked.
 *
 * The highest priority (lowest number) is given to the longest edge.
 */
static void long_edge_queue_create(EdgeQueueContext *eq_ctx,
                                   PBVH *bvh, const float center[3],
                                   float radius)
{
	int n;

	eq_ctx->q->heap = BLI_heap_new();
	eq_ctx->q->center = center;
	eq_ctx->q->radius_squared = radius * radius;
	eq_ctx->q->limit_len_squared = bvh->bm_max_edge_len * bvh->bm_max_edge_len;

	for (n = 0; n < bvh->totnode; n++) {
		PBVHNode *node = &bvh->nodes[n];

		/* Check leaf nodes marked for topology update */
		if ((node->flag & PBVH_Leaf) &&
			(node->flag & PBVH_UpdateTopology))
		{
			GHashIterator gh_iter;

			/* Check each face */
			GHASH_ITER (gh_iter, node->bm_faces) {
				BMFace *f = BLI_ghashIterator_getKey(&gh_iter);

				long_edge_queue_face_add(eq_ctx, f);
			}
		}
	}
}

/* Create a priority queue containing vertex pairs connected by a
 * short edge as defined by PBVH.bm_min_edge_len.
 *
 * Only nodes marked for topology update are checked, and in those
 * nodes only edges used by a face intersecting the (center, radius)
 * sphere are checked.
 *
 * The highest priority (lowest number) is given to the shortest edge.
 */
static void short_edge_queue_create(EdgeQueueContext *eq_ctx,
                                    PBVH *bvh, const float center[3],
                                    float radius)
{
	int n;

	eq_ctx->q->heap = BLI_heap_new();
	eq_ctx->q->center = center;
	eq_ctx->q->radius_squared = radius * radius;
	eq_ctx->q->limit_len_squared = bvh->bm_min_edge_len * bvh->bm_min_edge_len;

	for (n = 0; n < bvh->totnode; n++) {
		PBVHNode *node = &bvh->nodes[n];

		/* Check leaf nodes marked for topology update */
		if ((node->flag & PBVH_Leaf) &&
			(node->flag & PBVH_UpdateTopology))
		{
			GHashIterator gh_iter;

			/* Check each face */
			GHASH_ITER (gh_iter, node->bm_faces) {
				BMFace *f = BLI_ghashIterator_getKey(&gh_iter);

				short_edge_queue_face_add(eq_ctx, f);
			}
		}
	}
}

/*************************** Topology update **************************/

static void bm_edges_from_tri(BMesh *bm, BMVert *v_tri[3], BMEdge *e_tri[3])
{
	e_tri[0] = BM_edge_create(bm, v_tri[0], v_tri[1], NULL, BM_CREATE_NO_DOUBLE);
	e_tri[1] = BM_edge_create(bm, v_tri[1], v_tri[2], NULL, BM_CREATE_NO_DOUBLE);
	e_tri[2] = BM_edge_create(bm, v_tri[2], v_tri[0], NULL, BM_CREATE_NO_DOUBLE);
}

static void pbvh_bmesh_split_edge(EdgeQueueContext *eq_ctx, PBVH *bvh,
                                  BMEdge *e, BLI_Buffer *edge_loops)
{
	BMVert *v_new;
	float mid[3];
	int i, node_index;

	/* Get all faces adjacent to the edge */
	pbvh_bmesh_edge_loops(edge_loops, e);

	/* Create a new vertex in current node at the edge's midpoint */
	mid_v3_v3v3(mid, e->v1->co, e->v2->co);

	node_index = GET_INT_FROM_POINTER(BLI_ghash_lookup(bvh->bm_vert_to_node,
	                                                   e->v1));
	v_new = pbvh_bmesh_vert_create(bvh, node_index, mid, e->v1);

	/* For each face, add two new triangles and delete the original */
	for (i = 0; i < edge_loops->count; i++) {
		BMLoop *l_adj = BLI_buffer_at(edge_loops, BMLoop *, i);
		BMFace *f_adj = l_adj->f;
		BMFace *f_new;
		BMVert *v_opp, *v1, *v2;
		BMVert *v_tri[3];
		BMEdge *e_tri[3];
		void *nip;
		int ni;

		BLI_assert(f_adj->len == 3);
		nip = BLI_ghash_lookup(bvh->bm_face_to_node, f_adj);
		ni = GET_INT_FROM_POINTER(nip);

		/* Ensure node gets redrawn */
		bvh->nodes[ni].flag |= PBVH_UpdateDrawBuffers | PBVH_UpdateNormals;

		/* Find the vertex not in the edge */
		v_opp = l_adj->prev->v;

		/* Get e->v1 and e->v2 in the order they appear in the
		 * existing face so that the new faces' winding orders
		 * match */
		v1 = l_adj->v;
		v2 = l_adj->next->v;

		if (ni != node_index && i == 0)
			pbvh_bmesh_vert_ownership_transfer(bvh, &bvh->nodes[ni], v_new);

		/* Create two new faces */
		v_tri[0] = v1;
		v_tri[1] = v_new;
		v_tri[2] = v_opp;
		bm_edges_from_tri(bvh->bm, v_tri, e_tri);
		f_new = pbvh_bmesh_face_create(bvh, ni, v_tri, e_tri, f_adj);
		long_edge_queue_face_add(eq_ctx, f_new);

		v_tri[0] = v_new;
		v_tri[1] = v2;
		/* v_tri[2] = v_opp; */ /* unchanged */
		e_tri[0] = BM_edge_create(bvh->bm, v_tri[0], v_tri[1], NULL, BM_CREATE_NO_DOUBLE);
		e_tri[2] = e_tri[1];  /* switched */
		e_tri[1] = BM_edge_create(bvh->bm, v_tri[1], v_tri[2], NULL, BM_CREATE_NO_DOUBLE);
		f_new = pbvh_bmesh_face_create(bvh, ni, v_tri, e_tri, f_adj);
		long_edge_queue_face_add(eq_ctx, f_new);

		/* Delete original */
		pbvh_bmesh_face_remove(bvh, f_adj);
		BM_face_kill(bvh->bm, f_adj);

		/* Ensure new vertex is in the node */
		if (!BLI_gset_haskey(bvh->nodes[ni].bm_unique_verts, v_new) &&
			!BLI_gset_haskey(bvh->nodes[ni].bm_other_verts, v_new))
		{
			BLI_gset_insert(bvh->nodes[ni].bm_other_verts, v_new);
		}

		if (BM_vert_edge_count(v_opp) >= 9) {
			BMIter bm_iter;
			BMEdge *e2;

			BM_ITER_ELEM (e2, &bm_iter, v_opp, BM_EDGES_OF_VERT) {
				long_edge_queue_edge_add(eq_ctx, e2);
			}
		}
	}

	BM_edge_kill(bvh->bm, e);
}

static int pbvh_bmesh_subdivide_long_edges(EdgeQueueContext *eq_ctx, PBVH *bvh,
                                           BLI_Buffer *edge_loops)
{
	int any_subdivided = FALSE;

	while (!BLI_heap_is_empty(eq_ctx->q->heap)) {
		BMVert **pair = BLI_heap_popmin(eq_ctx->q->heap);
		BMEdge *e;

		/* Check that the edge still exists */
		if (!(e = BM_edge_exists(pair[0], pair[1]))) {
			BLI_mempool_free(eq_ctx->pool, pair);
			continue;
		}

		BLI_mempool_free(eq_ctx->pool, pair);
		pair = NULL;

		/* Check that the edge's vertices are still in the PBVH. It's
		 * possible that an edge collapse has deleted adjacent faces
		 * and the node has been split, thus leaving wire edges and
		 * associated vertices. */
		if (!BLI_ghash_haskey(bvh->bm_vert_to_node, e->v1) ||
			!BLI_ghash_haskey(bvh->bm_vert_to_node, e->v2))
		{
			continue;
		}

		if (BM_edge_calc_length_squared(e) <= eq_ctx->q->limit_len_squared)
			continue;

		any_subdivided = TRUE;

		pbvh_bmesh_split_edge(eq_ctx, bvh, e, edge_loops);
	}

	return any_subdivided;
}

static void pbvh_bmesh_collapse_edge(PBVH *bvh, BMEdge *e, BMVert *v1,
                                     BMVert *v2, GHash *deleted_verts,
                                     BLI_Buffer *edge_loops,
                                     BLI_Buffer *deleted_faces)
{
	BMIter bm_iter;
	BMFace *f;
	int i;

	/* Get all faces adjacent to the edge */
	pbvh_bmesh_edge_loops(edge_loops, e);

	/* Remove the merge vertex from the PBVH */
	pbvh_bmesh_vert_remove(bvh, v2);

	/* Remove all faces adjacent to the edge */
	for (i = 0; i < edge_loops->count; i++) {
		BMLoop *l_adj = BLI_buffer_at(edge_loops, BMLoop *, i);
		BMFace *f_adj = l_adj->f;

		pbvh_bmesh_face_remove(bvh, f_adj);
		BM_face_kill(bvh->bm, f_adj);
	}

	/* Kill the edge */
	BLI_assert(BM_edge_face_count(e) == 0);
	BM_edge_kill(bvh->bm, e);

	/* For all remaining faces of v2, create a new face that is the
	 * same except it uses v1 instead of v2 */
	/* Note: this could be done with BM_vert_splice(), but that
	 * requires handling other issues like duplicate edges, so doesn't
	 * really buy anything. */
	deleted_faces->count = 0;
	BM_ITER_ELEM (f, &bm_iter, v2, BM_FACES_OF_VERT) {
		BMVert *v_tri[3];
		BMFace *existing_face;
		PBVHNode *n;
		int ni;

		/* Get vertices, replace use of v2 with v1 */
		// BM_iter_as_array(NULL, BM_VERTS_OF_FACE, f, (void **)v_tri, 3);
		BM_face_as_array_vert_tri(f, v_tri);
		for (i = 0; i < 3; i++) {
			if (v_tri[i] == v2) {
				v_tri[i] = v1;
			}
		}

		/* Check if a face using these vertices already exists. If so,
		 * skip adding this face and mark the existing one for
		 * deletion as well. Prevents extraneous "flaps" from being
		 * created. */
		if (BM_face_exists(v_tri, 3, &existing_face)) {
			BLI_assert(existing_face);
			BLI_buffer_append(deleted_faces, BMFace *, existing_face);
		}
		else {
			BMEdge *e_tri[3];
			n = pbvh_bmesh_node_lookup(bvh, bvh->bm_face_to_node, f);
			ni = n - bvh->nodes;
			bm_edges_from_tri(bvh->bm, v_tri, e_tri);
			pbvh_bmesh_face_create(bvh, ni, v_tri, e_tri, f);

			/* Ensure that v1 is in the new face's node */
			if (!BLI_gset_haskey(n->bm_unique_verts, v1) &&
			    !BLI_gset_haskey(n->bm_other_verts,  v1))
			{
				BLI_gset_insert(n->bm_other_verts, v1);
			}
		}

		BLI_buffer_append(deleted_faces, BMFace *, f);
	}

	/* Delete the tagged faces */
	for (i = 0; i < deleted_faces->count; i++) {
		BMFace *f_del = BLI_buffer_at(deleted_faces, BMFace *, i);
		BMLoop *l_iter;
		BMVert *v_tri[3];
		BMEdge *e_tri[3];
		int j;

		/* Get vertices and edges of face */
		BLI_assert(f_del->len == 3);
		l_iter = BM_FACE_FIRST_LOOP(f_del);
		v_tri[0] = l_iter->v; e_tri[0] = l_iter->e; l_iter = l_iter->next;
		v_tri[1] = l_iter->v; e_tri[1] = l_iter->e; l_iter = l_iter->next;
		v_tri[2] = l_iter->v; e_tri[2] = l_iter->e;

		/* Check if any of the face's vertices are now unused, if so
		 * remove them from the PBVH */
		for (j = 0; j < 3; j++) {
			if (v_tri[j] != v2 && BM_vert_face_count(v_tri[j]) == 1) {
				BLI_ghash_insert(deleted_verts, v_tri[j], NULL);
				pbvh_bmesh_vert_remove(bvh, v_tri[j]);
			}
			else {
				v_tri[j] = NULL;
			}
		}

		/* Remove the face */
		pbvh_bmesh_face_remove(bvh, f_del);
		BM_face_kill(bvh->bm, f_del);

		/* Check if any of the face's edges are now unused by any
		 * face, if so delete them */
		for (j = 0; j < 3; j++) {
			if (BM_edge_face_count(e_tri[j]) == 0)
				BM_edge_kill(bvh->bm, e_tri[j]);
		}

		/* Delete unused vertices */
		for (j = 0; j < 3; j++) {
			if (v_tri[j]) {
				BM_log_vert_removed(bvh->bm, bvh->bm_log, v_tri[j]);
				BM_vert_kill(bvh->bm, v_tri[j]);
			}
		}
	}

	/* Move v1 to the midpoint of v1 and v2 (if v1 still exists, it
	 * may have been deleted above) */
	if (!BLI_ghash_haskey(deleted_verts, v1)) {
		BM_log_vert_before_modified(bvh->bm, bvh->bm_log, v1);
		mid_v3_v3v3(v1->co, v1->co, v2->co);
	}

	/* Delete v2 */
	BLI_assert(BM_vert_face_count(v2) == 0);
	BLI_ghash_insert(deleted_verts, v2, NULL);
	BM_log_vert_removed(bvh->bm, bvh->bm_log, v2);
	BM_vert_kill(bvh->bm, v2);
}

static int pbvh_bmesh_collapse_short_edges(EdgeQueueContext *eq_ctx,
                                           PBVH *bvh,
                                           BLI_Buffer *edge_loops,
                                           BLI_Buffer *deleted_faces)
{
	float min_len_squared = bvh->bm_min_edge_len * bvh->bm_min_edge_len;
	GHash *deleted_verts;
	int any_collapsed = FALSE;

	deleted_verts = BLI_ghash_ptr_new("deleted_verts");

	while (!BLI_heap_is_empty(eq_ctx->q->heap)) {
		BMVert **pair = BLI_heap_popmin(eq_ctx->q->heap);
		BMEdge *e;
		BMVert *v1, *v2;

		v1 = pair[0];
		v2 = pair[1];
		BLI_mempool_free(eq_ctx->pool, pair);
		pair = NULL;

		/* Check that the vertices/edge still exist */
		if (BLI_ghash_haskey(deleted_verts, v1) ||
		    BLI_ghash_haskey(deleted_verts, v2) ||
		    !(e = BM_edge_exists(v1, v2)))
		{
			continue;
		}

		/* Check that the edge's vertices are still in the PBVH. It's
		 * possible that an edge collapse has deleted adjacent faces
		 * and the node has been split, thus leaving wire edges and
		 * associated vertices. */
		if (!BLI_ghash_haskey(bvh->bm_vert_to_node, e->v1) ||
			!BLI_ghash_haskey(bvh->bm_vert_to_node, e->v2))
		{
			continue;
		}

		if (BM_edge_calc_length_squared(e) >= min_len_squared)
			continue;

		any_collapsed = TRUE;

		pbvh_bmesh_collapse_edge(bvh, e, v1, v2,
		                         deleted_verts, edge_loops,
		                         deleted_faces);
	}

	BLI_ghash_free(deleted_verts, NULL, NULL);

	return any_collapsed;
}

/************************* Called from pbvh.c *************************/

int pbvh_bmesh_node_raycast(PBVHNode *node, const float ray_start[3],
                            const float ray_normal[3], float *dist,
                            int use_original)
{
	GHashIterator gh_iter;
	int hit = 0;

	if (use_original && node->bm_tot_ortri) {
		int i;
		for (i = 0; i < node->bm_tot_ortri; i++) {
			const int *t = node->bm_ortri[i];
			hit |= ray_face_intersection(ray_start, ray_normal,
			                             node->bm_orco[t[0]],
			                             node->bm_orco[t[1]],
			                             node->bm_orco[t[2]],
			                             NULL, dist);
		}
	}
	else {
		GHASH_ITER (gh_iter, node->bm_faces) {
			BMFace *f = BLI_ghashIterator_getKey(&gh_iter);

			BLI_assert(f->len == 3);
			if (f->len == 3 && !paint_is_bmesh_face_hidden(f)) {
				BMVert *v_tri[3];

				BM_face_as_array_vert_tri(f, v_tri);
				hit |= ray_face_intersection(ray_start, ray_normal,
				                             v_tri[0]->co,
				                             v_tri[1]->co,
				                             v_tri[2]->co,
				                             NULL, dist);
			}
		}
	}

	return hit;
}


void pbvh_bmesh_normals_update(PBVHNode **nodes, int totnode)
{
	int n;

	for (n = 0; n < totnode; n++) {
		PBVHNode *node = nodes[n];

		if (node->flag & PBVH_UpdateNormals) {
			GHashIterator gh_iter;
			GSetIterator gs_iter;

			GHASH_ITER (gh_iter, node->bm_faces) {
				BM_face_normal_update(BLI_ghashIterator_getKey(&gh_iter));
			}
			GSET_ITER (gs_iter, node->bm_unique_verts) {
				BM_vert_normal_update(BLI_gsetIterator_getKey(&gs_iter));
			}
			/* This should be unneeded normally */
			GSET_ITER (gs_iter, node->bm_other_verts) {
				BM_vert_normal_update(BLI_gsetIterator_getKey(&gs_iter));
			}
			node->flag &= ~PBVH_UpdateNormals;
		}
	}
}

/***************************** Public API *****************************/

/* Build a PBVH from a BMesh */
void BKE_pbvh_build_bmesh(PBVH *bvh, BMesh *bm, int smooth_shading,
                          BMLog *log)
{
	BMIter iter;
	BMFace *f;
	PBVHNode *n;
	int node_index = 0;

	bvh->bm = bm;

	BKE_pbvh_bmesh_detail_size_set(bvh, 0.75);

	bvh->type = PBVH_BMESH;
	bvh->bm_face_to_node = BLI_ghash_ptr_new("bm_face_to_node");
	bvh->bm_vert_to_node = BLI_ghash_ptr_new("bm_vert_to_node");
	bvh->bm_log = log;

	/* TODO: choose leaf limit better */
	bvh->leaf_limit = 100;

	if (smooth_shading)
		bvh->flags |= PBVH_DYNTOPO_SMOOTH_SHADING;

	/* Start with all faces in the root node */
	n = bvh->nodes = MEM_callocN(sizeof(PBVHNode), "PBVHNode");
	bvh->totnode = 1;
	n->flag = PBVH_Leaf;
	n->bm_faces = BLI_ghash_ptr_new_ex("bm_faces", bvh->bm->totface);
	BM_ITER_MESH (f, &iter, bvh->bm, BM_FACES_OF_MESH) {
		BLI_ghash_insert(n->bm_faces, f, NULL);
	}

	/* Recursively split the node until it is under the limit; if no
	 * splitting occurs then finalize the existing leaf node */
	if (!pbvh_bmesh_node_limit_ensure(bvh, node_index))
		pbvh_bmesh_node_finalize(bvh, 0);
}

/* Collapse short edges, subdivide long edges */
int BKE_pbvh_bmesh_update_topology(PBVH *bvh, PBVHTopologyUpdateMode mode,
                                   const float center[3], float radius)
{
	/* 2 is enough for edge faces - manifold edge */
	BLI_buffer_declare_static(BMFace *, edge_loops, BLI_BUFFER_NOP, 2);
	BLI_buffer_declare_static(BMFace *, deleted_faces, BLI_BUFFER_NOP, 32);
	const int cd_vert_mask_offset = CustomData_get_offset(&bvh->bm->vdata, CD_PAINT_MASK);

	int modified = FALSE;
	int n;

	if (mode & PBVH_Collapse) {
		EdgeQueue q;
		BLI_mempool *queue_pool = BLI_mempool_create(sizeof(BMVert) * 2,
		                                             128, 128, 0);
		EdgeQueueContext eq_ctx = {&q, queue_pool, bvh->bm, cd_vert_mask_offset};

		short_edge_queue_create(&eq_ctx, bvh, center, radius);
		pbvh_bmesh_collapse_short_edges(&eq_ctx, bvh, &edge_loops,
		                                &deleted_faces);
		BLI_heap_free(q.heap, NULL);
		BLI_mempool_destroy(queue_pool);
	}

	if (mode & PBVH_Subdivide) {
		EdgeQueue q;
		BLI_mempool *queue_pool = BLI_mempool_create(sizeof(BMVert) * 2,
		                                             128, 128, 0);
		EdgeQueueContext eq_ctx = {&q, queue_pool, bvh->bm, cd_vert_mask_offset};

		long_edge_queue_create(&eq_ctx, bvh, center, radius);
		pbvh_bmesh_subdivide_long_edges(&eq_ctx, bvh, &edge_loops);
		BLI_heap_free(q.heap, NULL);
		BLI_mempool_destroy(queue_pool);
	}
	
	/* Unmark nodes */
	for (n = 0; n < bvh->totnode; n++) {
		PBVHNode *node = &bvh->nodes[n];

		if (node->flag & PBVH_Leaf &&
			node->flag & PBVH_UpdateTopology)
		{
			node->flag &= ~PBVH_UpdateTopology;
		}
	}
	BLI_buffer_free(&edge_loops);
	BLI_buffer_free(&deleted_faces);

	return modified;
}

BLI_INLINE void bm_face_as_array_index_tri(BMFace *f, int r_index[3])
{
	BMLoop *l = BM_FACE_FIRST_LOOP(f);

	BLI_assert(f->len == 3);

	r_index[0] = BM_elem_index_get(l->v); l = l->next;
	r_index[1] = BM_elem_index_get(l->v); l = l->next;
	r_index[2] = BM_elem_index_get(l->v);
}

/* In order to perform operations on the original node coordinates
 * (currently just raycast), store the node's triangles and vertices.
 *
 * Skips triangles that are hidden. */
void BKE_pbvh_bmesh_node_save_orig(PBVHNode *node)
{
	GHashIterator gh_iter;
	GSetIterator gs_iter;
	int i, totvert, tottri;

	/* Skip if original coords/triangles are already saved */
	if (node->bm_orco)
		return;

	totvert = (BLI_gset_size(node->bm_unique_verts) +
	           BLI_gset_size(node->bm_other_verts));

	tottri = BLI_ghash_size(node->bm_faces);

	node->bm_orco = MEM_mallocN(sizeof(*node->bm_orco) * totvert, AT);
	node->bm_ortri = MEM_mallocN(sizeof(*node->bm_ortri) * tottri, AT);

	/* Copy out the vertices and assign a temporary index */
	i = 0;
	GSET_ITER (gs_iter, node->bm_unique_verts) {
		BMVert *v = BLI_gsetIterator_getKey(&gs_iter);
		copy_v3_v3(node->bm_orco[i], v->co);
		BM_elem_index_set(v, i); /* set_dirty! */
		i++;
	}
	GSET_ITER (gs_iter, node->bm_other_verts) {
		BMVert *v = BLI_gsetIterator_getKey(&gs_iter);
		copy_v3_v3(node->bm_orco[i], v->co);
		BM_elem_index_set(v, i); /* set_dirty! */
		i++;
	}

	/* Copy the triangles */
	i = 0;
	GHASH_ITER (gh_iter, node->bm_faces) {
		BMFace *f = BLI_ghashIterator_getKey(&gh_iter);

		if (paint_is_bmesh_face_hidden(f))
			continue;

#if 0
		BMIter bm_iter;
		BMVert *v;
		int j = 0;
		BM_ITER_ELEM (v, &bm_iter, f, BM_VERTS_OF_FACE) {
			node->bm_ortri[i][j] = BM_elem_index_get(v);
			j++;
		}
#else
		bm_face_as_array_index_tri(f, node->bm_ortri[i]);
#endif
		i++;
	}
	node->bm_tot_ortri = i;
}

void BKE_pbvh_bmesh_after_stroke(PBVH *bvh)
{
	int i;
	for (i = 0; i < bvh->totnode; i++) {
		PBVHNode *n = &bvh->nodes[i];
		if (n->flag & PBVH_Leaf) {
			/* Free orco/ortri data */
			pbvh_bmesh_node_drop_orig(n);

			/* Recursively split nodes that have gotten too many
			 * elements */
			pbvh_bmesh_node_limit_ensure(bvh, i);
		}
	}
}

void BKE_pbvh_bmesh_detail_size_set(PBVH *bvh, float detail_size)
{
	bvh->bm_max_edge_len = detail_size;
	bvh->bm_min_edge_len = bvh->bm_max_edge_len * 0.4f;
}

void BKE_pbvh_node_mark_topology_update(PBVHNode *node)
{
	node->flag |= PBVH_UpdateTopology;
}

GSet *BKE_pbvh_bmesh_node_unique_verts(PBVHNode *node)
{
	return node->bm_unique_verts;
}

GSet *BKE_pbvh_bmesh_node_other_verts(PBVHNode *node)
{
	return node->bm_other_verts;
}

/****************************** Debugging *****************************/

#if 0
void bli_ghash_duplicate_key_check(GHash *gh)
{
	GHashIterator gh_iter1, gh_iter2;

	GHASH_ITER (gh_iter1, gh) {
		void *key1 = BLI_ghashIterator_getKey(&gh_iter1);
		int dup = -1;

		GHASH_ITER (gh_iter2, gh) {
			void *key2 = BLI_ghashIterator_getKey(&gh_iter2);

			if (key1 == key2) {
				dup++;
				if (dup > 0) {
					BLI_assert(!"duplicate in hash");
				}
			}
		}
	}
}

void bli_gset_duplicate_key_check(GSet *gs)
{
	GSetIterator gs_iter1, gs_iter2;

	GSET_ITER (gs_iter1, gs) {
		void *key1 = BLI_gsetIterator_getKey(&gs_iter1);
		int dup = -1;

		GSET_ITER (gs_iter2, gs) {
			void *key2 = BLI_gsetIterator_getKey(&gs_iter2);

			if (key1 == key2) {
				dup++;
				if (dup > 0) {
					BLI_assert(!"duplicate in hash");
				}
			}
		}
	}
}

void bmesh_print(BMesh *bm)
{
	BMIter iter, siter;
	BMVert *v;
	BMEdge *e;
	BMFace *f;
	BMLoop *l;

	fprintf(stderr, "\nbm=%p, totvert=%d, totedge=%d, "
	        "totloop=%d, totface=%d\n",
	        bm, bm->totvert, bm->totedge,
	        bm->totloop, bm->totface);

	fprintf(stderr, "vertices:\n");
	BM_ITER_MESH (v, &iter, bm, BM_VERTS_OF_MESH) {
		fprintf(stderr, "  %d co=(%.3f %.3f %.3f) oflag=%x\n",
		        BM_elem_index_get(v), v->co[0], v->co[1], v->co[2],
		        v->oflags[bm->stackdepth - 1].f);
	}

	fprintf(stderr, "edges:\n");
	BM_ITER_MESH (e, &iter, bm, BM_EDGES_OF_MESH) {
		fprintf(stderr, "  %d v1=%d, v2=%d, oflag=%x\n",
		        BM_elem_index_get(e),
		        BM_elem_index_get(e->v1),
		        BM_elem_index_get(e->v2),
		        e->oflags[bm->stackdepth - 1].f);
	}

	fprintf(stderr, "faces:\n");
	BM_ITER_MESH (f, &iter, bm, BM_FACES_OF_MESH) {
		fprintf(stderr, "  %d len=%d, oflag=%x\n",
		        BM_elem_index_get(f), f->len,
		        f->oflags[bm->stackdepth - 1].f);

		fprintf(stderr, "    v: ");
		BM_ITER_ELEM(v, &siter, f, BM_VERTS_OF_FACE) {
			fprintf(stderr, "%d ", BM_elem_index_get(v));
		}
		fprintf(stderr, "\n");

		fprintf(stderr, "    e: ");
		BM_ITER_ELEM(e, &siter, f, BM_EDGES_OF_FACE) {
			fprintf(stderr, "%d ", BM_elem_index_get(e));
		}
		fprintf(stderr, "\n");

		fprintf(stderr, "    l: ");
		BM_ITER_ELEM(l, &siter, f, BM_LOOPS_OF_FACE) {
			fprintf(stderr, "%d(v=%d, e=%d) ",
			        BM_elem_index_get(l),
			        BM_elem_index_get(l->v),
			        BM_elem_index_get(l->e));
		}
		fprintf(stderr, "\n");
	}	
}

void pbvh_bmesh_print(PBVH *bvh)
{
	GHashIterator gh_iter;
	GSetIterator gs_iter;
	int n;

	fprintf(stderr, "\npbvh=%p\n", bvh);
	fprintf(stderr, "bm_face_to_node:\n");
	GHASH_ITER (gh_iter, bvh->bm_face_to_node) {
		fprintf(stderr, "  %d -> %d\n",
		        BM_elem_index_get((BMFace *)BLI_ghashIterator_getKey(&gh_iter)),
		        GET_INT_FROM_POINTER(BLI_ghashIterator_getValue(&gh_iter)));
	}

	fprintf(stderr, "bm_vert_to_node:\n");
	GHASH_ITER (gh_iter, bvh->bm_vert_to_node) {
		fprintf(stderr, "  %d -> %d\n",
		        BM_elem_index_get((BMVert *)BLI_ghashIterator_getKey(&gh_iter)),
		        GET_INT_FROM_POINTER(BLI_ghashIterator_getValue(&gh_iter)));
	}

	for (n = 0; n < bvh->totnode; n++) {
		PBVHNode *node = &bvh->nodes[n];
		if (!(node->flag & PBVH_Leaf))
			continue;

		fprintf(stderr, "node %d\n  faces:\n", n);
		GHASH_ITER (gh_iter, node->bm_faces)
			fprintf(stderr, "    %d\n",
			        BM_elem_index_get((BMFace *)BLI_ghashIterator_getKey(&gh_iter)));
		fprintf(stderr, "  unique verts:\n");
		GSET_ITER (gs_iter, node->bm_unique_verts)
			fprintf(stderr, "    %d\n",
			        BM_elem_index_get((BMVert *)BLI_gsetIterator_getKey(&gs_iter)));
		fprintf(stderr, "  other verts:\n");
		GSET_ITER (gs_iter, node->bm_other_verts)
			fprintf(stderr, "    %d\n",
			        BM_elem_index_get((BMVert *)BLI_gsetIterator_getKey(&gs_iter)));
	}
}

void print_flag_factors(int flag)
{
	int i;
	printf("flag=0x%x:\n", flag);
	for (i = 0; i < 32; i++) {
		if (flag & (1 << i)) {
			printf("  %d (1 << %d)\n", 1 << i, i);
		}
	}
}

void pbvh_bmesh_verify(PBVH *bvh)
{
	GHashIterator gh_iter;
	GSetIterator gs_iter;
	int i, vert_count = 0;
	BMIter iter;
	BMVert *vi;

	/* Check faces */
	BLI_assert(bvh->bm->totface == BLI_ghash_size(bvh->bm_face_to_node));
	GHASH_ITER (gh_iter, bvh->bm_face_to_node) {
		BMIter bm_iter;
		BMVert *v;
		BMFace *f = BLI_ghashIterator_getKey(&gh_iter);
		void *nip = BLI_ghashIterator_getValue(&gh_iter);
		int ni = GET_INT_FROM_POINTER(nip);
		PBVHNode *n = &bvh->nodes[ni];

		/* Check that the face's node is a leaf */
		BLI_assert(n->flag & PBVH_Leaf);

		/* Check that the face's node knows it owns the face */
		BLI_assert(BLI_ghash_haskey(n->bm_faces, f));

		/* Check the face's vertices... */
		BM_ITER_ELEM (v, &bm_iter, f, BM_VERTS_OF_FACE) {
			PBVHNode *nv;

			/* Check that the vertex is in the node */
			BLI_assert(BLI_gset_haskey(n->bm_unique_verts, v) ^
			           BLI_gset_haskey(n->bm_other_verts, v));

			/* Check that the vertex has a node owner */
			nv = pbvh_bmesh_node_lookup(bvh, bvh->bm_vert_to_node, v);

			/* Check that the vertex's node knows it owns the vert */
			BLI_assert(BLI_gset_haskey(nv->bm_unique_verts, v));

			/* Check that the vertex isn't duplicated as an 'other' vert */
			BLI_assert(!BLI_gset_haskey(nv->bm_other_verts, v));
		}
	}

	/* Check verts */
	BLI_assert(bvh->bm->totvert == BLI_ghash_size(bvh->bm_vert_to_node));
	GHASH_ITER (gh_iter, bvh->bm_vert_to_node) {
		BMIter bm_iter;
		BMVert *v = BLI_ghashIterator_getKey(&gh_iter);
		BMFace *f;
		void *nip = BLI_ghashIterator_getValue(&gh_iter);
		int ni = GET_INT_FROM_POINTER(nip);
		PBVHNode *n = &bvh->nodes[ni];
		int found;

		/* Check that the vert's node is a leaf */
		BLI_assert(n->flag & PBVH_Leaf);

		/* Check that the vert's node knows it owns the vert */
		BLI_assert(BLI_gset_haskey(n->bm_unique_verts, v));

		/* Check that the vertex isn't duplicated as an 'other' vert */
		BLI_assert(!BLI_gset_haskey(n->bm_other_verts, v));

		/* Check that the vert's node also contains one of the vert's
		 * adjacent faces */
		BM_ITER_ELEM (f, &bm_iter, v, BM_FACES_OF_VERT) {
			if (BLI_ghash_lookup(bvh->bm_face_to_node, f) == nip) {
				found = TRUE;
				break;
			}
		}
		BLI_assert(found);

		#if 1
		/* total freak stuff, check if node exists somewhere else */
		/* Slow */
		for (i = 0; i < bvh->totnode; i++) {
			PBVHNode *n = &bvh->nodes[i];
			if (i != ni && n->bm_unique_verts)
				BLI_assert(!BLI_gset_haskey(n->bm_unique_verts, v));
		}

		#endif
	}

	#if 0
	/* check that every vert belongs somewhere */
	/* Slow */
	BM_ITER_MESH (vi, &iter, bvh->bm, BM_VERTS_OF_MESH) {
		bool has_unique = false;
		for (i = 0; i < bvh->totnode; i++) {
			PBVHNode *n = &bvh->nodes[i];
			if ((n->bm_unique_verts != NULL) && BLI_gset_haskey(n->bm_unique_verts, vi))
				has_unique = true;
		}
		BLI_assert(has_unique);
		vert_count++;
	}

	/* if totvert differs from number of verts inside the hash. hash-totvert is checked above  */
	BLI_assert(vert_count == bvh->bm->totvert);
	#endif

	/* Check that node elements are recorded in the top level */
	for (i = 0; i < bvh->totnode; i++) {
		PBVHNode *n = &bvh->nodes[i];
		if (n->flag & PBVH_Leaf) {
			/* Check for duplicate entries */
			/* Slow */
			#if 0
			bli_ghash_duplicate_key_check(n->bm_faces);
			bli_gset_duplicate_key_check(n->bm_unique_verts);
			bli_gset_duplicate_key_check(n->bm_other_verts);
			#endif

			GHASH_ITER (gh_iter, n->bm_faces) {
				BMFace *f = BLI_ghashIterator_getKey(&gh_iter);
				void *nip = BLI_ghash_lookup(bvh->bm_face_to_node, f);
				BLI_assert(BLI_ghash_haskey(bvh->bm_face_to_node, f));
				BLI_assert(GET_INT_FROM_POINTER(nip) == (n - bvh->nodes));
			}

			GSET_ITER (gs_iter, n->bm_unique_verts) {
				BMVert *v = BLI_gsetIterator_getKey(&gs_iter);
				void *nip = BLI_ghash_lookup(bvh->bm_vert_to_node, v);
				BLI_assert(BLI_ghash_haskey(bvh->bm_vert_to_node, v));
				BLI_assert(!BLI_gset_haskey(n->bm_other_verts, v));
				BLI_assert(GET_INT_FROM_POINTER(nip) == (n - bvh->nodes));
			}

			GSET_ITER (gs_iter, n->bm_other_verts) {
				BMVert *v = BLI_gsetIterator_getKey(&gs_iter);
				BLI_assert(BLI_ghash_haskey(bvh->bm_vert_to_node, v));
				BLI_assert(BM_vert_face_count(v) > 0);
			}
		}
	}
}

#endif

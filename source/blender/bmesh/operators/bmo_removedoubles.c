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
 * Contributor(s): Joseph Eagar.
 *
 * ***** END GPL LICENSE BLOCK *****
 */

/** \file blender/bmesh/operators/bmo_removedoubles.c
 *  \ingroup bmesh
 */

#include "MEM_guardedalloc.h"

#include "BLI_math.h"
#include "BLI_array.h"

#include "BKE_customdata.h"

#include "bmesh.h"
#include "intern/bmesh_private.h"

#include "intern/bmesh_operators_private.h" /* own include */

static void remdoubles_splitface(BMFace *f, BMesh *bm, BMOperator *op, BMOpSlot *slot_targetmap)
{
	BMIter liter;
	BMLoop *l;
	BMVert *v2, *doub;
	int split = FALSE;

	BM_ITER_ELEM (l, &liter, f, BM_LOOPS_OF_FACE) {
		v2 = BMO_slot_map_elem_get(slot_targetmap, l->v);
		/* ok: if v2 is NULL (e.g. not in the map) then it's
		 *     a target vert, otherwise it's a double */
		if ((v2 && BM_vert_in_face(f, v2)) &&
		    (v2 != l->prev->v) &&
		    (v2 != l->next->v))
		{
			doub = l->v;
			split = TRUE;
			break;
		}
	}

	if (split && doub != v2) {
		BMLoop *nl;
		BMFace *f2 = BM_face_split(bm, f, doub, v2, &nl, NULL, FALSE);

		remdoubles_splitface(f, bm, op, slot_targetmap);
		remdoubles_splitface(f2, bm, op, slot_targetmap);
	}
}

#define ELE_DEL		1
#define EDGE_COL	2
#define FACE_MARK	2

#if 0
int remdoubles_face_overlaps(BMesh *bm, BMVert **varr,
                             int len, BMFace *exclude,
                             BMFace **overlapface)
{
	BMIter vertfaces;
	BMFace *f;
	int i, amount;

	if (overlapface) *overlapface = NULL;

	for (i = 0; i < len; i++) {
		f = BM_iter_new(&vertfaces, bm, BM_FACES_OF_VERT, varr[i]);
		while (f) {
			amount = BM_verts_in_face(bm, f, varr, len);
			if (amount >= len) {
				if (overlapface) *overlapface = f;
				return TRUE;
			}
			f = BM_iter_step(&vertfaces);
		}
	}
	return FALSE;
}
#endif

void bmo_weld_verts_exec(BMesh *bm, BMOperator *op)
{
	BMIter iter, liter;
	BMVert *v, *v2;
	BMEdge *e, *e2, **edges = NULL;
	BLI_array_declare(edges);
	BMLoop *l, *l2, **loops = NULL;
	BLI_array_declare(loops);
	BMFace *f, *f2;
	int a, b;
	BMOpSlot *slot_targetmap = BMO_slot_get(op->slots_in, "targetmap");

	/* mark merge verts for deletion */
	BM_ITER_MESH (v, &iter, bm, BM_VERTS_OF_MESH) {
		if ((v2 = BMO_slot_map_elem_get(slot_targetmap, v))) {
			BMO_elem_flag_enable(bm, v, ELE_DEL);

			/* merge the vertex flags, else we get randomly selected/unselected verts */
			BM_elem_flag_merge(v, v2);
		}
	}

	/* check if any faces are getting their own corners merged
	 * together, split face if so */
	BM_ITER_MESH (f, &iter, bm, BM_FACES_OF_MESH) {
		remdoubles_splitface(f, bm, op, slot_targetmap);
	}

	BM_ITER_MESH (e, &iter, bm, BM_EDGES_OF_MESH) {
		if (BMO_elem_flag_test(bm, e->v1, ELE_DEL) || BMO_elem_flag_test(bm, e->v2, ELE_DEL)) {
			v  = BMO_slot_map_elem_get(slot_targetmap, e->v1);
			v2 = BMO_slot_map_elem_get(slot_targetmap, e->v2);
			
			if (!v) v = e->v1;
			if (!v2) v2 = e->v2;

			if (v == v2) {
				BMO_elem_flag_enable(bm, e, EDGE_COL);
			}
			else if (!BM_edge_exists(v, v2)) {
				BM_edge_create(bm, v, v2, e, BM_CREATE_NO_DOUBLE);
			}

			BMO_elem_flag_enable(bm, e, ELE_DEL);
		}
	}

	/* BMESH_TODO, stop abusing face index here */
	BM_ITER_MESH (f, &iter, bm, BM_FACES_OF_MESH) {
		BM_elem_index_set(f, 0); /* set_dirty! */
		BM_ITER_ELEM (l, &liter, f, BM_LOOPS_OF_FACE) {
			if (BMO_elem_flag_test(bm, l->v, ELE_DEL)) {
				BMO_elem_flag_enable(bm, f, FACE_MARK | ELE_DEL);
			}
			if (BMO_elem_flag_test(bm, l->e, EDGE_COL)) {
				BM_elem_index_set(f, BM_elem_index_get(f) + 1); /* set_dirty! */
			}
		}
	}
	bm->elem_index_dirty |= BM_FACE;

	/* faces get "modified" by creating new faces here, then at the
	 * end the old faces are deleted */
	BM_ITER_MESH (f, &iter, bm, BM_FACES_OF_MESH) {
		if (!BMO_elem_flag_test(bm, f, FACE_MARK))
			continue;

		if (f->len - BM_elem_index_get(f) < 3) {
			BMO_elem_flag_enable(bm, f, ELE_DEL);
			continue;
		}

		BLI_array_empty(edges);
		BLI_array_empty(loops);
		a = 0;
		BM_ITER_ELEM (l, &liter, f, BM_LOOPS_OF_FACE) {
			v = l->v;
			v2 = l->next->v;
			if (BMO_elem_flag_test(bm, v, ELE_DEL)) {
				v = BMO_slot_map_elem_get(slot_targetmap, v);
			}
			if (BMO_elem_flag_test(bm, v2, ELE_DEL)) {
				v2 = BMO_slot_map_elem_get(slot_targetmap, v2);
			}
			
			e2 = v != v2 ? BM_edge_exists(v, v2) : NULL;
			if (e2) {
				for (b = 0; b < a; b++) {
					if (edges[b] == e2) {
						break;
					}
				}
				if (b != a) {
					continue;
				}

				BLI_array_grow_one(edges);
				BLI_array_grow_one(loops);

				edges[a] = e2;
				loops[a] = l;

				a++;
			}
		}
		
		if (BLI_array_count(loops) < 3)
			continue;
		v = loops[0]->v;
		v2 = loops[1]->v;

		if (BMO_elem_flag_test(bm, v, ELE_DEL)) {
			v = BMO_slot_map_elem_get(slot_targetmap, v);
		}
		if (BMO_elem_flag_test(bm, v2, ELE_DEL)) {
			v2 = BMO_slot_map_elem_get(slot_targetmap, v2);
		}
		
		f2 = BM_face_create_ngon(bm, v, v2, edges, a, BM_CREATE_NO_DOUBLE);
		if (f2 && (f2 != f)) {
			BM_elem_attrs_copy(bm, bm, f, f2);

			a = 0;
			BM_ITER_ELEM (l, &liter, f2, BM_LOOPS_OF_FACE) {
				l2 = loops[a];
				BM_elem_attrs_copy(bm, bm, l2, l);

				a++;
			}
		}
	}

	BMO_op_callf(bm, op->flag, "delete geom=%fvef context=%i", ELE_DEL, DEL_ONLYTAGGED);

	BLI_array_free(edges);
	BLI_array_free(loops);
}

static int vergaverco(const void *e1, const void *e2)
{
	const BMVert *v1 = *(void **)e1, *v2 = *(void **)e2;
	float x1 = v1->co[0] + v1->co[1] + v1->co[2];
	float x2 = v2->co[0] + v2->co[1] + v2->co[2];

	if      (x1 > x2) return  1;
	else if (x1 < x2) return -1;
	else return 0;
}

// #define VERT_TESTED	1 // UNUSED
#define VERT_DOUBLE	2
#define VERT_TARGET	4
#define VERT_KEEP	8
// #define VERT_MARK	16 // UNUSED
#define VERT_IN		32

#define EDGE_MARK	1

void bmo_pointmerge_facedata_exec(BMesh *bm, BMOperator *op)
{
	BMOIter siter;
	BMIter iter;
	BMVert *v, *vert_snap;
	BMLoop *l, *firstl = NULL;
	float fac;
	int i, tot;

	vert_snap = BMO_slot_buffer_get_single(BMO_slot_get(op->slots_in, "vert_snap"));
	tot = BM_vert_face_count(vert_snap);

	if (!tot)
		return;

	fac = 1.0f / tot;
	BM_ITER_ELEM (l, &iter, vert_snap, BM_LOOPS_OF_VERT) {
		if (!firstl) {
			firstl = l;
		}
		
		for (i = 0; i < bm->ldata.totlayer; i++) {
			if (CustomData_layer_has_math(&bm->ldata, i)) {
				int type = bm->ldata.layers[i].type;
				void *e1, *e2;

				e1 = CustomData_bmesh_get_layer_n(&bm->ldata, firstl->head.data, i);
				e2 = CustomData_bmesh_get_layer_n(&bm->ldata, l->head.data, i);
				
				CustomData_data_multiply(type, e2, fac);

				if (l != firstl)
					CustomData_data_add(type, e1, e2);
			}
		}
	}

	BMO_ITER (v, &siter, op->slots_in, "verts", BM_VERT) {
		BM_ITER_ELEM (l, &iter, v, BM_LOOPS_OF_VERT) {
			if (l == firstl) {
				continue;
			}

			CustomData_bmesh_copy_data(&bm->ldata, &bm->ldata, firstl->head.data, &l->head.data);
		}
	}
}

void bmo_average_vert_facedata_exec(BMesh *bm, BMOperator *op)
{
	BMOIter siter;
	BMIter iter;
	BMVert *v;
	BMLoop *l /* , *firstl = NULL */;
	CDBlockBytes min, max;
	void *block;
	int i, type;

	for (i = 0; i < bm->ldata.totlayer; i++) {
		if (!CustomData_layer_has_math(&bm->ldata, i))
			continue;
		
		type = bm->ldata.layers[i].type;
		CustomData_data_initminmax(type, &min, &max);

		BMO_ITER (v, &siter, op->slots_in, "verts", BM_VERT) {
			BM_ITER_ELEM (l, &iter, v, BM_LOOPS_OF_VERT) {
				block = CustomData_bmesh_get_layer_n(&bm->ldata, l->head.data, i);
				CustomData_data_dominmax(type, block, &min, &max);
			}
		}

		CustomData_data_multiply(type, &min, 0.5f);
		CustomData_data_multiply(type, &max, 0.5f);
		CustomData_data_add(type, &min, &max);

		BMO_ITER (v, &siter, op->slots_in, "verts", BM_VERT) {
			BM_ITER_ELEM (l, &iter, v, BM_LOOPS_OF_VERT) {
				block = CustomData_bmesh_get_layer_n(&bm->ldata, l->head.data, i);
				CustomData_data_copy_value(type, &min, block);
			}
		}
	}
}

void bmo_pointmerge_exec(BMesh *bm, BMOperator *op)
{
	BMOperator weldop;
	BMOIter siter;
	BMVert *v, *vert_snap = NULL;
	float vec[3];
	BMOpSlot *slot_targetmap;
	
	BMO_slot_vec_get(op->slots_in, "merge_co", vec);

	//BMO_op_callf(bm, op->flag, "collapse_uvs edges=%s", op, "edges");
	BMO_op_init(bm, &weldop, op->flag, "weld_verts");

	slot_targetmap = BMO_slot_get(weldop.slots_in, "targetmap");

	BMO_ITER (v, &siter, op->slots_in, "verts", BM_VERT) {
		if (!vert_snap) {
			vert_snap = v;
			copy_v3_v3(vert_snap->co, vec);
		}
		else {
			BMO_slot_map_elem_insert(&weldop, slot_targetmap, v, vert_snap);
		}
	}

	BMO_op_exec(bm, &weldop);
	BMO_op_finish(bm, &weldop);
}

void bmo_collapse_exec(BMesh *bm, BMOperator *op)
{
	BMOperator weldop;
	BMWalker walker;
	BMIter iter;
	BMEdge *e, **edges = NULL;
	BLI_array_declare(edges);
	float min[3], max[3], center[3];
	int i, tot;
	BMOpSlot *slot_targetmap;
	
	BMO_op_callf(bm, op->flag, "collapse_uvs edges=%s", op, "edges");
	BMO_op_init(bm, &weldop, op->flag, "weld_verts");
	slot_targetmap = BMO_slot_get(weldop.slots_in, "targetmap");

	BMO_slot_buffer_flag_enable(bm, op->slots_in, "edges", BM_EDGE, EDGE_MARK);

	BMW_init(&walker, bm, BMW_SHELL,
	         BMW_MASK_NOP, EDGE_MARK, BMW_MASK_NOP,
	         BMW_FLAG_NOP, /* no need to use BMW_FLAG_TEST_HIDDEN, already marked data */
	         BMW_NIL_LAY);

	BM_ITER_MESH (e, &iter, bm, BM_EDGES_OF_MESH) {
		if (!BMO_elem_flag_test(bm, e, EDGE_MARK))
			continue;

		BLI_array_empty(edges);

		INIT_MINMAX(min, max);
		for (e = BMW_begin(&walker, e->v1), tot = 0; e; e = BMW_step(&walker), tot++) {
			BLI_array_grow_one(edges);
			edges[tot] = e;

			minmax_v3v3_v3(min, max, e->v1->co);
			minmax_v3v3_v3(min, max, e->v2->co);
		}

		mid_v3_v3v3(center, min, max);

		/* snap edges to a point.  for initial testing purposes anyway */
		for (i = 0; i < tot; i++) {
			copy_v3_v3(edges[i]->v1->co, center);
			copy_v3_v3(edges[i]->v2->co, center);
			
			if (edges[i]->v1 != edges[0]->v1)
				BMO_slot_map_elem_insert(&weldop, slot_targetmap, edges[i]->v1, edges[0]->v1);
			if (edges[i]->v2 != edges[0]->v1)
				BMO_slot_map_elem_insert(&weldop, slot_targetmap, edges[i]->v2, edges[0]->v1);
		}
	}
	
	BMO_op_exec(bm, &weldop);
	BMO_op_finish(bm, &weldop);

	BMW_end(&walker);
	BLI_array_free(edges);
}

/* uv collapse function */
static void bmo_collapsecon_do_layer(BMesh *bm, BMOperator *op, int layer)
{
	BMIter iter, liter;
	BMFace *f;
	BMLoop *l, *l2;
	BMWalker walker;
	void **blocks = NULL;
	BLI_array_declare(blocks);
	CDBlockBytes min, max;
	int i, tot, type = bm->ldata.layers[layer].type;

	/* clear all short flags */
	BMO_mesh_flag_disable_all(bm, op, BM_ALL, (1 << 16) - 1);

	BMO_slot_buffer_flag_enable(bm, op->slots_in, "edges", BM_EDGE, EDGE_MARK);

	BMW_init(&walker, bm, BMW_LOOPDATA_ISLAND,
	         BMW_MASK_NOP, EDGE_MARK, BMW_MASK_NOP,
	         BMW_FLAG_NOP, /* no need to use BMW_FLAG_TEST_HIDDEN, already marked data */
	         layer);

	BM_ITER_MESH (f, &iter, bm, BM_FACES_OF_MESH) {
		BM_ITER_ELEM (l, &liter, f, BM_LOOPS_OF_FACE) {
			if (BMO_elem_flag_test(bm, l->e, EDGE_MARK)) {
				/* walk */
				BLI_array_empty(blocks);

				CustomData_data_initminmax(type, &min, &max);
				for (l2 = BMW_begin(&walker, l), tot = 0; l2; l2 = BMW_step(&walker), tot++) {
					BLI_array_grow_one(blocks);
					blocks[tot] = CustomData_bmesh_get_layer_n(&bm->ldata, l2->head.data, layer);
					CustomData_data_dominmax(type, blocks[tot], &min, &max);
				}

				if (tot) {
					CustomData_data_multiply(type, &min, 0.5f);
					CustomData_data_multiply(type, &max, 0.5f);
					CustomData_data_add(type, &min, &max);

					/* snap CD (uv, vcol) points to their centroid */
					for (i = 0; i < tot; i++) {
						CustomData_data_copy_value(type, &min, blocks[i]);
					}
				}
			}
		}
	}

	BMW_end(&walker);
	BLI_array_free(blocks);
}

void bmo_collapse_uvs_exec(BMesh *bm, BMOperator *op)
{
	int i;

	for (i = 0; i < bm->ldata.totlayer; i++) {
		if (CustomData_layer_has_math(&bm->ldata, i))
			bmo_collapsecon_do_layer(bm, op, i);
	}
}

static void bmesh_find_doubles_common(BMesh *bm, BMOperator *op,
                                      BMOperator *optarget, BMOpSlot *optarget_slot)
{
	BMVert  **verts;
	int       verts_len;

	int i, j, keepvert = 0;

	const float dist  = BMO_slot_float_get(op->slots_in, "dist");
	const float dist3 = dist * 3.0f;

	/* Test whether keep_verts arg exists and is non-empty */
	if (BMO_slot_exists(op->slots_in, "keep_verts")) {
		BMOIter oiter;
		keepvert = BMO_iter_new(&oiter, op->slots_in, "keep_verts", BM_VERT) != NULL;
	}

	/* get the verts as an array we can sort */
	verts = BMO_slot_as_arrayN(op->slots_in, "verts", &verts_len);

	/* sort by vertex coordinates added together */
	qsort(verts, verts_len, sizeof(BMVert *), vergaverco);

	/* Flag keep_verts */
	if (keepvert) {
		BMO_slot_buffer_flag_enable(bm, op->slots_in, "keep_verts", BM_VERT, VERT_KEEP);
	}

	for (i = 0; i < verts_len; i++) {
		BMVert *v_check = verts[i];

		if (BMO_elem_flag_test(bm, v_check, VERT_DOUBLE)) {
			continue;
		}

		for (j = i + 1; j < verts_len; j++) {
			BMVert *v_other = verts[j];

			/* Compare sort values of the verts using 3x tolerance (allowing for the tolerance
			 * on each of the three axes). This avoids the more expensive length comparison
			 * for most vertex pairs. */
			if ((v_other->co[0] + v_other->co[1] + v_other->co[2]) -
			    (v_check->co[0] + v_check->co[1] + v_check->co[2]) > dist3)
			{
				break;
			}

			if (keepvert) {
				if (BMO_elem_flag_test(bm, v_other, VERT_KEEP) == BMO_elem_flag_test(bm, v_check, VERT_KEEP))
					continue;
			}

			if (compare_len_v3v3(v_check->co, v_other->co, dist)) {

				/* If one vert is marked as keep, make sure it will be the target */
				if (BMO_elem_flag_test(bm, v_other, VERT_KEEP)) {
					SWAP(BMVert *, v_check, v_other);
				}

				BMO_elem_flag_enable(bm, v_other, VERT_DOUBLE);
				BMO_elem_flag_enable(bm, v_check, VERT_TARGET);

				BMO_slot_map_elem_insert(optarget, optarget_slot, v_other, v_check);
			}
		}
	}

	MEM_freeN(verts);
}

void bmo_remove_doubles_exec(BMesh *bm, BMOperator *op)
{
	BMOperator weldop;
	BMOpSlot *slot_targetmap;

	BMO_op_init(bm, &weldop, op->flag, "weld_verts");
	slot_targetmap = BMO_slot_get(weldop.slots_in, "targetmap");
	bmesh_find_doubles_common(bm, op,
	                          &weldop, slot_targetmap);
	BMO_op_exec(bm, &weldop);
	BMO_op_finish(bm, &weldop);
}


void bmo_find_doubles_exec(BMesh *bm, BMOperator *op)
{
	BMOpSlot *slot_targetmap_out;
	slot_targetmap_out = BMO_slot_get(op->slots_out, "targetmap.out");
	bmesh_find_doubles_common(bm, op,
	                          op, slot_targetmap_out);
}

void bmo_automerge_exec(BMesh *bm, BMOperator *op)
{
	BMOperator findop, weldop;
	BMIter viter;
	BMVert *v;

	/* The "verts" input sent to this op is the set of verts that
	 * can be merged away into any other verts. Mark all other verts
	 * as VERT_KEEP. */
	BMO_slot_buffer_flag_enable(bm, op->slots_in, "verts", BM_VERT, VERT_IN);
	BM_ITER_MESH (v, &viter, bm, BM_VERTS_OF_MESH) {
		if (!BMO_elem_flag_test(bm, v, VERT_IN)) {
			BMO_elem_flag_enable(bm, v, VERT_KEEP);
		}
	}

	/* Search for doubles among all vertices, but only merge non-VERT_KEEP
	 * vertices into VERT_KEEP vertices. */
	BMO_op_initf(bm, &findop, op->flag, "find_doubles verts=%av keep_verts=%fv", VERT_KEEP);
	BMO_slot_copy(op,      slots_in, "dist",
	              &findop, slots_in, "dist");
	BMO_op_exec(bm, &findop);

	/* weld the vertices */
	BMO_op_init(bm, &weldop, op->flag, "weld_verts");
	BMO_slot_copy(&findop, slots_out, "targetmap.out",
	              &weldop, slots_in,  "targetmap");
	BMO_op_exec(bm, &weldop);

	BMO_op_finish(bm, &findop);
	BMO_op_finish(bm, &weldop);
}

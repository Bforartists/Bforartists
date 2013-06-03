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
 * Contributor(s): Campbell Barton
 *
 * ***** END GPL LICENSE BLOCK *****
 */

/** \file blender/bmesh/tools/bmesh_decimate_dissolve.c
 *  \ingroup bmesh
 *
 * BMesh decimator that dissolves flat areas into polygons (ngons).
 */


#include "MEM_guardedalloc.h"

#include "BLI_math.h"

#include "bmesh.h"
#include "bmesh_decimate.h"  /* own include */

#define UNIT_TO_ANGLE DEG2RADF(90.0f)
#define ANGLE_TO_UNIT (1.0f / UNIT_TO_ANGLE)

/* multiply vertex edge angle by face angle
 * this means we are not left with sharp corners between _almost_ planer faces
 * convert angles [0-PI/2] -> [0-1], multiply together, then convert back to radians. */
static float bm_vert_edge_face_angle(BMVert *v)
{
	const float angle = BM_vert_calc_edge_angle(v);
	/* note: could be either edge, it doesn't matter */
	if (v->e && BM_edge_is_manifold(v->e)) {
		return ((angle * ANGLE_TO_UNIT) * (BM_edge_calc_face_angle(v->e) * ANGLE_TO_UNIT)) * UNIT_TO_ANGLE;
	}
	else {
		return angle;
	}
}

#undef UNIT_TO_ANGLE
#undef ANGLE_TO_UNIT

typedef struct DissolveElemWeight {
	BMHeader *ele;
	float weight;
} DissolveElemWeight;

static int dissolve_elem_cmp(const void *a1, const void *a2)
{
	const struct DissolveElemWeight *d1 = a1, *d2 = a2;

	if      (d1->weight > d2->weight) return  1;
	else if (d1->weight < d2->weight) return -1;
	return 0;
}

void BM_mesh_decimate_dissolve_ex(BMesh *bm, const float angle_limit, const bool do_dissolve_boundaries,
                                  const BMO_Delimit delimit,
                                  BMVert **vinput_arr, const int vinput_len,
                                  BMEdge **einput_arr, const int einput_len)
{
	const float angle_max = (float)M_PI / 2.0f;
	DissolveElemWeight *weight_elems = MEM_mallocN(max_ii(einput_len, vinput_len) *
	                                               sizeof(DissolveElemWeight), __func__);
	int i, tot_found;
	BMIter iter;
	BMEdge *e_iter;
	BMEdge **earray;

	int *vert_reverse_lookup;

	/* --- first edges --- */

	/* wire -> tag */
	BM_ITER_MESH (e_iter, &iter, bm, BM_EDGES_OF_MESH) {
		BM_elem_flag_set(e_iter, BM_ELEM_TAG, BM_edge_is_wire(e_iter));
	}

	/* go through and split edge */
	for (i = 0, tot_found = 0; i < einput_len; i++) {
		BMEdge *e = einput_arr[i];
		const bool is_contig = BM_edge_is_contiguous(e);
		float angle;

		angle = BM_edge_calc_face_angle(e);
		if (is_contig == false) {
			angle = (float)M_PI - angle;
		}

		if (angle < angle_limit) {
			tot_found++;
		}
		weight_elems[i].ele = (BMHeader *)e;
		weight_elems[i].weight = angle;
	}

	if (tot_found != 0) {
		qsort(weight_elems, einput_len, sizeof(DissolveElemWeight), dissolve_elem_cmp);

		for (i = 0; i < tot_found; i++) {
			BMEdge *e = (BMEdge *)weight_elems[i].ele;
			const bool is_contig = BM_edge_is_contiguous(e);
			float angle;

			/* may have become non-manifold */
			if (!BM_edge_is_manifold(e)) {
				continue;
			}

			if ((delimit & BMO_DELIM_SEAM) &&
			    (BM_elem_flag_test(e, BM_ELEM_SEAM)))
			{
				continue;
			}

			if ((delimit & BMO_DELIM_MATERIAL) &&
			    (e->l->f->mat_nr != e->l->radial_next->f->mat_nr))
			{
				continue;
			}

			if ((delimit & BMO_DELIM_NORMAL) &&
			    (is_contig == false))
			{
				continue;
			}

			/* check twice because cumulative effect could dissolve over angle limit */
			angle = BM_edge_calc_face_angle(e);
			if (is_contig == false) {
				angle = (float)M_PI - angle;
			}

			if (angle < angle_limit) {
				BMFace *f_new = BM_faces_join_pair(bm, e->l->f,
				                                   e->l->radial_next->f,
				                                   e,
				                                   false); /* join faces */

				/* there may be some errors, we don't mind, just move on */
				if (f_new) {
					BM_face_normal_update(f_new);
				}
				else {
					BMO_error_clear(bm);
				}
			}
		}
	}

	/* prepare for cleanup */
	BM_mesh_elem_index_ensure(bm, BM_VERT);
	vert_reverse_lookup = MEM_mallocN(sizeof(int) * bm->totvert, __func__);
	fill_vn_i(vert_reverse_lookup, bm->totvert, -1);
	for (i = 0, tot_found = 0; i < vinput_len; i++) {
		BMVert *v = vinput_arr[i];
		vert_reverse_lookup[BM_elem_index_get(v)] = i;
	}

	/* --- cleanup --- */
	earray = MEM_mallocN(sizeof(BMEdge *) * bm->totedge, __func__);
	BM_ITER_MESH_INDEX (e_iter, &iter, bm, BM_EDGES_OF_MESH, i) {
		earray[i] = e_iter;
	}
	/* remove all edges/verts left behind from dissolving, NULL'ing the vertex array so we dont re-use */
	for (i = bm->totedge - 1; i != -1; i--) {
		e_iter = earray[i];

		if (BM_edge_is_wire(e_iter) && (BM_elem_flag_test(e_iter, BM_ELEM_TAG) == false)) {
			/* edge has become wire */
			int vidx_reverse;
			BMVert *v1 = e_iter->v1;
			BMVert *v2 = e_iter->v2;
			BM_edge_kill(bm, e_iter);
			if (v1->e == NULL) {
				vidx_reverse = vert_reverse_lookup[BM_elem_index_get(v1)];
				if (vidx_reverse != -1) vinput_arr[vidx_reverse] = NULL;
				BM_vert_kill(bm, v1);
			}
			if (v2->e == NULL) {
				vidx_reverse = vert_reverse_lookup[BM_elem_index_get(v2)];
				if (vidx_reverse != -1) vinput_arr[vidx_reverse] = NULL;
				BM_vert_kill(bm, v2);
			}
		}
	}
	MEM_freeN(vert_reverse_lookup);

	MEM_freeN(earray);


	/* --- second verts --- */
	if (do_dissolve_boundaries) {
		/* simple version of the branch below, sincve we will dissolve _all_ verts that use 2 edges */
		for (i = 0; i < vinput_len; i++) {
			BMVert *v = vinput_arr[i];
			if (LIKELY(v != NULL) &&
			    BM_vert_edge_count(v) == 2)
			{
				BM_vert_collapse_edge(bm, v->e, v, true); /* join edges */
			}
		}
	}
	else {
		for (i = 0, tot_found = 0; i < vinput_len; i++) {
			BMVert *v = vinput_arr[i];
			const float angle = v ? bm_vert_edge_face_angle(v) : angle_limit;

			if (angle < angle_limit) {
				weight_elems[i].ele = (BMHeader *)v;
				weight_elems[i].weight = angle;
				tot_found++;
			}
			else {
				weight_elems[i].ele = NULL;
				weight_elems[i].weight = angle_max;
			}
		}

		if (tot_found != 0) {
			qsort(weight_elems, vinput_len, sizeof(DissolveElemWeight), dissolve_elem_cmp);

			for (i = 0; i < tot_found; i++) {
				BMVert *v = (BMVert *)weight_elems[i].ele;
				if (LIKELY(v != NULL) &&
				    /* topology changes may cause this to be un-collapsable */
				    (BM_vert_edge_count(v) == 2) &&
				    /* check twice because cumulative effect could dissolve over angle limit */
				    bm_vert_edge_face_angle(v) < angle_limit)
				{
					BMEdge *e_new = BM_vert_collapse_edge(bm, v->e, v, true); /* join edges */

					if (e_new && e_new->l) {
						BM_edge_normals_update(e_new);
					}
				}
			}
		}
	}

	MEM_freeN(weight_elems);
}

void BM_mesh_decimate_dissolve(BMesh *bm, const float angle_limit, const bool do_dissolve_boundaries,
                               const BMO_Delimit delimit)
{
	int vinput_len;
	int einput_len;

	BMVert **vinput_arr = BM_iter_as_arrayN(bm, BM_VERTS_OF_MESH, NULL, &vinput_len, NULL, 0);
	BMEdge **einput_arr = BM_iter_as_arrayN(bm, BM_EDGES_OF_MESH, NULL, &einput_len, NULL, 0);


	BM_mesh_decimate_dissolve_ex(bm, angle_limit, do_dissolve_boundaries,
	                             delimit,
	                             vinput_arr, vinput_len,
	                             einput_arr, einput_len);

	MEM_freeN(vinput_arr);
	MEM_freeN(einput_arr);
}

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
 * The Original Code is Copyright (C) 2017 by Blender Foundation.
 * All rights reserved.
 *
 * Contributor(s): Blender Foundation, Mike Erwin, Dalai Felinto
 *
 * ***** END GPL LICENSE BLOCK *****
 */

/** \file blender/blenkernel/intern/mesh_render.c
 *  \ingroup bke
 *
 * \brief Mesh API for render engines
 */

#include "MEM_guardedalloc.h"

#include "BLI_utildefines.h"
#include "BLI_edgehash.h"
#include "BLI_math_vector.h"

#include "DNA_mesh_types.h"
#include "DNA_meshdata_types.h"

#include "BKE_customdata.h"
#include "BKE_depsgraph.h"
#include "BKE_DerivedMesh.h"
#include "BKE_editmesh.h"
#include "BKE_mesh.h"
#include "BKE_mesh_render.h"

#include "bmesh.h"

#include "GPU_batch.h"

/* ---------------------------------------------------------------------- */
/* Mesh/BMesh Interface, direct access to basic data. */

static int mesh_render_verts_num_get(Mesh *me)
{
	return me->edit_btmesh ? me->edit_btmesh->bm->totvert : me->totvert;
}

static int mesh_render_edges_num_get(Mesh *me)
{
	return me->edit_btmesh ? me->edit_btmesh->bm->totedge : me->totedge;
}

static int mesh_render_looptri_num_get(Mesh *me)
{
	return me->edit_btmesh ? me->edit_btmesh->tottri : poly_to_tri_count(me->totpoly, me->totloop);
}

static int mesh_render_polys_num_get(Mesh *me)
{
	return me->edit_btmesh ? me->edit_btmesh->bm->totface : me->totpoly;
}

static int UNUSED_FUNCTION(mesh_render_loops_num_get)(Mesh *me)
{
	return me->edit_btmesh ? me->edit_btmesh->bm->totloop : me->totloop;
}

/* ---------------------------------------------------------------------- */
/* Mesh/BMesh Interface, indirect, partially cached access to complex data. */

typedef struct EdgeAdjacentPolys {
	int count;
	int face_index[2];
} EdgeAdjacentPolys;

typedef struct MeshRenderData {
	int types;

	int totvert;
	int totedge;
	int tottri;
	int totloop;
	int totpoly;
	int totlvert;
	int totledge;

	BMEditMesh *edit_bmesh;
	MVert *mvert;
	MEdge *medge;
	MLoop *mloop;
	MPoly *mpoly;

	BMVert *eve_act;
	BMEdge *eed_act;
	BMFace *efa_act;

	int crease_ofs;
	int bweight_ofs;

	/* Data created on-demand (usually not for bmesh-based data). */
	EdgeHash *ehash;
	EdgeAdjacentPolys *edges_adjacent_polys;
	MLoopTri *mlooptri;
	int *loose_edges;
	int *loose_verts;

	float (*poly_normals)[3];
	short (*poly_normals_short)[3];
	short (*vert_normals_short)[3];
} MeshRenderData;

enum {
	MR_DATATYPE_VERT       = 1 << 0,
	MR_DATATYPE_EDGE       = 1 << 1,
	MR_DATATYPE_LOOPTRI    = 1 << 2,
	MR_DATATYPE_LOOP       = 1 << 3,
	MR_DATATYPE_POLY       = 1 << 4,
	MR_DATATYPE_OVERLAY    = 1 << 5,
};

static MeshRenderData *mesh_render_data_create(Mesh *me, const int types)
{
	MeshRenderData *mrdata = MEM_callocN(sizeof(*mrdata), __func__);
	mrdata->types = types;

	if (me->edit_btmesh) {
		BMEditMesh *embm = me->edit_btmesh;
		BMesh *bm = embm->bm;

		mrdata->edit_bmesh = embm;

		int bm_ensure_types = 0;
		if (types & (MR_DATATYPE_VERT)) {
			mrdata->totvert = bm->totvert;
			bm_ensure_types |= BM_VERT;
		}
		if (types & (MR_DATATYPE_EDGE)) {
			mrdata->totedge = bm->totedge;
			bm_ensure_types |= BM_EDGE;
		}
		if (types & MR_DATATYPE_LOOPTRI) {
			BKE_editmesh_tessface_calc(embm);
			mrdata->tottri = embm->tottri;
		}
		if (types & MR_DATATYPE_LOOP) {
			mrdata->totloop = bm->totloop;
			bm_ensure_types |= BM_LOOP;
		}
		if (types & MR_DATATYPE_POLY) {
			mrdata->totpoly = bm->totface;
			bm_ensure_types |= BM_FACE;
		}
		if (types & MR_DATATYPE_OVERLAY) {
			mrdata->efa_act = BM_mesh_active_face_get(bm, false, true);
			mrdata->eed_act = BM_mesh_active_edge_get(bm);
			mrdata->eve_act = BM_mesh_active_vert_get(bm);
			mrdata->crease_ofs = CustomData_get_offset(&bm->edata, CD_CREASE);
			mrdata->bweight_ofs = CustomData_get_offset(&bm->edata, CD_BWEIGHT);
		}
		BM_mesh_elem_index_ensure(bm, bm_ensure_types);
		BM_mesh_elem_table_ensure(bm, bm_ensure_types & ~BM_LOOP);
		if (types & MR_DATATYPE_OVERLAY) {
			mrdata->totlvert = mrdata->totledge = 0;

			int *lverts = mrdata->loose_verts = MEM_mallocN(mrdata->totvert * sizeof(int), "Loose Vert");
			int *ledges = mrdata->loose_edges = MEM_mallocN(mrdata->totedge * sizeof(int), "Loose Edges");

			for (int i = 0; i < mrdata->totvert; ++i) {
				BMVert *bv = BM_vert_at_index(bm, i);

				/* Loose vert */
				if (bv->e == NULL) {
					lverts[mrdata->totlvert] = BM_elem_index_get(bv);
					mrdata->totlvert++;
					continue;
				}

				/* Find Loose Edges */
				BMEdge *e_iter, *e_first;
				e_first = e_iter = bv->e;
				do {
					if (e_iter->l == NULL) {
						BMVert *other_vert = BM_edge_other_vert(e_iter, bv);

						/* Verify we do not add the same edge twice */
						if (BM_elem_index_get(other_vert) > i) {
							ledges[mrdata->totledge] = BM_elem_index_get(e_iter);
							mrdata->totledge++;
						}
					}
				} while ((e_iter = BM_DISK_EDGE_NEXT(e_iter, bv)) != e_first);
			}
			mrdata->loose_verts = MEM_reallocN(mrdata->loose_verts, mrdata->totlvert * sizeof(int));
			mrdata->loose_edges = MEM_reallocN(mrdata->loose_edges, mrdata->totledge * sizeof(int));
		}
	}
	else {
		if (types & (MR_DATATYPE_VERT)) {
			mrdata->totvert = me->totvert;
			mrdata->mvert = CustomData_get_layer(&me->vdata, CD_MVERT);
		}
		if (types & (MR_DATATYPE_EDGE)) {
			mrdata->totedge = me->totedge;
			mrdata->medge = CustomData_get_layer(&me->edata, CD_MEDGE);
		}
		if (types & MR_DATATYPE_LOOPTRI) {
			const int tottri = mrdata->tottri = poly_to_tri_count(me->totpoly, me->totloop);
			mrdata->mlooptri = MEM_mallocN(sizeof(*mrdata->mlooptri) * tottri, __func__);
			BKE_mesh_recalc_looptri(me->mloop, me->mpoly, me->mvert, me->totloop, me->totpoly, mrdata->mlooptri);
		}
		if (types & MR_DATATYPE_LOOP) {
			mrdata->totloop = me->totloop;
			mrdata->mloop = CustomData_get_layer(&me->ldata, CD_MLOOP);
		}
		if (types & MR_DATATYPE_POLY) {
			mrdata->totpoly = me->totpoly;
			mrdata->mpoly = CustomData_get_layer(&me->pdata, CD_MPOLY);
		}
	}

	return mrdata;
}

static void mesh_render_data_free(MeshRenderData *mrdata)
{
	if (mrdata->ehash) {
		BLI_edgehash_free(mrdata->ehash, NULL);
	}
	if (mrdata->loose_verts) {
		MEM_freeN(mrdata->loose_verts);
	}
	if (mrdata->loose_edges) {
		MEM_freeN(mrdata->loose_edges);
	}
	if (mrdata->edges_adjacent_polys) {
		MEM_freeN(mrdata->edges_adjacent_polys);
	}
	if (mrdata->mlooptri) {
		MEM_freeN(mrdata->mlooptri);
	}
	if (mrdata->poly_normals) {
		MEM_freeN(mrdata->poly_normals);
	}
	if (mrdata->poly_normals_short) {
		MEM_freeN(mrdata->poly_normals_short);
	}
	if (mrdata->vert_normals_short) {
		MEM_freeN(mrdata->vert_normals_short);
	}
	MEM_freeN(mrdata);
}

static int mesh_render_data_verts_num_get(const MeshRenderData *mrdata)
{
	BLI_assert(mrdata->types & MR_DATATYPE_VERT);
	return mrdata->totvert;
}

static int mesh_render_data_loose_verts_num_get(const MeshRenderData *mrdata)
{
	BLI_assert(mrdata->types & MR_DATATYPE_OVERLAY);
	return mrdata->totlvert;
}

static int mesh_render_data_edges_num_get(const MeshRenderData *mrdata)
{
	BLI_assert(mrdata->types & MR_DATATYPE_EDGE);
	return mrdata->totedge;
}

static int mesh_render_data_loose_edges_num_get(const MeshRenderData *mrdata)
{
	BLI_assert(mrdata->types & MR_DATATYPE_OVERLAY);
	return mrdata->totledge;
}

static int mesh_render_data_looptri_num_get(const MeshRenderData *mrdata)
{
	BLI_assert(mrdata->types & MR_DATATYPE_LOOPTRI);
	return mrdata->tottri;
}

static int UNUSED_FUNCTION(mesh_render_data_loops_num_get)(const MeshRenderData *mrdata)
{
	BLI_assert(mrdata->types & MR_DATATYPE_LOOP);
	return mrdata->totloop;
}

static int mesh_render_data_polys_num_get(const MeshRenderData *mrdata)
{
	BLI_assert(mrdata->types & MR_DATATYPE_POLY);
	return mrdata->totpoly;
}

static float *mesh_render_data_vert_co(const MeshRenderData *mrdata, const int vert_idx)
{
	BLI_assert(mrdata->types & MR_DATATYPE_VERT);

	if (mrdata->edit_bmesh) {
		BMesh *bm = mrdata->edit_bmesh->bm;
		BMVert *bv = BM_vert_at_index(bm, vert_idx);
		return bv->co;
	}
	else {
		return mrdata->mvert[vert_idx].co;
	}
}

static short *mesh_render_data_vert_nor(const MeshRenderData *mrdata, const int vert_idx)
{
	BLI_assert(mrdata->types & MR_DATATYPE_VERT);

	if (mrdata->edit_bmesh) {
		static short fno[3];
		BMesh *bm = mrdata->edit_bmesh->bm;
		BMVert *bv = BM_vert_at_index(bm, vert_idx);
		normal_float_to_short_v3(fno, bv->no);
		return fno;
	}
	else {
		return mrdata->mvert[vert_idx].no;
	}
}

static void mesh_render_data_edge_verts_indices_get(const MeshRenderData *mrdata, const int edge_idx, int r_vert_idx[2])
{
	BLI_assert(mrdata->types & MR_DATATYPE_EDGE);

	if (mrdata->edit_bmesh) {
		const BMEdge *bm_edge = BM_edge_at_index(mrdata->edit_bmesh->bm, edge_idx);
		r_vert_idx[0] = BM_elem_index_get(bm_edge->v1);
		r_vert_idx[1] = BM_elem_index_get(bm_edge->v2);
	}
	else {
		const MEdge *me = &mrdata->medge[edge_idx];
		r_vert_idx[0] = me->v1;
		r_vert_idx[1] = me->v2;
	}
}

static void mesh_render_data_pnors_pcenter_select_get(MeshRenderData *mrdata, const int poly, float pnors[3], float center[3], bool *selected)
{
	BLI_assert(mrdata->types & (MR_DATATYPE_VERT | MR_DATATYPE_LOOP | MR_DATATYPE_POLY));

	if (mrdata->edit_bmesh) {
		const BMFace *bf = BM_face_at_index(mrdata->edit_bmesh->bm, poly);
		BM_face_calc_center_mean(bf, center);
		BM_face_calc_normal(bf, pnors);
		*selected = (BM_elem_flag_test(bf, BM_ELEM_SELECT) != 0) ? true : false;
	}
	else {
		MVert *mvert = mrdata->mvert;
		const MPoly *mpoly = mrdata->mpoly + poly;
		const MLoop *mloop = mrdata->mloop + mpoly->loopstart;

		BKE_mesh_calc_poly_center(mpoly, mloop, mvert, center);
		BKE_mesh_calc_poly_normal(mpoly, mloop, mvert, pnors);

		*selected = false; /* No selection if not in edit mode */
	}
}

static bool mesh_render_data_edge_exists(MeshRenderData *mrdata, const int v1, const int v2)
{
	BLI_assert(mrdata->types & MR_DATATYPE_EDGE);

	if (mrdata->edit_bmesh) {
		BMesh *bm = mrdata->edit_bmesh->bm;
		BMVert *bv1 = BM_vert_at_index(bm, v1);
		BMVert *bv2 = BM_vert_at_index(bm, v2);
		return BM_edge_exists(bv1, bv2) != NULL;
	}
	else {
		EdgeHash *ehash = mrdata->ehash;

		if (!ehash) {
			/* Create edge hash on demand. */
			ehash = mrdata->ehash = BLI_edgehash_new(__func__);

			MEdge *medge = mrdata->medge;
			for (int i = 0; i < mrdata->totedge; i++, medge++) {
				BLI_edgehash_insert(ehash, medge->v1, medge->v2, medge);
			}
		}

		return BLI_edgehash_lookup(ehash, v1, v2) != NULL;
	}
}

static bool mesh_render_data_edge_vcos_manifold_pnors(
        MeshRenderData *mrdata, const int edge_index,
        float **r_vco1, float **r_vco2, float **r_pnor1, float **r_pnor2)
{
	BLI_assert(mrdata->types & (MR_DATATYPE_VERT | MR_DATATYPE_EDGE | MR_DATATYPE_LOOP | MR_DATATYPE_POLY));

	if (mrdata->edit_bmesh) {
		BMesh *bm = mrdata->edit_bmesh->bm;
		BMEdge *bm_edge = BM_edge_at_index(bm, edge_index);
		*r_vco1 = bm_edge->v1->co;
		*r_vco2 = bm_edge->v2->co;
		if (BM_edge_is_manifold(bm_edge)) {
			*r_pnor1 = bm_edge->l->f->no;
			*r_pnor2 = bm_edge->l->radial_next->f->no;
			return true;
		}
	}
	else {
		MVert *mvert = mrdata->mvert;
		MEdge *medge = mrdata->medge;
		EdgeAdjacentPolys *eap = mrdata->edges_adjacent_polys;
		float (*pnors)[3] = mrdata->poly_normals;

		if (!eap) {
			const MLoop *mloop = mrdata->mloop;
			const MPoly *mpoly = mrdata->mpoly;
			const int poly_ct = mrdata->totpoly;
			const bool do_pnors = (pnors == NULL);

			eap = mrdata->edges_adjacent_polys = MEM_callocN(sizeof(*eap) * mrdata->totedge, __func__);
			if (do_pnors) {
				pnors = mrdata->poly_normals = MEM_mallocN(sizeof(*pnors) * poly_ct, __func__);
			}

			for (int i = 0; i < poly_ct; i++, mpoly++) {
				if (do_pnors) {
					BKE_mesh_calc_poly_normal(mpoly, mloop + mpoly->loopstart, mvert, pnors[i]);
				}

				const int loopend = mpoly->loopstart + mpoly->totloop;
				for (int j = mpoly->loopstart; j < loopend; j++) {
					const int edge_idx = mloop[j].e;
					if (eap[edge_idx].count < 2) {
						eap[edge_idx].face_index[eap[edge_idx].count] = i;
					}
					eap[edge_idx].count++;
				}
			}
		}
		BLI_assert(eap && pnors);

		*r_vco1 = mvert[medge[edge_index].v1].co;
		*r_vco2 = mvert[medge[edge_index].v2].co;
		if (eap[edge_index].count == 2) {
			*r_pnor1 = pnors[eap[edge_index].face_index[0]];
			*r_pnor2 = pnors[eap[edge_index].face_index[1]];
			return true;
		}
	}

	return false;
}

static void mesh_render_data_looptri_verts_indices_get(const MeshRenderData *mrdata, const int tri_idx, int r_vert_idx[3])
{
	BLI_assert(mrdata->types & (MR_DATATYPE_LOOPTRI | MR_DATATYPE_LOOP));

	if (mrdata->edit_bmesh) {
		const BMLoop **bm_looptri = (const BMLoop **)mrdata->edit_bmesh->looptris[tri_idx];
		r_vert_idx[0] = BM_elem_index_get(bm_looptri[0]->v);
		r_vert_idx[1] = BM_elem_index_get(bm_looptri[1]->v);
		r_vert_idx[2] = BM_elem_index_get(bm_looptri[2]->v);
	}
	else {
		const MLoopTri *mlt = &mrdata->mlooptri[tri_idx];
		r_vert_idx[0] = mrdata->mloop[mlt->tri[0]].v;
		r_vert_idx[1] = mrdata->mloop[mlt->tri[1]].v;
		r_vert_idx[2] = mrdata->mloop[mlt->tri[2]].v;
	}
}

static bool mesh_render_data_looptri_cos_nors_smooth_get(
        MeshRenderData *mrdata, const int tri_idx, float *(*r_vert_cos)[3], short **r_tri_nor, short *(*r_vert_nors)[3])
{
	BLI_assert(mrdata->types & (MR_DATATYPE_VERT | MR_DATATYPE_LOOPTRI | MR_DATATYPE_LOOP | MR_DATATYPE_POLY));

	if (mrdata->edit_bmesh) {
		const BMLoop **bm_looptri = (const BMLoop **)mrdata->edit_bmesh->looptris[tri_idx];
		short (*pnors_short)[3] = mrdata->poly_normals_short;
		short (*vnors_short)[3] = mrdata->vert_normals_short;

		if (!pnors_short) {
			BMesh *bm = mrdata->edit_bmesh->bm;
			BMIter fiter;
			BMFace *face;
			int i;

			pnors_short = mrdata->poly_normals_short = MEM_mallocN(sizeof(*pnors_short) * mrdata->totpoly, __func__);
			BM_ITER_MESH_INDEX(face, &fiter, bm, BM_FACES_OF_MESH, i) {
				normal_float_to_short_v3(pnors_short[i], face->no);
			}
		}
		if (!vnors_short) {
			BMesh *bm = mrdata->edit_bmesh->bm;
			BMIter viter;
			BMVert *vert;
			int i;

			vnors_short = mrdata->vert_normals_short = MEM_mallocN(sizeof(*vnors_short) * mrdata->totvert, __func__);
			BM_ITER_MESH_INDEX(vert, &viter, bm, BM_VERT, i) {
				normal_float_to_short_v3(vnors_short[i], vert->no);
			}
		}

		(*r_vert_cos)[0] = bm_looptri[0]->v->co;
		(*r_vert_cos)[1] = bm_looptri[1]->v->co;
		(*r_vert_cos)[2] = bm_looptri[2]->v->co;
		*r_tri_nor = pnors_short[BM_elem_index_get(bm_looptri[0]->f)];
		(*r_vert_nors)[0] = vnors_short[BM_elem_index_get(bm_looptri[0]->v)];
		(*r_vert_nors)[1] = vnors_short[BM_elem_index_get(bm_looptri[1]->v)];
		(*r_vert_nors)[2] = vnors_short[BM_elem_index_get(bm_looptri[2]->v)];

		return BM_elem_flag_test_bool(bm_looptri[0]->f, BM_ELEM_SMOOTH);
	}
	else {
		const MLoopTri *mlt = &mrdata->mlooptri[tri_idx];
		short (*pnors_short)[3] = mrdata->poly_normals_short;

		if (!pnors_short) {
			float (*pnors)[3] = mrdata->poly_normals;

			if (!pnors) {
				pnors = mrdata->poly_normals = MEM_mallocN(sizeof(*pnors) * mrdata->totpoly, __func__);
				BKE_mesh_calc_normals_poly(
				            mrdata->mvert, NULL, mrdata->totvert,
				            mrdata->mloop, mrdata->mpoly, mrdata->totloop, mrdata->totpoly, pnors, true);
			}

			pnors_short = mrdata->poly_normals_short = MEM_mallocN(sizeof(*pnors_short) * mrdata->totpoly, __func__);
			for (int i = 0; i < mrdata->totpoly; i++) {
				normal_float_to_short_v3(pnors_short[i], pnors[i]);
			}
		}

		(*r_vert_cos)[0] = mrdata->mvert[mrdata->mloop[mlt->tri[0]].v].co;
		(*r_vert_cos)[1] = mrdata->mvert[mrdata->mloop[mlt->tri[1]].v].co;
		(*r_vert_cos)[2] = mrdata->mvert[mrdata->mloop[mlt->tri[2]].v].co;
		*r_tri_nor = pnors_short[mlt->poly];
		(*r_vert_nors)[0] = mrdata->mvert[mrdata->mloop[mlt->tri[0]].v].no;
		(*r_vert_nors)[1] = mrdata->mvert[mrdata->mloop[mlt->tri[1]].v].no;
		(*r_vert_nors)[2] = mrdata->mvert[mrdata->mloop[mlt->tri[2]].v].no;

		return (mrdata->mpoly[mlt->poly].flag & ME_SMOOTH) != 0;
	}
}

/* First 2 bytes are bit flags
 * 3rd is for sharp edges
 * 4rd is for creased edges */
enum {
	VFLAG_VERTEX_ACTIVE   = 1 << 0,
	VFLAG_VERTEX_SELECTED = 1 << 1,
	VFLAG_FACE_ACTIVE     = 1 << 2,
	VFLAG_FACE_SELECTED   = 1 << 3,
};

enum {
	VFLAG_EDGE_EXISTS   = 1 << 0,
	VFLAG_EDGE_ACTIVE   = 1 << 1,
	VFLAG_EDGE_SELECTED = 1 << 2,
	VFLAG_EDGE_SEAM     = 1 << 3,
	VFLAG_EDGE_SHARP    = 1 << 4,
	/* Beware to not go over 1 << 7
	 * (see gpu_shader_edit_overlay_geom.glsl) */
};

static unsigned char mesh_render_data_looptri_flag(MeshRenderData *mrdata, const int f)
{
	unsigned char fflag = 0;

	if (mrdata->edit_bmesh) {
		BMFace *bf = mrdata->edit_bmesh->looptris[f][0]->f;

		if (bf == mrdata->efa_act)
			fflag |= VFLAG_FACE_ACTIVE;

		if (BM_elem_flag_test(bf, BM_ELEM_SELECT))
			fflag |= VFLAG_FACE_SELECTED;
	}

	return fflag;
}

static unsigned char *mesh_render_data_edge_flag(
        MeshRenderData *mrdata, const int v1, const int v2, const int e)
{
	static unsigned char eflag[4];
	memset(eflag, 0, sizeof(char) * 4);

	/* if edge exists */
	if (mrdata->edit_bmesh) {
		BMesh *bm = mrdata->edit_bmesh->bm;
		BMEdge *be = NULL;

		if (e != -1) be = BM_edge_at_index(bm, e);
		else         be = BM_edge_exists(BM_vert_at_index(bm, v1),
		                                 BM_vert_at_index(bm, v2));

		if (be != NULL) {

			eflag[1] |= VFLAG_EDGE_EXISTS;

			if (be == mrdata->eed_act)
				eflag[1] |= VFLAG_EDGE_ACTIVE;

			if (BM_elem_flag_test(be, BM_ELEM_SELECT))
				eflag[1] |= VFLAG_EDGE_SELECTED;

			if (BM_elem_flag_test(be, BM_ELEM_SEAM))
				eflag[1] |= VFLAG_EDGE_SEAM;

			if (!BM_elem_flag_test(be, BM_ELEM_SMOOTH))
				eflag[1] |= VFLAG_EDGE_SHARP;

			/* Use a byte for value range */
			if (mrdata->crease_ofs != -1) {
				float crease = BM_ELEM_CD_GET_FLOAT(be, mrdata->crease_ofs);
				if (crease > 0) {
					eflag[2] = (char)(crease * 255.0f);
				}
			}

			/* Use a byte for value range */
			if (mrdata->bweight_ofs != -1) {
				float bweight = BM_ELEM_CD_GET_FLOAT(be, mrdata->bweight_ofs);
				if (bweight > 0) {
					eflag[3] = (char)(bweight * 255.0f);
				}
			}
		}
	}
	else if ((e == -1) && mesh_render_data_edge_exists(mrdata, v1, v2)) {
		eflag[1] |= VFLAG_EDGE_EXISTS;
	}

	return eflag;
}

static unsigned char mesh_render_data_vertex_flag(MeshRenderData *mrdata, const int v)
{

	unsigned char vflag = 0;

	if (mrdata->edit_bmesh) {
		BMesh *bm = mrdata->edit_bmesh->bm;
		BMVert *bv = BM_vert_at_index(bm, v);

		/* Current vertex */
		if (bv == mrdata->eve_act)
			vflag |= VFLAG_VERTEX_ACTIVE;

		if (BM_elem_flag_test(bv, BM_ELEM_SELECT))
			vflag |= VFLAG_VERTEX_SELECTED;
	}

	return vflag;
}

static void add_overlay_tri(
        MeshRenderData *mrdata, VertexBuffer *vbo, const unsigned int pos_id, const unsigned int edgeMod_id,
        const int v1, const int v2, const int v3, const int f, const int base_vert_idx)
{
	const float *pos = mesh_render_data_vert_co(mrdata, v1);
	unsigned char *eflag = mesh_render_data_edge_flag(mrdata, v2, v3, -1);
	unsigned char  fflag = mesh_render_data_looptri_flag(mrdata, f);
	unsigned char  vflag = mesh_render_data_vertex_flag(mrdata, v1);
	eflag[0] = fflag | vflag;
	setAttrib(vbo, pos_id, base_vert_idx + 0, pos);
	setAttrib(vbo, edgeMod_id, base_vert_idx + 0, eflag);

	pos = mesh_render_data_vert_co(mrdata, v2);
	eflag = mesh_render_data_edge_flag(mrdata, v1, v3, -1);
	vflag = mesh_render_data_vertex_flag(mrdata, v2);
	eflag[0] = fflag | vflag;
	setAttrib(vbo, pos_id, base_vert_idx + 1, pos);
	setAttrib(vbo, edgeMod_id, base_vert_idx + 1, eflag);

	pos = mesh_render_data_vert_co(mrdata, v3);
	eflag = mesh_render_data_edge_flag(mrdata, v1, v2, -1);
	vflag = mesh_render_data_vertex_flag(mrdata, v3);
	eflag[0] = fflag | vflag;
	setAttrib(vbo, pos_id, base_vert_idx + 2, pos);
	setAttrib(vbo, edgeMod_id, base_vert_idx + 2, eflag);
}

static void add_overlay_loose_edge(
        MeshRenderData *mrdata, VertexBuffer *vbo, const unsigned int pos_id, const unsigned int edgeMod_id,
        const int v1, const int v2, const int e, const int base_vert_idx)
{
	unsigned char *eflag = mesh_render_data_edge_flag(mrdata, 0, 0, e);
	const float *pos = mesh_render_data_vert_co(mrdata, v1);
	eflag[0] = mesh_render_data_vertex_flag(mrdata, v1);
	setAttrib(vbo, pos_id, base_vert_idx + 0, pos);
	setAttrib(vbo, edgeMod_id, base_vert_idx + 0, eflag);

	pos = mesh_render_data_vert_co(mrdata, v2);
	eflag[0] = mesh_render_data_vertex_flag(mrdata, v2);
	setAttrib(vbo, pos_id, base_vert_idx + 1, pos);
	setAttrib(vbo, edgeMod_id, base_vert_idx + 1, eflag);
}

static void add_overlay_loose_vert(
        MeshRenderData *mrdata, VertexBuffer *vbo, const unsigned int pos_id, const unsigned int edgeMod_id,
        const int v, const int base_vert_idx)
{
	unsigned char vflag[4] = {0, 0, 0, 0};
	const float *pos = mesh_render_data_vert_co(mrdata, v);
	vflag[0] = mesh_render_data_vertex_flag(mrdata, v);
	setAttrib(vbo, pos_id, base_vert_idx + 0, pos);
	setAttrib(vbo, edgeMod_id, base_vert_idx + 0, vflag);
}

/* ---------------------------------------------------------------------- */
/* Mesh Batch Cache */

typedef struct MeshBatchCache {
	VertexBuffer *pos_in_order;
	VertexBuffer *nor_in_order;
	ElementList *edges_in_order;
	ElementList *triangles_in_order;

	Batch *all_verts;
	Batch *all_edges;
	Batch *all_triangles;

	VertexBuffer *pos_with_normals;
	Batch *triangles_with_normals;
	Batch *points_with_normals;
	Batch *fancy_edges; /* owns its vertex buffer (not shared) */

	/* TODO : split in 2 buffers to avoid unnecessary
	 * data transfer when selecting/deselecting
	 * and combine into one batch and use offsets to render
	 * Tri / edges / verts separately */
	Batch *overlay_triangles;
	Batch *overlay_loose_verts;
	Batch *overlay_loose_edges;
	Batch *overlay_facedots;

	/* settings to determine if cache is invalid */
	bool is_dirty;
	int tot_edges;
	int tot_tris;
	int tot_polys;
	int tot_verts;
	bool is_editmode;
} MeshBatchCache;

/* Batch cache management. */

static bool mesh_batch_cache_valid(Mesh *me)
{
	MeshBatchCache *cache = me->batch_cache;

	if (cache == NULL) {
		return false;
	}

	if (cache->is_editmode != (me->edit_btmesh != NULL)) {
		return false;
	}

	if (cache->is_dirty == false) {
		return true;
	}
	else {
		if (cache->is_editmode) {
			return false;
		}
		else if ((cache->tot_verts != mesh_render_verts_num_get(me)) ||
		         (cache->tot_edges != mesh_render_edges_num_get(me)) ||
		         (cache->tot_tris != mesh_render_looptri_num_get(me)) ||
		         (cache->tot_polys != mesh_render_polys_num_get(me)))
		{
			return false;
		}
	}

	return true;
}

static void mesh_batch_cache_init(Mesh *me)
{
	MeshBatchCache *cache = me->batch_cache;

	if (!cache) {
		cache = me->batch_cache = MEM_callocN(sizeof(*cache), __func__);
	}
	else {
		memset(cache, 0, sizeof(*cache));
	}

	cache->is_editmode = me->edit_btmesh != NULL;

	if (cache->is_editmode == false) {
		cache->tot_edges = mesh_render_edges_num_get(me);
		cache->tot_tris = mesh_render_looptri_num_get(me);
		cache->tot_polys = mesh_render_polys_num_get(me);
		cache->tot_verts = mesh_render_verts_num_get(me);
	}

	cache->is_dirty = false;
}

static MeshBatchCache *mesh_batch_cache_get(Mesh *me)
{
	if (!mesh_batch_cache_valid(me)) {
		BKE_mesh_batch_cache_clear(me);
		mesh_batch_cache_init(me);
	}
	return me->batch_cache;
}

void BKE_mesh_batch_cache_dirty(struct Mesh *me)
{
	MeshBatchCache *cache = me->batch_cache;
	if (cache) {
		cache->is_dirty = true;
	}
}

void BKE_mesh_batch_selection_dirty(struct Mesh *me)
{
	MeshBatchCache *cache = me->batch_cache;
	if (cache) {
		/* TODO Separate Flag vbo */
		if (cache->overlay_triangles) {
			Batch_discard_all(cache->overlay_triangles);
			cache->overlay_triangles = NULL;
		}
		if (cache->overlay_loose_verts) {
			Batch_discard_all(cache->overlay_loose_verts);
			cache->overlay_loose_verts = NULL;
		}
		if (cache->overlay_loose_edges) {
			Batch_discard_all(cache->overlay_loose_edges);
			cache->overlay_loose_edges = NULL;
		}
		if (cache->overlay_facedots) {
			Batch_discard_all(cache->overlay_facedots);
			cache->overlay_facedots = NULL;
		}
	}
}

void BKE_mesh_batch_cache_clear(Mesh *me)
{
	MeshBatchCache *cache = me->batch_cache;
	if (!cache) {
		return;
	}

	if (cache->all_verts) Batch_discard(cache->all_verts);
	if (cache->all_edges) Batch_discard(cache->all_edges);
	if (cache->all_triangles) Batch_discard(cache->all_triangles);

	if (cache->pos_in_order) VertexBuffer_discard(cache->pos_in_order);
	if (cache->edges_in_order) ElementList_discard(cache->edges_in_order);
	if (cache->triangles_in_order) ElementList_discard(cache->triangles_in_order);

	if (cache->overlay_triangles) Batch_discard_all(cache->overlay_triangles);
	if (cache->overlay_loose_verts) Batch_discard_all(cache->overlay_loose_verts);
	if (cache->overlay_loose_edges) Batch_discard_all(cache->overlay_loose_edges);
	if (cache->overlay_facedots) Batch_discard_all(cache->overlay_facedots);

	if (cache->triangles_with_normals) Batch_discard(cache->triangles_with_normals);
	if (cache->points_with_normals) Batch_discard(cache->points_with_normals);
	if (cache->pos_with_normals) VertexBuffer_discard(cache->pos_with_normals);
	

	if (cache->fancy_edges) {
		Batch_discard_all(cache->fancy_edges);
	}
}

void BKE_mesh_batch_cache_free(Mesh *me)
{
	BKE_mesh_batch_cache_clear(me);
	MEM_SAFE_FREE(me->batch_cache);
}

/* Batch cache usage. */

static VertexBuffer *mesh_batch_cache_get_pos_and_normals(MeshRenderData *mrdata, MeshBatchCache *cache)
{
	BLI_assert(mrdata->types & (MR_DATATYPE_VERT | MR_DATATYPE_LOOPTRI | MR_DATATYPE_LOOP | MR_DATATYPE_POLY));

	if (cache->pos_with_normals == NULL) {
		unsigned int vidx = 0, nidx = 0;

		static VertexFormat format = { 0 };
		static unsigned int pos_id, nor_id;
		if (format.attrib_ct == 0) {
			/* initialize vertex format */
			pos_id = add_attrib(&format, "pos", GL_FLOAT, 3, KEEP_FLOAT);
			nor_id = add_attrib(&format, "nor", GL_SHORT, 3, NORMALIZE_INT_TO_FLOAT);
		}

		const int tottri = mesh_render_data_looptri_num_get(mrdata);

		cache->pos_with_normals = VertexBuffer_create_with_format(&format);
		VertexBuffer_allocate_data(cache->pos_with_normals, tottri * 3);

		for (int i = 0; i < tottri; i++) {
			float *tri_vert_cos[3];
			short *tri_nor, *tri_vert_nors[3];

			const bool is_smooth = mesh_render_data_looptri_cos_nors_smooth_get(mrdata, i, &tri_vert_cos, &tri_nor, &tri_vert_nors);

			if (is_smooth) {
				setAttrib(cache->pos_with_normals, nor_id, nidx++, tri_vert_nors[0]);
				setAttrib(cache->pos_with_normals, nor_id, nidx++, tri_vert_nors[1]);
				setAttrib(cache->pos_with_normals, nor_id, nidx++, tri_vert_nors[2]);
			}
			else {
				setAttrib(cache->pos_with_normals, nor_id, nidx++, tri_nor);
				setAttrib(cache->pos_with_normals, nor_id, nidx++, tri_nor);
				setAttrib(cache->pos_with_normals, nor_id, nidx++, tri_nor);
			}

			setAttrib(cache->pos_with_normals, pos_id, vidx++, tri_vert_cos[0]);
			setAttrib(cache->pos_with_normals, pos_id, vidx++, tri_vert_cos[1]);
			setAttrib(cache->pos_with_normals, pos_id, vidx++, tri_vert_cos[2]);
		}
	}
	return cache->pos_with_normals;
}
static VertexBuffer *mesh_batch_cache_get_pos_and_nor_in_order(MeshRenderData *mrdata, MeshBatchCache *cache)
{
	BLI_assert(mrdata->types & MR_DATATYPE_VERT);

	if (cache->pos_in_order == NULL) {
		static VertexFormat format = { 0 };
		static unsigned pos_id, nor_id;
		if (format.attrib_ct == 0) {
			/* initialize vertex format */
			pos_id = add_attrib(&format, "pos", GL_FLOAT, 3, KEEP_FLOAT);
			nor_id = add_attrib(&format, "nor", GL_SHORT, 3, NORMALIZE_INT_TO_FLOAT);
		}

		const int vertex_ct = mesh_render_data_verts_num_get(mrdata);

		cache->pos_in_order = VertexBuffer_create_with_format(&format);
		VertexBuffer_allocate_data(cache->pos_in_order, vertex_ct);
		for (int i = 0; i < vertex_ct; ++i) {
			setAttrib(cache->pos_in_order, pos_id, i, mesh_render_data_vert_co(mrdata, i));
			setAttrib(cache->pos_in_order, nor_id, i, mesh_render_data_vert_nor(mrdata, i));
		}
	}

	return cache->pos_in_order;
}

static ElementList *mesh_batch_cache_get_edges_in_order(MeshRenderData *mrdata, MeshBatchCache *cache)
{
	BLI_assert(mrdata->types & (MR_DATATYPE_VERT | MR_DATATYPE_EDGE));

	if (cache->edges_in_order == NULL) {
		printf("Caching edges in order...\n");
		const int vertex_ct = mesh_render_data_verts_num_get(mrdata);
		const int edge_ct = mesh_render_data_edges_num_get(mrdata);

		ElementListBuilder elb;
		ElementListBuilder_init(&elb, GL_LINES, edge_ct, vertex_ct);
		for (int i = 0; i < edge_ct; ++i) {
			int vert_idx[2];
			mesh_render_data_edge_verts_indices_get(mrdata, i, vert_idx);
			add_line_vertices(&elb, vert_idx[0], vert_idx[1]);
		}
		cache->edges_in_order = ElementList_build(&elb);
	}

	return cache->edges_in_order;
}

static ElementList *mesh_batch_cache_get_triangles_in_order(MeshRenderData *mrdata, MeshBatchCache *cache)
{
	BLI_assert(mrdata->types & (MR_DATATYPE_VERT | MR_DATATYPE_LOOPTRI));

	if (cache->triangles_in_order == NULL) {
		const int vertex_ct = mesh_render_data_verts_num_get(mrdata);
		const int tri_ct = mesh_render_data_looptri_num_get(mrdata);

		ElementListBuilder elb;
		ElementListBuilder_init(&elb, GL_TRIANGLES, tri_ct, vertex_ct);
		for (int i = 0; i < tri_ct; ++i) {
			int tri_vert_idx[3];
			mesh_render_data_looptri_verts_indices_get(mrdata, i, tri_vert_idx);

			add_triangle_vertices(&elb, tri_vert_idx[0], tri_vert_idx[1], tri_vert_idx[2]);
		}
		cache->triangles_in_order = ElementList_build(&elb);
	}

	return cache->triangles_in_order;
}

Batch *BKE_mesh_batch_cache_get_all_edges(Mesh *me)
{
	MeshBatchCache *cache = mesh_batch_cache_get(me);

	if (cache->all_edges == NULL) {
		/* create batch from Mesh */
		MeshRenderData *mrdata = mesh_render_data_create(me, MR_DATATYPE_VERT | MR_DATATYPE_EDGE);

		cache->all_edges = Batch_create(GL_LINES, mesh_batch_cache_get_pos_and_nor_in_order(mrdata, cache),
		                                mesh_batch_cache_get_edges_in_order(mrdata, cache));

		mesh_render_data_free(mrdata);
	}

	return cache->all_edges;
}

Batch *BKE_mesh_batch_cache_get_all_triangles(Mesh *me)
{
	MeshBatchCache *cache = mesh_batch_cache_get(me);

	if (cache->all_triangles == NULL) {
		/* create batch from DM */
		MeshRenderData *mrdata = mesh_render_data_create(me, MR_DATATYPE_VERT | MR_DATATYPE_LOOPTRI);

		cache->all_triangles = Batch_create(GL_TRIANGLES, mesh_batch_cache_get_pos_and_nor_in_order(mrdata, cache),
		                                    mesh_batch_cache_get_triangles_in_order(mrdata, cache));

		mesh_render_data_free(mrdata);
	}

	return cache->all_triangles;
}

Batch *BKE_mesh_batch_cache_get_triangles_with_normals(Mesh *me)
{
	MeshBatchCache *cache = mesh_batch_cache_get(me);

	if (cache->triangles_with_normals == NULL) {
		MeshRenderData *mrdata = mesh_render_data_create(me, MR_DATATYPE_VERT | MR_DATATYPE_LOOPTRI | MR_DATATYPE_LOOP | MR_DATATYPE_POLY);

		cache->triangles_with_normals = Batch_create(GL_TRIANGLES, mesh_batch_cache_get_pos_and_normals(mrdata, cache), NULL);

		mesh_render_data_free(mrdata);
	}

	return cache->triangles_with_normals;
}

Batch *BKE_mesh_batch_cache_get_points_with_normals(Mesh *me)
{
	MeshBatchCache *cache = mesh_batch_cache_get(me);

	if (cache->points_with_normals == NULL) {
		MeshRenderData *mrdata = mesh_render_data_create(me, MR_DATATYPE_VERT | MR_DATATYPE_LOOPTRI | MR_DATATYPE_LOOP | MR_DATATYPE_POLY);

		cache->points_with_normals = Batch_create(GL_POINTS, mesh_batch_cache_get_pos_and_normals(mrdata, cache), NULL);

		mesh_render_data_free(mrdata);
	}

	return cache->points_with_normals;
}

Batch *BKE_mesh_batch_cache_get_all_verts(Mesh *me)
{
	MeshBatchCache *cache = mesh_batch_cache_get(me);

	if (cache->all_verts == NULL) {
		/* create batch from DM */
		MeshRenderData *mrdata = mesh_render_data_create(me, MR_DATATYPE_VERT);

		cache->all_verts = Batch_create(GL_POINTS, mesh_batch_cache_get_pos_and_nor_in_order(mrdata, cache), NULL);

		mesh_render_data_free(mrdata);
	}

	return cache->all_verts;
}

Batch *BKE_mesh_batch_cache_get_fancy_edges(Mesh *me)
{
	MeshBatchCache *cache = mesh_batch_cache_get(me);

	if (cache->fancy_edges == NULL) {
		/* create batch from DM */
		static VertexFormat format = { 0 };
		static unsigned int pos_id, n1_id, n2_id;
		if (format.attrib_ct == 0) {
			/* initialize vertex format */
			pos_id = add_attrib(&format, "pos", COMP_F32, 3, KEEP_FLOAT);

#if USE_10_10_10 /* takes 1/3 the space */
			n1_id = add_attrib(&format, "N1", COMP_I10, 3, NORMALIZE_INT_TO_FLOAT);
			n2_id = add_attrib(&format, "N2", COMP_I10, 3, NORMALIZE_INT_TO_FLOAT);
#else
			n1_id = add_attrib(&format, "N1", COMP_F32, 3, KEEP_FLOAT);
			n2_id = add_attrib(&format, "N2", COMP_F32, 3, KEEP_FLOAT);
#endif
		}
		VertexBuffer *vbo = VertexBuffer_create_with_format(&format);

		MeshRenderData *mrdata = mesh_render_data_create(me, MR_DATATYPE_VERT | MR_DATATYPE_EDGE | MR_DATATYPE_LOOP | MR_DATATYPE_POLY);

		const int edge_ct = mesh_render_data_edges_num_get(mrdata);

		const int vertex_ct = edge_ct * 2; /* these are GL_LINE verts, not mesh verts */
		VertexBuffer_allocate_data(vbo, vertex_ct);
		for (int i = 0; i < edge_ct; ++i) {
			float *vcos1, *vcos2;
			float *pnor1 = NULL, *pnor2 = NULL;
			const bool is_manifold = mesh_render_data_edge_vcos_manifold_pnors(mrdata, i, &vcos1, &vcos2, &pnor1, &pnor2);

#if USE_10_10_10
			PackedNormal n1value = { .x = 0, .y = 0, .z = +511 };
			PackedNormal n2value = { .x = 0, .y = 0, .z = -511 };

			if (is_manifold) {
				n1value = convert_i10_v3(pnor1);
				n2value = convert_i10_v3(pnor2);
			}

			const PackedNormal *n1 = &n1value;
			const PackedNormal *n2 = &n2value;
#else
			const float dummy1[3] = { 0.0f, 0.0f, +1.0f };
			const float dummy2[3] = { 0.0f, 0.0f, -1.0f };

			const float *n1 = (is_manifold) ? pnor1 : dummy1;
			const float *n2 = (is_manifold) ? pnor2 : dummy2;
#endif

			setAttrib(vbo, pos_id, 2 * i, vcos1);
			setAttrib(vbo, n1_id, 2 * i, n1);
			setAttrib(vbo, n2_id, 2 * i, n2);

			setAttrib(vbo, pos_id, 2 * i + 1, vcos2);
			setAttrib(vbo, n1_id, 2 * i + 1, n1);
			setAttrib(vbo, n2_id, 2 * i + 1, n2);
		}

		cache->fancy_edges = Batch_create(GL_LINES, vbo, NULL);

		mesh_render_data_free(mrdata);
	}

	return cache->fancy_edges;
}

static void mesh_batch_cache_create_overlay_batches(Mesh *me)
{
	/* Since MR_DATATYPE_OVERLAY is slow to generate, generate them all at once */
	int options = MR_DATATYPE_VERT | MR_DATATYPE_EDGE | MR_DATATYPE_LOOPTRI | MR_DATATYPE_OVERLAY;

	MeshBatchCache *cache = mesh_batch_cache_get(me);
	MeshRenderData *mrdata = mesh_render_data_create(me, options);

	static VertexFormat format = { 0 };
	static unsigned pos_id, data_id;
	if (format.attrib_ct == 0) {
		/* initialize vertex format */
		pos_id = add_attrib(&format, "pos", GL_FLOAT, 3, KEEP_FLOAT);
		data_id = add_attrib(&format, "data", GL_UNSIGNED_BYTE, 4, KEEP_INT);
	}

	const int tri_ct = mesh_render_data_looptri_num_get(mrdata);
	const int ledge_ct = mesh_render_data_loose_edges_num_get(mrdata);
	const int lvert_ct = mesh_render_data_loose_verts_num_get(mrdata);

	if (cache->overlay_triangles == NULL) {
		VertexBuffer *vbo = VertexBuffer_create_with_format(&format);
		VertexBuffer_allocate_data(vbo, tri_ct * 3);

		int gpu_vert_idx = 0;
		for (int i = 0; i < tri_ct; ++i) {
			int tri_vert_idx[3];
			mesh_render_data_looptri_verts_indices_get(mrdata, i, tri_vert_idx);
			add_overlay_tri(mrdata, vbo, pos_id, data_id,
			                tri_vert_idx[0], tri_vert_idx[1], tri_vert_idx[2], i, gpu_vert_idx);
			gpu_vert_idx += 3;
		}

		cache->overlay_triangles = Batch_create(GL_TRIANGLES, vbo, NULL);
	}

	if (cache->overlay_loose_edges == NULL) {
		VertexBuffer *vbo = VertexBuffer_create_with_format(&format);
		VertexBuffer_allocate_data(vbo, ledge_ct * 2);

		int gpu_vert_idx = 0;
		for (int i = 0; i < ledge_ct; ++i) {
			int vert_idx[2];
			mesh_render_data_edge_verts_indices_get(mrdata, mrdata->loose_edges[i], vert_idx);
			add_overlay_loose_edge(mrdata, vbo, pos_id, data_id,
			                       vert_idx[0], vert_idx[1], mrdata->loose_edges[i], gpu_vert_idx);
			gpu_vert_idx += 2;
		}
		cache->overlay_loose_edges = Batch_create(GL_LINES, vbo, NULL);
	}

	if (cache->overlay_loose_verts == NULL) {
		VertexBuffer *vbo = VertexBuffer_create_with_format(&format);
		VertexBuffer_allocate_data(vbo, lvert_ct);

		int gpu_vert_idx = 0;
		for (int i = 0; i < lvert_ct; ++i) {
			add_overlay_loose_vert(mrdata, vbo, pos_id, data_id,
			                       mrdata->loose_verts[i], gpu_vert_idx);
			gpu_vert_idx += 1;
		}
		cache->overlay_loose_verts = Batch_create(GL_POINTS, vbo, NULL);
	}

	mesh_render_data_free(mrdata);
}

Batch *BKE_mesh_batch_cache_get_overlay_triangles(Mesh *me)
{
	MeshBatchCache *cache = mesh_batch_cache_get(me);

	if (cache->overlay_triangles == NULL) {
		mesh_batch_cache_create_overlay_batches(me);
	}

	return cache->overlay_triangles;
}

Batch *BKE_mesh_batch_cache_get_overlay_loose_edges(Mesh *me)
{
	MeshBatchCache *cache = mesh_batch_cache_get(me);

	if (cache->overlay_loose_edges == NULL) {
		mesh_batch_cache_create_overlay_batches(me);
	}

	return cache->overlay_loose_edges;
}

Batch *BKE_mesh_batch_cache_get_overlay_loose_verts(Mesh *me)
{
	MeshBatchCache *cache = mesh_batch_cache_get(me);

	if (cache->overlay_loose_verts == NULL) {
		mesh_batch_cache_create_overlay_batches(me);
	}

	return cache->overlay_loose_verts;
}

Batch *BKE_mesh_batch_cache_get_overlay_facedots(Mesh *me)
{
	MeshBatchCache *cache = mesh_batch_cache_get(me);

	if (cache->overlay_facedots == NULL) {
		MeshRenderData *mrdata = mesh_render_data_create(me, MR_DATATYPE_VERT | MR_DATATYPE_LOOP | MR_DATATYPE_POLY);

		static VertexFormat format = { 0 };
		static unsigned pos_id, data_id;
		if (format.attrib_ct == 0) {
			/* initialize vertex format */
			pos_id = add_attrib(&format, "pos", GL_FLOAT, 3, KEEP_FLOAT);
#if USE_10_10_10
			data_id = add_attrib(&format, "norAndFlag", COMP_I10, 4, NORMALIZE_INT_TO_FLOAT);
#else
			data_id = add_attrib(&format, "norAndFlag", GL_FLOAT, 4, KEEP_FLOAT);
#endif
		}

		const int poly_ct = mesh_render_data_polys_num_get(mrdata);

		VertexBuffer *vbo = VertexBuffer_create_with_format(&format);
		VertexBuffer_allocate_data(vbo, poly_ct);

		for (int i = 0; i < poly_ct; ++i) {
			float pcenter[3], pnor[3];
			int selected = 0;

			mesh_render_data_pnors_pcenter_select_get(mrdata, i, pnor, pcenter, (bool *)&selected);

#if USE_10_10_10
			PackedNormal nor = { .x = 0, .y = 0, .z = -511 };
			nor = convert_i10_v3(pnor);
			nor.w = selected;
			setAttrib(vbo, data_id, i, &nor);
#else
			float nor[4] = {pnor[0], pnor[1], pnor[2], (float)selected};
			setAttrib(vbo, data_id, i, nor);
#endif

			setAttrib(vbo, pos_id, i, pcenter);
		}

		cache->overlay_facedots = Batch_create(GL_POINTS, vbo, NULL);

		mesh_render_data_free(mrdata);
	}

	return cache->overlay_facedots;
}

#undef MESH_RENDER_FUNCTION

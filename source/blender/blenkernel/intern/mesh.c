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
 * The Original Code is Copyright (C) 2001-2002 by NaN Holding BV.
 * All rights reserved.
 *
 * Contributor(s): Blender Foundation
 *
 * ***** END GPL LICENSE BLOCK *****
 */

/** \file blender/blenkernel/intern/mesh.c
 *  \ingroup bke
 */

#include "MEM_guardedalloc.h"

#include "DNA_object_types.h"
#include "DNA_key_types.h"
#include "DNA_mesh_types.h"

#include "BLI_utildefines.h"
#include "BLI_math.h"
#include "BLI_linklist.h"
#include "BLI_memarena.h"
#include "BLI_edgehash.h"
#include "BLI_string.h"

#include "BKE_animsys.h"
#include "BKE_main.h"
#include "BKE_DerivedMesh.h"
#include "BKE_global.h"
#include "BKE_mesh.h"
#include "BKE_library.h"
#include "BKE_material.h"
#include "BKE_modifier.h"
#include "BKE_multires.h"
#include "BKE_depsgraph.h"
#include "BKE_object.h"
#include "BKE_editmesh.h"

#include "DEG_depsgraph.h"

enum {
	MESHCMP_DVERT_WEIGHTMISMATCH = 1,
	MESHCMP_DVERT_GROUPMISMATCH,
	MESHCMP_DVERT_TOTGROUPMISMATCH,
	MESHCMP_LOOPCOLMISMATCH,
	MESHCMP_LOOPUVMISMATCH,
	MESHCMP_LOOPMISMATCH,
	MESHCMP_POLYVERTMISMATCH,
	MESHCMP_POLYMISMATCH,
	MESHCMP_EDGEUNKNOWN,
	MESHCMP_VERTCOMISMATCH,
	MESHCMP_CDLAYERS_MISMATCH
};

static const char *cmpcode_to_str(int code)
{
	switch (code) {
		case MESHCMP_DVERT_WEIGHTMISMATCH:
			return "Vertex Weight Mismatch";
		case MESHCMP_DVERT_GROUPMISMATCH:
			return "Vertex Group Mismatch";
		case MESHCMP_DVERT_TOTGROUPMISMATCH:
			return "Vertex Doesn't Belong To Same Number Of Groups";
		case MESHCMP_LOOPCOLMISMATCH:
			return "Vertex Color Mismatch";
		case MESHCMP_LOOPUVMISMATCH:
			return "UV Mismatch";
		case MESHCMP_LOOPMISMATCH:
			return "Loop Mismatch";
		case MESHCMP_POLYVERTMISMATCH:
			return "Loop Vert Mismatch In Poly Test";
		case MESHCMP_POLYMISMATCH:
			return "Loop Vert Mismatch";
		case MESHCMP_EDGEUNKNOWN:
			return "Edge Mismatch";
		case MESHCMP_VERTCOMISMATCH:
			return "Vertex Coordinate Mismatch";
		case MESHCMP_CDLAYERS_MISMATCH:
			return "CustomData Layer Count Mismatch";
		default:
			return "Mesh Comparison Code Unknown";
	}
}

/* thresh is threshold for comparing vertices, uvs, vertex colors,
 * weights, etc.*/
static int customdata_compare(CustomData *c1, CustomData *c2, Mesh *m1, Mesh *m2, const float thresh)
{
	const float thresh_sq = thresh * thresh;
	CustomDataLayer *l1, *l2;
	int i, i1 = 0, i2 = 0, tot, j;

	for (i = 0; i < c1->totlayer; i++) {
		if (ELEM(c1->layers[i].type, CD_MVERT, CD_MEDGE, CD_MPOLY,
		         CD_MLOOPUV, CD_MLOOPCOL, CD_MTEXPOLY, CD_MDEFORMVERT))
		{
			i1++;
		}
	}

	for (i = 0; i < c2->totlayer; i++) {
		if (ELEM(c2->layers[i].type, CD_MVERT, CD_MEDGE, CD_MPOLY,
		         CD_MLOOPUV, CD_MLOOPCOL, CD_MTEXPOLY, CD_MDEFORMVERT))
		{
			i2++;
		}
	}

	if (i1 != i2)
		return MESHCMP_CDLAYERS_MISMATCH;

	l1 = c1->layers; l2 = c2->layers;
	tot = i1;
	i1 = 0; i2 = 0;
	for (i = 0; i < tot; i++) {
		while (i1 < c1->totlayer && !ELEM(l1->type, CD_MVERT, CD_MEDGE, CD_MPOLY,
		                                  CD_MLOOPUV, CD_MLOOPCOL, CD_MTEXPOLY, CD_MDEFORMVERT))
		{
			i1++;
			l1++;
		}

		while (i2 < c2->totlayer && !ELEM(l2->type, CD_MVERT, CD_MEDGE, CD_MPOLY,
		                                  CD_MLOOPUV, CD_MLOOPCOL, CD_MTEXPOLY, CD_MDEFORMVERT))
		{
			i2++;
			l2++;
		}

		if (l1->type == CD_MVERT) {
			MVert *v1 = l1->data;
			MVert *v2 = l2->data;
			int vtot = m1->totvert;

			for (j = 0; j < vtot; j++, v1++, v2++) {
				if (len_squared_v3v3(v1->co, v2->co) > thresh_sq)
					return MESHCMP_VERTCOMISMATCH;
				/* I don't care about normals, let's just do coodinates */
			}
		}

		/*we're order-agnostic for edges here*/
		if (l1->type == CD_MEDGE) {
			MEdge *e1 = l1->data;
			MEdge *e2 = l2->data;
			int etot = m1->totedge;
			EdgeHash *eh = BLI_edgehash_new_ex(__func__, etot);

			for (j = 0; j < etot; j++, e1++) {
				BLI_edgehash_insert(eh, e1->v1, e1->v2, e1);
			}

			for (j = 0; j < etot; j++, e2++) {
				if (!BLI_edgehash_lookup(eh, e2->v1, e2->v2))
					return MESHCMP_EDGEUNKNOWN;
			}
			BLI_edgehash_free(eh, NULL);
		}

		if (l1->type == CD_MPOLY) {
			MPoly *p1 = l1->data;
			MPoly *p2 = l2->data;
			int ptot = m1->totpoly;

			for (j = 0; j < ptot; j++, p1++, p2++) {
				MLoop *lp1, *lp2;
				int k;

				if (p1->totloop != p2->totloop)
					return MESHCMP_POLYMISMATCH;

				lp1 = m1->mloop + p1->loopstart;
				lp2 = m2->mloop + p2->loopstart;

				for (k = 0; k < p1->totloop; k++, lp1++, lp2++) {
					if (lp1->v != lp2->v)
						return MESHCMP_POLYVERTMISMATCH;
				}
			}
		}
		if (l1->type == CD_MLOOP) {
			MLoop *lp1 = l1->data;
			MLoop *lp2 = l2->data;
			int ltot = m1->totloop;

			for (j = 0; j < ltot; j++, lp1++, lp2++) {
				if (lp1->v != lp2->v)
					return MESHCMP_LOOPMISMATCH;
			}
		}
		if (l1->type == CD_MLOOPUV) {
			MLoopUV *lp1 = l1->data;
			MLoopUV *lp2 = l2->data;
			int ltot = m1->totloop;

			for (j = 0; j < ltot; j++, lp1++, lp2++) {
				if (len_squared_v2v2(lp1->uv, lp2->uv) > thresh_sq)
					return MESHCMP_LOOPUVMISMATCH;
			}
		}

		if (l1->type == CD_MLOOPCOL) {
			MLoopCol *lp1 = l1->data;
			MLoopCol *lp2 = l2->data;
			int ltot = m1->totloop;

			for (j = 0; j < ltot; j++, lp1++, lp2++) {
				if (ABS(lp1->r - lp2->r) > thresh ||
				    ABS(lp1->g - lp2->g) > thresh ||
				    ABS(lp1->b - lp2->b) > thresh ||
				    ABS(lp1->a - lp2->a) > thresh)
				{
					return MESHCMP_LOOPCOLMISMATCH;
				}
			}
		}

		if (l1->type == CD_MDEFORMVERT) {
			MDeformVert *dv1 = l1->data;
			MDeformVert *dv2 = l2->data;
			int dvtot = m1->totvert;

			for (j = 0; j < dvtot; j++, dv1++, dv2++) {
				int k;
				MDeformWeight *dw1 = dv1->dw, *dw2 = dv2->dw;

				if (dv1->totweight != dv2->totweight)
					return MESHCMP_DVERT_TOTGROUPMISMATCH;

				for (k = 0; k < dv1->totweight; k++, dw1++, dw2++) {
					if (dw1->def_nr != dw2->def_nr)
						return MESHCMP_DVERT_GROUPMISMATCH;
					if (fabsf(dw1->weight - dw2->weight) > thresh)
						return MESHCMP_DVERT_WEIGHTMISMATCH;
				}
			}
		}
	}

	return 0;
}

/**
 * Used for unit testing; compares two meshes, checking only
 * differences we care about.  should be usable with leaf's
 * testing framework I get RNA work done, will use hackish
 * testing code for now.
 */
const char *BKE_mesh_cmp(Mesh *me1, Mesh *me2, float thresh)
{
	int c;

	if (!me1 || !me2)
		return "Requires two input meshes";

	if (me1->totvert != me2->totvert)
		return "Number of verts don't match";

	if (me1->totedge != me2->totedge)
		return "Number of edges don't match";

	if (me1->totpoly != me2->totpoly)
		return "Number of faces don't match";

	if (me1->totloop != me2->totloop)
		return "Number of loops don't match";

	if ((c = customdata_compare(&me1->vdata, &me2->vdata, me1, me2, thresh)))
		return cmpcode_to_str(c);

	if ((c = customdata_compare(&me1->edata, &me2->edata, me1, me2, thresh)))
		return cmpcode_to_str(c);

	if ((c = customdata_compare(&me1->ldata, &me2->ldata, me1, me2, thresh)))
		return cmpcode_to_str(c);

	if ((c = customdata_compare(&me1->pdata, &me2->pdata, me1, me2, thresh)))
		return cmpcode_to_str(c);

	return NULL;
}

static void mesh_ensure_tessellation_customdata(Mesh *me)
{
	if (UNLIKELY((me->totface != 0) && (me->totpoly == 0))) {
		/* Pass, otherwise this function  clears 'mface' before
		 * versioning 'mface -> mpoly' code kicks in [#30583]
		 *
		 * Callers could also check but safer to do here - campbell */
	}
	else {
		const int tottex_original = CustomData_number_of_layers(&me->pdata, CD_MTEXPOLY);
		const int totcol_original = CustomData_number_of_layers(&me->ldata, CD_MLOOPCOL);

		const int tottex_tessface = CustomData_number_of_layers(&me->fdata, CD_MTFACE);
		const int totcol_tessface = CustomData_number_of_layers(&me->fdata, CD_MCOL);

		if (tottex_tessface != tottex_original ||
		    totcol_tessface != totcol_original)
		{
			BKE_mesh_tessface_clear(me);

			CustomData_from_bmeshpoly(&me->fdata, &me->pdata, &me->ldata, me->totface);

			/* TODO - add some --debug-mesh option */
			if (G.debug & G_DEBUG) {
				/* note: this warning may be un-called for if we are initializing the mesh for the
				 * first time from bmesh, rather then giving a warning about this we could be smarter
				 * and check if there was any data to begin with, for now just print the warning with
				 * some info to help troubleshoot whats going on - campbell */
				printf("%s: warning! Tessellation uvs or vcol data got out of sync, "
				       "had to reset!\n    CD_MTFACE: %d != CD_MTEXPOLY: %d || CD_MCOL: %d != CD_MLOOPCOL: %d\n",
				       __func__, tottex_tessface, tottex_original, totcol_tessface, totcol_original);
			}
		}
	}
}

void BKE_mesh_ensure_skin_customdata(Mesh *me)
{
	BMesh *bm = me->edit_btmesh ? me->edit_btmesh->bm : NULL;
	MVertSkin *vs;

	if (bm) {
		if (!CustomData_has_layer(&bm->vdata, CD_MVERT_SKIN)) {
			BMVert *v;
			BMIter iter;

			BM_data_layer_add(bm, &bm->vdata, CD_MVERT_SKIN);

			/* Mark an arbitrary vertex as root */
			BM_ITER_MESH (v, &iter, bm, BM_VERTS_OF_MESH) {
				vs = CustomData_bmesh_get(
				        &bm->vdata, v->head.data,
				        CD_MVERT_SKIN);
				vs->flag |= MVERT_SKIN_ROOT;
				break;
			}
		}
	}
	else {
		if (!CustomData_has_layer(&me->vdata, CD_MVERT_SKIN)) {
			vs = CustomData_add_layer(
			        &me->vdata,
			        CD_MVERT_SKIN,
			        CD_DEFAULT,
			        NULL,
			        me->totvert);

			/* Mark an arbitrary vertex as root */
			if (vs) {
				vs->flag |= MVERT_SKIN_ROOT;
			}
		}
	}
}

/* this ensures grouped customdata (e.g. mtexpoly and mloopuv and mtface, or
 * mloopcol and mcol) have the same relative active/render/clone/mask indices.
 *
 * note that for undo mesh data we want to skip 'ensure_tess_cd' call since
 * we don't want to store memory for tessface when its only used for older
 * versions of the mesh. - campbell*/
static void mesh_update_linked_customdata(Mesh *me, const bool do_ensure_tess_cd)
{
	if (me->edit_btmesh)
		BKE_editmesh_update_linked_customdata(me->edit_btmesh);

	if (do_ensure_tess_cd) {
		mesh_ensure_tessellation_customdata(me);
	}

	CustomData_bmesh_update_active_layers(&me->fdata, &me->pdata, &me->ldata);
}

void BKE_mesh_update_customdata_pointers(Mesh *me, const bool do_ensure_tess_cd)
{
	mesh_update_linked_customdata(me, do_ensure_tess_cd);

	me->mvert = CustomData_get_layer(&me->vdata, CD_MVERT);
	me->dvert = CustomData_get_layer(&me->vdata, CD_MDEFORMVERT);

	me->medge = CustomData_get_layer(&me->edata, CD_MEDGE);

	me->mface = CustomData_get_layer(&me->fdata, CD_MFACE);
	me->mcol = CustomData_get_layer(&me->fdata, CD_MCOL);
	me->mtface = CustomData_get_layer(&me->fdata, CD_MTFACE);

	me->mpoly = CustomData_get_layer(&me->pdata, CD_MPOLY);
	me->mloop = CustomData_get_layer(&me->ldata, CD_MLOOP);

	me->mtpoly = CustomData_get_layer(&me->pdata, CD_MTEXPOLY);
	me->mloopcol = CustomData_get_layer(&me->ldata, CD_MLOOPCOL);
	me->mloopuv = CustomData_get_layer(&me->ldata, CD_MLOOPUV);
}

bool BKE_mesh_has_custom_loop_normals(Mesh *me)
{
	if (me->edit_btmesh) {
		return CustomData_has_layer(&me->edit_btmesh->bm->ldata, CD_CUSTOMLOOPNORMAL);
	}
	else {
		return CustomData_has_layer(&me->ldata, CD_CUSTOMLOOPNORMAL);
	}
}

/** Free (or release) any data used by this mesh (does not free the mesh itself). */
void BKE_mesh_free(Mesh *me)
{
	BKE_animdata_free(&me->id, false);

	CustomData_free(&me->vdata, me->totvert);
	CustomData_free(&me->edata, me->totedge);
	CustomData_free(&me->fdata, me->totface);
	CustomData_free(&me->ldata, me->totloop);
	CustomData_free(&me->pdata, me->totpoly);

	MEM_SAFE_FREE(me->mat);
	MEM_SAFE_FREE(me->bb);
	MEM_SAFE_FREE(me->mselect);
	MEM_SAFE_FREE(me->edit_btmesh);
}

static void mesh_tessface_clear_intern(Mesh *mesh, int free_customdata)
{
	if (free_customdata) {
		CustomData_free(&mesh->fdata, mesh->totface);
	}
	else {
		CustomData_reset(&mesh->fdata);
	}

	mesh->mface = NULL;
	mesh->mtface = NULL;
	mesh->mcol = NULL;
	mesh->totface = 0;
}

void BKE_mesh_init(Mesh *me)
{
	BLI_assert(MEMCMP_STRUCT_OFS_IS_ZERO(me, id));

	me->size[0] = me->size[1] = me->size[2] = 1.0;
	me->smoothresh = DEG2RADF(30);
	me->texflag = ME_AUTOSPACE;

	/* disable because its slow on many GPU's, see [#37518] */
#if 0
	me->flag = ME_TWOSIDED;
#endif
	me->drawflag = ME_DRAWEDGES | ME_DRAWFACES | ME_DRAWCREASES;

	CustomData_reset(&me->vdata);
	CustomData_reset(&me->edata);
	CustomData_reset(&me->fdata);
	CustomData_reset(&me->pdata);
	CustomData_reset(&me->ldata);
}

Mesh *BKE_mesh_add(Main *bmain, const char *name)
{
	Mesh *me;

	me = BKE_libblock_alloc(bmain, ID_ME, name, 0);

	BKE_mesh_init(me);

	return me;
}

/**
 * Only copy internal data of Mesh ID from source to already allocated/initialized destination.
 * You probably nerver want to use that directly, use id_copy or BKE_id_copy_ex for typical needs.
 *
 * WARNING! This function will not handle ID user count!
 *
 * \param flag  Copying options (see BKE_library.h's LIB_ID_COPY_... flags for more).
 */
void BKE_mesh_copy_data(Main *bmain, Mesh *me_dst, const Mesh *me_src, const int flag)
{
	const bool do_tessface = ((me_src->totface != 0) && (me_src->totpoly == 0)); /* only do tessface if we have no polys */

	me_dst->mat = MEM_dupallocN(me_src->mat);

	CustomData_copy(&me_src->vdata, &me_dst->vdata, CD_MASK_MESH, CD_DUPLICATE, me_dst->totvert);
	CustomData_copy(&me_src->edata, &me_dst->edata, CD_MASK_MESH, CD_DUPLICATE, me_dst->totedge);
	CustomData_copy(&me_src->ldata, &me_dst->ldata, CD_MASK_MESH, CD_DUPLICATE, me_dst->totloop);
	CustomData_copy(&me_src->pdata, &me_dst->pdata, CD_MASK_MESH, CD_DUPLICATE, me_dst->totpoly);
	if (do_tessface) {
		CustomData_copy(&me_src->fdata, &me_dst->fdata, CD_MASK_MESH, CD_DUPLICATE, me_dst->totface);
	}
	else {
		mesh_tessface_clear_intern(me_dst, false);
	}

	BKE_mesh_update_customdata_pointers(me_dst, do_tessface);

	me_dst->edit_btmesh = NULL;

	me_dst->mselect = MEM_dupallocN(me_dst->mselect);
	me_dst->bb = MEM_dupallocN(me_dst->bb);

	/* TODO Do we want to add flag to prevent this? */
	if (me_src->key) {
		BKE_id_copy_ex(bmain, &me_src->key->id, (ID **)&me_dst->key, flag, false);
	}
}

Mesh *BKE_mesh_copy(Main *bmain, const Mesh *me)
{
	Mesh *me_copy;
	BKE_id_copy_ex(bmain, &me->id, (ID **)&me_copy, 0, false);
	return me_copy;
}

BMesh *BKE_mesh_to_bmesh(
        Mesh *me, Object *ob,
        const bool add_key_index, const struct BMeshCreateParams *params)
{
	BMesh *bm;
	const BMAllocTemplate allocsize = BMALLOC_TEMPLATE_FROM_ME(me);

	bm = BM_mesh_create(&allocsize, params);

	BM_mesh_bm_from_me(
	        bm, me, (&(struct BMeshFromMeshParams){
	            .add_key_index = add_key_index, .use_shapekey = true, .active_shapekey = ob->shapenr,
	        }));

	return bm;
}

void BKE_mesh_make_local(Main *bmain, Mesh *me, const bool lib_local)
{
	BKE_id_make_local_generic(bmain, &me->id, true, lib_local);
}

bool BKE_mesh_uv_cdlayer_rename_index(
        Mesh *me, const int poly_index, const int loop_index, const int face_index,
        const char *new_name, const bool do_tessface)
{
	CustomData *pdata, *ldata, *fdata;
	CustomDataLayer *cdlp, *cdlu, *cdlf;
	const int step = do_tessface ? 3 : 2;
	int i;

	if (me->edit_btmesh) {
		pdata = &me->edit_btmesh->bm->pdata;
		ldata = &me->edit_btmesh->bm->ldata;
		fdata = NULL;  /* No tessellated data in BMesh! */
	}
	else {
		pdata = &me->pdata;
		ldata = &me->ldata;
		fdata = &me->fdata;
	}
	cdlp = &pdata->layers[poly_index];
	cdlu = &ldata->layers[loop_index];
	cdlf = fdata && do_tessface ? &fdata->layers[face_index] : NULL;

	if (cdlp->name != new_name) {
		/* Mesh validate passes a name from the CD layer as the new name,
		 * Avoid memcpy from self to self in this case.
		 */
		BLI_strncpy(cdlp->name, new_name, sizeof(cdlp->name));
		CustomData_set_layer_unique_name(pdata, cdlp - pdata->layers);
	}

	/* Loop until we do have exactly the same name for all layers! */
	for (i = 1; !STREQ(cdlp->name, cdlu->name) || (cdlf && !STREQ(cdlp->name, cdlf->name)); i++) {
		switch (i % step) {
			case 0:
				BLI_strncpy(cdlp->name, cdlu->name, sizeof(cdlp->name));
				CustomData_set_layer_unique_name(pdata, cdlp - pdata->layers);
				break;
			case 1:
				BLI_strncpy(cdlu->name, cdlp->name, sizeof(cdlu->name));
				CustomData_set_layer_unique_name(ldata, cdlu - ldata->layers);
				break;
			case 2:
				if (cdlf) {
					BLI_strncpy(cdlf->name, cdlp->name, sizeof(cdlf->name));
					CustomData_set_layer_unique_name(fdata, cdlf - fdata->layers);
				}
				break;
		}
	}

	return true;
}

bool BKE_mesh_uv_cdlayer_rename(Mesh *me, const char *old_name, const char *new_name, bool do_tessface)
{
	CustomData *pdata, *ldata, *fdata;
	if (me->edit_btmesh) {
		pdata = &me->edit_btmesh->bm->pdata;
		ldata = &me->edit_btmesh->bm->ldata;
		/* No tessellated data in BMesh! */
		fdata = NULL;
		do_tessface = false;
	}
	else {
		pdata = &me->pdata;
		ldata = &me->ldata;
		fdata = &me->fdata;
		do_tessface = (do_tessface && fdata->totlayer);
	}

	{
		const int pidx_start = CustomData_get_layer_index(pdata, CD_MTEXPOLY);
		const int lidx_start = CustomData_get_layer_index(ldata, CD_MLOOPUV);
		const int fidx_start = do_tessface ? CustomData_get_layer_index(fdata, CD_MTFACE) : -1;
		int pidx = CustomData_get_named_layer(pdata, CD_MTEXPOLY, old_name);
		int lidx = CustomData_get_named_layer(ldata, CD_MLOOPUV, old_name);
		int fidx = do_tessface ? CustomData_get_named_layer(fdata, CD_MTFACE, old_name) : -1;

		/* None of those cases should happen, in theory!
		 * Note this assume we have the same number of mtexpoly, mloopuv and mtface layers!
		 */
		if (pidx == -1) {
			if (lidx == -1) {
				if (fidx == -1) {
					/* No layer found with this name! */
					return false;
				}
				else {
					lidx = fidx;
				}
			}
			pidx = lidx;
		}
		else {
			if (lidx == -1) {
				lidx = pidx;
			}
			if (fidx == -1 && do_tessface) {
				fidx = pidx;
			}
		}
#if 0
		/* For now, we do not consider mismatch in indices (i.e. same name leading to (relative) different indices). */
		else if (pidx != lidx) {
			lidx = pidx;
		}
#endif

		/* Go back to absolute indices! */
		pidx += pidx_start;
		lidx += lidx_start;
		if (fidx != -1)
			fidx += fidx_start;

		return BKE_mesh_uv_cdlayer_rename_index(me, pidx, lidx, fidx, new_name, do_tessface);
	}
}

void BKE_mesh_boundbox_calc(Mesh *me, float r_loc[3], float r_size[3])
{
	BoundBox *bb;
	float min[3], max[3];
	float mloc[3], msize[3];

	if (me->bb == NULL) me->bb = MEM_callocN(sizeof(BoundBox), "boundbox");
	bb = me->bb;

	if (!r_loc) r_loc = mloc;
	if (!r_size) r_size = msize;

	INIT_MINMAX(min, max);
	if (!BKE_mesh_minmax(me, min, max)) {
		min[0] = min[1] = min[2] = -1.0f;
		max[0] = max[1] = max[2] = 1.0f;
	}

	mid_v3_v3v3(r_loc, min, max);

	r_size[0] = (max[0] - min[0]) / 2.0f;
	r_size[1] = (max[1] - min[1]) / 2.0f;
	r_size[2] = (max[2] - min[2]) / 2.0f;

	BKE_boundbox_init_from_minmax(bb, min, max);

	bb->flag &= ~BOUNDBOX_DIRTY;
}

void BKE_mesh_texspace_calc(Mesh *me)
{
	float loc[3], size[3];
	int a;

	BKE_mesh_boundbox_calc(me, loc, size);

	if (me->texflag & ME_AUTOSPACE) {
		for (a = 0; a < 3; a++) {
			if (size[a] == 0.0f) size[a] = 1.0f;
			else if (size[a] > 0.0f && size[a] < 0.00001f) size[a] = 0.00001f;
			else if (size[a] < 0.0f && size[a] > -0.00001f) size[a] = -0.00001f;
		}

		copy_v3_v3(me->loc, loc);
		copy_v3_v3(me->size, size);
		zero_v3(me->rot);
	}
}

BoundBox *BKE_mesh_boundbox_get(Object *ob)
{
	Mesh *me = ob->data;

	if (ob->bb)
		return ob->bb;

	if (me->bb == NULL || (me->bb->flag & BOUNDBOX_DIRTY)) {
		BKE_mesh_texspace_calc(me);
	}

	return me->bb;
}

void BKE_mesh_texspace_get(Mesh *me, float r_loc[3], float r_rot[3], float r_size[3])
{
	if (me->bb == NULL || (me->bb->flag & BOUNDBOX_DIRTY)) {
		BKE_mesh_texspace_calc(me);
	}

	if (r_loc) copy_v3_v3(r_loc,  me->loc);
	if (r_rot) copy_v3_v3(r_rot,  me->rot);
	if (r_size) copy_v3_v3(r_size, me->size);
}

void BKE_mesh_texspace_copy_from_object(Mesh *me, Object *ob)
{
	float *texloc, *texrot, *texsize;
	short *texflag;

	if (BKE_object_obdata_texspace_get(ob, &texflag, &texloc, &texsize, &texrot)) {
		me->texflag = *texflag;
		copy_v3_v3(me->loc, texloc);
		copy_v3_v3(me->size, texsize);
		copy_v3_v3(me->rot, texrot);
	}
}

float (*BKE_mesh_orco_verts_get(Object *ob))[3]
{
	Mesh *me = ob->data;
	MVert *mvert = NULL;
	Mesh *tme = me->texcomesh ? me->texcomesh : me;
	int a, totvert;
	float (*vcos)[3] = NULL;

	/* Get appropriate vertex coordinates */
	vcos = MEM_calloc_arrayN(me->totvert, sizeof(*vcos), "orco mesh");
	mvert = tme->mvert;
	totvert = min_ii(tme->totvert, me->totvert);

	for (a = 0; a < totvert; a++, mvert++) {
		copy_v3_v3(vcos[a], mvert->co);
	}

	return vcos;
}

void BKE_mesh_orco_verts_transform(Mesh *me, float (*orco)[3], int totvert, int invert)
{
	float loc[3], size[3];
	int a;

	BKE_mesh_texspace_get(me->texcomesh ? me->texcomesh : me, loc, NULL, size);

	if (invert) {
		for (a = 0; a < totvert; a++) {
			float *co = orco[a];
			madd_v3_v3v3v3(co, loc, co, size);
		}
	}
	else {
		for (a = 0; a < totvert; a++) {
			float *co = orco[a];
			co[0] = (co[0] - loc[0]) / size[0];
			co[1] = (co[1] - loc[1]) / size[1];
			co[2] = (co[2] - loc[2]) / size[2];
		}
	}
}

/* rotates the vertices of a face in case v[2] or v[3] (vertex index) is = 0.
 * this is necessary to make the if (mface->v4) check for quads work */
int test_index_face(MFace *mface, CustomData *fdata, int mfindex, int nr)
{
	/* first test if the face is legal */
	if ((mface->v3 || nr == 4) && mface->v3 == mface->v4) {
		mface->v4 = 0;
		nr--;
	}
	if ((mface->v2 || mface->v4) && mface->v2 == mface->v3) {
		mface->v3 = mface->v4;
		mface->v4 = 0;
		nr--;
	}
	if (mface->v1 == mface->v2) {
		mface->v2 = mface->v3;
		mface->v3 = mface->v4;
		mface->v4 = 0;
		nr--;
	}

	/* check corrupt cases, bow-tie geometry, cant handle these because edge data wont exist so just return 0 */
	if (nr == 3) {
		if (
		    /* real edges */
		    mface->v1 == mface->v2 ||
		    mface->v2 == mface->v3 ||
		    mface->v3 == mface->v1)
		{
			return 0;
		}
	}
	else if (nr == 4) {
		if (
		    /* real edges */
		    mface->v1 == mface->v2 ||
		    mface->v2 == mface->v3 ||
		    mface->v3 == mface->v4 ||
		    mface->v4 == mface->v1 ||
		    /* across the face */
		    mface->v1 == mface->v3 ||
		    mface->v2 == mface->v4)
		{
			return 0;
		}
	}

	/* prevent a zero at wrong index location */
	if (nr == 3) {
		if (mface->v3 == 0) {
			static int corner_indices[4] = {1, 2, 0, 3};

			SWAP(unsigned int, mface->v1, mface->v2);
			SWAP(unsigned int, mface->v2, mface->v3);

			if (fdata)
				CustomData_swap_corners(fdata, mfindex, corner_indices);
		}
	}
	else if (nr == 4) {
		if (mface->v3 == 0 || mface->v4 == 0) {
			static int corner_indices[4] = {2, 3, 0, 1};

			SWAP(unsigned int, mface->v1, mface->v3);
			SWAP(unsigned int, mface->v2, mface->v4);

			if (fdata)
				CustomData_swap_corners(fdata, mfindex, corner_indices);
		}
	}

	return nr;
}

Mesh *BKE_mesh_from_object(Object *ob)
{

	if (ob == NULL) return NULL;
	if (ob->type == OB_MESH) return ob->data;
	else return NULL;
}

void BKE_mesh_assign_object(Main *bmain, Object *ob, Mesh *me)
{
	Mesh *old = NULL;

	multires_force_update(ob);

	if (ob == NULL) return;

	if (ob->type == OB_MESH) {
		old = ob->data;
		if (old)
			id_us_min(&old->id);
		ob->data = me;
		id_us_plus((ID *)me);
	}

	test_object_materials(bmain, ob, (ID *)me);

	test_object_modifiers(ob);
}


void BKE_mesh_material_index_remove(Mesh *me, short index)
{
	MPoly *mp;
	MFace *mf;
	int i;

	for (mp = me->mpoly, i = 0; i < me->totpoly; i++, mp++) {
		if (mp->mat_nr && mp->mat_nr >= index) {
			mp->mat_nr--;
		}
	}

	for (mf = me->mface, i = 0; i < me->totface; i++, mf++) {
		if (mf->mat_nr && mf->mat_nr >= index) {
			mf->mat_nr--;
		}
	}
}

void BKE_mesh_material_index_clear(Mesh *me)
{
	MPoly *mp;
	MFace *mf;
	int i;

	for (mp = me->mpoly, i = 0; i < me->totpoly; i++, mp++) {
		mp->mat_nr = 0;
	}

	for (mf = me->mface, i = 0; i < me->totface; i++, mf++) {
		mf->mat_nr = 0;
	}
}

void BKE_mesh_material_remap(Mesh *me, const unsigned int *remap, unsigned int remap_len)
{
	const short remap_len_short = (short)remap_len;

#define MAT_NR_REMAP(n) \
	if (n < remap_len_short) { \
		BLI_assert(n >= 0 && remap[n] < remap_len_short); \
		n = remap[n]; \
	} ((void)0)

	if (me->edit_btmesh) {
		BMEditMesh *em = me->edit_btmesh;
		BMIter iter;
		BMFace *efa;

		BM_ITER_MESH(efa, &iter, em->bm, BM_FACES_OF_MESH) {
			MAT_NR_REMAP(efa->mat_nr);
		}
	}
	else {
		int i;
		for (i = 0; i < me->totpoly; i++) {
			MAT_NR_REMAP(me->mpoly[i].mat_nr);
		}
	}

#undef MAT_NR_REMAP

}

void BKE_mesh_smooth_flag_set(Object *meshOb, int enableSmooth)
{
	Mesh *me = meshOb->data;
	int i;

	for (i = 0; i < me->totpoly; i++) {
		MPoly *mp = &me->mpoly[i];

		if (enableSmooth) {
			mp->flag |= ME_SMOOTH;
		}
		else {
			mp->flag &= ~ME_SMOOTH;
		}
	}

	for (i = 0; i < me->totface; i++) {
		MFace *mf = &me->mface[i];

		if (enableSmooth) {
			mf->flag |= ME_SMOOTH;
		}
		else {
			mf->flag &= ~ME_SMOOTH;
		}
	}
}

/**
 * Return a newly MEM_malloc'd array of all the mesh vertex locations
 * \note \a r_numVerts may be NULL
 */
float (*BKE_mesh_vertexCos_get(const Mesh *me, int *r_numVerts))[3]
{
	int i, numVerts = me->totvert;
	float (*cos)[3] = MEM_malloc_arrayN(numVerts, sizeof(*cos), "vertexcos1");

	if (r_numVerts) *r_numVerts = numVerts;
	for (i = 0; i < numVerts; i++)
		copy_v3_v3(cos[i], me->mvert[i].co);

	return cos;
}

/**
 * Find the index of the loop in 'poly' which references vertex,
 * returns -1 if not found
 */
int poly_find_loop_from_vert(
        const MPoly *poly, const MLoop *loopstart,
        unsigned vert)
{
	int j;
	for (j = 0; j < poly->totloop; j++, loopstart++) {
		if (loopstart->v == vert)
			return j;
	}

	return -1;
}

/**
 * Fill \a r_adj with the loop indices in \a poly adjacent to the
 * vertex. Returns the index of the loop matching vertex, or -1 if the
 * vertex is not in \a poly
 */
int poly_get_adj_loops_from_vert(
        const MPoly *poly,
        const MLoop *mloop, unsigned int vert,
        unsigned int r_adj[2])
{
	int corner = poly_find_loop_from_vert(
	        poly,
	        &mloop[poly->loopstart],
	        vert);

	if (corner != -1) {
#if 0	/* unused - this loop */
		const MLoop *ml = &mloop[poly->loopstart + corner];
#endif

		/* vertex was found */
		r_adj[0] = ME_POLY_LOOP_PREV(mloop, poly, corner)->v;
		r_adj[1] = ME_POLY_LOOP_NEXT(mloop, poly, corner)->v;
	}

	return corner;
}

/**
 * Return the index of the edge vert that is not equal to \a v. If
 * neither edge vertex is equal to \a v, returns -1.
 */
int BKE_mesh_edge_other_vert(const MEdge *e, int v)
{
	if (e->v1 == v)
		return e->v2;
	else if (e->v2 == v)
		return e->v1;
	else
		return -1;
}

/* basic vertex data functions */
bool BKE_mesh_minmax(const Mesh *me, float r_min[3], float r_max[3])
{
	int i = me->totvert;
	MVert *mvert;
	for (mvert = me->mvert; i--; mvert++) {
		minmax_v3v3_v3(r_min, r_max, mvert->co);
	}

	return (me->totvert != 0);
}

void BKE_mesh_transform(Mesh *me, float mat[4][4], bool do_keys)
{
	int i;
	MVert *mvert = me->mvert;
	float (*lnors)[3] = CustomData_get_layer(&me->ldata, CD_NORMAL);

	for (i = 0; i < me->totvert; i++, mvert++)
		mul_m4_v3(mat, mvert->co);

	if (do_keys && me->key) {
		KeyBlock *kb;
		for (kb = me->key->block.first; kb; kb = kb->next) {
			float *fp = kb->data;
			for (i = kb->totelem; i--; fp += 3) {
				mul_m4_v3(mat, fp);
			}
		}
	}

	/* don't update normals, caller can do this explicitly.
	 * We do update loop normals though, those may not be auto-generated (see e.g. STL import script)! */
	if (lnors) {
		float m3[3][3];

		copy_m3_m4(m3, mat);
		normalize_m3(m3);
		for (i = 0; i < me->totloop; i++, lnors++) {
			mul_m3_v3(m3, *lnors);
		}
	}
}

void BKE_mesh_translate(Mesh *me, const float offset[3], const bool do_keys)
{
	int i = me->totvert;
	MVert *mvert;
	for (mvert = me->mvert; i--; mvert++) {
		add_v3_v3(mvert->co, offset);
	}

	if (do_keys && me->key) {
		KeyBlock *kb;
		for (kb = me->key->block.first; kb; kb = kb->next) {
			float *fp = kb->data;
			for (i = kb->totelem; i--; fp += 3) {
				add_v3_v3(fp, offset);
			}
		}
	}
}

void BKE_mesh_ensure_navmesh(Mesh *me)
{
	if (!CustomData_has_layer(&me->pdata, CD_RECAST)) {
		int i;
		int numFaces = me->totpoly;
		int *recastData;
		recastData = (int *)MEM_malloc_arrayN(numFaces, sizeof(int), __func__);
		for (i = 0; i < numFaces; i++) {
			recastData[i] = i + 1;
		}
		CustomData_add_layer_named(&me->pdata, CD_RECAST, CD_ASSIGN, recastData, numFaces, "recastData");
	}
}

void BKE_mesh_tessface_calc(Mesh *mesh)
{
	mesh->totface = BKE_mesh_recalc_tessellation(
	        &mesh->fdata, &mesh->ldata, &mesh->pdata,
	        mesh->mvert,
	        mesh->totface, mesh->totloop, mesh->totpoly,
	        /* calc normals right after, don't copy from polys here */
	        false);

	BKE_mesh_update_customdata_pointers(mesh, true);
}

void BKE_mesh_tessface_ensure(Mesh *mesh)
{
	if (mesh->totpoly && mesh->totface == 0) {
		BKE_mesh_tessface_calc(mesh);
	}
}

void BKE_mesh_tessface_clear(Mesh *mesh)
{
	mesh_tessface_clear_intern(mesh, true);
}

void BKE_mesh_do_versions_cd_flag_init(Mesh *mesh)
{
	if (UNLIKELY(mesh->cd_flag)) {
		return;
	}
	else {
		MVert *mv;
		MEdge *med;
		int i;

		for (mv = mesh->mvert, i = 0; i < mesh->totvert; mv++, i++) {
			if (mv->bweight != 0) {
				mesh->cd_flag |= ME_CDFLAG_VERT_BWEIGHT;
				break;
			}
		}

		for (med = mesh->medge, i = 0; i < mesh->totedge; med++, i++) {
			if (med->bweight != 0) {
				mesh->cd_flag |= ME_CDFLAG_EDGE_BWEIGHT;
				if (mesh->cd_flag & ME_CDFLAG_EDGE_CREASE) {
					break;
				}
			}
			if (med->crease != 0) {
				mesh->cd_flag |= ME_CDFLAG_EDGE_CREASE;
				if (mesh->cd_flag & ME_CDFLAG_EDGE_BWEIGHT) {
					break;
				}
			}
		}

	}
}


/* -------------------------------------------------------------------- */
/* MSelect functions (currently used in weight paint mode) */

void BKE_mesh_mselect_clear(Mesh *me)
{
	if (me->mselect) {
		MEM_freeN(me->mselect);
		me->mselect = NULL;
	}
	me->totselect = 0;
}

void BKE_mesh_mselect_validate(Mesh *me)
{
	MSelect *mselect_src, *mselect_dst;
	int i_src, i_dst;

	if (me->totselect == 0)
		return;

	mselect_src = me->mselect;
	mselect_dst = MEM_malloc_arrayN((me->totselect), sizeof(MSelect), "Mesh selection history");

	for (i_src = 0, i_dst = 0; i_src < me->totselect; i_src++) {
		int index = mselect_src[i_src].index;
		switch (mselect_src[i_src].type) {
			case ME_VSEL:
			{
				if (me->mvert[index].flag & SELECT) {
					mselect_dst[i_dst] = mselect_src[i_src];
					i_dst++;
				}
				break;
			}
			case ME_ESEL:
			{
				if (me->medge[index].flag & SELECT) {
					mselect_dst[i_dst] = mselect_src[i_src];
					i_dst++;
				}
				break;
			}
			case ME_FSEL:
			{
				if (me->mpoly[index].flag & SELECT) {
					mselect_dst[i_dst] = mselect_src[i_src];
					i_dst++;
				}
				break;
			}
			default:
			{
				BLI_assert(0);
				break;
			}
		}
	}

	MEM_freeN(mselect_src);

	if (i_dst == 0) {
		MEM_freeN(mselect_dst);
		mselect_dst = NULL;
	}
	else if (i_dst != me->totselect) {
		mselect_dst = MEM_reallocN(mselect_dst, sizeof(MSelect) * i_dst);
	}

	me->totselect = i_dst;
	me->mselect = mselect_dst;

}

/**
 * Return the index within me->mselect, or -1
 */
int BKE_mesh_mselect_find(Mesh *me, int index, int type)
{
	int i;

	BLI_assert(ELEM(type, ME_VSEL, ME_ESEL, ME_FSEL));

	for (i = 0; i < me->totselect; i++) {
		if ((me->mselect[i].index == index) &&
		    (me->mselect[i].type == type))
		{
			return i;
		}
	}

	return -1;
}

/**
 * Return The index of the active element.
 */
int BKE_mesh_mselect_active_get(Mesh *me, int type)
{
	BLI_assert(ELEM(type, ME_VSEL, ME_ESEL, ME_FSEL));

	if (me->totselect) {
		if (me->mselect[me->totselect - 1].type == type) {
			return me->mselect[me->totselect - 1].index;
		}
	}
	return -1;
}

void BKE_mesh_mselect_active_set(Mesh *me, int index, int type)
{
	const int msel_index = BKE_mesh_mselect_find(me, index, type);

	if (msel_index == -1) {
		/* add to the end */
		me->mselect = MEM_reallocN(me->mselect, sizeof(MSelect) * (me->totselect + 1));
		me->mselect[me->totselect].index = index;
		me->mselect[me->totselect].type  = type;
		me->totselect++;
	}
	else if (msel_index != me->totselect - 1) {
		/* move to the end */
		SWAP(MSelect, me->mselect[msel_index], me->mselect[me->totselect - 1]);
	}

	BLI_assert((me->mselect[me->totselect - 1].index == index) &&
	           (me->mselect[me->totselect - 1].type  == type));
}

/**
 * Compute 'split' (aka loop, or per face corner's) normals.
 *
 * \param r_lnors_spacearr Allows to get computed loop normal space array. That data, among other things,
 *                         contains 'smooth fan' info, useful e.g. to split geometry along sharp edges...
 */
void BKE_mesh_calc_normals_split_ex(Mesh *mesh, MLoopNorSpaceArray *r_lnors_spacearr)
{
	float (*r_loopnors)[3];
	float (*polynors)[3];
	short (*clnors)[2] = NULL;
	bool free_polynors = false;

	/* Note that we enforce computing clnors when the clnor space array is requested by caller here.
	 * However, we obviously only use the autosmooth angle threshold only in case autosmooth is enabled. */
	const bool use_split_normals = (r_lnors_spacearr != NULL) || ((mesh->flag & ME_AUTOSMOOTH) != 0);
	const float split_angle = (mesh->flag & ME_AUTOSMOOTH) != 0 ? mesh->smoothresh : (float)M_PI;

	if (CustomData_has_layer(&mesh->ldata, CD_NORMAL)) {
		r_loopnors = CustomData_get_layer(&mesh->ldata, CD_NORMAL);
		memset(r_loopnors, 0, sizeof(float[3]) * mesh->totloop);
	}
	else {
		r_loopnors = CustomData_add_layer(&mesh->ldata, CD_NORMAL, CD_CALLOC, NULL, mesh->totloop);
		CustomData_set_layer_flag(&mesh->ldata, CD_NORMAL, CD_FLAG_TEMPORARY);
	}

	/* may be NULL */
	clnors = CustomData_get_layer(&mesh->ldata, CD_CUSTOMLOOPNORMAL);

	if (CustomData_has_layer(&mesh->pdata, CD_NORMAL)) {
		/* This assume that layer is always up to date, not sure this is the case (esp. in Edit mode?)... */
		polynors = CustomData_get_layer(&mesh->pdata, CD_NORMAL);
		free_polynors = false;
	}
	else {
		polynors = MEM_malloc_arrayN(mesh->totpoly, sizeof(float[3]), __func__);
		BKE_mesh_calc_normals_poly(
		        mesh->mvert, NULL, mesh->totvert,
		        mesh->mloop, mesh->mpoly, mesh->totloop, mesh->totpoly, polynors, false);
		free_polynors = true;
	}

	BKE_mesh_normals_loop_split(
	        mesh->mvert, mesh->totvert, mesh->medge, mesh->totedge,
	        mesh->mloop, r_loopnors, mesh->totloop, mesh->mpoly, (const float (*)[3])polynors, mesh->totpoly,
	        use_split_normals, split_angle, r_lnors_spacearr, clnors, NULL);

	if (free_polynors) {
		MEM_freeN(polynors);
	}
}

void BKE_mesh_calc_normals_split(Mesh *mesh)
{
	BKE_mesh_calc_normals_split_ex(mesh, NULL);
}

/* Split faces helper functions. */

typedef struct SplitFaceNewVert {
	struct SplitFaceNewVert *next;
	int new_index;
	int orig_index;
	float *vnor;
} SplitFaceNewVert;

typedef struct SplitFaceNewEdge {
	struct SplitFaceNewEdge *next;
	int new_index;
	int orig_index;
	int v1;
	int v2;
} SplitFaceNewEdge;

/* Detect needed new vertices, and update accordingly loops' vertex indices.
 * WARNING! Leaves mesh in invalid state. */
static int split_faces_prepare_new_verts(
        const Mesh *mesh, MLoopNorSpaceArray *lnors_spacearr, SplitFaceNewVert **new_verts, MemArena *memarena)
{
	/* This is now mandatory, trying to do the job in simple way without that data is doomed to fail, even when only
	 * dealing with smooth/flat faces one can find cases that no simple algorithm can handle properly. */
	BLI_assert(lnors_spacearr != NULL);

	const int num_loops = mesh->totloop;
	int num_verts = mesh->totvert;
	MVert *mvert = mesh->mvert;
	MLoop *mloop = mesh->mloop;

	BLI_bitmap *verts_used = BLI_BITMAP_NEW(num_verts, __func__);
	BLI_bitmap *done_loops = BLI_BITMAP_NEW(num_loops, __func__);

	MLoop *ml = mloop;
	MLoopNorSpace **lnor_space = lnors_spacearr->lspacearr;

	BLI_assert(lnors_spacearr->data_type == MLNOR_SPACEARR_LOOP_INDEX);

	for (int loop_idx = 0; loop_idx < num_loops; loop_idx++, ml++, lnor_space++) {
		if (!BLI_BITMAP_TEST(done_loops, loop_idx)) {
			const int vert_idx = ml->v;
			const bool vert_used = BLI_BITMAP_TEST_BOOL(verts_used, vert_idx);
			/* If vert is already used by another smooth fan, we need a new vert for this one. */
			const int new_vert_idx = vert_used ? num_verts++ : vert_idx;

			BLI_assert(*lnor_space);

			if ((*lnor_space)->flags & MLNOR_SPACE_IS_SINGLE) {
				/* Single loop in this fan... */
				BLI_assert(GET_INT_FROM_POINTER((*lnor_space)->loops) == loop_idx);
				BLI_BITMAP_ENABLE(done_loops, loop_idx);
				if (vert_used) {
					ml->v = new_vert_idx;
				}
			}
			else {
				for (LinkNode *lnode = (*lnor_space)->loops; lnode; lnode = lnode->next) {
					const int ml_fan_idx = GET_INT_FROM_POINTER(lnode->link);
					BLI_BITMAP_ENABLE(done_loops, ml_fan_idx);
					if (vert_used) {
						mloop[ml_fan_idx].v = new_vert_idx;
					}
				}
			}

			if (!vert_used) {
				BLI_BITMAP_ENABLE(verts_used, vert_idx);
				/* We need to update that vertex's normal here, we won't go over it again. */
				/* This is important! *DO NOT* set vnor to final computed lnor, vnor should always be defined to
				 * 'automatic normal' value computed from its polys, not some custom normal.
				 * Fortunately, that's the loop normal space's 'lnor' reference vector. ;) */
				normal_float_to_short_v3(mvert[vert_idx].no, (*lnor_space)->vec_lnor);
			}
			else {
				/* Add new vert to list. */
				SplitFaceNewVert *new_vert = BLI_memarena_alloc(memarena, sizeof(*new_vert));
				new_vert->orig_index = vert_idx;
				new_vert->new_index = new_vert_idx;
				new_vert->vnor = (*lnor_space)->vec_lnor;  /* See note above. */
				new_vert->next = *new_verts;
				*new_verts = new_vert;
			}
		}
	}

	MEM_freeN(done_loops);
	MEM_freeN(verts_used);

	return num_verts - mesh->totvert;
}

/* Detect needed new edges, and update accordingly loops' edge indices.
 * WARNING! Leaves mesh in invalid state. */
static int split_faces_prepare_new_edges(
        const Mesh *mesh, SplitFaceNewEdge **new_edges, MemArena *memarena)
{
	const int num_polys = mesh->totpoly;
	int num_edges = mesh->totedge;
	MEdge *medge = mesh->medge;
	MLoop *mloop = mesh->mloop;
	const MPoly *mpoly = mesh->mpoly;

	BLI_bitmap *edges_used = BLI_BITMAP_NEW(num_edges, __func__);
	EdgeHash *edges_hash = BLI_edgehash_new_ex(__func__, num_edges);

	const MPoly *mp = mpoly;
	for (int poly_idx = 0; poly_idx < num_polys; poly_idx++, mp++) {
		MLoop *ml_prev = &mloop[mp->loopstart + mp->totloop - 1];
		MLoop *ml = &mloop[mp->loopstart];
		for (int loop_idx = 0; loop_idx < mp->totloop; loop_idx++, ml++) {
			void **eval;
			if (!BLI_edgehash_ensure_p(edges_hash, ml_prev->v, ml->v, &eval)) {
				const int edge_idx = ml_prev->e;

				/* That edge has not been encountered yet, define it. */
				if (BLI_BITMAP_TEST(edges_used, edge_idx)) {
					/* Original edge has already been used, we need to define a new one. */
					const int new_edge_idx = num_edges++;
					*eval = SET_INT_IN_POINTER(new_edge_idx);
					ml_prev->e = new_edge_idx;

					SplitFaceNewEdge *new_edge = BLI_memarena_alloc(memarena, sizeof(*new_edge));
					new_edge->orig_index = edge_idx;
					new_edge->new_index = new_edge_idx;
					new_edge->v1 = ml_prev->v;
					new_edge->v2 = ml->v;
					new_edge->next = *new_edges;
					*new_edges = new_edge;
				}
				else {
					/* We can re-use original edge. */
					medge[edge_idx].v1 = ml_prev->v;
					medge[edge_idx].v2 = ml->v;
					*eval = SET_INT_IN_POINTER(edge_idx);
					BLI_BITMAP_ENABLE(edges_used, edge_idx);
				}
			}
			else {
				/* Edge already known, just update loop's edge index. */
				ml_prev->e = GET_INT_FROM_POINTER(*eval);
			}

			ml_prev = ml;
		}
	}

	MEM_freeN(edges_used);
	BLI_edgehash_free(edges_hash, NULL);

	return num_edges - mesh->totedge;
}

/* Perform actual split of vertices. */
static void split_faces_split_new_verts(
        Mesh *mesh, SplitFaceNewVert *new_verts, const int num_new_verts)
{
	const int num_verts = mesh->totvert - num_new_verts;
	MVert *mvert = mesh->mvert;

	/* Remember new_verts is a single linklist, so its items are in reversed order... */
	MVert *new_mv = &mvert[mesh->totvert - 1];
	for (int i = mesh->totvert - 1; i >= num_verts ; i--, new_mv--, new_verts = new_verts->next) {
		BLI_assert(new_verts->new_index == i);
		BLI_assert(new_verts->new_index != new_verts->orig_index);
		CustomData_copy_data(&mesh->vdata, &mesh->vdata, new_verts->orig_index, i, 1);
		if (new_verts->vnor) {
			normal_float_to_short_v3(new_mv->no, new_verts->vnor);
		}
	}
}

/* Perform actual split of edges. */
static void split_faces_split_new_edges(
        Mesh *mesh, SplitFaceNewEdge *new_edges, const int num_new_edges)
{
	const int num_edges = mesh->totedge - num_new_edges;
	MEdge *medge = mesh->medge;

	/* Remember new_edges is a single linklist, so its items are in reversed order... */
	MEdge *new_med = &medge[mesh->totedge - 1];
	for (int i = mesh->totedge - 1; i >= num_edges ; i--, new_med--, new_edges = new_edges->next) {
		BLI_assert(new_edges->new_index == i);
		BLI_assert(new_edges->new_index != new_edges->orig_index);
		CustomData_copy_data(&mesh->edata, &mesh->edata, new_edges->orig_index, i, 1);
		new_med->v1 = new_edges->v1;
		new_med->v2 = new_edges->v2;
	}
}

/* Split faces based on the edge angle and loop normals.
 * Matches behavior of face splitting in render engines.
 *
 * NOTE: Will leave CD_NORMAL loop data layer which is
 * used by render engines to set shading up.
 */
void BKE_mesh_split_faces(Mesh *mesh, bool free_loop_normals)
{
	const int num_polys = mesh->totpoly;

	if (num_polys == 0) {
		return;
	}
	BKE_mesh_tessface_clear(mesh);

	MLoopNorSpaceArray lnors_spacearr = {NULL};
	/* Compute loop normals and loop normal spaces (a.k.a. smooth fans of faces around vertices). */
	BKE_mesh_calc_normals_split_ex(mesh, &lnors_spacearr);
	/* Stealing memarena from loop normals space array. */
	MemArena *memarena = lnors_spacearr.mem;

	SplitFaceNewVert *new_verts = NULL;
	SplitFaceNewEdge *new_edges = NULL;

	/* Detect loop normal spaces (a.k.a. smooth fans) that will need a new vert. */
	const int num_new_verts = split_faces_prepare_new_verts(mesh, &lnors_spacearr, &new_verts, memarena);

	if (num_new_verts > 0) {
		/* Reminder: beyond this point, there is no way out, mesh is in invalid state (due to early-reassignment of
		 * loops' vertex and edge indices to new, to-be-created split ones). */

		const int num_new_edges = split_faces_prepare_new_edges(mesh, &new_edges, memarena);
		/* We can have to split a vertex without having to add a single new edge... */
		const bool do_edges = (num_new_edges > 0);

		/* Reallocate all vert and edge related data. */
		mesh->totvert += num_new_verts;
		CustomData_realloc(&mesh->vdata, mesh->totvert);
		if (do_edges) {
			mesh->totedge += num_new_edges;
			CustomData_realloc(&mesh->edata, mesh->totedge);
		}
		/* Update pointers to a newly allocated memory. */
		BKE_mesh_update_customdata_pointers(mesh, false);

		/* Perform actual split of vertices and edges. */
		split_faces_split_new_verts(mesh, new_verts, num_new_verts);
		if (do_edges) {
			split_faces_split_new_edges(mesh, new_edges, num_new_edges);
		}
	}

	/* Note: after this point mesh is expected to be valid again. */

	/* CD_NORMAL is expected to be temporary only. */
	if (free_loop_normals) {
		CustomData_free_layers(&mesh->ldata, CD_NORMAL, mesh->totloop);
	}

	/* Also frees new_verts/edges temp data, since we used its memarena to allocate them. */
	BKE_lnor_spacearr_free(&lnors_spacearr);

#ifdef VALIDATE_MESH
	BKE_mesh_validate(mesh, true, true);
#endif
}


/* **** Depsgraph evaluation **** */

void BKE_mesh_eval_geometry(
        EvaluationContext *UNUSED(eval_ctx),
        Mesh *mesh)
{
	DEG_debug_print_eval(__func__, mesh->id.name, mesh);
	if (mesh->bb == NULL || (mesh->bb->flag & BOUNDBOX_DIRTY)) {
		BKE_mesh_texspace_calc(mesh);
	}
}

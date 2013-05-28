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


#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <math.h>

#include "MEM_guardedalloc.h"

#include "DNA_scene_types.h"
#include "DNA_material_types.h"
#include "DNA_object_types.h"
#include "DNA_key_types.h"
#include "DNA_mesh_types.h"
#include "DNA_meshdata_types.h"
#include "DNA_ipo_types.h"
#include "DNA_customdata_types.h"

#include "BLI_utildefines.h"
#include "BLI_blenlib.h"
#include "BLI_math.h"
#include "BLI_edgehash.h"
#include "BLI_scanfill.h"
#include "BLI_array.h"

#include "BKE_animsys.h"
#include "BKE_main.h"
#include "BKE_customdata.h"
#include "BKE_DerivedMesh.h"
#include "BKE_global.h"
#include "BKE_mesh.h"
#include "BKE_displist.h"
#include "BKE_library.h"
#include "BKE_material.h"
#include "BKE_modifier.h"
#include "BKE_multires.h"
#include "BKE_key.h"
/* these 2 are only used by conversion functions */
#include "BKE_curve.h"
/* -- */
#include "BKE_object.h"
#include "BKE_editmesh.h"
#include "BLI_edgehash.h"

#include "bmesh.h"

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
		if (ELEM7(c1->layers[i].type, CD_MVERT, CD_MEDGE, CD_MPOLY,
		          CD_MLOOPUV, CD_MLOOPCOL, CD_MTEXPOLY, CD_MDEFORMVERT))
		{
			i1++;
		}
	}

	for (i = 0; i < c2->totlayer; i++) {
		if (ELEM7(c2->layers[i].type, CD_MVERT, CD_MEDGE, CD_MPOLY,
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
		while (i1 < c1->totlayer && !ELEM7(l1->type, CD_MVERT, CD_MEDGE, CD_MPOLY, 
		                                   CD_MLOOPUV, CD_MLOOPCOL, CD_MTEXPOLY, CD_MDEFORMVERT))
		{
			i1++, l1++;
		}

		while (i2 < c2->totlayer && !ELEM7(l2->type, CD_MVERT, CD_MEDGE, CD_MPOLY,
		                                   CD_MLOOPUV, CD_MLOOPCOL, CD_MTEXPOLY, CD_MDEFORMVERT))
		{
			i2++, l2++;
		}
		
		if (l1->type == CD_MVERT) {
			MVert *v1 = l1->data;
			MVert *v2 = l2->data;
			int vtot = m1->totvert;
			
			for (j = 0; j < vtot; j++, v1++, v2++) {
				if (len_v3v3(v1->co, v2->co) > thresh)
					return MESHCMP_VERTCOMISMATCH;
				/* I don't care about normals, let's just do coodinates */
			}
		}
		
		/*we're order-agnostic for edges here*/
		if (l1->type == CD_MEDGE) {
			MEdge *e1 = l1->data;
			MEdge *e2 = l2->data;
			EdgeHash *eh = BLI_edgehash_new();
			int etot = m1->totedge;
		
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
					if (ABS(dw1->weight - dw2->weight) > thresh)
						return MESHCMP_DVERT_WEIGHTMISMATCH;
				}
			}
		}
	}
	
	return 0;
}

/*used for testing.  returns an error string the two meshes don't match*/
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

/* Note: unlinking is called when me->id.us is 0, question remains how
 * much unlinking of Library data in Mesh should be done... probably
 * we need a more generic method, like the expand() functions in
 * readfile.c */

void BKE_mesh_unlink(Mesh *me)
{
	int a;
	
	if (me == NULL) return;
	
	if (me->mat)
	for (a = 0; a < me->totcol; a++) {
		if (me->mat[a]) me->mat[a]->id.us--;
		me->mat[a] = NULL;
	}

	if (me->key) {
		me->key->id.us--;
	}
	me->key = NULL;
	
	if (me->texcomesh) me->texcomesh = NULL;
}

/* do not free mesh itself */
void BKE_mesh_free(Mesh *me, int unlink)
{
	if (unlink)
		BKE_mesh_unlink(me);

	CustomData_free(&me->vdata, me->totvert);
	CustomData_free(&me->edata, me->totedge);
	CustomData_free(&me->fdata, me->totface);
	CustomData_free(&me->ldata, me->totloop);
	CustomData_free(&me->pdata, me->totpoly);

	if (me->adt) {
		BKE_free_animdata(&me->id);
		me->adt = NULL;
	}
	
	if (me->mat) MEM_freeN(me->mat);
	
	if (me->bb) MEM_freeN(me->bb);
	if (me->mselect) MEM_freeN(me->mselect);
	if (me->edit_btmesh) MEM_freeN(me->edit_btmesh);
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

Mesh *BKE_mesh_add(Main *bmain, const char *name)
{
	Mesh *me;
	
	me = BKE_libblock_alloc(&bmain->mesh, ID_ME, name);
	
	me->size[0] = me->size[1] = me->size[2] = 1.0;
	me->smoothresh = 30;
	me->texflag = ME_AUTOSPACE;
	me->flag = ME_TWOSIDED;
	me->drawflag = ME_DRAWEDGES | ME_DRAWFACES | ME_DRAWCREASES;

	CustomData_reset(&me->vdata);
	CustomData_reset(&me->edata);
	CustomData_reset(&me->fdata);
	CustomData_reset(&me->pdata);
	CustomData_reset(&me->ldata);

	return me;
}

Mesh *BKE_mesh_copy_ex(Main *bmain, Mesh *me)
{
	Mesh *men;
	MTFace *tface;
	MTexPoly *txface;
	int a, i;
	const int do_tessface = ((me->totface != 0) && (me->totpoly == 0)); /* only do tessface if we have no polys */
	
	men = BKE_libblock_copy_ex(bmain, &me->id);
	
	men->mat = MEM_dupallocN(me->mat);
	for (a = 0; a < men->totcol; a++) {
		id_us_plus((ID *)men->mat[a]);
	}
	id_us_plus((ID *)men->texcomesh);

	CustomData_copy(&me->vdata, &men->vdata, CD_MASK_MESH, CD_DUPLICATE, men->totvert);
	CustomData_copy(&me->edata, &men->edata, CD_MASK_MESH, CD_DUPLICATE, men->totedge);
	CustomData_copy(&me->ldata, &men->ldata, CD_MASK_MESH, CD_DUPLICATE, men->totloop);
	CustomData_copy(&me->pdata, &men->pdata, CD_MASK_MESH, CD_DUPLICATE, men->totpoly);
	if (do_tessface) {
		CustomData_copy(&me->fdata, &men->fdata, CD_MASK_MESH, CD_DUPLICATE, men->totface);
	}
	else {
		mesh_tessface_clear_intern(men, FALSE);
	}

	BKE_mesh_update_customdata_pointers(men, do_tessface);

	/* ensure indirect linked data becomes lib-extern */
	for (i = 0; i < me->fdata.totlayer; i++) {
		if (me->fdata.layers[i].type == CD_MTFACE) {
			tface = (MTFace *)me->fdata.layers[i].data;

			for (a = 0; a < me->totface; a++, tface++)
				if (tface->tpage)
					id_lib_extern((ID *)tface->tpage);
		}
	}
	
	for (i = 0; i < me->pdata.totlayer; i++) {
		if (me->pdata.layers[i].type == CD_MTEXPOLY) {
			txface = (MTexPoly *)me->pdata.layers[i].data;

			for (a = 0; a < me->totpoly; a++, txface++)
				if (txface->tpage)
					id_lib_extern((ID *)txface->tpage);
		}
	}

	men->mselect = NULL;
	men->edit_btmesh = NULL;

	men->bb = MEM_dupallocN(men->bb);
	
	men->key = BKE_key_copy(me->key);
	if (men->key) men->key->from = (ID *)men;

	return men;
}

Mesh *BKE_mesh_copy(Mesh *me)
{
	return BKE_mesh_copy_ex(G.main, me);
}

BMesh *BKE_mesh_to_bmesh(Mesh *me, Object *ob)
{
	BMesh *bm;

	bm = BM_mesh_create(&bm_mesh_allocsize_default);

	BM_mesh_bm_from_me(bm, me, true, ob->shapenr);

	return bm;
}

static void expand_local_mesh(Mesh *me)
{
	id_lib_extern((ID *)me->texcomesh);

	if (me->mtface || me->mtpoly) {
		int a, i;

		for (i = 0; i < me->pdata.totlayer; i++) {
			if (me->pdata.layers[i].type == CD_MTEXPOLY) {
				MTexPoly *txface = (MTexPoly *)me->pdata.layers[i].data;

				for (a = 0; a < me->totpoly; a++, txface++) {
					/* special case: ima always local immediately */
					if (txface->tpage) {
						id_lib_extern((ID *)txface->tpage);
					}
				}
			}
		}

		for (i = 0; i < me->fdata.totlayer; i++) {
			if (me->fdata.layers[i].type == CD_MTFACE) {
				MTFace *tface = (MTFace *)me->fdata.layers[i].data;

				for (a = 0; a < me->totface; a++, tface++) {
					/* special case: ima always local immediately */
					if (tface->tpage) {
						id_lib_extern((ID *)tface->tpage);
					}
				}
			}
		}
	}

	if (me->mat) {
		extern_local_matarar(me->mat, me->totcol);
	}
}

void BKE_mesh_make_local(Mesh *me)
{
	Main *bmain = G.main;
	Object *ob;
	int is_local = FALSE, is_lib = FALSE;

	/* - only lib users: do nothing
	 * - only local users: set flag
	 * - mixed: make copy
	 */

	if (me->id.lib == NULL) return;
	if (me->id.us == 1) {
		id_clear_lib_data(bmain, &me->id);
		expand_local_mesh(me);
		return;
	}

	for (ob = bmain->object.first; ob && ELEM(0, is_lib, is_local); ob = ob->id.next) {
		if (me == ob->data) {
			if (ob->id.lib) is_lib = TRUE;
			else is_local = TRUE;
		}
	}

	if (is_local && is_lib == FALSE) {
		id_clear_lib_data(bmain, &me->id);
		expand_local_mesh(me);
	}
	else if (is_local && is_lib) {
		Mesh *me_new = BKE_mesh_copy(me);
		me_new->id.us = 0;


		/* Remap paths of new ID using old library as base. */
		BKE_id_lib_local_paths(bmain, me->id.lib, &me_new->id);

		for (ob = bmain->object.first; ob; ob = ob->id.next) {
			if (me == ob->data) {
				if (ob->id.lib == NULL) {
					BKE_mesh_assign_object(ob, me_new);
				}
			}
		}
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

	if (!me->bb)
		BKE_mesh_texspace_calc(me);

	return me->bb;
}

void BKE_mesh_texspace_get(Mesh *me, float r_loc[3], float r_rot[3], float r_size[3])
{
	if (!me->bb) {
		BKE_mesh_texspace_calc(me);
	}

	if (r_loc) copy_v3_v3(r_loc,  me->loc);
	if (r_rot) copy_v3_v3(r_rot,  me->rot);
	if (r_size) copy_v3_v3(r_size, me->size);
}

float (*BKE_mesh_orco_verts_get(Object *ob))[3]
{
	Mesh *me = ob->data;
	MVert *mvert = NULL;
	Mesh *tme = me->texcomesh ? me->texcomesh : me;
	int a, totvert;
	float (*vcos)[3] = NULL;

	/* Get appropriate vertex coordinates */
	vcos = MEM_callocN(sizeof(*vcos) * me->totvert, "orco mesh");
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
				CustomData_swap(fdata, mfindex, corner_indices);
		}
	}
	else if (nr == 4) {
		if (mface->v3 == 0 || mface->v4 == 0) {
			static int corner_indices[4] = {2, 3, 0, 1};

			SWAP(unsigned int, mface->v1, mface->v3);
			SWAP(unsigned int, mface->v2, mface->v4);

			if (fdata)
				CustomData_swap(fdata, mfindex, corner_indices);
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

void BKE_mesh_assign_object(Object *ob, Mesh *me)
{
	Mesh *old = NULL;

	multires_force_update(ob);
	
	if (ob == NULL) return;
	
	if (ob->type == OB_MESH) {
		old = ob->data;
		if (old)
			old->id.us--;
		ob->data = me;
		id_us_plus((ID *)me);
	}
	
	test_object_materials(G.main, (ID *)me);

	test_object_modifiers(ob);
}

/* ************** make edges in a Mesh, for outside of editmode */

struct edgesort {
	unsigned int v1, v2;
	short is_loose, is_draw;
};

/* edges have to be added with lowest index first for sorting */
static void to_edgesort(struct edgesort *ed,
                        unsigned int v1, unsigned int v2,
                        short is_loose, short is_draw)
{
	if (v1 < v2) {
		ed->v1 = v1; ed->v2 = v2;
	}
	else {
		ed->v1 = v2; ed->v2 = v1;
	}
	ed->is_loose = is_loose;
	ed->is_draw = is_draw;
}

static int vergedgesort(const void *v1, const void *v2)
{
	const struct edgesort *x1 = v1, *x2 = v2;

	if (x1->v1 > x2->v1) return 1;
	else if (x1->v1 < x2->v1) return -1;
	else if (x1->v2 > x2->v2) return 1;
	else if (x1->v2 < x2->v2) return -1;
	
	return 0;
}


/* Create edges based on known verts and faces */
static void make_edges_mdata(MVert *UNUSED(allvert), MFace *allface, MLoop *allloop,
                             MPoly *allpoly, int UNUSED(totvert), int totface, int UNUSED(totloop), int totpoly,
                             int old, MEdge **alledge, int *_totedge)
{
	MPoly *mpoly;
	MFace *mface;
	MEdge *medge;
	EdgeHash *hash = BLI_edgehash_new();
	struct edgesort *edsort, *ed;
	int a, totedge = 0, final = 0;

	/* we put all edges in array, sort them, and detect doubles that way */

	for (a = totface, mface = allface; a > 0; a--, mface++) {
		if (mface->v4) totedge += 4;
		else if (mface->v3) totedge += 3;
		else totedge += 1;
	}

	if (totedge == 0) {
		/* flag that mesh has edges */
		(*alledge) = MEM_callocN(0, "make mesh edges");
		(*_totedge) = 0;
		return;
	}

	ed = edsort = MEM_mallocN(totedge * sizeof(struct edgesort), "edgesort");

	for (a = totface, mface = allface; a > 0; a--, mface++) {
		to_edgesort(ed++, mface->v1, mface->v2, !mface->v3, mface->edcode & ME_V1V2);
		if (mface->v4) {
			to_edgesort(ed++, mface->v2, mface->v3, 0, mface->edcode & ME_V2V3);
			to_edgesort(ed++, mface->v3, mface->v4, 0, mface->edcode & ME_V3V4);
			to_edgesort(ed++, mface->v4, mface->v1, 0, mface->edcode & ME_V4V1);
		}
		else if (mface->v3) {
			to_edgesort(ed++, mface->v2, mface->v3, 0, mface->edcode & ME_V2V3);
			to_edgesort(ed++, mface->v3, mface->v1, 0, mface->edcode & ME_V3V1);
		}
	}

	qsort(edsort, totedge, sizeof(struct edgesort), vergedgesort);

	/* count final amount */
	for (a = totedge, ed = edsort; a > 1; a--, ed++) {
		/* edge is unique when it differs from next edge, or is last */
		if (ed->v1 != (ed + 1)->v1 || ed->v2 != (ed + 1)->v2) final++;
	}
	final++;

	(*alledge) = medge = MEM_callocN(sizeof(MEdge) * final, "BKE_mesh_make_edges mdge");
	(*_totedge) = final;

	for (a = totedge, ed = edsort; a > 1; a--, ed++) {
		/* edge is unique when it differs from next edge, or is last */
		if (ed->v1 != (ed + 1)->v1 || ed->v2 != (ed + 1)->v2) {
			medge->v1 = ed->v1;
			medge->v2 = ed->v2;
			if (old == 0 || ed->is_draw) medge->flag = ME_EDGEDRAW | ME_EDGERENDER;
			if (ed->is_loose) medge->flag |= ME_LOOSEEDGE;

			/* order is swapped so extruding this edge as a surface wont flip face normals
			 * with cyclic curves */
			if (ed->v1 + 1 != ed->v2) {
				SWAP(unsigned int, medge->v1, medge->v2);
			}
			medge++;
		}
		else {
			/* equal edge, we merge the drawflag */
			(ed + 1)->is_draw |= ed->is_draw;
		}
	}
	/* last edge */
	medge->v1 = ed->v1;
	medge->v2 = ed->v2;
	medge->flag = ME_EDGEDRAW;
	if (ed->is_loose) medge->flag |= ME_LOOSEEDGE;
	medge->flag |= ME_EDGERENDER;

	MEM_freeN(edsort);
	
	/* set edge members of mloops */
	medge = *alledge;
	for (a = 0; a < *_totedge; a++, medge++) {
		BLI_edgehash_insert(hash, medge->v1, medge->v2, SET_INT_IN_POINTER(a));
	}
	
	mpoly = allpoly;
	for (a = 0; a < totpoly; a++, mpoly++) {
		MLoop *ml, *ml_next;
		int i = mpoly->totloop;

		ml_next = allloop + mpoly->loopstart;  /* first loop */
		ml = &ml_next[i - 1];                  /* last loop */

		while (i-- != 0) {
			ml->e = GET_INT_FROM_POINTER(BLI_edgehash_lookup(hash, ml->v, ml_next->v));
			ml = ml_next;
			ml_next++;
		}
	}
	
	BLI_edgehash_free(hash, NULL);
}

void BKE_mesh_make_edges(Mesh *me, int old)
{
	MEdge *medge;
	int totedge = 0;

	make_edges_mdata(me->mvert, me->mface, me->mloop, me->mpoly, me->totvert, me->totface, me->totloop, me->totpoly, old, &medge, &totedge);
	if (totedge == 0) {
		/* flag that mesh has edges */
		me->medge = medge;
		me->totedge = 0;
		return;
	}

	medge = CustomData_add_layer(&me->edata, CD_MEDGE, CD_ASSIGN, medge, totedge);
	me->medge = medge;
	me->totedge = totedge;

	BKE_mesh_strip_loose_faces(me);
}

/* We need to keep this for edge creation (for now?), and some old readfile code... */
void BKE_mesh_strip_loose_faces(Mesh *me)
{
	MFace *f;
	int a, b;

	for (a = b = 0, f = me->mface; a < me->totface; a++, f++) {
		if (f->v3) {
			if (a != b) {
				memcpy(&me->mface[b], f, sizeof(me->mface[b]));
				CustomData_copy_data(&me->fdata, &me->fdata, a, b, 1);
			}
			b++;
		}
	}
	if (a != b) {
		CustomData_free_elem(&me->fdata, b, a - b);
		me->totface = b;
	}
}

/* Works on both loops and polys! */
/* Note: It won't try to guess which loops of an invalid poly to remove!
 *       this is the work of the caller, to mark those loops...
 *       See e.g. BKE_mesh_validate_arrays(). */
void BKE_mesh_strip_loose_polysloops(Mesh *me)
{
	MPoly *p;
	MLoop *l;
	int a, b;
	/* New loops idx! */
	int *new_idx = MEM_mallocN(sizeof(int) * me->totloop, __func__);

	for (a = b = 0, p = me->mpoly; a < me->totpoly; a++, p++) {
		int invalid = FALSE;
		int i = p->loopstart;
		int stop = i + p->totloop;

		if (stop > me->totloop || stop < i) {
			invalid = TRUE;
		}
		else {
			l = &me->mloop[i];
			i = stop - i;
			/* If one of the poly's loops is invalid, the whole poly is invalid! */
			for (; i--; l++) {
				if (l->e == INVALID_LOOP_EDGE_MARKER) {
					invalid = TRUE;
					break;
				}
			}
		}

		if (p->totloop >= 3 && !invalid) {
			if (a != b) {
				memcpy(&me->mpoly[b], p, sizeof(me->mpoly[b]));
				CustomData_copy_data(&me->pdata, &me->pdata, a, b, 1);
			}
			b++;
		}
	}
	if (a != b) {
		CustomData_free_elem(&me->pdata, b, a - b);
		me->totpoly = b;
	}

	/* And now, get rid of invalid loops. */
	for (a = b = 0, l = me->mloop; a < me->totloop; a++, l++) {
		if (l->e != INVALID_LOOP_EDGE_MARKER) {
			if (a != b) {
				memcpy(&me->mloop[b], l, sizeof(me->mloop[b]));
				CustomData_copy_data(&me->ldata, &me->ldata, a, b, 1);
			}
			new_idx[a] = b;
			b++;
		}
		else {
			/* XXX Theoretically, we should be able to not do this, as no remaining poly
			 *     should use any stripped loop. But for security's sake... */
			new_idx[a] = -a;
		}
	}
	if (a != b) {
		CustomData_free_elem(&me->ldata, b, a - b);
		me->totloop = b;
	}

	/* And now, update polys' start loop index. */
	/* Note: At this point, there should never be any poly using a striped loop! */
	for (a = 0, p = me->mpoly; a < me->totpoly; a++, p++) {
		p->loopstart = new_idx[p->loopstart];
	}

	MEM_freeN(new_idx);
}

void BKE_mesh_strip_loose_edges(Mesh *me)
{
	MEdge *e;
	MLoop *l;
	int a, b;
	unsigned int *new_idx = MEM_mallocN(sizeof(int) * me->totedge, __func__);

	for (a = b = 0, e = me->medge; a < me->totedge; a++, e++) {
		if (e->v1 != e->v2) {
			if (a != b) {
				memcpy(&me->medge[b], e, sizeof(me->medge[b]));
				CustomData_copy_data(&me->edata, &me->edata, a, b, 1);
			}
			new_idx[a] = b;
			b++;
		}
		else {
			new_idx[a] = INVALID_LOOP_EDGE_MARKER;
		}
	}
	if (a != b) {
		CustomData_free_elem(&me->edata, b, a - b);
		me->totedge = b;
	}

	/* And now, update loops' edge indices. */
	/* XXX We hope no loop was pointing to a striped edge!
	 *     Else, its e will be set to INVALID_LOOP_EDGE_MARKER :/ */
	for (a = 0, l = me->mloop; a < me->totloop; a++, l++) {
		l->e = new_idx[l->e];
	}

	MEM_freeN(new_idx);
}

void BKE_mesh_from_metaball(ListBase *lb, Mesh *me)
{
	DispList *dl;
	MVert *mvert;
	MLoop *mloop, *allloop;
	MPoly *mpoly;
	float *nors, *verts;
	int a, *index;
	
	dl = lb->first;
	if (dl == NULL) return;

	if (dl->type == DL_INDEX4) {
		mvert = CustomData_add_layer(&me->vdata, CD_MVERT, CD_CALLOC, NULL, dl->nr);
		allloop = mloop = CustomData_add_layer(&me->ldata, CD_MLOOP, CD_CALLOC, NULL, dl->parts * 4);
		mpoly = CustomData_add_layer(&me->pdata, CD_MPOLY, CD_CALLOC, NULL, dl->parts);
		me->mvert = mvert;
		me->mloop = mloop;
		me->mpoly = mpoly;
		me->totvert = dl->nr;
		me->totpoly = dl->parts;

		a = dl->nr;
		nors = dl->nors;
		verts = dl->verts;
		while (a--) {
			copy_v3_v3(mvert->co, verts);
			normal_float_to_short_v3(mvert->no, nors);
			mvert++;
			nors += 3;
			verts += 3;
		}
		
		a = dl->parts;
		index = dl->index;
		while (a--) {
			int count = index[2] != index[3] ? 4 : 3;

			mloop[0].v = index[0];
			mloop[1].v = index[1];
			mloop[2].v = index[2];
			if (count == 4)
				mloop[3].v = index[3];

			mpoly->totloop = count;
			mpoly->loopstart = (int)(mloop - allloop);
			mpoly->flag = ME_SMOOTH;


			mpoly++;
			mloop += count;
			me->totloop += count;
			index += 4;
		}

		BKE_mesh_update_customdata_pointers(me, true);

		BKE_mesh_calc_normals(me->mvert, me->totvert, me->mloop, me->mpoly, me->totloop, me->totpoly, NULL);

		BKE_mesh_calc_edges(me, true, false);
	}
}

/**
 * Specialized function to use when we _know_ existing edges don't overlap with poly edges.
 */
static void make_edges_mdata_extend(MEdge **r_alledge, int *r_totedge,
                                    const MPoly *mpoly, MLoop *mloop,
                                    const int totpoly)
{
	int totedge = *r_totedge;
	int totedge_new;
	EdgeHash *eh;
	const MPoly *mp;
	int i;

	eh = BLI_edgehash_new();

	for (i = 0, mp = mpoly; i < totpoly; i++, mp++) {
		BKE_mesh_poly_edgehash_insert(eh, mp, mloop + mp->loopstart);
	}

	totedge_new = BLI_edgehash_size(eh);

#ifdef DEBUG
	/* ensure that theres no overlap! */
	if (totedge_new) {
		MEdge *medge = *r_alledge;
		for (i = 0; i < totedge; i++, medge++) {
			BLI_assert(BLI_edgehash_haskey(eh, medge->v1, medge->v2) == false);
		}
	}
#endif

	if (totedge_new) {
		EdgeHashIterator *ehi;
		MEdge *medge;
		unsigned int e_index = totedge;

		*r_alledge = medge = (*r_alledge ? MEM_reallocN(*r_alledge, sizeof(MEdge) * (totedge + totedge_new)) :
		                                   MEM_callocN(sizeof(MEdge) * totedge_new, __func__));
		medge += totedge;

		totedge += totedge_new;

		/* --- */
		for (ehi = BLI_edgehashIterator_new(eh);
		     BLI_edgehashIterator_isDone(ehi) == FALSE;
		     BLI_edgehashIterator_step(ehi), ++medge, e_index++)
		{
			BLI_edgehashIterator_getKey(ehi, &medge->v1, &medge->v2);
			BLI_edgehashIterator_setValue(ehi, SET_UINT_IN_POINTER(e_index));

			medge->crease = medge->bweight = 0;
			medge->flag = ME_EDGEDRAW | ME_EDGERENDER;
		}
		BLI_edgehashIterator_free(ehi);

		*r_totedge = totedge;


		for (i = 0, mp = mpoly; i < totpoly; i++, mp++) {
			MLoop *l = &mloop[mp->loopstart];
			MLoop *l_prev = (l + (mp->totloop - 1));
			int j;
			for (j = 0; j < mp->totloop; j++, l++) {
				/* lookup hashed edge index */
				l_prev->e = GET_UINT_FROM_POINTER(BLI_edgehash_lookup(eh, l_prev->v, l->v));
				l_prev = l;
			}
		}
	}

	BLI_edgehash_free(eh, NULL);
}


/* Initialize mverts, medges and, faces for converting nurbs to mesh and derived mesh */
/* return non-zero on error */
int BKE_mesh_nurbs_to_mdata(Object *ob, MVert **allvert, int *totvert,
                            MEdge **alledge, int *totedge, MLoop **allloop, MPoly **allpoly,
                            int *totloop, int *totpoly)
{
	return BKE_mesh_nurbs_displist_to_mdata(ob, &ob->disp,
	                                        allvert, totvert,
	                                        alledge, totedge,
	                                        allloop, allpoly, NULL,
	                                        totloop, totpoly);
}

/* BMESH: this doesn't calculate all edges from polygons,
 * only free standing edges are calculated */

/* Initialize mverts, medges and, faces for converting nurbs to mesh and derived mesh */
/* use specified dispbase */
int BKE_mesh_nurbs_displist_to_mdata(Object *ob, ListBase *dispbase,
                                     MVert **allvert, int *_totvert,
                                     MEdge **alledge, int *_totedge,
                                     MLoop **allloop, MPoly **allpoly,
                                     MLoopUV **alluv,
                                     int *_totloop, int *_totpoly)
{
	Curve *cu = ob->data;
	DispList *dl;
	MVert *mvert;
	MPoly *mpoly;
	MLoop *mloop;
	MLoopUV *mloopuv = NULL;
	MEdge *medge;
	float *data;
	int a, b, ofs, vertcount, startvert, totvert = 0, totedge = 0, totloop = 0, totvlak = 0;
	int p1, p2, p3, p4, *index;
	const bool conv_polys = ((cu->flag & CU_3D) ||    /* 2d polys are filled with DL_INDEX3 displists */
	                         (ob->type == OB_SURF));  /* surf polys are never filled */

	/* count */
	dl = dispbase->first;
	while (dl) {
		if (dl->type == DL_SEGM) {
			totvert += dl->parts * dl->nr;
			totedge += dl->parts * (dl->nr - 1);
		}
		else if (dl->type == DL_POLY) {
			if (conv_polys) {
				totvert += dl->parts * dl->nr;
				totedge += dl->parts * dl->nr;
			}
		}
		else if (dl->type == DL_SURF) {
			int tot;
			totvert += dl->parts * dl->nr;
			tot = (dl->parts - 1 + ((dl->flag & DL_CYCL_V) == 2)) * (dl->nr - 1 + (dl->flag & DL_CYCL_U));
			totvlak += tot;
			totloop += tot * 4;
		}
		else if (dl->type == DL_INDEX3) {
			int tot;
			totvert += dl->nr;
			tot = dl->parts;
			totvlak += tot;
			totloop += tot * 3;
		}
		dl = dl->next;
	}

	if (totvert == 0) {
		/* error("can't convert"); */
		/* Make Sure you check ob->data is a curve */
		return -1;
	}

	*allvert = mvert = MEM_callocN(sizeof(MVert) * totvert, "nurbs_init mvert");
	*alledge = medge = MEM_callocN(sizeof(MEdge) * totedge, "nurbs_init medge");
	*allloop = mloop = MEM_callocN(sizeof(MLoop) * totvlak * 4, "nurbs_init mloop"); // totloop
	*allpoly = mpoly = MEM_callocN(sizeof(MPoly) * totvlak, "nurbs_init mloop");

	if (alluv)
		*alluv = mloopuv = MEM_callocN(sizeof(MLoopUV) * totvlak * 4, "nurbs_init mloopuv");
	
	/* verts and faces */
	vertcount = 0;

	dl = dispbase->first;
	while (dl) {
		int smooth = dl->rt & CU_SMOOTH ? 1 : 0;

		if (dl->type == DL_SEGM) {
			startvert = vertcount;
			a = dl->parts * dl->nr;
			data = dl->verts;
			while (a--) {
				copy_v3_v3(mvert->co, data);
				data += 3;
				vertcount++;
				mvert++;
			}

			for (a = 0; a < dl->parts; a++) {
				ofs = a * dl->nr;
				for (b = 1; b < dl->nr; b++) {
					medge->v1 = startvert + ofs + b - 1;
					medge->v2 = startvert + ofs + b;
					medge->flag = ME_LOOSEEDGE | ME_EDGERENDER | ME_EDGEDRAW;

					medge++;
				}
			}

		}
		else if (dl->type == DL_POLY) {
			if (conv_polys) {
				startvert = vertcount;
				a = dl->parts * dl->nr;
				data = dl->verts;
				while (a--) {
					copy_v3_v3(mvert->co, data);
					data += 3;
					vertcount++;
					mvert++;
				}

				for (a = 0; a < dl->parts; a++) {
					ofs = a * dl->nr;
					for (b = 0; b < dl->nr; b++) {
						medge->v1 = startvert + ofs + b;
						if (b == dl->nr - 1) medge->v2 = startvert + ofs;
						else medge->v2 = startvert + ofs + b + 1;
						medge->flag = ME_LOOSEEDGE | ME_EDGERENDER | ME_EDGEDRAW;
						medge++;
					}
				}
			}
		}
		else if (dl->type == DL_INDEX3) {
			startvert = vertcount;
			a = dl->nr;
			data = dl->verts;
			while (a--) {
				copy_v3_v3(mvert->co, data);
				data += 3;
				vertcount++;
				mvert++;
			}

			a = dl->parts;
			index = dl->index;
			while (a--) {
				mloop[0].v = startvert + index[0];
				mloop[1].v = startvert + index[2];
				mloop[2].v = startvert + index[1];
				mpoly->loopstart = (int)(mloop - (*allloop));
				mpoly->totloop = 3;
				mpoly->mat_nr = dl->col;

				if (mloopuv) {
					int i;

					for (i = 0; i < 3; i++, mloopuv++) {
						mloopuv->uv[0] = (mloop[i].v - startvert) / (float)(dl->nr - 1);
						mloopuv->uv[1] = 0.0f;
					}
				}

				if (smooth) mpoly->flag |= ME_SMOOTH;
				mpoly++;
				mloop += 3;
				index += 3;
			}
		}
		else if (dl->type == DL_SURF) {
			startvert = vertcount;
			a = dl->parts * dl->nr;
			data = dl->verts;
			while (a--) {
				copy_v3_v3(mvert->co, data);
				data += 3;
				vertcount++;
				mvert++;
			}

			for (a = 0; a < dl->parts; a++) {

				if ( (dl->flag & DL_CYCL_V) == 0 && a == dl->parts - 1) break;

				if (dl->flag & DL_CYCL_U) {         /* p2 -> p1 -> */
					p1 = startvert + dl->nr * a;    /* p4 -> p3 -> */
					p2 = p1 + dl->nr - 1;       /* -----> next row */
					p3 = p1 + dl->nr;
					p4 = p2 + dl->nr;
					b = 0;
				}
				else {
					p2 = startvert + dl->nr * a;
					p1 = p2 + 1;
					p4 = p2 + dl->nr;
					p3 = p1 + dl->nr;
					b = 1;
				}
				if ( (dl->flag & DL_CYCL_V) && a == dl->parts - 1) {
					p3 -= dl->parts * dl->nr;
					p4 -= dl->parts * dl->nr;
				}

				for (; b < dl->nr; b++) {
					mloop[0].v = p1;
					mloop[1].v = p3;
					mloop[2].v = p4;
					mloop[3].v = p2;
					mpoly->loopstart = (int)(mloop - (*allloop));
					mpoly->totloop = 4;
					mpoly->mat_nr = dl->col;

					if (mloopuv) {
						int orco_sizeu = dl->nr - 1;
						int orco_sizev = dl->parts - 1;
						int i;

						/* exception as handled in convertblender.c too */
						if (dl->flag & DL_CYCL_U) {
							orco_sizeu++;
							if (dl->flag & DL_CYCL_V)
								orco_sizev++;
						}

						for (i = 0; i < 4; i++, mloopuv++) {
							/* find uv based on vertex index into grid array */
							int v = mloop[i].v - startvert;

							mloopuv->uv[0] = (v / dl->nr) / (float)orco_sizev;
							mloopuv->uv[1] = (v % dl->nr) / (float)orco_sizeu;

							/* cyclic correction */
							if ((i == 0 || i == 1) && mloopuv->uv[1] == 0.0f)
								mloopuv->uv[1] = 1.0f;
						}
					}

					if (smooth) mpoly->flag |= ME_SMOOTH;
					mpoly++;
					mloop += 4;

					p4 = p3;
					p3++;
					p2 = p1;
					p1++;
				}
			}
		}

		dl = dl->next;
	}
	
	if (totvlak) {
		make_edges_mdata_extend(alledge, &totedge,
		                        *allpoly, *allloop, totvlak);
	}

	*_totpoly = totvlak;
	*_totloop = totloop;
	*_totedge = totedge;
	*_totvert = totvert;

	return 0;
}


/* this may fail replacing ob->data, be sure to check ob->type */
void BKE_mesh_from_nurbs_displist(Object *ob, ListBase *dispbase, const bool use_orco_uv)
{
	Main *bmain = G.main;
	Object *ob1;
	DerivedMesh *dm = ob->derivedFinal;
	Mesh *me;
	Curve *cu;
	MVert *allvert = NULL;
	MEdge *alledge = NULL;
	MLoop *allloop = NULL;
	MLoopUV *alluv = NULL;
	MPoly *allpoly = NULL;
	int totvert, totedge, totloop, totpoly;

	cu = ob->data;

	if (dm == NULL) {
		if (BKE_mesh_nurbs_displist_to_mdata(ob, dispbase, &allvert, &totvert,
		                                     &alledge, &totedge, &allloop,
		                                     &allpoly, (use_orco_uv) ? &alluv : NULL,
		                                     &totloop, &totpoly) != 0)
		{
			/* Error initializing */
			return;
		}

		/* make mesh */
		me = BKE_mesh_add(G.main, "Mesh");
		me->totvert = totvert;
		me->totedge = totedge;
		me->totloop = totloop;
		me->totpoly = totpoly;

		me->mvert = CustomData_add_layer(&me->vdata, CD_MVERT, CD_ASSIGN, allvert, me->totvert);
		me->medge = CustomData_add_layer(&me->edata, CD_MEDGE, CD_ASSIGN, alledge, me->totedge);
		me->mloop = CustomData_add_layer(&me->ldata, CD_MLOOP, CD_ASSIGN, allloop, me->totloop);
		me->mpoly = CustomData_add_layer(&me->pdata, CD_MPOLY, CD_ASSIGN, allpoly, me->totpoly);

		if (alluv) {
			const char *uvname = "Orco";
			me->mtpoly = CustomData_add_layer_named(&me->pdata, CD_MTEXPOLY, CD_DEFAULT, NULL, me->totpoly, uvname);
			me->mloopuv = CustomData_add_layer_named(&me->ldata, CD_MLOOPUV, CD_ASSIGN, alluv, me->totloop, uvname);
		}

		BKE_mesh_calc_normals(me->mvert, me->totvert, me->mloop, me->mpoly, me->totloop, me->totpoly, NULL);
	}
	else {
		me = BKE_mesh_add(G.main, "Mesh");
		DM_to_mesh(dm, me, ob, CD_MASK_MESH);
	}

	me->totcol = cu->totcol;
	me->mat = cu->mat;

	BKE_mesh_texspace_calc(me);

	cu->mat = NULL;
	cu->totcol = 0;

	if (ob->data) {
		BKE_libblock_free(&bmain->curve, ob->data);
	}
	ob->data = me;
	ob->type = OB_MESH;

	/* other users */
	ob1 = bmain->object.first;
	while (ob1) {
		if (ob1->data == cu) {
			ob1->type = OB_MESH;
		
			ob1->data = ob->data;
			id_us_plus((ID *)ob->data);
		}
		ob1 = ob1->id.next;
	}
}

void BKE_mesh_from_nurbs(Object *ob)
{
	BKE_mesh_from_nurbs_displist(ob, &ob->disp, false);
}

typedef struct EdgeLink {
	Link *next, *prev;
	void *edge;
} EdgeLink;

typedef struct VertLink {
	Link *next, *prev;
	unsigned int index;
} VertLink;

static void prependPolyLineVert(ListBase *lb, unsigned int index)
{
	VertLink *vl = MEM_callocN(sizeof(VertLink), "VertLink");
	vl->index = index;
	BLI_addhead(lb, vl);
}

static void appendPolyLineVert(ListBase *lb, unsigned int index)
{
	VertLink *vl = MEM_callocN(sizeof(VertLink), "VertLink");
	vl->index = index;
	BLI_addtail(lb, vl);
}

void BKE_mesh_to_curve_nurblist(DerivedMesh *dm, ListBase *nurblist, const int edge_users_test)
{
	MVert       *mvert = dm->getVertArray(dm);
	MEdge *med, *medge = dm->getEdgeArray(dm);
	MPoly *mp,  *mpoly = dm->getPolyArray(dm);
	MLoop       *mloop = dm->getLoopArray(dm);

	int dm_totedge = dm->getNumEdges(dm);
	int dm_totpoly = dm->getNumPolys(dm);
	int totedges = 0;
	int i;

	/* only to detect edge polylines */
	int *edge_users;

	ListBase edges = {NULL, NULL};

	/* get boundary edges */
	edge_users = MEM_callocN(sizeof(int) * dm_totedge, __func__);
	for (i = 0, mp = mpoly; i < dm_totpoly; i++, mp++) {
		MLoop *ml = &mloop[mp->loopstart];
		int j;
		for (j = 0; j < mp->totloop; j++, ml++) {
			edge_users[ml->e]++;
		}
	}

	/* create edges from all faces (so as to find edges not in any faces) */
	med = medge;
	for (i = 0; i < dm_totedge; i++, med++) {
		if (edge_users[i] == edge_users_test) {
			EdgeLink *edl = MEM_callocN(sizeof(EdgeLink), "EdgeLink");
			edl->edge = med;

			BLI_addtail(&edges, edl);   totedges++;
		}
	}
	MEM_freeN(edge_users);

	if (edges.first) {
		while (edges.first) {
			/* each iteration find a polyline and add this as a nurbs poly spline */

			ListBase polyline = {NULL, NULL}; /* store a list of VertLink's */
			int closed = FALSE;
			int totpoly = 0;
			MEdge *med_current = ((EdgeLink *)edges.last)->edge;
			unsigned int startVert = med_current->v1;
			unsigned int endVert = med_current->v2;
			int ok = TRUE;

			appendPolyLineVert(&polyline, startVert);   totpoly++;
			appendPolyLineVert(&polyline, endVert);     totpoly++;
			BLI_freelinkN(&edges, edges.last);          totedges--;

			while (ok) { /* while connected edges are found... */
				ok = FALSE;
				i = totedges;
				while (i) {
					EdgeLink *edl;

					i -= 1;
					edl = BLI_findlink(&edges, i);
					med = edl->edge;

					if (med->v1 == endVert) {
						endVert = med->v2;
						appendPolyLineVert(&polyline, med->v2); totpoly++;
						BLI_freelinkN(&edges, edl);             totedges--;
						ok = TRUE;
					}
					else if (med->v2 == endVert) {
						endVert = med->v1;
						appendPolyLineVert(&polyline, endVert); totpoly++;
						BLI_freelinkN(&edges, edl);             totedges--;
						ok = TRUE;
					}
					else if (med->v1 == startVert) {
						startVert = med->v2;
						prependPolyLineVert(&polyline, startVert);  totpoly++;
						BLI_freelinkN(&edges, edl);                 totedges--;
						ok = TRUE;
					}
					else if (med->v2 == startVert) {
						startVert = med->v1;
						prependPolyLineVert(&polyline, startVert);  totpoly++;
						BLI_freelinkN(&edges, edl);                 totedges--;
						ok = TRUE;
					}
				}
			}

			/* Now we have a polyline, make into a curve */
			if (startVert == endVert) {
				BLI_freelinkN(&polyline, polyline.last);
				totpoly--;
				closed = TRUE;
			}

			/* --- nurbs --- */
			{
				Nurb *nu;
				BPoint *bp;
				VertLink *vl;

				/* create new 'nurb' within the curve */
				nu = (Nurb *)MEM_callocN(sizeof(Nurb), "MeshNurb");

				nu->pntsu = totpoly;
				nu->pntsv = 1;
				nu->orderu = 4;
				nu->flagu = CU_NURB_ENDPOINT | (closed ? CU_NURB_CYCLIC : 0);  /* endpoint */
				nu->resolu = 12;

				nu->bp = (BPoint *)MEM_callocN(sizeof(BPoint) * totpoly, "bpoints");

				/* add points */
				vl = polyline.first;
				for (i = 0, bp = nu->bp; i < totpoly; i++, bp++, vl = (VertLink *)vl->next) {
					copy_v3_v3(bp->vec, mvert[vl->index].co);
					bp->f1 = SELECT;
					bp->radius = bp->weight = 1.0;
				}
				BLI_freelistN(&polyline);

				/* add nurb to curve */
				BLI_addtail(nurblist, nu);
			}
			/* --- done with nurbs --- */
		}
	}
}

void BKE_mesh_to_curve(Scene *scene, Object *ob)
{
	/* make new mesh data from the original copy */
	DerivedMesh *dm = mesh_get_derived_final(scene, ob, CD_MASK_MESH);
	ListBase nurblist = {NULL, NULL};
	bool needsFree = false;

	BKE_mesh_to_curve_nurblist(dm, &nurblist, 0);
	BKE_mesh_to_curve_nurblist(dm, &nurblist, 1);

	if (nurblist.first) {
		Curve *cu = BKE_curve_add(G.main, ob->id.name + 2, OB_CURVE);
		cu->flag |= CU_3D;

		cu->nurb = nurblist;

		((Mesh *)ob->data)->id.us--;
		ob->data = cu;
		ob->type = OB_CURVE;

		/* curve objects can't contain DM in usual cases, we could free memory */
		needsFree = true;
	}

	dm->needsFree = needsFree;
	dm->release(dm);

	if (needsFree) {
		ob->derivedFinal = NULL;

		/* curve object could have got bounding box only in special cases */
		if (ob->bb) {
			MEM_freeN(ob->bb);
			ob->bb = NULL;
		}
	}
}

void BKE_mesh_delete_material_index(Mesh *me, short index)
{
	int i;

	for (i = 0; i < me->totpoly; i++) {
		MPoly *mp = &((MPoly *) me->mpoly)[i];
		if (mp->mat_nr && mp->mat_nr >= index)
			mp->mat_nr--;
	}
	
	for (i = 0; i < me->totface; i++) {
		MFace *mf = &((MFace *) me->mface)[i];
		if (mf->mat_nr && mf->mat_nr >= index)
			mf->mat_nr--;
	}
}

void BKE_mesh_smooth_flag_set(Object *meshOb, int enableSmooth) 
{
	Mesh *me = meshOb->data;
	int i;

	for (i = 0; i < me->totpoly; i++) {
		MPoly *mp = &((MPoly *) me->mpoly)[i];

		if (enableSmooth) {
			mp->flag |= ME_SMOOTH;
		}
		else {
			mp->flag &= ~ME_SMOOTH;
		}
	}
	
	for (i = 0; i < me->totface; i++) {
		MFace *mf = &((MFace *) me->mface)[i];

		if (enableSmooth) {
			mf->flag |= ME_SMOOTH;
		}
		else {
			mf->flag &= ~ME_SMOOTH;
		}
	}
}

void BKE_mesh_calc_normals_mapping(MVert *mverts, int numVerts,
                                   MLoop *mloop, MPoly *mpolys, int numLoops, int numPolys, float (*polyNors_r)[3],
                                   MFace *mfaces, int numFaces, int *origIndexFace, float (*faceNors_r)[3])
{
	BKE_mesh_calc_normals_mapping_ex(mverts, numVerts, mloop, mpolys,
	                                 numLoops, numPolys, polyNors_r, mfaces, numFaces,
	                                 origIndexFace, faceNors_r, FALSE);
}

void BKE_mesh_calc_normals_mapping_ex(MVert *mverts, int numVerts,
                                      MLoop *mloop, MPoly *mpolys,
                                      int numLoops, int numPolys, float (*polyNors_r)[3],
                                      MFace *mfaces, int numFaces, int *origIndexFace, float (*faceNors_r)[3],
                                      const bool only_face_normals)
{
	float (*pnors)[3] = polyNors_r, (*fnors)[3] = faceNors_r;
	int i;
	MFace *mf;
	MPoly *mp;

	if (numPolys == 0) {
		return;
	}

	/* if we are not calculating verts and no verts were passes then we have nothing to do */
	if ((only_face_normals == TRUE) && (polyNors_r == NULL) && (faceNors_r == NULL)) {
		printf("%s: called with nothing to do\n", __func__);
		return;
	}

	if (!pnors) pnors = MEM_callocN(sizeof(float) * 3 * numPolys, "poly_nors mesh.c");
	/* if (!fnors) fnors = MEM_callocN(sizeof(float) * 3 * numFaces, "face nors mesh.c"); */ /* NO NEED TO ALLOC YET */


	if (only_face_normals == FALSE) {
		/* vertex normals are optional, they require some extra calculations,
		 * so make them optional */
		BKE_mesh_calc_normals(mverts, numVerts, mloop, mpolys, numLoops, numPolys, pnors);
	}
	else {
		/* only calc poly normals */
		mp = mpolys;
		for (i = 0; i < numPolys; i++, mp++) {
			BKE_mesh_calc_poly_normal(mp, mloop + mp->loopstart, mverts, pnors[i]);
		}
	}

	if (origIndexFace &&
	    /* fnors == faceNors_r */ /* NO NEED TO ALLOC YET */
	    fnors != NULL &&
	    numFaces)
	{
		mf = mfaces;
		for (i = 0; i < numFaces; i++, mf++, origIndexFace++) {
			if (*origIndexFace < numPolys) {
				copy_v3_v3(fnors[i], pnors[*origIndexFace]);
			}
			else {
				/* eek, we're not corresponding to polys */
				printf("error in BKE_mesh_calc_normals; tessellation face indices are incorrect.  normals may look bad.\n");
			}
		}
	}

	if (pnors != polyNors_r) MEM_freeN(pnors);
	/* if (fnors != faceNors_r) MEM_freeN(fnors); */ /* NO NEED TO ALLOC YET */

	fnors = pnors = NULL;
	
}

static void mesh_calc_normals_poly_accum(MPoly *mp, MLoop *ml,
                                         MVert *mvert, float polyno[3], float (*tnorms)[3])
{
	const int nverts = mp->totloop;
	float (*edgevecbuf)[3] = BLI_array_alloca(edgevecbuf, nverts);
	int i;

	/* Polygon Normal and edge-vector */
	/* inline version of #BKE_mesh_calc_poly_normal, also does edge-vectors */
	{
		int i_prev = nverts - 1;
		float const *v_prev = mvert[ml[i_prev].v].co;
		float const *v_curr;

		zero_v3(polyno);
		/* Newell's Method */
		for (i = 0; i < nverts; i++) {
			v_curr = mvert[ml[i].v].co;
			add_newell_cross_v3_v3v3(polyno, v_prev, v_curr);

			/* Unrelated to normalize, calcualte edge-vector */
			sub_v3_v3v3(edgevecbuf[i_prev], v_prev, v_curr);
			normalize_v3(edgevecbuf[i_prev]);
			i_prev = i;

			v_prev = v_curr;
		}
		if (UNLIKELY(normalize_v3(polyno) == 0.0f)) {
			polyno[2] = 1.0f; /* other axis set to 0.0 */
		}
	}

	/* accumulate angle weighted face normal */
	/* inline version of #accumulate_vertex_normals_poly */
	{
		const float *prev_edge = edgevecbuf[nverts - 1];

		for (i = 0; i < nverts; i++) {
			const float *cur_edge = edgevecbuf[i];

			/* calculate angle between the two poly edges incident on
			 * this vertex */
			const float fac = saacos(-dot_v3v3(cur_edge, prev_edge));

			/* accumulate */
			madd_v3_v3fl(tnorms[ml[i].v], polyno, fac);
			prev_edge = cur_edge;
		}
	}

}

void BKE_mesh_calc_normals(MVert *mverts, int numVerts, MLoop *mloop, MPoly *mpolys,
                           int UNUSED(numLoops), int numPolys, float (*polyNors_r)[3])
{
	float (*pnors)[3] = polyNors_r;
	float (*tnorms)[3];
	float tpnor[3];  /* temp poly normal */
	int i;
	MPoly *mp;

	/* first go through and calculate normals for all the polys */
	tnorms = MEM_callocN(sizeof(*tnorms) * numVerts, __func__);

	mp = mpolys;
	for (i = 0; i < numPolys; i++, mp++) {
		mesh_calc_normals_poly_accum(mp, mloop + mp->loopstart, mverts, pnors ? pnors[i] : tpnor, tnorms);
	}

	/* following Mesh convention; we use vertex coordinate itself for normal in this case */
	for (i = 0; i < numVerts; i++) {
		MVert *mv = &mverts[i];
		float *no = tnorms[i];

		if (UNLIKELY(normalize_v3(no) == 0.0f)) {
			normalize_v3_v3(no, mv->co);
		}

		normal_float_to_short_v3(mv->no, no);
	}

	MEM_freeN(tnorms);
}

void BKE_mesh_calc_normals_tessface(MVert *mverts, int numVerts, MFace *mfaces, int numFaces, float (*faceNors_r)[3])
{
	float (*tnorms)[3] = MEM_callocN(numVerts * sizeof(*tnorms), "tnorms");
	float (*fnors)[3] = (faceNors_r) ? faceNors_r : MEM_callocN(sizeof(*fnors) * numFaces, "meshnormals");
	int i;

	for (i = 0; i < numFaces; i++) {
		MFace *mf = &mfaces[i];
		float *f_no = fnors[i];
		float *n4 = (mf->v4) ? tnorms[mf->v4] : NULL;
		float *c4 = (mf->v4) ? mverts[mf->v4].co : NULL;

		if (mf->v4)
			normal_quad_v3(f_no, mverts[mf->v1].co, mverts[mf->v2].co, mverts[mf->v3].co, mverts[mf->v4].co);
		else
			normal_tri_v3(f_no, mverts[mf->v1].co, mverts[mf->v2].co, mverts[mf->v3].co);

		accumulate_vertex_normals(tnorms[mf->v1], tnorms[mf->v2], tnorms[mf->v3], n4,
		                          f_no, mverts[mf->v1].co, mverts[mf->v2].co, mverts[mf->v3].co, c4);
	}

	/* following Mesh convention; we use vertex coordinate itself for normal in this case */
	for (i = 0; i < numVerts; i++) {
		MVert *mv = &mverts[i];
		float *no = tnorms[i];
		
		if (UNLIKELY(normalize_v3(no) == 0.0f)) {
			normalize_v3_v3(no, mv->co);
		}

		normal_float_to_short_v3(mv->no, no);
	}
	
	MEM_freeN(tnorms);

	if (fnors != faceNors_r)
		MEM_freeN(fnors);
}

static void bm_corners_to_loops_ex(ID *id, CustomData *fdata, CustomData *ldata, CustomData *pdata,
                                   MFace *mface, int totloop, int findex, int loopstart, int numTex, int numCol)
{
	MTFace *texface;
	MTexPoly *texpoly;
	MCol *mcol;
	MLoopCol *mloopcol;
	MLoopUV *mloopuv;
	MFace *mf;
	int i;

	mf = mface + findex;

	for (i = 0; i < numTex; i++) {
		texface = CustomData_get_n(fdata, CD_MTFACE, findex, i);
		texpoly = CustomData_get_n(pdata, CD_MTEXPOLY, findex, i);

		ME_MTEXFACE_CPY(texpoly, texface);

		mloopuv = CustomData_get_n(ldata, CD_MLOOPUV, loopstart, i);
		copy_v2_v2(mloopuv->uv, texface->uv[0]); mloopuv++;
		copy_v2_v2(mloopuv->uv, texface->uv[1]); mloopuv++;
		copy_v2_v2(mloopuv->uv, texface->uv[2]); mloopuv++;

		if (mf->v4) {
			copy_v2_v2(mloopuv->uv, texface->uv[3]); mloopuv++;
		}
	}

	for (i = 0; i < numCol; i++) {
		mloopcol = CustomData_get_n(ldata, CD_MLOOPCOL, loopstart, i);
		mcol = CustomData_get_n(fdata, CD_MCOL, findex, i);

		MESH_MLOOPCOL_FROM_MCOL(mloopcol, &mcol[0]); mloopcol++;
		MESH_MLOOPCOL_FROM_MCOL(mloopcol, &mcol[1]); mloopcol++;
		MESH_MLOOPCOL_FROM_MCOL(mloopcol, &mcol[2]); mloopcol++;
		if (mf->v4) {
			MESH_MLOOPCOL_FROM_MCOL(mloopcol, &mcol[3]); mloopcol++;
		}
	}

	if (CustomData_has_layer(fdata, CD_MDISPS)) {
		MDisps *ld = CustomData_get(ldata, loopstart, CD_MDISPS);
		MDisps *fd = CustomData_get(fdata, findex, CD_MDISPS);
		float (*disps)[3] = fd->disps;
		int tot = mf->v4 ? 4 : 3;
		int side, corners;

		if (CustomData_external_test(fdata, CD_MDISPS)) {
			if (id && fdata->external) {
				CustomData_external_add(ldata, id, CD_MDISPS,
				                        totloop, fdata->external->filename);
			}
		}

		corners = multires_mdisp_corners(fd);

		if (corners == 0) {
			/* Empty MDisp layers appear in at least one of the sintel.blend files.
			 * Not sure why this happens, but it seems fine to just ignore them here.
			 * If (corners == 0) for a non-empty layer though, something went wrong. */
			BLI_assert(fd->totdisp == 0);
		}
		else {
			side = sqrt(fd->totdisp / corners);

			for (i = 0; i < tot; i++, disps += side * side, ld++) {
				ld->totdisp = side * side;
				ld->level = (int)(logf(side - 1.0f) / (float)M_LN2) + 1;

				if (ld->disps)
					MEM_freeN(ld->disps);

				ld->disps = MEM_callocN(sizeof(float) * 3 * side * side, "converted loop mdisps");
				if (fd->disps) {
					memcpy(ld->disps, disps, sizeof(float) * 3 * side * side);
				}
			}
		}
	}
}

void BKE_mesh_convert_mfaces_to_mpolys(Mesh *mesh)
{
	BKE_mesh_convert_mfaces_to_mpolys_ex(&mesh->id, &mesh->fdata, &mesh->ldata, &mesh->pdata,
	                                     mesh->totedge, mesh->totface, mesh->totloop, mesh->totpoly,
	                                     mesh->medge, mesh->mface,
	                                     &mesh->totloop, &mesh->totpoly, &mesh->mloop, &mesh->mpoly);

	BKE_mesh_update_customdata_pointers(mesh, true);
}

/* the same as BKE_mesh_convert_mfaces_to_mpolys but oriented to be used in do_versions from readfile.c
 * the difference is how active/render/clone/stencil indices are handled here
 *
 * normally thay're being set from pdata which totally makes sense for meshes which are already
 * converted to bmesh structures, but when loading older files indices shall be updated in other
 * way around, so newly added pdata and ldata would have this indices set based on fdata layer
 *
 * this is normally only needed when reading older files, in all other cases BKE_mesh_convert_mfaces_to_mpolys
 * shall be always used
 */
void BKE_mesh_do_versions_convert_mfaces_to_mpolys(Mesh *mesh)
{
	BKE_mesh_convert_mfaces_to_mpolys_ex(&mesh->id, &mesh->fdata, &mesh->ldata, &mesh->pdata,
	                                     mesh->totedge, mesh->totface, mesh->totloop, mesh->totpoly,
	                                     mesh->medge, mesh->mface,
	                                     &mesh->totloop, &mesh->totpoly, &mesh->mloop, &mesh->mpoly);

	CustomData_bmesh_do_versions_update_active_layers(&mesh->fdata, &mesh->pdata, &mesh->ldata);

	BKE_mesh_update_customdata_pointers(mesh, true);
}

void BKE_mesh_convert_mfaces_to_mpolys_ex(ID *id, CustomData *fdata, CustomData *ldata, CustomData *pdata,
                                          int totedge_i, int totface_i, int totloop_i, int totpoly_i,
                                          MEdge *medge, MFace *mface,
                                          int *totloop_r, int *totpoly_r,
                                          MLoop **mloop_r, MPoly **mpoly_r)
{
	MFace *mf;
	MLoop *ml, *mloop;
	MPoly *mp, *mpoly;
	MEdge *me;
	EdgeHash *eh;
	int numTex, numCol;
	int i, j, totloop, totpoly, *polyindex;

	/* just in case some of these layers are filled in (can happen with python created meshes) */
	CustomData_free(ldata, totloop_i);
	CustomData_free(pdata, totpoly_i);

	totpoly = totface_i;
	mpoly = MEM_callocN(sizeof(MPoly) * totpoly, "mpoly converted");
	CustomData_add_layer(pdata, CD_MPOLY, CD_ASSIGN, mpoly, totpoly);

	numTex = CustomData_number_of_layers(fdata, CD_MTFACE);
	numCol = CustomData_number_of_layers(fdata, CD_MCOL);

	totloop = 0;
	mf = mface;
	for (i = 0; i < totface_i; i++, mf++) {
		totloop += mf->v4 ? 4 : 3;
	}

	mloop = MEM_callocN(sizeof(MLoop) * totloop, "mloop converted");

	CustomData_add_layer(ldata, CD_MLOOP, CD_ASSIGN, mloop, totloop);

	CustomData_to_bmeshpoly(fdata, pdata, ldata, totloop, totpoly);

	if (id) {
		/* ensure external data is transferred */
		CustomData_external_read(fdata, id, CD_MASK_MDISPS, totface_i);
	}

	eh = BLI_edgehash_new();

	/* build edge hash */
	me = medge;
	for (i = 0; i < totedge_i; i++, me++) {
		BLI_edgehash_insert(eh, me->v1, me->v2, SET_INT_IN_POINTER(i));

		/* unrelated but avoid having the FGON flag enabled, so we can reuse it later for something else */
		me->flag &= ~ME_FGON;
	}

	polyindex = CustomData_get_layer(fdata, CD_ORIGINDEX);

	j = 0; /* current loop index */
	ml = mloop;
	mf = mface;
	mp = mpoly;
	for (i = 0; i < totface_i; i++, mf++, mp++) {
		mp->loopstart = j;

		mp->totloop = mf->v4 ? 4 : 3;

		mp->mat_nr = mf->mat_nr;
		mp->flag = mf->flag;

#       define ML(v1, v2) { \
			ml->v = mf->v1; ml->e = GET_INT_FROM_POINTER(BLI_edgehash_lookup(eh, mf->v1, mf->v2)); ml++; j++; \
		} (void)0

		ML(v1, v2);
		ML(v2, v3);
		if (mf->v4) {
			ML(v3, v4);
			ML(v4, v1);
		}
		else {
			ML(v3, v1);
		}

#       undef ML

		bm_corners_to_loops_ex(id, fdata, ldata, pdata, mface, totloop, i, mp->loopstart, numTex, numCol);

		if (polyindex) {
			*polyindex = i;
			polyindex++;
		}
	}

	/* note, we don't convert NGons at all, these are not even real ngons,
	 * they have their own UV's, colors etc - its more an editing feature. */

	BLI_edgehash_free(eh, NULL);

	*totpoly_r = totpoly;
	*totloop_r = totloop;
	*mpoly_r = mpoly;
	*mloop_r = mloop;
}

float (*BKE_mesh_vertexCos_get(Mesh *me, int *r_numVerts))[3]
{
	int i, numVerts = me->totvert;
	float (*cos)[3] = MEM_mallocN(sizeof(*cos) * numVerts, "vertexcos1");

	if (r_numVerts) *r_numVerts = numVerts;
	for (i = 0; i < numVerts; i++)
		copy_v3_v3(cos[i], me->mvert[i].co);

	return cos;
}


/* ngon version wip, based on EDBM_uv_vert_map_create */
/* this replaces the non bmesh function (in trunk) which takes MTFace's, if we ever need it back we could
 * but for now this replaces it because its unused. */

UvVertMap *BKE_mesh_uv_vert_map_create(struct MPoly *mpoly, struct MLoop *mloop, struct MLoopUV *mloopuv,
                                       unsigned int totpoly, unsigned int totvert, int selected, float *limit)
{
	UvVertMap *vmap;
	UvMapVert *buf;
	MPoly *mp;
	unsigned int a;
	int i, totuv, nverts;

	totuv = 0;

	/* generate UvMapVert array */
	mp = mpoly;
	for (a = 0; a < totpoly; a++, mp++)
		if (!selected || (!(mp->flag & ME_HIDE) && (mp->flag & ME_FACE_SEL)))
			totuv += mp->totloop;

	if (totuv == 0)
		return NULL;
	
	vmap = (UvVertMap *)MEM_callocN(sizeof(*vmap), "UvVertMap");
	if (!vmap)
		return NULL;

	vmap->vert = (UvMapVert **)MEM_callocN(sizeof(*vmap->vert) * totvert, "UvMapVert*");
	buf = vmap->buf = (UvMapVert *)MEM_callocN(sizeof(*vmap->buf) * totuv, "UvMapVert");

	if (!vmap->vert || !vmap->buf) {
		BKE_mesh_uv_vert_map_free(vmap);
		return NULL;
	}

	mp = mpoly;
	for (a = 0; a < totpoly; a++, mp++) {
		if (!selected || (!(mp->flag & ME_HIDE) && (mp->flag & ME_FACE_SEL))) {
			nverts = mp->totloop;

			for (i = 0; i < nverts; i++) {
				buf->tfindex = i;
				buf->f = a;
				buf->separate = 0;
				buf->next = vmap->vert[mloop[mp->loopstart + i].v];
				vmap->vert[mloop[mp->loopstart + i].v] = buf;
				buf++;
			}
		}
	}
	
	/* sort individual uvs for each vert */
	for (a = 0; a < totvert; a++) {
		UvMapVert *newvlist = NULL, *vlist = vmap->vert[a];
		UvMapVert *iterv, *v, *lastv, *next;
		float *uv, *uv2, uvdiff[2];

		while (vlist) {
			v = vlist;
			vlist = vlist->next;
			v->next = newvlist;
			newvlist = v;

			uv = mloopuv[mpoly[v->f].loopstart + v->tfindex].uv;
			lastv = NULL;
			iterv = vlist;

			while (iterv) {
				next = iterv->next;

				uv2 = mloopuv[mpoly[iterv->f].loopstart + iterv->tfindex].uv;
				sub_v2_v2v2(uvdiff, uv2, uv);


				if (fabsf(uv[0] - uv2[0]) < limit[0] && fabsf(uv[1] - uv2[1]) < limit[1]) {
					if (lastv) lastv->next = next;
					else vlist = next;
					iterv->next = newvlist;
					newvlist = iterv;
				}
				else
					lastv = iterv;

				iterv = next;
			}

			newvlist->separate = 1;
		}

		vmap->vert[a] = newvlist;
	}
	
	return vmap;
}

UvMapVert *BKE_mesh_uv_vert_map_get_vert(UvVertMap *vmap, unsigned int v)
{
	return vmap->vert[v];
}

void BKE_mesh_uv_vert_map_free(UvVertMap *vmap)
{
	if (vmap) {
		if (vmap->vert) MEM_freeN(vmap->vert);
		if (vmap->buf) MEM_freeN(vmap->buf);
		MEM_freeN(vmap);
	}
}

/* Generates a map where the key is the vertex and the value is a list
 * of polys that use that vertex as a corner. The lists are allocated
 * from one memory pool. */
void BKE_mesh_vert_poly_map_create(MeshElemMap **map, int **mem,
                                   const MPoly *mpoly, const MLoop *mloop,
                                   int totvert, int totpoly, int totloop)
{
	int i, j;
	int *indices;

	(*map) = MEM_callocN(sizeof(MeshElemMap) * totvert, "vert poly map");
	(*mem) = MEM_mallocN(sizeof(int) * totloop, "vert poly map mem");

	/* Count number of polys for each vertex */
	for (i = 0; i < totpoly; i++) {
		const MPoly *p = &mpoly[i];
		
		for (j = 0; j < p->totloop; j++)
			(*map)[mloop[p->loopstart + j].v].count++;
	}

	/* Assign indices mem */
	indices = (*mem);
	for (i = 0; i < totvert; i++) {
		(*map)[i].indices = indices;
		indices += (*map)[i].count;

		/* Reset 'count' for use as index in last loop */
		(*map)[i].count = 0;
	}
		
	/* Find the users */
	for (i = 0; i < totpoly; i++) {
		const MPoly *p = &mpoly[i];
		
		for (j = 0; j < p->totloop; j++) {
			int v = mloop[p->loopstart + j].v;
			
			(*map)[v].indices[(*map)[v].count] = i;
			(*map)[v].count++;
		}
	}
}

/* Generates a map where the key is the vertex and the value is a list
 * of edges that use that vertex as an endpoint. The lists are allocated
 * from one memory pool. */
void BKE_mesh_vert_edge_map_create(MeshElemMap **map, int **mem,
                                   const MEdge *medge, int totvert, int totedge)
{
	int i, *indices;

	(*map) = MEM_callocN(sizeof(MeshElemMap) * totvert, "vert-edge map");
	(*mem) = MEM_mallocN(sizeof(int) * totedge * 2, "vert-edge map mem");

	/* Count number of edges for each vertex */
	for (i = 0; i < totedge; i++) {
		(*map)[medge[i].v1].count++;
		(*map)[medge[i].v2].count++;
	}

	/* Assign indices mem */
	indices = (*mem);
	for (i = 0; i < totvert; i++) {
		(*map)[i].indices = indices;
		indices += (*map)[i].count;

		/* Reset 'count' for use as index in last loop */
		(*map)[i].count = 0;
	}
		
	/* Find the users */
	for (i = 0; i < totedge; i++) {
		const int v[2] = {medge[i].v1, medge[i].v2};

		(*map)[v[0]].indices[(*map)[v[0]].count] = i;
		(*map)[v[1]].indices[(*map)[v[1]].count] = i;
		
		(*map)[v[0]].count++;
		(*map)[v[1]].count++;
	}
}

void BKE_mesh_loops_to_mface_corners(CustomData *fdata, CustomData *ldata,
                                     CustomData *pdata, int lindex[4], int findex,
                                     const int polyindex,
                                     const int mf_len, /* 3 or 4 */

                                     /* cache values to avoid lookups every time */
                                     const int numTex, /* CustomData_number_of_layers(pdata, CD_MTEXPOLY) */
                                     const int numCol, /* CustomData_number_of_layers(ldata, CD_MLOOPCOL) */
                                     const int hasPCol, /* CustomData_has_layer(ldata, CD_PREVIEW_MLOOPCOL) */
                                     const int hasOrigSpace /* CustomData_has_layer(ldata, CD_ORIGSPACE_MLOOP) */
                                     )
{
	MTFace *texface;
	MTexPoly *texpoly;
	MCol *mcol;
	MLoopCol *mloopcol;
	MLoopUV *mloopuv;
	int i, j;
	
	for (i = 0; i < numTex; i++) {
		texface = CustomData_get_n(fdata, CD_MTFACE, findex, i);
		texpoly = CustomData_get_n(pdata, CD_MTEXPOLY, polyindex, i);

		ME_MTEXFACE_CPY(texface, texpoly);

		for (j = 0; j < mf_len; j++) {
			mloopuv = CustomData_get_n(ldata, CD_MLOOPUV, lindex[j], i);
			copy_v2_v2(texface->uv[j], mloopuv->uv);
		}
	}

	for (i = 0; i < numCol; i++) {
		mcol = CustomData_get_n(fdata, CD_MCOL, findex, i);

		for (j = 0; j < mf_len; j++) {
			mloopcol = CustomData_get_n(ldata, CD_MLOOPCOL, lindex[j], i);
			MESH_MLOOPCOL_TO_MCOL(mloopcol, &mcol[j]);
		}
	}

	if (hasPCol) {
		mcol = CustomData_get(fdata,  findex, CD_PREVIEW_MCOL);

		for (j = 0; j < mf_len; j++) {
			mloopcol = CustomData_get(ldata, lindex[j], CD_PREVIEW_MLOOPCOL);
			MESH_MLOOPCOL_TO_MCOL(mloopcol, &mcol[j]);
		}
	}

	if (hasOrigSpace) {
		OrigSpaceFace *of = CustomData_get(fdata, findex, CD_ORIGSPACE);
		OrigSpaceLoop *lof;

		for (j = 0; j < mf_len; j++) {
			lof = CustomData_get(ldata, lindex[j], CD_ORIGSPACE_MLOOP);
			copy_v2_v2(of->uv[j], lof->uv);
		}
	}
}

/*
 * this function recreates a tessellation.
 * returns number of tessellation faces.
 */
int BKE_mesh_recalc_tessellation(CustomData *fdata,
                                 CustomData *ldata, CustomData *pdata,
                                 MVert *mvert, int totface, int totloop,
                                 int totpoly,
                                 /* when tessellating to recalculate normals after
                                  * we can skip copying here */
                                 const bool do_face_nor_cpy)
{
	/* use this to avoid locking pthread for _every_ polygon
	 * and calling the fill function */

#define USE_TESSFACE_SPEEDUP
#define USE_TESSFACE_QUADS // NEEDS FURTHER TESTING

#define TESSFACE_SCANFILL (1 << 0)
#define TESSFACE_IS_QUAD  (1 << 1)

	const int looptris_tot = poly_to_tri_count(totpoly, totloop);

	MPoly *mp, *mpoly;
	MLoop *ml, *mloop;
	MFace *mface, *mf;
	ScanFillContext sf_ctx;
	ScanFillVert *sf_vert, *sf_vert_last, *sf_vert_first;
	ScanFillFace *sf_tri;
	int *mface_to_poly_map;
	int lindex[4]; /* only ever use 3 in this case */
	int poly_index, j, mface_index;

	const int numTex = CustomData_number_of_layers(pdata, CD_MTEXPOLY);
	const int numCol = CustomData_number_of_layers(ldata, CD_MLOOPCOL);
	const int hasPCol = CustomData_has_layer(ldata, CD_PREVIEW_MLOOPCOL);
	const int hasOrigSpace = CustomData_has_layer(ldata, CD_ORIGSPACE_MLOOP);

	mpoly = CustomData_get_layer(pdata, CD_MPOLY);
	mloop = CustomData_get_layer(ldata, CD_MLOOP);

	/* allocate the length of totfaces, avoid many small reallocs,
	 * if all faces are tri's it will be correct, quads == 2x allocs */
	/* take care. we are _not_ calloc'ing so be sure to initialize each field */
	mface_to_poly_map = MEM_mallocN(sizeof(*mface_to_poly_map) * looptris_tot, __func__);
	mface             = MEM_mallocN(sizeof(*mface) *             looptris_tot, __func__);

	mface_index = 0;
	mp = mpoly;
	for (poly_index = 0; poly_index < totpoly; poly_index++, mp++) {
		if (mp->totloop < 3) {
			/* do nothing */
		}

#ifdef USE_TESSFACE_SPEEDUP

#define ML_TO_MF(i1, i2, i3)                                                  \
		mface_to_poly_map[mface_index] = poly_index;                          \
		mf = &mface[mface_index];                                             \
		/* set loop indices, transformed to vert indices later */             \
		mf->v1 = mp->loopstart + i1;                                          \
		mf->v2 = mp->loopstart + i2;                                          \
		mf->v3 = mp->loopstart + i3;                                          \
		mf->v4 = 0;                                                           \
		mf->mat_nr = mp->mat_nr;                                              \
		mf->flag = mp->flag;                                                  \
		mf->edcode = 0;                                                       \
		(void)0

/* ALMOST IDENTICAL TO DEFINE ABOVE (see EXCEPTION) */
#define ML_TO_MF_QUAD()                                                       \
		mface_to_poly_map[mface_index] = poly_index;                          \
		mf = &mface[mface_index];                                             \
		/* set loop indices, transformed to vert indices later */             \
		mf->v1 = mp->loopstart + 0; /* EXCEPTION */                           \
		mf->v2 = mp->loopstart + 1; /* EXCEPTION */                           \
		mf->v3 = mp->loopstart + 2; /* EXCEPTION */                           \
		mf->v4 = mp->loopstart + 3; /* EXCEPTION */                           \
		mf->mat_nr = mp->mat_nr;                                              \
		mf->flag = mp->flag;                                                  \
		mf->edcode = TESSFACE_IS_QUAD; /* EXCEPTION */                        \
		(void)0


		else if (mp->totloop == 3) {
			ML_TO_MF(0, 1, 2);
			mface_index++;
		}
		else if (mp->totloop == 4) {
#ifdef USE_TESSFACE_QUADS
			ML_TO_MF_QUAD();
			mface_index++;
#else
			ML_TO_MF(0, 1, 2);
			mface_index++;
			ML_TO_MF(0, 2, 3);
			mface_index++;
#endif
		}
#endif /* USE_TESSFACE_SPEEDUP */
		else {
			int totfilltri;

			ml = mloop + mp->loopstart;
			
			BLI_scanfill_begin(&sf_ctx);
			sf_vert_first = NULL;
			sf_vert_last = NULL;
			for (j = 0; j < mp->totloop; j++, ml++) {
				sf_vert = BLI_scanfill_vert_add(&sf_ctx, mvert[ml->v].co);
	
				sf_vert->keyindex = mp->loopstart + j;
	
				if (sf_vert_last)
					BLI_scanfill_edge_add(&sf_ctx, sf_vert_last, sf_vert);
	
				if (!sf_vert_first)
					sf_vert_first = sf_vert;
				sf_vert_last = sf_vert;
			}
			BLI_scanfill_edge_add(&sf_ctx, sf_vert_last, sf_vert_first);
			
			totfilltri = BLI_scanfill_calc(&sf_ctx, 0);
			BLI_assert(totfilltri <= mp->totloop - 2);
			(void)totfilltri;

			for (sf_tri = sf_ctx.fillfacebase.first; sf_tri; sf_tri = sf_tri->next, mf++) {
				mface_to_poly_map[mface_index] = poly_index;
				mf = &mface[mface_index];

				/* set loop indices, transformed to vert indices later */
				mf->v1 = sf_tri->v1->keyindex;
				mf->v2 = sf_tri->v2->keyindex;
				mf->v3 = sf_tri->v3->keyindex;
				mf->v4 = 0;

				mf->mat_nr = mp->mat_nr;
				mf->flag = mp->flag;

#ifdef USE_TESSFACE_SPEEDUP
				mf->edcode = TESSFACE_SCANFILL; /* tag for sorting loop indices */
#endif

				mface_index++;
			}
	
			BLI_scanfill_end(&sf_ctx);
		}
	}

	CustomData_free(fdata, totface);
	totface = mface_index;

	BLI_assert(totface <= looptris_tot);

	/* not essential but without this we store over-alloc'd memory in the CustomData layers */
	if (LIKELY(looptris_tot != totface)) {
		mface = MEM_reallocN(mface, sizeof(*mface) * totface);
		mface_to_poly_map = MEM_reallocN(mface_to_poly_map, sizeof(*mface_to_poly_map) * totface);
	}

	CustomData_add_layer(fdata, CD_MFACE, CD_ASSIGN, mface, totface);

	/* CD_ORIGINDEX will contain an array of indices from tessfaces to the polygons
	 * they are directly tessellated from */
	CustomData_add_layer(fdata, CD_ORIGINDEX, CD_ASSIGN, mface_to_poly_map, totface);
	CustomData_from_bmeshpoly(fdata, pdata, ldata, totface);

	if (do_face_nor_cpy) {
		/* If polys have a normals layer, copying that to faces can help
		 * avoid the need to recalculate normals later */
		if (CustomData_has_layer(pdata, CD_NORMAL)) {
			float (*pnors)[3] = CustomData_get_layer(pdata, CD_NORMAL);
			float (*fnors)[3] = CustomData_add_layer(fdata, CD_NORMAL, CD_CALLOC, NULL, totface);
			for (mface_index = 0; mface_index < totface; mface_index++) {
				copy_v3_v3(fnors[mface_index], pnors[mface_to_poly_map[mface_index]]);
			}
		}
	}

	mf = mface;
	for (mface_index = 0; mface_index < totface; mface_index++, mf++) {

#ifdef USE_TESSFACE_QUADS
		const int mf_len = mf->edcode & TESSFACE_IS_QUAD ? 4 : 3;
#endif

#ifdef USE_TESSFACE_SPEEDUP
		/* skip sorting when not using ngons */
		if (UNLIKELY(mf->edcode & TESSFACE_SCANFILL))
#endif
		{
			/* sort loop indices to ensure winding is correct */
			if (mf->v1 > mf->v2) SWAP(unsigned int, mf->v1, mf->v2);
			if (mf->v2 > mf->v3) SWAP(unsigned int, mf->v2, mf->v3);
			if (mf->v1 > mf->v2) SWAP(unsigned int, mf->v1, mf->v2);

			if (mf->v1 > mf->v2) SWAP(unsigned int, mf->v1, mf->v2);
			if (mf->v2 > mf->v3) SWAP(unsigned int, mf->v2, mf->v3);
			if (mf->v1 > mf->v2) SWAP(unsigned int, mf->v1, mf->v2);
		}

		/* end abusing the edcode */
#if defined(USE_TESSFACE_QUADS) || defined(USE_TESSFACE_SPEEDUP)
		mf->edcode = 0;
#endif


		lindex[0] = mf->v1;
		lindex[1] = mf->v2;
		lindex[2] = mf->v3;
#ifdef USE_TESSFACE_QUADS
		if (mf_len == 4) lindex[3] = mf->v4;
#endif

		/*transform loop indices to vert indices*/
		mf->v1 = mloop[mf->v1].v;
		mf->v2 = mloop[mf->v2].v;
		mf->v3 = mloop[mf->v3].v;
#ifdef USE_TESSFACE_QUADS
		if (mf_len == 4) mf->v4 = mloop[mf->v4].v;
#endif

		BKE_mesh_loops_to_mface_corners(fdata, ldata, pdata,
		                                lindex, mface_index, mface_to_poly_map[mface_index],
#ifdef USE_TESSFACE_QUADS
		                                mf_len,
#else
		                                3,
#endif
		                                numTex, numCol, hasPCol, hasOrigSpace);


#ifdef USE_TESSFACE_QUADS
		test_index_face(mf, fdata, mface_index, mf_len);
#endif

	}

	return totface;

#undef USE_TESSFACE_SPEEDUP

}


#ifdef USE_BMESH_SAVE_AS_COMPAT

/*
 * this function recreates a tessellation.
 * returns number of tessellation faces.
 */
int BKE_mesh_mpoly_to_mface(struct CustomData *fdata, struct CustomData *ldata,
                            struct CustomData *pdata, int totface, int UNUSED(totloop), int totpoly)
{
	MLoop *mloop;

	int lindex[4];
	int i;
	int k;

	MPoly *mp, *mpoly;
	MFace *mface = NULL, *mf;
	BLI_array_declare(mface);

	const int numTex = CustomData_number_of_layers(pdata, CD_MTEXPOLY);
	const int numCol = CustomData_number_of_layers(ldata, CD_MLOOPCOL);
	const int hasPCol = CustomData_has_layer(ldata, CD_PREVIEW_MLOOPCOL);
	const int hasOrigSpace = CustomData_has_layer(ldata, CD_ORIGSPACE_MLOOP);

	mpoly = CustomData_get_layer(pdata, CD_MPOLY);
	mloop = CustomData_get_layer(ldata, CD_MLOOP);

	mp = mpoly;
	k = 0;
	for (i = 0; i < totpoly; i++, mp++) {
		if (ELEM(mp->totloop, 3, 4)) {
			BLI_array_grow_one(mface);
			mf = &mface[k];

			mf->mat_nr = mp->mat_nr;
			mf->flag = mp->flag;

			mf->v1 = mp->loopstart + 0;
			mf->v2 = mp->loopstart + 1;
			mf->v3 = mp->loopstart + 2;
			mf->v4 = (mp->totloop == 4) ? (mp->loopstart + 3) : 0;

			/* abuse edcode for temp storage and clear next loop */
			mf->edcode = (char)mp->totloop; /* only ever 3 or 4 */

			k++;
		}
	}

	CustomData_free(fdata, totface);

	totface = k;

	CustomData_add_layer(fdata, CD_MFACE, CD_ASSIGN, mface, totface);

	CustomData_from_bmeshpoly(fdata, pdata, ldata, totface);

	mp = mpoly;
	k = 0;
	for (i = 0; i < totpoly; i++, mp++) {
		if (ELEM(mp->totloop, 3, 4)) {
			mf = &mface[k];

			if (mf->edcode == 3) {
				/* sort loop indices to ensure winding is correct */
				/* NO SORT - looks like we can skip this */

				lindex[0] = mf->v1;
				lindex[1] = mf->v2;
				lindex[2] = mf->v3;
				lindex[3] = 0; /* unused */

				/* transform loop indices to vert indices */
				mf->v1 = mloop[mf->v1].v;
				mf->v2 = mloop[mf->v2].v;
				mf->v3 = mloop[mf->v3].v;

				BKE_mesh_loops_to_mface_corners(fdata, ldata, pdata,
				                                lindex, k, i, 3,
				                                numTex, numCol, hasPCol, hasOrigSpace);
				test_index_face(mf, fdata, k, 3);
			}
			else {
				/* sort loop indices to ensure winding is correct */
				/* NO SORT - looks like we can skip this */

				lindex[0] = mf->v1;
				lindex[1] = mf->v2;
				lindex[2] = mf->v3;
				lindex[3] = mf->v4;

				/* transform loop indices to vert indices */
				mf->v1 = mloop[mf->v1].v;
				mf->v2 = mloop[mf->v2].v;
				mf->v3 = mloop[mf->v3].v;
				mf->v4 = mloop[mf->v4].v;

				BKE_mesh_loops_to_mface_corners(fdata, ldata, pdata,
				                                lindex, k, i, 4,
				                                numTex, numCol, hasPCol, hasOrigSpace);
				test_index_face(mf, fdata, k, 4);
			}

			mf->edcode = 0;

			k++;
		}
	}

	return k;
}
#endif /* USE_BMESH_SAVE_AS_COMPAT */

/*
 * COMPUTE POLY NORMAL
 *
 * Computes the normal of a planar 
 * polygon See Graphics Gems for 
 * computing newell normal.
 *
 */
static void mesh_calc_ngon_normal(MPoly *mpoly, MLoop *loopstart, 
                                  MVert *mvert, float normal[3])
{
	const int nverts = mpoly->totloop;
	float const *v_prev = mvert[loopstart[nverts - 1].v].co;
	float const *v_curr;
	int i;

	zero_v3(normal);

	/* Newell's Method */
	for (i = 0; i < nverts; i++) {
		v_curr = mvert[loopstart[i].v].co;
		add_newell_cross_v3_v3v3(normal, v_prev, v_curr);
		v_prev = v_curr;
	}

	if (UNLIKELY(normalize_v3(normal) == 0.0f)) {
		normal[2] = 1.0f; /* other axis set to 0.0 */
	}
}

void BKE_mesh_calc_poly_normal(MPoly *mpoly, MLoop *loopstart,
                               MVert *mvarray, float no[3])
{
	if (mpoly->totloop > 4) {
		mesh_calc_ngon_normal(mpoly, loopstart, mvarray, no);
	}
	else if (mpoly->totloop == 3) {
		normal_tri_v3(no,
		              mvarray[loopstart[0].v].co,
		              mvarray[loopstart[1].v].co,
		              mvarray[loopstart[2].v].co
		              );
	}
	else if (mpoly->totloop == 4) {
		normal_quad_v3(no,
		               mvarray[loopstart[0].v].co,
		               mvarray[loopstart[1].v].co,
		               mvarray[loopstart[2].v].co,
		               mvarray[loopstart[3].v].co
		               );
	}
	else { /* horrible, two sided face! */
		no[0] = 0.0;
		no[1] = 0.0;
		no[2] = 1.0;
	}
}
/* duplicate of function above _but_ takes coords rather then mverts */
static void mesh_calc_ngon_normal_coords(MPoly *mpoly, MLoop *loopstart,
                                         const float (*vertex_coords)[3], float normal[3])
{
	const int nverts = mpoly->totloop;
	float const *v_prev = vertex_coords[loopstart[nverts - 1].v];
	float const *v_curr;
	int i;

	zero_v3(normal);

	/* Newell's Method */
	for (i = 0; i < nverts; i++) {
		v_curr = vertex_coords[loopstart[i].v];
		add_newell_cross_v3_v3v3(normal, v_prev, v_curr);
		v_prev = v_curr;
	}

	if (UNLIKELY(normalize_v3(normal) == 0.0f)) {
		normal[2] = 1.0f; /* other axis set to 0.0 */
	}
}

void BKE_mesh_calc_poly_normal_coords(MPoly *mpoly, MLoop *loopstart,
                                      const float (*vertex_coords)[3], float no[3])
{
	if (mpoly->totloop > 4) {
		mesh_calc_ngon_normal_coords(mpoly, loopstart, vertex_coords, no);
	}
	else if (mpoly->totloop == 3) {
		normal_tri_v3(no,
		              vertex_coords[loopstart[0].v],
		              vertex_coords[loopstart[1].v],
		              vertex_coords[loopstart[2].v]
		              );
	}
	else if (mpoly->totloop == 4) {
		normal_quad_v3(no,
		               vertex_coords[loopstart[0].v],
		               vertex_coords[loopstart[1].v],
		               vertex_coords[loopstart[2].v],
		               vertex_coords[loopstart[3].v]
		               );
	}
	else { /* horrible, two sided face! */
		no[0] = 0.0;
		no[1] = 0.0;
		no[2] = 1.0;
	}
}

static void mesh_calc_ngon_center(MPoly *mpoly, MLoop *loopstart,
                                  MVert *mvert, float cent[3])
{
	const float w = 1.0f / (float)mpoly->totloop;
	int i;

	zero_v3(cent);

	for (i = 0; i < mpoly->totloop; i++) {
		madd_v3_v3fl(cent, mvert[(loopstart++)->v].co, w);
	}
}

void BKE_mesh_calc_poly_center(MPoly *mpoly, MLoop *loopstart,
                               MVert *mvarray, float cent[3])
{
	if (mpoly->totloop == 3) {
		cent_tri_v3(cent,
		            mvarray[loopstart[0].v].co,
		            mvarray[loopstart[1].v].co,
		            mvarray[loopstart[2].v].co
		            );
	}
	else if (mpoly->totloop == 4) {
		cent_quad_v3(cent,
		             mvarray[loopstart[0].v].co,
		             mvarray[loopstart[1].v].co,
		             mvarray[loopstart[2].v].co,
		             mvarray[loopstart[3].v].co
		             );
	}
	else {
		mesh_calc_ngon_center(mpoly, loopstart, mvarray, cent);
	}
}

/* note, passing polynormal is only a speedup so we can skip calculating it */
float BKE_mesh_calc_poly_area(MPoly *mpoly, MLoop *loopstart,
                              MVert *mvarray, const float polynormal[3])
{
	if (mpoly->totloop == 3) {
		return area_tri_v3(mvarray[loopstart[0].v].co,
		                   mvarray[loopstart[1].v].co,
		                   mvarray[loopstart[2].v].co
		                   );
	}
	else if (mpoly->totloop == 4) {
		return area_quad_v3(mvarray[loopstart[0].v].co,
		                    mvarray[loopstart[1].v].co,
		                    mvarray[loopstart[2].v].co,
		                    mvarray[loopstart[3].v].co
		                    );
	}
	else {
		int i;
		MLoop *l_iter = loopstart;
		float area, polynorm_local[3];
		float (*vertexcos)[3] = BLI_array_alloca(vertexcos, mpoly->totloop);
		const float *no = polynormal ? polynormal : polynorm_local;

		/* pack vertex cos into an array for area_poly_v3 */
		for (i = 0; i < mpoly->totloop; i++, l_iter++) {
			copy_v3_v3(vertexcos[i], mvarray[l_iter->v].co);
		}

		/* need normal for area_poly_v3 as well */
		if (polynormal == NULL) {
			BKE_mesh_calc_poly_normal(mpoly, loopstart, mvarray, polynorm_local);
		}

		/* finally calculate the area */
		area = area_poly_v3(mpoly->totloop, vertexcos, no);

		return area;
	}
}

/* note, results won't be correct if polygon is non-planar */
static float mesh_calc_poly_planar_area_centroid(MPoly *mpoly, MLoop *loopstart, MVert *mvarray, float cent[3])
{
	int i;
	float tri_area;
	float total_area = 0.0f;
	float v1[3], v2[3], v3[3], normal[3], tri_cent[3];

	BKE_mesh_calc_poly_normal(mpoly, loopstart, mvarray, normal);
	copy_v3_v3(v1, mvarray[loopstart[0].v].co);
	copy_v3_v3(v2, mvarray[loopstart[1].v].co);
	zero_v3(cent);

	for (i = 2; i < mpoly->totloop; i++) {
		copy_v3_v3(v3, mvarray[loopstart[i].v].co);

		tri_area = area_tri_signed_v3(v1, v2, v3, normal);
		total_area += tri_area;

		cent_tri_v3(tri_cent, v1, v2, v3);
		madd_v3_v3fl(cent, tri_cent, tri_area);

		copy_v3_v3(v2, v3);
	}

	mul_v3_fl(cent, 1.0f / total_area);

	return total_area;
}

/**
 * This function takes the difference between 2 vertex-coord-arrays
 * (\a vert_cos_src, \a vert_cos_dst),
 * and applies the difference to \a vert_cos_new relative to \a vert_cos_org.
 *
 * \param vert_cos_src reference deform source.
 * \param vert_cos_dst reference deform destination.
 *
 * \param vert_cos_org reference for the output location.
 * \param vert_cos_new resulting coords.
 */
void BKE_mesh_calc_relative_deform(
        const MPoly *mpoly, const int totpoly,
        const MLoop *mloop, const int totvert,

        const float (*vert_cos_src)[3],
        const float (*vert_cos_dst)[3],

        const float (*vert_cos_org)[3],
              float (*vert_cos_new)[3])
{
	const MPoly *mp;
	int i;

	int *vert_accum = MEM_callocN(sizeof(*vert_accum) * totvert, __func__);

	memset(vert_cos_new, '\0', sizeof(*vert_cos_new) * totvert);

	for (i = 0, mp = mpoly; i < totpoly; i++, mp++) {
		const MLoop *loopstart = mloop + mp->loopstart;
		int j;

		for (j = 0; j < mp->totloop; j++) {
			int v_prev = (loopstart + ((mp->totloop + (j - 1)) % mp->totloop))->v;
			int v_curr = (loopstart + j)->v;
			int v_next = (loopstart + ((j + 1) % mp->totloop))->v;

			float tvec[3];

			barycentric_transform(
			            tvec, vert_cos_dst[v_curr],
			            vert_cos_org[v_prev], vert_cos_org[v_curr], vert_cos_org[v_next],
			            vert_cos_src[v_prev], vert_cos_src[v_curr], vert_cos_src[v_next]
			            );

			add_v3_v3(vert_cos_new[v_curr], tvec);
			vert_accum[v_curr] += 1;
		}
	}

	for (i = 0; i < totvert; i++) {
		if (vert_accum[i]) {
			mul_v3_fl(vert_cos_new[i], 1.0f / (float)vert_accum[i]);
		}
		else {
			copy_v3_v3(vert_cos_new[i], vert_cos_org[i]);
		}
	}

	MEM_freeN(vert_accum);
}

/* Find the index of the loop in 'poly' which references vertex,
 * returns -1 if not found */
int poly_find_loop_from_vert(const MPoly *poly, const MLoop *loopstart,
                             unsigned vert)
{
	int j;
	for (j = 0; j < poly->totloop; j++, loopstart++) {
		if (loopstart->v == vert)
			return j;
	}
	
	return -1;
}

/* Fill 'adj_r' with the loop indices in 'poly' adjacent to the
 * vertex. Returns the index of the loop matching vertex, or -1 if the
 * vertex is not in 'poly' */
int poly_get_adj_loops_from_vert(unsigned adj_r[3], const MPoly *poly,
                                 const MLoop *mloop, unsigned vert)
{
	int corner = poly_find_loop_from_vert(poly,
	                                      &mloop[poly->loopstart],
	                                      vert);
		
	if (corner != -1) {
		const MLoop *ml = &mloop[poly->loopstart + corner];

		/* vertex was found */
		adj_r[0] = ME_POLY_LOOP_PREV(mloop, poly, corner)->v;
		adj_r[1] = ml->v;
		adj_r[2] = ME_POLY_LOOP_NEXT(mloop, poly, corner)->v;
	}

	return corner;
}

/* Return the index of the edge vert that is not equal to 'v'. If
 * neither edge vertex is equal to 'v', returns -1. */
int BKE_mesh_edge_other_vert(const MEdge *e, int v)
{
	if (e->v1 == v)
		return e->v2;
	else if (e->v2 == v)
		return e->v1;
	else
		return -1;
}

/* update the hide flag for edges and faces from the corresponding
 * flag in verts */
void BKE_mesh_flush_hidden_from_verts(const MVert *mvert,
                                      const MLoop *mloop,
                                      MEdge *medge, int totedge,
                                      MPoly *mpoly, int totpoly)
{
	int i, j;
	
	for (i = 0; i < totedge; i++) {
		MEdge *e = &medge[i];
		if (mvert[e->v1].flag & ME_HIDE ||
		    mvert[e->v2].flag & ME_HIDE)
		{
			e->flag |= ME_HIDE;
		}
		else {
			e->flag &= ~ME_HIDE;
		}
	}
	for (i = 0; i < totpoly; i++) {
		MPoly *p = &mpoly[i];
		p->flag &= ~ME_HIDE;
		for (j = 0; j < p->totloop; j++) {
			if (mvert[mloop[p->loopstart + j].v].flag & ME_HIDE)
				p->flag |= ME_HIDE;
		}
	}
}

/**
 * simple poly -> vert/edge selection.
 */
void BKE_mesh_flush_select_from_polys_ex(MVert *mvert,       const int totvert,
                                         MLoop *mloop,
                                         MEdge *medge,       const int totedge,
                                         const MPoly *mpoly, const int totpoly)
{
	MVert *mv;
	MEdge *med;
	const MPoly *mp;
	int i;

	i = totvert;
	for (mv = mvert; i--; mv++) {
		mv->flag &= ~SELECT;
	}

	i = totedge;
	for (med = medge; i--; med++) {
		med->flag &= ~SELECT;
	}

	i = totpoly;
	for (mp = mpoly; i--; mp++) {
		/* assume if its selected its not hidden and none of its verts/edges are hidden
		 * (a common assumption)*/
		if (mp->flag & ME_FACE_SEL) {
			MLoop *ml;
			int j;
			j = mp->totloop;
			for (ml = &mloop[mp->loopstart]; j--; ml++) {
				mvert[ml->v].flag |= SELECT;
				medge[ml->e].flag |= SELECT;
			}
		}
	}
}
void BKE_mesh_flush_select_from_polys(Mesh *me)
{
	BKE_mesh_flush_select_from_polys_ex(me->mvert, me->totvert,
	                                 me->mloop,
	                                 me->medge, me->totedge,
	                                 me->mpoly, me->totpoly);
}

void BKE_mesh_flush_select_from_verts_ex(const MVert *mvert, const int UNUSED(totvert),
                                         MLoop *mloop,
                                         MEdge *medge,       const int totedge,
                                         MPoly *mpoly,       const int totpoly)
{
	MEdge *med;
	MPoly *mp;
	int i;

	/* edges */
	i = totedge;
	for (med = medge; i--; med++) {
		if ((med->flag & ME_HIDE) == 0) {
			if ((mvert[med->v1].flag & SELECT) && (mvert[med->v2].flag & SELECT)) {
				med->flag |= SELECT;
			}
			else {
				med->flag &= ~SELECT;
			}
		}
	}

	/* polys */
	i = totpoly;
	for (mp = mpoly; i--; mp++) {
		if ((mp->flag & ME_HIDE) == 0) {
			int ok = TRUE;
			MLoop *ml;
			int j;
			j = mp->totloop;
			for (ml = &mloop[mp->loopstart]; j--; ml++) {
				if ((mvert[ml->v].flag & SELECT) == 0) {
					ok = FALSE;
					break;
				}
			}

			if (ok) {
				mp->flag |= ME_FACE_SEL;
			}
			else {
				mp->flag &= ~ME_FACE_SEL;
			}
		}
	}
}
void BKE_mesh_flush_select_from_verts(Mesh *me)
{
	BKE_mesh_flush_select_from_verts_ex(me->mvert, me->totvert,
	                                    me->mloop,
	                                    me->medge, me->totedge,
	                                    me->mpoly, me->totpoly);
}


/* basic vertex data functions */
int BKE_mesh_minmax(Mesh *me, float r_min[3], float r_max[3])
{
	int i = me->totvert;
	MVert *mvert;
	for (mvert = me->mvert; i--; mvert++) {
		minmax_v3v3_v3(r_min, r_max, mvert->co);
	}
	
	return (me->totvert != 0);
}

int BKE_mesh_center_median(Mesh *me, float cent[3])
{
	int i = me->totvert;
	MVert *mvert;
	zero_v3(cent);
	for (mvert = me->mvert; i--; mvert++) {
		add_v3_v3(cent, mvert->co);
	}
	/* otherwise we get NAN for 0 verts */
	if (me->totvert) {
		mul_v3_fl(cent, 1.0f / (float)me->totvert);
	}

	return (me->totvert != 0);
}

int BKE_mesh_center_bounds(Mesh *me, float cent[3])
{
	float min[3], max[3];
	INIT_MINMAX(min, max);
	if (BKE_mesh_minmax(me, min, max)) {
		mid_v3_v3v3(cent, min, max);
		return 1;
	}

	return 0;
}

int BKE_mesh_center_centroid(Mesh *me, float cent[3])
{
	int i = me->totpoly;
	MPoly *mpoly;
	float poly_area;
	float total_area = 0.0f;
	float poly_cent[3];
	
	zero_v3(cent);
	
	/* calculate a weighted average of polygon centroids */
	for (mpoly = me->mpoly; i--; mpoly++) {
		poly_area = mesh_calc_poly_planar_area_centroid(mpoly, me->mloop + mpoly->loopstart, me->mvert, poly_cent);

		madd_v3_v3fl(cent, poly_cent, poly_area);
		total_area += poly_area;
	}
	/* otherwise we get NAN for 0 polys */
	if (me->totpoly) {
		mul_v3_fl(cent, 1.0f / total_area);
	}

	return (me->totpoly != 0);
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
		recastData = (int *)MEM_mallocN(numFaces * sizeof(int), __func__);
		for (i = 0; i < numFaces; i++) {
			recastData[i] = i + 1;
		}
		CustomData_add_layer_named(&me->pdata, CD_RECAST, CD_ASSIGN, recastData, numFaces, "recastData");
	}
}

void BKE_mesh_tessface_calc(Mesh *mesh)
{
	mesh->totface = BKE_mesh_recalc_tessellation(&mesh->fdata, &mesh->ldata, &mesh->pdata,
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
	mesh_tessface_clear_intern(mesh, TRUE);
}

#if 0 /* slow version of the function below */
void BKE_mesh_calc_poly_angles(MPoly *mpoly, MLoop *loopstart,
                               MVert *mvarray, float angles[])
{
	MLoop *ml;
	MLoop *mloop = &loopstart[-mpoly->loopstart];

	int j;
	for (j = 0, ml = loopstart; j < mpoly->totloop; j++, ml++) {
		MLoop *ml_prev = ME_POLY_LOOP_PREV(mloop, mpoly, j);
		MLoop *ml_next = ME_POLY_LOOP_NEXT(mloop, mpoly, j);

		float e1[3], e2[3];

		sub_v3_v3v3(e1, mvarray[ml_next->v].co, mvarray[ml->v].co);
		sub_v3_v3v3(e2, mvarray[ml_prev->v].co, mvarray[ml->v].co);

		angles[j] = (float)M_PI - angle_v3v3(e1, e2);
	}
}

#else /* equivalent the function above but avoid multiple subtractions + normalize */

void BKE_mesh_calc_poly_angles(MPoly *mpoly, MLoop *loopstart,
                               MVert *mvarray, float angles[])
{
	float nor_prev[3];
	float nor_next[3];

	int i_this = mpoly->totloop - 1;
	int i_next = 0;

	sub_v3_v3v3(nor_prev, mvarray[loopstart[i_this - 1].v].co, mvarray[loopstart[i_this].v].co);
	normalize_v3(nor_prev);

	while (i_next < mpoly->totloop) {
		sub_v3_v3v3(nor_next, mvarray[loopstart[i_this].v].co, mvarray[loopstart[i_next].v].co);
		normalize_v3(nor_next);
		angles[i_this] = angle_normalized_v3v3(nor_prev, nor_next);

		/* step */
		copy_v3_v3(nor_prev, nor_next);
		i_this = i_next;
		i_next++;
	}
}
#endif

void BKE_mesh_poly_edgehash_insert(EdgeHash *ehash, const MPoly *mp, const MLoop *mloop)
{
	const MLoop *ml, *ml_next;
	int i = mp->totloop;

	ml_next = mloop;       /* first loop */
	ml = &ml_next[i - 1];  /* last loop */

	while (i-- != 0) {
		if (!BLI_edgehash_haskey(ehash, ml->v, ml_next->v)) {
			BLI_edgehash_insert(ehash, ml->v, ml_next->v, NULL);
		}

		ml = ml_next;
		ml_next++;
	}
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

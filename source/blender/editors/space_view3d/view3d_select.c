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
 * The Original Code is Copyright (C) 2008 Blender Foundation.
 * All rights reserved.
 *
 * 
 * Contributor(s): Blender Foundation
 *
 * ***** END GPL LICENSE BLOCK *****
 */

/** \file blender/editors/space_view3d/view3d_select.c
 *  \ingroup spview3d
 */


#include <string.h>
#include <stdio.h>
#include <math.h>
#include <float.h>
#include <assert.h>

#include "DNA_action_types.h"
#include "DNA_armature_types.h"
#include "DNA_curve_types.h"
#include "DNA_meta_types.h"
#include "DNA_mesh_types.h"
#include "DNA_meshdata_types.h"
#include "DNA_object_types.h"
#include "DNA_scene_types.h"
#include "DNA_tracking_types.h"

#include "MEM_guardedalloc.h"

#include "BLI_math.h"
#include "BLI_lasso.h"
#include "BLI_rect.h"
#include "BLI_rand.h"
#include "BLI_linklist.h"
#include "BLI_listbase.h"
#include "BLI_string.h"
#include "BLI_utildefines.h"

/* vertex box select */
#include "IMB_imbuf_types.h"
#include "IMB_imbuf.h"
#include "BKE_global.h"

#include "BKE_armature.h"
#include "BKE_context.h"
#include "BKE_depsgraph.h"
#include "BKE_mball.h"
#include "BKE_movieclip.h"
#include "BKE_object.h"
#include "BKE_paint.h"
#include "BKE_tessmesh.h"
#include "BKE_tracking.h"


#include "BIF_gl.h"
#include "BIF_glutil.h"

#include "WM_api.h"
#include "WM_types.h"

#include "RNA_access.h"
#include "RNA_define.h"
#include "RNA_enum_types.h"

#include "ED_armature.h"
#include "ED_curve.h"
#include "ED_particle.h"
#include "ED_mesh.h"
#include "ED_object.h"
#include "ED_screen.h"
#include "ED_mball.h"

#include "UI_interface.h"
#include "UI_resources.h"

#include "view3d_intern.h"  /* own include */

/* TODO: should return whether there is valid context to continue */
void view3d_set_viewcontext(bContext *C, ViewContext *vc)
{
	memset(vc, 0, sizeof(ViewContext));
	vc->ar = CTX_wm_region(C);
	vc->scene = CTX_data_scene(C);
	vc->v3d = CTX_wm_view3d(C);
	vc->rv3d = CTX_wm_region_view3d(C);
	vc->obact = CTX_data_active_object(C);
	vc->obedit = CTX_data_edit_object(C);
}

int view3d_get_view_aligned_coordinate(ViewContext *vc, float fp[3], const int mval[2], const short do_fallback)
{
	float dvec[3];
	int mval_cpy[2];
	eV3DProjStatus ret;

	mval_cpy[0] = mval[0];
	mval_cpy[1] = mval[1];

	ret = ED_view3d_project_int_global(vc->ar, fp, mval_cpy, V3D_PROJ_TEST_NOP);

	initgrabz(vc->rv3d, fp[0], fp[1], fp[2]);

	if (ret == V3D_PROJ_RET_OK) {
		const float mval_f[2] = {(float)(mval_cpy[0] - mval[0]),
		                         (float)(mval_cpy[1] - mval[1])};
		ED_view3d_win_to_delta(vc->ar, mval_f, dvec);
		sub_v3_v3(fp, dvec);

		return TRUE;
	}
	else {
		/* fallback to the view center */
		if (do_fallback) {
			negate_v3_v3(fp, vc->rv3d->ofs);
			return view3d_get_view_aligned_coordinate(vc, fp, mval, FALSE);
		}
		else {
			return FALSE;
		}
	}
}

/*
 * ob == NULL if you want global matrices
 * */
void view3d_get_transformation(const ARegion *ar, RegionView3D *rv3d, Object *ob, bglMats *mats)
{
	float cpy[4][4];
	int i, j;

	if (ob) {
		mult_m4_m4m4(cpy, rv3d->viewmat, ob->obmat);
	}
	else {
		copy_m4_m4(cpy, rv3d->viewmat);
	}

	for (i = 0; i < 4; ++i) {
		for (j = 0; j < 4; ++j) {
			mats->projection[i * 4 + j] = rv3d->winmat[i][j];
			mats->modelview[i * 4 + j] = cpy[i][j];
		}
	}

	mats->viewport[0] = ar->winrct.xmin;
	mats->viewport[1] = ar->winrct.ymin;
	mats->viewport[2] = ar->winx;
	mats->viewport[3] = ar->winy;	
}

/* ********************** view3d_select: selection manipulations ********************* */

/* local prototypes */

static void edbm_backbuf_check_and_select_verts(BMEditMesh *em, int select)
{
	BMVert *eve;
	BMIter iter;
	int index = bm_wireoffs;

	eve = BM_iter_new(&iter, em->bm, BM_VERTS_OF_MESH, NULL);
	for (; eve; eve = BM_iter_step(&iter), index++) {
		if (!BM_elem_flag_test(eve, BM_ELEM_HIDDEN)) {
			if (EDBM_backbuf_check(index)) {
				BM_vert_select_set(em->bm, eve, select);
			}
		}
	}
}

static void edbm_backbuf_check_and_select_edges(BMEditMesh *em, int select)
{
	BMEdge *eed;
	BMIter iter;
	int index = bm_solidoffs;

	eed = BM_iter_new(&iter, em->bm, BM_EDGES_OF_MESH, NULL);
	for (; eed; eed = BM_iter_step(&iter), index++) {
		if (!BM_elem_flag_test(eed, BM_ELEM_HIDDEN)) {
			if (EDBM_backbuf_check(index)) {
				BM_edge_select_set(em->bm, eed, select);
			}
		}
	}
}

static void edbm_backbuf_check_and_select_faces(BMEditMesh *em, int select)
{
	BMFace *efa;
	BMIter iter;
	int index = 1;

	efa = BM_iter_new(&iter, em->bm, BM_FACES_OF_MESH, NULL);
	for (; efa; efa = BM_iter_step(&iter), index++) {
		if (!BM_elem_flag_test(efa, BM_ELEM_HIDDEN)) {
			if (EDBM_backbuf_check(index)) {
				BM_face_select_set(em->bm, efa, select);
			}
		}
	}
}


/* object mode, EM_ prefix is confusing here, rename? */
static void edbm_backbuf_check_and_select_verts_obmode(Mesh *me, int select)
{
	MVert *mv = me->mvert;
	int a;

	if (mv) {
		for (a = 1; a <= me->totvert; a++, mv++) {
			if (EDBM_backbuf_check(a)) {
				if (!(mv->flag & ME_HIDE)) {
					mv->flag = select ? (mv->flag | SELECT) : (mv->flag & ~SELECT);
				}
			}
		}
	}
}
/* object mode, EM_ prefix is confusing here, rename? */

static void edbm_backbuf_check_and_select_tfaces(Mesh *me, int select)
{
	MPoly *mpoly = me->mpoly;
	int a;

	if (mpoly) {
		for (a = 1; a <= me->totpoly; a++, mpoly++) {
			if (EDBM_backbuf_check(a)) {
				mpoly->flag = select ? (mpoly->flag | ME_FACE_SEL) : (mpoly->flag & ~ME_FACE_SEL);
			}
		}
	}
}

/* *********************** GESTURE AND LASSO ******************* */

typedef struct LassoSelectUserData {
	ViewContext *vc;
	const rcti *rect;
	const int (*mcords)[2];
	int moves;
	int select;

	/* runtime */
	int pass;
	int is_done;
	int is_change;
} LassoSelectUserData;

static void view3d_userdata_lassoselect_init(LassoSelectUserData *r_data,
                                             ViewContext *vc, const rcti *rect, const int (*mcords)[2],
                                             const int moves, const int select)
{
	r_data->vc = vc;
	r_data->rect = rect;
	r_data->mcords = mcords;
	r_data->moves = moves;
	r_data->select = select;

	/* runtime */
	r_data->pass = 0;
	r_data->is_done = FALSE;
	r_data->is_change = FALSE;
}

static int view3d_selectable_data(bContext *C)
{
	Object *ob = CTX_data_active_object(C);

	if (!ED_operator_region_view3d_active(C))
		return 0;

	if (ob) {
		if (ob->mode & OB_MODE_EDIT) {
			if (ob->type == OB_FONT) {
				return 0;
			}
		}
		else {
			if (ob->mode & OB_MODE_SCULPT) {
				return 0;
			}
			if ((ob->mode & (OB_MODE_VERTEX_PAINT | OB_MODE_WEIGHT_PAINT | OB_MODE_TEXTURE_PAINT)) &&
			    !paint_facesel_test(ob) && !paint_vertsel_test(ob))
			{
				return 0;
			}
		}
	}

	return 1;
}


/* helper also for borderselect */
static int edge_fully_inside_rect(const rcti *rect, int x1, int y1, int x2, int y2)
{
	return BLI_rcti_isect_pt(rect, x1, y1) && BLI_rcti_isect_pt(rect, x2, y2);
}

static int edge_inside_rect(const rcti *rect, int x1, int y1, int x2, int y2)
{
	int d1, d2, d3, d4;
	
	/* check points in rect */
	if (edge_fully_inside_rect(rect, x1, y1, x2, y2)) return 1;
	
	/* check points completely out rect */
	if (x1 < rect->xmin && x2 < rect->xmin) return 0;
	if (x1 > rect->xmax && x2 > rect->xmax) return 0;
	if (y1 < rect->ymin && y2 < rect->ymin) return 0;
	if (y1 > rect->ymax && y2 > rect->ymax) return 0;
	
	/* simple check lines intersecting. */
	d1 = (y1 - y2) * (x1 - rect->xmin) + (x2 - x1) * (y1 - rect->ymin);
	d2 = (y1 - y2) * (x1 - rect->xmin) + (x2 - x1) * (y1 - rect->ymax);
	d3 = (y1 - y2) * (x1 - rect->xmax) + (x2 - x1) * (y1 - rect->ymax);
	d4 = (y1 - y2) * (x1 - rect->xmax) + (x2 - x1) * (y1 - rect->ymin);
	
	if (d1 < 0 && d2 < 0 && d3 < 0 && d4 < 0) return 0;
	if (d1 > 0 && d2 > 0 && d3 > 0 && d4 > 0) return 0;
	
	return 1;
}

static void do_lasso_select_pose__doSelectBone(void *userData, struct bPoseChannel *pchan, int x0, int y0, int x1, int y1)
{
	LassoSelectUserData *data = userData;
	bArmature *arm = data->vc->obact->data;

	if (PBONE_SELECTABLE(arm, pchan->bone)) {
		int is_point_done = FALSE;
		int points_proj_tot = 0;

		/* project head location to screenspace */
		if (x0 != IS_CLIPPED) {
			points_proj_tot++;
			if (BLI_rcti_isect_pt(data->rect, x0, y0) &&
			    BLI_lasso_is_point_inside(data->mcords, data->moves, x0, y0, INT_MAX))
			{
				is_point_done = TRUE;
			}
		}

		/* project tail location to screenspace */
		if (x1 != IS_CLIPPED) {
			points_proj_tot++;
			if (BLI_rcti_isect_pt(data->rect, x1, y1) &&
			    BLI_lasso_is_point_inside(data->mcords, data->moves, x1, y1, INT_MAX))
			{
				is_point_done = TRUE;
			}
		}

		/* if one of points selected, we skip the bone itself */
		if ((is_point_done == TRUE) ||
		    ((is_point_done == FALSE) && (points_proj_tot == 2) &&
		     BLI_lasso_is_edge_inside(data->mcords, data->moves, x0, y0, x1, y1, INT_MAX)))
		{
			if (data->select) pchan->bone->flag |=  BONE_SELECTED;
			else              pchan->bone->flag &= ~BONE_SELECTED;
			data->is_change = TRUE;
		}
		data->is_change |= is_point_done;
	}
}
static void do_lasso_select_pose(ViewContext *vc, Object *ob, const int mcords[][2], short moves, short select)
{
	LassoSelectUserData data;
	rcti rect;
	
	if ((ob->type != OB_ARMATURE) || (ob->pose == NULL)) {
		return;
	}

	view3d_userdata_lassoselect_init(&data, vc, &rect, mcords, moves, select);

	ED_view3d_init_mats_rv3d(vc->obact, vc->rv3d);

	BLI_lasso_boundbox(&rect, mcords, moves);

	pose_foreachScreenBone(vc, do_lasso_select_pose__doSelectBone, &data);

	if (data.is_change) {
		bArmature *arm = ob->data;
		if (arm->flag & ARM_HAS_VIZ_DEPS) {
			/* mask modifier ('armature' mode), etc. */
			DAG_id_tag_update(&ob->id, OB_RECALC_DATA);
		}
	}
}

static void object_deselect_all_visible(Scene *scene, View3D *v3d)
{
	Base *base;

	for (base = scene->base.first; base; base = base->next) {
		if (BASE_SELECTABLE(v3d, base)) {
			ED_base_object_select(base, BA_DESELECT);
		}
	}
}

static void do_lasso_select_objects(ViewContext *vc, const int mcords[][2], const short moves, short extend, short select)
{
	Base *base;
	
	if (extend == 0 && select)
		object_deselect_all_visible(vc->scene, vc->v3d);

	for (base = vc->scene->base.first; base; base = base->next) {
		if (BASE_SELECTABLE(vc->v3d, base)) { /* use this to avoid un-needed lasso lookups */
			ED_view3d_project_base(vc->ar, base);
			if (BLI_lasso_is_point_inside(mcords, moves, base->sx, base->sy, IS_CLIPPED)) {
				
				if (select) ED_base_object_select(base, BA_SELECT);
				else ED_base_object_select(base, BA_DESELECT);
				base->object->flag = base->flag;
			}
			if (base->object->mode & OB_MODE_POSE) {
				do_lasso_select_pose(vc, base->object, mcords, moves, select);
			}
		}
	}
}

static void do_lasso_select_mesh__doSelectVert(void *userData, BMVert *eve, int x, int y, int UNUSED(index))
{
	LassoSelectUserData *data = userData;

	if (BLI_rcti_isect_pt(data->rect, x, y) &&
	    BLI_lasso_is_point_inside(data->mcords, data->moves, x, y, IS_CLIPPED))
	{
		BM_vert_select_set(data->vc->em->bm, eve, data->select);
	}
}
static void do_lasso_select_mesh__doSelectEdge(void *userData, BMEdge *eed, int x0, int y0, int x1, int y1, int index)
{
	LassoSelectUserData *data = userData;

	if (EDBM_backbuf_check(bm_solidoffs + index)) {
		if (data->pass == 0) {
			if (edge_fully_inside_rect(data->rect, x0, y0, x1, y1)  &&
			    BLI_lasso_is_point_inside(data->mcords, data->moves, x0, y0, IS_CLIPPED) &&
			    BLI_lasso_is_point_inside(data->mcords, data->moves, x1, y1, IS_CLIPPED))
			{
				BM_edge_select_set(data->vc->em->bm, eed, data->select);
				data->is_done = TRUE;
			}
		}
		else {
			if (BLI_lasso_is_edge_inside(data->mcords, data->moves, x0, y0, x1, y1, IS_CLIPPED)) {
				BM_edge_select_set(data->vc->em->bm, eed, data->select);
			}
		}
	}
}
static void do_lasso_select_mesh__doSelectFace(void *userData, BMFace *efa, int x, int y, int UNUSED(index))
{
	LassoSelectUserData *data = userData;

	if (BLI_rcti_isect_pt(data->rect, x, y) &&
	    BLI_lasso_is_point_inside(data->mcords, data->moves, x, y, IS_CLIPPED))
	{
		BM_face_select_set(data->vc->em->bm, efa, data->select);
	}
}

static void do_lasso_select_mesh(ViewContext *vc, const int mcords[][2], short moves, short extend, short select)
{
	LassoSelectUserData data;
	ToolSettings *ts = vc->scene->toolsettings;
	rcti rect;
	int bbsel;
	
	BLI_lasso_boundbox(&rect, mcords, moves);
	
	/* set editmesh */
	vc->em = BMEdit_FromObject(vc->obedit);

	view3d_userdata_lassoselect_init(&data, vc, &rect, mcords, moves, select);

	if (extend == 0 && select)
		EDBM_flag_disable_all(vc->em, BM_ELEM_SELECT);

	/* for non zbuf projections, don't change the GL state */
	ED_view3d_init_mats_rv3d(vc->obedit, vc->rv3d);

	glLoadMatrixf(vc->rv3d->viewmat);
	bbsel = EDBM_backbuf_border_mask_init(vc, mcords, moves, rect.xmin, rect.ymin, rect.xmax, rect.ymax);
	
	if (ts->selectmode & SCE_SELECT_VERTEX) {
		if (bbsel) {
			edbm_backbuf_check_and_select_verts(vc->em, select);
		}
		else {
			mesh_foreachScreenVert(vc, do_lasso_select_mesh__doSelectVert, &data, V3D_CLIP_TEST_RV3D_CLIPPING);
		}
	}
	if (ts->selectmode & SCE_SELECT_EDGE) {
		/* Does both bbsel and non-bbsel versions (need screen cos for both) */
		data.pass = 0;
		mesh_foreachScreenEdge(vc, do_lasso_select_mesh__doSelectEdge, &data, V3D_CLIP_TEST_OFF);

		if (data.is_done == 0) {
			data.pass = 1;
			mesh_foreachScreenEdge(vc, do_lasso_select_mesh__doSelectEdge, &data, V3D_CLIP_TEST_OFF);
		}
	}
	
	if (ts->selectmode & SCE_SELECT_FACE) {
		if (bbsel) {
			edbm_backbuf_check_and_select_faces(vc->em, select);
		}
		else {
			mesh_foreachScreenFace(vc, do_lasso_select_mesh__doSelectFace, &data);
		}
	}
	
	EDBM_backbuf_free();
	EDBM_selectmode_flush(vc->em);
}

static void do_lasso_select_curve__doSelect(void *userData, Nurb *UNUSED(nu), BPoint *bp, BezTriple *bezt, int beztindex, int x, int y)
{
	LassoSelectUserData *data = userData;
	Object *obedit = data->vc->obedit;
	Curve *cu = (Curve *)obedit->data;

	if (BLI_lasso_is_point_inside(data->mcords, data->moves, x, y, IS_CLIPPED)) {
		if (bp) {
			bp->f1 = data->select ? (bp->f1 | SELECT) : (bp->f1 & ~SELECT);
			if (bp == cu->lastsel && !(bp->f1 & SELECT)) cu->lastsel = NULL;
		}
		else {
			if (cu->drawflag & CU_HIDE_HANDLES) {
				/* can only be (beztindex == 0) here since handles are hidden */
				bezt->f1 = bezt->f2 = bezt->f3 = data->select ? (bezt->f2 | SELECT) : (bezt->f2 & ~SELECT);
			}
			else {
				if (beztindex == 0) {
					bezt->f1 = data->select ? (bezt->f1 | SELECT) : (bezt->f1 & ~SELECT);
				}
				else if (beztindex == 1) {
					bezt->f2 = data->select ? (bezt->f2 | SELECT) : (bezt->f2 & ~SELECT);
				}
				else {
					bezt->f3 = data->select ? (bezt->f3 | SELECT) : (bezt->f3 & ~SELECT);
				}
			}

			if (bezt == cu->lastsel && !(bezt->f2 & SELECT)) cu->lastsel = NULL;
		}
	}
}

static void do_lasso_select_curve(ViewContext *vc, const int mcords[][2], short moves, short extend, short select)
{
	LassoSelectUserData data;

	view3d_userdata_lassoselect_init(&data, vc, NULL, mcords, moves, select);

	if (extend == 0 && select)
		CU_deselect_all(vc->obedit);

	ED_view3d_init_mats_rv3d(vc->obedit, vc->rv3d); /* for foreach's screen/vert projection */
	nurbs_foreachScreenVert(vc, do_lasso_select_curve__doSelect, &data);
}

static void do_lasso_select_lattice__doSelect(void *userData, BPoint *bp, int x, int y)
{
	LassoSelectUserData *data = userData;

	if (BLI_lasso_is_point_inside(data->mcords, data->moves, x, y, IS_CLIPPED)) {
		bp->f1 = data->select ? (bp->f1 | SELECT) : (bp->f1 & ~SELECT);
	}
}
static void do_lasso_select_lattice(ViewContext *vc, const int mcords[][2], short moves, short extend, short select)
{
	LassoSelectUserData data;

	view3d_userdata_lassoselect_init(&data, vc, NULL, mcords, moves, select);

	if (extend == 0 && select)
		ED_setflagsLatt(vc->obedit, 0);

	ED_view3d_init_mats_rv3d(vc->obedit, vc->rv3d); /* for foreach's screen/vert projection */
	lattice_foreachScreenVert(vc, do_lasso_select_lattice__doSelect, &data);
}

static void do_lasso_select_armature__doSelectBone(void *userData, struct EditBone *ebone, int x0, int y0, int x1, int y1)
{
	LassoSelectUserData *data = userData;
	bArmature *arm = data->vc->obedit->data;

	if (EBONE_SELECTABLE(arm, ebone)) {
		int is_point_done = FALSE;
		int points_proj_tot = 0;

		/* project head location to screenspace */
		if (x0 != IS_CLIPPED) {
			points_proj_tot++;
			if (BLI_rcti_isect_pt(data->rect, x0, y0) &&
			    BLI_lasso_is_point_inside(data->mcords, data->moves, x0, y0, INT_MAX))
			{
				is_point_done = TRUE;
				if (data->select) ebone->flag |=  BONE_ROOTSEL;
				else              ebone->flag &= ~BONE_ROOTSEL;
			}
		}

		/* project tail location to screenspace */
		if (x1 != IS_CLIPPED) {
			points_proj_tot++;
			if (BLI_rcti_isect_pt(data->rect, x1, y1) &&
			    BLI_lasso_is_point_inside(data->mcords, data->moves, x1, y1, INT_MAX))
			{
				is_point_done = TRUE;
				if (data->select) ebone->flag |=  BONE_TIPSEL;
				else              ebone->flag &= ~BONE_TIPSEL;
			}
		}

		/* if one of points selected, we skip the bone itself */
		if ((is_point_done == FALSE) && (points_proj_tot == 2) &&
		    BLI_lasso_is_edge_inside(data->mcords, data->moves, x0, y0, x1, y1, INT_MAX))
		{
			if (data->select) ebone->flag |=  (BONE_SELECTED | BONE_TIPSEL | BONE_ROOTSEL);
			else              ebone->flag &= ~(BONE_SELECTED | BONE_TIPSEL | BONE_ROOTSEL);
			data->is_change = TRUE;
		}

		data->is_change |= is_point_done;
	}
}

static void do_lasso_select_armature(ViewContext *vc, const int mcords[][2], short moves, short extend, short select)
{
	LassoSelectUserData data;
	rcti rect;

	view3d_userdata_lassoselect_init(&data, vc, &rect, mcords, moves, select);

	ED_view3d_init_mats_rv3d(vc->obedit, vc->rv3d);

	BLI_lasso_boundbox(&rect, mcords, moves);

	if (extend == 0 && select)
		ED_armature_deselect_all_visible(vc->obedit);

	armature_foreachScreenBone(vc, do_lasso_select_armature__doSelectBone, &data);

	if (data.is_change) {
		bArmature *arm = vc->obedit->data;
		ED_armature_sync_selection(arm->edbo);
		ED_armature_validate_active(arm);
		WM_main_add_notifier(NC_OBJECT | ND_BONE_SELECT, vc->obedit);
	}
}

static void do_lasso_select_mball__doSelectElem(void *userData, struct MetaElem *ml, int x, int y)
{
	LassoSelectUserData *data = userData;

	if (BLI_rcti_isect_pt(data->rect, x, y) &&
	    BLI_lasso_is_point_inside(data->mcords, data->moves, x, y, INT_MAX)) {
		if (data->select) ml->flag |=  SELECT;
		else              ml->flag &= ~SELECT;
		data->is_change = TRUE;
	}
}
static void do_lasso_select_meta(ViewContext *vc, const int mcords[][2], short moves, short extend, short select)
{
	LassoSelectUserData data;
	rcti rect;

	MetaBall *mb = (MetaBall *)vc->obedit->data;

	if (extend == 0 && select)
		 BKE_mball_deselect_all(mb);

	view3d_userdata_lassoselect_init(&data, vc, &rect, mcords, moves, select);

	ED_view3d_init_mats_rv3d(vc->obedit, vc->rv3d);

	BLI_lasso_boundbox(&rect, mcords, moves);

	mball_foreachScreenElem(vc, do_lasso_select_mball__doSelectElem, &data);
}

static int do_paintvert_box_select(ViewContext *vc, rcti *rect, int select, int extend)
{
	Mesh *me;
	MVert *mvert;
	struct ImBuf *ibuf;
	unsigned int *rt;
	int a, index;
	char *selar;
	int sx = BLI_rcti_size_x(rect) + 1;
	int sy = BLI_rcti_size_y(rect) + 1;

	me = vc->obact->data;

	if (me == NULL || me->totvert == 0 || sx * sy <= 0)
		return OPERATOR_CANCELLED;

	selar = MEM_callocN(me->totvert + 1, "selar");

	if (extend == 0 && select)
		paintvert_deselect_all_visible(vc->obact, SEL_DESELECT, FALSE);

	view3d_validate_backbuf(vc);

	ibuf = IMB_allocImBuf(sx, sy, 32, IB_rect);
	rt = ibuf->rect;
	glReadPixels(rect->xmin + vc->ar->winrct.xmin,  rect->ymin + vc->ar->winrct.ymin, sx, sy, GL_RGBA, GL_UNSIGNED_BYTE,  ibuf->rect);
	if (ENDIAN_ORDER == B_ENDIAN) IMB_convert_rgba_to_abgr(ibuf);

	a = sx * sy;
	while (a--) {
		if (*rt) {
			index = WM_framebuffer_to_index(*rt);
			if (index <= me->totvert) selar[index] = 1;
		}
		rt++;
	}

	mvert = me->mvert;
	for (a = 1; a <= me->totvert; a++, mvert++) {
		if (selar[a]) {
			if ((mvert->flag & ME_HIDE) == 0) {
				if (select) mvert->flag |=  SELECT;
				else        mvert->flag &= ~SELECT;
			}
		}
	}

	IMB_freeImBuf(ibuf);
	MEM_freeN(selar);

#ifdef __APPLE__	
	glReadBuffer(GL_BACK);
#endif

	paintvert_flush_flags(vc->obact);

	return OPERATOR_FINISHED;
}

static void do_lasso_select_paintvert(ViewContext *vc, const int mcords[][2], short moves, short extend, short select)
{
	Object *ob = vc->obact;
	Mesh *me = ob ? ob->data : NULL;
	rcti rect;

	if (me == NULL || me->totvert == 0)
		return;

	if (extend == 0 && select)
		paintvert_deselect_all_visible(ob, SEL_DESELECT, FALSE);  /* flush selection at the end */
	bm_vertoffs = me->totvert + 1; /* max index array */

	BLI_lasso_boundbox(&rect, mcords, moves);
	EDBM_backbuf_border_mask_init(vc, mcords, moves, rect.xmin, rect.ymin, rect.xmax, rect.ymax);

	edbm_backbuf_check_and_select_verts_obmode(me, select);

	EDBM_backbuf_free();

	paintvert_flush_flags(ob);
}
static void do_lasso_select_paintface(ViewContext *vc, const int mcords[][2], short moves, short extend, short select)
{
	Object *ob = vc->obact;
	Mesh *me = ob ? ob->data : NULL;
	rcti rect;

	if (me == NULL || me->totpoly == 0)
		return;

	if (extend == 0 && select)
		paintface_deselect_all_visible(ob, SEL_DESELECT, FALSE);  /* flush selection at the end */

	bm_vertoffs = me->totpoly + 1; /* max index array */

	BLI_lasso_boundbox(&rect, mcords, moves);
	EDBM_backbuf_border_mask_init(vc, mcords, moves, rect.xmin, rect.ymin, rect.xmax, rect.ymax);
	
	edbm_backbuf_check_and_select_tfaces(me, select);

	EDBM_backbuf_free();

	paintface_flush_flags(ob);
}

#if 0
static void do_lasso_select_node(int mcords[][2], short moves, short select)
{
	SpaceNode *snode = sa->spacedata.first;
	
	bNode *node;
	rcti rect;
	int node_cent[2];
	float node_centf[2];
	
	BLI_lasso_boundbox(&rect, mcords, moves);
	
	/* store selection in temp test flag */
	for (node = snode->edittree->nodes.first; node; node = node->next) {
		node_centf[0] = BLI_RCT_CENTER_X(&node->totr);
		node_centf[1] = BLI_RCT_CENTER_Y(&node->totr);
		
		ipoco_to_areaco_noclip(G.v2d, node_centf, node_cent);
		if (BLI_rcti_isect_pt_v(&rect, node_cent) && BLI_lasso_is_point_inside(mcords, moves, node_cent[0], node_cent[1])) {
			if (select) {
				node->flag |= SELECT;
			}
			else {
				node->flag &= ~SELECT;
			}
		}
	}
	BIF_undo_push("Lasso select nodes");
}
#endif

static void view3d_lasso_select(bContext *C, ViewContext *vc,
                                const int mcords[][2], short moves,
                                short extend, short select)
{
	Object *ob = CTX_data_active_object(C);

	if (vc->obedit == NULL) { /* Object Mode */
		if (paint_facesel_test(ob))
			do_lasso_select_paintface(vc, mcords, moves, extend, select);
		else if (paint_vertsel_test(ob))
			do_lasso_select_paintvert(vc, mcords, moves, extend, select);
		else if (ob && ob->mode & (OB_MODE_VERTEX_PAINT | OB_MODE_WEIGHT_PAINT | OB_MODE_TEXTURE_PAINT))
			;
		else if (ob && ob->mode & OB_MODE_PARTICLE_EDIT)
			PE_lasso_select(C, mcords, moves, extend, select);
		else {
			do_lasso_select_objects(vc, mcords, moves, extend, select);
			WM_event_add_notifier(C, NC_SCENE | ND_OB_SELECT, vc->scene);
		}
	}
	else { /* Edit Mode */
		switch (vc->obedit->type) {
			case OB_MESH:
				do_lasso_select_mesh(vc, mcords, moves, extend, select);
				break;
			case OB_CURVE:
			case OB_SURF:
				do_lasso_select_curve(vc, mcords, moves, extend, select);
				break;
			case OB_LATTICE:
				do_lasso_select_lattice(vc, mcords, moves, extend, select);
				break;
			case OB_ARMATURE:
				do_lasso_select_armature(vc, mcords, moves, extend, select);
				break;
			case OB_MBALL:
				do_lasso_select_meta(vc, mcords, moves, extend, select);
				break;
			default:
				assert(!"lasso select on incorrect object type");
		}

		WM_event_add_notifier(C, NC_GEOM | ND_SELECT, vc->obedit->data);
	}
}


/* lasso operator gives properties, but since old code works
 * with short array we convert */
static int view3d_lasso_select_exec(bContext *C, wmOperator *op)
{
	ViewContext vc;
	int mcords_tot;
	const int (*mcords)[2] = WM_gesture_lasso_path_to_array(C, op, &mcords_tot);
	
	if (mcords) {
		short extend, select;
		view3d_operator_needs_opengl(C);
		
		/* setup view context for argument to callbacks */
		view3d_set_viewcontext(C, &vc);
		
		extend = RNA_boolean_get(op->ptr, "extend");
		select = !RNA_boolean_get(op->ptr, "deselect");
		view3d_lasso_select(C, &vc, mcords, mcords_tot, extend, select);
		
		MEM_freeN(mcords);

		return OPERATOR_FINISHED;
	}
	return OPERATOR_PASS_THROUGH;
}

void VIEW3D_OT_select_lasso(wmOperatorType *ot)
{
	ot->name = "Lasso Select";
	ot->description = "Select items using lasso selection";
	ot->idname = "VIEW3D_OT_select_lasso";
	
	ot->invoke = WM_gesture_lasso_invoke;
	ot->modal = WM_gesture_lasso_modal;
	ot->exec = view3d_lasso_select_exec;
	ot->poll = view3d_selectable_data;
	ot->cancel = WM_gesture_lasso_cancel;
	
	/* flags */
	ot->flag = OPTYPE_UNDO;
	
	RNA_def_collection_runtime(ot->srna, "path", &RNA_OperatorMousePath, "Path", "");
	RNA_def_boolean(ot->srna, "deselect", 0, "Deselect", "Deselect rather than select items");
	RNA_def_boolean(ot->srna, "extend", 1, "Extend", "Extend selection instead of deselecting everything first");
}


/* ************************************************* */

#if 0
/* smart function to sample a rect spiralling outside, nice for backbuf selection */
static unsigned int samplerect(unsigned int *buf, int size, unsigned int dontdo)
{
	Base *base;
	unsigned int *bufmin, *bufmax;
	int a, b, rc, tel, len, dirvec[4][2], maxob;
	unsigned int retval = 0;
	
	base = LASTBASE;
	if (base == 0) return 0;
	maxob = base->selcol;

	len = (size - 1) / 2;
	rc = 0;

	dirvec[0][0] = 1;
	dirvec[0][1] = 0;
	dirvec[1][0] = 0;
	dirvec[1][1] = -size;
	dirvec[2][0] = -1;
	dirvec[2][1] = 0;
	dirvec[3][0] = 0;
	dirvec[3][1] = size;

	bufmin = buf;
	bufmax = buf + size * size;
	buf += len * size + len;

	for (tel = 1; tel <= size; tel++) {

		for (a = 0; a < 2; a++) {
			for (b = 0; b < tel; b++) {

				if (*buf && *buf <= maxob && *buf != dontdo) return *buf;
				if (*buf == dontdo) retval = dontdo;  /* if only color dontdo is available, still return dontdo */
				
				buf += (dirvec[rc][0] + dirvec[rc][1]);

				if (buf < bufmin || buf >= bufmax) return retval;
			}
			rc++;
			rc &= 3;
		}
	}
	return retval;
}
#endif

/* ************************** mouse select ************************* */


/* The max number of menu items in an object select menu */
typedef struct SelMenuItemF {
	char idname[MAX_ID_NAME - 2];
	int icon;
} SelMenuItemF;

#define SEL_MENU_SIZE   22
static SelMenuItemF object_mouse_select_menu_data[SEL_MENU_SIZE];

/* special (crappy) operator only for menu select */
static EnumPropertyItem *object_select_menu_enum_itemf(bContext *C, PointerRNA *UNUSED(ptr), PropertyRNA *UNUSED(prop), int *free)
{
	EnumPropertyItem *item = NULL, item_tmp = {0};
	int totitem = 0;
	int i = 0;

	/* don't need context but avoid docgen using this */
	if (C == NULL || object_mouse_select_menu_data[i].idname[0] == '\0') {
		return DummyRNA_NULL_items;
	}

	for (; i < SEL_MENU_SIZE && object_mouse_select_menu_data[i].idname[0] != '\0'; i++) {
		item_tmp.name = object_mouse_select_menu_data[i].idname;
		item_tmp.identifier = object_mouse_select_menu_data[i].idname;
		item_tmp.value = i;
		item_tmp.icon = object_mouse_select_menu_data[i].icon;
		RNA_enum_item_add(&item, &totitem, &item_tmp);
	}

	RNA_enum_item_end(&item, &totitem);
	*free = 1;

	return item;
}

static int object_select_menu_exec(bContext *C, wmOperator *op)
{
	int name_index = RNA_enum_get(op->ptr, "name");
	short extend = RNA_boolean_get(op->ptr, "extend");
	short changed = 0;
	const char *name = object_mouse_select_menu_data[name_index].idname;

	if (!extend) {
		CTX_DATA_BEGIN (C, Base *, base, selectable_bases)
		{
			if (base->flag & SELECT) {
				ED_base_object_select(base, BA_DESELECT);
				changed = 1;
			}
		}
		CTX_DATA_END;
	}

	CTX_DATA_BEGIN (C, Base *, base, selectable_bases)
	{
		/* this is a bit dodjy, there should only be ONE object with this name, but library objects can mess this up */
		if (strcmp(name, base->object->id.name + 2) == 0) {
			ED_base_object_activate(C, base);
			ED_base_object_select(base, BA_SELECT);
			changed = 1;
		}
	}
	CTX_DATA_END;

	/* weak but ensures we activate menu again before using the enum */
	memset(object_mouse_select_menu_data, 0, sizeof(object_mouse_select_menu_data));

	/* undo? */
	if (changed) {
		WM_event_add_notifier(C, NC_SCENE | ND_OB_SELECT, CTX_data_scene(C));
		return OPERATOR_FINISHED;
	}
	else {
		return OPERATOR_CANCELLED;
	}
}

void VIEW3D_OT_select_menu(wmOperatorType *ot)
{
	PropertyRNA *prop;

	/* identifiers */
	ot->name = "Select Menu";
	ot->description = "Menu object selection";
	ot->idname = "VIEW3D_OT_select_menu";

	/* api callbacks */
	ot->invoke = WM_menu_invoke;
	ot->exec = object_select_menu_exec;

	/* flags */
	ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;

	/* keyingset to use (dynamic enum) */
	prop = RNA_def_enum(ot->srna, "name", DummyRNA_NULL_items, 0, "Object Name", "");
	RNA_def_enum_funcs(prop, object_select_menu_enum_itemf);
	RNA_def_property_flag(prop, PROP_HIDDEN);
	ot->prop = prop;

	RNA_def_boolean(ot->srna, "extend", 0, "Extend", "Extend selection instead of deselecting everything first");
}

static void deselectall_except(Scene *scene, Base *b)   /* deselect all except b */
{
	Base *base;
	
	for (base = FIRSTBASE; base; base = base->next) {
		if (base->flag & SELECT) {
			if (b != base) {
				ED_base_object_select(base, BA_DESELECT);
			}
		}
	}
}

static Base *object_mouse_select_menu(bContext *C, ViewContext *vc, unsigned int *buffer, int hits, const int mval[2], short extend)
{
	short baseCount = 0;
	short ok;
	LinkNode *linklist = NULL;
	
	CTX_DATA_BEGIN (C, Base *, base, selectable_bases)
	{
		ok = FALSE;

		/* two selection methods, the CTRL select uses max dist of 15 */
		if (buffer) {
			int a;
			for (a = 0; a < hits; a++) {
				/* index was converted */
				if (base->selcol == buffer[(4 * a) + 3])
					ok = TRUE;
			}
		}
		else {
			int temp, dist = 15;
			ED_view3d_project_base(vc->ar, base);
			
			temp = abs(base->sx - mval[0]) + abs(base->sy - mval[1]);
			if (temp < dist)
				ok = TRUE;
		}

		if (ok) {
			baseCount++;
			BLI_linklist_prepend(&linklist, base);

			if (baseCount == SEL_MENU_SIZE)
				break;
		}
	}
	CTX_DATA_END;

	if (baseCount == 0) {
		return NULL;
	}
	if (baseCount == 1) {
		Base *base = (Base *)linklist->link;
		BLI_linklist_free(linklist, NULL);
		return base;
	}
	else {
		/* UI, full in static array values that we later use in an enum function */
		LinkNode *node;
		int i;

		memset(object_mouse_select_menu_data, 0, sizeof(object_mouse_select_menu_data));

		for (node = linklist, i = 0; node; node = node->next, i++) {
			Base *base = node->link;
			Object *ob = base->object;
			char *name = ob->id.name + 2;

			BLI_strncpy(object_mouse_select_menu_data[i].idname, name, MAX_ID_NAME - 2);
			object_mouse_select_menu_data[i].icon = uiIconFromID(&ob->id);
		}

		{
			PointerRNA ptr;

			WM_operator_properties_create(&ptr, "VIEW3D_OT_select_menu");
			RNA_boolean_set(&ptr, "extend", extend);
			WM_operator_name_call(C, "VIEW3D_OT_select_menu", WM_OP_INVOKE_DEFAULT, &ptr);
			WM_operator_properties_free(&ptr);
		}

		BLI_linklist_free(linklist, NULL);
		return NULL;
	}
}

/* we want a select buffer with bones, if there are... */
/* so check three selection levels and compare */
static short mixed_bones_object_selectbuffer(ViewContext *vc, unsigned int *buffer, const int mval[2])
{
	rcti rect;
	int offs;
	short a, hits15, hits9 = 0, hits5 = 0;
	short has_bones15 = 0, has_bones9 = 0, has_bones5 = 0;
	
	BLI_rcti_init(&rect, mval[0] - 14, mval[0] + 14, mval[1] - 14, mval[1] + 14);
	hits15 = view3d_opengl_select(vc, buffer, MAXPICKBUF, &rect);
	if (hits15 > 0) {
		for (a = 0; a < hits15; a++) if (buffer[4 * a + 3] & 0xFFFF0000) has_bones15 = 1;

		offs = 4 * hits15;
		BLI_rcti_init(&rect, mval[0] - 9, mval[0] + 9, mval[1] - 9, mval[1] + 9);
		hits9 = view3d_opengl_select(vc, buffer + offs, MAXPICKBUF - offs, &rect);
		if (hits9 > 0) {
			for (a = 0; a < hits9; a++) if (buffer[offs + 4 * a + 3] & 0xFFFF0000) has_bones9 = 1;

			offs += 4 * hits9;
			BLI_rcti_init(&rect, mval[0] - 5, mval[0] + 5, mval[1] - 5, mval[1] + 5);
			hits5 = view3d_opengl_select(vc, buffer + offs, MAXPICKBUF - offs, &rect);
			if (hits5 > 0) {
				for (a = 0; a < hits5; a++) if (buffer[offs + 4 * a + 3] & 0xFFFF0000) has_bones5 = 1;
			}
		}
		
		if (has_bones5) {
			offs = 4 * hits15 + 4 * hits9;
			memcpy(buffer, buffer + offs, 4 * offs);
			return hits5;
		}
		if (has_bones9) {
			offs = 4 * hits15;
			memcpy(buffer, buffer + offs, 4 * offs);
			return hits9;
		}
		if (has_bones15) {
			return hits15;
		}
		
		if (hits5 > 0) {
			offs = 4 * hits15 + 4 * hits9;
			memcpy(buffer, buffer + offs, 4 * offs);
			return hits5;
		}
		if (hits9 > 0) {
			offs = 4 * hits15;
			memcpy(buffer, buffer + offs, 4 * offs);
			return hits9;
		}
		return hits15;
	}
	
	return 0;
}

/* returns basact */
static Base *mouse_select_eval_buffer(ViewContext *vc, unsigned int *buffer, int hits, const int mval[2], Base *startbase, int has_bones)
{
	Scene *scene = vc->scene;
	View3D *v3d = vc->v3d;
	Base *base, *basact = NULL;
	static int lastmval[2] = {-100, -100};
	int a, do_nearest = FALSE;
	
	/* define if we use solid nearest select or not */
	if (v3d->drawtype > OB_WIRE) {
		do_nearest = TRUE;
		if (ABS(mval[0] - lastmval[0]) < 3 && ABS(mval[1] - lastmval[1]) < 3) {
			if (!has_bones) /* hrms, if theres bones we always do nearest */
				do_nearest = FALSE;
		}
	}
	lastmval[0] = mval[0]; lastmval[1] = mval[1];
	
	if (do_nearest) {
		unsigned int min = 0xFFFFFFFF;
		int selcol = 0, notcol = 0;
		
		
		if (has_bones) {
			/* we skip non-bone hits */
			for (a = 0; a < hits; a++) {
				if (min > buffer[4 * a + 1] && (buffer[4 * a + 3] & 0xFFFF0000) ) {
					min = buffer[4 * a + 1];
					selcol = buffer[4 * a + 3] & 0xFFFF;
				}
			}
		}
		else {
			/* only exclude active object when it is selected... */
			if (BASACT && (BASACT->flag & SELECT) && hits > 1) notcol = BASACT->selcol;
			
			for (a = 0; a < hits; a++) {
				if (min > buffer[4 * a + 1] && notcol != (buffer[4 * a + 3] & 0xFFFF)) {
					min = buffer[4 * a + 1];
					selcol = buffer[4 * a + 3] & 0xFFFF;
				}
			}
		}
		
		base = FIRSTBASE;
		while (base) {
			if (BASE_SELECTABLE(v3d, base)) {
				if (base->selcol == selcol) break;
			}
			base = base->next;
		}
		if (base) basact = base;
	}
	else {
		
		base = startbase;
		while (base) {
			/* skip objects with select restriction, to prevent prematurely ending this loop
			 * with an un-selectable choice */
			if (base->object->restrictflag & OB_RESTRICT_SELECT) {
				base = base->next;
				if (base == NULL) base = FIRSTBASE;
				if (base == startbase) break;
			}
			
			if (BASE_SELECTABLE(v3d, base)) {
				for (a = 0; a < hits; a++) {
					if (has_bones) {
						/* skip non-bone objects */
						if ((buffer[4 * a + 3] & 0xFFFF0000)) {
							if (base->selcol == (buffer[(4 * a) + 3] & 0xFFFF))
								basact = base;
						}
					}
					else {
						if (base->selcol == (buffer[(4 * a) + 3] & 0xFFFF))
							basact = base;
					}
				}
			}
			
			if (basact) break;
			
			base = base->next;
			if (base == NULL) base = FIRSTBASE;
			if (base == startbase) break;
		}
	}
	
	return basact;
}

/* mval comes from event->mval, only use within region handlers */
Base *ED_view3d_give_base_under_cursor(bContext *C, const int mval[2])
{
	ViewContext vc;
	Base *basact = NULL;
	unsigned int buffer[4 * MAXPICKBUF];
	int hits;
	
	/* setup view context for argument to callbacks */
	view3d_operator_needs_opengl(C);
	view3d_set_viewcontext(C, &vc);
	
	hits = mixed_bones_object_selectbuffer(&vc, buffer, mval);
	
	if (hits > 0) {
		int a, has_bones = 0;
		
		for (a = 0; a < hits; a++) if (buffer[4 * a + 3] & 0xFFFF0000) has_bones = 1;
		
		basact = mouse_select_eval_buffer(&vc, buffer, hits, mval, vc.scene->base.first, has_bones);
	}
	
	return basact;
}

static void deselect_all_tracks(MovieTracking *tracking)
{
	MovieTrackingObject *object;

	object = tracking->objects.first;
	while (object) {
		ListBase *tracksbase = BKE_tracking_object_get_tracks(tracking, object);
		MovieTrackingTrack *track = tracksbase->first;

		while (track) {
			BKE_tracking_track_deselect(track, TRACK_AREA_ALL);

			track = track->next;
		}

		object = object->next;
	}
}

/* mval is region coords */
static int mouse_select(bContext *C, const int mval[2], short extend, short deselect, short toggle, short obcenter, short enumerate)
{
	ViewContext vc;
	ARegion *ar = CTX_wm_region(C);
	View3D *v3d = CTX_wm_view3d(C);
	Scene *scene = CTX_data_scene(C);
	Base *base, *startbase = NULL, *basact = NULL, *oldbasact = NULL;
	int temp, a, dist = 100;
	int retval = 0;
	short hits;
	
	/* setup view context for argument to callbacks */
	view3d_set_viewcontext(C, &vc);
	
	/* always start list from basact in wire mode */
	startbase =  FIRSTBASE;
	if (BASACT && BASACT->next) startbase = BASACT->next;
	
	/* This block uses the control key to make the object selected by its center point rather than its contents */
	/* in editmode do not activate */
	if (obcenter) {
		
		/* note; shift+alt goes to group-flush-selecting */
		if (enumerate) {
			basact = object_mouse_select_menu(C, &vc, NULL, 0, mval, extend);
		}
		else {
			base = startbase;
			while (base) {
				if (BASE_SELECTABLE(v3d, base)) {
					ED_view3d_project_base(ar, base);
					temp = abs(base->sx - mval[0]) + abs(base->sy - mval[1]);
					if (base == BASACT) temp += 10;
					if (temp < dist) {
						
						dist = temp;
						basact = base;
					}
				}
				base = base->next;
				
				if (base == NULL) base = FIRSTBASE;
				if (base == startbase) break;
			}
		}
	}
	else {
		unsigned int buffer[4 * MAXPICKBUF];

		/* if objects have posemode set, the bones are in the same selection buffer */
		
		hits = mixed_bones_object_selectbuffer(&vc, buffer, mval);
		
		if (hits > 0) {
			int has_bones = 0;
			
			/* note: bundles are handling in the same way as bones */
			for (a = 0; a < hits; a++) if (buffer[4 * a + 3] & 0xFFFF0000) has_bones = 1;

			/* note; shift+alt goes to group-flush-selecting */
			if (has_bones == 0 && enumerate) {
				basact = object_mouse_select_menu(C, &vc, buffer, hits, mval, extend);
			}
			else {
				basact = mouse_select_eval_buffer(&vc, buffer, hits, mval, startbase, has_bones);
			}
			
			if (has_bones && basact) {
				if (basact->object->type == OB_CAMERA) {
					if (BASACT == basact) {
						int i, hitresult;
						int changed = 0;

						for (i = 0; i < hits; i++) {
							hitresult = buffer[3 + (i * 4)];

							/* if there's bundles in buffer select bundles first,
							 * so non-camera elements should be ignored in buffer */
							if (basact->selcol != (hitresult & 0xFFFF)) {
								continue;
							}

							/* index of bundle is 1<<16-based. if there's no "bone" index
							 * in height word, this buffer value belongs to camera,. not to bundle */
							if (buffer[4 * i + 3] & 0xFFFF0000) {
								MovieClip *clip = BKE_object_movieclip_get(scene, basact->object, 0);
								MovieTracking *tracking = &clip->tracking;
								ListBase *tracksbase;
								MovieTrackingTrack *track;

								track = BKE_tracking_track_get_indexed(&clip->tracking, hitresult >> 16, &tracksbase);

								if (TRACK_SELECTED(track) && extend) {
									changed = 0;
									BKE_tracking_track_deselect(track, TRACK_AREA_ALL);
								}
								else {
									int oldsel = TRACK_SELECTED(track) ? 1 : 0;
									if (!extend)
										deselect_all_tracks(tracking);

									BKE_tracking_track_select(tracksbase, track, TRACK_AREA_ALL, extend);

									if (oldsel != (TRACK_SELECTED(track) ? 1 : 0))
										changed = 1;
								}

								basact->flag |= SELECT;
								basact->object->flag = basact->flag;

								retval = 1;

								WM_event_add_notifier(C, NC_MOVIECLIP | ND_SELECT, track);
								WM_event_add_notifier(C, NC_SCENE | ND_OB_SELECT, scene);

								break;
							}
						}

						if (!changed) {
							/* fallback to regular object selection if no new bundles were selected,
							 * allows to select object parented to reconstruction object */
							basact = mouse_select_eval_buffer(&vc, buffer, hits, mval, startbase, 0);
						}
					}
				}
				else if (ED_do_pose_selectbuffer(scene, basact, buffer, hits, extend, deselect, toggle) ) {
					/* then bone is found */
				
					/* we make the armature selected: 
					 * not-selected active object in posemode won't work well for tools */
					basact->flag |= SELECT;
					basact->object->flag = basact->flag;
					
					retval = 1;
					WM_event_add_notifier(C, NC_OBJECT | ND_BONE_SELECT, basact->object);
					WM_event_add_notifier(C, NC_OBJECT | ND_BONE_ACTIVE, basact->object);
					
					/* in weightpaint, we use selected bone to select vertexgroup, so no switch to new active object */
					if (BASACT && (BASACT->object->mode & OB_MODE_WEIGHT_PAINT)) {
						/* prevent activating */
						basact = NULL;
					}

				}
				/* prevent bone selecting to pass on to object selecting */
				if (basact == BASACT)
					basact = NULL;
			}
		}
	}
	
	/* so, do we have something selected? */
	if (basact) {
		retval = 1;
		
		if (vc.obedit) {
			/* only do select */
			deselectall_except(scene, basact);
			ED_base_object_select(basact, BA_SELECT);
		}
		/* also prevent making it active on mouse selection */
		else if (BASE_SELECTABLE(v3d, basact)) {

			oldbasact = BASACT;
			
			if (extend) {
				ED_base_object_select(basact, BA_SELECT);
			}
			else if (deselect) {
				ED_base_object_select(basact, BA_DESELECT);
			}
			else if (toggle) {
				if (basact->flag & SELECT) {
					if (basact == oldbasact) {
						ED_base_object_select(basact, BA_DESELECT);
					}
				}
				else {
					ED_base_object_select(basact, BA_SELECT);
				}
			}
			else {
				deselectall_except(scene, basact);
				ED_base_object_select(basact, BA_SELECT);
			}

			if (oldbasact != basact) {
				ED_base_object_activate(C, basact); /* adds notifier */
			}
		}

		WM_event_add_notifier(C, NC_SCENE | ND_OB_SELECT, scene);
	}

	return retval;
}

/* ********************  border and circle ************************************** */

typedef struct BoxSelectUserData {
	ViewContext *vc;
	const rcti *rect;
	int select;

	/* runtime */
	int pass;
	int is_done;
	int is_change;
} BoxSelectUserData;

static void view3d_userdata_boxselect_init(BoxSelectUserData *r_data,
                                           ViewContext *vc, const rcti *rect, const int select)
{
	r_data->vc = vc;
	r_data->rect = rect;
	r_data->select = select;

	/* runtime */
	r_data->pass = 0;
	r_data->is_done = FALSE;
	r_data->is_change = FALSE;
}

int edge_inside_circle(int centx, int centy, int radius, int x1, int y1, int x2, int y2)
{
	int radius_squared = radius * radius;

	/* check points in circle itself */
	if ((x1 - centx) * (x1 - centx) + (y1 - centy) * (y1 - centy) <= radius_squared) {
		return TRUE;
	}
	else if ((x2 - centx) * (x2 - centx) + (y2 - centy) * (y2 - centy) <= radius_squared) {
		return TRUE;
	}
	else {
		const float cent[2] = {centx, centy};
		const float v1[2] = {x1, y1};
		const float v2[2] = {x2, y2};
		/* pointdistline */
		if (dist_squared_to_line_segment_v2(cent, v1, v2) < (float)radius_squared) {
			return TRUE;
		}
	}

	return FALSE;
}

static void do_nurbs_box_select__doSelect(void *userData, Nurb *UNUSED(nu), BPoint *bp, BezTriple *bezt, int beztindex, int x, int y)
{
	BoxSelectUserData *data = userData;
	Object *obedit = data->vc->obedit;
	Curve *cu = (Curve *)obedit->data;

	if (BLI_rcti_isect_pt(data->rect, x, y)) {
		if (bp) {
			bp->f1 = data->select ? (bp->f1 | SELECT) : (bp->f1 & ~SELECT);
			if (bp == cu->lastsel && !(bp->f1 & SELECT)) cu->lastsel = NULL;
		}
		else {
			if (cu->drawflag & CU_HIDE_HANDLES) {
				/* can only be (beztindex == 0) here since handles are hidden */
				bezt->f1 = bezt->f2 = bezt->f3 = data->select ? (bezt->f2 | SELECT) : (bezt->f2 & ~SELECT);
			}
			else {
				if (beztindex == 0) {
					bezt->f1 = data->select ? (bezt->f1 | SELECT) : (bezt->f1 & ~SELECT);
				}
				else if (beztindex == 1) {
					bezt->f2 = data->select ? (bezt->f2 | SELECT) : (bezt->f2 & ~SELECT);
				}
				else {
					bezt->f3 = data->select ? (bezt->f3 | SELECT) : (bezt->f3 & ~SELECT);
				}
			}

			if (bezt == cu->lastsel && !(bezt->f2 & SELECT)) cu->lastsel = NULL;
		}
	}
}
static int do_nurbs_box_select(ViewContext *vc, rcti *rect, int select, int extend)
{
	BoxSelectUserData data;
	
	view3d_userdata_boxselect_init(&data, vc, rect, select);

	if (extend == 0 && select)
		CU_deselect_all(vc->obedit);

	ED_view3d_init_mats_rv3d(vc->obedit, vc->rv3d); /* for foreach's screen/vert projection */
	nurbs_foreachScreenVert(vc, do_nurbs_box_select__doSelect, &data);

	return OPERATOR_FINISHED;
}

static void do_lattice_box_select__doSelect(void *userData, BPoint *bp, int x, int y)
{
	BoxSelectUserData *data = userData;

	if (BLI_rcti_isect_pt(data->rect, x, y)) {
		bp->f1 = data->select ? (bp->f1 | SELECT) : (bp->f1 & ~SELECT);
	}
}
static int do_lattice_box_select(ViewContext *vc, rcti *rect, int select, int extend)
{
	BoxSelectUserData data;

	view3d_userdata_boxselect_init(&data, vc, rect, select);

	if (extend == 0 && select)
		ED_setflagsLatt(vc->obedit, 0);

	ED_view3d_init_mats_rv3d(vc->obedit, vc->rv3d); /* for foreach's screen/vert projection */
	lattice_foreachScreenVert(vc, do_lattice_box_select__doSelect, &data);
	
	return OPERATOR_FINISHED;
}

static void do_mesh_box_select__doSelectVert(void *userData, BMVert *eve, int x, int y, int UNUSED(index))
{
	BoxSelectUserData *data = userData;

	if (BLI_rcti_isect_pt(data->rect, x, y)) {
		BM_vert_select_set(data->vc->em->bm, eve, data->select);
	}
}
static void do_mesh_box_select__doSelectEdge(void *userData, BMEdge *eed, int x0, int y0, int x1, int y1, int index)
{
	BoxSelectUserData *data = userData;

	if (EDBM_backbuf_check(bm_solidoffs + index)) {
		if (data->pass == 0) {
			if (edge_fully_inside_rect(data->rect, x0, y0, x1, y1)) {
				BM_edge_select_set(data->vc->em->bm, eed, data->select);
				data->is_done = TRUE;
			}
		}
		else {
			if (edge_inside_rect(data->rect, x0, y0, x1, y1)) {
				BM_edge_select_set(data->vc->em->bm, eed, data->select);
			}
		}
	}
}
static void do_mesh_box_select__doSelectFace(void *userData, BMFace *efa, int x, int y, int UNUSED(index))
{
	BoxSelectUserData *data = userData;

	if (BLI_rcti_isect_pt(data->rect, x, y)) {
		BM_face_select_set(data->vc->em->bm, efa, data->select);
	}
}
static int do_mesh_box_select(ViewContext *vc, rcti *rect, int select, int extend)
{
	BoxSelectUserData data;
	ToolSettings *ts = vc->scene->toolsettings;
	int bbsel;
	
	view3d_userdata_boxselect_init(&data, vc, rect, select);

	if (extend == 0 && select)
		EDBM_flag_disable_all(vc->em, BM_ELEM_SELECT);

	/* for non zbuf projections, don't change the GL state */
	ED_view3d_init_mats_rv3d(vc->obedit, vc->rv3d);

	glLoadMatrixf(vc->rv3d->viewmat);
	bbsel = EDBM_backbuf_border_init(vc, rect->xmin, rect->ymin, rect->xmax, rect->ymax);

	if (ts->selectmode & SCE_SELECT_VERTEX) {
		if (bbsel) {
			edbm_backbuf_check_and_select_verts(vc->em, select);
		}
		else {
			mesh_foreachScreenVert(vc, do_mesh_box_select__doSelectVert, &data, V3D_CLIP_TEST_RV3D_CLIPPING);
		}
	}
	if (ts->selectmode & SCE_SELECT_EDGE) {
		/* Does both bbsel and non-bbsel versions (need screen cos for both) */

		data.pass = 0;
		mesh_foreachScreenEdge(vc, do_mesh_box_select__doSelectEdge, &data, V3D_CLIP_TEST_OFF);

		if (data.is_done == 0) {
			data.pass = 1;
			mesh_foreachScreenEdge(vc, do_mesh_box_select__doSelectEdge, &data, V3D_CLIP_TEST_OFF);
		}
	}
	
	if (ts->selectmode & SCE_SELECT_FACE) {
		if (bbsel) {
			edbm_backbuf_check_and_select_faces(vc->em, select);
		}
		else {
			mesh_foreachScreenFace(vc, do_mesh_box_select__doSelectFace, &data);
		}
	}
	
	EDBM_backbuf_free();
		
	EDBM_selectmode_flush(vc->em);
	
	return OPERATOR_FINISHED;
}

static int do_meta_box_select(ViewContext *vc, rcti *rect, int select, int extend)
{
	MetaBall *mb = (MetaBall *)vc->obedit->data;
	MetaElem *ml;
	int a;

	unsigned int buffer[4 * MAXPICKBUF];
	short hits;

	hits = view3d_opengl_select(vc, buffer, MAXPICKBUF, rect);

	if (extend == 0 && select)
		BKE_mball_deselect_all(mb);
	
	for (ml = mb->editelems->first; ml; ml = ml->next) {
		for (a = 0; a < hits; a++) {
			if (ml->selcol1 == buffer[(4 * a) + 3]) {
				ml->flag |= MB_SCALE_RAD;
				if (select) ml->flag |= SELECT;
				else ml->flag &= ~SELECT;
				break;
			}
			if (ml->selcol2 == buffer[(4 * a) + 3]) {
				ml->flag &= ~MB_SCALE_RAD;
				if (select) ml->flag |= SELECT;
				else ml->flag &= ~SELECT;
				break;
			}
		}
	}

	return OPERATOR_FINISHED;
}

static int do_armature_box_select(ViewContext *vc, rcti *rect, short select, short extend)
{
	bArmature *arm = vc->obedit->data;
	EditBone *ebone;
	int a;

	unsigned int buffer[4 * MAXPICKBUF];
	short hits;

	hits = view3d_opengl_select(vc, buffer, MAXPICKBUF, rect);
	
	/* clear flag we use to detect point was affected */
	for (ebone = arm->edbo->first; ebone; ebone = ebone->next)
		ebone->flag &= ~BONE_DONE;
	
	if (extend == 0 && select)
		ED_armature_deselect_all_visible(vc->obedit);

	/* first we only check points inside the border */
	for (a = 0; a < hits; a++) {
		int index = buffer[(4 * a) + 3];
		if (index != -1) {
			ebone = BLI_findlink(arm->edbo, index & ~(BONESEL_ANY));
			if ((ebone->flag & BONE_UNSELECTABLE) == 0) {
				if (index & BONESEL_TIP) {
					ebone->flag |= BONE_DONE;
					if (select) ebone->flag |= BONE_TIPSEL;
					else ebone->flag &= ~BONE_TIPSEL;
				}
				
				if (index & BONESEL_ROOT) {
					ebone->flag |= BONE_DONE;
					if (select) ebone->flag |= BONE_ROOTSEL;
					else ebone->flag &= ~BONE_ROOTSEL;
				}
			}
		}
	}
	
	/* now we have to flush tag from parents... */
	for (ebone = arm->edbo->first; ebone; ebone = ebone->next) {
		if (ebone->parent && (ebone->flag & BONE_CONNECTED)) {
			if (ebone->parent->flag & BONE_DONE)
				ebone->flag |= BONE_DONE;
		}
	}
	
	/* only select/deselect entire bones when no points where in the rect */
	for (a = 0; a < hits; a++) {
		int index = buffer[(4 * a) + 3];
		if (index != -1) {
			ebone = BLI_findlink(arm->edbo, index & ~(BONESEL_ANY));
			if (index & BONESEL_BONE) {
				if ((ebone->flag & BONE_UNSELECTABLE) == 0) {
					if (!(ebone->flag & BONE_DONE)) {
						if (select)
							ebone->flag |= (BONE_ROOTSEL | BONE_TIPSEL | BONE_SELECTED);
						else
							ebone->flag &= ~(BONE_ROOTSEL | BONE_TIPSEL | BONE_SELECTED);
					}
				}
			}
		}
	}
	
	ED_armature_sync_selection(arm->edbo);
	
	return OPERATOR_CANCELLED;
}

static int do_object_pose_box_select(bContext *C, ViewContext *vc, rcti *rect, int select, int extend)
{
	Bone *bone;
	Object *ob = vc->obact;
	unsigned int *vbuffer = NULL; /* selection buffer	*/
	unsigned int *col;          /* color in buffer	*/
	int bone_only;
	int bone_selected = 0;
	int totobj = MAXPICKBUF; /* XXX solve later */
	short hits;
	
	if ((ob) && (ob->mode & OB_MODE_POSE))
		bone_only = 1;
	else
		bone_only = 0;
	
	if (extend == 0 && select) {
		if (bone_only) {
			CTX_DATA_BEGIN (C, bPoseChannel *, pchan, visible_pose_bones)
			{
				if ((pchan->bone->flag & BONE_UNSELECTABLE) == 0) {
					pchan->bone->flag &= ~(BONE_SELECTED | BONE_TIPSEL | BONE_ROOTSEL);
				}
			}
			CTX_DATA_END;
		}
		else {
			object_deselect_all_visible(vc->scene, vc->v3d);
		}
	}

	/* selection buffer now has bones potentially too, so we add MAXPICKBUF */
	vbuffer = MEM_mallocN(4 * (totobj + MAXPICKBUF) * sizeof(unsigned int), "selection buffer");
	hits = view3d_opengl_select(vc, vbuffer, 4 * (totobj + MAXPICKBUF), rect);
	/*
	 * LOGIC NOTES (theeth):
	 * The buffer and ListBase have the same relative order, which makes the selection
	 * very simple. Loop through both data sets at the same time, if the color
	 * is the same as the object, we have a hit and can move to the next color
	 * and object pair, if not, just move to the next object,
	 * keeping the same color until we have a hit.
	 * 
	 * The buffer order is defined by OGL standard, hopefully no stupid GFX card
	 * does it incorrectly.
	 */

	if (hits > 0) { /* no need to loop if there's no hit */
		Base *base;
		col = vbuffer + 3;
		
		for (base = vc->scene->base.first; base && hits; base = base->next) {
			if (BASE_SELECTABLE(vc->v3d, base)) {
				while (base->selcol == (*col & 0xFFFF)) {   /* we got an object */
					if (*col & 0xFFFF0000) {                    /* we got a bone */
						bone = get_indexed_bone(base->object, *col & ~(BONESEL_ANY));
						if (bone) {
							if (select) {
								if ((bone->flag & BONE_UNSELECTABLE) == 0) {
									bone->flag |= BONE_SELECTED;
									bone_selected = 1;
								}
							}
							else {
								bArmature *arm = base->object->data;
								bone->flag &= ~BONE_SELECTED;
								if (arm->act_bone == bone)
									arm->act_bone = NULL;
							}
						}
					}
					else if (!bone_only) {
						if (select)
							ED_base_object_select(base, BA_SELECT);
						else
							ED_base_object_select(base, BA_DESELECT);
					}
					
					col += 4; /* next color */
					hits--;
					if (hits == 0) break;
				}
			}
			
			if (bone_selected) {
				Object *ob = base->object;
				
				if (ob && (ob->type == OB_ARMATURE)) {
					bArmature *arm = ob->data;
					
					WM_event_add_notifier(C, NC_OBJECT | ND_BONE_SELECT, ob);
					
					if (arm && (arm->flag & ARM_HAS_VIZ_DEPS)) {
						/* mask modifier ('armature' mode), etc. */
						DAG_id_tag_update(&ob->id, OB_RECALC_DATA);
					}
				}
			}
		}
		
		WM_event_add_notifier(C, NC_SCENE | ND_OB_SELECT, vc->scene);
	}
	MEM_freeN(vbuffer);

	return hits > 0 ? OPERATOR_FINISHED : OPERATOR_CANCELLED;
}

static int view3d_borderselect_exec(bContext *C, wmOperator *op)
{
	ViewContext vc;
	rcti rect;
	short extend;
	short select;

	int ret = OPERATOR_CANCELLED;

	view3d_operator_needs_opengl(C);

	/* setup view context for argument to callbacks */
	view3d_set_viewcontext(C, &vc);
	
	select = (RNA_int_get(op->ptr, "gesture_mode") == GESTURE_MODAL_SELECT);
	WM_operator_properties_border_to_rcti(op, &rect);
	extend = RNA_boolean_get(op->ptr, "extend");

	if (vc.obedit) {
		switch (vc.obedit->type) {
			case OB_MESH:
				vc.em = BMEdit_FromObject(vc.obedit);
				ret = do_mesh_box_select(&vc, &rect, select, extend);
//			if (EM_texFaceCheck())
				if (ret & OPERATOR_FINISHED) {
					WM_event_add_notifier(C, NC_GEOM | ND_SELECT, vc.obedit->data);
				}
				break;
			case OB_CURVE:
			case OB_SURF:
				ret = do_nurbs_box_select(&vc, &rect, select, extend);
				if (ret & OPERATOR_FINISHED) {
					WM_event_add_notifier(C, NC_GEOM | ND_SELECT, vc.obedit->data);
				}
				break;
			case OB_MBALL:
				ret = do_meta_box_select(&vc, &rect, select, extend);
				if (ret & OPERATOR_FINISHED) {
					WM_event_add_notifier(C, NC_GEOM | ND_SELECT, vc.obedit->data);
				}
				break;
			case OB_ARMATURE:
				ret = do_armature_box_select(&vc, &rect, select, extend);
				if (ret & OPERATOR_FINISHED) {
					WM_event_add_notifier(C, NC_OBJECT | ND_BONE_SELECT, vc.obedit);
				}
				break;
			case OB_LATTICE:
				ret = do_lattice_box_select(&vc, &rect, select, extend);
				if (ret & OPERATOR_FINISHED) {
					WM_event_add_notifier(C, NC_GEOM | ND_SELECT, vc.obedit->data);
				}
				break;
			default:
				assert(!"border select on incorrect object type");
		}
	}
	else {  /* no editmode, unified for bones and objects */
		if (vc.obact && vc.obact->mode & OB_MODE_SCULPT) {
			/* pass */
		}
		else if (vc.obact && paint_facesel_test(vc.obact)) {
			ret = do_paintface_box_select(&vc, &rect, select, extend);
		}
		else if (vc.obact && paint_vertsel_test(vc.obact)) {
			ret = do_paintvert_box_select(&vc, &rect, select, extend);
		}
		else if (vc.obact && vc.obact->mode & OB_MODE_PARTICLE_EDIT) {
			ret = PE_border_select(C, &rect, select, extend);
		}
		else { /* object mode with none active */
			ret = do_object_pose_box_select(C, &vc, &rect, select, extend);
		}
	}

	return ret;
} 


/* *****************Selection Operators******************* */

/* ****** Border Select ****** */
void VIEW3D_OT_select_border(wmOperatorType *ot)
{
	/* identifiers */
	ot->name = "Border Select";
	ot->description = "Select items using border selection";
	ot->idname = "VIEW3D_OT_select_border";
	
	/* api callbacks */
	ot->invoke = WM_border_select_invoke;
	ot->exec = view3d_borderselect_exec;
	ot->modal = WM_border_select_modal;
	ot->poll = view3d_selectable_data;
	ot->cancel = WM_border_select_cancel;
	
	/* flags */
	ot->flag = OPTYPE_UNDO;
	
	/* rna */
	WM_operator_properties_gesture_border(ot, TRUE);
}

/* mouse selection in weight paint */
/* gets called via generic mouse select operator */
static int mouse_weight_paint_vertex_select(bContext *C, const int mval[2], short extend, short deselect, short toggle, Object *obact)
{
	Mesh *me = obact->data; /* already checked for NULL */
	unsigned int index = 0;
	MVert *mv;

	if (ED_mesh_pick_vert(C, me, mval, &index, ED_MESH_PICK_DEFAULT_VERT_SIZE)) {
		mv = &me->mvert[index];
		if (extend) {
			mv->flag |= SELECT;
		}
		else if (deselect) {
			mv->flag &= ~SELECT;
		}
		else if (toggle) {
			mv->flag ^= SELECT;
		}
		else {
			paintvert_deselect_all_visible(obact, SEL_DESELECT, FALSE);
			mv->flag |= SELECT;
		}
		paintvert_flush_flags(obact);
		WM_event_add_notifier(C, NC_GEOM | ND_SELECT, obact->data);
		return 1;
	}
	return 0;
}

/* ****** Mouse Select ****** */


static int view3d_select_invoke(bContext *C, wmOperator *op, wmEvent *event)
{
	Object *obedit = CTX_data_edit_object(C);
	Object *obact = CTX_data_active_object(C);
	short extend = RNA_boolean_get(op->ptr, "extend");
	short deselect = RNA_boolean_get(op->ptr, "deselect");
	short toggle = RNA_boolean_get(op->ptr, "toggle");
	short center = RNA_boolean_get(op->ptr, "center");
	short enumerate = RNA_boolean_get(op->ptr, "enumerate");
	short object = RNA_boolean_get(op->ptr, "object");
	int retval = 0;

	view3d_operator_needs_opengl(C);

	if (object) {
		obedit = NULL;
		obact = NULL;

		/* ack, this is incorrect but to do this correctly we would need an
		 * alternative editmode/objectmode keymap, this copies the functionality
		 * from 2.4x where Ctrl+Select in editmode does object select only */
		center = FALSE;
	}

	if (obedit && object == FALSE) {
		if (obedit->type == OB_MESH)
			retval = EDBM_select_pick(C, event->mval, extend, deselect, toggle);
		else if (obedit->type == OB_ARMATURE)
			retval = mouse_armature(C, event->mval, extend, deselect, toggle);
		else if (obedit->type == OB_LATTICE)
			retval = mouse_lattice(C, event->mval, extend, deselect, toggle);
		else if (ELEM(obedit->type, OB_CURVE, OB_SURF))
			retval = mouse_nurb(C, event->mval, extend, deselect, toggle);
		else if (obedit->type == OB_MBALL)
			retval = mouse_mball(C, event->mval, extend, deselect, toggle);
			
	}
	else if (obact && obact->mode & OB_MODE_SCULPT)
		return OPERATOR_CANCELLED;
	else if (obact && obact->mode & OB_MODE_PARTICLE_EDIT)
		return PE_mouse_particles(C, event->mval, extend, deselect, toggle);
	else if (obact && paint_facesel_test(obact))
		retval = paintface_mouse_select(C, obact, event->mval, extend, deselect, toggle);
	else if (paint_vertsel_test(obact))
		retval = mouse_weight_paint_vertex_select(C, event->mval, extend, deselect, toggle, obact);
	else
		retval = mouse_select(C, event->mval, extend, deselect, toggle, center, enumerate);

	/* passthrough allows tweaks
	 * FINISHED to signal one operator worked
	 * */
	if (retval)
		return OPERATOR_PASS_THROUGH | OPERATOR_FINISHED;
	else
		return OPERATOR_PASS_THROUGH;  /* nothing selected, just passthrough */
}

void VIEW3D_OT_select(wmOperatorType *ot)
{
	/* identifiers */
	ot->name = "Activate/Select";
	ot->description = "Activate/select item(s)";
	ot->idname = "VIEW3D_OT_select";
	
	/* api callbacks */
	ot->invoke = view3d_select_invoke;
	ot->poll = ED_operator_view3d_active;
	
	/* flags */
	ot->flag = OPTYPE_UNDO;
	
	/* properties */
	WM_operator_properties_mouse_select(ot);

	RNA_def_boolean(ot->srna, "center", 0, "Center", "Use the object center when selecting, in editmode used to extend object selection");
	RNA_def_boolean(ot->srna, "enumerate", 0, "Enumerate", "List objects under the mouse (object mode only)");
	RNA_def_boolean(ot->srna, "object", 0, "Object", "Use object selection (editmode only)");
}


/* -------------------- circle select --------------------------------------------- */

typedef struct CircleSelectUserData {
	ViewContext *vc;
	short select;
	int mval[2];
	float radius;
	float radius_squared;

	/* runtime */
	int is_change;
} CircleSelectUserData;

static void view3d_userdata_circleselect_init(CircleSelectUserData *r_data,
                                              ViewContext *vc, const int select, const int mval[2], const float rad)
{
	r_data->vc = vc;
	r_data->select = select;
	copy_v2_v2_int(r_data->mval, mval);
	r_data->radius = rad;
	r_data->radius_squared = rad * rad;

	/* runtime */
	r_data->is_change = FALSE;
}

static void mesh_circle_doSelectVert(void *userData, BMVert *eve, int x, int y, int UNUSED(index))
{
	CircleSelectUserData *data = userData;
	const float delta[2] = {(float)(x - data->mval[0]),
	                        (float)(y - data->mval[1])};

	if (len_squared_v2(delta) <= data->radius_squared) {
		BM_vert_select_set(data->vc->em->bm, eve, data->select);
	}
}
static void mesh_circle_doSelectEdge(void *userData, BMEdge *eed, int x0, int y0, int x1, int y1, int UNUSED(index))
{
	CircleSelectUserData *data = userData;

	if (edge_inside_circle(data->mval[0], data->mval[1], (int)data->radius, x0, y0, x1, y1)) {
		BM_edge_select_set(data->vc->em->bm, eed, data->select);
	}
}
static void mesh_circle_doSelectFace(void *userData, BMFace *efa, int x, int y, int UNUSED(index))
{
	CircleSelectUserData *data = userData;
	const float delta[2] = {(float)(x - data->mval[0]),
	                        (float)(y - data->mval[1])};

	if (len_squared_v2(delta) <= data->radius_squared) {
		BM_face_select_set(data->vc->em->bm, efa, data->select);
	}
}

static void mesh_circle_select(ViewContext *vc, int select, const int mval[2], float rad)
{
	ToolSettings *ts = vc->scene->toolsettings;
	int bbsel;
	CircleSelectUserData data;
	
	bbsel = EDBM_backbuf_circle_init(vc, mval[0], mval[1], (short)(rad + 1.0f));
	ED_view3d_init_mats_rv3d(vc->obedit, vc->rv3d); /* for foreach's screen/vert projection */

	vc->em = BMEdit_FromObject(vc->obedit);

	view3d_userdata_circleselect_init(&data, vc, select, mval, rad);

	if (ts->selectmode & SCE_SELECT_VERTEX) {
		if (bbsel) {
			edbm_backbuf_check_and_select_verts(vc->em, select == LEFTMOUSE);
		}
		else {
			mesh_foreachScreenVert(vc, mesh_circle_doSelectVert, &data, V3D_CLIP_TEST_RV3D_CLIPPING);
		}
	}

	if (ts->selectmode & SCE_SELECT_EDGE) {
		if (bbsel) {
			edbm_backbuf_check_and_select_edges(vc->em, select == LEFTMOUSE);
		}
		else {
			mesh_foreachScreenEdge(vc, mesh_circle_doSelectEdge, &data, V3D_CLIP_TEST_OFF);
		}
	}
	
	if (ts->selectmode & SCE_SELECT_FACE) {
		if (bbsel) {
			edbm_backbuf_check_and_select_faces(vc->em, select == LEFTMOUSE);
		}
		else {
			mesh_foreachScreenFace(vc, mesh_circle_doSelectFace, &data);
		}
	}

	EDBM_backbuf_free();
	EDBM_selectmode_flush(vc->em);
}

static void paint_facesel_circle_select(ViewContext *vc, int select, const int mval[2], float rad)
{
	Object *ob = vc->obact;
	Mesh *me = ob ? ob->data : NULL;
	/* int bbsel; */ /* UNUSED */

	if (me) {
		bm_vertoffs = me->totpoly + 1; /* max index array */

		/* bbsel= */ /* UNUSED */ EDBM_backbuf_circle_init(vc, mval[0], mval[1], (short)(rad + 1.0f));
		edbm_backbuf_check_and_select_tfaces(me, select == LEFTMOUSE);
		EDBM_backbuf_free();
		paintface_flush_flags(ob);
	}
}


static void paint_vertsel_circle_select(ViewContext *vc, int select, const int mval[2], float rad)
{
	Object *ob = vc->obact;
	Mesh *me = ob ? ob->data : NULL;
	/* int bbsel; */ /* UNUSED */
	/* CircleSelectUserData data = {NULL}; */ /* UNUSED */
	if (me) {
		bm_vertoffs = me->totvert + 1; /* max index array */

		/* bbsel= */ /* UNUSED */ EDBM_backbuf_circle_init(vc, mval[0], mval[1], (short)(rad + 1.0f));
		edbm_backbuf_check_and_select_verts_obmode(me, select == LEFTMOUSE);
		EDBM_backbuf_free();

		paintvert_flush_flags(ob);
	}
}


static void nurbscurve_circle_doSelect(void *userData, Nurb *UNUSED(nu), BPoint *bp, BezTriple *bezt, int beztindex, int x, int y)
{
	CircleSelectUserData *data = userData;
	Object *obedit = data->vc->obedit;
	Curve *cu = (Curve *)obedit->data;

	const float delta[2] = {(float)(x - data->mval[0]),
	                        (float)(y - data->mval[1])};

	if (len_squared_v2(delta) <= data->radius_squared) {
		if (bp) {
			bp->f1 = data->select ? (bp->f1 | SELECT) : (bp->f1 & ~SELECT);

			if (bp == cu->lastsel && !(bp->f1 & SELECT)) cu->lastsel = NULL;
		}
		else {
			if (cu->drawflag & CU_HIDE_HANDLES) {
				/* can only be (beztindex == 0) here since handles are hidden */
				bezt->f1 = bezt->f2 = bezt->f3 = data->select ? (bezt->f2 | SELECT) : (bezt->f2 & ~SELECT);
			}
			else {
				if (beztindex == 0) {
					bezt->f1 = data->select ? (bezt->f1 | SELECT) : (bezt->f1 & ~SELECT);
				}
				else if (beztindex == 1) {
					bezt->f2 = data->select ? (bezt->f2 | SELECT) : (bezt->f2 & ~SELECT);
				}
				else {
					bezt->f3 = data->select ? (bezt->f3 | SELECT) : (bezt->f3 & ~SELECT);
				}
			}

			if (bezt == cu->lastsel && !(bezt->f2 & SELECT)) cu->lastsel = NULL;
		}
	}
}
static void nurbscurve_circle_select(ViewContext *vc, int select, const int mval[2], float rad)
{
	CircleSelectUserData data;

	view3d_userdata_circleselect_init(&data, vc, select, mval, rad);

	ED_view3d_init_mats_rv3d(vc->obedit, vc->rv3d); /* for foreach's screen/vert projection */
	nurbs_foreachScreenVert(vc, nurbscurve_circle_doSelect, &data);
}


static void latticecurve_circle_doSelect(void *userData, BPoint *bp, int x, int y)
{
	CircleSelectUserData *data = userData;
	const float delta[2] = {(float)(x - data->mval[0]),
	                        (float)(y - data->mval[1])};

	if (len_squared_v2(delta) <= data->radius_squared) {
		bp->f1 = data->select ? (bp->f1 | SELECT) : (bp->f1 & ~SELECT);
	}
}
static void lattice_circle_select(ViewContext *vc, int select, const int mval[2], float rad)
{
	CircleSelectUserData data;

	view3d_userdata_circleselect_init(&data, vc, select, mval, rad);

	ED_view3d_init_mats_rv3d(vc->obedit, vc->rv3d); /* for foreach's screen/vert projection */
	lattice_foreachScreenVert(vc, latticecurve_circle_doSelect, &data);
}


/* NOTE: pose-bone case is copied from editbone case... */
static short pchan_circle_doSelectJoint(void *userData, bPoseChannel *pchan, int x, int y)
{
	CircleSelectUserData *data = userData;
	const float delta[2] = {(float)(x - data->mval[0]),
	                        (float)(y - data->mval[1])};

	if (len_squared_v2(delta) <= data->radius_squared) {
		if (data->select)
			pchan->bone->flag |= BONE_SELECTED;
		else
			pchan->bone->flag &= ~BONE_SELECTED;
		return 1;
	}
	return 0;
}
static void do_circle_select_pose__doSelectBone(void *userData, struct bPoseChannel *pchan, int x0, int y0, int x1, int y1)
{
	CircleSelectUserData *data = userData;
	bArmature *arm = data->vc->obact->data;

	if (PBONE_SELECTABLE(arm, pchan->bone)) {
		int is_point_done = FALSE;
		int points_proj_tot = 0;

		/* project head location to screenspace */
		if (x0 != IS_CLIPPED) {
			points_proj_tot++;
			if (pchan_circle_doSelectJoint(data, pchan, x0, y0)) {
				is_point_done = TRUE;
			}
		}

		/* project tail location to screenspace */
		if (x1 != IS_CLIPPED) {
			points_proj_tot++;
			if (pchan_circle_doSelectJoint(data, pchan, x1, y1)) {
				is_point_done = TRUE;
			}
		}

		/* check if the head and/or tail is in the circle
		 * - the call to check also does the selection already
		 */

		/* only if the endpoints didn't get selected, deal with the middle of the bone too
		 * It works nicer to only do this if the head or tail are not in the circle,
		 * otherwise there is no way to circle select joints alone */
		if ((is_point_done == FALSE) && (points_proj_tot == 2) &&
		    edge_inside_circle(data->mval[0], data->mval[1], data->radius, x0, y0, x1, y1))
		{
			if (data->select) pchan->bone->flag |= BONE_SELECTED;
			else              pchan->bone->flag &= ~BONE_SELECTED;
			data->is_change = TRUE;
		}

		data->is_change |= is_point_done;
	}
}
static void pose_circle_select(ViewContext *vc, int select, const int mval[2], float rad)
{
	CircleSelectUserData data;
	
	view3d_userdata_circleselect_init(&data, vc, select, mval, rad);

	ED_view3d_init_mats_rv3d(vc->obact, vc->rv3d); /* for foreach's screen/vert projection */
	
	pose_foreachScreenBone(vc, do_circle_select_pose__doSelectBone, &data);

	if (data.is_change) {
		bArmature *arm = vc->obact->data;

		WM_main_add_notifier(NC_OBJECT | ND_BONE_SELECT, vc->obact);

		if (arm->flag & ARM_HAS_VIZ_DEPS) {
			/* mask modifier ('armature' mode), etc. */
			DAG_id_tag_update(&vc->obact->id, OB_RECALC_DATA);
		}
	}
}

static short armature_circle_doSelectJoint(void *userData, EditBone *ebone, int x, int y, short head)
{
	CircleSelectUserData *data = userData;
	const float delta[2] = {(float)(x - data->mval[0]),
	                        (float)(y - data->mval[1])};
	
	if (len_squared_v2(delta) <= data->radius_squared) {
		if (head) {
			if (data->select)
				ebone->flag |= BONE_ROOTSEL;
			else 
				ebone->flag &= ~BONE_ROOTSEL;
		}
		else {
			if (data->select)
				ebone->flag |= BONE_TIPSEL;
			else 
				ebone->flag &= ~BONE_TIPSEL;
		}
		return 1;
	}
	return 0;
}
static void do_circle_select_armature__doSelectBone(void *userData, struct EditBone *ebone, int x0, int y0, int x1, int y1)
{
	CircleSelectUserData *data = userData;
	bArmature *arm = data->vc->obedit->data;

	if (EBONE_SELECTABLE(arm, ebone)) {
		int is_point_done = FALSE;
		int points_proj_tot = 0;

		/* project head location to screenspace */
		if (x0 != IS_CLIPPED) {
			points_proj_tot++;
			if (armature_circle_doSelectJoint(data, ebone, x0, y0, TRUE)) {
				is_point_done = TRUE;
			}
		}

		/* project tail location to screenspace */
		if (x1 != IS_CLIPPED) {
			points_proj_tot++;
			if (armature_circle_doSelectJoint(data, ebone, x1, y1, FALSE)) {
				is_point_done = TRUE;
			}
		}

		/* check if the head and/or tail is in the circle
		 * - the call to check also does the selection already
		 */

		/* only if the endpoints didn't get selected, deal with the middle of the bone too
		 * It works nicer to only do this if the head or tail are not in the circle,
		 * otherwise there is no way to circle select joints alone */
		if ((is_point_done == FALSE) && (points_proj_tot == 2) &&
		    edge_inside_circle(data->mval[0], data->mval[1], data->radius, x0, y0, x1, y1))
		{
			if (data->select) ebone->flag |=  (BONE_SELECTED | BONE_TIPSEL | BONE_ROOTSEL);
			else              ebone->flag &= ~(BONE_SELECTED | BONE_TIPSEL | BONE_ROOTSEL);
			data->is_change = TRUE;
		}

		data->is_change |= is_point_done;
	}
}
static void armature_circle_select(ViewContext *vc, int select, const int mval[2], float rad)
{
	CircleSelectUserData data;
	bArmature *arm = vc->obedit->data;

	view3d_userdata_circleselect_init(&data, vc, select, mval, rad);

	ED_view3d_init_mats_rv3d(vc->obedit, vc->rv3d);

	armature_foreachScreenBone(vc, do_circle_select_armature__doSelectBone, &data);

	if (data.is_change) {
		ED_armature_sync_selection(arm->edbo);
		ED_armature_validate_active(arm);
		WM_main_add_notifier(NC_OBJECT | ND_BONE_SELECT, vc->obedit);
	}
}

static void do_circle_select_mball__doSelectElem(void *userData, struct MetaElem *ml, int x, int y)
{
	CircleSelectUserData *data = userData;
	const float delta[2] = {(float)(x - data->mval[0]),
	                        (float)(y - data->mval[1])};

	if (len_squared_v2(delta) <= data->radius_squared) {
		if (data->select) ml->flag |=  SELECT;
		else              ml->flag &= ~SELECT;
		data->is_change = TRUE;
	}
}
static void mball_circle_select(ViewContext *vc, int select, const int mval[2], float rad)
{
	CircleSelectUserData data;

	view3d_userdata_circleselect_init(&data, vc, select, mval, rad);

	ED_view3d_init_mats_rv3d(vc->obedit, vc->rv3d);

	mball_foreachScreenElem(vc, do_circle_select_mball__doSelectElem, &data);
}

/** Callbacks for circle selection in Editmode */

static void obedit_circle_select(ViewContext *vc, short select, const int mval[2], float rad)
{
	switch (vc->obedit->type) {
		case OB_MESH:
			mesh_circle_select(vc, select, mval, rad);
			break;
		case OB_CURVE:
		case OB_SURF:
			nurbscurve_circle_select(vc, select, mval, rad);
			break;
		case OB_LATTICE:
			lattice_circle_select(vc, select, mval, rad);
			break;
		case OB_ARMATURE:
			armature_circle_select(vc, select, mval, rad);
			break;
		case OB_MBALL:
			mball_circle_select(vc, select, mval, rad);
			break;
		default:
			return;
	}
}

static int object_circle_select(ViewContext *vc, int select, const int mval[2], float rad)
{
	Scene *scene = vc->scene;
	const float radius_squared = rad * rad;
	const float mval_fl[2] = {mval[0], mval[1]};
	int is_change = FALSE;

	Base *base;
	select = select ? BA_SELECT : BA_DESELECT;
	for (base = FIRSTBASE; base; base = base->next) {
		if (((base->flag & SELECT) == 0) && BASE_SELECTABLE(vc->v3d, base)) {
			float screen_co[2];
			if (ED_view3d_project_float_global(vc->ar, base->object->obmat[3], screen_co,
			                                   V3D_PROJ_TEST_CLIP_BB | V3D_PROJ_TEST_CLIP_WIN) == V3D_PROJ_RET_OK)
			{
				if (len_squared_v2v2(mval_fl, screen_co) <= radius_squared) {
					ED_base_object_select(base, select);
					is_change = TRUE;
				}
			}
		}
	}

	return is_change;
}

/* not a real operator, only for circle test */
static int view3d_circle_select_exec(bContext *C, wmOperator *op)
{
	Scene *scene = CTX_data_scene(C);
	Object *obact = CTX_data_active_object(C);
	int radius = RNA_int_get(op->ptr, "radius");
	int gesture_mode = RNA_int_get(op->ptr, "gesture_mode");
	int select;
	const int mval[2] = {RNA_int_get(op->ptr, "x"),
	                     RNA_int_get(op->ptr, "y")};
	
	select = (gesture_mode == GESTURE_MODAL_SELECT);

	if (CTX_data_edit_object(C) || paint_facesel_test(obact) || paint_vertsel_test(obact) ||
	    (obact && (obact->mode & (OB_MODE_PARTICLE_EDIT | OB_MODE_POSE))) )
	{
		ViewContext vc;
		
		view3d_operator_needs_opengl(C);
		
		view3d_set_viewcontext(C, &vc);

		if (CTX_data_edit_object(C)) {
			obedit_circle_select(&vc, select, mval, (float)radius);
			WM_event_add_notifier(C, NC_GEOM | ND_SELECT, obact->data);
		}
		else if (paint_facesel_test(obact)) {
			paint_facesel_circle_select(&vc, select, mval, (float)radius);
			WM_event_add_notifier(C, NC_GEOM | ND_SELECT, obact->data);
		}
		else if (paint_vertsel_test(obact)) {
			paint_vertsel_circle_select(&vc, select, mval, (float)radius);
			WM_event_add_notifier(C, NC_GEOM | ND_SELECT, obact->data);
		}
		else if (obact->mode & OB_MODE_POSE)
			pose_circle_select(&vc, select, mval, (float)radius);
		else
			return PE_circle_select(C, select, mval, (float)radius);
	}
	else if (obact && obact->mode & OB_MODE_SCULPT) {
		return OPERATOR_CANCELLED;
	}
	else {
		ViewContext vc;
		view3d_set_viewcontext(C, &vc);

		if (object_circle_select(&vc, select, mval, (float)radius)) {
			WM_event_add_notifier(C, NC_SCENE | ND_OB_SELECT, scene);
		}
	}
	
	return OPERATOR_FINISHED;
}

void VIEW3D_OT_select_circle(wmOperatorType *ot)
{
	ot->name = "Circle Select";
	ot->description = "Select items using circle selection";
	ot->idname = "VIEW3D_OT_select_circle";
	
	ot->invoke = WM_gesture_circle_invoke;
	ot->modal = WM_gesture_circle_modal;
	ot->exec = view3d_circle_select_exec;
	ot->poll = view3d_selectable_data;
	ot->cancel = WM_gesture_circle_cancel;
	
	/* flags */
	ot->flag = OPTYPE_UNDO;
	
	RNA_def_int(ot->srna, "x", 0, INT_MIN, INT_MAX, "X", "", INT_MIN, INT_MAX);
	RNA_def_int(ot->srna, "y", 0, INT_MIN, INT_MAX, "Y", "", INT_MIN, INT_MAX);
	RNA_def_int(ot->srna, "radius", 0, INT_MIN, INT_MAX, "Radius", "", INT_MIN, INT_MAX);
	RNA_def_int(ot->srna, "gesture_mode", 0, INT_MIN, INT_MAX, "Event Type", "", INT_MIN, INT_MAX);
}

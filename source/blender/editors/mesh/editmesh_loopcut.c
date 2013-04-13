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
 * The Original Code is Copyright (C) 2007 Blender Foundation.
 * All rights reserved.
 *
 * 
 * Contributor(s): Joseph Eagar, Joshua Leung
 *
 * ***** END GPL LICENSE BLOCK *****
 */

/** \file blender/editors/mesh/editmesh_loopcut.c
 *  \ingroup edmesh
 */

#include "DNA_object_types.h"

#include "MEM_guardedalloc.h"

#include "BLI_array.h"
#include "BLI_string.h"
#include "BLI_math.h"

#include "BLF_translation.h"

#include "BKE_context.h"
#include "BKE_modifier.h"
#include "BKE_report.h"
#include "BKE_editmesh.h"

#include "BIF_gl.h"

#include "ED_screen.h"
#include "ED_space_api.h"
#include "ED_view3d.h"
#include "ED_mesh.h"
#include "ED_numinput.h"

#include "RNA_access.h"
#include "RNA_define.h"

#include "WM_api.h"
#include "WM_types.h"

#include "mesh_intern.h"  /* own include */


/* ringsel operator */

/* struct for properties used while drawing */
typedef struct RingSelOpData {
	ARegion *ar;        /* region that ringsel was activated in */
	void *draw_handle;  /* for drawing preview loop */
	
	float (*edges)[2][3];
	int totedge;

	ViewContext vc;

	Object *ob;
	BMEditMesh *em;
	BMEdge *eed;
	NumInput num;

	bool extend;
	bool do_cut;
} RingSelOpData;

/* modal loop selection drawing callback */
static void ringsel_draw(const bContext *C, ARegion *UNUSED(ar), void *arg)
{
	View3D *v3d = CTX_wm_view3d(C);
	RingSelOpData *lcd = arg;
	int i;
	
	if (lcd->totedge > 0) {
		if (v3d && v3d->zbuf)
			glDisable(GL_DEPTH_TEST);

		glPushMatrix();
		glMultMatrixf(lcd->ob->obmat);

		glColor3ub(255, 0, 255);
		glBegin(GL_LINES);
		for (i = 0; i < lcd->totedge; i++) {
			glVertex3fv(lcd->edges[i][0]);
			glVertex3fv(lcd->edges[i][1]);
		}
		glEnd();

		glPopMatrix();
		if (v3d && v3d->zbuf)
			glEnable(GL_DEPTH_TEST);
	}
}

/* given two opposite edges in a face, finds the ordering of their vertices so
 * that cut preview lines won't cross each other */
static void edgering_find_order(BMEdge *lasteed, BMEdge *eed,
                                BMVert *lastv1, BMVert *v[2][2])
{
	BMIter liter;
	BMLoop *l, *l2;
	int rev;

	l = eed->l;

	/* find correct order for v[1] */
	if (!(BM_edge_in_face(l->f, eed) && BM_edge_in_face(l->f, lasteed))) {
		BM_ITER_ELEM (l, &liter, l, BM_LOOPS_OF_LOOP) {
			if (BM_edge_in_face(l->f, eed) && BM_edge_in_face(l->f, lasteed))
				break;
		}
	}
	
	/* this should never happen */
	if (!l) {
		v[0][0] = eed->v1;
		v[0][1] = eed->v2;
		v[1][0] = lasteed->v1;
		v[1][1] = lasteed->v2;
		return;
	}
	
	l2 = BM_face_other_edge_loop(l->f, l->e, eed->v1);
	rev = (l2 == l->prev);
	while (l2->v != lasteed->v1 && l2->v != lasteed->v2) {
		l2 = rev ? l2->prev : l2->next;
	}

	if (l2->v == lastv1) {
		v[0][0] = eed->v1;
		v[0][1] = eed->v2;
	}
	else {
		v[0][0] = eed->v2;
		v[0][1] = eed->v1;
	}
}

static void edgering_sel(RingSelOpData *lcd, int previewlines, int select)
{
	BMEditMesh *em = lcd->em;
	BMEdge *eed_start = lcd->eed;
	BMEdge *eed, *eed_last;
	BMVert *v[2][2], *v_last;
	BMWalker walker;
	float (*edges)[2][3] = NULL;
	BLI_array_declare(edges);
	int i, tot = 0;
	
	memset(v, 0, sizeof(v));
	
	if (!eed_start)
		return;

	if (lcd->edges) {
		MEM_freeN(lcd->edges);
		lcd->edges = NULL;
		lcd->totedge = 0;
	}

	if (!lcd->extend) {
		EDBM_flag_disable_all(lcd->em, BM_ELEM_SELECT);
	}

	if (select) {
		BMW_init(&walker, em->bm, BMW_EDGERING,
		         BMW_MASK_NOP, BMW_MASK_NOP, BMW_MASK_NOP,
		         BMW_FLAG_TEST_HIDDEN,
		         BMW_NIL_LAY);

		for (eed = BMW_begin(&walker, eed_start); eed; eed = BMW_step(&walker)) {
			BM_edge_select_set(em->bm, eed, true);
		}
		BMW_end(&walker);

		return;
	}

	BMW_init(&walker, em->bm, BMW_EDGERING,
	         BMW_MASK_NOP, BMW_MASK_NOP, BMW_MASK_NOP,
	         BMW_FLAG_TEST_HIDDEN,
	         BMW_NIL_LAY);

	v_last   = NULL;
	eed_last = NULL;

	for (eed = eed_start = BMW_begin(&walker, eed_start); eed; eed = BMW_step(&walker)) {
		if (eed_last) {
			if (v_last) {
				v[1][0] = v[0][0];
				v[1][1] = v[0][1];
			}
			else {
				v[1][0] = eed_last->v1;
				v[1][1] = eed_last->v2;
				v_last  = eed_last->v1;
			}

			edgering_find_order(eed_last, eed, v_last, v);
			v_last = v[0][0];

			BLI_array_grow_items(edges, previewlines);

			for (i = 1; i <= previewlines; i++) {
				const float fac = (i / ((float)previewlines + 1));
				interp_v3_v3v3(edges[tot][0], v[0][0]->co, v[0][1]->co, fac);
				interp_v3_v3v3(edges[tot][1], v[1][0]->co, v[1][1]->co, fac);
				tot++;
			}
		}
		eed_last = eed;
	}
	
#ifdef BMW_EDGERING_NGON
	if (lasteed != startedge && BM_edge_share_face_check(lasteed, startedge)) {
#else
	if (eed_last != eed_start && BM_edge_share_quad_check(eed_last, eed_start)) {
#endif
		v[1][0] = v[0][0];
		v[1][1] = v[0][1];

		edgering_find_order(eed_last, eed_start, v_last, v);
		
		BLI_array_grow_items(edges, previewlines);

		for (i = 1; i <= previewlines; i++) {
			const float fac = (i / ((float)previewlines + 1));

			if (!v[0][0] || !v[0][1] || !v[1][0] || !v[1][1]) {
				continue;
			}

			interp_v3_v3v3(edges[tot][0], v[0][0]->co, v[0][1]->co, fac);
			interp_v3_v3v3(edges[tot][1], v[1][0]->co, v[1][1]->co, fac);
			tot++;
		}
	}

	BMW_end(&walker);
	lcd->edges = edges;
	lcd->totedge = tot;
}

static void ringsel_find_edge(RingSelOpData *lcd, int cuts)
{
	if (lcd->eed) {
		edgering_sel(lcd, cuts, 0);
	}
	else if (lcd->edges) {
		MEM_freeN(lcd->edges);
		lcd->edges = NULL;
		lcd->totedge = 0;
	}
}

static void ringsel_finish(bContext *C, wmOperator *op)
{
	RingSelOpData *lcd = op->customdata;
	const int cuts = RNA_int_get(op->ptr, "number_cuts");
	const float smoothness = 0.292f * RNA_float_get(op->ptr, "smoothness");
#ifdef BMW_EDGERING_NGON
	const bool use_only_quads = false;
#else
	const bool use_only_quads = false;
#endif

	if (lcd->eed) {
		BMEditMesh *em = lcd->em;

		edgering_sel(lcd, cuts, 1);
		
		if (lcd->do_cut) {
			/* Enable gridfill, so that intersecting loopcut works as one would expect.
			 * Note though that it will break edgeslide in this specific case.
			 * See [#31939]. */
			BM_mesh_esubdivide(em->bm, BM_ELEM_SELECT,
			                   smoothness, 0.0f, 0.0f,
			                   cuts,
			                   SUBDIV_SELECT_LOOPCUT, SUBD_PATH, 0, true,
			                   use_only_quads, 0);

			/* tessface is already re-recalculated */
			EDBM_update_generic(em, false, true);

			/* force edge slide to edge select mode in in face select mode */
			if (EDBM_selectmode_disable(lcd->vc.scene, em, SCE_SELECT_FACE, SCE_SELECT_EDGE)) {
				/* pass, the change will flush selection */
			}
			else {
				/* else flush explicitly */
				EDBM_selectmode_flush(lcd->em);
			}
		}
		else {
			/* XXX Is this piece of code ever used now? Simple loop select is now
			 *     in editmesh_select.c (around line 1000)... */
			/* sets as active, useful for other tools */
			if (em->selectmode & SCE_SELECT_VERTEX)
				BM_select_history_store(em->bm, lcd->eed->v1);  /* low priority TODO, get vertrex close to mouse */
			if (em->selectmode & SCE_SELECT_EDGE)
				BM_select_history_store(em->bm, lcd->eed);
			
			EDBM_selectmode_flush(lcd->em);
			WM_event_add_notifier(C, NC_GEOM | ND_SELECT, lcd->ob->data);
		}
	}
}

/* called when modal loop selection is done... */
static void ringsel_exit(bContext *UNUSED(C), wmOperator *op)
{
	RingSelOpData *lcd = op->customdata;

	/* deactivate the extra drawing stuff in 3D-View */
	ED_region_draw_cb_exit(lcd->ar->type, lcd->draw_handle);
	
	if (lcd->edges)
		MEM_freeN(lcd->edges);

	ED_region_tag_redraw(lcd->ar);

	/* free the custom data */
	MEM_freeN(lcd);
	op->customdata = NULL;
}


/* called when modal loop selection gets set up... */
static int ringsel_init(bContext *C, wmOperator *op, bool do_cut)
{
	RingSelOpData *lcd;

	/* alloc new customdata */
	lcd = op->customdata = MEM_callocN(sizeof(RingSelOpData), "ringsel Modal Op Data");
	
	/* assign the drawing handle for drawing preview line... */
	lcd->ar = CTX_wm_region(C);
	lcd->draw_handle = ED_region_draw_cb_activate(lcd->ar->type, ringsel_draw, lcd, REGION_DRAW_POST_VIEW);
	lcd->ob = CTX_data_edit_object(C);
	lcd->em = BMEdit_FromObject(lcd->ob);
	lcd->extend = do_cut ? 0 : RNA_boolean_get(op->ptr, "extend");
	lcd->do_cut = do_cut;
	
	initNumInput(&lcd->num);
	lcd->num.idx_max = 0;
	lcd->num.flag |= NUM_NO_NEGATIVE | NUM_NO_FRACTION;

	/* XXX, temp, workaround for [#	] */
	EDBM_mesh_ensure_valid_dm_hack(CTX_data_scene(C), lcd->em);

	em_setup_viewcontext(C, &lcd->vc);

	ED_region_tag_redraw(lcd->ar);

	return 1;
}

static int ringcut_cancel(bContext *C, wmOperator *op)
{
	/* this is just a wrapper around exit() */
	ringsel_exit(C, op);
	return OPERATOR_CANCELLED;
}

static int ringcut_invoke(bContext *C, wmOperator *op, const wmEvent *event)
{
	ScrArea *sa = CTX_wm_area(C);
	Object *obedit = CTX_data_edit_object(C);
	RingSelOpData *lcd;
	BMEdge *edge;
	float dist = 75.0f;

	if (modifiers_isDeformedByLattice(obedit) || modifiers_isDeformedByArmature(obedit))
		BKE_report(op->reports, RPT_WARNING, "Loop cut does not work well on deformed edit mesh display");
	
	view3d_operator_needs_opengl(C);

	if (!ringsel_init(C, op, 1))
		return OPERATOR_CANCELLED;
	
	/* add a modal handler for this operator - handles loop selection */
	WM_event_add_modal_handler(C, op);

	lcd = op->customdata;
	copy_v2_v2_int(lcd->vc.mval, event->mval);
	
	edge = EDBM_edge_find_nearest(&lcd->vc, &dist);
	if (edge != lcd->eed) {
		lcd->eed = edge;
		ringsel_find_edge(lcd, 1);
	}
	ED_area_headerprint(sa, IFACE_("Select a ring to be cut, use mouse-wheel or page-up/down for number of cuts, "
	                               "hold Alt for smooth"));
	
	return OPERATOR_RUNNING_MODAL;
}

static int loopcut_modal(bContext *C, wmOperator *op, const wmEvent *event)
{
	float smoothness = RNA_float_get(op->ptr, "smoothness");
	int cuts = RNA_int_get(op->ptr, "number_cuts");
	RingSelOpData *lcd = op->customdata;
	bool show_cuts = false;

	view3d_operator_needs_opengl(C);

	switch (event->type) {
		case RETKEY:
		case PADENTER:
		case LEFTMOUSE: /* confirm */ // XXX hardcoded
			if (event->val == KM_PRESS) {
				/* finish */
				ED_region_tag_redraw(lcd->ar);
				
				ringsel_finish(C, op);
				ringsel_exit(C, op);
				
				ED_area_headerprint(CTX_wm_area(C), NULL);
				
				return OPERATOR_FINISHED;
			}
			
			ED_region_tag_redraw(lcd->ar);
			break;
		case RIGHTMOUSE: /* abort */ // XXX hardcoded
			ED_region_tag_redraw(lcd->ar);
			ringsel_exit(C, op);
			ED_area_headerprint(CTX_wm_area(C), NULL);

			return OPERATOR_FINISHED;
		case ESCKEY:
			if (event->val == KM_RELEASE) {
				/* cancel */
				ED_region_tag_redraw(lcd->ar);
				ED_area_headerprint(CTX_wm_area(C), NULL);
				
				return ringcut_cancel(C, op);
			}
			
			ED_region_tag_redraw(lcd->ar);
			break;
		case PADPLUSKEY:
		case PAGEUPKEY:
		case WHEELUPMOUSE:  /* change number of cuts */
			if (event->val == KM_RELEASE)
				break;
			if (event->alt == 0) {
				cuts++;
				RNA_int_set(op->ptr, "number_cuts", cuts);
				ringsel_find_edge(lcd, cuts);
				show_cuts = true;
			}
			else {
				smoothness = min_ff(smoothness + 0.05f, 4.0f);
				RNA_float_set(op->ptr, "smoothness", smoothness);
				show_cuts = true;
			}
			
			ED_region_tag_redraw(lcd->ar);
			break;
		case PADMINUS:
		case PAGEDOWNKEY:
		case WHEELDOWNMOUSE:  /* change number of cuts */
			if (event->val == KM_RELEASE)
				break;

			if (event->alt == 0) {
				cuts = max_ii(cuts - 1, 0);
				RNA_int_set(op->ptr, "number_cuts", cuts);
				ringsel_find_edge(lcd, cuts);
				show_cuts = true;
			}
			else {
				smoothness = max_ff(smoothness - 0.05f, 0.0f);
				RNA_float_set(op->ptr, "smoothness", smoothness);
				show_cuts = true;
			}
			
			ED_region_tag_redraw(lcd->ar);
			break;
		case MOUSEMOVE:  /* mouse moved somewhere to select another loop */
		{
			float dist = 75.0f;
			BMEdge *edge;

			lcd->vc.mval[0] = event->mval[0];
			lcd->vc.mval[1] = event->mval[1];
			edge = EDBM_edge_find_nearest(&lcd->vc, &dist);

			if (edge != lcd->eed) {
				lcd->eed = edge;
				ringsel_find_edge(lcd, cuts);
			}

			ED_region_tag_redraw(lcd->ar);
			break;
		}
	}
	
	/* using the keyboard to input the number of cuts */
	if (event->val == KM_PRESS) {
		/* init as zero so backspace clears */
		
		if (handleNumInput(&lcd->num, event)) {
			float value = RNA_int_get(op->ptr, "number_cuts");
			applyNumInput(&lcd->num, &value);
			
			/* allow zero so you can backspace and type in a value
			 * otherwise 1 as minimum would make more sense */
			cuts = CLAMPIS(value, 0, 130);
			
			RNA_int_set(op->ptr, "number_cuts", cuts);
			ringsel_find_edge(lcd, cuts);
			show_cuts = true;
			
			ED_region_tag_redraw(lcd->ar);
		}
	}
	
	if (show_cuts) {
		char buf[64];
		BLI_snprintf(buf, sizeof(buf), IFACE_("Number of Cuts: %d, Smooth: %.2f (Alt)"), cuts, smoothness);
		ED_area_headerprint(CTX_wm_area(C), buf);
	}
	
	/* keep going until the user confirms */
	return OPERATOR_RUNNING_MODAL;
}

/* for bmesh this tool is in bmesh_select.c */
#if 0

void MESH_OT_edgering_select(wmOperatorType *ot)
{
	/* description */
	ot->name = "Edge Ring Select";
	ot->idname = "MESH_OT_edgering_select";
	ot->description = "Select an edge ring";
	
	/* callbacks */
	ot->invoke = ringsel_invoke;
	ot->poll = ED_operator_editmesh_region_view3d; 
	
	/* flags */
	ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;

	RNA_def_boolean(ot->srna, "extend", 0, "Extend", "Extend the selection");
}

#endif

void MESH_OT_loopcut(wmOperatorType *ot)
{
	PropertyRNA *prop;

	/* description */
	ot->name = "Loop Cut";
	ot->idname = "MESH_OT_loopcut";
	ot->description = "Add a new loop between existing loops";
	
	/* callbacks */
	ot->invoke = ringcut_invoke;
	ot->modal = loopcut_modal;
	ot->cancel = ringcut_cancel;
	ot->poll = ED_operator_editmesh_region_view3d;
	
	/* flags */
	ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO | OPTYPE_BLOCKING;

	/* properties */
	prop = RNA_def_int(ot->srna, "number_cuts", 1, 1, INT_MAX, "Number of Cuts", "", 1, 10);
	/* avoid re-using last var because it can cause _very_ high poly meshes and annoy users (or worse crash) */
	RNA_def_property_flag(prop, PROP_SKIP_SAVE);

	prop = RNA_def_float(ot->srna, "smoothness", 0.0f, 0.0f, FLT_MAX, "Smoothness", "Smoothness factor", 0.0f, 4.0f);
	RNA_def_property_flag(prop, PROP_SKIP_SAVE);
}

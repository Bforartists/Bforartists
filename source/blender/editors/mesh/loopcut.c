/**
 * $Id:
 *
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
 * Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
 *
 * The Original Code is Copyright (C) 2007 Blender Foundation.
 * All rights reserved.
 *
 * 
 * Contributor(s): Joseph Eagar, Joshua Leung
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#include <float.h>
#define _USE_MATH_DEFINES
#include <math.h>
#include <string.h>
#include <ctype.h>
#include <stdio.h>

#include "DNA_ID.h"
#include "DNA_screen_types.h"
#include "DNA_scene_types.h"
#include "DNA_userdef_types.h"
#include "DNA_windowmanager_types.h"
#include "DNA_object_types.h"

#include "MEM_guardedalloc.h"

#include "PIL_time.h"

#include "BLI_blenlib.h"
#include "BLI_dynstr.h" /*for WM_operator_pystring */
#include "BLI_editVert.h"
#include "BLI_array.h"

#include "BKE_blender.h"
#include "BKE_context.h"
#include "BKE_depsgraph.h"
#include "BKE_scene.h"
#include "BKE_utildefines.h"
#include "BKE_mesh.h"
#include "BKE_tessmesh.h"
#include "BKE_depsgraph.h"

#include "BIF_gl.h"
#include "BIF_glutil.h" /* for paint cursor */

#include "IMB_imbuf_types.h"

#include "ED_screen.h"
#include "ED_util.h"
#include "ED_space_api.h"
#include "ED_view3d.h"
#include "ED_mesh.h"

#include "RNA_access.h"
#include "RNA_define.h"

#include "UI_interface.h"
#include "UI_resources.h"

#include "WM_api.h"
#include "WM_types.h"

#include "mesh_intern.h"

/* ringsel operator */

/* struct for properties used while drawing */
typedef struct tringselOpData {
	ARegion *ar;		/* region that ringsel was activated in */
	void *draw_handle;	/* for drawing preview loop */
	
	float (*edges)[2][3];
	int totedge;

	ViewContext vc;

	Object *ob;
	BMEditMesh *em;
	BMEdge *eed;

	int extend;
	int do_cut;
} tringselOpData;

/* modal loop selection drawing callback */
static void ringsel_draw(const bContext *C, ARegion *ar, void *arg)
{
	int i;
	tringselOpData *lcd = arg;
	
	glDisable(GL_DEPTH_TEST);

	glPushMatrix();
	glMultMatrixf(lcd->ob->obmat);

	glColor3ub(255, 0, 255);
	glBegin(GL_LINES);
	for (i=0; i<lcd->totedge; i++) {
		glVertex3fv(lcd->edges[i][0]);
		glVertex3fv(lcd->edges[i][1]);
	}
	glEnd();

	glPopMatrix();
	glEnable(GL_DEPTH_TEST);
}

/*given two opposite edges in a face, finds the ordering of their vertices so
  that cut preview lines won't cross each other*/
static void edgering_find_order(BMEditMesh *em, BMEdge *lasteed, BMEdge *eed, 
                                BMVert *lastv1, BMVert *v[2][2])
{
	BMIter iter, liter;
	BMLoop *l, *l2;
	int rev;

	l = eed->loop;

	/*find correct order for v[1]*/
	if (!(BM_Edge_In_Face(l->f, eed) && BM_Edge_In_Face(l->f, lasteed))) {
		BM_ITER(l, &liter, em->bm, BM_LOOPS_OF_LOOP, l) {
			if (BM_Edge_In_Face(l->f, eed) && BM_Edge_In_Face(l->f, lasteed))
				break;
		}
	}
	
	/*this should never happen*/
	if (!l) {
		v[0][0] = eed->v1;
		v[0][1] = eed->v2;
		v[1][0] = lasteed->v1;
		v[1][1] = lasteed->v2;
		return;
	}
	
	l2 = BM_OtherFaceLoop(l->e, l->f, eed->v1);
	rev = (l2 == (BMLoop*)l->head.prev);
	while (l2->v != lasteed->v1 && l2->v != lasteed->v2) {
		l2 = rev ? (BMLoop*)l2->head.prev : (BMLoop*)l2->head.next;
	}

	if (l2->v == lastv1) {
		v[0][0] = eed->v1;
		v[0][1] = eed->v2;
	} else {
		v[0][0] = eed->v2;
		v[0][1] = eed->v1;
	}
}

static void edgering_sel(tringselOpData *lcd, int previewlines, int select)
{
	BMEditMesh *em = lcd->em;
	BMEdge *startedge = lcd->eed;
	BMEdge *eed, *lasteed;
	BMVert *v[2][2], *lastv1;
	BMWalker walker;
	float (*edges)[2][3] = NULL;
	BLI_array_declare(edges);
	float co[2][3];
	int looking=1, i, tot=0;
	
	if (!startedge)
		return;

	if (lcd->edges) {
		MEM_freeN(lcd->edges);
		lcd->edges = NULL;
		lcd->totedge = 0;
	}

	if (!lcd->extend) {
		EDBM_clear_flag_all(lcd->em, BM_SELECT);
	}

	if (select) {
		BMW_Init(&walker, em->bm, BMW_EDGERING, 0, 0);
		eed = BMW_Begin(&walker, startedge);
		for (; eed; eed=BMW_Step(&walker)) {
			BM_Select(em->bm, eed, 1);
		}
		BMW_End(&walker);

		return;
	}

	BMW_Init(&walker, em->bm, BMW_EDGERING, 0, 0);
	eed = startedge = BMW_Begin(&walker, startedge);
	lastv1 = NULL;
	for (lasteed=NULL; eed; eed=BMW_Step(&walker)) {
		if (lasteed) {
			BMIter liter;
			BMLoop *l, *l2;
			int rev;

			if (lastv1) {
				v[1][0] = v[0][0];
				v[1][1] = v[0][1];
			} else {
				v[1][0] = lasteed->v1;
				v[1][1] = lasteed->v2;
				lastv1 = lasteed->v1;
			}

			edgering_find_order(em, lasteed, eed, lastv1, v);
			lastv1 = v[0][0];

			for(i=1;i<=previewlines;i++){
				co[0][0] = (v[0][1]->co[0] - v[0][0]->co[0])*(i/((float)previewlines+1))+v[0][0]->co[0];
				co[0][1] = (v[0][1]->co[1] - v[0][0]->co[1])*(i/((float)previewlines+1))+v[0][0]->co[1];
				co[0][2] = (v[0][1]->co[2] - v[0][0]->co[2])*(i/((float)previewlines+1))+v[0][0]->co[2];

				co[1][0] = (v[1][1]->co[0] - v[1][0]->co[0])*(i/((float)previewlines+1))+v[1][0]->co[0];
				co[1][1] = (v[1][1]->co[1] - v[1][0]->co[1])*(i/((float)previewlines+1))+v[1][0]->co[1];
				co[1][2] = (v[1][1]->co[2] - v[1][0]->co[2])*(i/((float)previewlines+1))+v[1][0]->co[2];					
				
				BLI_array_growone(edges);
				VECCOPY(edges[tot][0], co[0]);
				VECCOPY(edges[tot][1], co[1]);
				tot++;
			}
		}
		lasteed = eed;
	}
	
	if (BM_Edge_Share_Faces(lasteed, startedge)) {
		edgering_find_order(em, lasteed, startedge, lastv1, v);

		for(i=1;i<=previewlines;i++){
			co[0][0] = (v[0][1]->co[0] - v[0][0]->co[0])*(i/((float)previewlines+1))+v[0][0]->co[0];
			co[0][1] = (v[0][1]->co[1] - v[0][0]->co[1])*(i/((float)previewlines+1))+v[0][0]->co[1];
			co[0][2] = (v[0][1]->co[2] - v[0][0]->co[2])*(i/((float)previewlines+1))+v[0][0]->co[2];

			co[1][0] = (v[1][1]->co[0] - v[1][0]->co[0])*(i/((float)previewlines+1))+v[1][0]->co[0];
			co[1][1] = (v[1][1]->co[1] - v[1][0]->co[1])*(i/((float)previewlines+1))+v[1][0]->co[1];
			co[1][2] = (v[1][1]->co[2] - v[1][0]->co[2])*(i/((float)previewlines+1))+v[1][0]->co[2];					
			
			BLI_array_growone(edges);
			VECCOPY(edges[tot][0], co[0]);
			VECCOPY(edges[tot][1], co[1]);
			tot++;
		}
	}

	BMW_End(&walker);
	lcd->edges = edges;
	lcd->totedge = tot;
}

static void ringsel_find_edge(tringselOpData *lcd, const bContext *C, ARegion *ar, int cuts)
{
	if (lcd->eed)
		edgering_sel(lcd, cuts, 0);
}

static void ringsel_finish(bContext *C, wmOperator *op)
{
	tringselOpData *lcd= op->customdata;
	int cuts= RNA_int_get(op->ptr,"number_cuts");

	if (lcd->eed) {
		edgering_sel(lcd, cuts, 1);
		if (lcd->do_cut) {
			BMEditMesh *em = lcd->em;
			BM_esubdivideflag(lcd->ob, em->bm, BM_SELECT, 0.0f, 
			                  0.0f, 0, cuts, SUBDIV_SELECT_LOOPCUT, 
			                  SUBD_PATH, 0, 0);

			WM_event_add_notifier(C, NC_GEOM|ND_SELECT|ND_DATA, lcd->ob->data);
			DAG_id_flush_update(lcd->ob->data, OB_RECALC_DATA);
		}
		WM_event_add_notifier(C, NC_GEOM|ND_DATA, lcd->ob->data);
	}
}

/* called when modal loop selection is done... */
static void ringsel_exit (bContext *C, wmOperator *op)
{
	tringselOpData *lcd= op->customdata;

	/* deactivate the extra drawing stuff in 3D-View */
	ED_region_draw_cb_exit(lcd->ar->type, lcd->draw_handle);
	
	if (lcd->edges)
		MEM_freeN(lcd->edges);

	ED_region_tag_redraw(lcd->ar);

	/* free the custom data */
	MEM_freeN(lcd);
	op->customdata= NULL;
}

/* called when modal loop selection gets set up... */
static int ringsel_init (bContext *C, wmOperator *op, int do_cut)
{
	tringselOpData *lcd;
	
	/* alloc new customdata */
	lcd= op->customdata= MEM_callocN(sizeof(tringselOpData), "ringsel Modal Op Data");
	
	/* assign the drawing handle for drawing preview line... */
	lcd->ar= CTX_wm_region(C);
	lcd->draw_handle= ED_region_draw_cb_activate(lcd->ar->type, ringsel_draw, lcd, REGION_DRAW_POST_VIEW);
	lcd->ob = CTX_data_edit_object(C);
	lcd->em= ((Mesh *)lcd->ob->data)->edit_btmesh;
	lcd->extend = do_cut ? 0 : RNA_boolean_get(op->ptr, "extend");
	lcd->do_cut = do_cut;
	em_setup_viewcontext(C, &lcd->vc);

	ED_region_tag_redraw(lcd->ar);

	return 1;
}

static int ringsel_cancel (bContext *C, wmOperator *op)
{
	/* this is just a wrapper around exit() */
	ringsel_exit(C, op);
	return OPERATOR_CANCELLED;
}

static int ringsel_invoke (bContext *C, wmOperator *op, wmEvent *evt)
{
	tringselOpData *lcd;
	BMEdge *edge;
	int dist = 75;

	view3d_operator_needs_opengl(C);

	if (!ringsel_init(C, op, 0))
		return OPERATOR_CANCELLED;
	
	/* add a modal handler for this operator - handles loop selection */
	WM_event_add_modal_handler(C, op);

	lcd = op->customdata;
	lcd->vc.mval[0] = evt->mval[0];
	lcd->vc.mval[1] = evt->mval[1];
	
	edge = EDBM_findnearestedge(&lcd->vc, &dist);
	if (edge != lcd->eed) {
		lcd->eed = edge;
		ringsel_find_edge(lcd, C, lcd->ar, 1);
	}

	return OPERATOR_RUNNING_MODAL;
}


static int ringcut_invoke (bContext *C, wmOperator *op, wmEvent *evt)
{
	tringselOpData *lcd;
	BMEdge *edge;
	int dist = 75;

	view3d_operator_needs_opengl(C);

	if (!ringsel_init(C, op, 1))
		return OPERATOR_CANCELLED;
	
	/* add a modal handler for this operator - handles loop selection */
	WM_event_add_modal_handler(C, op);

	lcd = op->customdata;
	lcd->vc.mval[0] = evt->mval[0];
	lcd->vc.mval[1] = evt->mval[1];
	
	edge = EDBM_findnearestedge(&lcd->vc, &dist);
	if (edge != lcd->eed) {
		lcd->eed = edge;
		ringsel_find_edge(lcd, C, lcd->ar, 1);
	}

	return OPERATOR_RUNNING_MODAL;
}

static int ringsel_modal (bContext *C, wmOperator *op, wmEvent *event)
{
	int cuts= RNA_int_get(op->ptr,"number_cuts");
	tringselOpData *lcd= op->customdata;

	view3d_operator_needs_opengl(C);


	switch (event->type) {
		case LEFTMOUSE: /* abort */ // XXX hardcoded
			ED_region_tag_redraw(lcd->ar);
			ringsel_exit(C, op);

			return OPERATOR_FINISHED;
		case RIGHTMOUSE: /* confirm */ // XXX hardcoded
			if (event->val == KM_RELEASE) {
				/* finish */
				ED_region_tag_redraw(lcd->ar);
				
				ringsel_finish(C, op);
				ringsel_exit(C, op);
				
				return OPERATOR_FINISHED;
			}
			
			ED_region_tag_redraw(lcd->ar);
			break;
		case ESCKEY:
			if (event->val == KM_RELEASE) {
				/* cancel */
				ED_region_tag_redraw(lcd->ar);
				
				return ringsel_cancel(C, op);
			}
			
			ED_region_tag_redraw(lcd->ar);
			break;
		case MOUSEMOVE: { /* mouse moved somewhere to select another loop */
			int dist = 75;
			BMEdge *edge;

			lcd->vc.mval[0] = event->mval[0];
			lcd->vc.mval[1] = event->mval[1];
			edge = EDBM_findnearestedge(&lcd->vc, &dist);

			if (edge != lcd->eed) {
				lcd->eed = edge;
				ringsel_find_edge(lcd, C, lcd->ar, cuts);
			}

			ED_region_tag_redraw(lcd->ar);
			break;
		}			
	}
	
	/* keep going until the user confirms */
	return OPERATOR_RUNNING_MODAL;
}

static int loopcut_modal (bContext *C, wmOperator *op, wmEvent *event)
{
	int cuts= RNA_int_get(op->ptr,"number_cuts");
	tringselOpData *lcd= op->customdata;

	view3d_operator_needs_opengl(C);


	switch (event->type) {
		case LEFTMOUSE: /* confirm */ // XXX hardcoded
			if (event->val == KM_RELEASE) {
				/* finish */
				ED_region_tag_redraw(lcd->ar);
				
				ringsel_finish(C, op);
				ringsel_exit(C, op);
				
				return OPERATOR_FINISHED;
			}
			
			ED_region_tag_redraw(lcd->ar);
			break;
		case RIGHTMOUSE: /* abort */ // XXX hardcoded
			ED_region_tag_redraw(lcd->ar);
			ringsel_exit(C, op);

			return OPERATOR_FINISHED;
		case ESCKEY:
			if (event->val == KM_RELEASE) {
				/* cancel */
				ED_region_tag_redraw(lcd->ar);
				
				return ringsel_cancel(C, op);
			}
			
			ED_region_tag_redraw(lcd->ar);
			break;
		case PAGEUPKEY:
		case WHEELUPMOUSE:  /* change number of cuts */
			if (event->val == KM_RELEASE)
				break;

			cuts++;
			RNA_int_set(op->ptr,"number_cuts",cuts);
			ringsel_find_edge(lcd, C, lcd->ar, cuts);
			
			ED_region_tag_redraw(lcd->ar);
			break;
		case PAGEDOWNKEY:
		case WHEELDOWNMOUSE:  /* change number of cuts */
			if (event->val == KM_RELEASE)
				break;

			cuts=MAX2(cuts-1,1);
			RNA_int_set(op->ptr,"number_cuts",cuts);
			ringsel_find_edge(lcd, C, lcd->ar,cuts);
			
			ED_region_tag_redraw(lcd->ar);
			break;
		case MOUSEMOVE: { /* mouse moved somewhere to select another loop */
			int dist = 75;
			BMEdge *edge;

			lcd->vc.mval[0] = event->mval[0];
			lcd->vc.mval[1] = event->mval[1];
			edge = EDBM_findnearestedge(&lcd->vc, &dist);

			if (edge != lcd->eed) {
				lcd->eed = edge;
				ringsel_find_edge(lcd, C, lcd->ar, cuts);
			}

			ED_region_tag_redraw(lcd->ar);
			break;
		}			
	}
	
	/* keep going until the user confirms */
	return OPERATOR_RUNNING_MODAL;
}

void MESH_OT_edgering_select (wmOperatorType *ot)
{
	/* description */
	ot->name= "Edge Ring Select";
	ot->idname= "MESH_OT_edgering_select";
	ot->description= "Select an edge ring";
	
	/* callbacks */
	ot->invoke= ringsel_invoke;
	ot->modal= ringsel_modal;
	ot->cancel= ringsel_cancel;
	ot->poll= ED_operator_editmesh_view3d;
	
	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO|OPTYPE_BLOCKING;

	RNA_def_boolean(ot->srna, "extend", 0, "Extend", "Extend the selection");
}

void MESH_OT_loopcut (wmOperatorType *ot)
{
	/* description */
	ot->name= "Loop Cut";
	ot->idname= "MESH_OT_loopcut";
	ot->description= "Add a new loop between existing loops.";
	
	/* callbacks */
	ot->invoke= ringcut_invoke;
	ot->modal= loopcut_modal;
	ot->cancel= ringsel_cancel;
	ot->poll= ED_operator_editmesh_view3d;
	
	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO|OPTYPE_BLOCKING;

	/* properties */
	RNA_def_int(ot->srna, "number_cuts", 1, 1, INT_MAX, "Number of Cuts", "", 1, 10);
}

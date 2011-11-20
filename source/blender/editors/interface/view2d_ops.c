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
 * Contributor(s): Blender Foundation, Joshua Leung
 *
 * ***** END GPL LICENSE BLOCK *****
 */

/** \file blender/editors/interface/view2d_ops.c
 *  \ingroup edinterface
 */


#include <math.h>

#include "MEM_guardedalloc.h"

#include "DNA_userdef_types.h"

#include "BLI_blenlib.h"
#include "BLI_utildefines.h"

#include "BKE_context.h"

#include "RNA_access.h"
#include "RNA_define.h"

#include "WM_api.h"
#include "WM_types.h"


#include "ED_screen.h"

#include "UI_view2d.h"
#include "UI_interface.h"

#include "PIL_time.h" /* USER_ZOOM_CONT */

static int view2d_poll(bContext *C)
{
	ARegion *ar= CTX_wm_region(C);

	return (ar != NULL) && (ar->v2d.flag & V2D_IS_INITIALISED);
}

/* ********************************************************* */
/* VIEW PANNING OPERATOR								 */

/* 	This group of operators come in several forms:
 *		1) Modal 'dragging' with MMB - where movement of mouse dictates amount to pan view by
 *		2) Scrollwheel 'steps' - rolling mousewheel by one step moves view by predefined amount
 *
 *	In order to make sure this works, each operator must define the following RNA-Operator Props:
 *		deltax, deltay 	- define how much to move view by (relative to zoom-correction factor)
 */

/* ------------------ Shared 'core' stuff ---------------------- */
 
/* temp customdata for operator */
typedef struct v2dViewPanData {
	bScreen *sc;			/* screen where view pan was initiated */
	ScrArea *sa;			/* area where view pan was initiated */
	ARegion *ar;			/* region where view pan was initiated */
	View2D *v2d;			/* view2d we're operating in */
	
	float facx, facy;		/* amount to move view relative to zoom */
	
		/* options for version 1 */
	int startx, starty;		/* mouse x/y values in window when operator was initiated */
	int lastx, lasty;		/* previous x/y values of mouse in window */
	int invoke_event;		/* event starting pan, for modal exit */
	
	short in_scroller;		/* for MMB in scrollers (old feature in past, but now not that useful) */
} v2dViewPanData;
 
/* initialise panning customdata */
static int view_pan_init(bContext *C, wmOperator *op)
{
	ARegion *ar= CTX_wm_region(C);
	v2dViewPanData *vpd;
	View2D *v2d;
	float winx, winy;
	
	/* regions now have v2d-data by default, so check for region */
	if (ar == NULL)
		return 0;
		
	/* check if panning is allowed at all */
	v2d= &ar->v2d;
	if ((v2d->keepofs & V2D_LOCKOFS_X) && (v2d->keepofs & V2D_LOCKOFS_Y))
		return 0;
	
	/* set custom-data for operator */
	vpd= MEM_callocN(sizeof(v2dViewPanData), "v2dViewPanData");
	op->customdata= vpd;
	
	/* set pointers to owners */
	vpd->sc= CTX_wm_screen(C);
	vpd->sa= CTX_wm_area(C);
	vpd->v2d= v2d;
	vpd->ar = ar;
	
	/* calculate translation factor - based on size of view */
	winx= (float)(ar->winrct.xmax - ar->winrct.xmin + 1);
	winy= (float)(ar->winrct.ymax - ar->winrct.ymin + 1);
	vpd->facx= (v2d->cur.xmax - v2d->cur.xmin) / winx;
	vpd->facy= (v2d->cur.ymax - v2d->cur.ymin) / winy;
	
	return 1;
}

/* apply transform to view (i.e. adjust 'cur' rect) */
static void view_pan_apply(wmOperator *op)
{
	v2dViewPanData *vpd= op->customdata;
	View2D *v2d= vpd->v2d;
	float dx, dy;
	
	/* calculate amount to move view by */
	dx= vpd->facx * (float)RNA_int_get(op->ptr, "deltax");
	dy= vpd->facy * (float)RNA_int_get(op->ptr, "deltay");
	
	/* only move view on an axis if change is allowed */
	if ((v2d->keepofs & V2D_LOCKOFS_X)==0) {
		v2d->cur.xmin += dx;
		v2d->cur.xmax += dx;
	}
	if ((v2d->keepofs & V2D_LOCKOFS_Y)==0) {
		v2d->cur.ymin += dy;
		v2d->cur.ymax += dy;
	}
	
	/* validate that view is in valid configuration after this operation */
	UI_view2d_curRect_validate(v2d);
	
	/* request updates to be done... */
	ED_region_tag_redraw(vpd->ar);
	
	UI_view2d_sync(vpd->sc, vpd->sa, v2d, V2D_LOCK_COPY);
	
	/* exceptions */
	if (vpd->sa->spacetype==SPACE_OUTLINER) {
		/* don't rebuild full tree, since we're just changing our view */
		SpaceOops *soops= vpd->sa->spacedata.first;
		soops->storeflag |= SO_TREESTORE_REDRAW;
	}
}

/* cleanup temp customdata  */
static void view_pan_exit(wmOperator *op)
{
	if (op->customdata) {
		MEM_freeN(op->customdata);
		op->customdata= NULL;				
	}
} 
 
/* ------------------ Modal Drag Version (1) ---------------------- */

/* for 'redo' only, with no user input */
static int view_pan_exec(bContext *C, wmOperator *op)
{
	if (!view_pan_init(C, op))
		return OPERATOR_CANCELLED;
	
	view_pan_apply(op);
	view_pan_exit(op);
	return OPERATOR_FINISHED;
}

/* set up modal operator and relevant settings */
static int view_pan_invoke(bContext *C, wmOperator *op, wmEvent *event)
{
	wmWindow *window= CTX_wm_window(C);
	v2dViewPanData *vpd;
	View2D *v2d;
	
	/* set up customdata */
	if (!view_pan_init(C, op))
		return OPERATOR_PASS_THROUGH;
	
	vpd= op->customdata;
	v2d= vpd->v2d;
	
	/* set initial settings */
	vpd->startx= vpd->lastx= event->x;
	vpd->starty= vpd->lasty= event->y;
	vpd->invoke_event= event->type;
	
	if (event->type == MOUSEPAN) {
		RNA_int_set(op->ptr, "deltax", event->prevx - event->x);
		RNA_int_set(op->ptr, "deltay", event->prevy - event->y);
		
		view_pan_apply(op);
		view_pan_exit(op);
		return OPERATOR_FINISHED;
	}
	
	RNA_int_set(op->ptr, "deltax", 0);
	RNA_int_set(op->ptr, "deltay", 0);
	
	if (v2d->keepofs & V2D_LOCKOFS_X)
		WM_cursor_modal(window, BC_NS_SCROLLCURSOR);
	else if (v2d->keepofs & V2D_LOCKOFS_Y)
		WM_cursor_modal(window, BC_EW_SCROLLCURSOR);
	else
		WM_cursor_modal(window, BC_NSEW_SCROLLCURSOR);
	
	/* add temp handler */
	WM_event_add_modal_handler(C, op);

	return OPERATOR_RUNNING_MODAL;
}

/* handle user input - calculations of mouse-movement need to be done here, not in the apply callback! */
static int view_pan_modal(bContext *C, wmOperator *op, wmEvent *event)
{
	v2dViewPanData *vpd= op->customdata;
	
	/* execute the events */
	switch (event->type) {
		case MOUSEMOVE:
		{
			/* calculate new delta transform, then store mouse-coordinates for next-time */
			RNA_int_set(op->ptr, "deltax", (vpd->lastx - event->x));
			RNA_int_set(op->ptr, "deltay", (vpd->lasty - event->y));
			
			vpd->lastx= event->x;
			vpd->lasty= event->y;
			
			view_pan_apply(op);
		}
			break;
			
		case LEFTMOUSE:
			/* switch to zoom */
			if (event->val==KM_PRESS) {
				/* calculate overall delta mouse-movement for redo */
				RNA_int_set(op->ptr, "deltax", (vpd->startx - vpd->lastx));
				RNA_int_set(op->ptr, "deltay", (vpd->starty - vpd->lasty));
				
				view_pan_exit(op);
				WM_cursor_restore(CTX_wm_window(C));
				
				WM_operator_name_call(C, "VIEW2D_OT_zoom", WM_OP_INVOKE_DEFAULT, NULL);
				return OPERATOR_FINISHED;
			}
			
		default:
			if (event->type == vpd->invoke_event || event->type==ESCKEY) {
				if (event->val==KM_RELEASE) {
					/* calculate overall delta mouse-movement for redo */
					RNA_int_set(op->ptr, "deltax", (vpd->startx - vpd->lastx));
					RNA_int_set(op->ptr, "deltay", (vpd->starty - vpd->lasty));
					
					view_pan_exit(op);
					WM_cursor_restore(CTX_wm_window(C));
					
					return OPERATOR_FINISHED;
				}
			}
			break;
	}

	return OPERATOR_RUNNING_MODAL;
}

static int view_pan_cancel(bContext *UNUSED(C), wmOperator *op)
{
	view_pan_exit(op);
	return OPERATOR_CANCELLED;
}

static void VIEW2D_OT_pan(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Pan View";
	ot->description= "Pan the view";
	ot->idname= "VIEW2D_OT_pan";
	
	/* api callbacks */
	ot->exec= view_pan_exec;
	ot->invoke= view_pan_invoke;
	ot->modal= view_pan_modal;
	ot->cancel= view_pan_cancel;
	
	/* operator is modal */
	ot->flag= OPTYPE_BLOCKING|OPTYPE_GRAB_POINTER;
	
	/* rna - must keep these in sync with the other operators */
	RNA_def_int(ot->srna, "deltax", 0, INT_MIN, INT_MAX, "Delta X", "", INT_MIN, INT_MAX);
	RNA_def_int(ot->srna, "deltay", 0, INT_MIN, INT_MAX, "Delta Y", "", INT_MIN, INT_MAX);
}

/* ------------------ Scrollwheel Versions (2) ---------------------- */

/* this operator only needs this single callback, where it callsthe view_pan_*() methods */
static int view_scrollright_exec(bContext *C, wmOperator *op)
{
	v2dViewPanData *vpd;
	
	/* initialise default settings (and validate if ok to run) */
	if (!view_pan_init(C, op))
		return OPERATOR_PASS_THROUGH;
		
	/* also, check if can pan in horizontal axis */
	vpd= op->customdata;
	if (vpd->v2d->keepofs & V2D_LOCKOFS_X) {
		view_pan_exit(op);
		return OPERATOR_PASS_THROUGH;
	}
	
	/* set RNA-Props - only movement in positive x-direction */
	RNA_int_set(op->ptr, "deltax", 20);
	RNA_int_set(op->ptr, "deltay", 0);
	
	/* apply movement, then we're done */
	view_pan_apply(op);
	view_pan_exit(op);
	
	return OPERATOR_FINISHED;
}

static void VIEW2D_OT_scroll_right(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Scroll Right";
	ot->description= "Scroll the view right";
	ot->idname= "VIEW2D_OT_scroll_right";
	
	/* api callbacks */
	ot->exec= view_scrollright_exec;
	
	/* rna - must keep these in sync with the other operators */
	RNA_def_int(ot->srna, "deltax", 0, INT_MIN, INT_MAX, "Delta X", "", INT_MIN, INT_MAX);
	RNA_def_int(ot->srna, "deltay", 0, INT_MIN, INT_MAX, "Delta Y", "", INT_MIN, INT_MAX);
}



/* this operator only needs this single callback, where it callsthe view_pan_*() methods */
static int view_scrollleft_exec(bContext *C, wmOperator *op)
{
	v2dViewPanData *vpd;
	
	/* initialise default settings (and validate if ok to run) */
	if (!view_pan_init(C, op))
		return OPERATOR_PASS_THROUGH;
		
	/* also, check if can pan in horizontal axis */
	vpd= op->customdata;
	if (vpd->v2d->keepofs & V2D_LOCKOFS_X) {
		view_pan_exit(op);
		return OPERATOR_PASS_THROUGH;
	}
	
	/* set RNA-Props - only movement in negative x-direction */
	RNA_int_set(op->ptr, "deltax", -20);
	RNA_int_set(op->ptr, "deltay", 0);
	
	/* apply movement, then we're done */
	view_pan_apply(op);
	view_pan_exit(op);
	
	return OPERATOR_FINISHED;
}

static void VIEW2D_OT_scroll_left(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Scroll Left";
	ot->description= "Scroll the view left";
	ot->idname= "VIEW2D_OT_scroll_left";
	
	/* api callbacks */
	ot->exec= view_scrollleft_exec;
	
	/* rna - must keep these in sync with the other operators */
	RNA_def_int(ot->srna, "deltax", 0, INT_MIN, INT_MAX, "Delta X", "", INT_MIN, INT_MAX);
	RNA_def_int(ot->srna, "deltay", 0, INT_MIN, INT_MAX, "Delta Y", "", INT_MIN, INT_MAX);
}


/* this operator only needs this single callback, where it callsthe view_pan_*() methods */
static int view_scrolldown_exec(bContext *C, wmOperator *op)
{
	v2dViewPanData *vpd;
	
	/* initialise default settings (and validate if ok to run) */
	if (!view_pan_init(C, op))
		return OPERATOR_PASS_THROUGH;
		
	/* also, check if can pan in vertical axis */
	vpd= op->customdata;
	if (vpd->v2d->keepofs & V2D_LOCKOFS_Y) {
		view_pan_exit(op);
		return OPERATOR_PASS_THROUGH;
	}
	
	/* set RNA-Props */
	RNA_int_set(op->ptr, "deltax", 0);
	RNA_int_set(op->ptr, "deltay", -40);
	
	if(RNA_boolean_get(op->ptr, "page")) {
		ARegion *ar= CTX_wm_region(C);
		RNA_int_set(op->ptr, "deltay", ar->v2d.mask.ymin - ar->v2d.mask.ymax);
	}
	
	/* apply movement, then we're done */
	view_pan_apply(op);
	view_pan_exit(op);
	
	return OPERATOR_FINISHED;
}

static void VIEW2D_OT_scroll_down(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Scroll Down";
	ot->description= "Scroll the view down";
	ot->idname= "VIEW2D_OT_scroll_down";
	
	/* api callbacks */
	ot->exec= view_scrolldown_exec;
	
	/* rna - must keep these in sync with the other operators */
	RNA_def_int(ot->srna, "deltax", 0, INT_MIN, INT_MAX, "Delta X", "", INT_MIN, INT_MAX);
	RNA_def_int(ot->srna, "deltay", 0, INT_MIN, INT_MAX, "Delta Y", "", INT_MIN, INT_MAX);
	RNA_def_boolean(ot->srna, "page", 0, "Page", "Scroll down one page");
}



/* this operator only needs this single callback, where it callsthe view_pan_*() methods */
static int view_scrollup_exec(bContext *C, wmOperator *op)
{
	v2dViewPanData *vpd;
	
	/* initialise default settings (and validate if ok to run) */
	if (!view_pan_init(C, op))
		return OPERATOR_PASS_THROUGH;
		
	/* also, check if can pan in vertical axis */
	vpd= op->customdata;
	if (vpd->v2d->keepofs & V2D_LOCKOFS_Y) {
		view_pan_exit(op);
		return OPERATOR_PASS_THROUGH;
	}
	
	/* set RNA-Props */
	RNA_int_set(op->ptr, "deltax", 0);
	RNA_int_set(op->ptr, "deltay", 40);
	
	if(RNA_boolean_get(op->ptr, "page")) {
		ARegion *ar= CTX_wm_region(C);
		RNA_int_set(op->ptr, "deltay", ar->v2d.mask.ymax - ar->v2d.mask.ymin);
	}
	
	/* apply movement, then we're done */
	view_pan_apply(op);
	view_pan_exit(op);
	
	return OPERATOR_FINISHED;
}

static void VIEW2D_OT_scroll_up(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Scroll Up";
	ot->description= "Scroll the view up";
	ot->idname= "VIEW2D_OT_scroll_up";
	
	/* api callbacks */
	ot->exec= view_scrollup_exec;
	
	/* rna - must keep these in sync with the other operators */
	RNA_def_int(ot->srna, "deltax", 0, INT_MIN, INT_MAX, "Delta X", "", INT_MIN, INT_MAX);
	RNA_def_int(ot->srna, "deltay", 0, INT_MIN, INT_MAX, "Delta Y", "", INT_MIN, INT_MAX);
	RNA_def_boolean(ot->srna, "page", 0, "Page", "Scroll up one page");
}

/* ********************************************************* */
/* SINGLE-STEP VIEW ZOOMING OPERATOR						 */

/* 	This group of operators come in several forms:
 *		1) Scrollwheel 'steps' - rolling mousewheel by one step zooms view by predefined amount
 *		2) Scrollwheel 'steps' + alt + ctrl/shift - zooms view on one axis only (ctrl=x, shift=y)  // XXX this could be implemented...
 *		3) Pad +/- Keys - pressing each key moves the zooms the view by a predefined amount
 *
 *	In order to make sure this works, each operator must define the following RNA-Operator Props:
 *		zoomfacx, zoomfacy	- These two zoom factors allow for non-uniform scaling.
 *							  It is safe to scale by 0, as these factors are used to determine
 *							  amount to enlarge 'cur' by
 */

/* ------------------ 'Shared' stuff ------------------------ */

/* temp customdata for operator */
typedef struct v2dViewZoomData {
	View2D *v2d;			/* view2d we're operating in */
	ARegion *ar;

	/* needed for continuous zoom */
	wmTimer *timer;
	double timer_lastdraw;

	int lastx, lasty;		/* previous x/y values of mouse in window */
	int invoke_event;		/* event type that invoked, for modal exits */
	float dx, dy;			/* running tally of previous delta values (for obtaining final zoom) */
	float mx_2d, my_2d;		/* initial mouse location in v2d coords */
} v2dViewZoomData;


/* initialise panning customdata */
static int view_zoomdrag_init(bContext *C, wmOperator *op)
{
	ARegion *ar= CTX_wm_region(C);
	v2dViewZoomData *vzd;
	View2D *v2d;
	
	/* regions now have v2d-data by default, so check for region */
	if (ar == NULL)
		return 0;
	v2d= &ar->v2d;
	
	/* check that 2d-view is zoomable */
	if ((v2d->keepzoom & V2D_LOCKZOOM_X) && (v2d->keepzoom & V2D_LOCKZOOM_Y))
		return 0;
	
	/* set custom-data for operator */
	vzd= MEM_callocN(sizeof(v2dViewZoomData), "v2dViewZoomData");
	op->customdata= vzd;
	
	/* set pointers to owners */
	vzd->v2d= v2d;
	vzd->ar = ar;
	
	return 1;
}

/* check if step-zoom can be applied */
static int view_zoom_poll(bContext *C)
{
	ARegion *ar= CTX_wm_region(C);
	View2D *v2d;
	
	/* check if there's a region in context to work with */
	if (ar == NULL)
		return 0;
	v2d= &ar->v2d;
	
	/* check that 2d-view is zoomable */
	if ((v2d->keepzoom & V2D_LOCKZOOM_X) && (v2d->keepzoom & V2D_LOCKZOOM_Y))
		return 0;
		
	/* view is zoomable */
	return 1;
}
 
/* apply transform to view (i.e. adjust 'cur' rect) */
static void view_zoomstep_apply(bContext *C, wmOperator *op)
{
	v2dViewZoomData *vzd= op->customdata;
	ARegion *ar= CTX_wm_region(C);
	View2D *v2d= &ar->v2d;
	float dx, dy, facx, facy;
	
	/* calculate amount to move view by, ensuring symmetry so the
	 * old zoom level is restored after zooming back the same amount 
	 */
	facx= RNA_float_get(op->ptr, "zoomfacx");
	facy= RNA_float_get(op->ptr, "zoomfacy");

	if (facx >= 0.0f) {
		dx= (v2d->cur.xmax - v2d->cur.xmin) * facx;
		dy= (v2d->cur.ymax - v2d->cur.ymin) * facy;
	}
	else {
		dx= ((v2d->cur.xmax - v2d->cur.xmin)/(1.0f + 2.0f*facx)) * facx;
		dy= ((v2d->cur.ymax - v2d->cur.ymin)/(1.0f + 2.0f*facy)) * facy;
	}

	/* only resize view on an axis if change is allowed */
	if ((v2d->keepzoom & V2D_LOCKZOOM_X)==0) {
		if (v2d->keepofs & V2D_LOCKOFS_X) {
			v2d->cur.xmax -= 2*dx;
		}
		else if (v2d->keepofs & V2D_KEEPOFS_X) {
			if (v2d->align & V2D_ALIGN_NO_POS_X)
				v2d->cur.xmin += 2*dx;
			else
				v2d->cur.xmax -= 2*dx;
		}
		else {
			if (U.uiflag & USER_ZOOM_TO_MOUSEPOS) {
				float mval_fac = (vzd->mx_2d - v2d->cur.xmin) / (v2d->cur.xmax-v2d->cur.xmin);
				float mval_faci = 1.0f - mval_fac;
				float ofs= (mval_fac * dx) - (mval_faci * dx);
				
				v2d->cur.xmin += ofs + dx;
				v2d->cur.xmax += ofs - dx;
			}
			else {
				v2d->cur.xmin += dx;
				v2d->cur.xmax -= dx;
			}
		}
	}
	if ((v2d->keepzoom & V2D_LOCKZOOM_Y)==0) {
		if (v2d->keepofs & V2D_LOCKOFS_Y) {
			v2d->cur.ymax -= 2*dy;
		}
		else if (v2d->keepofs & V2D_KEEPOFS_Y) {
			if (v2d->align & V2D_ALIGN_NO_POS_Y)
				v2d->cur.ymin += 2*dy;
			else
				v2d->cur.ymax -= 2*dy;
		}
		else {
			if (U.uiflag & USER_ZOOM_TO_MOUSEPOS) {
				float mval_fac = (vzd->my_2d - v2d->cur.ymin) / (v2d->cur.ymax-v2d->cur.ymin);
				float mval_faci = 1.0f - mval_fac;
				float ofs= (mval_fac * dy) - (mval_faci * dy);
				
				v2d->cur.ymin += ofs + dy;
				v2d->cur.ymax += ofs - dy;
			} 
			else {
				v2d->cur.ymin += dy;
				v2d->cur.ymax -= dy;
			}
		}
	}

	/* validate that view is in valid configuration after this operation */
	UI_view2d_curRect_validate(v2d);

	/* request updates to be done... */
	ED_region_tag_redraw(vzd->ar);
	UI_view2d_sync(CTX_wm_screen(C), CTX_wm_area(C), v2d, V2D_LOCK_COPY);
}

/* --------------- Individual Operators ------------------- */

/* cleanup temp customdata  */
static void view_zoomstep_exit(wmOperator *op)
{
	if (op->customdata) {
		MEM_freeN(op->customdata);
		op->customdata= NULL;				
	}
}

/* this operator only needs this single callback, where it calls the view_zoom_*() methods */
static int view_zoomin_exec(bContext *C, wmOperator *op)
{
	/* check that there's an active region, as View2D data resides there */
	if (!view_zoom_poll(C))
		return OPERATOR_PASS_THROUGH;
	
	/* set RNA-Props - zooming in by uniform factor */
	RNA_float_set(op->ptr, "zoomfacx", 0.0375f);
	RNA_float_set(op->ptr, "zoomfacy", 0.0375f);
	
	/* apply movement, then we're done */
	view_zoomstep_apply(C, op);
	
	view_zoomstep_exit(op);
	
	return OPERATOR_FINISHED;
}

static int view_zoomin_invoke(bContext *C, wmOperator *op, wmEvent *event)
{
	v2dViewZoomData *vzd;
	
	if (!view_zoomdrag_init(C, op))
		return OPERATOR_PASS_THROUGH;
	
	vzd= op->customdata;
	
	if (U.uiflag & USER_ZOOM_TO_MOUSEPOS) {
		ARegion *ar= CTX_wm_region(C);
		
		/* store initial mouse position (in view space) */
		UI_view2d_region_to_view(&ar->v2d, 
				event->mval[0], event->mval[1],
				&vzd->mx_2d, &vzd->my_2d);
	}
	
	return view_zoomin_exec(C, op);
}

static void VIEW2D_OT_zoom_in(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Zoom In";
	ot->description= "Zoom in the view";
	ot->idname= "VIEW2D_OT_zoom_in";
	
	/* api callbacks */
	ot->invoke= view_zoomin_invoke;
//	ot->exec= view_zoomin_exec;  // XXX, needs view_zoomdrag_init called first.
	ot->poll= view_zoom_poll;
	
	/* rna - must keep these in sync with the other operators */
	RNA_def_float(ot->srna, "zoomfacx", 0, -FLT_MAX, FLT_MAX, "Zoom Factor X", "", -FLT_MAX, FLT_MAX);
	RNA_def_float(ot->srna, "zoomfacy", 0, -FLT_MAX, FLT_MAX, "Zoom Factor Y", "", -FLT_MAX, FLT_MAX);
}
	
/* this operator only needs this single callback, where it callsthe view_zoom_*() methods */
static int view_zoomout_exec(bContext *C, wmOperator *op)
{
	/* check that there's an active region, as View2D data resides there */
	if (!view_zoom_poll(C))
		return OPERATOR_PASS_THROUGH;
	
	/* set RNA-Props - zooming in by uniform factor */
	RNA_float_set(op->ptr, "zoomfacx", -0.0375f);
	RNA_float_set(op->ptr, "zoomfacy", -0.0375f);
	
	/* apply movement, then we're done */
	view_zoomstep_apply(C, op);

	view_zoomstep_exit(op);
	
	return OPERATOR_FINISHED;
}

static int view_zoomout_invoke(bContext *C, wmOperator *op, wmEvent *event)
{
	v2dViewZoomData *vzd;
	
	if (!view_zoomdrag_init(C, op))
		return OPERATOR_PASS_THROUGH;

	vzd= op->customdata;
	
	if(U.uiflag & USER_ZOOM_TO_MOUSEPOS) {
		ARegion *ar= CTX_wm_region(C);
		
		/* store initial mouse position (in view space) */
		UI_view2d_region_to_view(&ar->v2d, 
				event->mval[0], event->mval[1],
				&vzd->mx_2d, &vzd->my_2d);
	}
	
	return view_zoomout_exec(C, op);
}

static void VIEW2D_OT_zoom_out(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Zoom Out";
	ot->description= "Zoom out the view";
	ot->idname= "VIEW2D_OT_zoom_out";
	
	/* api callbacks */
	ot->invoke= view_zoomout_invoke;
//	ot->exec= view_zoomout_exec; // XXX, needs view_zoomdrag_init called first.
	ot->poll= view_zoom_poll;
	
	/* rna - must keep these in sync with the other operators */
	RNA_def_float(ot->srna, "zoomfacx", 0, -FLT_MAX, FLT_MAX, "Zoom Factor X", "", -FLT_MAX, FLT_MAX);
	RNA_def_float(ot->srna, "zoomfacy", 0, -FLT_MAX, FLT_MAX, "Zoom Factor Y", "", -FLT_MAX, FLT_MAX);
}

/* ********************************************************* */
/* DRAG-ZOOM OPERATOR									 */

/* 	MMB Drag - allows non-uniform scaling by dragging mouse
 *
 *	In order to make sure this works, each operator must define the following RNA-Operator Props:
 *		deltax, deltay	- amounts to add to each side of the 'cur' rect
 */

/* apply transform to view (i.e. adjust 'cur' rect) */
static void view_zoomdrag_apply(bContext *C, wmOperator *op)
{
	v2dViewZoomData *vzd= op->customdata;
	View2D *v2d= vzd->v2d;
	float dx, dy;
	
	/* get amount to move view by */
	dx= RNA_float_get(op->ptr, "deltax");
	dy= RNA_float_get(op->ptr, "deltay");

	/* continous zoom shouldn't move that fast... */
	if (U.viewzoom == USER_ZOOM_CONT) { // XXX store this setting as RNA prop?
		double time= PIL_check_seconds_timer();
		float time_step= (float)(time - vzd->timer_lastdraw);

		dx *= time_step * 0.5f;
		dy *= time_step * 0.5f;
		
		vzd->timer_lastdraw= time;
	}

	/* only move view on an axis if change is allowed */
	if ((v2d->keepzoom & V2D_LOCKZOOM_X)==0) {
		if (v2d->keepofs & V2D_LOCKOFS_X) {
			v2d->cur.xmax -= 2*dx;
		}
		else {
			if (U.uiflag & USER_ZOOM_TO_MOUSEPOS) {
				float mval_fac = (vzd->mx_2d - v2d->cur.xmin) / (v2d->cur.xmax-v2d->cur.xmin);
				float mval_faci = 1.0f - mval_fac;
				float ofs= (mval_fac * dx) - (mval_faci * dx);
				
				v2d->cur.xmin += ofs + dx;
				v2d->cur.xmax += ofs - dx;
			}
			else {
				v2d->cur.xmin += dx;
				v2d->cur.xmax -= dx;
			}
		}
	}
	if ((v2d->keepzoom & V2D_LOCKZOOM_Y)==0) {
		if (v2d->keepofs & V2D_LOCKOFS_Y) {
			v2d->cur.ymax -= 2*dy;
		}
		else {
			if (U.uiflag & USER_ZOOM_TO_MOUSEPOS) {
				float mval_fac = (vzd->my_2d - v2d->cur.ymin) / (v2d->cur.ymax-v2d->cur.ymin);
				float mval_faci = 1.0f - mval_fac;
				float ofs= (mval_fac * dy) - (mval_faci * dy);
				
				v2d->cur.ymin += ofs + dy;
				v2d->cur.ymax += ofs - dy;
			}
			else {
				v2d->cur.ymin += dy;
				v2d->cur.ymax -= dy;
			}
		}
	}
	
	/* validate that view is in valid configuration after this operation */
	UI_view2d_curRect_validate(v2d);
	
	/* request updates to be done... */
	ED_region_tag_redraw(vzd->ar);
	UI_view2d_sync(CTX_wm_screen(C), CTX_wm_area(C), v2d, V2D_LOCK_COPY);
}

/* cleanup temp customdata  */
static void view_zoomdrag_exit(bContext *C, wmOperator *op)
{
	if (op->customdata) {
		v2dViewZoomData *vzd= op->customdata;
		
		if(vzd->timer)
			WM_event_remove_timer(CTX_wm_manager(C), CTX_wm_window(C), vzd->timer);
		
		MEM_freeN(op->customdata);
		op->customdata= NULL;				
	}
} 

static int view_zoomdrag_cancel(bContext *C, wmOperator *op)
{
	view_zoomdrag_exit(C, op);

	return OPERATOR_CANCELLED;
}

/* for 'redo' only, with no user input */
static int view_zoomdrag_exec(bContext *C, wmOperator *op)
{
	if (!view_zoomdrag_init(C, op))
		return OPERATOR_PASS_THROUGH;
	
	view_zoomdrag_apply(C, op);
	view_zoomdrag_exit(C, op);
	return OPERATOR_FINISHED;
}

/* set up modal operator and relevant settings */
static int view_zoomdrag_invoke(bContext *C, wmOperator *op, wmEvent *event)
{
	wmWindow *window= CTX_wm_window(C);
	v2dViewZoomData *vzd;
	View2D *v2d;
	
	/* set up customdata */
	if (!view_zoomdrag_init(C, op))
		return OPERATOR_PASS_THROUGH;
	
	vzd= op->customdata;
	v2d= vzd->v2d;
	
	if (event->type == MOUSEZOOM) {
		float dx, dy, fac;
		
		vzd->lastx= event->prevx;
		vzd->lasty= event->prevy;
		
		/* As we have only 1D information (magnify value), feed both axes
		 * with magnify information that is stored in x axis 
		 */
		fac= 0.01f * (event->x - event->prevx);
		dx= fac * (v2d->cur.xmax - v2d->cur.xmin) / 10.0f;
		dy= fac * (v2d->cur.ymax - v2d->cur.ymin) / 10.0f;

		RNA_float_set(op->ptr, "deltax", dx);
		RNA_float_set(op->ptr, "deltay", dy);
		
		view_zoomdrag_apply(C, op);
		view_zoomdrag_exit(C, op);
		return OPERATOR_FINISHED;
	}	
	
	/* set initial settings */
	vzd->lastx= event->x;
	vzd->lasty= event->y;
	RNA_float_set(op->ptr, "deltax", 0);
	RNA_float_set(op->ptr, "deltay", 0);
	
	/* for modal exit test */
	vzd->invoke_event= event->type;
	
	if (U.uiflag & USER_ZOOM_TO_MOUSEPOS) {
		ARegion *ar= CTX_wm_region(C);
		
		/* store initial mouse position (in view space) */
		UI_view2d_region_to_view(&ar->v2d, 
				event->mval[0], event->mval[1],
				&vzd->mx_2d, &vzd->my_2d);
	}

	if (v2d->keepofs & V2D_LOCKOFS_X)
		WM_cursor_modal(window, BC_NS_SCROLLCURSOR);
	else if (v2d->keepofs & V2D_LOCKOFS_Y)
		WM_cursor_modal(window, BC_EW_SCROLLCURSOR);
	else
		WM_cursor_modal(window, BC_NSEW_SCROLLCURSOR);
	
	/* add temp handler */
	WM_event_add_modal_handler(C, op);

	if (U.viewzoom == USER_ZOOM_CONT) {
		/* needs a timer to continue redrawing */
		vzd->timer= WM_event_add_timer(CTX_wm_manager(C), CTX_wm_window(C), TIMER, 0.01f);
		vzd->timer_lastdraw= PIL_check_seconds_timer();
	}

	return OPERATOR_RUNNING_MODAL;
}

/* handle user input - calculations of mouse-movement need to be done here, not in the apply callback! */
static int view_zoomdrag_modal(bContext *C, wmOperator *op, wmEvent *event)
{
	v2dViewZoomData *vzd= op->customdata;
	View2D *v2d= vzd->v2d;
	
	/* execute the events */
	if (event->type == TIMER && event->customdata == vzd->timer) {
		view_zoomdrag_apply(C, op);
	}
	else if(event->type == MOUSEMOVE) {
		float dx, dy;
		
		/* calculate new delta transform, based on zooming mode */
		if (U.viewzoom == USER_ZOOM_SCALE) {
			/* 'scale' zooming */
			float dist;
			
			/* x-axis transform */
			dist = (v2d->mask.xmax - v2d->mask.xmin) / 2.0f;
			dx= 1.0f - (fabsf(vzd->lastx - dist) + 2.0f) / (fabsf(event->x - dist) + 2.0f);
			dx*= 0.5f * (v2d->cur.xmax - v2d->cur.xmin);
			
			/* y-axis transform */
			dist = (v2d->mask.ymax - v2d->mask.ymin) / 2.0f;
			dy= 1.0f - (fabsf(vzd->lasty - dist) + 2.0f) / (fabsf(event->y - dist) + 2.0f);
			dy*= 0.5f * (v2d->cur.ymax - v2d->cur.ymin);
		}
		else {
			/* 'continuous' or 'dolly' */
			float fac;
			
			/* x-axis transform */
			fac= 0.01f * (event->x - vzd->lastx);
			dx= fac * (v2d->cur.xmax - v2d->cur.xmin);
			
			/* y-axis transform */
			fac= 0.01f * (event->y - vzd->lasty);
			dy= fac * (v2d->cur.ymax - v2d->cur.ymin);
#if 0
			/* continous zoom shouldn't move that fast... */
			if (U.viewzoom == USER_ZOOM_CONT) { // XXX store this setting as RNA prop?
				double time= PIL_check_seconds_timer();
				float time_step= (float)(time - vzd->timer_lastdraw);

				dx /= (0.1f / time_step);
				dy /= (0.1f / time_step);
				
				vzd->timer_lastdraw= time;
			}
#endif
		}
		
		/* set transform amount, and add current deltas to stored total delta (for redo) */
		RNA_float_set(op->ptr, "deltax", dx);
		RNA_float_set(op->ptr, "deltay", dy);
		vzd->dx += dx;
		vzd->dy += dy;
		
		/* store mouse coordinates for next time, if not doing continuous zoom
		 *	- continuous zoom only depends on distance of mouse to starting point to determine rate of change
		 */
		if (U.viewzoom != USER_ZOOM_CONT) { // XXX store this setting as RNA prop?
			vzd->lastx= event->x;
			vzd->lasty= event->y;
		}
		
		/* apply zooming */
		view_zoomdrag_apply(C, op);
	} 
	else if (event->type == vzd->invoke_event || event->type==ESCKEY) {
		if (event->val == KM_RELEASE) {
			
			/* for redo, store the overall deltas - need to respect zoom-locks here... */
			if ((v2d->keepzoom & V2D_LOCKZOOM_X)==0)
				RNA_float_set(op->ptr, "deltax", vzd->dx);
			else
				RNA_float_set(op->ptr, "deltax", 0);
				
			if ((v2d->keepzoom & V2D_LOCKZOOM_Y)==0)
				RNA_float_set(op->ptr, "deltay", vzd->dy);
			else
				RNA_float_set(op->ptr, "deltay", 0);
			
			/* free customdata */
			view_zoomdrag_exit(C, op);
			WM_cursor_restore(CTX_wm_window(C));
			
			return OPERATOR_FINISHED;
		}
	}

	return OPERATOR_RUNNING_MODAL;
}

static void VIEW2D_OT_zoom(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Zoom 2D View";
	ot->description= "Zoom in/out the view";
	ot->idname= "VIEW2D_OT_zoom";
	
	/* api callbacks */
	ot->exec= view_zoomdrag_exec;
	ot->invoke= view_zoomdrag_invoke;
	ot->modal= view_zoomdrag_modal;
	ot->cancel= view_zoomdrag_cancel;
	
	ot->poll= view_zoom_poll;
	
	/* operator is repeatable */
	// ot->flag= OPTYPE_BLOCKING;
	
	/* rna - must keep these in sync with the other operators */
	RNA_def_float(ot->srna, "deltax", 0, -FLT_MAX, FLT_MAX, "Delta X", "", -FLT_MAX, FLT_MAX);
	RNA_def_float(ot->srna, "deltay", 0, -FLT_MAX, FLT_MAX, "Delta Y", "", -FLT_MAX, FLT_MAX);
}

/* ********************************************************* */
/* BORDER-ZOOM */

/* The user defines a rect using standard borderselect tools, and we use this rect to 
 * define the new zoom-level of the view in the following ways:
 *	1) LEFTMOUSE - zoom in to view
 *	2) RIGHTMOUSE - zoom out of view
 *
 * Currently, these key mappings are hardcoded, but it shouldn't be too important to
 * have custom keymappings for this...
 */
 
static int view_borderzoom_exec(bContext *C, wmOperator *op)
{
	ARegion *ar= CTX_wm_region(C);
	View2D *v2d= &ar->v2d;
	rctf rect;
	int gesture_mode;
	
	/* convert coordinates of rect to 'tot' rect coordinates */
	UI_view2d_region_to_view(v2d, RNA_int_get(op->ptr, "xmin"), RNA_int_get(op->ptr, "ymin"), &rect.xmin, &rect.ymin);
	UI_view2d_region_to_view(v2d, RNA_int_get(op->ptr, "xmax"), RNA_int_get(op->ptr, "ymax"), &rect.xmax, &rect.ymax);
	
	/* check if zooming in/out view */
	gesture_mode= RNA_int_get(op->ptr, "gesture_mode");
	
	if (gesture_mode == GESTURE_MODAL_IN) {
		/* zoom in: 
		 *	- 'cur' rect will be defined by the coordinates of the border region 
		 *	- just set the 'cur' rect to have the same coordinates as the border region
		 *	  if zoom is allowed to be changed
		 */
		if ((v2d->keepzoom & V2D_LOCKZOOM_X)==0) {
			v2d->cur.xmin= rect.xmin;
			v2d->cur.xmax= rect.xmax;
		}
		if ((v2d->keepzoom & V2D_LOCKZOOM_Y)==0) {
			v2d->cur.ymin= rect.ymin;
			v2d->cur.ymax= rect.ymax;
		}
	}
	else /* if (gesture_mode == GESTURE_MODAL_OUT) */ {
		/* zoom out:
		 *	- the current 'cur' rect coordinates are going to end upwhere the 'rect' ones are, 
		 *	  but the 'cur' rect coordinates will need to be adjusted to take in more of the view
		 *	- calculate zoom factor, and adjust using center-point
		 */
		float zoom, center, size;
		
		// TODO: is this zoom factor calculation valid? It seems to produce same results everytime...
		if ((v2d->keepzoom & V2D_LOCKZOOM_X)==0) {
			size= (v2d->cur.xmax - v2d->cur.xmin);
			zoom= size / (rect.xmax - rect.xmin);
			center= (v2d->cur.xmax + v2d->cur.xmin) * 0.5f;
			
			v2d->cur.xmin= center - (size * zoom);
			v2d->cur.xmax= center + (size * zoom);
		}
		if ((v2d->keepzoom & V2D_LOCKZOOM_Y)==0) {
			size= (v2d->cur.ymax - v2d->cur.ymin);
			zoom= size / (rect.ymax - rect.ymin);
			center= (v2d->cur.ymax + v2d->cur.ymin) * 0.5f;
			
			v2d->cur.ymin= center - (size * zoom);
			v2d->cur.ymax= center + (size * zoom);
		}
	}
	
	/* validate that view is in valid configuration after this operation */
	UI_view2d_curRect_validate(v2d);
	
	/* request updates to be done... */
	ED_region_tag_redraw(ar);
	UI_view2d_sync(CTX_wm_screen(C), CTX_wm_area(C), v2d, V2D_LOCK_COPY);
	
	return OPERATOR_FINISHED;
} 

static void VIEW2D_OT_zoom_border(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Zoom to Border";
	ot->description= "Zoom in the view to the nearest item contained in the border";
	ot->idname= "VIEW2D_OT_zoom_border";
	
	/* api callbacks */
	ot->invoke= WM_border_select_invoke;
	ot->exec= view_borderzoom_exec;
	ot->modal= WM_border_select_modal;
	ot->cancel= WM_border_select_cancel;
	
	ot->poll= view_zoom_poll;
	
	/* rna */
	RNA_def_int(ot->srna, "gesture_mode", 0, INT_MIN, INT_MAX, "Gesture Mode", "", INT_MIN, INT_MAX);
	RNA_def_int(ot->srna, "xmin", 0, INT_MIN, INT_MAX, "X Min", "", INT_MIN, INT_MAX);
	RNA_def_int(ot->srna, "xmax", 0, INT_MIN, INT_MAX, "X Max", "", INT_MIN, INT_MAX);
	RNA_def_int(ot->srna, "ymin", 0, INT_MIN, INT_MAX, "Y Min", "", INT_MIN, INT_MAX);
	RNA_def_int(ot->srna, "ymax", 0, INT_MIN, INT_MAX, "Y Max", "", INT_MIN, INT_MAX);
}

/* ********************************************************* */
/* SCROLLERS */

/* 	Scrollers should behave in the following ways, when clicked on with LMB (and dragged):
 *		1) 'Handles' on end of 'bubble' - when the axis that the scroller represents is zoomable, 
 *			enlarge 'cur' rect on the relevant side 
 *		2) 'Bubble'/'bar' - just drag, and bar should move with mouse (view pans opposite)
 *
 *	In order to make sure this works, each operator must define the following RNA-Operator Props:
 *		deltax, deltay 	- define how much to move view by (relative to zoom-correction factor)
 */

/* customdata for scroller-invoke data */
typedef struct v2dScrollerMove {
	View2D *v2d;			/* View2D data that this operation affects */
	ARegion *ar;			/* region that the scroller is in */
	
	short scroller;			/* scroller that mouse is in ('h' or 'v') */
	short zone;				/* -1 is min zoomer, 0 is bar, 1 is max zoomer */ // XXX find some way to provide visual feedback of this (active color?)
	
	float fac;				/* view adjustment factor, based on size of region */
	float delta;			/* amount moved by mouse on axis of interest */
	
	float scrollbarwidth;	/* width of the scrollbar itself, used for page up/down clicks */
	
	int lastx, lasty;		/* previous mouse coordinates (in screen coordinates) for determining movement */
} v2dScrollerMove;


/* View2DScrollers is typedef'd in UI_view2d.h 
 * This is a CUT DOWN VERSION of the 'real' version, which is defined in view2d.c, as we only need focus bubble info
 * WARNING: the start of this struct must not change, so that it stays in sync with the 'real' version
 * 		   For now, we don't need to have a separate (internal) header for structs like this...
 */
struct View2DScrollers {	
		/* focus bubbles */
	int vert_min, vert_max;	/* vertical scrollbar */
	int hor_min, hor_max;	/* horizontal scrollbar */
};

/* quick enum for vsm->zone (scroller handles) */
enum {
	SCROLLHANDLE_MIN= -1,
	SCROLLHANDLE_BAR,
	SCROLLHANDLE_MAX,
	SCROLLHANDLE_MIN_OUTSIDE,
	SCROLLHANDLE_MAX_OUTSIDE
} /*eV2DScrollerHandle_Zone*/;

/* ------------------------ */

/* check if mouse is within scroller handle 
 *	- mouse			= 	relevant mouse coordinate in region space
 *	- sc_min, sc_max	= 	extents of scroller 'groove' (potential available space for scroller)
 *	- sh_min, sh_max	= 	positions of scrollbar handles
 */
static short mouse_in_scroller_handle(int mouse, int sc_min, int sc_max, int sh_min, int sh_max)
{
	short in_min, in_max, in_bar, out_min, out_max, in_view=1;
	
	/* firstly, check if 
	 *	- 'bubble' fills entire scroller 
	 *	- 'bubble' completely out of view on either side 
	 */
	if ((sh_min <= sc_min) && (sh_max >= sc_max)) in_view= 0;
	if (sh_min == sh_max) {
		if (sh_min <= sc_min) in_view= 0;
		if (sh_max >= sc_max) in_view= 0;
	}
	else {
		if (sh_max <= sc_min) in_view= 0;
		if (sh_min >= sc_max) in_view= 0;
	}
	
	
	if (in_view == 0) {
		return SCROLLHANDLE_BAR;
	}
	
	/* check if mouse is in or past either handle */
	// TODO: check if these extents are still valid or not
	in_max= ( (mouse >= (sh_max - V2D_SCROLLER_HANDLE_SIZE)) && (mouse <= (sh_max + V2D_SCROLLER_HANDLE_SIZE)) );
	in_min= ( (mouse <= (sh_min + V2D_SCROLLER_HANDLE_SIZE)) && (mouse >= (sh_min - V2D_SCROLLER_HANDLE_SIZE)) );
	in_bar= ( (mouse < (sh_max - V2D_SCROLLER_HANDLE_SIZE)) && (mouse > (sh_min + V2D_SCROLLER_HANDLE_SIZE)) );
	out_min= mouse < (sh_min - V2D_SCROLLER_HANDLE_SIZE);
	out_max= mouse > (sh_max + V2D_SCROLLER_HANDLE_SIZE);
	
	if (in_bar)
		return SCROLLHANDLE_BAR;
	else if (in_max)
		return SCROLLHANDLE_MAX;
	else if (in_min)
		return SCROLLHANDLE_MIN;
	else if (out_min)
		return SCROLLHANDLE_MIN_OUTSIDE;			  
	else if (out_max)
		return SCROLLHANDLE_MAX_OUTSIDE;
	
	/* unlikely to happen, though we just cover it in case */
	return SCROLLHANDLE_BAR;
} 

/* initialise customdata for scroller manipulation operator */
static void scroller_activate_init(bContext *C, wmOperator *op, wmEvent *event, short in_scroller)
{
	v2dScrollerMove *vsm;
	View2DScrollers *scrollers;
	ARegion *ar= CTX_wm_region(C);
	View2D *v2d= &ar->v2d;
	float mask_size;
	
	/* set custom-data for operator */
	vsm= MEM_callocN(sizeof(v2dScrollerMove), "v2dScrollerMove");
	op->customdata= vsm;
	
	/* set general data */
	vsm->v2d= v2d;
	vsm->ar= ar;
	vsm->scroller= in_scroller;
	
	/* store mouse-coordinates, and convert mouse/screen coordinates to region coordinates */
	vsm->lastx = event->x;
	vsm->lasty = event->y;
	
	/* 'zone' depends on where mouse is relative to bubble 
	 *	- zooming must be allowed on this axis, otherwise, default to pan
	 */
	scrollers= UI_view2d_scrollers_calc(C, v2d, V2D_ARG_DUMMY, V2D_ARG_DUMMY, V2D_ARG_DUMMY, V2D_ARG_DUMMY);
	if (in_scroller == 'h') {
		/* horizontal scroller - calculate adjustment factor first */
		mask_size= (float)(v2d->hor.xmax - v2d->hor.xmin);
		vsm->fac= (v2d->tot.xmax - v2d->tot.xmin) / mask_size;
		
		/* get 'zone' (i.e. which part of scroller is activated) */
		vsm->zone= mouse_in_scroller_handle(event->mval[0], v2d->hor.xmin, v2d->hor.xmax, scrollers->hor_min, scrollers->hor_max);
		
		if ((v2d->keepzoom & V2D_LOCKZOOM_X) && ELEM(vsm->zone, SCROLLHANDLE_MIN, SCROLLHANDLE_MAX)) {
			/* default to scroll, as handles not usable */
			vsm->zone= SCROLLHANDLE_BAR;
		}

		vsm->scrollbarwidth = scrollers->hor_max - scrollers->hor_min;
	}
	else {
		/* vertical scroller - calculate adjustment factor first */
		mask_size= (float)(v2d->vert.ymax - v2d->vert.ymin);
		vsm->fac= (v2d->tot.ymax - v2d->tot.ymin) / mask_size;
		
		/* get 'zone' (i.e. which part of scroller is activated) */
		vsm->zone= mouse_in_scroller_handle(event->mval[1], v2d->vert.ymin, v2d->vert.ymax, scrollers->vert_min, scrollers->vert_max);
			
		if ((v2d->keepzoom & V2D_LOCKZOOM_Y) && ELEM(vsm->zone, SCROLLHANDLE_MIN, SCROLLHANDLE_MAX)) {
			/* default to scroll, as handles not usable */
			vsm->zone= SCROLLHANDLE_BAR;
		}
		
		vsm->scrollbarwidth = scrollers->vert_max - scrollers->vert_min;
	}
	
	UI_view2d_scrollers_free(scrollers);
	ED_region_tag_redraw(ar);
}

/* cleanup temp customdata  */
static void scroller_activate_exit(bContext *C, wmOperator *op)
{
	if (op->customdata) {
		v2dScrollerMove *vsm= op->customdata;

		vsm->v2d->scroll_ui &= ~(V2D_SCROLL_H_ACTIVE|V2D_SCROLL_V_ACTIVE);
		
		MEM_freeN(op->customdata);
		op->customdata= NULL;		
		
		ED_region_tag_redraw(CTX_wm_region(C));
	}
}

static int scroller_activate_cancel(bContext *C, wmOperator *op)
{
	scroller_activate_exit(C, op);

	return OPERATOR_CANCELLED;
}

/* apply transform to view (i.e. adjust 'cur' rect) */
static void scroller_activate_apply(bContext *C, wmOperator *op)
{
	v2dScrollerMove *vsm= op->customdata;
	View2D *v2d= vsm->v2d;
	float temp;
	
	/* calculate amount to move view by */
	temp= vsm->fac * vsm->delta;
	
	/* type of movement */
	switch (vsm->zone) {
		case SCROLLHANDLE_MIN:
			/* only expand view on axis if zoom is allowed */
			if ((vsm->scroller == 'h') && !(v2d->keepzoom & V2D_LOCKZOOM_X))
				v2d->cur.xmin -= temp;
			if ((vsm->scroller == 'v') && !(v2d->keepzoom & V2D_LOCKZOOM_Y))
				v2d->cur.ymin -= temp;
			break;
			
		case SCROLLHANDLE_MAX:
			
			/* only expand view on axis if zoom is allowed */
			if ((vsm->scroller == 'h') && !(v2d->keepzoom & V2D_LOCKZOOM_X))
				v2d->cur.xmax += temp;
			if ((vsm->scroller == 'v') && !(v2d->keepzoom & V2D_LOCKZOOM_Y))
				v2d->cur.ymax += temp;
			break;
			
		case SCROLLHANDLE_MIN_OUTSIDE:
		case SCROLLHANDLE_MAX_OUTSIDE:
		case SCROLLHANDLE_BAR:
		default:
			/* only move view on an axis if panning is allowed */
			if ((vsm->scroller == 'h') && !(v2d->keepofs & V2D_LOCKOFS_X)) {
				v2d->cur.xmin += temp;
				v2d->cur.xmax += temp;
			}
			if ((vsm->scroller == 'v') && !(v2d->keepofs & V2D_LOCKOFS_Y)) {
				v2d->cur.ymin += temp;
				v2d->cur.ymax += temp;
			}
			break;
			
	}
	
	/* validate that view is in valid configuration after this operation */
	UI_view2d_curRect_validate(v2d);
	
	/* request updates to be done... */
	ED_region_tag_redraw(vsm->ar);
	UI_view2d_sync(CTX_wm_screen(C), CTX_wm_area(C), v2d, V2D_LOCK_COPY);
}

/* handle user input for scrollers - calculations of mouse-movement need to be done here, not in the apply callback! */
static int scroller_activate_modal(bContext *C, wmOperator *op, wmEvent *event)
{
	v2dScrollerMove *vsm= op->customdata;
	
	/* execute the events */
	switch (event->type) {
		case MOUSEMOVE:
		{
			/* calculate new delta transform, then store mouse-coordinates for next-time */
			if (ELEM(vsm->zone, SCROLLHANDLE_BAR, SCROLLHANDLE_MAX)) {
				/* if using bar (i.e. 'panning') or 'max' zoom widget */
				switch (vsm->scroller) {
					case 'h': /* horizontal scroller - so only horizontal movement ('cur' moves opposite to mouse) */
						vsm->delta= (float)(event->x - vsm->lastx);
						break;
					case 'v': /* vertical scroller - so only vertical movement ('cur' moves opposite to mouse) */
						vsm->delta= (float)(event->y - vsm->lasty);
						break;
				}
			}
			else if (vsm->zone == SCROLLHANDLE_MIN) {
				/* using 'min' zoom widget */
				switch (vsm->scroller) {
					case 'h': /* horizontal scroller - so only horizontal movement ('cur' moves with mouse) */
						vsm->delta= (float)(vsm->lastx - event->x);
						break;
					case 'v': /* vertical scroller - so only vertical movement ('cur' moves with to mouse) */
						vsm->delta= (float)(vsm->lasty - event->y);
						break;
				}
			}
			
			/* store previous coordinates */
			vsm->lastx= event->x;
			vsm->lasty= event->y;
			
			scroller_activate_apply(C, op);
		}
			break;
			
		case LEFTMOUSE:
			if (event->val==KM_RELEASE) {
				/* single-click was in empty space outside bubble, so scroll by 1 'page' */
				if (ELEM(vsm->zone, SCROLLHANDLE_MIN_OUTSIDE, SCROLLHANDLE_MAX_OUTSIDE)) {
					if (vsm->zone == SCROLLHANDLE_MIN_OUTSIDE)
						vsm->delta = -vsm->scrollbarwidth * 0.8f;
					else if (vsm->zone == SCROLLHANDLE_MAX_OUTSIDE)
						vsm->delta = vsm->scrollbarwidth * 0.8f;
					
					scroller_activate_apply(C, op);
					scroller_activate_exit(C, op);
					return OPERATOR_FINISHED;
				}
				
				/* otherwise, end the drag action  */
				if (vsm->lastx || vsm->lasty) {
					scroller_activate_exit(C, op);
					return OPERATOR_FINISHED;
				}
			}
			break;
	}

	return OPERATOR_RUNNING_MODAL;
}


/* a click (or click drag in progress) should have occurred, so check if it happened in scrollbar */
static int scroller_activate_invoke(bContext *C, wmOperator *op, wmEvent *event)
{
	ARegion *ar= CTX_wm_region(C);
	View2D *v2d= &ar->v2d;
	short in_scroller= 0;
		
	/* check if mouse in scrollbars, if they're enabled */
	in_scroller= UI_view2d_mouse_in_scrollers(C, v2d, event->x, event->y);
	
	/* if in a scroller, init customdata then set modal handler which will catch mousedown to start doing useful stuff */
	if (in_scroller) {
		v2dScrollerMove *vsm;
		
		/* initialise customdata */
		scroller_activate_init(C, op, event, in_scroller);
		vsm= (v2dScrollerMove *)op->customdata;
		
		/* check if zoom zones are inappropriate (i.e. zoom widgets not shown), so cannot continue
		 * NOTE: see view2d.c for latest conditions, and keep this in sync with that
		 */
		if (ELEM(vsm->zone, SCROLLHANDLE_MIN, SCROLLHANDLE_MAX)) {
			if ( ((vsm->scroller=='h') && (v2d->scroll & V2D_SCROLL_SCALE_HORIZONTAL)==0) ||
				 ((vsm->scroller=='v') && (v2d->scroll & V2D_SCROLL_SCALE_VERTICAL)==0) )
			{
				/* switch to bar (i.e. no scaling gets handled) */
				vsm->zone= SCROLLHANDLE_BAR;
			}
		}
		
		/* check if zone is inappropriate (i.e. 'bar' but panning is banned), so cannot continue */
		if (vsm->zone == SCROLLHANDLE_BAR) {
			if ( ((vsm->scroller=='h') && (v2d->keepofs & V2D_LOCKOFS_X)) ||
				 ((vsm->scroller=='v') && (v2d->keepofs & V2D_LOCKOFS_Y)) )
			{
				/* free customdata initialised */
				scroller_activate_exit(C, op);
				
				/* can't catch this event for ourselves, so let it go to someone else? */
				return OPERATOR_PASS_THROUGH;
			}			
		}
		
		/* zone is also inappropriate if scroller is not visible... */
		if ( ((vsm->scroller=='h') && (v2d->scroll & (V2D_SCROLL_HORIZONTAL_HIDE|V2D_SCROLL_HORIZONTAL_FULLR))) ||
			 ((vsm->scroller=='v') && (v2d->scroll & (V2D_SCROLL_VERTICAL_HIDE|V2D_SCROLL_VERTICAL_FULLR))) )
		{
			/* free customdata initialised */
			scroller_activate_exit(C, op);
				
			/* can't catch this event for ourselves, so let it go to someone else? */
			/* XXX note: if handlers use mask rect to clip input, input will fail for this case */
			return OPERATOR_PASS_THROUGH;
		}
		
		/* activate the scroller */
		if (vsm->scroller=='h')
			v2d->scroll_ui |= V2D_SCROLL_H_ACTIVE;
		else
			v2d->scroll_ui |= V2D_SCROLL_V_ACTIVE;
		
		/* still ok, so can add */
		WM_event_add_modal_handler(C, op);
		return OPERATOR_RUNNING_MODAL;
	}
	else {
		/* not in scroller, so nothing happened... (pass through let's something else catch event) */
		return OPERATOR_PASS_THROUGH;
	}
}

/* LMB-Drag in Scrollers - not repeatable operator! */
static void VIEW2D_OT_scroller_activate(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Scroller Activate";
	ot->description= "Scroll view by mouse click and drag";
	ot->idname= "VIEW2D_OT_scroller_activate";

	/* flags */
	ot->flag= OPTYPE_BLOCKING;
	
	/* api callbacks */
	ot->invoke= scroller_activate_invoke;
	ot->modal= scroller_activate_modal;
	ot->cancel= scroller_activate_cancel;

	ot->poll= view2d_poll;
}

/* ********************************************************* */
/* RESET */

static int reset_exec(bContext *C, wmOperator *UNUSED(op))
{
	uiStyle *style= UI_GetStyle();
	ARegion *ar= CTX_wm_region(C);
	View2D *v2d= &ar->v2d;
	int winx, winy;

	/* zoom 1.0 */
	winx= (float)(v2d->mask.xmax - v2d->mask.xmin + 1);
	winy= (float)(v2d->mask.ymax - v2d->mask.ymin + 1);

	v2d->cur.xmax= v2d->cur.xmin + winx;
	v2d->cur.ymax= v2d->cur.ymin + winy;
	
	/* align */
	if (v2d->align) {
		/* posx and negx flags are mutually exclusive, so watch out */
		if ((v2d->align & V2D_ALIGN_NO_POS_X) && !(v2d->align & V2D_ALIGN_NO_NEG_X)) {
			v2d->cur.xmax= 0.0f;
			v2d->cur.xmin= -winx*style->panelzoom;
		}
		else if ((v2d->align & V2D_ALIGN_NO_NEG_X) && !(v2d->align & V2D_ALIGN_NO_POS_X)) {
			v2d->cur.xmax= winx*style->panelzoom;
			v2d->cur.xmin= 0.0f;
		}

		/* - posx and negx flags are mutually exclusive, so watch out */
		if ((v2d->align & V2D_ALIGN_NO_POS_Y) && !(v2d->align & V2D_ALIGN_NO_NEG_Y)) {
			v2d->cur.ymax= 0.0f;
			v2d->cur.ymin= -winy*style->panelzoom;
		}
		else if ((v2d->align & V2D_ALIGN_NO_NEG_Y) && !(v2d->align & V2D_ALIGN_NO_POS_Y)) {
			v2d->cur.ymax= winy*style->panelzoom;
			v2d->cur.ymin= 0.0f;
		}
	}

	/* validate that view is in valid configuration after this operation */
	UI_view2d_curRect_validate(v2d);
	
	/* request updates to be done... */
	ED_region_tag_redraw(ar);
	UI_view2d_sync(CTX_wm_screen(C), CTX_wm_area(C), v2d, V2D_LOCK_COPY);
	
	return OPERATOR_FINISHED;
}
 
static void VIEW2D_OT_reset(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Reset View";
	ot->description= "Reset the view";
	ot->idname= "VIEW2D_OT_reset";
	
	/* api callbacks */
	ot->exec= reset_exec;
	ot->poll= view2d_poll;
}
 
/* ********************************************************* */
/* Registration */

void UI_view2d_operatortypes(void)
{
	WM_operatortype_append(VIEW2D_OT_pan);
	
	WM_operatortype_append(VIEW2D_OT_scroll_left);
	WM_operatortype_append(VIEW2D_OT_scroll_right);
	WM_operatortype_append(VIEW2D_OT_scroll_up);
	WM_operatortype_append(VIEW2D_OT_scroll_down);
	
	WM_operatortype_append(VIEW2D_OT_zoom_in);
	WM_operatortype_append(VIEW2D_OT_zoom_out);
	
	WM_operatortype_append(VIEW2D_OT_zoom);
	WM_operatortype_append(VIEW2D_OT_zoom_border);
	
	WM_operatortype_append(VIEW2D_OT_scroller_activate);

	WM_operatortype_append(VIEW2D_OT_reset);
}

void UI_view2d_keymap(wmKeyConfig *keyconf)
{
	wmKeyMap *keymap= WM_keymap_find(keyconf, "View2D", 0, 0);
	
	/* pan/scroll */
	WM_keymap_add_item(keymap, "VIEW2D_OT_pan", MIDDLEMOUSE, KM_PRESS, 0, 0);
	WM_keymap_add_item(keymap, "VIEW2D_OT_pan", MIDDLEMOUSE, KM_PRESS, KM_SHIFT, 0);
	
	WM_keymap_add_item(keymap, "VIEW2D_OT_pan", MOUSEPAN, 0, 0, 0);
	
	WM_keymap_add_item(keymap, "VIEW2D_OT_scroll_right", WHEELDOWNMOUSE, KM_PRESS, KM_CTRL, 0);
	WM_keymap_add_item(keymap, "VIEW2D_OT_scroll_left", WHEELUPMOUSE, KM_PRESS, KM_CTRL, 0);
	
	WM_keymap_add_item(keymap, "VIEW2D_OT_scroll_down", WHEELDOWNMOUSE, KM_PRESS, KM_SHIFT, 0);
	WM_keymap_add_item(keymap, "VIEW2D_OT_scroll_up", WHEELUPMOUSE, KM_PRESS, KM_SHIFT, 0);
	
	/* zoom - single step */
	WM_keymap_add_item(keymap, "VIEW2D_OT_zoom_out", WHEELOUTMOUSE, KM_PRESS, 0, 0);
	WM_keymap_add_item(keymap, "VIEW2D_OT_zoom_in", WHEELINMOUSE, KM_PRESS, 0, 0);
	WM_keymap_add_item(keymap, "VIEW2D_OT_zoom_out", PADMINUS, KM_PRESS, 0, 0);
	WM_keymap_add_item(keymap, "VIEW2D_OT_zoom_in", PADPLUSKEY, KM_PRESS, 0, 0);
	
	/* scroll up/down - no modifiers, only when zoom fails */
		/* these may fail if zoom is disallowed, in which case they should pass on event */
	WM_keymap_add_item(keymap, "VIEW2D_OT_scroll_down", WHEELDOWNMOUSE, KM_PRESS, 0, 0);
	WM_keymap_add_item(keymap, "VIEW2D_OT_scroll_up", WHEELUPMOUSE, KM_PRESS, 0, 0);
		/* these may be necessary if vertical scroll is disallowed */
	WM_keymap_add_item(keymap, "VIEW2D_OT_scroll_right", WHEELDOWNMOUSE, KM_PRESS, 0, 0);
	WM_keymap_add_item(keymap, "VIEW2D_OT_scroll_left", WHEELUPMOUSE, KM_PRESS, 0, 0);
	
	/* alternatives for page up/down to scroll */
#if 0 // XXX disabled, since this causes conflicts with hotkeys in animation editors
		/* scroll up/down may fall through to left/right */
	WM_keymap_add_item(keymap, "VIEW2D_OT_scroll_down", PAGEDOWNKEY, KM_PRESS, 0, 0);
	WM_keymap_add_item(keymap, "VIEW2D_OT_scroll_up", PAGEUPKEY, KM_PRESS, 0, 0);
	WM_keymap_add_item(keymap, "VIEW2D_OT_scroll_right", PAGEDOWNKEY, KM_PRESS, 0, 0);
	WM_keymap_add_item(keymap, "VIEW2D_OT_scroll_left", PAGEUPKEY, KM_PRESS, 0, 0);
		/* shift for moving view left/right with page up/down */
	WM_keymap_add_item(keymap, "VIEW2D_OT_scroll_right", PAGEDOWNKEY, KM_PRESS, KM_SHIFT, 0);
	WM_keymap_add_item(keymap, "VIEW2D_OT_scroll_left", PAGEUPKEY, KM_PRESS, KM_SHIFT, 0);
#endif
	
	/* zoom - drag */
	WM_keymap_add_item(keymap, "VIEW2D_OT_zoom", MIDDLEMOUSE, KM_PRESS, KM_CTRL, 0);
	WM_keymap_add_item(keymap, "VIEW2D_OT_zoom", MOUSEZOOM, 0, 0, 0);
	
	/* borderzoom - drag */
	WM_keymap_add_item(keymap, "VIEW2D_OT_zoom_border", BKEY, KM_PRESS, KM_SHIFT, 0);
	
	/* scrollers */
	WM_keymap_add_item(keymap, "VIEW2D_OT_scroller_activate", LEFTMOUSE, KM_PRESS, 0, 0);

	/* Alternative keymap for buttons listview */
	keymap= WM_keymap_find(keyconf, "View2D Buttons List", 0, 0);
	WM_keymap_add_item(keymap, "VIEW2D_OT_pan", MIDDLEMOUSE, KM_PRESS, 0, 0);
	WM_keymap_add_item(keymap, "VIEW2D_OT_pan", MOUSEPAN, 0, 0, 0);
	WM_keymap_add_item(keymap, "VIEW2D_OT_scroll_down", WHEELDOWNMOUSE, KM_PRESS, 0, 0);
	WM_keymap_add_item(keymap, "VIEW2D_OT_scroll_up", WHEELUPMOUSE, KM_PRESS, 0, 0);
	
	RNA_boolean_set(WM_keymap_add_item(keymap, "VIEW2D_OT_scroll_down", PAGEDOWNKEY, KM_PRESS, 0, 0)->ptr, "page", 1);
	RNA_boolean_set(WM_keymap_add_item(keymap, "VIEW2D_OT_scroll_up", PAGEUPKEY, KM_PRESS, 0, 0)->ptr, "page", 1);
	
	WM_keymap_add_item(keymap, "VIEW2D_OT_zoom", MIDDLEMOUSE, KM_PRESS, KM_CTRL, 0);
	WM_keymap_add_item(keymap, "VIEW2D_OT_zoom", MOUSEZOOM, 0, 0, 0);
	WM_keymap_add_item(keymap, "VIEW2D_OT_zoom_out", PADMINUS, KM_PRESS, 0, 0);
	WM_keymap_add_item(keymap, "VIEW2D_OT_zoom_in", PADPLUSKEY, KM_PRESS, 0, 0);
	WM_keymap_add_item(keymap, "VIEW2D_OT_reset", HOMEKEY, KM_PRESS, 0, 0);
	WM_keymap_add_item(keymap, "VIEW2D_OT_scroller_activate", LEFTMOUSE, KM_PRESS, 0, 0);
}


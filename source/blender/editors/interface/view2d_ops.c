/**
 * $Id$
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
 * The Original Code is Copyright (C) 2008 Blender Foundation.
 * All rights reserved.
 * 
 * Contributor(s): Blender Foundation, Joshua Leung
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#include <math.h>

#include "MEM_guardedalloc.h"

#include "DNA_scene_types.h"
#include "DNA_screen_types.h"
#include "DNA_space_types.h"
#include "DNA_view2d_types.h"

#include "BLI_blenlib.h"

#include "BKE_global.h"
#include "BKE_utildefines.h"

#include "RNA_access.h"
#include "RNA_define.h"

#include "WM_api.h"
#include "WM_types.h"

#include "BIF_gl.h"

#include "UI_resources.h"
#include "UI_view2d.h"

/* ********************************************************* */
/* General Polling Funcs */

/* Check if mouse is within scrollbars 
 *	- Returns appropriate code for match
 *		'h' = in horizontal scrollbar
 *		'v' = in vertical scrollbar
 *		0 = not in scrollbar
 *	
 *	- x,y	= mouse coordinates in screen (not region) space
 */
static short mouse_in_v2d_scrollers (const bContext *C, View2D *v2d, int x, int y)
{
	ARegion *ar= C->region;
	int co[2];
	
	/* clamp x,y to region-coordinates first */
	co[0]= x - ar->winrct.xmin;
	co[1]= y - ar->winrct.ymin;
	
	/* check if within scrollbars */
	if (v2d->scroll & (V2D_SCROLL_HORIZONTAL|V2D_SCROLL_HORIZONTAL_O)) {
		if (IN_2D_HORIZ_SCROLL(v2d, co)) return 'h';
	}
	if (v2d->scroll & V2D_SCROLL_VERTICAL) {
		if (IN_2D_VERT_SCROLL(v2d, co)) return 'v';
	}	
	
	/* not found */
	return 0;
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
	View2D *v2d;			/* view2d we're operating in */
	
	float facx, facy;		/* amount to move view relative to zoom */
	
		/* options for version 1 */
	int startx, starty;		/* mouse x/y values in window when operator was initiated */
	int lastx, lasty;		/* previous x/y values of mouse in window */
	
	short in_scroller;		/* for MMB in scrollers (old feature in past, but now not that useful) */
} v2dViewPanData;
 
/* initialise panning customdata */
static int view_pan_init(bContext *C, wmOperator *op)
{
	v2dViewPanData *vpd;
	ARegion *ar;
	View2D *v2d;
	float winx, winy;
	
	/* regions now have v2d-data by default, so check for region */
	if (C->region == NULL)
		return 0;
	ar= C->region;
	
	/* set custom-data for operator */
	vpd= MEM_callocN(sizeof(v2dViewPanData), "v2dViewPanData");
	op->customdata= vpd;
	
	/* set pointers to owners */
	vpd->v2d= v2d= &ar->v2d;
	
	/* calculate translation factor - based on size of view */
	winx= (float)(ar->winrct.xmax - ar->winrct.xmin);
	winy= (float)(ar->winrct.ymax - ar->winrct.ymin);
	vpd->facx= (v2d->cur.xmax - v2d->cur.xmin) / winx;
	vpd->facy= (v2d->cur.ymax - v2d->cur.ymin) / winy;
	
	return 1;
}

/* apply transform to view (i.e. adjust 'cur' rect) */
static void view_pan_apply(bContext *C, wmOperator *op)
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
	UI_view2d_status_enforce(v2d);
	
	/* request updates to be done... */
	WM_event_add_notifier(C, WM_NOTE_AREA_REDRAW, 0, NULL);
	/* XXX: add WM_NOTE_TIME_CHANGED? */
}

/* cleanup temp customdata  */
static void view_pan_exit(bContext *C, wmOperator *op)
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
	
	view_pan_apply(C, op);
	view_pan_exit(C, op);
	return OPERATOR_FINISHED;
}

/* set up modal operator and relevant settings */
static int view_pan_invoke(bContext *C, wmOperator *op, wmEvent *event)
{
	v2dViewPanData *vpd;
	View2D *v2d;
	
	/* set up customdata */
	if (!view_pan_init(C, op))
		return OPERATOR_CANCELLED;
	
	vpd= op->customdata;
	v2d= vpd->v2d;
	
	/* set initial settings */
	vpd->startx= vpd->lastx= event->x;
	vpd->starty= vpd->lasty= event->y;
	RNA_int_set(op->ptr, "deltax", 0);
	RNA_int_set(op->ptr, "deltay", 0);
	
	vpd->in_scroller= mouse_in_v2d_scrollers(C, v2d, event->x, event->y);
	
#if 0 // XXX - enable this when cursors are working properly
	if (v2d->keepofs & V2D_LOCKOFS_X)
		WM_set_cursor(C, BC_NS_SCROLLCURSOR);
	else if (v2d->keepofs & V2D_LOCKOFS_Y)
		WM_set_cursor(C, BC_EW_SCROLLCURSOR);
	else
		WM_set_cursor(C, BC_NSEW_SCROLLCURSOR);
#endif // XXX - enable this when cursors are working properly
	
	/* add temp handler */
	WM_event_add_modal_handler(C, &C->window->handlers, op);

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
			switch (vpd->in_scroller) {
				case 'h': /* horizontal scrollbar - so only horizontal scroll (inverse direction) */
					RNA_int_set(op->ptr, "deltax", (event->x - vpd->lastx));
					RNA_int_set(op->ptr, "deltay", 0);
					break;
				case 'v': /* vertical scrollbar - so only vertical scroll (inverse direction) */
					RNA_int_set(op->ptr, "deltax", 0);
					RNA_int_set(op->ptr, "deltay", (event->y - vpd->lasty));
					break;
				default:
					RNA_int_set(op->ptr, "deltax", (vpd->lastx - event->x));
					RNA_int_set(op->ptr, "deltay", (vpd->lasty - event->y));
					break;
			}
			
			vpd->lastx= event->x;
			vpd->lasty= event->y;
			
			view_pan_apply(C, op);
		}
			break;
			
		case MIDDLEMOUSE:
			if (event->val==0) {
				/* calculate overall delta mouse-movement for redo */
				switch (vpd->in_scroller) {
					case 'h': /* horizontal scrollbar - so only horizontal scroll (inverse direction) */
						RNA_int_set(op->ptr, "deltax", (vpd->lastx - vpd->startx));
						RNA_int_set(op->ptr, "deltay", 0);
						break;
					case 'v': /* vertical scrollbar - so only vertical scroll (inverse direction) */
						RNA_int_set(op->ptr, "deltax", 0);
						RNA_int_set(op->ptr, "deltay", (vpd->lasty - vpd->starty));
						break;
					default:
						RNA_int_set(op->ptr, "deltax", (vpd->startx - vpd->lastx));
						RNA_int_set(op->ptr, "deltay", (vpd->starty - vpd->lasty));
						break;
				}
				RNA_int_set(op->ptr, "deltax", (vpd->startx - vpd->lastx));
				RNA_int_set(op->ptr, "deltay", (vpd->starty - vpd->lasty));
				
				view_pan_exit(C, op);
				//WM_set_cursor(C, CURSOR_STD);		// XXX - enable this when cursors are working properly	
				
				return OPERATOR_FINISHED;
			}
			break;
	}

	return OPERATOR_RUNNING_MODAL;
}

void ED_View2D_OT_view_pan(wmOperatorType *ot)
{
	PropertyRNA *prop;
	
	/* identifiers */
	ot->name= "Pan View";
	ot->idname= "ED_View2D_OT_view_pan";
	
	/* api callbacks */
	ot->exec= view_pan_exec;
	ot->invoke= view_pan_invoke;
	ot->modal= view_pan_modal;
	
	/* operator is repeatable */
	ot->flag= OPTYPE_REGISTER;
	
	/* rna - must keep these in sync with the other operators */
	prop= RNA_def_property(ot->srna, "deltax", PROP_INT, PROP_NONE);
	prop= RNA_def_property(ot->srna, "deltay", PROP_INT, PROP_NONE);
}

/* ------------------ Scrollwheel Versions (2) ---------------------- */

/* this operator only needs this single callback, where it callsthe view_pan_*() methods */
static int view_scrollright_exec(bContext *C, wmOperator *op)
{
	/* initialise default settings (and validate if ok to run) */
	if (!view_pan_init(C, op))
		return OPERATOR_CANCELLED;
	
	/* set RNA-Props - only movement in positive x-direction */
	RNA_int_set(op->ptr, "deltax", 20);
	RNA_int_set(op->ptr, "deltay", 0);
	
	/* apply movement, then we're done */
	view_pan_apply(C, op);
	view_pan_exit(C, op);
	
	return OPERATOR_FINISHED;
}

void ED_View2D_OT_view_scrollright(wmOperatorType *ot)
{
	PropertyRNA *prop;
	
	/* identifiers */
	ot->name= "Scroll Right";
	ot->idname= "ED_View2D_OT_view_rightscroll";
	
	/* api callbacks */
	ot->exec= view_scrollright_exec;
	
	/* operator is repeatable */
	ot->flag= OPTYPE_REGISTER;
	
	/* rna - must keep these in sync with the other operators */
	prop= RNA_def_property(ot->srna, "deltax", PROP_INT, PROP_NONE);
	prop= RNA_def_property(ot->srna, "deltay", PROP_INT, PROP_NONE);
}



/* this operator only needs this single callback, where it callsthe view_pan_*() methods */
static int view_scrollleft_exec(bContext *C, wmOperator *op)
{
	/* initialise default settings (and validate if ok to run) */
	if (!view_pan_init(C, op))
		return OPERATOR_CANCELLED;
	
	/* set RNA-Props - only movement in negative x-direction */
	RNA_int_set(op->ptr, "deltax", -20);
	RNA_int_set(op->ptr, "deltay", 0);
	
	/* apply movement, then we're done */
	view_pan_apply(C, op);
	view_pan_exit(C, op);
	
	return OPERATOR_FINISHED;
}

void ED_View2D_OT_view_scrollleft(wmOperatorType *ot)
{
	PropertyRNA *prop;
	
	/* identifiers */
	ot->name= "Scroll Left";
	ot->idname= "ED_View2D_OT_view_leftscroll";
	
	/* api callbacks */
	ot->exec= view_scrollleft_exec;
	
	/* operator is repeatable */
	ot->flag= OPTYPE_REGISTER;
	
	/* rna - must keep these in sync with the other operators */
	prop= RNA_def_property(ot->srna, "deltax", PROP_INT, PROP_NONE);
	prop= RNA_def_property(ot->srna, "deltay", PROP_INT, PROP_NONE);
}

/* this operator only needs this single callback, where it callsthe view_pan_*() methods */
static int view_scrolldown_exec(bContext *C, wmOperator *op)
{
	/* initialise default settings (and validate if ok to run) */
	if (!view_pan_init(C, op))
		return OPERATOR_CANCELLED;
	
	/* set RNA-Props - only movement in positive x-direction */
	RNA_int_set(op->ptr, "deltax", 0);
	RNA_int_set(op->ptr, "deltay", -20);
	
	/* apply movement, then we're done */
	view_pan_apply(C, op);
	view_pan_exit(C, op);
	
	return OPERATOR_FINISHED;
}

void ED_View2D_OT_view_scrolldown(wmOperatorType *ot)
{
	PropertyRNA *prop;
	
	/* identifiers */
	ot->name= "Scroll Down";
	ot->idname= "ED_View2D_OT_view_downscroll";
	
	/* api callbacks */
	ot->exec= view_scrolldown_exec;
	
	/* operator is repeatable */
	ot->flag= OPTYPE_REGISTER;
	
	/* rna - must keep these in sync with the other operators */
	prop= RNA_def_property(ot->srna, "deltax", PROP_INT, PROP_NONE);
	prop= RNA_def_property(ot->srna, "deltay", PROP_INT, PROP_NONE);
}



/* this operator only needs this single callback, where it callsthe view_pan_*() methods */
static int view_scrollup_exec(bContext *C, wmOperator *op)
{
	/* initialise default settings (and validate if ok to run) */
	if (!view_pan_init(C, op))
		return OPERATOR_CANCELLED;
	
	/* set RNA-Props - only movement in negative x-direction */
	RNA_int_set(op->ptr, "deltax", 0);
	RNA_int_set(op->ptr, "deltay", 20);
	
	/* apply movement, then we're done */
	view_pan_apply(C, op);
	view_pan_exit(C, op);
	
	return OPERATOR_FINISHED;
}

void ED_View2D_OT_view_scrollup(wmOperatorType *ot)
{
	PropertyRNA *prop;
	
	/* identifiers */
	ot->name= "Scroll Up";
	ot->idname= "ED_View2D_OT_view_upscroll";
	
	/* api callbacks */
	ot->exec= view_scrollup_exec;
	
	/* operator is repeatable */
	ot->flag= OPTYPE_REGISTER;
	
	/* rna - must keep these in sync with the other operators */
	prop= RNA_def_property(ot->srna, "deltax", PROP_INT, PROP_NONE);
	prop= RNA_def_property(ot->srna, "deltay", PROP_INT, PROP_NONE);
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
 
/* apply transform to view (i.e. adjust 'cur' rect) */
static void view_zoom_apply(bContext *C, wmOperator *op)
{
	View2D *v2d= &C->region->v2d;
	float dx, dy;
	
	/* calculate amount to move view by */
	dx= (v2d->cur.xmax - v2d->cur.xmin) * (float)RNA_float_get(op->ptr, "zoomfacx");
	dy= (v2d->cur.ymax - v2d->cur.ymin) * (float)RNA_float_get(op->ptr, "zoomfacy");
	
	/* only move view on an axis if change is allowed */
	if ((v2d->keepofs & V2D_LOCKOFS_X)==0) {
		v2d->cur.xmin += dx;
		v2d->cur.xmax -= dx;
	}
	if ((v2d->keepofs & V2D_LOCKOFS_Y)==0) {
		v2d->cur.ymin += dy;
		v2d->cur.ymax -= dy;
	}
	
	/* validate that view is in valid configuration after this operation */
	UI_view2d_status_enforce(v2d);
	
	/* request updates to be done... */
	WM_event_add_notifier(C, WM_NOTE_AREA_REDRAW, 0, NULL);
	/* XXX: add WM_NOTE_TIME_CHANGED? */
}

/* --------------- Individual Operators ------------------- */

/* this operator only needs this single callback, where it calls the view_zoom_*() methods */
static int view_zoomin_exec(bContext *C, wmOperator *op)
{
	/* check that there's an active region, as View2D data resides there */
	if (C->region == NULL)
		return OPERATOR_CANCELLED;
	
	/* set RNA-Props - zooming in by uniform factor */
	RNA_float_set(op->ptr, "zoomfacx", 0.0375f);
	RNA_float_set(op->ptr, "zoomfacy", 0.0375f);
	
	/* apply movement, then we're done */
	view_zoom_apply(C, op);
	
	return OPERATOR_FINISHED;
}

void ED_View2D_OT_view_zoomin(wmOperatorType *ot)
{
	PropertyRNA *prop;
	
	/* identifiers */
	ot->name= "Zoom In";
	ot->idname= "ED_View2D_OT_view_zoomin";
	
	/* api callbacks */
	ot->exec= view_zoomin_exec;
	
	/* operator is repeatable */
	ot->flag= OPTYPE_REGISTER;
	
	/* rna - must keep these in sync with the other operators */
	prop= RNA_def_property(ot->srna, "zoomfacx", PROP_FLOAT, PROP_NONE);
	prop= RNA_def_property(ot->srna, "zoomfacy", PROP_FLOAT, PROP_NONE);
}



/* this operator only needs this single callback, where it callsthe view_zoom_*() methods */
static int view_zoomout_exec(bContext *C, wmOperator *op)
{
	/* check that there's an active region, as View2D data resides there */
	if (C->region == NULL)
		return OPERATOR_CANCELLED;
	
	/* set RNA-Props - zooming in by uniform factor */
	RNA_float_set(op->ptr, "zoomfacx", -0.0375f);
	RNA_float_set(op->ptr, "zoomfacy", -0.0375f);
	
	/* apply movement, then we're done */
	view_zoom_apply(C, op);
	
	return OPERATOR_FINISHED;
}

void ED_View2D_OT_view_zoomout(wmOperatorType *ot)
{
	PropertyRNA *prop;
	
	/* identifiers */
	ot->name= "Zoom Out";
	ot->idname= "ED_View2D_OT_view_zoomout";
	
	/* api callbacks */
	ot->exec= view_zoomout_exec;
	
	/* operator is repeatable */
	ot->flag= OPTYPE_REGISTER;
	
	/* rna - must keep these in sync with the other operators */
	prop= RNA_def_property(ot->srna, "zoomfacx", PROP_FLOAT, PROP_NONE);
	prop= RNA_def_property(ot->srna, "zoomfacy", PROP_FLOAT, PROP_NONE);
}

/* ********************************************************* */
/* Scrollers */

/* customdata for scroller-invoke data */
typedef struct v2dScrollerMove {
	View2D *v2d;			/* View2D data that this operation affects */
	
	short scroller;			/* scroller that mouse is in ('h' or 'v') */
	short zone;				/* -1 is min zoomer, 0 is bar, 1 is max zoomer */ // XXX find some way to provide visual feedback of this (active colour?)
	
	float fac;				/* view adjustment factor, based on size of region */
	float delta;			/* amount moved by mouse on axis of interest */
	
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
	SCROLLHANDLE_MAX
} eV2DScrollerHandle_Zone;

/* ------------------------ */

/* check if mouse is within scroller handle 
 *	- mouse			= 	relevant mouse coordinate in region space
 *	- sc_min, sc_max	= 	extents of scroller
 *	- sh_min, sh_max	= 	positions of scroller handles
 */
static short mouse_in_scroller_handle(int mouse, int sc_min, int sc_max, int sh_min, int sh_max)
{
	short in_min, in_max;
	
	/* firstly, check if 'bubble' fills entire scroller */
	// XXX this isn't so good for anim-editors...
	if ((sh_min <= sc_min) && (sh_max >= sc_max)) {
		/* use midpoint to determine which handle to use (favour 'max' handle) */
		if (mouse >= ((sc_max + sc_min) / 2)) 
			return SCROLLHANDLE_MAX;
		else
			return SCROLLHANDLE_MIN;
	}
	
	/* check if mouse is in or past either handle */
	in_max= (mouse >= (sh_max - V2D_SCROLLER_HANDLE_SIZE));
	in_min= (mouse <= (sh_min + V2D_SCROLLER_HANDLE_SIZE));
	
	/* check if overlap --> which means user clicked on bar, as bar is within handles region */
	if (in_max && in_min)
		return SCROLLHANDLE_BAR;
	if (in_max)
		return SCROLLHANDLE_MAX;
	else if (in_min)
		return SCROLLHANDLE_MIN;
		
	/* unlikely to happen, though we just cover it in case */
	else
		return SCROLLHANDLE_BAR;
} 

/* initialise customdata for scroller manipulation operator */
static void scroller_activate_init(bContext *C, wmOperator *op, wmEvent *event, short in_scroller)
{
	v2dScrollerMove *vsm;
	View2DScrollers *scrollers;
	ARegion *ar= C->region;
	View2D *v2d= &ar->v2d;
	float mask_size;
	int x, y;
	
	/* set custom-data for operator */
	vsm= MEM_callocN(sizeof(v2dScrollerMove), "v2dScrollerMove");
	op->customdata= vsm;
	
	/* set general data */
	vsm->v2d= v2d;
	vsm->scroller= in_scroller;
	
	/* store mouse-coordinates, and convert mouse/screen coordinates to region coordinates */
	vsm->lastx = event->x;
	vsm->lasty = event->y;
	x= event->x - ar->winrct.xmin;
	y= event->y - ar->winrct.ymin;
	
	/* 'zone' depends on where mouse is relative to bubble 
	 *	- zooming must be allowed on this axis, otherwise, default to pan
	 */
	scrollers= UI_view2d_scrollers_calc(C, v2d, V2D_ARG_DUMMY, V2D_ARG_DUMMY, V2D_ARG_DUMMY, V2D_ARG_DUMMY);
	if (in_scroller == 'h') {
		/* horizontal scroller - calculate adjustment factor first */
		mask_size= (float)(v2d->hor.xmax - v2d->hor.xmin);
		vsm->fac= (v2d->tot.xmax - v2d->tot.xmin) / mask_size;
		
		/* get 'zone' (i.e. which part of scroller is activated) */
		if (v2d->keepzoom & V2D_LOCKZOOM_X) {
			/* default to scroll, as handles not usable */
			vsm->zone= SCROLLHANDLE_BAR;
		}
		else {
			/* check which handle we're in */
			vsm->zone= mouse_in_scroller_handle(x, v2d->hor.xmin, v2d->hor.xmax, scrollers->hor_min, scrollers->hor_max); 
		}
	}
	else {
		/* vertical scroller - calculate adjustment factor first */
		mask_size= (float)(v2d->vert.ymax - v2d->vert.ymin);
		vsm->fac= (v2d->tot.ymax - v2d->tot.ymin) / mask_size;
		
		/* get 'zone' (i.e. which part of scroller is activated) */
		if (v2d->keepzoom & V2D_LOCKZOOM_Y) {
			/* default to scroll, as handles not usable */
			vsm->zone= SCROLLHANDLE_BAR;
		}
		else {
			/* check which handle we're in */
			vsm->zone= mouse_in_scroller_handle(y, v2d->vert.xmin, v2d->vert.xmax, scrollers->vert_min, scrollers->vert_max); 
		}
	}
	UI_view2d_scrollers_free(scrollers);
}

/* cleanup temp customdata  */
static void scroller_activate_exit(bContext *C, wmOperator *op)
{
	if (op->customdata) {
		MEM_freeN(op->customdata);
		op->customdata= NULL;				
	}
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
		
		default: /* SCROLLHANDLE_BAR */
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
	UI_view2d_status_enforce(v2d);
	
	/* request updates to be done... */
	WM_event_add_notifier(C, WM_NOTE_AREA_REDRAW, 0, NULL);
	/* XXX: add WM_NOTE_TIME_CHANGED? */
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
			if (vsm->zone != SCROLLHANDLE_MIN) {
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
			else {
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
			if (event->val==0) {
				scroller_activate_exit(C, op);
				return OPERATOR_FINISHED;
			}
			break;
	}

	return OPERATOR_RUNNING_MODAL;
}


/* a click (or click drag in progress) should have occurred, so check if it happened in scrollbar */
static int scroller_activate_invoke(bContext *C, wmOperator *op, wmEvent *event)
{
	View2D *v2d= NULL;
	short in_scroller= 0;
	
	/* firstly, check context to see if mouse is actually in region */
	// XXX isn't this the job of poll() callbacks which can't check events, but only context?
	if (C->region == NULL) 
		return OPERATOR_CANCELLED;
	else
		v2d= &C->region->v2d;
		
	/* check if mouse in scrollbars, if they're enabled */
	in_scroller= mouse_in_v2d_scrollers(C, v2d, event->x, event->y);
	
	/* if in a scroller, init customdata then set modal handler which will catch mousedown to start doing useful stuff */
	if (in_scroller) {
		v2dScrollerMove *vsm;
		
		/* initialise customdata */
		scroller_activate_init(C, op, event, in_scroller);
		vsm= (v2dScrollerMove *)op->customdata;
		
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
		
		/* still ok, so can add */
		WM_event_add_modal_handler(C, &C->window->handlers, op);
		return OPERATOR_RUNNING_MODAL;
	}
	else {
		/* not in scroller, so nothing happened... (pass through let's something else catch event) */
		return OPERATOR_PASS_THROUGH;
	}
}

/* LMB-Drag in Scrollers - not repeatable operator! */
void ED_View2D_OT_scroller_activate(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Scroller Activate";
	ot->idname= "ED_View2D_OT_scroller_activate";
	
	/* api callbacks */
	ot->invoke= scroller_activate_invoke;
	ot->modal= scroller_activate_modal;
}
 
/* ********************************************************* */
/* Registration */

void ui_view2d_operatortypes(void)
{
	WM_operatortype_append(ED_View2D_OT_view_pan);
	
	WM_operatortype_append(ED_View2D_OT_view_scrollleft);
	WM_operatortype_append(ED_View2D_OT_view_scrollright);
	WM_operatortype_append(ED_View2D_OT_view_scrollup);
	WM_operatortype_append(ED_View2D_OT_view_scrolldown);
	
	WM_operatortype_append(ED_View2D_OT_view_zoomin);
	WM_operatortype_append(ED_View2D_OT_view_zoomout);
	
	WM_operatortype_append(ED_View2D_OT_scroller_activate);
}

void UI_view2d_keymap(wmWindowManager *wm)
{
	ui_view2d_operatortypes();
	
	/* pan/scroll operators */
	WM_keymap_add_item(&wm->view2dkeymap, "ED_View2D_OT_view_pan", MIDDLEMOUSE, KM_PRESS, 0, 0);
	
	WM_keymap_add_item(&wm->view2dkeymap, "ED_View2D_OT_view_rightscroll", WHEELDOWNMOUSE, KM_ANY, KM_CTRL, 0);
	WM_keymap_add_item(&wm->view2dkeymap, "ED_View2D_OT_view_leftscroll", WHEELUPMOUSE, KM_ANY, KM_CTRL, 0);
	
	WM_keymap_add_item(&wm->view2dkeymap, "ED_View2D_OT_view_downscroll", WHEELDOWNMOUSE, KM_ANY, KM_SHIFT, 0);
	WM_keymap_add_item(&wm->view2dkeymap, "ED_View2D_OT_view_upscroll", WHEELUPMOUSE, KM_ANY, KM_SHIFT, 0);
	
	/* zoom - single step */
	WM_keymap_add_item(&wm->view2dkeymap, "ED_View2D_OT_view_zoomout", WHEELUPMOUSE, KM_ANY, 0, 0);
	WM_keymap_add_item(&wm->view2dkeymap, "ED_View2D_OT_view_zoomin", WHEELDOWNMOUSE, KM_ANY, 0, 0);
	WM_keymap_add_item(&wm->view2dkeymap, "ED_View2D_OT_view_zoomout", PADMINUS, KM_PRESS, 0, 0);
	WM_keymap_add_item(&wm->view2dkeymap, "ED_View2D_OT_view_zoomin", PADPLUSKEY, KM_PRESS, 0, 0);
	
	/* scrollers */
	WM_keymap_add_item(&wm->view2dkeymap, "ED_View2D_OT_scroller_activate", LEFTMOUSE, KM_PRESS, 0, 0);
}


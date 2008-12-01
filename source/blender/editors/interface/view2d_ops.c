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
/* VIEW PANNING OPERATOR								 */

/* 	This group of operators come in several forms:
 *		1) Modal 'dragging' with MMB - where movement of mouse dictates amount to pan view by
 *		2) Scrollwheel 'steps' - rolling mousewheel by one step moves view by predefined amount
 *		3) Scroller drag - similar to 1), but only while mouse is still in view
 *
 *	In order to make sure this works, each operator must define the following RNA-Operator Props:
 *		deltax, deltay 	- define how much to move view by (relative to zoom-correction factor)
 */

 /* ------------------ Shared 'core' stuff ---------------------- */
 
/* temp customdata for operator */
typedef struct v2dViewPanData {
	ARegion *region;		/* region we're operating in */
	View2D *v2d;			/* view2d we're operating in */
	
	float facx, facy;		/* amount to move view relative to zoom */
	
		/* options for version 1 */
	int startx, starty;		/* mouse x/y values in window when operator was initiated */
	int lastx, lasty;		/* previous x/y values of mouse in window */
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
	
	/* set custom-data for operator */
	vpd= MEM_callocN(sizeof(v2dViewPanData), "v2dViewPanData");
	op->customdata= vpd;
	
	/* set pointers to owners */
	vpd->region= ar= C->region;
	vpd->v2d= v2d= &C->region->v2d;
	
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
	
	/* request updates to be done... */
	WM_event_add_notifier(C->wm, C->window, 0, WM_NOTE_AREA_REDRAW, 0, NULL);
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
	
#if 0 // XXX - enable this when cursors are working properly
	if (v2d->keepofs & V2D_LOCKOFS_X)
		WM_set_cursor(C, BC_NS_SCROLLCURSOR);
	else if (v2d->keepofs & V2D_LOCKOFS_Y)
		WM_set_cursor(C, BC_EW_SCROLLCURSOR);
	else
		WM_set_cursor(C, BC_NSEW_SCROLLCURSOR);
#endif // XXX - enable this when cursors are working properly
	
	/* add temp handler */
	WM_event_add_modal_handler(&C->window->handlers, op);

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
			
			view_pan_apply(C, op);
		}
			break;
			
		case MIDDLEMOUSE:
			if (event->val==0) {
				/* calculate overall delta mouse-movement for redo */
				RNA_int_set(op->ptr, "deltax", (vpd->startx - vpd->lastx));
				RNA_int_set(op->ptr, "deltay", (vpd->starty - vpd->lasty));
				
				view_pan_exit(C, op);
				//WM_set_cursor(C, CURSOR_STD);		// XXX - enable this when cursors are working properly	
				WM_event_remove_modal_handler(&C->window->handlers, op);
				
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
	
	/* rna - must keep these in sync with the other operators */
	prop= RNA_def_property(ot->srna, "deltax", PROP_INT, PROP_NONE);
	prop= RNA_def_property(ot->srna, "deltay", PROP_INT, PROP_NONE);
}

/* ------------------ Scrollwheel Versions (2) ---------------------- */
// XXX should these be unified a bit?

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
	
	/* rna - must keep these in sync with the other operators */
	prop= RNA_def_property(ot->srna, "deltax", PROP_INT, PROP_NONE);
	prop= RNA_def_property(ot->srna, "deltay", PROP_INT, PROP_NONE);
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
}

void UI_view2d_keymap(wmWindowManager *wm)
{
	ui_view2d_operatortypes();
	
	/* pan/scroll operators */
	WM_keymap_add_item(&wm->view2dkeymap, "ED_View2D_OT_view_pan", MIDDLEMOUSE, KM_PRESS, 0, 0);
	
	WM_keymap_add_item(&wm->view2dkeymap, "ED_View2D_OT_view_rightscroll", WHEELDOWNMOUSE, KM_PRESS, KM_CTRL, 0);
	WM_keymap_add_item(&wm->view2dkeymap, "ED_View2D_OT_view_leftscroll", WHEELUPMOUSE, KM_PRESS, KM_CTRL, 0);
	
	WM_keymap_add_item(&wm->view2dkeymap, "ED_View2D_OT_view_downscroll", WHEELDOWNMOUSE, KM_PRESS, KM_SHIFT, 0);
	WM_keymap_add_item(&wm->view2dkeymap, "ED_View2D_OT_view_upscroll", WHEELUPMOUSE, KM_PRESS, KM_SHIFT, 0);
	
	/* zoom */
	
	/* scrollbars */
	//WM_keymap_add_item(&wm->view2dkeymap, "ED_V2D_OT_scrollbar_activate", MOUSEMOVE, 0, 0, 0);
}


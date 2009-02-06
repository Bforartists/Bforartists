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
 * Contributor(s): Blender Foundation
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#include <float.h>
#define _USE_MATH_DEFINES
#include <math.h>
#include <string.h>

#include "DNA_ID.h"
#include "DNA_screen_types.h"
#include "DNA_userdef_types.h"
#include "DNA_windowmanager_types.h"

#include "MEM_guardedalloc.h"

#include "BLI_blenlib.h"
#include "BLI_dynstr.h" /*for WM_operator_pystring */

#include "BKE_blender.h"
#include "BKE_context.h"
#include "BKE_idprop.h"
#include "BKE_library.h"
#include "BKE_global.h"
#include "BKE_main.h"
#include "BKE_utildefines.h"

#include "BIF_gl.h"
#include "BIF_glutil.h" /* for paint cursor */
#include "IMB_imbuf_types.h"

#include "ED_fileselect.h"
#include "ED_screen.h"

#include "RNA_access.h"
#include "RNA_define.h"

#include "UI_interface.h"
#include "UI_resources.h"

#include "WM_api.h"
#include "WM_types.h"

#include "wm.h"
#include "wm_window.h"
#include "wm_subwindow.h"
#include "wm_event_system.h"



static ListBase global_ops= {NULL, NULL};

/* ************ operator API, exported ********** */

wmOperatorType *WM_operatortype_find(const char *idname)
{
	wmOperatorType *ot;
	
	for(ot= global_ops.first; ot; ot= ot->next) {
		if(strncmp(ot->idname, idname, OP_MAX_TYPENAME)==0)
		   return ot;
	}
	printf("search for unknown operator %s\n", idname);
	return NULL;
}

wmOperatorType *WM_operatortype_first(void)
{
	return global_ops.first;
}

/* all ops in 1 list (for time being... needs evaluation later) */
void WM_operatortype_append(void (*opfunc)(wmOperatorType*))
{
	wmOperatorType *ot;
	
	ot= MEM_callocN(sizeof(wmOperatorType), "operatortype");
	ot->srna= RNA_def_struct(&BLENDER_RNA, "", "OperatorProperties");
	opfunc(ot);
	RNA_def_struct_ui_text(ot->srna, ot->name, "DOC_BROKEN"); /* TODO - add a discription to wmOperatorType? */
	RNA_def_struct_identifier(ot->srna, ot->idname);
	BLI_addtail(&global_ops, ot);
}

void WM_operatortype_append_ptr(void (*opfunc)(wmOperatorType*, void*), void *userdata)
{
	wmOperatorType *ot;

	ot= MEM_callocN(sizeof(wmOperatorType), "operatortype");
	ot->srna= RNA_def_struct(&BLENDER_RNA, "", "OperatorProperties");
	opfunc(ot, userdata);
	RNA_def_struct_ui_text(ot->srna, ot->name, "DOC_BROKEN"); /* TODO - add a discription to wmOperatorType? */
	RNA_def_struct_identifier(ot->srna, ot->idname);
	BLI_addtail(&global_ops, ot);
}

int WM_operatortype_remove(const char *idname)
{
	wmOperatorType *ot = WM_operatortype_find(idname);

	if (ot==NULL)
		return 0;
	
	BLI_remlink(&global_ops, ot);
	RNA_struct_free(&BLENDER_RNA, ot->srna);
	MEM_freeN(ot);

	return 1;
}

/* print a string representation of the operator, with the args that it runs 
 * so python can run it again */
char *WM_operator_pystring(wmOperator *op)
{
	const char *arg_name= NULL;

	PropertyRNA *prop, *iterprop;
	CollectionPropertyIterator iter;

	/* for building the string */
	DynStr *dynstr= BLI_dynstr_new();
	char *cstring, *buf;
	int first_iter=1;

	BLI_dynstr_appendf(dynstr, "%s(", op->idname);

	iterprop= RNA_struct_iterator_property(op->ptr);
	RNA_property_collection_begin(op->ptr, iterprop, &iter);

	for(; iter.valid; RNA_property_collection_next(&iter)) {
		prop= iter.ptr.data;
		arg_name= RNA_property_identifier(&iter.ptr, prop);

		if (strcmp(arg_name, "rna_type")==0) continue;

		buf= RNA_property_as_string(op->ptr, prop);
		
		BLI_dynstr_appendf(dynstr, first_iter?"%s=%s":", %s=%s", arg_name, buf);

		MEM_freeN(buf);
		first_iter = 0;
	}

	RNA_property_collection_end(&iter);

	BLI_dynstr_append(dynstr, ")");

	cstring = BLI_dynstr_get_cstring(dynstr);
	BLI_dynstr_free(dynstr);
	return cstring;
}

void WM_operator_properties_create(PointerRNA *ptr, const char *opstring)
{
	wmOperatorType *ot= WM_operatortype_find(opstring);

	if(ot)
		RNA_pointer_create(NULL, ot->srna, NULL, ptr);
	else
		RNA_pointer_create(NULL, &RNA_OperatorProperties, NULL, ptr);
}

void WM_operator_properties_free(PointerRNA *ptr)
{
	IDProperty *properties= ptr->data;

	if(properties) {
		IDP_FreeProperty(properties);
		MEM_freeN(properties);
	}
}

/* ************ default op callbacks, exported *********** */

/* invoke callback, uses enum property named "type" */
/* only weak thing is the fixed property name... */
int WM_menu_invoke(bContext *C, wmOperator *op, wmEvent *event)
{
	PropertyRNA *prop= RNA_struct_find_property(op->ptr, "type");
	uiMenuItem *head;

	if(prop==NULL) {
		printf("WM_menu_invoke: %s has no \"type\" enum property\n", op->type->idname);
	}
	else if (RNA_property_type(op->ptr, prop) != PROP_ENUM) {
		printf("WM_menu_invoke: %s \"type\" is not an enum property\n", op->type->idname);
	}
	else {
		head= uiPupMenuBegin(op->type->name, 0);
		uiMenuItemsEnumO(head, op->type->idname, "type");
		uiPupMenuEnd(C, head);
	}

	return OPERATOR_CANCELLED;
}

/* op->invoke */
int WM_operator_confirm(bContext *C, wmOperator *op, wmEvent *event)
{
	uiMenuItem *head;

	head= uiPupMenuBegin("OK?", ICON_HELP);
	uiMenuItemO(head, 0, op->type->idname);
	uiPupMenuEnd(C, head);
	
	return OPERATOR_CANCELLED;
}

/* op->invoke, opens fileselect if filename property not set, otherwise executes */
int WM_operator_filesel(bContext *C, wmOperator *op, wmEvent *event)
{
	if (RNA_property_is_set(op->ptr, "filename")) {
		return WM_operator_call(C, op);
	} else {
		SpaceFile *sfile;

		ED_screen_full_newspace(C, CTX_wm_area(C), SPACE_FILE);
		
		/* settings for filebrowser */
		sfile= (SpaceFile*)CTX_wm_space_data(C);
		sfile->op = op;
		ED_fileselect_set_params(sfile, FILE_BLENDER, op->type->name, "", 0, 0, 0);

		/* screen and area have been reset already in ED_screen_full_newspace */
		return OPERATOR_RUNNING_MODAL;
	}
}

/* op->poll */
int WM_operator_winactive(bContext *C)
{
	if(CTX_wm_window(C)==NULL) return 0;
	return 1;
}

/* ************ window / screen operator definitions ************** */

static void WM_OT_window_duplicate(wmOperatorType *ot)
{
	ot->name= "Duplicate Window";
	ot->idname= "WM_OT_window_duplicate";
	
	ot->invoke= WM_operator_confirm;
	ot->exec= wm_window_duplicate_op;
	ot->poll= WM_operator_winactive;
}

static void WM_OT_save_homefile(wmOperatorType *ot)
{
	ot->name= "Save User Settings";
	ot->idname= "WM_OT_save_homefile";
	
	ot->invoke= WM_operator_confirm;
	ot->exec= WM_write_homefile;
	ot->poll= WM_operator_winactive;
}

/* ********* recent file *********** */

static int recentfile_exec(bContext *C, wmOperator *op)
{
	int event= RNA_enum_get(op->ptr, "nr");

	// XXX wm in context is not set correctly after WM_read_file -> crash
	// do it before for now, but is this correct with multiple windows?

	if(event>0) {
		if (G.sce[0] && (event==1)) {
			WM_event_add_notifier(C, NC_WINDOW, NULL);
			WM_read_file(C, G.sce, op->reports);
		}
		else {
			struct RecentFile *recent = BLI_findlink(&(G.recent_files), event-2);
			if(recent) {
				WM_event_add_notifier(C, NC_WINDOW, NULL);
				WM_read_file(C, recent->filename, op->reports);
			}
		}
	}
	return 0;
}

static int wm_recentfile_invoke(bContext *C, wmOperator *op, wmEvent *event)
{
	struct RecentFile *recent;
	uiMenuItem *head;
	int i, ofs= 0;

	head= uiPupMenuBegin("Open Recent", 0);

	if(G.sce[0]) {
		uiMenuItemIntO(head, G.sce, 0, op->type->idname, "nr", 1);
		ofs = 1;
	}
	
	for(recent = G.recent_files.first, i=0; (i<U.recent_files) && (recent); recent = recent->next, i++)
		if(strcmp(recent->filename, G.sce))
			uiMenuItemIntO(head, recent->filename, 0, op->type->idname, "nr", i+ofs+1);

	uiPupMenuEnd(C, head);
	
	return OPERATOR_CANCELLED;
}

static void WM_OT_open_recentfile(wmOperatorType *ot)
{
	ot->name= "Open Recent File";
	ot->idname= "WM_OT_open_recentfile";
	
	ot->invoke= wm_recentfile_invoke;
	ot->exec= recentfile_exec;
	ot->poll= WM_operator_winactive;
	
	RNA_def_property(ot->srna, "nr", PROP_ENUM, PROP_NONE);
}

/* ********* main file *********** */

static int wm_mainfile_invoke(bContext *C, wmOperator *op, wmEvent *event)
{
	SpaceFile *sfile;
	
	ED_screen_full_newspace(C, CTX_wm_area(C), SPACE_FILE);

	/* settings for filebrowser */
	sfile= (SpaceFile*)CTX_wm_space_data(C);
	sfile->op = op;
	// XXX replace G.sce
	ED_fileselect_set_params(sfile, FILE_BLENDER, "Load", G.sce, 0, 0, 0);

	/* screen and area have been reset already in ED_screen_full_newspace */

	return OPERATOR_RUNNING_MODAL;
}

static int wm_mainfile_exec(bContext *C, wmOperator *op)
{
	char filename[FILE_MAX];
	RNA_string_get(op->ptr, "filename", filename);
	
	// XXX wm in context is not set correctly after WM_read_file -> crash
	// do it before for now, but is this correct with multiple windows?
	WM_event_add_notifier(C, NC_WINDOW, NULL);

	WM_read_file(C, filename, op->reports);
	
	return 0;
}

static void WM_OT_open_mainfile(wmOperatorType *ot)
{
	ot->name= "Open Blender File";
	ot->idname= "WM_OT_open_mainfile";
	
	ot->invoke= wm_mainfile_invoke;
	ot->exec= wm_mainfile_exec;
	ot->poll= WM_operator_winactive;
	
	ot->flag= 0;
	
	RNA_def_property(ot->srna, "filename", PROP_STRING, PROP_FILEPATH);

}

static int wm_save_as_mainfile_invoke(bContext *C, wmOperator *op, wmEvent *event)
{
	SpaceFile *sfile;
	
	ED_screen_full_newspace(C, CTX_wm_area(C), SPACE_FILE);

	/* settings for filebrowser */
	sfile= (SpaceFile*)CTX_wm_space_data(C);
	sfile->op = op;
	// XXX replace G.sce
	ED_fileselect_set_params(sfile, FILE_BLENDER, "Save As", G.sce, 0, 0, 0);

	/* screen and area have been reset already in ED_screen_full_newspace */

	return OPERATOR_RUNNING_MODAL;
}

static int wm_save_as_mainfile_exec(bContext *C, wmOperator *op)
{
	char filename[FILE_MAX];
	RNA_string_get(op->ptr, "filename", filename);
	
	WM_write_file(C, filename, op->reports);
	
	WM_event_add_notifier(C, NC_WINDOW, NULL);

	return 0;
}

static void WM_OT_save_as_mainfile(wmOperatorType *ot)
{
	ot->name= "Open Blender File";
	ot->idname= "WM_OT_save_as_mainfile";
	
	ot->invoke= wm_save_as_mainfile_invoke;
	ot->exec= wm_save_as_mainfile_exec;
	ot->poll= WM_operator_winactive;
	
	ot->flag= 0;
	
	RNA_def_property(ot->srna, "filename", PROP_STRING, PROP_FILEPATH);

}

/* *********************** */

static void WM_OT_window_fullscreen_toggle(wmOperatorType *ot)
{
    ot->name= "Toggle Fullscreen";
    ot->idname= "WM_OT_window_fullscreen_toggle";

    ot->invoke= WM_operator_confirm;
    ot->exec= wm_window_fullscreen_toggle_op;
    ot->poll= WM_operator_winactive;
}

static int wm_exit_blender_op(bContext *C, wmOperator *op)
{
	WM_operator_free(op);
	
	WM_exit(C);	
	
	return OPERATOR_FINISHED;
}

static void WM_OT_exit_blender(wmOperatorType *ot)
{
	ot->name= "Exit Blender";
	ot->idname= "WM_OT_exit_blender";

	ot->invoke= WM_operator_confirm;
	ot->exec= wm_exit_blender_op;
	ot->poll= WM_operator_winactive;
}

/* ************ default paint cursors, draw always around cursor *********** */
/*
 - returns handler to free 
 - poll(bContext): returns 1 if draw should happen
 - draw(bContext): drawing callback for paint cursor
*/

void *WM_paint_cursor_activate(wmWindowManager *wm, int (*poll)(bContext *C),
			       void (*draw)(bContext *C, int, int, void *customdata), void *customdata)
{
	wmPaintCursor *pc= MEM_callocN(sizeof(wmPaintCursor), "paint cursor");
	
	BLI_addtail(&wm->paintcursors, pc);
	
	pc->customdata = customdata;
	pc->poll= poll;
	pc->draw= draw;
	
	return pc;
}

void WM_paint_cursor_end(wmWindowManager *wm, void *handle)
{
	wmPaintCursor *pc;
	
	for(pc= wm->paintcursors.first; pc; pc= pc->next) {
		if(pc == (wmPaintCursor *)handle) {
			BLI_remlink(&wm->paintcursors, pc);
			MEM_freeN(pc);
			return;
		}
	}
}

/* ************ window gesture operator-callback definitions ************** */
/*
 * These are default callbacks for use in operators requiring gesture input
 */

/* **************** Border gesture *************** */

/* Border gesture has two types:
   1) WM_GESTURE_CROSS_RECT: starts a cross, on mouse click it changes to border 
   2) WM_GESTURE_RECT: starts immediate as a border, on mouse click or release it ends

   It stores 4 values (xmin, xmax, ymin, ymax) and event it ended with (event_type)
*/

static int border_apply(bContext *C, wmOperator *op, int event_type)
{
	wmGesture *gesture= op->customdata;
	rcti *rect= gesture->customdata;
	
	if(rect->xmin > rect->xmax)
		SWAP(int, rect->xmin, rect->xmax);
	if(rect->ymin > rect->ymax)
		SWAP(int, rect->ymin, rect->ymax);
	
	if(rect->xmin==rect->xmax || rect->ymin==rect->ymax)
		return 0;
		
	/* operator arguments and storage. */
	RNA_int_set(op->ptr, "xmin", rect->xmin);
	RNA_int_set(op->ptr, "ymin", rect->ymin);
	RNA_int_set(op->ptr, "xmax", rect->xmax);
	RNA_int_set(op->ptr, "ymax", rect->ymax);
	if( RNA_struct_find_property(op->ptr, "event_type") )
		RNA_int_set(op->ptr, "event_type", event_type);
	
	op->type->exec(C, op);
	
	return 1;
}

static void wm_gesture_end(bContext *C, wmOperator *op)
{
	wmGesture *gesture= op->customdata;
	
	WM_gesture_end(C, gesture);	/* frees gesture itself, and unregisters from window */
	op->customdata= NULL;

	ED_area_tag_redraw(CTX_wm_area(C));
	
}

int WM_border_select_invoke(bContext *C, wmOperator *op, wmEvent *event)
{
	op->customdata= WM_gesture_new(C, event, WM_GESTURE_CROSS_RECT);

	/* add modal handler */
	WM_event_add_modal_handler(C, &CTX_wm_window(C)->handlers, op);
	
	wm_gesture_tag_redraw(C);

	return OPERATOR_RUNNING_MODAL;
}

int WM_border_select_modal(bContext *C, wmOperator *op, wmEvent *event)
{
	wmGesture *gesture= op->customdata;
	rcti *rect= gesture->customdata;
	int sx, sy;
	
	switch(event->type) {
		case MOUSEMOVE:
			
			wm_subwindow_getorigin(CTX_wm_window(C), gesture->swinid, &sx, &sy);
			
			if(gesture->type==WM_GESTURE_CROSS_RECT && gesture->mode==0) {
				rect->xmin= rect->xmax= event->x - sx;
				rect->ymin= rect->ymax= event->y - sy;
			}
			else {
				rect->xmax= event->x - sx;
				rect->ymax= event->y - sy;
			}
			
			wm_gesture_tag_redraw(C);

			break;
			
		case LEFTMOUSE:
		case MIDDLEMOUSE:
		case RIGHTMOUSE:
			if(event->val==1) {
				if(gesture->type==WM_GESTURE_CROSS_RECT && gesture->mode==0) {
					gesture->mode= 1;
					wm_gesture_tag_redraw(C);
				}
			}
			else {
				if(border_apply(C, op, event->type)) {
					wm_gesture_end(C, op);
					return OPERATOR_FINISHED;
				}
				wm_gesture_end(C, op);
				return OPERATOR_CANCELLED;
			}
			break;
		case ESCKEY:
			wm_gesture_end(C, op);
			return OPERATOR_CANCELLED;
	}
	return OPERATOR_RUNNING_MODAL;
}

/* **************** circle gesture *************** */
/* works now only for selection or modal paint stuff, calls exec while hold mouse, exit on release */

int WM_gesture_circle_invoke(bContext *C, wmOperator *op, wmEvent *event)
{
	op->customdata= WM_gesture_new(C, event, WM_GESTURE_CIRCLE);
	
	/* add modal handler */
	WM_event_add_modal_handler(C, &CTX_wm_window(C)->handlers, op);
	
	wm_gesture_tag_redraw(C);
	
	return OPERATOR_RUNNING_MODAL;
}

static void gesture_circle_apply(bContext *C, wmOperator *op)
{
	wmGesture *gesture= op->customdata;
	rcti *rect= gesture->customdata;
	
	/* operator arguments and storage. */
	RNA_int_set(op->ptr, "x", rect->xmin);
	RNA_int_set(op->ptr, "y", rect->ymin);
	RNA_int_set(op->ptr, "radius", rect->xmax);
	
	if(op->type->exec)
		op->type->exec(C, op);
}

int WM_gesture_circle_modal(bContext *C, wmOperator *op, wmEvent *event)
{
	wmGesture *gesture= op->customdata;
	rcti *rect= gesture->customdata;
	int sx, sy;
	
	switch(event->type) {
		case MOUSEMOVE:
			
			wm_subwindow_getorigin(CTX_wm_window(C), gesture->swinid, &sx, &sy);
			
			rect->xmin= event->x - sx;
			rect->ymin= event->y - sy;
			
			wm_gesture_tag_redraw(C);
			
			if(gesture->mode)
				gesture_circle_apply(C, op);

			break;
		case WHEELUPMOUSE:
			rect->xmax += 2 + rect->xmax/10;
			wm_gesture_tag_redraw(C);
			break;
		case WHEELDOWNMOUSE:
			rect->xmax -= 2 + rect->xmax/10;
			if(rect->xmax < 1) rect->xmax= 1;
			wm_gesture_tag_redraw(C);
			break;
		case LEFTMOUSE:
		case MIDDLEMOUSE:
		case RIGHTMOUSE:
			if(event->val==0) {	/* key release */
				wm_gesture_end(C, op);
				return OPERATOR_FINISHED;
			}
			else {
				if( RNA_struct_find_property(op->ptr, "event_type") )
					RNA_int_set(op->ptr, "event_type", event->type);
				
				/* apply first click */
				gesture_circle_apply(C, op);
				gesture->mode= 1;
			}
			break;
		case ESCKEY:
			wm_gesture_end(C, op);
			return OPERATOR_CANCELLED;
	}
	return OPERATOR_RUNNING_MODAL;
}

#if 0
/* template to copy from */
void WM_OT_circle_gesture(wmOperatorType *ot)
{
	ot->name= "Circle Gesture";
	ot->idname= "WM_OT_circle_gesture";
	
	ot->invoke= WM_gesture_circle_invoke;
	ot->modal= WM_gesture_circle_modal;
	
	ot->poll= WM_operator_winactive;
	
	RNA_def_property(ot->srna, "x", PROP_INT, PROP_NONE);
	RNA_def_property(ot->srna, "y", PROP_INT, PROP_NONE);
	RNA_def_property(ot->srna, "radius", PROP_INT, PROP_NONE);

}
#endif

/* **************** Tweak gesture *************** */

static void tweak_gesture_modal(bContext *C, wmEvent *event)
{
	wmWindow *window= CTX_wm_window(C);
	wmGesture *gesture= window->tweak;
	rcti *rect= gesture->customdata;
	int sx, sy, val;
	
	switch(event->type) {
		case MOUSEMOVE:
			
			wm_subwindow_getorigin(window, gesture->swinid, &sx, &sy);
			
			rect->xmax= event->x - sx;
			rect->ymax= event->y - sy;
			
			if((val= wm_gesture_evaluate(C, gesture))) {
				wmEvent event;

				event= *(window->eventstate);
				if(gesture->event_type==LEFTMOUSE)
					event.type= EVT_TWEAK_L;
				else if(gesture->event_type==RIGHTMOUSE)
					event.type= EVT_TWEAK_R;
				else
					event.type= EVT_TWEAK_M;
				event.val= val;
				/* mouse coords! */
				wm_event_add(window, &event);
				
				WM_gesture_end(C, gesture);	/* frees gesture itself, and unregisters from window */
				window->tweak= NULL;
			}
			
			break;
			
		case LEFTMOUSE:
		case RIGHTMOUSE:
		case MIDDLEMOUSE:
			if(gesture->event_type==event->type) {
				WM_gesture_end(C, gesture);
				window->tweak= NULL;
				
				/* when tweak fails we should give the other keymap entries a chance */
				event->val= KM_RELEASE;
			}
			break;
		default:
			WM_gesture_end(C, gesture);
			window->tweak= NULL;
	}
}

/* standard tweak, called after window handlers passed on event */
void wm_tweakevent_test(bContext *C, wmEvent *event, int action)
{
	wmWindow *win= CTX_wm_window(C);
	
	if(win->tweak==NULL) {
		if(CTX_wm_region(C)) {
			if(event->val) { // pressed
				if( ELEM3(event->type, LEFTMOUSE, MIDDLEMOUSE, RIGHTMOUSE) )
					win->tweak= WM_gesture_new(C, event, WM_GESTURE_TWEAK);
			}
		}
	}
	else {
		if(action==WM_HANDLER_BREAK) {
			WM_gesture_end(C, win->tweak);
			win->tweak= NULL;
		}
		else
			tweak_gesture_modal(C, event);
	}
}

/* *********************** lasso gesture ****************** */

int WM_gesture_lasso_invoke(bContext *C, wmOperator *op, wmEvent *event)
{
	op->customdata= WM_gesture_new(C, event, WM_GESTURE_LASSO);
	
	/* add modal handler */
	WM_event_add_modal_handler(C, &CTX_wm_window(C)->handlers, op);
	
	wm_gesture_tag_redraw(C);
	
	return OPERATOR_RUNNING_MODAL;
}


static void gesture_lasso_apply(bContext *C, wmOperator *op, int event_type)
{
	wmGesture *gesture= op->customdata;
	PointerRNA itemptr;
	float loc[2];
	int i;
	short *lasso= gesture->customdata;
	
	/* operator storage as path. */

	for(i=0; i<gesture->points; i++, lasso+=2) {
		loc[0]= lasso[0];
		loc[1]= lasso[1];
		RNA_collection_add(op->ptr, "path", &itemptr);
		RNA_float_set_array(&itemptr, "loc", loc);
	}
	
	wm_gesture_end(C, op);
		
	if(op->type->exec)
		op->type->exec(C, op);
	
}

int WM_gesture_lasso_modal(bContext *C, wmOperator *op, wmEvent *event)
{
	wmGesture *gesture= op->customdata;
	int sx, sy;
	
	switch(event->type) {
		case MOUSEMOVE:
			
			wm_gesture_tag_redraw(C);
			
			wm_subwindow_getorigin(CTX_wm_window(C), gesture->swinid, &sx, &sy);
			if(gesture->points < WM_LASSO_MAX_POINTS) {
				short *lasso= gesture->customdata;
				lasso += 2 * gesture->points;
				lasso[0] = event->x - sx;
				lasso[1] = event->y - sy;
				gesture->points++;
			}
			else {
				gesture_lasso_apply(C, op, event->type);
				return OPERATOR_FINISHED;
			}
			break;
			
		case LEFTMOUSE:
		case MIDDLEMOUSE:
		case RIGHTMOUSE:
			if(event->val==0) {	/* key release */
				gesture_lasso_apply(C, op, event->type);
				return OPERATOR_FINISHED;
			}
			break;
		case ESCKEY:
			wm_gesture_end(C, op);
			return OPERATOR_CANCELLED;
	}
	return OPERATOR_RUNNING_MODAL;
}

#if 0
/* template to copy from */

static int gesture_lasso_exec(bContext *C, wmOperator *op)
{
	RNA_BEGIN(op->ptr, itemptr, "path") {
		float loc[2];
		
		RNA_float_get_array(&itemptr, "loc", loc);
		printf("Location: %f %f\n", loc[0], loc[1]);
	}
	RNA_END;
	
	return OPERATOR_FINISHED;
}

void WM_OT_lasso_gesture(wmOperatorType *ot)
{
	PropertyRNA *prop;
	
	ot->name= "Lasso Gesture";
	ot->idname= "WM_OT_lasso_gesture";
	
	ot->invoke= WM_gesture_lasso_invoke;
	ot->modal= WM_gesture_lasso_modal;
	ot->exec= gesture_lasso_exec;
	
	ot->poll= WM_operator_winactive;
	
	prop= RNA_def_property(ot->srna, "path", PROP_COLLECTION, PROP_NONE);
	RNA_def_property_struct_runtime(prop, &RNA_OperatorMousePath);
}
#endif

/* *********************** radial control ****************** */

const int WM_RADIAL_CONTROL_DISPLAY_SIZE = 200;

typedef struct wmRadialControl {
	int mode;
	float initial_value, value, max_value;
	int initial_mouse[2];
	void *cursor;
	GLuint tex;
} wmRadialControl;

static void wm_radial_control_paint(bContext *C, int x, int y, void *customdata)
{
	wmRadialControl *rc = (wmRadialControl*)customdata;
	ARegion *ar = CTX_wm_region(C);
	float r1=0.0f, r2=0.0f, r3=0.0f, angle=0.0f;

	/* Keep cursor in the original place */
	x = rc->initial_mouse[0] - ar->winrct.xmin;
	y = rc->initial_mouse[1] - ar->winrct.ymin;

	glPushMatrix();
	
	glTranslatef((float)x, (float)y, 0.0f);

	if(rc->mode == WM_RADIALCONTROL_SIZE) {
		r1= rc->value;
		r2= rc->initial_value;
		r3= r1;
	} else if(rc->mode == WM_RADIALCONTROL_STRENGTH) {
		r1= (1 - rc->value) * WM_RADIAL_CONTROL_DISPLAY_SIZE;
		r2= WM_RADIAL_CONTROL_DISPLAY_SIZE;
		r3= WM_RADIAL_CONTROL_DISPLAY_SIZE;
	} else if(rc->mode == WM_RADIALCONTROL_ANGLE) {
		r1= r2= WM_RADIAL_CONTROL_DISPLAY_SIZE;
		r3= WM_RADIAL_CONTROL_DISPLAY_SIZE;
		angle = rc->value;
	}

	glColor4ub(255, 255, 255, 128);
	glEnable( GL_LINE_SMOOTH );
	glEnable(GL_BLEND);

	if(rc->mode == WM_RADIALCONTROL_ANGLE)
		fdrawline(0, 0, WM_RADIAL_CONTROL_DISPLAY_SIZE, 0);

	if(rc->tex) {
		const float str = rc->mode == WM_RADIALCONTROL_STRENGTH ? (rc->value + 0.5) : 1;

		if(rc->mode == WM_RADIALCONTROL_ANGLE) {
			glRotatef(angle, 0, 0, 1);
			fdrawline(0, 0, WM_RADIAL_CONTROL_DISPLAY_SIZE, 0);
		}

		glBindTexture(GL_TEXTURE_2D, rc->tex);

		glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR);
		glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);

		glEnable(GL_TEXTURE_2D);
		glBegin(GL_QUADS);
		glColor4f(0,0,0, str);
		glTexCoord2f(0,0);
		glVertex2f(-r3, -r3);
		glTexCoord2f(1,0);
		glVertex2f(r3, -r3);
		glTexCoord2f(1,1);
		glVertex2f(r3, r3);
		glTexCoord2f(0,1);
		glVertex2f(-r3, r3);
		glEnd();
		glDisable(GL_TEXTURE_2D);
	}

	glColor4ub(255, 255, 255, 128);	
	glutil_draw_lined_arc(0.0, M_PI*2.0, r1, 40);
	glutil_draw_lined_arc(0.0, M_PI*2.0, r2, 40);
	glDisable(GL_BLEND);
	glDisable( GL_LINE_SMOOTH );
	
	glPopMatrix();
}

int WM_radial_control_modal(bContext *C, wmOperator *op, wmEvent *event)
{
	wmRadialControl *rc = (wmRadialControl*)op->customdata;
	int mode, initial_mouse[2], delta[2];
	float dist;
	double new_value = RNA_float_get(op->ptr, "new_value");
	int ret = OPERATOR_RUNNING_MODAL;

	mode = RNA_int_get(op->ptr, "mode");
	RNA_int_get_array(op->ptr, "initial_mouse", initial_mouse);

	switch(event->type) {
	case MOUSEMOVE:
		delta[0]= initial_mouse[0] - event->x;
		delta[1]= initial_mouse[1] - event->y;
		dist= sqrt(delta[0]*delta[0]+delta[1]*delta[1]);

		if(mode == WM_RADIALCONTROL_SIZE)
			new_value = dist;
		else if(mode == WM_RADIALCONTROL_STRENGTH) {
			new_value = 1 - dist / WM_RADIAL_CONTROL_DISPLAY_SIZE;
		} else if(mode == WM_RADIALCONTROL_ANGLE)
			new_value = ((int)(atan2(delta[1], delta[0]) * (180.0 / M_PI)) + 180);
		
		if(event->ctrl) {
			if(mode == WM_RADIALCONTROL_STRENGTH)
				new_value = ((int)(new_value * 100) / 10*10) / 100.0f;
			else
				new_value = ((int)new_value + 5) / 10*10;
		}
		
		break;
	case ESCKEY:
	case RIGHTMOUSE:
		ret = OPERATOR_CANCELLED;
		break;
	case LEFTMOUSE:
	case PADENTER:
		op->type->exec(C, op);
		ret = OPERATOR_FINISHED;
		break;
	}

	/* Clamp */
	if(new_value > rc->max_value)
		new_value = rc->max_value;
	else if(new_value < 0)
		new_value = 0;

	/* Update paint data */
	rc->value = new_value;

	RNA_float_set(op->ptr, "new_value", new_value);

	if(ret != OPERATOR_RUNNING_MODAL) {
		WM_paint_cursor_end(CTX_wm_manager(C), rc->cursor);
		MEM_freeN(rc);
	}
	
	ED_region_tag_redraw(CTX_wm_region(C));

	return ret;
}

/* Expects the operator customdata to be an ImBuf (or NULL) */
int WM_radial_control_invoke(bContext *C, wmOperator *op, wmEvent *event)
{
	wmRadialControl *rc = MEM_callocN(sizeof(wmRadialControl), "radial control");
	int mode = RNA_int_get(op->ptr, "mode");
	float initial_value = RNA_float_get(op->ptr, "initial_value");
	int mouse[2] = {event->x, event->y};

	if(mode == WM_RADIALCONTROL_SIZE) {
		rc->max_value = 200;
		mouse[0]-= initial_value;
	}
	else if(mode == WM_RADIALCONTROL_STRENGTH) {
		rc->max_value = 1;
		mouse[0]-= WM_RADIAL_CONTROL_DISPLAY_SIZE * (1 - initial_value);
	}
	else if(mode == WM_RADIALCONTROL_ANGLE) {
		rc->max_value = 360;
		mouse[0]-= WM_RADIAL_CONTROL_DISPLAY_SIZE * cos(initial_value);
		mouse[1]-= WM_RADIAL_CONTROL_DISPLAY_SIZE * sin(initial_value);
		initial_value *= 180.0f/M_PI;
	}

	if(op->customdata) {
		ImBuf *im = (ImBuf*)op->customdata;
		/* Build GL texture */
		glGenTextures(1, &rc->tex);
		glBindTexture(GL_TEXTURE_2D, rc->tex);
		glTexImage2D(GL_TEXTURE_2D, 0, GL_ALPHA, im->x, im->y, 0, GL_ALPHA, GL_FLOAT, im->rect_float);
		MEM_freeN(im->rect_float);
		MEM_freeN(im);
	}

	RNA_int_set_array(op->ptr, "initial_mouse", mouse);
	RNA_float_set(op->ptr, "new_value", initial_value);
		
	op->customdata = rc;
	rc->mode = mode;
	rc->initial_value = initial_value;
	rc->initial_mouse[0] = mouse[0];
	rc->initial_mouse[1] = mouse[1];
	rc->cursor = WM_paint_cursor_activate(CTX_wm_manager(C), op->type->poll,
					      wm_radial_control_paint, op->customdata);

	/* add modal handler */
	WM_event_add_modal_handler(C, &CTX_wm_window(C)->handlers, op);
	
	WM_radial_control_modal(C, op, event);
	
	return OPERATOR_RUNNING_MODAL;
}

/* Gets a descriptive string of the operation */
void WM_radial_control_string(wmOperator *op, char str[], int maxlen)
{
	int mode = RNA_int_get(op->ptr, "mode");
	float v = RNA_float_get(op->ptr, "new_value");

	if(mode == WM_RADIALCONTROL_SIZE)
		sprintf(str, "Size: %d", (int)v);
	else if(mode == WM_RADIALCONTROL_STRENGTH)
		sprintf(str, "Strength: %d", (int)v);
	else if(mode == WM_RADIALCONTROL_ANGLE)
		sprintf(str, "Angle: %d", (int)(v * 180.0f/M_PI));
}

/** Important: this doesn't define an actual operator, it
    just sets up the common parts of the radial control op. **/
void WM_OT_radial_control_partial(wmOperatorType *ot)
{
	static EnumPropertyItem prop_mode_items[] = {
		{WM_RADIALCONTROL_SIZE, "SIZE", "Size", ""},
		{WM_RADIALCONTROL_STRENGTH, "STRENGTH", "Strength", ""},
		{WM_RADIALCONTROL_ANGLE, "ANGLE", "Angle", ""},
		{0, NULL, NULL, NULL}};

	/* Should be set in custom invoke() */
	RNA_def_float(ot->srna, "initial_value", 0, 0, FLT_MAX, "Initial Value", "", 0, FLT_MAX);

	/* Set internally, should be used in custom exec() to get final value */
	RNA_def_float(ot->srna, "new_value", 0, 0, FLT_MAX, "New Value", "", 0, FLT_MAX);

	/* Should be set before calling operator */
	RNA_def_enum(ot->srna, "mode", prop_mode_items, 0, "Mode", "");

	/* Internal */
	RNA_def_int_vector(ot->srna, "initial_mouse", 2, NULL, INT_MIN, INT_MAX, "initial_mouse", "", INT_MIN, INT_MAX);
}

/* ******************************************************* */
 
/* called on initialize WM_exit() */
void wm_operatortype_free(void)
{
	BLI_freelistN(&global_ops);
}

/* called on initialize WM_init() */
void wm_operatortype_init(void)
{
	WM_operatortype_append(WM_OT_window_duplicate);
	WM_operatortype_append(WM_OT_save_homefile);
	WM_operatortype_append(WM_OT_window_fullscreen_toggle);
	WM_operatortype_append(WM_OT_exit_blender);
	WM_operatortype_append(WM_OT_open_recentfile);
	WM_operatortype_append(WM_OT_open_mainfile);
	WM_operatortype_append(WM_OT_jobs_timer);
	WM_operatortype_append(WM_OT_save_as_mainfile);
}

/* default keymap for windows and screens, only call once per WM */
void wm_window_keymap(wmWindowManager *wm)
{
	ListBase *keymap= WM_keymap_listbase(wm, "Window", 0, 0);
	
	/* items to make WM work */
	WM_keymap_verify_item(keymap, "WM_OT_jobs_timer", TIMERJOBS, KM_ANY, KM_ANY, 0);
	
	/* note, this doesn't replace existing keymap items */
	WM_keymap_verify_item(keymap, "WM_OT_window_duplicate", WKEY, KM_PRESS, KM_CTRL|KM_ALT, 0);
	WM_keymap_verify_item(keymap, "WM_OT_save_homefile", UKEY, KM_PRESS, KM_CTRL, 0);
	WM_keymap_verify_item(keymap, "WM_OT_open_recentfile", OKEY, KM_PRESS, KM_CTRL, 0);
	WM_keymap_verify_item(keymap, "WM_OT_open_mainfile", F1KEY, KM_PRESS, 0, 0);
	WM_keymap_verify_item(keymap, "WM_OT_save_as_mainfile", F2KEY, KM_PRESS, 0, 0);
	WM_keymap_verify_item(keymap, "WM_OT_window_fullscreen_toggle", F11KEY, KM_PRESS, 0, 0);
	WM_keymap_verify_item(keymap, "WM_OT_exit_blender", QKEY, KM_PRESS, KM_CTRL, 0);

}


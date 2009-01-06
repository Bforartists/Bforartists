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
		RNA_pointer_create(NULL, NULL, ot->srna, NULL, ptr);
	else
		memset(ptr, 0, sizeof(*ptr));
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
	const EnumPropertyItem *item;
	int totitem, i, len= strlen(op->type->name) + 5;
	char *menu, *p;
	
	if(prop) {
		RNA_property_enum_items(op->ptr, prop, &item, &totitem);
		
		for (i=0; i<totitem; i++)
			len+= strlen(item[i].name) + 5;
		
		menu= MEM_callocN(len, "string");
		
		p= menu + sprintf(menu, "%s %%t", op->type->name);
		for (i=0; i<totitem; i++)
			p+= sprintf(p, "|%s %%x%d", item[i].name, item[i].value);
		
		uiPupmenuOperator(C, totitem/30, op, "type", menu);
		MEM_freeN(menu);
		
		return OPERATOR_RUNNING_MODAL;
	}
	return OPERATOR_CANCELLED;
}

/* op->invoke */
int WM_operator_confirm(bContext *C, wmOperator *op, wmEvent *event)
{
	char buf[512];
	
	sprintf(buf, "OK? %%i%d%%t|%s", ICON_HELP, op->type->name);
	uiPupmenuOperator(C, 0, op, NULL, buf);
	
	return OPERATOR_RUNNING_MODAL;
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
	
	ot->flag= OPTYPE_REGISTER;
}

/* ********* recent file *********** */

static void recent_filelist(char *pup)
{
	struct RecentFile *recent;
	int i, ofs= 0;
	char *p;
	
	p= pup + sprintf(pup, "Open Recent%%t");
	
	if (G.sce[0]) {
		p+= sprintf(p, "|%s %%x%d", G.sce, 1);
		ofs = 1;
	}
	
	for (recent = G.recent_files.first, i=0; (i<U.recent_files) && (recent); recent = recent->next, i++) {
		if (strcmp(recent->filename, G.sce)) {
			p+= sprintf(p, "|%s %%x%d", recent->filename, i+ofs+1);
		}
	}
}

static int recentfile_exec(bContext *C, wmOperator *op)
{
	int event= RNA_enum_get(op->ptr, "nr");
	
	if(event>0) {
		if (G.sce[0] && (event==1))
			WM_read_file(C, G.sce, op->reports);
		else {
			struct RecentFile *recent = BLI_findlink(&(G.recent_files), event-2);
			if(recent) {
				WM_read_file(C, recent->filename, op->reports);
			}
		}
	}
	return 0;
}

static int wm_recentfile_invoke(bContext *C, wmOperator *op, wmEvent *event)
{
	char pup[2048];
	
	recent_filelist(pup);
	uiPupmenuOperator(C, 0, op, "nr", pup);
	
	return OPERATOR_RUNNING_MODAL;
}

static void WM_OT_open_recentfile(wmOperatorType *ot)
{
	ot->name= "Open Recent File";
	ot->idname= "WM_OT_open_recentfile";
	
	ot->invoke= wm_recentfile_invoke;
	ot->exec= recentfile_exec;
	ot->poll= WM_operator_winactive;
	
	ot->flag= OPTYPE_REGISTER;
	
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

	ED_fileselect_set_params(C, FILE_BLENDER, "Load", "C:\\", 0, 0, 0);

	/* screen, areas init */
	WM_event_add_notifier(C, NC_SCREEN|NA_EDITED, NULL);
	
	return OPERATOR_RUNNING_MODAL;
}

static int wm_mainfile_exec(bContext *C, wmOperator *op)
{
	char filename[FILE_MAX];
	RNA_string_get(op->ptr, "filename", filename);
	
	WM_read_file(C, filename, op->reports);
	
	WM_event_add_notifier(C, NC_WINDOW, NULL);

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

/* *********************** */

static void WM_OT_window_fullscreen_toggle(wmOperatorType *ot)
{
    ot->name= "Toggle Fullscreen";
    ot->idname= "WM_OT_window_fullscreen_toggle";

    ot->invoke= WM_operator_confirm;
    ot->exec= wm_window_fullscreen_toggle_op;
    ot->poll= WM_operator_winactive;
}

static void WM_OT_exit_blender(wmOperatorType *ot)
{
	ot->name= "Exit Blender";
	ot->idname= "WM_OT_exit_blender";

	ot->invoke= WM_operator_confirm;
	ot->exec= wm_exit_blender_op;
	ot->poll= WM_operator_winactive;
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

static void border_apply(bContext *C, wmOperator *op, int event_type)
{
	wmGesture *gesture= op->customdata;
	rcti *rect= gesture->customdata;
	
	if(rect->xmin > rect->xmax)
		SWAP(int, rect->xmin, rect->xmax);
	if(rect->ymin > rect->ymax)
		SWAP(int, rect->ymin, rect->ymax);
	
	/* operator arguments and storage. */
	RNA_int_set(op->ptr, "xmin", rect->xmin);
	RNA_int_set(op->ptr, "ymin", rect->ymin);
	RNA_int_set(op->ptr, "xmax", rect->xmax);
	RNA_int_set(op->ptr, "ymax", rect->ymax);
	if( RNA_struct_find_property(op->ptr, "event_type") )
		RNA_int_set(op->ptr, "event_type", event_type);
	
	op->type->exec(C, op);
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
				border_apply(C, op, event->type);
				wm_gesture_end(C, op);
				return OPERATOR_FINISHED;
			}
			break;
		case ESCKEY:
			wm_gesture_end(C, op);
			return OPERATOR_CANCELLED;
	}
	return OPERATOR_RUNNING_MODAL;
}

/* **************** circle gesture *************** */
/* works now only for selection or modal paint stuff, calls exec while hold mouse */

int WM_gesture_circle_invoke(bContext *C, wmOperator *op, wmEvent *event)
{
	op->customdata= WM_gesture_new(C, event, WM_GESTURE_CIRCLE);
	
	/* add modal handler */
	WM_event_add_modal_handler(C, &CTX_wm_window(C)->handlers, op);
	
	wm_gesture_tag_redraw(C);
	
	return OPERATOR_RUNNING_MODAL;
}

static void gesture_circle_apply(bContext *C, wmOperator *op, int event_type)
{
	wmGesture *gesture= op->customdata;
	rcti *rect= gesture->customdata;
	
	/* operator arguments and storage. */
	RNA_int_set(op->ptr, "x", rect->xmin);
	RNA_int_set(op->ptr, "y", rect->ymin);
	RNA_int_set(op->ptr, "radius", rect->xmax);
	if( RNA_struct_find_property(op->ptr, "event_type") )
		RNA_int_set(op->ptr, "event_type", event_type);
	
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
				gesture_circle_apply(C, op, event->type);

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
			else
				gesture->mode= 1;

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

static int tweak_gesture_invoke(bContext *C, wmOperator *op, wmEvent *event)
{
	op->customdata= WM_gesture_new(C, event, WM_GESTURE_TWEAK);
	
	/* add modal handler */
	WM_event_add_modal_handler(C, &CTX_wm_window(C)->handlers, op);
	
	wm_gesture_tag_redraw(C);
	
	return OPERATOR_RUNNING_MODAL;
}

static int tweak_gesture_modal(bContext *C, wmOperator *op, wmEvent *event)
{
	wmWindow *window= CTX_wm_window(C);
	wmGesture *gesture= op->customdata;
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
				
				wm_gesture_end(C, op);
				return OPERATOR_FINISHED;
			}
			else
				wm_gesture_tag_redraw(C);
			
			break;
			
		case LEFTMOUSE:
		case RIGHTMOUSE:
		case MIDDLEMOUSE:
			if(gesture->event_type==event->type) {
				wm_gesture_evaluate(C, gesture);
				wm_gesture_end(C, op);
				return OPERATOR_FINISHED;
			}
			break;
	}
	return OPERATOR_RUNNING_MODAL;
}

void WM_OT_tweak_gesture(wmOperatorType *ot)
{
	ot->name= "Tweak Gesture";
	ot->idname= "WM_OT_tweak_gesture";
	
	ot->invoke= tweak_gesture_invoke;
	ot->modal= tweak_gesture_modal;

	ot->poll= WM_operator_winactive;
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
	WM_operatortype_append(WM_OT_tweak_gesture);
	WM_operatortype_append(WM_OT_open_recentfile);
	WM_operatortype_append(WM_OT_open_mainfile);
}

/* default keymap for windows and screens, only call once per WM */
void wm_window_keymap(wmWindowManager *wm)
{
	ListBase *keymap= WM_keymap_listbase(wm, "Window", 0, 0);
	
	/* note, this doesn't replace existing keymap items */
	WM_keymap_verify_item(keymap, "WM_OT_window_duplicate", AKEY, KM_PRESS, KM_CTRL|KM_ALT, 0);
	WM_keymap_verify_item(keymap, "WM_OT_save_homefile", UKEY, KM_PRESS, KM_CTRL, 0);
	WM_keymap_verify_item(keymap, "WM_OT_open_recentfile", OKEY, KM_PRESS, KM_CTRL, 0);
	WM_keymap_verify_item(keymap, "WM_OT_open_mainfile", F1KEY, KM_PRESS, 0, 0);
	WM_keymap_verify_item(keymap, "WM_OT_window_fullscreen_toggle", FKEY, KM_PRESS, 0, 0);
	WM_keymap_verify_item(keymap, "WM_OT_exit_blender", QKEY, KM_PRESS, KM_CTRL, 0);
}


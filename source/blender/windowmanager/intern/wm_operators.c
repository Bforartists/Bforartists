/*
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
 * Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
 *
 * The Original Code is Copyright (C) 2007 Blender Foundation.
 * All rights reserved.
 *
 * 
 * Contributor(s): Blender Foundation
 *
 * ***** END GPL LICENSE BLOCK *****
 */

/** \file blender/windowmanager/intern/wm_operators.c
 *  \ingroup wm
 */


#include <float.h>
#include <string.h>
#include <ctype.h>
#include <stdio.h>
#include <stddef.h>
#include <assert.h>

#ifdef WIN32
#include "BLI_winstuff.h"
#include <windows.h>  

#include <io.h>
#endif

#include "MEM_guardedalloc.h"

#include "DNA_ID.h"
#include "DNA_object_types.h"
#include "DNA_screen_types.h"
#include "DNA_scene_types.h"
#include "DNA_userdef_types.h"
#include "DNA_windowmanager_types.h"

#include "BLF_api.h"

#include "PIL_time.h"

#include "BLI_blenlib.h"
#include "BLI_dynstr.h" /*for WM_operator_pystring */
#include "BLI_math.h"
#include "BLI_utildefines.h"

#include "BLO_readfile.h"

#include "BKE_blender.h"
#include "BKE_context.h"
#include "BKE_depsgraph.h"
#include "BKE_idprop.h"
#include "BKE_library.h"
#include "BKE_global.h"
#include "BKE_main.h"
#include "BKE_report.h"
#include "BKE_scene.h"
#include "BKE_screen.h" /* BKE_ST_MAXNAME */

#include "BKE_idcode.h"

#include "BIF_gl.h"
#include "BIF_glutil.h" /* for paint cursor */

#include "IMB_imbuf_types.h"

#include "ED_screen.h"
#include "ED_util.h"

#include "RNA_access.h"
#include "RNA_define.h"
#include "RNA_enum_types.h"

#include "UI_interface.h"
#include "UI_resources.h"

#include "WM_api.h"
#include "WM_types.h"

#include "wm.h"
#include "wm_draw.h"
#include "wm_event_system.h"
#include "wm_event_types.h"
#include "wm_subwindow.h"
#include "wm_window.h"

static ListBase global_ops= {NULL, NULL};

/* ************ operator API, exported ********** */


wmOperatorType *WM_operatortype_find(const char *idname, int quiet)
{
	wmOperatorType *ot;
	
	char idname_bl[OP_MAX_TYPENAME]; // XXX, needed to support python style names without the _OT_ syntax
	WM_operator_bl_idname(idname_bl, idname);

	if (idname_bl[0]) {
		ot= (wmOperatorType *)BLI_findstring_ptr(&global_ops, idname_bl, offsetof(wmOperatorType, idname));
		if(ot) {
			return ot;
		}
	}
	
	if(!quiet)
		printf("search for unknown operator %s, %s\n", idname_bl, idname);
	
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

	if(ot->name==NULL) {
		static char dummy_name[] = "Dummy Name";
		fprintf(stderr, "ERROR: Operator %s has no name property!\n", ot->idname);
		ot->name= dummy_name;
	}

	RNA_def_struct_ui_text(ot->srna, ot->name, ot->description ? ot->description:"(undocumented operator)"); // XXX All ops should have a description but for now allow them not to.
	RNA_def_struct_identifier(ot->srna, ot->idname);
	BLI_addtail(&global_ops, ot);
}

void WM_operatortype_append_ptr(void (*opfunc)(wmOperatorType*, void*), void *userdata)
{
	wmOperatorType *ot;

	ot= MEM_callocN(sizeof(wmOperatorType), "operatortype");
	ot->srna= RNA_def_struct(&BLENDER_RNA, "", "OperatorProperties");
	opfunc(ot, userdata);
	RNA_def_struct_ui_text(ot->srna, ot->name, ot->description ? ot->description:"(undocumented operator)");
	RNA_def_struct_identifier(ot->srna, ot->idname);
	BLI_addtail(&global_ops, ot);
}

/* ********************* macro operator ******************** */

typedef struct {
	int retval;
} MacroData;

static void wm_macro_start(wmOperator *op)
{
	if (op->customdata == NULL) {
		op->customdata = MEM_callocN(sizeof(MacroData), "MacroData");
	}
}

static int wm_macro_end(wmOperator *op, int retval)
{
	if (retval & OPERATOR_CANCELLED) {
		MacroData *md = op->customdata;

		if (md->retval & OPERATOR_FINISHED) {
			retval |= OPERATOR_FINISHED;
			retval &= ~OPERATOR_CANCELLED;
		}
	}

	/* if modal is ending, free custom data */
	if (retval & (OPERATOR_FINISHED|OPERATOR_CANCELLED)) {
		if (op->customdata) {
			MEM_freeN(op->customdata);
			op->customdata = NULL;
		}
	}

	return retval;
}

/* macro exec only runs exec calls */
static int wm_macro_exec(bContext *C, wmOperator *op)
{
	wmOperator *opm;
	int retval= OPERATOR_FINISHED;
	
	wm_macro_start(op);

	for(opm= op->macro.first; opm; opm= opm->next) {
		
		if(opm->type->exec) {
			retval= opm->type->exec(C, opm);
		
			if (retval & OPERATOR_FINISHED) {
				MacroData *md = op->customdata;
				md->retval = OPERATOR_FINISHED; /* keep in mind that at least one operator finished */
			} else {
				break; /* operator didn't finish, end macro */
			}
		}
	}
	
	return wm_macro_end(op, retval);
}

static int wm_macro_invoke_internal(bContext *C, wmOperator *op, wmEvent *event, wmOperator *opm)
{
	int retval= OPERATOR_FINISHED;

	/* start from operator received as argument */
	for( ; opm; opm= opm->next) {
		if(opm->type->invoke)
			retval= opm->type->invoke(C, opm, event);
		else if(opm->type->exec)
			retval= opm->type->exec(C, opm);

		BLI_movelisttolist(&op->reports->list, &opm->reports->list);
		
		if (retval & OPERATOR_FINISHED) {
			MacroData *md = op->customdata;
			md->retval = OPERATOR_FINISHED; /* keep in mind that at least one operator finished */
		} else {
			break; /* operator didn't finish, end macro */
		}
	}

	return wm_macro_end(op, retval);
}

static int wm_macro_invoke(bContext *C, wmOperator *op, wmEvent *event)
{
	wm_macro_start(op);
	return wm_macro_invoke_internal(C, op, event, op->macro.first);
}

static int wm_macro_modal(bContext *C, wmOperator *op, wmEvent *event)
{
	wmOperator *opm = op->opm;
	int retval= OPERATOR_FINISHED;
	
	if(opm==NULL)
		printf("macro error, calling NULL modal()\n");
	else {
		retval = opm->type->modal(C, opm, event);

		/* if this one is done but it's not the last operator in the macro */
		if ((retval & OPERATOR_FINISHED) && opm->next) {
			MacroData *md = op->customdata;

			md->retval = OPERATOR_FINISHED; /* keep in mind that at least one operator finished */

			retval = wm_macro_invoke_internal(C, op, event, opm->next);

			/* if new operator is modal and also added its own handler */
			if (retval & OPERATOR_RUNNING_MODAL && op->opm != opm) {
				wmWindow *win = CTX_wm_window(C);
				wmEventHandler *handler = NULL;

				for (handler = win->modalhandlers.first; handler; handler = handler->next) {
					/* first handler in list is the new one */
					if (handler->op == op)
						break;
				}

				if (handler) {
					BLI_remlink(&win->modalhandlers, handler);
					wm_event_free_handler(handler);
				}

				/* if operator is blocking, grab cursor
				 * This may end up grabbing twice, but we don't care.
				 * */
				if(op->opm->type->flag & OPTYPE_BLOCKING) {
					int bounds[4] = {-1,-1,-1,-1};
					int wrap = (U.uiflag & USER_CONTINUOUS_MOUSE) && ((op->opm->flag & OP_GRAB_POINTER) || (op->opm->type->flag & OPTYPE_GRAB_POINTER));

					if(wrap) {
						ARegion *ar= CTX_wm_region(C);
						if(ar) {
							bounds[0]= ar->winrct.xmin;
							bounds[1]= ar->winrct.ymax;
							bounds[2]= ar->winrct.xmax;
							bounds[3]= ar->winrct.ymin;
						}
					}

					WM_cursor_grab(CTX_wm_window(C), wrap, FALSE, bounds);
				}
			}
		}
	}

	return wm_macro_end(op, retval);
}

static int wm_macro_cancel(bContext *C, wmOperator *op)
{
	/* call cancel on the current modal operator, if any */
	if (op->opm && op->opm->type->cancel) {
		op->opm->type->cancel(C, op->opm);
	}

	return wm_macro_end(op, OPERATOR_CANCELLED);
}

/* Names have to be static for now */
wmOperatorType *WM_operatortype_append_macro(const char *idname, const char *name, int flag)
{
	wmOperatorType *ot;
	
	if(WM_operatortype_find(idname, TRUE)) {
		printf("Macro error: operator %s exists\n", idname);
		return NULL;
	}
	
	ot= MEM_callocN(sizeof(wmOperatorType), "operatortype");
	ot->srna= RNA_def_struct(&BLENDER_RNA, "", "OperatorProperties");
	
	ot->idname= idname;
	ot->name= name;
	ot->flag= OPTYPE_MACRO|flag;
	
	ot->exec= wm_macro_exec;
	ot->invoke= wm_macro_invoke;
	ot->modal= wm_macro_modal;
	ot->cancel= wm_macro_cancel;
	ot->poll= NULL;

	if(!ot->description)
		ot->description= "(undocumented operator)";
	
	RNA_def_struct_ui_text(ot->srna, ot->name, ot->description); // XXX All ops should have a description but for now allow them not to.
	RNA_def_struct_identifier(ot->srna, ot->idname);

	BLI_addtail(&global_ops, ot);

	return ot;
}

void WM_operatortype_append_macro_ptr(void (*opfunc)(wmOperatorType*, void*), void *userdata)
{
	wmOperatorType *ot;

	ot= MEM_callocN(sizeof(wmOperatorType), "operatortype");
	ot->srna= RNA_def_struct(&BLENDER_RNA, "", "OperatorProperties");

	ot->flag= OPTYPE_MACRO;
	ot->exec= wm_macro_exec;
	ot->invoke= wm_macro_invoke;
	ot->modal= wm_macro_modal;
	ot->cancel= wm_macro_cancel;
	ot->poll= NULL;

	if(!ot->description)
		ot->description= "(undocumented operator)";

	opfunc(ot, userdata);

	RNA_def_struct_ui_text(ot->srna, ot->name, ot->description);
	RNA_def_struct_identifier(ot->srna, ot->idname);

	BLI_addtail(&global_ops, ot);
}

wmOperatorTypeMacro *WM_operatortype_macro_define(wmOperatorType *ot, const char *idname)
{
	wmOperatorTypeMacro *otmacro= MEM_callocN(sizeof(wmOperatorTypeMacro), "wmOperatorTypeMacro");

	BLI_strncpy(otmacro->idname, idname, OP_MAX_TYPENAME);

	/* do this on first use, since operatordefinitions might have been not done yet */
	WM_operator_properties_alloc(&(otmacro->ptr), &(otmacro->properties), idname);
	WM_operator_properties_sanitize(otmacro->ptr, 1);

	BLI_addtail(&ot->macro, otmacro);

	{
		/* operator should always be found but in the event its not. dont segfault */
		wmOperatorType *otsub = WM_operatortype_find(idname, 0);
		if(otsub) {
			RNA_def_pointer_runtime(ot->srna, otsub->idname, otsub->srna,
			otsub->name, otsub->description);
		}
	}

	return otmacro;
}

static void wm_operatortype_free_macro(wmOperatorType *ot)
{
	wmOperatorTypeMacro *otmacro;
	
	for(otmacro= ot->macro.first; otmacro; otmacro= otmacro->next) {
		if(otmacro->ptr) {
			WM_operator_properties_free(otmacro->ptr);
			MEM_freeN(otmacro->ptr);
		}
	}
	BLI_freelistN(&ot->macro);
}


int WM_operatortype_remove(const char *idname)
{
	wmOperatorType *ot = WM_operatortype_find(idname, 0);

	if (ot==NULL)
		return 0;
	
	BLI_remlink(&global_ops, ot);
	RNA_struct_free(&BLENDER_RNA, ot->srna);
	
	if(ot->macro.first)
		wm_operatortype_free_macro(ot);
	
	MEM_freeN(ot);

	return 1;
}

/* SOME_OT_op -> some.op */
void WM_operator_py_idname(char *to, const char *from)
{
	char *sep= strstr(from, "_OT_");
	if(sep) {
		int i, ofs= (sep-from);

		for(i=0; i<ofs; i++)
			to[i]= tolower(from[i]);

		to[ofs] = '.';
		BLI_strncpy(to+(ofs+1), sep+4, OP_MAX_TYPENAME);
	}
	else {
		/* should not happen but support just incase */
		BLI_strncpy(to, from, OP_MAX_TYPENAME);
	}
}

/* some.op -> SOME_OT_op */
void WM_operator_bl_idname(char *to, const char *from)
{
	if (from) {
		char *sep= strchr(from, '.');

		if(sep) {
			int i, ofs= (sep-from);

			for(i=0; i<ofs; i++)
				to[i]= toupper(from[i]);

			BLI_strncpy(to+ofs, "_OT_", OP_MAX_TYPENAME);
			BLI_strncpy(to+(ofs+4), sep+1, OP_MAX_TYPENAME);
		}
		else {
			/* should not happen but support just incase */
			BLI_strncpy(to, from, OP_MAX_TYPENAME);
		}
	}
	else
		to[0]= 0;
}

/* print a string representation of the operator, with the args that it runs 
 * so python can run it again,
 *
 * When calling from an existing wmOperator do.
 * WM_operator_pystring(op->type, op->ptr);
 */
char *WM_operator_pystring(bContext *C, wmOperatorType *ot, PointerRNA *opptr, int all_args)
{
	const char *arg_name= NULL;
	char idname_py[OP_MAX_TYPENAME];

	PropertyRNA *prop, *iterprop;

	/* for building the string */
	DynStr *dynstr= BLI_dynstr_new();
	char *cstring, *buf;
	int first_iter=1, ok= 1;


	/* only to get the orginal props for comparisons */
	PointerRNA opptr_default;
	PropertyRNA *prop_default;
	char *buf_default;
	if(all_args==0 || opptr==NULL) {
		WM_operator_properties_create_ptr(&opptr_default, ot);

		if(opptr==NULL)
			opptr = &opptr_default;
	}


	WM_operator_py_idname(idname_py, ot->idname);
	BLI_dynstr_appendf(dynstr, "bpy.ops.%s(", idname_py);

	iterprop= RNA_struct_iterator_property(opptr->type);

	RNA_PROP_BEGIN(opptr, propptr, iterprop) {
		prop= propptr.data;
		arg_name= RNA_property_identifier(prop);

		if (strcmp(arg_name, "rna_type")==0) continue;

		buf= RNA_property_as_string(C, opptr, prop);
		
		ok= 1;

		if(!all_args) {
			/* not verbose, so only add in attributes that use non-default values
			 * slow but good for tooltips */
			prop_default= RNA_struct_find_property(&opptr_default, arg_name);

			if(prop_default) {
				buf_default= RNA_property_as_string(C, &opptr_default, prop_default);

				if(strcmp(buf, buf_default)==0)
					ok= 0; /* values match, dont bother printing */

				MEM_freeN(buf_default);
			}

		}
		if(ok) {
			BLI_dynstr_appendf(dynstr, first_iter?"%s=%s":", %s=%s", arg_name, buf);
			first_iter = 0;
		}

		MEM_freeN(buf);

	}
	RNA_PROP_END;

	if(all_args==0 || opptr==&opptr_default )
		WM_operator_properties_free(&opptr_default);

	BLI_dynstr_append(dynstr, ")");

	cstring = BLI_dynstr_get_cstring(dynstr);
	BLI_dynstr_free(dynstr);
	return cstring;
}

void WM_operator_properties_create_ptr(PointerRNA *ptr, wmOperatorType *ot)
{
	RNA_pointer_create(NULL, ot->srna, NULL, ptr);
}

void WM_operator_properties_create(PointerRNA *ptr, const char *opstring)
{
	wmOperatorType *ot= WM_operatortype_find(opstring, 0);

	if(ot)
		WM_operator_properties_create_ptr(ptr, ot);
	else
		RNA_pointer_create(NULL, &RNA_OperatorProperties, NULL, ptr);
}

/* similar to the function above except its uses ID properties
 * used for keymaps and macros */
void WM_operator_properties_alloc(PointerRNA **ptr, IDProperty **properties, const char *opstring)
{
	if(*properties==NULL) {
		IDPropertyTemplate val = {0};
		*properties= IDP_New(IDP_GROUP, val, "wmOpItemProp");
	}

	if(*ptr==NULL) {
		*ptr= MEM_callocN(sizeof(PointerRNA), "wmOpItemPtr");
		WM_operator_properties_create(*ptr, opstring);
	}

	(*ptr)->data= *properties;

}

void WM_operator_properties_sanitize(PointerRNA *ptr, const short no_context)
{
	RNA_STRUCT_BEGIN(ptr, prop) {
		switch(RNA_property_type(prop)) {
		case PROP_ENUM:
			if (no_context)
				RNA_def_property_flag(prop, PROP_ENUM_NO_CONTEXT);
			else
				RNA_def_property_clear_flag(prop, PROP_ENUM_NO_CONTEXT);
			break;
		case PROP_POINTER:
			{
				StructRNA *ptype= RNA_property_pointer_type(ptr, prop);

				/* recurse into operator properties */
				if (RNA_struct_is_a(ptype, &RNA_OperatorProperties)) {
					PointerRNA opptr = RNA_property_pointer_get(ptr, prop);
					WM_operator_properties_sanitize(&opptr, no_context);
				}
				break;
			}
		default:
			break;
		}
	}
	RNA_STRUCT_END;
}

void WM_operator_properties_free(PointerRNA *ptr)
{
	IDProperty *properties= ptr->data;

	if(properties) {
		IDP_FreeProperty(properties);
		MEM_freeN(properties);
		ptr->data= NULL; /* just incase */
	}
}

/* ************ default op callbacks, exported *********** */

/* invoke callback, uses enum property named "type" */
int WM_menu_invoke(bContext *C, wmOperator *op, wmEvent *UNUSED(event))
{
	PropertyRNA *prop= op->type->prop;
	uiPopupMenu *pup;
	uiLayout *layout;

	if(prop==NULL) {
		printf("WM_menu_invoke: %s has no enum property set\n", op->type->idname);
	}
	else if (RNA_property_type(prop) != PROP_ENUM) {
		printf("WM_menu_invoke: %s \"%s\" is not an enum property\n", op->type->idname, RNA_property_identifier(prop));
	}
	else if (RNA_property_is_set(op->ptr, RNA_property_identifier(prop))) {
		return op->type->exec(C, op);
	}
	else {
		pup= uiPupMenuBegin(C, op->type->name, ICON_NONE);
		layout= uiPupMenuLayout(pup);
		uiItemsFullEnumO(layout, op->type->idname, (char*)RNA_property_identifier(prop), op->ptr->data, WM_OP_EXEC_REGION_WIN, 0);
		uiPupMenuEnd(C, pup);
	}

	return OPERATOR_CANCELLED;
}


/* generic enum search invoke popup */
static void operator_enum_search_cb(const struct bContext *C, void *arg_ot, const char *str, uiSearchItems *items)
{
	wmOperatorType *ot = (wmOperatorType *)arg_ot;
	PropertyRNA *prop= ot->prop;

	if(prop==NULL) {
		printf("WM_enum_search_invoke: %s has no enum property set\n", ot->idname);
	}
	else if (RNA_property_type(prop) != PROP_ENUM) {
		printf("WM_enum_search_invoke: %s \"%s\" is not an enum property\n", ot->idname, RNA_property_identifier(prop));
	}
	else {
		PointerRNA ptr;

		EnumPropertyItem *item, *item_array;
		int do_free;

		RNA_pointer_create(NULL, ot->srna, NULL, &ptr);
		RNA_property_enum_items((bContext *)C, &ptr, prop, &item_array, NULL, &do_free);

		for(item= item_array; item->identifier; item++) {
			/* note: need to give the intex rather then the dientifier because the enum can be freed */
			if(BLI_strcasestr(item->name, str))
				if(0==uiSearchItemAdd(items, item->name, SET_INT_IN_POINTER(item->value), 0))
					break;
		}

		if(do_free)
			MEM_freeN(item_array);
	}
}

static void operator_enum_call_cb(struct bContext *C, void *arg1, void *arg2)
{
	wmOperatorType *ot= arg1;

	if(ot) {
		PointerRNA props_ptr;
		WM_operator_properties_create_ptr(&props_ptr, ot);
		RNA_property_enum_set(&props_ptr, ot->prop, GET_INT_FROM_POINTER(arg2));
		WM_operator_name_call(C, ot->idname, WM_OP_EXEC_DEFAULT, &props_ptr);
		WM_operator_properties_free(&props_ptr);
	}
}

static uiBlock *wm_enum_search_menu(bContext *C, ARegion *ar, void *arg_op)
{
	static char search[256]= "";
	wmEvent event;
	wmWindow *win= CTX_wm_window(C);
	uiBlock *block;
	uiBut *but;
	wmOperator *op= (wmOperator *)arg_op;

	block= uiBeginBlock(C, ar, "_popup", UI_EMBOSS);
	uiBlockSetFlag(block, UI_BLOCK_LOOP|UI_BLOCK_RET_1|UI_BLOCK_MOVEMOUSE_QUIT);

	//uiDefBut(block, LABEL, 0, op->type->name, 10, 10, 180, 19, NULL, 0.0, 0.0, 0, 0, ""); // ok, this isnt so easy...
	but= uiDefSearchBut(block, search, 0, ICON_VIEWZOOM, 256, 10, 10, 180, 19, 0, 0, "");
	uiButSetSearchFunc(but, operator_enum_search_cb, op->type, operator_enum_call_cb, NULL);

	/* fake button, it holds space for search items */
	uiDefBut(block, LABEL, 0, "", 10, 10 - uiSearchBoxhHeight(), 180, uiSearchBoxhHeight(), NULL, 0, 0, 0, 0, NULL);

	uiPopupBoundsBlock(block, 6, 0, -20); /* move it downwards, mouse over button */
	uiEndBlock(C, block);

	event= *(win->eventstate);	/* XXX huh huh? make api call */
	event.type= EVT_BUT_OPEN;
	event.val= KM_PRESS;
	event.customdata= but;
	event.customdatafree= FALSE;
	wm_event_add(win, &event);

	return block;
}


int WM_enum_search_invoke(bContext *C, wmOperator *op, wmEvent *UNUSED(event))
{
	uiPupBlock(C, wm_enum_search_menu, op);
	return OPERATOR_CANCELLED;
}

/* Can't be used as an invoke directly, needs message arg (can be NULL) */
int WM_operator_confirm_message(bContext *C, wmOperator *op, const char *message)
{
	uiPopupMenu *pup;
	uiLayout *layout;
	IDProperty *properties= op->ptr->data;

	if(properties && properties->len)
		properties= IDP_CopyProperty(op->ptr->data);
	else
		properties= NULL;

	pup= uiPupMenuBegin(C, "OK?", ICON_QUESTION);
	layout= uiPupMenuLayout(pup);
	uiItemFullO(layout, op->type->idname, message, ICON_NONE, properties, WM_OP_EXEC_REGION_WIN, 0);
	uiPupMenuEnd(C, pup);
	
	return OPERATOR_CANCELLED;
}


int WM_operator_confirm(bContext *C, wmOperator *op, wmEvent *UNUSED(event))
{
	return WM_operator_confirm_message(C, op, NULL);
}

/* op->invoke, opens fileselect if path property not set, otherwise executes */
int WM_operator_filesel(bContext *C, wmOperator *op, wmEvent *UNUSED(event))
{
	if (RNA_property_is_set(op->ptr, "filepath")) {
		return WM_operator_call(C, op);
	} 
	else {
		WM_event_add_fileselect(C, op);
		return OPERATOR_RUNNING_MODAL;
	}
}

/* default properties for fileselect */
void WM_operator_properties_filesel(wmOperatorType *ot, int filter, short type, short action, short flag)
{
	PropertyRNA *prop;


	if(flag & WM_FILESEL_FILEPATH)
		RNA_def_string_file_path(ot->srna, "filepath", "", FILE_MAX, "File Path", "Path to file");

	if(flag & WM_FILESEL_DIRECTORY)
		RNA_def_string_dir_path(ot->srna, "directory", "", FILE_MAX, "Directory", "Directory of the file");

	if(flag & WM_FILESEL_FILENAME)
		RNA_def_string_file_name(ot->srna, "filename", "", FILE_MAX, "File Name", "Name of the file");

	if (action == FILE_SAVE) {
		prop= RNA_def_boolean(ot->srna, "check_existing", 1, "Check Existing", "Check and warn on overwriting existing files");
		RNA_def_property_flag(prop, PROP_HIDDEN);
	}
	
	prop= RNA_def_boolean(ot->srna, "filter_blender", (filter & BLENDERFILE), "Filter .blend files", "");
	RNA_def_property_flag(prop, PROP_HIDDEN);
	prop= RNA_def_boolean(ot->srna, "filter_image", (filter & IMAGEFILE), "Filter image files", "");
	RNA_def_property_flag(prop, PROP_HIDDEN);
	prop= RNA_def_boolean(ot->srna, "filter_movie", (filter & MOVIEFILE), "Filter movie files", "");
	RNA_def_property_flag(prop, PROP_HIDDEN);
	prop= RNA_def_boolean(ot->srna, "filter_python", (filter & PYSCRIPTFILE), "Filter python files", "");
	RNA_def_property_flag(prop, PROP_HIDDEN);
	prop= RNA_def_boolean(ot->srna, "filter_font", (filter & FTFONTFILE), "Filter font files", "");
	RNA_def_property_flag(prop, PROP_HIDDEN);
	prop= RNA_def_boolean(ot->srna, "filter_sound", (filter & SOUNDFILE), "Filter sound files", "");
	RNA_def_property_flag(prop, PROP_HIDDEN);
	prop= RNA_def_boolean(ot->srna, "filter_text", (filter & TEXTFILE), "Filter text files", "");
	RNA_def_property_flag(prop, PROP_HIDDEN);
	prop= RNA_def_boolean(ot->srna, "filter_btx", (filter & BTXFILE), "Filter btx files", "");
	RNA_def_property_flag(prop, PROP_HIDDEN);
	prop= RNA_def_boolean(ot->srna, "filter_collada", (filter & COLLADAFILE), "Filter COLLADA files", "");
	RNA_def_property_flag(prop, PROP_HIDDEN);
	prop= RNA_def_boolean(ot->srna, "filter_folder", (filter & FOLDERFILE), "Filter folders", "");
	RNA_def_property_flag(prop, PROP_HIDDEN);

	prop= RNA_def_int(ot->srna, "filemode", type, FILE_LOADLIB, FILE_SPECIAL, 
		"File Browser Mode", "The setting for the file browser mode to load a .blend file, a library or a special file",
		FILE_LOADLIB, FILE_SPECIAL);
	RNA_def_property_flag(prop, PROP_HIDDEN);

	if(flag & WM_FILESEL_RELPATH)
		RNA_def_boolean(ot->srna, "relative_path", (U.flag & USER_RELPATHS) ? 1:0, "Relative Path", "Select the file relative to the blend file");
}

void WM_operator_properties_select_all(wmOperatorType *ot) {
	static EnumPropertyItem select_all_actions[] = {
			{SEL_TOGGLE, "TOGGLE", 0, "Toggle", "Toggle selection for all elements"},
			{SEL_SELECT, "SELECT", 0, "Select", "Select all elements"},
			{SEL_DESELECT, "DESELECT", 0, "Deselect", "Deselect all elements"},
			{SEL_INVERT, "INVERT", 0, "Invert", "Invert selection of all elements"},
			{0, NULL, 0, NULL, NULL}
	};

	RNA_def_enum(ot->srna, "action", select_all_actions, SEL_TOGGLE, "Action", "Selection action to execute");
}

void WM_operator_properties_gesture_border(wmOperatorType *ot, int extend)
{
	RNA_def_int(ot->srna, "gesture_mode", 0, INT_MIN, INT_MAX, "Gesture Mode", "", INT_MIN, INT_MAX);
	RNA_def_int(ot->srna, "xmin", 0, INT_MIN, INT_MAX, "X Min", "", INT_MIN, INT_MAX);
	RNA_def_int(ot->srna, "xmax", 0, INT_MIN, INT_MAX, "X Max", "", INT_MIN, INT_MAX);
	RNA_def_int(ot->srna, "ymin", 0, INT_MIN, INT_MAX, "Y Min", "", INT_MIN, INT_MAX);
	RNA_def_int(ot->srna, "ymax", 0, INT_MIN, INT_MAX, "Y Max", "", INT_MIN, INT_MAX);

	if(extend)
		RNA_def_boolean(ot->srna, "extend", 1, "Extend", "Extend selection instead of deselecting everything first");
}

void WM_operator_properties_gesture_straightline(wmOperatorType *ot, int cursor)
{
	RNA_def_int(ot->srna, "xstart", 0, INT_MIN, INT_MAX, "X Start", "", INT_MIN, INT_MAX);
	RNA_def_int(ot->srna, "xend", 0, INT_MIN, INT_MAX, "X End", "", INT_MIN, INT_MAX);
	RNA_def_int(ot->srna, "ystart", 0, INT_MIN, INT_MAX, "Y Start", "", INT_MIN, INT_MAX);
	RNA_def_int(ot->srna, "yend", 0, INT_MIN, INT_MAX, "Y End", "", INT_MIN, INT_MAX);
	
	if(cursor)
		RNA_def_int(ot->srna, "cursor", cursor, 0, INT_MAX, "Cursor", "Mouse cursor style to use during the modal operator", 0, INT_MAX);
}


/* op->poll */
int WM_operator_winactive(bContext *C)
{
	if(CTX_wm_window(C)==NULL) return 0;
	return 1;
}

static uiBlock *wm_block_create_redo(bContext *C, ARegion *ar, void *arg_op)
{
	wmOperator *op= arg_op;
	uiBlock *block;
	uiLayout *layout;
	uiStyle *style= U.uistyles.first;
	int width= 300;
	

	block= uiBeginBlock(C, ar, "redo_popup", UI_EMBOSS);
	uiBlockClearFlag(block, UI_BLOCK_LOOP);
	uiBlockSetFlag(block, UI_BLOCK_KEEP_OPEN|UI_BLOCK_RET_1|UI_BLOCK_MOVEMOUSE_QUIT);

	/* if register is not enabled, the operator gets freed on OPERATOR_FINISHED
	 * ui_apply_but_funcs_after calls ED_undo_operator_repeate_cb and crashes */
	assert(op->type->flag & OPTYPE_REGISTER);

	uiBlockSetHandleFunc(block, ED_undo_operator_repeat_cb_evt, arg_op);
	layout= uiBlockLayout(block, UI_LAYOUT_VERTICAL, UI_LAYOUT_PANEL, 0, 0, width, 20, style);

	if(ED_undo_valid(C, op->type->name)==0)
		uiLayoutSetEnabled(layout, 0);

	uiLayoutOperatorButs(C, layout, op, NULL, 'H', UI_LAYOUT_OP_SHOW_TITLE);

	uiPopupBoundsBlock(block, 4, 0, 0);
	uiEndBlock(C, block);

	return block;
}

/* Only invoked by OK button in popups created with wm_block_create_dialog() */
static void dialog_exec_cb(bContext *C, void *arg1, void *arg2)
{
	wmOperator *op= arg1;
	uiBlock *block= arg2;

	WM_operator_call(C, op);

	uiPupBlockClose(C, block);
}

static void dialog_check_cb(bContext *C, void *op_ptr, void *UNUSED(arg))
{
	wmOperator *op= op_ptr;
	if(op->type->check) {
		if(op->type->check(C, op)) {
			/* refresh */
		}
	}
}

/* Dialogs are popups that require user verification (click OK) before exec */
static uiBlock *wm_block_create_dialog(bContext *C, ARegion *ar, void *userData)
{
	struct { wmOperator *op; int width; int height; } * data = userData;
	wmOperator *op= data->op;
	uiBlock *block;
	uiLayout *layout;
	uiStyle *style= U.uistyles.first;

	block = uiBeginBlock(C, ar, "operator dialog", UI_EMBOSS);
	uiBlockClearFlag(block, UI_BLOCK_LOOP);
	uiBlockSetFlag(block, UI_BLOCK_KEEP_OPEN|UI_BLOCK_RET_1|UI_BLOCK_MOVEMOUSE_QUIT);

	layout= uiBlockLayout(block, UI_LAYOUT_VERTICAL, UI_LAYOUT_PANEL, 0, 0, data->width, data->height, style);
	
	uiBlockSetFunc(block, dialog_check_cb, op, NULL);

	uiLayoutOperatorButs(C, layout, op, NULL, 'H', UI_LAYOUT_OP_SHOW_TITLE);
	
	/* clear so the OK button is left alone */
	uiBlockSetFunc(block, NULL, NULL, NULL);

	/* new column so as not to interfear with custom layouts [#26436] */
	{
		uiBlock *col_block;
		uiLayout *col;
		uiBut *btn;

		col= uiLayoutColumn(layout, FALSE);
		col_block= uiLayoutGetBlock(col);
		/* Create OK button, the callback of which will execute op */
		btn= uiDefBut(col_block, BUT, 0, "OK", 0, -30, 0, 20, NULL, 0, 0, 0, 0, "");
		uiButSetFunc(btn, dialog_exec_cb, op, col_block);
	}

	/* center around the mouse */
	uiPopupBoundsBlock(block, 4, data->width/-2, data->height/2);
	uiEndBlock(C, block);

	return block;
}

static uiBlock *wm_operator_create_ui(bContext *C, ARegion *ar, void *userData)
{
	struct { wmOperator *op; int width; int height; } * data = userData;
	wmOperator *op= data->op;
	uiBlock *block;
	uiLayout *layout;
	uiStyle *style= U.uistyles.first;

	block= uiBeginBlock(C, ar, "opui_popup", UI_EMBOSS);
	uiBlockClearFlag(block, UI_BLOCK_LOOP);
	uiBlockSetFlag(block, UI_BLOCK_KEEP_OPEN|UI_BLOCK_RET_1|UI_BLOCK_MOVEMOUSE_QUIT);

	layout= uiBlockLayout(block, UI_LAYOUT_VERTICAL, UI_LAYOUT_PANEL, 0, 0, data->width, data->height, style);

	/* since ui is defined the auto-layout args are not used */
	uiLayoutOperatorButs(C, layout, op, NULL, 'V', 0);

	uiPopupBoundsBlock(block, 4, 0, 0);
	uiEndBlock(C, block);

	return block;
}

/* operator menu needs undo, for redo callback */
int WM_operator_props_popup(bContext *C, wmOperator *op, wmEvent *UNUSED(event))
{
	
	if((op->type->flag & OPTYPE_REGISTER)==0) {
		BKE_reportf(op->reports, RPT_ERROR, "Operator '%s' does not have register enabled, incorrect invoke function.", op->type->idname);
		return OPERATOR_CANCELLED;
	}
	
	ED_undo_push_op(C, op);
	wm_operator_register(C, op);

	uiPupBlock(C, wm_block_create_redo, op);

	return OPERATOR_RUNNING_MODAL;
}

int WM_operator_props_dialog_popup(bContext *C, wmOperator *op, int width, int height)
{
	struct { wmOperator *op; int width; int height; } data;
	
	data.op= op;
	data.width= width;
	data.height= height;

	/* op is not executed until popup OK but is clicked */
	uiPupBlock(C, wm_block_create_dialog, &data);

	return OPERATOR_RUNNING_MODAL;
}

int WM_operator_ui_popup(bContext *C, wmOperator *op, int width, int height)
{
	struct { wmOperator *op; int width; int height; } data;
	data.op = op;
	data.width = width;
	data.height = height;
	uiPupBlock(C, wm_operator_create_ui, &data);
	return OPERATOR_RUNNING_MODAL;
}

int WM_operator_redo_popup(bContext *C, wmOperator *op)
{
	/* CTX_wm_reports(C) because operator is on stack, not active in event system */
	if((op->type->flag & OPTYPE_REGISTER)==0) {
		BKE_reportf(CTX_wm_reports(C), RPT_ERROR, "Operator redo '%s' does not have register enabled, incorrect invoke function.", op->type->idname);
		return OPERATOR_CANCELLED;
	}
	if(op->type->poll && op->type->poll(C)==0) {
		BKE_reportf(CTX_wm_reports(C), RPT_ERROR, "Operator redo '%s': wrong context.", op->type->idname);
		return OPERATOR_CANCELLED;
	}
	
	uiPupBlock(C, wm_block_create_redo, op);

	return OPERATOR_CANCELLED;
}

/* ***************** Debug menu ************************* */

static int wm_debug_menu_exec(bContext *C, wmOperator *op)
{
	G.rt= RNA_int_get(op->ptr, "debug_value");
	ED_screen_refresh(CTX_wm_manager(C), CTX_wm_window(C));
	WM_event_add_notifier(C, NC_WINDOW, NULL);

	return OPERATOR_FINISHED;	
}

static int wm_debug_menu_invoke(bContext *C, wmOperator *op, wmEvent *UNUSED(event))
{
	RNA_int_set(op->ptr, "debug_value", G.rt);
	return WM_operator_props_dialog_popup(C, op, 180, 20);
}

static void WM_OT_debug_menu(wmOperatorType *ot)
{
	ot->name= "Debug Menu";
	ot->idname= "WM_OT_debug_menu";
	ot->description= "Open a popup to set the debug level";
	
	ot->invoke= wm_debug_menu_invoke;
	ot->exec= wm_debug_menu_exec;
	ot->poll= WM_operator_winactive;
	
	RNA_def_int(ot->srna, "debug_value", 0, -10000, 10000, "Debug Value", "", INT_MIN, INT_MAX);
}


/* ***************** Splash Screen ************************* */

static void wm_block_splash_close(bContext *C, void *arg_block, void *UNUSED(arg))
{
	uiPupBlockClose(C, arg_block);
}

static uiBlock *wm_block_create_splash(bContext *C, ARegion *ar, void *arg_unused);

/* XXX: hack to refresh splash screen with updated prest menu name,
 * since popup blocks don't get regenerated like panels do */
static void wm_block_splash_refreshmenu (bContext *UNUSED(C), void *UNUSED(arg_block), void *UNUSED(arg))
{
	/* ugh, causes crashes in other buttons, disabling for now until 
	 * a better fix
	uiPupBlockClose(C, arg_block);
	uiPupBlock(C, wm_block_create_splash, NULL);
	  */
}

static int wm_resource_check_prev(void)
{

	char *res= BLI_get_folder_version(BLENDER_RESOURCE_PATH_USER, BLENDER_VERSION, TRUE);

	// if(res) printf("USER: %s\n", res);

	if(res == NULL) {
		res= BLI_get_folder_version(BLENDER_RESOURCE_PATH_LOCAL, BLENDER_VERSION, TRUE);
	}

	// if(res) printf("LOCAL: %s\n", res);

	if(res == NULL) {
		int res_dir[]= {BLENDER_RESOURCE_PATH_USER, BLENDER_RESOURCE_PATH_LOCAL, -1};
		int i= 0;

		for(i= 0; res_dir[i] != -1; i++) {
			if(BLI_get_folder_version(res_dir[i], BLENDER_VERSION - 1, TRUE)) {
				return TRUE;
			}
		}
	}

	return FALSE;
}

static uiBlock *wm_block_create_splash(bContext *C, ARegion *ar, void *UNUSED(arg))
{
	uiBlock *block;
	uiBut *but;
	uiLayout *layout, *split, *col;
	uiStyle *style= U.uistyles.first;
	struct RecentFile *recent;
	int i;
	MenuType *mt= WM_menutype_find("USERPREF_MT_splash", TRUE);
	char url[64];
	
#ifdef NAN_BUILDINFO
	int ver_width, rev_width;
	char *version_str = NULL;
	char *revision_str = NULL;
	char version_buf[128];
	char revision_buf[128];
	extern char build_rev[];
	
	version_str = &version_buf[0];
	revision_str = &revision_buf[0];
	
	sprintf(version_str, "%d.%02d.%d", BLENDER_VERSION/100, BLENDER_VERSION%100, BLENDER_SUBVERSION);
	sprintf(revision_str, "r%s", build_rev);
	
	BLF_size(style->widgetlabel.uifont_id, style->widgetlabel.points, U.dpi);
	ver_width = (int)BLF_width(style->widgetlabel.uifont_id, version_str) + 5;
	rev_width = (int)BLF_width(style->widgetlabel.uifont_id, revision_str) + 5;
#endif //NAN_BUILDINFO

	block= uiBeginBlock(C, ar, "_popup", UI_EMBOSS);
	uiBlockSetFlag(block, UI_BLOCK_KEEP_OPEN);
	
	but= uiDefBut(block, BUT_IMAGE, 0, "", 0, 10, 501, 282, NULL, 0.0, 0.0, 0, 0, "");
	uiButSetFunc(but, wm_block_splash_close, block, NULL);
	uiBlockSetFunc(block, wm_block_splash_refreshmenu, block, NULL);
	
#ifdef NAN_BUILDINFO	
	uiDefBut(block, LABEL, 0, version_str, 494-ver_width, 282-24, ver_width, 20, NULL, 0, 0, 0, 0, NULL);
	uiDefBut(block, LABEL, 0, revision_str, 494-rev_width, 282-36, rev_width, 20, NULL, 0, 0, 0, 0, NULL);
#endif //NAN_BUILDINFO
	
	layout= uiBlockLayout(block, UI_LAYOUT_VERTICAL, UI_LAYOUT_PANEL, 10, 2, 480, 110, style);
	
	uiBlockSetEmboss(block, UI_EMBOSS);
	/* show the splash menu (containing interaction presets), using python */
	if (mt) {
		Menu menu= {NULL};
		menu.layout= layout;
		menu.type= mt;
		mt->draw(C, &menu);

//		wmWindowManager *wm= CTX_wm_manager(C);
//		uiItemM(layout, C, "USERPREF_MT_keyconfigs", U.keyconfigstr, ICON_NONE);
	}
	
	uiBlockSetEmboss(block, UI_EMBOSSP);
	uiLayoutSetOperatorContext(layout, WM_OP_EXEC_REGION_WIN);
	
	split = uiLayoutSplit(layout, 0, 0);
	col = uiLayoutColumn(split, 0);
	uiItemL(col, "Links", ICON_NONE);
	uiItemStringO(col, "Donations", ICON_URL, "WM_OT_url_open", "url", "http://www.blender.org/blenderorg/blender-foundation/donation-payment/");
	uiItemStringO(col, "Release Log", ICON_URL, "WM_OT_url_open", "url", "http://www.blender.org/development/release-logs/blender-256-beta/");
	uiItemStringO(col, "Manual", ICON_URL, "WM_OT_url_open", "url", "http://wiki.blender.org/index.php/Doc:Manual");
	uiItemStringO(col, "Blender Website", ICON_URL, "WM_OT_url_open", "url", "http://www.blender.org/");
	uiItemStringO(col, "User Community", ICON_URL, "WM_OT_url_open", "url", "http://www.blender.org/community/user-community/"); // 
	BLI_snprintf(url, sizeof(url), "http://www.blender.org/documentation/blender_python_api_%d_%d_%d", BLENDER_VERSION/100, BLENDER_VERSION%100, BLENDER_SUBVERSION);
	uiItemStringO(col, "Python API Reference", ICON_URL, "WM_OT_url_open", "url", url);
	uiItemL(col, "", ICON_NONE);

	col = uiLayoutColumn(split, 0);
	uiItemL(col, "Recent", ICON_NONE);
	for(recent = G.recent_files.first, i=0; (i<5) && (recent); recent = recent->next, i++) {
		uiItemStringO(col, BLI_path_basename(recent->filepath), ICON_FILE_BLEND, "WM_OT_open_mainfile", "filepath", recent->filepath);
	}

	if(wm_resource_check_prev()) {
		uiItemS(col);
		uiItemO(col, NULL, ICON_NEW, "WM_OT_copy_prev_settings");
	}

	uiItemS(col);
	uiItemO(col, NULL, ICON_RECOVER_LAST, "WM_OT_recover_last_session");
	uiItemL(col, "", ICON_NONE);
	
	uiCenteredBoundsBlock(block, 0);
	uiEndBlock(C, block);
	
	return block;
}

static int wm_splash_invoke(bContext *C, wmOperator *UNUSED(op), wmEvent *UNUSED(event))
{
	uiPupBlock(C, wm_block_create_splash, NULL);
	
	return OPERATOR_FINISHED;
}

static void WM_OT_splash(wmOperatorType *ot)
{
	ot->name= "Splash Screen";
	ot->idname= "WM_OT_splash";
	ot->description= "Opens a blocking popup region with release info";
	
	ot->invoke= wm_splash_invoke;
	ot->poll= WM_operator_winactive;
}


/* ***************** Search menu ************************* */
static void operator_call_cb(struct bContext *C, void *UNUSED(arg1), void *arg2)
{
	wmOperatorType *ot= arg2;
	
	if(ot)
		WM_operator_name_call(C, ot->idname, WM_OP_INVOKE_DEFAULT, NULL);
}

static void operator_search_cb(const struct bContext *C, void *UNUSED(arg), const char *str, uiSearchItems *items)
{
	wmOperatorType *ot = WM_operatortype_first();
	
	for(; ot; ot= ot->next) {
		
		if(BLI_strcasestr(ot->name, str)) {
			if(WM_operator_poll((bContext*)C, ot)) {
				char name[256];
				int len= strlen(ot->name);
				
				/* display name for menu, can hold hotkey */
				BLI_strncpy(name, ot->name, 256);
				
				/* check for hotkey */
				if(len < 256-6) {
					if(WM_key_event_operator_string(C, ot->idname, WM_OP_EXEC_DEFAULT, NULL, &name[len+1], 256-len-1))
						name[len]= '|';
				}
				
				if(0==uiSearchItemAdd(items, name, ot, 0))
					break;
			}
		}
	}
}

static uiBlock *wm_block_search_menu(bContext *C, ARegion *ar, void *UNUSED(arg_op))
{
	static char search[256]= "";
	wmEvent event;
	wmWindow *win= CTX_wm_window(C);
	uiBlock *block;
	uiBut *but;
	
	block= uiBeginBlock(C, ar, "_popup", UI_EMBOSS);
	uiBlockSetFlag(block, UI_BLOCK_LOOP|UI_BLOCK_RET_1|UI_BLOCK_MOVEMOUSE_QUIT);
	
	but= uiDefSearchBut(block, search, 0, ICON_VIEWZOOM, 256, 10, 10, 180, 19, 0, 0, "");
	uiButSetSearchFunc(but, operator_search_cb, NULL, operator_call_cb, NULL);
	
	/* fake button, it holds space for search items */
	uiDefBut(block, LABEL, 0, "", 10, 10 - uiSearchBoxhHeight(), 180, uiSearchBoxhHeight(), NULL, 0, 0, 0, 0, NULL);
	
	uiPopupBoundsBlock(block, 6, 0, -20); /* move it downwards, mouse over button */
	uiEndBlock(C, block);
	
	event= *(win->eventstate);	/* XXX huh huh? make api call */
	event.type= EVT_BUT_OPEN;
	event.val= KM_PRESS;
	event.customdata= but;
	event.customdatafree= FALSE;
	wm_event_add(win, &event);
	
	return block;
}

static int wm_search_menu_exec(bContext *UNUSED(C), wmOperator *UNUSED(op))
{
	return OPERATOR_FINISHED;	
}

static int wm_search_menu_invoke(bContext *C, wmOperator *op, wmEvent *UNUSED(event))
{
	uiPupBlock(C, wm_block_search_menu, op);
	
	return OPERATOR_CANCELLED;
}

/* op->poll */
static int wm_search_menu_poll(bContext *C)
{
	if(CTX_wm_window(C)==NULL) return 0;
	if(CTX_wm_area(C) && CTX_wm_area(C)->spacetype==SPACE_CONSOLE) return 0;  // XXX - so we can use the shortcut in the console
	if(CTX_wm_area(C) && CTX_wm_area(C)->spacetype==SPACE_TEXT) return 0;  // XXX - so we can use the spacebar in the text editor
	if(CTX_data_edit_object(C) && CTX_data_edit_object(C)->type==OB_FONT) return 0; // XXX - so we can use the spacebar for entering text
	return 1;
}

static void WM_OT_search_menu(wmOperatorType *ot)
{
	ot->name= "Search Menu";
	ot->idname= "WM_OT_search_menu";
	
	ot->invoke= wm_search_menu_invoke;
	ot->exec= wm_search_menu_exec;
	ot->poll= wm_search_menu_poll;
}

static int wm_call_menu_exec(bContext *C, wmOperator *op)
{
	char idname[BKE_ST_MAXNAME];
	RNA_string_get(op->ptr, "name", idname);

	uiPupMenuInvoke(C, idname);

	return OPERATOR_CANCELLED;
}

static void WM_OT_call_menu(wmOperatorType *ot)
{
	ot->name= "Call Menu";
	ot->idname= "WM_OT_call_menu";

	ot->exec= wm_call_menu_exec;
	ot->poll= WM_operator_winactive;

	RNA_def_string(ot->srna, "name", "", BKE_ST_MAXNAME, "Name", "Name of the menu");
}

/* ************ window / screen operator definitions ************** */

/* this poll functions is needed in place of WM_operator_winactive
 * while it crashes on full screen */
static int wm_operator_winactive_normal(bContext *C)
{
	wmWindow *win= CTX_wm_window(C);

	if(win==NULL || win->screen==NULL || win->screen->full != SCREENNORMAL)
		return 0;

	return 1;
}

static void WM_OT_window_duplicate(wmOperatorType *ot)
{
	ot->name= "Duplicate Window";
	ot->idname= "WM_OT_window_duplicate";
	ot->description="Duplicate the current Blender window";
		
	ot->exec= wm_window_duplicate_exec;
	ot->poll= wm_operator_winactive_normal;
}

static void WM_OT_save_homefile(wmOperatorType *ot)
{
	ot->name= "Save User Settings";
	ot->idname= "WM_OT_save_homefile";
	ot->description="Make the current file the default .blend file";
		
	ot->invoke= WM_operator_confirm;
	ot->exec= WM_write_homefile;
	ot->poll= WM_operator_winactive;
}

static void WM_OT_read_homefile(wmOperatorType *ot)
{
	ot->name= "Reload Start-Up File";
	ot->idname= "WM_OT_read_homefile";
	ot->description="Open the default file (doesn't save the current file)";
	
	ot->invoke= WM_operator_confirm;
	ot->exec= WM_read_homefile_exec;
	/* ommit poll to run in background mode */
}

static void WM_OT_read_factory_settings(wmOperatorType *ot)
{
	ot->name= "Load Factory Settings";
	ot->idname= "WM_OT_read_factory_settings";
	ot->description="Load default file and user preferences";
	
	ot->invoke= WM_operator_confirm;
	ot->exec= WM_read_homefile_exec;
	/* ommit poll to run in background mode */
}

/* *************** open file **************** */

static void open_set_load_ui(wmOperator *op)
{
	if(!RNA_property_is_set(op->ptr, "load_ui"))
		RNA_boolean_set(op->ptr, "load_ui", !(U.flag & USER_FILENOUI));
}

static void open_set_use_scripts(wmOperator *op)
{
	if(!RNA_property_is_set(op->ptr, "use_scripts")) {
		/* use G_SCRIPT_AUTOEXEC rather then the userpref because this means if
		 * the flag has been disabled from the command line, then opening
		 * from the menu wont enable this setting. */
		RNA_boolean_set(op->ptr, "use_scripts", (G.f & G_SCRIPT_AUTOEXEC));
	}
}

static int wm_open_mainfile_invoke(bContext *C, wmOperator *op, wmEvent *UNUSED(event))
{
	const char *openname= G.main->name;

	/* if possible, get the name of the most recently used .blend file */
	if (G.recent_files.first) {
		struct RecentFile *recent = G.recent_files.first;
		openname = recent->filepath;
	}

	RNA_string_set(op->ptr, "filepath", openname);
	open_set_load_ui(op);
	open_set_use_scripts(op);

	WM_event_add_fileselect(C, op);

	return OPERATOR_RUNNING_MODAL;
}

static int wm_open_mainfile_exec(bContext *C, wmOperator *op)
{
	char path[FILE_MAX];

	RNA_string_get(op->ptr, "filepath", path);
	open_set_load_ui(op);
	open_set_use_scripts(op);

	if(RNA_boolean_get(op->ptr, "load_ui"))
		G.fileflags &= ~G_FILE_NO_UI;
	else
		G.fileflags |= G_FILE_NO_UI;
		
	if(RNA_boolean_get(op->ptr, "use_scripts"))
		G.f |= G_SCRIPT_AUTOEXEC;
	else
		G.f &= ~G_SCRIPT_AUTOEXEC;
	
	// XXX wm in context is not set correctly after WM_read_file -> crash
	// do it before for now, but is this correct with multiple windows?
	WM_event_add_notifier(C, NC_WINDOW, NULL);

	WM_read_file(C, path, op->reports);
	
	return OPERATOR_FINISHED;
}

static void WM_OT_open_mainfile(wmOperatorType *ot)
{
	ot->name= "Open Blender File";
	ot->idname= "WM_OT_open_mainfile";
	ot->description="Open a Blender file";
	
	ot->invoke= wm_open_mainfile_invoke;
	ot->exec= wm_open_mainfile_exec;
	ot->poll= WM_operator_winactive;
	
	WM_operator_properties_filesel(ot, FOLDERFILE|BLENDERFILE, FILE_BLENDER, FILE_OPENFILE, WM_FILESEL_FILEPATH);

	RNA_def_boolean(ot->srna, "load_ui", 1, "Load UI", "Load user interface setup in the .blend file");
	RNA_def_boolean(ot->srna, "use_scripts", 1, "Trusted Source", "Allow blend file execute scripts automatically, default available from system preferences");
}

/* **************** link/append *************** */

static int wm_link_append_invoke(bContext *C, wmOperator *op, wmEvent *UNUSED(event))
{
	if(!RNA_property_is_set(op->ptr, "relative_path"))
		RNA_boolean_set(op->ptr, "relative_path", U.flag & USER_RELPATHS);

	if(RNA_property_is_set(op->ptr, "filepath")) {
		return WM_operator_call(C, op);
	} 
	else {
		/* XXX TODO solve where to get last linked library from */
		RNA_string_set(op->ptr, "filepath", G.lib);
		WM_event_add_fileselect(C, op);
		return OPERATOR_RUNNING_MODAL;
	}
}

static short wm_link_append_flag(wmOperator *op)
{
	short flag= 0;

	if(RNA_boolean_get(op->ptr, "autoselect")) flag |= FILE_AUTOSELECT;
	if(RNA_boolean_get(op->ptr, "active_layer")) flag |= FILE_ACTIVELAY;
	if(RNA_boolean_get(op->ptr, "relative_path")) flag |= FILE_RELPATH;
	if(RNA_boolean_get(op->ptr, "link")) flag |= FILE_LINK;
	if(RNA_boolean_get(op->ptr, "instance_groups")) flag |= FILE_GROUP_INSTANCE;

	return flag;
}

static int wm_link_append_exec(bContext *C, wmOperator *op)
{
	Main *bmain= CTX_data_main(C);
	Scene *scene= CTX_data_scene(C);
	Main *mainl= NULL;
	BlendHandle *bh;
	PropertyRNA *prop;
	char name[FILE_MAX], dir[FILE_MAX], libname[FILE_MAX], group[GROUP_MAX];
	int idcode, totfiles=0;
	short flag;

	name[0] = '\0';
	RNA_string_get(op->ptr, "filename", name);
	RNA_string_get(op->ptr, "directory", dir);

	/* test if we have a valid data */
	if(BLO_is_a_library(dir, libname, group) == 0) {
		BKE_report(op->reports, RPT_ERROR, "Not a library");
		return OPERATOR_CANCELLED;
	}
	else if(group[0] == 0) {
		BKE_report(op->reports, RPT_ERROR, "Nothing indicated");
		return OPERATOR_CANCELLED;
	}
	else if(BLI_path_cmp(bmain->name, libname) == 0) {
		BKE_report(op->reports, RPT_ERROR, "Cannot use current file as library");
		return OPERATOR_CANCELLED;
	}

	/* check if something is indicated for append/link */
	prop = RNA_struct_find_property(op->ptr, "files");
	if(prop) {
		totfiles= RNA_property_collection_length(op->ptr, prop);
		if(totfiles == 0) {
			if(name[0] == '\0') {
				BKE_report(op->reports, RPT_ERROR, "Nothing indicated");
				return OPERATOR_CANCELLED;
			}
		}
	}
	else if(name[0] == '\0') {
		BKE_report(op->reports, RPT_ERROR, "Nothing indicated");
		return OPERATOR_CANCELLED;
	}

	bh = BLO_blendhandle_from_file(libname, op->reports);

	if(bh == NULL) {
		/* unlikely since we just browsed it, but possible
		 * error reports will have been made by BLO_blendhandle_from_file() */
		return OPERATOR_CANCELLED;
	}


	/* from here down, no error returns */

	idcode = BKE_idcode_from_name(group);

	/* now we have or selected, or an indicated file */
	if(RNA_boolean_get(op->ptr, "autoselect"))
		scene_deselect_all(scene);

	
	flag = wm_link_append_flag(op);

	/* sanity checks for flag */
	if(scene->id.lib && (flag & FILE_GROUP_INSTANCE)) {
		/* TODO, user never gets this message */
		BKE_reportf(op->reports, RPT_WARNING, "Scene '%s' is linked, group instance disabled", scene->id.name+2);
		flag &= ~FILE_GROUP_INSTANCE;
	}


	/* tag everything, all untagged data can be made local
	 * its also generally useful to know what is new
	 *
	 * take extra care flag_all_listbases_ids(LIB_LINK_TAG, 0) is called after! */
	flag_all_listbases_ids(LIB_PRE_EXISTING, 1);

	/* here appending/linking starts */
	mainl = BLO_library_append_begin(C, &bh, libname);
	if(totfiles == 0) {
		BLO_library_append_named_part(C, mainl, &bh, name, idcode, flag);
	}
	else {
		RNA_BEGIN(op->ptr, itemptr, "files") {
			RNA_string_get(&itemptr, "name", name);
			BLO_library_append_named_part(C, mainl, &bh, name, idcode, flag);
		}
		RNA_END;
	}
	BLO_library_append_end(C, mainl, &bh, idcode, flag);
	
	/* mark all library linked objects to be updated */
	recalc_all_library_objects(bmain);

	/* append, rather than linking */
	if((flag & FILE_LINK)==0) {
		Library *lib= BLI_findstring(&bmain->library, libname, offsetof(Library, filepath));
		if(lib)	all_local(lib, 1);
		else	BLI_assert(!"cant find name of just added library!");
	}

	/* important we unset, otherwise these object wont
	 * link into other scenes from this blend file */
	flag_all_listbases_ids(LIB_PRE_EXISTING, 0);

	/* recreate dependency graph to include new objects */
	DAG_scene_sort(bmain, scene);
	DAG_ids_flush_update(bmain, 0);

	BLO_blendhandle_close(bh);

	/* XXX TODO: align G.lib with other directory storage (like last opened image etc...) */
	BLI_strncpy(G.lib, dir, FILE_MAX);

	WM_event_add_notifier(C, NC_WINDOW, NULL);

	return OPERATOR_FINISHED;
}

static void WM_OT_link_append(wmOperatorType *ot)
{
	ot->name= "Link/Append from Library";
	ot->idname= "WM_OT_link_append";
	ot->description= "Link or Append from a Library .blend file";
	
	ot->invoke= wm_link_append_invoke;
	ot->exec= wm_link_append_exec;
	ot->poll= WM_operator_winactive;
	
	ot->flag |= OPTYPE_UNDO;

	WM_operator_properties_filesel(ot, FOLDERFILE|BLENDERFILE, FILE_LOADLIB, FILE_OPENFILE, WM_FILESEL_FILEPATH|WM_FILESEL_DIRECTORY|WM_FILESEL_FILENAME| WM_FILESEL_RELPATH);
	
	RNA_def_boolean(ot->srna, "link", 1, "Link", "Link the objects or datablocks rather than appending");
	RNA_def_boolean(ot->srna, "autoselect", 1, "Select", "Select the linked objects");
	RNA_def_boolean(ot->srna, "active_layer", 1, "Active Layer", "Put the linked objects on the active layer");
	RNA_def_boolean(ot->srna, "instance_groups", 1, "Instance Groups", "Create instances for each group as a DupliGroup");

	RNA_def_collection_runtime(ot->srna, "files", &RNA_OperatorFileListElement, "Files", "");
}	

/* *************** recover last session **************** */

static int wm_recover_last_session_exec(bContext *C, wmOperator *op)
{
	char filename[FILE_MAX];

	G.fileflags |= G_FILE_RECOVER;

	// XXX wm in context is not set correctly after WM_read_file -> crash
	// do it before for now, but is this correct with multiple windows?
	WM_event_add_notifier(C, NC_WINDOW, NULL);

	/* load file */
	BLI_make_file_string("/", filename, btempdir, "quit.blend");
	WM_read_file(C, filename, op->reports);

	G.fileflags &= ~G_FILE_RECOVER;
	return OPERATOR_FINISHED;
}

static void WM_OT_recover_last_session(wmOperatorType *ot)
{
	ot->name= "Recover Last Session";
	ot->idname= "WM_OT_recover_last_session";
	ot->description="Open the last closed file (\"quit.blend\")";
	
	ot->exec= wm_recover_last_session_exec;
	ot->poll= WM_operator_winactive;
}

/* *************** recover auto save **************** */

static int wm_recover_auto_save_exec(bContext *C, wmOperator *op)
{
	char path[FILE_MAX];

	RNA_string_get(op->ptr, "filepath", path);

	G.fileflags |= G_FILE_RECOVER;

	// XXX wm in context is not set correctly after WM_read_file -> crash
	// do it before for now, but is this correct with multiple windows?
	WM_event_add_notifier(C, NC_WINDOW, NULL);

	/* load file */
	WM_read_file(C, path, op->reports);

	G.fileflags &= ~G_FILE_RECOVER;

	return OPERATOR_FINISHED;
}

static int wm_recover_auto_save_invoke(bContext *C, wmOperator *op, wmEvent *UNUSED(event))
{
	char filename[FILE_MAX];

	wm_autosave_location(filename);
	RNA_string_set(op->ptr, "filepath", filename);
	WM_event_add_fileselect(C, op);

	return OPERATOR_RUNNING_MODAL;
}

static void WM_OT_recover_auto_save(wmOperatorType *ot)
{
	ot->name= "Recover Auto Save";
	ot->idname= "WM_OT_recover_auto_save";
	ot->description="Open an automatically saved file to recover it";
	
	ot->exec= wm_recover_auto_save_exec;
	ot->invoke= wm_recover_auto_save_invoke;
	ot->poll= WM_operator_winactive;

	WM_operator_properties_filesel(ot, BLENDERFILE, FILE_BLENDER, FILE_OPENFILE, WM_FILESEL_FILEPATH);
}

/* *************** save file as **************** */

static void untitled(char *name)
{
	if(G.save_over == 0 && strlen(name) < FILE_MAX-16) {
		char *c= BLI_last_slash(name);
		
		if(c)
			strcpy(&c[1], "untitled.blend");
		else
			strcpy(name, "untitled.blend");
	}
}

static void save_set_compress(wmOperator *op)
{
	if(!RNA_property_is_set(op->ptr, "compress")) {
		if(G.save_over) /* keep flag for existing file */
			RNA_boolean_set(op->ptr, "compress", G.fileflags & G_FILE_COMPRESS);
		else /* use userdef for new file */
			RNA_boolean_set(op->ptr, "compress", U.flag & USER_FILECOMPRESS);
	}
}

static int wm_save_as_mainfile_invoke(bContext *C, wmOperator *op, wmEvent *UNUSED(event))
{
	char name[FILE_MAX];

	save_set_compress(op);
	
	/* if not saved before, get the name of the most recently used .blend file */
	if(G.main->name[0]==0 && G.recent_files.first) {
		struct RecentFile *recent = G.recent_files.first;
		BLI_strncpy(name, recent->filepath, FILE_MAX);
	}
	else
		BLI_strncpy(name, G.main->name, FILE_MAX);
	
	untitled(name);
	RNA_string_set(op->ptr, "filepath", name);
	
	WM_event_add_fileselect(C, op);

	return OPERATOR_RUNNING_MODAL;
}

/* function used for WM_OT_save_mainfile too */
static int wm_save_as_mainfile_exec(bContext *C, wmOperator *op)
{
	char path[FILE_MAX];
	int fileflags;
	int copy=0;

	save_set_compress(op);
	
	if(RNA_property_is_set(op->ptr, "filepath"))
		RNA_string_get(op->ptr, "filepath", path);
	else {
		BLI_strncpy(path, G.main->name, FILE_MAX);
		untitled(path);
	}

	if(RNA_property_is_set(op->ptr, "copy"))
		copy = RNA_boolean_get(op->ptr, "copy");
	
	fileflags= G.fileflags;

	/* set compression flag */
	if(RNA_boolean_get(op->ptr, "compress"))		fileflags |=  G_FILE_COMPRESS;
	else											fileflags &= ~G_FILE_COMPRESS;
	if(RNA_boolean_get(op->ptr, "relative_remap"))	fileflags |=  G_FILE_RELATIVE_REMAP;
	else											fileflags &= ~G_FILE_RELATIVE_REMAP;

	if ( WM_write_file(C, path, fileflags, op->reports, copy) != 0)
		return OPERATOR_CANCELLED;

	WM_event_add_notifier(C, NC_WM|ND_FILESAVE, NULL);

	return OPERATOR_FINISHED;
}

/* function used for WM_OT_save_mainfile too */
static int blend_save_check(bContext *UNUSED(C), wmOperator *op)
{
	char filepath[FILE_MAX];
	RNA_string_get(op->ptr, "filepath", filepath);
	if(BLI_replace_extension(filepath, sizeof(filepath), ".blend")) {
		RNA_string_set(op->ptr, "filepath", filepath);
		return TRUE;
	}
	return FALSE;
}

static void WM_OT_save_as_mainfile(wmOperatorType *ot)
{
	ot->name= "Save As Blender File";
	ot->idname= "WM_OT_save_as_mainfile";
	ot->description="Save the current file in the desired location";
	
	ot->invoke= wm_save_as_mainfile_invoke;
	ot->exec= wm_save_as_mainfile_exec;
	ot->check= blend_save_check;
	/* ommit window poll so this can work in background mode */

	WM_operator_properties_filesel(ot, FOLDERFILE|BLENDERFILE, FILE_BLENDER, FILE_SAVE, WM_FILESEL_FILEPATH);
	RNA_def_boolean(ot->srna, "compress", 0, "Compress", "Write compressed .blend file");
	RNA_def_boolean(ot->srna, "relative_remap", 1, "Remap Relative", "Remap relative paths when saving in a different directory");
	RNA_def_boolean(ot->srna, "copy", 0, "Save Copy", "Save a copy of the actual working state but does not make saved file active.");
}

/* *************** save file directly ******** */

static int wm_save_mainfile_invoke(bContext *C, wmOperator *op, wmEvent *UNUSED(event))
{
	char name[FILE_MAX];
	int check_existing=1;
	
	/* cancel if no active window */
	if (CTX_wm_window(C) == NULL)
		return OPERATOR_CANCELLED;

	save_set_compress(op);

	/* if not saved before, get the name of the most recently used .blend file */
	if(G.main->name[0]==0 && G.recent_files.first) {
		struct RecentFile *recent = G.recent_files.first;
		BLI_strncpy(name, recent->filepath, FILE_MAX);
	}
	else
		BLI_strncpy(name, G.main->name, FILE_MAX);

	untitled(name);
	
	RNA_string_set(op->ptr, "filepath", name);
	
	if (RNA_struct_find_property(op->ptr, "check_existing"))
		if (RNA_boolean_get(op->ptr, "check_existing")==0)
			check_existing = 0;
	
	if (G.save_over) {
		if (check_existing)
			uiPupMenuSaveOver(C, op, name);
		else {
			wm_save_as_mainfile_exec(C, op);
		}
	} else {
		WM_event_add_fileselect(C, op);
	}
	
	return OPERATOR_RUNNING_MODAL;
}

static void WM_OT_save_mainfile(wmOperatorType *ot)
{
	ot->name= "Save Blender File";
	ot->idname= "WM_OT_save_mainfile";
	ot->description="Save the current Blender file";
	
	ot->invoke= wm_save_mainfile_invoke;
	ot->exec= wm_save_as_mainfile_exec;
	ot->check= blend_save_check;
	ot->poll= NULL;
	
	WM_operator_properties_filesel(ot, FOLDERFILE|BLENDERFILE, FILE_BLENDER, FILE_SAVE, WM_FILESEL_FILEPATH);
	RNA_def_boolean(ot->srna, "compress", 0, "Compress", "Write compressed .blend file");
	RNA_def_boolean(ot->srna, "relative_remap", 0, "Remap Relative", "Remap relative paths when saving in a different directory");
}

/* XXX: move these collada operators to a more appropriate place */
#ifdef WITH_COLLADA

#include "../../collada/collada.h"

static int wm_collada_export_invoke(bContext *C, wmOperator *op, wmEvent *UNUSED(event))
{	
	if(!RNA_property_is_set(op->ptr, "filepath")) {
		char filepath[FILE_MAX];
		BLI_strncpy(filepath, G.main->name, sizeof(filepath));
		BLI_replace_extension(filepath, sizeof(filepath), ".dae");
		RNA_string_set(op->ptr, "filepath", filepath);
	}

	WM_event_add_fileselect(C, op);

	return OPERATOR_RUNNING_MODAL;
}

/* function used for WM_OT_save_mainfile too */
static int wm_collada_export_exec(bContext *C, wmOperator *op)
{
	char filename[FILE_MAX];
	
	if(!RNA_property_is_set(op->ptr, "filepath")) {
		BKE_report(op->reports, RPT_ERROR, "No filename given");
		return OPERATOR_CANCELLED;
	}
	
	RNA_string_get(op->ptr, "filepath", filename);
	collada_export(CTX_data_scene(C), filename);
	
	return OPERATOR_FINISHED;
}

static void WM_OT_collada_export(wmOperatorType *ot)
{
	ot->name= "Export COLLADA";
	ot->idname= "WM_OT_collada_export";
	
	ot->invoke= wm_collada_export_invoke;
	ot->exec= wm_collada_export_exec;
	ot->poll= WM_operator_winactive;
	
	WM_operator_properties_filesel(ot, FOLDERFILE|COLLADAFILE, FILE_BLENDER, FILE_SAVE, WM_FILESEL_FILEPATH);
}

/* function used for WM_OT_save_mainfile too */
static int wm_collada_import_exec(bContext *C, wmOperator *op)
{
	char filename[FILE_MAX];
	
	if(!RNA_property_is_set(op->ptr, "filepath")) {
		BKE_report(op->reports, RPT_ERROR, "No filename given");
		return OPERATOR_CANCELLED;
	}

	RNA_string_get(op->ptr, "filepath", filename);
	collada_import(C, filename);
	
	return OPERATOR_FINISHED;
}

static void WM_OT_collada_import(wmOperatorType *ot)
{
	ot->name= "Import COLLADA";
	ot->idname= "WM_OT_collada_import";
	
	ot->invoke= WM_operator_filesel;
	ot->exec= wm_collada_import_exec;
	ot->poll= WM_operator_winactive;
	
	WM_operator_properties_filesel(ot, FOLDERFILE|COLLADAFILE, FILE_BLENDER, FILE_OPENFILE, WM_FILESEL_FILEPATH);
}

#endif



/* *********************** */

static void WM_OT_window_fullscreen_toggle(wmOperatorType *ot)
{
	ot->name= "Toggle Fullscreen";
	ot->idname= "WM_OT_window_fullscreen_toggle";
	ot->description="Toggle the current window fullscreen";

	ot->exec= wm_window_fullscreen_toggle_exec;
	ot->poll= WM_operator_winactive;
}

static int wm_exit_blender_op(bContext *C, wmOperator *op)
{
	WM_operator_free(op);
	
	WM_exit(C);	
	
	return OPERATOR_FINISHED;
}

static void WM_OT_quit_blender(wmOperatorType *ot)
{
	ot->name= "Quit Blender";
	ot->idname= "WM_OT_quit_blender";
	ot->description= "Quit Blender";

	ot->invoke= WM_operator_confirm;
	ot->exec= wm_exit_blender_op;
	ot->poll= WM_operator_winactive;
}

/* *********************** */
#if defined(WIN32)
static int console= 1;
void WM_console_toggle(bContext *UNUSED(C), short show)
{
	if(show) {
		ShowWindow(GetConsoleWindow(),SW_SHOW);
		console= 1;
	}
	else {
		ShowWindow(GetConsoleWindow(),SW_HIDE);
		console= 0;
	}
}

static int wm_console_toggle_op(bContext *C, wmOperator *UNUSED(op))
{
	if(console) {
		WM_console_toggle(C, 0);
	}
	else {
		WM_console_toggle(C, 1);
	}
	return OPERATOR_FINISHED;
}

static void WM_OT_console_toggle(wmOperatorType *ot)
{
	ot->name= "Toggle System Console";
	ot->idname= "WM_OT_console_toggle";
	ot->description= "Toggle System Console";
	
	ot->exec= wm_console_toggle_op;
	ot->poll= WM_operator_winactive;
}
#endif

/* ************ default paint cursors, draw always around cursor *********** */
/*
 - returns handler to free 
 - poll(bContext): returns 1 if draw should happen
 - draw(bContext): drawing callback for paint cursor
*/

void *WM_paint_cursor_activate(wmWindowManager *wm, int (*poll)(bContext *C),
				   wmPaintCursorDraw draw, void *customdata)
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

static int border_apply_rect(wmOperator *op)
{
	wmGesture *gesture= op->customdata;
	rcti *rect= gesture->customdata;
	
	if(rect->xmin==rect->xmax || rect->ymin==rect->ymax)
		return 0;

	
	/* operator arguments and storage. */
	RNA_int_set(op->ptr, "xmin", MIN2(rect->xmin, rect->xmax) );
	RNA_int_set(op->ptr, "ymin", MIN2(rect->ymin, rect->ymax) );
	RNA_int_set(op->ptr, "xmax", MAX2(rect->xmin, rect->xmax) );
	RNA_int_set(op->ptr, "ymax", MAX2(rect->ymin, rect->ymax) );

	return 1;
}

static int border_apply(bContext *C, wmOperator *op, int gesture_mode)
{
	if (!border_apply_rect(op))
		return 0;
	
	/* XXX weak; border should be configured for this without reading event types */
	if( RNA_struct_find_property(op->ptr, "gesture_mode") )
		RNA_int_set(op->ptr, "gesture_mode", gesture_mode);

	op->type->exec(C, op);
	return 1;
}

static void wm_gesture_end(bContext *C, wmOperator *op)
{
	wmGesture *gesture= op->customdata;
	
	WM_gesture_end(C, gesture);	/* frees gesture itself, and unregisters from window */
	op->customdata= NULL;

	ED_area_tag_redraw(CTX_wm_area(C));
	
	if( RNA_struct_find_property(op->ptr, "cursor") )
		WM_cursor_restore(CTX_wm_window(C));
}

int WM_border_select_invoke(bContext *C, wmOperator *op, wmEvent *event)
{
	if(ISTWEAK(event->type))
		op->customdata= WM_gesture_new(C, event, WM_GESTURE_RECT);
	else
		op->customdata= WM_gesture_new(C, event, WM_GESTURE_CROSS_RECT);

	/* add modal handler */
	WM_event_add_modal_handler(C, op);
	
	wm_gesture_tag_redraw(C);

	return OPERATOR_RUNNING_MODAL;
}

int WM_border_select_modal(bContext *C, wmOperator *op, wmEvent *event)
{
	wmGesture *gesture= op->customdata;
	rcti *rect= gesture->customdata;
	int sx, sy;
	
	if(event->type== MOUSEMOVE) {
		wm_subwindow_getorigin(CTX_wm_window(C), gesture->swinid, &sx, &sy);

		if(gesture->type==WM_GESTURE_CROSS_RECT && gesture->mode==0) {
			rect->xmin= rect->xmax= event->x - sx;
			rect->ymin= rect->ymax= event->y - sy;
		}
		else {
			rect->xmax= event->x - sx;
			rect->ymax= event->y - sy;
		}
		border_apply_rect(op);

		wm_gesture_tag_redraw(C);
	}
	else if (event->type==EVT_MODAL_MAP) {
		switch (event->val) {
		case GESTURE_MODAL_BEGIN:
			if(gesture->type==WM_GESTURE_CROSS_RECT && gesture->mode==0) {
				gesture->mode= 1;
				wm_gesture_tag_redraw(C);
			}
			break;
		case GESTURE_MODAL_SELECT:
		case GESTURE_MODAL_DESELECT:
		case GESTURE_MODAL_IN:
		case GESTURE_MODAL_OUT:
			if(border_apply(C, op, event->val)) {
				wm_gesture_end(C, op);
				return OPERATOR_FINISHED;
			}
			wm_gesture_end(C, op);
			return OPERATOR_CANCELLED;
			break;

		case GESTURE_MODAL_CANCEL:
			wm_gesture_end(C, op);
			return OPERATOR_CANCELLED;
		}

	}
//	// Allow view navigation???
//	else {
//		return OPERATOR_PASS_THROUGH;
//	}

	return OPERATOR_RUNNING_MODAL;
}

/* **************** circle gesture *************** */
/* works now only for selection or modal paint stuff, calls exec while hold mouse, exit on release */

#ifdef GESTURE_MEMORY
int circle_select_size= 25; // XXX - need some operator memory thing\!
#endif

int WM_gesture_circle_invoke(bContext *C, wmOperator *op, wmEvent *event)
{
	op->customdata= WM_gesture_new(C, event, WM_GESTURE_CIRCLE);
	
	/* add modal handler */
	WM_event_add_modal_handler(C, op);
	
	wm_gesture_tag_redraw(C);
	
	return OPERATOR_RUNNING_MODAL;
}

static void gesture_circle_apply(bContext *C, wmOperator *op)
{
	wmGesture *gesture= op->customdata;
	rcti *rect= gesture->customdata;
	
	if(RNA_int_get(op->ptr, "gesture_mode")==GESTURE_MODAL_NOP)
		return;

	/* operator arguments and storage. */
	RNA_int_set(op->ptr, "x", rect->xmin);
	RNA_int_set(op->ptr, "y", rect->ymin);
	RNA_int_set(op->ptr, "radius", rect->xmax);
	
	if(op->type->exec)
		op->type->exec(C, op);

#ifdef GESTURE_MEMORY
	circle_select_size= rect->xmax;
#endif
}

int WM_gesture_circle_modal(bContext *C, wmOperator *op, wmEvent *event)
{
	wmGesture *gesture= op->customdata;
	rcti *rect= gesture->customdata;
	int sx, sy;

	if(event->type== MOUSEMOVE) {
		wm_subwindow_getorigin(CTX_wm_window(C), gesture->swinid, &sx, &sy);

		rect->xmin= event->x - sx;
		rect->ymin= event->y - sy;

		wm_gesture_tag_redraw(C);

		if(gesture->mode)
			gesture_circle_apply(C, op);
	}
	else if (event->type==EVT_MODAL_MAP) {
		switch (event->val) {
		case GESTURE_MODAL_CIRCLE_ADD:
			rect->xmax += 2 + rect->xmax/10;
			wm_gesture_tag_redraw(C);
			break;
		case GESTURE_MODAL_CIRCLE_SUB:
			rect->xmax -= 2 + rect->xmax/10;
			if(rect->xmax < 1) rect->xmax= 1;
			wm_gesture_tag_redraw(C);
			break;
		case GESTURE_MODAL_SELECT:
		case GESTURE_MODAL_DESELECT:
		case GESTURE_MODAL_NOP:
			if(RNA_struct_find_property(op->ptr, "gesture_mode"))
				RNA_int_set(op->ptr, "gesture_mode", event->val);

			if(event->val != GESTURE_MODAL_NOP) {
				/* apply first click */
				gesture_circle_apply(C, op);
				gesture->mode= 1;
				wm_gesture_tag_redraw(C);
			}
			break;

		case GESTURE_MODAL_CANCEL:
		case GESTURE_MODAL_CONFIRM:
			wm_gesture_end(C, op);
			return OPERATOR_FINISHED; /* use finish or we dont get an undo */
		}
	}
//	// Allow view navigation???
//	else {
//		return OPERATOR_PASS_THROUGH;
//	}

	return OPERATOR_RUNNING_MODAL;
}

#if 0
/* template to copy from */
void WM_OT_circle_gesture(wmOperatorType *ot)
{
	ot->name= "Circle Gesture";
	ot->idname= "WM_OT_circle_gesture";
	ot->description="Enter rotate mode with a circular gesture";
	
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
		case INBETWEEN_MOUSEMOVE:
			
			wm_subwindow_getorigin(window, gesture->swinid, &sx, &sy);
			
			rect->xmax= event->x - sx;
			rect->ymax= event->y - sy;
			
			if((val= wm_gesture_evaluate(gesture))) {
				wmEvent tevent;

				tevent= *(window->eventstate);
				if(gesture->event_type==LEFTMOUSE)
					tevent.type= EVT_TWEAK_L;
				else if(gesture->event_type==RIGHTMOUSE)
					tevent.type= EVT_TWEAK_R;
				else
					tevent.type= EVT_TWEAK_M;
				tevent.val= val;
				/* mouse coords! */
				wm_event_add(window, &tevent);
				
				WM_gesture_end(C, gesture);	/* frees gesture itself, and unregisters from window */
			}
			
			break;
			
		case LEFTMOUSE:
		case RIGHTMOUSE:
		case MIDDLEMOUSE:
			if(gesture->event_type==event->type) {
				WM_gesture_end(C, gesture);

				/* when tweak fails we should give the other keymap entries a chance */
				event->val= KM_RELEASE;
			}
			break;
		default:
			if(!ISTIMER(event->type)) {
				WM_gesture_end(C, gesture);
			}
			break;
	}
}

/* standard tweak, called after window handlers passed on event */
void wm_tweakevent_test(bContext *C, wmEvent *event, int action)
{
	wmWindow *win= CTX_wm_window(C);
	
	if(win->tweak==NULL) {
		if(CTX_wm_region(C)) {
			if(event->val==KM_PRESS) { 
				if( ELEM3(event->type, LEFTMOUSE, MIDDLEMOUSE, RIGHTMOUSE) )
					win->tweak= WM_gesture_new(C, event, WM_GESTURE_TWEAK);
			}
		}
	}
	else {
		/* no tweaks if event was handled */
		if((action & WM_HANDLER_BREAK)) {
			WM_gesture_end(C, win->tweak);
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
	WM_event_add_modal_handler(C, op);
	
	wm_gesture_tag_redraw(C);
	
	if( RNA_struct_find_property(op->ptr, "cursor") )
		WM_cursor_modal(CTX_wm_window(C), RNA_int_get(op->ptr, "cursor"));
	
	return OPERATOR_RUNNING_MODAL;
}

int WM_gesture_lines_invoke(bContext *C, wmOperator *op, wmEvent *event)
{
	op->customdata= WM_gesture_new(C, event, WM_GESTURE_LINES);
	
	/* add modal handler */
	WM_event_add_modal_handler(C, op);
	
	wm_gesture_tag_redraw(C);
	
	if( RNA_struct_find_property(op->ptr, "cursor") )
		WM_cursor_modal(CTX_wm_window(C), RNA_int_get(op->ptr, "cursor"));
	
	return OPERATOR_RUNNING_MODAL;
}


static void gesture_lasso_apply(bContext *C, wmOperator *op)
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
		case INBETWEEN_MOUSEMOVE:
			
			wm_gesture_tag_redraw(C);
			
			wm_subwindow_getorigin(CTX_wm_window(C), gesture->swinid, &sx, &sy);

			if(gesture->points == gesture->size) {
				short *old_lasso = gesture->customdata;
				gesture->customdata= MEM_callocN(2*sizeof(short)*(gesture->size + WM_LASSO_MIN_POINTS), "lasso points");
				memcpy(gesture->customdata, old_lasso, 2*sizeof(short)*gesture->size);
				gesture->size = gesture->size + WM_LASSO_MIN_POINTS;
				MEM_freeN(old_lasso);
				printf("realloc\n");
			}

			{
				short x, y;
				short *lasso= gesture->customdata;
				
				lasso += (2 * gesture->points - 2);
				x = (event->x - sx - lasso[0]);
				y = (event->y - sy - lasso[1]);
				
				/* make a simple distance check to get a smoother lasso
				   add only when at least 2 pixels between this and previous location */
				if((x*x+y*y) > 4) {
					lasso += 2;
					lasso[0] = event->x - sx;
					lasso[1] = event->y - sy;
					gesture->points++;
				}
			}
			break;
			
		case LEFTMOUSE:
		case MIDDLEMOUSE:
		case RIGHTMOUSE:
			if(event->val==KM_RELEASE) {	/* key release */
				gesture_lasso_apply(C, op);
				return OPERATOR_FINISHED;
			}
			break;
		case ESCKEY:
			wm_gesture_end(C, op);
			return OPERATOR_CANCELLED;
	}
	return OPERATOR_RUNNING_MODAL;
}

int WM_gesture_lines_modal(bContext *C, wmOperator *op, wmEvent *event)
{
	return WM_gesture_lasso_modal(C, op, event);
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
	ot->description="Select objects within the lasso as you move the pointer";
	
	ot->invoke= WM_gesture_lasso_invoke;
	ot->modal= WM_gesture_lasso_modal;
	ot->exec= gesture_lasso_exec;
	
	ot->poll= WM_operator_winactive;
	
	prop= RNA_def_property(ot->srna, "path", PROP_COLLECTION, PROP_NONE);
	RNA_def_property_struct_runtime(prop, &RNA_OperatorMousePath);
}
#endif

/* *********************** straight line gesture ****************** */

static int straightline_apply(bContext *C, wmOperator *op)
{
	wmGesture *gesture= op->customdata;
	rcti *rect= gesture->customdata;
	
	if(rect->xmin==rect->xmax && rect->ymin==rect->ymax)
		return 0;
	
	/* operator arguments and storage. */
	RNA_int_set(op->ptr, "xstart", rect->xmin);
	RNA_int_set(op->ptr, "ystart", rect->ymin);
	RNA_int_set(op->ptr, "xend", rect->xmax);
	RNA_int_set(op->ptr, "yend", rect->ymax);

	if(op->type->exec)
		op->type->exec(C, op);
	
	return 1;
}


int WM_gesture_straightline_invoke(bContext *C, wmOperator *op, wmEvent *event)
{
	op->customdata= WM_gesture_new(C, event, WM_GESTURE_STRAIGHTLINE);
	
	/* add modal handler */
	WM_event_add_modal_handler(C, op);
	
	wm_gesture_tag_redraw(C);
	
	if( RNA_struct_find_property(op->ptr, "cursor") )
		WM_cursor_modal(CTX_wm_window(C), RNA_int_get(op->ptr, "cursor"));
		
	return OPERATOR_RUNNING_MODAL;
}

int WM_gesture_straightline_modal(bContext *C, wmOperator *op, wmEvent *event)
{
	wmGesture *gesture= op->customdata;
	rcti *rect= gesture->customdata;
	int sx, sy;
	
	if(event->type== MOUSEMOVE) {
		wm_subwindow_getorigin(CTX_wm_window(C), gesture->swinid, &sx, &sy);
		
		if(gesture->mode==0) {
			rect->xmin= rect->xmax= event->x - sx;
			rect->ymin= rect->ymax= event->y - sy;
		}
		else {
			rect->xmax= event->x - sx;
			rect->ymax= event->y - sy;
			straightline_apply(C, op);
		}
		
		wm_gesture_tag_redraw(C);
	}
	else if (event->type==EVT_MODAL_MAP) {
		switch (event->val) {
			case GESTURE_MODAL_BEGIN:
				if(gesture->mode==0) {
					gesture->mode= 1;
					wm_gesture_tag_redraw(C);
				}
				break;
			case GESTURE_MODAL_SELECT:
				if(straightline_apply(C, op)) {
					wm_gesture_end(C, op);
					return OPERATOR_FINISHED;
				}
				wm_gesture_end(C, op);
				return OPERATOR_CANCELLED;
				break;
				
			case GESTURE_MODAL_CANCEL:
				wm_gesture_end(C, op);
				return OPERATOR_CANCELLED;
		}
		
	}

	return OPERATOR_RUNNING_MODAL;
}

#if 0
/* template to copy from */
void WM_OT_straightline_gesture(wmOperatorType *ot)
{
	PropertyRNA *prop;
	
	ot->name= "Straight Line Gesture";
	ot->idname= "WM_OT_straightline_gesture";
	ot->description="Draw a straight line as you move the pointer";
	
	ot->invoke= WM_gesture_straightline_invoke;
	ot->modal= WM_gesture_straightline_modal;
	ot->exec= gesture_straightline_exec;
	
	ot->poll= WM_operator_winactive;
	
	WM_operator_properties_gesture_straightline(ot, 0);
}
#endif

/* *********************** radial control ****************** */

static const int WM_RADIAL_CONTROL_DISPLAY_SIZE = 200;

typedef struct wmRadialControl {
	int mode;
	float initial_value, value, max_value;
	float col[4], tex_col[4];
	int initial_mouse[2];
	void *cursor;
	GLuint tex;
} wmRadialControl;

static void wm_radial_control_paint(bContext *C, int x, int y, void *customdata)
{
	wmRadialControl *rc = (wmRadialControl*)customdata;
	ARegion *ar = CTX_wm_region(C);
	float r1=0.0f, r2=0.0f, r3=0.0f, angle=0.0f;

	// int hit = 0;
	
	if(rc->mode == WM_RADIALCONTROL_STRENGTH)
		rc->tex_col[3]= (rc->value + 0.5f);

	if(rc->mode == WM_RADIALCONTROL_SIZE) {
		r1= rc->value;
		r2= rc->initial_value;
		r3= r1;
	} else if(rc->mode == WM_RADIALCONTROL_STRENGTH) {
		r1= (1 - rc->value) * WM_RADIAL_CONTROL_DISPLAY_SIZE;
		r2= r3= (float)WM_RADIAL_CONTROL_DISPLAY_SIZE;
	} else if(rc->mode == WM_RADIALCONTROL_ANGLE) {
		r1= r2= r3= (float)WM_RADIAL_CONTROL_DISPLAY_SIZE;
		angle = rc->value;
	}

	/* Keep cursor in the original place */
	x = rc->initial_mouse[0] - ar->winrct.xmin;
	y = rc->initial_mouse[1] - ar->winrct.ymin;

	glTranslatef((float)x, (float)y, 0.0f);

	glEnable(GL_BLEND);

	if(rc->mode == WM_RADIALCONTROL_ANGLE) {
		glRotatef(angle, 0, 0, 1);
	}

	if (rc->tex) {
		glBindTexture(GL_TEXTURE_2D, rc->tex);

		glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR);
		glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);

		glEnable(GL_TEXTURE_2D);
		glBegin(GL_QUADS);
		glColor4f(rc->tex_col[0], rc->tex_col[1], rc->tex_col[2], rc->tex_col[3]);
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

	if(rc->mode == WM_RADIALCONTROL_ANGLE) {
		glColor4f(rc->col[0], rc->col[1], rc->col[2], rc->col[3]);
		glEnable(GL_LINE_SMOOTH);
		glRotatef(-angle, 0, 0, 1);
		fdrawline(0.0f, 0.0f, (float)WM_RADIAL_CONTROL_DISPLAY_SIZE, 0.0f);
		glRotatef(angle, 0, 0, 1);
		fdrawline(0.0f, 0.0f, (float)WM_RADIAL_CONTROL_DISPLAY_SIZE, 0.0f);
		glDisable(GL_LINE_SMOOTH);
	}

	glColor4f(rc->col[0], rc->col[1], rc->col[2], rc->col[3]);
	glutil_draw_lined_arc(0.0, (float)(M_PI*2.0), r1, 40);
	glutil_draw_lined_arc(0.0, (float)(M_PI*2.0), r2, 40);
	glDisable(GL_BLEND);
}

int WM_radial_control_modal(bContext *C, wmOperator *op, wmEvent *event)
{
	wmRadialControl *rc = (wmRadialControl*)op->customdata;
	int mode, initial_mouse[2], delta[2];
	float dist;
	double new_value = RNA_float_get(op->ptr, "new_value");
	int ret = OPERATOR_RUNNING_MODAL;
	// float initial_value = RNA_float_get(op->ptr, "initial_value");

	mode = RNA_enum_get(op->ptr, "mode");
	RNA_int_get_array(op->ptr, "initial_mouse", initial_mouse);

	switch(event->type) {
	case MOUSEMOVE:
		delta[0]= initial_mouse[0] - event->x;
		delta[1]= initial_mouse[1] - event->y;

		//if (mode == WM_RADIALCONTROL_SIZE) 
		//	delta[0]+= initial_value;
		//else if(mode == WM_RADIALCONTROL_STRENGTH)
		//	delta[0]+= WM_RADIAL_CONTROL_DISPLAY_SIZE * (1 - initial_value);
		//else if(mode == WM_RADIALCONTROL_ANGLE) {
		//	delta[0]+= WM_RADIAL_CONTROL_DISPLAY_SIZE * cos(initial_value*M_PI/180.0f);
		//	delta[1]+= WM_RADIAL_CONTROL_DISPLAY_SIZE * sin(initial_value*M_PI/180.0f);
		//}

		dist= sqrtf(delta[0]*delta[0]+delta[1]*delta[1]);

		if(mode == WM_RADIALCONTROL_SIZE)
			new_value = dist;
		else if(mode == WM_RADIALCONTROL_STRENGTH) {
			new_value = 1 - dist / WM_RADIAL_CONTROL_DISPLAY_SIZE;
		} else if(mode == WM_RADIALCONTROL_ANGLE)
			new_value = ((int)(atan2f(delta[1], delta[0]) * (float)(180.0 / M_PI)) + 180);
		
		if(event->ctrl) {
			if(mode == WM_RADIALCONTROL_STRENGTH)
				new_value = ((int)ceilf(new_value * 10.f) * 10.0f) / 100.f;
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
	rc->value = (float)new_value;

	RNA_float_set(op->ptr, "new_value", rc->value);

	if(ret != OPERATOR_RUNNING_MODAL) {
		WM_paint_cursor_end(CTX_wm_manager(C), rc->cursor);
		MEM_freeN(rc);
	}
	
	ED_region_tag_redraw(CTX_wm_region(C));

	//if (ret != OPERATOR_RUNNING_MODAL) {
	//	wmWindow *win = CTX_wm_window(C);
	//	WM_cursor_restore(win);
	//}

	return ret;
}

/* Expects the operator customdata to be an ImBuf (or NULL) */
int WM_radial_control_invoke(bContext *C, wmOperator *op, wmEvent *event)
{
	wmRadialControl *rc = MEM_callocN(sizeof(wmRadialControl), "radial control");
	// wmWindow *win = CTX_wm_window(C);
	int mode = RNA_enum_get(op->ptr, "mode");
	float initial_value = RNA_float_get(op->ptr, "initial_value");
	//float initial_size = RNA_float_get(op->ptr, "initial_size");
	int mouse[2];

	mouse[0]= event->x;
	mouse[1]= event->y;

	//if (initial_size == 0)
	//	initial_size = WM_RADIAL_CONTROL_DISPLAY_SIZE;

	if(mode == WM_RADIALCONTROL_SIZE) {
		rc->max_value = 200;
		mouse[0]-= (int)initial_value;
	}
	else if(mode == WM_RADIALCONTROL_STRENGTH) {
		rc->max_value = 1;
		mouse[0]-= (int)(WM_RADIAL_CONTROL_DISPLAY_SIZE * (1.0f - initial_value));
	}
	else if(mode == WM_RADIALCONTROL_ANGLE) {
		rc->max_value = 360;
		mouse[0]-= (int)(WM_RADIAL_CONTROL_DISPLAY_SIZE * cos(initial_value));
		mouse[1]-= (int)(WM_RADIAL_CONTROL_DISPLAY_SIZE * sin(initial_value));
		initial_value *= 180.0f/(float)M_PI;
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

	RNA_float_get_array(op->ptr, "color", rc->col);
	RNA_float_get_array(op->ptr, "texture_color", rc->tex_col);

	RNA_int_set_array(op->ptr, "initial_mouse", mouse);
	RNA_float_set(op->ptr, "new_value", initial_value);
		
	op->customdata = rc;
	rc->mode = mode;
	rc->initial_value = initial_value;
	rc->initial_mouse[0] = mouse[0];
	rc->initial_mouse[1] = mouse[1];
	rc->cursor = WM_paint_cursor_activate(CTX_wm_manager(C), op->type->poll,
						  wm_radial_control_paint, op->customdata);

	//WM_cursor_modal(win, CURSOR_NONE);

	/* add modal handler */
	WM_event_add_modal_handler(C, op);
	
	WM_radial_control_modal(C, op, event);
	
	return OPERATOR_RUNNING_MODAL;
}

/* Gets a descriptive string of the operation */
void WM_radial_control_string(wmOperator *op, char str[], int maxlen)
{
	int mode = RNA_enum_get(op->ptr, "mode");
	float v = RNA_float_get(op->ptr, "new_value");

	if(mode == WM_RADIALCONTROL_SIZE)
		BLI_snprintf(str, maxlen, "Size: %d", (int)v);
	else if(mode == WM_RADIALCONTROL_STRENGTH)
		BLI_snprintf(str, maxlen, "Strength: %d", (int)v);
	else if(mode == WM_RADIALCONTROL_ANGLE)
		BLI_snprintf(str, maxlen, "Angle: %d", (int)(v * 180.0f/(float)M_PI));
}

/** Important: this doesn't define an actual operator, it
	just sets up the common parts of the radial control op. **/
void WM_OT_radial_control_partial(wmOperatorType *ot)
{
	static EnumPropertyItem radial_mode_items[] = {
		{WM_RADIALCONTROL_SIZE, "SIZE", 0, "Size", ""},
		{WM_RADIALCONTROL_STRENGTH, "STRENGTH", 0, "Strength", ""},
		{WM_RADIALCONTROL_ANGLE, "ANGLE", 0, "Angle", ""},
		{0, NULL, 0, NULL, NULL}};
	static float color[4] = {1.0f, 1.0f, 1.0f, 0.5f};
	static float tex_color[4] = {1.0f, 1.0f, 1.0f, 1.0f};

	/* Should be set in custom invoke() */
	RNA_def_float(ot->srna, "initial_value", 0, 0, FLT_MAX, "Initial Value", "", 0, FLT_MAX);

	/* Set internally, should be used in custom exec() to get final value */
	RNA_def_float(ot->srna, "new_value", 0, 0, FLT_MAX, "New Value", "", 0, FLT_MAX);

	/* Should be set before calling operator */
	RNA_def_enum(ot->srna, "mode", radial_mode_items, 0, "Mode", "");

	/* Internal */
	RNA_def_int_vector(ot->srna, "initial_mouse", 2, NULL, INT_MIN, INT_MAX, "Initial Mouse", "", INT_MIN, INT_MAX);

	RNA_def_float_color(ot->srna, "color", 4, color, 0.0f, FLT_MAX, "Color", "Radial control color", 0.0f, 1.0f);
	RNA_def_float_color(ot->srna, "texture_color", 4, tex_color, 0.0f, FLT_MAX, "Texture Color", "Radial control texture color", 0.0f, 1.0f);
}

/* ************************** timer for testing ***************** */

/* uses no type defines, fully local testing function anyway... ;) */

static void redraw_timer_window_swap(bContext *C)
{
	wmWindow *win= CTX_wm_window(C);
	ScrArea *sa;

	for(sa= CTX_wm_screen(C)->areabase.first; sa; sa= sa->next)
		ED_area_tag_redraw(sa);
	wm_draw_update(C);

	CTX_wm_window_set(C, win);	/* XXX context manipulation warning! */
}

static EnumPropertyItem redraw_timer_type_items[] = {
	{0, "DRAW", 0, "Draw Region", "Draw Region"},
	{1, "DRAW_SWAP", 0, "Draw Region + Swap", "Draw Region and Swap"},
	{2, "DRAW_WIN", 0, "Draw Window", "Draw Window"},
	{3, "DRAW_WIN_SWAP", 0, "Draw Window + Swap", "Draw Window and Swap"},
	{4, "ANIM_STEP", 0, "Anim Step", "Animation Steps"},
	{5, "ANIM_PLAY", 0, "Anim Play", "Animation Playback"},
	{6, "UNDO", 0, "Undo/Redo", "Undo/Redo"},
	{0, NULL, 0, NULL, NULL}};

static int redraw_timer_exec(bContext *C, wmOperator *op)
{
	ARegion *ar= CTX_wm_region(C);
	double stime= PIL_check_seconds_timer();
	int type = RNA_enum_get(op->ptr, "type");
	int iter = RNA_int_get(op->ptr, "iterations");
	int a;
	float time;
	const char *infostr= "";
	
	WM_cursor_wait(1);

	for(a=0; a<iter; a++) {
		if (type==0) {
			if(ar)
				ED_region_do_draw(C, ar);
		} 
		else if (type==1) {
			wmWindow *win= CTX_wm_window(C);
			
			ED_region_tag_redraw(ar);
			wm_draw_update(C);
			
			CTX_wm_window_set(C, win);	/* XXX context manipulation warning! */
		}
		else if (type==2) {
			wmWindow *win= CTX_wm_window(C);
			ScrArea *sa;
			
			ScrArea *sa_back= CTX_wm_area(C);
			ARegion *ar_back= CTX_wm_region(C);

			for(sa= CTX_wm_screen(C)->areabase.first; sa; sa= sa->next) {
				ARegion *ar_iter;
				CTX_wm_area_set(C, sa);

				for(ar_iter= sa->regionbase.first; ar_iter; ar_iter= ar_iter->next) {
					if(ar_iter->swinid) {
						CTX_wm_region_set(C, ar_iter);
						ED_region_do_draw(C, ar_iter);
					}
				}
			}

			CTX_wm_window_set(C, win);	/* XXX context manipulation warning! */

			CTX_wm_area_set(C, sa_back);
			CTX_wm_region_set(C, ar_back);
		}
		else if (type==3) {
			redraw_timer_window_swap(C);
		}
		else if (type==4) {
			Main *bmain= CTX_data_main(C);
			Scene *scene= CTX_data_scene(C);
			
			if(a & 1) scene->r.cfra--;
			else scene->r.cfra++;
			scene_update_for_newframe(bmain, scene, scene->lay);
		}
		else if (type==5) {

			/* play anim, return on same frame as started with */
			Main *bmain= CTX_data_main(C);
			Scene *scene= CTX_data_scene(C);
			int tot= (scene->r.efra - scene->r.sfra) + 1;

			while(tot--) {
				/* todo, ability to escape! */
				scene->r.cfra++;
				if(scene->r.cfra > scene->r.efra)
					scene->r.cfra= scene->r.sfra;

				scene_update_for_newframe(bmain, scene, scene->lay);
				redraw_timer_window_swap(C);
			}
		}
		else { /* 6 */
			ED_undo_pop(C);
			ED_undo_redo(C);
		}
	}
	
	time= (float)((PIL_check_seconds_timer()-stime)*1000);

	RNA_enum_description(redraw_timer_type_items, type, &infostr);

	WM_cursor_wait(0);

	BKE_reportf(op->reports, RPT_WARNING, "%d x %s: %.2f ms,  average: %.4f", iter, infostr, time, time/iter);
	
	return OPERATOR_FINISHED;
}

static void WM_OT_redraw_timer(wmOperatorType *ot)
{
	ot->name= "Redraw Timer";
	ot->idname= "WM_OT_redraw_timer";
	ot->description="Simple redraw timer to test the speed of updating the interface";

	ot->invoke= WM_menu_invoke;
	ot->exec= redraw_timer_exec;
	ot->poll= WM_operator_winactive;

	ot->prop= RNA_def_enum(ot->srna, "type", redraw_timer_type_items, 0, "Type", "");
	RNA_def_int(ot->srna, "iterations", 10, 1,INT_MAX, "Iterations", "Number of times to redraw", 1,1000);

}

/* ************************** memory statistics for testing ***************** */

static int memory_statistics_exec(bContext *UNUSED(C), wmOperator *UNUSED(op))
{
	MEM_printmemlist_stats();
	return OPERATOR_FINISHED;
}

static void WM_OT_memory_statistics(wmOperatorType *ot)
{
	ot->name= "Memory Statistics";
	ot->idname= "WM_OT_memory_statistics";
	ot->description= "Print memory statistics to the console";
	
	ot->exec= memory_statistics_exec;
}

/* ******************************************************* */
 
/* called on initialize WM_exit() */
void wm_operatortype_free(void)
{
	wmOperatorType *ot;
	
	for(ot= global_ops.first; ot; ot= ot->next) {
		if(ot->macro.first)
			wm_operatortype_free_macro(ot);

		if(ot->ext.srna) /* python operator, allocs own string */
			MEM_freeN((void *)ot->idname);
	}
	
	BLI_freelistN(&global_ops);
}

/* called on initialize WM_init() */
void wm_operatortype_init(void)
{
	WM_operatortype_append(WM_OT_window_duplicate);
	WM_operatortype_append(WM_OT_read_homefile);
	WM_operatortype_append(WM_OT_read_factory_settings);
	WM_operatortype_append(WM_OT_save_homefile);
	WM_operatortype_append(WM_OT_window_fullscreen_toggle);
	WM_operatortype_append(WM_OT_quit_blender);
	WM_operatortype_append(WM_OT_open_mainfile);
	WM_operatortype_append(WM_OT_link_append);
	WM_operatortype_append(WM_OT_recover_last_session);
	WM_operatortype_append(WM_OT_recover_auto_save);
	WM_operatortype_append(WM_OT_save_as_mainfile);
	WM_operatortype_append(WM_OT_save_mainfile);
	WM_operatortype_append(WM_OT_redraw_timer);
	WM_operatortype_append(WM_OT_memory_statistics);
	WM_operatortype_append(WM_OT_debug_menu);
	WM_operatortype_append(WM_OT_splash);
	WM_operatortype_append(WM_OT_search_menu);
	WM_operatortype_append(WM_OT_call_menu);
#if defined(WIN32)
	WM_operatortype_append(WM_OT_console_toggle);
#endif

#ifdef WITH_COLLADA
	/* XXX: move these */
	WM_operatortype_append(WM_OT_collada_export);
	WM_operatortype_append(WM_OT_collada_import);
#endif

}

/* circleselect-like modal operators */
static void gesture_circle_modal_keymap(wmKeyConfig *keyconf)
{
	static EnumPropertyItem modal_items[] = {
	{GESTURE_MODAL_CANCEL,	"CANCEL", 0, "Cancel", ""},
	{GESTURE_MODAL_CONFIRM,	"CONFIRM", 0, "Confirm", ""},
	{GESTURE_MODAL_CIRCLE_ADD, "ADD", 0, "Add", ""},
	{GESTURE_MODAL_CIRCLE_SUB, "SUBTRACT", 0, "Subtract", ""},

	{GESTURE_MODAL_SELECT,	"SELECT", 0, "Select", ""},
	{GESTURE_MODAL_DESELECT,"DESELECT", 0, "DeSelect", ""},
	{GESTURE_MODAL_NOP,"NOP", 0, "No Operation", ""},


	{0, NULL, 0, NULL, NULL}};

	wmKeyMap *keymap= WM_modalkeymap_get(keyconf, "View3D Gesture Circle");

	/* this function is called for each spacetype, only needs to add map once */
	if(keymap) return;

	keymap= WM_modalkeymap_add(keyconf, "View3D Gesture Circle", modal_items);

	/* items for modal map */
	WM_modalkeymap_add_item(keymap, ESCKEY,    KM_PRESS, KM_ANY, 0, GESTURE_MODAL_CANCEL);
	WM_modalkeymap_add_item(keymap, RIGHTMOUSE, KM_ANY, KM_ANY, 0, GESTURE_MODAL_CANCEL);

	WM_modalkeymap_add_item(keymap, RETKEY, KM_PRESS, KM_ANY, 0, GESTURE_MODAL_CONFIRM);
	WM_modalkeymap_add_item(keymap, PADENTER, KM_PRESS, 0, 0, GESTURE_MODAL_CONFIRM);

	WM_modalkeymap_add_item(keymap, LEFTMOUSE, KM_PRESS, 0, 0, GESTURE_MODAL_SELECT);

#if 0 // Durien guys like this :S
	WM_modalkeymap_add_item(keymap, LEFTMOUSE, KM_PRESS, KM_SHIFT, 0, GESTURE_MODAL_DESELECT);
	WM_modalkeymap_add_item(keymap, LEFTMOUSE, KM_RELEASE, KM_SHIFT, 0, GESTURE_MODAL_NOP);
#else
	WM_modalkeymap_add_item(keymap, MIDDLEMOUSE, KM_PRESS, 0, 0, GESTURE_MODAL_DESELECT); //  defailt 2.4x
	WM_modalkeymap_add_item(keymap, MIDDLEMOUSE, KM_RELEASE, 0, 0, GESTURE_MODAL_NOP); //  defailt 2.4x
#endif

	WM_modalkeymap_add_item(keymap, LEFTMOUSE, KM_RELEASE, 0, 0, GESTURE_MODAL_NOP);

	WM_modalkeymap_add_item(keymap, WHEELUPMOUSE, KM_PRESS, 0, 0, GESTURE_MODAL_CIRCLE_SUB);
	WM_modalkeymap_add_item(keymap, PADMINUS, KM_PRESS, 0, 0, GESTURE_MODAL_CIRCLE_SUB);
	WM_modalkeymap_add_item(keymap, WHEELDOWNMOUSE, KM_PRESS, 0, 0, GESTURE_MODAL_CIRCLE_ADD);
	WM_modalkeymap_add_item(keymap, PADPLUSKEY, KM_PRESS, 0, 0, GESTURE_MODAL_CIRCLE_ADD);

	/* assign map to operators */
	WM_modalkeymap_assign(keymap, "VIEW3D_OT_select_circle");
	WM_modalkeymap_assign(keymap, "UV_OT_circle_select");

}

/* straight line modal operators */
static void gesture_straightline_modal_keymap(wmKeyConfig *keyconf)
{
	static EnumPropertyItem modal_items[] = {
		{GESTURE_MODAL_CANCEL,	"CANCEL", 0, "Cancel", ""},
		{GESTURE_MODAL_SELECT,	"SELECT", 0, "Select", ""},
		{GESTURE_MODAL_BEGIN,	"BEGIN", 0, "Begin", ""},
		{0, NULL, 0, NULL, NULL}};
	
	wmKeyMap *keymap= WM_modalkeymap_get(keyconf, "Gesture Straight Line");
	
	/* this function is called for each spacetype, only needs to add map once */
	if(keymap) return;
	
	keymap= WM_modalkeymap_add(keyconf, "Gesture Straight Line", modal_items);
	
	/* items for modal map */
	WM_modalkeymap_add_item(keymap, ESCKEY,    KM_PRESS, KM_ANY, 0, GESTURE_MODAL_CANCEL);
	WM_modalkeymap_add_item(keymap, RIGHTMOUSE, KM_ANY, KM_ANY, 0, GESTURE_MODAL_CANCEL);
	
	WM_modalkeymap_add_item(keymap, LEFTMOUSE, KM_PRESS, 0, 0, GESTURE_MODAL_BEGIN);
	WM_modalkeymap_add_item(keymap, LEFTMOUSE, KM_RELEASE, 0, 0, GESTURE_MODAL_SELECT);
	
	/* assign map to operators */
	WM_modalkeymap_assign(keymap, "IMAGE_OT_sample_line");
}


/* borderselect-like modal operators */
static void gesture_border_modal_keymap(wmKeyConfig *keyconf)
{
	static EnumPropertyItem modal_items[] = {
	{GESTURE_MODAL_CANCEL,	"CANCEL", 0, "Cancel", ""},
	{GESTURE_MODAL_SELECT,	"SELECT", 0, "Select", ""},
	{GESTURE_MODAL_DESELECT,"DESELECT", 0, "DeSelect", ""},
	{GESTURE_MODAL_BEGIN,	"BEGIN", 0, "Begin", ""},
	{0, NULL, 0, NULL, NULL}};

	wmKeyMap *keymap= WM_modalkeymap_get(keyconf, "Gesture Border");

	/* this function is called for each spacetype, only needs to add map once */
	if(keymap) return;

	keymap= WM_modalkeymap_add(keyconf, "Gesture Border", modal_items);

	/* items for modal map */
	WM_modalkeymap_add_item(keymap, ESCKEY,    KM_PRESS, KM_ANY, 0, GESTURE_MODAL_CANCEL);
	WM_modalkeymap_add_item(keymap, RIGHTMOUSE, KM_ANY, KM_ANY, 0, GESTURE_MODAL_CANCEL);

	WM_modalkeymap_add_item(keymap, LEFTMOUSE, KM_PRESS, 0, 0, GESTURE_MODAL_BEGIN);
	WM_modalkeymap_add_item(keymap, LEFTMOUSE, KM_RELEASE, KM_ANY, 0, GESTURE_MODAL_SELECT);

#if 0 // Durian guys like this
	WM_modalkeymap_add_item(keymap, LEFTMOUSE, KM_PRESS, KM_SHIFT, 0, GESTURE_MODAL_BEGIN);
	WM_modalkeymap_add_item(keymap, LEFTMOUSE, KM_RELEASE, KM_SHIFT, 0, GESTURE_MODAL_DESELECT);
#else
	WM_modalkeymap_add_item(keymap, MIDDLEMOUSE, KM_PRESS, 0, 0, GESTURE_MODAL_BEGIN);
	WM_modalkeymap_add_item(keymap, MIDDLEMOUSE, KM_RELEASE, 0, 0, GESTURE_MODAL_DESELECT);
#endif

	/* assign map to operators */
	WM_modalkeymap_assign(keymap, "ACTION_OT_select_border");
	WM_modalkeymap_assign(keymap, "ANIM_OT_channels_select_border");
	WM_modalkeymap_assign(keymap, "ANIM_OT_previewrange_set");
	WM_modalkeymap_assign(keymap, "INFO_OT_select_border");
	WM_modalkeymap_assign(keymap, "FILE_OT_select_border");
	WM_modalkeymap_assign(keymap, "GRAPH_OT_select_border");
	WM_modalkeymap_assign(keymap, "MARKER_OT_select_border");
	WM_modalkeymap_assign(keymap, "NLA_OT_select_border");
	WM_modalkeymap_assign(keymap, "NODE_OT_select_border");
//	WM_modalkeymap_assign(keymap, "SCREEN_OT_border_select"); // template
	WM_modalkeymap_assign(keymap, "SEQUENCER_OT_select_border");
	WM_modalkeymap_assign(keymap, "SEQUENCER_OT_view_ghost_border");
	WM_modalkeymap_assign(keymap, "UV_OT_select_border");
	WM_modalkeymap_assign(keymap, "VIEW2D_OT_zoom_border");
	WM_modalkeymap_assign(keymap, "VIEW3D_OT_clip_border");
	WM_modalkeymap_assign(keymap, "VIEW3D_OT_render_border");
	WM_modalkeymap_assign(keymap, "VIEW3D_OT_select_border");
	WM_modalkeymap_assign(keymap, "VIEW3D_OT_zoom_border"); // XXX TODO: zoom border should perhaps map rightmouse to zoom out instead of in+cancel
}

/* zoom to border modal operators */
static void gesture_zoom_border_modal_keymap(wmKeyConfig *keyconf)
{
	static EnumPropertyItem modal_items[] = {
	{GESTURE_MODAL_CANCEL, "CANCEL", 0, "Cancel", ""},
	{GESTURE_MODAL_IN,	"IN", 0, "In", ""},
	{GESTURE_MODAL_OUT, "OUT", 0, "Out", ""},
	{GESTURE_MODAL_BEGIN, "BEGIN", 0, "Begin", ""},
	{0, NULL, 0, NULL, NULL}};

	wmKeyMap *keymap= WM_modalkeymap_get(keyconf, "Gesture Zoom Border");

	/* this function is called for each spacetype, only needs to add map once */
	if(keymap) return;

	keymap= WM_modalkeymap_add(keyconf, "Gesture Zoom Border", modal_items);

	/* items for modal map */
	WM_modalkeymap_add_item(keymap, ESCKEY,    KM_PRESS, KM_ANY, 0, GESTURE_MODAL_CANCEL);
	WM_modalkeymap_add_item(keymap, RIGHTMOUSE, KM_ANY, KM_ANY, 0, GESTURE_MODAL_CANCEL);

	WM_modalkeymap_add_item(keymap, LEFTMOUSE, KM_PRESS, 0, 0, GESTURE_MODAL_BEGIN);
	WM_modalkeymap_add_item(keymap, LEFTMOUSE, KM_RELEASE, 0, 0, GESTURE_MODAL_IN); 

	WM_modalkeymap_add_item(keymap, MIDDLEMOUSE, KM_PRESS, 0, 0, GESTURE_MODAL_BEGIN);
	WM_modalkeymap_add_item(keymap, MIDDLEMOUSE, KM_RELEASE, 0, 0, GESTURE_MODAL_OUT);

	/* assign map to operators */
	WM_modalkeymap_assign(keymap, "VIEW2D_OT_zoom_border");
	WM_modalkeymap_assign(keymap, "VIEW3D_OT_zoom_border");
}

/* default keymap for windows and screens, only call once per WM */
void wm_window_keymap(wmKeyConfig *keyconf)
{
	wmKeyMap *keymap= WM_keymap_find(keyconf, "Window", 0, 0);
	wmKeyMapItem *kmi;
	
	/* note, this doesn't replace existing keymap items */
	WM_keymap_verify_item(keymap, "WM_OT_window_duplicate", WKEY, KM_PRESS, KM_CTRL|KM_ALT, 0);
	#ifdef __APPLE__
	WM_keymap_add_item(keymap, "WM_OT_read_homefile", NKEY, KM_PRESS, KM_OSKEY, 0);
	WM_keymap_add_menu(keymap, "INFO_MT_file_open_recent", OKEY, KM_PRESS, KM_SHIFT|KM_OSKEY, 0);
	WM_keymap_add_item(keymap, "WM_OT_open_mainfile", OKEY, KM_PRESS, KM_OSKEY, 0);
	WM_keymap_add_item(keymap, "WM_OT_save_mainfile", SKEY, KM_PRESS, KM_OSKEY, 0);
	WM_keymap_add_item(keymap, "WM_OT_save_as_mainfile", SKEY, KM_PRESS, KM_SHIFT|KM_OSKEY, 0);
	WM_keymap_add_item(keymap, "WM_OT_quit_blender", QKEY, KM_PRESS, KM_OSKEY, 0);
	#endif
	WM_keymap_add_item(keymap, "WM_OT_read_homefile", NKEY, KM_PRESS, KM_CTRL, 0);
	WM_keymap_add_item(keymap, "WM_OT_save_homefile", UKEY, KM_PRESS, KM_CTRL, 0); 
	WM_keymap_add_menu(keymap, "INFO_MT_file_open_recent", OKEY, KM_PRESS, KM_SHIFT|KM_CTRL, 0);
	WM_keymap_add_item(keymap, "WM_OT_open_mainfile", OKEY, KM_PRESS, KM_CTRL, 0);
	WM_keymap_add_item(keymap, "WM_OT_open_mainfile", F1KEY, KM_PRESS, 0, 0);
	WM_keymap_add_item(keymap, "WM_OT_link_append", OKEY, KM_PRESS, KM_CTRL|KM_ALT, 0);
	kmi= WM_keymap_add_item(keymap, "WM_OT_link_append", F1KEY, KM_PRESS, KM_SHIFT, 0);
	RNA_boolean_set(kmi->ptr, "link", FALSE);
	RNA_boolean_set(kmi->ptr, "instance_groups", FALSE);

	WM_keymap_add_item(keymap, "WM_OT_save_mainfile", SKEY, KM_PRESS, KM_CTRL, 0);
	WM_keymap_add_item(keymap, "WM_OT_save_mainfile", WKEY, KM_PRESS, KM_CTRL, 0);
	WM_keymap_add_item(keymap, "WM_OT_save_as_mainfile", SKEY, KM_PRESS, KM_SHIFT|KM_CTRL, 0);
	WM_keymap_add_item(keymap, "WM_OT_save_as_mainfile", F2KEY, KM_PRESS, 0, 0);
	kmi= WM_keymap_add_item(keymap, "WM_OT_save_as_mainfile", SKEY, KM_PRESS, KM_ALT|KM_CTRL, 0);
	RNA_boolean_set(kmi->ptr, "copy", 1);

	WM_keymap_verify_item(keymap, "WM_OT_window_fullscreen_toggle", F11KEY, KM_PRESS, KM_ALT, 0);
	WM_keymap_add_item(keymap, "WM_OT_quit_blender", QKEY, KM_PRESS, KM_CTRL, 0);

	/* debug/testing */
	WM_keymap_verify_item(keymap, "WM_OT_redraw_timer", TKEY, KM_PRESS, KM_ALT|KM_CTRL, 0);
	WM_keymap_verify_item(keymap, "WM_OT_debug_menu", DKEY, KM_PRESS, KM_ALT|KM_CTRL, 0);
	WM_keymap_verify_item(keymap, "WM_OT_search_menu", SPACEKEY, KM_PRESS, 0, 0);
	
	/* Space switching */


	kmi = WM_keymap_add_item(keymap, "WM_OT_context_set_enum", F2KEY, KM_PRESS, KM_SHIFT, 0); /* new in 2.5x, was DXF export */
	RNA_string_set(kmi->ptr, "data_path", "area.type");
	RNA_string_set(kmi->ptr, "value", "LOGIC_EDITOR");

	kmi = WM_keymap_add_item(keymap, "WM_OT_context_set_enum", F3KEY, KM_PRESS, KM_SHIFT, 0);
	RNA_string_set(kmi->ptr, "data_path", "area.type");
	RNA_string_set(kmi->ptr, "value", "NODE_EDITOR");

	kmi = WM_keymap_add_item(keymap, "WM_OT_context_set_enum", F4KEY, KM_PRESS, KM_SHIFT, 0); /* new in 2.5x, was data browser */
	RNA_string_set(kmi->ptr, "data_path", "area.type");
	RNA_string_set(kmi->ptr, "value", "CONSOLE");

	kmi = WM_keymap_add_item(keymap, "WM_OT_context_set_enum", F5KEY, KM_PRESS, KM_SHIFT, 0);
	RNA_string_set(kmi->ptr, "data_path", "area.type");
	RNA_string_set(kmi->ptr, "value", "VIEW_3D");

	kmi = WM_keymap_add_item(keymap, "WM_OT_context_set_enum", F6KEY, KM_PRESS, KM_SHIFT, 0);
	RNA_string_set(kmi->ptr, "data_path", "area.type");
	RNA_string_set(kmi->ptr, "value", "GRAPH_EDITOR");

	kmi = WM_keymap_add_item(keymap, "WM_OT_context_set_enum", F7KEY, KM_PRESS, KM_SHIFT, 0);
	RNA_string_set(kmi->ptr, "data_path", "area.type");
	RNA_string_set(kmi->ptr, "value", "PROPERTIES");

	kmi = WM_keymap_add_item(keymap, "WM_OT_context_set_enum", F8KEY, KM_PRESS, KM_SHIFT, 0);
	RNA_string_set(kmi->ptr, "data_path", "area.type");
	RNA_string_set(kmi->ptr, "value", "SEQUENCE_EDITOR");

	kmi = WM_keymap_add_item(keymap, "WM_OT_context_set_enum", F9KEY, KM_PRESS, KM_SHIFT, 0);
	RNA_string_set(kmi->ptr, "data_path", "area.type");
	RNA_string_set(kmi->ptr, "value", "OUTLINER");

	kmi = WM_keymap_add_item(keymap, "WM_OT_context_set_enum", F10KEY, KM_PRESS, KM_SHIFT, 0);
	RNA_string_set(kmi->ptr, "data_path", "area.type");
	RNA_string_set(kmi->ptr, "value", "IMAGE_EDITOR");

	kmi = WM_keymap_add_item(keymap, "WM_OT_context_set_enum", F11KEY, KM_PRESS, KM_SHIFT, 0);
	RNA_string_set(kmi->ptr, "data_path", "area.type");
	RNA_string_set(kmi->ptr, "value", "TEXT_EDITOR");

	kmi = WM_keymap_add_item(keymap, "WM_OT_context_set_enum", F12KEY, KM_PRESS, KM_SHIFT, 0);
	RNA_string_set(kmi->ptr, "data_path", "area.type");
	RNA_string_set(kmi->ptr, "value", "DOPESHEET_EDITOR");

	gesture_circle_modal_keymap(keyconf);
	gesture_border_modal_keymap(keyconf);
	gesture_zoom_border_modal_keymap(keyconf);
	gesture_straightline_modal_keymap(keyconf);
}

/* Generic itemf's for operators that take library args */
static EnumPropertyItem *rna_id_itemf(bContext *UNUSED(C), PointerRNA *UNUSED(ptr), int *do_free, ID *id, int local)
{
	EnumPropertyItem item_tmp= {0}, *item= NULL;
	int totitem= 0;
	int i= 0;

	for( ; id; id= id->next) {
		if(local==FALSE || id->lib==NULL) {
			item_tmp.identifier= item_tmp.name= id->name+2;
			item_tmp.value= i++;
			RNA_enum_item_add(&item, &totitem, &item_tmp);
		}
	}

	RNA_enum_item_end(&item, &totitem);
	*do_free= 1;

	return item;
}

/* can add more as needed */
EnumPropertyItem *RNA_action_itemf(bContext *C, PointerRNA *ptr, int *do_free)
{
	return rna_id_itemf(C, ptr, do_free, C ? (ID *)CTX_data_main(C)->action.first : NULL, FALSE);
}
EnumPropertyItem *RNA_action_local_itemf(bContext *C, PointerRNA *ptr, int *do_free)
{
	return rna_id_itemf(C, ptr, do_free, C ? (ID *)CTX_data_main(C)->action.first : NULL, TRUE);
}

EnumPropertyItem *RNA_group_itemf(bContext *C, PointerRNA *ptr, int *do_free)
{
	return rna_id_itemf(C, ptr, do_free, C ? (ID *)CTX_data_main(C)->group.first : NULL, FALSE);
}
EnumPropertyItem *RNA_group_local_itemf(bContext *C, PointerRNA *ptr, int *do_free)
{
	return rna_id_itemf(C, ptr, do_free, C ? (ID *)CTX_data_main(C)->group.first : NULL, TRUE);
}

EnumPropertyItem *RNA_image_itemf(bContext *C, PointerRNA *ptr, int *do_free)
{
	return rna_id_itemf(C, ptr, do_free, C ? (ID *)CTX_data_main(C)->image.first : NULL, FALSE);
}
EnumPropertyItem *RNA_image_local_itemf(bContext *C, PointerRNA *ptr, int *do_free)
{
	return rna_id_itemf(C, ptr, do_free, C ? (ID *)CTX_data_main(C)->image.first : NULL, TRUE);
}

EnumPropertyItem *RNA_scene_itemf(bContext *C, PointerRNA *ptr, int *do_free)
{
	return rna_id_itemf(C, ptr, do_free, C ? (ID *)CTX_data_main(C)->scene.first : NULL, FALSE);
}
EnumPropertyItem *RNA_scene_local_itemf(bContext *C, PointerRNA *ptr, int *do_free)
{
	return rna_id_itemf(C, ptr, do_free, C ? (ID *)CTX_data_main(C)->scene.first : NULL, TRUE);
}

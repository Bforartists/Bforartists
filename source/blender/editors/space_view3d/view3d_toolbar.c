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
 * Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
 *
 * The Original Code is Copyright (C) 2009 Blender Foundation.
 * All rights reserved.
 *
 * 
 * Contributor(s): Blender Foundation
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#include <string.h>
#include <stdio.h>
#include <math.h>
#include <float.h>

#include "DNA_object_types.h"
#include "DNA_scene_types.h"

#include "MEM_guardedalloc.h"

#include "BLI_math.h"
#include "BLI_blenlib.h"
#include "BLI_editVert.h"
#include "BLI_rand.h"

#include "BKE_context.h"
#include "BKE_idprop.h"
#include "BKE_global.h"
#include "BKE_screen.h"


#include "WM_api.h"
#include "WM_types.h"

#include "RNA_access.h"

#include "ED_screen.h"
#include "ED_util.h"

#include "UI_interface.h"
#include "UI_resources.h"

#include "view3d_intern.h"	// own include


/* ******************* view3d space & buttons ************** */


/* op->invoke */
static void redo_cb(bContext *C, void *arg_op, void *UNUSED(arg2))
{
	wmOperator *lastop= arg_op;
	
	if(lastop) {
		int retval;
		
		if (G.f & G_DEBUG)
			printf("operator redo %s\n", lastop->type->name);
		ED_undo_pop_op(C, lastop);
		retval= WM_operator_repeat(C, lastop);
		if((retval & OPERATOR_FINISHED)==0) {
			if (G.f & G_DEBUG)
				printf("operator redo failed %s\n", lastop->type->name);
			ED_undo_redo(C);
		}
	}
}

static wmOperator *view3d_last_operator(const bContext *C)
{
	wmWindowManager *wm= CTX_wm_manager(C);
	wmOperator *op;

	/* only for operators that are registered and did an undo push */
	for(op= wm->operators.last; op; op= op->prev)
		if((op->type->flag & OPTYPE_REGISTER) && (op->type->flag & OPTYPE_UNDO))
			break;

	return op;
}

static void view3d_panel_operator_redo_buts(const bContext *C, Panel *pa, wmOperator *op)
{
	wmWindowManager *wm= CTX_wm_manager(C);
	PointerRNA ptr;
	
	if(!op->properties) {
		IDPropertyTemplate val = {0};
		op->properties= IDP_New(IDP_GROUP, val, "wmOperatorProperties");
	}
	
	RNA_pointer_create(&wm->id, op->type->srna, op->properties, &ptr);
	if(op->type->ui) {
		op->layout= pa->layout;
		op->type->ui((bContext*)C, op);
		op->layout= NULL;
	}
	else
		uiDefAutoButsRNA(pa->layout, &ptr, 1);
}

static void view3d_panel_operator_redo_header(const bContext *C, Panel *pa)
{
	wmOperator *op= view3d_last_operator(C);

	if(op) BLI_strncpy(pa->drawname, op->type->name, sizeof(pa->drawname));
	else BLI_strncpy(pa->drawname, "Operator", sizeof(pa->drawname));
}

static void view3d_panel_operator_redo_operator(const bContext *C, Panel *pa, wmOperator *op)
{
	if(op->type->flag & OPTYPE_MACRO) {
		for(op= op->macro.first; op; op= op->next) {
			uiItemL(pa->layout, op->type->name, 0);
			view3d_panel_operator_redo_operator(C, pa, op);
		}
	}
	else {
		view3d_panel_operator_redo_buts(C, pa, op);
	}
}

static void view3d_panel_operator_redo(const bContext *C, Panel *pa)
{
	wmOperator *op= view3d_last_operator(C);
	uiBlock *block;
	
	if(op==NULL)
		return;
	if(WM_operator_poll((bContext*)C, op->type) == 0)
		return;
	
	block= uiLayoutGetBlock(pa->layout);

	uiBlockSetFunc(block, redo_cb, op, NULL);
	
	view3d_panel_operator_redo_operator(C, pa, op);
}

/* ******************* */

typedef struct CustomTool {
	struct CustomTool *next, *prev;
	char opname[OP_MAX_TYPENAME];
	char context[OP_MAX_TYPENAME];
} CustomTool;

static void operator_call_cb(struct bContext *C, void *arg_listbase, void *arg2)
{
	wmOperatorType *ot= arg2;
	
	if(ot) {
		CustomTool *ct= MEM_callocN(sizeof(CustomTool), "CustomTool");
		
		BLI_addtail(arg_listbase, ct);
		BLI_strncpy(ct->opname, ot->idname, OP_MAX_TYPENAME);
		BLI_strncpy(ct->context, CTX_data_mode_string(C), OP_MAX_TYPENAME);
	}
		
}

static void operator_search_cb(const struct bContext *C, void *UNUSED(arg), char *str, uiSearchItems *items)
{
	wmOperatorType *ot = WM_operatortype_first();
	
	for(; ot; ot= ot->next) {
		
		if(BLI_strcasestr(ot->name, str)) {
			if(WM_operator_poll((bContext*)C, ot)) {
				
				if(0==uiSearchItemAdd(items, ot->name, ot, 0))
					break;
			}
		}
	}
}


/* ID Search browse menu, open */
static uiBlock *tool_search_menu(bContext *C, ARegion *ar, void *arg_listbase)
{
	static char search[OP_MAX_TYPENAME];
	wmEvent event;
	wmWindow *win= CTX_wm_window(C);
	uiBlock *block;
	uiBut *but;
	
	/* clear initial search string, then all items show */
	search[0]= 0;
	
	block= uiBeginBlock(C, ar, "_popup", UI_EMBOSS);
	uiBlockSetFlag(block, UI_BLOCK_LOOP|UI_BLOCK_REDRAW|UI_BLOCK_RET_1);
	
	/* fake button, it holds space for search items */
	uiDefBut(block, LABEL, 0, "", 10, 15, 150, uiSearchBoxhHeight(), NULL, 0, 0, 0, 0, NULL);
	
	but= uiDefSearchBut(block, search, 0, ICON_VIEWZOOM, OP_MAX_TYPENAME, 10, 0, 150, 19, 0, 0, "");
	uiButSetSearchFunc(but, operator_search_cb, arg_listbase, operator_call_cb, NULL);
	
	uiBoundsBlock(block, 6);
	uiBlockSetDirection(block, UI_DOWN);	
	uiEndBlock(C, block);
	
	event= *(win->eventstate);	/* XXX huh huh? make api call */
	event.type= EVT_BUT_OPEN;
	event.val= KM_PRESS;
	event.customdata= but;
	event.customdatafree= FALSE;
	wm_event_add(win, &event);
	
	return block;
}


static void view3d_panel_tool_shelf(const bContext *C, Panel *pa)
{
	SpaceLink *sl= CTX_wm_space_data(C);
	SpaceType *st= NULL;
	uiLayout *col;
	const char *context= CTX_data_mode_string(C);
	
	if(sl)
		st= BKE_spacetype_from_id(sl->spacetype);
	
	if(st && st->toolshelf.first) {
		CustomTool *ct;
		
		for(ct= st->toolshelf.first; ct; ct= ct->next) {
			if(0==strncmp(context, ct->context, OP_MAX_TYPENAME)) {
				col= uiLayoutColumn(pa->layout, 1);
				uiItemFullO(col, ct->opname, NULL, 0, NULL, WM_OP_INVOKE_REGION_WIN, 0);
			}
		}
	}
	col= uiLayoutColumn(pa->layout, 1);
	uiDefBlockBut(uiLayoutGetBlock(pa->layout), tool_search_menu, &st->toolshelf, "Add Tool", 0, 0, UI_UNIT_X, UI_UNIT_Y, "Add Tool in shelf, gets saved in files");
}


void view3d_toolshelf_register(ARegionType *art)
{
	PanelType *pt;

	pt= MEM_callocN(sizeof(PanelType), "spacetype view3d panel tools");
	strcpy(pt->idname, "VIEW3D_PT_tool_shelf");
	strcpy(pt->label, "Tool Shelf");
	pt->draw= view3d_panel_tool_shelf;
	BLI_addtail(&art->paneltypes, pt);
}

void view3d_tool_props_register(ARegionType *art)
{
	PanelType *pt;
	
	pt= MEM_callocN(sizeof(PanelType), "spacetype view3d panel last operator");
	strcpy(pt->idname, "VIEW3D_PT_last_operator");
	strcpy(pt->label, "Operator");
	pt->draw_header= view3d_panel_operator_redo_header;
	pt->draw= view3d_panel_operator_redo;
	BLI_addtail(&art->paneltypes, pt);
}

/* ********** operator to open/close toolshelf region */

static int view3d_toolshelf(bContext *C, wmOperator *UNUSED(op))
{
	ScrArea *sa= CTX_wm_area(C);
	ARegion *ar= view3d_has_tools_region(sa);
	
	if(ar)
		ED_region_toggle_hidden(C, ar);

	return OPERATOR_FINISHED;
}

void VIEW3D_OT_toolshelf(wmOperatorType *ot)
{
	ot->name= "Tool Shelf";
	ot->description= "Toggles tool shelf display";
	ot->idname= "VIEW3D_OT_toolshelf";
	
	ot->exec= view3d_toolshelf;
	ot->poll= ED_operator_view3d_active;
	
	/* flags */
	ot->flag= 0;
}

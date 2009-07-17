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
 * Contributor(s): Blender Foundation (2009)
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#include <stdlib.h>

#include "DNA_screen_types.h"

#include "RNA_define.h"
#include "RNA_types.h"

#include "rna_internal.h"
#include "RNA_enum_types.h"

#include "UI_interface.h"

#include "WM_types.h"

#ifdef RNA_RUNTIME

#include "MEM_guardedalloc.h"

#include "RNA_access.h"

#include "BLI_dynstr.h"

#include "BKE_context.h"
#include "BKE_report.h"
#include "BKE_screen.h"

#include "WM_api.h"

static ARegionType *region_type_find(ReportList *reports, int space_type, int region_type)
{
	SpaceType *st;
	ARegionType *art;

	st= BKE_spacetype_from_id(space_type);

	for(art= (st)? st->regiontypes.first: NULL; art; art= art->next) {
		if (art->regionid==region_type)
			break;
	}
	
	/* region type not found? abort */
	if (art==NULL) {
		BKE_report(reports, RPT_ERROR, "Region not found in spacetype.");
		return NULL;
	}

	return art;
}

/* Panel */

static int panel_poll(const bContext *C, PanelType *pt)
{
	PointerRNA ptr;
	ParameterList list;
	FunctionRNA *func;
	void *ret;
	int visible;

	RNA_pointer_create(NULL, pt->py_srna, NULL, &ptr); /* dummy */
	func= RNA_struct_find_function(&ptr, "poll");

	RNA_parameter_list_create(&list, &ptr, func);
	RNA_parameter_set_lookup(&list, "context", &C);
	pt->py_call(&ptr, func, &list);

	RNA_parameter_get_lookup(&list, "visible", &ret);
	visible= *(int*)ret;

	RNA_parameter_list_free(&list);

	return visible;
}

static void panel_draw(const bContext *C, Panel *pnl)
{
	PointerRNA ptr;
	ParameterList list;
	FunctionRNA *func;

	RNA_pointer_create(&CTX_wm_screen(C)->id, pnl->type->py_srna, pnl, &ptr);
	func= RNA_struct_find_function(&ptr, "draw");

	RNA_parameter_list_create(&list, &ptr, func);
	RNA_parameter_set_lookup(&list, "context", &C);
	pnl->type->py_call(&ptr, func, &list);

	RNA_parameter_list_free(&list);
}

static void panel_draw_header(const bContext *C, Panel *pnl)
{
	PointerRNA ptr;
	ParameterList list;
	FunctionRNA *func;

	RNA_pointer_create(&CTX_wm_screen(C)->id, pnl->type->py_srna, pnl, &ptr);
	func= RNA_struct_find_function(&ptr, "draw_header");

	RNA_parameter_list_create(&list, &ptr, func);
	RNA_parameter_set_lookup(&list, "context", &C);
	pnl->type->py_call(&ptr, func, &list);

	RNA_parameter_list_free(&list);
}

static void rna_Panel_unregister(const bContext *C, StructRNA *type)
{
	ARegionType *art;
	PanelType *pt= RNA_struct_blender_type_get(type);

	if(!pt)
		return;
	if(!(art=region_type_find(NULL, pt->space_type, pt->region_type)))
		return;
	
	BLI_freelinkN(&art->paneltypes, pt);
	RNA_struct_free(&BLENDER_RNA, type);

	/* update while blender is running */
	if(C)
		WM_event_add_notifier(C, NC_SCREEN|NA_EDITED, NULL);
}

static StructRNA *rna_Panel_register(const bContext *C, ReportList *reports, void *data, StructValidateFunc validate, StructCallbackFunc call, StructFreeFunc free)
{
	ARegionType *art;
	PanelType *pt, dummypt = {0};
	Panel dummypanel= {0};
	PointerRNA dummyptr;
	int have_function[3];

	/* setup dummy panel & panel type to store static properties in */
	dummypanel.type= &dummypt;
	RNA_pointer_create(NULL, &RNA_Panel, &dummypanel, &dummyptr);

	/* validate the python class */
	if(validate(&dummyptr, data, have_function) != 0)
		return NULL;
	
	if(!(art=region_type_find(reports, dummypt.space_type, dummypt.region_type)))
		return NULL;

	/* check if we have registered this panel type before, and remove it */
	for(pt=art->paneltypes.first; pt; pt=pt->next) {
		if(strcmp(pt->idname, dummypt.idname) == 0) {
			if(pt->py_srna)
				rna_Panel_unregister(C, pt->py_srna);
			else
				BLI_freelinkN(&art->paneltypes, pt);
			break;
		}
	}
	
	/* create a new panel type */
	pt= MEM_callocN(sizeof(PanelType), "python buttons panel");
	memcpy(pt, &dummypt, sizeof(dummypt));

	pt->py_srna= RNA_def_struct(&BLENDER_RNA, pt->idname, "Panel"); 
	pt->py_data= data;
	pt->py_call= call;
	pt->py_free= free;
	RNA_struct_blender_type_set(pt->py_srna, pt);

	pt->poll= (have_function[0])? panel_poll: NULL;
	pt->draw= (have_function[1])? panel_draw: NULL;
	pt->draw_header= (have_function[2])? panel_draw_header: NULL;

	BLI_addtail(&art->paneltypes, pt);

	/* update while blender is running */
	if(C)
		WM_event_add_notifier(C, NC_SCREEN|NA_EDITED, NULL);
	
	return pt->py_srna;
}

static StructRNA* rna_Panel_refine(struct PointerRNA *ptr)
{
	Panel *hdr= (Panel*)ptr->data;
	return (hdr->type && hdr->type->py_srna)? hdr->type->py_srna: &RNA_Panel;
}

/* Header */

static void header_draw(const bContext *C, Header *hdr)
{
	PointerRNA htr;
	ParameterList list;
	FunctionRNA *func;

	RNA_pointer_create(&CTX_wm_screen(C)->id, hdr->type->py_srna, hdr, &htr);
	func= RNA_struct_find_function(&htr, "draw");

	RNA_parameter_list_create(&list, &htr, func);
	RNA_parameter_set_lookup(&list, "context", &C);
	hdr->type->py_call(&htr, func, &list);

	RNA_parameter_list_free(&list);
}

static void rna_Header_unregister(const bContext *C, StructRNA *type)
{
	ARegionType *art;
	HeaderType *ht= RNA_struct_blender_type_get(type);

	if(!ht)
		return;
	if(!(art=region_type_find(NULL, ht->space_type, RGN_TYPE_HEADER)))
		return;
	
	BLI_freelinkN(&art->headertypes, ht);
	RNA_struct_free(&BLENDER_RNA, type);

	/* update while blender is running */
	if(C)
		WM_event_add_notifier(C, NC_SCREEN|NA_EDITED, NULL);
}

static StructRNA *rna_Header_register(const bContext *C, ReportList *reports, void *data, StructValidateFunc validate, StructCallbackFunc call, StructFreeFunc free)
{
	ARegionType *art;
	HeaderType *ht, dummyht = {0};
	Header dummyheader= {0};
	PointerRNA dummyhtr;
	int have_function[1];

	/* setup dummy header & header type to store static properties in */
	dummyheader.type= &dummyht;
	RNA_pointer_create(NULL, &RNA_Header, &dummyheader, &dummyhtr);

	/* validate the python class */
	if(validate(&dummyhtr, data, have_function) != 0)
		return NULL;
	
	if(!(art=region_type_find(reports, dummyht.space_type, RGN_TYPE_HEADER)))
		return NULL;

	/* check if we have registered this header type before, and remove it */
	for(ht=art->headertypes.first; ht; ht=ht->next) {
		if(strcmp(ht->idname, dummyht.idname) == 0) {
			if(ht->py_srna)
				rna_Header_unregister(C, ht->py_srna);
			break;
		}
	}
	
	/* create a new header type */
	ht= MEM_callocN(sizeof(HeaderType), "python buttons header");
	memcpy(ht, &dummyht, sizeof(dummyht));

	ht->py_srna= RNA_def_struct(&BLENDER_RNA, ht->idname, "Header"); 
	ht->py_data= data;
	ht->py_call= call;
	ht->py_free= free;
	RNA_struct_blender_type_set(ht->py_srna, ht);

	ht->draw= (have_function[0])? header_draw: NULL;

	BLI_addtail(&art->headertypes, ht);

	/* update while blender is running */
	if(C)
		WM_event_add_notifier(C, NC_SCREEN|NA_EDITED, NULL);
	
	return ht->py_srna;
}

static StructRNA* rna_Header_refine(struct PointerRNA *htr)
{
	Header *hdr= (Header*)htr->data;
	return (hdr->type && hdr->type->py_srna)? hdr->type->py_srna: &RNA_Header;
}

/* Menu */

static int menu_poll(const bContext *C, MenuType *pt)
{
	PointerRNA ptr;
	ParameterList list;
	FunctionRNA *func;
	void *ret;
	int visible;

	RNA_pointer_create(NULL, pt->py_srna, NULL, &ptr); /* dummy */
	func= RNA_struct_find_function(&ptr, "poll");

	RNA_parameter_list_create(&list, &ptr, func);
	RNA_parameter_set_lookup(&list, "context", &C);
	pt->py_call(&ptr, func, &list);

	RNA_parameter_get_lookup(&list, "visible", &ret);
	visible= *(int*)ret;

	RNA_parameter_list_free(&list);

	return visible;
}

static void menu_draw(const bContext *C, Menu *hdr)
{
	PointerRNA mtr;
	ParameterList list;
	FunctionRNA *func;

	RNA_pointer_create(&CTX_wm_screen(C)->id, hdr->type->py_srna, hdr, &mtr);
	func= RNA_struct_find_function(&mtr, "draw");

	RNA_parameter_list_create(&list, &mtr, func);
	RNA_parameter_set_lookup(&list, "context", &C);
	hdr->type->py_call(&mtr, func, &list);

	RNA_parameter_list_free(&list);
}

static void rna_Menu_unregister(const bContext *C, StructRNA *type)
{
	ARegionType *art;
	MenuType *mt= RNA_struct_blender_type_get(type);

	if(!mt)
		return;
	if(!(art=region_type_find(NULL, mt->space_type, RGN_TYPE_HEADER)))
		return;
	
	BLI_freelinkN(&art->menutypes, mt);
	RNA_struct_free(&BLENDER_RNA, type);

	/* update while blender is running */
	if(C)
		WM_event_add_notifier(C, NC_SCREEN|NA_EDITED, NULL);
}

static StructRNA *rna_Menu_register(const bContext *C, ReportList *reports, void *data, StructValidateFunc validate, StructCallbackFunc call, StructFreeFunc free)
{
	ARegionType *art;
	MenuType *mt, dummymt = {0};
	Menu dummymenu= {0};
	PointerRNA dummymtr;
	int have_function[2];

	/* setup dummy menu & menu type to store static properties in */
	dummymenu.type= &dummymt;
	RNA_pointer_create(NULL, &RNA_Menu, &dummymenu, &dummymtr);

	/* validate the python class */
	if(validate(&dummymtr, data, have_function) != 0)
		return NULL;
	
	if(!(art=region_type_find(reports, dummymt.space_type, RGN_TYPE_HEADER)))
		return NULL;

	/* check if we have registered this menu type before, and remove it */
	for(mt=art->menutypes.first; mt; mt=mt->next) {
		if(strcmp(mt->idname, dummymt.idname) == 0) {
			if(mt->py_srna)
				rna_Menu_unregister(C, mt->py_srna);
			break;
		}
	}
	
	/* create a new menu type */
	mt= MEM_callocN(sizeof(MenuType), "python buttons menu");
	memcpy(mt, &dummymt, sizeof(dummymt));

	mt->py_srna= RNA_def_struct(&BLENDER_RNA, mt->idname, "Menu"); 
	mt->py_data= data;
	mt->py_call= call;
	mt->py_free= free;
	RNA_struct_blender_type_set(mt->py_srna, mt);

	mt->poll= (have_function[0])? menu_poll: NULL;
	mt->draw= (have_function[1])? menu_draw: NULL;

	BLI_addtail(&art->menutypes, mt);

	/* update while blender is running */
	if(C)
		WM_event_add_notifier(C, NC_SCREEN|NA_EDITED, NULL);
	
	return mt->py_srna;
}

static StructRNA* rna_Menu_refine(struct PointerRNA *mtr)
{
	Menu *hdr= (Menu*)mtr->data;
	return (hdr->type && hdr->type->py_srna)? hdr->type->py_srna: &RNA_Menu;
}

static int rna_UILayout_active_get(struct PointerRNA *ptr)
{
	return uiLayoutGetActive(ptr->data);
}

static void rna_UILayout_active_set(struct PointerRNA *ptr, int value)
{
	uiLayoutSetActive(ptr->data, value);
}

static void rna_UILayout_op_context_set(struct PointerRNA *ptr, int value)
{
	uiLayoutSetOperatorContext(ptr->data, value);
}

static int rna_UILayout_op_context_get(struct PointerRNA *ptr)
{
	return uiLayoutGetOperatorContext(ptr->data);
}

static int rna_UILayout_enabled_get(struct PointerRNA *ptr)
{
	return uiLayoutGetEnabled(ptr->data);
}

static void rna_UILayout_enabled_set(struct PointerRNA *ptr, int value)
{
	uiLayoutSetEnabled(ptr->data, value);
}

static int rna_UILayout_red_alert_get(struct PointerRNA *ptr)
{
	return uiLayoutGetRedAlert(ptr->data);
}

static void rna_UILayout_red_alert_set(struct PointerRNA *ptr, int value)
{
	uiLayoutSetRedAlert(ptr->data, value);
}

static int rna_UILayout_keep_aspect_get(struct PointerRNA *ptr)
{
	return uiLayoutGetKeepAspect(ptr->data);
}

static void rna_UILayout_keep_aspect_set(struct PointerRNA *ptr, int value)
{
	uiLayoutSetKeepAspect(ptr->data, value);
}

static int rna_UILayout_alignment_get(struct PointerRNA *ptr)
{
	return uiLayoutGetAlignment(ptr->data);
}

static void rna_UILayout_alignment_set(struct PointerRNA *ptr, int value)
{
	uiLayoutSetAlignment(ptr->data, value);
}

static float rna_UILayout_scale_x_get(struct PointerRNA *ptr)
{
	return uiLayoutGetScaleX(ptr->data);
}

static void rna_UILayout_scale_x_set(struct PointerRNA *ptr, float value)
{
	uiLayoutSetScaleX(ptr->data, value);
}

static float rna_UILayout_scale_y_get(struct PointerRNA *ptr)
{
	return uiLayoutGetScaleY(ptr->data);
}

static void rna_UILayout_scale_y_set(struct PointerRNA *ptr, float value)
{
	uiLayoutSetScaleY(ptr->data, value);
}

#else // RNA_RUNTIME

static void rna_def_ui_layout(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	static EnumPropertyItem alignment_items[] = {
		{UI_LAYOUT_ALIGN_EXPAND, "EXPAND", 0, "Expand", ""},
		{UI_LAYOUT_ALIGN_LEFT, "LEFT", 0, "Left", ""},
		{UI_LAYOUT_ALIGN_CENTER, "CENTER", 0, "Center", ""},
		{UI_LAYOUT_ALIGN_RIGHT, "RIGHT", 0, "RIght", ""},
		{0, NULL, 0, NULL, NULL}};
		
	/* see WM_types.h */
	static EnumPropertyItem operator_context_items[] = {
		{WM_OP_INVOKE_DEFAULT, "INVOKE_DEFAULT", 0, "Invoke Default", ""},
		{WM_OP_INVOKE_REGION_WIN, "INVOKE_REGION_WIN", 0, "Invoke Region Window", ""},
		{WM_OP_INVOKE_AREA, "INVOKE_AREA", 0, "Invoke Area", ""},
		{WM_OP_INVOKE_SCREEN, "INVOKE_SCREEN", 0, "Invoke Screen", ""},
		{WM_OP_EXEC_DEFAULT, "EXEC_DEFAULT", 0, "Exec Default", ""},
		{WM_OP_EXEC_REGION_WIN, "EXEC_REGION_WIN", 0, "Exec Region Window", ""},
		{WM_OP_EXEC_AREA, "EXEC_AREA", 0, "Exec Area", ""},
		{WM_OP_EXEC_SCREEN, "EXEC_SCREEN", 0, "Exec Screen", ""},
		{0, NULL, 0, NULL, NULL}};

	srna= RNA_def_struct(brna, "UILayout", NULL);
	RNA_def_struct_sdna(srna, "uiLayout");
	RNA_def_struct_ui_text(srna, "UI Layout", "User interface layout in a panel or header.");

	prop= RNA_def_property(srna, "active", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_funcs(prop, "rna_UILayout_active_get", "rna_UILayout_active_set");
	
	prop= RNA_def_property(srna, "operator_context", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_items(prop, operator_context_items);
	RNA_def_property_enum_funcs(prop, "rna_UILayout_op_context_get", "rna_UILayout_op_context_set", NULL);

	prop= RNA_def_property(srna, "enabled", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_funcs(prop, "rna_UILayout_enabled_get", "rna_UILayout_enabled_set");

	prop= RNA_def_property(srna, "red_alert", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_funcs(prop, "rna_UILayout_red_alert_get", "rna_UILayout_red_alert_set");

	prop= RNA_def_property(srna, "alignment", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_items(prop, alignment_items);
	RNA_def_property_enum_funcs(prop, "rna_UILayout_alignment_get", "rna_UILayout_alignment_set", NULL);

	prop= RNA_def_property(srna, "keep_aspect", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_funcs(prop, "rna_UILayout_keep_aspect_get", "rna_UILayout_keep_aspect_set");

	prop= RNA_def_property(srna, "scale_x", PROP_FLOAT, PROP_UNSIGNED);
	RNA_def_property_float_funcs(prop, "rna_UILayout_scale_x_get", "rna_UILayout_scale_x_set", NULL);

	prop= RNA_def_property(srna, "scale_y", PROP_FLOAT, PROP_UNSIGNED);
	RNA_def_property_float_funcs(prop, "rna_UILayout_scale_y_get", "rna_UILayout_scale_y_set", NULL);

	RNA_api_ui_layout(srna);
}

static void rna_def_panel(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;
	FunctionRNA *func;
	
	srna= RNA_def_struct(brna, "Panel", NULL);
	RNA_def_struct_ui_text(srna, "Panel", "Panel containing buttons.");
	RNA_def_struct_sdna(srna, "Panel");
	RNA_def_struct_refine_func(srna, "rna_Panel_refine");
	RNA_def_struct_register_funcs(srna, "rna_Panel_register", "rna_Panel_unregister");

	/* poll */
	func= RNA_def_function(srna, "poll", NULL);
	RNA_def_function_ui_description(func, "Test if the panel is visible or not.");
	RNA_def_function_flag(func, FUNC_REGISTER|FUNC_REGISTER_OPTIONAL);
	RNA_def_function_return(func, RNA_def_boolean(func, "visible", 1, "", ""));
	RNA_def_pointer(func, "context", "Context", "", "");

	/* draw */
	func= RNA_def_function(srna, "draw", NULL);
	RNA_def_function_ui_description(func, "Draw buttons into the panel UI layout.");
	RNA_def_function_flag(func, FUNC_REGISTER);
	RNA_def_pointer(func, "context", "Context", "", "");

	func= RNA_def_function(srna, "draw_header", NULL);
	RNA_def_function_ui_description(func, "Draw buttons into the panel header UI layout.");
	RNA_def_function_flag(func, FUNC_REGISTER);
	RNA_def_pointer(func, "context", "Context", "", "");

	prop= RNA_def_property(srna, "layout", PROP_POINTER, PROP_NONE);
	RNA_def_property_struct_type(prop, "UILayout");

	/* registration */
	prop= RNA_def_property(srna, "idname", PROP_STRING, PROP_NONE);
	RNA_def_property_string_sdna(prop, NULL, "type->idname");
	RNA_def_property_flag(prop, PROP_REGISTER);

	prop= RNA_def_property(srna, "label", PROP_STRING, PROP_NONE);
	RNA_def_property_string_sdna(prop, NULL, "type->label");
	RNA_def_property_flag(prop, PROP_REGISTER);

	prop= RNA_def_property(srna, "space_type", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "type->space_type");
	RNA_def_property_enum_items(prop, space_type_items);
	RNA_def_property_flag(prop, PROP_REGISTER);

	prop= RNA_def_property(srna, "region_type", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "type->region_type");
	RNA_def_property_enum_items(prop, region_type_items);
	RNA_def_property_flag(prop, PROP_REGISTER);

	prop= RNA_def_property(srna, "context", PROP_STRING, PROP_NONE);
	RNA_def_property_string_sdna(prop, NULL, "type->context");
	RNA_def_property_flag(prop, PROP_REGISTER);

	prop= RNA_def_property(srna, "default_closed", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "type->flag", PNL_DEFAULT_CLOSED);
	RNA_def_property_flag(prop, PROP_REGISTER);

	prop= RNA_def_property(srna, "no_header", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "type->flag", PNL_NO_HEADER);
	RNA_def_property_flag(prop, PROP_REGISTER);
}

static void rna_def_header(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;
	FunctionRNA *func;
	
	srna= RNA_def_struct(brna, "Header", NULL);
	RNA_def_struct_ui_text(srna, "Header", "Editor header containing buttons.");
	RNA_def_struct_sdna(srna, "Header");
	RNA_def_struct_refine_func(srna, "rna_Header_refine");
	RNA_def_struct_register_funcs(srna, "rna_Header_register", "rna_Header_unregister");

	/* draw */
	func= RNA_def_function(srna, "draw", NULL);
	RNA_def_function_ui_description(func, "Draw buttons into the header UI layout.");
	RNA_def_function_flag(func, FUNC_REGISTER);
	RNA_def_pointer(func, "context", "Context", "", "");

	prop= RNA_def_property(srna, "layout", PROP_POINTER, PROP_NONE);
	RNA_def_property_struct_type(prop, "UILayout");

	/* registration */
	prop= RNA_def_property(srna, "idname", PROP_STRING, PROP_NONE);
	RNA_def_property_string_sdna(prop, NULL, "type->idname");
	RNA_def_property_flag(prop, PROP_REGISTER);

	prop= RNA_def_property(srna, "space_type", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "type->space_type");
	RNA_def_property_enum_items(prop, space_type_items);
	RNA_def_property_flag(prop, PROP_REGISTER);
}

static void rna_def_menu(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;
	FunctionRNA *func;
	
	srna= RNA_def_struct(brna, "Menu", NULL);
	RNA_def_struct_ui_text(srna, "Menu", "Editor menu containing buttons.");
	RNA_def_struct_sdna(srna, "Menu");
	RNA_def_struct_refine_func(srna, "rna_Menu_refine");
	RNA_def_struct_register_funcs(srna, "rna_Menu_register", "rna_Menu_unregister");

	/* poll */
	func= RNA_def_function(srna, "poll", NULL);
	RNA_def_function_ui_description(func, "Test if the menu is visible or not.");
	RNA_def_function_flag(func, FUNC_REGISTER|FUNC_REGISTER_OPTIONAL);
	RNA_def_function_return(func, RNA_def_boolean(func, "visible", 1, "", ""));
	RNA_def_pointer(func, "context", "Context", "", "");

	/* draw */
	func= RNA_def_function(srna, "draw", NULL);
	RNA_def_function_ui_description(func, "Draw buttons into the menu UI layout.");
	RNA_def_function_flag(func, FUNC_REGISTER);
	RNA_def_pointer(func, "context", "Context", "", "");

	prop= RNA_def_property(srna, "layout", PROP_POINTER, PROP_NONE);
	RNA_def_property_struct_type(prop, "UILayout");

	/* registration */
	prop= RNA_def_property(srna, "idname", PROP_STRING, PROP_NONE);
	RNA_def_property_string_sdna(prop, NULL, "type->idname");
	RNA_def_property_flag(prop, PROP_REGISTER);

	prop= RNA_def_property(srna, "label", PROP_STRING, PROP_NONE);
	RNA_def_property_string_sdna(prop, NULL, "type->label");
	RNA_def_property_flag(prop, PROP_REGISTER);

	prop= RNA_def_property(srna, "space_type", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "type->space_type");
	RNA_def_property_enum_items(prop, space_type_items);
	RNA_def_property_flag(prop, PROP_REGISTER);
}

void RNA_def_ui(BlenderRNA *brna)
{
	rna_def_ui_layout(brna);
	rna_def_panel(brna);
	rna_def_header(brna);
	rna_def_menu(brna);
}

#endif // RNA_RUNTIME


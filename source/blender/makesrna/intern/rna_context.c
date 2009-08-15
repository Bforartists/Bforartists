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
 * Contributor(s): Blender Foundation (2009).
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#include <stdlib.h>

#include "DNA_ID.h"
#include "DNA_userdef_types.h"

#include "RNA_access.h"
#include "RNA_define.h"
#include "RNA_types.h"

#ifdef RNA_RUNTIME

#include "BKE_context.h"

static PointerRNA rna_Context_manager_get(PointerRNA *ptr)
{
	bContext *C= (bContext*)ptr->data;
	return rna_pointer_inherit_refine(ptr, &RNA_WindowManager, CTX_wm_manager(C));
}

static PointerRNA rna_Context_window_get(PointerRNA *ptr)
{
	bContext *C= (bContext*)ptr->data;
	return rna_pointer_inherit_refine(ptr, &RNA_Window, CTX_wm_window(C));
}

static PointerRNA rna_Context_screen_get(PointerRNA *ptr)
{
	bContext *C= (bContext*)ptr->data;
	return rna_pointer_inherit_refine(ptr, &RNA_Screen, CTX_wm_screen(C));
}

static PointerRNA rna_Context_area_get(PointerRNA *ptr)
{
	bContext *C= (bContext*)ptr->data;
	PointerRNA newptr;
	RNA_pointer_create((ID*)CTX_wm_screen(C), &RNA_Area, CTX_wm_area(C), &newptr);
	return newptr;
}

static PointerRNA rna_Context_space_data_get(PointerRNA *ptr)
{
	bContext *C= (bContext*)ptr->data;
	PointerRNA newptr;
	RNA_pointer_create((ID*)CTX_wm_screen(C), &RNA_Space, CTX_wm_space_data(C), &newptr);
	return newptr;
}

static PointerRNA rna_Context_region_get(PointerRNA *ptr)
{
	bContext *C= (bContext*)ptr->data;
	PointerRNA newptr;
	RNA_pointer_create((ID*)CTX_wm_screen(C), &RNA_Region, CTX_wm_region(C), &newptr);
	return newptr;
}

/*static PointerRNA rna_Context_region_data_get(PointerRNA *ptr)
{
	bContext *C= (bContext*)ptr->data;
	PointerRNA newptr;
	RNA_pointer_create((ID*)CTX_wm_screen(C), &RNA_RegionData, CTX_wm_region_data(C), &newptr);
	return newptr;
}*/

static PointerRNA rna_Context_main_get(PointerRNA *ptr)
{
	bContext *C= (bContext*)ptr->data;
	return rna_pointer_inherit_refine(ptr, &RNA_Main, CTX_data_main(C));
}

static PointerRNA rna_Context_scene_get(PointerRNA *ptr)
{
	bContext *C= (bContext*)ptr->data;
	return rna_pointer_inherit_refine(ptr, &RNA_Scene, CTX_data_scene(C));
}

static PointerRNA rna_Context_tool_settings_get(PointerRNA *ptr)
{
	bContext *C= (bContext*)ptr->data;
	return rna_pointer_inherit_refine(ptr, &RNA_ToolSettings, CTX_data_tool_settings(C));
}

static PointerRNA rna_Context_user_preferences_get(PointerRNA *ptr)
{
	PointerRNA newptr;
	RNA_pointer_create(NULL, &RNA_UserPreferences, &U, &newptr);
	return newptr;
}

static void rna_Context_mode_string_get(PointerRNA *ptr, char *value)
{
	bContext *C= (bContext*)ptr->data;
	strcpy(value, CTX_data_mode_string(C));
}

static int rna_Context_mode_string_length(PointerRNA *ptr)
{
	bContext *C= (bContext*)ptr->data;
	return strlen(CTX_data_mode_string(C));
}

#else

void RNA_def_context(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	srna= RNA_def_struct(brna, "Context", NULL);
	RNA_def_struct_ui_text(srna, "Context", "Current windowmanager and data context.");
	RNA_def_struct_sdna(srna, "bContext");

	/* WM */
	prop= RNA_def_property(srna, "manager", PROP_POINTER, PROP_NONE);
	RNA_def_property_clear_flag(prop, PROP_EDITABLE);
	RNA_def_property_struct_type(prop, "WindowManager");
	RNA_def_property_pointer_funcs(prop, "rna_Context_manager_get", NULL, NULL);

	prop= RNA_def_property(srna, "window", PROP_POINTER, PROP_NONE);
	RNA_def_property_clear_flag(prop, PROP_EDITABLE);
	RNA_def_property_struct_type(prop, "Window");
	RNA_def_property_pointer_funcs(prop, "rna_Context_window_get", NULL, NULL);

	prop= RNA_def_property(srna, "screen", PROP_POINTER, PROP_NONE);
	RNA_def_property_clear_flag(prop, PROP_EDITABLE);
	RNA_def_property_struct_type(prop, "Screen");
	RNA_def_property_pointer_funcs(prop, "rna_Context_screen_get", NULL, NULL);

	prop= RNA_def_property(srna, "area", PROP_POINTER, PROP_NONE);
	RNA_def_property_clear_flag(prop, PROP_EDITABLE);
	RNA_def_property_struct_type(prop, "Area");
	RNA_def_property_pointer_funcs(prop, "rna_Context_area_get", NULL, NULL);

	prop= RNA_def_property(srna, "space_data", PROP_POINTER, PROP_NONE);
	RNA_def_property_clear_flag(prop, PROP_EDITABLE);
	RNA_def_property_struct_type(prop, "Space");
	RNA_def_property_pointer_funcs(prop, "rna_Context_space_data_get", NULL, NULL);

	prop= RNA_def_property(srna, "region", PROP_POINTER, PROP_NONE);
	RNA_def_property_clear_flag(prop, PROP_EDITABLE);
	RNA_def_property_struct_type(prop, "Region");
	RNA_def_property_pointer_funcs(prop, "rna_Context_region_get", NULL, NULL);

	/*prop= RNA_def_property(srna, "region_data", PROP_POINTER, PROP_NONE);
	RNA_def_property_clear_flag(prop, PROP_EDITABLE);
	RNA_def_property_struct_type(prop, "RegionData");
	RNA_def_property_pointer_funcs(prop, "rna_Context_region_data_get", NULL, NULL);*/

	/* Data */
	prop= RNA_def_property(srna, "main", PROP_POINTER, PROP_NONE);
	RNA_def_property_clear_flag(prop, PROP_EDITABLE);
	RNA_def_property_struct_type(prop, "Main");
	RNA_def_property_pointer_funcs(prop, "rna_Context_main_get", NULL, NULL);

	prop= RNA_def_property(srna, "scene", PROP_POINTER, PROP_NONE);
	RNA_def_property_clear_flag(prop, PROP_EDITABLE);
	RNA_def_property_struct_type(prop, "Scene");
	RNA_def_property_pointer_funcs(prop, "rna_Context_scene_get", NULL, NULL);

	prop= RNA_def_property(srna, "tool_settings", PROP_POINTER, PROP_NONE);
	RNA_def_property_clear_flag(prop, PROP_EDITABLE);
	RNA_def_property_struct_type(prop, "ToolSettings");
	RNA_def_property_pointer_funcs(prop, "rna_Context_tool_settings_get", NULL, NULL);

	prop= RNA_def_property(srna, "user_preferences", PROP_POINTER, PROP_NONE);
	RNA_def_property_clear_flag(prop, PROP_EDITABLE);
	RNA_def_property_struct_type(prop, "UserPreferences");
	RNA_def_property_pointer_funcs(prop, "rna_Context_user_preferences_get", NULL, NULL);

	prop= RNA_def_property(srna, "mode_string", PROP_STRING, PROP_NONE);
	RNA_def_property_clear_flag(prop, PROP_EDITABLE);
	RNA_def_property_string_funcs(prop, "rna_Context_mode_string_get", "rna_Context_mode_string_length", NULL);
}

#endif


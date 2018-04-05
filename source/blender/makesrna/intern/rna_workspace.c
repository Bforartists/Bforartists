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
 * ***** END GPL LICENSE BLOCK *****
 */

/** \file blender/makesrna/intern/rna_workspace.c
 *  \ingroup RNA
 */

#include "RNA_define.h"
#include "RNA_enum_types.h"
#include "RNA_types.h"

#include "BKE_workspace.h"

#include "ED_render.h"

#include "RE_engine.h"

#include "WM_api.h"
#include "WM_types.h"

#include "rna_internal.h"

/* Allow accessing private members of DNA_workspace_types.h */
#define DNA_PRIVATE_WORKSPACE_ALLOW
#include "DNA_workspace_types.h"

#ifdef RNA_RUNTIME

#include "BLI_listbase.h"

#include "BKE_global.h"

#include "DNA_object_types.h"
#include "DNA_screen_types.h"

#include "RNA_access.h"

static void rna_window_update_all(Main *UNUSED(bmain), Scene *UNUSED(scene), PointerRNA *UNUSED(ptr))
{
	WM_main_add_notifier(NC_WINDOW, NULL);
}

void rna_workspace_screens_begin(CollectionPropertyIterator *iter, PointerRNA *ptr)
{
	WorkSpace *workspace = ptr->id.data;
	rna_iterator_listbase_begin(iter, BKE_workspace_layouts_get(workspace), NULL);
}

static PointerRNA rna_workspace_screens_item_get(CollectionPropertyIterator *iter)
{
	WorkSpaceLayout *layout = rna_iterator_listbase_get(iter);
	bScreen *screen = BKE_workspace_layout_screen_get(layout);

	return rna_pointer_inherit_refine(&iter->parent, &RNA_Screen, screen);
}

void rna_workspace_transform_orientations_begin(CollectionPropertyIterator *iter, PointerRNA *ptr)
{
	WorkSpace *workspace = ptr->id.data;
	rna_iterator_listbase_begin(iter, BKE_workspace_transform_orientations_get(workspace), NULL);
}

static PointerRNA rna_workspace_transform_orientations_item_get(CollectionPropertyIterator *iter)
{
	TransformOrientation *transform_orientation = rna_iterator_listbase_get(iter);
	return rna_pointer_inherit_refine(&iter->parent, &RNA_TransformOrientation, transform_orientation);
}

/* workspace.owner_ids */

static wmOwnerID *rna_WorkSpace_owner_ids_new(
        WorkSpace *workspace, const char *name)
{
	wmOwnerID *owner_id = MEM_callocN(sizeof(*owner_id), __func__);
	BLI_addtail(&workspace->owner_ids, owner_id);
	BLI_strncpy(owner_id->name, name, sizeof(owner_id->name));
	WM_main_add_notifier(NC_WINDOW, NULL);
	return owner_id;
}

static void rna_WorkSpace_owner_ids_remove(
        WorkSpace *workspace, ReportList *reports, PointerRNA *wstag_ptr)
{
	wmOwnerID *owner_id = wstag_ptr->data;
	if (BLI_remlink_safe(&workspace->owner_ids, owner_id) == false) {
		BKE_reportf(reports, RPT_ERROR,
		            "wmOwnerID '%s' not in workspace '%s'",
		            owner_id->name, workspace->id.name + 2);
		return;
	}

	MEM_freeN(owner_id);
	RNA_POINTER_INVALIDATE(wstag_ptr);

	WM_main_add_notifier(NC_WINDOW, NULL);
}

static void rna_WorkSpace_owner_ids_clear(
        WorkSpace *workspace)
{
	BLI_freelistN(&workspace->owner_ids);
	WM_main_add_notifier(NC_OBJECT | ND_MODIFIER | NA_REMOVED, workspace);
}

#else /* RNA_RUNTIME */

static void rna_def_workspace_owner(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	srna = RNA_def_struct(brna, "wmOwnerID", NULL);
	RNA_def_struct_sdna(srna, "wmOwnerID");
	RNA_def_struct_clear_flag(srna, STRUCT_UNDO);
	RNA_def_struct_ui_text(srna, "Work Space UI Tag", "");

	prop = RNA_def_property(srna, "name", PROP_STRING, PROP_NONE);
	RNA_def_property_ui_text(prop, "Name", "");
	RNA_def_struct_name_property(srna, prop);
}

static void rna_def_workspace_owner_ids(BlenderRNA *brna, PropertyRNA *cprop)
{
	StructRNA *srna;

	FunctionRNA *func;
	PropertyRNA *parm;

	RNA_def_property_srna(cprop, "wmOwnerIDs");
	srna = RNA_def_struct(brna, "wmOwnerIDs", NULL);
	RNA_def_struct_sdna(srna, "WorkSpace");
	RNA_def_struct_ui_text(srna, "WorkSpace UI Tags", "");

	/* add owner_id */
	func = RNA_def_function(srna, "new", "rna_WorkSpace_owner_ids_new");
	RNA_def_function_ui_description(func, "Add ui tag");
	parm = RNA_def_string(func, "name", "Name", 0, "", "New name for the tag");
	RNA_def_parameter_flags(parm, 0, PARM_REQUIRED);
	/* return type */
	parm = RNA_def_pointer(func, "owner_id", "wmOwnerID", "", "");
	RNA_def_function_return(func, parm);

	/* remove owner_id */
	func = RNA_def_function(srna, "remove", "rna_WorkSpace_owner_ids_remove");
	RNA_def_function_flag(func, FUNC_USE_REPORTS);
	RNA_def_function_ui_description(func, "Remove ui tag");
	/* owner_id to remove */
	parm = RNA_def_pointer(func, "owner_id", "wmOwnerID", "", "Tag to remove");
	RNA_def_parameter_flags(parm, PROP_NEVER_NULL, PARM_REQUIRED | PARM_RNAPTR);
	RNA_def_parameter_clear_flags(parm, PROP_THICK_WRAP, 0);

	/* clear all modifiers */
	func = RNA_def_function(srna, "clear", "rna_WorkSpace_owner_ids_clear");
	RNA_def_function_ui_description(func, "Remove all tags");
}

static void rna_def_workspace(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	srna = RNA_def_struct(brna, "WorkSpace", "ID");
	RNA_def_struct_sdna(srna, "WorkSpace");
	RNA_def_struct_ui_text(srna, "Workspace", "Workspace data-block, defining the working environment for the user");
	/* TODO: real icon, just to show something */
	RNA_def_struct_ui_icon(srna, ICON_RENDER_RESULT);

	prop = RNA_def_property(srna, "screens", PROP_COLLECTION, PROP_NONE);
	RNA_def_property_collection_sdna(prop, NULL, "layouts", NULL);
	RNA_def_property_struct_type(prop, "Screen");
	RNA_def_property_collection_funcs(prop, "rna_workspace_screens_begin", NULL, NULL,
	                                  "rna_workspace_screens_item_get", NULL, NULL, NULL, NULL);
	RNA_def_property_ui_text(prop, "Screens", "Screen layouts of a workspace");

	prop = RNA_def_property(srna, "tool_keymap", PROP_STRING, PROP_NONE);
	RNA_def_property_string_sdna(prop, NULL, "tool.keymap");
	RNA_def_property_ui_text(prop, "Active Tool", "Currently active tool keymap");
	RNA_def_property_clear_flag(prop, PROP_EDITABLE);

	prop = RNA_def_property(srna, "tool_manipulator_group", PROP_STRING, PROP_NONE);
	RNA_def_property_string_sdna(prop, NULL, "tool.manipulator_group");
	RNA_def_property_ui_text(prop, "Active Tool", "Currently active tool manipulator");
	RNA_def_property_clear_flag(prop, PROP_EDITABLE);

	prop = RNA_def_property(srna, "tool_index", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "tool.index");
	RNA_def_property_ui_text(prop, "Active Tool Index", "Tool group index");
	RNA_def_property_clear_flag(prop, PROP_EDITABLE);

	prop = RNA_def_property(srna, "orientations", PROP_COLLECTION, PROP_NONE);
	RNA_def_property_collection_sdna(prop, NULL, "transform_orientations", NULL);
	RNA_def_property_struct_type(prop, "TransformOrientation");
	RNA_def_property_collection_funcs(prop, "rna_workspace_transform_orientations_begin", NULL, NULL,
	                                  "rna_workspace_transform_orientations_item_get", NULL, NULL, NULL, NULL);
	RNA_def_property_ui_text(prop, "Transform Orientations", "");

	prop = RNA_def_property(srna, "owner_ids", PROP_COLLECTION, PROP_NONE);
	RNA_def_property_struct_type(prop, "wmOwnerID");
	RNA_def_property_ui_text(prop, "UI Tags", "");
	rna_def_workspace_owner_ids(brna, prop);

#if 0
	prop = RNA_def_property(srna, "object_mode", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_items(prop, rna_enum_object_mode_items);
	RNA_def_property_ui_text(prop, "Mode", "Object interaction mode used in this window");
#endif

	/* View Render */
	prop = RNA_def_property(srna, "view_render", PROP_POINTER, PROP_NONE);
	RNA_def_property_flag(prop, PROP_NEVER_NULL);
	RNA_def_property_struct_type(prop, "ViewRenderSettings");
	RNA_def_property_ui_text(prop, "View Render", "");

	/* Flags */
	prop = RNA_def_property(srna, "use_scene_settings", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_clear_flag(prop, PROP_ANIMATABLE);
	RNA_def_property_boolean_sdna(prop, NULL, "flags", WORKSPACE_USE_SCENE_SETTINGS);
	RNA_def_property_ui_text(prop, "Scene Settings",
	                         "Use scene settings instead of workspace settings");
	RNA_def_property_update(prop, NC_SCREEN | ND_LAYER, NULL);

	prop = RNA_def_property(srna, "use_filter_by_owner", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_clear_flag(prop, PROP_ANIMATABLE);
	RNA_def_property_boolean_sdna(prop, NULL, "flags", WORKSPACE_USE_FILTER_BY_ORIGIN);
	RNA_def_property_ui_text(prop, "Use UI Tags",
	                         "Filter the UI by tags");
	RNA_def_property_update(prop, 0, "rna_window_update_all");
}

static void rna_def_transform_orientation(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	srna = RNA_def_struct(brna, "TransformOrientation", NULL);

	prop = RNA_def_property(srna, "matrix", PROP_FLOAT, PROP_MATRIX);
	RNA_def_property_float_sdna(prop, NULL, "mat");
	RNA_def_property_multi_array(prop, 2, rna_matrix_dimsize_3x3);
	RNA_def_property_update(prop, NC_SPACE | ND_SPACE_VIEW3D, NULL);

	prop = RNA_def_property(srna, "name", PROP_STRING, PROP_NONE);
	RNA_def_struct_name_property(srna, prop);
	RNA_def_property_ui_text(prop, "Name", "Name of the custom transform orientation");
	RNA_def_property_update(prop, NC_SPACE | ND_SPACE_VIEW3D, NULL);
}

void RNA_def_workspace(BlenderRNA *brna)
{
	rna_def_workspace_owner(brna);
	rna_def_workspace(brna);
	rna_def_transform_orientation(brna);
}

#endif /* RNA_RUNTIME */

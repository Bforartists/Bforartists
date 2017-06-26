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

/** \file blender/makesrna/intern/rna_wm_manipulator_api.c
 *  \ingroup RNA
 */


#include <stdlib.h>
#include <stdio.h>

#include "BLI_utildefines.h"

#include "BKE_report.h"

#include "RNA_define.h"
#include "RNA_enum_types.h"

#include "DNA_windowmanager_types.h"

#include "WM_api.h"

#include "rna_internal.h"  /* own include */

#ifdef RNA_RUNTIME

#include "UI_interface.h"
#include "BKE_context.h"

#include "ED_manipulator_library.h"

static void rna_manipulator_draw_preset_box(
        wmManipulator *mpr, float matrix[16], int select_id)
{
	ED_manipulator_draw_preset_box(mpr, (float (*)[4])matrix, select_id);
}

static void rna_manipulator_draw_preset_arrow(
        wmManipulator *mpr, float matrix[16], int axis, int select_id)
{
	ED_manipulator_draw_preset_arrow(mpr, (float (*)[4])matrix, axis, select_id);
}

static void rna_manipulator_draw_preset_circle(
        wmManipulator *mpr, float matrix[16], int axis, int select_id)
{
	ED_manipulator_draw_preset_circle(mpr, (float (*)[4])matrix, axis, select_id);
}

static void rna_manipulator_draw_preset_facemap(
        wmManipulator *mpr, struct bContext *C, struct Object *ob, int facemap, int select_id)
{
	struct Scene *scene = CTX_data_scene(C);
	ED_manipulator_draw_preset_facemap(mpr, scene, ob, facemap, select_id);
}

static void rna_manipulator_target_set_prop(
        wmManipulator *mpr, ReportList *reports, const char *target_propname,
        PointerRNA *ptr, const char *propname, int index)
{
	const wmManipulatorPropertyType *mpr_prop_type =
	        WM_manipulatortype_target_property_find(mpr->type, target_propname);
	if (mpr_prop_type == NULL) {
		BKE_reportf(reports, RPT_ERROR, "Manipulator target property '%s.%s' not found",
		            mpr->type->idname, target_propname);
		return;
	}

	PropertyRNA *prop = RNA_struct_find_property(ptr, propname);
	if (prop == NULL) {
		BKE_reportf(reports, RPT_ERROR, "Property '%s.%s' not found",
		            RNA_struct_identifier(ptr->type), target_propname);
		return;
	}

	if (mpr_prop_type->data_type != RNA_property_type(prop)) {
		const int manipulator_type_index = RNA_enum_from_value(rna_enum_property_type_items, mpr_prop_type->data_type);
		const int prop_type_index = RNA_enum_from_value(rna_enum_property_type_items, RNA_property_type(prop));
		BLI_assert((manipulator_type_index != -1) && (prop_type_index == -1));

		BKE_reportf(reports, RPT_ERROR, "Manipulator target '%s.%s' expects '%s', '%s.%s' is '%s'",
		            mpr->type->idname, target_propname,
		            rna_enum_property_type_items[manipulator_type_index].identifier,
		            RNA_struct_identifier(ptr->type), propname,
		            rna_enum_property_type_items[prop_type_index].identifier);
		return;
	}

	if (RNA_property_array_check(prop)) {
		if (index == -1) {
			const int prop_array_length = RNA_property_array_length(ptr, prop);
			if (mpr_prop_type->array_length != prop_array_length) {
				BKE_reportf(reports, RPT_ERROR,
				            "Manipulator target property '%s.%s' expects an array of length %d, found %d",
				            mpr->type->idname, target_propname,
				            mpr_prop_type->array_length,
				            prop_array_length);
				return;
			}
		}
	}
	else {
		if (mpr_prop_type->array_length != 1) {
			BKE_reportf(reports, RPT_ERROR,
			            "Manipulator target property '%s.%s' expects an array of length %d",
			            mpr->type->idname, target_propname,
			            mpr_prop_type->array_length);
			return;
		}
	}

	if (index >= mpr_prop_type->array_length) {
		BKE_reportf(reports, RPT_ERROR, "Manipulator target property '%s.%s', index %d must be below %d",
		            mpr->type->idname, target_propname, index, mpr_prop_type->array_length);
		return;
	}

	WM_manipulator_target_property_def_rna_ptr(mpr, mpr_prop_type, ptr, prop, index);
}

static PointerRNA rna_manipulator_target_set_operator(
        wmManipulator *mpr, ReportList *reports, const char *opname)
{
	wmOperatorType *ot;

	ot = WM_operatortype_find(opname, 0); /* print error next */
	if (!ot || !ot->srna) {
		BKE_reportf(reports, RPT_ERROR, "%s '%s'", ot ? "unknown operator" : "operator missing srna", opname);
		return PointerRNA_NULL;
	}

	/* For the return value to be usable, we need 'PointerRNA.data' to be set. */
	IDProperty *properties;
	{
		IDPropertyTemplate val = {0};
		properties = IDP_New(IDP_GROUP, &val, "wmManipulatorProperties");
	}

	WM_manipulator_set_operator(mpr, ot, properties);

	return mpr->op_data.ptr;
}

#else

void RNA_api_manipulator(StructRNA *srna)
{
	/* Utility draw functions, since we don't expose new OpenGL drawing wrappers via Python yet.
	 * exactly how these should be exposed isn't totally clear.
	 * However it's probably good to have some high level API's for this anyway.
	 * Just note that this could be re-worked once tests are done.
	 */

	FunctionRNA *func;
	PropertyRNA *parm;

	/* -------------------------------------------------------------------- */
	/* Primitive Shapes */

	/* draw_preset_box */
	func = RNA_def_function(srna, "draw_preset_box", "rna_manipulator_draw_preset_box");
	RNA_def_function_ui_description(func, "Draw a box");
	parm = RNA_def_property(func, "matrix", PROP_FLOAT, PROP_MATRIX);
	RNA_def_property_flag(parm, PARM_REQUIRED);
	RNA_def_property_multi_array(parm, 2, rna_matrix_dimsize_4x4);
	RNA_def_property_ui_text(parm, "", "The matrix to transform");
	RNA_def_int(func, "select_id", -1, -1, INT_MAX, "Zero when not selecting", "", -1, INT_MAX);

	/* draw_preset_box */
	func = RNA_def_function(srna, "draw_preset_arrow", "rna_manipulator_draw_preset_arrow");
	RNA_def_function_ui_description(func, "Draw a box");
	parm = RNA_def_property(func, "matrix", PROP_FLOAT, PROP_MATRIX);
	RNA_def_property_flag(parm, PARM_REQUIRED);
	RNA_def_property_multi_array(parm, 2, rna_matrix_dimsize_4x4);
	RNA_def_property_ui_text(parm, "", "The matrix to transform");
	RNA_def_enum(func, "axis", rna_enum_object_axis_items, 2, "", "Arrow Orientation");
	RNA_def_int(func, "select_id", -1, -1, INT_MAX, "Zero when not selecting", "", -1, INT_MAX);

	func = RNA_def_function(srna, "draw_preset_circle", "rna_manipulator_draw_preset_circle");
	RNA_def_function_ui_description(func, "Draw a box");
	parm = RNA_def_property(func, "matrix", PROP_FLOAT, PROP_MATRIX);
	RNA_def_property_flag(parm, PARM_REQUIRED);
	RNA_def_property_multi_array(parm, 2, rna_matrix_dimsize_4x4);
	RNA_def_property_ui_text(parm, "", "The matrix to transform");
	RNA_def_enum(func, "axis", rna_enum_object_axis_items, 2, "", "Arrow Orientation");
	RNA_def_int(func, "select_id", -1, -1, INT_MAX, "Zero when not selecting", "", -1, INT_MAX);

	/* -------------------------------------------------------------------- */
	/* Other Shapes */

	/* draw_preset_facemap */
	func = RNA_def_function(srna, "draw_preset_facemap", "rna_manipulator_draw_preset_facemap");
	RNA_def_function_ui_description(func, "Draw the face-map of a mesh object");
	RNA_def_function_flag(func, FUNC_USE_CONTEXT);
	parm = RNA_def_pointer(func, "object", "Object", "", "Object");
	RNA_def_parameter_flags(parm, PROP_NEVER_NULL, PARM_REQUIRED);
	RNA_def_int(func, "facemap", 0, 0, INT_MAX, "Face map index", "", 0, INT_MAX);
	RNA_def_int(func, "select_id", -1, -1, INT_MAX, "Zero when not selecting", "", -1, INT_MAX);


	/* -------------------------------------------------------------------- */
	/* Property API */

	/* note, 'target_set_handler' is defined in 'bpy_rna_manipulator.c' */
	func = RNA_def_function(srna, "target_set_prop", "rna_manipulator_target_set_prop");
	RNA_def_function_flag(func, FUNC_USE_REPORTS);
	RNA_def_function_ui_description(func, "");
	parm = RNA_def_string(func, "target", NULL, 0, "", "Target property");
	RNA_def_parameter_flags(parm, 0, PARM_REQUIRED);
	/* similar to UILayout.prop */
	parm = RNA_def_pointer(func, "data", "AnyType", "", "Data from which to take property");
	RNA_def_parameter_flags(parm, PROP_NEVER_NULL, PARM_REQUIRED | PARM_RNAPTR);
	parm = RNA_def_string(func, "property", NULL, 0, "", "Identifier of property in data");
	RNA_def_parameter_flags(parm, 0, PARM_REQUIRED);
	RNA_def_int(func, "index", -1, -1, INT_MAX, "", "", -1, INT_MAX); /* RNA_NO_INDEX == -1 */

	func = RNA_def_function(srna, "target_set_operator", "rna_manipulator_target_set_operator");
	RNA_def_function_flag(func, FUNC_USE_REPORTS);
	RNA_def_function_ui_description(
	        func,"Operator to run when activating the manipulator "
	        "(overrides property targets)");
	parm = RNA_def_string(func, "operator", NULL, 0, "", "Target operator");
	RNA_def_parameter_flags(parm, 0, PARM_REQUIRED);
	/* similar to UILayout.operator */
	parm = RNA_def_pointer(func, "properties", "OperatorProperties", "", "Operator properties to fill in");
	RNA_def_parameter_flags(parm, 0, PARM_REQUIRED | PARM_RNAPTR);
	RNA_def_function_return(func, parm);

}


void RNA_api_manipulatorgroup(StructRNA *UNUSED(srna))
{
	/* nothing yet */
}

#endif

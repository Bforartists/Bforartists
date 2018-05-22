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

/** \file blender/makesrna/intern/rna_workspace_api.c
 *  \ingroup RNA
 */


#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <time.h>

#include "BLI_utildefines.h"

#include "RNA_define.h"

#include "DNA_object_types.h"
#include "DNA_windowmanager_types.h"

#include "RNA_enum_types.h"  /* own include */

#include "rna_internal.h"  /* own include */

#ifdef RNA_RUNTIME

static void rna_WorkspaceTool_setup(
        ID *id,
        bToolRef *tref,
        bContext *C,
        const char *name,
        /* Args for: 'bToolRef_Runtime'. */
        int cursor,
        const char *keymap,
        const char *manipulator_group,
        const char *data_block,
        int index)
{
	bToolRef_Runtime tref_rt = {0};

	tref_rt.cursor = cursor;
	STRNCPY(tref_rt.keymap, keymap);
	STRNCPY(tref_rt.manipulator_group, manipulator_group);
	STRNCPY(tref_rt.data_block, data_block);
	tref_rt.index = index;

	WM_toolsystem_ref_set_from_runtime(C, (WorkSpace *)id, tref, &tref_rt, name);
}

static PointerRNA rna_WorkspaceTool_operator_properties(
        bToolRef *tref,
        const char *idname)
{
	wmOperatorType *ot = WM_operatortype_find(idname, true);

	if (ot != NULL) {
		PointerRNA ptr;
		WM_toolsystem_ref_properties_ensure(tref, ot, &ptr);
		return ptr;
	}
	return PointerRNA_NULL;
}

#else

void RNA_api_workspace(StructRNA *UNUSED(srna))
{
	/* FunctionRNA *func; */
	/* PropertyRNA *parm; */
}

void RNA_api_workspace_tool(StructRNA *srna)
{
	PropertyRNA *parm;
	FunctionRNA *func;

	func = RNA_def_function(srna, "setup", "rna_WorkspaceTool_setup");
	RNA_def_function_flag(func, FUNC_USE_SELF_ID | FUNC_USE_CONTEXT);
	RNA_def_function_ui_description(func, "Set the tool settings");

	parm = RNA_def_string(func, "name", NULL, KMAP_MAX_NAME, "Name", "");
	RNA_def_parameter_flags(parm, 0, PARM_REQUIRED);

	/* 'bToolRef_Runtime' */
	parm = RNA_def_property(func, "cursor", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_items(parm, rna_enum_window_cursor_items);
	RNA_def_string(func, "keymap", NULL, KMAP_MAX_NAME, "Key Map", "");
	RNA_def_string(func, "manipulator_group", NULL, MAX_NAME, "Manipulator Group", "");
	RNA_def_string(func, "data_block", NULL, MAX_NAME, "Data Block", "");
	RNA_def_int(func, "index", 0, INT_MIN, INT_MAX, "Index", "", INT_MIN, INT_MAX);

	/* Access tool operator options (optionally create). */
	func = RNA_def_function(srna, "operator_properties", "rna_WorkspaceTool_operator_properties");
	parm = RNA_def_string(func, "operator", NULL, 0, "", "");
	RNA_def_parameter_flags(parm, 0, PARM_REQUIRED);
	/* return */
	parm = RNA_def_pointer(func, "result", "OperatorProperties", "", "");
	RNA_def_parameter_flags(parm, PROP_NEVER_NULL, PARM_RNAPTR);
	RNA_def_function_return(func, parm);

}

#endif

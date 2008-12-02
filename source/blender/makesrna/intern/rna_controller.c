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
 * Contributor(s): Blender Foundation (2008).
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#include <stdlib.h>

#include "RNA_access.h"
#include "RNA_define.h"
#include "RNA_types.h"

#include "rna_internal.h"

#include "DNA_controller_types.h"

#ifdef RNA_RUNTIME

static struct StructRNA* rna_Controller_refine(struct PointerRNA *ptr)
{
	bController *controller= (bController*)ptr->data;

	switch(controller->type) {
		case CONT_LOGIC_AND:
			return &RNA_AndController;
		case CONT_LOGIC_OR:
			return &RNA_OrController;
		case CONT_LOGIC_NAND:
			return &RNA_NandController;
		case CONT_LOGIC_NOR:
			return &RNA_NorController;
		case CONT_LOGIC_XOR:
			return &RNA_XorController;
		case CONT_LOGIC_XNOR:
			return &RNA_XnorController;
 		case CONT_EXPRESSION:
			return &RNA_ExpressionController;
		case CONT_PYTHON:
			return &RNA_PythonController;
		default:
			return &RNA_Controller;
	}
}

#else

void RNA_def_controller(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;
	static EnumPropertyItem controller_type_items[] ={
		{CONT_LOGIC_AND, "LOGICAND", "Logic And", ""},
		{CONT_LOGIC_OR, "LOGICOR", "Logic Or", ""},
		{CONT_LOGIC_NAND, "LOGICNAND", "Logic Nand", ""},
		{CONT_LOGIC_NOR, "LOGICNOR", "Logic Nor", ""},
		{CONT_LOGIC_XOR, "LOGICXOR", "Logic Xor", ""},
		{CONT_LOGIC_XNOR, "LOGICXNOR", "Logic Xnor", ""},
		{CONT_EXPRESSION, "EXPRESSION", "Expression", ""},
		{CONT_PYTHON, "PYTHON", "Python Script", ""},
		{0, NULL, NULL, NULL}};

	/* Controller */
	srna= RNA_def_struct(brna, "Controller", NULL , "Controller");
	RNA_def_struct_sdna(srna, "bController");
	RNA_def_struct_funcs(srna, NULL, "rna_Controller_refine");

	prop= RNA_def_property(srna, "name", PROP_STRING, PROP_NONE);
	RNA_def_property_ui_text(prop, "Name", "");
	RNA_def_struct_name_property(srna, prop);

	/* type is not editable, would need to do proper data free/alloc */
	prop= RNA_def_property(srna, "type", PROP_ENUM, PROP_NONE);
	RNA_def_property_flag(prop, PROP_NOT_EDITABLE);
	RNA_def_property_enum_items(prop, controller_type_items);
	RNA_def_property_ui_text(prop, "Type", "");

	/* Expression Controller */
	srna= RNA_def_struct(brna, "ExpressionController", "Controller", "Expression Controller");
	RNA_def_struct_sdna_from(srna, "bExpressionCont", "data");

	prop= RNA_def_property(srna, "expression", PROP_STRING, PROP_NONE);
	RNA_def_property_string_sdna(prop, NULL, "str");
	RNA_def_property_string_maxlength(prop, 127);
	RNA_def_property_ui_text(prop, "Expression", "");

	/* Python Controller */
	srna= RNA_def_struct(brna, "PythonController", "Controller" , "Python Controller");
	RNA_def_struct_sdna_from(srna, "bPythonCont", "data");

	prop= RNA_def_property(srna, "text", PROP_POINTER, PROP_NONE);
	RNA_def_property_struct_type(prop, "ID");
	RNA_def_property_ui_text(prop, "Python Text", "");

	/* Other Controllers */
	RNA_def_struct(brna, "AndController", "Controller", "And Controller");
	RNA_def_struct(brna, "OrController", "Controller", "Or Controller");
	RNA_def_struct(brna, "NorController", "Controller", "Nor Controller");
	RNA_def_struct(brna, "NandController", "Controller", "Nand Controller");
	RNA_def_struct(brna, "XorController", "Controller", "Xor Controller");
	RNA_def_struct(brna, "XnorController", "Controller", "Xnor Controller");
}

#endif


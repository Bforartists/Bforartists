/*
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
 * Contributor(s): Campbell Barton
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#include <stdlib.h>
#include <stdio.h>


#include "RNA_define.h"

#ifdef RNA_RUNTIME

#else

void RNA_api_text(StructRNA *srna)
{
	FunctionRNA *func;
	PropertyRNA *prop;

	func= RNA_def_function(srna, "clear", "clear_text");
	RNA_def_function_ui_description(func, "clear the text block.");

	func= RNA_def_function(srna, "write", "write_text");
	RNA_def_function_ui_description(func, "write text at the cursor location and advance to the end of the text block.");
	prop= RNA_def_string(func, "text", "Text", 0, "", "New text for this datablock.");
	RNA_def_property_flag(prop, PROP_REQUIRED);
}

#endif

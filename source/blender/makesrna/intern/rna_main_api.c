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
 * The Original Code is Copyright (C) 2009 Blender Foundation.
 * All rights reserved.
 *
 * 
 * Contributor(s): Blender Foundation
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#include <stdlib.h>
#include <stdio.h>

#include "RNA_define.h"
#include "RNA_types.h"

#include "DNA_object_types.h"

#ifdef RNA_RUNTIME

#include "BKE_main.h"
#include "BKE_mesh.h"
#include "BKE_library.h"
#include "BKE_object.h"

#include "DNA_mesh_types.h"

static Mesh *rna_Main_add_mesh(Main *main, char *name)
{
	Mesh *me= add_mesh(name);
	me->id.us--;
	return me;
}

static void rna_Main_remove_mesh(Main *main, ReportList *reports, Mesh *me)
{
	if(me->id.us == 0)
		free_libblock(&main->mesh, me);
	else
		BKE_report(reports, RPT_ERROR, "Mesh must have zero users to be removed.");
	
	/* XXX python now has invalid pointer? */
}

static Object* rna_Main_add_object(Main *main, int type, char *name)
{
	return add_only_object(type, name);
}

#else

void RNA_api_main(StructRNA *srna)
{
	FunctionRNA *func;
	PropertyRNA *parm;

	/* copied from rna_def_object */
	static EnumPropertyItem object_type_items[] = {
		{OB_EMPTY, "EMPTY", 0, "Empty", ""},
		{OB_MESH, "MESH", 0, "Mesh", ""},
		{OB_CURVE, "CURVE", 0, "Curve", ""},
		{OB_SURF, "SURFACE", 0, "Surface", ""},
		{OB_FONT, "TEXT", 0, "Text", ""},
		{OB_MBALL, "META", 0, "Meta", ""},
		{OB_LAMP, "LAMP", 0, "Lamp", ""},
		{OB_CAMERA, "CAMERA", 0, "Camera", ""},
		{OB_WAVE, "WAVE", 0, "Wave", ""},
		{OB_LATTICE, "LATTICE", 0, "Lattice", ""},
		{OB_ARMATURE, "ARMATURE", 0, "Armature", ""},
		{0, NULL, 0, NULL, NULL}};

	func= RNA_def_function(srna, "add_object", "rna_Main_add_object");
	RNA_def_function_ui_description(func, "Add a new object.");
	parm= RNA_def_enum(func, "type", object_type_items, 0, "Type", "Type of Object.");
	RNA_def_property_flag(parm, PROP_REQUIRED);
	parm= RNA_def_string(func, "name", "Object", 0, "", "New name for the datablock.");
	RNA_def_property_flag(parm, PROP_REQUIRED);
	parm= RNA_def_pointer(func, "object", "Object", "", "New object.");
	RNA_def_function_return(func, parm);

	func= RNA_def_function(srna, "add_mesh", "rna_Main_add_mesh");
	RNA_def_function_ui_description(func, "Add a new mesh.");
	parm= RNA_def_string(func, "name", "Mesh", 0, "", "New name for the datablock.");
	RNA_def_property_flag(parm, PROP_REQUIRED);
	parm= RNA_def_pointer(func, "mesh", "Mesh", "", "New mesh.");
	RNA_def_function_return(func, parm);

	func= RNA_def_function(srna, "remove_mesh", "rna_Main_remove_mesh");
	RNA_def_function_flag(func, FUNC_USE_REPORTS);
	RNA_def_function_ui_description(func, "Remove a mesh if it has zero users.");
	parm= RNA_def_pointer(func, "mesh", "Mesh", "", "Mesh to remove.");
	RNA_def_property_flag(parm, PROP_REQUIRED);

}

#endif


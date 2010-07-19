/**
 * $Id: rna_mesh_api.c 21283 2009-07-01 12:19:00Z blendix $
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

#include <stdlib.h>
#include <stdio.h>

#include "RNA_define.h"

#include "BLO_sys_types.h"

#include "ED_mesh.h"

#ifdef RNA_RUNTIME

static void rna_Mesh_uv_texture_add(struct Mesh *me, struct bContext *C)
{
	ED_mesh_uv_texture_add(C, NULL, NULL, me);
}

static void rna_Mesh_vertex_color_add(struct Mesh *me, struct bContext *C)
{
	ED_mesh_color_add(C, NULL, NULL, me);
}

#else

void RNA_api_mesh(StructRNA *srna)
{
	FunctionRNA *func;
	PropertyRNA *parm;

	func= RNA_def_function(srna, "transform", "ED_mesh_transform");
	RNA_def_function_ui_description(func, "Transform mesh vertices by a matrix.");
	parm= RNA_def_float_matrix(func, "matrix", 4, 4, NULL, 0.0f, 0.0f, "", "Matrix.", 0.0f, 0.0f);
	RNA_def_property_flag(parm, PROP_REQUIRED);

	func= RNA_def_function(srna, "add_geometry", "ED_mesh_geometry_add");
	RNA_def_function_flag(func, FUNC_USE_REPORTS);
	parm= RNA_def_int(func, "verts", 0, 0, INT_MAX, "Number", "Number of vertices to add.", 0, INT_MAX);
	RNA_def_property_flag(parm, PROP_REQUIRED);
	parm= RNA_def_int(func, "edges", 0, 0, INT_MAX, "Number", "Number of edges to add.", 0, INT_MAX);
	RNA_def_property_flag(parm, PROP_REQUIRED);
	parm= RNA_def_int(func, "faces", 0, 0, INT_MAX, "Number", "Number of faces to add.", 0, INT_MAX);
	RNA_def_property_flag(parm, PROP_REQUIRED);

	func= RNA_def_function(srna, "add_uv_texture", "rna_Mesh_uv_texture_add");
	RNA_def_function_flag(func, FUNC_USE_CONTEXT);
	RNA_def_function_ui_description(func, "Add a UV texture layer to Mesh.");

	func= RNA_def_function(srna, "add_vertex_color", "rna_Mesh_vertex_color_add");
	RNA_def_function_flag(func, FUNC_USE_CONTEXT);
	RNA_def_function_ui_description(func, "Add a vertex color layer to Mesh.");

	func= RNA_def_function(srna, "calc_normals", "ED_mesh_calc_normals");
	RNA_def_function_ui_description(func, "Calculate vertex normals.");

	func= RNA_def_function(srna, "update", "ED_mesh_update");
	RNA_def_boolean(func, "calc_edges", 0, "Calculate Edges", "Force recalculation of edges.");
	RNA_def_function_flag(func, FUNC_USE_CONTEXT);

	func= RNA_def_function(srna, "add_material", "ED_mesh_material_add");
	RNA_def_function_ui_description(func, "Add a new material to Mesh.");
	parm= RNA_def_pointer(func, "material", "Material", "", "Material to add.");
	RNA_def_property_flag(parm, PROP_REQUIRED);


}

#endif


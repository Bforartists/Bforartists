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
#include <string.h>
#include <time.h>

#include "RNA_define.h"
#include "RNA_types.h"

#include "DNA_object_types.h"

#ifdef RNA_RUNTIME

#include "BKE_customdata.h"
#include "BKE_DerivedMesh.h"
#include "BKE_anim.h"
#include "BKE_report.h"
#include "BKE_depsgraph.h"

#include "DNA_mesh_types.h"
#include "DNA_scene_types.h"
#include "DNA_meshdata_types.h"

#include "BLI_arithb.h"

#include "BLO_sys_types.h" /* needed for intptr_t used in ED_mesh.h */

#include "ED_mesh.h"

/* copied from init_render_mesh (render code) */
static Mesh *create_mesh(Object *ob, bContext *C, ReportList *reports, int render_mesh)
{
	/* CustomDataMask mask = CD_MASK_BAREMESH|CD_MASK_MTFACE|CD_MASK_MCOL; */
	CustomDataMask mask = CD_MASK_MESH; /* this seems more suitable, exporter,
										   for example, needs CD_MASK_MDEFORMVERT */
	DerivedMesh *dm;
	Mesh *me;
	Scene *sce;

	sce= CTX_data_scene(C);
	
	/* TODO: other types */
	if(ob->type != OB_MESH) {
		BKE_report(reports, RPT_ERROR, "Object should be of type MESH.");
		return NULL;
	}
	
	dm= render_mesh ? mesh_create_derived_render(sce, ob, mask) : mesh_create_derived_view(sce, ob, mask);

	if(!dm) {
		/* TODO: report */
		return NULL;
	}

	me= add_mesh("tmp_render_mesh");
	me->id.us--; /* we don't assign it to anything */
	DM_to_mesh(dm, me);
	dm->release(dm);

	return me;
}

static Mesh *rna_Object_create_render_mesh(Object *ob, bContext *C, ReportList *reports)
{
	return create_mesh(ob, C, reports, 1);
}

static Mesh *rna_Object_create_preview_mesh(Object *ob, bContext *C, ReportList *reports)
{
	return create_mesh(ob, C, reports, 0);
}

/* When no longer needed, duplilist should be freed with Object.free_duplilist */
static void rna_Object_create_duplilist(Object *ob, bContext *C, ReportList *reports)
{
	if (!(ob->transflag & OB_DUPLI)) {
		BKE_report(reports, RPT_ERROR, "Object does not have duplis.");
		return;
	}

	/* free duplilist if a user forgets to */
	if (ob->duplilist) {
		BKE_reportf(reports, RPT_WARNING, "%s.dupli_list has not been freed.", RNA_struct_identifier(&RNA_Object));

		free_object_duplilist(ob->duplilist);
		ob->duplilist= NULL;
	}

	ob->duplilist= object_duplilist(CTX_data_scene(C), ob);

	/* ob->duplilist should now be freed with Object.free_duplilist */
}

static void rna_Object_free_duplilist(Object *ob, ReportList *reports)
{
	if (ob->duplilist) {
		free_object_duplilist(ob->duplilist);
		ob->duplilist= NULL;
	}
}

static void rna_Object_convert_to_triface(Object *ob, bContext *C, ReportList *reports, Scene *sce)
{
	Mesh *me;
	int ob_editing = CTX_data_edit_object(C) == ob;

	if (ob->type != OB_MESH) {
		BKE_report(reports, RPT_ERROR, "Object should be of type MESH.");
		return;
	}

	me= (Mesh*)ob->data;

	if (!ob_editing)
		make_editMesh(sce, ob);

	/* select all */
	EM_set_flag_all(me->edit_mesh, SELECT);

	convert_to_triface(me->edit_mesh, 0);

	load_editMesh(sce, ob);

	if (!ob_editing)
		free_editMesh(me->edit_mesh);

	DAG_object_flush_update(sce, ob, OB_RECALC_DATA);
}


#else

void RNA_api_object(StructRNA *srna)
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

	func= RNA_def_function(srna, "create_render_mesh", "rna_Object_create_render_mesh");
	RNA_def_function_ui_description(func, "Create a Mesh datablock with all modifiers applied for rendering.");
	RNA_def_function_flag(func, FUNC_USE_CONTEXT|FUNC_USE_REPORTS);
	parm= RNA_def_pointer(func, "mesh", "Mesh", "", "Mesh created from object, remove it if it is only used for export.");
	RNA_def_function_return(func, parm);

	func= RNA_def_function(srna, "create_preview_mesh", "rna_Object_create_preview_mesh");
	RNA_def_function_ui_description(func, "Create a Mesh datablock with all modifiers applied for preview.");
	RNA_def_function_flag(func, FUNC_USE_CONTEXT|FUNC_USE_REPORTS);
	parm= RNA_def_pointer(func, "mesh", "Mesh", "", "Mesh created from object, remove it if it is only used for export.");
	RNA_def_function_return(func, parm);
	
	func= RNA_def_function(srna, "create_dupli_list", "rna_Object_create_duplilist");
	RNA_def_function_ui_description(func, "Create a list of dupli objects for this object, needs to be freed manually with free_dupli_list.");
	RNA_def_function_flag(func, FUNC_USE_CONTEXT|FUNC_USE_REPORTS);

	func= RNA_def_function(srna, "free_dupli_list", "rna_Object_free_duplilist");
	RNA_def_function_ui_description(func, "Free the list of dupli objects.");
	RNA_def_function_flag(func, FUNC_USE_REPORTS);

	func= RNA_def_function(srna, "convert_to_triface", "rna_Object_convert_to_triface");
	RNA_def_function_ui_description(func, "Convert all mesh faces to triangles.");
	RNA_def_function_flag(func, FUNC_USE_CONTEXT|FUNC_USE_REPORTS);
	parm= RNA_def_pointer(func, "scene", "Scene", "", "Scene where the object belongs.");
	RNA_def_property_flag(parm, PROP_REQUIRED);
}

#endif


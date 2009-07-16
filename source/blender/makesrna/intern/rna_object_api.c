/**
 * $Id: rna_object_api.c 21094 2009-06-23 00:09:26Z gsrb3d $
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

#ifdef RNA_RUNTIME

#include "BKE_customdata.h"
#include "BKE_DerivedMesh.h"

#include "DNA_mesh_types.h"
#include "DNA_scene_types.h"

/* copied from init_render_mesh (render code) */
Mesh *rna_Object_create_render_mesh(Object *ob, Scene *scene)
{
	CustomDataMask mask = CD_MASK_BAREMESH|CD_MASK_MTFACE|CD_MASK_MCOL;
	DerivedMesh *dm;
	Mesh *me;
	
	/* TODO: other types */
	if(ob->type != OB_MESH)
		return NULL;
	
	dm= mesh_create_derived_render(scene, ob, mask);

	if(!dm)
		return NULL;

	me= add_mesh("tmp_render_mesh");
	me->id.us--; /* we don't assign it to anything */
	DM_to_mesh(dm, me);
	dm->release(dm);

	return me;
}

#else

void RNA_api_object(StructRNA *srna)
{
	FunctionRNA *func;
	PropertyRNA *prop;

	func= RNA_def_function(srna, "create_render_mesh", "rna_Object_create_render_mesh");
	RNA_def_function_ui_description(func, "Create a Mesh datablock with all modifiers applied.");
	prop= RNA_def_pointer(func, "scene", "Scene", "", "");
	RNA_def_property_flag(prop, PROP_REQUIRED);
	prop= RNA_def_pointer(func, "mesh", "Mesh", "", "Mesh created from object, remove it if it is only used for export.");
	RNA_def_function_return(func, prop);
}

#endif


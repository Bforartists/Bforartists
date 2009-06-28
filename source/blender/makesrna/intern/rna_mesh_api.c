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

#ifdef RNA_RUNTIME

#include "BKE_customdata.h"
#include "BKE_DerivedMesh.h"
#include "BKE_mesh.h"

#include "BLI_arithb.h"

#include "DNA_mesh_types.h"
#include "DNA_scene_types.h"

/*
void rna_Mesh_copy(Mesh *me, Mesh *from)
{
	copy_mesh_data(me, from);
}

void rna_Mesh_copy_applied(Mesh *me, Scene *sce, Object *ob)
{
	DerivedMesh *dm= mesh_create_derived_view(sce, ob, CD_MASK_MESH);
	DM_to_mesh(dm, me);
	dm->release(dm);
}
*/

void rna_Mesh_transform(Mesh *me, float *mat)
{
	/* TODO: old API transform had recalc_normals option */
	int i;
	MVert *mvert= me->mvert;

	for(i= 0; i < me->totvert; i++, mvert++) {
		Mat4MulVecfl(mat, mvert->co);
	}
}

Mesh *rna_Mesh_create_copy(Mesh *me)
{
	Mesh *ret= copy_mesh(me);
	ret->id.us--;
	
	return ret;
}

#if 0
/* extern struct EditVert *addvertlist(EditMesh *em, float *vec, struct EditVert *example); */

static void rna_Mesh_verts_add(PointerRNA *ptr, PointerRNA *ptr_item)
{
	//Mesh *me= (Mesh*)ptr->data;

	/*
	// XXX if item is not MVert we fail silently
	if (item->type == RNA_MeshVertex)
		return;

	// XXX this must be slow...
	EditMesh *em= BKE_mesh_get_editmesh(me);

	MVert *v = (MVert*)ptr_item->ptr->data;
	addvertlist(em, v->co, NULL);

	BKE_mesh_end_editmesh(me, em);
	*/
}
#endif

#else

void RNA_api_mesh(StructRNA *srna)
{
	FunctionRNA *func;
	PropertyRNA *parm;

	func= RNA_def_function(srna, "transform", "rna_Mesh_transform");
	RNA_def_function_ui_description(func, "Transform mesh vertices by a matrix.");
	parm= RNA_def_float_matrix(func, "matrix", 16, NULL, 0.0f, 0.0f, "", "Matrix.", 0.0f, 0.0f);
	RNA_def_property_flag(parm, PROP_REQUIRED);

	func= RNA_def_function(srna, "create_copy", "rna_Mesh_create_copy");
	RNA_def_function_ui_description(func, "Create a copy of this Mesh datablock.");
	parm= RNA_def_pointer(func, "mesh", "Mesh", "", "Mesh, remove it if it is only used for export.");
	RNA_def_function_return(func, parm);

	/*
	func= RNA_def_function(srna, "add_geom", "rna_Mesh_add_geom");
	RNA_def_function_ui_description(func, "Add geometry data to mesh.");
	prop= RNA_def_collection(func, "verts", "?", "", "Vertices.");
	RNA_def_property_flag(prop, PROP_REQUIRED);
	prop= RNA_def_collection(func, "faces", "?", "", "Faces.");
	RNA_def_property_flag(prop, PROP_REQUIRED);
	*/
}

#endif


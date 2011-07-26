/*
 * $Id$
 *
 * ***** BEGIN GPL LICENSE BLOCK *****
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version. The Blender
 * Foundation also sells licenses for use in proprietary software under
 * the Blender License.  See http://www.blender.org/BL/ for information
 * about this.
 *
 * This program is distributed in the hope that it will be useful;
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software Foundation;
 * Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
 *
 * The Original Code is Copyright (C) 2005 Blender Foundation.
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): Ben Batt
 *
 * ***** END GPL LICENSE BLOCK *****
 */

/** \file blender/modifiers/intern/MOD_util.c
 *  \ingroup modifiers
 */


#include <string.h>

#include "DNA_lattice_types.h"
#include "DNA_modifier_types.h"
#include "DNA_object_types.h"
#include "DNA_curve_types.h"
#include "DNA_meshdata_types.h"

#include "BLI_utildefines.h"
#include "BLI_math_vector.h"
#include "BLI_math_matrix.h"

#include "BKE_cdderivedmesh.h"
#include "BKE_deform.h"
#include "BKE_lattice.h"
#include "BKE_mesh.h"
#include "BKE_displist.h"

#include "BKE_modifier.h"

#include "MOD_util.h"
#include "MOD_modifiertypes.h"

#include "MEM_guardedalloc.h"

#include "RE_shader_ext.h"

void get_texture_value(Tex *texture, float *tex_co, TexResult *texres)
{
	int result_type;

	/* no node textures for now */
	result_type = multitex_ext_safe(texture, tex_co, texres);

	/* if the texture gave an RGB value, we assume it didn't give a valid
	* intensity, so calculate one (formula from do_material_tex).
	* if the texture didn't give an RGB value, copy the intensity across
	*/
	if(result_type & TEX_RGB)
		texres->tin = (0.35f * texres->tr + 0.45f * texres->tg
				+ 0.2f * texres->tb);
	else
		texres->tr = texres->tg = texres->tb = texres->tin;
}

void get_texture_coords(MappingInfoModifierData *dmd, Object *ob,
                        DerivedMesh *dm,
                        float (*co)[3], float (*texco)[3],
                        int numVerts)
{
	int i;
	int texmapping = dmd->texmapping;
	float mapob_imat[4][4];

	if(texmapping == MOD_DISP_MAP_OBJECT) {
		if(dmd->map_object)
			invert_m4_m4(mapob_imat, dmd->map_object->obmat);
		else /* if there is no map object, default to local */
			texmapping = MOD_DISP_MAP_LOCAL;
	}

	/* UVs need special handling, since they come from faces */
	if(texmapping == MOD_DISP_MAP_UV) {
		if(CustomData_has_layer(&dm->faceData, CD_MTFACE)) {
			MFace *mface = dm->getTessFaceArray(dm);
			MFace *mf;
			char *done = MEM_callocN(sizeof(*done) * numVerts,
			                         "get_texture_coords done");
			int numFaces = dm->getNumTessFaces(dm);
			char uvname[32];
			MTFace *tf;

			validate_layer_name(&dm->faceData, CD_MTFACE, dmd->uvlayer_name, uvname);
			tf = CustomData_get_layer_named(&dm->faceData, CD_MTFACE, uvname);

			/* verts are given the UV from the first face that uses them */
			for(i = 0, mf = mface; i < numFaces; ++i, ++mf, ++tf) {
				if(!done[mf->v1]) {
					texco[mf->v1][0] = tf->uv[0][0];
					texco[mf->v1][1] = tf->uv[0][1];
					texco[mf->v1][2] = 0;
					done[mf->v1] = 1;
				}
				if(!done[mf->v2]) {
					texco[mf->v2][0] = tf->uv[1][0];
					texco[mf->v2][1] = tf->uv[1][1];
					texco[mf->v2][2] = 0;
					done[mf->v2] = 1;
				}
				if(!done[mf->v3]) {
					texco[mf->v3][0] = tf->uv[2][0];
					texco[mf->v3][1] = tf->uv[2][1];
					texco[mf->v3][2] = 0;
					done[mf->v3] = 1;
				}
				if(!done[mf->v4]) {
					texco[mf->v4][0] = tf->uv[3][0];
					texco[mf->v4][1] = tf->uv[3][1];
					texco[mf->v4][2] = 0;
					done[mf->v4] = 1;
				}
			}

			/* remap UVs from [0, 1] to [-1, 1] */
			for(i = 0; i < numVerts; ++i) {
				texco[i][0] = texco[i][0] * 2 - 1;
				texco[i][1] = texco[i][1] * 2 - 1;
			}

			MEM_freeN(done);
			return;
		} else /* if there are no UVs, default to local */
			texmapping = MOD_DISP_MAP_LOCAL;
	}

	for(i = 0; i < numVerts; ++i, ++co, ++texco) {
		switch(texmapping) {
		case MOD_DISP_MAP_LOCAL:
			copy_v3_v3(*texco, *co);
			break;
		case MOD_DISP_MAP_GLOBAL:
			mul_v3_m4v3(*texco, ob->obmat, *co);
			break;
		case MOD_DISP_MAP_OBJECT:
			mul_v3_m4v3(*texco, ob->obmat, *co);
			mul_m4_v3(mapob_imat, *texco);
			break;
		}
	}
}

void modifier_vgroup_cache(ModifierData *md, float (*vertexCos)[3])
{
	while((md=md->next) && md->type==eModifierType_Armature) {
		ArmatureModifierData *amd = (ArmatureModifierData*) md;
		if(amd->multi && amd->prevCos==NULL)
			amd->prevCos= MEM_dupallocN(vertexCos);
		else
			break;
	}
	/* lattice/mesh modifier too */
}

void validate_layer_name(const CustomData *data, int type, char *name, char *outname)
{
	int index = -1;

	/* if a layer name was given, try to find that layer */
	if(name[0])
		index = CustomData_get_named_layer_index(data, type, name);

	if(index < 0) {
		/* either no layer was specified, or the layer we want has been
		* deleted, so assign the active layer to name
		*/
		index = CustomData_get_active_layer_index(data, type);
		strcpy(outname, data->layers[index].name);
	}
	else
		strcpy(outname, name);
}

/* returns a cdderivedmesh if dm == NULL or is another type of derivedmesh */
DerivedMesh *get_cddm(Object *ob, struct BMEditMesh *em, DerivedMesh *dm, float (*vertexCos)[3])
{
	if(dm && dm->type == DM_TYPE_CDDM)
		return dm;

	if(!dm) {
		dm= get_dm(ob, em, dm, vertexCos, 0);
	}
	else {
		dm= CDDM_copy(dm, 0);
		CDDM_apply_vert_coords(dm, vertexCos);
	}

	if(dm)
		CDDM_calc_normals(dm);
	
	return dm;
}

/* returns a derived mesh if dm == NULL, for deforming modifiers that need it */
DerivedMesh *get_dm(Object *ob, struct BMEditMesh *em, DerivedMesh *dm, float (*vertexCos)[3], int orco)
{
	if(dm)
		return dm;

	if(ob->type==OB_MESH) {
		if(em) dm= CDDM_from_BMEditMesh(em, ob->data, 0);
		else dm = CDDM_from_mesh((struct Mesh *)(ob->data), ob);

		if(vertexCos) {
			CDDM_apply_vert_coords(dm, vertexCos);
			//CDDM_calc_normals(dm);
		}
		
		if(orco)
			DM_add_vert_layer(dm, CD_ORCO, CD_ASSIGN, get_mesh_orco_verts(ob));
	}
	else if(ELEM3(ob->type,OB_FONT,OB_CURVE,OB_SURF)) {
		dm= CDDM_from_curve(ob);
	}

	return dm;
}

void modifier_get_vgroup(Object *ob, DerivedMesh *dm, const char *name, MDeformVert **dvert, int *defgrp_index)
{
	*defgrp_index = defgroup_name_index(ob, name);
	*dvert = NULL;

	if(*defgrp_index >= 0) {
		if(ob->type == OB_LATTICE)
			*dvert = lattice_get_deform_verts(ob);
		else if(dm)
			*dvert = dm->getVertDataArray(dm, CD_MDEFORMVERT);
	}
}

/* only called by BKE_modifier.h/modifier.c */
void modifier_type_init(ModifierTypeInfo *types[])
{
#define INIT_TYPE(typeName) (types[eModifierType_##typeName] = &modifierType_##typeName)
	INIT_TYPE(None);
	INIT_TYPE(Curve);
	INIT_TYPE(Lattice);
	INIT_TYPE(Subsurf);
	INIT_TYPE(Build);
	INIT_TYPE(Array);
	INIT_TYPE(Mirror);
	INIT_TYPE(EdgeSplit);
	INIT_TYPE(Bevel);
	INIT_TYPE(Displace);
	INIT_TYPE(UVProject);
	INIT_TYPE(Decimate);
	INIT_TYPE(Smooth);
	INIT_TYPE(Cast);
	INIT_TYPE(Wave);
	INIT_TYPE(Armature);
	INIT_TYPE(Hook);
	INIT_TYPE(Softbody);
	INIT_TYPE(Cloth);
	INIT_TYPE(Collision);
	INIT_TYPE(Boolean);
	INIT_TYPE(MeshDeform);
	INIT_TYPE(ParticleSystem);
	INIT_TYPE(ParticleInstance);
	INIT_TYPE(Explode);
	INIT_TYPE(Shrinkwrap);
	INIT_TYPE(Fluidsim);
	INIT_TYPE(Mask);
	INIT_TYPE(SimpleDeform);
	INIT_TYPE(Multires);
	INIT_TYPE(Surface);
	INIT_TYPE(Smoke);
	INIT_TYPE(ShapeKey);
	INIT_TYPE(Solidify);
	INIT_TYPE(Screw);
	INIT_TYPE(Warp);
	INIT_TYPE(NgonInterp);
#undef INIT_TYPE
}

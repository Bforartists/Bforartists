/*
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
* along with this program; if not, write to the Free Software  Foundation,
* Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
*
* The Original Code is Copyright (C) 2011 by Bastien Montagne.
* All rights reserved.
*
* Contributor(s): None yet.
*
* ***** END GPL LICENSE BLOCK *****
*
*/

/*
 * XXX I’d like to make modified weights visible in WeightPaint mode,
 *     but couldn’t figure a way to do this…
 *     Maybe this will need changes in mesh_calc_modifiers (DerivedMesh.c)?
 *     Or the WeightPaint mode code itself?
 */

#include "BLI_utildefines.h"
#include "BLI_math.h"
#include "BLI_string.h"

#include "DNA_color_types.h"      /* CurveMapping. */
#include "DNA_mesh_types.h"
#include "DNA_meshdata_types.h"
#include "DNA_modifier_types.h"
#include "DNA_object_types.h"

#include "BKE_cdderivedmesh.h"
#include "BKE_colortools.h"       /* CurveMapping. */
#include "BKE_deform.h"
#include "BKE_mesh.h"
#include "BKE_modifier.h"
#include "BKE_texture.h"          /* Texture masking. */

#include "depsgraph_private.h"
#include "MEM_guardedalloc.h"
#include "MOD_util.h"
#include "MOD_weightvg_util.h"

/**************************************
 * Modifiers functions.               *
 **************************************/
static void initData(ModifierData *md)
{
	WeightVGEditModifierData *wmd = (WeightVGEditModifierData*) md;
	wmd->edit_flags             = MOD_WVG_EDIT_CLAMP;
	wmd->default_weight         = 0.0f;

	wmd->map_org_min            = 0.0f;
	wmd->map_org_max            = 1.0f;
	wmd->map_new_min            = 0.0f;
	wmd->map_new_max            = 1.0f;
	wmd->cmap_curve             = curvemapping_add(1, 0.0, 0.0, 1.0, 1.0);
	curvemapping_initialize(wmd->cmap_curve);

	wmd->clamp_weight_min       = 0.0f;
	wmd->clamp_weight_max       = 1.0f;

	wmd->add_threshold          = 0.01f;
	wmd->rem_threshold          = 0.01f;

	wmd->mask_constant          = 1.0f;
	wmd->mask_tex_use_channel   = MOD_WVG_MASK_TEX_USE_INT; /* Use intensity by default. */
	wmd->mask_tex_mapping       = MOD_DISP_MAP_LOCAL;
}

static void freeData(ModifierData *md)
{
	WeightVGEditModifierData *wmd = (WeightVGEditModifierData*) md;
	curvemapping_free(wmd->cmap_curve);
}

static void copyData(ModifierData *md, ModifierData *target)
{
	WeightVGEditModifierData *wmd  = (WeightVGEditModifierData*) md;
	WeightVGEditModifierData *twmd = (WeightVGEditModifierData*) target;

	BLI_strncpy(twmd->defgrp_name, wmd->defgrp_name, sizeof(twmd->defgrp_name));

	twmd->edit_flags             = wmd->edit_flags;
	twmd->default_weight         = wmd->default_weight;

	twmd->map_org_min            = wmd->map_org_min;
	twmd->map_org_max            = wmd->map_org_max;
	twmd->map_new_min            = wmd->map_new_min;
	twmd->map_new_max            = wmd->map_new_max;
	twmd->cmap_curve             = curvemapping_copy(wmd->cmap_curve);

	twmd->clamp_weight_min       = wmd->clamp_weight_min;
	twmd->clamp_weight_max       = wmd->clamp_weight_max;

	twmd->add_threshold          = wmd->add_threshold;
	twmd->rem_threshold          = wmd->rem_threshold;

	twmd->mask_constant          = wmd->mask_constant;
	BLI_strncpy(twmd->mask_defgrp_name, wmd->mask_defgrp_name, sizeof(twmd->mask_defgrp_name));
	twmd->mask_texture           = wmd->mask_texture;
	twmd->mask_tex_use_channel   = wmd->mask_tex_use_channel;
	twmd->mask_tex_mapping       = wmd->mask_tex_mapping;
	twmd->mask_tex_map_obj       = wmd->mask_tex_map_obj;
	BLI_strncpy(twmd->mask_tex_uvlayer_name, wmd->mask_tex_uvlayer_name,
	            sizeof(twmd->mask_tex_uvlayer_name));
}

static CustomDataMask requiredDataMask(Object *UNUSED(ob), ModifierData *md)
{
	WeightVGEditModifierData *wmd = (WeightVGEditModifierData*) md;
	CustomDataMask dataMask = 0;

	/* We need vertex groups! */
	dataMask |= CD_MASK_MDEFORMVERT;

	/* Ask for UV coordinates if we need them. */
	if(wmd->mask_tex_mapping == MOD_DISP_MAP_UV)
		dataMask |= CD_MASK_MTFACE;

	return dataMask;
}

static int dependsOnTime(ModifierData *md)
{
	WeightVGEditModifierData *wmd = (WeightVGEditModifierData*) md;

	if(wmd->mask_texture)
		return BKE_texture_dependsOnTime(wmd->mask_texture);
	return 0;
}

static void foreachObjectLink(ModifierData *md, Object *ob,
                              void (*walk)(void *userData, Object *ob, Object **obpoin),
                              void *userData)
{
	WeightVGEditModifierData *wmd = (WeightVGEditModifierData*) md;
	walk(userData, ob, &wmd->mask_tex_map_obj);
}

static void foreachIDLink(ModifierData *md, Object *ob, IDWalkFunc walk, void *userData)
{
	WeightVGEditModifierData *wmd = (WeightVGEditModifierData*) md;

	walk(userData, ob, (ID **)&wmd->mask_texture);

	foreachObjectLink(md, ob, (ObjectWalkFunc)walk, userData);
}

static void updateDepgraph(ModifierData *md, DagForest *forest, struct Scene *UNUSED(scene),
                           Object *UNUSED(ob), DagNode *obNode)
{
	WeightVGEditModifierData *wmd = (WeightVGEditModifierData*) md;
	DagNode *curNode;

	if(wmd->mask_tex_map_obj && wmd->mask_tex_mapping == MOD_DISP_MAP_OBJECT) {
		curNode = dag_get_node(forest, wmd->mask_tex_map_obj);

		dag_add_relation(forest, curNode, obNode, DAG_RL_DATA_DATA|DAG_RL_OB_DATA,
		                 "WeightVGEdit Modifier");
	}

	if(wmd->mask_tex_mapping == MOD_DISP_MAP_GLOBAL)
		dag_add_relation(forest, obNode, obNode, DAG_RL_DATA_DATA|DAG_RL_OB_DATA,
		                 "WeightVGEdit Modifier");
}

static int isDisabled(ModifierData *md, int UNUSED(useRenderParams))
{
	WeightVGEditModifierData *wmd = (WeightVGEditModifierData*) md;
	/* If no vertex group, bypass. */
	return (wmd->defgrp_name == NULL);
}

static DerivedMesh *applyModifier(ModifierData *md, Object *ob, DerivedMesh *derivedData,
                                  int UNUSED(useRenderParams), int UNUSED(isFinalCalc))
{
	WeightVGEditModifierData *wmd = (WeightVGEditModifierData*) md;
	DerivedMesh *dm = derivedData, *ret = NULL;
	Mesh *ob_m = NULL;
	MDeformVert *dvert = NULL;
	float *org_w = NULL; /* Array original weights. */
	float *new_w = NULL; /* Array new weights. */
	int numVerts;
	int defgrp_idx;
	int i;
	char rel_ret = 0; /* Boolean, whether we have to release ret dm or not, when not using it! */
	float *mapf = NULL; /* Cache for mapping factors. */
	/* Flags. */
	char do_map   = wmd->edit_flags & MOD_WVG_EDIT_MAP;
	char do_cmap  = wmd->edit_flags & MOD_WVG_EDIT_CMAP;
	char do_rev   = wmd->edit_flags & MOD_WVG_EDIT_REVERSE_WEIGHTS;
	char do_add   = wmd->edit_flags & MOD_WVG_EDIT_ADD2VG;
	char do_rem   = wmd->edit_flags & MOD_WVG_EDIT_REMFVG;
	char do_clamp = wmd->edit_flags & MOD_WVG_EDIT_CLAMP;

	/* Get number of verts. */
	numVerts = dm->getNumVerts(dm);

	/* Check if we can just return the original mesh.
	 * Must have verts and therefore verts assigned to vgroups to do anything useful!
	 */
	if ((numVerts == 0) || (ob->defbase.first == NULL))
		return dm;

	/* Get vgroup idx from its name. */
	defgrp_idx = defgroup_name_index(ob, wmd->defgrp_name);
	if (defgrp_idx < 0)
		return dm;

	/* XXX All this to avoid copying dm when not needed… However, it nearly doubles compute
	 *     time! See scene 5 of the WeighVG test file…
	 */
#if 0
	/* Get actual dverts (ie vertex group data). */
	dvert = dm->getVertDataArray(dm, CD_MDEFORMVERT);
	/* If no dverts, return unmodified data… */
	if (dvert == NULL)
		return dm;

	/* Get org mesh, only to test whether affected cdata layer has already been copied
	 * somewhere up in the modifiers stack.
	 */
	ob_m = get_mesh(ob);
	if (ob_m == NULL)
		return dm;

	/* Create a copy of our dmesh, only if our affected cdata layer is the same as org mesh. */
	if (dvert == CustomData_get_layer(&ob_m->vdata, CD_MDEFORMVERT)) {
		/* XXX Seems to create problems with weightpaint mode???
		 *     I’m missing something here, I guess…
		 */
//		DM_set_only_copy(dm, CD_MASK_MDEFORMVERT); /* Only copy defgroup layer. */
		ret = CDDM_copy(dm);
		dvert = ret->getVertDataArray(ret, CD_MDEFORMVERT);
		if (dvert == NULL) {
			ret->release(ret);
			return dm;
		}
		rel_ret = 1;
	}
	else
		ret = dm;
#else
	ret = CDDM_copy(dm);
	rel_ret = 1;
	dvert = ret->getVertDataArray(ret, CD_MDEFORMVERT);
	if (dvert == NULL) {
		if (rel_ret)
			ret->release(ret);
		return dm;
	}
#endif

	/* Get org weights, assuming 0.0 for vertices not in given vgroup. */
	org_w = MEM_mallocN(sizeof(float) * numVerts, "WeightVGEdit Modifier, org_w");
	new_w = MEM_mallocN(sizeof(float) * numVerts, "WeightVGEdit Modifier, org_w");
	for (i = 0; i < numVerts; i++) {
		int j;
		org_w[i] = new_w[i] = wmd->default_weight;
		for (j = 0; j < dvert[i].totweight; j++) {
			if(dvert[i].dw[j].def_nr == defgrp_idx) {
				org_w[i] = new_w[i] = dvert[i].dw[j].weight;
				break;
			}
		}
		/* Do mapping. */
		if (do_map) {
			/* This mapping is a simple func: a*in + b.
			 * with a = (out_min - out_max)/(in_min - in_max)
			 * and  b = out_max - a*in_max
			 * Note a and b are cached!
			 */
			if (mapf == NULL) {
				float denom = wmd->map_org_min - wmd->map_org_max;
				mapf = MEM_mallocN(sizeof(float) * 2, "WeightVGEdit, mapf");
				if (denom > 0.0 && denom < MOD_WVG_ZEROFLOOR)
					denom = MOD_WVG_ZEROFLOOR;
				else if (denom < 0.0 && denom > -MOD_WVG_ZEROFLOOR)
					denom = -MOD_WVG_ZEROFLOOR;
				mapf[0] = (wmd->map_new_min - wmd->map_new_max) / denom;
				mapf[1] = wmd->map_new_max - (mapf[0] * wmd->map_org_max);
			}
			new_w[i] = (mapf[0] * new_w[i]) + mapf[1];
		}
		if (do_cmap)
			new_w[i] = curvemapping_evaluateF(wmd->cmap_curve, 0, new_w[i]);
		if (do_rev)
			new_w[i] = (-1.0 * new_w[i]) + 1.0;
	}

	/* Do masking. */
	weightvg_do_mask(numVerts, NULL, org_w, new_w, ob, ret, wmd->mask_constant,
	                 wmd->mask_defgrp_name, wmd->mask_texture, wmd->mask_tex_use_channel,
	                 wmd->mask_tex_mapping, wmd->mask_tex_map_obj, wmd->mask_tex_uvlayer_name);

	/* Do clamping. */
	if (do_clamp) {
		for (i = 0; i < numVerts; i++)
			CLAMP(org_w[i], wmd->clamp_weight_min, wmd->clamp_weight_max);
	}

	/* Update/add/remove from vgroup. */
	weightvg_update_vg(dvert, defgrp_idx, numVerts, NULL, org_w, do_add, wmd->add_threshold,
	                   do_rem, wmd->rem_threshold);

	/* Freeing stuff. */
	if (org_w)
		MEM_freeN(org_w);
	if (new_w)
		MEM_freeN(new_w);
	if (mapf)
		MEM_freeN(mapf);

	/* Return the vgroup-modified mesh. */
	return ret;
}

static DerivedMesh *applyModifierEM(ModifierData *md, Object *ob,
                                    struct EditMesh *UNUSED(editData),
                                    DerivedMesh *derivedData)
{
	return applyModifier(md, ob, derivedData, 0, 1);
}


ModifierTypeInfo modifierType_WeightVGEdit = {
	/* name */              "WeightVGEdit",
	/* structName */        "WeightVGEditModifierData",
	/* structSize */        sizeof(WeightVGEditModifierData),
	/* type */              eModifierTypeType_Nonconstructive,
	/* flags */             eModifierTypeFlag_AcceptsMesh
	                       |eModifierTypeFlag_SupportsMapping
	                       |eModifierTypeFlag_SupportsEditmode,

	/* copyData */          copyData,
	/* deformVerts */       NULL,
	/* deformMatrices */    NULL,
	/* deformVertsEM */     NULL,
	/* deformMatricesEM */  NULL,
	/* applyModifier */     applyModifier,
	/* applyModifierEM */   applyModifierEM,
	/* initData */          initData,
	/* requiredDataMask */  requiredDataMask,
	/* freeData */          freeData,
	/* isDisabled */        isDisabled,
	/* updateDepgraph */    updateDepgraph,
	/* dependsOnTime */     dependsOnTime,
	/* dependsOnNormals */  NULL,
	/* foreachObjectLink */ foreachObjectLink,
	/* foreachIDLink */     foreachIDLink,
};


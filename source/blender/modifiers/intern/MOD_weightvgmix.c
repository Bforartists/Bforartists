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
 * XXX I'd like to make modified weights visible in WeightPaint mode,
 *     but couldn't figure a way to do this…
 *     Maybe this will need changes in mesh_calc_modifiers (DerivedMesh.c)?
 *     Or the WeightPaint mode code itself?
 */

#include "BLI_utildefines.h"
#include "BLI_math.h"
#include "BLI_string.h"

#include "DNA_mesh_types.h"
#include "DNA_meshdata_types.h"
#include "DNA_modifier_types.h"
#include "DNA_object_types.h"

#include "BKE_cdderivedmesh.h"
#include "BKE_deform.h"
#include "BKE_mesh.h"
#include "BKE_modifier.h"
#include "BKE_texture.h"          /* Texture masking. */

#include "depsgraph_private.h"
#include "MEM_guardedalloc.h"
#include "MOD_util.h"
#include "MOD_weightvg_util.h"


/**
 * This mixes the old weight with the new weight factor.
 */
static float mix_weight(float weight, float weight2, char mix_mode)
{
#if 0
	/*
	 * XXX Don't know why, but the switch version takes many CPU time,
	 *     and produces lag in realtime playback…
	 */
	switch (mix_mode)
	{
	case MOD_WVG_MIX_ADD:
		return (weight + weight2);
	case MOD_WVG_MIX_SUB:
		return (weight - weight2);
	case MOD_WVG_MIX_MUL:
		return (weight * weight2);
	case MOD_WVG_MIX_DIV:
		/* Avoid dividing by zero (or really small values). */
		if (0.0 <= weight2 < MOD_WVG_ZEROFLOOR)
			weight2 = MOD_WVG_ZEROFLOOR;
		else if (-MOD_WVG_ZEROFLOOR < weight2)
			weight2 = -MOD_WVG_ZEROFLOOR;
		return (weight / weight2);
	case MOD_WVG_MIX_DIF:
		return (weight < weight2 ? weight2 - weight : weight - weight2);
	case MOD_WVG_MIX_AVG:
		return (weight + weight2) / 2.0;
	case MOD_WVG_MIX_SET:
	default:
		return weight2;
	}
#endif
	if (mix_mode == MOD_WVG_MIX_SET)
		return weight2;
	else if (mix_mode == MOD_WVG_MIX_ADD)
		return (weight + weight2);
	else if (mix_mode == MOD_WVG_MIX_SUB)
		return (weight - weight2);
	else if (mix_mode == MOD_WVG_MIX_MUL)
		return (weight * weight2);
	else if (mix_mode == MOD_WVG_MIX_DIV) {
		/* Avoid dividing by zero (or really small values). */
		if (weight2 < 0.0 && weight2 > -MOD_WVG_ZEROFLOOR)
			weight2 = -MOD_WVG_ZEROFLOOR;
		else if (weight2 >= 0.0 && weight2 < MOD_WVG_ZEROFLOOR)
			weight2 = MOD_WVG_ZEROFLOOR;
		return (weight / weight2);
	}
	else if (mix_mode == MOD_WVG_MIX_DIF)
		return (weight < weight2 ? weight2 - weight : weight - weight2);
	else if (mix_mode == MOD_WVG_MIX_AVG)
		return (weight + weight2) / 2.0;
	else return weight2;
}

/**************************************
 * Modifiers functions.               *
 **************************************/
static void initData(ModifierData *md)
{
	WeightVGMixModifierData *wmd = (WeightVGMixModifierData*) md;

	wmd->default_weight         = 0.0;
	wmd->default_weight2        = 0.0;
	wmd->mix_mode               = MOD_WVG_MIX_SET;
	wmd->mix_set                = MOD_WVG_SET_INTER;

	wmd->mask_constant          = 1.0f;
	wmd->mask_tex_use_channel   = MOD_WVG_MASK_TEX_USE_INT; /* Use intensity by default. */
	wmd->mask_tex_mapping       = MOD_DISP_MAP_LOCAL;
}

static void copyData(ModifierData *md, ModifierData *target)
{
	WeightVGMixModifierData *wmd  = (WeightVGMixModifierData*) md;
	WeightVGMixModifierData *twmd = (WeightVGMixModifierData*) target;

	BLI_strncpy(twmd->defgrp_name, wmd->defgrp_name, sizeof(twmd->defgrp_name));
	BLI_strncpy(twmd->defgrp_name2, wmd->defgrp_name2, sizeof(twmd->defgrp_name2));
	twmd->default_weight         = wmd->default_weight;
	twmd->default_weight2        = wmd->default_weight2;
	twmd->mix_mode               = wmd->mix_mode;
	twmd->mix_set                = wmd->mix_set;

	twmd->mask_constant          = wmd->mask_constant;
	BLI_strncpy(twmd->mask_defgrp_name, wmd->mask_defgrp_name, sizeof(twmd->mask_defgrp_name));
	twmd->mask_texture           = wmd->mask_texture;
	twmd->mask_tex_use_channel   = wmd->mask_tex_use_channel;
	twmd->mask_tex_mapping       = wmd->mask_tex_mapping;
	twmd->mask_tex_map_obj       = wmd->mask_tex_map_obj;
	BLI_strncpy(twmd->mask_tex_uvlayer_name, wmd->mask_tex_uvlayer_name, sizeof(twmd->mask_tex_uvlayer_name));
}

static CustomDataMask requiredDataMask(Object *UNUSED(ob), ModifierData *md)
{
	WeightVGMixModifierData *wmd = (WeightVGMixModifierData*) md;
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
	WeightVGMixModifierData *wmd = (WeightVGMixModifierData*) md;

	if(wmd->mask_texture)
		return BKE_texture_dependsOnTime(wmd->mask_texture);
	return 0;
}

static void foreachObjectLink(ModifierData *md, Object *ob,
                              void (*walk)(void *userData, Object *ob, Object **obpoin),
                              void *userData)
{
	WeightVGMixModifierData *wmd = (WeightVGMixModifierData*) md;
	walk(userData, ob, &wmd->mask_tex_map_obj);
}

static void foreachIDLink(ModifierData *md, Object *ob, IDWalkFunc walk, void *userData)
{
	WeightVGMixModifierData *wmd = (WeightVGMixModifierData*) md;

	walk(userData, ob, (ID **)&wmd->mask_texture);

	foreachObjectLink(md, ob, (ObjectWalkFunc)walk, userData);
}

static void foreachTexLink(ModifierData *md, Object *ob, TexWalkFunc walk, void *userData)
{
	walk(userData, ob, md, "mask_texture");
}

static void updateDepgraph(ModifierData *md, DagForest *forest, struct Scene *UNUSED(scene),
                           Object *UNUSED(ob), DagNode *obNode)
{
	WeightVGMixModifierData *wmd = (WeightVGMixModifierData*) md;
	DagNode *curNode;

	if(wmd->mask_tex_map_obj && wmd->mask_tex_mapping == MOD_DISP_MAP_OBJECT) {
		curNode = dag_get_node(forest, wmd->mask_tex_map_obj);

		dag_add_relation(forest, curNode, obNode, DAG_RL_DATA_DATA|DAG_RL_OB_DATA,
		                 "WeightVGMix Modifier");
	}

	if(wmd->mask_tex_mapping == MOD_DISP_MAP_GLOBAL)
		dag_add_relation(forest, obNode, obNode, DAG_RL_DATA_DATA|DAG_RL_OB_DATA,
		                 "WeightVGMix Modifier");
}

static int isDisabled(ModifierData *md, int UNUSED(useRenderParams))
{
	WeightVGMixModifierData *wmd = (WeightVGMixModifierData*) md;
	/* If no vertex group, bypass. */
	return (wmd->defgrp_name == NULL);
}

static DerivedMesh *applyModifier(ModifierData *md, Object *ob, DerivedMesh *derivedData,
                                  int UNUSED(useRenderParams), int UNUSED(isFinalCalc))
{
	WeightVGMixModifierData *wmd = (WeightVGMixModifierData*) md;
	DerivedMesh *dm = derivedData, *ret = NULL;
#if 0
	Mesh *ob_m = NULL;
#endif
	MDeformVert *dvert = NULL;
	int numVerts;
	int defgrp_idx, defgrp_idx2 = -1;
	float *org_w = NULL;
	float *new_w = NULL;
	int *tidx, *indices = NULL;
	int numIdx = 0;
	int i, j;
	char rel_ret = 0; /* Boolean, whether we have to release ret dm or not, when not using it! */

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
	/* Get seconf vgroup idx from its name, if given. */
	if (wmd->defgrp_name2[0] != (char)0) {
		defgrp_idx2 = defgroup_name_index(ob, wmd->defgrp_name2);
		if (defgrp_idx2 < 0)
			return dm;
	}

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
		 *     I'm missing something here, I guess…
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

	/* Find out which vertices to work on. */
	tidx = MEM_mallocN(sizeof(int) * numVerts, "WeightVGMix Modifier, tidx");
	switch (wmd->mix_set) {
	case MOD_WVG_SET_ORG:
		/* All vertices in first vgroup. */
		for (i = 0; i < numVerts; i++) {
			for (j = 0; j < dvert[i].totweight; j++) {
				if(dvert[i].dw[j].def_nr == defgrp_idx) {
					tidx[numIdx++] = i;
					break;
				}
			}
		}
		break;
	case MOD_WVG_SET_NEW:
		/* All vertices in second vgroup. */
		for (i = 0; i < numVerts; i++) {
			for (j = 0; j < dvert[i].totweight; j++) {
				if(dvert[i].dw[j].def_nr == defgrp_idx2) {
					tidx[numIdx++] = i;
					break;
				}
			}
		}
		break;
	case MOD_WVG_SET_UNION:
		/* All vertices in one vgroup or the other. */
		for (i = 0; i < numVerts; i++) {
			for (j = 0; j < dvert[i].totweight; j++) {
				if(dvert[i].dw[j].def_nr == defgrp_idx || dvert[i].dw[j].def_nr == defgrp_idx2) {
					tidx[numIdx++] = i;
					break;
				}
			}
		}
		break;
	case MOD_WVG_SET_INTER:
		/* All vertices in both vgroups. */
		for (i = 0; i < numVerts; i++) {
			char idx1 = 0;
			char idx2 = 0;
			for (j = 0; j < dvert[i].totweight; j++) {
				if(dvert[i].dw[j].def_nr == defgrp_idx) {
					if (idx2) {
						tidx[numIdx++] = i;
						break;
					}
					else
						idx1 = 1;
				}
				else if(dvert[i].dw[j].def_nr == defgrp_idx2) {
					if (idx1) {
						tidx[numIdx++] = i;
						break;
					}
					else
						idx2 = 1;
				}
			}
		}
		break;
	case MOD_WVG_SET_ALL:
	default:
		/* Use all vertices, no need to do anything here. */
		break;
	}
	if (numIdx) {
		indices = MEM_mallocN(sizeof(int) * numIdx, "WeightVGMix Modifier, indices");
		memcpy(indices, tidx, sizeof(int) * numIdx);
	}
	else
		numIdx = numVerts;
	MEM_freeN(tidx);

	org_w = MEM_mallocN(sizeof(float) * numIdx, "WeightVGMix Modifier, org_w");
	new_w = MEM_mallocN(sizeof(float) * numIdx, "WeightVGMix Modifier, new_w");

	/* Mix weights. */
	for (i = 0; i < numIdx; i++) {
		float weight2 = 0.0;
		char w1 = 0;
		char w2 = 0;
		int idx = indices ? indices[i] : i;
		for (j = 0; j < dvert[idx].totweight; j++) {
			if(dvert[idx].dw[j].def_nr == defgrp_idx) {
				org_w[i] = dvert[idx].dw[j].weight;
				w1 = 1;
				if (w2)
					break;
			}
			else if(dvert[idx].dw[j].def_nr == defgrp_idx2) {
				weight2 = dvert[idx].dw[j].weight;
				w2 = 1;
				if (w1)
					break;
			}
		}
		if (w1 == 0)
			org_w[i] = wmd->default_weight;
		if (w2 == 0)
			weight2 = wmd->default_weight2;
		new_w[i] = mix_weight(org_w[i], weight2, wmd->mix_mode);
	}

	/* Do masking. */
	weightvg_do_mask(numIdx, indices, org_w, new_w, ob, ret, wmd->mask_constant,
	                 wmd->mask_defgrp_name, wmd->mask_texture, wmd->mask_tex_use_channel,
	                 wmd->mask_tex_mapping, wmd->mask_tex_map_obj, wmd->mask_tex_uvlayer_name);

	/* Update (add to) vgroup.
	 * XXX Depending on the MOD_WVG_SET_xxx option chosen, we might have to add vertices to vgroup.
	 */
	weightvg_update_vg(dvert, defgrp_idx, numIdx, indices, org_w, 1, -FLT_MAX, 0, 0.0f);

	/* Freeing stuff. */
	if (org_w)
		MEM_freeN(org_w);
	if (new_w)
		MEM_freeN(new_w);
	if (indices)
		MEM_freeN(indices);

	/* Return the vgroup-modified mesh. */
	return ret;
}

static DerivedMesh *applyModifierEM(ModifierData *md, Object *ob,
                                    struct EditMesh *UNUSED(editData),
                                    DerivedMesh *derivedData)
{
	return applyModifier(md, ob, derivedData, 0, 1);
}


ModifierTypeInfo modifierType_WeightVGMix = {
	/* name */              "WeightVGMix",
	/* structName */        "WeightVGMixModifierData",
	/* structSize */        sizeof(WeightVGMixModifierData),
	/* type */              eModifierTypeType_Nonconstructive,
	/* flags */             eModifierTypeFlag_AcceptsMesh
/*	                       |eModifierTypeFlag_SupportsMapping*/
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
	/* freeData */          NULL,
	/* isDisabled */        isDisabled,
	/* updateDepgraph */    updateDepgraph,
	/* dependsOnTime */     dependsOnTime,
	/* dependsOnNormals */  NULL,
	/* foreachObjectLink */ foreachObjectLink,
	/* foreachIDLink */     foreachIDLink,
	/* foreachTexLink */    foreachTexLink,
};

/*
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
 * The Original Code is Copyright (C) 2005 by the Blender Foundation.
 * All rights reserved.
 *
 * Contributor(s): Daniel Dunbar
 *                 Ton Roosendaal,
 *                 Ben Batt,
 *                 Brecht Van Lommel,
 *                 Campbell Barton
 *
 * ***** END GPL LICENSE BLOCK *****
 *
 */

/** \file blender/modifiers/intern/MOD_shrinkwrap.c
 *  \ingroup modifiers
 */


#include <string.h>

#include "DNA_object_types.h"

#include "BLI_math.h"
#include "BLI_utildefines.h"

#include "BKE_cdderivedmesh.h"
#include "BKE_library_query.h"
#include "BKE_modifier.h"
#include "BKE_shrinkwrap.h"

#include "MOD_util.h"

static bool dependsOnNormals(ModifierData *md);


static void initData(ModifierData *md)
{
	ShrinkwrapModifierData *smd = (ShrinkwrapModifierData *) md;
	smd->shrinkType = MOD_SHRINKWRAP_NEAREST_SURFACE;
	smd->shrinkOpts = MOD_SHRINKWRAP_PROJECT_ALLOW_POS_DIR;
	smd->keepDist   = 0.0f;

	smd->target     = NULL;
	smd->auxTarget  = NULL;
}

static CustomDataMask requiredDataMask(Object *UNUSED(ob), ModifierData *md)
{
	ShrinkwrapModifierData *smd = (ShrinkwrapModifierData *)md;
	CustomDataMask dataMask = 0;

	/* ask for vertexgroups if we need them */
	if (smd->vgroup_name[0])
		dataMask |= CD_MASK_MDEFORMVERT;

	if ((smd->shrinkType == MOD_SHRINKWRAP_PROJECT) &&
	    (smd->projAxis == MOD_SHRINKWRAP_PROJECT_OVER_NORMAL))
	{
		dataMask |= CD_MASK_MVERT;
	}

	return dataMask;
}

static bool isDisabled(ModifierData *md, int UNUSED(useRenderParams))
{
	ShrinkwrapModifierData *smd = (ShrinkwrapModifierData *) md;
	return !smd->target;
}


static void foreachObjectLink(ModifierData *md, Object *ob, ObjectWalkFunc walk, void *userData)
{
	ShrinkwrapModifierData *smd = (ShrinkwrapModifierData *) md;

	walk(userData, ob, &smd->target, IDWALK_CB_NOP);
	walk(userData, ob, &smd->auxTarget, IDWALK_CB_NOP);
}

static void deformVerts(ModifierData *md, const ModifierEvalContext *ctx,
                        DerivedMesh *derivedData,
                        float (*vertexCos)[3],
                        int numVerts)
{
	DerivedMesh *dm = derivedData;
	CustomDataMask dataMask = requiredDataMask(ctx->object, md);
	bool forRender = (ctx->flag & MOD_APPLY_RENDER) != 0;

	/* ensure we get a CDDM with applied vertex coords */
	if (dataMask) {
		dm = get_cddm(ctx->object, NULL, dm, vertexCos, dependsOnNormals(md));
	}

	shrinkwrapModifier_deform((ShrinkwrapModifierData *)md, ctx->object, dm, vertexCos, numVerts, forRender);

	if (dm != derivedData)
		dm->release(dm);
}

static void deformVertsEM(ModifierData *md, const ModifierEvalContext *ctx,
                          struct BMEditMesh *editData, DerivedMesh *derivedData,
                          float (*vertexCos)[3], int numVerts)
{
	DerivedMesh *dm = derivedData;
	CustomDataMask dataMask = requiredDataMask(ctx->object, md);

	/* ensure we get a CDDM with applied vertex coords */
	if (dataMask) {
		dm = get_cddm(ctx->object, editData, dm, vertexCos, dependsOnNormals(md));
	}

	shrinkwrapModifier_deform((ShrinkwrapModifierData *)md, ctx->object, dm, vertexCos, numVerts, false);

	if (dm != derivedData)
		dm->release(dm);
}

static void updateDepsgraph(ModifierData *md, const ModifierUpdateDepsgraphContext *ctx)
{
	ShrinkwrapModifierData *smd = (ShrinkwrapModifierData *)md;
	if (smd->target != NULL) {
		DEG_add_object_relation(ctx->node, smd->target, DEG_OB_COMP_TRANSFORM, "Shrinkwrap Modifier");
		DEG_add_object_relation(ctx->node, smd->target, DEG_OB_COMP_GEOMETRY, "Shrinkwrap Modifier");
	}
	if (smd->auxTarget != NULL) {
		DEG_add_object_relation(ctx->node, smd->auxTarget, DEG_OB_COMP_TRANSFORM, "Shrinkwrap Modifier");
		DEG_add_object_relation(ctx->node, smd->auxTarget, DEG_OB_COMP_GEOMETRY, "Shrinkwrap Modifier");
	}
}

static bool dependsOnNormals(ModifierData *md)
{
	ShrinkwrapModifierData *smd = (ShrinkwrapModifierData *)md;

	if (smd->target && smd->shrinkType == MOD_SHRINKWRAP_PROJECT)
		return (smd->projAxis == MOD_SHRINKWRAP_PROJECT_OVER_NORMAL);
	
	return false;
}

ModifierTypeInfo modifierType_Shrinkwrap = {
	/* name */              "Shrinkwrap",
	/* structName */        "ShrinkwrapModifierData",
	/* structSize */        sizeof(ShrinkwrapModifierData),
	/* type */              eModifierTypeType_OnlyDeform,
	/* flags */             eModifierTypeFlag_AcceptsMesh |
	                        eModifierTypeFlag_AcceptsCVs |
	                        eModifierTypeFlag_AcceptsLattice |
	                        eModifierTypeFlag_SupportsEditmode |
	                        eModifierTypeFlag_EnableInEditmode,

	/* copyData */          modifier_copyData_generic,

	/* deformVerts_DM */    deformVerts,
	/* deformMatrices_DM */ NULL,
	/* deformVertsEM_DM */  deformVertsEM,
	/* deformMatricesEM_DM*/NULL,
	/* applyModifier_DM */  NULL,
	/* applyModifierEM_DM */NULL,

	/* deformVerts */       NULL,
	/* deformMatrices */    NULL,
	/* deformVertsEM */     NULL,
	/* deformMatricesEM */  NULL,
	/* applyModifier */     NULL,
	/* applyModifierEM */   NULL,

	/* initData */          initData,
	/* requiredDataMask */  requiredDataMask,
	/* freeData */          NULL,
	/* isDisabled */        isDisabled,
	/* updateDepsgraph */   updateDepsgraph,
	/* dependsOnTime */     NULL,
	/* dependsOnNormals */  dependsOnNormals,
	/* foreachObjectLink */ foreachObjectLink,
	/* foreachIDLink */     NULL,
	/* foreachTexLink */    NULL,
};

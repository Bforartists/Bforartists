/*
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
 */

/** \file blender/modifiers/intern/MOD_curve.c
 *  \ingroup modifiers
 */

#include <string.h>

#include "DNA_scene_types.h"
#include "DNA_object_types.h"

#include "BLI_utildefines.h"

#include "BKE_cdderivedmesh.h"
#include "BKE_lattice.h"
#include "BKE_library_query.h"
#include "BKE_modifier.h"

#include "depsgraph_private.h"
#include "DEG_depsgraph_build.h"

#include "MOD_modifiertypes.h"

static void initData(ModifierData *md)
{
	CurveModifierData *cmd = (CurveModifierData *) md;

	cmd->defaxis = MOD_CURVE_POSX;
}

static CustomDataMask requiredDataMask(Object *UNUSED(ob), ModifierData *md)
{
	CurveModifierData *cmd = (CurveModifierData *)md;
	CustomDataMask dataMask = 0;

	/* ask for vertexgroups if we need them */
	if (cmd->name[0]) dataMask |= CD_MASK_MDEFORMVERT;

	return dataMask;
}

static bool isDisabled(ModifierData *md, int UNUSED(userRenderParams))
{
	CurveModifierData *cmd = (CurveModifierData *) md;

	return !cmd->object;
}

static void foreachObjectLink(
        ModifierData *md, Object *ob,
        ObjectWalkFunc walk, void *userData)
{
	CurveModifierData *cmd = (CurveModifierData *) md;

	walk(userData, ob, &cmd->object, IDWALK_CB_NOP);
}

static void updateDepgraph(ModifierData *md, const ModifierUpdateDepsgraphContext *ctx)
{
	CurveModifierData *cmd = (CurveModifierData *) md;

	if (cmd->object) {
		DagNode *curNode = dag_get_node(ctx->forest, cmd->object);
		curNode->eval_flags |= DAG_EVAL_NEED_CURVE_PATH;

		dag_add_relation(ctx->forest, curNode, ctx->obNode,
		                 DAG_RL_DATA_DATA | DAG_RL_OB_DATA, "Curve Modifier");
	}
}

static void updateDepsgraph(ModifierData *md, const ModifierUpdateDepsgraphContext *ctx)
{
	CurveModifierData *cmd = (CurveModifierData *)md;
	if (cmd->object != NULL) {
		/* TODO(sergey): Need to do the same eval_flags trick for path
		 * as happening in legacy depsgraph callback.
		 */
		/* TODO(sergey): Currently path is evaluated as a part of modifier stack,
		 * might be changed in the future.
		 */
		struct Depsgraph *depsgraph = DEG_get_graph_from_handle(ctx->node);
		DEG_add_object_relation(ctx->node, cmd->object, DEG_OB_COMP_GEOMETRY, "Curve Modifier");
		DEG_add_special_eval_flag(depsgraph, &cmd->object->id, DAG_EVAL_NEED_CURVE_PATH);
	}

	DEG_add_object_relation(ctx->node, ctx->object, DEG_OB_COMP_TRANSFORM, "Curve Modifier");
}

static void deformVerts(
        ModifierData *md, Object *ob,
        DerivedMesh *derivedData,
        float (*vertexCos)[3],
        int numVerts,
        ModifierApplyFlag UNUSED(flag))
{
	CurveModifierData *cmd = (CurveModifierData *) md;

	/* silly that defaxis and curve_deform_verts are off by 1
	 * but leave for now to save having to call do_versions */
	curve_deform_verts(md->scene, cmd->object, ob, derivedData, vertexCos, numVerts,
	                   cmd->name, cmd->defaxis - 1);
}

static void deformVertsEM(
        ModifierData *md, Object *ob, struct BMEditMesh *em,
        DerivedMesh *derivedData, float (*vertexCos)[3], int numVerts)
{
	DerivedMesh *dm = derivedData;

	if (!derivedData) dm = CDDM_from_editbmesh(em, false, false);

	deformVerts(md, ob, dm, vertexCos, numVerts, 0);

	if (!derivedData) dm->release(dm);
}


ModifierTypeInfo modifierType_Curve = {
	/* name */              "Curve",
	/* structName */        "CurveModifierData",
	/* structSize */        sizeof(CurveModifierData),
	/* type */              eModifierTypeType_OnlyDeform,
	/* flags */             eModifierTypeFlag_AcceptsCVs |
	                        eModifierTypeFlag_AcceptsLattice |
	                        eModifierTypeFlag_SupportsEditmode,

	/* copyData */          modifier_copyData_generic,
	/* deformVerts */       deformVerts,
	/* deformMatrices */    NULL,
	/* deformVertsEM */     deformVertsEM,
	/* deformMatricesEM */  NULL,
	/* applyModifier */     NULL,
	/* applyModifierEM */   NULL,
	/* initData */          initData,
	/* requiredDataMask */  requiredDataMask,
	/* freeData */          NULL,
	/* isDisabled */        isDisabled,
	/* updateDepgraph */    updateDepgraph,
	/* updateDepsgraph */   updateDepsgraph,
	/* dependsOnTime */     NULL,
	/* dependsOnNormals */  NULL,
	/* foreachObjectLink */ foreachObjectLink,
	/* foreachIDLink */     NULL,
	/* foreachTexLink */    NULL,
};

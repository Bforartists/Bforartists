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

/** \file
 * \ingroup modifiers
 */

#include <string.h>

#include "BLI_utildefines.h"

#include "DNA_mesh_types.h"
#include "DNA_scene_types.h"
#include "DNA_object_types.h"

#include "BKE_editmesh.h"
#include "BKE_lattice.h"
#include "BKE_library.h"
#include "BKE_library_query.h"
#include "BKE_mesh.h"
#include "BKE_modifier.h"

#include "DEG_depsgraph.h"
#include "DEG_depsgraph_build.h"
#include "DEG_depsgraph_query.h"

#include "MOD_modifiertypes.h"
#include "MOD_util.h"

static void initData(ModifierData *md)
{
  CurveModifierData *cmd = (CurveModifierData *)md;

  cmd->defaxis = MOD_CURVE_POSX;
}

static void requiredDataMask(Object *UNUSED(ob),
                             ModifierData *md,
                             CustomData_MeshMasks *r_cddata_masks)
{
  CurveModifierData *cmd = (CurveModifierData *)md;

  /* ask for vertexgroups if we need them */
  if (cmd->name[0] != '\0') {
    r_cddata_masks->vmask |= CD_MASK_MDEFORMVERT;
  }
}

static bool isDisabled(const Scene *UNUSED(scene), ModifierData *md, bool UNUSED(userRenderParams))
{
  CurveModifierData *cmd = (CurveModifierData *)md;

  /* The object type check is only needed here in case we have a placeholder
   * object assigned (because the library containing the curve is missing).
   *
   * In other cases it should be impossible to have a type mismatch.
   */
  return !cmd->object || cmd->object->type != OB_CURVE;
}

static void foreachObjectLink(ModifierData *md, Object *ob, ObjectWalkFunc walk, void *userData)
{
  CurveModifierData *cmd = (CurveModifierData *)md;

  walk(userData, ob, &cmd->object, IDWALK_CB_NOP);
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
    DEG_add_object_relation(ctx->node, cmd->object, DEG_OB_COMP_TRANSFORM, "Curve Modifier");
    DEG_add_object_relation(ctx->node, cmd->object, DEG_OB_COMP_GEOMETRY, "Curve Modifier");
    DEG_add_special_eval_flag(ctx->node, &cmd->object->id, DAG_EVAL_NEED_CURVE_PATH);
  }

  DEG_add_modifier_to_transform_relation(ctx->node, "Curve Modifier");
}

static void deformVerts(ModifierData *md,
                        const ModifierEvalContext *ctx,
                        Mesh *mesh,
                        float (*vertexCos)[3],
                        int numVerts)
{
  CurveModifierData *cmd = (CurveModifierData *)md;
  Mesh *mesh_src = NULL;

  if (ctx->object->type == OB_MESH && cmd->name[0] != '\0') {
    /* mesh_src is only needed for vgroups. */
    mesh_src = MOD_deform_mesh_eval_get(ctx->object, NULL, mesh, NULL, numVerts, false, false);
  }

  struct MDeformVert *dvert = NULL;
  int defgrp_index = -1;
  MOD_get_vgroup(ctx->object, mesh_src, cmd->name, &dvert, &defgrp_index);

  /* silly that defaxis and curve_deform_verts are off by 1
   * but leave for now to save having to call do_versions */
  curve_deform_verts(
      cmd->object, ctx->object, vertexCos, numVerts, dvert, defgrp_index, cmd->defaxis - 1);

  if (!ELEM(mesh_src, NULL, mesh)) {
    BKE_id_free(NULL, mesh_src);
  }
}

static void deformVertsEM(ModifierData *md,
                          const ModifierEvalContext *ctx,
                          struct BMEditMesh *em,
                          Mesh *mesh,
                          float (*vertexCos)[3],
                          int numVerts)
{
  Mesh *mesh_src = MOD_deform_mesh_eval_get(ctx->object, em, mesh, NULL, numVerts, false, false);

  deformVerts(md, ctx, mesh_src, vertexCos, numVerts);

  if (!ELEM(mesh_src, NULL, mesh)) {
    BKE_id_free(NULL, mesh_src);
  }
}

ModifierTypeInfo modifierType_Curve = {
    /* name */ "Curve",
    /* structName */ "CurveModifierData",
    /* structSize */ sizeof(CurveModifierData),
    /* type */ eModifierTypeType_OnlyDeform,
    /* flags */ eModifierTypeFlag_AcceptsCVs | eModifierTypeFlag_AcceptsLattice |
        eModifierTypeFlag_SupportsEditmode,

    /* copyData */ modifier_copyData_generic,

    /* deformVerts */ deformVerts,
    /* deformMatrices */ NULL,
    /* deformVertsEM */ deformVertsEM,
    /* deformMatricesEM */ NULL,
    /* applyModifier */ NULL,

    /* initData */ initData,
    /* requiredDataMask */ requiredDataMask,
    /* freeData */ NULL,
    /* isDisabled */ isDisabled,
    /* updateDepsgraph */ updateDepsgraph,
    /* dependsOnTime */ NULL,
    /* dependsOnNormals */ NULL,
    /* foreachObjectLink */ foreachObjectLink,
    /* foreachIDLink */ NULL,
    /* foreachTexLink */ NULL,
    /* freeRuntimeData */ NULL,
};

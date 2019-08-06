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
 * The Original Code is Copyright (C) 2011 by Bastien Montagne.
 * All rights reserved.
 */

/** \file
 * \ingroup modifiers
 */

#include "BLI_utildefines.h"

#include "BLI_ghash.h"
#include "BLI_listbase.h"
#include "BLI_rand.h"

#include "DNA_color_types.h" /* CurveMapping. */
#include "DNA_mesh_types.h"
#include "DNA_meshdata_types.h"
#include "DNA_modifier_types.h"
#include "DNA_object_types.h"

#include "BKE_colortools.h" /* CurveMapping. */
#include "BKE_deform.h"
#include "BKE_library_query.h"
#include "BKE_modifier.h"
#include "BKE_texture.h" /* Texture masking. */

#include "DEG_depsgraph_build.h"
#include "DEG_depsgraph_query.h"

#include "MEM_guardedalloc.h"

#include "MOD_weightvg_util.h"
#include "MOD_modifiertypes.h"

/**************************************
 * Modifiers functions.               *
 **************************************/
static void initData(ModifierData *md)
{
  WeightVGEditModifierData *wmd = (WeightVGEditModifierData *)md;
  wmd->edit_flags = 0;
  wmd->falloff_type = MOD_WVG_MAPPING_NONE;
  wmd->default_weight = 0.0f;

  wmd->cmap_curve = BKE_curvemapping_add(1, 0.0, 0.0, 1.0, 1.0);
  BKE_curvemapping_initialize(wmd->cmap_curve);

  wmd->rem_threshold = 0.01f;
  wmd->add_threshold = 0.01f;

  wmd->mask_constant = 1.0f;
  wmd->mask_tex_use_channel = MOD_WVG_MASK_TEX_USE_INT; /* Use intensity by default. */
  wmd->mask_tex_mapping = MOD_DISP_MAP_LOCAL;
}

static void freeData(ModifierData *md)
{
  WeightVGEditModifierData *wmd = (WeightVGEditModifierData *)md;
  BKE_curvemapping_free(wmd->cmap_curve);
}

static void copyData(const ModifierData *md, ModifierData *target, const int flag)
{
  const WeightVGEditModifierData *wmd = (const WeightVGEditModifierData *)md;
  WeightVGEditModifierData *twmd = (WeightVGEditModifierData *)target;

  modifier_copyData_generic(md, target, flag);

  twmd->cmap_curve = BKE_curvemapping_copy(wmd->cmap_curve);
}

static void requiredDataMask(Object *UNUSED(ob),
                             ModifierData *md,
                             CustomData_MeshMasks *r_cddata_masks)
{
  WeightVGEditModifierData *wmd = (WeightVGEditModifierData *)md;

  /* We need vertex groups! */
  r_cddata_masks->vmask |= CD_MASK_MDEFORMVERT;

  /* Ask for UV coordinates if we need them. */
  if (wmd->mask_tex_mapping == MOD_DISP_MAP_UV) {
    r_cddata_masks->fmask |= CD_MASK_MTFACE;
  }

  /* No need to ask for CD_PREVIEW_MLOOPCOL... */
}

static bool dependsOnTime(ModifierData *md)
{
  WeightVGEditModifierData *wmd = (WeightVGEditModifierData *)md;

  if (wmd->mask_texture) {
    return BKE_texture_dependsOnTime(wmd->mask_texture);
  }
  return false;
}

static void foreachObjectLink(ModifierData *md, Object *ob, ObjectWalkFunc walk, void *userData)
{
  WeightVGEditModifierData *wmd = (WeightVGEditModifierData *)md;
  walk(userData, ob, &wmd->mask_tex_map_obj, IDWALK_CB_NOP);
}

static void foreachIDLink(ModifierData *md, Object *ob, IDWalkFunc walk, void *userData)
{
  WeightVGEditModifierData *wmd = (WeightVGEditModifierData *)md;

  walk(userData, ob, (ID **)&wmd->mask_texture, IDWALK_CB_USER);

  foreachObjectLink(md, ob, (ObjectWalkFunc)walk, userData);
}

static void foreachTexLink(ModifierData *md, Object *ob, TexWalkFunc walk, void *userData)
{
  walk(userData, ob, md, "mask_texture");
}

static void updateDepsgraph(ModifierData *md, const ModifierUpdateDepsgraphContext *ctx)
{
  WeightVGEditModifierData *wmd = (WeightVGEditModifierData *)md;
  if (wmd->mask_tex_map_obj != NULL && wmd->mask_tex_mapping == MOD_DISP_MAP_OBJECT) {
    DEG_add_object_relation(
        ctx->node, wmd->mask_tex_map_obj, DEG_OB_COMP_TRANSFORM, "WeightVGEdit Modifier");
    DEG_add_modifier_to_transform_relation(ctx->node, "WeightVGEdit Modifier");
  }
  else if (wmd->mask_tex_mapping == MOD_DISP_MAP_GLOBAL) {
    DEG_add_modifier_to_transform_relation(ctx->node, "WeightVGEdit Modifier");
  }
  if (wmd->mask_texture != NULL) {
    DEG_add_generic_id_relation(ctx->node, &wmd->mask_texture->id, "WeightVGEdit Modifier");
  }
}

static bool isDisabled(const struct Scene *UNUSED(scene),
                       ModifierData *md,
                       bool UNUSED(useRenderParams))
{
  WeightVGEditModifierData *wmd = (WeightVGEditModifierData *)md;
  /* If no vertex group, bypass. */
  return (wmd->defgrp_name[0] == '\0');
}

static Mesh *applyModifier(ModifierData *md, const ModifierEvalContext *ctx, Mesh *mesh)
{
  BLI_assert(mesh != NULL);

  WeightVGEditModifierData *wmd = (WeightVGEditModifierData *)md;

  MDeformVert *dvert = NULL;
  MDeformWeight **dw = NULL;
  float *org_w; /* Array original weights. */
  float *new_w; /* Array new weights. */
  int i;

  /* Flags. */
  const bool do_add = (wmd->edit_flags & MOD_WVG_EDIT_ADD2VG) != 0;
  const bool do_rem = (wmd->edit_flags & MOD_WVG_EDIT_REMFVG) != 0;
  /* Only do weight-preview in Object, Sculpt and Pose modes! */
#if 0
  const bool do_prev = (wmd->modifier.mode & eModifierMode_DoWeightPreview);
#endif

  /* Get number of verts. */
  const int numVerts = mesh->totvert;

  /* Check if we can just return the original mesh.
   * Must have verts and therefore verts assigned to vgroups to do anything useful!
   */
  if ((numVerts == 0) || BLI_listbase_is_empty(&ctx->object->defbase)) {
    return mesh;
  }

  /* Get vgroup idx from its name. */
  const int defgrp_index = defgroup_name_index(ctx->object, wmd->defgrp_name);
  if (defgrp_index == -1) {
    return mesh;
  }

  const bool has_mdef = CustomData_has_layer(&mesh->vdata, CD_MDEFORMVERT);
  /* If no vertices were ever added to an object's vgroup, dvert might be NULL. */
  if (!has_mdef) {
    /* If this modifier is not allowed to add vertices, just return. */
    if (!do_add) {
      return mesh;
    }
  }

  if (has_mdef) {
    dvert = CustomData_duplicate_referenced_layer(&mesh->vdata, CD_MDEFORMVERT, numVerts);
  }
  else {
    /* Add a valid data layer! */
    dvert = CustomData_add_layer(&mesh->vdata, CD_MDEFORMVERT, CD_CALLOC, NULL, numVerts);
  }
  /* Ultimate security check. */
  if (!dvert) {
    return mesh;
  }
  mesh->dvert = dvert;

  /* Get org weights, assuming 0.0 for vertices not in given vgroup. */
  org_w = MEM_malloc_arrayN(numVerts, sizeof(float), "WeightVGEdit Modifier, org_w");
  new_w = MEM_malloc_arrayN(numVerts, sizeof(float), "WeightVGEdit Modifier, new_w");
  dw = MEM_malloc_arrayN(numVerts, sizeof(MDeformWeight *), "WeightVGEdit Modifier, dw");
  for (i = 0; i < numVerts; i++) {
    dw[i] = defvert_find_index(&dvert[i], defgrp_index);
    if (dw[i]) {
      org_w[i] = new_w[i] = dw[i]->weight;
    }
    else {
      org_w[i] = new_w[i] = wmd->default_weight;
    }
  }

  /* Do mapping. */
  if (wmd->falloff_type != MOD_WVG_MAPPING_NONE) {
    RNG *rng = NULL;

    if (wmd->falloff_type == MOD_WVG_MAPPING_RANDOM) {
      rng = BLI_rng_new_srandom(BLI_ghashutil_strhash(ctx->object->id.name + 2));
    }

    weightvg_do_map(numVerts, new_w, wmd->falloff_type, wmd->cmap_curve, rng);

    if (rng) {
      BLI_rng_free(rng);
    }
  }

  /* Do masking. */
  struct Scene *scene = DEG_get_evaluated_scene(ctx->depsgraph);
  weightvg_do_mask(ctx,
                   numVerts,
                   NULL,
                   org_w,
                   new_w,
                   ctx->object,
                   mesh,
                   wmd->mask_constant,
                   wmd->mask_defgrp_name,
                   scene,
                   wmd->mask_texture,
                   wmd->mask_tex_use_channel,
                   wmd->mask_tex_mapping,
                   wmd->mask_tex_map_obj,
                   wmd->mask_tex_uvlayer_name);

  /* Update/add/remove from vgroup. */
  weightvg_update_vg(dvert,
                     defgrp_index,
                     dw,
                     numVerts,
                     NULL,
                     org_w,
                     do_add,
                     wmd->add_threshold,
                     do_rem,
                     wmd->rem_threshold);

  /* If weight preview enabled... */
#if 0 /* XXX Currently done in mod stack :/ */
  if (do_prev) {
    DM_update_weight_mcol(ob, dm, 0, org_w, 0, NULL);
  }
#endif

  /* Freeing stuff. */
  MEM_freeN(org_w);
  MEM_freeN(new_w);
  MEM_freeN(dw);

  /* Return the vgroup-modified mesh. */
  return mesh;
}

ModifierTypeInfo modifierType_WeightVGEdit = {
    /* name */ "VertexWeightEdit",
    /* structName */ "WeightVGEditModifierData",
    /* structSize */ sizeof(WeightVGEditModifierData),
    /* type */ eModifierTypeType_NonGeometrical,
    /* flags */ eModifierTypeFlag_AcceptsMesh | eModifierTypeFlag_SupportsMapping |
        eModifierTypeFlag_SupportsEditmode | eModifierTypeFlag_UsesPreview,

    /* copyData */ copyData,

    /* deformVerts */ NULL,
    /* deformMatrices */ NULL,
    /* deformVertsEM */ NULL,
    /* deformMatricesEM */ NULL,
    /* applyModifier */ applyModifier,

    /* initData */ initData,
    /* requiredDataMask */ requiredDataMask,
    /* freeData */ freeData,
    /* isDisabled */ isDisabled,
    /* updateDepsgraph */ updateDepsgraph,
    /* dependsOnTime */ dependsOnTime,
    /* dependsOnNormals */ NULL,
    /* foreachObjectLink */ foreachObjectLink,
    /* foreachIDLink */ foreachIDLink,
    /* foreachTexLink */ foreachTexLink,
    /* freeRuntimeData */ NULL,
};

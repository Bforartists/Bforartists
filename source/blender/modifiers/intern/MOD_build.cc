/* SPDX-License-Identifier: GPL-2.0-or-later
 * Copyright 2005 Blender Foundation. All rights reserved. */

/** \file
 * \ingroup modifiers
 */

#include "MEM_guardedalloc.h"

#include "BLI_utildefines.h"

#include "BLI_ghash.h"
#include "BLI_math_vector.h"
#include "BLI_rand.h"

#include "BLT_translation.h"

#include "DNA_defaults.h"
#include "DNA_mesh_types.h"
#include "DNA_meshdata_types.h"
#include "DNA_object_types.h"
#include "DNA_screen_types.h"

#include "DEG_depsgraph_query.h"

#include "BKE_context.h"
#include "BKE_mesh.hh"
#include "BKE_modifier.h"
#include "BKE_particle.h"
#include "BKE_scene.h"
#include "BKE_screen.h"

#include "UI_interface.h"
#include "UI_resources.h"

#include "RNA_access.h"
#include "RNA_prototypes.h"

#include "MOD_modifiertypes.h"
#include "MOD_ui_common.h"

static void initData(ModifierData *md)
{
  BuildModifierData *bmd = (BuildModifierData *)md;

  BLI_assert(MEMCMP_STRUCT_AFTER_IS_ZERO(bmd, modifier));

  MEMCPY_STRUCT_AFTER(bmd, DNA_struct_default_get(BuildModifierData), modifier);
}

static bool dependsOnTime(Scene * /*scene*/, ModifierData * /*md*/)
{
  return true;
}

static Mesh *modifyMesh(ModifierData *md, const ModifierEvalContext *ctx, Mesh *mesh)
{
  Mesh *result;
  BuildModifierData *bmd = (BuildModifierData *)md;
  int i, j, k;
  int faces_dst_num, edges_dst_num, loops_dst_num = 0;
  float frac;
  MPoly *mpoly_dst;
  GHashIterator gh_iter;
  /* maps vert indices in old mesh to indices in new mesh */
  GHash *vertHash = BLI_ghash_int_new("build ve apply gh");
  /* maps edge indices in new mesh to indices in old mesh */
  GHash *edgeHash = BLI_ghash_int_new("build ed apply gh");
  /* maps edge indices in old mesh to indices in new mesh */
  GHash *edgeHash2 = BLI_ghash_int_new("build ed apply gh");

  const int vert_src_num = mesh->totvert;
  const blender::Span<MEdge> edges_src = mesh->edges();
  const blender::Span<MPoly> polys_src = mesh->polys();
  const blender::Span<int> corner_verts_src = mesh->corner_verts();
  const blender::Span<int> corner_edges_src = mesh->corner_edges();

  int *vertMap = static_cast<int *>(MEM_malloc_arrayN(vert_src_num, sizeof(int), __func__));
  int *edgeMap = static_cast<int *>(MEM_malloc_arrayN(edges_src.size(), sizeof(int), __func__));
  int *faceMap = static_cast<int *>(MEM_malloc_arrayN(polys_src.size(), sizeof(int), __func__));

  range_vn_i(vertMap, vert_src_num, 0);
  range_vn_i(edgeMap, edges_src.size(), 0);
  range_vn_i(faceMap, polys_src.size(), 0);

  Scene *scene = DEG_get_input_scene(ctx->depsgraph);
  frac = (BKE_scene_ctime_get(scene) - bmd->start) / bmd->length;
  CLAMP(frac, 0.0f, 1.0f);
  if (bmd->flag & MOD_BUILD_FLAG_REVERSE) {
    frac = 1.0f - frac;
  }

  faces_dst_num = polys_src.size() * frac;
  edges_dst_num = edges_src.size() * frac;

  /* if there's at least one face, build based on faces */
  if (faces_dst_num) {
    const MPoly *polys, *poly;
    uintptr_t hash_num, hash_num_alt;

    if (bmd->flag & MOD_BUILD_FLAG_RANDOMIZE) {
      BLI_array_randomize(faceMap, sizeof(*faceMap), polys_src.size(), bmd->seed);
    }

    /* get the set of all vert indices that will be in the final mesh,
     * mapped to the new indices
     */
    polys = polys_src.data();
    hash_num = 0;
    for (i = 0; i < faces_dst_num; i++) {
      poly = polys + faceMap[i];
      for (j = 0; j < poly->totloop; j++) {
        const int vert_i = corner_verts_src[poly->loopstart + j];
        void **val_p;
        if (!BLI_ghash_ensure_p(vertHash, POINTER_FROM_INT(vert_i), &val_p)) {
          *val_p = (void *)hash_num;
          hash_num++;
        }
      }

      loops_dst_num += poly->totloop;
    }
    BLI_assert(hash_num == BLI_ghash_len(vertHash));

    /* get the set of edges that will be in the new mesh (i.e. all edges
     * that have both verts in the new mesh)
     */
    hash_num = 0;
    hash_num_alt = 0;
    for (i = 0; i < edges_src.size(); i++, hash_num_alt++) {
      const MEdge *edge = edges_src.data() + i;

      if (BLI_ghash_haskey(vertHash, POINTER_FROM_INT(edge->v1)) &&
          BLI_ghash_haskey(vertHash, POINTER_FROM_INT(edge->v2))) {
        BLI_ghash_insert(edgeHash, (void *)hash_num, (void *)hash_num_alt);
        BLI_ghash_insert(edgeHash2, (void *)hash_num_alt, (void *)hash_num);
        hash_num++;
      }
    }
    BLI_assert(hash_num == BLI_ghash_len(edgeHash));
  }
  else if (edges_dst_num) {
    const MEdge *edge;
    uintptr_t hash_num;

    if (bmd->flag & MOD_BUILD_FLAG_RANDOMIZE) {
      BLI_array_randomize(edgeMap, sizeof(*edgeMap), edges_src.size(), bmd->seed);
    }

    /* get the set of all vert indices that will be in the final mesh,
     * mapped to the new indices
     */
    const MEdge *edges = edges_src.data();
    hash_num = 0;
    BLI_assert(hash_num == BLI_ghash_len(vertHash));
    for (i = 0; i < edges_dst_num; i++) {
      void **val_p;
      edge = edges + edgeMap[i];

      if (!BLI_ghash_ensure_p(vertHash, POINTER_FROM_INT(edge->v1), &val_p)) {
        *val_p = (void *)hash_num;
        hash_num++;
      }
      if (!BLI_ghash_ensure_p(vertHash, POINTER_FROM_INT(edge->v2), &val_p)) {
        *val_p = (void *)hash_num;
        hash_num++;
      }
    }
    BLI_assert(hash_num == BLI_ghash_len(vertHash));

    /* get the set of edges that will be in the new mesh */
    for (i = 0; i < edges_dst_num; i++) {
      j = BLI_ghash_len(edgeHash);

      BLI_ghash_insert(edgeHash, POINTER_FROM_INT(j), POINTER_FROM_INT(edgeMap[i]));
      BLI_ghash_insert(edgeHash2, POINTER_FROM_INT(edgeMap[i]), POINTER_FROM_INT(j));
    }
  }
  else {
    int verts_num = vert_src_num * frac;

    if (bmd->flag & MOD_BUILD_FLAG_RANDOMIZE) {
      BLI_array_randomize(vertMap, sizeof(*vertMap), vert_src_num, bmd->seed);
    }

    /* get the set of all vert indices that will be in the final mesh,
     * mapped to the new indices
     */
    for (i = 0; i < verts_num; i++) {
      BLI_ghash_insert(vertHash, POINTER_FROM_INT(vertMap[i]), POINTER_FROM_INT(i));
    }
  }

  /* now we know the number of verts, edges and faces, we can create the mesh. */
  result = BKE_mesh_new_nomain_from_template(
      mesh, BLI_ghash_len(vertHash), BLI_ghash_len(edgeHash), loops_dst_num, faces_dst_num);
  blender::MutableSpan<MEdge> result_edges = result->edges_for_write();
  blender::MutableSpan<MPoly> result_polys = result->polys_for_write();
  blender::MutableSpan<int> result_corner_verts = result->corner_verts_for_write();
  blender::MutableSpan<int> result_corner_edges = result->corner_edges_for_write();

  /* copy the vertices across */
  GHASH_ITER (gh_iter, vertHash) {
    int oldIndex = POINTER_AS_INT(BLI_ghashIterator_getKey(&gh_iter));
    int newIndex = POINTER_AS_INT(BLI_ghashIterator_getValue(&gh_iter));
    CustomData_copy_data(&mesh->vdata, &result->vdata, oldIndex, newIndex, 1);
  }

  /* copy the edges across, remapping indices */
  for (i = 0; i < BLI_ghash_len(edgeHash); i++) {
    MEdge source;
    MEdge *dest;
    int oldIndex = POINTER_AS_INT(BLI_ghash_lookup(edgeHash, POINTER_FROM_INT(i)));

    source = edges_src[oldIndex];
    dest = &result_edges[i];

    source.v1 = POINTER_AS_INT(BLI_ghash_lookup(vertHash, POINTER_FROM_INT(source.v1)));
    source.v2 = POINTER_AS_INT(BLI_ghash_lookup(vertHash, POINTER_FROM_INT(source.v2)));

    CustomData_copy_data(&mesh->edata, &result->edata, oldIndex, i, 1);
    *dest = source;
  }

  mpoly_dst = result_polys.data();

  /* copy the faces across, remapping indices */
  k = 0;
  for (i = 0; i < faces_dst_num; i++) {
    const MPoly *source;
    MPoly *dest;

    source = &polys_src[faceMap[i]];
    dest = mpoly_dst + i;
    CustomData_copy_data(&mesh->pdata, &result->pdata, faceMap[i], i, 1);

    *dest = *source;
    dest->loopstart = k;
    CustomData_copy_data(
        &mesh->ldata, &result->ldata, source->loopstart, dest->loopstart, dest->totloop);

    for (j = 0; j < source->totloop; j++, k++) {
      const int vert_src = corner_verts_src[source->loopstart + j];
      const int edge_src = corner_edges_src[source->loopstart + j];
      result_corner_verts[dest->loopstart + j] = POINTER_AS_INT(
          BLI_ghash_lookup(vertHash, POINTER_FROM_INT(vert_src)));
      result_corner_edges[dest->loopstart + j] = POINTER_AS_INT(
          BLI_ghash_lookup(edgeHash2, POINTER_FROM_INT(edge_src)));
    }
  }

  BLI_ghash_free(vertHash, nullptr, nullptr);
  BLI_ghash_free(edgeHash, nullptr, nullptr);
  BLI_ghash_free(edgeHash2, nullptr, nullptr);

  MEM_freeN(vertMap);
  MEM_freeN(edgeMap);
  MEM_freeN(faceMap);

  /* TODO(sybren): also copy flags & tags? */
  return result;
}

static void panel_draw(const bContext * /*C*/, Panel *panel)
{
  uiLayout *layout = panel->layout;

  PointerRNA *ptr = modifier_panel_get_property_pointers(panel, nullptr);

  uiLayoutSetPropSep(layout, true);

  uiItemR(layout, ptr, "frame_start", 0, nullptr, ICON_NONE);
  uiItemR(layout, ptr, "frame_duration", 0, nullptr, ICON_NONE);
  uiItemR(layout, ptr, "use_reverse", 0, nullptr, ICON_NONE);

  modifier_panel_end(layout, ptr);
}

static void random_panel_header_draw(const bContext * /*C*/, Panel *panel)
{
  uiLayout *layout = panel->layout;

  PointerRNA *ptr = modifier_panel_get_property_pointers(panel, nullptr);

  uiItemR(layout, ptr, "use_random_order", 0, nullptr, ICON_NONE);
}

static void random_panel_draw(const bContext * /*C*/, Panel *panel)
{
  uiLayout *layout = panel->layout;

  PointerRNA *ptr = modifier_panel_get_property_pointers(panel, nullptr);

  uiLayoutSetPropSep(layout, true);

  uiLayoutSetActive(layout, RNA_boolean_get(ptr, "use_random_order"));
  uiItemR(layout, ptr, "seed", 0, nullptr, ICON_NONE);
}

static void panelRegister(ARegionType *region_type)
{
  PanelType *panel_type = modifier_panel_register(region_type, eModifierType_Build, panel_draw);
  modifier_subpanel_register(
      region_type, "randomize", "", random_panel_header_draw, random_panel_draw, panel_type);
}

ModifierTypeInfo modifierType_Build = {
    /*name*/ N_("Build"),
    /*structName*/ "BuildModifierData",
    /*structSize*/ sizeof(BuildModifierData),
    /*srna*/ &RNA_BuildModifier,
    /*type*/ eModifierTypeType_Nonconstructive,
    /*flags*/ eModifierTypeFlag_AcceptsMesh | eModifierTypeFlag_AcceptsCVs,
    /*icon*/ ICON_MOD_BUILD,

    /*copyData*/ BKE_modifier_copydata_generic,

    /*deformVerts*/ nullptr,
    /*deformMatrices*/ nullptr,
    /*deformVertsEM*/ nullptr,
    /*deformMatricesEM*/ nullptr,
    /*modifyMesh*/ modifyMesh,
    /*modifyGeometrySet*/ nullptr,

    /*initData*/ initData,
    /*requiredDataMask*/ nullptr,
    /*freeData*/ nullptr,
    /*isDisabled*/ nullptr,
    /*updateDepsgraph*/ nullptr,
    /*dependsOnTime*/ dependsOnTime,
    /*dependsOnNormals*/ nullptr,
    /*foreachIDLink*/ nullptr,
    /*foreachTexLink*/ nullptr,
    /*freeRuntimeData*/ nullptr,
    /*panelRegister*/ panelRegister,
    /*blendWrite*/ nullptr,
    /*blendRead*/ nullptr,
};

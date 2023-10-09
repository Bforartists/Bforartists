/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup modifiers
 */

#include <vector>

#include "BKE_geometry_set.hh"
#include "BKE_lib_id.h"
#include "BKE_lib_query.h"
#include "BKE_mesh_runtime.hh"
#include "BKE_mesh_wrapper.hh"
#include "BKE_modifier.h"
#include "BKE_object.hh"
#include "BKE_volume.h"

#include "BLT_translation.h"

#include "DNA_mesh_types.h"
#include "DNA_meshdata_types.h"
#include "DNA_object_types.h"
#include "DNA_screen_types.h"
#include "DNA_volume_types.h"

#include "DEG_depsgraph.hh"

#include "GEO_mesh_to_volume.hh"

#include "UI_interface.hh"
#include "UI_resources.hh"

#include "BLO_read_write.hh"

#include "MEM_guardedalloc.h"

#include "MOD_modifiertypes.hh"
#include "MOD_ui_common.hh"

#include "BLI_index_range.hh"
#include "BLI_math_matrix_types.hh"
#include "BLI_span.hh"

#include "RNA_access.hh"
#include "RNA_prototypes.h"

static void init_data(ModifierData *md)
{
  MeshToVolumeModifierData *mvmd = reinterpret_cast<MeshToVolumeModifierData *>(md);
  mvmd->object = nullptr;
  mvmd->resolution_mode = MESH_TO_VOLUME_RESOLUTION_MODE_VOXEL_AMOUNT;
  mvmd->voxel_size = 0.1f;
  mvmd->voxel_amount = 32;
  mvmd->interior_band_width = 0.2f;
  mvmd->density = 1.0f;
}

static void update_depsgraph(ModifierData *md, const ModifierUpdateDepsgraphContext *ctx)
{
  MeshToVolumeModifierData *mvmd = reinterpret_cast<MeshToVolumeModifierData *>(md);
  DEG_add_depends_on_transform_relation(ctx->node, "Mesh to Volume Modifier");
  if (mvmd->object) {
    DEG_add_object_relation(
        ctx->node, mvmd->object, DEG_OB_COMP_GEOMETRY, "Mesh to Volume Modifier");
    DEG_add_object_relation(
        ctx->node, mvmd->object, DEG_OB_COMP_TRANSFORM, "Mesh to Volume Modifier");
  }
}

static void foreach_ID_link(ModifierData *md, Object *ob, IDWalkFunc walk, void *user_data)
{
  MeshToVolumeModifierData *mvmd = reinterpret_cast<MeshToVolumeModifierData *>(md);
  walk(user_data, ob, (ID **)&mvmd->object, IDWALK_CB_NOP);
}

static void panel_draw(const bContext * /*C*/, Panel *panel)
{
  uiLayout *layout = panel->layout;

  PointerRNA *ptr = modifier_panel_get_property_pointers(panel, nullptr);
  MeshToVolumeModifierData *mvmd = static_cast<MeshToVolumeModifierData *>(ptr->data);

  uiLayoutSetPropSep(layout, true);

  uiItemR(layout, ptr, "object", UI_ITEM_NONE, nullptr, ICON_NONE);
  uiItemR(layout, ptr, "density", UI_ITEM_NONE, nullptr, ICON_NONE);

  {
    uiLayout *col = uiLayoutColumn(layout, false);
    uiItemR(col, ptr, "interior_band_width", UI_ITEM_NONE, nullptr, ICON_NONE);
  }
  {
    uiLayout *col = uiLayoutColumn(layout, false);
    uiItemR(col, ptr, "resolution_mode", UI_ITEM_NONE, nullptr, ICON_NONE);
    if (mvmd->resolution_mode == MESH_TO_VOLUME_RESOLUTION_MODE_VOXEL_AMOUNT) {
      uiItemR(col, ptr, "voxel_amount", UI_ITEM_NONE, nullptr, ICON_NONE);
    }
    else {
      uiItemR(col, ptr, "voxel_size", UI_ITEM_NONE, nullptr, ICON_NONE);
    }
  }

  modifier_panel_end(layout, ptr);
}

static void panel_register(ARegionType *region_type)
{
  modifier_panel_register(region_type, eModifierType_MeshToVolume, panel_draw);
}

static Volume *mesh_to_volume(ModifierData *md,
                              const ModifierEvalContext *ctx,
                              Volume *input_volume)
{
#ifdef WITH_OPENVDB
  using namespace blender;

  MeshToVolumeModifierData *mvmd = reinterpret_cast<MeshToVolumeModifierData *>(md);
  Object *object_to_convert = mvmd->object;

  if (object_to_convert == nullptr) {
    return input_volume;
  }
  Mesh *mesh = BKE_modifier_get_evaluated_mesh_from_evaluated_object(object_to_convert);
  if (mesh == nullptr) {
    return input_volume;
  }
  BKE_mesh_wrapper_ensure_mdata(mesh);
  if (mesh->totvert == 0) {
    return input_volume;
  }

  const float4x4 mesh_to_own_object_space_transform = float4x4(ctx->object->world_to_object) *
                                                      float4x4(object_to_convert->object_to_world);
  geometry::MeshToVolumeResolution resolution;
  resolution.mode = (MeshToVolumeModifierResolutionMode)mvmd->resolution_mode;
  if (resolution.mode == MESH_TO_VOLUME_RESOLUTION_MODE_VOXEL_AMOUNT) {
    resolution.settings.voxel_amount = mvmd->voxel_amount;
    if (resolution.settings.voxel_amount < 1.0f) {
      return input_volume;
    }
  }
  else if (resolution.mode == MESH_TO_VOLUME_RESOLUTION_MODE_VOXEL_SIZE) {
    resolution.settings.voxel_size = mvmd->voxel_size;
    if (resolution.settings.voxel_size < 1e-5f) {
      return input_volume;
    }
  }

  auto bounds_fn = [&](float3 &r_min, float3 &r_max) {
    const Bounds<float3> bounds = *mesh->bounds_min_max();
    r_min = bounds.min;
    r_max = bounds.max;
  };

  const float voxel_size = geometry::volume_compute_voxel_size(
      ctx->depsgraph, bounds_fn, resolution, 0.0f, mesh_to_own_object_space_transform);

  /* Create a new volume. */
  Volume *volume;
  if (input_volume == nullptr) {
    volume = static_cast<Volume *>(BKE_id_new_nomain(ID_VO, "Volume"));
  }
  else {
    volume = BKE_volume_new_for_eval(input_volume);
  }

  /* Convert mesh to grid and add to volume. */
  geometry::fog_volume_grid_add_from_mesh(volume,
                                          "density",
                                          mesh,
                                          mesh_to_own_object_space_transform,
                                          voxel_size,
                                          mvmd->interior_band_width,
                                          mvmd->density);

  return volume;

#else
  UNUSED_VARS(md);
  BKE_modifier_set_error(ctx->object, md, "Compiled without OpenVDB");
  return input_volume;
#endif
}

static void modify_geometry_set(ModifierData *md,
                                const ModifierEvalContext *ctx,
                                blender::bke::GeometrySet *geometry_set)
{
  Volume *input_volume = geometry_set->get_volume_for_write();
  Volume *result_volume = mesh_to_volume(md, ctx, input_volume);
  if (result_volume != input_volume) {
    geometry_set->replace_volume(result_volume);
  }
}

ModifierTypeInfo modifierType_MeshToVolume = {
    /*idname*/ "Mesh to Volume",
    /*name*/ N_("Mesh to Volume"),
    /*struct_name*/ "MeshToVolumeModifierData",
    /*struct_size*/ sizeof(MeshToVolumeModifierData),
    /*srna*/ &RNA_MeshToVolumeModifier,
    /*type*/ eModifierTypeType_Constructive,
    /*flags*/ static_cast<ModifierTypeFlag>(0),
    /*icon*/ ICON_VOLUME_DATA, /* TODO: Use correct icon. */

    /*copy_data*/ BKE_modifier_copydata_generic,

    /*deform_verts*/ nullptr,
    /*deform_matrices*/ nullptr,
    /*deform_verts_EM*/ nullptr,
    /*deform_matrices_EM*/ nullptr,
    /*modify_mesh*/ nullptr,
    /*modify_geometry_set*/ modify_geometry_set,

    /*init_data*/ init_data,
    /*required_data_mask*/ nullptr,
    /*free_data*/ nullptr,
    /*is_disabled*/ nullptr,
    /*update_depsgraph*/ update_depsgraph,
    /*depends_on_time*/ nullptr,
    /*depends_on_normals*/ nullptr,
    /*foreach_ID_link*/ foreach_ID_link,
    /*foreach_tex_link*/ nullptr,
    /*free_runtime_data*/ nullptr,
    /*panel_register*/ panel_register,
    /*blend_write*/ nullptr,
    /*blend_read*/ nullptr,
};

/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#include "draw_cache.hh"
#include "draw_common_c.hh"

#include "workbench_private.hh"

#include "BKE_volume.hh"
#include "BKE_volume_render.hh"
#include "BLI_math_geom.h"
#include "BLI_rand.h"
#include "DNA_fluid_types.h"
#include "DNA_modifier_types.h"

namespace blender::workbench {

void VolumePass::sync(SceneResources &resources)
{
  active_ = false;
  ps_.init();
  ps_.bind_ubo(WB_WORLD_SLOT, resources.world_buf);

  dummy_shadow_tx_.ensure_3d(GPU_RGBA8, int3(1), GPU_TEXTURE_USAGE_SHADER_READ, float4(1));
  dummy_volume_tx_.ensure_3d(GPU_RGBA8, int3(1), GPU_TEXTURE_USAGE_SHADER_READ, float4(0));
  dummy_coba_tx_.ensure_1d(GPU_RGBA8, 1, GPU_TEXTURE_USAGE_SHADER_READ, float4(0));
}

void VolumePass::object_sync_volume(Manager &manager,
                                    SceneResources &resources,
                                    const SceneState &scene_state,
                                    ObjectRef &ob_ref,
                                    float3 color)
{
  Object *ob = ob_ref.object;
  /* Create 3D textures. */
  Volume &volume = DRW_object_get_data_for_drawing<Volume>(*ob);
  BKE_volume_load(&volume, G.main);
  const bke::VolumeGridData *volume_grid = BKE_volume_grid_active_get_for_read(&volume);
  if (volume_grid == nullptr) {
    return;
  }

  DRWVolumeGrid *grid = DRW_volume_batch_cache_get_grid(&volume, volume_grid);
  if (grid == nullptr) {
    return;
  }

  active_ = true;

  PassMain::Sub &sub_ps = ps_.sub("Volume Object SubPass");

  const bool use_slice = (volume.display.axis_slice_method == AXIS_SLICE_SINGLE);

  sub_ps.shader_set(
      ShaderCache::get().volume_get(false, volume.display.interpolation_method, false, use_slice));
  sub_ps.push_constant("do_depth_test", scene_state.shading.type >= OB_SOLID);

  const float density_fac = volume.display.density *
                            BKE_volume_density_scale(&volume, ob->object_to_world().ptr());

  sub_ps.bind_texture("depth_buffer", &resources.depth_tx);
  sub_ps.bind_texture("stencil_tx", &stencil_tx_);
  sub_ps.bind_texture("density_tx", grid->texture);
  /* TODO: implement shadow texture, see manta_smoke_calc_transparency. */
  sub_ps.bind_texture("shadow_tx", dummy_shadow_tx_);
  sub_ps.push_constant("active_color", color);
  sub_ps.push_constant("density_fac", density_fac);
  sub_ps.push_constant("volume_object_to_texture", float4x4(grid->object_to_texture));
  sub_ps.push_constant("volume_texture_to_object", float4x4(grid->texture_to_object));

  if (use_slice) {
    draw_slice_ps(
        manager, resources, sub_ps, ob_ref, volume.display.slice_axis, volume.display.slice_depth);
  }
  else {
    float4x4 texture_to_world = ob->object_to_world() * float4x4(grid->texture_to_object);
    float3 world_size = math::to_scale(texture_to_world);

    int3 resolution;
    GPU_texture_get_mipmap_size(grid->texture, 0, resolution);
    float3 slice_count = float3(resolution) * 5.0f;

    draw_volume_ps(
        manager, resources, sub_ps, ob_ref, scene_state.sample, slice_count, world_size);
  }
}

void VolumePass::object_sync_modifier(Manager &manager,
                                      SceneResources &resources,
                                      const SceneState &scene_state,
                                      ObjectRef &ob_ref,
                                      ModifierData *md)
{
  Object *ob = ob_ref.object;

  FluidModifierData *modifier = reinterpret_cast<FluidModifierData *>(md);
  FluidDomainSettings &settings = *modifier->domain;

  if (!settings.fluid) {
    return;
  }

  bool can_load = false;
  if (settings.use_coba) {
    DRW_smoke_ensure_coba_field(modifier);
    can_load = settings.tex_field != nullptr;
  }
  else if (settings.type == FLUID_DOMAIN_TYPE_GAS) {
    DRW_smoke_ensure(modifier, settings.flags & FLUID_DOMAIN_USE_NOISE);
    can_load = settings.tex_density != nullptr || settings.tex_color != nullptr;
  }

  if (!can_load) {
    return;
  }

  active_ = true;

  PassMain::Sub &sub_ps = ps_.sub("Volume Modifier SubPass");

  const bool use_slice = settings.axis_slice_method == AXIS_SLICE_SINGLE;

  sub_ps.shader_set(
      ShaderCache::get().volume_get(true, settings.interp_method, settings.use_coba, use_slice));
  sub_ps.push_constant("do_depth_test", scene_state.shading.type >= OB_SOLID);

  if (settings.use_coba) {
    const bool show_flags = settings.coba_field == FLUID_DOMAIN_FIELD_FLAGS;
    const bool show_pressure = settings.coba_field == FLUID_DOMAIN_FIELD_PRESSURE;
    const bool show_phi = ELEM(settings.coba_field,
                               FLUID_DOMAIN_FIELD_PHI,
                               FLUID_DOMAIN_FIELD_PHI_IN,
                               FLUID_DOMAIN_FIELD_PHI_OUT,
                               FLUID_DOMAIN_FIELD_PHI_OBSTACLE);

    sub_ps.push_constant("show_flags", show_flags);
    sub_ps.push_constant("show_pressure", show_pressure);
    sub_ps.push_constant("show_phi", show_phi);
    sub_ps.push_constant("grid_scale", settings.grid_scale);

    if (show_flags) {
      sub_ps.bind_texture("flag_tx", settings.tex_field);
    }
    else {
      sub_ps.bind_texture("density_tx", settings.tex_field);
    }

    if (!show_flags && !show_pressure && !show_phi) {
      sub_ps.bind_texture("transfer_tx", settings.tex_coba);
    }
  }
  else {
    bool use_constant_color = ((settings.active_fields & FLUID_DOMAIN_ACTIVE_COLORS) == 0 &&
                               (settings.active_fields & FLUID_DOMAIN_ACTIVE_COLOR_SET) != 0);

    sub_ps.push_constant("active_color",
                         use_constant_color ? float3(settings.active_color) : float3(1));

    sub_ps.bind_texture("density_tx",
                        settings.tex_color ? settings.tex_color : settings.tex_density);
    sub_ps.bind_texture("flame_tx", settings.tex_flame ? settings.tex_flame : dummy_volume_tx_);
    sub_ps.bind_texture("flame_color_tx",
                        settings.tex_flame ? settings.tex_flame_coba : dummy_coba_tx_);
    sub_ps.bind_texture("shadow_tx", settings.tex_shadow);
  }

  sub_ps.push_constant("density_fac", 10.0f * settings.display_thickness);
  sub_ps.bind_texture("depth_buffer", &resources.depth_tx);
  sub_ps.bind_texture("stencil_tx", &stencil_tx_);

  if (use_slice) {
    draw_slice_ps(manager, resources, sub_ps, ob_ref, settings.slice_axis, settings.slice_depth);
  }
  else {
    float3 world_size;
    BKE_object_dimensions_get(ob, world_size);

    float3 slice_count = float3(settings.res) * std::max(0.001f, settings.slice_per_voxel);

    draw_volume_ps(
        manager, resources, sub_ps, ob_ref, scene_state.sample, slice_count, world_size);
  }
}

void VolumePass::draw(Manager &manager, View &view, SceneResources &resources)
{
  if (!active_) {
    return;
  }

  stencil_tx_ = resources.depth_tx.ptr()->stencil_view();

  fb_.ensure(GPU_ATTACHMENT_NONE, GPU_ATTACHMENT_TEXTURE(resources.color_tx));
  fb_.bind();
  manager.submit(ps_, view);
}

void VolumePass::draw_slice_ps(Manager &manager,
                               SceneResources &resources,
                               PassMain::Sub &ps,
                               ObjectRef &ob_ref,
                               int slice_axis_enum,
                               float slice_depth)
{
  float4x4 view_mat_inv = blender::draw::View::default_get().viewinv();

  const int axis = (slice_axis_enum == SLICE_AXIS_AUTO) ?
                       axis_dominant_v3_single(view_mat_inv[2]) :
                       slice_axis_enum - 1;

  float3 dimensions;
  BKE_object_dimensions_get(ob_ref.object, dimensions);
  /* 0.05f to achieve somewhat the same opacity as the full view. */
  float step_length = std::max(1e-16f, dimensions[axis] * 0.05f);

  ps.state_set(DRW_STATE_WRITE_COLOR | DRW_STATE_BLEND_ALPHA_PREMUL | DRW_STATE_CULL_FRONT);
  ps.push_constant("slice_position", slice_depth);
  ps.push_constant("slice_axis", axis);
  ps.push_constant("step_length", step_length);

  ps.draw(resources.volume_cube_batch, manager.unique_handle(ob_ref));
}

void VolumePass::draw_volume_ps(Manager &manager,
                                SceneResources &resources,
                                PassMain::Sub &ps,
                                ObjectRef &ob_ref,
                                int taa_sample,
                                float3 slice_count,
                                float3 world_size)
{
  double noise_offset;
  BLI_halton_1d(3, 0.0, taa_sample, &noise_offset);

  int max_slice = std::max({UNPACK3(slice_count)});
  float step_length = math::length((1.0f / slice_count) * world_size);

  ps.state_set(DRW_STATE_WRITE_COLOR | DRW_STATE_BLEND_ALPHA_PREMUL | DRW_STATE_CULL_FRONT);
  ps.push_constant("samples_len", max_slice);
  ps.push_constant("step_length", step_length);
  ps.push_constant("noise_ofs", float(noise_offset));

  ps.draw(resources.volume_cube_batch, manager.unique_handle(ob_ref));
}

}  // namespace blender::workbench

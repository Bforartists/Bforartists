/* SPDX-FileCopyrightText: 2021 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup eevee
 *
 * A view is either:
 * - The entire main view.
 * - A fragment of the main view (for panoramic projections).
 * - A shadow map view.
 * - A light-probe view (either planar, cube-map, irradiance grid).
 *
 * A pass is a container for scene data. It is view agnostic but has specific logic depending on
 * its type. Passes are shared between views.
 */

#include "BKE_global.h"
#include "DRW_render.h"

#include "eevee_instance.hh"

#include "eevee_view.hh"

namespace blender::eevee {

/* -------------------------------------------------------------------- */
/** \name ShadingView
 * \{ */

void ShadingView::init()
{
  // dof_.init();
  // mb_.init();
}

void ShadingView::sync()
{
  int2 render_extent = inst_.film.render_extent_get();

  if (false /* inst_.camera.is_panoramic() */) {
    int64_t render_pixel_count = render_extent.x * int64_t(render_extent.y);
    /* Divide pixel count between the 6 views. Rendering to a square target. */
    extent_[0] = extent_[1] = ceilf(sqrtf(1 + (render_pixel_count / 6)));
    /* TODO(@fclem): Clip unused views here. */
    is_enabled_ = true;
  }
  else {
    extent_ = render_extent;
    /* Only enable -Z view. */
    is_enabled_ = (StringRefNull(name_) == "negZ_view");
  }

  if (!is_enabled_) {
    return;
  }

  /* Create views. */
  const CameraData &cam = inst_.camera.data_get();

  float4x4 viewmat, winmat;
  const float(*viewmat_p)[4] = viewmat.ptr(), (*winmat_p)[4] = winmat.ptr();
  if (false /* inst_.camera.is_panoramic() */) {
    /* TODO(@fclem) Over-scans. */
    /* For now a mandatory 5% over-scan for DoF. */
    float side = cam.clip_near * 1.05f;
    float near = cam.clip_near;
    float far = cam.clip_far;
    perspective_m4(winmat.ptr(), -side, side, -side, side, near, far);
    viewmat = face_matrix_ * cam.viewmat;
  }
  else {
    viewmat_p = cam.viewmat.ptr();
    winmat_p = cam.winmat.ptr();
  }

  main_view_ = DRW_view_create(viewmat_p, winmat_p, nullptr, nullptr, nullptr);
  sub_view_ = DRW_view_create_sub(main_view_, viewmat_p, winmat_p);
  render_view_ = DRW_view_create_sub(main_view_, viewmat_p, winmat_p);

  // dof_.sync(winmat_p, extent_);
  // rt_buffer_opaque_.sync(extent_);
  // rt_buffer_refract_.sync(extent_);
  // inst_.hiz_back.view_sync(extent_);
  // inst_.hiz_front.view_sync(extent_);
  // inst_.gbuffer.view_sync(extent_);
}

void ShadingView::render()
{
  if (!is_enabled_) {
    return;
  }

  /* Query temp textures and create frame-buffers. */
  RenderBuffers &rbufs = inst_.render_buffers;
  rbufs.acquire(extent_);
  combined_fb_.ensure(GPU_ATTACHMENT_TEXTURE(rbufs.depth_tx),
                      GPU_ATTACHMENT_TEXTURE(rbufs.combined_tx));
  prepass_fb_.ensure(GPU_ATTACHMENT_TEXTURE(rbufs.depth_tx),
                     GPU_ATTACHMENT_TEXTURE(rbufs.vector_tx));

  update_view();

  DRW_stats_group_start(name_);
  DRW_view_set_active(render_view_);

  inst_.planar_probes.set_view(render_view_new_, extent_);

  /* If camera has any motion, compute motion vector in the film pass. Otherwise, we avoid float
   * precision issue by setting the motion of all static geometry to 0. */
  float4 clear_velocity = float4(inst_.velocity.camera_has_motion() ? VELOCITY_INVALID : 0.0f);

  GPU_framebuffer_bind(prepass_fb_);
  GPU_framebuffer_clear_color(prepass_fb_, clear_velocity);
  /* Alpha stores transmittance. So start at 1. */
  float4 clear_color = {0.0f, 0.0f, 0.0f, 1.0f};
  GPU_framebuffer_bind(combined_fb_);
  GPU_framebuffer_clear_color_depth(combined_fb_, clear_color, 1.0f);

  inst_.hiz_buffer.set_source(&inst_.render_buffers.depth_tx);
  inst_.hiz_buffer.set_dirty();

  inst_.pipelines.background.render(render_view_new_);

  /* TODO(fclem): Move it after the first prepass (and hiz update) once pipeline is stabilized. */
  inst_.lights.set_view(render_view_new_, extent_);
  inst_.reflection_probes.set_view(render_view_new_);

  inst_.volume.draw_prepass(render_view_new_);

  /* TODO: cleanup. */
  View main_view_new("MainView", main_view_);
  /* TODO(Miguel Pozo): Deferred and forward prepass should happen before the GBuffer pass. */
  inst_.pipelines.deferred.render(main_view_new,
                                  render_view_new_,
                                  prepass_fb_,
                                  combined_fb_,
                                  extent_,
                                  rt_buffer_opaque_,
                                  rt_buffer_refract_);

  inst_.volume.draw_compute(render_view_new_);

  // inst_.lookdev.render_overlay(view_fb_);

  inst_.pipelines.forward.render(render_view_new_, prepass_fb_, combined_fb_, rbufs.combined_tx);

  inst_.lights.debug_draw(render_view_new_, combined_fb_);
  inst_.hiz_buffer.debug_draw(render_view_new_, combined_fb_);
  inst_.shadows.debug_draw(render_view_new_, combined_fb_);
  inst_.irradiance_cache.viewport_draw(render_view_new_, combined_fb_);
  inst_.reflection_probes.viewport_draw(render_view_new_, combined_fb_);
  inst_.planar_probes.viewport_draw(render_view_new_, combined_fb_);

  inst_.ambient_occlusion.render_pass(render_view_new_);

  GPUTexture *combined_final_tx = render_postfx(rbufs.combined_tx);
  inst_.film.accumulate(sub_view_, combined_final_tx);

  rbufs.release();
  postfx_tx_.release();

  DRW_stats_group_end();
}

GPUTexture *ShadingView::render_postfx(GPUTexture *input_tx)
{
  if (!inst_.depth_of_field.postfx_enabled() && !inst_.motion_blur.postfx_enabled()) {
    return input_tx;
  }
  postfx_tx_.acquire(extent_, GPU_RGBA16F);

  GPUTexture *output_tx = postfx_tx_;

  /* Swapping is done internally. Actual output is set to the next input. */
  inst_.depth_of_field.render(render_view_new_, &input_tx, &output_tx, dof_buffer_);
  inst_.motion_blur.render(render_view_new_, &input_tx, &output_tx);

  return input_tx;
}

void ShadingView::update_view()
{
  float4x4 viewmat, winmat;
  DRW_view_viewmat_get(main_view_, viewmat.ptr(), false);
  DRW_view_winmat_get(main_view_, winmat.ptr(), false);

  /* TODO(fclem): Mixed-resolution rendering: We need to make sure we render with exactly the same
   * distances between pixels to line up render samples and target pixels.
   * So if the target resolution is not a multiple of the resolution divisor, we need to make the
   * projection window bigger in the +X and +Y directions. */

  /* Anti-Aliasing / Super-Sampling jitter. */
  float2 jitter = inst_.film.pixel_jitter_get() / float2(extent_);
  /* Transform to NDC space. */
  jitter *= 2.0f;

  window_translate_m4(winmat.ptr(), winmat.ptr(), UNPACK2(jitter));
  DRW_view_update_sub(sub_view_, viewmat.ptr(), winmat.ptr());

  /* FIXME(fclem): The offset may be noticeably large and the culling might make object pop
   * out of the blurring radius. To fix this, use custom enlarged culling matrix. */
  inst_.depth_of_field.jitter_apply(winmat, viewmat);
  DRW_view_update_sub(render_view_, viewmat.ptr(), winmat.ptr());

  render_view_new_.sync(viewmat, winmat);
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Capture View
 * \{ */

void CaptureView::render_world()
{
  const std::optional<ReflectionProbeUpdateInfo> update_info =
      inst_.reflection_probes.update_info_pop(ReflectionProbe::Type::WORLD);
  if (!update_info.has_value()) {
    return;
  }

  View view = {"Capture.View"};
  GPU_debug_group_begin("World.Capture");

  if (update_info->do_render) {
    for (int face : IndexRange(6)) {
      float4x4 view_m4 = cubeface_mat(face);
      float4x4 win_m4 = math::projection::perspective(-update_info->clipping_distances.x,
                                                      update_info->clipping_distances.x,
                                                      -update_info->clipping_distances.x,
                                                      update_info->clipping_distances.x,
                                                      update_info->clipping_distances.x,
                                                      update_info->clipping_distances.y);
      view.sync(view_m4, win_m4);

      capture_fb_.ensure(
          GPU_ATTACHMENT_NONE,
          GPU_ATTACHMENT_TEXTURE_CUBEFACE(inst_.reflection_probes.cubemap_tx_, face));
      GPU_framebuffer_bind(capture_fb_);
      inst_.pipelines.world.render(view);
    }

    inst_.reflection_probes.remap_to_octahedral_projection(update_info->atlas_coord);
    inst_.reflection_probes.update_probes_texture_mipmaps();
  }

  if (update_info->do_world_irradiance_update) {
    inst_.reflection_probes.update_world_irradiance();
  }

  GPU_debug_group_end();
}

void CaptureView::render_probes()
{
  Framebuffer prepass_fb;
  View view = {"Capture.View"};
  bool do_update_mipmap_chain = false;
  while (const std::optional<ReflectionProbeUpdateInfo> update_info =
             inst_.reflection_probes.update_info_pop(ReflectionProbe::Type::PROBE))
  {
    GPU_debug_group_begin("Probe.Capture");
    do_update_mipmap_chain = true;

    int2 extent = int2(update_info->resolution);
    inst_.render_buffers.acquire(extent);

    inst_.render_buffers.vector_tx.clear(float4(0.0f));
    prepass_fb.ensure(GPU_ATTACHMENT_TEXTURE(inst_.render_buffers.depth_tx),
                      GPU_ATTACHMENT_TEXTURE(inst_.render_buffers.vector_tx));

    for (int face : IndexRange(6)) {
      float4x4 view_m4 = cubeface_mat(face);
      view_m4 = math::translate(view_m4, -update_info->probe_pos);
      float4x4 win_m4 = math::projection::perspective(-update_info->clipping_distances.x,
                                                      update_info->clipping_distances.x,
                                                      -update_info->clipping_distances.x,
                                                      update_info->clipping_distances.x,
                                                      update_info->clipping_distances.x,
                                                      update_info->clipping_distances.y);
      view.sync(view_m4, win_m4);

      capture_fb_.ensure(
          GPU_ATTACHMENT_TEXTURE(inst_.render_buffers.depth_tx),
          GPU_ATTACHMENT_TEXTURE_CUBEFACE(inst_.reflection_probes.cubemap_tx_, face));

      GPU_framebuffer_bind(capture_fb_);
      GPU_framebuffer_clear_color_depth(capture_fb_, float4(0.0f, 0.0f, 0.0f, 1.0f), 1.0f);
      inst_.pipelines.probe.render(view, prepass_fb, capture_fb_, extent);
    }

    inst_.render_buffers.release();
    GPU_debug_group_end();
    inst_.reflection_probes.remap_to_octahedral_projection(update_info->atlas_coord);
  }

  if (do_update_mipmap_chain) {
    /* TODO: only update the regions that have been updated. */
    inst_.reflection_probes.update_probes_texture_mipmaps();
  }
}

/** \} */

}  // namespace blender::eevee

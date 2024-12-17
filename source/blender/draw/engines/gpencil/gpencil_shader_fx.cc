/* SPDX-FileCopyrightText: 2017 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup draw
 */
#include "DNA_camera_types.h"
#include "DNA_gpencil_legacy_types.h"
#include "DNA_shader_fx_types.h"
#include "DNA_view3d_types.h"

#include "BKE_gpencil_legacy.h"

#include "BLI_link_utils.h"
#include "BLI_memblock.h"

#include "DRW_render.hh"

#include "BKE_camera.h"

#include "gpencil_engine.h"

using namespace blender::draw;

/* verify if this fx is active */
static bool effect_is_active(ShaderFxData *fx, bool is_edit, bool is_viewport)
{
  if (fx == nullptr) {
    return false;
  }

  if (((fx->mode & eShaderFxMode_Editmode) == 0) && (is_edit) && (is_viewport)) {
    return false;
  }

  if (((fx->mode & eShaderFxMode_Realtime) && (is_viewport == true)) ||
      ((fx->mode & eShaderFxMode_Render) && (is_viewport == false)))
  {
    return true;
  }

  return false;
}

struct gpIterVfxData {
  GPENCIL_PrivateData *pd;
  GPENCIL_tObject *tgp_ob;
  GPUFrameBuffer **target_fb;
  GPUFrameBuffer **source_fb;
  GPUTexture **target_color_tx;
  GPUTexture **source_color_tx;
  GPUTexture **target_reveal_tx;
  GPUTexture **source_reveal_tx;
};

static PassSimple &gpencil_vfx_pass_create(
    const char *name,
    DRWState state,
    gpIterVfxData *iter,
    GPUShader *sh,
    GPUSamplerState sampler = GPUSamplerState::internal_sampler())
{
  UNUSED_VARS(name);

  int64_t id = iter->pd->gp_vfx_pool->append_and_get_index({});
  GPENCIL_tVfx *tgp_vfx = &(*iter->pd->gp_vfx_pool)[id];
  tgp_vfx->target_fb = iter->target_fb;

  PassSimple &pass = *tgp_vfx->vfx_ps;
  pass.init();
  pass.state_set(state);
  pass.shader_set(sh);
  pass.bind_texture("colorBuf", iter->source_color_tx, sampler);
  pass.bind_texture("revealBuf", iter->source_reveal_tx, sampler);

  std::swap(iter->target_fb, iter->source_fb);
  std::swap(iter->target_color_tx, iter->source_color_tx);
  std::swap(iter->target_reveal_tx, iter->source_reveal_tx);

  BLI_LINKS_APPEND(&iter->tgp_ob->vfx, tgp_vfx);

  return pass;
}

static void gpencil_vfx_blur(BlurShaderFxData *fx, Object *ob, gpIterVfxData *iter)
{
  if ((fx->samples == 0.0f) || (fx->radius[0] == 0.0f && fx->radius[1] == 0.0f)) {
    return;
  }

  if ((fx->flag & FX_BLUR_DOF_MODE) && iter->pd->camera == nullptr) {
    /* No blur outside camera view (or when DOF is disabled on the camera). */
    return;
  }

  const float s = sin(fx->rotation);
  const float c = cos(fx->rotation);

  float4x4 winmat, persmat;
  float blur_size[2] = {fx->radius[0], fx->radius[1]};
  persmat = blender::draw::View::default_get().persmat();
  const float w = fabsf(mul_project_m4_v3_zfac(persmat.ptr(), ob->object_to_world().location()));

  if (fx->flag & FX_BLUR_DOF_MODE) {
    /* Compute circle of confusion size. */
    float coc = (iter->pd->dof_params[0] / -w) - iter->pd->dof_params[1];
    copy_v2_fl(blur_size, fabsf(coc));
  }
  else {
    /* Modify by distance to camera and object scale. */
    winmat = blender::draw::View::default_get().winmat();
    const float *vp_size = DRW_viewport_size_get();
    float world_pixel_scale = 1.0f / GPENCIL_PIXEL_FACTOR;
    float scale = mat4_to_scale(ob->object_to_world().ptr());
    float distance_factor = world_pixel_scale * scale * winmat[1][1] * vp_size[1] / w;
    mul_v2_fl(blur_size, distance_factor);
  }

  GPUShader *sh = GPENCIL_shader_fx_blur_get();

  DRWState state = DRW_STATE_WRITE_COLOR;
  if (blur_size[0] > 0.0f) {
    auto &grp = gpencil_vfx_pass_create("Fx Blur H", state, iter, sh);
    grp.push_constant("offset", float2(blur_size[0] * c, blur_size[0] * s));
    grp.push_constant("sampCount", max_ii(1, min_ii(fx->samples, blur_size[0])));
    grp.draw_procedural(GPU_PRIM_TRIS, 1, 3);
  }
  if (blur_size[1] > 0.0f) {
    auto &grp = gpencil_vfx_pass_create("Fx Blur V", state, iter, sh);
    grp.push_constant("offset", float2(-blur_size[1] * s, blur_size[1] * c));
    grp.push_constant("sampCount", max_ii(1, min_ii(fx->samples, blur_size[1])));
    grp.draw_procedural(GPU_PRIM_TRIS, 1, 3);
  }
}

static void gpencil_vfx_colorize(ColorizeShaderFxData *fx, Object * /*ob*/, gpIterVfxData *iter)
{
  GPUShader *sh = GPENCIL_shader_fx_colorize_get();

  DRWState state = DRW_STATE_WRITE_COLOR;
  auto &grp = gpencil_vfx_pass_create("Fx Colorize", state, iter, sh);
  grp.push_constant("lowColor", float3(fx->low_color));
  grp.push_constant("highColor", float3(fx->high_color));
  grp.push_constant("factor", fx->factor);
  grp.push_constant("mode", fx->mode);
  grp.draw_procedural(GPU_PRIM_TRIS, 1, 3);
}

static void gpencil_vfx_flip(FlipShaderFxData *fx, Object * /*ob*/, gpIterVfxData *iter)
{
  float axis_flip[2];
  axis_flip[0] = (fx->flag & FX_FLIP_HORIZONTAL) ? -1.0f : 1.0f;
  axis_flip[1] = (fx->flag & FX_FLIP_VERTICAL) ? -1.0f : 1.0f;

  GPUShader *sh = GPENCIL_shader_fx_transform_get();

  DRWState state = DRW_STATE_WRITE_COLOR;
  auto &grp = gpencil_vfx_pass_create("Fx Flip", state, iter, sh);
  grp.push_constant("axisFlip", float2(axis_flip));
  grp.push_constant("waveOffset", float2(0.0f, 0.0f));
  grp.push_constant("swirlRadius", 0.0f);
  grp.draw_procedural(GPU_PRIM_TRIS, 1, 3);
}

static void gpencil_vfx_rim(RimShaderFxData *fx, Object *ob, gpIterVfxData *iter)
{
  float4x4 winmat, persmat;
  float offset[2] = {float(fx->offset[0]), float(fx->offset[1])};
  float blur_size[2] = {float(fx->blur[0]), float(fx->blur[1])};
  winmat = blender::draw::View::default_get().winmat();
  persmat = blender::draw::View::default_get().persmat();
  const float *vp_size = DRW_viewport_size_get();
  const float *vp_size_inv = DRW_viewport_invert_size_get();

  const float w = fabsf(mul_project_m4_v3_zfac(persmat.ptr(), ob->object_to_world().location()));

  /* Modify by distance to camera and object scale. */
  float world_pixel_scale = 1.0f / GPENCIL_PIXEL_FACTOR;
  float scale = mat4_to_scale(ob->object_to_world().ptr());
  float distance_factor = (world_pixel_scale * scale * winmat[1][1] * vp_size[1]) / w;
  mul_v2_fl(offset, distance_factor);
  mul_v2_v2(offset, vp_size_inv);
  mul_v2_fl(blur_size, distance_factor);

  GPUShader *sh = GPENCIL_shader_fx_rim_get();

  {
    DRWState state = DRW_STATE_WRITE_COLOR;
    auto &grp = gpencil_vfx_pass_create("Fx Rim H", state, iter, sh);
    grp.push_constant("blurDir", float2(blur_size[0] * vp_size_inv[0], 0.0f));
    grp.push_constant("uvOffset", float2(offset));
    grp.push_constant("sampCount", max_ii(1, min_ii(fx->samples, blur_size[0])));
    grp.push_constant("maskColor", float3(fx->mask_rgb));
    grp.push_constant("isFirstPass", true);
    grp.draw_procedural(GPU_PRIM_TRIS, 1, 3);
  }

  {
    DRWState state = DRW_STATE_WRITE_COLOR;
    switch (fx->mode) {
      case eShaderFxRimMode_Normal:
        state |= DRW_STATE_BLEND_ALPHA_PREMUL;
        break;
      case eShaderFxRimMode_Add:
        state |= DRW_STATE_BLEND_ADD_FULL;
        break;
      case eShaderFxRimMode_Subtract:
        state |= DRW_STATE_BLEND_SUB;
        break;
      case eShaderFxRimMode_Multiply:
      case eShaderFxRimMode_Divide:
      case eShaderFxRimMode_Overlay:
        state |= DRW_STATE_BLEND_MUL;
        break;
    }

    zero_v2(offset);

    auto &grp = gpencil_vfx_pass_create("Fx Rim V", state, iter, sh);
    grp.push_constant("blurDir", float2(0.0f, blur_size[1] * vp_size_inv[1]));
    grp.push_constant("uvOffset", float2(offset));
    grp.push_constant("rimColor", float3(fx->rim_rgb));
    grp.push_constant("sampCount", max_ii(1, min_ii(fx->samples, blur_size[1])));
    grp.push_constant("blendMode", fx->mode);
    grp.push_constant("isFirstPass", false);
    grp.draw_procedural(GPU_PRIM_TRIS, 1, 3);

    if (fx->mode == eShaderFxRimMode_Overlay) {
      /* We cannot do custom blending on multi-target frame-buffers.
       * Workaround by doing 2 passes. */
      grp.state_set(DRW_STATE_WRITE_COLOR | DRW_STATE_BLEND_ADD_FULL);
      grp.push_constant("blendMode", 999);
      grp.draw_procedural(GPU_PRIM_TRIS, 1, 3);
    }
  }
}

static void gpencil_vfx_pixelize(PixelShaderFxData *fx, Object *ob, gpIterVfxData *iter)
{
  float4x4 persmat, winmat;
  float ob_center[3], pixsize_uniform[2];
  winmat = blender::draw::View::default_get().winmat();
  persmat = blender::draw::View::default_get().persmat();
  const float *vp_size = DRW_viewport_size_get();
  const float *vp_size_inv = DRW_viewport_invert_size_get();
  float pixel_size[2] = {float(fx->size[0]), float(fx->size[1])};
  mul_v2_v2(pixel_size, vp_size_inv);

  /* Fixed pixelisation center from object center. */
  const float w = fabsf(mul_project_m4_v3_zfac(persmat.ptr(), ob->object_to_world().location()));
  mul_v3_m4v3(ob_center, persmat.ptr(), ob->object_to_world().location());
  mul_v3_fl(ob_center, 1.0f / w);

  const bool use_antialiasing = ((fx->flag & FX_PIXEL_FILTER_NEAREST) == 0);

  /* Convert to uvs. */
  mul_v2_fl(ob_center, 0.5f);
  add_v2_fl(ob_center, 0.5f);

  /* Modify by distance to camera and object scale. */
  float world_pixel_scale = 1.0f / GPENCIL_PIXEL_FACTOR;
  float scale = mat4_to_scale(ob->object_to_world().ptr());
  mul_v2_fl(pixel_size, (world_pixel_scale * scale * winmat[1][1] * vp_size[1]) / w);

  /* Center to texel */
  madd_v2_v2fl(ob_center, pixel_size, -0.5f);

  GPUShader *sh = GPENCIL_shader_fx_pixelize_get();

  DRWState state = DRW_STATE_WRITE_COLOR;

  /* Only if pixelated effect is bigger than 1px. */
  if (pixel_size[0] > vp_size_inv[0]) {
    copy_v2_fl2(pixsize_uniform, pixel_size[0], vp_size_inv[1]);
    GPUSamplerState sampler = (use_antialiasing) ? GPUSamplerState::internal_sampler() :
                                                   GPUSamplerState::default_sampler();

    auto &grp = gpencil_vfx_pass_create("Fx Pixelize X", state, iter, sh, sampler);
    grp.push_constant("targetPixelSize", float2(pixsize_uniform));
    grp.push_constant("targetPixelOffset", float2(ob_center));
    grp.push_constant("accumOffset", float2(pixel_size[0], 0.0f));
    int samp_count = (pixel_size[0] / vp_size_inv[0] > 3.0) ? 2 : 1;
    grp.push_constant("sampCount", int(use_antialiasing ? samp_count : 0));
    grp.draw_procedural(GPU_PRIM_TRIS, 1, 3);
  }

  if (pixel_size[1] > vp_size_inv[1]) {
    GPUSamplerState sampler = (use_antialiasing) ? GPUSamplerState::internal_sampler() :
                                                   GPUSamplerState::default_sampler();
    copy_v2_fl2(pixsize_uniform, vp_size_inv[0], pixel_size[1]);
    auto &grp = gpencil_vfx_pass_create("Fx Pixelize Y", state, iter, sh, sampler);
    grp.push_constant("targetPixelSize", float2(pixsize_uniform));
    grp.push_constant("accumOffset", float2(0.0f, pixel_size[1]));
    int samp_count = (pixel_size[1] / vp_size_inv[1] > 3.0) ? 2 : 1;
    grp.push_constant("sampCount", int(use_antialiasing ? samp_count : 0));
    grp.draw_procedural(GPU_PRIM_TRIS, 1, 3);
  }
}

static void gpencil_vfx_shadow(ShadowShaderFxData *fx, Object *ob, gpIterVfxData *iter)
{
  const bool use_obj_pivot = (fx->flag & FX_SHADOW_USE_OBJECT) != 0;
  const bool use_wave = (fx->flag & FX_SHADOW_USE_WAVE) != 0;

  float4x4 uv_mat, winmat, persmat;
  float rot_center[3];
  float wave_ofs[3], wave_dir[3], wave_phase, blur_dir[2], tmp[2];
  float offset[2] = {float(fx->offset[0]), float(fx->offset[1])};
  float blur_size[2] = {float(fx->blur[0]), float(fx->blur[1])};
  winmat = blender::draw::View::default_get().winmat();
  persmat = blender::draw::View::default_get().persmat();
  const float *vp_size = DRW_viewport_size_get();
  const float *vp_size_inv = DRW_viewport_invert_size_get();
  const float ratio = vp_size_inv[1] / vp_size_inv[0];

  copy_v3_v3(rot_center,
             (use_obj_pivot && fx->object) ? fx->object->object_to_world().location() :
                                             ob->object_to_world().location());

  const float w = fabsf(mul_project_m4_v3_zfac(persmat.ptr(), rot_center));
  mul_v3_m4v3(rot_center, persmat.ptr(), rot_center);
  mul_v3_fl(rot_center, 1.0f / w);

  /* Modify by distance to camera and object scale. */
  float world_pixel_scale = 1.0f / GPENCIL_PIXEL_FACTOR;
  float scale = mat4_to_scale(ob->object_to_world().ptr());
  float distance_factor = (world_pixel_scale * scale * winmat[1][1] * vp_size[1]) / w;
  mul_v2_fl(offset, distance_factor);
  mul_v2_v2(offset, vp_size_inv);
  mul_v2_fl(blur_size, distance_factor);

  rot_center[0] = rot_center[0] * 0.5f + 0.5f;
  rot_center[1] = rot_center[1] * 0.5f + 0.5f;

  /* UV transform matrix. (loc, rot, scale) Sent to shader as 2x3 matrix. */
  unit_m4(uv_mat.ptr());
  translate_m4(uv_mat.ptr(), rot_center[0], rot_center[1], 0.0f);
  rescale_m4(uv_mat.ptr(), blender::float3{1.0f / fx->scale[0], 1.0f / fx->scale[1], 1.0f});
  translate_m4(uv_mat.ptr(), -offset[0], -offset[1], 0.0f);
  rescale_m4(uv_mat.ptr(), blender::float3{1.0f / ratio, 1.0f, 1.0f});
  rotate_m4(uv_mat.ptr(), 'Z', fx->rotation);
  rescale_m4(uv_mat.ptr(), blender::float3{ratio, 1.0f, 1.0f});
  translate_m4(uv_mat.ptr(), -rot_center[0], -rot_center[1], 0.0f);

  if (use_wave) {
    float dir[2];
    if (fx->orientation == 0) {
      /* Horizontal */
      copy_v2_fl2(dir, 1.0f, 0.0f);
    }
    else {
      /* Vertical */
      copy_v2_fl2(dir, 0.0f, 1.0f);
    }
    /* This is applied after rotation. Counter the rotation to keep aligned with global axis. */
    rotate_v2_v2fl(wave_dir, dir, fx->rotation);
    /* Rotate 90 degrees. */
    copy_v2_v2(wave_ofs, wave_dir);
    std::swap(wave_ofs[0], wave_ofs[1]);
    wave_ofs[1] *= -1.0f;
    /* Keep world space scaling and aspect ratio. */
    mul_v2_fl(wave_dir, 1.0f / (max_ff(1e-8f, fx->period) * distance_factor));
    mul_v2_v2(wave_dir, vp_size);
    mul_v2_fl(wave_ofs, fx->amplitude * distance_factor);
    mul_v2_v2(wave_ofs, vp_size_inv);
    /* Phase start at shadow center. */
    wave_phase = fx->phase - dot_v2v2(rot_center, wave_dir);
  }
  else {
    zero_v2(wave_dir);
    zero_v2(wave_ofs);
    wave_phase = 0.0f;
  }

  GPUShader *sh = GPENCIL_shader_fx_shadow_get();

  copy_v2_fl2(blur_dir, blur_size[0] * vp_size_inv[0], 0.0f);

  {
    DRWState state = DRW_STATE_WRITE_COLOR;
    auto &grp = gpencil_vfx_pass_create("Fx Shadow H", state, iter, sh);
    grp.push_constant("blurDir", float2(blur_dir));
    grp.push_constant("waveDir", float2(wave_dir));
    grp.push_constant("waveOffset", float2(wave_ofs));
    grp.push_constant("wavePhase", wave_phase);
    grp.push_constant("uvRotX", float2(uv_mat[0]));
    grp.push_constant("uvRotY", float2(uv_mat[1]));
    grp.push_constant("uvOffset", float2(uv_mat[3]));
    grp.push_constant("sampCount", max_ii(1, min_ii(fx->samples, blur_size[0])));
    grp.push_constant("isFirstPass", true);
    grp.draw_procedural(GPU_PRIM_TRIS, 1, 3);
  }

  unit_m4(uv_mat.ptr());
  zero_v2(wave_ofs);

  /* Reset the `uv_mat` to account for rotation in the Y-axis (Shadow-V parameter). */
  copy_v2_fl2(tmp, 0.0f, blur_size[1]);
  rotate_v2_v2fl(blur_dir, tmp, -fx->rotation);
  mul_v2_v2(blur_dir, vp_size_inv);

  {
    DRWState state = DRW_STATE_WRITE_COLOR | DRW_STATE_BLEND_ALPHA_PREMUL;
    auto &grp = gpencil_vfx_pass_create("Fx Shadow V", state, iter, sh);
    grp.push_constant("shadowColor", float4(fx->shadow_rgba));
    grp.push_constant("blurDir", float2(blur_dir));
    grp.push_constant("waveOffset", float2(wave_ofs));
    grp.push_constant("uvRotX", float2(uv_mat[0]));
    grp.push_constant("uvRotY", float2(uv_mat[1]));
    grp.push_constant("uvOffset", float2(uv_mat[3]));
    grp.push_constant("sampCount", max_ii(1, min_ii(fx->samples, blur_size[1])));
    grp.push_constant("isFirstPass", false);
    grp.draw_procedural(GPU_PRIM_TRIS, 1, 3);
  }
}

static void gpencil_vfx_glow(GlowShaderFxData *fx, Object * /*ob*/, gpIterVfxData *iter)
{
  const bool use_glow_under = (fx->flag & FX_GLOW_USE_ALPHA) != 0;
  const float s = sin(fx->rotation);
  const float c = cos(fx->rotation);

  GPUShader *sh = GPENCIL_shader_fx_glow_get();

  float ref_col[4];

  if (fx->mode == eShaderFxGlowMode_Luminance) {
    /* Only pass in the first value for luminance. */
    ref_col[0] = fx->threshold;
    ref_col[1] = -1.0f;
    ref_col[2] = -1.0f;
    ref_col[3] = -1.0f;
  }
  else {
    /* First three values are the RGB for the selected color, last value the threshold. */
    copy_v3_v3(ref_col, fx->select_color);
    ref_col[3] = fx->threshold;
  }

  DRWState state = DRW_STATE_WRITE_COLOR;
  auto &grp = gpencil_vfx_pass_create("Fx Glow H", state, iter, sh);
  grp.push_constant("offset", float2(fx->blur[0] * c, fx->blur[0] * s));
  grp.push_constant("sampCount", max_ii(1, min_ii(fx->samples, fx->blur[0])));
  grp.push_constant("threshold", float4(ref_col));
  grp.push_constant("glowColor", float4(fx->glow_color));
  grp.push_constant("glowUnder", use_glow_under);
  grp.push_constant("firstPass", true);
  grp.draw_procedural(GPU_PRIM_TRIS, 1, 3);

  state = DRW_STATE_WRITE_COLOR;
  /* Blending: Force blending. */
  switch (fx->blend_mode) {
    case eGplBlendMode_Regular:
      state |= DRW_STATE_BLEND_ALPHA_PREMUL;
      break;
    case eGplBlendMode_Add:
      state |= DRW_STATE_BLEND_ADD_FULL;
      break;
    case eGplBlendMode_Subtract:
      state |= DRW_STATE_BLEND_SUB;
      break;
    case eGplBlendMode_Multiply:
    case eGplBlendMode_Divide:
      state |= DRW_STATE_BLEND_MUL;
      break;
  }

  /* Small Hack: We ask for RGBA16F buffer if using use_glow_under to store original
   * revealage in alpha channel. */
  if (fx->blend_mode == eGplBlendMode_Subtract || use_glow_under) {
    /* For this effect to propagate, we need a signed floating point buffer. */
    iter->pd->use_signed_fb = true;
  }

  {
    auto &grp = gpencil_vfx_pass_create("Fx Glow V", state, iter, sh);
    grp.push_constant("offset", float2(-fx->blur[1] * s, fx->blur[1] * c));
    grp.push_constant("sampCount", max_ii(1, min_ii(fx->samples, fx->blur[0])));
    grp.push_constant("threshold", blender::float4{-1.0f, -1.0f, -1.0f, -1.0});
    grp.push_constant("glowColor", blender::float4{1.0f, 1.0f, 1.0f, fx->glow_color[3]});
    grp.push_constant("firstPass", false);
    grp.push_constant("blendMode", fx->blend_mode);
    grp.draw_procedural(GPU_PRIM_TRIS, 1, 3);
  }
}

static void gpencil_vfx_wave(WaveShaderFxData *fx, Object *ob, gpIterVfxData *iter)
{
  float4x4 winmat, persmat;
  float wave_center[3];
  float wave_ofs[3], wave_dir[3], wave_phase;
  winmat = blender::draw::View::default_get().winmat();
  persmat = blender::draw::View::default_get().persmat();
  const float *vp_size = DRW_viewport_size_get();
  const float *vp_size_inv = DRW_viewport_invert_size_get();

  const float w = fabsf(mul_project_m4_v3_zfac(persmat.ptr(), ob->object_to_world().location()));
  mul_v3_m4v3(wave_center, persmat.ptr(), ob->object_to_world().location());
  mul_v3_fl(wave_center, 1.0f / w);

  /* Modify by distance to camera and object scale. */
  float world_pixel_scale = 1.0f / GPENCIL_PIXEL_FACTOR;
  float scale = mat4_to_scale(ob->object_to_world().ptr());
  float distance_factor = (world_pixel_scale * scale * winmat[1][1] * vp_size[1]) / w;

  wave_center[0] = wave_center[0] * 0.5f + 0.5f;
  wave_center[1] = wave_center[1] * 0.5f + 0.5f;

  if (fx->orientation == 0) {
    /* Horizontal */
    copy_v2_fl2(wave_dir, 1.0f, 0.0f);
  }
  else {
    /* Vertical */
    copy_v2_fl2(wave_dir, 0.0f, 1.0f);
  }
  /* Rotate 90 degrees. */
  copy_v2_v2(wave_ofs, wave_dir);
  std::swap(wave_ofs[0], wave_ofs[1]);
  wave_ofs[1] *= -1.0f;
  /* Keep world space scaling and aspect ratio. */
  mul_v2_fl(wave_dir, 1.0f / (max_ff(1e-8f, fx->period) * distance_factor));
  mul_v2_v2(wave_dir, vp_size);
  mul_v2_fl(wave_ofs, fx->amplitude * distance_factor);
  mul_v2_v2(wave_ofs, vp_size_inv);
  /* Phase start at shadow center. */
  wave_phase = fx->phase - dot_v2v2(wave_center, wave_dir);

  GPUShader *sh = GPENCIL_shader_fx_transform_get();

  DRWState state = DRW_STATE_WRITE_COLOR;
  auto &grp = gpencil_vfx_pass_create("Fx Wave", state, iter, sh);
  grp.push_constant("axisFlip", float2(1.0f, 1.0f));
  grp.push_constant("waveDir", float2(wave_dir));
  grp.push_constant("waveOffset", float2(wave_ofs));
  grp.push_constant("wavePhase", wave_phase);
  grp.push_constant("swirlRadius", 0.0f);
  grp.draw_procedural(GPU_PRIM_TRIS, 1, 3);
}

static void gpencil_vfx_swirl(SwirlShaderFxData *fx, Object * /*ob*/, gpIterVfxData *iter)
{
  if (fx->object == nullptr) {
    return;
  }

  float4x4 winmat, persmat;
  float swirl_center[3];
  winmat = blender::draw::View::default_get().winmat();
  persmat = blender::draw::View::default_get().persmat();
  const float *vp_size = DRW_viewport_size_get();

  copy_v3_v3(swirl_center, fx->object->object_to_world().location());

  const float w = fabsf(mul_project_m4_v3_zfac(persmat.ptr(), swirl_center));
  mul_v3_m4v3(swirl_center, persmat.ptr(), swirl_center);
  mul_v3_fl(swirl_center, 1.0f / w);

  /* Modify by distance to camera and object scale. */
  float world_pixel_scale = 1.0f / GPENCIL_PIXEL_FACTOR;
  float scale = mat4_to_scale(fx->object->object_to_world().ptr());
  float distance_factor = (world_pixel_scale * scale * winmat[1][1] * vp_size[1]) / w;

  mul_v2_fl(swirl_center, 0.5f);
  add_v2_fl(swirl_center, 0.5f);
  mul_v2_v2(swirl_center, vp_size);

  float radius = fx->radius * distance_factor;
  if (radius < 1.0f) {
    return;
  }

  GPUShader *sh = GPENCIL_shader_fx_transform_get();

  DRWState state = DRW_STATE_WRITE_COLOR;
  auto &grp = gpencil_vfx_pass_create("Fx Flip", state, iter, sh);
  grp.push_constant("axisFlip", float2(1.0f, 1.0f));
  grp.push_constant("waveOffset", float2(0.0f, 0.0f));
  grp.push_constant("swirlCenter", float2(swirl_center));
  grp.push_constant("swirlAngle", fx->angle);
  grp.push_constant("swirlRadius", radius);
  grp.draw_procedural(GPU_PRIM_TRIS, 1, 3);
}

void gpencil_vfx_cache_populate(GPENCIL_Data *vedata,
                                Object *ob,
                                GPENCIL_tObject *tgp_ob,
                                const bool is_edit_mode)
{
  GPENCIL_Instance *inst = vedata->instance;
  GPENCIL_PrivateData *pd = vedata->stl->pd;

  /* These may not be allocated yet, use address of future pointer. */
  gpIterVfxData iter{};
  iter.pd = pd;
  iter.tgp_ob = tgp_ob;
  iter.target_fb = &inst->layer_fb;
  iter.source_fb = &inst->object_fb;
  iter.target_color_tx = &inst->color_layer_tx;
  iter.source_color_tx = &inst->color_object_tx;
  iter.target_reveal_tx = &inst->reveal_layer_tx;
  iter.source_reveal_tx = &inst->reveal_object_tx;

  /* If simplify enabled, nothing more to do. */
  if (!pd->simplify_fx) {
    LISTBASE_FOREACH (ShaderFxData *, fx, &ob->shader_fx) {
      if (effect_is_active(fx, is_edit_mode, pd->is_viewport)) {
        switch (fx->type) {
          case eShaderFxType_Blur:
            gpencil_vfx_blur((BlurShaderFxData *)fx, ob, &iter);
            break;
          case eShaderFxType_Colorize:
            gpencil_vfx_colorize((ColorizeShaderFxData *)fx, ob, &iter);
            break;
          case eShaderFxType_Flip:
            gpencil_vfx_flip((FlipShaderFxData *)fx, ob, &iter);
            break;
          case eShaderFxType_Pixel:
            gpencil_vfx_pixelize((PixelShaderFxData *)fx, ob, &iter);
            break;
          case eShaderFxType_Rim:
            gpencil_vfx_rim((RimShaderFxData *)fx, ob, &iter);
            break;
          case eShaderFxType_Shadow:
            gpencil_vfx_shadow((ShadowShaderFxData *)fx, ob, &iter);
            break;
          case eShaderFxType_Glow:
            gpencil_vfx_glow((GlowShaderFxData *)fx, ob, &iter);
            break;
          case eShaderFxType_Swirl:
            gpencil_vfx_swirl((SwirlShaderFxData *)fx, ob, &iter);
            break;
          case eShaderFxType_Wave:
            gpencil_vfx_wave((WaveShaderFxData *)fx, ob, &iter);
            break;
          default:
            break;
        }
      }
    }
  }

  if ((!pd->simplify_fx && tgp_ob->vfx.first != nullptr) || tgp_ob->do_mat_holdout) {
    /* We need an extra pass to combine result to main buffer. */
    iter.target_fb = &inst->gpencil_fb;

    GPUShader *sh = GPENCIL_shader_fx_composite_get();

    DRWState state = DRW_STATE_WRITE_COLOR | DRW_STATE_BLEND_MUL;
    auto &grp = gpencil_vfx_pass_create("GPencil Object Compose", state, &iter, sh);
    grp.push_constant("isFirstPass", true);
    grp.draw_procedural(GPU_PRIM_TRIS, 1, 3);

    /* We cannot do custom blending on multi-target frame-buffers.
     * Workaround by doing 2 passes. */
    grp.state_set(DRW_STATE_WRITE_COLOR | DRW_STATE_BLEND_ADD_FULL);
    grp.push_constant("isFirstPass", false);
    grp.draw_procedural(GPU_PRIM_TRIS, 1, 3);

    pd->use_object_fb = true;
    pd->use_layer_fb = true;
  }
}

/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#ifdef GPU_SHADER
#  pragma once
#  include "gpu_glsl_cpp_stubs.hh"

#  include "draw_view_info.hh"
#  include "eevee_common_info.hh"
#  include "gpu_shader_fullscreen_info.hh"
#endif

#include "eevee_defines.hh"
#include "gpu_shader_create_info.hh"

#define image_out(slot, format, name) \
  image(slot, format, Qualifier::write, ImageType::Float2D, name, Frequency::PASS)
#define uimage_out(slot, format, name) \
  image(slot, format, Qualifier::write, ImageType::Uint2D, name, Frequency::PASS)
#define image_in(slot, format, name) \
  image(slot, format, Qualifier::read, ImageType::Float2D, name, Frequency::PASS)
#define image_array_out(slot, qualifier, format, name) \
  image(slot, format, qualifier, ImageType::Float2DArray, name, Frequency::PASS)

/* -------------------------------------------------------------------- */
/** \name Thickness Amend
 * \{ */

GPU_SHADER_CREATE_INFO(eevee_deferred_thickness_amend)
DO_STATIC_COMPILATION()
DEFINE("GBUFFER_LOAD")
SAMPLER(0, usampler2DArray, gbuf_header_tx)
IMAGE(0, GPU_RG16, read_write, image2DArray, gbuf_normal_img)
/* Early fragment test is needed to discard fragment that do not need this processing. */
EARLY_FRAGMENT_TEST(true)
FRAGMENT_SOURCE("eevee_deferred_thickness_amend_frag.glsl")
ADDITIONAL_INFO(draw_view)
ADDITIONAL_INFO(gpu_fullscreen)
ADDITIONAL_INFO(eevee_sampling_data)
ADDITIONAL_INFO(eevee_shared)
ADDITIONAL_INFO(eevee_light_data)
ADDITIONAL_INFO(eevee_shadow_data)
ADDITIONAL_INFO(eevee_hiz_data)
GPU_SHADER_CREATE_END()

/** \} */

GPU_SHADER_CREATE_INFO(eevee_deferred_tile_classify)
FRAGMENT_SOURCE("eevee_deferred_tile_classify_frag.glsl")
ADDITIONAL_INFO(eevee_shared)
ADDITIONAL_INFO(gpu_fullscreen)
SUBPASS_IN(1, uint, Uint2DArray, in_gbuffer_header, DEFERRED_GBUFFER_ROG_ID)
TYPEDEF_SOURCE("draw_shader_shared.hh")
PUSH_CONSTANT(int, current_bit)
DO_STATIC_COMPILATION()
GPU_SHADER_CREATE_END()

GPU_SHADER_CREATE_INFO(eevee_deferred_light)
FRAGMENT_SOURCE("eevee_deferred_light_frag.glsl")
/* Early fragment test is needed to avoid processing background fragments. */
EARLY_FRAGMENT_TEST(true)
FRAGMENT_OUT(0, float4, out_combined)
/* Chaining to next pass. */
IMAGE_FREQ(2, DEFERRED_RADIANCE_FORMAT, write, uimage2D, direct_radiance_1_img, PASS)
IMAGE_FREQ(3, DEFERRED_RADIANCE_FORMAT, write, uimage2D, direct_radiance_2_img, PASS)
IMAGE_FREQ(4, DEFERRED_RADIANCE_FORMAT, write, uimage2D, direct_radiance_3_img, PASS)
/* Optimized out if use_split_indirect is false. */
IMAGE_FREQ(5, RAYTRACE_RADIANCE_FORMAT, write, image2D, indirect_radiance_1_img, PASS)
IMAGE_FREQ(6, RAYTRACE_RADIANCE_FORMAT, write, image2D, indirect_radiance_2_img, PASS)
IMAGE_FREQ(7, RAYTRACE_RADIANCE_FORMAT, write, image2D, indirect_radiance_3_img, PASS)
SPECIALIZATION_CONSTANT(bool, use_split_indirect, true)
SPECIALIZATION_CONSTANT(bool, use_lightprobe_eval, true)
SPECIALIZATION_CONSTANT(bool, use_transmission, false)
SPECIALIZATION_CONSTANT(int, render_pass_shadow_id, -1)
DEFINE("SPECIALIZED_SHADOW_PARAMS")
SPECIALIZATION_CONSTANT(int, shadow_ray_count, 1)
SPECIALIZATION_CONSTANT(int, shadow_ray_step_count, 6)
ADDITIONAL_INFO(eevee_shared)
ADDITIONAL_INFO(eevee_gbuffer_data)
ADDITIONAL_INFO(eevee_utility_texture)
ADDITIONAL_INFO(eevee_sampling_data)
ADDITIONAL_INFO(eevee_light_data)
ADDITIONAL_INFO(eevee_shadow_data)
ADDITIONAL_INFO(eevee_hiz_data)
ADDITIONAL_INFO(eevee_lightprobe_data)
ADDITIONAL_INFO(eevee_render_pass_out)
ADDITIONAL_INFO(gpu_fullscreen)
ADDITIONAL_INFO(draw_object_infos)
ADDITIONAL_INFO(draw_view)
GPU_SHADER_CREATE_END()

GPU_SHADER_CREATE_INFO(eevee_deferred_light_single)
ADDITIONAL_INFO(eevee_deferred_light)
DEFINE_VALUE("LIGHT_CLOSURE_EVAL_COUNT", "1")
DO_STATIC_COMPILATION()
GPU_SHADER_CREATE_END()

GPU_SHADER_CREATE_INFO(eevee_deferred_light_double)
ADDITIONAL_INFO(eevee_deferred_light)
DEFINE_VALUE("LIGHT_CLOSURE_EVAL_COUNT", "2")
DO_STATIC_COMPILATION()
GPU_SHADER_CREATE_END()

GPU_SHADER_CREATE_INFO(eevee_deferred_light_triple)
ADDITIONAL_INFO(eevee_deferred_light)
DEFINE_VALUE("LIGHT_CLOSURE_EVAL_COUNT", "3")
DO_STATIC_COMPILATION()
GPU_SHADER_CREATE_END()

GPU_SHADER_CREATE_INFO(eevee_deferred_combine)
/* Early fragment test is needed to avoid processing fragments background fragments. */
EARLY_FRAGMENT_TEST(true)
/* Inputs. */
SAMPLER(2, usampler2D, direct_radiance_1_tx)
SAMPLER(3, usampler2D, direct_radiance_2_tx)
SAMPLER(4, usampler2D, direct_radiance_3_tx)
SAMPLER(5, sampler2D, indirect_radiance_1_tx)
SAMPLER(6, sampler2D, indirect_radiance_2_tx)
SAMPLER(7, sampler2D, indirect_radiance_3_tx)
IMAGE(5, GPU_RGBA16F, read_write, image2D, radiance_feedback_img)
FRAGMENT_OUT(0, float4, out_combined)
ADDITIONAL_INFO(eevee_shared)
ADDITIONAL_INFO(eevee_gbuffer_data)
ADDITIONAL_INFO(eevee_render_pass_out)
ADDITIONAL_INFO(gpu_fullscreen)
FRAGMENT_SOURCE("eevee_deferred_combine_frag.glsl")
/* NOTE: Both light IDs have a valid specialized assignment of '-1' so only when default is
 * present will we instead dynamically look-up ID from the uniform buffer. */
SPECIALIZATION_CONSTANT(bool, render_pass_diffuse_light_enabled, false)
SPECIALIZATION_CONSTANT(bool, render_pass_specular_light_enabled, false)
SPECIALIZATION_CONSTANT(bool, render_pass_normal_enabled, false)
SPECIALIZATION_CONSTANT(bool, use_radiance_feedback, false)
SPECIALIZATION_CONSTANT(bool, use_split_radiance, true)
DO_STATIC_COMPILATION()
GPU_SHADER_CREATE_END()

GPU_SHADER_CREATE_INFO(eevee_deferred_capture_eval)
/* Early fragment test is needed to avoid processing fragments without correct GBuffer data. */
EARLY_FRAGMENT_TEST(true)
/* Inputs. */
FRAGMENT_OUT(0, float4, out_radiance)
DEFINE_VALUE("LIGHT_CLOSURE_EVAL_COUNT", "1")
ADDITIONAL_INFO(eevee_shared)
ADDITIONAL_INFO(eevee_gbuffer_data)
ADDITIONAL_INFO(eevee_utility_texture)
ADDITIONAL_INFO(eevee_sampling_data)
ADDITIONAL_INFO(eevee_light_data)
ADDITIONAL_INFO(eevee_shadow_data)
ADDITIONAL_INFO(eevee_hiz_data)
ADDITIONAL_INFO(eevee_volume_probe_data)
ADDITIONAL_INFO(draw_view)
ADDITIONAL_INFO(gpu_fullscreen)
ADDITIONAL_INFO(draw_object_infos)
FRAGMENT_SOURCE("eevee_deferred_capture_frag.glsl")
DO_STATIC_COMPILATION()
GPU_SHADER_CREATE_END()

GPU_SHADER_CREATE_INFO(eevee_deferred_planar_eval)
/* Early fragment test is needed to avoid processing fragments without correct GBuffer data. */
EARLY_FRAGMENT_TEST(true)
/* Inputs. */
FRAGMENT_OUT(0, float4, out_radiance)
DEFINE("SPHERE_PROBE")
DEFINE_VALUE("LIGHT_CLOSURE_EVAL_COUNT", "1")
ADDITIONAL_INFO(eevee_shared)
ADDITIONAL_INFO(eevee_gbuffer_data)
ADDITIONAL_INFO(eevee_utility_texture)
ADDITIONAL_INFO(eevee_sampling_data)
ADDITIONAL_INFO(eevee_light_data)
ADDITIONAL_INFO(eevee_lightprobe_data)
ADDITIONAL_INFO(eevee_shadow_data)
ADDITIONAL_INFO(eevee_hiz_data)
ADDITIONAL_INFO(draw_view)
ADDITIONAL_INFO(gpu_fullscreen)
ADDITIONAL_INFO(draw_object_infos)
FRAGMENT_SOURCE("eevee_deferred_planar_frag.glsl")
DO_STATIC_COMPILATION()
GPU_SHADER_CREATE_END()

#undef image_array_out
#undef image_out
#undef image_in

/* -------------------------------------------------------------------- */
/** \name Debug
 * \{ */

GPU_SHADER_CREATE_INFO(eevee_debug_gbuffer)
DO_STATIC_COMPILATION()
FRAGMENT_OUT_DUAL(0, float4, out_color_add, SRC_0)
FRAGMENT_OUT_DUAL(0, float4, out_color_mul, SRC_1)
PUSH_CONSTANT(int, debug_mode)
FRAGMENT_SOURCE("eevee_debug_gbuffer_frag.glsl")
ADDITIONAL_INFO(draw_view)
ADDITIONAL_INFO(gpu_fullscreen)
ADDITIONAL_INFO(eevee_shared)
ADDITIONAL_INFO(eevee_gbuffer_data)
GPU_SHADER_CREATE_END()

/** \} */

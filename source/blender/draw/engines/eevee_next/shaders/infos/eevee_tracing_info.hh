/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#include "eevee_defines.hh"
#include "gpu_shader_create_info.hh"

#define EEVEE_RAYTRACE_CLOSURE_VARIATION(name, ...) \
  GPU_SHADER_CREATE_INFO(name##_diffuse) \
      .do_static_compilation(true) \
      .define("RAYTRACE_DIFFUSE") \
      .define("CLOSURE_ACTIVE", "eClosureBits(CLOSURE_DIFFUSE)") \
      .additional_info(#name); \
  GPU_SHADER_CREATE_INFO(name##_reflect) \
      .do_static_compilation(true) \
      .define("RAYTRACE_REFLECT") \
      .define("CLOSURE_ACTIVE", "eClosureBits(CLOSURE_REFLECTION)") \
      .additional_info(#name); \
  GPU_SHADER_CREATE_INFO(name##_refract) \
      .do_static_compilation(true) \
      .define("RAYTRACE_REFRACT") \
      .define("CLOSURE_ACTIVE", "eClosureBits(CLOSURE_REFRACTION)") \
      .additional_info(#name);

/* -------------------------------------------------------------------- */
/** \name Ray tracing Pipeline
 * \{ */

GPU_SHADER_CREATE_INFO(eevee_ray_tile_classify)
    .do_static_compilation(true)
    .local_group_size(RAYTRACE_GROUP_SIZE, RAYTRACE_GROUP_SIZE)
    .additional_info("eevee_shared", "eevee_gbuffer_data", "eevee_global_ubo")
    .typedef_source("draw_shader_shared.h")
    .image(0, RAYTRACE_TILEMASK_FORMAT, Qualifier::WRITE, ImageType::UINT_2D, "tile_mask_img")
    .storage_buf(0, Qualifier::WRITE, "DispatchCommand", "ray_dispatch_buf")
    .storage_buf(1, Qualifier::WRITE, "DispatchCommand", "denoise_dispatch_buf")
    .compute_source("eevee_ray_tile_classify_comp.glsl");

GPU_SHADER_CREATE_INFO(eevee_ray_tile_compact)
    .do_static_compilation(true)
    .local_group_size(RAYTRACE_GROUP_SIZE, RAYTRACE_GROUP_SIZE)
    .additional_info("eevee_shared", "eevee_global_ubo")
    .typedef_source("draw_shader_shared.h")
    .image(0, RAYTRACE_TILEMASK_FORMAT, Qualifier::READ, ImageType::UINT_2D, "tile_mask_img")
    .storage_buf(0, Qualifier::READ_WRITE, "DispatchCommand", "ray_dispatch_buf")
    .storage_buf(1, Qualifier::READ_WRITE, "DispatchCommand", "denoise_dispatch_buf")
    .storage_buf(2, Qualifier::WRITE, "uint", "ray_tiles_buf[]")
    .storage_buf(3, Qualifier::WRITE, "uint", "denoise_tiles_buf[]")
    .compute_source("eevee_ray_tile_compact_comp.glsl");

GPU_SHADER_CREATE_INFO(eevee_ray_generate)
    .local_group_size(RAYTRACE_GROUP_SIZE, RAYTRACE_GROUP_SIZE)
    .additional_info("eevee_shared",
                     "eevee_gbuffer_data",
                     "eevee_global_ubo",
                     "eevee_sampling_data",
                     "draw_view",
                     "eevee_utility_texture")
    .image(0, GPU_RGBA16F, Qualifier::WRITE, ImageType::FLOAT_2D, "out_ray_data_img")
    .storage_buf(4, Qualifier::READ, "uint", "tiles_coord_buf[]")
    .compute_source("eevee_ray_generate_comp.glsl");

EEVEE_RAYTRACE_CLOSURE_VARIATION(eevee_ray_generate)

GPU_SHADER_CREATE_INFO(eevee_ray_trace_fallback)
    .do_static_compilation(true)
    .local_group_size(RAYTRACE_GROUP_SIZE, RAYTRACE_GROUP_SIZE)
    .additional_info("eevee_shared", "eevee_global_ubo", "draw_view", "eevee_lightprobe_data")
    .image(0, GPU_RGBA16F, Qualifier::READ, ImageType::FLOAT_2D, "ray_data_img")
    .image(1, RAYTRACE_RAYTIME_FORMAT, Qualifier::WRITE, ImageType::FLOAT_2D, "ray_time_img")
    .image(2, RAYTRACE_RADIANCE_FORMAT, Qualifier::WRITE, ImageType::FLOAT_2D, "ray_radiance_img")
    .sampler(1, ImageType::DEPTH_2D, "depth_tx")
    .storage_buf(5, Qualifier::READ, "uint", "tiles_coord_buf[]")
    .compute_source("eevee_ray_trace_fallback_comp.glsl");

GPU_SHADER_CREATE_INFO(eevee_ray_trace_planar)
    .do_static_compilation(true)
    .local_group_size(RAYTRACE_GROUP_SIZE, RAYTRACE_GROUP_SIZE)
    .define("PLANAR_PROBES")
    .additional_info("eevee_shared",
                     "eevee_global_ubo",
                     "eevee_sampling_data",
                     "draw_view",
                     "eevee_lightprobe_data",
                     "eevee_lightprobe_planar_data")
    .image(0, GPU_RGBA16F, Qualifier::READ_WRITE, ImageType::FLOAT_2D, "ray_data_img")
    .image(1, RAYTRACE_RAYTIME_FORMAT, Qualifier::WRITE, ImageType::FLOAT_2D, "ray_time_img")
    .image(2, RAYTRACE_RADIANCE_FORMAT, Qualifier::WRITE, ImageType::FLOAT_2D, "ray_radiance_img")
    .sampler(2, ImageType::DEPTH_2D, "depth_tx")
    .storage_buf(5, Qualifier::READ, "uint", "tiles_coord_buf[]")
    .compute_source("eevee_ray_trace_planar_comp.glsl");

GPU_SHADER_CREATE_INFO(eevee_ray_trace_screen)
    .local_group_size(RAYTRACE_GROUP_SIZE, RAYTRACE_GROUP_SIZE)
    .additional_info("eevee_shared",
                     "eevee_global_ubo",
                     "eevee_sampling_data",
                     "draw_view",
                     "eevee_hiz_data",
                     "eevee_lightprobe_data")
    .image(0, GPU_RGBA16F, Qualifier::READ, ImageType::FLOAT_2D, "ray_data_img")
    .image(1, RAYTRACE_RAYTIME_FORMAT, Qualifier::WRITE, ImageType::FLOAT_2D, "ray_time_img")
    .image(2, RAYTRACE_RADIANCE_FORMAT, Qualifier::WRITE, ImageType::FLOAT_2D, "ray_radiance_img")
    .sampler(0, ImageType::FLOAT_2D, "screen_radiance_tx")
    .sampler(1, ImageType::DEPTH_2D, "depth_tx")
    .storage_buf(5, Qualifier::READ, "uint", "tiles_coord_buf[]")
    .compute_source("eevee_ray_trace_screen_comp.glsl");

EEVEE_RAYTRACE_CLOSURE_VARIATION(eevee_ray_trace_screen)

GPU_SHADER_CREATE_INFO(eevee_ray_denoise_spatial)
    .local_group_size(RAYTRACE_GROUP_SIZE, RAYTRACE_GROUP_SIZE)
    .additional_info("eevee_shared",
                     "eevee_gbuffer_data",
                     "eevee_global_ubo",
                     "eevee_sampling_data",
                     "draw_view",
                     "eevee_utility_texture")
    .sampler(3, ImageType::DEPTH_2D, "depth_tx")
    .image(0, GPU_RGBA16F, Qualifier::READ, ImageType::FLOAT_2D, "ray_data_img")
    .image(1, RAYTRACE_RAYTIME_FORMAT, Qualifier::READ, ImageType::FLOAT_2D, "ray_time_img")
    .image(2, RAYTRACE_RADIANCE_FORMAT, Qualifier::READ, ImageType::FLOAT_2D, "ray_radiance_img")
    .image(3, RAYTRACE_RADIANCE_FORMAT, Qualifier::WRITE, ImageType::FLOAT_2D, "out_radiance_img")
    .image(4, RAYTRACE_VARIANCE_FORMAT, Qualifier::WRITE, ImageType::FLOAT_2D, "out_variance_img")
    .image(5, GPU_R32F, Qualifier::WRITE, ImageType::FLOAT_2D, "out_hit_depth_img")
    .image(6, RAYTRACE_TILEMASK_FORMAT, Qualifier::READ, ImageType::UINT_2D, "tile_mask_img")
    .storage_buf(4, Qualifier::READ, "uint", "tiles_coord_buf[]")
    .compute_source("eevee_ray_denoise_spatial_comp.glsl");

EEVEE_RAYTRACE_CLOSURE_VARIATION(eevee_ray_denoise_spatial)

GPU_SHADER_CREATE_INFO(eevee_ray_denoise_temporal)
    .do_static_compilation(true)
    .local_group_size(RAYTRACE_GROUP_SIZE, RAYTRACE_GROUP_SIZE)
    .additional_info("eevee_shared", "eevee_global_ubo", "draw_view")
    .sampler(0, ImageType::FLOAT_2D, "radiance_history_tx")
    .sampler(1, ImageType::FLOAT_2D, "variance_history_tx")
    .sampler(2, ImageType::UINT_2D, "tilemask_history_tx")
    .sampler(3, ImageType::DEPTH_2D, "depth_tx")
    .image(0, GPU_R32F, Qualifier::READ, ImageType::FLOAT_2D, "hit_depth_img")
    .image(1, RAYTRACE_RADIANCE_FORMAT, Qualifier::READ, ImageType::FLOAT_2D, "in_radiance_img")
    .image(2, RAYTRACE_RADIANCE_FORMAT, Qualifier::WRITE, ImageType::FLOAT_2D, "out_radiance_img")
    .image(3, RAYTRACE_VARIANCE_FORMAT, Qualifier::READ, ImageType::FLOAT_2D, "in_variance_img")
    .image(4, RAYTRACE_VARIANCE_FORMAT, Qualifier::WRITE, ImageType::FLOAT_2D, "out_variance_img")
    .storage_buf(4, Qualifier::READ, "uint", "tiles_coord_buf[]")
    .compute_source("eevee_ray_denoise_temporal_comp.glsl");

GPU_SHADER_CREATE_INFO(eevee_ray_denoise_bilateral)
    .local_group_size(RAYTRACE_GROUP_SIZE, RAYTRACE_GROUP_SIZE)
    .additional_info("eevee_shared",
                     "eevee_gbuffer_data",
                     "eevee_global_ubo",
                     "eevee_sampling_data",
                     "draw_view")
    .sampler(1, ImageType::DEPTH_2D, "depth_tx")
    .image(1, RAYTRACE_RADIANCE_FORMAT, Qualifier::READ, ImageType::FLOAT_2D, "in_radiance_img")
    .image(2, RAYTRACE_RADIANCE_FORMAT, Qualifier::WRITE, ImageType::FLOAT_2D, "out_radiance_img")
    .image(3, RAYTRACE_VARIANCE_FORMAT, Qualifier::READ, ImageType::FLOAT_2D, "in_variance_img")
    .image(6, RAYTRACE_TILEMASK_FORMAT, Qualifier::READ, ImageType::UINT_2D, "tile_mask_img")
    .storage_buf(4, Qualifier::READ, "uint", "tiles_coord_buf[]")
    .compute_source("eevee_ray_denoise_bilateral_comp.glsl");

EEVEE_RAYTRACE_CLOSURE_VARIATION(eevee_ray_denoise_bilateral)

/** \} */

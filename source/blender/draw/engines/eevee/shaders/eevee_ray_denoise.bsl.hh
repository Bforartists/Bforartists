/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/**
 * Ray-tracing denoising pipeline.
 *
 * Following "Stochastic All The Things: Raytracing in Hybrid Real-Time Rendering"
 * by Tomasz Stachowiak
 * https://www.ea.com/seed/news/seed-dd18-presentation-slides-raytracing
 */

#pragma once

#include "infos/eevee_tracing_infos.hh"

SHADER_LIBRARY_CREATE_INFO(eevee_gbuffer_data)
SHADER_LIBRARY_CREATE_INFO(eevee_global_ubo)
SHADER_LIBRARY_CREATE_INFO(eevee_sampling_data)
SHADER_LIBRARY_CREATE_INFO(draw_view)
SHADER_LIBRARY_CREATE_INFO(eevee_utility_texture)

#include "draw_view_lib.glsl"
#include "eevee_closure_lib.glsl"
#include "eevee_colorspace_lib.bsl.hh"
#include "eevee_defines.hh"
#include "eevee_filter_lib.glsl"
#include "eevee_gbuffer_read_lib.glsl"
#include "eevee_reverse_z_lib.bsl.hh"
#include "eevee_sampling_lib.glsl"
#include "gpu_shader_codegen_lib.glsl"
#include "gpu_shader_math_matrix_transform_lib.glsl"
#include "gpu_shader_math_vector_lib.glsl"
#include "gpu_shader_utildefines_lib.glsl"

namespace eevee::raytracing::denoise {

struct TileBuffer {
  [[storage(4, read)]] uint (&tiles_coord_buf)[];

  uint2 tile_coord(uint tile_id)
  {
    return unpackUvec2x16(tiles_coord_buf[tile_id]);
  }
};

struct DenoiseSpatial {
  [[legacy_info]] ShaderCreateInfo eevee_gbuffer_data;
  [[legacy_info]] ShaderCreateInfo eevee_global_ubo;
  [[legacy_info]] ShaderCreateInfo eevee_sampling_data;
  [[legacy_info]] ShaderCreateInfo draw_view;
  [[legacy_info]] ShaderCreateInfo eevee_utility_texture;

  [[specialization_constant(2)]] int raytrace_resolution_scale;
  [[specialization_constant(false)]] bool skip_denoise;
  [[specialization_constant(0)]] int closure_index;

  [[sampler(3)]] sampler2DDepth depth_tx;

  [[image(0, read, SFLOAT_16_16_16_16)]] image2D ray_data_img;
  [[image(1, read, RAYTRACE_RAYTIME_FORMAT)]] image2D ray_time_img;
  [[image(2, read, RAYTRACE_RADIANCE_FORMAT)]] image2D ray_radiance_img;

  [[image(3, write, RAYTRACE_RADIANCE_FORMAT)]] image2D out_radiance_img;
  [[image(4, write, RAYTRACE_VARIANCE_FORMAT)]] image2D out_variance_img;

  [[image(5, write, SFLOAT_32)]] image2D out_hit_depth_img;

  [[image(6, read, RAYTRACE_TILEMASK_FORMAT)]] uimage2DArray tile_mask_img;

  [[resource_table]] srt_t<TileBuffer> tiles;

  /* Tag pixel radiance as invalid. */
  void invalid_pixel_write(int2 texel)
  {
    imageStoreFast(out_radiance_img, texel, float4(FLT_11_11_10_MAX, 0.0f));
    imageStoreFast(out_variance_img, texel, float4(0.0f));
    imageStoreFast(out_hit_depth_img, texel, float4(0.0f));
  }
};

void transmission_thickness_amend_closure(ClosureUndetermined &cl, float3 &V, Thickness thickness)
{
  switch (cl.type) {
    case CLOSURE_BSDF_MICROFACET_GGX_REFRACTION_ID:
      bxdf_ggx_context_amend_transmission(cl, V, thickness);
      break;
    case CLOSURE_NONE_ID:
    case CLOSURE_BSDF_DIFFUSE_ID:
    case CLOSURE_BSDF_TRANSLUCENT_ID:
    case CLOSURE_BSDF_MICROFACET_GGX_REFLECTION_ID:
    case CLOSURE_BSSRDF_BURLEY_ID:
      break;
  }
}

/**
 * Spatial ray reuse. Denoise raytrace result using ratio estimator.
 *
 * Input: Ray direction * hit time, Ray radiance, Ray hit depth
 * Output: Ray radiance reconstructed, Mean Ray hit depth, Radiance Variance
 *
 * Shader is specialized depending on the type of ray to denoise.
 */
[[compute,
  local_size(RAYTRACE_GROUP_SIZE, RAYTRACE_GROUP_SIZE),
  /* Metal: Provide compiler with hint to tune per-thread resource allocation. */
  metal_max_total_threads_per_threadgroup(316)]]
void spatial_main([[resource_table]] DenoiseSpatial &srt,
                  [[work_group_id]] const uint3 work_group,
                  [[local_invocation_id]] const uint3 local_id)
{
  [[resource_table]] TileBuffer &tiles = srt.tiles;
  uint2 tile_coord = tiles.tile_coord(work_group.x);

  constexpr uint tile_size = RAYTRACE_GROUP_SIZE;
  int2 texel_fullres = int2(local_id.xy + tile_coord * tile_size);
  int2 texel = (texel_fullres) / srt.raytrace_resolution_scale;

  if (srt.skip_denoise) {
    imageStore(srt.out_radiance_img, texel_fullres, imageLoad(srt.ray_radiance_img, texel));
    return;
  }

  /* Clear neighbor tiles that will not be processed. */
  /* TODO(fclem): Optimize this. We don't need to clear the whole ring. */
  for (int x = -1; x <= 1; x++) {
    for (int y = -1; y <= 1; y++) {
      if (x == 0 && y == 0) {
        continue;
      }

      int2 tile_coord_neighbor = int2(tile_coord) + int2(x, y);
      if (!in_image_range(tile_coord_neighbor, srt.tile_mask_img)) {
        continue;
      }

      int3 sample_tile = int3(tile_coord_neighbor, srt.closure_index);

      uint tile_mask = imageLoadFast(srt.tile_mask_img, sample_tile).r;
      bool tile_is_unused = !flag_test(tile_mask, 1u << 0u);
      if (tile_is_unused) {
        int2 texel_fullres_neighbor = texel_fullres + int2(x, y) * int(tile_size);
        srt.invalid_pixel_write(texel_fullres_neighbor);
      }
    }
  }

  bool valid_texel = in_texture_range(texel_fullres, gbuf_header_tx);
  if (!valid_texel) {
    srt.invalid_pixel_write(texel_fullres);
    return;
  }

  gbuffer::Header gbuf_header = gbuffer::read_header(texel_fullres);

  ClosureUndetermined closure = gbuffer::read_bin(texel_fullres, srt.closure_index);

  if (closure.type == CLOSURE_NONE_ID) {
    srt.invalid_pixel_write(texel_fullres);
    return;
  }

  float2 uv = (float2(texel_fullres) + 0.5f) * uniform_buf.raytrace.full_resolution_inv;
  float3 P = drw_point_screen_to_world(float3(uv, 0.5f));
  float3 V = drw_world_incident_vector(P);

  Thickness thickness = gbuffer::read_thickness(gbuf_header, texel_fullres);
  if (thickness.value() != 0.0f) {
    transmission_thickness_amend_closure(closure, V, thickness);
  }

  /* Compute filter size and needed sample count */
  float apparent_roughness = closure_apparent_roughness_get(closure);
  float filter_size_factor = saturate(apparent_roughness * 8.0f);
  uint sample_count = 1u + uint(15.0f * filter_size_factor + 0.5f);
  /* NOTE: filter_size should never be greater than twice RAYTRACE_GROUP_SIZE. Otherwise, the
   * reconstruction can becomes ill defined since we don't know if further tiles are valid. */
  float filter_size = 12.0f * sqrt(filter_size_factor);
  if (srt.raytrace_resolution_scale > 1) {
    /* Filter at least 1 trace pixel to fight the undersampling. */
    filter_size = max(filter_size, 3.0f);
    sample_count = max(sample_count, 5u);
  }

  float2 noise = utility_tx_fetch(utility_tx, float2(texel_fullres), UTIL_BLUE_NOISE_LAYER).ba;
  noise += sampling_rng_1D_get(SAMPLING_CLOSURE);

  float3 rgb_moment = float3(0.0f);
  float3 radiance_accum = float3(0.0f);
  float weight_accum = 0.0f;
  float closest_hit_time = 1.0e10f;

  for (uint i = 0u; i < sample_count; i++) {
    float2 offset_f = (fract(hammersley_2d(i, sample_count) + noise) - 0.5f) * filter_size;
    int2 offset = int2(floor(offset_f + 0.5f));
    int2 sample_texel = texel + offset;

    float4 ray_data = imageLoad(srt.ray_data_img, sample_texel);
    float ray_time = imageLoad(srt.ray_time_img, sample_texel).r;
    float4 ray_radiance = imageLoad(srt.ray_radiance_img, sample_texel);

    float3 ray_direction = ray_data.xyz;
    float ray_pdf_inv = abs(ray_data.w);
    /* Skip invalid pixels. */
    if (ray_pdf_inv == 0.0f) {
      continue;
    }

    closest_hit_time = min(closest_hit_time, ray_time);

    /* Slide 54. */
    /* The reference is wrong.
     * The ratio estimator is `pdf_local / pdf_ray` instead of `bsdf_local / pdf_ray`. */
    float pdf = closure_evaluate_pdf(closure, ray_direction, V, thickness);
    float weight = pdf * ray_pdf_inv;

    radiance_accum += ray_radiance.rgb * weight;
    weight_accum += weight;

    rgb_moment += square(ray_radiance.rgb) * weight;
  }
  float inv_weight = safe_rcp(weight_accum);

  radiance_accum *= inv_weight;
  /* Use radiance sum as signal mean. */
  float3 rgb_mean = radiance_accum;
  rgb_moment *= inv_weight;

  float3 rgb_variance = abs(rgb_moment - square(rgb_mean));
  float hit_variance = reduce_max(rgb_variance);

  float depth = reverse_z::read(texelFetch(srt.depth_tx, texel_fullres, 0).r);
  float scene_z = drw_depth_screen_to_view(depth);
  float hit_depth = drw_depth_view_to_screen(scene_z - closest_hit_time);

  imageStoreFast(srt.out_radiance_img, texel_fullres, float4(radiance_accum, 0.0f));
  imageStoreFast(srt.out_variance_img, texel_fullres, float4(hit_variance));
  imageStoreFast(srt.out_hit_depth_img, texel_fullres, float4(hit_depth));
}

struct LocalStatistics {
  float3 mean;
  float3 moment;
  float3 variance;
  float3 deviation;
  float3 clamp_min;
  float3 clamp_max;
};

float4 bilinear_weights_from_subpixel_coord(float2 co)
{
  /* From top left in clockwise order. */
  float4 weights;
  weights.x = (1.0f - co.x) * co.y;
  weights.y = co.x * co.y;
  weights.z = co.x * (1.0f - co.y);
  weights.w = (1.0f - co.x) * (1.0f - co.y);
  return weights;
}

struct DenoiseTemporal {
  [[legacy_info]] ShaderCreateInfo eevee_global_ubo;
  [[legacy_info]] ShaderCreateInfo draw_view;

  [[specialization_constant(0)]] int closure_index;

  [[sampler(0)]] sampler2D radiance_history_tx;
  [[sampler(1)]] sampler2D variance_history_tx;

  [[sampler(2)]] usampler2DArray tilemask_history_tx;

  [[sampler(3)]] sampler2DDepth depth_tx;

  [[image(0, read, SFLOAT_32)]] image2D hit_depth_img;

  [[image(1, read, RAYTRACE_RADIANCE_FORMAT)]] image2D in_radiance_img;
  [[image(3, read, RAYTRACE_VARIANCE_FORMAT)]] image2D in_variance_img;

  [[image(2, write, RAYTRACE_RADIANCE_FORMAT)]] image2D out_radiance_img;
  [[image(4, write, RAYTRACE_VARIANCE_FORMAT)]] image2D out_variance_img;

  [[resource_table]] srt_t<TileBuffer> tiles;

  LocalStatistics local_statistics_get(int2 texel, float3 center_radiance)
  {
    float3 center_radiance_YCoCg = colorspace::YCoCg_from_scene_linear(center_radiance);

    /* Build Local statistics (slide 46). */
    LocalStatistics result;
    result.mean = center_radiance_YCoCg;
    result.moment = square(center_radiance_YCoCg);
    float weight_accum = 1.0f;

    for (int x = -1; x <= 1; x++) {
      for (int y = -1; y <= 1; y++) {
        if (x == 0 && y == 0) {
          continue;
        }

        int2 neighbor_texel = texel + int2(x, y);
        if (!in_image_range(neighbor_texel, in_radiance_img)) {
          continue;
        }
        float3 radiance = imageLoad(in_radiance_img, neighbor_texel).rgb;
        /* Exclude unprocessed pixels. */
        if (all(equal(radiance, FLT_11_11_10_MAX))) {
          continue;
        }

        /* Weight corners less to avoid box artifacts.
         * Same idea as in "High Quality Temporal Supersampling" by Brian Karis at SIGGRAPH 2014
         * (Slide 32) Simple clamp to min/max of 8 neighbors results in 3x3 box artifacts. */
        /* TODO(@fclem): Evaluate if beneficial. Currently not use to soak more noise? Unsure. */
        // float weight = (abs(x) == abs(y)) ? 0.25f : 1.0f;
        /* Use YCoCg for clamping and accumulation to avoid color shift artifacts. */
        float3 radiance_YCoCg = colorspace::YCoCg_from_scene_linear(radiance.rgb);
        result.mean += radiance_YCoCg;
        result.moment += square(radiance_YCoCg);
        weight_accum += 1.0f;
      }
    }
    float inv_weight = safe_rcp(weight_accum);
    result.mean *= inv_weight;
    result.moment *= inv_weight;
    result.variance = abs(result.moment - square(result.mean));
    result.deviation = max(float3(1e-4f), sqrt(result.variance));
    result.clamp_min = result.mean - result.deviation;
    result.clamp_max = result.mean + result.deviation;
    return result;
  }

  float4 radiance_history_fetch(int2 texel, float bilinear_weight)
  {
    /* Out of history view. Return sample without weight. */
    if (!in_texture_range(texel, radiance_history_tx)) {
      return float4(0.0f);
    }

    int3 history_tile = int3(texel / RAYTRACE_GROUP_SIZE, closure_index);
    /* Fetch previous tilemask to avoid loading invalid data. */
    bool is_valid_history = texelFetch(tilemask_history_tx, history_tile, 0).r != 0;
    /* Exclude unprocessed pixels. */
    if (!is_valid_history) {
      return float4(0.0f);
    }
    float3 history_radiance = texelFetch(radiance_history_tx, texel, 0).rgb;
    /* Exclude unprocessed pixels. */
    if (all(equal(history_radiance, FLT_11_11_10_MAX))) {
      return float4(0.0f);
    }
    return float4(history_radiance * bilinear_weight, bilinear_weight);
  }

  float4 radiance_history_sample(float3 P, LocalStatistics local)
  {
    float2 uv = project_point(uniform_buf.raytrace.denoise_history_persmat, P).xy * 0.5f + 0.5f;

    /* FIXME(fclem): Find why we need this half pixel offset. */
    float2 texel_co = uv * float2(textureSize(radiance_history_tx, 0).xy) - 0.5f;
    float4 bilinear_weights = bilinear_weights_from_subpixel_coord(fract(texel_co));
    int2 texel = int2(floor(texel_co));

    /* Radiance needs to be manually interpolated because any pixel might contain invalid data. */
    float4 history_radiance;
    history_radiance = radiance_history_fetch(texel + int2(0, 1), bilinear_weights.x);
    history_radiance += radiance_history_fetch(texel + int2(1, 1), bilinear_weights.y);
    history_radiance += radiance_history_fetch(texel + int2(1, 0), bilinear_weights.z);
    history_radiance += radiance_history_fetch(texel + int2(0, 0), bilinear_weights.w);

    /* Use YCoCg for clamping and accumulation to avoid color shift artifacts. */
    float4 history_radiance_YCoCg;
    history_radiance_YCoCg.rgb = colorspace::YCoCg_from_scene_linear(history_radiance.rgb);
    history_radiance_YCoCg.a = history_radiance.a;

    /* Weighted contribution (slide 46). */
    float3 dist = abs(history_radiance_YCoCg.rgb - local.mean) / local.deviation;
    float weight = exp2(-4.0f * dot(dist, float3(1.0f)));

    return history_radiance_YCoCg * weight;
  }

  float2 variance_history_sample(float3 P)
  {
    float2 uv = project_point(uniform_buf.raytrace.denoise_history_persmat, P).xy * 0.5f + 0.5f;

    if (!in_range_exclusive(uv, float2(0.0f), float2(1.0f))) {
      /* Out of history view. Return sample without weight. */
      return float2(0.0f);
    }

    float history_variance = texture(variance_history_tx, uv).r;

    int2 history_texel = int2(floor(uv * float2(textureSize(variance_history_tx, 0).xy)));
    int3 history_tile = int3(history_texel / RAYTRACE_GROUP_SIZE, closure_index);
    /* Fetch previous tilemask to avoid loading invalid data. */
    bool is_valid_history = texelFetch(tilemask_history_tx, history_tile, 0).r != 0;

    if (is_valid_history) {
      return float2(history_variance, 1.0f);
    }
    return float2(0.0f);
  }
};

/**
 * Temporal Reprojection and accumulation of denoised ray-traced radiance.
 *
 * Dispatched at full-resolution using a tile list.
 *
 * Input: Spatially denoised radiance, Variance, Hit depth
 * Output: Stabilized Radiance, Stabilized Variance
 */
[[compute,
  local_size(RAYTRACE_GROUP_SIZE, RAYTRACE_GROUP_SIZE),
  /* Metal: Provide compiler with hint to tune per-thread resource allocation. */
  metal_max_total_threads_per_threadgroup(512)]]
void temporal_main([[resource_table]] DenoiseTemporal &srt,
                   [[work_group_id]] const uint3 work_group,
                   [[local_invocation_id]] const uint3 local_id)
{
  [[resource_table]] TileBuffer &tiles = srt.tiles;
  uint2 tile_coord = tiles.tile_coord(work_group.x);

  constexpr uint tile_size = RAYTRACE_GROUP_SIZE;
  int2 texel_fullres = int2(local_id.xy + tile_coord * tile_size);
  float2 uv = (float2(texel_fullres) + 0.5f) * uniform_buf.raytrace.full_resolution_inv;

  /* Check if texel is out of bounds,
   * so we can utilize fast texture functions and early-out if not. */
  if (any(greaterThanEqual(texel_fullres, imageSize(srt.in_radiance_img).xy))) {
    return;
  }

  float in_variance = imageLoadFast(srt.in_variance_img, texel_fullres).r;
  float3 in_radiance = imageLoadFast(srt.in_radiance_img, texel_fullres).rgb;

  if (all(equal(in_radiance, FLT_11_11_10_MAX))) {
    /* Early out on pixels that were marked unprocessed by the previous pass. */
    imageStoreFast(srt.out_radiance_img, texel_fullres, float4(FLT_11_11_10_MAX, 0.0f));
    imageStoreFast(srt.out_variance_img, texel_fullres, float4(0.0f));
    return;
  }

  LocalStatistics local = srt.local_statistics_get(texel_fullres, in_radiance);

  /* Radiance. */

  /* Surface reprojection. */
  /* TODO(fclem): Use per pixel velocity. Is this worth it? */
  float scene_depth = reverse_z::read(texelFetch(srt.depth_tx, texel_fullres, 0).r);
  float3 P = drw_point_screen_to_world(float3(uv, scene_depth));
  float4 history_radiance = srt.radiance_history_sample(P, local);
  /* Reflection reprojection. */
  float hit_depth = imageLoadFast(srt.hit_depth_img, texel_fullres).r;
  float3 P_hit = drw_point_screen_to_world(float3(uv, hit_depth));
  history_radiance += srt.radiance_history_sample(P_hit, local);
  /* Finalize accumulation. */
  history_radiance *= safe_rcp(history_radiance.w);
  /* Clamp resulting history radiance (slide 47). */
  history_radiance.rgb = clamp(history_radiance.rgb, local.clamp_min, local.clamp_max);
  /* Go back from YCoCg for final blend. */
  history_radiance.rgb = colorspace::scene_linear_from_YCoCg(history_radiance.rgb);
  /* Blend history with new radiance. */
  float mix_fac = (history_radiance.w > 1e-3f) ? 0.97f : 0.0f;
  /* Reduce blend factor to improve low roughness reflections. Use variance instead for speed. */
  mix_fac *= mix(0.75f, 1.0f, saturate(in_variance * 20.0f));
  float3 out_radiance = mix(
      colorspace::safe_color(in_radiance), colorspace::safe_color(history_radiance.rgb), mix_fac);
  /* This is feedback next frame as radiance_history_tx. */
  imageStoreFast(srt.out_radiance_img, texel_fullres, float4(out_radiance, 0.0f));

  /* Variance. */

  /* Reflection reprojection. */
  float2 history_variance = srt.variance_history_sample(P_hit);
  /* Blend history with new variance. */
  float mix_variance_fac = (history_variance.y == 0.0f) ? 0.0f : 0.90f;
  float out_variance = mix(in_variance, history_variance.x, mix_variance_fac);
  /* This is feedback next frame as variance_history_tx. */
  imageStoreFast(srt.out_variance_img, texel_fullres, float4(out_variance));
}

/* In order to remove some more fireflies, "tone-map" the color samples during the accumulation. */
float3 to_accumulation_space(float3 color)
{
  return color / (1.0f + reduce_max(color));
}
float3 from_accumulation_space(float3 color)
{
  return color / (1.0f - reduce_max(color));
}

struct DenoiseBilateral {
  [[legacy_info]] ShaderCreateInfo eevee_gbuffer_data;
  [[legacy_info]] ShaderCreateInfo eevee_global_ubo;
  [[legacy_info]] ShaderCreateInfo eevee_sampling_data;
  [[legacy_info]] ShaderCreateInfo draw_view;

  [[sampler(1)]] sampler2DDepth depth_tx;

  [[image(6, read, RAYTRACE_TILEMASK_FORMAT)]] uimage2DArray tile_mask_img;

  [[image(1, read, RAYTRACE_RADIANCE_FORMAT)]] image2D in_radiance_img;
  [[image(3, read, RAYTRACE_VARIANCE_FORMAT)]] image2D in_variance_img;

  [[image(2, write, RAYTRACE_RADIANCE_FORMAT)]] image2D out_radiance_img;

  [[specialization_constant(0)]] int closure_index;

  [[resource_table]] srt_t<TileBuffer> tiles;
};

/**
 * Bilateral filtering of denoised ray-traced radiance.
 *
 * Dispatched at full-resolution using a tile list.
 *
 * Input: Temporally Stabilized Radiance, Stabilized Variance
 * Output: Denoised radiance
 */
[[compute, local_size(RAYTRACE_GROUP_SIZE, RAYTRACE_GROUP_SIZE)]]
void bilateral_main([[resource_table]] DenoiseBilateral &srt,
                    [[work_group_id]] const uint3 work_group,
                    [[local_invocation_id]] const uint3 local_id)
{
  [[resource_table]] TileBuffer &tiles = srt.tiles;
  uint2 tile_coord = tiles.tile_coord(work_group.x);

  constexpr uint tile_size = RAYTRACE_GROUP_SIZE;
  int2 texel_fullres = int2(local_id.xy + tile_coord * tile_size);
  float2 center_uv = (float2(texel_fullres) + 0.5f) * uniform_buf.raytrace.full_resolution_inv;

  float center_depth = reverse_z::read(texelFetch(srt.depth_tx, texel_fullres, 0).r);
  float3 center_P = drw_point_screen_to_world(float3(center_uv, center_depth));

  ClosureUndetermined center_closure = gbuffer::read_bin(texel_fullres, srt.closure_index);

  if (center_closure.type == CLOSURE_NONE_ID) {
    /* Output nothing. This shouldn't even be loaded. */
    return;
  }

  float roughness = closure_apparent_roughness_get(center_closure);
  float variance = imageLoadFast(srt.in_variance_img, texel_fullres).r;
  float3 in_radiance = imageLoadFast(srt.in_radiance_img, texel_fullres).rgb;

  bool is_background = (center_depth == 0.0f);
  bool is_smooth = (roughness < 0.05f);
  bool is_low_variance = (variance < 0.05f);
  bool is_high_variance = (variance > 0.5f);

  /* Width of the box filter in pixels. */
  float filter_size_factor = saturate(roughness * 8.0f);
  float filter_size = mix(0.0f, 9.0f, filter_size_factor);
  uint sample_count = uint(mix(1.0f, 10.0f, filter_size_factor) *
                           (is_high_variance ? 1.5f : 1.0f));

  if (is_smooth || is_background || is_low_variance) {
    /* Early out cases. */
    imageStoreFast(srt.out_radiance_img, texel_fullres, float4(in_radiance, 0.0f));
    return;
  }

  float2 noise = interleaved_gradient_noise(
      float2(texel_fullres) + 0.5f, float2(3, 5), float2(0.0f));
  noise += sampling_rng_2D_get(SAMPLING_RAYTRACE_W);

  float3 accum_radiance = to_accumulation_space(in_radiance);
  float accum_weight = 1.0f;
  /* We want to resize the blur depending on the roughness and keep the amount of sample low.
   * So we do a random sampling around the center point. */
  for (uint i = 0u; i < sample_count; i++) {
    /* Essentially a box radius overtime. */
    float2 offset_f = (fract(hammersley_2d(i, sample_count) + noise) - 0.5f) * filter_size;
    int2 offset = int2(floor(offset_f + 0.5f));

    int2 sample_texel = texel_fullres + offset;
    int3 sample_tile = int3(sample_texel / RAYTRACE_GROUP_SIZE, srt.closure_index);
    /* Make sure the sample has been processed and do not contain garbage data. */
    if (imageLoad(srt.tile_mask_img, sample_tile).r == 0u) {
      continue;
    }

    float sample_depth = reverse_z::read(texelFetch(srt.depth_tx, sample_texel, 0).r);
    float2 sample_uv = (float2(sample_texel) + 0.5f) * uniform_buf.raytrace.full_resolution_inv;
    float3 sample_P = drw_point_screen_to_world(float3(sample_uv, sample_depth));

    /* Background case. */
    if (sample_depth == 0.0f) {
      continue;
    }

    float3 radiance = imageLoadFast(srt.in_radiance_img, sample_texel).rgb;

    /* Do not gather unprocessed pixels. */
    if (all(equal(radiance, FLT_11_11_10_MAX))) {
      continue;
    }

    ClosureUndetermined sample_closure = gbuffer::read_bin(sample_texel, srt.closure_index);

    if (sample_closure.type == CLOSURE_NONE_ID) {
      continue;
    }

    float gauss = filter_gaussian_factor(filter_size, 1.5f);

    /* TODO(fclem): Scene parameter. 10000.0f is dependent on scene scale. */
    float depth_weight = filter_planar_weight(center_closure.N, center_P, sample_P, 10000.0f);
    float spatial_weight = filter_gaussian_weight(gauss, length_squared(float2(offset)));
    float normal_weight = filter_angle_weight(center_closure.N, sample_closure.N);
    float weight = depth_weight * spatial_weight * normal_weight;

    accum_radiance += to_accumulation_space(radiance) * weight;
    accum_weight += weight;
  }

  float3 out_radiance = accum_radiance * safe_rcp(accum_weight);
  out_radiance = from_accumulation_space(out_radiance);

  imageStoreFast(srt.out_radiance_img, texel_fullres, float4(out_radiance, 0.0f));
}

PipelineCompute spatial(spatial_main);
PipelineCompute temporal(temporal_main);
PipelineCompute bilateral(bilateral_main);

}  // namespace eevee::raytracing::denoise

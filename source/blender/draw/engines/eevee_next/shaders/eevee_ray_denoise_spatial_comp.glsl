/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/**
 * Spatial ray reuse. Denoise raytrace result using ratio estimator.
 *
 * Input: Ray direction * hit time, Ray radiance, Ray hit depth
 * Output: Ray radiance reconstructed, Mean Ray hit depth, Radiance Variance
 *
 * Shader is specialized depending on the type of ray to denoise.
 *
 * Following "Stochastic All The Things: Raytracing in Hybrid Real-Time Rendering"
 * by Tomasz Stachowiak
 * https://www.ea.com/seed/news/seed-dd18-presentation-slides-raytracing
 */

#pragma BLENDER_REQUIRE(draw_view_lib.glsl)
#pragma BLENDER_REQUIRE(gpu_shader_codegen_lib.glsl)
#pragma BLENDER_REQUIRE(gpu_shader_utildefines_lib.glsl)
#pragma BLENDER_REQUIRE(eevee_gbuffer_lib.glsl)
#pragma BLENDER_REQUIRE(eevee_sampling_lib.glsl)
#pragma BLENDER_REQUIRE(eevee_bxdf_lib.glsl)
#pragma BLENDER_REQUIRE(eevee_closure_lib.glsl)

float bxdf_eval(ClosureUndetermined cl, vec3 L, vec3 V)
{
  switch (cl.type) {
    case CLOSURE_BSDF_TRANSLUCENT_ID:
      return bsdf_lambert(-cl.N, L);
    case CLOSURE_BSSRDF_BURLEY_ID:
    case CLOSURE_BSDF_DIFFUSE_ID:
      return bsdf_lambert(cl.N, L);
    case CLOSURE_BSDF_MICROFACET_GGX_REFLECTION_ID:
      return bsdf_ggx_reflect(
          cl.N, L, V, square(max(BSDF_ROUGHNESS_THRESHOLD, to_closure_reflection(cl).roughness)));
    case CLOSURE_BSDF_MICROFACET_GGX_REFRACTION_ID:
      return bsdf_ggx_refract(
          cl.N,
          L,
          V,
          square(max(BSDF_ROUGHNESS_THRESHOLD, to_closure_refraction(cl).roughness)),
          to_closure_refraction(cl).ior);
    case CLOSURE_NONE_ID:
    default:
      return 0.0;
  }
}

/* Tag pixel radiance as invalid. */
void invalid_pixel_write(ivec2 texel)
{
  imageStore(out_radiance_img, texel, vec4(FLT_11_11_10_MAX, 0.0));
  imageStore(out_variance_img, texel, vec4(0.0));
  imageStore(out_hit_depth_img, texel, vec4(0.0));
}

void main()
{
  const uint tile_size = RAYTRACE_GROUP_SIZE;
  uvec2 tile_coord = unpackUvec2x16(tiles_coord_buf[gl_WorkGroupID.x]);

#ifdef GPU_METAL
  int rt_resolution_scale = raytrace_resolution_scale;
#else /* TODO(fclem): Support specialization on OpenGL and Vulkan. */
  int rt_resolution_scale = uniform_buf.raytrace.resolution_scale;
#endif

  ivec2 texel_fullres = ivec2(gl_LocalInvocationID.xy + tile_coord * tile_size);
  ivec2 texel = (texel_fullres) / rt_resolution_scale;

#ifdef GPU_METAL
  bool do_skip_denoise = skip_denoise;
#else /* TODO(fclem): Support specialization on OpenGL and Vulkan. */
  bool do_skip_denoise = uniform_buf.raytrace.skip_denoise;
#endif
  if (do_skip_denoise) {
    imageStore(out_radiance_img, texel_fullres, imageLoad(ray_radiance_img, texel));
    return;
  }

  /* Clear neighbor tiles that will not be processed. */
  /* TODO(fclem): Optimize this. We don't need to clear the whole ring. */
  for (int x = -1; x <= 1; x++) {
    for (int y = -1; y <= 1; y++) {
      if (x == 0 && y == 0) {
        continue;
      }

      ivec2 tile_coord_neighbor = ivec2(tile_coord) + ivec2(x, y);
      if (!in_image_range(tile_coord_neighbor, tile_mask_img)) {
        continue;
      }

      ivec3 sample_tile = ivec3(tile_coord_neighbor, closure_index);

      uint tile_mask = imageLoad(tile_mask_img, sample_tile).r;
      bool tile_is_unused = !flag_test(tile_mask, 1u << 0u);
      if (tile_is_unused) {
        ivec2 texel_fullres_neighbor = texel_fullres + ivec2(x, y) * int(tile_size);
        invalid_pixel_write(texel_fullres_neighbor);
      }
    }
  }

  bool valid_texel = in_texture_range(texel_fullres, gbuf_header_tx);
  if (!valid_texel) {
    invalid_pixel_write(texel_fullres);
    return;
  }

  ClosureUndetermined closure = gbuffer_read_bin(
      gbuf_header_tx, gbuf_closure_tx, gbuf_normal_tx, texel_fullres, closure_index);

  if (closure.type == CLOSURE_NONE_ID) {
    invalid_pixel_write(texel_fullres);
    return;
  }

  vec2 uv = (vec2(texel_fullres) + 0.5) * uniform_buf.raytrace.full_resolution_inv;
  vec3 P = drw_point_screen_to_world(vec3(uv, 0.5));
  vec3 V = drw_world_incident_vector(P);

  /* Compute filter size and needed sample count */
  float apparent_roughness = closure_apparent_roughness_get(closure);
  float filter_size_factor = saturate(apparent_roughness * 8.0);
  uint sample_count = 1u + uint(15.0 * filter_size_factor + 0.5);
  /* NOTE: filter_size should never be greater than twice RAYTRACE_GROUP_SIZE. Otherwise, the
   * reconstruction can becomes ill defined since we don't know if further tiles are valid. */
  float filter_size = 12.0 * sqrt(filter_size_factor);
  if (rt_resolution_scale > 1) {
    /* Filter at least 1 trace pixel to fight the undersampling. */
    filter_size = max(filter_size, 3.0);
    sample_count = max(sample_count, 5u);
  }

  vec2 noise = utility_tx_fetch(utility_tx, vec2(texel_fullres), UTIL_BLUE_NOISE_LAYER).ba;
  noise += sampling_rng_1D_get(SAMPLING_CLOSURE);

  vec3 rgb_moment = vec3(0.0);
  vec3 radiance_accum = vec3(0.0);
  float weight_accum = 0.0;
  float closest_hit_time = 1.0e10;

  for (uint i = 0u; i < sample_count; i++) {
    vec2 offset_f = (fract(hammersley_2d(i, sample_count) + noise) - 0.5) * filter_size;
    ivec2 offset = ivec2(floor(offset_f + 0.5));
    ivec2 sample_texel = texel + offset;

    vec4 ray_data = imageLoad(ray_data_img, sample_texel);
    float ray_time = imageLoad(ray_time_img, sample_texel).r;
    vec4 ray_radiance = imageLoad(ray_radiance_img, sample_texel);

    vec3 ray_direction = ray_data.xyz;
    float ray_pdf_inv = abs(ray_data.w);
    /* Skip invalid pixels. */
    if (ray_pdf_inv == 0.0) {
      continue;
    }

    closest_hit_time = min(closest_hit_time, ray_time);

    /* Slide 54. */
    /* TODO(fclem): Apparently, ratio estimator should be pdf_bsdf / pdf_ray. */
    float weight = bxdf_eval(closure, ray_direction, V) * ray_pdf_inv;

    radiance_accum += ray_radiance.rgb * weight;
    weight_accum += weight;

    rgb_moment += square(ray_radiance.rgb) * weight;
  }
  float inv_weight = safe_rcp(weight_accum);

  radiance_accum *= inv_weight;
  /* Use radiance sum as signal mean. */
  vec3 rgb_mean = radiance_accum;
  rgb_moment *= inv_weight;

  vec3 rgb_variance = abs(rgb_moment - square(rgb_mean));
  float hit_variance = reduce_max(rgb_variance);

  float scene_z = drw_depth_screen_to_view(texelFetch(depth_tx, texel_fullres, 0).r);
  float hit_depth = drw_depth_view_to_screen(scene_z - closest_hit_time);

  imageStore(out_radiance_img, texel_fullres, vec4(radiance_accum, 0.0));
  imageStore(out_variance_img, texel_fullres, vec4(hit_variance));
  imageStore(out_hit_depth_img, texel_fullres, vec4(hit_depth));
}

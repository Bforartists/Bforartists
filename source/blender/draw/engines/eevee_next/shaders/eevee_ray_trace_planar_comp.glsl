/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/**
 * Use screen space tracing against depth buffer of recorded planar capture to find intersection
 * with the scene and its radiance.
 * This pass runs before the screen trace and evaluates valid rays for planar probes. These rays
 * are then tagged to avoid re-evaluation by screen trace.
 */

#pragma BLENDER_REQUIRE(eevee_lightprobe_eval_lib.glsl)
#pragma BLENDER_REQUIRE(eevee_bxdf_sampling_lib.glsl)
#pragma BLENDER_REQUIRE(eevee_sampling_lib.glsl)
#pragma BLENDER_REQUIRE(eevee_ray_types_lib.glsl)
#pragma BLENDER_REQUIRE(eevee_ray_trace_screen_lib.glsl)

void main()
{
  const uint tile_size = RAYTRACE_GROUP_SIZE;
  uvec2 tile_coord = unpackUvec2x16(tiles_coord_buf[gl_WorkGroupID.x]);
  ivec2 texel = ivec2(gl_LocalInvocationID.xy + tile_coord * tile_size);

  vec4 ray_data = imageLoad(ray_data_img, texel);
  float ray_pdf_inv = ray_data.w;

  if (ray_pdf_inv == 0.0) {
    /* Invalid ray or pixels without ray. Do not trace. */
    imageStore(ray_time_img, texel, vec4(0.0));
    imageStore(ray_radiance_img, texel, vec4(0.0));
    return;
  }

  ivec2 texel_fullres = texel * uniform_buf.raytrace.resolution_scale +
                        uniform_buf.raytrace.resolution_bias;

  float depth = texelFetch(depth_tx, texel_fullres, 0).r;
  vec2 uv = (vec2(texel_fullres) + 0.5) * uniform_buf.raytrace.full_resolution_inv;

  vec3 P = drw_point_screen_to_world(vec3(uv, depth));
  vec3 V = drw_world_incident_vector(P);

  int planar_id = lightprobe_planar_select(P, V, ray_data.xyz);
  if (planar_id == -1) {
    return;
  }

  ProbePlanarData planar = probe_planar_buf[planar_id];

  /* Tag the ray data so that screen trace will not try to evaluate it and override the result. */
  imageStore(ray_data_img, texel, vec4(ray_data.xyz, -ray_data.w));

  Ray ray;
  ray.origin = P;
  ray.direction = ray_data.xyz;

  vec3 radiance = vec3(0.0);
  float noise_offset = sampling_rng_1D_get(SAMPLING_RAYTRACE_W);
  float rand_trace = interlieved_gradient_noise(vec2(texel), 5.0, noise_offset);

  /* TODO(fclem): Take IOR into account in the roughness LOD bias. */
  /* TODO(fclem): pdf to roughness mapping is a crude approximation. Find something better. */
  float roughness = saturate(sample_pdf_uniform_hemisphere() / ray_pdf_inv);

  /* Transform the ray into planar view-space. */
  Ray ray_view;
  ray_view.origin = transform_point(planar.viewmat, ray.origin);
  ray_view.direction = transform_direction(planar.viewmat, ray.direction);
  /* Extend the ray to cover the whole view. */
  ray_view.max_time = 1000.0;

  ScreenTraceHitData hit = raytrace_planar(
      uniform_buf.raytrace, planar_depth_tx, planar, rand_trace, ray_view);

  if (hit.valid) {
    /* Evaluate radiance at hit-point. */
    radiance = textureLod(planar_radiance_tx, vec3(hit.ss_hit_P.xy, planar_id), 0.0).rgb;

    /* Transmit twice if thickness is set and ray is longer than thickness. */
    // if (thickness > 0.0 && length(ray_data.xyz) > thickness) {
    //   ray_radiance.rgb *= color;
    // }
  }
  else {
    /* Using ray direction as geometric normal to bias the sampling position.
     * This is faster than loading the gbuffer again and averages between reflected and normal
     * direction over many rays. */
    vec3 Ng = ray.direction;
    /* Fallback to nearest light-probe. */
    LightProbeSample samp = lightprobe_load(P, Ng, V);
    radiance = lightprobe_eval_direction(samp, P, ray.direction, safe_rcp(ray_pdf_inv));
    /* Set point really far for correct reprojection of background. */
    hit.time = 10000.0;
  }

  float luma = max(1e-8, reduce_max(radiance));
  radiance *= 1.0 - max(0.0, luma - uniform_buf.raytrace.brightness_clamp) / luma;

  imageStore(ray_time_img, texel, vec4(hit.time));
  imageStore(ray_radiance_img, texel, vec4(radiance, 0.0));
}

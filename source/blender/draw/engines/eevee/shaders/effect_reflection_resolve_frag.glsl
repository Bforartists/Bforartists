/* SPDX-FileCopyrightText: 2017-2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#pragma BLENDER_REQUIRE(common_math_lib.glsl)
#pragma BLENDER_REQUIRE(common_math_geom_lib.glsl)
#pragma BLENDER_REQUIRE(closure_eval_glossy_lib.glsl)
#pragma BLENDER_REQUIRE(closure_eval_lib.glsl)
#pragma BLENDER_REQUIRE(lightprobe_lib.glsl)
#pragma BLENDER_REQUIRE(bsdf_common_lib.glsl)
#pragma BLENDER_REQUIRE(surface_lib.glsl)
#pragma BLENDER_REQUIRE(effect_reflection_lib.glsl)

/* Based on:
 * "Stochastic Screen Space Reflections"
 * by Tomasz Stachowiak.
 * https://www.ea.com/frostbite/news/stochastic-screen-space-reflections
 * and
 * "Stochastic all the things: raytracing in hybrid real-time rendering"
 * by Tomasz Stachowiak.
 * https://media.contentapi.ea.com/content/dam/ea/seed/presentations/dd18-seed-raytracing-in-hybrid-real-time-rendering.pdf
 */

vec4 ssr_get_scene_color_and_mask(vec3 hit_vP, int planar_index, float mip)
{
  vec2 uv;
  if (planar_index != -1) {
    uv = get_uvs_from_view(hit_vP);
    /* Planar X axis is flipped. */
    uv.x = 1.0 - uv.x;
  }
  else {
    /* Find hit position in previous frame. */
    /* TODO: Combine matrices. */
    vec3 hit_P = transform_point(ViewMatrixInverse, hit_vP);
    /* TODO: real reprojection with motion vectors, etc... */
    uv = project_point(pastViewProjectionMatrix, hit_P).xy * 0.5 + 0.5;
  }

  vec3 color;
  if (planar_index != -1) {
    color = textureLod(probePlanars, vec3(uv, planar_index), mip).rgb;
  }
  else {

    /* Do not sample scene buffer if running probe pass in split reflection mode. */
#ifndef RESOLVE_PROBE
    color = textureLod(colorBuffer, uv * hizUvScale.xy, mip).rgb;
#else
    color = vec3(0.0);
#endif
  }

  /* Clamped brightness. */
  float luma = max_v3(color);
  color *= 1.0 - max(0.0, luma - ssrFireflyFac) * safe_rcp(luma);

  float mask = screen_border_mask(uv);
  return vec4(color, mask);
}

void resolve_reflection_sample(int planar_index,
                               vec2 sample_uv,
                               vec3 vP,
                               vec3 vN,
                               vec3 vV,
                               float roughness_squared,
                               float cone_tan,
                               inout float weight_accum,
                               inout vec4 ssr_accum)
{
  vec4 hit_data = texture(hitBuffer, sample_uv);
  float hit_depth = texture(hitDepth, sample_uv).r;
  HitData data = decode_hit_data(hit_data, hit_depth);

  float hit_dist = length(data.hit_dir);

  /* Slide 54. */
  float bsdf = bsdf_ggx(vN, data.hit_dir / hit_dist, vV, roughness_squared);

  float weight = bsdf * data.ray_pdf_inv;

  /* Do not reuse hit-point from planar reflections for normal reflections and vice versa. */
  if ((planar_index == -1 && data.is_planar) || (planar_index != -1 && !data.is_planar)) {
    return;
  }
  /* Do not add light if ray has failed but still weight it. */
  if (!data.is_hit) {
    weight_accum += weight;
    return;
  }

  vec3 hit_vP = vP + data.hit_dir;

  /* Compute cone footprint in screen space. */
  float cone_footprint = hit_dist * cone_tan;
  float homcoord = ProjectionMatrix[2][3] * hit_vP.z + ProjectionMatrix[3][3];
  cone_footprint *= max(ProjectionMatrix[0][0], ProjectionMatrix[1][1]) / homcoord;
  cone_footprint *= ssrBrdfBias * 0.5;
  /* Estimate a cone footprint to sample a corresponding mipmap level. */
  float mip = log2(cone_footprint * max_v2(vec2(textureSize(specroughBuffer, 0))));

  vec4 radiance_mask = ssr_get_scene_color_and_mask(hit_vP, planar_index, mip);

  ssr_accum += radiance_mask * weight;
  weight_accum += weight;
}

/* NOTE(Metal): For Apple silicon GPUs executing this particular shader, by default, memory read
 * pressure is high while ALU remains low. Packing the sample data into a smaller format balances
 * this trade-off by reducing local shader register pressure and expensive memory look-ups into
 * spilled local shader memory, resulting in an increase in performance of 20% for this shader. */
#ifdef GPU_METAL
#  define SAMPLE_STORAGE_TYPE uchar
#  define pack_sample(x, y) uchar(((uchar(x + 2)) << uchar(3)) + (uchar(y + 2)))
#  define unpack_sample(x) vec2((char(x) >> 3) - 2, (char(x) & 7) - 2)
#else
#  define SAMPLE_STORAGE_TYPE vec2
#  define pack_sample(x, y) SAMPLE_STORAGE_TYPE(x, y)
#  define unpack_sample(x) x
#endif

void raytrace_resolve(ClosureInputGlossy cl_in,
                      inout ClosureEvalGlossy cl_eval,
                      inout ClosureEvalCommon cl_common,
                      inout ClosureOutputGlossy cl_out)
{
  /* Note: Reflection samples declared in function scope to avoid per-thread memory pressure on
   * tile-based GPUs e.g. Apple Silicon. */
  const SAMPLE_STORAGE_TYPE resolve_sample_offsets[36] = SAMPLE_STORAGE_TYPE[36](
      /* Set 1. */
      /* First Ring (2x2). */
      pack_sample(0, 0),
      /* Second Ring (6x6). */
      pack_sample(-1, 3),
      pack_sample(1, 3),
      pack_sample(-1, 1),
      pack_sample(3, 1),
      pack_sample(-2, 0),
      pack_sample(3, 0),
      pack_sample(2, -1),
      pack_sample(1, -2),
      /* Set 2. */
      /* First Ring (2x2). */
      pack_sample(1, 1),
      /* Second Ring (6x6). */
      pack_sample(-2, 3),
      pack_sample(3, 3),
      pack_sample(0, 2),
      pack_sample(2, 2),
      pack_sample(-2, -1),
      pack_sample(1, -1),
      pack_sample(0, -2),
      pack_sample(3, -2),
      /* Set 3. */
      /* First Ring (2x2). */
      pack_sample(0, 1),
      /* Second Ring (6x6). */
      pack_sample(0, 3),
      pack_sample(3, 2),
      pack_sample(-2, 1),
      pack_sample(2, 1),
      pack_sample(-1, 0),
      pack_sample(-2, -2),
      pack_sample(0, -1),
      pack_sample(2, -2),
      /* Set 4. */
      /* First Ring (2x2). */
      pack_sample(1, 0),
      /* Second Ring (6x6). */
      pack_sample(2, 3),
      pack_sample(-2, 2),
      pack_sample(-1, 2),
      pack_sample(1, 2),
      pack_sample(2, 0),
      pack_sample(-1, -1),
      pack_sample(3, -1),
      pack_sample(-1, -2));

  float roughness = cl_in.roughness;

  vec4 ssr_accum = vec4(0.0);
  float weight_acc = 0.0;

  if (roughness < ssrMaxRoughness + 0.2) {
    /* Find Planar Reflections affecting this pixel */
    int planar_index = -1;
    for (int i = 0; i < MAX_PLANAR && i < prbNumPlanar; i++) {
      float fade = probe_attenuation_planar(planars_data[i], cl_common.P);
      fade *= probe_attenuation_planar_normal_roughness(planars_data[i], cl_in.N, 0.0);
      if (fade > 0.5) {
        planar_index = i;
        break;
      }
    }

    vec3 V, P, N;
    if (planar_index != -1) {
      PlanarData pd = planars_data[planar_index];
      /* Evaluate everything in reflected space. */
      P = line_plane_intersect(cl_common.P, cl_common.V, pd.pl_plane_eq);
      V = reflect(cl_common.V, pd.pl_normal);
      N = reflect(cl_in.N, pd.pl_normal);
    }
    else {
      V = cl_common.V;
      P = cl_common.P;
      N = cl_in.N;
    }

    /* Using view space */
    vec3 vV = transform_direction(ViewMatrix, cl_common.V);
    vec3 vP = transform_point(ViewMatrix, cl_common.P);
    vec3 vN = transform_direction(ViewMatrix, cl_in.N);

    float roughness_squared = max(1e-3, sqr(roughness));
    float cone_cos = cone_cosine(roughness_squared);
    float cone_tan = sqrt(1.0 - cone_cos * cone_cos) / cone_cos;
    cone_tan *= mix(saturate(dot(vN, -vV) * 2.0), 1.0, roughness); /* Elongation fit */

    int sample_pool = int((uint(gl_FragCoord.x) & 1u) + (uint(gl_FragCoord.y) & 1u) * 2u);
    sample_pool = (sample_pool + (samplePoolOffset / 5)) % 4;

    for (int i = 0; i < resolve_samples_count; i++) {
      int sample_id = sample_pool * resolve_samples_count + i;
      vec2 texture_size = vec2(textureSize(hitBuffer, 0));
      vec2 sample_texel = texture_size * uvcoordsvar.xy * ssrUvScale;
      vec2 sample_uv = (sample_texel + unpack_sample(resolve_sample_offsets[sample_id])) /
                       texture_size;

      resolve_reflection_sample(
          planar_index, sample_uv, vP, vN, vV, roughness_squared, cone_tan, weight_acc, ssr_accum);
    }
  }

  /* Compute SSR contribution */
  ssr_accum *= safe_rcp(weight_acc);
  /* fade between 0.5 and 1.0 roughness */
  ssr_accum.a *= smoothstep(ssrMaxRoughness + 0.2, ssrMaxRoughness, roughness);

  cl_eval.raytrace_radiance = ssr_accum.rgb * ssr_accum.a;
  cl_common.specular_accum -= ssr_accum.a;
}

CLOSURE_EVAL_FUNCTION_DECLARE_1(ssr_resolve, Glossy)

void main()
{
  float depth = textureLod(maxzBuffer, uvcoordsvar.xy * hizUvScale.xy, 0.0).r;
#if defined(GPU_INTEL) && defined(GPU_METAL)
  float factor = 1.0f;
#endif
  if (depth == 1.0) {
#if defined(GPU_INTEL) && defined(GPU_METAL)
    /* Divergent code execution (and sampling) causes corruption due to undefined
     * derivative/sampling behavior, on Intel GPUs. Using a mask factor to ensure shaders do not
     * diverge and only the final result is masked. */
    factor = 0.0f;
#else
    /* Note: In the Metal API, prior to Metal 2.3, Discard is not an explicit return and can
     * produce undefined behavior. This is especially prominent with derivatives if control-flow
     * divergence is present.
     *
     * Adding a return call eliminates undefined behavior and a later out-of-bounds read causing
     * a crash on AMD platforms.
     * This behavior can also affect OpenGL on certain devices. */
    discard;
    return;
#endif
  }

  ivec2 texel = ivec2(gl_FragCoord.xy);
  vec4 speccol_roughness = texelFetch(specroughBuffer, texel, 0).rgba;
  vec3 brdf = speccol_roughness.rgb;
  float roughness = speccol_roughness.a;

  if (max_v3(brdf) <= 0.0) {
#if defined(GPU_INTEL) && defined(GPU_METAL)
    factor = 0.0f;
#else
    discard;
    return;
#endif
  }

  FragDepth = depth;

  viewPosition = get_view_space_from_depth(uvcoordsvar.xy, depth);
  worldPosition = transform_point(ViewMatrixInverse, viewPosition);

  vec2 normal_encoded = texelFetch(normalBuffer, texel, 0).rg;
  viewNormal = normal_decode(normal_encoded, viewCameraVec(viewPosition));
  worldNormal = transform_direction(ViewMatrixInverse, viewNormal);

  CLOSURE_VARS_DECLARE_1(Glossy);

  in_Glossy_0.N = worldNormal;
  in_Glossy_0.roughness = roughness;

  /* Do a full deferred evaluation of the glossy BSDF. The only difference is that we inject the
   * SSR resolve before the cube-map iter. BRDF term is already computed during main pass and is
   * passed as specular color. */
  CLOSURE_EVAL_FUNCTION_1(ssr_resolve, Glossy);

  /* Default single pass resolve */
  fragColor = vec4(out_Glossy_0.radiance * brdf, 1.0);
#if defined(GPU_INTEL) && defined(GPU_METAL)
  /* Due to non-uniform control flow with discard, Intel on macOS requires blending factor
   * to discard unwanted fragments. */
  fragColor *= factor;
#endif
}

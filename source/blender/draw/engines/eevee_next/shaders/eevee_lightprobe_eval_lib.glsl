/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#pragma BLENDER_REQUIRE(gpu_shader_math_base_lib.glsl)
#pragma BLENDER_REQUIRE(gpu_shader_codegen_lib.glsl)
#pragma BLENDER_REQUIRE(eevee_lightprobe_lib.glsl)
#pragma BLENDER_REQUIRE(eevee_ray_generate_lib.glsl)
#pragma BLENDER_REQUIRE(eevee_reflection_probe_eval_lib.glsl)
#pragma BLENDER_REQUIRE(eevee_lightprobe_volume_eval_lib.glsl)
#pragma BLENDER_REQUIRE(eevee_sampling_lib.glsl)
#pragma BLENDER_REQUIRE(eevee_spherical_harmonics_lib.glsl)

#ifdef REFLECTION_PROBE

struct LightProbeSample {
  SphericalHarmonicL1 volume_irradiance;
  int spherical_id;
};

/**
 * Return cached light-probe data at P.
 * Ng and V are use for biases.
 */
LightProbeSample lightprobe_load(vec3 P, vec3 Ng, vec3 V)
{
  /* TODO: Dependency hell */
  float noise = 0.0;

  LightProbeSample result;
  result.volume_irradiance = lightprobe_irradiance_sample(P, V, Ng);
  result.spherical_id = reflection_probes_select(P, noise);
  return result;
}

/* Return the best parallax corrected ray direction from the probe center. */
vec3 lightprobe_sphere_parallax(ReflectionProbeData probe, vec3 P, vec3 L)
{
  bool is_world = (probe.influence_scale == 0.0);
  if (is_world) {
    return L;
  }
  /* Correct reflection ray using parallax volume intersection. */
  vec3 lP = vec4(P, 1.0) * probe.world_to_probe_transposed;
  vec3 lL = (mat3x3(probe.world_to_probe_transposed) * L) / probe.parallax_distance;

  float dist = (probe.parallax_shape == SHAPE_ELIPSOID) ? line_unit_sphere_intersect_dist(lP, lL) :
                                                          line_unit_box_intersect_dist(lP, lL);

  /* Use distance in world space directly to recover intersection.
   * This works because we assume no shear in the probe matrix. */
  vec3 L_new = P + L * dist - probe.location;

  /* TODO(fclem): Roughness adjustment. */

  return L_new;
}

/**
 * Return spherical sample normalized by irradiance at sample position.
 * This avoid most of light leaking and reduce the need for many local probes.
 */
vec3 lightprobe_spherical_sample_normalized_with_parallax(
    int probe_index, vec3 P, vec3 L, float lod, SphericalHarmonicL1 P_sh)
{
  ReflectionProbeData probe = reflection_probe_buf[probe_index];
  ReflectionProbeLowFreqLight shading_sh = reflection_probes_extract_low_freq(P_sh);
  vec3 normalization_factor = reflection_probes_normalization_eval(
      L, shading_sh, probe.low_freq_light);
  L = lightprobe_sphere_parallax(probe, P, L);
  return normalization_factor * reflection_probes_sample(L, lod, probe.atlas_coord).rgb;
}

float pdf_to_lod(float pdf)
{
  return 1.0; /* TODO */
}

vec3 lightprobe_eval_direction(LightProbeSample samp, vec3 P, vec3 L, float pdf)
{
  vec3 radiance_sh = lightprobe_spherical_sample_normalized_with_parallax(
      samp.spherical_id, P, L, pdf_to_lod(pdf), samp.volume_irradiance);

  return radiance_sh;
}

float lightprobe_roughness_to_cube_sh_mix_fac(float roughness)
{
  /* Temporary. Do something better. */
  return square(saturate(roughness * 4.0 - 2.0));
}

float lightprobe_roughness_to_lod(float roughness)
{
  /* Temporary. Do something better. */
  return sqrt(roughness) * REFLECTION_PROBE_MIPMAP_LEVELS;
}

vec3 lightprobe_eval(LightProbeSample samp, ClosureDiffuse cl, vec3 P, vec3 V)
{
  vec3 radiance_sh = spherical_harmonics_evaluate_lambert(cl.N, samp.volume_irradiance);
  return radiance_sh;
}

vec3 lightprobe_eval(LightProbeSample samp, ClosureTranslucent cl, vec3 P, vec3 V)
{
  vec3 radiance_sh = spherical_harmonics_evaluate_lambert(-cl.N, samp.volume_irradiance);
  return radiance_sh;
}

vec3 lightprobe_reflection_dominant_dir(vec3 N, vec3 V, float roughness)
{
  vec3 R = -reflect(V, N);
  float smoothness = 1.0 - roughness;
  float fac = smoothness * (sqrt(smoothness) + roughness);
  return normalize(mix(N, R, fac));
}

vec3 lightprobe_eval(LightProbeSample samp, ClosureReflection reflection, vec3 P, vec3 V)
{
  vec3 L = lightprobe_reflection_dominant_dir(reflection.N, V, reflection.roughness);

  float lod = lightprobe_roughness_to_lod(reflection.roughness);
  vec3 radiance_cube = lightprobe_spherical_sample_normalized_with_parallax(
      samp.spherical_id, P, L, lod, samp.volume_irradiance);

  float fac = lightprobe_roughness_to_cube_sh_mix_fac(reflection.roughness);
  vec3 radiance_sh = spherical_harmonics_evaluate_lambert(L, samp.volume_irradiance);
  return mix(radiance_cube, radiance_sh, fac);
}

vec3 lightprobe_refraction_dominant_dir(vec3 N, vec3 V, float ior, float roughness)
{
  vec3 R = refract(-V, N, 1.0 / ior);
  float smoothness = 1.0 - roughness;
  float fac = smoothness * (sqrt(smoothness) + roughness);
  return normalize(mix(-N, R, fac));
}

vec3 lightprobe_eval(LightProbeSample samp, ClosureRefraction cl, vec3 P, vec3 V)
{
  vec3 L = lightprobe_refraction_dominant_dir(cl.N, V, cl.ior, cl.roughness);

  float lod = lightprobe_roughness_to_lod(cl.roughness);
  vec3 radiance_cube = lightprobe_spherical_sample_normalized_with_parallax(
      samp.spherical_id, P, L, lod, samp.volume_irradiance);

  float fac = lightprobe_roughness_to_cube_sh_mix_fac(cl.roughness);
  vec3 radiance_sh = spherical_harmonics_evaluate_lambert(L, samp.volume_irradiance);
  return mix(radiance_cube, radiance_sh, fac);
}

#endif /* REFLECTION_PROBE */

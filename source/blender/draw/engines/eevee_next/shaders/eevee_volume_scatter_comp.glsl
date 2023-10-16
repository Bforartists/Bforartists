/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/* Based on Frosbite Unified Volumetric.
 * https://www.ea.com/frostbite/news/physically-based-unified-volumetric-rendering-in-frostbite */

/* Step 2 : Evaluate all light scattering for each froxels.
 * Also do the temporal reprojection to fight aliasing artifacts. */

#pragma BLENDER_REQUIRE(gpu_shader_math_vector_lib.glsl)

/* Included here to avoid requiring lightprobe resources for all volume lib users. */
#pragma BLENDER_REQUIRE(eevee_lightprobe_eval_lib.glsl)
#pragma BLENDER_REQUIRE(eevee_volume_lib.glsl)
#pragma BLENDER_REQUIRE(eevee_sampling_lib.glsl)

#pragma BLENDER_REQUIRE(eevee_volume_lib.glsl)
#pragma BLENDER_REQUIRE(eevee_sampling_lib.glsl)

#ifdef VOLUME_LIGHTING

vec3 volume_scatter_light_eval(
    const bool is_directional, vec3 P, vec3 V, uint l_idx, float s_anisotropy)
{
  LightData light = light_buf[l_idx];

  if (light.power[LIGHT_VOLUME] == 0.0) {
    return vec3(0);
  }

  LightVector lv = light_shape_vector_get(light, is_directional, P);

  float attenuation = light_attenuation_volume(light, is_directional, lv);
  if (attenuation < LIGHT_ATTENUATION_THRESHOLD) {
    return vec3(0);
  }

  float visibility = attenuation;
  if (light.tilemap_index != LIGHT_NO_SHADOW) {
    visibility *= shadow_sample(is_directional, shadow_atlas_tx, shadow_tilemaps_tx, light, P)
                      .light_visibilty;
  }

  if (visibility < LIGHT_ATTENUATION_THRESHOLD) {
    return vec3(0);
  }

  vec3 Li = volume_light(light, is_directional, lv) *
            volume_shadow(light, is_directional, P, lv, extinction_tx);
  return Li * visibility * volume_phase_function(-V, lv.L, s_anisotropy);
}

#endif

void main()
{
  ivec3 froxel = ivec3(gl_GlobalInvocationID);

  if (any(greaterThanEqual(froxel, uniform_buf.volumes.tex_size))) {
    return;
  }

  /* Emission. */
  vec3 scattering = imageLoad(in_emission_img, froxel).rgb;
  vec3 extinction = imageLoad(in_extinction_img, froxel).rgb;
  vec3 s_scattering = imageLoad(in_scattering_img, froxel).rgb;

  vec3 jitter = sampling_rng_3D_get(SAMPLING_VOLUME_U);
  vec3 volume_screen = volume_to_screen((vec3(froxel) + jitter) *
                                        uniform_buf.volumes.inv_tex_size);
  vec3 vP = drw_point_screen_to_view(volume_screen);
  vec3 P = drw_point_view_to_world(vP);
  vec3 V = drw_world_incident_vector(P);

  vec2 phase = imageLoad(in_phase_img, froxel).rg;
  /* Divide by phase total weight, to compute the mean anisotropy. */
  float s_anisotropy = phase.x / max(1.0, phase.y);

  scattering += volume_irradiance(P) * s_scattering * volume_phase_function_isotropic();

#ifdef VOLUME_LIGHTING

  LIGHT_FOREACH_BEGIN_DIRECTIONAL (light_cull_buf, l_idx) {
    scattering += volume_scatter_light_eval(true, P, V, l_idx, s_anisotropy) * s_scattering;
  }
  LIGHT_FOREACH_END

  vec2 pixel = (vec2(froxel.xy) + vec2(0.5)) / vec2(uniform_buf.volumes.tex_size.xy) /
               uniform_buf.volumes.viewport_size_inv;

  LIGHT_FOREACH_BEGIN_LOCAL (light_cull_buf, light_zbin_buf, light_tile_buf, pixel, vP.z, l_idx) {
    scattering += volume_scatter_light_eval(false, P, V, l_idx, s_anisotropy) * s_scattering;
  }
  LIGHT_FOREACH_END

#endif

  /* Catch NaNs. */
  if (any(isnan(scattering)) || any(isnan(extinction))) {
    scattering = vec3(0.0);
    extinction = vec3(0.0);
  }

  imageStore(out_scattering_img, froxel, vec4(scattering, 1.0));
  imageStore(out_extinction_img, froxel, vec4(extinction, 1.0));
}

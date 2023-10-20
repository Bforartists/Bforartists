/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/**
 * Virtual shadow-mapping: Usage tagging
 *
 * Shadow pages are only allocated if they are visible.
 * This pass scans all volume froxels and tags tiles needed for shadowing.
 */

#pragma BLENDER_REQUIRE(eevee_volume_lib.glsl)
#pragma BLENDER_REQUIRE(eevee_sampling_lib.glsl)
#pragma BLENDER_REQUIRE(eevee_shadow_tag_usage_lib.glsl)

void main()
{
  ivec3 froxel = ivec3(gl_GlobalInvocationID);

  if (any(greaterThanEqual(froxel, uniform_buf.volumes.tex_size))) {
    return;
  }

  vec3 extinction = imageLoad(in_extinction_img, froxel).rgb;
  vec3 scattering = imageLoad(in_scattering_img, froxel).rgb;

  if (is_zero(extinction) || is_zero(scattering)) {
    return;
  }

  vec3 jitter = sampling_rng_3D_get(SAMPLING_VOLUME_U);
  vec3 volume_ndc = volume_to_screen((vec3(froxel) + jitter) * uniform_buf.volumes.inv_tex_size);
  vec3 vP = drw_point_screen_to_view(vec3(volume_ndc.xy, volume_ndc.z));
  vec3 P = drw_point_view_to_world(vP);

  float depth = texelFetch(hiz_tx, froxel.xy, uniform_buf.volumes.tile_size_lod).r;
  if (depth < volume_ndc.z) {
    return;
  }

  vec2 pixel = (vec2(froxel.xy) + vec2(0.5)) / vec2(uniform_buf.volumes.tex_size.xy) /
               uniform_buf.volumes.viewport_size_inv;

  int bias = uniform_buf.volumes.tile_size_lod;
  shadow_tag_usage(vP, P, drw_world_incident_vector(P), 0.01, length(vP), pixel, bias);
}

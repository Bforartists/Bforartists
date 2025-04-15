/* SPDX-FileCopyrightText: 2018-2022 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#include "infos/overlay_armature_info.hh"

FRAGMENT_SHADER_CREATE_INFO(overlay_armature_sphere_solid)

#include "draw_view_lib.glsl"
#include "select_lib.glsl"

void main()
{
  constexpr float sphere_radius = 0.05f;

  bool is_perp = (drw_view().winmat[3][3] == 0.0f);
  float3 ray_ori_view = (is_perp) ? float3(0.0f) : viewPosition.xyz;
  float3 ray_dir_view = (is_perp) ? viewPosition : float3(0.0f, 0.0f, -1.0f);

  /* Single matrix mul without branch. */
  float4 mul_vec = (is_perp) ? float4(ray_dir_view, 0.0f) : float4(ray_ori_view, 1.0f);
  float3 mul_res = (sphereMatrix * mul_vec).xyz;

  /* Reminder :
   * sphereMatrix[3] is the view space origin in sphere space (sph_ori -> view_ori).
   * sphereMatrix[2] is the view space Z axis in sphere space. */

  /* convert to sphere local space */
  float3 ray_ori = (is_perp) ? sphereMatrix[3].xyz : mul_res;
  float3 ray_dir = (is_perp) ? mul_res : -sphereMatrix[2].xyz;
  float ray_len = length(ray_dir);
  ray_dir /= ray_len;

  /* Line to sphere intersect */
  constexpr float sphere_radius_sqr = sphere_radius * sphere_radius;
  float b = dot(ray_ori, ray_dir);
  float c = dot(ray_ori, ray_ori) - sphere_radius_sqr;
  float h = b * b - c;
  float t = -sqrt(max(0.0f, h)) - b;

  /* Compute dot product for lighting */
  float3 p = ray_dir * t + ray_ori; /* Point on sphere */
  float3 n = normalize(p);          /* Normal is just the point in sphere space, normalized. */
  float3 l = normalize(sphereMatrix[2].xyz); /* Just the view Z axis in the sphere space. */

  /* Smooth lighting factor. */
  constexpr float s = 0.2f; /* [0.0f-0.5f] range */
  float fac = clamp((dot(n, l) * (1.0f - s)) + s, 0.0f, 1.0f);
  fragColor.rgb = mix(finalStateColor, finalBoneColor, fac * fac);

  /* 2x2 dither pattern to smooth the lighting. */
  float dither = (0.5f + dot(float2(int2(gl_FragCoord.xy) & int2(1)), float2(1.0f, 2.0f))) * 0.25f;
  dither *= (1.0f / 255.0f); /* Assume 8bit per color buffer. */

  fragColor = float4(fragColor.rgb + dither, alpha);
  lineOutput = float4(0.0f);

  t /= ray_len;

#ifndef SELECT_ENABLE
  gl_FragDepth = drw_depth_view_to_screen(ray_dir_view.z * t + ray_ori_view.z);
#endif
  select_id_output(select_id);
}

/* SPDX-FileCopyrightText: 2018-2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#include "infos/overlay_edit_mode_info.hh"

FRAGMENT_SHADER_CREATE_INFO(overlay_depth_gpencil)

#include "draw_grease_pencil_lib.glsl"
#include "select_lib.glsl"

float3 ray_plane_intersection(float3 ray_ori, float3 ray_dir, float4 plane)
{
  float d = dot(plane.xyz, ray_dir);
  float3 plane_co = plane.xyz * (-plane.w / dot(plane.xyz, plane.xyz));
  float3 h = ray_ori - plane_co;
  float lambda = -dot(plane.xyz, h) / ((abs(d) < 1e-8f) ? 1e-8f : d);
  return ray_ori + ray_dir * lambda;
}

void main()
{
  if (gpencil_stroke_round_cap_mask(gp_interp_flat.sspos.xy,
                                    gp_interp_flat.sspos.zw,
                                    gp_interp_flat.aspect,
                                    gp_interp_noperspective.thickness.x,
                                    gp_interp_noperspective.hardness) < 0.001f)
  {
#ifndef SELECT_ENABLE
    /* We cannot discard the fragment in selection mode. Otherwise we would break pipeline
     * correctness (no discard if early depth test enforced). */
    discard;
#endif
    return;
  }

#ifndef SELECT_ENABLE
  /* We cannot change the fragment's depth in selection mode. Otherwise we would break pipeline
   * correctness when early depth test enforced. */
  if (!gpStrokeOrder3d) {
    /* Stroke order 2D. Project to gpDepthPlane. */
    bool is_persp = drw_view().winmat[3][3] == 0.0f;
    float2 uvs = float2(gl_FragCoord.xy) * sizeViewportInv;
    float3 pos_ndc = float3(uvs, gl_FragCoord.z) * 2.0f - 1.0f;
    float4 pos_world = drw_view().viewinv * (drw_view().wininv * float4(pos_ndc, 1.0f));
    float3 pos = pos_world.xyz / pos_world.w;

    float3 ray_ori = pos;
    float3 ray_dir = (is_persp) ? (drw_view().viewinv[3].xyz - pos) : drw_view().viewinv[2].xyz;
    float3 isect = ray_plane_intersection(ray_ori, ray_dir, gpDepthPlane);
    float4 ndc = drw_point_world_to_homogenous(isect);
    gl_FragDepth = (ndc.z / ndc.w) * 0.5f + 0.5f;
  }
  else {
    gl_FragDepth = gl_FragCoord.z;
  }
#endif

  /* This is optimized to NOP in the non select case. */
  select_id_output(select_id);
}

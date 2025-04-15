/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#include "infos/eevee_lightprobe_sphere_info.hh"

VERTEX_SHADER_CREATE_INFO(eevee_display_lightprobe_planar)

#include "draw_view_lib.glsl"
#include "gpu_shader_math_matrix_lib.glsl"

void main()
{
  /* Constant array moved inside function scope.
   * Minimizes local register allocation in MSL. */
  constexpr float2 pos[6] = float2_array(float2(-1.0f, -1.0f),
                                         float2(1.0f, -1.0f),
                                         float2(-1.0f, 1.0f),

                                         float2(1.0f, -1.0f),
                                         float2(1.0f, 1.0f),
                                         float2(-1.0f, 1.0f));

  float2 lP = pos[gl_VertexID % 6];
  int display_index = gl_VertexID / 6;

  probe_index = display_data_buf[display_index].probe_index;

  float4x4 plane_to_world = display_data_buf[display_index].plane_to_world;
  probe_normal = safe_normalize(plane_to_world[2].xyz);

  float3 P = transform_point(plane_to_world, float3(lP, 0.0f));
  gl_Position = drw_point_world_to_homogenous(P);
  /* Small bias to let the probe draw without Z-fighting. */
  gl_Position.z -= 0.0001f;
}

/* SPDX-FileCopyrightText: 2018-2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#pragma BLENDER_REQUIRE(common_view_lib.glsl)

void main()
{
  vData.pos = pos;
  vData.frontPosition = point_object_to_ndc(pos);
  vData_flat.light_direction_os = normal_world_to_object(vec3(pass_data.light_direction_ws));
  vec3 pos_ws = point_object_to_world(pos);
  float extrude_distance = 1e5f;
  float LDoFP = dot(pass_data.light_direction_ws, pass_data.far_plane.xyz);
  if (LDoFP > 0) {
    float signed_distance = dot(pass_data.far_plane.xyz, pos_ws) - pass_data.far_plane.w;
    extrude_distance = -signed_distance / LDoFP;
    /* Ensure we don't overlap the far plane. */
    extrude_distance -= 1e-3f;
  }
  vData.backPosition = point_world_to_ndc(pos_ws +
                                          pass_data.light_direction_ws * extrude_distance);
}

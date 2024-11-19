/* SPDX-FileCopyrightText: 2016-2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#include "infos/workbench_prepass_info.hh"

VERTEX_SHADER_CREATE_INFO(workbench_prepass)
VERTEX_SHADER_CREATE_INFO(workbench_lighting_flat)
VERTEX_SHADER_CREATE_INFO(workbench_transparent_accum)
VERTEX_SHADER_CREATE_INFO(workbench_pointcloud)

#include "draw_view_lib.glsl"

#include "draw_pointcloud_lib.glsl"
#include "draw_view_clipping_lib.glsl"

#include "workbench_common_lib.glsl"
#include "workbench_image_lib.glsl"
#include "workbench_material_lib.glsl"

void main()
{
  vec3 world_pos;
  pointcloud_get_pos_and_nor(world_pos, normal_interp);

  normal_interp = normalize(drw_normal_world_to_view(normal_interp));

  gl_Position = drw_point_world_to_homogenous(world_pos);

  view_clipping_distances(world_pos);

  uv_interp = vec2(0.0);

  workbench_material_data_get(
      int(drw_CustomID), vec3(1.0), color_interp, alpha_interp, _roughness, metallic);

  object_id = int(uint(resource_handle) & 0xFFFFu) + 1;
}

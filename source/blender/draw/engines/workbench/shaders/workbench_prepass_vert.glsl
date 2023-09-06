/* SPDX-FileCopyrightText: 2016-2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#pragma BLENDER_REQUIRE(common_view_clipping_lib.glsl)
#pragma BLENDER_REQUIRE(common_view_lib.glsl)
#pragma BLENDER_REQUIRE(workbench_common_lib.glsl)
#pragma BLENDER_REQUIRE(workbench_material_lib.glsl)
#pragma BLENDER_REQUIRE(workbench_image_lib.glsl)

void main()
{
  vec3 world_pos = point_object_to_world(pos);
  gl_Position = point_world_to_ndc(world_pos);

  view_clipping_distances(world_pos);

  uv_interp = au;

  normal_interp = normalize(normal_object_to_view(nor));

  object_id = int(uint(resource_id) & 0xFFFFu) + 1;

  workbench_material_data_get(
      int(drw_CustomID), ac.rgb, color_interp, alpha_interp, _roughness, metallic);
}

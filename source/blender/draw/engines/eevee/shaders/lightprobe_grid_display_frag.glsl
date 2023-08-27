/* SPDX-FileCopyrightText: 2017-2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#pragma BLENDER_REQUIRE(common_view_lib.glsl)
#pragma BLENDER_REQUIRE(irradiance_lib.glsl)

void main()
{
  float dist_sqr = dot(quadCoord, quadCoord);

  /* Discard outside the circle. */
  if (dist_sqr > 1.0) {
    discard;
    return;
  }

  vec3 view_nor = vec3(quadCoord, sqrt(max(0.0, 1.0 - dist_sqr)));
  vec3 world_nor = mat3(ViewMatrixInverse) * view_nor;
  IrradianceData ir_data = load_irradiance_cell(cellOffset, world_nor);
  FragColor = vec4(compute_irradiance(world_nor, ir_data), 1.0);
}

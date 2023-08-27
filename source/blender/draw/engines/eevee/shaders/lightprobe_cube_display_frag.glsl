/* SPDX-FileCopyrightText: 2017-2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#pragma BLENDER_REQUIRE(common_view_lib.glsl)
#pragma BLENDER_REQUIRE(lightprobe_lib.glsl)

void main()
{
  float dist_sqr = dot(quadCoord, quadCoord);

  /* Discard outside the circle. */
  if (dist_sqr > 1.0) {
    discard;
    return;
  }

  vec3 view_nor = vec3(quadCoord, sqrt(max(0.0, 1.0 - dist_sqr)));
  vec3 world_ref = mat3(ViewMatrixInverse) * reflect(vec3(0.0, 0.0, -1.0), view_nor);
  FragColor = vec4(textureLod_cubemapArray(probeCubes, vec4(world_ref, pid), 0.0).rgb, 1.0);
}

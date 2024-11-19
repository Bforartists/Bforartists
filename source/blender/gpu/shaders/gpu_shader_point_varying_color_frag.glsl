/* SPDX-FileCopyrightText: 2016-2022 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#include "infos/gpu_shader_2D_point_varying_size_varying_color_info.hh"

FRAGMENT_SHADER_CREATE_INFO(gpu_shader_2D_point_varying_size_varying_color)

void main()
{
  vec2 centered = gl_PointCoord - vec2(0.5);
  float dist_squared = dot(centered, centered);
  const float rad_squared = 0.25;

  /* Round point with jagged edges. */
  if (dist_squared > rad_squared) {
    discard;
  }

  fragColor = finalColor;
}

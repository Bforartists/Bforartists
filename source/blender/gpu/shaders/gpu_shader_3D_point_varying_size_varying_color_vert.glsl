/* SPDX-FileCopyrightText: 2016-2022 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#include "infos/gpu_shader_3D_point_info.hh"

VERTEX_SHADER_CREATE_INFO(gpu_shader_3D_point_varying_size_varying_color)

void main()
{
  gl_Position = ModelViewProjectionMatrix * vec4(pos, 1.0);
  gl_PointSize = size;
  finalColor = color;
}

/* SPDX-FileCopyrightText: 2016-2022 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#include "infos/gpu_shader_3D_flat_color_info.hh"

#include "gpu_shader_cfg_world_clip_lib.glsl"

VERTEX_SHADER_CREATE_INFO(gpu_shader_3D_flat_color)

void main()
{
  vec4 pos_4d = vec4(pos, 1.0);
  gl_Position = ModelViewProjectionMatrix * pos_4d;
  finalColor = color;

#ifdef USE_WORLD_CLIP_PLANES
  world_clip_planes_calc_clip_distance((clipPlanes.ClipModelMatrix * pos_4d).xyz);
#endif
}

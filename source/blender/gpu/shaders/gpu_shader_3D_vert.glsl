/* SPDX-FileCopyrightText: 2016-2022 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#include "infos/gpu_shader_3D_depth_only_info.hh"

#include "gpu_shader_cfg_world_clip_lib.glsl"

VERTEX_SHADER_CREATE_INFO(gpu_shader_3D_depth_only)

void main()
{
  gl_Position = ModelViewProjectionMatrix * float4(pos, 1.0f);

#ifdef USE_WORLD_CLIP_PLANES
  world_clip_planes_calc_clip_distance((clipPlanes.ClipModelMatrix * float4(pos, 1.0f)).xyz);
#endif
}

/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#ifdef GPU_SHADER
#  pragma once
#  include "gpu_glsl_cpp_stubs.hh"

#  include "draw_common_shader_shared.hh"
#  include "draw_object_infos_info.hh"
#  include "draw_view_info.hh"
#endif

#include "overlay_common_info.hh"

GPU_SHADER_INTERFACE_INFO(overlay_sculpt_mask_iface)
FLAT(VEC3, faceset_color)
SMOOTH(FLOAT, mask_color)
SMOOTH(VEC4, finalColor)
GPU_SHADER_INTERFACE_END()

GPU_SHADER_CREATE_INFO(overlay_sculpt_mask)
DO_STATIC_COMPILATION()
PUSH_CONSTANT(FLOAT, maskOpacity)
PUSH_CONSTANT(FLOAT, faceSetsOpacity)
VERTEX_IN(0, VEC3, pos)
VERTEX_IN(1, VEC3, fset)
VERTEX_IN(2, FLOAT, msk)
VERTEX_OUT(overlay_sculpt_mask_iface)
VERTEX_SOURCE("overlay_sculpt_mask_vert.glsl")
FRAGMENT_SOURCE("overlay_sculpt_mask_frag.glsl")
FRAGMENT_OUT(0, VEC4, fragColor)
ADDITIONAL_INFO(draw_view)
ADDITIONAL_INFO(draw_modelmat)
ADDITIONAL_INFO(draw_globals)
GPU_SHADER_CREATE_END()

OVERLAY_INFO_CLIP_VARIATION(overlay_sculpt_mask)

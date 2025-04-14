/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#ifdef GPU_SHADER
#  pragma once
#  include "gpu_glsl_cpp_stubs.hh"

#  include "draw_common_shader_shared.hh"
#  include "draw_view_info.hh"

#  include "overlay_shader_shared.h"
#endif

#include "overlay_common_info.hh"

/* We use the normalized local position to avoid precision loss during interpolation. */
GPU_SHADER_INTERFACE_INFO(overlay_grid_iface)
SMOOTH(float3, local_pos)
GPU_SHADER_INTERFACE_END()

GPU_SHADER_CREATE_INFO(overlay_grid_next)
DO_STATIC_COMPILATION()
TYPEDEF_SOURCE("overlay_shader_shared.h")
VERTEX_IN(0, float3, pos)
VERTEX_OUT(overlay_grid_iface)
FRAGMENT_OUT(0, float4, out_color)
SAMPLER(0, DEPTH_2D, depth_tx)
SAMPLER(1, DEPTH_2D, depth_infront_tx)
UNIFORM_BUF(3, OVERLAY_GridData, grid_buf)
PUSH_CONSTANT(float3, plane_axes)
PUSH_CONSTANT(int, grid_flag)
VERTEX_SOURCE("overlay_grid_vert.glsl")
FRAGMENT_SOURCE("overlay_grid_frag.glsl")
ADDITIONAL_INFO(draw_view)
ADDITIONAL_INFO(draw_globals)
GPU_SHADER_CREATE_END()

GPU_SHADER_CREATE_INFO(overlay_grid_background)
DO_STATIC_COMPILATION()
VERTEX_IN(0, float3, pos)
SAMPLER(0, DEPTH_2D, depthBuffer)
PUSH_CONSTANT(float4, ucolor)
FRAGMENT_OUT(0, float4, fragColor)
VERTEX_SOURCE("overlay_edit_uv_tiled_image_borders_vert.glsl")
FRAGMENT_SOURCE("overlay_grid_background_frag.glsl")
ADDITIONAL_INFO(draw_view)
ADDITIONAL_INFO(draw_modelmat)
ADDITIONAL_INFO(draw_globals)
DEFINE_VALUE("tile_pos", "float3(0.0f)")
PUSH_CONSTANT(float3, tile_scale)
GPU_SHADER_CREATE_END()

GPU_SHADER_CREATE_INFO(overlay_grid_image)
DO_STATIC_COMPILATION()
VERTEX_IN(0, float3, pos)
PUSH_CONSTANT(float4, ucolor)
FRAGMENT_OUT(0, float4, fragColor)
VERTEX_SOURCE("overlay_edit_uv_tiled_image_borders_vert.glsl")
FRAGMENT_SOURCE("overlay_uniform_color_frag.glsl")
ADDITIONAL_INFO(draw_view)
ADDITIONAL_INFO(draw_modelmat)
ADDITIONAL_INFO(draw_globals)
STORAGE_BUF(0, READ, float3, tile_pos_buf[])
DEFINE_VALUE("tile_pos", "tile_pos_buf[gl_InstanceID]")
DEFINE_VALUE("tile_scale", "float3(1.0f)");
GPU_SHADER_CREATE_END()

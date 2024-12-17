/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#include "gpu_shader_create_info.hh"

/* We use the normalized local position to avoid precision loss during interpolation. */
GPU_SHADER_INTERFACE_INFO(overlay_grid_iface)
SMOOTH(VEC3, local_pos)
GPU_SHADER_INTERFACE_END()

GPU_SHADER_CREATE_INFO(overlay_grid_next)
DO_STATIC_COMPILATION()
TYPEDEF_SOURCE("overlay_shader_shared.h")
VERTEX_IN(0, VEC3, pos)
VERTEX_OUT(overlay_grid_iface)
FRAGMENT_OUT(0, VEC4, out_color)
SAMPLER(0, DEPTH_2D, depth_tx)
SAMPLER(1, DEPTH_2D, depth_infront_tx)
UNIFORM_BUF(3, OVERLAY_GridData, grid_buf)
PUSH_CONSTANT(VEC3, plane_axes)
PUSH_CONSTANT(INT, grid_flag)
VERTEX_SOURCE("overlay_grid_vert.glsl")
FRAGMENT_SOURCE("overlay_grid_frag.glsl")
ADDITIONAL_INFO(draw_view)
ADDITIONAL_INFO(draw_globals)
GPU_SHADER_CREATE_END()

GPU_SHADER_CREATE_INFO(overlay_grid_background)
DO_STATIC_COMPILATION()
VERTEX_IN(0, VEC3, pos)
SAMPLER(0, DEPTH_2D, depthBuffer)
PUSH_CONSTANT(VEC4, ucolor)
FRAGMENT_OUT(0, VEC4, fragColor)
VERTEX_SOURCE("overlay_edit_uv_tiled_image_borders_vert.glsl")
FRAGMENT_SOURCE("overlay_grid_background_frag.glsl")
ADDITIONAL_INFO(draw_view)
ADDITIONAL_INFO(draw_modelmat_new)
ADDITIONAL_INFO(draw_resource_handle_new)
ADDITIONAL_INFO(draw_globals)
DEFINE_VALUE("tile_pos", "vec3(0.0)")
PUSH_CONSTANT(VEC3, tile_scale)
GPU_SHADER_CREATE_END()

GPU_SHADER_CREATE_INFO(overlay_grid_image)
DO_STATIC_COMPILATION()
VERTEX_IN(0, VEC3, pos)
PUSH_CONSTANT(VEC4, ucolor)
FRAGMENT_OUT(0, VEC4, fragColor)
VERTEX_SOURCE("overlay_edit_uv_tiled_image_borders_vert.glsl")
FRAGMENT_SOURCE("overlay_uniform_color_frag.glsl")
ADDITIONAL_INFO(draw_view)
ADDITIONAL_INFO(draw_modelmat_new)
ADDITIONAL_INFO(draw_resource_handle_new)
ADDITIONAL_INFO(draw_globals)
STORAGE_BUF(0, READ, vec3, tile_pos_buf[])
DEFINE_VALUE("tile_pos", "tile_pos_buf[gl_InstanceID]")
DEFINE_VALUE("tile_scale", "vec3(1.0)");
GPU_SHADER_CREATE_END()

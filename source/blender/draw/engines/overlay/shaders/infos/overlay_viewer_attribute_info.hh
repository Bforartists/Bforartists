/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#ifdef GPU_SHADER
#  pragma once
#  include "gpu_glsl_cpp_stubs.hh"

#  include "draw_common_shader_shared.hh"
#  include "draw_object_infos_info.hh"
#  include "draw_view_info.hh"
#  include "overlay_common_info.hh"

#  define HAIR_SHADER
#  define DRW_HAIR_INFO

#  define POINTCLOUD_SHADER
#  define DRW_POINTCLOUD_INFO
#endif

#include "overlay_common_info.hh"

GPU_SHADER_INTERFACE_INFO(overlay_viewer_attribute_iface)
SMOOTH(VEC4, finalColor)
GPU_SHADER_INTERFACE_END()

GPU_SHADER_CREATE_INFO(overlay_viewer_attribute_common)
PUSH_CONSTANT(FLOAT, opacity)
GPU_SHADER_CREATE_END()

GPU_SHADER_CREATE_INFO(overlay_viewer_attribute_mesh)
DO_STATIC_COMPILATION()
VERTEX_SOURCE("overlay_viewer_attribute_mesh_vert.glsl")
FRAGMENT_SOURCE("overlay_viewer_attribute_frag.glsl")
FRAGMENT_OUT(0, VEC4, out_color)
FRAGMENT_OUT(1, VEC4, lineOutput)
VERTEX_IN(0, VEC3, pos)
VERTEX_IN(1, VEC4, attribute_value)
VERTEX_OUT(overlay_viewer_attribute_iface)
ADDITIONAL_INFO(overlay_viewer_attribute_common)
ADDITIONAL_INFO(draw_view)
ADDITIONAL_INFO(draw_modelmat)
ADDITIONAL_INFO(draw_globals)
GPU_SHADER_CREATE_END()

OVERLAY_INFO_CLIP_VARIATION(overlay_viewer_attribute_mesh)

GPU_SHADER_CREATE_INFO(overlay_viewer_attribute_pointcloud)
DO_STATIC_COMPILATION()
VERTEX_SOURCE("overlay_viewer_attribute_pointcloud_vert.glsl")
FRAGMENT_SOURCE("overlay_viewer_attribute_frag.glsl")
FRAGMENT_OUT(0, VEC4, out_color)
FRAGMENT_OUT(1, VEC4, lineOutput)
SAMPLER(3, FLOAT_BUFFER, attribute_tx)
VERTEX_OUT(overlay_viewer_attribute_iface)
ADDITIONAL_INFO(overlay_viewer_attribute_common)
ADDITIONAL_INFO(draw_pointcloud)
ADDITIONAL_INFO(draw_globals)
ADDITIONAL_INFO(draw_view)
ADDITIONAL_INFO(draw_modelmat)
GPU_SHADER_CREATE_END()

OVERLAY_INFO_CLIP_VARIATION(overlay_viewer_attribute_pointcloud)

GPU_SHADER_CREATE_INFO(overlay_viewer_attribute_curve)
DO_STATIC_COMPILATION()
VERTEX_SOURCE("overlay_viewer_attribute_curve_vert.glsl")
FRAGMENT_SOURCE("overlay_viewer_attribute_frag.glsl")
FRAGMENT_OUT(0, VEC4, out_color)
FRAGMENT_OUT(1, VEC4, lineOutput)
VERTEX_IN(0, VEC3, pos)
VERTEX_IN(1, VEC4, attribute_value)
VERTEX_OUT(overlay_viewer_attribute_iface)
ADDITIONAL_INFO(overlay_viewer_attribute_common)
ADDITIONAL_INFO(draw_view)
ADDITIONAL_INFO(draw_globals)
ADDITIONAL_INFO(draw_modelmat)
GPU_SHADER_CREATE_END()

OVERLAY_INFO_CLIP_VARIATION(overlay_viewer_attribute_curve)

GPU_SHADER_CREATE_INFO(overlay_viewer_attribute_curves)
DO_STATIC_COMPILATION()
VERTEX_SOURCE("overlay_viewer_attribute_curves_vert.glsl")
FRAGMENT_SOURCE("overlay_viewer_attribute_frag.glsl")
FRAGMENT_OUT(0, VEC4, out_color)
FRAGMENT_OUT(1, VEC4, lineOutput)
SAMPLER(1, FLOAT_BUFFER, color_tx)
PUSH_CONSTANT(BOOL, is_point_domain)
VERTEX_OUT(overlay_viewer_attribute_iface)
ADDITIONAL_INFO(overlay_viewer_attribute_common)
ADDITIONAL_INFO(draw_hair)
ADDITIONAL_INFO(draw_view)
ADDITIONAL_INFO(draw_globals)
ADDITIONAL_INFO(draw_modelmat)
GPU_SHADER_CREATE_END()

OVERLAY_INFO_CLIP_VARIATION(overlay_viewer_attribute_curves)

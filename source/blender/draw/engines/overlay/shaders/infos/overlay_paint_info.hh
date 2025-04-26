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

/* -------------------------------------------------------------------- */
/** \name OVERLAY_shader_paint_face.
 *
 * Used for face selection mode in Weight, Vertex and Texture Paint.
 * \{ */

GPU_SHADER_CREATE_INFO(overlay_paint_face)
DO_STATIC_COMPILATION()
VERTEX_IN(0, float3, pos)
VERTEX_IN(1, float4, nor) /* Select flag on the 4th component. */
PUSH_CONSTANT(float4, ucolor)
FRAGMENT_OUT(0, float4, fragColor)
VERTEX_SOURCE("overlay_paint_face_vert.glsl")
FRAGMENT_SOURCE("overlay_uniform_color_frag.glsl")
ADDITIONAL_INFO(draw_view)
ADDITIONAL_INFO(draw_modelmat)
ADDITIONAL_INFO(draw_globals)
GPU_SHADER_CREATE_END()

OVERLAY_INFO_CLIP_VARIATION(overlay_paint_face)

/** \} */

/* -------------------------------------------------------------------- */
/** \name OVERLAY_shader_paint_point.
 *
 * Used for vertex selection mode in Weight and Vertex Paint.
 * \{ */

GPU_SHADER_INTERFACE_INFO(overlay_overlay_paint_point_iface)
SMOOTH(float4, finalColor)
GPU_SHADER_INTERFACE_END()

GPU_SHADER_CREATE_INFO(overlay_paint_point)
DO_STATIC_COMPILATION()
VERTEX_IN(0, float3, pos)
VERTEX_IN(1, float4, nor) /* Select flag on the 4th component. */
VERTEX_OUT(overlay_overlay_paint_point_iface)
FRAGMENT_OUT(0, float4, fragColor)
VERTEX_SOURCE("overlay_paint_point_vert.glsl")
FRAGMENT_SOURCE("overlay_point_varying_color_frag.glsl")
ADDITIONAL_INFO(draw_view)
ADDITIONAL_INFO(draw_modelmat)
ADDITIONAL_INFO(draw_globals)
GPU_SHADER_CREATE_END()

OVERLAY_INFO_CLIP_VARIATION(overlay_paint_point)

/** \} */

/* -------------------------------------------------------------------- */
/** \name OVERLAY_shader_paint_texture.
 *
 * Used in Texture Paint mode for the Stencil Image Masking.
 * \{ */

GPU_SHADER_INTERFACE_INFO(overlay_paint_texture_iface)
SMOOTH(float2, uv_interp)
GPU_SHADER_INTERFACE_END()

GPU_SHADER_CREATE_INFO(overlay_paint_texture)
DO_STATIC_COMPILATION()
VERTEX_IN(0, float3, pos)
VERTEX_IN(1, float2, mu) /* Masking uv map. */
VERTEX_OUT(overlay_paint_texture_iface)
SAMPLER(0, FLOAT_2D, maskImage)
PUSH_CONSTANT(float3, maskColor)
PUSH_CONSTANT(float, opacity) /* `1.0f` by default. */
PUSH_CONSTANT(bool, maskInvertStencil)
PUSH_CONSTANT(bool, maskImagePremultiplied)
FRAGMENT_OUT(0, float4, fragColor)
VERTEX_SOURCE("overlay_paint_texture_vert.glsl")
FRAGMENT_SOURCE("overlay_paint_texture_frag.glsl")
ADDITIONAL_INFO(draw_view)
ADDITIONAL_INFO(draw_modelmat)
ADDITIONAL_INFO(draw_globals)
GPU_SHADER_CREATE_END()

OVERLAY_INFO_CLIP_VARIATION(overlay_paint_texture)

/** \} */

/* -------------------------------------------------------------------- */
/** \name OVERLAY_shader_paint_weight.
 *
 * Used to display Vertex Weights.
 * `overlay paint weight` is for wireframe display mode.
 * \{ */

GPU_SHADER_INTERFACE_INFO(overlay_paint_weight_iface)
SMOOTH(float2, weight_interp) /* (weight, alert) */
SMOOTH(float, color_fac)
GPU_SHADER_INTERFACE_END()

GPU_SHADER_CREATE_INFO(overlay_paint_weight)
DO_STATIC_COMPILATION()
VERTEX_IN(0, float, weight)
VERTEX_IN(1, float3, pos)
VERTEX_IN(2, float3, nor)
VERTEX_OUT(overlay_paint_weight_iface)
SAMPLER(0, FLOAT_1D, colorramp)
PUSH_CONSTANT(float, opacity)     /* `1.0f` by default. */
PUSH_CONSTANT(bool, drawContours) /* `false` by default. */
FRAGMENT_OUT(0, float4, fragColor)
FRAGMENT_OUT(1, float4, lineOutput)
VERTEX_SOURCE("overlay_paint_weight_vert.glsl")
FRAGMENT_SOURCE("overlay_paint_weight_frag.glsl")
ADDITIONAL_INFO(draw_view)
ADDITIONAL_INFO(draw_modelmat)
ADDITIONAL_INFO(draw_globals)
GPU_SHADER_CREATE_END()

OVERLAY_INFO_CLIP_VARIATION(overlay_paint_weight)

GPU_SHADER_CREATE_INFO(overlay_paint_weight_fake_shading)
DO_STATIC_COMPILATION()
ADDITIONAL_INFO(overlay_paint_weight)
DEFINE("FAKE_SHADING")
PUSH_CONSTANT(float3, light_dir)
GPU_SHADER_CREATE_END()

OVERLAY_INFO_CLIP_VARIATION(overlay_paint_weight_fake_shading)

/** \} */

/* -------------------------------------------------------------------- */
/** \name OVERLAY_shader_paint_wire.
 *
 * Used in face selection mode to display edges of selected faces in Weight, Vertex and Texture
 * paint modes.
 * \{ */

GPU_SHADER_INTERFACE_INFO(overlay_paint_wire_iface)
FLAT(float4, finalColor)
GPU_SHADER_INTERFACE_END()

GPU_SHADER_CREATE_INFO(overlay_paint_wire)
DO_STATIC_COMPILATION()
VERTEX_IN(0, float3, pos)
VERTEX_IN(1, float4, nor) /* flag stored in w */
VERTEX_OUT(overlay_paint_wire_iface)
PUSH_CONSTANT(bool, useSelect)
FRAGMENT_OUT(0, float4, fragColor)
VERTEX_SOURCE("overlay_paint_wire_vert.glsl")
FRAGMENT_SOURCE("overlay_varying_color.glsl")
ADDITIONAL_INFO(draw_view)
ADDITIONAL_INFO(draw_modelmat)
ADDITIONAL_INFO(draw_globals)
GPU_SHADER_CREATE_END()

OVERLAY_INFO_CLIP_VARIATION(overlay_paint_wire)

/** \} */

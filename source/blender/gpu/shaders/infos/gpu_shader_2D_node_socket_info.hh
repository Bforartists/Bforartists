/* SPDX-FileCopyrightText: 2022 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup gpu
 */

#ifdef GPU_SHADER
#  pragma once
#  include "gpu_glsl_cpp_stubs.hh"

#  define widgetID 0
#endif

#include "gpu_shader_create_info.hh"

GPU_SHADER_INTERFACE_INFO(gpu_node_socket_iface)
FLAT(VEC4, finalColor)
FLAT(VEC4, finalOutlineColor)
FLAT(FLOAT, finalDotRadius)
FLAT(FLOAT, finalOutlineThickness)
FLAT(FLOAT, AAsize)
FLAT(VEC2, extrusion)
FLAT(INT, finalShape)
SMOOTH(VEC2, uv)
GPU_SHADER_INTERFACE_END()

/* TODO(lone_noel): Share with C code. */
#define MAX_SOCKET_PARAMETERS 4
#define MAX_SOCKET_INSTANCE 32

GPU_SHADER_CREATE_INFO(gpu_shader_2D_node_socket_shared)
DEFINE_VALUE("MAX_SOCKET_PARAMETERS", STRINGIFY(MAX_SOCKET_PARAMETERS))
PUSH_CONSTANT(MAT4, ModelViewProjectionMatrix)
VERTEX_OUT(gpu_node_socket_iface)
FRAGMENT_OUT(0, VEC4, fragColor)
VERTEX_SOURCE("gpu_shader_2D_node_socket_vert.glsl")
FRAGMENT_SOURCE("gpu_shader_2D_node_socket_frag.glsl")
GPU_SHADER_CREATE_END()

GPU_SHADER_CREATE_INFO(gpu_shader_2D_node_socket)
DO_STATIC_COMPILATION()
/* gl_InstanceID is supposed to be 0 if not drawing instances, but this seems
 * to be violated in some drivers. For example, macOS 10.15.4 and Intel Iris
 * causes #78307 when using gl_InstanceID outside of instance. */
DEFINE_VALUE("widgetID", "0")
PUSH_CONSTANT_ARRAY(VEC4, parameters, MAX_SOCKET_PARAMETERS)
ADDITIONAL_INFO(gpu_shader_2D_node_socket_shared)
GPU_SHADER_CREATE_END()

GPU_SHADER_CREATE_INFO(gpu_shader_2D_node_socket_inst)
DO_STATIC_COMPILATION()
DEFINE_VALUE("widgetID", "gl_InstanceID")
PUSH_CONSTANT_ARRAY(VEC4, parameters, (MAX_SOCKET_PARAMETERS * MAX_SOCKET_INSTANCE))
ADDITIONAL_INFO(gpu_shader_2D_node_socket_shared)
GPU_SHADER_CREATE_END()

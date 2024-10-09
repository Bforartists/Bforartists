/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#include "gpu_shader_create_info.hh"

GPU_SHADER_CREATE_INFO(compositor_read_input_shared)
LOCAL_GROUP_SIZE(16, 16)
PUSH_CONSTANT(IVEC2, lower_bound)
SAMPLER(0, FLOAT_2D, input_tx)
COMPUTE_SOURCE("compositor_read_input.glsl")
GPU_SHADER_CREATE_END()

GPU_SHADER_CREATE_INFO(compositor_read_input_float)
ADDITIONAL_INFO(compositor_read_input_shared)
IMAGE(0, GPU_R16F, WRITE, FLOAT_2D, output_img)
DEFINE_VALUE("READ_EXPRESSION(input_color)", "vec4(input_color.r, vec3(0.0))")
DO_STATIC_COMPILATION()
GPU_SHADER_CREATE_END()

GPU_SHADER_CREATE_INFO(compositor_read_input_vector)
ADDITIONAL_INFO(compositor_read_input_shared)
IMAGE(0, GPU_RGBA16F, WRITE, FLOAT_2D, output_img)
DEFINE_VALUE("READ_EXPRESSION(input_color)", "input_color")
DO_STATIC_COMPILATION()
GPU_SHADER_CREATE_END()

GPU_SHADER_CREATE_INFO(compositor_read_input_color)
ADDITIONAL_INFO(compositor_read_input_shared)
IMAGE(0, GPU_RGBA16F, WRITE, FLOAT_2D, output_img)
DEFINE_VALUE("READ_EXPRESSION(input_color)", "input_color")
DO_STATIC_COMPILATION()
GPU_SHADER_CREATE_END()

GPU_SHADER_CREATE_INFO(compositor_read_input_alpha)
ADDITIONAL_INFO(compositor_read_input_shared)
IMAGE(0, GPU_R16F, WRITE, FLOAT_2D, output_img)
DEFINE_VALUE("READ_EXPRESSION(input_color)", "vec4(input_color.a, vec3(0.0))")
DO_STATIC_COMPILATION()
GPU_SHADER_CREATE_END()

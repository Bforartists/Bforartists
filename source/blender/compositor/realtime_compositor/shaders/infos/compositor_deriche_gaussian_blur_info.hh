/* SPDX-FileCopyrightText: 2024 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#include "gpu_shader_create_info.hh"

GPU_SHADER_CREATE_INFO(compositor_deriche_gaussian_blur)
LOCAL_GROUP_SIZE(128, 2)
PUSH_CONSTANT(VEC4, causal_feedforward_coefficients)
PUSH_CONSTANT(VEC4, non_causal_feedforward_coefficients)
PUSH_CONSTANT(VEC4, feedback_coefficients)
PUSH_CONSTANT(FLOAT, causal_boundary_coefficient)
PUSH_CONSTANT(FLOAT, non_causal_boundary_coefficient)
SAMPLER(0, FLOAT_2D, input_tx)
IMAGE(0, GPU_RGBA16F, WRITE, FLOAT_2D, causal_output_img)
IMAGE(1, GPU_RGBA16F, WRITE, FLOAT_2D, non_causal_output_img)
COMPUTE_SOURCE("compositor_deriche_gaussian_blur.glsl")
DO_STATIC_COMPILATION()
GPU_SHADER_CREATE_END()

GPU_SHADER_CREATE_INFO(compositor_deriche_gaussian_blur_sum)
LOCAL_GROUP_SIZE(16, 16)
SAMPLER(0, FLOAT_2D, causal_input_tx)
SAMPLER(1, FLOAT_2D, non_causal_input_tx)
IMAGE(0, GPU_RGBA16F, WRITE, FLOAT_2D, output_img)
COMPUTE_SOURCE("compositor_deriche_gaussian_blur_sum.glsl")
DO_STATIC_COMPILATION()
GPU_SHADER_CREATE_END()

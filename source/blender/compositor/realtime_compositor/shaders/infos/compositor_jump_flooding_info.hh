/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#include "gpu_shader_create_info.hh"

GPU_SHADER_CREATE_INFO(compositor_jump_flooding)
LOCAL_GROUP_SIZE(16, 16)
PUSH_CONSTANT(INT, step_size)
SAMPLER(0, INT_2D, input_tx)
IMAGE(0, GPU_RG16I, WRITE, INT_2D, output_img)
COMPUTE_SOURCE("compositor_jump_flooding.glsl")
DO_STATIC_COMPILATION()
GPU_SHADER_CREATE_END()

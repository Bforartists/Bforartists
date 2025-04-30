/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#include "gpu_shader_create_info.hh"

GPU_SHADER_CREATE_INFO(compositor_compute_preview)
LOCAL_GROUP_SIZE(16, 16)
SAMPLER(0, sampler2D, input_tx)
IMAGE(0, GPU_RGBA16F, write, image2D, preview_img)
COMPUTE_SOURCE("compositor_compute_preview.glsl")
DO_STATIC_COMPILATION()
GPU_SHADER_CREATE_END()

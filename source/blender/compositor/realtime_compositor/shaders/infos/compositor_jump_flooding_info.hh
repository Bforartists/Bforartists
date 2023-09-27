/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#include "gpu_shader_create_info.hh"

GPU_SHADER_CREATE_INFO(compositor_jump_flooding)
    .local_group_size(16, 16)
    .push_constant(Type::INT, "step_size")
    .sampler(0, ImageType::INT_2D, "input_tx")
    .image(0, GPU_RG16I, Qualifier::WRITE, ImageType::INT_2D, "output_img")
    .compute_source("compositor_jump_flooding.glsl")
    .do_static_compilation(true);

/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#include "gpu_shader_create_info.hh"

GPU_SHADER_CREATE_INFO(compositor_normalize)
    .local_group_size(16, 16)
    .push_constant(Type::FLOAT, "minimum")
    .push_constant(Type::FLOAT, "scale")
    .sampler(0, ImageType::FLOAT_2D, "input_tx")
    .image(0, GPU_R16F, Qualifier::WRITE, ImageType::FLOAT_2D, "output_img")
    .compute_source("compositor_normalize.glsl")
    .do_static_compilation(true);

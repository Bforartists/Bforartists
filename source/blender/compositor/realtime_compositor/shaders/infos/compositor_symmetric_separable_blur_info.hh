/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#include "gpu_shader_create_info.hh"

GPU_SHADER_CREATE_INFO(compositor_symmetric_separable_blur_shared)
    .local_group_size(16, 16)
    .push_constant(Type::BOOL, "extend_bounds")
    .push_constant(Type::BOOL, "gamma_correct_input")
    .push_constant(Type::BOOL, "gamma_uncorrect_output")
    .sampler(0, ImageType::FLOAT_2D, "input_tx")
    .sampler(1, ImageType::FLOAT_1D, "weights_tx")
    .compute_source("compositor_symmetric_separable_blur.glsl");

GPU_SHADER_CREATE_INFO(compositor_symmetric_separable_blur_float)
    .additional_info("compositor_symmetric_separable_blur_shared")
    .image(0, GPU_R16F, Qualifier::WRITE, ImageType::FLOAT_2D, "output_img")
    .do_static_compilation(true);

GPU_SHADER_CREATE_INFO(compositor_symmetric_separable_blur_color)
    .additional_info("compositor_symmetric_separable_blur_shared")
    .image(0, GPU_RGBA16F, Qualifier::WRITE, ImageType::FLOAT_2D, "output_img")
    .do_static_compilation(true);

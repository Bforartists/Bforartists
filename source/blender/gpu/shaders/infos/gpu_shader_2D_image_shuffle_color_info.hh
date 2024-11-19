/* SPDX-FileCopyrightText: 2022 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup gpu
 */

#ifdef GPU_SHADER
#  pragma once
#  include "gpu_glsl_cpp_stubs.hh"

#  include "GPU_shader_shared.hh"
#  include "gpu_shader_2D_image_info.hh"
#endif

#include "gpu_shader_create_info.hh"

GPU_SHADER_CREATE_INFO(gpu_shader_2D_image_shuffle_color)
ADDITIONAL_INFO(gpu_shader_2D_image_common)
PUSH_CONSTANT(VEC4, color)
PUSH_CONSTANT(VEC4, shuffle)
FRAGMENT_SOURCE("gpu_shader_image_shuffle_color_frag.glsl")
DO_STATIC_COMPILATION()
GPU_SHADER_CREATE_END()

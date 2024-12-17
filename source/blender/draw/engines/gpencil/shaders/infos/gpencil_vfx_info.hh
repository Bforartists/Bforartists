/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#ifdef GPU_SHADER
#  pragma once

#  include "gpu_glsl_cpp_stubs.hh"

#  include "gpencil_shader_shared.h"

#  include "draw_fullscreen_info.hh"
#  include "draw_view_info.hh"

#  define COMPOSITE
#endif

#include "gpu_shader_create_info.hh"

GPU_SHADER_CREATE_INFO(gpencil_fx_common)
SAMPLER(0, FLOAT_2D, colorBuf)
SAMPLER(1, FLOAT_2D, revealBuf)
/* Reminder: This is considered SRC color in blend equations.
 * Same operation on all buffers. */
FRAGMENT_OUT(0, VEC4, fragColor)
FRAGMENT_OUT(1, VEC4, fragRevealage)
FRAGMENT_SOURCE("gpencil_vfx_frag.glsl")
GPU_SHADER_CREATE_END()

GPU_SHADER_CREATE_INFO(gpencil_fx_composite)
DO_STATIC_COMPILATION()
DEFINE("COMPOSITE")
PUSH_CONSTANT(BOOL, isFirstPass)
ADDITIONAL_INFO(gpencil_fx_common)
ADDITIONAL_INFO(draw_fullscreen)
GPU_SHADER_CREATE_END()

GPU_SHADER_CREATE_INFO(gpencil_fx_colorize)
DO_STATIC_COMPILATION()
DEFINE("COLORIZE")
PUSH_CONSTANT(VEC3, lowColor)
PUSH_CONSTANT(VEC3, highColor)
PUSH_CONSTANT(FLOAT, factor)
PUSH_CONSTANT(INT, mode)
ADDITIONAL_INFO(gpencil_fx_common)
ADDITIONAL_INFO(draw_fullscreen)
GPU_SHADER_CREATE_END()

GPU_SHADER_CREATE_INFO(gpencil_fx_blur)
DO_STATIC_COMPILATION()
DEFINE("BLUR")
PUSH_CONSTANT(VEC2, offset)
PUSH_CONSTANT(INT, sampCount)
ADDITIONAL_INFO(gpencil_fx_common)
ADDITIONAL_INFO(draw_fullscreen)
GPU_SHADER_CREATE_END()

GPU_SHADER_CREATE_INFO(gpencil_fx_transform)
DO_STATIC_COMPILATION()
DEFINE("TRANSFORM")
PUSH_CONSTANT(VEC2, axisFlip)
PUSH_CONSTANT(VEC2, waveDir)
PUSH_CONSTANT(VEC2, waveOffset)
PUSH_CONSTANT(FLOAT, wavePhase)
PUSH_CONSTANT(VEC2, swirlCenter)
PUSH_CONSTANT(FLOAT, swirlAngle)
PUSH_CONSTANT(FLOAT, swirlRadius)
ADDITIONAL_INFO(gpencil_fx_common)
ADDITIONAL_INFO(draw_fullscreen)
GPU_SHADER_CREATE_END()

GPU_SHADER_CREATE_INFO(gpencil_fx_glow)
DO_STATIC_COMPILATION()
DEFINE("GLOW")
PUSH_CONSTANT(VEC4, glowColor)
PUSH_CONSTANT(VEC2, offset)
PUSH_CONSTANT(INT, sampCount)
PUSH_CONSTANT(VEC4, threshold)
PUSH_CONSTANT(BOOL, firstPass)
PUSH_CONSTANT(BOOL, glowUnder)
PUSH_CONSTANT(INT, blendMode)
ADDITIONAL_INFO(gpencil_fx_common)
ADDITIONAL_INFO(draw_fullscreen)
GPU_SHADER_CREATE_END()

GPU_SHADER_CREATE_INFO(gpencil_fx_rim)
DO_STATIC_COMPILATION()
DEFINE("RIM")
PUSH_CONSTANT(VEC2, blurDir)
PUSH_CONSTANT(VEC2, uvOffset)
PUSH_CONSTANT(VEC3, rimColor)
PUSH_CONSTANT(VEC3, maskColor)
PUSH_CONSTANT(INT, sampCount)
PUSH_CONSTANT(INT, blendMode)
PUSH_CONSTANT(BOOL, isFirstPass)
ADDITIONAL_INFO(gpencil_fx_common)
ADDITIONAL_INFO(draw_fullscreen)
GPU_SHADER_CREATE_END()

GPU_SHADER_CREATE_INFO(gpencil_fx_shadow)
DO_STATIC_COMPILATION()
DEFINE("SHADOW")
PUSH_CONSTANT(VEC4, shadowColor)
PUSH_CONSTANT(VEC2, uvRotX)
PUSH_CONSTANT(VEC2, uvRotY)
PUSH_CONSTANT(VEC2, uvOffset)
PUSH_CONSTANT(VEC2, blurDir)
PUSH_CONSTANT(VEC2, waveDir)
PUSH_CONSTANT(VEC2, waveOffset)
PUSH_CONSTANT(FLOAT, wavePhase)
PUSH_CONSTANT(INT, sampCount)
PUSH_CONSTANT(BOOL, isFirstPass)
ADDITIONAL_INFO(gpencil_fx_common)
ADDITIONAL_INFO(draw_fullscreen)
GPU_SHADER_CREATE_END()

GPU_SHADER_CREATE_INFO(gpencil_fx_pixelize)
DO_STATIC_COMPILATION()
DEFINE("PIXELIZE")
PUSH_CONSTANT(VEC2, targetPixelSize)
PUSH_CONSTANT(VEC2, targetPixelOffset)
PUSH_CONSTANT(VEC2, accumOffset)
PUSH_CONSTANT(INT, sampCount)
ADDITIONAL_INFO(gpencil_fx_common)
ADDITIONAL_INFO(draw_fullscreen)
GPU_SHADER_CREATE_END()

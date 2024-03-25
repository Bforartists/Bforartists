/* SPDX-FileCopyrightText: 2022 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup gpu
 *
 * Glue definition to make shared declaration of struct & functions work in both C / C++ and GLSL.
 * We use the same vector and matrix types as Blender C++. Some math functions are defined to use
 * the float version to match the GLSL syntax.
 * This file can be used for C & C++ code and the syntax used should follow the same rules.
 * Some preprocessing is done by the GPU back-end to make it GLSL compatible.
 *
 * IMPORTANT:
 * - Always use `u` suffix for enum values. GLSL do not support implicit cast.
 * - Define all values. This is in order to simplify custom pre-processor code.
 * - (C++ only) Always use `uint32_t` as underlying type (`enum eMyEnum : uint32_t`).
 * - (C only) do NOT use the enum type inside UBO/SSBO structs and use `uint` instead.
 * - Use float suffix by default for float literals to avoid double promotion in C++.
 * - Pack one float or int after a vec3/ivec3 to fulfill alignment rules.
 *
 * NOTE: Due to alignment restriction and buggy drivers, do not try to use mat3 inside structs.
 * NOTE: (UBO only) Do not use arrays of float. They are padded to arrays of vec4 and are not worth
 * it. This does not apply to SSBO.
 *
 * IMPORTANT: Do not forget to align mat4, vec3 and vec4 to 16 bytes, and vec2 to 8 bytes.
 *
 * NOTE: You can use bool type using bool32_t a int boolean type matching the GLSL type.
 */

#ifdef GPU_SHADER
/* Silence macros when compiling for shaders. */
#  define BLI_STATIC_ASSERT(cond, msg)
#  define BLI_STATIC_ASSERT_ALIGN(type_, align_)
#  define BLI_STATIC_ASSERT_SIZE(type_, size_)
#  define ENUM_OPERATORS(a, b)
/* Incompatible keywords. */
#  define static
#  define inline
/* Math function renaming. */
#  define cosf cos
#  define sinf sin
#  define tanf tan
#  define acosf acos
#  define asinf asin
#  define atanf atan
#  define floorf floor
#  define ceilf ceil
#  define sqrtf sqrt
#  define expf exp

#else /* C / C++ */
#  pragma once

#  include "BLI_assert.h"

#  include "BLI_math_matrix_types.hh"
#  include "BLI_math_vector_types.hh"

using bool32_t = int32_t;
// using bool2 = blender::int2; /* Size is not consistent across backend. */
// using bool3 = blender::int3; /* Size is not consistent across backend. */
// using bool4 = blender::int4; /* Size is not consistent across backend. */

using blender::float2;
using blender::float4;
using blender::int2;
using blender::int4;
using blender::uint2;
using blender::uint4;
/** IMPORTANT: Do not use in shared struct. Use packed_(float/int/uint)3 instead.
 * Here for static functions usage only. */
using blender::float3;
using blender::int3;
using blender::uint3;
/** Packed types are needed for MSL which have different alignment rules for float3. */
using packed_float3 = blender::float3;
using packed_int3 = blender::int3;
using packed_uint3 = blender::uint3;

using blender::float2x2;
// using blender::float3x2; /* Does not follow alignment rules of GPU. */
using blender::float4x2;
// using blender::float2x3; /* Does not follow alignment rules of GPU. */
// using blender::float3x3; /* Does not follow alignment rules of GPU. */
// using blender::float4x3; /* Does not follow alignment rules of GPU. */
using blender::float2x4;
using blender::float3x4;
using blender::float4x4;

#endif

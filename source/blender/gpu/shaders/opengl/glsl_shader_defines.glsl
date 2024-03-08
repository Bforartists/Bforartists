/* SPDX-FileCopyrightText: 2022-2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** Type aliases. */
/** IMPORTANT: Be warry of size and alignment matching for types that are present
 * in C++ shared code. */

/* Boolean in GLSL are 32bit in interface structs. */
#define bool32_t bool
#define bool2 bvec2
#define bool3 bvec3
#define bool4 bvec4

#define float2 vec2
#define float3 vec3
#define float4 vec4
#define int2 ivec2
#define int3 ivec3
#define int4 ivec4
#define uint2 uvec2
#define uint3 uvec3
#define uint4 uvec4
/* GLSL already follows the packed alignement / size rules for vec3. */
#define packed_float3 float3
#define packed_int3 int3
#define packed_uint3 uint3

#define float2x2 mat2x2
#define float3x2 mat3x2
#define float4x2 mat4x2
#define float2x3 mat2x3
#define float3x3 mat3x3
#define float4x3 mat4x3
#define float2x4 mat2x4
#define float3x4 mat3x4
#define float4x4 mat4x4

/* Fast store variant macro. In GLSL this is the same as imageStore, but assumes no bounds
 * checking. */
#define imageStoreFast imageStore
#define imageLoadFast imageLoad

/* Texture format tokens -- Type explicitness required by other Graphics APIs. */
#define depth2D sampler2D
#define depth2DArray sampler2DArray
#define depth2DMS sampler2DMS
#define depth2DMSArray sampler2DMSArray
#define depthCube samplerCube
#define depthCubeArray samplerCubeArray
#define depth2DArrayShadow sampler2DArrayShadow

#define usampler2DArrayAtomic usampler2DArray
#define usampler2DAtomic usampler2D
#define usampler3DAtomic usampler3D
#define isampler2DArrayAtomic isampler2DArray
#define isampler2DAtomic isampler2D
#define isampler3DAtomic isampler3D

/* Backend Functions. */
#define select(A, B, mask) mix(A, B, mask)

bool is_zero(vec2 A)
{
  return all(equal(A, vec2(0.0)));
}

bool is_zero(vec3 A)
{
  return all(equal(A, vec3(0.0)));
}

bool is_zero(vec4 A)
{
  return all(equal(A, vec4(0.0)));
}

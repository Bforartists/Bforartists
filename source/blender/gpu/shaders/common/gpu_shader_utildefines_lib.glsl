/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/* WORKAROUND: to guard against double include in EEVEE. */
#ifndef GPU_SHADER_UTILDEFINES_GLSL
#define GPU_SHADER_UTILDEFINES_GLSL

#ifndef FLT_MAX
#  define FLT_MAX uintBitsToFloat(0x7F7FFFFFu)
#  define FLT_MIN uintBitsToFloat(0x00800000u)
#  define FLT_EPSILON 1.192092896e-07F
#  define SHRT_MAX 0x00007FFF
#  define INT_MAX 0x7FFFFFFF
#  define USHRT_MAX 0x0000FFFFu
#  define UINT_MAX 0xFFFFFFFFu
#endif
#define NAN_FLT uintBitsToFloat(0x7FC00000u)
#define FLT_11_MAX uintBitsToFloat(0x477E0000)
#define FLT_10_MAX uintBitsToFloat(0x477C0000)
#define FLT_11_11_10_MAX vec3(FLT_11_MAX, FLT_11_MAX, FLT_10_MAX)

#define UNPACK2(a) (a)[0], (a)[1]
#define UNPACK3(a) (a)[0], (a)[1], (a)[2]
#define UNPACK4(a) (a)[0], (a)[1], (a)[2], (a)[3]

/**
 * Clamp input into [0..1] range.
 */
#define saturate(a) clamp(a, 0.0, 1.0)

#define isfinite(a) (!isinf(a) && !isnan(a))

/* clang-format off */
#define in_range_inclusive(val, min_v, max_v) (all(greaterThanEqual(val, min_v)) && all(lessThanEqual(val, max_v)))
#define in_range_exclusive(val, min_v, max_v) (all(greaterThan(val, min_v)) && all(lessThan(val, max_v)))
#define in_texture_range(texel, tex) (all(greaterThanEqual(texel, ivec2(0))) && all(lessThan(texel, textureSize(tex, 0).xy)))
#define in_image_range(texel, tex) (all(greaterThanEqual(texel, ivec2(0))) && all(lessThan(texel, imageSize(tex).xy)))

#define weighted_sum(val0, val1, val2, val3, weights) ((val0 * weights[0] + val1 * weights[1] + val2 * weights[2] + val3 * weights[3]) * safe_rcp(weights[0] + weights[1] + weights[2] + weights[3]))
#define weighted_sum_array(val, weights) ((val[0] * weights[0] + val[1] * weights[1] + val[2] * weights[2] + val[3] * weights[3]) * safe_rcp(weights[0] + weights[1] + weights[2] + weights[3]))
/* clang-format on */

bool flag_test(uint flag, uint val)
{
  return (flag & val) != 0u;
}
bool flag_test(int flag, uint val)
{
  return flag_test(uint(flag), val);
}
bool flag_test(int flag, int val)
{
  return (flag & val) != 0;
}

void set_flag_from_test(inout uint value, bool test, uint flag)
{
  if (test) {
    value |= flag;
  }
  else {
    value &= ~flag;
  }
}
void set_flag_from_test(inout int value, bool test, int flag)
{
  if (test) {
    value |= flag;
  }
  else {
    value &= ~flag;
  }
}

/* Keep define to match C++ implementation. */
#define SET_FLAG_FROM_TEST(value, test, flag) set_flag_from_test(value, test, flag)

/**
 * Pack two 16-bit uint into one 32-bit uint.
 */
uint packUvec2x16(uvec2 data)
{
  data = (data & 0xFFFFu) << uvec2(0u, 16u);
  return data.x | data.y;
}
uvec2 unpackUvec2x16(uint data)
{
  return (uvec2(data) >> uvec2(0u, 16u)) & uvec2(0xFFFFu);
}

/**
 * Pack four 8-bit uint into one 32-bit uint.
 */
uint packUvec4x8(uvec4 data)
{
  data = (data & 0xFFu) << uvec4(0u, 8u, 16u, 24u);
  return data.x | data.y | data.z | data.w;
}
uvec4 unpackUvec4x8(uint data)
{
  return (uvec4(data) >> uvec4(0u, 8u, 16u, 24u)) & uvec4(0xFFu);
}

/**
 * Convert from float representation to ordered int allowing min/max atomic operation.
 * Based on: https://stackoverflow.com/a/31010352
 */
int floatBitsToOrderedInt(float value)
{
  /* Floats can be sorted using their bits interpreted as integers for positive values.
   * Negative values do not follow int's two's complement ordering which is reversed.
   * So we have to XOR all bits except the sign bits in order to reverse the ordering.
   * Note that this is highly hardware dependent, but there seems to be no case of GPU where the
   * ints ares not two's complement. */
  int int_value = floatBitsToInt(value);
  return (int_value < 0) ? (int_value ^ 0x7FFFFFFF) : int_value;
}
float orderedIntBitsToFloat(int int_value)
{
  return intBitsToFloat((int_value < 0) ? (int_value ^ 0x7FFFFFFF) : int_value);
}

/**
 * Ray offset to avoid self intersection.
 *
 * This can be used to compute a modified ray start position for rays leaving from a surface.
 * From:
 * "A Fast and Robust Method for Avoiding Self-Intersection"
 * Ray Tracing Gems, chapter 6.
 */
vec3 offset_ray(vec3 P, vec3 Ng)
{
  const float origin = 1.0 / 32.0;
  const float float_scale = 1.0 / 65536.0;
  const float int_scale = 256.0;

  ivec3 of_i = ivec3(int_scale * Ng);
  of_i = ivec3((P.x < 0.0) ? -of_i.x : of_i.x,
               (P.y < 0.0) ? -of_i.y : of_i.y,
               (P.z < 0.0) ? -of_i.z : of_i.z);
  vec3 P_i = intBitsToFloat(floatBitsToInt(P) + of_i);

  vec3 uf = P + float_scale * Ng;
  return vec3((abs(P.x) < origin) ? uf.x : P_i.x,
              (abs(P.y) < origin) ? uf.y : P_i.y,
              (abs(P.z) < origin) ? uf.z : P_i.z);
}

#endif /* GPU_SHADER_UTILDEFINES_GLSL */

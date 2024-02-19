/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#pragma BLENDER_REQUIRE(gpu_shader_math_base_lib.glsl)
#pragma BLENDER_REQUIRE(gpu_shader_math_vector_lib.glsl)

/* -------------------------------------------------------------------- */
/** \name Spherical Harmonics Functions
 *
 * `L` denote the row and `M` the column in the spherical harmonics table (1).
 * `p` denote positive column and `n` negative ones.
 *
 * Use precomputed constants to avoid constant folding differences across compilers.
 * Note that (2) doesn't use Condon-Shortley phase whereas our implementation does.
 *
 * Reference:
 * (1) https://en.wikipedia.org/wiki/Spherical_harmonics#/media/File:Sphericalfunctions.svg
 * (2) https://en.wikipedia.org/wiki/Table_of_spherical_harmonics#Real_spherical_harmonics
 * (3) https://seblagarde.wordpress.com/2012/01/08/pi-or-not-to-pi-in-game-lighting-equation/
 *
 * \{ */

/* L0 Band. */
float spherical_harmonics_L0_M0(vec3 v)
{
  return 0.282094792;
}

/* L1 Band. */
float spherical_harmonics_L1_Mn1(vec3 v)
{
  return -0.488602512 * v.y;
}
float spherical_harmonics_L1_M0(vec3 v)
{
  return 0.488602512 * v.z;
}
float spherical_harmonics_L1_Mp1(vec3 v)
{
  return -0.488602512 * v.x;
}

/* L2 Band. */
float spherical_harmonics_L2_Mn2(vec3 v)
{
  return 1.092548431 * (v.x * v.y);
}
float spherical_harmonics_L2_Mn1(vec3 v)
{
  return -1.092548431 * (v.y * v.z);
}
float spherical_harmonics_L2_M0(vec3 v)
{
  return 0.315391565 * (3.0 * v.z * v.z - 1.0);
}
float spherical_harmonics_L2_Mp1(vec3 v)
{
  return -1.092548431 * (v.x * v.z);
}
float spherical_harmonics_L2_Mp2(vec3 v)
{
  return 0.546274215 * (v.x * v.x - v.y * v.y);
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Structure
 * \{ */

struct SphericalHarmonicBandL0 {
  vec4 M0;
};

struct SphericalHarmonicBandL1 {
  vec4 Mn1;
  vec4 M0;
  vec4 Mp1;
};

struct SphericalHarmonicBandL2 {
  vec4 Mn2;
  vec4 Mn1;
  vec4 M0;
  vec4 Mp1;
  vec4 Mp2;
};

struct SphericalHarmonicL0 {
  SphericalHarmonicBandL0 L0;
};

struct SphericalHarmonicL1 {
  SphericalHarmonicBandL0 L0;
  SphericalHarmonicBandL1 L1;
};

struct SphericalHarmonicL2 {
  SphericalHarmonicBandL0 L0;
  SphericalHarmonicBandL1 L1;
  SphericalHarmonicBandL2 L2;
};

/** \} */

/* -------------------------------------------------------------------- */
/** \name Encode
 *
 * Decompose an input signal into spherical harmonic coefficients.
 * Note that `amplitude` need to be scaled by solid angle.
 * \{ */

void spherical_harmonics_L0_encode_signal_sample(vec3 direction,
                                                 vec4 amplitude,
                                                 inout SphericalHarmonicBandL0 r_L0)
{
  r_L0.M0 += spherical_harmonics_L0_M0(direction) * amplitude;
}

void spherical_harmonics_L1_encode_signal_sample(vec3 direction,
                                                 vec4 amplitude,
                                                 inout SphericalHarmonicBandL1 r_L1)
{
  r_L1.Mn1 += spherical_harmonics_L1_Mn1(direction) * amplitude;
  r_L1.M0 += spherical_harmonics_L1_M0(direction) * amplitude;
  r_L1.Mp1 += spherical_harmonics_L1_Mp1(direction) * amplitude;
}

void spherical_harmonics_L2_encode_signal_sample(vec3 direction,
                                                 vec4 amplitude,
                                                 inout SphericalHarmonicBandL2 r_L2)
{
  r_L2.Mn2 += spherical_harmonics_L2_Mn2(direction) * amplitude;
  r_L2.Mn1 += spherical_harmonics_L2_Mn1(direction) * amplitude;
  r_L2.M0 += spherical_harmonics_L2_M0(direction) * amplitude;
  r_L2.Mp1 += spherical_harmonics_L2_Mp1(direction) * amplitude;
  r_L2.Mp2 += spherical_harmonics_L2_Mp2(direction) * amplitude;
}

void spherical_harmonics_encode_signal_sample(vec3 direction,
                                              vec4 amplitude,
                                              inout SphericalHarmonicL0 sh)
{
  spherical_harmonics_L0_encode_signal_sample(direction, amplitude, sh.L0);
}

void spherical_harmonics_encode_signal_sample(vec3 direction,
                                              vec4 amplitude,
                                              inout SphericalHarmonicL1 sh)
{
  spherical_harmonics_L0_encode_signal_sample(direction, amplitude, sh.L0);
  spherical_harmonics_L1_encode_signal_sample(direction, amplitude, sh.L1);
}

void spherical_harmonics_encode_signal_sample(vec3 direction,
                                              vec4 amplitude,
                                              inout SphericalHarmonicL2 sh)
{
  spherical_harmonics_L0_encode_signal_sample(direction, amplitude, sh.L0);
  spherical_harmonics_L1_encode_signal_sample(direction, amplitude, sh.L1);
  spherical_harmonics_L2_encode_signal_sample(direction, amplitude, sh.L2);
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Decode
 *
 * Evaluate an encoded signal in a given unit vector direction.
 * \{ */

vec4 spherical_harmonics_L0_evaluate(vec3 direction, SphericalHarmonicBandL0 L0)
{
  return spherical_harmonics_L0_M0(direction) * L0.M0;
}

vec4 spherical_harmonics_L1_evaluate(vec3 direction, SphericalHarmonicBandL1 L1)
{
  return spherical_harmonics_L1_Mn1(direction) * L1.Mn1 +
         spherical_harmonics_L1_M0(direction) * L1.M0 +
         spherical_harmonics_L1_Mp1(direction) * L1.Mp1;
}

vec4 spherical_harmonics_L2_evaluate(vec3 direction, SphericalHarmonicBandL2 L2)
{
  return spherical_harmonics_L2_Mn2(direction) * L2.Mn2 +
         spherical_harmonics_L2_Mn1(direction) * L2.Mn1 +
         spherical_harmonics_L2_M0(direction) * L2.M0 +
         spherical_harmonics_L2_Mp1(direction) * L2.Mp1 +
         spherical_harmonics_L2_Mp2(direction) * L2.Mp2;
}

vec3 spherical_harmonics_evaluate(vec3 direction, SphericalHarmonicL0 sh)
{
  vec3 radiance = spherical_harmonics_L0_evaluate(direction, sh.L0).rgb;
  return max(vec3(0.0), radiance);
}

vec3 spherical_harmonics_evaluate(vec3 direction, SphericalHarmonicL1 sh)
{
  vec3 radiance = spherical_harmonics_L0_evaluate(direction, sh.L0).rgb +
                  spherical_harmonics_L1_evaluate(direction, sh.L1).rgb;
  return max(vec3(0.0), radiance);
}

vec3 spherical_harmonics_evaluate(vec3 direction, SphericalHarmonicL2 sh)
{
  vec3 radiance = spherical_harmonics_L0_evaluate(direction, sh.L0).rgb +
                  spherical_harmonics_L1_evaluate(direction, sh.L1).rgb +
                  spherical_harmonics_L2_evaluate(direction, sh.L2).rgb;
  return max(vec3(0.0), radiance);
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Rotation
 * \{ */

SphericalHarmonicBandL0 spherical_harmonics_L0_rotate(mat3x3 rotation, SphericalHarmonicBandL0 L0)
{
  /* L0 band being a constant function (i.e: there is no directionality) there is nothing to
   * rotate. This is a no-op. */
  return L0;
}

SphericalHarmonicBandL1 spherical_harmonics_L1_rotate(mat3x3 rotation, SphericalHarmonicBandL1 L1)
{
  /* Convert L1 coefficients to per channel column.
   * Note the component shuffle to match blender coordinate system. */
  mat4x3 per_channel = transpose(mat3x4(L1.Mp1, L1.Mn1, -L1.M0));
  /* Rotate each channel. */
  per_channel[0] = rotation * per_channel[0];
  per_channel[1] = rotation * per_channel[1];
  per_channel[2] = rotation * per_channel[2];
  per_channel[3] = rotation * per_channel[3];
  /* Convert back from L1 coefficients to per channel column.
   * Note the component shuffle to match blender coordinate system. */
  mat3x4 per_coef = transpose(per_channel);
  L1.Mn1 = per_coef[1];
  L1.M0 = -per_coef[2];
  L1.Mp1 = per_coef[0];
  return L1;
}

SphericalHarmonicL1 spherical_harmonics_rotate(mat3x3 rotation, SphericalHarmonicL1 sh)
{
  sh.L0 = spherical_harmonics_L0_rotate(rotation, sh.L0);
  sh.L1 = spherical_harmonics_L1_rotate(rotation, sh.L1);
  return sh;
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Evaluation
 * \{ */

/**
 * Convolve a spherical harmonic encoded irradiance signal as a lambertian reflection.
 * Returns the lambertian radiance (cosine lobe divided by PI) so the coefficients simplify to 1,
 * 2/3 and 1/4. See this reference for more explanation:
 * https://seblagarde.wordpress.com/2012/01/08/pi-or-not-to-pi-in-game-lighting-equation/
 */
vec3 spherical_harmonics_evaluate_lambert(vec3 N, SphericalHarmonicL0 sh)
{
  vec3 radiance = spherical_harmonics_L0_evaluate(N, sh.L0).rgb;
  return max(vec3(0.0), radiance);
}
vec3 spherical_harmonics_evaluate_lambert(vec3 N, SphericalHarmonicL1 sh)
{
  vec3 radiance = spherical_harmonics_L0_evaluate(N, sh.L0).rgb +
                  spherical_harmonics_L1_evaluate(N, sh.L1).rgb * (2.0 / 3.0);
  return max(vec3(0.0), radiance);
}
vec3 spherical_harmonics_evaluate_lambert(vec3 N, SphericalHarmonicL2 sh)
{
  vec3 radiance = spherical_harmonics_L0_evaluate(N, sh.L0).rgb +
                  spherical_harmonics_L1_evaluate(N, sh.L1).rgb * (2.0 / 3.0) +
                  spherical_harmonics_L2_evaluate(N, sh.L2).rgb * (1.0 / 4.0);
  return max(vec3(0.0), radiance);
}

/**
 * Use non-linear reconstruction method to avoid negative lobe artifacts.
 * See this reference for more explanation:
 * https://grahamhazel.com/blog/2017/12/22/converting-sh-radiance-to-irradiance/
 */
float spherical_harmonics_evaluate_non_linear(vec3 N, float R0, vec3 R1)
{
  /* No idea why this is needed. */
  R1 /= 2.0;

  float R1_len;
  vec3 R1_dir = normalize_and_get_length(R1, R1_len);
  float rcp_R0 = safe_rcp(R0);

  float q = (1.0 + dot(R1_dir, N)) / 2.0;
  float p = 1.0 + 2.0 * R1_len * rcp_R0;
  float a = (1.0 - R1_len * rcp_R0) * safe_rcp(1.0 + R1_len * rcp_R0);

  return R0 * (a + (1.0 - a) * (p + 1.0) * pow(q, p));
}
vec3 spherical_harmonics_evaluate_lambert_non_linear(vec3 N, SphericalHarmonicL1 sh)
{
  /* Shuffling based on spherical_harmonics_L1_* functions. */
  vec3 R1_r = vec3(-sh.L1.Mp1.r, -sh.L1.Mn1.r, sh.L1.M0.r);
  vec3 R1_g = vec3(-sh.L1.Mp1.g, -sh.L1.Mn1.g, sh.L1.M0.g);
  vec3 R1_b = vec3(-sh.L1.Mp1.b, -sh.L1.Mn1.b, sh.L1.M0.b);

  vec3 radiance = vec3(spherical_harmonics_evaluate_non_linear(N, sh.L0.M0.r, R1_r),
                       spherical_harmonics_evaluate_non_linear(N, sh.L0.M0.g, R1_g),
                       spherical_harmonics_evaluate_non_linear(N, sh.L0.M0.b, R1_b));
  /* Return lambertian radiance. So divide by PI. */
  return radiance / M_PI;
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Load/Store
 *
 * This section define the compression scheme of spherical harmonic data.
 * \{ */

SphericalHarmonicL1 spherical_harmonics_unpack(vec4 L0_L1_a,
                                               vec4 L0_L1_b,
                                               vec4 L0_L1_c,
                                               vec4 L0_L1_vis)
{
  SphericalHarmonicL1 sh;
  sh.L0.M0.xyz = L0_L1_a.xyz;
  sh.L1.Mn1.xyz = L0_L1_b.xyz;
  sh.L1.M0.xyz = L0_L1_c.xyz;
  sh.L1.Mp1.xyz = vec3(L0_L1_a.w, L0_L1_b.w, L0_L1_c.w);
  sh.L0.M0.w = L0_L1_vis.x;
  sh.L1.Mn1.w = L0_L1_vis.y;
  sh.L1.M0.w = L0_L1_vis.z;
  sh.L1.Mp1.w = L0_L1_vis.w;
  return sh;
}

void spherical_harmonics_pack(SphericalHarmonicL1 sh,
                              out vec4 L0_L1_a,
                              out vec4 L0_L1_b,
                              out vec4 L0_L1_c,
                              out vec4 L0_L1_vis)
{
  L0_L1_a.xyz = sh.L0.M0.xyz;
  L0_L1_b.xyz = sh.L1.Mn1.xyz;
  L0_L1_c.xyz = sh.L1.M0.xyz;
  L0_L1_a.w = sh.L1.Mp1.x;
  L0_L1_b.w = sh.L1.Mp1.y;
  L0_L1_c.w = sh.L1.Mp1.z;
  L0_L1_vis = vec4(sh.L0.M0.w, sh.L1.Mn1.w, sh.L1.M0.w, sh.L1.Mp1.w);
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Triple Product
 * \{ */

SphericalHarmonicL1 spherical_harmonics_triple_product(SphericalHarmonicL1 a,
                                                       SphericalHarmonicL1 b)
{
  /* Adapted from:
   * "Code Generation and Factoring for Fast Evaluation of Low-order Spherical Harmonic Products
   * and Squares" Function "SH_product_3". */
  SphericalHarmonicL1 sh;
  sh.L0.M0 = 0.282094792 * a.L0.M0 * b.L0.M0;

  vec4 ta = 0.282094791 * a.L0.M0;
  vec4 tb = 0.282094791 * b.L0.M0;

  sh.L1.Mn1 = ta * b.L1.Mn1 + tb * a.L1.Mn1;
  sh.L0.M0 += 0.282094791 * (a.L1.Mn1 * b.L1.Mn1);

  sh.L1.M0 += ta * b.L1.M0 + tb * a.L1.M0;
  sh.L0.M0 += 0.282094795 * (a.L1.M0 * b.L1.M0);

  sh.L1.Mp1 += ta * b.L1.Mp1 + tb * a.L1.Mp1;
  sh.L0.M0 += 0.282094791 * (a.L1.Mp1 * b.L1.Mp1);
  return sh;
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Multiply Add
 * \{ */

SphericalHarmonicBandL0 spherical_harmonics_L0_madd(SphericalHarmonicBandL0 a,
                                                    float b,
                                                    SphericalHarmonicBandL0 c)
{
  SphericalHarmonicBandL0 result;
  result.M0 = a.M0 * b + c.M0;
  return result;
}

SphericalHarmonicBandL1 spherical_harmonics_L1_madd(SphericalHarmonicBandL1 a,
                                                    float b,
                                                    SphericalHarmonicBandL1 c)
{
  SphericalHarmonicBandL1 result;
  result.Mn1 = a.Mn1 * b + c.Mn1;
  result.M0 = a.M0 * b + c.M0;
  result.Mp1 = a.Mp1 * b + c.Mp1;
  return result;
}

SphericalHarmonicBandL2 spherical_harmonics_L2_madd(SphericalHarmonicBandL2 a,
                                                    float b,
                                                    SphericalHarmonicBandL2 c)
{
  SphericalHarmonicBandL2 result;
  result.Mn2 = a.Mn2 * b + c.Mn2;
  result.Mn1 = a.Mn1 * b + c.Mn1;
  result.M0 = a.M0 * b + c.M0;
  result.Mp1 = a.Mp1 * b + c.Mp1;
  result.Mp2 = a.Mp2 * b + c.Mp2;
  return result;
}

SphericalHarmonicL0 spherical_harmonics_madd(SphericalHarmonicL0 a, float b, SphericalHarmonicL0 c)
{
  SphericalHarmonicL0 result;
  result.L0 = spherical_harmonics_L0_madd(a.L0, b, c.L0);
  return result;
}

SphericalHarmonicL1 spherical_harmonics_madd(SphericalHarmonicL1 a, float b, SphericalHarmonicL1 c)
{
  SphericalHarmonicL1 result;
  result.L0 = spherical_harmonics_L0_madd(a.L0, b, c.L0);
  result.L1 = spherical_harmonics_L1_madd(a.L1, b, c.L1);
  return result;
}

SphericalHarmonicL2 spherical_harmonics_madd(SphericalHarmonicL2 a, float b, SphericalHarmonicL2 c)
{
  SphericalHarmonicL2 result;
  result.L0 = spherical_harmonics_L0_madd(a.L0, b, c.L0);
  result.L1 = spherical_harmonics_L1_madd(a.L1, b, c.L1);
  result.L2 = spherical_harmonics_L2_madd(a.L2, b, c.L2);
  return result;
}
/** \} */

/* -------------------------------------------------------------------- */
/** \name Multiply
 * \{ */

SphericalHarmonicBandL0 spherical_harmonics_L0_mul(SphericalHarmonicBandL0 a, float b)
{
  SphericalHarmonicBandL0 result;
  result.M0 = a.M0 * b;
  return result;
}

SphericalHarmonicBandL1 spherical_harmonics_L1_mul(SphericalHarmonicBandL1 a, float b)
{
  SphericalHarmonicBandL1 result;
  result.Mn1 = a.Mn1 * b;
  result.M0 = a.M0 * b;
  result.Mp1 = a.Mp1 * b;
  return result;
}

SphericalHarmonicBandL2 spherical_harmonics_L2_mul(SphericalHarmonicBandL2 a, float b)
{
  SphericalHarmonicBandL2 result;
  result.Mn2 = a.Mn2 * b;
  result.Mn1 = a.Mn1 * b;
  result.M0 = a.M0 * b;
  result.Mp1 = a.Mp1 * b;
  result.Mp2 = a.Mp2 * b;
  return result;
}

SphericalHarmonicL0 spherical_harmonics_mul(SphericalHarmonicL0 a, float b)
{
  SphericalHarmonicL0 result;
  result.L0 = spherical_harmonics_L0_mul(a.L0, b);
  return result;
}

SphericalHarmonicL1 spherical_harmonics_mul(SphericalHarmonicL1 a, float b)
{
  SphericalHarmonicL1 result;
  result.L0 = spherical_harmonics_L0_mul(a.L0, b);
  result.L1 = spherical_harmonics_L1_mul(a.L1, b);
  return result;
}

SphericalHarmonicL2 spherical_harmonics_mul(SphericalHarmonicL2 a, float b)
{
  SphericalHarmonicL2 result;
  result.L0 = spherical_harmonics_L0_mul(a.L0, b);
  result.L1 = spherical_harmonics_L1_mul(a.L1, b);
  result.L2 = spherical_harmonics_L2_mul(a.L2, b);
  return result;
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Add
 * \{ */

SphericalHarmonicBandL0 spherical_harmonics_L0_add(SphericalHarmonicBandL0 a,
                                                   SphericalHarmonicBandL0 b)
{
  SphericalHarmonicBandL0 result;
  result.M0 = a.M0 + b.M0;
  return result;
}

SphericalHarmonicBandL1 spherical_harmonics_L1_add(SphericalHarmonicBandL1 a,
                                                   SphericalHarmonicBandL1 b)
{
  SphericalHarmonicBandL1 result;
  result.Mn1 = a.Mn1 + b.Mn1;
  result.M0 = a.M0 + b.M0;
  result.Mp1 = a.Mp1 + b.Mp1;
  return result;
}

SphericalHarmonicBandL2 spherical_harmonics_L2_add(SphericalHarmonicBandL2 a,
                                                   SphericalHarmonicBandL2 b)
{
  SphericalHarmonicBandL2 result;
  result.Mn2 = a.Mn2 + b.Mn2;
  result.Mn1 = a.Mn1 + b.Mn1;
  result.M0 = a.M0 + b.M0;
  result.Mp1 = a.Mp1 + b.Mp1;
  result.Mp2 = a.Mp2 + b.Mp2;
  return result;
}

SphericalHarmonicL0 spherical_harmonics_add(SphericalHarmonicL0 a, SphericalHarmonicL0 b)
{
  SphericalHarmonicL0 result;
  result.L0 = spherical_harmonics_L0_add(a.L0, b.L0);
  return result;
}

SphericalHarmonicL1 spherical_harmonics_add(SphericalHarmonicL1 a, SphericalHarmonicL1 b)
{
  SphericalHarmonicL1 result;
  result.L0 = spherical_harmonics_L0_add(a.L0, b.L0);
  result.L1 = spherical_harmonics_L1_add(a.L1, b.L1);
  return result;
}

SphericalHarmonicL2 spherical_harmonics_add(SphericalHarmonicL2 a, SphericalHarmonicL2 b)
{
  SphericalHarmonicL2 result;
  result.L0 = spherical_harmonics_L0_add(a.L0, b.L0);
  result.L1 = spherical_harmonics_L1_add(a.L1, b.L1);
  result.L2 = spherical_harmonics_L2_add(a.L2, b.L2);
  return result;
}

/** \} */

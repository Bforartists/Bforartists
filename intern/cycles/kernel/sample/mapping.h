/* SPDX-FileCopyrightText: 2009-2010 Sony Pictures Imageworks Inc., et al. All Rights Reserved.
 * SPDX-FileCopyrightText: 2011-2022 Blender Foundation
 *
 * SPDX-License-Identifier: BSD-3-Clause
 *
 * Adapted code from Open Shading Language. */

#pragma once

CCL_NAMESPACE_BEGIN

/* Distribute 2D uniform random samples on [0, 1] over unit disk [-1, 1], with concentric mapping
 * to better preserve stratification for some RNG sequences. */
ccl_device float2 sample_uniform_disk(const float2 rand)
{
  float phi, r;
  float a = 2.0f * rand.x - 1.0f;
  float b = 2.0f * rand.y - 1.0f;

  if (a == 0.0f && b == 0.0f) {
    return zero_float2();
  }
  else if (a * a > b * b) {
    r = a;
    phi = M_PI_4_F * (b / a);
  }
  else {
    r = b;
    phi = M_PI_2_F - M_PI_4_F * (a / b);
  }

  return make_float2(r * cosf(phi), r * sinf(phi));
}

/* return an orthogonal tangent and bitangent given a normal and tangent that
 * may not be exactly orthogonal */
ccl_device void make_orthonormals_tangent(const float3 N,
                                          const float3 T,
                                          ccl_private float3 *a,
                                          ccl_private float3 *b)
{
  *b = normalize(cross(N, T));
  *a = cross(*b, N);
}

/* sample direction with cosine weighted distributed in hemisphere */
ccl_device_inline void sample_cos_hemisphere(const float3 N,
                                             float2 rand_in,
                                             ccl_private float3 *wo,
                                             ccl_private float *pdf)
{
  float2 rand = sample_uniform_disk(rand_in);
  float costheta = safe_sqrtf(1.0f - len_squared(rand));

  float3 T, B;
  make_orthonormals(N, &T, &B);
  *wo = rand.x * T + rand.y * B + costheta * N;
  *pdf = costheta * M_1_PI_F;
}

ccl_device_inline float pdf_cos_hemisphere(const float3 N, const float3 D)
{
  const float cos_theta = dot(N, D);
  return cos_theta > 0 ? cos_theta * M_1_PI_F : 0.0f;
}

/* sample direction uniformly distributed in hemisphere */
ccl_device_inline void sample_uniform_hemisphere(const float3 N,
                                                 const float2 rand,
                                                 ccl_private float3 *wo,
                                                 ccl_private float *pdf)
{
  float2 xy = sample_uniform_disk(rand);
  float z = 1.0f - len_squared(xy);

  xy *= safe_sqrtf(z + 1.0f);

  float3 T, B;
  make_orthonormals(N, &T, &B);

  *wo = xy.x * T + xy.y * B + z * N;
  *pdf = M_1_2PI_F;
}

ccl_device_inline float pdf_uniform_cone(const float3 N, float3 D, float angle)
{
  float z = precise_angle(N, D);
  if (z < angle) {
    return M_1_2PI_F / one_minus_cos(angle);
  }
  return 0.0f;
}

/* Uniformly sample a direction in a cone of given angle around `N`. Use concentric mapping to
 * better preserve stratification. Return the angle between `N` and the sampled direction as
 * `cos_theta`.
 * Pass `1 - cos(angle)` as argument instead of `angle` to alleviate precision issues at small
 * angles (see sphere light for reference). */
ccl_device_inline float3 sample_uniform_cone(const float3 N,
                                             const float one_minus_cos_angle,
                                             const float2 rand,
                                             ccl_private float *cos_theta,
                                             ccl_private float *pdf)
{
  if (one_minus_cos_angle > 0) {
    /* Remap radius to get a uniform distribution w.r.t. solid angle on the cone.
     * The logic to derive this mapping is as follows:
     *
     * Sampling a cone is comparable to sampling the hemisphere, we just restrict theta. Therefore,
     * the same trick of first sampling the unit disk and the projecting the result up towards the
     * hemisphere by calculating the appropriate z coordinate still works.
     *
     * However, by itself this results in cosine-weighted hemisphere sampling, so we need some kind
     * of remapping. Cosine-weighted hemisphere and uniform cone sampling have the same conditional
     * PDF for phi (both are constant), so we only need to think about theta, which corresponds
     * directly to the radius.
     *
     * To find this mapping, we consider the simplest sampling strategies for cosine-weighted
     * hemispheres and uniform cones. In both, phi is chosen as 2pi * random(). For the former,
     * r_disk(rand) = sqrt(rand). This is just naive disk sampling, since the projection to the
     * hemisphere doesn't change the radius. For the latter, r_cone(rand) =
     * sin_from_cos(mix(cos_angle, 1, rand)).
     *
     * So, to remap, we just invert r_disk `(-> rand(r_disk) = r_disk^2)` and insert it into
     * r_cone: `r_cone(r_disk) = r_cone(rand(r_disk)) = sin_from_cos(mix(cos_angle, 1, r_disk^2))`.
     * In practice, we need to replace `rand` with `1 - rand` to preserve the stratification,
     * but since it's uniform, that's fine. */
    float2 xy = sample_uniform_disk(rand);
    const float r2 = len_squared(xy);

    /* Equivalent to `mix(cos_angle, 1.0f, 1.0f - r2)`. */
    *cos_theta = 1.0f - r2 * one_minus_cos_angle;

    /* Remap disk radius to cone radius, equivalent to `xy *= sin_theta / sqrt(r2)`. */
    xy *= safe_sqrtf(one_minus_cos_angle * (2.0f - one_minus_cos_angle * r2));

    *pdf = M_1_2PI_F / one_minus_cos_angle;

    float3 T, B;
    make_orthonormals(N, &T, &B);
    return xy.x * T + xy.y * B + *cos_theta * N;
  }

  *cos_theta = 1.0f;
  *pdf = 1.0f;

  return N;
}

/* sample uniform point on the surface of a sphere */
ccl_device float3 sample_uniform_sphere(const float2 rand)
{
  float z = 1.0f - 2.0f * rand.x;
  float r = sin_from_cos(z);
  float phi = M_2PI_F * rand.y;
  float x = r * cosf(phi);
  float y = r * sinf(phi);

  return make_float3(x, y, z);
}

/* sample point in unit polygon with given number of corners and rotation */
ccl_device float2 regular_polygon_sample(float corners, float rotation, const float2 rand)
{
  float u = rand.x, v = rand.y;

  /* sample corner number and reuse u */
  float corner = floorf(u * corners);
  u = u * corners - corner;

  /* uniform sampled triangle weights */
  u = sqrtf(u);
  v = v * u;
  u = 1.0f - u;

  /* point in triangle */
  float angle = M_PI_F / corners;
  float2 p = make_float2((u + v) * cosf(angle), (u - v) * sinf(angle));

  /* rotate */
  rotation += corner * 2.0f * angle;

  float cr = cosf(rotation);
  float sr = sinf(rotation);

  return make_float2(cr * p.x - sr * p.y, sr * p.x + cr * p.y);
}

CCL_NAMESPACE_END

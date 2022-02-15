/* SPDX-License-Identifier: GPL-2.0-or-later
 * Copyright 2022 Blender Foundation. */

#pragma once

/** \file
 * \ingroup bli
 */

#include <cmath>
#include <type_traits>

#include "BLI_math_base_safe.h"
#include "BLI_math_vec_types.hh"
#include "BLI_span.hh"
#include "BLI_utildefines.h"

#ifdef WITH_GMP
#  include "BLI_math_mpq.hh"
#endif

namespace blender::math {

#ifndef NDEBUG
#  define BLI_ASSERT_UNIT(v) \
    { \
      const float _test_unit = length_squared(v); \
      BLI_assert(!(std::abs(_test_unit - 1.0f) >= BLI_ASSERT_UNIT_EPSILON) || \
                 !(std::abs(_test_unit) >= BLI_ASSERT_UNIT_EPSILON)); \
    } \
    (void)0
#else
#  define BLI_ASSERT_UNIT(v) (void)(v)
#endif

#define bT typename T::base_type

#ifdef WITH_GMP
#  define BLI_ENABLE_IF_FLT_VEC(T) \
    BLI_ENABLE_IF((std::is_floating_point_v<typename T::base_type> || \
                   std::is_same_v<typename T::base_type, mpq_class>))
#else
#  define BLI_ENABLE_IF_FLT_VEC(T) BLI_ENABLE_IF((std::is_floating_point_v<typename T::base_type>))
#endif

#define BLI_ENABLE_IF_INT_VEC(T) BLI_ENABLE_IF((std::is_integral_v<typename T::base_type>))

template<typename T> inline bool is_zero(const T &a)
{
  for (int i = 0; i < T::type_length; i++) {
    if (a[i] != bT(0)) {
      return false;
    }
  }
  return true;
}

template<typename T> inline T abs(const T &a)
{
  T result;
  for (int i = 0; i < T::type_length; i++) {
    result[i] = a[i] >= 0 ? a[i] : -a[i];
  }
  return result;
}

template<typename T> inline T min(const T &a, const T &b)
{
  T result;
  for (int i = 0; i < T::type_length; i++) {
    result[i] = a[i] < b[i] ? a[i] : b[i];
  }
  return result;
}

template<typename T> inline T max(const T &a, const T &b)
{
  T result;
  for (int i = 0; i < T::type_length; i++) {
    result[i] = a[i] > b[i] ? a[i] : b[i];
  }
  return result;
}

template<typename T> inline T clamp(const T &a, const T &min_v, const T &max_v)
{
  T result = a;
  for (int i = 0; i < T::type_length; i++) {
    CLAMP(result[i], min_v[i], max_v[i]);
  }
  return result;
}

template<typename T> inline T clamp(const T &a, const bT &min_v, const bT &max_v)
{
  T result = a;
  for (int i = 0; i < T::type_length; i++) {
    CLAMP(result[i], min_v, max_v);
  }
  return result;
}

template<typename T, BLI_ENABLE_IF_FLT_VEC(T)> inline T mod(const T &a, const T &b)
{
  T result;
  for (int i = 0; i < T::type_length; i++) {
    BLI_assert(b[i] != 0);
    result[i] = std::fmod(a[i], b[i]);
  }
  return result;
}

template<typename T, BLI_ENABLE_IF_FLT_VEC(T)> inline T mod(const T &a, bT b)
{
  BLI_assert(b != 0);
  T result;
  for (int i = 0; i < T::type_length; i++) {
    result[i] = std::fmod(a[i], b);
  }
  return result;
}

template<typename T, BLI_ENABLE_IF_FLT_VEC(T)> inline T safe_mod(const T &a, const T &b)
{
  T result;
  for (int i = 0; i < T::type_length; i++) {
    result[i] = (b[i] != 0) ? std::fmod(a[i], b[i]) : 0;
  }
  return result;
}

template<typename T, BLI_ENABLE_IF_FLT_VEC(T)> inline T safe_mod(const T &a, bT b)
{
  if (b == 0) {
    return T(0.0f);
  }
  T result;
  for (int i = 0; i < T::type_length; i++) {
    result[i] = std::fmod(a[i], b);
  }
  return result;
}

template<typename T> inline void min_max(const T &vector, T &min_vec, T &max_vec)
{
  min_vec = min(vector, min_vec);
  max_vec = max(vector, max_vec);
}

template<typename T, BLI_ENABLE_IF_FLT_VEC(T)> inline T safe_divide(const T &a, const T &b)
{
  T result;
  for (int i = 0; i < T::type_length; i++) {
    result[i] = (b[i] == 0) ? 0 : a[i] / b[i];
  }
  return result;
}

template<typename T, BLI_ENABLE_IF_FLT_VEC(T)> inline T safe_divide(const T &a, const bT b)
{
  return (b != 0) ? a / b : T(0.0f);
}

template<typename T, BLI_ENABLE_IF_FLT_VEC(T)> inline T floor(const T &a)
{
  T result;
  for (int i = 0; i < T::type_length; i++) {
    result[i] = std::floor(a[i]);
  }
  return result;
}

template<typename T, BLI_ENABLE_IF_FLT_VEC(T)> inline T ceil(const T &a)
{
  T result;
  for (int i = 0; i < T::type_length; i++) {
    result[i] = std::ceil(a[i]);
  }
  return result;
}

template<typename T, BLI_ENABLE_IF_FLT_VEC(T)> inline T fract(const T &a)
{
  T result;
  for (int i = 0; i < T::type_length; i++) {
    result[i] = a[i] - std::floor(a[i]);
  }
  return result;
}

template<typename T, BLI_ENABLE_IF_FLT_VEC(T)> inline bT dot(const T &a, const T &b)
{
  bT result = a[0] * b[0];
  for (int i = 1; i < T::type_length; i++) {
    result += a[i] * b[i];
  }
  return result;
}

template<typename T> inline bT length_manhattan(const T &a)
{
  bT result = std::abs(a[0]);
  for (int i = 1; i < T::type_length; i++) {
    result += std::abs(a[i]);
  }
  return result;
}

template<typename T, BLI_ENABLE_IF_FLT_VEC(T)> inline bT length_squared(const T &a)
{
  return dot(a, a);
}

template<typename T, BLI_ENABLE_IF_FLT_VEC(T)> inline bT length(const T &a)
{
  return std::sqrt(length_squared(a));
}

template<typename T, BLI_ENABLE_IF_FLT_VEC(T)> inline bT distance_manhattan(const T &a, const T &b)
{
  return length_manhattan(a - b);
}

template<typename T, BLI_ENABLE_IF_FLT_VEC(T)> inline bT distance_squared(const T &a, const T &b)
{
  return length_squared(a - b);
}

template<typename T, BLI_ENABLE_IF_FLT_VEC(T)> inline bT distance(const T &a, const T &b)
{
  return length(a - b);
}

template<typename T, BLI_ENABLE_IF_FLT_VEC(T)> inline T reflect(const T &incident, const T &normal)
{
  BLI_ASSERT_UNIT(normal);
  return incident - 2.0 * dot(normal, incident) * normal;
}

template<typename T, BLI_ENABLE_IF_FLT_VEC(T)>
inline T refract(const T &incident, const T &normal, const bT eta)
{
  float dot_ni = dot(normal, incident);
  float k = 1.0f - eta * eta * (1.0f - dot_ni * dot_ni);
  if (k < 0.0f) {
    return T(0.0f);
  }
  return eta * incident - (eta * dot_ni + sqrt(k)) * normal;
}

template<typename T, BLI_ENABLE_IF_FLT_VEC(T)> inline T project(const T &p, const T &v_proj)
{
  if (UNLIKELY(is_zero(v_proj))) {
    return T(0.0f);
  }
  return v_proj * (dot(p, v_proj) / dot(v_proj, v_proj));
}

template<typename T, BLI_ENABLE_IF_FLT_VEC(T)>
inline T normalize_and_get_length(const T &v, bT &out_length)
{
  out_length = length_squared(v);
  /* A larger value causes normalize errors in a scaled down models with camera extreme close. */
  constexpr bT threshold = std::is_same_v<bT, double> ? 1.0e-70 : 1.0e-35f;
  if (out_length > threshold) {
    out_length = sqrt(out_length);
    return v / out_length;
  }
  /* Either the vector is small or one of it's values contained `nan`. */
  out_length = 0.0;
  return T(0.0);
}

template<typename T, BLI_ENABLE_IF_FLT_VEC(T)> inline T normalize(const T &v)
{
  bT len;
  return normalize_and_get_length(v, len);
}

template<typename T, BLI_ENABLE_IF_FLT_VEC(T), BLI_ENABLE_IF((T::type_length == 3))>
inline T cross(const T &a, const T &b)
{
  return {a.y * b.z - a.z * b.y, a.z * b.x - a.x * b.z, a.x * b.y - a.y * b.x};
}

template<typename T,
         BLI_ENABLE_IF((std::is_same_v<bT, float>)),
         BLI_ENABLE_IF((T::type_length == 3))>
inline T cross_high_precision(const T &a, const T &b)
{
  return {(float)((double)a.y * b.z - (double)a.z * b.y),
          (float)((double)a.z * b.x - (double)a.x * b.z),
          (float)((double)a.x * b.y - (double)a.y * b.x)};
}

template<typename T, BLI_ENABLE_IF_FLT_VEC(T), BLI_ENABLE_IF((T::type_length == 3))>
inline T cross_poly(Span<T> poly)
{
  /* Newell's Method. */
  int nv = static_cast<int>(poly.size());
  if (nv < 3) {
    return T(0, 0, 0);
  }
  const T *v_prev = &poly[nv - 1];
  const T *v_curr = &poly[0];
  T n(0, 0, 0);
  for (int i = 0; i < nv;) {
    n[0] = n[0] + ((*v_prev)[1] - (*v_curr)[1]) * ((*v_prev)[2] + (*v_curr)[2]);
    n[1] = n[1] + ((*v_prev)[2] - (*v_curr)[2]) * ((*v_prev)[0] + (*v_curr)[0]);
    n[2] = n[2] + ((*v_prev)[0] - (*v_curr)[0]) * ((*v_prev)[1] + (*v_curr)[1]);
    v_prev = v_curr;
    ++i;
    if (i < nv) {
      v_curr = &poly[i];
    }
  }
  return n;
}

template<typename T, BLI_ENABLE_IF_FLT_VEC(T)> inline T interpolate(const T &a, const T &b, bT t)
{
  return a * (1 - t) + b * t;
}

template<typename T, BLI_ENABLE_IF_FLT_VEC(T)> inline T midpoint(const T &a, const T &b)
{
  return (a + b) * 0.5;
}

template<typename T, BLI_ENABLE_IF_FLT_VEC(T)>
inline T faceforward(const T &vector, const T &incident, const T &reference)
{
  return (dot(reference, incident) < 0) ? vector : -vector;
}

template<typename T> inline int dominant_axis(const T &a)
{
  T b = abs(a);
  return ((b.x > b.y) ? ((b.x > b.z) ? 0 : 2) : ((b.y > b.z) ? 1 : 2));
}

/** Intersections. */

template<typename T> struct isect_result {
  enum {
    LINE_LINE_COLINEAR = -1,
    LINE_LINE_NONE = 0,
    LINE_LINE_EXACT = 1,
    LINE_LINE_CROSS = 2,
  } kind;
  bT lambda;
};

template<typename T, BLI_ENABLE_IF_FLT_VEC(T)>
isect_result<T> isect_seg_seg(const T &v1, const T &v2, const T &v3, const T &v4);

#undef BLI_ENABLE_IF_FLT_VEC
#undef BLI_ENABLE_IF_INT_VEC
#undef bT

}  // namespace blender::math

/*
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software Foundation,
 * Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
 */

#pragma once

#include "DNA_node_types.h"

#include "BLI_float3.hh"
#include "BLI_math_base_safe.h"
#include "BLI_math_rotation.h"
#include "BLI_string_ref.hh"

namespace blender::nodes {

struct FloatMathOperationInfo {
  StringRefNull title_case_name;
  StringRefNull shader_name;

  FloatMathOperationInfo() = delete;
  FloatMathOperationInfo(StringRefNull title_case_name, StringRefNull shader_name)
      : title_case_name(title_case_name), shader_name(shader_name)
  {
  }
};

const FloatMathOperationInfo *get_float_math_operation_info(const int operation);
const FloatMathOperationInfo *get_float3_math_operation_info(const int operation);
const FloatMathOperationInfo *get_float_compare_operation_info(const int operation);

/**
 * This calls the `callback` with two arguments:
 *  1. The math function that takes a float as input and outputs a new float.
 *  2. A #FloatMathOperationInfo struct reference.
 * Returns true when the callback has been called, otherwise false.
 *
 * The math function that is passed to the callback is actually a lambda function that is different
 * for every operation. Therefore, if the callback is templated on the math function, it will get
 * instantiated for every operation separately. This has two benefits:
 *  - The compiler can optimize the callback for every operation separately.
 *  - A static variable declared in the callback will be generated for every operation separately.
 *
 * If separate instantiations are not desired, the callback can also take a function pointer with
 * the following signature as input instead: float (*math_function)(float a).
 */
template<typename Callback>
inline bool try_dispatch_float_math_fl_to_fl(const int operation, Callback &&callback)
{
  const FloatMathOperationInfo *info = get_float_math_operation_info(operation);
  if (info == nullptr) {
    return false;
  }

  /* This is just an utility function to keep the individual cases smaller. */
  auto dispatch = [&](auto math_function) -> bool {
    callback(math_function, *info);
    return true;
  };

  switch (operation) {
    case NODE_MATH_EXPONENT:
      return dispatch([](float a) { return expf(a); });
    case NODE_MATH_SQRT:
      return dispatch([](float a) { return safe_sqrtf(a); });
    case NODE_MATH_INV_SQRT:
      return dispatch([](float a) { return safe_inverse_sqrtf(a); });
    case NODE_MATH_ABSOLUTE:
      return dispatch([](float a) { return fabs(a); });
    case NODE_MATH_RADIANS:
      return dispatch([](float a) { return (float)DEG2RAD(a); });
    case NODE_MATH_DEGREES:
      return dispatch([](float a) { return (float)RAD2DEG(a); });
    case NODE_MATH_SIGN:
      return dispatch([](float a) { return compatible_signf(a); });
    case NODE_MATH_ROUND:
      return dispatch([](float a) { return floorf(a + 0.5f); });
    case NODE_MATH_FLOOR:
      return dispatch([](float a) { return floorf(a); });
    case NODE_MATH_CEIL:
      return dispatch([](float a) { return ceilf(a); });
    case NODE_MATH_FRACTION:
      return dispatch([](float a) { return a - floorf(a); });
    case NODE_MATH_TRUNC:
      return dispatch([](float a) { return a >= 0.0f ? floorf(a) : ceilf(a); });
    case NODE_MATH_SINE:
      return dispatch([](float a) { return sinf(a); });
    case NODE_MATH_COSINE:
      return dispatch([](float a) { return cosf(a); });
    case NODE_MATH_TANGENT:
      return dispatch([](float a) { return tanf(a); });
    case NODE_MATH_SINH:
      return dispatch([](float a) { return sinhf(a); });
    case NODE_MATH_COSH:
      return dispatch([](float a) { return coshf(a); });
    case NODE_MATH_TANH:
      return dispatch([](float a) { return tanhf(a); });
    case NODE_MATH_ARCSINE:
      return dispatch([](float a) { return safe_asinf(a); });
    case NODE_MATH_ARCCOSINE:
      return dispatch([](float a) { return safe_acosf(a); });
    case NODE_MATH_ARCTANGENT:
      return dispatch([](float a) { return atanf(a); });
  }
  return false;
}

/**
 * This is similar to try_dispatch_float_math_fl_to_fl, just with a different callback signature.
 */
template<typename Callback>
inline bool try_dispatch_float_math_fl_fl_to_fl(const int operation, Callback &&callback)
{
  const FloatMathOperationInfo *info = get_float_math_operation_info(operation);
  if (info == nullptr) {
    return false;
  }

  /* This is just an utility function to keep the individual cases smaller. */
  auto dispatch = [&](auto math_function) -> bool {
    callback(math_function, *info);
    return true;
  };

  switch (operation) {
    case NODE_MATH_ADD:
      return dispatch([](float a, float b) { return a + b; });
    case NODE_MATH_SUBTRACT:
      return dispatch([](float a, float b) { return a - b; });
    case NODE_MATH_MULTIPLY:
      return dispatch([](float a, float b) { return a * b; });
    case NODE_MATH_DIVIDE:
      return dispatch([](float a, float b) { return safe_divide(a, b); });
    case NODE_MATH_POWER:
      return dispatch([](float a, float b) { return safe_powf(a, b); });
    case NODE_MATH_LOGARITHM:
      return dispatch([](float a, float b) { return safe_logf(a, b); });
    case NODE_MATH_MINIMUM:
      return dispatch([](float a, float b) { return std::min(a, b); });
    case NODE_MATH_MAXIMUM:
      return dispatch([](float a, float b) { return std::max(a, b); });
    case NODE_MATH_LESS_THAN:
      return dispatch([](float a, float b) { return (float)(a < b); });
    case NODE_MATH_GREATER_THAN:
      return dispatch([](float a, float b) { return (float)(a > b); });
    case NODE_MATH_MODULO:
      return dispatch([](float a, float b) { return safe_modf(a, b); });
    case NODE_MATH_SNAP:
      return dispatch([](float a, float b) { return floorf(safe_divide(a, b)) * b; });
    case NODE_MATH_ARCTAN2:
      return dispatch([](float a, float b) { return atan2f(a, b); });
    case NODE_MATH_PINGPONG:
      return dispatch([](float a, float b) { return pingpongf(a, b); });
  }
  return false;
}

/**
 * This is similar to try_dispatch_float_math_fl_to_fl, just with a different callback signature.
 */
template<typename Callback>
inline bool try_dispatch_float_math_fl_fl_fl_to_fl(const int operation, Callback &&callback)
{
  const FloatMathOperationInfo *info = get_float_math_operation_info(operation);
  if (info == nullptr) {
    return false;
  }

  /* This is just an utility function to keep the individual cases smaller. */
  auto dispatch = [&](auto math_function) -> bool {
    callback(math_function, *info);
    return true;
  };

  switch (operation) {
    case NODE_MATH_MULTIPLY_ADD:
      return dispatch([](float a, float b, float c) { return a * b + c; });
    case NODE_MATH_COMPARE:
      return dispatch([](float a, float b, float c) -> float {
        return ((a == b) || (fabsf(a - b) <= fmaxf(c, FLT_EPSILON))) ? 1.0f : 0.0f;
      });
    case NODE_MATH_SMOOTH_MIN:
      return dispatch([](float a, float b, float c) { return smoothminf(a, b, c); });
    case NODE_MATH_SMOOTH_MAX:
      return dispatch([](float a, float b, float c) { return -smoothminf(-a, -b, -c); });
    case NODE_MATH_WRAP:
      return dispatch([](float a, float b, float c) { return wrapf(a, b, c); });
  }
  return false;
}

/**
 * This is similar to try_dispatch_float_math_fl_to_fl, just with a different callback signature.
 */
template<typename Callback>
inline bool try_dispatch_float_math_fl_fl_to_bool(const FloatCompareOperation operation,
                                                  Callback &&callback)
{
  const FloatMathOperationInfo *info = get_float_compare_operation_info(operation);
  if (info == nullptr) {
    return false;
  }

  /* This is just an utility function to keep the individual cases smaller. */
  auto dispatch = [&](auto math_function) -> bool {
    callback(math_function, *info);
    return true;
  };

  switch (operation) {
    case NODE_FLOAT_COMPARE_LESS_THAN:
      return dispatch([](float a, float b) { return a < b; });
    case NODE_FLOAT_COMPARE_LESS_EQUAL:
      return dispatch([](float a, float b) { return a <= b; });
    case NODE_FLOAT_COMPARE_GREATER_THAN:
      return dispatch([](float a, float b) { return a > b; });
    case NODE_FLOAT_COMPARE_GREATER_EQUAL:
      return dispatch([](float a, float b) { return a >= b; });
    default:
      return false;
  }
  return false;
}

/**
 * This is similar to try_dispatch_float_math_fl_to_fl, just with a different callback signature.
 */
template<typename Callback>
inline bool try_dispatch_float_math_fl3_fl3_to_fl3(const NodeVectorMathOperation operation,
                                                   Callback &&callback)
{
  const FloatMathOperationInfo *info = get_float3_math_operation_info(operation);
  if (info == nullptr) {
    return false;
  }

  /* This is just a utility function to keep the individual cases smaller. */
  auto dispatch = [&](auto math_function) -> bool {
    callback(math_function, *info);
    return true;
  };

  switch (operation) {
    case NODE_VECTOR_MATH_ADD:
      return dispatch([](float3 a, float3 b) { return a + b; });
    case NODE_VECTOR_MATH_SUBTRACT:
      return dispatch([](float3 a, float3 b) { return a - b; });
    case NODE_VECTOR_MATH_MULTIPLY:
      return dispatch([](float3 a, float3 b) { return a * b; });
    case NODE_VECTOR_MATH_DIVIDE:
      return dispatch([](float3 a, float3 b) {
        return float3(safe_divide(a.x, b.x), safe_divide(a.y, b.y), safe_divide(a.z, b.z));
      });
    case NODE_VECTOR_MATH_CROSS_PRODUCT:
      return dispatch([](float3 a, float3 b) { return float3::cross_high_precision(a, b); });
    case NODE_VECTOR_MATH_PROJECT:
      return dispatch([](float3 a, float3 b) {
        float length_squared = float3::dot(a, b);
        return (length_squared != 0.0) ? (float3::dot(a, b) / length_squared) * b : float3(0.0f);
      });
    case NODE_VECTOR_MATH_REFLECT:
      return dispatch([](float3 a, float3 b) {
        b.normalize();
        return a.reflected(b);
      });
    case NODE_VECTOR_MATH_SNAP:
      return dispatch([](float3 a, float3 b) {
        return float3(floor(safe_divide(a.x, b.x)),
                      floor(safe_divide(a.y, b.y)),
                      floor(safe_divide(a.z, b.z))) *
               b;
      });
    case NODE_VECTOR_MATH_MODULO:
      return dispatch([](float3 a, float3 b) {
        return float3(safe_modf(a.x, b.x), safe_modf(a.y, b.y), safe_modf(a.z, b.z));
      });
    case NODE_VECTOR_MATH_MINIMUM:
      return dispatch([](float3 a, float3 b) {
        return float3(min_ff(a.x, b.x), min_ff(a.y, b.y), min_ff(a.z, b.z));
      });
    case NODE_VECTOR_MATH_MAXIMUM:
      return dispatch([](float3 a, float3 b) {
        return float3(max_ff(a.x, b.x), max_ff(a.y, b.y), max_ff(a.z, b.z));
      });
    default:
      return false;
  }
  return false;
}

/**
 * This is similar to try_dispatch_float_math_fl_to_fl, just with a different callback signature.
 */
template<typename Callback>
inline bool try_dispatch_float_math_fl3_fl3_to_fl(const NodeVectorMathOperation operation,
                                                  Callback &&callback)
{
  const FloatMathOperationInfo *info = get_float3_math_operation_info(operation);
  if (info == nullptr) {
    return false;
  }

  /* This is just a utility function to keep the individual cases smaller. */
  auto dispatch = [&](auto math_function) -> bool {
    callback(math_function, *info);
    return true;
  };

  switch (operation) {
    case NODE_VECTOR_MATH_DOT_PRODUCT:
      return dispatch([](float3 a, float3 b) { return float3::dot(a, b); });
    case NODE_VECTOR_MATH_DISTANCE:
      return dispatch([](float3 a, float3 b) { return float3::distance(a, b); });
    default:
      return false;
  }
  return false;
}

/**
 * This is similar to try_dispatch_float_math_fl_to_fl, just with a different callback signature.
 */
template<typename Callback>
inline bool try_dispatch_float_math_fl3_fl3_fl3_to_fl3(const NodeVectorMathOperation operation,
                                                       Callback &&callback)
{
  const FloatMathOperationInfo *info = get_float3_math_operation_info(operation);
  if (info == nullptr) {
    return false;
  }

  /* This is just a utility function to keep the individual cases smaller. */
  auto dispatch = [&](auto math_function) -> bool {
    callback(math_function, *info);
    return true;
  };

  switch (operation) {
    case NODE_VECTOR_MATH_WRAP:
      return dispatch([](float3 a, float3 b, float3 c) {
        return float3(wrapf(a.x, b.x, c.x), wrapf(a.y, b.y, c.y), wrapf(a.z, b.z, c.z));
      });
    case NODE_VECTOR_MATH_FACEFORWARD:
      return dispatch([](float3 a, float3 b, float3 c) { return float3::faceforward(a, b, c); });
    default:
      return false;
  }
  return false;
}

/**
 * This is similar to try_dispatch_float_math_fl_to_fl, just with a different callback signature.
 */
template<typename Callback>
inline bool try_dispatch_float_math_fl3_fl3_fl_to_fl3(const NodeVectorMathOperation operation,
                                                      Callback &&callback)
{
  const FloatMathOperationInfo *info = get_float3_math_operation_info(operation);
  if (info == nullptr) {
    return false;
  }

  /* This is just a utility function to keep the individual cases smaller. */
  auto dispatch = [&](auto math_function) -> bool {
    callback(math_function, *info);
    return true;
  };

  switch (operation) {
    case NODE_VECTOR_MATH_REFRACT:
      return dispatch(
          [](float3 a, float3 b, float c) { return float3::refract(a, b.normalized(), c); });
    default:
      return false;
  }
  return false;
}

/**
 * This is similar to try_dispatch_float_math_fl_to_fl, just with a different callback signature.
 */
template<typename Callback>
inline bool try_dispatch_float_math_fl3_to_fl(const NodeVectorMathOperation operation,
                                              Callback &&callback)
{
  const FloatMathOperationInfo *info = get_float3_math_operation_info(operation);
  if (info == nullptr) {
    return false;
  }

  /* This is just a utility function to keep the individual cases smaller. */
  auto dispatch = [&](auto math_function) -> bool {
    callback(math_function, *info);
    return true;
  };

  switch (operation) {
    case NODE_VECTOR_MATH_LENGTH:
      return dispatch([](float3 in) { return in.length(); });
    default:
      return false;
  }
  return false;
}

/**
 * This is similar to try_dispatch_float_math_fl_to_fl, just with a different callback signature.
 */
template<typename Callback>
inline bool try_dispatch_float_math_fl3_fl_to_fl3(const NodeVectorMathOperation operation,
                                                  Callback &&callback)
{
  const FloatMathOperationInfo *info = get_float3_math_operation_info(operation);
  if (info == nullptr) {
    return false;
  }

  /* This is just a utility function to keep the individual cases smaller. */
  auto dispatch = [&](auto math_function) -> bool {
    callback(math_function, *info);
    return true;
  };

  switch (operation) {
    case NODE_VECTOR_MATH_SCALE:
      return dispatch([](float3 a, float b) { return a * b; });
    default:
      return false;
  }
  return false;
}

/**
 * This is similar to try_dispatch_float_math_fl_to_fl, just with a different callback signature.
 */
template<typename Callback>
inline bool try_dispatch_float_math_fl3_to_fl3(const NodeVectorMathOperation operation,
                                               Callback &&callback)
{
  const FloatMathOperationInfo *info = get_float3_math_operation_info(operation);
  if (info == nullptr) {
    return false;
  }

  /* This is just a utility function to keep the individual cases smaller. */
  auto dispatch = [&](auto math_function) -> bool {
    callback(math_function, *info);
    return true;
  };

  switch (operation) {
    case NODE_VECTOR_MATH_NORMALIZE:
      return dispatch([](float3 in) {
        float3 out = in;
        out.normalize();
        return out;
      }); /* Should be safe. */
    case NODE_VECTOR_MATH_FLOOR:
      return dispatch([](float3 in) { return float3(floor(in.x), floor(in.y), floor(in.z)); });
    case NODE_VECTOR_MATH_CEIL:
      return dispatch([](float3 in) { return float3(ceil(in.x), ceil(in.y), ceil(in.z)); });
    case NODE_VECTOR_MATH_FRACTION:
      return dispatch(
          [](float3 in) { return in - float3(floor(in.x), floor(in.y), floor(in.z)); });
    case NODE_VECTOR_MATH_ABSOLUTE:
      return dispatch([](float3 in) { return float3::abs(in); });
    case NODE_VECTOR_MATH_SINE:
      return dispatch([](float3 in) { return float3(sinf(in.x), sinf(in.y), sinf(in.z)); });
    case NODE_VECTOR_MATH_COSINE:
      return dispatch([](float3 in) { return float3(cosf(in.x), cosf(in.y), cosf(in.z)); });
    case NODE_VECTOR_MATH_TANGENT:
      return dispatch([](float3 in) { return float3(tanf(in.x), tanf(in.y), tanf(in.z)); });
    default:
      return false;
  }
  return false;
}

}  // namespace blender::nodes

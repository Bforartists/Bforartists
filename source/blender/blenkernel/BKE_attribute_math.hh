/* SPDX-License-Identifier: GPL-2.0-or-later */

#pragma once

#include "BLI_array.hh"
#include "BLI_color.hh"
#include "BLI_math_vector.h"
#include "BLI_math_vector.hh"

#include "DNA_customdata_types.h"

#include "FN_cpp_type.hh"

namespace blender::attribute_math {

using fn::CPPType;

/**
 * Utility function that simplifies calling a templated function based on a custom data type.
 */
template<typename Func>
inline void convert_to_static_type(const CustomDataType data_type, const Func &func)
{
  switch (data_type) {
    case CD_PROP_FLOAT:
      func(float());
      break;
    case CD_PROP_FLOAT2:
      func(float2());
      break;
    case CD_PROP_FLOAT3:
      func(float3());
      break;
    case CD_PROP_INT32:
      func(int());
      break;
    case CD_PROP_BOOL:
      func(bool());
      break;
    case CD_PROP_INT8:
      func(int8_t());
      break;
    case CD_PROP_COLOR:
      func(ColorGeometry4f());
      break;
    default:
      BLI_assert_unreachable();
      break;
  }
}

template<typename Func>
inline void convert_to_static_type(const fn::CPPType &cpp_type, const Func &func)
{
  if (cpp_type.is<float>()) {
    func(float());
  }
  else if (cpp_type.is<float2>()) {
    func(float2());
  }
  else if (cpp_type.is<float3>()) {
    func(float3());
  }
  else if (cpp_type.is<int>()) {
    func(int());
  }
  else if (cpp_type.is<bool>()) {
    func(bool());
  }
  else if (cpp_type.is<int8_t>()) {
    func(int8_t());
  }
  else if (cpp_type.is<ColorGeometry4f>()) {
    func(ColorGeometry4f());
  }
  else {
    BLI_assert_unreachable();
  }
}

/* -------------------------------------------------------------------- */
/** \name Mix three values of the same type.
 *
 * This is typically used to interpolate values within a triangle.
 * \{ */

template<typename T> T mix3(const float3 &weights, const T &v0, const T &v1, const T &v2);

template<>
inline int8_t mix3(const float3 &weights, const int8_t &v0, const int8_t &v1, const int8_t &v2)
{
  return static_cast<int8_t>(weights.x * v0 + weights.y * v1 + weights.z * v2);
}

template<> inline bool mix3(const float3 &weights, const bool &v0, const bool &v1, const bool &v2)
{
  return (weights.x * v0 + weights.y * v1 + weights.z * v2) >= 0.5f;
}

template<> inline int mix3(const float3 &weights, const int &v0, const int &v1, const int &v2)
{
  return static_cast<int>(weights.x * v0 + weights.y * v1 + weights.z * v2);
}

template<>
inline float mix3(const float3 &weights, const float &v0, const float &v1, const float &v2)
{
  return weights.x * v0 + weights.y * v1 + weights.z * v2;
}

template<>
inline float2 mix3(const float3 &weights, const float2 &v0, const float2 &v1, const float2 &v2)
{
  return weights.x * v0 + weights.y * v1 + weights.z * v2;
}

template<>
inline float3 mix3(const float3 &weights, const float3 &v0, const float3 &v1, const float3 &v2)
{
  return weights.x * v0 + weights.y * v1 + weights.z * v2;
}

template<>
inline ColorGeometry4f mix3(const float3 &weights,
                            const ColorGeometry4f &v0,
                            const ColorGeometry4f &v1,
                            const ColorGeometry4f &v2)
{
  ColorGeometry4f result;
  interp_v4_v4v4v4(result, v0, v1, v2, weights);
  return result;
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Mix two values of the same type.
 *
 * This is just basic linear interpolation.
 * \{ */

template<typename T> T mix2(float factor, const T &a, const T &b);

template<> inline bool mix2(const float factor, const bool &a, const bool &b)
{
  return ((1.0f - factor) * a + factor * b) >= 0.5f;
}

template<> inline int8_t mix2(const float factor, const int8_t &a, const int8_t &b)
{
  return static_cast<int8_t>((1.0f - factor) * a + factor * b);
}

template<> inline int mix2(const float factor, const int &a, const int &b)
{
  return static_cast<int>((1.0f - factor) * a + factor * b);
}

template<> inline float mix2(const float factor, const float &a, const float &b)
{
  return (1.0f - factor) * a + factor * b;
}

template<> inline float2 mix2(const float factor, const float2 &a, const float2 &b)
{
  return math::interpolate(a, b, factor);
}

template<> inline float3 mix2(const float factor, const float3 &a, const float3 &b)
{
  return math::interpolate(a, b, factor);
}

template<>
inline ColorGeometry4f mix2(const float factor, const ColorGeometry4f &a, const ColorGeometry4f &b)
{
  ColorGeometry4f result;
  interp_v4_v4v4(result, a, b, factor);
  return result;
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Mix a dynamic amount of values with weights for many elements.
 *
 * This section provides an abstraction for "mixers". The abstraction encapsulates details about
 * how different types should be mixed. Usually #DefaultMixer<T> should be used to get a mixer for
 * a specific type.
 * \{ */

template<typename T> class SimpleMixer {
 private:
  MutableSpan<T> buffer_;
  T default_value_;
  Array<float> total_weights_;

 public:
  /**
   * \param buffer: Span where the interpolated values should be stored.
   * \param default_value: Output value for an element that has not been affected by a #mix_in.
   */
  SimpleMixer(MutableSpan<T> buffer, T default_value = {})
      : buffer_(buffer), default_value_(default_value), total_weights_(buffer.size(), 0.0f)
  {
    BLI_STATIC_ASSERT(std::is_trivial_v<T>, "");
    memset(buffer_.data(), 0, sizeof(T) * buffer_.size());
  }

  /**
   * Mix a #value into the element with the given #index.
   */
  void mix_in(const int64_t index, const T &value, const float weight = 1.0f)
  {
    BLI_assert(weight >= 0.0f);
    buffer_[index] += value * weight;
    total_weights_[index] += weight;
  }

  /**
   * Has to be called before the buffer provided in the constructor is used.
   */
  void finalize()
  {
    for (const int64_t i : buffer_.index_range()) {
      const float weight = total_weights_[i];
      if (weight > 0.0f) {
        buffer_[i] *= 1.0f / weight;
      }
      else {
        buffer_[i] = default_value_;
      }
    }
  }
};

/**
 * Mixes together booleans with "or" while fitting the same interface as the other
 * mixers in order to be simpler to use. This mixing method has a few benefits:
 *  - An "average" for selections is relatively meaningless.
 *  - Predictable selection propagation is very super important.
 *  - It's generally  easier to remove an element from a selection that is slightly too large than
 *    the opposite.
 */
class BooleanPropagationMixer {
 private:
  MutableSpan<bool> buffer_;

 public:
  /**
   * \param buffer: Span where the interpolated values should be stored.
   */
  BooleanPropagationMixer(MutableSpan<bool> buffer) : buffer_(buffer)
  {
    buffer_.fill(false);
  }

  /**
   * Mix a #value into the element with the given #index.
   */
  void mix_in(const int64_t index, const bool value, [[maybe_unused]] const float weight = 1.0f)
  {
    buffer_[index] |= value;
  }

  /**
   * Does not do anything, since the mixing is trivial.
   */
  void finalize()
  {
  }
};

/**
 * This mixer accumulates values in a type that is different from the one that is mixed.
 * Some types cannot encode the floating point weights in their values (e.g. int and bool).
 */
template<typename T, typename AccumulationT, T (*ConvertToT)(const AccumulationT &value)>
class SimpleMixerWithAccumulationType {
 private:
  struct Item {
    /* Store both values together, because they are accessed together. */
    AccumulationT value = {0};
    float weight = 0.0f;
  };

  MutableSpan<T> buffer_;
  T default_value_;
  Array<Item> accumulation_buffer_;

 public:
  SimpleMixerWithAccumulationType(MutableSpan<T> buffer, T default_value = {})
      : buffer_(buffer), default_value_(default_value), accumulation_buffer_(buffer.size())
  {
  }

  void mix_in(const int64_t index, const T &value, const float weight = 1.0f)
  {
    const AccumulationT converted_value = static_cast<AccumulationT>(value);
    Item &item = accumulation_buffer_[index];
    item.value += converted_value * weight;
    item.weight += weight;
  }

  void finalize()
  {
    for (const int64_t i : buffer_.index_range()) {
      const Item &item = accumulation_buffer_[i];
      if (item.weight > 0.0f) {
        const float weight_inv = 1.0f / item.weight;
        const T converted_value = ConvertToT(item.value * weight_inv);
        buffer_[i] = converted_value;
      }
      else {
        buffer_[i] = default_value_;
      }
    }
  }
};

class ColorGeometryMixer {
 private:
  MutableSpan<ColorGeometry4f> buffer_;
  ColorGeometry4f default_color_;
  Array<float> total_weights_;

 public:
  ColorGeometryMixer(MutableSpan<ColorGeometry4f> buffer,
                     ColorGeometry4f default_color = ColorGeometry4f(0.0f, 0.0f, 0.0f, 1.0f));
  void mix_in(int64_t index, const ColorGeometry4f &color, float weight = 1.0f);
  void finalize();
};

template<typename T> struct DefaultMixerStruct {
  /* Use void by default. This can be checked for in `if constexpr` statements. */
  using type = void;
};
template<> struct DefaultMixerStruct<float> {
  using type = SimpleMixer<float>;
};
template<> struct DefaultMixerStruct<float2> {
  using type = SimpleMixer<float2>;
};
template<> struct DefaultMixerStruct<float3> {
  using type = SimpleMixer<float3>;
};
template<> struct DefaultMixerStruct<ColorGeometry4f> {
  /* Use a special mixer for colors. ColorGeometry4f can't be added/multiplied, because this is not
   * something one should usually do with colors. */
  using type = ColorGeometryMixer;
};
template<> struct DefaultMixerStruct<int> {
  static int double_to_int(const double &value)
  {
    return static_cast<int>(value);
  }
  /* Store interpolated ints in a double temporarily, so that weights are handled correctly. It
   * uses double instead of float so that it is accurate for all 32 bit integers. */
  using type = SimpleMixerWithAccumulationType<int, double, double_to_int>;
};
template<> struct DefaultMixerStruct<bool> {
  static bool float_to_bool(const float &value)
  {
    return value >= 0.5f;
  }
  /* Store interpolated booleans in a float temporary.
   * Otherwise information provided by weights is easily rounded away. */
  using type = SimpleMixerWithAccumulationType<bool, float, float_to_bool>;
};

template<> struct DefaultMixerStruct<int8_t> {
  static int8_t float_to_int8_t(const float &value)
  {
    return static_cast<int8_t>(value);
  }
  /* Store interpolated 8 bit integers in a float temporarily to increase accuracy. */
  using type = SimpleMixerWithAccumulationType<int8_t, float, float_to_int8_t>;
};

template<typename T> struct DefaultPropatationMixerStruct {
  /* Use void by default. This can be checked for in `if constexpr` statements. */
  using type = typename DefaultMixerStruct<T>::type;
};

template<> struct DefaultPropatationMixerStruct<bool> {
  using type = BooleanPropagationMixer;
};

/**
 * This mixer is meant for propagating attributes when creating new geometry. A key difference
 * with the default mixer is that booleans are mixed with "or" instead of "at least half"
 * (the default mixing for booleans).
 */
template<typename T>
using DefaultPropatationMixer = typename DefaultPropatationMixerStruct<T>::type;

/* Utility to get a good default mixer for a given type. This is `void` when there is no default
 * mixer for the given type. */
template<typename T> using DefaultMixer = typename DefaultMixerStruct<T>::type;

/** \} */

}  // namespace blender::attribute_math

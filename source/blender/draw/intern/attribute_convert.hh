/* SPDX-FileCopyrightText: 2005 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup gpu
 */

#include "BLI_color.hh"
#include "BLI_generic_span.hh"
#include "BLI_math_quaternion_types.hh"
#include "BLI_math_vector_types.hh"
#include "BLI_string_ref.hh"

#include "DNA_customdata_types.h" /* #eCustomDataType. */

#include "GPU_vertex_format.h"

struct GPUVertBuf;

/**
 * Component length of 3 is used for scalars because implicit conversion is done by OpenGL from a
 * scalar `s` will produce `vec4(s, 0, 0, 1)`. However, following the Blender convention, it should
 * be `vec4(s, s, s, 1)`.
 */
constexpr int COMPONENT_LEN_SCALAR = 3;

namespace blender::draw {

/**
 * Utility to convert from the type used in the attributes to the types for GPU vertex buffers.
 */
template<typename T> struct AttributeConverter {
  using VBOType = void;
};

template<> struct AttributeConverter<bool> {
  using VBOType = VecBase<int, COMPONENT_LEN_SCALAR>;
  static constexpr GPUVertCompType gpu_component_type = GPU_COMP_I32;
  static constexpr int gpu_component_len = COMPONENT_LEN_SCALAR;
  static constexpr GPUVertFetchMode gpu_fetch_mode = GPU_FETCH_INT_TO_FLOAT;
  static VBOType convert(const bool &value)
  {
    return VBOType(value);
  }
};
template<> struct AttributeConverter<int8_t> {
  using VBOType = VecBase<int, COMPONENT_LEN_SCALAR>;
  static constexpr GPUVertCompType gpu_component_type = GPU_COMP_I32;
  static constexpr int gpu_component_len = COMPONENT_LEN_SCALAR;
  static constexpr GPUVertFetchMode gpu_fetch_mode = GPU_FETCH_INT_TO_FLOAT;
  static VBOType convert(const int8_t &value)
  {
    return VecBase<int, COMPONENT_LEN_SCALAR>(value);
  }
};
template<> struct AttributeConverter<int> {
  using VBOType = VecBase<int, COMPONENT_LEN_SCALAR>;
  static constexpr GPUVertCompType gpu_component_type = GPU_COMP_I32;
  static constexpr int gpu_component_len = COMPONENT_LEN_SCALAR;
  static constexpr GPUVertFetchMode gpu_fetch_mode = GPU_FETCH_INT_TO_FLOAT;
  static VBOType convert(const int &value)
  {
    return int3(value);
  }
};
template<> struct AttributeConverter<int2> {
  using VBOType = int2;
  static constexpr GPUVertCompType gpu_component_type = GPU_COMP_I32;
  static constexpr int gpu_component_len = 2;
  static constexpr GPUVertFetchMode gpu_fetch_mode = GPU_FETCH_INT_TO_FLOAT;
  static VBOType convert(const int2 &value)
  {
    return int2(value.x, value.y);
  }
};
template<> struct AttributeConverter<float> {
  using VBOType = VecBase<float, COMPONENT_LEN_SCALAR>;
  static constexpr GPUVertCompType gpu_component_type = GPU_COMP_F32;
  static constexpr int gpu_component_len = COMPONENT_LEN_SCALAR;
  static constexpr GPUVertFetchMode gpu_fetch_mode = GPU_FETCH_FLOAT;
  static VBOType convert(const float &value)
  {
    return VBOType(value);
  }
};
template<> struct AttributeConverter<float2> {
  using VBOType = float2;
  static constexpr GPUVertCompType gpu_component_type = GPU_COMP_F32;
  static constexpr int gpu_component_len = 2;
  static constexpr GPUVertFetchMode gpu_fetch_mode = GPU_FETCH_FLOAT;
  static VBOType convert(const float2 &value)
  {
    return value;
  }
};
template<> struct AttributeConverter<float3> {
  using VBOType = float3;
  static constexpr GPUVertCompType gpu_component_type = GPU_COMP_F32;
  static constexpr int gpu_component_len = 3;
  static constexpr GPUVertFetchMode gpu_fetch_mode = GPU_FETCH_FLOAT;
  static VBOType convert(const float3 &value)
  {
    return value;
  }
};
template<> struct AttributeConverter<ColorGeometry4b> {
  /* 16 bits are required to store the color in linear space without precision loss. */
  using VBOType = ushort4;
  static constexpr GPUVertCompType gpu_component_type = GPU_COMP_U16;
  static constexpr int gpu_component_len = 4;
  static constexpr GPUVertFetchMode gpu_fetch_mode = GPU_FETCH_INT_TO_FLOAT_UNIT;
  static VBOType convert(const ColorGeometry4b &value)
  {
    return {unit_float_to_ushort_clamp(BLI_color_from_srgb_table[value.r]),
            unit_float_to_ushort_clamp(BLI_color_from_srgb_table[value.g]),
            unit_float_to_ushort_clamp(BLI_color_from_srgb_table[value.b]),
            ushort(value.a * 257)};
  }
};
template<> struct AttributeConverter<ColorGeometry4f> {
  using VBOType = ColorGeometry4f;
  static constexpr GPUVertCompType gpu_component_type = GPU_COMP_F32;
  static constexpr int gpu_component_len = 4;
  static constexpr GPUVertFetchMode gpu_fetch_mode = GPU_FETCH_FLOAT;
  static VBOType convert(const ColorGeometry4f &value)
  {
    return value;
  }
};
template<> struct AttributeConverter<math::Quaternion> {
  using VBOType = float4;
  static constexpr GPUVertCompType gpu_component_type = GPU_COMP_F32;
  static constexpr int gpu_component_len = 4;
  static constexpr GPUVertFetchMode gpu_fetch_mode = GPU_FETCH_FLOAT;
  static VBOType convert(const math::Quaternion &value)
  {
    return float4(value.w, value.x, value.y, value.z);
  }
};

GPUVertFormat init_format_for_attribute(eCustomDataType data_type, StringRefNull vbo_name);

void vertbuf_data_extract_direct(GSpan attribute, GPUVertBuf &vbo);

}  // namespace blender::draw

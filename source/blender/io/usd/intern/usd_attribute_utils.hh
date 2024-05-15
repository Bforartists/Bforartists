/* SPDX-FileCopyrightText: 2024 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */
#pragma once

#include "BLI_color.hh"
#include "BLI_generic_virtual_array.hh"
#include "BLI_math_quaternion_types.hh"
#include "BLI_math_vector_types.hh"
#include "BLI_span.hh"
#include "BLI_virtual_array.hh"

#include "BKE_attribute.hh"

#include "DNA_customdata_types.h"

#include <pxr/base/gf/quatf.h>
#include <pxr/base/gf/vec2f.h>
#include <pxr/base/gf/vec3f.h>
#include <pxr/base/vt/array.h>

#include <pxr/usd/sdf/types.h>
#include <pxr/usd/sdf/valueTypeName.h>
#include <pxr/usd/usd/timeCode.h>
#include <pxr/usd/usdGeom/primvar.h>
#include <pxr/usd/usdUtils/sparseValueWriter.h>

#include <cstdint>
#include <optional>
#include <type_traits>

namespace blender::io::usd {

namespace detail {

/* Until we can use C++20, implement our own version of std::is_layout_compatible.
 * Types with compatible layouts can be exchanged much more efficiently than otherwise.
 */
template<class T, class U> struct is_layout_compatible : std::false_type {};

template<> struct is_layout_compatible<float2, pxr::GfVec2f> : std::true_type {};
template<> struct is_layout_compatible<float3, pxr::GfVec3f> : std::true_type {};

template<> struct is_layout_compatible<pxr::GfVec2f, float2> : std::true_type {};
template<> struct is_layout_compatible<pxr::GfVec3f, float3> : std::true_type {};

/* Conversion utilities to convert a Blender type to an USD type. */
template<typename From, typename To> inline To convert_value(const From value)
{
  return value;
}

template<> inline pxr::GfVec2f convert_value(const float2 value)
{
  return pxr::GfVec2f(value[0], value[1]);
}
template<> inline pxr::GfVec3f convert_value(const float3 value)
{
  return pxr::GfVec3f(value[0], value[1], value[2]);
}
template<> inline pxr::GfVec3f convert_value(const ColorGeometry4f value)
{
  return pxr::GfVec3f(value.r, value.g, value.b);
}
template<> inline pxr::GfQuatf convert_value(const math::Quaternion value)
{
  return pxr::GfQuatf(value.x, value.y, value.z, value.w);
}

template<> inline float2 convert_value(const pxr::GfVec2f value)
{
  return float2(value[0], value[1]);
}
template<> inline float3 convert_value(const pxr::GfVec3f value)
{
  return float3(value[0], value[1], value[2]);
}
template<> inline ColorGeometry4f convert_value(const pxr::GfVec3f value)
{
  return ColorGeometry4f(value[0], value[1], value[2], 1.0f);
}

}  // namespace detail

std::optional<pxr::SdfValueTypeName> convert_blender_type_to_usd(
    const eCustomDataType blender_type);

std::optional<eCustomDataType> convert_usd_type_to_blender(const pxr::SdfValueTypeName usd_type);

/* Copy a typed Blender attribute array into a typed USD primvar attribute. */
template<typename BlenderT, typename USDT>
void copy_blender_buffer_to_primvar(const VArray<BlenderT> &buffer,
                                    const pxr::UsdTimeCode timecode,
                                    const pxr::UsdGeomPrimvar &primvar,
                                    pxr::UsdUtilsSparseValueWriter &value_writer)
{
  constexpr bool is_same = std::is_same_v<BlenderT, USDT>;
  constexpr bool is_compatible = detail::is_layout_compatible<BlenderT, USDT>::value;

  pxr::VtArray<USDT> usd_data;
  if (const std::optional<BlenderT> value = buffer.get_if_single()) {
    usd_data.assign(buffer.size(), detail::convert_value<BlenderT, USDT>(*value));
  }
  else {
    const VArraySpan<BlenderT> data(buffer);
    if constexpr (is_same || is_compatible) {
      usd_data.assign(data.template cast<USDT>().begin(), data.template cast<USDT>().end());
    }
    else {
      usd_data.resize(data.size());
      for (const int i : data.index_range()) {
        usd_data[i] = detail::convert_value<BlenderT, USDT>(data[i]);
      }
    }
  }

  if (!primvar.HasValue() && timecode != pxr::UsdTimeCode::Default()) {
    primvar.Set(usd_data, pxr::UsdTimeCode::Default());
  }
  else {
    primvar.Set(usd_data, timecode);
  }

  value_writer.SetAttribute(primvar.GetAttr(), usd_data, timecode);
}

void copy_blender_attribute_to_primvar(const GVArray &attribute,
                                       const eCustomDataType data_type,
                                       const pxr::UsdTimeCode timecode,
                                       const pxr::UsdGeomPrimvar &primvar,
                                       pxr::UsdUtilsSparseValueWriter &value_writer);

template<typename T>
pxr::VtArray<T> get_primvar_array(const pxr::UsdGeomPrimvar &primvar,
                                  const pxr::UsdTimeCode timecode)
{
  pxr::VtValue primvar_val;
  if (!primvar.ComputeFlattened(&primvar_val, timecode)) {
    return {};
  }

  if (!primvar_val.CanCast<pxr::VtArray<T>>()) {
    return {};
  }

  return primvar_val.Cast<pxr::VtArray<T>>().template UncheckedGet<pxr::VtArray<T>>();
}

template<typename USDT, typename BlenderT>
void copy_primvar_to_blender_buffer(const pxr::UsdGeomPrimvar &primvar,
                                    const pxr::UsdTimeCode timecode,
                                    const OffsetIndices<int> faces,
                                    MutableSpan<BlenderT> attribute)
{
  pxr::VtArray<USDT> usd_data = get_primvar_array<USDT>(primvar, timecode);
  if (usd_data.empty()) {
    return;
  }

  constexpr bool is_same = std::is_same_v<USDT, BlenderT>;
  constexpr bool is_compatible = detail::is_layout_compatible<USDT, BlenderT>::value;

  const pxr::TfToken pv_interp = primvar.GetInterpolation();
  if (pv_interp == pxr::UsdGeomTokens->constant) {
    /* For situations where there's only a single item, flood fill the object. */
    attribute.fill(detail::convert_value<USDT, BlenderT>(usd_data[0]));
  }
  else if (pv_interp == pxr::UsdGeomTokens->faceVarying) {
    if (!faces.is_empty()) {
      /* Reverse the index order. */
      for (const int i : faces.index_range()) {
        const IndexRange face = faces[i];
        for (int j : face.index_range()) {
          const int rev_index = face.last(j);
          attribute[face.start() + j] = detail::convert_value<USDT, BlenderT>(usd_data[rev_index]);
        }
      }
    }
    else {
      if constexpr (is_same || is_compatible) {
        const Span<USDT> src(usd_data.data(), usd_data.size());
        attribute.copy_from(src.template cast<BlenderT>());
      }
      else {
        for (const int64_t i : attribute.index_range()) {
          attribute[i] = detail::convert_value<USDT, BlenderT>(usd_data[i]);
        }
      }
    }
  }
  else {
    /* Assume direct one-to-one mapping. */
    if (usd_data.size() == attribute.size()) {
      if constexpr (is_same || is_compatible) {
        const Span<USDT> src(usd_data.data(), usd_data.size());
        attribute.copy_from(src.template cast<BlenderT>());
      }
      else {
        for (const int64_t i : attribute.index_range()) {
          attribute[i] = detail::convert_value<USDT, BlenderT>(usd_data[i]);
        }
      }
    }
  }
}

void copy_primvar_to_blender_attribute(const pxr::UsdGeomPrimvar &primvar,
                                       const pxr::UsdTimeCode timecode,
                                       const eCustomDataType data_type,
                                       const bke::AttrDomain domain,
                                       const OffsetIndices<int> face_indices,
                                       bke::MutableAttributeAccessor attributes);

}  // namespace blender::io::usd

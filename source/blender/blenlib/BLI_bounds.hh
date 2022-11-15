/* SPDX-License-Identifier: GPL-2.0-or-later */

#pragma once

/** \file
 * \ingroup bli
 *
 * Generic algorithms for finding the largest and smallest elements in a span.
 */

#include <optional>

#include "BLI_bounds_types.hh"
#include "BLI_math_vector.hh"
#include "BLI_task.hh"

namespace blender::bounds {

/**
 * Find the smallest and largest values element-wise in the span.
 */
template<typename T> static std::optional<Bounds<T>> min_max(Span<T> values)
{
  if (values.is_empty()) {
    return std::nullopt;
  }
  const Bounds<T> init{values.first(), values.first()};
  return threading::parallel_reduce(
      values.index_range(),
      1024,
      init,
      [&](IndexRange range, const Bounds<T> &init) {
        Bounds<T> result = init;
        for (const int i : range) {
          math::min_max(values[i], result.min, result.max);
        }
        return result;
      },
      [](const Bounds<T> &a, const Bounds<T> &b) {
        return Bounds<T>{math::min(a.min, b.min), math::max(a.max, b.max)};
      });
}

/**
 * Find the smallest and largest values element-wise in the span, adding the radius to each element
 * first. The template type T is expected to have an addition operator implemented with RadiusT.
 */
template<typename T, typename RadiusT>
static std::optional<Bounds<T>> min_max_with_radii(Span<T> values, Span<RadiusT> radii)
{
  BLI_assert(values.size() == radii.size());
  if (values.is_empty()) {
    return std::nullopt;
  }
  const Bounds<T> init{values.first(), values.first()};
  return threading::parallel_reduce(
      values.index_range(),
      1024,
      init,
      [&](IndexRange range, const Bounds<T> &init) {
        Bounds<T> result = init;
        for (const int i : range) {
          result.min = math::min(values[i] - radii[i], result.min);
          result.max = math::max(values[i] + radii[i], result.max);
        }
        return result;
      },
      [](const Bounds<T> &a, const Bounds<T> &b) {
        return Bounds<T>{math::min(a.min, b.min), math::max(a.max, b.max)};
      });
}

}  // namespace blender::bounds

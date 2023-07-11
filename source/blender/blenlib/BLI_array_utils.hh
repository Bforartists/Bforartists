/* SPDX-FileCopyrightText: 2023 Blender Foundation
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#pragma once

#include "BLI_generic_span.hh"
#include "BLI_generic_virtual_array.hh"
#include "BLI_index_mask.hh"
#include "BLI_task.hh"
#include "BLI_virtual_array.hh"

namespace blender::array_utils {

/**
 * Fill the destination span by copying all values from the `src` array. Threaded based on
 * grain-size.
 */
void copy(const GVArray &src, GMutableSpan dst, int64_t grain_size = 4096);
template<typename T>
inline void copy(const VArray<T> &src, MutableSpan<T> dst, const int64_t grain_size = 4096)
{
  BLI_assert(src.size() == dst.size());
  threading::parallel_for(src.index_range(), grain_size, [&](const IndexRange range) {
    src.materialize_to_uninitialized(range, dst);
  });
}

/**
 * Fill the destination span by copying all values from the `src` array. Threaded based on
 * grain-size.
 */
template<typename T>
inline void copy(const Span<T> src, MutableSpan<T> dst, const int64_t grain_size = 4096)
{
  BLI_assert(src.size() == dst.size());
  threading::parallel_for(src.index_range(), grain_size, [&](const IndexRange range) {
    dst.slice(range).copy_from(src.slice(range));
  });
}

/**
 * Fill the destination span by copying masked values from the `src` array. Threaded based on
 * grain-size.
 */
void copy(const GVArray &src,
          const IndexMask &selection,
          GMutableSpan dst,
          int64_t grain_size = 4096);

/**
 * Fill the destination span by copying values from the `src` array. Threaded based on
 * grain-size.
 */
template<typename T>
inline void copy(const Span<T> src,
                 const IndexMask &selection,
                 MutableSpan<T> dst,
                 const int64_t grain_size = 4096)
{
  BLI_assert(src.size() == dst.size());
  selection.foreach_index_optimized<int64_t>(GrainSize(grain_size),
                                             [&](const int64_t i) { dst[i] = src[i]; });
}

/**
 * Fill the destination span by gathering indexed values from the `src` array.
 */
void gather(const GVArray &src,
            const IndexMask &indices,
            GMutableSpan dst,
            int64_t grain_size = 4096);

/**
 * Fill the destination span by gathering indexed values from the `src` array.
 */
void gather(GSpan src, const IndexMask &indices, GMutableSpan dst, int64_t grain_size = 4096);

/**
 * Fill the destination span by gathering indexed values from the `src` array.
 */
template<typename T>
inline void gather(const VArray<T> &src,
                   const IndexMask &indices,
                   MutableSpan<T> dst,
                   const int64_t grain_size = 4096)
{
  BLI_assert(indices.size() == dst.size());
  threading::parallel_for(indices.index_range(), grain_size, [&](const IndexRange range) {
    src.materialize_compressed_to_uninitialized(indices.slice(range), dst.slice(range));
  });
}

/**
 * Fill the destination span by gathering indexed values from the `src` array.
 */
template<typename T, typename IndexT>
inline void gather(const Span<T> src,
                   const IndexMask &indices,
                   MutableSpan<T> dst,
                   const int64_t grain_size = 4096)
{
  BLI_assert(indices.size() == dst.size());
  indices.foreach_segment(GrainSize(grain_size),
                          [&](const IndexMaskSegment segment, const int64_t segment_pos) {
                            for (const int64_t i : segment.index_range()) {
                              dst[segment_pos + i] = src[segment[i]];
                            }
                          });
}

/**
 * Fill the destination span by gathering indexed values from the `src` array.
 */
template<typename T, typename IndexT>
inline void gather(const Span<T> src,
                   const Span<IndexT> indices,
                   MutableSpan<T> dst,
                   const int64_t grain_size = 4096)
{
  BLI_assert(indices.size() == dst.size());
  threading::parallel_for(indices.index_range(), grain_size, [&](const IndexRange range) {
    for (const int64_t i : range) {
      dst[i] = src[indices[i]];
    }
  });
}

/**
 * Fill the destination span by gathering indexed values from the `src` array.
 */
template<typename T, typename IndexT>
inline void gather(const VArray<T> &src,
                   const Span<IndexT> indices,
                   MutableSpan<T> dst,
                   const int64_t grain_size = 4096)
{
  BLI_assert(indices.size() == dst.size());
  devirtualize_varray(src, [&](const auto &src) {
    threading::parallel_for(indices.index_range(), grain_size, [&](const IndexRange range) {
      for (const int64_t i : range) {
        dst[i] = src[indices[i]];
      }
    });
  });
}

/**
 * Count the number of occurrences of each index.
 * \param indices: The indices to count.
 * \param counts: The number of occurrences of each index. Typically initialized to zero.
 * Must be large enough to contain the maximum index.
 *
 * \note The memory referenced by the two spans must not overlap.
 */
void count_indices(Span<int> indices, MutableSpan<int> counts);

void invert_booleans(MutableSpan<bool> span);

enum class BooleanMix {
  None,
  AllFalse,
  AllTrue,
  Mixed,
};
BooleanMix booleans_mix_calc(const VArray<bool> &varray, IndexRange range_to_check);
inline BooleanMix booleans_mix_calc(const VArray<bool> &varray)
{
  return booleans_mix_calc(varray, varray.index_range());
}

}  // namespace blender::array_utils

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

#include "BLI_array.hh"
#include "BLI_span.hh"
#include "BLI_task.hh"
#include "BLI_timeit.hh"

#include "BKE_spline.hh"

#include "FN_generic_virtual_array.hh"

using blender::Array;
using blender::float3;
using blender::IndexRange;
using blender::MutableSpan;
using blender::Span;
using blender::fn::GMutableSpan;
using blender::fn::GSpan;
using blender::fn::GVArray;
using blender::fn::GVArray_For_GSpan;
using blender::fn::GVArray_Typed;
using blender::fn::GVArrayPtr;

Spline::Type Spline::type() const
{
  return type_;
}

void Spline::translate(const blender::float3 &translation)
{
  for (float3 &position : this->positions()) {
    position += translation;
  }
  this->mark_cache_invalid();
}

void Spline::transform(const blender::float4x4 &matrix)
{
  for (float3 &position : this->positions()) {
    position = matrix * position;
  }
  this->mark_cache_invalid();
}

int Spline::evaluated_edges_size() const
{
  const int eval_size = this->evaluated_points_size();
  if (eval_size == 1) {
    return 0;
  }

  return this->is_cyclic_ ? eval_size : eval_size - 1;
}

float Spline::length() const
{
  Span<float> lengths = this->evaluated_lengths();
  return (lengths.size() == 0) ? 0 : this->evaluated_lengths().last();
}

int Spline::segments_size() const
{
  const int points_len = this->size();

  return is_cyclic_ ? points_len : points_len - 1;
}

bool Spline::is_cyclic() const
{
  return is_cyclic_;
}

void Spline::set_cyclic(const bool value)
{
  is_cyclic_ = value;
}

static void accumulate_lengths(Span<float3> positions,
                               const bool is_cyclic,
                               MutableSpan<float> lengths)
{
  float length = 0.0f;
  for (const int i : IndexRange(positions.size() - 1)) {
    length += float3::distance(positions[i], positions[i + 1]);
    lengths[i] = length;
  }
  if (is_cyclic) {
    lengths.last() = length + float3::distance(positions.last(), positions.first());
  }
}

/**
 * Return non-owning access to the cache of accumulated lengths along the spline. Each item is the
 * length of the subsequent segment, i.e. the first value is the length of the first segment rather
 * than 0. This calculation is rather trivial, and only depends on the evaluated positions.
 * However, the results are used often, so it makes sense to cache it.
 */
Span<float> Spline::evaluated_lengths() const
{
  if (!length_cache_dirty_) {
    return evaluated_lengths_cache_;
  }

  std::lock_guard lock{length_cache_mutex_};
  if (!length_cache_dirty_) {
    return evaluated_lengths_cache_;
  }

  const int total = evaluated_edges_size();
  evaluated_lengths_cache_.resize(total);

  Span<float3> positions = this->evaluated_positions();
  accumulate_lengths(positions, is_cyclic_, evaluated_lengths_cache_);

  length_cache_dirty_ = false;
  return evaluated_lengths_cache_;
}

static float3 direction_bisect(const float3 &prev, const float3 &middle, const float3 &next)
{
  const float3 dir_prev = (middle - prev).normalized();
  const float3 dir_next = (next - middle).normalized();

  return (dir_prev + dir_next).normalized();
}

static void calculate_tangents(Span<float3> positions,
                               const bool is_cyclic,
                               MutableSpan<float3> tangents)
{
  if (positions.size() == 1) {
    return;
  }

  for (const int i : IndexRange(1, positions.size() - 2)) {
    tangents[i] = direction_bisect(positions[i - 1], positions[i], positions[i + 1]);
  }

  if (is_cyclic) {
    const float3 &second_to_last = positions[positions.size() - 2];
    const float3 &last = positions.last();
    const float3 &first = positions.first();
    const float3 &second = positions[1];
    tangents.first() = direction_bisect(last, first, second);
    tangents.last() = direction_bisect(second_to_last, last, first);
  }
  else {
    tangents.first() = (positions[1] - positions[0]).normalized();
    tangents.last() = (positions.last() - positions[positions.size() - 2]).normalized();
  }
}

/**
 * Return non-owning access to the direction of the curve at each evaluated point.
 */
Span<float3> Spline::evaluated_tangents() const
{
  if (!tangent_cache_dirty_) {
    return evaluated_tangents_cache_;
  }

  std::lock_guard lock{tangent_cache_mutex_};
  if (!tangent_cache_dirty_) {
    return evaluated_tangents_cache_;
  }

  const int eval_size = this->evaluated_points_size();
  evaluated_tangents_cache_.resize(eval_size);

  Span<float3> positions = this->evaluated_positions();

  if (eval_size == 1) {
    evaluated_tangents_cache_.first() = float3(1.0f, 0.0f, 0.0f);
  }
  else {
    calculate_tangents(positions, is_cyclic_, evaluated_tangents_cache_);
    this->correct_end_tangents();
  }

  tangent_cache_dirty_ = false;
  return evaluated_tangents_cache_;
}

static float3 rotate_direction_around_axis(const float3 &direction,
                                           const float3 &axis,
                                           const float angle)
{
  BLI_ASSERT_UNIT_V3(direction);
  BLI_ASSERT_UNIT_V3(axis);

  const float3 axis_scaled = axis * float3::dot(direction, axis);
  const float3 diff = direction - axis_scaled;
  const float3 cross = float3::cross(axis, diff);

  return axis_scaled + diff * std::cos(angle) + cross * std::sin(angle);
}

static void calculate_normals_z_up(Span<float3> tangents, MutableSpan<float3> r_normals)
{
  BLI_assert(r_normals.size() == tangents.size());

  /* Same as in `vec_to_quat`. */
  const float epsilon = 1e-4f;
  for (const int i : r_normals.index_range()) {
    const float3 &tangent = tangents[i];
    if (fabsf(tangent.x) + fabsf(tangent.y) < epsilon) {
      r_normals[i] = {1.0f, 0.0f, 0.0f};
    }
    else {
      r_normals[i] = float3(tangent.y, -tangent.x, 0.0f).normalized();
    }
  }
}

/**
 * Rotate the last normal in the same way the tangent has been rotated.
 */
static float3 calculate_next_normal(const float3 &last_normal,
                                    const float3 &last_tangent,
                                    const float3 &current_tangent)
{
  if (last_tangent.is_zero() || current_tangent.is_zero()) {
    return last_normal;
  }
  const float angle = angle_normalized_v3v3(last_tangent, current_tangent);
  if (angle != 0.0) {
    const float3 axis = float3::cross(last_tangent, current_tangent).normalized();
    return rotate_direction_around_axis(last_normal, axis, angle);
  }
  else {
    return last_normal;
  }
}

static void calculate_normals_minimum(Span<float3> tangents,
                                      const bool cyclic,
                                      MutableSpan<float3> r_normals)
{
  BLI_assert(r_normals.size() == tangents.size());

  if (r_normals.is_empty()) {
    return;
  }

  const float epsilon = 1e-4f;

  /* Set initial normal. */
  const float3 &first_tangent = tangents[0];
  if (fabs(first_tangent.x) + fabs(first_tangent.y) < epsilon) {
    r_normals[0] = {1.0f, 0.0f, 0.0f};
  }
  else {
    r_normals[0] = float3(first_tangent.y, -first_tangent.x, 0.0f).normalized();
  }

  /* Forward normal with minimum twist along the entire spline. */
  for (const int i : IndexRange(1, r_normals.size() - 1)) {
    r_normals[i] = calculate_next_normal(r_normals[i - 1], tangents[i - 1], tangents[i]);
  }

  if (!cyclic) {
    return;
  }

  /* Compute how much the first normal deviates from the normal that has been forwarded along the
   * entire cyclic spline. */
  const float3 uncorrected_last_normal = calculate_next_normal(
      r_normals.last(), tangents.last(), tangents[0]);
  float correction_angle = angle_signed_on_axis_v3v3_v3(
      r_normals[0], uncorrected_last_normal, tangents[0]);
  if (correction_angle > M_PI) {
    correction_angle = correction_angle - 2 * M_PI;
  }

  /* Gradually apply correction by rotating all normals slightly. */
  const float angle_step = correction_angle / r_normals.size();
  for (const int i : r_normals.index_range()) {
    const float angle = angle_step * i;
    r_normals[i] = rotate_direction_around_axis(r_normals[i], tangents[i], angle);
  }
}

/**
 * Return non-owning access to the direction vectors perpendicular to the tangents at every
 * evaluated point. The method used to generate the normal vectors depends on Spline.normal_mode.
 */
Span<float3> Spline::evaluated_normals() const
{
  if (!normal_cache_dirty_) {
    return evaluated_normals_cache_;
  }

  std::lock_guard lock{normal_cache_mutex_};
  if (!normal_cache_dirty_) {
    return evaluated_normals_cache_;
  }

  const int eval_size = this->evaluated_points_size();
  evaluated_normals_cache_.resize(eval_size);

  Span<float3> tangents = this->evaluated_tangents();
  MutableSpan<float3> normals = evaluated_normals_cache_;

  /* Only Z up normals are supported at the moment. */
  switch (this->normal_mode) {
    case ZUp: {
      calculate_normals_z_up(tangents, normals);
      break;
    }
    case Minimum: {
      calculate_normals_minimum(tangents, is_cyclic_, normals);
      break;
    }
    case Tangent: {
      /* Tangent mode is not yet supported. */
      calculate_normals_z_up(tangents, normals);
      break;
    }
  }

  /* Rotate the generated normals with the interpolated tilt data. */
  GVArray_Typed<float> tilts = this->interpolate_to_evaluated_points(this->tilts());
  for (const int i : normals.index_range()) {
    normals[i] = rotate_direction_around_axis(normals[i], tangents[i], tilts[i]);
  }

  normal_cache_dirty_ = false;
  return evaluated_normals_cache_;
}

Spline::LookupResult Spline::lookup_evaluated_factor(const float factor) const
{
  return this->lookup_evaluated_length(this->length() * factor);
}

/**
 * \note This does not support extrapolation currently.
 */
Spline::LookupResult Spline::lookup_evaluated_length(const float length) const
{
  BLI_assert(length >= 0.0f && length <= this->length());

  Span<float> lengths = this->evaluated_lengths();

  const float *offset = std::lower_bound(lengths.begin(), lengths.end(), length);
  const int index = offset - lengths.begin();
  const int next_index = (index == this->size() - 1) ? 0 : index + 1;

  const float previous_length = (index == 0) ? 0.0f : lengths[index - 1];
  const float factor = (length - previous_length) / (lengths[index] - previous_length);

  return LookupResult{index, next_index, factor};
}

/**
 * Return an array of evenly spaced samples along the length of the spline. The samples are indices
 * and factors to the next index encoded in floats. The logic for converting from the float values
 * to interpolation data is in #lookup_data_from_index_factor.
 */
Array<float> Spline::sample_uniform_index_factors(const int samples_size) const
{
  const Span<float> lengths = this->evaluated_lengths();

  BLI_assert(samples_size > 0);
  Array<float> samples(samples_size);

  samples[0] = 0.0f;
  if (samples_size == 1) {
    return samples;
  }

  const float total_length = this->length();
  const float sample_length = total_length / (samples_size - (is_cyclic_ ? 0 : 1));

  /* Store the length at the previous evaluated point in a variable so it can
   * start out at zero (the lengths array doesn't contain 0 for the first point). */
  float prev_length = 0.0f;
  int i_sample = 1;
  for (const int i_evaluated : IndexRange(this->evaluated_edges_size())) {
    const float length = lengths[i_evaluated];

    /* Add every sample that fits in this evaluated edge. */
    while ((sample_length * i_sample) < length && i_sample < samples_size) {
      const float factor = (sample_length * i_sample - prev_length) / (length - prev_length);
      samples[i_sample] = i_evaluated + factor;
      i_sample++;
    }

    prev_length = length;
  }

  if (!is_cyclic_) {
    /* In rare cases this can prevent overflow of the stored index. */
    samples.last() = lengths.size();
  }

  return samples;
}

Spline::LookupResult Spline::lookup_data_from_index_factor(const float index_factor) const
{
  const int points_len = this->evaluated_points_size();

  if (is_cyclic_) {
    if (index_factor < points_len) {
      const int index = std::floor(index_factor);
      const int next_index = (index < points_len - 1) ? index + 1 : 0;
      return LookupResult{index, next_index, index_factor - index};
    }
    return LookupResult{points_len - 1, 0, 1.0f};
  }

  if (index_factor < points_len - 1) {
    const int index = std::floor(index_factor);
    const int next_index = index + 1;
    return LookupResult{index, next_index, index_factor - index};
  }
  return LookupResult{points_len - 2, points_len - 1, 1.0f};
}

void Spline::bounds_min_max(float3 &min, float3 &max, const bool use_evaluated) const
{
  Span<float3> positions = use_evaluated ? this->evaluated_positions() : this->positions();
  for (const float3 &position : positions) {
    minmax_v3v3_v3(min, max, position);
  }
}

GVArrayPtr Spline::interpolate_to_evaluated_points(GSpan data) const
{
  return this->interpolate_to_evaluated_points(GVArray_For_GSpan(data));
}

/**
 * Sample any input data with a value for each evaluated point (already interpolated to evaluated
 * points) to arbitrary parameters in between the evaluated points. The interpolation is quite
 * simple, but this handles the cyclic and end point special cases.
 */
void Spline::sample_based_on_index_factors(const GVArray &src,
                                           Span<float> index_factors,
                                           GMutableSpan dst) const
{
  BLI_assert(src.size() == this->evaluated_points_size());

  blender::attribute_math::convert_to_static_type(src.type(), [&](auto dummy) {
    using T = decltype(dummy);
    const GVArray_Typed<T> src_typed = src.typed<T>();
    MutableSpan<T> dst_typed = dst.typed<T>();
    blender::threading::parallel_for(dst_typed.index_range(), 1024, [&](IndexRange range) {
      for (const int i : range) {
        const LookupResult interp = this->lookup_data_from_index_factor(index_factors[i]);
        dst_typed[i] = blender::attribute_math::mix2(interp.factor,
                                                     src_typed[interp.evaluated_index],
                                                     src_typed[interp.next_evaluated_index]);
      }
    });
  });
}

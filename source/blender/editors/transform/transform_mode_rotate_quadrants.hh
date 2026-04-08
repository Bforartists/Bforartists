/* SPDX-FileCopyrightText: 2026 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup edtransform
 *
 * Used to apply 90 degree rotations directly, without imprecision from floating point operations,
 * see #150900.
 */

#pragma once

#include <optional>

struct TransInfo;

namespace blender::ed::transform {

/**
 * Build a rotation matrix, using exact sin/cos when a quadrant index (0..3) is provided.
 * \param quadrant: If set, the exact quadrant (0=0, 1=90, 2=180, 3=270 degrees).
 */
void axis_angle_normalized_to_mat3_with_quadrant(float mat[3][3],
                                                 const float axis[3],
                                                 const float angle,
                                                 const std::optional<int> quadrant);

/**
 * Return the quadrant index (0..3) if the current rotation is a multiple of 90 degrees,
 * detected from either numeric input or snap increment. Returns #std::nullopt otherwise.
 * Reads #TransInfo.values_final which must be set before calling.
 *
 * \param is_large_rotation_limited: When true, the radian angle was clamped to avoid
 * excessively large values, breaking the correspondence between the input and actual angle.
 */
std::optional<int> transform_angle_to_quadrant_or_null(const TransInfo *t,
                                                       const bool is_large_rotation_limited);

}  // namespace blender::ed::transform

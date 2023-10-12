/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#pragma once

#include "BLI_math_matrix_types.hh"

#include "COM_context.hh"
#include "COM_domain.hh"
#include "COM_result.hh"

namespace blender::realtime_compositor {

/* Transforms the given result based on the given transformation and interpolation, writing the
 * transformed result to the given output.
 *
 * The rotation and scale components of the transformation are realized and the size of the result
 * is increased/reduced to adapt to the new transformation. For instance, if the transformation is
 * a rotation, the input will be rotated and expanded in size to account for the bounding box of
 * the input after rotation. The size of the returned result is bound and clipped by the maximum
 * possible GPU texture size to avoid allocations that surpass hardware limits, which is typically
 * 16k.
 *
 * The translation component of the transformation is delayed and only stored in the domain of the
 * result to be realized later when needed. */
void transform(Context &context,
               Result &input,
               Result &output,
               float3x3 transformation,
               Interpolation interpolation);

}  // namespace blender::realtime_compositor

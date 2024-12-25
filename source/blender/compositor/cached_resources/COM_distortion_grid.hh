/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#pragma once

#include <cstdint>
#include <memory>

#include "BLI_array.hh"
#include "BLI_map.hh"
#include "BLI_math_vector_types.hh"

#include "DNA_movieclip_types.h"

#include "COM_cached_resource.hh"
#include "COM_result.hh"

namespace blender::compositor {

class Context;

enum class DistortionType : uint8_t {
  Distort,
  Undistort,
};

/* ------------------------------------------------------------------------------------------------
 * Distortion Grid Key.
 */
class DistortionGridKey {
 public:
  MovieTrackingCamera camera;
  int2 size;
  DistortionType type;
  int2 calibration_size;

  DistortionGridKey(const MovieTrackingCamera &camera,
                    int2 size,
                    DistortionType type,
                    int2 calibration_size);

  uint64_t hash() const;
};

bool operator==(const DistortionGridKey &a, const DistortionGridKey &b);

/* -------------------------------------------------------------------------------------------------
 * Distortion Grid.
 *
 * A cached resource that computes and caches a result containing the normalized coordinates after
 * applying the camera distortion of a given movie clip tracking camera. See the constructor for
 * more information. */
class DistortionGrid : public CachedResource {
 private:
  Array<float2> distortion_grid_;

 public:
  Result result;

 public:
  /* The calibration size is the size of the image where the tracking camera was calibrated, this
   * is the size of the movie clip in most cases. */
  DistortionGrid(Context &context,
                 MovieClip *movie_clip,
                 int2 size,
                 DistortionType type,
                 int2 calibration_size);

  ~DistortionGrid();
};

/* ------------------------------------------------------------------------------------------------
 * Distortion Grid Container.
 */
class DistortionGridContainer : CachedResourceContainer {
 private:
  Map<DistortionGridKey, std::unique_ptr<DistortionGrid>> map_;

 public:
  void reset() override;

  /* Check if there is an available DistortionGrid cached resource with the given parameters in the
   * container, if one exists, return it, otherwise, return a newly created one and add it to the
   * container. In both cases, tag the cached resource as needed to keep it cached for the next
   * evaluation. */
  Result &get(
      Context &context, MovieClip *movie_clip, int2 size, DistortionType type, int frame_number);
};

}  // namespace blender::compositor

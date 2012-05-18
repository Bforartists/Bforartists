// Copyright (c) 2012 libmv authors.
//
// Permission is hereby granted, free of charge, to any person obtaining a copy
// of this software and associated documentation files (the "Software"), to
// deal in the Software without restriction, including without limitation the
// rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
// sell copies of the Software, and to permit persons to whom the Software is
// furnished to do so, subject to the following conditions:
//
// The above copyright notice and this permission notice shall be included in
// all copies or substantial portions of the Software.
//
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
// IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
// FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
// AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
// LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
// FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
// IN THE SOFTWARE.

#ifndef LIBMV_TRACKING_TRACK_REGION_H_

// Necessary for M_E when building with MSVC.
#define _USE_MATH_DEFINES

#include "libmv/tracking/esm_region_tracker.h"

#include "libmv/image/image.h"
#include "libmv/image/sample.h"
#include "libmv/numeric/numeric.h"

namespace libmv {

struct TrackRegionOptions {
  TrackRegionOptions();

  enum Mode {
    TRANSLATION,
    TRANSLATION_ROTATION,
    TRANSLATION_SCALE,
    TRANSLATION_ROTATION_SCALE,
    AFFINE,
    HOMOGRAPHY,
  };
  Mode mode;

  double minimum_correlation;
  int max_iterations;

  // Use the "Efficient Second-order Minimization" scheme. This increases
  // convergence speed at the cost of more per-iteration work.
  bool use_esm;

  // If true, apply a brute-force translation-only search before attempting the
  // full search. This is not enabled if the destination image ("image2") is
  // too small; in that case eithen the basin of attraction is close enough
  // that the nearby minima is correct, or the search area is too small.
  bool use_brute_initialization;

  // If true, normalize the image patches by their mean before doing the sum of
  // squared error calculation. This is reasonable since the effect of
  // increasing light intensity is multiplicative on the pixel intensities.
  //
  // Note: This does nearly double the solving time, so it is not advised to
  // turn this on all the time.
  bool use_normalized_intensities;

  // The size in pixels of the blur kernel used to both smooth the image and
  // take the image derivative.
  double sigma;

  // Extra points that should get transformed by the warp. This is useful
  // because the actual warp parameters are not exposed.
  int num_extra_points;

  // If non-null, this is used as the pattern mask. It should match the size of
  // image1, even though only values inside the image1 quad are examined. The
  // values must be in the range 0.0 to 0.1.
  FloatImage *image1_mask;
};

struct TrackRegionResult {
  enum Termination {
    // Ceres termination types, duplicated; though, not the int values.
    PARAMETER_TOLERANCE,
    FUNCTION_TOLERANCE,
    GRADIENT_TOLERANCE,
    NO_CONVERGENCE,
    DID_NOT_RUN,
    NUMERICAL_FAILURE,

    // Libmv specific errors.
    SOURCE_OUT_OF_BOUNDS,
    DESTINATION_OUT_OF_BOUNDS,
    FELL_OUT_OF_BOUNDS,
    INSUFFICIENT_CORRELATION,
    CONFIGURATION_ERROR,
  };
  Termination termination;

  int num_iterations;
  double correlation;

  // Final parameters?
  bool used_brute_translation_initialization;
};

// Always needs 4 correspondences.
void TrackRegion(const FloatImage &image1,
                 const FloatImage &image2,
                 const double *x1, const double *y1,
                 const TrackRegionOptions &options,
                 double *x2, double *y2,
                 TrackRegionResult *result);

}  // namespace libmv

#endif  // LIBMV_TRACKING_TRACK_REGION_H_

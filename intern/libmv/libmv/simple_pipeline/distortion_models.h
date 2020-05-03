// Copyright (c) 2014 libmv authors.
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

#ifndef LIBMV_SIMPLE_PIPELINE_DISTORTION_MODELS_H_
#define LIBMV_SIMPLE_PIPELINE_DISTORTION_MODELS_H_

#include <algorithm>

namespace libmv {

enum DistortionModelType {
  DISTORTION_MODEL_POLYNOMIAL,
  DISTORTION_MODEL_DIVISION,
  DISTORTION_MODEL_NUKE,
};

// Invert camera intrinsics on the image point to get normalized coordinates.
// This inverts the radial lens distortion to a point which is in image pixel
// coordinates to get normalized coordinates.
void InvertPolynomialDistortionModel(const double focal_length_x,
                                     const double focal_length_y,
                                     const double principal_point_x,
                                     const double principal_point_y,
                                     const double k1,
                                     const double k2,
                                     const double k3,
                                     const double p1,
                                     const double p2,
                                     const double image_x,
                                     const double image_y,
                                     double *normalized_x,
                                     double *normalized_y);

// Apply camera intrinsics to the normalized point to get image coordinates.
// This applies the radial lens distortion to a point which is in normalized
// camera coordinates (i.e. the principal point is at (0, 0)) to get image
// coordinates in pixels. Templated for use with autodifferentiation.
template <typename T>
inline void ApplyPolynomialDistortionModel(const T &focal_length_x,
                                           const T &focal_length_y,
                                           const T &principal_point_x,
                                           const T &principal_point_y,
                                           const T &k1,
                                           const T &k2,
                                           const T &k3,
                                           const T &p1,
                                           const T &p2,
                                           const T &normalized_x,
                                           const T &normalized_y,
                                           T *image_x,
                                           T *image_y) {
  T x = normalized_x;
  T y = normalized_y;

  // Apply distortion to the normalized points to get (xd, yd).
  T r2 = x*x + y*y;
  T r4 = r2 * r2;
  T r6 = r4 * r2;
  T r_coeff = (T(1) + k1*r2 + k2*r4 + k3*r6);
  T xd = x * r_coeff + T(2)*p1*x*y + p2*(r2 + T(2)*x*x);
  T yd = y * r_coeff + T(2)*p2*x*y + p1*(r2 + T(2)*y*y);

  // Apply focal length and principal point to get the final image coordinates.
  *image_x = focal_length_x * xd + principal_point_x;
  *image_y = focal_length_y * yd + principal_point_y;
}

// Invert camera intrinsics on the image point to get normalized coordinates.
// This inverts the radial lens distortion to a point which is in image pixel
// coordinates to get normalized coordinates.
//
// Uses division distortion model.
void InvertDivisionDistortionModel(const double focal_length_x,
                                   const double focal_length_y,
                                   const double principal_point_x,
                                   const double principal_point_y,
                                   const double k1,
                                   const double k2,
                                   const double image_x,
                                   const double image_y,
                                   double *normalized_x,
                                   double *normalized_y);

// Apply camera intrinsics to the normalized point to get image coordinates.
// This applies the radial lens distortion to a point which is in normalized
// camera coordinates (i.e. the principal point is at (0, 0)) to get image
// coordinates in pixels. Templated for use with autodifferentiation.
//
// Uses division distortion model.
template <typename T>
inline void ApplyDivisionDistortionModel(const T &focal_length_x,
                                         const T &focal_length_y,
                                         const T &principal_point_x,
                                         const T &principal_point_y,
                                         const T &k1,
                                         const T &k2,
                                         const T &normalized_x,
                                         const T &normalized_y,
                                         T *image_x,
                                         T *image_y) {

  T x = normalized_x;
  T y = normalized_y;
  T r2 = x*x + y*y;
  T r4 = r2 * r2;

  T xd = x / (T(1) + k1 * r2 + k2 * r4);
  T yd = y / (T(1) + k1 * r2 + k2 * r4);

  // Apply focal length and principal point to get the final image coordinates.
  *image_x = focal_length_x * xd + principal_point_x;
  *image_y = focal_length_y * yd + principal_point_y;
}

// Invert camera intrinsics on the image point to get normalized coordinates.
// This inverts the radial lens distortion to a point which is in image pixel
// coordinates to get normalized coordinates.
//
// Uses Nuke distortion model.
template <typename T>
void InvertNukeDistortionModel(const T &focal_length_x,
                               const T &focal_length_y,
                               const T &principal_point_x,
                               const T &principal_point_y,
                               const int image_width,
                               const int image_height,
                               const T &k1,
                               const T &k2,
                               const T &image_x,
                               const T &image_y,
                               T *normalized_x,
                               T *normalized_y) {
  // According to the documentation:
  //
  //   xu = xd / (1 + k0 * rd^2 + k1 * rd^4)
  //   yu = yd / (1 + k0 * rd^2 + k1 * rd^4)
  //
  // Legend:
  //   (xd, yd) are the distorted cartesian coordinates,
  //   (rd, phid) are the distorted polar coordinates,
  //   (xu, yu) are the undistorted cartesian coordinates,
  //   (ru, phiu) are the undistorted polar coordinates,
  //   the k-values are the distortion coefficients.
  //
  // The coordinate systems are relative to the distortion centre.

  const int max_image_size = std::max(image_width, image_height);
  const double max_half_image_size = max_image_size * 0.5;

  if (max_half_image_size == 0.0) {
    *normalized_x = image_x * max_half_image_size / focal_length_x;
    *normalized_y = image_y * max_half_image_size / focal_length_y;
    return;
  }

  const T xd = (image_x - principal_point_x) / max_half_image_size;
  const T yd = (image_y - principal_point_y) / max_half_image_size;

  T rd2 = xd*xd + yd*yd;
  T rd4 = rd2 * rd2;
  T r_coeff = T(1) / (T(1) + k1*rd2 + k2*rd4);
  T xu = xd * r_coeff;
  T yu = yd * r_coeff;

  *normalized_x = xu * max_half_image_size / focal_length_x;
  *normalized_y = yu * max_half_image_size / focal_length_y;
}

// Apply camera intrinsics to the normalized point to get image coordinates.
// This applies the radial lens distortion to a point which is in normalized
// camera coordinates (i.e. the principal point is at (0, 0)) to get image
// coordinates in pixels. Templated for use with autodifferentiation.
//
// Uses Nuke distortion model.
void ApplyNukeDistortionModel(const double focal_length_x,
                              const double focal_length_y,
                              const double principal_point_x,
                              const double principal_point_y,
                              const int image_width,
                              const int image_height,
                              const double k1,
                              const double k2,
                              const double normalized_x,
                              const double normalized_y,
                              double *image_x,
                              double *image_y);

}  // namespace libmv

#endif  // LIBMV_SIMPLE_PIPELINE_DISTORTION_MODELS_H_

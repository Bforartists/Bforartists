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
//
// Author: mierle@google.com (Keir Mierle)

// Necessary for M_E when building with MSVC.
#define _USE_MATH_DEFINES

#include "libmv/tracking/track_region.h"

#include <Eigen/SVD>
#include <Eigen/QR>
#include <iostream>
#include "ceres/ceres.h"
#include "libmv/logging/logging.h"
#include "libmv/image/image.h"
#include "libmv/image/sample.h"
#include "libmv/image/convolve.h"
#include "libmv/multiview/homography.h"
#include "libmv/numeric/numeric.h"

namespace libmv {

TrackRegionOptions::TrackRegionOptions()
    : mode(TRANSLATION),
      minimum_correlation(0),
      max_iterations(20),
      use_esm(true),
      use_brute_initialization(true),
      use_normalized_intensities(false),
      sigma(0.9),
      num_extra_points(0),
      image1_mask(NULL) {
}

namespace {

// TODO(keir): Consider adding padding.
template<typename T>
bool InBounds(const FloatImage &image,
              const T &x,
              const T &y) {
  return 0.0 <= x && x < image.Width() &&
         0.0 <= y && y < image.Height();
}

bool AllInBounds(const FloatImage &image,
                 const double *x,
                 const double *y) {
  for (int i = 0; i < 4; ++i) {
    if (!InBounds(image, x[i], y[i])) {
      return false;
    }
  }
  return true;
}

// Because C++03 doesn't support partial template specializations for
// functions, but at the same time member function specializations are not
// supported, the sample function must be inside a template-specialized class
// with a non-templated static member.

// The "AutoDiff::Sample()" function allows sampling an image at an x, y
// position such that if x and y are jets, then the derivative information is
// correctly propagated.

// Empty default template.
template<typename T>
struct AutoDiff {
  // Sample only the image when the coordinates are scalars.
  static T Sample(const FloatImage &image_and_gradient,
                  const T &x, const T &y) {
    return SampleLinear(image_and_gradient, y, x, 0);
  }

  static void SetScalarPart(double scalar, T *value) {
    *value = scalar;
  }
  static void ScaleDerivative(double scale_by, T *value) {
    // For double, there is no derivative to scale.
  }
};

// Sample the image and gradient when the coordinates are jets, applying the
// jacobian appropriately to propagate the derivatives from the coordinates.
template<>
template<typename T, int N>
struct AutoDiff<ceres::Jet<T, N> > {
  static ceres::Jet<T, N> Sample(const FloatImage &image_and_gradient,
                                 const ceres::Jet<T, N> &x,
                                 const ceres::Jet<T, N> &y) {
    // Sample the image and its derivatives in x and y. One way to think of
    // this is that the image is a scalar function with a single vector
    // argument, xy, of dimension 2. Call this s(xy).
    const T s    = SampleLinear(image_and_gradient, y.a, x.a, 0);
    const T dsdx = SampleLinear(image_and_gradient, y.a, x.a, 1);
    const T dsdy = SampleLinear(image_and_gradient, y.a, x.a, 2);

    // However, xy is itself a function of another variable ("z"); xy(z) =
    // [x(z), y(z)]^T. What this function needs to return is "s", but with the
    // derivative with respect to z attached to the jet. So combine the
    // derivative part of x and y's jets to form a Jacobian matrix between x, y
    // and z (i.e. dxy/dz).
    Eigen::Matrix<T, 2, N> dxydz;
    dxydz.row(0) = x.v.transpose();
    dxydz.row(1) = y.v.transpose();

    // Now apply the chain rule to obtain ds/dz. Combine the derivative with
    // the scalar part to obtain s with full derivative information.
    ceres::Jet<T, N> jet_s;
    jet_s.a = s;
    jet_s.v = Matrix<T, 1, 2>(dsdx, dsdy) * dxydz;
    return jet_s;
  }

  static void SetScalarPart(double scalar, ceres::Jet<T, N> *value) {
    value->a = scalar;
  }
  static void ScaleDerivative(double scale_by, ceres::Jet<T, N> *value) {
    value->v *= scale_by;
  }
};

template<typename Warp>
class BoundaryCheckingCallback : public ceres::IterationCallback {
 public:
  BoundaryCheckingCallback(const FloatImage& image2,
                           const Warp &warp,
                           const double *x1, const double *y1)
      : image2_(image2), warp_(warp), x1_(x1), y1_(y1) {}

  virtual ceres::CallbackReturnType operator()(
      const ceres::IterationSummary& summary) {
    // Warp the original 4 points with the current warp into image2.
    double x2[4];
    double y2[4];
    for (int i = 0; i < 4; ++i) {
      warp_.Forward(warp_.parameters, x1_[i], y1_[i], x2 + i, y2 + i);
    }
    // Enusre they are all in bounds.
    if (!AllInBounds(image2_, x2, y2)) {
      return ceres::SOLVER_ABORT;
    }
    return ceres::SOLVER_CONTINUE;
  }

 private:
  const FloatImage &image2_;
  const Warp &warp_;
  const double *x1_;
  const double *y1_;
};

template<typename Warp>
class WarpCostFunctor {
 public:
  WarpCostFunctor(const TrackRegionOptions &options,
                  const FloatImage &image_and_gradient1,
                  const FloatImage &image_and_gradient2,
                  const Mat3 &canonical_to_image1,
                  int num_samples_x,
                  int num_samples_y,
                  const Warp &warp)
      : options_(options),
        image_and_gradient1_(image_and_gradient1),       
        image_and_gradient2_(image_and_gradient2),       
        canonical_to_image1_(canonical_to_image1),
        num_samples_x_(num_samples_x),
        num_samples_y_(num_samples_y),
        warp_(warp) {}

  template<typename T>
  bool operator()(const T *warp_parameters, T *residuals) const {
    for (int i = 0; i < Warp::NUM_PARAMETERS; ++i) {
      VLOG(2) << "warp_parameters[" << i << "]: " << warp_parameters[i];
    }

    T src_mean = T(1.0);
    T dst_mean = T(1.0);
    if (options_.use_normalized_intensities) {
      ComputeNormalizingCoefficients(warp_parameters,
                                     &src_mean,
                                     &dst_mean);
    }

    int cursor = 0;
    for (int r = 0; r < num_samples_y_; ++r) {
      for (int c = 0; c < num_samples_x_; ++c) {
        // Compute the location of the source pixel (via homography).
        Vec3 image1_position = canonical_to_image1_ * Vec3(c, r, 1);
        image1_position /= image1_position(2);
        
        // Sample the mask early; if it's zero, this pixel has no effect. This
        // allows early bailout from the expensive sampling that happens below.
        double mask_value = 1.0;
        if (options_.image1_mask != NULL) {
          mask_value = AutoDiff<double>::Sample(*options_.image1_mask,
                                                image1_position[0],
                                                image1_position[1]);
          if (mask_value == 0.0) {
            residuals[cursor++] = T(0.0);
            continue;
          }
        }

        // Compute the location of the destination pixel.
        T image2_position[2];
        warp_.Forward(warp_parameters,
                      T(image1_position[0]),
                      T(image1_position[1]),
                      &image2_position[0],
                      &image2_position[1]);

        // Sample the destination, propagating derivatives.
        T dst_sample = AutoDiff<T>::Sample(image_and_gradient2_,
                                           image2_position[0],
                                           image2_position[1]);

        // Sample the source. This is made complicated by ESM mode.
        T src_sample;
        if (options_.use_esm) {
          // In ESM mode, the derivative of the source is also taken into
          // account. This changes the linearization in a way that causes
          // better convergence. Copy the derivative of the warp parameters
          // onto the jets for the image1 position. This is the ESM hack.
          T image1_position_x = image2_position[0];
          T image1_position_y = image2_position[1];
          AutoDiff<T>::SetScalarPart(image1_position[0], &image1_position_x);
          AutoDiff<T>::SetScalarPart(image1_position[1], &image1_position_y);
          src_sample = AutoDiff<T>::Sample(image_and_gradient1_,
                                           image1_position_x,
                                           image1_position_y);

          // The jacobians for these should be averaged. Due to the subtraction
          // below, flip the sign of the src derivative so that the effect
          // after subtraction of the jets is that they are averaged.
          AutoDiff<T>::ScaleDerivative(-0.5, &src_sample);
          AutoDiff<T>::ScaleDerivative(0.5, &dst_sample);
        } else {
          // This is the traditional, forward-mode KLT solution.
          src_sample = T(AutoDiff<double>::Sample(image_and_gradient1_,
                                                  image1_position[0],
                                                  image1_position[1]));
        }

        // Normalize the samples by the mean values of each signal. The typical
        // light model assumes multiplicative intensity changes with changing
        // light, so this is a reasonable choice. Note that dst_mean has
        // derivative information attached thanks to autodiff.
        if (options_.use_normalized_intensities) {
          src_sample /= src_mean;
          dst_sample /= dst_mean;
        }

        // The difference is the error.
        T error = src_sample - dst_sample;

        // Weight the error by the mask, if one is present.
        if (options_.image1_mask != NULL) {
          error *= T(AutoDiff<double>::Sample(*options_.image1_mask,
                                              image1_position[0],
                                              image1_position[1]));
        }
        residuals[cursor++] = error;
      }
    }
    return true;
  }

  // For normalized matching, the average and 
  template<typename T>
  void ComputeNormalizingCoefficients(const T *warp_parameters,
                                      T *src_mean,
                                      T *dst_mean) const {

    *src_mean = T(0.0);
    *dst_mean = T(0.0);
    double num_samples = 0.0;
    for (int r = 0; r < num_samples_y_; ++r) {
      for (int c = 0; c < num_samples_x_; ++c) {
        // Compute the location of the source pixel (via homography).
        Vec3 image1_position = canonical_to_image1_ * Vec3(c, r, 1);
        image1_position /= image1_position(2);
        
        // Sample the mask early; if it's zero, this pixel has no effect. This
        // allows early bailout from the expensive sampling that happens below.
        double mask_value = 1.0;
        if (options_.image1_mask != NULL) {
          mask_value = AutoDiff<double>::Sample(*options_.image1_mask,
                                                image1_position[0],
                                                image1_position[1]);
          if (mask_value == 0.0) {
            continue;
          }
        }

        // Compute the location of the destination pixel.
        T image2_position[2];
        warp_.Forward(warp_parameters,
                      T(image1_position[0]),
                      T(image1_position[1]),
                      &image2_position[0],
                      &image2_position[1]);


        // Sample the destination, propagating derivatives.
        // TODO(keir): This accumulation can, surprisingly, be done as a
        // pre-pass by using integral images. This is complicated by the need
        // to store the jets in the integral image, but it is possible.
        T dst_sample = AutoDiff<T>::Sample(image_and_gradient2_,
                                           image2_position[0],
                                           image2_position[1]);

        // Sample the source.
        // TODO(keir): There is no reason to do this inside the loop;
        // precompute this and reuse it.
        T src_sample = T(AutoDiff<double>::Sample(image_and_gradient1_,
                                                  image1_position[0],
                                                  image1_position[1]));

        // Weight the sample by the mask, if one is present.
        if (options_.image1_mask != NULL) {
          src_sample *= T(mask_value);
          dst_sample *= T(mask_value);
        }

        *src_mean += src_sample;
        *dst_mean += dst_sample;
        num_samples += mask_value;
      }
    }
    *src_mean /= T(num_samples);
    *dst_mean /= T(num_samples);
    std::cout << "Normalization for src:\n" << *src_mean << "\n";
    std::cout << "Normalization for dst:\n" << *dst_mean << "\n";
  }

 // TODO(keir): Consider also computing the cost here.
 double PearsonProductMomentCorrelationCoefficient(
     const double *warp_parameters) const {
   for (int i = 0; i < Warp::NUM_PARAMETERS; ++i) {
     VLOG(2) << "Correlation warp_parameters[" << i << "]: "
             << warp_parameters[i];
   }

   // The single-pass PMCC computation is somewhat numerically unstable, but
   // it's sufficient for the tracker.
   double sX = 0, sY = 0, sXX = 0, sYY = 0, sXY = 0;

   // Due to masking, it's important to account for fractional samples.
   // Samples with a 50% mask get counted as a half sample.
   double num_samples = 0;

   for (int r = 0; r < num_samples_y_; ++r) {
     for (int c = 0; c < num_samples_x_; ++c) {
        // Compute the location of the source pixel (via homography).
        // TODO(keir): Cache these projections.
        Vec3 image1_position = canonical_to_image1_ * Vec3(c, r, 1);
        image1_position /= image1_position(2);
        
        // Compute the location of the destination pixel.
        double image2_position[2];
        warp_.Forward(warp_parameters,
                      image1_position[0],
                      image1_position[1],
                      &image2_position[0],
                      &image2_position[1]);

        double x = AutoDiff<double>::Sample(image_and_gradient2_,
                                            image2_position[0],
                                            image2_position[1]);

        double y = AutoDiff<double>::Sample(image_and_gradient1_,
                                            image1_position[0],
                                            image1_position[1]);

        // Weight the signals by the mask, if one is present.
        if (options_.image1_mask != NULL) {
          double mask_value = AutoDiff<double>::Sample(*options_.image1_mask,
                                                       image1_position[0],
                                                       image1_position[1]);
          x *= mask_value;
          y *= mask_value;
          num_samples += mask_value;
        } else {
          num_samples++;
        }
        sX += x;
        sY += y;
        sXX += x*x;
        sYY += y*y;
        sXY += x*y;
      }
    }
    // Normalize.
    sX /= num_samples;
    sY /= num_samples;
    sXX /= num_samples;
    sYY /= num_samples;
    sXY /= num_samples;

    double var_x = sXX - sX*sX;
    double var_y = sYY - sY*sY;
    double covariance_xy = sXY - sX*sY;

    double correlation = covariance_xy / sqrt(var_x * var_y);
    LG << "Covariance xy: " << covariance_xy
       << ", var 1: " << var_x << ", var 2: " << var_y
       << ", correlation: " << correlation;
    return correlation;
  }

 private:
  const TrackRegionOptions &options_;
  const FloatImage &image_and_gradient1_;
  const FloatImage &image_and_gradient2_;
  const Mat3 &canonical_to_image1_;
  int num_samples_x_;
  int num_samples_y_;
  const Warp &warp_;
};

// Compute the warp from rectangular coordinates, where one corner is the
// origin, and the opposite corner is at (num_samples_x, num_samples_y).
Mat3 ComputeCanonicalHomography(const double *x1,
                                const double *y1,
                                int num_samples_x,
                                int num_samples_y) {
  Mat canonical(2, 4);
  canonical << 0, num_samples_x, num_samples_x, 0,
               0, 0,             num_samples_y, num_samples_y;

  Mat xy1(2, 4);
  xy1 << x1[0], x1[1], x1[2], x1[3],
         y1[0], y1[1], y1[2], y1[3];

  Mat3 H;
  if (!Homography2DFromCorrespondencesLinear(canonical, xy1, &H, 1e-12)) {
    LG << "Couldn't construct homography.";
  }
  return H;
}

class Quad {
 public:
  Quad(const double *x, const double *y) : x_(x), y_(y) {
    // Compute the centroid and store it.
    centroid_ = Vec2(0.0, 0.0);
    for (int i = 0; i < 4; ++i) {
      centroid_ += Vec2(x_[i], y_[i]);
    }
    centroid_ /= 4.0;
  }

  // The centroid of the four points representing the quad.
  const Vec2& Centroid() const {
    return centroid_;
  }

  // The average magnitude of the four points relative to the centroid.
  double Scale() const {
    double scale = 0.0;
    for (int i = 0; i < 4; ++i) {
      scale += (Vec2(x_[i], y_[i]) - Centroid()).norm();
    }
    return scale / 4.0;
  }

  Vec2 CornerRelativeToCentroid(int i) const {
    return Vec2(x_[i], y_[i]) - centroid_;
  }

 private:
  const double *x_;
  const double *y_;
  Vec2 centroid_;
};

struct TranslationWarp {
  TranslationWarp(const double *x1, const double *y1,
                  const double *x2, const double *y2) {
    Vec2 t = Quad(x2, y2).Centroid() - Quad(x1, y1).Centroid();
    parameters[0] = t[0];
    parameters[1] = t[1];
  }

  template<typename T>
  void Forward(const T *warp_parameters,
               const T &x1, const T& y1, T *x2, T* y2) const {
    *x2 = x1 + warp_parameters[0];
    *y2 = y1 + warp_parameters[1];
  }

  // Translation x, translation y.
  enum { NUM_PARAMETERS = 2 };
  double parameters[NUM_PARAMETERS];
};

struct TranslationScaleWarp {
  TranslationScaleWarp(const double *x1, const double *y1,
                       const double *x2, const double *y2)
      : q1(x1, y1) {
    Quad q2(x2, y2);

    // The difference in centroids is the best guess for translation.
    Vec2 t = q2.Centroid() - q1.Centroid();
    parameters[0] = t[0];
    parameters[1] = t[1];

    // The difference in scales is the estimate for the scale.
    parameters[2] = 1.0 - q2.Scale() / q1.Scale();
  }

  // The strange way of parameterizing the translation and scaling is to make
  // the knobs that the optimizer sees easy to adjust. This is less important
  // for the scaling case than the rotation case.
  template<typename T>
  void Forward(const T *warp_parameters,
               const T &x1, const T& y1, T *x2, T* y2) const {
    // Make the centroid of Q1 the origin.
    const T x1_origin = x1 - q1.Centroid()(0);
    const T y1_origin = y1 - q1.Centroid()(1);

    // Scale uniformly about the origin.
    const T scale = 1.0 + warp_parameters[2];
    const T x1_origin_scaled = scale * x1_origin;
    const T y1_origin_scaled = scale * y1_origin;

    // Translate back into the space of Q1 (but scaled).
    const T x1_scaled = x1_origin_scaled + q1.Centroid()(0);
    const T y1_scaled = y1_origin_scaled + q1.Centroid()(1);

    // Translate into the space of Q2.
    *x2 = x1_scaled + warp_parameters[0];
    *y2 = y1_scaled + warp_parameters[1];
  }

  // Translation x, translation y, scale.
  enum { NUM_PARAMETERS = 3 };
  double parameters[NUM_PARAMETERS];

  Quad q1;
};

// Assumes the given points are already zero-centroid and the same size.
Mat2 OrthogonalProcrustes(const Mat2 &correlation_matrix) {
  Eigen::JacobiSVD<Mat2> svd(correlation_matrix,
                             Eigen::ComputeFullU | Eigen::ComputeFullV);
  return svd.matrixV() * svd.matrixU().transpose();
}

struct TranslationRotationWarp {
  TranslationRotationWarp(const double *x1, const double *y1,
                          const double *x2, const double *y2)
      : q1(x1, y1) {
    Quad q2(x2, y2);

    // The difference in centroids is the best guess for translation.
    Vec2 t = q2.Centroid() - q1.Centroid();
    parameters[0] = t[0];
    parameters[1] = t[1];

    // Obtain the rotation via orthorgonal procrustes.
    Mat2 correlation_matrix;
    for (int i = 0; i < 4; ++i) {
      correlation_matrix += q1.CornerRelativeToCentroid(i) * 
                            q2.CornerRelativeToCentroid(i).transpose();
    }
    Mat2 R = OrthogonalProcrustes(correlation_matrix);
    parameters[2] = atan2(R(1, 0), R(0, 0));

    std::cout << "correlation_matrix:\n" << correlation_matrix << "\n";
    std::cout << "R:\n" << R << "\n";
    std::cout << "theta:" << parameters[2] << "\n";
  }

  // The strange way of parameterizing the translation and rotation is to make
  // the knobs that the optimizer sees easy to adjust. The reason is that while
  // it is always the case that it is possible to express composed rotations
  // and translations as a single translation and rotation, the numerical
  // values needed for the composition are often large in magnitude. This is
  // enough to throw off any minimizer, since it must do the equivalent of
  // compose rotations and translations.
  //
  // Instead, use the parameterization below that offers a parameterization
  // that exposes the degrees of freedom in a way amenable to optimization.
  template<typename T>
  void Forward(const T *warp_parameters,
                      const T &x1, const T& y1, T *x2, T* y2) const {
    // Make the centroid of Q1 the origin.
    const T x1_origin = x1 - q1.Centroid()(0);
    const T y1_origin = y1 - q1.Centroid()(1);

    // Rotate about the origin (i.e. centroid of Q1).
    const T theta = warp_parameters[2];
    const T costheta = cos(theta);
    const T sintheta = sin(theta);
    const T x1_origin_rotated = costheta * x1_origin - sintheta * y1_origin;
    const T y1_origin_rotated = sintheta * x1_origin + costheta * y1_origin;

    // Translate back into the space of Q1 (but scaled).
    const T x1_rotated = x1_origin_rotated + q1.Centroid()(0);
    const T y1_rotated = y1_origin_rotated + q1.Centroid()(1);

    // Translate into the space of Q2.
    *x2 = x1_rotated + warp_parameters[0];
    *y2 = y1_rotated + warp_parameters[1];
  }

  // Translation x, translation y, rotation about the center of Q1 degrees.
  enum { NUM_PARAMETERS = 3 };
  double parameters[NUM_PARAMETERS];

  Quad q1;
};

struct TranslationRotationScaleWarp {
  TranslationRotationScaleWarp(const double *x1, const double *y1,
                               const double *x2, const double *y2)
      : q1(x1, y1) {
    Quad q2(x2, y2);

    // The difference in centroids is the best guess for translation.
    Vec2 t = q2.Centroid() - q1.Centroid();
    parameters[0] = t[0];
    parameters[1] = t[1];

    // The difference in scales is the estimate for the scale.
    parameters[2] = 1.0 - q2.Scale() / q1.Scale();

    // Obtain the rotation via orthorgonal procrustes.
    Mat2 correlation_matrix;
    for (int i = 0; i < 4; ++i) {
      correlation_matrix += q1.CornerRelativeToCentroid(i) * 
                            q2.CornerRelativeToCentroid(i).transpose();
    }
    std::cout << "correlation_matrix:\n" << correlation_matrix << "\n";
    Mat2 R = OrthogonalProcrustes(correlation_matrix);
    std::cout << "R:\n" << R << "\n";
    parameters[3] = atan2(R(1, 0), R(0, 0));
    std::cout << "theta:" << parameters[3] << "\n";
  }

  // The strange way of parameterizing the translation and rotation is to make
  // the knobs that the optimizer sees easy to adjust. The reason is that while
  // it is always the case that it is possible to express composed rotations
  // and translations as a single translation and rotation, the numerical
  // values needed for the composition are often large in magnitude. This is
  // enough to throw off any minimizer, since it must do the equivalent of
  // compose rotations and translations.
  //
  // Instead, use the parameterization below that offers a parameterization
  // that exposes the degrees of freedom in a way amenable to optimization.
  template<typename T>
  void Forward(const T *warp_parameters,
                      const T &x1, const T& y1, T *x2, T* y2) const {
    // Make the centroid of Q1 the origin.
    const T x1_origin = x1 - q1.Centroid()(0);
    const T y1_origin = y1 - q1.Centroid()(1);

    // Rotate about the origin (i.e. centroid of Q1).
    const T theta = warp_parameters[3];
    const T costheta = cos(theta);
    const T sintheta = sin(theta);
    const T x1_origin_rotated = costheta * x1_origin - sintheta * y1_origin;
    const T y1_origin_rotated = sintheta * x1_origin + costheta * y1_origin;

    // Scale uniformly about the origin.
    const T scale = 1.0 + warp_parameters[2];
    const T x1_origin_rotated_scaled = scale * x1_origin_rotated;
    const T y1_origin_rotated_scaled = scale * y1_origin_rotated;

    // Translate back into the space of Q1 (but scaled and rotated).
    const T x1_rotated_scaled = x1_origin_rotated_scaled + q1.Centroid()(0);
    const T y1_rotated_scaled = y1_origin_rotated_scaled + q1.Centroid()(1);

    // Translate into the space of Q2.
    *x2 = x1_rotated_scaled + warp_parameters[0];
    *y2 = y1_rotated_scaled + warp_parameters[1];
  }

  // Translation x, translation y, rotation about the center of Q1 degrees,
  // scale.
  enum { NUM_PARAMETERS = 4 };
  double parameters[NUM_PARAMETERS];

  Quad q1;
};

struct AffineWarp {
  AffineWarp(const double *x1, const double *y1,
             const double *x2, const double *y2)
      : q1(x1, y1) {
    Quad q2(x2, y2);

    // The difference in centroids is the best guess for translation.
    Vec2 t = q2.Centroid() - q1.Centroid();
    parameters[0] = t[0];
    parameters[1] = t[1];

    // Estimate the four affine parameters with the usual least squares.
    Mat Q1(8, 4);
    Vec Q2(8);
    for (int i = 0; i < 4; ++i) {
      Vec2 v1 = q1.CornerRelativeToCentroid(i);
      Vec2 v2 = q2.CornerRelativeToCentroid(i);

      Q1.row(2 * i + 0) << v1[0], v1[1],   0,     0  ;
      Q1.row(2 * i + 1) <<   0,     0,   v1[0], v1[1];

      Q2(2 * i + 0) = v2[0];
      Q2(2 * i + 1) = v2[1];
    }

    // TODO(keir): Check solution quality.
    Vec4 a = Q1.jacobiSvd(Eigen::ComputeThinU | Eigen::ComputeThinV).solve(Q2);
    parameters[2] = a[0];
    parameters[3] = a[1];
    parameters[4] = a[2];
    parameters[5] = a[3];

    std::cout << "a:" << a.transpose() << "\n";
    std::cout << "t:" << t.transpose() << "\n";
  }

  // See comments in other parameterizations about why the centroid is used.
  template<typename T>
  void Forward(const T *p, const T &x1, const T& y1, T *x2, T* y2) const {
    // Make the centroid of Q1 the origin.
    const T x1_origin = x1 - q1.Centroid()(0);
    const T y1_origin = y1 - q1.Centroid()(1);

    // Apply the affine transformation.
    const T x1_origin_affine = p[2] * x1_origin + p[3] * y1_origin;
    const T y1_origin_affine = p[4] * x1_origin + p[5] * y1_origin;

    // Translate back into the space of Q1 (but affine transformed).
    const T x1_affine = x1_origin_affine + q1.Centroid()(0);
    const T y1_affine = y1_origin_affine + q1.Centroid()(1);

    // Translate into the space of Q2.
    *x2 = x1_affine + p[0];
    *y2 = y1_affine + p[1];
  }

  // Translation x, translation y, rotation about the center of Q1 degrees,
  // scale.
  enum { NUM_PARAMETERS = 6 };
  double parameters[NUM_PARAMETERS];

  Quad q1;
};

struct HomographyWarp {
  HomographyWarp(const double *x1, const double *y1,
                 const double *x2, const double *y2) {
    Mat quad1(2, 4);
    quad1 << x1[0], x1[1], x1[2], x1[3],
             y1[0], y1[1], y1[2], y1[3];

    Mat quad2(2, 4);
    quad2 << x2[0], x2[1], x2[2], x2[3],
             y2[0], y2[1], y2[2], y2[3];

    Mat3 H;
    if (!Homography2DFromCorrespondencesLinear(quad1, quad2, &H, 1e-12)) {
      LG << "Couldn't construct homography.";
    }

    // Assume H(2, 2) != 0, and fix scale at H(2, 2) == 1.0.
    H /= H(2, 2);

    // Assume H is close to identity, so subtract out the diagonal.
    H(0, 0) -= 1.0;
    H(1, 1) -= 1.0;

    CHECK_NE(H(2, 2), 0.0) << H;
    for (int i = 0; i < 8; ++i) {
      parameters[i] = H(i / 3, i % 3);
      LG << "Parameters[" << i << "]: " << parameters[i];
    }
  }

  template<typename T>
  static void Forward(const T *p,
                      const T &x1, const T& y1, T *x2, T* y2) {
    // Homography warp with manual 3x3 matrix multiply.
    const T xx2 = (1.0 + p[0]) * x1 +     p[1]     * y1 + p[2];
    const T yy2 =     p[3]     * x1 + (1.0 + p[4]) * y1 + p[5];
    const T zz2 =     p[6]     * x1 +     p[7]     * y1 + 1.0;
    *x2 = xx2 / zz2;
    *y2 = yy2 / zz2;
  }

  enum { NUM_PARAMETERS = 8 };
  double parameters[NUM_PARAMETERS];
};

// Determine the number of samples to use for x and y. Quad winding goes:
//
//    0 1
//    3 2
//
// The idea is to take the maximum x or y distance. This may be oversampling.
// TODO(keir): Investigate the various choices; perhaps average is better?
void PickSampling(const double *x1, const double *y1,
                  const double *x2, const double *y2,
                  int *num_samples_x, int *num_samples_y) {
  Vec2 a0(x1[0], y1[0]);
  Vec2 a1(x1[1], y1[1]);
  Vec2 a2(x1[2], y1[2]);
  Vec2 a3(x1[3], y1[3]);

  Vec2 b0(x1[0], y1[0]);
  Vec2 b1(x1[1], y1[1]);
  Vec2 b2(x1[2], y1[2]);
  Vec2 b3(x1[3], y1[3]);

  double x_dimensions[4] = {
    (a1 - a0).norm(),
    (a3 - a2).norm(),
    (b1 - b0).norm(),
    (b3 - b2).norm()
  };

  double y_dimensions[4] = {
    (a3 - a0).norm(),
    (a1 - a2).norm(),
    (b3 - b0).norm(),
    (b1 - b2).norm()
  };
  const double kScaleFactor = 1.0;
  *num_samples_x = static_cast<int>(
      kScaleFactor * *std::max_element(x_dimensions, x_dimensions + 4));
  *num_samples_y = static_cast<int>(
      kScaleFactor * *std::max_element(y_dimensions, y_dimensions + 4));
  LG << "Automatic num_samples_x: " << *num_samples_x
     << ", num_samples_y: " << *num_samples_y;
}

bool SearchAreaTooBigForDescent(const FloatImage &image2,
                                const double *x2, const double *y2) {
  // TODO(keir): Check the bounds and enable only when it makes sense.
  return true;
}

bool PointOnRightHalfPlane(const Vec2 &a, const Vec2 &b, double x, double y) {
  Vec2 ba = b - a;
  return ((Vec2(x, y) - b).transpose() * Vec2(-ba.y(), ba.x())) > 0;
}

// Determine if a point is in a quad. The quad is arranged as:
//
//    +--> x
//    |
//    |  0 1
//    v  3 2
//    y
//
// The idea is to take the maximum x or y distance. This may be oversampling.
// TODO(keir): Investigate the various choices; perhaps average is better?
bool PointInQuad(const double *xs, const double *ys, double x, double y) {
  Vec2 a0(xs[0], ys[0]);
  Vec2 a1(xs[1], ys[1]);
  Vec2 a2(xs[2], ys[2]);
  Vec2 a3(xs[3], ys[3]);

  return PointOnRightHalfPlane(a0, a1, x, y) &&
         PointOnRightHalfPlane(a1, a2, x, y) &&
         PointOnRightHalfPlane(a2, a3, x, y) &&
         PointOnRightHalfPlane(a3, a0, x, y);
}

typedef Eigen::Array<float, Eigen::Dynamic, Eigen::Dynamic, Eigen::RowMajor> FloatArray;

// This creates a pattern in the frame of image2, from the pixel is image1,
// based on the initial guess represented by the two quads x1, y1, and x2, y2.
template<typename Warp>
void CreateBrutePattern(const double *x1, const double *y1,
                        const double *x2, const double *y2,
                        const FloatImage &image1,
                        const FloatImage *image1_mask,
                        FloatArray *pattern,
                        FloatArray *mask,
                        int *origin_x,
                        int *origin_y) {
  // Get integer bounding box of quad2 in image2.
  int min_x = static_cast<int>(floor(*std::min_element(x2, x2 + 4)));
  int min_y = static_cast<int>(floor(*std::min_element(y2, y2 + 4)));
  int max_x = static_cast<int>(ceil (*std::max_element(x2, x2 + 4)));
  int max_y = static_cast<int>(ceil (*std::max_element(y2, y2 + 4)));

  int w = max_x - min_x;
  int h = max_y - min_y;

  pattern->resize(h, w);
  mask->resize(h, w);

  Warp inverse_warp(x2, y2, x1, y1);

  // r,c are in the coordinate frame of image2.
  for (int r = min_y; r < max_y; ++r) {
    for (int c = min_x; c < max_x; ++c) {
      // i and j are in the coordinate frame of the pattern in image2.
      int i = r - min_y;
      int j = c - min_x;

      double dst_x = c;
      double dst_y = r;
      double src_x;
      double src_y;
      inverse_warp.Forward(inverse_warp.parameters,
                           dst_x, dst_y,
                           &src_x, &src_y);
      
      if (PointInQuad(x1, y1, src_x, src_y)) {
        (*pattern)(i, j) = SampleLinear(image1, src_y, src_x);
        (*mask)(i, j) = 1.0;
        if (image1_mask) {
          (*mask)(i, j) = SampleLinear(*image1_mask, src_y, src_x);;
        }
      } else {
        (*pattern)(i, j) = 0.0;
        (*mask)(i, j) = 0.0;
      }
    }
  }
  *origin_x = min_x;
  *origin_y = min_y;
}

template<typename Warp>
void BruteTranslationOnlyInitialize(const FloatImage &image1,
                                    const FloatImage *image1_mask,
                                    const FloatImage &image2,
                                    const int num_extra_points,
                                    const double *x1, const double *y1,
                                    double *x2, double *y2) {
  // Create the pattern to match in the space of image2, assuming our inital
  // guess isn't too far from the template in image1. If there is no image1
  // mask, then the resulting mask is binary.
  FloatArray pattern;
  FloatArray mask;
  int origin_x = -1, origin_y = -1;
  CreateBrutePattern<Warp>(x1, y1, x2, y2, image1, image1_mask,
                           &pattern, &mask, &origin_x, &origin_y);

  // Use Eigen on the images via maps for strong vectorization.
  Map<const FloatArray> search(image2.Data(), image2.Height(), image2.Width());

  // Try all possible locations inside the search area. Yes, everywhere.
  //
  // TODO(keir): There are a number of possible optimizations here. One choice
  // is to make a grid and only try one out of every N possible samples.
  // 
  // Another, slightly more clever idea, is to compute some sort of spatial
  // frequency distribution of the pattern patch. If the spatial resolution is
  // high (e.g. a grating pattern or fine lines) then checking every possible
  // translation is necessary, since a 1-pixel shift may induce a massive
  // change in the cost function. If the image is a blob or splotch with blurry
  // edges, then fewer samples are necessary since a few pixels offset won't
  // change the cost function much.
  double best_sad = std::numeric_limits<double>::max();
  int best_r = -1;
  int best_c = -1;
  int w = pattern.cols();
  int h = pattern.rows();
  for (int r = 0; r < (image2.Height() - h); ++r) {
    for (int c = 0; c < (image2.Width() - w); ++c) {
      // Compute the weighted sum of absolute differences, Eigen style.
      double sad = (mask * (pattern - search.block(r, c, h, w))).abs().sum();
      if (sad < best_sad) {
        best_r = r;
        best_c = c;
        best_sad = sad;
      }
    }
  }
  CHECK_NE(best_r, -1);
  CHECK_NE(best_c, -1);

  LG << "Brute force translation found a shift. "
     << "best_c: " << best_c << ", best_r: " << best_r << ", "
     << "origin_x: " << origin_x << ", origin_y: " << origin_y << ", "
     << "dc: " << (best_c - origin_x) << ", "
     << "dr: " << (best_r - origin_y)
     << ", tried " << ((image2.Height() - h) * (image2.Width() - w))
     << " shifts.";

  // Apply the shift.
  for (int i = 0; i < 4 + num_extra_points; ++i) {
    x2[i] += best_c - origin_x;
    y2[i] += best_r - origin_y;
  }
}

}  // namespace

template<typename Warp>
void TemplatedTrackRegion(const FloatImage &image1,
                          const FloatImage &image2,
                          const double *x1, const double *y1,
                          const TrackRegionOptions &options,
                          double *x2, double *y2,
                          TrackRegionResult *result) {
  for (int i = 0; i < 4; ++i) {
    LG << "P" << i << ": (" << x1[i] << ", " << y1[i] << "); guess ("
       << x2[i] << ", " << y2[i] << "); (dx, dy): (" << (x2[i] - x1[i]) << ", "
       << (y2[i] - y1[i]) << ").";
  }

  // Bail early if the points are already outside.
  if (!AllInBounds(image1, x1, y1)) {
    result->termination = TrackRegionResult::SOURCE_OUT_OF_BOUNDS;
    return;
  }
  if (!AllInBounds(image2, x2, y2)) {
    result->termination = TrackRegionResult::DESTINATION_OUT_OF_BOUNDS;
    return;
  }
  // TODO(keir): Check quads to ensure there is some area.

  // Prepare the image and gradient.
  Array3Df image_and_gradient1;
  Array3Df image_and_gradient2;
  BlurredImageAndDerivativesChannels(image1, options.sigma,
                                     &image_and_gradient1);
  BlurredImageAndDerivativesChannels(image2, options.sigma,
                                     &image_and_gradient2);

  // Possibly do a brute-force translation-only initialization.
  if (SearchAreaTooBigForDescent(image2, x2, y2) &&
      options.use_brute_initialization) {
    LG << "Running brute initialization...";
    BruteTranslationOnlyInitialize<Warp>(image_and_gradient1,
                                         options.image1_mask,
                                         image2,
                                         options.num_extra_points,
                                         x1, y1, x2, y2);
    for (int i = 0; i < 4; ++i) {
      LG << "P" << i << ": (" << x1[i] << ", " << y1[i] << "); brute ("
         << x2[i] << ", " << y2[i] << "); (dx, dy): (" << (x2[i] - x1[i]) << ", "
         << (y2[i] - y1[i]) << ").";
    }
  }

  // Prepare the initial warp parameters from the four correspondences.
  // Note: This must happen after the brute initialization runs.
  Warp warp(x1, y1, x2, y2);

  // Decide how many samples to use in the x and y dimensions.
  int num_samples_x;
  int num_samples_y;
  PickSampling(x1, y1, x2, y2, &num_samples_x, &num_samples_y);

  ceres::Solver::Options solver_options;
  solver_options.linear_solver_type = ceres::DENSE_QR;
  solver_options.max_num_iterations = options.max_iterations;
  solver_options.update_state_every_iteration = true;
  solver_options.parameter_tolerance = 1e-16;
  solver_options.function_tolerance = 1e-16;

  // TODO(keir): Consider removing these options before committing.
  solver_options.numeric_derivative_relative_step_size = 1e-3;
  solver_options.check_gradients = false;
  solver_options.gradient_check_relative_precision = 1e-10;
  solver_options.minimizer_progress_to_stdout = false;

  // Prevent the corners from going outside the destination image.
  BoundaryCheckingCallback<Warp> callback(image2, warp, x1, y1);
  solver_options.callbacks.push_back(&callback);

  // Compute the warp from rectangular coordinates.
  Mat3 canonical_homography = ComputeCanonicalHomography(x1, y1,
                                                         num_samples_x,
                                                         num_samples_y);

  // Construct the warp cost function. AutoDiffCostFunction takes ownership.
  WarpCostFunctor<Warp> *warp_cost_function =
      new WarpCostFunctor<Warp>(options,
                                image_and_gradient1,
                                image_and_gradient2,
                                canonical_homography,
                                num_samples_x,
                                num_samples_y,
                                warp);

  // Construct the problem with a single residual.
  ceres::Problem::Options problem_options;
  problem_options.cost_function_ownership = ceres::DO_NOT_TAKE_OWNERSHIP;
  ceres::Problem problem(problem_options);
  problem.AddResidualBlock(
      new ceres::AutoDiffCostFunction<
          WarpCostFunctor<Warp>,
          ceres::DYNAMIC,
          Warp::NUM_PARAMETERS>(warp_cost_function,
                                num_samples_x * num_samples_y),
      NULL,
      warp.parameters);

  ceres::Solver::Summary summary;
  ceres::Solve(solver_options, &problem, &summary);

  LG << "Summary:\n" << summary.FullReport();

  // Update the four points with the found solution; if the solver failed, then
  // the warp parameters are the identity (so ignore failure).
  //
  // Also warp any extra points on the end of the array.
  for (int i = 0; i < 4 + options.num_extra_points; ++i) {
    warp.Forward(warp.parameters, x1[i], y1[i], x2 + i, y2 + i);
    LG << "Warped point " << i << ": (" << x1[i] << ", " << y1[i] << ") -> ("
       << x2[i] << ", " << y2[i] << "); (dx, dy): (" << (x2[i] - x1[i]) << ", "
       << (y2[i] - y1[i]) << ").";
  }

  // TODO(keir): Update the result statistics.
  // TODO(keir): Add a normalize-cross-correlation variant.

  CHECK_NE(summary.termination_type, ceres::USER_ABORT) << "Libmv bug.";
  if (summary.termination_type == ceres::USER_ABORT) {
    result->termination = TrackRegionResult::FELL_OUT_OF_BOUNDS;
    return;
  }
#define HANDLE_TERMINATION(termination_enum) \
  if (summary.termination_type == ceres::termination_enum) { \
    result->termination = TrackRegionResult::termination_enum; \
    return; \
  }

  // Avoid computing correlation for tracking failures.
  HANDLE_TERMINATION(DID_NOT_RUN);
  HANDLE_TERMINATION(NUMERICAL_FAILURE);

  // Otherwise, run a final correlation check.
  if (options.minimum_correlation > 0.0) {
    result->correlation = warp_cost_function->
          PearsonProductMomentCorrelationCoefficient(warp.parameters);
    if (result->correlation < options.minimum_correlation) {
      LG << "Failing with insufficient correlation.";
      result->termination = TrackRegionResult::INSUFFICIENT_CORRELATION;
      return;
    }
  }

  HANDLE_TERMINATION(PARAMETER_TOLERANCE);
  HANDLE_TERMINATION(FUNCTION_TOLERANCE);
  HANDLE_TERMINATION(GRADIENT_TOLERANCE);
  HANDLE_TERMINATION(NO_CONVERGENCE);
#undef HANDLE_TERMINATION
};

void TrackRegion(const FloatImage &image1,
                 const FloatImage &image2,
                 const double *x1, const double *y1,
                 const TrackRegionOptions &options,
                 double *x2, double *y2,
                 TrackRegionResult *result) {
  // Enum is necessary due to templated nature of autodiff.
#define HANDLE_MODE(mode_enum, mode_type) \
  if (options.mode == TrackRegionOptions::mode_enum) { \
    TemplatedTrackRegion<mode_type>(image1, image2, \
                                    x1, y1, \
                                    options, \
                                    x2, y2, \
                                    result); \
    return; \
  }

  HANDLE_MODE(TRANSLATION,                TranslationWarp);
  HANDLE_MODE(TRANSLATION_SCALE,          TranslationScaleWarp);
  HANDLE_MODE(TRANSLATION_ROTATION,       TranslationRotationWarp);
  HANDLE_MODE(TRANSLATION_ROTATION_SCALE, TranslationRotationScaleWarp);
  HANDLE_MODE(AFFINE,                     AffineWarp);
  HANDLE_MODE(HOMOGRAPHY,                 HomographyWarp);
#undef HANDLE_MODE
}

}  // namespace libmv

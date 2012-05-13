// Copyright (c) 2007, 2008, 2009, 2011 libmv authors.
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

/* needed for M_E when building with msvc */
#define _USE_MATH_DEFINES

#include "libmv/tracking/esm_region_tracker.h"

#include "libmv/logging/logging.h"
#include "libmv/image/image.h"
#include "libmv/image/convolve.h"
#include "libmv/image/correlation.h"
#include "libmv/image/sample.h"
#include "libmv/numeric/numeric.h"
#include "libmv/tracking/track_region.h"

namespace libmv {

// TODO(keir): Reduce duplication between here and the other region trackers.
static bool RegionIsInBounds(const FloatImage &image1,
                      double x, double y,
                      int half_window_size) {
  // Check the minimum coordinates.
  int min_x = floor(x) - half_window_size - 1;
  int min_y = floor(y) - half_window_size - 1;
  if (min_x < 0.0 ||
      min_y < 0.0) {
    LG << "Out of bounds; min_x: " << min_x << ", min_y: " << min_y;
    return false;
  }

  // Check the maximum coordinates.
  int max_x = ceil(x) + half_window_size + 1;
  int max_y = ceil(y) + half_window_size + 1;
  if (max_x > image1.cols() ||
      max_y > image1.rows()) {
    LG << "Out of bounds; max_x: " << max_x << ", max_y: " << max_y
       << ", image1.cols(): " << image1.cols()
       << ", image1.rows(): " << image1.rows();
    return false;
  }

  // Ok, we're good.
  return true;
}

// This is implemented from "Lukas and Kanade 20 years on: Part 1. Page 42,
// figure 14: the Levenberg-Marquardt-Inverse Compositional Algorithm".
bool EsmRegionTracker::Track(const FloatImage &image1,
                             const FloatImage &image2,
                             double  x1, double  y1,
                             double *x2, double *y2) const {
  if (!RegionIsInBounds(image1, x1, y1, half_window_size)) {
    LG << "Fell out of image1's window with x1=" << x1 << ", y1=" << y1
       << ", hw=" << half_window_size << ".";
    return false;
  }
  
  // XXX
  // TODO(keir): Delete the block between the XXX's once the planar tracker is
  // integrated into blender.
  //
  // For now, to test, replace the ESM tracker with the Ceres tracker in
  // translation mode. In the future, this should get removed and alloed to
  // co-exist, since Ceres is not as fast as the ESM implementation since it
  // specializes for translation.
  double xx1[4], yy1[4];
  double xx2[4], yy2[4];
  // Clockwise winding, starting from the "origin" (top-left).
  xx1[0] = xx2[0] = x1 - half_window_size;
  yy1[0] = yy2[0] = y1 - half_window_size;

  xx1[1] = xx2[1] = x1 + half_window_size;
  yy1[1] = yy2[1] = y1 - half_window_size;

  xx1[2] = xx2[2] = x1 + half_window_size;
  yy1[2] = yy2[2] = y1 + half_window_size;

  xx1[3] = xx2[3] = x1 - half_window_size;
  yy1[3] = yy2[3] = y1 + half_window_size;

  TrackRegionOptions options;
  options.mode = TrackRegionOptions::TRANSLATION;
  options.num_samples_x = 2 * half_window_size + 1;
  options.num_samples_y = 2 * half_window_size + 1;
  options.max_iterations = 20;
  options.sigma = sigma;
  
  TrackRegionResult result;
  TrackRegion(image1, image2, xx1, yy1, options, xx2, yy2, &result);

  *x2 = xx2[0] + half_window_size;
  *y2 = yy2[0] + half_window_size;

  return true;

  // XXX
  int width = 2 * half_window_size + 1;

  // TODO(keir): Avoid recomputing gradients for e.g. the pyramid tracker.
  Array3Df image_and_gradient1;
  Array3Df image_and_gradient2;
  BlurredImageAndDerivativesChannels(image1, sigma, &image_and_gradient1);
  BlurredImageAndDerivativesChannels(image2, sigma, &image_and_gradient2);

  // Step -1: Resample the template (image1) since it is not pixel aligned.
  //
  // Take a sample of the gradient of the pattern area of image1 at the
  // subpixel position x1, x2. This is reused for each iteration, so
  // precomputing it saves time.
  Array3Df image_and_gradient1_sampled;
  SamplePattern(image_and_gradient1, x1, y1, half_window_size, 3,
                &image_and_gradient1_sampled);

  // Step 0: Initialize delta = 0.01.
  // 
  // Ignored for my "normal" LM loop.

  // Step 1: Warp I with W(x, p) to compute I(W(x; p).
  //
  // Use two images for accepting / rejecting updates.
  // XXX is this necessary?
  int current_image = 0, new_image = 1;
  Array3Df image_and_gradient2_sampled[2];
  SamplePattern(image_and_gradient2, *x2, *y2, half_window_size, 3,
                &image_and_gradient2_sampled[current_image]);

  // Step 2: Compute the squared error I - J.
  double error = 0;
  for (int r = 0; r < width; ++r) {
    for (int c = 0; c < width; ++c) {
      double e = image_and_gradient1_sampled(r, c, 0) -
                 image_and_gradient2_sampled[current_image](r, c, 0);
      error += e*e;
    }
  }

  // Step 3: Evaluate the gradient of the template.
  //
  // This is done above when sampling the template (step -1).

  // Step 4: Evaluate the jacobian dw/dp at (x; 0).
  //
  // The jacobian between dx,dy and the warp is constant 2x2 identity, so it
  // doesn't have to get computed. The Gauss-Newton Hessian matrix computation
  // below would normally have to include a multiply by the jacobian.

  // Step 5: Compute the steepest descent images of the template.
  //
  // Since the jacobian of the position w.r.t. the sampled template position is
  // the identity, the steepest descent images are the same as the gradient.

  // Step 6: Compute the Gauss-Newton Hessian for the template (image1).
  //
  // This could get rolled into the previous loop, but split it for now for
  // clarity.
  Mat2 H_image1 = Mat2::Zero();
  for (int r = 0; r < width; ++r) {
    for (int c = 0; c < width; ++c) {
      Vec2 g(image_and_gradient1_sampled(r, c, 1),
             image_and_gradient1_sampled(r, c, 2));
      H_image1 += g * g.transpose();
    }
  }

  double tau = 1e-4, eps1, eps2, eps3;
  eps1 = eps2 = eps3 = 1e-15;

  double mu = tau * std::max(H_image1(0, 0), H_image1(1, 1));
  double nu = M_E;

  int i;
  for (i = 0; i < max_iterations; ++i) {
    // Check that the entire image patch is within the bounds of the images.
    if (!RegionIsInBounds(image2, *x2, *y2, half_window_size)) {
      LG << "Fell out of image2's window with x2=" << *x2 << ", y2=" << *y2
         << ", hw=" << half_window_size << ".";
      return false;
    }

    Mat2 H = Mat2::Zero();
    for (int r = 0; r < width; ++r) {
      for (int c = 0; c < width; ++c) {
        Vec2 g1(image_and_gradient1_sampled(r, c, 1),
                image_and_gradient1_sampled(r, c, 2));
        Vec2 g2(image_and_gradient2_sampled[current_image](r, c, 1),
                image_and_gradient2_sampled[current_image](r, c, 2));
        Vec2 g = g1 + g2; // Should be / 2.0, but do that outside the loop.
        H += g * g.transpose();
      }
    }
    H /= 4.0;

    // Step 7: Compute z
    Vec2 z = Vec2::Zero();
    for (int r = 0; r < width; ++r) {
      for (int c = 0; c < width; ++c) {
        double e = image_and_gradient2_sampled[current_image](r, c, 0) -
                   image_and_gradient1_sampled(r, c, 0);
        z(0) += image_and_gradient1_sampled(r, c, 1) * e;
        z(1) += image_and_gradient1_sampled(r, c, 2) * e;
        z(0) += image_and_gradient2_sampled[current_image](r, c, 1) * e;
        z(1) += image_and_gradient2_sampled[current_image](r, c, 2) * e;
      }
    }
    z /= 2.0;

    // Step 8: Compute Hlm and (dx,dy)
    Mat2 diag  = H.diagonal().asDiagonal();
    diag *= mu;
    Mat2 Hlm = H + diag;
    Vec2 d = Hlm.lu().solve(z);

    // TODO(keir): Use the usual LM termination and update criterion instead of
    // this hacky version from the LK 20 years on paper.
    LG << "x=" << *x2 << ", y=" << *y2 << ", dx=" << d[0] << ", dy=" << d[1]
       << ", mu=" << mu << ", nu=" << nu;

    // Step 9: Update the warp; W(x; p) <-- W(x;p) compose W(x, dp)^-1
    double new_x2 = *x2 - d[0];
    double new_y2 = *y2 - d[1];

    // Step 9.1: Sample the image at the new position.
    SamplePattern(image_and_gradient2, new_x2, new_y2, half_window_size, 3,
                  &image_and_gradient2_sampled[new_image]);

    // Step 9.2: Compute the new error.
    // TODO(keir): Eliminate duplication with above code.
    double new_error = 0;
    for (int r = 0; r < width; ++r) {
      for (int c = 0; c < width; ++c) {
        double e = image_and_gradient1_sampled(r, c, 0) -
                   image_and_gradient2_sampled[new_image](r, c, 0);
        new_error += e*e;
      }
    }
    LG << "Old error: " << error << ", new error: " << new_error;

    double rho = (error - new_error) / (d.transpose() * (mu * d + z));

    // Step 10: Accept or reject step.
    if (rho <= 0) {
      // This was a bad step, so don't update.
      mu *= nu;

      // The standard Levenberg-Marquardt update multiplies nu by 2, but
      // instead chose e. I chose a constant greater than 2 since in typical
      // tracking examples, I saw that once updates started failing they should
      // ramp towards steepest descent faster. This has no basis in theory, but
      // appears to lead to faster tracking overall.
      nu *= M_E;
      LG << "Error increased, so reject update.";
    } else {
      // The step was good, so update.
      *x2 = new_x2;
      *y2 = new_y2;
      std::swap(new_image, current_image);
      error = new_error;

      mu *= std::max(1/3., 1 - pow(2*rho - 1, 3));
      nu = M_E;  // See above for why to use e.
      LG << "Error decreased, so accept update.";
    }

    // If the step was accepted, then check for termination.
    if (d.squaredNorm() < min_update_squared_distance) {
      // Compute the Pearson product-moment correlation coefficient to check
      // for sanity.
      double correlation = PearsonProductMomentCorrelation(image_and_gradient1_sampled,
                                                           image_and_gradient2_sampled[new_image],
                                                           width);
      LG << "Final correlation: " << correlation;

      // Note: Do the comparison here to handle nan's correctly (since all
      // comparisons with nan are false).
      if (minimum_correlation < correlation) {
        LG << "Successful track in " << (i + 1) << " iterations.";
        return true;
      }
      LG << "Correlation " << correlation << " greater than "
         << minimum_correlation << " or is nan; bailing.";
      return false;
    }
  }
  // Getting here means we hit max iterations, so tracking failed.
  LG << "Too many iterations; max is set to " << max_iterations << ".";
  return false;
}

}  // namespace libmv

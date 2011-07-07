// Copyright (c) 2011 libmv authors.
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

#include "libmv/base/vector.h"
#include "libmv/logging/logging.h"
#include "libmv/multiview/euclidean_resection.h"
#include "libmv/multiview/resection.h"
#include "libmv/multiview/projection.h"
#include "libmv/numeric/numeric.h"
#include "libmv/numeric/levenberg_marquardt.h"
#include "libmv/simple_pipeline/reconstruction.h"
#include "libmv/simple_pipeline/tracks.h"

namespace libmv {
namespace {

Mat2X PointMatrixFromMarkers(const vector<Marker> &markers) {
  Mat2X points(2, markers.size());
  for (int i = 0; i < markers.size(); ++i) {
    points(0, i) = markers[i].x;
    points(1, i) = markers[i].y;
  }
  return points;
}

Mat3 RotationFromEulerVector(Vec3 euler_vector) {
  double theta = euler_vector.norm();
  if (theta == 0.0) {
    return Mat3::Identity();
  }
  Vec3 w = euler_vector / theta;
  Mat3 w_hat = CrossProductMatrix(w);
  return Mat3::Identity() + w_hat*sin(theta) + w_hat*w_hat*(1 - cos(theta));
}

// Uses an incremental rotation:
//
//   x = R' * R * X + t;
//
// to avoid issues with the rotation representation. R' is derived from a
// euler vector encoding the rotation in 3 parameters; the direction is the
// axis to rotate around and the magnitude is the amount of the rotation.
struct ResectCostFunction {
 public:
  typedef Vec  FMatrixType;
  typedef Vec6 XMatrixType;

  ResectCostFunction(const vector<Marker> &markers,
                     const Reconstruction &reconstruction,
                     const Mat3 initial_R)
    : markers(markers),
      reconstruction(reconstruction),
      initial_R(initial_R) {}

  // dRt has dR (delta R) encoded as a euler vector in the first 3 parameters,
  // followed by t in the next 3 parameters.
  Vec operator()(const Vec6 &dRt) const {
    // Unpack R, t from dRt.
    Mat3 R = RotationFromEulerVector(dRt.head<3>()) * initial_R;
    Vec3 t = dRt.tail<3>();

    // Compute the reprojection error for each coordinate.
    Vec residuals(2 * markers.size());
    residuals.setZero();
    for (int i = 0; i < markers.size(); ++i) {
      const Point &point = *reconstruction.PointForTrack(markers[i].track);
      Vec3 projected = R * point.X + t;
      projected /= projected(2);
      residuals[2*i + 0] = projected(0) - markers[i].x;
      residuals[2*i + 1] = projected(1) - markers[i].y;
    }
    return residuals;
  }

  const vector<Marker> &markers;
  const Reconstruction &reconstruction;
  const Mat3 &initial_R;
};

}  // namespace

bool Resect(const vector<Marker> &markers, Reconstruction *reconstruction) {
  if (markers.size() < 5) {
    return false;
  }
  Mat2X points_2d = PointMatrixFromMarkers(markers);
  Mat3X points_3d(3, markers.size());
  for (int i = 0; i < markers.size(); i++) {
    points_3d.col(i) = reconstruction->PointForTrack(markers[i].track)->X;
  }
  LG << "Points for resect:\n" << points_2d;

  Mat3 R;
  Vec3 t;
  if (0 || !euclidean_resection::EuclideanResection(points_2d, points_3d, &R, &t)) {
    LG << "Resection for image " << markers[0].image << " failed;"
       << " trying fallback projective resection.";
    return false;
    // Euclidean resection failed. Fall back to projective resection, which is
    // less reliable but better conditioned when there are many points.
    Mat34 P;
    Mat4X points_3d_homogeneous(4, markers.size());
    for (int i = 0; i < markers.size(); i++) {
      points_3d_homogeneous.col(i).head<3>() = points_3d.col(i);
      points_3d_homogeneous(3, i) = 1.0;
    }
    resection::Resection(points_2d, points_3d_homogeneous, &P);
    if ((P * points_3d_homogeneous.col(0))(2) < 0) {
      LG << "Point behind camera; switch sign.";
      P = -P;
    }

    Mat3 ignored;
    KRt_From_P(P, &ignored, &R, &t);

    // The R matrix should be a rotation, but don't rely on it.
    Eigen::JacobiSVD<Mat3> svd(R, Eigen::ComputeFullU | Eigen::ComputeFullV);

    LG << "Resection rotation is: " << svd.singularValues().transpose();
    LG << "Determinant is: " << R.determinant();

    // Correct to make R a rotation.
    R = svd.matrixU() * svd.matrixV().transpose();

    Vec3 xx = R * points_3d.col(0) + t;
    if (xx(2) < 0.0) {
      LG << "Final point is still behind camera...";
    }
    // XXX Need to check if error is horrible and fail here too in that case.
  }

  // Refine the result.
  typedef LevenbergMarquardt<ResectCostFunction> Solver;

  // Give the cost our initial guess for R.
  ResectCostFunction resect_cost(markers, *reconstruction, R);

  // Encode the initial parameters: start with zero delta rotation, and the
  // guess for t obtained from resection.
  Vec6 dRt = Vec6::Zero();
  dRt.tail<3>() = t;

  Solver solver(resect_cost);

  Solver::SolverParameters params;
  Solver::Results results = solver.minimize(params, &dRt);
  LG << "LM found incremental rotation: " << dRt.head<3>().transpose();
  // TODO(keir): Check results to ensure clean termination.

  // Unpack the rotation and translation.
  R = RotationFromEulerVector(dRt.head<3>()) * R;
  t = dRt.tail<3>();

  LG << "Resection for image " << markers[0].image << " got:\n"
     << "R:\n" << R << "\nt:\n" << t;
  reconstruction->InsertCamera(markers[0].image, R, t);
  return true;
}

}  // namespace libmv

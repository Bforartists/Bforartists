/* SPDX-License-Identifier: GPL-2.0-or-later */

#pragma once

/** \file
 * \ingroup bli
 *
 * A `blender::math::AxisAngle<T>` represents a rotation around a unit axis.
 *
 * It is mainly useful for rotating a point around a given axis or quickly getting the rotation
 * between 2 vectors. It is cheaper to create than a #Quaternion or a matrix rotation.
 *
 * If the rotation axis is one of the basis axes (eg: {1,0,0}), then most operations are reduced to
 * 2D operations and are thus faster.
 *
 * Interpolation isn't possible between two `blender::math::AxisAngle<T>`; they must be
 * converted to other rotation types for that. Converting to `blender::math::Quaternion<T>` is the
 * fastest and more correct option.
 */

#include "BLI_math_angle_types.hh"
#include "BLI_math_base.hh"
#include "BLI_math_basis_types.hh"
#include "BLI_math_vector_types.hh"

namespace blender::math {

namespace detail {

/* Forward declaration for casting operators. */
template<typename T> struct Euler3;
template<typename T> struct EulerXYZ;
template<typename T> struct Quaternion;

template<typename T, typename AngleT> struct AxisAngle {
  using vec3_type = VecBase<T, 3>;

 private:
  /** Normalized direction around which we rotate anti-clockwise. */
  vec3_type axis_ = {0, 1, 0};
  AngleT angle_ = AngleT::identity();

 public:
  AxisAngle() = default;

  /**
   * Create a rotation from a basis axis and an angle.
   */
  AxisAngle(const AxisSigned axis, const AngleT &angle);

  /**
   * Create a rotation from an axis and an angle.
   * \note `axis` have to be normalized.
   */
  AxisAngle(const vec3_type &axis, const AngleT &angle);

  /**
   * Create a rotation from 2 normalized vectors.
   * \note `from` and `to` must be normalized.
   * \note Consider using `AxisAngleCartesian` for faster conversion to other rotation.
   */
  AxisAngle(const vec3_type &from, const vec3_type &to);

  /** Static functions. */

  static AxisAngle identity()
  {
    return {};
  }

  /** Methods. */

  const vec3_type &axis() const
  {
    return axis_;
  }

  const AngleT &angle() const
  {
    return angle_;
  }

  /** Operators. */

  friend bool operator==(const AxisAngle &a, const AxisAngle &b)
  {
    return (a.axis() == b.axis()) && (a.angle() == b.angle());
  }

  friend bool operator!=(const AxisAngle &a, const AxisAngle &b)
  {
    return (a != b);
  }

  friend std::ostream &operator<<(std::ostream &stream, const AxisAngle &rot)
  {
    return stream << "AxisAngle(axis=" << rot.axis() << ", angle=" << rot.angle() << ")";
  }
};

};  // namespace detail

using AxisAngle = math::detail::AxisAngle<float, detail::AngleRadian<float>>;
using AxisAngleCartesian = math::detail::AxisAngle<float, detail::AngleCartesian<float>>;

}  // namespace blender::math

/** \} */

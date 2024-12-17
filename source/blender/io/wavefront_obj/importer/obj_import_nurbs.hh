/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup obj
 */

#pragma once

#include "BKE_curve.hh"

#include "BLI_utility_mixins.hh"

#include "DNA_curve_types.h"

#include "obj_import_objects.hh"

namespace blender::io::obj {

/**
 * Make a Blender NURBS Curve block from a Geometry of GEOM_CURVE type.
 */
class CurveFromGeometry : NonMovable, NonCopyable {
 private:
  const Geometry &curve_geometry_;
  const GlobalVertices &global_vertices_;

 public:
  CurveFromGeometry(const Geometry &geometry, const GlobalVertices &global_vertices)
      : curve_geometry_(geometry), global_vertices_(global_vertices)
  {
  }

  Curve *create_curve(const OBJImportParams &import_params);

  Object *create_curve_object(Main *bmain, const OBJImportParams &import_params);

 private:
  /**
   * Create a NURBS spline for the Curve converted from Geometry.
   */
  void create_nurbs(Curve *curve, const OBJImportParams &import_params);

  short detect_knot_mode(const OBJImportParams &import_params,
                         int degree,
                         Span<int> indices,
                         Span<float> knots,
                         float2 range);
};
}  // namespace blender::io::obj

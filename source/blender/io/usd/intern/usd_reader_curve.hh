/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later
 * Adapted from the Blender Alembic importer implementation. Copyright 2016 Kévin Dietrich.
 * Modifications Copyright 2021 Tangent Animation. All rights reserved. */
#pragma once

#include "usd.hh"
#include "usd_reader_geom.hh"

#include <pxr/usd/usdGeom/basisCurves.h>

struct Curves;
namespace blender::bke {
struct GeometrySet;
class CurvesGeometry;
}  // namespace blender::bke

namespace blender::io::usd {

class USDCurvesReader : public USDGeomReader {
 protected:
  pxr::UsdGeomBasisCurves curve_prim_;

 public:
  USDCurvesReader(const pxr::UsdPrim &prim,
                  const USDImportParams &import_params,
                  const ImportSettings &settings)
      : USDGeomReader(prim, import_params, settings), curve_prim_(prim)
  {
  }

  bool valid() const override
  {
    return bool(curve_prim_);
  }

  void create_object(Main *bmain, double motionSampleTime) override;
  void read_object_data(Main *bmain, double motionSampleTime) override;

  void read_curve_sample(Curves *curves_id, double motionSampleTime);

  void read_geometry(bke::GeometrySet &geometry_set,
                     USDMeshReadParams params,
                     const char **r_err_str) override;

  void read_custom_data(bke::CurvesGeometry &curves, const double motionSampleTime) const;
};

}  // namespace blender::io::usd

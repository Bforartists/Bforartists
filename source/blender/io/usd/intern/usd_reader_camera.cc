/* SPDX-FileCopyrightText: 2021 Tangent Animation. All rights reserved.
 * SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later
 *
 * Adapted from the Blender Alembic importer implementation. */

#include "usd_reader_camera.h"

#include "DNA_camera_types.h"
#include "DNA_object_types.h"

#include "BLI_math_base.h"

#include "BKE_camera.h"
#include "BKE_object.hh"

#include <pxr/pxr.h>
#include <pxr/usd/usdGeom/camera.h>

namespace blender::io::usd {

void USDCameraReader::create_object(Main *bmain, const double /*motionSampleTime*/)
{
  Camera *bcam = static_cast<Camera *>(BKE_camera_add(bmain, name_.c_str()));

  object_ = BKE_object_add_only_object(bmain, OB_CAMERA, name_.c_str());
  object_->data = bcam;
}

void USDCameraReader::read_object_data(Main *bmain, const double motionSampleTime)
{
  Camera *bcam = (Camera *)object_->data;

  pxr::UsdGeomCamera cam_prim(prim_);

  if (!cam_prim) {
    return;
  }

  pxr::VtValue val;
  cam_prim.GetFocalLengthAttr().Get(&val, motionSampleTime);
  pxr::VtValue verApOffset;
  cam_prim.GetVerticalApertureOffsetAttr().Get(&verApOffset, motionSampleTime);
  pxr::VtValue horApOffset;
  cam_prim.GetHorizontalApertureOffsetAttr().Get(&horApOffset, motionSampleTime);
  pxr::VtValue clippingRangeVal;
  cam_prim.GetClippingRangeAttr().Get(&clippingRangeVal, motionSampleTime);
  pxr::VtValue focalDistanceVal;
  cam_prim.GetFocusDistanceAttr().Get(&focalDistanceVal, motionSampleTime);
  pxr::VtValue fstopVal;
  cam_prim.GetFStopAttr().Get(&fstopVal, motionSampleTime);
  pxr::VtValue projectionVal;
  cam_prim.GetProjectionAttr().Get(&projectionVal, motionSampleTime);
  pxr::VtValue verAp;
  cam_prim.GetVerticalApertureAttr().Get(&verAp, motionSampleTime);
  pxr::VtValue horAp;
  cam_prim.GetHorizontalApertureAttr().Get(&horAp, motionSampleTime);

  /*
   * For USD, these camera properties are in tenths of a world unit.
   * https://graphics.pixar.com/usd/release/api/class_usd_geom_camera.html#UsdGeom_CameraUnits
   *
   * tenth_unit_to_meters  = stage_meters_per_unit / 10
   * tenth_unit_to_millimeters = 1000 * unit_to_tenth_unit
   *                           = 100 * stage_meters_per_unit
   */
  const double tenth_unit_to_millimeters = 100.0 * settings_->stage_meters_per_unit;
  bcam->lens = val.Get<float>() * tenth_unit_to_millimeters;
  bcam->sensor_x = horAp.Get<float>() * tenth_unit_to_millimeters;
  bcam->sensor_y = verAp.Get<float>() * tenth_unit_to_millimeters;

  bcam->sensor_fit = bcam->sensor_x >= bcam->sensor_y ? CAMERA_SENSOR_FIT_HOR :
                                                        CAMERA_SENSOR_FIT_VERT;

  float sensor_size = bcam->sensor_x >= bcam->sensor_y ? bcam->sensor_x : bcam->sensor_y;
  bcam->shiftx = (horApOffset.Get<float>() * tenth_unit_to_millimeters) / sensor_size;
  bcam->shifty = (verApOffset.Get<float>() * tenth_unit_to_millimeters) / sensor_size;

  bcam->type = (projectionVal.Get<pxr::TfToken>().GetString() == "perspective") ? CAM_PERSP :
                                                                                  CAM_ORTHO;

  /* Call UncheckedGet() to silence compiler warnings.
   * Clamp to 1e-6 matching range defined in RNA. */
  bcam->clip_end = clippingRangeVal.UncheckedGet<pxr::GfVec2f>()[1];

  bcam->dof.focus_distance = focalDistanceVal.Get<float>();
  bcam->dof.aperture_fstop = float(fstopVal.Get<float>());

  if (bcam->type == CAM_ORTHO) {
    bcam->ortho_scale = max_ff(verAp.Get<float>(), horAp.Get<float>());
  }

  USDXformReader::read_object_data(bmain, motionSampleTime);
}

}  // namespace blender::io::usd

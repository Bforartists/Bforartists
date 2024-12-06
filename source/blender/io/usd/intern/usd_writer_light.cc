/* SPDX-FileCopyrightText: 2019 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */
#include "usd_writer_light.hh"
#include "usd_attribute_utils.hh"
#include "usd_hierarchy_iterator.hh"

#include <pxr/usd/usdLux/diskLight.h>
#include <pxr/usd/usdLux/distantLight.h>
#include <pxr/usd/usdLux/rectLight.h>
#include <pxr/usd/usdLux/shapingAPI.h>
#include <pxr/usd/usdLux/sphereLight.h>

#include "BLI_assert.h"
#include "BLI_math_rotation.h"

#include "DNA_light_types.h"

namespace blender::io::usd {

USDLightWriter::USDLightWriter(const USDExporterContext &ctx) : USDAbstractWriter(ctx) {}

bool USDLightWriter::is_supported(const HierarchyContext * /*context*/) const
{
  return true;
}

static void set_light_extents(const pxr::UsdPrim &prim,
                              const pxr::UsdTimeCode time,
                              pxr::UsdUtilsSparseValueWriter usd_value_writer)
{
  if (auto boundable = pxr::UsdGeomBoundable(prim)) {
    pxr::VtArray<pxr::GfVec3f> extent;
    pxr::UsdGeomBoundable::ComputeExtentFromPlugins(boundable, time, &extent);
    pxr::UsdAttribute attr_extent = boundable.CreateExtentAttr(pxr::VtValue(), true);

    set_attribute(attr_extent, extent, time, usd_value_writer);
  }

  /* We're intentionally not setting an error on non-boundable lights,
   * because overly noisy errors are annoying. */
}

void USDLightWriter::do_write(HierarchyContext &context)
{
  pxr::UsdStageRefPtr stage = usd_export_context_.stage;
  const pxr::SdfPath &usd_path = usd_export_context_.usd_path;
  pxr::UsdTimeCode timecode = get_export_time_code();

  const Light *light = static_cast<const Light *>(context.object->data);
  pxr::UsdLuxLightAPI usd_light_api;

  switch (light->type) {
    case LA_AREA: {
      switch (light->area_shape) {
        case LA_AREA_RECT: {
          pxr::UsdLuxRectLight rect_light = pxr::UsdLuxRectLight::Define(stage, usd_path);
          set_attribute(rect_light.CreateWidthAttr(pxr::VtValue(), true),
                        light->area_size,
                        timecode,
                        usd_value_writer_);
          set_attribute(rect_light.CreateHeightAttr(pxr::VtValue(), true),
                        light->area_sizey,
                        timecode,
                        usd_value_writer_);
          usd_light_api = rect_light.LightAPI();
          break;
        }
        case LA_AREA_SQUARE: {
          pxr::UsdLuxRectLight rect_light = pxr::UsdLuxRectLight::Define(stage, usd_path);
          set_attribute(rect_light.CreateWidthAttr(pxr::VtValue(), true),
                        light->area_size,
                        timecode,
                        usd_value_writer_);
          set_attribute(rect_light.CreateHeightAttr(pxr::VtValue(), true),
                        light->area_size,
                        timecode,
                        usd_value_writer_);
          usd_light_api = rect_light.LightAPI();
          break;
        }
        case LA_AREA_DISK: {
          pxr::UsdLuxDiskLight disk_light = pxr::UsdLuxDiskLight::Define(stage, usd_path);
          set_attribute(disk_light.CreateRadiusAttr(pxr::VtValue(), true),
                        light->area_size / 2.0f,
                        timecode,
                        usd_value_writer_);
          usd_light_api = disk_light.LightAPI();
          break;
        }
        case LA_AREA_ELLIPSE: {
          /* An ellipse light deteriorates into a disk light. */
          pxr::UsdLuxDiskLight disk_light = pxr::UsdLuxDiskLight::Define(stage, usd_path);
          set_attribute(disk_light.CreateRadiusAttr(pxr::VtValue(), true),
                        (light->area_size + light->area_sizey) / 4.0f,
                        timecode,
                        usd_value_writer_);
          usd_light_api = disk_light.LightAPI();
          break;
        }
      }
      break;
    }
    case LA_LOCAL:
    case LA_SPOT: {
      pxr::UsdLuxSphereLight sphere_light = pxr::UsdLuxSphereLight::Define(stage, usd_path);
      set_attribute(sphere_light.CreateRadiusAttr(pxr::VtValue(), true),
                    light->radius,
                    timecode,
                    usd_value_writer_);
      set_attribute(sphere_light.CreateTreatAsPointAttr(pxr::VtValue(), true),
                    light->radius == 0.0f,
                    timecode,
                    usd_value_writer_);

      if (light->type == LA_SPOT) {
        pxr::UsdLuxShapingAPI shaping_api = pxr::UsdLuxShapingAPI::Apply(sphere_light.GetPrim());
        if (shaping_api) {
          set_attribute(shaping_api.CreateShapingConeAngleAttr(pxr::VtValue(), true),
                        RAD2DEGF(light->spotsize) / 2.0f,
                        timecode,
                        usd_value_writer_);
          set_attribute(shaping_api.CreateShapingConeSoftnessAttr(pxr::VtValue(), true),
                        light->spotblend,
                        timecode,
                        usd_value_writer_);
        }
      }

      usd_light_api = sphere_light.LightAPI();
      break;
    }
    case LA_SUN: {
      pxr::UsdLuxDistantLight distant_light = pxr::UsdLuxDistantLight::Define(stage, usd_path);
      set_attribute(distant_light.CreateAngleAttr(pxr::VtValue(), true),
                    RAD2DEGF(light->sun_angle / 2.0f),
                    timecode,
                    usd_value_writer_);
      usd_light_api = distant_light.LightAPI();
      break;
    }
    default:
      BLI_assert_unreachable();
      break;
  }

  float intensity;
  if (light->type == LA_SUN) {
    /* Unclear why, but approximately matches Karma. */
    intensity = light->energy / 4.0f;
  }
  else {
    /* Convert from radiant flux to intensity. */
    intensity = light->energy / M_PI;
  }

  set_attribute(usd_light_api.CreateIntensityAttr(pxr::VtValue(), true),
                intensity,
                timecode,
                usd_value_writer_);
  set_attribute(
      usd_light_api.CreateExposureAttr(pxr::VtValue(), true), 0.0f, timecode, usd_value_writer_);
  set_attribute(usd_light_api.CreateColorAttr(pxr::VtValue(), true),
                pxr::GfVec3f(light->r, light->g, light->b),
                timecode,
                usd_value_writer_);
  set_attribute(usd_light_api.CreateDiffuseAttr(pxr::VtValue(), true),
                light->diff_fac,
                timecode,
                usd_value_writer_);
  set_attribute(usd_light_api.CreateSpecularAttr(pxr::VtValue(), true),
                light->spec_fac,
                timecode,
                usd_value_writer_);
  set_attribute(
      usd_light_api.CreateNormalizeAttr(pxr::VtValue(), true), true, timecode, usd_value_writer_);

  pxr::UsdPrim prim = usd_light_api.GetPrim();
  write_id_properties(prim, light->id, timecode);

  set_light_extents(prim, timecode, usd_value_writer_);
}

}  // namespace blender::io::usd

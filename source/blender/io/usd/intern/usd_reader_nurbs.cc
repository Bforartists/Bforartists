/* SPDX-FileCopyrightText: 2021 Tangent Animation. All rights reserved.
 * SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later
 *
 * Adapted from the Blender Alembic importer implementation. */

#include "usd_reader_nurbs.hh"

#include "BKE_curve.hh"
#include "BKE_geometry_set.hh"
#include "BKE_mesh.hh"
#include "BKE_object.hh"

#include "BLI_listbase.h"

#include "DNA_curve_types.h"
#include "DNA_object_types.h"

#include "MEM_guardedalloc.h"

#include <pxr/base/vt/types.h>

#include <pxr/usd/usdGeom/curves.h>

static bool set_knots(const pxr::VtDoubleArray &knots, float *&nu_knots)
{
  if (knots.empty()) {
    return false;
  }

  /* Skip first and last knots, as they are used for padding. */
  const size_t num_knots = knots.size();
  nu_knots = MEM_calloc_arrayN<float>(num_knots, __func__);

  for (size_t i = 0; i < num_knots; i++) {
    nu_knots[i] = float(knots[i]);
  }

  return true;
}

namespace blender::io::usd {

void USDNurbsReader::create_object(Main *bmain)
{
  Curve *cu = BKE_curve_add(bmain, name_.c_str(), OB_CURVES_LEGACY);

  cu->flag |= CU_3D;
  cu->actvert = CU_ACT_NONE;
  cu->resolu = 2;

  object_ = BKE_object_add_only_object(bmain, OB_CURVES_LEGACY, name_.c_str());
  object_->data = cu;
}

void USDNurbsReader::read_object_data(Main *bmain, const pxr::UsdTimeCode time)
{
  Curve *cu = (Curve *)object_->data;
  read_curve_sample(cu, time);

  if (curve_prim_.GetPointsAttr().ValueMightBeTimeVarying()) {
    add_cache_modifier();
  }

  USDXformReader::read_object_data(bmain, time);
}

void USDNurbsReader::read_curve_sample(Curve *cu, const pxr::UsdTimeCode time)
{
  pxr::UsdAttribute widthsAttr = curve_prim_.GetWidthsAttr();
  pxr::UsdAttribute vertexAttr = curve_prim_.GetCurveVertexCountsAttr();
  pxr::UsdAttribute pointsAttr = curve_prim_.GetPointsAttr();

  pxr::VtIntArray usdCounts;
  vertexAttr.Get(&usdCounts, time);

  pxr::VtVec3fArray usdPoints;
  pointsAttr.Get(&usdPoints, time);

  pxr::VtFloatArray usdWidths;
  widthsAttr.Get(&usdWidths, time);

  pxr::VtIntArray orders;
  curve_prim_.GetOrderAttr().Get(&orders, time);

  pxr::VtDoubleArray knots;
  curve_prim_.GetKnotsAttr().Get(&knots, time);

  pxr::VtVec3fArray usdNormals;
  curve_prim_.GetNormalsAttr().Get(&usdNormals, time);

  /* If normals, extrude, else bevel.
   * Perhaps to be replaced by Blender USD Schema. */
  if (!usdNormals.empty()) {
    /* Set extrusion to 1. */
    cu->extrude = 1.0f;
  }
  else {
    /* Set bevel depth to 1. */
    cu->bevel_radius = 1.0f;
  }

  size_t idx = 0;
  for (size_t i = 0; i < usdCounts.size(); i++) {
    const int num_verts = usdCounts[i];

    Nurb *nu = MEM_callocN<Nurb>(__func__);
    nu->flag = CU_SMOOTH;
    nu->type = CU_NURBS;

    nu->resolu = cu->resolu;
    nu->resolv = cu->resolv;

    nu->pntsu = num_verts;
    nu->pntsv = 1;

    if (i < orders.size()) {
      nu->orderu = short(orders[i]);
    }
    else {
      nu->orderu = 4;
      nu->orderv = 4;
    }

    /* TODO(makowalski): investigate setting Cyclic U and Endpoint U options. */
#if 0
    if (knots.size() > 3) {
      if ((knots[0] == knots[1]) && (knots[knots.size()] == knots[knots.size() - 1])) {
        nu->flagu |= CU_NURB_ENDPOINT;
      }
      else {
        nu->flagu |= CU_NURB_CYCLIC;
      }
    }
#endif

    float weight = 1.0f;

    nu->bp = MEM_calloc_arrayN<BPoint>(nu->pntsu, __func__);
    BPoint *bp = nu->bp;

    for (int j = 0; j < nu->pntsu; j++, bp++, idx++) {
      bp->vec[0] = usdPoints[idx][0];
      bp->vec[1] = usdPoints[idx][1];
      bp->vec[2] = usdPoints[idx][2];
      bp->vec[3] = weight;
      bp->f1 = SELECT;
      bp->weight = weight;

      float radius = 0.1f;
      if (idx < usdWidths.size()) {
        radius = usdWidths[idx] / 2.0f;
      }

      bp->radius = radius;
    }

    if (!set_knots(knots, nu->knotsu)) {
      BKE_nurb_knot_calc_u(nu);
    }

    BLI_addtail(BKE_curve_nurbs_get(cu), nu);
  }
}

void USDNurbsReader::read_geometry(bke::GeometrySet &geometry_set,
                                   const USDMeshReadParams params,
                                   const char **r_err_str)
{
  BLI_assert(geometry_set.has_mesh());
  Mesh *new_mesh = read_mesh(nullptr, params, r_err_str);
  geometry_set.replace_mesh(new_mesh);
}

Mesh *USDNurbsReader::read_mesh(Mesh * /*existing_mesh*/,
                                const USDMeshReadParams params,
                                const char ** /*r_err_str*/)
{
  pxr::UsdGeomCurves curve_prim(prim_);

  pxr::UsdAttribute widthsAttr = curve_prim.GetWidthsAttr();
  pxr::UsdAttribute vertexAttr = curve_prim.GetCurveVertexCountsAttr();
  pxr::UsdAttribute pointsAttr = curve_prim.GetPointsAttr();

  pxr::VtIntArray usdCounts;

  vertexAttr.Get(&usdCounts, params.motion_sample_time);
  int num_subcurves = usdCounts.size();

  pxr::VtVec3fArray usdPoints;
  pointsAttr.Get(&usdPoints, params.motion_sample_time);

  int vertex_idx = 0;
  int curve_idx;
  Curve *curve = static_cast<Curve *>(object_->data);

  const int curve_count = BLI_listbase_count(&curve->nurb);
  bool same_topology = curve_count == num_subcurves;

  if (same_topology) {
    Nurb *nurbs = static_cast<Nurb *>(curve->nurb.first);
    for (curve_idx = 0; nurbs; nurbs = nurbs->next, curve_idx++) {
      const int num_in_usd = usdCounts[curve_idx];
      const int num_in_blender = nurbs->pntsu;

      if (num_in_usd != num_in_blender) {
        same_topology = false;
        break;
      }
    }
  }

  if (!same_topology) {
    BKE_nurbList_free(&curve->nurb);
    read_curve_sample(curve, params.motion_sample_time);
  }
  else {
    Nurb *nurbs = static_cast<Nurb *>(curve->nurb.first);
    for (curve_idx = 0; nurbs; nurbs = nurbs->next, curve_idx++) {
      const int totpoint = usdCounts[curve_idx];

      if (nurbs->bp) {
        BPoint *point = nurbs->bp;

        for (int i = 0; i < totpoint; i++, point++, vertex_idx++) {
          point->vec[0] = usdPoints[vertex_idx][0];
          point->vec[1] = usdPoints[vertex_idx][1];
          point->vec[2] = usdPoints[vertex_idx][2];
        }
      }
      else if (nurbs->bezt) {
        BezTriple *bezier = nurbs->bezt;

        for (int i = 0; i < totpoint; i++, bezier++, vertex_idx++) {
          bezier->vec[1][0] = usdPoints[vertex_idx][0];
          bezier->vec[1][1] = usdPoints[vertex_idx][1];
          bezier->vec[1][2] = usdPoints[vertex_idx][2];
        }
      }
    }
  }

  return BKE_mesh_new_nomain_from_curve(object_);
}

}  // namespace blender::io::usd

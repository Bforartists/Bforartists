/* SPDX-FileCopyrightText: 2023 Blender Authors All rights reserved.
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#include <numeric>

#include <pxr/usd/usdGeom/basisCurves.h>
#include <pxr/usd/usdGeom/curves.h>
#include <pxr/usd/usdGeom/nurbsCurves.h>
#include <pxr/usd/usdGeom/tokens.h>
#include <pxr/usd/usdShade/material.h>
#include <pxr/usd/usdShade/materialBindingAPI.h>

#include "usd_hierarchy_iterator.hh"
#include "usd_writer_curves.hh"

#include "BLI_array_utils.hh"

#include "BKE_attribute.hh"
#include "BKE_curve_legacy_convert.hh"
#include "BKE_curves.hh"
#include "BKE_lib_id.hh"
#include "BKE_material.h"
#include "BKE_report.hh"

#include "BLT_translation.hh"

#include "RNA_access.hh"
#include "RNA_enum_types.hh"

namespace blender::io::usd {

pxr::UsdGeomBasisCurves USDCurvesWriter::DefineUsdGeomBasisCurves(pxr::VtValue curve_basis,
                                                                  const bool is_cyclic,
                                                                  const bool is_cubic) const
{
  pxr::UsdGeomBasisCurves basis_curves = pxr::UsdGeomBasisCurves::Define(
      usd_export_context_.stage, usd_export_context_.usd_path);
  /* Not required to set the basis attribute for linear curves
   * https://graphics.pixar.com/usd/dev/api/class_usd_geom_basis_curves.html#details */
  if (is_cubic) {
    basis_curves.CreateTypeAttr(pxr::VtValue(pxr::UsdGeomTokens->cubic));
    basis_curves.CreateBasisAttr(curve_basis);
  }
  else {
    basis_curves.CreateTypeAttr(pxr::VtValue(pxr::UsdGeomTokens->linear));
  }

  if (is_cyclic) {
    basis_curves.CreateWrapAttr(pxr::VtValue(pxr::UsdGeomTokens->periodic));
  }
  else if (curve_basis == pxr::VtValue(pxr::UsdGeomTokens->catmullRom)) {
    /* In Blender the first and last points are treated as endpoints. The pinned attribute tells
     * the client that to evaluate or render the curve, it must effectively add 'phantom
     * points' at the beginning and end of every curve in a batch. These phantom points are
     * injected to ensure that the interpolated curve begins at P[0] and ends at P[n-1]. */
    basis_curves.CreateWrapAttr(pxr::VtValue(pxr::UsdGeomTokens->pinned));
  }
  else {
    basis_curves.CreateWrapAttr(pxr::VtValue(pxr::UsdGeomTokens->nonperiodic));
  }

  return basis_curves;
}

static void populate_curve_widths(const bke::CurvesGeometry &curves, pxr::VtArray<float> &widths)
{
  const bke::AttributeAccessor curve_attributes = curves.attributes();
  const bke::AttributeReader<float> radii = curve_attributes.lookup<float>("radius",
                                                                           bke::AttrDomain::Point);

  widths.resize(radii.varray.size());

  for (const int i : radii.varray.index_range()) {
    widths[i] = radii.varray[i] * 2.0f;
  }
}

static pxr::TfToken get_curve_width_interpolation(const pxr::VtArray<float> &widths,
                                                  const pxr::VtArray<int> &segments,
                                                  const pxr::VtIntArray &control_point_counts,
                                                  const bool is_cyclic,
                                                  ReportList *reports)
{
  if (widths.empty()) {
    return pxr::TfToken();
  }

  const size_t accumulated_control_point_count = std::accumulate(
      control_point_counts.begin(), control_point_counts.end(), 0);

  /* For Blender curves, radii are always stored per point. For linear curves, this should match
   * with USD's vertex interpolation. For cubic curves, this should match with USD's varying
   * interpolation. */
  if (widths.size() == accumulated_control_point_count) {
    return pxr::UsdGeomTokens->vertex;
  }

  size_t expectedVaryingSize = std::accumulate(segments.begin(), segments.end(), 0);
  if (!is_cyclic) {
    expectedVaryingSize += control_point_counts.size();
  }

  if (widths.size() == expectedVaryingSize) {
    return pxr::UsdGeomTokens->varying;
  }

  BKE_report(reports, RPT_WARNING, "Curve width size not supported for USD interpolation");
  return pxr::TfToken();
}

static void populate_curve_verts(const bke::CurvesGeometry &curves,
                                 const Span<float3> positions,
                                 pxr::VtArray<pxr::GfVec3f> &verts,
                                 pxr::VtIntArray &control_point_counts,
                                 pxr::VtArray<int> &segments,
                                 const bool is_cyclic,
                                 const bool is_cubic)
{
  const OffsetIndices points_by_curve = curves.points_by_curve();
  for (const int i_curve : curves.curves_range()) {

    const IndexRange points = points_by_curve[i_curve];
    for (const int i_point : points) {
      verts.push_back(
          pxr::GfVec3f(positions[i_point][0], positions[i_point][1], positions[i_point][2]));
    }

    const int tot_points = points.size();
    control_point_counts[i_curve] = tot_points;

    /* For periodic linear curve, segment count = curveVertexCount.
     * For periodic cubic curve, segment count = curveVertexCount / vstep.
     * For nonperiodic linear curve, segment count = curveVertexCount - 1.
     * For nonperiodic cubic curve, segment count = ((curveVertexCount - 4) / vstep) + 1.
     * This function handles linear and Catmull-Rom curves. For Catmull-Rom, vstep is 1.
     * https://graphics.pixar.com/usd/dev/api/class_usd_geom_basis_curves.html */
    if (is_cyclic) {
      segments[i_curve] = tot_points;
    }
    else if (is_cubic) {
      segments[i_curve] = (tot_points - 4) + 1;
    }
    else {
      segments[i_curve] = tot_points - 1;
    }
  }
}

static void populate_curve_props(const bke::CurvesGeometry &curves,
                                 pxr::VtArray<pxr::GfVec3f> &verts,
                                 pxr::VtIntArray &control_point_counts,
                                 pxr::VtArray<float> &widths,
                                 pxr::TfToken &interpolation,
                                 const bool is_cyclic,
                                 const bool is_cubic,
                                 ReportList *reports)
{
  const int num_curves = curves.curve_num;
  const Span<float3> positions = curves.positions();

  pxr::VtArray<int> segments(num_curves);

  populate_curve_verts(
      curves, positions, verts, control_point_counts, segments, is_cyclic, is_cubic);

  populate_curve_widths(curves, widths);
  interpolation = get_curve_width_interpolation(
      widths, segments, control_point_counts, is_cyclic, reports);
}

static void populate_curve_verts_for_bezier(const bke::CurvesGeometry &curves,
                                            const Span<float3> positions,
                                            const Span<float3> handles_l,
                                            const Span<float3> handles_r,
                                            pxr::VtArray<pxr::GfVec3f> &verts,
                                            pxr::VtIntArray &control_point_counts,
                                            pxr::VtArray<int> &segments,
                                            const bool is_cyclic)
{
  const int bezier_vstep = 3;
  const OffsetIndices points_by_curve = curves.points_by_curve();

  for (const int i_curve : curves.curves_range()) {

    const IndexRange points = points_by_curve[i_curve];
    const int start_point_index = points[0];
    const int last_point_index = points[points.size() - 1];

    const int start_verts_count = verts.size();

    for (int i_point = start_point_index; i_point < last_point_index; i_point++) {

      /* The order verts in the USD bezier curve representation is [control point 0, right handle
       * 0, left handle 1, control point 1, right handle 1, left handle 2, control point 2, ...].
       * The last vert in the array doesn't need a right handle because the curve stops at that
       * point. */
      verts.push_back(
          pxr::GfVec3f(positions[i_point][0], positions[i_point][1], positions[i_point][2]));

      const blender::float3 right_handle = handles_r[i_point];
      verts.push_back(pxr::GfVec3f(right_handle[0], right_handle[1], right_handle[2]));

      const blender::float3 left_handle = handles_l[i_point + 1];
      verts.push_back(pxr::GfVec3f(left_handle[0], left_handle[1], left_handle[2]));
    }

    verts.push_back(pxr::GfVec3f(positions[last_point_index][0],
                                 positions[last_point_index][1],
                                 positions[last_point_index][2]));

    /* For USD periodic bezier curves, since the curve is closed, we need to include
     * the right handle of the last point and the left handle of the first point.
     */
    if (is_cyclic) {
      const blender::float3 right_handle = handles_r[last_point_index];
      verts.push_back(pxr::GfVec3f(right_handle[0], right_handle[1], right_handle[2]));

      const blender::float3 left_handle = handles_l[start_point_index];
      verts.push_back(pxr::GfVec3f(left_handle[0], left_handle[1], left_handle[2]));
    }

    const int tot_points = verts.size() - start_verts_count;
    control_point_counts[i_curve] = tot_points;

    if (is_cyclic) {
      segments[i_curve] = tot_points / bezier_vstep;
    }
    else {
      segments[i_curve] = ((tot_points - 4) / bezier_vstep) + 1;
    }
  }
}

static void populate_curve_props_for_bezier(const bke::CurvesGeometry &curves,
                                            pxr::VtArray<pxr::GfVec3f> &verts,
                                            pxr::VtIntArray &control_point_counts,
                                            pxr::VtArray<float> &widths,
                                            pxr::TfToken &interpolation,
                                            const bool is_cyclic,
                                            ReportList *reports)
{
  const int num_curves = curves.curve_num;

  const Span<float3> positions = curves.positions();
  const Span<float3> handles_l = curves.handle_positions_left();
  const Span<float3> handles_r = curves.handle_positions_right();

  pxr::VtArray<int> segments(num_curves);

  populate_curve_verts_for_bezier(
      curves, positions, handles_l, handles_r, verts, control_point_counts, segments, is_cyclic);

  populate_curve_widths(curves, widths);
  interpolation = get_curve_width_interpolation(
      widths, segments, control_point_counts, is_cyclic, reports);
}

static void populate_curve_props_for_nurbs(const bke::CurvesGeometry &curves,
                                           pxr::VtArray<pxr::GfVec3f> &verts,
                                           pxr::VtIntArray &control_point_counts,
                                           pxr::VtArray<float> &widths,
                                           pxr::VtArray<double> &knots,
                                           pxr::VtArray<int> &orders,
                                           pxr::TfToken &interpolation,
                                           const bool is_cyclic)
{
  /* Order and range, when representing a batched NurbsCurve should be authored one value per
   * curve. */
  const int num_curves = curves.curve_num;
  orders.resize(num_curves);

  const Span<float3> positions = curves.positions();

  VArray<int8_t> geom_orders = curves.nurbs_orders();
  VArray<int8_t> knots_modes = curves.nurbs_knots_modes();

  const OffsetIndices points_by_curve = curves.points_by_curve();
  for (const int i_curve : curves.curves_range()) {
    const IndexRange points = points_by_curve[i_curve];
    for (const int i_point : points) {
      verts.push_back(
          pxr::GfVec3f(positions[i_point][0], positions[i_point][1], positions[i_point][2]));
    }

    const int tot_points = points.size();
    control_point_counts[i_curve] = tot_points;

    const int8_t order = geom_orders[i_curve];
    orders[i_curve] = int(geom_orders[i_curve]);

    const KnotsMode mode = KnotsMode(knots_modes[i_curve]);

    const int knots_num = bke::curves::nurbs::knots_num(tot_points, order, is_cyclic);
    Array<float> temp_knots(knots_num);
    bke::curves::nurbs::calculate_knots(tot_points, mode, order, is_cyclic, temp_knots);

    /* Knots should be the concatenation of all batched curves.
     * https://graphics.pixar.com/usd/dev/api/class_usd_geom_nurbs_curves.html#details */
    for (int i_knot = 0; i_knot < knots_num; i_knot++) {
      knots.push_back(double(temp_knots[i_knot]));
    }

    /* For USD it is required to set specific end knots for periodic/non-periodic curves
     * https://graphics.pixar.com/usd/dev/api/class_usd_geom_nurbs_curves.html#details */
    int zeroth_knot_index = knots.size() - knots_num;
    if (is_cyclic) {
      knots[zeroth_knot_index] = knots[zeroth_knot_index + 1] -
                                 (knots[knots.size() - 2] - knots[knots.size() - 3]);
      knots[knots.size() - 1] = knots[knots.size() - 2] +
                                (knots[zeroth_knot_index + 2] - knots[zeroth_knot_index + 1]);
    }
    else {
      knots[zeroth_knot_index] = knots[zeroth_knot_index + 1];
      knots[knots.size() - 1] = knots[knots.size() - 2];
    }
  }

  populate_curve_widths(curves, widths);
  interpolation = pxr::UsdGeomTokens->vertex;
}

void USDCurvesWriter::set_writer_attributes_for_nurbs(
    const pxr::UsdGeomNurbsCurves &usd_nurbs_curves,
    const pxr::VtArray<double> &knots,
    const pxr::VtArray<int> &orders,
    const pxr::UsdTimeCode timecode)
{
  pxr::UsdAttribute attr_knots = usd_nurbs_curves.CreateKnotsAttr(pxr::VtValue(), true);
  usd_value_writer_.SetAttribute(attr_knots, pxr::VtValue(knots), timecode);
  pxr::UsdAttribute attr_order = usd_nurbs_curves.CreateOrderAttr(pxr::VtValue(), true);
  usd_value_writer_.SetAttribute(attr_order, pxr::VtValue(orders), timecode);
}

void USDCurvesWriter::set_writer_attributes(pxr::UsdGeomCurves &usd_curves,
                                            const pxr::VtArray<pxr::GfVec3f> &verts,
                                            const pxr::VtIntArray &control_point_counts,
                                            const pxr::VtArray<float> &widths,
                                            const pxr::UsdTimeCode timecode,
                                            const pxr::TfToken interpolation)
{
  pxr::UsdAttribute attr_points = usd_curves.CreatePointsAttr(pxr::VtValue(), true);
  usd_value_writer_.SetAttribute(attr_points, pxr::VtValue(verts), timecode);

  pxr::UsdAttribute attr_vertex_counts = usd_curves.CreateCurveVertexCountsAttr(pxr::VtValue(),
                                                                                true);
  usd_value_writer_.SetAttribute(attr_vertex_counts, pxr::VtValue(control_point_counts), timecode);

  if (!widths.empty()) {
    pxr::UsdAttribute attr_widths = usd_curves.CreateWidthsAttr(pxr::VtValue(), true);
    usd_value_writer_.SetAttribute(attr_widths, pxr::VtValue(widths), timecode);

    usd_curves.SetWidthsInterpolation(interpolation);
  }
}

void USDCurvesWriter::do_write(HierarchyContext &context)
{
  Curves *curves_id;
  std::unique_ptr<Curves, std::function<void(Curves *)>> converted_curves;

  switch (context.object->type) {
    case OB_CURVES_LEGACY: {
      const Curve *legacy_curve = static_cast<Curve *>(context.object->data);
      converted_curves = std::unique_ptr<Curves, std::function<void(Curves *)>>(
          bke::curve_legacy_to_curves(*legacy_curve), [](Curves *c) { BKE_id_free(nullptr, c); });
      curves_id = converted_curves.get();
      break;
    }
    case OB_CURVES:
      curves_id = static_cast<Curves *>(context.object->data);
      break;
    default:
      BLI_assert_unreachable();
      return;
  }

  const bke::CurvesGeometry &curves = curves_id->geometry.wrap();
  if (curves.points_num() == 0) {
    return;
  }

  const std::array<int, CURVE_TYPES_NUM> &curve_type_counts = curves.curve_type_counts();
  const int number_of_curve_types = std::count_if(curve_type_counts.begin(),
                                                  curve_type_counts.end(),
                                                  [](const int count) { return count > 0; });
  if (number_of_curve_types > 1) {
    BKE_report(
        reports(), RPT_WARNING, "Cannot export mixed curve types in the same Curves object");
    return;
  }

  if (array_utils::booleans_mix_calc(curves.cyclic()) == array_utils::BooleanMix::Mixed) {
    BKE_report(reports(),
               RPT_WARNING,
               "Cannot export mixed cyclic and non-cyclic curves in the same Curves object");
    return;
  }

  const pxr::UsdTimeCode timecode = get_export_time_code();
  const int8_t curve_type = curves.curve_types()[0];

  if (first_frame_curve_type == -1) {
    first_frame_curve_type = curve_type;
  }
  else if (first_frame_curve_type != curve_type) {
    const char *first_frame_curve_type_name = nullptr;
    RNA_enum_name_from_value(
        rna_enum_curves_type_items, int(first_frame_curve_type), &first_frame_curve_type_name);

    const char *current_curve_type_name = nullptr;
    RNA_enum_name_from_value(
        rna_enum_curves_type_items, int(curve_type), &current_curve_type_name);

    BKE_reportf(reports(),
                RPT_WARNING,
                "USD does not support animating curve types. The curve type changes from %s to "
                "%s on frame %f",
                IFACE_(first_frame_curve_type_name),
                IFACE_(current_curve_type_name),
                timecode.GetValue());
    return;
  }

  const bool is_cyclic = curves.cyclic().first();
  pxr::VtArray<pxr::GfVec3f> verts;
  pxr::VtIntArray control_point_counts;
  pxr::VtArray<float> widths;
  pxr::TfToken interpolation;

  pxr::UsdGeomBasisCurves usd_basis_curves;
  pxr::UsdGeomNurbsCurves usd_nurbs_curves;
  pxr::UsdGeomCurves *usd_curves = nullptr;

  control_point_counts.resize(curves.curves_num());
  switch (curve_type) {
    case CURVE_TYPE_POLY:
      usd_basis_curves = DefineUsdGeomBasisCurves(pxr::VtValue(), is_cyclic, false);
      usd_curves = &usd_basis_curves;

      populate_curve_props(
          curves, verts, control_point_counts, widths, interpolation, is_cyclic, false, reports());
      break;
    case CURVE_TYPE_CATMULL_ROM:
      usd_basis_curves = DefineUsdGeomBasisCurves(
          pxr::VtValue(pxr::UsdGeomTokens->catmullRom), is_cyclic, true);
      usd_curves = &usd_basis_curves;

      populate_curve_props(
          curves, verts, control_point_counts, widths, interpolation, is_cyclic, true, reports());
      break;
    case CURVE_TYPE_BEZIER:
      usd_basis_curves = DefineUsdGeomBasisCurves(
          pxr::VtValue(pxr::UsdGeomTokens->bezier), is_cyclic, true);
      usd_curves = &usd_basis_curves;

      populate_curve_props_for_bezier(
          curves, verts, control_point_counts, widths, interpolation, is_cyclic, reports());
      break;
    case CURVE_TYPE_NURBS: {
      pxr::VtArray<double> knots;
      pxr::VtArray<int> orders;
      orders.resize(curves.curves_num());

      usd_nurbs_curves = pxr::UsdGeomNurbsCurves::Define(usd_export_context_.stage,
                                                         usd_export_context_.usd_path);
      usd_curves = &usd_nurbs_curves;

      populate_curve_props_for_nurbs(
          curves, verts, control_point_counts, widths, knots, orders, interpolation, is_cyclic);

      set_writer_attributes_for_nurbs(usd_nurbs_curves, knots, orders, timecode);

      break;
    }
    default:
      BLI_assert_unreachable();
  }

  set_writer_attributes(*usd_curves, verts, control_point_counts, widths, timecode, interpolation);

  assign_materials(context, *usd_curves);

  auto prim = usd_curves->GetPrim();
  write_id_properties(prim, curves_id->id, timecode);
}

void USDCurvesWriter::assign_materials(const HierarchyContext &context,
                                       const pxr::UsdGeomCurves &usd_curves)
{
  if (context.object->totcol == 0) {
    return;
  }

  bool curve_material_bound = false;
  for (short mat_num = 0; mat_num < context.object->totcol; mat_num++) {
    Material *material = BKE_object_material_get(context.object, mat_num + 1);
    if (material == nullptr) {
      continue;
    }

    pxr::UsdPrim curve_prim = usd_curves.GetPrim();
    pxr::UsdShadeMaterialBindingAPI api = pxr::UsdShadeMaterialBindingAPI(curve_prim);
    pxr::UsdShadeMaterial usd_material = ensure_usd_material(context, material);
    api.Bind(usd_material);
    pxr::UsdShadeMaterialBindingAPI::Apply(curve_prim);

    /* USD seems to support neither per-material nor per-face-group double-sidedness, so we just
     * use the flag from the first non-empty material slot. */
    usd_curves.CreateDoubleSidedAttr(
        pxr::VtValue((material->blend_flag & MA_BL_CULL_BACKFACE) == 0));

    curve_material_bound = true;
    break;
  }

  if (!curve_material_bound) {
    /* Blender defaults to double-sided, but USD to single-sided. */
    usd_curves.CreateDoubleSidedAttr(pxr::VtValue(true));
  }
}

}  // namespace blender::io::usd

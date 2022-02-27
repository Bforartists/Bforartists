/* SPDX-License-Identifier: GPL-2.0-or-later */

#include "BKE_spline.hh"

#include "UI_interface.h"
#include "UI_resources.h"

#include "node_geometry_util.hh"

namespace blender::nodes::node_geo_curve_primitive_bezier_segment_cc {

NODE_STORAGE_FUNCS(NodeGeometryCurvePrimitiveBezierSegment)

static void node_declare(NodeDeclarationBuilder &b)
{
  b.add_input<decl::Int>(N_("Resolution"))
      .default_value(16)
      .min(1)
      .max(256)
      .subtype(PROP_UNSIGNED)
      .description(N_("The number of evaluated points on the curve"));
  b.add_input<decl::Vector>(N_("Start"))
      .default_value({-1.0f, 0.0f, 0.0f})
      .subtype(PROP_TRANSLATION)
      .description(N_("Position of the start control point of the curve"));
  b.add_input<decl::Vector>(N_("Start Handle"))
      .default_value({-0.5f, 0.5f, 0.0f})
      .subtype(PROP_TRANSLATION)
      .description(
          N_("Position of the start handle used to define the shape of the curve. In Offset mode, "
             "relative to Start point"));
  b.add_input<decl::Vector>(N_("End Handle"))
      .subtype(PROP_TRANSLATION)
      .description(
          N_("Position of the end handle used to define the shape of the curve. In Offset mode, "
             "relative to End point"));
  b.add_input<decl::Vector>(N_("End"))
      .default_value({1.0f, 0.0f, 0.0f})
      .subtype(PROP_TRANSLATION)
      .description(N_("Position of the end control point of the curve"));
  b.add_output<decl::Geometry>(N_("Curve"));
}

static void node_layout(uiLayout *layout, bContext *UNUSED(C), PointerRNA *ptr)
{
  uiItemR(layout, ptr, "mode", UI_ITEM_R_EXPAND, nullptr, ICON_NONE);
}

static void node_init(bNodeTree *UNUSED(tree), bNode *node)
{
  NodeGeometryCurvePrimitiveBezierSegment *data =
      MEM_cnew<NodeGeometryCurvePrimitiveBezierSegment>(__func__);

  data->mode = GEO_NODE_CURVE_PRIMITIVE_BEZIER_SEGMENT_POSITION;
  node->storage = data;
}

static std::unique_ptr<CurveEval> create_bezier_segment_curve(
    const float3 start,
    const float3 start_handle_right,
    const float3 end,
    const float3 end_handle_left,
    const int resolution,
    const GeometryNodeCurvePrimitiveBezierSegmentMode mode)
{
  std::unique_ptr<CurveEval> curve = std::make_unique<CurveEval>();
  std::unique_ptr<BezierSpline> spline = std::make_unique<BezierSpline>();
  spline->set_resolution(resolution);

  spline->resize(2);
  MutableSpan<float3> positions = spline->positions();
  spline->handle_types_left().fill(BEZIER_HANDLE_ALIGN);
  spline->handle_types_right().fill(BEZIER_HANDLE_ALIGN);
  spline->radii().fill(1.0f);
  spline->tilts().fill(0.0f);

  positions.first() = start;
  positions.last() = end;

  MutableSpan<float3> handles_right = spline->handle_positions_right();
  MutableSpan<float3> handles_left = spline->handle_positions_left();

  if (mode == GEO_NODE_CURVE_PRIMITIVE_BEZIER_SEGMENT_POSITION) {
    handles_left.first() = 2.0f * start - start_handle_right;
    handles_right.first() = start_handle_right;

    handles_left.last() = end_handle_left;
    handles_right.last() = 2.0f * end - end_handle_left;
  }
  else {
    handles_left.first() = start - start_handle_right;
    handles_right.first() = start + start_handle_right;

    handles_left.last() = end + end_handle_left;
    handles_right.last() = end - end_handle_left;
  }

  curve->add_spline(std::move(spline));
  curve->attributes.reallocate(1);
  return curve;
}

static void node_geo_exec(GeoNodeExecParams params)
{
  const NodeGeometryCurvePrimitiveBezierSegment &storage = node_storage(params.node());
  const GeometryNodeCurvePrimitiveBezierSegmentMode mode =
      (const GeometryNodeCurvePrimitiveBezierSegmentMode)storage.mode;

  std::unique_ptr<CurveEval> curve = create_bezier_segment_curve(
      params.extract_input<float3>("Start"),
      params.extract_input<float3>("Start Handle"),
      params.extract_input<float3>("End"),
      params.extract_input<float3>("End Handle"),
      std::max(params.extract_input<int>("Resolution"), 1),
      mode);
  params.set_output("Curve", GeometrySet::create_with_curve(curve.release()));
}

}  // namespace blender::nodes::node_geo_curve_primitive_bezier_segment_cc

void register_node_type_geo_curve_primitive_bezier_segment()
{
  namespace file_ns = blender::nodes::node_geo_curve_primitive_bezier_segment_cc;

  static bNodeType ntype;
  geo_node_type_base(
      &ntype, GEO_NODE_CURVE_PRIMITIVE_BEZIER_SEGMENT, "Bezier Segment", NODE_CLASS_GEOMETRY);
  node_type_init(&ntype, file_ns::node_init);
  node_type_storage(&ntype,
                    "NodeGeometryCurvePrimitiveBezierSegment",
                    node_free_standard_storage,
                    node_copy_standard_storage);
  ntype.declare = file_ns::node_declare;
  ntype.draw_buttons = file_ns::node_layout;
  ntype.geometry_node_execute = file_ns::node_geo_exec;
  nodeRegisterType(&ntype);
}

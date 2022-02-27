/* SPDX-License-Identifier: GPL-2.0-or-later */

#include "BKE_spline.hh"

#include "UI_interface.h"
#include "UI_resources.h"

#include "node_geometry_util.hh"

namespace blender::nodes::node_geo_legacy_curve_set_handles_cc {

static void node_decalre(NodeDeclarationBuilder &b)
{
  b.add_input<decl::Geometry>(N_("Curve"));
  b.add_input<decl::String>(N_("Selection"));
  b.add_output<decl::Geometry>(N_("Curve"));
}

static void node_layout(uiLayout *layout, bContext *UNUSED(C), PointerRNA *ptr)
{
  uiItemR(layout, ptr, "mode", UI_ITEM_R_EXPAND, nullptr, ICON_NONE);
  uiItemR(layout, ptr, "handle_type", 0, "", ICON_NONE);
}

static void node_init(bNodeTree *UNUSED(tree), bNode *node)
{
  NodeGeometryCurveSetHandles *data = MEM_cnew<NodeGeometryCurveSetHandles>(__func__);

  data->handle_type = GEO_NODE_CURVE_HANDLE_AUTO;
  data->mode = GEO_NODE_CURVE_HANDLE_LEFT | GEO_NODE_CURVE_HANDLE_RIGHT;
  node->storage = data;
}

static HandleType handle_type_from_input_type(GeometryNodeCurveHandleType type)
{
  switch (type) {
    case GEO_NODE_CURVE_HANDLE_AUTO:
      return BEZIER_HANDLE_AUTO;
    case GEO_NODE_CURVE_HANDLE_ALIGN:
      return BEZIER_HANDLE_ALIGN;
    case GEO_NODE_CURVE_HANDLE_FREE:
      return BEZIER_HANDLE_FREE;
    case GEO_NODE_CURVE_HANDLE_VECTOR:
      return BEZIER_HANDLE_VECTOR;
  }
  BLI_assert_unreachable();
  return BEZIER_HANDLE_AUTO;
}

static void node_geo_exec(GeoNodeExecParams params)
{
  const NodeGeometryCurveSetHandles *node_storage =
      (NodeGeometryCurveSetHandles *)params.node().storage;
  const GeometryNodeCurveHandleType type = (GeometryNodeCurveHandleType)node_storage->handle_type;
  const GeometryNodeCurveHandleMode mode = (GeometryNodeCurveHandleMode)node_storage->mode;

  GeometrySet geometry_set = params.extract_input<GeometrySet>("Curve");
  geometry_set = geometry::realize_instances_legacy(geometry_set);
  if (!geometry_set.has_curve()) {
    params.set_output("Curve", geometry_set);
    return;
  }

  /* Retrieve data for write access so we can avoid new allocations for the handles data. */
  CurveComponent &curve_component = geometry_set.get_component_for_write<CurveComponent>();
  CurveEval &curve = *curve_component.get_for_write();
  MutableSpan<SplinePtr> splines = curve.splines();

  const std::string selection_name = params.extract_input<std::string>("Selection");
  VArray<bool> selection = curve_component.attribute_get_for_read(
      selection_name, ATTR_DOMAIN_POINT, true);

  const HandleType new_handle_type = handle_type_from_input_type(type);
  int point_index = 0;
  bool has_bezier_spline = false;
  for (SplinePtr &spline : splines) {
    if (spline->type() != CURVE_TYPE_BEZIER) {
      point_index += spline->positions().size();
      continue;
    }

    BezierSpline &bezier_spline = static_cast<BezierSpline &>(*spline);
    if (ELEM(new_handle_type, BEZIER_HANDLE_FREE, BEZIER_HANDLE_ALIGN)) {
      /* In this case the automatically calculated handle types need to be "baked", because
       * they're possibly changing from a type that is calculated automatically to a type that
       * is positioned manually. */
      bezier_spline.ensure_auto_handles();
    }
    has_bezier_spline = true;
    for (int i_point : IndexRange(bezier_spline.size())) {
      if (selection[point_index]) {
        if (mode & GEO_NODE_CURVE_HANDLE_LEFT) {
          bezier_spline.handle_types_left()[i_point] = new_handle_type;
        }
        if (mode & GEO_NODE_CURVE_HANDLE_RIGHT) {
          bezier_spline.handle_types_right()[i_point] = new_handle_type;
        }
      }
      point_index++;
    }
    bezier_spline.mark_cache_invalid();
  }

  if (!has_bezier_spline) {
    params.error_message_add(NodeWarningType::Info, TIP_("No Bezier splines in input curve"));
  }

  params.set_output("Curve", geometry_set);
}
}  // namespace blender::nodes::node_geo_legacy_curve_set_handles_cc

void register_node_type_geo_legacy_curve_set_handles()
{
  namespace file_ns = blender::nodes::node_geo_legacy_curve_set_handles_cc;

  static bNodeType ntype;
  geo_node_type_base(
      &ntype, GEO_NODE_LEGACY_CURVE_SET_HANDLES, "Set Handle Type", NODE_CLASS_GEOMETRY);
  ntype.declare = file_ns::node_decalre;
  ntype.geometry_node_execute = file_ns::node_geo_exec;
  node_type_init(&ntype, file_ns::node_init);
  node_type_storage(&ntype,
                    "NodeGeometryCurveSetHandles",
                    node_free_standard_storage,
                    node_copy_standard_storage);
  ntype.draw_buttons = file_ns::node_layout;

  nodeRegisterType(&ntype);
}

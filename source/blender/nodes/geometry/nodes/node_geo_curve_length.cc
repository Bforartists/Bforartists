/* SPDX-License-Identifier: GPL-2.0-or-later */

#include "BKE_spline.hh"
#include "node_geometry_util.hh"

namespace blender::nodes::node_geo_curve_length_cc {

static void node_declare(NodeDeclarationBuilder &b)
{
  b.add_input<decl::Geometry>(N_("Curve")).supported_type(GEO_COMPONENT_TYPE_CURVE);
  b.add_output<decl::Float>(N_("Length"));
}

static void node_geo_exec(GeoNodeExecParams params)
{
  GeometrySet curve_set = params.extract_input<GeometrySet>("Curve");
  if (!curve_set.has_curve()) {
    params.set_default_remaining_outputs();
    return;
  }
  const CurveEval &curve = *curve_set.get_curve_for_read();
  float length = 0.0f;
  for (const SplinePtr &spline : curve.splines()) {
    length += spline->length();
  }
  params.set_output("Length", length);
}

}  // namespace blender::nodes::node_geo_curve_length_cc

void register_node_type_geo_curve_length()
{
  namespace file_ns = blender::nodes::node_geo_curve_length_cc;

  static bNodeType ntype;

  geo_node_type_base(&ntype, GEO_NODE_CURVE_LENGTH, "Curve Length", NODE_CLASS_GEOMETRY);
  ntype.declare = file_ns::node_declare;
  ntype.geometry_node_execute = file_ns::node_geo_exec;
  nodeRegisterType(&ntype);
}

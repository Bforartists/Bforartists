/* SPDX-License-Identifier: GPL-2.0-or-later */

#include "DNA_modifier_types.h"

#include "node_geometry_util.hh"

extern "C" {
Mesh *doEdgeSplit(const Mesh *mesh, EdgeSplitModifierData *emd);
}

namespace blender::nodes::node_geo_legacy_edge_split_cc {

static void node_declare(NodeDeclarationBuilder &b)
{
  b.add_input<decl::Geometry>(N_("Geometry"));
  b.add_input<decl::Bool>(N_("Edge Angle")).default_value(true);
  b.add_input<decl::Float>(N_("Angle"))
      .default_value(DEG2RADF(30.0f))
      .min(0.0f)
      .max(DEG2RADF(180.0f))
      .subtype(PROP_ANGLE);
  b.add_input<decl::Bool>(N_("Sharp Edges"));
  b.add_output<decl::Geometry>(N_("Geometry"));
}

static void node_geo_exec(GeoNodeExecParams params)
{
  GeometrySet geometry_set = params.extract_input<GeometrySet>("Geometry");

  geometry_set = geometry::realize_instances_legacy(geometry_set);

  if (!geometry_set.has_mesh()) {
    params.set_output("Geometry", std::move(geometry_set));
    return;
  }

  const bool use_sharp_flag = params.extract_input<bool>("Sharp Edges");
  const bool use_edge_angle = params.extract_input<bool>("Edge Angle");

  if (!use_edge_angle && !use_sharp_flag) {
    params.set_output("Geometry", std::move(geometry_set));
    return;
  }

  const float split_angle = params.extract_input<float>("Angle");
  const Mesh *mesh_in = geometry_set.get_mesh_for_read();

  /* Use modifier struct to pass arguments to the modifier code. */
  EdgeSplitModifierData emd;
  memset(&emd, 0, sizeof(EdgeSplitModifierData));
  emd.split_angle = split_angle;
  if (use_edge_angle) {
    emd.flags = MOD_EDGESPLIT_FROMANGLE;
  }
  if (use_sharp_flag) {
    emd.flags |= MOD_EDGESPLIT_FROMFLAG;
  }

  Mesh *mesh_out = doEdgeSplit(mesh_in, &emd);
  geometry_set.replace_mesh(mesh_out);

  params.set_output("Geometry", std::move(geometry_set));
}

}  // namespace blender::nodes::node_geo_legacy_edge_split_cc

void register_node_type_geo_legacy_edge_split()
{
  namespace file_ns = blender::nodes::node_geo_legacy_edge_split_cc;

  static bNodeType ntype;

  geo_node_type_base(&ntype, GEO_NODE_LEGACY_EDGE_SPLIT, "Edge Split", NODE_CLASS_GEOMETRY);
  ntype.geometry_node_execute = file_ns::node_geo_exec;
  ntype.declare = file_ns::node_declare;
  nodeRegisterType(&ntype);
}

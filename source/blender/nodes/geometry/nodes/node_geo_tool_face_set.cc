/* SPDX-FileCopyrightText: 2023 Blender Foundation
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#include "BKE_geometry_fields.hh"

#include "node_geometry_util.hh"

namespace blender::nodes::node_geo_tool_face_set_cc {

static void node_declare(NodeDeclarationBuilder &b)
{
  b.add_output<decl::Int>("Face Set").field_source();
  b.add_output<decl::Bool>("Exists").field_source();
}

static void node_geo_exec(GeoNodeExecParams params)
{
  if (!check_tool_context_and_error(params)) {
    return;
  }
  params.set_output("Face Set", bke::AttributeFieldInput::Create<int>(".sculpt_face_set"));
  params.set_output("Exists", bke::AttributeExistsFieldInput::Create(".sculpt_face_set"));
}

}  // namespace blender::nodes::node_geo_tool_face_set_cc

void register_node_type_geo_tool_face_set()
{
  namespace file_ns = blender::nodes::node_geo_tool_face_set_cc;
  static bNodeType ntype;
  geo_node_type_base(&ntype, GEO_NODE_TOOL_FACE_SET, "Face Set", NODE_CLASS_INPUT);
  ntype.declare = file_ns::node_declare;
  ntype.geometry_node_execute = file_ns::node_geo_exec;
  ntype.gather_add_node_search_ops = blender::nodes::search_link_ops_for_for_tool_node;
  ntype.gather_link_search_ops = blender::nodes::search_link_ops_for_tool_node;
  nodeRegisterType(&ntype);
}

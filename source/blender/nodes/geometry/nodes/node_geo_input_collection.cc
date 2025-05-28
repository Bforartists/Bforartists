/* SPDX-FileCopyrightText: 2024 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#include "UI_interface.hh"
#include "UI_resources.hh"

#include "node_geometry_util.hh"

namespace blender::nodes::node_geo_input_collection_cc {

static void node_declare(NodeDeclarationBuilder &b)
{
  b.add_output<decl::Collection>("Collection").custom_draw([](CustomSocketDrawParams &params) {
    uiLayoutSetAlignment(&params.layout, UI_LAYOUT_ALIGN_EXPAND);
    params.layout.prop(&params.node_ptr, "collection", UI_ITEM_NONE, "", ICON_NONE);
  });
}

static void node_geo_exec(GeoNodeExecParams params)
{
  Collection *collection = reinterpret_cast<Collection *>(params.node().id);
  params.set_output("Collection", collection);
}

static void node_register()
{
  static blender::bke::bNodeType ntype;

  geo_node_type_base(&ntype, "GeometryNodeInputCollection", GEO_NODE_INPUT_COLLECTION);
  ntype.ui_name = "Collection";
  ntype.ui_description = "Output a single collection";
  ntype.enum_name_legacy = "INPUT_COLLECTION";
  ntype.nclass = NODE_CLASS_INPUT;
  ntype.declare = node_declare;
  ntype.geometry_node_execute = node_geo_exec;
  blender::bke::node_register_type(ntype);
}
NOD_REGISTER_NODE(node_register)

}  // namespace blender::nodes::node_geo_input_collection_cc

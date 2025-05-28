/* SPDX-FileCopyrightText: 2024 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#include "UI_interface.hh"
#include "UI_resources.hh"

#include "node_geometry_util.hh"

namespace blender::nodes::node_geo_input_object_cc {

static void node_declare(NodeDeclarationBuilder &b)
{
  b.add_output<decl::Object>("Object").custom_draw([](CustomSocketDrawParams &params) {
    uiLayoutSetAlignment(&params.layout, UI_LAYOUT_ALIGN_EXPAND);
    params.layout.prop(&params.node_ptr, "object", UI_ITEM_NONE, "", ICON_NONE);
  });
}

static void node_geo_exec(GeoNodeExecParams params)
{
  Object *object = reinterpret_cast<Object *>(params.node().id);
  params.set_output("Object", object);
}

static void node_register()
{
  static blender::bke::bNodeType ntype;

  geo_node_type_base(&ntype, "GeometryNodeInputObject", GEO_NODE_INPUT_OBJECT);
  ntype.ui_name = "Object";
  ntype.ui_description = "Output a single object";
  ntype.enum_name_legacy = "INPUT_OBJECT";
  ntype.nclass = NODE_CLASS_INPUT;
  ntype.declare = node_declare;
  ntype.geometry_node_execute = node_geo_exec;
  blender::bke::node_register_type(ntype);
}
NOD_REGISTER_NODE(node_register)

}  // namespace blender::nodes::node_geo_input_object_cc

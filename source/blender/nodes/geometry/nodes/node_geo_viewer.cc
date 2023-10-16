/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#include "BKE_context.h"

#include "NOD_rna_define.hh"
#include "NOD_socket_search_link.hh"

#include "UI_interface.hh"
#include "UI_resources.hh"

#include "ED_node.hh"
#include "ED_viewer_path.hh"

#include "RNA_enum_types.hh"

#include "node_geometry_util.hh"

namespace blender::nodes::node_geo_viewer_cc {

NODE_STORAGE_FUNCS(NodeGeometryViewer)

static void node_declare(NodeDeclarationBuilder &b)
{
  b.add_input<decl::Geometry>("Geometry");
  b.add_input<decl::Float>("Value").field_on_all().hide_value();
  b.add_input<decl::Vector>("Value", "Value_001").field_on_all().hide_value();
  b.add_input<decl::Color>("Value", "Value_002").field_on_all().hide_value();
  b.add_input<decl::Int>("Value", "Value_003").field_on_all().hide_value();
  b.add_input<decl::Bool>("Value", "Value_004").field_on_all().hide_value();
  b.add_input<decl::Rotation>("Value", "Value_005").field_on_all().hide_value();
}

static void node_init(bNodeTree * /*tree*/, bNode *node)
{
  NodeGeometryViewer *data = MEM_cnew<NodeGeometryViewer>(__func__);
  data->data_type = CD_PROP_FLOAT;
  data->domain = ATTR_DOMAIN_AUTO;

  node->storage = data;
}

static void node_layout(uiLayout *layout, bContext * /*C*/, PointerRNA *ptr)
{
  uiItemR(layout, ptr, "domain", UI_ITEM_NONE, "", ICON_NONE);
}

static void node_layout_ex(uiLayout *layout, bContext * /*C*/, PointerRNA *ptr)
{
  uiItemR(layout, ptr, "data_type", UI_ITEM_NONE, "", ICON_NONE);
}

static eNodeSocketDatatype custom_data_type_to_socket_type(const eCustomDataType type)
{
  switch (type) {
    case CD_PROP_FLOAT:
      return SOCK_FLOAT;
    case CD_PROP_INT32:
      return SOCK_INT;
    case CD_PROP_FLOAT3:
      return SOCK_VECTOR;
    case CD_PROP_BOOL:
      return SOCK_BOOLEAN;
    case CD_PROP_COLOR:
      return SOCK_RGBA;
    case CD_PROP_QUATERNION:
      return SOCK_ROTATION;
    default:
      BLI_assert_unreachable();
      return SOCK_FLOAT;
  }
}

static void node_update(bNodeTree *ntree, bNode *node)
{
  const NodeGeometryViewer &storage = node_storage(*node);
  const eCustomDataType data_type = eCustomDataType(storage.data_type);
  const eNodeSocketDatatype socket_type = custom_data_type_to_socket_type(data_type);

  LISTBASE_FOREACH (bNodeSocket *, socket, &node->inputs) {
    if (socket->type == SOCK_GEOMETRY) {
      continue;
    }
    bke::nodeSetSocketAvailability(ntree, socket, socket->type == socket_type);
  }
}

static void node_gather_link_searches(GatherLinkSearchOpParams &params)
{
  auto set_active_fn = [](LinkSearchOpParams &params, bNode &viewer_node) {
    /* Set this new viewer node active in spreadsheet editors. */
    SpaceNode *snode = CTX_wm_space_node(&params.C);
    Main *bmain = CTX_data_main(&params.C);
    ED_node_set_active(bmain, snode, &params.node_tree, &viewer_node, nullptr);
    ed::viewer_path::activate_geometry_node(*bmain, *snode, viewer_node);
  };

  const eNodeSocketDatatype socket_type = eNodeSocketDatatype(params.other_socket().type);
  const std::optional<eCustomDataType> type = bke::socket_type_to_custom_data_type(socket_type);
  if (params.in_out() == SOCK_OUT) {
    /* The viewer node only has inputs. */
    return;
  }
  if (params.other_socket().type == SOCK_GEOMETRY) {
    params.add_item(IFACE_("Geometry"), [set_active_fn](LinkSearchOpParams &params) {
      bNode &node = params.add_node("GeometryNodeViewer");
      params.connect_available_socket(node, "Geometry");
      set_active_fn(params, node);
    });
  }
  if (type && ELEM(type,
                   CD_PROP_FLOAT,
                   CD_PROP_BOOL,
                   CD_PROP_INT32,
                   CD_PROP_FLOAT3,
                   CD_PROP_COLOR,
                   CD_PROP_QUATERNION))
  {
    params.add_item(IFACE_("Value"), [type, set_active_fn](LinkSearchOpParams &params) {
      bNode &node = params.add_node("GeometryNodeViewer");
      node_storage(node).data_type = *type;
      params.update_and_connect_available_socket(node, "Value");

      /* If the source node has a geometry socket, connect it to the new viewer node as well. */
      LISTBASE_FOREACH (bNodeSocket *, socket, &params.node.outputs) {
        if (socket->type == SOCK_GEOMETRY && socket->is_visible()) {
          nodeAddLink(&params.node_tree,
                      &params.node,
                      socket,
                      &node,
                      static_cast<bNodeSocket *>(node.inputs.first));
        }
      }

      set_active_fn(params, node);
    });
  }
}

static void node_rna(StructRNA *srna)
{
  RNA_def_node_enum(srna,
                    "data_type",
                    "Data Type",
                    "",
                    rna_enum_attribute_type_items,
                    NOD_storage_enum_accessors(data_type),
                    CD_PROP_FLOAT,
                    enums::attribute_type_type_with_socket_fn);

  RNA_def_node_enum(srna,
                    "domain",
                    "Domain",
                    "Domain to evaluate the field on",
                    rna_enum_attribute_domain_with_auto_items,
                    NOD_storage_enum_accessors(domain),
                    ATTR_DOMAIN_POINT);
}

static void node_register()
{
  static bNodeType ntype;

  geo_node_type_base(&ntype, GEO_NODE_VIEWER, "Viewer", NODE_CLASS_OUTPUT);
  node_type_storage(
      &ntype, "NodeGeometryViewer", node_free_standard_storage, node_copy_standard_storage);
  ntype.updatefunc = node_update;
  ntype.initfunc = node_init;
  ntype.declare = node_declare;
  ntype.draw_buttons = node_layout;
  ntype.draw_buttons_ex = node_layout_ex;
  ntype.gather_link_search_ops = node_gather_link_searches;
  ntype.no_muting = true;
  nodeRegisterType(&ntype);

  node_rna(ntype.rna_ext.srna);
}
NOD_REGISTER_NODE(node_register)

}  // namespace blender::nodes::node_geo_viewer_cc

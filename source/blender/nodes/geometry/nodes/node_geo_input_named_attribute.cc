/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#include "NOD_rna_define.hh"

#include "UI_interface.hh"
#include "UI_resources.hh"

#include "NOD_socket_search_link.hh"

#include "RNA_enum_types.hh"

#include "node_geometry_util.hh"

namespace blender::nodes::node_geo_input_named_attribute_cc {

NODE_STORAGE_FUNCS(NodeGeometryInputNamedAttribute)

static void node_declare(NodeDeclarationBuilder &b)
{
  b.add_input<decl::String>("Name").is_attribute_name();

  b.add_output<decl::Vector>("Attribute", "Attribute_Vector").field_source();
  b.add_output<decl::Float>("Attribute", "Attribute_Float").field_source();
  b.add_output<decl::Color>("Attribute", "Attribute_Color").field_source();
  b.add_output<decl::Bool>("Attribute", "Attribute_Bool").field_source();
  b.add_output<decl::Int>("Attribute", "Attribute_Int").field_source();
  b.add_output<decl::Rotation>("Attribute", "Attribute_Rotation").field_source();

  b.add_output<decl::Bool>("Exists").field_source();
}

static void node_layout(uiLayout *layout, bContext * /*C*/, PointerRNA *ptr)
{
  uiItemR(layout, ptr, "data_type", UI_ITEM_NONE, "", ICON_NONE);
}

static void node_init(bNodeTree * /*tree*/, bNode *node)
{
  NodeGeometryInputNamedAttribute *data = MEM_cnew<NodeGeometryInputNamedAttribute>(__func__);
  data->data_type = CD_PROP_FLOAT;
  node->storage = data;
}

static void node_update(bNodeTree *ntree, bNode *node)
{
  const NodeGeometryInputNamedAttribute &storage = node_storage(*node);
  const eCustomDataType data_type = eCustomDataType(storage.data_type);

  bNodeSocket *socket_vector = static_cast<bNodeSocket *>(node->outputs.first);
  bNodeSocket *socket_float = socket_vector->next;
  bNodeSocket *socket_color4f = socket_float->next;
  bNodeSocket *socket_boolean = socket_color4f->next;
  bNodeSocket *socket_int32 = socket_boolean->next;
  bNodeSocket *socket_quat = socket_int32->next;

  bke::nodeSetSocketAvailability(ntree, socket_vector, data_type == CD_PROP_FLOAT3);
  bke::nodeSetSocketAvailability(ntree, socket_float, data_type == CD_PROP_FLOAT);
  bke::nodeSetSocketAvailability(ntree, socket_color4f, data_type == CD_PROP_COLOR);
  bke::nodeSetSocketAvailability(ntree, socket_boolean, data_type == CD_PROP_BOOL);
  bke::nodeSetSocketAvailability(ntree, socket_int32, data_type == CD_PROP_INT32);
  bke::nodeSetSocketAvailability(ntree, socket_quat, data_type == CD_PROP_QUATERNION);
}

static void node_gather_link_searches(GatherLinkSearchOpParams &params)
{
  const NodeDeclaration &declaration = *params.node_type().static_declaration;
  search_link_ops_for_declarations(params, declaration.inputs);

  const bNodeType &node_type = params.node_type();
  if (params.in_out() == SOCK_OUT) {
    const std::optional<eCustomDataType> type = bke::socket_type_to_custom_data_type(
        eNodeSocketDatatype(params.other_socket().type));
    if (type && *type != CD_PROP_STRING) {
      /* The input and output sockets have the same name. */
      params.add_item(IFACE_("Attribute"), [node_type, type](LinkSearchOpParams &params) {
        bNode &node = params.add_node(node_type);
        node_storage(node).data_type = *type;
        params.update_and_connect_available_socket(node, "Attribute");
      });
      if (params.node_tree().typeinfo->validate_link(
              SOCK_BOOLEAN, eNodeSocketDatatype(params.other_socket().type)))
      {
        params.add_item(
            IFACE_("Exists"),
            [node_type](LinkSearchOpParams &params) {
              bNode &node = params.add_node(node_type);
              params.update_and_connect_available_socket(node, "Exists");
            },
            -1);
      }
    }
  }
}

static void node_geo_exec(GeoNodeExecParams params)
{
  const NodeGeometryInputNamedAttribute &storage = node_storage(params.node());
  const eCustomDataType data_type = eCustomDataType(storage.data_type);

  const std::string name = params.extract_input<std::string>("Name");

  if (name.empty()) {
    params.set_default_remaining_outputs();
    return;
  }
  if (!bke::allow_procedural_attribute_access(name)) {
    params.error_message_add(NodeWarningType::Info, TIP_(bke::no_procedural_access_message));
    params.set_default_remaining_outputs();
    return;
  }

  params.used_named_attribute(name, NamedAttributeUsage::Read);

  switch (data_type) {
    case CD_PROP_FLOAT:
      params.set_output("Attribute_Float", AttributeFieldInput::Create<float>(name));
      break;
    case CD_PROP_FLOAT3:
      params.set_output("Attribute_Vector", AttributeFieldInput::Create<float3>(name));
      break;
    case CD_PROP_COLOR:
      params.set_output("Attribute_Color", AttributeFieldInput::Create<ColorGeometry4f>(name));
      break;
    case CD_PROP_BOOL:
      params.set_output("Attribute_Bool", AttributeFieldInput::Create<bool>(name));
      break;
    case CD_PROP_INT32:
      params.set_output("Attribute_Int", AttributeFieldInput::Create<int>(name));
      break;
    case CD_PROP_QUATERNION:
      params.set_output("Attribute_Rotation", AttributeFieldInput::Create<math::Quaternion>(name));
      break;
    default:
      break;
  }

  params.set_output("Exists", bke::AttributeExistsFieldInput::Create(std::move(name)));
}

static void node_rna(StructRNA *srna)
{
  RNA_def_node_enum(srna,
                    "data_type",
                    "Data Type",
                    "The data type used to read the attribute values",
                    rna_enum_attribute_type_items,
                    NOD_storage_enum_accessors(data_type),
                    CD_PROP_FLOAT,
                    enums::attribute_type_type_with_socket_fn);
}

static void node_register()
{
  static bNodeType ntype;

  geo_node_type_base(&ntype, GEO_NODE_INPUT_NAMED_ATTRIBUTE, "Named Attribute", NODE_CLASS_INPUT);
  ntype.geometry_node_execute = node_geo_exec;
  ntype.declare = node_declare;
  ntype.draw_buttons = node_layout;
  ntype.gather_link_search_ops = node_gather_link_searches;
  ntype.updatefunc = node_update;
  ntype.initfunc = node_init;
  node_type_storage(&ntype,
                    "NodeGeometryInputNamedAttribute",
                    node_free_standard_storage,
                    node_copy_standard_storage);
  nodeRegisterType(&ntype);

  node_rna(ntype.rna_ext.srna);
}
NOD_REGISTER_NODE(node_register)

}  // namespace blender::nodes::node_geo_input_named_attribute_cc

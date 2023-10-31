/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#include "NOD_rna_define.hh"

#include "UI_interface.hh"
#include "UI_resources.hh"

#include "BKE_attribute_math.hh"

#include "NOD_socket_search_link.hh"

#include "RNA_enum_types.hh"

#include "node_geometry_util.hh"

namespace blender::nodes::node_geo_attribute_capture_cc {

NODE_STORAGE_FUNCS(NodeGeometryAttributeCapture)

static void node_declare(NodeDeclarationBuilder &b)
{
  b.add_input<decl::Geometry>("Geometry");
  b.add_input<decl::Vector>("Value").field_on_all();
  b.add_input<decl::Float>("Value", "Value_001").field_on_all();
  b.add_input<decl::Color>("Value", "Value_002").field_on_all();
  b.add_input<decl::Bool>("Value", "Value_003").field_on_all();
  b.add_input<decl::Int>("Value", "Value_004").field_on_all();
  b.add_input<decl::Rotation>("Value", "Value_005").field_on_all();

  b.add_output<decl::Geometry>("Geometry").propagate_all();
  b.add_output<decl::Vector>("Attribute").field_on_all();
  b.add_output<decl::Float>("Attribute", "Attribute_001").field_on_all();
  b.add_output<decl::Color>("Attribute", "Attribute_002").field_on_all();
  b.add_output<decl::Bool>("Attribute", "Attribute_003").field_on_all();
  b.add_output<decl::Int>("Attribute", "Attribute_004").field_on_all();
  b.add_output<decl::Rotation>("Attribute", "Attribute_005").field_on_all();
}

static void node_layout(uiLayout *layout, bContext * /*C*/, PointerRNA *ptr)
{
  uiLayoutSetPropSep(layout, true);
  uiLayoutSetPropDecorate(layout, false);
  uiItemR(layout, ptr, "data_type", UI_ITEM_NONE, "", ICON_NONE);
  uiItemR(layout, ptr, "domain", UI_ITEM_NONE, "", ICON_NONE);
}

static void node_init(bNodeTree * /*tree*/, bNode *node)
{
  NodeGeometryAttributeCapture *data = MEM_cnew<NodeGeometryAttributeCapture>(__func__);
  data->data_type = CD_PROP_FLOAT;
  data->domain = ATTR_DOMAIN_POINT;

  node->storage = data;
}

static void node_update(bNodeTree *ntree, bNode *node)
{
  const NodeGeometryAttributeCapture &storage = node_storage(*node);
  const eCustomDataType data_type = eCustomDataType(storage.data_type);

  bNodeSocket *socket_value_geometry = static_cast<bNodeSocket *>(node->inputs.first);
  bNodeSocket *socket_value_vector = socket_value_geometry->next;
  bNodeSocket *socket_value_float = socket_value_vector->next;
  bNodeSocket *socket_value_color4f = socket_value_float->next;
  bNodeSocket *socket_value_boolean = socket_value_color4f->next;
  bNodeSocket *socket_value_int32 = socket_value_boolean->next;
  bNodeSocket *socket_value_quat = socket_value_int32->next;

  bke::nodeSetSocketAvailability(ntree, socket_value_vector, data_type == CD_PROP_FLOAT3);
  bke::nodeSetSocketAvailability(ntree, socket_value_float, data_type == CD_PROP_FLOAT);
  bke::nodeSetSocketAvailability(ntree, socket_value_color4f, data_type == CD_PROP_COLOR);
  bke::nodeSetSocketAvailability(ntree, socket_value_boolean, data_type == CD_PROP_BOOL);
  bke::nodeSetSocketAvailability(ntree, socket_value_int32, data_type == CD_PROP_INT32);
  bke::nodeSetSocketAvailability(ntree, socket_value_quat, data_type == CD_PROP_QUATERNION);

  bNodeSocket *out_socket_value_geometry = static_cast<bNodeSocket *>(node->outputs.first);
  bNodeSocket *out_socket_value_vector = out_socket_value_geometry->next;
  bNodeSocket *out_socket_value_float = out_socket_value_vector->next;
  bNodeSocket *out_socket_value_color4f = out_socket_value_float->next;
  bNodeSocket *out_socket_value_boolean = out_socket_value_color4f->next;
  bNodeSocket *out_socket_value_int32 = out_socket_value_boolean->next;
  bNodeSocket *out_socket_value_quat = out_socket_value_int32->next;

  bke::nodeSetSocketAvailability(ntree, out_socket_value_vector, data_type == CD_PROP_FLOAT3);
  bke::nodeSetSocketAvailability(ntree, out_socket_value_float, data_type == CD_PROP_FLOAT);
  bke::nodeSetSocketAvailability(ntree, out_socket_value_color4f, data_type == CD_PROP_COLOR);
  bke::nodeSetSocketAvailability(ntree, out_socket_value_boolean, data_type == CD_PROP_BOOL);
  bke::nodeSetSocketAvailability(ntree, out_socket_value_int32, data_type == CD_PROP_INT32);
  bke::nodeSetSocketAvailability(ntree, out_socket_value_quat, data_type == CD_PROP_QUATERNION);
}

static void node_gather_link_searches(GatherLinkSearchOpParams &params)
{
  const NodeDeclaration &declaration = *params.node_type().static_declaration;
  search_link_ops_for_declarations(params, declaration.inputs.as_span().take_front(1));
  search_link_ops_for_declarations(params, declaration.outputs.as_span().take_front(1));

  const bNodeType &node_type = params.node_type();
  const std::optional<eCustomDataType> type = bke::socket_type_to_custom_data_type(
      eNodeSocketDatatype(params.other_socket().type));
  if (type && *type != CD_PROP_STRING) {
    if (params.in_out() == SOCK_OUT) {
      params.add_item(IFACE_("Attribute"), [node_type, type](LinkSearchOpParams &params) {
        bNode &node = params.add_node(node_type);
        node_storage(node).data_type = *type;
        params.update_and_connect_available_socket(node, "Attribute");
      });
    }
    else {
      params.add_item(IFACE_("Value"), [node_type, type](LinkSearchOpParams &params) {
        bNode &node = params.add_node(node_type);
        node_storage(node).data_type = *type;
        params.update_and_connect_available_socket(node, "Value");
      });
    }
  }
}

static void clean_unused_attributes(const AnonymousAttributePropagationInfo &propagation_info,
                                    const Set<AttributeIDRef> &skip,
                                    GeometryComponent &component)
{
  std::optional<MutableAttributeAccessor> attributes = component.attributes_for_write();
  if (!attributes.has_value()) {
    return;
  }

  Vector<std::string> unused_ids;
  attributes->for_all([&](const AttributeIDRef &id, const AttributeMetaData /*meta_data*/) {
    if (!id.is_anonymous()) {
      return true;
    }
    if (skip.contains(id)) {
      return true;
    }
    if (propagation_info.propagate(id.anonymous_id())) {
      return true;
    }
    unused_ids.append(id.name());
    return true;
  });

  for (const std::string &unused_id : unused_ids) {
    attributes->remove(unused_id);
  }
}

static StringRefNull identifier_suffix(eCustomDataType data_type)
{
  switch (data_type) {
    case CD_PROP_FLOAT:
      return "_001";
    case CD_PROP_INT32:
      return "_004";
    case CD_PROP_QUATERNION:
      return "_005";
    case CD_PROP_COLOR:
      return "_002";
    case CD_PROP_BOOL:
      return "_003";
    case CD_PROP_FLOAT3:
      return "";
    default:
      BLI_assert_unreachable();
      return "";
  }
}

static void node_geo_exec(GeoNodeExecParams params)
{
  GeometrySet geometry_set = params.extract_input<GeometrySet>("Geometry");

  if (!params.output_is_required("Geometry")) {
    params.error_message_add(
        NodeWarningType::Info,
        TIP_("The attribute output can not be used without the geometry output"));
    params.set_default_remaining_outputs();
    return;
  }

  const NodeGeometryAttributeCapture &storage = node_storage(params.node());
  const eCustomDataType data_type = eCustomDataType(storage.data_type);
  const eAttrDomain domain = eAttrDomain(storage.domain);

  const std::string output_identifier = "Attribute" + identifier_suffix(data_type);
  AnonymousAttributeIDPtr attribute_id = params.get_output_anonymous_attribute_id_if_needed(
      output_identifier);

  if (!attribute_id) {
    params.set_output("Geometry", geometry_set);
    params.set_default_remaining_outputs();
    return;
  }

  const std::string input_identifier = "Value" + identifier_suffix(data_type);
  GField field;

  switch (data_type) {
    case CD_PROP_FLOAT:
      field = params.extract_input<GField>(input_identifier);
      break;
    case CD_PROP_FLOAT3:
      field = params.extract_input<GField>(input_identifier);
      break;
    case CD_PROP_COLOR:
      field = params.extract_input<GField>(input_identifier);
      break;
    case CD_PROP_BOOL:
      field = params.extract_input<GField>(input_identifier);
      break;
    case CD_PROP_INT32:
      field = params.extract_input<GField>(input_identifier);
      break;
    case CD_PROP_QUATERNION:
      field = params.extract_input<GField>(input_identifier);
      break;
    default:
      break;
  }

  const auto capture_on = [&](GeometryComponent &component) {
    bke::try_capture_field_on_geometry(component, *attribute_id, domain, field);
    /* Changing of the anonymous attributes may require removing attributes that are no longer
     * needed. */
    clean_unused_attributes(
        params.get_output_propagation_info("Geometry"), {*attribute_id}, component);
  };

  /* Run on the instances component separately to only affect the top level of instances. */
  if (domain == ATTR_DOMAIN_INSTANCE) {
    if (geometry_set.has_instances()) {
      capture_on(geometry_set.get_component_for_write(GeometryComponent::Type::Instance));
    }
  }
  else {
    static const Array<GeometryComponent::Type> types = {GeometryComponent::Type::Mesh,
                                                         GeometryComponent::Type::PointCloud,
                                                         GeometryComponent::Type::Curve,
                                                         GeometryComponent::Type::GreasePencil};

    geometry_set.modify_geometry_sets([&](GeometrySet &geometry_set) {
      for (const GeometryComponent::Type type : types) {
        if (geometry_set.has(type)) {
          capture_on(geometry_set.get_component_for_write(type));
        }
      }
    });
  }

  params.set_output("Geometry", geometry_set);
}

static void node_rna(StructRNA *srna)
{
  RNA_def_node_enum(srna,
                    "data_type",
                    "Data Type",
                    "Type of data stored in attribute",
                    rna_enum_attribute_type_items,
                    NOD_storage_enum_accessors(data_type),
                    CD_PROP_FLOAT,
                    enums::attribute_type_type_with_socket_fn);

  RNA_def_node_enum(srna,
                    "domain",
                    "Domain",
                    "Which domain to store the data in",
                    rna_enum_attribute_domain_items,
                    NOD_storage_enum_accessors(domain),
                    ATTR_DOMAIN_POINT,
                    enums::domain_experimental_grease_pencil_version3_fn);
}

static void node_register()
{
  static bNodeType ntype;

  geo_node_type_base(
      &ntype, GEO_NODE_CAPTURE_ATTRIBUTE, "Capture Attribute", NODE_CLASS_ATTRIBUTE);
  node_type_storage(&ntype,
                    "NodeGeometryAttributeCapture",
                    node_free_standard_storage,
                    node_copy_standard_storage);
  ntype.initfunc = node_init;
  ntype.updatefunc = node_update;
  ntype.declare = node_declare;
  ntype.geometry_node_execute = node_geo_exec;
  ntype.draw_buttons = node_layout;
  ntype.gather_link_search_ops = node_gather_link_searches;
  nodeRegisterType(&ntype);

  node_rna(ntype.rna_ext.srna);
}
NOD_REGISTER_NODE(node_register)

}  // namespace blender::nodes::node_geo_attribute_capture_cc

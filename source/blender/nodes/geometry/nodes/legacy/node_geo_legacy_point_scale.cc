/* SPDX-License-Identifier: GPL-2.0-or-later */

#include "BKE_colorband.h"

#include "UI_interface.h"
#include "UI_resources.h"

#include "node_geometry_util.hh"

namespace blender::nodes::node_geo_legacy_point_scale_cc {

static void node_declare(NodeDeclarationBuilder &b)
{
  b.add_input<decl::Geometry>(N_("Geometry"));
  b.add_input<decl::String>(N_("Factor"));
  b.add_input<decl::Vector>(N_("Factor"), "Factor_001")
      .default_value({1.0f, 1.0f, 1.0f})
      .subtype(PROP_XYZ);
  b.add_input<decl::Float>(N_("Factor"), "Factor_002").default_value(1.0f).min(0.0f);
  b.add_output<decl::Geometry>(N_("Geometry"));
}

static void node_layout(uiLayout *layout, bContext *UNUSED(C), PointerRNA *ptr)
{
  uiLayoutSetPropSep(layout, true);
  uiLayoutSetPropDecorate(layout, false);
  uiItemR(layout, ptr, "input_type", 0, IFACE_("Type"), ICON_NONE);
}

static void node_init(bNodeTree *UNUSED(tree), bNode *node)
{
  NodeGeometryPointScale *data = MEM_cnew<NodeGeometryPointScale>(__func__);

  data->input_type = GEO_NODE_ATTRIBUTE_INPUT_VECTOR;
  node->storage = data;
}

static void node_update(bNodeTree *ntree, bNode *node)
{
  NodeGeometryPointScale &node_storage = *(NodeGeometryPointScale *)node->storage;

  update_attribute_input_socket_availabilities(
      *ntree, *node, "Factor", (GeometryNodeAttributeInputMode)node_storage.input_type);
}

static void execute_on_component(GeoNodeExecParams params, GeometryComponent &component)
{
  /* Note that scale doesn't necessarily need to be created with a vector type-- it could also use
   * the highest complexity of the existing attribute's type (if it exists) and the data type used
   * for the factor. But for it's simpler to simply always use float3, since that is usually
   * expected anyway. */
  static const float3 scale_default = float3(1.0f);
  OutputAttribute_Typed<float3> scale_attribute = component.attribute_try_get_for_output(
      "scale", ATTR_DOMAIN_POINT, CD_PROP_FLOAT3, &scale_default);
  if (!scale_attribute) {
    return;
  }

  const bNode &node = params.node();
  const NodeGeometryPointScale &node_storage = *(const NodeGeometryPointScale *)node.storage;
  const GeometryNodeAttributeInputMode input_type = (GeometryNodeAttributeInputMode)
                                                        node_storage.input_type;
  const CustomDataType data_type = (input_type == GEO_NODE_ATTRIBUTE_INPUT_FLOAT) ? CD_PROP_FLOAT :
                                                                                    CD_PROP_FLOAT3;

  GVArray attribute = params.get_input_attribute(
      "Factor", component, ATTR_DOMAIN_POINT, data_type, nullptr);
  if (!attribute) {
    return;
  }

  MutableSpan<float3> scale_span = scale_attribute.as_span();
  if (data_type == CD_PROP_FLOAT) {
    VArray<float> factors = attribute.typed<float>();
    for (const int i : scale_span.index_range()) {
      scale_span[i] = scale_span[i] * factors[i];
    }
  }
  else if (data_type == CD_PROP_FLOAT3) {
    VArray<float3> factors = attribute.typed<float3>();
    for (const int i : scale_span.index_range()) {
      scale_span[i] = scale_span[i] * factors[i];
    }
  }

  scale_attribute.save();
}

static void node_geo_exec(GeoNodeExecParams params)
{
  GeometrySet geometry_set = params.extract_input<GeometrySet>("Geometry");

  geometry_set = geometry::realize_instances_legacy(geometry_set);

  if (geometry_set.has<MeshComponent>()) {
    execute_on_component(params, geometry_set.get_component_for_write<MeshComponent>());
  }
  if (geometry_set.has<PointCloudComponent>()) {
    execute_on_component(params, geometry_set.get_component_for_write<PointCloudComponent>());
  }
  if (geometry_set.has<CurveComponent>()) {
    execute_on_component(params, geometry_set.get_component_for_write<CurveComponent>());
  }

  params.set_output("Geometry", std::move(geometry_set));
}

}  // namespace blender::nodes::node_geo_legacy_point_scale_cc

void register_node_type_geo_point_scale()
{
  namespace file_ns = blender::nodes::node_geo_legacy_point_scale_cc;

  static bNodeType ntype;

  geo_node_type_base(&ntype, GEO_NODE_LEGACY_POINT_SCALE, "Point Scale", NODE_CLASS_GEOMETRY);

  ntype.declare = file_ns::node_declare;
  node_type_init(&ntype, file_ns::node_init);
  node_type_update(&ntype, file_ns::node_update);
  node_type_storage(
      &ntype, "NodeGeometryPointScale", node_free_standard_storage, node_copy_standard_storage);
  ntype.geometry_node_execute = file_ns::node_geo_exec;
  ntype.draw_buttons = file_ns::node_layout;
  nodeRegisterType(&ntype);
}

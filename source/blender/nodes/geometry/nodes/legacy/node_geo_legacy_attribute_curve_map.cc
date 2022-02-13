/* SPDX-License-Identifier: GPL-2.0-or-later */

#include "BLI_blenlib.h"
#include "BLI_task.hh"

#include "BKE_colortools.h"

#include "UI_interface.h"
#include "UI_resources.h"

#include "node_geometry_util.hh"

namespace blender::nodes::node_geo_legacy_attribute_curve_map_cc {

static void node_declare(NodeDeclarationBuilder &b)
{
  b.add_input<decl::Geometry>(N_("Geometry"));
  b.add_input<decl::String>(N_("Attribute"));
  b.add_input<decl::String>(N_("Result"));
  b.add_output<decl::Geometry>(N_("Geometry"));
}

static void node_layout(uiLayout *layout, bContext *UNUSED(C), PointerRNA *ptr)
{
  uiItemR(layout, ptr, "data_type", 0, "", ICON_NONE);
  bNode *node = (bNode *)ptr->data;
  NodeAttributeCurveMap *data = (NodeAttributeCurveMap *)node->storage;
  switch (data->data_type) {
    case CD_PROP_FLOAT:
      uiTemplateCurveMapping(layout, ptr, "curve_vec", 0, false, false, false, false);
      break;
    case CD_PROP_FLOAT3:
      uiTemplateCurveMapping(layout, ptr, "curve_vec", 'v', false, false, false, false);
      break;
    case CD_PROP_COLOR:
      uiTemplateCurveMapping(layout, ptr, "curve_rgb", 'c', false, false, false, false);
      break;
  }
}

static void node_free_storage(bNode *node)
{
  if (node->storage) {
    NodeAttributeCurveMap *data = (NodeAttributeCurveMap *)node->storage;
    BKE_curvemapping_free(data->curve_vec);
    BKE_curvemapping_free(data->curve_rgb);
    MEM_freeN(node->storage);
  }
}

static void node_copy_storage(bNodeTree *UNUSED(dest_ntree),
                              bNode *dest_node,
                              const bNode *src_node)
{
  dest_node->storage = MEM_dupallocN(src_node->storage);
  NodeAttributeCurveMap *src_data = (NodeAttributeCurveMap *)src_node->storage;
  NodeAttributeCurveMap *dest_data = (NodeAttributeCurveMap *)dest_node->storage;
  dest_data->curve_vec = BKE_curvemapping_copy(src_data->curve_vec);
  dest_data->curve_rgb = BKE_curvemapping_copy(src_data->curve_rgb);
}

static void node_init(bNodeTree *UNUSED(ntree), bNode *node)
{
  NodeAttributeCurveMap *data = MEM_cnew<NodeAttributeCurveMap>(__func__);

  data->data_type = CD_PROP_FLOAT;
  data->curve_vec = BKE_curvemapping_add(4, -1.0f, -1.0f, 1.0f, 1.0f);
  data->curve_vec->cur = 3;
  data->curve_rgb = BKE_curvemapping_add(4, 0.0f, 0.0f, 1.0f, 1.0f);
  node->storage = data;
}

static void node_update(bNodeTree *UNUSED(ntree), bNode *node)
{
  /* Set the active curve when data type is changed. */
  NodeAttributeCurveMap *data = (NodeAttributeCurveMap *)node->storage;
  if (data->data_type == CD_PROP_FLOAT) {
    data->curve_vec->cur = 3;
  }
  else if (data->data_type == CD_PROP_FLOAT3) {
    data->curve_vec->cur = 0;
  }
}

static AttributeDomain get_result_domain(const GeometryComponent &component,
                                         StringRef input_name,
                                         StringRef result_name)
{
  /* Use the domain of the result attribute if it already exists. */
  std::optional<AttributeMetaData> result_info = component.attribute_get_meta_data(result_name);
  if (result_info) {
    return result_info->domain;
  }
  /* Otherwise use the input attribute's domain if it exists. */
  std::optional<AttributeMetaData> input_info = component.attribute_get_meta_data(input_name);
  if (input_info) {
    return input_info->domain;
  }

  return ATTR_DOMAIN_POINT;
}

static void execute_on_component(const GeoNodeExecParams &params, GeometryComponent &component)
{
  const bNode &bnode = params.node();
  NodeAttributeCurveMap &node_storage = *(NodeAttributeCurveMap *)bnode.storage;
  const std::string result_name = params.get_input<std::string>("Result");
  const std::string input_name = params.get_input<std::string>("Attribute");

  const CustomDataType result_type = (CustomDataType)node_storage.data_type;
  const AttributeDomain result_domain = get_result_domain(component, input_name, result_name);

  OutputAttribute attribute_result = component.attribute_try_get_for_output_only(
      result_name, result_domain, result_type);
  if (!attribute_result) {
    return;
  }

  switch (result_type) {
    case CD_PROP_FLOAT: {
      const CurveMapping *cumap = (CurveMapping *)node_storage.curve_vec;
      VArray<float> attribute_in = component.attribute_get_for_read<float>(
          input_name, result_domain, float(0.0f));
      MutableSpan<float> results = attribute_result.as_span<float>();
      threading::parallel_for(attribute_in.index_range(), 512, [&](IndexRange range) {
        for (const int i : range) {
          results[i] = BKE_curvemapping_evaluateF(cumap, 3, attribute_in[i]);
        }
      });
      break;
    }
    case CD_PROP_FLOAT3: {
      const CurveMapping *cumap = (CurveMapping *)node_storage.curve_vec;
      VArray<float3> attribute_in = component.attribute_get_for_read<float3>(
          input_name, result_domain, float3(0.0f));
      MutableSpan<float3> results = attribute_result.as_span<float3>();
      threading::parallel_for(attribute_in.index_range(), 512, [&](IndexRange range) {
        for (const int i : range) {
          BKE_curvemapping_evaluate3F(cumap, results[i], attribute_in[i]);
        }
      });
      break;
    }
    case CD_PROP_COLOR: {
      const CurveMapping *cumap = (CurveMapping *)node_storage.curve_rgb;
      VArray<ColorGeometry4f> attribute_in = component.attribute_get_for_read<ColorGeometry4f>(
          input_name, result_domain, ColorGeometry4f(0.0f, 0.0f, 0.0f, 1.0f));
      MutableSpan<ColorGeometry4f> results = attribute_result.as_span<ColorGeometry4f>();
      threading::parallel_for(attribute_in.index_range(), 512, [&](IndexRange range) {
        for (const int i : range) {
          BKE_curvemapping_evaluateRGBF(cumap, results[i], attribute_in[i]);
        }
      });
      break;
    }
    default: {
      BLI_assert_unreachable();
      break;
    }
  }

  attribute_result.save();
}

static void node_geo_exec(GeoNodeExecParams params)
{
  const bNode &bnode = params.node();
  NodeAttributeCurveMap *data = (NodeAttributeCurveMap *)bnode.storage;
  BKE_curvemapping_init(data->curve_vec);
  BKE_curvemapping_init(data->curve_rgb);

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

}  // namespace blender::nodes::node_geo_legacy_attribute_curve_map_cc

void register_node_type_geo_attribute_curve_map()
{
  namespace file_ns = blender::nodes::node_geo_legacy_attribute_curve_map_cc;

  static bNodeType ntype;

  geo_node_type_base(
      &ntype, GEO_NODE_LEGACY_ATTRIBUTE_CURVE_MAP, "Attribute Curve Map", NODE_CLASS_ATTRIBUTE);
  node_type_update(&ntype, file_ns::node_update);
  node_type_init(&ntype, file_ns::node_init);
  node_type_size_preset(&ntype, NODE_SIZE_LARGE);
  node_type_storage(
      &ntype, "NodeAttributeCurveMap", file_ns::node_free_storage, file_ns::node_copy_storage);
  ntype.declare = file_ns::node_declare;
  ntype.geometry_node_execute = file_ns::node_geo_exec;
  ntype.draw_buttons = file_ns::node_layout;
  nodeRegisterType(&ntype);
}

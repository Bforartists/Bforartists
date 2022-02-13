/* SPDX-License-Identifier: GPL-2.0-or-later */

#include "DNA_pointcloud_types.h"

#include "BKE_attribute_math.hh"
#include "BKE_pointcloud.h"

#include "UI_interface.h"
#include "UI_resources.h"

#include "node_geometry_util.hh"

using blender::Array;

namespace blender::nodes::node_geo_mesh_to_points_cc {

NODE_STORAGE_FUNCS(NodeGeometryMeshToPoints)

static void node_declare(NodeDeclarationBuilder &b)
{
  b.add_input<decl::Geometry>(N_("Mesh")).supported_type(GEO_COMPONENT_TYPE_MESH);
  b.add_input<decl::Bool>(N_("Selection")).default_value(true).supports_field().hide_value();
  b.add_input<decl::Vector>(N_("Position")).implicit_field();
  b.add_input<decl::Float>(N_("Radius"))
      .default_value(0.05f)
      .min(0.0f)
      .subtype(PROP_DISTANCE)
      .supports_field();
  b.add_output<decl::Geometry>(N_("Points"));
}

static void node_layout(uiLayout *layout, bContext *UNUSED(C), PointerRNA *ptr)
{
  uiItemR(layout, ptr, "mode", 0, "", ICON_NONE);
}

static void node_init(bNodeTree *UNUSED(tree), bNode *node)
{
  NodeGeometryMeshToPoints *data = MEM_cnew<NodeGeometryMeshToPoints>(__func__);
  data->mode = GEO_NODE_MESH_TO_POINTS_VERTICES;
  node->storage = data;
}

template<typename T>
static void copy_attribute_to_points(const VArray<T> &src,
                                     const IndexMask mask,
                                     MutableSpan<T> dst)
{
  for (const int i : mask.index_range()) {
    dst[i] = src[mask[i]];
  }
}

static void geometry_set_mesh_to_points(GeometrySet &geometry_set,
                                        Field<float3> &position_field,
                                        Field<float> &radius_field,
                                        Field<bool> &selection_field,
                                        const AttributeDomain domain)
{
  const MeshComponent *mesh_component = geometry_set.get_component_for_read<MeshComponent>();
  if (mesh_component == nullptr) {
    geometry_set.keep_only({GEO_COMPONENT_TYPE_INSTANCES});
    return;
  }
  GeometryComponentFieldContext field_context{*mesh_component, domain};
  const int domain_size = mesh_component->attribute_domain_size(domain);
  if (domain_size == 0) {
    geometry_set.keep_only({GEO_COMPONENT_TYPE_INSTANCES});
    return;
  }
  fn::FieldEvaluator evaluator{field_context, domain_size};
  evaluator.set_selection(selection_field);
  /* Evaluating directly into the point cloud doesn't work because we are not using the full
   * "min_array_size" array but compressing the selected elements into the final array with no
   * gaps. */
  evaluator.add(position_field);
  evaluator.add(radius_field);
  evaluator.evaluate();
  const IndexMask selection = evaluator.get_evaluated_selection_as_mask();

  PointCloud *pointcloud = BKE_pointcloud_new_nomain(selection.size());
  uninitialized_fill_n(pointcloud->radius, pointcloud->totpoint, 0.05f);
  geometry_set.replace_pointcloud(pointcloud);
  PointCloudComponent &point_component =
      geometry_set.get_component_for_write<PointCloudComponent>();

  copy_attribute_to_points(evaluator.get_evaluated<float3>(0),
                           selection,
                           {(float3 *)pointcloud->co, pointcloud->totpoint});
  copy_attribute_to_points(
      evaluator.get_evaluated<float>(1), selection, {pointcloud->radius, pointcloud->totpoint});

  Map<AttributeIDRef, AttributeKind> attributes;
  geometry_set.gather_attributes_for_propagation(
      {GEO_COMPONENT_TYPE_MESH}, GEO_COMPONENT_TYPE_POINT_CLOUD, false, attributes);
  attributes.remove("position");

  for (Map<AttributeIDRef, AttributeKind>::Item entry : attributes.items()) {
    const AttributeIDRef attribute_id = entry.key;
    const CustomDataType data_type = entry.value.data_type;
    GVArray src = mesh_component->attribute_get_for_read(attribute_id, domain, data_type);
    OutputAttribute dst = point_component.attribute_try_get_for_output_only(
        attribute_id, ATTR_DOMAIN_POINT, data_type);
    if (dst && src) {
      attribute_math::convert_to_static_type(data_type, [&](auto dummy) {
        using T = decltype(dummy);
        VArray<T> src_typed = src.typed<T>();
        copy_attribute_to_points(src_typed, selection, dst.as_span().typed<T>());
      });
      dst.save();
    }
  }

  geometry_set.keep_only({GEO_COMPONENT_TYPE_POINT_CLOUD, GEO_COMPONENT_TYPE_INSTANCES});
}

static void node_geo_exec(GeoNodeExecParams params)
{
  GeometrySet geometry_set = params.extract_input<GeometrySet>("Mesh");
  Field<float3> position = params.extract_input<Field<float3>>("Position");
  Field<float> radius = params.extract_input<Field<float>>("Radius");
  Field<bool> selection = params.extract_input<Field<bool>>("Selection");

  /* Use another multi-function operation to make sure the input radius is greater than zero.
   * TODO: Use mutable multi-function once that is supported. */
  static fn::CustomMF_SI_SO<float, float> max_zero_fn(
      __func__, [](float value) { return std::max(0.0f, value); });
  auto max_zero_op = std::make_shared<FieldOperation>(
      FieldOperation(max_zero_fn, {std::move(radius)}));
  Field<float> positive_radius(std::move(max_zero_op), 0);

  const NodeGeometryMeshToPoints &storage = node_storage(params.node());
  const GeometryNodeMeshToPointsMode mode = (GeometryNodeMeshToPointsMode)storage.mode;

  geometry_set.modify_geometry_sets([&](GeometrySet &geometry_set) {
    switch (mode) {
      case GEO_NODE_MESH_TO_POINTS_VERTICES:
        geometry_set_mesh_to_points(
            geometry_set, position, positive_radius, selection, ATTR_DOMAIN_POINT);
        break;
      case GEO_NODE_MESH_TO_POINTS_EDGES:
        geometry_set_mesh_to_points(
            geometry_set, position, positive_radius, selection, ATTR_DOMAIN_EDGE);
        break;
      case GEO_NODE_MESH_TO_POINTS_FACES:
        geometry_set_mesh_to_points(
            geometry_set, position, positive_radius, selection, ATTR_DOMAIN_FACE);
        break;
      case GEO_NODE_MESH_TO_POINTS_CORNERS:
        geometry_set_mesh_to_points(
            geometry_set, position, positive_radius, selection, ATTR_DOMAIN_CORNER);
        break;
    }
  });

  params.set_output("Points", std::move(geometry_set));
}

}  // namespace blender::nodes::node_geo_mesh_to_points_cc

void register_node_type_geo_mesh_to_points()
{
  namespace file_ns = blender::nodes::node_geo_mesh_to_points_cc;

  static bNodeType ntype;

  geo_node_type_base(&ntype, GEO_NODE_MESH_TO_POINTS, "Mesh to Points", NODE_CLASS_GEOMETRY);
  ntype.declare = file_ns::node_declare;
  ntype.geometry_node_execute = file_ns::node_geo_exec;
  node_type_init(&ntype, file_ns::node_init);
  ntype.draw_buttons = file_ns::node_layout;
  node_type_storage(
      &ntype, "NodeGeometryMeshToPoints", node_free_standard_storage, node_copy_standard_storage);
  nodeRegisterType(&ntype);
}

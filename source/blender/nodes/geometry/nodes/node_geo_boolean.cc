/* SPDX-FileCopyrightText: 2023 Blender Foundation
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#include "BKE_geometry_set_instances.hh"
#include "BKE_mesh_boolean_convert.hh"

#include "DNA_mesh_types.h"
#include "DNA_object_types.h"

#include "UI_interface.h"
#include "UI_resources.h"

#include "node_geometry_util.hh"

namespace blender::nodes::node_geo_boolean_cc {

static void node_declare(NodeDeclarationBuilder &b)
{
  b.add_input<decl::Geometry>("Mesh 1").only_realized_data().supported_type(
      GeometryComponent::Type::Mesh);
  b.add_input<decl::Geometry>("Mesh 2").multi_input().supported_type(
      GeometryComponent::Type::Mesh);
  b.add_input<decl::Bool>("Self Intersection");
  b.add_input<decl::Bool>("Hole Tolerant");
  b.add_output<decl::Geometry>("Mesh").propagate_all();
  b.add_output<decl::Bool>("Intersecting Edges").field_on_all();
}

static void node_layout(uiLayout *layout, bContext * /*C*/, PointerRNA *ptr)
{
  uiItemR(layout, ptr, "operation", 0, "", ICON_NONE);
}

struct AttributeOutputs {
  AnonymousAttributeIDPtr intersecting_edges_id;
};

static void node_update(bNodeTree *ntree, bNode *node)
{
  GeometryNodeBooleanOperation operation = (GeometryNodeBooleanOperation)node->custom1;

  bNodeSocket *geometry_1_socket = static_cast<bNodeSocket *>(node->inputs.first);
  bNodeSocket *geometry_2_socket = geometry_1_socket->next;

  switch (operation) {
    case GEO_NODE_BOOLEAN_INTERSECT:
    case GEO_NODE_BOOLEAN_UNION:
      bke::nodeSetSocketAvailability(ntree, geometry_1_socket, false);
      node_sock_label(geometry_2_socket, "Mesh");
      break;
    case GEO_NODE_BOOLEAN_DIFFERENCE:
      bke::nodeSetSocketAvailability(ntree, geometry_1_socket, true);
      node_sock_label(geometry_2_socket, "Mesh 2");
      break;
  }
}

static void node_init(bNodeTree * /*tree*/, bNode *node)
{
  node->custom1 = GEO_NODE_BOOLEAN_DIFFERENCE;
}

static void node_geo_exec(GeoNodeExecParams params)
{
#ifdef WITH_GMP
  GeometryNodeBooleanOperation operation = (GeometryNodeBooleanOperation)params.node().custom1;
  const bool use_self = params.get_input<bool>("Self Intersection");
  const bool hole_tolerant = params.get_input<bool>("Hole Tolerant");

  Vector<const Mesh *> meshes;
  VectorSet<Material *> materials;
  Vector<Array<short>> material_remaps;

  GeometrySet set_a;
  if (operation == GEO_NODE_BOOLEAN_DIFFERENCE) {
    set_a = params.extract_input<GeometrySet>("Mesh 1");
    /* Note that it technically wouldn't be necessary to realize the instances for the first
     * geometry input, but the boolean code expects the first shape for the difference operation
     * to be a single mesh. */
    if (const Mesh *mesh_in_a = set_a.get_mesh_for_read()) {
      meshes.append(mesh_in_a);
      if (mesh_in_a->totcol == 0) {
        /* Necessary for faces using the default material when there are no material slots. */
        materials.add(nullptr);
      }
      else {
        materials.add_multiple({mesh_in_a->mat, mesh_in_a->totcol});
      }
      material_remaps.append({});
    }
  }

  Vector<GeometrySet> geometry_sets = params.extract_input<Vector<GeometrySet>>("Mesh 2");

  for (const GeometrySet &geometry : geometry_sets) {
    if (const Mesh *mesh = geometry.get_mesh_for_read()) {
      meshes.append(mesh);
      Array<short> map(mesh->totcol);
      for (const int i : IndexRange(mesh->totcol)) {
        Material *material = mesh->mat[i];
        map[i] = material ? materials.index_of_or_add(material) : -1;
      }
      material_remaps.append(std::move(map));
    }
  }

  AttributeOutputs attribute_outputs;
  attribute_outputs.intersecting_edges_id = params.get_output_anonymous_attribute_id_if_needed(
      "Intersecting Edges");

  Vector<int> intersecting_edges;
  Mesh *result = blender::meshintersect::direct_mesh_boolean(
      meshes,
      {},
      float4x4::identity(),
      material_remaps,
      use_self,
      hole_tolerant,
      operation,
      attribute_outputs.intersecting_edges_id ? &intersecting_edges : nullptr);
  if (!result) {
    params.set_default_remaining_outputs();
    return;
  }

  MEM_SAFE_FREE(result->mat);
  result->mat = static_cast<Material **>(
      MEM_malloc_arrayN(materials.size(), sizeof(Material *), __func__));
  result->totcol = materials.size();
  MutableSpan(result->mat, result->totcol).copy_from(materials);

  /* Store intersecting edges in attribute. */
  if (attribute_outputs.intersecting_edges_id) {
    MutableAttributeAccessor attributes = result->attributes_for_write();
    SpanAttributeWriter<bool> selection = attributes.lookup_or_add_for_write_only_span<bool>(
        attribute_outputs.intersecting_edges_id.get(), ATTR_DOMAIN_EDGE);

    selection.span.fill(false);
    for (const int i : intersecting_edges) {
      selection.span[i] = true;
    }
    selection.finish();
  }

  params.set_output("Mesh", GeometrySet::create_with_mesh(result));
#else
  params.error_message_add(NodeWarningType::Error,
                           TIP_("Disabled, Blender was compiled without GMP"));
  params.set_default_remaining_outputs();
#endif
}

}  // namespace blender::nodes::node_geo_boolean_cc

void register_node_type_geo_boolean()
{
  namespace file_ns = blender::nodes::node_geo_boolean_cc;

  static bNodeType ntype;

  geo_node_type_base(&ntype, GEO_NODE_MESH_BOOLEAN, "Mesh Boolean", NODE_CLASS_GEOMETRY);
  ntype.declare = file_ns::node_declare;
  ntype.draw_buttons = file_ns::node_layout;
  ntype.updatefunc = file_ns::node_update;
  ntype.initfunc = file_ns::node_init;
  ntype.geometry_node_execute = file_ns::node_geo_exec;
  nodeRegisterType(&ntype);
}

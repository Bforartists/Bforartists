/* SPDX-License-Identifier: GPL-2.0-or-later */

#include "BLI_task.hh"

#include "BKE_mesh.hh"
#include "BKE_mesh_runtime.h"

#include "BKE_attribute_math.hh"

#include "node_geometry_util.hh"

namespace blender::nodes::node_geo_flip_faces_cc {

static void node_declare(NodeDeclarationBuilder &b)
{
  b.add_input<decl::Geometry>(N_("Mesh")).supported_type(GEO_COMPONENT_TYPE_MESH);
  b.add_input<decl::Bool>(N_("Selection")).default_value(true).hide_value().field_on_all();
  b.add_output<decl::Geometry>(N_("Mesh")).propagate_all();
}

static void mesh_flip_faces(Mesh &mesh, const Field<bool> &selection_field)
{
  if (mesh.totpoly == 0) {
    return;
  }
  bke::MeshFieldContext field_context{mesh, ATTR_DOMAIN_FACE};
  fn::FieldEvaluator evaluator{field_context, mesh.totpoly};
  evaluator.add(selection_field);
  evaluator.evaluate();
  const IndexMask selection = evaluator.get_evaluated_as_mask(0);

  const Span<MPoly> polys = mesh.polys();
  MutableSpan<int> corner_verts = mesh.corner_verts_for_write();
  MutableSpan<int> corner_edges = mesh.corner_edges_for_write();

  threading::parallel_for(selection.index_range(), 1024, [&](const IndexRange range) {
    for (const int i : selection.slice(range)) {
      const IndexRange poly(polys[i].loopstart, polys[i].totloop);
      for (const int j : IndexRange(poly.size() / 2)) {
        const int a = poly[j + 1];
        const int b = poly.last(j);
        std::swap(corner_verts[a], corner_verts[b]);
        std::swap(corner_edges[a - 1], corner_edges[b]);
      }
    }
  });

  MutableAttributeAccessor attributes = mesh.attributes_for_write();
  attributes.for_all(
      [&](const bke::AttributeIDRef &attribute_id, const AttributeMetaData &meta_data) {
        if (meta_data.data_type == CD_PROP_STRING) {
          return true;
        }
        if (meta_data.domain != ATTR_DOMAIN_CORNER) {
          return true;
        }
        if (ELEM(attribute_id.name(), ".corner_vert", ".corner_edge")) {
          return true;
        }
        GSpanAttributeWriter attribute = attributes.lookup_for_write_span(attribute_id);
        attribute_math::convert_to_static_type(meta_data.data_type, [&](auto dummy) {
          using T = decltype(dummy);
          MutableSpan<T> dst_span = attribute.span.typed<T>();
          threading::parallel_for(selection.index_range(), 1024, [&](const IndexRange range) {
            for (const int i : selection.slice(range)) {
              const IndexRange poly(polys[i].loopstart, polys[i].totloop);
              dst_span.slice(poly.drop_front(1)).reverse();
            }
          });
        });
        attribute.finish();
        return true;
      });
}

static void node_geo_exec(GeoNodeExecParams params)
{
  GeometrySet geometry_set = params.extract_input<GeometrySet>("Mesh");

  const Field<bool> selection_field = params.extract_input<Field<bool>>("Selection");

  geometry_set.modify_geometry_sets([&](GeometrySet &geometry_set) {
    if (Mesh *mesh = geometry_set.get_mesh_for_write()) {
      mesh_flip_faces(*mesh, selection_field);
    }
  });

  params.set_output("Mesh", std::move(geometry_set));
}

}  // namespace blender::nodes::node_geo_flip_faces_cc

void register_node_type_geo_flip_faces()
{
  namespace file_ns = blender::nodes::node_geo_flip_faces_cc;

  static bNodeType ntype;

  geo_node_type_base(&ntype, GEO_NODE_FLIP_FACES, "Flip Faces", NODE_CLASS_GEOMETRY);
  ntype.geometry_node_execute = file_ns::node_geo_exec;
  ntype.declare = file_ns::node_declare;
  nodeRegisterType(&ntype);
}

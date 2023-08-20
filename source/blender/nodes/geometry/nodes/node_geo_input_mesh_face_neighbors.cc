/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#include "BLI_array_utils.hh"

#include "BKE_mesh.hh"

#include "node_geometry_util.hh"

namespace blender::nodes::node_geo_input_mesh_face_neighbors_cc {

static void node_declare(NodeDeclarationBuilder &b)
{
  b.add_output<decl::Int>("Vertex Count")
      .field_source()
      .description("Number of edges or points in the face");
  b.add_output<decl::Int>("Face Count")
      .field_source()
      .description("Number of faces which share an edge with the face");
}

static VArray<int> construct_neighbor_count_varray(const Mesh &mesh, const eAttrDomain domain)
{
  const OffsetIndices faces = mesh.faces();
  const Span<int> corner_edges = mesh.corner_edges();

  Array<int> edge_count(mesh.totedge, 0);
  array_utils::count_indices(corner_edges, edge_count);

  Array<int> face_count(faces.size(), 0);
  for (const int face_index : faces.index_range()) {
    for (const int edge : corner_edges.slice(faces[face_index])) {
      face_count[face_index] += edge_count[edge] - 1;
    }
  }

  return mesh.attributes().adapt_domain<int>(
      VArray<int>::ForContainer(std::move(face_count)), ATTR_DOMAIN_FACE, domain);
}

class FaceNeighborCountFieldInput final : public bke::MeshFieldInput {
 public:
  FaceNeighborCountFieldInput()
      : bke::MeshFieldInput(CPPType::get<int>(), "Face Neighbor Count Field")
  {
    category_ = Category::Generated;
  }

  GVArray get_varray_for_context(const Mesh &mesh,
                                 const eAttrDomain domain,
                                 const IndexMask & /*mask*/) const final
  {
    return construct_neighbor_count_varray(mesh, domain);
  }

  uint64_t hash() const override
  {
    /* Some random constant hash. */
    return 823543774;
  }

  bool is_equal_to(const fn::FieldNode &other) const override
  {
    return dynamic_cast<const FaceNeighborCountFieldInput *>(&other) != nullptr;
  }

  std::optional<eAttrDomain> preferred_domain(const Mesh & /*mesh*/) const override
  {
    return ATTR_DOMAIN_FACE;
  }
};

static VArray<int> construct_vertex_count_varray(const Mesh &mesh, const eAttrDomain domain)
{
  const OffsetIndices faces = mesh.faces();
  return mesh.attributes().adapt_domain<int>(
      VArray<int>::ForFunc(faces.size(),
                           [faces](const int i) -> float { return faces[i].size(); }),
      ATTR_DOMAIN_FACE,
      domain);
}

class FaceVertexCountFieldInput final : public bke::MeshFieldInput {
 public:
  FaceVertexCountFieldInput() : bke::MeshFieldInput(CPPType::get<int>(), "Vertex Count Field")
  {
    category_ = Category::Generated;
  }

  GVArray get_varray_for_context(const Mesh &mesh,
                                 const eAttrDomain domain,
                                 const IndexMask & /*mask*/) const final
  {
    return construct_vertex_count_varray(mesh, domain);
  }

  uint64_t hash() const override
  {
    /* Some random constant hash. */
    return 236235463634;
  }

  bool is_equal_to(const fn::FieldNode &other) const override
  {
    return dynamic_cast<const FaceVertexCountFieldInput *>(&other) != nullptr;
  }

  std::optional<eAttrDomain> preferred_domain(const Mesh & /*mesh*/) const override
  {
    return ATTR_DOMAIN_FACE;
  }
};

static void node_geo_exec(GeoNodeExecParams params)
{
  Field<int> vertex_count_field{std::make_shared<FaceVertexCountFieldInput>()};
  Field<int> neighbor_count_field{std::make_shared<FaceNeighborCountFieldInput>()};
  params.set_output("Vertex Count", std::move(vertex_count_field));
  params.set_output("Face Count", std::move(neighbor_count_field));
}

static void node_register()
{
  static bNodeType ntype;
  geo_node_type_base(
      &ntype, GEO_NODE_INPUT_MESH_FACE_NEIGHBORS, "Face Neighbors", NODE_CLASS_INPUT);
  blender::bke::node_type_size_preset(&ntype, blender::bke::eNodeSizePreset::MIDDLE);
  ntype.declare = node_declare;
  ntype.geometry_node_execute = node_geo_exec;
  nodeRegisterType(&ntype);
}
NOD_REGISTER_NODE(node_register)

}  // namespace blender::nodes::node_geo_input_mesh_face_neighbors_cc

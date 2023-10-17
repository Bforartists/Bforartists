/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#include "node_geometry_util.hh"

#include "UI_interface.hh"
#include "UI_resources.hh"

#include "DNA_mesh_types.h"
#include "DNA_meshdata_types.h"

#include "BLI_task.hh"

#include "BKE_curves.hh"
#include "BKE_grease_pencil.hh"
#include "BKE_material.h"

namespace blender::nodes::node_geo_material_selection_cc {

static void node_declare(NodeDeclarationBuilder &b)
{
  b.add_input<decl::Material>("Material").hide_label(true);
  b.add_output<decl::Bool>("Selection").field_source();
}

static VArray<bool> select_by_material(const Span<Material *> materials,
                                       const Material *material,
                                       const AttributeAccessor &attributes,
                                       const eAttrDomain domain,
                                       const IndexMask &domain_mask)
{
  const int domain_size = attributes.domain_size(domain);
  Vector<int> slots;
  for (const int slot_i : materials.index_range()) {
    if (materials[slot_i] == material) {
      slots.append(slot_i);
    }
  }
  if (slots.is_empty()) {
    return VArray<bool>::ForSingle(false, domain_size);
  }

  const VArray<int> material_indices = *attributes.lookup_or_default<int>(
      "material_index", domain, 0);
  if (const std::optional<int> single = material_indices.get_if_single()) {
    return VArray<bool>::ForSingle(slots.contains(*single), domain_size);
  }

  const VArraySpan<int> material_indices_span(material_indices);
  Array<bool> domain_selection(domain_mask.min_array_size());
  domain_mask.foreach_index_optimized<int>(GrainSize(1024), [&](const int domain_index) {
    const int slot_i = material_indices_span[domain_index];
    domain_selection[domain_index] = slots.contains(slot_i);
  });
  return VArray<bool>::ForContainer(std::move(domain_selection));
}

class MaterialSelectionFieldInput final : public bke::GeometryFieldInput {
  Material *material_;

 public:
  MaterialSelectionFieldInput(Material *material)
      : bke::GeometryFieldInput(CPPType::get<bool>(), "Material Selection node"),
        material_(material)
  {
    category_ = Category::Generated;
  }

  GVArray get_varray_for_context(const bke::GeometryFieldContext &context,
                                 const IndexMask &mask) const final
  {
    switch (context.type()) {
      case GeometryComponent::Type::Mesh: {
        const Mesh *mesh = context.mesh();
        if (!mesh) {
          return {};
        }
        const eAttrDomain domain = context.domain();
        const IndexMask domain_mask = (domain == ATTR_DOMAIN_FACE) ? mask :
                                                                     IndexMask(mesh->faces_num);
        const AttributeAccessor attributes = mesh->attributes();
        VArray<bool> selection = select_by_material(
            {mesh->mat, mesh->totcol}, material_, attributes, ATTR_DOMAIN_FACE, domain_mask);
        return attributes.adapt_domain<bool>(std::move(selection), ATTR_DOMAIN_FACE, domain);
      }
      case GeometryComponent::Type::GreasePencil: {
        const bke::CurvesGeometry *curves = context.curves_or_strokes();
        if (!curves) {
          return {};
        }
        const eAttrDomain domain = context.domain();
        const IndexMask domain_mask = (domain == ATTR_DOMAIN_CURVE) ?
                                          mask :
                                          IndexMask(curves->curves_num());
        const AttributeAccessor attributes = curves->attributes();
        const VArray<int> material_indices = *attributes.lookup_or_default<int>(
            "material_index", ATTR_DOMAIN_CURVE, 0);
        const GreasePencil &grease_pencil = *context.grease_pencil();
        VArray<bool> selection = select_by_material(
            {grease_pencil.material_array, grease_pencil.material_array_num},
            material_,
            attributes,
            ATTR_DOMAIN_CURVE,
            domain_mask);
        return attributes.adapt_domain<bool>(std::move(selection), ATTR_DOMAIN_CURVE, domain);
      }
      default:
        return {};
    }
  }

  uint64_t hash() const override
  {
    return get_default_hash(material_);
  }

  bool is_equal_to(const fn::FieldNode &other) const override
  {
    if (const MaterialSelectionFieldInput *other_material_selection =
            dynamic_cast<const MaterialSelectionFieldInput *>(&other))
    {
      return material_ == other_material_selection->material_;
    }
    return false;
  }

  std::optional<eAttrDomain> preferred_domain(
      const GeometryComponent & /*component*/) const override
  {
    return ATTR_DOMAIN_FACE;
  }
};

static void node_geo_exec(GeoNodeExecParams params)
{
  Material *material = params.extract_input<Material *>("Material");
  Field<bool> material_field{std::make_shared<MaterialSelectionFieldInput>(material)};
  params.set_output("Selection", std::move(material_field));
}

static void node_register()
{
  static bNodeType ntype;

  geo_node_type_base(
      &ntype, GEO_NODE_MATERIAL_SELECTION, "Material Selection", NODE_CLASS_GEOMETRY);
  ntype.declare = node_declare;
  ntype.geometry_node_execute = node_geo_exec;
  nodeRegisterType(&ntype);
}
NOD_REGISTER_NODE(node_register)

}  // namespace blender::nodes::node_geo_material_selection_cc

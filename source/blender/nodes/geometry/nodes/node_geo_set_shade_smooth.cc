/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#include "DNA_mesh_types.h"

#include "UI_interface.hh"
#include "UI_resources.hh"

#include "NOD_rna_define.hh"

#include "RNA_enum_types.hh"

#include "node_geometry_util.hh"

namespace blender::nodes::node_geo_set_shade_smooth_cc {

static void node_declare(NodeDeclarationBuilder &b)
{
  b.add_input<decl::Geometry>("Geometry").supported_type(GeometryComponent::Type::Mesh);
  b.add_input<decl::Bool>("Selection").default_value(true).hide_value().field_on_all();
  b.add_input<decl::Bool>("Shade Smooth").default_value(true).field_on_all();
  b.add_output<decl::Geometry>("Geometry").propagate_all();
}

static void node_layout(uiLayout *layout, bContext * /*C*/, PointerRNA *ptr)
{
  uiItemR(layout, ptr, "domain", UI_ITEM_R_EXPAND, nullptr, ICON_NONE);
}

static void node_init(bNodeTree * /*tree*/, bNode *node)
{
  node->custom1 = ATTR_DOMAIN_FACE;
}

/**
 * When the `sharp_face` attribute doesn't exist, all faces are considered smooth. If all faces
 * are selected and the sharp value is a constant false value, we can remove the attribute instead
 * as an optimization to avoid storing it and propagating it in the future.
 */
static bool try_removing_sharp_attribute(Mesh &mesh,
                                         const StringRef name,
                                         const Field<bool> &selection_field,
                                         const Field<bool> &sharp_field)
{
  if (selection_field.node().depends_on_input() || sharp_field.node().depends_on_input()) {
    return false;
  }
  const bool selection = fn::evaluate_constant_field(selection_field);
  if (!selection) {
    return true;
  }
  const bool sharp = fn::evaluate_constant_field(sharp_field);
  if (sharp) {
    return false;
  }
  mesh.attributes_for_write().remove(name);
  return true;
}

static void set_sharp(Mesh &mesh,
                      const eAttrDomain domain,
                      const StringRef name,
                      const Field<bool> &selection_field,
                      const Field<bool> &sharp_field)
{
  const int domain_size = mesh.attributes().domain_size(domain);
  if (mesh.attributes().domain_size(domain) == 0) {
    return;
  }
  if (try_removing_sharp_attribute(mesh, name, selection_field, sharp_field)) {
    return;
  }

  MutableAttributeAccessor attributes = mesh.attributes_for_write();
  AttributeWriter<bool> sharp = attributes.lookup_or_add_for_write<bool>(name, domain);

  const bke::MeshFieldContext field_context{mesh, domain};
  fn::FieldEvaluator evaluator{field_context, domain_size};
  evaluator.set_selection(selection_field);
  evaluator.add_with_destination(sharp_field, sharp.varray);
  evaluator.evaluate();

  sharp.finish();
}

static void node_geo_exec(GeoNodeExecParams params)
{
  GeometrySet geometry_set = params.extract_input<GeometrySet>("Geometry");
  const eAttrDomain domain = eAttrDomain(params.node().custom1);
  Field<bool> selection_field = params.extract_input<Field<bool>>("Selection");
  Field<bool> smooth_field = params.extract_input<Field<bool>>("Shade Smooth");

  geometry_set.modify_geometry_sets([&](GeometrySet &geometry_set) {
    if (Mesh *mesh = geometry_set.get_mesh_for_write()) {
      set_sharp(*mesh,
                domain,
                domain == ATTR_DOMAIN_FACE ? "sharp_face" : "sharp_edge",
                selection_field,
                fn::invert_boolean_field(smooth_field));
    }
  });
  params.set_output("Geometry", std::move(geometry_set));
}

static void node_rna(StructRNA *srna)
{
  RNA_def_node_enum(srna,
                    "domain",
                    "Domain",
                    "",
                    rna_enum_attribute_domain_edge_face_items,
                    NOD_inline_enum_accessors(custom1));
}

static void node_register()
{
  static bNodeType ntype;

  geo_node_type_base(&ntype, GEO_NODE_SET_SHADE_SMOOTH, "Set Shade Smooth", NODE_CLASS_GEOMETRY);
  ntype.geometry_node_execute = node_geo_exec;
  ntype.declare = node_declare;
  ntype.initfunc = node_init;
  ntype.draw_buttons = node_layout;
  nodeRegisterType(&ntype);

  node_rna(ntype.rna_ext.srna);
}
NOD_REGISTER_NODE(node_register)

}  // namespace blender::nodes::node_geo_set_shade_smooth_cc

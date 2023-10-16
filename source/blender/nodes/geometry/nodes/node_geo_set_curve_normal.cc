/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#include "BKE_curves.hh"
#include "BKE_grease_pencil.hh"

#include "UI_interface.hh"
#include "UI_resources.hh"

#include "NOD_rna_define.hh"

#include "RNA_enum_types.hh"

#include "node_geometry_util.hh"

namespace blender::nodes::node_geo_set_curve_normal_cc {

static void node_declare(NodeDeclarationBuilder &b)
{
  b.add_input<decl::Geometry>("Curve").supported_type(
      {GeometryComponent::Type::Curve, GeometryComponent::Type::GreasePencil});
  b.add_input<decl::Bool>("Selection").default_value(true).hide_value().field_on_all();
  b.add_output<decl::Geometry>("Curve").propagate_all();
}

static void node_layout(uiLayout *layout, bContext * /*C*/, PointerRNA *ptr)
{
  uiItemR(layout, ptr, "mode", UI_ITEM_NONE, "", ICON_NONE);
}

static void node_init(bNodeTree * /*tree*/, bNode *node)
{
  node->custom1 = NORMAL_MODE_MINIMUM_TWIST;
}

static void set_curve_normal(bke::CurvesGeometry &curves,
                             const NormalMode mode,
                             const fn::FieldContext field_context,
                             const Field<bool> &selection_field)
{
  fn::FieldEvaluator evaluator{field_context, curves.curves_num()};
  evaluator.set_selection(selection_field);
  evaluator.evaluate();
  const IndexMask selection = evaluator.get_evaluated_selection_as_mask();
  index_mask::masked_fill<int8_t>(curves.normal_mode_for_write(), mode, selection);
  curves.tag_normals_changed();
}

static void set_grease_pencil_normal(GreasePencil &grease_pencil,
                                     const NormalMode mode,
                                     const Field<bool> &selection_field)
{
  using namespace blender::bke::greasepencil;
  for (const int layer_index : grease_pencil.layers().index_range()) {
    Drawing *drawing = get_eval_grease_pencil_layer_drawing_for_write(grease_pencil, layer_index);
    if (drawing == nullptr) {
      continue;
    }
    bke::CurvesGeometry &curves = drawing->strokes_for_write();
    const bke::GreasePencilLayerFieldContext field_context(
        grease_pencil, ATTR_DOMAIN_CURVE, layer_index);
    set_curve_normal(curves, mode, field_context, selection_field);
  }
}

static void node_geo_exec(GeoNodeExecParams params)
{
  const NormalMode mode = static_cast<NormalMode>(params.node().custom1);

  GeometrySet geometry_set = params.extract_input<GeometrySet>("Curve");
  Field<bool> selection_field = params.extract_input<Field<bool>>("Selection");

  geometry_set.modify_geometry_sets([&](GeometrySet &geometry_set) {
    if (Curves *curves_id = geometry_set.get_curves_for_write()) {
      bke::CurvesGeometry &curves = curves_id->geometry.wrap();
      const bke::CurvesFieldContext field_context{curves, ATTR_DOMAIN_CURVE};
      set_curve_normal(curves, mode, field_context, selection_field);
    }
    if (geometry_set.has_grease_pencil()) {
      set_grease_pencil_normal(*geometry_set.get_grease_pencil_for_write(), mode, selection_field);
    }
  });

  params.set_output("Curve", std::move(geometry_set));
}

static void node_rna(StructRNA *srna)
{
  RNA_def_node_enum(srna,
                    "mode",
                    "Mode",
                    "Mode for curve normal evaluation",
                    rna_enum_curve_normal_mode_items,
                    NOD_inline_enum_accessors(custom1));
}

static void node_register()
{
  static bNodeType ntype;
  geo_node_type_base(&ntype, GEO_NODE_SET_CURVE_NORMAL, "Set Curve Normal", NODE_CLASS_GEOMETRY);
  ntype.declare = node_declare;
  ntype.geometry_node_execute = node_geo_exec;
  ntype.initfunc = node_init;
  ntype.draw_buttons = node_layout;

  nodeRegisterType(&ntype);

  node_rna(ntype.rna_ext.srna);
}
NOD_REGISTER_NODE(node_register)

}  // namespace blender::nodes::node_geo_set_curve_normal_cc

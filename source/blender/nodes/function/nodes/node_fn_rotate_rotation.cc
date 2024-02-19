/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#include "BLI_math_quaternion.hh"

#include "UI_interface.hh"
#include "UI_resources.hh"

#include "NOD_rna_define.hh"

#include "node_function_util.hh"

namespace blender::nodes::node_fn_rotate_rotation_cc {

enum class RotationSpace {
  Global = 0,
  Local = 1,
};

static void node_declare(NodeDeclarationBuilder &b)
{
  b.is_function_node();
  b.add_input<decl::Rotation>("Rotation");
  b.add_input<decl::Rotation>("Rotate By");
  b.add_output<decl::Rotation>("Rotation");
};

static void node_layout(uiLayout *layout, bContext * /*C*/, PointerRNA *ptr)
{
  uiItemR(layout, ptr, "rotation_space", UI_ITEM_R_EXPAND, nullptr, ICON_NONE);
}

static void node_build_multi_function(NodeMultiFunctionBuilder &builder)
{
  switch (RotationSpace(builder.node().custom1)) {
    case RotationSpace::Global: {
      static auto fn = mf::build::SI2_SO<math::Quaternion, math::Quaternion, math::Quaternion>(
          "Rotate Rotation Global", [](math::Quaternion a, math::Quaternion b) { return b * a; });
      builder.set_matching_fn(fn);
      break;
    }
    case RotationSpace::Local: {
      static auto fn = mf::build::SI2_SO<math::Quaternion, math::Quaternion, math::Quaternion>(
          "Rotate Rotation Local", [](math::Quaternion a, math::Quaternion b) { return a * b; });
      builder.set_matching_fn(fn);
      break;
    }
  }
}

static void node_rna(StructRNA *srna)
{
  static const EnumPropertyItem space_items[] = {
      {int(RotationSpace::Global),
       "GLOBAL",
       ICON_NONE,
       "Global",
       "Rotate the input rotation in global space"},
      {int(RotationSpace::Local),
       "LOCAL",
       ICON_NONE,
       "Local",
       "Rotate the input rotation in its local space"},
      {0, nullptr, 0, nullptr, nullptr},
  };

  RNA_def_node_enum(srna,
                    "rotation_space",
                    "Space",
                    "Base orientation for the rotation",
                    space_items,
                    NOD_inline_enum_accessors(custom1));
}

static void node_register()
{
  static bNodeType ntype;
  fn_node_type_base(&ntype, FN_NODE_ROTATE_ROTATION, "Rotate Rotation", NODE_CLASS_CONVERTER);
  ntype.declare = node_declare;
  ntype.draw_buttons = node_layout;
  ntype.build_multi_function = node_build_multi_function;
  nodeRegisterType(&ntype);

  node_rna(ntype.rna_ext.srna);
}
NOD_REGISTER_NODE(node_register)

}  // namespace blender::nodes::node_fn_rotate_rotation_cc

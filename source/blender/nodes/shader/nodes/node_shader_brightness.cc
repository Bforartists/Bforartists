/* SPDX-FileCopyrightText: 2006 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#include "node_shader_util.hh"

namespace blender::nodes::node_shader_brightness_cc {

static void node_declare(NodeDeclarationBuilder &b)
{
  b.add_input<decl::Color>("Color").default_value({1.0f, 1.0f, 1.0f, 1.0f});
  b.add_input<decl::Float>("Bright").default_value(0.0f).min(-100.0f).max(100.0f);
  b.add_input<decl::Float>("Contrast").default_value(0.0f).min(-100.0f).max(100.0f);
  b.add_output<decl::Color>("Color");
}

static int gpu_shader_brightcontrast(GPUMaterial *mat,
                                     bNode *node,
                                     bNodeExecData * /*execdata*/,
                                     GPUNodeStack *in,
                                     GPUNodeStack *out)
{
  return GPU_stack_link(mat, node, "brightness_contrast", in, out);
}

NODE_SHADER_MATERIALX_BEGIN
#ifdef WITH_MATERIALX
{
  NodeItem color = get_input_value("Color", NodeItem::Type::Color3);
  NodeItem bright = get_input_value("Bright", NodeItem::Type::Float);
  NodeItem contrast = get_input_value("Contrast", NodeItem::Type::Float);

  /* This formula was given from OSL shader code in Cycles. */
  return (bright + color * (contrast + val(1.0f)) - contrast * val(0.5f)).max(val(0.0f));
}
#endif
NODE_SHADER_MATERIALX_END

}  // namespace blender::nodes::node_shader_brightness_cc

void register_node_type_sh_brightcontrast()
{
  namespace file_ns = blender::nodes::node_shader_brightness_cc;

  static bNodeType ntype;

  sh_node_type_base(&ntype, SH_NODE_BRIGHTCONTRAST, "Brightness/Contrast", NODE_CLASS_OP_COLOR);
  ntype.declare = file_ns::node_declare;
  ntype.gpu_fn = file_ns::gpu_shader_brightcontrast;
  ntype.materialx_fn = file_ns::node_shader_materialx;

  nodeRegisterType(&ntype);
}

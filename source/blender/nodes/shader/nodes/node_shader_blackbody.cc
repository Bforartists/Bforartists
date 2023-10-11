/* SPDX-FileCopyrightText: 2005 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#include "node_shader_util.hh"

#include "IMB_colormanagement.h"

namespace blender::nodes::node_shader_blackbody_cc {

static void node_declare(NodeDeclarationBuilder &b)
{
  b.add_input<decl::Float>("Temperature").default_value(1500.0f).min(800.0f).max(12000.0f);
  b.add_output<decl::Color>("Color");
}

static int node_shader_gpu_blackbody(GPUMaterial *mat,
                                     bNode *node,
                                     bNodeExecData * /*execdata*/,
                                     GPUNodeStack *in,
                                     GPUNodeStack *out)
{
  const int size = CM_TABLE + 1;
  float *data = static_cast<float *>(MEM_mallocN(sizeof(float) * size * 4, "blackbody texture"));

  IMB_colormanagement_blackbody_temperature_to_rgb_table(data, size, 800.0f, 12000.0f);

  float layer;
  GPUNodeLink *ramp_texture = GPU_color_band(mat, size, data, &layer);

  return GPU_stack_link(mat, node, "node_blackbody", in, out, ramp_texture, GPU_constant(&layer));
}

NODE_SHADER_MATERIALX_BEGIN
#ifdef WITH_MATERIALX
{
  /* TODO: This node doesn't have an implementation in MaterialX 1.38.6.
   * It's added in MaterialX 1.38.8. Uncomment this code after switching to 1.38.8.
   *
   * NodeItem temperature = get_input_value("Temperature", NodeItem::Type::Float);

   * NodeItem res = create_node("blackbody", NodeItem::Type::Color3);
   * res.set_input("temperature", temperature);
   * return res; */
  NodeItem res = empty();
  return res;
}
#endif
NODE_SHADER_MATERIALX_END

}  // namespace blender::nodes::node_shader_blackbody_cc

/* node type definition */
void register_node_type_sh_blackbody()
{
  namespace file_ns = blender::nodes::node_shader_blackbody_cc;

  static bNodeType ntype;

  sh_node_type_base(&ntype, SH_NODE_BLACKBODY, "Blackbody", NODE_CLASS_CONVERTER);
  ntype.declare = file_ns::node_declare;
  blender::bke::node_type_size_preset(&ntype, blender::bke::eNodeSizePreset::MIDDLE);
  ntype.gpu_fn = file_ns::node_shader_gpu_blackbody;
  ntype.materialx_fn = file_ns::node_shader_materialx;

  nodeRegisterType(&ntype);
}

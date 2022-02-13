/* SPDX-License-Identifier: GPL-2.0-or-later
 * Copyright 2005 Blender Foundation. All rights reserved. */

#include "node_shader_util.hh"

namespace blender::nodes::node_shader_object_info_cc {

static void node_declare(NodeDeclarationBuilder &b)
{
  b.add_output<decl::Vector>(N_("Location"));
  b.add_output<decl::Color>(N_("Color"));
  b.add_output<decl::Float>(N_("Object Index"));
  b.add_output<decl::Float>(N_("Material Index"));
  b.add_output<decl::Float>(N_("Random"));
}

static int node_shader_gpu_object_info(GPUMaterial *mat,
                                       bNode *node,
                                       bNodeExecData *UNUSED(execdata),
                                       GPUNodeStack *in,
                                       GPUNodeStack *out)
{
  Material *ma = GPU_material_get_material(mat);
  float index = ma ? ma->index : 0.0f;
  return GPU_stack_link(mat,
                        node,
                        "node_object_info",
                        in,
                        out,
                        GPU_builtin(GPU_OBJECT_MATRIX),
                        GPU_builtin(GPU_OBJECT_COLOR),
                        GPU_builtin(GPU_OBJECT_INFO),
                        GPU_constant(&index));
}

}  // namespace blender::nodes::node_shader_object_info_cc

void register_node_type_sh_object_info()
{
  namespace file_ns = blender::nodes::node_shader_object_info_cc;

  static bNodeType ntype;

  sh_node_type_base(&ntype, SH_NODE_OBJECT_INFO, "Object Info", NODE_CLASS_INPUT);
  ntype.declare = file_ns::node_declare;
  node_type_gpu(&ntype, file_ns::node_shader_gpu_object_info);

  nodeRegisterType(&ntype);
}

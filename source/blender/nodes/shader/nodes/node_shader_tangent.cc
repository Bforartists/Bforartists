/*
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software Foundation,
 * Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
 *
 * The Original Code is Copyright (C) 2005 Blender Foundation.
 * All rights reserved.
 */

#include "node_shader_util.hh"

namespace blender::nodes::node_shader_tangent_cc {

static void node_declare(NodeDeclarationBuilder &b)
{
  b.add_output<decl::Vector>(N_("Tangent"));
};

static void node_shader_init_tangent(bNodeTree *UNUSED(ntree), bNode *node)
{
  NodeShaderTangent *attr = MEM_cnew<NodeShaderTangent>("NodeShaderTangent");
  attr->axis = SHD_TANGENT_AXIS_Z;
  node->storage = attr;
}

static int node_shader_gpu_tangent(GPUMaterial *mat,
                                   bNode *node,
                                   bNodeExecData *UNUSED(execdata),
                                   GPUNodeStack *in,
                                   GPUNodeStack *out)
{
  NodeShaderTangent *attr = static_cast<NodeShaderTangent *>(node->storage);

  if (attr->direction_type == SHD_TANGENT_UVMAP) {
    return GPU_stack_link(
        mat, node, "node_tangentmap", in, out, GPU_attribute(mat, CD_TANGENT, attr->uv_map));
  }

  GPUNodeLink *orco = GPU_attribute(mat, CD_ORCO, "");

  if (attr->axis == SHD_TANGENT_AXIS_X) {
    GPU_link(mat, "tangent_orco_x", orco, &orco);
  }
  else if (attr->axis == SHD_TANGENT_AXIS_Y) {
    GPU_link(mat, "tangent_orco_y", orco, &orco);
  }
  else {
    GPU_link(mat, "tangent_orco_z", orco, &orco);
  }

  return GPU_stack_link(mat,
                        node,
                        "node_tangent",
                        in,
                        out,
                        GPU_builtin(GPU_WORLD_NORMAL),
                        orco,
                        GPU_builtin(GPU_OBJECT_MATRIX));
}

}  // namespace blender::nodes::node_shader_tangent_cc

/* node type definition */
void register_node_type_sh_tangent()
{
  namespace file_ns = blender::nodes::node_shader_tangent_cc;

  static bNodeType ntype;

  sh_node_type_base(&ntype, SH_NODE_TANGENT, "Tangent", NODE_CLASS_INPUT);
  ntype.declare = file_ns::node_declare;
  node_type_size_preset(&ntype, NODE_SIZE_MIDDLE);
  node_type_init(&ntype, file_ns::node_shader_init_tangent);
  node_type_gpu(&ntype, file_ns::node_shader_gpu_tangent);
  node_type_storage(
      &ntype, "NodeShaderTangent", node_free_standard_storage, node_copy_standard_storage);

  nodeRegisterType(&ntype);
}

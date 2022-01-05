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

namespace blender::nodes::node_shader_layer_weight_cc {

/* **************** Layer Weight ******************** */

static bNodeSocketTemplate sh_node_layer_weight_in[] = {
    {SOCK_FLOAT, N_("Blend"), 0.5f, 0.0f, 0.0f, 0.0f, 0.0f, 1.0f},
    {SOCK_VECTOR, N_("Normal"), 0.0f, 0.0f, 0.0f, 1.0f, -1.0f, 1.0f, PROP_NONE, SOCK_HIDE_VALUE},
    {-1, ""},
};

static bNodeSocketTemplate sh_node_layer_weight_out[] = {
    {SOCK_FLOAT, N_("Fresnel"), 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 1.0f},
    {SOCK_FLOAT, N_("Facing"), 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 1.0f},
    {-1, ""},
};

static int node_shader_gpu_layer_weight(GPUMaterial *mat,
                                        bNode *node,
                                        bNodeExecData *UNUSED(execdata),
                                        GPUNodeStack *in,
                                        GPUNodeStack *out)
{
  if (!in[1].link) {
    in[1].link = GPU_builtin(GPU_VIEW_NORMAL);
  }
  else {
    GPU_link(
        mat, "direction_transform_m4v3", in[1].link, GPU_builtin(GPU_VIEW_MATRIX), &in[1].link);
  }

  return GPU_stack_link(mat, node, "node_layer_weight", in, out, GPU_builtin(GPU_VIEW_POSITION));
}

}  // namespace blender::nodes::node_shader_layer_weight_cc

/* node type definition */
void register_node_type_sh_layer_weight()
{
  namespace file_ns = blender::nodes::node_shader_layer_weight_cc;

  static bNodeType ntype;

  sh_node_type_base(&ntype, SH_NODE_LAYER_WEIGHT, "Layer Weight", NODE_CLASS_INPUT);
  node_type_socket_templates(
      &ntype, file_ns::sh_node_layer_weight_in, file_ns::sh_node_layer_weight_out);
  node_type_gpu(&ntype, file_ns::node_shader_gpu_layer_weight);

  nodeRegisterType(&ntype);
}

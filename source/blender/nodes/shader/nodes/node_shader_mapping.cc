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

/** \file
 * \ingroup shdnodes
 */

#include "node_shader_util.hh"

namespace blender::nodes::node_shader_mapping_cc {

/* **************** MAPPING  ******************** */
static bNodeSocketTemplate sh_node_mapping_in[] = {
    {SOCK_VECTOR, N_("Vector"), 0.0f, 0.0f, 0.0f, 1.0f, -FLT_MAX, FLT_MAX, PROP_NONE},
    {SOCK_VECTOR, N_("Location"), 0.0f, 0.0f, 0.0f, 1.0f, -FLT_MAX, FLT_MAX, PROP_TRANSLATION},
    {SOCK_VECTOR, N_("Rotation"), 0.0f, 0.0f, 0.0f, 1.0f, -FLT_MAX, FLT_MAX, PROP_EULER},
    {SOCK_VECTOR, N_("Scale"), 1.0f, 1.0f, 1.0f, 1.0f, -FLT_MAX, FLT_MAX, PROP_XYZ},
    {-1, ""},
};

static bNodeSocketTemplate sh_node_mapping_out[] = {
    {SOCK_VECTOR, N_("Vector")},
    {-1, ""},
};

static const char *gpu_shader_get_name(int mode)
{
  switch (mode) {
    case NODE_MAPPING_TYPE_POINT:
      return "mapping_point";
    case NODE_MAPPING_TYPE_TEXTURE:
      return "mapping_texture";
    case NODE_MAPPING_TYPE_VECTOR:
      return "mapping_vector";
    case NODE_MAPPING_TYPE_NORMAL:
      return "mapping_normal";
  }
  return nullptr;
}

static int gpu_shader_mapping(GPUMaterial *mat,
                              bNode *node,
                              bNodeExecData *UNUSED(execdata),
                              GPUNodeStack *in,
                              GPUNodeStack *out)
{
  if (gpu_shader_get_name(node->custom1)) {
    return GPU_stack_link(mat, node, gpu_shader_get_name(node->custom1), in, out);
  }

  return 0;
}

static void node_shader_update_mapping(bNodeTree *ntree, bNode *node)
{
  bNodeSocket *sock = nodeFindSocket(node, SOCK_IN, "Location");
  nodeSetSocketAvailability(
      ntree, sock, ELEM(node->custom1, NODE_MAPPING_TYPE_POINT, NODE_MAPPING_TYPE_TEXTURE));
}

}  // namespace blender::nodes::node_shader_mapping_cc

void register_node_type_sh_mapping()
{
  namespace file_ns = blender::nodes::node_shader_mapping_cc;

  static bNodeType ntype;

  sh_node_type_base(&ntype, SH_NODE_MAPPING, "Mapping", NODE_CLASS_OP_VECTOR);
  node_type_socket_templates(&ntype, file_ns::sh_node_mapping_in, file_ns::sh_node_mapping_out);
  node_type_gpu(&ntype, file_ns::gpu_shader_mapping);
  node_type_update(&ntype, file_ns::node_shader_update_mapping);

  nodeRegisterType(&ntype);
}

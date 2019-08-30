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

#include "../node_shader_util.h"

/* **************** OUTPUT ******************** */

static bNodeSocketTemplate sh_node_normal_map_in[] = {
    {SOCK_FLOAT, 1, N_("Strength"), 1.0f, 0.0f, 0.0f, 0.0f, 0.0f, 10.0f},
    {SOCK_RGBA, 1, N_("Color"), 0.5f, 0.5f, 1.0f, 1.0f, 0.0f, 1.0f},
    {-1, 0, ""},
};

static bNodeSocketTemplate sh_node_normal_map_out[] = {
    {SOCK_VECTOR, 0, N_("Normal"), 0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 1.0f},
    {-1, 0, ""},
};

static void node_shader_init_normal_map(bNodeTree *UNUSED(ntree), bNode *node)
{
  NodeShaderNormalMap *attr = MEM_callocN(sizeof(NodeShaderNormalMap), "NodeShaderNormalMap");
  node->storage = attr;
}

static void node_shader_exec_normal_map(void *UNUSED(data),
                                        int UNUSED(thread),
                                        bNode *UNUSED(node),
                                        bNodeExecData *UNUSED(execdata),
                                        bNodeStack **UNUSED(in),
                                        bNodeStack **UNUSED(out))
{
}

static int gpu_shader_normal_map(GPUMaterial *mat,
                                 bNode *node,
                                 bNodeExecData *UNUSED(execdata),
                                 GPUNodeStack *in,
                                 GPUNodeStack *out)
{
  NodeShaderNormalMap *nm = node->storage;
  GPUNodeLink *negnorm;
  GPUNodeLink *realnorm;
  GPUNodeLink *strength;

  float strength_min[4] = {0, 0, 0, 0};

  if (in[0].link) {
    strength = in[0].link;
  }
  else if (node->original) {
    bNodeSocket *socket = BLI_findlink(&node->original->inputs, 0);
    bNodeSocketValueFloat *socket_data = socket->default_value;
    strength = GPU_uniform(&socket_data->value);
  }
  else {
    strength = GPU_constant(in[0].vec);
  }

  if (in[1].link) {
    realnorm = in[1].link;
  }
  else if (node->original) {
    bNodeSocket *socket = BLI_findlink(&node->original->inputs, 1);
    bNodeSocketValueRGBA *socket_data = socket->default_value;
    realnorm = GPU_uniform(socket_data->value);
  }
  else {
    realnorm = GPU_constant(in[1].vec);
  }

  negnorm = GPU_builtin(GPU_WORLD_NORMAL);
  GPU_link(mat, "math_maximum", strength, GPU_constant(strength_min), &strength);

  const char *color_to_normal_fnc_name = "color_to_normal_new_shading";
  if (nm->space == SHD_SPACE_BLENDER_OBJECT || nm->space == SHD_SPACE_BLENDER_WORLD) {
    color_to_normal_fnc_name = "color_to_blender_normal_new_shading";
  }

  GPU_link(mat, color_to_normal_fnc_name, realnorm, &realnorm);
  switch (nm->space) {
    case SHD_SPACE_TANGENT:
      GPU_link(mat,
               "node_normal_map",
               GPU_builtin(GPU_OBJECT_INFO),
               GPU_attribute(CD_TANGENT, nm->uv_map),
               GPU_builtin(GPU_WORLD_NORMAL),
               realnorm,
               &realnorm);
      break;
    case SHD_SPACE_OBJECT:
    case SHD_SPACE_BLENDER_OBJECT:
      GPU_link(
          mat, "direction_transform_m4v3", realnorm, GPU_builtin(GPU_OBJECT_MATRIX), &realnorm);
      break;
    case SHD_SPACE_WORLD:
    case SHD_SPACE_BLENDER_WORLD:
      /* Nothing to do. */
      break;
  }

  GPU_link(mat, "vector_mix", strength, realnorm, negnorm, &out[0].link);
  GPU_link(mat, "vector_normalize", out[0].link, &out[0].link);

  return true;
}

/* node type definition */
void register_node_type_sh_normal_map(void)
{
  static bNodeType ntype;

  sh_node_type_base(&ntype, SH_NODE_NORMAL_MAP, "Normal Map", NODE_CLASS_OP_VECTOR, 0);
  node_type_socket_templates(&ntype, sh_node_normal_map_in, sh_node_normal_map_out);
  node_type_size_preset(&ntype, NODE_SIZE_MIDDLE);
  node_type_init(&ntype, node_shader_init_normal_map);
  node_type_storage(
      &ntype, "NodeShaderNormalMap", node_free_standard_storage, node_copy_standard_storage);
  node_type_gpu(&ntype, gpu_shader_normal_map);
  node_type_exec(&ntype, NULL, NULL, node_shader_exec_normal_map);

  nodeRegisterType(&ntype);
}

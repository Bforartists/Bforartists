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

#include "node_shader_util.h"

#include "NOD_math_functions.hh"

/* **************** VECTOR MATH ******************** */
static bNodeSocketTemplate sh_node_vector_math_in[] = {
    {SOCK_VECTOR, N_("Vector"), 0.0f, 0.0f, 0.0f, 1.0f, -10000.0f, 10000.0f, PROP_NONE},
    {SOCK_VECTOR, N_("Vector"), 0.0f, 0.0f, 0.0f, 1.0f, -10000.0f, 10000.0f, PROP_NONE},
    {SOCK_VECTOR, N_("Vector"), 0.0f, 0.0f, 0.0f, 1.0f, -10000.0f, 10000.0f, PROP_NONE},
    {SOCK_FLOAT, N_("Scale"), 1.0f, 1.0f, 1.0f, 1.0f, -10000.0f, 10000.0f, PROP_NONE},
    {-1, ""}};

static bNodeSocketTemplate sh_node_vector_math_out[] = {
    {SOCK_VECTOR, N_("Vector")}, {SOCK_FLOAT, N_("Value")}, {-1, ""}};

static const char *gpu_shader_get_name(int mode)
{
  switch (mode) {
    case NODE_VECTOR_MATH_ADD:
      return "vector_math_add";
    case NODE_VECTOR_MATH_SUBTRACT:
      return "vector_math_subtract";
    case NODE_VECTOR_MATH_MULTIPLY:
      return "vector_math_multiply";
    case NODE_VECTOR_MATH_DIVIDE:
      return "vector_math_divide";

    case NODE_VECTOR_MATH_CROSS_PRODUCT:
      return "vector_math_cross";
    case NODE_VECTOR_MATH_PROJECT:
      return "vector_math_project";
    case NODE_VECTOR_MATH_REFLECT:
      return "vector_math_reflect";
    case NODE_VECTOR_MATH_DOT_PRODUCT:
      return "vector_math_dot";

    case NODE_VECTOR_MATH_DISTANCE:
      return "vector_math_distance";
    case NODE_VECTOR_MATH_LENGTH:
      return "vector_math_length";
    case NODE_VECTOR_MATH_SCALE:
      return "vector_math_scale";
    case NODE_VECTOR_MATH_NORMALIZE:
      return "vector_math_normalize";

    case NODE_VECTOR_MATH_SNAP:
      return "vector_math_snap";
    case NODE_VECTOR_MATH_FLOOR:
      return "vector_math_floor";
    case NODE_VECTOR_MATH_CEIL:
      return "vector_math_ceil";
    case NODE_VECTOR_MATH_MODULO:
      return "vector_math_modulo";
    case NODE_VECTOR_MATH_FRACTION:
      return "vector_math_fraction";
    case NODE_VECTOR_MATH_ABSOLUTE:
      return "vector_math_absolute";
    case NODE_VECTOR_MATH_MINIMUM:
      return "vector_math_minimum";
    case NODE_VECTOR_MATH_MAXIMUM:
      return "vector_math_maximum";
    case NODE_VECTOR_MATH_WRAP:
      return "vector_math_wrap";
    case NODE_VECTOR_MATH_SINE:
      return "vector_math_sine";
    case NODE_VECTOR_MATH_COSINE:
      return "vector_math_cosine";
    case NODE_VECTOR_MATH_TANGENT:
      return "vector_math_tangent";
    case NODE_VECTOR_MATH_REFRACT:
      return "vector_math_refract";
    case NODE_VECTOR_MATH_FACEFORWARD:
      return "vector_math_faceforward";
  }

  return nullptr;
}

static int gpu_shader_vector_math(GPUMaterial *mat,
                                  bNode *node,
                                  bNodeExecData *UNUSED(execdata),
                                  GPUNodeStack *in,
                                  GPUNodeStack *out)
{
  const char *name = gpu_shader_get_name(node->custom1);
  if (name != nullptr) {
    return GPU_stack_link(mat, node, name, in, out);
  }

  return 0;
}

static void node_shader_update_vector_math(bNodeTree *UNUSED(ntree), bNode *node)
{
  bNodeSocket *sockB = (bNodeSocket *)BLI_findlink(&node->inputs, 1);
  bNodeSocket *sockC = (bNodeSocket *)BLI_findlink(&node->inputs, 2);
  bNodeSocket *sockScale = nodeFindSocket(node, SOCK_IN, "Scale");

  bNodeSocket *sockVector = nodeFindSocket(node, SOCK_OUT, "Vector");
  bNodeSocket *sockValue = nodeFindSocket(node, SOCK_OUT, "Value");

  nodeSetSocketAvailability(sockB,
                            !ELEM(node->custom1,
                                  NODE_VECTOR_MATH_SINE,
                                  NODE_VECTOR_MATH_COSINE,
                                  NODE_VECTOR_MATH_TANGENT,
                                  NODE_VECTOR_MATH_CEIL,
                                  NODE_VECTOR_MATH_SCALE,
                                  NODE_VECTOR_MATH_FLOOR,
                                  NODE_VECTOR_MATH_LENGTH,
                                  NODE_VECTOR_MATH_ABSOLUTE,
                                  NODE_VECTOR_MATH_FRACTION,
                                  NODE_VECTOR_MATH_NORMALIZE));
  nodeSetSocketAvailability(
      sockC, ELEM(node->custom1, NODE_VECTOR_MATH_WRAP, NODE_VECTOR_MATH_FACEFORWARD));
  nodeSetSocketAvailability(sockScale,
                            ELEM(node->custom1, NODE_VECTOR_MATH_SCALE, NODE_VECTOR_MATH_REFRACT));
  nodeSetSocketAvailability(sockVector,
                            !ELEM(node->custom1,
                                  NODE_VECTOR_MATH_LENGTH,
                                  NODE_VECTOR_MATH_DISTANCE,
                                  NODE_VECTOR_MATH_DOT_PRODUCT));
  nodeSetSocketAvailability(sockValue,
                            ELEM(node->custom1,
                                 NODE_VECTOR_MATH_LENGTH,
                                 NODE_VECTOR_MATH_DISTANCE,
                                 NODE_VECTOR_MATH_DOT_PRODUCT));

  /* Labels */
  node_sock_label_clear(sockB);
  node_sock_label_clear(sockC);
  node_sock_label_clear(sockScale);
  switch (node->custom1) {
    case NODE_VECTOR_MATH_FACEFORWARD:
      node_sock_label(sockB, "Incident");
      node_sock_label(sockC, "Reference");
      break;
    case NODE_VECTOR_MATH_WRAP:
      node_sock_label(sockB, "Max");
      node_sock_label(sockC, "Min");
      break;
    case NODE_VECTOR_MATH_SNAP:
      node_sock_label(sockB, "Increment");
      break;
    case NODE_VECTOR_MATH_REFRACT:
      node_sock_label(sockScale, "Ior");
      break;
    case NODE_VECTOR_MATH_SCALE:
      node_sock_label(sockScale, "Scale");
      break;
  }
}

static const blender::fn::MultiFunction &get_multi_function(
    blender::nodes::NodeMFNetworkBuilder &builder)
{
  using blender::float3;

  NodeVectorMathOperation operation = NodeVectorMathOperation(builder.bnode().custom1);

  const blender::fn::MultiFunction *multi_fn = nullptr;

  blender::nodes::try_dispatch_float_math_fl3_fl3_to_fl3(
      operation, [&](auto function, const blender::nodes::FloatMathOperationInfo &info) {
        static blender::fn::CustomMF_SI_SI_SO<float3, float3, float3> fn{info.title_case_name,
                                                                         function};
        multi_fn = &fn;
      });
  if (multi_fn != nullptr) {
    return *multi_fn;
  }

  blender::nodes::try_dispatch_float_math_fl3_fl3_fl3_to_fl3(
      operation, [&](auto function, const blender::nodes::FloatMathOperationInfo &info) {
        static blender::fn::CustomMF_SI_SI_SI_SO<float3, float3, float3, float3> fn{
            info.title_case_name, function};
        multi_fn = &fn;
      });
  if (multi_fn != nullptr) {
    return *multi_fn;
  }

  blender::nodes::try_dispatch_float_math_fl3_fl3_fl_to_fl3(
      operation, [&](auto function, const blender::nodes::FloatMathOperationInfo &info) {
        static blender::fn::CustomMF_SI_SI_SI_SO<float3, float3, float, float3> fn{
            info.title_case_name, function};
        multi_fn = &fn;
      });
  if (multi_fn != nullptr) {
    return *multi_fn;
  }

  blender::nodes::try_dispatch_float_math_fl3_fl3_to_fl(
      operation, [&](auto function, const blender::nodes::FloatMathOperationInfo &info) {
        static blender::fn::CustomMF_SI_SI_SO<float3, float3, float> fn{info.title_case_name,
                                                                        function};
        multi_fn = &fn;
      });
  if (multi_fn != nullptr) {
    return *multi_fn;
  }

  blender::nodes::try_dispatch_float_math_fl3_fl_to_fl3(
      operation, [&](auto function, const blender::nodes::FloatMathOperationInfo &info) {
        static blender::fn::CustomMF_SI_SI_SO<float3, float, float3> fn{info.title_case_name,
                                                                        function};
        multi_fn = &fn;
      });
  if (multi_fn != nullptr) {
    return *multi_fn;
  }

  blender::nodes::try_dispatch_float_math_fl3_to_fl3(
      operation, [&](auto function, const blender::nodes::FloatMathOperationInfo &info) {
        static blender::fn::CustomMF_SI_SO<float3, float3> fn{info.title_case_name, function};
        multi_fn = &fn;
      });
  if (multi_fn != nullptr) {
    return *multi_fn;
  }

  blender::nodes::try_dispatch_float_math_fl3_to_fl(
      operation, [&](auto function, const blender::nodes::FloatMathOperationInfo &info) {
        static blender::fn::CustomMF_SI_SO<float3, float> fn{info.title_case_name, function};
        multi_fn = &fn;
      });
  if (multi_fn != nullptr) {
    return *multi_fn;
  }

  return builder.get_not_implemented_fn();
}

static void sh_node_vector_math_expand_in_mf_network(blender::nodes::NodeMFNetworkBuilder &builder)
{
  const blender::fn::MultiFunction &fn = get_multi_function(builder);
  builder.set_matching_fn(fn);
}

void register_node_type_sh_vect_math(void)
{
  static bNodeType ntype;

  sh_fn_node_type_base(&ntype, SH_NODE_VECTOR_MATH, "Vector Math", NODE_CLASS_OP_VECTOR, 0);
  node_type_socket_templates(&ntype, sh_node_vector_math_in, sh_node_vector_math_out);
  node_type_label(&ntype, node_vector_math_label);
  node_type_gpu(&ntype, gpu_shader_vector_math);
  node_type_update(&ntype, node_shader_update_vector_math);
  ntype.expand_in_mf_network = sh_node_vector_math_expand_in_mf_network;

  nodeRegisterType(&ntype);
}

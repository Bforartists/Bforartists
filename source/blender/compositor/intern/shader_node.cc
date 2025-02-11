/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#include "BLI_assert.h"
#include "BLI_math_vector.h"
#include "BLI_string_ref.hh"

#include "DNA_node_types.h"

#include "NOD_derived_node_tree.hh"

#include "GPU_material.hh"

#include "COM_shader_node.hh"
#include "COM_utilities.hh"
#include "COM_utilities_gpu_material.hh"
#include "COM_utilities_type_conversion.hh"

namespace blender::compositor {

using namespace nodes::derived_node_tree_types;

ShaderNode::ShaderNode(DNode node) : node_(node)
{
  populate_inputs();
  populate_outputs();
}

void ShaderNode::compile(GPUMaterial *material)
{
  node_->typeinfo->gpu_fn(
      material, const_cast<bNode *>(node_.bnode()), nullptr, inputs_.data(), outputs_.data());
}

GPUNodeStack &ShaderNode::get_input(const StringRef identifier)
{
  return get_shader_node_input(*node_, inputs_.data(), identifier);
}

GPUNodeStack &ShaderNode::get_output(const StringRef identifier)
{
  return get_shader_node_output(*node_, outputs_.data(), identifier);
}

static eGPUType gpu_type_from_socket_type(eNodeSocketDatatype type)
{
  switch (type) {
    case SOCK_FLOAT:
      return GPU_FLOAT;
    case SOCK_INT:
      /* GPUMaterial doesn't support int, so it is passed as a float. */
      return GPU_FLOAT;
    case SOCK_VECTOR:
      return GPU_VEC3;
    case SOCK_RGBA:
      return GPU_VEC4;
    default:
      BLI_assert_unreachable();
      return GPU_NONE;
  }
}

/* Initializes the vector value of the given GPU node stack from the default value of the given
 * socket. Note that the type of the stack may not match that of the socket, so perform implicit
 * conversion if needed. */
static void gpu_stack_vector_from_socket(GPUNodeStack &stack, const bNodeSocket *socket)
{
  const eNodeSocketDatatype input_type = static_cast<eNodeSocketDatatype>(socket->type);
  const eNodeSocketDatatype expected_type = static_cast<eNodeSocketDatatype>(stack.sockettype);

  switch (input_type) {
    case SOCK_FLOAT: {
      const float value = socket->default_value_typed<bNodeSocketValueFloat>()->value;
      switch (expected_type) {
        case SOCK_FLOAT:
          stack.vec[0] = value;
          return;
        case SOCK_INT:
          /* GPUMaterial doesn't support int, so it is passed as a float. */
          stack.vec[0] = float(float_to_int(value));
          return;
        case SOCK_VECTOR:
          copy_v4_v4(stack.vec, float_to_vector(value));
          return;
        case SOCK_RGBA:
          copy_v4_v4(stack.vec, float_to_color(value));
          return;
        default:
          break;
      }
      break;
    }
    case SOCK_INT: {
      const int value = socket->default_value_typed<bNodeSocketValueInt>()->value;
      switch (expected_type) {
        case SOCK_FLOAT:
          stack.vec[0] = int_to_float(value);
          return;
        case SOCK_INT:
          /* GPUMaterial doesn't support int, so it is passed as a float. */
          stack.vec[0] = float(value);
          return;
        case SOCK_VECTOR:
          copy_v4_v4(stack.vec, int_to_vector(value));
          return;
        case SOCK_RGBA:
          copy_v4_v4(stack.vec, int_to_color(value));
          return;
        default:
          break;
      }
      break;
    }
    case SOCK_VECTOR: {
      const float4 value = float4(
          float3(socket->default_value_typed<bNodeSocketValueVector>()->value), 0.0f);
      switch (expected_type) {
        case SOCK_FLOAT:
          stack.vec[0] = vector_to_float(value);
          return;
        case SOCK_INT:
          /* GPUMaterial doesn't support int, so it is passed as a float. */
          stack.vec[0] = float(vector_to_int(value));
          return;
        case SOCK_VECTOR:
          copy_v3_v3(stack.vec, value);
          return;
        case SOCK_RGBA:
          copy_v4_v4(stack.vec, vector_to_color(value));
          return;
        default:
          break;
      }
      break;
    }
    case SOCK_RGBA: {
      const float4 value = socket->default_value_typed<bNodeSocketValueRGBA>()->value;
      switch (expected_type) {
        case SOCK_FLOAT:
          stack.vec[0] = color_to_float(value);
          return;
        case SOCK_INT:
          /* GPUMaterial doesn't support int, so it is passed as a float. */
          stack.vec[0] = float(color_to_int(value));
          return;
        case SOCK_VECTOR:
          copy_v4_v4(stack.vec, color_to_vector(value));
          return;
        case SOCK_RGBA:
          copy_v4_v4(stack.vec, value);
          return;
        default:
          break;
      }
      break;
    }
    default:
      break;
  }

  BLI_assert_unreachable();
}

static void populate_gpu_node_stack(DSocket socket, GPUNodeStack &stack)
{
  /* Make sure this stack is not marked as the end of the stack array. */
  stack.end = false;
  /* This will be initialized later by the GPU material compiler or the compile method. */
  stack.link = nullptr;

  stack.sockettype = socket->type;
  stack.type = gpu_type_from_socket_type((eNodeSocketDatatype)socket->type);

  if (socket->is_input()) {
    const DInputSocket input(socket);

    DSocket origin = get_input_origin_socket(input);

    /* The input is linked if the origin socket is an output socket. Had it been an input socket,
     * then it is an unlinked input of a group input node. */
    stack.hasinput = origin->is_output();

    /* Get the socket value from the origin if it is an input, because then it would either be an
     * unlinked input or an unlinked input of a group input node that the socket is linked to,
     * otherwise, get the value from the socket itself. */
    if (origin->is_input()) {
      gpu_stack_vector_from_socket(stack, origin.bsocket());
    }
    else {
      gpu_stack_vector_from_socket(stack, socket.bsocket());
    }
  }
  else {
    stack.hasoutput = socket->is_logically_linked();
  }
}

void ShaderNode::populate_inputs()
{
  /* Reserve a stack for each input in addition to an extra stack at the end to mark the end of the
   * array, as this is what the GPU module functions expect. */
  const int num_input_sockets = node_->input_sockets().size();
  inputs_.resize(num_input_sockets + 1);
  inputs_.last().end = true;

  for (int i = 0; i < num_input_sockets; i++) {
    populate_gpu_node_stack(node_.input(i), inputs_[i]);
  }
}

void ShaderNode::populate_outputs()
{
  /* Reserve a stack for each output in addition to an extra stack at the end to mark the end of
   * the array, as this is what the GPU module functions expect. */
  const int num_output_sockets = node_->output_sockets().size();
  outputs_.resize(num_output_sockets + 1);
  outputs_.last().end = true;

  for (int i = 0; i < num_output_sockets; i++) {
    populate_gpu_node_stack(node_.output(i), outputs_[i]);
  }
}

}  // namespace blender::compositor

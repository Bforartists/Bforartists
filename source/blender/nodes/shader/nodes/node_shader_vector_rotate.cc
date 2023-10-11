/* SPDX-FileCopyrightText: 2013 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup shdnodes
 */

#include "BLI_math_matrix.h"
#include "BLI_math_rotation.h"
#include "BLI_math_vector_types.hh"

#include "FN_multi_function.hh"
#include "FN_multi_function_builder.hh"

#include "NOD_multi_function.hh"

#include "node_shader_util.hh"

#include "UI_interface.hh"
#include "UI_resources.hh"

namespace blender::nodes::node_shader_vector_rotate_cc {

static void sh_node_vector_rotate_declare(NodeDeclarationBuilder &b)
{
  b.is_function_node();
  b.add_input<decl::Vector>("Vector").min(0.0f).max(1.0f).hide_value();
  b.add_input<decl::Vector>("Center");
  b.add_input<decl::Vector>("Axis")
      .min(-1.0f)
      .max(1.0f)
      .default_value({0.0f, 0.0f, 1.0f})
      .make_available([](bNode &node) { node.custom1 = NODE_VECTOR_ROTATE_TYPE_AXIS; });
  b.add_input<decl::Float>("Angle").subtype(PROP_ANGLE);
  b.add_input<decl::Vector>("Rotation").subtype(PROP_EULER).make_available([](bNode &node) {
    node.custom1 = NODE_VECTOR_ROTATE_TYPE_EULER_XYZ;
  });
  b.add_output<decl::Vector>("Vector");
}

static void node_shader_buts_vector_rotate(uiLayout *layout, bContext * /*C*/, PointerRNA *ptr)
{
  uiItemR(layout, ptr, "rotation_type", UI_ITEM_R_SPLIT_EMPTY_NAME, nullptr, ICON_NONE);
  uiItemR(layout, ptr, "invert", UI_ITEM_R_SPLIT_EMPTY_NAME, nullptr, ICON_NONE);
}

static const char *gpu_shader_get_name(int mode)
{
  switch (mode) {
    case NODE_VECTOR_ROTATE_TYPE_AXIS:
      return "node_vector_rotate_axis_angle";
    case NODE_VECTOR_ROTATE_TYPE_AXIS_X:
      return "node_vector_rotate_axis_x";
    case NODE_VECTOR_ROTATE_TYPE_AXIS_Y:
      return "node_vector_rotate_axis_y";
    case NODE_VECTOR_ROTATE_TYPE_AXIS_Z:
      return "node_vector_rotate_axis_z";
    case NODE_VECTOR_ROTATE_TYPE_EULER_XYZ:
      return "node_vector_rotate_euler_xyz";
  }

  return nullptr;
}

static int gpu_shader_vector_rotate(GPUMaterial *mat,
                                    bNode *node,
                                    bNodeExecData * /*execdata*/,
                                    GPUNodeStack *in,
                                    GPUNodeStack *out)
{
  const char *name = gpu_shader_get_name(node->custom1);

  if (name != nullptr) {
    float invert = (node->custom2) ? -1.0 : 1.0;
    return GPU_stack_link(mat, node, name, in, out, GPU_constant(&invert));
  }

  return 0;
}

static float3 sh_node_vector_rotate_around_axis(const float3 &vector,
                                                const float3 &center,
                                                const float3 &axis,
                                                const float angle)
{
  float3 result = vector - center;
  float mat[3][3];
  axis_angle_to_mat3(mat, axis, angle);
  mul_m3_v3(mat, result);
  return result + center;
}

static float3 sh_node_vector_rotate_euler(const float3 &vector,
                                          const float3 &center,
                                          const float3 &rotation,
                                          const bool invert)
{
  float mat[3][3];
  float3 result = vector - center;
  eul_to_mat3(mat, rotation);
  if (invert) {
    invert_m3(mat);
  }
  mul_m3_v3(mat, result);
  return result + center;
}

static const mf::MultiFunction *get_multi_function(const bNode &node)
{
  bool invert = node.custom2;
  const int mode = node.custom1;

  switch (mode) {
    case NODE_VECTOR_ROTATE_TYPE_AXIS: {
      if (invert) {
        static auto fn = mf::build::SI4_SO<float3, float3, float3, float, float3>(
            "Rotate Axis",
            [](const float3 &in, const float3 &center, const float3 &axis, float angle) {
              return sh_node_vector_rotate_around_axis(in, center, axis, -angle);
            });
        return &fn;
      }
      static auto fn = mf::build::SI4_SO<float3, float3, float3, float, float3>(
          "Rotate Axis",
          [](const float3 &in, const float3 &center, const float3 &axis, float angle) {
            return sh_node_vector_rotate_around_axis(in, center, axis, angle);
          });
      return &fn;
    }
    case NODE_VECTOR_ROTATE_TYPE_AXIS_X: {
      float3 axis = float3(1.0f, 0.0f, 0.0f);
      if (invert) {
        static auto fn = mf::build::SI3_SO<float3, float3, float, float3>(
            "Rotate X-Axis", [=](const float3 &in, const float3 &center, float angle) {
              return sh_node_vector_rotate_around_axis(in, center, axis, -angle);
            });
        return &fn;
      }
      static auto fn = mf::build::SI3_SO<float3, float3, float, float3>(
          "Rotate X-Axis", [=](const float3 &in, const float3 &center, float angle) {
            return sh_node_vector_rotate_around_axis(in, center, axis, angle);
          });
      return &fn;
    }
    case NODE_VECTOR_ROTATE_TYPE_AXIS_Y: {
      float3 axis = float3(0.0f, 1.0f, 0.0f);
      if (invert) {
        static auto fn = mf::build::SI3_SO<float3, float3, float, float3>(
            "Rotate Y-Axis", [=](const float3 &in, const float3 &center, float angle) {
              return sh_node_vector_rotate_around_axis(in, center, axis, -angle);
            });
        return &fn;
      }
      static auto fn = mf::build::SI3_SO<float3, float3, float, float3>(
          "Rotate Y-Axis", [=](const float3 &in, const float3 &center, float angle) {
            return sh_node_vector_rotate_around_axis(in, center, axis, angle);
          });
      return &fn;
    }
    case NODE_VECTOR_ROTATE_TYPE_AXIS_Z: {
      float3 axis = float3(0.0f, 0.0f, 1.0f);
      if (invert) {
        static auto fn = mf::build::SI3_SO<float3, float3, float, float3>(
            "Rotate Z-Axis", [=](const float3 &in, const float3 &center, float angle) {
              return sh_node_vector_rotate_around_axis(in, center, axis, -angle);
            });
        return &fn;
      }
      static auto fn = mf::build::SI3_SO<float3, float3, float, float3>(
          "Rotate Z-Axis", [=](const float3 &in, const float3 &center, float angle) {
            return sh_node_vector_rotate_around_axis(in, center, axis, angle);
          });
      return &fn;
    }
    case NODE_VECTOR_ROTATE_TYPE_EULER_XYZ: {
      if (invert) {
        static auto fn = mf::build::SI3_SO<float3, float3, float3, float3>(
            "Rotate Euler", [](const float3 &in, const float3 &center, const float3 &rotation) {
              return sh_node_vector_rotate_euler(in, center, rotation, true);
            });
        return &fn;
      }
      static auto fn = mf::build::SI3_SO<float3, float3, float3, float3>(
          "Rotate Euler", [](const float3 &in, const float3 &center, const float3 &rotation) {
            return sh_node_vector_rotate_euler(in, center, rotation, false);
          });
      return &fn;
    }
    default:
      BLI_assert_unreachable();
      return nullptr;
  }
}

static void sh_node_vector_rotate_build_multi_function(NodeMultiFunctionBuilder &builder)
{
  const mf::MultiFunction *fn = get_multi_function(builder.node());
  builder.set_matching_fn(fn);
}

static void node_shader_update_vector_rotate(bNodeTree *ntree, bNode *node)
{
  bNodeSocket *sock_rotation = nodeFindSocket(node, SOCK_IN, "Rotation");
  bke::nodeSetSocketAvailability(
      ntree, sock_rotation, ELEM(node->custom1, NODE_VECTOR_ROTATE_TYPE_EULER_XYZ));
  bNodeSocket *sock_axis = nodeFindSocket(node, SOCK_IN, "Axis");
  bke::nodeSetSocketAvailability(
      ntree, sock_axis, ELEM(node->custom1, NODE_VECTOR_ROTATE_TYPE_AXIS));
  bNodeSocket *sock_angle = nodeFindSocket(node, SOCK_IN, "Angle");
  bke::nodeSetSocketAvailability(
      ntree, sock_angle, !ELEM(node->custom1, NODE_VECTOR_ROTATE_TYPE_EULER_XYZ));
}

NODE_SHADER_MATERIALX_BEGIN
#ifdef WITH_MATERIALX
{
  int mode = node_->custom1;
  bool invert = node_->custom2;

  NodeItem vector = get_input_value("Vector", NodeItem::Type::Vector3);
  NodeItem center = get_input_value("Center", NodeItem::Type::Vector3) *
                    val(MaterialX::Vector3(1.0f, 1.0f, -1.0f));
  vector = vector - center;

  if (mode == NODE_VECTOR_ROTATE_TYPE_EULER_XYZ) {
    NodeItem rotation = get_input_value("Rotation", NodeItem::Type::Vector3) *
                        val(MaterialX::Vector3(1.0f, 1.0f, -1.0f) * 180.0f / M_PI);

    return vector.rotate(invert ? -rotation : rotation, invert) + center;
  }

  NodeItem angle = get_input_value("Angle", NodeItem::Type::Float) * val(float(180.0f / M_PI));
  NodeItem axis = empty();
  switch (mode) {
    case NODE_VECTOR_ROTATE_TYPE_AXIS:
      axis = get_input_value("Axis", NodeItem::Type::Vector3) *
             val(MaterialX::Vector3(1.0f, 1.0f, -1.0f));
      break;
    case NODE_VECTOR_ROTATE_TYPE_AXIS_X:
      axis = val(MaterialX::Vector3(1.0f, 0.0f, 0.0f));
      break;
    case NODE_VECTOR_ROTATE_TYPE_AXIS_Y:
      axis = val(MaterialX::Vector3(0.0f, 1.0f, 0.0f));
      break;
    case NODE_VECTOR_ROTATE_TYPE_AXIS_Z:
      axis = val(MaterialX::Vector3(0.0f, 0.0f, -1.0f));
      break;
    default:
      BLI_assert_unreachable();
  }

  return vector.rotate(invert ? -angle : angle, axis) + center;
}
#endif
NODE_SHADER_MATERIALX_END

}  // namespace blender::nodes::node_shader_vector_rotate_cc

void register_node_type_sh_vector_rotate()
{
  namespace file_ns = blender::nodes::node_shader_vector_rotate_cc;

  static bNodeType ntype;

  sh_fn_node_type_base(&ntype, SH_NODE_VECTOR_ROTATE, "Vector Rotate", NODE_CLASS_OP_VECTOR);
  ntype.declare = file_ns::sh_node_vector_rotate_declare;
  ntype.draw_buttons = file_ns::node_shader_buts_vector_rotate;
  ntype.gpu_fn = file_ns::gpu_shader_vector_rotate;
  ntype.updatefunc = file_ns::node_shader_update_vector_rotate;
  ntype.build_multi_function = file_ns::sh_node_vector_rotate_build_multi_function;
  ntype.materialx_fn = file_ns::node_shader_materialx;

  nodeRegisterType(&ntype);
}

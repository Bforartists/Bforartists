/* SPDX-FileCopyrightText: 2005 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup shdnodes
 */

#include "node_shader_util.hh"
#include "node_util.hh"

#include "NOD_math_functions.hh"
#include "NOD_multi_function.hh"
#include "NOD_socket_search_link.hh"

#include "RNA_enum_types.hh"

#include "UI_interface.hh"
#include "UI_resources.hh"

namespace blender::nodes::node_shader_vector_math_cc {

static void sh_node_vector_math_declare(NodeDeclarationBuilder &b)
{
  b.is_function_node();
  b.add_input<decl::Vector>("Vector").min(-10000.0f).max(10000.0f);
  b.add_input<decl::Vector>("Vector", "Vector_001").min(-10000.0f).max(10000.0f);
  b.add_input<decl::Vector>("Vector", "Vector_002").min(-10000.0f).max(10000.0f);
  b.add_input<decl::Float>("Scale").default_value(1.0f).min(-10000.0f).max(10000.0f);
  b.add_output<decl::Vector>("Vector");
  b.add_output<decl::Float>("Value");
}

static void node_shader_buts_vect_math(uiLayout *layout, bContext * /*C*/, PointerRNA *ptr)
{
  uiItemR(layout, ptr, "operation", UI_ITEM_R_SPLIT_EMPTY_NAME, "", ICON_NONE);
}

class SocketSearchOp {
 public:
  std::string socket_name;
  NodeVectorMathOperation mode = NODE_VECTOR_MATH_ADD;
  void operator()(LinkSearchOpParams &params)
  {
    bNode &node = params.add_node("ShaderNodeVectorMath");
    node.custom1 = mode;
    params.update_and_connect_available_socket(node, socket_name);
  }
};

static void sh_node_vector_math_gather_link_searches(GatherLinkSearchOpParams &params)
{
  if (!params.node_tree().typeinfo->validate_link(
          static_cast<eNodeSocketDatatype>(params.other_socket().type), SOCK_VECTOR))
  {
    return;
  }

  const int weight = ELEM(params.other_socket().type, SOCK_VECTOR, SOCK_RGBA) ? 0 : -1;

  for (const EnumPropertyItem *item = rna_enum_node_vec_math_items; item->identifier != nullptr;
       item++)
  {
    if (item->name != nullptr && item->identifier[0] != '\0') {
      if ((params.in_out() == SOCK_OUT) && ELEM(item->value,
                                                NODE_VECTOR_MATH_LENGTH,
                                                NODE_VECTOR_MATH_DISTANCE,
                                                NODE_VECTOR_MATH_DOT_PRODUCT))
      {
        params.add_item(CTX_IFACE_(BLT_I18NCONTEXT_ID_NODETREE, item->name),
                        SocketSearchOp{"Value", (NodeVectorMathOperation)item->value},
                        weight);
      }
      else {
        params.add_item(CTX_IFACE_(BLT_I18NCONTEXT_ID_NODETREE, item->name),
                        SocketSearchOp{"Vector", (NodeVectorMathOperation)item->value},
                        weight);
      }
    }
  }
}

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
    case NODE_VECTOR_MATH_MULTIPLY_ADD:
      return "vector_math_multiply_add";
  }

  return nullptr;
}

static int gpu_shader_vector_math(GPUMaterial *mat,
                                  bNode *node,
                                  bNodeExecData * /*execdata*/,
                                  GPUNodeStack *in,
                                  GPUNodeStack *out)
{
  const char *name = gpu_shader_get_name(node->custom1);
  if (name != nullptr) {
    return GPU_stack_link(mat, node, name, in, out);
  }

  return 0;
}

static void node_shader_update_vector_math(bNodeTree *ntree, bNode *node)
{
  bNodeSocket *sockB = (bNodeSocket *)BLI_findlink(&node->inputs, 1);
  bNodeSocket *sockC = (bNodeSocket *)BLI_findlink(&node->inputs, 2);
  bNodeSocket *sockScale = nodeFindSocket(node, SOCK_IN, "Scale");

  bNodeSocket *sockVector = nodeFindSocket(node, SOCK_OUT, "Vector");
  bNodeSocket *sockValue = nodeFindSocket(node, SOCK_OUT, "Value");

  bke::nodeSetSocketAvailability(ntree,
                                 sockB,
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
  bke::nodeSetSocketAvailability(ntree,
                                 sockC,
                                 ELEM(node->custom1,
                                      NODE_VECTOR_MATH_WRAP,
                                      NODE_VECTOR_MATH_FACEFORWARD,
                                      NODE_VECTOR_MATH_MULTIPLY_ADD));
  bke::nodeSetSocketAvailability(
      ntree, sockScale, ELEM(node->custom1, NODE_VECTOR_MATH_SCALE, NODE_VECTOR_MATH_REFRACT));
  bke::nodeSetSocketAvailability(ntree,
                                 sockVector,
                                 !ELEM(node->custom1,
                                       NODE_VECTOR_MATH_LENGTH,
                                       NODE_VECTOR_MATH_DISTANCE,
                                       NODE_VECTOR_MATH_DOT_PRODUCT));
  bke::nodeSetSocketAvailability(ntree,
                                 sockValue,
                                 ELEM(node->custom1,
                                      NODE_VECTOR_MATH_LENGTH,
                                      NODE_VECTOR_MATH_DISTANCE,
                                      NODE_VECTOR_MATH_DOT_PRODUCT));

  /* Labels */
  node_sock_label_clear(sockB);
  node_sock_label_clear(sockC);
  node_sock_label_clear(sockScale);
  switch (node->custom1) {
    case NODE_VECTOR_MATH_MULTIPLY_ADD:
      node_sock_label(sockB, "Multiplier");
      node_sock_label(sockC, "Addend");
      break;
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

static const mf::MultiFunction *get_multi_function(const bNode &node)
{
  NodeVectorMathOperation operation = NodeVectorMathOperation(node.custom1);

  const mf::MultiFunction *multi_fn = nullptr;

  try_dispatch_float_math_fl3_fl3_to_fl3(
      operation, [&](auto exec_preset, auto function, const FloatMathOperationInfo &info) {
        static auto fn = mf::build::SI2_SO<float3, float3, float3>(
            info.title_case_name.c_str(), function, exec_preset);
        multi_fn = &fn;
      });
  if (multi_fn != nullptr) {
    return multi_fn;
  }

  try_dispatch_float_math_fl3_fl3_fl3_to_fl3(
      operation, [&](auto exec_preset, auto function, const FloatMathOperationInfo &info) {
        static auto fn = mf::build::SI3_SO<float3, float3, float3, float3>(
            info.title_case_name.c_str(), function, exec_preset);
        multi_fn = &fn;
      });
  if (multi_fn != nullptr) {
    return multi_fn;
  }

  try_dispatch_float_math_fl3_fl3_fl_to_fl3(
      operation, [&](auto exec_preset, auto function, const FloatMathOperationInfo &info) {
        static auto fn = mf::build::SI3_SO<float3, float3, float, float3>(
            info.title_case_name.c_str(), function, exec_preset);
        multi_fn = &fn;
      });
  if (multi_fn != nullptr) {
    return multi_fn;
  }

  try_dispatch_float_math_fl3_fl3_to_fl(
      operation, [&](auto exec_preset, auto function, const FloatMathOperationInfo &info) {
        static auto fn = mf::build::SI2_SO<float3, float3, float>(
            info.title_case_name.c_str(), function, exec_preset);
        multi_fn = &fn;
      });
  if (multi_fn != nullptr) {
    return multi_fn;
  }

  try_dispatch_float_math_fl3_fl_to_fl3(
      operation, [&](auto exec_preset, auto function, const FloatMathOperationInfo &info) {
        static auto fn = mf::build::SI2_SO<float3, float, float3>(
            info.title_case_name.c_str(), function, exec_preset);
        multi_fn = &fn;
      });
  if (multi_fn != nullptr) {
    return multi_fn;
  }

  try_dispatch_float_math_fl3_to_fl3(
      operation, [&](auto exec_preset, auto function, const FloatMathOperationInfo &info) {
        static auto fn = mf::build::SI1_SO<float3, float3>(
            info.title_case_name.c_str(), function, exec_preset);
        multi_fn = &fn;
      });
  if (multi_fn != nullptr) {
    return multi_fn;
  }

  try_dispatch_float_math_fl3_to_fl(
      operation, [&](auto exec_preset, auto function, const FloatMathOperationInfo &info) {
        static auto fn = mf::build::SI1_SO<float3, float>(
            info.title_case_name.c_str(), function, exec_preset);
        multi_fn = &fn;
      });
  if (multi_fn != nullptr) {
    return multi_fn;
  }

  return nullptr;
}

static void sh_node_vector_math_build_multi_function(NodeMultiFunctionBuilder &builder)
{
  const mf::MultiFunction *fn = get_multi_function(builder.node());
  builder.set_matching_fn(fn);
}

NODE_SHADER_MATERIALX_BEGIN
#ifdef WITH_MATERIALX
{
  CLG_LogRef *LOG_MATERIALX_SHADER = materialx::LOG_MATERIALX_SHADER;

  /* TODO: finish some math operations */
  auto op = node_->custom1;
  NodeItem res = empty();

  /* Single operand operations */
  NodeItem x = get_input_value(0, NodeItem::Type::Vector3);
  switch (op) {
    case NODE_VECTOR_MATH_SINE:
      res = x.sin();
      break;
    case NODE_VECTOR_MATH_COSINE:
      res = x.cos();
      break;
    case NODE_VECTOR_MATH_TANGENT:
      res = x.tan();
      break;
    case NODE_VECTOR_MATH_ABSOLUTE:
      res = x.abs();
      break;
    case NODE_VECTOR_MATH_FLOOR:
      res = x.floor();
      break;
    case NODE_VECTOR_MATH_CEIL:
      res = x.ceil();
      break;
    case NODE_VECTOR_MATH_FRACTION:
      res = x % val(1.0f);
      break;
    case NODE_VECTOR_MATH_LENGTH:
      CLOG_WARN(LOG_MATERIALX_SHADER, "Unimplemented math operation %d", op);
      break;
    case NODE_VECTOR_MATH_NORMALIZE:
      CLOG_WARN(LOG_MATERIALX_SHADER, "Unimplemented math operation %d", op);
      break;

    default: {
      /* 2-operand operations */
      NodeItem y = get_input_value(1, NodeItem::Type::Vector3);
      switch (op) {
        case NODE_VECTOR_MATH_ADD:
          res = x + y;
          break;
        case NODE_VECTOR_MATH_SUBTRACT:
          res = x - y;
          break;
        case NODE_VECTOR_MATH_MULTIPLY:
          res = x * y;
          break;
        case NODE_VECTOR_MATH_DIVIDE:
          res = x / y;
          break;
        case NODE_VECTOR_MATH_MINIMUM:
          res = x.min(y);
          break;
        case NODE_VECTOR_MATH_MAXIMUM:
          res = x.max(y);
          break;
        case NODE_VECTOR_MATH_MODULO:
          res = x % y;
          break;
        case NODE_VECTOR_MATH_SNAP:
          CLOG_WARN(LOG_MATERIALX_SHADER, "Unimplemented math operation %d", op);
          break;
        case NODE_VECTOR_MATH_CROSS_PRODUCT:
          CLOG_WARN(LOG_MATERIALX_SHADER, "Unimplemented math operation %d", op);
          break;
        case NODE_VECTOR_MATH_DOT_PRODUCT:
          CLOG_WARN(LOG_MATERIALX_SHADER, "Unimplemented math operation %d", op);
          break;
        case NODE_VECTOR_MATH_PROJECT:
          CLOG_WARN(LOG_MATERIALX_SHADER, "Unimplemented math operation %d", op);
          break;
        case NODE_VECTOR_MATH_REFLECT:
          CLOG_WARN(LOG_MATERIALX_SHADER, "Unimplemented math operation %d", op);
          break;
        case NODE_VECTOR_MATH_DISTANCE:
          CLOG_WARN(LOG_MATERIALX_SHADER, "Unimplemented math operation %d", op);
          break;
        case NODE_VECTOR_MATH_SCALE:
          CLOG_WARN(LOG_MATERIALX_SHADER, "Unimplemented math operation %d", op);
          break;

        default: {
          /* 3-operand operations */
          NodeItem z = get_input_value(2, NodeItem::Type::Vector3);
          switch (op) {
            case NODE_VECTOR_MATH_MULTIPLY_ADD:
              res = x * y + z;
              break;
            case NODE_VECTOR_MATH_REFRACT:
              CLOG_WARN(LOG_MATERIALX_SHADER, "Unimplemented math operation %d", op);
              break;
            case NODE_VECTOR_MATH_FACEFORWARD:
              CLOG_WARN(LOG_MATERIALX_SHADER, "Unimplemented math operation %d", op);
              break;
            case NODE_VECTOR_MATH_WRAP:
              CLOG_WARN(LOG_MATERIALX_SHADER, "Unimplemented math operation %d", op);
              break;

            default:
              BLI_assert_unreachable();
          }
        }
      }
    }
  }

  return res;
}
#endif
NODE_SHADER_MATERIALX_END

}  // namespace blender::nodes::node_shader_vector_math_cc

void register_node_type_sh_vect_math()
{
  namespace file_ns = blender::nodes::node_shader_vector_math_cc;

  static bNodeType ntype;

  sh_fn_node_type_base(&ntype, SH_NODE_VECTOR_MATH, "Vector Math", NODE_CLASS_OP_VECTOR);
  ntype.declare = file_ns::sh_node_vector_math_declare;
  ntype.draw_buttons = file_ns::node_shader_buts_vect_math;
  ntype.labelfunc = node_vector_math_label;
  ntype.gpu_fn = file_ns::gpu_shader_vector_math;
  ntype.updatefunc = file_ns::node_shader_update_vector_math;
  ntype.build_multi_function = file_ns::sh_node_vector_math_build_multi_function;
  ntype.gather_link_search_ops = file_ns::sh_node_vector_math_gather_link_searches;
  ntype.materialx_fn = file_ns::node_shader_materialx;

  nodeRegisterType(&ntype);
}

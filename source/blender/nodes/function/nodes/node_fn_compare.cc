/* SPDX-License-Identifier: GPL-2.0-or-later */

#include <cmath>

#include "BLI_listbase.h"
#include "BLI_math_vector.h"
#include "BLI_string.h"

#include "UI_interface.h"
#include "UI_resources.h"

#include "RNA_enum_types.h"

#include "node_function_util.hh"

#include "NOD_socket_search_link.hh"

namespace blender::nodes::node_fn_compare_cc {

NODE_STORAGE_FUNCS(NodeFunctionCompare)

static void node_declare(NodeDeclarationBuilder &b)
{
  b.is_function_node();
  b.add_input<decl::Float>(N_("A")).min(-10000.0f).max(10000.0f);
  b.add_input<decl::Float>(N_("B")).min(-10000.0f).max(10000.0f);

  b.add_input<decl::Int>(N_("A"), "A_INT");
  b.add_input<decl::Int>(N_("B"), "B_INT");

  b.add_input<decl::Vector>(N_("A"), "A_VEC3");
  b.add_input<decl::Vector>(N_("B"), "B_VEC3");

  b.add_input<decl::Color>(N_("A"), "A_COL");
  b.add_input<decl::Color>(N_("B"), "B_COL");

  b.add_input<decl::String>(N_("A"), "A_STR");
  b.add_input<decl::String>(N_("B"), "B_STR");

  b.add_input<decl::Float>(N_("C")).default_value(0.9f);
  b.add_input<decl::Float>(N_("Angle")).default_value(0.0872665f).subtype(PROP_ANGLE);
  b.add_input<decl::Float>(N_("Epsilon")).default_value(0.001).min(-10000.0f).max(10000.0f);

  b.add_output<decl::Bool>(N_("Result"));
}

static void node_layout(uiLayout *layout, bContext * /*C*/, PointerRNA *ptr)
{
  const NodeFunctionCompare &data = node_storage(*static_cast<const bNode *>(ptr->data));
  uiItemR(layout, ptr, "data_type", 0, "", ICON_NONE);
  if (data.data_type == SOCK_VECTOR) {
    uiItemR(layout, ptr, "mode", 0, "", ICON_NONE);
  }
  uiItemR(layout, ptr, "operation", 0, "", ICON_NONE);
}

static void node_update(bNodeTree *ntree, bNode *node)
{
  NodeFunctionCompare *data = (NodeFunctionCompare *)node->storage;

  bNodeSocket *sock_comp = (bNodeSocket *)BLI_findlink(&node->inputs, 10);
  bNodeSocket *sock_angle = (bNodeSocket *)BLI_findlink(&node->inputs, 11);
  bNodeSocket *sock_epsilon = (bNodeSocket *)BLI_findlink(&node->inputs, 12);

  LISTBASE_FOREACH (bNodeSocket *, socket, &node->inputs) {
    nodeSetSocketAvailability(ntree, socket, socket->type == (eNodeSocketDatatype)data->data_type);
  }

  nodeSetSocketAvailability(ntree,
                            sock_epsilon,
                            ELEM(data->operation, NODE_COMPARE_EQUAL, NODE_COMPARE_NOT_EQUAL) &&
                                !ELEM(data->data_type, SOCK_INT, SOCK_STRING));

  nodeSetSocketAvailability(ntree,
                            sock_comp,
                            ELEM(data->mode, NODE_COMPARE_MODE_DOT_PRODUCT) &&
                                data->data_type == SOCK_VECTOR);

  nodeSetSocketAvailability(ntree,
                            sock_angle,
                            ELEM(data->mode, NODE_COMPARE_MODE_DIRECTION) &&
                                data->data_type == SOCK_VECTOR);
}

static void node_init(bNodeTree * /*tree*/, bNode *node)
{
  NodeFunctionCompare *data = MEM_cnew<NodeFunctionCompare>(__func__);
  data->operation = NODE_COMPARE_GREATER_THAN;
  data->data_type = SOCK_FLOAT;
  data->mode = NODE_COMPARE_MODE_ELEMENT;
  node->storage = data;
}

class SocketSearchOp {
 public:
  const StringRef socket_name;
  eNodeSocketDatatype data_type;
  NodeCompareOperation operation;
  NodeCompareMode mode = NODE_COMPARE_MODE_ELEMENT;
  void operator()(LinkSearchOpParams &params)
  {
    bNode &node = params.add_node("FunctionNodeCompare");
    node_storage(node).data_type = data_type;
    node_storage(node).operation = operation;
    node_storage(node).mode = mode;
    params.update_and_connect_available_socket(node, socket_name);
  }
};

static std::optional<eNodeSocketDatatype> get_compare_type_for_operation(
    const eNodeSocketDatatype type, const NodeCompareOperation operation)
{
  switch (type) {
    case SOCK_BOOLEAN:
      if (ELEM(operation, NODE_COMPARE_COLOR_BRIGHTER, NODE_COMPARE_COLOR_DARKER)) {
        return SOCK_RGBA;
      }
      return SOCK_INT;
    case SOCK_INT:
    case SOCK_FLOAT:
    case SOCK_VECTOR:
      if (ELEM(operation, NODE_COMPARE_COLOR_BRIGHTER, NODE_COMPARE_COLOR_DARKER)) {
        return SOCK_RGBA;
      }
      return type;
    case SOCK_RGBA:
      if (!ELEM(operation,
                NODE_COMPARE_COLOR_BRIGHTER,
                NODE_COMPARE_COLOR_DARKER,
                NODE_COMPARE_EQUAL,
                NODE_COMPARE_NOT_EQUAL)) {
        return SOCK_VECTOR;
      }
      return type;
    case SOCK_STRING:
      if (!ELEM(operation, NODE_COMPARE_EQUAL, NODE_COMPARE_NOT_EQUAL)) {
        return std::nullopt;
      }
      return type;
    default:
      BLI_assert_unreachable();
      return std::nullopt;
  }
}

static void node_gather_link_searches(GatherLinkSearchOpParams &params)
{
  const eNodeSocketDatatype type = eNodeSocketDatatype(params.other_socket().type);
  if (!ELEM(type, SOCK_INT, SOCK_BOOLEAN, SOCK_FLOAT, SOCK_VECTOR, SOCK_RGBA, SOCK_STRING)) {
    return;
  }
  const StringRef socket_name = params.in_out() == SOCK_IN ? "A" : "Result";
  for (const EnumPropertyItem *item = rna_enum_node_compare_operation_items;
       item->identifier != nullptr;
       item++) {
    if (item->name != nullptr && item->identifier[0] != '\0') {
      const NodeCompareOperation operation = NodeCompareOperation(item->value);
      if (const std::optional<eNodeSocketDatatype> fixed_type = get_compare_type_for_operation(
              type, operation)) {
        params.add_item(IFACE_(item->name), SocketSearchOp{socket_name, *fixed_type, operation});
      }
    }
  }

  if (params.in_out() != SOCK_IN && type != SOCK_STRING) {
    params.add_item(
        IFACE_("Angle"),
        SocketSearchOp{
            "Angle", SOCK_VECTOR, NODE_COMPARE_GREATER_THAN, NODE_COMPARE_MODE_DIRECTION});
  }
}

static void node_label(const bNodeTree * /*tree*/, const bNode *node, char *label, int maxlen)
{
  const NodeFunctionCompare *data = (NodeFunctionCompare *)node->storage;
  const char *name;
  bool enum_label = RNA_enum_name(rna_enum_node_compare_operation_items, data->operation, &name);
  if (!enum_label) {
    name = "Unknown";
  }
  BLI_strncpy(label, IFACE_(name), maxlen);
}

static float component_average(float3 a)
{
  return (a.x + a.y + a.z) / 3.0f;
}

static const mf::MultiFunction *get_multi_function(const bNode &node)
{
  const NodeFunctionCompare *data = (NodeFunctionCompare *)node.storage;

  static auto exec_preset_all = mf::build::exec_presets::AllSpanOrSingle();
  static auto exec_preset_first_two = mf::build::exec_presets::SomeSpanOrSingle<0, 1>();

  switch (data->data_type) {
    case SOCK_FLOAT:
      switch (data->operation) {
        case NODE_COMPARE_LESS_THAN: {
          static auto fn = mf::build::SI2_SO<float, float, bool>(
              "Less Than", [](float a, float b) { return a < b; }, exec_preset_all);
          return &fn;
        }
        case NODE_COMPARE_LESS_EQUAL: {
          static auto fn = mf::build::SI2_SO<float, float, bool>(
              "Less Equal", [](float a, float b) { return a <= b; }, exec_preset_all);
          return &fn;
        }
        case NODE_COMPARE_GREATER_THAN: {
          static auto fn = mf::build::SI2_SO<float, float, bool>(
              "Greater Than", [](float a, float b) { return a > b; }, exec_preset_all);
          return &fn;
        }
        case NODE_COMPARE_GREATER_EQUAL: {
          static auto fn = mf::build::SI2_SO<float, float, bool>(
              "Greater Equal", [](float a, float b) { return a >= b; }, exec_preset_all);
          return &fn;
        }
        case NODE_COMPARE_EQUAL: {
          static auto fn = mf::build::SI3_SO<float, float, float, bool>(
              "Equal",
              [](float a, float b, float epsilon) { return std::abs(a - b) <= epsilon; },
              exec_preset_first_two);
          return &fn;
        }
        case NODE_COMPARE_NOT_EQUAL:
          static auto fn = mf::build::SI3_SO<float, float, float, bool>(
              "Not Equal",
              [](float a, float b, float epsilon) { return std::abs(a - b) > epsilon; },
              exec_preset_first_two);
          return &fn;
      }
      break;
    case SOCK_INT:
      switch (data->operation) {
        case NODE_COMPARE_LESS_THAN: {
          static auto fn = mf::build::SI2_SO<int, int, bool>(
              "Less Than", [](int a, int b) { return a < b; }, exec_preset_all);
          return &fn;
        }
        case NODE_COMPARE_LESS_EQUAL: {
          static auto fn = mf::build::SI2_SO<int, int, bool>(
              "Less Equal", [](int a, int b) { return a <= b; }, exec_preset_all);
          return &fn;
        }
        case NODE_COMPARE_GREATER_THAN: {
          static auto fn = mf::build::SI2_SO<int, int, bool>(
              "Greater Than", [](int a, int b) { return a > b; }, exec_preset_all);
          return &fn;
        }
        case NODE_COMPARE_GREATER_EQUAL: {
          static auto fn = mf::build::SI2_SO<int, int, bool>(
              "Greater Equal", [](int a, int b) { return a >= b; }, exec_preset_all);
          return &fn;
        }
        case NODE_COMPARE_EQUAL: {
          static auto fn = mf::build::SI2_SO<int, int, bool>(
              "Equal", [](int a, int b) { return a == b; }, exec_preset_all);
          return &fn;
        }
        case NODE_COMPARE_NOT_EQUAL: {
          static auto fn = mf::build::SI2_SO<int, int, bool>(
              "Not Equal", [](int a, int b) { return a != b; }, exec_preset_all);
          return &fn;
        }
      }
      break;
    case SOCK_VECTOR:
      switch (data->operation) {
        case NODE_COMPARE_LESS_THAN:
          switch (data->mode) {
            case NODE_COMPARE_MODE_AVERAGE: {
              static auto fn = mf::build::SI2_SO<float3, float3, bool>(
                  "Less Than - Average",
                  [](float3 a, float3 b) { return component_average(a) < component_average(b); },
                  exec_preset_all);
              return &fn;
            }
            case NODE_COMPARE_MODE_DOT_PRODUCT: {
              static auto fn = mf::build::SI3_SO<float3, float3, float, bool>(
                  "Less Than - Dot Product",
                  [](float3 a, float3 b, float comp) { return math::dot(a, b) < comp; },
                  exec_preset_first_two);
              return &fn;
            }
            case NODE_COMPARE_MODE_DIRECTION: {
              static auto fn = mf::build::SI3_SO<float3, float3, float, bool>(
                  "Less Than - Direction",
                  [](float3 a, float3 b, float angle) { return angle_v3v3(a, b) < angle; },
                  exec_preset_first_two);
              return &fn;
            }
            case NODE_COMPARE_MODE_ELEMENT: {
              static auto fn = mf::build::SI2_SO<float3, float3, bool>(
                  "Less Than - Element-wise",
                  [](float3 a, float3 b) { return a.x < b.x && a.y < b.y && a.z < b.z; },
                  exec_preset_all);
              return &fn;
            }
            case NODE_COMPARE_MODE_LENGTH: {
              static auto fn = mf::build::SI2_SO<float3, float3, bool>(
                  "Less Than - Length",
                  [](float3 a, float3 b) { return math::length(a) < math::length(b); },
                  exec_preset_all);
              return &fn;
            }
          }
          break;
        case NODE_COMPARE_LESS_EQUAL:
          switch (data->mode) {
            case NODE_COMPARE_MODE_AVERAGE: {
              static auto fn = mf::build::SI2_SO<float3, float3, bool>(
                  "Less Equal - Average",
                  [](float3 a, float3 b) { return component_average(a) <= component_average(b); },
                  exec_preset_all);
              return &fn;
            }
            case NODE_COMPARE_MODE_DOT_PRODUCT: {
              static auto fn = mf::build::SI3_SO<float3, float3, float, bool>(
                  "Less Equal - Dot Product",
                  [](float3 a, float3 b, float comp) { return math::dot(a, b) <= comp; },
                  exec_preset_first_two);
              return &fn;
            }
            case NODE_COMPARE_MODE_DIRECTION: {
              static auto fn = mf::build::SI3_SO<float3, float3, float, bool>(
                  "Less Equal - Direction",
                  [](float3 a, float3 b, float angle) { return angle_v3v3(a, b) <= angle; },
                  exec_preset_first_two);
              return &fn;
            }
            case NODE_COMPARE_MODE_ELEMENT: {
              static auto fn = mf::build::SI2_SO<float3, float3, bool>(
                  "Less Equal - Element-wise",
                  [](float3 a, float3 b) { return a.x <= b.x && a.y <= b.y && a.z <= b.z; },
                  exec_preset_all);
              return &fn;
            }
            case NODE_COMPARE_MODE_LENGTH: {
              static auto fn = mf::build::SI2_SO<float3, float3, bool>(
                  "Less Equal - Length",
                  [](float3 a, float3 b) { return math::length(a) <= math::length(b); },
                  exec_preset_all);
              return &fn;
            }
          }
          break;
        case NODE_COMPARE_GREATER_THAN:
          switch (data->mode) {
            case NODE_COMPARE_MODE_AVERAGE: {
              static auto fn = mf::build::SI2_SO<float3, float3, bool>(
                  "Greater Than - Average",
                  [](float3 a, float3 b) { return component_average(a) > component_average(b); },
                  exec_preset_all);
              return &fn;
            }
            case NODE_COMPARE_MODE_DOT_PRODUCT: {
              static auto fn = mf::build::SI3_SO<float3, float3, float, bool>(
                  "Greater Than - Dot Product",
                  [](float3 a, float3 b, float comp) { return math::dot(a, b) > comp; },
                  exec_preset_first_two);
              return &fn;
            }
            case NODE_COMPARE_MODE_DIRECTION: {
              static auto fn = mf::build::SI3_SO<float3, float3, float, bool>(
                  "Greater Than - Direction",
                  [](float3 a, float3 b, float angle) { return angle_v3v3(a, b) > angle; },
                  exec_preset_first_two);
              return &fn;
            }
            case NODE_COMPARE_MODE_ELEMENT: {
              static auto fn = mf::build::SI2_SO<float3, float3, bool>(
                  "Greater Than - Element-wise",
                  [](float3 a, float3 b) { return a.x > b.x && a.y > b.y && a.z > b.z; },
                  exec_preset_all);
              return &fn;
            }
            case NODE_COMPARE_MODE_LENGTH: {
              static auto fn = mf::build::SI2_SO<float3, float3, bool>(
                  "Greater Than - Length",
                  [](float3 a, float3 b) { return math::length(a) > math::length(b); },
                  exec_preset_all);
              return &fn;
            }
          }
          break;
        case NODE_COMPARE_GREATER_EQUAL:
          switch (data->mode) {
            case NODE_COMPARE_MODE_AVERAGE: {
              static auto fn = mf::build::SI2_SO<float3, float3, bool>(
                  "Greater Equal - Average",
                  [](float3 a, float3 b) { return component_average(a) >= component_average(b); },
                  exec_preset_all);
              return &fn;
            }
            case NODE_COMPARE_MODE_DOT_PRODUCT: {
              static auto fn = mf::build::SI3_SO<float3, float3, float, bool>(
                  "Greater Equal - Dot Product",
                  [](float3 a, float3 b, float comp) { return math::dot(a, b) >= comp; },
                  exec_preset_first_two);
              return &fn;
            }
            case NODE_COMPARE_MODE_DIRECTION: {
              static auto fn = mf::build::SI3_SO<float3, float3, float, bool>(
                  "Greater Equal - Direction",
                  [](float3 a, float3 b, float angle) { return angle_v3v3(a, b) >= angle; },
                  exec_preset_first_two);
              return &fn;
            }
            case NODE_COMPARE_MODE_ELEMENT: {
              static auto fn = mf::build::SI2_SO<float3, float3, bool>(
                  "Greater Equal - Element-wise",
                  [](float3 a, float3 b) { return a.x >= b.x && a.y >= b.y && a.z >= b.z; },
                  exec_preset_all);
              return &fn;
            }
            case NODE_COMPARE_MODE_LENGTH: {
              static auto fn = mf::build::SI2_SO<float3, float3, bool>(
                  "Greater Equal - Length",
                  [](float3 a, float3 b) { return math::length(a) >= math::length(b); },
                  exec_preset_all);
              return &fn;
            }
          }
          break;
        case NODE_COMPARE_EQUAL:
          switch (data->mode) {
            case NODE_COMPARE_MODE_AVERAGE: {
              static auto fn = mf::build::SI3_SO<float3, float3, float, bool>(
                  "Equal - Average",
                  [](float3 a, float3 b, float epsilon) {
                    return abs(component_average(a) - component_average(b)) <= epsilon;
                  },
                  exec_preset_first_two);
              return &fn;
            }
            case NODE_COMPARE_MODE_DOT_PRODUCT: {
              static auto fn = mf::build::SI4_SO<float3, float3, float, float, bool>(
                  "Equal - Dot Product",
                  [](float3 a, float3 b, float comp, float epsilon) {
                    return abs(math::dot(a, b) - comp) <= epsilon;
                  },
                  exec_preset_first_two);
              return &fn;
            }
            case NODE_COMPARE_MODE_DIRECTION: {
              static auto fn = mf::build::SI4_SO<float3, float3, float, float, bool>(
                  "Equal - Direction",
                  [](float3 a, float3 b, float angle, float epsilon) {
                    return abs(angle_v3v3(a, b) - angle) <= epsilon;
                  },
                  exec_preset_first_two);
              return &fn;
            }
            case NODE_COMPARE_MODE_ELEMENT: {
              static auto fn = mf::build::SI3_SO<float3, float3, float, bool>(
                  "Equal - Element-wise",
                  [](float3 a, float3 b, float epsilon) {
                    return abs(a.x - b.x) <= epsilon && abs(a.y - b.y) <= epsilon &&
                           abs(a.z - b.z) <= epsilon;
                  },
                  exec_preset_first_two);
              return &fn;
            }
            case NODE_COMPARE_MODE_LENGTH: {
              static auto fn = mf::build::SI3_SO<float3, float3, float, bool>(
                  "Equal - Length",
                  [](float3 a, float3 b, float epsilon) {
                    return abs(math::length(a) - math::length(b)) <= epsilon;
                  },
                  exec_preset_first_two);
              return &fn;
            }
          }
          break;
        case NODE_COMPARE_NOT_EQUAL:
          switch (data->mode) {
            case NODE_COMPARE_MODE_AVERAGE: {
              static auto fn = mf::build::SI3_SO<float3, float3, float, bool>(
                  "Not Equal - Average",
                  [](float3 a, float3 b, float epsilon) {
                    return abs(component_average(a) - component_average(b)) > epsilon;
                  },
                  exec_preset_first_two);
              return &fn;
            }
            case NODE_COMPARE_MODE_DOT_PRODUCT: {
              static auto fn = mf::build::SI4_SO<float3, float3, float, float, bool>(
                  "Not Equal - Dot Product",
                  [](float3 a, float3 b, float comp, float epsilon) {
                    return abs(math::dot(a, b) - comp) >= epsilon;
                  },
                  exec_preset_first_two);
              return &fn;
            }
            case NODE_COMPARE_MODE_DIRECTION: {
              static auto fn = mf::build::SI4_SO<float3, float3, float, float, bool>(
                  "Not Equal - Direction",
                  [](float3 a, float3 b, float angle, float epsilon) {
                    return abs(angle_v3v3(a, b) - angle) > epsilon;
                  },
                  exec_preset_first_two);
              return &fn;
            }
            case NODE_COMPARE_MODE_ELEMENT: {
              static auto fn = mf::build::SI3_SO<float3, float3, float, bool>(
                  "Not Equal - Element-wise",
                  [](float3 a, float3 b, float epsilon) {
                    return abs(a.x - b.x) > epsilon || abs(a.y - b.y) > epsilon ||
                           abs(a.z - b.z) > epsilon;
                  },
                  exec_preset_first_two);
              return &fn;
            }
            case NODE_COMPARE_MODE_LENGTH: {
              static auto fn = mf::build::SI3_SO<float3, float3, float, bool>(
                  "Not Equal - Length",
                  [](float3 a, float3 b, float epsilon) {
                    return abs(math::length(a) - math::length(b)) > epsilon;
                  },
                  exec_preset_first_two);
              return &fn;
            }
          }
          break;
      }
      break;
    case SOCK_RGBA:
      switch (data->operation) {
        case NODE_COMPARE_EQUAL: {
          static auto fn = mf::build::SI3_SO<ColorGeometry4f, ColorGeometry4f, float, bool>(
              "Equal",
              [](ColorGeometry4f a, ColorGeometry4f b, float epsilon) {
                return abs(a.r - b.r) <= epsilon && abs(a.g - b.g) <= epsilon &&
                       abs(a.b - b.b) <= epsilon;
              },
              exec_preset_first_two);
          return &fn;
        }
        case NODE_COMPARE_NOT_EQUAL: {
          static auto fn = mf::build::SI3_SO<ColorGeometry4f, ColorGeometry4f, float, bool>(
              "Not Equal",
              [](ColorGeometry4f a, ColorGeometry4f b, float epsilon) {
                return abs(a.r - b.r) > epsilon || abs(a.g - b.g) > epsilon ||
                       abs(a.b - b.b) > epsilon;
              },
              exec_preset_first_two);
          return &fn;
        }
        case NODE_COMPARE_COLOR_BRIGHTER: {
          static auto fn = mf::build::SI2_SO<ColorGeometry4f, ColorGeometry4f, bool>(
              "Brighter",
              [](ColorGeometry4f a, ColorGeometry4f b) {
                return rgb_to_grayscale(a) > rgb_to_grayscale(b);
              },
              exec_preset_all);
          return &fn;
        }
        case NODE_COMPARE_COLOR_DARKER: {
          static auto fn = mf::build::SI2_SO<ColorGeometry4f, ColorGeometry4f, bool>(
              "Darker",
              [](ColorGeometry4f a, ColorGeometry4f b) {
                return rgb_to_grayscale(a) < rgb_to_grayscale(b);
              },
              exec_preset_all);
          return &fn;
        }
      }
      break;
    case SOCK_STRING:
      switch (data->operation) {
        case NODE_COMPARE_EQUAL: {
          static auto fn = mf::build::SI2_SO<std::string, std::string, bool>(
              "Equal", [](std::string a, std::string b) { return a == b; });
          return &fn;
        }
        case NODE_COMPARE_NOT_EQUAL: {
          static auto fn = mf::build::SI2_SO<std::string, std::string, bool>(
              "Not Equal", [](std::string a, std::string b) { return a != b; });
          return &fn;
        }
      }
      break;
  }
  return nullptr;
}

static void node_build_multi_function(NodeMultiFunctionBuilder &builder)
{
  const mf::MultiFunction *fn = get_multi_function(builder.node());
  builder.set_matching_fn(fn);
}

}  // namespace blender::nodes::node_fn_compare_cc

void register_node_type_fn_compare()
{
  namespace file_ns = blender::nodes::node_fn_compare_cc;

  static bNodeType ntype;
  fn_node_type_base(&ntype, FN_NODE_COMPARE, "Compare", NODE_CLASS_CONVERTER);
  ntype.declare = file_ns::node_declare;
  ntype.labelfunc = file_ns::node_label;
  ntype.updatefunc = file_ns::node_update;
  ntype.initfunc = file_ns::node_init;
  node_type_storage(
      &ntype, "NodeFunctionCompare", node_free_standard_storage, node_copy_standard_storage);
  ntype.build_multi_function = file_ns::node_build_multi_function;
  ntype.draw_buttons = file_ns::node_layout;
  ntype.gather_link_search_ops = file_ns::node_gather_link_searches;
  nodeRegisterType(&ntype);
}

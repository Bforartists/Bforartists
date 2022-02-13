/* SPDX-License-Identifier: GPL-2.0-or-later */

#include "BLI_task.hh"

#include "RNA_enum_types.h"

#include "UI_interface.h"
#include "UI_resources.h"

#include "NOD_math_functions.hh"

#include "node_geometry_util.hh"

namespace blender::nodes::node_geo_legacy_attribute_math_cc {

static void node_declare(NodeDeclarationBuilder &b)
{
  b.add_input<decl::Geometry>(N_("Geometry"));
  b.add_input<decl::String>(N_("A"));
  b.add_input<decl::Float>(N_("A"), "A_001");
  b.add_input<decl::String>(N_("B"));
  b.add_input<decl::Float>(N_("B"), "B_001");
  b.add_input<decl::String>(N_("C"));
  b.add_input<decl::Float>(N_("C"), "C_001");
  b.add_input<decl::String>(N_("Result"));
  b.add_output<decl::Geometry>(N_("Geometry"));
}

static bool operation_use_input_c(const NodeMathOperation operation)
{
  return ELEM(operation,
              NODE_MATH_MULTIPLY_ADD,
              NODE_MATH_SMOOTH_MIN,
              NODE_MATH_SMOOTH_MAX,
              NODE_MATH_WRAP,
              NODE_MATH_COMPARE);
}

static bool operation_use_input_b(const NodeMathOperation operation)
{
  switch (operation) {
    case NODE_MATH_ADD:
    case NODE_MATH_SUBTRACT:
    case NODE_MATH_MULTIPLY:
    case NODE_MATH_DIVIDE:
    case NODE_MATH_POWER:
    case NODE_MATH_LOGARITHM:
    case NODE_MATH_MINIMUM:
    case NODE_MATH_MAXIMUM:
    case NODE_MATH_LESS_THAN:
    case NODE_MATH_GREATER_THAN:
    case NODE_MATH_MODULO:
    case NODE_MATH_ARCTAN2:
    case NODE_MATH_SNAP:
    case NODE_MATH_WRAP:
    case NODE_MATH_COMPARE:
    case NODE_MATH_MULTIPLY_ADD:
    case NODE_MATH_PINGPONG:
    case NODE_MATH_SMOOTH_MIN:
    case NODE_MATH_SMOOTH_MAX:
      return true;
    case NODE_MATH_SINE:
    case NODE_MATH_COSINE:
    case NODE_MATH_TANGENT:
    case NODE_MATH_ARCSINE:
    case NODE_MATH_ARCCOSINE:
    case NODE_MATH_ARCTANGENT:
    case NODE_MATH_ROUND:
    case NODE_MATH_ABSOLUTE:
    case NODE_MATH_FLOOR:
    case NODE_MATH_CEIL:
    case NODE_MATH_FRACTION:
    case NODE_MATH_SQRT:
    case NODE_MATH_INV_SQRT:
    case NODE_MATH_SIGN:
    case NODE_MATH_EXPONENT:
    case NODE_MATH_RADIANS:
    case NODE_MATH_DEGREES:
    case NODE_MATH_SINH:
    case NODE_MATH_COSH:
    case NODE_MATH_TANH:
    case NODE_MATH_TRUNC:
      return false;
  }
  BLI_assert(false);
  return false;
}

static void node_layout(uiLayout *layout, bContext *UNUSED(C), PointerRNA *ptr)
{
  bNode *node = (bNode *)ptr->data;
  NodeAttributeMath *node_storage = (NodeAttributeMath *)node->storage;
  NodeMathOperation operation = (NodeMathOperation)node_storage->operation;

  uiItemR(layout, ptr, "operation", 0, "", ICON_NONE);

  uiLayoutSetPropSep(layout, true);
  uiLayoutSetPropDecorate(layout, false);
  uiItemR(layout, ptr, "input_type_a", 0, IFACE_("A"), ICON_NONE);
  if (operation_use_input_b(operation)) {
    uiItemR(layout, ptr, "input_type_b", 0, IFACE_("B"), ICON_NONE);
  }
  if (operation_use_input_c(operation)) {
    uiItemR(layout, ptr, "input_type_c", 0, IFACE_("C"), ICON_NONE);
  }
}

static void node_init(bNodeTree *UNUSED(tree), bNode *node)
{
  NodeAttributeMath *data = MEM_cnew<NodeAttributeMath>(__func__);

  data->operation = NODE_MATH_ADD;
  data->input_type_a = GEO_NODE_ATTRIBUTE_INPUT_ATTRIBUTE;
  data->input_type_b = GEO_NODE_ATTRIBUTE_INPUT_ATTRIBUTE;
  data->input_type_c = GEO_NODE_ATTRIBUTE_INPUT_ATTRIBUTE;
  node->storage = data;
}

static void geo_node_math_label(const bNodeTree *UNUSED(ntree),
                                const bNode *node,
                                char *label,
                                int maxlen)
{
  NodeAttributeMath &node_storage = *(NodeAttributeMath *)node->storage;
  const char *name;
  bool enum_label = RNA_enum_name(rna_enum_node_math_items, node_storage.operation, &name);
  if (!enum_label) {
    name = "Unknown";
  }
  BLI_strncpy(label, IFACE_(name), maxlen);
}

static void node_update(bNodeTree *ntree, bNode *node)
{
  NodeAttributeMath &node_storage = *(NodeAttributeMath *)node->storage;
  NodeMathOperation operation = static_cast<NodeMathOperation>(node_storage.operation);

  update_attribute_input_socket_availabilities(
      *ntree, *node, "A", (GeometryNodeAttributeInputMode)node_storage.input_type_a);
  update_attribute_input_socket_availabilities(
      *ntree,
      *node,
      "B",
      (GeometryNodeAttributeInputMode)node_storage.input_type_b,
      operation_use_input_b(operation));
  update_attribute_input_socket_availabilities(
      *ntree,
      *node,
      "C",
      (GeometryNodeAttributeInputMode)node_storage.input_type_c,
      operation_use_input_c(operation));
}

static void do_math_operation(const VArray<float> &span_a,
                              const VArray<float> &span_b,
                              const VArray<float> &span_c,
                              MutableSpan<float> span_result,
                              const NodeMathOperation operation)
{
  bool success = try_dispatch_float_math_fl_fl_fl_to_fl(
      operation, [&](auto math_function, const FloatMathOperationInfo &UNUSED(info)) {
        threading::parallel_for(IndexRange(span_result.size()), 512, [&](IndexRange range) {
          for (const int i : range) {
            span_result[i] = math_function(span_a[i], span_b[i], span_c[i]);
          }
        });
      });
  BLI_assert(success);
  UNUSED_VARS_NDEBUG(success);
}

static void do_math_operation(const VArray<float> &span_a,
                              const VArray<float> &span_b,
                              MutableSpan<float> span_result,
                              const NodeMathOperation operation)
{
  bool success = try_dispatch_float_math_fl_fl_to_fl(
      operation, [&](auto math_function, const FloatMathOperationInfo &UNUSED(info)) {
        threading::parallel_for(IndexRange(span_result.size()), 1024, [&](IndexRange range) {
          for (const int i : range) {
            span_result[i] = math_function(span_a[i], span_b[i]);
          }
        });
      });
  BLI_assert(success);
  UNUSED_VARS_NDEBUG(success);
}

static void do_math_operation(const VArray<float> &span_input,
                              MutableSpan<float> span_result,
                              const NodeMathOperation operation)
{
  bool success = try_dispatch_float_math_fl_to_fl(
      operation, [&](auto math_function, const FloatMathOperationInfo &UNUSED(info)) {
        threading::parallel_for(IndexRange(span_result.size()), 1024, [&](IndexRange range) {
          for (const int i : range) {
            span_result[i] = math_function(span_input[i]);
          }
        });
      });
  BLI_assert(success);
  UNUSED_VARS_NDEBUG(success);
}

static AttributeDomain get_result_domain(const GeometryComponent &component,
                                         const GeoNodeExecParams &params,
                                         const NodeMathOperation operation,
                                         StringRef result_name)
{
  /* Use the domain of the result attribute if it already exists. */
  std::optional<AttributeMetaData> result_info = component.attribute_get_meta_data(result_name);
  if (result_info) {
    return result_info->domain;
  }

  /* Otherwise use the highest priority domain from existing input attributes, or the default. */
  const AttributeDomain default_domain = ATTR_DOMAIN_POINT;
  if (operation_use_input_b(operation)) {
    if (operation_use_input_c(operation)) {
      return params.get_highest_priority_input_domain({"A", "B", "C"}, component, default_domain);
    }
    return params.get_highest_priority_input_domain({"A", "B"}, component, default_domain);
  }
  return params.get_highest_priority_input_domain({"A"}, component, default_domain);
}

static void attribute_math_calc(GeometryComponent &component, const GeoNodeExecParams &params)
{
  const bNode &node = params.node();
  const NodeAttributeMath *node_storage = (const NodeAttributeMath *)node.storage;
  const NodeMathOperation operation = static_cast<NodeMathOperation>(node_storage->operation);
  const std::string result_name = params.get_input<std::string>("Result");

  /* The result type of this node is always float. */
  const AttributeDomain result_domain = get_result_domain(
      component, params, operation, result_name);

  OutputAttribute_Typed<float> attribute_result =
      component.attribute_try_get_for_output_only<float>(result_name, result_domain);
  if (!attribute_result) {
    return;
  }

  VArray<float> attribute_a = params.get_input_attribute<float>(
      "A", component, result_domain, 0.0f);

  MutableSpan<float> result_span = attribute_result.as_span();

  /* Note that passing the data with `get_internal_span<float>()` works
   * because the attributes were accessed with #CD_PROP_FLOAT. */
  if (operation_use_input_b(operation)) {
    VArray<float> attribute_b = params.get_input_attribute<float>(
        "B", component, result_domain, 0.0f);
    if (operation_use_input_c(operation)) {
      VArray<float> attribute_c = params.get_input_attribute<float>(
          "C", component, result_domain, 0.0f);
      do_math_operation(attribute_a, attribute_b, attribute_c, result_span, operation);
    }
    else {
      do_math_operation(attribute_a, attribute_b, result_span, operation);
    }
  }
  else {
    do_math_operation(attribute_a, result_span, operation);
  }

  attribute_result.save();
}

static void node_geo_exec(GeoNodeExecParams params)
{
  GeometrySet geometry_set = params.extract_input<GeometrySet>("Geometry");

  geometry_set = geometry::realize_instances_legacy(geometry_set);

  if (geometry_set.has<MeshComponent>()) {
    attribute_math_calc(geometry_set.get_component_for_write<MeshComponent>(), params);
  }
  if (geometry_set.has<PointCloudComponent>()) {
    attribute_math_calc(geometry_set.get_component_for_write<PointCloudComponent>(), params);
  }
  if (geometry_set.has<CurveComponent>()) {
    attribute_math_calc(geometry_set.get_component_for_write<CurveComponent>(), params);
  }

  params.set_output("Geometry", geometry_set);
}

}  // namespace blender::nodes::node_geo_legacy_attribute_math_cc

void register_node_type_geo_attribute_math()
{
  namespace file_ns = blender::nodes::node_geo_legacy_attribute_math_cc;

  static bNodeType ntype;

  geo_node_type_base(
      &ntype, GEO_NODE_LEGACY_ATTRIBUTE_MATH, "Attribute Math", NODE_CLASS_ATTRIBUTE);
  ntype.declare = file_ns::node_declare;
  ntype.geometry_node_execute = file_ns::node_geo_exec;
  ntype.draw_buttons = file_ns::node_layout;
  ntype.labelfunc = file_ns::geo_node_math_label;
  node_type_update(&ntype, file_ns::node_update);
  node_type_init(&ntype, file_ns::node_init);
  node_type_storage(
      &ntype, "NodeAttributeMath", node_free_standard_storage, node_copy_standard_storage);
  nodeRegisterType(&ntype);
}

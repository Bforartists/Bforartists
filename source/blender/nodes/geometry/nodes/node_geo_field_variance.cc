/* SPDX-FileCopyrightText: 2025 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#include "BKE_attribute_math.hh"

#include "BLI_array.hh"
#include "BLI_generic_virtual_array.hh"
#include "BLI_virtual_array.hh"

#include "NOD_rna_define.hh"
#include "NOD_socket_search_link.hh"

#include "RNA_enum_types.hh"

#include "node_geometry_util.hh"

#include "UI_interface.hh"
#include "UI_resources.hh"

#include <numeric>

namespace blender::nodes::node_geo_field_variance_cc {

static void node_declare(NodeDeclarationBuilder &b)
{
  const bNode *node = b.node_or_null();

  if (node != nullptr) {
    const eCustomDataType data_type = eCustomDataType(node->custom1);
    b.add_input(data_type, "Value")
        .supports_field()
        .description("The values the standard deviation and variance will be calculated from");
  }

  b.add_input<decl::Int>("Group ID", "Group Index")
      .supports_field()
      .hide_value()
      .description("An index used to group values together for multiple separate operations");

  if (node != nullptr) {
    const eCustomDataType data_type = eCustomDataType(node->custom1);
    b.add_output(data_type, "Standard Deviation")
        .field_source_reference_all()
        .description("The square root of the variance for each group");
    b.add_output(data_type, "Variance")
        .field_source_reference_all()
        .description("The expected squared deviation from the mean for each group");
  }
}

static void node_layout(uiLayout *layout, bContext * /*C*/, PointerRNA *ptr)
{
  uiItemR(layout, ptr, "data_type", UI_ITEM_NONE, "", ICON_NONE);
  uiItemR(layout, ptr, "domain", UI_ITEM_NONE, "", ICON_NONE);
}

static void node_init(bNodeTree * /*tree*/, bNode *node)
{
  node->custom1 = CD_PROP_FLOAT;
  node->custom2 = int16_t(AttrDomain::Point);
}

enum class Operation { StdDev = 0, Variance = 1 };

static std::optional<eCustomDataType> node_type_from_other_socket(const bNodeSocket &socket)
{
  switch (socket.type) {
    case SOCK_FLOAT:
    case SOCK_BOOLEAN:
    case SOCK_INT:
      return CD_PROP_FLOAT;
    case SOCK_VECTOR:
    case SOCK_RGBA:
      return CD_PROP_FLOAT3;
    default:
      return std::nullopt;
  }
}

static void node_gather_link_searches(GatherLinkSearchOpParams &params)
{
  const NodeDeclaration &declaration = *params.node_type().static_declaration;
  search_link_ops_for_declarations(params, declaration.inputs);

  const std::optional<eCustomDataType> type = node_type_from_other_socket(params.other_socket());
  if (!type) {
    return;
  }
  if (params.in_out() == SOCK_OUT) {
    params.add_item(
        IFACE_("Standard Deviation"),
        [type](LinkSearchOpParams &params) {
          bNode &node = params.add_node("GeometryNodeFieldVariance");
          node.custom1 = *type;
          params.update_and_connect_available_socket(node, "Standard Deviation");
        },
        0);
    params.add_item(
        IFACE_("Variance"),
        [type](LinkSearchOpParams &params) {
          bNode &node = params.add_node("GeometryNodeFieldVariance");
          node.custom1 = *type;
          params.update_and_connect_available_socket(node, "Variance");
        },
        -1);
  }
  else {
    params.add_item(
        IFACE_("Value"),
        [type](LinkSearchOpParams &params) {
          bNode &node = params.add_node("GeometryNodeFieldVariance");
          node.custom1 = *type;
          params.update_and_connect_available_socket(node, "Value");
        },
        0);
  }
}

class FieldVarianceInput final : public bke::GeometryFieldInput {
 private:
  GField input_;
  Field<int> group_index_;
  AttrDomain source_domain_;
  Operation operation_;

 public:
  FieldVarianceInput(const AttrDomain source_domain,
                     GField input,
                     Field<int> group_index,
                     Operation operation)
      : bke::GeometryFieldInput(input.cpp_type(), "Calculation"),
        input_(std::move(input)),
        group_index_(std::move(group_index)),
        source_domain_(source_domain),
        operation_(operation)
  {
  }

  GVArray get_varray_for_context(const bke::GeometryFieldContext &context,
                                 const IndexMask & /*mask*/) const final
  {
    const AttributeAccessor attributes = *context.attributes();
    const int64_t domain_size = attributes.domain_size(source_domain_);
    if (domain_size == 0) {
      return {};
    }

    const bke::GeometryFieldContext source_context{context, source_domain_};
    fn::FieldEvaluator evaluator{source_context, domain_size};
    evaluator.add(input_);
    evaluator.add(group_index_);
    evaluator.evaluate();
    const GVArray g_values = evaluator.get_evaluated(0);
    const VArray<int> group_indices = evaluator.get_evaluated<int>(1);

    GVArray g_outputs;

    bke::attribute_math::convert_to_static_type(g_values.type(), [&](auto dummy) {
      using T = decltype(dummy);
      if constexpr (is_same_any_v<T, int, float, float3>) {
        const VArraySpan<T> values = g_values.typed<T>();

        if (operation_ == Operation::StdDev) {
          if (group_indices.is_single()) {
            const T mean = std::reduce(values.begin(), values.end(), T()) / domain_size;
            const T sum_of_squared_diffs = std::reduce(
                values.begin(), values.end(), T(), [mean](T accumulator, const T &value) {
                  T difference = mean - value;
                  return accumulator + difference * difference;
                });
            g_outputs = VArray<T>::ForSingle(math::sqrt(sum_of_squared_diffs / domain_size),
                                             domain_size);
          }
          else {
            Map<int, std::pair<T, int>> sum_and_counts;
            Map<int, T> deviations;

            for (const int i : values.index_range()) {
              auto &pair = sum_and_counts.lookup_or_add(group_indices[i], std::make_pair(T(), 0));
              pair.first = pair.first + values[i];
              pair.second = pair.second + 1;
            }

            for (const int i : values.index_range()) {
              const auto &pair = sum_and_counts.lookup(group_indices[i]);
              T mean = pair.first / pair.second;
              T deviation = (mean - values[i]);
              deviation = deviation * deviation;

              T &dev_sum = deviations.lookup_or_add(group_indices[i], T());
              dev_sum = dev_sum + deviation;
            }

            Array<T> outputs(domain_size);
            for (const int i : values.index_range()) {
              const auto &pair = sum_and_counts.lookup(group_indices[i]);
              outputs[i] = math::sqrt(deviations.lookup(group_indices[i]) / pair.second);
            }
            g_outputs = VArray<T>::ForContainer(std::move(outputs));
          }
        }
        else {
          if (group_indices.is_single()) {
            const T mean = std::reduce(values.begin(), values.end(), T()) / domain_size;
            const T sum_of_squared_diffs = std::reduce(
                values.begin(), values.end(), T(), [mean](T accumulator, const T &value) {
                  T difference = mean - value;
                  return accumulator + difference * difference;
                });
            g_outputs = VArray<T>::ForSingle(sum_of_squared_diffs / domain_size, domain_size);
          }
          else {
            Map<int, std::pair<T, int>> sum_and_counts;
            Map<int, T> deviations;

            for (const int i : values.index_range()) {
              auto &pair = sum_and_counts.lookup_or_add(group_indices[i], std::make_pair(T(), 0));
              pair.first = pair.first + values[i];
              pair.second = pair.second + 1;
            }

            for (const int i : values.index_range()) {
              const auto &pair = sum_and_counts.lookup(group_indices[i]);
              T mean = pair.first / pair.second;
              T deviation = (mean - values[i]);
              deviation = deviation * deviation;

              T &dev_sum = deviations.lookup_or_add(group_indices[i], T());
              dev_sum = dev_sum + deviation;
            }

            Array<T> outputs(domain_size);
            for (const int i : values.index_range()) {
              const auto &pair = sum_and_counts.lookup(group_indices[i]);
              outputs[i] = deviations.lookup(group_indices[i]) / pair.second;
            }
            g_outputs = VArray<T>::ForContainer(std::move(outputs));
          }
        }
      }
    });

    return attributes.adapt_domain(std::move(g_outputs), source_domain_, context.domain());
  }

  uint64_t hash() const override
  {
    return get_default_hash(input_, group_index_, source_domain_, operation_);
  }

  bool is_equal_to(const fn::FieldNode &other) const override
  {
    if (const FieldVarianceInput *other_field = dynamic_cast<const FieldVarianceInput *>(&other)) {
      return input_ == other_field->input_ && group_index_ == other_field->group_index_ &&
             source_domain_ == other_field->source_domain_ &&
             operation_ == other_field->operation_;
    }
    return false;
  }

  std::optional<AttrDomain> preferred_domain(
      const GeometryComponent & /*component*/) const override
  {
    return source_domain_;
  }
};

static void node_geo_exec(GeoNodeExecParams params)
{
  const AttrDomain source_domain = AttrDomain(params.node().custom2);

  const Field<int> group_index_field = params.extract_input<Field<int>>("Group Index");
  const GField input_field = params.extract_input<GField>("Value");
  if (params.output_is_required("Standard Deviation")) {
    params.set_output<GField>(
        "Standard Deviation",
        GField{std::make_shared<FieldVarianceInput>(
            source_domain, input_field, group_index_field, Operation::StdDev)});
  }
  if (params.output_is_required("Variance")) {
    params.set_output<GField>(
        "Variance",
        GField{std::make_shared<FieldVarianceInput>(
            source_domain, input_field, group_index_field, Operation::Variance)});
  }
}

static void node_rna(StructRNA *srna)
{
  static EnumPropertyItem items[] = {
      {CD_PROP_FLOAT, "FLOAT", 0, "Float", "Floating-point value"},
      {CD_PROP_FLOAT3, "FLOAT_VECTOR", 0, "Vector", "3D vector with floating-point values"},
      {0, nullptr, 0, nullptr, nullptr},
  };

  RNA_def_node_enum(srna,
                    "data_type",
                    "Data Type",
                    "Type of data the outputs are calculated from",
                    items,
                    NOD_inline_enum_accessors(custom1),
                    CD_PROP_FLOAT);

  RNA_def_node_enum(srna,
                    "domain",
                    "Domain",
                    "",
                    rna_enum_attribute_domain_items,
                    NOD_inline_enum_accessors(custom2),
                    int(AttrDomain::Point),
                    nullptr,
                    true);
}

static void node_register()
{
  static blender::bke::bNodeType ntype;

  geo_node_type_base(&ntype, "GeometryNodeFieldVariance");
  ntype.ui_name = "Field Variance";
  ntype.ui_description = "Calculate the standard deviation and variance of a given field";
  ntype.nclass = NODE_CLASS_CONVERTER;
  ntype.geometry_node_execute = node_geo_exec;
  ntype.initfunc = node_init;
  ntype.draw_buttons = node_layout;
  ntype.declare = node_declare;
  ntype.gather_link_search_ops = node_gather_link_searches;
  blender::bke::node_register_type(ntype);
  node_rna(ntype.rna_ext.srna);
}
NOD_REGISTER_NODE(node_register)

}  // namespace blender::nodes::node_geo_field_variance_cc

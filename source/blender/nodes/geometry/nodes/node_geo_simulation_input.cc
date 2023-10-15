/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#include "BKE_compute_contexts.hh"
#include "BKE_scene.h"

#include "DEG_depsgraph_query.hh"

#include "UI_interface.hh"
#include "UI_resources.hh"

#include "NOD_geometry.hh"
#include "NOD_socket.hh"
#include "NOD_socket_items.hh"
#include "NOD_zone_socket_items.hh"

#include "node_geometry_util.hh"

namespace blender::nodes::node_geo_simulation_input_cc {

NODE_STORAGE_FUNCS(NodeGeometrySimulationInput);

class LazyFunctionForSimulationInputNode final : public LazyFunction {
  const bNode &node_;
  int32_t output_node_id_;
  Span<NodeSimulationItem> simulation_items_;

 public:
  LazyFunctionForSimulationInputNode(const bNodeTree &node_tree,
                                     const bNode &node,
                                     GeometryNodesLazyFunctionGraphInfo &own_lf_graph_info)
      : node_(node)
  {
    debug_name_ = "Simulation Input";
    output_node_id_ = node_storage(node).output_node_id;
    const bNode &output_node = *node_tree.node_by_id(output_node_id_);
    const NodeGeometrySimulationOutput &storage = *static_cast<NodeGeometrySimulationOutput *>(
        output_node.storage);
    simulation_items_ = {storage.items, storage.items_num};

    MutableSpan<int> lf_index_by_bsocket = own_lf_graph_info.mapping.lf_index_by_bsocket;
    lf_index_by_bsocket[node.output_socket(0).index_in_tree()] = outputs_.append_and_get_index_as(
        "Delta Time", CPPType::get<ValueOrField<float>>());

    for (const int i : simulation_items_.index_range()) {
      const NodeSimulationItem &item = simulation_items_[i];
      const bNodeSocket &input_bsocket = node.input_socket(i);
      const bNodeSocket &output_bsocket = node.output_socket(i + 1);

      const CPPType &type = get_simulation_item_cpp_type(item);

      lf_index_by_bsocket[input_bsocket.index_in_tree()] = inputs_.append_and_get_index_as(
          item.name, type, lf::ValueUsage::Maybe);
      lf_index_by_bsocket[output_bsocket.index_in_tree()] = outputs_.append_and_get_index_as(
          item.name, type);
    }
  }

  void execute_impl(lf::Params &params, const lf::Context &context) const final
  {
    const GeoNodesLFUserData &user_data = *static_cast<const GeoNodesLFUserData *>(
        context.user_data);
    if (!user_data.modifier_data) {
      params.set_default_remaining_outputs();
      return;
    }
    const GeoNodesModifierData &modifier_data = *user_data.modifier_data;
    if (!modifier_data.simulation_params) {
      params.set_default_remaining_outputs();
      return;
    }
    std::optional<FoundNestedNodeID> found_id = find_nested_node_id(user_data, output_node_id_);
    if (!found_id) {
      params.set_default_remaining_outputs();
      return;
    }
    if (found_id->is_in_loop) {
      params.set_default_remaining_outputs();
      return;
    }
    SimulationZoneBehavior *zone_behavior = modifier_data.simulation_params->get(found_id->id);
    if (!zone_behavior) {
      params.set_default_remaining_outputs();
      return;
    }
    sim_input::Behavior &input_behavior = zone_behavior->input;
    float delta_time = 0.0f;
    if (auto *info = std::get_if<sim_input::OutputCopy>(&input_behavior)) {
      delta_time = info->delta_time;
      this->output_simulation_state_copy(params, user_data, info->state);
    }
    else if (auto *info = std::get_if<sim_input::OutputMove>(&input_behavior)) {
      delta_time = info->delta_time;
      this->output_simulation_state_move(params, user_data, std::move(info->state));
    }
    else if (std::get_if<sim_input::PassThrough>(&input_behavior)) {
      delta_time = 0.0f;
      this->pass_through(params, user_data);
    }
    else {
      BLI_assert_unreachable();
    }
    if (!params.output_was_set(0)) {
      params.set_output(0, fn::ValueOrField<float>(delta_time));
    }
  }

  void output_simulation_state_copy(lf::Params &params,
                                    const GeoNodesLFUserData &user_data,
                                    const bke::bake::BakeStateRef &zone_state) const
  {
    Array<void *> outputs(simulation_items_.size());
    for (const int i : simulation_items_.index_range()) {
      outputs[i] = params.get_output_data_ptr(i + 1);
    }
    copy_simulation_state_to_values(simulation_items_,
                                    zone_state,
                                    *user_data.modifier_data->self_object,
                                    *user_data.compute_context,
                                    node_,
                                    outputs);
    for (const int i : simulation_items_.index_range()) {
      params.output_set(i + 1);
    }
  }

  void output_simulation_state_move(lf::Params &params,
                                    const GeoNodesLFUserData &user_data,
                                    bke::bake::BakeState zone_state) const
  {
    Array<void *> outputs(simulation_items_.size());
    for (const int i : simulation_items_.index_range()) {
      outputs[i] = params.get_output_data_ptr(i + 1);
    }
    move_simulation_state_to_values(simulation_items_,
                                    std::move(zone_state),
                                    *user_data.modifier_data->self_object,
                                    *user_data.compute_context,
                                    node_,
                                    outputs);
    for (const int i : simulation_items_.index_range()) {
      params.output_set(i + 1);
    }
  }

  void pass_through(lf::Params &params, const GeoNodesLFUserData &user_data) const
  {
    Array<void *> input_values(inputs_.size());
    for (const int i : inputs_.index_range()) {
      input_values[i] = params.try_get_input_data_ptr_or_request(i);
    }
    if (input_values.as_span().contains(nullptr)) {
      /* Wait for inputs to be computed. */
      return;
    }
    /* Instead of outputting the initial values directly, convert them to a simulation state and
     * then back. This ensures that some geometry processing happens on the data consistently (e.g.
     * removing anonymous attributes). */
    bke::bake::BakeState bake_state = move_values_to_simulation_state(simulation_items_,
                                                                      input_values);
    this->output_simulation_state_move(params, user_data, std::move(bake_state));
  }
};

}  // namespace blender::nodes::node_geo_simulation_input_cc

namespace blender::nodes {

std::unique_ptr<LazyFunction> get_simulation_input_lazy_function(
    const bNodeTree &node_tree,
    const bNode &node,
    GeometryNodesLazyFunctionGraphInfo &own_lf_graph_info)
{
  namespace file_ns = blender::nodes::node_geo_simulation_input_cc;
  BLI_assert(node.type == GEO_NODE_SIMULATION_INPUT);
  return std::make_unique<file_ns::LazyFunctionForSimulationInputNode>(
      node_tree, node, own_lf_graph_info);
}

}  // namespace blender::nodes

namespace blender::nodes::node_geo_simulation_input_cc {

static void node_declare(NodeDeclarationBuilder &b)
{
  b.add_output<decl::Float>("Delta Time");

  const bNode *node = b.node_or_null();
  const bNodeTree *node_tree = b.tree_or_null();
  if (ELEM(nullptr, node, node_tree)) {
    return;
  }

  const bNode *output_node = node_tree->node_by_id(node_storage(*node).output_node_id);
  if (!output_node) {
    return;
  }
  const auto &output_storage = *static_cast<const NodeGeometrySimulationOutput *>(
      output_node->storage);

  for (const int i : IndexRange(output_storage.items_num)) {
    const NodeSimulationItem &item = output_storage.items[i];
    const eNodeSocketDatatype socket_type = eNodeSocketDatatype(item.socket_type);
    const StringRef name = item.name;
    const std::string identifier = SimulationItemsAccessor::socket_identifier_for_item(item);
    auto &input_decl = b.add_input(socket_type, name, identifier);
    auto &output_decl = b.add_output(socket_type, name, identifier);
    if (socket_type_supports_fields(socket_type)) {
      input_decl.supports_field();
      output_decl.dependent_field({input_decl.input_index()});
    }
  }
  b.add_input<decl::Extend>("", "__extend__");
  b.add_output<decl::Extend>("", "__extend__");
}

static void node_init(bNodeTree * /*tree*/, bNode *node)
{
  NodeGeometrySimulationInput *data = MEM_cnew<NodeGeometrySimulationInput>(__func__);
  /* Needs to be initialized for the node to work. */
  data->output_node_id = 0;
  node->storage = data;
}

static bool node_insert_link(bNodeTree *ntree, bNode *node, bNodeLink *link)
{
  bNode *output_node = ntree->node_by_id(node_storage(*node).output_node_id);
  if (!output_node) {
    return true;
  }
  return socket_items::try_add_item_via_any_extend_socket<SimulationItemsAccessor>(
      *ntree, *node, *output_node, *link);
}

static void node_register()
{
  static bNodeType ntype;
  geo_node_type_base(&ntype, GEO_NODE_SIMULATION_INPUT, "Simulation Input", NODE_CLASS_INTERFACE);
  ntype.initfunc = node_init;
  ntype.declare = node_declare;
  ntype.insert_link = node_insert_link;
  ntype.gather_link_search_ops = nullptr;
  node_type_storage(&ntype,
                    "NodeGeometrySimulationInput",
                    node_free_standard_storage,
                    node_copy_standard_storage);
  nodeRegisterType(&ntype);
}
NOD_REGISTER_NODE(node_register)

}  // namespace blender::nodes::node_geo_simulation_input_cc

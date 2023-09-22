/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#include "NOD_node_declaration.hh"
#include "NOD_socket_declarations.hh"
#include "NOD_socket_declarations_geometry.hh"

#include "BLI_stack.hh"
#include "BLI_utildefines.h"

#include "BKE_geometry_fields.hh"
#include "BKE_node.hh"
#include "BKE_node_runtime.hh"

namespace blender::nodes {

void build_node_declaration(const bNodeType &typeinfo, NodeDeclaration &r_declaration)
{
  NodeDeclarationBuilder node_decl_builder{r_declaration};
  typeinfo.declare(node_decl_builder);
  node_decl_builder.finalize();
}

void build_node_declaration_dynamic(const bNodeTree &node_tree,
                                    const bNode &node,
                                    NodeDeclaration &r_declaration)
{
  r_declaration.items.clear();
  r_declaration.inputs.clear();
  r_declaration.outputs.clear();
  node.typeinfo->declare_dynamic(node_tree, node, r_declaration);
}

void NodeDeclarationBuilder::finalize()
{
  if (is_function_node_) {
    for (std::unique_ptr<BaseSocketDeclarationBuilder> &socket_builder : socket_builders_) {
      if (SocketDeclaration *socket_decl = socket_builder->input_declaration()) {
        if (socket_decl->input_field_type != InputSocketFieldType::Implicit) {
          socket_decl->input_field_type = InputSocketFieldType::IsSupported;
        }
      }
    }
    for (std::unique_ptr<BaseSocketDeclarationBuilder> &socket_builder : socket_builders_) {
      if (SocketDeclaration *socket_decl = socket_builder->output_declaration()) {
        socket_decl->output_field_dependency = OutputFieldDependency::ForDependentField();
        socket_builder->reference_pass_all_ = true;
      }
    }
  }

  Vector<int> geometry_inputs;
  for (const int i : declaration_.inputs.index_range()) {
    if (dynamic_cast<decl::Geometry *>(declaration_.inputs[i])) {
      geometry_inputs.append(i);
    }
  }
  Vector<int> geometry_outputs;
  for (const int i : declaration_.outputs.index_range()) {
    if (dynamic_cast<decl::Geometry *>(declaration_.outputs[i])) {
      geometry_outputs.append(i);
    }
  }

  for (std::unique_ptr<BaseSocketDeclarationBuilder> &socket_builder : socket_builders_) {
    if (!socket_builder->input_declaration()) {
      continue;
    }

    if (socket_builder->field_on_all_) {
      aal::RelationsInNode &relations = this->get_anonymous_attribute_relations();
      const int field_input = socket_builder->index_in_;
      for (const int geometry_input : geometry_inputs) {
        relations.eval_relations.append({field_input, geometry_input});
      }
    }
  }
  for (std::unique_ptr<BaseSocketDeclarationBuilder> &socket_builder : socket_builders_) {
    if (!socket_builder->output_declaration()) {
      continue;
    }

    if (socket_builder->field_on_all_) {
      aal::RelationsInNode &relations = this->get_anonymous_attribute_relations();
      const int field_output = socket_builder->index_out_;
      for (const int geometry_output : geometry_outputs) {
        relations.available_relations.append({field_output, geometry_output});
      }
    }
    if (socket_builder->reference_pass_all_) {
      aal::RelationsInNode &relations = this->get_anonymous_attribute_relations();
      const int field_output = socket_builder->index_out_;
      for (const int input_i : declaration_.inputs.index_range()) {
        SocketDeclaration &input_socket_decl = *declaration_.inputs[input_i];
        if (input_socket_decl.input_field_type != InputSocketFieldType::None) {
          relations.reference_relations.append({input_i, field_output});
        }
      }
    }
    if (socket_builder->propagate_from_all_) {
      aal::RelationsInNode &relations = this->get_anonymous_attribute_relations();
      const int geometry_output = socket_builder->index_out_;
      for (const int geometry_input : geometry_inputs) {
        relations.propagate_relations.append({geometry_input, geometry_output});
      }
    }
  }

  BLI_assert(declaration_.is_valid());
}

void NodeDeclarationBuilder::set_active_panel_builder(const PanelDeclarationBuilder *panel_builder)
{
  if (panel_builders_.is_empty()) {
    BLI_assert(panel_builder == nullptr);
    return;
  }

  BLI_assert(!panel_builder || !panel_builder->is_complete_);
  PanelDeclarationBuilder *last_panel_builder = panel_builders_.last().get();
  if (last_panel_builder != panel_builder) {
    last_panel_builder->is_complete_ = true;
  }
}

namespace anonymous_attribute_lifetime {

bool operator==(const RelationsInNode &a, const RelationsInNode &b)
{
  return a.propagate_relations == b.propagate_relations &&
         a.reference_relations == b.reference_relations && a.eval_relations == b.eval_relations &&
         a.available_relations == b.available_relations &&
         a.available_on_none == b.available_on_none;
}

bool operator!=(const RelationsInNode &a, const RelationsInNode &b)
{
  return !(a == b);
}

std::ostream &operator<<(std::ostream &stream, const RelationsInNode &relations)
{
  stream << "Propagate Relations: " << relations.propagate_relations.size() << "\n";
  for (const PropagateRelation &relation : relations.propagate_relations) {
    stream << "  " << relation.from_geometry_input << " -> " << relation.to_geometry_output
           << "\n";
  }
  stream << "Reference Relations: " << relations.reference_relations.size() << "\n";
  for (const ReferenceRelation &relation : relations.reference_relations) {
    stream << "  " << relation.from_field_input << " -> " << relation.to_field_output << "\n";
  }
  stream << "Eval Relations: " << relations.eval_relations.size() << "\n";
  for (const EvalRelation &relation : relations.eval_relations) {
    stream << "  eval " << relation.field_input << " on " << relation.geometry_input << "\n";
  }
  stream << "Available Relations: " << relations.available_relations.size() << "\n";
  for (const AvailableRelation &relation : relations.available_relations) {
    stream << "  " << relation.field_output << " available on " << relation.geometry_output
           << "\n";
  }
  stream << "Available on None: " << relations.available_on_none.size() << "\n";
  for (const int i : relations.available_on_none) {
    stream << "  output " << i << " available on none\n";
  }
  return stream;
}

}  // namespace anonymous_attribute_lifetime

bool NodeDeclaration::is_valid() const
{
  if (!this->use_custom_socket_order) {
    /* Skip validation for conventional socket layouts. */
    return true;
  }

  /* Validation state for the interface root items as well as any panel content. */
  struct ValidationState {
    /* Remaining number of items expected in a panel */
    int remaining_items = 0;
    /* Sockets first, followed by panels. */
    NodeTreeInterfaceItemType item_type = NODE_INTERFACE_SOCKET;
    /* Output sockets first, followed by input sockets. */
    eNodeSocketInOut socket_in_out = SOCK_OUT;
  };

  Stack<ValidationState> panel_states;
  panel_states.push({});

  for (const ItemDeclarationPtr &item_decl : items) {
    BLI_assert(panel_states.size() >= 1);
    ValidationState &state = panel_states.peek();

    if (const SocketDeclaration *socket_decl = dynamic_cast<const SocketDeclaration *>(
            item_decl.get()))
    {
      if (state.item_type != NODE_INTERFACE_SOCKET) {
        std::cout << "Socket added after panel" << std::endl;
        return false;
      }

      /* Check for consistent outputs.., inputs.. blocks. */
      if (state.socket_in_out == SOCK_OUT && socket_decl->in_out == SOCK_IN) {
        /* Start of input sockets. */
        state.socket_in_out = SOCK_IN;
      }
      if (socket_decl->in_out != state.socket_in_out) {
        std::cout << "Output socket added after input socket" << std::endl;
        return false;
      }

      /* Item counting for the panels, but ignore for root items. */
      if (panel_states.size() > 1) {
        if (state.remaining_items <= 0) {
          std::cout << "More sockets than expected in panel" << std::endl;
          return false;
        }
        --state.remaining_items;
        /* Panel closed after last item is added. */
        if (state.remaining_items == 0) {
          panel_states.pop();
        }
      }
    }
    else if (const PanelDeclaration *panel_decl = dynamic_cast<const PanelDeclaration *>(
                 item_decl.get()))
    {
      if (state.item_type == NODE_INTERFACE_SOCKET) {
        /* Start of panels section */
        state.item_type = NODE_INTERFACE_PANEL;
      }
      BLI_assert(state.item_type == NODE_INTERFACE_PANEL);

      if (panel_decl->num_child_decls > 0) {
        /* New panel started. */
        panel_states.push({panel_decl->num_child_decls});
      }
    }
    else {
      BLI_assert_unreachable();
      return false;
    }
  }

  /* All panels complete? */
  if (panel_states.size() != 1) {
    std::cout << "Incomplete last panel" << std::endl;
    return false;
  }
  return true;
}

bool NodeDeclaration::matches(const bNode &node) const
{
  const bNodeSocket *current_input = static_cast<bNodeSocket *>(node.inputs.first);
  const bNodeSocket *current_output = static_cast<bNodeSocket *>(node.outputs.first);
  const bNodePanelState *current_panel = node.panel_states_array;
  for (const ItemDeclarationPtr &item_decl : items) {
    if (const SocketDeclaration *socket_decl = dynamic_cast<const SocketDeclaration *>(
            item_decl.get()))
    {
      switch (socket_decl->in_out) {
        case SOCK_IN:
          if (current_input == nullptr || !socket_decl->matches(*current_input)) {
            return false;
          }
          current_input = current_input->next;
          break;
        case SOCK_OUT:
          if (current_output == nullptr || !socket_decl->matches(*current_output)) {
            return false;
          }
          current_output = current_output->next;
          break;
      }
    }
    else if (const PanelDeclaration *panel_decl = dynamic_cast<const PanelDeclaration *>(
                 item_decl.get()))
    {
      if (!node.panel_states().contains_ptr(current_panel) || !panel_decl->matches(*current_panel))
      {
        return false;
      }
      ++current_panel;
    }
    else {
      /* Unknown item type. */
      BLI_assert_unreachable();
    }
  }
  /* If items are left over, some were removed from the declaration. */
  if (current_input == nullptr || current_output == nullptr ||
      !node.panel_states().contains_ptr(current_panel))
  {
    return false;
  }
  return true;
}

bNodeSocket &SocketDeclaration::update_or_build(bNodeTree &ntree,
                                                bNode &node,
                                                bNodeSocket &socket) const
{
  /* By default just rebuild. */
  BLI_assert(socket.in_out == this->in_out);
  UNUSED_VARS_NDEBUG(socket);
  return this->build(ntree, node);
}

void SocketDeclaration::set_common_flags(bNodeSocket &socket) const
{
  SET_FLAG_FROM_TEST(socket.flag, compact, SOCK_COMPACT);
  SET_FLAG_FROM_TEST(socket.flag, hide_value, SOCK_HIDE_VALUE);
  SET_FLAG_FROM_TEST(socket.flag, hide_label, SOCK_HIDE_LABEL);
  SET_FLAG_FROM_TEST(socket.flag, is_multi_input, SOCK_MULTI_INPUT);
  SET_FLAG_FROM_TEST(socket.flag, no_mute_links, SOCK_NO_INTERNAL_LINK);
  SET_FLAG_FROM_TEST(socket.flag, is_unavailable, SOCK_UNAVAIL);
}

bool SocketDeclaration::matches_common_data(const bNodeSocket &socket) const
{
  if (socket.name != this->name) {
    return false;
  }
  if (socket.identifier != this->identifier) {
    return false;
  }
  if (((socket.flag & SOCK_COMPACT) != 0) != this->compact) {
    return false;
  }
  if (((socket.flag & SOCK_HIDE_VALUE) != 0) != this->hide_value) {
    return false;
  }
  if (((socket.flag & SOCK_HIDE_LABEL) != 0) != this->hide_label) {
    return false;
  }
  if (((socket.flag & SOCK_MULTI_INPUT) != 0) != this->is_multi_input) {
    return false;
  }
  if (((socket.flag & SOCK_NO_INTERNAL_LINK) != 0) != this->no_mute_links) {
    return false;
  }
  if (((socket.flag & SOCK_UNAVAIL) != 0) != this->is_unavailable) {
    return false;
  }
  return true;
}

PanelDeclarationBuilder &NodeDeclarationBuilder::add_panel(StringRef name, int identifier)
{
  std::unique_ptr<PanelDeclaration> panel_decl = std::make_unique<PanelDeclaration>();
  std::unique_ptr<PanelDeclarationBuilder> panel_decl_builder =
      std::make_unique<PanelDeclarationBuilder>();
  panel_decl_builder->decl_ = &*panel_decl;

  panel_decl_builder->node_decl_builder_ = this;
  if (identifier >= 0) {
    panel_decl->identifier = identifier;
  }
  else {
    /* Use index as identifier. */
    panel_decl->identifier = declaration_.items.size();
  }
  panel_decl->name = name;
  declaration_.items.append(std::move(panel_decl));

  PanelDeclarationBuilder &builder_ref = *panel_decl_builder;
  panel_builders_.append(std::move(panel_decl_builder));
  set_active_panel_builder(&builder_ref);

  return builder_ref;
}

void PanelDeclaration::build(bNodePanelState &panel) const
{
  panel = {0};
  panel.identifier = this->identifier;
  SET_FLAG_FROM_TEST(panel.flag, this->default_collapsed, NODE_PANEL_COLLAPSED);
}

bool PanelDeclaration::matches(const bNodePanelState &panel) const
{
  return panel.identifier == this->identifier;
}

void PanelDeclaration::update_or_build(const bNodePanelState &old_panel,
                                       bNodePanelState &new_panel) const
{
  build(new_panel);
  /* Copy existing state to the new panel */
  SET_FLAG_FROM_TEST(new_panel.flag, old_panel.is_collapsed(), NODE_PANEL_COLLAPSED);
}

namespace implicit_field_inputs {

void position(const bNode & /*node*/, void *r_value)
{
  new (r_value) fn::ValueOrField<float3>(bke::AttributeFieldInput::Create<float3>("position"));
}

void normal(const bNode & /*node*/, void *r_value)
{
  new (r_value)
      fn::ValueOrField<float3>(fn::Field<float3>(std::make_shared<bke::NormalFieldInput>()));
}

void index(const bNode & /*node*/, void *r_value)
{
  new (r_value) fn::ValueOrField<int>(fn::Field<int>(std::make_shared<fn::IndexFieldInput>()));
}

void id_or_index(const bNode & /*node*/, void *r_value)
{
  new (r_value)
      fn::ValueOrField<int>(fn::Field<int>(std::make_shared<bke::IDAttributeFieldInput>()));
}

}  // namespace implicit_field_inputs

}  // namespace blender::nodes

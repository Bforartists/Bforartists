/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#pragma once

#include <optional>

#include "BLI_compute_context.hh"
#include "BLI_string_ref.hh"
#include "BLI_vector_set.hh"

#include "ED_node_c.hh"

struct SpaceNode;
struct ARegion;
struct Main;
struct bContext;
struct bNodeSocket;
struct bNodeTree;
struct Object;
struct rcti;
struct NodesModifierData;
struct uiLayout;

namespace blender::ed::space_node {

/** Update the active node tree based on the context. */
void snode_set_context(const bContext &C);

VectorSet<bNode *> get_selected_nodes(bNodeTree &node_tree);

/**
 * \param is_new_node: If the node was just inserted, it is allowed to be inserted in a link, even
 * if it is linked already (after link-drag-search).
 */
void node_insert_on_link_flags_set(SpaceNode &snode,
                                   const ARegion &region,
                                   bool attach_enabled,
                                   bool is_new_node);

/**
 * Assumes link with #NODE_LINK_INSERT_TARGET set.
 */
void node_insert_on_link_flags(Main &bmain, SpaceNode &snode, bool is_new_node);
void node_insert_on_link_flags_clear(bNodeTree &node_tree);

/**
 * Draw a single node socket at default size.
 */
void node_socket_draw(bNodeSocket *sock, const rcti *rect, const float color[4], float scale);

/**
 * Find the nested node id of a currently visible node in the root tree.
 */
std::optional<int32_t> find_nested_node_id_in_root(const SpaceNode &snode, const bNode &node);

struct ObjectAndModifier {
  const Object *object;
  const NodesModifierData *nmd;
};
/**
 * Finds the context-modifier for the node editor.
 */
std::optional<ObjectAndModifier> get_modifier_for_node_editor(const SpaceNode &snode);
/**
 * Used to get the compute context for the (nested) node group that is currently edited.
 * Returns true on success.
 */
[[nodiscard]] bool push_compute_context_for_tree_path(
    const SpaceNode &snode, ComputeContextBuilder &compute_context_builder);

void ui_template_node_asset_menu_items(uiLayout &layout,
                                       const bContext &C,
                                       StringRef catalog_path);

}  // namespace blender::ed::space_node

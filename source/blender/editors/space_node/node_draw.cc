/* SPDX-FileCopyrightText: 2008 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup spnode
 * \brief higher level node drawing for the node editor.
 */

#include <iomanip>

#include "MEM_guardedalloc.h"

#include "DNA_light_types.h"
#include "DNA_linestyle_types.h"
#include "DNA_material_types.h"
#include "DNA_modifier_types.h"
#include "DNA_node_types.h"
#include "DNA_screen_types.h"
#include "DNA_space_types.h"
#include "DNA_text_types.h"
#include "DNA_texture_types.h"
#include "DNA_world_types.h"

#include "BLI_array.hh"
#include "BLI_bounds.hh"
#include "BLI_convexhull_2d.h"
#include "BLI_map.hh"
#include "BLI_set.hh"
#include "BLI_span.hh"
#include "BLI_string.h"
#include "BLI_string_ref.hh"
#include "BLI_vector.hh"

#include "BLT_translation.h"

#include "BKE_compute_contexts.hh"
#include "BKE_context.h"
#include "BKE_curves.hh"
#include "BKE_global.h"
#include "BKE_idtype.h"
#include "BKE_lib_id.h"
#include "BKE_main.h"
#include "BKE_node.hh"
#include "BKE_node_runtime.hh"
#include "BKE_node_tree_update.h"
#include "BKE_node_tree_zones.hh"
#include "BKE_object.hh"
#include "BKE_scene.h"
#include "BKE_type_conversions.hh"

#include "IMB_imbuf.h"

#include "DEG_depsgraph.hh"

#include "BLF_api.h"

#include "BIF_glutil.hh"

#include "GPU_framebuffer.h"
#include "GPU_immediate.h"
#include "GPU_immediate_util.h"
#include "GPU_matrix.h"
#include "GPU_shader_shared.h"
#include "GPU_state.h"
#include "GPU_viewport.h"

#include "WM_api.hh"
#include "WM_types.hh"

#include "ED_gpencil_legacy.hh"
#include "ED_node.hh"
#include "ED_node_preview.hh"
#include "ED_screen.hh"
#include "ED_space_api.hh"
#include "ED_viewer_path.hh"

#include "UI_interface.hh"
#include "UI_resources.hh"
#include "UI_view2d.hh"

#include "RNA_access.hh"
#include "RNA_prototypes.h"

#include "NOD_geometry_exec.hh"
#include "NOD_geometry_nodes_log.hh"
#include "NOD_node_declaration.hh"
#include "NOD_socket_declarations_geometry.hh"

#include "FN_field.hh"
#include "FN_field_cpp_type.hh"

#include "GEO_fillet_curves.hh"

#include "../interface/interface_intern.hh" /* TODO: Remove */

#include "node_intern.hh" /* own include */

#include <fmt/format.h>
#include <sstream>

namespace geo_log = blender::nodes::geo_eval_log;
using blender::bke::bNodeTreeZone;
using blender::bke::bNodeTreeZones;
using blender::ed::space_node::NestedTreePreviews;

/**
 * This is passed to many functions which draw the node editor.
 */
struct TreeDrawContext {
  /**
   * Whether a viewer node is active in geometry nodes can not be determined by a flag on the node
   * alone. That's because if the node group with the viewer is used multiple times, it's only
   * active in one of these cases.
   * The active node is cached here to avoid doing the more expensive check for every viewer node
   * in the tree.
   */
  const bNode *active_geometry_nodes_viewer = nullptr;
  /**
   * Geometry nodes logs various data during execution. The logged data that corresponds to the
   * currently drawn node tree can be retrieved from the log below.
   */
  blender::Map<const bNodeTreeZone *, geo_log::GeoTreeLog *> geo_log_by_zone;

  NestedTreePreviews *nested_group_infos = nullptr;
  /**
   * True if there is an active realtime compositor using the node tree, false otherwise.
   */
  bool used_by_realtime_compositor = false;
};

float ED_node_grid_size()
{
  return NODE_GRID_STEP_SIZE;
}

void ED_node_tree_update(const bContext *C)
{
  using namespace blender::ed::space_node;

  SpaceNode *snode = CTX_wm_space_node(C);
  if (snode) {
    snode_set_context(*C);

    if (snode->nodetree) {
      id_us_ensure_real(&snode->nodetree->id);
    }
  }
}

/* id is supposed to contain a node tree */
static bNodeTree *node_tree_from_ID(ID *id)
{
  if (id) {
    if (GS(id->name) == ID_NT) {
      return (bNodeTree *)id;
    }
    return ntreeFromID(id);
  }

  return nullptr;
}

void ED_node_tag_update_id(ID *id)
{
  bNodeTree *ntree = node_tree_from_ID(id);
  if (id == nullptr || ntree == nullptr) {
    return;
  }

  /* TODO(sergey): With the new dependency graph it should be just enough to only tag ntree itself.
   * All the users of this tree will have update flushed from the tree. */
  DEG_id_tag_update(&ntree->id, 0);

  if (ntree->type == NTREE_SHADER) {
    DEG_id_tag_update(id, 0);

    if (GS(id->name) == ID_MA) {
      WM_main_add_notifier(NC_MATERIAL | ND_SHADING, id);
    }
    else if (GS(id->name) == ID_LA) {
      WM_main_add_notifier(NC_LAMP | ND_LIGHTING, id);
    }
    else if (GS(id->name) == ID_WO) {
      WM_main_add_notifier(NC_WORLD | ND_WORLD, id);
    }
  }
  else if (ntree->type == NTREE_COMPOSIT) {
    WM_main_add_notifier(NC_SCENE | ND_NODES, id);
  }
  else if (ntree->type == NTREE_TEXTURE) {
    DEG_id_tag_update(id, 0);
    WM_main_add_notifier(NC_TEXTURE | ND_NODES, id);
  }
  else if (ntree->type == NTREE_GEOMETRY) {
    WM_main_add_notifier(NC_OBJECT | ND_MODIFIER, id);
  }
  else if (id == &ntree->id) {
    /* Node groups. */
    DEG_id_tag_update(id, 0);
  }
}

namespace blender::ed::space_node {

static const char *node_socket_get_translation_context(const bNodeSocket &socket)
{
  /* The node is not explicitly defined. */
  if (socket.runtime->declaration == nullptr) {
    return nullptr;
  }

  blender::StringRefNull translation_context = socket.runtime->declaration->translation_context;

  /* Default context. */
  if (translation_context.is_empty()) {
    return nullptr;
  }

  return translation_context.data();
}

static void node_socket_add_tooltip_in_node_editor(const bNodeTree &ntree,
                                                   const bNodeSocket &sock,
                                                   uiLayout &layout);

/** Return true when \a a should be behind \a b and false otherwise. */
static bool compare_node_depth(const bNode *a, const bNode *b)
{
  /* These tell if either the node or any of the parent nodes is selected.
   * A selected parent means an unselected node is also in foreground! */
  bool a_select = (a->flag & NODE_SELECT) != 0, b_select = (b->flag & NODE_SELECT) != 0;
  bool a_active = (a->flag & NODE_ACTIVE) != 0, b_active = (b->flag & NODE_ACTIVE) != 0;

  /* If one is an ancestor of the other. */
  /* XXX there might be a better sorting algorithm for stable topological sort,
   * this is O(n^2) worst case. */
  for (bNode *parent = a->parent; parent; parent = parent->parent) {
    /* If B is an ancestor, it is always behind A. */
    if (parent == b) {
      return false;
    }
    /* Any selected ancestor moves the node forward. */
    if (parent->flag & NODE_ACTIVE) {
      a_active = true;
    }
    if (parent->flag & NODE_SELECT) {
      a_select = true;
    }
  }
  for (bNode *parent = b->parent; parent; parent = parent->parent) {
    /* If A is an ancestor, it is always behind B. */
    if (parent == a) {
      return true;
    }
    /* Any selected ancestor moves the node forward. */
    if (parent->flag & NODE_ACTIVE) {
      b_active = true;
    }
    if (parent->flag & NODE_SELECT) {
      b_select = true;
    }
  }

  /* One of the nodes is in the background and the other not. */
  if ((a->flag & NODE_BACKGROUND) && !(b->flag & NODE_BACKGROUND)) {
    return true;
  }
  if ((b->flag & NODE_BACKGROUND) && !(a->flag & NODE_BACKGROUND)) {
    return false;
  }

  /* One has a higher selection state (active > selected > nothing). */
  if (a_active && !b_active) {
    return false;
  }
  if (b_active && !a_active) {
    return true;
  }
  if (!b_select && (a_active || a_select)) {
    return false;
  }
  if (!a_select && (b_active || b_select)) {
    return true;
  }

  return false;
}

void tree_draw_order_update(bNodeTree &ntree)
{
  Array<bNode *> sort_nodes = ntree.all_nodes();
  std::stable_sort(sort_nodes.begin(), sort_nodes.end(), compare_node_depth);
  for (const int i : sort_nodes.index_range()) {
    sort_nodes[i]->ui_order = i;
  }
}

Array<bNode *> tree_draw_order_calc_nodes(bNodeTree &ntree)
{
  Array<bNode *> nodes = ntree.all_nodes();
  if (nodes.is_empty()) {
    return {};
  }
  std::sort(nodes.begin(), nodes.end(), [](const bNode *a, const bNode *b) {
    return a->ui_order < b->ui_order;
  });
  return nodes;
}

Array<bNode *> tree_draw_order_calc_nodes_reversed(bNodeTree &ntree)
{
  Array<bNode *> nodes = ntree.all_nodes();
  if (nodes.is_empty()) {
    return {};
  }
  std::sort(nodes.begin(), nodes.end(), [](const bNode *a, const bNode *b) {
    return a->ui_order > b->ui_order;
  });
  return nodes;
}

static Array<uiBlock *> node_uiblocks_init(const bContext &C, const Span<bNode *> nodes)
{
  Array<uiBlock *> blocks(nodes.size());
  /* Add node uiBlocks in drawing order - prevents events going to overlapping nodes. */
  for (const int i : nodes.index_range()) {
    const std::string block_name = "node_" + std::string(nodes[i]->name);
    blocks[i] = UI_block_begin(&C, CTX_wm_region(&C), block_name.c_str(), UI_EMBOSS);
    /* This cancels events for background nodes. */
    UI_block_flag_enable(blocks[i], UI_BLOCK_CLIP_EVENTS);
  }

  return blocks;
}

float2 node_to_view(const bNode &node, const float2 &co)
{
  const float2 node_location = bke::nodeToView(&node, co);
  return node_location * UI_SCALE_FAC;
}

void node_to_updated_rect(const bNode &node, rctf &r_rect)
{
  const float2 xmin_ymax = node_to_view(node, {node.offsetx, node.offsety});
  r_rect.xmin = xmin_ymax.x;
  r_rect.ymax = xmin_ymax.y;
  const float2 xmax_ymin = node_to_view(node,
                                        {node.offsetx + node.width, node.offsety - node.height});
  r_rect.xmax = xmax_ymin.x;
  r_rect.ymin = xmax_ymin.y;
}

float2 node_from_view(const bNode &node, const float2 &co)
{
  const float2 node_location = co / UI_SCALE_FAC;
  return bke::nodeFromView(&node, node_location);
  ;
}

static bool is_node_panels_supported(const bNode &node)
{
  return node.declaration() && node.declaration()->use_custom_socket_order;
}

/* Draw UI for options, buttons, and previews. */
static bool node_update_basis_buttons(const bContext &C,
                                      bNodeTree &ntree,
                                      bNode &node,
                                      nodes::PanelDrawButtonsFunction draw_buttons,
                                      uiBlock &block,
                                      int &dy)
{
  /* Buttons rect? */
  const bool node_options = draw_buttons && (node.flag & NODE_OPTIONS);
  if (!node_options) {
    return false;
  }

  PointerRNA nodeptr = RNA_pointer_create(&ntree.id, &RNA_Node, &node);

  /* Get "global" coordinates. */
  float2 loc = node_to_view(node, float2(0));
  /* Round the node origin because text contents are always pixel-aligned. */
  loc.x = round(loc.x);
  loc.y = round(loc.y);

  dy -= NODE_DYS / 4;

  uiLayout *layout = UI_block_layout(&block,
                                     UI_LAYOUT_VERTICAL,
                                     UI_LAYOUT_PANEL,
                                     loc.x + NODE_DYS,
                                     dy,
                                     NODE_WIDTH(node) - NODE_DY,
                                     0,
                                     0,
                                     UI_style_get_dpi());

  if (node.flag & NODE_MUTED) {
    uiLayoutSetActive(layout, false);
  }

  uiLayoutSetContextPointer(layout, "node", &nodeptr);

  draw_buttons(layout, (bContext *)&C, &nodeptr);

  UI_block_align_end(&block);
  int buty;
  UI_block_layout_resolve(&block, nullptr, &buty);

  dy = buty - NODE_DYS / 4;
  return true;
}

const char *node_socket_get_label(const bNodeSocket *socket, const char *panel_label)
{
  /* Get the short label if possible. This is used when grouping sockets under panels,
   * to avoid redundancy in the label. */
  const char *socket_short_label = bke::nodeSocketShortLabel(socket);
  const char *socket_translation_context = node_socket_get_translation_context(*socket);

  if (socket_short_label) {
    return CTX_IFACE_(socket_translation_context, socket_short_label);
  }

  const char *socket_label = bke::nodeSocketLabel(socket);
  const char *translated_socket_label = CTX_IFACE_(socket_translation_context, socket_label);

  /* Shorten socket label if it begins with the panel label. */
  if (panel_label) {
    const int len_prefix = strlen(panel_label);
    if (STREQLEN(translated_socket_label, panel_label, len_prefix) &&
        translated_socket_label[len_prefix] == ' ')
    {
      return translated_socket_label + len_prefix + 1;
    }
  }

  /* Full label. */
  return translated_socket_label;
}

static bool node_update_basis_socket(const bContext &C,
                                     bNodeTree &ntree,
                                     bNode &node,
                                     const char *panel_label,
                                     bNodeSocket *input_socket,
                                     bNodeSocket *output_socket,
                                     uiBlock &block,
                                     const int &locx,
                                     int &locy)
{
  if ((!input_socket || !input_socket->is_visible()) &&
      (!output_socket || !output_socket->is_visible()))
  {
    return false;
  }

  const int topy = locy;

  /* Add the half the height of a multi-input socket to cursor Y
   * to account for the increased height of the taller sockets. */
  const bool is_multi_input = (input_socket ? input_socket->flag & SOCK_MULTI_INPUT : false);
  const float multi_input_socket_offset = is_multi_input ?
                                              std::max(input_socket->runtime->total_inputs - 2,
                                                       0) *
                                                  NODE_MULTI_INPUT_LINK_GAP :
                                              0.0f;
  locy -= multi_input_socket_offset * 0.5f;

  uiLayout *layout = UI_block_layout(&block,
                                     UI_LAYOUT_VERTICAL,
                                     UI_LAYOUT_PANEL,
                                     locx + NODE_DYS,
                                     locy,
                                     NODE_WIDTH(node) - NODE_DY,
                                     NODE_DY,
                                     0,
                                     UI_style_get_dpi());

  if (node.flag & NODE_MUTED) {
    uiLayoutSetActive(layout, false);
  }

  uiLayout *row = uiLayoutRow(layout, true);
  PointerRNA nodeptr = RNA_pointer_create(&ntree.id, &RNA_Node, &node);
  uiLayoutSetContextPointer(row, "node", &nodeptr);

  if (input_socket) {
    /* Context pointers for current node and socket. */
    PointerRNA sockptr = RNA_pointer_create(&ntree.id, &RNA_NodeSocket, input_socket);
    uiLayoutSetContextPointer(row, "socket", &sockptr);

    uiLayoutSetAlignment(row, UI_LAYOUT_ALIGN_EXPAND);

    input_socket->typeinfo->draw(
        (bContext *)&C, row, &sockptr, &nodeptr, node_socket_get_label(input_socket, panel_label));
  }
  else {
    /* Context pointers for current node and socket. */
    PointerRNA sockptr = RNA_pointer_create(&ntree.id, &RNA_NodeSocket, output_socket);
    uiLayoutSetContextPointer(row, "socket", &sockptr);

    /* Align output buttons to the right. */
    uiLayoutSetAlignment(row, UI_LAYOUT_ALIGN_RIGHT);

    output_socket->typeinfo->draw((bContext *)&C,
                                  row,
                                  &sockptr,
                                  &nodeptr,
                                  node_socket_get_label(output_socket, panel_label));
  }

  if (input_socket) {
    node_socket_add_tooltip_in_node_editor(ntree, *input_socket, *row);
    /* Round the socket location to stop it from jiggling. */
    input_socket->runtime->location = float2(round(locx), round(locy - NODE_DYS));
  }
  if (output_socket) {
    node_socket_add_tooltip_in_node_editor(ntree, *output_socket, *row);
    /* Round the socket location to stop it from jiggling. */
    output_socket->runtime->location = float2(round(locx + NODE_WIDTH(node)),
                                              round(locy - NODE_DYS));
  }

  UI_block_align_end(&block);

  int buty;
  UI_block_layout_resolve(&block, nullptr, &buty);
  /* Ensure minimum socket height in case layout is empty. */
  buty = min_ii(buty, topy - NODE_DY);
  locy = buty - multi_input_socket_offset * 0.5;
  return true;
}

struct NodeInterfaceItemData {
  /* Declaration of a socket (only for socket items). */
  const nodes::SocketDeclaration *socket_decl = nullptr;
  bNodeSocket *input = nullptr;
  bNodeSocket *output = nullptr;

  /* Declaration of a panel (only for panel items). */
  const nodes::PanelDeclaration *panel_decl = nullptr;
  /* State of the panel instance on the node.
   * Mutable so that panel visibility can be updated. */
  bNodePanelState *state = nullptr;
  /* Runtime panel state for draw locations. */
  bke::bNodePanelRuntime *runtime = nullptr;

  NodeInterfaceItemData(const nodes::SocketDeclaration *_socket_decl,
                        bNodeSocket *_input,
                        bNodeSocket *_output)
      : socket_decl(_socket_decl), input(_input), output(_output)
  {
  }
  NodeInterfaceItemData(const nodes::PanelDeclaration *_panel_decl,
                        bNodePanelState *_state,
                        bke::bNodePanelRuntime *_runtime)
      : panel_decl(_panel_decl), state(_state), runtime(_runtime)
  {
  }

  bool is_valid_socket() const
  {
    /* At least one socket pointer must be valid. */
    return this->socket_decl && (input || output);
  }

  bool is_valid_panel() const
  {
    /* Panel can only be drawn when state data is available. */
    return this->panel_decl && this->state && this->runtime;
  }
};

/* Compile relevant socket and panel pointer data into a vector.
 * This helps ensure correct pointer access in complex situations like inlined sockets.
 */
static Vector<NodeInterfaceItemData> node_build_item_data(bNode &node)
{
  namespace nodes = blender::nodes;
  using ItemDeclIterator = blender::Span<nodes::ItemDeclarationPtr>::iterator;
  using SocketIterator = blender::Span<bNodeSocket *>::iterator;
  using PanelStateIterator = blender::MutableSpan<bNodePanelState>::iterator;
  using PanelRuntimeIterator = blender::MutableSpan<bke::bNodePanelRuntime>::iterator;

  BLI_assert(is_node_panels_supported(node));
  BLI_assert(node.runtime->panels.size() == node.num_panel_states);

  ItemDeclIterator item_decl = node.declaration()->items.begin();
  SocketIterator input = node.input_sockets().begin();
  SocketIterator output = node.output_sockets().begin();
  PanelStateIterator panel_state = node.panel_states().begin();
  PanelRuntimeIterator panel_runtime = node.runtime->panels.begin();
  const ItemDeclIterator item_decl_end = node.declaration()->items.end();
  const SocketIterator input_end = node.input_sockets().end();
  const SocketIterator output_end = node.output_sockets().end();
  const PanelStateIterator panel_state_end = node.panel_states().end();
  const PanelRuntimeIterator panel_runtime_end = node.runtime->panels.end();
  UNUSED_VARS_NDEBUG(input_end, output_end, panel_state_end, panel_runtime_end);

  Vector<NodeInterfaceItemData> result;
  result.reserve(node.declaration()->items.size());

  while (item_decl != item_decl_end) {
    if (const nodes::SocketDeclaration *socket_decl =
            dynamic_cast<const nodes::SocketDeclaration *>(item_decl->get()))
    {
      switch (socket_decl->in_out) {
        case SOCK_IN:
          BLI_assert(input != input_end);
          result.append({socket_decl, *input, nullptr});
          ++input;
          break;
        case SOCK_OUT:
          BLI_assert(output != output_end);
          result.append({socket_decl, nullptr, *output});
          ++output;
          break;
      }
      ++item_decl;
    }
    else if (const nodes::PanelDeclaration *panel_decl =
                 dynamic_cast<const nodes::PanelDeclaration *>(item_decl->get()))
    {
      BLI_assert(panel_state != panel_state_end);
      BLI_assert(panel_runtime != panel_runtime_end);
      result.append({panel_decl, panel_state, panel_runtime});
      ++item_decl;
      ++panel_state;
      ++panel_runtime;
    }
  }
  return result;
}

using ItemIterator = Vector<NodeInterfaceItemData>::const_iterator;

struct VisibilityUpdateState {
  ItemIterator item_iter;
  const ItemIterator item_end;

  explicit VisibilityUpdateState(const Span<NodeInterfaceItemData> items)
      : item_iter(items.begin()), item_end(items.end())
  {
  }
};

/* Recursive function to determine visibility of items before drawing. */
static void node_update_panel_items_visibility_recursive(int num_items,
                                                         const bool is_parent_collapsed,
                                                         bNodePanelState &parent_state,
                                                         VisibilityUpdateState &state)
{
  parent_state.flag &= ~NODE_PANEL_CONTENT_VISIBLE;
  while (state.item_iter != state.item_end) {
    /* Stop after adding the expected number of items.
     * Root panel consumes all remaining items (num_items == -1). */
    if (num_items == 0) {
      break;
    }
    else if (num_items > 0) {
      --num_items;
    }
    /* Consume item. */
    const NodeInterfaceItemData &item = *state.item_iter++;

    if (item.is_valid_panel()) {
      SET_FLAG_FROM_TEST(item.state->flag, is_parent_collapsed, NODE_PANEL_PARENT_COLLAPSED);
      /* New top panel is collapsed if self or parent is collapsed. */
      const bool is_collapsed = is_parent_collapsed || item.state->is_collapsed();

      node_update_panel_items_visibility_recursive(
          item.panel_decl->num_child_decls, is_collapsed, *item.state, state);
      if (item.state->flag & NODE_PANEL_CONTENT_VISIBLE) {
        /* If child panel is visible so is the parent panel. */
        parent_state.flag |= NODE_PANEL_CONTENT_VISIBLE;
      }
    }
    else if (item.is_valid_socket()) {
      if (item.input) {
        SET_FLAG_FROM_TEST(item.input->flag, is_parent_collapsed, SOCK_PANEL_COLLAPSED);
        if (item.input->is_visible()) {
          parent_state.flag |= NODE_PANEL_CONTENT_VISIBLE;
        }
      }
      if (item.output) {
        SET_FLAG_FROM_TEST(item.output->flag, is_parent_collapsed, SOCK_PANEL_COLLAPSED);
        if (item.output->is_visible()) {
          parent_state.flag |= NODE_PANEL_CONTENT_VISIBLE;
        }
      }
    }
    else {
      /* Should not happen. */
      BLI_assert_unreachable();
    }
  }
}

struct LocationUpdateState {
  ItemIterator item_iter;
  const ItemIterator item_end;

  /* Checked at various places to avoid adding duplicate spacers without anything in between. */
  bool need_spacer_after_item = false;
  /* Makes sure buttons are only drawn once. */
  bool buttons_drawn = false;
  /* Only true for the first item in the layout. */
  bool is_first = true;

  explicit LocationUpdateState(const Span<NodeInterfaceItemData> items)
      : item_iter(items.begin()), item_end(items.end())
  {
  }
};

/* Recursive function that adds the expected number of items in a panel and advances the
 * iterator. */
static void add_panel_items_recursive(const bContext &C,
                                      bNodeTree &ntree,
                                      bNode &node,
                                      uiBlock &block,
                                      const int locx,
                                      int &locy,
                                      int num_items,
                                      const bool is_parent_collapsed,
                                      const char *parent_label,
                                      bke::bNodePanelRuntime *parent_runtime,
                                      LocationUpdateState &state)
{
  while (state.item_iter != state.item_end) {
    /* Stop after adding the expected number of items.
     * Root panel consumes all remaining items (num_items == -1). */
    if (num_items == 0) {
      break;
    }
    else if (num_items > 0) {
      --num_items;
    }
    /* Consume item. */
    const NodeInterfaceItemData &item = *state.item_iter++;

    if (item.is_valid_panel()) {
      /* Draw buttons before the first panel. */
      if (!state.buttons_drawn) {
        state.buttons_drawn = true;
        state.need_spacer_after_item = node_update_basis_buttons(
            C, ntree, node, node.typeinfo->draw_buttons, block, locy);
      }

      /* Panel visible if any content is visible. */
      if (item.state->has_visible_content()) {
        if (!is_parent_collapsed) {
          locy -= NODE_DY;
          state.is_first = false;
        }

        /* New top panel is collapsed if self or parent is collapsed. */
        const bool is_collapsed = is_parent_collapsed || item.state->is_collapsed();

        /* Round the socket location to stop it from jiggling. */
        item.runtime->location_y = round(locy + NODE_DYS);
        if (is_collapsed) {
          item.runtime->max_content_y = item.runtime->min_content_y = round(locy);
        }
        else {
          locy -= NODE_ITEM_SPACING_Y / 2; /* Space at bottom of panel header. */
          item.runtime->max_content_y = item.runtime->min_content_y = round(locy);
          locy -= NODE_ITEM_SPACING_Y; /* Space at top of panel contents. */

          node_update_basis_buttons(C, ntree, node, item.panel_decl->draw_buttons, block, locy);
        }

        add_panel_items_recursive(C,
                                  ntree,
                                  node,
                                  block,
                                  locx,
                                  locy,
                                  item.panel_decl->num_child_decls,
                                  is_collapsed,
                                  item.panel_decl->name.c_str(),
                                  item.runtime,
                                  state);
      }
    }
    else if (item.is_valid_socket()) {
      if (item.input) {
        /* Draw buttons before the first input. */
        if (!state.buttons_drawn) {
          state.buttons_drawn = true;
          state.need_spacer_after_item = node_update_basis_buttons(
              C, ntree, node, node.typeinfo->draw_buttons, block, locy);
        }

        if (is_parent_collapsed) {
          item.input->runtime->location = float2(locx, round(locy + NODE_DYS));
        }
        else {
          /* Space between items. */
          if (!state.is_first && item.input->is_visible()) {
            locy -= NODE_ITEM_SPACING_Y;
          }
        }
      }
      if (item.output) {
        if (is_parent_collapsed) {
          item.output->runtime->location = float2(round(locx + NODE_WIDTH(node)),
                                                  round(locy + NODE_DYS));
        }
        else {
          /* Space between items. */
          if (!state.is_first && item.output->is_visible()) {
            locy -= NODE_ITEM_SPACING_Y;
          }
        }
      }

      if (!is_parent_collapsed &&
          node_update_basis_socket(
              C, ntree, node, parent_label, item.input, item.output, block, locx, locy))
      {
        state.is_first = false;
        state.need_spacer_after_item = true;
      }
    }
    else {
      /* Should not happen. */
      BLI_assert_unreachable();
    }
  }

  /* Finalize the vertical extent of the content. */
  if (!is_parent_collapsed) {
    if (parent_runtime) {
      locy -= 2 * NODE_ITEM_SPACING_Y; /* Space at bottom of panel contents. */
      parent_runtime->min_content_y = round(locy);
    }
    locy -= NODE_ITEM_SPACING_Y / 2; /* Space at top of next panel header. */
  }
}

/* Advanced drawing with panels and arbitrary input/output ordering. */
static void node_update_basis_from_declaration(
    const bContext &C, bNodeTree &ntree, bNode &node, uiBlock &block, const int locx, int &locy)
{
  namespace nodes = blender::nodes;

  BLI_assert(is_node_panels_supported(node));
  BLI_assert(node.runtime->panels.size() == node.num_panel_states);

  const Vector<NodeInterfaceItemData> item_data = node_build_item_data(node);

  /* Update item visibility flags first. */
  VisibilityUpdateState visibility_state(item_data);
  /* Dummy state item to write into, unused. */
  bNodePanelState root_panel_state;
  node_update_panel_items_visibility_recursive(-1, false, root_panel_state, visibility_state);

  /* Space at the top. */
  locy -= NODE_DYS / 2;

  /* Start by adding root panel items. */
  LocationUpdateState location_state(item_data);
  add_panel_items_recursive(
      C, ntree, node, block, locx, locy, -1, false, "", nullptr, location_state);

  /* Draw buttons at the bottom if no inputs exist. */
  if (!location_state.buttons_drawn) {
    location_state.need_spacer_after_item = node_update_basis_buttons(
        C, ntree, node, node.typeinfo->draw_buttons, block, locy);
  }

  if (location_state.need_spacer_after_item) {
    locy -= NODE_DYS / 2;
  }
}

/* Conventional drawing in outputs/buttons/inputs order. */
static void node_update_basis_from_socket_lists(
    const bContext &C, bNodeTree &ntree, bNode &node, uiBlock &block, const int locx, int &locy)
{
  const bool node_options = node.typeinfo->draw_buttons && (node.flag & NODE_OPTIONS);
  const bool inputs_first = node.inputs.first && !(node.outputs.first || node_options);

  /* Add a little bit of padding above the top socket. */
  if (node.outputs.first || inputs_first) {
    locy -= NODE_DYS / 2;
  }

  /* Output sockets. */
  bool add_output_space = false;

  for (bNodeSocket *socket : node.output_sockets()) {
    /* Clear flag, conventional drawing does not support panels. */
    socket->flag &= ~SOCK_PANEL_COLLAPSED;

    if (node_update_basis_socket(C, ntree, node, nullptr, nullptr, socket, block, locx, locy)) {
      if (socket->next) {
        locy -= NODE_ITEM_SPACING_Y;
      }
      add_output_space = true;
    }
  }

  if (add_output_space) {
    locy -= NODE_DY / 4;
  }

  node_update_basis_buttons(C, ntree, node, node.typeinfo->draw_buttons, block, locy);

  /* Input sockets. */
  for (bNodeSocket *socket : node.input_sockets()) {
    /* Clear flag, conventional drawing does not support panels. */
    socket->flag &= ~SOCK_PANEL_COLLAPSED;

    if (node_update_basis_socket(C, ntree, node, nullptr, socket, nullptr, block, locx, locy)) {
      if (socket->next) {
        locy -= NODE_ITEM_SPACING_Y;
      }
    }
  }

  /* Little bit of space in end. */
  if (node.inputs.first || (node.flag & NODE_OPTIONS) == 0) {
    locy -= NODE_DYS / 2;
  }
}

/**
 * Based on settings and sockets in node, set drawing rect info.
 */
static void node_update_basis(const bContext &C,
                              const TreeDrawContext & /*tree_draw_ctx*/,
                              bNodeTree &ntree,
                              bNode &node,
                              uiBlock &block)
{
  /* Get "global" coordinates. */
  float2 loc = node_to_view(node, float2(0));
  /* Round the node origin because text contents are always pixel-aligned. */
  loc.x = round(loc.x);
  loc.y = round(loc.y);

  int dy = loc.y;

  /* Header. */
  dy -= NODE_DY;

  if (is_node_panels_supported(node)) {
    node_update_basis_from_declaration(C, ntree, node, block, loc.x, dy);
  }
  else {
    node_update_basis_from_socket_lists(C, ntree, node, block, loc.x, dy);
  }

  node.runtime->totr.xmin = loc.x;
  node.runtime->totr.xmax = loc.x + NODE_WIDTH(node);
  node.runtime->totr.ymax = loc.y;
  node.runtime->totr.ymin = min_ff(dy, loc.y - 2 * NODE_DY);

  /* Set the block bounds to clip mouse events from underlying nodes.
   * Add a margin for sockets on each side. */
  UI_block_bounds_set_explicit(&block,
                               node.runtime->totr.xmin - NODE_SOCKSIZE,
                               node.runtime->totr.ymin,
                               node.runtime->totr.xmax + NODE_SOCKSIZE,
                               node.runtime->totr.ymax);
}

/**
 * Based on settings in node, sets drawing rect info.
 */
static void node_update_hidden(bNode &node, uiBlock &block)
{
  int totin = 0, totout = 0;

  /* Get "global" coordinates. */
  float2 loc = node_to_view(node, float2(0));
  /* Round the node origin because text contents are always pixel-aligned. */
  loc.x = round(loc.x);
  loc.y = round(loc.y);

  /* Calculate minimal radius. */
  for (const bNodeSocket *socket : node.input_sockets()) {
    if (socket->is_visible()) {
      totin++;
    }
  }
  for (const bNodeSocket *socket : node.output_sockets()) {
    if (socket->is_visible()) {
      totout++;
    }
  }

  float hiddenrad = HIDDEN_RAD;
  float tot = MAX2(totin, totout);
  if (tot > 4) {
    hiddenrad += 5.0f * float(tot - 4);
  }

  node.runtime->totr.xmin = loc.x;
  node.runtime->totr.xmax = loc.x + max_ff(NODE_WIDTH(node), 2 * hiddenrad);
  node.runtime->totr.ymax = loc.y + (hiddenrad - 0.5f * NODE_DY);
  node.runtime->totr.ymin = node.runtime->totr.ymax - 2 * hiddenrad;

  /* Output sockets. */
  float rad = float(M_PI) / (1.0f + float(totout));
  float drad = rad;

  for (bNodeSocket *socket : node.output_sockets()) {
    if (socket->is_visible()) {
      /* Round the socket location to stop it from jiggling. */
      socket->runtime->location = {
          round(node.runtime->totr.xmax - hiddenrad + sinf(rad) * hiddenrad),
          round(node.runtime->totr.ymin + hiddenrad + cosf(rad) * hiddenrad)};
      rad += drad;
    }
  }

  /* Input sockets. */
  rad = drad = -float(M_PI) / (1.0f + float(totin));

  for (bNodeSocket *socket : node.input_sockets()) {
    if (socket->is_visible()) {
      /* Round the socket location to stop it from jiggling. */
      socket->runtime->location = {
          round(node.runtime->totr.xmin + hiddenrad + sinf(rad) * hiddenrad),
          round(node.runtime->totr.ymin + hiddenrad + cosf(rad) * hiddenrad)};
      rad += drad;
    }
  }

  /* Set the block bounds to clip mouse events from underlying nodes.
   * Add a margin for sockets on each side. */
  UI_block_bounds_set_explicit(&block,
                               node.runtime->totr.xmin - NODE_SOCKSIZE,
                               node.runtime->totr.ymin,
                               node.runtime->totr.xmax + NODE_SOCKSIZE,
                               node.runtime->totr.ymax);
}

static int node_get_colorid(TreeDrawContext &tree_draw_ctx, const bNode &node)
{
  const int nclass = (node.typeinfo->ui_class == nullptr) ? node.typeinfo->nclass :
                                                            node.typeinfo->ui_class(&node);
  switch (nclass) {
    case NODE_CLASS_INPUT:
      return TH_NODE_INPUT;
    case NODE_CLASS_OUTPUT: {
      if (node.type == GEO_NODE_VIEWER) {
        return &node == tree_draw_ctx.active_geometry_nodes_viewer ? TH_NODE_OUTPUT : TH_NODE;
      }
      return (node.flag & NODE_DO_OUTPUT) ? TH_NODE_OUTPUT : TH_NODE;
    }
    case NODE_CLASS_CONVERTER:
      return TH_NODE_CONVERTER;
    case NODE_CLASS_OP_COLOR:
      return TH_NODE_COLOR;
    case NODE_CLASS_OP_VECTOR:
      return TH_NODE_VECTOR;
    case NODE_CLASS_OP_FILTER:
      return TH_NODE_FILTER;
    case NODE_CLASS_GROUP:
      return TH_NODE_GROUP;
    case NODE_CLASS_INTERFACE:
      return TH_NODE_INTERFACE;
    case NODE_CLASS_MATTE:
      return TH_NODE_MATTE;
    case NODE_CLASS_DISTORT:
      return TH_NODE_DISTORT;
    case NODE_CLASS_TEXTURE:
      return TH_NODE_TEXTURE;
    case NODE_CLASS_SHADER:
      return TH_NODE_SHADER;
    case NODE_CLASS_SCRIPT:
      return TH_NODE_SCRIPT;
    case NODE_CLASS_PATTERN:
      return TH_NODE_PATTERN;
    case NODE_CLASS_LAYOUT:
      return TH_NODE_LAYOUT;
    case NODE_CLASS_GEOMETRY:
      return TH_NODE_GEOMETRY;
    case NODE_CLASS_ATTRIBUTE:
      return TH_NODE_ATTRIBUTE;
    default:
      return TH_NODE;
  }
}

static void node_draw_mute_line(const bContext &C,
                                const View2D &v2d,
                                const SpaceNode &snode,
                                const bNode &node)
{
  GPU_blend(GPU_BLEND_ALPHA);

  for (const bNodeLink &link : node.internal_links()) {
    if (!nodeLinkIsHidden(&link)) {
      node_draw_link_bezier(C, v2d, snode, link, TH_WIRE_INNER, TH_WIRE_INNER, TH_WIRE, false);
    }
  }

  GPU_blend(GPU_BLEND_NONE);
}

static void node_socket_draw(const bNodeSocket &sock,
                             const float color[4],
                             const float color_outline[4],
                             const float size,
                             const float locx,
                             const float locy,
                             uint pos_id,
                             uint col_id,
                             uint shape_id,
                             uint size_id,
                             uint outline_col_id)
{
  int flags;

  /* Set shape flags. */
  switch (sock.display_shape) {
    case SOCK_DISPLAY_SHAPE_DIAMOND:
    case SOCK_DISPLAY_SHAPE_DIAMOND_DOT:
      flags = GPU_KEYFRAME_SHAPE_DIAMOND;
      break;
    case SOCK_DISPLAY_SHAPE_SQUARE:
    case SOCK_DISPLAY_SHAPE_SQUARE_DOT:
      flags = GPU_KEYFRAME_SHAPE_SQUARE;
      break;
    default:
    case SOCK_DISPLAY_SHAPE_CIRCLE:
    case SOCK_DISPLAY_SHAPE_CIRCLE_DOT:
      flags = GPU_KEYFRAME_SHAPE_CIRCLE;
      break;
  }

  if (ELEM(sock.display_shape,
           SOCK_DISPLAY_SHAPE_DIAMOND_DOT,
           SOCK_DISPLAY_SHAPE_SQUARE_DOT,
           SOCK_DISPLAY_SHAPE_CIRCLE_DOT))
  {
    flags |= GPU_KEYFRAME_SHAPE_INNER_DOT;
  }

  immAttr4fv(col_id, color);
  immAttr1u(shape_id, flags);
  immAttr1f(size_id, size);
  immAttr4fv(outline_col_id, color_outline);
  immVertex2f(pos_id, locx, locy);
}

static void node_socket_draw_multi_input(const float color[4],
                                         const float color_outline[4],
                                         const float width,
                                         const float height,
                                         const float2 location)
{
  /* The other sockets are drawn with the keyframe shader. There, the outline has a base
   * thickness that can be varied but always scales with the size the socket is drawn at. Using
   * `UI_SCALE_FAC` has the same effect here. It scales the outline correctly across different
   * screen DPI's and UI scales without being affected by the 'line-width'. */
  const float outline_width = NODE_SOCK_OUTLINE_SCALE * UI_SCALE_FAC;

  /* UI_draw_roundbox draws the outline on the outer side, so compensate for the outline width.
   */
  const rctf rect = {
      location.x - width + outline_width * 0.5f,
      location.x + width - outline_width * 0.5f,
      location.y - height + outline_width * 0.5f,
      location.y + height - outline_width * 0.5f,
  };

  UI_draw_roundbox_corner_set(UI_CNR_ALL);
  UI_draw_roundbox_4fv_ex(
      &rect, color, nullptr, 1.0f, color_outline, outline_width, width - outline_width * 0.5f);
}

static const float virtual_node_socket_outline_color[4] = {0.5, 0.5, 0.5, 1.0};

static void node_socket_outline_color_get(const bool selected,
                                          const int socket_type,
                                          float r_outline_color[4])
{
  if (selected) {
    UI_GetThemeColor4fv(TH_ACTIVE, r_outline_color);
  }
  else if (socket_type == SOCK_CUSTOM) {
    /* Until there is a better place for per socket color,
     * the outline color for virtual sockets is set here. */
    copy_v4_v4(r_outline_color, virtual_node_socket_outline_color);
  }
  else {
    UI_GetThemeColor4fv(TH_WIRE, r_outline_color);
    r_outline_color[3] = 1.0f;
  }
}

void node_socket_color_get(const bContext &C,
                           const bNodeTree &ntree,
                           PointerRNA &node_ptr,
                           const bNodeSocket &sock,
                           float r_color[4])
{
  if (!sock.typeinfo->draw_color) {
    copy_v4_v4(r_color, float4(1.0f, 0.0f, 1.0f, 1.0f));
    return;
  }

  BLI_assert(RNA_struct_is_a(node_ptr.type, &RNA_Node));
  PointerRNA ptr = RNA_pointer_create(
      &const_cast<ID &>(ntree.id), &RNA_NodeSocket, &const_cast<bNodeSocket &>(sock));
  sock.typeinfo->draw_color((bContext *)&C, &ptr, &node_ptr, r_color);
}

static void create_inspection_string_for_generic_value(const bNodeSocket &socket,
                                                       const GPointer value,
                                                       std::stringstream &ss)
{
  auto id_to_inspection_string = [&](const ID *id, const short idcode) {
    ss << (id ? id->name + 2 : TIP_("None")) << " (" << TIP_(BKE_idtype_idcode_to_name(idcode))
       << ")";
  };

  const CPPType &value_type = *value.type();
  const void *buffer = value.get();
  if (value_type.is<Object *>()) {
    id_to_inspection_string(*static_cast<const ID *const *>(buffer), ID_OB);
    return;
  }
  if (value_type.is<Material *>()) {
    id_to_inspection_string(*static_cast<const ID *const *>(buffer), ID_MA);
    return;
  }
  if (value_type.is<Tex *>()) {
    id_to_inspection_string(*static_cast<const ID *const *>(buffer), ID_TE);
    return;
  }
  if (value_type.is<Image *>()) {
    id_to_inspection_string(*static_cast<const ID *const *>(buffer), ID_IM);
    return;
  }
  if (value_type.is<Collection *>()) {
    id_to_inspection_string(*static_cast<const ID *const *>(buffer), ID_GR);
    return;
  }
  if (value_type.is<std::string>()) {
    ss << fmt::format(TIP_("{} (String)"), *static_cast<const std::string *>(buffer));
    return;
  }

  const CPPType &socket_type = *socket.typeinfo->base_cpp_type;
  const bke::DataTypeConversions &convert = bke::get_implicit_type_conversions();
  if (value_type != socket_type) {
    if (!convert.is_convertible(value_type, socket_type)) {
      return;
    }
  }
  BUFFER_FOR_CPP_TYPE_VALUE(socket_type, socket_value);
  /* This will just copy the value if the types are equal. */
  convert.convert_to_uninitialized(value_type, socket_type, buffer, socket_value);
  BLI_SCOPED_DEFER([&]() { socket_type.destruct(socket_value); });

  if (socket_type.is<int>()) {
    ss << fmt::format(TIP_("{} (Integer)"), *static_cast<int *>(socket_value));
  }
  else if (socket_type.is<float>()) {
    ss << fmt::format(TIP_("{} (Float)"), *static_cast<float *>(socket_value));
  }
  else if (socket_type.is<blender::float3>()) {
    const blender::float3 &vector = *static_cast<blender::float3 *>(socket_value);
    ss << fmt::format(TIP_("({}, {}, {}) (Vector)"), vector.x, vector.y, vector.z);
  }
  else if (socket_type.is<blender::ColorGeometry4f>()) {
    const blender::ColorGeometry4f &color = *static_cast<blender::ColorGeometry4f *>(socket_value);
    ss << fmt::format(TIP_("({}, {}, {}, {}) (Color)"), color.r, color.g, color.b, color.a);
  }
  else if (socket_type.is<math::Quaternion>()) {
    const math::Quaternion &rotation = *static_cast<math::Quaternion *>(socket_value);
    const math::EulerXYZ euler = math::to_euler(rotation);
    ss << fmt::format(TIP_("({}" BLI_STR_UTF8_DEGREE_SIGN ", {}" BLI_STR_UTF8_DEGREE_SIGN
                           ", {}" BLI_STR_UTF8_DEGREE_SIGN ") (Rotation)"),
                      euler.x().degree(),
                      euler.y().degree(),
                      euler.z().degree());
  }
  else if (socket_type.is<bool>()) {
    ss << fmt::format(TIP_("{} (Boolean)"),
                      ((*static_cast<bool *>(socket_value)) ? TIP_("True") : TIP_("False")));
  }
}

static void create_inspection_string_for_field_info(const bNodeSocket &socket,
                                                    const geo_log::FieldInfoLog &value_log,
                                                    std::stringstream &ss)
{
  const CPPType &socket_type = *socket.typeinfo->base_cpp_type;
  const Span<std::string> input_tooltips = value_log.input_tooltips;

  if (input_tooltips.is_empty()) {
    /* Should have been logged as constant value. */
    BLI_assert_unreachable();
    ss << TIP_("Value has not been logged");
  }
  else {
    if (socket_type.is<int>()) {
      ss << TIP_("Integer field based on:");
    }
    else if (socket_type.is<float>()) {
      ss << TIP_("Float field based on:");
    }
    else if (socket_type.is<blender::float3>()) {
      ss << TIP_("Vector field based on:");
    }
    else if (socket_type.is<bool>()) {
      ss << TIP_("Boolean field based on:");
    }
    else if (socket_type.is<std::string>()) {
      ss << TIP_("String field based on:");
    }
    else if (socket_type.is<blender::ColorGeometry4f>()) {
      ss << TIP_("Color field based on:");
    }
    else if (socket_type.is<math::Quaternion>()) {
      ss << TIP_("Rotation field based on:");
    }
    ss << "\n";

    for (const int i : input_tooltips.index_range()) {
      const blender::StringRef tooltip = input_tooltips[i];
      ss << fmt::format(TIP_("\u2022 {}"), TIP_(tooltip.data()));
      if (i < input_tooltips.size() - 1) {
        ss << ".\n";
      }
    }
  }
}

static void create_inspection_string_for_geometry_info(const geo_log::GeometryInfoLog &value_log,
                                                       std::stringstream &ss)
{
  Span<bke::GeometryComponent::Type> component_types = value_log.component_types;
  if (component_types.is_empty()) {
    ss << TIP_("Empty Geometry");
    return;
  }

  auto to_string = [](int value) {
    char str[BLI_STR_FORMAT_INT32_GROUPED_SIZE];
    BLI_str_format_int_grouped(str, value);
    return std::string(str);
  };

  ss << TIP_("Geometry:") << "\n";
  for (bke::GeometryComponent::Type type : component_types) {
    switch (type) {
      case bke::GeometryComponent::Type::Mesh: {
        const geo_log::GeometryInfoLog::MeshInfo &mesh_info = *value_log.mesh_info;
        char line[256];
        SNPRINTF(line,
                 TIP_("\u2022 Mesh: %s vertices, %s edges, %s faces"),
                 to_string(mesh_info.verts_num).c_str(),
                 to_string(mesh_info.edges_num).c_str(),
                 to_string(mesh_info.faces_num).c_str());
        ss << line;
        break;
      }
      case bke::GeometryComponent::Type::PointCloud: {
        const geo_log::GeometryInfoLog::PointCloudInfo &pointcloud_info =
            *value_log.pointcloud_info;
        char line[256];
        SNPRINTF(line,
                 TIP_("\u2022 Point Cloud: %s points"),
                 to_string(pointcloud_info.points_num).c_str());
        ss << line;
        break;
      }
      case bke::GeometryComponent::Type::Curve: {
        const geo_log::GeometryInfoLog::CurveInfo &curve_info = *value_log.curve_info;
        char line[256];
        SNPRINTF(line,
                 TIP_("\u2022 Curve: %s points, %s splines"),
                 to_string(curve_info.points_num).c_str(),
                 to_string(curve_info.splines_num).c_str());
        ss << line;
        break;
      }
      case bke::GeometryComponent::Type::Instance: {
        const geo_log::GeometryInfoLog::InstancesInfo &instances_info = *value_log.instances_info;
        char line[256];
        SNPRINTF(
            line, TIP_("\u2022 Instances: %s"), to_string(instances_info.instances_num).c_str());
        ss << line;
        break;
      }
      case bke::GeometryComponent::Type::Volume: {
        ss << TIP_("\u2022 Volume");
        break;
      }
      case bke::GeometryComponent::Type::Edit: {
        if (value_log.edit_data_info.has_value()) {
          const geo_log::GeometryInfoLog::EditDataInfo &edit_info = *value_log.edit_data_info;
          char line[256];
          SNPRINTF(line,
                   TIP_("\u2022 Edit Curves: %s, %s"),
                   edit_info.has_deformed_positions ? TIP_("positions") : TIP_("no positions"),
                   edit_info.has_deform_matrices ? TIP_("matrices") : TIP_("no matrices"));
          ss << line;
        }
        break;
      }
      case bke::GeometryComponent::Type::GreasePencil: {
        const geo_log::GeometryInfoLog::GreasePencilInfo &grease_pencil_info =
            *value_log.grease_pencil_info;
        char line[256];
        SNPRINTF(line,
                 TIP_("\u2022 Grease Pencil: %s layers"),
                 to_string(grease_pencil_info.layers_num).c_str());
        ss << line;
        break;
        break;
      }
    }
    if (type != component_types.last()) {
      ss << ".\n";
    }
  }
}

static void create_inspection_string_for_geometry_socket(std::stringstream &ss,
                                                         const nodes::decl::Geometry *socket_decl,
                                                         const bool after_log)
{
  /* If the geometry declaration is null, as is the case for input to group output,
   * or it is an output socket don't show supported types. */
  if (socket_decl == nullptr || socket_decl->in_out == SOCK_OUT) {
    return;
  }

  if (after_log) {
    ss << ".\n\n";
  }

  Span<bke::GeometryComponent::Type> supported_types = socket_decl->supported_types();
  if (supported_types.is_empty()) {
    ss << TIP_("Supported: All Types");
    return;
  }

  ss << TIP_("Supported: ");
  for (bke::GeometryComponent::Type type : supported_types) {
    switch (type) {
      case bke::GeometryComponent::Type::Mesh: {
        ss << TIP_("Mesh");
        break;
      }
      case bke::GeometryComponent::Type::PointCloud: {
        ss << TIP_("Point Cloud");
        break;
      }
      case bke::GeometryComponent::Type::Curve: {
        ss << TIP_("Curve");
        break;
      }
      case bke::GeometryComponent::Type::Instance: {
        ss << TIP_("Instances");
        break;
      }
      case bke::GeometryComponent::Type::Volume: {
        ss << CTX_TIP_(BLT_I18NCONTEXT_ID_ID, "Volume");
        break;
      }
      case bke::GeometryComponent::Type::Edit: {
        break;
      }
      case bke::GeometryComponent::Type::GreasePencil: {
        ss << TIP_("Grease Pencil");
        break;
      }
    }
    if (type != supported_types.last()) {
      ss << ", ";
    }
  }
}

static std::optional<std::string> create_socket_inspection_string(
    geo_log::GeoTreeLog &geo_tree_log, const bNodeSocket &socket)
{
  using namespace blender::nodes::geo_eval_log;

  if (socket.typeinfo->base_cpp_type == nullptr) {
    return std::nullopt;
  }

  geo_tree_log.ensure_socket_values();
  ValueLog *value_log = geo_tree_log.find_socket_value_log(socket);
  std::stringstream ss;
  if (const geo_log::GenericValueLog *generic_value_log =
          dynamic_cast<const geo_log::GenericValueLog *>(value_log))
  {
    create_inspection_string_for_generic_value(socket, generic_value_log->value, ss);
  }
  else if (const geo_log::FieldInfoLog *gfield_value_log =
               dynamic_cast<const geo_log::FieldInfoLog *>(value_log))
  {
    create_inspection_string_for_field_info(socket, *gfield_value_log, ss);
  }
  else if (const geo_log::GeometryInfoLog *geo_value_log =
               dynamic_cast<const geo_log::GeometryInfoLog *>(value_log))
  {
    create_inspection_string_for_geometry_info(*geo_value_log, ss);
  }

  if (const nodes::decl::Geometry *socket_decl = dynamic_cast<const nodes::decl::Geometry *>(
          socket.runtime->declaration))
  {
    const bool after_log = value_log != nullptr;
    create_inspection_string_for_geometry_socket(ss, socket_decl, after_log);
  }

  std::string str = ss.str();
  if (str.empty()) {
    return std::nullopt;
  }
  return str;
}

static bool node_socket_has_tooltip(const bNodeTree &ntree, const bNodeSocket &socket)
{
  if (ntree.type == NTREE_GEOMETRY) {
    return true;
  }

  if (socket.runtime->declaration != nullptr) {
    const nodes::SocketDeclaration &socket_decl = *socket.runtime->declaration;
    return !socket_decl.description.empty();
  }

  return false;
}

static char *node_socket_get_tooltip(const SpaceNode *snode,
                                     const bNodeTree &ntree,
                                     const bNodeSocket &socket)
{
  TreeDrawContext tree_draw_ctx;
  if (snode != nullptr) {
    if (ntree.type == NTREE_GEOMETRY) {
      tree_draw_ctx.geo_log_by_zone =
          geo_log::GeoModifierLog::get_tree_log_by_zone_for_node_editor(*snode);
    }
  }

  std::stringstream output;
  if (socket.runtime->declaration != nullptr) {
    const blender::nodes::SocketDeclaration &socket_decl = *socket.runtime->declaration;
    blender::StringRef description = socket_decl.description;
    if (!description.is_empty()) {
      output << TIP_(description.data());
    }
  }

  geo_log::GeoTreeLog *geo_tree_log = [&]() -> geo_log::GeoTreeLog * {
    const bNodeTreeZones *zones = ntree.zones();
    if (!zones) {
      return nullptr;
    }
    const bNodeTreeZone *zone = zones->get_zone_by_socket(socket);
    return tree_draw_ctx.geo_log_by_zone.lookup_default(zone, nullptr);
  }();

  if (ntree.type == NTREE_GEOMETRY && geo_tree_log != nullptr) {
    if (!output.str().empty()) {
      output << ".\n\n";
    }

    std::optional<std::string> socket_inspection_str = create_socket_inspection_string(
        *geo_tree_log, socket);
    if (socket_inspection_str.has_value()) {
      output << *socket_inspection_str;
    }
    else {
      output << TIP_(
          "Unknown socket value. Either the socket was not used or its value was not logged "
          "during the last evaluation");
    }
  }

  if (output.str().empty()) {
    output << bke::nodeSocketLabel(&socket);
  }

  return BLI_strdup(output.str().c_str());
}

static void node_socket_add_tooltip_in_node_editor(const bNodeTree &ntree,
                                                   const bNodeSocket &sock,
                                                   uiLayout &layout)
{
  if (!node_socket_has_tooltip(ntree, sock)) {
    return;
  }
  uiLayoutSetTooltipFunc(
      &layout,
      [](bContext *C, void *argN, const char * /*tip*/) {
        const SpaceNode &snode = *CTX_wm_space_node(C);
        const bNodeTree &ntree = *snode.edittree;
        const int index_in_tree = POINTER_AS_INT(argN);
        ntree.ensure_topology_cache();
        return node_socket_get_tooltip(&snode, ntree, *ntree.all_sockets()[index_in_tree]);
      },
      POINTER_FROM_INT(sock.index_in_tree()),
      nullptr,
      nullptr);
}

void node_socket_add_tooltip(const bNodeTree &ntree, const bNodeSocket &sock, uiLayout &layout)
{
  if (!node_socket_has_tooltip(ntree, sock)) {
    return;
  }

  struct SocketTooltipData {
    const bNodeTree *ntree;
    const bNodeSocket *socket;
  };

  SocketTooltipData *data = MEM_cnew<SocketTooltipData>(__func__);
  data->ntree = &ntree;
  data->socket = &sock;

  uiLayoutSetTooltipFunc(
      &layout,
      [](bContext *C, void *argN, const char * /*tip*/) {
        SocketTooltipData *data = static_cast<SocketTooltipData *>(argN);
        const SpaceNode *snode = CTX_wm_space_node(C);
        return node_socket_get_tooltip(snode, *data->ntree, *data->socket);
      },
      data,
      MEM_dupallocN,
      MEM_freeN);
}

static void node_socket_draw_nested(const bContext &C,
                                    const bNodeTree &ntree,
                                    PointerRNA &node_ptr,
                                    uiBlock &block,
                                    const bNodeSocket &sock,
                                    const uint pos_id,
                                    const uint col_id,
                                    const uint shape_id,
                                    const uint size_id,
                                    const uint outline_col_id,
                                    const float size,
                                    const bool selected)
{
  const float2 location = sock.runtime->location;

  float color[4];
  float outline_color[4];
  node_socket_color_get(C, ntree, node_ptr, sock, color);
  node_socket_outline_color_get(selected, sock.type, outline_color);

  node_socket_draw(sock,
                   color,
                   outline_color,
                   size,
                   location.x,
                   location.y,
                   pos_id,
                   col_id,
                   shape_id,
                   size_id,
                   outline_col_id);

  if (!node_socket_has_tooltip(ntree, sock)) {
    return;
  }

  /* Ideally sockets themselves should be buttons, but they aren't currently. So add an invisible
   * button on top of them for the tooltip. */
  const eUIEmbossType old_emboss = UI_block_emboss_get(&block);
  UI_block_emboss_set(&block, UI_EMBOSS_NONE);
  uiBut *but = uiDefIconBut(&block,
                            UI_BTYPE_BUT,
                            0,
                            ICON_NONE,
                            location.x - size / 2.0f,
                            location.y - size / 2.0f,
                            size,
                            size,
                            nullptr,
                            0,
                            0,
                            0,
                            0,
                            nullptr);

  UI_but_func_tooltip_set(
      but,
      [](bContext *C, void *argN, const char * /*tip*/) {
        const SpaceNode &snode = *CTX_wm_space_node(C);
        const bNodeTree &ntree = *snode.edittree;
        const int index_in_tree = POINTER_AS_INT(argN);
        ntree.ensure_topology_cache();
        return node_socket_get_tooltip(&snode, ntree, *ntree.all_sockets()[index_in_tree]);
      },
      POINTER_FROM_INT(sock.index_in_tree()),
      nullptr);
  /* Disable the button so that clicks on it are ignored the link operator still works. */
  UI_but_flag_enable(but, UI_BUT_DISABLED);
  UI_block_emboss_set(&block, old_emboss);
}

void node_socket_draw(bNodeSocket *sock, const rcti *rect, const float color[4], float scale)
{
  const float size = NODE_SOCKSIZE_DRAW_MULIPLIER * NODE_SOCKSIZE * scale;
  rcti draw_rect = *rect;
  float outline_color[4] = {0};

  node_socket_outline_color_get(sock->flag & SELECT, sock->type, outline_color);

  BLI_rcti_resize(&draw_rect, size, size);

  GPUVertFormat *format = immVertexFormat();
  uint pos_id = GPU_vertformat_attr_add(format, "pos", GPU_COMP_F32, 2, GPU_FETCH_FLOAT);
  uint col_id = GPU_vertformat_attr_add(format, "color", GPU_COMP_F32, 4, GPU_FETCH_FLOAT);
  uint shape_id = GPU_vertformat_attr_add(format, "flags", GPU_COMP_U32, 1, GPU_FETCH_INT);
  uint size_id = GPU_vertformat_attr_add(format, "size", GPU_COMP_F32, 1, GPU_FETCH_FLOAT);
  uint outline_col_id = GPU_vertformat_attr_add(
      format, "outlineColor", GPU_COMP_F32, 4, GPU_FETCH_FLOAT);

  eGPUBlend state = GPU_blend_get();
  GPU_blend(GPU_BLEND_ALPHA);
  GPU_program_point_size(true);

  immBindBuiltinProgram(GPU_SHADER_KEYFRAME_SHAPE);
  immUniform1f("outline_scale", NODE_SOCK_OUTLINE_SCALE);
  immUniform2f("ViewportSize", -1.0f, -1.0f);

  /* Single point. */
  immBegin(GPU_PRIM_POINTS, 1);
  node_socket_draw(*sock,
                   color,
                   outline_color,
                   BLI_rcti_size_y(&draw_rect),
                   BLI_rcti_cent_x(&draw_rect),
                   BLI_rcti_cent_y(&draw_rect),
                   pos_id,
                   col_id,
                   shape_id,
                   size_id,
                   outline_col_id);
  immEnd();

  immUnbindProgram();
  GPU_program_point_size(false);

  /* Restore. */
  GPU_blend(state);
}

static void node_draw_preview_background(rctf *rect)
{
  GPUVertFormat *format = immVertexFormat();
  uint pos = GPU_vertformat_attr_add(format, "pos", GPU_COMP_F32, 2, GPU_FETCH_FLOAT);

  immBindBuiltinProgram(GPU_SHADER_2D_CHECKER);

  /* Drawing the checkerboard. */
  const float checker_dark = UI_ALPHA_CHECKER_DARK / 255.0f;
  const float checker_light = UI_ALPHA_CHECKER_LIGHT / 255.0f;
  immUniform4f("color1", checker_dark, checker_dark, checker_dark, 1.0f);
  immUniform4f("color2", checker_light, checker_light, checker_light, 1.0f);
  immUniform1i("size", 8);
  immRectf(pos, rect->xmin, rect->ymin, rect->xmax, rect->ymax);
  immUnbindProgram();
}

/* Not a callback. */
static void node_draw_preview(const Scene *scene, ImBuf *preview, rctf *prv)
{
  float xrect = BLI_rctf_size_x(prv);
  float yrect = BLI_rctf_size_y(prv);
  float xscale = xrect / float(preview->x);
  float yscale = yrect / float(preview->y);
  float scale;

  /* Uniform scale and offset. */
  rctf draw_rect = *prv;
  if (xscale < yscale) {
    float offset = 0.5f * (yrect - float(preview->y) * xscale);
    draw_rect.ymin += offset;
    draw_rect.ymax -= offset;
    scale = xscale;
  }
  else {
    float offset = 0.5f * (xrect - float(preview->x) * yscale);
    draw_rect.xmin += offset;
    draw_rect.xmax -= offset;
    scale = yscale;
  }

  node_draw_preview_background(&draw_rect);

  GPU_blend(GPU_BLEND_ALPHA);
  /* Premul graphics. */
  GPU_blend(GPU_BLEND_ALPHA);

  ED_draw_imbuf(preview,
                draw_rect.xmin,
                draw_rect.ymin,
                false,
                &scene->view_settings,
                &scene->display_settings,
                scale,
                scale);

  GPU_blend(GPU_BLEND_NONE);

  float black[4] = {0.0f, 0.0f, 0.0f, 1.0f};
  UI_draw_roundbox_corner_set(UI_CNR_ALL);
  const float outline_width = 1.0f;
  draw_rect.xmin -= outline_width;
  draw_rect.xmax += outline_width;
  draw_rect.ymin -= outline_width;
  draw_rect.ymax += outline_width;
  UI_draw_roundbox_4fv(&draw_rect, false, BASIS_RAD / 2, black);
}

/* Common handle function for operator buttons that need to select the node first. */
static void node_toggle_button_cb(bContext *C, void *node_argv, void *op_argv)
{
  SpaceNode &snode = *CTX_wm_space_node(C);
  bNodeTree &node_tree = *snode.edittree;
  bNode &node = *node_tree.node_by_id(POINTER_AS_INT(node_argv));
  const char *opname = (const char *)op_argv;

  /* Select & activate only the button's node. */
  node_select_single(*C, node);

  WM_operator_name_call(C, opname, WM_OP_INVOKE_DEFAULT, nullptr, nullptr);
}

static void node_draw_shadow(const SpaceNode &snode,
                             const bNode &node,
                             const float radius,
                             const float alpha)
{
  const rctf &rct = node.runtime->totr;
  UI_draw_roundbox_corner_set(UI_CNR_ALL);
  ui_draw_dropshadow(&rct, radius, snode.runtime->aspect, alpha, node.flag & SELECT);
}

static void node_draw_sockets(const View2D &v2d,
                              const bContext &C,
                              const bNodeTree &ntree,
                              const bNode &node,
                              uiBlock &block,
                              const bool draw_outputs,
                              const bool select_all)
{
  if (node.input_sockets().is_empty() && node.output_sockets().is_empty()) {
    return;
  }

  bool selected = false;

  GPUVertFormat *format = immVertexFormat();
  uint pos_id = GPU_vertformat_attr_add(format, "pos", GPU_COMP_F32, 2, GPU_FETCH_FLOAT);
  uint col_id = GPU_vertformat_attr_add(format, "color", GPU_COMP_F32, 4, GPU_FETCH_FLOAT);
  uint shape_id = GPU_vertformat_attr_add(format, "flags", GPU_COMP_U32, 1, GPU_FETCH_INT);
  uint size_id = GPU_vertformat_attr_add(format, "size", GPU_COMP_F32, 1, GPU_FETCH_FLOAT);
  uint outline_col_id = GPU_vertformat_attr_add(
      format, "outlineColor", GPU_COMP_F32, 4, GPU_FETCH_FLOAT);

  GPU_blend(GPU_BLEND_ALPHA);
  GPU_program_point_size(true);
  immBindBuiltinProgram(GPU_SHADER_KEYFRAME_SHAPE);
  immUniform1f("outline_scale", NODE_SOCK_OUTLINE_SCALE);
  immUniform2f("ViewportSize", -1.0f, -1.0f);

  /* Set handle size. */
  const float socket_draw_size = NODE_SOCKSIZE * NODE_SOCKSIZE_DRAW_MULIPLIER;
  float scale;
  UI_view2d_scale_get(&v2d, &scale, nullptr);
  scale *= socket_draw_size;

  if (!select_all) {
    immBeginAtMost(GPU_PRIM_POINTS, node.input_sockets().size() + node.output_sockets().size());
  }

  PointerRNA node_ptr = RNA_pointer_create(
      &const_cast<ID &>(ntree.id), &RNA_Node, &const_cast<bNode &>(node));

  /* Socket inputs. */
  int selected_input_len = 0;
  for (const bNodeSocket *sock : node.input_sockets()) {
    /* In "hidden" nodes: draw sockets even when panels are collapsed. */
    if (!node.is_socket_icon_drawn(*sock)) {
      continue;
    }
    if (select_all || (sock->flag & SELECT)) {
      if (!(sock->flag & SOCK_MULTI_INPUT)) {
        /* Don't add multi-input sockets here since they are drawn in a different batch. */
        selected_input_len++;
      }
      continue;
    }
    /* Don't draw multi-input sockets here since they are drawn in a different batch. */
    if (sock->flag & SOCK_MULTI_INPUT) {
      continue;
    }

    node_socket_draw_nested(C,
                            ntree,
                            node_ptr,
                            block,
                            *sock,
                            pos_id,
                            col_id,
                            shape_id,
                            size_id,
                            outline_col_id,
                            scale,
                            selected);
  }

  /* Socket outputs. */
  int selected_output_len = 0;
  if (draw_outputs) {
    for (const bNodeSocket *sock : node.output_sockets()) {
      /* In "hidden" nodes: draw sockets even when panels are collapsed. */
      if (!node.is_socket_icon_drawn(*sock)) {
        continue;
      }
      if (select_all || (sock->flag & SELECT)) {
        selected_output_len++;
        continue;
      }

      node_socket_draw_nested(C,
                              ntree,
                              node_ptr,
                              block,
                              *sock,
                              pos_id,
                              col_id,
                              shape_id,
                              size_id,
                              outline_col_id,
                              scale,
                              selected);
    }
  }

  if (!select_all) {
    immEnd();
  }

  /* Go back and draw selected sockets. */
  if (selected_input_len + selected_output_len > 0) {
    /* Outline for selected sockets. */

    selected = true;

    immBegin(GPU_PRIM_POINTS, selected_input_len + selected_output_len);

    if (selected_input_len) {
      /* Socket inputs. */
      for (const bNodeSocket *sock : node.input_sockets()) {
        if (!node.is_socket_icon_drawn(*sock)) {
          continue;
        }
        /* Don't draw multi-input sockets here since they are drawn in a different batch. */
        if (sock->flag & SOCK_MULTI_INPUT) {
          continue;
        }
        if (select_all || (sock->flag & SELECT)) {
          node_socket_draw_nested(C,
                                  ntree,
                                  node_ptr,
                                  block,
                                  *sock,
                                  pos_id,
                                  col_id,
                                  shape_id,
                                  size_id,
                                  outline_col_id,
                                  scale,
                                  selected);
          if (--selected_input_len == 0) {
            /* Stop as soon as last one is drawn. */
            break;
          }
        }
      }
    }

    if (selected_output_len) {
      /* Socket outputs. */
      for (const bNodeSocket *sock : node.output_sockets()) {
        if (!node.is_socket_icon_drawn(*sock)) {
          continue;
        }
        if (select_all || (sock->flag & SELECT)) {
          node_socket_draw_nested(C,
                                  ntree,
                                  node_ptr,
                                  block,
                                  *sock,
                                  pos_id,
                                  col_id,
                                  shape_id,
                                  size_id,
                                  outline_col_id,
                                  scale,
                                  selected);
          if (--selected_output_len == 0) {
            /* Stop as soon as last one is drawn. */
            break;
          }
        }
      }
    }

    immEnd();
  }

  immUnbindProgram();

  GPU_program_point_size(false);
  GPU_blend(GPU_BLEND_NONE);

  /* Draw multi-input sockets after the others because they are drawn with `UI_draw_roundbox`
   * rather than with `GL_POINT`. */
  for (const bNodeSocket *socket : node.input_sockets()) {
    if (!node.is_socket_icon_drawn(*socket)) {
      continue;
    }
    if (!(socket->flag & SOCK_MULTI_INPUT)) {
      continue;
    }

    const bool is_node_hidden = (node.flag & NODE_HIDDEN);
    const float width = 0.5f * socket_draw_size;
    float height = is_node_hidden ? width : node_socket_calculate_height(*socket) - width;

    float color[4];
    float outline_color[4];
    node_socket_color_get(C, ntree, node_ptr, *socket, color);
    node_socket_outline_color_get(socket->flag & SELECT, socket->type, outline_color);

    const float2 location = socket->runtime->location;
    node_socket_draw_multi_input(color, outline_color, width, height, location);
  }
}

static void node_panel_toggle_button_cb(bContext *C, void *panel_state_argv, void *ntree_argv)
{
  Main *bmain = CTX_data_main(C);
  bNodePanelState *panel_state = static_cast<bNodePanelState *>(panel_state_argv);
  bNodeTree *ntree = static_cast<bNodeTree *>(ntree_argv);

  panel_state->flag ^= NODE_PANEL_COLLAPSED;

  ED_node_tree_propagate_change(C, bmain, ntree);
}

/* Draw panel backgrounds first, so other node elements can be rendered on top. */
static void node_draw_panels_background(const bNode &node, uiBlock &block)
{
  namespace nodes = blender::nodes;

  BLI_assert(is_node_panels_supported(node));
  BLI_assert(node.runtime->panels.size() == node.panel_states().size());

  const nodes::NodeDeclaration &decl = *node.declaration();
  const rctf &rct = node.runtime->totr;
  float color_panel[4];
  UI_GetThemeColorBlend4f(TH_BACK, TH_NODE, 0.2f, color_panel);

  /* True if the last panel is open, draw bottom gap as background. */
  bool is_last_panel_visible = false;
  float last_panel_content_y = 0.0f;

  int panel_i = 0;
  for (const nodes::ItemDeclarationPtr &item_decl : decl.items) {
    const nodes::PanelDeclaration *panel_decl = dynamic_cast<nodes::PanelDeclaration *>(
        item_decl.get());
    if (panel_decl == nullptr) {
      /* Not a panel. */
      continue;
    }

    const bNodePanelState &state = node.panel_states()[panel_i];
    const bke::bNodePanelRuntime &runtime = node.runtime->panels[panel_i];

    /* Don't draw hidden or collapsed panels. */
    const bool is_background_visible = state.has_visible_content() &&
                                       !(state.is_collapsed() || state.is_parent_collapsed());
    is_last_panel_visible = is_background_visible;
    last_panel_content_y = runtime.max_content_y;
    if (!is_background_visible) {
      ++panel_i;
      continue;
    }

    UI_block_emboss_set(&block, UI_EMBOSS_NONE);

    /* Panel background. */
    const rctf content_rect = {rct.xmin, rct.xmax, runtime.min_content_y, runtime.max_content_y};
    UI_draw_roundbox_corner_set(UI_CNR_NONE);
    UI_draw_roundbox_4fv(&content_rect, true, BASIS_RAD, color_panel);

    UI_block_emboss_set(&block, UI_EMBOSS);

    ++panel_i;
  }

  /* If last item is an open panel, extend the panel background to cover the bottom border. */
  if (is_last_panel_visible) {
    UI_block_emboss_set(&block, UI_EMBOSS_NONE);

    const rctf content_rect = {rct.xmin, rct.xmax, rct.ymin, last_panel_content_y};
    UI_draw_roundbox_corner_set(UI_CNR_BOTTOM_RIGHT | UI_CNR_BOTTOM_LEFT);
    UI_draw_roundbox_4fv(&content_rect, true, BASIS_RAD, color_panel);

    UI_block_emboss_set(&block, UI_EMBOSS);
  }
}

static void node_draw_panels(bNodeTree &ntree, const bNode &node, uiBlock &block)
{
  namespace nodes = blender::nodes;

  BLI_assert(is_node_panels_supported(node));
  BLI_assert(node.runtime->panels.size() == node.panel_states().size());

  const nodes::NodeDeclaration &decl = *node.declaration();
  const rctf &rct = node.runtime->totr;

  int panel_i = 0;
  for (const nodes::ItemDeclarationPtr &item_decl : decl.items) {
    const nodes::PanelDeclaration *panel_decl = dynamic_cast<nodes::PanelDeclaration *>(
        item_decl.get());
    if (panel_decl == nullptr) {
      /* Not a panel. */
      continue;
    }

    const bNodePanelState &state = node.panel_states()[panel_i];
    /* Don't draw hidden panels. */
    const bool is_header_visible = state.has_visible_content() && !state.is_parent_collapsed();
    if (!is_header_visible) {
      ++panel_i;
      continue;
    }
    const bke::bNodePanelRuntime &runtime = node.runtime->panels[panel_i];

    const rctf rect = {
        rct.xmin,
        rct.xmax,
        runtime.location_y - NODE_DYS,
        runtime.location_y + NODE_DYS,
    };

    UI_block_emboss_set(&block, UI_EMBOSS_NONE);

    /* Collapse/expand icon. */
    const int but_size = U.widget_unit * 0.8f;
    uiDefIconBut(&block,
                 UI_BTYPE_BUT_TOGGLE,
                 0,
                 state.is_collapsed() ? ICON_RIGHTARROW : ICON_DOWNARROW_HLT,
                 rct.xmin + (NODE_MARGIN_X / 3),
                 runtime.location_y - but_size / 2,
                 but_size,
                 but_size,
                 nullptr,
                 0.0f,
                 0.0f,
                 0.0f,
                 0.0f,
                 "");

    /* Panel label. */
    uiBut *but = uiDefBut(&block,
                          UI_BTYPE_LABEL,
                          0,
                          IFACE_(panel_decl->name.c_str()),
                          int(rct.xmin + NODE_MARGIN_X + 0.4f),
                          int(runtime.location_y - NODE_DYS),
                          short(rct.xmax - rct.xmin - (30.0f * UI_SCALE_FAC)),
                          short(NODE_DY),
                          nullptr,
                          0,
                          0,
                          0,
                          0,
                          "");
    if (node.flag & NODE_MUTED) {
      UI_but_flag_enable(but, UI_BUT_INACTIVE);
    }

    /* Invisible button covering the entire header for collapsing/expanding. */
    const int header_but_margin = NODE_MARGIN_X / 3;
    but = uiDefIconBut(&block,
                       UI_BTYPE_BUT_TOGGLE,
                       0,
                       ICON_NONE,
                       rect.xmin + header_but_margin,
                       rect.ymin,
                       std::max(int(rect.xmax - rect.xmin - 2 * header_but_margin), 0),
                       rect.ymax - rect.ymin,
                       nullptr,
                       0.0f,
                       0.0f,
                       0.0f,
                       0.0f,
                       "");
    UI_but_func_set(
        but, node_panel_toggle_button_cb, const_cast<bNodePanelState *>(&state), &ntree);

    UI_block_emboss_set(&block, UI_EMBOSS);

    ++panel_i;
  }
}

static int node_error_type_to_icon(const geo_log::NodeWarningType type)
{
  switch (type) {
    case geo_log::NodeWarningType::Error:
      return ICON_ERROR;
    case geo_log::NodeWarningType::Warning:
      return ICON_ERROR;
    case geo_log::NodeWarningType::Info:
      return ICON_INFO;
  }

  BLI_assert(false);
  return ICON_ERROR;
}

static uint8_t node_error_type_priority(const geo_log::NodeWarningType type)
{
  switch (type) {
    case geo_log::NodeWarningType::Error:
      return 3;
    case geo_log::NodeWarningType::Warning:
      return 2;
    case geo_log::NodeWarningType::Info:
      return 1;
  }

  BLI_assert(false);
  return 0;
}

static geo_log::NodeWarningType node_error_highest_priority(Span<geo_log::NodeWarning> warnings)
{
  uint8_t highest_priority = 0;
  geo_log::NodeWarningType highest_priority_type = geo_log::NodeWarningType::Info;
  for (const geo_log::NodeWarning &warning : warnings) {
    const uint8_t priority = node_error_type_priority(warning.type);
    if (priority > highest_priority) {
      highest_priority = priority;
      highest_priority_type = warning.type;
    }
  }
  return highest_priority_type;
}

struct NodeErrorsTooltipData {
  Span<geo_log::NodeWarning> warnings;
};

static char *node_errors_tooltip_fn(bContext * /*C*/, void *argN, const char * /*tip*/)
{
  NodeErrorsTooltipData &data = *(NodeErrorsTooltipData *)argN;

  std::string complete_string;

  for (const geo_log::NodeWarning &warning : data.warnings.drop_back(1)) {
    complete_string += warning.message;
    /* Adding the period is not ideal for multi-line messages, but it is consistent
     * with other tooltip implementations in Blender, so it is added here. */
    complete_string += '.';
    complete_string += '\n';
  }

  /* Let the tooltip system automatically add the last period. */
  complete_string += data.warnings.last().message;

  return BLI_strdupn(complete_string.c_str(), complete_string.size());
}

#define NODE_HEADER_ICON_SIZE (0.8f * U.widget_unit)

static void node_add_unsupported_compositor_operation_error_message_button(const bNode &node,
                                                                           uiBlock &block,
                                                                           const rctf &rect,
                                                                           float &icon_offset)
{
  icon_offset -= NODE_HEADER_ICON_SIZE;
  UI_block_emboss_set(&block, UI_EMBOSS_NONE);
  uiDefIconBut(&block,
               UI_BTYPE_BUT,
               0,
               ICON_ERROR,
               icon_offset,
               rect.ymax - NODE_DY,
               NODE_HEADER_ICON_SIZE,
               UI_UNIT_Y,
               nullptr,
               0,
               0,
               0,
               0,
               TIP_(node.typeinfo->realtime_compositor_unsupported_message));
  UI_block_emboss_set(&block, UI_EMBOSS);
}

static void node_add_error_message_button(const TreeDrawContext &tree_draw_ctx,
                                          const bNode &node,
                                          uiBlock &block,
                                          const rctf &rect,
                                          float &icon_offset)
{
  if (tree_draw_ctx.used_by_realtime_compositor &&
      node.typeinfo->realtime_compositor_unsupported_message)
  {
    node_add_unsupported_compositor_operation_error_message_button(node, block, rect, icon_offset);
    return;
  }

  geo_log::GeoTreeLog *geo_tree_log = [&]() -> geo_log::GeoTreeLog * {
    const bNodeTreeZones *zones = node.owner_tree().zones();
    if (!zones) {
      return nullptr;
    }
    const bNodeTreeZone *zone = zones->get_zone_by_node(node.identifier);
    if (zone && ELEM(&node, zone->input_node, zone->output_node)) {
      zone = zone->parent_zone;
    }
    return tree_draw_ctx.geo_log_by_zone.lookup_default(zone, nullptr);
  }();

  Span<geo_log::NodeWarning> warnings;
  if (geo_tree_log) {
    geo_log::GeoNodeLog *node_log = geo_tree_log->nodes.lookup_ptr(node.identifier);
    if (node_log != nullptr) {
      warnings = node_log->warnings;
    }
  }
  if (warnings.is_empty()) {
    return;
  }

  const geo_log::NodeWarningType display_type = node_error_highest_priority(warnings);
  NodeErrorsTooltipData *tooltip_data = MEM_new<NodeErrorsTooltipData>(__func__);
  tooltip_data->warnings = warnings;

  icon_offset -= NODE_HEADER_ICON_SIZE;
  UI_block_emboss_set(&block, UI_EMBOSS_NONE);
  uiBut *but = uiDefIconBut(&block,
                            UI_BTYPE_BUT,
                            0,
                            node_error_type_to_icon(display_type),
                            icon_offset,
                            rect.ymax - NODE_DY,
                            NODE_HEADER_ICON_SIZE,
                            UI_UNIT_Y,
                            nullptr,
                            0,
                            0,
                            0,
                            0,
                            nullptr);
  UI_but_func_tooltip_set(but, node_errors_tooltip_fn, tooltip_data, [](void *arg) {
    MEM_delete(static_cast<NodeErrorsTooltipData *>(arg));
  });
  UI_block_emboss_set(&block, UI_EMBOSS);
}

static std::optional<std::chrono::nanoseconds> node_get_execution_time(
    const TreeDrawContext &tree_draw_ctx, const bNodeTree &ntree, const bNode &node)
{
  geo_log::GeoTreeLog *tree_log = [&]() -> geo_log::GeoTreeLog * {
    const bNodeTreeZones *zones = ntree.zones();
    if (!zones) {
      return nullptr;
    }
    const bNodeTreeZone *zone = zones->get_zone_by_node(node.identifier);
    return tree_draw_ctx.geo_log_by_zone.lookup_default(zone, nullptr);
  }();

  if (tree_log == nullptr) {
    return std::nullopt;
  }
  if (node.type == NODE_GROUP_OUTPUT) {
    return tree_log->run_time_sum;
  }
  if (node.is_frame()) {
    /* Could be cached in the future if this recursive code turns out to be slow. */
    std::chrono::nanoseconds run_time{0};
    bool found_node = false;

    for (const bNode *tnode : node.direct_children_in_frame()) {
      if (tnode->is_frame()) {
        std::optional<std::chrono::nanoseconds> sub_frame_run_time = node_get_execution_time(
            tree_draw_ctx, ntree, *tnode);
        if (sub_frame_run_time.has_value()) {
          run_time += *sub_frame_run_time;
          found_node = true;
        }
      }
      else {
        if (const geo_log::GeoNodeLog *node_log = tree_log->nodes.lookup_ptr_as(tnode->identifier))
        {
          found_node = true;
          run_time += node_log->run_time;
        }
      }
    }
    if (found_node) {
      return run_time;
    }
    return std::nullopt;
  }
  if (const geo_log::GeoNodeLog *node_log = tree_log->nodes.lookup_ptr(node.identifier)) {
    return node_log->run_time;
  }
  return std::nullopt;
}

static std::string node_get_execution_time_label(TreeDrawContext &tree_draw_ctx,
                                                 const SpaceNode &snode,
                                                 const bNode &node)
{
  const std::optional<std::chrono::nanoseconds> exec_time = node_get_execution_time(
      tree_draw_ctx, *snode.edittree, node);

  if (!exec_time.has_value()) {
    return std::string("");
  }

  const uint64_t exec_time_us =
      std::chrono::duration_cast<std::chrono::microseconds>(*exec_time).count();

  /* Don't show time if execution time is 0 microseconds. */
  if (exec_time_us == 0) {
    return std::string("-");
  }
  if (exec_time_us < 100) {
    return std::string("< 0.1 ms");
  }

  int precision = 0;
  /* Show decimal if value is below 1ms */
  if (exec_time_us < 1000) {
    precision = 2;
  }
  else if (exec_time_us < 10000) {
    precision = 1;
  }

  std::stringstream stream;
  stream << std::fixed << std::setprecision(precision) << (exec_time_us / 1000.0f);
  return stream.str() + " ms";
}

struct NodeExtraInfoRow {
  std::string text;
  int icon;
  const char *tooltip = nullptr;

  uiButToolTipFunc tooltip_fn = nullptr;
  void *tooltip_fn_arg = nullptr;
  void (*tooltip_fn_free_arg)(void *) = nullptr;
};

struct NamedAttributeTooltipArg {
  Map<StringRefNull, geo_log::NamedAttributeUsage> usage_by_attribute;
};

static char *named_attribute_tooltip(bContext * /*C*/, void *argN, const char * /*tip*/)
{
  NamedAttributeTooltipArg &arg = *static_cast<NamedAttributeTooltipArg *>(argN);

  std::stringstream ss;
  ss << TIP_("Accessed named attributes:") << "\n";

  struct NameWithUsage {
    StringRefNull name;
    geo_log::NamedAttributeUsage usage;
  };

  Vector<NameWithUsage> sorted_used_attribute;
  for (auto &&item : arg.usage_by_attribute.items()) {
    sorted_used_attribute.append({item.key, item.value});
  }
  std::sort(sorted_used_attribute.begin(),
            sorted_used_attribute.end(),
            [](const NameWithUsage &a, const NameWithUsage &b) {
              return BLI_strcasecmp_natural(a.name.c_str(), b.name.c_str()) <= 0;
            });

  for (const NameWithUsage &attribute : sorted_used_attribute) {
    const StringRefNull name = attribute.name;
    const geo_log::NamedAttributeUsage usage = attribute.usage;
    ss << fmt::format(TIP_("  \u2022 \"{}\": "), std::string_view(name));
    Vector<std::string> usages;
    if ((usage & geo_log::NamedAttributeUsage::Read) != geo_log::NamedAttributeUsage::None) {
      usages.append(TIP_("read"));
    }
    if ((usage & geo_log::NamedAttributeUsage::Write) != geo_log::NamedAttributeUsage::None) {
      usages.append(TIP_("write"));
    }
    if ((usage & geo_log::NamedAttributeUsage::Remove) != geo_log::NamedAttributeUsage::None) {
      usages.append(TIP_("remove"));
    }
    for (const int i : usages.index_range()) {
      ss << usages[i];
      if (i < usages.size() - 1) {
        ss << ", ";
      }
    }
    ss << "\n";
  }
  ss << "\n";
  ss << TIP_(
      "Attributes with these names used within the group may conflict with existing attributes");
  return BLI_strdup(ss.str().c_str());
}

static NodeExtraInfoRow row_from_used_named_attribute(
    const Map<StringRefNull, geo_log::NamedAttributeUsage> &usage_by_attribute_name)
{
  const int attributes_num = usage_by_attribute_name.size();

  NodeExtraInfoRow row;
  row.text = std::to_string(attributes_num) +
             (attributes_num == 1 ? TIP_(" Named Attribute") : TIP_(" Named Attributes"));
  row.icon = ICON_SPREADSHEET;
  row.tooltip_fn = named_attribute_tooltip;
  row.tooltip_fn_arg = new NamedAttributeTooltipArg{usage_by_attribute_name};
  row.tooltip_fn_free_arg = [](void *arg) { delete static_cast<NamedAttributeTooltipArg *>(arg); };
  return row;
}

static std::optional<NodeExtraInfoRow> node_get_accessed_attributes_row(
    TreeDrawContext &tree_draw_ctx, const bNode &node)
{
  geo_log::GeoTreeLog *geo_tree_log = [&]() -> geo_log::GeoTreeLog * {
    const bNodeTreeZones *zones = node.owner_tree().zones();
    if (!zones) {
      return nullptr;
    }
    const bNodeTreeZone *zone = zones->get_zone_by_node(node.identifier);
    return tree_draw_ctx.geo_log_by_zone.lookup_default(zone, nullptr);
  }();
  if (geo_tree_log == nullptr) {
    return std::nullopt;
  }
  if (ELEM(node.type,
           GEO_NODE_STORE_NAMED_ATTRIBUTE,
           GEO_NODE_REMOVE_ATTRIBUTE,
           GEO_NODE_INPUT_NAMED_ATTRIBUTE))
  {
    /* Only show the overlay when the name is passed in from somewhere else. */
    for (const bNodeSocket *socket : node.input_sockets()) {
      if (STREQ(socket->name, "Name")) {
        if (!socket->is_directly_linked()) {
          return std::nullopt;
        }
      }
    }
  }
  geo_tree_log->ensure_used_named_attributes();
  geo_log::GeoNodeLog *node_log = geo_tree_log->nodes.lookup_ptr(node.identifier);
  if (node_log == nullptr) {
    return std::nullopt;
  }
  if (node_log->used_named_attributes.is_empty()) {
    return std::nullopt;
  }
  return row_from_used_named_attribute(node_log->used_named_attributes);
}

static Vector<NodeExtraInfoRow> node_get_extra_info(TreeDrawContext &tree_draw_ctx,
                                                    const SpaceNode &snode,
                                                    const bNode &node)
{
  Vector<NodeExtraInfoRow> rows;
  if (!(snode.edittree->type == NTREE_GEOMETRY)) {
    /* Currently geometry nodes are the only nodes to have extra infos per nodes. */
    return rows;
  }

  if (snode.overlay.flag & SN_OVERLAY_SHOW_NAMED_ATTRIBUTES) {
    if (std::optional<NodeExtraInfoRow> row = node_get_accessed_attributes_row(tree_draw_ctx,
                                                                               node)) {
      rows.append(std::move(*row));
    }
  }

  if (snode.overlay.flag & SN_OVERLAY_SHOW_TIMINGS &&
      (ELEM(node.typeinfo->nclass, NODE_CLASS_GEOMETRY, NODE_CLASS_GROUP, NODE_CLASS_ATTRIBUTE) ||
       ELEM(node.type, NODE_FRAME, NODE_GROUP_OUTPUT)))
  {
    NodeExtraInfoRow row;
    row.text = node_get_execution_time_label(tree_draw_ctx, snode, node);
    if (!row.text.empty()) {
      row.tooltip = TIP_(
          "The execution time from the node tree's latest evaluation. For frame and group "
          "nodes, "
          "the time for all sub-nodes");
      row.icon = ICON_PREVIEW_RANGE;
      rows.append(std::move(row));
    }
  }

  geo_log::GeoTreeLog *tree_log = [&]() -> geo_log::GeoTreeLog * {
    const bNodeTreeZones *tree_zones = node.owner_tree().zones();
    if (!tree_zones) {
      return nullptr;
    }
    const bNodeTreeZone *zone = tree_zones->get_zone_by_node(node.identifier);
    return tree_draw_ctx.geo_log_by_zone.lookup_default(zone, nullptr);
  }();

  if (tree_log) {
    tree_log->ensure_debug_messages();
    const geo_log::GeoNodeLog *node_log = tree_log->nodes.lookup_ptr(node.identifier);
    if (node_log != nullptr) {
      for (const StringRef message : node_log->debug_messages) {
        NodeExtraInfoRow row;
        row.text = message;
        row.icon = ICON_INFO;
        rows.append(std::move(row));
      }
    }
  }

  return rows;
}

static void node_draw_extra_info_row(const bNode &node,
                                     uiBlock &block,
                                     const rctf &rect,
                                     const int row,
                                     const NodeExtraInfoRow &extra_info_row)
{
  const float but_icon_left = rect.xmin + 6.0f * UI_SCALE_FAC;
  const float but_icon_width = NODE_HEADER_ICON_SIZE * 0.8f;
  const float but_icon_right = but_icon_left + but_icon_width;

  UI_block_emboss_set(&block, UI_EMBOSS_NONE);
  uiBut *but_icon = uiDefIconBut(&block,
                                 UI_BTYPE_BUT,
                                 0,
                                 extra_info_row.icon,
                                 int(but_icon_left),
                                 int(rect.ymin + row * (20.0f * UI_SCALE_FAC)),
                                 but_icon_width,
                                 UI_UNIT_Y,
                                 nullptr,
                                 0,
                                 0,
                                 0,
                                 0,
                                 extra_info_row.tooltip);
  if (extra_info_row.tooltip_fn != nullptr) {
    UI_but_func_tooltip_set(but_icon,
                            extra_info_row.tooltip_fn,
                            extra_info_row.tooltip_fn_arg,
                            extra_info_row.tooltip_fn_free_arg);
  }
  UI_block_emboss_set(&block, UI_EMBOSS);

  const float but_text_left = but_icon_right + 6.0f * UI_SCALE_FAC;
  const float but_text_right = rect.xmax;
  const float but_text_width = but_text_right - but_text_left;

  uiBut *but_text = uiDefBut(&block,
                             UI_BTYPE_LABEL,
                             0,
                             extra_info_row.text.c_str(),
                             int(but_text_left),
                             int(rect.ymin + row * (20.0f * UI_SCALE_FAC)),
                             short(but_text_width),
                             short(NODE_DY),
                             nullptr,
                             0,
                             0,
                             0,
                             0,
                             "");

  if (node.flag & NODE_MUTED) {
    UI_but_flag_enable(but_text, UI_BUT_INACTIVE);
    UI_but_flag_enable(but_icon, UI_BUT_INACTIVE);
  }
}

static void node_draw_extra_info_panel_back(const bNode &node, const rctf &extra_info_rect)
{
  const rctf &node_rect = node.runtime->totr;
  rctf panel_back_rect = extra_info_rect;
  /* Extend the panel behind hidden nodes to accommodate the large rounded corners. */
  if (node.flag & NODE_HIDDEN) {
    panel_back_rect.ymin = BLI_rctf_cent_y(&node_rect);
  }

  ColorTheme4f color;
  if (node.flag & NODE_MUTED) {
    UI_GetThemeColorBlend4f(TH_BACK, TH_NODE, 0.2f, color);
  }
  else {
    UI_GetThemeColorBlend4f(TH_BACK, TH_NODE, 0.75f, color);
  }
  color.a -= 0.35f;

  ColorTheme4f color_outline;
  UI_GetThemeColorBlendShade4fv(TH_BACK, TH_NODE, 0.4f, -20, color_outline);

  const float outline_width = U.pixelsize;
  BLI_rctf_pad(&panel_back_rect, outline_width, outline_width);

  UI_draw_roundbox_corner_set(UI_CNR_TOP_LEFT | UI_CNR_TOP_RIGHT);
  UI_draw_roundbox_4fv_ex(
      &panel_back_rect, color, nullptr, 0.0f, color_outline, outline_width, BASIS_RAD);
}

static void node_draw_extra_info_panel(const Scene *scene,
                                       TreeDrawContext &tree_draw_ctx,
                                       const SpaceNode &snode,
                                       const bNode &node,
                                       ImBuf *preview,
                                       uiBlock &block)
{
  if (!(snode.overlay.flag & SN_OVERLAY_SHOW_OVERLAYS)) {
    return;
  }
  if (preview && !(preview->x > 0 && preview->y > 0)) {
    /* If the preview has an non-drawable size, just don't draw it. */
    preview = nullptr;
  }
  Vector<NodeExtraInfoRow> extra_info_rows = node_get_extra_info(tree_draw_ctx, snode, node);
  if (extra_info_rows.size() == 0 && !preview) {
    return;
  }

  const rctf &rct = node.runtime->totr;
  rctf extra_info_rect;

  if (node.is_frame()) {
    extra_info_rect.xmin = rct.xmin;
    extra_info_rect.xmax = rct.xmin + 95.0f * UI_SCALE_FAC;
    extra_info_rect.ymin = rct.ymin + 2.0f * UI_SCALE_FAC;
    extra_info_rect.ymax = rct.ymin + 2.0f * UI_SCALE_FAC;
  }
  else {
    const float padding = 3.0f * UI_SCALE_FAC;

    extra_info_rect.xmin = rct.xmin + padding;
    extra_info_rect.xmax = rct.xmax - padding;
    extra_info_rect.ymin = rct.ymax;
    extra_info_rect.ymax = rct.ymax + extra_info_rows.size() * (20.0f * UI_SCALE_FAC);

    float preview_height = 0.0f;
    rctf preview_rect;
    if (preview) {
      const float width = BLI_rctf_size_x(&extra_info_rect);
      if (preview->x > preview->y) {
        preview_height = (width - 2.0f * padding) * float(preview->y) / float(preview->x) +
                         2.0f * padding;
        preview_rect.ymin = extra_info_rect.ymin + padding;
        preview_rect.ymax = extra_info_rect.ymin + preview_height - padding;
        preview_rect.xmin = extra_info_rect.xmin + padding;
        preview_rect.xmax = extra_info_rect.xmax - padding;
        extra_info_rect.ymax += preview_height;
      }
      else {
        preview_height = width;
        const float preview_width = (width - 2.0f * padding) * float(preview->x) /
                                        float(preview->y) +
                                    2.0f * padding;
        preview_rect.ymin = extra_info_rect.ymin + padding;
        preview_rect.ymax = extra_info_rect.ymin + preview_height - padding;
        preview_rect.xmin = extra_info_rect.xmin + padding + (width - preview_width) / 2;
        preview_rect.xmax = extra_info_rect.xmax - padding - (width - preview_width) / 2;
        extra_info_rect.ymax += preview_height;
      }
    }

    node_draw_extra_info_panel_back(node, extra_info_rect);

    if (preview) {
      node_draw_preview(scene, preview, &preview_rect);
    }

    /* Resize the rect to draw the textual infos on top of the preview. */
    extra_info_rect.ymin += preview_height;
  }

  for (int row : extra_info_rows.index_range()) {
    node_draw_extra_info_row(node, block, extra_info_rect, row, extra_info_rows[row]);
  }
}

static void node_draw_basis(const bContext &C,
                            TreeDrawContext &tree_draw_ctx,
                            const View2D &v2d,
                            const SpaceNode &snode,
                            bNodeTree &ntree,
                            const bNode &node,
                            uiBlock &block,
                            bNodeInstanceKey key)
{
  const float iconbutw = NODE_HEADER_ICON_SIZE;
  const bool show_preview = (snode.overlay.flag & SN_OVERLAY_SHOW_OVERLAYS) &&
                            (snode.overlay.flag & SN_OVERLAY_SHOW_PREVIEWS) &&
                            (node.flag & NODE_PREVIEW) &&
                            (U.experimental.use_shader_node_previews ||
                             ntree.type != NTREE_SHADER);

  /* Skip if out of view. */
  rctf rect_with_preview = node.runtime->totr;
  if (show_preview) {
    rect_with_preview.ymax += NODE_WIDTH(node);
  }
  if (BLI_rctf_isect(&rect_with_preview, &v2d.cur, nullptr) == false) {
    UI_block_end(&C, &block);
    return;
  }

  /* Shadow. */
  if (!bke::all_zone_node_types().contains(node.type)) {
    node_draw_shadow(snode, node, BASIS_RAD, 1.0f);
  }

  const rctf &rct = node.runtime->totr;
  float color[4];
  int color_id = node_get_colorid(tree_draw_ctx, node);

  GPU_line_width(1.0f);

  /* Overlay atop the node. */
  {
    bool drawn_with_previews = false;

    if (show_preview) {
      bNodeInstanceHash *previews_compo = static_cast<bNodeInstanceHash *>(
          CTX_data_pointer_get(&C, "node_previews").data);
      NestedTreePreviews *previews_shader = tree_draw_ctx.nested_group_infos;

      if (previews_shader) {
        ImBuf *preview = node_preview_acquire_ibuf(ntree, *previews_shader, node);
        node_draw_extra_info_panel(CTX_data_scene(&C), tree_draw_ctx, snode, node, preview, block);
        node_release_preview_ibuf(*previews_shader);
        drawn_with_previews = true;
      }
      else if (previews_compo) {
        bNodePreview *preview_compositor = static_cast<bNodePreview *>(
            BKE_node_instance_hash_lookup(previews_compo, key));
        if (preview_compositor) {
          node_draw_extra_info_panel(
              CTX_data_scene(&C), tree_draw_ctx, snode, node, preview_compositor->ibuf, block);
          drawn_with_previews = true;
        }
      }
    }

    if (drawn_with_previews == false) {
      node_draw_extra_info_panel(CTX_data_scene(&C), tree_draw_ctx, snode, node, nullptr, block);
    }
  }

  /* Header. */
  {
    const rctf rect = {
        rct.xmin,
        rct.xmax,
        rct.ymax - NODE_DY,
        rct.ymax,
    };

    float color_header[4];

    /* Muted nodes get a mix of the background with the node color. */
    if (node.flag & NODE_MUTED) {
      UI_GetThemeColorBlend4f(TH_BACK, color_id, 0.1f, color_header);
    }
    else {
      UI_GetThemeColorBlend4f(TH_NODE, color_id, 0.4f, color_header);
    }

    UI_draw_roundbox_corner_set(UI_CNR_TOP_LEFT | UI_CNR_TOP_RIGHT);
    UI_draw_roundbox_4fv(&rect, true, BASIS_RAD, color_header);
  }

  /* Show/hide icons. */
  float iconofs = rct.xmax - 0.35f * U.widget_unit;

  /* Group edit. This icon should be the first for the node groups. */
  if (node.type == NODE_GROUP) {
    iconofs -= iconbutw;
    UI_block_emboss_set(&block, UI_EMBOSS_NONE);
    uiBut *but = uiDefIconBut(&block,
                              UI_BTYPE_BUT_TOGGLE,
                              0,
                              ICON_NODETREE,
                              iconofs,
                              rct.ymax - NODE_DY,
                              iconbutw,
                              UI_UNIT_Y,
                              nullptr,
                              0,
                              0,
                              0,
                              0,
                              "");
    UI_but_func_set(but,
                    node_toggle_button_cb,
                    POINTER_FROM_INT(node.identifier),
                    (void *)"NODE_OT_group_edit");
    if (node.id) {
      UI_but_icon_indicator_number_set(but, ID_REAL_USERS(node.id));
    }
    UI_block_emboss_set(&block, UI_EMBOSS);
  }
  /* Preview. */
  if (node_is_previewable(snode, ntree, node)) {
    iconofs -= iconbutw;
    UI_block_emboss_set(&block, UI_EMBOSS_NONE);
    uiBut *but = uiDefIconBut(&block,
                              UI_BTYPE_BUT_TOGGLE,
                              0,
                              ICON_MATERIAL,
                              iconofs,
                              rct.ymax - NODE_DY,
                              iconbutw,
                              UI_UNIT_Y,
                              nullptr,
                              0,
                              0,
                              0,
                              0,
                              "");
    UI_but_func_set(but,
                    node_toggle_button_cb,
                    POINTER_FROM_INT(node.identifier),
                    (void *)"NODE_OT_preview_toggle");
    UI_block_emboss_set(&block, UI_EMBOSS);
  }
  if (node.type == NODE_CUSTOM && node.typeinfo->ui_icon != ICON_NONE) {
    iconofs -= iconbutw;
    UI_block_emboss_set(&block, UI_EMBOSS_NONE);
    uiDefIconBut(&block,
                 UI_BTYPE_BUT,
                 0,
                 node.typeinfo->ui_icon,
                 iconofs,
                 rct.ymax - NODE_DY,
                 iconbutw,
                 UI_UNIT_Y,
                 nullptr,
                 0,
                 0,
                 0,
                 0,
                 "");
    UI_block_emboss_set(&block, UI_EMBOSS);
  }
  if (node.type == GEO_NODE_VIEWER) {
    const bool is_active = &node == tree_draw_ctx.active_geometry_nodes_viewer;
    iconofs -= iconbutw;
    UI_block_emboss_set(&block, UI_EMBOSS_NONE);
    uiBut *but = uiDefIconBut(&block,
                              UI_BTYPE_BUT,
                              0,
                              is_active ? ICON_HIDE_OFF : ICON_HIDE_ON,
                              iconofs,
                              rct.ymax - NODE_DY,
                              iconbutw,
                              UI_UNIT_Y,
                              nullptr,
                              0,
                              0,
                              0,
                              0,
                              "");
    /* Selection implicitly activates the node. */
    const char *operator_idname = is_active ? "NODE_OT_deactivate_viewer" : "NODE_OT_select";
    UI_but_func_set(
        but, node_toggle_button_cb, POINTER_FROM_INT(node.identifier), (void *)operator_idname);
    UI_block_emboss_set(&block, UI_EMBOSS);
  }

  node_add_error_message_button(tree_draw_ctx, node, block, rct, iconofs);

  /* Title. */
  if (node.flag & SELECT) {
    UI_GetThemeColor4fv(TH_SELECT, color);
  }
  else {
    UI_GetThemeColorBlendShade4fv(TH_SELECT, color_id, 0.4f, 10, color);
  }

  /* Collapse/expand icon. */
  {
    const int but_size = U.widget_unit * 0.8f;
    UI_block_emboss_set(&block, UI_EMBOSS_NONE);

    uiBut *but = uiDefIconBut(&block,
                              UI_BTYPE_BUT_TOGGLE,
                              0,
                              ICON_DOWNARROW_HLT,
                              rct.xmin + (NODE_MARGIN_X / 3),
                              rct.ymax - NODE_DY / 2.2f - but_size / 2,
                              but_size,
                              but_size,
                              nullptr,
                              0.0f,
                              0.0f,
                              0.0f,
                              0.0f,
                              "");

    UI_but_func_set(but,
                    node_toggle_button_cb,
                    POINTER_FROM_INT(node.identifier),
                    (void *)"NODE_OT_hide_toggle");
    UI_block_emboss_set(&block, UI_EMBOSS);
  }

  char showname[128];
  bke::nodeLabel(&ntree, &node, showname, sizeof(showname));

  uiBut *but = uiDefBut(&block,
                        UI_BTYPE_LABEL,
                        0,
                        showname,
                        int(rct.xmin + NODE_MARGIN_X + 0.4f),
                        int(rct.ymax - NODE_DY),
                        short(iconofs - rct.xmin - (18.0f * UI_SCALE_FAC)),
                        short(NODE_DY),
                        nullptr,
                        0,
                        0,
                        0,
                        0,
                        "");
  if (node.flag & NODE_MUTED) {
    UI_but_flag_enable(but, UI_BUT_INACTIVE);
  }

  /* Wire across the node when muted/disabled. */
  if (node.flag & NODE_MUTED) {
    node_draw_mute_line(C, v2d, snode, node);
  }

  /* Body. */
  const float outline_width = 1.0f;
  {
    /* Use warning color to indicate undefined types. */
    if (bke::node_type_is_undefined(&node)) {
      UI_GetThemeColorBlend4f(TH_REDALERT, TH_NODE, 0.4f, color);
    }
    /* Muted nodes get a mix of the background with the node color. */
    else if (node.flag & NODE_MUTED) {
      UI_GetThemeColorBlend4f(TH_BACK, TH_NODE, 0.2f, color);
    }
    else if (node.flag & NODE_CUSTOM_COLOR) {
      rgba_float_args_set(color, node.color[0], node.color[1], node.color[2], 1.0f);
    }
    else {
      UI_GetThemeColor4fv(TH_NODE, color);
    }

    /* Draw selected nodes fully opaque. */
    if (node.flag & SELECT) {
      color[3] = 1.0f;
    }

    /* Draw muted nodes slightly transparent so the wires inside are visible. */
    if (node.flag & NODE_MUTED) {
      color[3] -= 0.2f;
    }

    const rctf rect = {
        rct.xmin,
        rct.xmax,
        rct.ymin,
        rct.ymax - (NODE_DY + outline_width),
    };

    UI_draw_roundbox_corner_set(UI_CNR_BOTTOM_LEFT | UI_CNR_BOTTOM_RIGHT);
    UI_draw_roundbox_4fv(&rect, true, BASIS_RAD, color);

    if (is_node_panels_supported(node)) {
      node_draw_panels_background(node, block);
    }
  }

  /* Header underline. */
  {
    float color_underline[4];

    if (node.flag & NODE_MUTED) {
      UI_GetThemeColor4fv(TH_WIRE, color_underline);
      color_underline[3] = 1.0f;
    }
    else {
      UI_GetThemeColorBlend4f(TH_BACK, color_id, 0.2f, color_underline);
    }

    const rctf rect = {
        rct.xmin,
        rct.xmax,
        rct.ymax - (NODE_DY + outline_width),
        rct.ymax - NODE_DY,
    };

    UI_draw_roundbox_corner_set(UI_CNR_NONE);
    UI_draw_roundbox_4fv(&rect, true, 0.0f, color_underline);
  }

  /* Outline. */
  {
    const rctf rect = {
        rct.xmin - outline_width,
        rct.xmax + outline_width,
        rct.ymin - outline_width,
        rct.ymax + outline_width,
    };

    /* Color the outline according to active, selected, or undefined status. */
    float color_outline[4];

    if (node.flag & SELECT) {
      UI_GetThemeColor4fv((node.flag & NODE_ACTIVE) ? TH_ACTIVE : TH_SELECT, color_outline);
    }
    else if (bke::node_type_is_undefined(&node)) {
      UI_GetThemeColor4fv(TH_REDALERT, color_outline);
    }
    else if (const bke::bNodeZoneType *zone_type = bke::zone_type_by_node_type(node.type)) {
      UI_GetThemeColor4fv(zone_type->theme_id, color_outline);
      color_outline[3] = 1.0f;
    }
    else {
      UI_GetThemeColorBlendShade4fv(TH_BACK, TH_NODE, 0.4f, -20, color_outline);
    }

    UI_draw_roundbox_corner_set(UI_CNR_ALL);
    UI_draw_roundbox_4fv(&rect, false, BASIS_RAD + outline_width, color_outline);
  }

  float scale;
  UI_view2d_scale_get(&v2d, &scale, nullptr);

  /* Skip slow socket drawing if zoom is small. */
  if (scale > 0.2f) {
    node_draw_sockets(v2d, C, ntree, node, block, true, false);
  }

  if (is_node_panels_supported(node)) {
    node_draw_panels(ntree, node, block);
  }

  UI_block_end(&C, &block);
  UI_block_draw(&C, &block);
}

static void node_draw_hidden(const bContext &C,
                             TreeDrawContext &tree_draw_ctx,
                             const View2D &v2d,
                             const SpaceNode &snode,
                             bNodeTree &ntree,
                             bNode &node,
                             uiBlock &block)
{
  const rctf &rct = node.runtime->totr;
  float centy = BLI_rctf_cent_y(&rct);
  float hiddenrad = BLI_rctf_size_y(&rct) / 2.0f;

  float scale;
  UI_view2d_scale_get(&v2d, &scale, nullptr);

  const int color_id = node_get_colorid(tree_draw_ctx, node);

  node_draw_extra_info_panel(nullptr, tree_draw_ctx, snode, node, nullptr, block);

  /* Shadow. */
  node_draw_shadow(snode, node, hiddenrad, 1.0f);

  /* Wire across the node when muted/disabled. */
  if (node.flag & NODE_MUTED) {
    node_draw_mute_line(C, v2d, snode, node);
  }

  /* Body. */
  float color[4];
  {
    if (bke::node_type_is_undefined(&node)) {
      /* Use warning color to indicate undefined types. */
      UI_GetThemeColorBlend4f(TH_REDALERT, TH_NODE, 0.4f, color);
    }
    else if (node.flag & NODE_MUTED) {
      /* Muted nodes get a mix of the background with the node color. */
      UI_GetThemeColorBlendShade4fv(TH_BACK, color_id, 0.1f, 0, color);
    }
    else if (node.flag & NODE_CUSTOM_COLOR) {
      rgba_float_args_set(color, node.color[0], node.color[1], node.color[2], 1.0f);
    }
    else {
      UI_GetThemeColorBlend4f(TH_NODE, color_id, 0.4f, color);
    }

    /* Draw selected nodes fully opaque. */
    if (node.flag & SELECT) {
      color[3] = 1.0f;
    }

    /* Draw muted nodes slightly transparent so the wires inside are visible. */
    if (node.flag & NODE_MUTED) {
      color[3] -= 0.2f;
    }

    UI_draw_roundbox_4fv(&rct, true, hiddenrad, color);
  }

  /* Title. */
  if (node.flag & SELECT) {
    UI_GetThemeColor4fv(TH_SELECT, color);
  }
  else {
    UI_GetThemeColorBlendShade4fv(TH_SELECT, color_id, 0.4f, 10, color);
  }

  /* Collapse/expand icon. */
  {
    const int but_size = U.widget_unit * 1.0f;
    UI_block_emboss_set(&block, UI_EMBOSS_NONE);

    uiBut *but = uiDefIconBut(&block,
                              UI_BTYPE_BUT_TOGGLE,
                              0,
                              ICON_RIGHTARROW,
                              rct.xmin + (NODE_MARGIN_X / 3),
                              centy - but_size / 2,
                              but_size,
                              but_size,
                              nullptr,
                              0.0f,
                              0.0f,
                              0.0f,
                              0.0f,
                              "");

    UI_but_func_set(but,
                    node_toggle_button_cb,
                    POINTER_FROM_INT(node.identifier),
                    (void *)"NODE_OT_hide_toggle");
    UI_block_emboss_set(&block, UI_EMBOSS);
  }

  char showname[128];
  bke::nodeLabel(&ntree, &node, showname, sizeof(showname));

  uiBut *but = uiDefBut(&block,
                        UI_BTYPE_LABEL,
                        0,
                        showname,
                        round_fl_to_int(rct.xmin + NODE_MARGIN_X),
                        round_fl_to_int(centy - NODE_DY * 0.5f),
                        short(BLI_rctf_size_x(&rct) - ((18.0f + 12.0f) * UI_SCALE_FAC)),
                        short(NODE_DY),
                        nullptr,
                        0,
                        0,
                        0,
                        0,
                        "");

  /* Outline. */
  {
    const float outline_width = 1.0f;
    const rctf rect = {
        rct.xmin - outline_width,
        rct.xmax + outline_width,
        rct.ymin - outline_width,
        rct.ymax + outline_width,
    };

    /* Color the outline according to active, selected, or undefined status. */
    float color_outline[4];

    if (node.flag & SELECT) {
      UI_GetThemeColor4fv((node.flag & NODE_ACTIVE) ? TH_ACTIVE : TH_SELECT, color_outline);
    }
    else if (bke::node_type_is_undefined(&node)) {
      UI_GetThemeColor4fv(TH_REDALERT, color_outline);
    }
    else {
      UI_GetThemeColorBlendShade4fv(TH_BACK, TH_NODE, 0.4f, -20, color_outline);
    }

    UI_draw_roundbox_corner_set(UI_CNR_ALL);
    UI_draw_roundbox_4fv(&rect, false, hiddenrad, color_outline);
  }

  if (node.flag & NODE_MUTED) {
    UI_but_flag_enable(but, UI_BUT_INACTIVE);
  }

  /* Scale widget thing. */
  uint pos = GPU_vertformat_attr_add(immVertexFormat(), "pos", GPU_COMP_F32, 2, GPU_FETCH_FLOAT);
  GPU_blend(GPU_BLEND_ALPHA);
  immBindBuiltinProgram(GPU_SHADER_3D_UNIFORM_COLOR);

  immUniformThemeColorShadeAlpha(TH_TEXT, -40, -180);
  float dx = 0.5f * U.widget_unit;
  const float dx2 = 0.15f * U.widget_unit * snode.runtime->aspect;
  const float dy = 0.2f * U.widget_unit;

  immBegin(GPU_PRIM_LINES, 4);
  immVertex2f(pos, rct.xmax - dx, centy - dy);
  immVertex2f(pos, rct.xmax - dx, centy + dy);

  immVertex2f(pos, rct.xmax - dx - dx2, centy - dy);
  immVertex2f(pos, rct.xmax - dx - dx2, centy + dy);
  immEnd();

  immUniformThemeColorShadeAlpha(TH_TEXT, 0, -180);
  dx -= snode.runtime->aspect;

  immBegin(GPU_PRIM_LINES, 4);
  immVertex2f(pos, rct.xmax - dx, centy - dy);
  immVertex2f(pos, rct.xmax - dx, centy + dy);

  immVertex2f(pos, rct.xmax - dx - dx2, centy - dy);
  immVertex2f(pos, rct.xmax - dx - dx2, centy + dy);
  immEnd();

  immUnbindProgram();
  GPU_blend(GPU_BLEND_NONE);

  node_draw_sockets(v2d, C, ntree, node, block, true, false);

  UI_block_end(&C, &block);
  UI_block_draw(&C, &block);
}

int node_get_resize_cursor(NodeResizeDirection directions)
{
  if (directions == 0) {
    return WM_CURSOR_DEFAULT;
  }
  if ((directions & ~(NODE_RESIZE_TOP | NODE_RESIZE_BOTTOM)) == 0) {
    return WM_CURSOR_Y_MOVE;
  }
  if ((directions & ~(NODE_RESIZE_RIGHT | NODE_RESIZE_LEFT)) == 0) {
    return WM_CURSOR_X_MOVE;
  }
  return WM_CURSOR_EDIT;
}

static const bNode *find_node_under_cursor(SpaceNode &snode, const float2 &cursor)
{
  for (const bNode *node : tree_draw_order_calc_nodes_reversed(*snode.edittree)) {
    if (BLI_rctf_isect_pt(&node->runtime->totr, cursor[0], cursor[1])) {
      return node;
    }
  }
  return nullptr;
}

void node_set_cursor(wmWindow &win, SpaceNode &snode, const float2 &cursor)
{
  const bNodeTree *ntree = snode.edittree;
  if (ntree == nullptr) {
    WM_cursor_set(&win, WM_CURSOR_DEFAULT);
    return;
  }
  if (node_find_indicated_socket(snode, cursor, SOCK_IN | SOCK_OUT)) {
    WM_cursor_set(&win, WM_CURSOR_DEFAULT);
    return;
  }
  const bNode *node = find_node_under_cursor(snode, cursor);
  if (!node) {
    WM_cursor_set(&win, WM_CURSOR_DEFAULT);
    return;
  }
  const NodeResizeDirection dir = node_get_resize_direction(snode, node, cursor[0], cursor[1]);
  if (node->is_frame() && dir == NODE_RESIZE_NONE) {
    /* Indicate that frame nodes can be moved/selected on their borders. */
    const rctf frame_inside = node_frame_rect_inside(snode, *node);
    if (!BLI_rctf_isect_pt(&frame_inside, cursor[0], cursor[1])) {
      WM_cursor_set(&win, WM_CURSOR_NSEW_SCROLL);
      return;
    }
    WM_cursor_set(&win, WM_CURSOR_DEFAULT);
    return;
  }

  WM_cursor_set(&win, node_get_resize_cursor(dir));
}

static void count_multi_input_socket_links(bNodeTree &ntree, SpaceNode &snode)
{
  for (bNode *node : ntree.all_nodes()) {
    for (bNodeSocket *socket : node->input_sockets()) {
      if (socket->is_multi_input()) {
        socket->runtime->total_inputs = socket->directly_linked_links().size();
      }
    }
  }
  /* Count temporary links going into this socket. */
  if (snode.runtime->linkdrag) {
    for (const bNodeLink &link : snode.runtime->linkdrag->links) {
      if (link.tosock && (link.tosock->flag & SOCK_MULTI_INPUT)) {
        link.tosock->runtime->total_inputs++;
      }
    }
  }
}

static float frame_node_label_height(const NodeFrame &frame_data)
{
  return frame_data.label_size * UI_SCALE_FAC;
}

#define NODE_FRAME_MARGIN (1.5f * U.widget_unit)

/* XXX Does a bounding box update by iterating over all children.
 * Not ideal to do this in every draw call, but doing as transform callback doesn't work,
 * since the child node totr rects are not updated properly at that point. */
static void frame_node_prepare_for_draw(bNode &node, Span<bNode *> nodes)
{
  NodeFrame *data = (NodeFrame *)node.storage;

  const float margin = NODE_FRAME_MARGIN;
  const float has_label = node.label[0] != '\0';

  const float label_height = frame_node_label_height(*data);
  /* Add an additional 25% to account for the glyphs descender.
   * This works well in most cases. */
  const float margin_top = 0.5f * margin + (has_label ? 1.25f * label_height : 0.5f * margin);

  /* Initialize rect from current frame size. */
  rctf rect;
  node_to_updated_rect(node, rect);

  /* Frame can be resized manually only if shrinking is disabled or no children are attached. */
  data->flag |= NODE_FRAME_RESIZEABLE;
  /* For shrinking bounding box, initialize the rect from first child node. */
  bool bbinit = (data->flag & NODE_FRAME_SHRINK);
  /* Fit bounding box to all children. */
  for (const bNode *tnode : nodes) {
    if (tnode->parent != &node) {
      continue;
    }

    /* Add margin to node rect. */
    rctf noderect = tnode->runtime->totr;
    noderect.xmin -= margin;
    noderect.xmax += margin;
    noderect.ymin -= margin;
    noderect.ymax += margin_top;

    /* First child initializes frame. */
    if (bbinit) {
      bbinit = false;
      rect = noderect;
      data->flag &= ~NODE_FRAME_RESIZEABLE;
    }
    else {
      BLI_rctf_union(&rect, &noderect);
    }
  }

  /* Now adjust the frame size from view-space bounding box. */
  const float2 offset = node_from_view(node, {rect.xmin, rect.ymax});
  node.offsetx = offset.x;
  node.offsety = offset.y;
  const float2 max = node_from_view(node, {rect.xmax, rect.ymin});
  node.width = max.x - node.offsetx;
  node.height = -max.y + node.offsety;

  node.runtime->totr = rect;
}

static void reroute_node_prepare_for_draw(bNode &node)
{
  const float2 loc = node_to_view(node, float2(0));

  /* Reroute node has exactly one input and one output, both in the same place. */
  node.input_socket(0).runtime->location = loc;
  node.output_socket(0).runtime->location = loc;

  const float size = 8.0f;
  node.width = size * 2;
  node.runtime->totr.xmin = loc.x - size;
  node.runtime->totr.xmax = loc.x + size;
  node.runtime->totr.ymax = loc.y + size;
  node.runtime->totr.ymin = loc.y - size;
}

static void node_update_nodetree(const bContext &C,
                                 TreeDrawContext &tree_draw_ctx,
                                 bNodeTree &ntree,
                                 Span<bNode *> nodes,
                                 Span<uiBlock *> blocks)
{
  /* Make sure socket "used" tags are correct, for displaying value buttons. */
  SpaceNode *snode = CTX_wm_space_node(&C);

  count_multi_input_socket_links(ntree, *snode);

  for (const int i : nodes.index_range()) {
    bNode &node = *nodes[i];
    uiBlock &block = *blocks[i];
    if (node.is_frame()) {
      /* Frame sizes are calculated after all other nodes have calculating their #totr. */
      continue;
    }

    if (node.is_reroute()) {
      reroute_node_prepare_for_draw(node);
    }
    else {
      if (node.flag & NODE_HIDDEN) {
        node_update_hidden(node, block);
      }
      else {
        node_update_basis(C, tree_draw_ctx, ntree, node, block);
      }
    }
  }

  /* Now calculate the size of frame nodes, which can depend on the size of other nodes.
   * Update nodes in reverse, so children sizes get updated before parents. */
  for (int i = nodes.size() - 1; i >= 0; i--) {
    if (nodes[i]->is_frame()) {
      frame_node_prepare_for_draw(*nodes[i], nodes);
    }
  }
}

static void frame_node_draw_label(TreeDrawContext &tree_draw_ctx,
                                  const bNodeTree &ntree,
                                  const bNode &node,
                                  const SpaceNode &snode)
{
  const float aspect = snode.runtime->aspect;
  /* XXX font id is crap design */
  const int fontid = UI_style_get()->widgetlabel.uifont_id;
  const NodeFrame *data = (const NodeFrame *)node.storage;
  const float font_size = data->label_size / aspect;

  char label[MAX_NAME];
  bke::nodeLabel(&ntree, &node, label, sizeof(label));

  BLF_enable(fontid, BLF_ASPECT);
  BLF_aspect(fontid, aspect, aspect, 1.0f);
  BLF_size(fontid, font_size * UI_SCALE_FAC);

  /* Title color. */
  int color_id = node_get_colorid(tree_draw_ctx, node);
  uchar color[3];
  UI_GetThemeColorBlendShade3ubv(TH_TEXT, color_id, 0.4f, 10, color);
  BLF_color3ubv(fontid, color);

  const float margin = NODE_FRAME_MARGIN;
  const float width = BLF_width(fontid, label, sizeof(label));
  const int label_height = frame_node_label_height(*data);

  const rctf &rct = node.runtime->totr;
  const float label_x = BLI_rctf_cent_x(&rct) - (0.5f * width);
  const float label_y = rct.ymax - label_height - (0.5f * margin);

  /* Label. */
  const bool has_label = node.label[0] != '\0';
  if (has_label) {
    BLF_position(fontid, label_x, label_y, 0);
    BLF_draw(fontid, label, sizeof(label));
  }

  /* Draw text body. */
  if (node.id) {
    const Text *text = (const Text *)node.id;
    const int line_height_max = BLF_height_max(fontid);
    const float line_spacing = (line_height_max * aspect);
    const float line_width = (BLI_rctf_size_x(&rct) - 2 * margin) / aspect;

    const float x = rct.xmin + margin;
    float y = rct.ymax - label_height - (has_label ? line_spacing + margin : 0);

    const int y_min = rct.ymin + margin;

    BLF_enable(fontid, BLF_CLIPPING | BLF_WORD_WRAP);
    BLF_clipping(fontid, rct.xmin, rct.ymin + margin, rct.xmax, rct.ymax);

    BLF_wordwrap(fontid, line_width);

    LISTBASE_FOREACH (const TextLine *, line, &text->lines) {
      if (line->line[0]) {
        BLF_position(fontid, x, y, 0);
        ResultBLF info;
        BLF_draw_ex(fontid, line->line, line->len, &info);
        y -= line_spacing * info.lines;
      }
      else {
        y -= line_spacing;
      }
      if (y < y_min) {
        break;
      }
    }

    BLF_disable(fontid, BLF_CLIPPING | BLF_WORD_WRAP);
  }

  BLF_disable(fontid, BLF_ASPECT);
}

static void frame_node_draw(const bContext &C,
                            TreeDrawContext &tree_draw_ctx,
                            const ARegion &region,
                            const SpaceNode &snode,
                            bNodeTree &ntree,
                            bNode &node,
                            uiBlock &block)
{
  /* Skip if out of view. */
  if (BLI_rctf_isect(&node.runtime->totr, &region.v2d.cur, nullptr) == false) {
    UI_block_end(&C, &block);
    return;
  }

  float color[4];
  UI_GetThemeColor4fv(TH_NODE_FRAME, color);
  const float alpha = color[3];

  node_draw_shadow(snode, node, BASIS_RAD, alpha);

  if (node.flag & NODE_CUSTOM_COLOR) {
    rgba_float_args_set(color, node.color[0], node.color[1], node.color[2], alpha);
  }
  else {
    UI_GetThemeColor4fv(TH_NODE_FRAME, color);
  }

  const rctf &rct = node.runtime->totr;
  UI_draw_roundbox_corner_set(UI_CNR_ALL);
  UI_draw_roundbox_4fv(&rct, true, BASIS_RAD, color);

  /* Outline active and selected emphasis. */
  if (node.flag & SELECT) {
    if (node.flag & NODE_ACTIVE) {
      UI_GetThemeColorShadeAlpha4fv(TH_ACTIVE, 0, -40, color);
    }
    else {
      UI_GetThemeColorShadeAlpha4fv(TH_SELECT, 0, -40, color);
    }

    UI_draw_roundbox_aa(&rct, false, BASIS_RAD, color);
  }

  /* Label and text. */
  frame_node_draw_label(tree_draw_ctx, ntree, node, snode);

  node_draw_extra_info_panel(nullptr, tree_draw_ctx, snode, node, nullptr, block);

  UI_block_end(&C, &block);
  UI_block_draw(&C, &block);
}

static void reroute_node_draw(
    const bContext &C, ARegion &region, bNodeTree &ntree, const bNode &node, uiBlock &block)
{
  /* Skip if out of view. */
  const rctf &rct = node.runtime->totr;
  if (rct.xmax < region.v2d.cur.xmin || rct.xmin > region.v2d.cur.xmax ||
      rct.ymax < region.v2d.cur.ymin || node.runtime->totr.ymin > region.v2d.cur.ymax)
  {
    UI_block_end(&C, &block);
    return;
  }

  if (node.label[0] != '\0') {
    /* Draw title (node label). */
    char showname[128]; /* 128 used below */
    STRNCPY(showname, node.label);
    const short width = 512;
    const int x = BLI_rctf_cent_x(&node.runtime->totr) - (width / 2);
    const int y = node.runtime->totr.ymax;

    uiBut *label_but = uiDefBut(&block,
                                UI_BTYPE_LABEL,
                                0,
                                showname,
                                x,
                                y,
                                width,
                                short(NODE_DY),
                                nullptr,
                                0,
                                0,
                                0,
                                0,
                                nullptr);

    UI_but_drawflag_disable(label_but, UI_BUT_TEXT_LEFT);
  }

  /* Only draw input socket as they all are placed on the same position highlight
   * if node itself is selected, since we don't display the node body separately. */
  node_draw_sockets(region.v2d, C, ntree, node, block, false, node.flag & SELECT);

  UI_block_end(&C, &block);
  UI_block_draw(&C, &block);
}

static void node_draw(const bContext &C,
                      TreeDrawContext &tree_draw_ctx,
                      ARegion &region,
                      const SpaceNode &snode,
                      bNodeTree &ntree,
                      bNode &node,
                      uiBlock &block,
                      bNodeInstanceKey key)
{
  if (node.is_frame()) {
    frame_node_draw(C, tree_draw_ctx, region, snode, ntree, node, block);
  }
  else if (node.is_reroute()) {
    reroute_node_draw(C, region, ntree, node, block);
  }
  else {
    const View2D &v2d = region.v2d;
    if (node.flag & NODE_HIDDEN) {
      node_draw_hidden(C, tree_draw_ctx, v2d, snode, ntree, node, block);
    }
    else {
      node_draw_basis(C, tree_draw_ctx, v2d, snode, ntree, node, block, key);
    }
  }
}

static void add_rect_corner_positions(Vector<float2> &positions, const rctf &rect)
{
  positions.append({rect.xmin, rect.ymin});
  positions.append({rect.xmin, rect.ymax});
  positions.append({rect.xmax, rect.ymin});
  positions.append({rect.xmax, rect.ymax});
}

static void find_bounds_by_zone_recursive(const SpaceNode &snode,
                                          const bNodeTreeZone &zone,
                                          const Span<std::unique_ptr<bNodeTreeZone>> all_zones,
                                          MutableSpan<Vector<float2>> r_bounds_by_zone)
{
  const float node_padding = UI_UNIT_X;
  const float zone_padding = 0.3f * UI_UNIT_X;

  Vector<float2> &bounds = r_bounds_by_zone[zone.index];
  if (!bounds.is_empty()) {
    return;
  }

  Vector<float2> possible_bounds;
  for (const bNodeTreeZone *child_zone : zone.child_zones) {
    find_bounds_by_zone_recursive(snode, *child_zone, all_zones, r_bounds_by_zone);
    const Span<float2> child_bounds = r_bounds_by_zone[child_zone->index];
    for (const float2 &pos : child_bounds) {
      rctf rect;
      BLI_rctf_init_pt_radius(&rect, pos, zone_padding);
      add_rect_corner_positions(possible_bounds, rect);
    }
  }
  for (const bNode *child_node : zone.child_nodes) {
    rctf rect = child_node->runtime->totr;
    BLI_rctf_pad(&rect, node_padding, node_padding);
    add_rect_corner_positions(possible_bounds, rect);
  }
  if (zone.input_node) {
    const rctf &totr = zone.input_node->runtime->totr;
    rctf rect = totr;
    BLI_rctf_pad(&rect, node_padding, node_padding);
    rect.xmin = math::interpolate(totr.xmin, totr.xmax, 0.25f);
    add_rect_corner_positions(possible_bounds, rect);
  }
  if (zone.output_node) {
    const rctf &totr = zone.output_node->runtime->totr;
    rctf rect = totr;
    BLI_rctf_pad(&rect, node_padding, node_padding);
    rect.xmax = math::interpolate(totr.xmin, totr.xmax, 0.75f);
    add_rect_corner_positions(possible_bounds, rect);
  }

  if (snode.runtime->linkdrag) {
    for (const bNodeLink &link : snode.runtime->linkdrag->links) {
      if (link.fromnode == nullptr) {
        continue;
      }
      if (zone.contains_node_recursively(*link.fromnode) && zone.output_node != link.fromnode) {
        const float2 pos = node_link_bezier_points_dragged(snode, link)[3];
        rctf rect;
        BLI_rctf_init_pt_radius(&rect, pos, node_padding);
        add_rect_corner_positions(possible_bounds, rect);
      }
    }
  }

  Vector<int> convex_indices(possible_bounds.size());
  const int convex_positions_num = BLI_convexhull_2d(
      reinterpret_cast<float(*)[2]>(possible_bounds.data()),
      possible_bounds.size(),
      convex_indices.data());
  convex_indices.resize(convex_positions_num);

  for (const int i : convex_indices) {
    bounds.append(possible_bounds[i]);
  }
}

static void node_draw_zones(TreeDrawContext & /*tree_draw_ctx*/,
                            const ARegion &region,
                            const SpaceNode &snode,
                            const bNodeTree &ntree)
{
  const bNodeTreeZones *zones = ntree.zones();
  if (zones == nullptr) {
    return;
  }

  Array<Vector<float2>> bounds_by_zone(zones->zones.size());
  Array<bke::CurvesGeometry> fillet_curve_by_zone(zones->zones.size());
  /* Bounding box area of zones is used to determine draw order. */
  Array<float> bounding_box_area_by_zone(zones->zones.size());

  for (const int zone_i : zones->zones.index_range()) {
    const bNodeTreeZone &zone = *zones->zones[zone_i];

    find_bounds_by_zone_recursive(snode, zone, zones->zones, bounds_by_zone);
    const Span<float2> boundary_positions = bounds_by_zone[zone_i];
    const int boundary_positions_num = boundary_positions.size();

    const Bounds<float2> bounding_box = *bounds::min_max(boundary_positions);
    const float bounding_box_area = (bounding_box.max.x - bounding_box.min.x) *
                                    (bounding_box.max.y - bounding_box.min.y);
    bounding_box_area_by_zone[zone_i] = bounding_box_area;

    bke::CurvesGeometry boundary_curve(boundary_positions_num, 1);
    boundary_curve.cyclic_for_write().first() = true;
    boundary_curve.fill_curve_types(CURVE_TYPE_POLY);
    MutableSpan<float3> boundary_curve_positions = boundary_curve.positions_for_write();
    boundary_curve.offsets_for_write().copy_from({0, boundary_positions_num});
    for (const int i : boundary_positions.index_range()) {
      boundary_curve_positions[i] = float3(boundary_positions[i], 0.0f);
    }

    fillet_curve_by_zone[zone_i] = geometry::fillet_curves_poly(
        boundary_curve,
        IndexRange(1),
        VArray<float>::ForSingle(BASIS_RAD, boundary_positions_num),
        VArray<int>::ForSingle(5, boundary_positions_num),
        true,
        {});
  }

  const View2D &v2d = region.v2d;
  float scale;
  UI_view2d_scale_get(&v2d, &scale, nullptr);
  float line_width = 1.0f * scale;
  float viewport[4] = {};
  GPU_viewport_size_get_f(viewport);

  const auto get_theme_id = [&](const int zone_i) {
    const bNode *node = zones->zones[zone_i]->output_node;
    return bke::zone_type_by_node_type(node->type)->theme_id;
  };

  const uint pos = GPU_vertformat_attr_add(
      immVertexFormat(), "pos", GPU_COMP_F32, 3, GPU_FETCH_FLOAT);

  Vector<int> zone_draw_order;
  for (const int zone_i : zones->zones.index_range()) {
    zone_draw_order.append(zone_i);
  }
  std::sort(zone_draw_order.begin(), zone_draw_order.end(), [&](const int a, const int b) {
    /* Draw zones with smaller bounding box on top to make them visible. */
    return bounding_box_area_by_zone[a] > bounding_box_area_by_zone[b];
  });

  /* Draw all the contour lines after to prevent them from getting hidden by overlapping zones.
   */
  for (const int zone_i : zone_draw_order) {
    float zone_color[4];
    UI_GetThemeColor4fv(get_theme_id(zone_i), zone_color);
    if (zone_color[3] == 0.0f) {
      break;
    }
    const Span<float3> fillet_boundary_positions = fillet_curve_by_zone[zone_i].positions();
    /* Draw the background. */
    immBindBuiltinProgram(GPU_SHADER_3D_UNIFORM_COLOR);
    immUniformThemeColorBlend(TH_BACK, get_theme_id(zone_i), zone_color[3]);

    immBegin(GPU_PRIM_TRI_FAN, fillet_boundary_positions.size() + 1);
    for (const float3 &p : fillet_boundary_positions) {
      immVertex3fv(pos, p);
    }
    immVertex3fv(pos, fillet_boundary_positions[0]);
    immEnd();

    immUnbindProgram();
  }

  for (const int zone_i : zone_draw_order) {
    const Span<float3> fillet_boundary_positions = fillet_curve_by_zone[zone_i].positions();
    /* Draw the contour lines. */
    immBindBuiltinProgram(GPU_SHADER_3D_POLYLINE_UNIFORM_COLOR);

    immUniform2fv("viewportSize", &viewport[2]);
    immUniform1f("lineWidth", line_width * U.pixelsize);

    immUniformThemeColorAlpha(get_theme_id(zone_i), 1.0f);
    immBegin(GPU_PRIM_LINE_STRIP, fillet_boundary_positions.size() + 1);
    for (const float3 &p : fillet_boundary_positions) {
      immVertex3fv(pos, p);
    }
    immVertex3fv(pos, fillet_boundary_positions[0]);
    immEnd();

    immUnbindProgram();
  }
}

#define USE_DRAW_TOT_UPDATE

static void node_draw_nodetree(const bContext &C,
                               TreeDrawContext &tree_draw_ctx,
                               ARegion &region,
                               SpaceNode &snode,
                               bNodeTree &ntree,
                               Span<bNode *> nodes,
                               Span<uiBlock *> blocks,
                               bNodeInstanceKey parent_key)
{
#ifdef USE_DRAW_TOT_UPDATE
  BLI_rctf_init_minmax(&region.v2d.tot);
#endif

  /* Draw background nodes, last nodes in front. */
  for (const int i : nodes.index_range()) {
#ifdef USE_DRAW_TOT_UPDATE
    /* Unrelated to background nodes, update the v2d->tot,
     * can be anywhere before we draw the scroll bars. */
    BLI_rctf_union(&region.v2d.tot, &nodes[i]->runtime->totr);
#endif

    if (!(nodes[i]->flag & NODE_BACKGROUND)) {
      continue;
    }

    const bNodeInstanceKey key = BKE_node_instance_key(parent_key, &ntree, nodes[i]);
    node_draw(C, tree_draw_ctx, region, snode, ntree, *nodes[i], *blocks[i], key);
  }

  /* Node lines. */
  GPU_blend(GPU_BLEND_ALPHA);
  nodelink_batch_start(snode);

  for (const bNodeLink *link : ntree.all_links()) {
    if (!nodeLinkIsHidden(link) && !bke::nodeLinkIsSelected(link)) {
      node_draw_link(C, region.v2d, snode, *link, false);
    }
  }

  /* Draw selected node links after the unselected ones, so they are shown on top. */
  for (const bNodeLink *link : ntree.all_links()) {
    if (!nodeLinkIsHidden(link) && bke::nodeLinkIsSelected(link)) {
      node_draw_link(C, region.v2d, snode, *link, true);
    }
  }

  nodelink_batch_end(snode);
  GPU_blend(GPU_BLEND_NONE);

  /* Draw foreground nodes, last nodes in front. */
  for (const int i : nodes.index_range()) {
    if (nodes[i]->flag & NODE_BACKGROUND) {
      continue;
    }

    const bNodeInstanceKey key = BKE_node_instance_key(parent_key, &ntree, nodes[i]);
    node_draw(C, tree_draw_ctx, region, snode, ntree, *nodes[i], *blocks[i], key);
  }
}

/* Draw the breadcrumb on the top of the editor. */
static void draw_tree_path(const bContext &C, ARegion &region)
{
  GPU_matrix_push_projection();
  wmOrtho2_region_pixelspace(&region);

  const rcti *rect = ED_region_visible_rect(&region);

  const uiStyle *style = UI_style_get_dpi();
  const float padding_x = 16 * UI_SCALE_FAC;
  const int x = rect->xmin + padding_x;
  const int y = region.winy - UI_UNIT_Y * 0.6f;
  const int width = BLI_rcti_size_x(rect) - 2 * padding_x;

  uiBlock *block = UI_block_begin(&C, &region, __func__, UI_EMBOSS_NONE);
  uiLayout *layout = UI_block_layout(
      block, UI_LAYOUT_VERTICAL, UI_LAYOUT_PANEL, x, y, width, 1, 0, style);

  const Vector<ui::ContextPathItem> context_path = ed::space_node::context_path_for_space_node(C);
  ui::template_breadcrumbs(*layout, context_path);

  UI_block_layout_resolve(block, nullptr, nullptr);
  UI_block_end(&C, block);
  UI_block_draw(&C, block);

  GPU_matrix_pop_projection();
}

static void snode_setup_v2d(SpaceNode &snode, ARegion &region, const float2 &center)
{
  View2D &v2d = region.v2d;

  /* Shift view to node tree center. */
  UI_view2d_center_set(&v2d, center[0], center[1]);
  UI_view2d_view_ortho(&v2d);

  snode.runtime->aspect = BLI_rctf_size_x(&v2d.cur) / float(region.winx);
}

/* Similar to is_compositor_enabled() in `draw_manager.cc` but checks all 3D views. */
static bool realtime_compositor_is_in_use(const bContext &context)
{
  const Scene *scene = CTX_data_scene(&context);
  if (!scene->use_nodes) {
    return false;
  }

  if (!scene->nodetree) {
    return false;
  }

  if (U.experimental.use_full_frame_compositor &&
      scene->nodetree->execution_mode == NTREE_EXECUTION_MODE_REALTIME)
  {
    return true;
  }

  wmWindowManager *wm = CTX_wm_manager(&context);
  LISTBASE_FOREACH (const wmWindow *, win, &wm->windows) {
    const bScreen *screen = WM_window_get_active_screen(win);
    LISTBASE_FOREACH (const ScrArea *, area, &screen->areabase) {
      const SpaceLink &space = *static_cast<const SpaceLink *>(area->spacedata.first);
      if (space.spacetype == SPACE_VIEW3D) {
        const View3D &view_3d = reinterpret_cast<const View3D &>(space);

        if (view_3d.shading.use_compositor == V3D_SHADING_USE_COMPOSITOR_DISABLED) {
          continue;
        }

        if (!(view_3d.shading.type >= OB_MATERIAL)) {
          continue;
        }

        return true;
      }
    }
  }

  return false;
}

static void draw_nodetree(const bContext &C,
                          ARegion &region,
                          bNodeTree &ntree,
                          bNodeInstanceKey parent_key)
{
  SpaceNode *snode = CTX_wm_space_node(&C);
  ntree.ensure_topology_cache();

  Array<bNode *> nodes = tree_draw_order_calc_nodes(ntree);

  Array<uiBlock *> blocks = node_uiblocks_init(C, nodes);

  TreeDrawContext tree_draw_ctx;
  if (ntree.type == NTREE_GEOMETRY) {
    tree_draw_ctx.geo_log_by_zone = geo_log::GeoModifierLog::get_tree_log_by_zone_for_node_editor(
        *snode);
    for (geo_log::GeoTreeLog *log : tree_draw_ctx.geo_log_by_zone.values()) {
      log->ensure_node_warnings();
      log->ensure_node_run_time();
    }
    const WorkSpace *workspace = CTX_wm_workspace(&C);
    tree_draw_ctx.active_geometry_nodes_viewer = viewer_path::find_geometry_nodes_viewer(
        workspace->viewer_path, *snode);
  }
  else if (ntree.type == NTREE_COMPOSIT) {
    tree_draw_ctx.used_by_realtime_compositor = realtime_compositor_is_in_use(C);
  }
  else if (ntree.type == NTREE_SHADER && U.experimental.use_shader_node_previews &&
           BKE_scene_uses_shader_previews(CTX_data_scene(&C)) &&
           snode->overlay.flag & SN_OVERLAY_SHOW_OVERLAYS &&
           snode->overlay.flag & SN_OVERLAY_SHOW_PREVIEWS)
  {
    tree_draw_ctx.nested_group_infos = get_nested_previews(C, *snode);
  }

  node_update_nodetree(C, tree_draw_ctx, ntree, nodes, blocks);
  node_draw_zones(tree_draw_ctx, region, *snode, ntree);
  node_draw_nodetree(C, tree_draw_ctx, region, *snode, ntree, nodes, blocks, parent_key);
}

/**
 * Make the background slightly brighter to indicate that users are inside a node-group.
 */
static void draw_background_color(const SpaceNode &snode)
{
  const int max_tree_length = 3;
  const float bright_factor = 0.25f;

  /* We ignore the first element of the path since it is the top-most tree and it doesn't need to
   * be brighter. We also set a cap to how many levels we want to set apart, to avoid the
   * background from getting too bright. */
  const int clamped_tree_path_length = BLI_listbase_count_at_most(&snode.treepath,
                                                                  max_tree_length);
  const int depth = max_ii(0, clamped_tree_path_length - 1);

  float color[3];
  UI_GetThemeColor3fv(TH_BACK, color);
  mul_v3_fl(color, 1.0f + bright_factor * depth);
  GPU_clear_color(color[0], color[1], color[2], 1.0);
}

void node_draw_space(const bContext &C, ARegion &region)
{
  wmWindow *win = CTX_wm_window(&C);
  SpaceNode &snode = *CTX_wm_space_node(&C);
  View2D &v2d = region.v2d;

  /* Setup off-screen buffers. */
  GPUViewport *viewport = WM_draw_region_get_viewport(&region);

  GPUFrameBuffer *framebuffer_overlay = GPU_viewport_framebuffer_overlay_get(viewport);
  GPU_framebuffer_bind_no_srgb(framebuffer_overlay);

  UI_view2d_view_ortho(&v2d);
  draw_background_color(snode);
  GPU_depth_test(GPU_DEPTH_NONE);
  GPU_scissor_test(true);

  /* XXX `snode->runtime->cursor` set in coordinate-space for placing new nodes,
   * used for drawing noodles too. */
  UI_view2d_region_to_view(&region.v2d,
                           win->eventstate->xy[0] - region.winrct.xmin,
                           win->eventstate->xy[1] - region.winrct.ymin,
                           &snode.runtime->cursor[0],
                           &snode.runtime->cursor[1]);
  snode.runtime->cursor[0] /= UI_SCALE_FAC;
  snode.runtime->cursor[1] /= UI_SCALE_FAC;

  ED_region_draw_cb_draw(&C, &region, REGION_DRAW_PRE_VIEW);

  /* Only set once. */
  GPU_blend(GPU_BLEND_ALPHA);

  /* Nodes. */
  snode_set_context(C);

  const int grid_levels = UI_GetThemeValueType(TH_NODE_GRID_LEVELS, SPACE_NODE);
  UI_view2d_dot_grid_draw(&v2d, TH_GRID, NODE_GRID_STEP_SIZE, grid_levels);

  /* Draw parent node trees. */
  if (snode.treepath.last) {
    bNodeTreePath *path = (bNodeTreePath *)snode.treepath.last;

    /* Update tree path name (drawn in the bottom left). */
    ID *name_id = (path->nodetree && path->nodetree != snode.nodetree) ? &path->nodetree->id :
                                                                         snode.id;

    if (name_id && UNLIKELY(!STREQ(path->display_name, name_id->name + 2))) {
      STRNCPY(path->display_name, name_id->name + 2);
    }

    /* Current View2D center, will be set temporarily for parent node trees. */
    float2 center;
    UI_view2d_center_get(&v2d, &center.x, &center.y);

    /* Store new view center in path and current edit tree. */
    copy_v2_v2(path->view_center, center);
    if (snode.edittree) {
      copy_v2_v2(snode.edittree->view_center, center);
    }

    /* Top-level edit tree. */
    bNodeTree *ntree = path->nodetree;
    if (ntree) {
      snode_setup_v2d(snode, region, center);

      /* Backdrop. */
      draw_nodespace_back_pix(C, region, snode, path->parent_key);

      {
        float original_proj[4][4];
        GPU_matrix_projection_get(original_proj);

        GPU_matrix_push();
        GPU_matrix_identity_set();

        wmOrtho2_pixelspace(region.winx, region.winy);

        WM_gizmomap_draw(region.gizmo_map, &C, WM_GIZMOMAP_DRAWSTEP_2D);

        GPU_matrix_pop();
        GPU_matrix_projection_set(original_proj);
      }

      draw_nodetree(C, region, *ntree, path->parent_key);
    }

    /* Temporary links. */
    GPU_blend(GPU_BLEND_ALPHA);
    GPU_line_smooth(true);
    if (snode.runtime->linkdrag) {
      for (const bNodeLink &link : snode.runtime->linkdrag->links) {
        node_draw_link_dragged(C, v2d, snode, link);
      }
    }
    GPU_line_smooth(false);
    GPU_blend(GPU_BLEND_NONE);

    if (snode.overlay.flag & SN_OVERLAY_SHOW_OVERLAYS && snode.flag & SNODE_SHOW_GPENCIL) {
      /* Draw grease-pencil annotations. */
      ED_annotation_draw_view2d(&C, true);
    }
  }
  else {

    /* Backdrop. */
    draw_nodespace_back_pix(C, region, snode, NODE_INSTANCE_KEY_NONE);
  }

  ED_region_draw_cb_draw(&C, &region, REGION_DRAW_POST_VIEW);

  /* Reset view matrix. */
  UI_view2d_view_restore(&C);

  if (snode.overlay.flag & SN_OVERLAY_SHOW_OVERLAYS) {
    if (snode.flag & SNODE_SHOW_GPENCIL && snode.treepath.last) {
      /* Draw grease-pencil (screen strokes, and also paint-buffer). */
      ED_annotation_draw_view2d(&C, false);
    }

    /* Draw context path. */
    if (snode.overlay.flag & SN_OVERLAY_SHOW_PATH && snode.edittree) {
      draw_tree_path(C, region);
    }
  }

  /* Scrollers. */
  UI_view2d_scrollers_draw(&v2d, nullptr);
}

}  // namespace blender::ed::space_node

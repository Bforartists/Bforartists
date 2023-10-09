/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#include "BLI_index_range.hh"
#include "BLI_listbase.h"
#include "BLI_map.hh"
#include "BLI_rect.h"
#include "BLI_set.hh"
#include "BLI_string.h"
#include "BLI_string_ref.hh"

#include "DNA_modifier_types.h"
#include "DNA_node_types.h"
#include "DNA_object_types.h"
#include "DNA_space_types.h"

#include "BKE_context.h"
#include "BKE_node_runtime.hh"
#include "BKE_node_tree_update.h"
#include "BKE_node_tree_zones.hh"
#include "BKE_object.hh"

#include "RNA_access.hh"
#include "RNA_enum_types.hh"

#include "ED_node.hh"
#include "ED_screen.hh"
#include "ED_undo.hh"

#include "BLT_translation.h"

#include "UI_interface.hh"
#include "UI_resources.hh"

#include "NOD_geometry_nodes_log.hh"

#include "node_intern.hh"

using blender::nodes::geo_eval_log::GeometryAttributeInfo;

namespace blender::ed::space_node {

struct AttributeSearchData {
  int32_t node_id;
  char socket_identifier[MAX_NAME];
};

/* This class must not have a destructor, since it is used by buttons and freed with #MEM_freeN. */
BLI_STATIC_ASSERT(std::is_trivially_destructible_v<AttributeSearchData>, "");

static Vector<const GeometryAttributeInfo *> get_attribute_info_from_context(
    const bContext &C, AttributeSearchData &data)
{
  using namespace nodes::geo_eval_log;

  SpaceNode *snode = CTX_wm_space_node(&C);
  if (!snode) {
    BLI_assert_unreachable();
    return {};
  }
  bNodeTree *node_tree = snode->edittree;
  if (node_tree == nullptr) {
    BLI_assert_unreachable();
    return {};
  }
  const bNode *node = node_tree->node_by_id(data.node_id);
  if (node == nullptr) {
    BLI_assert_unreachable();
    return {};
  }
  const bke::bNodeTreeZones *tree_zones = node_tree->zones();
  if (!tree_zones) {
    return {};
  }
  const Map<const bke::bNodeTreeZone *, GeoTreeLog *> log_by_zone =
      GeoModifierLog::get_tree_log_by_zone_for_node_editor(*snode);

  Set<StringRef> names;

  /* For the attribute input node, collect attribute information from all nodes in the group. */
  if (node->type == GEO_NODE_INPUT_NAMED_ATTRIBUTE) {
    Vector<const GeometryAttributeInfo *> attributes;
    for (GeoTreeLog *tree_log : log_by_zone.values()) {
      tree_log->ensure_socket_values();
      tree_log->ensure_existing_attributes();
      for (const GeometryAttributeInfo *attribute : tree_log->existing_attributes) {
        if (!names.add(attribute->name)) {
          continue;
        }
        if (!bke::allow_procedural_attribute_access(attribute->name)) {
          continue;
        }
        attributes.append(attribute);
      }
    }
    return attributes;
  }
  const bke::bNodeTreeZone *zone = tree_zones->get_zone_by_node(node->identifier);
  GeoTreeLog *tree_log = log_by_zone.lookup_default(zone, nullptr);
  if (!tree_log) {
    return {};
  }
  tree_log->ensure_socket_values();
  GeoNodeLog *node_log = tree_log->nodes.lookup_ptr(node->identifier);
  if (node_log == nullptr) {
    return {};
  }

  Vector<const GeometryAttributeInfo *> attributes;
  for (const bNodeSocket *input_socket : node->input_sockets()) {
    if (input_socket->type != SOCK_GEOMETRY) {
      continue;
    }
    const ValueLog *value_log = tree_log->find_socket_value_log(*input_socket);
    if (value_log == nullptr) {
      continue;
    }
    if (const GeometryInfoLog *geo_log = dynamic_cast<const GeometryInfoLog *>(value_log)) {
      for (const GeometryAttributeInfo &attribute : geo_log->attributes) {
        if (bke::allow_procedural_attribute_access(attribute.name)) {
          if (names.add(attribute.name)) {
            attributes.append(&attribute);
          }
        }
      }
    }
  }
  return attributes;
}

static void attribute_search_update_fn(
    const bContext *C, void *arg, const char *str, uiSearchItems *items, const bool is_first)
{
  if (ED_screen_animation_playing(CTX_wm_manager(C))) {
    return;
  }

  AttributeSearchData *data = static_cast<AttributeSearchData *>(arg);

  Vector<const GeometryAttributeInfo *> infos = get_attribute_info_from_context(*C, *data);

  ui::attribute_search_add_items(str, true, infos, items, is_first);
}

/**
 * Some custom data types don't correspond to node types and therefore can't be
 * used by the named attribute input node. Find the best option or fallback to float.
 */
static eCustomDataType data_type_in_attribute_input_node(const eCustomDataType type)
{
  switch (type) {
    case CD_PROP_FLOAT:
    case CD_PROP_INT32:
    case CD_PROP_FLOAT3:
    case CD_PROP_COLOR:
    case CD_PROP_BOOL:
    case CD_PROP_QUATERNION:
      return type;
    case CD_PROP_BYTE_COLOR:
      return CD_PROP_COLOR;
    case CD_PROP_STRING:
      /* Unsupported currently. */
      return CD_PROP_FLOAT;
    case CD_PROP_FLOAT2:
    case CD_PROP_INT32_2D:
      /* No 2D vector sockets currently. */
      return CD_PROP_FLOAT3;
    case CD_PROP_INT8:
      return CD_PROP_INT32;
    default:
      return CD_PROP_FLOAT;
  }
}

static void attribute_search_exec_fn(bContext *C, void *data_v, void *item_v)
{
  if (ED_screen_animation_playing(CTX_wm_manager(C))) {
    return;
  }
  GeometryAttributeInfo *item = (GeometryAttributeInfo *)item_v;
  if (item == nullptr) {
    return;
  }
  SpaceNode *snode = CTX_wm_space_node(C);
  if (!snode) {
    BLI_assert_unreachable();
    return;
  }
  bNodeTree *node_tree = snode->edittree;
  if (node_tree == nullptr) {
    BLI_assert_unreachable();
    return;
  }
  AttributeSearchData *data = static_cast<AttributeSearchData *>(data_v);
  bNode *node = node_tree->node_by_id(data->node_id);
  if (node == nullptr) {
    BLI_assert_unreachable();
    return;
  }
  bNodeSocket *socket = bke::node_find_enabled_input_socket(*node, data->socket_identifier);
  if (socket == nullptr) {
    BLI_assert_unreachable();
    return;
  }
  BLI_assert(socket->type == SOCK_STRING);

  /* For the attribute input node, also adjust the type and links connected to the output. */
  if (node->type == GEO_NODE_INPUT_NAMED_ATTRIBUTE && item->data_type.has_value()) {
    NodeGeometryInputNamedAttribute &storage = *(NodeGeometryInputNamedAttribute *)node->storage;
    const eCustomDataType new_type = data_type_in_attribute_input_node(*item->data_type);
    if (new_type != storage.data_type) {
      storage.data_type = new_type;
      /* Make the output socket with the new type on the attribute input node active. */
      node->typeinfo->updatefunc(node_tree, node);

      /* Relink all node links to the newly active output socket. */
      bNodeSocket *output_socket = bke::node_find_enabled_output_socket(*node, "Attribute");
      LISTBASE_FOREACH (bNodeLink *, link, &node_tree->links) {
        if (link->fromnode != node) {
          continue;
        }
        if (!STREQ(link->fromsock->name, "Attribute")) {
          continue;
        }
        link->fromsock = output_socket;
        BKE_ntree_update_tag_link_changed(node_tree);
      }
    }
    BKE_ntree_update_tag_node_property(node_tree, node);
    ED_node_tree_propagate_change(C, CTX_data_main(C), node_tree);
  }

  bNodeSocketValueString *value = static_cast<bNodeSocketValueString *>(socket->default_value);
  BLI_strncpy(value->value, item->name.c_str(), MAX_NAME);

  ED_undo_push(C, "Assign Attribute Name");
}

void node_geometry_add_attribute_search_button(const bContext & /*C*/,
                                               const bNode &node,
                                               PointerRNA &socket_ptr,
                                               uiLayout &layout)
{
  uiBlock *block = uiLayoutGetBlock(&layout);
  uiBut *but = uiDefIconTextButR(block,
                                 UI_BTYPE_SEARCH_MENU,
                                 0,
                                 ICON_NONE,
                                 "",
                                 0,
                                 0,
                                 10 * UI_UNIT_X, /* Dummy value, replaced by layout system. */
                                 UI_UNIT_Y,
                                 &socket_ptr,
                                 "default_value",
                                 0,
                                 0.0f,
                                 0.0f,
                                 0.0f,
                                 0.0f,
                                 "");

  const bNodeSocket &socket = *static_cast<const bNodeSocket *>(socket_ptr.data);
  AttributeSearchData *data = MEM_new<AttributeSearchData>(__func__);
  data->node_id = node.identifier;
  STRNCPY(data->socket_identifier, socket.identifier);

  UI_but_func_search_set_results_are_suggestions(but, true);
  UI_but_func_search_set_sep_string(but, UI_MENU_ARROW_SEP);
  UI_but_func_search_set(but,
                         nullptr,
                         attribute_search_update_fn,
                         static_cast<void *>(data),
                         true,
                         nullptr,
                         attribute_search_exec_fn,
                         nullptr);
}

}  // namespace blender::ed::space_node

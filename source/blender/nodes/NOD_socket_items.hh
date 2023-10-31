/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#pragma once

/**
 * Some nodes have a dynamic number of sockets (e.g. simulation input/output). These nodes store an
 * array of items in their `bNode->storage` (e.g. `NodeSimulationItem`). Different nodes have
 * slightly different storage requirements, but a lot of the logic is still the same between nodes.
 * This file implements various shared functionality that can be used by different nodes to deal
 * with these item arrays.
 *
 * In order to use the functions, one has to implement an "accessor" which tells the shared code
 * how to deal with specific item arrays. Different functions have different requirements for the
 * accessor. It's easiest to just look at existing accessors like #SimulationItemsAccessor and
 * #RepeatItemsAccessor and to implement the same methods.
 */

#include "BLI_string.h"
#include "BLI_string_utils.hh"

#include "BKE_node.h"
#include "BKE_node_runtime.hh"

#include "NOD_socket.hh"

namespace blender::nodes::socket_items {

/**
 * References a "C-Array" that is stored elsewhere. This is different from a MutableSpan, because
 * one can even resize the array through this reference.
 */
template<typename T> struct SocketItemsRef {
  T **items;
  int *items_num;
  int *active_index;
};

/**
 * Iterates over the node tree to find the node that this item belongs to.
 */
template<typename Accessor>
inline bNode *find_node_by_item(bNodeTree &ntree, const typename Accessor::ItemT &item)
{
  ntree.ensure_topology_cache();
  for (bNode *node : ntree.nodes_by_type(Accessor::node_idname)) {
    SocketItemsRef array = Accessor::get_items_from_node(*node);
    if (&item >= *array.items && &item < *array.items + *array.items_num) {
      return node;
    }
  }
  return nullptr;
}

/**
 * Low level utility to remove an item from the array and to shift the elements after it.
 */
template<typename T>
inline void remove_item(T **items,
                        int *items_num,
                        int *active_index,
                        const int remove_index,
                        void (*destruct_item)(T *))
{
  static_assert(std::is_trivial_v<T>);
  BLI_assert(remove_index >= 0);
  BLI_assert(remove_index < *items_num);

  const int old_items_num = *items_num;
  const int new_items_num = old_items_num - 1;
  const int old_active_index = *active_index;

  T *old_items = *items;
  T *new_items = MEM_cnew_array<T>(new_items_num, __func__);

  std::copy_n(old_items, remove_index, new_items);
  std::copy_n(
      old_items + remove_index + 1, old_items_num - remove_index - 1, new_items + remove_index);

  destruct_item(&old_items[remove_index]);
  MEM_SAFE_FREE(old_items);

  const int new_active_index = std::max(
      0, old_active_index == new_items_num ? new_items_num - 1 : old_active_index);

  *items = new_items;
  *items_num = new_items_num;
  *active_index = new_active_index;
}

/**
 * Low level utility to remove all elements from an items array.
 */
template<typename T>
inline void clear_items(T **items, int *items_num, int *active_index, void (*destruct_item)(T *))
{
  static_assert(std::is_trivial_v<T>);
  for (const int i : blender::IndexRange(*items_num)) {
    destruct_item(&(*items)[i]);
  }
  MEM_SAFE_FREE(*items);
  *items_num = 0;
  *active_index = 0;
}

/**
 * Low level utility to move one item from one index to another.
 */
template<typename T>
inline void move_item(T *items, const int items_num, const int from_index, const int to_index)
{
  static_assert(std::is_trivial_v<T>);
  BLI_assert(from_index >= 0);
  BLI_assert(from_index < items_num);
  BLI_assert(to_index >= 0);
  BLI_assert(to_index < items_num);
  UNUSED_VARS_NDEBUG(items_num);

  if (from_index == to_index) {
    return;
  }

  if (from_index < to_index) {
    const T tmp = items[from_index];
    for (int i = from_index; i < to_index; i++) {
      items[i] = items[i + 1];
    }
    items[to_index] = tmp;
  }
  else if (from_index > to_index) {
    const T tmp = items[from_index];
    for (int i = from_index; i > to_index; i--) {
      items[i] = items[i - 1];
    }
    items[to_index] = tmp;
  }
}

/**
 * Destruct all the items and the free the array itself.
 */
template<typename Accessor> inline void destruct_array(bNode &node)
{
  using ItemT = typename Accessor::ItemT;
  SocketItemsRef ref = Accessor::get_items_from_node(node);
  for (const int i : IndexRange(*ref.items_num)) {
    ItemT &item = (*ref.items)[i];
    Accessor::destruct_item(&item);
  }
  MEM_SAFE_FREE(*ref.items);
}

/**
 * Copy the items from the storage of the source node to the storage of the destination node.
 */
template<typename Accessor> inline void copy_array(const bNode &src_node, bNode &dst_node)
{
  using ItemT = typename Accessor::ItemT;
  SocketItemsRef src_ref = Accessor::get_items_from_node(const_cast<bNode &>(src_node));
  SocketItemsRef dst_ref = Accessor::get_items_from_node(dst_node);
  const int items_num = *src_ref.items_num;
  *dst_ref.items = MEM_cnew_array<ItemT>(items_num, __func__);
  for (const int i : IndexRange(items_num)) {
    Accessor::copy_item((*src_ref.items)[i], (*dst_ref.items)[i]);
  }
}

/**
 * Changes the name of an existing item and makes sure that the name is unique among other the
 * other items in the same array.
 */
template<typename Accessor>
inline void set_item_name_and_make_unique(bNode &node,
                                          typename Accessor::ItemT &item,
                                          const char *value)
{
  using ItemT = typename Accessor::ItemT;
  SocketItemsRef array = Accessor::get_items_from_node(node);
  const char *default_name = nodeStaticSocketLabel(*Accessor::get_socket_type(item), 0);

  char unique_name[MAX_NAME + 4];
  STRNCPY(unique_name, value);

  struct Args {
    SocketItemsRef<ItemT> array;
    ItemT *item;
  } args = {array, &item};
  BLI_uniquename_cb(
      [](void *arg, const char *name) {
        const Args &args = *static_cast<Args *>(arg);
        for (ItemT &item : blender::MutableSpan(*args.array.items, *args.array.items_num)) {
          if (&item != args.item) {
            if (STREQ(*Accessor::get_name(item), name)) {
              return true;
            }
          }
        }
        return false;
      },
      &args,
      default_name,
      '.',
      unique_name,
      ARRAY_SIZE(unique_name));

  char **item_name = Accessor::get_name(item);
  MEM_SAFE_FREE(*item_name);
  *item_name = BLI_strdup(unique_name);
}

/**
 * Add a new item at the end with the given socket type and name.
 */
template<typename Accessor>
inline typename Accessor::ItemT *add_item_with_socket_and_name(
    bNode &node, const eNodeSocketDatatype socket_type, const char *name)
{
  using ItemT = typename Accessor::ItemT;
  BLI_assert(Accessor::supports_socket_type(socket_type));

  SocketItemsRef array = Accessor::get_items_from_node(node);

  ItemT *old_items = *array.items;
  const int old_items_num = *array.items_num;
  const int new_items_num = old_items_num + 1;

  ItemT *new_items = MEM_cnew_array<ItemT>(new_items_num, __func__);
  std::copy_n(old_items, old_items_num, new_items);
  ItemT &new_item = new_items[old_items_num];

  Accessor::init_with_socket_type_and_name(node, new_item, socket_type, name);

  MEM_SAFE_FREE(old_items);
  *array.items = new_items;
  *array.items_num = new_items_num;
  *array.active_index = old_items_num;

  return &new_item;
}

/**
 * Check if the link connects to the `extend_socket`. If yes, create a new item for the linked
 * socket, update the node and then change the link to point to the new socket.
 * \return False if the link should be removed.
 */
template<typename Accessor>
[[nodiscard]] inline bool try_add_item_via_extend_socket(bNodeTree &ntree,
                                                         bNode &extend_node,
                                                         bNodeSocket &extend_socket,
                                                         bNode &storage_node,
                                                         bNodeLink &link)
{
  using ItemT = typename Accessor::ItemT;
  bNodeSocket *src_socket = nullptr;
  if (link.tosock == &extend_socket) {
    src_socket = link.fromsock;
  }
  else if (link.fromsock == &extend_socket) {
    src_socket = link.tosock;
  }
  else {
    return false;
  }
  const eNodeSocketDatatype socket_type = eNodeSocketDatatype(src_socket->type);
  if (!Accessor::supports_socket_type(socket_type)) {
    return false;
  }
  const ItemT *item = add_item_with_socket_and_name<Accessor>(
      storage_node, socket_type, src_socket->name);
  if (item == nullptr) {
    return false;
  }
  update_node_declaration_and_sockets(ntree, extend_node);
  const std::string item_identifier = Accessor::socket_identifier_for_item(*item);
  if (extend_socket.is_input()) {
    bNodeSocket *new_socket = nodeFindSocket(&extend_node, SOCK_IN, item_identifier.c_str());
    link.tosock = new_socket;
  }
  else {
    bNodeSocket *new_socket = nodeFindSocket(&extend_node, SOCK_OUT, item_identifier.c_str());
    link.fromsock = new_socket;
  }
  return true;
}

/**
 * Allow the item array to be extended from any extend-socket in the node.
 * \return False if the link should be removed.
 */
template<typename Accessor>
[[nodiscard]] inline bool try_add_item_via_any_extend_socket(bNodeTree &ntree,
                                                             bNode &extend_node,
                                                             bNode &storage_node,
                                                             bNodeLink &link)
{
  bNodeSocket *possible_extend_socket = nullptr;
  if (link.fromnode == &extend_node) {
    possible_extend_socket = link.fromsock;
  }
  if (link.tonode == &extend_node) {
    possible_extend_socket = link.tosock;
  }
  if (possible_extend_socket == nullptr) {
    return true;
  }
  if (!STREQ(possible_extend_socket->idname, "NodeSocketVirtual")) {
    return true;
  }
  return try_add_item_via_extend_socket<Accessor>(
      ntree, extend_node, *possible_extend_socket, storage_node, link);
}

}  // namespace blender::nodes::socket_items

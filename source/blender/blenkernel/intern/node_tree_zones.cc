/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#include "BKE_node.hh"
#include "BKE_node_runtime.hh"
#include "BKE_node_tree_zones.hh"

#include "BLI_bit_group_vector.hh"
#include "BLI_bit_span_ops.hh"
#include "BLI_set.hh"
#include "BLI_task.hh"
#include "BLI_timeit.hh"

namespace blender::bke {

static void update_zone_depths(bNodeTreeZone &zone)
{
  if (zone.depth >= 0) {
    return;
  }
  if (zone.parent_zone == nullptr) {
    zone.depth = 0;
    return;
  }
  update_zone_depths(*zone.parent_zone);
  zone.depth = zone.parent_zone->depth + 1;
}

static Vector<std::unique_ptr<bNodeTreeZone>> find_zone_nodes(
    const bNodeTree &tree,
    bNodeTreeZones &owner,
    Map<const bNode *, bNodeTreeZone *> &r_zone_by_inout_node)
{
  const Span<const bNodeZoneType *> zone_types = all_zone_types();

  Vector<std::unique_ptr<bNodeTreeZone>> zones;
  Vector<const bNode *> zone_output_nodes;
  for (const bNodeZoneType *zone_type : zone_types) {
    zone_output_nodes.extend(tree.nodes_by_type(zone_type->output_idname));
  }
  for (const bNode *node : zone_output_nodes) {
    auto zone = std::make_unique<bNodeTreeZone>();
    zone->owner = &owner;
    zone->index = zones.size();
    zone->output_node = node;
    r_zone_by_inout_node.add(node, zone.get());
    zones.append_and_get_index(std::move(zone));
  }
  for (const bNodeZoneType *zone_type : zone_types) {
    for (const bNode *input_node : tree.nodes_by_type(zone_type->input_idname)) {
      if (const bNode *output_node = zone_type->get_corresponding_output(tree, *input_node)) {
        if (bNodeTreeZone *zone = r_zone_by_inout_node.lookup_default(output_node, nullptr)) {
          zone->input_node = input_node;
          r_zone_by_inout_node.add(input_node, zone);
        }
      }
    }
  }
  return zones;
}

struct ZoneRelation {
  bNodeTreeZone *parent;
  bNodeTreeZone *child;

  uint64_t hash() const
  {
    return get_default_hash_2(this->parent, this->child);
  }

  friend bool operator==(const ZoneRelation &a, const ZoneRelation &b)
  {
    return a.parent == b.parent && a.child == b.child;
  }
};

static std::optional<Vector<ZoneRelation>> get_direct_zone_relations(
    const Span<std::unique_ptr<bNodeTreeZone>> all_zones,
    const BitGroupVector<> &depend_on_input_flag_array)
{
  VectorSet<ZoneRelation> all_zone_relations;

  /* Gather all relations, even the transitive once. */
  for (const std::unique_ptr<bNodeTreeZone> &zone : all_zones) {
    const int zone_i = zone->index;
    for (const bNode *node : {zone->output_node}) {
      if (node == nullptr) {
        continue;
      }
      const BoundedBitSpan depend_on_input_flags = depend_on_input_flag_array[node->index()];
      bits::foreach_1_index(depend_on_input_flags, [&](const int parent_zone_i) {
        if (parent_zone_i != zone_i) {
          all_zone_relations.add_new({all_zones[parent_zone_i].get(), zone.get()});
        }
      });
    }
  }

  for (const ZoneRelation &relation : all_zone_relations) {
    const ZoneRelation reverse_relation{relation.child, relation.parent};
    if (all_zone_relations.contains(reverse_relation)) {
      /* There is a cyclic zone dependency. */
      return std::nullopt;
    }
  }

  /* Remove transitive relations. This is a brute force algorithm currently. */
  Vector<int> transitive_relations;
  for (const int a : all_zone_relations.index_range()) {
    const ZoneRelation &relation_a = all_zone_relations[a];
    for (const int b : all_zone_relations.index_range()) {
      if (a == b) {
        continue;
      }
      const ZoneRelation &relation_b = all_zone_relations[b];
      if (relation_a.child != relation_b.parent) {
        continue;
      }
      const ZoneRelation transitive_relation{relation_a.parent, relation_b.child};
      const int transitive_relation_i = all_zone_relations.index_of_try(transitive_relation);
      if (transitive_relation_i != -1) {
        transitive_relations.append_non_duplicates(transitive_relation_i);
      }
    }
  }
  std::sort(transitive_relations.begin(), transitive_relations.end(), std::greater<>());

  Vector<ZoneRelation> zone_relations = all_zone_relations.as_span();
  for (const int i : transitive_relations) {
    zone_relations.remove_and_reorder(i);
  }

  return zone_relations;
}

static bool update_zone_per_node(const Span<const bNode *> all_nodes,
                                 const Span<std::unique_ptr<bNodeTreeZone>> all_zones,
                                 const BitGroupVector<> &depend_on_input_flag_array,
                                 const Map<const bNode *, bNodeTreeZone *> &zone_by_inout_node,
                                 Map<int, int> &r_zone_by_node_id,
                                 Vector<const bNode *> &r_node_outside_zones)
{
  bool found_node_in_multiple_zones = false;
  for (const int node_i : all_nodes.index_range()) {
    const bNode &node = *all_nodes[node_i];
    const BoundedBitSpan depend_on_input_flags = depend_on_input_flag_array[node_i];
    bNodeTreeZone *parent_zone = nullptr;
    bits::foreach_1_index(depend_on_input_flags, [&](const int parent_zone_i) {
      bNodeTreeZone *zone = all_zones[parent_zone_i].get();
      if (ELEM(&node, zone->input_node, zone->output_node)) {
        return;
      }
      if (parent_zone == nullptr) {
        parent_zone = zone;
        return;
      }
      for (bNodeTreeZone *iter_zone = zone->parent_zone; iter_zone;
           iter_zone = iter_zone->parent_zone) {
        if (iter_zone == parent_zone) {
          /* This zone is nested in the parent zone, so it becomes the new parent of the node. */
          parent_zone = zone;
          return;
        }
      }
      for (bNodeTreeZone *iter_zone = parent_zone->parent_zone; iter_zone;
           iter_zone = iter_zone->parent_zone)
      {
        if (iter_zone == zone) {
          /* This zone is a parent of the current parent of the node, do nothing. */
          return;
        }
      }
      found_node_in_multiple_zones = true;
    });
    if (parent_zone == nullptr) {
      if (!zone_by_inout_node.contains(&node)) {
        r_node_outside_zones.append(&node);
      }
    }
    else {
      r_zone_by_node_id.add(node.identifier, parent_zone->index);
    }
  }
  for (const MapItem<const bNode *, bNodeTreeZone *> item : zone_by_inout_node.items()) {
    r_zone_by_node_id.add_overwrite(item.key->identifier, item.value->index);
  }
  return found_node_in_multiple_zones;
}

static void update_zone_border_links(const bNodeTree &tree, bNodeTreeZones &tree_zones)
{
  for (const bNodeLink *link : tree.all_links()) {
    if (!link->is_available()) {
      continue;
    }
    if (link->is_muted()) {
      continue;
    }
    bNodeTreeZone *from_zone = const_cast<bNodeTreeZone *>(
        tree_zones.get_zone_by_socket(*link->fromsock));
    bNodeTreeZone *to_zone = const_cast<bNodeTreeZone *>(
        tree_zones.get_zone_by_socket(*link->tosock));
    if (from_zone == to_zone) {
      continue;
    }
    BLI_assert(from_zone == nullptr || from_zone->contains_zone_recursively(*to_zone));
    for (bNodeTreeZone *zone = to_zone; zone != from_zone; zone = zone->parent_zone) {
      zone->border_links.append(link);
    }
  }
}

static std::unique_ptr<bNodeTreeZones> discover_tree_zones(const bNodeTree &tree)
{
  tree.ensure_topology_cache();
  if (tree.has_available_link_cycle()) {
    return {};
  }

  const Span<int> input_types = all_zone_input_node_types();
  const Span<int> output_types = all_zone_output_node_types();

  std::unique_ptr<bNodeTreeZones> tree_zones = std::make_unique<bNodeTreeZones>();

  const Span<const bNode *> all_nodes = tree.all_nodes();
  Map<const bNode *, bNodeTreeZone *> zone_by_inout_node;
  tree_zones->zones = find_zone_nodes(tree, *tree_zones, zone_by_inout_node);

  const int zones_num = tree_zones->zones.size();
  const int nodes_num = all_nodes.size();
  /* A bit for every node-zone-combination. The bit is set when the node is in the zone. */
  BitGroupVector<> depend_on_input_flag_array(nodes_num, zones_num, false);
  /* The bit is set when the node depends on the output of the zone. */
  BitGroupVector<> depend_on_output_flag_array(nodes_num, zones_num, false);

  const Span<const bNode *> sorted_nodes = tree.toposort_left_to_right();
  for (const bNode *node : sorted_nodes) {
    const int node_i = node->index();
    MutableBoundedBitSpan depend_on_input_flags = depend_on_input_flag_array[node_i];
    MutableBoundedBitSpan depend_on_output_flags = depend_on_output_flag_array[node_i];

    /* Forward all bits from the nodes to the left. */
    for (const bNodeSocket *input_socket : node->input_sockets()) {
      if (!input_socket->is_available()) {
        continue;
      }
      for (const bNodeLink *link : input_socket->directly_linked_links()) {
        if (link->is_muted()) {
          continue;
        }
        const bNode &from_node = *link->fromnode;
        const int from_node_i = from_node.index();
        depend_on_input_flags |= depend_on_input_flag_array[from_node_i];
        depend_on_output_flags |= depend_on_output_flag_array[from_node_i];
      }
    }
    if (input_types.contains(node->type)) {
      if (const bNodeTreeZone *zone = zone_by_inout_node.lookup_default(node, nullptr)) {
        /* Now entering a zone, so set the corresponding bit. */
        depend_on_input_flags[zone->index].set();
      }
    }
    else if (output_types.contains(node->type)) {
      if (const bNodeTreeZone *zone = zone_by_inout_node.lookup_default(node, nullptr)) {
        /* The output is implicitly linked to the input, so also propagate the bits from there. */
        if (const bNode *zone_input_node = zone->input_node) {
          const int input_node_i = zone_input_node->index();
          depend_on_input_flags |= depend_on_input_flag_array[input_node_i];
          depend_on_output_flags |= depend_on_output_flag_array[input_node_i];
        }
        /* Now exiting a zone, so change the bits accordingly. */
        depend_on_input_flags[zone->index].reset();
        depend_on_output_flags[zone->index].set();
      }
    }

    if (bits::has_common_set_bits(depend_on_input_flags, depend_on_output_flags)) {
      /* A node can not be inside and after a zone at the same time. */
      return {};
    }
  }

  const std::optional<Vector<ZoneRelation>> zone_relations = get_direct_zone_relations(
      tree_zones->zones, depend_on_input_flag_array);
  if (!zone_relations) {
    /* Found cyclic relations. */
    return {};
  }

  /* Set parent and child pointers in zones. */
  for (const ZoneRelation &relation : *zone_relations) {
    relation.parent->child_zones.append(relation.child);
    BLI_assert(relation.child->parent_zone == nullptr);
    relation.child->parent_zone = relation.parent;
  }

  Set<const bNodeTreeZone *> found_zones;
  for (std::unique_ptr<bNodeTreeZone> &main_zone : tree_zones->zones) {
    found_zones.clear();
    for (bNodeTreeZone *zone = main_zone.get(); zone; zone = zone->parent_zone) {
      if (!found_zones.add(zone)) {
        /* Found cyclic parent relationships between zones. */
        return {};
      }
    }
  }

  /* Update depths. */
  for (std::unique_ptr<bNodeTreeZone> &zone : tree_zones->zones) {
    update_zone_depths(*zone);
  }

  for (std::unique_ptr<bNodeTreeZone> &zone : tree_zones->zones) {
    if (zone->depth == 0) {
      tree_zones->root_zones.append(zone.get());
    }
  }

  const bool found_node_in_multiple_zones = update_zone_per_node(all_nodes,
                                                                 tree_zones->zones,
                                                                 depend_on_input_flag_array,
                                                                 zone_by_inout_node,
                                                                 tree_zones->zone_by_node_id,
                                                                 tree_zones->nodes_outside_zones);
  if (found_node_in_multiple_zones) {
    return {};
  }

  for (const bNode *node : tree.nodes_by_type("NodeGroupOutput")) {
    if (tree_zones->zone_by_node_id.contains(node->identifier)) {
      /* Group output nodes must not be in a zone. */
      return {};
    }
  }

  for (const int node_i : all_nodes.index_range()) {
    const bNode *node = all_nodes[node_i];
    const int zone_i = tree_zones->zone_by_node_id.lookup_default(node->identifier, -1);
    if (zone_i == -1) {
      continue;
    }
    const bNodeTreeZone &zone = *tree_zones->zones[zone_i];
    if (ELEM(node, zone.input_node, zone.output_node)) {
      continue;
    }
    tree_zones->zones[zone_i]->child_nodes.append(node);
  }

  update_zone_border_links(tree, *tree_zones);

  return tree_zones;
}

const bNodeTreeZones *get_tree_zones(const bNodeTree &tree)
{
  tree.ensure_topology_cache();
  tree.runtime->tree_zones_cache_mutex.ensure(
      [&]() { tree.runtime->tree_zones = discover_tree_zones(tree); });
  return tree.runtime->tree_zones.get();
}

bool bNodeTreeZone::contains_node_recursively(const bNode &node) const
{
  const bNodeTreeZones *zones = this->owner;
  const int zone_i = zones->zone_by_node_id.lookup_default(node.identifier, -1);
  if (zone_i == -1) {
    return false;
  }
  for (const bNodeTreeZone *zone = zones->zones[zone_i].get(); zone; zone = zone->parent_zone) {
    if (zone == this) {
      return true;
    }
  }
  return false;
}

bool bNodeTreeZone::contains_zone_recursively(const bNodeTreeZone &other_zone) const
{
  for (const bNodeTreeZone *zone = other_zone.parent_zone; zone; zone = zone->parent_zone) {
    if (zone == this) {
      return true;
    }
  }
  return false;
}

const bNodeTreeZone *bNodeTreeZones::get_zone_by_socket(const bNodeSocket &socket) const
{
  const bNode &node = socket.owner_node();
  const bNodeTreeZone *zone = this->get_zone_by_node(node.identifier);
  if (zone == nullptr) {
    return zone;
  }
  if (zone->input_node == &node) {
    if (socket.is_input()) {
      return zone->parent_zone;
    }
  }
  if (zone->output_node == &node) {
    if (socket.is_output()) {
      return zone->parent_zone;
    }
  }
  return zone;
}

const bNodeTreeZone *bNodeTreeZones::get_zone_by_node(const int32_t node_id) const
{
  const int zone_i = this->zone_by_node_id.lookup_default(node_id, -1);
  if (zone_i == -1) {
    return nullptr;
  }
  return this->zones[zone_i].get();
}

Vector<const bNodeTreeZone *> bNodeTreeZones::get_zone_stack_for_node(const int node_id) const
{
  const bNodeTreeZone *zone = this->get_zone_by_node(node_id);
  if (zone == nullptr) {
    return {};
  }
  Vector<const bNodeTreeZone *> zone_stack;
  for (; zone; zone = zone->parent_zone) {
    zone_stack.append(zone);
  }
  std::reverse(zone_stack.begin(), zone_stack.end());
  return zone_stack;
}

const bNode *bNodeZoneType::get_corresponding_input(const bNodeTree &tree,
                                                    const bNode &output_bnode) const
{
  for (const bNode *node : tree.nodes_by_type(this->input_idname)) {
    if (this->get_corresponding_output_id(*node) == output_bnode.identifier) {
      return node;
    }
  }
  return nullptr;
}

const bNode *bNodeZoneType::get_corresponding_output(const bNodeTree &tree,
                                                     const bNode &input_bnode) const
{
  return tree.node_by_id(this->get_corresponding_output_id(input_bnode));
}

bNode *bNodeZoneType::get_corresponding_input(bNodeTree &tree, const bNode &output_bnode) const
{
  return const_cast<bNode *>(
      this->get_corresponding_input(const_cast<const bNodeTree &>(tree), output_bnode));
}

bNode *bNodeZoneType::get_corresponding_output(bNodeTree &tree, const bNode &input_bnode) const
{
  return const_cast<bNode *>(
      this->get_corresponding_output(const_cast<const bNodeTree &>(tree), input_bnode));
}

static Vector<const bNodeZoneType *> &get_zone_types_vector()
{
  static Vector<const bNodeZoneType *> zone_types;
  return zone_types;
};

void register_node_zone_type(const bNodeZoneType &zone_type)
{
  get_zone_types_vector().append(&zone_type);
}

Span<const bNodeZoneType *> all_zone_types()
{
  return get_zone_types_vector();
}

Span<int> all_zone_node_types()
{
  static const Vector<int> node_types = []() {
    Vector<int> node_types;
    for (const bNodeZoneType *zone_type : all_zone_types()) {
      node_types.append(zone_type->input_type);
      node_types.append(zone_type->output_type);
    }
    return node_types;
  }();
  return node_types;
}

Span<int> all_zone_input_node_types()
{
  static const Vector<int> node_types = []() {
    Vector<int> node_types;
    for (const bNodeZoneType *zone_type : all_zone_types()) {
      node_types.append(zone_type->input_type);
    }
    return node_types;
  }();
  return node_types;
}

Span<int> all_zone_output_node_types()
{
  static const Vector<int> node_types = []() {
    Vector<int> node_types;
    for (const bNodeZoneType *zone_type : all_zone_types()) {
      node_types.append(zone_type->output_type);
    }
    return node_types;
  }();
  return node_types;
}

const bNodeZoneType *zone_type_by_node_type(const int node_type)
{
  for (const bNodeZoneType *zone_type : all_zone_types()) {
    if (ELEM(node_type, zone_type->input_type, zone_type->output_type)) {
      return zone_type;
    }
  }
  return nullptr;
}

}  // namespace blender::bke

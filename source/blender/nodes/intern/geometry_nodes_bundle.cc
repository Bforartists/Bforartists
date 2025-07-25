/* SPDX-FileCopyrightText: 2025 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#include "BLI_cpp_type.hh"

#include "BKE_node_runtime.hh"

#include "NOD_geometry_nodes_bundle.hh"
#include "NOD_geometry_nodes_bundle_signature.hh"

namespace blender::nodes {

SocketInterfaceKey::SocketInterfaceKey(std::string identifier)
{
  identifiers_.append(std::move(identifier));
}

SocketInterfaceKey::SocketInterfaceKey(Vector<std::string> identifiers)
    : identifiers_(std::move(identifiers))
{
  BLI_assert(!identifiers_.is_empty());
}

Span<std::string> SocketInterfaceKey::identifiers() const
{
  return identifiers_;
}

bool SocketInterfaceKey::matches(const SocketInterfaceKey &other) const
{
  for (const std::string &identifier : other.identifiers_) {
    if (identifiers_.contains(identifier)) {
      return true;
    }
  }
  return false;
}

bool SocketInterfaceKey::matches_exactly(const SocketInterfaceKey &other) const
{
  for (const std::string &identifier : identifiers_) {
    if (std::none_of(
            other.identifiers_.begin(),
            other.identifiers_.end(),
            [&](const std::string &other_identifier) { return other_identifier == identifier; }))
    {
      return false;
    }
  }
  return true;
}

bool BundleSignature::matches_exactly(const BundleSignature &other) const
{
  if (items.size() != other.items.size()) {
    return false;
  }
  for (const Item &item : items) {
    if (std::none_of(other.items.begin(), other.items.end(), [&](const Item &other_item) {
          return item.key.matches_exactly(other_item.key);
        }))
    {
      return false;
    }
  }
  return true;
}

bool BundleSignature::all_matching_exactly(const Span<BundleSignature> signatures)
{
  if (signatures.is_empty()) {
    return true;
  }
  for (const BundleSignature &signature : signatures.drop_front(1)) {
    if (!signatures[0].matches_exactly(signature)) {
      return false;
    }
  }
  return true;
}

Bundle::Bundle() = default;

Bundle::~Bundle()
{
  for (StoredItem &item : items_) {
    item.type->geometry_nodes_cpp_type->destruct(item.value);
  }
  for (void *buffer : buffers_) {
    MEM_freeN(buffer);
  }
}

Bundle::Bundle(const Bundle &other)
{
  for (const StoredItem &item : other.items_) {
    this->add_new(item.key, *item.type, item.value);
  }
}

Bundle::Bundle(Bundle &&other) noexcept
    : items_(std::move(other.items_)), buffers_(std::move(other.buffers_))
{
}

Bundle &Bundle::operator=(const Bundle &other)
{
  if (this == &other) {
    return *this;
  }
  this->~Bundle();
  new (this) Bundle(other);
  return *this;
}

Bundle &Bundle::operator=(Bundle &&other) noexcept
{
  if (this == &other) {
    return *this;
  }
  this->~Bundle();
  new (this) Bundle(std::move(other));
  return *this;
}

void Bundle::add_new(SocketInterfaceKey key, const bke::bNodeSocketType &type, const void *value)
{
  BLI_assert(!this->contains(key));
  BLI_assert(type.geometry_nodes_cpp_type);
  const CPPType &cpp_type = *type.geometry_nodes_cpp_type;
  void *buffer = MEM_mallocN_aligned(cpp_type.size, cpp_type.alignment, __func__);
  cpp_type.copy_construct(value, buffer);
  items_.append(StoredItem{std::move(key), &type, buffer});
  buffers_.append(buffer);
}

bool Bundle::add(const SocketInterfaceKey &key,
                 const bke::bNodeSocketType &type,
                 const void *value)
{
  if (this->contains(key)) {
    return false;
  }
  this->add_new(key, type, value);
  return true;
}

bool Bundle::add(SocketInterfaceKey &&key, const bke::bNodeSocketType &type, const void *value)
{
  if (this->contains(key)) {
    return false;
  }
  this->add_new(std::move(key), type, value);
  return true;
}

std::optional<Bundle::Item> Bundle::lookup(const SocketInterfaceKey &key) const
{
  for (const StoredItem &item : items_) {
    if (item.key.matches(key)) {
      return Item{item.type, item.value};
    }
  }
  return std::nullopt;
}

bool Bundle::remove(const SocketInterfaceKey &key)
{
  const int removed_num = items_.remove_if([&key](StoredItem &item) {
    if (item.key.matches(key)) {
      item.type->geometry_nodes_cpp_type->destruct(item.value);
      return true;
    }
    return false;
  });
  return removed_num >= 1;
}

bool Bundle::contains(const SocketInterfaceKey &key) const
{
  for (const StoredItem &item : items_) {
    if (item.key.matches(key)) {
      return true;
    }
  }
  return false;
}

void Bundle::delete_self()
{
  MEM_delete(this);
}

BundleSignature BundleSignature::from_combine_bundle_node(const bNode &node)
{
  BLI_assert(node.is_type("GeometryNodeCombineBundle"));
  const auto &storage = *static_cast<const NodeGeometryCombineBundle *>(node.storage);
  BundleSignature signature;
  for (const int i : IndexRange(storage.items_num)) {
    const NodeGeometryCombineBundleItem &item = storage.items[i];
    if (const bke::bNodeSocketType *stype = bke::node_socket_type_find_static(item.socket_type)) {
      signature.items.append({nodes::SocketInterfaceKey(item.name), stype});
    }
  }
  return signature;
}

BundleSignature BundleSignature::from_separate_bundle_node(const bNode &node)
{
  BLI_assert(node.is_type("GeometryNodeSeparateBundle"));
  const auto &storage = *static_cast<const NodeGeometrySeparateBundle *>(node.storage);
  BundleSignature signature;
  for (const int i : IndexRange(storage.items_num)) {
    const NodeGeometrySeparateBundleItem &item = storage.items[i];
    if (const bke::bNodeSocketType *stype = bke::node_socket_type_find_static(item.socket_type)) {
      signature.items.append({nodes::SocketInterfaceKey(item.name), stype});
    }
  }
  return signature;
}

}  // namespace blender::nodes

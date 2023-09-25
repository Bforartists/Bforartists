/* SPDX-FileCopyrightText: 2019 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup depsgraph
 */

#include "intern/node/deg_node_factory.hh"

namespace blender::deg {

/* Global type registry */
static DepsNodeFactory *node_typeinfo_registry[int(NodeType::NUM_TYPES)] = {nullptr};

void register_node_typeinfo(DepsNodeFactory *factory)
{
  BLI_assert(factory != nullptr);
  const int type_as_int = int(factory->type());
  node_typeinfo_registry[type_as_int] = factory;
}

DepsNodeFactory *type_get_factory(const NodeType type)
{
  /* Look up type - at worst, it doesn't exist in table yet, and we fail. */
  const int type_as_int = int(type);
  return node_typeinfo_registry[type_as_int];
}

}  // namespace blender::deg

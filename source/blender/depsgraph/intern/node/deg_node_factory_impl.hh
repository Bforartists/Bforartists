/* SPDX-FileCopyrightText: 2019 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup depsgraph
 */

#pragma once

#include "intern/node/deg_node_factory.hh"

struct ID;

namespace blender::deg {

template<class ModeObjectType> NodeType DepsNodeFactoryImpl<ModeObjectType>::type() const
{
  return ModeObjectType::typeinfo.type;
}

template<class ModeObjectType> const char *DepsNodeFactoryImpl<ModeObjectType>::type_name() const
{
  return ModeObjectType::typeinfo.type_name;
}

template<class ModeObjectType> int DepsNodeFactoryImpl<ModeObjectType>::id_recalc_tag() const
{
  return ModeObjectType::typeinfo.id_recalc_tag;
}

template<class ModeObjectType>
Node *DepsNodeFactoryImpl<ModeObjectType>::create_node(const ID *id,
                                                       const char *subdata,
                                                       const char *name) const
{
  Node *node = new ModeObjectType();
  node->type = type();
  node->name = name;
  node->init(id, subdata);
  return node;
}

}  // namespace blender::deg

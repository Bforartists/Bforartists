/*
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software Foundation,
 * Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
 *
 * The Original Code is Copyright (C) 2013 Blender Foundation.
 * All rights reserved.
 */

/** \file
 * \ingroup depsgraph
 */

#pragma once

#include "intern/node/deg_node.h"

namespace blender {
namespace deg {

/* Time Source Node. */
struct TimeSourceNode : public Node {
  bool tagged_for_update = false;

  // TODO: evaluate() operation needed

  virtual void tag_update(Depsgraph *graph, eUpdateSource source) override;

  void flush_update_tag(Depsgraph *graph);

  DEG_DEPSNODE_DECLARE;
};

}  // namespace deg
}  // namespace blender

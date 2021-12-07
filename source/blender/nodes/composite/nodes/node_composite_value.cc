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
 * The Original Code is Copyright (C) 2006 Blender Foundation.
 * All rights reserved.
 */

/** \file
 * \ingroup cmpnodes
 */

#include "node_composite_util.hh"

/* **************** VALUE ******************** */

namespace blender::nodes {

static void cmp_node_value_declare(NodeDeclarationBuilder &b)
{
  b.add_output<decl::Float>(N_("Value")).default_value(0.5f);
}

}  // namespace blender::nodes

void register_node_type_cmp_value(void)
{
  static bNodeType ntype;

  cmp_node_type_base(&ntype, CMP_NODE_VALUE, "Value", NODE_CLASS_INPUT, 0);
  ntype.declare = blender::nodes::cmp_node_value_declare;
  node_type_size_preset(&ntype, NODE_SIZE_SMALL);

  nodeRegisterType(&ntype);
}

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

/* **************** SET ALPHA ******************** */

namespace blender::nodes {

static void cmp_node_setalpha_declare(NodeDeclarationBuilder &b)
{
  b.add_input<decl::Color>(N_("Image")).default_value({1.0f, 1.0f, 1.0f, 1.0f});
  b.add_input<decl::Float>(N_("Alpha")).default_value(1.0f).min(0.0f).max(1.0f);
  b.add_output<decl::Color>(N_("Image"));
}

}  // namespace blender::nodes

static void node_composit_init_setalpha(bNodeTree *UNUSED(ntree), bNode *node)
{
  NodeSetAlpha *settings = (NodeSetAlpha *)MEM_callocN(sizeof(NodeSetAlpha), __func__);
  node->storage = settings;
  settings->mode = CMP_NODE_SETALPHA_MODE_APPLY;
}

void register_node_type_cmp_setalpha(void)
{
  static bNodeType ntype;

  cmp_node_type_base(&ntype, CMP_NODE_SETALPHA, "Set Alpha", NODE_CLASS_CONVERTER, 0);
  ntype.declare = blender::nodes::cmp_node_setalpha_declare;
  node_type_init(&ntype, node_composit_init_setalpha);
  node_type_storage(
      &ntype, "NodeSetAlpha", node_free_standard_storage, node_copy_standard_storage);

  nodeRegisterType(&ntype);
}

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
 * The Original Code is Copyright (C) 2011 Blender Foundation.
 * All rights reserved.
 */

/** \file
 * \ingroup cmpnodes
 */

#include "BLT_translation.h"

#include "DNA_movieclip_types.h"

#include "BLI_math_base.h"

#include "node_composite_util.hh"

/* **************** Keying  ******************** */

namespace blender::nodes {

static void cmp_node_keying_declare(NodeDeclarationBuilder &b)
{
  b.add_input<decl::Color>(N_("Image")).default_value({0.8f, 0.8f, 0.8f, 1.0f});
  b.add_input<decl::Color>(N_("Key Color")).default_value({1.0f, 1.0f, 1.0f, 1.0f});
  b.add_input<decl::Float>(N_("Garbage Matte")).hide_value();
  b.add_input<decl::Float>(N_("Core Matte")).hide_value();
  b.add_output<decl::Color>(N_("Image"));
  b.add_output<decl::Float>(N_("Matte"));
  b.add_output<decl::Float>(N_("Edges"));
}

}  // namespace blender::nodes

static void node_composit_init_keying(bNodeTree *UNUSED(ntree), bNode *node)
{
  NodeKeyingData *data = (NodeKeyingData *)MEM_callocN(sizeof(NodeKeyingData), "node keying data");

  data->screen_balance = 0.5f;
  data->despill_balance = 0.5f;
  data->despill_factor = 1.0f;
  data->edge_kernel_radius = 3;
  data->edge_kernel_tolerance = 0.1f;
  data->clip_black = 0.0f;
  data->clip_white = 1.0f;
  node->storage = data;
}

void register_node_type_cmp_keying(void)
{
  static bNodeType ntype;

  cmp_node_type_base(&ntype, CMP_NODE_KEYING, "Keying", NODE_CLASS_MATTE, 0);
  ntype.declare = blender::nodes::cmp_node_keying_declare;
  node_type_init(&ntype, node_composit_init_keying);
  node_type_storage(
      &ntype, "NodeKeyingData", node_free_standard_storage, node_copy_standard_storage);

  nodeRegisterType(&ntype);
}

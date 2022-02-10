/* SPDX-License-Identifier: GPL-2.0-or-later
 * Copyright 2006 Blender Foundation. All rights reserved. */

/** \file
 * \ingroup cmpnodes
 */

#include "UI_interface.h"
#include "UI_resources.h"

#include "node_composite_util.hh"

/* **************** FILTER  ******************** */

namespace blender::nodes::node_composite_despeckle_cc {

static void cmp_node_despeckle_declare(NodeDeclarationBuilder &b)
{
  b.add_input<decl::Float>(N_("Fac")).default_value(1.0f).min(0.0f).max(1.0f).subtype(PROP_FACTOR);
  b.add_input<decl::Color>(N_("Image")).default_value({1.0f, 1.0f, 1.0f, 1.0f});
  b.add_output<decl::Color>(N_("Image"));
}

static void node_composit_init_despeckle(bNodeTree *UNUSED(ntree), bNode *node)
{
  node->custom3 = 0.5f;
  node->custom4 = 0.5f;
}

static void node_composit_buts_despeckle(uiLayout *layout, bContext *UNUSED(C), PointerRNA *ptr)
{
  uiLayout *col;

  col = uiLayoutColumn(layout, false);
  uiItemR(col, ptr, "threshold", UI_ITEM_R_SPLIT_EMPTY_NAME, nullptr, ICON_NONE);
  uiItemR(col, ptr, "threshold_neighbor", UI_ITEM_R_SPLIT_EMPTY_NAME, nullptr, ICON_NONE);
}

}  // namespace blender::nodes::node_composite_despeckle_cc

void register_node_type_cmp_despeckle()
{
  namespace file_ns = blender::nodes::node_composite_despeckle_cc;

  static bNodeType ntype;

  cmp_node_type_base(&ntype, CMP_NODE_DESPECKLE, "Despeckle", NODE_CLASS_OP_FILTER);
  ntype.declare = file_ns::cmp_node_despeckle_declare;
  ntype.draw_buttons = file_ns::node_composit_buts_despeckle;
  ntype.flag |= NODE_PREVIEW;
  node_type_init(&ntype, file_ns::node_composit_init_despeckle);

  nodeRegisterType(&ntype);
}

/* SPDX-License-Identifier: GPL-2.0-or-later
 * Copyright 2006 Blender Foundation. All rights reserved. */

/** \file
 * \ingroup cmpnodes
 */

#include "UI_interface.h"
#include "UI_resources.h"

#include "node_composite_util.hh"

/* **************** SCALAR MATH ******************** */

namespace blender::nodes::node_composite_ellipsemask_cc {

static void cmp_node_ellipsemask_declare(NodeDeclarationBuilder &b)
{
  b.add_input<decl::Float>(N_("Mask")).default_value(0.0f).min(0.0f).max(1.0f);
  b.add_input<decl::Float>(N_("Value")).default_value(1.0f).min(0.0f).max(1.0f);
  b.add_output<decl::Float>(N_("Mask"));
}

static void node_composit_init_ellipsemask(bNodeTree *UNUSED(ntree), bNode *node)
{
  NodeEllipseMask *data = MEM_cnew<NodeEllipseMask>(__func__);
  data->x = 0.5;
  data->y = 0.5;
  data->width = 0.2;
  data->height = 0.1;
  data->rotation = 0.0;
  node->storage = data;
}

static void node_composit_buts_ellipsemask(uiLayout *layout, bContext *UNUSED(C), PointerRNA *ptr)
{
  uiLayout *row;
  row = uiLayoutRow(layout, true);
  uiItemR(row, ptr, "x", UI_ITEM_R_SPLIT_EMPTY_NAME, nullptr, ICON_NONE);
  uiItemR(row, ptr, "y", UI_ITEM_R_SPLIT_EMPTY_NAME, nullptr, ICON_NONE);
  row = uiLayoutRow(layout, true);
  uiItemR(row, ptr, "width", UI_ITEM_R_SPLIT_EMPTY_NAME | UI_ITEM_R_SLIDER, nullptr, ICON_NONE);
  uiItemR(row, ptr, "height", UI_ITEM_R_SPLIT_EMPTY_NAME | UI_ITEM_R_SLIDER, nullptr, ICON_NONE);

  uiItemR(layout, ptr, "rotation", UI_ITEM_R_SPLIT_EMPTY_NAME, nullptr, ICON_NONE);
  uiItemR(layout, ptr, "mask_type", UI_ITEM_R_SPLIT_EMPTY_NAME, nullptr, ICON_NONE);
}

}  // namespace blender::nodes::node_composite_ellipsemask_cc

void register_node_type_cmp_ellipsemask()
{
  namespace file_ns = blender::nodes::node_composite_ellipsemask_cc;

  static bNodeType ntype;

  cmp_node_type_base(&ntype, CMP_NODE_MASK_ELLIPSE, "Ellipse Mask", NODE_CLASS_MATTE);
  ntype.declare = file_ns::cmp_node_ellipsemask_declare;
  ntype.draw_buttons = file_ns::node_composit_buts_ellipsemask;
  node_type_size(&ntype, 260, 110, 320);
  node_type_init(&ntype, file_ns::node_composit_init_ellipsemask);
  node_type_storage(
      &ntype, "NodeEllipseMask", node_free_standard_storage, node_copy_standard_storage);

  nodeRegisterType(&ntype);
}

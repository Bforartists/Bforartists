/* SPDX-License-Identifier: GPL-2.0-or-later
 * Copyright 2006 Blender Foundation. All rights reserved. */

/** \file
 * \ingroup cmpnodes
 */

#include "RNA_access.h"

#include "UI_interface.h"
#include "UI_resources.h"

#include "node_composite_util.hh"

/* ******************* Color Spill Suppression ********************************* */

namespace blender::nodes::node_composite_color_spill_cc {

static void cmp_node_color_spill_declare(NodeDeclarationBuilder &b)
{
  b.add_input<decl::Color>(N_("Image")).default_value({1.0f, 1.0f, 1.0f, 1.0f});
  b.add_input<decl::Float>(N_("Fac")).default_value(1.0f).min(0.0f).max(1.0f).subtype(PROP_FACTOR);
  b.add_output<decl::Color>(N_("Image"));
}

static void node_composit_init_color_spill(bNodeTree *UNUSED(ntree), bNode *node)
{
  NodeColorspill *ncs = MEM_cnew<NodeColorspill>(__func__);
  node->storage = ncs;
  node->custom1 = 2;    /* green channel */
  node->custom2 = 0;    /* simple limit algorithm */
  ncs->limchan = 0;     /* limit by red */
  ncs->limscale = 1.0f; /* limit scaling factor */
  ncs->unspill = 0;     /* do not use unspill */
}

static void node_composit_buts_color_spill(uiLayout *layout, bContext *UNUSED(C), PointerRNA *ptr)
{
  uiLayout *row, *col;

  uiItemL(layout, IFACE_("Despill Channel:"), ICON_NONE);
  row = uiLayoutRow(layout, false);
  uiItemR(row, ptr, "channel", UI_ITEM_R_SPLIT_EMPTY_NAME | UI_ITEM_R_EXPAND, nullptr, ICON_NONE);

  col = uiLayoutColumn(layout, false);
  uiItemR(col, ptr, "limit_method", UI_ITEM_R_SPLIT_EMPTY_NAME, nullptr, ICON_NONE);

  if (RNA_enum_get(ptr, "limit_method") == 0) {
    uiItemL(col, IFACE_("Limiting Channel:"), ICON_NONE);
    row = uiLayoutRow(col, false);
    uiItemR(row,
            ptr,
            "limit_channel",
            UI_ITEM_R_SPLIT_EMPTY_NAME | UI_ITEM_R_EXPAND,
            nullptr,
            ICON_NONE);
  }

  uiItemR(col, ptr, "ratio", UI_ITEM_R_SPLIT_EMPTY_NAME | UI_ITEM_R_SLIDER, nullptr, ICON_NONE);
  uiItemR(col, ptr, "use_unspill", UI_ITEM_R_SPLIT_EMPTY_NAME, nullptr, ICON_NONE);
  if (RNA_boolean_get(ptr, "use_unspill") == true) {
    uiItemR(col,
            ptr,
            "unspill_red",
            UI_ITEM_R_SPLIT_EMPTY_NAME | UI_ITEM_R_SLIDER,
            nullptr,
            ICON_NONE);
    uiItemR(col,
            ptr,
            "unspill_green",
            UI_ITEM_R_SPLIT_EMPTY_NAME | UI_ITEM_R_SLIDER,
            nullptr,
            ICON_NONE);
    uiItemR(col,
            ptr,
            "unspill_blue",
            UI_ITEM_R_SPLIT_EMPTY_NAME | UI_ITEM_R_SLIDER,
            nullptr,
            ICON_NONE);
  }
}

}  // namespace blender::nodes::node_composite_color_spill_cc

void register_node_type_cmp_color_spill()
{
  namespace file_ns = blender::nodes::node_composite_color_spill_cc;

  static bNodeType ntype;

  cmp_node_type_base(&ntype, CMP_NODE_COLOR_SPILL, "Color Spill", NODE_CLASS_MATTE);
  ntype.declare = file_ns::cmp_node_color_spill_declare;
  ntype.draw_buttons = file_ns::node_composit_buts_color_spill;
  node_type_init(&ntype, file_ns::node_composit_init_color_spill);
  node_type_storage(
      &ntype, "NodeColorspill", node_free_standard_storage, node_copy_standard_storage);

  nodeRegisterType(&ntype);
}

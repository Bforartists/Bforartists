/* SPDX-License-Identifier: GPL-2.0-or-later
 * Copyright 2006 Blender Foundation. All rights reserved. */

/** \file
 * \ingroup cmpnodes
 */

#include "UI_interface.h"
#include "UI_resources.h"

#include "node_composite_util.hh"

/* **************** Translate ******************** */

namespace blender::nodes::node_composite_translate_cc {

static void cmp_node_translate_declare(NodeDeclarationBuilder &b)
{
  b.add_input<decl::Color>(N_("Image")).default_value({1.0f, 1.0f, 1.0f, 1.0f});
  b.add_input<decl::Float>(N_("X")).default_value(0.0f).min(-10000.0f).max(10000.0f);
  b.add_input<decl::Float>(N_("Y")).default_value(0.0f).min(-10000.0f).max(10000.0f);
  b.add_output<decl::Color>(N_("Image"));
}

static void node_composit_init_translate(bNodeTree *UNUSED(ntree), bNode *node)
{
  NodeTranslateData *data = MEM_cnew<NodeTranslateData>(__func__);
  node->storage = data;
}

static void node_composit_buts_translate(uiLayout *layout, bContext *UNUSED(C), PointerRNA *ptr)
{
  uiItemR(layout, ptr, "use_relative", UI_ITEM_R_SPLIT_EMPTY_NAME, nullptr, ICON_NONE);
  uiItemR(layout, ptr, "wrap_axis", UI_ITEM_R_SPLIT_EMPTY_NAME, nullptr, ICON_NONE);
}

}  // namespace blender::nodes::node_composite_translate_cc

void register_node_type_cmp_translate()
{
  namespace file_ns = blender::nodes::node_composite_translate_cc;

  static bNodeType ntype;

  cmp_node_type_base(&ntype, CMP_NODE_TRANSLATE, "Translate", NODE_CLASS_DISTORT);
  ntype.declare = file_ns::cmp_node_translate_declare;
  ntype.draw_buttons = file_ns::node_composit_buts_translate;
  node_type_init(&ntype, file_ns::node_composit_init_translate);
  node_type_storage(
      &ntype, "NodeTranslateData", node_free_standard_storage, node_copy_standard_storage);

  nodeRegisterType(&ntype);
}

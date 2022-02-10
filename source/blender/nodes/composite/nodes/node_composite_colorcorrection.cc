/* SPDX-License-Identifier: GPL-2.0-or-later
 * Copyright 2006 Blender Foundation. All rights reserved. */

/** \file
 * \ingroup cmpnodes
 */

#include "UI_interface.h"
#include "UI_resources.h"

#include "node_composite_util.hh"

/* ******************* Color Correction ********************************* */

namespace blender::nodes::node_composite_colorcorrection_cc {

static void cmp_node_colorcorrection_declare(NodeDeclarationBuilder &b)
{
  b.add_input<decl::Color>(N_("Image")).default_value({1.0f, 1.0f, 1.0f, 1.0f});
  b.add_input<decl::Float>(N_("Mask")).default_value(1.0f).min(0.0f).max(1.0f);
  b.add_output<decl::Color>(N_("Image"));
}

static void node_composit_init_colorcorrection(bNodeTree *UNUSED(ntree), bNode *node)
{
  NodeColorCorrection *n = MEM_cnew<NodeColorCorrection>(__func__);
  n->startmidtones = 0.2f;
  n->endmidtones = 0.7f;
  n->master.contrast = 1.0f;
  n->master.gain = 1.0f;
  n->master.gamma = 1.0f;
  n->master.lift = 0.0f;
  n->master.saturation = 1.0f;
  n->midtones.contrast = 1.0f;
  n->midtones.gain = 1.0f;
  n->midtones.gamma = 1.0f;
  n->midtones.lift = 0.0f;
  n->midtones.saturation = 1.0f;
  n->shadows.contrast = 1.0f;
  n->shadows.gain = 1.0f;
  n->shadows.gamma = 1.0f;
  n->shadows.lift = 0.0f;
  n->shadows.saturation = 1.0f;
  n->highlights.contrast = 1.0f;
  n->highlights.gain = 1.0f;
  n->highlights.gamma = 1.0f;
  n->highlights.lift = 0.0f;
  n->highlights.saturation = 1.0f;
  node->custom1 = 7;  // red + green + blue enabled
  node->storage = n;
}

static void node_composit_buts_colorcorrection(uiLayout *layout,
                                               bContext *UNUSED(C),
                                               PointerRNA *ptr)
{
  uiLayout *row;

  row = uiLayoutRow(layout, false);
  uiItemR(row, ptr, "red", UI_ITEM_R_SPLIT_EMPTY_NAME, nullptr, ICON_NONE);
  uiItemR(row, ptr, "green", UI_ITEM_R_SPLIT_EMPTY_NAME, nullptr, ICON_NONE);
  uiItemR(row, ptr, "blue", UI_ITEM_R_SPLIT_EMPTY_NAME, nullptr, ICON_NONE);

  row = uiLayoutRow(layout, false);
  uiItemL(row, "", ICON_NONE);
  uiItemL(row, IFACE_("Saturation"), ICON_NONE);
  uiItemL(row, IFACE_("Contrast"), ICON_NONE);
  uiItemL(row, IFACE_("Gamma"), ICON_NONE);
  uiItemL(row, IFACE_("Gain"), ICON_NONE);
  uiItemL(row, IFACE_("Lift"), ICON_NONE);

  row = uiLayoutRow(layout, false);
  uiItemL(row, IFACE_("Master"), ICON_NONE);
  uiItemR(
      row, ptr, "master_saturation", UI_ITEM_R_SPLIT_EMPTY_NAME | UI_ITEM_R_SLIDER, "", ICON_NONE);
  uiItemR(
      row, ptr, "master_contrast", UI_ITEM_R_SPLIT_EMPTY_NAME | UI_ITEM_R_SLIDER, "", ICON_NONE);
  uiItemR(row, ptr, "master_gamma", UI_ITEM_R_SPLIT_EMPTY_NAME | UI_ITEM_R_SLIDER, "", ICON_NONE);
  uiItemR(row, ptr, "master_gain", UI_ITEM_R_SPLIT_EMPTY_NAME | UI_ITEM_R_SLIDER, "", ICON_NONE);
  uiItemR(row, ptr, "master_lift", UI_ITEM_R_SPLIT_EMPTY_NAME | UI_ITEM_R_SLIDER, "", ICON_NONE);

  row = uiLayoutRow(layout, false);
  uiItemL(row, IFACE_("Highlights"), ICON_NONE);
  uiItemR(row,
          ptr,
          "highlights_saturation",
          UI_ITEM_R_SPLIT_EMPTY_NAME | UI_ITEM_R_SLIDER,
          "",
          ICON_NONE);
  uiItemR(row,
          ptr,
          "highlights_contrast",
          UI_ITEM_R_SPLIT_EMPTY_NAME | UI_ITEM_R_SLIDER,
          "",
          ICON_NONE);
  uiItemR(
      row, ptr, "highlights_gamma", UI_ITEM_R_SPLIT_EMPTY_NAME | UI_ITEM_R_SLIDER, "", ICON_NONE);
  uiItemR(
      row, ptr, "highlights_gain", UI_ITEM_R_SPLIT_EMPTY_NAME | UI_ITEM_R_SLIDER, "", ICON_NONE);
  uiItemR(
      row, ptr, "highlights_lift", UI_ITEM_R_SPLIT_EMPTY_NAME | UI_ITEM_R_SLIDER, "", ICON_NONE);

  row = uiLayoutRow(layout, false);
  uiItemL(row, IFACE_("Midtones"), ICON_NONE);
  uiItemR(row,
          ptr,
          "midtones_saturation",
          UI_ITEM_R_SPLIT_EMPTY_NAME | UI_ITEM_R_SLIDER,
          "",
          ICON_NONE);
  uiItemR(
      row, ptr, "midtones_contrast", UI_ITEM_R_SPLIT_EMPTY_NAME | UI_ITEM_R_SLIDER, "", ICON_NONE);
  uiItemR(
      row, ptr, "midtones_gamma", UI_ITEM_R_SPLIT_EMPTY_NAME | UI_ITEM_R_SLIDER, "", ICON_NONE);
  uiItemR(row, ptr, "midtones_gain", UI_ITEM_R_SPLIT_EMPTY_NAME | UI_ITEM_R_SLIDER, "", ICON_NONE);
  uiItemR(row, ptr, "midtones_lift", UI_ITEM_R_SPLIT_EMPTY_NAME | UI_ITEM_R_SLIDER, "", ICON_NONE);

  row = uiLayoutRow(layout, false);
  uiItemL(row, IFACE_("Shadows"), ICON_NONE);
  uiItemR(row,
          ptr,
          "shadows_saturation",
          UI_ITEM_R_SPLIT_EMPTY_NAME | UI_ITEM_R_SLIDER,
          "",
          ICON_NONE);
  uiItemR(
      row, ptr, "shadows_contrast", UI_ITEM_R_SPLIT_EMPTY_NAME | UI_ITEM_R_SLIDER, "", ICON_NONE);
  uiItemR(row, ptr, "shadows_gamma", UI_ITEM_R_SPLIT_EMPTY_NAME | UI_ITEM_R_SLIDER, "", ICON_NONE);
  uiItemR(row, ptr, "shadows_gain", UI_ITEM_R_SPLIT_EMPTY_NAME | UI_ITEM_R_SLIDER, "", ICON_NONE);
  uiItemR(row, ptr, "shadows_lift", UI_ITEM_R_SPLIT_EMPTY_NAME | UI_ITEM_R_SLIDER, "", ICON_NONE);

  row = uiLayoutRow(layout, false);
  uiItemR(row,
          ptr,
          "midtones_start",
          UI_ITEM_R_SPLIT_EMPTY_NAME | UI_ITEM_R_SLIDER,
          nullptr,
          ICON_NONE);
  uiItemR(
      row, ptr, "midtones_end", UI_ITEM_R_SPLIT_EMPTY_NAME | UI_ITEM_R_SLIDER, nullptr, ICON_NONE);
}

static void node_composit_buts_colorcorrection_ex(uiLayout *layout,
                                                  bContext *UNUSED(C),
                                                  PointerRNA *ptr)
{
  uiLayout *row;

  row = uiLayoutRow(layout, false);
  uiItemR(row, ptr, "red", UI_ITEM_R_SPLIT_EMPTY_NAME, nullptr, ICON_NONE);
  uiItemR(row, ptr, "green", UI_ITEM_R_SPLIT_EMPTY_NAME, nullptr, ICON_NONE);
  uiItemR(row, ptr, "blue", UI_ITEM_R_SPLIT_EMPTY_NAME, nullptr, ICON_NONE);
  row = layout;
  uiItemL(row, IFACE_("Saturation"), ICON_NONE);
  uiItemR(row,
          ptr,
          "master_saturation",
          UI_ITEM_R_SPLIT_EMPTY_NAME | UI_ITEM_R_SLIDER,
          nullptr,
          ICON_NONE);
  uiItemR(row,
          ptr,
          "highlights_saturation",
          UI_ITEM_R_SPLIT_EMPTY_NAME | UI_ITEM_R_SLIDER,
          nullptr,
          ICON_NONE);
  uiItemR(row,
          ptr,
          "midtones_saturation",
          UI_ITEM_R_SPLIT_EMPTY_NAME | UI_ITEM_R_SLIDER,
          nullptr,
          ICON_NONE);
  uiItemR(row,
          ptr,
          "shadows_saturation",
          UI_ITEM_R_SPLIT_EMPTY_NAME | UI_ITEM_R_SLIDER,
          nullptr,
          ICON_NONE);

  uiItemL(row, IFACE_("Contrast"), ICON_NONE);
  uiItemR(row,
          ptr,
          "master_contrast",
          UI_ITEM_R_SPLIT_EMPTY_NAME | UI_ITEM_R_SLIDER,
          nullptr,
          ICON_NONE);
  uiItemR(row,
          ptr,
          "highlights_contrast",
          UI_ITEM_R_SPLIT_EMPTY_NAME | UI_ITEM_R_SLIDER,
          nullptr,
          ICON_NONE);
  uiItemR(row,
          ptr,
          "midtones_contrast",
          UI_ITEM_R_SPLIT_EMPTY_NAME | UI_ITEM_R_SLIDER,
          nullptr,
          ICON_NONE);
  uiItemR(row,
          ptr,
          "shadows_contrast",
          UI_ITEM_R_SPLIT_EMPTY_NAME | UI_ITEM_R_SLIDER,
          nullptr,
          ICON_NONE);

  uiItemL(row, IFACE_("Gamma"), ICON_NONE);
  uiItemR(
      row, ptr, "master_gamma", UI_ITEM_R_SPLIT_EMPTY_NAME | UI_ITEM_R_SLIDER, nullptr, ICON_NONE);
  uiItemR(row,
          ptr,
          "highlights_gamma",
          UI_ITEM_R_SPLIT_EMPTY_NAME | UI_ITEM_R_SLIDER,
          nullptr,
          ICON_NONE);
  uiItemR(row,
          ptr,
          "midtones_gamma",
          UI_ITEM_R_SPLIT_EMPTY_NAME | UI_ITEM_R_SLIDER,
          nullptr,
          ICON_NONE);
  uiItemR(row,
          ptr,
          "shadows_gamma",
          UI_ITEM_R_SPLIT_EMPTY_NAME | UI_ITEM_R_SLIDER,
          nullptr,
          ICON_NONE);

  uiItemL(row, IFACE_("Gain"), ICON_NONE);
  uiItemR(
      row, ptr, "master_gain", UI_ITEM_R_SPLIT_EMPTY_NAME | UI_ITEM_R_SLIDER, nullptr, ICON_NONE);
  uiItemR(row,
          ptr,
          "highlights_gain",
          UI_ITEM_R_SPLIT_EMPTY_NAME | UI_ITEM_R_SLIDER,
          nullptr,
          ICON_NONE);
  uiItemR(row,
          ptr,
          "midtones_gain",
          UI_ITEM_R_SPLIT_EMPTY_NAME | UI_ITEM_R_SLIDER,
          nullptr,
          ICON_NONE);
  uiItemR(
      row, ptr, "shadows_gain", UI_ITEM_R_SPLIT_EMPTY_NAME | UI_ITEM_R_SLIDER, nullptr, ICON_NONE);

  uiItemL(row, IFACE_("Lift"), ICON_NONE);
  uiItemR(
      row, ptr, "master_lift", UI_ITEM_R_SPLIT_EMPTY_NAME | UI_ITEM_R_SLIDER, nullptr, ICON_NONE);
  uiItemR(row,
          ptr,
          "highlights_lift",
          UI_ITEM_R_SPLIT_EMPTY_NAME | UI_ITEM_R_SLIDER,
          nullptr,
          ICON_NONE);
  uiItemR(row,
          ptr,
          "midtones_lift",
          UI_ITEM_R_SPLIT_EMPTY_NAME | UI_ITEM_R_SLIDER,
          nullptr,
          ICON_NONE);
  uiItemR(
      row, ptr, "shadows_lift", UI_ITEM_R_SPLIT_EMPTY_NAME | UI_ITEM_R_SLIDER, nullptr, ICON_NONE);

  row = uiLayoutRow(layout, false);
  uiItemR(row, ptr, "midtones_start", UI_ITEM_R_SPLIT_EMPTY_NAME, nullptr, ICON_NONE);
  uiItemR(row, ptr, "midtones_end", UI_ITEM_R_SPLIT_EMPTY_NAME, nullptr, ICON_NONE);
}

}  // namespace blender::nodes::node_composite_colorcorrection_cc

void register_node_type_cmp_colorcorrection()
{
  namespace file_ns = blender::nodes::node_composite_colorcorrection_cc;

  static bNodeType ntype;

  cmp_node_type_base(&ntype, CMP_NODE_COLORCORRECTION, "Color Correction", NODE_CLASS_OP_COLOR);
  ntype.declare = file_ns::cmp_node_colorcorrection_declare;
  ntype.draw_buttons = file_ns::node_composit_buts_colorcorrection;
  ntype.draw_buttons_ex = file_ns::node_composit_buts_colorcorrection_ex;
  node_type_size(&ntype, 400, 200, 600);
  node_type_init(&ntype, file_ns::node_composit_init_colorcorrection);
  node_type_storage(
      &ntype, "NodeColorCorrection", node_free_standard_storage, node_copy_standard_storage);

  nodeRegisterType(&ntype);
}

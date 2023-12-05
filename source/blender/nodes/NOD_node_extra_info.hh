/* SPDX-FileCopyrightText: 2005 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#pragma once

#include "UI_interface_c.hh"

namespace blender::nodes {

struct NodeExtraInfoRow {
  std::string text;
  int icon = 0;
  const char *tooltip = nullptr;

  uiButToolTipFunc tooltip_fn = nullptr;
  void *tooltip_fn_arg = nullptr;
  void (*tooltip_fn_free_arg)(void *) = nullptr;
};

struct NodeExtraInfoParams {
  Vector<NodeExtraInfoRow> &rows;
  const bNode &node;
  const bContext &C;
};

}  // namespace blender::nodes

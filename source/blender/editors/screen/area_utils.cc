/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup edscr
 *
 * Helper functions for area/region API.
 */

#include "BKE_screen.hh"

#include "BLI_rect.h"
#include "BLI_utildefines.h"

#include "WM_message.hh"

#include "ED_screen.hh"

#include "UI_interface.hh"

/* -------------------------------------------------------------------- */
/** \name Generic Tool System Region Callbacks
 * \{ */

void ED_region_generic_tools_region_message_subscribe(const wmRegionMessageSubscribeParams *params)
{
  wmMsgBus *mbus = params->message_bus;
  ARegion *region = params->region;

  wmMsgSubscribeValue msg_sub_value_region_tag_redraw{};
  msg_sub_value_region_tag_redraw.owner = region;
  msg_sub_value_region_tag_redraw.user_data = region;
  msg_sub_value_region_tag_redraw.notify = ED_region_do_msg_notify_tag_redraw;
  WM_msg_subscribe_rna_anon_prop(mbus, WorkSpace, tools, &msg_sub_value_region_tag_redraw);
}

int ED_region_generic_tools_region_snap_size(const ARegion *region, int size, int axis)
{
  /* bfa - re-add tabs to tool area, take tabs' width into account when snapping */
  float offset = 0.0;
  // check if panel has tabs visible
  if (region->panels_category_active.first &&
      region->panels_category_active.first != region->panels_category_active.last) {
    offset = 20;
  }

  if (axis == 0) {
    /* Using Y axis avoids slight feedback loop when adjusting X. */
    const float aspect = BLI_rctf_size_y(&region->v2d.cur) /
                         (BLI_rcti_size_y(&region->v2d.mask) + 1);
    const float column = UI_TOOLBAR_COLUMN / aspect;
    const float margin = UI_TOOLBAR_MARGIN / aspect;
    const float snap_units[] = {
        column + margin + offset, /* need bfa offset for tabs */
        (2.0f * column) + margin + offset,
        (2.7f * column) + margin + offset,
        (3.4f * column) + margin + offset,
    };
    int best_diff = INT_MAX;
    int best_size = size;
    /* Only snap if less than last snap unit. */
    if (size <= snap_units[ARRAY_SIZE(snap_units) - 1]) {
      for (uint i = 0; i < ARRAY_SIZE(snap_units); i += 1) {
        const int test_size = snap_units[i];
        const int test_diff = abs(test_size - size);
        if (test_diff < best_diff) {
          best_size = test_size;
          best_diff = test_diff;
        }
      }
    }
    return best_size;
  }
  return size;
}

/** \} */

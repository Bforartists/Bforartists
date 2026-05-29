/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup edscr
 *
 * Helper functions for area/region API.
 */

#include <limits>

#include "BKE_screen.hh"

#include "BLI_math_base.h"
#include "BLI_rect.h"
#include "BLI_utildefines.h"
#include "BLI_listbase.h"

#include "DNA_userdef_types.h"

#include "WM_message.hh"

#include "ED_screen.hh"

#include "UI_interface.hh"
#include "UI_interface_c.hh"

namespace blender {

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
  if (axis == 0) {
    /* Using Y axis avoids slight feedback loop when adjusting X.
     * BFA - Check if v2d is initialized before using it.
     * If not initialized (e.g., during early startup), return size unchanged
     * to avoid division by zero or invalid calculations. */
    const float v2d_cur_y = BLI_rctf_size_y(&region->v2d.cur);
    const int v2d_mask_y = BLI_rcti_size_y(&region->v2d.mask);
    if (v2d_cur_y <= 0.0f || v2d_mask_y <= 0) {
      return size;
    }
    const float aspect = v2d_cur_y / (v2d_mask_y + 1);
    const float column = UI_TOOLBAR_COLUMN / aspect;
    const float margin = UI_TOOLBAR_MARGIN / aspect;
    /* BFA - Calculate tabs width accounting for compact mode margin offset. */
    float tabs_width = 0.0f;
    if (!(region->flag & RGN_FLAG_HIDE_CATEGORY_TABS)) {
      const bool compact = (U.uiflag2 & USER_UIFLAG2_PANEL_TABS_COMPACT) != 0;
      tabs_width = (compact ? 28.0f : 20.0f) / aspect;
    }
    const float snap_units[] = {
        tabs_width + column + margin,
        tabs_width + (2.0f * column) + margin,
        tabs_width + (3.0f * column) + margin,
        tabs_width + (4.0f * column) + margin,
    };
    int best_diff = std::numeric_limits<int>::max();
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

int ED_region_generic_panel_region_snap_size(const ARegion *region, int size, int axis)
{
  if (axis == 0) {
    if (!ui::panel_category_tabs_is_visible(region)) {
      return size;
    }

    /* Using Y axis avoids slight feedback loop when adjusting X. */
    const float aspect = BLI_rctf_size_y(&region->v2d.cur) /
                         (BLI_rcti_size_y(&region->v2d.mask) + 1);
    return int(UI_PANEL_CATEGORY_MIN_WIDTH / aspect);
  }
  return size;
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name BFA Toolbar Column Preservation Helper
 * \{ */

/* Compute the snapped toolbar width that preserves column count across a tab width change
 * (e.g. toggling compact mode or tab visibility). The caller must pass old_min_sizex read
 * from snap_size(region, 0, 0) in the PREVIOUS flag state, with the NEW state already active. */
short ED_region_toolbar_snap_preserve_columns(const ARegion *region,
                                               short old_sizex,
                                               short old_min_sizex)
{
  if (!region->runtime || !region->runtime->type || !region->runtime->type->snap_size) {
    return old_sizex;
  }
  const float v2d_cur_y = BLI_rctf_size_y(&region->v2d.cur);
  const int v2d_mask_y = BLI_rcti_size_y(&region->v2d.mask);
  if (v2d_cur_y <= 0.0f || v2d_mask_y <= 0) {
    return old_sizex;
  }
  const float aspect = v2d_cur_y / float(v2d_mask_y + 1);
  const int col_width = max_ii(1, int(UI_TOOLBAR_COLUMN / aspect));
  const int cols = max_ii(1, int(roundf(float(old_sizex - old_min_sizex) / float(col_width))) + 1);
  const short new_min_sizex = region->runtime->type->snap_size(region, 0, 0);
  const short new_sizex = region->runtime->type->snap_size(
      region, new_min_sizex + (cols - 1) * col_width, 0);
  return (new_sizex > 0) ? new_sizex : old_sizex;
}

/** \} */

}  // namespace blender

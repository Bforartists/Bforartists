/* SPDX-FileCopyrightText: 2001-2002 NaN Holding BV. All rights reserved.
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup edtransform
 */

#include <cstdlib>
#include <fmt/format.h>

#include "BLI_math_vector.h"
#include "BLI_task.hh"

#include "BKE_report.hh"
#include "BKE_unit.hh"

#include "ED_screen.hh"

#include "WM_api.hh"
#include "WM_types.hh"

#include "BLT_translation.hh"

#include "transform.hh"
#include "transform_convert.hh"
#include "transform_snap.hh"

#include "transform_mode.hh"

namespace blender::ed::transform {

/* -------------------------------------------------------------------- */
/** \name Transform (Shrink-Fatten)
 * \{ */

static void transdata_elem_shrink_fatten(const TransInfo *t,
                                         const TransDataContainer * /*tc*/,
                                         TransData *td,
                                         const float distance)
{
  /* Get the final offset. */
  float tdistance = distance * td->factor;
  if (td->ext && (t->flag & T_ALT_TRANSFORM) != 0) {
    tdistance *= td->ext->iscale[0]; /* Shell factor. */
  }

  madd_v3_v3v3fl(td->loc, td->iloc, td->axismtx[2], tdistance);
}

static eRedrawFlag shrinkfatten_handleEvent(TransInfo *t, const wmEvent *event)
{
  if (t->redraw) {
    /* Event already handled. */
    return TREDRAW_NOTHING;
  }

  BLI_assert(t->mode == TFM_SHRINKFATTEN);
  const wmKeyMapItem *kmi = static_cast<const wmKeyMapItem *>(t->custom.mode.data);
  if (kmi && event->type == kmi->type && event->val == kmi->val) {
    /* Allows the "Even Thickness" effect to be enabled as a toggle. */
    t->flag ^= T_ALT_TRANSFORM;
    return TREDRAW_HARD;
  }
  return TREDRAW_NOTHING;
}

static void applyShrinkFatten(TransInfo *t)
{
  float distance;
  fmt::memory_buffer str;
  const UnitSettings &unit = t->scene->unit;

  distance = t->values[0] + t->values_modal_offset[0];

  transform_snap_increment(t, &distance);

  applyNumInput(&t->num, &distance);

  t->values_final[0] = distance;

  /* Header print for NumInput. */
  fmt::format_to(fmt::appender(str), "{}", IFACE_("Shrink/Fatten: "));
  if (hasNumInput(&t->num)) {
    char c[NUM_STR_REP_LEN];
    outputNumInput(&(t->num), c, unit);
    fmt::format_to(fmt::appender(str), "{}", c);
  }
  else {
    /* Default header print. */
    if (unit.system != USER_UNIT_NONE) {
      char unit_str[64];
      BKE_unit_value_as_string_scaled(
          unit_str, sizeof(unit_str), distance, 4, B_UNIT_LENGTH, unit, true);
      fmt::format_to(fmt::appender(str), "{}", unit_str);
    }
    else {
      fmt::format_to(fmt::appender(str), "{:.4f}", distance);
    }
  }

  if (t->proptext[0]) {
    fmt::format_to(fmt::appender(str), " {}", t->proptext);
  }
  fmt::format_to(fmt::appender(str), ", (");

  const wmKeyMapItem *kmi = static_cast<const wmKeyMapItem *>(t->custom.mode.data);
  if (kmi) {
    str.append(WM_keymap_item_to_string(kmi, false).value_or(""));
  }

  fmt::format_to(fmt::appender(str),
                 fmt::runtime(IFACE_(" or Alt) Even Thickness {}")),
                 WM_bool_as_string((t->flag & T_ALT_TRANSFORM) != 0));
  /* Done with header string. */

  FOREACH_TRANS_DATA_CONTAINER (t, tc) {
    threading::parallel_for(IndexRange(tc->data_len), 1024, [&](const IndexRange range) {
      for (const int i : range) {
        TransData *td = &tc->data[i];
        if (td->flag & TD_SKIP) {
          continue;
        }
        transdata_elem_shrink_fatten(t, tc, td, distance);
      }
    });
  }

  recalc_data(t);

  ED_area_status_text(t->area, fmt::to_string(str).c_str());
}

static void initShrinkFatten(TransInfo *t, wmOperator * /*op*/)
{
  if ((t->flag & T_EDIT) == 0 || (t->obedit_type != OB_MESH)) {
    BKE_report(t->reports, RPT_ERROR, "'Shrink/Fatten' meshes is only supported in edit mode");
    t->state = TRANS_CANCEL;
  }

  t->mode = TFM_SHRINKFATTEN;

  initMouseInputMode(t, &t->mouse, INPUT_VERTICAL_ABSOLUTE);

  t->idx_max = 0;
  t->num.idx_max = 0;
  t->snap[0] = 1.0f;
  t->snap[1] = t->snap[0] * 0.1f;

  copy_v3_fl(t->num.val_inc, t->snap[0]);
  t->num.unit_sys = t->scene->unit.system;
  t->num.unit_type[0] = B_UNIT_LENGTH;

  if (t->keymap) {
    /* Workaround to use the same key as the modal keymap. */
    t->custom.mode.data = (void *)WM_modalkeymap_find_propvalue(t->keymap, TFM_MODAL_RESIZE);
  }
}

/** \} */

TransModeInfo TransMode_shrinkfatten = {
    /*flags*/ T_NO_CONSTRAINT,
    /*init_fn*/ initShrinkFatten,
    /*transform_fn*/ applyShrinkFatten,
    /*transform_matrix_fn*/ nullptr,
    /*handle_event_fn*/ shrinkfatten_handleEvent,
    /*snap_distance_fn*/ nullptr,
    /*snap_apply_fn*/ nullptr,
    /*draw_fn*/ nullptr,
};

}  // namespace blender::ed::transform

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
 * The Original Code is Copyright (C) 2001-2002 by NaN Holding BV.
 * All rights reserved.
 */

/** \file
 * \ingroup edtransform
 */

#include <stdlib.h>

#include "DNA_anim_types.h"

#include "BLI_math.h"
#include "BLI_string.h"

#include "BKE_context.h"
#include "BKE_nla.h"
#include "BKE_unit.h"

#include "ED_screen.h"

#include "UI_interface.h"

#include "BLT_translation.h"

#include "transform.h"
#include "transform_mode.h"

/* -------------------------------------------------------------------- */
/* Transform (Animation Time Scale) */

/** \name Transform Animation Time Scale
 * \{ */

static void headerTimeScale(TransInfo *t, char str[UI_MAX_DRAW_STR])
{
  char tvec[NUM_STR_REP_LEN * 3];

  if (hasNumInput(&t->num)) {
    outputNumInput(&(t->num), tvec, &t->scene->unit);
  }
  else {
    BLI_snprintf(&tvec[0], NUM_STR_REP_LEN, "%.4f", t->values_final[0]);
  }

  BLI_snprintf(str, UI_MAX_DRAW_STR, TIP_("ScaleX: %s"), &tvec[0]);
}

static void applyTimeScaleValue(TransInfo *t, float value)
{
  Scene *scene = t->scene;
  const short autosnap = getAnimEdit_SnapMode(t);

  FOREACH_TRANS_DATA_CONTAINER (t, tc) {
    TransData *td = tc->data;
    TransData2D *td2d = tc->data_2d;
    for (int i = 0; i < tc->data_len; i++, td++, td2d++) {
      /* it is assumed that td->extra is a pointer to the AnimData,
       * whose active action is where this keyframe comes from
       * (this is only valid when not in NLA)
       */
      AnimData *adt = (t->spacetype != SPACE_NLA) ? td->extra : NULL;
      float startx = CFRA;
      float fac = value;

      /* take proportional editing into account */
      fac = ((fac - 1.0f) * td->factor) + 1;

      /* check if any need to apply nla-mapping */
      if (adt) {
        startx = BKE_nla_tweakedit_remap(adt, startx, NLATIME_CONVERT_UNMAP);
      }

      /* now, calculate the new value */
      *(td->val) = ((td->ival - startx) * fac) + startx;

      /* apply nearest snapping */
      doAnimEdit_SnapFrame(t, td, td2d, adt, autosnap);
    }
  }
}

static void applyTimeScale(TransInfo *t, const int UNUSED(mval[2]))
{
  char str[UI_MAX_DRAW_STR];

  /* handle numeric-input stuff */
  t->vec[0] = t->values[0];
  applyNumInput(&t->num, &t->vec[0]);
  t->values_final[0] = t->vec[0];
  headerTimeScale(t, str);

  applyTimeScaleValue(t, t->values_final[0]);

  recalcData(t);

  ED_area_status_text(t->area, str);
}

void initTimeScale(TransInfo *t)
{
  float center[2];

  /* this tool is only really available in the Action Editor
   * AND NLA Editor (for strip scaling)
   */
  if (ELEM(t->spacetype, SPACE_ACTION, SPACE_NLA) == 0) {
    t->state = TRANS_CANCEL;
  }

  t->mode = TFM_TIME_SCALE;
  t->transform = applyTimeScale;

  /* recalculate center2d to use CFRA and mouse Y, since that's
   * what is used in time scale */
  if ((t->flag & T_OVERRIDE_CENTER) == 0) {
    t->center_global[0] = t->scene->r.cfra;
    projectFloatView(t, t->center_global, center);
    center[1] = t->mouse.imval[1];
  }

  /* force a reinit with the center2d used here */
  initMouseInput(t, &t->mouse, center, t->mouse.imval, false);

  initMouseInputMode(t, &t->mouse, INPUT_SPRING_FLIP);

  t->flag |= T_NULL_ONE;
  t->num.val_flag[0] |= NUM_NULL_ONE;

  /* num-input has max of (n-1) */
  t->idx_max = 0;
  t->num.flag = 0;
  t->num.idx_max = t->idx_max;

  /* initialize snap like for everything else */
  t->snap[0] = 0.0f;
  t->snap[1] = t->snap[2] = 1.0f;

  copy_v3_fl(t->num.val_inc, t->snap[1]);
  t->num.unit_sys = t->scene->unit.system;
  t->num.unit_type[0] = B_UNIT_NONE;
}
/** \} */

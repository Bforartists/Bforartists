/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup animrig
 */

#include <cmath>
#include <string.h>

#include "ANIM_animdata.hh"
#include "ANIM_fcurve.hh"
#include "BKE_fcurve.h"
#include "BLI_math_vector_types.hh"
#include "DNA_anim_types.h"
#include "ED_anim_api.hh"
#include "MEM_guardedalloc.h"

namespace blender::animrig {

bool delete_keyframe_fcurve(AnimData *adt, FCurve *fcu, float cfra)
{
  bool found;

  const int index = BKE_fcurve_bezt_binarysearch_index(fcu->bezt, cfra, fcu->totvert, &found);
  if (!found) {
    return false;
  }

  /* Delete the key at the index (will sanity check + do recalc afterwards). */
  BKE_fcurve_delete_key(fcu, index);
  BKE_fcurve_handles_recalc(fcu);

  /* Empty curves get automatically deleted. */
  if (BKE_fcurve_is_empty(fcu)) {
    animdata_fcurve_delete(nullptr, adt, fcu);
  }

  return true;
}

/* ************************************************** */
/* KEYFRAME INSERTION */

/* -------------- BezTriple Insertion -------------------- */

/* Change the Y position of a keyframe to match the input, adjusting handles. */
static void replace_bezt_keyframe_ypos(BezTriple *dst, const BezTriple *bezt)
{
  /* Just change the values when replacing, so as to not overwrite handles. */
  float dy = bezt->vec[1][1] - dst->vec[1][1];

  /* Just apply delta value change to the handle values. */
  dst->vec[0][1] += dy;
  dst->vec[1][1] += dy;
  dst->vec[2][1] += dy;

  dst->f1 = bezt->f1;
  dst->f2 = bezt->f2;
  dst->f3 = bezt->f3;

  /* TODO: perform some other operations? */
}

int insert_bezt_fcurve(FCurve *fcu, const BezTriple *bezt, eInsertKeyFlags flag)
{
  int i = 0;

  /* Are there already keyframes? */
  if (fcu->bezt) {
    bool replace;
    i = BKE_fcurve_bezt_binarysearch_index(fcu->bezt, bezt->vec[1][0], fcu->totvert, &replace);

    /* Replace an existing keyframe? */
    if (replace) {
      /* 'i' may in rare cases exceed arraylen. */
      if ((i >= 0) && (i < fcu->totvert)) {
        if (flag & INSERTKEY_OVERWRITE_FULL) {
          fcu->bezt[i] = *bezt;
        }
        else {
          replace_bezt_keyframe_ypos(&fcu->bezt[i], bezt);
        }

        if (flag & INSERTKEY_CYCLE_AWARE) {
          /* If replacing an end point of a cyclic curve without offset,
           * modify the other end too. */
          if (ELEM(i, 0, fcu->totvert - 1) && BKE_fcurve_get_cycle_type(fcu) == FCU_CYCLE_PERFECT)
          {
            replace_bezt_keyframe_ypos(&fcu->bezt[i == 0 ? fcu->totvert - 1 : 0], bezt);
          }
        }
      }
    }
    /* Keyframing modes allow not replacing the keyframe. */
    else if ((flag & INSERTKEY_REPLACE) == 0) {
      /* Insert new - if we're not restricted to replacing keyframes only. */
      BezTriple *newb = static_cast<BezTriple *>(
          MEM_callocN((fcu->totvert + 1) * sizeof(BezTriple), "beztriple"));

      /* Add the beztriples that should occur before the beztriple to be pasted
       * (originally in fcu). */
      if (i > 0) {
        memcpy(newb, fcu->bezt, i * sizeof(BezTriple));
      }

      /* Add beztriple to paste at index i. */
      *(newb + i) = *bezt;

      /* Add the beztriples that occur after the beztriple to be pasted (originally in fcu). */
      if (i < fcu->totvert) {
        memcpy(newb + i + 1, fcu->bezt + i, (fcu->totvert - i) * sizeof(BezTriple));
      }

      /* Replace (+ free) old with new, only if necessary to do so. */
      MEM_freeN(fcu->bezt);
      fcu->bezt = newb;

      fcu->totvert++;
    }
    else {
      return -1;
    }
  }
  /* No keyframes yet, but can only add if...
   * 1) keyframing modes say that keyframes can only be replaced, so adding new ones won't know
   * 2) there are no samples on the curve
   *    NOTE: maybe we may want to allow this later when doing samples -> bezt conversions,
   *    but for now, having both is asking for trouble
   */
  else if ((flag & INSERTKEY_REPLACE) == 0 && (fcu->fpt == nullptr)) {
    /* Create new keyframes array. */
    fcu->bezt = static_cast<BezTriple *>(MEM_callocN(sizeof(BezTriple), "beztriple"));
    *(fcu->bezt) = *bezt;
    fcu->totvert = 1;
  }
  /* Cannot add anything. */
  else {
    /* Return error code -1 to prevent any misunderstandings. */
    return -1;
  }

  /* We need to return the index, so that some tools which do post-processing can
   * detect where we added the BezTriple in the array.
   */
  return i;
}

/**
 * Update the FCurve to allow insertion of `bezt` without modifying the curve shape.
 *
 * Checks whether it is necessary to apply Bezier subdivision due to involvement of non-auto
 * handles. If necessary, changes `bezt` handles from Auto to Aligned.
 *
 * \param bezt: key being inserted
 * \param prev: keyframe before that key
 * \param next: keyframe after that key
 */
static void subdivide_nonauto_handles(const FCurve *fcu,
                                      BezTriple *bezt,
                                      BezTriple *prev,
                                      BezTriple *next)
{
  if (prev->ipo != BEZT_IPO_BEZ || bezt->ipo != BEZT_IPO_BEZ) {
    return;
  }

  /* Don't change Vector handles, or completely auto regions. */
  const bool bezt_auto = BEZT_IS_AUTOH(bezt) || (bezt->h1 == HD_VECT && bezt->h2 == HD_VECT);
  const bool prev_auto = BEZT_IS_AUTOH(prev) || (prev->h2 == HD_VECT);
  const bool next_auto = BEZT_IS_AUTOH(next) || (next->h1 == HD_VECT);
  if (bezt_auto && prev_auto && next_auto) {
    return;
  }

  /* Subdivide the curve. */
  float delta;
  if (!BKE_fcurve_bezt_subdivide_handles(bezt, prev, next, &delta)) {
    return;
  }

  /* Decide when to force auto to manual. */
  if (!BEZT_IS_AUTOH(bezt)) {
    return;
  }
  if ((prev_auto || next_auto) && fcu->auto_smoothing == FCURVE_SMOOTH_CONT_ACCEL) {
    const float hx = bezt->vec[1][0] - bezt->vec[0][0];
    const float dx = bezt->vec[1][0] - prev->vec[1][0];

    /* This mode always uses 1/3 of key distance for handle x size. */
    const bool auto_works_well = fabsf(hx - dx / 3.0f) < 0.001f;
    if (auto_works_well) {
      return;
    }
  }

  /* Turn off auto mode. */
  bezt->h1 = bezt->h2 = HD_ALIGN;
}

void initialize_bezt(BezTriple *beztr,
                     const float2 position,
                     const eBezTriple_KeyframeType keyframe_type,
                     const eInsertKeyFlags flag,
                     const eFCurve_Flags fcu_flags)
{
  /* Set all three points, for nicer start position.
   * NOTE: +/- 1 on vec.x for left and right handles is so that 'free' handles work ok...
   */
  beztr->vec[0][0] = position.x - 1.0f;
  beztr->vec[0][1] = position.y;
  beztr->vec[1][0] = position.x;
  beztr->vec[1][1] = position.y;
  beztr->vec[2][0] = position.x + 1.0f;
  beztr->vec[2][1] = position.y;
  beztr->f1 = beztr->f2 = beztr->f3 = SELECT;

  /* Set default handle types and interpolation mode. */
  if (flag & INSERTKEY_NO_USERPREF) {
    /* For Py-API, we want scripts to have predictable behavior,
     * hence the option to not depend on the userpref defaults.
     */
    beztr->h1 = beztr->h2 = HD_AUTO_ANIM;
    beztr->ipo = BEZT_IPO_BEZ;
  }
  else {
    /* For UI usage - defaults should come from the user-preferences and/or tool-settings. */
    beztr->h1 = beztr->h2 = U.keyhandles_new; /* Use default handle type here. */

    /* Use default interpolation mode, with exceptions for int/discrete values. */
    beztr->ipo = U.ipo_new;
  }

  /* Interpolation type used is constrained by the type of values the curve can take. */
  if (fcu_flags & FCURVE_DISCRETE_VALUES) {
    beztr->ipo = BEZT_IPO_CONST;
  }
  else if ((beztr->ipo == BEZT_IPO_BEZ) && (fcu_flags & FCURVE_INT_VALUES)) {
    beztr->ipo = BEZT_IPO_LIN;
  }

  /* Set keyframe type value (supplied), which should come from the scene
   * settings in most cases. */
  BEZKEYTYPE(beztr) = keyframe_type;

  /* Set default values for "easing" interpolation mode settings.
   * NOTE: Even if these modes aren't currently used, if users switch
   *       to these later, we want these to work in a sane way out of
   *       the box.
   */

  /* "back" easing - This value used to be used when overshoot=0, but that
   *                 introduced discontinuities in how the param worked. */
  beztr->back = 1.70158f;

  /* "elastic" easing - Values here were hand-optimized for a default duration of
   *                    ~10 frames (typical motion-graph motion length). */
  beztr->amplitude = 0.8f;
  beztr->period = 4.1f;
}

int insert_vert_fcurve(
    FCurve *fcu, float x, float y, eBezTriple_KeyframeType keyframe_type, eInsertKeyFlags flag)
{
  BezTriple beztr = {{{0}}};
  initialize_bezt(&beztr, {x, y}, keyframe_type, flag, eFCurve_Flags(fcu->flag));

  uint oldTot = fcu->totvert;
  int a;

  /* Add temp beztriple to keyframes. */
  a = insert_bezt_fcurve(fcu, &beztr, flag);
  BKE_fcurve_active_keyframe_set(fcu, &fcu->bezt[a]);

  /* If `a` is negative return to avoid segfaults. */
  if (a < 0) {
    return -1;
  }

  /* Set handle-type and interpolation. */
  if ((fcu->totvert > 2) && (flag & INSERTKEY_REPLACE) == 0) {
    BezTriple *bezt = (fcu->bezt + a);

    /* Set interpolation from previous (if available),
     * but only if we didn't just replace some keyframe:
     * - Replacement is indicated by no-change in number of verts.
     * - When replacing, the user may have specified some interpolation that should be kept.
     */
    if (fcu->totvert > oldTot) {
      if (a > 0) {
        bezt->ipo = (bezt - 1)->ipo;
      }
      else if (a < fcu->totvert - 1) {
        bezt->ipo = (bezt + 1)->ipo;
      }

      if (0 < a && a < (fcu->totvert - 1) && (flag & INSERTKEY_OVERWRITE_FULL) == 0) {
        subdivide_nonauto_handles(fcu, bezt, bezt - 1, bezt + 1);
      }
    }
  }

  /* Don't recalculate handles if fast is set.
   * - this is a hack to make importers faster
   * - we may calculate twice (due to auto-handle needing to be calculated twice)
   */
  if ((flag & INSERTKEY_FAST) == 0) {
    BKE_fcurve_handles_recalc(fcu);
  }

  /* Return the index at which the keyframe was added. */
  return a;
}

}  // namespace blender::animrig

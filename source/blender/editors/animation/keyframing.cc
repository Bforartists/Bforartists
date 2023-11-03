/* SPDX-FileCopyrightText: 2009 Blender Authors, Joshua Leung. All rights reserved.
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup edanimation
 */

#include <cstddef>
#include <cstdio>

#include "MEM_guardedalloc.h"

#include "BLI_blenlib.h"

#include "BLT_translation.h"

#include "DNA_action_types.h"
#include "DNA_anim_types.h"
#include "DNA_armature_types.h"
#include "DNA_constraint_types.h"
#include "DNA_key_types.h"
#include "DNA_material_types.h"
#include "DNA_object_types.h"
#include "DNA_scene_types.h"

#include "BKE_action.h"
#include "BKE_anim_data.h"
#include "BKE_animsys.h"
#include "BKE_armature.h"
#include "BKE_context.h"
#include "BKE_fcurve.h"
#include "BKE_global.h"
#include "BKE_idtype.h"
#include "BKE_nla.h"
#include "BKE_report.h"
#include "BKE_scene.h"

#include "DEG_depsgraph.hh"
#include "DEG_depsgraph_build.hh"

#include "ED_keyframes_edit.hh"
#include "ED_keyframing.hh"
#include "ED_object.hh"
#include "ED_screen.hh"

#include "ANIM_bone_collections.h"
#include "ANIM_fcurve.hh"
#include "ANIM_keyframing.hh"
#include "ANIM_rna.hh"

#include "UI_interface.hh"
#include "UI_resources.hh"

#include "WM_api.hh"
#include "WM_types.hh"

#include "RNA_access.hh"
#include "RNA_define.hh"
#include "RNA_enum_types.hh"
#include "RNA_path.hh"
#include "RNA_prototypes.h"

#include "anim_intern.h"

static KeyingSet *keyingset_get_from_op_with_error(wmOperator *op,
                                                   PropertyRNA *prop,
                                                   Scene *scene);

static int delete_key_using_keying_set(bContext *C, wmOperator *op, KeyingSet *ks);

/* ************************************************** */
/* Keyframing Setting Wrangling */

eInsertKeyFlags ANIM_get_keyframing_flags(Scene *scene, const bool use_autokey_mode)
{
  using namespace blender::animrig;
  eInsertKeyFlags flag = INSERTKEY_NOFLAGS;

  /* standard flags */
  {
    /* visual keying */
    if (is_autokey_flag(scene, AUTOKEY_FLAG_AUTOMATKEY)) {
      flag |= INSERTKEY_MATRIX;
    }

    /* only needed */
    if (is_autokey_flag(scene, AUTOKEY_FLAG_INSERTNEEDED)) {
      flag |= INSERTKEY_NEEDED;
    }

    /* default F-Curve color mode - RGB from XYZ indices */
    if (is_autokey_flag(scene, AUTOKEY_FLAG_XYZ2RGB)) {
      flag |= INSERTKEY_XYZ2RGB;
    }
  }

  /* only if including settings from the autokeying mode... */
  if (use_autokey_mode) {
    /* keyframing mode - only replace existing keyframes */
    if (is_autokey_mode(scene, AUTOKEY_MODE_EDITKEYS)) {
      flag |= INSERTKEY_REPLACE;
    }

    /* cycle-aware keyframe insertion - preserve cycle period and flow */
    if (is_autokey_flag(scene, AUTOKEY_FLAG_CYCLEAWARE)) {
      flag |= INSERTKEY_CYCLE_AWARE;
    }
  }

  return flag;
}

/* ******************************************* */
/* Animation Data Validation */

bAction *ED_id_action_ensure(Main *bmain, ID *id)
{
  AnimData *adt;

  /* init animdata if none available yet */
  adt = BKE_animdata_from_id(id);
  if (adt == nullptr) {
    adt = BKE_animdata_ensure_id(id);
  }
  if (adt == nullptr) {
    /* if still none (as not allowed to add, or ID doesn't have animdata for some reason) */
    printf("ERROR: Couldn't add AnimData (ID = %s)\n", (id) ? (id->name) : "<None>");
    return nullptr;
  }

  /* init action if none available yet */
  /* TODO: need some wizardry to handle NLA stuff correct */
  if (adt->action == nullptr) {
    /* init action name from name of ID block */
    char actname[sizeof(id->name) - 2];
    SNPRINTF(actname, "%sAction", id->name + 2);

    /* create action */
    adt->action = BKE_action_add(bmain, actname);

    /* set ID-type from ID-block that this is going to be assigned to
     * so that users can't accidentally break actions by assigning them
     * to the wrong places
     */
    BKE_animdata_action_ensure_idroot(id, adt->action);

    /* Tag depsgraph to be rebuilt to include time dependency. */
    DEG_relations_tag_update(bmain);
  }

  DEG_id_tag_update(&adt->action->id, ID_RECALC_ANIMATION_NO_FLUSH);

  /* return the action */
  return adt->action;
}

/** Helper for #update_autoflags_fcurve(). */
void update_autoflags_fcurve_direct(FCurve *fcu, PropertyRNA *prop)
{
  /* set additional flags for the F-Curve (i.e. only integer values) */
  fcu->flag &= ~(FCURVE_INT_VALUES | FCURVE_DISCRETE_VALUES);
  switch (RNA_property_type(prop)) {
    case PROP_FLOAT:
      /* do nothing */
      break;
    case PROP_INT:
      /* do integer (only 'whole' numbers) interpolation between all points */
      fcu->flag |= FCURVE_INT_VALUES;
      break;
    default:
      /* do 'discrete' (i.e. enum, boolean values which cannot take any intermediate
       * values at all) interpolation between all points
       *    - however, we must also ensure that evaluated values are only integers still
       */
      fcu->flag |= (FCURVE_DISCRETE_VALUES | FCURVE_INT_VALUES);
      break;
  }
}

void update_autoflags_fcurve(FCurve *fcu, bContext *C, ReportList *reports, PointerRNA *ptr)
{
  PointerRNA tmp_ptr;
  PropertyRNA *prop;
  int old_flag = fcu->flag;

  if ((ptr->owner_id == nullptr) && (ptr->data == nullptr)) {
    BKE_report(reports, RPT_ERROR, "No RNA pointer available to retrieve values for this F-curve");
    return;
  }

  /* try to get property we should be affecting */
  if (RNA_path_resolve_property(ptr, fcu->rna_path, &tmp_ptr, &prop) == false) {
    /* property not found... */
    const char *idname = (ptr->owner_id) ? ptr->owner_id->name : TIP_("<No ID pointer>");

    BKE_reportf(reports,
                RPT_ERROR,
                "Could not update flags for this F-curve, as RNA path is invalid for the given ID "
                "(ID = %s, path = %s)",
                idname,
                fcu->rna_path);
    return;
  }

  /* update F-Curve flags */
  update_autoflags_fcurve_direct(fcu, prop);

  if (old_flag != fcu->flag) {
    /* Same as if keyframes had been changed */
    WM_event_add_notifier(C, NC_ANIMATION | ND_KEYFRAME | NA_EDITED, nullptr);
  }
}

/* ************************************************** */
/* KEYFRAME INSERTION */

/* -------------- BezTriple Insertion -------------------- */

/* Change the Y position of a keyframe to match the input, adjusting handles. */
static void replace_bezt_keyframe_ypos(BezTriple *dst, const BezTriple *bezt)
{
  /* just change the values when replacing, so as to not overwrite handles */
  float dy = bezt->vec[1][1] - dst->vec[1][1];

  /* just apply delta value change to the handle values */
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

  /* are there already keyframes? */
  if (fcu->bezt) {
    bool replace;
    i = BKE_fcurve_bezt_binarysearch_index(fcu->bezt, bezt->vec[1][0], fcu->totvert, &replace);

    /* replace an existing keyframe? */
    if (replace) {
      /* sanity check: 'i' may in rare cases exceed arraylen */
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
      /* insert new - if we're not restricted to replacing keyframes only */
      BezTriple *newb = static_cast<BezTriple *>(
          MEM_callocN((fcu->totvert + 1) * sizeof(BezTriple), "beztriple"));

      /* Add the beztriples that should occur before the beztriple to be pasted
       * (originally in fcu). */
      if (i > 0) {
        memcpy(newb, fcu->bezt, i * sizeof(BezTriple));
      }

      /* add beztriple to paste at index i */
      *(newb + i) = *bezt;

      /* add the beztriples that occur after the beztriple to be pasted (originally in fcu) */
      if (i < fcu->totvert) {
        memcpy(newb + i + 1, fcu->bezt + i, (fcu->totvert - i) * sizeof(BezTriple));
      }

      /* replace (+ free) old with new, only if necessary to do so */
      MEM_freeN(fcu->bezt);
      fcu->bezt = newb;

      fcu->totvert++;
    }
    else {
      return -1;
    }
  }
  /* no keyframes already, but can only add if...
   * 1) keyframing modes say that keyframes can only be replaced, so adding new ones won't know
   * 2) there are no samples on the curve
   *    NOTE: maybe we may want to allow this later when doing samples -> bezt conversions,
   *    but for now, having both is asking for trouble
   */
  else if ((flag & INSERTKEY_REPLACE) == 0 && (fcu->fpt == nullptr)) {
    /* create new keyframes array */
    fcu->bezt = static_cast<BezTriple *>(MEM_callocN(sizeof(BezTriple), "beztriple"));
    *(fcu->bezt) = *bezt;
    fcu->totvert = 1;
  }
  /* cannot add anything */
  else {
    /* return error code -1 to prevent any misunderstandings */
    return -1;
  }

  /* we need to return the index, so that some tools which do post-processing can
   * detect where we added the BezTriple in the array
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

int insert_vert_fcurve(
    FCurve *fcu, float x, float y, eBezTriple_KeyframeType keyframe_type, eInsertKeyFlags flag)
{
  BezTriple beztr = {{{0}}};
  uint oldTot = fcu->totvert;
  int a;

  /* set all three points, for nicer start position
   * NOTE: +/- 1 on vec.x for left and right handles is so that 'free' handles work ok...
   */
  beztr.vec[0][0] = x - 1.0f;
  beztr.vec[0][1] = y;
  beztr.vec[1][0] = x;
  beztr.vec[1][1] = y;
  beztr.vec[2][0] = x + 1.0f;
  beztr.vec[2][1] = y;
  beztr.f1 = beztr.f2 = beztr.f3 = SELECT;

  /* set default handle types and interpolation mode */
  if (flag & INSERTKEY_NO_USERPREF) {
    /* for Py-API, we want scripts to have predictable behavior,
     * hence the option to not depend on the userpref defaults
     */
    beztr.h1 = beztr.h2 = HD_AUTO_ANIM;
    beztr.ipo = BEZT_IPO_BEZ;
  }
  else {
    /* For UI usage - defaults should come from the user-preferences and/or tool-settings. */
    beztr.h1 = beztr.h2 = U.keyhandles_new; /* use default handle type here */

    /* use default interpolation mode, with exceptions for int/discrete values */
    beztr.ipo = U.ipo_new;
  }

  /* interpolation type used is constrained by the type of values the curve can take */
  if (fcu->flag & FCURVE_DISCRETE_VALUES) {
    beztr.ipo = BEZT_IPO_CONST;
  }
  else if ((beztr.ipo == BEZT_IPO_BEZ) && (fcu->flag & FCURVE_INT_VALUES)) {
    beztr.ipo = BEZT_IPO_LIN;
  }

  /* set keyframe type value (supplied), which should come from the scene settings in most cases */
  BEZKEYTYPE(&beztr) = keyframe_type;

  /* set default values for "easing" interpolation mode settings
   * NOTE: Even if these modes aren't currently used, if users switch
   *       to these later, we want these to work in a sane way out of
   *       the box.
   */

  /* "back" easing - this value used to be used when overshoot=0, but that
   *                 introduced discontinuities in how the param worked. */
  beztr.back = 1.70158f;

  /* "elastic" easing - values here were hand-optimized for a default duration of
   *                    ~10 frames (typical mograph motion length) */
  beztr.amplitude = 0.8f;
  beztr.period = 4.1f;

  /* add temp beztriple to keyframes */
  a = insert_bezt_fcurve(fcu, &beztr, flag);
  BKE_fcurve_active_keyframe_set(fcu, &fcu->bezt[a]);

  /* what if 'a' is a negative index?
   * for now, just exit to prevent any segfaults
   */
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

  /* don't recalculate handles if fast is set
   * - this is a hack to make importers faster
   * - we may calculate twice (due to auto-handle needing to be calculated twice)
   */
  if ((flag & INSERTKEY_FAST) == 0) {
    BKE_fcurve_handles_recalc(fcu);
  }

  /* return the index at which the keyframe was added */
  return a;
}

/* ------------------------- Insert Key API ------------------------- */

void ED_keyframes_add(FCurve *fcu, int num_keys_to_add)
{
  BLI_assert_msg(num_keys_to_add >= 0, "cannot remove keyframes with this function");

  if (num_keys_to_add == 0) {
    return;
  }

  fcu->bezt = static_cast<BezTriple *>(
      MEM_recallocN(fcu->bezt, sizeof(BezTriple) * (fcu->totvert + num_keys_to_add)));
  BezTriple *bezt = fcu->bezt + fcu->totvert; /* Pointer to the first new one. '*/

  fcu->totvert += num_keys_to_add;

  /* Iterate over the new keys to update their settings. */
  while (num_keys_to_add--) {
    /* Defaults, ignoring user-preference gives predictable results for API. */
    bezt->f1 = bezt->f2 = bezt->f3 = SELECT;
    bezt->ipo = BEZT_IPO_BEZ;
    bezt->h1 = bezt->h2 = HD_AUTO_ANIM;
    bezt++;
  }
}

/* ******************************************* */
/* KEYFRAME MODIFICATION */

/* mode for commonkey_modifykey */
enum {
  COMMONKEY_MODE_INSERT = 0,
  COMMONKEY_MODE_DELETE,
} /*eCommonModifyKey_Modes*/;

/**
 * Polling callback for use with `ANIM_*_keyframe()` operators
 * This is based on the standard ED_operator_areaactive callback,
 * except that it does special checks for a few space-types too.
 */
static bool modify_key_op_poll(bContext *C)
{
  ScrArea *area = CTX_wm_area(C);
  Scene *scene = CTX_data_scene(C);

  /* if no area or active scene */
  if (ELEM(nullptr, area, scene)) {
    return false;
  }

  /* should be fine */
  return true;
}

/* Insert Key Operator ------------------------ */

static int insert_key_exec(bContext *C, wmOperator *op)
{
  Scene *scene = CTX_data_scene(C);
  Object *obedit = CTX_data_edit_object(C);
  bool ob_edit_mode = false;

  const float cfra = BKE_scene_frame_get(scene);
  int num_channels;
  const bool confirm = op->flag & OP_IS_INVOKE;

  KeyingSet *ks = keyingset_get_from_op_with_error(op, op->type->prop, scene);
  if (ks == nullptr) {
    return OPERATOR_CANCELLED;
  }

  /* exit the edit mode to make sure that those object data properties that have been
   * updated since the last switching to the edit mode will be keyframed correctly
   */
  if (obedit && ANIM_keyingset_find_id(ks, (ID *)obedit->data)) {
    ED_object_mode_set(C, OB_MODE_OBJECT);
    ob_edit_mode = true;
  }

  /* try to insert keyframes for the channels specified by KeyingSet */
  num_channels = ANIM_apply_keyingset(C, nullptr, ks, MODIFYKEY_MODE_INSERT, cfra);
  if (G.debug & G_DEBUG) {
    BKE_reportf(op->reports,
                RPT_INFO,
                "Keying set '%s' - successfully added %d keyframes",
                ks->name,
                num_channels);
  }

  /* restore the edit mode if necessary */
  if (ob_edit_mode) {
    ED_object_mode_set(C, OB_MODE_EDIT);
  }

  /* report failure or do updates? */
  if (num_channels < 0) {
    BKE_report(op->reports, RPT_ERROR, "No suitable context info for active keying set");
    return OPERATOR_CANCELLED;
  }

  if (num_channels > 0) {
    /* send notifiers that keyframes have been changed */
    WM_event_add_notifier(C, NC_ANIMATION | ND_KEYFRAME | NA_ADDED, nullptr);
  }

  if (confirm) {
    /* if called by invoke (from the UI), make a note that we've inserted keyframes */
    if (num_channels > 0) {
      BKE_reportf(op->reports,
                  RPT_INFO,
                  "Successfully added %d keyframes for keying set '%s'",
                  num_channels,
                  ks->name);
    }
    else {
      BKE_report(op->reports, RPT_WARNING, "Keying set failed to insert any keyframes");
    }
  }

  return OPERATOR_FINISHED;
}

void ANIM_OT_keyframe_insert(wmOperatorType *ot)
{
  PropertyRNA *prop;

  /* identifiers */
  ot->name = "Insert Keyframe";
  ot->idname = "ANIM_OT_keyframe_insert";
  ot->description =
      "Insert keyframes on the current frame for all properties in the specified Keying Set";

  /* callbacks */
  ot->exec = insert_key_exec;
  ot->poll = modify_key_op_poll;

  /* flags */
  ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;

  /* keyingset to use (dynamic enum) */
  prop = RNA_def_enum(
      ot->srna, "type", rna_enum_dummy_DEFAULT_items, 0, "Keying Set", "The Keying Set to use");
  RNA_def_enum_funcs(prop, ANIM_keying_sets_enum_itemf);
  RNA_def_property_flag(prop, PROP_HIDDEN);
  ot->prop = prop;
}

void ANIM_OT_keyframe_insert_by_name(wmOperatorType *ot)
{
  PropertyRNA *prop;

  /* identifiers */
  ot->name = "Insert Keyframe (by name)";
  ot->idname = "ANIM_OT_keyframe_insert_by_name";
  ot->description = "Alternate access to 'Insert Keyframe' for keymaps to use";

  /* callbacks */
  ot->exec = insert_key_exec;
  ot->poll = modify_key_op_poll;

  /* flags */
  ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;

  /* keyingset to use (idname) */
  prop = RNA_def_string(
      ot->srna, "type", nullptr, MAX_ID_NAME - 2, "Keying Set", "The Keying Set to use");
  RNA_def_property_string_search_func_runtime(
      prop, ANIM_keyingset_visit_for_search_no_poll, PROP_STRING_SEARCH_SUGGESTION);
  RNA_def_property_flag(prop, PROP_HIDDEN);
  ot->prop = prop;
}

/* Insert Key Operator (With Menu) ------------------------ */
/* This operator checks if a menu should be shown for choosing the KeyingSet to use,
 * then calls the menu if necessary before
 */

static int insert_key_menu_invoke(bContext *C, wmOperator *op, const wmEvent * /*event*/)
{
  Scene *scene = CTX_data_scene(C);

  /* When there is an active keying set and no request to prompt, keyframe immediately. */
  if ((scene->active_keyingset != 0) && !RNA_boolean_get(op->ptr, "always_prompt")) {
    /* Just call the exec() on the active keying-set. */
    RNA_enum_set(op->ptr, "type", 0);
    return op->type->exec(C, op);
  }

  /* Show a menu listing all keying-sets, the enum is expanded here to make use of the
   * operator that accesses the keying-set by name. This is important for the ability
   * to assign shortcuts to arbitrarily named keying sets. See #89560.
   * These menu items perform the key-frame insertion (not this operator)
   * hence the #OPERATOR_INTERFACE return. */
  uiPopupMenu *pup = UI_popup_menu_begin(
      C, WM_operatortype_name(op->type, op->ptr).c_str(), ICON_NONE);
  uiLayout *layout = UI_popup_menu_layout(pup);

  /* Even though `ANIM_OT_keyframe_insert_menu` can show a menu in one line,
   * prefer `ANIM_OT_keyframe_insert_by_name` so users can bind keys to specific
   * keying sets by name in the key-map instead of the index which isn't stable. */
  PropertyRNA *prop = RNA_struct_find_property(op->ptr, "type");
  const EnumPropertyItem *item_array = nullptr;
  int totitem;
  bool free;

  RNA_property_enum_items_gettexted(C, op->ptr, prop, &item_array, &totitem, &free);

  for (int i = 0; i < totitem; i++) {
    const EnumPropertyItem *item = &item_array[i];
    if (item->identifier[0] != '\0') {
      uiItemStringO(layout,
                    item->name,
                    item->icon,
                    "ANIM_OT_keyframe_insert_by_name",
                    "type",
                    item->identifier);
    }
    else {
      /* This enum shouldn't contain headings, assert there are none.
       * NOTE: If in the future the enum includes them, additional layout code can be
       * added to show them - although that doesn't seem likely. */
      BLI_assert(item->name == nullptr);
      uiItemS(layout);
    }
  }

  if (free) {
    MEM_freeN((void *)item_array);
  }

  UI_popup_menu_end(C, pup);

  return OPERATOR_INTERFACE;
}

void ANIM_OT_keyframe_insert_menu(wmOperatorType *ot)
{
  PropertyRNA *prop;

  /* identifiers */
  ot->name = "Insert Keyframe Menu";
  ot->idname = "ANIM_OT_keyframe_insert_menu";
  ot->description =
      "Insert Keyframes for specified Keying Set, with menu of available Keying Sets if undefined";

  /* callbacks */
  ot->invoke = insert_key_menu_invoke;
  ot->exec = insert_key_exec;
  ot->poll = ED_operator_areaactive;

  /* flags */
  ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;

  /* keyingset to use (dynamic enum) */
  prop = RNA_def_enum(
      ot->srna, "type", rna_enum_dummy_DEFAULT_items, 0, "Keying Set", "The Keying Set to use");
  RNA_def_enum_funcs(prop, ANIM_keying_sets_enum_itemf);
  RNA_def_property_flag(prop, PROP_HIDDEN);
  ot->prop = prop;

  /* whether the menu should always be shown
   * - by default, the menu should only be shown when there is no active Keying Set (2.5 behavior),
   *   although in some cases it might be useful to always shown (pre 2.5 behavior)
   */
  prop = RNA_def_boolean(ot->srna, "always_prompt", false, "Always Show Menu", "");
  RNA_def_property_flag(prop, PROP_HIDDEN);
}

/* Delete Key Operator ------------------------ */

static int delete_key_exec(bContext *C, wmOperator *op)
{
  Scene *scene = CTX_data_scene(C);
  KeyingSet *ks = keyingset_get_from_op_with_error(op, op->type->prop, scene);
  if (ks == nullptr) {
    return OPERATOR_CANCELLED;
  }

  return delete_key_using_keying_set(C, op, ks);
}

static int delete_key_using_keying_set(bContext *C, wmOperator *op, KeyingSet *ks)
{
  Scene *scene = CTX_data_scene(C);
  float cfra = BKE_scene_frame_get(scene);
  int num_channels;
  const bool confirm = op->flag & OP_IS_INVOKE;

  /* try to delete keyframes for the channels specified by KeyingSet */
  num_channels = ANIM_apply_keyingset(C, nullptr, ks, MODIFYKEY_MODE_DELETE, cfra);
  if (G.debug & G_DEBUG) {
    printf("KeyingSet '%s' - Successfully removed %d Keyframes\n", ks->name, num_channels);
  }

  /* report failure or do updates? */
  if (num_channels < 0) {
    BKE_report(op->reports, RPT_ERROR, "No suitable context info for active keying set");
    return OPERATOR_CANCELLED;
  }

  if (num_channels > 0) {
    WM_event_add_notifier(C, NC_ANIMATION | ND_KEYFRAME | NA_REMOVED, nullptr);
  }

  if (confirm) {
    /* if called by invoke (from the UI), make a note that we've removed keyframes */
    if (num_channels > 0) {
      BKE_reportf(op->reports,
                  RPT_INFO,
                  "Successfully removed %d keyframes for keying set '%s'",
                  num_channels,
                  ks->name);
    }
    else {
      BKE_report(op->reports, RPT_WARNING, "Keying set failed to remove any keyframes");
    }
  }
  return OPERATOR_FINISHED;
}

void ANIM_OT_keyframe_delete(wmOperatorType *ot)
{
  PropertyRNA *prop;

  /* identifiers */
  ot->name = "Delete Keying-Set Keyframe";
  ot->idname = "ANIM_OT_keyframe_delete";
  ot->description =
      "Delete keyframes on the current frame for all properties in the specified Keying Set";

  /* callbacks */
  ot->exec = delete_key_exec;
  ot->poll = modify_key_op_poll;

  /* flags */
  ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;

  /* keyingset to use (dynamic enum) */
  prop = RNA_def_enum(
      ot->srna, "type", rna_enum_dummy_DEFAULT_items, 0, "Keying Set", "The Keying Set to use");
  RNA_def_enum_funcs(prop, ANIM_keying_sets_enum_itemf);
  RNA_def_property_flag(prop, PROP_HIDDEN);
  ot->prop = prop;
}

void ANIM_OT_keyframe_delete_by_name(wmOperatorType *ot)
{
  PropertyRNA *prop;

  /* identifiers */
  ot->name = "Delete Keying-Set Keyframe (by name)";
  ot->idname = "ANIM_OT_keyframe_delete_by_name";
  ot->description = "Alternate access to 'Delete Keyframe' for keymaps to use";

  /* callbacks */
  ot->exec = delete_key_exec;
  ot->poll = modify_key_op_poll;

  /* flags */
  ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;

  /* keyingset to use (idname) */
  prop = RNA_def_string(
      ot->srna, "type", nullptr, MAX_ID_NAME - 2, "Keying Set", "The Keying Set to use");
  RNA_def_property_string_search_func_runtime(
      prop, ANIM_keyingset_visit_for_search_no_poll, PROP_STRING_SEARCH_SUGGESTION);
  RNA_def_property_flag(prop, PROP_HIDDEN);
  ot->prop = prop;
}

/* Delete Key Operator ------------------------ */
/* NOTE: Although this version is simpler than the more generic version for KeyingSets,
 * it is more useful for animators working in the 3D view.
 */

static int clear_anim_v3d_exec(bContext *C, wmOperator * /*op*/)
{
  bool changed = false;

  CTX_DATA_BEGIN (C, Object *, ob, selected_objects) {
    /* just those in active action... */
    if ((ob->adt) && (ob->adt->action)) {
      AnimData *adt = ob->adt;
      bAction *act = adt->action;
      FCurve *fcu, *fcn;

      for (fcu = static_cast<FCurve *>(act->curves.first); fcu; fcu = fcn) {
        bool can_delete = false;

        fcn = fcu->next;

        /* in pose mode, only delete the F-Curve if it belongs to a selected bone */
        if (ob->mode & OB_MODE_POSE) {
          if (fcu->rna_path) {
            /* Get bone-name, and check if this bone is selected. */
            bPoseChannel *pchan = nullptr;
            char bone_name[sizeof(pchan->name)];
            if (BLI_str_quoted_substr(fcu->rna_path, "pose.bones[", bone_name, sizeof(bone_name)))
            {
              pchan = BKE_pose_channel_find_name(ob->pose, bone_name);
              /* Delete if bone is selected. */
              if ((pchan) && (pchan->bone)) {
                if (pchan->bone->flag & BONE_SELECTED) {
                  can_delete = true;
                }
              }
            }
          }
        }
        else {
          /* object mode - all of Object's F-Curves are affected */
          can_delete = true;
        }

        /* delete F-Curve completely */
        if (can_delete) {
          ANIM_fcurve_delete_from_animdata(nullptr, adt, fcu);
          DEG_id_tag_update(&ob->id, ID_RECALC_TRANSFORM);
          changed = true;
        }
      }

      /* Delete the action itself if it is empty. */
      if (ANIM_remove_empty_action_from_animdata(adt)) {
        changed = true;
      }
    }
  }
  CTX_DATA_END;

  if (!changed) {
    return OPERATOR_CANCELLED;
  }

  /* send updates */
  WM_event_add_notifier(C, NC_OBJECT | ND_KEYS, nullptr);

  return OPERATOR_FINISHED;
}

void ANIM_OT_keyframe_clear_v3d(wmOperatorType *ot)
{
  /* identifiers */
  ot->name = "Remove Animation";
  ot->description = "Remove all keyframe animation for selected objects";
  ot->idname = "ANIM_OT_keyframe_clear_v3d";

  /* callbacks */
  ot->invoke = WM_operator_confirm_or_exec;
  ot->exec = clear_anim_v3d_exec;

  ot->poll = ED_operator_areaactive;

  /* flags */
  ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;
  WM_operator_properties_confirm_or_exec(ot);
}

static int delete_key_v3d_without_keying_set(bContext *C, wmOperator *op)
{
  Scene *scene = CTX_data_scene(C);
  const float cfra = BKE_scene_frame_get(scene);

  int selected_objects_len = 0;
  int selected_objects_success_len = 0;
  int success_multi = 0;

  const bool confirm = op->flag & OP_IS_INVOKE;

  CTX_DATA_BEGIN (C, Object *, ob, selected_objects) {
    ID *id = &ob->id;
    int success = 0;

    selected_objects_len += 1;

    /* just those in active action... */
    if ((ob->adt) && (ob->adt->action)) {
      AnimData *adt = ob->adt;
      bAction *act = adt->action;
      FCurve *fcu, *fcn;
      const float cfra_unmap = BKE_nla_tweakedit_remap(adt, cfra, NLATIME_CONVERT_UNMAP);

      for (fcu = static_cast<FCurve *>(act->curves.first); fcu; fcu = fcn) {
        fcn = fcu->next;

        /* don't touch protected F-Curves */
        if (BKE_fcurve_is_protected(fcu)) {
          BKE_reportf(op->reports,
                      RPT_WARNING,
                      "Not deleting keyframe for locked F-Curve '%s', object '%s'",
                      fcu->rna_path,
                      id->name + 2);
          continue;
        }

        /* Special exception for bones, as this makes this operator more convenient to use
         * NOTE: This is only done in pose mode.
         * In object mode, we're dealing with the entire object.
         */
        if (ob->mode & OB_MODE_POSE) {
          bPoseChannel *pchan = nullptr;

          /* Get bone-name, and check if this bone is selected. */
          char bone_name[sizeof(pchan->name)];
          if (!BLI_str_quoted_substr(fcu->rna_path, "pose.bones[", bone_name, sizeof(bone_name))) {
            continue;
          }
          pchan = BKE_pose_channel_find_name(ob->pose, bone_name);

          /* skip if bone is not selected */
          if ((pchan) && (pchan->bone)) {
            /* bones are only selected/editable if visible... */
            bArmature *arm = (bArmature *)ob->data;

            /* skipping - not visible on currently visible layers */
            if (!ANIM_bonecoll_is_visible_pchan(arm, pchan)) {
              continue;
            }
            /* skipping - is currently hidden */
            if (pchan->bone->flag & BONE_HIDDEN_P) {
              continue;
            }

            /* selection flag... */
            if ((pchan->bone->flag & BONE_SELECTED) == 0) {
              continue;
            }
          }
        }

        /* delete keyframes on current frame
         * WARNING: this can delete the next F-Curve, hence the "fcn" copying
         */
        success += blender::animrig::delete_keyframe_fcurve(adt, fcu, cfra_unmap);
      }
      DEG_id_tag_update(&ob->adt->action->id, ID_RECALC_ANIMATION_NO_FLUSH);
    }

    /* Only for reporting. */
    if (success) {
      selected_objects_success_len += 1;
      success_multi += success;
    }

    DEG_id_tag_update(&ob->id, ID_RECALC_TRANSFORM);
  }
  CTX_DATA_END;

  if (selected_objects_success_len) {
    /* send updates */
    WM_event_add_notifier(C, NC_OBJECT | ND_KEYS, nullptr);
  }

  if (confirm) {
    /* if called by invoke (from the UI), make a note that we've removed keyframes */
    if (selected_objects_success_len) {
      BKE_reportf(op->reports,
                  RPT_INFO,
                  "%d object(s) successfully had %d keyframes removed",
                  selected_objects_success_len,
                  success_multi);
    }
    else {
      BKE_reportf(
          op->reports, RPT_ERROR, "No keyframes removed from %d object(s)", selected_objects_len);
    }
  }
  return OPERATOR_FINISHED;
}

static int delete_key_v3d_exec(bContext *C, wmOperator *op)
{
  Scene *scene = CTX_data_scene(C);
  KeyingSet *ks = ANIM_scene_get_active_keyingset(scene);

  if (ks == nullptr) {
    return delete_key_v3d_without_keying_set(C, op);
  }

  return delete_key_using_keying_set(C, op, ks);
}

void ANIM_OT_keyframe_delete_v3d(wmOperatorType *ot)
{
  /* identifiers */
  ot->name = "Delete Keyframe";
  ot->description = "Remove keyframes on current frame for selected objects and bones";
  ot->idname = "ANIM_OT_keyframe_delete_v3d";

  /* callbacks */
  ot->invoke = WM_operator_confirm_or_exec;
  ot->exec = delete_key_v3d_exec;

  ot->poll = ED_operator_areaactive;

  /* flags */
  ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;
  WM_operator_properties_confirm_or_exec(ot);
}

/* Insert Key Button Operator ------------------------ */

static int insert_key_button_exec(bContext *C, wmOperator *op)
{
  Main *bmain = CTX_data_main(C);
  Scene *scene = CTX_data_scene(C);
  ToolSettings *ts = scene->toolsettings;
  PointerRNA ptr = {nullptr};
  PropertyRNA *prop = nullptr;
  char *path;
  uiBut *but;
  const AnimationEvalContext anim_eval_context = BKE_animsys_eval_context_construct(
      CTX_data_depsgraph_pointer(C), BKE_scene_frame_get(scene));
  bool changed = false;
  int index;
  const bool all = RNA_boolean_get(op->ptr, "all");
  eInsertKeyFlags flag = INSERTKEY_NOFLAGS;

  /* flags for inserting keyframes */
  flag = ANIM_get_keyframing_flags(scene, true);

  if (!(but = UI_context_active_but_prop_get(C, &ptr, &prop, &index))) {
    /* pass event on if no active button found */
    return (OPERATOR_CANCELLED | OPERATOR_PASS_THROUGH);
  }

  if ((ptr.owner_id && ptr.data && prop) && RNA_property_animateable(&ptr, prop)) {
    if (ptr.type == &RNA_NlaStrip) {
      /* Handle special properties for NLA Strips, whose F-Curves are stored on the
       * strips themselves. These are stored separately or else the properties will
       * not have any effect.
       */
      NlaStrip *strip = static_cast<NlaStrip *>(ptr.data);
      FCurve *fcu = BKE_fcurve_find(&strip->fcurves, RNA_property_identifier(prop), index);

      if (fcu) {
        changed = blender::animrig::insert_keyframe_direct(
            op->reports,
            ptr,
            prop,
            fcu,
            &anim_eval_context,
            eBezTriple_KeyframeType(ts->keyframe_type),
            nullptr,
            eInsertKeyFlags(0));
      }
      else {
        BKE_report(op->reports,
                   RPT_ERROR,
                   "This property cannot be animated as it will not get updated correctly");
      }
    }
    else if (UI_but_flag_is_set(but, UI_BUT_DRIVEN)) {
      /* Driven property - Find driver */
      FCurve *fcu;
      bool driven, special;

      fcu = BKE_fcurve_find_by_rna_context_ui(
          C, &ptr, prop, index, nullptr, nullptr, &driven, &special);

      if (fcu && driven) {
        changed = blender::animrig::insert_keyframe_direct(
            op->reports,
            ptr,
            prop,
            fcu,
            &anim_eval_context,
            eBezTriple_KeyframeType(ts->keyframe_type),
            nullptr,
            INSERTKEY_DRIVER);
      }
    }
    else {
      /* standard properties */
      path = RNA_path_from_ID_to_property(&ptr, prop);

      if (path) {
        const char *identifier = RNA_property_identifier(prop);
        const char *group = nullptr;

        /* Special exception for keyframing transforms:
         * Set "group" for this manually, instead of having them appearing at the bottom
         * (ungrouped) part of the channels list.
         * Leaving these ungrouped is not a nice user behavior in this case.
         *
         * TODO: Perhaps we can extend this behavior in future for other properties...
         */
        if (ptr.type == &RNA_PoseBone) {
          bPoseChannel *pchan = static_cast<bPoseChannel *>(ptr.data);
          group = pchan->name;
        }
        else if ((ptr.type == &RNA_Object) &&
                 (strstr(identifier, "location") || strstr(identifier, "rotation") ||
                  strstr(identifier, "scale")))
        {
          /* NOTE: Keep this label in sync with the "ID" case in
           * keyingsets_utils.py :: get_transform_generators_base_info()
           */
          group = "Object Transforms";
        }

        if (all) {
          /* -1 indicates operating on the entire array (or the property itself otherwise) */
          index = -1;
        }

        changed = (blender::animrig::insert_keyframe(bmain,
                                                     op->reports,
                                                     ptr.owner_id,
                                                     nullptr,
                                                     group,
                                                     path,
                                                     index,
                                                     &anim_eval_context,
                                                     eBezTriple_KeyframeType(ts->keyframe_type),
                                                     flag) != 0);

        MEM_freeN(path);
      }
      else {
        BKE_report(op->reports,
                   RPT_WARNING,
                   "Failed to resolve path to property, "
                   "try manually specifying this using a Keying Set instead");
      }
    }
  }
  else {
    if (prop && !RNA_property_animateable(&ptr, prop)) {
      BKE_reportf(op->reports,
                  RPT_WARNING,
                  "\"%s\" property cannot be animated",
                  RNA_property_identifier(prop));
    }
    else {
      BKE_reportf(op->reports,
                  RPT_WARNING,
                  "Button doesn't appear to have any property information attached (ptr.data = "
                  "%p, prop = %p)",
                  ptr.data,
                  (void *)prop);
    }
  }

  if (changed) {
    ID *id = ptr.owner_id;
    AnimData *adt = BKE_animdata_from_id(id);
    if (adt->action != nullptr) {
      DEG_id_tag_update(&adt->action->id, ID_RECALC_ANIMATION_NO_FLUSH);
    }
    DEG_id_tag_update(id, ID_RECALC_ANIMATION_NO_FLUSH);

    /* send updates */
    UI_context_update_anim_flag(C);

    /* send notifiers that keyframes have been changed */
    WM_event_add_notifier(C, NC_ANIMATION | ND_KEYFRAME | NA_ADDED, nullptr);
  }

  return (changed) ? OPERATOR_FINISHED : OPERATOR_CANCELLED;
}

void ANIM_OT_keyframe_insert_button(wmOperatorType *ot)
{
  /* identifiers */
  ot->name = "Insert Keyframe (Buttons)";
  ot->idname = "ANIM_OT_keyframe_insert_button";
  ot->description = "Insert a keyframe for current UI-active property";

  /* callbacks */
  ot->exec = insert_key_button_exec;
  ot->poll = modify_key_op_poll;

  /* flags */
  ot->flag = OPTYPE_UNDO | OPTYPE_INTERNAL;

  /* properties */
  RNA_def_boolean(ot->srna, "all", true, "All", "Insert a keyframe for all element of the array");
}

/* Delete Key Button Operator ------------------------ */

static int delete_key_button_exec(bContext *C, wmOperator *op)
{
  Scene *scene = CTX_data_scene(C);
  PointerRNA ptr = {nullptr};
  PropertyRNA *prop = nullptr;
  Main *bmain = CTX_data_main(C);
  char *path;
  const float cfra = BKE_scene_frame_get(scene);
  bool changed = false;
  int index;
  const bool all = RNA_boolean_get(op->ptr, "all");

  if (!UI_context_active_but_prop_get(C, &ptr, &prop, &index)) {
    /* pass event on if no active button found */
    return (OPERATOR_CANCELLED | OPERATOR_PASS_THROUGH);
  }

  if (ptr.owner_id && ptr.data && prop) {
    if (BKE_nlastrip_has_curves_for_property(&ptr, prop)) {
      /* Handle special properties for NLA Strips, whose F-Curves are stored on the
       * strips themselves. These are stored separately or else the properties will
       * not have any effect.
       */
      ID *id = ptr.owner_id;
      NlaStrip *strip = static_cast<NlaStrip *>(ptr.data);
      FCurve *fcu = BKE_fcurve_find(&strip->fcurves, RNA_property_identifier(prop), 0);

      if (fcu) {
        if (BKE_fcurve_is_protected(fcu)) {
          BKE_reportf(
              op->reports,
              RPT_WARNING,
              "Not deleting keyframe for locked F-Curve for NLA Strip influence on %s - %s '%s'",
              strip->name,
              BKE_idtype_idcode_to_name(GS(id->name)),
              id->name + 2);
        }
        else {
          /* remove the keyframe directly
           * NOTE: cannot use delete_keyframe_fcurve(), as that will free the curve,
           *       and delete_keyframe() expects the FCurve to be part of an action
           */
          bool found = false;
          int i;

          /* try to find index of beztriple to get rid of */
          i = BKE_fcurve_bezt_binarysearch_index(fcu->bezt, cfra, fcu->totvert, &found);
          if (found) {
            /* delete the key at the index (will sanity check + do recalc afterwards) */
            BKE_fcurve_delete_key(fcu, i);
            BKE_fcurve_handles_recalc(fcu);
            changed = true;
          }
        }
      }
    }
    else {
      /* standard properties */
      path = RNA_path_from_ID_to_property(&ptr, prop);

      if (path) {
        if (all) {
          /* -1 indicates operating on the entire array (or the property itself otherwise) */
          index = -1;
        }

        changed = blender::animrig::delete_keyframe(
                      bmain, op->reports, ptr.owner_id, nullptr, path, index, cfra) != 0;
        MEM_freeN(path);
      }
      else if (G.debug & G_DEBUG) {
        printf("Button Delete-Key: no path to property\n");
      }
    }
  }
  else if (G.debug & G_DEBUG) {
    printf("ptr.data = %p, prop = %p\n", ptr.data, (void *)prop);
  }

  if (changed) {
    /* send updates */
    UI_context_update_anim_flag(C);

    /* send notifiers that keyframes have been changed */
    WM_event_add_notifier(C, NC_ANIMATION | ND_KEYFRAME | NA_REMOVED, nullptr);
  }

  return (changed) ? OPERATOR_FINISHED : OPERATOR_CANCELLED;
}

void ANIM_OT_keyframe_delete_button(wmOperatorType *ot)
{
  /* identifiers */
  ot->name = "Delete Keyframe (Buttons)";
  ot->idname = "ANIM_OT_keyframe_delete_button";
  ot->description = "Delete current keyframe of current UI-active property";

  /* callbacks */
  ot->exec = delete_key_button_exec;
  ot->poll = modify_key_op_poll;

  /* flags */
  ot->flag = OPTYPE_UNDO | OPTYPE_INTERNAL;

  /* properties */
  RNA_def_boolean(ot->srna, "all", true, "All", "Delete keyframes from all elements of the array");
}

/* Clear Key Button Operator ------------------------ */

static int clear_key_button_exec(bContext *C, wmOperator *op)
{
  PointerRNA ptr = {nullptr};
  PropertyRNA *prop = nullptr;
  Main *bmain = CTX_data_main(C);
  char *path;
  bool changed = false;
  int index;
  const bool all = RNA_boolean_get(op->ptr, "all");

  if (!UI_context_active_but_prop_get(C, &ptr, &prop, &index)) {
    /* pass event on if no active button found */
    return (OPERATOR_CANCELLED | OPERATOR_PASS_THROUGH);
  }

  if (ptr.owner_id && ptr.data && prop) {
    path = RNA_path_from_ID_to_property(&ptr, prop);

    if (path) {
      if (all) {
        /* -1 indicates operating on the entire array (or the property itself otherwise) */
        index = -1;
      }

      changed |=
          (blender::animrig::clear_keyframe(
               bmain, op->reports, ptr.owner_id, nullptr, path, index, eInsertKeyFlags(0)) != 0);
      MEM_freeN(path);
    }
    else if (G.debug & G_DEBUG) {
      printf("Button Clear-Key: no path to property\n");
    }
  }
  else if (G.debug & G_DEBUG) {
    printf("ptr.data = %p, prop = %p\n", ptr.data, (void *)prop);
  }

  if (changed) {
    /* send updates */
    UI_context_update_anim_flag(C);

    /* send notifiers that keyframes have been changed */
    WM_event_add_notifier(C, NC_ANIMATION | ND_KEYFRAME | NA_REMOVED, nullptr);
  }

  return (changed) ? OPERATOR_FINISHED : OPERATOR_CANCELLED;
}

void ANIM_OT_keyframe_clear_button(wmOperatorType *ot)
{
  /* identifiers */
  ot->name = "Clear Keyframe (Buttons)";
  ot->idname = "ANIM_OT_keyframe_clear_button";
  ot->description = "Clear all keyframes on the currently active property";

  /* callbacks */
  ot->exec = clear_key_button_exec;
  ot->poll = modify_key_op_poll;

  /* flags */
  ot->flag = OPTYPE_UNDO | OPTYPE_INTERNAL;

  /* properties */
  RNA_def_boolean(ot->srna, "all", true, "All", "Clear keyframes from all elements of the array");
}

/* ******************************************* */
/* KEYFRAME DETECTION */

/* --------------- API/Per-Datablock Handling ------------------- */

bool fcurve_frame_has_keyframe(const FCurve *fcu, float frame)
{
  /* quick sanity check */
  if (ELEM(nullptr, fcu, fcu->bezt)) {
    return false;
  }

  if ((fcu->flag & FCURVE_MUTED) == 0) {
    bool replace;
    int i = BKE_fcurve_bezt_binarysearch_index(fcu->bezt, frame, fcu->totvert, &replace);

    /* BKE_fcurve_bezt_binarysearch_index will set replace to be 0 or 1
     * - obviously, 1 represents a match
     */
    if (replace) {
      /* sanity check: 'i' may in rare cases exceed arraylen */
      if ((i >= 0) && (i < fcu->totvert)) {
        return true;
      }
    }
  }

  return false;
}

bool fcurve_is_changed(PointerRNA ptr,
                       PropertyRNA *prop,
                       FCurve *fcu,
                       const AnimationEvalContext *anim_eval_context)
{
  PathResolvedRNA anim_rna;
  anim_rna.ptr = ptr;
  anim_rna.prop = prop;
  anim_rna.prop_index = fcu->array_index;

  int index = fcu->array_index;
  blender::Vector<float> values = blender::animrig::get_rna_values(&ptr, prop);

  float fcurve_val = calculate_fcurve(&anim_rna, fcu, anim_eval_context);
  float cur_val = (index >= 0 && index < values.size()) ? values[index] : 0.0f;

  return !compare_ff_relative(fcurve_val, cur_val, FLT_EPSILON, 64);
}

/**
 * Checks whether an Action has a keyframe for a given frame
 * Since we're only concerned whether a keyframe exists,
 * we can simply loop until a match is found.
 */
static bool action_frame_has_keyframe(bAction *act, float frame)
{
  /* can only find if there is data */
  if (act == nullptr) {
    return false;
  }

  if (act->flag & ACT_MUTED) {
    return false;
  }

  /* loop over F-Curves, using binary-search to try to find matches
   * - this assumes that keyframes are only beztriples
   */
  LISTBASE_FOREACH (FCurve *, fcu, &act->curves) {
    /* only check if there are keyframes (currently only of type BezTriple) */
    if (fcu->bezt && fcu->totvert) {
      if (fcurve_frame_has_keyframe(fcu, frame)) {
        return true;
      }
    }
  }

  /* nothing found */
  return false;
}

/* Checks whether an Object has a keyframe for a given frame */
static bool object_frame_has_keyframe(Object *ob, float frame)
{
  /* error checking */
  if (ob == nullptr) {
    return false;
  }

  /* check own animation data - specifically, the action it contains */
  if ((ob->adt) && (ob->adt->action)) {
    /* #41525 - When the active action is a NLA strip being edited,
     * we need to correct the frame number to "look inside" the
     * remapped action
     */
    float ob_frame = BKE_nla_tweakedit_remap(ob->adt, frame, NLATIME_CONVERT_UNMAP);

    if (action_frame_has_keyframe(ob->adt->action, ob_frame)) {
      return true;
    }
  }

  /* nothing found */
  return false;
}

/* --------------- API ------------------- */

bool id_frame_has_keyframe(ID *id, float frame)
{
  /* sanity checks */
  if (id == nullptr) {
    return false;
  }

  /* perform special checks for 'macro' types */
  switch (GS(id->name)) {
    case ID_OB: /* object */
      return object_frame_has_keyframe((Object *)id, frame);
#if 0
    /* XXX TODO... for now, just use 'normal' behavior */
    case ID_SCE: /* scene */
      break;
#endif
    default: /* 'normal type' */
    {
      AnimData *adt = BKE_animdata_from_id(id);

      /* only check keyframes in active action */
      if (adt) {
        return action_frame_has_keyframe(adt->action, frame);
      }
      break;
    }
  }

  /* no keyframe found */
  return false;
}

/* -------------------------------------------------------------------- */
/** \name Internal Utilities
 * \{ */

/** Use for insert/delete key-frame. */
static KeyingSet *keyingset_get_from_op_with_error(wmOperator *op, PropertyRNA *prop, Scene *scene)
{
  KeyingSet *ks = nullptr;
  const int prop_type = RNA_property_type(prop);
  if (prop_type == PROP_ENUM) {
    int type = RNA_property_enum_get(op->ptr, prop);
    ks = ANIM_keyingset_get_from_enum_type(scene, type);
    if (ks == nullptr) {
      BKE_report(op->reports, RPT_ERROR, "No active Keying Set");
    }
  }
  else if (prop_type == PROP_STRING) {
    char type_id[MAX_ID_NAME - 2];
    RNA_property_string_get(op->ptr, prop, type_id);
    ks = ANIM_keyingset_get_from_idname(scene, type_id);

    if (ks == nullptr) {
      BKE_reportf(op->reports, RPT_ERROR, "Keying set '%s' not found", type_id);
    }
  }
  else {
    BLI_assert(0);
  }
  return ks;
}

/** \} */

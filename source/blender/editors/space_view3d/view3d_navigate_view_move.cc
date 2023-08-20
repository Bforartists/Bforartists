/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup spview3d
 */

#include "BLI_math_vector.h"

#include "BKE_context.h"

#include "WM_api.hh"

#include "RNA_access.hh"
#include "RNA_define.hh"

#include "ED_screen.hh"

#include "view3d_intern.h"
#include "view3d_navigate.hh" /* own include */

/* -------------------------------------------------------------------- */
/** \name View Move (Pan) Operator
 * \{ */

/* NOTE: these defines are saved in keymap files, do not change values but just add new ones */

void viewmove_modal_keymap(wmKeyConfig *keyconf)
{
  static const EnumPropertyItem modal_items[] = {
      {VIEW_MODAL_CANCEL, "CANCEL", 0, "Cancel", ""},
      {VIEW_MODAL_CONFIRM, "CONFIRM", 0, "Confirm", ""},

      {VIEWROT_MODAL_SWITCH_ZOOM, "SWITCH_TO_ZOOM", 0, "Switch to Zoom"},
      {VIEWROT_MODAL_SWITCH_ROTATE, "SWITCH_TO_ROTATE", 0, "Switch to Rotate"},

      {0, nullptr, 0, nullptr, nullptr},
  };

  wmKeyMap *keymap = WM_modalkeymap_find(keyconf, "View3D Move Modal");

  /* This function is called for each space-type, only needs to add map once. */
  if (keymap && keymap->modal_items) {
    return;
  }

  keymap = WM_modalkeymap_ensure(keyconf, "View3D Move Modal", modal_items);

  /* assign map to operators */
  WM_modalkeymap_assign(keymap, "VIEW3D_OT_move");
}

static int viewmove_modal_impl(bContext *C,
                               ViewOpsData *vod,
                               const eV3D_OpEvent event_code,
                               const int xy[2])
{
  bool use_autokey = false;
  int ret = OPERATOR_RUNNING_MODAL;

  switch (event_code) {
    case VIEW_APPLY: {
      viewmove_apply(vod, xy[0], xy[1]);
      if (ED_screen_animation_playing(CTX_wm_manager(C))) {
        use_autokey = true;
      }
      break;
    }
    case VIEW_CONFIRM: {
      use_autokey = true;
      ret = OPERATOR_FINISHED;
      break;
    }
    case VIEW_CANCEL: {
      vod->state_restore();
      ret = OPERATOR_CANCELLED;
      break;
    }
    case VIEW_PASS:
      break;
  }

  if (use_autokey) {
    ED_view3d_camera_lock_autokey(vod->v3d, vod->rv3d, C, false, true);
  }

  return ret;
}

static int viewmove_invoke_impl(bContext * /*C*/,
                                ViewOpsData *vod,
                                const wmEvent *event,
                                PointerRNA * /*ptr*/)
{
  eV3D_OpEvent event_code = event->type == MOUSEPAN ? VIEW_CONFIRM : VIEW_PASS;

  if (event_code == VIEW_CONFIRM) {
    /* Invert it, trackpad scroll follows same principle as 2d windows this way. */
    int mx = 2 * event->xy[0] - event->prev_xy[0];
    int my = 2 * event->xy[1] - event->prev_xy[1];
    viewmove_apply(vod, mx, my);
    return OPERATOR_FINISHED;
  }

  return OPERATOR_RUNNING_MODAL;
}

static int viewmove_invoke(bContext *C, wmOperator *op, const wmEvent *event)
{
  return view3d_navigate_invoke_impl(C, op, event, &ViewOpsType_move);
}

void VIEW3D_OT_move(wmOperatorType *ot)
{
  /* identifiers */
  ot->name = "Pan View";
  ot->description = "Move the view";
  ot->idname = ViewOpsType_move.idname;

  /* api callbacks */
  ot->invoke = viewmove_invoke;
  ot->modal = view3d_navigate_modal_fn;
  ot->poll = view3d_location_poll;
  ot->cancel = view3d_navigate_cancel_fn;

  /* flags */
  ot->flag = OPTYPE_BLOCKING | OPTYPE_GRAB_CURSOR_XY;

  /* properties */
  view3d_operator_properties_common(ot, V3D_OP_PROP_USE_MOUSE_INIT);
}

/** \} */

const ViewOpsType ViewOpsType_move = {
    /*flag*/ (VIEWOPS_FLAG_DEPTH_NAVIGATE | VIEWOPS_FLAG_INIT_ZFAC),
    /*idname*/ "VIEW3D_OT_move",
    /*poll_fn*/ view3d_location_poll,
    /*init_fn*/ viewmove_invoke_impl,
    /*apply_fn*/ viewmove_modal_impl,
};

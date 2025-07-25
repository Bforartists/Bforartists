/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup spview3d
 *
 * Interactive fly navigation modal operator (flying around in space).
 *
 * Defines #VIEW3D_OT_fly modal operator.
 *
 * \note Similar logic to `view3d_navigate_walk.cc` changes here may apply there too.
 */

#ifdef WITH_INPUT_NDOF
// #  define NDOF_FLY_DEBUG
/* NOTE(@ideasman42): is this needed for NDOF? commented so redraw doesn't thrash. */
// #  define NDOF_FLY_DRAW_TOOMUCH
#endif /* WITH_INPUT_NDOF */

#include "DNA_object_types.h"

#include "MEM_guardedalloc.h"

#include "BLI_math_matrix.h"
#include "BLI_math_rotation.h"
#include "BLI_math_vector.h"
#include "BLI_rect.h"
#include "BLI_time.h" /* Smooth-view. */

#include "BKE_context.hh"
#include "BKE_lib_id.hh"
#include "BKE_report.hh"
#include "BKE_screen.hh"

#include "BLT_translation.hh"

#include "WM_api.hh"
#include "WM_types.hh"

#include "ED_screen.hh"
#include "ED_space_api.hh"
#include "ED_undo.hh"

#include "UI_resources.hh"

#include "GPU_immediate.hh"

#include "view3d_intern.hh" /* own include */
#include "view3d_navigate.hh"

#include <fmt/format.h>

#include "BLI_strict_flags.h" /* IWYU pragma: keep. Keep last. */

/* -------------------------------------------------------------------- */
/** \name Modal Key-map
 * \{ */

/* NOTE: these defines are saved in keymap files,
 * do not change values but just add new ones */
enum {
  FLY_MODAL_CANCEL = 1,
  FLY_MODAL_CONFIRM,
  FLY_MODAL_ACCELERATE,
  FLY_MODAL_DECELERATE,
  FLY_MODAL_PAN_ENABLE,
  FLY_MODAL_PAN_DISABLE,
  FLY_MODAL_DIR_FORWARD,
  FLY_MODAL_DIR_BACKWARD,
  FLY_MODAL_DIR_LEFT,
  FLY_MODAL_DIR_RIGHT,
  FLY_MODAL_DIR_UP,
  FLY_MODAL_DIR_DOWN,
  FLY_MODAL_AXIS_LOCK_X,
  FLY_MODAL_AXIS_LOCK_Z,
  FLY_MODAL_PRECISION_ENABLE,
  FLY_MODAL_PRECISION_DISABLE,
  FLY_MODAL_FREELOOK_ENABLE,
  FLY_MODAL_FREELOOK_DISABLE,
  FLY_MODAL_SPEED, /* mouse-pan typically. */
};

/** Relative view axis locking - xlock, zlock. */
enum eFlyPanState {
  /** Disabled. */
  FLY_AXISLOCK_STATE_OFF = 0,
  /**
   * Enabled but not checking because mouse hasn't moved outside the margin since locking was
   * checked an not needed when the mouse moves, locking is set to 2 so checks are done.
   */
  FLY_AXISLOCK_STATE_IDLE = 1,
  /**
   * Mouse moved and checking needed,
   * if no view altering is done its changed back to #FLY_AXISLOCK_STATE_IDLE.
   */
  FLY_AXISLOCK_STATE_ACTIVE = 2,
};

void fly_modal_keymap(wmKeyConfig *keyconf)
{
  static const EnumPropertyItem modal_items[] = {
      {FLY_MODAL_CONFIRM, "CONFIRM", 0, "Confirm", ""},
      {FLY_MODAL_CANCEL, "CANCEL", 0, "Cancel", ""},

      {FLY_MODAL_DIR_FORWARD, "FORWARD", 0, "Forward", ""},
      {FLY_MODAL_DIR_BACKWARD, "BACKWARD", 0, "Backward", ""},
      {FLY_MODAL_DIR_LEFT, "LEFT", 0, "Left", ""},
      {FLY_MODAL_DIR_RIGHT, "RIGHT", 0, "Right", ""},
      {FLY_MODAL_DIR_UP, "UP", 0, "Up", ""},
      {FLY_MODAL_DIR_DOWN, "DOWN", 0, "Down", ""},

      {FLY_MODAL_PAN_ENABLE, "PAN_ENABLE", 0, "Pan", ""},
      {FLY_MODAL_PAN_DISABLE, "PAN_DISABLE", 0, "Pan (Off)", ""},

      {FLY_MODAL_ACCELERATE, "ACCELERATE", 0, "Accelerate", ""},
      {FLY_MODAL_DECELERATE, "DECELERATE", 0, "Decelerate", ""},

      {FLY_MODAL_AXIS_LOCK_X, "AXIS_LOCK_X", 0, "X Axis Correction", "X axis correction (toggle)"},
      {FLY_MODAL_AXIS_LOCK_Z, "AXIS_LOCK_Z", 0, "Z Axis Correction", "Z axis correction (toggle)"},

      {FLY_MODAL_PRECISION_ENABLE, "PRECISION_ENABLE", 0, "Precision", ""},
      {FLY_MODAL_PRECISION_DISABLE, "PRECISION_DISABLE", 0, "Precision (Off)", ""},

      {FLY_MODAL_FREELOOK_ENABLE, "FREELOOK_ENABLE", 0, "Rotation", ""},
      {FLY_MODAL_FREELOOK_DISABLE, "FREELOOK_DISABLE", 0, "Rotation (Off)", ""},

      {0, nullptr, 0, nullptr, nullptr},
  };

  wmKeyMap *keymap = WM_modalkeymap_find(keyconf, "View3D Fly Modal");

  /* This function is called for each space-type, only needs to add map once. */
  if (keymap && keymap->modal_items) {
    return;
  }

  keymap = WM_modalkeymap_ensure(keyconf, "View3D Fly Modal", modal_items);

  /* Assign map to operators. */
  WM_modalkeymap_assign(keymap, "VIEW3D_OT_fly");
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Internal Fly Structs
 * \{ */

struct FlyInfo {
  /* context stuff */
  RegionView3D *rv3d;
  View3D *v3d;
  ARegion *region;
  Depsgraph *depsgraph;
  Scene *scene;

  /** Needed for updating that isn't triggered by input. */
  wmTimer *timer;

  short state;
  bool redraw;
  bool use_precision;
  /** If the user presses shift they can look about without moving the direction there looking. */
  bool use_freelook;

  /**
   * Needed for auto-keyframing, when animation isn't playing, only keyframe on confirmation.
   *
   * Currently we can't cancel this operator usefully while recording on animation playback
   * (this would need to un-key all previous frames).
   */
  bool anim_playing;

  /** Latest 2D mouse values. */
  int mval[2];
  /** Center mouse values. */
  int center_mval[2];
  /** Camera viewport size. */
  float viewport_size[2];

#ifdef WITH_INPUT_NDOF
  /** Latest 3D mouse values. */
  wmNDOFMotionData *ndof;
#endif

  /* Fly state. */
  /** The speed the view is moving per redraw. */
  float speed;
  /** Axis index to move along by default Z to move along the view. */
  short axis;
  /** When true, pan the view instead of rotating. */
  bool pan_view;

  eFlyPanState xlock, zlock;
  /** Nicer dynamics. */
  float xlock_momentum, zlock_momentum;
  /** World scale 1.0 default. */
  float grid;

  /* Compare between last state. */
  /** Used to accelerate when using the mouse-wheel a lot. */
  double time_lastwheel;
  /** Time between draws. */
  double time_lastdraw;

  void *draw_handle_pixel;

  /** Keep the previous value to smooth transitions (use lag). */
  float dvec_prev[3];

  View3DCameraControl *v3d_camera_control;
};

/** \} */

/* -------------------------------------------------------------------- */
/** \name Internal Fly Drawing
 * \{ */

/* Prototypes. */
#ifdef WITH_INPUT_NDOF
static void flyApply_ndof(bContext *C, FlyInfo *fly, bool is_confirm);
#endif /* WITH_INPUT_NDOF */
static int flyApply(bContext *C, FlyInfo *fly, bool is_confirm);

static void drawFlyPixel(const bContext * /*C*/, ARegion * /*region*/, void *arg)
{
  FlyInfo *fly = static_cast<FlyInfo *>(arg);
  rctf viewborder;
  int xoff, yoff;

  if (ED_view3d_cameracontrol_object_get(fly->v3d_camera_control)) {
    ED_view3d_calc_camera_border(
        fly->scene, fly->depsgraph, fly->region, fly->v3d, fly->rv3d, false, &viewborder);
    xoff = int(viewborder.xmin);
    yoff = int(viewborder.ymin);
  }
  else {
    xoff = 0;
    yoff = 0;
  }

  /* Draws 4 edge brackets that frame the safe area where the
   * mouse can move during fly mode without spinning the view. */

  const float x1 = float(xoff) + 0.45f * fly->viewport_size[0];
  const float y1 = float(yoff) + 0.45f * fly->viewport_size[1];
  const float x2 = float(xoff) + 0.55f * fly->viewport_size[0];
  const float y2 = float(yoff) + 0.55f * fly->viewport_size[1];

  GPUVertFormat *format = immVertexFormat();
  uint pos = GPU_vertformat_attr_add(format, "pos", blender::gpu::VertAttrType::SFLOAT_32_32);

  immBindBuiltinProgram(GPU_SHADER_3D_UNIFORM_COLOR);

  immUniformThemeColor3(TH_VIEW_OVERLAY);

  immBegin(GPU_PRIM_LINES, 16);

  /* Bottom left. */
  immVertex2f(pos, x1, y1);
  immVertex2f(pos, x1, y1 + 5);

  immVertex2f(pos, x1, y1);
  immVertex2f(pos, x1 + 5, y1);

  /* Top right. */
  immVertex2f(pos, x2, y2);
  immVertex2f(pos, x2, y2 - 5);

  immVertex2f(pos, x2, y2);
  immVertex2f(pos, x2 - 5, y2);

  /* Top left. */
  immVertex2f(pos, x1, y2);
  immVertex2f(pos, x1, y2 - 5);

  immVertex2f(pos, x1, y2);
  immVertex2f(pos, x1 + 5, y2);

  /* Bottom right. */
  immVertex2f(pos, x2, y1);
  immVertex2f(pos, x2, y1 + 5);

  immVertex2f(pos, x2, y1);
  immVertex2f(pos, x2 - 5, y1);

  immEnd();
  immUnbindProgram();
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Internal Fly Logic
 * \{ */

/** FlyInfo::state */
enum {
  FLY_RUNNING = 0,
  FLY_CANCEL = 1,
  FLY_CONFIRM = 2,
};

static bool initFlyInfo(bContext *C, FlyInfo *fly, wmOperator *op, const wmEvent *event)
{
  wmWindowManager *wm = CTX_wm_manager(C);
  wmWindow *win = CTX_wm_window(C);
  rctf viewborder;

  float upvec[3];
  float mat[3][3];

  fly->rv3d = CTX_wm_region_view3d(C);
  fly->v3d = CTX_wm_view3d(C);
  fly->region = CTX_wm_region(C);
  fly->depsgraph = CTX_data_expect_evaluated_depsgraph(C);
  fly->scene = CTX_data_scene(C);

#ifdef NDOF_FLY_DEBUG
  puts("\n-- fly begin --");
#endif

  /* Sanity check: for rare but possible case (if lib-linking the camera fails). */
  if ((fly->rv3d->persp == RV3D_CAMOB) && (fly->v3d->camera == nullptr)) {
    fly->rv3d->persp = RV3D_PERSP;
  }

  if (fly->rv3d->persp == RV3D_CAMOB &&
      !BKE_id_is_editable(CTX_data_main(C), &fly->v3d->camera->id))
  {
    BKE_report(op->reports,
               RPT_ERROR,
               "Cannot navigate a camera from an external library or non-editable override");

    return false;
  }

  if (ED_view3d_offset_lock_check(fly->v3d, fly->rv3d)) {
    BKE_report(op->reports, RPT_ERROR, "Cannot fly when the view offset is locked");
    return false;
  }

  if (fly->rv3d->persp == RV3D_CAMOB && fly->v3d->camera->constraints.first) {
    BKE_report(op->reports, RPT_ERROR, "Cannot fly an object with constraints");
    return false;
  }

  fly->state = FLY_RUNNING;
  fly->speed = 0.0f;
  fly->axis = 2;
  fly->pan_view = false;
  fly->xlock = FLY_AXISLOCK_STATE_OFF;
  fly->zlock = FLY_AXISLOCK_STATE_OFF;
  fly->xlock_momentum = 0.0f;
  fly->zlock_momentum = 0.0f;
  fly->grid = 1.0f;
  fly->use_precision = false;
  fly->use_freelook = false;
  fly->anim_playing = ED_screen_animation_playing(wm);

#ifdef NDOF_FLY_DRAW_TOOMUCH
  fly->redraw = 1;
#endif
  zero_v3(fly->dvec_prev);

  fly->timer = WM_event_timer_add(CTX_wm_manager(C), win, TIMER, 0.01f);

  copy_v2_v2_int(fly->mval, event->mval);

#ifdef WITH_INPUT_NDOF
  fly->ndof = nullptr;
#endif

  fly->time_lastdraw = fly->time_lastwheel = BLI_time_now_seconds();

  fly->draw_handle_pixel = ED_region_draw_cb_activate(
      fly->region->runtime->type, drawFlyPixel, fly, REGION_DRAW_POST_PIXEL);

  fly->rv3d->rflag |= RV3D_NAVIGATING;

  /* Detect whether to start with Z locking. */
  copy_v3_fl3(upvec, 1.0f, 0.0f, 0.0f);
  copy_m3_m4(mat, fly->rv3d->viewinv);
  mul_m3_v3(mat, upvec);
  if (fabsf(upvec[2]) < 0.1f) {
    fly->zlock = FLY_AXISLOCK_STATE_IDLE;
  }

  fly->v3d_camera_control = ED_view3d_cameracontrol_acquire(
      fly->depsgraph, fly->scene, fly->v3d, fly->rv3d);

  /* Calculate center. */
  if (ED_view3d_cameracontrol_object_get(fly->v3d_camera_control)) {
    ED_view3d_calc_camera_border(
        fly->scene, fly->depsgraph, fly->region, fly->v3d, fly->rv3d, false, &viewborder);

    fly->viewport_size[0] = BLI_rctf_size_x(&viewborder);
    fly->viewport_size[1] = BLI_rctf_size_y(&viewborder);

    fly->center_mval[0] = int(viewborder.xmin + (fly->viewport_size[0] / 2.0f));
    fly->center_mval[1] = int(viewborder.ymin + (fly->viewport_size[1] / 2));
  }
  else {
    fly->viewport_size[0] = fly->region->winx;
    fly->viewport_size[1] = fly->region->winy;

    fly->center_mval[0] = int(fly->viewport_size[0] / 2.0f);
    fly->center_mval[1] = int(fly->viewport_size[1] / 2.0f);
  }

  /* Center the mouse, probably the UI mafia are against this but without its quite annoying. */
  WM_cursor_warp(win,
                 fly->region->winrct.xmin + fly->center_mval[0],
                 fly->region->winrct.ymin + fly->center_mval[1]);

  return true;
}

static wmOperatorStatus flyEnd(bContext *C, FlyInfo *fly)
{
  wmWindow *win;
  RegionView3D *rv3d;

  if (fly->state == FLY_RUNNING) {
    return OPERATOR_RUNNING_MODAL;
  }
  if (fly->state == FLY_CONFIRM) {
    /* Needed for auto-keyframe. */
#ifdef WITH_INPUT_NDOF
    if (fly->ndof) {
      flyApply_ndof(C, fly, true);
    }
    else
#endif /* WITH_INPUT_NDOF */
    {
      flyApply(C, fly, true);
    }
  }

#ifdef NDOF_FLY_DEBUG
  puts("\n-- fly end --");
#endif

  win = CTX_wm_window(C);
  rv3d = fly->rv3d;

  ED_workspace_status_text(C, nullptr);

  WM_event_timer_remove(CTX_wm_manager(C), win, fly->timer);

  ED_region_draw_cb_exit(fly->region->runtime->type, fly->draw_handle_pixel);

  ED_view3d_cameracontrol_release(fly->v3d_camera_control, fly->state == FLY_CANCEL);

  rv3d->rflag &= ~RV3D_NAVIGATING;

#ifdef WITH_INPUT_NDOF
  if (fly->ndof) {
    MEM_freeN(fly->ndof);
  }
#endif

  if (fly->state == FLY_CONFIRM) {
    MEM_freeN(fly);
    return OPERATOR_FINISHED;
  }

  MEM_freeN(fly);
  return OPERATOR_CANCELLED;
}

static void flyEvent(FlyInfo *fly, const wmEvent *event)
{
  if (event->type == TIMER && event->customdata == fly->timer) {
    fly->redraw = true;
  }
  else if (event->type == MOUSEMOVE) {
    copy_v2_v2_int(fly->mval, event->mval);
  }
#ifdef WITH_INPUT_NDOF
  else if (event->type == NDOF_MOTION) {
    /* Do these auto-magically get delivered? yes. */
    // puts("ndof motion detected in fly mode!");
    // static const char *tag_name = "3D mouse position";

    const wmNDOFMotionData *incoming_ndof = static_cast<const wmNDOFMotionData *>(
        event->customdata);
    switch (incoming_ndof->progress) {
      case P_STARTING: {
        /* Start keeping track of 3D mouse position. */
#  ifdef NDOF_FLY_DEBUG
        puts("start keeping track of 3D mouse position");
#  endif
        /* Fall-through. */
      }
      case P_IN_PROGRESS: {
        /* Update 3D mouse position. */
#  ifdef NDOF_FLY_DEBUG
        putchar('.');
        fflush(stdout);
#  endif
        if (fly->ndof == nullptr) {
          // fly->ndof = MEM_mallocN(sizeof(wmNDOFMotionData), tag_name);
          fly->ndof = static_cast<wmNDOFMotionData *>(MEM_dupallocN(incoming_ndof));
          // fly->ndof = malloc(sizeof(wmNDOFMotionData));
        }
        else {
          memcpy(fly->ndof, incoming_ndof, sizeof(wmNDOFMotionData));
        }
        break;
      }
      case P_FINISHING: {
        /* Stop keeping track of 3D mouse position. */
#  ifdef NDOF_FLY_DEBUG
        puts("stop keeping track of 3D mouse position");
#  endif
        if (fly->ndof) {
          MEM_freeN(fly->ndof);
          // free(fly->ndof);
          fly->ndof = nullptr;
        }
        /* Update the time else the view will jump when 2D mouse/timer resume. */
        fly->time_lastdraw = BLI_time_now_seconds();
        break;
      }
      default: {
        /* Should always be one of the above 3. */
        break;
      }
    }
  }
#endif /* WITH_INPUT_NDOF */
  /* Handle modal key-map first. */
  else if (event->type == EVT_MODAL_MAP) {
    switch (event->val) {
      case FLY_MODAL_CANCEL: {
        fly->state = FLY_CANCEL;
        break;
      }
      case FLY_MODAL_CONFIRM: {
        fly->state = FLY_CONFIRM;
        break;
      }
      /* Speed adjusting with mouse-pan (trackpad). */
      case FLY_MODAL_SPEED: {
        float fac = 0.02f * float(event->prev_xy[1] - event->xy[1]);

        /* Allowing to brake immediate. */
        if (fac > 0.0f && fly->speed < 0.0f) {
          fly->speed = 0.0f;
        }
        else if (fac < 0.0f && fly->speed > 0.0f) {
          fly->speed = 0.0f;
        }
        else {
          fly->speed += fly->grid * fac;
        }

        break;
      }
      case FLY_MODAL_ACCELERATE: {
        double time_currwheel;
        float time_wheel;

        /* Not quite correct but avoids confusion WASD/arrow keys 'locking up'. */
        if (fly->axis == -1) {
          fly->axis = 2;
          fly->speed = fabsf(fly->speed);
        }

        time_currwheel = BLI_time_now_seconds();
        time_wheel = float(time_currwheel - fly->time_lastwheel);
        fly->time_lastwheel = time_currwheel;
        /* Mouse wheel delays range from (0.5 == slow) to (0.01 == fast). */
        /* 0-0.5 -> 0-5.0 */
        time_wheel = 1.0f + (10.0f - (20.0f * min_ff(time_wheel, 0.5f)));

        if (fly->speed < 0.0f) {
          fly->speed = 0.0f;
        }
        else {
          fly->speed += fly->grid * time_wheel * (fly->use_precision ? 0.1f : 1.0f);
        }
        break;
      }
      case FLY_MODAL_DECELERATE: {
        double time_currwheel;
        float time_wheel;

        /* Not quite correct but avoids confusion WASD/arrow keys 'locking up'. */
        if (fly->axis == -1) {
          fly->axis = 2;
          fly->speed = -fabsf(fly->speed);
        }

        time_currwheel = BLI_time_now_seconds();
        time_wheel = float(time_currwheel - fly->time_lastwheel);
        fly->time_lastwheel = time_currwheel;
        /* 0-0.5 -> 0-5.0 */
        time_wheel = 1.0f + (10.0f - (20.0f * min_ff(time_wheel, 0.5f)));

        if (fly->speed > 0.0f) {
          fly->speed = 0;
        }
        else {
          fly->speed -= fly->grid * time_wheel * (fly->use_precision ? 0.1f : 1.0f);
        }
        break;
      }
      case FLY_MODAL_PAN_ENABLE: {
        fly->pan_view = true;
        break;
      }
      case FLY_MODAL_PAN_DISABLE: {
        fly->pan_view = false;
        break;
      }
        /* Implement WASD keys, comments only for 'forward'. */
      case FLY_MODAL_DIR_FORWARD: {
        if (fly->axis == 2 && fly->speed < 0.0f) {
          /* Reverse direction stops, tap again to continue. */
          fly->axis = -1;
        }
        else {
          /* Flip speed rather than stopping, game like motion,
           * else increase like mouse-wheel if we're already moving in that direction. */
          if (fly->speed < 0.0f) {
            fly->speed = -fly->speed;
          }
          else if (fly->axis == 2) {
            fly->speed += fly->grid;
          }
          fly->axis = 2;
        }
        break;
      }
      case FLY_MODAL_DIR_BACKWARD: {
        if (fly->axis == 2 && fly->speed > 0.0f) {
          fly->axis = -1;
        }
        else {
          if (fly->speed > 0.0f) {
            fly->speed = -fly->speed;
          }
          else if (fly->axis == 2) {
            fly->speed -= fly->grid;
          }

          fly->axis = 2;
        }
        break;
      }
      case FLY_MODAL_DIR_LEFT: {
        if (fly->axis == 0 && fly->speed < 0.0f) {
          fly->axis = -1;
        }
        else {
          if (fly->speed < 0.0f) {
            fly->speed = -fly->speed;
          }
          else if (fly->axis == 0) {
            fly->speed += fly->grid;
          }

          fly->axis = 0;
        }
        break;
      }
      case FLY_MODAL_DIR_RIGHT: {
        if (fly->axis == 0 && fly->speed > 0.0f) {
          fly->axis = -1;
        }
        else {
          if (fly->speed > 0.0f) {
            fly->speed = -fly->speed;
          }
          else if (fly->axis == 0) {
            fly->speed -= fly->grid;
          }

          fly->axis = 0;
        }
        break;
      }
      case FLY_MODAL_DIR_DOWN: {
        if (fly->axis == 1 && fly->speed < 0.0f) {
          fly->axis = -1;
        }
        else {
          if (fly->speed < 0.0f) {
            fly->speed = -fly->speed;
          }
          else if (fly->axis == 1) {
            fly->speed += fly->grid;
          }
          fly->axis = 1;
        }
        break;
      }
      case FLY_MODAL_DIR_UP: {
        if (fly->axis == 1 && fly->speed > 0.0f) {
          fly->axis = -1;
        }
        else {
          if (fly->speed > 0.0f) {
            fly->speed = -fly->speed;
          }
          else if (fly->axis == 1) {
            fly->speed -= fly->grid;
          }
          fly->axis = 1;
        }
        break;
      }
      case FLY_MODAL_AXIS_LOCK_X: {
        if (fly->xlock != FLY_AXISLOCK_STATE_OFF) {
          fly->xlock = FLY_AXISLOCK_STATE_OFF;
        }
        else {
          fly->xlock = FLY_AXISLOCK_STATE_ACTIVE;
          fly->xlock_momentum = 0.0;
        }
        break;
      }
      case FLY_MODAL_AXIS_LOCK_Z: {
        if (fly->zlock != FLY_AXISLOCK_STATE_OFF) {
          fly->zlock = FLY_AXISLOCK_STATE_OFF;
        }
        else {
          fly->zlock = FLY_AXISLOCK_STATE_ACTIVE;
          fly->zlock_momentum = 0.0;
        }
        break;
      }
      case FLY_MODAL_PRECISION_ENABLE: {
        fly->use_precision = true;
        break;
      }
      case FLY_MODAL_PRECISION_DISABLE: {
        fly->use_precision = false;
        break;
      }
      case FLY_MODAL_FREELOOK_ENABLE: {
        fly->use_freelook = true;
        break;
      }
      case FLY_MODAL_FREELOOK_DISABLE: {
        fly->use_freelook = false;
        break;
      }
    }
  }
}

static void flyMoveCamera(bContext *C,
                          FlyInfo *fly,
                          const bool do_rotate,
                          const bool do_translate,
                          const bool is_confirm)
{
  /* We only consider auto-keying on playback or if user confirmed fly on the same frame
   * otherwise we get a keyframe even if the user cancels. */
  const bool use_autokey = is_confirm || fly->anim_playing;
  ED_view3d_cameracontrol_update(fly->v3d_camera_control, use_autokey, C, do_rotate, do_translate);
}

static int flyApply(bContext *C, FlyInfo *fly, bool is_confirm)
{
#define FLY_ROTATE_FAC 10.0f        /* More is faster. */
#define FLY_ZUP_CORRECT_FAC 0.1f    /* Amount to correct per step. */
#define FLY_ZUP_CORRECT_ACCEL 0.05f /* Increase upright momentum each step. */
#define FLY_SMOOTH_FAC 20.0f        /* Higher value less lag. */

  RegionView3D *rv3d = fly->rv3d;

  /* 3x3 copy of the view matrix so we can move along the view axis. */
  float mat[3][3];
  /* This is the direction that's added to the view offset per redraw. */
  float dvec[3] = {0, 0, 0};

  /* Camera Up-righting variables. */
  float moffset[2];  /* Mouse offset from the views center. */
  float tmp_quat[4]; /* Used for rotating the view. */

#ifdef NDOF_FLY_DEBUG
  {
    static uint iteration = 1;
    printf("fly timer %d\n", iteration++);
  }
#endif

  /* X and Y margin defining the safe area where the mouse's movement won't rotate the view. */
  const float xmargin = fly->viewport_size[0] / 20.0f;
  const float ymargin = fly->viewport_size[1] / 20.0f;

  {

    /* Mouse offset from the center. */
    moffset[0] = float(fly->mval[0] - fly->center_mval[0]);
    moffset[1] = float(fly->mval[1] - fly->center_mval[1]);

    /* Enforce a view margin. */
    if (moffset[0] > xmargin) {
      moffset[0] -= xmargin;
    }
    else if (moffset[0] < -xmargin) {
      moffset[0] += xmargin;
    }
    else {
      moffset[0] = 0;
    }

    if (moffset[1] > ymargin) {
      moffset[1] -= ymargin;
    }
    else if (moffset[1] < -ymargin) {
      moffset[1] += ymargin;
    }
    else {
      moffset[1] = 0;
    }

    /* Scale the mouse movement by this value - scales mouse movement to the view size
     * `moffset[0] / (region->winx-xmargin * 2)` - window size minus margin (same for Y).
     *
     * the mouse moves isn't linear. */

    if (moffset[0]) {
      moffset[0] /= fly->viewport_size[0] - (xmargin * 2);
      moffset[0] *= fabsf(moffset[0]);
    }

    if (moffset[1]) {
      moffset[1] /= fly->viewport_size[1] - (ymargin * 2);
      moffset[1] *= fabsf(moffset[1]);
    }

    /* Should we redraw? */
    if ((fly->speed != 0.0f) || moffset[0] || moffset[1] ||
        (fly->zlock != FLY_AXISLOCK_STATE_OFF) || (fly->xlock != FLY_AXISLOCK_STATE_OFF) ||
        dvec[0] || dvec[1] || dvec[2])
    {
      float dvec_tmp[3];

      /* Time how fast it takes for us to redraw,
       * this is so simple scenes don't fly too fast. */
      double time_current;
      float time_redraw;
      float time_redraw_clamped;
#ifdef NDOF_FLY_DRAW_TOOMUCH
      fly->redraw = 1;
#endif
      time_current = BLI_time_now_seconds();
      time_redraw = float(time_current - fly->time_lastdraw);

      /* Clamp redraw time to avoid jitter in roll correction. */
      time_redraw_clamped = min_ff(0.05f, time_redraw);

      fly->time_lastdraw = time_current;

      /* Scale the time to use shift to scale the speed down - just like
       * shift slows many other areas of blender down. */
      if (fly->use_precision) {
        fly->speed = fly->speed * (1.0f - time_redraw_clamped);
      }

      copy_m3_m4(mat, rv3d->viewinv);

      if (fly->pan_view == true) {
        /* Pan only. */
        copy_v3_fl3(dvec_tmp, -moffset[0], -moffset[1], 0.0f);

        if (fly->use_precision) {
          dvec_tmp[0] *= 0.1f;
          dvec_tmp[1] *= 0.1f;
        }

        mul_m3_v3(mat, dvec_tmp);
        mul_v3_fl(dvec_tmp, time_redraw * 200.0f * fly->grid);
      }
      else {
        /* Similar to the angle between the camera's up and the Z-up,
         * but its very rough so just roll. */
        float roll;

        /* Rotate about the X axis- look up/down. */
        if (moffset[1]) {
          float upvec[3];
          copy_v3_fl3(upvec, 1.0f, 0.0f, 0.0f);
          mul_m3_v3(mat, upvec);
          /* Rotate about the relative up vector. */
          axis_angle_to_quat(tmp_quat, upvec, moffset[1] * time_redraw * -FLY_ROTATE_FAC);
          mul_qt_qtqt(rv3d->viewquat, rv3d->viewquat, tmp_quat);

          if (fly->xlock != FLY_AXISLOCK_STATE_OFF) {
            fly->xlock = FLY_AXISLOCK_STATE_ACTIVE; /* Check for rotation. */
          }
          if (fly->zlock != FLY_AXISLOCK_STATE_OFF) {
            fly->zlock = FLY_AXISLOCK_STATE_ACTIVE;
          }
          fly->xlock_momentum = 0.0f;
        }

        /* Rotate about the Y axis- look left/right. */
        if (moffset[0]) {
          float upvec[3];
          /* If we're upside down invert the `moffset`. */
          copy_v3_fl3(upvec, 0.0f, 1.0f, 0.0f);
          mul_m3_v3(mat, upvec);

          if (upvec[2] < 0.0f) {
            moffset[0] = -moffset[0];
          }

          /* Make the lock vectors. */
          if (fly->zlock) {
            copy_v3_fl3(upvec, 0.0f, 0.0f, 1.0f);
          }
          else {
            copy_v3_fl3(upvec, 0.0f, 1.0f, 0.0f);
            mul_m3_v3(mat, upvec);
          }

          /* Rotate about the relative up vector. */
          axis_angle_to_quat(tmp_quat, upvec, moffset[0] * time_redraw * FLY_ROTATE_FAC);
          mul_qt_qtqt(rv3d->viewquat, rv3d->viewquat, tmp_quat);

          if (fly->xlock != FLY_AXISLOCK_STATE_OFF) {
            fly->xlock = FLY_AXISLOCK_STATE_ACTIVE; /* Check for rotation. */
          }
          if (fly->zlock != FLY_AXISLOCK_STATE_OFF) {
            fly->zlock = FLY_AXISLOCK_STATE_ACTIVE;
          }
        }

        if (fly->zlock == FLY_AXISLOCK_STATE_ACTIVE) {
          float upvec[3];
          copy_v3_fl3(upvec, 1.0f, 0.0f, 0.0f);
          mul_m3_v3(mat, upvec);

          /* Make sure we have some Z rolling. */
          if (fabsf(upvec[2]) > 0.00001f) {
            roll = upvec[2] * 5.0f;
            /* Rotate the view about this axis. */
            copy_v3_fl3(upvec, 0.0f, 0.0f, 1.0f);
            mul_m3_v3(mat, upvec);
            /* Rotate about the relative up vector. */
            axis_angle_to_quat(tmp_quat,
                               upvec,
                               roll * time_redraw_clamped * fly->zlock_momentum *
                                   FLY_ZUP_CORRECT_FAC);
            mul_qt_qtqt(rv3d->viewquat, rv3d->viewquat, tmp_quat);

            fly->zlock_momentum += FLY_ZUP_CORRECT_ACCEL;
          }
          else {
            /* Don't check until the view rotates again. */
            fly->zlock = FLY_AXISLOCK_STATE_IDLE;
            fly->zlock_momentum = 0.0f;
          }
        }

        /* Only apply X-axis correction when mouse isn't applying X rotation. */
        if (fly->xlock == FLY_AXISLOCK_STATE_ACTIVE && moffset[1] == 0) {
          float upvec[3];
          copy_v3_fl3(upvec, 0.0f, 0.0f, 1.0f);
          mul_m3_v3(mat, upvec);
          /* Make sure we have some Z rolling. */
          if (fabsf(upvec[2]) > 0.00001f) {
            roll = upvec[2] * -5.0f;
            /* Rotate the view about this axis. */
            copy_v3_fl3(upvec, 1.0f, 0.0f, 0.0f);
            mul_m3_v3(mat, upvec);

            /* Rotate about the relative up vector. */
            axis_angle_to_quat(
                tmp_quat, upvec, roll * time_redraw_clamped * fly->xlock_momentum * 0.1f);
            mul_qt_qtqt(rv3d->viewquat, rv3d->viewquat, tmp_quat);

            fly->xlock_momentum += 0.05f;
          }
          else {
            fly->xlock = FLY_AXISLOCK_STATE_IDLE; /* See above. */
            fly->xlock_momentum = 0.0f;
          }
        }

        if (fly->axis == -1) {
          /* Pause. */
          zero_v3(dvec_tmp);
        }
        else if (!fly->use_freelook) {
          /* Normal operation. */
          /* Define `dvec`, view direction vector. */
          zero_v3(dvec_tmp);
          /* Move along the current axis. */
          dvec_tmp[fly->axis] = 1.0f;

          mul_m3_v3(mat, dvec_tmp);
        }
        else {
          normalize_v3_v3(dvec_tmp, fly->dvec_prev);
          if (fly->speed < 0.0f) {
            negate_v3(dvec_tmp);
          }
        }

        mul_v3_fl(dvec_tmp, fly->speed * time_redraw * 0.25f);
      }

      /* Impose a directional lag. */
      interp_v3_v3v3(
          dvec, dvec_tmp, fly->dvec_prev, (1.0f / (1.0f + (time_redraw * FLY_SMOOTH_FAC))));

      add_v3_v3(rv3d->ofs, dvec);

      if (rv3d->persp == RV3D_CAMOB) {
        const bool do_rotate = ((fly->xlock != FLY_AXISLOCK_STATE_OFF) ||
                                (fly->zlock != FLY_AXISLOCK_STATE_OFF) ||
                                ((moffset[0] || moffset[1]) && !fly->pan_view));
        const bool do_translate = (fly->speed != 0.0f || fly->pan_view);
        flyMoveCamera(C, fly, do_rotate, do_translate, is_confirm);
      }
    }
    else {
      /* We're not redrawing but we need to update the time else the view will jump. */
      fly->time_lastdraw = BLI_time_now_seconds();
    }
    /* End drawing. */
    copy_v3_v3(fly->dvec_prev, dvec);
  }

  return OPERATOR_FINISHED;
}

#ifdef WITH_INPUT_NDOF
static void flyApply_ndof(bContext *C, FlyInfo *fly, bool is_confirm)
{
  Object *lock_ob = ED_view3d_cameracontrol_object_get(fly->v3d_camera_control);
  bool has_translate, has_rotate;

  view3d_ndof_fly(*fly->ndof,
                  fly->v3d,
                  fly->rv3d,
                  fly->use_precision,
                  lock_ob ? lock_ob->protectflag : 0,
                  &has_translate,
                  &has_rotate);

  if (has_translate || has_rotate) {
    fly->redraw = true;

    if (fly->rv3d->persp == RV3D_CAMOB) {
      flyMoveCamera(C, fly, has_rotate, has_translate, is_confirm);
    }
  }
}
#endif /* WITH_INPUT_NDOF */

/** \} */

/* -------------------------------------------------------------------- */
/** \name Fly Operator
 * \{ */

static void fly_draw_status(bContext *C, wmOperator *op)
{
  FlyInfo *fly = static_cast<FlyInfo *>(op->customdata);

  WorkspaceStatus status(C);

  status.opmodal(IFACE_("Confirm"), op->type, FLY_MODAL_CONFIRM);
  status.opmodal(IFACE_("Cancel"), op->type, FLY_MODAL_CANCEL);

  status.opmodal("", op->type, FLY_MODAL_DIR_FORWARD);
  status.opmodal("", op->type, FLY_MODAL_DIR_LEFT);
  status.opmodal("", op->type, FLY_MODAL_DIR_BACKWARD);
  status.opmodal("", op->type, FLY_MODAL_DIR_RIGHT);
  status.item(IFACE_("Move"), ICON_NONE);

  status.opmodal("", op->type, FLY_MODAL_DIR_UP);
  status.opmodal("", op->type, FLY_MODAL_DIR_DOWN);
  status.item(IFACE_("Up/Down"), ICON_NONE);

  status.opmodal(IFACE_("Pan"), op->type, FLY_MODAL_PAN_ENABLE);
  status.opmodal(IFACE_("Speed"), op->type, FLY_MODAL_SPEED);

  status.opmodal("", op->type, FLY_MODAL_AXIS_LOCK_X, fly->xlock != FLY_AXISLOCK_STATE_OFF);
  status.opmodal("", op->type, FLY_MODAL_AXIS_LOCK_Z, fly->zlock != FLY_AXISLOCK_STATE_OFF);
  status.item(IFACE_("Axis Lock"), ICON_NONE);

  status.opmodal(IFACE_("Precision"), op->type, FLY_MODAL_PRECISION_ENABLE, fly->use_precision);
  status.opmodal(IFACE_("Free Look"), op->type, FLY_MODAL_FREELOOK_ENABLE, fly->use_freelook);

  status.opmodal("", op->type, FLY_MODAL_ACCELERATE);
  status.opmodal("", op->type, FLY_MODAL_DECELERATE);
  status.item(fmt::format("{} ({:.2f})", IFACE_("Acceleration"), fly->speed), ICON_NONE);
}

static wmOperatorStatus fly_invoke(bContext *C, wmOperator *op, const wmEvent *event)
{
  RegionView3D *rv3d = CTX_wm_region_view3d(C);

  if (RV3D_LOCK_FLAGS(rv3d) & RV3D_LOCK_ANY_TRANSFORM) {
    return OPERATOR_CANCELLED;
  }

  FlyInfo *fly = MEM_callocN<FlyInfo>("FlyOperation");

  op->customdata = fly;

  if (initFlyInfo(C, fly, op, event) == false) {
    MEM_freeN(fly);
    return OPERATOR_CANCELLED;
  }

  flyEvent(fly, event);

  fly_draw_status(C, op);

  WM_event_add_modal_handler(C, op);

  return OPERATOR_RUNNING_MODAL;
}

static void fly_cancel(bContext *C, wmOperator *op)
{
  FlyInfo *fly = static_cast<FlyInfo *>(op->customdata);

  fly->state = FLY_CANCEL;
  flyEnd(C, fly);
  op->customdata = nullptr;
}

static wmOperatorStatus fly_modal(bContext *C, wmOperator *op, const wmEvent *event)
{
  bool do_draw = false;
  FlyInfo *fly = static_cast<FlyInfo *>(op->customdata);
  View3D *v3d = fly->v3d;
  RegionView3D *rv3d = fly->rv3d;
  Object *fly_object = ED_view3d_cameracontrol_object_get(fly->v3d_camera_control);

  fly->redraw = false;

  flyEvent(fly, event);

  fly_draw_status(C, op);

#ifdef WITH_INPUT_NDOF
  if (fly->ndof) { /* 3D mouse overrules [2D mouse + timer]. */
    if (event->type == NDOF_MOTION) {
      flyApply_ndof(C, fly, false);
    }
  }
  else
#endif /* WITH_INPUT_NDOF */
  {
    if (event->type == TIMER && event->customdata == fly->timer) {
      flyApply(C, fly, false);
    }
  }

  do_draw |= fly->redraw;

  wmOperatorStatus exit_code = flyEnd(C, fly);

  if (exit_code == OPERATOR_FINISHED) {
    const bool is_undo_pushed = ED_view3d_camera_lock_undo_push(op->type->name, v3d, rv3d, C);
    /* If generic 'locked camera' code did not push an undo, but there is a valid 'flying
     * object', an undo push is still needed, since that object transform was modified. */
    if (!is_undo_pushed && fly_object && ED_undo_is_memfile_compatible(C)) {
      ED_undo_push(C, op->type->name);
    }
  }
  if (exit_code != OPERATOR_RUNNING_MODAL) {
    do_draw = true;
  }

  if (do_draw) {
    if (rv3d->persp == RV3D_CAMOB) {
      WM_event_add_notifier(C, NC_OBJECT | ND_TRANSFORM, fly_object);
    }

    // puts("redraw!"); // too frequent, commented with NDOF_FLY_DRAW_TOOMUCH for now
    ED_region_tag_redraw(CTX_wm_region(C));
  }

  return exit_code;
}

void VIEW3D_OT_fly(wmOperatorType *ot)
{
  /* Identifiers. */
  ot->name = "Fly Navigation";
  ot->description = "Interactively fly around the scene";
  ot->idname = "VIEW3D_OT_fly";

  /* API callbacks. */
  ot->invoke = fly_invoke;
  ot->cancel = fly_cancel;
  ot->modal = fly_modal;
  ot->poll = ED_operator_region_view3d_active;

  /* Flags. */
  ot->flag = OPTYPE_BLOCKING;
}

/** \} */

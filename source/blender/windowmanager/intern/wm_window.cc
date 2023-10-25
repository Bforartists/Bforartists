/* SPDX-FileCopyrightText: 2001-2002 NaN Holding BV. All rights reserved. 2007 Blender Authors.
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup wm
 *
 * Window management, wrap GHOST.
 */

#include <chrono>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <thread>

#include "DNA_listBase.h"
#include "DNA_screen_types.h"
#include "DNA_windowmanager_types.h"
#include "DNA_workspace_types.h"

#include "MEM_guardedalloc.h"

#include "GHOST_C-api.h"

#include "BLI_blenlib.h"
#include "BLI_system.h"
#include "BLI_utildefines.h"

#include "BLT_translation.h"

#include "BKE_blender_version.h"
#include "BKE_context.h"
#include "BKE_global.h"
#include "BKE_icons.h"
#include "BKE_layer.h"
#include "BKE_main.h"
#include "BKE_report.h"
#include "BKE_screen.hh"
#include "BKE_workspace.h"

#include "RNA_access.hh"
#include "RNA_define.hh"
#include "RNA_enum_types.hh"

#include "WM_api.hh"
#include "WM_types.hh"
#include "wm.hh"
#include "wm_draw.hh"
#include "wm_event_system.h"
#include "wm_files.hh"
#include "wm_platform_support.h"
#include "wm_window.hh"
#include "wm_window_private.h"
#ifdef WITH_XR_OPENXR
#  include "wm_xr.h"
#endif

#include "ED_anim_api.hh"
#include "ED_fileselect.hh"
#include "ED_render.hh"
#include "ED_scene.hh"
#include "ED_screen.hh"

#include "IMB_imbuf.h"
#include "IMB_imbuf_types.h"

#include "UI_interface.hh"
#include "UI_interface_icons.hh"

#include "PIL_time.h"

#include "BLF_api.h"
#include "GPU_batch.h"
#include "GPU_batch_presets.h"
#include "GPU_context.h"
#include "GPU_framebuffer.h"
#include "GPU_immediate.h"
#include "GPU_init_exit.h"
#include "GPU_platform.h"
#include "GPU_state.h"
#include "GPU_texture.h"

#include "UI_resources.hh"

/* for assert */
#ifndef NDEBUG
#  include "BLI_threads.h"
#endif

/* the global to talk to ghost */
static GHOST_SystemHandle g_system = nullptr;
#if !(defined(WIN32) || defined(__APPLE__))
static const char *g_system_backend_id = nullptr;
#endif

enum eWinOverrideFlag {
  WIN_OVERRIDE_GEOM = (1 << 0),
  WIN_OVERRIDE_WINSTATE = (1 << 1),
};
ENUM_OPERATORS(eWinOverrideFlag, WIN_OVERRIDE_WINSTATE)

#define GHOST_WINDOW_STATE_DEFAULT GHOST_kWindowStateMaximized

/**
 * Override defaults or startup file when #eWinOverrideFlag is set.
 * These values are typically set by command line arguments.
 */
static struct WMInitStruct {
  /**
   * Window geometry:
   * - Defaults to the main screen-size.
   * - May be set by the `--window-geometry` argument,
   *   which also forces these values to be used by setting #WIN_OVERRIDE_GEOM.
   * - When #wmWindow::size_x is zero, these values are used as a fallback,
   *   needed so the #BLENDER_STARTUP_FILE loads at the size of the users main-screen
   *   instead of the size stored in the factory startup.
   *   Otherwise the window geometry saved in the blend-file is used and these values are ignored.
   */
  int size_x, size_y;
  int start_x, start_y;

  GHOST_TWindowState windowstate = GHOST_WINDOW_STATE_DEFAULT;
  eWinOverrideFlag override_flag;

  bool window_focus = true;
  bool native_pixels = true;
} wm_init_state;

/* -------------------------------------------------------------------- */
/** \name Modifier Constants
 * \{ */

static const struct {
  uint8_t flag;
  GHOST_TKey ghost_key_pair[2];
  GHOST_TModifierKey ghost_mask_pair[2];
} g_modifier_table[] = {
    {KM_SHIFT,
     {GHOST_kKeyLeftShift, GHOST_kKeyRightShift},
     {GHOST_kModifierKeyLeftShift, GHOST_kModifierKeyRightShift}},
    {KM_CTRL,
     {GHOST_kKeyLeftControl, GHOST_kKeyRightControl},
     {GHOST_kModifierKeyLeftControl, GHOST_kModifierKeyRightControl}},
    {KM_ALT,
     {GHOST_kKeyLeftAlt, GHOST_kKeyRightAlt},
     {GHOST_kModifierKeyLeftAlt, GHOST_kModifierKeyRightAlt}},
    {KM_OSKEY,
     {GHOST_kKeyLeftOS, GHOST_kKeyRightOS},
     {GHOST_kModifierKeyLeftOS, GHOST_kModifierKeyRightOS}},
};

enum ModSide {
  MOD_SIDE_LEFT = 0,
  MOD_SIDE_RIGHT = 1,
};

/** \} */

/* -------------------------------------------------------------------- */
/** \name Window Open
 * \{ */

static void wm_window_set_drawable(wmWindowManager *wm, wmWindow *win, bool activate);
static bool wm_window_timers_process(const bContext *C, int *sleep_us);
static uint8_t wm_ghost_modifier_query(const enum ModSide side);

bool wm_get_screensize(int *r_width, int *r_height)
{
  uint32_t uiwidth, uiheight;
  if (GHOST_GetMainDisplayDimensions(g_system, &uiwidth, &uiheight) == GHOST_kFailure) {
    return false;
  }
  *r_width = uiwidth;
  *r_height = uiheight;
  return true;
}

bool wm_get_desktopsize(int *r_width, int *r_height)
{
  uint32_t uiwidth, uiheight;
  if (GHOST_GetAllDisplayDimensions(g_system, &uiwidth, &uiheight) == GHOST_kFailure) {
    return false;
  }
  *r_width = uiwidth;
  *r_height = uiheight;
  return true;
}

/* keeps size within monitor bounds */
static void wm_window_check_size(rcti *rect)
{
  int width, height;
  if (wm_get_screensize(&width, &height)) {
    if (BLI_rcti_size_x(rect) > width) {
      BLI_rcti_resize_x(rect, width);
    }
    if (BLI_rcti_size_y(rect) > height) {
      BLI_rcti_resize_y(rect, height);
    }
  }
}

static void wm_ghostwindow_destroy(wmWindowManager *wm, wmWindow *win)
{
  if (UNLIKELY(!win->ghostwin)) {
    return;
  }

  /* Prevents non-drawable state of main windows (bugs #22967,
   * #25071 and possibly #22477 too). Always clear it even if
   * this window was not the drawable one, because we mess with
   * drawing context to discard the GW context. */
  wm_window_clear_drawable(wm);

  if (win == wm->winactive) {
    wm->winactive = nullptr;
  }

  /* We need this window's GPU context active to discard it. */
  GHOST_ActivateWindowDrawingContext(static_cast<GHOST_WindowHandle>(win->ghostwin));
  GPU_context_active_set(static_cast<GPUContext *>(win->gpuctx));

  /* Delete local GPU context. */
  GPU_context_discard(static_cast<GPUContext *>(win->gpuctx));

  GHOST_DisposeWindow(g_system, static_cast<GHOST_WindowHandle>(win->ghostwin));
  win->ghostwin = nullptr;
  win->gpuctx = nullptr;
}

void wm_window_free(bContext *C, wmWindowManager *wm, wmWindow *win)
{
  /* update context */
  if (C) {
    WM_event_remove_handlers(C, &win->handlers);
    WM_event_remove_handlers(C, &win->modalhandlers);

    if (CTX_wm_window(C) == win) {
      CTX_wm_window_set(C, nullptr);
    }
  }

  BKE_screen_area_map_free(&win->global_areas);

  /* end running jobs, a job end also removes its timer */
  LISTBASE_FOREACH_MUTABLE (wmTimer *, wt, &wm->timers) {
    if (wt->flags & WM_TIMER_TAGGED_FOR_REMOVAL) {
      continue;
    }
    if (wt->win == win && wt->event_type == TIMERJOBS) {
      wm_jobs_timer_end(wm, wt);
    }
  }

  /* timer removing, need to call this api function */
  LISTBASE_FOREACH_MUTABLE (wmTimer *, wt, &wm->timers) {
    if (wt->flags & WM_TIMER_TAGGED_FOR_REMOVAL) {
      continue;
    }
    if (wt->win == win) {
      WM_event_timer_remove(wm, win, wt);
    }
  }
  wm_window_timers_delete_removed(wm);

  if (win->eventstate) {
    MEM_freeN(win->eventstate);
  }
  if (win->event_last_handled) {
    MEM_freeN(win->event_last_handled);
  }
  if (win->event_queue_consecutive_gesture_data) {
    WM_event_consecutive_data_free(win);
  }

  if (win->cursor_keymap_status) {
    MEM_freeN(win->cursor_keymap_status);
  }

  WM_gestures_free_all(win);

  wm_event_free_all(win);

  wm_ghostwindow_destroy(wm, win);

  BKE_workspace_instance_hook_free(G_MAIN, win->workspace_hook);
  MEM_freeN(win->stereo3d_format);

  MEM_freeN(win);
}

static int find_free_winid(wmWindowManager *wm)
{
  int id = 1;

  LISTBASE_FOREACH (wmWindow *, win, &wm->windows) {
    if (id <= win->winid) {
      id = win->winid + 1;
    }
  }
  return id;
}

wmWindow *wm_window_new(const Main *bmain, wmWindowManager *wm, wmWindow *parent, bool dialog)
{
  wmWindow *win = static_cast<wmWindow *>(MEM_callocN(sizeof(wmWindow), "window"));

  BLI_addtail(&wm->windows, win);
  win->winid = find_free_winid(wm);

  /* Dialogs may have a child window as parent. Otherwise, a child must not be a parent too. */
  win->parent = (!dialog && parent && parent->parent) ? parent->parent : parent;
  win->stereo3d_format = static_cast<Stereo3dFormat *>(
      MEM_callocN(sizeof(Stereo3dFormat), "Stereo 3D Format (window)"));
  win->workspace_hook = BKE_workspace_instance_hook_create(bmain, win->winid);

  return win;
}

wmWindow *wm_window_copy(Main *bmain,
                         wmWindowManager *wm,
                         wmWindow *win_src,
                         const bool duplicate_layout,
                         const bool child)
{
  const bool is_dialog = GHOST_IsDialogWindow(static_cast<GHOST_WindowHandle>(win_src->ghostwin));
  wmWindow *win_parent = (child) ? win_src : win_src->parent;
  wmWindow *win_dst = wm_window_new(bmain, wm, win_parent, is_dialog);
  WorkSpace *workspace = WM_window_get_active_workspace(win_src);
  WorkSpaceLayout *layout_old = WM_window_get_active_layout(win_src);

  win_dst->posx = win_src->posx + 10;
  win_dst->posy = win_src->posy;
  win_dst->sizex = win_src->sizex;
  win_dst->sizey = win_src->sizey;

  win_dst->scene = win_src->scene;
  STRNCPY(win_dst->view_layer_name, win_src->view_layer_name);
  BKE_workspace_active_set(win_dst->workspace_hook, workspace);
  WorkSpaceLayout *layout_new = duplicate_layout ? ED_workspace_layout_duplicate(
                                                       bmain, workspace, layout_old, win_dst) :
                                                   layout_old;
  BKE_workspace_active_layout_set(win_dst->workspace_hook, win_dst->winid, workspace, layout_new);

  *win_dst->stereo3d_format = *win_src->stereo3d_format;

  return win_dst;
}

wmWindow *wm_window_copy_test(bContext *C,
                              wmWindow *win_src,
                              const bool duplicate_layout,
                              const bool child)
{
  Main *bmain = CTX_data_main(C);
  wmWindowManager *wm = CTX_wm_manager(C);

  wmWindow *win_dst = wm_window_copy(bmain, wm, win_src, duplicate_layout, child);

  WM_check(C);

  if (win_dst->ghostwin) {
    WM_event_add_notifier_ex(wm, CTX_wm_window(C), NC_WINDOW | NA_ADDED, nullptr);
    return win_dst;
  }
  wm_window_close(C, wm, win_dst);
  return nullptr;
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Window Quit Confirmation Dialog
 * \{ */

static void wm_save_file_on_quit_dialog_callback(bContext *C, void * /*user_data*/)
{
  wm_exit_schedule_delayed(C);
}

/**
 * Call the confirm dialog on quitting. It's displayed in the context window so
 * caller should set it as desired.
 */
static void wm_confirm_quit(bContext *C)
{
  wmGenericCallback *action = static_cast<wmGenericCallback *>(
      MEM_callocN(sizeof(*action), __func__));
  action->exec = wm_save_file_on_quit_dialog_callback;
  wm_close_file_dialog(C, action);
}

void wm_quit_with_optional_confirmation_prompt(bContext *C, wmWindow *win)
{
  wmWindow *win_ctx = CTX_wm_window(C);

  /* The popup will be displayed in the context window which may not be set
   * here (this function gets called outside of normal event handling loop). */
  CTX_wm_window_set(C, win);

  if (U.uiflag & USER_SAVE_PROMPT) {
    if (wm_file_or_session_data_has_unsaved_changes(CTX_data_main(C), CTX_wm_manager(C)) &&
        !G.background)
    {
      wm_window_raise(win);
      wm_confirm_quit(C);
    }
    else {
      wm_exit_schedule_delayed(C);
    }
  }
  else {
    wm_exit_schedule_delayed(C);
  }

  CTX_wm_window_set(C, win_ctx);
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Window Close
 * \{ */

void wm_window_close(bContext *C, wmWindowManager *wm, wmWindow *win)
{
  wmWindow *win_other;

  /* First check if there is another main window remaining. */
  for (win_other = static_cast<wmWindow *>(wm->windows.first); win_other;
       win_other = win_other->next)
  {
    if (win_other != win && win_other->parent == nullptr && !WM_window_is_temp_screen(win_other)) {
      break;
    }
  }

  if (win->parent == nullptr && win_other == nullptr) {
    wm_quit_with_optional_confirmation_prompt(C, win);
    return;
  }

  /* Close child windows */
  LISTBASE_FOREACH_MUTABLE (wmWindow *, iter_win, &wm->windows) {
    if (iter_win->parent == win) {
      wm_window_close(C, wm, iter_win);
    }
  }

  bScreen *screen = WM_window_get_active_screen(win);
  WorkSpace *workspace = WM_window_get_active_workspace(win);
  WorkSpaceLayout *layout = BKE_workspace_active_layout_get(win->workspace_hook);

  BLI_remlink(&wm->windows, win);

  CTX_wm_window_set(C, win); /* needed by handlers */
  WM_event_remove_handlers(C, &win->handlers);

  WM_event_remove_handlers(C, &win->modalhandlers);

  /* for regular use this will _never_ be nullptr,
   * however we may be freeing an improperly initialized window. */
  if (screen) {
    ED_screen_exit(C, win, screen);
  }

  wm_window_free(C, wm, win);

  /* if temp screen, delete it after window free (it stops jobs that can access it) */
  if (screen && screen->temp) {
    Main *bmain = CTX_data_main(C);

    BLI_assert(BKE_workspace_layout_screen_get(layout) == screen);
    BKE_workspace_layout_remove(bmain, workspace, layout);
    WM_event_add_notifier(C, NC_SCREEN | ND_LAYOUTDELETE, nullptr);
  }
}

void wm_window_title(wmWindowManager *wm, wmWindow *win)
{
  if (win->ghostwin == nullptr) {
    return;
  }

  if (WM_window_is_temp_screen(win)) {
    /* Nothing to do for 'temp' windows,
     * because #WM_window_open always sets window title. */
    return;
  }

  GHOST_WindowHandle handle = static_cast<GHOST_WindowHandle>(win->ghostwin);

  const char *filepath = BKE_main_blendfile_path_from_global();
  const char *filename = BLI_path_basename(filepath);

  const bool has_filepath = filepath[0] != '\0';
  const bool include_filepath = has_filepath && (filepath != filename) &&
                                (GHOST_SetPath(handle, filepath) == GHOST_kFailure);

  std::string str;
  str += wm->file_saved ? " " : "* ";
  if (has_filepath) {
    const size_t filename_no_ext_len = BLI_path_extension_or_end(filename) - filename;
    str.append(filename, filename_no_ext_len);
  }
  else {
    str += IFACE_("(Unsaved)");
  }

  if (G_MAIN->recovered) {
    str += IFACE_(" (Recovered)");
  }

  if (include_filepath) {
    str += " [";
    str += filepath;
    str += "]";
  }

  str += " - Blender ";
  str += BKE_blender_version_string_compact();

  GHOST_SetTitle(handle, str.c_str());

  /* Informs GHOST of unsaved changes to set the window modified visual indicator (macOS)
   * and to give a hint of unsaved changes for a user warning mechanism in case of OS application
   * terminate request (e.g., OS Shortcut Alt+F4, Command+Q, (...) or session end). */
  GHOST_SetWindowModifiedState(handle, bool(!wm->file_saved));
}

void WM_window_set_dpi(const wmWindow *win)
{
  float auto_dpi = GHOST_GetDPIHint(static_cast<GHOST_WindowHandle>(win->ghostwin));

  /* Clamp auto DPI to 96, since our font/interface drawing does not work well
   * with lower sizes. The main case we are interested in supporting is higher
   * DPI. If a smaller UI is desired it is still possible to adjust UI scale. */
  auto_dpi = max_ff(auto_dpi, 96.0f);

  /* Lazily init UI scale size, preserving backwards compatibility by
   * computing UI scale from ratio of previous DPI and auto DPI */
  if (U.ui_scale == 0) {
    int virtual_pixel = (U.virtual_pixel == VIRTUAL_PIXEL_NATIVE) ? 1 : 2;

    if (U.dpi == 0) {
      U.ui_scale = virtual_pixel;
    }
    else {
      U.ui_scale = (virtual_pixel * U.dpi * 96.0f) / (auto_dpi * 72.0f);
    }

    CLAMP(U.ui_scale, 0.25f, 4.0f);
  }

  /* Blender's UI drawing assumes DPI 72 as a good default following macOS
   * while Windows and Linux use DPI 96. GHOST assumes a default 96 so we
   * remap the DPI to Blender's convention. */
  auto_dpi *= GHOST_GetNativePixelSize(static_cast<GHOST_WindowHandle>(win->ghostwin));
  U.dpi = auto_dpi * U.ui_scale * (72.0 / 96.0f);

  /* Automatically set larger pixel size for high DPI. */
  int pixelsize = max_ii(1, int(U.dpi / 64));
  /* User adjustment for pixel size. */
  pixelsize = max_ii(1, pixelsize + U.ui_line_width);

  /* Set user preferences globals for drawing, and for forward compatibility. */
  U.pixelsize = pixelsize;
  U.virtual_pixel = (pixelsize == 1) ? VIRTUAL_PIXEL_NATIVE : VIRTUAL_PIXEL_DOUBLE;
  U.scale_factor = U.dpi / 72.0f;
  U.inv_scale_factor = 1.0f / U.scale_factor;

  /* Widget unit is 20 pixels at 1X scale. This consists of 18 user-scaled units plus
   * left and right borders of line-width (pixel-size). */
  U.widget_unit = int(roundf(18.0f * U.scale_factor)) + (2 * pixelsize);
}

/**
 * When windows are activated, simulate modifier press/release to match the current state of
 * held modifier keys, see #40317.
 *
 * NOTE(@ideasman42): There is a bug in Windows11 where Alt-Tab sends an Alt-press event
 * to the window after it's deactivated, this means window de-activation is not a fool-proof
 * way of ensuring modifier keys are cleared for inactive windows. So any event added to an
 * inactive window must run #wm_window_update_eventstate_modifiers first to ensure no modifier
 * keys are held. See: #105277.
 */
static void wm_window_update_eventstate_modifiers(wmWindowManager *wm,
                                                  wmWindow *win,
                                                  const uint64_t event_time_ms)
{
  const uint8_t keymodifier_sided[2] = {
      wm_ghost_modifier_query(MOD_SIDE_LEFT),
      wm_ghost_modifier_query(MOD_SIDE_RIGHT),
  };
  const uint8_t keymodifier = keymodifier_sided[0] | keymodifier_sided[1];
  const uint8_t keymodifier_eventstate = win->eventstate->modifier;
  if (keymodifier != keymodifier_eventstate) {
    GHOST_TEventKeyData kdata{};
    kdata.key = GHOST_kKeyUnknown;
    kdata.utf8_buf[0] = '\0';
    kdata.is_repeat = false;
    for (int i = 0; i < ARRAY_SIZE(g_modifier_table); i++) {
      if (keymodifier_eventstate & g_modifier_table[i].flag) {
        if ((keymodifier & g_modifier_table[i].flag) == 0) {
          for (int side = 0; side < 2; side++) {
            if ((keymodifier_sided[side] & g_modifier_table[i].flag) == 0) {
              kdata.key = g_modifier_table[i].ghost_key_pair[side];
              wm_event_add_ghostevent(wm, win, GHOST_kEventKeyUp, &kdata, event_time_ms);
              /* Only ever send one release event
               * (currently releasing multiple isn't needed and only confuses logic). */
              break;
            }
          }
        }
      }
      else {
        if (keymodifier & g_modifier_table[i].flag) {
          for (int side = 0; side < 2; side++) {
            if (keymodifier_sided[side] & g_modifier_table[i].flag) {
              kdata.key = g_modifier_table[i].ghost_key_pair[side];
              wm_event_add_ghostevent(wm, win, GHOST_kEventKeyDown, &kdata, event_time_ms);
            }
          }
        }
      }
    }
  }
}

/**
 * When the window is de-activated, release all held modifiers.
 *
 * Needed so events generated over unfocused (non-active) windows don't have modifiers held.
 * Since modifier press/release events aren't send to unfocused windows it's best to assume
 * modifiers are not pressed. This means when modifiers *are* held, events will incorrectly
 * reported as not being held. Since this is standard behavior for Linux/MS-Window,
 * opt to use this.
 *
 * NOTE(@ideasman42): Events generated for non-active windows are rare,
 * this happens when using the mouse-wheel over an unfocused window, see: #103722.
 */
static void wm_window_update_eventstate_modifiers_clear(wmWindowManager *wm,
                                                        wmWindow *win,
                                                        const uint64_t event_time_ms)
{
  /* Release all held modifiers before de-activating the window. */
  if (win->eventstate->modifier != 0) {
    const uint8_t keymodifier_eventstate = win->eventstate->modifier;
    const uint8_t keymodifier_l = wm_ghost_modifier_query(MOD_SIDE_LEFT);
    const uint8_t keymodifier_r = wm_ghost_modifier_query(MOD_SIDE_RIGHT);
    /* NOTE(@ideasman42): when non-zero, there are modifiers held in
     * `win->eventstate` which are not considered held by the GHOST internal state.
     * While this should not happen, it's important all modifier held in event-state
     * receive release events. Without this, so any events generated while the window
     * is *not* active will have modifiers held. */
    const uint8_t keymodifier_unhandled = keymodifier_eventstate &
                                          ~(keymodifier_l | keymodifier_r);
    const uint8_t keymodifier_sided[2] = {
        uint8_t(keymodifier_l | keymodifier_unhandled),
        keymodifier_r,
    };
    GHOST_TEventKeyData kdata{};
    kdata.key = GHOST_kKeyUnknown;
    kdata.utf8_buf[0] = '\0';
    kdata.is_repeat = false;
    for (int i = 0; i < ARRAY_SIZE(g_modifier_table); i++) {
      if (keymodifier_eventstate & g_modifier_table[i].flag) {
        for (int side = 0; side < 2; side++) {
          if ((keymodifier_sided[side] & g_modifier_table[i].flag) == 0) {
            kdata.key = g_modifier_table[i].ghost_key_pair[side];
            wm_event_add_ghostevent(wm, win, GHOST_kEventKeyUp, &kdata, event_time_ms);
          }
        }
      }
    }
  }
}

static void wm_window_update_eventstate(wmWindow *win)
{
  /* Update mouse position when a window is activated. */
  int xy[2];
  if (wm_cursor_position_get(win, &xy[0], &xy[1])) {
    copy_v2_v2_int(win->eventstate->xy, xy);
  }
}

static void wm_window_ensure_eventstate(wmWindow *win)
{
  if (win->eventstate) {
    return;
  }

  win->eventstate = static_cast<wmEvent *>(MEM_callocN(sizeof(wmEvent), "window event state"));
  wm_window_update_eventstate(win);
}

/* belongs to below */
static void wm_window_ghostwindow_add(wmWindowManager *wm,
                                      const char *title,
                                      wmWindow *win,
                                      bool is_dialog)
{
  /* A new window is created when page-flip mode is required for a window. */
  GHOST_GPUSettings gpuSettings = {0};
  if (win->stereo3d_format->display_mode == S3D_DISPLAY_PAGEFLIP) {
    gpuSettings.flags |= GHOST_gpuStereoVisual;
  }

  if (G.debug & G_DEBUG_GPU) {
    gpuSettings.flags |= GHOST_gpuDebugContext;
  }

  eGPUBackendType gpu_backend = GPU_backend_type_selection_get();
  gpuSettings.context_type = wm_ghost_drawing_context_type(gpu_backend);

  int posx = 0;
  int posy = 0;

  if (WM_capabilities_flag() & WM_CAPABILITY_WINDOW_POSITION) {
    int scr_w, scr_h;
    if (wm_get_desktopsize(&scr_w, &scr_h)) {
      posx = win->posx;
      posy = (scr_h - win->posy - win->sizey);
    }
  }

  /* Clear drawable so we can set the new window. */
  wmWindow *prev_windrawable = wm->windrawable;
  wm_window_clear_drawable(wm);

  GHOST_WindowHandle ghostwin = GHOST_CreateWindow(
      g_system,
      static_cast<GHOST_WindowHandle>((win->parent) ? win->parent->ghostwin : nullptr),
      title,
      posx,
      posy,
      win->sizex,
      win->sizey,
      (GHOST_TWindowState)win->windowstate,
      is_dialog,
      gpuSettings);

  if (ghostwin) {
    win->gpuctx = GPU_context_create(ghostwin, nullptr);
    GPU_render_begin();

    /* needed so we can detect the graphics card below */
    GPU_init();

    /* Set window as drawable upon creation. Note this has already been
     * it has already been activated by GHOST_CreateWindow. */
    wm_window_set_drawable(wm, win, false);

    win->ghostwin = ghostwin;
    GHOST_SetWindowUserData(ghostwin, win); /* pointer back */

    wm_window_ensure_eventstate(win);

    /* store actual window size in blender window */
    GHOST_RectangleHandle bounds = GHOST_GetClientBounds(
        static_cast<GHOST_WindowHandle>(win->ghostwin));

    /* win32: gives undefined window size when minimized */
    if (GHOST_GetWindowState(static_cast<GHOST_WindowHandle>(win->ghostwin)) !=
        GHOST_kWindowStateMinimized)
    {
      win->sizex = GHOST_GetWidthRectangle(bounds);
      win->sizey = GHOST_GetHeightRectangle(bounds);
    }
    GHOST_DisposeRectangle(bounds);

#ifndef __APPLE__
    /* set the state here, so minimized state comes up correct on windows */
    if (wm_init_state.window_focus) {
      GHOST_SetWindowState(ghostwin, (GHOST_TWindowState)win->windowstate);
    }
#endif
    /* until screens get drawn, make it nice gray */
    GPU_clear_color(0.55f, 0.55f, 0.55f, 1.0f);

    /* needed here, because it's used before it reads userdef */
    WM_window_set_dpi(win);

    wm_window_swap_buffers(win);

    /* Clear double buffer to avoids flickering of new windows on certain drivers. (See #97600) */
    GPU_clear_color(0.55f, 0.55f, 0.55f, 1.0f);

    GPU_render_end();
  }
  else {
    wm_window_set_drawable(wm, prev_windrawable, false);
  }
}

static void wm_window_ghostwindow_ensure(wmWindowManager *wm, wmWindow *win, bool is_dialog)
{
  if (win->ghostwin == nullptr) {
    if ((win->sizex == 0) || (wm_init_state.override_flag & WIN_OVERRIDE_GEOM)) {
      win->posx = wm_init_state.start_x;
      win->posy = wm_init_state.start_y;
      win->sizex = wm_init_state.size_x;
      win->sizey = wm_init_state.size_y;

      if (wm_init_state.override_flag & WIN_OVERRIDE_GEOM) {
        win->windowstate = GHOST_kWindowStateNormal;
        wm_init_state.override_flag &= ~WIN_OVERRIDE_GEOM;
      }
      else {
        win->windowstate = GHOST_WINDOW_STATE_DEFAULT;
      }
    }

    if (wm_init_state.override_flag & WIN_OVERRIDE_WINSTATE) {
      win->windowstate = wm_init_state.windowstate;
      wm_init_state.override_flag &= ~WIN_OVERRIDE_WINSTATE;
    }

    /* without this, cursor restore may fail, #45456 */
    if (win->cursor == 0) {
      win->cursor = WM_CURSOR_DEFAULT;
    }

    wm_window_ghostwindow_add(wm, "Blender", win, is_dialog);
  }

  if (win->ghostwin != nullptr) {
    /* If we have no `ghostwin` this is a buggy window that should be removed.
     * However we still need to initialize it correctly so the screen doesn't hang. */

    /* Happens after file-read. */
    wm_window_ensure_eventstate(win);

    WM_window_set_dpi(win);
  }

  /* add keymap handlers (1 handler for all keys in map!) */
  wmKeyMap *keymap = WM_keymap_ensure(wm->defaultconf, "Window", SPACE_EMPTY, RGN_TYPE_WINDOW);
  WM_event_add_keymap_handler(&win->handlers, keymap);

  keymap = WM_keymap_ensure(wm->defaultconf, "Screen", SPACE_EMPTY, RGN_TYPE_WINDOW);
  WM_event_add_keymap_handler(&win->handlers, keymap);

  keymap = WM_keymap_ensure(wm->defaultconf, "Screen Editing", SPACE_EMPTY, RGN_TYPE_WINDOW);
  WM_event_add_keymap_handler(&win->modalhandlers, keymap);

  /* Add drop boxes. */
  {
    ListBase *lb = WM_dropboxmap_find("Window", SPACE_EMPTY, RGN_TYPE_WINDOW);
    WM_event_add_dropbox_handler(&win->handlers, lb);
  }
  wm_window_title(wm, win);

  /* Add top-bar. */
  ED_screen_global_areas_refresh(win);
}

void wm_window_ghostwindows_ensure(wmWindowManager *wm)
{
  BLI_assert(G.background == false);

  /* No command-line prefsize? then we set this.
   * Note that these values will be used only
   * when there is no startup.blend yet.
   */
  if (wm_init_state.size_x == 0) {
    if (UNLIKELY(!wm_get_screensize(&wm_init_state.size_x, &wm_init_state.size_y))) {
      /* Use fallback values. */
      wm_init_state.size_x = 0;
      wm_init_state.size_y = 0;
    }

    /* NOTE: this isn't quite correct, active screen maybe offset 1000s if PX,
     * we'd need a #wm_get_screensize like function that gives offset,
     * in practice the window manager will likely move to the correct monitor */
    wm_init_state.start_x = 0;
    wm_init_state.start_y = 0;
  }

  LISTBASE_FOREACH (wmWindow *, win, &wm->windows) {
    wm_window_ghostwindow_ensure(wm, win, false);
  }
}

void wm_window_ghostwindows_remove_invalid(bContext *C, wmWindowManager *wm)
{
  BLI_assert(G.background == false);

  LISTBASE_FOREACH_MUTABLE (wmWindow *, win, &wm->windows) {
    if (win->ghostwin == nullptr) {
      wm_window_close(C, wm, win);
    }
  }
}

/* Update window size and position based on data from GHOST window. */
static bool wm_window_update_size_position(wmWindow *win)
{
  GHOST_RectangleHandle client_rect = GHOST_GetClientBounds(
      static_cast<GHOST_WindowHandle>(win->ghostwin));
  int l, t, r, b;
  GHOST_GetRectangle(client_rect, &l, &t, &r, &b);

  GHOST_DisposeRectangle(client_rect);

  int sizex = r - l;
  int sizey = b - t;

  int posx = 0;
  int posy = 0;

  if (WM_capabilities_flag() & WM_CAPABILITY_WINDOW_POSITION) {
    int scr_w, scr_h;
    if (wm_get_desktopsize(&scr_w, &scr_h)) {
      posx = l;
      posy = scr_h - t - win->sizey;
    }
  }

  if (win->sizex != sizex || win->sizey != sizey || win->posx != posx || win->posy != posy) {
    win->sizex = sizex;
    win->sizey = sizey;
    win->posx = posx;
    win->posy = posy;
    return true;
  }
  return false;
}

wmWindow *WM_window_open(bContext *C,
                         const char *title,
                         const rcti *rect_unscaled,
                         int space_type,
                         bool toplevel,
                         bool dialog,
                         bool temp,
                         eWindowAlignment alignment,
                         void (*area_setup_fn)(bScreen *screen, ScrArea *area, void *user_data),
                         void *area_setup_user_data)
{
  Main *bmain = CTX_data_main(C);
  wmWindowManager *wm = CTX_wm_manager(C);
  wmWindow *win_prev = CTX_wm_window(C);
  Scene *scene = CTX_data_scene(C);
  ViewLayer *view_layer = CTX_data_view_layer(C);
  int x = rect_unscaled->xmin;
  int y = rect_unscaled->ymin;
  int sizex = BLI_rcti_size_x(rect_unscaled);
  int sizey = BLI_rcti_size_y(rect_unscaled);
  rcti rect;

  const float native_pixel_size = GHOST_GetNativePixelSize(
      static_cast<GHOST_WindowHandle>(win_prev->ghostwin));
  /* convert to native OS window coordinates */
  rect.xmin = win_prev->posx + (x / native_pixel_size);
  rect.ymin = win_prev->posy + (y / native_pixel_size);
  sizex /= native_pixel_size;
  sizey /= native_pixel_size;

  if (alignment == WIN_ALIGN_LOCATION_CENTER) {
    /* Window centered around x,y location. */
    rect.xmin -= sizex / 2;
    rect.ymin -= sizey / 2;
  }
  else if (alignment == WIN_ALIGN_PARENT_CENTER) {
    /* Centered within parent. X,Y as offsets from there. */
    rect.xmin += (win_prev->sizex - sizex) / 2;
    rect.ymin += (win_prev->sizey - sizey) / 2;
  }
  else {
    /* Positioned absolutely within parent bounds. */
  }

  rect.xmax = rect.xmin + sizex;
  rect.ymax = rect.ymin + sizey;

  /* changes rect to fit within desktop */
  wm_window_check_size(&rect);

  /* Reuse temporary windows when they share the same single area. */
  wmWindow *win = nullptr;
  if (temp) {
    LISTBASE_FOREACH (wmWindow *, win_iter, &wm->windows) {
      const bScreen *screen = WM_window_get_active_screen(win_iter);
      if (screen && screen->temp && BLI_listbase_is_single(&screen->areabase)) {
        ScrArea *area = static_cast<ScrArea *>(screen->areabase.first);
        if (space_type == (area->butspacetype ? area->butspacetype : area->spacetype)) {
          win = win_iter;
          break;
        }
      }
    }
  }

  /* add new window? */
  if (win == nullptr) {
    win = wm_window_new(bmain, wm, toplevel ? nullptr : win_prev, dialog);
    win->posx = rect.xmin;
    win->posy = rect.ymin;
    win->sizex = BLI_rcti_size_x(&rect);
    win->sizey = BLI_rcti_size_y(&rect);
    *win->stereo3d_format = *win_prev->stereo3d_format;
  }

  bScreen *screen = WM_window_get_active_screen(win);

  if (WM_window_get_active_workspace(win) == nullptr) {
    WorkSpace *workspace = WM_window_get_active_workspace(win_prev);
    BKE_workspace_active_set(win->workspace_hook, workspace);
  }

  if (screen == nullptr) {
    /* add new screen layout */
    WorkSpace *workspace = WM_window_get_active_workspace(win);
    WorkSpaceLayout *layout = ED_workspace_layout_add(bmain, workspace, win, "temp");

    screen = BKE_workspace_layout_screen_get(layout);
    WM_window_set_active_layout(win, workspace, layout);
  }

  /* Set scene and view layer to match original window. */
  STRNCPY(win->view_layer_name, view_layer->name);
  if (WM_window_get_active_scene(win) != scene) {
    /* No need to refresh the tool-system as the window has not yet finished being setup. */
    ED_screen_scene_change(C, win, scene, false);
  }

  screen->temp = temp;

  /* make window active, and validate/resize */
  CTX_wm_window_set(C, win);
  const bool new_window = (win->ghostwin == nullptr);
  if (new_window) {
    wm_window_ghostwindow_ensure(wm, win, dialog);
  }
  WM_check(C);

  /* It's possible `win->ghostwin == nullptr`.
   * instead of attempting to cleanup here (in a half finished state),
   * finish setting up the screen, then free it at the end of the function,
   * to avoid having to take into account a partially-created window.
   */

  if (area_setup_fn) {
    /* When the caller is setting up the area, it should always be empty
     * because it's expected the callback sets the type. */
    BLI_assert(space_type == SPACE_EMPTY);
    /* NOTE(@ideasman42): passing in a callback to setup the `area` is admittedly awkward.
     * This is done so #ED_screen_refresh has a valid area to initialize,
     * otherwise it will attempt to make the empty area usable via #ED_area_init.
     * While refreshing the window could be postponed this makes the state of the
     * window less predictable to the caller. */
    ScrArea *area = static_cast<ScrArea *>(screen->areabase.first);
    area_setup_fn(screen, area, area_setup_user_data);
    CTX_wm_area_set(C, area);
  }
  else if (space_type != SPACE_EMPTY) {
    /* Ensure it shows the right space-type editor. */
    ScrArea *area = static_cast<ScrArea *>(screen->areabase.first);
    CTX_wm_area_set(C, area);
    ED_area_newspace(C, area, space_type, false);
  }

  ED_screen_change(C, screen);

  if (!new_window) {
    /* Set size in GHOST window and then update size and position from GHOST,
     * in case they where changed by GHOST to fit the monitor/screen. */
    wm_window_set_size(win, win->sizex, win->sizey);
    wm_window_update_size_position(win);
  }

  /* Refresh screen dimensions, after the effective window size is known. */
  ED_screen_refresh(wm, win);

  if (win->ghostwin) {
    wm_window_raise(win);
    GHOST_SetTitle(static_cast<GHOST_WindowHandle>(win->ghostwin), title);
    return win;
  }

  /* very unlikely! but opening a new window can fail */
  wm_window_close(C, wm, win);
  CTX_wm_window_set(C, win_prev);

  return nullptr;
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Operators
 * \{ */

int wm_window_close_exec(bContext *C, wmOperator * /*op*/)
{
  wmWindowManager *wm = CTX_wm_manager(C);
  wmWindow *win = CTX_wm_window(C);
  wm_window_close(C, wm, win);
  return OPERATOR_FINISHED;
}

int wm_window_new_exec(bContext *C, wmOperator *op)
{
  wmWindow *win_src = CTX_wm_window(C);
  ScrArea *area = BKE_screen_find_big_area(CTX_wm_screen(C), SPACE_TYPE_ANY, 0);
  const rcti window_rect = {
      /*xmin*/ 0,
      /*xmax*/ int(win_src->sizex * 0.95f),
      /*ymin*/ 0,
      /*ymax*/ int(win_src->sizey * 0.9f),
  };

  bool ok = (WM_window_open(C,
                            IFACE_("Blender"),
                            &window_rect,
                            area->spacetype,
                            false,
                            false,
                            false,
                            WIN_ALIGN_PARENT_CENTER,
                            nullptr,
                            nullptr) != nullptr);

  if (!ok) {
    BKE_report(op->reports, RPT_ERROR, "Failed to create window");
    return OPERATOR_CANCELLED;
  }
  return OPERATOR_FINISHED;
}

int wm_window_new_main_exec(bContext *C, wmOperator *op)
{
  wmWindow *win_src = CTX_wm_window(C);

  bool ok = (wm_window_copy_test(C, win_src, true, false) != nullptr);
  if (!ok) {
    BKE_report(op->reports, RPT_ERROR, "Failed to create window");
    return OPERATOR_CANCELLED;
  }
  return OPERATOR_FINISHED;
}

int wm_window_fullscreen_toggle_exec(bContext *C, wmOperator * /*op*/)
{
  wmWindow *window = CTX_wm_window(C);

  if (G.background) {
    return OPERATOR_CANCELLED;
  }

  GHOST_TWindowState state = GHOST_GetWindowState(
      static_cast<GHOST_WindowHandle>(window->ghostwin));
  if (state != GHOST_kWindowStateFullScreen) {
    GHOST_SetWindowState(static_cast<GHOST_WindowHandle>(window->ghostwin),
                         GHOST_kWindowStateFullScreen);
  }
  else {
    GHOST_SetWindowState(static_cast<GHOST_WindowHandle>(window->ghostwin),
                         GHOST_kWindowStateNormal);
  }

  return OPERATOR_FINISHED;
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Events
 * \{ */

void wm_cursor_position_from_ghost_client_coords(wmWindow *win, int *x, int *y)
{
  float fac = GHOST_GetNativePixelSize(static_cast<GHOST_WindowHandle>(win->ghostwin));
  *x *= fac;

  *y = (win->sizey - 1) - *y;
  *y *= fac;
}

void wm_cursor_position_to_ghost_client_coords(wmWindow *win, int *x, int *y)
{
  float fac = GHOST_GetNativePixelSize(static_cast<GHOST_WindowHandle>(win->ghostwin));

  *x /= fac;
  *y /= fac;
  *y = win->sizey - *y - 1;
}

void wm_cursor_position_from_ghost_screen_coords(wmWindow *win, int *x, int *y)
{
  GHOST_ScreenToClient(static_cast<GHOST_WindowHandle>(win->ghostwin), *x, *y, x, y);
  wm_cursor_position_from_ghost_client_coords(win, x, y);
}

void wm_cursor_position_to_ghost_screen_coords(wmWindow *win, int *x, int *y)
{
  wm_cursor_position_to_ghost_client_coords(win, x, y);
  GHOST_ClientToScreen(static_cast<GHOST_WindowHandle>(win->ghostwin), *x, *y, x, y);
}

bool wm_cursor_position_get(wmWindow *win, int *r_x, int *r_y)
{
  if (UNLIKELY(G.f & G_FLAG_EVENT_SIMULATE)) {
    *r_x = win->eventstate->xy[0];
    *r_y = win->eventstate->xy[1];
    return true;
  }

  if (GHOST_GetCursorPosition(
          g_system, static_cast<GHOST_WindowHandle>(win->ghostwin), r_x, r_y) == GHOST_kSuccess)
  {
    wm_cursor_position_from_ghost_client_coords(win, r_x, r_y);
    return true;
  }

  return false;
}

/** Check if specified modifier key type is pressed. */
static uint8_t wm_ghost_modifier_query(const enum ModSide side)
{
  uint8_t result = 0;
  for (int i = 0; i < ARRAY_SIZE(g_modifier_table); i++) {
    bool val = false;
    GHOST_GetModifierKeyState(g_system, g_modifier_table[i].ghost_mask_pair[side], &val);
    if (val) {
      result |= g_modifier_table[i].flag;
    }
  }
  return result;
}

static void wm_window_set_drawable(wmWindowManager *wm, wmWindow *win, bool activate)
{
  BLI_assert(ELEM(wm->windrawable, nullptr, win));

  wm->windrawable = win;
  if (activate) {
    GHOST_ActivateWindowDrawingContext(static_cast<GHOST_WindowHandle>(win->ghostwin));
  }
  GPU_context_active_set(static_cast<GPUContext *>(win->gpuctx));
}

void wm_window_clear_drawable(wmWindowManager *wm)
{
  if (wm->windrawable) {
    wm->windrawable = nullptr;
  }
}

void wm_window_make_drawable(wmWindowManager *wm, wmWindow *win)
{
  BLI_assert(GPU_framebuffer_active_get() == GPU_framebuffer_back_get());

  if (win != wm->windrawable && win->ghostwin) {
    // win->lmbut = 0; /* Keeps hanging when mouse-pressed while other window opened. */
    wm_window_clear_drawable(wm);

    if (G.debug & G_DEBUG_EVENTS) {
      printf("%s: set drawable %d\n", __func__, win->winid);
    }

    wm_window_set_drawable(wm, win, true);
  }

  if (win->ghostwin) {
    /* this can change per window */
    WM_window_set_dpi(win);
  }
}

void wm_window_reset_drawable()
{
  BLI_assert(BLI_thread_is_main());
  BLI_assert(GPU_framebuffer_active_get() == GPU_framebuffer_back_get());
  wmWindowManager *wm = static_cast<wmWindowManager *>(G_MAIN->wm.first);

  if (wm == nullptr) {
    return;
  }
  wmWindow *win = wm->windrawable;

  if (win && win->ghostwin) {
    wm_window_clear_drawable(wm);
    wm_window_set_drawable(wm, win, true);
  }
}

/**
 * Called by ghost, here we handle events for windows themselves or send to event system.
 *
 * Mouse coordinate conversion happens here.
 */
static bool ghost_event_proc(GHOST_EventHandle evt, GHOST_TUserDataPtr C_void_ptr)
{
  bContext *C = static_cast<bContext *>(C_void_ptr);
  wmWindowManager *wm = CTX_wm_manager(C);
  GHOST_TEventType type = GHOST_GetEventType(evt);

  GHOST_WindowHandle ghostwin = GHOST_GetEventWindow(evt);

  if (type == GHOST_kEventQuitRequest) {
    /* Find an active window to display quit dialog in. */
    wmWindow *win;
    if (ghostwin && GHOST_ValidWindow(g_system, ghostwin)) {
      win = static_cast<wmWindow *>(GHOST_GetWindowUserData(ghostwin));
    }
    else {
      win = wm->winactive;
    }

    /* Display quit dialog or quit immediately. */
    if (win) {
      wm_quit_with_optional_confirmation_prompt(C, win);
    }
    else {
      wm_exit_schedule_delayed(C);
    }
    return true;
  }

  GHOST_TEventDataPtr data = GHOST_GetEventData(evt);
  const uint64_t event_time_ms = GHOST_GetEventTime(evt);

  /* Ghost now can call this function for life resizes,
   * but it should return if WM didn't initialize yet.
   * Can happen on file read (especially full size window). */
  if ((wm->init_flag & WM_INIT_FLAG_WINDOW) == 0) {
    return true;
  }
  if (!ghostwin) {
    /* XXX: should be checked, why are we getting an event here, and what is it? */
    puts("<!> event has no window");
    return true;
  }
  if (!GHOST_ValidWindow(g_system, ghostwin)) {
    /* XXX: should be checked, why are we getting an event here, and what is it? */
    puts("<!> event has invalid window");
    return true;
  }

  wmWindow *win = static_cast<wmWindow *>(GHOST_GetWindowUserData(ghostwin));

  switch (type) {
    case GHOST_kEventWindowDeactivate: {
      wm_window_update_eventstate_modifiers_clear(wm, win, event_time_ms);

      wm_event_add_ghostevent(wm, win, type, data, event_time_ms);
      win->active = 0;
      break;
    }
    case GHOST_kEventWindowActivate: {
      /* Ensure the event state matches modifiers (window was inactive). */
      wm_window_update_eventstate_modifiers(wm, win, event_time_ms);

      /* Entering window, update mouse position (without sending an event). */
      wm_window_update_eventstate(win);

      /* No context change! `C->wm->windrawable` is drawable, or for area queues. */
      wm->winactive = win;
      win->active = 1;

      /* keymodifier zero, it hangs on hotkeys that open windows otherwise */
      win->eventstate->keymodifier = 0;

      win->addmousemove = 1; /* enables highlighted buttons */

      wm_window_make_drawable(wm, win);

      /* window might be focused by mouse click in configuration of window manager
       * when focus is not following mouse
       * click could have been done on a button and depending on window manager settings
       * click would be passed to blender or not, but in any case button under cursor
       * should be activated, so at max next click on button without moving mouse
       * would trigger its handle function
       * currently it seems to be common practice to generate new event for, but probably
       * we'll need utility function for this? (sergey)
       */
      wmEvent event;
      wm_event_init_from_window(win, &event);
      event.type = MOUSEMOVE;
      event.val = KM_NOTHING;
      copy_v2_v2_int(event.prev_xy, event.xy);
      event.flag = eWM_EventFlag(0);

      wm_event_add(win, &event);

      break;
    }
    case GHOST_kEventWindowClose: {
      wm_window_close(C, wm, win);
      break;
    }
    case GHOST_kEventWindowUpdate: {
      if (G.debug & G_DEBUG_EVENTS) {
        printf("%s: ghost redraw %d\n", __func__, win->winid);
      }

      wm_window_make_drawable(wm, win);
      WM_event_add_notifier(C, NC_WINDOW, nullptr);

      break;
    }
    case GHOST_kEventWindowUpdateDecor: {
      if (G.debug & G_DEBUG_EVENTS) {
        printf("%s: ghost redraw decor %d\n", __func__, win->winid);
      }

      wm_window_make_drawable(wm, win);
#if 0
        /* NOTE(@ideasman42): Ideally we could swap-buffers to avoid a full redraw.
         * however this causes window flickering on resize with LIBDECOR under WAYLAND. */
        wm_window_swap_buffers(win);
#else
      WM_event_add_notifier(C, NC_WINDOW, nullptr);
#endif

      break;
    }
    case GHOST_kEventWindowSize:
    case GHOST_kEventWindowMove: {
      GHOST_TWindowState state = GHOST_GetWindowState(
          static_cast<GHOST_WindowHandle>(win->ghostwin));
      win->windowstate = state;

      WM_window_set_dpi(win);

      /* win32: gives undefined window size when minimized */
      if (state != GHOST_kWindowStateMinimized) {
        /*
         * Ghost sometimes send size or move events when the window hasn't changed.
         * One case of this is using COMPIZ on Linux.
         * To alleviate the problem we ignore all such event here.
         *
         * It might be good to eventually do that at GHOST level, but that is for another time.
         */
        if (wm_window_update_size_position(win)) {
          const bScreen *screen = WM_window_get_active_screen(win);

          /* debug prints */
          if (G.debug & G_DEBUG_EVENTS) {
            const char *state_str;
            state = GHOST_GetWindowState(static_cast<GHOST_WindowHandle>(win->ghostwin));

            if (state == GHOST_kWindowStateNormal) {
              state_str = "normal";
            }
            else if (state == GHOST_kWindowStateMinimized) {
              state_str = "minimized";
            }
            else if (state == GHOST_kWindowStateMaximized) {
              state_str = "maximized";
            }
            else if (state == GHOST_kWindowStateFullScreen) {
              state_str = "full-screen";
            }
            else {
              state_str = "<unknown>";
            }

            printf("%s: window %d state = %s\n", __func__, win->winid, state_str);

            if (type != GHOST_kEventWindowSize) {
              printf("win move event pos %d %d size %d %d\n",
                     win->posx,
                     win->posy,
                     win->sizex,
                     win->sizey);
            }
          }

          wm_window_make_drawable(wm, win);
          BKE_icon_changed(screen->id.icon_id);
          WM_event_add_notifier(C, NC_SCREEN | NA_EDITED, nullptr);
          WM_event_add_notifier(C, NC_WINDOW | NA_EDITED, nullptr);

#if defined(__APPLE__) || defined(WIN32)
          /* MACOS and WIN32 don't return to the main-loop while resize. */
          int dummy_sleep_ms = 0;
          wm_window_timers_process(C, &dummy_sleep_ms);
          wm_event_do_handlers(C);
          wm_event_do_notifiers(C);
          wm_draw_update(C);
#endif
        }
      }
      break;
    }

    case GHOST_kEventWindowDPIHintChanged: {
      WM_window_set_dpi(win);
      /* font's are stored at each DPI level, without this we can easy load 100's of fonts */
      BLF_cache_clear();

      WM_main_add_notifier(NC_WINDOW, nullptr);             /* full redraw */
      WM_main_add_notifier(NC_SCREEN | NA_EDITED, nullptr); /* refresh region sizes */
      break;
    }

    case GHOST_kEventOpenMainFile: {
      const char *path = static_cast<const char *>(data);

      if (path) {
        wmOperatorType *ot = WM_operatortype_find("WM_OT_open_mainfile", false);
        /* operator needs a valid window in context, ensures
         * it is correctly set */
        CTX_wm_window_set(C, win);

        PointerRNA props_ptr;
        WM_operator_properties_create_ptr(&props_ptr, ot);
        RNA_string_set(&props_ptr, "filepath", path);
        RNA_boolean_set(&props_ptr, "display_file_selector", false);
        WM_operator_name_call_ptr(C, ot, WM_OP_INVOKE_DEFAULT, &props_ptr, nullptr);
        WM_operator_properties_free(&props_ptr);

        CTX_wm_window_set(C, nullptr);
      }
      break;
    }
    case GHOST_kEventDraggingDropDone: {
      const GHOST_TEventDragnDropData *ddd = static_cast<const GHOST_TEventDragnDropData *>(data);

      /* Ensure the event state matches modifiers (window was inactive). */
      wm_window_update_eventstate_modifiers(wm, win, event_time_ms);
      /* Entering window, update mouse position (without sending an event). */
      wm_window_update_eventstate(win);

      wmEvent event;
      wm_event_init_from_window(win, &event); /* copy last state, like mouse coords */

      /* activate region */
      event.type = MOUSEMOVE;
      event.val = KM_NOTHING;
      copy_v2_v2_int(event.prev_xy, event.xy);

      copy_v2_v2_int(event.xy, &ddd->x);
      wm_cursor_position_from_ghost_screen_coords(win, &event.xy[0], &event.xy[1]);

      /* The values from #wm_window_update_eventstate may not match (under WAYLAND they don't)
       * Write this into the event state. */
      copy_v2_v2_int(win->eventstate->xy, event.xy);

      event.flag = eWM_EventFlag(0);

      /* No context change! `C->wm->windrawable` is drawable, or for area queues. */
      wm->winactive = win;
      win->active = 1;

      wm_event_add(win, &event);

      /* make blender drop event with custom data pointing to wm drags */
      event.type = EVT_DROP;
      event.val = KM_RELEASE;
      event.custom = EVT_DATA_DRAGDROP;
      event.customdata = &wm->drags;
      event.customdata_free = true;

      wm_event_add(win, &event);

      // printf("Drop detected\n");

      /* add drag data to wm for paths: */

      if (ddd->dataType == GHOST_kDragnDropTypeFilenames) {
        const GHOST_TStringArray *stra = static_cast<const GHOST_TStringArray *>(ddd->data);

        for (int a = 0; a < stra->count; a++) {
          printf("drop file %s\n", stra->strings[a]);
          /* try to get icon type from extension */
          int icon = ED_file_extension_icon((char *)stra->strings[a]);
          wmDragPath *path_data = WM_drag_create_path_data((char *)stra->strings[a]);
          WM_event_start_drag(C, icon, WM_DRAG_PATH, path_data, 0.0, WM_DRAG_NOP);
          /* Void pointer should point to string, it makes a copy. */
          break; /* only one drop element supported now */
        }
      }

      break;
    }
    case GHOST_kEventNativeResolutionChange: {
      /* Only update if the actual pixel size changes. */
      float prev_pixelsize = U.pixelsize;
      WM_window_set_dpi(win);

      if (U.pixelsize != prev_pixelsize) {
        BKE_icon_changed(WM_window_get_active_screen(win)->id.icon_id);

        /* Close all popups since they are positioned with the pixel
         * size baked in and it's difficult to correct them. */
        CTX_wm_window_set(C, win);
        UI_popup_handlers_remove_all(C, &win->modalhandlers);
        CTX_wm_window_set(C, nullptr);

        wm_window_make_drawable(wm, win);

        WM_event_add_notifier(C, NC_SCREEN | NA_EDITED, nullptr);
        WM_event_add_notifier(C, NC_WINDOW | NA_EDITED, nullptr);
      }

      break;
    }
    case GHOST_kEventButtonDown:
    case GHOST_kEventButtonUp: {
      if (win->active == 0) {
        /* Entering window, update cursor/tablet state & modifiers.
         * (ghost sends win-activate *after* the mouse-click in window!) */
        wm_window_update_eventstate_modifiers(wm, win, event_time_ms);
        wm_window_update_eventstate(win);
      }

      wm_event_add_ghostevent(wm, win, type, data, event_time_ms);
      break;
    }
    default: {
      wm_event_add_ghostevent(wm, win, type, data, event_time_ms);
      break;
    }
  }

  return true;
}

/**
 * This timer system only gives maximum 1 timer event per redraw cycle,
 * to prevent queues to get overloaded.
 * - Timer handlers should check for delta to decide if they just update, or follow real time.
 * - Timer handlers can also set duration to match frames passed.
 *
 * \param sleep_us_p: The number of microseconds to sleep which may be reduced by this function
 * to account for timers that would run during the anticipated sleep period.
 */
static bool wm_window_timers_process(const bContext *C, int *sleep_us_p)
{
  Main *bmain = CTX_data_main(C);
  wmWindowManager *wm = CTX_wm_manager(C);
  const double time = PIL_check_seconds_timer();
  bool has_event = false;

  const int sleep_us = *sleep_us_p;
  /* The nearest time an active timer is scheduled to run.  */
  double ntime_min = DBL_MAX;

  /* Mutable in case the timer gets removed. */
  LISTBASE_FOREACH_MUTABLE (wmTimer *, wt, &wm->timers) {
    if (wt->flags & WM_TIMER_TAGGED_FOR_REMOVAL) {
      continue;
    }
    if (wt->sleep == true) {
      continue;
    }

    /* Future timer, update nearest time & skip. */
    if (wt->time_next >= time) {
      if ((has_event == false) && (sleep_us != 0)) {
        /* The timer is not ready to run but may run shortly. */
        if (wt->time_next < ntime_min) {
          ntime_min = wt->time_next;
        }
      }
      continue;
    }

    wt->time_delta = time - wt->time_last;
    wt->time_duration += wt->time_delta;
    wt->time_last = time;

    wt->time_next = wt->time_start;
    if (wt->time_step != 0.0f) {
      wt->time_next += wt->time_step * ceil(wt->time_duration / wt->time_step);
    }

    if (wt->event_type == TIMERJOBS) {
      wm_jobs_timer(wm, wt);
    }
    else if (wt->event_type == TIMERAUTOSAVE) {
      wm_autosave_timer(bmain, wm, wt);
    }
    else if (wt->event_type == TIMERNOTIFIER) {
      WM_main_add_notifier(POINTER_AS_UINT(wt->customdata), nullptr);
    }
    else if (wmWindow *win = wt->win) {
      wmEvent event;
      wm_event_init_from_window(win, &event);

      event.type = wt->event_type;
      event.val = KM_NOTHING;
      event.keymodifier = 0;
      event.flag = eWM_EventFlag(0);
      event.custom = EVT_DATA_TIMER;
      event.customdata = wt;
      wm_event_add(win, &event);

      has_event = true;
    }
  }

  if ((has_event == false) && (sleep_us != 0) && (ntime_min != DBL_MAX)) {
    /* Clamp the sleep time so next execution runs earlier (if necessary).
     * Use `ceil` so the timer is guarantee to be ready to run (not always the case with rounding).
     * Even though using `floor` or `round` is more responsive,
     * it causes CPU intensive loops that may run until the timer is reached, see: #111579. */
    const double microseconds = 1000000.0;
    const double sleep_sec = (double(sleep_us) / microseconds);
    const double sleep_sec_next = ntime_min - time;

    if (sleep_sec_next < sleep_sec) {
      *sleep_us_p = int(std::ceil(sleep_sec_next * microseconds));
    }
  }

  /* Effectively delete all timers marked for removal. */
  wm_window_timers_delete_removed(wm);

  return has_event;
}

void wm_window_events_process(const bContext *C)
{
  BLI_assert(BLI_thread_is_main());
  GPU_render_begin();

  bool has_event = GHOST_ProcessEvents(g_system, false); /* `false` is no wait. */

  if (has_event) {
    GHOST_DispatchEvents(g_system);
  }

  /* When there is no event, sleep 5 milliseconds not to use too much CPU when idle. */
  const int sleep_us_default = 5000;
  int sleep_us = has_event ? 0 : sleep_us_default;
  has_event |= wm_window_timers_process(C, &sleep_us);
#ifdef WITH_XR_OPENXR
  /* XR events don't use the regular window queues. So here we don't only trigger
   * processing/dispatching but also handling. */
  has_event |= wm_xr_events_handle(CTX_wm_manager(C));
#endif
  GPU_render_end();

  /* Skip sleeping when simulating events so tests don't idle unnecessarily as simulated
   * events are typically generated from a timer that runs in the main loop. */
  if ((has_event == false) && (sleep_us != 0) && !(G.f & G_FLAG_EVENT_SIMULATE)) {
    if (sleep_us == sleep_us_default) {
      /* NOTE(@ideasman42): prefer #PIL_sleep_ms over `sleep_for(..)` in the common case
       * because this function uses lower resolution (millisecond) resolution sleep timers
       * which are tried & true for the idle loop. We could move to C++ `sleep_for(..)`
       * if this works well on all platforms but this needs further testing. */
      PIL_sleep_ms(sleep_us_default / 1000);
    }
    else {
      /* The time was shortened to resume for the upcoming timer, use a high resolution sleep.
       * Mainly happens during animation playback but could happen immediately before any timer.
       *
       * NOTE(@ideasman42): At time of writing Windows-10-22H2 doesn't give higher precision sleep.
       * Keep the functionality as it doesn't have noticeable down sides either. */
      std::this_thread::sleep_for(std::chrono::microseconds(sleep_us));
    }
  }
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Ghost Init/Exit
 * \{ */

void wm_ghost_init(bContext *C)
{
  if (g_system) {
    return;
  }

  BLI_assert(C != nullptr);
  BLI_assert_msg(!G.background, "Use wm_ghost_init_background instead");

  GHOST_EventConsumerHandle consumer;

  consumer = GHOST_CreateEventConsumer(ghost_event_proc, C);

  GHOST_SetBacktraceHandler((GHOST_TBacktraceFn)BLI_system_backtrace);

  g_system = GHOST_CreateSystem();

  if (UNLIKELY(g_system == nullptr)) {
    /* GHOST will have reported the back-ends that failed to load. */
    fprintf(stderr, "GHOST: unable to initialize, exiting!\n");
    /* This will leak memory, it's preferable to crashing. */
    exit(EXIT_FAILURE);
  }
#if !(defined(WIN32) || defined(__APPLE__))
  g_system_backend_id = GHOST_SystemBackend();
#endif

  GHOST_Debug debug = {0};
  if (G.debug & G_DEBUG_GHOST) {
    debug.flags |= GHOST_kDebugDefault;
  }
  if (G.debug & G_DEBUG_WINTAB) {
    debug.flags |= GHOST_kDebugWintab;
  }
  GHOST_SystemInitDebug(g_system, debug);

  GHOST_AddEventConsumer(g_system, consumer);

  if (wm_init_state.native_pixels) {
    GHOST_UseNativePixels();
  }

  GHOST_UseWindowFocus(wm_init_state.window_focus);
}

void wm_ghost_init_background()
{
  /* TODO: move this to `wm_init_exit.cc`. */

  if (g_system) {
    return;
  }

  GHOST_SetBacktraceHandler((GHOST_TBacktraceFn)BLI_system_backtrace);

  g_system = GHOST_CreateSystemBackground();

  GHOST_Debug debug = {0};
  if (G.debug & G_DEBUG_GHOST) {
    debug.flags |= GHOST_kDebugDefault;
  }
  GHOST_SystemInitDebug(g_system, debug);
}

void wm_ghost_exit()
{
  if (g_system) {
    GHOST_DisposeSystem(g_system);
  }
  g_system = nullptr;
}

const char *WM_ghost_backend()
{
#if !(defined(WIN32) || defined(__APPLE__))
  return g_system_backend_id ? g_system_backend_id : "NONE";
#else
  /* While this could be supported, at the moment it's only needed with GHOST X11/WAYLAND
   * to check which was selected and the API call may be removed after that's no longer needed.
   * Use dummy values to prevent this being used on other systems. */
  return g_system ? "DEFAULT" : "NONE";
#endif
}

GHOST_TDrawingContextType wm_ghost_drawing_context_type(const eGPUBackendType gpu_backend)
{
  switch (gpu_backend) {
    case GPU_BACKEND_NONE:
      return GHOST_kDrawingContextTypeNone;
    case GPU_BACKEND_ANY:
    case GPU_BACKEND_OPENGL:
#ifdef WITH_OPENGL_BACKEND
      return GHOST_kDrawingContextTypeOpenGL;
#endif
      BLI_assert_unreachable();
      return GHOST_kDrawingContextTypeNone;
    case GPU_BACKEND_VULKAN:
#ifdef WITH_VULKAN_BACKEND
      return GHOST_kDrawingContextTypeVulkan;
#endif
      BLI_assert_unreachable();
      return GHOST_kDrawingContextTypeNone;
    case GPU_BACKEND_METAL:
#ifdef WITH_METAL_BACKEND
      return GHOST_kDrawingContextTypeMetal;
#endif
      BLI_assert_unreachable();
      return GHOST_kDrawingContextTypeNone;
  }

  /* Avoid control reaches end of non-void function compilation warning, which could be promoted
   * to error. */
  BLI_assert_unreachable();
  return GHOST_kDrawingContextTypeNone;
}

static uiBlock *block_create_opengl_usage_warning(bContext *C, ARegion *region, void * /*arg1*/)
{
  uiBlock *block = UI_block_begin(C, region, "autorun_warning_popup", UI_EMBOSS);
  UI_block_theme_style_set(block, UI_BLOCK_THEME_STYLE_POPUP);
  UI_block_emboss_set(block, UI_EMBOSS);

  uiLayout *layout = uiItemsAlertBox(block, 44, ALERT_ICON_ERROR);

  /* Title and explanation text. */
  uiLayout *col = uiLayoutColumn(layout, false);
  uiItemL_ex(col, TIP_("Python script uses OpenGL for drawing"), ICON_NONE, true, false);
  uiItemL(col, TIP_("This may lead to unexpected behavior"), ICON_NONE);
  uiItemL(col,
          TIP_("One of the add-ons or scripts is using OpenGL and will not work correct on Metal"),
          ICON_NONE);
  uiItemL(col,
          TIP_("Please contact the developer of the add-on to migrate to use 'gpu' module"),
          ICON_NONE);
  if (G.opengl_deprecation_usage_filename) {
    char location[1024];
    SNPRINTF(
        location, "%s:%d", G.opengl_deprecation_usage_filename, G.opengl_deprecation_usage_lineno);
    uiItemL(col, location, ICON_NONE);
  }
  uiItemL(col, TIP_("See system tab in preferences to switch to OpenGL backend"), ICON_NONE);

  uiItemS(layout);

  UI_block_bounds_set_centered(block, 14 * UI_SCALE_FAC);

  return block;
}

void wm_test_opengl_deprecation_warning(bContext *C)
{
  static bool message_shown = false;

  /* Exit when no failure detected. */
  if (!G.opengl_deprecation_usage_detected) {
    return;
  }

  /* Have we already shown a message during this Blender session. `bgl` calls are done in a draw
   * handler that will run many times. */
  if (message_shown) {
    return;
  }

  wmWindowManager *wm = CTX_wm_manager(C);
  wmWindow *win = static_cast<wmWindow *>((wm->winactive) ? wm->winactive : wm->windows.first);

  BKE_report(
      &wm->reports,
      RPT_ERROR,
      TIP_("One of the add-ons or scripts is using OpenGL and will not work correct on Metal. "
           "Please contact the developer of the add-on to migrate to use 'gpu' module"));

  if (win) {
    wmWindow *prevwin = CTX_wm_window(C);
    CTX_wm_window_set(C, win);
    UI_popup_block_invoke(C, block_create_opengl_usage_warning, nullptr, nullptr);
    CTX_wm_window_set(C, prevwin);
  }

  message_shown = true;
}

eWM_CapabilitiesFlag WM_capabilities_flag()
{
  static eWM_CapabilitiesFlag flag = eWM_CapabilitiesFlag(0);
  if (flag != 0) {
    return flag;
  }
  flag |= WM_CAPABILITY_INITIALIZED;

  const GHOST_TCapabilityFlag ghost_flag = GHOST_GetCapabilities();
  if (ghost_flag & GHOST_kCapabilityCursorWarp) {
    flag |= WM_CAPABILITY_CURSOR_WARP;
  }
  if (ghost_flag & GHOST_kCapabilityWindowPosition) {
    flag |= WM_CAPABILITY_WINDOW_POSITION;
  }
  if (ghost_flag & GHOST_kCapabilityPrimaryClipboard) {
    flag |= WM_CAPABILITY_PRIMARY_CLIPBOARD;
  }
  if (ghost_flag & GHOST_kCapabilityGPUReadFrontBuffer) {
    flag |= WM_CAPABILITY_GPU_FRONT_BUFFER_READ;
  }
  if (ghost_flag & GHOST_kCapabilityClipboardImages) {
    flag |= WM_CAPABILITY_CLIPBOARD_IMAGES;
  }
  if (ghost_flag & GHOST_kCapabilityDesktopSample) {
    flag |= WM_CAPABILITY_DESKTOP_SAMPLE;
  }
  if (ghost_flag & GHOST_kCapabilityInputIME) {
    flag |= WM_CAPABILITY_INPUT_IME;
  }

  return flag;
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Event Timer
 * \{ */

void WM_event_timer_sleep(wmWindowManager *wm, wmWindow * /*win*/, wmTimer *timer, bool do_sleep)
{
  /* Extra security check. */
  if (BLI_findindex(&wm->timers, timer) == -1) {
    return;
  }
  /* It's disputable if this is needed, when tagged for removal,
   * the sleep value won't be used anyway. */
  if (timer->flags & WM_TIMER_TAGGED_FOR_REMOVAL) {
    return;
  }
  timer->sleep = do_sleep;
}

wmTimer *WM_event_timer_add(wmWindowManager *wm, wmWindow *win, int event_type, double time_step)
{
  wmTimer *wt = static_cast<wmTimer *>(MEM_callocN(sizeof(wmTimer), "window timer"));
  BLI_assert(time_step >= 0.0f);

  wt->event_type = event_type;
  wt->time_last = PIL_check_seconds_timer();
  wt->time_next = wt->time_last + time_step;
  wt->time_start = wt->time_last;
  wt->time_step = time_step;
  wt->win = win;

  BLI_addtail(&wm->timers, wt);

  return wt;
}

wmTimer *WM_event_timer_add_notifier(wmWindowManager *wm,
                                     wmWindow *win,
                                     uint type,
                                     double time_step)
{
  wmTimer *wt = static_cast<wmTimer *>(MEM_callocN(sizeof(wmTimer), "window timer"));
  BLI_assert(time_step >= 0.0f);

  wt->event_type = TIMERNOTIFIER;
  wt->time_last = PIL_check_seconds_timer();
  wt->time_next = wt->time_last + time_step;
  wt->time_start = wt->time_last;
  wt->time_step = time_step;
  wt->win = win;
  wt->customdata = POINTER_FROM_UINT(type);
  wt->flags |= WM_TIMER_NO_FREE_CUSTOM_DATA;

  BLI_addtail(&wm->timers, wt);

  return wt;
}

void wm_window_timers_delete_removed(wmWindowManager *wm)
{
  LISTBASE_FOREACH_MUTABLE (wmTimer *, wt, &wm->timers) {
    if ((wt->flags & WM_TIMER_TAGGED_FOR_REMOVAL) == 0) {
      continue;
    }

    /* Actual removal and freeing of the timer. */
    BLI_remlink(&wm->timers, wt);
    MEM_freeN(wt);
  }
}

void WM_event_timer_free_data(wmTimer *timer)
{
  if (timer->customdata != nullptr && (timer->flags & WM_TIMER_NO_FREE_CUSTOM_DATA) == 0) {
    MEM_freeN(timer->customdata);
    timer->customdata = nullptr;
  }
}

void WM_event_timers_free_all(wmWindowManager *wm)
{
  BLI_assert_msg(BLI_listbase_is_empty(&wm->windows),
                 "This should only be called when freeing the window-manager");
  while (wmTimer *timer = static_cast<wmTimer *>(BLI_pophead(&wm->timers))) {
    WM_event_timer_free_data(timer);
    MEM_freeN(timer);
  }
}

void WM_event_timer_remove(wmWindowManager *wm, wmWindow * /*win*/, wmTimer *timer)
{
  /* Extra security check. */
  if (BLI_findindex(&wm->timers, timer) == -1) {
    return;
  }

  timer->flags |= WM_TIMER_TAGGED_FOR_REMOVAL;

  /* Clear existing references to the timer. */
  if (wm->reports.reporttimer == timer) {
    wm->reports.reporttimer = nullptr;
  }
  /* There might be events in queue with this timer as customdata. */
  LISTBASE_FOREACH (wmWindow *, win, &wm->windows) {
    LISTBASE_FOREACH (wmEvent *, event, &win->event_queue) {
      if (event->customdata == timer) {
        event->customdata = nullptr;
        event->type = EVENT_NONE; /* Timer users customdata, don't want `nullptr == nullptr`. */
      }
    }
  }

  /* Immediately free `customdata` if requested, so that invalid usages of that data after
   * calling `WM_event_timer_remove` can be easily spotted (through ASAN errors e.g.). */
  WM_event_timer_free_data(timer);
}

void WM_event_timer_remove_notifier(wmWindowManager *wm, wmWindow *win, wmTimer *timer)
{
  timer->customdata = nullptr;
  WM_event_timer_remove(wm, win, timer);
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Clipboard Wrappers
 *
 * GHOST function wrappers that support a "fake" clipboard used when simulating events.
 * This is useful user actions can be simulated while the system is in use without the system's
 * clipboard getting overwritten.
 * \{ */

struct {
  char *buffers[2];
} *g_wm_clipboard_text_simulate = nullptr;

void wm_clipboard_free()
{
  if (g_wm_clipboard_text_simulate == nullptr) {
    return;
  }
  for (int i = 0; i < ARRAY_SIZE(g_wm_clipboard_text_simulate->buffers); i++) {
    char *buf = g_wm_clipboard_text_simulate->buffers[i];
    if (buf) {
      MEM_freeN(buf);
    }
  }
  MEM_freeN(g_wm_clipboard_text_simulate);
  g_wm_clipboard_text_simulate = nullptr;
}

static char *wm_clipboard_text_get_impl(bool selection)
{
  if (UNLIKELY(G.f & G_FLAG_EVENT_SIMULATE)) {
    if (g_wm_clipboard_text_simulate == nullptr) {
      return nullptr;
    }
    const char *buf_src = g_wm_clipboard_text_simulate->buffers[int(selection)];
    if (buf_src == nullptr) {
      return nullptr;
    }
    size_t size = strlen(buf_src) + 1;
    char *buf = static_cast<char *>(malloc(size));
    memcpy(buf, buf_src, size);
    return buf;
  }

  return GHOST_getClipboard(selection);
}

static void wm_clipboard_text_set_impl(const char *buf, bool selection)
{
  if (UNLIKELY(G.f & G_FLAG_EVENT_SIMULATE)) {
    if (g_wm_clipboard_text_simulate == nullptr) {
      g_wm_clipboard_text_simulate = static_cast<decltype(g_wm_clipboard_text_simulate)>(
          MEM_callocN(sizeof(*g_wm_clipboard_text_simulate), __func__));
    }
    char **buf_src_p = &(g_wm_clipboard_text_simulate->buffers[int(selection)]);
    MEM_SAFE_FREE(*buf_src_p);
    *buf_src_p = BLI_strdup(buf);
    return;
  }

  GHOST_putClipboard(buf, selection);
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Clipboard
 * \{ */

static char *wm_clipboard_text_get_ex(bool selection,
                                      int *r_len,
                                      const bool ensure_utf8,
                                      const bool firstline)
{
  if (G.background) {
    *r_len = 0;
    return nullptr;
  }

  char *buf = wm_clipboard_text_get_impl(selection);
  if (!buf) {
    *r_len = 0;
    return nullptr;
  }

  int buf_len = strlen(buf);

  if (ensure_utf8) {
    /* TODO(@ideasman42): It would be good if unexpected byte sequences could be interpreted
     * instead of stripped - so mixed in characters (typically Latin1) aren't ignored.
     * Check on how Python bytes this, see: #PyC_UnicodeFromBytesAndSize,
     * there are clever ways to handle this although they increase the size of the buffer. */
    buf_len -= BLI_str_utf8_invalid_strip(buf, buf_len);
  }

  /* always convert from \r\n to \n */
  char *newbuf = static_cast<char *>(MEM_mallocN(buf_len + 1, __func__));
  char *p2 = newbuf;

  if (firstline) {
    /* will return an over-alloc'ed value in the case there are newlines */
    for (char *p = buf; *p; p++) {
      if (!ELEM(*p, '\n', '\r')) {
        *(p2++) = *p;
      }
      else {
        break;
      }
    }
  }
  else {
    for (char *p = buf; *p; p++) {
      if (*p != '\r') {
        *(p2++) = *p;
      }
    }
  }

  *p2 = '\0';

  free(buf); /* ghost uses regular malloc */

  *r_len = (p2 - newbuf);

  return newbuf;
}

char *WM_clipboard_text_get(bool selection, bool ensure_utf8, int *r_len)
{
  return wm_clipboard_text_get_ex(selection, r_len, ensure_utf8, false);
}

char *WM_clipboard_text_get_firstline(bool selection, bool ensure_utf8, int *r_len)
{
  return wm_clipboard_text_get_ex(selection, r_len, ensure_utf8, true);
}

void WM_clipboard_text_set(const char *buf, bool selection)
{
  if (!G.background) {
#ifdef _WIN32
    /* do conversion from \n to \r\n on Windows */
    const char *p;
    char *p2, *newbuf;
    int newlen = 0;

    for (p = buf; *p; p++) {
      if (*p == '\n') {
        newlen += 2;
      }
      else {
        newlen++;
      }
    }

    newbuf = static_cast<char *>(MEM_callocN(newlen + 1, "WM_clipboard_text_set"));

    for (p = buf, p2 = newbuf; *p; p++, p2++) {
      if (*p == '\n') {
        *(p2++) = '\r';
        *p2 = '\n';
      }
      else {
        *p2 = *p;
      }
    }
    *p2 = '\0';

    wm_clipboard_text_set_impl(newbuf, selection);
    MEM_freeN(newbuf);
#else
    wm_clipboard_text_set_impl(buf, selection);
#endif
  }
}

bool WM_clipboard_image_available()
{
  if (G.background) {
    return false;
  }
  return bool(GHOST_hasClipboardImage());
}

ImBuf *WM_clipboard_image_get()
{
  if (G.background) {
    return nullptr;
  }

  int width, height;

  uint8_t *rgba = (uint8_t *)GHOST_getClipboardImage(&width, &height);
  if (!rgba) {
    return nullptr;
  }

  ImBuf *ibuf = IMB_allocFromBuffer(rgba, nullptr, width, height, 4);
  free(rgba);

  return ibuf;
}

bool WM_clipboard_image_set(ImBuf *ibuf)
{
  if (G.background) {
    return false;
  }

  bool free_byte_buffer = false;
  if (ibuf->byte_buffer.data == nullptr) {
    /* Add a byte buffer if it does not have one. */
    IMB_rect_from_float(ibuf);
    free_byte_buffer = true;
  }

  bool success = bool(GHOST_putClipboardImage((uint *)ibuf->byte_buffer.data, ibuf->x, ibuf->y));

  if (free_byte_buffer) {
    /* Remove the byte buffer if we added it. */
    imb_freerectImBuf(ibuf);
  }

  return success;
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Progress Bar
 * \{ */

void WM_progress_set(wmWindow *win, float progress)
{
  /* In background mode we may have windows, but not actual GHOST windows. */
  if (win->ghostwin) {
    GHOST_SetProgressBar(static_cast<GHOST_WindowHandle>(win->ghostwin), progress);
  }
}

void WM_progress_clear(wmWindow *win)
{
  if (win->ghostwin) {
    GHOST_EndProgressBar(static_cast<GHOST_WindowHandle>(win->ghostwin));
  }
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Window Position/Size (internal)
 * \{ */

void wm_window_get_position(wmWindow *win, int *r_pos_x, int *r_pos_y)
{
  *r_pos_x = win->posx;
  *r_pos_y = win->posy;
}

void wm_window_set_size(wmWindow *win, int width, int height)
{
  GHOST_SetClientSize(static_cast<GHOST_WindowHandle>(win->ghostwin), width, height);
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Window Depth (Raise/Lower)
 * \{ */

void wm_window_lower(wmWindow *win)
{
  GHOST_SetWindowOrder(static_cast<GHOST_WindowHandle>(win->ghostwin), GHOST_kWindowOrderBottom);
}

void wm_window_raise(wmWindow *win)
{
  /* Restore window if minimized */
  if (GHOST_GetWindowState(static_cast<GHOST_WindowHandle>(win->ghostwin)) ==
      GHOST_kWindowStateMinimized)
  {
    GHOST_SetWindowState(static_cast<GHOST_WindowHandle>(win->ghostwin), GHOST_kWindowStateNormal);
  }
  GHOST_SetWindowOrder(static_cast<GHOST_WindowHandle>(win->ghostwin), GHOST_kWindowOrderTop);
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Window Buffers
 * \{ */

void wm_window_swap_buffers(wmWindow *win)
{
  GHOST_SwapWindowBuffers(static_cast<GHOST_WindowHandle>(win->ghostwin));
}

void wm_window_set_swap_interval(wmWindow *win, int interval)
{
  GHOST_SetSwapInterval(static_cast<GHOST_WindowHandle>(win->ghostwin), interval);
}

bool wm_window_get_swap_interval(wmWindow *win, int *intervalOut)
{
  return GHOST_GetSwapInterval(static_cast<GHOST_WindowHandle>(win->ghostwin), intervalOut);
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Find Window Utility
 * \{ */

wmWindow *WM_window_find_under_cursor(wmWindow *win,
                                      const int event_xy[2],
                                      int r_event_xy_other[2])
{
  int temp_xy[2];
  copy_v2_v2_int(temp_xy, event_xy);
  wm_cursor_position_to_ghost_screen_coords(win, &temp_xy[0], &temp_xy[1]);

  GHOST_WindowHandle ghostwin = GHOST_GetWindowUnderCursor(g_system, temp_xy[0], temp_xy[1]);

  if (!ghostwin) {
    return nullptr;
  }

  wmWindow *win_other = static_cast<wmWindow *>(GHOST_GetWindowUserData(ghostwin));
  wm_cursor_position_from_ghost_screen_coords(win_other, &temp_xy[0], &temp_xy[1]);
  copy_v2_v2_int(r_event_xy_other, temp_xy);
  return win_other;
}

wmWindow *WM_window_find_by_area(wmWindowManager *wm, const ScrArea *area)
{
  LISTBASE_FOREACH (wmWindow *, win, &wm->windows) {
    bScreen *sc = WM_window_get_active_screen(win);
    if (BLI_findindex(&sc->areabase, area) != -1) {
      return win;
    }
  }
  return nullptr;
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Initial Window State API
 * \{ */

void WM_init_state_size_set(int stax, int stay, int sizx, int sizy)
{
  wm_init_state.start_x = stax; /* left hand pos */
  wm_init_state.start_y = stay; /* bottom pos */
  wm_init_state.size_x = sizx < 640 ? 640 : sizx;
  wm_init_state.size_y = sizy < 480 ? 480 : sizy;
  wm_init_state.override_flag |= WIN_OVERRIDE_GEOM;
}

void WM_init_state_fullscreen_set()
{
  wm_init_state.windowstate = GHOST_kWindowStateFullScreen;
  wm_init_state.override_flag |= WIN_OVERRIDE_WINSTATE;
}

void WM_init_state_normal_set()
{
  wm_init_state.windowstate = GHOST_kWindowStateNormal;
  wm_init_state.override_flag |= WIN_OVERRIDE_WINSTATE;
}

void WM_init_state_maximized_set()
{
  wm_init_state.windowstate = GHOST_kWindowStateMaximized;
  wm_init_state.override_flag |= WIN_OVERRIDE_WINSTATE;
}

void WM_init_window_focus_set(bool do_it)
{
  wm_init_state.window_focus = do_it;
}

void WM_init_native_pixels(bool do_it)
{
  wm_init_state.native_pixels = do_it;
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Cursor API
 * \{ */

void WM_init_input_devices()
{
  if (UNLIKELY(!g_system)) {
    return;
  }

  GHOST_SetMultitouchGestures(g_system, (U.uiflag & USER_NO_MULTITOUCH_GESTURES) == 0);

  switch (U.tablet_api) {
    case USER_TABLET_NATIVE:
      GHOST_SetTabletAPI(g_system, GHOST_kTabletWinPointer);
      break;
    case USER_TABLET_WINTAB:
      GHOST_SetTabletAPI(g_system, GHOST_kTabletWintab);
      break;
    case USER_TABLET_AUTOMATIC:
    default:
      GHOST_SetTabletAPI(g_system, GHOST_kTabletAutomatic);
      break;
  }
}

void WM_cursor_warp(wmWindow *win, int x, int y)
{
  /* This function requires access to the GHOST_SystemHandle (`g_system`). */

  if (!(win && win->ghostwin)) {
    return;
  }

  int oldx = x, oldy = y;

  wm_cursor_position_to_ghost_client_coords(win, &x, &y);
  GHOST_SetCursorPosition(g_system, static_cast<GHOST_WindowHandle>(win->ghostwin), x, y);

  win->eventstate->prev_xy[0] = oldx;
  win->eventstate->prev_xy[1] = oldy;

  win->eventstate->xy[0] = oldx;
  win->eventstate->xy[1] = oldy;
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Window Size (public)
 * \{ */

int WM_window_pixels_x(const wmWindow *win)
{
  float f = GHOST_GetNativePixelSize(static_cast<GHOST_WindowHandle>(win->ghostwin));

  return int(f * float(win->sizex));
}
int WM_window_pixels_y(const wmWindow *win)
{
  float f = GHOST_GetNativePixelSize(static_cast<GHOST_WindowHandle>(win->ghostwin));

  return int(f * float(win->sizey));
}

void WM_window_rect_calc(const wmWindow *win, rcti *r_rect)
{
  BLI_rcti_init(r_rect, 0, WM_window_pixels_x(win), 0, WM_window_pixels_y(win));
}
void WM_window_screen_rect_calc(const wmWindow *win, rcti *r_rect)
{
  rcti window_rect, screen_rect;

  WM_window_rect_calc(win, &window_rect);
  screen_rect = window_rect;

  /* Subtract global areas from screen rectangle. */
  LISTBASE_FOREACH (ScrArea *, global_area, &win->global_areas.areabase) {
    int height = ED_area_global_size_y(global_area) - 1;

    if (global_area->global->flag & GLOBAL_AREA_IS_HIDDEN) {
      continue;
    }

    switch (global_area->global->align) {
      case GLOBAL_AREA_ALIGN_TOP:
        screen_rect.ymax -= height;
        break;
      case GLOBAL_AREA_ALIGN_BOTTOM:
        screen_rect.ymin += height;
        break;
      default:
        BLI_assert_unreachable();
        break;
    }
  }

  BLI_assert(BLI_rcti_is_valid(&screen_rect));

  *r_rect = screen_rect;
}

bool WM_window_is_fullscreen(const wmWindow *win)
{
  return win->windowstate == GHOST_kWindowStateFullScreen;
}

bool WM_window_is_maximized(const wmWindow *win)
{
  return win->windowstate == GHOST_kWindowStateMaximized;
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Window Screen/Scene/WorkSpaceViewLayer API
 * \{ */

void WM_windows_scene_data_sync(const ListBase *win_lb, Scene *scene)
{
  LISTBASE_FOREACH (wmWindow *, win, win_lb) {
    if (WM_window_get_active_scene(win) == scene) {
      ED_workspace_scene_data_sync(win->workspace_hook, scene);
    }
  }
}

Scene *WM_windows_scene_get_from_screen(const wmWindowManager *wm, const bScreen *screen)
{
  LISTBASE_FOREACH (wmWindow *, win, &wm->windows) {
    if (WM_window_get_active_screen(win) == screen) {
      return WM_window_get_active_scene(win);
    }
  }

  return nullptr;
}

ViewLayer *WM_windows_view_layer_get_from_screen(const wmWindowManager *wm, const bScreen *screen)
{
  LISTBASE_FOREACH (wmWindow *, win, &wm->windows) {
    if (WM_window_get_active_screen(win) == screen) {
      return WM_window_get_active_view_layer(win);
    }
  }

  return nullptr;
}

WorkSpace *WM_windows_workspace_get_from_screen(const wmWindowManager *wm, const bScreen *screen)
{
  LISTBASE_FOREACH (wmWindow *, win, &wm->windows) {
    if (WM_window_get_active_screen(win) == screen) {
      return WM_window_get_active_workspace(win);
    }
  }
  return nullptr;
}

Scene *WM_window_get_active_scene(const wmWindow *win)
{
  return win->scene;
}

void WM_window_set_active_scene(Main *bmain, bContext *C, wmWindow *win, Scene *scene)
{
  wmWindowManager *wm = CTX_wm_manager(C);
  wmWindow *win_parent = (win->parent) ? win->parent : win;
  bool changed = false;

  /* Set scene in parent and its child windows. */
  if (win_parent->scene != scene) {
    ED_screen_scene_change(C, win_parent, scene, true);
    changed = true;
  }

  LISTBASE_FOREACH (wmWindow *, win_child, &wm->windows) {
    if (win_child->parent == win_parent && win_child->scene != scene) {
      ED_screen_scene_change(C, win_child, scene, true);
      changed = true;
    }
  }

  if (changed) {
    /* Update depsgraph and renderers for scene change. */
    ViewLayer *view_layer = WM_window_get_active_view_layer(win_parent);
    ED_scene_change_update(bmain, scene, view_layer);

    /* Complete redraw. */
    WM_event_add_notifier(C, NC_WINDOW, nullptr);
  }
}

ViewLayer *WM_window_get_active_view_layer(const wmWindow *win)
{
  Scene *scene = WM_window_get_active_scene(win);
  if (scene == nullptr) {
    return nullptr;
  }

  ViewLayer *view_layer = BKE_view_layer_find(scene, win->view_layer_name);
  if (view_layer) {
    return view_layer;
  }

  view_layer = BKE_view_layer_default_view(scene);
  if (view_layer) {
    WM_window_set_active_view_layer((wmWindow *)win, view_layer);
  }

  return view_layer;
}

void WM_window_set_active_view_layer(wmWindow *win, ViewLayer *view_layer)
{
  BLI_assert(BKE_view_layer_find(WM_window_get_active_scene(win), view_layer->name) != nullptr);
  Main *bmain = G_MAIN;

  wmWindowManager *wm = static_cast<wmWindowManager *>(bmain->wm.first);
  wmWindow *win_parent = (win->parent) ? win->parent : win;

  /* Set view layer in parent and child windows. */
  LISTBASE_FOREACH (wmWindow *, win_iter, &wm->windows) {
    if ((win_iter == win_parent) || (win_iter->parent == win_parent)) {
      STRNCPY(win_iter->view_layer_name, view_layer->name);
      bScreen *screen = BKE_workspace_active_screen_get(win_iter->workspace_hook);
      ED_render_view_layer_changed(bmain, screen);
    }
  }
}

void WM_window_ensure_active_view_layer(wmWindow *win)
{
  /* Update layer name is correct after scene changes, load without UI, etc. */
  Scene *scene = WM_window_get_active_scene(win);

  if (scene && BKE_view_layer_find(scene, win->view_layer_name) == nullptr) {
    ViewLayer *view_layer = BKE_view_layer_default_view(scene);
    STRNCPY(win->view_layer_name, view_layer->name);
  }
}

WorkSpace *WM_window_get_active_workspace(const wmWindow *win)
{
  return BKE_workspace_active_get(win->workspace_hook);
}

void WM_window_set_active_workspace(bContext *C, wmWindow *win, WorkSpace *workspace)
{
  wmWindowManager *wm = CTX_wm_manager(C);
  wmWindow *win_parent = (win->parent) ? win->parent : win;

  ED_workspace_change(workspace, C, wm, win);

  LISTBASE_FOREACH (wmWindow *, win_child, &wm->windows) {
    if (win_child->parent == win_parent) {
      bScreen *screen = WM_window_get_active_screen(win_child);
      /* Don't change temporary screens, they only serve a single purpose. */
      if (screen->temp) {
        continue;
      }
      ED_workspace_change(workspace, C, wm, win_child);
    }
  }
}

WorkSpaceLayout *WM_window_get_active_layout(const wmWindow *win)
{
  const WorkSpace *workspace = WM_window_get_active_workspace(win);
  return (LIKELY(workspace != nullptr) ? BKE_workspace_active_layout_get(win->workspace_hook) :
                                         nullptr);
}
void WM_window_set_active_layout(wmWindow *win, WorkSpace *workspace, WorkSpaceLayout *layout)
{
  BKE_workspace_active_layout_set(win->workspace_hook, win->winid, workspace, layout);
}

bScreen *WM_window_get_active_screen(const wmWindow *win)
{
  const WorkSpace *workspace = WM_window_get_active_workspace(win);
  /* May be nullptr in rare cases like closing Blender */
  return (LIKELY(workspace != nullptr) ? BKE_workspace_active_screen_get(win->workspace_hook) :
                                         nullptr);
}
void WM_window_set_active_screen(wmWindow *win, WorkSpace *workspace, bScreen *screen)
{
  BKE_workspace_active_screen_set(win->workspace_hook, win->winid, workspace, screen);
}

bool WM_window_is_temp_screen(const wmWindow *win)
{
  const bScreen *screen = WM_window_get_active_screen(win);
  return (screen && screen->temp != 0);
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Window IME API
 * \{ */

#ifdef WITH_INPUT_IME
/**
 * \note Keep in mind #wm_window_IME_begin is also used to reposition the IME window.
 */
void wm_window_IME_begin(wmWindow *win, int x, int y, int w, int h, bool complete)
{
  BLI_assert(win);
  if ((WM_capabilities_flag() & WM_CAPABILITY_INPUT_IME) == 0) {
    return;
  }

  /* Convert to native OS window coordinates. */
  float fac = GHOST_GetNativePixelSize(static_cast<GHOST_WindowHandle>(win->ghostwin));
  x /= fac;
  y /= fac;
  GHOST_BeginIME(
      static_cast<GHOST_WindowHandle>(win->ghostwin), x, win->sizey - y, w, h, complete);
}

void wm_window_IME_end(wmWindow *win)
{
  if ((WM_capabilities_flag() & WM_CAPABILITY_INPUT_IME) == 0) {
    return;
  }

  BLI_assert(win);
  /* NOTE(@ideasman42): on WAYLAND a call to "begin" must be closed by an "end" call.
   * Even if no IME events were generated (which assigned `ime_data`).
   * TODO: check if #GHOST_EndIME can run on WIN32 & APPLE without causing problems. */
#  if defined(WIN32) || defined(__APPLE__)
  BLI_assert(win->ime_data);
#  endif
  GHOST_EndIME(static_cast<GHOST_WindowHandle>(win->ghostwin));
  win->ime_data = nullptr;
  win->ime_data_is_composing = false;
}
#endif /* WITH_INPUT_IME */

/** \} */

/* -------------------------------------------------------------------- */
/** \name Direct GPU Context Management
 * \{ */

void *WM_system_gpu_context_create()
{
  /* On Windows there is a problem creating contexts that share resources (almost any object,
   * including legacy display lists, but also textures) with a context which is current in another
   * thread. This is a documented and behavior of both `::wglCreateContextAttribsARB()` and
   * `::wglShareLists()`.
   *
   * Other platforms might successfully share resources from context which is active somewhere
   * else, but to keep our code behave the same on all platform we expect contexts to only be
   * created from the main thread. */

  BLI_assert(BLI_thread_is_main());
  BLI_assert(GPU_framebuffer_active_get() == GPU_framebuffer_back_get());

  GHOST_GPUSettings gpuSettings = {0};
  const eGPUBackendType gpu_backend = GPU_backend_type_selection_get();
  gpuSettings.context_type = wm_ghost_drawing_context_type(gpu_backend);
  if (G.debug & G_DEBUG_GPU) {
    gpuSettings.flags |= GHOST_gpuDebugContext;
  }
  return GHOST_CreateGPUContext(g_system, gpuSettings);
}

void WM_system_gpu_context_dispose(void *context)
{
  BLI_assert(GPU_framebuffer_active_get() == GPU_framebuffer_back_get());
  GHOST_DisposeGPUContext(g_system, (GHOST_ContextHandle)context);
}

void WM_system_gpu_context_activate(void *context)
{
  BLI_assert(GPU_framebuffer_active_get() == GPU_framebuffer_back_get());
  GHOST_ActivateGPUContext((GHOST_ContextHandle)context);
}

void WM_system_gpu_context_release(void *context)
{
  BLI_assert(GPU_framebuffer_active_get() == GPU_framebuffer_back_get());
  GHOST_ReleaseGPUContext((GHOST_ContextHandle)context);
}

void WM_ghost_show_message_box(const char *title,
                               const char *message,
                               const char *help_label,
                               const char *continue_label,
                               const char *link,
                               GHOST_DialogOptions dialog_options)
{
  BLI_assert(g_system);
  GHOST_ShowMessageBox(g_system, title, message, help_label, continue_label, link, dialog_options);
}

/** \} */

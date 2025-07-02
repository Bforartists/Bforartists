/* SPDX-FileCopyrightText: 2005-2007 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup wm
 *
 * Cursor pixmap and cursor utility functions to change the cursor.
 */

#include <cstring>

#include "GHOST_C-api.h"

#include "BLI_utildefines.h"

#include "DNA_listBase.h"
#include "DNA_userdef_types.h"
#include "DNA_workspace_types.h"

#include "BKE_global.hh"
#include "BKE_main.hh"

#include "nanosvgrast.h"
#include "svg_cursors.h"

#include "WM_api.hh"
#include "WM_types.hh"
#include "wm_cursors.hh"
#include "wm_window.hh"

/* Blender custom cursor. */
struct BCursor {
  const char *svg_source;
  blender::float2 hotspot;
  bool can_invert;
};

/* We currently support multiple types of mouse cursors. Preferred
 * is to use one provided by the OS. The availability of these are
 * checked with GHOST_HasCursorShape(). These cursors can include
 * platform-specific custom cursors. For example, on MacOS we provide
 * vector PDF files and on Windows we have CUR files.
 *
 * If the OS cannot provide a built-in or custom platform cursor,
 * then we use our own internal custom cursors. These are defined in
 * SVG files, using a document size of 1600x1600 being the "normal"
 * size, cropped to the image size and without any padding.  The hotspot
 * for these are set during definition at the bottom of this file, and
 * are a float factor (0-1) from the top-left corner of the image (not
 * of the document size).
 */

static BCursor BlenderCursor[WM_CURSOR_NUM] = {{nullptr}};

/* Blender cursor to GHOST standard cursor conversion. */
static GHOST_TStandardCursor convert_to_ghost_standard_cursor(WMCursorType curs)
{
  switch (curs) {
    case WM_CURSOR_DEFAULT:
      return GHOST_kStandardCursorDefault;
    case WM_CURSOR_WAIT:
      return GHOST_kStandardCursorWait;
    case WM_CURSOR_EDIT:
    case WM_CURSOR_CROSS:
      return GHOST_kStandardCursorCrosshair;
    case WM_CURSOR_MOVE:
      return GHOST_kStandardCursorMove;
    case WM_CURSOR_X_MOVE:
      return GHOST_kStandardCursorLeftRight;
    case WM_CURSOR_Y_MOVE:
      return GHOST_kStandardCursorUpDown;
    case WM_CURSOR_COPY:
      return GHOST_kStandardCursorCopy;
    case WM_CURSOR_HAND:
      return GHOST_kStandardCursorHandOpen;
    case WM_CURSOR_HAND_CLOSED:
      return GHOST_kStandardCursorHandClosed;
    case WM_CURSOR_HAND_POINT:
      return GHOST_kStandardCursorHandPoint;
    case WM_CURSOR_H_SPLIT:
      return GHOST_kStandardCursorHorizontalSplit;
    case WM_CURSOR_V_SPLIT:
      return GHOST_kStandardCursorVerticalSplit;
    case WM_CURSOR_STOP:
      return GHOST_kStandardCursorStop;
    case WM_CURSOR_KNIFE:
      return GHOST_kStandardCursorKnife;
    case WM_CURSOR_NSEW_SCROLL:
      return GHOST_kStandardCursorNSEWScroll;
    case WM_CURSOR_NS_SCROLL:
      return GHOST_kStandardCursorNSScroll;
    case WM_CURSOR_EW_SCROLL:
      return GHOST_kStandardCursorEWScroll;
    case WM_CURSOR_EYEDROPPER:
      return GHOST_kStandardCursorEyedropper;
    case WM_CURSOR_N_ARROW:
      return GHOST_kStandardCursorUpArrow;
    case WM_CURSOR_S_ARROW:
      return GHOST_kStandardCursorDownArrow;
    case WM_CURSOR_PAINT:
      return GHOST_kStandardCursorCrosshairA;
    case WM_CURSOR_DOT:
      return GHOST_kStandardCursorCrosshairB;
    case WM_CURSOR_CROSSC:
      return GHOST_kStandardCursorCrosshairC;
    case WM_CURSOR_ERASER:
      return GHOST_kStandardCursorEraser;
    case WM_CURSOR_ZOOM_IN:
      return GHOST_kStandardCursorZoomIn;
    case WM_CURSOR_ZOOM_OUT:
      return GHOST_kStandardCursorZoomOut;
    case WM_CURSOR_TEXT_EDIT:
      return GHOST_kStandardCursorText;
    case WM_CURSOR_PAINT_BRUSH:
      return GHOST_kStandardCursorPencil;
    case WM_CURSOR_E_ARROW:
      return GHOST_kStandardCursorRightArrow;
    case WM_CURSOR_W_ARROW:
      return GHOST_kStandardCursorLeftArrow;
    case WM_CURSOR_LEFT_HANDLE:
      return GHOST_kStandardCursorLeftHandle;
    case WM_CURSOR_RIGHT_HANDLE:
      return GHOST_kStandardCursorRightHandle;
    case WM_CURSOR_BOTH_HANDLES:
      return GHOST_kStandardCursorBothHandles;
    case WM_CURSOR_BLADE:
      return GHOST_kStandardCursorBlade;
    default:
      return GHOST_kStandardCursorCustom;
  }
}

static float cursor_size()
{
  /* Scaling with UI scale can be useful for magnified captures. */
  const bool scale_cursor_with_ui_scale = false;

  if (scale_cursor_with_ui_scale) {
    return 21.0f * UI_SCALE_FAC;
  }

#if (OS_MAC)
  /* MacOS always scales up this type of cursor for high-dpi displays. */
  return 21.0f;
#endif

  return WM_cursor_preferred_logical_size() * (UI_SCALE_FAC / U.ui_scale);
}

static blender::Array<uint8_t> cursor_bitmap_from_svg(const char *svg,
                                                      float size,
                                                      int r_bitmap_size[2])
{
  /* Nano alters the source string. */
  std::string svg_source = svg;

  NSVGimage *image = nsvgParse(svg_source.data(), "px", 96.0f);
  if (image == nullptr) {
    return {};
  }
  if (image->width == 0 || image->height == 0) {
    nsvgDelete(image);
    return {};
  }
  NSVGrasterizer *rast = nsvgCreateRasterizer();
  if (rast == nullptr) {
    nsvgDelete(image);
    return {};
  }

  float scale = (size / 1600.0f);
  const size_t dest_size[2] = {
      std::min(size_t(ceil(image->width * scale)), size_t(size)),
      std::min(size_t(ceil(image->height * scale)), size_t(size)),
  };
  scale = float(dest_size[0]) / image->width;

  blender::Array<uint8_t> bitmap_rgba(dest_size[0] * dest_size[1] * 4);

  nsvgRasterize(rast,
                image,
                0.0f,
                0.0f,
                scale,
                bitmap_rgba.data(),
                dest_size[0],
                dest_size[1],
                dest_size[0] * 4);

  nsvgDeleteRasterizer(rast);
  nsvgDelete(image);

  r_bitmap_size[0] = dest_size[0];
  r_bitmap_size[1] = dest_size[1];

  return bitmap_rgba;
}

/**
 * Convert 32-bit RGBA bitmap (1-32 x 1-32) to 32x32 1bpp XBitMap bitmap and mask.
 */
static void cursor_rgba_to_xbm_32(const blender::Array<uint8_t> &rgba,
                                  const int bitmap_size[2],
                                  uint8_t *bitmap,
                                  uint8_t *mask)
{
  for (int y = 0; y < bitmap_size[1]; y++) {
    for (int x = 0; x < bitmap_size[0]; x++) {
      int i = (y * bitmap_size[0] * 4) + (x * 4);
      int j = (y * 4) + (x >> 3);
      int k = (x % 8);
      if (rgba[i + 3] > 128) {
        if (rgba[i] > 128) {
          bitmap[j] |= (1 << k);
        }
        mask[j] |= (1 << k);
      }
    }
  }
}

static bool window_set_custom_cursor(wmWindow *win, BCursor *cursor)
{
  /* Option to force use of 1bpp XBitMap cursors is needed for testing. */
  const bool use_only_1bpp_cursors = false;

  const bool use_rgba = !use_only_1bpp_cursors &&
                        (WM_capabilities_flag() & WM_CAPABILITY_RGBA_CURSORS);

  const int max_size = use_rgba ? 128 : 32;
  const float size = std::min(cursor_size(), float(max_size));

  int bitmap_size[2];
  blender::Array<uint8_t> bitmap_rgba = cursor_bitmap_from_svg(
      cursor->svg_source, size, bitmap_size);
  if (UNLIKELY(bitmap_rgba.is_empty())) {
    return false;
  }

  const int hot_spot[2] = {
      int(cursor->hotspot[0] * (bitmap_size[0] - 1)),
      int(cursor->hotspot[1] * (bitmap_size[1] - 1)),
  };

  GHOST_TSuccess success;
  if (use_rgba) {
    success = GHOST_SetCustomCursorShape(static_cast<GHOST_WindowHandle>(win->ghostwin),
                                         bitmap_rgba.data(),
                                         nullptr,
                                         bitmap_size,
                                         hot_spot,
                                         cursor->can_invert);
  }
  else {
    int bitmap_size_fixed[2] = {32, 32};

    uint8_t bitmap[4 * 32] = {0};
    uint8_t mask[4 * 32] = {0};
    cursor_rgba_to_xbm_32(bitmap_rgba, bitmap_size, bitmap, mask);
    success = GHOST_SetCustomCursorShape(static_cast<GHOST_WindowHandle>(win->ghostwin),
                                         bitmap,
                                         mask,
                                         bitmap_size_fixed,
                                         hot_spot,
                                         cursor->can_invert);
  }
  return (success == GHOST_kSuccess) ? true : false;
}

void WM_cursor_set(wmWindow *win, int curs)
{
  /* Option to not use any OS-supplied cursors is needed for testing. */
  const bool use_only_custom_cursors = false;

  if (win == nullptr || G.background) {
    return; /* Can't set custom cursor before Window init. */
  }

  if (curs == WM_CURSOR_DEFAULT && win->modalcursor) {
    curs = win->modalcursor;
  }

  if (curs == WM_CURSOR_NONE) {
    GHOST_SetCursorVisibility(static_cast<GHOST_WindowHandle>(win->ghostwin), false);
    return;
  }

  GHOST_SetCursorVisibility(static_cast<GHOST_WindowHandle>(win->ghostwin), true);

  if (win->cursor == curs) {
    return; /* Cursor is already set. */
  }

  win->cursor = curs;

  if (curs < 0 || curs >= WM_CURSOR_NUM) {
    BLI_assert_msg(0, "Invalid cursor number");
    return;
  }

  GHOST_TStandardCursor ghost_cursor = convert_to_ghost_standard_cursor(WMCursorType(curs));

  if (!use_only_custom_cursors && ghost_cursor != GHOST_kStandardCursorCustom &&
      GHOST_HasCursorShape(static_cast<GHOST_WindowHandle>(win->ghostwin), ghost_cursor))
  {
    /* Use native GHOST cursor when available. */
    GHOST_SetCursorShape(static_cast<GHOST_WindowHandle>(win->ghostwin), ghost_cursor);
  }
  else {
    BCursor *bcursor = &BlenderCursor[curs];
    if (!bcursor || !bcursor->svg_source || !window_set_custom_cursor(win, bcursor)) {
      /* Fall back to default cursor if no bitmap found. */
      GHOST_SetCursorShape(static_cast<GHOST_WindowHandle>(win->ghostwin),
                           GHOST_kStandardCursorDefault);
    }
  }
}

bool WM_cursor_set_from_tool(wmWindow *win, const ScrArea *area, const ARegion *region)
{
  if (region && !ELEM(region->regiontype, RGN_TYPE_WINDOW, RGN_TYPE_PREVIEW)) {
    return false;
  }

  bToolRef_Runtime *tref_rt = (area && area->runtime.tool) ? area->runtime.tool->runtime : nullptr;
  if (tref_rt && tref_rt->cursor != WM_CURSOR_DEFAULT) {
    if (win->modalcursor == 0) {
      WM_cursor_set(win, tref_rt->cursor);
      win->cursor = tref_rt->cursor;
      return true;
    }
  }
  return false;
}

void WM_cursor_modal_set(wmWindow *win, int val)
{
  if (win->lastcursor == 0) {
    win->lastcursor = win->cursor;
  }
  win->modalcursor = val;
  WM_cursor_set(win, val);
}

void WM_cursor_modal_restore(wmWindow *win)
{
  win->modalcursor = 0;
  if (win->lastcursor) {
    WM_cursor_set(win, win->lastcursor);
  }
  win->lastcursor = 0;
}

void WM_cursor_wait(bool val)
{
  if (!G.background) {
    wmWindowManager *wm = static_cast<wmWindowManager *>(G_MAIN->wm.first);
    wmWindow *win = static_cast<wmWindow *>(wm ? wm->windows.first : nullptr);

    for (; win; win = win->next) {
      if (val) {
        WM_cursor_modal_set(win, WM_CURSOR_WAIT);
      }
      else {
        WM_cursor_modal_restore(win);
      }
    }
  }
}

void WM_cursor_grab_enable(wmWindow *win,
                           const eWM_CursorWrapAxis wrap,
                           const rcti *wrap_region,
                           const bool hide)
{
  int _wrap_region_buf[4];
  int *wrap_region_screen = nullptr;

  /* Only grab cursor when not running debug.
   * It helps not to get a stuck WM when hitting a break-point. */
  GHOST_TGrabCursorMode mode = GHOST_kGrabNormal;
  GHOST_TAxisFlag mode_axis = GHOST_TAxisFlag(GHOST_kAxisX | GHOST_kAxisY);

  if (wrap_region) {
    wrap_region_screen = _wrap_region_buf;
    wrap_region_screen[0] = wrap_region->xmin;
    wrap_region_screen[1] = wrap_region->ymax;
    wrap_region_screen[2] = wrap_region->xmax;
    wrap_region_screen[3] = wrap_region->ymin;
    wm_cursor_position_to_ghost_screen_coords(win, &wrap_region_screen[0], &wrap_region_screen[1]);
    wm_cursor_position_to_ghost_screen_coords(win, &wrap_region_screen[2], &wrap_region_screen[3]);
  }

  if (hide) {
    mode = GHOST_kGrabHide;
  }
  else if (wrap != WM_CURSOR_WRAP_NONE) {
    mode = GHOST_kGrabWrap;

    if (wrap == WM_CURSOR_WRAP_X) {
      mode_axis = GHOST_kAxisX;
    }
    else if (wrap == WM_CURSOR_WRAP_Y) {
      mode_axis = GHOST_kAxisY;
    }
  }

  if ((G.debug & G_DEBUG) == 0) {
    if (win->ghostwin) {
      if (win->eventstate->tablet.is_motion_absolute == false) {
        GHOST_SetCursorGrab(static_cast<GHOST_WindowHandle>(win->ghostwin),
                            mode,
                            mode_axis,
                            wrap_region_screen,
                            nullptr);
      }

      win->grabcursor = mode;
    }
  }
}

void WM_cursor_grab_disable(wmWindow *win, const int mouse_ungrab_xy[2])
{
  if ((G.debug & G_DEBUG) == 0) {
    if (win && win->ghostwin) {
      if (mouse_ungrab_xy) {
        int mouse_xy[2] = {mouse_ungrab_xy[0], mouse_ungrab_xy[1]};
        wm_cursor_position_to_ghost_screen_coords(win, &mouse_xy[0], &mouse_xy[1]);
        GHOST_SetCursorGrab(static_cast<GHOST_WindowHandle>(win->ghostwin),
                            GHOST_kGrabDisable,
                            GHOST_kAxisNone,
                            nullptr,
                            mouse_xy);
      }
      else {
        GHOST_SetCursorGrab(static_cast<GHOST_WindowHandle>(win->ghostwin),
                            GHOST_kGrabDisable,
                            GHOST_kAxisNone,
                            nullptr,
                            nullptr);
      }

      win->grabcursor = GHOST_kGrabDisable;
    }
  }
}

static void wm_cursor_warp_relative(wmWindow *win, int x, int y)
{
  /* NOTE: don't use wmEvent coords because of continuous grab #36409. */
  int cx, cy;
  if (wm_cursor_position_get(win, &cx, &cy)) {
    WM_cursor_warp(win, cx + x, cy + y);
  }
}

bool wm_cursor_arrow_move(wmWindow *win, const wmEvent *event)
{
  /* TODO: give it a modal keymap? Hard coded for now. */

  if (win && event->val == KM_PRESS) {
    /* Must move at least this much to avoid rounding in WM_cursor_warp. */
    float fac = GHOST_GetNativePixelSize(static_cast<GHOST_WindowHandle>(win->ghostwin));

    if (event->type == EVT_UPARROWKEY) {
      wm_cursor_warp_relative(win, 0, fac);
      return true;
    }
    if (event->type == EVT_DOWNARROWKEY) {
      wm_cursor_warp_relative(win, 0, -fac);
      return true;
    }
    if (event->type == EVT_LEFTARROWKEY) {
      wm_cursor_warp_relative(win, -fac, 0);
      return true;
    }
    if (event->type == EVT_RIGHTARROWKEY) {
      wm_cursor_warp_relative(win, fac, 0);
      return true;
    }
  }
  return false;
}

static bool wm_cursor_time_large(wmWindow *win, int nr)
{
  /* 10 16x16 digits. */
  const uchar number_bitmaps[][32] = {
      {0x00, 0x00, 0xf0, 0x0f, 0xf8, 0x1f, 0x1c, 0x38, 0x0c, 0x30, 0x0c,
       0x30, 0x0c, 0x30, 0x0c, 0x30, 0x0c, 0x30, 0x0c, 0x30, 0x0c, 0x30,
       0x0c, 0x30, 0x1c, 0x38, 0xf8, 0x1f, 0xf0, 0x0f, 0x00, 0x00},
      {0x00, 0x00, 0x80, 0x01, 0xc0, 0x01, 0xf0, 0x01, 0xbc, 0x01, 0x8c,
       0x01, 0x80, 0x01, 0x80, 0x01, 0x80, 0x01, 0x80, 0x01, 0x80, 0x01,
       0x80, 0x01, 0x80, 0x01, 0xfc, 0x3f, 0xfc, 0x3f, 0x00, 0x00},
      {0x00, 0x00, 0xf0, 0x1f, 0xf8, 0x3f, 0x1c, 0x30, 0x0c, 0x30, 0x00,
       0x30, 0x00, 0x30, 0xe0, 0x3f, 0xf0, 0x1f, 0x38, 0x00, 0x1c, 0x00,
       0x0c, 0x00, 0x0c, 0x00, 0xfc, 0x3f, 0xfc, 0x3f, 0x00, 0x00},
      {0x00, 0x00, 0xf0, 0x0f, 0xf8, 0x1f, 0x1c, 0x38, 0x00, 0x30, 0x00,
       0x30, 0x00, 0x38, 0xf0, 0x1f, 0xf0, 0x1f, 0x00, 0x38, 0x00, 0x30,
       0x00, 0x30, 0x1c, 0x38, 0xf8, 0x1f, 0xf0, 0x0f, 0x00, 0x00},
      {0x00, 0x00, 0x00, 0x0f, 0x80, 0x0f, 0xc0, 0x0d, 0xe0, 0x0c, 0x70,
       0x0c, 0x38, 0x0c, 0x1c, 0x0c, 0x0c, 0x0c, 0x0c, 0x0c, 0x0c, 0x0c,
       0xfc, 0x3f, 0xfc, 0x3f, 0x00, 0x0c, 0x00, 0x0c, 0x00, 0x00},
      {0x00, 0x00, 0xfc, 0x3f, 0xfc, 0x3f, 0x0c, 0x00, 0x0c, 0x00, 0x0c,
       0x00, 0xfc, 0x0f, 0xfc, 0x1f, 0x00, 0x38, 0x00, 0x30, 0x00, 0x30,
       0x00, 0x30, 0x0c, 0x38, 0xfc, 0x1f, 0xf8, 0x0f, 0x00, 0x00},
      {0x00, 0x00, 0xc0, 0x3f, 0xe0, 0x3f, 0x70, 0x00, 0x38, 0x00, 0x1c,
       0x00, 0xfc, 0x0f, 0xfc, 0x1f, 0x0c, 0x38, 0x0c, 0x30, 0x0c, 0x30,
       0x0c, 0x30, 0x1c, 0x38, 0xf8, 0x1f, 0xf0, 0x0f, 0x00, 0x00},
      {0x00, 0x00, 0xfc, 0x3f, 0xfc, 0x3f, 0x0c, 0x30, 0x0c, 0x38, 0x00,
       0x18, 0x00, 0x1c, 0x00, 0x0c, 0x00, 0x0e, 0x00, 0x06, 0x00, 0x07,
       0x00, 0x03, 0x80, 0x03, 0x80, 0x01, 0x80, 0x01, 0x00, 0x00},
      {0x00, 0x00, 0xf0, 0x0f, 0xf8, 0x1f, 0x1c, 0x38, 0x0c, 0x30, 0x0c,
       0x30, 0x1c, 0x38, 0xf8, 0x1f, 0xf8, 0x1f, 0x1c, 0x38, 0x0c, 0x30,
       0x0c, 0x30, 0x1c, 0x38, 0xf8, 0x1f, 0xf0, 0x0f, 0x00, 0x00},
      {0x00, 0x00, 0xf0, 0x0f, 0xf8, 0x1f, 0x1c, 0x38, 0x0c, 0x30, 0x0c,
       0x30, 0x0c, 0x30, 0x1c, 0x30, 0xf8, 0x3f, 0xf0, 0x3f, 0x00, 0x38,
       0x00, 0x1c, 0x00, 0x0e, 0xfc, 0x07, 0xfc, 0x03, 0x00, 0x00},
  };
  uint8_t mask[32][4] = {{0}};
  uint8_t bitmap[32][4] = {{0}};

  /* Print number bottom right justified. */
  for (int idx = 3; nr && idx >= 0; idx--) {
    const uchar *digit = number_bitmaps[nr % 10];
    int x = idx % 2;
    int y = idx / 2;

    for (int i = 0; i < 16; i++) {
      bitmap[i + y * 16][x * 2] = digit[i * 2];
      bitmap[i + y * 16][(x * 2) + 1] = digit[(i * 2) + 1];
    }
    for (int i = 0; i < 16; i++) {
      mask[i + y * 16][x * 2] = 0xFF;
      mask[i + y * 16][(x * 2) + 1] = 0xFF;
    }

    nr /= 10;
  }

  const int size[2] = {32, 32};
  const int hot_spot[2] = {15, 15};
  return GHOST_SetCustomCursorShape(static_cast<GHOST_WindowHandle>(win->ghostwin),
                                    bitmap[0],
                                    mask[0],
                                    size,
                                    hot_spot,
                                    false) == GHOST_kSuccess;
}

static void wm_cursor_time_small(wmWindow *win, int nr)
{
  /* 10 8x8 digits. */
  const char number_bitmaps[10][8] = {
      {0, 56, 68, 68, 68, 68, 68, 56},
      {0, 24, 16, 16, 16, 16, 16, 56},
      {0, 60, 66, 32, 16, 8, 4, 126},
      {0, 124, 32, 16, 56, 64, 66, 60},
      {0, 32, 48, 40, 36, 126, 32, 32},
      {0, 124, 4, 60, 64, 64, 68, 56},
      {0, 56, 4, 4, 60, 68, 68, 56},
      {0, 124, 64, 32, 16, 8, 8, 8},
      {0, 60, 66, 66, 60, 66, 66, 60},
      {0, 56, 68, 68, 120, 64, 68, 56},
  };
  uint8_t mask[16][2] = {{0}};
  uint8_t bitmap[16][2] = {{0}};

  /* Print number bottom right justified. */
  for (int idx = 3; nr && idx >= 0; idx--) {
    const char *digit = number_bitmaps[nr % 10];
    int x = idx % 2;
    int y = idx / 2;

    for (int i = 0; i < 8; i++) {
      bitmap[i + y * 8][x] = digit[i];
    }
    for (int i = 0; i < 8; i++) {
      mask[i + y * 8][x] = 0xFF;
    }
    nr /= 10;
  }

  const int size[2] = {16, 16};
  const int hot_spot[2] = {7, 7};
  GHOST_SetCustomCursorShape(static_cast<GHOST_WindowHandle>(win->ghostwin),
                             (uint8_t *)bitmap,
                             (uint8_t *)mask,
                             size,
                             hot_spot,
                             false);
}

void WM_cursor_time(wmWindow *win, int nr)
{
  if (win->lastcursor == 0) {
    win->lastcursor = win->cursor;
  }

  /* Use `U.ui_scale` instead of `UI_SCALE_FAC` here to ignore HiDPI/Retina scaling. */
  if (U.ui_scale < 1.45f || !wm_cursor_time_large(win, nr)) {
    wm_cursor_time_small(win, nr);
  }

  /* Unset current cursor value so it's properly reset to wmWindow.lastcursor. */
  win->cursor = 0;
}

static void wm_add_cursor(WMCursorType cursor,
                          const char *svg_source,
                          const blender::float2 &hotspot,
                          bool can_invert = true)
{
  BlenderCursor[cursor].svg_source = svg_source;
  BlenderCursor[cursor].hotspot = hotspot;
  BlenderCursor[cursor].can_invert = can_invert;
}

void wm_init_cursor_data()
{
  wm_add_cursor(WM_CURSOR_DEFAULT, datatoc_cursor_pointer_svg, {0.0f, 0.0f});
  wm_add_cursor(WM_CURSOR_NW_ARROW, datatoc_cursor_pointer_svg, {0.0f, 0.0f});
  wm_add_cursor(WM_CURSOR_COPY, datatoc_cursor_pointer_svg, {0.0f, 0.0f});
  wm_add_cursor(WM_CURSOR_MOVE, datatoc_cursor_pointer_svg, {0.0f, 0.0f});
  wm_add_cursor(WM_CURSOR_TEXT_EDIT, datatoc_cursor_text_edit_svg, {0.5f, 0.5f});
  wm_add_cursor(WM_CURSOR_WAIT, datatoc_cursor_wait_svg, {0.5f, 0.5f});
  wm_add_cursor(WM_CURSOR_STOP, datatoc_cursor_stop_svg, {0.5f, 0.5f});
  wm_add_cursor(WM_CURSOR_EDIT, datatoc_cursor_crosshair_svg, {0.5f, 0.5f});
  wm_add_cursor(WM_CURSOR_HAND, datatoc_cursor_hand_svg, {0.5f, 0.5f});
  wm_add_cursor(WM_CURSOR_HAND_CLOSED, datatoc_cursor_hand_closed_svg, {0.5f, 0.5f});
  wm_add_cursor(WM_CURSOR_HAND_POINT, datatoc_cursor_hand_point_svg, {0.5f, 0.5f});
  wm_add_cursor(WM_CURSOR_CROSS, datatoc_cursor_crosshair_svg, {0.5f, 0.5f});
  wm_add_cursor(WM_CURSOR_PAINT, datatoc_cursor_paint_svg, {0.5f, 0.5f});
  wm_add_cursor(WM_CURSOR_DOT, datatoc_cursor_dot_svg, {0.5f, 0.5f});
  wm_add_cursor(WM_CURSOR_CROSSC, datatoc_cursor_crossc_svg, {0.5f, 0.5f});
  wm_add_cursor(WM_CURSOR_KNIFE, datatoc_cursor_knife_svg, {0.0f, 1.0f});
  wm_add_cursor(WM_CURSOR_BLADE, datatoc_cursor_blade_svg, {0.0f, 0.375f});
  wm_add_cursor(WM_CURSOR_VERTEX_LOOP, datatoc_cursor_vertex_loop_svg, {0.0f, 0.0f});
  wm_add_cursor(WM_CURSOR_PAINT_BRUSH, datatoc_cursor_pencil_svg, {0.0f, 1.0f});
  wm_add_cursor(WM_CURSOR_ERASER, datatoc_cursor_eraser_svg, {0.0f, 1.0f});
  wm_add_cursor(WM_CURSOR_EYEDROPPER, datatoc_cursor_eyedropper_svg, {0.0f, 1.0f});
  wm_add_cursor(WM_CURSOR_SWAP_AREA, datatoc_cursor_swap_area_svg, {0.5f, 0.5f});
  wm_add_cursor(WM_CURSOR_X_MOVE, datatoc_cursor_x_move_svg, {0.5f, 0.5f});
  wm_add_cursor(WM_CURSOR_EW_ARROW, datatoc_cursor_x_move_svg, {0.5f, 0.5f});
  wm_add_cursor(WM_CURSOR_Y_MOVE, datatoc_cursor_y_move_svg, {0.5f, 0.5f});
  wm_add_cursor(WM_CURSOR_NS_ARROW, datatoc_cursor_y_move_svg, {0.5f, 0.5f});
  wm_add_cursor(WM_CURSOR_H_SPLIT, datatoc_cursor_h_split_svg, {0.5f, 0.5f});
  wm_add_cursor(WM_CURSOR_V_SPLIT, datatoc_cursor_v_split_svg, {0.5f, 0.5f});
  wm_add_cursor(WM_CURSOR_N_ARROW, datatoc_cursor_n_arrow_svg, {0.5f, 0.5f});
  wm_add_cursor(WM_CURSOR_S_ARROW, datatoc_cursor_s_arrow_svg, {0.5f, 0.5f});
  wm_add_cursor(WM_CURSOR_E_ARROW, datatoc_cursor_e_arrow_svg, {0.5f, 0.5f});
  wm_add_cursor(WM_CURSOR_W_ARROW, datatoc_cursor_w_arrow_svg, {0.5f, 0.5f});
  wm_add_cursor(WM_CURSOR_NSEW_SCROLL, datatoc_cursor_nsew_scroll_svg, {0.5f, 0.5f});
  wm_add_cursor(WM_CURSOR_EW_SCROLL, datatoc_cursor_ew_scroll_svg, {0.5f, 0.5f});
  wm_add_cursor(WM_CURSOR_NS_SCROLL, datatoc_cursor_ns_scroll_svg, {0.5f, 0.5f});
  wm_add_cursor(WM_CURSOR_ZOOM_IN, datatoc_cursor_zoom_in_svg, {0.32f, 0.32f});
  wm_add_cursor(WM_CURSOR_ZOOM_OUT, datatoc_cursor_zoom_out_svg, {0.32f, 0.32f});
  wm_add_cursor(WM_CURSOR_MUTE, datatoc_cursor_mute_svg, {0.59f, 0.59f});
  wm_add_cursor(WM_CURSOR_PICK_AREA, datatoc_cursor_pick_area_svg, {0.5f, 0.5f});
  wm_add_cursor(WM_CURSOR_BOTH_HANDLES, datatoc_cursor_both_handles_svg, {0.5f, 0.5f});
  wm_add_cursor(WM_CURSOR_RIGHT_HANDLE, datatoc_cursor_right_handle_svg, {0.5f, 0.5f});
  wm_add_cursor(WM_CURSOR_LEFT_HANDLE, datatoc_cursor_left_handle_svg, {0.5f, 0.5f});
}

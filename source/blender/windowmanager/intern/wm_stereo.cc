/* SPDX-FileCopyrightText: 2015 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup wm
 */

#include <cstdlib>
#include <cstring>

#include "RNA_access.hh"
#include "RNA_prototypes.hh"

#include "MEM_guardedalloc.h"

#include "BLI_utildefines.h"

#include "BKE_context.hh"
#include "BKE_global.hh"
#include "BKE_report.hh"

#include "BLT_translation.hh"

#include "GHOST_C-api.h"

#include "ED_screen.hh"

#include "GPU_capabilities.hh"
#include "GPU_immediate.hh"
#include "GPU_viewport.hh"

#include "WM_api.hh"
#include "WM_types.hh"
#include "wm.hh"
#include "wm_window.hh"

#include "UI_interface_layout.hh"
#include "UI_resources.hh"

void wm_stereo3d_draw_sidebyside(wmWindow *win, int view)
{
  bool cross_eyed = (win->stereo3d_format->flag & S3D_SIDEBYSIDE_CROSSEYED) != 0;

  GPUVertFormat *format = immVertexFormat();
  uint texcoord = GPU_vertformat_attr_add(
      format, "texCoord", blender::gpu::VertAttrType::SFLOAT_32_32);
  uint pos = GPU_vertformat_attr_add(format, "pos", blender::gpu::VertAttrType::SFLOAT_32_32);

  immBindBuiltinProgram(GPU_SHADER_3D_IMAGE);

  const blender::int2 win_size = WM_window_native_pixel_size(win);

  int soffx = win_size[0] / 2;
  if (view == STEREO_LEFT_ID) {
    if (!cross_eyed) {
      soffx = 0;
    }
  }
  else { /* #RIGHT_LEFT_ID. */
    if (cross_eyed) {
      soffx = 0;
    }
  }

  /* `wmOrtho` for the screen has this same offset. */
  const float halfx = GLA_PIXEL_OFS / win_size[0];
  const float halfy = GLA_PIXEL_OFS / win_size[1];

  /* Texture is already bound to GL_TEXTURE0 unit. */

  immBegin(GPU_PRIM_TRI_FAN, 4);

  immAttr2f(texcoord, halfx, halfy);
  immVertex2f(pos, soffx, 0.0f);

  immAttr2f(texcoord, 1.0f + halfx, halfy);
  immVertex2f(pos, soffx + (win_size[0] * 0.5f), 0.0f);

  immAttr2f(texcoord, 1.0f + halfx, 1.0f + halfy);
  immVertex2f(pos, soffx + (win_size[0] * 0.5f), win_size[1]);

  immAttr2f(texcoord, halfx, 1.0f + halfy);
  immVertex2f(pos, soffx, win_size[1]);

  immEnd();

  immUnbindProgram();
}

void wm_stereo3d_draw_topbottom(wmWindow *win, int view)
{
  GPUVertFormat *format = immVertexFormat();
  uint texcoord = GPU_vertformat_attr_add(
      format, "texCoord", blender::gpu::VertAttrType::SFLOAT_32_32);
  uint pos = GPU_vertformat_attr_add(format, "pos", blender::gpu::VertAttrType::SFLOAT_32_32);

  immBindBuiltinProgram(GPU_SHADER_3D_IMAGE);

  const blender::int2 win_size = WM_window_native_pixel_size(win);

  int soffy;
  if (view == STEREO_LEFT_ID) {
    soffy = win_size[1] * 0.5f;
  }
  else { /* #STEREO_RIGHT_ID. */
    soffy = 0;
  }

  /* `wmOrtho` for the screen has this same offset. */
  const float halfx = GLA_PIXEL_OFS / win_size[0];
  const float halfy = GLA_PIXEL_OFS / win_size[1];

  /* Texture is already bound to GL_TEXTURE0 unit. */

  immBegin(GPU_PRIM_TRI_FAN, 4);

  immAttr2f(texcoord, halfx, halfy);
  immVertex2f(pos, 0.0f, soffy);

  immAttr2f(texcoord, 1.0f + halfx, halfy);
  immVertex2f(pos, win_size[0], soffy);

  immAttr2f(texcoord, 1.0f + halfx, 1.0f + halfy);
  immVertex2f(pos, win_size[0], soffy + (win_size[1] * 0.5f));

  immAttr2f(texcoord, halfx, 1.0f + halfy);
  immVertex2f(pos, 0.0f, soffy + (win_size[1] * 0.5f));

  immEnd();

  immUnbindProgram();
}

static bool wm_stereo3d_is_fullscreen_required(eStereoDisplayMode stereo_display)
{
  return ELEM(stereo_display, S3D_DISPLAY_SIDEBYSIDE, S3D_DISPLAY_TOPBOTTOM);
}

bool WM_stereo3d_enabled(wmWindow *win, bool skip_stereo3d_check)
{
  const bScreen *screen = WM_window_get_active_screen(win);
  const Scene *scene = WM_window_get_active_scene(win);

  /* Some 3d methods change the window arrangement, thus they shouldn't
   * toggle on/off just because there is no 3d elements being drawn. */
  if (wm_stereo3d_is_fullscreen_required(eStereoDisplayMode(win->stereo3d_format->display_mode))) {
    return GHOST_GetWindowState(static_cast<GHOST_WindowHandle>(win->ghostwin)) ==
           GHOST_kWindowStateFullScreen;
  }

  if ((skip_stereo3d_check == false) && (ED_screen_stereo3d_required(screen, scene) == false)) {
    return false;
  }

  /* Some 3d methods change the window arrangement, thus they shouldn't
   * toggle on/off just because there is no 3d elements being drawn. */
  if (wm_stereo3d_is_fullscreen_required(eStereoDisplayMode(win->stereo3d_format->display_mode))) {
    return GHOST_GetWindowState(static_cast<GHOST_WindowHandle>(win->ghostwin)) ==
           GHOST_kWindowStateFullScreen;
  }

  return true;
}

void wm_stereo3d_mouse_offset_apply(wmWindow *win, int r_mouse_xy[2])
{
  if (!WM_stereo3d_enabled(win, false)) {
    return;
  }

  if (win->stereo3d_format->display_mode == S3D_DISPLAY_SIDEBYSIDE) {
    const int half_x = WM_window_native_pixel_x(win) / 2;
    /* Right half of the screen. */
    if (r_mouse_xy[0] > half_x) {
      r_mouse_xy[0] -= half_x;
    }
    r_mouse_xy[0] *= 2;
  }
  else if (win->stereo3d_format->display_mode == S3D_DISPLAY_TOPBOTTOM) {
    const int half_y = WM_window_native_pixel_y(win) / 2;
    /* Upper half of the screen. */
    if (r_mouse_xy[1] > half_y) {
      r_mouse_xy[1] -= half_y;
    }
    r_mouse_xy[1] *= 2;
  }
}

/************************** Stereo 3D operator **********************************/
struct Stereo3dData {
  Stereo3dFormat stereo3d_format;
};

static bool wm_stereo3d_set_properties(bContext * /*C*/, wmOperator *op)
{
  Stereo3dData *s3dd = static_cast<Stereo3dData *>(op->customdata);
  Stereo3dFormat *s3d = &s3dd->stereo3d_format;
  PropertyRNA *prop;
  bool is_set = false;

  prop = RNA_struct_find_property(op->ptr, "display_mode");
  if (RNA_property_is_set(op->ptr, prop)) {
    s3d->display_mode = RNA_property_enum_get(op->ptr, prop);
    is_set = true;
  }

  prop = RNA_struct_find_property(op->ptr, "anaglyph_type");
  if (RNA_property_is_set(op->ptr, prop)) {
    s3d->anaglyph_type = RNA_property_enum_get(op->ptr, prop);
    is_set = true;
  }

  prop = RNA_struct_find_property(op->ptr, "interlace_type");
  if (RNA_property_is_set(op->ptr, prop)) {
    s3d->interlace_type = RNA_property_enum_get(op->ptr, prop);
    is_set = true;
  }

  prop = RNA_struct_find_property(op->ptr, "use_interlace_swap");
  if (RNA_property_is_set(op->ptr, prop)) {
    if (RNA_property_boolean_get(op->ptr, prop)) {
      s3d->flag |= S3D_INTERLACE_SWAP;
    }
    else {
      s3d->flag &= ~S3D_INTERLACE_SWAP;
    }
    is_set = true;
  }

  prop = RNA_struct_find_property(op->ptr, "use_sidebyside_crosseyed");
  if (RNA_property_is_set(op->ptr, prop)) {
    if (RNA_property_boolean_get(op->ptr, prop)) {
      s3d->flag |= S3D_SIDEBYSIDE_CROSSEYED;
    }
    else {
      s3d->flag &= ~S3D_SIDEBYSIDE_CROSSEYED;
    }
    is_set = true;
  }

  return is_set;
}

static void wm_stereo3d_set_init(bContext *C, wmOperator *op)
{
  wmWindow *win = CTX_wm_window(C);

  Stereo3dData *s3dd = MEM_callocN<Stereo3dData>(__func__);
  op->customdata = s3dd;

  /* Store the original win stereo 3d settings in case of cancel. */
  s3dd->stereo3d_format = *win->stereo3d_format;
}

wmOperatorStatus wm_stereo3d_set_exec(bContext *C, wmOperator *op)
{
  wmWindowManager *wm = CTX_wm_manager(C);
  wmWindow *win_src = CTX_wm_window(C);
  wmWindow *win_dst = nullptr;
  const bool is_fullscreen = WM_window_is_fullscreen(win_src);
  char prev_display_mode = win_src->stereo3d_format->display_mode;
  bool ok = true;

  if (G.background) {
    return OPERATOR_CANCELLED;
  }

  if (op->customdata == nullptr) {
    /* No invoke means we need to set the operator properties here. */
    wm_stereo3d_set_init(C, op);
    wm_stereo3d_set_properties(C, op);
  }

  Stereo3dData *s3dd = static_cast<Stereo3dData *>(op->customdata);
  *win_src->stereo3d_format = s3dd->stereo3d_format;

  if (prev_display_mode == S3D_DISPLAY_PAGEFLIP &&
      prev_display_mode != win_src->stereo3d_format->display_mode)
  {
    /* In case the hardware supports page-flip but not the display. */
    if ((win_dst = wm_window_copy_test(C, win_src, false, false))) {
      /* Pass. */
    }
    else {
      BKE_report(
          op->reports,
          RPT_ERROR,
          "Failed to create a window without quad-buffer support, you may experience flickering");
      ok = false;
    }
  }
  else if (win_src->stereo3d_format->display_mode == S3D_DISPLAY_PAGEFLIP) {
    const bScreen *screen = WM_window_get_active_screen(win_src);

    /* #ED_workspace_layout_duplicate() can't handle other cases yet #44688 */
    if (screen->state != SCREENNORMAL) {
      BKE_report(
          op->reports, RPT_ERROR, "Failed to switch to Time Sequential mode when in fullscreen");
      ok = false;
    }
    /* Page-flip requires a new window to be created with the proper OS flags. */
    else if ((win_dst = wm_window_copy_test(C, win_src, false, false))) {
      if (GPU_stereo_quadbuffer_support()) {
        BKE_report(op->reports, RPT_INFO, "Quad-buffer window successfully created");
      }
      else {
        wm_window_close(C, wm, win_dst);
        win_dst = nullptr;
        BKE_report(op->reports, RPT_ERROR, "Quad-buffer not supported by the system");
        ok = false;
      }
    }
    else {
      BKE_report(op->reports,
                 RPT_ERROR,
                 "Failed to create a window compatible with the time sequential display method");
      ok = false;
    }
  }

  if (wm_stereo3d_is_fullscreen_required(eStereoDisplayMode(s3dd->stereo3d_format.display_mode))) {
    if (!is_fullscreen) {
      BKE_report(op->reports, RPT_INFO, "Stereo 3D Mode requires the window to be fullscreen");
    }
  }

  MEM_freeN(s3dd);
  op->customdata = nullptr;

  if (ok) {
    if (win_dst) {
      wm_window_close(C, wm, win_src);
    }

    WM_event_add_notifier(C, NC_WINDOW, nullptr);
    return OPERATOR_FINISHED;
  }

  /* Without this, the popup won't be freed properly, see #44688. */
  CTX_wm_window_set(C, win_src);
  win_src->stereo3d_format->display_mode = prev_display_mode;
  return OPERATOR_CANCELLED;
}

wmOperatorStatus wm_stereo3d_set_invoke(bContext *C, wmOperator *op, const wmEvent * /*event*/)
{
  wm_stereo3d_set_init(C, op);

  if (wm_stereo3d_set_properties(C, op)) {
    return wm_stereo3d_set_exec(C, op);
  }
  return WM_operator_props_dialog_popup(C, op, 300, IFACE_("Set Stereo 3D"), IFACE_("Set"));
}

void wm_stereo3d_set_draw(bContext * /*C*/, wmOperator *op)
{
  Stereo3dData *s3dd = static_cast<Stereo3dData *>(op->customdata);
  uiLayout *layout = op->layout;
  uiLayout *col;

  PointerRNA stereo3d_format_ptr = RNA_pointer_create_discrete(
      nullptr, &RNA_Stereo3dDisplay, &s3dd->stereo3d_format);

  layout->use_property_split_set(true);
  layout->use_property_decorate_set(false);

  col = &layout->column(false);
  col->prop(&stereo3d_format_ptr, "display_mode", UI_ITEM_NONE, std::nullopt, ICON_NONE);

  switch (s3dd->stereo3d_format.display_mode) {
    case S3D_DISPLAY_ANAGLYPH: {
      col->prop(&stereo3d_format_ptr, "anaglyph_type", UI_ITEM_NONE, std::nullopt, ICON_NONE);
      break;
    }
    case S3D_DISPLAY_INTERLACE: {
      col->prop(&stereo3d_format_ptr, "interlace_type", UI_ITEM_NONE, std::nullopt, ICON_NONE);
      col->prop(&stereo3d_format_ptr, "use_interlace_swap", UI_ITEM_NONE, std::nullopt, ICON_NONE);
      break;
    }
    case S3D_DISPLAY_SIDEBYSIDE: {
      col->prop(
          &stereo3d_format_ptr, "use_sidebyside_crosseyed", UI_ITEM_NONE, std::nullopt, ICON_NONE);
      /* Fall-through. */
    }
    case S3D_DISPLAY_PAGEFLIP:
    case S3D_DISPLAY_TOPBOTTOM:
    default: {
      break;
    }
  }
}

bool wm_stereo3d_set_check(bContext * /*C*/, wmOperator * /*op*/)
{
  /* The check function guarantees that the menu is updated to show the
   * sub-options when an enum change (e.g., it shows the anaglyph options
   * when anaglyph is on, and the interlace options when this is on. */
  return true;
}

void wm_stereo3d_set_cancel(bContext * /*C*/, wmOperator *op)
{
  Stereo3dData *s3dd = static_cast<Stereo3dData *>(op->customdata);
  MEM_freeN(s3dd);
  op->customdata = nullptr;
}

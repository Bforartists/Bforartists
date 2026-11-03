/* SPDX-FileCopyrightText: 2008 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup edinterface
 *
 * Pop-Over Region
 *
 * \note This is very close to `interface_region_menu_popup.cc`.
 *
 * We could even merge them, however menu logic is already over-loaded.
 * PopOver's have the following differences.
 *
 * - UI is not constrained to a list.
 * - Pressing a button won't close the pop-over.
 * - Different draw style (to show this is has different behavior from a menu).
 * - #PanelType are used instead of #MenuType.
 * - No menu flipping support.
 * - No moving the menu to fit the mouse cursor.
 * - No key accelerators to access menu items
 *   (if we add support they would work differently).
 * - No arrow key navigation.
 * - No menu memory.
 * - No title.
 */

#include <algorithm> /* BFA - Tear-Off Menu/Panel: std::max. */
#include <cmath>     /* BFA - Tear-Off Menu/Panel: fabsf. */
#include <cstring>   /* BFA - Tear-Off Menu/Panel: strcmp in STREQ. */
#include <memory>    /* BFA - Tear-Off Menu/Panel: the space type list holds unique_ptr. */

#include "MEM_guardedalloc.h"

#include "DNA_space_enums.h" /* BFA - Tear-Off Menu/Panel: the shelf editors. */
#include "DNA_userdef_types.h"

#include "BLI_listbase.hh"

#include "BLI_math_vector_c.hh"
#include "BLI_rect.hh"
#include "BLI_utildefines.hh" /* BFA - Tear-Off Menu/Panel: STREQ. */

#include "BLT_translation.hh" /* BFA - Tear-Off Menu/Panel: the width of the title. */

#include "BKE_context.hh"
#include "BKE_report.hh"
#include "BKE_screen.hh"

#include "ED_screen.hh"

#include "WM_api.hh"
#include "WM_types.hh"

#include "UI_interface_layout.hh"
#include "UI_view2d.hh" /* BFA - Tear-Off Menu/Panel: the shelf's zoom. */

#include "interface_intern.hh"

namespace blender::ui {

/* -------------------------------------------------------------------- */
/** \name Popup Menu with Callback or String
 * \{ */

struct Popover {
  Block *block;
  Layout *layout;
  Button *but;
  ARegion *butregion;

  /* Needed for keymap removal. */
  wmWindow *window;
  wmKeyMap *keymap;
  wmEventHandler_Keymap *keymap_handler;

  PopoverCreateFunc popover_func;
  const PanelType *panel_type;

  /* Size in pixels (ui scale applied). */
  int ui_size_x;
  /** Assign accelerator keys to buttons (#BLOCK_NUMSELECT). */
  bool use_numselect;

#ifdef USE_UI_POPOVER_ONCE
  bool is_once;
#endif
};

/**
 * \param region: Optional, the region the block will be placed in. Must be set if the popover is
 *                supposed to support refreshing.
 */
static void popover_create_block(bContext *C,
                                 ARegion *region,
                                 Popover *pup,
                                 wm::OpCallContext opcontext)
{
  BLI_assert(pup->ui_size_x != 0);

  const uiStyle *style = style_get_dpi();

  pup->block = block_begin(C, region, __func__, EmbossType::Emboss);

  block_flag_enable(pup->block, BLOCK_KEEP_OPEN | BLOCK_POPOVER);
#ifdef USE_UI_POPOVER_ONCE
  if (pup->is_once) {
    block_flag_enable(pup->block, BLOCK_POPOVER_ONCE);
  }
#endif

  pup->layout = &block_layout(
      pup->block, LayoutDirection::Vertical, LayoutType::Panel, 0, 0, pup->ui_size_x, 0, 0, style);

  pup->layout->operator_context_set(opcontext);

  if (pup->but) {
    if (pup->but->context) {
      pup->layout->context_copy(pup->but->context);
    }
  }
}

/* BFA - Tear-Off Menu/Panel: must give the same value as #toolsystem_column_count in
 * space_toolsystem_common.py, so the column count doesn't change on tearing off. */
static void tear_off_shelf_width_measure(const ARegion *region,
                                         const PanelType *pt,
                                         TearOffInit &init)
{
  if (!(region->v2d.flag & V2D_IS_INIT)) {
    return;
  }
  const float view_scale = view2d_region_to_view_x(&region->v2d, 1.0f) -
                           view2d_region_to_view_x(&region->v2d, 0.0f);
  /* Zoom removed, UI scale still included. */
  const float view_width = region->winx * view_scale;
  /* What #ED_region_panels_layout_ex takes off before the panel layout. */
  const float tabs = panel_category_tabs_is_visible(region) ? UI_PANEL_CATEGORY_MARGIN_WIDTH :
                                                              0.0f;
  const float margin = panel_should_show_background(region, pt) ? 2.0f * UI_PANEL_MARGIN_X : 0.0f;
  const float layout_width = view_width - tabs - margin - 2.0f * style_get_dpi()->panelspace;
  /* The Python thresholds drop by 20 when the tabs are hidden. Folding that in here means the
   * column count can't change when the tabs of the source shelf are toggled later. */
  const float tabs_offset = (region->flag & RGN_FLAG_HIDE_CATEGORY_TABS) ? 20.0f : 0.0f;
  init.width = view_width / UI_SCALE_FAC + tabs_offset;
  init.width_chrome = init.width - layout_width / UI_SCALE_FAC;
}

/* BFA - Tear-Off Menu/Panel: the floor fits the grip and the two header icons. A one column shelf
 * has about 38 units of layout, too narrow for the header. */
int tear_off_layout_width(const wmWindow *win, const PopupBlockHandle *handle)
{
  const float width = (handle->tear_off_width - handle->tear_off_width_chrome) * UI_SCALE_FAC;
  /* BFA - Tear-Off Menu/Panel: a window made smaller must not leave a wider panel behind. */
  const int max_width = WM_window_native_pixel_size(win)[0] - 2 * UI_SCREEN_MARGIN -
                        U.widget_unit;
  return std::max(std::min(int(width + 0.5f), max_width), 3 * UI_UNIT_X);
}

/* BFA - Tear-Off Menu/Panel: same formula as #popover_panel_create. */
static int tear_off_panel_designed_ui_size(const Popover *pup)
{
  const int ui_units_x = (pup->panel_type->ui_units_x == 0) ? UI_POPOVER_WIDTH_UNITS :
                                                              pup->panel_type->ui_units_x;
  return int(ui_units_x * U.widget_unit *
             (style_get_dpi()->widget.points / UI_DEFAULT_TEXT_POINTS));
}

/* BFA - Tear-Off Menu/Panel: what the title, the grip, the two icons and a margin need, plus the
 * panel's own header buttons. A draw_header with several buttons isn't measured. */
static int tear_off_panel_header_ui_size(const Popover *pup)
{
  const PanelType *pt = pup->panel_type;
  const char *title = CTX_IFACE_(pt->translation_context, pt->label);
  const bool has_header = !(pt->flag & PANEL_TYPE_NO_HEADER);
  const int units = 4 + ((has_header && pt->draw_header) ? 1 : 0) +
                    ((has_header && pt->draw_header_preset) ? 1 : 0);
  return units * UI_UNIT_X + fontstyle_string_width(&style_get_dpi()->widget, title);
}

/* BFA - Tear-Off Menu/Panel: the designed width, or what the header needs if that's more. There's
 * no other floor, so the block is exactly as wide as its layout. */
static int tear_off_panel_default_ui_size(const Popover *pup)
{
  return std::max(tear_off_panel_designed_ui_size(pup), tear_off_panel_header_ui_size(pup));
}

/* BFA - Tear-Off Menu/Panel: in the units of #tear_off_width. */
static float tear_off_panel_width_designed(const PopupBlockHandle *handle)
{
  const Popover *pup = static_cast<const Popover *>(handle->popup_create_vars.arg);
  return float(tear_off_panel_default_ui_size(pup)) / UI_SCALE_FAC;
}

/* BFA - Tear-Off Menu/Panel: the points of #ED_region_generic_tools_region_snap_size. They fall in
 * the bands of #toolsystem_column_count in space_toolsystem_common.py, so keep those in sync. The
 * width counts the tab strip whether or not it shows, see #tear_off_shelf_width_measure. */
static float tear_off_shelf_width_snap(const float width, const float max_width)
{
  const float tabs = (U.uiflag2 & USER_UIFLAG2_PANEL_TABS_COMPACT) ? 28.0f : 20.0f;
  const auto step = [&](const int n) { return tabs + n * UI_TOOLBAR_COLUMN + UI_TOOLBAR_MARGIN; };
  /* Free above the last step, as on the real shelf: the text list reflows. */
  if (width > step(4) && max_width > step(4)) {
    return std::min(width, max_width);
  }
  float best = step(1);
  for (int n = 2; n <= 4 && step(n) <= max_width; n++) {
    if (fabsf(step(n) - width) < fabsf(best - width)) {
      best = step(n);
    }
  }
  return best;
}

/* BFA - Tear-Off Menu/Panel: see the declaration. The layout can't say, because it estimates text
 * in a panel at a fixed 10 units. So take how much of its width each button's text would use at
 * the designed width: buttons narrow about in proportion to the layout, and the tightest one ends
 * the drag. A button sized to its text doesn't narrow, so it's a limit of its own. */
float tear_off_panel_width_min(const PopupBlockHandle *handle, const Block *block)
{
  const Popover *pup = static_cast<const Popover *>(handle->popup_create_vars.arg);
  const uiFontStyle *fstyle = &style_get_dpi()->widget;
  const float to_designed = float(tear_off_panel_default_ui_size(pup)) / float(pup->ui_size_x);
  float used = 0.0f;
  float text_sized = 0.0f;
  for (const Button &but : block->buttons()) {
    const float but_width = BLI_rctf_size_x(&but.rect);
    if (but.tear_off_header || (but.flag & UI_HIDDEN) || but.drawstr.empty() || but_width < 1.0f) {
      continue;
    }
    /* These clip and scroll their value already, so long data doesn't get to set a limit. */
    if (ELEM(but.type, ButtonType::Text, ButtonType::SearchMenu)) {
      continue;
    }
    int needed = fontstyle_string_width(fstyle, but.drawstr.c_str());
    /* The text's padding, which a plain label doesn't draw. */
    if (but.type != ButtonType::Label || (but.flag & UI_HAS_ICON)) {
      needed += int(0.8f * UI_UNIT_X);
    }
    /* The room of an icon, a checkbox or a dropdown's arrow. */
    if (but.flag & UI_HAS_ICON) {
      needed += UI_UNIT_X;
    }
    if (ELEM(but.type, ButtonType::Checkbox, ButtonType::CheckboxN, ButtonType::Menu)) {
      needed += UI_UNIT_X;
    }
    /* Text that already clips at the designed width can't be what stops the panel. */
    if (but.tear_off_text_sized) {
      if (needed < tear_off_panel_default_ui_size(pup)) {
        text_sized = std::max<float>(text_sized, needed);
      }
      continue;
    }
    const float share = needed / (but_width * to_designed);
    if (share < 1.0f) {
      used = std::max(used, share);
    }
  }
  const float layout_width = std::max(float(tear_off_panel_default_ui_size(pup)) * used, text_sized);
  return std::max<float>(layout_width, tear_off_panel_header_ui_size(pup)) / UI_SCALE_FAC;
}

/* BFA - Tear-Off Menu/Panel: see the declaration. */
bool tear_off_panel_width_drag(PopupBlockHandle *handle,
                               const float start_field,
                               const float delta_px,
                               const float room_px)
{
  const float max_width = (room_px - U.widget_unit) / UI_SCALE_FAC + handle->tear_off_width_chrome;
  const float base = start_field > 0.0f ? start_field : tear_off_panel_width_designed(handle);
  const float wanted = base + delta_px / UI_SCALE_FAC;
  float width;
  if (handle->tear_off_width_default > 0.0f) {
    width = tear_off_shelf_width_snap(wanted, max_width);
  }
  else {
    const float designed = tear_off_panel_width_designed(handle);
    /* Never above the designed width: a panel with long rows can already clip them there. Nor
     * above the width at the press: the measure is an estimate that can differ a little at each
     * width, and a drag that pulls in must not push the edge out. */
    const float min_width = std::min({handle->tear_off_drag_min_width, designed, base});
    width = std::min(std::max(wanted, min_width), std::max(max_width, min_width));
    /* The designed width itself is stored as 0, which follows the scale formula. */
    if (fabsf(width - designed) < 0.5f) {
      width = 0.0f;
    }
  }
  if (width == handle->tear_off_width) {
    return false;
  }
  handle->tear_off_width = width;
  return true;
}

/* BFA - Tear-Off Menu/Panel: tool shelf panels keep the shelf's look and column count. Other
 * panels keep their designed width, including the Clip and File Browser `TOOLS` regions, which
 * don't use the column count. */
TearOffInit tear_off_init_from_region(const bContext *C, const PanelType *pt)
{
  TearOffInit init;
  init.from_region = true;
  const ScrArea *area = CTX_wm_area(C);
  const ARegion *region = CTX_wm_region(C);
  if (area && region && region->regiontype == RGN_TYPE_TOOLS &&
      ELEM(area->spacetype, SPACE_VIEW3D, SPACE_IMAGE, SPACE_NODE, SPACE_SEQ))
  {
    tear_off_shelf_width_measure(region, pt, init);
  }
  return init;
}

static Block *block_func_POPOVER(bContext *C, PopupBlockHandle *handle, void *arg_pup)
{
  Popover *pup = static_cast<Popover *>(arg_pup);

  /* Create UI block and layout now if it wasn't done between begin/end. */
  if (!pup->layout) {
    /* BFA - Tear-Off Menu/Panel: a tear-off survives scale changes, so recompute the width
     * (same formula as popover_panel_create) or the panel keeps its old pixel width. */
    if (handle->is_tear_off && pup->panel_type) {
      if (handle->tear_off_width > 0.0f) {
        pup->ui_size_x = tear_off_layout_width(CTX_wm_window(C), handle);
      }
      else {
        pup->ui_size_x = tear_off_panel_default_ui_size(pup);
      }
    }
    popover_create_block(C, handle->region, pup, wm::OpCallContext::InvokeRegionWin);

    if (pup->popover_func) {
      pup->block->handle = handle;
      pup->popover_func(C, pup->layout, const_cast<PanelType *>(pup->panel_type));
      pup->block->handle = nullptr;
    }

    pup->layout = nullptr;
  }

  /* Setup and resolve UI layout for block. */
  Block *block = pup->block;

  if (pup->use_numselect) {
    block_flag_enable(block, BLOCK_NUMSELECT);
  }

  /* in some cases we create the block before the region,
   * so we set it delayed here if necessary */
  if (BLI_findindex(&handle->region->runtime->uiblocks, block) == -1) {
    block_region_set(block, handle->region);
  }

  block_layout_resolve(block);
  const ButtonMenu *popover_button = pup->but && pup->but->type == ButtonType::Popover ?
                                         static_cast<ButtonMenu *>(pup->but) :
                                         nullptr;
  const int direction = (popover_button && (popover_button->popup_attach_direction ==
                                            PopupAttachDirection::Horizontal)) ?
                            UI_DIR_LEFT :
                            UI_DIR_DOWN | UI_DIR_CENTER_X;
  block_direction_set(block, direction);

  const int block_margin = U.widget_unit / 2;

  if (pup->but) {
    /* For a header menu we set the direction automatic. */
    block->minbounds = BLI_rctf_size_x(&pup->but->rect);
    block_bounds_set_normal(block, block_margin);

    /* If menu slides out of other menu, override direction. */
    const bool slideout = block_is_menu(pup->but->block);
    if (slideout) {
      block_direction_set(block, UI_DIR_RIGHT);
    }

    /* Store the button location for positioning the popover arrow hint. */
    if (!handle->refresh) {
      float center[2] = {BLI_rctf_cent_x(&pup->but->rect), BLI_rctf_cent_y(&pup->but->rect)};
      /* BFA - Tear-Off Menu/Panel: a button in a tear-off is in the popup's region, not the region
       * the tear-off takes its context from, so the arrow pointed somewhere else. */
      const PopupBlockHandle *but_handle = pup->but->block->handle;
      block_to_window_fl((but_handle && but_handle->is_tear_off) ?
                             handle->popup_create_vars.butregion :
                             handle->ctx_region,
                         pup->but->block,
                         &center[0],
                         &center[1]);
      /* These variables aren't used for popovers,
       * we could add new variables if there is a conflict. */
      block->bounds_offset[0] = int(center[0]);
      block->bounds_offset[1] = int(center[1]);
      copy_v2_v2_int(handle->prev_bounds_offset, block->bounds_offset);
    }
    else {
      copy_v2_v2_int(block->bounds_offset, handle->prev_bounds_offset);
    }

    if (!slideout) {
      ARegion *region = CTX_wm_region(C);

      if (region && region->panels.first() && (direction & UI_DIR_DOWN)) {
        /* For regions with panels, prefer to open to top so we can
         * see the values of the buttons below changing. */
        block_direction_set(block, UI_DIR_UP | UI_DIR_CENTER_X);
      }
      /* Prefer popover from header to be positioned into the editor. */
      else if (region) {
        if (RGN_TYPE_IS_HEADER_ANY(region->regiontype)) {
          if (RGN_ALIGN_ENUM_FROM_MASK(region->alignment) == RGN_ALIGN_BOTTOM) {
            block_direction_set(block, UI_DIR_UP | UI_DIR_CENTER_X);
          }
        }
      }
    }

    /* Estimated a maximum size so we don't go off-screen for low height
     * areas near the bottom of the window on refreshes. */
    handle->max_size_y = UI_UNIT_Y * 16.0f;
  }
  else if (pup->panel_type &&
           (pup->panel_type->offset_units_xy.x || pup->panel_type->offset_units_xy.y))
  {
    block_flag_enable(block, BLOCK_LOOP);
    block_theme_style_set(block, BLOCK_THEME_STYLE_POPUP);
    block_direction_set(block, block->direction);
    block->minbounds = UI_MENU_WIDTH_MIN;

    const int bounds_offset[2] = {
        int(pup->panel_type->offset_units_xy.x * UI_UNIT_X),
        int(pup->panel_type->offset_units_xy.y * UI_UNIT_Y),
    };
    block_bounds_set_popup(block, block_margin, bounds_offset);
  }
  else {
    /* Not attached to a button. */
    int bounds_offset[2] = {0, 0};
    block_flag_enable(block, BLOCK_LOOP);
    block_theme_style_set(block, BLOCK_THEME_STYLE_POPUP);
    block_direction_set(block, block->direction);
    /* BFA - Tear-Off Menu/Panel: the width of a tear-off is exact, the minimum would widen the
     * block and leave dead space beside its layout. */
    block->minbounds = handle->is_tear_off ? 0 : UI_MENU_WIDTH_MIN;

    if (!handle->refresh) {
      const Button *but = nullptr;
      const Button *but_first = nullptr;
      for (const Button &but_iter : block->buttons()) {
        if ((but_first == nullptr) && button_is_editable(&but_iter)) {
          but_first = &but_iter;
        }
        if (but_iter.flag & (UI_SELECT | UI_SELECT_DRAW)) {
          but = &but_iter;
          break;
        }
      }

      /* BFA - Tear-Off Menu/Panel: a tear-off opens with its header under the cursor. Placing a
       * selected toggle there would jump the panel, and a grab would hold it by that toggle.
       * `but_first` is on the header row: the collapse icon or a draw_header checkbox. */
      if (handle->is_tear_off) {
        but = nullptr;
      }

      if (but) {
        bounds_offset[0] = -(but->rect.xmin + 0.8f * BLI_rctf_size_x(&but->rect));
        bounds_offset[1] = -BLI_rctf_cent_y(&but->rect);
      }
      else {
        bounds_offset[0] = -(pup->ui_size_x / 2);
        bounds_offset[1] = but_first ? -BLI_rctf_cent_y(&but_first->rect) : (UI_UNIT_Y / 2);
      }
      copy_v2_v2_int(handle->prev_bounds_offset, bounds_offset);
    }
    else {
      copy_v2_v2_int(bounds_offset, handle->prev_bounds_offset);
    }

    block_bounds_set_popup(block, block_margin, bounds_offset);
  }

  return block;
}

static void block_free_func_POPOVER(void *arg_pup)
{
  Popover *pup = static_cast<Popover *>(arg_pup);
  if (pup->keymap != nullptr) {
    wmWindow *window = pup->window;
    WM_event_remove_keymap_handler(&window->runtime->modalhandlers, pup->keymap);
  }
  MEM_delete(pup);
}

PopupBlockHandle *popover_panel_create(bContext *C,
                                       ARegion *butregion,
                                       Button *but,
                                       PopoverCreateFunc popover_func,
                                       const PanelType *panel_type,
                                       const bool is_tear_off, // BFA - Tear-Off Menu/Panel
                                       /* BFA - Tear-Off Menu/Panel */
                                       const TearOffInit &tear_off_init)
{
  wmWindow *window = CTX_wm_window(C);
  const uiStyle *style = style_get_dpi();

  /* Create popover, buttons are created from callback. */
  Popover *pup = MEM_new<Popover>(__func__);
  pup->but = but;

  /* FIXME: maybe one day we want non panel popovers? */
  {
    const int ui_units_x = (panel_type->ui_units_x == 0) ? UI_POPOVER_WIDTH_UNITS :
                                                           panel_type->ui_units_x;
    /* Scale width by changes to Text Style point size. */
    pup->ui_size_x = ui_units_x * U.widget_unit * (style->widget.points / UI_DEFAULT_TEXT_POINTS);
  }

  pup->popover_func = popover_func;
  pup->panel_type = panel_type;

#ifdef USE_UI_POPOVER_ONCE
  {
    /* Ideally this would be passed in. */
    const wmEvent *event = window->runtime->eventstate;
    /* BFA - Tear-Off Menu/Panel: "once" closes the popup on a release over a button, and
     * RETURN_CANCEL frees even a tear-off. Tearing off during a drag has the left button held, so
     * this would be true. Without it, the is_grab path doesn't depend on who gets the release. */
    pup->is_once = !is_tear_off && (event->type == LEFTMOUSE) && (event->val == KM_PRESS);
  }
#endif

  /* Create popup block. */
  /* BFA - Tear-Off Menu/Panel: is_tear_off and tear_off_init. */
  PopupBlockHandle *handle = popup_block_create(C,
                                                butregion,
                                                but,
                                                nullptr,
                                                block_func_POPOVER,
                                                pup,
                                                block_free_func_POPOVER,
                                                true,
                                                is_tear_off,
                                                tear_off_init);

  /* Add handlers. If attached to a button, the button will already
   * add a modal handler and pass on events. */
  if (!but) {
    popup_handlers_add(C, &window->runtime->modalhandlers, handle, 0);
    WM_event_add_mousemove(window);
    handle->popup = true;
  }
  handle->srna_owner = panel_type->rna_ext.srna;
  return handle;
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Standard Popover Panels
 * \{ */

/* BFA - Tear-Off Menu/Panel: split out of #popover_panel_invoke, because most C panels can't be
 * found by name in #WM_paneltype_find. */
wmOperatorStatus popover_paneltype_invoke(bContext *C,
                                          PanelType *pt,
                                          bool keep_open,
                                          bool use_numselect,
                                          PopupBlockHandle **r_handle,
                                          const bool is_tear_off,
                                          const TearOffInit &tear_off_init)
{
  Layout *layout;
  if (pt->poll && (pt->poll(C, pt) == false)) {
    /* cancel but allow event to pass through, just like operators do */
    return (OPERATOR_CANCELLED | OPERATOR_PASS_THROUGH);
  }

  Block *block = nullptr;
  PopupBlockHandle *handle = nullptr; // BFA - Tear-Off Menu/Panel
  if (keep_open) {
    /* BFA - Tear-Off Menu/Panel: is_tear_off and tear_off_init. */
    handle = popover_panel_create(
        C, nullptr, nullptr, item_paneltype_func, pt, is_tear_off, tear_off_init);
    Popover *pup = static_cast<Popover *>(handle->popup_create_vars.arg);
    pup->use_numselect = use_numselect;
    block = pup->block;

    /* Refresh so the block is recreated with the region visible
     * (this also applies `use_numselect`).
     *
     * Without this, `block_begin` sets #BLOCK_LOOP before the region is shown,
     * causing `template_popup_confirm` to skip attaching its close callback
     * (since it assumes #BLOCK_LOOP menus close via `menuretval`).
     * With #BLOCK_KEEP_OPEN set this doesn't happen, see #151778. */
    ED_region_tag_refresh_ui(handle->region);
  }
  else {
    Popover *pup = popover_begin(C, U.widget_unit * pt->ui_units_x, false, use_numselect);
    layout = popover_layout(pup);
    ui::UI_paneltype_draw(C, pt, layout);
    ui::popover_end(C, pup, nullptr);
    block = pup->block;
    handle = block ? block->handle : nullptr; // BFA - Tear-Off Menu/Panel
  }

  if (block) {
    handle = block->handle; // BFA - Tear-Off Menu/Panel
    block_active_only_flagged_buttons(C, handle->region, block);
  }
  if (r_handle) { // BFA - Tear-Off Menu/Panel
    *r_handle = handle; // BFA - Tear-Off Menu/Panel
  }
  return OPERATOR_INTERFACE;
}

wmOperatorStatus popover_panel_invoke(
    bContext *C,
    const char *idname,
    bool keep_open,
    bool use_numselect,
    ReportList *reports,  // BFA - Tear-Off Menu/Panel
    PopupBlockHandle **r_handle, // BFA - Tear-Off Menu/Panel
    const bool is_tear_off) // BFA - Tear-Off Menu/Panel

{
  PanelType *pt = WM_paneltype_find(idname, true);
  if (pt == nullptr) {
    BKE_reportf(reports, RPT_ERROR, "Panel \"%s\" not found", idname);
    return OPERATOR_CANCELLED;
  }
  return popover_paneltype_invoke(C, pt, keep_open, use_numselect, r_handle, is_tear_off);
}

/* BFA - Tear-Off Menu/Panel: search the source region first. A region can draw another space's
 * list (`category_override`, see #ED_view3d_buttons_region_layout_ex), so all spaces are the
 * last resort. */
PanelType *tear_off_paneltype_find(const bContext *C, const char *idname)
{
  auto find_in = [&](ARegionType &art) -> PanelType * {
    for (PanelType &pt : art.paneltypes) {
      if (STREQ(pt.idname, idname)) {
        return &pt;
      }
    }
    return nullptr;
  };
  if (const ARegion *region = CTX_wm_region(C)) {
    if (region->runtime->type) {
      if (PanelType *pt = find_in(*region->runtime->type)) {
        return pt;
      }
    }
  }
  if (PanelType *pt = WM_paneltype_find(idname, true)) {
    return pt;
  }
  for (const std::unique_ptr<SpaceType> &st : BKE_spacetypes_list()) {
    for (ARegionType &art : st->regiontypes) {
      if (PanelType *pt = find_in(art)) {
        return pt;
      }
    }
  }
  return nullptr;
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Popup Menu API with begin & end
 * \{ */

Popover *popover_begin(bContext *C, int ui_menu_width, bool from_active_button, bool use_numselect)
{
  Popover *pup = MEM_new<Popover>(__func__);
  if (ui_menu_width == 0) {
    ui_menu_width = U.widget_unit * UI_POPOVER_WIDTH_UNITS;
  }
  pup->ui_size_x = ui_menu_width;
  pup->use_numselect = use_numselect;

  ARegion *butregion = nullptr;
  Button *but = nullptr;

  if (from_active_button) {
    butregion = CTX_wm_region(C);
    but = region_active_but_get(butregion);
    if (but == nullptr) {
      butregion = nullptr;
    }
  }

  pup->but = but;
  pup->butregion = butregion;

  /* Operator context default same as menus, change if needed. */
  popover_create_block(C, nullptr, pup, wm::OpCallContext::ExecRegionWin);

  /* Create in advance so we can let buttons point to #PopupBlockHandle::retvalue
   * (and other return values) already. */
  pup->block->handle = MEM_new<PopupBlockHandle>(__func__);

  return pup;
}

static void popover_keymap_fn(wmKeyMap * /*keymap*/, wmKeyMapItem * /*kmi*/, void *user_data)
{
  Popover *pup = static_cast<Popover *>(user_data);
  pup->block->handle->menuretval = RETURN_OK;
}

void popover_end(bContext *C, Popover *pup, wmKeyMap *keymap)
{
  wmWindow *window = CTX_wm_window(C);

  if (keymap) {
    /* Add so we get keymaps shown in the buttons. */
    block_flag_enable(pup->block, BLOCK_SHOW_SHORTCUT_ALWAYS);
    pup->keymap = keymap;
    pup->keymap_handler = WM_event_add_keymap_handler_priority(
        &window->runtime->modalhandlers, keymap, 0);
    WM_event_set_keymap_handler_post_callback(pup->keymap_handler, popover_keymap_fn, pup);
  }

  /* Create popup block. No refresh support since the buttons were created
   * between begin/end and we have no callback to recreate them. */
  PopupBlockHandle *handle = popup_block_create(C,
                                                pup->butregion,
                                                pup->but,
                                                nullptr,
                                                block_func_POPOVER,
                                                pup,
                                                block_free_func_POPOVER,
                                                false);

  /* Add handlers. */
  popup_handlers_add(C, &window->runtime->modalhandlers, handle, 0);
  WM_event_add_mousemove(window);
  handle->popup = true;

  /* Re-add so it gets priority. */
  if (keymap) {
    BLI_remlink(&window->runtime->modalhandlers, pup->keymap_handler);
    BLI_addhead(&window->runtime->modalhandlers, pup->keymap_handler);
  }

  pup->window = window;

  /* TODO(@ideasman42): we may want to make this configurable.
   * The begin/end type of calling popups doesn't allow 'can_refresh' to be set.
   * For now close this style of popovers when accessed. */
  block_flag_disable(pup->block, BLOCK_KEEP_OPEN);
}

Layout *popover_layout(Popover *pup)
{
  return pup->layout;
}

#ifdef USE_UI_POPOVER_ONCE
void popover_once_clear(Popover *pup)
{
  pup->is_once = false;
}
#endif

/** \} */

}  // namespace blender::ui

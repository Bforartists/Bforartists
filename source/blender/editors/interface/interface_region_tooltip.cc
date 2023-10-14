/* SPDX-FileCopyrightText: 2008 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup edinterface
 *
 * ToolTip Region and Construction
 */

/* TODO(@ideasman42):
 * We may want to have a higher level API that initializes a timer,
 * checks for mouse motion and clears the tool-tip afterwards.
 * We never want multiple tool-tips at once
 * so this could be handled on the window / window-manager level.
 *
 * For now it's not a priority, so leave as-is.
 */

#include <cstdarg>
#include <cstdlib>
#include <cstring>

#include "MEM_guardedalloc.h"

#include "DNA_brush_types.h"
#include "DNA_userdef_types.h"

#include "BLI_listbase.h"
#include "BLI_math_color.h"
#include "BLI_math_vector.h"
#include "BLI_rect.h"
#include "BLI_string.h"
#include "BLI_utildefines.h"

#include "BKE_context.h"
#include "BKE_paint.hh"
#include "BKE_screen.hh"

#include "BIF_glutil.hh"

#include "GPU_immediate.h"
#include "GPU_immediate_util.h"
#include "GPU_state.h"

#include "IMB_imbuf.h"
#include "IMB_imbuf_types.h"

#include "WM_api.hh"
#include "WM_types.hh"

#include "RNA_access.hh"
#include "RNA_path.hh"

#include "UI_interface.hh"

#include "BLF_api.h"
#include "BLT_translation.h"

#ifdef WITH_PYTHON
#  include "BPY_extern_run.h"
#endif

#include "ED_screen.hh"

#include "interface_intern.hh"
#include "interface_regions_intern.hh"

#define UI_TIP_SPACER 0.3f
#define UI_TIP_PADDING int(1.3f * UI_UNIT_Y)
#define UI_TIP_MAXWIDTH 600
#define UI_TIP_MAXIMAGEWIDTH 500
#define UI_TIP_MAXIMAGEHEIGHT 300
#define UI_TIP_STR_MAX 1024

struct uiTooltipFormat {
  uiTooltipStyle style;
  uiTooltipColorID color_id;
};

struct uiTooltipField {
  /** Allocated text (owned by this structure), may be null. */
  const char *text;
  /** Allocated text (owned by this structure), may be null. */
  const char *text_suffix;
  struct {
    /** X cursor position at the end of the last line. */
    uint x_pos;
    /** Number of lines, 1 or more with word-wrap. */
    uint lines;
  } geom;
  uiTooltipFormat format;
  ImBuf *image;
  short image_size[2];
};

struct uiTooltipData {
  rcti bbox;
  uiTooltipField *fields;
  uint fields_len;
  uiFontStyle fstyle;
  int wrap_width;
  int toth, lineh;
};

BLI_STATIC_ASSERT(int(UI_TIP_LC_MAX) == int(UI_TIP_LC_ALERT) + 1, "invalid lc-max");

static uiTooltipField *text_field_add_only(uiTooltipData *data)
{
  data->fields_len += 1;
  data->fields = static_cast<uiTooltipField *>(
      MEM_recallocN(data->fields, sizeof(*data->fields) * data->fields_len));
  return &data->fields[data->fields_len - 1];
}

void UI_tooltip_text_field_add(uiTooltipData *data,
                               char *text,
                               char *suffix,
                               const uiTooltipStyle style,
                               const uiTooltipColorID color_id,
                               const bool is_pad)
{
  if (is_pad) {
    /* Add a spacer field before this one. */
    UI_tooltip_text_field_add(
        data, nullptr, nullptr, UI_TIP_STYLE_SPACER, UI_TIP_LC_NORMAL, false);
  }

  uiTooltipField *field = text_field_add_only(data);
  field->format = {};
  field->format.style = style;
  field->format.color_id = color_id;
  field->text = text;
  field->text_suffix = suffix;
}

void UI_tooltip_image_field_add(uiTooltipData *data, const ImBuf *image, const short image_size[2])
{
  uiTooltipField *field = text_field_add_only(data);
  field->format = {};
  field->format.style = UI_TIP_STYLE_IMAGE;
  field->image = IMB_dupImBuf(image);
  field->image_size[0] = MIN2(image_size[0], UI_TIP_MAXIMAGEWIDTH * UI_SCALE_FAC);
  field->image_size[1] = MIN2(image_size[1], UI_TIP_MAXIMAGEHEIGHT * UI_SCALE_FAC);
  field->text = nullptr;
}

/* -------------------------------------------------------------------- */
/** \name ToolTip Callbacks (Draw & Free)
 * \{ */

static void rgb_tint(float col[3], float h, float h_strength, float v, float v_strength)
{
  float col_hsv_from[3];
  float col_hsv_to[3];

  rgb_to_hsv_v(col, col_hsv_from);

  col_hsv_to[0] = h;
  col_hsv_to[1] = h_strength;
  col_hsv_to[2] = (col_hsv_from[2] * (1.0f - v_strength)) + (v * v_strength);

  hsv_to_rgb_v(col_hsv_to, col);
}

static void ui_tooltip_region_draw_cb(const bContext * /*C*/, ARegion *region)
{
  const float pad_px = UI_TIP_PADDING;
  uiTooltipData *data = static_cast<uiTooltipData *>(region->regiondata);
  const uiWidgetColors *theme = ui_tooltip_get_theme();
  rcti bbox = data->bbox;
  float tip_colors[UI_TIP_LC_MAX][3];
  uchar drawcol[4] = {0, 0, 0, 255}; /* to store color in while drawing (alpha is always 255) */

  /* The color from the theme. */
  float *main_color = tip_colors[UI_TIP_LC_MAIN];
  float *value_color = tip_colors[UI_TIP_LC_VALUE];
  float *active_color = tip_colors[UI_TIP_LC_ACTIVE];
  float *normal_color = tip_colors[UI_TIP_LC_NORMAL];
  float *python_color = tip_colors[UI_TIP_LC_PYTHON];
  float *alert_color = tip_colors[UI_TIP_LC_ALERT];

  float background_color[3];

  wmOrtho2_region_pixelspace(region);

  /* Draw background. */
  ui_draw_tooltip_background(UI_style_get(), nullptr, &bbox);

  /* set background_color */
  rgb_uchar_to_float(background_color, theme->inner);

  /* Calculate `normal_color`. */
  rgb_uchar_to_float(main_color, theme->text);
  copy_v3_v3(active_color, main_color);
  copy_v3_v3(normal_color, main_color);
  copy_v3_v3(python_color, main_color);
  copy_v3_v3(alert_color, main_color);
  copy_v3_v3(value_color, main_color);

  /* Find the brightness difference between background and text colors. */

  const float tone_bg = rgb_to_grayscale(background_color);
  // tone_fg = rgb_to_grayscale(main_color);

  /* Mix the colors. */
  rgb_tint(value_color, 0.0f, 0.0f, tone_bg, 0.2f);  /* Light gray. */
  rgb_tint(active_color, 0.6f, 0.2f, tone_bg, 0.2f); /* Light blue. */
  rgb_tint(normal_color, 0.0f, 0.0f, tone_bg, 0.4f); /* Gray. */
  rgb_tint(python_color, 0.0f, 0.0f, tone_bg, 0.5f); /* Dark gray. */
  rgb_tint(alert_color, 0.0f, 0.8f, tone_bg, 0.1f);  /* Red. */

  /* Draw text. */
  BLF_wordwrap(data->fstyle.uifont_id, data->wrap_width);
  BLF_wordwrap(blf_mono_font, data->wrap_width);

  bbox.xmin += 0.5f * pad_px; /* add padding to the text */
  bbox.ymax -= 0.25f * pad_px;

  for (int i = 0; i < data->fields_len; i++) {
    const uiTooltipField *field = &data->fields[i];

    bbox.ymin = bbox.ymax - (data->lineh * field->geom.lines);
    if (field->format.style == UI_TIP_STYLE_HEADER) {
      uiFontStyleDraw_Params fs_params{};
      fs_params.align = UI_STYLE_TEXT_LEFT;
      fs_params.word_wrap = true;

      /* Draw header and active data (is done here to be able to change color). */
      rgb_float_to_uchar(drawcol, tip_colors[UI_TIP_LC_MAIN]);
      UI_fontstyle_set(&data->fstyle);
      UI_fontstyle_draw(&data->fstyle, &bbox, field->text, UI_TIP_STR_MAX, drawcol, &fs_params);

      /* Offset to the end of the last line. */
      if (field->text_suffix) {
        const float xofs = field->geom.x_pos;
        const float yofs = data->lineh * (field->geom.lines - 1);
        bbox.xmin += xofs;
        bbox.ymax -= yofs;

        rgb_float_to_uchar(drawcol, tip_colors[UI_TIP_LC_ACTIVE]);
        UI_fontstyle_draw(
            &data->fstyle, &bbox, field->text_suffix, UI_TIP_STR_MAX, drawcol, &fs_params);

        /* Undo offset. */
        bbox.xmin -= xofs;
        bbox.ymax += yofs;
      }
    }
    else if (field->format.style == UI_TIP_STYLE_MONO) {
      uiFontStyleDraw_Params fs_params{};
      fs_params.align = UI_STYLE_TEXT_LEFT;
      fs_params.word_wrap = true;
      uiFontStyle fstyle_mono = data->fstyle;
      fstyle_mono.uifont_id = blf_mono_font;

      UI_fontstyle_set(&fstyle_mono);
      /* XXX: needed because we don't have mono in 'U.uifonts'. */
      BLF_size(fstyle_mono.uifont_id, fstyle_mono.points * UI_SCALE_FAC);
      rgb_float_to_uchar(drawcol, tip_colors[int(field->format.color_id)]);
      UI_fontstyle_draw(&fstyle_mono, &bbox, field->text, UI_TIP_STR_MAX, drawcol, &fs_params);
    }
    else if (field->format.style == UI_TIP_STYLE_IMAGE) {

      bbox.ymax -= field->image_size[1];

      GPU_blend(GPU_BLEND_ALPHA_PREMULT);
      IMMDrawPixelsTexState state = immDrawPixelsTexSetup(GPU_SHADER_3D_IMAGE_COLOR);
      immDrawPixelsTexScaledFullSize(&state,
                                     bbox.xmin,
                                     bbox.ymax,
                                     field->image->x,
                                     field->image->y,
                                     GPU_RGBA8,
                                     true,
                                     field->image->byte_buffer.data,
                                     1.0f,
                                     1.0f,
                                     float(field->image_size[0]) / float(field->image->x),
                                     float(field->image_size[1]) / float(field->image->y),
                                     nullptr);

      GPU_blend(GPU_BLEND_ALPHA);
    }
    else if (field->format.style == UI_TIP_STYLE_SPACER) {
      bbox.ymax -= data->lineh * UI_TIP_SPACER;
    }
    else {
      BLI_assert(field->format.style == UI_TIP_STYLE_NORMAL);
      uiFontStyleDraw_Params fs_params{};
      fs_params.align = UI_STYLE_TEXT_LEFT;
      fs_params.word_wrap = true;

      /* Draw remaining data. */
      rgb_float_to_uchar(drawcol, tip_colors[int(field->format.color_id)]);
      UI_fontstyle_set(&data->fstyle);
      UI_fontstyle_draw(&data->fstyle, &bbox, field->text, UI_TIP_STR_MAX, drawcol, &fs_params);
    }

    bbox.ymax -= data->lineh * field->geom.lines;
  }

  BLF_disable(data->fstyle.uifont_id, BLF_WORD_WRAP);
  BLF_disable(blf_mono_font, BLF_WORD_WRAP);
}

static void ui_tooltip_region_free_cb(ARegion *region)
{
  uiTooltipData *data = static_cast<uiTooltipData *>(region->regiondata);

  for (int i = 0; i < data->fields_len; i++) {
    const uiTooltipField *field = &data->fields[i];
    if (field->text) {
      MEM_freeN((void *)field->text);
    }
    if (field->text_suffix) {
      MEM_freeN((void *)field->text_suffix);
    }
    if (field->image) {
      IMB_freeImBuf(field->image);
    }
  }
  MEM_freeN(data->fields);
  MEM_freeN(data);
  region->regiondata = nullptr;
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name ToolTip Creation Utility Functions
 * \{ */

static char *ui_tooltip_text_python_from_op(bContext *C, wmOperatorType *ot, PointerRNA *opptr)
{
  char *str = WM_operator_pystring_ex(C, nullptr, false, false, ot, opptr);

  /* Avoid overly verbose tips (eg, arrays of 20 layers), exact limit is arbitrary. */
  WM_operator_pystring_abbreviate(str, 32);

  return str;
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name ToolTip Creation
 * \{ */

#ifdef WITH_PYTHON

static bool ui_tooltip_data_append_from_keymap(bContext *C, uiTooltipData *data, wmKeyMap *keymap)
{
  const int fields_len_init = data->fields_len;
  char buf[512];

  LISTBASE_FOREACH (wmKeyMapItem *, kmi, &keymap->items) {
    wmOperatorType *ot = WM_operatortype_find(kmi->idname, true);
    if (ot != nullptr) {
      /* Tip. */
      {
        UI_tooltip_text_field_add(data,
                                  BLI_strdup(ot->description ? ot->description : ot->name),
                                  nullptr,
                                  UI_TIP_STYLE_NORMAL,
                                  UI_TIP_LC_MAIN,
                                  true);
      }
      /* Shortcut. */
      {
        bool found = false;
        if (WM_keymap_item_to_string(kmi, false, buf, sizeof(buf))) {
          found = true;
        }
        UI_tooltip_text_field_add(data,
                                  BLI_sprintfN(TIP_("Shortcut: %s"), found ? buf : "None"),
                                  nullptr,
                                  UI_TIP_STYLE_NORMAL,
                                  UI_TIP_LC_NORMAL);
      }

      /* Python. */
      if (U.flag & USER_TOOLTIPS_PYTHON) {
        char *str = ui_tooltip_text_python_from_op(C, ot, kmi->ptr);
        UI_tooltip_text_field_add(data,
                                  BLI_sprintfN(TIP_("Python: %s"), str),
                                  nullptr,
                                  UI_TIP_STYLE_NORMAL,
                                  UI_TIP_LC_PYTHON);
        MEM_freeN(str);
      }
    }
  }

  return (fields_len_init != data->fields_len);
}

#endif /* WITH_PYTHON */

/**
 * Special tool-system exception.
 */
static uiTooltipData *ui_tooltip_data_from_tool(bContext *C, uiBut *but, bool is_label)
{
  if (but->optype == nullptr) {
    return nullptr;
  }
  /* While this should always be set for buttons as they are shown in the UI,
   * the operator search popup can create a button that has no properties, see: #112541. */
  if (but->opptr == nullptr) {
    return nullptr;
  }

  if (!STREQ(but->optype->idname, "WM_OT_tool_set_by_id")) {
    return nullptr;
  }

  /* Needed to get the space-data's type (below). */
  if (CTX_wm_space_data(C) == nullptr) {
    return nullptr;
  }

  char tool_id[MAX_NAME];
  RNA_string_get(but->opptr, "name", tool_id);
  BLI_assert(tool_id[0] != '\0');

  /* When false, we're in a different space type to the tool being set.
   * Needed for setting the fallback tool from the properties space.
   *
   * If we drop the hard coded 3D-view in properties hack, we can remove this check. */
  bool has_valid_context = true;
  const char *has_valid_context_error = IFACE_("Unsupported context");
  {
    ScrArea *area = CTX_wm_area(C);
    if (area == nullptr) {
      has_valid_context = false;
    }
    else {
      PropertyRNA *prop = RNA_struct_find_property(but->opptr, "space_type");
      if (RNA_property_is_set(but->opptr, prop)) {
        const int space_type_prop = RNA_property_enum_get(but->opptr, prop);
        if (space_type_prop != area->spacetype) {
          has_valid_context = false;
        }
      }
    }
  }

  /* We have a tool, now extract the info. */
  uiTooltipData *data = MEM_cnew<uiTooltipData>(__func__);

#ifdef WITH_PYTHON
  /* It turns out to be most simple to do this via Python since C
   * doesn't have access to information about non-active tools. */

  /* Title (when icon-only). */
  if (but->drawstr[0] == '\0') {
    const char *expr_imports[] = {"bpy", "bl_ui", nullptr};
    char expr[256];
    SNPRINTF(expr,
             "bl_ui.space_toolsystem_common.item_from_id("
             "bpy.context, "
             "bpy.context.space_data.type, "
             "'%s').label",
             tool_id);
    char *expr_result = nullptr;
    bool is_error = false;

    if (has_valid_context == false) {
      expr_result = BLI_strdup(has_valid_context_error);
    }
    else if (BPY_run_string_as_string(C, expr_imports, expr, nullptr, &expr_result)) {
      if (STREQ(expr_result, "")) {
        MEM_freeN(expr_result);
        expr_result = nullptr;
      }
    }
    else {
      /* NOTE: this is an exceptional case, we could even remove it
       * however there have been reports of tooltips failing, so keep it for now. */
      expr_result = BLI_strdup(IFACE_("Internal error!"));
      is_error = true;
    }

    if (expr_result != nullptr) {
      /* NOTE: This is a very weak hack to get a valid translation most of the time...
       * Proper way to do would be to get i18n context from the item, somehow. */
      const char *label_str = CTX_IFACE_(BLT_I18NCONTEXT_OPERATOR_DEFAULT, expr_result);
      if (label_str == expr_result) {
        label_str = IFACE_(expr_result);
      }

      if (label_str != expr_result) {
        MEM_freeN(expr_result);
        expr_result = BLI_strdup(label_str);
      }

      UI_tooltip_text_field_add(data,
                                expr_result,
                                nullptr,
                                UI_TIP_STYLE_NORMAL,
                                (is_error) ? UI_TIP_LC_ALERT : UI_TIP_LC_MAIN,
                                true);
    }
  }

  /* Tip. */
  if (is_label == false) {
    const char *expr_imports[] = {"bpy", "bl_ui", nullptr};
    char expr[256];
    SNPRINTF(expr,
             "bl_ui.space_toolsystem_common.description_from_id("
             "bpy.context, "
             "bpy.context.space_data.type, "
             "'%s') + '.'",
             tool_id);

    char *expr_result = nullptr;
    bool is_error = false;

    if (has_valid_context == false) {
      expr_result = BLI_strdup(has_valid_context_error);
    }
    else if (BPY_run_string_as_string(C, expr_imports, expr, nullptr, &expr_result)) {
      if (STREQ(expr_result, ".")) {
        MEM_freeN(expr_result);
        expr_result = nullptr;
      }
    }
    else {
      /* NOTE: this is an exceptional case, we could even remove it
       * however there have been reports of tooltips failing, so keep it for now. */
      expr_result = BLI_strdup(TIP_("Internal error!"));
      is_error = true;
    }

    if (expr_result != nullptr) {
      UI_tooltip_text_field_add(data,
                                expr_result,
                                nullptr,
                                UI_TIP_STYLE_NORMAL,
                                (is_error) ? UI_TIP_LC_ALERT : UI_TIP_LC_MAIN,
                                true);
    }
  }

  /* Shortcut. */
  const bool show_shortcut = is_label == false &&
                             ((but->block->flag & UI_BLOCK_SHOW_SHORTCUT_ALWAYS) == 0);

  if (show_shortcut) {
    /* There are different kinds of shortcuts:
     *
     * - Direct access to the tool (as if the toolbar button is pressed).
     * - The key is bound to a brush type (not the exact brush name).
     * - The key is assigned to the operator itself
     *   (bypassing the tool, executing the operator).
     *
     * Either way case it's useful to show the shortcut.
     */
    char *shortcut = nullptr;

    {
      uiStringInfo op_keymap = {BUT_GET_OP_KEYMAP, nullptr};
      UI_but_string_info_get(C, but, &op_keymap, nullptr);
      shortcut = op_keymap.strinfo;
    }

    if (shortcut == nullptr) {
      const ePaintMode paint_mode = BKE_paintmode_get_active_from_context(C);
      const char *tool_attr = BKE_paint_get_tool_prop_id_from_paintmode(paint_mode);
      if (tool_attr != nullptr) {
        const EnumPropertyItem *items = BKE_paint_get_tool_enum_from_paintmode(paint_mode);
        const char *tool_id_lstrip = strrchr(tool_id, '.');
        const int tool_id_offset = tool_id_lstrip ? ((tool_id_lstrip - tool_id) + 1) : 0;
        const int i = RNA_enum_from_name(items, tool_id + tool_id_offset);

        if (i != -1) {
          wmOperatorType *ot = WM_operatortype_find("paint.brush_select", true);
          PointerRNA op_props;
          WM_operator_properties_create_ptr(&op_props, ot);
          RNA_enum_set(&op_props, tool_attr, items[i].value);

          /* Check for direct access to the tool. */
          char shortcut_brush[128] = "";
          if (WM_key_event_operator_string(C,
                                           ot->idname,
                                           WM_OP_INVOKE_REGION_WIN,
                                           static_cast<IDProperty *>(op_props.data),
                                           true,
                                           shortcut_brush,
                                           ARRAY_SIZE(shortcut_brush)))
          {
            shortcut = BLI_strdup(shortcut_brush);
          }
          WM_operator_properties_free(&op_props);
        }
      }
    }

    if (shortcut == nullptr) {
      /* Check for direct access to the tool. */
      char shortcut_toolbar[128] = "";
      if (WM_key_event_operator_string(C,
                                       "WM_OT_toolbar",
                                       WM_OP_INVOKE_REGION_WIN,
                                       nullptr,
                                       true,
                                       shortcut_toolbar,
                                       ARRAY_SIZE(shortcut_toolbar)))
      {
        /* Generate keymap in order to inspect it.
         * NOTE: we could make a utility to avoid the keymap generation part of this. */
        const char *expr_imports[] = {
            "bpy", "bl_keymap_utils", "bl_keymap_utils.keymap_from_toolbar", nullptr};
        const char *expr =
            ("getattr("
             "bl_keymap_utils.keymap_from_toolbar.generate("
             "bpy.context, "
             "bpy.context.space_data.type), "
             "'as_pointer', lambda: 0)()");

        intptr_t expr_result = 0;

        if (has_valid_context == false) {
          shortcut = BLI_strdup(has_valid_context_error);
        }
        else if (BPY_run_string_as_intptr(C, expr_imports, expr, nullptr, &expr_result)) {
          if (expr_result != 0) {
            wmKeyMap *keymap = (wmKeyMap *)expr_result;
            LISTBASE_FOREACH (wmKeyMapItem *, kmi, &keymap->items) {
              if (STREQ(kmi->idname, but->optype->idname)) {
                char tool_id_test[MAX_NAME];
                RNA_string_get(kmi->ptr, "name", tool_id_test);
                if (STREQ(tool_id, tool_id_test)) {
                  char buf[128];
                  WM_keymap_item_to_string(kmi, false, buf, sizeof(buf));
                  shortcut = BLI_sprintfN("%s, %s", shortcut_toolbar, buf);
                  break;
                }
              }
            }
          }
        }
        else {
          BLI_assert(0);
        }
      }
    }

    if (shortcut != nullptr) {
      UI_tooltip_text_field_add(data,
                                BLI_sprintfN(TIP_("Shortcut: %s"), shortcut),
                                nullptr,
                                UI_TIP_STYLE_NORMAL,
                                UI_TIP_LC_VALUE,
                                true);
      MEM_freeN(shortcut);
    }
  }

  if (show_shortcut) {
    /* Shortcut for Cycling
     *
     * As a second option, we may have a shortcut to cycle this tool group.
     *
     * Since some keymaps may use this for the primary means of binding keys,
     * it's useful to show these too.
     * Without this there is no way to know how to use a key to set the tool.
     *
     * This is a little involved since the shortcut may be bound to another tool in this group,
     * instead of the current tool on display. */

    char *expr_result = nullptr;
    size_t expr_result_len;

    {
      const char *expr_imports[] = {"bpy", "bl_ui", nullptr};
      char expr[256];
      SNPRINTF(expr,
               "'\\x00'.join("
               "item.idname for item in bl_ui.space_toolsystem_common.item_group_from_id("
               "bpy.context, "
               "bpy.context.space_data.type, '%s', coerce=True) "
               "if item is not None)",
               tool_id);

      if (has_valid_context == false) {
        /* pass */
      }
      else if (BPY_run_string_as_string_and_len(
                   C, expr_imports, expr, nullptr, &expr_result, &expr_result_len))
      {
        /* pass. */
      }
    }

    if (expr_result != nullptr) {
      PointerRNA op_props;
      WM_operator_properties_create_ptr(&op_props, but->optype);
      RNA_boolean_set(&op_props, "cycle", true);

      char shortcut[128] = "";

      const char *item_end = expr_result + expr_result_len;
      const char *item_step = expr_result;

      while (item_step < item_end) {
        RNA_string_set(&op_props, "name", item_step);
        if (WM_key_event_operator_string(C,
                                         but->optype->idname,
                                         WM_OP_INVOKE_REGION_WIN,
                                         static_cast<IDProperty *>(op_props.data),
                                         true,
                                         shortcut,
                                         ARRAY_SIZE(shortcut)))
        {
          break;
        }
        item_step += strlen(item_step) + 1;
      }

      WM_operator_properties_free(&op_props);
      MEM_freeN(expr_result);

      if (shortcut[0] != '\0') {
        UI_tooltip_text_field_add(data,
                                  BLI_sprintfN(TIP_("Shortcut Cycle: %s"), shortcut),
                                  nullptr,
                                  UI_TIP_STYLE_NORMAL,
                                  UI_TIP_LC_VALUE,
                                  true);
      }
    }
  }

  /* Python */
  if ((is_label == false) && (U.flag & USER_TOOLTIPS_PYTHON)) {
    char *str = ui_tooltip_text_python_from_op(C, but->optype, but->opptr);
    UI_tooltip_text_field_add(data,
                              BLI_sprintfN(TIP_("Python: %s"), str),
                              nullptr,
                              UI_TIP_STYLE_NORMAL,
                              UI_TIP_LC_PYTHON,
                              true);
    MEM_freeN(str);
  }

  /* Keymap */

  /* This is too handy not to expose somehow, let's be sneaky for now. */
  if ((is_label == false) && CTX_wm_window(C)->eventstate->modifier & KM_SHIFT) {
    const char *expr_imports[] = {"bpy", "bl_ui", nullptr};
    char expr[256];
    SNPRINTF(expr,
             "getattr("
             "bl_ui.space_toolsystem_common.keymap_from_id("
             "bpy.context, "
             "bpy.context.space_data.type, "
             "'%s'), "
             "'as_pointer', lambda: 0)()",
             tool_id);

    intptr_t expr_result = 0;

    if (has_valid_context == false) {
      /* pass */
    }
    else if (BPY_run_string_as_intptr(C, expr_imports, expr, nullptr, &expr_result)) {
      if (expr_result != 0) {
        UI_tooltip_text_field_add(data,
                                  BLI_strdup("Tool Keymap:"),
                                  nullptr,
                                  UI_TIP_STYLE_NORMAL,
                                  UI_TIP_LC_NORMAL,
                                  true);
        wmKeyMap *keymap = (wmKeyMap *)expr_result;
        ui_tooltip_data_append_from_keymap(C, data, keymap);
      }
    }
    else {
      BLI_assert(0);
    }
  }
#else
  UNUSED_VARS(is_label, has_valid_context, has_valid_context_error);
#endif /* WITH_PYTHON */

  if (data->fields_len == 0) {
    MEM_freeN(data);
    return nullptr;
  }
  return data;
}

static uiTooltipData *ui_tooltip_data_from_button_or_extra_icon(bContext *C,
                                                                uiBut *but,
                                                                uiButExtraOpIcon *extra_icon,
                                                                const bool is_label)
{
  uiStringInfo but_label = {BUT_GET_LABEL, nullptr};
  uiStringInfo but_tip_label = {BUT_GET_TIP_LABEL, nullptr};
  uiStringInfo but_tip = {BUT_GET_TIP, nullptr};
  uiStringInfo enum_label = {BUT_GET_RNAENUM_LABEL, nullptr};
  uiStringInfo enum_tip = {BUT_GET_RNAENUM_TIP, nullptr};
  uiStringInfo op_keymap = {BUT_GET_OP_KEYMAP, nullptr};
  uiStringInfo prop_keymap = {BUT_GET_PROP_KEYMAP, nullptr};
  uiStringInfo rna_struct = {BUT_GET_RNASTRUCT_IDENTIFIER, nullptr};
  uiStringInfo rna_prop = {BUT_GET_RNAPROP_IDENTIFIER, nullptr};

  char buf[512];

  wmOperatorType *optype = extra_icon ? UI_but_extra_operator_icon_optype_get(extra_icon) :
                                        but->optype;
  PropertyRNA *rnaprop = extra_icon ? nullptr : but->rnaprop;

  /* create tooltip data */
  uiTooltipData *data = MEM_cnew<uiTooltipData>(__func__);

  if (extra_icon) {
    if (is_label) {
      UI_but_extra_icon_string_info_get(
          C, extra_icon, &but_tip_label, &but_label, &enum_label, nullptr);
    }
    else {
      UI_but_extra_icon_string_info_get(
          C, extra_icon, &but_label, &but_tip_label, &but_tip, &op_keymap, nullptr);
    }
  }
  else {
    if (is_label) {
      UI_but_string_info_get(C, but, &but_tip_label, &but_label, &enum_label, nullptr);
    }
    else {
      UI_but_string_info_get(C,
                             but,
                             &but_label,
                             &but_tip_label,
                             &but_tip,
                             &enum_label,
                             &enum_tip,
                             &op_keymap,
                             &prop_keymap,
                             &rna_struct,
                             &rna_prop,
                             nullptr);
    }
  }

  /* Label: If there is a custom tooltip label, use that to override the label to display.
   * Otherwise fallback to the regular label. */
  if (but_tip_label.strinfo) {
    UI_tooltip_text_field_add(
        data, BLI_strdup(but_tip_label.strinfo), nullptr, UI_TIP_STYLE_HEADER, UI_TIP_LC_NORMAL);
  }
  /* Regular (non-custom) label. Only show when the button doesn't already show the label. Check
   * prefix instead of comparing because the button may include the shortcut. Buttons with dynamic
   * tool-tips also don't get their default label here since they can already provide more accurate
   * and specific tool-tip content. */
  else if (but_label.strinfo && !STRPREFIX(but->drawstr, but_label.strinfo) && !but->tip_func) {
    UI_tooltip_text_field_add(
        data, BLI_strdup(but_label.strinfo), nullptr, UI_TIP_STYLE_HEADER, UI_TIP_LC_NORMAL);
  }

  /* Tip */
  if (but_tip.strinfo) {
    {
      if (enum_label.strinfo) {
        UI_tooltip_text_field_add(data,
                                  BLI_sprintfN("%s:  ", but_tip.strinfo),
                                  BLI_strdup(enum_label.strinfo),
                                  UI_TIP_STYLE_HEADER,
                                  UI_TIP_LC_NORMAL);
      }
      else {
        UI_tooltip_text_field_add(data,
                                  BLI_sprintfN("%s.", but_tip.strinfo),
                                  nullptr,
                                  UI_TIP_STYLE_HEADER,
                                  UI_TIP_LC_NORMAL);
      }
    }

    /* special case enum rna buttons */
    if ((but->type & UI_BTYPE_ROW) && rnaprop && RNA_property_flag(rnaprop) & PROP_ENUM_FLAG) {
      UI_tooltip_text_field_add(data,
                                BLI_strdup(TIP_("(Shift-Click/Drag to select multiple)")),
                                nullptr,
                                UI_TIP_STYLE_NORMAL,
                                UI_TIP_LC_NORMAL);
    }
  }
  /* When there is only an enum label (no button label or tip), draw that as header. */
  else if (enum_label.strinfo && !(but_label.strinfo && but_label.strinfo[0])) {
    UI_tooltip_text_field_add(
        data, BLI_strdup(enum_label.strinfo), nullptr, UI_TIP_STYLE_HEADER, UI_TIP_LC_NORMAL);
  }

  /* Enum field label & tip. */
  if (enum_tip.strinfo) {
    UI_tooltip_text_field_add(
        data, BLI_strdup(enum_tip.strinfo), nullptr, UI_TIP_STYLE_NORMAL, UI_TIP_LC_VALUE);
  }

  /* Operator shortcut. */
  if (op_keymap.strinfo) {
    UI_tooltip_text_field_add(data,
                              BLI_sprintfN(TIP_("Shortcut: %s"), op_keymap.strinfo),
                              nullptr,
                              UI_TIP_STYLE_NORMAL,
                              UI_TIP_LC_VALUE,
                              true);
  }

  /* Property context-toggle shortcut. */
  if (prop_keymap.strinfo) {
    UI_tooltip_text_field_add(data,
                              BLI_sprintfN(TIP_("Shortcut: %s"), prop_keymap.strinfo),
                              nullptr,
                              UI_TIP_STYLE_NORMAL,
                              UI_TIP_LC_VALUE,
                              true);
  }

  if (ELEM(but->type, UI_BTYPE_TEXT, UI_BTYPE_SEARCH_MENU)) {
    /* Better not show the value of a password. */
    if ((rnaprop && (RNA_property_subtype(rnaprop) == PROP_PASSWORD)) == 0) {
      /* Full string. */
      ui_but_string_get(but, buf, sizeof(buf));
      if (buf[0]) {
        UI_tooltip_text_field_add(data,
                                  BLI_sprintfN(TIP_("Value: %s"), buf),
                                  nullptr,
                                  UI_TIP_STYLE_NORMAL,
                                  UI_TIP_LC_VALUE,
                                  true);
      }
    }
  }

  if (rnaprop) {
    const int unit_type = UI_but_unit_type_get(but);

    if (unit_type == PROP_UNIT_ROTATION) {
      if (RNA_property_type(rnaprop) == PROP_FLOAT) {
        float value = RNA_property_array_check(rnaprop) ?
                          RNA_property_float_get_index(&but->rnapoin, rnaprop, but->rnaindex) :
                          RNA_property_float_get(&but->rnapoin, rnaprop);
        UI_tooltip_text_field_add(data,
                                  BLI_sprintfN(TIP_("Radians: %f"), value),
                                  nullptr,
                                  UI_TIP_STYLE_NORMAL,
                                  UI_TIP_LC_VALUE);
      }
    }

    if (but->flag & UI_BUT_DRIVEN) {
      if (ui_but_anim_expression_get(but, buf, sizeof(buf))) {
        UI_tooltip_text_field_add(data,
                                  BLI_sprintfN(TIP_("Expression: %s"), buf),
                                  nullptr,
                                  UI_TIP_STYLE_NORMAL,
                                  UI_TIP_LC_NORMAL);
      }
    }

    if (but->rnapoin.owner_id) {
      const ID *id = but->rnapoin.owner_id;
      if (ID_IS_LINKED(id)) {
        UI_tooltip_text_field_add(data,
                                  BLI_sprintfN(TIP_("Library: %s"), id->lib->filepath),
                                  nullptr,
                                  UI_TIP_STYLE_NORMAL,
                                  UI_TIP_LC_NORMAL);
      }
    }
  }
  else if (optype) {
    PointerRNA *opptr = extra_icon ? UI_but_extra_operator_icon_opptr_get(extra_icon) :
                                     /* Allocated when needed, the button owns it. */
                                     UI_but_operator_ptr_get(but);

    /* So the context is passed to field functions (some Python field functions use it). */
    WM_operator_properties_sanitize(opptr, false);

    char *str = ui_tooltip_text_python_from_op(C, optype, opptr);

    /* Operator info. */
    if (U.flag & USER_TOOLTIPS_PYTHON) {
      UI_tooltip_text_field_add(data,
                                BLI_sprintfN(TIP_("Python: %s"), str),
                                nullptr,
                                UI_TIP_STYLE_MONO,
                                UI_TIP_LC_PYTHON,
                                true);
    }

    MEM_freeN(str);
  }

  /* Button is disabled, we may be able to tell user why. */
  if ((but->flag & UI_BUT_DISABLED) || extra_icon) {
    const char *disabled_msg = nullptr;
    bool disabled_msg_free = false;

    /* If operator poll check failed, it can give pretty precise info why. */
    if (optype) {
      const wmOperatorCallContext opcontext = extra_icon ? extra_icon->optype_params->opcontext :
                                                           but->opcontext;
      wmOperatorCallParams call_params{};
      call_params.optype = optype;
      call_params.opcontext = opcontext;
      CTX_wm_operator_poll_msg_clear(C);
      ui_but_context_poll_operator_ex(C, but, &call_params);
      disabled_msg = CTX_wm_operator_poll_msg_get(C, &disabled_msg_free);
    }
    /* Alternatively, buttons can store some reasoning too. */
    else if (!extra_icon && but->disabled_info) {
      disabled_msg = TIP_(but->disabled_info);
    }

    if (disabled_msg && disabled_msg[0]) {
      UI_tooltip_text_field_add(data,
                                BLI_sprintfN(TIP_("Disabled: %s"), disabled_msg),
                                nullptr,
                                UI_TIP_STYLE_NORMAL,
                                UI_TIP_LC_ALERT);
    }
    if (disabled_msg_free) {
      MEM_freeN((void *)disabled_msg);
    }
  }

  if ((U.flag & USER_TOOLTIPS_PYTHON) && !optype && rna_struct.strinfo) {
    {
      UI_tooltip_text_field_add(
          data,
          (rna_prop.strinfo) ?
              BLI_sprintfN(TIP_("Python: %s.%s"), rna_struct.strinfo, rna_prop.strinfo) :
              BLI_sprintfN(TIP_("Python: %s"), rna_struct.strinfo),
          nullptr,
          UI_TIP_STYLE_MONO,
          UI_TIP_LC_PYTHON,
          true);
    }

    if (but->rnapoin.owner_id) {
      UI_tooltip_text_field_add(
          data,
          (rnaprop) ? RNA_path_full_property_py_ex(&but->rnapoin, rnaprop, but->rnaindex, true) :
                      RNA_path_full_struct_py(&but->rnapoin),
          nullptr,
          UI_TIP_STYLE_MONO,
          UI_TIP_LC_PYTHON);
    }
  }

  /* Free strinfo's... */
  if (but_label.strinfo) {
    MEM_freeN(but_label.strinfo);
  }
  if (but_tip_label.strinfo) {
    MEM_freeN(but_tip_label.strinfo);
  }
  if (but_tip.strinfo) {
    MEM_freeN(but_tip.strinfo);
  }
  if (enum_label.strinfo) {
    MEM_freeN(enum_label.strinfo);
  }
  if (enum_tip.strinfo) {
    MEM_freeN(enum_tip.strinfo);
  }
  if (op_keymap.strinfo) {
    MEM_freeN(op_keymap.strinfo);
  }
  if (prop_keymap.strinfo) {
    MEM_freeN(prop_keymap.strinfo);
  }
  if (rna_struct.strinfo) {
    MEM_freeN(rna_struct.strinfo);
  }
  if (rna_prop.strinfo) {
    MEM_freeN(rna_prop.strinfo);
  }

  if (data->fields_len == 0) {
    MEM_freeN(data);
    return nullptr;
  }
  return data;
}

static uiTooltipData *ui_tooltip_data_from_gizmo(bContext *C, wmGizmo *gz)
{
  uiTooltipData *data = MEM_cnew<uiTooltipData>(__func__);

  /* TODO(@ideasman42): a way for gizmos to have their own descriptions (low priority). */

  /* Operator Actions */
  {
    const bool use_drag = gz->drag_part != -1 && gz->highlight_part != gz->drag_part;
    struct GizmoOpActions {
      int part;
      const char *prefix;
    };
    GizmoOpActions gzop_actions[] = {
        {
            gz->highlight_part,
            use_drag ? CTX_TIP_(BLT_I18NCONTEXT_OPERATOR_DEFAULT, "Click") : nullptr,
        },
        {
            use_drag ? gz->drag_part : -1,
            use_drag ? CTX_TIP_(BLT_I18NCONTEXT_OPERATOR_DEFAULT, "Drag") : nullptr,
        },
    };

    for (int i = 0; i < ARRAY_SIZE(gzop_actions); i++) {
      wmGizmoOpElem *gzop = (gzop_actions[i].part != -1) ?
                                WM_gizmo_operator_get(gz, gzop_actions[i].part) :
                                nullptr;
      if (gzop != nullptr) {
        /* Description */
        std::string info = WM_operatortype_description_or_name(C, gzop->type, &gzop->ptr);

        if (!info.empty()) {
          UI_tooltip_text_field_add(
              data,
              gzop_actions[i].prefix ?
                  BLI_sprintfN("%s: %s", gzop_actions[i].prefix, info.c_str()) :
                  BLI_strdup(info.c_str()),
              nullptr,
              UI_TIP_STYLE_HEADER,
              UI_TIP_LC_VALUE,
              true);
        }

        /* Shortcut */
        {
          IDProperty *prop = static_cast<IDProperty *>(gzop->ptr.data);
          char buf[128];
          if (WM_key_event_operator_string(
                  C, gzop->type->idname, WM_OP_INVOKE_DEFAULT, prop, true, buf, ARRAY_SIZE(buf)))
          {
            UI_tooltip_text_field_add(data,
                                      BLI_sprintfN(TIP_("Shortcut: %s"), buf),
                                      nullptr,
                                      UI_TIP_STYLE_NORMAL,
                                      UI_TIP_LC_VALUE,
                                      true);
          }
        }
      }
    }
  }

  /* Property Actions */
  if (gz->type->target_property_defs_len) {
    wmGizmoProperty *gz_prop_array = WM_gizmo_target_property_array(gz);
    for (int i = 0; i < gz->type->target_property_defs_len; i++) {
      /* TODO(@ideasman42): function callback descriptions. */
      wmGizmoProperty *gz_prop = &gz_prop_array[i];
      if (gz_prop->prop != nullptr) {
        const char *info = RNA_property_ui_description(gz_prop->prop);
        if (info && info[0]) {
          UI_tooltip_text_field_add(
              data, BLI_strdup(info), nullptr, UI_TIP_STYLE_NORMAL, UI_TIP_LC_VALUE, true);
        }
      }
    }
  }

  if (data->fields_len == 0) {
    MEM_freeN(data);
    return nullptr;
  }
  return data;
}

static ARegion *ui_tooltip_create_with_data(bContext *C,
                                            uiTooltipData *data,
                                            const float init_position[2],
                                            const rcti *init_rect_overlap,
                                            const float aspect)
{
  const float pad_px = UI_TIP_PADDING;
  wmWindow *win = CTX_wm_window(C);
  const int winx = WM_window_pixels_x(win);
  const int winy = WM_window_pixels_y(win);
  const uiStyle *style = UI_style_get();
  rcti rect_i;
  int font_flag = 0;

  /* Create area region. */
  ARegion *region = ui_region_temp_add(CTX_wm_screen(C));

  static ARegionType type;
  memset(&type, 0, sizeof(ARegionType));
  type.draw = ui_tooltip_region_draw_cb;
  type.free = ui_tooltip_region_free_cb;
  type.regionid = RGN_TYPE_TEMPORARY;
  region->type = &type;

  /* Set font, get bounding-box. */
  data->fstyle = style->widget; /* copy struct */
  ui_fontscale(&data->fstyle.points, aspect);

  UI_fontstyle_set(&data->fstyle);

  data->wrap_width = min_ii(UI_TIP_MAXWIDTH * U.pixelsize / aspect, winx - (UI_TIP_PADDING * 2));

  font_flag |= BLF_WORD_WRAP;
  BLF_enable(data->fstyle.uifont_id, font_flag);
  BLF_enable(blf_mono_font, font_flag);
  BLF_wordwrap(data->fstyle.uifont_id, data->wrap_width);
  BLF_wordwrap(blf_mono_font, data->wrap_width);

  /* These defines tweaked depending on font. */
#define TIP_BORDER_X (16.0f / aspect)
#define TIP_BORDER_Y (6.0f / aspect)

  int h = BLF_height_max(data->fstyle.uifont_id);

  int i, fonth, fontw;
  for (i = 0, fontw = 0, fonth = 0; i < data->fields_len; i++) {
    uiTooltipField *field = &data->fields[i];
    ResultBLF info = {0};
    int w = 0;
    int x_pos = 0;
    int font_id;

    if (field->format.style == UI_TIP_STYLE_MONO) {
      BLF_size(blf_mono_font, data->fstyle.points * UI_SCALE_FAC);
      font_id = blf_mono_font;
    }
    else {
      font_id = data->fstyle.uifont_id;
    }

    if (field->text && field->text[0]) {
      w = BLF_width_ex(font_id, field->text, UI_TIP_STR_MAX, &info);
    }

    /* check for suffix (enum label) */
    if (field->text_suffix && field->text_suffix[0]) {
      x_pos = info.width;
      w = max_ii(w, x_pos + BLF_width(font_id, field->text_suffix, UI_TIP_STR_MAX));
    }

    fonth += h * info.lines;

    if (field->format.style == UI_TIP_STYLE_SPACER) {
      fonth += h * UI_TIP_SPACER;
    }

    if (field->format.style == UI_TIP_STYLE_IMAGE) {
      fonth += field->image_size[1];
      w = max_ii(w, field->image_size[0]);
    }

    fontw = max_ii(fontw, w);

    field->geom.lines = info.lines;
    field->geom.x_pos = x_pos;
  }

  // fontw *= aspect;

  BLF_disable(data->fstyle.uifont_id, font_flag);
  BLF_disable(blf_mono_font, font_flag);

  region->regiondata = data;

  data->toth = fonth;
  data->lineh = h;

  /* Compute position. */
  {
    rctf rect_fl;
    rect_fl.xmin = init_position[0] - TIP_BORDER_X;
    rect_fl.xmax = rect_fl.xmin + fontw + pad_px;
    rect_fl.ymax = init_position[1] - TIP_BORDER_Y;
    rect_fl.ymin = rect_fl.ymax - fonth - TIP_BORDER_Y;
    BLI_rcti_rctf_copy(&rect_i, &rect_fl);
  }

#undef TIP_BORDER_X
#undef TIP_BORDER_Y

  // #define USE_ALIGN_Y_CENTER

  /* Clamp to window bounds. */
  {
    /* Ensure at least 5 px above screen bounds.
     * #UI_UNIT_Y is just a guess to be above the menu item. */
    if (init_rect_overlap != nullptr) {
      const int pad = max_ff(1.0f, U.pixelsize) * 5;
      rcti init_rect;
      init_rect.xmin = init_rect_overlap->xmin - pad;
      init_rect.xmax = init_rect_overlap->xmax + pad;
      init_rect.ymin = init_rect_overlap->ymin - pad;
      init_rect.ymax = init_rect_overlap->ymax + pad;
      rcti rect_clamp;
      rect_clamp.xmin = 0;
      rect_clamp.xmax = winx;
      rect_clamp.ymin = 0;
      rect_clamp.ymax = winy;
      /* try right. */
      const int size_x = BLI_rcti_size_x(&rect_i);
      const int size_y = BLI_rcti_size_y(&rect_i);
      const int cent_overlap_x = BLI_rcti_cent_x(&init_rect);
#ifdef USE_ALIGN_Y_CENTER
      const int cent_overlap_y = BLI_rcti_cent_y(&init_rect);
#endif
      struct {
        rcti xpos;
        rcti xneg;
        rcti ypos;
        rcti yneg;
      } rect;

      { /* xpos */
        rcti r = rect_i;
        r.xmin = init_rect.xmax;
        r.xmax = r.xmin + size_x;
#ifdef USE_ALIGN_Y_CENTER
        r.ymin = cent_overlap_y - (size_y / 2);
        r.ymax = r.ymin + size_y;
#else
        r.ymin = init_rect.ymax - BLI_rcti_size_y(&rect_i);
        r.ymax = init_rect.ymax;
        r.ymin -= UI_POPUP_MARGIN;
        r.ymax -= UI_POPUP_MARGIN;
#endif
        rect.xpos = r;
      }
      { /* xneg */
        rcti r = rect_i;
        r.xmin = init_rect.xmin - size_x;
        r.xmax = r.xmin + size_x;
#ifdef USE_ALIGN_Y_CENTER
        r.ymin = cent_overlap_y - (size_y / 2);
        r.ymax = r.ymin + size_y;
#else
        r.ymin = init_rect.ymax - BLI_rcti_size_y(&rect_i);
        r.ymax = init_rect.ymax;
        r.ymin -= UI_POPUP_MARGIN;
        r.ymax -= UI_POPUP_MARGIN;
#endif
        rect.xneg = r;
      }
      { /* ypos */
        rcti r = rect_i;
        r.xmin = cent_overlap_x - (size_x / 2);
        r.xmax = r.xmin + size_x;
        r.ymin = init_rect.ymax;
        r.ymax = r.ymin + size_y;
        rect.ypos = r;
      }
      { /* yneg */
        rcti r = rect_i;
        r.xmin = cent_overlap_x - (size_x / 2);
        r.xmax = r.xmin + size_x;
        r.ymin = init_rect.ymin - size_y;
        r.ymax = r.ymin + size_y;
        rect.yneg = r;
      }

      bool found = false;
      for (int j = 0; j < 4; j++) {
        const rcti *r = (&rect.xpos) + j;
        if (BLI_rcti_inside_rcti(&rect_clamp, r)) {
          rect_i = *r;
          found = true;
          break;
        }
      }
      if (!found) {
        /* Fallback, we could pick the best fallback, for now just use xpos. */
        int offset_dummy[2];
        rect_i = rect.xpos;
        BLI_rcti_clamp(&rect_i, &rect_clamp, offset_dummy);
      }
    }
    else {
      const int pad = max_ff(1.0f, U.pixelsize) * 5;
      rcti rect_clamp;
      rect_clamp.xmin = pad;
      rect_clamp.xmax = winx - pad;
      rect_clamp.ymin = pad + (UI_UNIT_Y * 2);
      rect_clamp.ymax = winy - pad;
      int offset_dummy[2];
      BLI_rcti_clamp(&rect_i, &rect_clamp, offset_dummy);
    }
  }

#undef USE_ALIGN_Y_CENTER

  /* add padding */
  BLI_rcti_resize(&rect_i, BLI_rcti_size_x(&rect_i) + pad_px, BLI_rcti_size_y(&rect_i) + pad_px);

  /* widget rect, in region coords */
  {
    /* Compensate for margin offset, visually this corrects the position. */
    const int margin = UI_POPUP_MARGIN;
    if (init_rect_overlap != nullptr) {
      BLI_rcti_translate(&rect_i, margin, margin / 2);
    }

    data->bbox.xmin = margin;
    data->bbox.xmax = BLI_rcti_size_x(&rect_i) - margin;
    data->bbox.ymin = margin;
    data->bbox.ymax = BLI_rcti_size_y(&rect_i);

    /* region bigger for shadow */
    region->winrct.xmin = rect_i.xmin - margin;
    region->winrct.xmax = rect_i.xmax + margin;
    region->winrct.ymin = rect_i.ymin - margin;
    region->winrct.ymax = rect_i.ymax + margin;
  }

  /* Adds sub-window. */
  ED_region_floating_init(region);

  /* notify change and redraw */
  ED_region_tag_redraw(region);

  return region;
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name ToolTip Public API
 * \{ */

ARegion *UI_tooltip_create_from_button_or_extra_icon(
    bContext *C, ARegion *butregion, uiBut *but, uiButExtraOpIcon *extra_icon, bool is_label)
{
  wmWindow *win = CTX_wm_window(C);
  /* Aspect values that shrink text are likely unreadable. */
  const float aspect = min_ff(1.0f, but->block->aspect);
  float init_position[2];

  if (but->drawflag & UI_BUT_NO_TOOLTIP) {
    return nullptr;
  }
  uiTooltipData *data = nullptr;

  if (but->tip_custom_func) {
    data = (uiTooltipData *)MEM_callocN(sizeof(uiTooltipData), "uiTooltipData");
    but->tip_custom_func(C, data, but->tip_arg);
  }

  if (data == nullptr) {
    data = ui_tooltip_data_from_tool(C, but, is_label);
  }

  if (data == nullptr) {
    data = ui_tooltip_data_from_button_or_extra_icon(C, but, extra_icon, is_label);
  }

  if (data == nullptr) {
    data = ui_tooltip_data_from_button_or_extra_icon(C, but, nullptr, is_label);
  }

  if (data == nullptr) {
    return nullptr;
  }

  const bool is_no_overlap = UI_but_has_tooltip_label(but) || UI_but_is_tool(but);
  rcti init_rect;
  if (is_no_overlap) {
    rctf overlap_rect_fl;
    init_position[0] = BLI_rctf_cent_x(&but->rect);
    init_position[1] = BLI_rctf_cent_y(&but->rect);
    if (butregion) {
      ui_block_to_window_fl(butregion, but->block, &init_position[0], &init_position[1]);
      ui_block_to_window_rctf(butregion, but->block, &overlap_rect_fl, &but->rect);
    }
    else {
      overlap_rect_fl = but->rect;
    }
    BLI_rcti_rctf_copy_round(&init_rect, &overlap_rect_fl);
  }
  else {
    init_position[0] = BLI_rctf_cent_x(&but->rect);
    init_position[1] = but->rect.ymin;
    if (butregion) {
      ui_block_to_window_fl(butregion, but->block, &init_position[0], &init_position[1]);
      init_position[0] = win->eventstate->xy[0];
    }
    init_position[1] -= (UI_POPUP_MARGIN / 2);
  }

  ARegion *region = ui_tooltip_create_with_data(
      C, data, init_position, is_no_overlap ? &init_rect : nullptr, aspect);

  return region;
}

ARegion *UI_tooltip_create_from_button(bContext *C, ARegion *butregion, uiBut *but, bool is_label)
{
  return UI_tooltip_create_from_button_or_extra_icon(C, butregion, but, nullptr, is_label);
}

ARegion *UI_tooltip_create_from_gizmo(bContext *C, wmGizmo *gz)
{
  wmWindow *win = CTX_wm_window(C);
  const float aspect = 1.0f;
  float init_position[2] = {float(win->eventstate->xy[0]), float(win->eventstate->xy[1])};

  uiTooltipData *data = ui_tooltip_data_from_gizmo(C, gz);
  if (data == nullptr) {
    return nullptr;
  }

  /* TODO(@harley): Julian preferred that the gizmo callback return the 3D bounding box
   * which we then project to 2D here. Would make a nice improvement. */
  if (gz->type->screen_bounds_get) {
    rcti bounds;
    if (gz->type->screen_bounds_get(C, gz, &bounds)) {
      init_position[0] = bounds.xmin;
      init_position[1] = bounds.ymin;
    }
  }

  return ui_tooltip_create_with_data(C, data, init_position, nullptr, aspect);
}

static uiTooltipData *ui_tooltip_data_from_search_item_tooltip_data(
    const uiSearchItemTooltipData *item_tooltip_data)
{
  uiTooltipData *data = MEM_cnew<uiTooltipData>(__func__);

  if (item_tooltip_data->description[0]) {
    UI_tooltip_text_field_add(data,
                              BLI_strdup(item_tooltip_data->description),
                              nullptr,
                              UI_TIP_STYLE_HEADER,
                              UI_TIP_LC_NORMAL,
                              true);
  }

  if (item_tooltip_data->name && item_tooltip_data->name[0]) {
    UI_tooltip_text_field_add(data,
                              BLI_strdup(item_tooltip_data->name),
                              nullptr,
                              UI_TIP_STYLE_NORMAL,
                              UI_TIP_LC_VALUE,
                              true);
  }
  if (item_tooltip_data->hint[0]) {
    UI_tooltip_text_field_add(data,
                              BLI_strdup(item_tooltip_data->hint),
                              nullptr,
                              UI_TIP_STYLE_NORMAL,
                              UI_TIP_LC_NORMAL,
                              true);
  }

  if (data->fields_len == 0) {
    MEM_freeN(data);
    return nullptr;
  }
  return data;
}

ARegion *UI_tooltip_create_from_search_item_generic(
    bContext *C,
    const ARegion *searchbox_region,
    const rcti *item_rect,
    const uiSearchItemTooltipData *item_tooltip_data)
{
  uiTooltipData *data = ui_tooltip_data_from_search_item_tooltip_data(item_tooltip_data);
  if (data == nullptr) {
    return nullptr;
  }

  const float aspect = 1.0f;
  const wmWindow *win = CTX_wm_window(C);
  float init_position[2];
  init_position[0] = win->eventstate->xy[0];
  init_position[1] = item_rect->ymin + searchbox_region->winrct.ymin - (UI_POPUP_MARGIN / 2);

  return ui_tooltip_create_with_data(C, data, init_position, nullptr, aspect);
}

void UI_tooltip_free(bContext *C, bScreen *screen, ARegion *region)
{
  ui_region_temp_remove(C, screen, region);
}

/** \} */

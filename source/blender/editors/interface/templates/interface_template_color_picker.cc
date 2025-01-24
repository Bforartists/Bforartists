/* SPDX-FileCopyrightText: 2024 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup edinterface
 */

#include "BLI_math_vector.h"
#include "BLI_string_ref.hh"

#include "BLT_translation.hh"

#include "DNA_brush_types.h"

#include "RNA_access.hh"
#include "RNA_prototypes.hh"

#include "UI_interface.hh"
#include "interface_intern.hh"

using blender::StringRefNull;

#define WHEEL_SIZE (5 * U.widget_unit)

void uiTemplateColorPicker(uiLayout *layout,
                           PointerRNA *ptr,
                           const StringRefNull propname,
                           bool value_slider,
                           bool lock,
                           bool lock_luminosity,
                           bool cubic)
{
  PropertyRNA *prop = RNA_struct_find_property(ptr, propname.c_str());
  uiBlock *block = uiLayoutGetBlock(layout);
  ColorPicker *cpicker = ui_block_colorpicker_create(block);

  if (!prop) {
    RNA_warning("property not found: %s.%s", RNA_struct_identifier(ptr->type), propname.c_str());
    return;
  }

  float softmin, softmax, step, precision;
  RNA_property_float_ui_range(ptr, prop, &softmin, &softmax, &step, &precision);

  uiLayout *col = uiLayoutColumn(layout, true);
  uiLayout *row = uiLayoutRow(col, true);

  uiBut *but = nullptr;
  uiButHSVCube *hsv_but;
  switch (U.color_picker_type) {
    case USER_CP_SQUARE_SV:
    case USER_CP_SQUARE_HS:
    case USER_CP_SQUARE_HV:
      hsv_but = (uiButHSVCube *)uiDefButR_prop(block,
                                               UI_BTYPE_HSVCUBE,
                                               0,
                                               "",
                                               0,
                                               0,
                                               WHEEL_SIZE,
                                               WHEEL_SIZE,
                                               ptr,
                                               prop,
                                               -1,
                                               0.0,
                                               0.0,
                                               "");
      switch (U.color_picker_type) {
        case USER_CP_SQUARE_SV:
          hsv_but->gradient_type = UI_GRAD_SV;
          break;
        case USER_CP_SQUARE_HS:
          hsv_but->gradient_type = UI_GRAD_HS;
          break;
        case USER_CP_SQUARE_HV:
          hsv_but->gradient_type = UI_GRAD_HV;
          break;
      }
      but = hsv_but;
      break;

      /* user default */
    case USER_CP_CIRCLE_HSV:
    case USER_CP_CIRCLE_HSL:
    default:
      but = uiDefButR_prop(block,
                           UI_BTYPE_HSVCIRCLE,
                           0,
                           "",
                           0,
                           0,
                           WHEEL_SIZE,
                           WHEEL_SIZE,
                           ptr,
                           prop,
                           -1,
                           0.0,
                           0.0,
                           "");
      break;
  }

  but->custom_data = cpicker;

  cpicker->use_color_lock = lock;
  cpicker->use_color_cubic = cubic;
  cpicker->use_luminosity_lock = lock_luminosity;

  if (lock_luminosity) {
    float color[4]; /* in case of alpha */
    RNA_property_float_get_array(ptr, prop, color);
    cpicker->luminosity_lock_value = len_v3(color);
  }

  if (value_slider) {
    switch (U.color_picker_type) {
      case USER_CP_CIRCLE_HSL:
        uiItemS(row);
        hsv_but = (uiButHSVCube *)uiDefButR_prop(block,
                                                 UI_BTYPE_HSVCUBE,
                                                 0,
                                                 "",
                                                 WHEEL_SIZE + 6,
                                                 0,
                                                 14 * UI_SCALE_FAC,
                                                 WHEEL_SIZE,
                                                 ptr,
                                                 prop,
                                                 -1,
                                                 softmin,
                                                 softmax,
                                                 "");
        hsv_but->gradient_type = UI_GRAD_L_ALT;
        break;
      case USER_CP_SQUARE_SV:
        uiItemS(col);
        hsv_but = (uiButHSVCube *)uiDefButR_prop(block,
                                                 UI_BTYPE_HSVCUBE,
                                                 0,
                                                 "",
                                                 0,
                                                 4,
                                                 WHEEL_SIZE,
                                                 18 * UI_SCALE_FAC,
                                                 ptr,
                                                 prop,
                                                 -1,
                                                 softmin,
                                                 softmax,
                                                 "");
        hsv_but->gradient_type = eButGradientType(UI_GRAD_SV + 3);
        break;
      case USER_CP_SQUARE_HS:
        uiItemS(col);
        hsv_but = (uiButHSVCube *)uiDefButR_prop(block,
                                                 UI_BTYPE_HSVCUBE,
                                                 0,
                                                 "",
                                                 0,
                                                 4,
                                                 WHEEL_SIZE,
                                                 18 * UI_SCALE_FAC,
                                                 ptr,
                                                 prop,
                                                 -1,
                                                 softmin,
                                                 softmax,
                                                 "");
        hsv_but->gradient_type = eButGradientType(UI_GRAD_HS + 3);
        break;
      case USER_CP_SQUARE_HV:
        uiItemS(col);
        hsv_but = (uiButHSVCube *)uiDefButR_prop(block,
                                                 UI_BTYPE_HSVCUBE,
                                                 0,
                                                 "",
                                                 0,
                                                 4,
                                                 WHEEL_SIZE,
                                                 18 * UI_SCALE_FAC,
                                                 ptr,
                                                 prop,
                                                 -1,
                                                 softmin,
                                                 softmax,
                                                 "");
        hsv_but->gradient_type = eButGradientType(UI_GRAD_HV + 3);
        break;

        /* user default */
      case USER_CP_CIRCLE_HSV:
      default:
        uiItemS(row);
        hsv_but = (uiButHSVCube *)uiDefButR_prop(block,
                                                 UI_BTYPE_HSVCUBE,
                                                 0,
                                                 "",
                                                 WHEEL_SIZE + 6,
                                                 0,
                                                 14 * UI_SCALE_FAC,
                                                 WHEEL_SIZE,
                                                 ptr,
                                                 prop,
                                                 -1,
                                                 softmin,
                                                 softmax,
                                                 "");
        hsv_but->gradient_type = UI_GRAD_V_ALT;
        break;
    }

    hsv_but->custom_data = cpicker;
  }
}

static void ui_template_palette_menu(bContext * /*C*/, uiLayout *layout, void * /*but_p*/)
{
  uiLayout *row;

  uiItemL(layout, IFACE_("Sort By:"), ICON_NONE);
  row = uiLayoutRow(layout, false);
  uiItemEnumO_value(row, IFACE_("Hue"), ICON_NONE, "PALETTE_OT_sort", "type", 1);
  row = uiLayoutRow(layout, false);
  uiItemEnumO_value(row, IFACE_("Saturation"), ICON_NONE, "PALETTE_OT_sort", "type", 2);
  row = uiLayoutRow(layout, false);
  uiItemEnumO_value(row, IFACE_("Value"), ICON_NONE, "PALETTE_OT_sort", "type", 3);
  row = uiLayoutRow(layout, false);
  uiItemEnumO_value(row, IFACE_("Luminance"), ICON_NONE, "PALETTE_OT_sort", "type", 4);
}

void uiTemplatePalette(uiLayout *layout,
                       PointerRNA *ptr,
                       const StringRefNull propname,
                       bool /*colors*/)
{
  PropertyRNA *prop = RNA_struct_find_property(ptr, propname.c_str());
  uiBut *but = nullptr;

  const int cols_per_row = std::max(uiLayoutGetWidth(layout) / UI_UNIT_X, 1);

  if (!prop) {
    RNA_warning("property not found: %s.%s", RNA_struct_identifier(ptr->type), propname.c_str());
    return;
  }

  const PointerRNA cptr = RNA_property_pointer_get(ptr, prop);
  if (!cptr.data || !RNA_struct_is_a(cptr.type, &RNA_Palette)) {
    return;
  }

  uiBlock *block = uiLayoutGetBlock(layout);

  Palette *palette = static_cast<Palette *>(cptr.data);

  uiLayout *col = uiLayoutColumn(layout, true);
  uiLayoutRow(col, true);
  uiDefIconButO(block,
                UI_BTYPE_BUT,
                "PALETTE_OT_color_add",
                WM_OP_INVOKE_DEFAULT,
                ICON_ADD,
                0,
                0,
                UI_UNIT_X,
                UI_UNIT_Y,
                nullptr);
  uiDefIconButO(block,
                UI_BTYPE_BUT,
                "PALETTE_OT_color_delete",
                WM_OP_INVOKE_DEFAULT,
                ICON_REMOVE,
                0,
                0,
                UI_UNIT_X,
                UI_UNIT_Y,
                nullptr);
  if (palette->colors.first != nullptr) {
    but = uiDefIconButO(block,
                        UI_BTYPE_BUT,
                        "PALETTE_OT_color_move",
                        WM_OP_INVOKE_DEFAULT,
                        ICON_TRIA_UP,
                        0,
                        0,
                        UI_UNIT_X,
                        UI_UNIT_Y,
                        nullptr);
    UI_but_operator_ptr_ensure(but);
    RNA_enum_set(but->opptr, "type", -1);

    but = uiDefIconButO(block,
                        UI_BTYPE_BUT,
                        "PALETTE_OT_color_move",
                        WM_OP_INVOKE_DEFAULT,
                        ICON_TRIA_DOWN,
                        0,
                        0,
                        UI_UNIT_X,
                        UI_UNIT_Y,
                        nullptr);
    UI_but_operator_ptr_ensure(but);
    RNA_enum_set(but->opptr, "type", 1);

    /* Menu. */
    uiDefIconMenuBut(
        block, ui_template_palette_menu, nullptr, ICON_SORTSIZE, 0, 0, UI_UNIT_X, UI_UNIT_Y, "");
  }

  col = uiLayoutColumn(layout, true);
  uiLayoutRow(col, true);

  int row_cols = 0, col_id = 0;
  LISTBASE_FOREACH (PaletteColor *, color, &palette->colors) {
    if (row_cols >= cols_per_row) {
      uiLayoutRow(col, true);
      row_cols = 0;
    }

    PointerRNA color_ptr = RNA_pointer_create_discrete(&palette->id, &RNA_PaletteColor, color);
    uiButColor *color_but = (uiButColor *)uiDefButR(block,
                                                    UI_BTYPE_COLOR,
                                                    0,
                                                    "",
                                                    0,
                                                    0,
                                                    UI_UNIT_X,
                                                    UI_UNIT_Y,
                                                    &color_ptr,
                                                    "color",
                                                    -1,
                                                    0.0,
                                                    1.0,
                                                    "");
    color_but->is_pallete_color = true;
    color_but->palette_color_index = col_id;
    row_cols++;
    col_id++;
  }
}

void uiTemplateCryptoPicker(uiLayout *layout,
                            PointerRNA *ptr,
                            const StringRefNull propname,
                            int icon)
{
  PropertyRNA *prop = RNA_struct_find_property(ptr, propname.c_str());

  if (!prop) {
    RNA_warning("property not found: %s.%s", RNA_struct_identifier(ptr->type), propname.c_str());
    return;
  }

  uiBlock *block = uiLayoutGetBlock(layout);

  uiBut *but = uiDefIconButO(block,
                             UI_BTYPE_BUT,
                             "UI_OT_eyedropper_color",
                             WM_OP_INVOKE_DEFAULT,
                             icon,
                             0,
                             0,
                             UI_UNIT_X,
                             UI_UNIT_Y,
                             RNA_property_ui_description(prop));
  but->rnapoin = *ptr;
  but->rnaprop = prop;
  but->rnaindex = -1;
}

/*
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software Foundation,
 * Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
 *
 * The Original Code is Copyright (C) 2007 Blender Foundation.
 * All rights reserved.
 */

/** \file
 * \ingroup wm
 *
 * Generic re-usable property definitions and accessors for operators to share.
 * (`WM_operator_properties_*` functions).
 */

#include "DNA_space_types.h"

#include "BLI_math_base.h"
#include "BLI_rect.h"

#include "UI_resources.h"

#include "RNA_access.h"
#include "RNA_define.h"
#include "RNA_enum_types.h"

#include "ED_select_utils.h"

#include "WM_api.h"
#include "WM_types.h"

void WM_operator_properties_confirm_or_exec(wmOperatorType *ot)
{
  PropertyRNA *prop;

  prop = RNA_def_boolean(ot->srna, "confirm", true, "Confirm", "Prompt for confirmation");
  RNA_def_property_flag(prop, PROP_HIDDEN | PROP_SKIP_SAVE);
}

/* default properties for fileselect */
void WM_operator_properties_filesel(wmOperatorType *ot,
                                    int filter,
                                    short type,
                                    short action,
                                    short flag,
                                    short display,
                                    short sort)
{
  PropertyRNA *prop;

  static const EnumPropertyItem file_display_items[] = {
      {FILE_DEFAULTDISPLAY,
       "DEFAULT",
       0,
       "Default",
       "Automatically determine display type for files"},
      {FILE_VERTICALDISPLAY,
       "LIST_VERTICAL",
       ICON_SHORTDISPLAY, /* Name of deprecated short list */
       "Short List",
       "Display files as short list"},
      {FILE_HORIZONTALDISPLAY,
       "LIST_HORIZONTAL",
       ICON_LONGDISPLAY, /* Name of deprecated long list */
       "Long List",
       "Display files as a detailed list"},
      {FILE_IMGDISPLAY, "THUMBNAIL", ICON_IMGDISPLAY, "Thumbnails", "Display files as thumbnails"},
      {0, NULL, 0, NULL, NULL},
  };

  if (flag & WM_FILESEL_FILEPATH) {
    RNA_def_string_file_path(ot->srna, "filepath", NULL, FILE_MAX, "File Path", "Path to file");
  }

  if (flag & WM_FILESEL_DIRECTORY) {
    RNA_def_string_dir_path(
        ot->srna, "directory", NULL, FILE_MAX, "Directory", "Directory of the file");
  }

  if (flag & WM_FILESEL_FILENAME) {
    RNA_def_string_file_name(
        ot->srna, "filename", NULL, FILE_MAX, "File Name", "Name of the file");
  }

  if (flag & WM_FILESEL_FILES) {
    prop = RNA_def_collection_runtime(
        ot->srna, "files", &RNA_OperatorFileListElement, "Files", "");
    RNA_def_property_flag(prop, PROP_HIDDEN | PROP_SKIP_SAVE);
  }

  if ((flag & WM_FILESEL_SHOW_PROPS) == 0) {
    prop = RNA_def_boolean(ot->srna,
                           "hide_props_region",
                           true,
                           "Hide Operator Properties",
                           "Collapse the region displaying the operator settings");
    RNA_def_property_flag(prop, PROP_HIDDEN | PROP_SKIP_SAVE);
  }

  if (action == FILE_SAVE) {
    /* note, this is only used to check if we should highlight the filename area red when the
     * filepath is an existing file. */
    prop = RNA_def_boolean(ot->srna,
                           "check_existing",
                           true,
                           "Check Existing",
                           "Check and warn on overwriting existing files");
    RNA_def_property_flag(prop, PROP_HIDDEN | PROP_SKIP_SAVE);
  }

  prop = RNA_def_boolean(
      ot->srna, "filter_blender", (filter & FILE_TYPE_BLENDER) != 0, "Filter .blend files", "");
  RNA_def_property_flag(prop, PROP_HIDDEN | PROP_SKIP_SAVE);
  prop = RNA_def_boolean(ot->srna,
                         "filter_backup",
                         (filter & FILE_TYPE_BLENDER_BACKUP) != 0,
                         "Filter .blend files",
                         "");
  RNA_def_property_flag(prop, PROP_HIDDEN | PROP_SKIP_SAVE);
  prop = RNA_def_boolean(
      ot->srna, "filter_image", (filter & FILE_TYPE_IMAGE) != 0, "Filter image files", "");
  RNA_def_property_flag(prop, PROP_HIDDEN | PROP_SKIP_SAVE);
  prop = RNA_def_boolean(
      ot->srna, "filter_movie", (filter & FILE_TYPE_MOVIE) != 0, "Filter movie files", "");
  RNA_def_property_flag(prop, PROP_HIDDEN | PROP_SKIP_SAVE);
  prop = RNA_def_boolean(
      ot->srna, "filter_python", (filter & FILE_TYPE_PYSCRIPT) != 0, "Filter python files", "");
  RNA_def_property_flag(prop, PROP_HIDDEN | PROP_SKIP_SAVE);
  prop = RNA_def_boolean(
      ot->srna, "filter_font", (filter & FILE_TYPE_FTFONT) != 0, "Filter font files", "");
  RNA_def_property_flag(prop, PROP_HIDDEN | PROP_SKIP_SAVE);
  prop = RNA_def_boolean(
      ot->srna, "filter_sound", (filter & FILE_TYPE_SOUND) != 0, "Filter sound files", "");
  RNA_def_property_flag(prop, PROP_HIDDEN | PROP_SKIP_SAVE);
  prop = RNA_def_boolean(
      ot->srna, "filter_text", (filter & FILE_TYPE_TEXT) != 0, "Filter text files", "");
  RNA_def_property_flag(prop, PROP_HIDDEN | PROP_SKIP_SAVE);
  prop = RNA_def_boolean(
      ot->srna, "filter_archive", (filter & FILE_TYPE_ARCHIVE) != 0, "Filter archive files", "");
  RNA_def_property_flag(prop, PROP_HIDDEN | PROP_SKIP_SAVE);
  prop = RNA_def_boolean(
      ot->srna, "filter_btx", (filter & FILE_TYPE_BTX) != 0, "Filter btx files", "");
  RNA_def_property_flag(prop, PROP_HIDDEN | PROP_SKIP_SAVE);
  prop = RNA_def_boolean(
      ot->srna, "filter_collada", (filter & FILE_TYPE_COLLADA) != 0, "Filter COLLADA files", "");
  RNA_def_property_flag(prop, PROP_HIDDEN | PROP_SKIP_SAVE);
  prop = RNA_def_boolean(
      ot->srna, "filter_alembic", (filter & FILE_TYPE_ALEMBIC) != 0, "Filter Alembic files", "");
  RNA_def_property_flag(prop, PROP_HIDDEN | PROP_SKIP_SAVE);
  prop = RNA_def_boolean(
      ot->srna, "filter_usd", (filter & FILE_TYPE_USD) != 0, "Filter USD files", "");
  RNA_def_property_flag(prop, PROP_HIDDEN | PROP_SKIP_SAVE);
  prop = RNA_def_boolean(ot->srna,
                         "filter_volume",
                         (filter & FILE_TYPE_VOLUME) != 0,
                         "Filter OpenVDB volume files",
                         "");
  RNA_def_property_flag(prop, PROP_HIDDEN | PROP_SKIP_SAVE);
  prop = RNA_def_boolean(
      ot->srna, "filter_folder", (filter & FILE_TYPE_FOLDER) != 0, "Filter folders", "");
  RNA_def_property_flag(prop, PROP_HIDDEN | PROP_SKIP_SAVE);
  prop = RNA_def_boolean(
      ot->srna, "filter_blenlib", (filter & FILE_TYPE_BLENDERLIB) != 0, "Filter Blender IDs", "");
  RNA_def_property_flag(prop, PROP_HIDDEN | PROP_SKIP_SAVE);

  prop = RNA_def_int(
      ot->srna,
      "filemode",
      type,
      FILE_LOADLIB,
      FILE_SPECIAL,
      "File Browser Mode",
      "The setting for the file browser mode to load a .blend file, a library or a special file",
      FILE_LOADLIB,
      FILE_SPECIAL);
  RNA_def_property_flag(prop, PROP_HIDDEN | PROP_SKIP_SAVE);

  if (flag & WM_FILESEL_RELPATH) {
    RNA_def_boolean(ot->srna,
                    "relative_path",
                    true,
                    "Relative Path",
                    "Select the file relative to the blend file");
  }

  if ((filter & FILE_TYPE_IMAGE) || (filter & FILE_TYPE_MOVIE)) {
    prop = RNA_def_boolean(ot->srna, "show_multiview", 0, "Enable Multi-View", "");
    RNA_def_property_flag(prop, PROP_HIDDEN | PROP_SKIP_SAVE);
    prop = RNA_def_boolean(ot->srna, "use_multiview", 0, "Use Multi-View", "");
    RNA_def_property_flag(prop, PROP_HIDDEN | PROP_SKIP_SAVE);
  }

  prop = RNA_def_enum(ot->srna, "display_type", file_display_items, display, "Display Type", "");
  RNA_def_property_flag(prop, PROP_HIDDEN | PROP_SKIP_SAVE);

  prop = RNA_def_enum(
      ot->srna, "sort_method", rna_enum_file_sort_items, sort, "File sorting mode", "");
  RNA_def_property_flag(prop, PROP_HIDDEN | PROP_SKIP_SAVE);
}

static void wm_operator_properties_select_action_ex(wmOperatorType *ot,
                                                    int default_action,
                                                    const EnumPropertyItem *select_actions,
                                                    bool hide_gui)
{
  PropertyRNA *prop;
  prop = RNA_def_enum(
      ot->srna, "action", select_actions, default_action, "Action", "Selection action to execute");

  if (hide_gui) {
    RNA_def_property_flag(prop, PROP_HIDDEN | PROP_SKIP_SAVE);
  }
}

void WM_operator_properties_select_action(wmOperatorType *ot, int default_action, bool hide_gui)
{
  static const EnumPropertyItem select_actions[] = {
      {SEL_TOGGLE, "TOGGLE", 0, "Toggle", "Toggle selection for all elements"},
      {SEL_SELECT, "SELECT", 0, "Select", "Select all elements"},
      {SEL_DESELECT, "DESELECT", 0, "Deselect", "Deselect all elements"},
      {SEL_INVERT, "INVERT", 0, "Invert", "Invert selection of all elements"},
      {0, NULL, 0, NULL, NULL},
  };

  wm_operator_properties_select_action_ex(ot, default_action, select_actions, hide_gui);
}

/**
 * only SELECT/DESELECT
 */
void WM_operator_properties_select_action_simple(wmOperatorType *ot,
                                                 int default_action,
                                                 bool hide_gui)
{
  static const EnumPropertyItem select_actions[] = {
      {SEL_SELECT, "SELECT", 0, "Select", "Select all elements"},
      {SEL_DESELECT, "DESELECT", 0, "Deselect", "Deselect all elements"},
      {0, NULL, 0, NULL, NULL},
  };

  wm_operator_properties_select_action_ex(ot, default_action, select_actions, hide_gui);
}

/**
 * Use for all select random operators.
 * Adds properties: percent, seed, action.
 */
void WM_operator_properties_select_random(wmOperatorType *ot)
{
  RNA_def_float_percentage(ot->srna,
                           "percent",
                           50.f,
                           0.0f,
                           100.0f,
                           "Percent",
                           "Percentage of objects to select randomly",
                           0.f,
                           100.0f);
  RNA_def_int(ot->srna,
              "seed",
              0,
              0,
              INT_MAX,
              "Random Seed",
              "Seed for the random number generator",
              0,
              255);

  WM_operator_properties_select_action_simple(ot, SEL_SELECT, false);
}

int WM_operator_properties_select_random_seed_increment_get(wmOperator *op)
{
  PropertyRNA *prop = RNA_struct_find_property(op->ptr, "seed");
  int value = RNA_property_int_get(op->ptr, prop);

  if (op->flag & OP_IS_INVOKE) {
    if (!RNA_property_is_set(op->ptr, prop)) {
      value += 1;
      RNA_property_int_set(op->ptr, prop, value);
    }
  }
  return value;
}

void WM_operator_properties_select_all(wmOperatorType *ot)
{
  WM_operator_properties_select_action(ot, SEL_TOGGLE, true);
}

void WM_operator_properties_border(wmOperatorType *ot)
{
  PropertyRNA *prop;

  prop = RNA_def_int(ot->srna, "xmin", 0, INT_MIN, INT_MAX, "X Min", "", INT_MIN, INT_MAX);
  RNA_def_property_flag(prop, PROP_HIDDEN | PROP_SKIP_SAVE);
  prop = RNA_def_int(ot->srna, "xmax", 0, INT_MIN, INT_MAX, "X Max", "", INT_MIN, INT_MAX);
  RNA_def_property_flag(prop, PROP_HIDDEN | PROP_SKIP_SAVE);
  prop = RNA_def_int(ot->srna, "ymin", 0, INT_MIN, INT_MAX, "Y Min", "", INT_MIN, INT_MAX);
  RNA_def_property_flag(prop, PROP_HIDDEN | PROP_SKIP_SAVE);
  prop = RNA_def_int(ot->srna, "ymax", 0, INT_MIN, INT_MAX, "Y Max", "", INT_MIN, INT_MAX);
  RNA_def_property_flag(prop, PROP_HIDDEN | PROP_SKIP_SAVE);

  prop = RNA_def_boolean(ot->srna, "wait_for_input", true, "Wait for Input", "");
  RNA_def_property_flag(prop, PROP_HIDDEN | PROP_SKIP_SAVE);
}

void WM_operator_properties_border_to_rcti(struct wmOperator *op, rcti *rect)
{
  rect->xmin = RNA_int_get(op->ptr, "xmin");
  rect->ymin = RNA_int_get(op->ptr, "ymin");
  rect->xmax = RNA_int_get(op->ptr, "xmax");
  rect->ymax = RNA_int_get(op->ptr, "ymax");
}

void WM_operator_properties_border_to_rctf(struct wmOperator *op, rctf *rect)
{
  rcti rect_i;
  WM_operator_properties_border_to_rcti(op, &rect_i);
  BLI_rctf_rcti_copy(rect, &rect_i);
}

/**
 * Use with #WM_gesture_box_invoke
 */
void WM_operator_properties_gesture_box_ex(wmOperatorType *ot, bool deselect, bool extend)
{
  PropertyRNA *prop;

  WM_operator_properties_border(ot);

  if (deselect) {
    prop = RNA_def_boolean(
        ot->srna, "deselect", false, "Deselect", "Deselect rather than select items");
    RNA_def_property_flag(prop, PROP_SKIP_SAVE);
  }
  if (extend) {
    prop = RNA_def_boolean(ot->srna,
                           "extend",
                           true,
                           "Extend",
                           "Extend selection instead of deselecting everything first");
    RNA_def_property_flag(prop, PROP_SKIP_SAVE);
  }
}

/**
 * Disable using cursor position,
 * use when view operators are initialized from buttons.
 */
void WM_operator_properties_use_cursor_init(wmOperatorType *ot)
{
  PropertyRNA *prop = RNA_def_boolean(ot->srna,
                                      "use_cursor_init",
                                      true,
                                      "Use Mouse Position",
                                      "Allow the initial mouse position to be used");
  RNA_def_property_flag(prop, PROP_SKIP_SAVE | PROP_HIDDEN);
}

void WM_operator_properties_gesture_box_select(wmOperatorType *ot)
{
  WM_operator_properties_gesture_box_ex(ot, true, true);
}
void WM_operator_properties_gesture_box(wmOperatorType *ot)
{
  WM_operator_properties_gesture_box_ex(ot, false, false);
}

void WM_operator_properties_select_operation(wmOperatorType *ot)
{
  static const EnumPropertyItem select_mode_items[] = {
      {SEL_OP_SET, "SET", ICON_SELECT_SET, "Set", "Set a new selection"},
      {SEL_OP_ADD, "ADD", ICON_SELECT_EXTEND, "Extend", "Extend existing selection"},
      {SEL_OP_SUB, "SUB", ICON_SELECT_SUBTRACT, "Subtract", "Subtract existing selection"},
      {SEL_OP_XOR, "XOR", ICON_SELECT_DIFFERENCE, "Difference", "Inverts existing selection"},
      {SEL_OP_AND, "AND", ICON_SELECT_INTERSECT, "Intersect", "Intersect existing selection"},
      {0, NULL, 0, NULL, NULL},
  };
  PropertyRNA *prop = RNA_def_enum(ot->srna, "mode", select_mode_items, SEL_OP_SET, "Mode", "");
  RNA_def_property_flag(prop, PROP_SKIP_SAVE);
}

/* Some tools don't support XOR/AND. */
void WM_operator_properties_select_operation_simple(wmOperatorType *ot)
{
  static const EnumPropertyItem select_mode_items[] = {
      {SEL_OP_SET, "SET", ICON_SELECT_SET, "Set", "Set a new selection"},
      {SEL_OP_ADD, "ADD", ICON_SELECT_EXTEND, "Extend", "Extend existing selection"},
      {SEL_OP_SUB, "SUB", ICON_SELECT_SUBTRACT, "Subtract", "Subtract existing selection"},
      {0, NULL, 0, NULL, NULL},
  };
  PropertyRNA *prop = RNA_def_enum(ot->srna, "mode", select_mode_items, SEL_OP_SET, "Mode", "");
  RNA_def_property_flag(prop, PROP_SKIP_SAVE);
}

void WM_operator_properties_select_walk_direction(wmOperatorType *ot)
{
  static const EnumPropertyItem direction_items[] = {
      {UI_SELECT_WALK_UP, "UP", 0, "Prev", ""},
      {UI_SELECT_WALK_DOWN, "DOWN", 0, "Next", ""},
      {UI_SELECT_WALK_LEFT, "LEFT", 0, "Left", ""},
      {UI_SELECT_WALK_RIGHT, "RIGHT", 0, "Right", ""},
      {0, NULL, 0, NULL, NULL},
  };
  PropertyRNA *prop;
  prop = RNA_def_enum(ot->srna,
                      "direction",
                      direction_items,
                      0,
                      "Walk Direction",
                      "Select/Deselect element in this direction");
  RNA_def_property_flag(prop, PROP_SKIP_SAVE);
}

/**
 * Selecting and tweaking items are overlapping operations. Getting both to work without conflicts
 * requires special care. See
 * https://wiki.blender.org/wiki/Human_Interface_Guidelines/Selection#Select-tweaking for the
 * desired behavior.
 *
 * For default click selection (with no modifier keys held), the select operators can do the
 * following:
 * - On a mouse press on an unselected item, change selection and finish immediately after.
 *   This sends an undo push and allows transform to take over should a tweak event be caught now.
 * - On a mouse press on a selected item, don't change selection state, but start modal execution
 *   of the operator. Idea is that we wait with deselecting other items until we know that the
 *   intention wasn't to tweak (mouse press+drag) all selected items.
 * - If a tweak is recognized before the release event happens, cancel the operator, so that
 *   transform can take over and no undo-push is sent.
 * - If the release event occurs rather than a tweak one, deselect all items but the one under the
 *   cursor, and finish the modal operator.
 *
 * This utility, together with #WM_generic_select_invoke() and #WM_generic_select_modal() should
 * help getting the wanted behavior to work. Most generic logic should be handled in these, so that
 * the select operators only have to care for the case dependent handling.
 *
 * Every select operator has slightly different requirements, e.g. VSE strip selection also needs
 * to account for handle selection. This should be the baseline behavior though.
 */
void WM_operator_properties_generic_select(wmOperatorType *ot)
{
  /* On the initial mouse press, this is set by #WM_generic_select_modal() to let the select
   * operator exec callback know that it should not __yet__ deselect other items when clicking on
   * an already selected one. Instead should make sure the operator executes modal then (see
   * #WM_generic_select_modal()), so that the exec callback can be called a second time on the
   * mouse release event to do this part. */
  PropertyRNA *prop = RNA_def_boolean(
      ot->srna, "wait_to_deselect_others", false, "Wait to Deselect Others", "");
  RNA_def_property_flag(prop, PROP_HIDDEN | PROP_SKIP_SAVE);

  RNA_def_int(ot->srna, "mouse_x", 0, INT_MIN, INT_MAX, "Mouse X", "", INT_MIN, INT_MAX);
  RNA_def_int(ot->srna, "mouse_y", 0, INT_MIN, INT_MAX, "Mouse Y", "", INT_MIN, INT_MAX);
}

void WM_operator_properties_gesture_box_zoom(wmOperatorType *ot)
{
  WM_operator_properties_border(ot);

  PropertyRNA *prop;
  prop = RNA_def_boolean(ot->srna, "zoom_out", false, "Zoom Out", "");
  RNA_def_property_flag(prop, PROP_HIDDEN | PROP_SKIP_SAVE);
}

/**
 * Use with #WM_gesture_lasso_invoke
 */
void WM_operator_properties_gesture_lasso(wmOperatorType *ot)
{
  PropertyRNA *prop;
  prop = RNA_def_collection_runtime(ot->srna, "path", &RNA_OperatorMousePath, "Path", "");
  RNA_def_property_flag(prop, PROP_HIDDEN | PROP_SKIP_SAVE);
}

/**
 * Use with #WM_gesture_straightline_invoke
 */
void WM_operator_properties_gesture_straightline(wmOperatorType *ot, int cursor)
{
  PropertyRNA *prop;

  prop = RNA_def_int(ot->srna, "xstart", 0, INT_MIN, INT_MAX, "X Start", "", INT_MIN, INT_MAX);
  RNA_def_property_flag(prop, PROP_HIDDEN | PROP_SKIP_SAVE);
  prop = RNA_def_int(ot->srna, "xend", 0, INT_MIN, INT_MAX, "X End", "", INT_MIN, INT_MAX);
  RNA_def_property_flag(prop, PROP_HIDDEN | PROP_SKIP_SAVE);
  prop = RNA_def_int(ot->srna, "ystart", 0, INT_MIN, INT_MAX, "Y Start", "", INT_MIN, INT_MAX);
  RNA_def_property_flag(prop, PROP_HIDDEN | PROP_SKIP_SAVE);
  prop = RNA_def_int(ot->srna, "yend", 0, INT_MIN, INT_MAX, "Y End", "", INT_MIN, INT_MAX);
  RNA_def_property_flag(prop, PROP_HIDDEN | PROP_SKIP_SAVE);

  if (cursor) {
    prop = RNA_def_int(ot->srna,
                       "cursor",
                       cursor,
                       0,
                       INT_MAX,
                       "Cursor",
                       "Mouse cursor style to use during the modal operator",
                       0,
                       INT_MAX);
    RNA_def_property_flag(prop, PROP_HIDDEN);
  }
}

/**
 * Use with #WM_gesture_circle_invoke
 */
void WM_operator_properties_gesture_circle(wmOperatorType *ot)
{
  PropertyRNA *prop;
  const int radius_default = 25;

  prop = RNA_def_int(ot->srna, "x", 0, INT_MIN, INT_MAX, "X", "", INT_MIN, INT_MAX);
  RNA_def_property_flag(prop, PROP_HIDDEN | PROP_SKIP_SAVE);
  prop = RNA_def_int(ot->srna, "y", 0, INT_MIN, INT_MAX, "Y", "", INT_MIN, INT_MAX);
  RNA_def_property_flag(prop, PROP_HIDDEN | PROP_SKIP_SAVE);
  RNA_def_int(ot->srna, "radius", radius_default, 1, INT_MAX, "Radius", "", 1, INT_MAX);

  prop = RNA_def_boolean(ot->srna, "wait_for_input", true, "Wait for Input", "");
  RNA_def_property_flag(prop, PROP_HIDDEN | PROP_SKIP_SAVE);
}

void WM_operator_properties_mouse_select(wmOperatorType *ot)
{
  PropertyRNA *prop;

  prop = RNA_def_boolean(ot->srna,
                         "extend",
                         false,
                         "Extend",
                         "Extend selection instead of deselecting everything first");
  RNA_def_property_flag(prop, PROP_SKIP_SAVE);
  prop = RNA_def_boolean(ot->srna, "deselect", false, "Deselect", "Remove from selection");
  RNA_def_property_flag(prop, PROP_SKIP_SAVE);
  prop = RNA_def_boolean(ot->srna, "toggle", false, "Toggle Selection", "Toggle the selection");
  RNA_def_property_flag(prop, PROP_SKIP_SAVE);

  prop = RNA_def_boolean(ot->srna,
                         "deselect_all",
                         false,
                         "Deselect On Nothing",
                         "Deselect all when nothing under the cursor");
  RNA_def_property_flag(prop, PROP_SKIP_SAVE);
}

/**
 * \param nth_can_disable: Enable if we want to be able to select no interval at all.
 */
void WM_operator_properties_checker_interval(wmOperatorType *ot, bool nth_can_disable)
{
  const int nth_default = nth_can_disable ? 0 : 1;
  const int nth_min = min_ii(nth_default, 1);
  RNA_def_int(ot->srna,
              "skip",
              nth_default,
              nth_min,
              INT_MAX,
              "Deselected",
              "Number of deselected elements in the repetitive sequence",
              nth_min,
              100);
  RNA_def_int(ot->srna,
              "nth",
              1,
              1,
              INT_MAX,
              "Selected",
              "Number of selected elements in the repetitive sequence",
              1,
              100);
  RNA_def_int(ot->srna,
              "offset",
              0,
              INT_MIN,
              INT_MAX,
              "Offset",
              "Offset from the starting point",
              -100,
              100);
}

void WM_operator_properties_checker_interval_from_op(struct wmOperator *op,
                                                     struct CheckerIntervalParams *op_params)
{
  const int nth = RNA_int_get(op->ptr, "nth");
  const int skip = RNA_int_get(op->ptr, "skip");
  int offset = RNA_int_get(op->ptr, "offset");

  op_params->nth = nth;
  op_params->skip = skip;

  /* So input of offset zero ends up being (nth - 1). */
  op_params->offset = mod_i(offset, nth + skip);
}

bool WM_operator_properties_checker_interval_test(const struct CheckerIntervalParams *op_params,
                                                  int depth)
{
  return ((op_params->skip == 0) ||
          ((op_params->offset + depth) % (op_params->skip + op_params->nth) >= op_params->skip));
}

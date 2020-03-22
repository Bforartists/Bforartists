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
 */

/** \file
 * \ingroup RNA
 */

#include <stdio.h>
#include <stdlib.h>

#include "BLI_utildefines.h"

#include "ED_text.h"

#include "RNA_define.h"

#include "rna_internal.h" /* own include */

#ifdef RNA_RUNTIME

#  include "WM_api.h"
#  include "WM_types.h"

static void rna_Text_clear(Text *text)
{
  BKE_text_clear(text);
  WM_main_add_notifier(NC_TEXT | NA_EDITED, text);
}

static void rna_Text_write(Text *text, const char *str)
{
  BKE_text_write(text, str);
  WM_main_add_notifier(NC_TEXT | NA_EDITED, text);
}

static void rna_Text_select_set(Text *text, int startl, int startc, int endl, int endc)
{
  txt_sel_set(text, startl, startc, endl, endc);
  WM_main_add_notifier(NC_TEXT | NA_EDITED, text);
}

static void rna_Text_cursor_set(Text *text, int line, int ch, bool select)
{
  txt_move_to(text, line, ch, select);
  WM_main_add_notifier(NC_TEXT | NA_EDITED, text);
}

#else

void RNA_api_text(StructRNA *srna)
{
  FunctionRNA *func;
  PropertyRNA *parm;

  func = RNA_def_function(srna, "clear", "rna_Text_clear");
  RNA_def_function_ui_description(func, "clear the text block");

  func = RNA_def_function(srna, "write", "rna_Text_write");
  RNA_def_function_ui_description(
      func, "write text at the cursor location and advance to the end of the text block");
  parm = RNA_def_string(func, "text", "Text", 0, "", "New text for this data-block");
  RNA_def_parameter_flags(parm, 0, PARM_REQUIRED);

  func = RNA_def_function(
      srna, "is_syntax_highlight_supported", "ED_text_is_syntax_highlight_supported");
  RNA_def_function_return(func,
                          RNA_def_boolean(func, "is_syntax_highlight_supported", false, "", ""));
  RNA_def_function_ui_description(func,
                                  "Returns True if the editor supports syntax highlighting "
                                  "for the current text datablock");

  func = RNA_def_function(srna, "select_set", "rna_Text_select_set");
  RNA_def_function_ui_description(func, "Set selection range by line and character index");
  parm = RNA_def_int(func, "line_start", 0, INT_MIN, INT_MAX, "Start Line", "", INT_MIN, INT_MAX);
  RNA_def_parameter_flags(parm, 0, PARM_REQUIRED);
  parm = RNA_def_int(
      func, "char_start", 0, INT_MIN, INT_MAX, "Start Character", "", INT_MIN, INT_MAX);
  RNA_def_parameter_flags(parm, 0, PARM_REQUIRED);
  parm = RNA_def_int(func, "line_end", 0, INT_MIN, INT_MAX, "End Line", "", INT_MIN, INT_MAX);
  RNA_def_parameter_flags(parm, 0, PARM_REQUIRED);
  parm = RNA_def_int(func, "char_end", 0, INT_MIN, INT_MAX, "End Character", "", INT_MIN, INT_MAX);
  RNA_def_parameter_flags(parm, 0, PARM_REQUIRED);

  func = RNA_def_function(srna, "cursor_set", "rna_Text_cursor_set");
  RNA_def_function_ui_description(func, "Set cursor by line and (optionally) character index");
  parm = RNA_def_int(func, "line", 0, 0, INT_MAX, "Line", "", 0, INT_MAX);
  RNA_def_parameter_flags(parm, 0, PARM_REQUIRED);
  parm = RNA_def_int(func, "character", 0, 0, INT_MAX, "Character", "", 0, INT_MAX);
  RNA_def_boolean(func, "select", false, "", "Select when moving the cursor");
}

#endif

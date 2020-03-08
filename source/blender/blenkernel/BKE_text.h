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
 * The Original Code is Copyright (C) 2001-2002 by NaN Holding BV.
 * All rights reserved.
 */
#ifndef __BKE_TEXT_H__
#define __BKE_TEXT_H__

/** \file
 * \ingroup bke
 */

#ifdef __cplusplus
extern "C" {
#endif

struct Main;
struct Text;
struct TextLine;

void BKE_text_free_lines(struct Text *text);
struct Text *BKE_text_add(struct Main *bmain, const char *name);
int txt_extended_ascii_as_utf8(char **str);
bool BKE_text_reload(struct Text *text);
struct Text *BKE_text_load_ex(struct Main *bmain,
                              const char *file,
                              const char *relpath,
                              const bool is_internal);
struct Text *BKE_text_load(struct Main *bmain, const char *file, const char *relpath);
struct Text *BKE_text_copy(struct Main *bmain, const struct Text *ta);
void BKE_text_clear(struct Text *text);
void BKE_text_write(struct Text *text, const char *str);
int BKE_text_file_modified_check(struct Text *text);
void BKE_text_file_modified_ignore(struct Text *text);

char *txt_to_buf(struct Text *text, int *r_buf_strlen);
void txt_clean_text(struct Text *text);
void txt_order_cursors(struct Text *text, const bool reverse);
int txt_find_string(struct Text *text, const char *findstr, int wrap, int match_case);
bool txt_has_sel(struct Text *text);
int txt_get_span(struct TextLine *from, struct TextLine *to);
void txt_move_up(struct Text *text, const bool sel);
void txt_move_down(struct Text *text, const bool sel);
void txt_move_left(struct Text *text, const bool sel);
void txt_move_right(struct Text *text, const bool sel);
void txt_jump_left(struct Text *text, const bool sel, const bool use_init_step);
void txt_jump_right(struct Text *text, const bool sel, const bool use_init_step);
void txt_move_bof(struct Text *text, const bool sel);
void txt_move_eof(struct Text *text, const bool sel);
void txt_move_bol(struct Text *text, const bool sel);
void txt_move_eol(struct Text *text, const bool sel);
void txt_move_toline(struct Text *text, unsigned int line, const bool sel);
void txt_move_to(struct Text *text, unsigned int line, unsigned int ch, const bool sel);
void txt_pop_sel(struct Text *text);
void txt_delete_char(struct Text *text);
void txt_delete_word(struct Text *text);
void txt_delete_selected(struct Text *text);
void txt_sel_all(struct Text *text);
void txt_sel_clear(struct Text *text);
void txt_sel_line(struct Text *text);
void txt_sel_set(struct Text *text, int startl, int startc, int endl, int endc);
char *txt_sel_to_buf(struct Text *text, int *r_buf_strlen);
void txt_insert_buf(struct Text *text, const char *in_buffer);
void txt_split_curline(struct Text *text);
void txt_backspace_char(struct Text *text);
void txt_backspace_word(struct Text *text);
bool txt_add_char(struct Text *text, unsigned int add);
bool txt_add_raw_char(struct Text *text, unsigned int add);
bool txt_replace_char(struct Text *text, unsigned int add);
bool txt_unindent(struct Text *text);
void txt_comment(struct Text *text);
void txt_indent(struct Text *text);
bool txt_uncomment(struct Text *text);
void txt_move_lines(struct Text *text, const int direction);
void txt_duplicate_line(struct Text *text);
int txt_setcurr_tab_spaces(struct Text *text, int space);
bool txt_cursor_is_line_start(struct Text *text);
bool txt_cursor_is_line_end(struct Text *text);

int txt_calc_tab_left(struct TextLine *line, int ch);
int txt_calc_tab_right(struct TextLine *line, int ch);

/* utility functions, could be moved somewhere more generic but are python/text related  */
int text_check_bracket(const char ch);
bool text_check_delim(const char ch);
bool text_check_digit(const char ch);
bool text_check_identifier(const char ch);
bool text_check_identifier_nodigit(const char ch);
bool text_check_whitespace(const char ch);
int text_find_identifier_start(const char *str, int i);

/* defined in bpy_interface.c */
extern int text_check_identifier_unicode(const unsigned int ch);
extern int text_check_identifier_nodigit_unicode(const unsigned int ch);

enum {
  TXT_MOVE_LINE_UP = -1,
  TXT_MOVE_LINE_DOWN = 1,
};

/* Fast non-validating buffer conversion for undo. */
char *txt_to_buf_for_undo(struct Text *text, int *r_buf_strlen);
void txt_from_buf_for_undo(struct Text *text, const char *buf, int buf_len);

#ifdef __cplusplus
}
#endif

#endif

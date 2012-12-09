/*
 * ***** BEGIN GPL LICENSE BLOCK *****
 *
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
 * The Original Code is Copyright (C) 2011 Blender Foundation.
 * All rights reserved.
 *
 * Contributor(s): Campbell Barton.
 *
 * ***** END GPL LICENSE BLOCK *****
 *
 */

/** \file blender/blenlib/intern/string_cursor_utf8.c
 *  \ingroup bli
 */

#include <stdio.h>
#include <stdlib.h>

#include "BLI_utildefines.h"
#include "BLI_string_utf8.h"

#include "BLI_string_cursor_utf8.h" /* own include */

typedef enum strCursorDelimType {
	STRCUR_DELIM_NONE,
	STRCUR_DELIM_ALPHANUMERIC,
	STRCUR_DELIM_PUNCT,
	STRCUR_DELIM_BRACE,
	STRCUR_DELIM_OPERATOR,
	STRCUR_DELIM_QUOTE,
	STRCUR_DELIM_WHITESPACE,
	STRCUR_DELIM_OTHER
} strCursorDelimType;

static strCursorDelimType cursor_delim_type(const char *ch_utf8)
{
	/* for full unicode support we really need to have large lookup tables to figure
	 * out whats what in every possible char set - and python, glib both have these. */
	unsigned int uch = BLI_str_utf8_as_unicode(ch_utf8);

	switch (uch) {
		case ',':
		case '.':
			return STRCUR_DELIM_PUNCT;

		case '{':
		case '}':
		case '[':
		case ']':
		case '(':
		case ')':
			return STRCUR_DELIM_BRACE;

		case '+':
		case '-':
		case '=':
		case '~':
		case '%':
		case '/':
		case '<':
		case '>':
		case '^':
		case '*':
		case '&':
		case '|':
			return STRCUR_DELIM_OPERATOR;

		case '\'':
		case '\"':
			return STRCUR_DELIM_QUOTE;

		case ' ':
		case '\t':
			return STRCUR_DELIM_WHITESPACE;

		case '\\':
		case '@':
		case '#':
		case '$':
		case ':':
		case ';':
		case '?':
		case '!':
		case 0xA3:  /* pound */
		case 0x80:  /* euro */
			/* case '_': *//* special case, for python */
			return STRCUR_DELIM_OTHER;

		default:
			break;
	}
	return STRCUR_DELIM_ALPHANUMERIC; /* Not quite true, but ok for now */
}

int BLI_str_cursor_step_next_utf8(const char *str, size_t maxlen, int *pos)
{
	const char *str_end = str + (maxlen + 1);
	const char *str_pos = str + (*pos);
	const char *str_next = BLI_str_find_next_char_utf8(str_pos, str_end);
	if (str_next) {
		(*pos) += (str_next - str_pos);
		if ((*pos) > maxlen) {
			(*pos) = maxlen;
		}
		return TRUE;
	}

	return FALSE;
}

int BLI_str_cursor_step_prev_utf8(const char *str, size_t UNUSED(maxlen), int *pos)
{
	if ((*pos) > 0) {
		const char *str_pos = str + (*pos);
		const char *str_prev = BLI_str_find_prev_char_utf8(str, str_pos);
		if (str_prev) {
			(*pos) -= (str_pos - str_prev);
			return TRUE;
		}
	}

	return FALSE;
}

void BLI_str_cursor_step_utf8(const char *str, size_t maxlen,
                              int *pos, strCursorJumpDirection direction,
                              strCursorJumpType jump)
{
	if (direction == STRCUR_DIR_NEXT) {
		BLI_str_cursor_step_next_utf8(str, maxlen, pos);
		if (jump != STRCUR_JUMP_NONE) {
			const strCursorDelimType delim_type = (*pos) < maxlen ? cursor_delim_type(&str[(*pos) - 1]) : STRCUR_DELIM_NONE;
			/* jump between special characters (/,\,_,-, etc.),
			 * look at function test_special_char() for complete
			 * list of special character, ctr -> */
			while (TRUE) {
				if ((jump != STRCUR_JUMP_ALL) && (delim_type != cursor_delim_type(&str[*pos]))) {
					break;
				}
				else if ((*pos) >= maxlen) {
					break;
				}
				BLI_str_cursor_step_next_utf8(str, maxlen, pos);
			}
		}
	}
	else if (direction == STRCUR_DIR_PREV) {
		BLI_str_cursor_step_prev_utf8(str, maxlen, pos);
		if (jump != STRCUR_JUMP_NONE) {
			const strCursorDelimType delim_type = (*pos) > 0 ? cursor_delim_type(&str[(*pos)]) : STRCUR_DELIM_NONE;
			/* jump between special characters (/,\,_,-, etc.),
			 * look at function test_special_char() for complete
			 * list of special character, ctr -> */
			while (TRUE) {
				if ((jump != STRCUR_JUMP_ALL) && (delim_type != cursor_delim_type(&str[*pos]))) {
					/* left only: compensate for index/change in direction */
					if (delim_type != STRCUR_DELIM_NONE) {
						BLI_str_cursor_step_next_utf8(str, maxlen, pos);
					}
					break;
				}
				else if ((*pos) <= 0) {
					break;
				}
				BLI_str_cursor_step_prev_utf8(str, maxlen, pos);
			}
		}
	}
	else {
		BLI_assert(0);
	}
}

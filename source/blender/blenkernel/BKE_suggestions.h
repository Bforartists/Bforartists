/**	
 * $Id: $ 
 *
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
 * Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
 *
 * The Original Code is Copyright (C) 2008, Blender Foundation
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): none yet.
 *
 * ***** END GPL LICENSE BLOCK *****
 */
#ifndef BKE_SUGGESTIONS_H
#define BKE_SUGGESTIONS_H

#ifdef __cplusplus
extern "C" {
#endif

/* ****************************************************************************
Suggestions must be added in sorted order (no attempt is made to sort the list)
The list is then divided up based on the prefix provided by update_suggestions:
Example:
  Prefix: ab
  aaa <-- first
  aab
  aba <-- firstmatch
  abb <-- lastmatch
  baa
  bab <-- last
**************************************************************************** */

struct Text;

typedef struct SuggItem {
	struct SuggItem *prev, *next;
	char *name;
	char type;
} SuggItem;

typedef struct SuggList {
	SuggItem *first, *last;
	SuggItem *firstmatch, *lastmatch;
} SuggList;

void free_suggestions();

void add_suggestion(const char *name, char type);
void update_suggestions(const char *prefix);
SuggItem *suggest_first();
SuggItem *suggest_last();

void set_suggest_text(Text *text);
void clear_suggest_text();
short is_suggest_active(Text *text);

#ifdef __cplusplus
}
#endif

#endif

/**
 * $Id:
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
 * The Original Code is Copyright (C) 2008 Blender Foundation.
 * All rights reserved.
 *
 * 
 * Contributor(s): Blender Foundation
 *
 * ***** END GPL LICENSE BLOCK *****
 */
#ifndef ED_FILE_INTERN_H
#define ED_FILE_INTERN_H

/* internal exports only */


/* file_header.c */
void file_header_buttons(const bContext *C, ARegion *ar);


/* file_draw.c */
#define TILE_BORDER_X 8
#define TILE_BORDER_Y 8

void file_draw_buttons(const bContext *C, ARegion *ar);
void file_calc_previews(const bContext *C, ARegion *ar);
void file_draw_previews(const bContext *C, ARegion *ar);
void file_draw_list(const bContext *C, ARegion *ar);
void file_draw_fsmenu(const bContext *C, ARegion *ar);

/* file_ops.h */
struct wmOperatorType;
void ED_FILE_OT_select(struct wmOperatorType *ot);
void ED_FILE_OT_select_bookmark(struct wmOperatorType *ot);
#endif /* ED_FILE_INTERN_H */


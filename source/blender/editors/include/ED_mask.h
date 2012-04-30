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
 * The Original Code is Copyright (C) 2012 Blender Foundation.
 * All rights reserved.
 *
 * Contributor(s): Blender Foundation,
 *                 Sergey Sharybin
 *
 * ***** END GPL LICENSE BLOCK *****
 */

/** \file ED_mask.h
 *  \ingroup editors
 */

#ifndef __ED_MASK_H__
#define __ED_MASK_H__

struct wmKeyConfig;

/* mask_editor.c */
void ED_operatortypes_mask(void);
void ED_keymap_mask(struct wmKeyConfig *keyconf);
void ED_operatormacros_mask(void);

/* mask_draw.c */
void ED_mask_draw(bContext *C, int width, int height, float zoomx, float zoomy);

#endif /* ED_TEXT_H */

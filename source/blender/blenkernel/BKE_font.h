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
 * The Original Code is Copyright (C) 2001-2002 by NaN Holding BV.
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): none yet.
 *
 * ***** END GPL LICENSE BLOCK *****
 */
#ifndef __BKE_FONT_H__
#define __BKE_FONT_H__

/** \file BKE_font.h
 *  \ingroup bke
 */

#ifdef __cplusplus
extern "C" {
#endif

#include <wchar.h>

struct VFont;
struct Scene;
struct Object;
struct Curve;
struct objfnt;
struct TmpFont;
struct CharInfo;
struct Main;

struct CharTrans {
	float xof, yof;
	float rot;
	short linenr, charnr;
	char dobreak;
};

typedef struct SelBox {
	float x, y, w, h;
} SelBox;

typedef struct EditFont {	
	wchar_t *copybuf;
	wchar_t *copybufinfo;
	
	wchar_t *textbuf;
	struct CharInfo *textbufinfo;
	wchar_t *oldstr;
	struct CharInfo *oldstrinfo;
	
	float textcurs[4][2];
	
} EditFont;


bool BKE_vfont_is_builtin(struct VFont *vfont);
void BKE_vfont_builtin_register(void *mem, int size);

void BKE_vfont_free_data(struct VFont *vfont);
void BKE_vfont_free(struct VFont *sc); 
struct VFont *BKE_vfont_builtin_get(void);
struct VFont *BKE_vfont_load(struct Main *bmain, const char *name);

struct CharTrans *BKE_vfont_to_curve(struct Main *bmain, struct Scene *scene, struct Object *ob, int mode);

int BKE_vfont_select_get(struct Object *ob, int *start, int *end);

#ifdef __cplusplus
}
#endif

#endif


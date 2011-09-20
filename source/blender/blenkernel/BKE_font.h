/*
 * $Id$ 
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
#ifndef BKE_VFONT_H
#define BKE_VFONT_H

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

struct chartrans {
	float xof, yof;
	float rot;
	short linenr,charnr;
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


void BKE_font_register_builtin(void *mem, int size);

void free_vfont(struct VFont *sc); 
void free_ttfont(void);
struct VFont *get_builtin_font(void);
struct VFont *load_vfont(const char *name);
struct TmpFont *vfont_find_tmpfont(struct VFont *vfont);

struct chartrans *BKE_text_to_curve(struct Scene *scene, struct Object *ob, int mode);

int BKE_font_getselection(struct Object *ob, int *start, int *end);

size_t chtoutf8(const unsigned long c, char o[4]);
void wcs2utf8s(char *dst, const wchar_t *src);
size_t wcsleninu8(wchar_t *src);
size_t utf8towchar(wchar_t *w, const char *c);

#ifdef __cplusplus
}
#endif

#endif


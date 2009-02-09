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
 * The Original Code is Copyright (C) 2009 Blender Foundation.
 * All rights reserved.
 *
 * 
 * Contributor(s): Blender Foundation
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#if 0

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <ft2build.h>

#include FT_FREETYPE_H
#include FT_GLYPH_H

#include "MEM_guardedalloc.h"

#include "DNA_listBase.h"

#include "BKE_utildefines.h"

#include "BLI_blenlib.h"
#include "BLI_linklist.h"	/* linknode */
#include "BLI_string.h"

#include "blf_internal_types.h"


unsigned int blf_glyph_hash(unsigned int val)
{
	unsigned int key;

	key= val;
	key += ~(key << 16);
	key ^= (key >> 5);
	key += (key << 3);
	key ^= (key >> 13);
	key += ~(key << 9);
	key ^= (key >> 17);
	return(key % 257);
}

GlyphCacheBLF *blf_glyph_cache_find(FontBLF *font, int size, int dpi)
{
	GlyphCacheBLF *p;

	p= (GlyphCacheBLF *)font->cache.first;
	while (p) {
		if (p->size == size && p->dpi == dpi)
			return(p);
		p= p->next;
	}
	return(NULL);
}

/* Create a new glyph cache for the current size and dpi. */
GlyphCacheBLF *blf_glyph_cache_new(FontBLF *font)
{
	GlyphCacheBLF *gc;
	int i;

	gc= (GlyphCacheBLF *)MEM_mallocN(sizeof(GlyphCacheBLF));
	gc->next= NULL;
	gc->prev= NULL;
	gc->size= font->size;
	gc->dpi= font->dpi;

	for (i= 0; i < 257; i++) {
		gc->bucket[i].first= NULL;
		gc->bucket[i].last= NULL;
	}

	gc->textures= (GLuint *)malloc(sizeof(GLunit)*256);
	gc->ntex= 256;
	gc->cur_tex= -1;
	gc->x_offs= 0;
	gc->y_offs= 0;
	gc->pad= 3;

	gc->num_glyphs= font->face.num_glyphs;
	gc->rem_glyphs= font->face.num_glyphs;
	gc->ascender= ((float)font->size.metrics.ascender) / 64.0f;
	gc->descender= ((float)font->size.metrics.descender) / 64.0f;

	if (FT_IS_SCALABLE(font->face)) {
		gc->max_glyph_width= (float)((font->face->bbox.xMax - font->face->bbox.xMin) *
					(((float)font->face->size.metrics.x_ppem) /
					 ((float)font->face->units_per_EM)));

		gc->max_glyph_height= (float)((font->face->bbox.yMax - font->face->bbox.yMin) *
					(((float)font->face->size.metrics.y_ppem) /
					 ((float)font->face->units_per_EM)));
	}
	else {
		gc->max_glyph_width= ((float)font->face->metrics.max_advance) / 64.0f;
		gc->max_glyph_height= ((float)font->face->size.metrics.height) / 64.0f;
	}

	gc->p2_width= 0;
	gc->p2_height= 0;

	BLI_addhead(&font->cache, gc);
	return(gc);
}

void blf_glyph_cache_texture(FontBLF *font, GlyphCacheBLF *gc)
{
	int tot_mem;
	unsigned char *buf;

	/* move the index. */
	gc->cur_tex++;

	if (gc->cur_tex > gc->ntex) {
		gc->ntex *= 2;
		gc->textures= (GLuint *)realloc((void *)gc->textures, sizeof(GLunit)*gc->ntex);
	}

	gc->p2_width= blf_next_p2((gc->rem_glyphs * gc->max_glyph_width) + (gc->pad * 2));
	if (gc->p2_width > font->max_tex_size)
		gc->p2_width= font->max_tex_size;

	i= (int)((gc->p2_width - (gc->pad * 2)) / gc->p2_width);
	gc->p2_height= blf_next_p2(((gc->num_glyphs / i) + 1) * gc->max_glyph_height);

	if (gc->p2_height > font->max_tex_size)
		gc->p2_height= font->max_tex_size;

	tot_mem= gc->p2_width * gc->p2_height;
	buf= (unsigned char *)malloc(tot_mem);
	memset((void *)buf, 0, tot_mem);

	glGenTextures(1, (GLuint*)gc->texures[gc->cur_tex]);
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP);
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP);
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST);
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST);

	glTexImage2D(GL_TEXTURE_2D, 0, GL_ALPHA, gc->p2_width, gc->p2_height, 0, GL_ALPHA, GL_UNSIGNED_BYTE, buf);
	free((void *)buf);
}

GlyphBLF *blf_glyph_search(GlyphCacheBLF *gc, FT_UInt idx)
{
	GlyphBLF *p;
	unsigned int key;

	key= blf_glyph_hash(idx);
	p= gc->bucket[key].first;
	while (p) {
		if (p->index == idx)
			return(p);
		p= p->next;
	}
	return(NULL);
}

GlyphBLF *blf_glyph_add(FontBLF *font, FT_UInt index, unsigned int c)
{
	FT_GlyphSlot slot;
	GlyphCache *gc;
	GlyphBLF *g;
	FT_Error err;
	FT_Bitmap bitmap;
	FTBBox bbox;
	unsigned int key;

	g= blf_glyph_search(font->glyph_cache, index);
	if (g)
		return(g);

	err= FT_Load_Glyph(font->face, index, FT_LOAD_NO_HINTING | FT_LOAD_NO_BITMAP);
	if (err)
		return(NULL);

	/* get the glyph. */
	slot= font->face->glyph;

	err= FT_Render_Glyph(slot, FT_RENDER_MODE_NORMAL);
	if (err)
		return(NULL);

	g= (GlyphBLF *)MEM_mallocN(sizeof(GlyphBLF), "blf_glyph_add");
	g->next= NULL;
	g->prev= NULL;
	g->c= c;
	g->index= index;

	gc= font->glyph_cache;
	if (gc->cur_tex == -1) {
		blf_glyph_cache_texture(font, gc);
		gc->x_offs= gc->pad;
		gc->y_offs= gc->pad;
	}

	if (gc->x_offs > (gc->p2_width - gc->max_glyph_width)) {
		gc->x_offs= gc->pad;
		gc->y_offs += gc->max_glyph_height;

		if (gc->y_offs > (gc->p2_height - gc->max_glyph_height)) {
			gc->y_offs= gc->pad;
			blf_glyph_cache_texture(font, gc);
		}
	}

	bitmap= slot->bitmap;
	g->tex= gc->textures[gc->cur_tex];
	g->xoff= gc->x_offs;
	g->yoff= gc->y_offs;
	g->width= bitmap.width;
	g->height= bitmap.rows;

	if (g->width && g->height) {
		glPushClientAttrib(GL_CLIENT_PIXEL_STORE_BIT);
		glPixelStorei(GL_UNPACK_LSB_FIRST, GL_FALSE);
		glPixelStorei(GL_UNPACK_ROW_LENGTH, 0);
		glPixelStorei(GL_UNPACK_ALIGNMENT, 1);

		glBindTexture(GL_TEXTURE_2D, g->tex);
		glTexSubImage2D(GL_TEXTURE_2D, 0, g->xoff, g->yoff, g->width, g->height, GL_ALPHA, GL_UNSIGNED_BYTE, bitmap.buffer);
		glPopClientAttrib();
	}

	g->advance= ((float)slot->advance.x) / 64.0f;
	g->pos_x= bitmap.left;
	g->pos_y= bitmap.top;

	FT_Outline_Get_CBox(&(slot->outline), &bbox);
	g->box.xmin= ((float)bbox.xMin) / 64.0f;
	g->box.xmax= ((float)bbox.xMax) / 64.0f;
	g->box.ymin= ((float)bbox.yMin) / 64.0f;
	g->box.ymax= ((float)bbox.yMax) / 64.0f;

	g->uv[0][0]= ((float)g->xoff) / ((float)g->p2_width);
	g->uv[0][1]= ((float)g->yoff) / ((float)g->p2_height);
	g->uv[1][0]= ((float)(g->xoff + g->width)) / ((float)g->p2_width);
	g->uv[1][1]= ((float)(g->yoff + g->height)) / ((float)g->p2_height);

	key= blf_glyph_hash(g->index);
	BLI_addhead(&gc->bucket[key], g);
	return(g);
}

#endif /* zero!! */

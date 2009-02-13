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
#include "blf_internal.h"


/* freetype2 handle. */
FT_Library global_ft_lib;

int blf_font_init(void)
{
	return(FT_Init_FreeType(&global_ft_lib));
}

void blf_font_exit(void)
{
	FT_Done_Freetype(global_ft_lib);
}

void blf_font_fill(FontBLF *font)
{
	font->ref= 1;
	font->aspect= 1.0f;
	font->pos[0]= 0.0f;
	font->pos[1]= 0.0f;
	font->angle[0]= 0.0f;
	font->angle[1]= 0.0f;
	font->angle[2]= 0.0f;
	Mat4One(font->mat);
	font->clip_rec.xmin= 0.0f;
	font->clip_rec.xmax= 0.0f;
	font->clip_rec.ymin= 0.0f;
	font->clip_rec.ymax= 0.0f;
	font->clip_mode= BLF_CLIP_DISABLE;
	font->dpi= 0;
	font->size= 0;
	font->cache.first= NULL;
	font->cache.last= NULL;
	font->glyph_cache= NULL;
	glGetIntegerv(GL_MAX_TEXTURE_SIZE, (GLint *)&font->max_tex_size);
}

FontBLF *blf_font_new(char *name, char *filename)
{
	FontBLF *font;
	FT_Error err;

	font= (FontBLF *)MEM_mallocN(sizeof(FontBLF), "blf_font_new");
	err= FT_New_Face(global_ft_lib, filename, 0, &font->face);
	if (err) {
		printf("BLF: Can't load font: %s\n", filename);
		MEM_freeN(font);
		return(NULL);
	}

	err= FT_Select_Charmap(font->face, ft_encoding_unicode);
	if (err) {
		printf("Warning: FT_Select_Charmap fail!!\n");
		FT_Done_Face(font->face);
		MEM_freeN(font);
		return(NULL);
	}

	font->name= MEM_strdup(name);
	font->filename= MEM_strdup(filename);
	blf_font_fill(font);
	return(font);
}

FontBLF *blf_font_new_from_mem(char *name, unsigned char *mem, int mem_size)
{
	FontBLF *font;
	FT_Error err;

	font= (FontBLF *)MEM_mallocN(sizeof(FontBLF), "blf_font_new_from_mem");
	err= FT_New_Memory_Face(global_ft_lib, mem, size, 0, &font->face);
	if (err) {
		printf("BLF: Can't load font: %s, from memory!!\n", name);
		MEM_freeN(font);
		return(NULL);
	}

	err= FT_Select_Charmap(font->face, ft_encoding_unicode);
	if (err) {
		printf("BLF: FT_Select_Charmap fail!!\n");
		FT_Done_Face(font->face);
		MEM_freeN(font);
		return(NULL);
	}

	font->name= MEM_strdup(name);
	font->filename= NULL;
	blf_font_fill(font);
	return(font);
}

void blf_font_size(FontBLF *font, int size, int dpi)
{
	GlyphCacheBLF *gc;
	FT_Error err;
	
	err= FT_Set_Char_Size(font->face, 0, (size * 64), dpi, dpi);
	if (err) {
		/* FIXME: here we can go through the fixed size and choice a close one */
		printf("Warning: The current face don't support the size (%d) and dpi (%d)\n", size, dpi);
		return;
	}

	font->size= size;
	font->dpi= dpi;

	gc= blf_glyph_cache_find(font, size, dpi);
	if (gc)
		font->glyph_cache= gc;
	else {
		gc= blf_glyph_cache_new(font);
		if (gc)
			font->glyph_cache= gc;
	}
}

void blf_font_draw(FontBLF *font, char *str)
{
	unsigned int c;
	GlyphBLF *g, *g_prev;
	FT_Vector delta;
	FT_UInt glyph_index;
	int pen_x, pen_y;
	int i, has_kerning;

	i= 0;
	pen_x= 0;
	pen_y= 0;
	has_kerning= FT_HAS_KERNING(font->face);
	g_prev= NULL;

	while (str[i]) {
		c= blf_uf8_next((unsigned char *)str, &i);
		if (c == 0)
			break;

		glyph_index= FT_Get_Char_Index(face, c);
		g= blf_glyph_search(font->glyph_cache, glyph_index);
		if (!g)
			g= blf_glyph_add(font, glyph_index, c);

		/* if we don't found a glyph, skip it. */
		if (!g)
			continue;

		if (use_kering && g_prev) {
			delta.x= 0;
			delta.y= 0;

			FT_Get_Kerning(font->face, g_prev->index, glyph_index, FT_KERNING_MODE_UNFITTED, &delta);
			pen_x += delta.x >> 6;
		}

		blf_glyph_render(g, (float)pen_x, (float)pen_y);
		pen_x += g->advance;
		g_prev= g;
	}
}

#endif /* zero!! */

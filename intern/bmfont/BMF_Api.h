/**
 * $Id$
 * ***** BEGIN GPL/BL DUAL LICENSE BLOCK *****
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version. The Blender
 * Foundation also sells licenses for use in proprietary software under
 * the Blender License.  See http://www.blender.org/BL/ for information
 * about this.
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
 * The Original Code is Copyright (C) 2001-2002 by NaN Holding BV.
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): none yet.
 *
 * ***** END GPL/BL DUAL LICENSE BLOCK *****
 */

/**

 * $Id$
 * Copyright (C) 2001 NaN Technologies B.V.
 *
 * API of the OpenGL bitmap font library.
 * Currently draws fonts using the glBitmap routine.
 * This implies that drawing speed is heavyly dependant on
 * the 2D capabilities of the graphics card.
 */

#ifndef __BMF_API_H
#define __BMF_API_H

#ifdef __cplusplus
extern "C" { 
#endif

#include "BMF_Fonts.h"

/**
 * Returns the font for a given font type.
 * @param font	The font to retrieve.
 * @return The font (or nil if not found).
 */
BMF_Font* BMF_GetFont(BMF_FontType font);

/**
 * Draws a character at the current raster position.
 * @param font	The font to use.
 * @param c		The character to draw.
 * @return Indication of success (0 == error).
 */
int BMF_DrawCharacter(BMF_Font* font, char c);

/**
 * Draws a string at the current raster position.
 * @param font	The font to use.
 * @param str	The string to draw.
 * @return Indication of success (0 == error).
 */
int BMF_DrawString(BMF_Font* font, char* str);

/**
 * Returns the width of a character in pixels.
 * @param font	The font to use.
 * @param c		The character.
 * @return The length.
 */
int BMF_GetCharacterWidth(BMF_Font* font, char c);

/**
 * Returns the width of a string of characters.
 * @param font	The font to use.
 * @param str	The string.
 * @return The length.
 */
int BMF_GetStringWidth(BMF_Font* font, char* str);

/**
 * Returns the bounding box of the font. The width and
 * height represent the bounding box of the union of
 * all glyps. The minimum and maximum values of the
 * box represent the extent of the font and its positioning
 * about the origin.
 */
void BMF_GetBoundingBox(BMF_Font* font, int *xmin_r, int *ymin_r, int *xmax_r, int *ymax_r);

/**
 * Convert the given @a font to a texture, and return the GL texture
 * ID of the texture. If the texture ID is bound, text can
 * be drawn using the texture by calling DrawStringTexture.
 * 
 * @param font The font to create the texture from.
 * @return The GL texture ID of the new texture, or -1 if unable
 * to create.
 */
int BMF_GetFontTexture(BMF_Font* font);

/**
 * Draw the given @a str at the point @a x, @a y, @a z, using
 * texture coordinates. This assumes that an appropriate texture
 * has been bound, see BMF_BitmapFont::GetTexture(). The string
 * is drawn along the positive X axis.
 * 
 * @param font The font to draw with.
 * @param string The c-string to draw.
 * @param x The x coordinate to start drawing at.
 * @param y The y coordinate to start drawing at.
 * @param z The z coordinate to start drawing at.
 */
void BMF_DrawStringTexture(BMF_Font* font, char* string, float x, float y, float z);

#ifdef __cplusplus
}
#endif

#endif /* __BMF_API_H */

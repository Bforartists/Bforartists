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
 */

#ifndef __BMF_BITMAP_FONT_H
#define __BMF_BITMAP_FONT_H

#include "BMF_FontData.h"

/**
 * Base class for OpenGL bitmap fonts.
 */
class BMF_BitmapFont
{
public:
	/**
	 * Default constructor.
	 */
	BMF_BitmapFont(BMF_FontData* fontData);

	/**
	 * Destructor.
	 */
	virtual	~BMF_BitmapFont(void);

	/**
	 * Draws a string at the current raster position.
	 * @param str	The string to draw.
	 */
	void DrawString(char* str);

	/**
	 * Draws a string at the current raster position.
	 * @param str	The string to draw.
	 * @return The width of the string.
	 */
	int GetStringWidth(char* str);

	/**
	 * Returns the bounding box of the font. The width and
	 * height represent the bounding box of the union of
	 * all glyps. The minimum and maximum values of the
	 * box represent the extent of the font and its positioning
	 * about the origin.
	 */
	void GetBoundingBox(int & xMin, int & yMin, int & xMax, int & yMax);

	/**
	 * Convert the font to a texture, and return the GL texture
	 * ID of the texture. If the texture ID is bound, text can
	 * be drawn using the texture by calling DrawStringTexture.
	 * 
	 * @return The GL texture ID of the new texture, or -1 if unable
	 * to create.
	 */
	int GetTexture();
	
	/**
	 * Draw the given @a string at the point @a x, @a y, @a z, using
	 * texture coordinates. This assumes that an appropriate texture
	 * has been bound, see BMF_BitmapFont::GetTexture(). The string
	 * is drawn along the positive X axis.
	 * 
	 * @param string The c-string to draw.
	 * @param x The x coordinate to start drawing at.
	 * @param y The y coordinate to start drawing at.
	 * @param z The z coordinate to start drawing at.
	 */
	void DrawStringTexture(char* string, float x, float y, float z);
	
protected:
	/** Pointer to the font data. */
	 BMF_FontData* m_fontData;
};

#endif // __BMF_BITMAP_FONT_H

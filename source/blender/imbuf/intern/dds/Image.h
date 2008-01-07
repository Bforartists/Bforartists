/**
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
 * Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
 *
 * Contributors: Amorilia (amorilia@gamebox.net)
 *
 * ***** END GPL LICENSE BLOCK *****
 */

/*
 * This file is based on a similar file from the NVIDIA texture tools
 * (http://nvidia-texture-tools.googlecode.com/)
 *
 * Original license from NVIDIA follows.
 */

// This code is in the public domain -- castanyo@yahoo.es

#ifndef _DDS_IMAGE_H
#define _DDS_IMAGE_H

#include <Color.h>

/// 32 bit RGBA image.
class Image
{
public:
	
	enum Format 
	{
		Format_RGB,
		Format_ARGB,
	};
	
	Image();
	~Image();
	
	void allocate(unsigned int w, unsigned int h);
	/*
	bool load(const char * name);
	
	void wrap(void * data, unsigned int w, unsigned int h);
	void unwrap();
	*/
	
	unsigned int width() const;
	unsigned int height() const;
	
	const Color32 * scanline(unsigned int h) const;
	Color32 * scanline(unsigned int h);
	
	const Color32 * pixels() const;
	Color32 * pixels();
	
	const Color32 & pixel(unsigned int idx) const;
	Color32 & pixel(unsigned int idx);
	
	const Color32 & pixel(unsigned int x, unsigned int y) const;
	Color32 & pixel(unsigned int x, unsigned int y);
	
	Format format() const;
	void setFormat(Format f);
	
private:
	void free();
	
private:
	unsigned int m_width;
	unsigned int m_height;
	Format m_format;
	Color32 * m_data;
};


inline const Color32 & Image::pixel(unsigned int x, unsigned int y) const
{
	return pixel(y * width() + x);
}

inline Color32 & Image::pixel(unsigned int x, unsigned int y)
{
	return pixel(y * width() + x);
}

#endif // _DDS_IMAGE_H

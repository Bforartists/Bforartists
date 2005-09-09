/**
 * $Id$
 *
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
#include "../IMG_Api.h"
#include "IMG_BrushRGBA32.h"
#include "IMG_CanvasRGBA32.h"

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

IMG_BrushPtr IMG_BrushCreate(unsigned int w, unsigned int h, float r, float g, float b, float a)
{
	IMG_BrushPtr brush = 0;
	try {
		IMG_ColorRGB c (r, g, b);
		brush = new IMG_BrushRGBA32 (w, h, c, a);
	}
	catch (...) {
		brush = 0;
	}
	return brush;
}


void IMG_BrushDispose(IMG_BrushPtr brush)
{
	if (brush) {
		delete ((IMG_BrushRGBA32*)brush);
		brush = 0;
	}
}

void IMG_BrushSetInnerRaduisRatio(IMG_BrushPtr brush,float aspect)
{
	if (brush) {
		TUns32 he = ((IMG_BrushRGBA32*)brush)->getHeight();
		TUns32 we = ((IMG_BrushRGBA32*)brush)->getWidth();
        TUns32 si = we;
		if (he > si) si = we;
		he = si/2;
		we = (TUns32)(aspect*si/2);
		if (we < 2) we = 2;


		((IMG_BrushRGBA32*)brush)->setRadii(we,he);
	}
}



IMG_CanvasPtr IMG_CanvasCreate(unsigned int w, unsigned int h)
{
	IMG_CanvasPtr canvas = 0;
	try {
		canvas = new IMG_CanvasRGBA32 (w, h);
	}
	catch (...) {
		canvas = 0;
	}
	return canvas;
}


IMG_CanvasPtr IMG_CanvasCreateFromPtr(void* imagePtr, unsigned int w, unsigned int h, size_t rowBytes)
{
	IMG_CanvasPtr canvas = 0;
	try {
		canvas = new IMG_CanvasRGBA32 (imagePtr, w, h, rowBytes);
	}
	catch (...) {
		canvas = 0;
	}
	return canvas;
}

void IMG_CanvasDispose(IMG_CanvasPtr canvas)
{
	if (canvas) {
		delete ((IMG_CanvasRGBA32*)canvas);
		canvas = 0;
	}
}

#if 0
void IMG_CanvasDraw(IMG_CanvasPtr canvas, IMG_BrushPtr brush, unsigned int x, unsigned int y)
{
	if (!(canvas && brush)) return;
	((IMG_CanvasRGBA32*)canvas)->blendPixmap((TUns32)x, (TUns32)y, *((IMG_BrushRGBA32*)brush));
}


void IMG_CanvasDrawUV(IMG_CanvasPtr canvas, IMG_BrushPtr brush, float u, float v)
{
	if (!(canvas && brush)) return;
	((IMG_CanvasRGBA32*)canvas)->blendPixmap(u, v, *((IMG_BrushRGBA32*)brush));
}
#endif


void IMG_CanvasDrawLine(IMG_CanvasPtr canvas, IMG_BrushPtr brush, unsigned int xStart, unsigned int yStart, unsigned int xEnd, unsigned int yEnd)
{
	if (!(canvas && brush)) return;
	((IMG_CanvasRGBA32*)canvas)->blendPixmap((TUns32)xStart, (TUns32)yStart, (TUns32)xEnd, (TUns32)yEnd, *((IMG_BrushRGBA32*)brush));
}


void IMG_CanvasDrawLineUV(IMG_CanvasPtr canvas, IMG_BrushPtr brush, float uStart, float vStart, float uEnd, float vEnd)
{
	if (!(canvas && brush)) return;
	((IMG_CanvasRGBA32*)canvas)->blendPixmap(uStart, vStart, uEnd, vEnd, *((IMG_BrushRGBA32*)brush));
}

void IMG_CanvasDrawLineUVEX(IMG_CanvasPtr canvas, IMG_BrushPtr brush, float uStart, float vStart, float uEnd, float vEnd,char mode)
{
	if (!(canvas && brush)) return;
	((IMG_CanvasRGBA32*)canvas)->blendPixmap(uStart, vStart, uEnd, vEnd, *((IMG_BrushRGBA32*)brush),mode);
}

void IMG_CanvasSoftenAt(IMG_CanvasPtr canvas,float u, float v, unsigned int size,float alpha, float aspect,char mode)
{
	((IMG_CanvasRGBA32*)canvas)->SoftenAt(u,v,(TUns32)size,alpha,aspect,mode);
}

void IMG_CanvasFill(IMG_CanvasPtr canvas,float red, float green, float blue, float alpha)
{
		IMG_ColorRGB c (red, green, blue);
		IMG_Rect R (0, 0, ((IMG_CanvasRGBA32*)canvas)->getWidth(),
			              ((IMG_CanvasRGBA32*)canvas)->getHeight());	// Bounds of this pixmap
		((IMG_CanvasRGBA32*)canvas)->fillRect(R,c);
}

void IMG_CanvasSmear(IMG_CanvasPtr canvas,float uStart, float vStart, float uEnd, float vEnd, unsigned int size, float alpha, float aspect,char mode)
{
	((IMG_CanvasRGBA32*)canvas)->Smear(uStart,vStart,uEnd,vEnd,size,alpha,aspect,mode);

}

void IMG_CanvasCloneAt(IMG_CanvasPtr canvas,IMG_CanvasPtr other,float u,float v,float cu,float cv,int size,float alpha,float aspect)
{
     ((IMG_CanvasRGBA32*)canvas)->CloneAt((IMG_CanvasRGBA32*)other, u, v, cu, cv, size, alpha, aspect);
}


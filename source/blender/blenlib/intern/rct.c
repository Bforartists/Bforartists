/*
 * 
 * rct.c
 * 
 * april 95
 * 
 * $Id$
 *
 * A minimalist lib for functions doing stuff with rectangle structs.
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
 *
 */

#include "DNA_vec_types.h"
#include "BLI_blenlib.h"

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

int BLI_rcti_is_empty(rcti * rect)
{
	return ((rect->xmax<=rect->xmin) ||
			(rect->ymax<=rect->ymin));
}

int BLI_in_rcti(rcti * rect, int x, int y)
{

	if(x<rect->xmin) return 0;
	if(x>rect->xmax) return 0;
	if(y<rect->ymin) return 0;
	if(y>rect->ymax) return 0;
	return 1;
}

int BLI_in_rctf(rctf *rect, float x, float y)
{

	if(x<rect->xmin) return 0;
	if(x>rect->xmax) return 0;
	if(y<rect->ymin) return 0;
	if(y>rect->ymax) return 0;
	return 1;
}

void BLI_union_rctf(rctf *rct1, rctf *rct2)
{

	if(rct1->xmin>rct2->xmin) rct1->xmin= rct2->xmin;
	if(rct1->xmax<rct2->xmax) rct1->xmax= rct2->xmax;
	if(rct1->ymin>rct2->ymin) rct1->ymin= rct2->ymin;
	if(rct1->ymax<rct2->ymax) rct1->ymax= rct2->ymax;
}

void BLI_init_rctf(rctf *rect, float xmin, float xmax, float ymin, float ymax)
{
	rect->xmin= xmin;
	rect->xmax= xmax;
	rect->ymin= ymin;
	rect->ymax= ymax;
}
void BLI_init_rcti(rcti *rect, int xmin, int xmax, int ymin, int ymax)
{
	rect->xmin= xmin;
	rect->xmax= xmax;
	rect->ymin= ymin;
	rect->ymax= ymax;
}

void BLI_translate_rcti(rcti *rect, int x, int y)
{
	rect->xmin += x;
	rect->ymin += y;
	rect->xmax += x;
	rect->ymax += y;
}
void BLI_translate_rctf(rctf *rect, float x, float y)
{
	rect->xmin += x;
	rect->ymin += y;
	rect->xmax += x;
	rect->ymax += y;
}

int BLI_isect_rctf(rctf *src1, rctf *src2, rctf *dest)
{
	float xmin, xmax;
	float ymin, ymax;

	xmin = (src1->xmin) > (src2->xmin) ? (src1->xmin) : (src2->xmin);
	xmax = (src1->xmax) < (src2->xmax) ? (src1->xmax) : (src2->xmax);
	ymin = (src1->ymin) > (src2->ymin) ? (src1->ymin) : (src2->ymin);
	ymax = (src1->ymax) < (src2->ymax) ? (src1->ymax) : (src2->ymax);
	
	if(xmax>=xmin && ymax>=ymin) {
		if(dest) {
			dest->xmin = xmin;
			dest->xmax = xmax;
			dest->ymin = ymin;
			dest->ymax = ymax;
		}
		return 1;
	}
	else {
		if(dest) {
			dest->xmin = 0;
			dest->xmax = 0;
			dest->ymin = 0;
			dest->ymax = 0;
		}
		return 0;
	}
}

int BLI_isect_rcti(rcti *src1, rcti *src2, rcti *dest)
{
	int xmin, xmax;
	int ymin, ymax;
	
	xmin = (src1->xmin) > (src2->xmin) ? (src1->xmin) : (src2->xmin);
	xmax = (src1->xmax) < (src2->xmax) ? (src1->xmax) : (src2->xmax);
	ymin = (src1->ymin) > (src2->ymin) ? (src1->ymin) : (src2->ymin);
	ymax = (src1->ymax) < (src2->ymax) ? (src1->ymax) : (src2->ymax);
	
	if(xmax>=xmin && ymax>=ymin) {
		if(dest) {
			dest->xmin = xmin;
			dest->xmax = xmax;
			dest->ymin = ymin;
			dest->ymax = ymax;
		}
		return 1;
	}
	else {
		if(dest) {
			dest->xmin = 0;
			dest->xmax = 0;
			dest->ymin = 0;
			dest->ymax = 0;
		}
		return 0;
	}
}

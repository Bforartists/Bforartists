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
 * The Original Code is Copyright (C) 2005 Blender Foundation.
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): none yet.
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#ifndef DNA_BRUSH_TYPES_H
#define DNA_BRUSH_TYPES_H

#include "DNA_ID.h"

typedef struct Brush {
	ID id;
	
	short flag, blend;			/* general purpose flag, blend mode */
	int size;					/* brush diameter */
	float innerradius;			/* inner radius after which the falloff starts */
	float spacing;				/* spacing of paint operations */
	float rate;					/* paint operations / second (airbrush) */

	float rgb[3];				/* color */
	float alpha;				/* opacity */

	struct Clone {
		struct Image *image;	/* image for clone tool */
		float offset[2];		/* offset of clone image from canvas */
		float alpha;			/* transparency for drawing of clone image */
	} clone;
} Brush;

/* Brush.flag */
#define BRUSH_AIRBRUSH	1
#define BRUSH_TORUS		2

/* Brush.blend */
#define BRUSH_BLEND_MIX 	0
#define BRUSH_BLEND_ADD 	1
#define BRUSH_BLEND_SUB 	2
#define BRUSH_BLEND_MUL 	3
#define BRUSH_BLEND_LIGHTEN 4
#define BRUSH_BLEND_DARKEN	5

#define PAINT_TOOL_DRAW		0
#define PAINT_TOOL_SOFTEN	1
#define PAINT_TOOL_SMEAR	2
#define PAINT_TOOL_CLONE	3

#endif


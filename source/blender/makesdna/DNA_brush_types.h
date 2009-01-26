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

#ifndef MAX_MTEX
#define MAX_MTEX	18
#endif

struct CurveMapping;
struct MTex;
struct Image;

typedef struct BrushClone {
	struct Image *image;		/* image for clone tool */
	float offset[2];			/* offset of clone image from canvas */
	float alpha, pad;			/* transparency for drawing of clone image */
} BrushClone;

typedef struct Brush {
	ID id;

	struct BrushClone clone;

	struct CurveMapping *curve;		/* falloff curve */
	struct MTex *mtex[18];		/* MAX_MTEX */
	
	short flag, blend;			/* general purpose flag, blend mode */
	int size;					/* brush diameter */
	float innerradius;			/* inner radius after which the falloff starts */
	float spacing;				/* spacing of paint operations */
	float rate;					/* paint operations / second (airbrush) */

	float rgb[3];				/* color */
	float alpha;				/* opacity */

	float rot;				/* rotation in radians */

	short texact;				/* active texture */
	char sculpt_tool;			/* active tool */
	char tex_mode;
	
	char pad[4];
} Brush;

/* Brush.flag */
#define BRUSH_AIRBRUSH			1
#define BRUSH_TORUS				2
#define BRUSH_ALPHA_PRESSURE	4
#define BRUSH_SIZE_PRESSURE		8
#define BRUSH_RAD_PRESSURE		16
#define BRUSH_SPACING_PRESSURE	32
#define BRUSH_FIXED_TEX			64
#define BRUSH_RAKE		128
#define BRUSH_ANCHORED		256
#define BRUSH_DIR_IN		512
#define BRUSH_SPACE		1024

/* Brush.blend */
#define BRUSH_BLEND_MIX 		0
#define BRUSH_BLEND_ADD 		1
#define BRUSH_BLEND_SUB 		2
#define BRUSH_BLEND_MUL 		3
#define BRUSH_BLEND_LIGHTEN		4
#define BRUSH_BLEND_DARKEN		5
#define BRUSH_BLEND_ERASE_ALPHA	6
#define BRUSH_BLEND_ADD_ALPHA	7

/* Brush.tex_mode */
#define BRUSH_TEX_DRAG 0
#define BRUSH_TEX_TILE 1
#define BRUSH_TEX_3D   2

/* Brush.sculpt_tool */
#define SCULPT_TOOL_DRAW    1
#define SCULPT_TOOL_SMOOTH  2
#define SCULPT_TOOL_PINCH   3
#define SCULPT_TOOL_INFLATE 4
#define SCULPT_TOOL_GRAB    5
#define SCULPT_TOOL_LAYER   6
#define SCULPT_TOOL_FLATTEN 7

#define PAINT_TOOL_DRAW		0
#define PAINT_TOOL_SOFTEN	1
#define PAINT_TOOL_SMEAR	2
#define PAINT_TOOL_CLONE	3

#endif


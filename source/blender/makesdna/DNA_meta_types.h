/**
 * blenlib/DNA_meta_types.h (mar-2001 nzc)
 *
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
#ifndef DNA_META_TYPES_H
#define DNA_META_TYPES_H

#include "DNA_listBase.h"
#include "DNA_ID.h"

struct BoundBox;
struct Ipo;
struct Material;


typedef struct MetaElem {
	struct MetaElem *next, *prev;

	struct BoundBox *bb;		/* Bound Box of MetaElem */
	int i1,j1,k1, i2,j2,k2;		/* corners of Bounding Box in lattice */

	short type, lay, flag, selcol;
	float x, y, z;			/* Position of centre of MetaElem */
	float quat[4];			/* Rotation of MetaElem */
	float expx, expy, expz;		/* dx, dy, dz parameters */
	float rad, rad2, s, len;
	
	float *mat, *imat;
	
} MetaElem;

typedef struct MetaBall {
	ID id;
	
	struct BoundBox *bb;

	ListBase elems;
	ListBase disp;
	struct Ipo *ipo;

	struct Material **mat;

	short flag, totcol;
	int texflag;
	float loc[3];
	float size[3];
	float rot[3];
	float wiresize, rendersize, thresh;
	
} MetaBall;

/* **************** METABALL ********************* */

#define MB_MAXELEM		1024

/* texflag */
#define MB_AUTOSPACE	1

/* mb->flag */
#define MB_UPDATE_ALWAYS	0
#define MB_UPDATE_HALFRES	1
#define MB_UPDATE_FAST		2
#define MB_UPDATE_NEVER		3

/* ml->type */
#define MB_BALL		0
#define MB_TUBEX	1
#define MB_TUBEY	2
#define MB_TUBEZ	3
#define MB_TUBE		4
#define MB_PLANE	5
#define MB_ELIPSOID	6
#define MB_CUBE 	7

/* ml->flag */
#define MB_NEGATIVE	2
#define MB_HIDE		8

#endif


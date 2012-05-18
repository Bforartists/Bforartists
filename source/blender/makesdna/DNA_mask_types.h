/*
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
 * Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
 *
 * The Original Code is Copyright (C) 2012 Blender Foundation.
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): Blender Foundation,
 *                 Sergey Sharybin
 *
 * ***** END GPL LICENSE BLOCK *****
 */

/** \file DNA_mask_types.h
 *  \ingroup DNA
 *  \since march-2012
 *  \author Sergey Sharybin
 */

#ifndef __DNA_MASK_TYPES_H__
#define __DNA_MASK_TYPES_H__

#include "DNA_defs.h"
#include "DNA_ID.h"
#include "DNA_listBase.h"
#include "DNA_curve_types.h"

typedef struct Mask {
	ID id;
	struct AnimData *adt;
	ListBase shapes;     /* shapes which defines this mask */
	int shapenr;         /* index of active shape */
	int tot_shape;       /* total number of shapes */
} Mask;

typedef struct MaskParent {
	int flag;             /* parenting flags */
	int id_type;          /* type of parenting */
	ID *id;               /* ID block of entity to which mask/spline is parented to
	                       * in case of parenting to movie tracking data set to MovieClip datablock */
	char parent[64];      /* entity of parent to which parenting happened
	                       * in case of parenting to movie tracking data contains name of object */
	char sub_parent[64];  /* sub-entity of parent to which parenting happened
	                       * in case of parenting to movie tracking data contains name of track */
	float offset[2];      /* offset from parent position, so object/control point can be parented to a
	                       * motion track and also be animated (see ZanQdo's request below)  */
} MaskParent;

typedef struct MaskSplinePointUW {
	float u, w;            /* u coordinate along spline segment and weight of this point */
	int flag;              /* different flags of this point */
} MaskSplinePointUW;

typedef struct MaskSplinePoint {
	BezTriple bezt;        /* actual point coordinates and it's handles  */
	int pad;
	int tot_uw;            /* number of uv feather values */
	MaskSplinePointUW *uw; /* feather UV values */
	MaskParent parent;     /* parenting information of particular spline point */
} MaskSplinePoint;

typedef struct MaskSpline {
	struct MaskSpline *next, *prev;

	int flag;                /* defferent spline flag (closed, ...) */
	int tot_point;           /* total number of points */
	MaskSplinePoint *points; /* points which defines spline itself */
	MaskParent parent;       /* parenting information of the whole spline */

	int weight_interp, pad;  /* weight interpolation */
} MaskSpline;

typedef struct MaskShape {
	struct MaskShape *next, *prev;

	char name[64];                     /* name of the shape (64 = MAD_ID_NAME - 2) */

	ListBase splines;                  /* list of splines which defines this shape */
	struct MaskSpline *act_spline;     /* active spline */
	struct MaskSplinePoint *act_point; /* active point */
} MaskShape;

/* MaskParent->flag */
#define MASK_PARENT_ACTIVE  (1 << 0)

/* MaskSpline->flag */
#define MASK_SPLINE_CYCLIC  (1 << 1)

/* MaskSpline->weight_interp */
#define MASK_SPLINE_INTERP_LINEAR   1
#define MASK_SPLINE_INTERP_EASE     2

#endif // __DNA_MASK_TYPES_H__

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
 * Constraint DNA data
 */

#ifndef DNA_CONSTRAINT_TYPES_H
#define DNA_CONSTRAINT_TYPES_H

#include "DNA_ID.h"
#include "DNA_ipo_types.h"
#include "DNA_object_types.h"

struct Action;

/* channels reside in Object or Action (ListBase) constraintChannels */
typedef struct bConstraintChannel{
	struct bConstraintChannel *next, *prev;
	Ipo			*ipo;
	short		flag;
	char		name[30];
} bConstraintChannel;

typedef struct bConstraint{
	struct bConstraint *next, *prev;
	void		*data;		/*	Constraint data	(a valid constraint type) */
	short		type;		/*	Constraint type	*/
	short		flag;		/*	Flag */
	short		reserved1;	
	char		name[30];	/*	Constraint name	*/

	float		enforce;
} bConstraint;

/* Single-target subobject constraints */
typedef struct bKinematicConstraint{
	Object		*tar;
	float		tolerance;		/* Acceptable distance from target */
	short		iterations;		/* Maximum number of iterations to try */
	short		flag;			/* Like IK to Tip */
	char		subtarget[32];	/* String to specify sub-object target */


} bKinematicConstraint;

typedef struct bTrackToConstraint{
	Object		*tar;
	int			reserved1; /* I'll be using reserved1 and reserved2 as Track and Up flags, not sure if that's what they were intented for anyway. Not sure either if it would create backward incompatibility if I were to rename them. - theeth*/
	int			reserved2;
	char		subtarget[32];
} bTrackToConstraint;

typedef struct bRotateLikeConstraint{
	Object		*tar;
	int			flag;
	int			reserved1;
	char		subtarget[32];
} bRotateLikeConstraint;

typedef struct bLocateLikeConstraint{
	Object		*tar;
	int			flag;
	int			reserved1;
	char		subtarget[32];
} bLocateLikeConstraint;

typedef struct bActionConstraint{
	Object		*tar;
	short		type;
	short		local;
	short		start;
	short		end;
	float		min;
	float		max;
	struct bAction	*act;
	char		subtarget[32];
} bActionConstraint;

/* Locked Axis Tracking constraint */
typedef struct bLockTrackConstraint{
	Object		*tar;
	int			trackflag;
	int			lockflag;
	char		subtarget[32];
} bLockTrackConstraint;

/* Follow Path constraints */
typedef struct bFollowPathConstraint{
	Object		*tar;	/* Must be path object */
	float		offset; /* Offset in time on the path (in frame) */
	int			followflag;
	int			trackflag;
	int			upflag;
} bFollowPathConstraint;

/* Distance Limiting constraints */
typedef struct bDistanceLimitConstraint{
	Object	*tar;
	char		subtarget[32];
	float		pad1;
	float		pad2;
	float		distance;
	float		offset[3];
} bDistanceLimitConstraint;	


/* Zero-target constraints */
typedef struct bRotationConstraint{
	float xmin, xmax;
	float ymin, ymax;
	float zmin, zmax;
} bRotationConstraint;

/* Stretch to constraint */
typedef struct bStretchToConstraint{
	Object		*tar;
	int			volmode; 
	int         plane;
	float		orglength;
	float		bulge;
	char		subtarget[32];
} bStretchToConstraint;


/* bConstraint.type */
#define CONSTRAINT_TYPE_NULL		0
#define CONSTRAINT_TYPE_CHILDOF		1	/* Unimplemented */
#define CONSTRAINT_TYPE_TRACKTO		2	
#define CONSTRAINT_TYPE_KINEMATIC	3	
#define CONSTRAINT_TYPE_FOLLOWPATH	4
#define CONSTRAINT_TYPE_ROTLIMIT	5	/* Unimplemented */
#define CONSTRAINT_TYPE_LOCLIMIT	6	/* Unimplemented */
#define CONSTRAINT_TYPE_SIZELIMIT	7	/* Unimplemented */
#define CONSTRAINT_TYPE_ROTLIKE		8	
#define CONSTRAINT_TYPE_LOCLIKE		9	
#define CONSTRAINT_TYPE_SIZELIKE	10	/* Unimplemented */
#define CONSTRAINT_TYPE_PYTHON		11	/* Unimplemented */
#define CONSTRAINT_TYPE_ACTION		12
#define CONSTRAINT_TYPE_LOCKTRACK	13	/* New Tracking constraint that locks an axis in place - theeth */
#define CONSTRAINT_TYPE_DISTANCELIMIT	14 
#define CONSTRAINT_TYPE_STRETCHTO	15  /* claiming this to be mine :) is in tuhopuu bjornmose */ 


/* bConstraint.flag */
		/* expand for UI */
#define CONSTRAINT_EXPAND		0x01
		/* pre-check for illegal object name or bone name */
#define CONSTRAINT_DISABLE		0x04
		/* flags 0x2 and 0x8 were used in past, skip this */
		/* to indicate which Ipo should be shown, maybe for 3d access later too */
#define CONSTRAINT_ACTIVE		0x10

/* bConstraintChannel.flag */
#define CONSTRAINT_CHANNEL_SELECT	0x01

/* bLocateLikeConstraint.flag */
#define LOCLIKE_X		0x01
#define LOCLIKE_Y		0x02
#define LOCLIKE_Z		0x04
#define LOCSPACE		0x08

/* Axis flags */
#define LOCK_X		0x00
#define LOCK_Y		0x01
#define LOCK_Z		0x02

#define UP_X		0x00
#define UP_Y		0x01
#define UP_Z		0x02

#define TRACK_X		0x00
#define TRACK_Y		0x01
#define TRACK_Z		0x02
#define TRACK_nX	0x03
#define TRACK_nY	0x04
#define TRACK_nZ	0x05

#define VOLUME_XZ	0x00
#define VOLUME_X	0x01
#define VOLUME_Z	0x02
#define NO_VOLUME	0x03

#define PLANE_X		0x00
#define PLANE_Y		0x01
#define PLANE_Z		0x02

/* bKinematicConstraint->flag */
#define CONSTRAINT_IK_TIP		1

#endif


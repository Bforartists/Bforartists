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
 * Contributor(s): Full recode, Ton Roosendaal, Crete 2005
 *
 * ***** END GPL/BL DUAL LICENSE BLOCK *****
 */

#ifndef DNA_ARMATURE_TYPES_H
#define DNA_ARMATURE_TYPES_H

#include "DNA_listBase.h"
#include "DNA_ID.h"

/* this system works on different transformation space levels;

1) Bone Space;		with each Bone having own (0,0,0) origin
2) Armature Space;  the rest position, in Object space, Bones Spaces are applied hierarchical
3) Pose Space;		the animation position, in Object space
4) World Space;		Object matrix applied to Pose or Armature space

*/

typedef struct Bone {
	struct Bone		*next, *prev;	/*	Next/prev elements within this list	*/
	struct Bone		*parent;		/*	Parent (ik parent if appropriate flag is set		*/
	ListBase		childbase;		/*	Children	*/
	char			name[32];		/*  Name of the bone - must be unique within the armature */

	float			roll;   /*  roll is input for editmode, length calculated */
	float			head[3];		
	float			tail[3];		/*	head/tail and roll in Bone Space	*/
	float			bone_mat[3][3]; /*  rotation derived from head/tail/roll */
	
	int				flag;
	
	float			arm_head[3];		
	float			arm_tail[3];	/*	head/tail and roll in Armature Space (rest pos) */
	float			arm_mat[4][4];  /*  matrix: (bonemat(b)+head(b))*arm_mat(b-1), rest pos*/
	
	float			dist, weight;			/*  dist, weight: for non-deformgroup deforms */
	float			xwidth, length, zwidth;	/*  width: for block bones. keep in this order, transform! */
	float			ease1, ease2;			/*  length of bezier handles */
	float			rad_head, rad_tail;	/* radius for head/tail sphere, defining deform as well, parent->rad_tip overrides rad_head*/
	
	float			size[3];		/*  patch for upward compat, UNUSED! */
	short			layer;
	short			segments;		/*  for B-bones */
} Bone;

typedef struct bArmature {
	ID			id;
	ListBase	bonebase;
	ListBase	chainbase;
	int			flag;
	int			drawtype;			
	short		deformflag; 
	short		pathflag;
	short		layer, layer_protected;		/* for buttons to work, both variables in this order together */
	short		ghostep, ghostsize;		/* number of frames to ghosts to show, and step between them  */
	short		ghosttype, pathsize;		/* ghost drawing options and number of frames between points of path */
	int			ghostsf, ghostef;		/* start and end frames of ghost-drawing range */
	int 		pathsf, pathef;			/* start and end frames of path-calculation range for all bones */
	int			pathbc, pathac;			/* number of frames before/after current frame of path-calculation for all bones  */
} bArmature;

/* armature->flag */
/* dont use bit 7, was saved in files to disable stuff */
typedef enum eArmature_Flag {
	ARM_RESTPOS			= (1<<0),
	ARM_DRAWXRAY		= (1<<1),	/* XRAY is here only for backwards converting */
	ARM_DRAWAXES		= (1<<2),
	ARM_DRAWNAMES		= (1<<3), 
	ARM_POSEMODE		= (1<<4), 
	ARM_EDITMODE		= (1<<5), 
	ARM_DELAYDEFORM 	= (1<<6), 
	ARM_DONT_USE    	= (1<<7),
	ARM_MIRROR_EDIT		= (1<<8),
	ARM_AUTO_IK			= (1<<9),
	ARM_NO_CUSTOM		= (1<<10), 	/* made option negative, for backwards compat */
	ARM_COL_CUSTOM		= (1<<11),	/* draw custom colours  */
	ARM_GHOST_ONLYSEL 	= (1<<12)	/* when ghosting, only show selected bones (this should belong to ghostflag instead) */
} eArmature_Flag;

/* armature->drawtype */
typedef enum eArmature_Drawtype {
	ARM_OCTA = 0,
	ARM_LINE,
	ARM_B_BONE,
	ARM_ENVELOPE
} eArmature_Drawtype;

/* armature->deformflag */
typedef enum eArmature_DeformFlag {
	ARM_DEF_VGROUP			= (1<<0),
	ARM_DEF_ENVELOPE		= (1<<1),
	ARM_DEF_QUATERNION		= (1<<2),
	ARM_DEF_B_BONE_REST		= (1<<3),
	ARM_DEF_INVERT_VGROUP	= (1<<4)
} eArmature_DeformFlag;

/* armature->pathflag */
typedef enum eArmature_PathFlag {
	ARM_PATH_FNUMS		= (1<<0),
	ARM_PATH_KFRAS		= (1<<1),
	ARM_PATH_HEADS		= (1<<2),
	ARM_PATH_ACFRA		= (1<<3),
	ARM_PATH_KFNOS		= (1<<4)
} eArmature_PathFlag;

/* armature->ghosttype */
typedef enum eArmature_GhostType {
	ARM_GHOST_CUR = 0,
	ARM_GHOST_RANGE,
	ARM_GHOST_KEYS
} eArmature_GhostType;

/* bone->flag */
typedef enum eBone_Flag {
	BONE_SELECTED 				= (1<<0),
	BONE_ROOTSEL				= (1<<1),
	BONE_TIPSEL					= (1<<2),
	BONE_TRANSFORM  			= (1<<3),	/* Used instead of BONE_SELECTED during transform */
	BONE_CONNECTED 				= (1<<4),	/* when bone has a parent, connect head of bone to parent's tail*/
	/* 32 used to be quatrot, was always set in files, do not reuse unless you clear it always */	
	BONE_HIDDEN_P				= (1<<6), 	/* hidden Bones when drawing PoseChannels */	
	BONE_DONE					= (1<<7),	/* For detecting cyclic dependancies */
	BONE_ACTIVE					= (1<<8), 	/* active is on mouse clicks only */
	BONE_HINGE					= (1<<9),	/* No parent rotation or scale */
	BONE_HIDDEN_A				= (1<<10), 	/* hidden Bones when drawing Armature Editmode */
	BONE_MULT_VG_ENV 			= (1<<11), 	/* multiplies vgroup with envelope */
	BONE_NO_DEFORM				= (1<<12),	/* bone doesn't deform geometry */
	BONE_UNKEYED				= (1<<13), 	/* set to prevent destruction of its unkeyframed pose (after transform) */		
	BONE_HINGE_CHILD_TRANSFORM 	= (1<<14), 	/* set to prevent hinge child bones from influencing the transform center */
	BONE_NO_SCALE				= (1<<15), 	/* No parent scale */
	BONE_HIDDEN_PG				= (1<<16),	/* hidden bone when drawing PoseChannels (for ghost drawing) */
	BONE_DRAWWIRE				= (1<<17),	/* bone should be drawn as OB_WIRE, regardless of draw-types of view+armature */
	BONE_NO_CYCLICOFFSET		= (1<<18)	/* when no parent, bone will not get cyclic offset */
} eBone_Flag;

#endif

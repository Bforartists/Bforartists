/*  BKE_action.h   May 2001
 *  
 *  Blender kernel action functionality
 *
 *	Reevan McKay
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

#ifndef BKE_ACTION_H
#define BKE_ACTION_H

#include "DNA_listBase.h"

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

/**
 * The following structures are defined in DNA_action_types.h
 */

struct bAction;
struct bActionChannel;
struct bPose;
struct bPoseChannel;
struct Object;

/* Kernel prototypes */
#ifdef __cplusplus
extern "C" {
#endif

/**
 * Allocate a new pose channel on the heap and binary copy the 
 * contents of the src pose channel.
 */
	struct bPoseChannel *
copy_pose_channel (
	const struct bPoseChannel *src
);

/**
 * Removes and deallocates all channels from a pose.
 * Does not free the pose itself.
 */
	void	
clear_pose (
	struct bPose *pose
);

/* Sets the value of a pose channel */
	struct bPoseChannel *
set_pose_channel (
	struct bPose *pose, 
	struct bPoseChannel *chan
);

/**
 * Allocate a new pose on the heap, and copy the src pose and it's channels
 * into the new pose. *dst is set to the newly allocated structure.
 */ 
	void	
copy_pose(
	struct bPose **dst, 
	const struct bPose *src, 
	int copyconstraints
);

/**
 * Deallocate the action's channels including constraint channels.
 * does not free the action structure.
 */
	void	
free_action(
	struct bAction * id
);

	void	
make_local_action(
	struct bAction *act
);

	void	
do_all_actions(
	void
);

/**
 * Return a pointer to the pose channel of the given name
 * from this pose.
 */
 
	struct	bPoseChannel *
get_pose_channel (
	const struct bPose *pose,
	const char *name
);

/** 
 * Looks to see if the channel with the given name
 * already exists in this pose - if not a new one is
 * allocated and initialized.
 */
	void	
verify_pose_channel (
	struct bPose* pose,
	const char* name
);
	
/**
 * Allocate a new bAction on the heap and copy 
 * the contents of src into it. If src is NULL NULL is returned.
 */

	struct	bAction* 
copy_action(
	const struct bAction *src
);

/**
 * Some kind of bounding box operation on the action.
 */

	float	
calc_action_start (
	const struct bAction *act
);

	float	
calc_action_end (
	const struct bAction *act
);

/**
 * Evaluate the pose from the given action.
 * If the pose does not exist, a new one is created.
 * Some deep calls into blender are made here.
 */
	void	
get_pose_from_action (
	struct bPose **pose,
	struct bAction *act,
	float ctime
);

/**
 * I think this duplicates the src into *pose.
 * If the pose does not exist, a new one is created.
 * If the pose does not contain channels from src
 * new channels are created.
 */ 
	void	
get_pose_from_pose (
	struct bPose **pose,
	const struct bPose *src
);

	void	
clear_pose_constraint_status (
	struct Object *ob
);

/**
 * Blends the common subset of channels from dst and src.
 * and writes result to dst.
 */
	void	
blend_poses (
	struct bPose *dst,
	const struct bPose *src,
	float srcweight,
	short mode
);

/**
 * Iterate through the action channels of the action
 * and return the channel with the given name.
 * Returns NULL if no channel.
 */

	struct bActionChannel *
get_named_actionchannel (
	struct bAction *act,
	const char *name
);

#ifdef __cplusplus
};
#endif

enum	{
			POSE_BLEND		= 0,
			POSE_ADD
};

enum	{
			POSE_KEY		=	0x10000000,
			POSE_LOC		=	0x00000001,
			POSE_ROT		=	0x00000002,
			POSE_SIZE		=	0x00000004,
			POSE_UNUSED1	=	0x00000008,
			POSE_UNUSED2	=	0x00000010,
			POSE_UNUSED3	=	0x00000020,
			POSE_UNUSED4	=	0x00000040,
			POSE_UNUSED5	=	0x00000080,
			POSE_OBMAT		=	0x00000100,
			POSE_PARMAT		=	0x00000200,
			PCHAN_DONE		=	0x00000400

};

#endif


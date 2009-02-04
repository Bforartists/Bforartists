/**
 * $Id:
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
 * The Original Code is Copyright (C) 2008 Blender Foundation.
 * All rights reserved.
 *
 * 
 * Contributor(s): Blender Foundation, Joshua Leung
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#include <stdlib.h>
#include <math.h>

#include "MEM_guardedalloc.h"

#include "DNA_action_types.h"
#include "DNA_armature_types.h"
#include "DNA_object_types.h"
#include "DNA_scene_types.h"

#include "BLI_blenlib.h"

#include "BKE_action.h"
#include "BKE_context.h"
#include "BKE_depsgraph.h"
#include "BKE_main.h"
#include "BKE_scene.h"
#include "BKE_utildefines.h"

#include "RNA_access.h"
#include "RNA_define.h"

#include "ED_anim_api.h"
#include "ED_screen.h"

#include "WM_api.h"
#include "WM_types.h"

/* ***************** depsgraph calls and anim updates ************* */
/* ***************** only these can be called from editors ******** */

/* generic update flush, reads from context Screen (layers) and scene */
/* this is for compliancy, later it can do all windows etc */
void ED_anim_dag_flush_update(const bContext *C)
{
	Scene *scene= CTX_data_scene(C);
	bScreen *screen= CTX_wm_screen(C);
	
	DAG_scene_flush_update(scene, ED_screen_view3d_layers(screen), 0);
}

/* flushes changes from object to all relations in scene */
void ED_anim_object_flush_update(const bContext *C, Object *ob)
{
	Scene *scene= CTX_data_scene(C);
	bScreen *screen= CTX_wm_screen(C);
	
	DAG_object_update_flags(scene, ob, ED_screen_view3d_layers(screen));
}


/* **************************** animation tool notifiers ******************************** */

/* Send notifiers on behalf of animation editing tools, based on various context info 
 *	- data_changed: eAnimData_Changed
 */
void ANIM_animdata_send_notifiers (bContext *C, bAnimContext *ac, short data_changed)
{
	/* types of notifiers to send, depends on the editor context */
	switch (ac->datatype) {
		case ANIMCONT_DOPESHEET: /* dopesheet */
		case ANIMCONT_FCURVES: /* fcurve editor */
		case ANIMCONT_DRIVERS: /* drivers editor */	// XXX probably this will need separate handling, since these are part of dependency system 
		{
			/* what action was taken */
			switch (data_changed) {
				case ANIM_CHANGED_KEYFRAMES_VALUES:
					/* keyframe values changed, so transform may have changed */
					// XXX what about other cases? maybe we need general ND_KEYFRAMES or ND_ANIMATION?
					WM_event_add_notifier(C, NC_OBJECT|ND_TRANSFORM, NULL);
					break;
				case ANIM_CHANGED_KEYFRAMES_SELECT:	// XXX what to do here?
					WM_event_add_notifier(C, NC_SCENE, NULL);
					break;
				case ANIM_CHANGED_CHANNELS:
					// XXX err... check available datatypes in dopesheet first?
					// FIXME: this currently doesn't work (to update own view)
					WM_event_add_notifier(C, NC_SCENE|ND_OB_ACTIVE|ND_OB_SELECT, ac->scene);
					WM_event_add_notifier(C, NC_OBJECT|ND_BONE_ACTIVE|ND_BONE_SELECT, NULL);
					break;
			}
			
			// XXX for now, at least update own editor!
			ED_area_tag_redraw(CTX_wm_area(C));
		}
			break;
		
		case ANIMCONT_ACTION: /* action editor */
		{
			Object *obact= CTX_data_active_object(C);
			
			// only update active object for now... more detail to come!
			WM_event_add_notifier(C, NC_OBJECT, obact);
		}
			break;
			
		default: /* some other data... just update area for now */
			ED_area_tag_redraw(CTX_wm_area(C)); 
	}
}

/* **************************** pose <-> action syncing ******************************** */
/* Summary of what needs to be synced between poses and actions:
 *	1) Flags
 *		a) Visibility (only for pose to action) 
 *		b) Selection status (both ways)
 *	2) Group settings  (only for pose to action) - do we also need to make sure same groups exist?
 *	3) Grouping (only for pose to action for now)
 */

/* Notifier from Action/Dopesheet (this may be extended to include other things such as Python...)
 * Channels in action changed, so update pose channels/groups to reflect changes.
 *
 * An object (usually 'active' Object) needs to be supplied, so that its Pose-Channels can be synced with
 * the channels in its active Action.
 */
void ANIM_action_to_pose_sync (Object *ob)
{
	bAction *act= (bAction *)ob->action;
	bActionChannel *achan;
	bPoseChannel *pchan;
	
	/* error checking */
	if ((ob == NULL) || (ob->type != OB_ARMATURE) || ELEM(NULL, act, ob->pose))
		return;
	
	/* 1b) loop through all Action-Channels (there should be fewer channels to search through here in general) */
	for (achan= act->chanbase.first; achan; achan= achan->next) {
		/* find matching pose-channel */
		pchan= get_pose_channel(ob->pose, achan->name);
		
		/* sync active and selected flags */
		if (pchan && pchan->bone) {
			/* selection */
			if (achan->flag & ACHAN_SELECTED)
				pchan->bone->flag |= BONE_SELECTED;
			else
				pchan->bone->flag &= ~BONE_SELECTED;
			
			/* active */
			if (achan->flag & ACHAN_HILIGHTED)
				pchan->bone->flag |= BONE_ACTIVE;
			else
				pchan->bone->flag &= ~BONE_ACTIVE;
		}
	}
	
	// TODO: add grouping changes too? For now, these tools aren't exposed to users in animation editors yet...
} 
 
/* Notifier from 3D-View/Outliner (this is likely to include other sources too...)
 * Pose channels/groups changed, so update action channels
 *
 * An object (usually 'active' Object) needs to be supplied, so that its Pose-Channels can be synced with
 * the channels in its active Action.
 */
void ANIM_pose_to_action_sync (Object *ob, ScrArea *sa)
{
	SpaceAction *saction= (SpaceAction *)sa->spacedata.first;
	bArmature *arm= (bArmature *)ob->data;
	bAction *act= (bAction *)ob->action;
	bActionChannel *achan;
	//bActionGroup *agrp, *bgrp;
	bPoseChannel *pchan;
	
	/* error checking */
	if ((ob == NULL) || (ob->type != OB_ARMATURE) || ELEM3(NULL, arm, act, ob->pose))
		return;
		
	/* 1) loop through all Action-Channels (there should be fewer channels to search through here in general) */
	for (achan= act->chanbase.first; achan; achan= achan->next) {
		/* find matching pose-channel */
		pchan= get_pose_channel(ob->pose, achan->name);
		
		/* sync selection and visibility settings */
		if (pchan && pchan->bone) {
			/* visibility - if layer is hidden, or if bone itself is hidden */
			if (!(saction->flag & SACTION_NOHIDE) && !(saction->pin)) {
				if (!(pchan->bone->layer & arm->layer) || (pchan->bone->flag & BONE_HIDDEN_P))
					achan->flag |= ACHAN_HIDDEN;
				else
					achan->flag &= ~ACHAN_HIDDEN;
			}
				
			/* selection */
			if (pchan->bone->flag & BONE_SELECTED)
				achan->flag |= ACHAN_SELECTED;
			else
				achan->flag &= ~ACHAN_SELECTED;
		}
	}
	
	// XXX step 2 needs to be coded still... currently missing action/bone group API to do any more work here...	
	// XXX step 3 needs to be coded still... it's a messy case to deal with (we'll use the temp indices for this?)
}

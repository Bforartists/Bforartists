/**
 * $Id: editaction.c 17746 2008-12-08 11:19:44Z aligorith $
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
 * The Original Code is Copyright (C) 2001-2002 by NaN Holding BV.
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): Joshua Leung
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#include <math.h>
#include <stdlib.h>
#include <string.h>
#include <float.h>

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

#include "MEM_guardedalloc.h"

#include "BLI_blenlib.h"
#include "BLI_arithb.h"

#include "DNA_listBase.h"
#include "DNA_anim_types.h"
#include "DNA_action_types.h"
#include "DNA_armature_types.h"
#include "DNA_camera_types.h"
#include "DNA_curve_types.h"
#include "DNA_object_types.h"
#include "DNA_screen_types.h"
#include "DNA_scene_types.h"
#include "DNA_space_types.h"
#include "DNA_constraint_types.h"
#include "DNA_key_types.h"
#include "DNA_lamp_types.h"
#include "DNA_material_types.h"
#include "DNA_userdef_types.h"
#include "DNA_gpencil_types.h"
#include "DNA_windowmanager_types.h"
#include "DNA_world_types.h"

#include "RNA_access.h"
#include "RNA_define.h"

#include "BKE_action.h"
#include "BKE_depsgraph.h"
#include "BKE_ipo.h"
#include "BKE_key.h"
#include "BKE_material.h"
#include "BKE_object.h"
#include "BKE_context.h"
#include "BKE_utildefines.h"

#include "UI_interface.h"
#include "UI_resources.h"
#include "UI_view2d.h"

#include "ED_anim_api.h"
#include "ED_keyframes_edit.h" // XXX move the select modes out of there!
#include "ED_screen.h"
#include "ED_space_api.h"

#include "WM_api.h"
#include "WM_types.h"

/* ************************************************************************** */
/* CHANNELS API */

/* -------------------------- Internal Macros ------------------------------- */

/* set/clear/toggle macro 
 *	- channel - channel with a 'flag' member that we're setting
 *	- smode - 0=clear, 1=set, 2=toggle
 *	- sflag - bitflag to set
 */
#define ACHANNEL_SET_FLAG(channel, smode, sflag) \
	{ \
		if (smode == ACHANNEL_SETFLAG_TOGGLE) 	(channel)->flag ^= (sflag); \
		else if (smode == ACHANNEL_SETFLAG_ADD) (channel)->flag |= (sflag); \
		else 									(channel)->flag &= ~(sflag); \
	}
	
/* set/clear/toggle macro, where the flag is negative 
 *	- channel - channel with a 'flag' member that we're setting
 *	- smode - 0=clear, 1=set, 2=toggle
 *	- sflag - bitflag to set
 */
#define ACHANNEL_SET_FLAG_NEG(channel, smode, sflag) \
	{ \
		if (smode == ACHANNEL_SETFLAG_TOGGLE) 	(channel)->flag ^= (sflag); \
		else if (smode == ACHANNEL_SETFLAG_ADD) (channel)->flag &= ~(sflag); \
		else 									(channel)->flag |= (sflag); \
	}

/* -------------------------- Exposed API ----------------------------------- */

/* Set the given animation-channel as the active one for the active context */
void ANIM_set_active_channel (void *data, short datatype, int filter, void *channel_data, short channel_type)
{
	ListBase anim_data = {NULL, NULL};
	bAnimListElem *ale;
	
	/* try to build list of filtered items */
	// XXX we don't need/supply animcontext for now, since in this case, there's nothing really essential there that isn't already covered
	ANIM_animdata_filter(NULL, &anim_data, filter, data, datatype);
	if (anim_data.first == NULL)
		return;
		
	/* only clear the 'active' flag for the channels of the same type */
	for (ale= anim_data.first; ale; ale= ale->next) {
		/* skip if types don't match */
		if (channel_type != ale->type)
			continue;
		
		/* flag to set depends on type */
		switch (ale->type) {
			case ANIMTYPE_GROUP:
			{
				bActionGroup *agrp= (bActionGroup *)ale->data;
				
				ACHANNEL_SET_FLAG(agrp, ACHANNEL_SETFLAG_CLEAR, AGRP_ACTIVE);
			}
				break;
			case ANIMTYPE_FCURVE:
			{
				FCurve *fcu= (FCurve *)ale->data;
				
				ACHANNEL_SET_FLAG(fcu, ACHANNEL_SETFLAG_CLEAR, FCURVE_ACTIVE);
			}
				break;
			case ANIMTYPE_NLATRACK:
			{
				NlaTrack *nlt= (NlaTrack *)ale->data;
				
				ACHANNEL_SET_FLAG(nlt, ACHANNEL_SETFLAG_CLEAR, NLATRACK_ACTIVE);
			}
				break;
		}
	}
	
	/* set active flag */
	if (channel_data) {
		switch (channel_type) {
			case ANIMTYPE_GROUP:
			{
				bActionGroup *agrp= (bActionGroup *)channel_data;
				agrp->flag |= AGRP_ACTIVE;
			}
				break;
			case ANIMTYPE_FCURVE:
			{
				FCurve *fcu= (FCurve *)channel_data;
				fcu->flag |= FCURVE_ACTIVE;
			}
				break;
			case ANIMTYPE_NLATRACK:
			{
				NlaTrack *nlt= (NlaTrack *)channel_data;
				
				ACHANNEL_SET_FLAG(nlt, ACHANNEL_SETFLAG_CLEAR, NLATRACK_ACTIVE);
			}
				break;
		}
	}
	
	/* clean up */
	BLI_freelistN(&anim_data);
}

/* Deselect all animation channels 
 *	- data: pointer to datatype, as contained in bAnimContext
 *	- datatype: the type of data that 'data' represents (eAnimCont_Types)
 *	- test: check if deselecting instead of selecting
 *	- sel: eAnimChannels_SetFlag;
 */
void ANIM_deselect_anim_channels (void *data, short datatype, short test, short sel)
{
	ListBase anim_data = {NULL, NULL};
	bAnimListElem *ale;
	int filter;
	
	/* filter data */
	filter= ANIMFILTER_VISIBLE;
	ANIM_animdata_filter(NULL, &anim_data, filter, data, datatype);
	
	/* See if we should be selecting or deselecting */
	if (test) {
		for (ale= anim_data.first; ale; ale= ale->next) {
			if (sel == 0) 
				break;
			
			switch (ale->type) {
				case ANIMTYPE_SCENE:
					if (ale->flag & SCE_DS_SELECTED)
						sel= ACHANNEL_SETFLAG_CLEAR;
					break;
				case ANIMTYPE_OBJECT:
					if (ale->flag & SELECT)
						sel= ACHANNEL_SETFLAG_CLEAR;
					break;
				case ANIMTYPE_FILLACTD:
					if (ale->flag & ACT_SELECTED)
						sel= ACHANNEL_SETFLAG_CLEAR;
					break;
				case ANIMTYPE_GROUP:
					if (ale->flag & AGRP_SELECTED)
						sel= ACHANNEL_SETFLAG_CLEAR;
					break;
				case ANIMTYPE_FCURVE:
					if (ale->flag & FCURVE_SELECTED)
						sel= ACHANNEL_SETFLAG_CLEAR;
					break;
				case ANIMTYPE_NLATRACK:
					if (ale->flag & NLATRACK_SELECTED)
						sel= ACHANNEL_SETFLAG_CLEAR;
					break;
			}
		}
	}
		
	/* Now set the flags */
	for (ale= anim_data.first; ale; ale= ale->next) {
		switch (ale->type) {
			case ANIMTYPE_SCENE:
			{
				Scene *scene= (Scene *)ale->data;
				
				ACHANNEL_SET_FLAG(scene, sel, SCE_DS_SELECTED);
			}
				break;
			case ANIMTYPE_OBJECT:
			{
				Base *base= (Base *)ale->data;
				Object *ob= base->object;
				
				ACHANNEL_SET_FLAG(base, sel, SELECT);
				ACHANNEL_SET_FLAG(ob, sel, SELECT);
			}
				break;
			case ANIMTYPE_FILLACTD:
			{
				bAction *act= (bAction *)ale->data;
				
				ACHANNEL_SET_FLAG(act, sel, ACT_SELECTED);
			}
				break;
			case ANIMTYPE_GROUP:
			{
				bActionGroup *agrp= (bActionGroup *)ale->data;
				
				ACHANNEL_SET_FLAG(agrp, sel, AGRP_SELECTED);
				agrp->flag &= ~AGRP_ACTIVE;
			}
				break;
			case ANIMTYPE_FCURVE:
			{
				FCurve *fcu= (FCurve *)ale->data;
				
				ACHANNEL_SET_FLAG(fcu, sel, FCURVE_SELECTED);
				fcu->flag &= ~FCURVE_ACTIVE;
			}
				break;
			case ANIMTYPE_NLATRACK:
			{
				NlaTrack *nlt= (NlaTrack *)ale->data;
				
				ACHANNEL_SET_FLAG(nlt, sel, NLATRACK_SELECTED);
				nlt->flag &= ~NLATRACK_ACTIVE;
			}
				break;
		}
	}
	
	/* Cleanup */
	BLI_freelistN(&anim_data);
}

/* ************************************************************************** */
/* OPERATORS */

/* ****************** Rearrange Channels Operator ******************* */
/* This operator only works for Action Editor mode for now, as having it elsewhere makes things difficult */

#if 0 // XXX old animation system - needs to be updated for new system...

/* constants for channel rearranging */
/* WARNING: don't change exising ones without modifying rearrange func accordingly */
enum {
	REARRANGE_ACTCHAN_TOP= -2,
	REARRANGE_ACTCHAN_UP= -1,
	REARRANGE_ACTCHAN_DOWN= 1,
	REARRANGE_ACTCHAN_BOTTOM= 2
};

/* make sure all action-channels belong to a group (and clear action's list) */
static void split_groups_action_temp (bAction *act, bActionGroup *tgrp)
{
	bActionChannel *achan;
	bActionGroup *agrp;
	
	/* Separate action-channels into lists per group */
	for (agrp= act->groups.first; agrp; agrp= agrp->next) {
		if (agrp->channels.first) {
			achan= agrp->channels.last;
			act->chanbase.first= achan->next;
			
			achan= agrp->channels.first;
			achan->prev= NULL;
			
			achan= agrp->channels.last;
			achan->next= NULL;
		}
	}
	
	/* Initialise memory for temp-group */
	memset(tgrp, 0, sizeof(bActionGroup));
	tgrp->flag |= (AGRP_EXPANDED|AGRP_TEMP);
	strcpy(tgrp->name, "#TempGroup");
		
	/* Move any action-channels not already moved, to the temp group */
	if (act->chanbase.first) {
		/* start of list */
		achan= act->chanbase.first;
		achan->prev= NULL;
		tgrp->channels.first= achan;
		act->chanbase.first= NULL;
		
		/* end of list */
		achan= act->chanbase.last;
		achan->next= NULL;
		tgrp->channels.last= achan;
		act->chanbase.last= NULL;
	}
	
	/* Add temp-group to list */
	BLI_addtail(&act->groups, tgrp);
}

/* link lists of channels that groups have */
static void join_groups_action_temp (bAction *act)
{
	bActionGroup *agrp;
	bActionChannel *achan;
	
	for (agrp= act->groups.first; agrp; agrp= agrp->next) {
		ListBase tempGroup;
		
		/* add list of channels to action's channels */
		tempGroup= agrp->channels;
		addlisttolist(&act->chanbase, &agrp->channels);
		agrp->channels= tempGroup;
		
		/* clear moved flag */
		agrp->flag &= ~AGRP_MOVED;
		
		/* if temp-group... remove from list (but don't free as it's on the stack!) */
		if (agrp->flag & AGRP_TEMP) {
			BLI_remlink(&act->groups, agrp);
			break;
		}
	}
	
	/* clear "moved" flag from all achans */
	for (achan= act->chanbase.first; achan; achan= achan->next) 
		achan->flag &= ~ACHAN_MOVED;
}


static short rearrange_actchannel_is_ok (Link *channel, short type)
{
	if (type == ANIMTYPE_GROUP) {
		bActionGroup *agrp= (bActionGroup *)channel;
		
		if (SEL_AGRP(agrp) && !(agrp->flag & AGRP_MOVED))
			return 1;
	}
	else if (type == ANIMTYPE_ACHAN) {
		bActionChannel *achan= (bActionChannel *)channel;
		
		if (VISIBLE_ACHAN(achan) && SEL_ACHAN(achan) && !(achan->flag & ACHAN_MOVED))
			return 1;
	}
	
	return 0;
}

static short rearrange_actchannel_after_ok (Link *channel, short type)
{
	if (type == ANIMTYPE_GROUP) {
		bActionGroup *agrp= (bActionGroup *)channel;
		
		if (agrp->flag & AGRP_TEMP)
			return 0;
	}
	
	return 1;
}


static short rearrange_actchannel_top (ListBase *list, Link *channel, short type)
{
	if (rearrange_actchannel_is_ok(channel, type)) {
		/* take it out off the chain keep data */
		BLI_remlink(list, channel);
		
		/* make it first element */
		BLI_insertlinkbefore(list, list->first, channel);
		
		return 1;
	}
	
	return 0;
}

static short rearrange_actchannel_up (ListBase *list, Link *channel, short type)
{
	if (rearrange_actchannel_is_ok(channel, type)) {
		Link *prev= channel->prev;
		
		if (prev) {
			/* take it out off the chain keep data */
			BLI_remlink(list, channel);
			
			/* push it up */
			BLI_insertlinkbefore(list, prev, channel);
			
			return 1;
		}
	}
	
	return 0;
}

static short rearrange_actchannel_down (ListBase *list, Link *channel, short type)
{
	if (rearrange_actchannel_is_ok(channel, type)) {
		Link *next = (channel->next) ? channel->next->next : NULL;
		
		if (next) {
			/* take it out off the chain keep data */
			BLI_remlink(list, channel);
			
			/* move it down */
			BLI_insertlinkbefore(list, next, channel);
			
			return 1;
		}
		else if (rearrange_actchannel_after_ok(list->last, type)) {
			/* take it out off the chain keep data */
			BLI_remlink(list, channel);
			
			/* add at end */
			BLI_addtail(list, channel);
			
			return 1;
		}
		else {
			/* take it out off the chain keep data */
			BLI_remlink(list, channel);
			
			/* add just before end */
			BLI_insertlinkbefore(list, list->last, channel);
			
			return 1;
		}
	}
	
	return 0;
}

static short rearrange_actchannel_bottom (ListBase *list, Link *channel, short type)
{
	if (rearrange_actchannel_is_ok(channel, type)) {
		if (rearrange_actchannel_after_ok(list->last, type)) {
			/* take it out off the chain keep data */
			BLI_remlink(list, channel);
			
			/* add at end */
			BLI_addtail(list, channel);
			
			return 1;
		}
	}
	
	return 0;
}


/* Change the order of action-channels 
 *	mode: REARRANGE_ACTCHAN_*  
 */
static void rearrange_action_channels (bAnimContext *ac, short mode)
{
	bAction *act;
	bActionChannel *achan, *chan;
	bActionGroup *agrp, *grp;
	bActionGroup tgrp;
	
	short (*rearrange_func)(ListBase *, Link *, short);
	short do_channels = 1;
	
	/* Get the active action, exit if none are selected */
	act= (bAction *)ac->data;
	
	/* exit if invalid mode */
	switch (mode) {
		case REARRANGE_ACTCHAN_TOP:
			rearrange_func= rearrange_actchannel_top;
			break;
		case REARRANGE_ACTCHAN_UP:
			rearrange_func= rearrange_actchannel_up;
			break;
		case REARRANGE_ACTCHAN_DOWN:
			rearrange_func= rearrange_actchannel_down;
			break;
		case REARRANGE_ACTCHAN_BOTTOM:
			rearrange_func= rearrange_actchannel_bottom;
			break;
		default:
			return;
	}
	
	/* make sure we're only operating with groups */
	split_groups_action_temp(act, &tgrp);
	
	/* rearrange groups first (and then, only consider channels if the groups weren't moved) */
	#define GET_FIRST(list) ((mode > 0) ? (list.first) : (list.last))
	#define GET_NEXT(item) ((mode > 0) ? (item->next) : (item->prev))
	
	for (agrp= GET_FIRST(act->groups); agrp; agrp= grp) {
		/* Get next group to consider */
		grp= GET_NEXT(agrp);
		
		/* try to do group first */
		if (rearrange_func(&act->groups, (Link *)agrp, ANIMTYPE_GROUP)) {
			do_channels= 0;
			agrp->flag |= AGRP_MOVED;
		}
	}
	
	if (do_channels) {
		for (agrp= GET_FIRST(act->groups); agrp; agrp= grp) {
			/* Get next group to consider */
			grp= GET_NEXT(agrp);
			
			/* only consider action-channels if they're visible (group expanded) */
			if (EXPANDED_AGRP(agrp)) {
				for (achan= GET_FIRST(agrp->channels); achan; achan= chan) {
					/* Get next channel to consider */
					chan= GET_NEXT(achan);
					
					/* Try to do channel */
					if (rearrange_func(&agrp->channels, (Link *)achan, ANIMTYPE_ACHAN))
						achan->flag |= ACHAN_MOVED;
				}
			}
		}
	}
	#undef GET_FIRST
	#undef GET_NEXT
	
	/* assemble lists into one list (and clear moved tags) */
	join_groups_action_temp(act);
}

/* ------------------- */

static int animchannels_rearrange_exec(bContext *C, wmOperator *op)
{
	bAnimContext ac;
	short mode;
	
	/* get editor data - only for Action Editor (for now) */
	if (ANIM_animdata_get_context(C, &ac) == 0)
		return OPERATOR_CANCELLED;
	if (ac.datatype != ANIMCONT_ACTION)
		return OPERATOR_PASS_THROUGH;
		
	/* get mode, then rearrange channels */
	mode= RNA_enum_get(op->ptr, "direction");
	rearrange_action_channels(&ac, mode);
	
	/* set notifier tha things have changed */
	ANIM_animdata_send_notifiers(C, &ac, ANIM_CHANGED_CHANNELS);
	
	return OPERATOR_FINISHED;
}
 

void ANIM_OT_channels_move_up (wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Move Channel(s) Up";
	ot->idname= "ANIM_OT_channels_move_up";
	
	/* api callbacks */
	ot->exec= animchannels_rearrange_exec;
	ot->poll= ED_operator_areaactive;
	
	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
	
	/* props */
	RNA_def_enum(ot->srna, "direction", NULL /* XXX add enum for this */, REARRANGE_ACTCHAN_UP, "Direction", "");
}

void ANIM_OT_channels_move_down (wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Move Channel(s) Down";
	ot->idname= "ANIM_OT_channels_move_down";
	
	/* api callbacks */
	ot->exec= animchannels_rearrange_exec;
	ot->poll= ED_operator_areaactive;
	
	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
	
	/* props */
	RNA_def_enum(ot->srna, "direction", NULL /* XXX add enum for this */, REARRANGE_ACTCHAN_DOWN, "Direction", "");
}

void ANIM_OT_channels_move_top (wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Move Channel(s) to Top";
	ot->idname= "ANIM_OT_channels_move_to_top";
	
	/* api callbacks */
	ot->exec= animchannels_rearrange_exec;
	ot->poll= ED_operator_areaactive;
	
	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
	
	/* props */
	RNA_def_enum(ot->srna, "direction", NULL /* XXX add enum for this */, REARRANGE_ACTCHAN_TOP, "Direction", "");
}

void ANIM_OT_channels_move_bottom (wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Move Channel(s) to Bottom";
	ot->idname= "ANIM_OT_channels_move_to_bottom";
	
	/* api callbacks */
	ot->exec= animchannels_rearrange_exec;
	ot->poll= ED_operator_areaactive;
	
	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
	
	/* props */
	RNA_def_enum(ot->srna, "direction", NULL /* XXX add enum for this */, REARRANGE_ACTCHAN_BOTTOM, "Direction", "");
}

#endif // XXX old animation system - needs to be updated for new system...


/* ******************** Toggle Channel Visibility Operator *********************** */

static int animchannels_visibility_toggle_exec(bContext *C, wmOperator *op)
{
	bAnimContext ac;
	ListBase anim_data = {NULL, NULL};
	bAnimListElem *ale;
	int filter;
	short vis= ACHANNEL_SETFLAG_ADD;
	
	/* get editor data */
	if (ANIM_animdata_get_context(C, &ac) == 0)
		return OPERATOR_CANCELLED;
		
	/* filter data */
	filter= (ANIMFILTER_VISIBLE | ANIMFILTER_SEL | ANIMFILTER_CURVESONLY);
	ANIM_animdata_filter(&ac, &anim_data, filter, ac.data, ac.datatype);
	
	/* See if we should be making showing all selected or hiding */
	for (ale= anim_data.first; ale; ale= ale->next) {
		if (vis == ACHANNEL_SETFLAG_CLEAR) 
			break;
		
		if (ale->flag & FCURVE_VISIBLE)
			vis= ACHANNEL_SETFLAG_CLEAR;
	}
		
	/* Now set the flags */
	for (ale= anim_data.first; ale; ale= ale->next) {
		FCurve *fcu= (FCurve *)ale->data;
		ACHANNEL_SET_FLAG(fcu, vis, FCURVE_VISIBLE);
	}
	
	/* cleanup */
	BLI_freelistN(&anim_data);
	
	/* set notifier tha things have changed */
	ANIM_animdata_send_notifiers(C, &ac, ANIM_CHANGED_CHANNELS);
	
	return OPERATOR_FINISHED;
}
 
void ANIM_OT_channels_visibility_toggle (wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Toggle Visibility";
	ot->idname= "ANIM_OT_channels_visibility_toggle";
	
	/* api callbacks */
	ot->exec= animchannels_visibility_toggle_exec;
	ot->poll= ED_operator_ipo_active;
	
	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
}

/* ********************** Set Flags Operator *********************** */

enum {
// 	ACHANNEL_SETTING_SELECT = 0,
	ACHANNEL_SETTING_PROTECT = 1,
	ACHANNEL_SETTING_MUTE,
	ACHANNEL_SETTING_VISIBLE,
	ACHANNEL_SETTING_EXPAND,
} eAnimChannel_Settings;

/* defines for setting animation-channel flags */
EnumPropertyItem prop_animchannel_setflag_types[] = {
	{ACHANNEL_SETFLAG_CLEAR, "DISABLE", "Disable", ""},
	{ACHANNEL_SETFLAG_ADD, "ENABLE", "Enable", ""},
	{ACHANNEL_SETFLAG_TOGGLE, "TOGGLE", "Toggle", ""},
	{0, NULL, NULL, NULL}
};

/* defines for set animation-channel settings */
EnumPropertyItem prop_animchannel_settings_types[] = {
	{ACHANNEL_SETTING_PROTECT, "PROTECT", "Protect", ""},
	{ACHANNEL_SETTING_MUTE, "MUTE", "Mute", ""},
	{0, NULL, NULL, NULL}
};


/* ------------------- */

/* macro to be used in setflag_anim_channels */
#define ASUBCHANNEL_SEL_OK(ale) ( (onlysel == 0) || \
		((ale->id) && (GS(ale->id->name)==ID_OB) && (((Object *)ale->id)->flag & SELECT)) ) 

/* Set/clear a particular flag (setting) for all selected + visible channels 
 *	setting: the setting to modify
 *	mode: eAnimChannels_SetFlag
 *	onlysel: only selected channels get the flag set
 */
static void setflag_anim_channels (bAnimContext *ac, short setting, short mode, short onlysel)
{
	ListBase anim_data = {NULL, NULL};
	bAnimListElem *ale;
	int filter;
	
	/* filter data */
	filter= (ANIMFILTER_VISIBLE | ANIMFILTER_CHANNELS);
	if (onlysel) filter |= ANIMFILTER_SEL;
	ANIM_animdata_filter(ac, &anim_data, filter, ac->data, ac->datatype);
	
	/* affect selected channels */
	for (ale= anim_data.first; ale; ale= ale->next) {
		switch (ale->type) {
			case ANIMTYPE_OBJECT:
			{
				Base *base= (Base *)ale->data;
				Object *ob= base->object;
				
				if (setting == ACHANNEL_SETTING_EXPAND) {
					// XXX - settings should really be moved out of ob->nlaflag
					if (mode == ACHANNEL_SETFLAG_TOGGLE) 	ob->nlaflag ^= OB_ADS_COLLAPSED;
					else if (mode == ACHANNEL_SETFLAG_ADD) 	ob->nlaflag &= ~OB_ADS_COLLAPSED;
					else 									ob->nlaflag |= OB_ADS_COLLAPSED;
				}
			}
				break;
			
			case ANIMTYPE_FILLACTD:
			{
				bAction *act= (bAction *)ale->data;
				
				if (ASUBCHANNEL_SEL_OK(ale)) {
					if (setting == ACHANNEL_SETTING_EXPAND) {
						ACHANNEL_SET_FLAG_NEG(act, mode, ACT_COLLAPSED);
					}
				}
			}
				break;
			case ANIMTYPE_FILLDRIVERS:
			{
				AnimData *adt= (AnimData *)ale->data;
				
				if (ASUBCHANNEL_SEL_OK(ale)) {
					if (setting == ACHANNEL_SETTING_EXPAND) {
						ACHANNEL_SET_FLAG_NEG(adt, mode, ADT_DRIVERS_COLLAPSED);
					}
				}
			}
				break;
			case ANIMTYPE_FILLMATD:
			{
				Object *ob= (Object *)ale->data;
				
				// XXX - settings should really be moved out of ob->nlaflag
				if ((onlysel == 0) || (ob->flag & SELECT)) {
					if (setting == ACHANNEL_SETTING_EXPAND) {
						if (mode == ACHANNEL_SETFLAG_TOGGLE) 	ob->nlaflag ^= OB_ADS_SHOWMATS;
						else if (mode == ACHANNEL_SETFLAG_ADD) 	ob->nlaflag |= OB_ADS_SHOWMATS;
						else 									ob->nlaflag &= ~OB_ADS_SHOWMATS;
					}
				}
			}
				break;
					
			case ANIMTYPE_DSMAT:
			{
				Material *ma= (Material *)ale->data;
				
				if (ASUBCHANNEL_SEL_OK(ale)) {
					if (setting == ACHANNEL_SETTING_EXPAND) {
						ACHANNEL_SET_FLAG(ma, mode, MA_DS_EXPAND);
					}
				}
			}
				break;
			case ANIMTYPE_DSLAM:
			{
				Lamp *la= (Lamp *)ale->data;
				
				if (ASUBCHANNEL_SEL_OK(ale)) {
					if (setting == ACHANNEL_SETTING_EXPAND) {
						ACHANNEL_SET_FLAG(la, mode, LA_DS_EXPAND);
					}
				}
			}
				break;
			case ANIMTYPE_DSCAM:
			{
				Camera *ca= (Camera *)ale->data;
				
				if (ASUBCHANNEL_SEL_OK(ale)) {
					if (setting == ACHANNEL_SETTING_EXPAND) {
						ACHANNEL_SET_FLAG(ca, mode, CAM_DS_EXPAND);
					}
				}
			}
				break;
			case ANIMTYPE_DSCUR:
			{
				Curve *cu= (Curve *)ale->data;
				
				if (ASUBCHANNEL_SEL_OK(ale)) {
					if (setting == ACHANNEL_SETTING_EXPAND) {
						ACHANNEL_SET_FLAG(cu, mode, CU_DS_EXPAND);
					}
				}
			}
				break;
			case ANIMTYPE_DSSKEY:
			{
				Key *key= (Key *)ale->data;
				
				if (ASUBCHANNEL_SEL_OK(ale)) {
					if (setting == ACHANNEL_SETTING_EXPAND) {
						ACHANNEL_SET_FLAG(key, mode, KEYBLOCK_DS_EXPAND);
					}
				}
			}
				break;
			case ANIMTYPE_DSWOR:
			{
				World *wo= (World *)ale->data;
				
				if (ASUBCHANNEL_SEL_OK(ale)) {
					if (setting == ACHANNEL_SETTING_EXPAND) {
						ACHANNEL_SET_FLAG(wo, mode, WO_DS_EXPAND);
					}
				}
			}
				break;
				
			case ANIMTYPE_GROUP:
			{
				bActionGroup *agrp= (bActionGroup *)ale->data;
				
				switch (setting) {
					case ACHANNEL_SETTING_PROTECT:
						ACHANNEL_SET_FLAG(agrp, mode, AGRP_PROTECTED);
						break;
					case ACHANNEL_SETTING_EXPAND:
						ACHANNEL_SET_FLAG(agrp, mode, AGRP_EXPANDED);
						break;
				}
			}
				break;
			case ANIMTYPE_FCURVE:
			{
				FCurve *fcu= (FCurve *)ale->data;
				
				switch (setting) {
					case ACHANNEL_SETTING_MUTE:
						ACHANNEL_SET_FLAG(fcu, mode, FCURVE_MUTED);
						break;
					case ACHANNEL_SETTING_PROTECT:
						ACHANNEL_SET_FLAG(fcu, mode, FCURVE_PROTECTED);
						break;
					case ACHANNEL_SETTING_VISIBLE:
						ACHANNEL_SET_FLAG(fcu, mode, FCURVE_VISIBLE);
						break;
				}
			}
				break;
			case ANIMTYPE_GPLAYER:
			{
				bGPDlayer *gpl= (bGPDlayer *)ale->data;
				
				switch (setting) {
					case ACHANNEL_SETTING_MUTE:
						ACHANNEL_SET_FLAG(gpl, mode, GP_LAYER_HIDE);
						break;
					case ACHANNEL_SETTING_PROTECT:
						ACHANNEL_SET_FLAG(gpl, mode, GP_LAYER_LOCKED);
						break;
				}
			}
				break;
		}
	}
	
	BLI_freelistN(&anim_data);
}

/* ------------------- */

static int animchannels_setflag_exec(bContext *C, wmOperator *op)
{
	bAnimContext ac;
	short mode, setting;
	
	/* get editor data */
	if (ANIM_animdata_get_context(C, &ac) == 0)
		return OPERATOR_CANCELLED;
		
	/* mode (eAnimChannels_SetFlag), setting (eAnimChannel_Settings) */
	mode= RNA_enum_get(op->ptr, "mode");
	setting= RNA_enum_get(op->ptr, "type");
	
	/* modify setting */
	setflag_anim_channels(&ac, setting, mode, 1);
	
	/* set notifier tha things have changed */
	ANIM_animdata_send_notifiers(C, &ac, ANIM_CHANGED_CHANNELS);
	
	return OPERATOR_FINISHED;
}


void ANIM_OT_channels_setting_enable (wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Enable Channel Setting";
	ot->idname= "ANIM_OT_channels_setting_enable";
	
	/* api callbacks */
	ot->invoke= WM_menu_invoke;
	ot->exec= animchannels_setflag_exec;
	ot->poll= ED_operator_areaactive;
	
	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
	
	/* props */
		/* flag-setting mode */
	RNA_def_enum(ot->srna, "mode", prop_animchannel_setflag_types, ACHANNEL_SETFLAG_ADD, "Mode", "");
		/* setting to set */
	RNA_def_enum(ot->srna, "type", prop_animchannel_settings_types, 0, "Type", "");
}

void ANIM_OT_channels_setting_disable (wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Disable Channel Setting";
	ot->idname= "ANIM_OT_channels_setting_disable";
	
	/* api callbacks */
	ot->invoke= WM_menu_invoke;
	ot->exec= animchannels_setflag_exec;
	ot->poll= ED_operator_areaactive;
	
	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
	
	/* props */
		/* flag-setting mode */
	RNA_def_enum(ot->srna, "mode", prop_animchannel_setflag_types, ACHANNEL_SETFLAG_CLEAR, "Mode", "");
		/* setting to set */
	RNA_def_enum(ot->srna, "type", prop_animchannel_settings_types, 0, "Type", "");
}

void ANIM_OT_channels_setting_toggle (wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Toggle Channel Setting";
	ot->idname= "ANIM_OT_channels_setting_toggle";
	
	/* api callbacks */
	ot->invoke= WM_menu_invoke;
	ot->exec= animchannels_setflag_exec;
	ot->poll= ED_operator_areaactive;
	
	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
	
	/* props */
		/* flag-setting mode */
	RNA_def_enum(ot->srna, "mode", prop_animchannel_setflag_types, ACHANNEL_SETFLAG_TOGGLE, "Mode", "");
		/* setting to set */
	RNA_def_enum(ot->srna, "type", prop_animchannel_settings_types, 0, "Type", "");
}

// XXX currently, this is a separate operator, but perhaps we could in future specify in keymaps whether to call invoke or exec?
void ANIM_OT_channels_editable_toggle (wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Toggle Channel Editability";
	ot->idname= "ANIM_OT_channels_editable_toggle";
	
	/* api callbacks */
	ot->exec= animchannels_setflag_exec;
	ot->poll= ED_operator_areaactive;
	
	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
	
	/* props */
		/* flag-setting mode */
	RNA_def_enum(ot->srna, "mode", prop_animchannel_setflag_types, ACHANNEL_SETFLAG_TOGGLE, "Mode", "");
		/* setting to set */
	RNA_def_enum(ot->srna, "type", prop_animchannel_settings_types, ACHANNEL_SETTING_PROTECT, "Type", "");
}

/* ********************** Expand Channels Operator *********************** */

static int animchannels_expand_exec (bContext *C, wmOperator *op)
{
	bAnimContext ac;
	short onlysel= 1;
	
	/* get editor data */
	if (ANIM_animdata_get_context(C, &ac) == 0)
		return OPERATOR_CANCELLED;
		
	/* only affect selected channels? */
	if (RNA_boolean_get(op->ptr, "all"))
		onlysel= 0;
	
	/* modify setting */
	setflag_anim_channels(&ac, ACHANNEL_SETTING_EXPAND, ACHANNEL_SETFLAG_ADD, onlysel);
	
	/* set notifier that things have changed */
	ANIM_animdata_send_notifiers(C, &ac, ANIM_CHANGED_CHANNELS);
	
	return OPERATOR_FINISHED;
}

void ANIM_OT_channels_expand (wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Expand Channels";
	ot->idname= "ANIM_OT_channels_expand";
	
	/* api callbacks */
	ot->exec= animchannels_expand_exec;
	ot->poll= ED_operator_areaactive;
	
	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
	
	/* props */
	RNA_def_boolean(ot->srna, "all", 0, "All", "Expand all channels (not just selected ones)");
}

/* ********************** Collapse Channels Operator *********************** */

static int animchannels_collapse_exec (bContext *C, wmOperator *op)
{
	bAnimContext ac;
	short onlysel= 1;
	
	/* get editor data */
	if (ANIM_animdata_get_context(C, &ac) == 0)
		return OPERATOR_CANCELLED;
		
	/* only affect selected channels? */
	if (RNA_boolean_get(op->ptr, "all"))
		onlysel= 0;
	
	/* modify setting */
	setflag_anim_channels(&ac, ACHANNEL_SETTING_EXPAND, ACHANNEL_SETFLAG_CLEAR, onlysel);
	
	/* set notifier that things have changed */
	ANIM_animdata_send_notifiers(C, &ac, ANIM_CHANGED_CHANNELS);
	
	return OPERATOR_FINISHED;
}

void ANIM_OT_channels_collapse (wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Collapse Channels";
	ot->idname= "ANIM_OT_channels_collapse";
	
	/* api callbacks */
	ot->exec= animchannels_collapse_exec;
	ot->poll= ED_operator_areaactive;
	
	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
	
	/* props */
	RNA_def_boolean(ot->srna, "all", 0, "All", "Collapse all channels (not just selected ones)");
}

/* ********************** Select All Operator *********************** */

static int animchannels_deselectall_exec(bContext *C, wmOperator *op)
{
	bAnimContext ac;
	
	/* get editor data */
	if (ANIM_animdata_get_context(C, &ac) == 0)
		return OPERATOR_CANCELLED;
		
	/* 'standard' behaviour - check if selected, then apply relevant selection */
	if (RNA_boolean_get(op->ptr, "invert"))
		ANIM_deselect_anim_channels(ac.data, ac.datatype, 0, ACHANNEL_SETFLAG_TOGGLE);
	else
		ANIM_deselect_anim_channels(ac.data, ac.datatype, 1, ACHANNEL_SETFLAG_ADD);
	
	/* set notifier tha things have changed */
	ANIM_animdata_send_notifiers(C, &ac, ANIM_CHANGED_CHANNELS);
	
	return OPERATOR_FINISHED;
}
 
void ANIM_OT_channels_select_all_toggle (wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Select All";
	ot->idname= "ANIM_OT_channels_select_all_toggle";
	
	/* api callbacks */
	ot->exec= animchannels_deselectall_exec;
	ot->poll= ED_operator_areaactive;
	
	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
	
	/* props */
	RNA_def_boolean(ot->srna, "invert", 0, "Invert", "");
}

/* ******************** Borderselect Operator *********************** */

static void borderselect_anim_channels (bAnimContext *ac, rcti *rect, short selectmode)
{
	ListBase anim_data = {NULL, NULL};
	bAnimListElem *ale;
	int filter;
	
	View2D *v2d= &ac->ar->v2d;
	rctf rectf;
	float ymin=0, ymax=(float)(-ACHANNEL_HEIGHT);
	
	/* convert border-region to view coordinates */
	UI_view2d_region_to_view(v2d, rect->xmin, rect->ymin+2, &rectf.xmin, &rectf.ymin);
	UI_view2d_region_to_view(v2d, rect->xmax, rect->ymax-2, &rectf.xmax, &rectf.ymax);
	
	/* filter data */
	filter= (ANIMFILTER_VISIBLE | ANIMFILTER_CHANNELS);
	ANIM_animdata_filter(ac, &anim_data, filter, ac->data, ac->datatype);
	
	/* loop over data, doing border select */
	for (ale= anim_data.first; ale; ale= ale->next) {
		ymin= ymax - ACHANNEL_STEP;
		
		/* if channel is within border-select region, alter it */
		if (!((ymax < rectf.ymin) || (ymin > rectf.ymax))) {
			/* only the following types can be selected */
			switch (ale->type) {
				case ANIMTYPE_OBJECT: /* object */
				{
					Base *base= (Base *)ale->data;
					Object *ob= base->object;
					
					ACHANNEL_SET_FLAG(base, selectmode, SELECT);
					ACHANNEL_SET_FLAG(ob, selectmode, SELECT);
				}
					break;
				case ANIMTYPE_GROUP: /* action group */
				{
					bActionGroup *agrp= (bActionGroup *)ale->data;
					
					ACHANNEL_SET_FLAG(agrp, selectmode, AGRP_SELECTED);
					agrp->flag &= ~AGRP_ACTIVE;
				}
					break;
				case ANIMTYPE_FCURVE: /* F-Curve channel */
				{
					FCurve *fcu = (FCurve *)ale->data;
					
					ACHANNEL_SET_FLAG(fcu, selectmode, FCURVE_SELECTED);
				}
					break;
				case ANIMTYPE_GPLAYER: /* grease-pencil layer */
				{
					bGPDlayer *gpl = (bGPDlayer *)ale->data;
					
					ACHANNEL_SET_FLAG(gpl, selectmode, GP_LAYER_SELECT);
				}
					break;
			}
		}
		
		/* set minimum extent to be the maximum of the next channel */
		ymax= ymin;
	}
	
	/* cleanup */
	BLI_freelistN(&anim_data);
}

/* ------------------- */

static int animchannels_borderselect_exec(bContext *C, wmOperator *op)
{
	bAnimContext ac;
	rcti rect;
	short selectmode=0;
	int event;
	
	/* get editor data */
	if (ANIM_animdata_get_context(C, &ac) == 0)
		return OPERATOR_CANCELLED;
	
	/* get settings from operator */
	rect.xmin= RNA_int_get(op->ptr, "xmin");
	rect.ymin= RNA_int_get(op->ptr, "ymin");
	rect.xmax= RNA_int_get(op->ptr, "xmax");
	rect.ymax= RNA_int_get(op->ptr, "ymax");
		
	event= RNA_int_get(op->ptr, "event_type");
	if (event == LEFTMOUSE) // FIXME... hardcoded
		selectmode = ACHANNEL_SETFLAG_ADD;
	else
		selectmode = ACHANNEL_SETFLAG_CLEAR;
	
	/* apply borderselect animation channels */
	borderselect_anim_channels(&ac, &rect, selectmode);
	
	return OPERATOR_FINISHED;
} 

void ANIM_OT_channels_select_border(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Border Select";
	ot->idname= "ANIM_OT_channels_select_border";
	
	/* api callbacks */
	ot->invoke= WM_border_select_invoke;
	ot->exec= animchannels_borderselect_exec;
	ot->modal= WM_border_select_modal;
	
	ot->poll= ED_operator_areaactive;
	
	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
	
	/* rna */
	RNA_def_int(ot->srna, "event_type", 0, INT_MIN, INT_MAX, "Event Type", "", INT_MIN, INT_MAX);
	RNA_def_int(ot->srna, "xmin", 0, INT_MIN, INT_MAX, "X Min", "", INT_MIN, INT_MAX);
	RNA_def_int(ot->srna, "xmax", 0, INT_MIN, INT_MAX, "X Max", "", INT_MIN, INT_MAX);
	RNA_def_int(ot->srna, "ymin", 0, INT_MIN, INT_MAX, "Y Min", "", INT_MIN, INT_MAX);
	RNA_def_int(ot->srna, "ymax", 0, INT_MIN, INT_MAX, "Y Max", "", INT_MIN, INT_MAX);
}

/* ******************** Mouse-Click Operator *********************** */
/* Depending on the channel that was clicked on, the mouse click will activate whichever
 * part of the channel is relevant.
 *
 * NOTE: eventually, this should probably be phased out when many of these things are replaced with buttons
 */

static void mouse_anim_channels (bAnimContext *ac, float x, int channel_index, short selectmode)
{
	ListBase anim_data = {NULL, NULL};
	bAnimListElem *ale;
	int filter;
	
	/* get the channel that was clicked on */
		/* filter channels */
	filter= (ANIMFILTER_VISIBLE | ANIMFILTER_CHANNELS);
	filter= ANIM_animdata_filter(ac, &anim_data, filter, ac->data, ac->datatype);
	
		/* get channel from index */
	ale= BLI_findlink(&anim_data, channel_index);
	if (ale == NULL) {
		/* channel not found */
		printf("Error: animation channel (index = %d) not found in mouse_anim_channels() \n", channel_index);
		
		BLI_freelistN(&anim_data);
		return;
	}
	
	/* selectmode -1 is a special case for ActionGroups only, which selects all of the channels underneath it only... */
	// TODO: should this feature be extended to work with other channel types too?
	if ((selectmode == -1) && (ale->type != ANIMTYPE_GROUP)) {
		/* normal channels should not behave normally in this case */
		BLI_freelistN(&anim_data);
		return;
	}
	
	/* action to take depends on what channel we've got */
	switch (ale->type) {
		case ANIMTYPE_SCENE:
		{
			Scene *sce= (Scene *)ale->data;
			
			if (x < 16) {
				/* toggle expand */
				sce->flag ^= SCE_DS_COLLAPSED;
			}
			else {
				/* set selection status */
				if (selectmode == SELECT_INVERT) {
					/* swap select */
					sce->flag ^= SCE_DS_SELECTED;
				}
				else {
					sce->flag |= SCE_DS_SELECTED;
				}
			}
		}
			break;
		case ANIMTYPE_OBJECT:
		{
			bDopeSheet *ads= (bDopeSheet *)ac->data;
			Scene *sce= (Scene *)ads->source;
			Base *base= (Base *)ale->data;
			Object *ob= base->object;
			
			if (x < 16) {
				/* toggle expand */
				ob->nlaflag ^= OB_ADS_COLLAPSED; // XXX 
			}
			else {
				/* set selection status */
				if (selectmode == SELECT_INVERT) {
					/* swap select */
					base->flag ^= SELECT;
					ob->flag= base->flag;
				}
				else {
					Base *b;
					
					/* deleselect all */
					for (b= sce->base.first; b; b= b->next) {
						b->flag &= ~SELECT;
						b->object->flag= b->flag;
					}
					
					/* select object now */
					base->flag |= SELECT;
					ob->flag |= SELECT;
				}
				
				/* xxx should be ED_base_object_activate(), but we need context pointer for that... */
				//set_active_base(base);
			}
		}
			break;
		case ANIMTYPE_FILLACTD:
		{
			bAction *act= (bAction *)ale->data;
			act->flag ^= ACT_COLLAPSED;
		}
			break;
		case ANIMTYPE_FILLDRIVERS:
		{
			AnimData *adt= (AnimData* )ale->data;
			adt->flag ^= ADT_DRIVERS_COLLAPSED;
		}
			break;
		case ANIMTYPE_FILLMATD:
		{
			Object *ob= (Object *)ale->data;
			ob->nlaflag ^= OB_ADS_SHOWMATS;	// XXX 
		}
			break;
				
		case ANIMTYPE_DSMAT:
		{
			Material *ma= (Material *)ale->data;
			ma->flag ^= MA_DS_EXPAND;
		}
			break;
		case ANIMTYPE_DSLAM:
		{
			Lamp *la= (Lamp *)ale->data;
			la->flag ^= LA_DS_EXPAND;
		}
			break;
		case ANIMTYPE_DSCAM:
		{
			Camera *ca= (Camera *)ale->data;
			ca->flag ^= CAM_DS_EXPAND;
		}
			break;
		case ANIMTYPE_DSCUR:
		{
			Curve *cu= (Curve *)ale->data;
			cu->flag ^= CU_DS_EXPAND;
		}
			break;
		case ANIMTYPE_DSSKEY:
		{
			Key *key= (Key *)ale->data;
			key->flag ^= KEYBLOCK_DS_EXPAND;
		}
			break;
		case ANIMTYPE_DSWOR:
		{
			World *wo= (World *)ale->data;
			wo->flag ^= WO_DS_EXPAND;
		}
			break;
			
		case ANIMTYPE_GROUP: 
		{
			bActionGroup *agrp= (bActionGroup *)ale->data;
			short offset= (ELEM3(ac->datatype, ANIMCONT_DOPESHEET, ANIMCONT_FCURVES, ANIMCONT_DRIVERS))? 18 : 0;
			
			if ((x < (offset+17)) && (agrp->channels.first)) {
				/* toggle expand */
				agrp->flag ^= AGRP_EXPANDED;
			}
			else if (x >= (ACHANNEL_NAMEWIDTH-ACHANNEL_BUTTON_WIDTH)) {
				/* toggle protection/locking */
				agrp->flag ^= AGRP_PROTECTED;
			}
			else {
				/* select/deselect group */
				if (selectmode == SELECT_INVERT) {
					/* inverse selection status of this group only */
					agrp->flag ^= AGRP_SELECTED;
				}
				else if (selectmode == -1) {
					/* select all in group (and deselect everthing else) */	
					FCurve *fcu;
					
					/* deselect all other channels */
					ANIM_deselect_anim_channels(ac->data, ac->datatype, 0, ACHANNEL_SETFLAG_CLEAR);
					
					/* only select channels in group and group itself */
					for (fcu= agrp->channels.first; fcu && fcu->grp==agrp; fcu= fcu->next)
						fcu->flag |= FCURVE_SELECTED;
					agrp->flag |= AGRP_SELECTED;					
				}
				else {
					/* select group by itself */
					ANIM_deselect_anim_channels(ac->data, ac->datatype, 0, ACHANNEL_SETFLAG_CLEAR);
					agrp->flag |= AGRP_SELECTED;
				}
				
				/* if group is selected now, make group the 'active' one in the visible list */
				if (agrp->flag & AGRP_SELECTED)
					ANIM_set_active_channel(ac->data, ac->datatype, filter, agrp, ANIMTYPE_GROUP);
			}
		}
			break;
		case ANIMTYPE_FCURVE: 
		{
			FCurve *fcu= (FCurve *)ale->data;
			short offset;
			
			if (ac->datatype != ANIMCONT_ACTION) {
				/* for now, special case for materials */
				if (ale->ownertype == ANIMTYPE_DSMAT)
					offset= 21;
				else
					offset= 18;
			}
			else
				offset = 0;
			
			if (x >= (ACHANNEL_NAMEWIDTH-ACHANNEL_BUTTON_WIDTH)) {
				/* toggle protection (only if there's a toggle there) */
				if (fcu->bezt)
					fcu->flag ^= FCURVE_PROTECTED;
			}
			else if (x >= (ACHANNEL_NAMEWIDTH-2*ACHANNEL_BUTTON_WIDTH)) {
				/* toggle mute */
				fcu->flag ^= FCURVE_MUTED;
			}
			else if ((x < (offset+17)) && (ac->spacetype==SPACE_IPO)) {
				/* toggle visibility */
				fcu->flag ^= FCURVE_VISIBLE;
			}
			else {
				/* select/deselect */
				if (selectmode == SELECT_INVERT) {
					/* inverse selection status of this F-Curve only */
					fcu->flag ^= FCURVE_SELECTED;
				}
				else {
					/* select F-Curve by itself */
					ANIM_deselect_anim_channels(ac->data, ac->datatype, 0, ACHANNEL_SETFLAG_CLEAR);
					fcu->flag |= FCURVE_SELECTED;
				}
				
				/* if F-Curve is selected now, make F-Curve the 'active' one in the visible list */
				if (fcu->flag & FCURVE_SELECTED)
					ANIM_set_active_channel(ac->data, ac->datatype, filter, fcu, ANIMTYPE_FCURVE);
			}
		}
			break;
		case ANIMTYPE_GPDATABLOCK:
		{
			bGPdata *gpd= (bGPdata *)ale->data;
			
			/* toggle expand */
			gpd->flag ^= GP_DATA_EXPAND;
		}
			break;
		case ANIMTYPE_GPLAYER:
		{
#if 0 // XXX future of this is unclear
			bGPdata *gpd= (bGPdata *)ale->owner;
			bGPDlayer *gpl= (bGPDlayer *)ale->data;
			
			if (x >= (ACHANNEL_NAMEWIDTH-16)) {
				/* toggle lock */
				gpl->flag ^= GP_LAYER_LOCKED;
			}
			else if (x >= (ACHANNEL_NAMEWIDTH-32)) {
				/* toggle hide */
				gpl->flag ^= GP_LAYER_HIDE;
			}
			else {
				/* select/deselect */
				//if (G.qual & LR_SHIFTKEY) {
					//select_gplayer_channel(gpd, gpl, SELECT_INVERT);
				//}
				//else {
					//deselect_gpencil_layers(data, 0);
					//select_gplayer_channel(gpd, gpl, SELECT_INVERT);
				//}
			}
#endif // XXX future of this is unclear
		}
			break;
		case ANIMTYPE_SHAPEKEY:
			/* TODO: shapekey channels cannot be selected atm... */
			break;
		default:
			printf("Error: Invalid channel type in mouse_anim_channels() \n");
	}
	
	/* free channels */
	BLI_freelistN(&anim_data);
}

/* ------------------- */

/* handle clicking */
static int animchannels_mouseclick_invoke(bContext *C, wmOperator *op, wmEvent *event)
{
	bAnimContext ac;
	Scene *scene;
	ARegion *ar;
	View2D *v2d;
	int mval[2], channel_index;
	short selectmode;
	float x, y;
	
	
	/* get editor data */
	if (ANIM_animdata_get_context(C, &ac) == 0)
		return OPERATOR_CANCELLED;
		
	/* get useful pointers from animation context data */
	scene= ac.scene;
	ar= ac.ar;
	v2d= &ar->v2d;
	
	/* get mouse coordinates (in region coordinates) */
	mval[0]= (event->x - ar->winrct.xmin);
	mval[1]= (event->y - ar->winrct.ymin);
	
	/* select mode is either replace (deselect all, then add) or add/extend */
	if (RNA_boolean_get(op->ptr, "extend"))
		selectmode= SELECT_INVERT;
	else if (RNA_boolean_get(op->ptr, "children_only"))
		selectmode= -1; /* this is a bit of a special case for ActionGroups only... should it be removed or extended to all instead? */
	else
		selectmode= SELECT_REPLACE;
	
	/* figure out which channel user clicked in 
	 * Note: although channels technically start at y= ACHANNEL_FIRST, we need to adjust by half a channel's height
	 *		so that the tops of channels get caught ok. Since ACHANNEL_FIRST is really ACHANNEL_HEIGHT, we simply use
	 *		ACHANNEL_HEIGHT_HALF.
	 */
	UI_view2d_region_to_view(v2d, mval[0], mval[1], &x, &y);
	UI_view2d_listview_view_to_cell(v2d, ACHANNEL_NAMEWIDTH, ACHANNEL_STEP, 0, (float)ACHANNEL_HEIGHT_HALF, x, y, NULL, &channel_index);
	
	/* handle mouse-click in the relevant channel then */
	mouse_anim_channels(&ac, x, channel_index, selectmode);
	
	/* set notifier tha things have changed */
	ANIM_animdata_send_notifiers(C, &ac, ANIM_CHANGED_CHANNELS);
	
	return OPERATOR_FINISHED;
}
 
void ANIM_OT_channels_click (wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Mouse Click on Channels";
	ot->idname= "ANIM_OT_channels_click";
	
	/* api callbacks */
	ot->invoke= animchannels_mouseclick_invoke;
	ot->poll= ED_operator_areaactive;
	
	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
	
	/* id-props */
	RNA_def_boolean(ot->srna, "extend", 0, "Extend Select", ""); // SHIFTKEY
	RNA_def_boolean(ot->srna, "children_only", 0, "Select Children Only", ""); // CTRLKEY|SHIFTKEY
}

/* ************************************************************************** */
/* Operator Registration */

void ED_operatortypes_animchannels(void)
{
	WM_operatortype_append(ANIM_OT_channels_select_all_toggle);
	WM_operatortype_append(ANIM_OT_channels_select_border);
	WM_operatortype_append(ANIM_OT_channels_click);
	
	WM_operatortype_append(ANIM_OT_channels_setting_enable);
	WM_operatortype_append(ANIM_OT_channels_setting_disable);
	WM_operatortype_append(ANIM_OT_channels_setting_toggle);
	
		// XXX does this need to be a separate operator?
	WM_operatortype_append(ANIM_OT_channels_editable_toggle);
	
		// XXX these need to be updated for new system... todo...
	//WM_operatortype_append(ANIM_OT_channels_move_up);
	//WM_operatortype_append(ANIM_OT_channels_move_down);
	//WM_operatortype_append(ANIM_OT_channels_move_top);
	//WM_operatortype_append(ANIM_OT_channels_move_bottom);
	
	WM_operatortype_append(ANIM_OT_channels_expand);
	WM_operatortype_append(ANIM_OT_channels_collapse);
	
	WM_operatortype_append(ANIM_OT_channels_visibility_toggle);
}

void ED_keymap_animchannels(wmWindowManager *wm)
{
	ListBase *keymap = WM_keymap_listbase(wm, "Animation_Channels", 0, 0);
	
	/* selection */
		/* click-select */
		// XXX for now, only leftmouse.... 
	WM_keymap_add_item(keymap, "ANIM_OT_channels_click", LEFTMOUSE, KM_PRESS, 0, 0);
	RNA_boolean_set(WM_keymap_add_item(keymap, "ANIM_OT_channels_click", LEFTMOUSE, KM_PRESS, KM_SHIFT, 0)->ptr, "extend", 1);
	RNA_boolean_set(WM_keymap_add_item(keymap, "ANIM_OT_channels_click", LEFTMOUSE, KM_PRESS, KM_CTRL|KM_SHIFT, 0)->ptr, "children_only", 1);
	
		/* deselect all */
	WM_keymap_add_item(keymap, "ANIM_OT_channels_select_all_toggle", AKEY, KM_PRESS, 0, 0);
	RNA_boolean_set(WM_keymap_add_item(keymap, "ANIM_OT_channels_select_all_toggle", IKEY, KM_PRESS, KM_CTRL, 0)->ptr, "invert", 1);
	
		/* borderselect */
	WM_keymap_add_item(keymap, "ANIM_OT_channels_select_border", BKEY, KM_PRESS, 0, 0);
	
	/* settings */
	WM_keymap_add_item(keymap, "ANIM_OT_channels_setting_toggle", WKEY, KM_PRESS, KM_SHIFT, 0);
	WM_keymap_add_item(keymap, "ANIM_OT_channels_setting_enable", WKEY, KM_PRESS, KM_CTRL|KM_SHIFT, 0);
	WM_keymap_add_item(keymap, "ANIM_OT_channels_setting_disable", WKEY, KM_PRESS, KM_ALT, 0);
	
	/* settings - specialised hotkeys */
	WM_keymap_add_item(keymap, "ANIM_OT_channels_editable_toggle", TABKEY, KM_PRESS, 0, 0);
	
	/* expand/collapse */
	WM_keymap_add_item(keymap, "ANIM_OT_channels_expand", PADPLUSKEY, KM_PRESS, 0, 0);
	WM_keymap_add_item(keymap, "ANIM_OT_channels_collapse", PADMINUS, KM_PRESS, 0, 0);
	
	RNA_boolean_set(WM_keymap_add_item(keymap, "ANIM_OT_channels_expand", PADPLUSKEY, KM_PRESS, KM_CTRL, 0)->ptr, "all", 1);
	RNA_boolean_set(WM_keymap_add_item(keymap, "ANIM_OT_channels_collapse", PADMINUS, KM_PRESS, KM_CTRL, 0)->ptr, "all", 1);
	
	/* rearranging - actions only */
	//WM_keymap_add_item(keymap, "ANIM_OT_channels_move_up", PAGEUPKEY, KM_PRESS, KM_SHIFT, 0);
	//WM_keymap_add_item(keymap, "ANIM_OT_channels_move_down", PAGEDOWNKEY, KM_PRESS, KM_SHIFT, 0);
	//WM_keymap_add_item(keymap, "ANIM_OT_channels_move_to_top", PAGEUPKEY, KM_PRESS, KM_CTRL|KM_SHIFT, 0);
	//WM_keymap_add_item(keymap, "ANIM_OT_channels_move_to_bottom", PAGEDOWNKEY, KM_PRESS, KM_CTRL|KM_SHIFT, 0);
	
	/* Graph Editor only */
	WM_keymap_add_item(keymap, "ANIM_OT_channels_visibility_toggle", VKEY, KM_PRESS, 0, 0);
}

/* ************************************************************************** */

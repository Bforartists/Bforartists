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
 * The Original Code is Copyright (C) 2009 Blender Foundation, Joshua Leung
 * All rights reserved.
 *
 * 
 * Contributor(s): Joshua Leung (major recode)
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#include <string.h>
#include <stdio.h>

#include "DNA_anim_types.h"
#include "DNA_action_types.h"
#include "DNA_nla_types.h"
#include "DNA_object_types.h"
#include "DNA_space_types.h"
#include "DNA_scene_types.h"
#include "DNA_screen_types.h"
#include "DNA_windowmanager_types.h"

#include "MEM_guardedalloc.h"

#include "BLI_blenlib.h"
#include "BLI_arithb.h"
#include "BLI_rand.h"

#include "BKE_animsys.h"
#include "BKE_nla.h"
#include "BKE_context.h"
#include "BKE_report.h"
#include "BKE_screen.h"

#include "ED_anim_api.h"
#include "ED_keyframes_edit.h"
#include "ED_markers.h"
#include "ED_space_api.h"
#include "ED_screen.h"

#include "RNA_access.h"
#include "RNA_define.h"

#include "WM_api.h"
#include "WM_types.h"

#include "UI_interface.h"
#include "UI_resources.h"
#include "UI_view2d.h"

#include "nla_intern.h"	// own include

/* ******************** Utilities ***************************************** */

/* Convert SELECT_* flags to ACHANNEL_SETFLAG_* flags */
static short selmodes_to_flagmodes (short sel)
{
	/* convert selection modes to selection modes */
	switch (sel) {
		case SELECT_SUBTRACT:
			return ACHANNEL_SETFLAG_CLEAR;
			break;
			
		case SELECT_INVERT:
			return ACHANNEL_SETFLAG_TOGGLE;
			break;
			
		case SELECT_ADD:
		default:
			return ACHANNEL_SETFLAG_ADD;
			break;
	}
}


/* ******************** Deselect All Operator ***************************** */
/* This operator works in one of three ways:
 *	1) (de)select all (AKEY) - test if select all or deselect all
 *	2) invert all (CTRL-IKEY) - invert selection of all keyframes
 *	3) (de)select all - no testing is done; only for use internal tools as normal function...
 */

/* Deselects strips in the NLA Editor
 *	- This is called by the deselect all operator, as well as other ones!
 *
 * 	- test: check if select or deselect all
 *	- sel: how to select keyframes 
 *		0 = deselect
 *		1 = select
 *		2 = invert
 */
static void deselect_nla_strips (bAnimContext *ac, short test, short sel)
{
	ListBase anim_data = {NULL, NULL};
	bAnimListElem *ale;
	int filter;
	short smode;
	
	/* determine type-based settings - curvesonly eliminates all the unnecessary channels... */
	filter= (ANIMFILTER_VISIBLE|ANIMFILTER_CURVESONLY);
	
	/* filter data */
	ANIM_animdata_filter(ac, &anim_data, filter, ac->data, ac->datatype);
	
	/* See if we should be selecting or deselecting */
	if (test) {
		for (ale= anim_data.first; ale; ale= ale->next) {
			NlaTrack *nlt= (NlaTrack *)ale->data;
			NlaStrip *strip;
			
			/* if any strip is selected, break out, since we should now be deselecting */
			for (strip= nlt->strips.first; strip; strip= strip->next) {
				if (strip->flag & NLASTRIP_FLAG_SELECT) {
					sel= SELECT_SUBTRACT;
					break;
				}
			}
			
			if (sel == SELECT_SUBTRACT)
				break;
		}
	}
	
	/* convert selection modes to selection modes */
	smode= selmodes_to_flagmodes(sel);
	
	/* Now set the flags */
	for (ale= anim_data.first; ale; ale= ale->next) {
		NlaTrack *nlt= (NlaTrack *)ale->data;
		NlaStrip *strip;
		
		/* apply same selection to all strips */
		for (strip= nlt->strips.first; strip; strip= strip->next) {
			/* set selection */
			ACHANNEL_SET_FLAG(strip, smode, NLASTRIP_FLAG_SELECT);
			
			/* clear active flag */
			strip->flag &= ~NLASTRIP_FLAG_ACTIVE;
		}
	}
	
	/* Cleanup */
	BLI_freelistN(&anim_data);
}

/* ------------------- */

static int nlaedit_deselectall_exec(bContext *C, wmOperator *op)
{
	bAnimContext ac;
	
	/* get editor data */
	if (ANIM_animdata_get_context(C, &ac) == 0)
		return OPERATOR_CANCELLED;
		
	/* 'standard' behaviour - check if selected, then apply relevant selection */
	if (RNA_boolean_get(op->ptr, "invert"))
		deselect_nla_strips(&ac, 0, SELECT_INVERT);
	else
		deselect_nla_strips(&ac, 1, SELECT_ADD);
	
	/* set notifier that things have changed */
	ANIM_animdata_send_notifiers(C, &ac, ANIM_CHANGED_BOTH);
	
	return OPERATOR_FINISHED;
}
 
void NLAEDIT_OT_select_all_toggle (wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Select All";
	ot->idname= "NLAEDIT_OT_select_all_toggle";
	
	/* api callbacks */
	ot->exec= nlaedit_deselectall_exec;
	ot->poll= ED_operator_areaactive;
	
	/* flags */
	ot->flag= OPTYPE_REGISTER/*|OPTYPE_UNDO*/;
	
	/* props */
	RNA_def_boolean(ot->srna, "invert", 0, "Invert", "");
}

/* ******************** Mouse-Click Select Operator *********************** */
/* This operator works in one of 2 ways:
 *	1) Select the strip directly under the mouse
 *	2) Select all the strips to one side of the mouse
 */

/* defines for left-right select tool */
static EnumPropertyItem prop_nlaedit_leftright_select_types[] = {
	{NLAEDIT_LRSEL_TEST, "CHECK", "Check if Select Left or Right", ""},
	{NLAEDIT_LRSEL_NONE, "OFF", "Don't select", ""},
	{NLAEDIT_LRSEL_LEFT, "LEFT", "Before current frame", ""},
	{NLAEDIT_LRSEL_RIGHT, "RIGHT", "After current frame", ""},
	{0, NULL, NULL, NULL}
};

/* sensitivity factor for frame-selections */
#define FRAME_CLICK_THRESH 		0.1f


/* ------------------- */

/* option 1) select strip directly under mouse */
static void mouse_nla_strips (bAnimContext *ac, int mval[2], short select_mode)
{
	ListBase anim_data = {NULL, NULL};
	bAnimListElem *ale = NULL;
	int filter;
	
	View2D *v2d= &ac->ar->v2d;
	NlaStrip *strip = NULL;
	int channel_index;
	float xmin, xmax, dummy;
	float x, y;
	
	
	/* use View2D to determine the index of the channel (i.e a row in the list) where keyframe was */
	UI_view2d_region_to_view(v2d, mval[0], mval[1], &x, &y);
	UI_view2d_listview_view_to_cell(v2d, 0, NLACHANNEL_STEP, 0, 0, x, y, NULL, &channel_index);
	
	/* x-range to check is +/- 7 (in screen/region-space) on either side of mouse click 
	 * (that is the size of keyframe icons, so user should be expecting similar tolerances) 
	 */
	UI_view2d_region_to_view(v2d, mval[0]-7, mval[1], &xmin, &dummy);
	UI_view2d_region_to_view(v2d, mval[0]+7, mval[1], &xmax, &dummy);
	
	/* filter data */
	filter= (ANIMFILTER_VISIBLE | ANIMFILTER_CHANNELS);
	ANIM_animdata_filter(ac, &anim_data, filter, ac->data, ac->datatype);
	
	/* try to get channel */
	ale= BLI_findlink(&anim_data, channel_index);
	if (ale == NULL) {
		/* channel not found */
		printf("Error: animation channel (index = %d) not found in mouse_nla_strips() \n", channel_index);
		BLI_freelistN(&anim_data);
		return;
	}
	else {
		/* found some channel - we only really should do somethign when its an Nla-Track */
		if (ale->type == ANIMTYPE_NLATRACK) {
			NlaTrack *nlt= (NlaTrack *)ale->data;
			
			/* loop over NLA-strips in this track, trying to find one which occurs in the necessary bounds */
			for (strip= nlt->strips.first; strip; strip= strip->next) {
				if (BKE_nlastrip_within_bounds(strip, xmin, xmax))
					break;
			}
		}
		
		/* remove active channel from list of channels for separate treatment (since it's needed later on) */
		BLI_remlink(&anim_data, ale);
		
		/* free list of channels, since it's not used anymore */
		BLI_freelistN(&anim_data);
	}
	
	/* for replacing selection, firstly need to clear existing selection */
	if (select_mode == SELECT_REPLACE) {
		/* reset selection mode for next steps */
		select_mode = SELECT_ADD;
		
		/* deselect all strips */
		deselect_nla_strips(ac, 0, SELECT_SUBTRACT);
		
		/* deselect all other channels first */
		ANIM_deselect_anim_channels(ac->data, ac->datatype, 0, ACHANNEL_SETFLAG_CLEAR);
		
		/* Highlight NLA-Track */
		if (ale->type == ANIMTYPE_NLATRACK) {	
			NlaTrack *nlt= (NlaTrack *)ale->data;
			
			nlt->flag |= NLATRACK_SELECTED;
			ANIM_set_active_channel(ac->data, ac->datatype, filter, nlt, ANIMTYPE_NLATRACK);
		}
	}
	
	/* only select strip if we clicked on a valid channel and hit something */
	if (ale) {
		/* select the strip accordingly (if a matching one was found) */
		if (strip) {
			select_mode= selmodes_to_flagmodes(select_mode);
			ACHANNEL_SET_FLAG(strip, select_mode, NLASTRIP_FLAG_SELECT);
		}
		
		/* free this channel */
		MEM_freeN(ale);
	}
}

/* Option 2) Selects all the strips on either side of the current frame (depends on which side the mouse is on) */
static void nlaedit_mselect_leftright (bAnimContext *ac, short leftright, short select_mode)
{
	ListBase anim_data = {NULL, NULL};
	bAnimListElem *ale;
	int filter;
	
	Scene *scene= ac->scene;
	float xmin, xmax;
	
	/* if select mode is replace, deselect all keyframes (and channels) first */
	if (select_mode==SELECT_REPLACE) {
		select_mode= SELECT_ADD;
		
		/* deselect all other channels and keyframes */
		ANIM_deselect_anim_channels(ac->data, ac->datatype, 0, ACHANNEL_SETFLAG_CLEAR);
		deselect_nla_strips(ac, 0, SELECT_SUBTRACT);
	}
	
	/* get range, and get the right flag-setting mode */
	if (leftright == NLAEDIT_LRSEL_LEFT) {
		xmin = -MAXFRAMEF;
		xmax = (float)(CFRA + FRAME_CLICK_THRESH);
	} 
	else {
		xmin = (float)(CFRA - FRAME_CLICK_THRESH);
		xmax = MAXFRAMEF;
	}
	
	select_mode= selmodes_to_flagmodes(select_mode);
	
	
	/* filter data */
	filter= (ANIMFILTER_VISIBLE | ANIMFILTER_CURVESONLY);
	ANIM_animdata_filter(ac, &anim_data, filter, ac->data, ac->datatype);
	
	/* select strips on the side where most data occurs */
	for (ale= anim_data.first; ale; ale= ale->next) {
		NlaTrack *nlt= (NlaTrack *)ale->data;
		NlaStrip *strip;
		
		/* check each strip to see if it is appropriate */
		for (strip= nlt->strips.first; strip; strip= strip->next) {
			if (BKE_nlastrip_within_bounds(strip, xmin, xmax)) {
				ACHANNEL_SET_FLAG(strip, select_mode, NLASTRIP_FLAG_SELECT);
			}
		}
	}
	
	/* Cleanup */
	BLI_freelistN(&anim_data);
}

/* ------------------- */

/* handle clicking */
static int nlaedit_clickselect_invoke(bContext *C, wmOperator *op, wmEvent *event)
{
	bAnimContext ac;
	Scene *scene;
	ARegion *ar;
	View2D *v2d;
	short selectmode;
	int mval[2];
	
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
	else
		selectmode= SELECT_REPLACE;
	
	/* figure out action to take */
	if (RNA_enum_get(op->ptr, "left_right")) {
		/* select all keys on same side of current frame as mouse */
		float x;
		
		UI_view2d_region_to_view(v2d, mval[0], mval[1], &x, NULL);
		if (x < CFRA)
			RNA_int_set(op->ptr, "left_right", NLAEDIT_LRSEL_LEFT);
		else 	
			RNA_int_set(op->ptr, "left_right", NLAEDIT_LRSEL_RIGHT);
		
		nlaedit_mselect_leftright(&ac, RNA_enum_get(op->ptr, "left_right"), selectmode);
	}
	else {
		/* select strips based upon mouse position */
		mouse_nla_strips(&ac, mval, selectmode);
	}
	
	/* set notifier that things have changed */
	ANIM_animdata_send_notifiers(C, &ac, ANIM_CHANGED_BOTH);
	
	/* for tweak grab to work */
	return OPERATOR_FINISHED|OPERATOR_PASS_THROUGH;
}
 
void NLAEDIT_OT_click_select (wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Mouse Select";
	ot->idname= "NLAEDIT_OT_click_select";
	
	/* api callbacks - absolutely no exec() this yet... */
	ot->invoke= nlaedit_clickselect_invoke;
	ot->poll= ED_operator_areaactive;
	
	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
	
	/* id-props */
	// XXX should we make this into separate operators?
	RNA_def_enum(ot->srna, "left_right", prop_nlaedit_leftright_select_types, 0, "Left Right", ""); // CTRLKEY
	RNA_def_boolean(ot->srna, "extend", 0, "Extend Select", ""); // SHIFTKEY
}

/* *********************************************** */

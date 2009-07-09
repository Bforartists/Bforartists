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
 * The Original Code is Copyright (C) 2008 Blender Foundation
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
#include "BKE_fcurve.h"
#include "BKE_key.h"
#include "BKE_material.h"
#include "BKE_nla.h"
#include "BKE_object.h"
#include "BKE_context.h"
#include "BKE_utildefines.h"

#include "UI_view2d.h"

#include "ED_anim_api.h"
#include "ED_keyframing.h"
#include "ED_keyframes_draw.h"
#include "ED_keyframes_edit.h"
#include "ED_markers.h"
#include "ED_screen.h"
#include "ED_space_api.h"

#include "WM_api.h"
#include "WM_types.h"

#include "action_intern.h"

/* ************************************************************************** */
/* KEYFRAMES STUFF */

/* ******************** Deselect All Operator ***************************** */
/* This operator works in one of three ways:
 *	1) (de)select all (AKEY) - test if select all or deselect all
 *	2) invert all (CTRL-IKEY) - invert selection of all keyframes
 *	3) (de)select all - no testing is done; only for use internal tools as normal function...
 */

/* Deselects keyframes in the action editor
 *	- This is called by the deselect all operator, as well as other ones!
 *
 * 	- test: check if select or deselect all
 *	- sel: how to select keyframes 
 *		0 = deselect
 *		1 = select
 *		2 = invert
 */
static void deselect_action_keys (bAnimContext *ac, short test, short sel)
{
	ListBase anim_data = {NULL, NULL};
	bAnimListElem *ale;
	int filter;
	
	BeztEditData bed;
	BeztEditFunc test_cb, sel_cb;
	
	/* determine type-based settings */
	if (ac->datatype == ANIMCONT_GPENCIL)
		filter= (ANIMFILTER_VISIBLE);
	else
		filter= (ANIMFILTER_VISIBLE | ANIMFILTER_CURVESONLY);
	
	/* filter data */
	ANIM_animdata_filter(ac, &anim_data, filter, ac->data, ac->datatype);
	
	/* init BezTriple looping data */
	memset(&bed, 0, sizeof(BeztEditData));
	test_cb= ANIM_editkeyframes_ok(BEZT_OK_SELECTED);
	
	/* See if we should be selecting or deselecting */
	if (test) {
		for (ale= anim_data.first; ale; ale= ale->next) {
			if (ale->type == ANIMTYPE_GPLAYER) {
				//if (is_gplayer_frame_selected(ale->data)) {
				//	sel= 0;
				//	break;
				//}
			}
			else {
				if (ANIM_fcurve_keys_bezier_loop(&bed, ale->key_data, NULL, test_cb, NULL)) {
					sel= SELECT_SUBTRACT;
					break;
				}
			}
		}
	}
	
	/* convert sel to selectmode, and use that to get editor */
	sel_cb= ANIM_editkeyframes_select(sel);
	
	/* Now set the flags */
	for (ale= anim_data.first; ale; ale= ale->next) {
		//if (ale->type == ACTTYPE_GPLAYER)
		//	set_gplayer_frame_selection(ale->data, sel);
		//else
			ANIM_fcurve_keys_bezier_loop(&bed, ale->key_data, NULL, sel_cb, NULL);
	}
	
	/* Cleanup */
	BLI_freelistN(&anim_data);
}

/* ------------------- */

static int actkeys_deselectall_exec(bContext *C, wmOperator *op)
{
	bAnimContext ac;
	
	/* get editor data */
	if (ANIM_animdata_get_context(C, &ac) == 0)
		return OPERATOR_CANCELLED;
		
	/* 'standard' behaviour - check if selected, then apply relevant selection */
	if (RNA_boolean_get(op->ptr, "invert"))
		deselect_action_keys(&ac, 0, SELECT_INVERT);
	else
		deselect_action_keys(&ac, 1, SELECT_ADD);
	
	/* set notifier that things have changed */
	ANIM_animdata_send_notifiers(C, &ac, ANIM_CHANGED_BOTH);
	
	return OPERATOR_FINISHED;
}
 
void ACT_OT_select_all_toggle (wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Select All";
	ot->idname= "ACT_OT_select_all_toggle";
	
	/* api callbacks */
	ot->exec= actkeys_deselectall_exec;
	ot->poll= ED_operator_action_active;
	
	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
	
	/* props */
	RNA_def_boolean(ot->srna, "invert", 0, "Invert", "");
}

/* ******************** Border Select Operator **************************** */
/* This operator currently works in one of three ways:
 *	-> BKEY 	- 1) all keyframes within region are selected (ACTKEYS_BORDERSEL_ALLKEYS)
 *	-> ALT-BKEY - depending on which axis of the region was larger...
 *		-> 2) x-axis, so select all frames within frame range (ACTKEYS_BORDERSEL_FRAMERANGE)
 *		-> 3) y-axis, so select all frames within channels that region included (ACTKEYS_BORDERSEL_CHANNELS)
 */

/* defines for borderselect mode */
enum {
	ACTKEYS_BORDERSEL_ALLKEYS	= 0,
	ACTKEYS_BORDERSEL_FRAMERANGE,
	ACTKEYS_BORDERSEL_CHANNELS,
} eActKeys_BorderSelect_Mode;


static void borderselect_action (bAnimContext *ac, rcti rect, short mode, short selectmode)
{
	ListBase anim_data = {NULL, NULL};
	bAnimListElem *ale;
	int filter;
	
	BeztEditData bed;
	BeztEditFunc ok_cb, select_cb;
	View2D *v2d= &ac->ar->v2d;
	rctf rectf;
	//float ymin=0, ymax=(float)(-ACHANNEL_HEIGHT);
	float ymin=0, ymax=(float)(-ACHANNEL_HEIGHT_HALF);
	
	/* convert mouse coordinates to frame ranges and channel coordinates corrected for view pan/zoom */
	UI_view2d_region_to_view(v2d, rect.xmin, rect.ymin+2, &rectf.xmin, &rectf.ymin);
	UI_view2d_region_to_view(v2d, rect.xmax, rect.ymax-2, &rectf.xmax, &rectf.ymax);
	
	/* filter data */
	filter= (ANIMFILTER_VISIBLE | ANIMFILTER_CHANNELS);
	ANIM_animdata_filter(ac, &anim_data, filter, ac->data, ac->datatype);
	
	/* get beztriple editing/validation funcs  */
	select_cb= ANIM_editkeyframes_select(selectmode);
	
	if (ELEM(mode, ACTKEYS_BORDERSEL_FRAMERANGE, ACTKEYS_BORDERSEL_ALLKEYS))
		ok_cb= ANIM_editkeyframes_ok(BEZT_OK_FRAMERANGE);
	else
		ok_cb= NULL;
		
	/* init editing data */
	memset(&bed, 0, sizeof(BeztEditData));
	
	/* loop over data, doing border select */
	for (ale= anim_data.first; ale; ale= ale->next) {
		AnimData *adt= ANIM_nla_mapping_get(ac, ale);
		
		/* get new vertical minimum extent of channel */
		ymin= ymax - ACHANNEL_STEP;
		
		/* set horizontal range (if applicable) */
		if (ELEM(mode, ACTKEYS_BORDERSEL_FRAMERANGE, ACTKEYS_BORDERSEL_ALLKEYS)) {
			/* if channel is mapped in NLA, apply correction */
			if (adt) {
				bed.f1= BKE_nla_tweakedit_remap(adt, rectf.xmin, NLATIME_CONVERT_UNMAP);
				bed.f2= BKE_nla_tweakedit_remap(adt, rectf.xmax, NLATIME_CONVERT_UNMAP);
			}
			else {
				bed.f1= rectf.xmin;
				bed.f2= rectf.xmax;
			}
		}
		
		/* perform vertical suitability check (if applicable) */
		if ( (mode == ACTKEYS_BORDERSEL_FRAMERANGE) || 
			!((ymax < rectf.ymin) || (ymin > rectf.ymax)) )
		{
			/* loop over data selecting */
			if (ale->key_data) {
				if (ale->datatype == ALE_FCURVE)
					ANIM_fcurve_keys_bezier_loop(&bed, ale->key_data, ok_cb, select_cb, NULL);
			}
			else if (ale->type == ANIMTYPE_GROUP) {
				bActionGroup *agrp= ale->data;
				FCurve *fcu;
				
				for (fcu= agrp->channels.first; fcu && fcu->grp==agrp; fcu= fcu->next) 
					ANIM_fcurve_keys_bezier_loop(&bed, fcu, ok_cb, select_cb, NULL);
			}
			//else if (ale->type == ANIMTYPE_GPLAYER) {
			//	borderselect_gplayer_frames(ale->data, rectf.xmin, rectf.xmax, selectmode);
			//}
		}
		
		/* set minimum extent to be the maximum of the next channel */
		ymax=ymin;
	}
	
	/* cleanup */
	BLI_freelistN(&anim_data);
}

/* ------------------- */

static int actkeys_borderselect_exec(bContext *C, wmOperator *op)
{
	bAnimContext ac;
	rcti rect;
	short mode=0, selectmode=0;
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
		selectmode = SELECT_ADD;
	else
		selectmode = SELECT_SUBTRACT;
	
	/* selection 'mode' depends on whether borderselect region only matters on one axis */
	if (RNA_boolean_get(op->ptr, "axis_range")) {
		/* mode depends on which axis of the range is larger to determine which axis to use 
		 *	- checking this in region-space is fine, as it's fundamentally still going to be a different rect size
		 *	- the frame-range select option is favoured over the channel one (x over y), as frame-range one is often
		 *	  used for tweaking timing when "blocking", while channels is not that useful...
		 */
		if ((rect.xmax - rect.xmin) >= (rect.ymax - rect.ymin))
			mode= ACTKEYS_BORDERSEL_FRAMERANGE;
		else
			mode= ACTKEYS_BORDERSEL_CHANNELS;
	}
	else 
		mode= ACTKEYS_BORDERSEL_ALLKEYS;
	
	/* apply borderselect action */
	borderselect_action(&ac, rect, mode, selectmode);
	
	return OPERATOR_FINISHED;
} 

void ACT_OT_select_border(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Border Select";
	ot->idname= "ACT_OT_select_border";
	
	/* api callbacks */
	ot->invoke= WM_border_select_invoke;
	ot->exec= actkeys_borderselect_exec;
	ot->modal= WM_border_select_modal;
	
	ot->poll= ED_operator_action_active;
	
	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
	
	/* rna */
	RNA_def_int(ot->srna, "event_type", 0, INT_MIN, INT_MAX, "Event Type", "", INT_MIN, INT_MAX);
	RNA_def_int(ot->srna, "xmin", 0, INT_MIN, INT_MAX, "X Min", "", INT_MIN, INT_MAX);
	RNA_def_int(ot->srna, "xmax", 0, INT_MIN, INT_MAX, "X Max", "", INT_MIN, INT_MAX);
	RNA_def_int(ot->srna, "ymin", 0, INT_MIN, INT_MAX, "Y Min", "", INT_MIN, INT_MAX);
	RNA_def_int(ot->srna, "ymax", 0, INT_MIN, INT_MAX, "Y Max", "", INT_MIN, INT_MAX);
	
	RNA_def_boolean(ot->srna, "axis_range", 0, "Axis Range", "");
}

/* ******************** Column Select Operator **************************** */
/* This operator works in one of four ways:
 *	- 1) select all keyframes in the same frame as a selected one  (KKEY)
 *	- 2) select all keyframes in the same frame as the current frame marker (CTRL-KKEY)
 *	- 3) select all keyframes in the same frame as a selected markers (SHIFT-KKEY)
 *	- 4) select all keyframes that occur between selected markers (ALT-KKEY)
 */

/* defines for column-select mode */
static EnumPropertyItem prop_column_select_types[] = {
	{ACTKEYS_COLUMNSEL_KEYS, "KEYS", 0, "On Selected Keyframes", ""},
	{ACTKEYS_COLUMNSEL_CFRA, "CFRA", 0, "On Current Frame", ""},
	{ACTKEYS_COLUMNSEL_MARKERS_COLUMN, "MARKERS_COLUMN", 0, "On Selected Markers", ""},
	{ACTKEYS_COLUMNSEL_MARKERS_BETWEEN, "MARKERS_BETWEEN", 0, "Between Min/Max Selected Markers", ""},
	{0, NULL, 0, NULL, NULL}
};

/* ------------------- */ 

/* Selects all visible keyframes between the specified markers */
static void markers_selectkeys_between (bAnimContext *ac)
{
	ListBase anim_data = {NULL, NULL};
	bAnimListElem *ale;
	int filter;
	
	BeztEditFunc ok_cb, select_cb;
	BeztEditData bed;
	float min, max;
	
	/* get extreme markers */
	ED_markers_get_minmax(ac->markers, 1, &min, &max);
	min -= 0.5f;
	max += 0.5f;
	
	/* get editing funcs + data */
	ok_cb= ANIM_editkeyframes_ok(BEZT_OK_FRAMERANGE);
	select_cb= ANIM_editkeyframes_select(SELECT_ADD);
	
	memset(&bed, 0, sizeof(BeztEditData));
	bed.f1= min; 
	bed.f2= max;
	
	/* filter data */
	filter= (ANIMFILTER_VISIBLE | ANIMFILTER_CURVESONLY);
	ANIM_animdata_filter(ac, &anim_data, filter, ac->data, ac->datatype);
	
	/* select keys in-between */
	for (ale= anim_data.first; ale; ale= ale->next) {
		AnimData *adt= ANIM_nla_mapping_get(ac, ale);
		
		if (adt) {	
			ANIM_nla_mapping_apply_fcurve(adt, ale->key_data, 0, 1);
			ANIM_fcurve_keys_bezier_loop(&bed, ale->key_data, ok_cb, select_cb, NULL);
			ANIM_nla_mapping_apply_fcurve(adt, ale->key_data, 1, 1);
		}
		else {
			ANIM_fcurve_keys_bezier_loop(&bed, ale->key_data, ok_cb, select_cb, NULL);
		}
	}
	
	/* Cleanup */
	BLI_freelistN(&anim_data);
}


/* Selects all visible keyframes in the same frames as the specified elements */
static void columnselect_action_keys (bAnimContext *ac, short mode)
{
	ListBase anim_data= {NULL, NULL};
	bAnimListElem *ale;
	int filter;
	
	Scene *scene= ac->scene;
	CfraElem *ce;
	BeztEditFunc select_cb, ok_cb;
	BeztEditData bed;
	
	/* initialise keyframe editing data */
	memset(&bed, 0, sizeof(BeztEditData));
	
	/* build list of columns */
	switch (mode) {
		case ACTKEYS_COLUMNSEL_KEYS: /* list of selected keys */
			if (ac->datatype == ANIMCONT_GPENCIL) {
				filter= (ANIMFILTER_VISIBLE);
				ANIM_animdata_filter(ac, &anim_data, filter, ac->data, ac->datatype);
				
				//for (ale= anim_data.first; ale; ale= ale->next)
				//	gplayer_make_cfra_list(ale->data, &elems, 1);
			}
			else {
				filter= (ANIMFILTER_VISIBLE | ANIMFILTER_CURVESONLY);
				ANIM_animdata_filter(ac, &anim_data, filter, ac->data, ac->datatype);
				
				for (ale= anim_data.first; ale; ale= ale->next)
					ANIM_fcurve_keys_bezier_loop(&bed, ale->key_data, NULL, bezt_to_cfraelem, NULL);
			}
			BLI_freelistN(&anim_data);
			break;
			
		case ACTKEYS_COLUMNSEL_CFRA: /* current frame */
			/* make a single CfraElem for storing this */
			ce= MEM_callocN(sizeof(CfraElem), "cfraElem");
			BLI_addtail(&bed.list, ce);
			
			ce->cfra= (float)CFRA;
			break;
			
		case ACTKEYS_COLUMNSEL_MARKERS_COLUMN: /* list of selected markers */
			ED_markers_make_cfra_list(ac->markers, &bed.list, 1);
			break;
			
		default: /* invalid option */
			return;
	}
	
	/* set up BezTriple edit callbacks */
	select_cb= ANIM_editkeyframes_select(SELECT_ADD);
	ok_cb= ANIM_editkeyframes_ok(BEZT_OK_FRAME);
	
	/* loop through all of the keys and select additional keyframes
	 * based on the keys found to be selected above
	 */
	if (ac->datatype == ANIMCONT_GPENCIL)
		filter= (ANIMFILTER_VISIBLE);
	else
		filter= (ANIMFILTER_VISIBLE | ANIMFILTER_CURVESONLY);
	ANIM_animdata_filter(ac, &anim_data, filter, ac->data, ac->datatype);
	
	for (ale= anim_data.first; ale; ale= ale->next) {
		AnimData *adt= ANIM_nla_mapping_get(ac, ale);
		
		/* loop over cfraelems (stored in the BeztEditData->list)
		 *	- we need to do this here, as we can apply fewer NLA-mapping conversions
		 */
		for (ce= bed.list.first; ce; ce= ce->next) {
			/* set frame for validation callback to refer to */
			if (adt)
				bed.f1= BKE_nla_tweakedit_remap(adt, ce->cfra, NLATIME_CONVERT_UNMAP);
			else
				bed.f1= ce->cfra;
			
			/* select elements with frame number matching cfraelem */
			ANIM_fcurve_keys_bezier_loop(&bed, ale->key_data, ok_cb, select_cb, NULL);
			
#if 0 // XXX reenable when Grease Pencil stuff is back
			if (ale->type == ANIMTYPE_GPLAYER) {
				bGPDlayer *gpl= (bGPDlayer *)ale->data;
				bGPDframe *gpf;
				
				for (gpf= gpl->frames.first; gpf; gpf= gpf->next) {
					if (ecfra == gpf->framenum) 
						gpf->flag |= GP_FRAME_SELECT;
				}
			}
			//else... 
#endif // XXX reenable when Grease Pencil stuff is back
		}
	}
	
	/* free elements */
	BLI_freelistN(&bed.list);
	BLI_freelistN(&anim_data);
}

/* ------------------- */

static int actkeys_columnselect_exec(bContext *C, wmOperator *op)
{
	bAnimContext ac;
	short mode;
	
	/* get editor data */
	if (ANIM_animdata_get_context(C, &ac) == 0)
		return OPERATOR_CANCELLED;
		
	/* action to take depends on the mode */
	mode= RNA_enum_get(op->ptr, "mode");
	
	if (mode == ACTKEYS_COLUMNSEL_MARKERS_BETWEEN)
		markers_selectkeys_between(&ac);
	else
		columnselect_action_keys(&ac, mode);
	
	/* set notifier that things have changed */
	ANIM_animdata_send_notifiers(C, &ac, ANIM_CHANGED_KEYFRAMES_SELECT);
	
	return OPERATOR_FINISHED;
}
 
void ACT_OT_select_column (wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Select All";
	ot->idname= "ACT_OT_select_column";
	
	/* api callbacks */
	ot->exec= actkeys_columnselect_exec;
	ot->poll= ED_operator_action_active;
	
	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
	
	/* props */
	RNA_def_enum(ot->srna, "mode", prop_column_select_types, 0, "Mode", "");
}

/* ******************** Mouse-Click Select Operator *********************** */
/* This operator works in one of three ways:
 *	- 1) keyframe under mouse - no special modifiers
 *	- 2) all keyframes on the same side of current frame indicator as mouse - ALT modifier
 *	- 3) column select all keyframes in frame under mouse - CTRL modifier
 *
 * In addition to these basic options, the SHIFT modifier can be used to toggle the 
 * selection mode between replacing the selection (without) and inverting the selection (with).
 */

/* defines for left-right select tool */
static EnumPropertyItem prop_actkeys_leftright_select_types[] = {
	{ACTKEYS_LRSEL_TEST, "CHECK", 0, "Check if Select Left or Right", ""},
	{ACTKEYS_LRSEL_NONE, "OFF", 0, "Don't select", ""},
	{ACTKEYS_LRSEL_LEFT, "LEFT", 0, "Before current frame", ""},
	{ACTKEYS_LRSEL_RIGHT, "RIGHT", 0, "After current frame", ""},
	{0, NULL, 0, NULL, NULL}
};

/* sensitivity factor for frame-selections */
#define FRAME_CLICK_THRESH 		0.1f

/* ------------------- */
 
/* option 1) select keyframe directly under mouse */
static void actkeys_mselect_single (bAnimContext *ac, bAnimListElem *ale, short select_mode, float selx)
{
	bDopeSheet *ads= (ac->datatype == ANIMCONT_DOPESHEET) ? ac->data : NULL;
	int ds_filter = ((ads) ? (ads->filterflag) : (0));
	
	BeztEditData bed;
	BeztEditFunc select_cb, ok_cb;
	
	/* get functions for selecting keyframes */
	select_cb= ANIM_editkeyframes_select(select_mode);
	ok_cb= ANIM_editkeyframes_ok(BEZT_OK_FRAME);
	memset(&bed, 0, sizeof(BeztEditData)); 
	bed.f1= selx;
	
	/* select the nominated keyframe on the given frame */
	ANIM_animchannel_keys_bezier_loop(&bed, ale, ok_cb, select_cb, NULL, ds_filter);
}

/* Option 2) Selects all the keyframes on either side of the current frame (depends on which side the mouse is on) */
static void actkeys_mselect_leftright (bAnimContext *ac, short leftright, short select_mode)
{
	ListBase anim_data = {NULL, NULL};
	bAnimListElem *ale;
	int filter;
	
	BeztEditFunc ok_cb, select_cb;
	BeztEditData bed;
	Scene *scene= ac->scene;
	
	/* if select mode is replace, deselect all keyframes (and channels) first */
	if (select_mode==SELECT_REPLACE) {
		select_mode= SELECT_ADD;
		
		/* deselect all other channels and keyframes */
		ANIM_deselect_anim_channels(ac->data, ac->datatype, 0, ACHANNEL_SETFLAG_CLEAR);
		deselect_action_keys(ac, 0, SELECT_SUBTRACT);
	}
	
	/* set callbacks and editing data */
	ok_cb= ANIM_editkeyframes_ok(BEZT_OK_FRAMERANGE);
	select_cb= ANIM_editkeyframes_select(select_mode);
	
	memset(&bed, 0, sizeof(BeztEditFunc));
	if (leftright == ACTKEYS_LRSEL_LEFT) {
		bed.f1 = MINAFRAMEF;
		bed.f2 = (float)(CFRA + FRAME_CLICK_THRESH);
	} 
	else {
		bed.f1 = (float)(CFRA - FRAME_CLICK_THRESH);
		bed.f2 = MAXFRAMEF;
	}
	
	/* filter data */
	if (ac->datatype == ANIMCONT_GPENCIL)
		filter= (ANIMFILTER_VISIBLE);
	else
		filter= (ANIMFILTER_VISIBLE | ANIMFILTER_CURVESONLY);
	ANIM_animdata_filter(ac, &anim_data, filter, ac->data, ac->datatype);
		
	/* select keys on the side where most data occurs */
	for (ale= anim_data.first; ale; ale= ale->next) {
		AnimData *adt= ANIM_nla_mapping_get(ac, ale);
		
		if (adt) {
			ANIM_nla_mapping_apply_fcurve(adt, ale->key_data, 0, 1);
			ANIM_fcurve_keys_bezier_loop(&bed, ale->key_data, ok_cb, select_cb, NULL);
			ANIM_nla_mapping_apply_fcurve(adt, ale->key_data, 1, 1);
		}
		//else if (ale->type == ANIMTYPE_GPLAYER)
		//	borderselect_gplayer_frames(ale->data, min, max, SELECT_ADD);
		else
			ANIM_fcurve_keys_bezier_loop(&bed, ale->key_data, ok_cb, select_cb, NULL);
	}
	
	/* Cleanup */
	BLI_freelistN(&anim_data);
}

/* Option 3) Selects all visible keyframes in the same frame as the mouse click */
static void actkeys_mselect_column(bAnimContext *ac, short select_mode, float selx)
{
	ListBase anim_data= {NULL, NULL};
	bAnimListElem *ale;
	int filter;
	
	BeztEditFunc select_cb, ok_cb;
	BeztEditData bed;
	
	/* initialise keyframe editing data */
	memset(&bed, 0, sizeof(BeztEditData));
	
	/* set up BezTriple edit callbacks */
	select_cb= ANIM_editkeyframes_select(select_mode);
	ok_cb= ANIM_editkeyframes_ok(BEZT_OK_FRAME);
	
	/* loop through all of the keys and select additional keyframes
	 * based on the keys found to be selected above
	 */
	if (ac->datatype == ANIMCONT_GPENCIL)
		filter= (ANIMFILTER_VISIBLE);
	else
		filter= (ANIMFILTER_VISIBLE | ANIMFILTER_CURVESONLY);
	ANIM_animdata_filter(ac, &anim_data, filter, ac->data, ac->datatype);
	
	for (ale= anim_data.first; ale; ale= ale->next) {
		AnimData *adt= ANIM_nla_mapping_get(ac, ale);
		
		/* set frame for validation callback to refer to */
		if (adt)
			bed.f1= BKE_nla_tweakedit_remap(adt, selx, NLATIME_CONVERT_UNMAP);
		else
			bed.f1= selx;
		
		/* select elements with frame number matching cfra */
		ANIM_fcurve_keys_bezier_loop(&bed, ale->key_data, ok_cb, select_cb, NULL);
			
#if 0 // XXX reenable when Grease Pencil stuff is back
			if (ale->type == ANIMTYPE_GPLAYER) {
				bGPDlayer *gpl= (bGPDlayer *)ale->data;
				bGPDframe *gpf;
				
				for (gpf= gpl->frames.first; gpf; gpf= gpf->next) {
					if (ecfra == gpf->framenum) 
						gpf->flag |= GP_FRAME_SELECT;
				}
			}
			//else... 
#endif // XXX reenable when Grease Pencil stuff is back
	}
	
	/* free elements */
	BLI_freelistN(&bed.list);
	BLI_freelistN(&anim_data);
}
 
/* ------------------- */

static void mouse_action_keys (bAnimContext *ac, int mval[2], short select_mode, short column)
{
	ListBase anim_data = {NULL, NULL};
	ListBase anim_keys = {NULL, NULL};
	bAnimListElem *ale;
	int filter;
	
	View2D *v2d= &ac->ar->v2d;
	bDopeSheet *ads = NULL;
	int channel_index;
	short found = 0;
	float selx = 0.0f;
	float x, y;
	rctf rectf;
	
	/* get dopesheet info */
	if (ac->datatype == ANIMCONT_DOPESHEET)
		ads= ac->data;
	
	/* use View2D to determine the index of the channel (i.e a row in the list) where keyframe was */
	UI_view2d_region_to_view(v2d, mval[0], mval[1], &x, &y);
	UI_view2d_listview_view_to_cell(v2d, 0, ACHANNEL_STEP, 0, (float)ACHANNEL_HEIGHT_HALF, x, y, NULL, &channel_index);
	
	/* x-range to check is +/- 7 (in screen/region-space) on either side of mouse click (size of keyframe icon) */
	UI_view2d_region_to_view(v2d, mval[0]-7, mval[1], &rectf.xmin, &rectf.ymin);
	UI_view2d_region_to_view(v2d, mval[0]+7, mval[1], &rectf.xmax, &rectf.ymax);
	
	/* filter data */
	filter= (ANIMFILTER_VISIBLE | ANIMFILTER_CHANNELS);
	ANIM_animdata_filter(ac, &anim_data, filter, ac->data, ac->datatype);
	
	/* try to get channel */
	ale= BLI_findlink(&anim_data, channel_index);
	if (ale == NULL) {
		/* channel not found */
		printf("Error: animation channel (index = %d) not found in mouse_action_keys() \n", channel_index);
		BLI_freelistN(&anim_data);
		return;
	}
	else {
		/* found match - must return here... */
		AnimData *adt= ANIM_nla_mapping_get(ac, ale);
		ActKeyColumn *ak;
		
		/* make list of keyframes */
		// TODO: it would be great if we didn't have to apply this to all the keyframes to do this...
		if (ale->key_data) {
			switch (ale->datatype) {
				case ALE_OB:
				{
					Object *ob= (Object *)ale->key_data;
					ob_to_keylist(ads, ob, &anim_keys, NULL);
				}
					break;
				case ALE_ACT:
				{
					bAction *act= (bAction *)ale->key_data;
					action_to_keylist(adt, act, &anim_keys, NULL);
				}
					break;
				case ALE_FCURVE:
				{
					FCurve *fcu= (FCurve *)ale->key_data;
					fcurve_to_keylist(adt, fcu, &anim_keys, NULL);
				}
					break;
			}
		}
		else if (ale->type == ANIMTYPE_GROUP) {
			bActionGroup *agrp= (bActionGroup *)ale->data;
			agroup_to_keylist(adt, agrp, &anim_keys, NULL);
		}
		else if (ale->type == ANIMTYPE_GPDATABLOCK) {
			/* cleanup */
			// FIXME:...
			BLI_freelistN(&anim_data);
			return;
		}
		else if (ale->type == ANIMTYPE_GPLAYER) {
			bGPDlayer *gpl= (bGPDlayer *)ale->data;
			gpl_to_keylist(ads, gpl, &anim_keys, NULL);
		}
		
		/* loop through keyframes, finding one that was clicked on */
		for (ak= anim_keys.first; ak; ak= ak->next) {
			if (IN_RANGE(ak->cfra, rectf.xmin, rectf.xmax)) {
				/* set the frame to use, and apply inverse-correction for NLA-mapping 
				 * so that the frame will get selected by the selection functiosn without
				 * requiring to map each frame once again...
				 */
				selx= BKE_nla_tweakedit_remap(adt, ak->cfra, NLATIME_CONVERT_UNMAP);
				found= 1;
				break;
			}
		}
		
		/* remove active channel from list of channels for separate treatment (since it's needed later on) */
		BLI_remlink(&anim_data, ale);
		
		/* cleanup temporary lists */
		BLI_freelistN(&anim_keys);
		anim_keys.first = anim_keys.last = NULL;
		
		/* free list of channels, since it's not used anymore */
		BLI_freelistN(&anim_data);
	}
	
	/* for replacing selection, firstly need to clear existing selection */
	if (select_mode == SELECT_REPLACE) {
		/* reset selection mode for next steps */
		select_mode = SELECT_ADD;
		
		/* deselect all keyframes */
		deselect_action_keys(ac, 0, SELECT_SUBTRACT);
		
		/* highlight channel clicked on */
		if (ELEM(ac->datatype, ANIMCONT_ACTION, ANIMCONT_DOPESHEET)) {
			/* deselect all other channels first */
			ANIM_deselect_anim_channels(ac->data, ac->datatype, 0, ACHANNEL_SETFLAG_CLEAR);
			
			/* Highlight Action-Group or F-Curve? */
			if (ale && ale->data) {
				if (ale->type == ANIMTYPE_GROUP) {
					bActionGroup *agrp= ale->data;
					
					agrp->flag |= AGRP_SELECTED;
					ANIM_set_active_channel(ac, ac->data, ac->datatype, filter, agrp, ANIMTYPE_GROUP);
				}	
				else if (ale->type == ANIMTYPE_FCURVE) {
					FCurve *fcu= ale->data;
					
					fcu->flag |= FCURVE_SELECTED;
					ANIM_set_active_channel(ac, ac->data, ac->datatype, filter, fcu, ANIMTYPE_FCURVE);
				}
			}
		}
		else if (ac->datatype == ANIMCONT_GPENCIL) {
			ANIM_deselect_anim_channels(ac->data, ac->datatype, 0, ACHANNEL_SETFLAG_CLEAR);
			
			/* Highlight gpencil layer */
			//gpl->flag |= GP_LAYER_SELECT;
			//gpencil_layer_setactive(gpd, gpl);
		}
	}
	
	/* only select keyframes if we clicked on a valid channel and hit something */
	if (ale) {
		if (found) {
			/* apply selection to keyframes */
			if (/*gpl*/0) {
				/* grease pencil */
				//select_gpencil_frame(gpl, (int)selx, selectmode);
			}
			else if (column) {
				/* select all keyframes in the same frame as the one we hit on the active channel */
				actkeys_mselect_column(ac, select_mode, selx);
			}
			else {
				/* select the nominated keyframe on the given frame */
				actkeys_mselect_single(ac, ale, select_mode, selx);
			}
		}
		
		/* free this channel */
		MEM_freeN(ale);
	}
}

/* handle clicking */
static int actkeys_clickselect_invoke(bContext *C, wmOperator *op, wmEvent *event)
{
	bAnimContext ac;
	Scene *scene;
	ARegion *ar;
	View2D *v2d;
	short selectmode, column;
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
		
	/* column selection */
	column= RNA_boolean_get(op->ptr, "column");
	
	/* figure out action to take */
	if (RNA_enum_get(op->ptr, "left_right")) {
		/* select all keys on same side of current frame as mouse */
		float x;
		
		UI_view2d_region_to_view(v2d, mval[0], mval[1], &x, NULL);
		if (x < CFRA)
			RNA_int_set(op->ptr, "left_right", ACTKEYS_LRSEL_LEFT);
		else 	
			RNA_int_set(op->ptr, "left_right", ACTKEYS_LRSEL_RIGHT);
		
		actkeys_mselect_leftright(&ac, RNA_enum_get(op->ptr, "left_right"), selectmode);
	}
	else {
		/* select keyframe(s) based upon mouse position*/
		mouse_action_keys(&ac, mval, selectmode, column);
	}
	
	/* set notifier that things have changed */
	ANIM_animdata_send_notifiers(C, &ac, ANIM_CHANGED_BOTH);
	
	/* for tweak grab to work */
	return OPERATOR_FINISHED|OPERATOR_PASS_THROUGH;
}
 
void ACT_OT_clickselect (wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Mouse Select Keys";
	ot->idname= "ACT_OT_clickselect";
	
	/* api callbacks - absolutely no exec() this yet... */
	ot->invoke= actkeys_clickselect_invoke;
	ot->poll= ED_operator_action_active;
	
	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
	
	/* id-props */
	// XXX should we make this into separate operators?
	RNA_def_enum(ot->srna, "left_right", prop_actkeys_leftright_select_types, 0, "Left Right", ""); // CTRLKEY
	RNA_def_boolean(ot->srna, "extend", 0, "Extend Select", ""); // SHIFTKEY
	RNA_def_boolean(ot->srna, "column", 0, "Column Select", ""); // ALTKEY
}

/* ************************************************************************** */

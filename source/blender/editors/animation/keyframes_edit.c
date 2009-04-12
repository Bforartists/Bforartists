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
 * The Original Code is Copyright (C) 2008 Blender Foundation
 *
 * Contributor(s): Joshua Leung
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <float.h>

#include "MEM_guardedalloc.h"

#include "BLI_blenlib.h"
#include "BLI_arithb.h"

#include "DNA_anim_types.h"
#include "DNA_action_types.h"
#include "DNA_curve_types.h"
#include "DNA_key_types.h"
#include "DNA_object_types.h"
#include "DNA_space_types.h"
#include "DNA_scene_types.h"
#include "DNA_world_types.h"

#include "BKE_action.h"
#include "BKE_fcurve.h"
#include "BKE_key.h"
#include "BKE_utildefines.h"

#include "ED_anim_api.h"
#include "ED_keyframes_edit.h"
#include "ED_markers.h"

/* This file defines an API and set of callback-operators for non-destructive editing of keyframe data.
 *
 * Two API functions are defined for actually performing the operations on the data:
 *			ANIM_fcurve_keys_bezier_loop()
 * which take the data they operate on, a few callbacks defining what operations to perform.
 *
 * As operators which work on keyframes usually apply the same operation on all BezTriples in 
 * every channel, the code has been optimised providing a set of functions which will get the 
 * appropriate bezier-modify function to set. These functions (ANIM_editkeyframes_*) will need
 * to be called before getting any channels.
 * 
 * A set of 'validation' callbacks are provided for checking if a BezTriple should be operated on.
 * These should only be used when using a 'general' BezTriple editor (i.e. selection setters which 
 * don't check existing selection status).
 * 
 * - Joshua Leung, Dec 2008
 */

/* ************************************************************************** */
/* Keyframe Editing Loops - Exposed API */

/* --------------------------- Base Functions ------------------------------------ */

/* This function is used to loop over BezTriples in the given F-Curve, applying a given 
 * operation on them, and optionally applies an F-Curve validation function afterwards.
 */
short ANIM_fcurve_keys_bezier_loop(BeztEditData *bed, FCurve *fcu, BeztEditFunc bezt_ok, BeztEditFunc bezt_cb, FcuEditFunc fcu_cb) 
{
    BezTriple *bezt;
	int b;
	
	/* sanity check */
	if (ELEM(NULL, fcu, fcu->bezt))
		return 0;
	
	/* if function to apply to bezier curves is set, then loop through executing it on beztriples */
    if (bezt_cb) {
		/* if there's a validation func, include that check in the loop 
		 * (this is should be more efficient than checking for it in every loop)
		 */
		if (bezt_ok) {
			for (b=0, bezt=fcu->bezt; b < fcu->totvert; b++, bezt++) {
				/* Only operate on this BezTriple if it fullfills the criteria of the validation func */
				if (bezt_ok(bed, bezt)) {
					/* Exit with return-code '1' if function returns positive
					 * This is useful if finding if some BezTriple satisfies a condition.
					 */
			        if (bezt_cb(bed, bezt)) return 1;
				}
			}
		}
		else {
			for (b=0, bezt=fcu->bezt; b < fcu->totvert; b++, bezt++) {
				/* Exit with return-code '1' if function returns positive
				 * This is useful if finding if some BezTriple satisfies a condition.
				 */
		        if (bezt_cb(bed, bezt)) return 1;
			}
		}
    }

    /* if fcu_cb (F-Curve post-editing callback) has been specified then execute it */
    if (fcu_cb)
        fcu_cb(fcu);
	
	/* done */	
    return 0;
}

/* -------------------------------- Further Abstracted (Not Exposed Directly) ----------------------------- */

/* This function is used to loop over the keyframe data in an Action Group */
static short agrp_keys_bezier_loop(BeztEditData *bed, bActionGroup *agrp, BeztEditFunc bezt_ok, BeztEditFunc bezt_cb, FcuEditFunc fcu_cb)
{
	FCurve *fcu;
	
	/* only iterate over the F-Curves that are in this group */
	for (fcu= agrp->channels.first; fcu && fcu->grp==agrp; fcu= fcu->next) {
		if (ANIM_fcurve_keys_bezier_loop(bed, fcu, bezt_ok, bezt_cb, fcu_cb))
			return 1;
	}
	
	return 0;
}

/* This function is used to loop over the keyframe data in an Action */
static short act_keys_bezier_loop(BeztEditData *bed, bAction *act, BeztEditFunc bezt_ok, BeztEditFunc bezt_cb, FcuEditFunc fcu_cb)
{
	FCurve *fcu;
	
	/* just loop through all F-Curves */
	for (fcu= act->curves.first; fcu; fcu= fcu->next) {
		if (ANIM_fcurve_keys_bezier_loop(bed, fcu, bezt_ok, bezt_cb, fcu_cb))
			return 1;
	}
	
	return 0;
}

/* This function is used to loop over the keyframe data of an AnimData block */
static short adt_keys_bezier_loop(BeztEditData *bed, AnimData *adt, BeztEditFunc bezt_ok, BeztEditFunc bezt_cb, FcuEditFunc fcu_cb, int filterflag)
{
	/* drivers or actions? */
	if (filterflag & ADS_FILTER_ONLYDRIVERS) {
		FCurve *fcu;
		
		/* just loop through all F-Curves acting as Drivers */
		for (fcu= adt->drivers.first; fcu; fcu= fcu->next) {
			if (ANIM_fcurve_keys_bezier_loop(bed, fcu, bezt_ok, bezt_cb, fcu_cb))
				return 1;
		}
	}
	else if (adt->action) {
		/* call the function for actions */
		if (act_keys_bezier_loop(bed, adt->action, bezt_ok, bezt_cb, fcu_cb))
			return 1;
	}
	
	return 0;
}

/* This function is used to loop over the keyframe data in an Object */
static short ob_keys_bezier_loop(BeztEditData *bed, Object *ob, BeztEditFunc bezt_ok, BeztEditFunc bezt_cb, FcuEditFunc fcu_cb, int filterflag)
{
	Key *key= ob_get_key(ob);
	
	/* firstly, Object's own AnimData */
	if (ob->adt) 
		adt_keys_bezier_loop(bed, ob->adt, bezt_ok, bezt_cb, fcu_cb, filterflag);
	
	/* shapekeys */
	if ((key && key->adt) && !(filterflag & ADS_FILTER_NOSHAPEKEYS))
		adt_keys_bezier_loop(bed, key->adt, bezt_ok, bezt_cb, fcu_cb, filterflag);
		
	// FIXME: add materials, etc. (but drawing code doesn't do it yet too! :)
	
	return 0;
}

/* This function is used to loop over the keyframe data in a Scene */
static short scene_keys_bezier_loop(BeztEditData *bed, Scene *sce, BeztEditFunc bezt_ok, BeztEditFunc bezt_cb, FcuEditFunc fcu_cb, int filterflag)
{
	World *wo= sce->world;
	
	/* Scene's own animation */
	if (sce->adt)
		adt_keys_bezier_loop(bed, sce->adt, bezt_ok, bezt_cb, fcu_cb, filterflag);
	
	/* World */
	if (wo && wo->adt)
		adt_keys_bezier_loop(bed, wo->adt, bezt_ok, bezt_cb, fcu_cb, filterflag);
	
	return 0;
}

/* --- */

/* This function is used to apply operation to all keyframes, regardless of the type */
short ANIM_animchannel_keys_bezier_loop(BeztEditData *bed, bAnimListElem *ale, BeztEditFunc bezt_ok, BeztEditFunc bezt_cb, FcuEditFunc fcu_cb, int filterflag)
{
	/* sanity checks */
	if (ale == NULL)
		return 0;
	
	/* method to use depends on the type of keyframe data */
	switch (ale->datatype) {
		/* direct keyframe data (these loops are exposed) */
		case ALE_FCURVE: /* F-Curve */
			return ANIM_fcurve_keys_bezier_loop(bed, ale->key_data, bezt_ok, bezt_cb, fcu_cb);
		
		/* indirect 'summaries' (these are not exposed directly) 
		 * NOTE: must keep this code in sync with the drawing code and also the filtering code!
		 */
		case ALE_GROUP: /* action group */
			return agrp_keys_bezier_loop(bed, (bActionGroup *)ale->data, bezt_ok, bezt_cb, fcu_cb);
		case ALE_ACT: /* action */
			return act_keys_bezier_loop(bed, (bAction *)ale->data, bezt_ok, bezt_cb, fcu_cb);
			
		case ALE_OB: /* object */
			return ob_keys_bezier_loop(bed, (Object *)ale->data, bezt_ok, bezt_cb, fcu_cb, filterflag);
		case ALE_SCE: /* scene */
			return scene_keys_bezier_loop(bed, (Scene *)ale->data, bezt_ok, bezt_cb, fcu_cb, filterflag);
	}
	
	return 0;
}

/* ************************************************************************** */
/* Keyframe Integrity Tools */

/* Rearrange keyframes if some are out of order */
// used to be recalc_*_ipos() where * was object or action
void ANIM_editkeyframes_refresh(bAnimContext *ac)
{
	ListBase anim_data = {NULL, NULL};
	bAnimListElem *ale;
	int filter;
	
	/* filter animation data */
	filter= ANIMFILTER_CURVESONLY; 
	ANIM_animdata_filter(ac, &anim_data, filter, ac->data, ac->datatype);
	
	/* loop over ipo-curves that are likely to have been edited, and check them */
	for (ale= anim_data.first; ale; ale= ale->next) {
		FCurve *fcu= ale->key_data;
		
		/* make sure keyframes in F-curve are all in order, and handles are in valid positions */
		sort_time_fcurve(fcu);
		testhandles_fcurve(fcu);
	}
	
	/* free temp data */
	BLI_freelistN(&anim_data);
}

/* ************************************************************************** */
/* BezTriple Validation Callbacks */

static short ok_bezier_frame(BeztEditData *bed, BezTriple *bezt)
{
	/* frame is stored in f1 property (this float accuracy check may need to be dropped?) */
	return IS_EQ(bezt->vec[1][0], bed->f1);
}

static short ok_bezier_framerange(BeztEditData *bed, BezTriple *bezt)
{
	/* frame range is stored in float properties */
	return ((bezt->vec[1][0] > bed->f1) && (bezt->vec[1][0] < bed->f2));
}

static short ok_bezier_selected(BeztEditData *bed, BezTriple *bezt)
{
	/* this macro checks all beztriple handles for selection... */
	return BEZSELECTED(bezt);
}

static short ok_bezier_value(BeztEditData *bed, BezTriple *bezt)
{
	/* value is stored in f1 property 
	 *	- this float accuracy check may need to be dropped?
	 *	- should value be stored in f2 instead so that we won't have conflicts when using f1 for frames too?
	 */
	return IS_EQ(bezt->vec[1][1], bed->f1);
}

static short ok_bezier_valuerange(BeztEditData *bed, BezTriple *bezt)
{
	/* value range is stored in float properties */
	return ((bezt->vec[1][1] > bed->f1) && (bezt->vec[1][1] < bed->f2));
}

static short ok_bezier_region(BeztEditData *bed, BezTriple *bezt)
{
	/* rect is stored in data property (it's of type rectf, but may not be set) */
	if (bed->data)
		return BLI_in_rctf(bed->data, bezt->vec[1][0], bezt->vec[1][1]);
	else 
		return 0;
}


BeztEditFunc ANIM_editkeyframes_ok(short mode)
{
	/* eEditKeyframes_Validate */
	switch (mode) {
		case BEZT_OK_FRAME: /* only if bezt falls on the right frame (float) */
			return ok_bezier_frame;
		case BEZT_OK_FRAMERANGE: /* only if bezt falls within the specified frame range (floats) */
			return ok_bezier_framerange;
		case BEZT_OK_SELECTED:	/* only if bezt is selected (self) */
			return ok_bezier_selected;
		case BEZT_OK_VALUE: /* only if bezt value matches (float) */
			return ok_bezier_value;
		case BEZT_OK_VALUERANGE: /* only if bezier falls within the specified value range (floats) */
			return ok_bezier_valuerange;
		case BEZT_OK_REGION: /* only if bezier falls within the specified rect (data -> rectf) */
			return ok_bezier_region;
		default: /* nothing was ok */
			return NULL;
	}
}

/* ******************************************* */
/* Assorted Utility Functions */

/* helper callback for <animeditor>_cfrasnap_exec() -> used to help get the average time of all selected beztriples */
short bezt_calc_average(BeztEditData *bed, BezTriple *bezt)
{
	/* only if selected */
	if (bezt->f2 & SELECT) {
		/* store average time in float (only do rounding at last step */
		bed->f1 += bezt->vec[1][0];
		
		/* increment number of items */
		bed->i1++;
	}
	
	return 0;
}

/* ******************************************* */
/* Transform */

static short snap_bezier_nearest(BeztEditData *bed, BezTriple *bezt)
{
	if (bezt->f2 & SELECT)
		bezt->vec[1][0]= (float)(floor(bezt->vec[1][0]+0.5));
	return 0;
}

static short snap_bezier_nearestsec(BeztEditData *bed, BezTriple *bezt)
{
	const Scene *scene= bed->scene;
	const float secf = (float)FPS;
	
	if (bezt->f2 & SELECT)
		bezt->vec[1][0]= ((float)floor(bezt->vec[1][0]/secf + 0.5f) * secf);
	return 0;
}

static short snap_bezier_cframe(BeztEditData *bed, BezTriple *bezt)
{
	const Scene *scene= bed->scene;
	if (bezt->f2 & SELECT)
		bezt->vec[1][0]= (float)CFRA;
	return 0;
}

static short snap_bezier_nearmarker(BeztEditData *bed, BezTriple *bezt)
{
	//if (bezt->f2 & SELECT)
	//	bezt->vec[1][0]= (float)find_nearest_marker_time(bezt->vec[1][0]);  // XXX missing function!
	return 0;
}

static short snap_bezier_horizontal(BeztEditData *bed, BezTriple *bezt)
{
	if (bezt->f2 & SELECT) {
		bezt->vec[0][1]= bezt->vec[2][1]= bezt->vec[1][1];
		if ((bezt->h1==HD_AUTO) || (bezt->h1==HD_VECT)) bezt->h1= HD_ALIGN;
		if ((bezt->h2==HD_AUTO) || (bezt->h2==HD_VECT)) bezt->h2= HD_ALIGN;
	}
	return 0;	
}

// calchandles_ipocurve
BeztEditFunc ANIM_editkeyframes_snap(short type)
{
	/* eEditKeyframes_Snap */
	switch (type) {
		case SNAP_KEYS_NEARFRAME: /* snap to nearest frame */
			return snap_bezier_nearest;
		case SNAP_KEYS_CURFRAME: /* snap to current frame */
			return snap_bezier_cframe;
		case SNAP_KEYS_NEARMARKER: /* snap to nearest marker */
			return snap_bezier_nearmarker;
		case SNAP_KEYS_NEARSEC: /* snap to nearest second */
			return snap_bezier_nearestsec;
		case SNAP_KEYS_HORIZONTAL: /* snap handles to same value */
			return snap_bezier_horizontal;
		default: /* just in case */
			return snap_bezier_nearest;
	}
}

/* --------- */

static short mirror_bezier_cframe(BeztEditData *bed, BezTriple *bezt)
{
	const Scene *scene= bed->scene;
	float diff;
	
	if (bezt->f2 & SELECT) {
		diff= ((float)CFRA - bezt->vec[1][0]);
		bezt->vec[1][0]= ((float)CFRA + diff);
	}
	
	return 0;
}

static short mirror_bezier_yaxis(BeztEditData *bed, BezTriple *bezt)
{
	float diff;
	
	if (bezt->f2 & SELECT) {
		diff= (0.0f - bezt->vec[1][0]);
		bezt->vec[1][0]= (0.0f + diff);
	}
	
	return 0;
}

static short mirror_bezier_xaxis(BeztEditData *bed, BezTriple *bezt)
{
	float diff;
	
	if (bezt->f2 & SELECT) {
		diff= (0.0f - bezt->vec[1][1]);
		bezt->vec[1][1]= (0.0f + diff);
	}
	
	return 0;
}

static short mirror_bezier_marker(BeztEditData *bed, BezTriple *bezt)
{
	/* mirroring time stored in f1 */
	if (bezt->f2 & SELECT) {
		const float diff= (bed->f1 - bezt->vec[1][0]);
		bezt->vec[1][0]= (bed->f1 + diff);
	}
	
	return 0;
}

/* Note: for markers case, need to set global vars (eww...) */
// calchandles_fcurve
BeztEditFunc ANIM_editkeyframes_mirror(short type)
{
	switch (type) {
		case MIRROR_KEYS_CURFRAME: /* mirror over current frame */
			return mirror_bezier_cframe;
		case MIRROR_KEYS_YAXIS: /* mirror over frame 0 */
			return mirror_bezier_yaxis;
		case MIRROR_KEYS_XAXIS: /* mirror over value 0 */
			return mirror_bezier_xaxis;
		case MIRROR_KEYS_MARKER: /* mirror over marker */
			return mirror_bezier_marker; 
		default: /* just in case */
			return mirror_bezier_yaxis;
			break;
	}
}

/* ******************************************* */
/* Settings */

/* Sets the selected bezier handles to type 'auto' */
static short set_bezier_auto(BeztEditData *bed, BezTriple *bezt) 
{
	if((bezt->f1  & SELECT) || (bezt->f3 & SELECT)) {
		if (bezt->f1 & SELECT) bezt->h1= 1; /* the secret code for auto */
		if (bezt->f3 & SELECT) bezt->h2= 1;
		
		/* if the handles are not of the same type, set them
		 * to type free
		 */
		if (bezt->h1 != bezt->h2) {
			if ELEM(bezt->h1, HD_ALIGN, HD_AUTO) bezt->h1= HD_FREE;
			if ELEM(bezt->h2, HD_ALIGN, HD_AUTO) bezt->h2= HD_FREE;
		}
	}
	return 0;
}

/* Sets the selected bezier handles to type 'vector'  */
static short set_bezier_vector(BeztEditData *bed, BezTriple *bezt) 
{
	if ((bezt->f1 & SELECT) || (bezt->f3 & SELECT)) {
		if (bezt->f1 & SELECT) bezt->h1= HD_VECT;
		if (bezt->f3 & SELECT) bezt->h2= HD_VECT;
		
		/* if the handles are not of the same type, set them
		 * to type free
		 */
		if (bezt->h1 != bezt->h2) {
			if ELEM(bezt->h1, HD_ALIGN, HD_AUTO) bezt->h1= HD_FREE;
			if ELEM(bezt->h2, HD_ALIGN, HD_AUTO) bezt->h2= HD_FREE;
		}
	}
	return 0;
}

/* Queries if the handle should be set to 'free' or 'align' */
static short bezier_isfree(BeztEditData *bed, BezTriple *bezt) 
{
	if ((bezt->f1 & SELECT) && (bezt->h1)) return 1;
	if ((bezt->f3 & SELECT) && (bezt->h2)) return 1;
	return 0;
}

/* Sets selected bezier handles to type 'align' */
static short set_bezier_align(BeztEditData *bed, BezTriple *bezt) 
{	
	if (bezt->f1 & SELECT) bezt->h1= HD_ALIGN;
	if (bezt->f3 & SELECT) bezt->h2= HD_ALIGN;
	return 0;
}

/* Sets selected bezier handles to type 'free'  */
static short set_bezier_free(BeztEditData *bed, BezTriple *bezt) 
{
	if (bezt->f1 & SELECT) bezt->h1= HD_FREE;
	if (bezt->f3 & SELECT) bezt->h2= HD_FREE;
	return 0;
}

/* Set all Bezier Handles to a single type */
// calchandles_fcurve
BeztEditFunc ANIM_editkeyframes_handles(short code)
{
	switch (code) {
		case HD_AUTO: /* auto */
			return set_bezier_auto;
		case HD_VECT: /* vector */
			return set_bezier_vector;
		case HD_FREE: /* free */
			return set_bezier_free;
		case HD_ALIGN: /* align */
			return set_bezier_align;
		
		default: /* free or align? */
			return bezier_isfree;
	}
}

/* ------- */

static short set_bezt_constant(BeztEditData *bed, BezTriple *bezt) 
{
	if (bezt->f2 & SELECT) 
		bezt->ipo= BEZT_IPO_CONST;
	return 0;
}

static short set_bezt_linear(BeztEditData *bed, BezTriple *bezt) 
{
	if (bezt->f2 & SELECT) 
		bezt->ipo= BEZT_IPO_LIN;
	return 0;
}

static short set_bezt_bezier(BeztEditData *bed, BezTriple *bezt) 
{
	if (bezt->f2 & SELECT) 
		bezt->ipo= BEZT_IPO_BEZ;
	return 0;
}

/* Set the interpolation type of the selected BezTriples in each IPO curve to the specified one */
// ANIM_editkeyframes_ipocurve_ipotype() !
BeztEditFunc ANIM_editkeyframes_ipo(short code)
{
	switch (code) {
		case BEZT_IPO_CONST: /* constant */
			return set_bezt_constant;
		case BEZT_IPO_LIN: /* linear */	
			return set_bezt_linear;
		default: /* bezier */
			return set_bezt_bezier;
	}
}

/* ******************************************* */
/* Selection */

static short select_bezier_add(BeztEditData *bed, BezTriple *bezt) 
{
	/* Select the bezier triple */
	BEZ_SEL(bezt);
	return 0;
}

static short select_bezier_subtract(BeztEditData *bed, BezTriple *bezt) 
{
	/* Deselect the bezier triple */
	BEZ_DESEL(bezt);
	return 0;
}

static short select_bezier_invert(BeztEditData *bed, BezTriple *bezt) 
{
	/* Invert the selection for the bezier triple */
	bezt->f2 ^= SELECT;
	if (bezt->f2 & SELECT) {
		bezt->f1 |= SELECT;
		bezt->f3 |= SELECT;
	}
	else {
		bezt->f1 &= ~SELECT;
		bezt->f3 &= ~SELECT;
	}
	return 0;
}

// NULL
BeztEditFunc ANIM_editkeyframes_select(short selectmode)
{
	switch (selectmode) {
		case SELECT_ADD: /* add */
			return select_bezier_add;
		case SELECT_SUBTRACT: /* subtract */
			return select_bezier_subtract;
		case SELECT_INVERT: /* invert */
			return select_bezier_invert;
		default: /* replace (need to clear all, then add) */
			return select_bezier_add;
	}
}

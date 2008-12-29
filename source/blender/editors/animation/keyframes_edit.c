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

#include "DNA_action_types.h"
#include "DNA_curve_types.h"
#include "DNA_ipo_types.h"
#include "DNA_key_types.h"
#include "DNA_object_types.h"
#include "DNA_space_types.h"
#include "DNA_scene_types.h"

#include "BKE_action.h"
#include "BKE_ipo.h"
#include "BKE_key.h"
#include "BKE_utildefines.h"

#include "ED_anim_api.h"
#include "ED_keyframes_edit.h"
#include "ED_markers.h"

/* This file defines an API and set of callback-operators for non-destructive editing of keyframe data.
 *
 * Two API functions are defined for actually performing the operations on the data:
 *			ipo_keys_bezier_loop() and icu_keys_bezier_loop()
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
/* IPO Editing Loops - Exposed API */

/* --------------------------- Base Functions ------------------------------------ */

/* This function is used to loop over BezTriples in the given IpoCurve, applying a given 
 * operation on them, and optionally applies an IPO-curve validate function afterwards.
 */
short icu_keys_bezier_loop(BeztEditData *bed, IpoCurve *icu, BeztEditFunc bezt_ok, BeztEditFunc bezt_cb, IcuEditFunc icu_cb) 
{
    BezTriple *bezt;
	int b;
	
	/* if function to apply to bezier curves is set, then loop through executing it on beztriples */
    if (bezt_cb) {
		/* if there's a validation func, include that check in the loop 
		 * (this is should be more efficient than checking for it in every loop)
		 */
		if (bezt_ok) {
			for (b=0, bezt=icu->bezt; b < icu->totvert; b++, bezt++) {
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
			for (b=0, bezt=icu->bezt; b < icu->totvert; b++, bezt++) {
				/* Exit with return-code '1' if function returns positive
				 * This is useful if finding if some BezTriple satisfies a condition.
				 */
		        if (bezt_cb(bed, bezt)) return 1;
			}
		}
    }

    /* if ipocurve_function has been specified then execute it */
    if (icu_cb)
        icu_cb(icu);
	
	/* done */	
    return 0;
}

/* This function is used to loop over the IPO curves (and subsequently the keyframes in them) */
short ipo_keys_bezier_loop(BeztEditData *bed, Ipo *ipo, BeztEditFunc bezt_ok, BeztEditFunc bezt_cb, IcuEditFunc icu_cb)
{
    IpoCurve *icu;
	
	/* Sanity check */
	if (ipo == NULL)
		return 0;
	
    /* Loop through each curve in the Ipo */
    for (icu= ipo->curve.first; icu; icu=icu->next) {
        if (icu_keys_bezier_loop(bed, icu, bezt_ok, bezt_cb, icu_cb))
            return 1;
    }

    return 0;
}

/* -------------------------------- Further Abstracted ----------------------------- */

/* This function is used to apply operation to all keyframes, regardless of the type */
short animchannel_keys_bezier_loop(BeztEditData *bed, bAnimListElem *ale, BeztEditFunc bezt_ok, BeztEditFunc bezt_cb, IcuEditFunc icu_cb)
{
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
	filter= ANIMFILTER_ONLYICU;
	ANIM_animdata_filter(&anim_data, filter, ac->data, ac->datatype);
	
	/* loop over ipo-curves that are likely to have been edited, and check them */
	for (ale= anim_data.first; ale; ale= ale->next) {
		IpoCurve *icu= ale->key_data;
		
		/* make sure keyframes in IPO-curve are all in order, and handles are in valid positions */
		sort_time_ipocurve(icu);
		testhandles_ipocurve(icu);
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


BeztEditFunc ANIM_editkeyframes_ok(short mode)
{
	/* eEditKeyframes_Validate */
	switch (mode) {
		case BEZT_OK_FRAME: /* only if bezt falls on the right frame (float) */
			return ok_bezier_frame;
		case BEZT_OK_FRAMERANGE: /* only if bezt falls within the specified frame range (floats) */
			return ok_bezier_framerange;
		case BEZT_OK_SELECTED:	/* only if bezt is selected */
			return ok_bezier_selected;
		case BEZT_OK_VALUE: /* only if bezt value matches (float) */
			return ok_bezier_value;
		default: /* nothing was ok */
			return NULL;
	}
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
	const float secf = FPS;
	
	if (bezt->f2 & SELECT)
		bezt->vec[1][0]= (float)(floor(bezt->vec[1][0]/secf + 0.5f) * secf);
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
// calchandles_ipocurve
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

/* --------- */

/* This function is called to calculate the average location of the
 * selected keyframes, and place the current frame at that location.
 *
 * It must be called like so:
 *	snap_cfra_ipo_keys(scene, NULL, -1); // initialise the static vars first
 *	for (ipo...) snap_cfra_ipo_keys(scene, ipo, 0); // sum up keyframe times
 *	snap_cfra_ipo_keys(scene, NULL, 1); // set current frame after taking average
 */
// XXX this thing needs to be refactored!
void snap_cfra_ipo_keys(BeztEditData *bed, Ipo *ipo, short mode)
{
	static int cfra;
	static int tot;
	
	Scene *scene= bed->scene;
	IpoCurve *icu;
	BezTriple *bezt;
	int a;
	
	
	if (mode == -1) {
		/* initialise a new snap-operation */
		cfra= 0;
		tot= 0;
	}
	else if (mode == 1) {
		/* set current frame - using average frame */
		if (tot != 0)
			CFRA = cfra / tot;
	}
	else {
		/* loop through keys in ipo, summing the frame
		 * numbers of those that are selected 
		 */
		if (ipo == NULL) 
			return;
		
		for (icu= ipo->curve.first; icu; icu= icu->next) {
			for (a=0, bezt=icu->bezt; a < icu->totvert; a++, bezt++) {
				if (BEZSELECTED(bezt)) {
					cfra += bezt->vec[1][0];
					tot++;
				}
			}
		}
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
// calchandles_ipocurve
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

/* IPO-curve sanity callback - the name of this is a bit unwieldy, by is best to keep this in style... */
// was called set_ipocurve_mixed()
void ANIM_editkeyframes_ipocurve_ipotype(IpoCurve *icu)
{
	/* Sets the type of the IPO curve to mixed, as some (selected)
	 * keyframes were set to other interpolation types
	 */
	icu->ipo= IPO_MIXED;
	
	/* recalculate handles, as some changes may have occurred */
	calchandles_ipocurve(icu);
}

static short set_bezt_constant(BeztEditData *bed, BezTriple *bezt) 
{
	if (bezt->f2 & SELECT) 
		bezt->ipo= IPO_CONST;
	return 0;
}

static short set_bezt_linear(BeztEditData *bed, BezTriple *bezt) 
{
	if (bezt->f2 & SELECT) 
		bezt->ipo= IPO_LIN;
	return 0;
}

static short set_bezt_bezier(BeztEditData *bed, BezTriple *bezt) 
{
	if (bezt->f2 & SELECT) 
		bezt->ipo= IPO_BEZ;
	return 0;
}

/* Set the interpolation type of the selected BezTriples in each IPO curve to the specified one */
// ANIM_editkeyframes_ipocurve_ipotype() !
BeztEditFunc ANIM_editkeyframes_ipo(short code)
{
	switch (code) {
		case IPO_CONST: /* constant */
			return set_bezt_constant;
		case IPO_LIN: /* linear */	
			return set_bezt_linear;
		default: /* bezier */
			return set_bezt_bezier;
	}
}

// XXX will we keep this?
void setexprap_ipoloop(Ipo *ipo, short code)
{
	IpoCurve *icu;
	
	/* Loop through each curve in the Ipo */
	for (icu=ipo->curve.first; icu; icu=icu->next)
		icu->extrap= code;
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


short is_ipo_key_selected(Ipo *ipo)
{
	IpoCurve *icu;
	BezTriple *bezt;
	int i;
	
	if (ipo == NULL)
		return 0;
	
	for (icu=ipo->curve.first; icu; icu=icu->next) {
		for (i=0, bezt=icu->bezt; i<icu->totvert; i++, bezt++) {
			if (BEZSELECTED(bezt))
				return 1;
		}
	}
	
	return 0;
}

// XXX although this is still needed, it should be removed!
void set_ipo_key_selection(Ipo *ipo, short sel)
{
	IpoCurve *icu;
	BezTriple *bezt;
	int i;
	
	if (ipo == NULL)
		return;
	
	for (icu=ipo->curve.first; icu; icu=icu->next) {
		for (i=0, bezt=icu->bezt; i<icu->totvert; i++, bezt++) {
			if (sel == 2) {
				BEZ_INVSEL(bezt);
			}
			else if (sel == 1) {
				BEZ_SEL(bezt);
			}
			else {
				BEZ_DESEL(bezt);
			}
		}
	}
}

// XXX port this over to the new system!
// err... this is this still used?
int fullselect_ipo_keys(Ipo *ipo)
{
	IpoCurve *icu;
	int tvtot = 0;
	int i;
	
	if (!ipo)
		return tvtot;
	
	for (icu=ipo->curve.first; icu; icu=icu->next) {
		for (i=0; i<icu->totvert; i++) {
			if (icu->bezt[i].f2 & SELECT) {
				tvtot+=3;
				icu->bezt[i].f1 |= SELECT;
				icu->bezt[i].f3 |= SELECT;
			}
		}
	}
	
	return tvtot;
}


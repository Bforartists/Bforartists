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
 * Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
 *
 * The Original Code is Copyright (C) 2009 Blender Foundation.
 * All rights reserved.
 *
 * 
 * Contributor(s): Blender Foundation, Joshua Leung
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#include <string.h>
#include <stdio.h>
#include <math.h>
#include <float.h>

#include "DNA_anim_types.h"
#include "DNA_space_types.h"
#include "DNA_screen_types.h"

#include "MEM_guardedalloc.h"

#include "BLI_math.h"
#include "BLI_blenlib.h"
#include "BLI_editVert.h"
#include "BLI_rand.h"

#include "BKE_context.h"
#include "BKE_fcurve.h"

#include "BIF_gl.h"

#include "WM_api.h"


#include "ED_anim_api.h"


#include "graph_intern.h"	// own include

/* ************************************************************** */
/* Active F-Curve */

/* Find 'active' F-Curve. It must be editable, since that's the purpose of these buttons (subject to change).  
 * We return the 'wrapper' since it contains valuable context info (about hierarchy), which will need to be freed 
 * when the caller is done with it.
 */
bAnimListElem *get_active_fcurve_channel (bAnimContext *ac)
{
	ListBase anim_data = {NULL, NULL};
	int filter= (ANIMFILTER_VISIBLE | ANIMFILTER_FOREDIT | ANIMFILTER_ACTIVE | ANIMFILTER_CURVESONLY);
	int items = ANIM_animdata_filter(ac, &anim_data, filter, ac->data, ac->datatype);
	
	/* We take the first F-Curve only, since some other ones may have had 'active' flag set
	 * if they were from linked data.
	 */
	if (items) {
		bAnimListElem *ale= (bAnimListElem *)anim_data.first;
		
		/* remove first item from list, then free the rest of the list and return the stored one */
		BLI_remlink(&anim_data, ale);
		BLI_freelistN(&anim_data);
		
		return ale;
	}
	
	/* no active F-Curve */
	return NULL;
}

/* ************************************************************** */
/* Operator Polling Callbacks */

/* check if any FModifiers to draw controls for  - fcm is 'active' modifier 
 * used for the polling callbacks + also for drawing
 */
// TODO: restructure these tests
// TODO: maybe for now, just allow editing always for now...
short fcurve_needs_draw_fmodifier_controls (FCurve *fcu, FModifier *fcm)
{
	/* don't draw if there aren't any modifiers at all */
	if (fcu->modifiers.first == NULL) 
		return 0;
	
	/* if only one modifier 
	 *	- don't draw if it is muted or disabled 
	 *	- set it as the active one if no active one is present 
	 */
	if (fcu->modifiers.first == fcu->modifiers.last) {
		fcm= fcu->modifiers.first;
		if (fcm->flag & (FMODIFIER_FLAG_DISABLED|FMODIFIER_FLAG_MUTED)) 
			return 0;
	}
	
	/* if there's an active modifier - don't draw if it doesn't drastically
	 * alter the curve...
	 */
	if (fcm) {
		switch (fcm->type) {
			/* clearly harmless */
			case FMODIFIER_TYPE_CYCLES:
				return 0;
			case FMODIFIER_TYPE_STEPPED:
				return 0;
				
			/* borderline... */
			case FMODIFIER_TYPE_NOISE:
				return 0;
		}
	}
	
	/* if only active modifier - don't draw if it is muted or disabled */
	if (fcm) {
		if (fcm->flag & (FMODIFIER_FLAG_DISABLED|FMODIFIER_FLAG_MUTED)) 
			return 0;
	}
	
	/* if we're still here, this means that there are modifiers with controls to be drawn */
	// FIXME: what happens if all the modifiers were muted/disabled
	return 1;
}

/* ------------------- */

/* Check if there are any visible keyframes (for selection tools) */
int graphop_visible_keyframes_poll (bContext *C)
{
	bAnimContext ac;
	bAnimListElem *ale;
	ListBase anim_data = {NULL, NULL};
	ScrArea *sa= CTX_wm_area(C);
	int filter, items;
	short found = 0;
	
	/* firstly, check if in Graph Editor */
	// TODO: also check for region?
	if ((sa == NULL) || (sa->spacetype != SPACE_IPO))
		return 0;
		
	/* try to init Anim-Context stuff ourselves and check */
	if (ANIM_animdata_get_context(C, &ac) == 0)
		return 0;
	
	/* loop over the visible (selection doesn't matter) F-Curves, and see if they're suitable
	 * stopping on the first successful match
	 */
	filter= (ANIMFILTER_VISIBLE | ANIMFILTER_CURVESONLY);
	items = ANIM_animdata_filter(&ac, &anim_data, filter, ac.data, ac.datatype);
	if (items == 0) 
		return 0;
	
	for (ale = anim_data.first; ale; ale= ale->next) {
		FCurve *fcu= (FCurve *)ale->data;
		FModifier *fcm;
		
		/* visible curves for selection must fulfull the following criteria:
		 *	- it has bezier keyframes
		 *	- F-Curve modifiers do not interfere with the result too much 
		 *	  (i.e. the modifier-control drawing check returns false)
		 */
		if (fcu->bezt == NULL)
			continue;
		fcm= find_active_fmodifier(&fcu->modifiers);
		
		found= (fcurve_needs_draw_fmodifier_controls(fcu, fcm) == 0);
		if (found) break;
	}
	
	/* cleanup and return findings */
	BLI_freelistN(&anim_data);
	return found;
}

/* Check if there are any visible + editable keyframes (for editing tools) */
int graphop_editable_keyframes_poll (bContext *C)
{
	bAnimContext ac;
	bAnimListElem *ale;
	ListBase anim_data = {NULL, NULL};
	ScrArea *sa= CTX_wm_area(C);
	int filter, items;
	short found = 0;
	
	/* firstly, check if in Graph Editor */
	// TODO: also check for region?
	if ((sa == NULL) || (sa->spacetype != SPACE_IPO))
		return 0;
		
	/* try to init Anim-Context stuff ourselves and check */
	if (ANIM_animdata_get_context(C, &ac) == 0)
		return 0;
	
	/* loop over the editable F-Curves, and see if they're suitable
	 * stopping on the first successful match
	 */
	filter= (ANIMFILTER_VISIBLE | ANIMFILTER_FOREDIT | ANIMFILTER_CURVESONLY);
	items = ANIM_animdata_filter(&ac, &anim_data, filter, ac.data, ac.datatype);
	if (items == 0) 
		return 0;
	
	for (ale = anim_data.first; ale; ale= ale->next) {
		FCurve *fcu= (FCurve *)ale->data;
		FModifier *fcm;
		
		/* editable curves must fulfull the following criteria:
		 *	- it has bezier keyframes
		 *	- it must not be protected from editing (this is already checked for with the foredit flag
		 *	- F-Curve modifiers do not interfere with the result too much 
		 *	  (i.e. the modifier-control drawing check returns false)
		 */
		if (fcu->bezt == NULL)
			continue;
		fcm= find_active_fmodifier(&fcu->modifiers);
		
		found= (fcurve_needs_draw_fmodifier_controls(fcu, fcm) == 0);
		if (found) break;
	}
	
	/* cleanup and return findings */
	BLI_freelistN(&anim_data);
	return found;
}

/* has active F-Curve that's editable */
int graphop_active_fcurve_poll (bContext *C)
{
	bAnimContext ac;
	bAnimListElem *ale;
	ScrArea *sa= CTX_wm_area(C);
	short has_fcurve= 0;
	
	/* firstly, check if in Graph Editor */
	// TODO: also check for region?
	if ((sa == NULL) || (sa->spacetype != SPACE_IPO))
		return 0;
		
	/* try to init Anim-Context stuff ourselves and check */
	if (ANIM_animdata_get_context(C, &ac) == 0)
		return 0;
		
	/* try to get the Active F-Curve */
	ale= get_active_fcurve_channel(&ac);
	if (ale == NULL)
		return 0;
		
	/* free temp data... */
	has_fcurve= ((ale->data) && (ale->type == ANIMTYPE_FCURVE));
	MEM_freeN(ale);
	
	/* return success */
	return has_fcurve;
}

/* has selected F-Curve that's editable */
int graphop_selected_fcurve_poll (bContext *C)
{
	bAnimContext ac;
	ListBase anim_data = {NULL, NULL};
	ScrArea *sa= CTX_wm_area(C);
	int filter, items;
	
	/* firstly, check if in Graph Editor */
	// TODO: also check for region?
	if ((sa == NULL) || (sa->spacetype != SPACE_IPO))
		return 0;
		
	/* try to init Anim-Context stuff ourselves and check */
	if (ANIM_animdata_get_context(C, &ac) == 0)
		return 0;
	
	/* get the editable + selected F-Curves, and as long as we got some, we can return */
	filter= (ANIMFILTER_VISIBLE | ANIMFILTER_SEL | ANIMFILTER_FOREDIT | ANIMFILTER_CURVESONLY);
	items = ANIM_animdata_filter(&ac, &anim_data, filter, ac.data, ac.datatype);
	if (items == 0) 
		return 0;
	
	/* cleanup and return findings */
	BLI_freelistN(&anim_data);
	return 1;
}

/* ************************************************************** */

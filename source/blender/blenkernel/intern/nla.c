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
 * The Original Code is Copyright (C) 2009 Blender Foundation, Joshua Leung
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): Joshua Leung (full recode)
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#include <stdlib.h>
#include <stddef.h>
#include <stdio.h>
#include <math.h>
#include <float.h>

#include "MEM_guardedalloc.h"

#include "BLI_blenlib.h"

#include "DNA_anim_types.h"
#include "DNA_action_types.h"

#include "BKE_animsys.h"
#include "BKE_action.h"
#include "BKE_fcurve.h"
#include "BKE_nla.h"
#include "BKE_blender.h"
#include "BKE_library.h"
#include "BKE_object.h"
#include "BKE_utildefines.h"

#include "RNA_access.h"
#include "nla_private.h"


#ifdef HAVE_CONFIG_H
#include <config.h>
#endif


/* *************************************************** */
/* Data Management */

/* Freeing ------------------------------------------- */

/* Remove the given NLA strip from the NLA track it occupies, free the strip's data,
 * and the strip itself. 
 */
void free_nlastrip (ListBase *strips, NlaStrip *strip)
{
	NlaStrip *cs, *csn;
	
	/* sanity checks */
	if (strip == NULL)
		return;
		
	/* free child-strips */
	for (cs= strip->strips.first; cs; cs= csn) {
		csn= cs->next;
		free_nlastrip(&strip->strips, cs);
	}
		
	/* remove reference to action */
	if (strip->act)
		strip->act->id.us--;
		
	/* free remapping info */
	//if (strip->remap)
	//	BKE_animremap_free();
	
	/* free own F-Curves */
	free_fcurves(&strip->fcurves);
	
	/* free own F-Modifiers */
	free_fmodifiers(&strip->modifiers);
	
	/* free the strip itself */
	if (strips)
		BLI_freelinkN(strips, strip);
	else
		MEM_freeN(strip);
}

/* Remove the given NLA track from the set of NLA tracks, free the track's data,
 * and the track itself.
 */
void free_nlatrack (ListBase *tracks, NlaTrack *nlt)
{
	NlaStrip *strip, *stripn;
	
	/* sanity checks */
	if (nlt == NULL)
		return;
		
	/* free strips */
	for (strip= nlt->strips.first; strip; strip= stripn) {
		stripn= strip->next;
		free_nlastrip(&nlt->strips, strip);
	}
	
	/* free NLA track itself now */
	if (tracks)
		BLI_freelinkN(tracks, nlt);
	else
		MEM_freeN(nlt);
}

/* Free the elements of type NLA Tracks provided in the given list, but do not free
 * the list itself since that is not free-standing
 */
void free_nladata (ListBase *tracks)
{
	NlaTrack *nlt, *nltn;
	
	/* sanity checks */
	if ELEM(NULL, tracks, tracks->first)
		return;
		
	/* free tracks one by one */
	for (nlt= tracks->first; nlt; nlt= nltn) {
		nltn= nlt->next;
		free_nlatrack(tracks, nlt);
	}
	
	/* clear the list's pointers to be safe */
	tracks->first= tracks->last= NULL;
}

/* Copying ------------------------------------------- */

/* Copy NLA strip */
NlaStrip *copy_nlastrip (NlaStrip *strip)
{
	NlaStrip *strip_d;
	NlaStrip *cs, *cs_d;
	
	/* sanity check */
	if (strip == NULL)
		return NULL;
		
	/* make a copy */
	strip_d= MEM_dupallocN(strip);
	strip_d->next= strip_d->prev= NULL;
	
	/* increase user-count of action */
	if (strip_d->act)
		strip_d->act->id.us++;
		
	/* copy F-Curves and modifiers */
	copy_fcurves(&strip_d->fcurves, &strip->fcurves);
	copy_fmodifiers(&strip_d->modifiers, &strip->modifiers);
	
	/* make a copy of all the child-strips, one at a time */
	strip_d->strips.first= strip_d->strips.last= NULL;
	
	for (cs= strip->strips.first; cs; cs= cs->next) {
		cs_d= copy_nlastrip(cs);
		BLI_addtail(&strip_d->strips, cs_d);
	}
	
	/* return the strip */
	return strip_d;
}

/* Copy NLA Track */
NlaTrack *copy_nlatrack (NlaTrack *nlt)
{
	NlaStrip *strip, *strip_d;
	NlaTrack *nlt_d;
	
	/* sanity check */
	if (nlt == NULL)
		return NULL;
		
	/* make a copy */
	nlt_d= MEM_dupallocN(nlt);
	nlt_d->next= nlt_d->prev= NULL;
	
	/* make a copy of all the strips, one at a time */
	nlt_d->strips.first= nlt_d->strips.last= NULL;
	
	for (strip= nlt->strips.first; strip; strip= strip->next) {
		strip_d= copy_nlastrip(strip);
		BLI_addtail(&nlt_d->strips, strip_d);
	}
	
	/* return the copy */
	return nlt_d;
}

/* Copy all NLA data */
void copy_nladata (ListBase *dst, ListBase *src)
{
	NlaTrack *nlt, *nlt_d;
	
	/* sanity checks */
	if ELEM(NULL, dst, src)
		return;
		
	/* copy each NLA-track, one at a time */
	for (nlt= src->first; nlt; nlt= nlt->next) {
		/* make a copy, and add the copy to the destination list */
		nlt_d= copy_nlatrack(nlt);
		BLI_addtail(dst, nlt_d);
	}
}

/* Adding ------------------------------------------- */

/* Add a NLA Track to the given AnimData 
 *	- prev: NLA-Track to add the new one after
 */
NlaTrack *add_nlatrack (AnimData *adt, NlaTrack *prev)
{
	NlaTrack *nlt;
	
	/* sanity checks */
	if (adt == NULL)
		return NULL;
		
	/* allocate new track */
	nlt= MEM_callocN(sizeof(NlaTrack), "NlaTrack");
	
	/* set settings requiring the track to not be part of the stack yet */
	nlt->flag = NLATRACK_SELECTED;
	nlt->index= BLI_countlist(&adt->nla_tracks);
	
	/* add track to stack, and make it the active one */
	if (prev)
		BLI_insertlinkafter(&adt->nla_tracks, prev, nlt);
	else
		BLI_addtail(&adt->nla_tracks, nlt);
	BKE_nlatrack_set_active(&adt->nla_tracks, nlt);
	
	/* must have unique name, but we need to seed this */
	sprintf(nlt->name, "NlaTrack");
	BLI_uniquename(&adt->nla_tracks, nlt, "NlaTrack", '.', offsetof(NlaTrack, name), 64);
	
	/* return the new track */
	return nlt;
}

/* Add a NLA Strip referencing the given Action */
NlaStrip *add_nlastrip (bAction *act)
{
	NlaStrip *strip;
	
	/* sanity checks */
	if (act == NULL)
		return NULL;
		
	/* allocate new strip */
	strip= MEM_callocN(sizeof(NlaStrip), "NlaStrip");
	
	/* generic settings 
	 *	- selected flag to highlight this to the user
	 *	- auto-blends to ensure that blend in/out values are automatically 
	 *	  determined by overlaps of strips
	 *	- (XXX) synchronisation of strip-length in accordance with changes to action-length
	 *	  is not done though, since this should only really happens in editmode for strips now
	 *	  though this decision is still subject to further review...
	 */
	strip->flag = NLASTRIP_FLAG_SELECT|NLASTRIP_FLAG_AUTO_BLENDS;
	
	/* assign the action reference */
	strip->act= act;
	id_us_plus(&act->id);
	
	/* determine initial range 
	 *	- strip length cannot be 0... ever...
	 */
	calc_action_range(strip->act, &strip->actstart, &strip->actend, 1);
	
	strip->start = strip->actstart;
	strip->end = (IS_EQ(strip->actstart, strip->actend)) ?  (strip->actstart + 1.0f): (strip->actend);
	
	/* strip should be referenced as-is */
	strip->scale= 1.0f;
	strip->repeat = 1.0f;
	
	/* return the new strip */
	return strip;
}

/* Add new NLA-strip to the top of the NLA stack - i.e. into the last track if space, or a new one otherwise */
NlaStrip *add_nlastrip_to_stack (AnimData *adt, bAction *act)
{
	NlaStrip *strip;
	NlaTrack *nlt;
	
	/* sanity checks */
	if ELEM(NULL, adt, act)
		return NULL;
	
	/* create a new NLA strip */
	strip= add_nlastrip(act);
	if (strip == NULL)
		return NULL;
	
	/* firstly try adding strip to last track, but if that fails, add to a new track */
	if (BKE_nlatrack_add_strip(adt->nla_tracks.last, strip) == 0) {
		/* trying to add to the last track failed (no track or no space), 
		 * so add a new track to the stack, and add to that...
		 */
		nlt= add_nlatrack(adt, NULL);
		BKE_nlatrack_add_strip(nlt, strip);
	}
	
	/* returns the strip added */
	return strip;
}

/* *************************************************** */
/* NLA Evaluation <-> Editing Stuff */

/* Strip Mapping ------------------------------------- */

/* non clipped mapping for strip-time <-> global time (for Action-Clips)
 *	invert = convert action-strip time to global time 
 */
static float nlastrip_get_frame_actionclip (NlaStrip *strip, float cframe, short mode)
{
	float actlength, repeat, scale;
	
	/* get number of repeats */
	if (IS_EQ(strip->repeat, 0.0f)) strip->repeat = 1.0f;
	repeat = strip->repeat;
	
	/* scaling */
	if (IS_EQ(strip->scale, 0.0f)) strip->scale= 1.0f;
	scale = (float)fabs(strip->scale); /* scale must be positive - we've got a special flag for reversing */
	
	/* length of referenced action */
	actlength = strip->actend - strip->actstart;
	if (IS_EQ(actlength, 0.0f)) actlength = 1.0f;
	
	/* reversed = play strip backwards */
	if (strip->flag & NLASTRIP_FLAG_REVERSE) {
		// FIXME: this won't work right with Graph Editor?
		if (mode == NLATIME_CONVERT_MAP) {
			return strip->end - scale*(cframe - strip->actstart);
		}
		else if (mode == NLATIME_CONVERT_UNMAP) {
			int repeatsNum = (int)((cframe - strip->start) / (actlength * scale));
			
			/* this method doesn't clip the values to lie within the action range only 
			 *	- the '(repeatsNum * actlength * scale)' compensates for the fmod(...)
			 *	- the fmod(...) works in the same way as for eval 
			 */
			return strip->actend - (repeatsNum * actlength * scale) 
					- (fmod(cframe - strip->start, actlength*scale) / scale);
		}
		else {
			if (IS_EQ(cframe, strip->end) && IS_EQ(strip->repeat, ((int)strip->repeat))) {
				/* this case prevents the motion snapping back to the first frame at the end of the strip 
				 * by catching the case where repeats is a whole number, which means that the end of the strip
				 * could also be interpreted as the end of the start of a repeat
				 */
				return strip->actstart;
			}
			else {
				/* - the 'fmod(..., actlength*scale)' is needed to get the repeats working
				 * - the '/ scale' is needed to ensure that scaling influences the timing within the repeat
				 */
				return strip->actend - fmod(cframe - strip->start, actlength*scale) / scale; 
			}
		}
	}
	else {
		if (mode == NLATIME_CONVERT_MAP) {
			return strip->start + scale*(cframe - strip->actstart);
		}
		else if (mode == NLATIME_CONVERT_UNMAP) {
			int repeatsNum = (int)((cframe - strip->start) / (actlength * scale));
			
			/* this method doesn't clip the values to lie within the action range only 
			 *	- the '(repeatsNum * actlength * scale)' compensates for the fmod(...)
			 *	- the fmod(...) works in the same way as for eval 
			 */
			return strip->actstart + (repeatsNum * actlength * scale) 
					+ (fmod(cframe - strip->start, actlength*scale) / scale);
		}
		else /* if (mode == NLATIME_CONVERT_EVAL) */{
			if (IS_EQ(cframe, strip->end) && IS_EQ(strip->repeat, ((int)strip->repeat))) {
				/* this case prevents the motion snapping back to the first frame at the end of the strip 
				 * by catching the case where repeats is a whole number, which means that the end of the strip
				 * could also be interpreted as the end of the start of a repeat
				 */
				return strip->actend;
			}
			else {
				/* - the 'fmod(..., actlength*scale)' is needed to get the repeats working
				 * - the '/ scale' is needed to ensure that scaling influences the timing within the repeat
				 */
				return strip->actstart + fmod(cframe - strip->start, actlength*scale) / scale; 
			}
		}
	}
}

/* non clipped mapping for strip-time <-> global time (for Transitions)
 *	invert = convert action-strip time to global time 
 */
static float nlastrip_get_frame_transition (NlaStrip *strip, float cframe, short mode)
{
	float length;
	
	/* length of strip */
	length= strip->end - strip->start;
	
	/* reversed = play strip backwards */
	if (strip->flag & NLASTRIP_FLAG_REVERSE) {
		if (mode == NLATIME_CONVERT_MAP)
			return strip->end - (length * cframe);
		else
			return (strip->end - cframe) / length;
	}
	else {
		if (mode == NLATIME_CONVERT_MAP)
			return (length * cframe) + strip->start;
		else
			return (cframe - strip->start) / length;
	}
}

/* non clipped mapping for strip-time <-> global time
 * 	mode = eNlaTime_ConvertModes[] -> NLATIME_CONVERT_*
 *
 * only secure for 'internal' (i.e. within AnimSys evaluation) operations,
 * but should not be directly relied on for stuff which interacts with editors
 */
float nlastrip_get_frame (NlaStrip *strip, float cframe, short mode)
{
	switch (strip->type) {
		case NLASTRIP_TYPE_META: /* meta (is just a container for other strips, so shouldn't use the action-clip method) */
		case NLASTRIP_TYPE_TRANSITION: /* transition */
			return nlastrip_get_frame_transition(strip, cframe, mode);
		
		case NLASTRIP_TYPE_CLIP: /* action-clip (default) */
		default:
			return nlastrip_get_frame_actionclip(strip, cframe, mode);
	}	
}


/* Non clipped mapping for strip-time <-> global time
 *	mode = eNlaTime_ConvertModesp[] -> NLATIME_CONVERT_*
 *
 * Public API method - perform this mapping using the given AnimData block
 * and perform any necessary sanity checks on the value
 */
float BKE_nla_tweakedit_remap (AnimData *adt, float cframe, short mode)
{
	NlaStrip *strip;
	
	/* sanity checks 
	 *	- obviously we've got to have some starting data
	 *	- when not in tweakmode, the active Action does not have any scaling applied :)
	 *	- when in tweakmode, if the no-mapping flag is set, do not map
	 */
	if ((adt == NULL) || (adt->flag & ADT_NLA_EDIT_ON)==0 || (adt->flag & ADT_NLA_EDIT_NOMAP))
		return cframe;
		
	/* if the active-strip info has been stored already, access this, otherwise look this up
	 * and store for (very probable) future usage
	 */
	if (adt->actstrip == NULL) {
		NlaTrack *nlt= BKE_nlatrack_find_active(&adt->nla_tracks);
		adt->actstrip= BKE_nlastrip_find_active(nlt);
	}
	strip= adt->actstrip;
	
	/* sanity checks 
	 *	- in rare cases, we may not be able to find this strip for some reason (internal error)
	 *	- for now, if the user has defined a curve to control the time, this correction cannot be performed
	 *	  reliably...
	 */
	if ((strip == NULL) || (strip->flag & NLASTRIP_FLAG_USR_TIME))
		return cframe;
		
	/* perform the correction now... */
	return nlastrip_get_frame(strip, cframe, mode);
}

/* *************************************************** */
/* Basic Utilities */

/* List of Strips ------------------------------------ */
/* (these functions are used for NLA-Tracks and also for nested/meta-strips) */

/* Check if there is any space in the given list to add the given strip */
short BKE_nlastrips_has_space (ListBase *strips, float start, float end)
{
	NlaStrip *strip;
	
	/* sanity checks */
	if ((strips == NULL) || IS_EQ(start, end))
		return 0;
	if (start > end) {
		puts("BKE_nlastrips_has_space() error... start and end arguments swapped");
		SWAP(float, start, end);
	}
	
	/* loop over NLA strips checking for any overlaps with this area... */
	for (strip= strips->first; strip; strip= strip->next) {
		/* if start frame of strip is past the target end-frame, that means that
		 * we've gone past the window we need to check for, so things are fine
		 */
		if (strip->start > end)
			return 1;
		
		/* if the end of the strip is greater than either of the boundaries, the range
		 * must fall within the extents of the strip
		 */
		if ((strip->end > start) || (strip->end > end))
			return 0;
	}
	
	/* if we are still here, we haven't encountered any overlapping strips */
	return 1;
}

/* Rearrange the strips in the track so that they are always in order 
 * (usually only needed after a strip has been moved) 
 */
void BKE_nlastrips_sort_strips (ListBase *strips)
{
	ListBase tmp = {NULL, NULL};
	NlaStrip *strip, *sstrip;
	
	/* sanity checks */
	if ELEM(NULL, strips, strips->first)
		return;
		
	/* we simply perform insertion sort on this list, since it is assumed that per track,
	 * there are only likely to be at most 5-10 strips
	 */
	for (strip= strips->first; strip; strip= strip->next) {
		short not_added = 1;
		
		/* remove this strip from the list, and add it to the new list, searching from the end of 
		 * the list, assuming that the lists are in order 
		 */
		BLI_remlink(strips, strip);
		
		for (sstrip= tmp.last; not_added && sstrip; sstrip= sstrip->prev) {
			/* check if add after */
			if (sstrip->end < strip->start) {
				BLI_insertlinkafter(&tmp, sstrip, strip);
				not_added= 0;
				break;
			}
		}
		
		/* add before first? */
		if (not_added)
			BLI_addhead(&tmp, strip);
	}
	
	/* reassign the start and end points of the strips */
	strips->first= tmp.first;
	strips->last= tmp.last;
}

/* Add the given NLA-Strip to the given list of strips, assuming that it 
 * isn't currently a member of another list
 */
short BKE_nlastrips_add_strip (ListBase *strips, NlaStrip *strip)
{
	NlaStrip *ns;
	short not_added = 1;
	
	/* sanity checks */
	if ELEM(NULL, strips, strip)
		return 0;
		
	/* check if any space to add */
	if (BKE_nlastrips_has_space(strips, strip->start, strip->end)==0)
		return 0;
	
	/* find the right place to add the strip to the nominated track */
	for (ns= strips->first; ns; ns= ns->next) {
		/* if current strip occurs after the new strip, add it before */
		if (ns->start > strip->end) {
			BLI_insertlinkbefore(strips, ns, strip);
			not_added= 0;
			break;
		}
	}
	if (not_added) {
		/* just add to the end of the list of the strips then... */
		BLI_addtail(strips, strip);
	}
	
	/* added... */
	return 1;
}


/* Meta-Strips ------------------------------------ */

/* Convert 'islands' (i.e. continuous string of) selected strips to be
 * contained within 'Meta-Strips' which act as strips which contain strips.
 *	temp: are the meta-strips to be created 'temporary' ones used for transforms?
 */
void BKE_nlastrips_make_metas (ListBase *strips, short temp)
{
	NlaStrip *mstrip = NULL;
	NlaStrip *strip, *stripn;
	
	/* sanity checks */
	if ELEM(NULL, strips, strips->first)
		return;
	
	/* group all continuous chains of selected strips into meta-strips */
	for (strip= strips->first; strip; strip= stripn) {
		stripn= strip->next;
		
		if (strip->flag & NLASTRIP_FLAG_SELECT) {
			/* if there is an existing meta-strip, add this strip to it, otherwise, create a new one */
			if (mstrip == NULL) {
				/* add a new meta-strip, and add it before the current strip that it will replace... */
				mstrip= MEM_callocN(sizeof(NlaStrip), "Meta-NlaStrip");
				mstrip->type = NLASTRIP_TYPE_META;
				BLI_insertlinkbefore(strips, strip, mstrip);
				
				/* set flags */
				mstrip->flag = NLASTRIP_FLAG_SELECT;
				
				/* set temp flag if appropriate (i.e. for transform-type editing) */
				if (temp)
					mstrip->flag |= NLASTRIP_FLAG_TEMP_META;
				
				/* make its start frame be set to the start frame of the current strip */
				mstrip->start= strip->start;
			}
			
			/* remove the selected strips from the track, and add to the meta */
			BLI_remlink(strips, strip);
			BLI_addtail(&mstrip->strips, strip);
			
			/* expand the meta's dimensions to include the newly added strip- i.e. its last frame */
			mstrip->end= strip->end;
		}
		else {
			/* current strip wasn't selected, so the end of 'island' of selected strips has been reached,
			 * so stop adding strips to the current meta
			 */
			mstrip= NULL;
		}
	}
}

/* Remove meta-strips (i.e. flatten the list of strips) from the top-level of the list of strips
 *	sel: only consider selected meta-strips, otherwise all meta-strips are removed
 *	onlyTemp: only remove the 'temporary' meta-strips used for transforms
 */
void BKE_nlastrips_clear_metas (ListBase *strips, short onlySel, short onlyTemp)
{
	NlaStrip *strip, *stripn;
	
	/* sanity checks */
	if ELEM(NULL, strips, strips->first)
		return;
	
	/* remove meta-strips fitting the criteria of the arguments */
	for (strip= strips->first; strip; strip= stripn) {
		stripn= strip->next;
		
		/* check if strip is a meta-strip */
		if (strip->type == NLASTRIP_TYPE_META) {
			/* if check if selection and 'temporary-only' considerations are met */
			if ((onlySel==0) || (strip->flag & NLASTRIP_FLAG_SELECT)) {
				if ((!onlyTemp) || (strip->flag & NLASTRIP_FLAG_TEMP_META)) {
					NlaStrip *cs, *csn;
					
					/* move each one of the meta-strip's children before the meta-strip
					 * in the list of strips after unlinking them from the meta-strip
					 */
					for (cs= strip->strips.first; cs; cs= csn) {
						csn= cs->next;
						BLI_remlink(&strip->strips, cs);
						BLI_insertlinkbefore(strips, strip, cs);
					}
					
					/* free the meta-strip now */
					BLI_freelinkN(strips, strip);
				}
			}
		}
	}
}

/* Add the given NLA-Strip to the given Meta-Strip, assuming that the
 * strip isn't attached to anyy list of strips 
 */
short BKE_nlameta_add_strip (NlaStrip *mstrip, NlaStrip *strip)
{
	/* sanity checks */
	if ELEM(NULL, mstrip, strip)
		return 0;
		
	/* firstly, check if the meta-strip has space for this */
	if (BKE_nlastrips_has_space(&mstrip->strips, strip->start, strip->end) == 0)
		return 0;
		
	/* check if this would need to be added to the ends of the meta,
	 * and subsequently, if the neighbouring strips allow us enough room
	 */
	if (strip->start < mstrip->start) {
		/* check if strip to the left (if it exists) ends before the 
		 * start of the strip we're trying to add 
		 */
		if ((mstrip->prev == NULL) || (mstrip->prev->end <= strip->start)) {
			/* add strip to start of meta's list, and expand dimensions */
			BLI_addhead(&mstrip->strips, strip);
			mstrip->start= strip->start;
			
			return 1;
		}
		else /* failed... no room before */
			return 0;
	}
	else if (strip->end > mstrip->end) {
		/* check if strip to the right (if it exists) starts before the 
		 * end of the strip we're trying to add 
		 */
		if ((mstrip->next == NULL) || (mstrip->next->start >= strip->end)) {
			/* add strip to end of meta's list, and expand dimensions */
			BLI_addtail(&mstrip->strips, strip);
			mstrip->end= strip->end;
			
			return 1;
		}
		else /* failed... no room after */
			return 0;
	}
	else {
		/* just try to add to the meta-strip (no dimension changes needed) */
		return BKE_nlastrips_add_strip(&mstrip->strips, strip);
	}
}

/* Adjust the settings of NLA-Strips contained within a Meta-Strip (recursively), 
 * until the Meta-Strips children all fit within the Meta-Strip's new dimensions
 */
void BKE_nlameta_flush_transforms (NlaStrip *mstrip) 
{
	NlaStrip *strip;
	float oStart, oEnd, offset;
	
	/* sanity checks 
	 *	- strip must exist
	 *	- strip must be a meta-strip with some contents
	 */
	if ELEM(NULL, mstrip, mstrip->strips.first)
		return;
	if (mstrip->type != NLASTRIP_TYPE_META)
		return;
		
	/* get the original start/end points, and calculate the start-frame offset
	 *	- these are simply the start/end frames of the child strips, 
	 *	  since we assume they weren't transformed yet
	 */
	oStart= ((NlaStrip *)mstrip->strips.first)->start;
	oEnd= ((NlaStrip *)mstrip->strips.last)->end;
	offset= mstrip->start - oStart;
	
	/* optimisation:
	 * don't flush if nothing changed yet
	 *	TODO: maybe we need a flag to say always flush?
	 */
	if (IS_EQ(oStart, mstrip->start) && IS_EQ(oEnd, mstrip->end))
		return;
	
	/* for each child-strip, calculate new start/end points based on this new info */
	for (strip= mstrip->strips.first; strip; strip= strip->next) {
		//PointerRNA strip_ptr;
		
		/* firstly, just apply the changes in offset to both ends of the strip */
		strip->start += offset;
		strip->end += offset;
		
		/* now, we need to fix the endpoint to take into account scaling */
		// TODO..
		
		/* finally, make sure the strip's children (if it is a meta-itself), get updated */
		BKE_nlameta_flush_transforms(strip);
	}
}

/* NLA-Tracks ---------------------------------------- */

/* Find the active NLA-track for the given stack */
NlaTrack *BKE_nlatrack_find_active (ListBase *tracks)
{
	NlaTrack *nlt;
	
	/* sanity check */
	if ELEM(NULL, tracks, tracks->first)
		return NULL;
		
	/* try to find the first active track */
	for (nlt= tracks->first; nlt; nlt= nlt->next) {
		if (nlt->flag & NLATRACK_ACTIVE)
			return nlt;
	}
	
	/* none found */
	return NULL;
}

/* Toggle the 'solo' setting for the given NLA-track, making sure that it is the only one
 * that has this status in its AnimData block.
 */
void BKE_nlatrack_solo_toggle (AnimData *adt, NlaTrack *nlt)
{
	NlaTrack *nt;
	
	/* sanity check */
	if ELEM(NULL, adt, adt->nla_tracks.first)
		return;
		
	/* firstly, make sure 'solo' flag for all tracks is disabled */
	for (nt= adt->nla_tracks.first; nt; nt= nt->next) {
		if (nt != nlt)
			nt->flag &= ~NLATRACK_SOLO;
	}
		
	/* now, enable 'solo' for the given track if appropriate */
	if (nlt) {
		/* toggle solo status */
		nlt->flag ^= NLATRACK_SOLO;
		
		/* set or clear solo-status on AnimData */
		if (nlt->flag & NLATRACK_SOLO)
			adt->flag |= ADT_NLA_SOLO_TRACK;
		else
			adt->flag &= ~ADT_NLA_SOLO_TRACK;
	}
	else
		adt->flag &= ~ADT_NLA_SOLO_TRACK;
}

/* Make the given NLA-track the active one for the given stack. If no track is provided, 
 * this function can be used to simply deactivate all the NLA tracks in the given stack too.
 */
void BKE_nlatrack_set_active (ListBase *tracks, NlaTrack *nlt_a)
{
	NlaTrack *nlt;
	
	/* sanity check */
	if ELEM(NULL, tracks, tracks->first)
		return;
	
	/* deactive all the rest */
	for (nlt= tracks->first; nlt; nlt= nlt->next) 
		nlt->flag &= ~NLATRACK_ACTIVE;
		
	/* set the given one as the active one */
	if (nlt_a)
		nlt_a->flag |= NLATRACK_ACTIVE;
}


/* Check if there is any space in the given track to add a strip of the given length */
short BKE_nlatrack_has_space (NlaTrack *nlt, float start, float end)
{
	/* sanity checks */
	if ((nlt == NULL) || IS_EQ(start, end))
		return 0;
	if (start > end) {
		puts("BKE_nlatrack_has_space() error... start and end arguments swapped");
		SWAP(float, start, end);
	}
	
	/* check if there's any space left in the track for a strip of the given length */
	return BKE_nlastrips_has_space(&nlt->strips, start, end);
}

/* Rearrange the strips in the track so that they are always in order 
 * (usually only needed after a strip has been moved) 
 */
void BKE_nlatrack_sort_strips (NlaTrack *nlt)
{
	/* sanity checks */
	if ELEM(NULL, nlt, nlt->strips.first)
		return;
	
	/* sort the strips with a more generic function */
	BKE_nlastrips_sort_strips(&nlt->strips);
}

/* Add the given NLA-Strip to the given NLA-Track, assuming that it 
 * isn't currently attached to another one 
 */
short BKE_nlatrack_add_strip (NlaTrack *nlt, NlaStrip *strip)
{
	/* sanity checks */
	if ELEM(NULL, nlt, strip)
		return 0;
		
	/* try to add the strip to the track using a more generic function */
	return BKE_nlastrips_add_strip(&nlt->strips, strip);
}

/* NLA Strips -------------------------------------- */

/* Find the active NLA-strip within the given track */
NlaStrip *BKE_nlastrip_find_active (NlaTrack *nlt)
{
	NlaStrip *strip;
	
	/* sanity check */
	if ELEM(NULL, nlt, nlt->strips.first)
		return NULL;
		
	/* try to find the first active strip */
	for (strip= nlt->strips.first; strip; strip= strip->next) {
		if (strip->flag & NLASTRIP_FLAG_ACTIVE)
			return strip;
	}
	
	/* none found */
	return NULL;
}

/* Does the given NLA-strip fall within the given bounds (times)? */
short BKE_nlastrip_within_bounds (NlaStrip *strip, float min, float max)
{
	const float stripLen= (strip) ? strip->end - strip->start : 0.0f;
	const float boundsLen= (float)fabs(max - min);
	
	/* sanity checks */
	if ((strip == NULL) || IS_EQ(stripLen, 0.0f) || IS_EQ(boundsLen, 0.0f))
		return 0;
	
	/* only ok if at least part of the strip is within the bounding window
	 *	- first 2 cases cover when the strip length is less than the bounding area
	 *	- second 2 cases cover when the strip length is greater than the bounding area
	 */
	if ( (stripLen < boundsLen) && 
		 !(IN_RANGE(strip->start, min, max) ||
		   IN_RANGE(strip->end, min, max)) )
	{
		return 0;
	}
	if ( (stripLen > boundsLen) && 
		 !(IN_RANGE(min, strip->start, strip->end) ||
		   IN_RANGE(max, strip->start, strip->end)) )
	{
		return 0;
	}
	
	/* should be ok! */
	return 1;
}

/* Is the given NLA-strip the first one to occur for the given AnimData block */
// TODO: make this an api method if necesary, but need to add prefix first
short nlastrip_is_first (AnimData *adt, NlaStrip *strip)
{
	NlaTrack *nlt;
	NlaStrip *ns;
	
	/* sanity checks */
	if ELEM(NULL, adt, strip)
		return 0;
		
	/* check if strip has any strips before it */
	if (strip->prev)
		return 0;
		
	/* check other tracks to see if they have a strip that's earlier */
	// TODO: or should we check that the strip's track is also the first?
	for (nlt= adt->nla_tracks.first; nlt; nlt= nlt->next) {
		/* only check the first strip, assuming that they're all in order */
		ns= nlt->strips.first;
		if (ns) {
			if (ns->start < strip->start)
				return 0;
		}
	}	
	
	/* should be first now */
	return 1;
}
 
/* Tools ------------------------------------------- */

/* For the given AnimData block, add the active action to the NLA
 * stack (i.e. 'push-down' action). The UI should only allow this 
 * for normal editing only (i.e. not in editmode for some strip's action),
 * so no checks for this are performed.
 */
// TODO: maybe we should have checks for this too...
void BKE_nla_action_pushdown (AnimData *adt)
{
	NlaStrip *strip;
	
	/* sanity checks */
	// TODO: need to report the error for this
	if ELEM(NULL, adt, adt->action) 
		return;
		
	/* if the action is empty, we also shouldn't try to add to stack, 
	 * as that will cause us grief down the track
	 */
	// TODO: what about modifiers?
	if (action_has_motion(adt->action) == 0) {
		printf("BKE_nla_action_pushdown(): action has no data \n");
		return;
	}
	
	/* add a new NLA strip to the track, which references the active action */
	strip= add_nlastrip_to_stack(adt, adt->action);
	
	/* do other necessary work on strip */	
	if (strip) {
		/* clear reference to action now that we've pushed it onto the stack */
		adt->action->id.us--;
		adt->action= NULL;
		
		/* if the strip is the first one in the track it lives in, check if there
		 * are strips in any other tracks that may be before this, and set the extend
		 * mode accordingly
		 */
		if (nlastrip_is_first(adt, strip) == 0) {
			/* not first, so extend mode can only be NLASTRIP_EXTEND_HOLD_FORWARD not NLASTRIP_EXTEND_HOLD,
			 * so that it doesn't override strips in previous tracks
			 */
			// FIXME: this needs to be more automated, since user can rearrange strips
			strip->extendmode= NLASTRIP_EXTEND_HOLD_FORWARD;
		}
	}
}


/* Find the active strip + track combo, and set them up as the tweaking track,
 * and return if successful or not.
 */
short BKE_nla_tweakmode_enter (AnimData *adt)
{
	NlaTrack *nlt, *activeTrack=NULL;
	NlaStrip *strip, *activeStrip=NULL;
	
	/* verify that data is valid */
	if ELEM(NULL, adt, adt->nla_tracks.first)
		return 0;
		
	/* if block is already in tweakmode, just leave, but we should report 
	 * that this block is in tweakmode (as our returncode)
	 */
	if (adt->flag & ADT_NLA_EDIT_ON)
		return 1;
		
	/* go over the tracks, finding the active one, and its active strip
	 * 	- if we cannot find both, then there's nothing to do
	 */
	for (nlt= adt->nla_tracks.first; nlt; nlt= nlt->next) {
		/* check if active */
		if (nlt->flag & NLATRACK_ACTIVE) {
			/* store reference to this active track */
			activeTrack= nlt;
			
			/* now try to find active strip */
			activeStrip= BKE_nlastrip_find_active(nlt);
			break;
		}	
	}
	if ELEM3(NULL, activeTrack, activeStrip, activeStrip->act) {
		printf("NLA tweakmode enter - neither active requirement found \n");
		return 0;
	}
		
	/* go over all the tracks up to the active one, tagging each strip that uses the same 
	 * action as the active strip, but leaving everything else alone
	 */
	for (nlt= activeTrack->prev; nlt; nlt= nlt->prev) {
		for (strip= nlt->strips.first; strip; strip= strip->next) {
			if (strip->act == activeStrip->act)
				strip->flag |= NLASTRIP_FLAG_TWEAKUSER;
			else
				strip->flag &= ~NLASTRIP_FLAG_TWEAKUSER;
		}
	}
	
	
	/* go over all the tracks after AND INCLUDING the active one, tagging them as being disabled 
	 *	- the active track needs to also be tagged, otherwise, it'll overlap with the tweaks going on
	 */
	for (nlt= activeTrack; nlt; nlt= nlt->next)
		nlt->flag |= NLATRACK_DISABLED;
	
	/* handle AnimData level changes:
	 *	- 'real' active action to temp storage (no need to change user-counts)
	 *	- action of active strip set to be the 'active action', and have its usercount incremented
	 *	- editing-flag for this AnimData block should also get turned on (for more efficient restoring)
	 *	- take note of the active strip for mapping-correction of keyframes in the action being edited
	 */
	adt->tmpact= adt->action;
	adt->action= activeStrip->act;
	adt->actstrip= activeStrip;
	id_us_plus(&activeStrip->act->id);
	adt->flag |= ADT_NLA_EDIT_ON;
	
	/* done! */
	return 1;
}

/* Exit tweakmode for this AnimData block */
void BKE_nla_tweakmode_exit (AnimData *adt)
{
	NlaStrip *strip;
	NlaTrack *nlt;
	
	/* verify that data is valid */
	if ELEM(NULL, adt, adt->nla_tracks.first)
		return;
		
	/* hopefully the flag is correct - skip if not on */
	if ((adt->flag & ADT_NLA_EDIT_ON) == 0)
		return;
		
	// TODO: need to sync the user-strip with the new state of the action!
		
	/* for all Tracks, clear the 'disabled' flag
	 * for all Strips, clear the 'tweak-user' flag
	 */
	for (nlt= adt->nla_tracks.first; nlt; nlt= nlt->next) {
		nlt->flag &= ~NLATRACK_DISABLED;
		
		for (strip= nlt->strips.first; strip; strip= strip->next) 
			strip->flag &= ~NLASTRIP_FLAG_TWEAKUSER;
	}
	
	/* handle AnimData level changes:
	 *	- 'temporary' active action needs its usercount decreased, since we're removing this reference
	 *	- 'real' active action is restored from storage
	 *	- storage pointer gets cleared (to avoid having bad notes hanging around)
	 *	- editing-flag for this AnimData block should also get turned off
	 *	- clear pointer to active strip
	 */
	if (adt->action) adt->action->id.us--;
	adt->action= adt->tmpact;
	adt->tmpact= NULL;
	adt->actstrip= NULL;
	adt->flag &= ~ADT_NLA_EDIT_ON;
}

/* *************************************************** */

/**
 * $Id: BKE_nla.h 20999 2009-06-19 04:45:56Z aligorith $
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

#ifndef NLA_PRIVATE
#define NLA_PRIVATE

/* --------------- NLA Evaluation DataTypes ----------------------- */

/* used for list of strips to accumulate at current time */
typedef struct NlaEvalStrip {
	struct NlaEvalStrip *next, *prev;
	
	NlaTrack *track;			/* track that this strip belongs to */
	NlaStrip *strip;			/* strip that's being used */
	
	short track_index;			/* the index of the track within the list */
	short strip_mode;			/* which end of the strip are we looking at */
	
	float strip_time;			/* time at which which strip is being evaluated */
} NlaEvalStrip;

/* NlaEvalStrip->strip_mode */
enum {
		/* standard evaluation */
	NES_TIME_BEFORE = -1,
	NES_TIME_WITHIN,
	NES_TIME_AFTER,
	
		/* transition-strip evaluations */
	NES_TIME_TRANSITION_START,
	NES_TIME_TRANSITION_END,
} eNlaEvalStrip_StripMode;


/* temp channel for accumulating data from NLA (avoids needing to clear all values first) */
// TODO: maybe this will be used as the 'cache' stuff needed for editable values too?
typedef struct NlaEvalChannel {
	struct NlaEvalChannel *next, *prev;
	
	PointerRNA ptr;			/* pointer to struct containing property to use */
	PropertyRNA *prop;		/* RNA-property type to use (should be in the struct given) */
	int index;				/* array index (where applicable) */
	
	float value;			/* value of this channel */
} NlaEvalChannel;

/* --------------- NLA Functions (not to be used as a proper API) ----------------------- */

/* convert from strip time <-> global time */
float nlastrip_get_frame(NlaStrip *strip, float cframe, short invert);

#endif // NLA_PRIVATE

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
 * Contributor(s): Blender Foundation
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#include <stdlib.h>
#include <math.h>

#include "MEM_guardedalloc.h"

#include "DNA_scene_types.h"

#include "BLI_blenlib.h"

#include "BKE_global.h"


/* ********* general editor util funcs, not BKE stuff please! ********* */
/* ***** XXX: functions are using old blender names, cleanup later ***** */


/* now only used in 2d spaces, like time, ipo, nla, sima... */
/* XXX clean G.qual */
void apply_keyb_grid(float *val, float fac1, float fac2, float fac3, int invert)
{
	/* fac1 is for 'nothing', fac2 for CTRL, fac3 for SHIFT */
	int ctrl;
	
	if(invert) {
		if(G.qual & LR_CTRLKEY) ctrl= 0;
		else ctrl= 1;
	}
	else ctrl= (G.qual & LR_CTRLKEY);
	
	if(ctrl && (G.qual & LR_SHIFTKEY)) {
		if(fac3!= 0.0) *val= fac3*floor(*val/fac3 +.5);
	}
	else if(ctrl) {
		if(fac2!= 0.0) *val= fac2*floor(*val/fac2 +.5);
	}
	else {
		if(fac1!= 0.0) *val= fac1*floor(*val/fac1 +.5);
	}
}


/**
 * $Id$
 *
 * ***** BEGIN GPL/BL DUAL LICENSE BLOCK *****
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version. The Blender
 * Foundation also sells licenses for use in proprietary software under
 * the Blender License.  See http://www.blender.org/BL/ for information
 * about this.
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
 * Contributor(s): none yet.
 *
 * ***** END GPL/BL DUAL LICENSE BLOCK *****
 */

#include <stdlib.h>
#include <string.h>
#include <math.h>

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

#ifndef WIN32
#include <unistd.h>
#else
#include <io.h>
#endif

#include "MEM_guardedalloc.h"

#include "BKE_global.h" /* for G */

#include "blendef.h"

#include "mydevice.h"

#include "BLI_arithb.h"

#include "transform.h"

/* ************************** Functions *************************** */

/* ************************** NUMINPUT **************************** */

void outputNumInput(NumInput *n, char *str)
{
	char cur;
	short i, j;

	for (j=0; j<=n->idx_max; j++) {
		/* if AFFECTALL and no number typed and cursor not on number, use first number */
		if (n->flag & NUM_AFFECT_ALL && n->idx != j && n->ctrl[j] == 0)
			i = 0;
		else
			i = j;

		if (n->idx != i)
			cur = ' ';
		else
			cur = '|';

		switch (n->ctrl[i]) {
		case 0:
			sprintf(&str[j*20], "NONE%c", cur);
			break;
		case 1:
		case -1:
			sprintf(&str[j*20], "%.0f%c", n->val[i], cur);
			break;
		case 10:
		case -10:
			sprintf(&str[j*20], "%.f.%c", n->val[i], cur);
			break;
		case 100:
		case -100:
			sprintf(&str[j*20], "%.1f%c", n->val[i], cur);
			break;
		case 1000:
		case -1000:
			sprintf(&str[j*20], "%.2f%c", n->val[i], cur);
		case 10000:
		case -10000:
			sprintf(&str[j*20], "%.3f%c", n->val[i], cur);
			break;
		default:
			sprintf(&str[j*20], "%.4f%c", n->val[i], cur);
		}
	}
}

short hasNumInput(NumInput *n)
{
	short i;

	for (i=0; i<=n->idx_max; i++) {
		if (n->ctrl[i])
			return 1;
	}

	return 0;
}

void applyNumInput(NumInput *n, float *vec)
{
	short i, j;

	if (hasNumInput(n)) {
		for (j=0; j<=n->idx_max; j++) {
			/* if AFFECTALL and no number typed and cursor not on number, use first number */
			if (n->flag & NUM_AFFECT_ALL && n->idx != j && n->ctrl[j] == 0)
				i = 0;
			else
				i = j;

			if (n->ctrl[i] == 0 && n->flag & NUM_NULL_ONE) {
				vec[j] = 1.0f;
			}
			else if (n->val[i] == 0.0f && n->flag & NUM_NO_ZERO) {
				vec[j] = 0.0001f;
			}
			else {
				vec[j] = n->val[i];
			}
		}
	}
}

char handleNumInput(NumInput *n, unsigned short event)
{
	float Val = 0;
	short idx = n->idx, idx_max = n->idx_max;

	switch (event) {
	case BACKSPACEKEY:
		if (n->ctrl[idx] == 0) {
			n->val[0]		= 
				n->val[1]	= 
				n->val[2]	= 0.0f;
			n->ctrl[0]		= 
				n->ctrl[1]	= 
				n->ctrl[2]	= 0;
		}
		else {
			n->val[idx] = 0.0f;
			n->ctrl[idx] = 0;
		}
		break;
	case PERIODKEY:
	case PADPERIOD:
		if (n->flag & NUM_NO_FRACTION)
			break;

		switch (n->ctrl[idx])
		{
		case 0:
		case 1:
			n->ctrl[idx] = 10;
			break;
		case -1:
			n->ctrl[idx] = -10;
		}
		break;
	case PADMINUS:
		if(G.qual & LR_ALTKEY)
			break;
	case MINUSKEY:
		if (n->flag & NUM_NO_NEGATIVE)
			break;

		if (n->ctrl[idx]) {
			n->ctrl[idx] *= -1;
			n->val[idx] *= -1;
		}
		else
			n->ctrl[idx] = -1;
		break;
	case TABKEY:
		idx++;
		if (idx > idx_max)
			idx = 0;
		n->idx = idx;
		break;
	case PAD9:
	case NINEKEY:
		Val += 1.0f;
	case PAD8:
	case EIGHTKEY:
		Val += 1.0f;
	case PAD7:
	case SEVENKEY:
		Val += 1.0f;
	case PAD6:
	case SIXKEY:
		Val += 1.0f;
	case PAD5:
	case FIVEKEY:
		Val += 1.0f;
	case PAD4:
	case FOURKEY:
		Val += 1.0f;
	case PAD3:
	case THREEKEY:
		Val += 1.0f;
	case PAD2:
	case TWOKEY:
		Val += 1.0f;
	case PAD1:
	case ONEKEY:
		Val += 1.0f;
	case PAD0:
	case ZEROKEY:
		if (!n->ctrl[idx])
			n->ctrl[idx] = 1;

		if (n->ctrl[idx] == 1) {
			n->val[idx] *= 10;
			n->val[idx] += Val;
		}
		else if (n->ctrl[idx] == -1) {
			n->val[idx] *= 10;
			n->val[idx] -= Val;
		}
		else {
			n->val[idx] += Val / (float)n->ctrl[idx];
			n->ctrl[idx] *= 10;
		}
		break;
	default:
		return 0;
	}
	/* REDRAW SINCE NUMBERS HAVE CHANGED */
	return 1;
}

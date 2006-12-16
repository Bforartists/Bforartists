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

#ifndef BDR_DRAWACTION_H
#define BDR_DRAWACTION_H

struct BezTriple;
struct Ipo;
struct IpoCurve;
struct gla2DDrawInfo;
struct bAction;
struct Object;
struct ListBase;

/* 'Long Keyframe' Struct */
typedef struct ActKeyBlock {
	struct ActKeyBlock *next, *prev;
	short sel, handle_type;
	float val;
	float start, end;
	
	/* only while drawing - used to determine if block needs to be drawn */
	short modified;
	short totcurve; 
} ActKeyBlock;

/*Action Generics */
void draw_cfra_action(void);
int count_action_levels (struct bAction *act);

/* Channel Drawing */
void draw_icu_channel(struct gla2DDrawInfo *di, IpoCurve *icu, float ypos);
void draw_ipo_channel(struct gla2DDrawInfo *di, Ipo *ipo, float ypos);
void draw_action_channel(struct gla2DDrawInfo *di, bAction *act, float ypos);
void draw_object_channel(struct gla2DDrawInfo *di, Object *ob, float ypos);

/* Keydata Generation */
void icu_to_keylist(struct IpoCurve *icu, ListBase *keys, ListBase *blocks);
int ipo_to_keylist(struct Ipo *ipo, ListBase *keys, ListBase *blocks);
int action_to_keylist(bAction *act, ListBase *keys, ListBase *blocks);
int ob_to_keylist(Object *ob, ListBase *keys, ListBase *blocks);

#endif  /*  BDR_DRAWACTION_H */


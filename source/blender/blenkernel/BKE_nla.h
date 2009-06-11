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

#ifndef BKE_NLA_H
#define BKE_NLA_H

struct AnimData;
struct NlaStrip;
struct NlaTrack;
struct bAction;

/* ----------------------------- */
/* Data Management */

void free_nlastrip(ListBase *strips, struct NlaStrip *strip);
void free_nlatrack(ListBase *tracks, struct NlaTrack *nlt);
void free_nladata(ListBase *tracks);

struct NlaStrip *copy_nlastrip(struct NlaStrip *strip);
struct NlaTrack *copy_nlatrack(struct NlaTrack *nlt);
void copy_nladata(ListBase *dst, ListBase *src);

struct NlaTrack *add_nlatrack(struct AnimData *adt, struct NlaTrack *prev);
struct NlaStrip *add_nlastrip(struct bAction *act);
struct NlaStrip *add_nlastrip_to_stack(struct AnimData *adt, struct bAction *act);

/* ----------------------------- */
/* API */

struct NlaTrack *BKE_nlatrack_find_active(ListBase *tracks);
void BKE_nlatrack_set_active(ListBase *tracks, struct NlaTrack *nlt);

void BKE_nlatrack_solo_toggle(struct AnimData *adt, struct NlaTrack *nlt);

short BKE_nlatrack_has_space(struct NlaTrack *nlt, float start, float end);
void BKE_nlatrack_sort_strips(struct NlaTrack *nlt);


struct NlaStrip *BKE_nlastrip_find_active(struct NlaTrack *nlt);
short BKE_nlastrip_within_bounds(struct NlaStrip *strip, float min, float max);


void BKE_nla_action_pushdown(struct AnimData *adt);

short BKE_nla_tweakmode_enter(struct AnimData *adt);
void BKE_nla_tweakmode_exit(struct AnimData *adt);

#endif


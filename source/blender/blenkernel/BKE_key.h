/**
 * blenlib/BKE_key.h (mar-2001 nzc)
 *	
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
#ifndef BKE_KEY_H
#define BKE_KEY_H

struct Key;
struct KeyBlock;
struct ID;
struct ListBase;
struct Curve;
struct Object;
struct Lattice;
struct Mesh;

void free_key(struct Key *sc); 
struct Key *add_key(struct ID *id);
struct Key *copy_key(struct Key *key);
void make_local_key(struct Key *key);
void sort_keys(struct Key *key);

void set_four_ipo(float d, float *data, int type);
void set_afgeleide_four_ipo(float d, float *data, int type);

/* only exported to curve.c! */
void cp_cu_key(struct Curve *cu, struct KeyBlock *kb, int start, int end);

int do_ob_key(struct Object *ob);

struct Key *ob_get_key(struct Object *ob);
struct KeyBlock *ob_get_keyblock(struct Object *ob);
struct KeyBlock *key_get_keyblock(struct Key *key, int index);

#endif


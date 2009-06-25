/**
 * $Id$
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
 * The Original Code is Copyright (C) 2001-2002 by NaN Holding BV.
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Original author: Benoit Bolsee
 * Contributor(s): 
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#ifndef BIK_API_H
#define BIK_API_H

#ifdef __cplusplus
extern "C" {
#endif

struct Object;
struct bPoseChannel;
struct bArmature;

void BIK_initialize_tree(struct Object *ob, float ctime);
void BIK_execute_tree(struct Object *ob, struct bPoseChannel *pchan, float ctime);
void BIK_release_tree(struct Object *ob, float ctime);
void BIK_remove_armature(struct bArmature *arm);
void BIK_clear_cache(struct bArmature *arm);

// number of solver available
// 0 = iksolver
// 1 = iTaSC
#define BIK_SOLVER_COUNT		2

#ifdef __cplusplus
}
#endif

#endif // BIK_API_H


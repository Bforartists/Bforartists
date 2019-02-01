/*
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
 * The Original Code is Copyright (C) 2008 Blender Foundation.
 * All rights reserved.
 */

/** \file ED_lattice.h
 *  \ingroup editors
 */

#ifndef __ED_LATTICE_H__
#define __ED_LATTICE_H__

struct Object;
struct UndoType;
struct wmKeyConfig;

/* lattice_ops.c */
void ED_operatortypes_lattice(void);
void ED_keymap_lattice(struct wmKeyConfig *keyconf);

/* editlattice_select.c */
void ED_lattice_flags_set(struct Object *obedit, int flag);
bool ED_lattice_select_pick(struct bContext *C, const int mval[2], bool extend, bool deselect, bool toggle);

/* editlattice_undo.c */
void ED_lattice_undosys_type(struct UndoType *ut);

#endif  /* __ED_LATTICE_H__ */

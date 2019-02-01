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

/** \file ED_util.h
 *  \ingroup editors
 */

#ifndef __ED_UTIL_H__
#define __ED_UTIL_H__

struct PackedFile;
struct ScrArea;
struct SpaceLink;
struct bContext;
struct wmOperatorType;

/* ed_util.c */

void    ED_editors_init(struct bContext *C);
void    ED_editors_exit(struct bContext *C);

bool    ED_editors_flush_edits(const struct bContext *C, bool for_render);

void    ED_spacedata_id_remap(struct ScrArea *sa, struct SpaceLink *sl, struct ID *old_id, struct ID *new_id);

void    ED_OT_flush_edits(struct wmOperatorType *ot);

/* ************** XXX OLD CRUFT WARNING ************* */

void apply_keyb_grid(int shift, int ctrl, float *val, float fac1, float fac2, float fac3, int invert);

/* where else to go ? */
void unpack_menu(struct bContext *C, const char *opname, const char *id_name, const char *abs_name, const char *folder, struct PackedFile *pf);

#endif /* __ED_UTIL_H__ */

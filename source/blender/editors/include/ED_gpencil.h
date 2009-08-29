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
 * The Original Code is Copyright (C) 2008, Blender Foundation
 * This is a new part of Blender
 *
 * Contributor(s): Joshua Leung
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#ifndef ED_GPENCIL_H
#define ED_GPENCIL_H

struct ListBase;
struct bScreen;
struct ScrArea;
struct ARegion;
struct View3D;
struct SpaceNode;
struct SpaceSeq;
struct bGPdata;
struct bGPDlayer;
struct bGPDframe;
struct PointerRNA;
struct Panel;
struct ImBuf;
struct wmWindowManager;


/* ------------- Grease-Pencil Helpers ---------------- */

/* Temporary 'Stroke Point' data 
 *
 * Used as part of the 'stroke cache' used during drawing of new strokes
 */
typedef struct tGPspoint {
	short x, y;				/* x and y coordinates of cursor (in relative to area) */
	float pressure;			/* pressure of tablet at this point */
} tGPspoint;

/* ----------- Grease Pencil Tools/Context ------------- */

struct bGPdata **gpencil_data_get_pointers(struct bContext *C, struct PointerRNA *ptr);
struct bGPdata *gpencil_data_get_active(struct bContext *C);

/* ----------- Grease Pencil Operators ----------------- */

void gpencil_common_keymap(struct wmWindowManager *wm, ListBase *keymap);

void ED_operatortypes_gpencil(void);

/* ------------ Grease-Pencil Drawing API ------------------ */
/* drawgpencil.c */

void draw_gpencil_2dimage(struct bContext *C, struct ImBuf *ibuf);
void draw_gpencil_2dview(struct bContext *C, short onlyv2d);
void draw_gpencil_3dview(struct bContext *C, short only3d);
void draw_gpencil_oglrender(struct bContext *C);

void gpencil_panel_standard(const struct bContext *C, struct Panel *pa);


#endif /*  ED_GPENCIL_H */

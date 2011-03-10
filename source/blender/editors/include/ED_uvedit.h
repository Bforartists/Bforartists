/*
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
 * Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
 *
 * The Original Code is Copyright (C) 2008 Blender Foundation.
 * All rights reserved.
 * 
 * Contributor(s): Blender Foundation
 *
 * ***** END GPL LICENSE BLOCK *****
 */

/** \file ED_uvedit.h
 *  \ingroup editors
 */

#ifndef ED_UVEDIT_H
#define ED_UVEDIT_H

struct bContext;
struct Scene;
struct Object;
struct MTFace;
struct EditFace;
struct Image;
struct wmKeyConfig;

/* uvedit_ops.c */
void ED_operatortypes_uvedit(void);
void ED_keymap_uvedit(struct wmKeyConfig *keyconf);

void ED_uvedit_assign_image(struct Scene *scene, struct Object *obedit, struct Image *ima, struct Image *previma);
int ED_uvedit_minmax(struct Scene *scene, struct Image *ima, struct Object *obedit, float *min, float *max);

int ED_uvedit_test_silent(struct Object *obedit);
int ED_uvedit_test(struct Object *obedit);

/* visibility and selection */
int uvedit_edge_selected(struct Scene *scene, struct EditFace *efa, struct MTFace *tf, int i);
int uvedit_face_selected(struct Scene *scene, struct EditFace *efa, struct MTFace *tf);
int uvedit_face_visible_nolocal(struct Scene *scene, struct EditFace *efa);
int uvedit_face_visible(struct Scene *scene, struct Image *ima, struct EditFace *efa, struct MTFace *tf);
int uvedit_uv_selected(struct Scene *scene, struct EditFace *efa, struct MTFace *tf, int i);
void uvedit_edge_deselect(struct Scene *scene, struct EditFace *efa, struct MTFace *tf, int i);
void uvedit_edge_select(struct Scene *scene, struct EditFace *efa, struct MTFace *tf, int i);
void uvedit_face_deselect(struct Scene *scene, struct EditFace *efa, struct MTFace *tf);
void uvedit_face_select(struct Scene *scene, struct EditFace *efa, struct MTFace *tf);
void uvedit_uv_deselect(struct Scene *scene, struct EditFace *efa, struct MTFace *tf, int i);
void uvedit_uv_select(struct Scene *scene, struct EditFace *efa, struct MTFace *tf, int i);


int ED_uvedit_nearest_uv(struct Scene *scene, struct Object *obedit, struct Image *ima, float co[2], float uv[2]);

/* uvedit_unwrap_ops.c */
void ED_uvedit_live_unwrap_begin(struct Scene *scene, struct Object *obedit);
void ED_uvedit_live_unwrap_re_solve(void);
void ED_uvedit_live_unwrap_end(short cancel);

/* single call up unwrap using scene settings, used for edge tag unwrapping */
void ED_unwrap_lscm(struct Scene *scene, struct Object *obedit, const short sel);

/* uvedit_draw.c */
void draw_uvedit_main(struct SpaceImage *sima, struct ARegion *ar, struct Scene *scene, struct Object *obedit);

#endif /* ED_UVEDIT_H */


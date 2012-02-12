/*
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
 * Contributor(s): Joseph Eagar.
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#ifndef __BMESH_MARKING_H__
#define __BMESH_MARKING_H__

/** \file blender/bmesh/bmesh_marking.h
 *  \ingroup bmesh
 */

typedef struct BMEditSelection
{
	struct BMEditSelection *next, *prev;
	void *data;
	char htype;
} BMEditSelection;

/* geometry hiding code */
void BM_elem_hide_set(BMesh *bm, void *element, int hide);
void BM_vert_hide_set(BMesh *bm, BMVert *v, int hide);
void BM_edge_hide_set(BMesh *bm, BMEdge *e, int hide);
void BM_face_hide_set(BMesh *bm, BMFace *f, int hide);

/* Selection code */
void BM_elem_select_set(struct BMesh *bm, void *element, int select);
/* I don't use this function anywhere, been using BM_elem_flag_test instead.
 * Need to decide either to keep it and convert everything over, or
 * chuck it.*/
int BM_elem_select_test(BMesh *bm, const void *element);

void BM_clear_flag_all(BMesh *bm, const char hflag);

/* individual element select functions, BM_elem_select_set is a shortcut for these
 * that automatically detects which one to use*/
void BM_vert_select(struct BMesh *bm, struct BMVert *v, int select);
void BM_edge_select(struct BMesh *bm, struct BMEdge *e, int select);
void BM_face_select(struct BMesh *bm, struct BMFace *f, int select);

void BM_select_mode_set(struct BMesh *bm, int selectmode);

/* counts number of elements with flag set */
int BM_mesh_count_flag(struct BMesh *bm, const char htype, const char hflag, int respecthide);

/* edit selection stuff */
void    BM_active_face_set(BMesh *em, BMFace *f);
BMFace *BM_active_face_get(BMesh *bm, int sloppy);
void BM_editselection_center(BMesh *bm, float r_center[3], BMEditSelection *ese);
void BM_editselection_normal(float r_normal[3], BMEditSelection *ese);
void BM_editselection_plane(BMesh *bm, float r_plane[3], BMEditSelection *ese);

int  BM_select_history_check(BMesh *bm, void *data);
void BM_select_history_remove(BMesh *bm, void *data);
void BM_select_history_store(BMesh *bm, void *data);
void BM_select_history_validate(BMesh *bm);
void BM_select_history_clear(BMesh *em);

#endif /* __BMESH_MARKING_H__ */

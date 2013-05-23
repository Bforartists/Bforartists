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

#ifndef __BMESH_QUERIES_H__
#define __BMESH_QUERIES_H__

/** \file blender/bmesh/intern/bmesh_queries.h
 *  \ingroup bmesh
 */

bool    BM_vert_in_face(BMFace *f, BMVert *v);
int     BM_verts_in_face_count(BMFace *f, BMVert **varr, int len);
bool    BM_verts_in_face(BMFace *f, BMVert **varr, int len);

bool    BM_edge_in_face(BMFace *f, BMEdge *e);
bool    BM_edge_in_loop(BMEdge *e, BMLoop *l);

bool    BM_vert_in_edge(const BMEdge *e, const BMVert *v);
bool    BM_verts_in_edge(BMVert *v1, BMVert *v2, BMEdge *e);

float   BM_edge_calc_length(BMEdge *e);
float   BM_edge_calc_length_squared(BMEdge *e);
bool    BM_edge_face_pair(BMEdge *e, BMFace **r_fa, BMFace **r_fb);
bool    BM_edge_loop_pair(BMEdge *e, BMLoop **r_la, BMLoop **r_lb);
BMVert *BM_edge_other_vert(BMEdge *e, BMVert *v);
BMLoop *BM_edge_other_loop(BMEdge *e, BMLoop *l);
BMLoop *BM_face_other_edge_loop(BMFace *f, BMEdge *e, BMVert *v);
BMLoop *BM_loop_other_edge_loop(BMLoop *l, BMVert *v);
BMLoop *BM_face_other_vert_loop(BMFace *f, BMVert *v_prev, BMVert *v);
BMLoop *BM_loop_other_vert_loop(BMLoop *l, BMVert *v);
BMLoop *BM_vert_step_fan_loop(BMLoop *l, BMEdge **e_step);
BMLoop *BM_vert_find_first_loop(BMVert *v);

int     BM_vert_edge_count_nonwire(BMVert *v);
int     BM_vert_edge_count(BMVert *v);
int     BM_edge_face_count(BMEdge *e);
int     BM_vert_face_count(BMVert *v);
BMEdge *BM_vert_other_disk_edge(BMVert *v, BMEdge *e);

bool    BM_vert_is_wire(BMVert *v);
bool    BM_edge_is_wire(BMEdge *e);

bool    BM_vert_is_manifold(BMVert *v);
bool    BM_edge_is_manifold(BMEdge *e);
bool    BM_vert_is_boundary(BMVert *v);
bool    BM_edge_is_boundary(BMEdge *e);
bool    BM_edge_is_contiguous(BMEdge *e);
bool    BM_edge_is_convex(BMEdge *e);

bool    BM_loop_is_convex(BMLoop *l);

float   BM_loop_calc_face_angle(BMLoop *l);
void    BM_loop_calc_face_normal(BMLoop *l, float r_normal[3]);
void    BM_loop_calc_face_direction(BMLoop *l, float r_normal[3]);
void    BM_loop_calc_face_tangent(BMLoop *l, float r_tangent[3]);

float   BM_edge_calc_face_angle(BMEdge *e);
float   BM_edge_calc_face_angle_signed(BMEdge *e);
void    BM_edge_calc_face_tangent(BMEdge *e, BMLoop *e_loop, float r_tangent[3]);

float   BM_vert_calc_edge_angle(BMVert *v);
float   BM_vert_calc_shell_factor(BMVert *v);
float   BM_vert_calc_shell_factor_ex(BMVert *v, const char hflag);
float   BM_vert_calc_mean_tagged_edge_length(BMVert *v);

BMLoop *BM_face_find_shortest_loop(BMFace *f);
BMLoop *BM_face_find_longest_loop(BMFace *f);

BMEdge *BM_edge_exists(BMVert *v1, BMVert *v2);
BMEdge *BM_edge_find_double(BMEdge *e);

bool    BM_face_exists(BMVert **varr, int len, BMFace **r_existface);

bool    BM_face_exists_multi(BMVert **varr, BMEdge **earr, int len);
bool    BM_face_exists_multi_edge(BMEdge **earr, int len);

int     BM_face_share_face_count(BMFace *f1, BMFace *f2);
int     BM_face_share_edge_count(BMFace *f1, BMFace *f2);

bool    BM_face_share_face_check(BMFace *f1, BMFace *f2);
bool    BM_face_share_edge_check(BMFace *f1, BMFace *f2);
bool    BM_edge_share_face_check(BMEdge *e1, BMEdge *e2);
bool    BM_edge_share_quad_check(BMEdge *e1, BMEdge *e2);
bool    BM_edge_share_vert_check(BMEdge *e1, BMEdge *e2);

BMVert *BM_edge_share_vert(BMEdge *e1, BMEdge *e2);
BMLoop *BM_face_vert_share_loop(BMFace *f, BMVert *v);
BMLoop *BM_face_edge_share_loop(BMFace *f, BMEdge *e);

void    BM_edge_ordered_verts(BMEdge *edge, BMVert **r_v1, BMVert **r_v2);
void    BM_edge_ordered_verts_ex(BMEdge *edge, BMVert **r_v1, BMVert **r_v2,
                                 BMLoop *edge_loop);

bool BM_edge_is_any_vert_flag_test(BMEdge *e, const char hflag);
bool BM_face_is_any_vert_flag_test(BMFace *f, const char hflag);
bool BM_face_is_any_edge_flag_test(BMFace *f, const char hflag);

float BM_mesh_calc_volume(BMesh *bm, bool is_signed);

/* not really any good place  to put this */
float bmesh_subd_falloff_calc(const int falloff, float val);

#endif /* __BMESH_QUERIES_H__ */

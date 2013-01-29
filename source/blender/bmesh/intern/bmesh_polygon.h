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

#ifndef __BMESH_POLYGON_H__
#define __BMESH_POLYGON_H__

/** \file blender/bmesh/intern/bmesh_polygon.h
 *  \ingroup bmesh
 */

float BM_face_calc_area(BMFace *f);
float BM_face_calc_perimeter(BMFace *f);
void  BM_face_calc_center_bounds(BMFace *f, float center[3]);
void  BM_face_calc_center_mean(BMFace *f, float center[3]);

void  BM_face_normal_update(BMFace *f);
void  BM_face_normal_update_vcos(BMesh *bm, BMFace *f, float no[3],
                                 float const (*vertexCos)[3]);

void  BM_edge_normals_update(BMEdge *e);

void  BM_vert_normal_update(BMVert *v);
void  BM_vert_normal_update_all(BMVert *v);

void  BM_face_normal_flip(BMesh *bm, BMFace *f);
bool  BM_face_point_inside_test(BMFace *f, const float co[3]);

void  BM_face_triangulate(BMesh *bm, BMFace *f, BMFace **newfaces,
                          const bool use_beauty, const bool use_tag);

void  BM_face_legal_splits(BMesh *bm, BMFace *f, BMLoop *(*loops)[2], int len);

void BM_face_as_array_vert_tri(BMFace *f, BMVert *r_verts[3]);
void BM_face_as_array_vert_quad(BMFace *f, BMVert *r_verts[4]);

#endif /* __BMESH_POLYGON_H__ */

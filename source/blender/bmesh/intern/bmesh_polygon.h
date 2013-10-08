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

#include "BLI_compiler_attrs.h"

int   BM_face_calc_tessellation(const BMFace *f, BMLoop **r_loops, int (*r_index)[3]) ATTR_WARN_UNUSED_RESULT ATTR_NONNULL();
void  BM_face_calc_normal(const BMFace *f, float r_no[3]) ATTR_NONNULL();
void  BM_face_calc_normal_vcos(BMesh *bm, BMFace *f, float r_no[3],
                               float const (*vertexCos)[3]) ATTR_NONNULL();
float BM_face_calc_area(BMFace *f) ATTR_WARN_UNUSED_RESULT ATTR_NONNULL();
float BM_face_calc_perimeter(BMFace *f) ATTR_WARN_UNUSED_RESULT ATTR_NONNULL();
void  BM_face_calc_plane(BMFace *f, float r_plane[3]) ATTR_NONNULL();
void  BM_face_calc_center_bounds(BMFace *f, float center[3]) ATTR_NONNULL();
void  BM_face_calc_center_mean(BMFace *f, float center[3]) ATTR_NONNULL();
void  BM_face_calc_center_mean_vcos(BMesh *bm, BMFace *f, float r_cent[3],
                                    float const (*vertexCos)[3]) ATTR_NONNULL();
void  BM_face_calc_center_mean_weighted(BMFace *f, float center[3]) ATTR_NONNULL();

void  BM_face_normal_update(BMFace *f) ATTR_NONNULL();

void  BM_edge_normals_update(BMEdge *e) ATTR_NONNULL();

void  BM_vert_normal_update(BMVert *v) ATTR_NONNULL();
void  BM_vert_normal_update_all(BMVert *v) ATTR_NONNULL();

void  BM_face_normal_flip(BMesh *bm, BMFace *f) ATTR_NONNULL();
bool  BM_face_point_inside_test(BMFace *f, const float co[3]) ATTR_WARN_UNUSED_RESULT ATTR_NONNULL();

void  BM_face_triangulate(BMesh *bm, BMFace *f, BMFace **newfaces,
                          struct MemArena *sf_arena,
                          const bool use_beauty, const bool use_tag) ATTR_NONNULL(1, 2);

void  BM_face_legal_splits(BMFace *f, BMLoop *(*loops)[2], int len) ATTR_NONNULL();

void BM_face_as_array_vert_tri(BMFace *f, BMVert *r_verts[3]) ATTR_NONNULL();
void BM_face_as_array_vert_quad(BMFace *f, BMVert *r_verts[4]) ATTR_NONNULL();

void BM_face_as_array_loop_tri(BMFace *f, BMLoop *r_loops[3]) ATTR_NONNULL();
void BM_face_as_array_loop_quad(BMFace *f, BMLoop *r_loops[4]) ATTR_NONNULL();

#endif /* __BMESH_POLYGON_H__ */

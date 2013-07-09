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
 * Contributor(s): Geoffrey Bantle, Levi Schooley.
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#ifndef __BMESH_MESH_H__
#define __BMESH_MESH_H__

/** \file blender/bmesh/intern/bmesh_mesh.h
 *  \ingroup bmesh
 */

struct BMAllocTemplate;

void   BM_mesh_elem_toolflags_ensure(BMesh *bm);
void   BM_mesh_elem_toolflags_clear(BMesh *bm);
BMesh *BM_mesh_create(const struct BMAllocTemplate *allocsize);

void   BM_mesh_free(BMesh *bm);
void   BM_mesh_data_free(BMesh *bm);
void   BM_mesh_clear(BMesh *bm);

void BM_mesh_normals_update(BMesh *bm);

void bmesh_edit_begin(BMesh *bm, const BMOpTypeFlag type_flag);
void bmesh_edit_end(BMesh *bm, const BMOpTypeFlag type_flag);

void BM_mesh_elem_index_ensure(BMesh *bm, const char hflag);
void BM_mesh_elem_index_validate(BMesh *bm, const char *location, const char *func,
                                 const char *msg_a, const char *msg_b);
int  BM_mesh_elem_count(BMesh *bm, const char htype);

void BM_mesh_remap(BMesh *bm, int *vert_idx, int *edge_idx, int *face_idx);

BMVert *BM_vert_at_index(BMesh *bm, const int index);
BMEdge *BM_edge_at_index(BMesh *bm, const int index);
BMFace *BM_face_at_index(BMesh *bm, const int index);

typedef struct BMAllocTemplate {
	int totvert, totedge, totloop, totface;
} BMAllocTemplate;

extern const BMAllocTemplate bm_mesh_allocsize_default;
extern const BMAllocTemplate bm_mesh_chunksize_default;

enum {
	BM_MESH_CREATE_USE_TOOLFLAGS = (1 << 0)
};

#endif /* __BMESH_MESH_H__ */

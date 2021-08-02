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
 * The Original Code is Copyright (C) 2019 by Blender Foundation
 * All rights reserved.
 */

#pragma once

/** \file
 * \ingroup bke
 */

#ifdef __cplusplus
extern "C" {
#endif

struct Mesh;

struct Mesh *BKE_mesh_remesh_voxel_fix_poles(const struct Mesh *mesh);
struct Mesh *BKE_mesh_remesh_voxel(const struct Mesh *mesh,
                                   float voxel_size,
                                   float adaptivity,
                                   float isovalue);
struct Mesh *BKE_mesh_remesh_quadriflow(const struct Mesh *mesh,
                                        int target_faces,
                                        int seed,
                                        bool preserve_sharp,
                                        bool preserve_boundary,
                                        bool adaptive_scale,
                                        void (*update_cb)(void *, float progress, int *cancel),
                                        void *update_cb_data);

/* Data reprojection functions */
void BKE_mesh_remesh_reproject_paint_mask(struct Mesh *target, struct Mesh *source);
void BKE_remesh_reproject_vertex_paint(struct Mesh *target, const struct Mesh *source);
void BKE_remesh_reproject_sculpt_face_sets(struct Mesh *target, struct Mesh *source);

#ifdef __cplusplus
}
#endif

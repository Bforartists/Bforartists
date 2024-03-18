/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */
#pragma once

/** \file
 * \ingroup bke
 */

struct Mesh;

enum MeshForeachFlag {
  MESH_FOREACH_NOP = 0,
  /* foreachMappedVert, foreachMappedLoop, foreachMappedFaceCenter */
  MESH_FOREACH_USE_NORMAL = (1 << 0),
};

void BKE_mesh_foreach_mapped_vert(
    const Mesh *mesh,
    void (*func)(void *user_data, int index, const float co[3], const float no[3]),
    void *user_data,
    MeshForeachFlag flag);
/**
 * Copied from #cdDM_foreachMappedEdge.
 * \param tot_edges: Number of original edges. Used to avoid calling the callback with invalid
 * edge indices.
 */
void BKE_mesh_foreach_mapped_edge(
    Mesh *mesh,
    int tot_edges,
    void (*func)(void *user_data, int index, const float v0co[3], const float v1co[3]),
    void *user_data);
void BKE_mesh_foreach_mapped_loop(Mesh *mesh,
                                  void (*func)(void *user_data,
                                               int vertex_index,
                                               int face_index,
                                               const float co[3],
                                               const float no[3]),
                                  void *user_data,
                                  MeshForeachFlag flag);
void BKE_mesh_foreach_mapped_face_center(
    Mesh *mesh,
    void (*func)(void *user_data, int index, const float cent[3], const float no[3]),
    void *user_data,
    MeshForeachFlag flag);
void BKE_mesh_foreach_mapped_subdiv_face_center(
    Mesh *mesh,
    void (*func)(void *user_data, int index, const float cent[3], const float no[3]),
    void *user_data,
    MeshForeachFlag flag);

void BKE_mesh_foreach_mapped_vert_coords_get(const Mesh *me_eval, float (*r_cos)[3], int totcos);

/* SPDX-FileCopyrightText: 2020 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup edsculpt
 */

#include <cmath>
#include <cstdlib>

#include "MEM_guardedalloc.h"

#include "BLI_linklist_stack.h"
#include "BLI_math_geom.h"
#include "BLI_math_vector.h"
#include "BLI_task.h"

#include "DNA_brush_types.h"
#include "DNA_mesh_types.h"
#include "DNA_meshdata_types.h"
#include "DNA_object_types.h"

#include "BKE_ccg.h"
#include "BKE_context.h"
#include "BKE_mesh.hh"
#include "BKE_mesh_mapping.hh"
#include "BKE_object.hh"
#include "BKE_paint.hh"
#include "BKE_pbvh_api.hh"

#include "paint_intern.hh"
#include "sculpt_intern.hh"

#include "bmesh.h"

#define SCULPT_GEODESIC_VERTEX_NONE -1

/* Propagate distance from v1 and v2 to v0. */
static bool sculpt_geodesic_mesh_test_dist_add(const float (*vert_positions)[3],
                                               const int v0,
                                               const int v1,
                                               const int v2,
                                               float *dists,
                                               GSet *initial_verts)
{
  if (BLI_gset_haskey(initial_verts, POINTER_FROM_INT(v0))) {
    return false;
  }

  BLI_assert(dists[v1] != FLT_MAX);
  if (dists[v0] <= dists[v1]) {
    return false;
  }

  float dist0;
  if (v2 != SCULPT_GEODESIC_VERTEX_NONE) {
    BLI_assert(dists[v2] != FLT_MAX);
    if (dists[v0] <= dists[v2]) {
      return false;
    }
    dist0 = geodesic_distance_propagate_across_triangle(
        vert_positions[v0], vert_positions[v1], vert_positions[v2], dists[v1], dists[v2]);
  }
  else {
    float vec[3];
    sub_v3_v3v3(vec, vert_positions[v1], vert_positions[v0]);
    dist0 = dists[v1] + len_v3(vec);
  }

  if (dist0 < dists[v0]) {
    dists[v0] = dist0;
    return true;
  }

  return false;
}

static float *geodesic_mesh_create(Object *ob, GSet *initial_verts, const float limit_radius)
{
  SculptSession *ss = ob->sculpt;
  Mesh *mesh = BKE_object_get_original_mesh(ob);

  const int totvert = mesh->totvert;
  const int totedge = mesh->totedge;

  const float limit_radius_sq = limit_radius * limit_radius;

  float(*vert_positions)[3] = SCULPT_mesh_deformed_positions_get(ss);
  const blender::Span<blender::int2> edges = mesh->edges();
  const blender::OffsetIndices faces = mesh->faces();
  const blender::Span<int> corner_verts = mesh->corner_verts();
  const blender::Span<int> corner_edges = mesh->corner_edges();

  float *dists = static_cast<float *>(MEM_malloc_arrayN(totvert, sizeof(float), __func__));
  BLI_bitmap *edge_tag = BLI_BITMAP_NEW(totedge, "edge tag");

  if (ss->epmap.is_empty()) {
    ss->epmap = blender::bke::mesh::build_edge_to_face_map(
        faces, corner_edges, edges.size(), ss->edge_to_face_offsets, ss->edge_to_face_indices);
  }
  if (ss->vemap.is_empty()) {
    ss->vemap = blender::bke::mesh::build_vert_to_edge_map(
        edges, mesh->totvert, ss->vert_to_edge_offsets, ss->vert_to_edge_indices);
  }

  /* Both contain edge indices encoded as *void. */
  BLI_LINKSTACK_DECLARE(queue, void *);
  BLI_LINKSTACK_DECLARE(queue_next, void *);

  BLI_LINKSTACK_INIT(queue);
  BLI_LINKSTACK_INIT(queue_next);

  for (int i = 0; i < totvert; i++) {
    if (BLI_gset_haskey(initial_verts, POINTER_FROM_INT(i))) {
      dists[i] = 0.0f;
    }
    else {
      dists[i] = FLT_MAX;
    }
  }

  /* Masks vertices that are further than limit radius from an initial vertex. As there is no need
   * to define a distance to them the algorithm can stop earlier by skipping them. */
  BLI_bitmap *affected_vertex = BLI_BITMAP_NEW(totvert, "affected vertex");
  GSetIterator gs_iter;

  if (limit_radius == FLT_MAX) {
    /* In this case, no need to loop through all initial vertices to check distances as they are
     * all going to be affected. */
    BLI_bitmap_set_all(affected_vertex, true, totvert);
  }
  else {
    /* This is an O(n^2) loop used to limit the geodesic distance calculation to a radius. When
     * this optimization is needed, it is expected for the tool to request the distance to a low
     * number of vertices (usually just 1 or 2). */
    GSET_ITER (gs_iter, initial_verts) {
      const int v = POINTER_AS_INT(BLI_gsetIterator_getKey(&gs_iter));
      float *v_co = vert_positions[v];
      for (int i = 0; i < totvert; i++) {
        if (len_squared_v3v3(v_co, vert_positions[i]) <= limit_radius_sq) {
          BLI_BITMAP_ENABLE(affected_vertex, i);
        }
      }
    }
  }

  /* Add edges adjacent to an initial vertex to the queue. */
  for (int i = 0; i < totedge; i++) {
    const int v1 = edges[i][0];
    const int v2 = edges[i][1];
    if (!BLI_BITMAP_TEST(affected_vertex, v1) && !BLI_BITMAP_TEST(affected_vertex, v2)) {
      continue;
    }
    if (dists[v1] != FLT_MAX || dists[v2] != FLT_MAX) {
      BLI_LINKSTACK_PUSH(queue, POINTER_FROM_INT(i));
    }
  }

  do {
    while (BLI_LINKSTACK_SIZE(queue)) {
      const int e = POINTER_AS_INT(BLI_LINKSTACK_POP(queue));
      int v1 = edges[e][0];
      int v2 = edges[e][1];

      if (dists[v1] == FLT_MAX || dists[v2] == FLT_MAX) {
        if (dists[v1] > dists[v2]) {
          SWAP(int, v1, v2);
        }
        sculpt_geodesic_mesh_test_dist_add(
            vert_positions, v2, v1, SCULPT_GEODESIC_VERTEX_NONE, dists, initial_verts);
      }

      if (ss->epmap[e].size() != 0) {
        for (int face_map_index = 0; face_map_index < ss->epmap[e].size(); face_map_index++) {
          const int face = ss->epmap[e][face_map_index];
          if (ss->hide_poly && ss->hide_poly[face]) {
            continue;
          }
          for (const int v_other : corner_verts.slice(faces[face])) {
            if (ELEM(v_other, v1, v2)) {
              continue;
            }
            if (sculpt_geodesic_mesh_test_dist_add(
                    vert_positions, v_other, v1, v2, dists, initial_verts)) {
              for (int edge_map_index = 0; edge_map_index < ss->vemap[v_other].size();
                   edge_map_index++) {
                const int e_other = ss->vemap[v_other][edge_map_index];
                int ev_other;
                if (edges[e_other][0] == v_other) {
                  ev_other = edges[e_other][1];
                }
                else {
                  ev_other = edges[e_other][0];
                }

                if (e_other != e && !BLI_BITMAP_TEST(edge_tag, e_other) &&
                    (ss->epmap[e_other].size() == 0 || dists[ev_other] != FLT_MAX))
                {
                  if (BLI_BITMAP_TEST(affected_vertex, v_other) ||
                      BLI_BITMAP_TEST(affected_vertex, ev_other)) {
                    BLI_BITMAP_ENABLE(edge_tag, e_other);
                    BLI_LINKSTACK_PUSH(queue_next, POINTER_FROM_INT(e_other));
                  }
                }
              }
            }
          }
        }
      }
    }

    for (LinkNode *lnk = queue_next; lnk; lnk = lnk->next) {
      const int e = POINTER_AS_INT(lnk->link);
      BLI_BITMAP_DISABLE(edge_tag, e);
    }

    BLI_LINKSTACK_SWAP(queue, queue_next);

  } while (BLI_LINKSTACK_SIZE(queue));

  BLI_LINKSTACK_FREE(queue);
  BLI_LINKSTACK_FREE(queue_next);
  MEM_SAFE_FREE(edge_tag);
  MEM_SAFE_FREE(affected_vertex);

  return dists;
}

/* For sculpt mesh data that does not support a geodesic distances algorithm, fallback to the
 * distance to each vertex. In this case, only one of the initial vertices will be used to
 * calculate the distance. */
static float *geodesic_fallback_create(Object *ob, GSet *initial_verts)
{

  SculptSession *ss = ob->sculpt;
  Mesh *mesh = BKE_object_get_original_mesh(ob);
  const int totvert = mesh->totvert;
  float *dists = static_cast<float *>(MEM_malloc_arrayN(totvert, sizeof(float), __func__));
  int first_affected = SCULPT_GEODESIC_VERTEX_NONE;
  GSetIterator gs_iter;
  GSET_ITER (gs_iter, initial_verts) {
    first_affected = POINTER_AS_INT(BLI_gsetIterator_getKey(&gs_iter));
    break;
  }

  if (first_affected == SCULPT_GEODESIC_VERTEX_NONE) {
    for (int i = 0; i < totvert; i++) {
      dists[i] = FLT_MAX;
    }
    return dists;
  }

  const float *first_affected_co = SCULPT_vertex_co_get(
      ss, BKE_pbvh_index_to_vertex(ss->pbvh, first_affected));
  for (int i = 0; i < totvert; i++) {
    PBVHVertRef vertex = BKE_pbvh_index_to_vertex(ss->pbvh, i);

    dists[i] = len_v3v3(first_affected_co, SCULPT_vertex_co_get(ss, vertex));
  }

  return dists;
}

float *SCULPT_geodesic_distances_create(Object *ob, GSet *initial_verts, const float limit_radius)
{
  SculptSession *ss = ob->sculpt;
  switch (BKE_pbvh_type(ss->pbvh)) {
    case PBVH_FACES:
      return geodesic_mesh_create(ob, initial_verts, limit_radius);
    case PBVH_BMESH:
    case PBVH_GRIDS:
      return geodesic_fallback_create(ob, initial_verts);
  }
  BLI_assert_unreachable();
  return nullptr;
}

float *SCULPT_geodesic_from_vertex_and_symm(Sculpt *sd,
                                            Object *ob,
                                            const PBVHVertRef vertex,
                                            const float limit_radius)
{
  SculptSession *ss = ob->sculpt;
  GSet *initial_verts = BLI_gset_int_new("initial_verts");

  const char symm = SCULPT_mesh_symmetry_xyz_get(ob);
  for (char i = 0; i <= symm; ++i) {
    if (SCULPT_is_symmetry_iteration_valid(i, symm)) {
      PBVHVertRef v = {PBVH_REF_NONE};

      if (i == 0) {
        v = vertex;
      }
      else {
        float location[3];
        flip_v3_v3(location, SCULPT_vertex_co_get(ss, vertex), ePaintSymmetryFlags(i));
        v = SCULPT_nearest_vertex_get(sd, ob, location, FLT_MAX, false);
      }
      if (v.i != PBVH_REF_NONE) {
        BLI_gset_add(initial_verts, POINTER_FROM_INT(BKE_pbvh_vertex_to_index(ss->pbvh, v)));
      }
    }
  }

  float *dists = SCULPT_geodesic_distances_create(ob, initial_verts, limit_radius);
  BLI_gset_free(initial_verts, nullptr);
  return dists;
}

float *SCULPT_geodesic_from_vertex(Object *ob, const PBVHVertRef vertex, const float limit_radius)
{
  GSet *initial_verts = BLI_gset_int_new("initial_verts");
  BLI_gset_add(initial_verts,
               POINTER_FROM_INT(BKE_pbvh_vertex_to_index(ob->sculpt->pbvh, vertex)));
  float *dists = SCULPT_geodesic_distances_create(ob, initial_verts, limit_radius);
  BLI_gset_free(initial_verts, nullptr);
  return dists;
}

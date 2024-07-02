/* SPDX-FileCopyrightText: 2020 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup edsculpt
 */

#include "MEM_guardedalloc.h"

#include "BLI_task.h"

#include "DNA_brush_types.h"
#include "DNA_object_types.h"

#include "BKE_brush.hh"
#include "BKE_ccg.hh"
#include "BKE_colortools.hh"
#include "BKE_paint.hh"
#include "BKE_pbvh_api.hh"

#include "paint_intern.hh"
#include "sculpt_intern.hh"

#include "GPU_immediate.hh"
#include "GPU_state.hh"

#include <cmath>
#include <cstdlib>

#define BOUNDARY_VERTEX_NONE -1
#define BOUNDARY_STEPS_NONE -1

namespace blender::ed::sculpt_paint::boundary {

struct BoundaryInitialVertexFloodFillData {
  PBVHVertRef initial_vert;
  int initial_vert_i;
  int boundary_initial_vert_steps;
  PBVHVertRef boundary_initial_vert;
  int boundary_initial_vert_i;
  int *floodfill_steps;
  float radius_sq;
};

static bool initial_vert_floodfill_fn(SculptSession &ss,
                                      PBVHVertRef from_v,
                                      PBVHVertRef to_v,
                                      bool is_duplicate,
                                      BoundaryInitialVertexFloodFillData *data)
{
  int from_v_i = BKE_pbvh_vertex_to_index(*ss.pbvh, from_v);
  int to_v_i = BKE_pbvh_vertex_to_index(*ss.pbvh, to_v);

  if (!hide::vert_visible_get(ss, to_v)) {
    return false;
  }

  if (!is_duplicate) {
    data->floodfill_steps[to_v_i] = data->floodfill_steps[from_v_i] + 1;
  }
  else {
    data->floodfill_steps[to_v_i] = data->floodfill_steps[from_v_i];
  }

  if (SCULPT_vertex_is_boundary(ss, to_v)) {
    if (data->floodfill_steps[to_v_i] < data->boundary_initial_vert_steps) {
      data->boundary_initial_vert_steps = data->floodfill_steps[to_v_i];
      data->boundary_initial_vert_i = to_v_i;
      data->boundary_initial_vert = to_v;
    }
  }

  const float len_sq = len_squared_v3v3(SCULPT_vertex_co_get(ss, data->initial_vert),
                                        SCULPT_vertex_co_get(ss, to_v));
  return len_sq < data->radius_sq;
}

/* From a vertex index anywhere in the mesh, returns the closest vertex in a mesh boundary inside
 * the given radius, if it exists. */
static PBVHVertRef get_closest_boundary_vert(SculptSession &ss,
                                             const PBVHVertRef initial_vert,
                                             const float radius)
{

  if (SCULPT_vertex_is_boundary(ss, initial_vert)) {
    return initial_vert;
  }

  flood_fill::FillData flood = flood_fill::init_fill(ss);
  flood_fill::add_initial(flood, initial_vert);

  BoundaryInitialVertexFloodFillData fdata{};
  fdata.initial_vert = initial_vert;
  fdata.boundary_initial_vert = {BOUNDARY_VERTEX_NONE};
  fdata.boundary_initial_vert_steps = INT_MAX;
  fdata.radius_sq = radius * radius;

  fdata.floodfill_steps = MEM_cnew_array<int>(SCULPT_vertex_count_get(ss), __func__);

  flood_fill::execute(ss, flood, [&](PBVHVertRef from_v, PBVHVertRef to_v, bool is_duplicate) {
    return initial_vert_floodfill_fn(ss, from_v, to_v, is_duplicate, &fdata);
  });

  MEM_freeN(fdata.floodfill_steps);
  return fdata.boundary_initial_vert;
}

/* Used to allocate the memory of the boundary index arrays. This was decided considered the most
 * common use cases for the brush deformers, taking into account how many vertices those
 * deformations usually need in the boundary. */
static int BOUNDARY_INDICES_BLOCK_SIZE = 300;

static void add_index(SculptBoundary &boundary,
                      const PBVHVertRef new_vertex,
                      const int new_index,
                      const float distance,
                      GSet *included_verts)
{
  boundary.verts.append(new_vertex);

  if (!boundary.distance.is_empty()) {
    boundary.distance[new_index] = distance;
  }
  if (included_verts) {
    BLI_gset_add(included_verts, POINTER_FROM_INT(new_index));
  }
};

/**
 * This function is used to check where the propagation should stop when calculating the boundary,
 * as well as to check if the initial vertex is valid.
 */
static bool is_vert_in_editable_boundary(SculptSession &ss, const PBVHVertRef initial_vert)
{
  if (!hide::vert_visible_get(ss, initial_vert)) {
    return false;
  }

  int neighbor_count = 0;
  int boundary_vertex_count = 0;
  SculptVertexNeighborIter ni;
  SCULPT_VERTEX_NEIGHBORS_ITER_BEGIN (ss, initial_vert, ni) {
    if (hide::vert_visible_get(ss, ni.vertex)) {
      neighbor_count++;
      if (SCULPT_vertex_is_boundary(ss, ni.vertex)) {
        boundary_vertex_count++;
      }
    }
  }
  SCULPT_VERTEX_NEIGHBORS_ITER_END(ni);

  /* Corners are ambiguous as it can't be decide which boundary should be active. The flood fill
   * should also stop at corners. */
  if (neighbor_count <= 2) {
    return false;
  }

  /* Non manifold geometry in the mesh boundary.
   * The deformation result will be unpredictable and not very useful. */
  if (boundary_vertex_count > 2) {
    return false;
  }

  return true;
}

/* Flood fill that adds to the boundary data all the vertices from a boundary and its duplicates.
 */

struct BoundaryFloodFillData {
  SculptBoundary *boundary;
  GSet *included_verts;

  PBVHVertRef last_visited_vertex;
};

static bool floodfill_fn(SculptSession &ss,
                         PBVHVertRef from_v,
                         PBVHVertRef to_v,
                         bool is_duplicate,
                         BoundaryFloodFillData *data)
{
  int from_v_i = BKE_pbvh_vertex_to_index(*ss.pbvh, from_v);
  int to_v_i = BKE_pbvh_vertex_to_index(*ss.pbvh, to_v);

  SculptBoundary &boundary = *data->boundary;
  if (!SCULPT_vertex_is_boundary(ss, to_v)) {
    return false;
  }
  const float edge_len = len_v3v3(SCULPT_vertex_co_get(ss, from_v),
                                  SCULPT_vertex_co_get(ss, to_v));
  const float distance_boundary_to_dst = !boundary.distance.is_empty() ?
                                             boundary.distance[from_v_i] + edge_len :
                                             0.0f;
  add_index(boundary, to_v, to_v_i, distance_boundary_to_dst, data->included_verts);
  if (!is_duplicate) {
    boundary.edges.append({from_v, to_v});
  }
  return is_vert_in_editable_boundary(ss, to_v);
}

static void indices_init(SculptSession &ss,
                         SculptBoundary &boundary,
                         const bool init_boundary_distances,
                         const PBVHVertRef initial_boundary_vert)
{

  const int totvert = SCULPT_vertex_count_get(ss);

  if (init_boundary_distances) {
    boundary.distance = Array<float>(totvert, 0.0f);
  }

  GSet *included_verts = BLI_gset_int_new_ex("included verts", BOUNDARY_INDICES_BLOCK_SIZE);
  flood_fill::FillData flood = flood_fill::init_fill(ss);

  int initial_boundary_index = BKE_pbvh_vertex_to_index(*ss.pbvh, initial_boundary_vert);

  boundary.initial_vert = initial_boundary_vert;
  boundary.initial_vert_i = initial_boundary_index;

  copy_v3_v3(boundary.initial_vert_position, SCULPT_vertex_co_get(ss, boundary.initial_vert));
  add_index(boundary, initial_boundary_vert, initial_boundary_index, 0.0f, included_verts);
  flood_fill::add_initial(flood, boundary.initial_vert);

  BoundaryFloodFillData fdata{};
  fdata.boundary = &boundary;
  fdata.included_verts = included_verts;
  fdata.last_visited_vertex = {BOUNDARY_VERTEX_NONE};

  flood_fill::execute(ss, flood, [&](PBVHVertRef from_v, PBVHVertRef to_v, bool is_duplicate) {
    return floodfill_fn(ss, from_v, to_v, is_duplicate, &fdata);
  });

  /* Check if the boundary loops into itself and add the extra preview edge to close the loop. */
  if (fdata.last_visited_vertex.i != BOUNDARY_VERTEX_NONE &&
      is_vert_in_editable_boundary(ss, fdata.last_visited_vertex))
  {
    SculptVertexNeighborIter ni;
    SCULPT_VERTEX_NEIGHBORS_ITER_BEGIN (ss, fdata.last_visited_vertex, ni) {
      if (BLI_gset_haskey(included_verts, POINTER_FROM_INT(ni.index)) &&
          is_vert_in_editable_boundary(ss, ni.vertex))
      {
        boundary.edges.append({fdata.last_visited_vertex, ni.vertex});
        boundary.forms_loop = true;
      }
    }
    SCULPT_VERTEX_NEIGHBORS_ITER_END(ni);
  }

  BLI_gset_free(included_verts, nullptr);
}

/**
 * This functions initializes all data needed to calculate falloffs and deformation from the
 * boundary into the mesh into a #SculptBoundaryEditInfo array. This includes how many steps are
 * needed to go from a boundary vertex to an interior vertex and which vertex of the boundary is
 * the closest one.
 */
static void edit_data_init(SculptSession &ss,
                           SculptBoundary &boundary,
                           const PBVHVertRef initial_vert,
                           const float radius)
{
  const int totvert = SCULPT_vertex_count_get(ss);

  const bool has_duplicates = BKE_pbvh_type(*ss.pbvh) == PBVH_GRIDS;

  boundary.edit_info = Array<SculptBoundaryEditInfo>(totvert);

  for (int i = 0; i < totvert; i++) {
    boundary.edit_info[i].original_vertex_i = BOUNDARY_VERTEX_NONE;
    boundary.edit_info[i].propagation_steps_num = BOUNDARY_STEPS_NONE;
  }

  std::queue<PBVHVertRef> current_iteration;
  std::queue<PBVHVertRef> next_iteration;

  for (int i = 0; i < boundary.verts.size(); i++) {
    int index = BKE_pbvh_vertex_to_index(*ss.pbvh, boundary.verts[i]);

    boundary.edit_info[index].original_vertex_i = BKE_pbvh_vertex_to_index(*ss.pbvh,
                                                                           boundary.verts[i]);
    boundary.edit_info[index].propagation_steps_num = 0;

    /* This ensures that all duplicate vertices in the boundary have the same original_vertex
     * index, so the deformation for them will be the same. */
    if (has_duplicates) {
      SculptVertexNeighborIter ni_duplis;
      SCULPT_VERTEX_DUPLICATES_AND_NEIGHBORS_ITER_BEGIN (ss, boundary.verts[i], ni_duplis) {
        if (ni_duplis.is_duplicate) {
          boundary.edit_info[ni_duplis.index].original_vertex_i = BKE_pbvh_vertex_to_index(
              *ss.pbvh, boundary.verts[i]);
        }
      }
      SCULPT_VERTEX_NEIGHBORS_ITER_END(ni_duplis);
    }

    current_iteration.push(boundary.verts[i]);
  }

  int propagation_steps_num = 0;
  float accum_distance = 0.0f;

  while (true) {
    /* Stop adding steps to edit info. This happens when a steps is further away from the boundary
     * than the brush radius or when the entire mesh was already processed. */
    if (accum_distance > radius || current_iteration.empty()) {
      boundary.max_propagation_steps = propagation_steps_num;
      break;
    }

    while (!current_iteration.empty()) {
      PBVHVertRef from_v = current_iteration.front();
      current_iteration.pop();

      int from_v_i = BKE_pbvh_vertex_to_index(*ss.pbvh, from_v);

      SculptVertexNeighborIter ni;
      SCULPT_VERTEX_DUPLICATES_AND_NEIGHBORS_ITER_BEGIN (ss, from_v, ni) {
        const bool is_visible = hide::vert_visible_get(ss, ni.vertex);
        if (!is_visible ||
            boundary.edit_info[ni.index].propagation_steps_num != BOUNDARY_STEPS_NONE)
        {
          continue;
        }
        boundary.edit_info[ni.index].original_vertex_i =
            boundary.edit_info[from_v_i].original_vertex_i;

        if (ni.is_duplicate) {
          /* Grids duplicates handling. */
          boundary.edit_info[ni.index].propagation_steps_num =
              boundary.edit_info[from_v_i].propagation_steps_num;
        }
        else {
          boundary.edit_info[ni.index].propagation_steps_num =
              boundary.edit_info[from_v_i].propagation_steps_num + 1;

          next_iteration.push(ni.vertex);

          /* When copying the data to the neighbor for the next iteration, it has to be copied to
           * all its duplicates too. This is because it is not possible to know if the updated
           * neighbor or one if its uninitialized duplicates is going to come first in order to
           * copy the data in the from_v neighbor iterator. */
          if (has_duplicates) {
            SculptVertexNeighborIter ni_duplis;
            SCULPT_VERTEX_DUPLICATES_AND_NEIGHBORS_ITER_BEGIN (ss, ni.vertex, ni_duplis) {
              if (ni_duplis.is_duplicate) {
                boundary.edit_info[ni_duplis.index].original_vertex_i =
                    boundary.edit_info[from_v_i].original_vertex_i;
                boundary.edit_info[ni_duplis.index].propagation_steps_num =
                    boundary.edit_info[from_v_i].propagation_steps_num + 1;
              }
            }
            SCULPT_VERTEX_NEIGHBORS_ITER_END(ni_duplis);
          }

          /* Check the distance using the vertex that was propagated from the initial vertex that
           * was used to initialize the boundary. */
          if (boundary.edit_info[from_v_i].original_vertex_i ==
              BKE_pbvh_vertex_to_index(*ss.pbvh, initial_vert))
          {
            boundary.pivot_vertex = ni.vertex;
            copy_v3_v3(boundary.initial_pivot_position, SCULPT_vertex_co_get(ss, ni.vertex));
            accum_distance += len_v3v3(SCULPT_vertex_co_get(ss, from_v),
                                       SCULPT_vertex_co_get(ss, ni.vertex));
          }
        }
      }
      SCULPT_VERTEX_NEIGHBORS_ITER_END(ni);
    }

    /* Copy the new vertices to the queue to be processed in the next iteration. */
    while (!next_iteration.empty()) {
      PBVHVertRef next_v = next_iteration.front();
      next_iteration.pop();
      current_iteration.push(next_v);
    }

    propagation_steps_num++;
  }
}

/* This functions assigns a falloff factor to each one of the SculptBoundaryEditInfo structs based
 * on the brush curve and its propagation steps. The falloff goes from the boundary into the mesh.
 */
static void init_falloff(SculptSession &ss,
                         SculptBoundary &boundary,
                         const Brush &brush,
                         const float radius)
{
  const int totvert = SCULPT_vertex_count_get(ss);
  BKE_curvemapping_init(brush.curve);

  for (int i = 0; i < totvert; i++) {
    if (boundary.edit_info[i].propagation_steps_num != -1) {
      boundary.edit_info[i].strength_factor = BKE_brush_curve_strength(
          &brush, boundary.edit_info[i].propagation_steps_num, boundary.max_propagation_steps);
    }

    if (boundary.edit_info[i].original_vertex_i ==
        BKE_pbvh_vertex_to_index(*ss.pbvh, boundary.initial_vert))
    {
      /* All vertices that are propagated from the original vertex won't be affected by the
       * boundary falloff, so there is no need to calculate anything else. */
      continue;
    }

    if (boundary.distance.is_empty()) {
      /* There are falloff modes that do not require to modify the previously calculated falloff
       * based on boundary distances. */
      continue;
    }

    const float boundary_distance = boundary.distance[boundary.edit_info[i].original_vertex_i];
    float falloff_distance = 0.0f;
    float direction = 1.0f;

    switch (brush.boundary_falloff_type) {
      case BRUSH_BOUNDARY_FALLOFF_RADIUS:
        falloff_distance = boundary_distance;
        break;
      case BRUSH_BOUNDARY_FALLOFF_LOOP: {
        const int div = boundary_distance / radius;
        const float mod = fmodf(boundary_distance, radius);
        falloff_distance = div % 2 == 0 ? mod : radius - mod;
        break;
      }
      case BRUSH_BOUNDARY_FALLOFF_LOOP_INVERT: {
        const int div = boundary_distance / radius;
        const float mod = fmodf(boundary_distance, radius);
        falloff_distance = div % 2 == 0 ? mod : radius - mod;
        /* Inverts the falloff in the intervals 1 2 5 6 9 10 ... etc. */
        if (((div - 1) & 2) == 0) {
          direction = -1.0f;
        }
        break;
      }
      case BRUSH_BOUNDARY_FALLOFF_CONSTANT:
        /* For constant falloff distances are not allocated, so this should never happen. */
        BLI_assert(false);
    }

    boundary.edit_info[i].strength_factor *= direction * BKE_brush_curve_strength(
                                                             &brush, falloff_distance, radius);
  }
}

std::unique_ptr<SculptBoundary> data_init(Object &object,
                                          const Brush *brush,
                                          const PBVHVertRef initial_vert,
                                          const float radius)
{
  SculptSession &ss = *object.sculpt;

  if (initial_vert.i == PBVH_REF_NONE) {
    return nullptr;
  }

  SCULPT_vertex_random_access_ensure(ss);
  SCULPT_boundary_info_ensure(object);

  const PBVHVertRef boundary_initial_vert = get_closest_boundary_vert(ss, initial_vert, radius);

  if (boundary_initial_vert.i == BOUNDARY_VERTEX_NONE) {
    return nullptr;
  }

  /* Starting from a vertex that is the limit of a boundary is ambiguous, so return nullptr instead
   * of forcing a random active boundary from a corner. */
  if (!is_vert_in_editable_boundary(ss, initial_vert)) {
    return nullptr;
  }

  std::unique_ptr<SculptBoundary> boundary = std::make_unique<SculptBoundary>();
  *boundary = {};

  const bool init_boundary_distances = brush ? brush->boundary_falloff_type !=
                                                   BRUSH_BOUNDARY_FALLOFF_CONSTANT :
                                               false;

  indices_init(ss, *boundary, init_boundary_distances, boundary_initial_vert);

  const float boundary_radius = brush ? radius * (1.0f + brush->boundary_offset) : radius;
  edit_data_init(ss, *boundary, boundary_initial_vert, boundary_radius);

  return boundary;
}

/* These functions initialize the required vectors for the desired deformation using the
 * SculptBoundaryEditInfo. They calculate the data using the vertices that have the
 * max_propagation_steps value and them this data is copied to the rest of the vertices using the
 * original vertex index. */
static void bend_data_init(SculptSession &ss, SculptBoundary &boundary)
{
  const int totvert = SCULPT_vertex_count_get(ss);
  boundary.bend.pivot_rotation_axis = Array<float3>(totvert, float3(0));
  boundary.bend.pivot_positions = Array<float3>(totvert, float3(0));

  for (int i = 0; i < totvert; i++) {
    if (boundary.edit_info[i].propagation_steps_num != boundary.max_propagation_steps) {
      continue;
    }

    PBVHVertRef vertex = BKE_pbvh_index_to_vertex(*ss.pbvh, i);

    float dir[3];
    float3 normal = SCULPT_vertex_normal_get(ss, vertex);
    sub_v3_v3v3(
        dir,
        SCULPT_vertex_co_get(
            ss, BKE_pbvh_index_to_vertex(*ss.pbvh, boundary.edit_info[i].original_vertex_i)),
        SCULPT_vertex_co_get(ss, vertex));
    cross_v3_v3v3(
        boundary.bend.pivot_rotation_axis[boundary.edit_info[i].original_vertex_i], dir, normal);
    normalize_v3(boundary.bend.pivot_rotation_axis[boundary.edit_info[i].original_vertex_i]);
    copy_v3_v3(boundary.bend.pivot_positions[boundary.edit_info[i].original_vertex_i],
               SCULPT_vertex_co_get(ss, vertex));
  }

  for (int i = 0; i < totvert; i++) {
    if (boundary.edit_info[i].propagation_steps_num == BOUNDARY_STEPS_NONE) {
      continue;
    }
    copy_v3_v3(boundary.bend.pivot_positions[i],
               boundary.bend.pivot_positions[boundary.edit_info[i].original_vertex_i]);
    copy_v3_v3(boundary.bend.pivot_rotation_axis[i],
               boundary.bend.pivot_rotation_axis[boundary.edit_info[i].original_vertex_i]);
  }
}

static void slide_data_init(SculptSession &ss, SculptBoundary &boundary)
{
  const int totvert = SCULPT_vertex_count_get(ss);
  boundary.slide.directions = Array<float3>(totvert, float3(0));

  for (int i = 0; i < totvert; i++) {
    if (boundary.edit_info[i].propagation_steps_num != boundary.max_propagation_steps) {
      continue;
    }
    sub_v3_v3v3(
        boundary.slide.directions[boundary.edit_info[i].original_vertex_i],
        SCULPT_vertex_co_get(
            ss, BKE_pbvh_index_to_vertex(*ss.pbvh, boundary.edit_info[i].original_vertex_i)),
        SCULPT_vertex_co_get(ss, BKE_pbvh_index_to_vertex(*ss.pbvh, i)));
    normalize_v3(boundary.slide.directions[boundary.edit_info[i].original_vertex_i]);
  }

  for (int i = 0; i < totvert; i++) {
    if (boundary.edit_info[i].propagation_steps_num == BOUNDARY_STEPS_NONE) {
      continue;
    }
    copy_v3_v3(boundary.slide.directions[i],
               boundary.slide.directions[boundary.edit_info[i].original_vertex_i]);
  }
}

static void twist_data_init(SculptSession &ss, SculptBoundary &boundary)
{
  zero_v3(boundary.twist.pivot_position);
  Array<float3> face_verts(boundary.verts.size());
  for (int i = 0; i < boundary.verts.size(); i++) {
    add_v3_v3(boundary.twist.pivot_position, SCULPT_vertex_co_get(ss, boundary.verts[i]));
    copy_v3_v3(face_verts[i], SCULPT_vertex_co_get(ss, boundary.verts[i]));
  }
  mul_v3_fl(boundary.twist.pivot_position, 1.0f / boundary.verts.size());
  if (boundary.forms_loop) {
    normal_poly_v3(boundary.twist.rotation_axis,
                   reinterpret_cast<const float(*)[3]>(face_verts.data()),
                   boundary.verts.size());
  }
  else {
    sub_v3_v3v3(boundary.twist.rotation_axis,
                SCULPT_vertex_co_get(ss, boundary.pivot_vertex),
                SCULPT_vertex_co_get(ss, boundary.initial_vert));
    normalize_v3(boundary.twist.rotation_axis);
  }
}

static float displacement_from_grab_delta_get(SculptSession &ss, SculptBoundary &boundary)
{
  float plane[4];
  float pos[3];
  float normal[3];
  sub_v3_v3v3(normal, ss.cache->initial_location, boundary.initial_pivot_position);
  normalize_v3(normal);
  plane_from_point_normal_v3(plane, ss.cache->initial_location, normal);
  add_v3_v3v3(pos, ss.cache->initial_location, ss.cache->grab_delta_symmetry);
  return dist_signed_to_plane_v3(pos, plane);
}

static void boundary_brush_bend_task(Object &ob, const Brush &brush, PBVHNode *node)
{
  SculptSession &ss = *ob.sculpt;
  const int symm_area = ss.cache->mirror_symmetry_pass;
  SculptBoundary &boundary = *ss.cache->boundaries[symm_area];
  const ePaintSymmetryFlags symm = SCULPT_mesh_symmetry_xyz_get(ob);

  const float strength = ss.cache->bstrength;

  PBVHVertexIter vd;
  SculptOrigVertData orig_data = SCULPT_orig_vert_data_init(ob, *node, undo::Type::Position);

  const float disp = strength * displacement_from_grab_delta_get(ss, boundary);
  float angle_factor = disp / ss.cache->radius;
  /* Angle Snapping when inverting the brush. */
  if (ss.cache->invert) {
    angle_factor = floorf(angle_factor * 10) / 10.0f;
  }
  const float angle = angle_factor * M_PI;
  auto_mask::NodeData automask_data = auto_mask::node_begin(
      ob, ss.cache->automasking.get(), *node);

  BKE_pbvh_vertex_iter_begin (*ss.pbvh, node, vd, PBVH_ITER_UNIQUE) {
    if (boundary.edit_info[vd.index].propagation_steps_num == -1) {
      continue;
    }

    auto_mask::node_update(automask_data, vd);
    SCULPT_orig_vert_data_update(orig_data, vd);
    if (!SCULPT_check_vertex_pivot_symmetry(orig_data.co, boundary.initial_vert_position, symm)) {
      continue;
    }

    const float mask = 1.0f - vd.mask;
    const float automask = auto_mask::factor_get(
        ss.cache->automasking.get(), ss, vd.vertex, &automask_data);
    float t_orig_co[3];
    float *target_co = SCULPT_brush_deform_target_vertex_co_get(ss, brush.deform_target, &vd);
    sub_v3_v3v3(t_orig_co, orig_data.co, boundary.bend.pivot_positions[vd.index]);
    rotate_v3_v3v3fl(target_co,
                     t_orig_co,
                     boundary.bend.pivot_rotation_axis[vd.index],
                     angle * boundary.edit_info[vd.index].strength_factor * mask * automask);
    add_v3_v3(target_co, boundary.bend.pivot_positions[vd.index]);
  }
  BKE_pbvh_vertex_iter_end;
}

static void brush_slide_task(Object &ob, const Brush &brush, PBVHNode *node)
{
  SculptSession &ss = *ob.sculpt;
  const int symm_area = ss.cache->mirror_symmetry_pass;
  SculptBoundary &boundary = *ss.cache->boundaries[symm_area];
  const ePaintSymmetryFlags symm = SCULPT_mesh_symmetry_xyz_get(ob);

  const float strength = ss.cache->bstrength;

  PBVHVertexIter vd;
  SculptOrigVertData orig_data = SCULPT_orig_vert_data_init(ob, *node, undo::Type::Position);

  const float disp = displacement_from_grab_delta_get(ss, boundary);
  auto_mask::NodeData automask_data = auto_mask::node_begin(
      ob, ss.cache->automasking.get(), *node);

  BKE_pbvh_vertex_iter_begin (*ss.pbvh, node, vd, PBVH_ITER_UNIQUE) {
    if (boundary.edit_info[vd.index].propagation_steps_num == -1) {
      continue;
    }

    auto_mask::node_update(automask_data, vd);
    SCULPT_orig_vert_data_update(orig_data, vd);
    if (!SCULPT_check_vertex_pivot_symmetry(orig_data.co, boundary.initial_vert_position, symm)) {
      continue;
    }

    const float mask = 1.0f - vd.mask;
    const float automask = auto_mask::factor_get(
        ss.cache->automasking.get(), ss, vd.vertex, &automask_data);
    float *target_co = SCULPT_brush_deform_target_vertex_co_get(ss, brush.deform_target, &vd);
    madd_v3_v3v3fl(target_co,
                   orig_data.co,
                   boundary.slide.directions[vd.index],
                   boundary.edit_info[vd.index].strength_factor * disp * mask * automask *
                       strength);
  }
  BKE_pbvh_vertex_iter_end;
}

static void brush_inflate_task(Object &ob, const Brush &brush, PBVHNode *node)
{
  SculptSession &ss = *ob.sculpt;
  const int symm_area = ss.cache->mirror_symmetry_pass;
  SculptBoundary &boundary = *ss.cache->boundaries[symm_area];
  const ePaintSymmetryFlags symm = SCULPT_mesh_symmetry_xyz_get(ob);

  const float strength = ss.cache->bstrength;

  PBVHVertexIter vd;
  SculptOrigVertData orig_data = SCULPT_orig_vert_data_init(ob, *node, undo::Type::Position);
  auto_mask::NodeData automask_data = auto_mask::node_begin(
      ob, ss.cache->automasking.get(), *node);

  const float disp = displacement_from_grab_delta_get(ss, boundary);

  BKE_pbvh_vertex_iter_begin (*ss.pbvh, node, vd, PBVH_ITER_UNIQUE) {
    if (boundary.edit_info[vd.index].propagation_steps_num == -1) {
      continue;
    }

    auto_mask::node_update(automask_data, vd);
    SCULPT_orig_vert_data_update(orig_data, vd);
    if (!SCULPT_check_vertex_pivot_symmetry(orig_data.co, boundary.initial_vert_position, symm)) {
      continue;
    }

    const float mask = 1.0f - vd.mask;
    const float automask = auto_mask::factor_get(
        ss.cache->automasking.get(), ss, vd.vertex, &automask_data);
    float *target_co = SCULPT_brush_deform_target_vertex_co_get(ss, brush.deform_target, &vd);
    madd_v3_v3v3fl(target_co,
                   orig_data.co,
                   orig_data.no,
                   boundary.edit_info[vd.index].strength_factor * disp * mask * automask *
                       strength);
  }
  BKE_pbvh_vertex_iter_end;
}

static void brush_grab_task(Object &ob, const Brush &brush, PBVHNode *node)
{
  SculptSession &ss = *ob.sculpt;
  const int symm_area = ss.cache->mirror_symmetry_pass;
  SculptBoundary &boundary = *ss.cache->boundaries[symm_area];
  const ePaintSymmetryFlags symm = SCULPT_mesh_symmetry_xyz_get(ob);

  const float strength = ss.cache->bstrength;

  PBVHVertexIter vd;
  SculptOrigVertData orig_data = SCULPT_orig_vert_data_init(ob, *node, undo::Type::Position);
  auto_mask::NodeData automask_data = auto_mask::node_begin(
      ob, ss.cache->automasking.get(), *node);

  BKE_pbvh_vertex_iter_begin (*ss.pbvh, node, vd, PBVH_ITER_UNIQUE) {
    if (boundary.edit_info[vd.index].propagation_steps_num == -1) {
      continue;
    }

    auto_mask::node_update(automask_data, vd);
    SCULPT_orig_vert_data_update(orig_data, vd);
    if (!SCULPT_check_vertex_pivot_symmetry(orig_data.co, boundary.initial_vert_position, symm)) {
      continue;
    }

    const float mask = 1.0f - vd.mask;
    const float automask = auto_mask::factor_get(
        ss.cache->automasking.get(), ss, vd.vertex, &automask_data);
    float *target_co = SCULPT_brush_deform_target_vertex_co_get(ss, brush.deform_target, &vd);
    madd_v3_v3v3fl(target_co,
                   orig_data.co,
                   ss.cache->grab_delta_symmetry,
                   boundary.edit_info[vd.index].strength_factor * mask * automask * strength);
  }
  BKE_pbvh_vertex_iter_end;
}

static void brush_twist_task(Object &ob, const Brush &brush, PBVHNode *node)
{
  SculptSession &ss = *ob.sculpt;
  const int symm_area = ss.cache->mirror_symmetry_pass;
  SculptBoundary &boundary = *ss.cache->boundaries[symm_area];
  const ePaintSymmetryFlags symm = SCULPT_mesh_symmetry_xyz_get(ob);

  const float strength = ss.cache->bstrength;

  PBVHVertexIter vd;
  SculptOrigVertData orig_data = SCULPT_orig_vert_data_init(ob, *node, undo::Type::Position);
  auto_mask::NodeData automask_data = auto_mask::node_begin(
      ob, ss.cache->automasking.get(), *node);

  const float disp = strength * displacement_from_grab_delta_get(ss, boundary);
  float angle_factor = disp / ss.cache->radius;
  /* Angle Snapping when inverting the brush. */
  if (ss.cache->invert) {
    angle_factor = floorf(angle_factor * 10) / 10.0f;
  }
  const float angle = angle_factor * M_PI;

  BKE_pbvh_vertex_iter_begin (*ss.pbvh, node, vd, PBVH_ITER_UNIQUE) {
    if (boundary.edit_info[vd.index].propagation_steps_num == -1) {
      continue;
    }

    auto_mask::node_update(automask_data, vd);
    SCULPT_orig_vert_data_update(orig_data, vd);
    if (!SCULPT_check_vertex_pivot_symmetry(orig_data.co, boundary.initial_vert_position, symm)) {
      continue;
    }

    const float mask = 1.0f - vd.mask;
    const float automask = auto_mask::factor_get(
        ss.cache->automasking.get(), ss, vd.vertex, &automask_data);
    float t_orig_co[3];
    float *target_co = SCULPT_brush_deform_target_vertex_co_get(ss, brush.deform_target, &vd);
    sub_v3_v3v3(t_orig_co, orig_data.co, boundary.twist.pivot_position);
    rotate_v3_v3v3fl(target_co,
                     t_orig_co,
                     boundary.twist.rotation_axis,
                     angle * mask * automask * boundary.edit_info[vd.index].strength_factor);
    add_v3_v3(target_co, boundary.twist.pivot_position);
  }
  BKE_pbvh_vertex_iter_end;
}

static void brush_smooth_task(Object &ob, const Brush &brush, PBVHNode *node)
{
  SculptSession &ss = *ob.sculpt;
  const int symmetry_pass = ss.cache->mirror_symmetry_pass;
  const SculptBoundary &boundary = *ss.cache->boundaries[symmetry_pass];
  const ePaintSymmetryFlags symm = SCULPT_mesh_symmetry_xyz_get(ob);

  const float strength = ss.cache->bstrength;

  PBVHVertexIter vd;
  SculptOrigVertData orig_data = SCULPT_orig_vert_data_init(ob, *node, undo::Type::Position);

  BKE_pbvh_vertex_iter_begin (*ss.pbvh, node, vd, PBVH_ITER_UNIQUE) {
    if (boundary.edit_info[vd.index].propagation_steps_num == -1) {
      continue;
    }

    SCULPT_orig_vert_data_update(orig_data, vd);
    if (!SCULPT_check_vertex_pivot_symmetry(orig_data.co, boundary.initial_vert_position, symm)) {
      continue;
    }

    float coord_accum[3] = {0.0f, 0.0f, 0.0f};
    int total_neighbors = 0;
    const int current_propagation_steps = boundary.edit_info[vd.index].propagation_steps_num;
    SculptVertexNeighborIter ni;
    SCULPT_VERTEX_NEIGHBORS_ITER_BEGIN (ss, vd.vertex, ni) {
      if (current_propagation_steps == boundary.edit_info[ni.index].propagation_steps_num) {
        add_v3_v3(coord_accum, SCULPT_vertex_co_get(ss, ni.vertex));
        total_neighbors++;
      }
    }
    SCULPT_VERTEX_NEIGHBORS_ITER_END(ni);

    if (total_neighbors == 0) {
      continue;
    }
    float disp[3];
    float avg[3];
    const float mask = 1.0f - vd.mask;
    mul_v3_v3fl(avg, coord_accum, 1.0f / total_neighbors);
    sub_v3_v3v3(disp, avg, vd.co);
    float *target_co = SCULPT_brush_deform_target_vertex_co_get(ss, brush.deform_target, &vd);
    madd_v3_v3v3fl(
        target_co, vd.co, disp, boundary.edit_info[vd.index].strength_factor * mask * strength);
  }
  BKE_pbvh_vertex_iter_end;
}

void do_boundary_brush(const Sculpt &sd, Object &ob, Span<PBVHNode *> nodes)
{
  SculptSession &ss = *ob.sculpt;
  const Brush &brush = *BKE_paint_brush_for_read(&sd.paint);

  const ePaintSymmetryFlags symm_area = ss.cache->mirror_symmetry_pass;
  if (SCULPT_stroke_is_first_brush_step_of_symmetry_pass(*ss.cache)) {

    PBVHVertRef initial_vert;

    if (ss.cache->mirror_symmetry_pass == 0) {
      initial_vert = SCULPT_active_vertex_get(ss);
    }
    else {
      float location[3];
      flip_v3_v3(location, SCULPT_active_vertex_co_get(ss), symm_area);
      initial_vert = SCULPT_nearest_vertex_get(ob, location, ss.cache->radius_squared, false);
    }

    ss.cache->boundaries[symm_area] = data_init(
        ob, &brush, initial_vert, ss.cache->initial_radius);

    if (ss.cache->boundaries[symm_area]) {
      switch (brush.boundary_deform_type) {
        case BRUSH_BOUNDARY_DEFORM_BEND:
          bend_data_init(ss, *ss.cache->boundaries[symm_area]);
          break;
        case BRUSH_BOUNDARY_DEFORM_EXPAND:
          slide_data_init(ss, *ss.cache->boundaries[symm_area]);
          break;
        case BRUSH_BOUNDARY_DEFORM_TWIST:
          twist_data_init(ss, *ss.cache->boundaries[symm_area]);
          break;
        case BRUSH_BOUNDARY_DEFORM_INFLATE:
        case BRUSH_BOUNDARY_DEFORM_GRAB:
          /* Do nothing. These deform modes don't need any extra data to be precomputed. */
          break;
      }

      init_falloff(ss, *ss.cache->boundaries[symm_area], brush, ss.cache->initial_radius);
    }
  }

  /* No active boundary under the cursor. */
  if (!ss.cache->boundaries[symm_area]) {
    return;
  }

  switch (brush.boundary_deform_type) {
    case BRUSH_BOUNDARY_DEFORM_BEND:
      threading::parallel_for(nodes.index_range(), 1, [&](const IndexRange range) {
        for (const int i : range) {
          boundary_brush_bend_task(ob, brush, nodes[i]);
        }
      });
      break;
    case BRUSH_BOUNDARY_DEFORM_EXPAND:
      threading::parallel_for(nodes.index_range(), 1, [&](const IndexRange range) {
        for (const int i : range) {
          brush_slide_task(ob, brush, nodes[i]);
        }
      });
      break;
    case BRUSH_BOUNDARY_DEFORM_INFLATE:
      threading::parallel_for(nodes.index_range(), 1, [&](const IndexRange range) {
        for (const int i : range) {
          brush_inflate_task(ob, brush, nodes[i]);
        }
      });
      break;
    case BRUSH_BOUNDARY_DEFORM_GRAB:
      threading::parallel_for(nodes.index_range(), 1, [&](const IndexRange range) {
        for (const int i : range) {
          brush_grab_task(ob, brush, nodes[i]);
        }
      });
      break;
    case BRUSH_BOUNDARY_DEFORM_TWIST:
      threading::parallel_for(nodes.index_range(), 1, [&](const IndexRange range) {
        for (const int i : range) {
          brush_twist_task(ob, brush, nodes[i]);
        }
      });
      break;
    case BRUSH_BOUNDARY_DEFORM_SMOOTH:
      threading::parallel_for(nodes.index_range(), 1, [&](const IndexRange range) {
        for (const int i : range) {
          brush_smooth_task(ob, brush, nodes[i]);
        }
      });
      break;
  }
}

void edges_preview_draw(const uint gpuattr,
                        SculptSession &ss,
                        const float outline_col[3],
                        const float outline_alpha)
{
  if (!ss.boundary_preview) {
    return;
  }
  immUniformColor3fvAlpha(outline_col, outline_alpha);
  GPU_line_width(2.0f);
  immBegin(GPU_PRIM_LINES, ss.boundary_preview->edges.size() * 2);
  for (int i = 0; i < ss.boundary_preview->edges.size(); i++) {
    immVertex3fv(gpuattr, SCULPT_vertex_co_get(ss, ss.boundary_preview->edges[i].v1));
    immVertex3fv(gpuattr, SCULPT_vertex_co_get(ss, ss.boundary_preview->edges[i].v2));
  }
  immEnd();
}

void pivot_line_preview_draw(const uint gpuattr, SculptSession &ss)
{
  if (!ss.boundary_preview) {
    return;
  }
  immUniformColor4f(1.0f, 1.0f, 1.0f, 0.8f);
  GPU_line_width(2.0f);
  immBegin(GPU_PRIM_LINES, 2);
  immVertex3fv(gpuattr, SCULPT_vertex_co_get(ss, ss.boundary_preview->pivot_vertex));
  immVertex3fv(gpuattr, SCULPT_vertex_co_get(ss, ss.boundary_preview->initial_vert));
  immEnd();
}

}  // namespace blender::ed::sculpt_paint::boundary

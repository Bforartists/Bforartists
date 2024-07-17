/* SPDX-FileCopyrightText: 2024 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#include "editors/sculpt_paint/brushes/types.hh"

#include "DNA_brush_types.h"
#include "DNA_mesh_types.h"
#include "DNA_object_types.h"
#include "DNA_scene_types.h"

#include "BKE_key.hh"
#include "BKE_mesh.hh"
#include "BKE_paint.hh"
#include "BKE_pbvh.hh"
#include "BKE_subdiv_ccg.hh"

#include "BLI_array.hh"
#include "BLI_array_utils.hh"
#include "BLI_enumerable_thread_specific.hh"
#include "BLI_math_vector.hh"
#include "BLI_task.hh"

#include "editors/sculpt_paint/mesh_brush_common.hh"
#include "editors/sculpt_paint/sculpt_intern.hh"

namespace blender::ed::sculpt_paint {

inline namespace enhance_details_cc {

struct LocalData {
  Vector<float3> positions;
  Vector<float3> new_positions;
  Vector<float> factors;
  Vector<float> distances;
  Vector<Vector<int>> vert_neighbors;
  Vector<float3> translations;
};

static void calc_faces(const Sculpt &sd,
                       const Brush &brush,
                       const Span<float3> positions_eval,
                       const Span<float3> vert_normals,
                       const Span<float3> all_translations,
                       const float strength,
                       const PBVHNode &node,
                       Object &object,
                       LocalData &tls,
                       const MutableSpan<float3> positions_orig)
{
  SculptSession &ss = *object.sculpt;
  const StrokeCache &cache = *ss.cache;
  Mesh &mesh = *static_cast<Mesh *>(object.data);

  const Span<int> verts = bke::pbvh::node_unique_verts(node);

  tls.factors.reinitialize(verts.size());
  const MutableSpan<float> factors = tls.factors;
  fill_factor_from_hide_and_mask(mesh, verts, factors);
  filter_region_clip_factors(ss, positions_eval, verts, factors);
  if (brush.flag & BRUSH_FRONTFACE) {
    calc_front_face(cache.view_normal, vert_normals, verts, factors);
  }

  tls.distances.reinitialize(verts.size());
  const MutableSpan<float> distances = tls.distances;
  calc_brush_distances(
      ss, positions_eval, verts, eBrushFalloffShape(brush.falloff_shape), distances);
  filter_distances_with_radius(cache.radius, distances, factors);
  apply_hardness_to_distances(cache, distances);
  calc_brush_strength_factors(cache, brush, distances, factors);

  if (cache.automasking) {
    auto_mask::calc_vert_factors(object, *cache.automasking, node, verts, factors);
  }

  calc_brush_texture_factors(ss, brush, positions_eval, verts, factors);

  scale_factors(factors, strength);

  tls.translations.reinitialize(verts.size());
  const MutableSpan<float3> translations = tls.translations;
  array_utils::gather(all_translations, verts, translations);
  scale_translations(translations, factors);

  write_translations(sd, object, positions_eval, verts, translations, positions_orig);
}

static void calc_grids(const Sculpt &sd,
                       Object &object,
                       const Brush &brush,
                       const Span<float3> all_translations,
                       const float strength,
                       const PBVHNode &node,
                       LocalData &tls)
{
  SculptSession &ss = *object.sculpt;
  const StrokeCache &cache = *ss.cache;
  SubdivCCG &subdiv_ccg = *ss.subdiv_ccg;
  const CCGKey key = BKE_subdiv_ccg_key_top_level(subdiv_ccg);

  const Span<int> grids = bke::pbvh::node_grid_indices(node);
  const int grid_verts_num = grids.size() * key.grid_area;

  tls.positions.reinitialize(grid_verts_num);
  const MutableSpan<float3> positions = tls.positions;
  gather_grids_positions(subdiv_ccg, grids, positions);

  tls.factors.reinitialize(grid_verts_num);
  const MutableSpan<float> factors = tls.factors;
  fill_factor_from_hide_and_mask(subdiv_ccg, grids, factors);
  filter_region_clip_factors(ss, positions, factors);
  if (brush.flag & BRUSH_FRONTFACE) {
    calc_front_face(cache.view_normal, subdiv_ccg, grids, factors);
  }

  tls.distances.reinitialize(grid_verts_num);
  const MutableSpan<float> distances = tls.distances;
  calc_brush_distances(ss, positions, eBrushFalloffShape(brush.falloff_shape), distances);
  filter_distances_with_radius(cache.radius, distances, factors);
  apply_hardness_to_distances(cache, distances);
  calc_brush_strength_factors(cache, brush, distances, factors);

  if (cache.automasking) {
    auto_mask::calc_grids_factors(object, *cache.automasking, node, grids, factors);
  }

  calc_brush_texture_factors(ss, brush, positions, factors);

  scale_factors(factors, strength);

  tls.translations.reinitialize(grid_verts_num);
  const MutableSpan<float3> translations = tls.translations;
  gather_data_grids(subdiv_ccg, all_translations, grids, translations);
  scale_translations(translations, factors);

  clip_and_lock_translations(sd, ss, positions, translations);
  apply_translations(translations, grids, subdiv_ccg);
}

static void calc_bmesh(const Sculpt &sd,
                       Object &object,
                       const Brush &brush,
                       const Span<float3> all_translations,
                       const float strength,
                       PBVHNode &node,
                       LocalData &tls)
{
  SculptSession &ss = *object.sculpt;
  const StrokeCache &cache = *ss.cache;

  const Set<BMVert *, 0> &verts = BKE_pbvh_bmesh_node_unique_verts(&node);

  tls.positions.reinitialize(verts.size());
  const MutableSpan<float3> positions = tls.positions;
  gather_bmesh_positions(verts, positions);

  tls.factors.reinitialize(verts.size());
  const MutableSpan<float> factors = tls.factors;
  fill_factor_from_hide_and_mask(*ss.bm, verts, factors);
  filter_region_clip_factors(ss, positions, factors);
  if (brush.flag & BRUSH_FRONTFACE) {
    calc_front_face(cache.view_normal, verts, factors);
  }

  tls.distances.reinitialize(verts.size());
  const MutableSpan<float> distances = tls.distances;
  calc_brush_distances(ss, positions, eBrushFalloffShape(brush.falloff_shape), distances);
  filter_distances_with_radius(cache.radius, distances, factors);
  apply_hardness_to_distances(cache, distances);
  calc_brush_strength_factors(cache, brush, distances, factors);

  if (cache.automasking) {
    auto_mask::calc_vert_factors(object, *cache.automasking, node, verts, factors);
  }

  calc_brush_texture_factors(ss, brush, positions, factors);

  scale_factors(factors, strength);

  tls.translations.reinitialize(verts.size());
  const MutableSpan<float3> translations = tls.translations;
  gather_data_vert_bmesh(all_translations, verts, translations);
  scale_translations(translations, factors);

  clip_and_lock_translations(sd, ss, positions, translations);
  apply_translations(translations, verts);
}

static void calc_translations_faces(const Span<float3> vert_positions,
                                    const OffsetIndices<int> faces,
                                    const Span<int> corner_verts,
                                    const GroupedSpan<int> vert_to_face_map,
                                    const PBVHNode &node,
                                    LocalData &tls,
                                    const MutableSpan<float3> all_translations)
{
  const Span<int> verts = bke::pbvh::node_unique_verts(node);

  tls.vert_neighbors.reinitialize(verts.size());
  const MutableSpan<Vector<int>> neighbors = tls.vert_neighbors;
  calc_vert_neighbors(faces, corner_verts, vert_to_face_map, {}, verts, neighbors);

  tls.new_positions.reinitialize(verts.size());
  const MutableSpan<float3> new_positions = tls.new_positions;
  smooth::neighbor_position_average_mesh(vert_positions, verts, neighbors, new_positions);

  tls.translations.reinitialize(verts.size());
  const MutableSpan<float3> translations = tls.translations;
  translations_from_new_positions(new_positions, verts, vert_positions, translations);
  array_utils::scatter(translations.as_span(), verts, all_translations);
}

static void calc_translations_grids(const SubdivCCG &subdiv_ccg,
                                    const PBVHNode &node,
                                    LocalData &tls,
                                    const MutableSpan<float3> all_translations)
{
  const CCGKey key = BKE_subdiv_ccg_key_top_level(subdiv_ccg);

  const Span<int> grids = bke::pbvh::node_grid_indices(node);
  const int grid_verts_num = grids.size() * key.grid_area;

  tls.positions.reinitialize(grid_verts_num);
  const MutableSpan<float3> positions = tls.positions;
  gather_grids_positions(subdiv_ccg, grids, positions);

  tls.new_positions.reinitialize(grid_verts_num);
  const MutableSpan<float3> new_positions = tls.new_positions;
  smooth::neighbor_position_average_grids(subdiv_ccg, grids, new_positions);

  tls.translations.reinitialize(grid_verts_num);
  const MutableSpan<float3> translations = tls.translations;
  translations_from_new_positions(new_positions, positions, translations);
  scatter_data_grids(subdiv_ccg, translations.as_span(), grids, all_translations);
}

static void calc_translations_bmesh(PBVHNode &node,
                                    LocalData &tls,
                                    const MutableSpan<float3> all_translations)
{
  const Set<BMVert *, 0> &verts = BKE_pbvh_bmesh_node_unique_verts(&node);

  tls.positions.reinitialize(verts.size());
  const MutableSpan<float3> positions = tls.positions;
  gather_bmesh_positions(verts, positions);

  tls.new_positions.reinitialize(verts.size());
  const MutableSpan<float3> new_positions = tls.new_positions;
  smooth::neighbor_position_average_bmesh(verts, new_positions);

  tls.translations.reinitialize(verts.size());
  const MutableSpan<float3> translations = tls.translations;
  translations_from_new_positions(new_positions, positions, translations);
  scatter_data_vert_bmesh(translations.as_span(), verts, all_translations);
}

/**
 * The brush uses translations calculated at the beginning of the stroke. They can't be calculated
 * dynamically because changing positions will influence neighboring translations. However we can
 * reduce the cost in some cases by skipping initializing values for vertices in hidden or masked
 * nodes.
 */
static void precalc_translations(Object &object, const MutableSpan<float3> translations)
{
  SculptSession &ss = *object.sculpt;
  PBVH &pbvh = *ss.pbvh;

  Vector<PBVHNode *> effective_nodes = bke::pbvh::search_gather(
      pbvh, [&](PBVHNode &node) { return !node_fully_masked_or_hidden(node); });

  threading::EnumerableThreadSpecific<LocalData> all_tls;
  switch (BKE_pbvh_type(pbvh)) {
    case PBVH_FACES: {
      Mesh &mesh = *static_cast<Mesh *>(object.data);
      const Span<float3> positions_eval = BKE_pbvh_get_vert_positions(pbvh);
      const OffsetIndices faces = mesh.faces();
      const Span<int> corner_verts = mesh.corner_verts();
      threading::parallel_for(effective_nodes.index_range(), 1, [&](const IndexRange range) {
        LocalData &tls = all_tls.local();
        threading::isolate_task([&]() {
          for (const int i : range) {
            calc_translations_faces(positions_eval,
                                    faces,
                                    corner_verts,
                                    ss.vert_to_face_map,
                                    *effective_nodes[i],
                                    tls,
                                    translations);
          }
        });
      });
      break;
    }
    case PBVH_GRIDS: {
      SubdivCCG &subdiv_ccg = *ss.subdiv_ccg;
      threading::parallel_for(effective_nodes.index_range(), 1, [&](const IndexRange range) {
        LocalData &tls = all_tls.local();
        for (const int i : range) {
          calc_translations_grids(subdiv_ccg, *effective_nodes[i], tls, translations);
        }
      });
      break;
    }
    case PBVH_BMESH:
      BM_mesh_elem_index_ensure(ss.bm, BM_VERT);
      BM_mesh_elem_table_ensure(ss.bm, BM_VERT);
      threading::parallel_for(effective_nodes.index_range(), 1, [&](const IndexRange range) {
        LocalData &tls = all_tls.local();
        for (const int i : range) {
          calc_translations_bmesh(*effective_nodes[i], tls, translations);
        }
      });
      break;
  }
}

}  // namespace enhance_details_cc

void do_enhance_details_brush(const Sculpt &sd, Object &object, Span<PBVHNode *> nodes)
{
  SculptSession &ss = *object.sculpt;
  const Brush &brush = *BKE_paint_brush_for_read(&sd.paint);
  PBVH &pbvh = *ss.pbvh;

  if (SCULPT_stroke_is_first_brush_step(*ss.cache)) {
    ss.cache->detail_directions.reinitialize(SCULPT_vertex_count_get(ss));
    precalc_translations(object, ss.cache->detail_directions);
  }

  const float strength = std::clamp(ss.cache->bstrength, -1.0f, 1.0f);
  MutableSpan<float3> translations = ss.cache->detail_directions;

  threading::EnumerableThreadSpecific<LocalData> all_tls;
  switch (BKE_pbvh_type(pbvh)) {
    case PBVH_FACES: {
      Mesh &mesh = *static_cast<Mesh *>(object.data);
      const Span<float3> positions_eval = BKE_pbvh_get_vert_positions(pbvh);
      const Span<float3> vert_normals = BKE_pbvh_get_vert_normals(pbvh);
      MutableSpan<float3> positions_orig = mesh.vert_positions_for_write();
      threading::parallel_for(nodes.index_range(), 1, [&](const IndexRange range) {
        LocalData &tls = all_tls.local();
        threading::isolate_task([&]() {
          for (const int i : range) {
            calc_faces(sd,
                       brush,
                       positions_eval,
                       vert_normals,
                       translations,
                       strength,
                       *nodes[i],
                       object,
                       tls,
                       positions_orig);
            BKE_pbvh_node_mark_positions_update(nodes[i]);
          }
        });
      });
      break;
    }
    case PBVH_GRIDS:
      threading::parallel_for(nodes.index_range(), 1, [&](const IndexRange range) {
        LocalData &tls = all_tls.local();
        for (const int i : range) {
          calc_grids(sd, object, brush, translations, strength, *nodes[i], tls);
        }
      });
      break;
    case PBVH_BMESH:
      threading::parallel_for(nodes.index_range(), 1, [&](const IndexRange range) {
        LocalData &tls = all_tls.local();
        for (const int i : range) {
          calc_bmesh(sd, object, brush, translations, strength, *nodes[i], tls);
        }
      });
      break;
  }
}

}  // namespace blender::ed::sculpt_paint

/* SPDX-FileCopyrightText: 2024 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#include "editors/sculpt_paint/brushes/types.hh"

#include "DNA_brush_types.h"
#include "DNA_mesh_types.h"
#include "DNA_object_types.h"
#include "DNA_scene_types.h"

#include "BKE_mesh.hh"
#include "BKE_paint.hh"
#include "BKE_pbvh.hh"
#include "BKE_subdiv_ccg.hh"

#include "BLI_array.hh"
#include "BLI_enumerable_thread_specific.hh"
#include "BLI_task.hh"

#include "editors/sculpt_paint/mesh_brush_common.hh"
#include "editors/sculpt_paint/sculpt_intern.hh"
#include "editors/sculpt_paint/sculpt_smooth.hh"

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

static void calc_faces(const Depsgraph &depsgraph,
                       const Sculpt &sd,
                       const Brush &brush,
                       const Span<float3> positions_eval,
                       const Span<float3> vert_normals,
                       const Span<float3> all_translations,
                       const float strength,
                       const bke::pbvh::MeshNode &node,
                       Object &object,
                       LocalData &tls,
                       const MutableSpan<float3> positions_orig)
{
  SculptSession &ss = *object.sculpt;
  const StrokeCache &cache = *ss.cache;
  Mesh &mesh = *static_cast<Mesh *>(object.data);

  const Span<int> verts = node.verts();

  tls.factors.resize(verts.size());
  const MutableSpan<float> factors = tls.factors;
  fill_factor_from_hide_and_mask(mesh, verts, factors);
  filter_region_clip_factors(ss, positions_eval, verts, factors);
  if (brush.flag & BRUSH_FRONTFACE) {
    calc_front_face(cache.view_normal_symm, vert_normals, verts, factors);
  }

  tls.distances.resize(verts.size());
  const MutableSpan<float> distances = tls.distances;
  calc_brush_distances(
      ss, positions_eval, verts, eBrushFalloffShape(brush.falloff_shape), distances);
  filter_distances_with_radius(cache.radius, distances, factors);
  apply_hardness_to_distances(cache, distances);
  calc_brush_strength_factors(cache, brush, distances, factors);

  auto_mask::calc_vert_factors(depsgraph, object, cache.automasking.get(), node, verts, factors);

  calc_brush_texture_factors(ss, brush, positions_eval, verts, factors);

  scale_factors(factors, strength);

  tls.translations.resize(verts.size());
  const MutableSpan<float3> translations = tls.translations;
  gather_data_mesh(all_translations, verts, translations);
  scale_translations(translations, factors);

  write_translations(depsgraph, sd, object, positions_eval, verts, translations, positions_orig);
}

static void calc_grids(const Depsgraph &depsgraph,
                       const Sculpt &sd,
                       Object &object,
                       const Brush &brush,
                       const Span<float3> all_translations,
                       const float strength,
                       const bke::pbvh::GridsNode &node,
                       LocalData &tls)
{
  SculptSession &ss = *object.sculpt;
  const StrokeCache &cache = *ss.cache;
  SubdivCCG &subdiv_ccg = *ss.subdiv_ccg;

  const Span<int> grids = node.grids();
  const MutableSpan positions = gather_grids_positions(subdiv_ccg, grids, tls.positions);

  tls.factors.resize(positions.size());
  const MutableSpan<float> factors = tls.factors;
  fill_factor_from_hide_and_mask(subdiv_ccg, grids, factors);
  filter_region_clip_factors(ss, positions, factors);
  if (brush.flag & BRUSH_FRONTFACE) {
    calc_front_face(cache.view_normal_symm, subdiv_ccg, grids, factors);
  }

  tls.distances.resize(positions.size());
  const MutableSpan<float> distances = tls.distances;
  calc_brush_distances(ss, positions, eBrushFalloffShape(brush.falloff_shape), distances);
  filter_distances_with_radius(cache.radius, distances, factors);
  apply_hardness_to_distances(cache, distances);
  calc_brush_strength_factors(cache, brush, distances, factors);

  auto_mask::calc_grids_factors(depsgraph, object, cache.automasking.get(), node, grids, factors);

  calc_brush_texture_factors(ss, brush, positions, factors);

  scale_factors(factors, strength);

  const MutableSpan<float3> translations = gather_data_grids(
      subdiv_ccg, all_translations, grids, tls.translations);
  scale_translations(translations, factors);

  clip_and_lock_translations(sd, ss, positions, translations);
  apply_translations(translations, grids, subdiv_ccg);
}

static void calc_bmesh(const Depsgraph &depsgraph,
                       const Sculpt &sd,
                       Object &object,
                       const Brush &brush,
                       const Span<float3> all_translations,
                       const float strength,
                       bke::pbvh::BMeshNode &node,
                       LocalData &tls)
{
  SculptSession &ss = *object.sculpt;
  const StrokeCache &cache = *ss.cache;

  const Set<BMVert *, 0> &verts = BKE_pbvh_bmesh_node_unique_verts(&node);
  const MutableSpan positions = gather_bmesh_positions(verts, tls.positions);

  tls.factors.resize(verts.size());
  const MutableSpan<float> factors = tls.factors;
  fill_factor_from_hide_and_mask(*ss.bm, verts, factors);
  filter_region_clip_factors(ss, positions, factors);
  if (brush.flag & BRUSH_FRONTFACE) {
    calc_front_face(cache.view_normal_symm, verts, factors);
  }

  tls.distances.resize(verts.size());
  const MutableSpan<float> distances = tls.distances;
  calc_brush_distances(ss, positions, eBrushFalloffShape(brush.falloff_shape), distances);
  filter_distances_with_radius(cache.radius, distances, factors);
  apply_hardness_to_distances(cache, distances);
  calc_brush_strength_factors(cache, brush, distances, factors);

  auto_mask::calc_vert_factors(depsgraph, object, cache.automasking.get(), node, verts, factors);

  calc_brush_texture_factors(ss, brush, positions, factors);

  scale_factors(factors, strength);

  const MutableSpan translations = gather_data_bmesh(all_translations, verts, tls.translations);
  scale_translations(translations, factors);

  clip_and_lock_translations(sd, ss, positions, translations);
  apply_translations(translations, verts);
}

static void calc_translations_faces(const Span<float3> vert_positions,
                                    const OffsetIndices<int> faces,
                                    const Span<int> corner_verts,
                                    const GroupedSpan<int> vert_to_face_map,
                                    const bke::pbvh::MeshNode &node,
                                    LocalData &tls,
                                    const MutableSpan<float3> all_translations)
{
  const Span<int> verts = node.verts();

  tls.vert_neighbors.resize(verts.size());
  const MutableSpan<Vector<int>> neighbors = tls.vert_neighbors;
  calc_vert_neighbors(faces, corner_verts, vert_to_face_map, {}, verts, neighbors);

  tls.new_positions.resize(verts.size());
  const MutableSpan<float3> new_positions = tls.new_positions;
  smooth::neighbor_data_average_mesh(vert_positions, neighbors, new_positions);

  tls.translations.resize(verts.size());
  const MutableSpan<float3> translations = tls.translations;
  translations_from_new_positions(new_positions, verts, vert_positions, translations);
  scatter_data_mesh(translations.as_span(), verts, all_translations);
}

static void calc_translations_grids(const SubdivCCG &subdiv_ccg,
                                    const bke::pbvh::GridsNode &node,
                                    LocalData &tls,
                                    const MutableSpan<float3> all_translations)
{
  const Span<int> grids = node.grids();
  const MutableSpan positions = gather_grids_positions(subdiv_ccg, grids, tls.positions);

  tls.new_positions.resize(positions.size());
  const MutableSpan<float3> new_positions = tls.new_positions;
  smooth::neighbor_position_average_grids(subdiv_ccg, grids, new_positions);

  tls.translations.resize(positions.size());
  const MutableSpan<float3> translations = tls.translations;
  translations_from_new_positions(new_positions, positions, translations);
  scatter_data_grids(subdiv_ccg, translations.as_span(), grids, all_translations);
}

static void calc_translations_bmesh(const bke::pbvh::BMeshNode &node,
                                    LocalData &tls,
                                    const MutableSpan<float3> all_translations)
{
  const Set<BMVert *, 0> &verts = BKE_pbvh_bmesh_node_unique_verts(
      const_cast<bke::pbvh::BMeshNode *>(&node));
  const MutableSpan positions = gather_bmesh_positions(verts, tls.positions);

  tls.new_positions.resize(verts.size());
  const MutableSpan<float3> new_positions = tls.new_positions;
  smooth::neighbor_position_average_bmesh(verts, new_positions);

  tls.translations.resize(verts.size());
  const MutableSpan<float3> translations = tls.translations;
  translations_from_new_positions(new_positions, positions, translations);
  scatter_data_bmesh(translations.as_span(), verts, all_translations);
}

}  // namespace enhance_details_cc

/**
 * The brush uses translations calculated at the beginning of the stroke. They can't be calculated
 * dynamically because changing positions will influence neighboring translations. However we can
 * reduce the cost in some cases by skipping initializing values for vertices in hidden or masked
 * nodes.
 */
void calc_smooth_translations(const Depsgraph &depsgraph,
                              const Object &object,
                              const IndexMask &node_mask,
                              const MutableSpan<float3> translations)
{
  const SculptSession &ss = *object.sculpt;
  const bke::pbvh::Tree &pbvh = *bke::object::pbvh_get(object);

  threading::EnumerableThreadSpecific<LocalData> all_tls;
  switch (pbvh.type()) {
    case bke::pbvh::Type::Mesh: {
      Mesh &mesh = *static_cast<Mesh *>(object.data);
      const Span<float3> positions_eval = bke::pbvh::vert_positions_eval(depsgraph, object);
      const OffsetIndices faces = mesh.faces();
      const Span<int> corner_verts = mesh.corner_verts();
      const Span<bke::pbvh::MeshNode> nodes = pbvh.nodes<bke::pbvh::MeshNode>();
      threading::parallel_for(node_mask.index_range(), 1, [&](const IndexRange range) {
        LocalData &tls = all_tls.local();
        node_mask.slice(range).foreach_index([&](const int i) {
          calc_translations_faces(positions_eval,
                                  faces,
                                  corner_verts,
                                  ss.vert_to_face_map,
                                  nodes[i],
                                  tls,
                                  translations);
        });
      });
      break;
    }
    case bke::pbvh::Type::Grids: {
      SubdivCCG &subdiv_ccg = *ss.subdiv_ccg;
      const Span<bke::pbvh::GridsNode> nodes = pbvh.nodes<bke::pbvh::GridsNode>();
      threading::parallel_for(node_mask.index_range(), 1, [&](const IndexRange range) {
        LocalData &tls = all_tls.local();
        node_mask.slice(range).foreach_index([&](const int i) {
          calc_translations_grids(subdiv_ccg, nodes[i], tls, translations);
        });
      });
      break;
    }
    case bke::pbvh::Type::BMesh:
      BM_mesh_elem_index_ensure(ss.bm, BM_VERT);
      BM_mesh_elem_table_ensure(ss.bm, BM_VERT);
      const Span<bke::pbvh::BMeshNode> nodes = pbvh.nodes<bke::pbvh::BMeshNode>();
      threading::parallel_for(node_mask.index_range(), 1, [&](const IndexRange range) {
        LocalData &tls = all_tls.local();
        node_mask.slice(range).foreach_index(
            [&](const int i) { calc_translations_bmesh(nodes[i], tls, translations); });
      });
      break;
  }
}

void do_enhance_details_brush(const Depsgraph &depsgraph,
                              const Sculpt &sd,
                              Object &object,
                              const IndexMask &node_mask)
{
  SculptSession &ss = *object.sculpt;
  const Brush &brush = *BKE_paint_brush_for_read(&sd.paint);
  bke::pbvh::Tree &pbvh = *bke::object::pbvh_get(object);

  if (SCULPT_stroke_is_first_brush_step(*ss.cache)) {
    ss.cache->detail_directions.reinitialize(SCULPT_vertex_count_get(object));
    IndexMaskMemory memory;
    const IndexMask effective_nodes = bke::pbvh::search_nodes(
        pbvh, memory, [&](const bke::pbvh::Node &node) {
          return !node_fully_masked_or_hidden(node);
        });
    calc_smooth_translations(depsgraph, object, effective_nodes, ss.cache->detail_directions);
  }

  const float strength = std::clamp(ss.cache->bstrength, -1.0f, 1.0f);
  MutableSpan<float3> translations = ss.cache->detail_directions;

  threading::EnumerableThreadSpecific<LocalData> all_tls;
  switch (pbvh.type()) {
    case bke::pbvh::Type::Mesh: {
      Mesh &mesh = *static_cast<Mesh *>(object.data);
      const Span<float3> positions_eval = bke::pbvh::vert_positions_eval(depsgraph, object);
      const Span<float3> vert_normals = bke::pbvh::vert_normals_eval(depsgraph, object);
      MutableSpan<float3> positions_orig = mesh.vert_positions_for_write();
      MutableSpan<bke::pbvh::MeshNode> nodes = pbvh.nodes<bke::pbvh::MeshNode>();
      threading::parallel_for(node_mask.index_range(), 1, [&](const IndexRange range) {
        LocalData &tls = all_tls.local();
        node_mask.slice(range).foreach_index([&](const int i) {
          calc_faces(depsgraph,
                     sd,
                     brush,
                     positions_eval,
                     vert_normals,
                     translations,
                     strength,
                     nodes[i],
                     object,
                     tls,
                     positions_orig);
          BKE_pbvh_node_mark_positions_update(nodes[i]);
        });
      });
      break;
    }
    case bke::pbvh::Type::Grids: {
      MutableSpan<bke::pbvh::GridsNode> nodes = pbvh.nodes<bke::pbvh::GridsNode>();
      threading::parallel_for(node_mask.index_range(), 1, [&](const IndexRange range) {
        LocalData &tls = all_tls.local();
        node_mask.slice(range).foreach_index([&](const int i) {
          calc_grids(depsgraph, sd, object, brush, translations, strength, nodes[i], tls);
        });
      });
      break;
    }
    case bke::pbvh::Type::BMesh: {
      MutableSpan<bke::pbvh::BMeshNode> nodes = pbvh.nodes<bke::pbvh::BMeshNode>();
      threading::parallel_for(node_mask.index_range(), 1, [&](const IndexRange range) {
        LocalData &tls = all_tls.local();
        node_mask.slice(range).foreach_index([&](const int i) {
          calc_bmesh(depsgraph, sd, object, brush, translations, strength, nodes[i], tls);
        });
      });
      break;
    }
  }
}

}  // namespace blender::ed::sculpt_paint

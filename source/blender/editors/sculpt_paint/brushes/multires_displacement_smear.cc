/* SPDX-FileCopyrightText: 2024 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#include "editors/sculpt_paint/brushes/types.hh"

#include "DNA_brush_types.h"
#include "DNA_mesh_types.h"
#include "DNA_object_types.h"
#include "DNA_scene_types.h"

#include "BKE_paint.hh"
#include "BKE_pbvh.hh"
#include "BKE_subdiv_ccg.hh"

#include "BLI_enumerable_thread_specific.hh"
#include "BLI_math_matrix.hh"
#include "BLI_math_vector.h"
#include "BLI_math_vector.hh"
#include "BLI_task.h"
#include "BLI_task.hh"

#include "editors/sculpt_paint/mesh_brush_common.hh"
#include "editors/sculpt_paint/sculpt_intern.hh"

namespace blender::ed::sculpt_paint {

inline namespace multires_displacement_smear_cc {

struct LocalData {
  Vector<float3> positions;
  Vector<float> factors;
  Vector<float> distances;
};

static void calc_node(const Depsgraph &depsgraph,
                      Object &object,
                      const Brush &brush,
                      const float strength,
                      const bke::pbvh::GridsNode &node,
                      LocalData &tls)
{
  SculptSession &ss = *object.sculpt;
  const StrokeCache &cache = *ss.cache;
  SubdivCCG &subdiv_ccg = *ss.subdiv_ccg;
  const Span<CCGElem *> elems = subdiv_ccg.grids;
  const CCGKey key = BKE_subdiv_ccg_key_top_level(subdiv_ccg);

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

  for (const int i : grids.index_range()) {
    const int node_start = i * key.grid_area;
    const int grid = grids[i];
    const int start = grid * key.grid_area;
    CCGElem *elem = elems[grid];
    for (const int y : IndexRange(key.grid_size)) {
      for (const int x : IndexRange(key.grid_size)) {
        const int offset = CCG_grid_xy_to_index(key.grid_size, x, y);
        const int node_vert_index = node_start + offset;
        const int grid_vert_index = start + offset;

        float3 interp_limit_surface_disp =
            cache.displacement_smear.prev_displacement[grid_vert_index];

        float3 current_disp;
        switch (brush.smear_deform_type) {
          case BRUSH_SMEAR_DEFORM_DRAG:
            current_disp = cache.location_symm - cache.last_location_symm;
            break;
          case BRUSH_SMEAR_DEFORM_PINCH:
            current_disp = cache.location_symm - positions[node_vert_index];
            break;
          case BRUSH_SMEAR_DEFORM_EXPAND:
            current_disp = positions[node_vert_index] - cache.location_symm;
            break;
        }

        const float3 current_disp_norm = math::normalize(current_disp);
        current_disp *= cache.bstrength;

        float weights_accum = 1.0f;

        SubdivCCGCoord coord{};
        coord.grid_index = grid;
        coord.x = x;
        coord.y = y;

        SubdivCCGNeighbors neighbors;
        BKE_subdiv_ccg_neighbor_coords_get(*ss.subdiv_ccg, coord, false, neighbors);

        for (const SubdivCCGCoord neighbor : neighbors.coords) {
          const int neighbor_grid_vert_index = neighbor.grid_index * key.grid_area +
                                               CCG_grid_xy_to_index(
                                                   key.grid_size, neighbor.x, neighbor.y);
          const float3 vert_disp =
              cache.displacement_smear.limit_surface_co[neighbor_grid_vert_index] -
              cache.displacement_smear.limit_surface_co[grid_vert_index];
          const float3 &neighbor_limit_surface_disp =
              cache.displacement_smear.prev_displacement[neighbor_grid_vert_index];
          const float3 vert_disp_norm = math::normalize(vert_disp);

          if (math::dot(current_disp_norm, vert_disp_norm) >= 0.0f) {
            continue;
          }

          const float disp_interp = std::clamp(
              -math::dot(current_disp_norm, vert_disp_norm), 0.0f, 1.0f);
          interp_limit_surface_disp += neighbor_limit_surface_disp * disp_interp;
          weights_accum += disp_interp;
        }

        interp_limit_surface_disp *= math::rcp(weights_accum);

        float3 new_co = cache.displacement_smear.limit_surface_co[grid_vert_index] +
                        interp_limit_surface_disp;
        CCG_elem_offset_co(key, elem, offset) = math::interpolate(
            positions[node_vert_index], new_co, factors[node_vert_index]);
      }
    }
  }
}

BLI_NOINLINE static void eval_all_limit_positions(const SubdivCCG &subdiv_ccg,
                                                  const MutableSpan<float3> limit_positions)
{
  const CCGKey key = BKE_subdiv_ccg_key_top_level(subdiv_ccg);
  threading::parallel_for(subdiv_ccg.grids.index_range(), 1024, [&](const IndexRange range) {
    for (const int grid : range) {
      const MutableSpan grid_limit_positions = limit_positions.slice(grid * key.grid_area,
                                                                     key.grid_area);
      BKE_subdiv_ccg_eval_limit_positions(subdiv_ccg, key, grid, grid_limit_positions);
    }
  });
}

BLI_NOINLINE static void store_node_prev_displacement(const Span<float3> limit_positions,
                                                      const Span<CCGElem *> elems,
                                                      const CCGKey &key,
                                                      const bke::pbvh::GridsNode &node,
                                                      const MutableSpan<float3> prev_displacement)
{
  for (const int grid : node.grids()) {
    const int start = grid * key.grid_area;
    CCGElem *elem = elems[grid];
    for (const int i : IndexRange(key.grid_area)) {
      prev_displacement[start + i] = CCG_elem_offset_co(key, elem, i) - limit_positions[start + i];
    }
  }
}

}  // namespace multires_displacement_smear_cc

void do_displacement_smear_brush(const Depsgraph &depsgraph,
                                 const Sculpt &sd,
                                 Object &ob,
                                 const IndexMask &node_mask)
{
  const Brush &brush = *BKE_paint_brush_for_read(&sd.paint);
  SculptSession &ss = *ob.sculpt;
  bke::pbvh::Tree &pbvh = *bke::object::pbvh_get(ob);
  MutableSpan<bke::pbvh::GridsNode> nodes = pbvh.nodes<bke::pbvh::GridsNode>();

  SubdivCCG &subdiv_ccg = *ss.subdiv_ccg;
  const Span<CCGElem *> elems = subdiv_ccg.grids;
  const CCGKey key = BKE_subdiv_ccg_key_top_level(subdiv_ccg);

  if (ss.cache->displacement_smear.limit_surface_co.is_empty()) {
    ss.cache->displacement_smear.prev_displacement = Array<float3>(elems.size() * key.grid_area);
    ss.cache->displacement_smear.limit_surface_co = Array<float3>(elems.size() * key.grid_area);

    eval_all_limit_positions(subdiv_ccg, ss.cache->displacement_smear.limit_surface_co);
  }

  threading::parallel_for(node_mask.index_range(), 1, [&](const IndexRange range) {
    node_mask.slice(range).foreach_index([&](const int i) {
      store_node_prev_displacement(ss.cache->displacement_smear.limit_surface_co,
                                   elems,
                                   key,
                                   nodes[i],
                                   ss.cache->displacement_smear.prev_displacement);
    });
  });

  const float strength = std::clamp(ss.cache->bstrength, 0.0f, 1.0f);

  threading::EnumerableThreadSpecific<LocalData> all_tls;
  threading::parallel_for(node_mask.index_range(), 1, [&](const IndexRange range) {
    LocalData &tls = all_tls.local();
    node_mask.slice(range).foreach_index(
        [&](const int i) { calc_node(depsgraph, ob, brush, strength, nodes[i], tls); });
  });
}

}  // namespace blender::ed::sculpt_paint

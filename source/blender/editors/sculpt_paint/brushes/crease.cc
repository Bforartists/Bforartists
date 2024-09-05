/* SPDX-FileCopyrightText: 2024 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#include "editors/sculpt_paint/brushes/types.hh"

#include "DNA_brush_types.h"
#include "DNA_mesh_types.h"
#include "DNA_object_types.h"
#include "DNA_scene_types.h"

#include "BKE_brush.hh"
#include "BKE_key.hh"
#include "BKE_mesh.hh"
#include "BKE_paint.hh"
#include "BKE_pbvh.hh"
#include "BKE_subdiv_ccg.hh"

#include "BLI_array.hh"
#include "BLI_enumerable_thread_specific.hh"
#include "BLI_math_geom.h"
#include "BLI_math_matrix.hh"
#include "BLI_math_vector.hh"
#include "BLI_task.h"
#include "BLI_task.hh"

#include "editors/sculpt_paint/mesh_brush_common.hh"
#include "editors/sculpt_paint/sculpt_intern.hh"

namespace blender::ed::sculpt_paint {

inline namespace crease_cc {

struct LocalData {
  Vector<float3> positions;
  Vector<float> factors;
  Vector<float> distances;
  Vector<float3> translations;
};

BLI_NOINLINE static void translations_from_position(const Span<float3> positions_eval,
                                                    const Span<int> verts,
                                                    const float3 &location,
                                                    const MutableSpan<float3> translations)
{
  for (const int i : verts.index_range()) {
    translations[i] = location - positions_eval[verts[i]];
  }
}

BLI_NOINLINE static void translations_from_position(const Span<float3> positions,
                                                    const float3 &location,
                                                    const MutableSpan<float3> translations)
{
  for (const int i : positions.index_range()) {
    translations[i] = location - positions[i];
  }
}

BLI_NOINLINE static void add_offset_to_translations(const MutableSpan<float3> translations,
                                                    const Span<float> factors,
                                                    const float3 &offset)
{
  for (const int i : translations.index_range()) {
    translations[i] += offset * factors[i];
  }
}

static void calc_faces(const Depsgraph &depsgraph,
                       const Sculpt &sd,
                       const Brush &brush,
                       const float3 &offset,
                       const float strength,
                       const Span<float3> positions_eval,
                       const Span<float3> vert_normals,
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

  tls.translations.resize(verts.size());
  const MutableSpan<float3> translations = tls.translations;
  translations_from_position(positions_eval, verts, cache.location_symm, translations);

  if (brush.falloff_shape == PAINT_FALLOFF_SHAPE_TUBE) {
    project_translations(translations, cache.view_normal_symm);
  }

  scale_translations(translations, factors);
  scale_translations(translations, strength);

  /* The vertices are pinched towards a line instead of a single point. Without this we get a
   * 'flat' surface surrounding the pinch. */
  project_translations(translations, cache.sculpt_normal_symm);

  add_offset_to_translations(translations, factors, offset);

  write_translations(depsgraph, sd, object, positions_eval, verts, translations, positions_orig);
}

static void calc_grids(const Depsgraph &depsgraph,
                       const Sculpt &sd,
                       Object &object,
                       const Brush &brush,
                       const float3 &offset,
                       const float strength,
                       bke::pbvh::GridsNode &node,
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

  tls.translations.resize(positions.size());
  const MutableSpan<float3> translations = tls.translations;
  translations_from_position(positions, cache.location_symm, translations);

  if (brush.falloff_shape == PAINT_FALLOFF_SHAPE_TUBE) {
    project_translations(translations, cache.view_normal_symm);
  }

  scale_translations(translations, factors);
  scale_translations(translations, strength);

  project_translations(translations, cache.sculpt_normal_symm);

  add_offset_to_translations(translations, factors, offset);

  clip_and_lock_translations(sd, ss, positions, translations);
  apply_translations(translations, grids, subdiv_ccg);
}

static void calc_bmesh(const Depsgraph &depsgraph,
                       const Sculpt &sd,
                       Object &object,
                       const Brush &brush,
                       const float3 &offset,
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

  tls.translations.resize(verts.size());
  const MutableSpan<float3> translations = tls.translations;
  translations_from_position(positions, cache.location_symm, translations);

  if (brush.falloff_shape == PAINT_FALLOFF_SHAPE_TUBE) {
    project_translations(translations, cache.view_normal_symm);
  }

  scale_translations(translations, factors);
  scale_translations(translations, strength);

  project_translations(translations, cache.sculpt_normal_symm);

  add_offset_to_translations(translations, factors, offset);

  clip_and_lock_translations(sd, ss, positions, translations);
  apply_translations(translations, verts);
}

static void do_crease_or_blob_brush(const Depsgraph &depsgraph,
                                    const Scene &scene,
                                    const Sculpt &sd,
                                    const bool invert_strength,
                                    Object &object,
                                    const IndexMask &node_mask)
{
  const SculptSession &ss = *object.sculpt;
  bke::pbvh::Tree &pbvh = *bke::object::pbvh_get(object);
  const StrokeCache &cache = *ss.cache;
  const Brush &brush = *BKE_paint_brush_for_read(&sd.paint);

  /* Offset with as much as possible factored in already. */
  const float3 offset = cache.sculpt_normal_symm * cache.scale * cache.radius * cache.bstrength;

  /* We divide out the squared alpha and multiply by the squared crease
   * to give us the pinch strength. */
  float crease_correction = brush.crease_pinch_factor * brush.crease_pinch_factor;
  float brush_alpha = BKE_brush_alpha_get(&scene, &brush);
  if (brush_alpha > 0.0f) {
    crease_correction /= brush_alpha * brush_alpha;
  }

  /* We always want crease to pinch or blob to relax even when draw is negative. */
  const float strength = std::abs(cache.bstrength) * crease_correction *
                         (invert_strength ? -1.0f : 1.0f);

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
                     offset,
                     strength,
                     positions_eval,
                     vert_normals,
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
          calc_grids(depsgraph, sd, object, brush, offset, strength, nodes[i], tls);
        });
      });
      break;
    }
    case bke::pbvh::Type::BMesh: {
      MutableSpan<bke::pbvh::BMeshNode> nodes = pbvh.nodes<bke::pbvh::BMeshNode>();
      threading::parallel_for(node_mask.index_range(), 1, [&](const IndexRange range) {
        LocalData &tls = all_tls.local();
        node_mask.slice(range).foreach_index([&](const int i) {
          calc_bmesh(depsgraph, sd, object, brush, offset, strength, nodes[i], tls);
        });
      });
      break;
    }
  }
}

}  // namespace crease_cc

void do_crease_brush(const Depsgraph &depsgraph,
                     const Scene &scene,
                     const Sculpt &sd,
                     Object &object,
                     const IndexMask &node_mask)
{
  do_crease_or_blob_brush(depsgraph, scene, sd, false, object, node_mask);
}

void do_blob_brush(const Depsgraph &depsgraph,
                   const Scene &scene,
                   const Sculpt &sd,
                   Object &object,
                   const IndexMask &node_mask)
{
  do_crease_or_blob_brush(depsgraph, scene, sd, true, object, node_mask);
}

}  // namespace blender::ed::sculpt_paint

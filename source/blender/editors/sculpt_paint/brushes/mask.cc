/* SPDX-FileCopyrightText: 2024 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#include "editors/sculpt_paint/brushes/types.hh"

#include "DNA_brush_types.h"
#include "DNA_mesh_types.h"
#include "DNA_object_types.h"
#include "DNA_scene_types.h"

#include "BKE_pbvh.hh"
#include "BKE_subdiv_ccg.hh"

#include "BLI_array.hh"
#include "BLI_array_utils.hh"
#include "BLI_enumerable_thread_specific.hh"
#include "BLI_math_vector.hh"
#include "BLI_span.hh"
#include "BLI_task.h"

#include "editors/sculpt_paint/mesh_brush_common.hh"
#include "editors/sculpt_paint/sculpt_intern.hh"

namespace blender::ed::sculpt_paint {
inline namespace mask_cc {

struct LocalData {
  Vector<float3> positions;
  Vector<float> factors;
  Vector<float> distances;
  Vector<float> current_masks;
  Vector<float> new_masks;
};

BLI_NOINLINE static void invert_mask(const MutableSpan<float> masks)
{
  for (float &mask : masks) {
    mask = 1.0f - mask;
  }
}

BLI_NOINLINE static void apply_factors(const float strength,
                                       const Span<float> current_masks,
                                       const Span<float> factors,
                                       const MutableSpan<float> masks)
{
  BLI_assert(current_masks.size() == masks.size());
  BLI_assert(factors.size() == masks.size());
  for (const int i : masks.index_range()) {
    masks[i] += factors[i] * current_masks[i] * strength;
  }
}

BLI_NOINLINE static void clamp_mask(const MutableSpan<float> masks)
{
  for (float &mask : masks) {
    mask = std::clamp(mask, 0.0f, 1.0f);
  }
}

static void calc_faces(const Brush &brush,
                       const float strength,
                       const Span<float3> positions,
                       const Span<float3> vert_normals,
                       const PBVHNode &node,
                       Object &object,
                       Mesh &mesh,
                       LocalData &tls,
                       const MutableSpan<float> mask)
{
  SculptSession &ss = *object.sculpt;
  const StrokeCache &cache = *ss.cache;

  const Span<int> verts = bke::pbvh::node_unique_verts(node);

  tls.factors.reinitialize(verts.size());
  const MutableSpan<float> factors = tls.factors;
  fill_factor_from_hide(mesh, verts, factors);
  filter_region_clip_factors(ss, positions, verts, factors);
  if (brush.flag & BRUSH_FRONTFACE) {
    calc_front_face(cache.view_normal, vert_normals, verts, factors);
  }

  tls.distances.reinitialize(verts.size());
  const MutableSpan<float> distances = tls.distances;
  calc_distance_falloff(
      ss, positions, verts, eBrushFalloffShape(brush.falloff_shape), distances, factors);
  apply_hardness_to_distances(cache, distances);
  calc_brush_strength_factors(cache, brush, distances, factors);

  if (cache.automasking) {
    auto_mask::calc_vert_factors(object, *cache.automasking, node, verts, factors);
  }

  calc_brush_texture_factors(ss, brush, positions, verts, factors);

  tls.new_masks.reinitialize(verts.size());
  const MutableSpan<float> new_masks = tls.new_masks;
  array_utils::gather(mask.as_span(), verts, new_masks);

  tls.current_masks = tls.new_masks;
  const MutableSpan<float> current_masks = tls.current_masks;
  if (strength > 0.0f) {
    invert_mask(current_masks);
  }
  apply_factors(strength, current_masks, factors, new_masks);
  clamp_mask(new_masks);

  array_utils::scatter(new_masks.as_span(), verts, mask);
}

static BLI_NOINLINE void gather_mask(const SubdivCCG &subdiv_ccg,
                                     const Span<int> grids,
                                     const MutableSpan<float> mask)
{
  const CCGKey key = BKE_subdiv_ccg_key_top_level(subdiv_ccg);
  const Span<CCGElem *> elems = subdiv_ccg.grids;
  BLI_assert(grids.size() * key.grid_area == mask.size());

  for (const int i : grids.index_range()) {
    CCGElem *elem = elems[grids[i]];
    const int start = i * key.grid_area;
    for (const int offset : IndexRange(key.grid_area)) {
      mask[start + offset] = CCG_elem_offset_mask(key, elem, offset);
    }
  }
}

static BLI_NOINLINE void scatter_mask(const Span<float> mask,
                                      const Span<int> grids,
                                      SubdivCCG &subdiv_ccg)
{
  const CCGKey key = BKE_subdiv_ccg_key_top_level(subdiv_ccg);
  const Span<CCGElem *> elems = subdiv_ccg.grids;
  BLI_assert(grids.size() * key.grid_area == mask.size());

  for (const int i : grids.index_range()) {
    CCGElem *elem = elems[grids[i]];
    const int start = i * key.grid_area;
    for (const int offset : IndexRange(key.grid_area)) {
      CCG_elem_offset_mask(key, elem, offset) = mask[start + offset];
    }
  }
}

static void calc_grids(
    Object &object, const Brush &brush, const float strength, PBVHNode &node, LocalData &tls)
{
  SculptSession &ss = *object.sculpt;
  const StrokeCache &cache = *ss.cache;
  SubdivCCG &subdiv_ccg = *ss.subdiv_ccg;
  const CCGKey key = BKE_subdiv_ccg_key_top_level(subdiv_ccg);

  const Span<int> grids = bke::pbvh::node_grid_indices(node);
  const int grid_verts_num = grids.size() * key.grid_area;

  tls.positions.reinitialize(grid_verts_num);
  MutableSpan<float3> positions = tls.positions;
  gather_grids_positions(subdiv_ccg, grids, positions);

  tls.factors.reinitialize(grid_verts_num);
  const MutableSpan<float> factors = tls.factors;
  fill_factor_from_hide(subdiv_ccg, grids, factors);
  filter_region_clip_factors(ss, positions, factors);
  if (brush.flag & BRUSH_FRONTFACE) {
    calc_front_face(cache.view_normal, subdiv_ccg, grids, factors);
  }

  tls.distances.reinitialize(grid_verts_num);
  const MutableSpan<float> distances = tls.distances;
  calc_distance_falloff(
      ss, positions, eBrushFalloffShape(brush.falloff_shape), distances, factors);
  apply_hardness_to_distances(cache, distances);
  calc_brush_strength_factors(cache, brush, distances, factors);

  if (cache.automasking) {
    auto_mask::calc_grids_factors(object, *cache.automasking, node, grids, factors);
  }

  calc_brush_texture_factors(ss, brush, positions, factors);

  tls.new_masks.reinitialize(grid_verts_num);
  const MutableSpan<float> new_masks = tls.new_masks;
  gather_mask(subdiv_ccg, grids, new_masks);

  tls.current_masks = tls.new_masks;
  const MutableSpan<float> current_masks = tls.current_masks;
  if (strength > 0.0f) {
    invert_mask(current_masks);
  }
  apply_factors(strength, current_masks, factors, new_masks);
  clamp_mask(new_masks);

  scatter_mask(new_masks.as_span(), grids, subdiv_ccg);
}

static BLI_NOINLINE void gather_mask(const Set<BMVert *, 0> &verts,
                                     const int offset,
                                     const MutableSpan<float> mask)
{
  BLI_assert(verts.size() == mask.size());

  int i = 0;
  for (const BMVert *vert : verts) {
    mask[i] = BM_ELEM_CD_GET_FLOAT(vert, offset);
    i++;
  }
}

static BLI_NOINLINE void scatter_mask(const Span<float> mask,
                                      const int offset,
                                      const Set<BMVert *, 0> &verts)
{
  BLI_assert(verts.size() == mask.size());

  int i = 0;
  for (BMVert *vert : verts) {
    BM_ELEM_CD_SET_FLOAT(vert, offset, mask[i]);
    i++;
  }
}

static void calc_bmesh(
    Object &object, const Brush &brush, const float strength, PBVHNode &node, LocalData &tls)
{
  SculptSession &ss = *object.sculpt;
  const BMesh &bm = *ss.bm;
  const StrokeCache &cache = *ss.cache;

  const Set<BMVert *, 0> &verts = BKE_pbvh_bmesh_node_unique_verts(&node);

  tls.positions.reinitialize(verts.size());
  MutableSpan<float3> positions = tls.positions;
  gather_bmesh_positions(verts, positions);

  const int mask_offset = CustomData_get_offset_named(&bm.vdata, CD_PROP_FLOAT, ".sculpt_mask");

  tls.factors.reinitialize(verts.size());
  const MutableSpan<float> factors = tls.factors;
  fill_factor_from_hide(verts, factors);
  filter_region_clip_factors(ss, positions, factors);
  if (brush.flag & BRUSH_FRONTFACE) {
    calc_front_face(cache.view_normal, verts, factors);
  }

  tls.distances.reinitialize(verts.size());
  const MutableSpan<float> distances = tls.distances;
  calc_distance_falloff(
      ss, positions, eBrushFalloffShape(brush.falloff_shape), distances, factors);
  apply_hardness_to_distances(cache, distances);
  calc_brush_strength_factors(cache, brush, distances, factors);

  if (cache.automasking) {
    auto_mask::calc_vert_factors(object, *cache.automasking, node, verts, factors);
  }

  calc_brush_texture_factors(ss, brush, positions, factors);

  tls.new_masks.reinitialize(verts.size());
  const MutableSpan<float> new_masks = tls.new_masks;
  gather_mask(verts, mask_offset, new_masks);

  tls.current_masks = tls.new_masks;
  const MutableSpan<float> current_masks = tls.current_masks;
  if (strength > 0.0f) {
    invert_mask(current_masks);
  }
  apply_factors(strength, current_masks, factors, new_masks);
  clamp_mask(new_masks);

  scatter_mask(new_masks.as_span(), mask_offset, verts);
}

}  // namespace mask_cc

void do_mask_brush(const Sculpt &sd, Object &object, Span<PBVHNode *> nodes)
{
  SculptSession &ss = *object.sculpt;
  const Brush &brush = *BKE_paint_brush_for_read(&sd.paint);
  const float bstrength = ss.cache->bstrength;

  threading::EnumerableThreadSpecific<LocalData> all_tls;
  switch (BKE_pbvh_type(*ss.pbvh)) {
    case PBVH_FACES: {
      Mesh &mesh = *static_cast<Mesh *>(object.data);

      const PBVH &pbvh = *ss.pbvh;
      const Span<float3> positions = BKE_pbvh_get_vert_positions(pbvh);
      const Span<float3> vert_normals = BKE_pbvh_get_vert_normals(pbvh);

      bke::MutableAttributeAccessor attributes = mesh.attributes_for_write();

      bke::SpanAttributeWriter<float> mask = attributes.lookup_or_add_for_write_span<float>(
          ".sculpt_mask", bke::AttrDomain::Point);

      threading::parallel_for(nodes.index_range(), 1, [&](const IndexRange range) {
        threading::isolate_task([&]() {
          LocalData &tls = all_tls.local();
          for (const int i : range) {
            calc_faces(brush,
                       bstrength,
                       positions,
                       vert_normals,
                       *nodes[i],
                       object,
                       mesh,
                       tls,
                       mask.span);
          }
        });
      });
      mask.finish();
      break;
    }
    case PBVH_GRIDS: {
      threading::parallel_for(nodes.index_range(), 1, [&](const IndexRange range) {
        LocalData &tls = all_tls.local();
        for (const int i : range) {
          calc_grids(object, brush, bstrength, *nodes[i], tls);
        }
      });
      break;
    }
    case PBVH_BMESH: {
      threading::parallel_for(nodes.index_range(), 1, [&](const IndexRange range) {
        LocalData &tls = all_tls.local();
        for (const int i : range) {
          calc_bmesh(object, brush, bstrength, *nodes[i], tls);
        }
      });
      break;
    }
  }
}
}  // namespace blender::ed::sculpt_paint

/* SPDX-FileCopyrightText: 2012 by Nicholas Bishop. All rights reserved.
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup edsculpt
 */
#include "paint_mask.hh"

#include <cstdlib>

#include "MEM_guardedalloc.h"

#include "DNA_object_types.h"

#include "BLI_array_utils.hh"
#include "BLI_bit_span_ops.hh"
#include "BLI_enumerable_thread_specific.hh"
#include "BLI_math_base.hh"
#include "BLI_span.hh"
#include "BLI_vector.hh"

#include "BKE_attribute.hh"
#include "BKE_brush.hh"
#include "BKE_ccg.hh"
#include "BKE_context.hh"
#include "BKE_mesh.hh"
#include "BKE_multires.hh"
#include "BKE_paint.hh"
#include "BKE_pbvh_api.hh"
#include "BKE_subdiv_ccg.hh"
#include "BKE_subsurf.hh"

#include "RNA_access.hh"
#include "RNA_define.hh"

#include "WM_api.hh"
#include "WM_types.hh"

#include "ED_select_utils.hh"

#include "bmesh.hh"

#include "mesh_brush_common.hh"
#include "paint_intern.hh"
#include "sculpt_gesture.hh"
#include "sculpt_hide.hh"
#include "sculpt_intern.hh"
#include "sculpt_undo.hh"

namespace blender::ed::sculpt_paint::mask {

/* -------------------------------------------------------------------- */
/** \name Public API
 * \{ */

Array<float> duplicate_mask(const Object &object)
{
  const SculptSession &ss = *object.sculpt;
  switch (bke::object::pbvh_get(object)->type()) {
    case bke::pbvh::Type::Mesh: {
      const Mesh &mesh = *static_cast<const Mesh *>(object.data);
      const bke::AttributeAccessor attributes = mesh.attributes();
      const VArray mask = *attributes.lookup_or_default<float>(
          ".sculpt_mask", bke::AttrDomain::Point, 0.0f);
      Array<float> result(mask.size());
      mask.materialize(result);
      return result;
    }
    case bke::pbvh::Type::Grids: {
      const SubdivCCG &subdiv_ccg = *ss.subdiv_ccg;
      const CCGKey key = BKE_subdiv_ccg_key_top_level(subdiv_ccg);
      const Span<CCGElem *> grids = subdiv_ccg.grids;

      Array<float> result(grids.size() * key.grid_area);
      int index = 0;
      for (const int grid : grids.index_range()) {
        CCGElem *elem = grids[grid];
        for (const int i : IndexRange(key.grid_area)) {
          result[index] = CCG_elem_offset_mask(key, elem, i);
          index++;
        }
      }
      return result;
    }
    case bke::pbvh::Type::BMesh: {
      BMesh &bm = *ss.bm;
      const int offset = CustomData_get_offset_named(&bm.vdata, CD_PROP_FLOAT, ".sculpt_mask");
      Array<float> result(bm.totvert);
      if (offset == -1) {
        result.fill(0.0f);
      }
      else {
        BM_mesh_elem_table_ensure(&bm, BM_VERT);
        for (const int i : result.index_range()) {
          result[i] = BM_ELEM_CD_GET_FLOAT(BM_vert_at_index(&bm, i), offset);
        }
      }
      return result;
    }
  }
  BLI_assert_unreachable();
  return {};
}

void mix_new_masks(const Span<float> new_masks,
                   const Span<float> factors,
                   const MutableSpan<float> masks)
{
  BLI_assert(new_masks.size() == factors.size());
  BLI_assert(new_masks.size() == masks.size());

  for (const int i : masks.index_range()) {
    masks[i] += (new_masks[i] - masks[i]) * factors[i];
  }
}

void clamp_mask(const MutableSpan<float> masks)
{
  for (float &mask : masks) {
    mask = std::clamp(mask, 0.0f, 1.0f);
  }
}

void gather_mask_bmesh(const BMesh &bm,
                       const Set<BMVert *, 0> &verts,
                       const MutableSpan<float> r_mask)
{
  BLI_assert(verts.size() == r_mask.size());

  /* TODO: Avoid overhead of accessing attributes for every bke::pbvh::Tree node. */
  const int mask_offset = CustomData_get_offset_named(&bm.vdata, CD_PROP_FLOAT, ".sculpt_mask");
  int i = 0;
  for (const BMVert *vert : verts) {
    r_mask[i] = (mask_offset == -1) ? 0.0f : BM_ELEM_CD_GET_FLOAT(vert, mask_offset);
    i++;
  }
}

void gather_mask_grids(const SubdivCCG &subdiv_ccg,
                       const Span<int> grids,
                       const MutableSpan<float> r_mask)
{
  const CCGKey key = BKE_subdiv_ccg_key_top_level(subdiv_ccg);
  const Span<CCGElem *> elems = subdiv_ccg.grids;
  BLI_assert(grids.size() * key.grid_area == r_mask.size());

  if (key.has_mask) {
    for (const int i : grids.index_range()) {
      CCGElem *elem = elems[grids[i]];
      const int start = i * key.grid_area;
      for (const int offset : IndexRange(key.grid_area)) {
        r_mask[start + offset] = CCG_elem_offset_mask(key, elem, offset);
      }
    }
  }
  else {
    r_mask.fill(0.0f);
  }
}

void scatter_mask_grids(const Span<float> mask, SubdivCCG &subdiv_ccg, const Span<int> grids)
{
  const CCGKey key = BKE_subdiv_ccg_key_top_level(subdiv_ccg);
  const Span<CCGElem *> elems = subdiv_ccg.grids;
  BLI_assert(key.has_mask);
  BLI_assert(mask.size() == grids.size() * key.grid_area);
  for (const int i : grids.index_range()) {
    CCGElem *elem = elems[grids[i]];
    const int start = i * key.grid_area;
    for (const int offset : IndexRange(key.grid_area)) {
      CCG_elem_offset_mask(key, elem, offset) = mask[start + offset];
    }
  }
}

void scatter_mask_bmesh(const Span<float> mask, const BMesh &bm, const Set<BMVert *, 0> &verts)
{
  BLI_assert(verts.size() == mask.size());

  const int mask_offset = CustomData_get_offset_named(&bm.vdata, CD_PROP_FLOAT, ".sculpt_mask");
  BLI_assert(mask_offset != -1);
  int i = 0;
  for (BMVert *vert : verts) {
    BM_ELEM_CD_SET_FLOAT(vert, mask_offset, mask[i]);
    i++;
  }
}

static float average_masks(const CCGKey &key,
                           const Span<CCGElem *> elems,
                           const Span<SubdivCCGCoord> coords)
{
  float sum = 0;
  for (const SubdivCCGCoord coord : coords) {
    sum += CCG_grid_elem_mask(key, elems[coord.grid_index], coord.x, coord.y);
  }
  return sum / float(coords.size());
}

void average_neighbor_mask_grids(const SubdivCCG &subdiv_ccg,
                                 const Span<int> grids,
                                 const MutableSpan<float> new_masks)
{
  const CCGKey key = BKE_subdiv_ccg_key_top_level(subdiv_ccg);
  const Span<CCGElem *> elems = subdiv_ccg.grids;

  for (const int i : grids.index_range()) {
    const int grid = grids[i];
    const int node_verts_start = i * key.grid_area;

    for (const int y : IndexRange(key.grid_size)) {
      for (const int x : IndexRange(key.grid_size)) {
        const int offset = CCG_grid_xy_to_index(key.grid_size, x, y);
        const int node_vert_index = node_verts_start + offset;

        SubdivCCGCoord coord{};
        coord.grid_index = grid;
        coord.x = x;
        coord.y = y;

        SubdivCCGNeighbors neighbors;
        BKE_subdiv_ccg_neighbor_coords_get(subdiv_ccg, coord, false, neighbors);

        new_masks[node_vert_index] = average_masks(key, elems, neighbors.coords);
      }
    }
  }
}

static float average_masks(const int mask_offset, const Span<const BMVert *> verts)
{
  float sum = 0;
  for (const BMVert *vert : verts) {
    sum += BM_ELEM_CD_GET_FLOAT(vert, mask_offset);
  }
  return sum / float(verts.size());
}

void average_neighbor_mask_bmesh(const int mask_offset,
                                 const Set<BMVert *, 0> &verts,
                                 const MutableSpan<float> new_masks)
{
  Vector<BMVert *, 64> neighbors;
  int i = 0;
  for (BMVert *vert : verts) {
    new_masks[i] = average_masks(mask_offset, vert_neighbors_get_bmesh(*vert, neighbors));
    i++;
  }
}

void update_mask_mesh(const Depsgraph &depsgraph,
                      Object &object,
                      const IndexMask &node_mask,
                      FunctionRef<void(MutableSpan<float>, Span<int>)> update_fn)
{
  bke::pbvh::Tree &pbvh = *bke::object::pbvh_get(object);
  MutableSpan<bke::pbvh::MeshNode> nodes = pbvh.nodes<bke::pbvh::MeshNode>();

  Mesh &mesh = *static_cast<Mesh *>(object.data);
  bke::MutableAttributeAccessor attributes = mesh.attributes_for_write();
  const VArraySpan hide_vert = *attributes.lookup<bool>(".hide_vert", bke::AttrDomain::Point);
  bke::SpanAttributeWriter<float> mask = attributes.lookup_or_add_for_write_span<float>(
      ".sculpt_mask", bke::AttrDomain::Point);
  if (!mask) {
    return;
  }

  struct LocalData {
    Vector<int> visible_verts;
    Vector<float> mask;
  };

  threading::EnumerableThreadSpecific<LocalData> all_tls;
  threading::parallel_for(node_mask.index_range(), 1, [&](const IndexRange range) {
    LocalData &tls = all_tls.local();
    node_mask.slice(range).foreach_index([&](const int i) {
      const Span<int> verts = hide::node_visible_verts(nodes[i], hide_vert, tls.visible_verts);
      tls.mask.resize(verts.size());
      gather_data_mesh(mask.span.as_span(), verts, tls.mask.as_mutable_span());
      update_fn(tls.mask, verts);
      if (array_utils::indexed_data_equal<float>(mask.span, verts, tls.mask)) {
        return;
      }
      undo::push_node(depsgraph, object, &nodes[i], undo::Type::Mask);
      scatter_data_mesh(tls.mask.as_span(), verts, mask.span);
      bke::pbvh::node_update_mask_mesh(mask.span, static_cast<bke::pbvh::MeshNode &>(nodes[i]));
      BKE_pbvh_node_mark_redraw(nodes[i]);
    });
  });

  mask.finish();
}

bool mask_equals_array_grids(const Span<CCGElem *> elems,
                             const CCGKey &key,
                             const Span<int> grids,
                             const Span<float> values)
{
  BLI_assert(grids.size() * key.grid_area == values.size());

  const IndexRange range = grids.index_range();
  return std::all_of(range.begin(), range.end(), [&](const int i) {
    const int grid = grids[i];
    const int node_verts_start = i * key.grid_area;

    CCGElem *elem = elems[grid];
    for (const int offset : IndexRange(key.grid_area)) {
      if (CCG_elem_offset_mask(key, elem, i) != values[node_verts_start + offset]) {
        return false;
      }
    }
    return true;
  });
}

bool mask_equals_array_bmesh(const int mask_offset,
                             const Set<BMVert *, 0> &verts,
                             const Span<float> values)
{
  BLI_assert(verts.size() == values.size());

  int i = 0;
  for (const BMVert *vert : verts) {
    if (BM_ELEM_CD_GET_FLOAT(vert, mask_offset) != values[i]) {
      return false;
    }
    i++;
  }
  return true;
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Global Mask Operators
 * Operators that act upon the entirety of a given object's mesh.
 * \{ */

/* The gesture API doesn't write to this enum type,
 * it writes to eSelectOp from ED_select_utils.hh.
 * We must thus map the modes here to the desired
 * eSelectOp modes.
 *
 * Fixes #102349.
 */
enum class FloodFillMode {
  Value = SEL_OP_SUB,
  InverseValue = SEL_OP_ADD,
  InverseMeshValue = SEL_OP_XOR,
};

static const EnumPropertyItem mode_items[] = {
    {int(FloodFillMode::Value),
     "VALUE",
     0,
     "Value",
     "Set mask to the level specified by the 'value' property"},
    {int(FloodFillMode::InverseValue),
     "VALUE_INVERSE",
     0,
     "Value Inverted",
     "Set mask to the level specified by the inverted 'value' property"},
    {int(FloodFillMode::InverseMeshValue), "INVERT", 0, "Invert", "Invert the mask"},
    {0}};

static Span<int> get_hidden_verts(const bke::pbvh::MeshNode &node,
                                  const Span<bool> hide_vert,
                                  Vector<int> &indices)
{
  if (hide_vert.is_empty()) {
    return {};
  }
  const Span<int> verts = node.verts();
  if (BKE_pbvh_node_fully_hidden_get(node)) {
    return verts;
  }
  indices.resize(verts.size());
  const int *end = std::copy_if(verts.begin(), verts.end(), indices.begin(), [&](const int vert) {
    return hide_vert[vert];
  });
  indices.resize(end - indices.begin());
  return indices;
}

static bool try_remove_mask_mesh(const Depsgraph &depsgraph,
                                 Object &object,
                                 const IndexMask &node_mask)
{
  bke::pbvh::Tree &pbvh = *bke::object::pbvh_get(object);
  MutableSpan<bke::pbvh::MeshNode> nodes = pbvh.nodes<bke::pbvh::MeshNode>();
  Mesh &mesh = *static_cast<Mesh *>(object.data);
  bke::MutableAttributeAccessor attributes = mesh.attributes_for_write();
  const VArraySpan mask = *attributes.lookup<float>(".sculpt_mask", bke::AttrDomain::Point);
  if (mask.is_empty()) {
    return true;
  }

  /* If there are any hidden vertices that shouldn't be affected with a mask value set, the
   * attribute cannot be removed. This could also be done by building an IndexMask in the full
   * vertex domain. */
  const VArraySpan hide_vert = *attributes.lookup<bool>(".hide_vert", bke::AttrDomain::Point);
  threading::EnumerableThreadSpecific<Vector<int>> all_index_data;
  const bool hidden_masked_verts = threading::parallel_reduce(
      node_mask.index_range(),
      1,
      false,
      [&](const IndexRange range, bool value) {
        if (value) {
          return value;
        }
        Vector<int> &index_data = all_index_data.local();
        node_mask.slice(range).foreach_index([&](const int i) {
          if (value) {
            return;
          }
          const Span<int> verts = get_hidden_verts(nodes[i], hide_vert, index_data);
          if (std::any_of(verts.begin(), verts.end(), [&](int i) { return mask[i] > 0.0f; })) {
            value = true;
            return;
          }
        });
        return value;
      },
      std::logical_or());
  if (hidden_masked_verts) {
    return false;
  }

  /* Store undo data for nodes with changed mask. */
  node_mask.foreach_index(GrainSize(1), [&](const int i) {
    const Span<int> verts = nodes[i].verts();
    if (std::all_of(verts.begin(), verts.end(), [&](const int i) { return mask[i] == 0.0f; })) {
      return;
    }
    undo::push_node(depsgraph, object, &nodes[i], undo::Type::Mask);
    BKE_pbvh_node_mark_redraw(nodes[i]);
  });

  attributes.remove(".sculpt_mask");
  /* Avoid calling #BKE_pbvh_node_mark_update_mask by doing that update here. */
  node_mask.foreach_index([&](const int i) {
    BKE_pbvh_node_fully_masked_set(nodes[i], false);
    BKE_pbvh_node_fully_unmasked_set(nodes[i], true);
  });
  return true;
}

static void fill_mask_mesh(const Depsgraph &depsgraph,
                           Object &object,
                           const float value,
                           const IndexMask &node_mask)
{
  bke::pbvh::Tree &pbvh = *bke::object::pbvh_get(object);
  MutableSpan<bke::pbvh::MeshNode> nodes = pbvh.nodes<bke::pbvh::MeshNode>();

  Mesh &mesh = *static_cast<Mesh *>(object.data);
  bke::MutableAttributeAccessor attributes = mesh.attributes_for_write();
  const VArraySpan hide_vert = *attributes.lookup<bool>(".hide_vert", bke::AttrDomain::Point);
  if (value == 0.0f) {
    if (try_remove_mask_mesh(depsgraph, object, node_mask)) {
      return;
    }
  }

  bke::SpanAttributeWriter<float> mask = attributes.lookup_or_add_for_write_span<float>(
      ".sculpt_mask", bke::AttrDomain::Point);

  threading::EnumerableThreadSpecific<Vector<int>> all_index_data;
  threading::parallel_for(node_mask.index_range(), 1, [&](const IndexRange range) {
    Vector<int> &index_data = all_index_data.local();
    node_mask.slice(range).foreach_index([&](const int i) {
      const Span<int> verts = hide::node_visible_verts(nodes[i], hide_vert, index_data);
      if (std::all_of(verts.begin(), verts.end(), [&](int i) { return mask.span[i] == value; })) {
        return;
      }
      undo::push_node(depsgraph, object, &nodes[i], undo::Type::Mask);
      mask.span.fill_indices(verts, value);
      BKE_pbvh_node_mark_redraw(nodes[i]);
    });
  });

  mask.finish();
  /* Avoid calling #BKE_pbvh_node_mark_update_mask by doing that update here. */
  node_mask.foreach_index([&](const int i) {
    BKE_pbvh_node_fully_masked_set(nodes[i], value == 1.0f);
    BKE_pbvh_node_fully_unmasked_set(nodes[i], value == 0.0f);
  });
}

static void fill_mask_grids(Main &bmain,
                            const Scene &scene,
                            Depsgraph &depsgraph,
                            Object &object,
                            const float value,
                            const IndexMask &node_mask)
{
  SculptSession &ss = *object.sculpt;
  bke::pbvh::Tree &pbvh = *bke::object::pbvh_get(object);
  MutableSpan<bke::pbvh::GridsNode> nodes = pbvh.nodes<bke::pbvh::GridsNode>();

  SubdivCCG &subdiv_ccg = *ss.subdiv_ccg;

  const CCGKey key = BKE_subdiv_ccg_key_top_level(subdiv_ccg);
  if (value == 0.0f && !key.has_mask) {
    /* Unlike meshes, don't dynamically remove masks since it is interleaved with other data. */
    return;
  }

  MultiresModifierData &mmd = *BKE_sculpt_multires_active(&scene, &object);
  BKE_sculpt_mask_layers_ensure(&depsgraph, &bmain, &object, &mmd);

  const BitGroupVector<> &grid_hidden = subdiv_ccg.grid_hidden;

  const Span<CCGElem *> grids = subdiv_ccg.grids;
  bool any_changed = false;
  node_mask.foreach_index(GrainSize(1), [&](const int i) {
    const Span<int> grid_indices = nodes[i].grids();
    if (std::all_of(grid_indices.begin(), grid_indices.end(), [&](const int grid) {
          CCGElem *elem = grids[grid];
          for (const int i : IndexRange(key.grid_area)) {
            if (CCG_elem_offset_mask(key, elem, i) != value) {
              return false;
            }
          }
          return true;
        }))
    {
      return;
    }
    undo::push_node(depsgraph, object, &nodes[i], undo::Type::Mask);

    if (grid_hidden.is_empty()) {
      for (const int grid : grid_indices) {
        CCGElem *elem = grids[grid];
        for (const int i : IndexRange(key.grid_area)) {
          CCG_elem_offset_mask(key, elem, i) = value;
        }
      }
    }
    else {
      for (const int grid : grid_indices) {
        CCGElem *elem = grids[grid];
        bits::foreach_0_index(grid_hidden[grid],
                              [&](const int i) { CCG_elem_offset_mask(key, elem, i) = value; });
      }
    }
    BKE_pbvh_node_mark_redraw(nodes[i]);
    any_changed = true;
  });

  if (any_changed) {
    multires_mark_as_modified(&depsgraph, &object, MULTIRES_COORDS_MODIFIED);
  }
  /* Avoid calling #BKE_pbvh_node_mark_update_mask by doing that update here. */
  node_mask.foreach_index([&](const int i) {
    BKE_pbvh_node_fully_masked_set(nodes[i], value == 1.0f);
    BKE_pbvh_node_fully_unmasked_set(nodes[i], value == 0.0f);
  });
}

static void fill_mask_bmesh(const Depsgraph &depsgraph,
                            Object &object,
                            const float value,
                            const IndexMask &node_mask)
{
  SculptSession &ss = *object.sculpt;
  bke::pbvh::Tree &pbvh = *bke::object::pbvh_get(object);
  MutableSpan<bke::pbvh::BMeshNode> nodes = pbvh.nodes<bke::pbvh::BMeshNode>();

  BMesh &bm = *ss.bm;
  const int offset = CustomData_get_offset_named(&bm.vdata, CD_PROP_FLOAT, ".sculpt_mask");
  if (value == 0.0f && offset == -1) {
    return;
  }
  if (offset == -1) {
    /* Mask is not dynamically added or removed for dynamic topology sculpting. */
    BLI_assert_unreachable();
    return;
  }

  node_mask.foreach_index(GrainSize(1), [&](const int i) {
    bool redraw = false;
    undo::push_node(depsgraph, object, &nodes[i], undo::Type::Mask);
    for (BMVert *vert : BKE_pbvh_bmesh_node_unique_verts(&nodes[i])) {
      if (!BM_elem_flag_test(vert, BM_ELEM_HIDDEN)) {
        if (BM_ELEM_CD_GET_FLOAT(vert, offset) != value) {
          BM_ELEM_CD_SET_FLOAT(vert, offset, value);
          redraw = true;
        }
      }
    }
    if (redraw) {
      BKE_pbvh_node_mark_redraw(nodes[i]);
    }
  });
  /* Avoid calling #BKE_pbvh_node_mark_update_mask by doing that update here. */
  node_mask.foreach_index([&](const int i) {
    BKE_pbvh_node_fully_masked_set(nodes[i], value == 1.0f);
    BKE_pbvh_node_fully_unmasked_set(nodes[i], value == 0.0f);
  });
}

static void fill_mask(
    Main &bmain, const Scene &scene, Depsgraph &depsgraph, Object &object, const float value)
{
  bke::pbvh::Tree &pbvh = *bke::object::pbvh_get(object);
  IndexMaskMemory memory;
  const IndexMask node_mask = bke::pbvh::all_leaf_nodes(pbvh, memory);
  switch (pbvh.type()) {
    case bke::pbvh::Type::Mesh:
      fill_mask_mesh(depsgraph, object, value, node_mask);
      break;
    case bke::pbvh::Type::Grids:
      fill_mask_grids(bmain, scene, depsgraph, object, value, node_mask);
      break;
    case bke::pbvh::Type::BMesh:
      fill_mask_bmesh(depsgraph, object, value, node_mask);
      break;
  }
}

static void invert_mask_grids(Main &bmain,
                              const Scene &scene,
                              Depsgraph &depsgraph,
                              Object &object,
                              const IndexMask &node_mask)
{
  SculptSession &ss = *object.sculpt;
  bke::pbvh::Tree &pbvh = *bke::object::pbvh_get(object);
  MutableSpan<bke::pbvh::GridsNode> nodes = pbvh.nodes<bke::pbvh::GridsNode>();

  SubdivCCG &subdiv_ccg = *ss.subdiv_ccg;

  MultiresModifierData &mmd = *BKE_sculpt_multires_active(&scene, &object);
  BKE_sculpt_mask_layers_ensure(&depsgraph, &bmain, &object, &mmd);

  undo::push_nodes(depsgraph, object, node_mask, undo::Type::Mask);

  const BitGroupVector<> &grid_hidden = subdiv_ccg.grid_hidden;

  const CCGKey key = BKE_subdiv_ccg_key_top_level(subdiv_ccg);
  const Span<CCGElem *> grids = subdiv_ccg.grids;
  node_mask.foreach_index(GrainSize(1), [&](const int i) {
    const Span<int> grid_indices = nodes[i].grids();
    if (grid_hidden.is_empty()) {
      for (const int grid : grid_indices) {
        CCGElem *elem = grids[grid];
        for (const int i : IndexRange(key.grid_area)) {
          CCG_elem_offset_mask(key, elem, i) = 1.0f - CCG_elem_offset_mask(key, elem, i);
        }
      }
    }
    else {
      for (const int grid : grid_indices) {
        CCGElem *elem = grids[grid];
        bits::foreach_0_index(grid_hidden[grid], [&](const int i) {
          CCG_elem_offset_mask(key, elem, i) = 1.0f - CCG_elem_offset_mask(key, elem, i);
        });
      }
    }
    BKE_pbvh_node_mark_update_mask(nodes[i]);
    bke::pbvh::node_update_mask_grids(key, grids, nodes[i]);
  });

  multires_mark_as_modified(&depsgraph, &object, MULTIRES_COORDS_MODIFIED);
}

static void invert_mask_bmesh(const Depsgraph &depsgraph,
                              Object &object,
                              const IndexMask &node_mask)
{
  bke::pbvh::Tree &pbvh = *bke::object::pbvh_get(object);
  MutableSpan<bke::pbvh::BMeshNode> nodes = pbvh.nodes<bke::pbvh::BMeshNode>();
  BMesh &bm = *object.sculpt->bm;
  const int offset = CustomData_get_offset_named(&bm.vdata, CD_PROP_FLOAT, ".sculpt_mask");
  if (offset == -1) {
    BLI_assert_unreachable();
    return;
  }

  undo::push_nodes(depsgraph, object, node_mask, undo::Type::Mask);
  node_mask.foreach_index(GrainSize(1), [&](const int i) {
    for (BMVert *vert : BKE_pbvh_bmesh_node_unique_verts(&nodes[i])) {
      if (!BM_elem_flag_test(vert, BM_ELEM_HIDDEN)) {
        BM_ELEM_CD_SET_FLOAT(vert, offset, 1.0f - BM_ELEM_CD_GET_FLOAT(vert, offset));
      }
    }
    BKE_pbvh_node_mark_update_mask(nodes[i]);
    bke::pbvh::node_update_mask_bmesh(offset, nodes[i]);
  });
}

static void invert_mask(Main &bmain, const Scene &scene, Depsgraph &depsgraph, Object &object)
{
  IndexMaskMemory memory;
  const IndexMask node_mask = bke::pbvh::all_leaf_nodes(*bke::object::pbvh_get(object), memory);
  switch (bke::object::pbvh_get(object)->type()) {
    case bke::pbvh::Type::Mesh:
      write_mask_mesh(
          depsgraph, object, node_mask, [&](MutableSpan<float> mask, const Span<int> verts) {
            for (const int vert : verts) {
              mask[vert] = 1.0f - mask[vert];
            }
          });
      break;
    case bke::pbvh::Type::Grids:
      invert_mask_grids(bmain, scene, depsgraph, object, node_mask);
      break;
    case bke::pbvh::Type::BMesh:
      invert_mask_bmesh(depsgraph, object, node_mask);
      break;
  }
}

static int mask_flood_fill_exec(bContext *C, wmOperator *op)
{
  Main &bmain = *CTX_data_main(C);
  const Scene &scene = *CTX_data_scene(C);
  Object &object = *CTX_data_active_object(C);
  Depsgraph &depsgraph = *CTX_data_ensure_evaluated_depsgraph(C);

  const FloodFillMode mode = FloodFillMode(RNA_enum_get(op->ptr, "mode"));
  const float value = RNA_float_get(op->ptr, "value");

  BKE_sculpt_update_object_for_edit(&depsgraph, &object, false);

  undo::push_begin(object, op);
  switch (mode) {
    case FloodFillMode::Value:
      fill_mask(bmain, scene, depsgraph, object, value);
      break;
    case FloodFillMode::InverseValue:
      fill_mask(bmain, scene, depsgraph, object, 1.0f - value);
      break;
    case FloodFillMode::InverseMeshValue:
      invert_mask(bmain, scene, depsgraph, object);
      break;
  }

  undo::push_end(object);

  SCULPT_tag_update_overlays(C);

  return OPERATOR_FINISHED;
}

void PAINT_OT_mask_flood_fill(wmOperatorType *ot)
{
  /* Identifiers. */
  ot->name = "Mask Flood Fill";
  ot->idname = "PAINT_OT_mask_flood_fill";
  ot->description = "Fill the whole mask with a given value, or invert its values";

  /* API callbacks. */
  ot->exec = mask_flood_fill_exec;
  ot->poll = SCULPT_mode_poll;

  ot->flag = OPTYPE_REGISTER;

  /* RNA. */
  RNA_def_enum(ot->srna, "mode", mode_items, int(FloodFillMode::Value), "Mode", nullptr);
  RNA_def_float(
      ot->srna,
      "value",
      0.0f,
      0.0f,
      1.0f,
      "Value",
      "Mask level to use when mode is 'Value'; zero means no masking and one is fully masked",
      0.0f,
      1.0f);
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Gesture-based Mask Operators
 * Operators that act upon a user-selected area.
 * \{ */

struct MaskOperation {
  gesture::Operation op;

  FloodFillMode mode;
  float value;
};

static void gesture_begin(bContext &C, wmOperator &op, gesture::GestureData &gesture_data)
{
  Depsgraph *depsgraph = CTX_data_depsgraph_pointer(&C);
  BKE_sculpt_update_object_for_edit(depsgraph, gesture_data.vc.obact, false);
  undo::push_begin(*gesture_data.vc.obact, &op);
}

static float mask_gesture_get_new_value(const float elem, FloodFillMode mode, float value)
{
  switch (mode) {
    case FloodFillMode::Value:
      return value;
    case FloodFillMode::InverseValue:
      return 1.0f - value;
    case FloodFillMode::InverseMeshValue:
      return 1.0f - elem;
  }
  BLI_assert_unreachable();
  return 0.0f;
}

static void gesture_apply_for_symmetry_pass(bContext & /*C*/, gesture::GestureData &gesture_data)
{
  const IndexMask &node_mask = gesture_data.node_mask;
  const MaskOperation &op = *reinterpret_cast<const MaskOperation *>(gesture_data.operation);
  Object &object = *gesture_data.vc.obact;
  const Depsgraph &depsgraph = *gesture_data.vc.depsgraph;
  switch (bke::object::pbvh_get(object)->type()) {
    case bke::pbvh::Type::Mesh: {
      const Span<float3> positions = bke::pbvh::vert_positions_eval(depsgraph, object);
      const Span<float3> normals = bke::pbvh::vert_normals_eval(depsgraph, object);
      update_mask_mesh(
          depsgraph, object, node_mask, [&](MutableSpan<float> node_mask, const Span<int> verts) {
            for (const int i : verts.index_range()) {
              const int vert = verts[i];
              if (gesture::is_affected(gesture_data, positions[vert], normals[vert])) {
                node_mask[i] = mask_gesture_get_new_value(node_mask[i], op.mode, op.value);
              }
            }
          });
      break;
    }
    case bke::pbvh::Type::Grids: {
      bke::pbvh::Tree &pbvh = *bke::object::pbvh_get(object);
      MutableSpan<bke::pbvh::GridsNode> nodes = pbvh.nodes<bke::pbvh::GridsNode>();
      SubdivCCG &subdiv_ccg = *gesture_data.ss->subdiv_ccg;
      const Span<CCGElem *> grids = subdiv_ccg.grids;
      const BitGroupVector<> &grid_hidden = subdiv_ccg.grid_hidden;
      const CCGKey key = BKE_subdiv_ccg_key_top_level(subdiv_ccg);
      threading::parallel_for(node_mask.index_range(), 1, [&](const IndexRange range) {
        node_mask.slice(range).foreach_index([&](const int i) {
          bool any_changed = false;
          for (const int grid : nodes[i].grids()) {
            CCGElem *elem = grids[grid];
            BKE_subdiv_ccg_foreach_visible_grid_vert(key, grid_hidden, grid, [&](const int i) {
              if (gesture::is_affected(gesture_data,
                                       CCG_elem_offset_co(key, elem, i),
                                       CCG_elem_offset_no(key, elem, i)))
              {
                float &mask = CCG_elem_offset_mask(key, elem, i);
                if (!any_changed) {
                  any_changed = true;
                  undo::push_node(depsgraph, object, &nodes[i], undo::Type::Mask);
                }
                mask = mask_gesture_get_new_value(mask, op.mode, op.value);
              }
            });
            BKE_pbvh_node_mark_update_mask(nodes[i]);
          }
        });
      });
      break;
    }
    case bke::pbvh::Type::BMesh: {
      bke::pbvh::Tree &pbvh = *bke::object::pbvh_get(object);
      MutableSpan<bke::pbvh::BMeshNode> nodes = pbvh.nodes<bke::pbvh::BMeshNode>();
      BMesh &bm = *gesture_data.ss->bm;
      const int offset = CustomData_get_offset_named(&bm.vdata, CD_PROP_FLOAT, ".sculpt_mask");
      threading::parallel_for(node_mask.index_range(), 1, [&](const IndexRange range) {
        node_mask.slice(range).foreach_index([&](const int i) {
          bool any_changed = false;
          for (BMVert *vert : BKE_pbvh_bmesh_node_unique_verts(&nodes[i])) {
            if (gesture::is_affected(gesture_data, vert->co, vert->no)) {
              const float old_mask = BM_ELEM_CD_GET_FLOAT(vert, offset);
              if (!any_changed) {
                any_changed = true;
                undo::push_node(depsgraph, object, &nodes[i], undo::Type::Mask);
              }
              const float new_mask = mask_gesture_get_new_value(old_mask, op.mode, op.value);
              BM_ELEM_CD_SET_FLOAT(vert, offset, new_mask);
            }
          }
          BKE_pbvh_node_mark_update_mask(nodes[i]);
        });
      });
      break;
    }
  }
}

static void gesture_end(bContext &C, gesture::GestureData &gesture_data)
{
  Depsgraph *depsgraph = CTX_data_depsgraph_pointer(&C);
  Object &object = *gesture_data.vc.obact;
  if (bke::object::pbvh_get(object)->type() == bke::pbvh::Type::Grids) {
    multires_mark_as_modified(depsgraph, &object, MULTIRES_COORDS_MODIFIED);
  }
  bke::pbvh::update_mask(object, *bke::object::pbvh_get(object));
  undo::push_end(object);
}

static void init_operation(bContext &C, gesture::GestureData &gesture_data, wmOperator &op)
{
  gesture_data.operation = reinterpret_cast<gesture::Operation *>(
      MEM_cnew<MaskOperation>(__func__));

  MaskOperation *mask_operation = (MaskOperation *)gesture_data.operation;

  Object *object = gesture_data.vc.obact;
  MultiresModifierData *mmd = BKE_sculpt_multires_active(gesture_data.vc.scene, object);
  BKE_sculpt_mask_layers_ensure(
      CTX_data_depsgraph_pointer(&C), CTX_data_main(&C), gesture_data.vc.obact, mmd);

  mask_operation->op.begin = gesture_begin;
  mask_operation->op.apply_for_symmetry_pass = gesture_apply_for_symmetry_pass;
  mask_operation->op.end = gesture_end;

  mask_operation->mode = FloodFillMode(RNA_enum_get(op.ptr, "mode"));
  mask_operation->value = RNA_float_get(op.ptr, "value");
}

static void gesture_operator_properties(wmOperatorType *ot)
{
  RNA_def_enum(ot->srna, "mode", mode_items, int(FloodFillMode::Value), "Mode", nullptr);
  RNA_def_float(
      ot->srna,
      "value",
      1.0f,
      0.0f,
      1.0f,
      "Value",
      "Mask level to use when mode is 'Value'; zero means no masking and one is fully masked",
      0.0f,
      1.0f);
}

static int gesture_box_exec(bContext *C, wmOperator *op)
{
  std::unique_ptr<gesture::GestureData> gesture_data = gesture::init_from_box(C, op);
  if (!gesture_data) {
    return OPERATOR_CANCELLED;
  }
  init_operation(*C, *gesture_data, *op);
  gesture::apply(*C, *gesture_data, *op);
  return OPERATOR_FINISHED;
}

static int gesture_lasso_exec(bContext *C, wmOperator *op)
{
  std::unique_ptr<gesture::GestureData> gesture_data = gesture::init_from_lasso(C, op);
  if (!gesture_data) {
    return OPERATOR_CANCELLED;
  }
  init_operation(*C, *gesture_data, *op);
  gesture::apply(*C, *gesture_data, *op);
  return OPERATOR_FINISHED;
}

static int gesture_line_exec(bContext *C, wmOperator *op)
{
  std::unique_ptr<gesture::GestureData> gesture_data = gesture::init_from_line(C, op);
  if (!gesture_data) {
    return OPERATOR_CANCELLED;
  }
  init_operation(*C, *gesture_data, *op);
  gesture::apply(*C, *gesture_data, *op);
  return OPERATOR_FINISHED;
}

static int gesture_polyline_exec(bContext *C, wmOperator *op)
{
  std::unique_ptr<gesture::GestureData> gesture_data = gesture::init_from_polyline(C, op);
  if (!gesture_data) {
    return OPERATOR_CANCELLED;
  }
  init_operation(*C, *gesture_data, *op);
  gesture::apply(*C, *gesture_data, *op);
  return OPERATOR_FINISHED;
}

void PAINT_OT_mask_lasso_gesture(wmOperatorType *ot)
{
  ot->name = "Mask Lasso Gesture";
  ot->idname = "PAINT_OT_mask_lasso_gesture";
  ot->description = "Mask within a shape defined by the cursor";

  ot->invoke = WM_gesture_lasso_invoke;
  ot->modal = WM_gesture_lasso_modal;
  ot->exec = gesture_lasso_exec;

  ot->poll = SCULPT_mode_poll_view3d;

  ot->flag = OPTYPE_REGISTER | OPTYPE_DEPENDS_ON_CURSOR;

  WM_operator_properties_gesture_lasso(ot);
  gesture::operator_properties(ot, gesture::ShapeType::Lasso);

  gesture_operator_properties(ot);
}

void PAINT_OT_mask_box_gesture(wmOperatorType *ot)
{
  ot->name = "Mask Box Gesture";
  ot->idname = "PAINT_OT_mask_box_gesture";
  ot->description = "Mask within a rectangle defined by the cursor";

  ot->invoke = WM_gesture_box_invoke;
  ot->modal = WM_gesture_box_modal;
  ot->exec = gesture_box_exec;

  ot->poll = SCULPT_mode_poll_view3d;

  ot->flag = OPTYPE_REGISTER;

  WM_operator_properties_border(ot);
  gesture::operator_properties(ot, gesture::ShapeType::Box);

  gesture_operator_properties(ot);
}

void PAINT_OT_mask_line_gesture(wmOperatorType *ot)
{
  ot->name = "Mask Line Gesture";
  ot->idname = "PAINT_OT_mask_line_gesture";
  ot->description = "Mask to one side of a line defined by the cursor";

  ot->invoke = WM_gesture_straightline_active_side_invoke;
  ot->modal = WM_gesture_straightline_oneshot_modal;
  ot->exec = gesture_line_exec;

  ot->poll = SCULPT_mode_poll_view3d;

  ot->flag = OPTYPE_REGISTER;

  WM_operator_properties_gesture_straightline(ot, WM_CURSOR_EDIT);
  gesture::operator_properties(ot, gesture::ShapeType::Line);

  gesture_operator_properties(ot);
}

void PAINT_OT_mask_polyline_gesture(wmOperatorType *ot)
{
  ot->name = "Mask Polyline Gesture";
  ot->idname = "PAINT_OT_mask_polyline_gesture";
  ot->description = "Mask within a shape defined by the cursor";

  ot->invoke = WM_gesture_polyline_invoke;
  ot->modal = WM_gesture_polyline_modal;
  ot->exec = gesture_polyline_exec;

  ot->poll = SCULPT_mode_poll_view3d;

  ot->flag = OPTYPE_REGISTER | OPTYPE_DEPENDS_ON_CURSOR;

  WM_operator_properties_gesture_polyline(ot);
  gesture::operator_properties(ot, gesture::ShapeType::Lasso);

  gesture_operator_properties(ot);
}

/** \} */

}  // namespace blender::ed::sculpt_paint::mask

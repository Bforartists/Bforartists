/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#include "BLI_array.hh"
#include "BLI_array_utils.hh"
#include "BLI_set.hh"

#include "BKE_attribute.hh"
#include "BKE_attribute_math.hh"
#include "BKE_curves.hh"
#include "BKE_mesh.hh"

#include "GEO_mesh_to_curve.hh"
#include "GEO_randomize.hh"

namespace blender::geometry {

BLI_NOINLINE bke::CurvesGeometry create_curve_from_vert_indices(
    const bke::AttributeAccessor &mesh_attributes,
    const Span<int> vert_indices,
    const Span<int> curve_offsets,
    const IndexRange cyclic_curves,
    const bke::AttributeFilter &attribute_filter)
{
  bke::CurvesGeometry curves(vert_indices.size(), curve_offsets.size());
  curves.offsets_for_write().drop_back(1).copy_from(curve_offsets);
  curves.offsets_for_write().last() = vert_indices.size();
  curves.fill_curve_types(CURVE_TYPE_POLY);

  bke::MutableAttributeAccessor curves_attributes = curves.attributes_for_write();

  if (!cyclic_curves.is_empty()) {
    curves.cyclic_for_write().slice(cyclic_curves).fill(true);
  }

  /* Don't copy attributes that are built-in on meshes but not on curves. */
  Set<std::string> skip;
  for (const StringRef id : mesh_attributes.all_ids()) {
    if (mesh_attributes.is_builtin(id) && !curves_attributes.is_builtin(id)) {
      skip.add(id);
    }
  }
  const auto attribute_filter_with_skip = bke::attribute_filter_with_skip_ref(attribute_filter,
                                                                              skip);

  bke::gather_attributes(mesh_attributes,
                         bke::AttrDomain::Point,
                         bke::AttrDomain::Point,
                         attribute_filter_with_skip,
                         vert_indices,
                         curves_attributes);

  mesh_attributes.foreach_attribute([&](const bke::AttributeIter &iter) {
    if (iter.domain == bke::AttrDomain::Point) {
      return;
    }
    if (iter.data_type == CD_PROP_STRING) {
      return;
    }
    if (attribute_filter_with_skip.allow_skip(iter.name)) {
      return;
    }

    const bke::GAttributeReader src = iter.get(bke::AttrDomain::Point);
    /* Some attributes might not exist if they were builtin on domains that don't have
     * any elements, i.e. a face attribute on the output of the line primitive node. */
    if (!src) {
      return;
    }
    bke::GSpanAttributeWriter dst = curves_attributes.lookup_or_add_for_write_only_span(
        iter.name, bke::AttrDomain::Point, iter.data_type);
    if (!dst) {
      return;
    }
    bke::attribute_math::gather(*src, vert_indices, dst.span);
    dst.finish();
  });

  debug_randomize_curve_order(&curves);

  return curves;
}

struct CurveFromEdgesOutput {
  /** The indices in the mesh for each control point of each result curves. */
  Vector<int> vert_indices;
  /** The first index of each curve in the result. */
  Vector<int> curve_offsets;
  /** A subset of curves that should be set cyclic. */
  IndexRange cyclic_curves;
};

BLI_NOINLINE static CurveFromEdgesOutput edges_to_curve_point_indices(const int verts_num,
                                                                      const Span<int2> edges)
{
  /* Compute the number of edges connecting to each vertex. */
  Array<int> neighbor_offsets_data(verts_num + 1, 0);
  offset_indices::build_reverse_offsets(edges.cast<int>(), neighbor_offsets_data);
  const OffsetIndices<int> neighbor_offsets(neighbor_offsets_data);

  /* Use as an index into the "neighbor group" for each vertex. */
  Array<int> used_slots(verts_num, 0);
  /* Calculate the indices of each vertex's neighboring edges. */
  Array<int> neighbors(edges.size() * 2);
  for (const int i : edges.index_range()) {
    const int v1 = edges[i][0];
    const int v2 = edges[i][1];
    neighbors[neighbor_offsets[v1].start() + used_slots[v1]] = v2;
    neighbors[neighbor_offsets[v2].start() + used_slots[v2]] = v1;
    used_slots[v1]++;
    used_slots[v2]++;
  }

  Vector<int> vert_indices;
  vert_indices.reserve(edges.size());
  Vector<int> curve_offsets;

  /* Now use the neighbor group offsets calculated above to count used edges at each vertex. */
  Array<int> unused_edges = std::move(used_slots);

  for (const int start_vert : IndexRange(verts_num)) {
    /* Don't start at vertices with two neighbors, which may become part of cyclic curves. */
    if (neighbor_offsets[start_vert].size() == 2) {
      continue;
    }

    /* The vertex has no connected edges, or they were already used. */
    if (unused_edges[start_vert] == 0) {
      continue;
    }

    for (const int neighbor : neighbors.as_span().slice(neighbor_offsets[start_vert])) {
      int current_vert = start_vert;
      int next_vert = neighbor;

      if (unused_edges[next_vert] == 0) {
        continue;
      }

      /* Start a new curve in the output. */
      curve_offsets.append(vert_indices.size());
      vert_indices.append(current_vert);

      /* Follow connected edges until we read a vertex with more than two connected edges. */
      while (true) {
        int last_vert = current_vert;
        current_vert = next_vert;

        vert_indices.append(current_vert);
        unused_edges[current_vert]--;
        unused_edges[last_vert]--;

        if (neighbor_offsets[current_vert].size() != 2) {
          break;
        }

        const int offset = neighbor_offsets[current_vert].start();
        const int next_a = neighbors[offset];
        const int next_b = neighbors[offset + 1];
        next_vert = (last_vert == next_a) ? next_b : next_a;
      }
    }
  }

  /* All curves added after this are cyclic. */
  const int cyclic_start = curve_offsets.size();

  /* All remaining edges are part of cyclic curves because
   * we skipped starting at vertices with two edges before. */
  for (const int start_vert : IndexRange(verts_num)) {
    if (unused_edges[start_vert] != 2) {
      continue;
    }

    int current_vert = start_vert;
    int next_vert = neighbors[neighbor_offsets[current_vert].start()];

    curve_offsets.append(vert_indices.size());
    vert_indices.append(current_vert);

    /* Follow connected edges until we loop back to the start vertex. */
    while (next_vert != start_vert) {
      const int last_vert = current_vert;
      current_vert = next_vert;

      vert_indices.append(current_vert);
      unused_edges[current_vert]--;
      unused_edges[last_vert]--;

      const int offset = neighbor_offsets[current_vert].start();
      const int next_a = neighbors[offset];
      const int next_b = neighbors[offset + 1];
      next_vert = (last_vert == next_a) ? next_b : next_a;
    }
  }

  const IndexRange cyclic_curves = curve_offsets.index_range().drop_front(cyclic_start);

  return {std::move(vert_indices), std::move(curve_offsets), cyclic_curves};
}

BLI_NOINLINE static bke::CurvesGeometry edges_to_curves_convert(
    const Mesh &mesh, const Span<int2> edges, const bke::AttributeFilter &attribute_filter)
{
  CurveFromEdgesOutput output = edges_to_curve_point_indices(mesh.verts_num, edges);
  return create_curve_from_vert_indices(mesh.attributes(),
                                        output.vert_indices,
                                        output.curve_offsets,
                                        output.cyclic_curves,
                                        attribute_filter);
}

bke::CurvesGeometry mesh_to_curve_convert(const Mesh &mesh,
                                          const IndexMask &selection,
                                          const bke::AttributeFilter &attribute_filter)
{
  const Span<int2> edges = mesh.edges();
  if (selection.size() == edges.size()) {
    return edges_to_curves_convert(mesh, edges, attribute_filter);
  }
  Array<int2> selected_edges(selection.size());
  array_utils::gather(edges, selection, selected_edges.as_mutable_span());
  return edges_to_curves_convert(mesh, selected_edges, attribute_filter);
}

}  // namespace blender::geometry

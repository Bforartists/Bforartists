/* SPDX-License-Identifier: GPL-2.0-or-later */

#include "BLI_array.hh"
#include "BLI_set.hh"
#include "BLI_string_ref.hh"
#include "BLI_task.hh"

#include "DNA_mesh_types.h"
#include "DNA_meshdata_types.h"

#include "BKE_attribute_access.hh"
#include "BKE_attribute_math.hh"
#include "BKE_geometry_set.hh"
#include "BKE_spline.hh"

#include "GEO_mesh_to_curve.hh"

namespace blender::geometry {

template<typename T>
static void copy_attribute_to_points(const VArray<T> &source_data,
                                     Span<int> map,
                                     MutableSpan<T> dest_data)
{
  for (const int point_index : map.index_range()) {
    const int vert_index = map[point_index];
    dest_data[point_index] = source_data[vert_index];
  }
}

static std::unique_ptr<CurveEval> create_curve_from_vert_indices(
    const MeshComponent &mesh_component, Span<Vector<int>> vert_indices, IndexRange cyclic_splines)
{
  std::unique_ptr<CurveEval> curve = std::make_unique<CurveEval>();
  curve->resize(vert_indices.size());

  MutableSpan<SplinePtr> splines = curve->splines();

  for (const int i : vert_indices.index_range()) {
    splines[i] = std::make_unique<PolySpline>();
    splines[i]->resize(vert_indices[i].size());
  }
  for (const int i : cyclic_splines) {
    splines[i]->set_cyclic(true);
  }

  Set<bke::AttributeIDRef> source_attribute_ids = mesh_component.attribute_ids();

  /* Copy builtin control point attributes. */
  if (source_attribute_ids.contains("tilt")) {
    const VArray<float> tilt_attribute = mesh_component.attribute_get_for_read<float>(
        "tilt", ATTR_DOMAIN_POINT, 0.0f);
    threading::parallel_for(splines.index_range(), 256, [&](IndexRange range) {
      for (const int i : range) {
        copy_attribute_to_points<float>(tilt_attribute, vert_indices[i], splines[i]->tilts());
      }
    });
    source_attribute_ids.remove_contained("tilt");
  }
  else {
    for (SplinePtr &spline : splines) {
      spline->tilts().fill(0.0f);
    }
  }

  if (source_attribute_ids.contains("radius")) {
    const VArray<float> radius_attribute = mesh_component.attribute_get_for_read<float>(
        "radius", ATTR_DOMAIN_POINT, 1.0f);
    threading::parallel_for(splines.index_range(), 256, [&](IndexRange range) {
      for (const int i : range) {
        copy_attribute_to_points<float>(radius_attribute, vert_indices[i], splines[i]->radii());
      }
    });
    source_attribute_ids.remove_contained("radius");
  }
  else {
    for (SplinePtr &spline : splines) {
      spline->radii().fill(1.0f);
    }
  }

  VArray<float3> mesh_positions = mesh_component.attribute_get_for_read(
      "position", ATTR_DOMAIN_POINT, float3(0));
  threading::parallel_for(splines.index_range(), 128, [&](IndexRange range) {
    for (const int i : range) {
      copy_attribute_to_points(mesh_positions, vert_indices[i], splines[i]->positions());
    }
  });

  for (const bke::AttributeIDRef &attribute_id : source_attribute_ids) {
    if (mesh_component.attribute_is_builtin(attribute_id)) {
      /* Don't copy attributes that are built-in on meshes but not on curves. */
      continue;
    }

    if (!attribute_id.should_be_kept()) {
      continue;
    }

    const fn::GVArray mesh_attribute = mesh_component.attribute_try_get_for_read(
        attribute_id, ATTR_DOMAIN_POINT);
    /* Some attributes might not exist if they were builtin attribute on domains that don't
     * have any elements, i.e. a face attribute on the output of the line primitive node. */
    if (!mesh_attribute) {
      continue;
    }

    const CustomDataType data_type = bke::cpp_type_to_custom_data_type(mesh_attribute.type());

    threading::parallel_for(splines.index_range(), 128, [&](IndexRange range) {
      for (const int i : range) {
        /* Create attribute on the spline points. */
        splines[i]->attributes.create(attribute_id, data_type);
        std::optional<fn::GMutableSpan> spline_attribute = splines[i]->attributes.get_for_write(
            attribute_id);
        BLI_assert(spline_attribute);

        /* Copy attribute based on the map for this spline. */
        attribute_math::convert_to_static_type(mesh_attribute.type(), [&](auto dummy) {
          using T = decltype(dummy);
          copy_attribute_to_points<T>(
              mesh_attribute.typed<T>(), vert_indices[i], spline_attribute->typed<T>());
        });
      }
    });
  }

  curve->assert_valid_point_attributes();
  return curve;
}

struct CurveFromEdgesOutput {
  /** The indices in the mesh for each control point of each result splines. */
  Vector<Vector<int>> vert_indices;
  /** A subset of splines that should be set cyclic. */
  IndexRange cyclic_splines;
};

static CurveFromEdgesOutput edges_to_curve_point_indices(Span<MVert> verts,
                                                         Span<std::pair<int, int>> edges)
{
  Vector<Vector<int>> vert_indices;

  /* Compute the number of edges connecting to each vertex. */
  Array<int> neighbor_count(verts.size(), 0);
  for (const std::pair<int, int> &edge : edges) {
    neighbor_count[edge.first]++;
    neighbor_count[edge.second]++;
  }

  /* Compute an offset into the array of neighbor edges based on the counts. */
  Array<int> neighbor_offsets(verts.size());
  int start = 0;
  for (const int i : verts.index_range()) {
    neighbor_offsets[i] = start;
    start += neighbor_count[i];
  }

  /* Use as an index into the "neighbor group" for each vertex. */
  Array<int> used_slots(verts.size(), 0);
  /* Calculate the indices of each vertex's neighboring edges. */
  Array<int> neighbors(edges.size() * 2);
  for (const int i : edges.index_range()) {
    const int v1 = edges[i].first;
    const int v2 = edges[i].second;
    neighbors[neighbor_offsets[v1] + used_slots[v1]] = v2;
    neighbors[neighbor_offsets[v2] + used_slots[v2]] = v1;
    used_slots[v1]++;
    used_slots[v2]++;
  }

  /* Now use the neighbor group offsets calculated above as a count used edges at each vertex. */
  Array<int> unused_edges = std::move(used_slots);

  for (const int start_vert : verts.index_range()) {
    /* The vertex will be part of a cyclic spline. */
    if (neighbor_count[start_vert] == 2) {
      continue;
    }

    /* The vertex has no connected edges, or they were already used. */
    if (unused_edges[start_vert] == 0) {
      continue;
    }

    for (const int i : IndexRange(neighbor_count[start_vert])) {
      int current_vert = start_vert;
      int next_vert = neighbors[neighbor_offsets[current_vert] + i];

      if (unused_edges[next_vert] == 0) {
        continue;
      }

      Vector<int> spline_indices;
      spline_indices.append(current_vert);

      /* Follow connected edges until we read a vertex with more than two connected edges. */
      while (true) {
        int last_vert = current_vert;
        current_vert = next_vert;

        spline_indices.append(current_vert);
        unused_edges[current_vert]--;
        unused_edges[last_vert]--;

        if (neighbor_count[current_vert] != 2) {
          break;
        }

        const int offset = neighbor_offsets[current_vert];
        const int next_a = neighbors[offset];
        const int next_b = neighbors[offset + 1];
        next_vert = (last_vert == next_a) ? next_b : next_a;
      }

      vert_indices.append(std::move(spline_indices));
    }
  }

  /* All splines added after this are cyclic. */
  const int cyclic_start = vert_indices.size();

  /* All remaining edges are part of cyclic splines (we skipped vertices with two edges before). */
  for (const int start_vert : verts.index_range()) {
    if (unused_edges[start_vert] != 2) {
      continue;
    }

    int current_vert = start_vert;
    int next_vert = neighbors[neighbor_offsets[current_vert]];

    Vector<int> spline_indices;

    spline_indices.append(current_vert);

    /* Follow connected edges until we loop back to the start vertex. */
    while (next_vert != start_vert) {
      const int last_vert = current_vert;
      current_vert = next_vert;

      spline_indices.append(current_vert);
      unused_edges[current_vert]--;
      unused_edges[last_vert]--;

      const int offset = neighbor_offsets[current_vert];
      const int next_a = neighbors[offset];
      const int next_b = neighbors[offset + 1];
      next_vert = (last_vert == next_a) ? next_b : next_a;
    }

    vert_indices.append(std::move(spline_indices));
  }

  const int final_size = vert_indices.size();

  return {std::move(vert_indices), IndexRange(cyclic_start, final_size - cyclic_start)};
}

/**
 * Get a separate array of the indices for edges in a selection (a boolean attribute).
 * This helps to make the above algorithm simpler by removing the need to check for selection
 * in many places.
 */
static Vector<std::pair<int, int>> get_selected_edges(const Mesh &mesh, const IndexMask selection)
{
  Vector<std::pair<int, int>> selected_edges;
  for (const int i : selection) {
    selected_edges.append({mesh.medge[i].v1, mesh.medge[i].v2});
  }
  return selected_edges;
}

std::unique_ptr<CurveEval> mesh_to_curve_convert(const MeshComponent &mesh_component,
                                                 const IndexMask selection)
{
  const Mesh &mesh = *mesh_component.get_for_read();
  Vector<std::pair<int, int>> selected_edges = get_selected_edges(*mesh_component.get_for_read(),
                                                                  selection);
  CurveFromEdgesOutput output = edges_to_curve_point_indices({mesh.mvert, mesh.totvert},
                                                             selected_edges);

  return create_curve_from_vert_indices(
      mesh_component, output.vert_indices, output.cyclic_splines);
}

}  // namespace blender::geometry

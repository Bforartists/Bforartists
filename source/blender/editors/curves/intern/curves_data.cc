/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#include "BKE_curves.hh"

#include "DNA_object_types.h"

#include "ED_curves.hh"
#include "ED_transverts.hh"

namespace blender::ed::curves {

Vector<MutableSpan<float3>> get_curves_positions_for_write(bke::CurvesGeometry &curves)
{
  Vector<MutableSpan<float3>> positions_per_attribute;
  positions_per_attribute.append(curves.positions_for_write());
  if (curves.has_curve_with_type(CURVE_TYPE_BEZIER)) {
    positions_per_attribute.append(curves.handle_positions_left_for_write());
    positions_per_attribute.append(curves.handle_positions_right_for_write());
  }
  return positions_per_attribute;
}

void transverts_from_curves_positions_create(bke::CurvesGeometry &curves,
                                             TransVertStore *tvs,
                                             const bool skip_handles)
{
  const Span<StringRef> selection_names = ed::curves::get_curves_selection_attribute_names(curves);

  IndexMaskMemory memory;
  std::array<IndexMask, 3> selection;
  for (const int i : selection_names.index_range()) {
    selection[i] = ed::curves::retrieve_selected_points(curves, selection_names[i], memory);
  }

  if (skip_handles) {
    /* When the control point is selected, both handles are ignored. */
    selection[1] = IndexMask::from_difference(selection[1], selection[0], memory);
    selection[2] = IndexMask::from_difference(selection[2], selection[0], memory);
  }

  const int size = selection[0].size() + selection[1].size() + selection[2].size();
  if (size == 0) {
    return;
  }

  tvs->transverts = static_cast<TransVert *>(MEM_calloc_arrayN(size, sizeof(TransVert), __func__));
  tvs->transverts_tot = size;

  int offset = 0;
  const Vector<MutableSpan<float3>> positions = ed::curves::get_curves_positions_for_write(curves);
  for (const int attribute_i : positions.index_range()) {
    selection[attribute_i].foreach_index(GrainSize(1024), [&](const int64_t i, const int64_t pos) {
      TransVert &tv = tvs->transverts[pos + offset];
      tv.loc = positions[attribute_i][i];
      tv.flag = SELECT;
      copy_v3_v3(tv.oldloc, tv.loc);
    });

    offset += selection[attribute_i].size();
  }
}

float (*point_normals_array_create(const Curves *curves_id))[3]
{
  using namespace blender;
  const bke::CurvesGeometry &curves = curves_id->geometry.wrap();
  const int size = curves.points_num();
  float3 *data = static_cast<float3 *>(MEM_malloc_arrayN(size, sizeof(float3), __func__));
  bke::curves_normals_point_domain_calc(curves, {data, size});
  return reinterpret_cast<float(*)[3]>(data);
}

}  // namespace blender::ed::curves

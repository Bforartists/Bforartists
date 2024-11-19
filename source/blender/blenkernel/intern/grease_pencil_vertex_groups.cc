/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup bke
 */

#include "DNA_meshdata_types.h"

#include "BLI_listbase.h"
#include "BLI_set.hh"
#include "BLI_string.h"

#include "BKE_curves.hh"
#include "BKE_deform.hh"
#include "BKE_grease_pencil.hh"
#include "BKE_grease_pencil_vertex_groups.hh"

namespace blender::bke::greasepencil {

/* ------------------------------------------------------------------- */
/** \name Vertex groups in drawings
 * \{ */

void validate_drawing_vertex_groups(GreasePencil &grease_pencil)
{
  Set<std::string> valid_names;
  LISTBASE_FOREACH (const bDeformGroup *, defgroup, &grease_pencil.vertex_group_names) {
    valid_names.add_new(defgroup->name);
  }

  for (GreasePencilDrawingBase *base : grease_pencil.drawings()) {
    if (base->type != GP_DRAWING) {
      continue;
    }
    Drawing &drawing = reinterpret_cast<GreasePencilDrawing *>(base)->wrap();

    /* Remove unknown vertex groups. */
    CurvesGeometry &curves = drawing.strokes_for_write();
    int defgroup_index = 0;
    LISTBASE_FOREACH_MUTABLE (bDeformGroup *, defgroup, &curves.vertex_group_names) {
      if (!valid_names.contains(defgroup->name)) {
        remove_defgroup_index(curves.deform_verts_for_write(), defgroup_index);

        BLI_remlink(&curves.vertex_group_names, defgroup);
        MEM_SAFE_FREE(defgroup);
      }

      ++defgroup_index;
    }
  }
}

int ensure_vertex_group(const StringRef name, ListBase &vertex_group_names)
{
  int def_nr = BKE_defgroup_name_index(&vertex_group_names, name);
  if (def_nr < 0) {
    bDeformGroup *defgroup = MEM_cnew<bDeformGroup>(__func__);
    name.copy(defgroup->name);
    BLI_addtail(&vertex_group_names, defgroup);
    def_nr = BLI_listbase_count(&vertex_group_names) - 1;
    BLI_assert(def_nr >= 0);
  }
  return def_nr;
}

void assign_to_vertex_group_from_mask(bke::CurvesGeometry &curves,
                                      const IndexMask &mask,
                                      const StringRef name,
                                      const float weight)
{
  if (mask.is_empty()) {
    return;
  }

  ListBase &vertex_group_names = curves.vertex_group_names;
  /* Look for existing group, otherwise lazy-initialize if any vertex is selected. */
  int def_nr = BKE_defgroup_name_index(&vertex_group_names, name);

  /* Lazily add the vertex group if any vertex is selected. */
  if (def_nr < 0) {
    bDeformGroup *defgroup = MEM_cnew<bDeformGroup>(__func__);
    name.copy(defgroup->name);
    BLI_addtail(&vertex_group_names, defgroup);
    def_nr = BLI_listbase_count(&vertex_group_names) - 1;
    BLI_assert(def_nr >= 0);
  }

  const MutableSpan<MDeformVert> dverts = curves.deform_verts_for_write();
  mask.foreach_index([&](const int point_i) {
    if (MDeformWeight *dw = BKE_defvert_ensure_index(&dverts[point_i], def_nr)) {
      dw->weight = weight;
    }
  });
}

void assign_to_vertex_group(Drawing &drawing, const StringRef name, const float weight)
{

  bke::CurvesGeometry &curves = drawing.strokes_for_write();
  ListBase &vertex_group_names = curves.vertex_group_names;

  const bke::AttributeAccessor attributes = curves.attributes();
  const VArray<bool> selection = *attributes.lookup_or_default<bool>(
      ".selection", bke::AttrDomain::Point, true);

  /* Look for existing group, otherwise lazy-initialize if any vertex is selected. */
  int def_nr = BKE_defgroup_name_index(&vertex_group_names, name);

  const MutableSpan<MDeformVert> dverts = curves.deform_verts_for_write();
  for (const int i : dverts.index_range()) {
    if (selection[i]) {
      /* Lazily add the vertex group if any vertex is selected. */
      if (def_nr < 0) {
        bDeformGroup *defgroup = MEM_cnew<bDeformGroup>(__func__);
        name.copy(defgroup->name);

        BLI_addtail(&vertex_group_names, defgroup);
        def_nr = BLI_listbase_count(&vertex_group_names) - 1;
        BLI_assert(def_nr >= 0);
      }

      MDeformWeight *dw = BKE_defvert_ensure_index(&dverts[i], def_nr);
      if (dw) {
        dw->weight = weight;
      }
    }
  }
}

bool remove_from_vertex_group(Drawing &drawing, const StringRef name, const bool use_selection)
{
  bool changed = false;
  bke::CurvesGeometry &curves = drawing.strokes_for_write();
  ListBase &vertex_group_names = curves.vertex_group_names;

  const int def_nr = BKE_defgroup_name_index(&vertex_group_names, name);
  if (def_nr < 0) {
    /* No vertices assigned to the group in this drawing. */
    return false;
  }

  const MutableSpan<MDeformVert> dverts = curves.deform_verts_for_write();
  const bke::AttributeAccessor attributes = curves.attributes();
  const VArray<bool> selection = *attributes.lookup_or_default<bool>(
      ".selection", bke::AttrDomain::Point, true);
  for (const int i : dverts.index_range()) {
    if (!use_selection || selection[i]) {
      MDeformVert *dv = &dverts[i];
      MDeformWeight *dw = BKE_defvert_find_index(dv, def_nr);
      BKE_defvert_remove_group(dv, dw);

      /* Adjust remaining vertex group indices. */
      for (const int j : IndexRange(dv->totweight)) {
        if (dv->dw[j].def_nr > def_nr) {
          dv->dw[j].def_nr--;
        }
      }

      changed = true;
    }
  }
  return changed;
}

void clear_vertex_groups(GreasePencil &grease_pencil)
{
  for (GreasePencilDrawingBase *base : grease_pencil.drawings()) {
    if (base->type != GP_DRAWING) {
      continue;
    }
    Drawing &drawing = reinterpret_cast<GreasePencilDrawing *>(base)->wrap();
    bke::CurvesGeometry &curves = drawing.strokes_for_write();

    for (MDeformVert &dvert : curves.deform_verts_for_write()) {
      BKE_defvert_clear(&dvert);
    }
  }
}

void select_from_group(Drawing &drawing,
                       const AttrDomain selection_domain,
                       const StringRef name,
                       const bool select)
{

  bke::CurvesGeometry &curves = drawing.strokes_for_write();
  ListBase &vertex_group_names = curves.vertex_group_names;

  const int def_nr = BKE_defgroup_name_index(&vertex_group_names, name);
  if (def_nr < 0) {
    /* No vertices assigned to the group in this drawing. */
    return;
  }

  const Span<MDeformVert> dverts = curves.deform_verts_for_write();
  if (dverts.is_empty()) {
    return;
  }

  MutableAttributeAccessor attributes = curves.attributes_for_write();
  const int num_elements = attributes.domain_size(selection_domain);
  SpanAttributeWriter<bool> selection = attributes.lookup_or_add_for_write_span<bool>(
      ".selection",
      selection_domain,
      bke::AttributeInitVArray(VArray<bool>::ForSingle(true, num_elements)));

  switch (selection_domain) {
    case AttrDomain::Point:
      threading::parallel_for(curves.points_range(), 4096, [&](const IndexRange range) {
        for (const int point_i : range) {
          if (BKE_defvert_find_index(&dverts[point_i], def_nr)) {
            selection.span[point_i] = select;
          }
        }
      });
      break;
    case AttrDomain::Curve: {
      const OffsetIndices<int> points_by_curve = curves.points_by_curve();
      threading::parallel_for(curves.curves_range(), 1024, [&](const IndexRange range) {
        for (const int curve_i : range) {
          const IndexRange points = points_by_curve[curve_i];
          bool any_point_in_group = false;
          for (const int point_i : points) {
            if (BKE_defvert_find_index(&dverts[point_i], def_nr)) {
              any_point_in_group = true;
              break;
            }
          }
          if (any_point_in_group) {
            selection.span[curve_i] = select;
          }
        }
      });
      break;
    }

    default:
      BLI_assert_unreachable();
      break;
  }

  selection.finish();
}

/** \} */

}  // namespace blender::bke::greasepencil

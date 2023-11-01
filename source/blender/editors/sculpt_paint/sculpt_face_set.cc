/* SPDX-FileCopyrightText: 2020 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup edsculpt
 */

#include <cmath>
#include <cstdlib>
#include <queue>

#include "MEM_guardedalloc.h"

#include "BLI_array.hh"
#include "BLI_bit_vector.hh"
#include "BLI_function_ref.hh"
#include "BLI_hash.h"
#include "BLI_math_matrix.h"
#include "BLI_math_vector.h"
#include "BLI_math_vector.hh"
#include "BLI_math_vector_types.hh"
#include "BLI_span.hh"
#include "BLI_task.h"
#include "BLI_task.hh"
#include "BLI_vector.hh"

#include "DNA_brush_types.h"
#include "DNA_customdata_types.h"
#include "DNA_mesh_types.h"
#include "DNA_meshdata_types.h"
#include "DNA_object_types.h"
#include "DNA_scene_types.h"

#include "BKE_attribute.hh"
#include "BKE_ccg.h"
#include "BKE_colortools.h"
#include "BKE_context.h"
#include "BKE_customdata.h"
#include "BKE_mesh.hh"
#include "BKE_mesh_fair.hh"
#include "BKE_mesh_mapping.hh"
#include "BKE_object.hh"
#include "BKE_paint.hh"
#include "BKE_pbvh_api.hh"

#include "DEG_depsgraph.hh"

#include "WM_api.hh"
#include "WM_types.hh"

#include "ED_sculpt.hh"

#include "sculpt_intern.hh"

#include "RNA_access.hh"
#include "RNA_define.hh"

#include "bmesh.h"

using blender::Array;
using blender::float3;
using blender::Vector;

/* Utils. */

int ED_sculpt_face_sets_find_next_available_id(Mesh *mesh)
{
  const int *face_sets = static_cast<const int *>(
      CustomData_get_layer_named(&mesh->face_data, CD_PROP_INT32, ".sculpt_face_set"));
  if (!face_sets) {
    return SCULPT_FACE_SET_NONE;
  }

  int next_face_set_id = 0;
  for (int i = 0; i < mesh->faces_num; i++) {
    next_face_set_id = max_ii(next_face_set_id, face_sets[i]);
  }
  next_face_set_id++;

  return next_face_set_id;
}

void ED_sculpt_face_sets_initialize_none_to_id(Mesh *mesh, const int new_id)
{
  int *face_sets = static_cast<int *>(CustomData_get_layer_named_for_write(
      &mesh->face_data, CD_PROP_INT32, ".sculpt_face_set", mesh->faces_num));
  if (!face_sets) {
    return;
  }

  for (int i = 0; i < mesh->faces_num; i++) {
    if (face_sets[i] == SCULPT_FACE_SET_NONE) {
      face_sets[i] = new_id;
    }
  }
}

int ED_sculpt_face_sets_active_update_and_get(bContext *C, Object *ob, const float mval[2])
{
  SculptSession *ss = ob->sculpt;
  if (!ss) {
    return SCULPT_FACE_SET_NONE;
  }

  SculptCursorGeometryInfo gi;
  if (!SCULPT_cursor_geometry_info_update(C, &gi, mval, false)) {
    return SCULPT_FACE_SET_NONE;
  }

  return SCULPT_active_face_set_get(ss);
}

/* Draw Face Sets Brush. */

constexpr float FACE_SET_BRUSH_MIN_FADE = 0.05f;

static void do_draw_face_sets_brush_faces(Object *ob, const Brush *brush, PBVHNode *node)
{
  using namespace blender;

  SculptSession *ss = ob->sculpt;

  BLI_assert(BKE_pbvh_type(ss->pbvh) == PBVH_FACES);

  const float bstrength = ss->cache->bstrength;
  const int thread_id = BLI_task_parallel_thread_id(nullptr);

  SculptBrushTest test;
  SculptBrushTestFn sculpt_brush_test_sq_fn = SCULPT_brush_test_init_with_falloff_shape(
      ss, &test, brush->falloff_shape);

  const Span<float3> positions(
      reinterpret_cast<const float3 *>(SCULPT_mesh_deformed_positions_get(ss)),
      SCULPT_vertex_count_get(ss));

  AutomaskingNodeData automask_data;
  SCULPT_automasking_node_begin(ob, ss, ss->cache->automasking, &automask_data, node);

  bool changed = false;

  PBVHVertexIter vd;
  BKE_pbvh_vertex_iter_begin (ss->pbvh, node, vd, PBVH_ITER_UNIQUE) {
    SCULPT_automasking_node_update(ss, &automask_data, &vd);

    for (const int face_i : ss->pmap[vd.index]) {
      const blender::IndexRange face = ss->faces[face_i];

      const float3 poly_center = bke::mesh::face_center_calc(positions,
                                                             ss->corner_verts.slice(face));

      if (!sculpt_brush_test_sq_fn(&test, poly_center)) {
        continue;
      }
      const bool face_hidden = ss->hide_poly && ss->hide_poly[face_i];
      if (face_hidden) {
        continue;
      }
      const float fade = bstrength * SCULPT_brush_strength_factor(ss,
                                                                  brush,
                                                                  vd.co,
                                                                  sqrtf(test.dist),
                                                                  vd.no,
                                                                  vd.fno,
                                                                  vd.mask,
                                                                  vd.vertex,
                                                                  thread_id,
                                                                  &automask_data);

      if (fade > FACE_SET_BRUSH_MIN_FADE) {
        ss->face_sets[face_i] = ss->cache->paint_face_set;
        changed = true;
      }
    }
  }
  BKE_pbvh_vertex_iter_end;

  if (changed) {
    SCULPT_undo_push_node(ob, node, SCULPT_UNDO_FACE_SETS);
  }
}

static void do_draw_face_sets_brush_grids(Object *ob, const Brush *brush, PBVHNode *node)
{
  using namespace blender;

  SculptSession *ss = ob->sculpt;

  BLI_assert(BKE_pbvh_type(ss->pbvh) == PBVH_GRIDS);

  const float bstrength = ss->cache->bstrength;
  const int thread_id = BLI_task_parallel_thread_id(nullptr);

  SculptBrushTest test;
  SculptBrushTestFn sculpt_brush_test_sq_fn = SCULPT_brush_test_init_with_falloff_shape(
      ss, &test, brush->falloff_shape);

  AutomaskingNodeData automask_data;
  SCULPT_automasking_node_begin(ob, ss, ss->cache->automasking, &automask_data, node);

  bool changed = false;

  PBVHVertexIter vd;
  BKE_pbvh_vertex_iter_begin (ss->pbvh, node, vd, PBVH_ITER_UNIQUE) {
    SCULPT_automasking_node_update(ss, &automask_data, &vd);

    if (!sculpt_brush_test_sq_fn(&test, vd.co)) {
      continue;
    }
    const float fade = bstrength * SCULPT_brush_strength_factor(ss,
                                                                brush,
                                                                vd.co,
                                                                sqrtf(test.dist),
                                                                vd.no,
                                                                vd.fno,
                                                                vd.mask,
                                                                vd.vertex,
                                                                thread_id,
                                                                &automask_data);

    if (fade > FACE_SET_BRUSH_MIN_FADE) {
      SCULPT_vertex_face_set_set(ss, vd.vertex, ss->cache->paint_face_set);
      changed = true;
    }
  }
  BKE_pbvh_vertex_iter_end;

  if (changed) {
    SCULPT_undo_push_node(ob, node, SCULPT_UNDO_FACE_SETS);
  }
}

static void do_draw_face_sets_brush_bmesh(Object *ob, const Brush *brush, PBVHNode *node)
{
  using namespace blender;

  SculptSession *ss = ob->sculpt;

  BLI_assert(BKE_pbvh_type(ss->pbvh) == PBVH_BMESH);

  const float bstrength = ss->cache->bstrength;
  const int thread_id = BLI_task_parallel_thread_id(nullptr);

  SculptBrushTest test;
  SculptBrushTestFn sculpt_brush_test_sq_fn = SCULPT_brush_test_init_with_falloff_shape(
      ss, &test, brush->falloff_shape);

  /* Disable auto-masking code path which rely on an undo step to access original data.
   *
   * This is because the dynamic topology uses BMesh Log based undo system, which creates a single
   * node for the undo step, and its type could be different for the needs of the brush undo and
   * the original data access.
   *
   * For the brushes like Draw the ss->cache->automasking is set to nullptr at the first step of
   * the brush, as there is an explicit check there for the brushes which support dynamic topology.
   * Do it locally here for the Draw Face Set brush here, to mimic the behavior of the other
   * brushes but without marking the brush as supporting dynamic topology. */
  AutomaskingNodeData automask_data;
  SCULPT_automasking_node_begin(ob, ss, nullptr, &automask_data, node);

  bool changed = false;

  const int cd_offset = CustomData_get_offset_named(
      &ss->bm->pdata, CD_PROP_INT32, ".sculpt_face_set");

  for (BMFace *f : BKE_pbvh_bmesh_node_faces(node)) {
    if (BM_elem_flag_test(f, BM_ELEM_HIDDEN)) {
      continue;
    }

    float3 face_center;
    BM_face_calc_center_median(f, face_center);

    const BMLoop *l_iter = f->l_first = BM_FACE_FIRST_LOOP(f);
    do {
      if (!sculpt_brush_test_sq_fn(&test, l_iter->v->co)) {
        continue;
      }

      BMVert *vert = l_iter->v;

      /* There is no need to update the automasking data as it is disabled above. Additionally,
       * there is no access to the PBVHVertexIter as iteration happens over faces.
       *
       * The full auto-masking support would be very good to be implemented here, so keeping the
       * typical code flow for it here for the reference, and ease of looking at what needs to be
       * done for such integration.
       *
       * SCULPT_automasking_node_update(ss, &automask_data, &vd); */

      const float fade = bstrength *
                         SCULPT_brush_strength_factor(ss,
                                                      brush,
                                                      face_center,
                                                      sqrtf(test.dist),
                                                      f->no,
                                                      f->no,
                                                      0.0f,
                                                      BKE_pbvh_make_vref(intptr_t(vert)),
                                                      thread_id,
                                                      &automask_data);

      if (fade <= FACE_SET_BRUSH_MIN_FADE) {
        continue;
      }

      int &fset = *static_cast<int *>(POINTER_OFFSET(f->head.data, cd_offset));
      fset = ss->cache->paint_face_set;
      changed = true;
      break;

    } while ((l_iter = l_iter->next) != f->l_first);
  }

  if (changed) {
    SCULPT_undo_push_node(ob, node, SCULPT_UNDO_FACE_SETS);
  }
}

static void do_draw_face_sets_brush_task(Object *ob, const Brush *brush, PBVHNode *node)
{
  const SculptSession *ss = ob->sculpt;

  switch (BKE_pbvh_type(ss->pbvh)) {
    case PBVH_FACES:
      do_draw_face_sets_brush_faces(ob, brush, node);
      break;

    case PBVH_GRIDS:
      do_draw_face_sets_brush_grids(ob, brush, node);
      break;

    case PBVH_BMESH:
      do_draw_face_sets_brush_bmesh(ob, brush, node);
      break;
  }
}

static void do_relax_face_sets_brush_task(Object *ob,
                                          const Brush *brush,
                                          const int iteration,
                                          PBVHNode *node)
{
  SculptSession *ss = ob->sculpt;
  float bstrength = ss->cache->bstrength;

  PBVHVertexIter vd;

  SculptBrushTest test;
  SculptBrushTestFn sculpt_brush_test_sq_fn = SCULPT_brush_test_init_with_falloff_shape(
      ss, &test, brush->falloff_shape);

  const bool relax_face_sets = !(ss->cache->iteration_count % 3 == 0);
  /* This operations needs a strength tweak as the relax deformation is too weak by default. */
  if (relax_face_sets && iteration < 2) {
    bstrength *= 1.5f;
  }

  const int thread_id = BLI_task_parallel_thread_id(nullptr);
  AutomaskingNodeData automask_data;
  SCULPT_automasking_node_begin(ob, ss, ss->cache->automasking, &automask_data, node);

  BKE_pbvh_vertex_iter_begin (ss->pbvh, node, vd, PBVH_ITER_UNIQUE) {
    SCULPT_automasking_node_update(ss, &automask_data, &vd);

    if (!sculpt_brush_test_sq_fn(&test, vd.co)) {
      continue;
    }
    if (relax_face_sets == SCULPT_vertex_has_unique_face_set(ss, vd.vertex)) {
      continue;
    }

    const float fade = bstrength * SCULPT_brush_strength_factor(ss,
                                                                brush,
                                                                vd.co,
                                                                sqrtf(test.dist),
                                                                vd.no,
                                                                vd.fno,
                                                                vd.mask,
                                                                vd.vertex,
                                                                thread_id,
                                                                &automask_data);

    SCULPT_relax_vertex(ss, &vd, fade * bstrength, relax_face_sets, vd.co);
    if (vd.is_mesh) {
      BKE_pbvh_vert_tag_update_normal(ss->pbvh, vd.vertex);
    }
  }
  BKE_pbvh_vertex_iter_end;
}

void SCULPT_do_draw_face_sets_brush(Sculpt *sd, Object *ob, Span<PBVHNode *> nodes)
{
  using namespace blender;
  SculptSession *ss = ob->sculpt;
  Brush *brush = BKE_paint_brush(&sd->paint);

  BKE_curvemapping_init(brush->curve);

  TaskParallelSettings settings;
  BKE_pbvh_parallel_range_settings(&settings, true, nodes.size());
  if (ss->cache->alt_smooth) {
    SCULPT_boundary_info_ensure(ob);
    for (int i = 0; i < 4; i++) {
      threading::parallel_for(nodes.index_range(), 1, [&](const IndexRange range) {
        for (const int i : range) {
          do_relax_face_sets_brush_task(ob, brush, i, nodes[i]);
        }
      });
    }
  }
  else {
    threading::parallel_for(nodes.index_range(), 1, [&](const IndexRange range) {
      for (const int i : range) {
        do_draw_face_sets_brush_task(ob, brush, nodes[i]);
      }
    });
  }
}

/* Face Sets Operators */

enum eSculptFaceGroupsCreateModes {
  SCULPT_FACE_SET_MASKED = 0,
  SCULPT_FACE_SET_VISIBLE = 1,
  SCULPT_FACE_SET_ALL = 2,
  SCULPT_FACE_SET_SELECTION = 3,
};

static EnumPropertyItem prop_sculpt_face_set_create_types[] = {
    {
        SCULPT_FACE_SET_MASKED,
        "MASKED",
        0,
        "Face Set from Masked",
        "Create a new Face Set from the masked faces",
    },
    {
        SCULPT_FACE_SET_VISIBLE,
        "VISIBLE",
        0,
        "Face Set from Visible",
        "Create a new Face Set from the visible vertices",
    },
    {
        SCULPT_FACE_SET_ALL,
        "ALL",
        0,
        "Face Set Full Mesh",
        "Create an unique Face Set with all faces in the sculpt",
    },
    {
        SCULPT_FACE_SET_SELECTION,
        "SELECTION",
        0,
        "Face Set from Edit Mode Selection",
        "Create an Face Set corresponding to the Edit Mode face selection",
    },
    {0, nullptr, 0, nullptr, nullptr},
};

static int sculpt_face_set_create_exec(bContext *C, wmOperator *op)
{
  using namespace blender;
  Object *ob = CTX_data_active_object(C);
  SculptSession *ss = ob->sculpt;
  Depsgraph *depsgraph = CTX_data_depsgraph_pointer(C);

  const int mode = RNA_enum_get(op->ptr, "mode");

  /* Dyntopo not supported. */
  if (BKE_pbvh_type(ss->pbvh) == PBVH_BMESH) {
    return OPERATOR_CANCELLED;
  }

  ss->face_sets = BKE_sculpt_face_sets_ensure(ob);
  Mesh *mesh = static_cast<Mesh *>(ob->data);

  BKE_sculpt_update_object_for_edit(depsgraph, ob, true, mode == SCULPT_FACE_SET_MASKED, false);

  const int tot_vert = SCULPT_vertex_count_get(ss);
  float threshold = 0.5f;

  PBVH *pbvh = ob->sculpt->pbvh;
  Vector<PBVHNode *> nodes = blender::bke::pbvh::search_gather(pbvh, {});

  if (nodes.is_empty()) {
    return OPERATOR_CANCELLED;
  }

  SCULPT_undo_push_begin(ob, op);
  for (PBVHNode *node : nodes) {
    SCULPT_undo_push_node(ob, node, SCULPT_UNDO_FACE_SETS);
  }

  const int next_face_set = SCULPT_face_set_next_available_get(ss);

  if (mode == SCULPT_FACE_SET_MASKED) {
    for (int i = 0; i < tot_vert; i++) {
      PBVHVertRef vertex = BKE_pbvh_index_to_vertex(ss->pbvh, i);

      if (SCULPT_vertex_mask_get(ss, vertex) >= threshold && SCULPT_vertex_visible_get(ss, vertex))
      {
        SCULPT_vertex_face_set_set(ss, vertex, next_face_set);
      }
    }
  }

  if (mode == SCULPT_FACE_SET_VISIBLE) {

    /* If all vertices in the sculpt are visible, create the new face set and update the default
     * color. This way the new face set will be white, which is a quick way of disabling all face
     * sets and the performance hit of rendering the overlay. */
    bool all_visible = true;
    for (int i = 0; i < tot_vert; i++) {
      PBVHVertRef vertex = BKE_pbvh_index_to_vertex(ss->pbvh, i);

      if (!SCULPT_vertex_visible_get(ss, vertex)) {
        all_visible = false;
        break;
      }
    }

    if (all_visible) {
      mesh->face_sets_color_default = next_face_set;
    }

    for (int i = 0; i < tot_vert; i++) {
      PBVHVertRef vertex = BKE_pbvh_index_to_vertex(ss->pbvh, i);

      if (SCULPT_vertex_visible_get(ss, vertex)) {
        SCULPT_vertex_face_set_set(ss, vertex, next_face_set);
      }
    }
  }

  if (mode == SCULPT_FACE_SET_ALL) {
    for (int i = 0; i < tot_vert; i++) {
      PBVHVertRef vertex = BKE_pbvh_index_to_vertex(ss->pbvh, i);

      SCULPT_vertex_face_set_set(ss, vertex, next_face_set);
    }
  }

  if (mode == SCULPT_FACE_SET_SELECTION) {
    const bke::AttributeAccessor attributes = mesh->attributes();
    const VArraySpan<bool> select_poly = *attributes.lookup_or_default<bool>(
        ".select_poly", ATTR_DOMAIN_FACE, false);
    threading::parallel_for(select_poly.index_range(), 4096, [&](const IndexRange range) {
      for (const int i : range) {
        if (select_poly[i]) {
          ss->face_sets[i] = next_face_set;
        }
      }
    });
  }

  for (PBVHNode *node : nodes) {
    BKE_pbvh_node_mark_redraw(node);
  }

  SCULPT_undo_push_end(ob);

  SCULPT_tag_update_overlays(C);

  return OPERATOR_FINISHED;
}

void SCULPT_OT_face_sets_create(wmOperatorType *ot)
{
  /* identifiers */
  ot->name = "Create Face Set";
  ot->idname = "SCULPT_OT_face_sets_create";
  ot->description = "Create a new Face Set";

  /* api callbacks */
  ot->exec = sculpt_face_set_create_exec;
  ot->poll = SCULPT_mode_poll;

  ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;

  RNA_def_enum(
      ot->srna, "mode", prop_sculpt_face_set_create_types, SCULPT_FACE_SET_MASKED, "Mode", "");
}

enum eSculptFaceSetsInitMode {
  SCULPT_FACE_SETS_FROM_LOOSE_PARTS = 0,
  SCULPT_FACE_SETS_FROM_MATERIALS = 1,
  SCULPT_FACE_SETS_FROM_NORMALS = 2,
  SCULPT_FACE_SETS_FROM_UV_SEAMS = 3,
  SCULPT_FACE_SETS_FROM_CREASES = 4,
  SCULPT_FACE_SETS_FROM_SHARP_EDGES = 5,
  SCULPT_FACE_SETS_FROM_BEVEL_WEIGHT = 6,
  SCULPT_FACE_SETS_FROM_FACE_SET_BOUNDARIES = 8,
};

static EnumPropertyItem prop_sculpt_face_sets_init_types[] = {
    {
        SCULPT_FACE_SETS_FROM_LOOSE_PARTS,
        "LOOSE_PARTS",
        0,
        "Face Sets from Loose Parts",
        "Create a Face Set per loose part in the mesh",
    },
    {
        SCULPT_FACE_SETS_FROM_MATERIALS,
        "MATERIALS",
        0,
        "Face Sets from Material Slots",
        "Create a Face Set per Material Slot",
    },
    {
        SCULPT_FACE_SETS_FROM_NORMALS,
        "NORMALS",
        0,
        "Face Sets from Mesh Normals",
        "Create Face Sets for Faces that have similar normal",
    },
    {
        SCULPT_FACE_SETS_FROM_UV_SEAMS,
        "UV_SEAMS",
        0,
        "Face Sets from UV Seams",
        "Create Face Sets using UV Seams as boundaries",
    },
    {
        SCULPT_FACE_SETS_FROM_CREASES,
        "CREASES",
        0,
        "Face Sets from Edge Creases",
        "Create Face Sets using Edge Creases as boundaries",
    },
    {
        SCULPT_FACE_SETS_FROM_BEVEL_WEIGHT,
        "BEVEL_WEIGHT",
        0,
        "Face Sets from Bevel Weight",
        "Create Face Sets using Bevel Weights as boundaries",
    },
    {
        SCULPT_FACE_SETS_FROM_SHARP_EDGES,
        "SHARP_EDGES",
        0,
        "Face Sets from Sharp Edges",
        "Create Face Sets using Sharp Edges as boundaries",
    },

    {
        SCULPT_FACE_SETS_FROM_FACE_SET_BOUNDARIES,
        "FACE_SET_BOUNDARIES",
        0,
        "Face Sets from Face Set Boundaries",
        "Create a Face Set per isolated Face Set",
    },

    {0, nullptr, 0, nullptr, nullptr},
};

using FaceSetsFloodFillFn = blender::FunctionRef<bool(int from_face, int edge, int to_face)>;

static void sculpt_face_sets_init_flood_fill(Object *ob, const FaceSetsFloodFillFn &test_fn)
{
  using namespace blender;
  SculptSession *ss = ob->sculpt;
  Mesh *mesh = static_cast<Mesh *>(ob->data);

  BitVector<> visited_faces(mesh->faces_num, false);

  int *face_sets = ss->face_sets;

  const Span<int2> edges = mesh->edges();
  const OffsetIndices faces = mesh->faces();
  const Span<int> corner_edges = mesh->corner_edges();

  if (ss->epmap.is_empty()) {
    ss->epmap = bke::mesh::build_edge_to_face_map(
        faces, corner_edges, edges.size(), ss->edge_to_face_offsets, ss->edge_to_face_indices);
  }

  int next_face_set = 1;

  for (const int i : faces.index_range()) {
    if (visited_faces[i]) {
      continue;
    }
    std::queue<int> queue;

    face_sets[i] = next_face_set;
    visited_faces[i].set(true);
    queue.push(i);

    while (!queue.empty()) {
      const int face_i = queue.front();
      queue.pop();

      for (const int edge_i : corner_edges.slice(faces[face_i])) {
        for (const int neighbor_i : ss->epmap[edge_i]) {
          if (neighbor_i == face_i) {
            continue;
          }
          if (visited_faces[neighbor_i]) {
            continue;
          }
          if (!test_fn(face_i, edge_i, neighbor_i)) {
            continue;
          }

          face_sets[neighbor_i] = next_face_set;
          visited_faces[neighbor_i].set(true);
          queue.push(neighbor_i);
        }
      }
    }

    next_face_set += 1;
  }
}

static void sculpt_face_sets_init_loop(Object *ob, const int mode)
{
  using namespace blender;
  Mesh *mesh = static_cast<Mesh *>(ob->data);
  SculptSession *ss = ob->sculpt;

  if (mode == SCULPT_FACE_SETS_FROM_MATERIALS) {
    const bke::AttributeAccessor attributes = mesh->attributes();
    const VArraySpan<int> material_indices = *attributes.lookup_or_default<int>(
        "material_index", ATTR_DOMAIN_FACE, 0);
    for (const int i : IndexRange(mesh->faces_num)) {
      ss->face_sets[i] = material_indices[i] + 1;
    }
  }
}

static int sculpt_face_set_init_exec(bContext *C, wmOperator *op)
{
  using namespace blender;
  Object *ob = CTX_data_active_object(C);
  SculptSession *ss = ob->sculpt;
  Depsgraph *depsgraph = CTX_data_depsgraph_pointer(C);

  const int mode = RNA_enum_get(op->ptr, "mode");

  BKE_sculpt_update_object_for_edit(depsgraph, ob, true, false, false);

  /* Dyntopo not supported. */
  if (BKE_pbvh_type(ss->pbvh) == PBVH_BMESH) {
    return OPERATOR_CANCELLED;
  }

  PBVH *pbvh = ob->sculpt->pbvh;
  Vector<PBVHNode *> nodes = blender::bke::pbvh::search_gather(pbvh, {});

  if (nodes.is_empty()) {
    return OPERATOR_CANCELLED;
  }

  SCULPT_undo_push_begin(ob, op);
  for (PBVHNode *node : nodes) {
    SCULPT_undo_push_node(ob, node, SCULPT_UNDO_FACE_SETS);
  }

  const float threshold = RNA_float_get(op->ptr, "threshold");

  Mesh *mesh = static_cast<Mesh *>(ob->data);
  ss->face_sets = BKE_sculpt_face_sets_ensure(ob);
  const bke::AttributeAccessor attributes = mesh->attributes();

  switch (mode) {
    case SCULPT_FACE_SETS_FROM_LOOSE_PARTS: {
      const VArray<bool> hide_poly = *attributes.lookup_or_default<bool>(
          ".hide_poly", ATTR_DOMAIN_FACE, false);
      sculpt_face_sets_init_flood_fill(
          ob, [&](const int from_face, const int /*edge*/, const int to_face) {
            return hide_poly[from_face] == hide_poly[to_face];
          });
      break;
    }
    case SCULPT_FACE_SETS_FROM_MATERIALS: {
      sculpt_face_sets_init_loop(ob, SCULPT_FACE_SETS_FROM_MATERIALS);
      break;
    }
    case SCULPT_FACE_SETS_FROM_NORMALS: {
      const Span<float3> face_normals = mesh->face_normals();
      sculpt_face_sets_init_flood_fill(
          ob, [&](const int from_face, const int /*edge*/, const int to_face) -> bool {
            return std::abs(math::dot(face_normals[from_face], face_normals[to_face])) > threshold;
          });
      break;
    }
    case SCULPT_FACE_SETS_FROM_UV_SEAMS: {
      const VArraySpan<bool> uv_seams = *mesh->attributes().lookup_or_default<bool>(
          ".uv_seam", ATTR_DOMAIN_EDGE, false);
      sculpt_face_sets_init_flood_fill(
          ob, [&](const int /*from_face*/, const int edge, const int /*to_face*/) -> bool {
            return !uv_seams[edge];
          });
      break;
    }
    case SCULPT_FACE_SETS_FROM_CREASES: {
      const float *creases = static_cast<const float *>(
          CustomData_get_layer_named(&mesh->edge_data, CD_PROP_FLOAT, "crease_edge"));
      sculpt_face_sets_init_flood_fill(
          ob, [&](const int /*from_face*/, const int edge, const int /*to_face*/) -> bool {
            return creases ? creases[edge] < threshold : true;
          });
      break;
    }
    case SCULPT_FACE_SETS_FROM_SHARP_EDGES: {
      const VArraySpan<bool> sharp_edges = *mesh->attributes().lookup_or_default<bool>(
          "sharp_edge", ATTR_DOMAIN_EDGE, false);
      sculpt_face_sets_init_flood_fill(
          ob, [&](const int /*from_face*/, const int edge, const int /*to_face*/) -> bool {
            return !sharp_edges[edge];
          });
      break;
    }
    case SCULPT_FACE_SETS_FROM_BEVEL_WEIGHT: {
      const float *bevel_weights = static_cast<const float *>(
          CustomData_get_layer_named(&mesh->edge_data, CD_PROP_FLOAT, "bevel_weight_edge"));
      sculpt_face_sets_init_flood_fill(
          ob, [&](const int /*from_face*/, const int edge, const int /*to_face*/) -> bool {
            return bevel_weights ? bevel_weights[edge] < threshold : true;
          });
      break;
    }
    case SCULPT_FACE_SETS_FROM_FACE_SET_BOUNDARIES: {
      Array<int> face_sets_copy(Span<int>(ss->face_sets, mesh->faces_num));
      sculpt_face_sets_init_flood_fill(
          ob, [&](const int from_face, const int /*edge*/, const int to_face) -> bool {
            return face_sets_copy[from_face] == face_sets_copy[to_face];
          });
      break;
    }
  }

  SCULPT_undo_push_end(ob);

  /* Sync face sets visibility and vertex visibility as now all Face Sets are visible. */
  SCULPT_visibility_sync_all_from_faces(ob);

  for (PBVHNode *node : nodes) {
    BKE_pbvh_node_mark_update_visibility(node);
  }

  BKE_pbvh_update_visibility(ss->pbvh);

  SCULPT_tag_update_overlays(C);

  return OPERATOR_FINISHED;
}

void SCULPT_OT_face_sets_init(wmOperatorType *ot)
{
  /* identifiers */
  ot->name = "Init Face Sets";
  ot->idname = "SCULPT_OT_face_sets_init";
  ot->description = "Initializes all Face Sets in the mesh";

  /* api callbacks */
  ot->exec = sculpt_face_set_init_exec;
  ot->poll = SCULPT_mode_poll;

  ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;

  RNA_def_enum(
      ot->srna, "mode", prop_sculpt_face_sets_init_types, SCULPT_FACE_SET_MASKED, "Mode", "");
  RNA_def_float(
      ot->srna,
      "threshold",
      0.5f,
      0.0f,
      1.0f,
      "Threshold",
      "Minimum value to consider a certain attribute a boundary when creating the Face Sets",
      0.0f,
      1.0f);
}

enum eSculptFaceGroupVisibilityModes {
  SCULPT_FACE_SET_VISIBILITY_TOGGLE = 0,
  SCULPT_FACE_SET_VISIBILITY_SHOW_ACTIVE = 1,
  SCULPT_FACE_SET_VISIBILITY_HIDE_ACTIVE = 2,
};

static EnumPropertyItem prop_sculpt_face_sets_change_visibility_types[] = {
    {
        SCULPT_FACE_SET_VISIBILITY_TOGGLE,
        "TOGGLE",
        0,
        "Toggle Visibility",
        "Hide all Face Sets except for the active one",
    },
    {
        SCULPT_FACE_SET_VISIBILITY_SHOW_ACTIVE,
        "SHOW_ACTIVE",
        0,
        "Show Active Face Set",
        "Show Active Face Set",
    },
    {
        SCULPT_FACE_SET_VISIBILITY_HIDE_ACTIVE,
        "HIDE_ACTIVE",
        0,
        "Hide Active Face Sets",
        "Hide Active Face Sets",
    },
    {0, nullptr, 0, nullptr, nullptr},
};

static int sculpt_face_set_change_visibility_exec(bContext *C, wmOperator *op)
{
  Object *ob = CTX_data_active_object(C);
  SculptSession *ss = ob->sculpt;
  Depsgraph *depsgraph = CTX_data_depsgraph_pointer(C);

  Mesh *mesh = BKE_object_get_original_mesh(ob);

  BKE_sculpt_update_object_for_edit(depsgraph, ob, true, true, false);

  /* Not supported for dyntopo. */
  if (BKE_pbvh_type(ss->pbvh) == PBVH_BMESH) {
    return OPERATOR_CANCELLED;
  }

  const int mode = RNA_enum_get(op->ptr, "mode");
  const int tot_vert = SCULPT_vertex_count_get(ss);

  PBVH *pbvh = ob->sculpt->pbvh;
  Vector<PBVHNode *> nodes = blender::bke::pbvh::search_gather(pbvh, {});

  if (nodes.is_empty()) {
    return OPERATOR_CANCELLED;
  }

  const int active_face_set = SCULPT_active_face_set_get(ss);
  ss->hide_poly = BKE_sculpt_hide_poly_ensure(mesh);

  SCULPT_undo_push_begin(ob, op);
  for (PBVHNode *node : nodes) {
    SCULPT_undo_push_node(ob, node, SCULPT_UNDO_HIDDEN);
  }

  switch (mode) {
    case SCULPT_FACE_SET_VISIBILITY_TOGGLE: {
      bool hidden_vertex = false;

      /* This can fail with regular meshes with non-manifold geometry as the visibility state can't
       * be synced from face sets to non-manifold vertices. */
      if (BKE_pbvh_type(ss->pbvh) == PBVH_GRIDS) {
        for (int i = 0; i < tot_vert; i++) {
          PBVHVertRef vertex = BKE_pbvh_index_to_vertex(ss->pbvh, i);

          if (!SCULPT_vertex_visible_get(ss, vertex)) {
            hidden_vertex = true;
            break;
          }
        }
      }

      if (ss->hide_poly) {
        for (int i = 0; i < ss->totfaces; i++) {
          if (ss->hide_poly[i]) {
            hidden_vertex = true;
            break;
          }
        }
      }

      if (hidden_vertex) {
        SCULPT_face_visibility_all_set(ss, true);
      }
      else {
        if (ss->face_sets) {
          SCULPT_face_visibility_all_set(ss, false);
          SCULPT_face_set_visibility_set(ss, active_face_set, true);
        }
        else {
          SCULPT_face_visibility_all_set(ss, true);
        }
      }
      break;
    }
    case SCULPT_FACE_SET_VISIBILITY_SHOW_ACTIVE:
      ss->hide_poly = BKE_sculpt_hide_poly_ensure(mesh);

      if (ss->face_sets) {
        SCULPT_face_visibility_all_set(ss, false);
        SCULPT_face_set_visibility_set(ss, active_face_set, true);
      }
      else {
        SCULPT_face_set_visibility_set(ss, active_face_set, true);
      }
      break;
    case SCULPT_FACE_SET_VISIBILITY_HIDE_ACTIVE:
      ss->hide_poly = BKE_sculpt_hide_poly_ensure(mesh);

      if (ss->face_sets) {
        SCULPT_face_set_visibility_set(ss, active_face_set, false);
      }
      else {
        SCULPT_face_visibility_all_set(ss, false);
      }

      break;
  }

  /* For modes that use the cursor active vertex, update the rotation origin for viewport
   * navigation.
   */
  if (ELEM(mode, SCULPT_FACE_SET_VISIBILITY_TOGGLE, SCULPT_FACE_SET_VISIBILITY_SHOW_ACTIVE)) {
    UnifiedPaintSettings *ups = &CTX_data_tool_settings(C)->unified_paint_settings;
    float location[3];
    copy_v3_v3(location, SCULPT_active_vertex_co_get(ss));
    mul_m4_v3(ob->object_to_world, location);
    copy_v3_v3(ups->average_stroke_accum, location);
    ups->average_stroke_counter = 1;
    ups->last_stroke_valid = true;
  }

  /* Sync face sets visibility and vertex visibility. */
  SCULPT_visibility_sync_all_from_faces(ob);

  SCULPT_undo_push_end(ob);
  for (PBVHNode *node : nodes) {
    BKE_pbvh_node_mark_update_visibility(node);
  }

  BKE_pbvh_update_visibility(ss->pbvh);

  SCULPT_tag_update_overlays(C);

  return OPERATOR_FINISHED;
}

static int sculpt_face_set_change_visibility_invoke(bContext *C,
                                                    wmOperator *op,
                                                    const wmEvent *event)
{
  Object *ob = CTX_data_active_object(C);
  SculptSession *ss = ob->sculpt;

  /* Update the active vertex and Face Set using the cursor position to avoid relying on the paint
   * cursor updates. */
  SculptCursorGeometryInfo sgi;
  const float mval_fl[2] = {float(event->mval[0]), float(event->mval[1])};
  SCULPT_vertex_random_access_ensure(ss);
  SCULPT_cursor_geometry_info_update(C, &sgi, mval_fl, false);

  return sculpt_face_set_change_visibility_exec(C, op);
}

void SCULPT_OT_face_set_change_visibility(wmOperatorType *ot)
{
  /* Identifiers. */
  ot->name = "Face Sets Visibility";
  ot->idname = "SCULPT_OT_face_set_change_visibility";
  ot->description = "Change the visibility of the Face Sets of the sculpt";

  /* Api callbacks. */
  ot->exec = sculpt_face_set_change_visibility_exec;
  ot->invoke = sculpt_face_set_change_visibility_invoke;
  ot->poll = SCULPT_mode_poll;

  ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO | OPTYPE_DEPENDS_ON_CURSOR;

  RNA_def_enum(ot->srna,
               "mode",
               prop_sculpt_face_sets_change_visibility_types,
               SCULPT_FACE_SET_VISIBILITY_TOGGLE,
               "Mode",
               "");
}

static int sculpt_face_sets_randomize_colors_exec(bContext *C, wmOperator * /*op*/)
{

  Object *ob = CTX_data_active_object(C);
  SculptSession *ss = ob->sculpt;

  /* Dyntopo not supported. */
  if (BKE_pbvh_type(ss->pbvh) == PBVH_BMESH) {
    return OPERATOR_CANCELLED;
  }

  if (!ss->face_sets) {
    return OPERATOR_CANCELLED;
  }

  PBVH *pbvh = ob->sculpt->pbvh;
  Mesh *mesh = static_cast<Mesh *>(ob->data);

  mesh->face_sets_color_seed += 1;
  if (ss->face_sets) {
    const int random_index = clamp_i(ss->totfaces * BLI_hash_int_01(mesh->face_sets_color_seed),
                                     0,
                                     max_ii(0, ss->totfaces - 1));
    mesh->face_sets_color_default = ss->face_sets[random_index];
  }

  Vector<PBVHNode *> nodes = blender::bke::pbvh::search_gather(pbvh, {});
  for (PBVHNode *node : nodes) {
    BKE_pbvh_node_mark_redraw(node);
  }

  SCULPT_tag_update_overlays(C);

  return OPERATOR_FINISHED;
}

void SCULPT_OT_face_sets_randomize_colors(wmOperatorType *ot)
{
  /* Identifiers. */
  ot->name = "Randomize Face Sets Colors";
  ot->idname = "SCULPT_OT_face_sets_randomize_colors";
  ot->description = "Generates a new set of random colors to render the Face Sets in the viewport";

  /* Api callbacks. */
  ot->exec = sculpt_face_sets_randomize_colors_exec;
  ot->poll = SCULPT_mode_poll;

  ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;
}

enum eSculptFaceSetEditMode {
  SCULPT_FACE_SET_EDIT_GROW = 0,
  SCULPT_FACE_SET_EDIT_SHRINK = 1,
  SCULPT_FACE_SET_EDIT_DELETE_GEOMETRY = 2,
  SCULPT_FACE_SET_EDIT_FAIR_POSITIONS = 3,
  SCULPT_FACE_SET_EDIT_FAIR_TANGENCY = 4,
};

static EnumPropertyItem prop_sculpt_face_sets_edit_types[] = {
    {
        SCULPT_FACE_SET_EDIT_GROW,
        "GROW",
        0,
        "Grow Face Set",
        "Grows the Face Sets boundary by one face based on mesh topology",
    },
    {
        SCULPT_FACE_SET_EDIT_SHRINK,
        "SHRINK",
        0,
        "Shrink Face Set",
        "Shrinks the Face Sets boundary by one face based on mesh topology",
    },
    {
        SCULPT_FACE_SET_EDIT_DELETE_GEOMETRY,
        "DELETE_GEOMETRY",
        0,
        "Delete Geometry",
        "Deletes the faces that are assigned to the Face Set",
    },
    {
        SCULPT_FACE_SET_EDIT_FAIR_POSITIONS,
        "FAIR_POSITIONS",
        0,
        "Fair Positions",
        "Creates a smooth as possible geometry patch from the Face Set minimizing changes in "
        "vertex positions",
    },
    {
        SCULPT_FACE_SET_EDIT_FAIR_TANGENCY,
        "FAIR_TANGENCY",
        0,
        "Fair Tangency",
        "Creates a smooth as possible geometry patch from the Face Set minimizing changes in "
        "vertex tangents",
    },
    {0, nullptr, 0, nullptr, nullptr},
};

static void sculpt_face_set_grow(Object *ob,
                                 SculptSession *ss,
                                 const int *prev_face_sets,
                                 const int active_face_set_id,
                                 const bool modify_hidden)
{
  using namespace blender;
  Mesh *mesh = BKE_mesh_from_object(ob);
  const OffsetIndices faces = mesh->faces();
  const Span<int> corner_verts = mesh->corner_verts();

  for (const int p : faces.index_range()) {
    if (!modify_hidden && prev_face_sets[p] <= 0) {
      continue;
    }
    for (const int vert : corner_verts.slice(faces[p])) {
      for (const int neighbor_face_index : ss->pmap[vert]) {
        if (neighbor_face_index == p) {
          continue;
        }
        if (prev_face_sets[neighbor_face_index] == active_face_set_id) {
          ss->face_sets[p] = active_face_set_id;
        }
      }
    }
  }
}

static void sculpt_face_set_shrink(Object *ob,
                                   SculptSession *ss,
                                   const int *prev_face_sets,
                                   const int active_face_set_id,
                                   const bool modify_hidden)
{
  using namespace blender;
  Mesh *mesh = BKE_mesh_from_object(ob);
  const OffsetIndices faces = mesh->faces();
  const Span<int> corner_verts = mesh->corner_verts();
  for (const int p : faces.index_range()) {
    if (!modify_hidden && prev_face_sets[p] <= 0) {
      continue;
    }
    if (prev_face_sets[p] == active_face_set_id) {
      for (const int vert_i : corner_verts.slice(faces[p])) {
        for (const int neighbor_face_index : ss->pmap[vert_i]) {
          if (neighbor_face_index == p) {
            continue;
          }
          if (prev_face_sets[neighbor_face_index] != active_face_set_id) {
            ss->face_sets[p] = prev_face_sets[neighbor_face_index];
          }
        }
      }
    }
  }
}

static bool check_single_face_set(SculptSession *ss,
                                  const int *face_sets,
                                  const bool check_visible_only)
{
  if (face_sets == nullptr) {
    return true;
  }
  int first_face_set = SCULPT_FACE_SET_NONE;
  if (check_visible_only) {
    for (int f = 0; f < ss->totfaces; f++) {
      if (ss->hide_poly && ss->hide_poly[f]) {
        continue;
      }
      first_face_set = face_sets[f];
      break;
    }
  }
  else {
    first_face_set = face_sets[0];
  }

  if (first_face_set == SCULPT_FACE_SET_NONE) {
    return true;
  }

  for (int f = 0; f < ss->totfaces; f++) {
    if (check_visible_only && ss->hide_poly && ss->hide_poly[f]) {
      continue;
    }
    if (face_sets[f] != first_face_set) {
      return false;
    }
  }
  return true;
}

static void sculpt_face_set_delete_geometry(Object *ob,
                                            SculptSession *ss,
                                            const int active_face_set_id,
                                            const bool modify_hidden)
{

  Mesh *mesh = static_cast<Mesh *>(ob->data);
  const BMAllocTemplate allocsize = BMALLOC_TEMPLATE_FROM_ME(mesh);
  BMeshCreateParams create_params{};
  create_params.use_toolflags = true;
  BMesh *bm = BM_mesh_create(&allocsize, &create_params);

  BMeshFromMeshParams convert_params{};
  convert_params.calc_vert_normal = true;
  convert_params.calc_face_normal = true;
  BM_mesh_bm_from_me(bm, mesh, &convert_params);

  BM_mesh_elem_table_init(bm, BM_FACE);
  BM_mesh_elem_table_ensure(bm, BM_FACE);
  BM_mesh_elem_hflag_disable_all(bm, BM_VERT | BM_EDGE | BM_FACE, BM_ELEM_TAG, false);
  BMIter iter;
  BMFace *f;
  BM_ITER_MESH (f, &iter, bm, BM_FACES_OF_MESH) {
    const int face_index = BM_elem_index_get(f);
    if (!modify_hidden && ss->hide_poly && ss->hide_poly[face_index]) {
      continue;
    }
    BM_elem_flag_set(f, BM_ELEM_TAG, ss->face_sets[face_index] == active_face_set_id);
  }
  BM_mesh_delete_hflag_context(bm, BM_ELEM_TAG, DEL_FACES);
  BM_mesh_elem_hflag_disable_all(bm, BM_VERT | BM_EDGE | BM_FACE, BM_ELEM_TAG, false);

  BMeshToMeshParams bmesh_to_mesh_params{};
  bmesh_to_mesh_params.calc_object_remap = false;
  BM_mesh_bm_to_me(nullptr, bm, mesh, &bmesh_to_mesh_params);

  BM_mesh_free(bm);
}

static void sculpt_face_set_edit_fair_face_set(Object *ob,
                                               const int active_face_set_id,
                                               const eMeshFairingDepth fair_order,
                                               const float strength)
{
  SculptSession *ss = ob->sculpt;
  const int totvert = SCULPT_vertex_count_get(ss);

  Mesh *mesh = static_cast<Mesh *>(ob->data);
  Vector<float3> orig_positions;
  Vector<bool> fair_verts;

  orig_positions.resize(totvert);
  fair_verts.resize(totvert);

  SCULPT_boundary_info_ensure(ob);

  for (int i = 0; i < totvert; i++) {
    PBVHVertRef vertex = BKE_pbvh_index_to_vertex(ss->pbvh, i);

    orig_positions[i] = SCULPT_vertex_co_get(ss, vertex);
    fair_verts[i] = !SCULPT_vertex_is_boundary(ss, vertex) &&
                    SCULPT_vertex_has_face_set(ss, vertex, active_face_set_id) &&
                    SCULPT_vertex_has_unique_face_set(ss, vertex);
  }

  float(*positions)[3] = SCULPT_mesh_deformed_positions_get(ss);
  BKE_mesh_prefair_and_fair_verts(mesh, positions, fair_verts.data(), fair_order);

  for (int i = 0; i < totvert; i++) {
    if (fair_verts[i]) {
      interp_v3_v3v3(positions[i], orig_positions[i], positions[i], strength);
      BKE_pbvh_vert_tag_update_normal(ss->pbvh, BKE_pbvh_index_to_vertex(ss->pbvh, i));
    }
  }
}

static void sculpt_face_set_apply_edit(Object *ob,
                                       const int active_face_set_id,
                                       const int mode,
                                       const bool modify_hidden,
                                       const float strength = 0.0f)
{
  SculptSession *ss = ob->sculpt;

  switch (mode) {
    case SCULPT_FACE_SET_EDIT_GROW: {
      int *prev_face_sets = static_cast<int *>(MEM_dupallocN(ss->face_sets));
      sculpt_face_set_grow(ob, ss, prev_face_sets, active_face_set_id, modify_hidden);
      MEM_SAFE_FREE(prev_face_sets);
      break;
    }
    case SCULPT_FACE_SET_EDIT_SHRINK: {
      int *prev_face_sets = static_cast<int *>(MEM_dupallocN(ss->face_sets));
      sculpt_face_set_shrink(ob, ss, prev_face_sets, active_face_set_id, modify_hidden);
      MEM_SAFE_FREE(prev_face_sets);
      break;
    }
    case SCULPT_FACE_SET_EDIT_DELETE_GEOMETRY:
      sculpt_face_set_delete_geometry(ob, ss, active_face_set_id, modify_hidden);
      break;
    case SCULPT_FACE_SET_EDIT_FAIR_POSITIONS:
      sculpt_face_set_edit_fair_face_set(
          ob, active_face_set_id, MESH_FAIRING_DEPTH_POSITION, strength);
      break;
    case SCULPT_FACE_SET_EDIT_FAIR_TANGENCY:
      sculpt_face_set_edit_fair_face_set(
          ob, active_face_set_id, MESH_FAIRING_DEPTH_TANGENCY, strength);
      break;
  }
}

static bool sculpt_face_set_edit_is_operation_valid(SculptSession *ss,
                                                    const eSculptFaceSetEditMode mode,
                                                    const bool modify_hidden)
{
  if (BKE_pbvh_type(ss->pbvh) == PBVH_BMESH) {
    /* Dyntopo is not supported. */
    return false;
  }

  if (mode == SCULPT_FACE_SET_EDIT_DELETE_GEOMETRY) {
    if (BKE_pbvh_type(ss->pbvh) == PBVH_GRIDS) {
      /* Modification of base mesh geometry requires special remapping of multi-resolution
       * displacement, which does not happen here.
       * Disable delete operation. It can be supported in the future by doing similar displacement
       * data remapping as what happens in the mesh edit mode. */
      return false;
    }
    if (check_single_face_set(ss, ss->face_sets, !modify_hidden)) {
      /* Cancel the operator if the mesh only contains one Face Set to avoid deleting the
       * entire object. */
      return false;
    }
  }

  if (ELEM(mode, SCULPT_FACE_SET_EDIT_FAIR_POSITIONS, SCULPT_FACE_SET_EDIT_FAIR_TANGENCY)) {
    if (BKE_pbvh_type(ss->pbvh) == PBVH_GRIDS) {
      /* TODO: Multi-resolution topology representation using grids and duplicates can't be used
       * directly by the fair algorithm. Multi-resolution topology needs to be exposed in a
       * different way or converted to a mesh for this operation. */
      return false;
    }
  }

  return true;
}

static void sculpt_face_set_edit_modify_geometry(bContext *C,
                                                 Object *ob,
                                                 const int active_face_set,
                                                 const eSculptFaceSetEditMode mode,
                                                 const bool modify_hidden,
                                                 wmOperator *op)
{
  Mesh *mesh = static_cast<Mesh *>(ob->data);
  ED_sculpt_undo_geometry_begin(ob, op);
  sculpt_face_set_apply_edit(ob, active_face_set, mode, modify_hidden);
  ED_sculpt_undo_geometry_end(ob);
  BKE_mesh_batch_cache_dirty_tag(mesh, BKE_MESH_BATCH_DIRTY_ALL);
  DEG_id_tag_update(&ob->id, ID_RECALC_GEOMETRY);
  WM_event_add_notifier(C, NC_GEOM | ND_DATA, mesh);
}

static void face_set_edit_do_post_visibility_updates(Object *ob, Span<PBVHNode *> nodes)
{
  SculptSession *ss = ob->sculpt;

  /* Sync face sets visibility and vertex visibility as now all Face Sets are visible. */
  SCULPT_visibility_sync_all_from_faces(ob);

  for (PBVHNode *node : nodes) {
    BKE_pbvh_node_mark_update_visibility(node);
  }

  BKE_pbvh_update_visibility(ss->pbvh);
}

static void sculpt_face_set_edit_modify_face_sets(Object *ob,
                                                  const int active_face_set,
                                                  const eSculptFaceSetEditMode mode,
                                                  const bool modify_hidden,
                                                  wmOperator *op)
{
  PBVH *pbvh = ob->sculpt->pbvh;
  Vector<PBVHNode *> nodes = blender::bke::pbvh::search_gather(pbvh, {});

  if (nodes.is_empty()) {
    return;
  }
  SCULPT_undo_push_begin(ob, op);
  for (PBVHNode *node : nodes) {
    SCULPT_undo_push_node(ob, node, SCULPT_UNDO_FACE_SETS);
  }
  sculpt_face_set_apply_edit(ob, active_face_set, mode, modify_hidden);
  SCULPT_undo_push_end(ob);
  face_set_edit_do_post_visibility_updates(ob, nodes);
}

static void sculpt_face_set_edit_modify_coordinates(bContext *C,
                                                    Object *ob,
                                                    const int active_face_set,
                                                    const eSculptFaceSetEditMode mode,
                                                    wmOperator *op)
{
  Sculpt *sd = CTX_data_tool_settings(C)->sculpt;
  SculptSession *ss = ob->sculpt;
  PBVH *pbvh = ss->pbvh;

  Vector<PBVHNode *> nodes = blender::bke::pbvh::search_gather(pbvh, {});

  const float strength = RNA_float_get(op->ptr, "strength");

  SCULPT_undo_push_begin(ob, op);
  for (PBVHNode *node : nodes) {
    BKE_pbvh_node_mark_update(node);
    SCULPT_undo_push_node(ob, node, SCULPT_UNDO_COORDS);
  }
  sculpt_face_set_apply_edit(ob, active_face_set, mode, false, strength);

  if (ss->deform_modifiers_active || ss->shapekey_active) {
    SCULPT_flush_stroke_deform(sd, ob, true);
  }
  SCULPT_flush_update_step(C, SCULPT_UPDATE_COORDS);
  SCULPT_flush_update_done(C, ob, SCULPT_UPDATE_COORDS);
  SCULPT_undo_push_end(ob);
}

static bool sculpt_face_set_edit_init(bContext *C, wmOperator *op)
{
  Object *ob = CTX_data_active_object(C);
  SculptSession *ss = ob->sculpt;
  Depsgraph *depsgraph = CTX_data_ensure_evaluated_depsgraph(C);
  const eSculptFaceSetEditMode mode = static_cast<eSculptFaceSetEditMode>(
      RNA_enum_get(op->ptr, "mode"));
  const bool modify_hidden = RNA_boolean_get(op->ptr, "modify_hidden");

  if (!sculpt_face_set_edit_is_operation_valid(ss, mode, modify_hidden)) {
    return false;
  }

  ss->face_sets = BKE_sculpt_face_sets_ensure(ob);
  BKE_sculpt_update_object_for_edit(depsgraph, ob, true, false, false);

  return true;
}

static int sculpt_face_set_edit_exec(bContext *C, wmOperator *op)
{
  if (!sculpt_face_set_edit_init(C, op)) {
    return OPERATOR_CANCELLED;
  }

  Object *ob = CTX_data_active_object(C);

  const int active_face_set = RNA_int_get(op->ptr, "active_face_set");
  const eSculptFaceSetEditMode mode = static_cast<eSculptFaceSetEditMode>(
      RNA_enum_get(op->ptr, "mode"));
  const bool modify_hidden = RNA_boolean_get(op->ptr, "modify_hidden");

  switch (mode) {
    case SCULPT_FACE_SET_EDIT_DELETE_GEOMETRY:
      sculpt_face_set_edit_modify_geometry(C, ob, active_face_set, mode, modify_hidden, op);
      break;
    case SCULPT_FACE_SET_EDIT_GROW:
    case SCULPT_FACE_SET_EDIT_SHRINK:
      sculpt_face_set_edit_modify_face_sets(ob, active_face_set, mode, modify_hidden, op);
      break;
    case SCULPT_FACE_SET_EDIT_FAIR_POSITIONS:
    case SCULPT_FACE_SET_EDIT_FAIR_TANGENCY:
      sculpt_face_set_edit_modify_coordinates(C, ob, active_face_set, mode, op);
      break;
  }

  SCULPT_tag_update_overlays(C);

  return OPERATOR_FINISHED;
}

static int sculpt_face_set_edit_invoke(bContext *C, wmOperator *op, const wmEvent *event)
{
  Depsgraph *depsgraph = CTX_data_depsgraph_pointer(C);
  Object *ob = CTX_data_active_object(C);
  SculptSession *ss = ob->sculpt;

  BKE_sculpt_update_object_for_edit(depsgraph, ob, true, false, false);

  /* Update the current active Face Set and Vertex as the operator can be used directly from the
   * tool without brush cursor. */
  SculptCursorGeometryInfo sgi;
  const float mval_fl[2] = {float(event->mval[0]), float(event->mval[1])};
  if (!SCULPT_cursor_geometry_info_update(C, &sgi, mval_fl, false)) {
    /* The cursor is not over the mesh. Cancel to avoid editing the last updated Face Set ID. */
    return OPERATOR_CANCELLED;
  }
  RNA_int_set(op->ptr, "active_face_set", SCULPT_active_face_set_get(ss));

  return sculpt_face_set_edit_exec(C, op);
}

void SCULPT_OT_face_sets_edit(wmOperatorType *ot)
{
  /* Identifiers. */
  ot->name = "Edit Face Set";
  ot->idname = "SCULPT_OT_face_set_edit";
  ot->description = "Edits the current active Face Set";

  /* Api callbacks. */
  ot->invoke = sculpt_face_set_edit_invoke;
  ot->exec = sculpt_face_set_edit_exec;
  ot->poll = SCULPT_mode_poll;

  ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO | OPTYPE_DEPENDS_ON_CURSOR;

  PropertyRNA *prop = RNA_def_int(
      ot->srna, "active_face_set", 1, 0, INT_MAX, "Active Face Set", "", 0, 64);
  RNA_def_property_flag(prop, PROP_HIDDEN);

  RNA_def_enum(
      ot->srna, "mode", prop_sculpt_face_sets_edit_types, SCULPT_FACE_SET_EDIT_GROW, "Mode", "");
  RNA_def_float(ot->srna, "strength", 1.0f, 0.0f, 1.0f, "Strength", "", 0.0f, 1.0f);

  ot->prop = RNA_def_boolean(ot->srna,
                             "modify_hidden",
                             true,
                             "Modify Hidden",
                             "Apply the edit operation to hidden Face Sets");
}

static int sculpt_face_sets_invert_visibility_exec(bContext *C, wmOperator *op)
{
  Object *ob = CTX_data_active_object(C);
  SculptSession *ss = ob->sculpt;
  Mesh *mesh = static_cast<Mesh *>(ob->data);
  Depsgraph *depsgraph = CTX_data_depsgraph_pointer(C);

  BKE_sculpt_update_object_for_edit(depsgraph, ob, true, true, false);

  /* Not supported for dyntopo. */
  if (BKE_pbvh_type(ss->pbvh) == PBVH_BMESH) {
    return OPERATOR_CANCELLED;
  }

  PBVH *pbvh = ob->sculpt->pbvh;
  Vector<PBVHNode *> nodes = blender::bke::pbvh::search_gather(pbvh, {});

  if (nodes.is_empty()) {
    return OPERATOR_CANCELLED;
  }

  ss->hide_poly = BKE_sculpt_hide_poly_ensure(mesh);

  SCULPT_undo_push_begin(ob, op);
  for (PBVHNode *node : nodes) {
    SCULPT_undo_push_node(ob, node, SCULPT_UNDO_HIDDEN);
  }

  SCULPT_face_visibility_all_invert(ss);

  SCULPT_undo_push_end(ob);

  /* Sync face sets visibility and vertex visibility. */
  SCULPT_visibility_sync_all_from_faces(ob);

  for (PBVHNode *node : nodes) {
    BKE_pbvh_node_mark_update_visibility(node);
  }

  BKE_pbvh_update_visibility(ss->pbvh);

  SCULPT_tag_update_overlays(C);

  return OPERATOR_FINISHED;
}

void SCULPT_OT_face_sets_invert_visibility(wmOperatorType *ot)
{
  /* Identifiers. */
  ot->name = "Invert Face Set Visibility";
  ot->idname = "SCULPT_OT_face_set_invert_visibility";
  ot->description = "Invert the visibility of the Face Sets of the sculpt";

  /* Api callbacks. */
  ot->exec = sculpt_face_sets_invert_visibility_exec;
  ot->poll = SCULPT_mode_poll;

  ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;
}

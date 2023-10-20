/* SPDX-FileCopyrightText: 2021 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup draw
 *
 * \brief Extraction of Mesh data into VBO to feed to GPU.
 */

#include "MEM_guardedalloc.h"

#include "BLI_array.hh"
#include "BLI_array_utils.hh"
#include "BLI_enumerable_thread_specific.hh"
#include "BLI_index_mask.hh"
#include "BLI_math_matrix.h"
#include "BLI_task.hh"
#include "BLI_virtual_array.hh"

#include "BKE_attribute.hh"
#include "BKE_editmesh.h"
#include "BKE_editmesh_cache.hh"
#include "BKE_mesh.hh"
#include "BKE_mesh_runtime.hh"

#include "GPU_batch.h"

#include "ED_mesh.hh"

#include "mesh_extractors/extract_mesh.hh"

/* ---------------------------------------------------------------------- */
/** \name Update Loose Geometry
 * \{ */

static void extract_set_bits(const blender::BitSpan bits, blender::MutableSpan<int> indices)
{
  int count = 0;
  for (const int64_t i : bits.index_range()) {
    if (bits[i]) {
      indices[count] = int(i);
      count++;
    }
  }
  BLI_assert(count == indices.size());
}

static void mesh_render_data_loose_geom_mesh(const MeshRenderData &mr, MeshBufferCache &cache)
{
  using namespace blender;
  const Mesh &mesh = *mr.me;
  const bool no_loose_vert_hint = mesh.runtime->loose_verts_cache.is_cached() &&
                                  mesh.runtime->loose_verts_cache.data().count == 0;
  const bool no_loose_edge_hint = mesh.runtime->loose_edges_cache.is_cached() &&
                                  mesh.runtime->loose_edges_cache.data().count == 0;
  threading::parallel_invoke(
      mesh.totedge > 4096 && !no_loose_vert_hint && !no_loose_edge_hint,
      [&]() {
        const bke::LooseEdgeCache &loose_edges = mesh.loose_edges();
        if (loose_edges.count > 0) {
          cache.loose_geom.edges.reinitialize(loose_edges.count);
          extract_set_bits(loose_edges.is_loose_bits, cache.loose_geom.edges);
        }
      },
      [&]() {
        const bke::LooseVertCache &loose_verts = mesh.loose_verts();
        if (loose_verts.count > 0) {
          cache.loose_geom.verts.reinitialize(loose_verts.count);
          extract_set_bits(loose_verts.is_loose_bits, cache.loose_geom.verts);
        }
      });
}

static void mesh_render_data_loose_verts_bm(const MeshRenderData &mr,
                                            MeshBufferCache &cache,
                                            BMesh &bm)
{
  using namespace blender;
  int i;
  BMIter iter;
  BMVert *vert;
  int count = 0;
  Array<int> loose_verts(mr.vert_len);
  BM_ITER_MESH_INDEX (vert, &iter, &bm, BM_VERTS_OF_MESH, i) {
    if (vert->e == nullptr) {
      loose_verts[count] = i;
      count++;
    }
  }
  if (count < mr.vert_len) {
    cache.loose_geom.verts = loose_verts.as_span().take_front(count);
  }
  else {
    cache.loose_geom.verts = std::move(loose_verts);
  }
}

static void mesh_render_data_loose_edges_bm(const MeshRenderData &mr,
                                            MeshBufferCache &cache,
                                            BMesh &bm)
{
  using namespace blender;
  int i;
  BMIter iter;
  BMEdge *edge;
  int count = 0;
  Array<int> loose_edges(mr.edge_len);
  BM_ITER_MESH_INDEX (edge, &iter, &bm, BM_EDGES_OF_MESH, i) {
    if (edge->l == nullptr) {
      loose_edges[count] = i;
      count++;
    }
  }
  if (count < mr.edge_len) {
    cache.loose_geom.edges = loose_edges.as_span().take_front(count);
  }
  else {
    cache.loose_geom.edges = std::move(loose_edges);
  }
}

static void mesh_render_data_loose_geom_build(const MeshRenderData &mr, MeshBufferCache &cache)
{
  if (mr.extract_type != MR_EXTRACT_BMESH) {
    /* Mesh */
    mesh_render_data_loose_geom_mesh(mr, cache);
  }
  else {
    /* #BMesh */
    BMesh &bm = *mr.bm;
    mesh_render_data_loose_verts_bm(mr, cache, bm);
    mesh_render_data_loose_edges_bm(mr, cache, bm);
  }
}

static void mesh_render_data_loose_geom_ensure(const MeshRenderData &mr, MeshBufferCache &cache)
{
  /* Early exit: Are loose geometry already available.
   * Only checking for loose verts as loose edges and verts are calculated at the same time. */
  if (!cache.loose_geom.verts.is_empty()) {
    return;
  }
  mesh_render_data_loose_geom_build(mr, cache);
}

void mesh_render_data_update_loose_geom(MeshRenderData &mr,
                                        MeshBufferCache &cache,
                                        const eMRIterType iter_type,
                                        const eMRDataType data_flag)
{
  if ((iter_type & (MR_ITER_LOOSE_EDGE | MR_ITER_LOOSE_VERT)) || (data_flag & MR_DATA_LOOSE_GEOM))
  {
    mesh_render_data_loose_geom_ensure(mr, cache);
    mr.loose_edges = cache.loose_geom.edges;
    mr.loose_verts = cache.loose_geom.verts;
    mr.vert_loose_len = cache.loose_geom.verts.size();
    mr.edge_loose_len = cache.loose_geom.edges.size();

    mr.loop_loose_len = mr.vert_loose_len + (mr.edge_loose_len * 2);
  }
}

/** \} */

/* ---------------------------------------------------------------------- */
/** \name Polygons sorted per material
 *
 * Contains face indices sorted based on their material.
 * \{ */

namespace blender::draw {

static void accumululate_material_counts_bm(
    const BMesh &bm, threading::EnumerableThreadSpecific<Array<int>> &all_tri_counts)
{
  threading::parallel_for(IndexRange(bm.totface), 1024, [&](const IndexRange range) {
    Array<int> &tri_counts = all_tri_counts.local();
    const short last_index = tri_counts.size() - 1;
    for (const int i : range) {
      const BMFace &face = *BM_face_at_index(&const_cast<BMesh &>(bm), i);
      if (!BM_elem_flag_test(&face, BM_ELEM_HIDDEN)) {
        const short mat = std::clamp<short>(face.mat_nr, 0, last_index);
        tri_counts[mat] += face.len - 2;
      }
    }
  });
}

static void accumululate_material_counts_mesh(
    const MeshRenderData &mr, threading::EnumerableThreadSpecific<Array<int>> &all_tri_counts)
{
  const OffsetIndices faces = mr.faces;
  if (!mr.material_indices) {
    if (mr.use_hide && mr.hide_poly) {
      const Span hide_poly(mr.hide_poly, mr.face_len);
      all_tri_counts.local().first() = threading::parallel_reduce(
          faces.index_range(),
          4096,
          0,
          [&](const IndexRange range, int count) {
            for (const int face : range) {
              if (!hide_poly[face]) {
                count += bke::mesh::face_triangles_num(faces[face].size());
              }
            }
            return count;
          },
          std::plus<int>());
    }
    else {
      all_tri_counts.local().first() = poly_to_tri_count(mr.face_len, mr.loop_len);
    }
    return;
  }

  const Span material_indices(mr.material_indices, mr.face_len);
  threading::parallel_for(material_indices.index_range(), 1024, [&](const IndexRange range) {
    Array<int> &tri_counts = all_tri_counts.local();
    const int last_index = tri_counts.size() - 1;
    if (mr.use_hide && mr.hide_poly) {
      for (const int i : range) {
        if (!mr.hide_poly[i]) {
          const int mat = std::clamp(material_indices[i], 0, last_index);
          tri_counts[mat] += bke::mesh::face_triangles_num(faces[i].size());
        }
      }
    }
    else {
      for (const int i : range) {
        const int mat = std::clamp(material_indices[i], 0, last_index);
        tri_counts[mat] += bke::mesh::face_triangles_num(faces[i].size());
      }
    }
  });
}

/* Count how many triangles for each material. */
static Array<int> mesh_render_data_mat_tri_len_build(const MeshRenderData &mr)
{
  threading::EnumerableThreadSpecific<Array<int>> all_tri_counts(
      [&]() { return Array<int>(mr.mat_len, 0); });

  if (mr.extract_type == MR_EXTRACT_BMESH) {
    accumululate_material_counts_bm(*mr.bm, all_tri_counts);
  }
  else {
    accumululate_material_counts_mesh(mr, all_tri_counts);
  }

  Array<int> &mat_tri_len = all_tri_counts.local();
  for (const Array<int> &counts : all_tri_counts) {
    if (&counts != &mat_tri_len) {
      for (const int i : mat_tri_len.index_range()) {
        mat_tri_len[i] += counts[i];
      }
    }
  }
  return std::move(mat_tri_len);
}

static void mesh_render_data_faces_sorted_build(MeshRenderData &mr, MeshBufferCache &cache)
{
  cache.face_sorted.mat_tri_len = mesh_render_data_mat_tri_len_build(mr);
  const Span<int> mat_tri_len = cache.face_sorted.mat_tri_len;

  /* Apply offset. */
  int visible_tri_len = 0;
  Array<int, 32> mat_tri_offs(mr.mat_len);
  {
    for (int i = 0; i < mr.mat_len; i++) {
      mat_tri_offs[i] = visible_tri_len;
      visible_tri_len += mat_tri_len[i];
    }
  }
  cache.face_sorted.visible_tri_len = visible_tri_len;

  cache.face_sorted.tri_first_index.reinitialize(mr.face_len);
  MutableSpan<int> tri_first_index = cache.face_sorted.tri_first_index;

  /* Sort per material. */
  int mat_last = mr.mat_len - 1;
  if (mr.extract_type == MR_EXTRACT_BMESH) {
    BMIter iter;
    BMFace *f;
    int i;
    BM_ITER_MESH_INDEX (f, &iter, mr.bm, BM_FACES_OF_MESH, i) {
      if (!BM_elem_flag_test(f, BM_ELEM_HIDDEN)) {
        const int mat = clamp_i(f->mat_nr, 0, mat_last);
        tri_first_index[i] = mat_tri_offs[mat];
        mat_tri_offs[mat] += f->len - 2;
      }
      else {
        tri_first_index[i] = -1;
      }
    }
  }
  else {
    for (int i = 0; i < mr.face_len; i++) {
      if (!(mr.use_hide && mr.hide_poly && mr.hide_poly[i])) {
        const int mat = mr.material_indices ? clamp_i(mr.material_indices[i], 0, mat_last) : 0;
        tri_first_index[i] = mat_tri_offs[mat];
        mat_tri_offs[mat] += mr.faces[i].size() - 2;
      }
      else {
        tri_first_index[i] = -1;
      }
    }
  }
}

static void mesh_render_data_faces_sorted_ensure(MeshRenderData &mr, MeshBufferCache &cache)
{
  if (!cache.face_sorted.tri_first_index.is_empty()) {
    return;
  }
  mesh_render_data_faces_sorted_build(mr, cache);
}

}  // namespace blender::draw

void mesh_render_data_update_faces_sorted(MeshRenderData &mr,
                                          MeshBufferCache &cache,
                                          const eMRDataType data_flag)
{
  if (data_flag & MR_DATA_POLYS_SORTED) {
    blender::draw::mesh_render_data_faces_sorted_ensure(mr, cache);
    mr.face_sorted = &cache.face_sorted;
  }
}

/** \} */

/* ---------------------------------------------------------------------- */
/** \name Mesh/BMesh Interface (indirect, partially cached access to complex data).
 * \{ */

void mesh_render_data_update_looptris(MeshRenderData &mr,
                                      const eMRIterType iter_type,
                                      const eMRDataType data_flag)
{
  if (mr.extract_type != MR_EXTRACT_BMESH) {
    /* Mesh */
    if ((iter_type & MR_ITER_LOOPTRI) || (data_flag & MR_DATA_LOOPTRI)) {
      mr.looptris = mr.me->looptris();
      mr.looptri_faces = mr.me->looptri_faces();
    }
  }
  else {
    /* #BMesh */
    if ((iter_type & MR_ITER_LOOPTRI) || (data_flag & MR_DATA_LOOPTRI)) {
      /* Edit mode ensures this is valid, no need to calculate. */
      BLI_assert((mr.bm->totloop == 0) || (mr.edit_bmesh->looptris != nullptr));
    }
  }
}

static bool bm_edge_is_sharp(const BMEdge *const &edge)
{
  return !BM_elem_flag_test(edge, BM_ELEM_SMOOTH);
}

static bool bm_face_is_sharp(const BMFace *const &face)
{
  return !BM_elem_flag_test(face, BM_ELEM_SMOOTH);
}

/**
 * Returns whether loop normals are required because of mixed sharp and smooth flags.
 * Similar to #Mesh::normals_domain().
 */
static bool bm_loop_normals_required(BMesh *bm)
{
  using namespace blender;
  using namespace blender::bke;
  if (bm->totface == 0) {
    return false;
  }

  if (CustomData_has_layer(&bm->ldata, CD_CUSTOMLOOPNORMAL)) {
    return true;
  }

  BM_mesh_elem_table_ensure(bm, BM_FACE);
  const VArray<bool> sharp_faces = VArray<bool>::ForDerivedSpan<const BMFace *, bm_face_is_sharp>(
      Span(bm->ftable, bm->totface));
  const array_utils::BooleanMix face_mix = array_utils::booleans_mix_calc(sharp_faces);
  if (face_mix == array_utils::BooleanMix::AllTrue) {
    return false;
  }

  BM_mesh_elem_table_ensure(bm, BM_EDGE);
  const VArray<bool> sharp_edges = VArray<bool>::ForDerivedSpan<const BMEdge *, bm_edge_is_sharp>(
      Span(bm->etable, bm->totedge));
  const array_utils::BooleanMix edge_mix = array_utils::booleans_mix_calc(sharp_edges);
  if (edge_mix == array_utils::BooleanMix::AllTrue) {
    return false;
  }

  if (edge_mix == array_utils::BooleanMix::AllFalse &&
      face_mix == array_utils::BooleanMix::AllFalse) {
    return false;
  }

  return true;
}

void mesh_render_data_update_normals(MeshRenderData &mr, const eMRDataType data_flag)
{
  if (mr.extract_type != MR_EXTRACT_BMESH) {
    /* Mesh */
    mr.vert_normals = mr.me->vert_normals();
    if (data_flag & (MR_DATA_POLY_NOR | MR_DATA_LOOP_NOR | MR_DATA_TAN_LOOP_NOR)) {
      mr.face_normals = mr.me->face_normals();
    }
    if (((data_flag & MR_DATA_LOOP_NOR) && ELEM(mr.me->normals_domain(),
                                                blender::bke::MeshNormalDomain::Corner,
                                                blender::bke::MeshNormalDomain::Face)) ||
        (data_flag & MR_DATA_TAN_LOOP_NOR))
    {
      mr.loop_normals = mr.me->corner_normals();
    }
  }
  else {
    /* #BMesh */
    if (data_flag & MR_DATA_POLY_NOR) {
      /* Use #BMFace.no instead. */
    }
    if (((data_flag & MR_DATA_LOOP_NOR) && bm_loop_normals_required(mr.bm)) ||
        (data_flag & MR_DATA_TAN_LOOP_NOR))
    {

      const float(*vert_coords)[3] = nullptr;
      const float(*vert_normals)[3] = nullptr;
      const float(*face_normals)[3] = nullptr;

      if (mr.edit_data && !mr.edit_data->vertexCos.is_empty()) {
        vert_coords = reinterpret_cast<const float(*)[3]>(mr.bm_vert_coords.data());
        vert_normals = reinterpret_cast<const float(*)[3]>(mr.bm_vert_normals.data());
        face_normals = reinterpret_cast<const float(*)[3]>(mr.bm_face_normals.data());
      }

      mr.bm_loop_normals.reinitialize(mr.loop_len);
      const int clnors_offset = CustomData_get_offset(&mr.bm->ldata, CD_CUSTOMLOOPNORMAL);
      BM_loops_calc_normal_vcos(mr.bm,
                                vert_coords,
                                vert_normals,
                                face_normals,
                                true,
                                reinterpret_cast<float(*)[3]>(mr.bm_loop_normals.data()),
                                nullptr,
                                nullptr,
                                clnors_offset,
                                false);
      mr.loop_normals = mr.bm_loop_normals;
    }
  }
}

static void retrieve_active_attribute_names(MeshRenderData &mr,
                                            const Object &object,
                                            const Mesh &mesh)
{
  const Mesh *mesh_final = editmesh_final_or_this(&object, &mesh);
  mr.active_color_name = mesh_final->active_color_attribute;
  mr.default_color_name = mesh_final->default_color_attribute;
}

MeshRenderData *mesh_render_data_create(Object *object,
                                        Mesh *me,
                                        const bool is_editmode,
                                        const bool is_paint_mode,
                                        const bool is_mode_active,
                                        const float obmat[4][4],
                                        const bool do_final,
                                        const bool do_uvedit,
                                        const ToolSettings *ts)
{
  MeshRenderData *mr = MEM_new<MeshRenderData>(__func__);
  mr->toolsettings = ts;
  mr->mat_len = mesh_render_mat_len_get(object, me);

  copy_m4_m4(mr->obmat, obmat);

  if (is_editmode) {
    Mesh *editmesh_eval_final = BKE_object_get_editmesh_eval_final(object);
    Mesh *editmesh_eval_cage = BKE_object_get_editmesh_eval_cage(object);

    BLI_assert(editmesh_eval_cage && editmesh_eval_final);
    mr->bm = me->edit_mesh->bm;
    mr->edit_bmesh = me->edit_mesh;
    mr->me = (do_final) ? editmesh_eval_final : editmesh_eval_cage;
    mr->edit_data = is_mode_active ? mr->me->runtime->edit_data : nullptr;

    /* If there is no distinct cage, hide unmapped edges that can't be selected. */
    mr->hide_unmapped_edges = !do_final || editmesh_eval_final == editmesh_eval_cage;

    if (mr->edit_data) {
      blender::bke::EditMeshData *emd = mr->edit_data;
      if (!emd->vertexCos.is_empty()) {
        BKE_editmesh_cache_ensure_vert_normals(mr->edit_bmesh, emd);
        BKE_editmesh_cache_ensure_face_normals(mr->edit_bmesh, emd);
      }

      mr->bm_vert_coords = mr->edit_data->vertexCos;
      mr->bm_vert_normals = mr->edit_data->vertexNos;
      mr->bm_face_normals = mr->edit_data->faceNos;
      mr->bm_face_centers = mr->edit_data->faceCos;
    }

    int bm_ensure_types = BM_VERT | BM_EDGE | BM_LOOP | BM_FACE;

    BM_mesh_elem_index_ensure(mr->bm, bm_ensure_types);
    BM_mesh_elem_table_ensure(mr->bm, bm_ensure_types & ~BM_LOOP);

    mr->efa_act_uv = EDBM_uv_active_face_get(mr->edit_bmesh, false, false);
    mr->efa_act = BM_mesh_active_face_get(mr->bm, false, true);
    mr->eed_act = BM_mesh_active_edge_get(mr->bm);
    mr->eve_act = BM_mesh_active_vert_get(mr->bm);

    mr->vert_crease_ofs = CustomData_get_offset_named(
        &mr->bm->vdata, CD_PROP_FLOAT, "crease_vert");
    mr->edge_crease_ofs = CustomData_get_offset_named(
        &mr->bm->edata, CD_PROP_FLOAT, "crease_edge");
    mr->bweight_ofs = CustomData_get_offset_named(
        &mr->bm->edata, CD_PROP_FLOAT, "bevel_weight_edge");
#ifdef WITH_FREESTYLE
    mr->freestyle_edge_ofs = CustomData_get_offset(&mr->bm->edata, CD_FREESTYLE_EDGE);
    mr->freestyle_face_ofs = CustomData_get_offset(&mr->bm->pdata, CD_FREESTYLE_FACE);
#endif

    /* Use bmesh directly when the object is in edit mode unchanged by any modifiers.
     * For non-final UVs, always use original bmesh since the UV editor does not support
     * using the cage mesh with deformed coordinates. */
    if ((is_mode_active && mr->me->runtime->is_original_bmesh &&
         mr->me->runtime->wrapper_type == ME_WRAPPER_TYPE_BMESH) ||
        (do_uvedit && !do_final))
    {
      mr->extract_type = MR_EXTRACT_BMESH;
    }
    else {
      mr->extract_type = MR_EXTRACT_MESH;

      /* Use mapping from final to original mesh when the object is in edit mode. */
      if (is_mode_active && do_final) {
        mr->v_origindex = static_cast<const int *>(
            CustomData_get_layer(&mr->me->vert_data, CD_ORIGINDEX));
        mr->e_origindex = static_cast<const int *>(
            CustomData_get_layer(&mr->me->edge_data, CD_ORIGINDEX));
        mr->p_origindex = static_cast<const int *>(
            CustomData_get_layer(&mr->me->face_data, CD_ORIGINDEX));
      }
      else {
        mr->v_origindex = nullptr;
        mr->e_origindex = nullptr;
        mr->p_origindex = nullptr;
      }
    }
  }
  else {
    mr->me = me;
    mr->edit_bmesh = nullptr;
    mr->extract_type = MR_EXTRACT_MESH;
    mr->hide_unmapped_edges = false;

    if (is_paint_mode && mr->me) {
      mr->v_origindex = static_cast<const int *>(
          CustomData_get_layer(&mr->me->vert_data, CD_ORIGINDEX));
      mr->e_origindex = static_cast<const int *>(
          CustomData_get_layer(&mr->me->edge_data, CD_ORIGINDEX));
      mr->p_origindex = static_cast<const int *>(
          CustomData_get_layer(&mr->me->face_data, CD_ORIGINDEX));
    }
    else {
      mr->v_origindex = nullptr;
      mr->e_origindex = nullptr;
      mr->p_origindex = nullptr;
    }
  }

  if (mr->extract_type != MR_EXTRACT_BMESH) {
    /* Mesh */
    mr->vert_len = mr->me->totvert;
    mr->edge_len = mr->me->totedge;
    mr->loop_len = mr->me->totloop;
    mr->face_len = mr->me->faces_num;
    mr->tri_len = poly_to_tri_count(mr->face_len, mr->loop_len);

    mr->vert_positions = mr->me->vert_positions();
    mr->edges = mr->me->edges();
    mr->faces = mr->me->faces();
    mr->corner_verts = mr->me->corner_verts();
    mr->corner_edges = mr->me->corner_edges();

    mr->v_origindex = static_cast<const int *>(
        CustomData_get_layer(&mr->me->vert_data, CD_ORIGINDEX));
    mr->e_origindex = static_cast<const int *>(
        CustomData_get_layer(&mr->me->edge_data, CD_ORIGINDEX));
    mr->p_origindex = static_cast<const int *>(
        CustomData_get_layer(&mr->me->face_data, CD_ORIGINDEX));

    mr->material_indices = static_cast<const int *>(
        CustomData_get_layer_named(&mr->me->face_data, CD_PROP_INT32, "material_index"));

    mr->hide_vert = static_cast<const bool *>(
        CustomData_get_layer_named(&mr->me->vert_data, CD_PROP_BOOL, ".hide_vert"));
    mr->hide_edge = static_cast<const bool *>(
        CustomData_get_layer_named(&mr->me->edge_data, CD_PROP_BOOL, ".hide_edge"));
    mr->hide_poly = static_cast<const bool *>(
        CustomData_get_layer_named(&mr->me->face_data, CD_PROP_BOOL, ".hide_poly"));

    mr->select_vert = static_cast<const bool *>(
        CustomData_get_layer_named(&mr->me->vert_data, CD_PROP_BOOL, ".select_vert"));
    mr->select_edge = static_cast<const bool *>(
        CustomData_get_layer_named(&mr->me->edge_data, CD_PROP_BOOL, ".select_edge"));
    mr->select_poly = static_cast<const bool *>(
        CustomData_get_layer_named(&mr->me->face_data, CD_PROP_BOOL, ".select_poly"));

    mr->sharp_faces = static_cast<const bool *>(
        CustomData_get_layer_named(&mr->me->face_data, CD_PROP_BOOL, "sharp_face"));
  }
  else {
    /* #BMesh */
    BMesh *bm = mr->bm;

    mr->vert_len = bm->totvert;
    mr->edge_len = bm->totedge;
    mr->loop_len = bm->totloop;
    mr->face_len = bm->totface;
    mr->tri_len = poly_to_tri_count(mr->face_len, mr->loop_len);
  }

  retrieve_active_attribute_names(*mr, *object, *mr->me);

  return mr;
}

void mesh_render_data_free(MeshRenderData *mr)
{
  MEM_delete(mr);
}

/** \} */

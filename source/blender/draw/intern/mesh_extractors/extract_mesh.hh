/* SPDX-FileCopyrightText: 2021 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup draw
 *
 * \brief Extraction of Mesh data into VBO to feed to GPU.
 */

#pragma once

#include "BLI_math_vector_types.hh"

#include "DNA_mesh_types.h"
#include "DNA_meshdata_types.h"
#include "DNA_object_types.h"
#include "DNA_scene_types.h"

#include "BKE_customdata.h"
#include "BKE_editmesh.h"
#include "BKE_editmesh_cache.hh"
#include "BKE_mesh.hh"

#include "draw_cache_extract.hh"

struct DRWSubdivCache;

#define MIN_RANGE_LEN 1024

/* ---------------------------------------------------------------------- */
/** \name Mesh Render Data
 * \{ */

enum eMRExtractType {
  MR_EXTRACT_BMESH,
  MR_EXTRACT_MESH,
};

struct MeshRenderData {
  eMRExtractType extract_type;

  int face_len, edge_len, vert_len, loop_len;
  int edge_loose_len;
  int vert_loose_len;
  int loop_loose_len;
  int tri_len;
  int mat_len;

  bool use_hide;
  bool use_subsurf_fdots;
  bool use_final_mesh;
  bool hide_unmapped_edges;

  /** Use for #MeshStatVis calculation which use world-space coords. */
  float obmat[4][4];

  const ToolSettings *toolsettings;
  /** Edit Mesh */
  BMEditMesh *edit_bmesh;
  BMesh *bm;
  blender::bke::EditMeshData *edit_data;

  /* For deformed edit-mesh data. */
  /* Use for #ME_WRAPPER_TYPE_BMESH. */
  blender::Span<blender::float3> bm_vert_coords;
  blender::Span<blender::float3> bm_vert_normals;
  blender::Span<blender::float3> bm_face_normals;
  blender::Span<blender::float3> bm_face_centers;
  blender::Array<blender::float3> bm_loop_normals;

  const int *v_origindex, *e_origindex, *p_origindex;
  int edge_crease_ofs;
  int vert_crease_ofs;
  int bweight_ofs;
  int freestyle_edge_ofs;
  int freestyle_face_ofs;
  /** Mesh */
  Mesh *me;
  blender::Span<blender::float3> vert_positions;
  blender::Span<blender::int2> edges;
  blender::OffsetIndices<int> faces;
  blender::Span<int> corner_verts;
  blender::Span<int> corner_edges;
  BMVert *eve_act;
  BMEdge *eed_act;
  BMFace *efa_act;
  BMFace *efa_act_uv;
  /* The triangulation of #Mesh faces, owned by the mesh. */
  blender::Span<MLoopTri> looptris;
  blender::Span<int> looptri_faces;
  const int *material_indices;
  blender::Span<blender::float3> vert_normals;
  blender::Span<blender::float3> face_normals;
  blender::Span<blender::float3> loop_normals;
  const bool *hide_vert;
  const bool *hide_edge;
  const bool *hide_poly;
  const bool *select_vert;
  const bool *select_edge;
  const bool *select_poly;
  const bool *sharp_faces;

  blender::Span<int> loose_verts;
  blender::Span<int> loose_edges;
  const SortedFaceData *face_sorted;

  const char *active_color_name;
  const char *default_color_name;
};

BLI_INLINE const Mesh *editmesh_final_or_this(const Object *object, const Mesh *me)
{
  if (me->edit_mesh != nullptr) {
    Mesh *editmesh_eval_final = BKE_object_get_editmesh_eval_final(object);
    if (editmesh_eval_final != nullptr) {
      return editmesh_eval_final;
    }
  }

  return me;
}

BLI_INLINE const CustomData *mesh_cd_ldata_get_from_mesh(const Mesh *me)
{
  switch (me->runtime->wrapper_type) {
    case ME_WRAPPER_TYPE_SUBD:
    case ME_WRAPPER_TYPE_MDATA:
      return &me->loop_data;
      break;
    case ME_WRAPPER_TYPE_BMESH:
      return &me->edit_mesh->bm->ldata;
      break;
  }

  BLI_assert(0);
  return &me->loop_data;
}

BLI_INLINE const CustomData *mesh_cd_pdata_get_from_mesh(const Mesh *me)
{
  switch (me->runtime->wrapper_type) {
    case ME_WRAPPER_TYPE_SUBD:
    case ME_WRAPPER_TYPE_MDATA:
      return &me->face_data;
      break;
    case ME_WRAPPER_TYPE_BMESH:
      return &me->edit_mesh->bm->pdata;
      break;
  }

  BLI_assert(0);
  return &me->face_data;
}

BLI_INLINE const CustomData *mesh_cd_edata_get_from_mesh(const Mesh *me)
{
  switch (me->runtime->wrapper_type) {
    case ME_WRAPPER_TYPE_SUBD:
    case ME_WRAPPER_TYPE_MDATA:
      return &me->edge_data;
      break;
    case ME_WRAPPER_TYPE_BMESH:
      return &me->edit_mesh->bm->edata;
      break;
  }

  BLI_assert(0);
  return &me->edge_data;
}

BLI_INLINE const CustomData *mesh_cd_vdata_get_from_mesh(const Mesh *me)
{
  switch (me->runtime->wrapper_type) {
    case ME_WRAPPER_TYPE_SUBD:
    case ME_WRAPPER_TYPE_MDATA:
      return &me->vert_data;
      break;
    case ME_WRAPPER_TYPE_BMESH:
      return &me->edit_mesh->bm->vdata;
      break;
  }

  BLI_assert(0);
  return &me->vert_data;
}

BLI_INLINE BMFace *bm_original_face_get(const MeshRenderData &mr, int idx)
{
  return ((mr.p_origindex != nullptr) && (mr.p_origindex[idx] != ORIGINDEX_NONE) && mr.bm) ?
             BM_face_at_index(mr.bm, mr.p_origindex[idx]) :
             nullptr;
}

BLI_INLINE BMEdge *bm_original_edge_get(const MeshRenderData &mr, int idx)
{
  return ((mr.e_origindex != nullptr) && (mr.e_origindex[idx] != ORIGINDEX_NONE) && mr.bm) ?
             BM_edge_at_index(mr.bm, mr.e_origindex[idx]) :
             nullptr;
}

BLI_INLINE BMVert *bm_original_vert_get(const MeshRenderData &mr, int idx)
{
  return ((mr.v_origindex != nullptr) && (mr.v_origindex[idx] != ORIGINDEX_NONE) && mr.bm) ?
             BM_vert_at_index(mr.bm, mr.v_origindex[idx]) :
             nullptr;
}

BLI_INLINE const float *bm_vert_co_get(const MeshRenderData &mr, const BMVert *eve)
{
  if (!mr.bm_vert_coords.is_empty()) {
    return mr.bm_vert_coords[BM_elem_index_get(eve)];
  }
  return eve->co;
}

BLI_INLINE const float *bm_vert_no_get(const MeshRenderData &mr, const BMVert *eve)
{
  if (!mr.bm_vert_normals.is_empty()) {
    return mr.bm_vert_normals[BM_elem_index_get(eve)];
  }
  return eve->no;
}

BLI_INLINE const float *bm_face_no_get(const MeshRenderData &mr, const BMFace *efa)
{
  if (!mr.bm_face_normals.is_empty()) {
    return mr.bm_face_normals[BM_elem_index_get(efa)];
  }
  return efa->no;
}

/** \} */

/* ---------------------------------------------------------------------- */
/** \name Mesh Elements Extract Struct
 * \{ */

/* TODO(jbakker): move parameters inside a struct. */

using ExtractTriBMeshFn = void(const MeshRenderData &mr, BMLoop **elt, int elt_index, void *data);
using ExtractTriMeshFn = void(const MeshRenderData &mr,
                              const MLoopTri *mlt,
                              int elt_index,
                              void *data);
using ExtractFaceBMeshFn = void(const MeshRenderData &mr,
                                const BMFace *f,
                                int f_index,
                                void *data);
using ExtractFaceMeshFn = void(const MeshRenderData &mr, int face_index, void *data);
using ExtractLEdgeBMeshFn = void(const MeshRenderData &mr,
                                 const BMEdge *eed,
                                 int loose_edge_i,
                                 void *data);
using ExtractLEdgeMeshFn = void(const MeshRenderData &mr,
                                blender::int2 edge,
                                int loose_edge_i,
                                void *data);
using ExtractLVertBMeshFn = void(const MeshRenderData &mr,
                                 const BMVert *eve,
                                 int loose_vert_i,
                                 void *data);
using ExtractLVertMeshFn = void(const MeshRenderData &mr, int loose_vert_i, void *data);
using ExtractLooseGeomSubdivFn = void(const DRWSubdivCache &subdiv_cache,
                                      const MeshRenderData &mr,
                                      void *buffer,
                                      void *data);
using ExtractInitFn = void(const MeshRenderData &mr,
                           MeshBatchCache &cache,
                           void *buffer,
                           void *r_data);
using ExtractFinishFn = void(const MeshRenderData &mr,
                             MeshBatchCache &cache,
                             void *buffer,
                             void *data);
using ExtractTaskReduceFn = void(void *userdata, void *task_userdata);

using ExtractInitSubdivFn = void(const DRWSubdivCache &subdiv_cache,
                                 const MeshRenderData &mr,
                                 MeshBatchCache &cache,
                                 void *buf,
                                 void *data);
using ExtractIterSubdivBMeshFn = void(const DRWSubdivCache &subdiv_cache,
                                      const MeshRenderData &mr,
                                      void *data,
                                      uint subdiv_quad_index,
                                      const BMFace *coarse_quad);
using ExtractIterSubdivMeshFn = void(const DRWSubdivCache &subdiv_cache,
                                     const MeshRenderData &mr,
                                     void *data,
                                     uint subdiv_quad_index,
                                     int coarse_quad_index);
using ExtractFinishSubdivFn = void(const DRWSubdivCache &subdiv_cache,
                                   const MeshRenderData &mr,
                                   MeshBatchCache &cache,
                                   void *buf,
                                   void *data);

struct MeshExtract {
  /** Executed on main thread and return user data for iteration functions. */
  ExtractInitFn *init;
  /** Executed on one (or more if use_threading) worker thread(s). */
  ExtractTriBMeshFn *iter_looptri_bm;
  ExtractTriMeshFn *iter_looptri_mesh;
  ExtractFaceBMeshFn *iter_face_bm;
  ExtractFaceMeshFn *iter_face_mesh;
  ExtractLEdgeBMeshFn *iter_loose_edge_bm;
  ExtractLEdgeMeshFn *iter_loose_edge_mesh;
  ExtractLVertBMeshFn *iter_loose_vert_bm;
  ExtractLVertMeshFn *iter_loose_vert_mesh;
  ExtractLooseGeomSubdivFn *iter_loose_geom_subdiv;
  /** Executed on one worker thread after all elements iterations. */
  ExtractTaskReduceFn *task_reduce;
  ExtractFinishFn *finish;
  /** Executed on main thread for subdivision evaluation. */
  ExtractInitSubdivFn *init_subdiv;
  ExtractIterSubdivBMeshFn *iter_subdiv_bm;
  ExtractIterSubdivMeshFn *iter_subdiv_mesh;
  ExtractFinishSubdivFn *finish_subdiv;
  /** Used to request common data. */
  eMRDataType data_type;
  size_t data_size;
  /** Used to know if the element callbacks are thread-safe and can be parallelized. */
  bool use_threading;
  /**
   * Offset in bytes of the buffer inside a MeshBufferList instance. Points to a vertex or index
   * buffer.
   */
  size_t mesh_buffer_offset;
};

/** \} */

/* `draw_cache_extract_mesh_render_data.cc` */

/**
 * \param is_mode_active: When true, use the modifiers from the edit-data,
 * otherwise don't use modifiers as they are not from this object.
 */
MeshRenderData *mesh_render_data_create(Object *object,
                                        Mesh *me,
                                        bool is_editmode,
                                        bool is_paint_mode,
                                        bool is_mode_active,
                                        const float obmat[4][4],
                                        bool do_final,
                                        bool do_uvedit,
                                        const ToolSettings *ts);
void mesh_render_data_free(MeshRenderData *mr);
void mesh_render_data_update_normals(MeshRenderData &mr, eMRDataType data_flag);
void mesh_render_data_update_loose_geom(MeshRenderData &mr,
                                        MeshBufferCache &cache,
                                        eMRIterType iter_type,
                                        eMRDataType data_flag);
void mesh_render_data_update_faces_sorted(MeshRenderData &mr,
                                          MeshBufferCache &cache,
                                          eMRDataType data_flag);
/**
 * Part of the creation of the #MeshRenderData that happens in a thread.
 */
void mesh_render_data_update_looptris(MeshRenderData &mr,
                                      eMRIterType iter_type,
                                      eMRDataType data_flag);

/* draw_cache_extract_mesh_extractors.c */

struct EditLoopData {
  uchar v_flag;
  uchar e_flag;
  /* This is used for both vertex and edge creases. The edge crease value is stored in the bottom 4
   * bits, while the vertex crease is stored in the upper 4 bits. */
  uchar crease;
  uchar bweight;
};

void *mesh_extract_buffer_get(const MeshExtract *extractor, MeshBufferList *mbuflist);
eMRIterType mesh_extract_iter_type(const MeshExtract *ext);
const MeshExtract *mesh_extract_override_get(const MeshExtract *extractor,
                                             bool do_hq_normals,
                                             bool do_single_mat);
void mesh_render_data_face_flag(const MeshRenderData &mr,
                                const BMFace *efa,
                                BMUVOffsets offsets,
                                EditLoopData *eattr);
void mesh_render_data_loop_flag(const MeshRenderData &mr,
                                BMLoop *l,
                                BMUVOffsets offsets,
                                EditLoopData *eattr);
void mesh_render_data_loop_edge_flag(const MeshRenderData &mr,
                                     BMLoop *l,
                                     BMUVOffsets offsets,
                                     EditLoopData *eattr);

extern const MeshExtract extract_tris;
extern const MeshExtract extract_tris_single_mat;
extern const MeshExtract extract_lines;
extern const MeshExtract extract_lines_with_lines_loose;
extern const MeshExtract extract_lines_loose_only;
extern const MeshExtract extract_points;
extern const MeshExtract extract_fdots;
extern const MeshExtract extract_lines_paint_mask;
extern const MeshExtract extract_lines_adjacency;
extern const MeshExtract extract_edituv_tris;
extern const MeshExtract extract_edituv_lines;
extern const MeshExtract extract_edituv_points;
extern const MeshExtract extract_edituv_fdots;
extern const MeshExtract extract_pos_nor;
extern const MeshExtract extract_pos_nor_hq;
extern const MeshExtract extract_lnor_hq;
extern const MeshExtract extract_lnor;
extern const MeshExtract extract_uv;
extern const MeshExtract extract_tan;
extern const MeshExtract extract_tan_hq;
extern const MeshExtract extract_sculpt_data;
extern const MeshExtract extract_vcol;
extern const MeshExtract extract_orco;
extern const MeshExtract extract_edge_fac;
extern const MeshExtract extract_weights;
extern const MeshExtract extract_edit_data;
extern const MeshExtract extract_edituv_data;
extern const MeshExtract extract_edituv_stretch_area;
extern const MeshExtract extract_edituv_stretch_angle;
extern const MeshExtract extract_mesh_analysis;
extern const MeshExtract extract_fdots_pos;
extern const MeshExtract extract_fdots_nor;
extern const MeshExtract extract_fdots_nor_hq;
extern const MeshExtract extract_fdots_uv;
extern const MeshExtract extract_fdots_edituv_data;
extern const MeshExtract extract_skin_roots;
extern const MeshExtract extract_face_idx;
extern const MeshExtract extract_edge_idx;
extern const MeshExtract extract_vert_idx;
extern const MeshExtract extract_fdot_idx;
extern const MeshExtract extract_attr[GPU_MAX_ATTR];
extern const MeshExtract extract_attr_viewer;

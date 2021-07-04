/*
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software Foundation,
 * Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
 *
 * The Original Code is Copyright (C) 2021 by Blender Foundation.
 * All rights reserved.
 */

/** \file
 * \ingroup draw
 */

#include "draw_cache_extract_mesh_private.h"

namespace blender::draw {

/* ---------------------------------------------------------------------- */
/** \name Extract Selection Index
 * \{ */

static void extract_select_idx_init_impl(const MeshRenderData *UNUSED(mr),
                                         const int len,
                                         void *buf,
                                         void *tls_data)
{
  GPUVertBuf *vbo = static_cast<GPUVertBuf *>(buf);
  static GPUVertFormat format = {0};
  if (format.attr_len == 0) {
    /* TODO: rename "color" to something more descriptive. */
    GPU_vertformat_attr_add(&format, "color", GPU_COMP_U32, 1, GPU_FETCH_INT);
  }
  GPU_vertbuf_init_with_format(vbo, &format);
  GPU_vertbuf_data_alloc(vbo, len);
  *(uint32_t **)tls_data = (uint32_t *)GPU_vertbuf_get_data(vbo);
}

static void extract_select_idx_init(const MeshRenderData *mr,
                                    struct MeshBatchCache *UNUSED(cache),
                                    void *buf,
                                    void *tls_data)
{
  extract_select_idx_init_impl(mr, mr->loop_len + mr->loop_loose_len, buf, tls_data);
}

/* TODO: Use #glVertexID to get loop index and use the data structure on the CPU to retrieve the
 * select element associated with this loop ID. This would remove the need for this separate
 * index VBO's. We could upload the p/e/v_origindex as a buffer texture and sample it inside the
 * shader to output original index. */

static void extract_poly_idx_iter_poly_bm(const MeshRenderData *UNUSED(mr),
                                          const BMFace *f,
                                          const int f_index,
                                          void *data)
{
  BMLoop *l_iter, *l_first;
  l_iter = l_first = BM_FACE_FIRST_LOOP(f);
  do {
    const int l_index = BM_elem_index_get(l_iter);
    (*(uint32_t **)data)[l_index] = f_index;
  } while ((l_iter = l_iter->next) != l_first);
}

static void extract_edge_idx_iter_poly_bm(const MeshRenderData *UNUSED(mr),
                                          const BMFace *f,
                                          const int UNUSED(f_index),
                                          void *data)
{
  BMLoop *l_iter, *l_first;
  l_iter = l_first = BM_FACE_FIRST_LOOP(f);
  do {
    const int l_index = BM_elem_index_get(l_iter);
    (*(uint32_t **)data)[l_index] = BM_elem_index_get(l_iter->e);
  } while ((l_iter = l_iter->next) != l_first);
}

static void extract_vert_idx_iter_poly_bm(const MeshRenderData *UNUSED(mr),
                                          const BMFace *f,
                                          const int UNUSED(f_index),
                                          void *data)
{
  BMLoop *l_iter, *l_first;
  l_iter = l_first = BM_FACE_FIRST_LOOP(f);
  do {
    const int l_index = BM_elem_index_get(l_iter);
    (*(uint32_t **)data)[l_index] = BM_elem_index_get(l_iter->v);
  } while ((l_iter = l_iter->next) != l_first);
}

static void extract_edge_idx_iter_ledge_bm(const MeshRenderData *mr,
                                           const BMEdge *eed,
                                           const int ledge_index,
                                           void *data)
{
  (*(uint32_t **)data)[mr->loop_len + ledge_index * 2 + 0] = BM_elem_index_get(eed);
  (*(uint32_t **)data)[mr->loop_len + ledge_index * 2 + 1] = BM_elem_index_get(eed);
}

static void extract_vert_idx_iter_ledge_bm(const MeshRenderData *mr,
                                           const BMEdge *eed,
                                           const int ledge_index,
                                           void *data)
{
  (*(uint32_t **)data)[mr->loop_len + ledge_index * 2 + 0] = BM_elem_index_get(eed->v1);
  (*(uint32_t **)data)[mr->loop_len + ledge_index * 2 + 1] = BM_elem_index_get(eed->v2);
}

static void extract_vert_idx_iter_lvert_bm(const MeshRenderData *mr,
                                           const BMVert *eve,
                                           const int lvert_index,
                                           void *data)
{
  const int offset = mr->loop_len + (mr->edge_loose_len * 2);

  (*(uint32_t **)data)[offset + lvert_index] = BM_elem_index_get(eve);
}

static void extract_poly_idx_iter_poly_mesh(const MeshRenderData *mr,
                                            const MPoly *mp,
                                            const int mp_index,
                                            void *data)
{
  const int ml_index_end = mp->loopstart + mp->totloop;
  for (int ml_index = mp->loopstart; ml_index < ml_index_end; ml_index += 1) {
    (*(uint32_t **)data)[ml_index] = (mr->p_origindex) ? mr->p_origindex[mp_index] : mp_index;
  }
}

static void extract_edge_idx_iter_poly_mesh(const MeshRenderData *mr,
                                            const MPoly *mp,
                                            const int UNUSED(mp_index),
                                            void *data)
{
  const MLoop *mloop = mr->mloop;
  const int ml_index_end = mp->loopstart + mp->totloop;
  for (int ml_index = mp->loopstart; ml_index < ml_index_end; ml_index += 1) {
    const MLoop *ml = &mloop[ml_index];
    (*(uint32_t **)data)[ml_index] = (mr->e_origindex) ? mr->e_origindex[ml->e] : ml->e;
  }
}

static void extract_vert_idx_iter_poly_mesh(const MeshRenderData *mr,
                                            const MPoly *mp,
                                            const int UNUSED(mp_index),
                                            void *data)
{
  const MLoop *mloop = mr->mloop;
  const int ml_index_end = mp->loopstart + mp->totloop;
  for (int ml_index = mp->loopstart; ml_index < ml_index_end; ml_index += 1) {
    const MLoop *ml = &mloop[ml_index];
    (*(uint32_t **)data)[ml_index] = (mr->v_origindex) ? mr->v_origindex[ml->v] : ml->v;
  }
}

static void extract_edge_idx_iter_ledge_mesh(const MeshRenderData *mr,
                                             const MEdge *UNUSED(med),
                                             const int ledge_index,
                                             void *data)
{
  const int e_index = mr->ledges[ledge_index];
  const int e_orig = (mr->e_origindex) ? mr->e_origindex[e_index] : e_index;
  (*(uint32_t **)data)[mr->loop_len + ledge_index * 2 + 0] = e_orig;
  (*(uint32_t **)data)[mr->loop_len + ledge_index * 2 + 1] = e_orig;
}

static void extract_vert_idx_iter_ledge_mesh(const MeshRenderData *mr,
                                             const MEdge *med,
                                             const int ledge_index,
                                             void *data)
{
  int v1_orig = (mr->v_origindex) ? mr->v_origindex[med->v1] : med->v1;
  int v2_orig = (mr->v_origindex) ? mr->v_origindex[med->v2] : med->v2;
  (*(uint32_t **)data)[mr->loop_len + ledge_index * 2 + 0] = v1_orig;
  (*(uint32_t **)data)[mr->loop_len + ledge_index * 2 + 1] = v2_orig;
}

static void extract_vert_idx_iter_lvert_mesh(const MeshRenderData *mr,
                                             const MVert *UNUSED(mv),
                                             const int lvert_index,
                                             void *data)
{
  const int offset = mr->loop_len + (mr->edge_loose_len * 2);

  const int v_index = mr->lverts[lvert_index];
  const int v_orig = (mr->v_origindex) ? mr->v_origindex[v_index] : v_index;
  (*(uint32_t **)data)[offset + lvert_index] = v_orig;
}

constexpr MeshExtract create_extractor_poly_idx()
{
  MeshExtract extractor = {nullptr};
  extractor.init = extract_select_idx_init;
  extractor.iter_poly_bm = extract_poly_idx_iter_poly_bm;
  extractor.iter_poly_mesh = extract_poly_idx_iter_poly_mesh;
  extractor.data_type = MR_DATA_NONE;
  extractor.data_size = sizeof(uint32_t *);
  extractor.use_threading = true;
  extractor.mesh_buffer_offset = offsetof(MeshBufferCache, vbo.poly_idx);
  return extractor;
}

constexpr MeshExtract create_extractor_edge_idx()
{
  MeshExtract extractor = {nullptr};
  extractor.init = extract_select_idx_init;
  extractor.iter_poly_bm = extract_edge_idx_iter_poly_bm;
  extractor.iter_poly_mesh = extract_edge_idx_iter_poly_mesh;
  extractor.iter_ledge_bm = extract_edge_idx_iter_ledge_bm;
  extractor.iter_ledge_mesh = extract_edge_idx_iter_ledge_mesh;
  extractor.data_type = MR_DATA_NONE;
  extractor.data_size = sizeof(uint32_t *);
  extractor.use_threading = true;
  extractor.mesh_buffer_offset = offsetof(MeshBufferCache, vbo.edge_idx);
  return extractor;
}

constexpr MeshExtract create_extractor_vert_idx()
{
  MeshExtract extractor = {nullptr};
  extractor.init = extract_select_idx_init;
  extractor.iter_poly_bm = extract_vert_idx_iter_poly_bm;
  extractor.iter_poly_mesh = extract_vert_idx_iter_poly_mesh;
  extractor.iter_ledge_bm = extract_vert_idx_iter_ledge_bm;
  extractor.iter_ledge_mesh = extract_vert_idx_iter_ledge_mesh;
  extractor.iter_lvert_bm = extract_vert_idx_iter_lvert_bm;
  extractor.iter_lvert_mesh = extract_vert_idx_iter_lvert_mesh;
  extractor.data_type = MR_DATA_NONE;
  extractor.data_size = sizeof(uint32_t *);
  extractor.use_threading = true;
  extractor.mesh_buffer_offset = offsetof(MeshBufferCache, vbo.vert_idx);
  return extractor;
}

static void extract_fdot_idx_init(const MeshRenderData *mr,
                                  struct MeshBatchCache *UNUSED(cache),
                                  void *buf,
                                  void *tls_data)
{
  extract_select_idx_init_impl(mr, mr->poly_len, buf, tls_data);
}

static void extract_fdot_idx_iter_poly_bm(const MeshRenderData *UNUSED(mr),
                                          const BMFace *UNUSED(f),
                                          const int f_index,
                                          void *data)
{
  (*(uint32_t **)data)[f_index] = f_index;
}

static void extract_fdot_idx_iter_poly_mesh(const MeshRenderData *mr,
                                            const MPoly *UNUSED(mp),
                                            const int mp_index,
                                            void *data)
{
  if (mr->p_origindex != nullptr) {
    (*(uint32_t **)data)[mp_index] = mr->p_origindex[mp_index];
  }
  else {
    (*(uint32_t **)data)[mp_index] = mp_index;
  }
}

constexpr MeshExtract create_extractor_fdot_idx()
{
  MeshExtract extractor = {nullptr};
  extractor.init = extract_fdot_idx_init;
  extractor.iter_poly_bm = extract_fdot_idx_iter_poly_bm;
  extractor.iter_poly_mesh = extract_fdot_idx_iter_poly_mesh;
  extractor.data_type = MR_DATA_NONE;
  extractor.data_size = sizeof(uint32_t *);
  extractor.use_threading = true;
  extractor.mesh_buffer_offset = offsetof(MeshBufferCache, vbo.fdot_idx);
  return extractor;
}

/** \} */

}  // namespace blender::draw

extern "C" {
const MeshExtract extract_poly_idx = blender::draw::create_extractor_poly_idx();
const MeshExtract extract_edge_idx = blender::draw::create_extractor_edge_idx();
const MeshExtract extract_vert_idx = blender::draw::create_extractor_vert_idx();
const MeshExtract extract_fdot_idx = blender::draw::create_extractor_fdot_idx();
}

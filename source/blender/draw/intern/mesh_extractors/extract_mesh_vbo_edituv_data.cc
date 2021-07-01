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
#include "draw_cache_impl.h"

namespace blender::draw {

/* ---------------------------------------------------------------------- */
/** \name Extract Edit UV Data / Flags
 * \{ */

struct MeshExtract_EditUVData_Data {
  EditLoopData *vbo_data;
  int cd_ofs;
};

static void extract_edituv_data_init(const MeshRenderData *mr,
                                     struct MeshBatchCache *UNUSED(cache),
                                     void *buf,
                                     void *tls_data)
{
  GPUVertBuf *vbo = static_cast<GPUVertBuf *>(buf);
  static GPUVertFormat format = {0};
  if (format.attr_len == 0) {
    /* WARNING: Adjust #EditLoopData struct accordingly. */
    GPU_vertformat_attr_add(&format, "data", GPU_COMP_U8, 4, GPU_FETCH_INT);
    GPU_vertformat_alias_add(&format, "flag");
  }

  GPU_vertbuf_init_with_format(vbo, &format);
  GPU_vertbuf_data_alloc(vbo, mr->loop_len);

  CustomData *cd_ldata = (mr->extract_type == MR_EXTRACT_BMESH) ? &mr->bm->ldata : &mr->me->ldata;

  MeshExtract_EditUVData_Data *data = static_cast<MeshExtract_EditUVData_Data *>(tls_data);
  data->vbo_data = (EditLoopData *)GPU_vertbuf_get_data(vbo);
  data->cd_ofs = CustomData_get_offset(cd_ldata, CD_MLOOPUV);
}

static void extract_edituv_data_iter_poly_bm(const MeshRenderData *mr,
                                             const BMFace *f,
                                             const int UNUSED(f_index),
                                             void *_data)
{
  BMLoop *l_iter, *l_first;
  l_iter = l_first = BM_FACE_FIRST_LOOP(f);
  do {
    const int l_index = BM_elem_index_get(l_iter);
    MeshExtract_EditUVData_Data *data = static_cast<MeshExtract_EditUVData_Data *>(_data);
    EditLoopData *eldata = &data->vbo_data[l_index];
    memset(eldata, 0x0, sizeof(*eldata));
    mesh_render_data_loop_flag(mr, l_iter, data->cd_ofs, eldata);
    mesh_render_data_face_flag(mr, f, data->cd_ofs, eldata);
    mesh_render_data_loop_edge_flag(mr, l_iter, data->cd_ofs, eldata);
  } while ((l_iter = l_iter->next) != l_first);
}

static void extract_edituv_data_iter_poly_mesh(const MeshRenderData *mr,
                                               const MPoly *mp,
                                               const int mp_index,
                                               void *_data)
{
  MeshExtract_EditUVData_Data *data = static_cast<MeshExtract_EditUVData_Data *>(_data);
  const MLoop *mloop = mr->mloop;
  const int ml_index_end = mp->loopstart + mp->totloop;
  for (int ml_index = mp->loopstart; ml_index < ml_index_end; ml_index += 1) {
    const MLoop *ml = &mloop[ml_index];

    EditLoopData *eldata = &data->vbo_data[ml_index];
    memset(eldata, 0x0, sizeof(*eldata));
    BMFace *efa = bm_original_face_get(mr, mp_index);
    if (efa) {
      BMEdge *eed = bm_original_edge_get(mr, ml->e);
      BMVert *eve = bm_original_vert_get(mr, ml->v);
      if (eed && eve) {
        /* Loop on an edge endpoint. */
        BMLoop *l = BM_face_edge_share_loop(efa, eed);
        mesh_render_data_loop_flag(mr, l, data->cd_ofs, eldata);
        mesh_render_data_loop_edge_flag(mr, l, data->cd_ofs, eldata);
      }
      else {
        if (eed == nullptr) {
          /* Find if the loop's vert is not part of an edit edge.
           * For this, we check if the previous loop was on an edge. */
          const int ml_index_last = mp->loopstart + mp->totloop - 1;
          const int l_prev = (ml_index == mp->loopstart) ? ml_index_last : (ml_index - 1);
          const MLoop *ml_prev = &mr->mloop[l_prev];
          eed = bm_original_edge_get(mr, ml_prev->e);
        }
        if (eed) {
          /* Mapped points on an edge between two edit verts. */
          BMLoop *l = BM_face_edge_share_loop(efa, eed);
          mesh_render_data_loop_edge_flag(mr, l, data->cd_ofs, eldata);
        }
      }
    }
  }
}

constexpr MeshExtract create_extractor_edituv_data()
{
  MeshExtract extractor = {nullptr};
  extractor.init = extract_edituv_data_init;
  extractor.iter_poly_bm = extract_edituv_data_iter_poly_bm;
  extractor.iter_poly_mesh = extract_edituv_data_iter_poly_mesh;
  extractor.data_type = MR_DATA_NONE;
  extractor.data_size = sizeof(MeshExtract_EditUVData_Data);
  extractor.use_threading = true;
  extractor.mesh_buffer_offset = offsetof(MeshBufferCache, vbo.edituv_data);
  return extractor;
}

/** \} */

}  // namespace blender::draw

extern "C" {
const MeshExtract extract_edituv_data = blender::draw::create_extractor_edituv_data();
}

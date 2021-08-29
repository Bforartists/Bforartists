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

#include "BLI_string.h"

#include "extract_mesh.h"

namespace blender::draw {

/* ---------------------------------------------------------------------- */
/** \name Extract UV  layers
 * \{ */

static void extract_uv_init(const MeshRenderData *mr,
                            struct MeshBatchCache *cache,
                            void *buf,
                            void *UNUSED(tls_data))
{
  GPUVertBuf *vbo = static_cast<GPUVertBuf *>(buf);
  GPUVertFormat format = {0};
  GPU_vertformat_deinterleave(&format);

  CustomData *cd_ldata = (mr->extract_type == MR_EXTRACT_BMESH) ? &mr->bm->ldata : &mr->me->ldata;
  uint32_t uv_layers = cache->cd_used.uv;
  /* HACK to fix T68857 */
  if (mr->extract_type == MR_EXTRACT_BMESH && cache->cd_used.edit_uv == 1) {
    int layer = CustomData_get_active_layer(cd_ldata, CD_MLOOPUV);
    if (layer != -1) {
      uv_layers |= (1 << layer);
    }
  }

  for (int i = 0; i < MAX_MTFACE; i++) {
    if (uv_layers & (1 << i)) {
      char attr_name[32], attr_safe_name[GPU_MAX_SAFE_ATTR_NAME];
      const char *layer_name = CustomData_get_layer_name(cd_ldata, CD_MLOOPUV, i);

      GPU_vertformat_safe_attr_name(layer_name, attr_safe_name, GPU_MAX_SAFE_ATTR_NAME);
      /* UV layer name. */
      BLI_snprintf(attr_name, sizeof(attr_name), "u%s", attr_safe_name);
      GPU_vertformat_attr_add(&format, attr_name, GPU_COMP_F32, 2, GPU_FETCH_FLOAT);
      /* Auto layer name. */
      BLI_snprintf(attr_name, sizeof(attr_name), "a%s", attr_safe_name);
      GPU_vertformat_alias_add(&format, attr_name);
      /* Active render layer name. */
      if (i == CustomData_get_render_layer(cd_ldata, CD_MLOOPUV)) {
        GPU_vertformat_alias_add(&format, "u");
      }
      /* Active display layer name. */
      if (i == CustomData_get_active_layer(cd_ldata, CD_MLOOPUV)) {
        GPU_vertformat_alias_add(&format, "au");
        /* Alias to `pos` for edit uvs. */
        GPU_vertformat_alias_add(&format, "pos");
      }
      /* Stencil mask uv layer name. */
      if (i == CustomData_get_stencil_layer(cd_ldata, CD_MLOOPUV)) {
        GPU_vertformat_alias_add(&format, "mu");
      }
    }
  }

  int v_len = mr->loop_len;
  if (format.attr_len == 0) {
    GPU_vertformat_attr_add(&format, "dummy", GPU_COMP_F32, 1, GPU_FETCH_FLOAT);
    /* VBO will not be used, only allocate minimum of memory. */
    v_len = 1;
  }

  GPU_vertbuf_init_with_format(vbo, &format);
  GPU_vertbuf_data_alloc(vbo, v_len);

  float(*uv_data)[2] = (float(*)[2])GPU_vertbuf_get_data(vbo);
  for (int i = 0; i < MAX_MTFACE; i++) {
    if (uv_layers & (1 << i)) {
      if (mr->extract_type == MR_EXTRACT_BMESH) {
        int cd_ofs = CustomData_get_n_offset(cd_ldata, CD_MLOOPUV, i);
        BMIter f_iter;
        BMFace *efa;
        BM_ITER_MESH (efa, &f_iter, mr->bm, BM_FACES_OF_MESH) {
          BMLoop *l_iter, *l_first;
          l_iter = l_first = BM_FACE_FIRST_LOOP(efa);
          do {
            MLoopUV *luv = (MLoopUV *)BM_ELEM_CD_GET_VOID_P(l_iter, cd_ofs);
            memcpy(uv_data, luv->uv, sizeof(*uv_data));
            uv_data++;
          } while ((l_iter = l_iter->next) != l_first);
        }
      }
      else {
        MLoopUV *layer_data = (MLoopUV *)CustomData_get_layer_n(cd_ldata, CD_MLOOPUV, i);
        for (int ml_index = 0; ml_index < mr->loop_len; ml_index++, uv_data++, layer_data++) {
          memcpy(uv_data, layer_data->uv, sizeof(*uv_data));
        }
      }
    }
  }
}

constexpr MeshExtract create_extractor_uv()
{
  MeshExtract extractor = {nullptr};
  extractor.init = extract_uv_init;
  extractor.data_type = MR_DATA_NONE;
  extractor.data_size = 0;
  extractor.use_threading = false;
  extractor.mesh_buffer_offset = offsetof(MeshBufferList, vbo.uv);
  return extractor;
}

/** \} */

}  // namespace blender::draw

extern "C" {
const MeshExtract extract_uv = blender::draw::create_extractor_uv();
}

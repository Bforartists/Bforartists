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
 *
 * \brief Extraction of Mesh data into VBO to feed to GPU.
 */

#include "MEM_guardedalloc.h"

#include "DNA_object_types.h"

#include "ED_uvedit.h"

#include "extract_mesh.h"

#include "draw_cache_impl.h"

void *mesh_extract_buffer_get(const MeshExtract *extractor, MeshBufferList *mbuflist)
{
  /* NOTE: POINTER_OFFSET on windows platforms casts internally to `void *`, but on GCC/CLANG to
   * `MeshBufferList *`. What shows a different usage versus intent. */
  void **buffer_ptr = (void **)POINTER_OFFSET(mbuflist, extractor->mesh_buffer_offset);
  void *buffer = *buffer_ptr;
  BLI_assert(buffer);
  return buffer;
}

eMRIterType mesh_extract_iter_type(const MeshExtract *ext)
{
  eMRIterType type = 0;
  SET_FLAG_FROM_TEST(type, (ext->iter_looptri_bm || ext->iter_looptri_mesh), MR_ITER_LOOPTRI);
  SET_FLAG_FROM_TEST(type, (ext->iter_poly_bm || ext->iter_poly_mesh), MR_ITER_POLY);
  SET_FLAG_FROM_TEST(type, (ext->iter_ledge_bm || ext->iter_ledge_mesh), MR_ITER_LEDGE);
  SET_FLAG_FROM_TEST(type, (ext->iter_lvert_bm || ext->iter_lvert_mesh), MR_ITER_LVERT);
  return type;
}

/* ---------------------------------------------------------------------- */
/** \name Override extractors
 * Extractors can be overridden. When overridden a specialized version is used. The next functions
 * would check for any needed overrides and usage of the specialized version.
 * \{ */

static const MeshExtract *mesh_extract_override_hq_normals(const MeshExtract *extractor)
{
  if (extractor == &extract_pos_nor) {
    return &extract_pos_nor_hq;
  }
  if (extractor == &extract_lnor) {
    return &extract_lnor_hq;
  }
  if (extractor == &extract_tan) {
    return &extract_tan_hq;
  }
  if (extractor == &extract_fdots_nor) {
    return &extract_fdots_nor_hq;
  }
  return extractor;
}

static const MeshExtract *mesh_extract_override_single_material(const MeshExtract *extractor)
{
  if (extractor == &extract_tris) {
    return &extract_tris_single_mat;
  }
  return extractor;
}

const MeshExtract *mesh_extract_override_get(const MeshExtract *extractor,
                                             const bool do_hq_normals,
                                             const bool do_single_mat)
{
  if (do_hq_normals) {
    extractor = mesh_extract_override_hq_normals(extractor);
  }

  if (do_single_mat) {
    extractor = mesh_extract_override_single_material(extractor);
  }

  return extractor;
}

/** \} */

/* ---------------------------------------------------------------------- */
/** \name Extract Edit Flag Utils
 * \{ */

void mesh_render_data_face_flag(const MeshRenderData *mr,
                                const BMFace *efa,
                                const int cd_ofs,
                                EditLoopData *eattr)
{
  if (efa == mr->efa_act) {
    eattr->v_flag |= VFLAG_FACE_ACTIVE;
  }
  if (BM_elem_flag_test(efa, BM_ELEM_SELECT)) {
    eattr->v_flag |= VFLAG_FACE_SELECTED;
  }

  if (efa == mr->efa_act_uv) {
    eattr->v_flag |= VFLAG_FACE_UV_ACTIVE;
  }
  if ((cd_ofs != -1) && uvedit_face_select_test_ex(mr->toolsettings, (BMFace *)efa, cd_ofs)) {
    eattr->v_flag |= VFLAG_FACE_UV_SELECT;
  }

#ifdef WITH_FREESTYLE
  if (mr->freestyle_face_ofs != -1) {
    const FreestyleFace *ffa = (const FreestyleFace *)BM_ELEM_CD_GET_VOID_P(
        efa, mr->freestyle_face_ofs);
    if (ffa->flag & FREESTYLE_FACE_MARK) {
      eattr->v_flag |= VFLAG_FACE_FREESTYLE;
    }
  }
#endif
}

void mesh_render_data_loop_flag(const MeshRenderData *mr,
                                BMLoop *l,
                                const int cd_ofs,
                                EditLoopData *eattr)
{
  if (cd_ofs == -1) {
    return;
  }
  MLoopUV *luv = (MLoopUV *)BM_ELEM_CD_GET_VOID_P(l, cd_ofs);
  if (luv != NULL && (luv->flag & MLOOPUV_PINNED)) {
    eattr->v_flag |= VFLAG_VERT_UV_PINNED;
  }
  if (uvedit_uv_select_test_ex(mr->toolsettings, l, cd_ofs)) {
    eattr->v_flag |= VFLAG_VERT_UV_SELECT;
  }
}

void mesh_render_data_loop_edge_flag(const MeshRenderData *mr,
                                     BMLoop *l,
                                     const int cd_ofs,
                                     EditLoopData *eattr)
{
  if (cd_ofs == -1) {
    return;
  }
  if (uvedit_edge_select_test_ex(mr->toolsettings, l, cd_ofs)) {
    eattr->v_flag |= VFLAG_EDGE_UV_SELECT;
    eattr->v_flag |= VFLAG_VERT_UV_SELECT;
  }
}

/** \} */

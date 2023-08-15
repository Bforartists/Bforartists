/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup bke
 *
 * Manage edit mesh cache: #EditMeshData
 */

#include "MEM_guardedalloc.h"

#include "BLI_bounds.hh"
#include "BLI_math_vector.h"
#include "BLI_span.hh"

#include "DNA_mesh_types.h"

#include "BKE_editmesh.h"
#include "BKE_editmesh_cache.hh" /* own include */

/* -------------------------------------------------------------------- */
/** \name Ensure Data (derived from coords)
 * \{ */

void BKE_editmesh_cache_ensure_face_normals(BMEditMesh *em, blender::bke::EditMeshData *emd)
{
  if (emd->vertexCos.is_empty() || !emd->faceNos.is_empty()) {
    return;
  }
  BMesh *bm = em->bm;

  emd->faceNos.reinitialize(bm->totface);

  BM_mesh_elem_index_ensure(bm, BM_VERT);
  BMFace *efa;
  BMIter fiter;
  int i;
  BM_ITER_MESH_INDEX (efa, &fiter, bm, BM_FACES_OF_MESH, i) {
    BM_elem_index_set(efa, i); /* set_inline */
    BM_face_calc_normal_vcos(
        bm, efa, emd->faceNos[i], reinterpret_cast<const float(*)[3]>(emd->vertexCos.data()));
  }
  bm->elem_index_dirty &= ~BM_FACE;
}

void BKE_editmesh_cache_ensure_vert_normals(BMEditMesh *em, blender::bke::EditMeshData *emd)
{
  if (emd->vertexCos.is_empty() || !emd->vertexNos.is_empty()) {
    return;
  }
  BMesh *bm = em->bm;

  /* Calculate vertex normals from face normals. */
  BKE_editmesh_cache_ensure_face_normals(em, emd);

  emd->vertexNos.reinitialize(bm->totvert);

  BM_mesh_elem_index_ensure(bm, BM_FACE);
  BM_verts_calc_normal_vcos(bm,
                            reinterpret_cast<const float(*)[3]>(emd->faceNos.data()),
                            reinterpret_cast<const float(*)[3]>(emd->vertexCos.data()),
                            reinterpret_cast<float(*)[3]>(emd->vertexNos.data()));
}

void BKE_editmesh_cache_ensure_face_centers(BMEditMesh *em, blender::bke::EditMeshData *emd)
{
  if (!emd->faceCos.is_empty()) {
    return;
  }
  BMesh *bm = em->bm;

  emd->faceCos.reinitialize(bm->totface);

  BMFace *efa;
  BMIter fiter;
  int i;
  if (emd->vertexCos.is_empty()) {
    BM_ITER_MESH_INDEX (efa, &fiter, bm, BM_FACES_OF_MESH, i) {
      BM_face_calc_center_median(efa, emd->faceCos[i]);
    }
  }
  else {
    BM_mesh_elem_index_ensure(bm, BM_VERT);
    BM_ITER_MESH_INDEX (efa, &fiter, bm, BM_FACES_OF_MESH, i) {
      BM_face_calc_center_median_vcos(
          bm, efa, emd->faceCos[i], reinterpret_cast<const float(*)[3]>(emd->vertexCos.data()));
    }
  }
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Calculate Min/Max
 * \{ */

bool BKE_editmesh_cache_calc_minmax(BMEditMesh *em,
                                    blender::bke::EditMeshData *emd,
                                    float min[3],
                                    float max[3])
{
  using namespace blender;
  BMesh *bm = em->bm;
  if (bm->totvert == 0) {
    zero_v3(min);
    zero_v3(max);
    return false;
  }

  if (emd->vertexCos.is_empty()) {
    BMVert *eve;
    BMIter iter;
    BM_ITER_MESH (eve, &iter, bm, BM_VERTS_OF_MESH) {
      minmax_v3v3_v3(min, max, eve->co);
    }
  }
  else {
    const Bounds<float3> bounds = *bounds::min_max(emd->vertexCos.as_span());
    copy_v3_v3(min, math::min(bounds.min, float3(min)));
    copy_v3_v3(max, math::max(bounds.max, float3(max)));
  }
  return true;
}

/** \} */

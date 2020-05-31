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
 */

/** \file
 * \ingroup bke
 *
 * Manage edit mesh cache: #EditMeshData
 */

#include "MEM_guardedalloc.h"

#include "BLI_math_vector.h"

#include "DNA_mesh_types.h"

#include "BKE_editmesh.h"
#include "BKE_editmesh_cache.h" /* own include */

/* -------------------------------------------------------------------- */
/** \name Ensure Data (derived from coords)
 * \{ */

void BKE_editmesh_cache_ensure_poly_normals(BMEditMesh *em, EditMeshData *emd)
{
  if (!(emd->vertexCos && (emd->polyNos == NULL))) {
    return;
  }

  BMesh *bm = em->bm;
  const float(*vertexCos)[3];
  float(*polyNos)[3];

  BMFace *efa;
  BMIter fiter;
  int i;

  BM_mesh_elem_index_ensure(bm, BM_VERT);

  polyNos = MEM_mallocN(sizeof(*polyNos) * bm->totface, __func__);

  vertexCos = emd->vertexCos;

  BM_ITER_MESH_INDEX (efa, &fiter, bm, BM_FACES_OF_MESH, i) {
    BM_elem_index_set(efa, i); /* set_inline */
    BM_face_calc_normal_vcos(bm, efa, polyNos[i], vertexCos);
  }
  bm->elem_index_dirty &= ~BM_FACE;

  emd->polyNos = (const float(*)[3])polyNos;
}

void BKE_editmesh_cache_ensure_vert_normals(BMEditMesh *em, EditMeshData *emd)
{
  if (!(emd->vertexCos && (emd->vertexNos == NULL))) {
    return;
  }

  BMesh *bm = em->bm;
  const float(*vertexCos)[3], (*polyNos)[3];
  float(*vertexNos)[3];

  /* calculate vertex normals from poly normals */
  BKE_editmesh_cache_ensure_poly_normals(em, emd);

  BM_mesh_elem_index_ensure(bm, BM_FACE);

  polyNos = emd->polyNos;
  vertexCos = emd->vertexCos;
  vertexNos = MEM_callocN(sizeof(*vertexNos) * bm->totvert, __func__);

  BM_verts_calc_normal_vcos(bm, polyNos, vertexCos, vertexNos);

  emd->vertexNos = (const float(*)[3])vertexNos;
}

void BKE_editmesh_cache_ensure_poly_centers(BMEditMesh *em, EditMeshData *emd)
{
  if (emd->polyCos != NULL) {
    return;
  }
  BMesh *bm = em->bm;
  float(*polyCos)[3];

  BMFace *efa;
  BMIter fiter;
  int i;

  polyCos = MEM_mallocN(sizeof(*polyCos) * bm->totface, __func__);

  if (emd->vertexCos) {
    const float(*vertexCos)[3];
    vertexCos = emd->vertexCos;

    BM_mesh_elem_index_ensure(bm, BM_VERT);

    BM_ITER_MESH_INDEX (efa, &fiter, bm, BM_FACES_OF_MESH, i) {
      BM_face_calc_center_median_vcos(bm, efa, polyCos[i], vertexCos);
    }
  }
  else {
    BM_ITER_MESH_INDEX (efa, &fiter, bm, BM_FACES_OF_MESH, i) {
      BM_face_calc_center_median(efa, polyCos[i]);
    }
  }

  emd->polyCos = (const float(*)[3])polyCos;
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Calculate Min/Max
 * \{ */

bool BKE_editmesh_cache_calc_minmax(struct BMEditMesh *em,
                                    struct EditMeshData *emd,
                                    float min[3],
                                    float max[3])
{
  BMesh *bm = em->bm;
  BMVert *eve;
  BMIter iter;
  int i;

  if (bm->totvert) {
    if (emd->vertexCos) {
      BM_ITER_MESH_INDEX (eve, &iter, bm, BM_VERTS_OF_MESH, i) {
        minmax_v3v3_v3(min, max, emd->vertexCos[i]);
      }
    }
    else {
      BM_ITER_MESH (eve, &iter, bm, BM_VERTS_OF_MESH) {
        minmax_v3v3_v3(min, max, eve->co);
      }
    }
    return true;
  }
  else {
    zero_v3(min);
    zero_v3(max);
    return false;
  }
}

/** \} */

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
 * The Original Code is Copyright (C) 2001-2002 by NaN Holding BV.
 * All rights reserved.
 */

/** \file
 * \ingroup edtransform
 */

#include "DNA_mesh_types.h"
#include "DNA_meshdata_types.h"

#include "MEM_guardedalloc.h"

#include "BLI_alloca.h"
#include "BLI_bitmap.h"
#include "BLI_linklist_stack.h"
#include "BLI_math.h"
#include "BLI_memarena.h"

#include "BKE_context.h"
#include "BKE_crazyspace.h"
#include "BKE_editmesh.h"
#include "BKE_mesh.h"
#include "BKE_modifier.h"
#include "BKE_scene.h"

#include "ED_mesh.h"

#include "DEG_depsgraph_query.h"

#include "transform.h"
#include "transform_mode.h"
#include "transform_snap.h"

/* Own include. */
#include "transform_convert.h"

/* -------------------------------------------------------------------- */
/** \name Island Creation
 *
 * \{ */

struct TransIslandData {
  float (*center)[3];
  float (*axismtx)[3][3];
  int island_tot;
  int *island_vert_map;
};

static void editmesh_islands_info_calc(BMEditMesh *em,
                                       const bool calc_single_islands,
                                       const bool calc_island_center,
                                       const bool calc_island_axismtx,
                                       struct TransIslandData *r_island_data)
{
  BMesh *bm = em->bm;
  char htype;
  char itype;
  int i;

  /* group vars */
  float(*center)[3] = NULL;
  float(*axismtx)[3][3] = NULL;
  int *groups_array;
  int(*group_index)[2];
  int group_tot;
  void **ele_array;

  int *vert_map;

  if (em->selectmode & (SCE_SELECT_VERTEX | SCE_SELECT_EDGE)) {
    groups_array = MEM_mallocN(sizeof(*groups_array) * bm->totedgesel, __func__);
    group_tot = BM_mesh_calc_edge_groups(
        bm, groups_array, &group_index, NULL, NULL, BM_ELEM_SELECT);

    htype = BM_EDGE;
    itype = BM_VERTS_OF_EDGE;
  }
  else { /* (bm->selectmode & SCE_SELECT_FACE) */
    groups_array = MEM_mallocN(sizeof(*groups_array) * bm->totfacesel, __func__);
    group_tot = BM_mesh_calc_face_groups(
        bm, groups_array, &group_index, NULL, NULL, BM_ELEM_SELECT, BM_VERT);

    htype = BM_FACE;
    itype = BM_VERTS_OF_FACE;
  }

  if (calc_island_center) {
    center = MEM_mallocN(sizeof(*center) * group_tot, __func__);
  }

  if (calc_island_axismtx) {
    axismtx = MEM_mallocN(sizeof(*axismtx) * group_tot, __func__);
  }

  vert_map = MEM_mallocN(sizeof(*vert_map) * bm->totvert, __func__);
  /* we shouldn't need this, but with incorrect selection flushing
   * its possible we have a selected vertex that's not in a face,
   * for now best not crash in that case. */
  copy_vn_i(vert_map, bm->totvert, -1);

  BM_mesh_elem_table_ensure(bm, htype);
  ele_array = (htype == BM_FACE) ? (void **)bm->ftable : (void **)bm->etable;

  BM_mesh_elem_index_ensure(bm, BM_VERT);

  /* may be an edge OR a face array */
  for (i = 0; i < group_tot; i++) {
    BMEditSelection ese = {NULL};

    const int fg_sta = group_index[i][0];
    const int fg_len = group_index[i][1];
    float co[3], no[3], tangent[3];
    int j;

    zero_v3(co);
    zero_v3(no);
    zero_v3(tangent);

    ese.htype = htype;

    /* loop on each face or edge in this group:
     * - assign r_vert_map
     * - calculate (co, no)
     */
    for (j = 0; j < fg_len; j++) {
      ese.ele = ele_array[groups_array[fg_sta + j]];

      if (center) {
        float tmp_co[3];
        BM_editselection_center(&ese, tmp_co);
        add_v3_v3(co, tmp_co);
      }

      if (axismtx) {
        float tmp_no[3], tmp_tangent[3];
        BM_editselection_normal(&ese, tmp_no);
        BM_editselection_plane(&ese, tmp_tangent);
        add_v3_v3(no, tmp_no);
        add_v3_v3(tangent, tmp_tangent);
      }

      {
        /* setup vertex map */
        BMIter iter;
        BMVert *v;

        /* connected edge-verts */
        BM_ITER_ELEM (v, &iter, ese.ele, itype) {
          vert_map[BM_elem_index_get(v)] = i;
        }
      }
    }

    if (center) {
      mul_v3_v3fl(center[i], co, 1.0f / (float)fg_len);
    }

    if (axismtx) {
      if (createSpaceNormalTangent(axismtx[i], no, tangent)) {
        /* pass */
      }
      else {
        if (normalize_v3(no) != 0.0f) {
          axis_dominant_v3_to_m3(axismtx[i], no);
          invert_m3(axismtx[i]);
        }
        else {
          unit_m3(axismtx[i]);
        }
      }
    }
  }

  MEM_freeN(groups_array);
  MEM_freeN(group_index);

  /* for PET we need islands of 1 so connected vertices can use it with V3D_AROUND_LOCAL_ORIGINS */
  if (calc_single_islands) {
    BMIter viter;
    BMVert *v;
    int group_tot_single = 0;

    BM_ITER_MESH_INDEX (v, &viter, bm, BM_VERTS_OF_MESH, i) {
      if (BM_elem_flag_test(v, BM_ELEM_SELECT) && (vert_map[i] == -1)) {
        group_tot_single += 1;
      }
    }

    if (group_tot_single != 0) {
      if (center) {
        center = MEM_reallocN(center, sizeof(*center) * (group_tot + group_tot_single));
      }
      if (axismtx) {
        axismtx = MEM_reallocN(axismtx, sizeof(*axismtx) * (group_tot + group_tot_single));
      }

      BM_ITER_MESH_INDEX (v, &viter, bm, BM_VERTS_OF_MESH, i) {
        if (BM_elem_flag_test(v, BM_ELEM_SELECT) && (vert_map[i] == -1)) {
          vert_map[i] = group_tot;
          if (center) {
            copy_v3_v3(center[group_tot], v->co);
          }
          if (axismtx) {
            if (is_zero_v3(v->no) != 0.0f) {
              axis_dominant_v3_to_m3(axismtx[group_tot], v->no);
              invert_m3(axismtx[group_tot]);
            }
            else {
              unit_m3(axismtx[group_tot]);
            }
          }

          group_tot += 1;
        }
      }
    }
  }

  r_island_data->axismtx = axismtx;
  r_island_data->center = center;
  r_island_data->island_tot = group_tot;
  r_island_data->island_vert_map = vert_map;
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Connectivity Distance for Proportional Editing
 *
 * \{ */

static bool bmesh_test_dist_add(BMVert *v,
                                BMVert *v_other,
                                float *dists,
                                const float *dists_prev,
                                /* optionally track original index */
                                int *index,
                                const int *index_prev,
                                const float mtx[3][3])
{
  if ((BM_elem_flag_test(v_other, BM_ELEM_SELECT) == 0) &&
      (BM_elem_flag_test(v_other, BM_ELEM_HIDDEN) == 0)) {
    const int i = BM_elem_index_get(v);
    const int i_other = BM_elem_index_get(v_other);
    float vec[3];
    float dist_other;
    sub_v3_v3v3(vec, v->co, v_other->co);
    mul_m3_v3(mtx, vec);

    dist_other = dists_prev[i] + len_v3(vec);
    if (dist_other < dists[i_other]) {
      dists[i_other] = dist_other;
      if (index != NULL) {
        index[i_other] = index_prev[i];
      }
      return true;
    }
  }

  return false;
}

/**
 * \param mtx: Measure distance in this space.
 * \param dists: Store the closest connected distance to selected vertices.
 * \param index: Optionally store the original index we're measuring the distance to (can be NULL).
 */
static void editmesh_set_connectivity_distance(BMesh *bm,
                                               const float mtx[3][3],
                                               float *dists,
                                               int *index)
{
  BLI_LINKSTACK_DECLARE(queue, BMVert *);

  /* any BM_ELEM_TAG'd vertex is in 'queue_next', so we don't add in twice */
  BLI_LINKSTACK_DECLARE(queue_next, BMVert *);

  BLI_LINKSTACK_INIT(queue);
  BLI_LINKSTACK_INIT(queue_next);

  {
    BMIter viter;
    BMVert *v;
    int i;

    BM_ITER_MESH_INDEX (v, &viter, bm, BM_VERTS_OF_MESH, i) {
      float dist;
      BM_elem_index_set(v, i); /* set_inline */
      BM_elem_flag_disable(v, BM_ELEM_TAG);

      if (BM_elem_flag_test(v, BM_ELEM_SELECT) == 0 || BM_elem_flag_test(v, BM_ELEM_HIDDEN)) {
        dist = FLT_MAX;
        if (index != NULL) {
          index[i] = i;
        }
      }
      else {
        BLI_LINKSTACK_PUSH(queue, v);
        dist = 0.0f;
        if (index != NULL) {
          index[i] = i;
        }
      }

      dists[i] = dist;
    }
    bm->elem_index_dirty &= ~BM_VERT;
  }

  /* need to be very careful of feedback loops here, store previous dist's to avoid feedback */
  float *dists_prev = MEM_dupallocN(dists);
  int *index_prev = MEM_dupallocN(index); /* may be NULL */

  do {
    BMVert *v;
    LinkNode *lnk;

    /* this is correct but slow to do each iteration,
     * instead sync the dist's while clearing BM_ELEM_TAG (below) */
#if 0
    memcpy(dists_prev, dists, sizeof(float) * bm->totvert);
#endif

    while ((v = BLI_LINKSTACK_POP(queue))) {
      BLI_assert(dists[BM_elem_index_get(v)] != FLT_MAX);

      /* connected edge-verts */
      if (v->e != NULL) {
        BMEdge *e_iter, *e_first;

        e_iter = e_first = v->e;

        /* would normally use BM_EDGES_OF_VERT, but this runs so often,
         * its faster to iterate on the data directly */
        do {

          if (BM_elem_flag_test(e_iter, BM_ELEM_HIDDEN) == 0) {

            /* edge distance */
            {
              BMVert *v_other = BM_edge_other_vert(e_iter, v);
              if (bmesh_test_dist_add(v, v_other, dists, dists_prev, index, index_prev, mtx)) {
                if (BM_elem_flag_test(v_other, BM_ELEM_TAG) == 0) {
                  BM_elem_flag_enable(v_other, BM_ELEM_TAG);
                  BLI_LINKSTACK_PUSH(queue_next, v_other);
                }
              }
            }

            /* face distance */
            if (e_iter->l) {
              BMLoop *l_iter_radial, *l_first_radial;
              /**
               * imaginary edge diagonally across quad.
               * \note This takes advantage of the rules of winding that we
               * know 2 or more of a verts edges wont reference the same face twice.
               * Also, if the edge is hidden, the face will be hidden too.
               */
              l_iter_radial = l_first_radial = e_iter->l;

              do {
                if ((l_iter_radial->v == v) && (l_iter_radial->f->len == 4) &&
                    (BM_elem_flag_test(l_iter_radial->f, BM_ELEM_HIDDEN) == 0)) {
                  BMVert *v_other = l_iter_radial->next->next->v;
                  if (bmesh_test_dist_add(v, v_other, dists, dists_prev, index, index_prev, mtx)) {
                    if (BM_elem_flag_test(v_other, BM_ELEM_TAG) == 0) {
                      BM_elem_flag_enable(v_other, BM_ELEM_TAG);
                      BLI_LINKSTACK_PUSH(queue_next, v_other);
                    }
                  }
                }
              } while ((l_iter_radial = l_iter_radial->radial_next) != l_first_radial);
            }
          }
        } while ((e_iter = BM_DISK_EDGE_NEXT(e_iter, v)) != e_first);
      }
    }

    /* clear for the next loop */
    for (lnk = queue_next; lnk; lnk = lnk->next) {
      BMVert *v_link = lnk->link;
      const int i = BM_elem_index_get(v_link);

      BM_elem_flag_disable(v_link, BM_ELEM_TAG);

      /* keep in sync, avoid having to do full memcpy each iteration */
      dists_prev[i] = dists[i];
      if (index != NULL) {
        index_prev[i] = index[i];
      }
    }

    BLI_LINKSTACK_SWAP(queue, queue_next);

    /* none should be tagged now since 'queue_next' is empty */
    BLI_assert(BM_iter_mesh_count_flag(BM_VERTS_OF_MESH, bm, BM_ELEM_TAG, true) == 0);

  } while (BLI_LINKSTACK_SIZE(queue));

  BLI_LINKSTACK_FREE(queue);
  BLI_LINKSTACK_FREE(queue_next);

  MEM_freeN(dists_prev);
  if (index_prev != NULL) {
    MEM_freeN(index_prev);
  }
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name TransDataMirror Creation
 *
 * \{ */

/* Used for both mirror epsilon and TD_MIRROR_EDGE_ */
#define TRANSFORM_MAXDIST_MIRROR 0.00002f

struct MirrorDataVert {
  int index;
  int flag;
};

struct TransMirrorData {
  struct MirrorDataVert *vert_map;
  int mirror_elem_len;
};

static bool is_in_quadrant_v3(const float co[3], const int quadrant[3], const float epsilon)
{
  if (quadrant[0] && ((co[0] * quadrant[0]) < -epsilon)) {
    return false;
  }
  if (quadrant[1] && ((co[1] * quadrant[1]) < -epsilon)) {
    return false;
  }
  if (quadrant[2] && ((co[2] * quadrant[2]) < -epsilon)) {
    return false;
  }
  return true;
}

static void editmesh_mirror_data_calc(BMEditMesh *em,
                                      const bool use_select,
                                      const bool use_topology,
                                      const bool mirror_axis[3],
                                      struct TransMirrorData *r_mirror_data)
{
  struct MirrorDataVert *vert_map;

  BMesh *bm = em->bm;
  BMVert *eve;
  BMIter iter;
  int i, flag, totvert = bm->totvert;

  vert_map = MEM_mallocN(totvert * sizeof(*vert_map), __func__);

  float select_sum[3] = {0};
  BM_ITER_MESH_INDEX (eve, &iter, bm, BM_VERTS_OF_MESH, i) {
    vert_map[i] = (struct MirrorDataVert){-1, 0};
    if (BM_elem_flag_test(eve, BM_ELEM_HIDDEN)) {
      continue;
    }
    if (BM_elem_flag_test(eve, BM_ELEM_SELECT)) {
      add_v3_v3(select_sum, eve->co);
    }
  }

  /* Tag only elements that will be transformed within the quadrant. */
  int quadrant[3];
  for (int a = 0; a < 3; a++) {
    if (mirror_axis[a]) {
      quadrant[a] = select_sum[a] >= 0.0f ? 1 : -1;
    }
    else {
      quadrant[a] = 0;
    }
  }

  uint mirror_elem_len = 0;
  int *index[3] = {NULL, NULL, NULL};
  bool test_selected_only = use_select && (mirror_axis[0] + mirror_axis[1] + mirror_axis[2]) == 1;
  for (int a = 0; a < 3; a++) {
    if (!mirror_axis[a]) {
      continue;
    }

    index[a] = MEM_mallocN(totvert * sizeof(*index[a]), __func__);
    EDBM_verts_mirror_cache_begin_ex(
        em, a, false, test_selected_only, use_topology, TRANSFORM_MAXDIST_MIRROR, index[a]);

    flag = TD_MIRROR_X << a;
    BM_ITER_MESH_INDEX (eve, &iter, bm, BM_VERTS_OF_MESH, i) {
      int i_mirr = index[a][i];
      if (i_mirr < 0) {
        continue;
      }
      if (BM_elem_flag_test(eve, BM_ELEM_HIDDEN)) {
        continue;
      }
      if (use_select && !BM_elem_flag_test(eve, BM_ELEM_SELECT)) {
        continue;
      }
      if (!is_in_quadrant_v3(eve->co, quadrant, TRANSFORM_MAXDIST_MIRROR)) {
        continue;
      }

      vert_map[i_mirr] = (struct MirrorDataVert){i, flag};
      mirror_elem_len++;
    }
  }

  if (mirror_elem_len) {
    for (int a = 0; a < 3; a++) {
      if (!mirror_axis[a]) {
        continue;
      }

      flag = TD_MIRROR_X << a;
      for (i = 0; i < totvert; i++) {
        int i_mirr = index[a][i];
        if (i_mirr < 0) {
          continue;
        }
        if (vert_map[i].index != -1 && !(vert_map[i].flag & flag)) {
          if (vert_map[i_mirr].index == -1) {
            mirror_elem_len++;
          }
          vert_map[i_mirr].index = vert_map[i].index;
          vert_map[i_mirr].flag |= vert_map[i].flag | flag;
        }
      }
    }
  }
  else {
    MEM_freeN(vert_map);
    vert_map = NULL;
  }

  MEM_SAFE_FREE(index[0]);
  MEM_SAFE_FREE(index[1]);
  MEM_SAFE_FREE(index[2]);

  r_mirror_data->vert_map = vert_map;
  r_mirror_data->mirror_elem_len = mirror_elem_len;
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Edit Mesh Verts Transform Creation
 *
 * \{ */

static void transdata_center_get(const struct TransIslandData *island_data,
                                 const int island_index,
                                 const float iloc[3],
                                 float r_center[3])
{
  if (island_data->center && island_index != -1) {
    copy_v3_v3(r_center, island_data->center[island_index]);
  }
  else {
    copy_v3_v3(r_center, iloc);
  }
}

/* way to overwrite what data is edited with transform */
static void VertsToTransData(TransInfo *t,
                             TransData *td,
                             TransDataExtension *tx,
                             BMEditMesh *em,
                             BMVert *eve,
                             float *bweight,
                             const struct TransIslandData *island_data,
                             const int island_index)
{
  float *no, _no[3];
  BLI_assert(BM_elem_flag_test(eve, BM_ELEM_HIDDEN) == 0);

  td->flag = 0;
  // if (key)
  //  td->loc = key->co;
  // else
  td->loc = eve->co;
  copy_v3_v3(td->iloc, td->loc);

  if ((t->mode == TFM_SHRINKFATTEN) && (em->selectmode & SCE_SELECT_FACE) &&
      BM_elem_flag_test(eve, BM_ELEM_SELECT) &&
      (BM_vert_calc_normal_ex(eve, BM_ELEM_SELECT, _no))) {
    no = _no;
  }
  else {
    no = eve->no;
  }

  transdata_center_get(island_data, island_index, td->iloc, td->center);

  if ((island_index != -1) && island_data->axismtx) {
    copy_m3_m3(td->axismtx, island_data->axismtx[island_index]);
  }
  else if (t->around == V3D_AROUND_LOCAL_ORIGINS) {
    createSpaceNormal(td->axismtx, no);
  }
  else {
    /* Setting normals */
    copy_v3_v3(td->axismtx[2], no);
    td->axismtx[0][0] = td->axismtx[0][1] = td->axismtx[0][2] = td->axismtx[1][0] =
        td->axismtx[1][1] = td->axismtx[1][2] = 0.0f;
  }

  td->ext = NULL;
  td->val = NULL;
  td->extra = eve;
  if (t->mode == TFM_BWEIGHT) {
    td->val = bweight;
    td->ival = *bweight;
  }
  else if (t->mode == TFM_SKIN_RESIZE) {
    MVertSkin *vs = CustomData_bmesh_get(&em->bm->vdata, eve->head.data, CD_MVERT_SKIN);
    if (vs) {
      /* skin node size */
      td->ext = tx;
      copy_v3_v3(tx->isize, vs->radius);
      tx->size = vs->radius;
      td->val = vs->radius;
    }
    else {
      td->flag |= TD_SKIP;
    }
  }
  else if (t->mode == TFM_SHRINKFATTEN) {
    td->ext = tx;
    tx->isize[0] = BM_vert_calc_shell_factor_ex(eve, no, BM_ELEM_SELECT);
  }
}

void createTransEditVerts(TransInfo *t)
{
  FOREACH_TRANS_DATA_CONTAINER (t, tc) {
    TransDataExtension *tx = NULL;
    BMEditMesh *em = BKE_editmesh_from_object(tc->obedit);
    Mesh *me = tc->obedit->data;
    BMesh *bm = em->bm;
    BMVert *eve;
    BMIter iter;
    float mtx[3][3], smtx[3][3];
    int a;
    const int prop_mode = (t->flag & T_PROP_EDIT) ? (t->flag & T_PROP_EDIT_ALL) : 0;

    struct TransIslandData island_data = {NULL};
    struct TransMirrorData mirror_data = {NULL};

    /**
     * Quick check if we can transform.
     *
     * \note ignore modes here, even in edge/face modes,
     * transform data is created by selected vertices.
     */

    /* Support other objects using PET to adjust these, unless connected is enabled. */
    if ((!prop_mode || (prop_mode & T_PROP_CONNECTED)) && (bm->totvertsel == 0)) {
      continue;
    }

    int data_len = 0;
    if (prop_mode) {
      BM_ITER_MESH (eve, &iter, bm, BM_VERTS_OF_MESH) {
        if (!BM_elem_flag_test(eve, BM_ELEM_HIDDEN)) {
          data_len++;
        }
      }
    }
    else {
      data_len = bm->totvertsel;
    }

    if (data_len == 0) {
      continue;
    }

    /* Snap rotation along normal needs a common axis for whole islands,
     * otherwise one get random crazy results, see T59104.
     * However, we do not want to use the island center for the pivot/translation reference. */
    const bool is_snap_rotate = ((t->mode == TFM_TRANSLATION) &&
                                 /* There is not guarantee that snapping
                                  * is initialized yet at this point... */
                                 (usingSnappingNormal(t) ||
                                  (t->settings->snap_flag & SCE_SNAP_ROTATE) != 0) &&
                                 (t->around != V3D_AROUND_LOCAL_ORIGINS));

    /* Even for translation this is needed because of island-orientation, see: T51651. */
    const bool is_island_center = (t->around == V3D_AROUND_LOCAL_ORIGINS) || is_snap_rotate;
    if (is_island_center) {
      /* In this specific case, near-by vertices will need to know
       * the island of the nearest connected vertex. */
      const bool calc_single_islands = ((prop_mode & T_PROP_CONNECTED) &&
                                        (t->around == V3D_AROUND_LOCAL_ORIGINS) &&
                                        (em->selectmode & SCE_SELECT_VERTEX));

      const bool calc_island_center = !is_snap_rotate;
      /* The island axismtx is only necessary in some modes.
       * TODO(Germano): Extend the list to exclude other modes. */
      const bool calc_island_axismtx = !ELEM(t->mode, TFM_SHRINKFATTEN);

      editmesh_islands_info_calc(
          em, calc_single_islands, calc_island_center, calc_island_axismtx, &island_data);
    }

    copy_m3_m4(mtx, tc->obedit->obmat);
    /* we use a pseudo-inverse so that when one of the axes is scaled to 0,
     * matrix inversion still works and we can still moving along the other */
    pseudoinverse_m3_m3(smtx, mtx, PSEUDOINVERSE_EPSILON);

    /* Original index of our connected vertex when connected distances are calculated.
     * Optional, allocate if needed. */
    int *dists_index = NULL;
    float *dists = NULL;
    if (prop_mode & T_PROP_CONNECTED) {
      dists = MEM_mallocN(bm->totvert * sizeof(float), __func__);
      if (is_island_center) {
        dists_index = MEM_mallocN(bm->totvert * sizeof(int), __func__);
      }
      editmesh_set_connectivity_distance(em->bm, mtx, dists, dists_index);
    }

    /* Create TransDataMirror. */
    if (tc->use_mirror_axis_any) {
      bool use_topology = (me->editflag & ME_EDIT_MIRROR_TOPO) != 0;
      bool use_select = (t->flag & T_PROP_EDIT) == 0;
      bool mirror_axis[3] = {tc->use_mirror_axis_x, tc->use_mirror_axis_y, tc->use_mirror_axis_z};
      editmesh_mirror_data_calc(em, use_select, use_topology, mirror_axis, &mirror_data);

      if (mirror_data.vert_map) {
        tc->data_mirror_len = mirror_data.mirror_elem_len;
        tc->data_mirror = MEM_mallocN(mirror_data.mirror_elem_len * sizeof(*tc->data_mirror),
                                      __func__);

        BM_ITER_MESH_INDEX (eve, &iter, bm, BM_VERTS_OF_MESH, a) {
          if (prop_mode || BM_elem_flag_test(eve, BM_ELEM_SELECT)) {
            if (mirror_data.vert_map[a].index != -1) {
              data_len--;
            }
          }
        }
      }
    }

    /* Create TransData. */
    BLI_assert(data_len >= 1);
    tc->data_len = data_len;
    tc->data = MEM_callocN(data_len * sizeof(TransData), "TransObData(Mesh EditMode)");
    if (ELEM(t->mode, TFM_SKIN_RESIZE, TFM_SHRINKFATTEN)) {
      /* warning, this is overkill, we only need 2 extra floats,
       * but this stores loads of extra stuff, for TFM_SHRINKFATTEN its even more overkill
       * since we may not use the 'alt' transform mode to maintain shell thickness,
       * but with generic transform code its hard to lazy init vars */
      tx = tc->data_ext = MEM_callocN(tc->data_len * sizeof(TransDataExtension),
                                      "TransObData ext");
    }

    /* detect CrazySpace [tm] */
    float(*quats)[4] = NULL;
    float(*defmats)[3][3] = NULL;
    if (BKE_modifiers_get_cage_index(t->scene, tc->obedit, NULL, 1) != -1) {
      float(*defcos)[3] = NULL;
      int totleft = -1;
      if (BKE_modifiers_is_correctable_deformed(t->scene, tc->obedit)) {
        BKE_scene_graph_evaluated_ensure(t->depsgraph, CTX_data_main(t->context));

        /* Use evaluated state because we need b-bone cache. */
        Scene *scene_eval = (Scene *)DEG_get_evaluated_id(t->depsgraph, &t->scene->id);
        Object *obedit_eval = (Object *)DEG_get_evaluated_id(t->depsgraph, &tc->obedit->id);
        BMEditMesh *em_eval = BKE_editmesh_from_object(obedit_eval);
        /* check if we can use deform matrices for modifier from the
         * start up to stack, they are more accurate than quats */
        totleft = BKE_crazyspace_get_first_deform_matrices_editbmesh(
            t->depsgraph, scene_eval, obedit_eval, em_eval, &defmats, &defcos);
      }

      /* if we still have more modifiers, also do crazyspace
       * correction with quats, relative to the coordinates after
       * the modifiers that support deform matrices (defcos) */

#if 0 /* TODO, fix crazyspace+extrude so it can be enabled for general use - campbell */
      if ((totleft > 0) || (totleft == -1))
#else
      if (totleft > 0)
#endif
      {
        float(*mappedcos)[3] = NULL;
        mappedcos = BKE_crazyspace_get_mapped_editverts(t->depsgraph, tc->obedit);
        quats = MEM_mallocN(em->bm->totvert * sizeof(*quats), "crazy quats");
        BKE_crazyspace_set_quats_editmesh(em, defcos, mappedcos, quats, !prop_mode);
        if (mappedcos) {
          MEM_freeN(mappedcos);
        }
      }

      if (defcos) {
        MEM_freeN(defcos);
      }
    }

    int cd_vert_bweight_offset = -1;
    if (t->mode == TFM_BWEIGHT) {
      BM_mesh_cd_flag_ensure(bm, BKE_mesh_from_object(tc->obedit), ME_CDFLAG_VERT_BWEIGHT);
      cd_vert_bweight_offset = CustomData_get_offset(&bm->vdata, CD_BWEIGHT);
    }

    TransData *tob = tc->data;
    TransDataMirror *td_mirror = tc->data_mirror;
    BM_ITER_MESH_INDEX (eve, &iter, bm, BM_VERTS_OF_MESH, a) {
      if (BM_elem_flag_test(eve, BM_ELEM_HIDDEN)) {
        continue;
      }
      else {
        int island_index = -1;
        if (island_data.island_vert_map) {
          const int connected_index = (dists_index && dists_index[a] != -1) ? dists_index[a] : a;
          island_index = island_data.island_vert_map[connected_index];
        }

        if (mirror_data.vert_map && mirror_data.vert_map[a].index != -1) {
          int elem_index = mirror_data.vert_map[a].index;
          BMVert *v_src = BM_vert_at_index(bm, elem_index);

          if (BM_elem_flag_test(eve, BM_ELEM_SELECT)) {
            mirror_data.vert_map[a].flag |= TD_SELECTED;
          }

          td_mirror->extra = eve;
          td_mirror->loc = eve->co;
          copy_v3_v3(td_mirror->iloc, eve->co);
          td_mirror->flag = mirror_data.vert_map[a].flag;
          td_mirror->loc_src = v_src->co;
          transdata_center_get(&island_data, island_index, td_mirror->iloc, td_mirror->center);

          td_mirror++;
        }
        else if (prop_mode || BM_elem_flag_test(eve, BM_ELEM_SELECT)) {
          float *bweight = (cd_vert_bweight_offset != -1) ?
                               BM_ELEM_CD_GET_VOID_P(eve, cd_vert_bweight_offset) :
                               NULL;

          /* Do not use the island center in case we are using islands
           * only to get axis for snap/rotate to normal... */
          VertsToTransData(t, tob, tx, em, eve, bweight, &island_data, island_index);
          if (tx) {
            tx++;
          }

          /* selected */
          if (BM_elem_flag_test(eve, BM_ELEM_SELECT)) {
            tob->flag |= TD_SELECTED;
          }

          if (prop_mode) {
            if (prop_mode & T_PROP_CONNECTED) {
              tob->dist = dists[a];
            }
            else {
              tob->flag |= TD_NOTCONNECTED;
              tob->dist = FLT_MAX;
            }
          }

          /* CrazySpace */
          const bool use_quats = quats && BM_elem_flag_test(eve, BM_ELEM_TAG);
          if (use_quats || defmats) {
            float mat[3][3], qmat[3][3], imat[3][3];

            /* Use both or either quat and defmat correction. */
            if (use_quats) {
              quat_to_mat3(qmat, quats[BM_elem_index_get(eve)]);

              if (defmats) {
                mul_m3_series(mat, defmats[a], qmat, mtx);
              }
              else {
                mul_m3_m3m3(mat, mtx, qmat);
              }
            }
            else {
              mul_m3_m3m3(mat, mtx, defmats[a]);
            }

            invert_m3_m3(imat, mat);

            copy_m3_m3(tob->smtx, imat);
            copy_m3_m3(tob->mtx, mat);
          }
          else {
            copy_m3_m3(tob->smtx, smtx);
            copy_m3_m3(tob->mtx, mtx);
          }

          if (tc->use_mirror_axis_any) {
            if (tc->use_mirror_axis_x && fabsf(tob->loc[0]) < TRANSFORM_MAXDIST_MIRROR) {
              tob->flag |= TD_MIRROR_EDGE_X;
            }
            if (tc->use_mirror_axis_y && fabsf(tob->loc[1]) < TRANSFORM_MAXDIST_MIRROR) {
              tob->flag |= TD_MIRROR_EDGE_Y;
            }
            if (tc->use_mirror_axis_z && fabsf(tob->loc[2]) < TRANSFORM_MAXDIST_MIRROR) {
              tob->flag |= TD_MIRROR_EDGE_Z;
            }
          }

          tob++;
        }
      }
    }

    if (island_data.center) {
      MEM_freeN(island_data.center);
    }
    if (island_data.axismtx) {
      MEM_freeN(island_data.axismtx);
    }
    if (island_data.island_vert_map) {
      MEM_freeN(island_data.island_vert_map);
    }
    if (mirror_data.vert_map) {
      MEM_freeN(mirror_data.vert_map);
    }
    if (quats) {
      MEM_freeN(quats);
    }
    if (defmats) {
      MEM_freeN(defmats);
    }
    if (dists) {
      MEM_freeN(dists);
    }
    if (dists_index) {
      MEM_freeN(dists_index);
    }
  }
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name CustomData Layer Correction (for meshes)
 *
 * \{ */

struct TransCustomDataLayerVert {
  BMVert *v;
  float co_orig_3d[3];
  struct LinkNode **cd_loop_groups;
};

struct TransCustomDataLayer {
  BMesh *bm;

  int cd_loop_mdisp_offset;

  /** map {BMVert: TransCustomDataLayerVert} */
  struct GHash *origverts;
  struct GHash *origfaces;
  struct BMesh *bm_origfaces;

  struct MemArena *arena;
  /** Number of math BMLoop layers. */
  int layer_math_map_num;
  /** Array size of 'layer_math_map_num'
   * maps TransCustomDataLayerVert.cd_group index to absolute CustomData layer index */
  int *layer_math_map;

  /* Array with all elements transformed. */
  struct TransCustomDataLayerVert *data;
  int data_len;
};

static void trans_mesh_customdata_free_cb(struct TransInfo *UNUSED(t),
                                          struct TransDataContainer *UNUSED(tc),
                                          struct TransCustomData *custom_data)
{
  struct TransCustomDataLayer *tcld = custom_data->data;
  bmesh_edit_end(tcld->bm, BMO_OPTYPE_FLAG_UNTAN_MULTIRES);

  if (tcld->bm_origfaces) {
    BM_mesh_free(tcld->bm_origfaces);
  }
  if (tcld->origfaces) {
    BLI_ghash_free(tcld->origfaces, NULL, NULL);
  }
  if (tcld->origverts) {
    BLI_ghash_free(tcld->origverts, NULL, NULL);
  }
  if (tcld->arena) {
    BLI_memarena_free(tcld->arena);
  }
  if (tcld->layer_math_map) {
    MEM_freeN(tcld->layer_math_map);
  }

  MEM_freeN(tcld);
  custom_data->data = NULL;
}

static void create_trans_vert_customdata_layer(BMVert *v,
                                               struct TransCustomDataLayer *tcld,
                                               struct TransCustomDataLayerVert *r_tcld_vert)
{
  BMesh *bm = tcld->bm;
  BMIter liter;
  int j, l_num;
  float *loop_weights;

  /* copy face data */
  // BM_ITER_ELEM (l, &liter, sv->v, BM_LOOPS_OF_VERT) {
  BM_iter_init(&liter, bm, BM_LOOPS_OF_VERT, v);
  l_num = liter.count;
  loop_weights = BLI_array_alloca(loop_weights, l_num);
  for (j = 0; j < l_num; j++) {
    BMLoop *l = BM_iter_step(&liter);
    BMLoop *l_prev, *l_next;
    void **val_p;
    if (!BLI_ghash_ensure_p(tcld->origfaces, l->f, &val_p)) {
      BMFace *f_copy = BM_face_copy(tcld->bm_origfaces, bm, l->f, true, true);
      *val_p = f_copy;
    }

    if ((l_prev = BM_loop_find_prev_nodouble(l, l->next, FLT_EPSILON)) &&
        (l_next = BM_loop_find_next_nodouble(l, l_prev, FLT_EPSILON))) {
      loop_weights[j] = angle_v3v3v3(l_prev->v->co, l->v->co, l_next->v->co);
    }
    else {
      loop_weights[j] = 0.0f;
    }
  }

  /* store cd_loop_groups */
  if (tcld->layer_math_map_num && (l_num != 0)) {
    r_tcld_vert->cd_loop_groups = BLI_memarena_alloc(tcld->arena,
                                                     tcld->layer_math_map_num * sizeof(void *));
    for (j = 0; j < tcld->layer_math_map_num; j++) {
      const int layer_nr = tcld->layer_math_map[j];
      r_tcld_vert->cd_loop_groups[j] = BM_vert_loop_groups_data_layer_create(
          bm, v, layer_nr, loop_weights, tcld->arena);
    }
  }
  else {
    r_tcld_vert->cd_loop_groups = NULL;
  }

  r_tcld_vert->v = v;
  copy_v3_v3(r_tcld_vert->co_orig_3d, v->co);
  BLI_ghash_insert(tcld->origverts, v, r_tcld_vert);
}

void trans_mesh_customdata_correction_init(TransInfo *t, TransDataContainer *tc)
{
  if (tc->custom.type.data) {
    /* Custom data correction has initiated before. */
    BLI_assert(tc->custom.type.free_cb == trans_mesh_customdata_free_cb);
    return;
  }
  int i;

  BMEditMesh *em = BKE_editmesh_from_object(tc->obedit);
  BMesh *bm = em->bm;

  bool use_origfaces;
  int cd_loop_mdisp_offset;
  {
    const bool has_layer_math = CustomData_has_math(&bm->ldata);
    cd_loop_mdisp_offset = CustomData_get_offset(&bm->ldata, CD_MDISPS);
    if ((t->settings->uvcalc_flag & UVCALC_TRANSFORM_CORRECT) &&
        /* don't do this at all for non-basis shape keys, too easy to
         * accidentally break uv maps or vertex colors then */
        (bm->shapenr <= 1) && (has_layer_math || (cd_loop_mdisp_offset != -1))) {
      use_origfaces = true;
    }
    else {
      use_origfaces = false;
      cd_loop_mdisp_offset = -1;
    }
  }

  if (use_origfaces) {
    /* create copies of faces for customdata projection */
    bmesh_edit_begin(bm, BMO_OPTYPE_FLAG_UNTAN_MULTIRES);

    struct GHash *origfaces = BLI_ghash_ptr_new(__func__);
    struct BMesh *bm_origfaces = BM_mesh_create(&bm_mesh_allocsize_default,
                                                &((struct BMeshCreateParams){
                                                    .use_toolflags = false,
                                                }));

    /* we need to have matching customdata */
    BM_mesh_copy_init_customdata(bm_origfaces, bm, NULL);

    int *layer_math_map = NULL;
    int layer_index_dst = 0;
    {
      /* TODO: We don't need `sod->layer_math_map` when there are no loops linked
       * to one of the sliding vertices. */
      if (CustomData_has_math(&bm->ldata)) {
        /* over alloc, only 'math' layers are indexed */
        layer_math_map = MEM_mallocN(bm->ldata.totlayer * sizeof(int), __func__);
        for (i = 0; i < bm->ldata.totlayer; i++) {
          if (CustomData_layer_has_math(&bm->ldata, i)) {
            layer_math_map[layer_index_dst++] = i;
          }
        }
        BLI_assert(layer_index_dst != 0);
      }
    }

    struct TransCustomDataLayer *tcld;
    tc->custom.type.data = tcld = MEM_mallocN(sizeof(*tcld), __func__);
    tc->custom.type.free_cb = trans_mesh_customdata_free_cb;

    tcld->bm = bm;
    tcld->origfaces = origfaces;
    tcld->bm_origfaces = bm_origfaces;
    tcld->cd_loop_mdisp_offset = cd_loop_mdisp_offset;
    tcld->layer_math_map = layer_math_map;
    tcld->layer_math_map_num = layer_index_dst;
    tcld->arena = BLI_memarena_new(BLI_MEMARENA_STD_BUFSIZE, __func__);

    int data_len = tc->data_len + tc->data_mirror_len;
    struct GHash *origverts = BLI_ghash_ptr_new_ex(__func__, data_len);
    tcld->origverts = origverts;

    struct TransCustomDataLayerVert *tcld_vert, *tcld_vert_iter;
    tcld_vert = BLI_memarena_alloc(tcld->arena, data_len * sizeof(*tcld_vert));
    tcld_vert_iter = &tcld_vert[0];

    TransData *tob;
    for (i = tc->data_len, tob = tc->data; i--; tob++, tcld_vert_iter++) {
      BMVert *v = tob->extra;
      create_trans_vert_customdata_layer(v, tcld, tcld_vert_iter);
    }

    TransDataMirror *td_mirror = tc->data_mirror;
    for (i = tc->data_mirror_len; i--; td_mirror++, tcld_vert_iter++) {
      BMVert *v = td_mirror->extra;
      create_trans_vert_customdata_layer(v, tcld, tcld_vert_iter);
    }

    tcld->data = tcld_vert;
    tcld->data_len = data_len;
  }
}

/**
 * If we're sliding the vert, return its original location, if not, the current location is good.
 */
static const float *trans_vert_orig_co_get(struct TransCustomDataLayer *tcld, BMVert *v)
{
  struct TransCustomDataLayerVert *tcld_vert = BLI_ghash_lookup(tcld->origverts, v);
  return tcld_vert ? tcld_vert->co_orig_3d : v->co;
}

static void trans_mesh_customdata_correction_apply_vert(struct TransCustomDataLayer *tcld,
                                                        struct TransCustomDataLayerVert *tcld_vert,
                                                        bool is_final)
{
  BMesh *bm = tcld->bm;
  BMVert *v = tcld_vert->v;
  const float *co_orig_3d = tcld_vert->co_orig_3d;
  struct LinkNode **cd_loop_groups = tcld_vert->cd_loop_groups;

  BMIter liter;
  int j, l_num;
  float *loop_weights;
  const bool is_moved = (len_squared_v3v3(v->co, co_orig_3d) > FLT_EPSILON);
  const bool do_loop_weight = tcld->layer_math_map_num && is_moved;
  const bool do_loop_mdisps = is_final && is_moved && (tcld->cd_loop_mdisp_offset != -1);
  const float *v_proj_axis = v->no;
  /* original (l->prev, l, l->next) projections for each loop ('l' remains unchanged) */
  float v_proj[3][3];

  if (do_loop_weight || do_loop_mdisps) {
    project_plane_normalized_v3_v3v3(v_proj[1], co_orig_3d, v_proj_axis);
  }

  // BM_ITER_ELEM (l, &liter, sv->v, BM_LOOPS_OF_VERT)
  BM_iter_init(&liter, bm, BM_LOOPS_OF_VERT, v);
  l_num = liter.count;
  loop_weights = do_loop_weight ? BLI_array_alloca(loop_weights, l_num) : NULL;
  for (j = 0; j < l_num; j++) {
    BMFace *f_copy; /* the copy of 'f' */
    BMLoop *l = BM_iter_step(&liter);

    f_copy = BLI_ghash_lookup(tcld->origfaces, l->f);

    /* only loop data, no vertex data since that contains shape keys,
     * and we do not want to mess up other shape keys */
    BM_loop_interp_from_face(bm, l, f_copy, false, false);

    /* make sure face-attributes are correct (e.g. #MLoopUV, #MLoopCol) */
    BM_elem_attrs_copy_ex(tcld->bm_origfaces, bm, f_copy, l->f, BM_ELEM_SELECT, CD_MASK_NORMAL);

    /* weight the loop */
    if (do_loop_weight) {
      const float eps = 1.0e-8f;
      const BMLoop *l_prev = l->prev;
      const BMLoop *l_next = l->next;
      const float *co_prev = trans_vert_orig_co_get(tcld, l_prev->v);
      const float *co_next = trans_vert_orig_co_get(tcld, l_next->v);
      bool co_prev_ok;
      bool co_next_ok;

      /* In the unlikely case that we're next to a zero length edge -
       * walk around the to the next.
       *
       * Since we only need to check if the vertex is in this corner,
       * its not important _which_ loop - as long as its not overlapping
       * 'sv->co_orig_3d', see: T45096. */
      project_plane_normalized_v3_v3v3(v_proj[0], co_prev, v_proj_axis);
      while (UNLIKELY(((co_prev_ok = (len_squared_v3v3(v_proj[1], v_proj[0]) > eps)) == false) &&
                      ((l_prev = l_prev->prev) != l->next))) {
        co_prev = trans_vert_orig_co_get(tcld, l_prev->v);
        project_plane_normalized_v3_v3v3(v_proj[0], co_prev, v_proj_axis);
      }
      project_plane_normalized_v3_v3v3(v_proj[2], co_next, v_proj_axis);
      while (UNLIKELY(((co_next_ok = (len_squared_v3v3(v_proj[1], v_proj[2]) > eps)) == false) &&
                      ((l_next = l_next->next) != l->prev))) {
        co_next = trans_vert_orig_co_get(tcld, l_next->v);
        project_plane_normalized_v3_v3v3(v_proj[2], co_next, v_proj_axis);
      }

      if (co_prev_ok && co_next_ok) {
        const float dist = dist_signed_squared_to_corner_v3v3v3(
            v->co, UNPACK3(v_proj), v_proj_axis);

        loop_weights[j] = (dist >= 0.0f) ? 1.0f : ((dist <= -eps) ? 0.0f : (1.0f + (dist / eps)));
        if (UNLIKELY(!isfinite(loop_weights[j]))) {
          loop_weights[j] = 0.0f;
        }
      }
      else {
        loop_weights[j] = 0.0f;
      }
    }
  }

  if (tcld->layer_math_map_num && cd_loop_groups) {
    if (do_loop_weight) {
      for (j = 0; j < tcld->layer_math_map_num; j++) {
        BM_vert_loop_groups_data_layer_merge_weights(
            bm, cd_loop_groups[j], tcld->layer_math_map[j], loop_weights);
      }
    }
    else {
      for (j = 0; j < tcld->layer_math_map_num; j++) {
        BM_vert_loop_groups_data_layer_merge(bm, cd_loop_groups[j], tcld->layer_math_map[j]);
      }
    }
  }

  /* Special handling for multires
   *
   * Interpolate from every other loop (not ideal)
   * However values will only be taken from loops which overlap other mdisps.
   * */
  if (do_loop_mdisps) {
    float(*faces_center)[3] = BLI_array_alloca(faces_center, l_num);
    BMLoop *l;

    BM_ITER_ELEM_INDEX (l, &liter, v, BM_LOOPS_OF_VERT, j) {
      BM_face_calc_center_median(l->f, faces_center[j]);
    }

    BM_ITER_ELEM_INDEX (l, &liter, v, BM_LOOPS_OF_VERT, j) {
      BMFace *f_copy = BLI_ghash_lookup(tcld->origfaces, l->f);
      float f_copy_center[3];
      BMIter liter_other;
      BMLoop *l_other;
      int j_other;

      BM_face_calc_center_median(f_copy, f_copy_center);

      BM_ITER_ELEM_INDEX (l_other, &liter_other, v, BM_LOOPS_OF_VERT, j_other) {
        BM_face_interp_multires_ex(bm,
                                   l_other->f,
                                   f_copy,
                                   faces_center[j_other],
                                   f_copy_center,
                                   tcld->cd_loop_mdisp_offset);
      }
    }
  }
}

static void trans_mesh_customdata_correction_apply(struct TransDataContainer *tc, bool is_final)
{
  struct TransCustomDataLayer *tcld = tc->custom.type.data;
  if (!tcld) {
    return;
  }

  const bool has_mdisps = (tcld->cd_loop_mdisp_offset != -1);
  struct TransCustomDataLayerVert *tcld_vert_iter = &tcld->data[0];

  for (int i = tcld->data_len; i--; tcld_vert_iter++) {
    if (tcld_vert_iter->cd_loop_groups || has_mdisps) {
      trans_mesh_customdata_correction_apply_vert(tcld, tcld_vert_iter, is_final);
    }
  }
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Recalc Mesh Data
 *
 * \{ */

static void transform_apply_to_mirror(TransInfo *t)
{
  FOREACH_TRANS_DATA_CONTAINER (t, tc) {
    if (tc->use_mirror_axis_any) {
      int i;
      TransData *td;
      for (i = 0, td = tc->data; i < tc->data_len; i++, td++) {
        if (td->flag & (TD_MIRROR_EDGE_X | TD_MIRROR_EDGE_Y | TD_MIRROR_EDGE_Z)) {
          if (td->flag & TD_MIRROR_EDGE_X) {
            td->loc[0] = 0.0f;
          }
          if (td->flag & TD_MIRROR_EDGE_Y) {
            td->loc[1] = 0.0f;
          }
          if (td->flag & TD_MIRROR_EDGE_Z) {
            td->loc[2] = 0.0f;
          }
        }
      }

      TransDataMirror *td_mirror = tc->data_mirror;
      for (i = 0; i < tc->data_mirror_len; i++, td_mirror++) {
        copy_v3_v3(td_mirror->loc, td_mirror->loc_src);
        if (td_mirror->flag & TD_MIRROR_X) {
          td_mirror->loc[0] *= -1;
        }
        if (td_mirror->flag & TD_MIRROR_Y) {
          td_mirror->loc[1] *= -1;
        }
        if (td_mirror->flag & TD_MIRROR_Z) {
          td_mirror->loc[2] *= -1;
        }
      }
    }
  }
}

void recalcData_mesh(TransInfo *t)
{
  /* mirror modifier clipping? */
  if (t->state != TRANS_CANCEL) {
    /* apply clipping after so we never project past the clip plane [#25423] */
    applyProject(t);
    clipMirrorModifier(t);

    if ((t->flag & T_NO_MIRROR) == 0 && (t->options & CTX_NO_MIRROR) == 0) {
      transform_apply_to_mirror(t);
    }
  }

  if (ELEM(t->mode, TFM_EDGE_SLIDE, TFM_VERT_SLIDE)) {
    FOREACH_TRANS_DATA_CONTAINER (t, tc) {
      trans_mesh_customdata_correction_apply(tc, false);
    }
  }

  FOREACH_TRANS_DATA_CONTAINER (t, tc) {
    DEG_id_tag_update(tc->obedit->data, 0); /* sets recalc flags */
    BMEditMesh *em = BKE_editmesh_from_object(tc->obedit);
    EDBM_mesh_normals_update(em);
    BKE_editmesh_looptri_calc(em);
  }
}
/** \} */

/* -------------------------------------------------------------------- */
/** \name Special After Transform Mesh
 * \{ */

void special_aftertrans_update__mesh(bContext *UNUSED(C), TransInfo *t)
{
  const bool canceled = (t->state == TRANS_CANCEL);

  if (canceled) {
    /* Exception, edge slide transformed UVs too. */
    if (t->mode == TFM_EDGE_SLIDE) {
      doEdgeSlide(t, 0.0f);
    }
    else if (t->mode == TFM_VERT_SLIDE) {
      doVertSlide(t, 0.0f);
    }
  }

  if (ELEM(t->mode, TFM_EDGE_SLIDE, TFM_VERT_SLIDE)) {
    /* Handle multires re-projection, done
     * on transform completion since it's
     * really slow -joeedh. */
    FOREACH_TRANS_DATA_CONTAINER (t, tc) {
      trans_mesh_customdata_correction_apply(tc, !canceled);
    }
  }

  bool use_automerge = !canceled && (t->flag & (T_AUTOMERGE | T_AUTOSPLIT)) != 0;
  if (use_automerge) {
    FOREACH_TRANS_DATA_CONTAINER (t, tc) {

      BMEditMesh *em = BKE_editmesh_from_object(tc->obedit);
      BMesh *bm = em->bm;
      char hflag;
      bool has_face_sel = (bm->totfacesel != 0);

      if (tc->use_mirror_axis_any) {
        /* Rather then adjusting the selection (which the user would notice)
         * tag all mirrored verts, then auto-merge those. */
        BM_mesh_elem_hflag_disable_all(bm, BM_VERT, BM_ELEM_TAG, false);

        TransDataMirror *td_mirror = tc->data_mirror;
        for (int i = tc->data_mirror_len; i--; td_mirror++) {
          BM_elem_flag_enable((BMVert *)td_mirror->extra, BM_ELEM_TAG);
        }

        hflag = BM_ELEM_SELECT | BM_ELEM_TAG;
      }
      else {
        hflag = BM_ELEM_SELECT;
      }

      if (t->flag & T_AUTOSPLIT) {
        EDBM_automerge_and_split(
            tc->obedit, true, true, true, hflag, t->scene->toolsettings->doublimit);
      }
      else {
        EDBM_automerge(tc->obedit, true, hflag, t->scene->toolsettings->doublimit);
      }

      /* Special case, this is needed or faces won't re-select.
       * Flush selected edges to faces. */
      if (has_face_sel && (em->selectmode == SCE_SELECT_FACE)) {
        EDBM_selectmode_flush_ex(em, SCE_SELECT_EDGE);
      }
    }
  }

  FOREACH_TRANS_DATA_CONTAINER (t, tc) {
    /* table needs to be created for each edit command, since vertices can move etc */
    ED_mesh_mirror_spatial_table_end(tc->obedit);
    /* TODO(campbell): xform: We need support for many mirror objects at once! */
    break;
  }
}
/** \} */

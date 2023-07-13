/* SPDX-FileCopyrightText: 2001-2002 NaN Holding BV. All rights reserved.
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup bke
 *
 * Functions to convert mesh data to and from legacy formats like #MFace.
 */

#define DNA_DEPRECATED_ALLOW

#include "MEM_guardedalloc.h"

#include "DNA_mesh_types.h"
#include "DNA_meshdata_types.h"
#include "DNA_object_types.h"

#include "BLI_edgehash.h"
#include "BLI_math.h"
#include "BLI_math_vector_types.hh"
#include "BLI_memarena.h"
#include "BLI_polyfill_2d.h"
#include "BLI_resource_scope.hh"
#include "BLI_task.hh"
#include "BLI_utildefines.h"

#include "BKE_attribute.hh"
#include "BKE_customdata.h"
#include "BKE_global.h"
#include "BKE_mesh.hh"
#include "BKE_mesh_legacy_convert.h"
#include "BKE_multires.h"

using blender::MutableSpan;
using blender::Span;

/* -------------------------------------------------------------------- */
/** \name Legacy Edge Calculation
 * \{ */

struct EdgeSort {
  uint v1, v2;
  char is_loose, is_draw;
};

/* edges have to be added with lowest index first for sorting */
static void to_edgesort(EdgeSort *ed, uint v1, uint v2, char is_loose, short is_draw)
{
  if (v1 < v2) {
    ed->v1 = v1;
    ed->v2 = v2;
  }
  else {
    ed->v1 = v2;
    ed->v2 = v1;
  }
  ed->is_loose = is_loose;
  ed->is_draw = is_draw;
}

static int vergedgesort(const void *v1, const void *v2)
{
  const EdgeSort *x1 = static_cast<const EdgeSort *>(v1);
  const EdgeSort *x2 = static_cast<const EdgeSort *>(v2);

  if (x1->v1 > x2->v1) {
    return 1;
  }
  if (x1->v1 < x2->v1) {
    return -1;
  }
  if (x1->v2 > x2->v2) {
    return 1;
  }
  if (x1->v2 < x2->v2) {
    return -1;
  }

  return 0;
}

/* Create edges based on known verts and faces,
 * this function is only used when loading very old blend files */
static void mesh_calc_edges_mdata(const MVert * /*allvert*/,
                                  const MFace *allface,
                                  MLoop *allloop,
                                  const MPoly *allpoly,
                                  int /*totvert*/,
                                  int totface,
                                  int /*totloop*/,
                                  int totpoly,
                                  MEdge **r_medge,
                                  int *r_totedge)
{
  const MPoly *mpoly;
  const MFace *mface;
  MEdge *edges, *edge;
  EdgeHash *hash;
  EdgeSort *edsort, *ed;
  int a, totedge = 0;
  uint totedge_final = 0;
  uint edge_index;

  /* we put all edges in array, sort them, and detect doubles that way */

  for (a = totface, mface = allface; a > 0; a--, mface++) {
    if (mface->v4) {
      totedge += 4;
    }
    else if (mface->v3) {
      totedge += 3;
    }
    else {
      totedge += 1;
    }
  }

  if (totedge == 0) {
    /* flag that mesh has edges */
    (*r_medge) = (MEdge *)MEM_callocN(0, __func__);
    (*r_totedge) = 0;
    return;
  }

  ed = edsort = (EdgeSort *)MEM_mallocN(totedge * sizeof(EdgeSort), "EdgeSort");

  for (a = totface, mface = allface; a > 0; a--, mface++) {
    to_edgesort(ed++, mface->v1, mface->v2, !mface->v3, mface->edcode & ME_V1V2);
    if (mface->v4) {
      to_edgesort(ed++, mface->v2, mface->v3, 0, mface->edcode & ME_V2V3);
      to_edgesort(ed++, mface->v3, mface->v4, 0, mface->edcode & ME_V3V4);
      to_edgesort(ed++, mface->v4, mface->v1, 0, mface->edcode & ME_V4V1);
    }
    else if (mface->v3) {
      to_edgesort(ed++, mface->v2, mface->v3, 0, mface->edcode & ME_V2V3);
      to_edgesort(ed++, mface->v3, mface->v1, 0, mface->edcode & ME_V3V1);
    }
  }

  qsort(edsort, totedge, sizeof(EdgeSort), vergedgesort);

  /* count final amount */
  for (a = totedge, ed = edsort; a > 1; a--, ed++) {
    /* edge is unique when it differs from next edge, or is last */
    if (ed->v1 != (ed + 1)->v1 || ed->v2 != (ed + 1)->v2) {
      totedge_final++;
    }
  }
  totedge_final++;

  edges = (MEdge *)MEM_callocN(sizeof(MEdge) * totedge_final, __func__);

  for (a = totedge, edge = edges, ed = edsort; a > 1; a--, ed++) {
    /* edge is unique when it differs from next edge, or is last */
    if (ed->v1 != (ed + 1)->v1 || ed->v2 != (ed + 1)->v2) {
      edge->v1 = ed->v1;
      edge->v2 = ed->v2;

      /* order is swapped so extruding this edge as a surface won't flip face normals
       * with cyclic curves */
      if (ed->v1 + 1 != ed->v2) {
        std::swap(edge->v1, edge->v2);
      }
      edge++;
    }
    else {
      /* Equal edge, merge the draw-flag. */
      (ed + 1)->is_draw |= ed->is_draw;
    }
  }
  /* last edge */
  edge->v1 = ed->v1;
  edge->v2 = ed->v2;

  MEM_freeN(edsort);

  /* set edge members of mloops */
  hash = BLI_edgehash_new_ex(__func__, totedge_final);
  for (edge_index = 0, edge = edges; edge_index < totedge_final; edge_index++, edge++) {
    BLI_edgehash_insert(hash, edge->v1, edge->v2, POINTER_FROM_UINT(edge_index));
  }

  mpoly = allpoly;
  for (a = 0; a < totpoly; a++, mpoly++) {
    MLoop *ml, *ml_next;
    int i = mpoly->totloop;

    ml_next = allloop + mpoly->loopstart; /* first loop */
    ml = &ml_next[i - 1];                 /* last loop */

    while (i-- != 0) {
      ml->e = POINTER_AS_UINT(BLI_edgehash_lookup(hash, ml->v, ml_next->v));
      ml = ml_next;
      ml_next++;
    }
  }

  BLI_edgehash_free(hash, nullptr);

  *r_medge = edges;
  *r_totedge = totedge_final;
}

void BKE_mesh_calc_edges_legacy(Mesh *me)
{
  using namespace blender;
  MEdge *edges;
  int totedge = 0;
  const Span<MVert> verts(static_cast<const MVert *>(CustomData_get_layer(&me->vdata, CD_MVERT)),
                          me->totvert);

  mesh_calc_edges_mdata(
      verts.data(),
      me->mface,
      static_cast<MLoop *>(CustomData_get_layer_for_write(&me->ldata, CD_MLOOP, me->totloop)),
      static_cast<const MPoly *>(CustomData_get_layer(&me->pdata, CD_MPOLY)),
      verts.size(),
      me->totface,
      me->totloop,
      me->totpoly,
      &edges,
      &totedge);

  if (totedge == 0) {
    /* flag that mesh has edges */
    me->totedge = 0;
    return;
  }

  edges = (MEdge *)CustomData_add_layer_with_data(&me->edata, CD_MEDGE, edges, totedge, nullptr);
  me->totedge = totedge;

  BKE_mesh_tag_topology_changed(me);
  BKE_mesh_strip_loose_faces(me);
}

void BKE_mesh_strip_loose_faces(Mesh *me)
{
  /* NOTE: We need to keep this for edge creation (for now?), and some old `readfile.c` code. */
  MFace *f;
  int a, b;
  MFace *mfaces = me->mface;

  for (a = b = 0, f = mfaces; a < me->totface; a++, f++) {
    if (f->v3) {
      if (a != b) {
        memcpy(&mfaces[b], f, sizeof(mfaces[b]));
        CustomData_copy_data(&me->fdata, &me->fdata, a, b, 1);
      }
      b++;
    }
  }
  if (a != b) {
    CustomData_free_elem(&me->fdata, b, a - b);
    me->totface = b;
  }
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name CD Flag Initialization
 * \{ */

void BKE_mesh_do_versions_cd_flag_init(Mesh *mesh)
{
  using namespace blender;
  if (UNLIKELY(mesh->cd_flag)) {
    return;
  }

  const Span<MVert> verts(static_cast<const MVert *>(CustomData_get_layer(&mesh->vdata, CD_MVERT)),
                          mesh->totvert);
  const Span<MEdge> edges(static_cast<const MEdge *>(CustomData_get_layer(&mesh->edata, CD_MEDGE)),
                          mesh->totedge);

  for (const MVert &vert : verts) {
    if (vert.bweight_legacy != 0) {
      mesh->cd_flag |= ME_CDFLAG_VERT_BWEIGHT;
      break;
    }
  }

  for (const MEdge &edge : edges) {
    if (edge.bweight_legacy != 0) {
      mesh->cd_flag |= ME_CDFLAG_EDGE_BWEIGHT;
      if (mesh->cd_flag & ME_CDFLAG_EDGE_CREASE) {
        break;
      }
    }
    if (edge.crease_legacy != 0) {
      mesh->cd_flag |= ME_CDFLAG_EDGE_CREASE;
      if (mesh->cd_flag & ME_CDFLAG_EDGE_BWEIGHT) {
        break;
      }
    }
  }
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name NGon Tessellation (NGon to MFace Conversion)
 * \{ */

#define MESH_MLOOPCOL_FROM_MCOL(_mloopcol, _mcol) \
  { \
    MLoopCol *mloopcol__tmp = _mloopcol; \
    const MCol *mcol__tmp = _mcol; \
    mloopcol__tmp->r = mcol__tmp->b; \
    mloopcol__tmp->g = mcol__tmp->g; \
    mloopcol__tmp->b = mcol__tmp->r; \
    mloopcol__tmp->a = mcol__tmp->a; \
  } \
  (void)0

static void bm_corners_to_loops_ex(ID *id,
                                   CustomData *fdata,
                                   const int totface,
                                   CustomData *ldata,
                                   MFace *mface,
                                   int totloop,
                                   int findex,
                                   int loopstart,
                                   int numTex,
                                   int numCol)
{
  MFace *mf = mface + findex;

  for (int i = 0; i < numTex; i++) {
    const MTFace *texface = (const MTFace *)CustomData_get_n_for_write(
        fdata, CD_MTFACE, findex, i, totface);

    blender::float2 *uv = static_cast<blender::float2 *>(
        CustomData_get_n_for_write(ldata, CD_PROP_FLOAT2, loopstart, i, totloop));
    copy_v2_v2(*uv, texface->uv[0]);
    uv++;
    copy_v2_v2(*uv, texface->uv[1]);
    uv++;
    copy_v2_v2(*uv, texface->uv[2]);
    uv++;

    if (mf->v4) {
      copy_v2_v2(*uv, texface->uv[3]);
      uv++;
    }
  }

  for (int i = 0; i < numCol; i++) {
    MLoopCol *mloopcol = (MLoopCol *)CustomData_get_n_for_write(
        ldata, CD_PROP_BYTE_COLOR, loopstart, i, totloop);
    const MCol *mcol = (const MCol *)CustomData_get_n_for_write(
        fdata, CD_MCOL, findex, i, totface);

    MESH_MLOOPCOL_FROM_MCOL(mloopcol, &mcol[0]);
    mloopcol++;
    MESH_MLOOPCOL_FROM_MCOL(mloopcol, &mcol[1]);
    mloopcol++;
    MESH_MLOOPCOL_FROM_MCOL(mloopcol, &mcol[2]);
    mloopcol++;
    if (mf->v4) {
      MESH_MLOOPCOL_FROM_MCOL(mloopcol, &mcol[3]);
      mloopcol++;
    }
  }

  if (CustomData_has_layer(fdata, CD_TESSLOOPNORMAL)) {
    float(*loop_normals)[3] = (float(*)[3])CustomData_get_for_write(
        ldata, loopstart, CD_NORMAL, totloop);
    const short(*tessloop_normals)[3] = (short(*)[3])CustomData_get_for_write(
        fdata, findex, CD_TESSLOOPNORMAL, totface);
    const int max = mf->v4 ? 4 : 3;

    for (int i = 0; i < max; i++, loop_normals++, tessloop_normals++) {
      normal_short_to_float_v3(*loop_normals, *tessloop_normals);
    }
  }

  if (CustomData_has_layer(fdata, CD_MDISPS)) {
    MDisps *ld = (MDisps *)CustomData_get_for_write(ldata, loopstart, CD_MDISPS, totloop);
    const MDisps *fd = (const MDisps *)CustomData_get_for_write(fdata, findex, CD_MDISPS, totface);
    const float(*disps)[3] = fd->disps;
    int tot = mf->v4 ? 4 : 3;
    int corners;

    if (CustomData_external_test(fdata, CD_MDISPS)) {
      if (id && fdata->external) {
        CustomData_external_add(ldata, id, CD_MDISPS, totloop, fdata->external->filepath);
      }
    }

    corners = multires_mdisp_corners(fd);

    if (corners == 0) {
      /* Empty #MDisp layers appear in at least one of the `sintel.blend` files.
       * Not sure why this happens, but it seems fine to just ignore them here.
       * If `corners == 0` for a non-empty layer though, something went wrong. */
      BLI_assert(fd->totdisp == 0);
    }
    else {
      const int side = int(sqrtf(float(fd->totdisp / corners)));
      const int side_sq = side * side;

      for (int i = 0; i < tot; i++, disps += side_sq, ld++) {
        ld->totdisp = side_sq;
        ld->level = int(logf(float(side) - 1.0f) / float(M_LN2)) + 1;

        if (ld->disps) {
          MEM_freeN(ld->disps);
        }

        ld->disps = (float(*)[3])MEM_malloc_arrayN(
            size_t(side_sq), sizeof(float[3]), "converted loop mdisps");
        if (fd->disps) {
          memcpy(ld->disps, disps, size_t(side_sq) * sizeof(float[3]));
        }
        else {
          memset(ld->disps, 0, size_t(side_sq) * sizeof(float[3]));
        }
      }
    }
  }
}

static void CustomData_to_bmeshpoly(CustomData *fdata, CustomData *ldata, int totloop)
{
  for (int i = 0; i < fdata->totlayer; i++) {
    if (fdata->layers[i].type == CD_MTFACE) {
      CustomData_add_layer_named(
          ldata, CD_PROP_FLOAT2, CD_SET_DEFAULT, totloop, fdata->layers[i].name);
    }
    else if (fdata->layers[i].type == CD_MCOL) {
      CustomData_add_layer_named(
          ldata, CD_PROP_BYTE_COLOR, CD_SET_DEFAULT, totloop, fdata->layers[i].name);
    }
    else if (fdata->layers[i].type == CD_MDISPS) {
      CustomData_add_layer_named(ldata, CD_MDISPS, CD_SET_DEFAULT, totloop, fdata->layers[i].name);
    }
    else if (fdata->layers[i].type == CD_TESSLOOPNORMAL) {
      CustomData_add_layer_named(ldata, CD_NORMAL, CD_SET_DEFAULT, totloop, fdata->layers[i].name);
    }
  }
}

static void convert_mfaces_to_mpolys(ID *id,
                                     CustomData *fdata,
                                     CustomData *ldata,
                                     CustomData *pdata,
                                     int totedge_i,
                                     int totface_i,
                                     int totloop_i,
                                     int totpoly_i,
                                     blender::int2 *edges,
                                     MFace *mface,
                                     int *r_totloop,
                                     int *r_totpoly)
{
  MFace *mf;
  MLoop *ml, *mloop;
  MPoly *poly, *mpoly;
  EdgeHash *eh;
  int numTex, numCol;
  int i, j, totloop, totpoly, *polyindex;

  /* just in case some of these layers are filled in (can happen with python created meshes) */
  CustomData_free(ldata, totloop_i);
  CustomData_free(pdata, totpoly_i);

  totpoly = totface_i;
  mpoly = (MPoly *)CustomData_add_layer(pdata, CD_MPOLY, CD_SET_DEFAULT, totpoly);
  int *material_indices = static_cast<int *>(
      CustomData_get_layer_named_for_write(pdata, CD_PROP_INT32, "material_index", totpoly));
  if (material_indices == nullptr) {
    material_indices = static_cast<int *>(CustomData_add_layer_named(
        pdata, CD_PROP_INT32, CD_SET_DEFAULT, totpoly, "material_index"));
  }
  bool *sharp_faces = static_cast<bool *>(
      CustomData_get_layer_named_for_write(pdata, CD_PROP_BOOL, "sharp_face", totpoly));
  if (!sharp_faces) {
    sharp_faces = static_cast<bool *>(
        CustomData_add_layer_named(pdata, CD_PROP_BOOL, CD_SET_DEFAULT, totpoly, "sharp_face"));
  }

  numTex = CustomData_number_of_layers(fdata, CD_MTFACE);
  numCol = CustomData_number_of_layers(fdata, CD_MCOL);

  totloop = 0;
  mf = mface;
  for (i = 0; i < totface_i; i++, mf++) {
    totloop += mf->v4 ? 4 : 3;
  }

  mloop = (MLoop *)CustomData_add_layer(ldata, CD_MLOOP, CD_SET_DEFAULT, totloop);

  CustomData_to_bmeshpoly(fdata, ldata, totloop);

  if (id) {
    /* ensure external data is transferred */
    /* TODO(sergey): Use multiresModifier_ensure_external_read(). */
    CustomData_external_read(fdata, id, CD_MASK_MDISPS, totface_i);
  }

  eh = BLI_edgehash_new_ex(__func__, uint(totedge_i));

  /* build edge hash */
  for (i = 0; i < totedge_i; i++) {
    BLI_edgehash_insert(eh, edges[i][0], edges[i][1], POINTER_FROM_UINT(i));
  }

  polyindex = (int *)CustomData_get_layer(fdata, CD_ORIGINDEX);

  j = 0; /* current loop index */
  ml = mloop;
  mf = mface;
  poly = mpoly;
  for (i = 0; i < totface_i; i++, mf++, poly++) {
    poly->loopstart = j;

    poly->totloop = mf->v4 ? 4 : 3;

    material_indices[i] = mf->mat_nr;
    sharp_faces[i] = (mf->flag & ME_SMOOTH) == 0;

#define ML(v1, v2) \
  { \
    ml->v = mf->v1; \
    ml->e = POINTER_AS_UINT(BLI_edgehash_lookup(eh, mf->v1, mf->v2)); \
    ml++; \
    j++; \
  } \
  (void)0

    ML(v1, v2);
    ML(v2, v3);
    if (mf->v4) {
      ML(v3, v4);
      ML(v4, v1);
    }
    else {
      ML(v3, v1);
    }

#undef ML

    bm_corners_to_loops_ex(
        id, fdata, totface_i, ldata, mface, totloop, i, poly->loopstart, numTex, numCol);

    if (polyindex) {
      *polyindex = i;
      polyindex++;
    }
  }

  /* NOTE: we don't convert NGons at all, these are not even real ngons,
   * they have their own UVs, colors etc - it's more an editing feature. */

  BLI_edgehash_free(eh, nullptr);

  *r_totpoly = totpoly;
  *r_totloop = totloop;
}

static void update_active_fdata_layers(Mesh &mesh, CustomData *fdata, CustomData *ldata)
{
  int act;

  if (CustomData_has_layer(ldata, CD_PROP_FLOAT2)) {
    act = CustomData_get_active_layer(ldata, CD_PROP_FLOAT2);
    CustomData_set_layer_active(fdata, CD_MTFACE, act);

    act = CustomData_get_render_layer(ldata, CD_PROP_FLOAT2);
    CustomData_set_layer_render(fdata, CD_MTFACE, act);

    act = CustomData_get_clone_layer(ldata, CD_PROP_FLOAT2);
    CustomData_set_layer_clone(fdata, CD_MTFACE, act);

    act = CustomData_get_stencil_layer(ldata, CD_PROP_FLOAT2);
    CustomData_set_layer_stencil(fdata, CD_MTFACE, act);
  }

  if (CustomData_has_layer(ldata, CD_PROP_BYTE_COLOR)) {
    if (mesh.active_color_attribute != nullptr) {
      act = CustomData_get_named_layer(ldata, CD_PROP_BYTE_COLOR, mesh.active_color_attribute);
      CustomData_set_layer_active(fdata, CD_MCOL, act);
    }

    if (mesh.default_color_attribute != nullptr) {
      act = CustomData_get_named_layer(ldata, CD_PROP_BYTE_COLOR, mesh.default_color_attribute);
      CustomData_set_layer_render(fdata, CD_MCOL, act);
    }

    act = CustomData_get_clone_layer(ldata, CD_PROP_BYTE_COLOR);
    CustomData_set_layer_clone(fdata, CD_MCOL, act);

    act = CustomData_get_stencil_layer(ldata, CD_PROP_BYTE_COLOR);
    CustomData_set_layer_stencil(fdata, CD_MCOL, act);
  }
}

#ifndef NDEBUG
/**
 * Debug check, used to assert when we expect layers to be in/out of sync.
 *
 * \param fallback: Use when there are no layers to handle,
 * since callers may expect success or failure.
 */
static bool check_matching_legacy_layer_counts(CustomData *fdata, CustomData *ldata, bool fallback)
{
  int a_num = 0, b_num = 0;
#  define LAYER_CMP(l_a, t_a, l_b, t_b) \
    ((a_num += CustomData_number_of_layers(l_a, t_a)) == \
     (b_num += CustomData_number_of_layers(l_b, t_b)))

  if (!LAYER_CMP(ldata, CD_PROP_FLOAT2, fdata, CD_MTFACE)) {
    return false;
  }
  if (!LAYER_CMP(ldata, CD_PROP_BYTE_COLOR, fdata, CD_MCOL)) {
    return false;
  }
  if (!LAYER_CMP(ldata, CD_PREVIEW_MLOOPCOL, fdata, CD_PREVIEW_MCOL)) {
    return false;
  }
  if (!LAYER_CMP(ldata, CD_ORIGSPACE_MLOOP, fdata, CD_ORIGSPACE)) {
    return false;
  }
  if (!LAYER_CMP(ldata, CD_NORMAL, fdata, CD_TESSLOOPNORMAL)) {
    return false;
  }
  if (!LAYER_CMP(ldata, CD_TANGENT, fdata, CD_TANGENT)) {
    return false;
  }

#  undef LAYER_CMP

  /* if no layers are on either CustomData's,
   * then there was nothing to do... */
  return a_num ? true : fallback;
}
#endif

static void add_mface_layers(Mesh &mesh, CustomData *fdata, CustomData *ldata, int total)
{
  /* avoid accumulating extra layers */
  BLI_assert(!check_matching_legacy_layer_counts(fdata, ldata, false));

  for (int i = 0; i < ldata->totlayer; i++) {
    if (ldata->layers[i].type == CD_PROP_FLOAT2) {
      CustomData_add_layer_named(fdata, CD_MTFACE, CD_SET_DEFAULT, total, ldata->layers[i].name);
    }
    if (ldata->layers[i].type == CD_PROP_BYTE_COLOR) {
      CustomData_add_layer_named(fdata, CD_MCOL, CD_SET_DEFAULT, total, ldata->layers[i].name);
    }
    else if (ldata->layers[i].type == CD_PREVIEW_MLOOPCOL) {
      CustomData_add_layer_named(
          fdata, CD_PREVIEW_MCOL, CD_SET_DEFAULT, total, ldata->layers[i].name);
    }
    else if (ldata->layers[i].type == CD_ORIGSPACE_MLOOP) {
      CustomData_add_layer_named(
          fdata, CD_ORIGSPACE, CD_SET_DEFAULT, total, ldata->layers[i].name);
    }
    else if (ldata->layers[i].type == CD_NORMAL) {
      CustomData_add_layer_named(
          fdata, CD_TESSLOOPNORMAL, CD_SET_DEFAULT, total, ldata->layers[i].name);
    }
    else if (ldata->layers[i].type == CD_TANGENT) {
      CustomData_add_layer_named(fdata, CD_TANGENT, CD_SET_DEFAULT, total, ldata->layers[i].name);
    }
  }

  update_active_fdata_layers(mesh, fdata, ldata);
}

static void mesh_ensure_tessellation_customdata(Mesh *me)
{
  if (UNLIKELY((me->totface != 0) && (me->totpoly == 0))) {
    /* Pass, otherwise this function  clears 'mface' before
     * versioning 'mface -> mpoly' code kicks in #30583.
     *
     * Callers could also check but safer to do here - campbell */
  }
  else {
    const int tottex_original = CustomData_number_of_layers(&me->ldata, CD_PROP_FLOAT2);
    const int totcol_original = CustomData_number_of_layers(&me->ldata, CD_PROP_BYTE_COLOR);

    const int tottex_tessface = CustomData_number_of_layers(&me->fdata, CD_MTFACE);
    const int totcol_tessface = CustomData_number_of_layers(&me->fdata, CD_MCOL);

    if (tottex_tessface != tottex_original || totcol_tessface != totcol_original) {
      BKE_mesh_tessface_clear(me);

      add_mface_layers(*me, &me->fdata, &me->ldata, me->totface);

      /* TODO: add some `--debug-mesh` option. */
      if (G.debug & G_DEBUG) {
        /* NOTE(campbell): this warning may be un-called for if we are initializing the mesh for
         * the first time from #BMesh, rather than giving a warning about this we could be smarter
         * and check if there was any data to begin with, for now just print the warning with
         * some info to help troubleshoot what's going on. */
        printf(
            "%s: warning! Tessellation uvs or vcol data got out of sync, "
            "had to reset!\n    CD_MTFACE: %d != CD_PROP_FLOAT2: %d || CD_MCOL: %d != "
            "CD_PROP_BYTE_COLOR: "
            "%d\n",
            __func__,
            tottex_tessface,
            tottex_original,
            totcol_tessface,
            totcol_original);
      }
    }
  }
}

void BKE_mesh_convert_mfaces_to_mpolys(Mesh *mesh)
{
  convert_mfaces_to_mpolys(&mesh->id,
                           &mesh->fdata,
                           &mesh->ldata,
                           &mesh->pdata,
                           mesh->totedge,
                           mesh->totface,
                           mesh->totloop,
                           mesh->totpoly,
                           mesh->edges_for_write().data(),
                           (MFace *)CustomData_get_layer(&mesh->fdata, CD_MFACE),
                           &mesh->totloop,
                           &mesh->totpoly);
  BKE_mesh_legacy_convert_loops_to_corners(mesh);
  BKE_mesh_legacy_convert_polys_to_offsets(mesh);

  mesh_ensure_tessellation_customdata(mesh);
}

/**
 * Update active indices for active/render/clone/stencil custom data layers
 * based on indices from fdata layers
 * used when creating pdata and ldata for pre-bmesh
 * meshes and needed to preserve active/render/clone/stencil flags set in pre-bmesh files.
 */
static void CustomData_bmesh_do_versions_update_active_layers(CustomData *fdata, CustomData *ldata)
{
  int act;

  if (CustomData_has_layer(fdata, CD_MTFACE)) {
    act = CustomData_get_active_layer(fdata, CD_MTFACE);
    CustomData_set_layer_active(ldata, CD_PROP_FLOAT2, act);

    act = CustomData_get_render_layer(fdata, CD_MTFACE);
    CustomData_set_layer_render(ldata, CD_PROP_FLOAT2, act);

    act = CustomData_get_clone_layer(fdata, CD_MTFACE);
    CustomData_set_layer_clone(ldata, CD_PROP_FLOAT2, act);

    act = CustomData_get_stencil_layer(fdata, CD_MTFACE);
    CustomData_set_layer_stencil(ldata, CD_PROP_FLOAT2, act);
  }

  if (CustomData_has_layer(fdata, CD_MCOL)) {
    act = CustomData_get_active_layer(fdata, CD_MCOL);
    CustomData_set_layer_active(ldata, CD_PROP_BYTE_COLOR, act);

    act = CustomData_get_render_layer(fdata, CD_MCOL);
    CustomData_set_layer_render(ldata, CD_PROP_BYTE_COLOR, act);

    act = CustomData_get_clone_layer(fdata, CD_MCOL);
    CustomData_set_layer_clone(ldata, CD_PROP_BYTE_COLOR, act);

    act = CustomData_get_stencil_layer(fdata, CD_MCOL);
    CustomData_set_layer_stencil(ldata, CD_PROP_BYTE_COLOR, act);
  }
}

void BKE_mesh_do_versions_convert_mfaces_to_mpolys(Mesh *mesh)
{
  convert_mfaces_to_mpolys(&mesh->id,
                           &mesh->fdata,
                           &mesh->ldata,
                           &mesh->pdata,
                           mesh->totedge,
                           mesh->totface,
                           mesh->totloop,
                           mesh->totpoly,
                           mesh->edges_for_write().data(),
                           (MFace *)CustomData_get_layer(&mesh->fdata, CD_MFACE),
                           &mesh->totloop,
                           &mesh->totpoly);
  BKE_mesh_legacy_convert_loops_to_corners(mesh);
  BKE_mesh_legacy_convert_polys_to_offsets(mesh);

  CustomData_bmesh_do_versions_update_active_layers(&mesh->fdata, &mesh->ldata);

  mesh_ensure_tessellation_customdata(mesh);
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name MFace Tessellation
 *
 * #MFace is a legacy data-structure that should be avoided, use #MLoopTri instead.
 * \{ */

#define MESH_MLOOPCOL_TO_MCOL(_mloopcol, _mcol) \
  { \
    const MLoopCol *mloopcol__tmp = _mloopcol; \
    MCol *mcol__tmp = _mcol; \
    mcol__tmp->b = mloopcol__tmp->r; \
    mcol__tmp->g = mloopcol__tmp->g; \
    mcol__tmp->r = mloopcol__tmp->b; \
    mcol__tmp->a = mloopcol__tmp->a; \
  } \
  (void)0

/**
 * Convert all CD layers from loop/poly to tessface data.
 *
 * \param loopindices: is an array of an int[4] per tessface,
 * mapping tessface's verts to loops indices.
 *
 * \note when mface is not null, mface[face_index].v4
 * is used to test quads, else, loopindices[face_index][3] is used.
 */
static void mesh_loops_to_tessdata(CustomData *fdata,
                                   CustomData *ldata,
                                   MFace *mface,
                                   const int *polyindices,
                                   uint (*loopindices)[4],
                                   const int num_faces)
{
  /* NOTE(mont29): performances are sub-optimal when we get a null #MFace,
   * we could be ~25% quicker with dedicated code.
   * The issue is, unless having two different functions with nearly the same code,
   * there's not much ways to solve this. Better IMHO to live with it for now (sigh). */
  const int numUV = CustomData_number_of_layers(ldata, CD_PROP_FLOAT2);
  const int numCol = CustomData_number_of_layers(ldata, CD_PROP_BYTE_COLOR);
  const bool hasPCol = CustomData_has_layer(ldata, CD_PREVIEW_MLOOPCOL);
  const bool hasOrigSpace = CustomData_has_layer(ldata, CD_ORIGSPACE_MLOOP);
  const bool hasLoopNormal = CustomData_has_layer(ldata, CD_NORMAL);
  const bool hasLoopTangent = CustomData_has_layer(ldata, CD_TANGENT);
  int findex, i, j;
  const int *pidx;
  uint(*lidx)[4];

  for (i = 0; i < numUV; i++) {
    MTFace *texface = (MTFace *)CustomData_get_layer_n_for_write(fdata, CD_MTFACE, i, num_faces);
    const blender::float2 *uv = static_cast<const blender::float2 *>(
        CustomData_get_layer_n(ldata, CD_PROP_FLOAT2, i));

    for (findex = 0, pidx = polyindices, lidx = loopindices; findex < num_faces;
         pidx++, lidx++, findex++, texface++)
    {
      for (j = (mface ? mface[findex].v4 : (*lidx)[3]) ? 4 : 3; j--;) {
        copy_v2_v2(texface->uv[j], uv[(*lidx)[j]]);
      }
    }
  }

  for (i = 0; i < numCol; i++) {
    MCol(*mcol)[4] = (MCol(*)[4])CustomData_get_layer_n_for_write(fdata, CD_MCOL, i, num_faces);
    const MLoopCol *mloopcol = (const MLoopCol *)CustomData_get_layer_n(
        ldata, CD_PROP_BYTE_COLOR, i);

    for (findex = 0, lidx = loopindices; findex < num_faces; lidx++, findex++, mcol++) {
      for (j = (mface ? mface[findex].v4 : (*lidx)[3]) ? 4 : 3; j--;) {
        MESH_MLOOPCOL_TO_MCOL(&mloopcol[(*lidx)[j]], &(*mcol)[j]);
      }
    }
  }

  if (hasPCol) {
    MCol(*mcol)[4] = (MCol(*)[4])CustomData_get_layer(fdata, CD_PREVIEW_MCOL);
    const MLoopCol *mloopcol = (const MLoopCol *)CustomData_get_layer(ldata, CD_PREVIEW_MLOOPCOL);

    for (findex = 0, lidx = loopindices; findex < num_faces; lidx++, findex++, mcol++) {
      for (j = (mface ? mface[findex].v4 : (*lidx)[3]) ? 4 : 3; j--;) {
        MESH_MLOOPCOL_TO_MCOL(&mloopcol[(*lidx)[j]], &(*mcol)[j]);
      }
    }
  }

  if (hasOrigSpace) {
    OrigSpaceFace *of = (OrigSpaceFace *)CustomData_get_layer(fdata, CD_ORIGSPACE);
    const OrigSpaceLoop *lof = (const OrigSpaceLoop *)CustomData_get_layer(ldata,
                                                                           CD_ORIGSPACE_MLOOP);

    for (findex = 0, lidx = loopindices; findex < num_faces; lidx++, findex++, of++) {
      for (j = (mface ? mface[findex].v4 : (*lidx)[3]) ? 4 : 3; j--;) {
        copy_v2_v2(of->uv[j], lof[(*lidx)[j]].uv);
      }
    }
  }

  if (hasLoopNormal) {
    short(*face_normals)[4][3] = (short(*)[4][3])CustomData_get_layer(fdata, CD_TESSLOOPNORMAL);
    const float(*loop_normals)[3] = (const float(*)[3])CustomData_get_layer(ldata, CD_NORMAL);

    for (findex = 0, lidx = loopindices; findex < num_faces; lidx++, findex++, face_normals++) {
      for (j = (mface ? mface[findex].v4 : (*lidx)[3]) ? 4 : 3; j--;) {
        normal_float_to_short_v3((*face_normals)[j], loop_normals[(*lidx)[j]]);
      }
    }
  }

  if (hasLoopTangent) {
    /* Need to do for all UV maps at some point. */
    float(*ftangents)[4] = (float(*)[4])CustomData_get_layer(fdata, CD_TANGENT);
    const float(*ltangents)[4] = (const float(*)[4])CustomData_get_layer(ldata, CD_TANGENT);

    for (findex = 0, pidx = polyindices, lidx = loopindices; findex < num_faces;
         pidx++, lidx++, findex++)
    {
      int nverts = (mface ? mface[findex].v4 : (*lidx)[3]) ? 4 : 3;
      for (j = nverts; j--;) {
        copy_v4_v4(ftangents[findex * 4 + j], ltangents[(*lidx)[j]]);
      }
    }
  }
}

int BKE_mesh_mface_index_validate(MFace *mface, CustomData *fdata, int mfindex, int nr)
{
  /* first test if the face is legal */
  if ((mface->v3 || nr == 4) && mface->v3 == mface->v4) {
    mface->v4 = 0;
    nr--;
  }
  if ((mface->v2 || mface->v4) && mface->v2 == mface->v3) {
    mface->v3 = mface->v4;
    mface->v4 = 0;
    nr--;
  }
  if (mface->v1 == mface->v2) {
    mface->v2 = mface->v3;
    mface->v3 = mface->v4;
    mface->v4 = 0;
    nr--;
  }

  /* Check corrupt cases, bow-tie geometry,
   * can't handle these because edge data won't exist so just return 0. */
  if (nr == 3) {
    if (
        /* real edges */
        mface->v1 == mface->v2 || mface->v2 == mface->v3 || mface->v3 == mface->v1)
    {
      return 0;
    }
  }
  else if (nr == 4) {
    if (
        /* real edges */
        mface->v1 == mface->v2 || mface->v2 == mface->v3 || mface->v3 == mface->v4 ||
        mface->v4 == mface->v1 ||
        /* across the face */
        mface->v1 == mface->v3 || mface->v2 == mface->v4)
    {
      return 0;
    }
  }

  /* prevent a zero at wrong index location */
  if (nr == 3) {
    if (mface->v3 == 0) {
      static int corner_indices[4] = {1, 2, 0, 3};

      std::swap(mface->v1, mface->v2);
      std::swap(mface->v2, mface->v3);

      if (fdata) {
        CustomData_swap_corners(fdata, mfindex, corner_indices);
      }
    }
  }
  else if (nr == 4) {
    if (mface->v3 == 0 || mface->v4 == 0) {
      static int corner_indices[4] = {2, 3, 0, 1};

      std::swap(mface->v1, mface->v3);
      std::swap(mface->v2, mface->v4);

      if (fdata) {
        CustomData_swap_corners(fdata, mfindex, corner_indices);
      }
    }
  }

  return nr;
}

static int mesh_tessface_calc(Mesh &mesh,
                              CustomData *fdata,
                              CustomData *ldata,
                              CustomData *pdata,
                              float (*positions)[3],
                              int totface,
                              int totloop,
                              int totpoly)
{
#define USE_TESSFACE_SPEEDUP
#define USE_TESSFACE_QUADS

/* We abuse #MFace.edcode to tag quad faces. See below for details. */
#define TESSFACE_IS_QUAD 1

  const int looptri_num = poly_to_tri_count(totpoly, totloop);

  MFace *mface, *mf;
  MemArena *arena = nullptr;
  int *mface_to_poly_map;
  uint(*lindices)[4];
  int poly_index, mface_index;
  uint j;

  const blender::OffsetIndices polys = mesh.polys();
  const Span<int> corner_verts = mesh.corner_verts();
  const int *material_indices = static_cast<const int *>(
      CustomData_get_layer_named(pdata, CD_PROP_INT32, "material_index"));
  const bool *sharp_faces = static_cast<const bool *>(
      CustomData_get_layer_named(pdata, CD_PROP_BOOL, "sharp_face"));

  /* Allocate the length of `totfaces`, avoid many small reallocation's,
   * if all faces are triangles it will be correct, `quads == 2x` allocations. */
  /* Take care since memory is _not_ zeroed so be sure to initialize each field. */
  mface_to_poly_map = (int *)MEM_malloc_arrayN(
      size_t(looptri_num), sizeof(*mface_to_poly_map), __func__);
  mface = (MFace *)MEM_malloc_arrayN(size_t(looptri_num), sizeof(*mface), __func__);
  lindices = (uint(*)[4])MEM_malloc_arrayN(size_t(looptri_num), sizeof(*lindices), __func__);

  mface_index = 0;
  for (poly_index = 0; poly_index < totpoly; poly_index++) {
    const uint mp_loopstart = uint(polys[poly_index].start());
    const uint mp_totloop = uint(polys[poly_index].size());
    uint l1, l2, l3, l4;
    uint *lidx;
    if (mp_totloop < 3) {
      /* Do nothing. */
    }

#ifdef USE_TESSFACE_SPEEDUP

#  define ML_TO_MF(i1, i2, i3) \
    mface_to_poly_map[mface_index] = poly_index; \
    mf = &mface[mface_index]; \
    lidx = lindices[mface_index]; \
    /* Set loop indices, transformed to vert indices later. */ \
    l1 = mp_loopstart + i1; \
    l2 = mp_loopstart + i2; \
    l3 = mp_loopstart + i3; \
    mf->v1 = corner_verts[l1]; \
    mf->v2 = corner_verts[l2]; \
    mf->v3 = corner_verts[l3]; \
    mf->v4 = 0; \
    lidx[0] = l1; \
    lidx[1] = l2; \
    lidx[2] = l3; \
    lidx[3] = 0; \
    mf->mat_nr = material_indices ? material_indices[poly_index] : 0; \
    mf->flag = (sharp_faces && sharp_faces[poly_index]) ? 0 : ME_SMOOTH; \
    mf->edcode = 0; \
    (void)0

/* ALMOST IDENTICAL TO DEFINE ABOVE (see EXCEPTION) */
#  define ML_TO_MF_QUAD() \
    mface_to_poly_map[mface_index] = poly_index; \
    mf = &mface[mface_index]; \
    lidx = lindices[mface_index]; \
    /* Set loop indices, transformed to vert indices later. */ \
    l1 = mp_loopstart + 0; /* EXCEPTION */ \
    l2 = mp_loopstart + 1; /* EXCEPTION */ \
    l3 = mp_loopstart + 2; /* EXCEPTION */ \
    l4 = mp_loopstart + 3; /* EXCEPTION */ \
    mf->v1 = corner_verts[l1]; \
    mf->v2 = corner_verts[l2]; \
    mf->v3 = corner_verts[l3]; \
    mf->v4 = corner_verts[l4]; \
    lidx[0] = l1; \
    lidx[1] = l2; \
    lidx[2] = l3; \
    lidx[3] = l4; \
    mf->mat_nr = material_indices ? material_indices[poly_index] : 0; \
    mf->flag = (sharp_faces && sharp_faces[poly_index]) ? 0 : ME_SMOOTH; \
    mf->edcode = TESSFACE_IS_QUAD; \
    (void)0

    else if (mp_totloop == 3) {
      ML_TO_MF(0, 1, 2);
      mface_index++;
    }
    else if (mp_totloop == 4) {
#  ifdef USE_TESSFACE_QUADS
      ML_TO_MF_QUAD();
      mface_index++;
#  else
      ML_TO_MF(0, 1, 2);
      mface_index++;
      ML_TO_MF(0, 2, 3);
      mface_index++;
#  endif
    }
#endif /* USE_TESSFACE_SPEEDUP */
    else {
      const float *co_curr, *co_prev;

      float normal[3];

      float axis_mat[3][3];
      float(*projverts)[2];
      uint(*tris)[3];

      const uint totfilltri = mp_totloop - 2;

      if (UNLIKELY(arena == nullptr)) {
        arena = BLI_memarena_new(BLI_MEMARENA_STD_BUFSIZE, __func__);
      }

      tris = (uint(*)[3])BLI_memarena_alloc(arena, sizeof(*tris) * size_t(totfilltri));
      projverts = (float(*)[2])BLI_memarena_alloc(arena, sizeof(*projverts) * size_t(mp_totloop));

      zero_v3(normal);

      /* Calculate the normal, flipped: to get a positive 2D cross product. */
      co_prev = positions[corner_verts[mp_loopstart + mp_totloop - 1]];
      for (j = 0; j < mp_totloop; j++) {
        const int vert = corner_verts[mp_loopstart + j];
        co_curr = positions[vert];
        add_newell_cross_v3_v3v3(normal, co_prev, co_curr);
        co_prev = co_curr;
      }
      if (UNLIKELY(normalize_v3(normal) == 0.0f)) {
        normal[2] = 1.0f;
      }

      /* Project verts to 2D. */
      axis_dominant_v3_to_m3_negate(axis_mat, normal);

      for (j = 0; j < mp_totloop; j++) {
        const int vert = corner_verts[mp_loopstart + j];
        mul_v2_m3v3(projverts[j], axis_mat, positions[vert]);
      }

      BLI_polyfill_calc_arena(projverts, mp_totloop, 1, tris, arena);

      /* Apply fill. */
      for (j = 0; j < totfilltri; j++) {
        uint *tri = tris[j];
        lidx = lindices[mface_index];

        mface_to_poly_map[mface_index] = poly_index;
        mf = &mface[mface_index];

        /* Set loop indices, transformed to vert indices later. */
        l1 = mp_loopstart + tri[0];
        l2 = mp_loopstart + tri[1];
        l3 = mp_loopstart + tri[2];

        mf->v1 = corner_verts[l1];
        mf->v2 = corner_verts[l2];
        mf->v3 = corner_verts[l3];
        mf->v4 = 0;

        lidx[0] = l1;
        lidx[1] = l2;
        lidx[2] = l3;
        lidx[3] = 0;

        mf->mat_nr = material_indices ? material_indices[poly_index] : 0;
        mf->edcode = 0;

        mface_index++;
      }

      BLI_memarena_clear(arena);
    }
  }

  if (arena) {
    BLI_memarena_free(arena);
    arena = nullptr;
  }

  CustomData_free(fdata, totface);
  totface = mface_index;

  BLI_assert(totface <= looptri_num);

  /* Not essential but without this we store over-allocated memory in the #CustomData layers. */
  if (LIKELY(looptri_num != totface)) {
    mface = (MFace *)MEM_reallocN(mface, sizeof(*mface) * size_t(totface));
    mface_to_poly_map = (int *)MEM_reallocN(mface_to_poly_map,
                                            sizeof(*mface_to_poly_map) * size_t(totface));
  }

  CustomData_add_layer_with_data(fdata, CD_MFACE, mface, totface, nullptr);

  /* #CD_ORIGINDEX will contain an array of indices from tessellation-faces to the polygons
   * they are directly tessellated from. */
  CustomData_add_layer_with_data(fdata, CD_ORIGINDEX, mface_to_poly_map, totface, nullptr);
  add_mface_layers(mesh, fdata, ldata, totface);

  /* NOTE: quad detection issue - fourth vertex-index vs fourth loop-index:
   * Polygons take care of their loops ordering, hence not of their vertices ordering.
   * Currently, the #TFace fourth vertex index might be 0 even for a quad.
   * However, we know our fourth loop index is never 0 for quads
   * (because they are sorted for polygons, and our quads are still mere copies of their polygons).
   * So we pass nullptr as #MFace pointer, and #mesh_loops_to_tessdata
   * will use the fourth loop index as quad test. */
  mesh_loops_to_tessdata(fdata, ldata, nullptr, mface_to_poly_map, lindices, totface);

  /* NOTE: quad detection issue - fourth vert-index vs fourth loop-index:
   * ...However, most #TFace code uses `MFace->v4 == 0` test to check whether it is a tri or quad.
   * BKE_mesh_mface_index_validate() will check this and rotate the tessellated face if needed.
   */
#ifdef USE_TESSFACE_QUADS
  mf = mface;
  for (mface_index = 0; mface_index < totface; mface_index++, mf++) {
    if (mf->edcode == TESSFACE_IS_QUAD) {
      BKE_mesh_mface_index_validate(mf, fdata, mface_index, 4);
      mf->edcode = 0;
    }
  }
#endif

  MEM_freeN(lindices);

  return totface;

#undef USE_TESSFACE_SPEEDUP
#undef USE_TESSFACE_QUADS

#undef ML_TO_MF
#undef ML_TO_MF_QUAD
}

void BKE_mesh_tessface_calc(Mesh *mesh)
{
  mesh->totface = mesh_tessface_calc(
      *mesh,
      &mesh->fdata,
      &mesh->ldata,
      &mesh->pdata,
      reinterpret_cast<float(*)[3]>(mesh->vert_positions_for_write().data()),
      mesh->totface,
      mesh->totloop,
      mesh->totpoly);

  mesh_ensure_tessellation_customdata(mesh);
}

void BKE_mesh_tessface_ensure(Mesh *mesh)
{
  if (mesh->totpoly && mesh->totface == 0) {
    BKE_mesh_tessface_calc(mesh);
  }
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Sharp Edge Conversion
 * \{ */

void BKE_mesh_legacy_sharp_faces_from_flags(Mesh *mesh)
{
  using namespace blender;
  using namespace blender::bke;
  MutableAttributeAccessor attributes = mesh->attributes_for_write();
  if (attributes.contains("sharp_face") || !CustomData_get_layer(&mesh->pdata, CD_MPOLY)) {
    return;
  }
  const Span<MPoly> polys(static_cast<const MPoly *>(CustomData_get_layer(&mesh->pdata, CD_MPOLY)),
                          mesh->totpoly);
  if (std::any_of(polys.begin(), polys.end(), [](const MPoly &poly) {
        return !(poly.flag_legacy & ME_SMOOTH);
      }))
  {
    SpanAttributeWriter<bool> sharp_faces = attributes.lookup_or_add_for_write_only_span<bool>(
        "sharp_face", ATTR_DOMAIN_FACE);
    threading::parallel_for(polys.index_range(), 4096, [&](const IndexRange range) {
      for (const int i : range) {
        sharp_faces.span[i] = !(polys[i].flag_legacy & ME_SMOOTH);
      }
    });
    sharp_faces.finish();
  }
  else {
    attributes.remove("sharp_face");
  }
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Face Set Conversion
 * \{ */

void BKE_mesh_legacy_face_set_to_generic(Mesh *mesh)
{
  using namespace blender;
  if (mesh->attributes().contains(".sculpt_face_set")) {
    return;
  }
  void *faceset_data = nullptr;
  const ImplicitSharingInfo *faceset_sharing_info = nullptr;
  for (const int i : IndexRange(mesh->pdata.totlayer)) {
    CustomDataLayer &layer = mesh->pdata.layers[i];
    if (layer.type == CD_SCULPT_FACE_SETS) {
      faceset_data = layer.data;
      faceset_sharing_info = layer.sharing_info;
      layer.data = nullptr;
      layer.sharing_info = nullptr;
      CustomData_free_layer(&mesh->pdata, CD_SCULPT_FACE_SETS, mesh->totpoly, i);
      break;
    }
  }
  if (faceset_data != nullptr) {
    CustomData_add_layer_named_with_data(&mesh->pdata,
                                         CD_PROP_INT32,
                                         faceset_data,
                                         mesh->totpoly,
                                         ".sculpt_face_set",
                                         faceset_sharing_info);
  }
  if (faceset_sharing_info != nullptr) {
    faceset_sharing_info->remove_user_and_delete_if_last();
  }
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Face Map Conversion
 * \{ */

void BKE_mesh_legacy_face_map_to_generic(Mesh *mesh)
{
  using namespace blender;
  if (mesh->attributes().contains("face_maps")) {
    return;
  }
  void *data = nullptr;
  const ImplicitSharingInfo *sharing_info = nullptr;
  for (const int i : IndexRange(mesh->pdata.totlayer)) {
    CustomDataLayer &layer = mesh->pdata.layers[i];
    if (layer.type == CD_FACEMAP) {
      data = layer.data;
      sharing_info = layer.sharing_info;
      layer.data = nullptr;
      layer.sharing_info = nullptr;
      CustomData_free_layer(&mesh->pdata, CD_FACEMAP, mesh->totpoly, i);
      break;
    }
  }
  if (data != nullptr) {
    CustomData_add_layer_named_with_data(
        &mesh->pdata, CD_PROP_INT32, data, mesh->totpoly, "face_maps", sharing_info);
  }
  if (sharing_info != nullptr) {
    sharing_info->remove_user_and_delete_if_last();
  }
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Bevel Weight Conversion
 * \{ */

void BKE_mesh_legacy_bevel_weight_to_layers(Mesh *mesh)
{
  using namespace blender;
  if (mesh->mvert && !CustomData_has_layer(&mesh->vdata, CD_BWEIGHT)) {
    const Span<MVert> verts(mesh->mvert, mesh->totvert);
    if (mesh->cd_flag & ME_CDFLAG_VERT_BWEIGHT) {
      float *weights = static_cast<float *>(
          CustomData_add_layer(&mesh->vdata, CD_BWEIGHT, CD_CONSTRUCT, verts.size()));
      for (const int i : verts.index_range()) {
        weights[i] = verts[i].bweight_legacy / 255.0f;
      }
    }
  }

  if (mesh->medge && !CustomData_has_layer(&mesh->edata, CD_BWEIGHT)) {
    const Span<MEdge> edges(mesh->medge, mesh->totedge);
    if (mesh->cd_flag & ME_CDFLAG_EDGE_BWEIGHT) {
      float *weights = static_cast<float *>(
          CustomData_add_layer(&mesh->edata, CD_BWEIGHT, CD_CONSTRUCT, edges.size()));
      for (const int i : edges.index_range()) {
        weights[i] = edges[i].bweight_legacy / 255.0f;
      }
    }
  }
}

static void replace_custom_data_layer_with_named(CustomData &custom_data,
                                                 const eCustomDataType old_type,
                                                 const eCustomDataType new_type,
                                                 const int elems_num,
                                                 const char *new_name)
{
  using namespace blender;
  void *data = nullptr;
  const ImplicitSharingInfo *sharing_info = nullptr;
  for (const int i : IndexRange(custom_data.totlayer)) {
    CustomDataLayer &layer = custom_data.layers[i];
    if (layer.type == old_type) {
      data = layer.data;
      sharing_info = layer.sharing_info;
      layer.data = nullptr;
      layer.sharing_info = nullptr;
      CustomData_free_layer(&custom_data, old_type, elems_num, i);
      break;
    }
  }
  if (data != nullptr) {
    CustomData_add_layer_named_with_data(
        &custom_data, new_type, data, elems_num, new_name, sharing_info);
  }
  if (sharing_info != nullptr) {
    sharing_info->remove_user_and_delete_if_last();
  }
}

void BKE_mesh_legacy_bevel_weight_to_generic(Mesh *mesh)
{
  if (!mesh->attributes().contains("bevel_weight_vert")) {
    replace_custom_data_layer_with_named(
        mesh->vdata, CD_BWEIGHT, CD_PROP_FLOAT, mesh->totvert, "bevel_weight_vert");
  }
  if (!mesh->attributes().contains("bevel_weight_edge")) {
    replace_custom_data_layer_with_named(
        mesh->edata, CD_BWEIGHT, CD_PROP_FLOAT, mesh->totedge, "bevel_weight_edge");
  }
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Crease Conversion
 * \{ */

void BKE_mesh_legacy_edge_crease_to_layers(Mesh *mesh)
{
  using namespace blender;
  if (!mesh->medge) {
    return;
  }
  if (CustomData_has_layer(&mesh->edata, CD_CREASE)) {
    return;
  }
  const Span<MEdge> edges(mesh->medge, mesh->totedge);
  if (mesh->cd_flag & ME_CDFLAG_EDGE_CREASE) {
    float *creases = static_cast<float *>(
        CustomData_add_layer(&mesh->edata, CD_CREASE, CD_CONSTRUCT, edges.size()));
    for (const int i : edges.index_range()) {
      creases[i] = edges[i].crease_legacy / 255.0f;
    }
  }
}

void BKE_mesh_legacy_crease_to_generic(Mesh *mesh)
{
  if (!mesh->attributes().contains("crease_vert")) {
    replace_custom_data_layer_with_named(
        mesh->vdata, CD_CREASE, CD_PROP_FLOAT, mesh->totvert, "crease_vert");
  }
  if (!mesh->attributes().contains("crease_edge")) {
    replace_custom_data_layer_with_named(
        mesh->edata, CD_CREASE, CD_PROP_FLOAT, mesh->totedge, "crease_edge");
  }
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Sharp Edge Conversion
 * \{ */

void BKE_mesh_legacy_sharp_edges_from_flags(Mesh *mesh)
{
  using namespace blender;
  using namespace blender::bke;
  if (!mesh->medge) {
    return;
  }
  const Span<MEdge> edges(mesh->medge, mesh->totedge);
  MutableAttributeAccessor attributes = mesh->attributes_for_write();
  if (attributes.contains("sharp_edge")) {
    return;
  }
  if (std::any_of(edges.begin(), edges.end(), [](const MEdge &edge) {
        return edge.flag_legacy & ME_SHARP;
      }))
  {
    SpanAttributeWriter<bool> sharp_edges = attributes.lookup_or_add_for_write_only_span<bool>(
        "sharp_edge", ATTR_DOMAIN_EDGE);
    threading::parallel_for(edges.index_range(), 4096, [&](const IndexRange range) {
      for (const int i : range) {
        sharp_edges.span[i] = edges[i].flag_legacy & ME_SHARP;
      }
    });
    sharp_edges.finish();
  }
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name UV Seam Conversion
 * \{ */

void BKE_mesh_legacy_uv_seam_from_flags(Mesh *mesh)
{
  using namespace blender;
  using namespace blender::bke;
  if (!mesh->medge) {
    return;
  }
  MutableSpan<MEdge> edges(mesh->medge, mesh->totedge);
  MutableAttributeAccessor attributes = mesh->attributes_for_write();
  if (attributes.contains(".uv_seam")) {
    return;
  }
  if (std::any_of(edges.begin(), edges.end(), [](const MEdge &edge) {
        return edge.flag_legacy & ME_SEAM;
      }))
  {
    SpanAttributeWriter<bool> uv_seams = attributes.lookup_or_add_for_write_only_span<bool>(
        ".uv_seam", ATTR_DOMAIN_EDGE);
    threading::parallel_for(edges.index_range(), 4096, [&](const IndexRange range) {
      for (const int i : range) {
        uv_seams.span[i] = edges[i].flag_legacy & ME_SEAM;
      }
    });
    uv_seams.finish();
  }
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Hide Attribute and Legacy Flag Conversion
 * \{ */

void BKE_mesh_legacy_convert_flags_to_hide_layers(Mesh *mesh)
{
  using namespace blender;
  using namespace blender::bke;
  MutableAttributeAccessor attributes = mesh->attributes_for_write();
  if (!mesh->mvert || attributes.contains(".hide_vert") || attributes.contains(".hide_edge") ||
      attributes.contains(".hide_poly"))
  {
    return;
  }
  const Span<MVert> verts(mesh->mvert, mesh->totvert);
  if (std::any_of(verts.begin(), verts.end(), [](const MVert &vert) {
        return vert.flag_legacy & ME_HIDE;
      }))
  {
    SpanAttributeWriter<bool> hide_vert = attributes.lookup_or_add_for_write_only_span<bool>(
        ".hide_vert", ATTR_DOMAIN_POINT);
    threading::parallel_for(verts.index_range(), 4096, [&](IndexRange range) {
      for (const int i : range) {
        hide_vert.span[i] = verts[i].flag_legacy & ME_HIDE;
      }
    });
    hide_vert.finish();
  }

  if (mesh->medge) {
    const Span<MEdge> edges(mesh->medge, mesh->totedge);
    if (std::any_of(edges.begin(), edges.end(), [](const MEdge &edge) {
          return edge.flag_legacy & ME_HIDE;
        }))
    {
      SpanAttributeWriter<bool> hide_edge = attributes.lookup_or_add_for_write_only_span<bool>(
          ".hide_edge", ATTR_DOMAIN_EDGE);
      threading::parallel_for(edges.index_range(), 4096, [&](IndexRange range) {
        for (const int i : range) {
          hide_edge.span[i] = edges[i].flag_legacy & ME_HIDE;
        }
      });
      hide_edge.finish();
    }
  }

  const Span<MPoly> polys(static_cast<const MPoly *>(CustomData_get_layer(&mesh->pdata, CD_MPOLY)),
                          mesh->totpoly);
  if (std::any_of(polys.begin(), polys.end(), [](const MPoly &poly) {
        return poly.flag_legacy & ME_HIDE;
      }))
  {
    SpanAttributeWriter<bool> hide_poly = attributes.lookup_or_add_for_write_only_span<bool>(
        ".hide_poly", ATTR_DOMAIN_FACE);
    threading::parallel_for(polys.index_range(), 4096, [&](IndexRange range) {
      for (const int i : range) {
        hide_poly.span[i] = polys[i].flag_legacy & ME_HIDE;
      }
    });
    hide_poly.finish();
  }
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Material Index Conversion
 * \{ */

void BKE_mesh_legacy_convert_mpoly_to_material_indices(Mesh *mesh)
{
  using namespace blender;
  using namespace blender::bke;
  MutableAttributeAccessor attributes = mesh->attributes_for_write();
  if (!CustomData_has_layer(&mesh->pdata, CD_MPOLY) || attributes.contains("material_index")) {
    return;
  }
  const Span<MPoly> polys(static_cast<const MPoly *>(CustomData_get_layer(&mesh->pdata, CD_MPOLY)),
                          mesh->totpoly);
  if (std::any_of(
          polys.begin(), polys.end(), [](const MPoly &poly) { return poly.mat_nr_legacy != 0; }))
  {
    SpanAttributeWriter<int> material_indices = attributes.lookup_or_add_for_write_only_span<int>(
        "material_index", ATTR_DOMAIN_FACE);
    threading::parallel_for(polys.index_range(), 4096, [&](IndexRange range) {
      for (const int i : range) {
        material_indices.span[i] = polys[i].mat_nr_legacy;
      }
    });
    material_indices.finish();
  }
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Generic UV Map Conversion
 * \{ */

void BKE_mesh_legacy_convert_uvs_to_generic(Mesh *mesh)
{
  using namespace blender;
  using namespace blender::bke;
  if (!CustomData_has_layer(&mesh->ldata, CD_MLOOPUV)) {
    return;
  }

  /* Store layer names since they will be removed, used to set the active status of new layers.
   * Use intermediate #StringRef because the names can be null. */

  Array<std::string> uv_names(CustomData_number_of_layers(&mesh->ldata, CD_MLOOPUV));
  for (const int i : uv_names.index_range()) {
    uv_names[i] = CustomData_get_layer_name(&mesh->ldata, CD_MLOOPUV, i);
  }
  const int active_name_i = uv_names.as_span().first_index_try(
      StringRef(CustomData_get_active_layer_name(&mesh->ldata, CD_MLOOPUV)));
  const int default_name_i = uv_names.as_span().first_index_try(
      StringRef(CustomData_get_render_layer_name(&mesh->ldata, CD_MLOOPUV)));

  for (const int i : uv_names.index_range()) {
    const MLoopUV *mloopuv = static_cast<const MLoopUV *>(
        CustomData_get_layer_named(&mesh->ldata, CD_MLOOPUV, uv_names[i].c_str()));
    const uint32_t needed_boolean_attributes = threading::parallel_reduce(
        IndexRange(mesh->totloop),
        4096,
        0,
        [&](const IndexRange range, uint32_t init) {
          for (const int i : range) {
            init |= mloopuv[i].flag;
          }
          return init;
        },
        [](const uint32_t a, const uint32_t b) { return a | b; });

    float2 *coords = static_cast<float2 *>(
        MEM_malloc_arrayN(mesh->totloop, sizeof(float2), __func__));
    bool *vert_selection = nullptr;
    bool *edge_selection = nullptr;
    bool *pin = nullptr;
    if (needed_boolean_attributes & MLOOPUV_VERTSEL) {
      vert_selection = static_cast<bool *>(
          MEM_malloc_arrayN(mesh->totloop, sizeof(bool), __func__));
    }
    if (needed_boolean_attributes & MLOOPUV_EDGESEL) {
      edge_selection = static_cast<bool *>(
          MEM_malloc_arrayN(mesh->totloop, sizeof(bool), __func__));
    }
    if (needed_boolean_attributes & MLOOPUV_PINNED) {
      pin = static_cast<bool *>(MEM_malloc_arrayN(mesh->totloop, sizeof(bool), __func__));
    }

    threading::parallel_for(IndexRange(mesh->totloop), 4096, [&](IndexRange range) {
      for (const int i : range) {
        coords[i] = mloopuv[i].uv;
      }
      if (vert_selection) {
        for (const int i : range) {
          vert_selection[i] = mloopuv[i].flag & MLOOPUV_VERTSEL;
        }
      }
      if (edge_selection) {
        for (const int i : range) {
          edge_selection[i] = mloopuv[i].flag & MLOOPUV_EDGESEL;
        }
      }
      if (pin) {
        for (const int i : range) {
          pin[i] = mloopuv[i].flag & MLOOPUV_PINNED;
        }
      }
    });

    CustomData_free_layer_named(&mesh->ldata, uv_names[i].c_str(), mesh->totloop);

    char new_name[MAX_CUSTOMDATA_LAYER_NAME];
    BKE_id_attribute_calc_unique_name(&mesh->id, uv_names[i].c_str(), new_name);
    uv_names[i] = new_name;

    CustomData_add_layer_named_with_data(
        &mesh->ldata, CD_PROP_FLOAT2, coords, mesh->totloop, new_name, nullptr);
    char buffer[MAX_CUSTOMDATA_LAYER_NAME];
    if (vert_selection) {
      CustomData_add_layer_named_with_data(&mesh->ldata,
                                           CD_PROP_BOOL,
                                           vert_selection,
                                           mesh->totloop,
                                           BKE_uv_map_vert_select_name_get(new_name, buffer),
                                           nullptr);
    }
    if (edge_selection) {
      CustomData_add_layer_named_with_data(&mesh->ldata,
                                           CD_PROP_BOOL,
                                           edge_selection,
                                           mesh->totloop,
                                           BKE_uv_map_edge_select_name_get(new_name, buffer),
                                           nullptr);
    }
    if (pin) {
      CustomData_add_layer_named_with_data(&mesh->ldata,
                                           CD_PROP_BOOL,
                                           pin,
                                           mesh->totloop,
                                           BKE_uv_map_pin_name_get(new_name, buffer),
                                           nullptr);
    }
  }

  if (active_name_i != -1) {
    CustomData_set_layer_active_index(
        &mesh->ldata,
        CD_PROP_FLOAT2,
        CustomData_get_named_layer_index(
            &mesh->ldata, CD_PROP_FLOAT2, uv_names[active_name_i].c_str()));
  }
  if (default_name_i != -1) {
    CustomData_set_layer_render_index(
        &mesh->ldata,
        CD_PROP_FLOAT2,
        CustomData_get_named_layer_index(
            &mesh->ldata, CD_PROP_FLOAT2, uv_names[default_name_i].c_str()));
  }
}

/** \} */

/** \name Selection Attribute and Legacy Flag Conversion
 * \{ */

void BKE_mesh_legacy_convert_flags_to_selection_layers(Mesh *mesh)
{
  using namespace blender;
  using namespace blender::bke;
  MutableAttributeAccessor attributes = mesh->attributes_for_write();
  if (!mesh->mvert || attributes.contains(".select_vert") || attributes.contains(".select_edge") ||
      attributes.contains(".select_poly"))
  {
    return;
  }

  const Span<MVert> verts(mesh->mvert, mesh->totvert);
  if (std::any_of(
          verts.begin(), verts.end(), [](const MVert &vert) { return vert.flag_legacy & SELECT; }))
  {
    SpanAttributeWriter<bool> select_vert = attributes.lookup_or_add_for_write_only_span<bool>(
        ".select_vert", ATTR_DOMAIN_POINT);
    threading::parallel_for(verts.index_range(), 4096, [&](IndexRange range) {
      for (const int i : range) {
        select_vert.span[i] = verts[i].flag_legacy & SELECT;
      }
    });
    select_vert.finish();
  }

  if (mesh->medge) {
    const Span<MEdge> edges(mesh->medge, mesh->totedge);
    if (std::any_of(edges.begin(), edges.end(), [](const MEdge &edge) {
          return edge.flag_legacy & SELECT;
        }))
    {
      SpanAttributeWriter<bool> select_edge = attributes.lookup_or_add_for_write_only_span<bool>(
          ".select_edge", ATTR_DOMAIN_EDGE);
      threading::parallel_for(edges.index_range(), 4096, [&](IndexRange range) {
        for (const int i : range) {
          select_edge.span[i] = edges[i].flag_legacy & SELECT;
        }
      });
      select_edge.finish();
    }
  }

  const Span<MPoly> polys(static_cast<const MPoly *>(CustomData_get_layer(&mesh->pdata, CD_MPOLY)),
                          mesh->totpoly);
  if (std::any_of(polys.begin(), polys.end(), [](const MPoly &poly) {
        return poly.flag_legacy & ME_FACE_SEL;
      }))
  {
    SpanAttributeWriter<bool> select_poly = attributes.lookup_or_add_for_write_only_span<bool>(
        ".select_poly", ATTR_DOMAIN_FACE);
    threading::parallel_for(polys.index_range(), 4096, [&](IndexRange range) {
      for (const int i : range) {
        select_poly.span[i] = polys[i].flag_legacy & ME_FACE_SEL;
      }
    });
    select_poly.finish();
  }
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Vertex and Position Conversion
 * \{ */

void BKE_mesh_legacy_convert_verts_to_positions(Mesh *mesh)
{
  using namespace blender;
  using namespace blender::bke;
  const MVert *mvert = static_cast<const MVert *>(CustomData_get_layer(&mesh->vdata, CD_MVERT));
  if (!mvert || CustomData_has_layer_named(&mesh->vdata, CD_PROP_FLOAT3, "position")) {
    return;
  }

  const Span<MVert> verts(mvert, mesh->totvert);
  MutableSpan<float3> positions(
      static_cast<float3 *>(CustomData_add_layer_named(
          &mesh->vdata, CD_PROP_FLOAT3, CD_CONSTRUCT, mesh->totvert, "position")),
      mesh->totvert);
  threading::parallel_for(verts.index_range(), 2048, [&](IndexRange range) {
    for (const int i : range) {
      positions[i] = verts[i].co_legacy;
    }
  });

  CustomData_free_layers(&mesh->vdata, CD_MVERT, mesh->totvert);
  mesh->mvert = nullptr;
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name MEdge and int2 conversion
 * \{ */

void BKE_mesh_legacy_convert_edges_to_generic(Mesh *mesh)
{
  using namespace blender;
  using namespace blender::bke;
  const MEdge *medge = static_cast<const MEdge *>(CustomData_get_layer(&mesh->edata, CD_MEDGE));
  if (!medge || CustomData_has_layer_named(&mesh->edata, CD_PROP_INT32_2D, ".edge_verts")) {
    return;
  }

  const Span<MEdge> legacy_edges(medge, mesh->totedge);
  MutableSpan<int2> edges(
      static_cast<int2 *>(CustomData_add_layer_named(
          &mesh->edata, CD_PROP_INT32_2D, CD_CONSTRUCT, mesh->totedge, ".edge_verts")),
      mesh->totedge);
  threading::parallel_for(legacy_edges.index_range(), 2048, [&](IndexRange range) {
    for (const int i : range) {
      edges[i] = int2(legacy_edges[i].v1, legacy_edges[i].v2);
    }
  });

  CustomData_free_layers(&mesh->edata, CD_MEDGE, mesh->totedge);
  mesh->medge = nullptr;
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Attribute Active Flag to String Conversion
 * \{ */

void BKE_mesh_legacy_attribute_flags_to_strings(Mesh *mesh)
{
  using namespace blender;
  /* It's not clear whether the active/render status was stored in the dedicated flags or in the
   * generic CustomData layer indices, so convert from both, preferring the explicit flags. */

  auto active_from_flags = [&](const CustomData &data) {
    if (!mesh->active_color_attribute) {
      for (const int i : IndexRange(data.totlayer)) {
        if (data.layers[i].flag & CD_FLAG_COLOR_ACTIVE) {
          mesh->active_color_attribute = BLI_strdup(data.layers[i].name);
        }
      }
    }
  };
  auto active_from_indices = [&](const CustomData &data) {
    if (!mesh->active_color_attribute) {
      const int i = CustomData_get_active_layer_index(&data, CD_PROP_COLOR);
      if (i != -1) {
        mesh->active_color_attribute = BLI_strdup(data.layers[i].name);
      }
    }
    if (!mesh->active_color_attribute) {
      const int i = CustomData_get_active_layer_index(&data, CD_PROP_BYTE_COLOR);
      if (i != -1) {
        mesh->active_color_attribute = BLI_strdup(data.layers[i].name);
      }
    }
  };
  auto default_from_flags = [&](const CustomData &data) {
    if (!mesh->default_color_attribute) {
      for (const int i : IndexRange(data.totlayer)) {
        if (data.layers[i].flag & CD_FLAG_COLOR_RENDER) {
          mesh->default_color_attribute = BLI_strdup(data.layers[i].name);
        }
      }
    }
  };
  auto default_from_indices = [&](const CustomData &data) {
    if (!mesh->default_color_attribute) {
      const int i = CustomData_get_render_layer_index(&data, CD_PROP_COLOR);
      if (i != -1) {
        mesh->default_color_attribute = BLI_strdup(data.layers[i].name);
      }
    }
    if (!mesh->default_color_attribute) {
      const int i = CustomData_get_render_layer_index(&data, CD_PROP_BYTE_COLOR);
      if (i != -1) {
        mesh->default_color_attribute = BLI_strdup(data.layers[i].name);
      }
    }
  };

  active_from_flags(mesh->vdata);
  active_from_flags(mesh->ldata);
  active_from_indices(mesh->vdata);
  active_from_indices(mesh->ldata);

  default_from_flags(mesh->vdata);
  default_from_flags(mesh->ldata);
  default_from_indices(mesh->vdata);
  default_from_indices(mesh->ldata);
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Face Corner Conversion
 * \{ */

void BKE_mesh_legacy_convert_loops_to_corners(Mesh *mesh)
{
  using namespace blender;
  if (CustomData_has_layer_named(&mesh->ldata, CD_PROP_INT32, ".corner_vert") &&
      CustomData_has_layer_named(&mesh->ldata, CD_PROP_INT32, ".corner_edge"))
  {
    return;
  }
  const Span<MLoop> loops(static_cast<const MLoop *>(CustomData_get_layer(&mesh->ldata, CD_MLOOP)),
                          mesh->totloop);
  MutableSpan<int> corner_verts(
      static_cast<int *>(CustomData_add_layer_named(
          &mesh->ldata, CD_PROP_INT32, CD_CONSTRUCT, mesh->totloop, ".corner_vert")),
      mesh->totloop);
  MutableSpan<int> corner_edges(
      static_cast<int *>(CustomData_add_layer_named(
          &mesh->ldata, CD_PROP_INT32, CD_CONSTRUCT, mesh->totloop, ".corner_edge")),
      mesh->totloop);
  threading::parallel_for(loops.index_range(), 2048, [&](IndexRange range) {
    for (const int i : range) {
      corner_verts[i] = loops[i].v;
      corner_edges[i] = loops[i].e;
    }
  });

  CustomData_free_layers(&mesh->ldata, CD_MLOOP, mesh->totloop);
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Poly Offset Conversion
 * \{ */

static bool poly_loops_orders_match(const Span<MPoly> polys)
{
  for (const int i : polys.index_range().drop_back(1)) {
    if (polys[i].loopstart > polys[i + 1].loopstart) {
      return false;
    }
  }
  return true;
}

void BKE_mesh_legacy_convert_polys_to_offsets(Mesh *mesh)
{
  using namespace blender;
  if (mesh->poly_offset_indices) {
    return;
  }
  const Span<MPoly> polys(static_cast<const MPoly *>(CustomData_get_layer(&mesh->pdata, CD_MPOLY)),
                          mesh->totpoly);

  BKE_mesh_poly_offsets_ensure_alloc(mesh);
  MutableSpan<int> offsets = mesh->poly_offsets_for_write();

  if (poly_loops_orders_match(polys)) {
    for (const int i : polys.index_range()) {
      offsets[i] = polys[i].loopstart;
    }
  }
  else {
    /* Reorder mesh polygons to match the order of their loops. */
    Array<int> orig_indices(polys.size());
    std::iota(orig_indices.begin(), orig_indices.end(), 0);
    std::stable_sort(orig_indices.begin(), orig_indices.end(), [polys](const int a, const int b) {
      return polys[a].loopstart < polys[b].loopstart;
    });
    CustomData old_poly_data = mesh->pdata;
    CustomData_reset(&mesh->pdata);
    CustomData_copy_layout(
        &old_poly_data, &mesh->pdata, CD_MASK_MESH.pmask, CD_CONSTRUCT, mesh->totpoly);

    int offset = 0;
    for (const int i : orig_indices.index_range()) {
      offsets[i] = offset;
      offset += polys[orig_indices[i]].totloop;
    }

    threading::parallel_for(orig_indices.index_range(), 1024, [&](const IndexRange range) {
      for (const int i : range) {
        CustomData_copy_data(&old_poly_data, &mesh->pdata, orig_indices[i], i, 1);
      }
    });

    CustomData_free(&old_poly_data, mesh->totpoly);
  }

  CustomData_free_layers(&mesh->pdata, CD_MPOLY, mesh->totpoly);
}

/** \} */

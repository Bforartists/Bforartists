/* SPDX-License-Identifier: GPL-2.0-or-later
 * Copyright 2001-2002 NaN Holding BV. All rights reserved. */

/** \file
 * \ingroup bke
 *
 * Mesh normal calculation functions.
 *
 * \see bmesh_mesh_normals.c for the equivalent #BMesh functionality.
 */

#include <climits>

#include "MEM_guardedalloc.h"

#include "DNA_mesh_types.h"
#include "DNA_meshdata_types.h"

#include "BLI_alloca.h"
#include "BLI_bit_vector.hh"
#include "BLI_linklist.h"
#include "BLI_linklist_stack.h"
#include "BLI_math.h"
#include "BLI_math_vector.hh"
#include "BLI_memarena.h"
#include "BLI_span.hh"
#include "BLI_stack.h"
#include "BLI_task.h"
#include "BLI_task.hh"
#include "BLI_timeit.hh"
#include "BLI_utildefines.h"

#include "BKE_attribute.hh"
#include "BKE_customdata.h"
#include "BKE_editmesh_cache.h"
#include "BKE_global.h"
#include "BKE_mesh.hh"
#include "BKE_mesh_mapping.h"

#include "atomic_ops.h"

using blender::BitVector;
using blender::float3;
using blender::int2;
using blender::MutableBitSpan;
using blender::MutableSpan;
using blender::short2;
using blender::Span;
using blender::VArray;

// #define DEBUG_TIME

#ifdef DEBUG_TIME
#  include "BLI_timeit.hh"
#endif

/* -------------------------------------------------------------------- */
/** \name Private Utility Functions
 * \{ */

/**
 * A thread-safe version of #add_v3_v3 that uses a spin-lock.
 *
 * \note Avoid using this when the chance of contention is high.
 */
static void add_v3_v3_atomic(float r[3], const float a[3])
{
#define FLT_EQ_NONAN(_fa, _fb) (*((const uint32_t *)&_fa) == *((const uint32_t *)&_fb))

  float virtual_lock = r[0];
  while (true) {
    /* This loops until following conditions are met:
     * - `r[0]` has same value as virtual_lock (i.e. it did not change since last try).
     * - `r[0]` was not `FLT_MAX`, i.e. it was not locked by another thread. */
    const float test_lock = atomic_cas_float(&r[0], virtual_lock, FLT_MAX);
    if (_ATOMIC_LIKELY(FLT_EQ_NONAN(test_lock, virtual_lock) && (test_lock != FLT_MAX))) {
      break;
    }
    virtual_lock = test_lock;
  }
  virtual_lock += a[0];
  r[1] += a[1];
  r[2] += a[2];

  /* Second atomic operation to 'release'
   * our lock on that vector and set its first scalar value. */
  /* Note that we do not need to loop here, since we 'locked' `r[0]`,
   * nobody should have changed it in the mean time. */
  virtual_lock = atomic_cas_float(&r[0], FLT_MAX, virtual_lock);
  BLI_assert(virtual_lock == FLT_MAX);

#undef FLT_EQ_NONAN
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Public Utility Functions
 *
 * Related to managing normals but not directly related to calculating normals.
 * \{ */

float (*BKE_mesh_vert_normals_for_write(Mesh *mesh))[3]
{
  mesh->runtime->vert_normals.reinitialize(mesh->totvert);
  return reinterpret_cast<float(*)[3]>(mesh->runtime->vert_normals.data());
}

float (*BKE_mesh_poly_normals_for_write(Mesh *mesh))[3]
{
  mesh->runtime->poly_normals.reinitialize(mesh->totpoly);
  return reinterpret_cast<float(*)[3]>(mesh->runtime->poly_normals.data());
}

void BKE_mesh_vert_normals_clear_dirty(Mesh *mesh)
{
  mesh->runtime->vert_normals_dirty = false;
  BLI_assert(mesh->runtime->vert_normals.size() == mesh->totvert);
}

void BKE_mesh_poly_normals_clear_dirty(Mesh *mesh)
{
  mesh->runtime->poly_normals_dirty = false;
  BLI_assert(mesh->runtime->poly_normals.size() == mesh->totpoly);
}

bool BKE_mesh_vert_normals_are_dirty(const Mesh *mesh)
{
  return mesh->runtime->vert_normals_dirty;
}

bool BKE_mesh_poly_normals_are_dirty(const Mesh *mesh)
{
  return mesh->runtime->poly_normals_dirty;
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Mesh Normal Calculation (Polygons)
 * \{ */

namespace blender::bke::mesh {

/*
 * COMPUTE POLY NORMAL
 *
 * Computes the normal of a planar
 * polygon See Graphics Gems for
 * computing newell normal.
 */
static float3 normal_calc_ngon(const Span<float3> vert_positions, const Span<int> poly_verts)
{
  float3 normal(0);

  /* Newell's Method */
  const float *v_prev = vert_positions[poly_verts.last()];
  for (const int i : poly_verts.index_range()) {
    const float *v_curr = vert_positions[poly_verts[i]];
    add_newell_cross_v3_v3v3(normal, v_prev, v_curr);
    v_prev = v_curr;
  }

  if (UNLIKELY(normalize_v3(normal) == 0.0f)) {
    normal[2] = 1.0f; /* other axis set to 0.0 */
  }

  return normal;
}

float3 poly_normal_calc(const Span<float3> vert_positions, const Span<int> poly_verts)
{
  if (poly_verts.size() > 4) {
    return normal_calc_ngon(vert_positions, poly_verts);
  }
  if (poly_verts.size() == 3) {
    return math::normal_tri(vert_positions[poly_verts[0]],
                            vert_positions[poly_verts[1]],
                            vert_positions[poly_verts[2]]);
  }
  if (poly_verts.size() == 4) {
    float3 normal;
    normal_quad_v3(normal,
                   vert_positions[poly_verts[0]],
                   vert_positions[poly_verts[1]],
                   vert_positions[poly_verts[2]],
                   vert_positions[poly_verts[3]]);
    return normal;
  }
  /* horrible, two sided face! */
  return float3(0);
}

}  // namespace blender::bke::mesh

void BKE_mesh_calc_poly_normal(const int *poly_verts,
                               const int poly_size,
                               const float (*vert_positions)[3],
                               const int verts_num,
                               float r_no[3])
{
  copy_v3_v3(r_no,
             blender::bke::mesh::poly_normal_calc(
                 {reinterpret_cast<const blender::float3 *>(vert_positions), verts_num},
                 {poly_verts, poly_size}));
}

namespace blender::bke::mesh {

void normals_calc_polys(const Span<float3> positions,
                        const Span<MPoly> polys,
                        const Span<int> corner_verts,
                        MutableSpan<float3> poly_normals)
{
  BLI_assert(polys.size() == poly_normals.size());
  threading::parallel_for(polys.index_range(), 1024, [&](const IndexRange range) {
    for (const int i : range) {
      const MPoly &poly = polys[i];
      poly_normals[i] = poly_normal_calc(positions,
                                         corner_verts.slice(poly.loopstart, poly.totloop));
    }
  });
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Mesh Normal Calculation (Polygons & Vertices)
 *
 * Take care making optimizations to this function as improvements to low-poly
 * meshes can slow down high-poly meshes. For details on performance, see D11993.
 * \{ */

void normals_calc_poly_vert(const Span<float3> positions,
                            const Span<MPoly> polys,
                            const Span<int> corner_verts,
                            MutableSpan<float3> poly_normals,
                            MutableSpan<float3> vert_normals)
{

  /* Zero the vertex normal array for accumulation. */
  {
    memset(vert_normals.data(), 0, vert_normals.as_span().size_in_bytes());
  }

  /* Compute poly normals, accumulating them into vertex normals. */
  {
    threading::parallel_for(polys.index_range(), 1024, [&](const IndexRange range) {
      for (const int poly_i : range) {
        const MPoly &poly = polys[poly_i];
        const Span<int> poly_verts = corner_verts.slice(poly.loopstart, poly.totloop);

        float3 &pnor = poly_normals[poly_i];

        const int i_end = poly.totloop - 1;

        /* Polygon Normal and edge-vector. */
        /* Inline version of #poly_normal_calc, also does edge-vectors. */
        {
          zero_v3(pnor);
          /* Newell's Method */
          const float *v_curr = positions[poly_verts[i_end]];
          for (int i_next = 0; i_next <= i_end; i_next++) {
            const float *v_next = positions[poly_verts[i_next]];
            add_newell_cross_v3_v3v3(pnor, v_curr, v_next);
            v_curr = v_next;
          }
          if (UNLIKELY(normalize_v3(pnor) == 0.0f)) {
            pnor[2] = 1.0f; /* Other axes set to zero. */
          }
        }

        /* Accumulate angle weighted face normal into the vertex normal. */
        /* Inline version of #accumulate_vertex_normals_poly_v3. */
        {
          float edvec_prev[3], edvec_next[3], edvec_end[3];
          const float *v_curr = positions[poly_verts[i_end]];
          sub_v3_v3v3(edvec_prev, positions[poly_verts[i_end - 1]], v_curr);
          normalize_v3(edvec_prev);
          copy_v3_v3(edvec_end, edvec_prev);

          for (int i_next = 0, i_curr = i_end; i_next <= i_end; i_curr = i_next++) {
            const float *v_next = positions[poly_verts[i_next]];

            /* Skip an extra normalization by reusing the first calculated edge. */
            if (i_next != i_end) {
              sub_v3_v3v3(edvec_next, v_curr, v_next);
              normalize_v3(edvec_next);
            }
            else {
              copy_v3_v3(edvec_next, edvec_end);
            }

            /* Calculate angle between the two poly edges incident on this vertex. */
            const float fac = saacos(-dot_v3v3(edvec_prev, edvec_next));
            const float vnor_add[3] = {pnor[0] * fac, pnor[1] * fac, pnor[2] * fac};

            float *vnor = vert_normals[poly_verts[i_curr]];
            add_v3_v3_atomic(vnor, vnor_add);
            v_curr = v_next;
            copy_v3_v3(edvec_prev, edvec_next);
          }
        }
      }
    });
  }

  /* Normalize and validate computed vertex normals. */
  {
    threading::parallel_for(positions.index_range(), 1024, [&](const IndexRange range) {
      for (const int vert_i : range) {
        float *no = vert_normals[vert_i];

        if (UNLIKELY(normalize_v3(no) == 0.0f)) {
          /* Following Mesh convention; we use vertex coordinate itself for normal in this case. */
          normalize_v3_v3(no, positions[vert_i]);
        }
      }
    });
  }
}

}  // namespace blender::bke::mesh

/** \} */

/* -------------------------------------------------------------------- */
/** \name Mesh Normal Calculation
 * \{ */

blender::Span<blender::float3> Mesh::vert_normals() const
{
  if (!this->runtime->vert_normals_dirty) {
    BLI_assert(this->runtime->vert_normals.size() == this->totvert);
    return this->runtime->vert_normals;
  }

  std::lock_guard lock{this->runtime->normals_mutex};
  if (!this->runtime->vert_normals_dirty) {
    BLI_assert(this->runtime->vert_normals.size() == this->totvert);
    return this->runtime->vert_normals;
  }

  /* Isolate task because a mutex is locked and computing normals is multi-threaded. */
  blender::threading::isolate_task([&]() {
    const Span<float3> positions = this->vert_positions();
    const Span<MPoly> polys = this->polys();
    const Span<int> corner_verts = this->corner_verts();

    this->runtime->vert_normals.reinitialize(positions.size());
    this->runtime->poly_normals.reinitialize(polys.size());
    blender::bke::mesh::normals_calc_poly_vert(
        positions, polys, corner_verts, this->runtime->poly_normals, this->runtime->vert_normals);

    this->runtime->vert_normals_dirty = false;
    this->runtime->poly_normals_dirty = false;
  });

  return this->runtime->vert_normals;
}

blender::Span<blender::float3> Mesh::poly_normals() const
{
  if (!this->runtime->poly_normals_dirty) {
    BLI_assert(this->runtime->poly_normals.size() == this->totpoly);
    return this->runtime->poly_normals;
  }

  std::lock_guard lock{this->runtime->normals_mutex};
  if (!this->runtime->poly_normals_dirty) {
    BLI_assert(this->runtime->poly_normals.size() == this->totpoly);
    return this->runtime->poly_normals;
  }

  /* Isolate task because a mutex is locked and computing normals is multi-threaded. */
  blender::threading::isolate_task([&]() {
    const Span<float3> positions = this->vert_positions();
    const Span<MPoly> polys = this->polys();
    const Span<int> corner_verts = this->corner_verts();

    this->runtime->poly_normals.reinitialize(polys.size());
    blender::bke::mesh::normals_calc_polys(
        positions, polys, corner_verts, this->runtime->poly_normals);

    this->runtime->poly_normals_dirty = false;
  });

  return this->runtime->poly_normals;
}

const float (*BKE_mesh_vert_normals_ensure(const Mesh *mesh))[3]
{
  return reinterpret_cast<const float(*)[3]>(mesh->vert_normals().data());
}

const float (*BKE_mesh_poly_normals_ensure(const Mesh *mesh))[3]
{
  return reinterpret_cast<const float(*)[3]>(mesh->vert_normals().data());
}

void BKE_mesh_ensure_normals_for_display(Mesh *mesh)
{
  switch (mesh->runtime->wrapper_type) {
    case ME_WRAPPER_TYPE_SUBD:
    case ME_WRAPPER_TYPE_MDATA:
      mesh->vert_normals();
      mesh->poly_normals();
      break;
    case ME_WRAPPER_TYPE_BMESH: {
      BMEditMesh *em = mesh->edit_mesh;
      EditMeshData *emd = mesh->runtime->edit_data;
      if (emd->vertexCos) {
        BKE_editmesh_cache_ensure_vert_normals(em, emd);
        BKE_editmesh_cache_ensure_poly_normals(em, emd);
      }
      return;
    }
  }
}

void BKE_lnor_spacearr_init(MLoopNorSpaceArray *lnors_spacearr,
                            const int numLoops,
                            const char data_type)
{
  if (!(lnors_spacearr->lspacearr && lnors_spacearr->loops_pool)) {
    MemArena *mem;

    if (!lnors_spacearr->mem) {
      lnors_spacearr->mem = BLI_memarena_new(BLI_MEMARENA_STD_BUFSIZE, __func__);
    }
    mem = lnors_spacearr->mem;
    if (numLoops > 0) {
      lnors_spacearr->lspacearr = (MLoopNorSpace **)BLI_memarena_calloc(
          mem, sizeof(MLoopNorSpace *) * size_t(numLoops));
      lnors_spacearr->loops_pool = (LinkNode *)BLI_memarena_alloc(
          mem, sizeof(LinkNode) * size_t(numLoops));
    }
    else {
      lnors_spacearr->lspacearr = nullptr;
      lnors_spacearr->loops_pool = nullptr;
    }

    lnors_spacearr->spaces_num = 0;
  }
  BLI_assert(ELEM(data_type, MLNOR_SPACEARR_BMLOOP_PTR, MLNOR_SPACEARR_LOOP_INDEX));
  lnors_spacearr->data_type = data_type;
}

void BKE_lnor_spacearr_tls_init(MLoopNorSpaceArray *lnors_spacearr,
                                MLoopNorSpaceArray *lnors_spacearr_tls)
{
  *lnors_spacearr_tls = *lnors_spacearr;
  lnors_spacearr_tls->mem = BLI_memarena_new(BLI_MEMARENA_STD_BUFSIZE, __func__);
}

void BKE_lnor_spacearr_tls_join(MLoopNorSpaceArray *lnors_spacearr,
                                MLoopNorSpaceArray *lnors_spacearr_tls)
{
  BLI_assert(lnors_spacearr->data_type == lnors_spacearr_tls->data_type);
  BLI_assert(lnors_spacearr->mem != lnors_spacearr_tls->mem);
  lnors_spacearr->spaces_num += lnors_spacearr_tls->spaces_num;
  BLI_memarena_merge(lnors_spacearr->mem, lnors_spacearr_tls->mem);
  BLI_memarena_free(lnors_spacearr_tls->mem);
  lnors_spacearr_tls->mem = nullptr;
  BKE_lnor_spacearr_clear(lnors_spacearr_tls);
}

void BKE_lnor_spacearr_clear(MLoopNorSpaceArray *lnors_spacearr)
{
  lnors_spacearr->spaces_num = 0;
  lnors_spacearr->lspacearr = nullptr;
  lnors_spacearr->loops_pool = nullptr;
  if (lnors_spacearr->mem != nullptr) {
    BLI_memarena_clear(lnors_spacearr->mem);
  }
}

void BKE_lnor_spacearr_free(MLoopNorSpaceArray *lnors_spacearr)
{
  lnors_spacearr->spaces_num = 0;
  lnors_spacearr->lspacearr = nullptr;
  lnors_spacearr->loops_pool = nullptr;
  BLI_memarena_free(lnors_spacearr->mem);
  lnors_spacearr->mem = nullptr;
}

MLoopNorSpace *BKE_lnor_space_create(MLoopNorSpaceArray *lnors_spacearr)
{
  lnors_spacearr->spaces_num++;
  return (MLoopNorSpace *)BLI_memarena_calloc(lnors_spacearr->mem, sizeof(MLoopNorSpace));
}

/* This threshold is a bit touchy (usual float precision issue), this value seems OK. */
#define LNOR_SPACE_TRIGO_THRESHOLD (1.0f - 1e-4f)

void BKE_lnor_space_define(MLoopNorSpace *lnor_space,
                           const float lnor[3],
                           float vec_ref[3],
                           float vec_other[3],
                           BLI_Stack *edge_vectors)
{
  const float pi2 = float(M_PI) * 2.0f;
  float tvec[3], dtp;
  const float dtp_ref = dot_v3v3(vec_ref, lnor);
  const float dtp_other = dot_v3v3(vec_other, lnor);

  if (UNLIKELY(fabsf(dtp_ref) >= LNOR_SPACE_TRIGO_THRESHOLD ||
               fabsf(dtp_other) >= LNOR_SPACE_TRIGO_THRESHOLD)) {
    /* If vec_ref or vec_other are too much aligned with lnor, we can't build lnor space,
     * tag it as invalid and abort. */
    lnor_space->ref_alpha = lnor_space->ref_beta = 0.0f;

    if (edge_vectors) {
      BLI_stack_clear(edge_vectors);
    }
    return;
  }

  copy_v3_v3(lnor_space->vec_lnor, lnor);

  /* Compute ref alpha, average angle of all available edge vectors to lnor. */
  if (edge_vectors) {
    float alpha = 0.0f;
    int count = 0;
    while (!BLI_stack_is_empty(edge_vectors)) {
      const float *vec = (const float *)BLI_stack_peek(edge_vectors);
      alpha += saacosf(dot_v3v3(vec, lnor));
      BLI_stack_discard(edge_vectors);
      count++;
    }
    /* NOTE: In theory, this could be `count > 2`,
     * but there is one case where we only have two edges for two loops:
     * a smooth vertex with only two edges and two faces (our Monkey's nose has that, e.g.).
     */
    BLI_assert(count >= 2); /* This piece of code shall only be called for more than one loop. */
    lnor_space->ref_alpha = alpha / float(count);
  }
  else {
    lnor_space->ref_alpha = (saacosf(dot_v3v3(vec_ref, lnor)) +
                             saacosf(dot_v3v3(vec_other, lnor))) /
                            2.0f;
  }

  /* Project vec_ref on lnor's ortho plane. */
  mul_v3_v3fl(tvec, lnor, dtp_ref);
  sub_v3_v3(vec_ref, tvec);
  normalize_v3_v3(lnor_space->vec_ref, vec_ref);

  cross_v3_v3v3(tvec, lnor, lnor_space->vec_ref);
  normalize_v3_v3(lnor_space->vec_ortho, tvec);

  /* Project vec_other on lnor's ortho plane. */
  mul_v3_v3fl(tvec, lnor, dtp_other);
  sub_v3_v3(vec_other, tvec);
  normalize_v3(vec_other);

  /* Beta is angle between ref_vec and other_vec, around lnor. */
  dtp = dot_v3v3(lnor_space->vec_ref, vec_other);
  if (LIKELY(dtp < LNOR_SPACE_TRIGO_THRESHOLD)) {
    const float beta = saacos(dtp);
    lnor_space->ref_beta = (dot_v3v3(lnor_space->vec_ortho, vec_other) < 0.0f) ? pi2 - beta : beta;
  }
  else {
    lnor_space->ref_beta = pi2;
  }
}

void BKE_lnor_space_add_loop(MLoopNorSpaceArray *lnors_spacearr,
                             MLoopNorSpace *lnor_space,
                             const int ml_index,
                             void *bm_loop,
                             const bool is_single)
{
  BLI_assert((lnors_spacearr->data_type == MLNOR_SPACEARR_LOOP_INDEX && bm_loop == nullptr) ||
             (lnors_spacearr->data_type == MLNOR_SPACEARR_BMLOOP_PTR && bm_loop != nullptr));

  lnors_spacearr->lspacearr[ml_index] = lnor_space;
  if (bm_loop == nullptr) {
    bm_loop = POINTER_FROM_INT(ml_index);
  }
  if (is_single) {
    BLI_assert(lnor_space->loops == nullptr);
    lnor_space->flags |= MLNOR_SPACE_IS_SINGLE;
    lnor_space->loops = (LinkNode *)bm_loop;
  }
  else {
    BLI_assert((lnor_space->flags & MLNOR_SPACE_IS_SINGLE) == 0);
    BLI_linklist_prepend_nlink(&lnor_space->loops, bm_loop, &lnors_spacearr->loops_pool[ml_index]);
  }
}

MINLINE float unit_short_to_float(const short val)
{
  return float(val) / float(SHRT_MAX);
}

MINLINE short unit_float_to_short(const float val)
{
  /* Rounding. */
  return short(floorf(val * float(SHRT_MAX) + 0.5f));
}

void BKE_lnor_space_custom_data_to_normal(const MLoopNorSpace *lnor_space,
                                          const short clnor_data[2],
                                          float r_custom_lnor[3])
{
  /* NOP custom normal data or invalid lnor space, return. */
  if (clnor_data[0] == 0 || lnor_space->ref_alpha == 0.0f || lnor_space->ref_beta == 0.0f) {
    copy_v3_v3(r_custom_lnor, lnor_space->vec_lnor);
    return;
  }

  {
    /* TODO: Check whether using #sincosf() gives any noticeable benefit
     * (could not even get it working under linux though)! */
    const float pi2 = float(M_PI * 2.0);
    const float alphafac = unit_short_to_float(clnor_data[0]);
    const float alpha = (alphafac > 0.0f ? lnor_space->ref_alpha : pi2 - lnor_space->ref_alpha) *
                        alphafac;
    const float betafac = unit_short_to_float(clnor_data[1]);

    mul_v3_v3fl(r_custom_lnor, lnor_space->vec_lnor, cosf(alpha));

    if (betafac == 0.0f) {
      madd_v3_v3fl(r_custom_lnor, lnor_space->vec_ref, sinf(alpha));
    }
    else {
      const float sinalpha = sinf(alpha);
      const float beta = (betafac > 0.0f ? lnor_space->ref_beta : pi2 - lnor_space->ref_beta) *
                         betafac;
      madd_v3_v3fl(r_custom_lnor, lnor_space->vec_ref, sinalpha * cosf(beta));
      madd_v3_v3fl(r_custom_lnor, lnor_space->vec_ortho, sinalpha * sinf(beta));
    }
  }
}

void BKE_lnor_space_custom_normal_to_data(const MLoopNorSpace *lnor_space,
                                          const float custom_lnor[3],
                                          short r_clnor_data[2])
{
  /* We use nullptr vector as NOP custom normal (can be simpler than giving auto-computed `lnor`).
   */
  if (is_zero_v3(custom_lnor) || compare_v3v3(lnor_space->vec_lnor, custom_lnor, 1e-4f)) {
    r_clnor_data[0] = r_clnor_data[1] = 0;
    return;
  }

  {
    const float pi2 = float(M_PI * 2.0);
    const float cos_alpha = dot_v3v3(lnor_space->vec_lnor, custom_lnor);
    float vec[3], cos_beta;
    float alpha;

    alpha = saacosf(cos_alpha);
    if (alpha > lnor_space->ref_alpha) {
      /* Note we could stick to [0, pi] range here,
       * but makes decoding more complex, not worth it. */
      r_clnor_data[0] = unit_float_to_short(-(pi2 - alpha) / (pi2 - lnor_space->ref_alpha));
    }
    else {
      r_clnor_data[0] = unit_float_to_short(alpha / lnor_space->ref_alpha);
    }

    /* Project custom lnor on (vec_ref, vec_ortho) plane. */
    mul_v3_v3fl(vec, lnor_space->vec_lnor, -cos_alpha);
    add_v3_v3(vec, custom_lnor);
    normalize_v3(vec);

    cos_beta = dot_v3v3(lnor_space->vec_ref, vec);

    if (cos_beta < LNOR_SPACE_TRIGO_THRESHOLD) {
      float beta = saacosf(cos_beta);
      if (dot_v3v3(lnor_space->vec_ortho, vec) < 0.0f) {
        beta = pi2 - beta;
      }

      if (beta > lnor_space->ref_beta) {
        r_clnor_data[1] = unit_float_to_short(-(pi2 - beta) / (pi2 - lnor_space->ref_beta));
      }
      else {
        r_clnor_data[1] = unit_float_to_short(beta / lnor_space->ref_beta);
      }
    }
    else {
      r_clnor_data[1] = 0;
    }
  }
}

#define LOOP_SPLIT_TASK_BLOCK_SIZE 1024

struct LoopSplitTaskData {
  enum class Type : int8_t {
    BlockEnd = 0, /* Set implicitly by calloc. */
    Fan = 1,
    Single = 2,
  };

  /** We have to create those outside of tasks, since #MemArena is not thread-safe. */
  MLoopNorSpace *lnor_space;
  int ml_curr_index;
  /** Also used a flag to switch between single or fan process! */
  int ml_prev_index;
  int poly_index;

  Type flag;
};

struct LoopSplitTaskDataCommon {
  /* Read/write.
   * Note we do not need to protect it, though, since two different tasks will *always* affect
   * different elements in the arrays. */
  MLoopNorSpaceArray *lnors_spacearr;
  MutableSpan<float3> loop_normals;
  MutableSpan<short2> clnors_data;

  /* Read-only. */
  Span<float3> positions;
  Span<MEdge> edges;
  Span<int> corner_verts;
  Span<int> corner_edges;
  Span<MPoly> polys;
  Span<int2> edge_to_loops;
  Span<int> loop_to_poly;
  Span<float3> poly_normals;
  Span<float3> vert_normals;
};

#define INDEX_UNSET INT_MIN
#define INDEX_INVALID -1
/* See comment about edge_to_loops below. */
#define IS_EDGE_SHARP(_e2l) ELEM((_e2l)[1], INDEX_UNSET, INDEX_INVALID)

namespace blender::bke::mesh {

static void mesh_edges_sharp_tag(const Span<MPoly> polys,
                                 const Span<int> corner_verts,
                                 const Span<int> corner_edges,
                                 const Span<int> loop_to_poly_map,
                                 const Span<float3> poly_normals,
                                 const Span<bool> sharp_faces,
                                 const Span<bool> sharp_edges,
                                 const bool check_angle,
                                 const float split_angle,
                                 MutableSpan<int2> edge_to_loops,
                                 MutableSpan<bool> r_sharp_edges)
{
  const float split_angle_cos = check_angle ? cosf(split_angle) : -1.0f;
  auto poly_is_smooth = [&](const int poly_i) {
    return sharp_faces.is_empty() || !sharp_faces[poly_i];
  };

  for (const int poly_i : polys.index_range()) {
    const MPoly &poly = polys[poly_i];
    for (const int loop_index : IndexRange(poly.loopstart, poly.totloop)) {
      const int vert_i = corner_verts[loop_index];
      const int edge_i = corner_edges[loop_index];

      int2 &e2l = edge_to_loops[edge_i];

      /* Check whether current edge might be smooth or sharp */
      if ((e2l[0] | e2l[1]) == 0) {
        /* 'Empty' edge until now, set e2l[0] (and e2l[1] to INDEX_UNSET to tag it as unset). */
        e2l[0] = loop_index;
        /* We have to check this here too, else we might miss some flat faces!!! */
        e2l[1] = (poly_is_smooth(poly_i)) ? INDEX_UNSET : INDEX_INVALID;
      }
      else if (e2l[1] == INDEX_UNSET) {
        const bool is_angle_sharp = (check_angle &&
                                     dot_v3v3(poly_normals[loop_to_poly_map[e2l[0]]],
                                              poly_normals[poly_i]) < split_angle_cos);

        /* Second loop using this edge, time to test its sharpness.
         * An edge is sharp if it is tagged as such, or its face is not smooth,
         * or both poly have opposed (flipped) normals, i.e. both loops on the same edge share the
         * same vertex, or angle between both its polys' normals is above split_angle value.
         */
        if (!poly_is_smooth(poly_i) || (!sharp_edges.is_empty() && sharp_edges[edge_i]) ||
            vert_i == corner_verts[e2l[0]] || is_angle_sharp) {
          /* NOTE: we are sure that loop != 0 here ;). */
          e2l[1] = INDEX_INVALID;

          /* We want to avoid tagging edges as sharp when it is already defined as such by
           * other causes than angle threshold. */
          if (!r_sharp_edges.is_empty() && is_angle_sharp) {
            r_sharp_edges[edge_i] = true;
          }
        }
        else {
          e2l[1] = loop_index;
        }
      }
      else if (!IS_EDGE_SHARP(e2l)) {
        /* More than two loops using this edge, tag as sharp if not yet done. */
        e2l[1] = INDEX_INVALID;

        /* We want to avoid tagging edges as sharp when it is already defined as such by
         * other causes than angle threshold. */
        if (!r_sharp_edges.is_empty()) {
          r_sharp_edges[edge_i] = false;
        }
      }
      /* Else, edge is already 'disqualified' (i.e. sharp)! */
    }
  }
}

void edges_sharp_from_angle_set(const Span<MPoly> polys,
                                const Span<int> corner_verts,
                                const Span<int> corner_edges,
                                const Span<float3> poly_normals,
                                const bool *sharp_faces,
                                const float split_angle,
                                MutableSpan<bool> sharp_edges)
{
  if (split_angle >= float(M_PI)) {
    /* Nothing to do! */
    return;
  }

  /* Mapping edge -> loops. See #bke::mesh::normals_calc_loop for details. */
  Array<int2> edge_to_loops(sharp_edges.size(), int2(0));

  /* Simple mapping from a loop to its polygon index. */
  const Array<int> loop_to_poly = mesh_topology::build_loop_to_poly_map(polys,
                                                                        corner_verts.size());

  mesh_edges_sharp_tag(polys,
                       corner_verts,
                       corner_edges,
                       loop_to_poly,
                       poly_normals,
                       Span<bool>(sharp_faces, sharp_faces ? polys.size() : 0),
                       sharp_edges,
                       true,
                       split_angle,
                       edge_to_loops,
                       sharp_edges);
}

static void loop_manifold_fan_around_vert_next(const Span<int> corner_verts,
                                               const Span<MPoly> polys,
                                               const Span<int> loop_to_poly,
                                               const int *e2lfan_curr,
                                               const uint mv_pivot_index,
                                               int *r_mlfan_curr_index,
                                               int *r_mlfan_vert_index,
                                               int *r_mpfan_curr_index)
{
  const int mlfan_curr_orig = *r_mlfan_curr_index;
  const uint vert_fan_orig = corner_verts[mlfan_curr_orig];

  /* WARNING: This is rather complex!
   * We have to find our next edge around the vertex (fan mode).
   * First we find the next loop, which is either previous or next to mlfan_curr_index, depending
   * whether both loops using current edge are in the same direction or not, and whether
   * mlfan_curr_index actually uses the vertex we are fanning around!
   * mlfan_curr_index is the index of mlfan_next here, and mlfan_next is not the real next one
   * (i.e. not the future `mlfan_curr`). */
  *r_mlfan_curr_index = (e2lfan_curr[0] == *r_mlfan_curr_index) ? e2lfan_curr[1] : e2lfan_curr[0];
  *r_mpfan_curr_index = loop_to_poly[*r_mlfan_curr_index];

  BLI_assert(*r_mlfan_curr_index >= 0);
  BLI_assert(*r_mpfan_curr_index >= 0);

  const uint vert_fan_next = corner_verts[*r_mlfan_curr_index];
  const MPoly &mpfan_next = polys[*r_mpfan_curr_index];
  if ((vert_fan_orig == vert_fan_next && vert_fan_orig == mv_pivot_index) ||
      !ELEM(vert_fan_orig, vert_fan_next, mv_pivot_index)) {
    /* We need the previous loop, but current one is our vertex's loop. */
    *r_mlfan_vert_index = *r_mlfan_curr_index;
    if (--(*r_mlfan_curr_index) < mpfan_next.loopstart) {
      *r_mlfan_curr_index = mpfan_next.loopstart + mpfan_next.totloop - 1;
    }
  }
  else {
    /* We need the next loop, which is also our vertex's loop. */
    if (++(*r_mlfan_curr_index) >= mpfan_next.loopstart + mpfan_next.totloop) {
      *r_mlfan_curr_index = mpfan_next.loopstart;
    }
    *r_mlfan_vert_index = *r_mlfan_curr_index;
  }
}

static void split_loop_nor_single_do(LoopSplitTaskDataCommon *common_data, LoopSplitTaskData *data)
{
  MLoopNorSpaceArray *lnors_spacearr = common_data->lnors_spacearr;
  const Span<short2> clnors_data = common_data->clnors_data;

  const Span<float3> positions = common_data->positions;
  const Span<MEdge> edges = common_data->edges;
  const Span<int> corner_verts = common_data->corner_verts;
  const Span<int> corner_edges = common_data->corner_edges;
  const Span<float3> poly_normals = common_data->poly_normals;
  MutableSpan<float3> loop_normals = common_data->loop_normals;

  MLoopNorSpace *lnor_space = data->lnor_space;
  const int ml_curr_index = data->ml_curr_index;
  const int ml_prev_index = data->ml_prev_index;
  const int poly_index = data->poly_index;

  /* Simple case (both edges around that vertex are sharp in current polygon),
   * this loop just takes its poly normal.
   */
  loop_normals[ml_curr_index] = poly_normals[poly_index];

#if 0
  printf("BASIC: handling loop %d / edge %d / vert %d / poly %d\n",
         ml_curr_index,
         loops[ml_curr_index].e,
         loops[ml_curr_index].v,
         poly_index);
#endif

  /* If needed, generate this (simple!) lnor space. */
  if (lnors_spacearr) {
    float vec_curr[3], vec_prev[3];

    const uint mv_pivot_index =
        corner_verts[ml_curr_index]; /* The vertex we are "fanning" around! */
    const MEdge *me_curr = &edges[corner_edges[ml_curr_index]];
    const int vert_2 = me_curr->v1 == mv_pivot_index ? me_curr->v2 : me_curr->v1;
    const MEdge *me_prev = &edges[corner_edges[ml_prev_index]];
    const int vert_3 = me_prev->v1 == mv_pivot_index ? me_prev->v2 : me_prev->v1;

    sub_v3_v3v3(vec_curr, positions[vert_2], positions[mv_pivot_index]);
    normalize_v3(vec_curr);
    sub_v3_v3v3(vec_prev, positions[vert_3], positions[mv_pivot_index]);
    normalize_v3(vec_prev);

    BKE_lnor_space_define(lnor_space, loop_normals[ml_curr_index], vec_curr, vec_prev, nullptr);
    /* We know there is only one loop in this space, no need to create a link-list in this case. */
    BKE_lnor_space_add_loop(lnors_spacearr, lnor_space, ml_curr_index, nullptr, true);

    if (!clnors_data.is_empty()) {
      BKE_lnor_space_custom_data_to_normal(
          lnor_space, clnors_data[ml_curr_index], loop_normals[ml_curr_index]);
    }
  }
}

static void split_loop_nor_fan_do(LoopSplitTaskDataCommon *common_data,
                                  LoopSplitTaskData *data,
                                  BLI_Stack *edge_vectors)
{
  MLoopNorSpaceArray *lnors_spacearr = common_data->lnors_spacearr;
  MutableSpan<float3> loop_normals = common_data->loop_normals;
  MutableSpan<short2> clnors_data = common_data->clnors_data;

  const Span<float3> positions = common_data->positions;
  const Span<MEdge> edges = common_data->edges;
  const Span<MPoly> polys = common_data->polys;
  const Span<int> corner_verts = common_data->corner_verts;
  const Span<int> corner_edges = common_data->corner_edges;
  const Span<int2> edge_to_loops = common_data->edge_to_loops;
  const Span<int> loop_to_poly = common_data->loop_to_poly;
  const Span<float3> poly_normals = common_data->poly_normals;

  MLoopNorSpace *lnor_space = data->lnor_space;
#if 0 /* Not needed for 'fan' loops. */
  float(*lnor)[3] = data->lnor;
#endif
  const int ml_curr_index = data->ml_curr_index;
  const int ml_prev_index = data->ml_prev_index;
  const int poly_index = data->poly_index;

  /* Sigh! we have to fan around current vertex, until we find the other non-smooth edge,
   * and accumulate face normals into the vertex!
   * Note in case this vertex has only one sharp edges, this is a waste because the normal is the
   * same as the vertex normal, but I do not see any easy way to detect that (would need to count
   * number of sharp edges per vertex, I doubt the additional memory usage would be worth it,
   * especially as it should not be a common case in real-life meshes anyway). */
  const int mv_pivot_index = corner_verts[ml_curr_index]; /* The vertex we are "fanning" around! */

  /* `ml_curr_index` would be mlfan_prev if we needed that one. */
  const MEdge *me_org = &edges[corner_edges[ml_curr_index]];

  float vec_curr[3], vec_prev[3], vec_org[3];
  float lnor[3] = {0.0f, 0.0f, 0.0f};

  /* We validate clnors data on the fly - cheapest way to do! */
  int clnors_avg[2] = {0, 0};
  short2 *clnor_ref = nullptr;
  int clnors_count = 0;
  bool clnors_invalid = false;

  /* Temp loop normal stack. */
  BLI_SMALLSTACK_DECLARE(normal, float *);
  /* Temp clnors stack. */
  BLI_SMALLSTACK_DECLARE(clnors, short *);

  /* `mlfan_vert_index` the loop of our current edge might not be the loop of our current vertex!
   */
  int mlfan_curr_index = ml_prev_index;
  int mlfan_vert_index = ml_curr_index;
  int mpfan_curr_index = poly_index;

  BLI_assert(mlfan_curr_index >= 0);
  BLI_assert(mlfan_vert_index >= 0);
  BLI_assert(mpfan_curr_index >= 0);

  /* Only need to compute previous edge's vector once, then we can just reuse old current one! */
  {
    const float3 &mv_2 = (me_org->v1 == mv_pivot_index) ? positions[me_org->v2] :
                                                          positions[me_org->v1];

    sub_v3_v3v3(vec_org, mv_2, positions[mv_pivot_index]);
    normalize_v3(vec_org);
    copy_v3_v3(vec_prev, vec_org);

    if (lnors_spacearr) {
      BLI_stack_push(edge_vectors, vec_org);
    }
  }

  // printf("FAN: vert %d, start edge %d\n", mv_pivot_index, ml_curr->e);

  while (true) {
    const MEdge *me_curr = &edges[corner_edges[mlfan_curr_index]];
    /* Compute edge vectors.
     * NOTE: We could pre-compute those into an array, in the first iteration, instead of computing
     *       them twice (or more) here. However, time gained is not worth memory and time lost,
     *       given the fact that this code should not be called that much in real-life meshes.
     */
    {
      const float3 &mv_2 = (me_curr->v1 == mv_pivot_index) ? positions[me_curr->v2] :
                                                             positions[me_curr->v1];

      sub_v3_v3v3(vec_curr, mv_2, positions[mv_pivot_index]);
      normalize_v3(vec_curr);
    }

    // printf("\thandling edge %d / loop %d\n", corner_edges[mlfan_curr_index], mlfan_curr_index);

    {
      /* Code similar to accumulate_vertex_normals_poly_v3. */
      /* Calculate angle between the two poly edges incident on this vertex. */
      const float fac = saacos(dot_v3v3(vec_curr, vec_prev));
      /* Accumulate */
      madd_v3_v3fl(lnor, poly_normals[mpfan_curr_index], fac);

      if (!clnors_data.is_empty()) {
        /* Accumulate all clnors, if they are not all equal we have to fix that! */
        short2 *clnor = &clnors_data[mlfan_vert_index];
        if (clnors_count) {
          clnors_invalid |= ((*clnor_ref)[0] != (*clnor)[0] || (*clnor_ref)[1] != (*clnor)[1]);
        }
        else {
          clnor_ref = clnor;
        }
        clnors_avg[0] += (*clnor)[0];
        clnors_avg[1] += (*clnor)[1];
        clnors_count++;
        /* We store here a pointer to all custom loop_normals processed. */
        BLI_SMALLSTACK_PUSH(clnors, (short *)*clnor);
      }
    }

    /* We store here a pointer to all loop-normals processed. */
    BLI_SMALLSTACK_PUSH(normal, (float *)(loop_normals[mlfan_vert_index]));

    if (lnors_spacearr) {
      /* Assign current lnor space to current 'vertex' loop. */
      BKE_lnor_space_add_loop(lnors_spacearr, lnor_space, mlfan_vert_index, nullptr, false);
      if (me_curr != me_org) {
        /* We store here all edges-normalized vectors processed. */
        BLI_stack_push(edge_vectors, vec_curr);
      }
    }

    if (IS_EDGE_SHARP(edge_to_loops[corner_edges[mlfan_curr_index]]) || (me_curr == me_org)) {
      /* Current edge is sharp and we have finished with this fan of faces around this vert,
       * or this vert is smooth, and we have completed a full turn around it. */
      // printf("FAN: Finished!\n");
      break;
    }

    copy_v3_v3(vec_prev, vec_curr);

    /* Find next loop of the smooth fan. */
    loop_manifold_fan_around_vert_next(corner_verts,
                                       polys,
                                       loop_to_poly,
                                       edge_to_loops[corner_edges[mlfan_curr_index]],
                                       mv_pivot_index,
                                       &mlfan_curr_index,
                                       &mlfan_vert_index,
                                       &mpfan_curr_index);
  }

  {
    float lnor_len = normalize_v3(lnor);

    /* If we are generating lnor spacearr, we can now define the one for this fan,
     * and optionally compute final lnor from custom data too!
     */
    if (lnors_spacearr) {
      if (UNLIKELY(lnor_len == 0.0f)) {
        /* Use vertex normal as fallback! */
        copy_v3_v3(lnor, loop_normals[mlfan_vert_index]);
        lnor_len = 1.0f;
      }

      BKE_lnor_space_define(lnor_space, lnor, vec_org, vec_curr, edge_vectors);

      if (!clnors_data.is_empty()) {
        if (clnors_invalid) {
          short *clnor;

          clnors_avg[0] /= clnors_count;
          clnors_avg[1] /= clnors_count;
          /* Fix/update all clnors of this fan with computed average value. */
          if (G.debug & G_DEBUG) {
            printf("Invalid clnors in this fan!\n");
          }
          while ((clnor = (short *)BLI_SMALLSTACK_POP(clnors))) {
            // print_v2("org clnor", clnor);
            clnor[0] = short(clnors_avg[0]);
            clnor[1] = short(clnors_avg[1]);
          }
          // print_v2("new clnors", clnors_avg);
        }
        /* Extra bonus: since small-stack is local to this function,
         * no more need to empty it at all cost! */

        BKE_lnor_space_custom_data_to_normal(lnor_space, *clnor_ref, lnor);
      }
    }

    /* In case we get a zero normal here, just use vertex normal already set! */
    if (LIKELY(lnor_len != 0.0f)) {
      /* Copy back the final computed normal into all related loop-normals. */
      float *nor;

      while ((nor = (float *)BLI_SMALLSTACK_POP(normal))) {
        copy_v3_v3(nor, lnor);
      }
    }
    /* Extra bonus: since small-stack is local to this function,
     * no more need to empty it at all cost! */
  }
}

static void loop_split_worker_do(LoopSplitTaskDataCommon *common_data,
                                 LoopSplitTaskData *data,
                                 BLI_Stack *edge_vectors)
{
  if (data->flag == LoopSplitTaskData::Type::Fan) {
    BLI_assert((edge_vectors == nullptr) || BLI_stack_is_empty(edge_vectors));
    split_loop_nor_fan_do(common_data, data, edge_vectors);
  }
  else {
    /* No need for edge_vectors for 'single' case! */
    split_loop_nor_single_do(common_data, data);
  }
}

static void loop_split_worker(TaskPool *__restrict pool, void *taskdata)
{
  LoopSplitTaskDataCommon *common_data = (LoopSplitTaskDataCommon *)BLI_task_pool_user_data(pool);
  LoopSplitTaskData *data = (LoopSplitTaskData *)taskdata;

  /* Temp edge vectors stack, only used when computing lnor spacearr. */
  BLI_Stack *edge_vectors = common_data->lnors_spacearr ?
                                BLI_stack_new(sizeof(float[3]), __func__) :
                                nullptr;

  for (int i = 0; i < LOOP_SPLIT_TASK_BLOCK_SIZE; i++, data++) {
    if (data->flag == LoopSplitTaskData::Type::BlockEnd) {
      break;
    }
    loop_split_worker_do(common_data, data, edge_vectors);
  }

  if (edge_vectors) {
    BLI_stack_free(edge_vectors);
  }
}

/**
 * Check whether given loop is part of an unknown-so-far cyclic smooth fan, or not.
 * Needed because cyclic smooth fans have no obvious 'entry point',
 * and yet we need to walk them once, and only once.
 */
static bool loop_split_generator_check_cyclic_smooth_fan(const Span<int> corner_verts,
                                                         const Span<int> corner_edges,
                                                         const Span<MPoly> polys,
                                                         const Span<int2> edge_to_loops,
                                                         const Span<int> loop_to_poly,
                                                         const int *e2l_prev,
                                                         MutableBitSpan skip_loops,
                                                         const int ml_curr_index,
                                                         const int ml_prev_index,
                                                         const int mp_curr_index)
{
  /* The vertex we are "fanning" around! */
  const uint mv_pivot_index = corner_verts[ml_curr_index];

  const int *e2lfan_curr = e2l_prev;
  if (IS_EDGE_SHARP(e2lfan_curr)) {
    /* Sharp loop, so not a cyclic smooth fan. */
    return false;
  }

  /* `mlfan_vert_index` the loop of our current edge might not be the loop of our current vertex!
   */
  int mlfan_curr_index = ml_prev_index;
  int mlfan_vert_index = ml_curr_index;
  int mpfan_curr_index = mp_curr_index;

  BLI_assert(mlfan_curr_index >= 0);
  BLI_assert(mlfan_vert_index >= 0);
  BLI_assert(mpfan_curr_index >= 0);

  BLI_assert(!skip_loops[mlfan_vert_index]);
  skip_loops[mlfan_vert_index].set();

  while (true) {
    /* Find next loop of the smooth fan. */
    loop_manifold_fan_around_vert_next(corner_verts,
                                       polys,
                                       loop_to_poly,
                                       e2lfan_curr,
                                       mv_pivot_index,
                                       &mlfan_curr_index,
                                       &mlfan_vert_index,
                                       &mpfan_curr_index);

    e2lfan_curr = edge_to_loops[corner_edges[mlfan_curr_index]];

    if (IS_EDGE_SHARP(e2lfan_curr)) {
      /* Sharp loop/edge, so not a cyclic smooth fan. */
      return false;
    }
    /* Smooth loop/edge. */
    if (skip_loops[mlfan_vert_index]) {
      if (mlfan_vert_index == ml_curr_index) {
        /* We walked around a whole cyclic smooth fan without finding any already-processed loop,
         * means we can use initial current / previous edge as start for this smooth fan. */
        return true;
      }
      /* Already checked in some previous looping, we can abort. */
      return false;
    }

    /* We can skip it in future, and keep checking the smooth fan. */
    skip_loops[mlfan_vert_index].set();
  }
}

static void loop_split_generator(TaskPool *pool, LoopSplitTaskDataCommon *common_data)
{
  MLoopNorSpaceArray *lnors_spacearr = common_data->lnors_spacearr;

  const Span<int> corner_verts = common_data->corner_verts;
  const Span<int> corner_edges = common_data->corner_edges;
  const Span<MPoly> polys = common_data->polys;
  const Span<int> loop_to_poly = common_data->loop_to_poly;
  const Span<int2> edge_to_loops = common_data->edge_to_loops;

  BitVector<> skip_loops(corner_verts.size(), false);

  LoopSplitTaskData *data_buff = nullptr;
  int data_idx = 0;

  /* Temp edge vectors stack, only used when computing lnor spacearr
   * (and we are not multi-threading). */
  BLI_Stack *edge_vectors = nullptr;

#ifdef DEBUG_TIME
  SCOPED_TIMER_AVERAGED(__func__);
#endif

  if (!pool) {
    if (lnors_spacearr) {
      edge_vectors = BLI_stack_new(sizeof(float[3]), __func__);
    }
  }

  /* We now know edges that can be smoothed (with their vector, and their two loops),
   * and edges that will be hard! Now, time to generate the normals.
   */
  for (const int poly_index : polys.index_range()) {
    const MPoly &poly = polys[poly_index];

    for (const int ml_curr_index : IndexRange(poly.loopstart, poly.totloop)) {
      const int ml_prev_index = mesh_topology::poly_loop_prev(poly, ml_curr_index);

#if 0
      printf("Checking loop %d / edge %u / vert %u (sharp edge: %d, skiploop: %d)",
             ml_curr_index,
             corner_edges[ml_curr_index],
             corner_verts[ml_curr_index],
             IS_EDGE_SHARP(edge_to_loops[corner_edges[ml_curr_index]]),
             skip_loops[ml_curr_index]);
#endif

      /* A smooth edge, we have to check for cyclic smooth fan case.
       * If we find a new, never-processed cyclic smooth fan, we can do it now using that loop/edge
       * as 'entry point', otherwise we can skip it. */

      /* NOTE: In theory, we could make #loop_split_generator_check_cyclic_smooth_fan() store
       * mlfan_vert_index'es and edge indexes in two stacks, to avoid having to fan again around
       * the vert during actual computation of `clnor` & `clnorspace`.
       * However, this would complicate the code, add more memory usage, and despite its logical
       * complexity, #loop_manifold_fan_around_vert_next() is quite cheap in term of CPU cycles,
       * so really think it's not worth it. */
      if (!IS_EDGE_SHARP(edge_to_loops[corner_edges[ml_curr_index]]) &&
          (skip_loops[ml_curr_index] || !loop_split_generator_check_cyclic_smooth_fan(
                                            corner_verts,
                                            corner_edges,
                                            polys,
                                            edge_to_loops,
                                            loop_to_poly,
                                            edge_to_loops[corner_edges[ml_prev_index]],
                                            skip_loops,
                                            ml_curr_index,
                                            ml_prev_index,
                                            poly_index))) {
        // printf("SKIPPING!\n");
      }
      else {
        LoopSplitTaskData *data, data_local;

        // printf("PROCESSING!\n");

        if (pool) {
          if (data_idx == 0) {
            data_buff = (LoopSplitTaskData *)MEM_calloc_arrayN(
                LOOP_SPLIT_TASK_BLOCK_SIZE, sizeof(*data_buff), __func__);
          }
          data = &data_buff[data_idx];
        }
        else {
          data = &data_local;
          memset(data, 0, sizeof(*data));
        }

        if (IS_EDGE_SHARP(edge_to_loops[corner_edges[ml_curr_index]]) &&
            IS_EDGE_SHARP(edge_to_loops[corner_edges[ml_prev_index]])) {
          data->ml_curr_index = ml_curr_index;
          data->ml_prev_index = ml_prev_index;
          data->flag = LoopSplitTaskData::Type::Single;
          data->poly_index = poly_index;
          if (lnors_spacearr) {
            data->lnor_space = BKE_lnor_space_create(lnors_spacearr);
          }
        }
        else {
          /* We do not need to check/tag loops as already computed. Due to the fact that a loop
           * only points to one of its two edges, the same fan will never be walked more than once.
           * Since we consider edges that have neighbor polys with inverted (flipped) normals as
           * sharp, we are sure that no fan will be skipped, even only considering the case (sharp
           * current edge, smooth previous edge), and not the alternative (smooth current edge,
           * sharp previous edge). All this due/thanks to the link between normals and loop
           * ordering (i.e. winding). */
          data->ml_curr_index = ml_curr_index;
          data->ml_prev_index = ml_prev_index;
          data->flag = LoopSplitTaskData::Type::Fan;
          data->poly_index = poly_index;
          if (lnors_spacearr) {
            data->lnor_space = BKE_lnor_space_create(lnors_spacearr);
          }
        }

        if (pool) {
          data_idx++;
          if (data_idx == LOOP_SPLIT_TASK_BLOCK_SIZE) {
            BLI_task_pool_push(pool, loop_split_worker, data_buff, true, nullptr);
            data_idx = 0;
          }
        }
        else {
          loop_split_worker_do(common_data, data, edge_vectors);
        }
      }
    }
  }

  if (pool && data_idx) {
    BLI_task_pool_push(pool, loop_split_worker, data_buff, true, nullptr);
  }

  if (edge_vectors) {
    BLI_stack_free(edge_vectors);
  }
}

void normals_calc_loop(const Span<float3> vert_positions,
                       const Span<MEdge> edges,
                       const Span<MPoly> polys,
                       const Span<int> corner_verts,
                       const Span<int> corner_edges,
                       const Span<int> loop_to_poly_map,
                       const Span<float3> vert_normals,
                       const Span<float3> poly_normals,
                       const bool *sharp_edges,
                       const bool *sharp_faces,
                       bool use_split_normals,
                       float split_angle,
                       short (*clnors_data)[2],
                       MLoopNorSpaceArray *r_lnors_spacearr,
                       MutableSpan<float3> r_loop_normals)
{
  /* For now this is not supported.
   * If we do not use split normals, we do not generate anything fancy! */
  BLI_assert(use_split_normals || !(r_lnors_spacearr));

  if (!use_split_normals) {
    /* In this case, simply fill `r_loop_normals` with `vert_normals`
     * (or `poly_normals` for flat faces), quite simple!
     * Note this is done here to keep some logic and consistency in this quite complex code,
     * since we may want to use loop_normals even when mesh's 'autosmooth' is disabled
     * (see e.g. mesh mapping code). As usual, we could handle that on case-by-case basis,
     * but simpler to keep it well confined here. */
    for (const int poly_index : polys.index_range()) {
      const MPoly *poly = &polys[poly_index];
      int ml_index = poly->loopstart;
      const int ml_index_end = ml_index + poly->totloop;
      const bool is_poly_flat = sharp_faces && sharp_faces[poly_index];

      for (; ml_index < ml_index_end; ml_index++) {
        if (is_poly_flat) {
          copy_v3_v3(r_loop_normals[ml_index], poly_normals[poly_index]);
        }
        else {
          copy_v3_v3(r_loop_normals[ml_index], vert_normals[corner_verts[ml_index]]);
        }
      }
    }
    return;
  }

  /**
   * Mapping edge -> loops.
   * If that edge is used by more than two loops (polys),
   * it is always sharp (and tagged as such, see below).
   * We also use the second loop index as a kind of flag:
   *
   * - smooth edge: > 0.
   * - sharp edge: < 0 (INDEX_INVALID || INDEX_UNSET).
   * - unset: INDEX_UNSET.
   *
   * Note that currently we only have two values for second loop of sharp edges.
   * However, if needed, we can store the negated value of loop index instead of INDEX_INVALID
   * to retrieve the real value later in code).
   * Note also that loose edges always have both values set to 0! */
  Array<int2> edge_to_loops(edges.size(), int2(0));

  /* Simple mapping from a loop to its polygon index. */
  Span<int> loop_to_poly;
  Array<int> local_loop_to_poly_map;
  if (loop_to_poly_map.is_empty()) {
    local_loop_to_poly_map = mesh_topology::build_loop_to_poly_map(polys, corner_verts.size());
    loop_to_poly = local_loop_to_poly_map;
  }
  else {
    loop_to_poly = loop_to_poly_map;
  }

  /* When using custom loop normals, disable the angle feature! */
  const bool check_angle = (split_angle < float(M_PI)) && (clnors_data == nullptr);

  MLoopNorSpaceArray _lnors_spacearr = {nullptr};

#ifdef DEBUG_TIME
  SCOPED_TIMER_AVERAGED(__func__);
#endif

  if (!r_lnors_spacearr && clnors_data) {
    /* We need to compute lnor spacearr if some custom lnor data are given to us! */
    r_lnors_spacearr = &_lnors_spacearr;
  }
  if (r_lnors_spacearr) {
    BKE_lnor_spacearr_init(r_lnors_spacearr, corner_verts.size(), MLNOR_SPACEARR_LOOP_INDEX);
  }

  /* Init data common to all tasks. */
  LoopSplitTaskDataCommon common_data;
  common_data.lnors_spacearr = r_lnors_spacearr;
  common_data.loop_normals = r_loop_normals;
  common_data.clnors_data = {reinterpret_cast<short2 *>(clnors_data),
                             clnors_data ? corner_verts.size() : 0};
  common_data.positions = vert_positions;
  common_data.edges = edges;
  common_data.polys = polys;
  common_data.corner_verts = corner_verts;
  common_data.corner_edges = corner_edges;
  common_data.edge_to_loops = edge_to_loops;
  common_data.loop_to_poly = loop_to_poly;
  common_data.poly_normals = poly_normals;
  common_data.vert_normals = vert_normals;

  /* Pre-populate all loop normals as if their verts were all smooth.
   * This way we don't have to compute those later! */
  threading::parallel_for(polys.index_range(), 1024, [&](const IndexRange range) {
    for (const int poly_i : range) {
      const MPoly &poly = polys[poly_i];
      for (const int loop_i : IndexRange(poly.loopstart, poly.totloop)) {
        copy_v3_v3(r_loop_normals[loop_i], vert_normals[corner_verts[loop_i]]);
      }
    }
  });

  /* This first loop check which edges are actually smooth, and compute edge vectors. */
  mesh_edges_sharp_tag(polys,
                       corner_verts,
                       corner_edges,
                       loop_to_poly,
                       poly_normals,
                       Span<bool>(sharp_faces, sharp_faces ? polys.size() : 0),
                       Span<bool>(sharp_edges, sharp_edges ? edges.size() : 0),
                       check_angle,
                       split_angle,
                       edge_to_loops,
                       {});

  if (corner_verts.size() < LOOP_SPLIT_TASK_BLOCK_SIZE * 8) {
    /* Not enough loops to be worth the whole threading overhead. */
    loop_split_generator(nullptr, &common_data);
  }
  else {
    TaskPool *task_pool = BLI_task_pool_create(&common_data, TASK_PRIORITY_HIGH);

    loop_split_generator(task_pool, &common_data);

    BLI_task_pool_work_and_wait(task_pool);

    BLI_task_pool_free(task_pool);
  }

  if (r_lnors_spacearr) {
    if (r_lnors_spacearr == &_lnors_spacearr) {
      BKE_lnor_spacearr_free(r_lnors_spacearr);
    }
  }
}

#undef INDEX_UNSET
#undef INDEX_INVALID
#undef IS_EDGE_SHARP

/**
 * Compute internal representation of given custom normals (as an array of float[2]).
 * It also makes sure the mesh matches those custom normals, by setting sharp edges flag as needed
 * to get a same custom lnor for all loops sharing a same smooth fan.
 * If use_vertices if true, r_custom_loop_normals is assumed to be per-vertex, not per-loop
 * (this allows to set whole vert's normals at once, useful in some cases).
 * r_custom_loop_normals is expected to have normalized normals, or zero ones,
 * in which case they will be replaced by default loop/vertex normal.
 */

static void mesh_normals_loop_custom_set(Span<float3> positions,
                                         Span<MEdge> edges,
                                         Span<MPoly> polys,
                                         Span<int> corner_verts,
                                         Span<int> corner_edges,
                                         Span<float3> vert_normals,
                                         Span<float3> poly_normals,
                                         const bool *sharp_faces,
                                         const bool use_vertices,
                                         MutableSpan<float3> r_custom_loop_normals,
                                         MutableSpan<bool> sharp_edges,
                                         short (*r_clnors_data)[2])
{
  /* We *may* make that poor #bke::mesh::normals_calc_loop() even more complex by making it
   * handling that feature too, would probably be more efficient in absolute. However, this
   * function *is not* performance-critical, since it is mostly expected to be called by io add-ons
   * when importing custom normals, and modifier (and perhaps from some editing tools later?). So
   * better to keep some simplicity here, and just call #bke::mesh::normals_calc_loop() twice! */
  MLoopNorSpaceArray lnors_spacearr = {nullptr};
  BitVector<> done_loops(corner_verts.size(), false);
  Array<float3> loop_normals(corner_verts.size());
  const Array<int> loop_to_poly = mesh_topology::build_loop_to_poly_map(polys,
                                                                        corner_verts.size());
  /* In this case we always consider split nors as ON,
   * and do not want to use angle to define smooth fans! */
  const bool use_split_normals = true;
  const float split_angle = float(M_PI);

  BLI_SMALLSTACK_DECLARE(clnors_data, short *);

  /* Compute current lnor spacearr. */
  normals_calc_loop(positions,
                    edges,
                    polys,
                    corner_verts,
                    corner_edges,
                    loop_to_poly,
                    vert_normals,
                    poly_normals,
                    sharp_edges.data(),
                    sharp_faces,
                    use_split_normals,
                    split_angle,
                    r_clnors_data,
                    &lnors_spacearr,
                    loop_normals);

  /* Set all given zero vectors to their default value. */
  if (use_vertices) {
    for (const int i : positions.index_range()) {
      if (is_zero_v3(r_custom_loop_normals[i])) {
        copy_v3_v3(r_custom_loop_normals[i], vert_normals[i]);
      }
    }
  }
  else {
    for (const int i : corner_verts.index_range()) {
      if (is_zero_v3(r_custom_loop_normals[i])) {
        copy_v3_v3(r_custom_loop_normals[i], loop_normals[i]);
      }
    }
  }

  BLI_assert(lnors_spacearr.data_type == MLNOR_SPACEARR_LOOP_INDEX);

  /* Now, check each current smooth fan (one lnor space per smooth fan!),
   * and if all its matching custom loop_normals are not (enough) equal, add sharp edges as needed.
   * This way, next time we run bke::mesh::normals_calc_loop(), we'll get lnor spacearr/smooth fans
   * matching given custom loop_normals.
   * Note this code *will never* unsharp edges! And quite obviously,
   * when we set custom normals per vertices, running this is absolutely useless. */
  if (use_vertices) {
    done_loops.fill(true);
  }
  else {
    for (const int i : corner_verts.index_range()) {
      if (!lnors_spacearr.lspacearr[i]) {
        /* This should not happen in theory, but in some rare case (probably ugly geometry)
         * we can get some nullptr loopspacearr at this point. :/
         * Maybe we should set those loops' edges as sharp? */
        done_loops[i].set();
        if (G.debug & G_DEBUG) {
          printf("WARNING! Getting invalid nullptr loop space for loop %d!\n", i);
        }
        continue;
      }
      if (done_loops[i]) {
        continue;
      }

      /* Notes:
       * - In case of mono-loop smooth fan, we have nothing to do.
       * - Loops in this linklist are ordered (in reversed order compared to how they were
       *   discovered by bke::mesh::normals_calc_loop(), but this is not a problem).
       *   Which means if we find a mismatching clnor,
       *   we know all remaining loops will have to be in a new, different smooth fan/lnor space.
       * - In smooth fan case, we compare each clnor against a ref one,
       *   to avoid small differences adding up into a real big one in the end!
       */
      if (lnors_spacearr.lspacearr[i]->flags & MLNOR_SPACE_IS_SINGLE) {
        done_loops[i].set();
        continue;
      }

      LinkNode *loop_link = lnors_spacearr.lspacearr[i]->loops;
      int prev_corner = -1;
      const float *org_nor = nullptr;

      while (loop_link) {
        const int lidx = POINTER_AS_INT(loop_link->link);
        float *nor = r_custom_loop_normals[lidx];

        if (!org_nor) {
          org_nor = nor;
        }
        else if (dot_v3v3(org_nor, nor) < LNOR_SPACE_TRIGO_THRESHOLD) {
          /* Current normal differs too much from org one, we have to tag the edge between
           * previous loop's face and current's one as sharp.
           * We know those two loops do not point to the same edge,
           * since we do not allow reversed winding in a same smooth fan. */
          const MPoly &poly = polys[loop_to_poly[lidx]];
          const int mlp = (lidx == poly.loopstart) ? poly.loopstart + poly.totloop - 1 : lidx - 1;
          const int edge = corner_edges[lidx];
          const int edge_p = corner_edges[mlp];
          const int prev_edge = corner_edges[prev_corner];
          sharp_edges[prev_edge == edge_p ? prev_edge : edge] = true;

          org_nor = nor;
        }

        prev_corner = lidx;
        loop_link = loop_link->next;
        done_loops[lidx].set();
      }

      /* We also have to check between last and first loops,
       * otherwise we may miss some sharp edges here!
       * This is just a simplified version of above while loop.
       * See #45984. */
      loop_link = lnors_spacearr.lspacearr[i]->loops;
      if (loop_link && org_nor) {
        const int lidx = POINTER_AS_INT(loop_link->link);
        float *nor = r_custom_loop_normals[lidx];

        if (dot_v3v3(org_nor, nor) < LNOR_SPACE_TRIGO_THRESHOLD) {
          const MPoly &poly = polys[loop_to_poly[lidx]];
          const int mlp = (lidx == poly.loopstart) ? poly.loopstart + poly.totloop - 1 : lidx - 1;
          const int edge = corner_edges[lidx];
          const int edge_p = corner_edges[mlp];
          const int prev_edge = corner_edges[prev_corner];
          sharp_edges[prev_edge == edge_p ? prev_edge : edge] = true;
        }
      }
    }

    /* And now, recompute our new auto `loop_normals` and lnor spacearr! */
    BKE_lnor_spacearr_clear(&lnors_spacearr);
    normals_calc_loop(positions,
                      edges,
                      polys,
                      corner_verts,
                      corner_edges,
                      loop_to_poly,
                      vert_normals,
                      poly_normals,
                      sharp_edges.data(),
                      sharp_faces,
                      use_split_normals,
                      split_angle,
                      r_clnors_data,
                      &lnors_spacearr,
                      loop_normals);
  }

  /* And we just have to convert plain object-space custom normals to our
   * lnor space-encoded ones. */
  for (const int i : corner_verts.index_range()) {
    if (!lnors_spacearr.lspacearr[i]) {
      done_loops[i].reset();
      if (G.debug & G_DEBUG) {
        printf("WARNING! Still getting invalid nullptr loop space in second loop for loop %d!\n",
               i);
      }
      continue;
    }

    if (done_loops[i]) {
      /* Note we accumulate and average all custom normals in current smooth fan,
       * to avoid getting different clnors data (tiny differences in plain custom normals can
       * give rather huge differences in computed 2D factors). */
      LinkNode *loop_link = lnors_spacearr.lspacearr[i]->loops;
      if (lnors_spacearr.lspacearr[i]->flags & MLNOR_SPACE_IS_SINGLE) {
        BLI_assert(POINTER_AS_INT(loop_link) == i);
        const int nidx = use_vertices ? corner_verts[i] : i;
        float *nor = r_custom_loop_normals[nidx];

        BKE_lnor_space_custom_normal_to_data(lnors_spacearr.lspacearr[i], nor, r_clnors_data[i]);
        done_loops[i].reset();
      }
      else {
        int avg_nor_count = 0;
        float avg_nor[3];
        short clnor_data_tmp[2], *clnor_data;

        zero_v3(avg_nor);
        while (loop_link) {
          const int lidx = POINTER_AS_INT(loop_link->link);
          const int nidx = use_vertices ? corner_verts[lidx] : lidx;
          float *nor = r_custom_loop_normals[nidx];

          avg_nor_count++;
          add_v3_v3(avg_nor, nor);
          BLI_SMALLSTACK_PUSH(clnors_data, (short *)r_clnors_data[lidx]);

          loop_link = loop_link->next;
          done_loops[lidx].reset();
        }

        mul_v3_fl(avg_nor, 1.0f / float(avg_nor_count));
        BKE_lnor_space_custom_normal_to_data(lnors_spacearr.lspacearr[i], avg_nor, clnor_data_tmp);

        while ((clnor_data = (short *)BLI_SMALLSTACK_POP(clnors_data))) {
          clnor_data[0] = clnor_data_tmp[0];
          clnor_data[1] = clnor_data_tmp[1];
        }
      }
    }
  }

  BKE_lnor_spacearr_free(&lnors_spacearr);
}

void normals_loop_custom_set(const Span<float3> vert_positions,
                             const Span<MEdge> edges,
                             const Span<MPoly> polys,
                             const Span<int> corner_verts,
                             const Span<int> corner_edges,
                             const Span<float3> vert_normals,
                             const Span<float3> poly_normals,
                             const bool *sharp_faces,
                             MutableSpan<bool> sharp_edges,
                             MutableSpan<float3> r_custom_loop_normals,
                             short (*r_clnors_data)[2])
{
  mesh_normals_loop_custom_set(vert_positions,
                               edges,
                               polys,
                               corner_verts,
                               corner_edges,
                               vert_normals,
                               poly_normals,
                               sharp_faces,
                               false,
                               r_custom_loop_normals,
                               sharp_edges,
                               r_clnors_data);
}

void normals_loop_custom_set_from_verts(const Span<float3> vert_positions,
                                        const Span<MEdge> edges,
                                        const Span<MPoly> polys,
                                        const Span<int> corner_verts,
                                        const Span<int> corner_edges,
                                        const Span<float3> vert_normals,
                                        const Span<float3> poly_normals,
                                        const bool *sharp_faces,
                                        MutableSpan<bool> sharp_edges,
                                        MutableSpan<float3> r_custom_vert_normals,
                                        short (*r_clnors_data)[2])
{
  mesh_normals_loop_custom_set(vert_positions,
                               edges,
                               polys,
                               corner_verts,
                               corner_edges,
                               vert_normals,
                               poly_normals,
                               sharp_faces,
                               true,
                               r_custom_vert_normals,
                               sharp_edges,
                               r_clnors_data);
}

static void mesh_set_custom_normals(Mesh *mesh, float (*r_custom_nors)[3], const bool use_vertices)
{
  short(*clnors)[2];
  const int numloops = mesh->totloop;

  clnors = (short(*)[2])CustomData_get_layer_for_write(
      &mesh->ldata, CD_CUSTOMLOOPNORMAL, mesh->totloop);
  if (clnors != nullptr) {
    memset(clnors, 0, sizeof(*clnors) * size_t(numloops));
  }
  else {
    clnors = (short(*)[2])CustomData_add_layer(
        &mesh->ldata, CD_CUSTOMLOOPNORMAL, CD_SET_DEFAULT, numloops);
  }
  MutableAttributeAccessor attributes = mesh->attributes_for_write();
  SpanAttributeWriter<bool> sharp_edges = attributes.lookup_or_add_for_write_span<bool>(
      "sharp_edge", ATTR_DOMAIN_EDGE);
  const bool *sharp_faces = static_cast<const bool *>(
      CustomData_get_layer_named(&mesh->pdata, CD_PROP_BOOL, "sharp_face"));

  mesh_normals_loop_custom_set(mesh->vert_positions(),
                               mesh->edges(),
                               mesh->polys(),
                               mesh->corner_verts(),
                               mesh->corner_edges(),
                               mesh->vert_normals(),
                               mesh->poly_normals(),
                               sharp_faces,
                               use_vertices,
                               {reinterpret_cast<blender::float3 *>(r_custom_nors),
                                use_vertices ? mesh->totvert : mesh->totloop},
                               sharp_edges.span,
                               clnors);

  sharp_edges.finish();
}

}  // namespace blender::bke::mesh

void BKE_mesh_set_custom_normals(Mesh *mesh, float (*r_custom_loop_normals)[3])
{
  blender::bke::mesh::mesh_set_custom_normals(mesh, r_custom_loop_normals, false);
}

void BKE_mesh_set_custom_normals_from_verts(Mesh *mesh, float (*r_custom_vert_normals)[3])
{
  blender::bke::mesh::mesh_set_custom_normals(mesh, r_custom_vert_normals, true);
}

void BKE_mesh_normals_loop_to_vertex(const int numVerts,
                                     const int *corner_verts,
                                     const int numLoops,
                                     const float (*clnors)[3],
                                     float (*r_vert_clnors)[3])
{
  int *vert_loops_count = (int *)MEM_calloc_arrayN(
      size_t(numVerts), sizeof(*vert_loops_count), __func__);

  copy_vn_fl((float *)r_vert_clnors, 3 * numVerts, 0.0f);

  int i;
  for (i = 0; i < numLoops; i++) {
    const int vert = corner_verts[i];
    add_v3_v3(r_vert_clnors[vert], clnors[i]);
    vert_loops_count[vert]++;
  }

  for (i = 0; i < numVerts; i++) {
    mul_v3_fl(r_vert_clnors[i], 1.0f / float(vert_loops_count[i]));
  }

  MEM_freeN(vert_loops_count);
}

#undef LNOR_SPACE_TRIGO_THRESHOLD

/** \} */

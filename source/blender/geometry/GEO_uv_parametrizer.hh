/* SPDX-License-Identifier: GPL-2.0-or-later */

#pragma once

#include "BLI_sys_types.h" /* for intptr_t support */

/** \file
 * \ingroup geo
 */

namespace blender::geometry {

struct ParamHandle;         /* Handle to an array of charts. */
using ParamKey = uintptr_t; /* Key (hash) for identifying verts and faces. */
#define PARAM_KEY_MAX UINTPTR_MAX

/* -------------------------------------------------------------------- */
/** \name Chart Construction:
 *
 * Faces and seams may only be added between #geometry::uv_parametrizer_construct_begin and
 * #geometry::uv_parametrizer_construct_end.
 *
 * The pointers to `co` and `uv` are stored, rather than being copied. Vertices are implicitly
 * created.
 *
 * In #geometry::uv_parametrizer_construct_end the mesh will be split up according to the seams.
 * The resulting charts must be manifold, connected and open (at least one boundary loop). The
 * output will be written to the `uv` pointers.
 *
 * \{ */

ParamHandle *uv_parametrizer_construct_begin();

void uv_parametrizer_aspect_ratio(ParamHandle *handle, float aspx, float aspy);

void uv_prepare_pin_index(ParamHandle *handle, const int bmvertindex, const float uv[2]);

ParamKey uv_find_pin_index(ParamHandle *handle, const int bmvertindex, const float uv[2]);

void uv_parametrizer_face_add(ParamHandle *handle,
                              const ParamKey key,
                              const int nverts,
                              const ParamKey *vkeys,
                              const float **co,
                              float **uv, /* Output will eventually be written to `uv`. */
                              const bool *pin,
                              const bool *select);

void uv_parametrizer_edge_set_seam(ParamHandle *handle, ParamKey *vkeys);

void uv_parametrizer_construct_end(ParamHandle *handle,
                                   bool fill_holes,
                                   bool topology_from_uvs,
                                   int *r_count_failed = nullptr);
void uv_parametrizer_delete(ParamHandle *handle);

/** \} */

/* -------------------------------------------------------------------- */
/** \name Least Squares Conformal Maps:
 *
 * Charts with less than two pinned vertices are assigned two pins. LSCM is divided to three steps:
 *
 * 1. Begin: compute matrix and its factorization (expensive).
 * 2. Solve using pinned coordinates (cheap).
 * 3. End: clean up.
 *
 * UV coordinates are allowed to change within begin/end, for quick re-solving.
 *
 * \{ */

void uv_parametrizer_lscm_begin(ParamHandle *handle, bool live, bool abf);
void uv_parametrizer_lscm_solve(ParamHandle *handle, int *count_changed, int *count_failed);
void uv_parametrizer_lscm_end(ParamHandle *handle);

/** \} */

/* -------------------------------------------------------------------- */
/** \name Stretch
 * \{ */

void uv_parametrizer_stretch_begin(ParamHandle *handle);
void uv_parametrizer_stretch_blend(ParamHandle *handle, float blend);
void uv_parametrizer_stretch_iter(ParamHandle *handle);
void uv_parametrizer_stretch_end(ParamHandle *handle);

/** \} */

/* -------------------------------------------------------------------- */
/** \name Packing
 * \{ */

void uv_parametrizer_pack(ParamHandle *handle, float margin, bool do_rotate, bool ignore_pinned);

/** \} */

/* -------------------------------------------------------------------- */
/** \name Average area for all charts
 * \{ */

void uv_parametrizer_average(ParamHandle *handle, bool ignore_pinned, bool scale_uv, bool shear);

/** \} */

/* -------------------------------------------------------------------- */
/** \name Simple x,y scale
 * \{ */

void uv_parametrizer_scale(ParamHandle *handle, float x, float y);

/** \} */

/* -------------------------------------------------------------------- */
/** \name Flushing
 * \{ */

void uv_parametrizer_flush(ParamHandle *handle);
void uv_parametrizer_flush_restore(ParamHandle *handle);

/** \} */

}  // namespace blender::geometry

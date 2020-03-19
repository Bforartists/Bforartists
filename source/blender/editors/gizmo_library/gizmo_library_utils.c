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
 * The Original Code is Copyright (C) 2015 Blender Foundation.
 * All rights reserved.
 */

/** \file
 * \ingroup edgizmolib
 *
 * \name Gizmo Library Utilities
 *
 * \brief This file contains functions for common behaviors of gizmos.
 */

#include "BLI_math.h"

#include "DNA_screen_types.h"
#include "DNA_view3d_types.h"

#include "BKE_context.h"

#include "RNA_access.h"

#include "WM_api.h"
#include "WM_types.h"

#include "ED_view3d.h"

/* own includes */
#include "gizmo_library_intern.h"

/* factor for precision tweaking */
#define GIZMO_PRECISION_FAC 0.05f

BLI_INLINE float gizmo_offset_from_value_constr(const float range_fac,
                                                const float min,
                                                const float range,
                                                const float value,
                                                const bool inverted)
{
  return inverted ? (range_fac * (min + range - value) / range) : (range_fac * (value / range));
}

BLI_INLINE float gizmo_value_from_offset_constr(const float range_fac,
                                                const float min,
                                                const float range,
                                                const float value,
                                                const bool inverted)
{
  return inverted ? (min + range - (value * range / range_fac)) : (value * range / range_fac);
}

float gizmo_offset_from_value(GizmoCommonData *data,
                              const float value,
                              const bool constrained,
                              const bool inverted)
{
  if (constrained) {
    return gizmo_offset_from_value_constr(
        data->range_fac, data->min, data->range, value, inverted);
  }

  return value;
}

float gizmo_value_from_offset(GizmoCommonData *data,
                              GizmoInteraction *inter,
                              const float offset,
                              const bool constrained,
                              const bool inverted,
                              const bool use_precision)
{
  const float max = data->min + data->range;

  if (use_precision) {
    /* add delta offset of this step to total precision_offset */
    inter->precision_offset += offset - inter->prev_offset;
  }
  inter->prev_offset = offset;

  float ofs_new = inter->init_offset + offset -
                  inter->precision_offset * (1.0f - GIZMO_PRECISION_FAC);
  float value;

  if (constrained) {
    value = gizmo_value_from_offset_constr(
        data->range_fac, data->min, data->range, ofs_new, inverted);
  }
  else {
    value = ofs_new;
  }

  /* clamp to custom range */
  if (data->is_custom_range_set) {
    CLAMP(value, data->min, max);
  }

  return value;
}

void gizmo_property_data_update(wmGizmo *gz,
                                GizmoCommonData *data,
                                wmGizmoProperty *gz_prop,
                                const bool constrained,
                                const bool inverted)
{
  if (gz_prop->custom_func.value_get_fn != NULL) {
    /* pass  */
  }
  else if (gz_prop->prop != NULL) {
    /* pass  */
  }
  else {
    data->offset = 0.0f;
    return;
  }

  float value = WM_gizmo_target_property_float_get(gz, gz_prop);

  if (constrained) {
    if (data->is_custom_range_set == false) {
      float range[2];
      if (WM_gizmo_target_property_float_range_get(gz, gz_prop, range)) {
        data->range = range[1] - range[0];
        data->min = range[0];
      }
      else {
        BLI_assert(0);
      }
    }
    data->offset = gizmo_offset_from_value_constr(
        data->range_fac, data->min, data->range, value, inverted);
  }
  else {
    data->offset = value;
  }
}

void gizmo_property_value_reset(bContext *C,
                                const wmGizmo *gz,
                                GizmoInteraction *inter,
                                wmGizmoProperty *gz_prop)
{
  WM_gizmo_target_property_float_set(C, gz, gz_prop, inter->init_value);
}

/* -------------------------------------------------------------------- */

void gizmo_color_get(const wmGizmo *gz, const bool highlight, float r_col[4])
{
  if (highlight && !(gz->flag & WM_GIZMO_DRAW_HOVER)) {
    copy_v4_v4(r_col, gz->color_hi);
  }
  else {
    copy_v4_v4(r_col, gz->color);
  }
}

/* -------------------------------------------------------------------- */

/**
 * Takes mouse coordinates and returns them in relation to the gizmo.
 * Both 2D & 3D supported, use so we can use 2D gizmos in the 3D view.
 */
bool gizmo_window_project_2d(bContext *C,
                             const struct wmGizmo *gz,
                             const float mval[2],
                             int axis,
                             bool use_offset,
                             float r_co[2])
{
  float mat[4][4];
  {
    float mat_identity[4][4];
    struct WM_GizmoMatrixParams params = {NULL};
    if (use_offset == false) {
      unit_m4(mat_identity);
      params.matrix_offset = mat_identity;
    }
    WM_gizmo_calc_matrix_final_params(gz, &params, mat);
  }

  /* rotate mouse in relation to the center and relocate it */
  if (gz->parent_gzgroup->type->flag & WM_GIZMOGROUPTYPE_3D) {
    /* For 3d views, transform 2D mouse pos onto plane. */
    ARegion *region = CTX_wm_region(C);

    float plane[4], co[3];
    plane_from_point_normal_v3(plane, mat[3], mat[2]);
    bool clip_ray = ((RegionView3D *)region->regiondata)->is_persp;
    if (ED_view3d_win_to_3d_on_plane(region, plane, mval, clip_ray, co)) {
      float imat[4][4];
      invert_m4_m4(imat, mat);
      mul_m4_v3(imat, co);
      r_co[0] = co[(axis + 1) % 3];
      r_co[1] = co[(axis + 2) % 3];
      return true;
    }
    return false;
  }
  else {
    float co[3] = {mval[0], mval[1], 0.0f};
    float imat[4][4];
    invert_m4_m4(imat, mat);
    mul_m4_v3(imat, co);
    copy_v2_v2(r_co, co);
    return true;
  }
}

bool gizmo_window_project_3d(
    bContext *C, const struct wmGizmo *gz, const float mval[2], bool use_offset, float r_co[3])
{
  float mat[4][4];
  {
    float mat_identity[4][4];
    struct WM_GizmoMatrixParams params = {NULL};
    if (use_offset == false) {
      unit_m4(mat_identity);
      params.matrix_offset = mat_identity;
    }
    WM_gizmo_calc_matrix_final_params(gz, &params, mat);
  }

  if (gz->parent_gzgroup->type->flag & WM_GIZMOGROUPTYPE_3D) {
    View3D *v3d = CTX_wm_view3d(C);
    ARegion *region = CTX_wm_region(C);
    /* Note: we might want a custom reference point passed in,
     * instead of the gizmo center. */
    ED_view3d_win_to_3d(v3d, region, mat[3], mval, r_co);
    invert_m4(mat);
    mul_m4_v3(mat, r_co);
    return true;
  }
  else {
    float co[3] = {mval[0], mval[1], 0.0f};
    float imat[4][4];
    invert_m4_m4(imat, mat);
    mul_m4_v3(imat, co);
    copy_v2_v2(r_co, co);
    return true;
  }
}

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
 * \ingroup bke
 *
 * Deform coordinates by a curve object (used by modifier).
 */

#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "BLI_math.h"
#include "BLI_utildefines.h"

#include "DNA_curve_types.h"
#include "DNA_meshdata_types.h"
#include "DNA_object_types.h"

#include "BKE_anim_path.h"
#include "BKE_curve.h"
#include "BKE_lattice.h"
#include "BKE_modifier.h"

#include "BKE_deform.h"

/* -------------------------------------------------------------------- */
/** \name Curve Deform Internal Utilities
 * \{ */

/* calculations is in local space of deformed object
 * so we store in latmat transform from path coord inside object
 */
typedef struct {
  float dmin[3], dmax[3];
  float curvespace[4][4], objectspace[4][4], objectspace3[3][3];
  int no_rot_axis;
} CurveDeform;

static void init_curve_deform(Object *par, Object *ob, CurveDeform *cd)
{
  invert_m4_m4(ob->imat, ob->obmat);
  mul_m4_m4m4(cd->objectspace, ob->imat, par->obmat);
  invert_m4_m4(cd->curvespace, cd->objectspace);
  copy_m3_m4(cd->objectspace3, cd->objectspace);
  cd->no_rot_axis = 0;
}

/* this makes sure we can extend for non-cyclic.
 *
 * returns OK: 1/0
 */
static bool where_on_path_deform(
    Object *ob, float ctime, float vec[4], float dir[3], float quat[4], float *radius)
{
  BevList *bl;
  float ctime1;
  int cycl = 0;

  /* test for cyclic */
  bl = ob->runtime.curve_cache->bev.first;
  if (!bl->nr) {
    return false;
  }
  if (bl->poly > -1) {
    cycl = 1;
  }

  if (cycl == 0) {
    ctime1 = CLAMPIS(ctime, 0.0f, 1.0f);
  }
  else {
    ctime1 = ctime;
  }

  /* vec needs 4 items */
  if (where_on_path(ob, ctime1, vec, dir, quat, radius, NULL)) {

    if (cycl == 0) {
      Path *path = ob->runtime.curve_cache->path;
      float dvec[3];

      if (ctime < 0.0f) {
        sub_v3_v3v3(dvec, path->data[1].vec, path->data[0].vec);
        mul_v3_fl(dvec, ctime * (float)path->len);
        add_v3_v3(vec, dvec);
        if (quat) {
          copy_qt_qt(quat, path->data[0].quat);
        }
        if (radius) {
          *radius = path->data[0].radius;
        }
      }
      else if (ctime > 1.0f) {
        sub_v3_v3v3(dvec, path->data[path->len - 1].vec, path->data[path->len - 2].vec);
        mul_v3_fl(dvec, (ctime - 1.0f) * (float)path->len);
        add_v3_v3(vec, dvec);
        if (quat) {
          copy_qt_qt(quat, path->data[path->len - 1].quat);
        }
        if (radius) {
          *radius = path->data[path->len - 1].radius;
        }
        /* weight - not used but could be added */
      }
    }
    return true;
  }
  return false;
}

/* for each point, rotate & translate to curve */
/* use path, since it has constant distances */
/* co: local coord, result local too */
/* returns quaternion for rotation, using cd->no_rot_axis */
/* axis is using another define!!! */
static bool calc_curve_deform(
    Object *par, float co[3], const short axis, CurveDeform *cd, float r_quat[4])
{
  Curve *cu = par->data;
  float fac, loc[4], dir[3], new_quat[4], radius;
  short index;
  const bool is_neg_axis = (axis > 2);

  if (par->runtime.curve_cache == NULL) {
    /* Happens with a cyclic dependencies. */
    return false;
  }

  if (par->runtime.curve_cache->path == NULL) {
    return false; /* happens on append, cyclic dependencies and empty curves */
  }

  /* options */
  if (is_neg_axis) {
    index = axis - 3;
    if (cu->flag & CU_STRETCH) {
      fac = -(co[index] - cd->dmax[index]) / (cd->dmax[index] - cd->dmin[index]);
    }
    else {
      fac = -(co[index] - cd->dmax[index]) / (par->runtime.curve_cache->path->totdist);
    }
  }
  else {
    index = axis;
    if (cu->flag & CU_STRETCH) {
      fac = (co[index] - cd->dmin[index]) / (cd->dmax[index] - cd->dmin[index]);
    }
    else {
      if (LIKELY(par->runtime.curve_cache->path->totdist > FLT_EPSILON)) {
        fac = +(co[index] - cd->dmin[index]) / (par->runtime.curve_cache->path->totdist);
      }
      else {
        fac = 0.0f;
      }
    }
  }

  if (where_on_path_deform(par, fac, loc, dir, new_quat, &radius)) { /* returns OK */
    float quat[4], cent[3];

    if (cd->no_rot_axis) { /* set by caller */

      /* This is not exactly the same as 2.4x, since the axis is having rotation removed rather
       * than changing the axis before calculating the tilt but serves much the same purpose. */
      float dir_flat[3] = {0, 0, 0}, q[4];
      copy_v3_v3(dir_flat, dir);
      dir_flat[cd->no_rot_axis - 1] = 0.0f;

      normalize_v3(dir);
      normalize_v3(dir_flat);

      rotation_between_vecs_to_quat(q, dir, dir_flat); /* Could this be done faster? */

      mul_qt_qtqt(new_quat, q, new_quat);
    }

    /* Logic for 'cent' orientation *
     *
     * The way 'co' is copied to 'cent' may seem to have no meaning, but it does.
     *
     * Use a curve modifier to stretch a cube out, color each side RGB,
     * positive side light, negative dark.
     * view with X up (default), from the angle that you can see 3 faces RGB colors (light),
     * anti-clockwise
     * Notice X,Y,Z Up all have light colors and each ordered CCW.
     *
     * Now for Neg Up XYZ, the colors are all dark, and ordered clockwise - Campbell
     *
     * note: moved functions into quat_apply_track/vec_apply_track
     * */
    copy_qt_qt(quat, new_quat);
    copy_v3_v3(cent, co);

    /* zero the axis which is not used,
     * the big block of text above now applies to these 3 lines */
    quat_apply_track(
        quat,
        axis,
        (axis == 0 || axis == 2) ? 1 : 0); /* up flag is a dummy, set so no rotation is done */
    vec_apply_track(cent, axis);
    cent[index] = 0.0f;

    /* scale if enabled */
    if (cu->flag & CU_PATH_RADIUS) {
      mul_v3_fl(cent, radius);
    }

    /* local rotation */
    normalize_qt(quat);
    mul_qt_v3(quat, cent);

    /* translation */
    add_v3_v3v3(co, cent, loc);

    if (r_quat) {
      copy_qt_qt(r_quat, quat);
    }

    return true;
  }
  return false;
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Curve Deform #BKE_curve_deform_coords API
 *
 * #BKE_curve_deform and related functions.
 * \{ */

void BKE_curve_deform_coords(Object *ob_curve,
                             Object *ob_target,
                             float (*vert_coords)[3],
                             const int vert_coords_len,
                             const MDeformVert *dvert,
                             const int defgrp_index,
                             const short flag,
                             const short defaxis)
{
  Curve *cu;
  int a;
  CurveDeform cd;
  const bool is_neg_axis = (defaxis > 2);
  const bool invert_vgroup = (flag & MOD_CURVE_INVERT_VGROUP) != 0;

  if (ob_curve->type != OB_CURVE) {
    return;
  }

  cu = ob_curve->data;

  init_curve_deform(ob_curve, ob_target, &cd);

  /* dummy bounds, keep if CU_DEFORM_BOUNDS_OFF is set */
  if (is_neg_axis == false) {
    cd.dmin[0] = cd.dmin[1] = cd.dmin[2] = 0.0f;
    cd.dmax[0] = cd.dmax[1] = cd.dmax[2] = 1.0f;
  }
  else {
    /* negative, these bounds give a good rest position */
    cd.dmin[0] = cd.dmin[1] = cd.dmin[2] = -1.0f;
    cd.dmax[0] = cd.dmax[1] = cd.dmax[2] = 0.0f;
  }

  if (dvert) {
    const MDeformVert *dvert_iter;
    float vec[3];

    if (cu->flag & CU_DEFORM_BOUNDS_OFF) {
      for (a = 0, dvert_iter = dvert; a < vert_coords_len; a++, dvert_iter++) {
        const float weight = invert_vgroup ?
                                 1.0f - BKE_defvert_find_weight(dvert_iter, defgrp_index) :
                                 BKE_defvert_find_weight(dvert_iter, defgrp_index);

        if (weight > 0.0f) {
          mul_m4_v3(cd.curvespace, vert_coords[a]);
          copy_v3_v3(vec, vert_coords[a]);
          calc_curve_deform(ob_curve, vec, defaxis, &cd, NULL);
          interp_v3_v3v3(vert_coords[a], vert_coords[a], vec, weight);
          mul_m4_v3(cd.objectspace, vert_coords[a]);
        }
      }
    }
    else {
      /* set mesh min/max bounds */
      INIT_MINMAX(cd.dmin, cd.dmax);

      for (a = 0, dvert_iter = dvert; a < vert_coords_len; a++, dvert_iter++) {
        const float weight = invert_vgroup ?
                                 1.0f - BKE_defvert_find_weight(dvert_iter, defgrp_index) :
                                 BKE_defvert_find_weight(dvert_iter, defgrp_index);
        if (weight > 0.0f) {
          mul_m4_v3(cd.curvespace, vert_coords[a]);
          minmax_v3v3_v3(cd.dmin, cd.dmax, vert_coords[a]);
        }
      }

      for (a = 0, dvert_iter = dvert; a < vert_coords_len; a++, dvert_iter++) {
        const float weight = invert_vgroup ?
                                 1.0f - BKE_defvert_find_weight(dvert_iter, defgrp_index) :
                                 BKE_defvert_find_weight(dvert_iter, defgrp_index);

        if (weight > 0.0f) {
          /* already in 'cd.curvespace', prev for loop */
          copy_v3_v3(vec, vert_coords[a]);
          calc_curve_deform(ob_curve, vec, defaxis, &cd, NULL);
          interp_v3_v3v3(vert_coords[a], vert_coords[a], vec, weight);
          mul_m4_v3(cd.objectspace, vert_coords[a]);
        }
      }
    }
  }
  else {
    if (cu->flag & CU_DEFORM_BOUNDS_OFF) {
      for (a = 0; a < vert_coords_len; a++) {
        mul_m4_v3(cd.curvespace, vert_coords[a]);
        calc_curve_deform(ob_curve, vert_coords[a], defaxis, &cd, NULL);
        mul_m4_v3(cd.objectspace, vert_coords[a]);
      }
    }
    else {
      /* set mesh min max bounds */
      INIT_MINMAX(cd.dmin, cd.dmax);

      for (a = 0; a < vert_coords_len; a++) {
        mul_m4_v3(cd.curvespace, vert_coords[a]);
        minmax_v3v3_v3(cd.dmin, cd.dmax, vert_coords[a]);
      }

      for (a = 0; a < vert_coords_len; a++) {
        /* already in 'cd.curvespace', prev for loop */
        calc_curve_deform(ob_curve, vert_coords[a], defaxis, &cd, NULL);
        mul_m4_v3(cd.objectspace, vert_coords[a]);
      }
    }
  }
}

/* input vec and orco = local coord in armature space */
/* orco is original not-animated or deformed reference point */
/* result written in vec and mat */
void BKE_curve_deform_co(Object *ob_curve,
                         Object *ob_target,
                         const float orco[3],
                         float vec[3],
                         float mat[3][3],
                         const int no_rot_axis)
{
  CurveDeform cd;
  float quat[4];

  if (ob_curve->type != OB_CURVE) {
    unit_m3(mat);
    return;
  }

  init_curve_deform(ob_curve, ob_target, &cd);
  cd.no_rot_axis = no_rot_axis; /* option to only rotate for XY, for example */

  copy_v3_v3(cd.dmin, orco);
  copy_v3_v3(cd.dmax, orco);

  mul_m4_v3(cd.curvespace, vec);

  if (calc_curve_deform(ob_curve, vec, ob_target->trackflag, &cd, quat)) {
    float qmat[3][3];

    quat_to_mat3(qmat, quat);
    mul_m3_m3m3(mat, qmat, cd.objectspace3);
  }
  else {
    unit_m3(mat);
  }

  mul_m4_v3(cd.objectspace, vec);
}

/** \} */

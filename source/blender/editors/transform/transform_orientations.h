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

#pragma once

struct TransInfo;

short transform_orientation_matrix_get(struct bContext *C,
                                       struct TransInfo *t,
                                       short orient_index,
                                       const float custom[3][3],
                                       float r_spacemtx[3][3]);
const char *transform_orientations_spacename_get(struct TransInfo *t, const short orient_type);
void transform_orientations_current_set(struct TransInfo *t, const short orient_index);

/* Those two fill in mat and return non-zero on success */
bool transform_orientations_create_from_axis(float mat[3][3],
                                             const float x[3],
                                             const float y[3],
                                             const float z[3]);
bool createSpaceNormal(float mat[3][3], const float normal[3]);
bool createSpaceNormalTangent(float mat[3][3], const float normal[3], const float tangent[3]);

struct TransformOrientation *addMatrixSpace(struct bContext *C,
                                            float mat[3][3],
                                            const char *name,
                                            const bool overwrite);
void applyTransformOrientation(const struct TransformOrientation *ts,
                               float r_mat[3][3],
                               char r_name[64]);

enum {
  ORIENTATION_NONE = 0,
  ORIENTATION_NORMAL = 1,
  ORIENTATION_VERT = 2,
  ORIENTATION_EDGE = 3,
  ORIENTATION_FACE = 4,
};
#define ORIENTATION_USE_PLANE(ty) ELEM(ty, ORIENTATION_NORMAL, ORIENTATION_EDGE, ORIENTATION_FACE)

int getTransformOrientation_ex(const struct bContext *C,
                               struct Object *ob,
                               struct Object *obedit,
                               float normal[3],
                               float plane[3],
                               const short around);
int getTransformOrientation(const struct bContext *C, float normal[3], float plane[3]);

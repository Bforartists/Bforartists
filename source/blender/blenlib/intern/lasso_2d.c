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
 * \ingroup bli
 */

#include "DNA_vec_types.h"

#include "BLI_math.h"
#include "BLI_strict_flags.h"

#include "BLI_lasso_2d.h" /* own include */

void BLI_lasso_boundbox(rcti *rect, const int mcoords[][2], const unsigned int mcoords_len)
{
  unsigned int a;

  rect->xmin = rect->xmax = mcoords[0][0];
  rect->ymin = rect->ymax = mcoords[0][1];

  for (a = 1; a < mcoords_len; a++) {
    if (mcoords[a][0] < rect->xmin) {
      rect->xmin = mcoords[a][0];
    }
    else if (mcoords[a][0] > rect->xmax) {
      rect->xmax = mcoords[a][0];
    }
    if (mcoords[a][1] < rect->ymin) {
      rect->ymin = mcoords[a][1];
    }
    else if (mcoords[a][1] > rect->ymax) {
      rect->ymax = mcoords[a][1];
    }
  }
}

bool BLI_lasso_is_point_inside(const int mcoords[][2],
                               const unsigned int mcoords_len,
                               const int sx,
                               const int sy,
                               const int error_value)
{
  if (sx == error_value || mcoords_len == 0) {
    return false;
  }
  else {
    int pt[2] = {sx, sy};
    return isect_point_poly_v2_int(pt, mcoords, mcoords_len, true);
  }
}

/* edge version for lasso select. we assume boundbox check was done */
bool BLI_lasso_is_edge_inside(const int mcoords[][2],
                              const unsigned int mcoords_len,
                              int x0,
                              int y0,
                              int x1,
                              int y1,
                              const int error_value)
{

  if (x0 == error_value || x1 == error_value || mcoords_len == 0) {
    return false;
  }

  const int v1[2] = {x0, y0}, v2[2] = {x1, y1};

  /* check points in lasso */
  if (BLI_lasso_is_point_inside(mcoords, mcoords_len, v1[0], v1[1], error_value)) {
    return true;
  }
  if (BLI_lasso_is_point_inside(mcoords, mcoords_len, v2[0], v2[1], error_value)) {
    return true;
  }

  /* no points in lasso, so we have to intersect with lasso edge */

  if (isect_seg_seg_v2_int(mcoords[0], mcoords[mcoords_len - 1], v1, v2) > 0) {
    return true;
  }
  for (unsigned int a = 0; a < mcoords_len - 1; a++) {
    if (isect_seg_seg_v2_int(mcoords[a], mcoords[a + 1], v1, v2) > 0) {
      return true;
    }
  }

  return false;
}

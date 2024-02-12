/* SPDX-FileCopyrightText: 2023 Blender Authors
 * SPDX-FileCopyrightText: 2001 softSurfer (http://www.softsurfer.com)
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup bli
 */

#include <algorithm>
#include <stdlib.h>
#include <string.h>

#include "MEM_guardedalloc.h"

#include "BLI_convexhull_2d.h"
#include "BLI_math_vector.h"
#include "BLI_strict_flags.h"
#include "BLI_utildefines.h"

/* Copyright 2001, softSurfer (http://www.softsurfer.com)
 * This code may be freely used and modified for any purpose
 * providing that this copyright notice is included with it.
 * SoftSurfer makes no warranty for this code, and cannot be held
 * liable for any real or imagined damage resulting from its use.
 * Users of this code must verify correctness for their application.
 * http://softsurfer.com/Archive/algorithm_0203/algorithm_0203.htm
 */

/* -------------------------------------------------------------------- */
/** \name Main Convex-Hull Calculation
 * \{ */

/**
 * tests if a point is Left|On|Right of an infinite line.
 *    Input:  three points P0, P1, and P2
 * \returns > 0.0 for P2 left of the line through P0 and P1.
 *          = 0.0 for P2 on the line.
 *          < 0.0 for P2 right of the line.
 */
static float is_left(const float p0[2], const float p1[2], const float p2[2])
{
  return (p1[0] - p0[0]) * (p2[1] - p0[1]) - (p2[0] - p0[0]) * (p1[1] - p0[1]);
}

static int convexhull_2d_sorted(const float (*points)[2], const int points_num, int r_points[])
{
  BLI_assert(points_num >= 2); /* Doesn't handle trivial cases. */
  /* The output array `r_points[]` will be used as the stack. */
  int bot = 0;
  /* Indices for bottom and top of the stack. */
  int top = -1;
  /* Array scan index. */
  int i;

  int minmin, minmax;
  int maxmin, maxmax;
  float xmax;

  /* Get the indices of points with min X-coord and min|max Y-coord. */
  float xmin = points[0][0];
  for (i = 1; i < points_num; i++) {
    if (points[i][0] != xmin) {
      break;
    }
  }

  minmin = 0;
  minmax = i - 1;
  if (minmax == points_num - 1) { /* Degenerate case: all x-coords == X-min. */
    r_points[++top] = minmin;
    if (points[minmax][1] != points[minmin][1]) {
      /* A nontrivial segment. */
      r_points[++top] = minmax;
    }
    r_points[++top] = minmin; /* Add polygon endpoint. */
    BLI_assert(top + 1 <= points_num);
    return top + 1;
  }

  /* Get the indices of points with max X-coord and min|max Y-coord. */

  maxmax = points_num - 1;
  xmax = points[points_num - 1][0];
  for (i = points_num - 2; i >= 0; i--) {
    if (points[i][0] != xmax) {
      break;
    }
  }
  maxmin = i + 1;

  /* Compute the lower hull on the stack `r_points`. */
  r_points[++top] = minmin; /* Push `minmin` point onto stack. */
  i = minmax;
  while (++i <= maxmin) {
    /* The lower line joins `points[minmin]` with `points[maxmin]`. */
    if (is_left(points[minmin], points[maxmin], points[i]) >= 0 && i < maxmin) {
      continue; /* Ignore `points[i]` above or on the lower line. */
    }

    while (top > 0) { /* There are at least 2 points on the stack. */
      /* Test if `points[i]` is left of the line at the stack top. */
      if (is_left(points[r_points[top - 1]], points[r_points[top]], points[i]) > 0.0f) {
        break; /* `points[i]` is a new hull vertex. */
      }
      top--; /* Pop top point off stack. */
    }

    r_points[++top] = i; /* Push `points[i]` onto stack. */
  }

  /* Next, compute the upper hull on the stack `r_points` above the bottom hull. */
  if (maxmax != maxmin) {     /* If distinct `xmax` points. */
    r_points[++top] = maxmax; /* Push `maxmax` point onto stack. */
  }

  bot = top; /* the bottom point of the upper hull stack */
  i = maxmin;
  while (--i >= minmax) {
    /* The upper line joins `points[maxmax]` with `points[minmax]`. */
    if (is_left(points[maxmax], points[minmax], points[i]) >= 0 && i > minmax) {
      continue; /* Ignore points[i] below or on the upper line. */
    }

    while (top > bot) { /* At least 2 points on the upper stack. */
      /* Test if `points[i]` is left of the line at the stack top. */
      if (is_left(points[r_points[top - 1]], points[r_points[top]], points[i]) > 0.0f) {
        break; /* points[i] is a new hull vertex. */
      }
      top--; /* Pop top point off stack. */
    }

    if (points[i][0] == points[r_points[0]][0] && points[i][1] == points[r_points[0]][1]) {
      BLI_assert(top + 1 <= points_num);
      return top + 1; /* Special case (mgomes). */
    }

    r_points[++top] = i; /* Push points[i] onto stack. */
  }

  if (minmax != minmin && r_points[0] != minmin) {
    r_points[++top] = minmin; /* Push joining endpoint onto stack. */
  }

  BLI_assert(top + 1 <= points_num);
  return top + 1;
}

int BLI_convexhull_2d(const float (*points)[2], const int points_num, int r_points[])
{
  BLI_assert(points_num >= 0);
  if (points_num < 2) {
    if (points_num == 1) {
      r_points[0] = 0;
    }
    return points_num;
  }
  int *points_map = static_cast<int *>(MEM_mallocN(sizeof(int) * size_t(points_num), __func__));
  float(*points_sort)[2] = static_cast<float(*)[2]>(
      MEM_mallocN(sizeof(*points_sort) * size_t(points_num), __func__));

  for (int i = 0; i < points_num; i++) {
    points_map[i] = i;
  }

  /* Sort the points by X, then by Y. */
  std::sort(points_map, points_map + points_num, [points](const int &a_index, const int &b_index) {
    const float *a = points[a_index];
    const float *b = points[b_index];
    if (a[1] > b[1]) {
      return false;
    }
    if (a[1] < b[1]) {
      return true;
    }

    if (a[0] > b[0]) {
      return false;
    }
    if (a[0] < b[0]) {
      return true;
    }
    return false;
  });

  for (int i = 0; i < points_num; i++) {
    copy_v2_v2(points_sort[i], points[points_map[i]]);
  }

  int points_hull_num = convexhull_2d_sorted(points_sort, points_num, r_points);

  /* Map back to the unsorted index values. */
  for (int i = 0; i < points_hull_num; i++) {
    r_points[i] = points_map[r_points[i]];
  }

  MEM_freeN(points_map);
  MEM_freeN(points_sort);

  BLI_assert(points_hull_num <= points_num);
  return points_hull_num;
}

/** \} */

/* Helper functions */

/* -------------------------------------------------------------------- */
/** \name Utility Convex-Hull Functions
 * \{ */

float BLI_convexhull_aabb_fit_hull_2d(const float (*points_hull)[2], int points_hull_num)
{
  float area_best = FLT_MAX;
  float dvec_best[2]; /* best angle, delay atan2 */

  for (int i = 0, i_prev = points_hull_num - 1; i < points_hull_num; i_prev = i++) {
    const float *ev_a = points_hull[i];
    const float *ev_b = points_hull[i_prev];
    float dvec[2]; /* 2d rotation matrix */

    sub_v2_v2v2(dvec, ev_a, ev_b);
    if (UNLIKELY(normalize_v2(dvec) == 0.0f)) {
      continue;
    }
    /* rotation matrix */
    float min[2] = {FLT_MAX, FLT_MAX}, max[2] = {-FLT_MAX, -FLT_MAX};
    float area_test;

    for (int j = 0; j < points_hull_num; j++) {
      float tvec[2];
      mul_v2_v2_cw(tvec, dvec, points_hull[j]);

      min[0] = min_ff(min[0], tvec[0]);
      min[1] = min_ff(min[1], tvec[1]);

      max[0] = max_ff(max[0], tvec[0]);
      max[1] = max_ff(max[1], tvec[1]);

      area_test = (max[0] - min[0]) * (max[1] - min[1]);
      if (area_test > area_best) {
        break;
      }
    }

    if (area_test < area_best) {
      area_best = area_test;
      copy_v2_v2(dvec_best, dvec);
    }
  }

  return (area_best != FLT_MAX) ? float(atan2(dvec_best[0], dvec_best[1])) : 0.0f;
}

float BLI_convexhull_aabb_fit_points_2d(const float (*points)[2], int points_num)
{
  BLI_assert(points_num >= 0);
  float angle = 0.0f;

  int *index_map = static_cast<int *>(
      MEM_mallocN(sizeof(*index_map) * size_t(points_num), __func__));

  int points_hull_num = BLI_convexhull_2d(points, points_num, index_map);

  if (points_hull_num > 1) {
    float(*points_hull)[2] = static_cast<float(*)[2]>(
        MEM_mallocN(sizeof(*points_hull) * size_t(points_hull_num), __func__));
    for (int j = 0; j < points_hull_num; j++) {
      copy_v2_v2(points_hull[j], points[index_map[j]]);
    }

    angle = BLI_convexhull_aabb_fit_hull_2d(points_hull, points_hull_num);
    MEM_freeN(points_hull);
  }

  MEM_freeN(index_map);

  return angle;
}

/** \} */

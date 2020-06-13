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
#ifndef __BKE_ANIM_PATH_H__
#define __BKE_ANIM_PATH_H__

/** \file
 * \ingroup bke
 */

#ifdef __cplusplus
extern "C" {
#endif

struct ListBase;
struct Object;
struct Path;

/* ---------------------------------------------------- */
/* Curve Paths */

void free_path(struct Path *path);
void calc_curvepath(struct Object *ob, struct ListBase *nurbs);
bool where_on_path(const struct Object *ob,
                   float ctime,
                   float r_vec[4],
                   float r_dir[3],
                   float r_quat[4],
                   float *r_radius,
                   float *r_weight);

#ifdef __cplusplus
}
#endif

#endif

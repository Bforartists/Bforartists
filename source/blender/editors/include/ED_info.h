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
 * The Original Code is Copyright (C) 2009, Blender Foundation
 */

/** \file
 * \ingroup editors
 */

#pragma once

#ifdef __cplusplus
extern "C" {
#endif

struct Main;
struct wmWindowManager;

/* info_stats.c */
void ED_info_stats_clear(struct wmWindowManager *wm, struct ViewLayer *view_layer);
const char *ED_info_statusbar_string(struct Main *bmain,
                                     struct Scene *scene,
                                     struct ViewLayer *view_layer);

const char *ED_info_statistics_string(struct Main *bmain,
                                      struct Scene *scene,
                                      struct ViewLayer *view_layer);

void ED_info_draw_stats(struct Main *bmain,
                        struct Scene *scene,
                        struct ViewLayer *view_layer,
                        struct View3D *v3d_local,
                        int x,
                        int *y,
                        int height);

#ifdef __cplusplus
}
#endif

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
 */

/** \file
 * \ingroup editors
 */

#pragma once

#define SNAP_MIN_DISTANCE 30

/* For enum. */
#include "DNA_space_types.h"

bool peelObjectsTransform(struct TransInfo *t,
                          const float mval[2],
                          const bool use_peel_object,
                          /* return args */
                          float r_loc[3],
                          float r_no[3],
                          float *r_thickness);

short snapObjectsTransform(struct TransInfo *t,
                           const float mval[2],
                           float *dist_px,
                           /* return args */
                           float r_loc[3],
                           float r_no[3]);
bool snapNodesTransform(struct TransInfo *t,
                        const int mval[2],
                        /* return args */
                        float r_loc[2],
                        float *r_dist_px,
                        char *r_node_border);
void snapFrameTransform(struct TransInfo *t,
                        const eAnimEdit_AutoSnap autosnap,
                        const bool is_frame_value,
                        const float delta,
                        /* return args */
                        float *r_val);

bool transformModeUseSnap(const TransInfo *t);

bool transform_snap_increment_ex(TransInfo *t, bool use_local_space, float *r_val);
bool transform_snap_increment(TransInfo *t, float *val);
bool transform_snap_grid(TransInfo *t, float *val);

void snapSequenceBounds(TransInfo *t, const int mval[2]);

bool activeSnap(const TransInfo *t);
bool validSnap(const TransInfo *t);

void initSnapping(struct TransInfo *t, struct wmOperator *op);
void freeSnapping(struct TransInfo *t);
void applyProject(TransInfo *t);
void applyGridAbsolute(TransInfo *t);
void applySnapping(TransInfo *t, float *vec);
void resetSnapping(TransInfo *t);
eRedrawFlag handleSnapping(TransInfo *t, const struct wmEvent *event);
void drawSnapping(const struct bContext *C, TransInfo *t);
bool usingSnappingNormal(const TransInfo *t);
bool validSnappingNormal(const TransInfo *t);

void getSnapPoint(const TransInfo *t, float vec[3]);
void addSnapPoint(TransInfo *t);
eRedrawFlag updateSelectedSnapPoint(TransInfo *t);
void removeSnapPoint(TransInfo *t);

float transform_snap_distance_len_squared_fn(TransInfo *t, const float p1[3], const float p2[3]);

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
#ifndef __BKE_ANIM_H__
#define __BKE_ANIM_H__

/** \file BKE_anim.h
 *  \ingroup bke
 *  \author nzc
 *  \since March 2001
 */
struct EvaluationContext;
struct ListBase;
struct Main;
struct Object;
struct Path;
struct ReportList;
struct Scene;
struct bAnimVizSettings;
struct bMotionPath;
struct bPoseChannel;

/* ---------------------------------------------------- */
/* Animation Visualization */

void animviz_settings_init(struct bAnimVizSettings *avs);

void animviz_free_motionpath_cache(struct bMotionPath *mpath);
void animviz_free_motionpath(struct bMotionPath *mpath);

struct bMotionPath *animviz_verify_motionpaths(struct ReportList *reports, struct Scene *scene, struct Object *ob, struct bPoseChannel *pchan);

void animviz_get_object_motionpaths(struct Object *ob, ListBase *targets);
void animviz_calc_motionpaths(struct Main *bmain, struct Scene *scene, ListBase *targets);

/* ---------------------------------------------------- */
/* Curve Paths */

void free_path(struct Path *path);
void calc_curvepath(struct Object *ob, struct ListBase *nurbs);
int where_on_path(struct Object *ob, float ctime, float vec[4], float dir[3], float quat[4], float *radius, float *weight);

/* ---------------------------------------------------- */
/* Dupli-Geometry */

struct ListBase *object_duplilist_ex(
        struct Main *bmain, struct EvaluationContext *eval_ctx, struct Scene *sce, struct Object *ob, bool update);
struct ListBase *object_duplilist(
        struct Main *bmain, struct EvaluationContext *eval_ctx, struct Scene *sce, struct Object *ob);
void free_object_duplilist(struct ListBase *lb);
int count_duplilist(struct Object *ob);

typedef struct DupliExtraData {
	float obmat[4][4];
	unsigned int lay;
} DupliExtraData;

typedef struct DupliApplyData {
	int num_objects;
	DupliExtraData *extra;
} DupliApplyData;

DupliApplyData *duplilist_apply(struct Object *ob, struct Scene *scene, struct ListBase *duplilist);
void duplilist_restore(struct ListBase *duplilist, DupliApplyData *apply_data);
void duplilist_free_apply_data(DupliApplyData *apply_data);

#endif

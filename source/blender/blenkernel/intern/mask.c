/*
 * ***** BEGIN GPL LICENSE BLOCK *****
 *
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
 * The Original Code is Copyright (C) 2012 Blender Foundation.
 * All rights reserved.
 *
 * Contributor(s): Blender Foundation,
 *                 Sergey Sharybin
 *
 * ***** END GPL LICENSE BLOCK *****
 */

/** \file blender/blenkernel/intern/mask.c
 *  \ingroup bke
 */

#include <stddef.h>
#include <string.h>

#include "MEM_guardedalloc.h"

#include "BLI_utildefines.h"
#include "BLI_path_util.h"
#include "BLI_string.h"
#include "BLI_listbase.h"
#include "BLI_math.h"

#include "DNA_mask_types.h"
#include "DNA_scene_types.h"
#include "DNA_object_types.h"
#include "DNA_screen_types.h"
#include "DNA_space_types.h"
#include "DNA_movieclip_types.h"
#include "DNA_tracking_types.h"

#include "BKE_curve.h"
#include "BKE_global.h"
#include "BKE_library.h"
#include "BKE_main.h"
#include "BKE_mask.h"
#include "BKE_tracking.h"
#include "BKE_movieclip.h"
#include "BKE_utildefines.h"

static MaskSplinePoint *mask_spline_point_next(MaskSpline *spline, MaskSplinePoint *points_array, MaskSplinePoint *point)
{
	if (point == &points_array[spline->tot_point - 1]) {
		if (spline->flag & MASK_SPLINE_CYCLIC) {
			return &points_array[0];
		}
		else {
			return NULL;
		}
	}
	else {
		return point + 1;
	}
}

static MaskSplinePoint *mask_spline_point_prev(MaskSpline *spline, MaskSplinePoint *points_array, MaskSplinePoint *point)
{
	if (point == points_array) {
		if (spline->flag & MASK_SPLINE_CYCLIC) {
			return &points_array[spline->tot_point - 1];
		}
		else {
			return NULL;
		}
	}
	else {
		return point - 1;
	}
}

static BezTriple *mask_spline_point_next_bezt(MaskSpline *spline, MaskSplinePoint *points_array, MaskSplinePoint *point)
{
	if (point == &points_array[spline->tot_point - 1]) {
		if (spline->flag & MASK_SPLINE_CYCLIC) {
			return &(points_array[0].bezt);
		}
		else {
			return NULL;
		}
	}
	else {
		return &((point + 1))->bezt;
	}
}

#if 0
static BezTriple *mask_spline_point_prev_bezt(MaskSpline *spline, MaskSplinePoint *points_array, MaskSplinePoint *point)
{
	if (point == points_array) {
		if (spline->flag & MASK_SPLINE_CYCLIC) {
			return &(points_array[0].bezt);
		}
		else {
			return NULL;
		}
	}
	else {
		return &((point - 1))->bezt;
	}
}
#endif

MaskSplinePoint *BKE_mask_spline_point_array(MaskSpline *spline)
{
	return spline->points_deform ? spline->points_deform : spline->points;
}

MaskSplinePoint *BKE_mask_spline_point_array_from_point(MaskSpline *spline, MaskSplinePoint *point_ref)
{
	if ((point_ref >= spline->points) && (point_ref < &spline->points[spline->tot_point])) {
		return spline->points;
	}

	if ((point_ref >= spline->points_deform) && (point_ref < &spline->points_deform[spline->tot_point])) {
		return spline->points_deform;
	}

	BLI_assert(!"wrong array");
	return NULL;
}

/* mask layers */

MaskLayer *BKE_mask_layer_new(Mask *mask, const char *name)
{
	MaskLayer *masklay = MEM_callocN(sizeof(MaskLayer), __func__);

	if (name && name[0])
		BLI_strncpy(masklay->name, name, sizeof(masklay->name));
	else
		strcpy(masklay->name, "MaskLayer");

	BLI_addtail(&mask->masklayers, masklay);

	BKE_mask_layer_unique_name(mask, masklay);

	mask->masklay_tot++;

	masklay->blend = MASK_BLEND_MERGE;
	masklay->alpha = 1.0f;

	return masklay;
}

/* note: may still be hidden, caller needs to check */
MaskLayer *BKE_mask_layer_active(Mask *mask)
{
	return BLI_findlink(&mask->masklayers, mask->masklay_act);
}

void BKE_mask_layer_active_set(Mask *mask, MaskLayer *masklay)
{
	mask->masklay_act = BLI_findindex(&mask->masklayers, masklay);
}

void BKE_mask_layer_remove(Mask *mask, MaskLayer *masklay)
{
	BLI_remlink(&mask->masklayers, masklay);
	BKE_mask_layer_free(masklay);

	mask->masklay_tot--;

	if (mask->masklay_act >= mask->masklay_tot)
		mask->masklay_act = mask->masklay_tot - 1;
}

void BKE_mask_layer_unique_name(Mask *mask, MaskLayer *masklay)
{
	BLI_uniquename(&mask->masklayers, masklay, "MaskLayer", '.', offsetof(MaskLayer, name), sizeof(masklay->name));
}

MaskLayer *BKE_mask_layer_copy(MaskLayer *masklay)
{
	MaskLayer *masklay_new;
	MaskSpline *spline;

	masklay_new = MEM_callocN(sizeof(MaskLayer), "new mask layer");

	BLI_strncpy(masklay_new->name, masklay->name, sizeof(masklay_new->name));

	masklay_new->alpha = masklay->alpha;
	masklay_new->blend = masklay->blend;
	masklay_new->blend_flag = masklay->blend_flag;
	masklay_new->flag = masklay->flag;
	masklay_new->restrictflag = masklay->restrictflag;

	for (spline = masklay->splines.first; spline; spline = spline->next) {
		MaskSpline *spline_new = BKE_mask_spline_copy(spline);

		BLI_addtail(&masklay_new->splines, spline_new);
	}

	/* correct animation */
	if (masklay->splines_shapes.first) {
		MaskLayerShape *masklay_shape;
		MaskLayerShape *masklay_shape_new;

		for (masklay_shape = masklay->splines_shapes.first;
		     masklay_shape;
		     masklay_shape = masklay_shape->next)
		{
			masklay_shape_new = MEM_callocN(sizeof(MaskLayerShape), "new mask layer shape");

			masklay_shape_new->data = MEM_dupallocN(masklay_shape->data);
			masklay_shape_new->tot_vert = masklay_shape->tot_vert;
			masklay_shape_new->flag = masklay_shape->flag;
			masklay_shape_new->frame = masklay_shape->frame;

			BLI_addtail(&masklay_new->splines_shapes, masklay_shape_new);
		}
	}

	return masklay_new;
}

void BKE_mask_layer_copy_list(ListBase *masklayers_new, ListBase *masklayers)
{
	MaskLayer *layer;

	for (layer = masklayers->first; layer; layer = layer->next) {
		MaskLayer *layer_new = BKE_mask_layer_copy(layer);

		BLI_addtail(masklayers_new, layer_new);
	}
}

/* splines */

MaskSpline *BKE_mask_spline_add(MaskLayer *masklay)
{
	MaskSpline *spline;

	spline = MEM_callocN(sizeof(MaskSpline), "new mask spline");
	BLI_addtail(&masklay->splines, spline);

	/* spline shall have one point at least */
	spline->points = MEM_callocN(sizeof(MaskSplinePoint), "new mask spline point");
	spline->tot_point = 1;

	/* cyclic shapes are more usually used */
	// spline->flag |= MASK_SPLINE_CYCLIC; // disable because its not so nice for drawing. could be done differently

	spline->weight_interp = MASK_SPLINE_INTERP_EASE;

	BKE_mask_parent_init(&spline->parent);

	return spline;
}

int BKE_mask_spline_resolution(MaskSpline *spline, int width, int height)
{
	float max_segment = 0.01f;
	int i, resol = 1;

	if (width != 0 && height != 0) {
		if (width >= height)
			max_segment = 1.0f / (float) width;
		else
			max_segment = 1.0f / (float) height;
	}

	for (i = 0; i < spline->tot_point; i++) {
		MaskSplinePoint *point = &spline->points[i];
		BezTriple *bezt, *bezt_next;
		float a, b, c, len;
		int cur_resol;

		bezt = &point->bezt;
		bezt_next = mask_spline_point_next_bezt(spline, spline->points, point);

		if (bezt_next == NULL) {
			break;
		}

		a = len_v3v3(bezt->vec[1], bezt->vec[2]);
		b = len_v3v3(bezt->vec[2], bezt_next->vec[0]);
		c = len_v3v3(bezt_next->vec[0], bezt_next->vec[1]);

		len = a + b + c;
		cur_resol = len / max_segment;

		resol = MAX2(resol, cur_resol);
	}

	BLI_assert(resol > 0);

	if (resol > MASK_RESOL_MAX) {
		resol = MASK_RESOL_MAX;
	}

	return resol;
}

int BKE_mask_spline_feather_resolution(MaskSpline *spline, int width, int height)
{
	const float max_segment = 0.005;
	int resol = BKE_mask_spline_resolution(spline, width, height);
	float max_jump = 0.0f;
	int i;

	for (i = 0; i < spline->tot_point; i++) {
		MaskSplinePoint *point = &spline->points[i];
		float prev_u, prev_w;
		int j;

		prev_u = 0.0f;
		prev_w = point->bezt.weight;

		for (j = 0; j < point->tot_uw; j++) {
			float jump = fabsf((point->uw[j].w - prev_w) / (point->uw[j].u - prev_u));

			max_jump = MAX2(max_jump, jump);

			prev_u = point->uw[j].u;
			prev_w = point->uw[j].w;
		}
	}

	resol += max_jump / max_segment;

	BLI_assert(resol > 0);

	if (resol > MASK_RESOL_MAX) {
		resol = MASK_RESOL_MAX;
	}

	return resol;
}

int BKE_mask_spline_differentiate_calc_total(const MaskSpline *spline, const int resol)
{
	int len;

	/* count */
	len = (spline->tot_point - 1) * resol;

	if (spline->flag & MASK_SPLINE_CYCLIC) {
		len += resol;
	}
	else {
		len++;
	}

	return len;
}

float (*BKE_mask_spline_differentiate_with_resolution_ex(MaskSpline *spline,
                                                         int *tot_diff_point,
                                                         const int resol
                                                         ))[2]
{
	MaskSplinePoint *points_array = BKE_mask_spline_point_array(spline);

	MaskSplinePoint *point, *prev;
	float (*diff_points)[2], (*fp)[2];
	const int tot = BKE_mask_spline_differentiate_calc_total(spline, resol);
	int a;

	if (spline->tot_point <= 1) {
		/* nothing to differentiate */
		*tot_diff_point = 0;
		return NULL;
	}

	/* len+1 because of 'forward_diff_bezier' function */
	*tot_diff_point = tot;
	diff_points = fp = MEM_mallocN((tot + 1) * sizeof(*diff_points), "mask spline vets");

	a = spline->tot_point - 1;
	if (spline->flag & MASK_SPLINE_CYCLIC)
		a++;

	prev = points_array;
	point = prev + 1;

	while (a--) {
		BezTriple *prevbezt;
		BezTriple *bezt;
		int j;

		if (a == 0 && (spline->flag & MASK_SPLINE_CYCLIC))
			point = points_array;

		prevbezt = &prev->bezt;
		bezt = &point->bezt;

		for (j = 0; j < 2; j++) {
			BKE_curve_forward_diff_bezier(prevbezt->vec[1][j], prevbezt->vec[2][j],
			                              bezt->vec[0][j], bezt->vec[1][j],
			                              &(*fp)[j], resol, 2 * sizeof(float));
		}

		fp += resol;

		if (a == 0 && (spline->flag & MASK_SPLINE_CYCLIC) == 0) {
			copy_v2_v2(*fp, bezt->vec[1]);
		}

		prev = point;
		point++;
	}

	return diff_points;
}

float (*BKE_mask_spline_differentiate_with_resolution(MaskSpline *spline, int width, int height,
                                                      int *tot_diff_point
                                                      ))[2]
{
	int resol = BKE_mask_spline_resolution(spline, width, height);

	return BKE_mask_spline_differentiate_with_resolution_ex(spline, tot_diff_point, resol);
}

float (*BKE_mask_spline_differentiate(MaskSpline *spline, int *tot_diff_point))[2]
{
	return BKE_mask_spline_differentiate_with_resolution(spline, 0, 0, tot_diff_point);
}

/* ** feather points self-intersection collapse routine ** */

typedef struct FeatherEdgesBucket {
	int tot_segment;
	int (*segments)[2];
	int alloc_segment;
} FeatherEdgesBucket;

static void feather_bucket_add_edge(FeatherEdgesBucket *bucket, int start, int end)
{
	const int alloc_delta = 256;

	if (bucket->tot_segment >= bucket->alloc_segment) {
		if (!bucket->segments) {
			bucket->segments = MEM_callocN(alloc_delta * sizeof(*bucket->segments), "feather bucket segments");
		}
		else {
			bucket->segments = MEM_reallocN(bucket->segments,
					(alloc_delta + bucket->tot_segment) * sizeof(*bucket->segments));
		}

		bucket->alloc_segment += alloc_delta;
	}

	bucket->segments[bucket->tot_segment][0] = start;
	bucket->segments[bucket->tot_segment][1] = end;

	bucket->tot_segment++;
}

static void feather_bucket_check_intersect(float (*feather_points)[2], int tot_feather_point, FeatherEdgesBucket *bucket,
                                           int cur_a, int cur_b)
{
	int i;

	float *v1 = (float *) feather_points[cur_a];
	float *v2 = (float *) feather_points[cur_b];

	for (i = 0; i < bucket->tot_segment; i++) {
		int check_a = bucket->segments[i][0];
		int check_b = bucket->segments[i][1];

		float *v3 = (float *) feather_points[check_a];
		float *v4 = (float *) feather_points[check_b];

		if (check_a >= cur_a - 1 || cur_b == check_a)
			continue;

		if (isect_seg_seg_v2(v1, v2, v3, v4)) {
			int k, len;
			float p[2];

			isect_seg_seg_v2_point(v1, v2, v3, v4, p);

			/* TODO: for now simply choose the shortest loop, could be made smarter in some way */
			len = cur_a - check_b;
			if (len < tot_feather_point - len) {
				for (k = check_b; k <= cur_a; k++) {
					copy_v2_v2(feather_points[k], p);
				}
			}
			else {
				for (k = 0; k <= check_a; k++) {
					copy_v2_v2(feather_points[k], p);
				}

				if (cur_b != 0) {
					for (k = cur_b; k < tot_feather_point; k++) {
						copy_v2_v2(feather_points[k], p);
					}
				}
			}
		}
	}
}

static int feather_bucket_index_from_coord(float co[2], const float min[2], const float bucket_scale[2],
                                           const int buckets_per_side)
{
	int x = (int) ((co[0] - min[0]) * bucket_scale[0]);
	int y = (int) ((co[1] - min[1]) * bucket_scale[1]);

	if (x == buckets_per_side)
		x--;

	if (y == buckets_per_side)
		y--;

	return y * buckets_per_side + x;
}

static void feather_bucket_get_diagonal(FeatherEdgesBucket *buckets, int start_bucket_index, int end_bucket_index,
                                        int buckets_per_side, FeatherEdgesBucket **diagonal_bucket_a_r,
                                        FeatherEdgesBucket **diagonal_bucket_b_r)
{
	int start_bucket_x = start_bucket_index % buckets_per_side;
	int start_bucket_y = start_bucket_index / buckets_per_side;

	int end_bucket_x = end_bucket_index % buckets_per_side;
	int end_bucket_y = end_bucket_index / buckets_per_side;

	int diagonal_bucket_a_index = start_bucket_y * buckets_per_side + end_bucket_x;
	int diagonal_bucket_b_index = end_bucket_y * buckets_per_side + start_bucket_x;

	*diagonal_bucket_a_r = &buckets[diagonal_bucket_a_index];
	*diagonal_bucket_b_r = &buckets[diagonal_bucket_b_index];
}

static void spline_feather_collapse_inner_loops(MaskSpline *spline, float (*feather_points)[2], int tot_feather_point)
{
#define BUCKET_INDEX(co) \
	feather_bucket_index_from_coord(co, min, bucket_scale, buckets_per_side)

	int buckets_per_side, tot_bucket;
	float bucket_size, bucket_scale[2];

	FeatherEdgesBucket *buckets;

	int i;
	float min[2], max[2];
	float max_delta_x = -1.0f, max_delta_y = -1.0f, max_delta;

	if (tot_feather_point < 4) {
		/* self-intersection works only for quads at least,
		 * in other cases polygon can't be self-intersecting anyway
		 */

		return;
	}

	/* find min/max corners of mask to build buckets in that space */
	INIT_MINMAX2(min, max);

	for (i = 0; i < tot_feather_point; i++) {
		int next = i + 1;
		float delta;

		DO_MINMAX2(feather_points[i], min, max);

		if (next == tot_feather_point) {
			if (spline->flag & MASK_SPLINE_CYCLIC)
				next = 0;
			else
				break;
		}

		delta = fabsf(feather_points[i][0] - feather_points[next][0]);
		if (delta > max_delta_x)
			max_delta_x = delta;

		delta = fabsf(feather_points[i][1] - feather_points[next][1]);
		if (delta > max_delta_y)
			max_delta_y = delta;
	}

	/* prevent divisionsby zero by ensuring bounding box is not collapsed */
	if (max[0] - min[0] < FLT_EPSILON) {
		max[0] += 0.01f;
		min[0] -= 0.01f;
	}

	if (max[1] - min[1] < FLT_EPSILON) {
		max[1] += 0.01f;
		min[1] -= 0.01f;
	}

	/* use dynamically calculated buckets per side, so we likely wouldn't
	 * run into a situation when segment doesn't fit two buckets which is
	 * pain collecting candidates for intersection
	 */

	max_delta_x /= max[0] - min[0];
	max_delta_y /= max[1] - min[1];

	max_delta = MAX2(max_delta_x, max_delta_y);

	buckets_per_side = MIN2(512, 0.9f / max_delta);

	if (buckets_per_side == 0) {
		/* happens when some segment fills the whole bounding box across some of dimension */

		buckets_per_side = 1;
	}

	tot_bucket = buckets_per_side * buckets_per_side;
	bucket_size = 1.0f / buckets_per_side;

	/* pre-compute multipliers, to save mathematical operations in loops */
	bucket_scale[0] = 1.0f / ((max[0] - min[0]) * bucket_size);
	bucket_scale[1] = 1.0f / ((max[1] - min[1]) * bucket_size);

	/* fill in buckets' edges */
	buckets = MEM_callocN(sizeof(FeatherEdgesBucket) * tot_bucket, "feather buckets");

	for (i = 0; i < tot_feather_point; i++) {
		int start = i, end = i + 1;
		int start_bucket_index, end_bucket_index;

		if (end == tot_feather_point) {
			if (spline->flag & MASK_SPLINE_CYCLIC)
				end = 0;
			else
				break;
		}

		start_bucket_index = BUCKET_INDEX(feather_points[start]);
		end_bucket_index = BUCKET_INDEX(feather_points[end]);

		feather_bucket_add_edge(&buckets[start_bucket_index], start, end);

		if (start_bucket_index != end_bucket_index) {
			FeatherEdgesBucket *end_bucket = &buckets[end_bucket_index];
			FeatherEdgesBucket *diagonal_bucket_a, *diagonal_bucket_b;

			feather_bucket_get_diagonal(buckets, start_bucket_index, end_bucket_index, buckets_per_side,
			                            &diagonal_bucket_a, &diagonal_bucket_b);

			feather_bucket_add_edge(end_bucket, start, end);
			feather_bucket_add_edge(diagonal_bucket_a, start, end);
			feather_bucket_add_edge(diagonal_bucket_a, start, end);
		}
	}

	/* check all edges for intersection with edges from their buckets */
	for (i = 0; i < tot_feather_point; i++) {
		int cur_a = i, cur_b = i + 1;
		int start_bucket_index, end_bucket_index;

		FeatherEdgesBucket *start_bucket;

		if (cur_b == tot_feather_point)
			cur_b = 0;

		start_bucket_index = BUCKET_INDEX(feather_points[cur_a]);
		end_bucket_index = BUCKET_INDEX(feather_points[cur_b]);

		start_bucket = &buckets[start_bucket_index];

		feather_bucket_check_intersect(feather_points, tot_feather_point, start_bucket, cur_a, cur_b);

		if (start_bucket_index != end_bucket_index) {
			FeatherEdgesBucket *end_bucket = &buckets[end_bucket_index];
			FeatherEdgesBucket *diagonal_bucket_a, *diagonal_bucket_b;

			feather_bucket_get_diagonal(buckets, start_bucket_index, end_bucket_index, buckets_per_side,
			                            &diagonal_bucket_a, &diagonal_bucket_b);

			feather_bucket_check_intersect(feather_points, tot_feather_point, end_bucket, cur_a, cur_b);
			feather_bucket_check_intersect(feather_points, tot_feather_point, diagonal_bucket_a, cur_a, cur_b);
			feather_bucket_check_intersect(feather_points, tot_feather_point, diagonal_bucket_b, cur_a, cur_b);
		}
	}

	/* free buckets */
	for (i = 0; i < tot_bucket; i++) {
		if (buckets[i].segments)
			MEM_freeN(buckets[i].segments);
	}

	MEM_freeN(buckets);

#undef BUCKET_INDEX
}

/**
 * values align with #BKE_mask_spline_differentiate_with_resolution_ex
 * when \a resol arguments match.
 */
float (*BKE_mask_spline_feather_differentiated_points_with_resolution_ex(MaskSpline *spline,
                                                                         int *tot_feather_point,
                                                                         const int resol,
                                                                         const int do_collapse
                                                                         ))[2]
{
	MaskSplinePoint *points_array = BKE_mask_spline_point_array(spline);
	MaskSplinePoint *point, *prev;
	float (*feather)[2], (*fp)[2];

	const int tot = BKE_mask_spline_differentiate_calc_total(spline, resol);
	int a;

	/* tot+1 because of 'forward_diff_bezier' function */
	feather = fp = MEM_mallocN((tot + 1) * sizeof(*feather), "mask spline feather diff points");

	a = spline->tot_point - 1;
	if (spline->flag & MASK_SPLINE_CYCLIC)
		a++;

	prev = points_array;
	point = prev + 1;

	while (a--) {
		/* BezTriple *prevbezt; */  /* UNUSED */
		/* BezTriple *bezt; */      /* UNUSED */
		int j;

		if (a == 0 && (spline->flag & MASK_SPLINE_CYCLIC))
			point = points_array;


		/* prevbezt = &prev->bezt; */
		/* bezt = &point->bezt; */

		for (j = 0; j < resol; j++, fp++) {
			float u = (float) j / resol, weight;
			float co[2], n[2];

			/* TODO - these calls all calculate similar things
			 * could be unified for some speed */
			BKE_mask_point_segment_co(spline, prev, u, co);
			BKE_mask_point_normal(spline, prev, u, n);
			weight = BKE_mask_point_weight(spline, prev, u);

			madd_v2_v2v2fl(*fp, co, n, weight);
		}

		if (a == 0 && (spline->flag & MASK_SPLINE_CYCLIC) == 0) {
			float u = 1.0f, weight;
			float co[2], n[2];

			BKE_mask_point_segment_co(spline, prev, u, co);
			BKE_mask_point_normal(spline, prev, u, n);
			weight = BKE_mask_point_weight(spline, prev, u);

			madd_v2_v2v2fl(*fp, co, n, weight);
		}

		prev = point;
		point++;
	}

	*tot_feather_point = tot;

	/* this is slow! - don't do on draw */
	if (do_collapse) {
		spline_feather_collapse_inner_loops(spline, feather, tot);
	}

	return feather;
}

float (*BKE_mask_spline_feather_differentiated_points_with_resolution(MaskSpline *spline, int width, int height,
                                                                      int *tot_feather_point))[2]
{
	int resol = BKE_mask_spline_feather_resolution(spline, width, height);

	return BKE_mask_spline_feather_differentiated_points_with_resolution_ex(spline, tot_feather_point, resol, FALSE);
}

float (*BKE_mask_spline_feather_differentiated_points(MaskSpline *spline, int *tot_feather_point))[2]
{
	return BKE_mask_spline_feather_differentiated_points_with_resolution(spline, 0, 0, tot_feather_point);
}

float (*BKE_mask_spline_feather_points(MaskSpline *spline, int *tot_feather_point))[2]
{
	MaskSplinePoint *points_array = BKE_mask_spline_point_array(spline);

	int i, tot = 0;
	float (*feather)[2], (*fp)[2];

	/* count */
	for (i = 0; i < spline->tot_point; i++) {
		MaskSplinePoint *point = &points_array[i];

		tot += point->tot_uw + 1;
	}

	/* create data */
	feather = fp = MEM_mallocN(tot * sizeof(*feather), "mask spline feather points");

	for (i = 0; i < spline->tot_point; i++) {
		MaskSplinePoint *point = &points_array[i];
		BezTriple *bezt = &point->bezt;
		float weight, n[2];
		int j;

		BKE_mask_point_normal(spline, point, 0.0f, n);
		weight = BKE_mask_point_weight(spline, point, 0.0f);

		madd_v2_v2v2fl(*fp, bezt->vec[1], n, weight);
		fp++;

		for (j = 0; j < point->tot_uw; j++) {
			float u = point->uw[j].u;
			float co[2];

			BKE_mask_point_segment_co(spline, point, u, co);
			BKE_mask_point_normal(spline, point, u, n);
			weight = BKE_mask_point_weight(spline, point, u);

			madd_v2_v2v2fl(*fp, co, n, weight);
			fp++;
		}
	}

	*tot_feather_point = tot;

	return feather;
}

void BKE_mask_point_direction_switch(MaskSplinePoint *point)
{
	const int tot_uw = point->tot_uw;
	const int tot_uw_half = tot_uw / 2;
	int i;

	float co_tmp[2];

	/* swap handles */
	copy_v2_v2(co_tmp, point->bezt.vec[0]);
	copy_v2_v2(point->bezt.vec[0], point->bezt.vec[2]);
	copy_v2_v2(point->bezt.vec[2], co_tmp);
	/* in this case the flags are unlikely to be different but swap anyway */
	SWAP(char, point->bezt.f1, point->bezt.f3);
	SWAP(char, point->bezt.h1, point->bezt.h2);


	/* swap UW's */
	if (tot_uw > 1) {
		/* count */
		for (i = 0; i < tot_uw_half; i++) {
			MaskSplinePointUW *uw_a = &point->uw[i];
			MaskSplinePointUW *uw_b = &point->uw[tot_uw - (i + 1)];
			SWAP(MaskSplinePointUW, *uw_a, *uw_b);
		}
	}

	for (i = 0; i < tot_uw; i++) {
		MaskSplinePointUW *uw = &point->uw[i];
		uw->u = 1.0f - uw->u;
	}
}

void BKE_mask_spline_direction_switch(MaskLayer *masklay, MaskSpline *spline)
{
	const int tot_point = spline->tot_point;
	const int tot_point_half = tot_point / 2;
	int i, i_prev;

	if (tot_point < 2) {
		return;
	}

	/* count */
	for (i = 0; i < tot_point_half; i++) {
		MaskSplinePoint *point_a = &spline->points[i];
		MaskSplinePoint *point_b = &spline->points[tot_point - (i + 1)];
		SWAP(MaskSplinePoint, *point_a, *point_b);
	}

	/* correct UW's */
	i_prev = tot_point - 1;
	for (i = 0; i < tot_point; i++) {

		BKE_mask_point_direction_switch(&spline->points[i]);

		SWAP(MaskSplinePointUW *, spline->points[i].uw,     spline->points[i_prev].uw);
		SWAP(int,                 spline->points[i].tot_uw, spline->points[i_prev].tot_uw);

		i_prev = i;
	}

	/* correct animation */
	if (masklay->splines_shapes.first) {
		MaskLayerShape *masklay_shape;

		const int spline_index = BKE_mask_layer_shape_spline_to_index(masklay, spline);

		for (masklay_shape = masklay->splines_shapes.first;
		     masklay_shape;
		     masklay_shape = masklay_shape->next)
		{
			MaskLayerShapeElem *fp_arr = (MaskLayerShapeElem *)masklay_shape->data;

			for (i = 0; i < tot_point_half; i++) {
				MaskLayerShapeElem *fp_a = &fp_arr[spline_index +              (i)     ];
				MaskLayerShapeElem *fp_b = &fp_arr[spline_index + (tot_point - (i + 1))];
				SWAP(MaskLayerShapeElem, *fp_a, *fp_b);
			}
		}
	}
}


float BKE_mask_spline_project_co(MaskSpline *spline, MaskSplinePoint *point,
                                 float start_u, const float co[2], const eMaskSign sign)
{
	const float proj_eps         = 1e-3;
	const float proj_eps_squared = proj_eps * proj_eps;
	const int N = 1000;
	float u = -1.0f, du = 1.0f / N, u1 = start_u, u2 = start_u;
	float ang = -1.0f;

	BLI_assert(ABS(sign) <= 1); /* (-1, 0, 1) */

	while (u1 > 0.0f || u2 < 1.0f) {
		float n1[2], n2[2], co1[2], co2[2];
		float v1[2], v2[2];
		float ang1, ang2;

		if (u1 >= 0.0f) {
			BKE_mask_point_segment_co(spline, point, u1, co1);
			BKE_mask_point_normal(spline, point, u1, n1);
			sub_v2_v2v2(v1, co, co1);

			if ((sign == MASK_PROJ_ANY) ||
			    ((sign == MASK_PROJ_NEG) && (dot_v2v2(v1, n1) <= 0.0f)) ||
			    ((sign == MASK_PROJ_POS) && (dot_v2v2(v1, n1) >= 0.0f)))
			{

				if (len_squared_v2(v1) > proj_eps_squared) {
					ang1 = angle_v2v2(v1, n1);
					if (ang1 > M_PI / 2.0f)
						ang1 = M_PI  - ang1;

					if (ang < 0.0f || ang1 < ang) {
						ang = ang1;
						u = u1;
					}
				}
				else {
					u = u1;
					break;
				}
			}
		}

		if (u2 <= 1.0f) {
			BKE_mask_point_segment_co(spline, point, u2, co2);
			BKE_mask_point_normal(spline, point, u2, n2);
			sub_v2_v2v2(v2, co, co2);

			if ((sign == MASK_PROJ_ANY) ||
			    ((sign == MASK_PROJ_NEG) && (dot_v2v2(v2, n2) <= 0.0f)) ||
			    ((sign == MASK_PROJ_POS) && (dot_v2v2(v2, n2) >= 0.0f)))
			{

				if (len_squared_v2(v2) > proj_eps_squared) {
					ang2 = angle_v2v2(v2, n2);
					if (ang2 > M_PI / 2.0f)
						ang2 = M_PI  - ang2;

					if (ang2 < ang) {
						ang = ang2;
						u = u2;
					}
				}
				else {
					u = u2;
					break;
				}
			}
		}

		u1 -= du;
		u2 += du;
	}

	return u;
}

/* point */

int BKE_mask_point_has_handle(MaskSplinePoint *point)
{
	BezTriple *bezt = &point->bezt;

	return bezt->h1 == HD_ALIGN;
}

void BKE_mask_point_handle(MaskSplinePoint *point, float handle[2])
{
	float vec[2];

	sub_v2_v2v2(vec, point->bezt.vec[0], point->bezt.vec[1]);

	handle[0] = (point->bezt.vec[1][0] + vec[1]);
	handle[1] = (point->bezt.vec[1][1] - vec[0]);
}

void BKE_mask_point_set_handle(MaskSplinePoint *point, float loc[2], int keep_direction,
                               float orig_handle[2], float orig_vec[3][3])
{
	BezTriple *bezt = &point->bezt;
	float v1[2], v2[2], vec[2];

	if (keep_direction) {
		sub_v2_v2v2(v1, loc, orig_vec[1]);
		sub_v2_v2v2(v2, orig_handle, orig_vec[1]);

		project_v2_v2v2(vec, v1, v2);

		if (dot_v2v2(v2, vec) > 0) {
			float len = len_v2(vec);

			sub_v2_v2v2(v1, orig_vec[0], orig_vec[1]);

			mul_v2_fl(v1, len / len_v2(v1));

			add_v2_v2v2(bezt->vec[0], bezt->vec[1], v1);
			sub_v2_v2v2(bezt->vec[2], bezt->vec[1], v1);
		}
		else {
			copy_v3_v3(bezt->vec[0], bezt->vec[1]);
			copy_v3_v3(bezt->vec[2], bezt->vec[1]);
		}
	}
	else {
		sub_v2_v2v2(v1, loc, bezt->vec[1]);

		v2[0] = -v1[1];
		v2[1] =  v1[0];

		add_v2_v2v2(bezt->vec[0], bezt->vec[1], v2);
		sub_v2_v2v2(bezt->vec[2], bezt->vec[1], v2);
	}
}

float *BKE_mask_point_segment_feather_diff_with_resolution(MaskSpline *spline, MaskSplinePoint *point,
                                                           int width, int height,
                                                           int *tot_feather_point)
{
	float *feather, *fp;
	int i, resol = BKE_mask_spline_feather_resolution(spline, width, height);

	feather = fp = MEM_callocN(2 * resol * sizeof(float), "mask point spline feather diff points");

	for (i = 0; i < resol; i++, fp += 2) {
		float u = (float)(i % resol) / resol, weight;
		float co[2], n[2];

		BKE_mask_point_segment_co(spline, point, u, co);
		BKE_mask_point_normal(spline, point, u, n);
		weight = BKE_mask_point_weight(spline, point, u);

		fp[0] = co[0] + n[0] * weight;
		fp[1] = co[1] + n[1] * weight;
	}

	*tot_feather_point = resol;

	return feather;
}

float *BKE_mask_point_segment_feather_diff(MaskSpline *spline, MaskSplinePoint *point, int *tot_feather_point)
{
	return BKE_mask_point_segment_feather_diff_with_resolution(spline, point, 0, 0, tot_feather_point);
}

float *BKE_mask_point_segment_diff_with_resolution(MaskSpline *spline, MaskSplinePoint *point,
                                                   int width, int height, int *tot_diff_point)
{
	MaskSplinePoint *points_array = BKE_mask_spline_point_array_from_point(spline, point);

	BezTriple *bezt, *bezt_next;
	float *diff_points, *fp;
	int j, resol = BKE_mask_spline_resolution(spline, width, height);

	bezt = &point->bezt;
	bezt_next = mask_spline_point_next_bezt(spline, points_array, point);

	if (!bezt_next)
		return NULL;

	/* resol+1 because of 'forward_diff_bezier' function */
	*tot_diff_point = resol + 1;
	diff_points = fp = MEM_callocN((resol + 1) * 2 * sizeof(float), "mask segment vets");

	for (j = 0; j < 2; j++) {
		BKE_curve_forward_diff_bezier(bezt->vec[1][j], bezt->vec[2][j],
		                              bezt_next->vec[0][j], bezt_next->vec[1][j],
		                              fp + j, resol, 2 * sizeof(float));
	}

	copy_v2_v2(fp + 2 * resol, bezt_next->vec[1]);

	return diff_points;
}

float *BKE_mask_point_segment_diff(MaskSpline *spline, MaskSplinePoint *point, int *tot_diff_point)
{
	return BKE_mask_point_segment_diff_with_resolution(spline, point, 0, 0, tot_diff_point);
}

void BKE_mask_point_segment_co(MaskSpline *spline, MaskSplinePoint *point, float u, float co[2])
{
	MaskSplinePoint *points_array = BKE_mask_spline_point_array_from_point(spline, point);

	BezTriple *bezt = &point->bezt, *bezt_next;
	float q0[2], q1[2], q2[2], r0[2], r1[2];

	bezt_next = mask_spline_point_next_bezt(spline, points_array, point);

	if (!bezt_next) {
		copy_v2_v2(co, bezt->vec[1]);
		return;
	}

	interp_v2_v2v2(q0, bezt->vec[1], bezt->vec[2], u);
	interp_v2_v2v2(q1, bezt->vec[2], bezt_next->vec[0], u);
	interp_v2_v2v2(q2, bezt_next->vec[0], bezt_next->vec[1], u);

	interp_v2_v2v2(r0, q0, q1, u);
	interp_v2_v2v2(r1, q1, q2, u);

	interp_v2_v2v2(co, r0, r1, u);
}

void BKE_mask_point_normal(MaskSpline *spline, MaskSplinePoint *point, float u, float n[2])
{
	MaskSplinePoint *points_array = BKE_mask_spline_point_array_from_point(spline, point);

	BezTriple *bezt = &point->bezt, *bezt_next;
	float q0[2], q1[2], q2[2], r0[2], r1[2], vec[2];

	bezt_next = mask_spline_point_next_bezt(spline, points_array, point);

	if (!bezt_next) {
		BKE_mask_point_handle(point, vec);

		sub_v2_v2v2(n, vec, bezt->vec[1]);
		normalize_v2(n);
		return;
	}

	interp_v2_v2v2(q0, bezt->vec[1], bezt->vec[2], u);
	interp_v2_v2v2(q1, bezt->vec[2], bezt_next->vec[0], u);
	interp_v2_v2v2(q2, bezt_next->vec[0], bezt_next->vec[1], u);

	interp_v2_v2v2(r0, q0, q1, u);
	interp_v2_v2v2(r1, q1, q2, u);

	sub_v2_v2v2(vec, r1, r0);

	n[0] = -vec[1];
	n[1] =  vec[0];

	normalize_v2(n);
}

static float mask_point_interp_weight(BezTriple *bezt, BezTriple *bezt_next, const float u)
{
	return (bezt->weight * (1.0f - u)) + (bezt_next->weight * u);
}

float BKE_mask_point_weight_scalar(MaskSpline *spline, MaskSplinePoint *point, const float u)
{
	MaskSplinePoint *points_array = BKE_mask_spline_point_array_from_point(spline, point);
	BezTriple *bezt = &point->bezt, *bezt_next;

	bezt_next = mask_spline_point_next_bezt(spline, points_array, point);

	if (!bezt_next) {
		return bezt->weight;
	}
	else if (u <= 0.0) {
		return bezt->weight;
	}
	else if (u >= 1.0f) {
		return bezt_next->weight;
	}
	else {
		return mask_point_interp_weight(bezt, bezt_next, u);
	}
}

float BKE_mask_point_weight(MaskSpline *spline, MaskSplinePoint *point, const float u)
{
	MaskSplinePoint *points_array = BKE_mask_spline_point_array_from_point(spline, point);
	BezTriple *bezt = &point->bezt, *bezt_next;

	bezt_next = mask_spline_point_next_bezt(spline, points_array, point);

	if (!bezt_next) {
		return bezt->weight;
	}
	else if (u <= 0.0) {
		return bezt->weight;
	}
	else if (u >= 1.0f) {
		return bezt_next->weight;
	}
	else {
		float cur_u = 0.0f, cur_w = 0.0f, next_u = 0.0f, next_w = 0.0f, fac; /* Quite warnings */
		int i;

		for (i = 0; i < point->tot_uw + 1; i++) {

			if (i == 0) {
				cur_u = 0.0f;
				cur_w = 1.0f; /* mask_point_interp_weight will scale it */
			}
			else {
				cur_u = point->uw[i - 1].u;
				cur_w = point->uw[i - 1].w;
			}

			if (i == point->tot_uw) {
				next_u = 1.0f;
				next_w = 1.0f; /* mask_point_interp_weight will scale it */
			}
			else {
				next_u = point->uw[i].u;
				next_w = point->uw[i].w;
			}

			if (u >= cur_u && u <= next_u) {
				break;
			}
		}

		fac = (u - cur_u) / (next_u - cur_u);

		cur_w  *= mask_point_interp_weight(bezt, bezt_next, cur_u);
		next_w *= mask_point_interp_weight(bezt, bezt_next, next_u);

		if (spline->weight_interp == MASK_SPLINE_INTERP_EASE) {
			return cur_w + (next_w - cur_w) * (3.0f * fac * fac - 2.0f * fac * fac * fac);
		}
		else {
			return (1.0f - fac) * cur_w + fac * next_w;
		}
	}
}

MaskSplinePointUW *BKE_mask_point_sort_uw(MaskSplinePoint *point, MaskSplinePointUW *uw)
{
	if (point->tot_uw > 1) {
		int idx = uw - point->uw;

		if (idx > 0 && point->uw[idx - 1].u > uw->u) {
			while (idx > 0 && point->uw[idx - 1].u > point->uw[idx].u) {
				SWAP(MaskSplinePointUW, point->uw[idx - 1], point->uw[idx]);
				idx--;
			}
		}

		if (idx < point->tot_uw - 1 && point->uw[idx + 1].u < uw->u) {
			while (idx < point->tot_uw - 1 && point->uw[idx + 1].u < point->uw[idx].u) {
				SWAP(MaskSplinePointUW, point->uw[idx + 1], point->uw[idx]);
				idx++;
			}
		}

		return &point->uw[idx];
	}

	return uw;
}

void BKE_mask_point_add_uw(MaskSplinePoint *point, float u, float w)
{
	if (!point->uw)
		point->uw = MEM_callocN(sizeof(*point->uw), "mask point uw");
	else
		point->uw = MEM_reallocN(point->uw, (point->tot_uw + 1) * sizeof(*point->uw));

	point->uw[point->tot_uw].u = u;
	point->uw[point->tot_uw].w = w;

	point->tot_uw++;

	BKE_mask_point_sort_uw(point, &point->uw[point->tot_uw - 1]);
}

void BKE_mask_point_select_set(MaskSplinePoint *point, const short do_select)
{
	int i;

	if (do_select) {
		MASKPOINT_SEL_ALL(point);
	}
	else {
		MASKPOINT_DESEL_ALL(point);
	}

	for (i = 0; i < point->tot_uw; i++) {
		if (do_select) {
			point->uw[i].flag |= SELECT;
		}
		else {
			point->uw[i].flag &= ~SELECT;
		}
	}
}

void BKE_mask_point_select_set_handle(MaskSplinePoint *point, const short do_select)
{
	if (do_select) {
		MASKPOINT_SEL_HANDLE(point);
	}
	else {
		MASKPOINT_DESEL_HANDLE(point);
	}
}

/* only mask block itself */
static Mask *mask_alloc(const char *name)
{
	Mask *mask;

	mask = BKE_libblock_alloc(&G.main->mask, ID_MSK, name);

	return mask;
}

Mask *BKE_mask_new(const char *name)
{
	Mask *mask;
	char mask_name[MAX_ID_NAME - 2];

	if (name && name[0])
		BLI_strncpy(mask_name, name, sizeof(mask_name));
	else
		strcpy(mask_name, "Mask");

	mask = mask_alloc(mask_name);

	/* arbitrary defaults */
	mask->sfra = 1;
	mask->efra = 100;

	return mask;
}

Mask *BKE_mask_copy_nolib(Mask *mask)
{
	Mask *mask_new;

	mask_new = MEM_dupallocN(mask);

	/*take care here! - we may want to copy anim data  */
	mask_new->adt = NULL;

	mask_new->masklayers.first = NULL;
	mask_new->masklayers.last = NULL;

	BKE_mask_layer_copy_list(&mask_new->masklayers, &mask->masklayers);

	/* enable fake user by default */
	if (!(mask_new->id.flag & LIB_FAKEUSER)) {
		mask_new->id.flag |= LIB_FAKEUSER;
		mask_new->id.us++;
	}

	return mask_new;
}

Mask *BKE_mask_copy(Mask *mask)
{
	Mask *mask_new;

	mask_new = BKE_libblock_copy(&mask->id);

	mask_new->masklayers.first = NULL;
	mask_new->masklayers.last = NULL;

	BKE_mask_layer_copy_list(&mask_new->masklayers, &mask->masklayers);

	/* enable fake user by default */
	if (!(mask_new->id.flag & LIB_FAKEUSER)) {
		mask_new->id.flag |= LIB_FAKEUSER;
		mask_new->id.us++;
	}

	return mask_new;
}

void BKE_mask_point_free(MaskSplinePoint *point)
{
	if (point->uw)
		MEM_freeN(point->uw);
}

void BKE_mask_spline_free(MaskSpline *spline)
{
	int i = 0;

	for (i = 0; i < spline->tot_point; i++) {
		MaskSplinePoint *point;
		point = &spline->points[i];
		BKE_mask_point_free(point);

		if (spline->points_deform) {
			point = &spline->points_deform[i];
			BKE_mask_point_free(point);
		}
	}

	MEM_freeN(spline->points);

	if (spline->points_deform) {
		MEM_freeN(spline->points_deform);
	}

	MEM_freeN(spline);
}

static MaskSplinePoint *mask_spline_points_copy(MaskSplinePoint *points, int tot_point)
{
	MaskSplinePoint *npoints;
	int i;

	npoints = MEM_dupallocN(points);

	for (i = 0; i < tot_point; i++) {
		MaskSplinePoint *point = &npoints[i];

		if (point->uw)
			point->uw = MEM_dupallocN(point->uw);
	}

	return npoints;
}

MaskSpline *BKE_mask_spline_copy(MaskSpline *spline)
{
	MaskSpline *nspline = MEM_callocN(sizeof(MaskSpline), "new spline");

	*nspline = *spline;

	nspline->points_deform = NULL;
	nspline->points = mask_spline_points_copy(spline->points, spline->tot_point);

	if (spline->points_deform) {
		nspline->points_deform = mask_spline_points_copy(spline->points_deform, spline->tot_point);
	}

	return nspline;
}

/* note: does NOT add to the list */
MaskLayerShape *BKE_mask_layer_shape_alloc(MaskLayer *masklay, const int frame)
{
	MaskLayerShape *masklay_shape;
	int tot_vert = BKE_mask_layer_shape_totvert(masklay);

	masklay_shape = MEM_mallocN(sizeof(MaskLayerShape), __func__);
	masklay_shape->frame = frame;
	masklay_shape->tot_vert = tot_vert;
	masklay_shape->data = MEM_mallocN(tot_vert * sizeof(float) * MASK_OBJECT_SHAPE_ELEM_SIZE, __func__);

	return masklay_shape;
}

void BKE_mask_layer_shape_free(MaskLayerShape *masklay_shape)
{
	MEM_freeN(masklay_shape->data);

	MEM_freeN(masklay_shape);
}

/** \brief Free all animation keys for a mask layer
 */
void BKE_mask_layer_free_shapes(MaskLayer *masklay)
{
	MaskLayerShape *masklay_shape;

	/* free animation data */
	masklay_shape = masklay->splines_shapes.first;
	while (masklay_shape) {
		MaskLayerShape *next_masklay_shape = masklay_shape->next;

		BLI_remlink(&masklay->splines_shapes, masklay_shape);
		BKE_mask_layer_shape_free(masklay_shape);

		masklay_shape = next_masklay_shape;
	}
}

void BKE_mask_layer_free(MaskLayer *masklay)
{
	MaskSpline *spline;

	/* free splines */
	spline = masklay->splines.first;
	while (spline) {
		MaskSpline *next_spline = spline->next;

		BLI_remlink(&masklay->splines, spline);
		BKE_mask_spline_free(spline);

		spline = next_spline;
	}

	/* free animation data */
	BKE_mask_layer_free_shapes(masklay);

	MEM_freeN(masklay);
}

void BKE_mask_layer_free_list(ListBase *masklayers)
{
	MaskLayer *masklay = masklayers->first;

	while (masklay) {
		MaskLayer *masklay_next = masklay->next;

		BLI_remlink(masklayers, masklay);
		BKE_mask_layer_free(masklay);

		masklay = masklay_next;
	}
}

void BKE_mask_free(Mask *mask)
{
	BKE_mask_layer_free_list(&mask->masklayers);
}

void BKE_mask_unlink(Main *bmain, Mask *mask)
{
	bScreen *scr;
	ScrArea *area;
	SpaceLink *sl;

	for (scr = bmain->screen.first; scr; scr = scr->id.next) {
		for (area = scr->areabase.first; area; area = area->next) {
			for (sl = area->spacedata.first; sl; sl = sl->next) {
				if (sl->spacetype == SPACE_CLIP) {
					SpaceClip *sc = (SpaceClip *) sl;

					if (sc->mask_info.mask == mask)
						sc->mask_info.mask = NULL;
				}
			}
		}
	}

	mask->id.us = 0;
}

void BKE_mask_coord_from_frame(float r_co[2], const float co[2], const float frame_size[2])
{
	if (frame_size[0] == frame_size[1]) {
		r_co[0] = co[0];
		r_co[1] = co[1];
	}
	else if (frame_size[0] < frame_size[1]) {
		r_co[0] = ((co[0] - 0.5f) * (frame_size[0] / frame_size[1])) + 0.5f;
		r_co[1] = co[1];
	}
	else { /* (frame_size[0] > frame_size[1]) */
		r_co[0] = co[0];
		r_co[1] = ((co[1] - 0.5f) * (frame_size[1] / frame_size[0])) + 0.5f;
	}
}
void BKE_mask_coord_from_movieclip(MovieClip *clip, MovieClipUser *user, float r_co[2], const float co[2])
{
	int width, height;
	float frame_size[2];

	/* scaling for the clip */
	BKE_movieclip_get_size(clip, user, &width, &height);

	frame_size[0] = (float)width;
	frame_size[1] = (float)height;

	BKE_mask_coord_from_frame(r_co, co, frame_size);
}

/* as above but divide */
void BKE_mask_coord_to_frame(float r_co[2], const float co[2], const float frame_size[2])
{
	if (frame_size[0] == frame_size[1]) {
		r_co[0] = co[0];
		r_co[1] = co[1];
	}
	else if (frame_size[0] < frame_size[1]) {
		r_co[0] = ((co[0] - 0.5f) / (frame_size[0] / frame_size[1])) + 0.5f;
		r_co[1] = co[1];
	}
	else { /* (frame_size[0] > frame_size[1]) */
		r_co[0] = co[0];
		r_co[1] = ((co[1] - 0.5f) / (frame_size[1] / frame_size[0])) + 0.5f;
	}
}
void BKE_mask_coord_to_movieclip(MovieClip *clip, MovieClipUser *user, float r_co[2], const float co[2])
{
	int width, height;
	float frame_size[2];

	/* scaling for the clip */
	BKE_movieclip_get_size(clip, user, &width, &height);

	frame_size[0] = (float)width;
	frame_size[1] = (float)height;

	BKE_mask_coord_to_frame(r_co, co, frame_size);
}

static int BKE_mask_evaluate_parent(MaskParent *parent, float ctime, float r_co[2])
{
	if (!parent)
		return FALSE;

	if (parent->id_type == ID_MC) {
		if (parent->id) {
			MovieClip *clip = (MovieClip *) parent->id;
			MovieTracking *tracking = (MovieTracking *) &clip->tracking;
			MovieTrackingObject *ob = BKE_tracking_object_get_named(tracking, parent->parent);

			if (ob) {
				MovieTrackingTrack *track = BKE_tracking_track_get_named(tracking, ob, parent->sub_parent);
				float clip_framenr = BKE_movieclip_remap_scene_to_clip_frame(clip, ctime);

				MovieClipUser user = {0};
				user.framenr = ctime;

				if (track) {
					float marker_pos_ofs[2];
					BKE_tracking_marker_get_subframe_position(track, clip_framenr, marker_pos_ofs);
					BKE_mask_coord_from_movieclip(clip, &user, r_co, marker_pos_ofs);

					return TRUE;
				}
			}
		}
	}

	return FALSE;
}

int BKE_mask_evaluate_parent_delta(MaskParent *parent, float ctime, float r_delta[2])
{
	float parent_co[2];

	if (BKE_mask_evaluate_parent(parent, ctime, parent_co)) {
		sub_v2_v2v2(r_delta, parent_co, parent->parent_orig);
		return TRUE;
	}
	else {
		return FALSE;
	}
}

static void mask_calc_point_handle(MaskSplinePoint *point, MaskSplinePoint *point_prev, MaskSplinePoint *point_next)
{
	BezTriple *bezt = &point->bezt;
	BezTriple *bezt_prev = NULL, *bezt_next = NULL;
	//int handle_type = bezt->h1;

	if (point_prev)
		bezt_prev = &point_prev->bezt;

	if (point_next)
		bezt_next = &point_next->bezt;

#if 1
	if (bezt_prev || bezt_next) {
		BKE_nurb_handle_calc(bezt, bezt_prev, bezt_next, 0);
	}
#else
	if (handle_type == HD_VECT) {
		BKE_nurb_handle_calc(bezt, bezt_prev, bezt_next, 0);
	}
	else if (handle_type == HD_AUTO) {
		BKE_nurb_handle_calc(bezt, bezt_prev, bezt_next, 0);
	}
	else if (handle_type == HD_ALIGN) {
		float v1[3], v2[3];
		float vec[3], h[3];

		sub_v3_v3v3(v1, bezt->vec[0], bezt->vec[1]);
		sub_v3_v3v3(v2, bezt->vec[2], bezt->vec[1]);
		add_v3_v3v3(vec, v1, v2);

		if (len_v3(vec) > 1e-3) {
			h[0] = vec[1];
			h[1] = -vec[0];
			h[2] = 0.0f;
		}
		else {
			copy_v3_v3(h, v1);
		}

		add_v3_v3v3(bezt->vec[0], bezt->vec[1], h);
		sub_v3_v3v3(bezt->vec[2], bezt->vec[1], h);
	}
#endif
}

void BKE_mask_get_handle_point_adjacent(MaskSpline *spline, MaskSplinePoint *point,
                                        MaskSplinePoint **r_point_prev, MaskSplinePoint **r_point_next)
{
	/* TODO, could avoid calling this at such low level */
	MaskSplinePoint *points_array = BKE_mask_spline_point_array_from_point(spline, point);

	*r_point_prev = mask_spline_point_prev(spline, points_array, point);
	*r_point_next = mask_spline_point_next(spline, points_array, point);
}

/* calculates the tanget of a point by its previous and next
 * (ignoring handles - as if its a poly line) */
void BKE_mask_calc_tangent_polyline(MaskSpline *spline, MaskSplinePoint *point, float t[2])
{
	float tvec_a[2], tvec_b[2];

	MaskSplinePoint *point_prev, *point_next;

	BKE_mask_get_handle_point_adjacent(spline, point,
	                                   &point_prev, &point_next);

	if (point_prev) {
		sub_v2_v2v2(tvec_a, point->bezt.vec[1], point_prev->bezt.vec[1]);
		normalize_v2(tvec_a);
	}
	else {
		zero_v2(tvec_a);
	}

	if (point_next) {
		sub_v2_v2v2(tvec_b, point_next->bezt.vec[1], point->bezt.vec[1]);
		normalize_v2(tvec_b);
	}
	else {
		zero_v2(tvec_b);
	}

	add_v2_v2v2(t, tvec_a, tvec_b);
	normalize_v2(t);
}

void BKE_mask_calc_handle_point(MaskSpline *spline, MaskSplinePoint *point)
{
	MaskSplinePoint *point_prev, *point_next;

	BKE_mask_get_handle_point_adjacent(spline, point,
	                                   &point_prev, &point_next);

	mask_calc_point_handle(point, point_prev, point_next);
}

static void enforce_dist_v2_v2fl(float v1[2], const float v2[2], const float dist)
{
	if (!equals_v2v2(v2, v1)) {
		float nor[2];

		sub_v2_v2v2(nor, v1, v2);
		normalize_v2(nor);
		madd_v2_v2v2fl(v1, v2, nor, dist);
	}
}

void BKE_mask_calc_handle_adjacent_interp(MaskSpline *spline, MaskSplinePoint *point, const float u)
{
	/* TODO! - make this interpolate between siblings - not always midpoint! */
	int length_tot = 0;
	float length_average = 0.0f;
	float weight_average = 0.0f;


	MaskSplinePoint *point_prev, *point_next;

	BLI_assert(u >= 0.0f && u <= 1.0f);

	BKE_mask_get_handle_point_adjacent(spline, point,
	                                   &point_prev, &point_next);

	if (point_prev && point_next) {
		length_average = ((len_v2v2(point_prev->bezt.vec[0], point_prev->bezt.vec[1]) * (1.0f - u)) +
		                  (len_v2v2(point_next->bezt.vec[2], point_next->bezt.vec[1]) * u));

		weight_average = (point_prev->bezt.weight * (1.0f - u) +
		                  point_next->bezt.weight * u);
		length_tot = 1;
	}
	else {
		if (point_prev) {
			length_average += len_v2v2(point_prev->bezt.vec[0], point_prev->bezt.vec[1]);
			weight_average += point_prev->bezt.weight;
			length_tot++;
		}

		if (point_next) {
			length_average += len_v2v2(point_next->bezt.vec[2], point_next->bezt.vec[1]);
			weight_average += point_next->bezt.weight;
			length_tot++;
		}
	}

	if (length_tot) {
		length_average /= (float)length_tot;
		weight_average /= (float)length_tot;

		enforce_dist_v2_v2fl(point->bezt.vec[0], point->bezt.vec[1], length_average);
		enforce_dist_v2_v2fl(point->bezt.vec[2], point->bezt.vec[1], length_average);
		point->bezt.weight = weight_average;
	}
}


/**
 * \brief Resets auto handles even for non-auto bezier points
 *
 * Useful for giving sane defaults.
 */
void BKE_mask_calc_handle_point_auto(MaskSpline *spline, MaskSplinePoint *point,
                                     const short do_recalc_length)
{
	MaskSplinePoint *point_prev, *point_next;
	const char h_back[2] = {point->bezt.h1, point->bezt.h2};
	const float length_average = (do_recalc_length) ? 0.0f /* dummy value */ :
	                             (len_v3v3(point->bezt.vec[0], point->bezt.vec[1]) +
	                              len_v3v3(point->bezt.vec[1], point->bezt.vec[2])) / 2.0f;

	BKE_mask_get_handle_point_adjacent(spline, point,
	                                   &point_prev, &point_next);

	point->bezt.h1 = HD_AUTO;
	point->bezt.h2 = HD_AUTO;
	mask_calc_point_handle(point, point_prev, point_next);

	point->bezt.h1 = h_back[0];
	point->bezt.h2 = h_back[1];

	/* preserve length by applying it back */
	if (do_recalc_length == FALSE) {
		enforce_dist_v2_v2fl(point->bezt.vec[0], point->bezt.vec[1], length_average);
		enforce_dist_v2_v2fl(point->bezt.vec[2], point->bezt.vec[1], length_average);
	}
}

void BKE_mask_layer_calc_handles(MaskLayer *masklay)
{
	MaskSpline *spline;
	for (spline = masklay->splines.first; spline; spline = spline->next) {
		int i;
		for (i = 0; i < spline->tot_point; i++) {
			BKE_mask_calc_handle_point(spline, &spline->points[i]);
		}
	}
}

void BKE_mask_layer_calc_handles_deform(MaskLayer *masklay)
{
	MaskSpline *spline;
	for (spline = masklay->splines.first; spline; spline = spline->next) {
		int i;
		for (i = 0; i < spline->tot_point; i++) {
			BKE_mask_calc_handle_point(spline, &spline->points_deform[i]);
		}
	}
}

void BKE_mask_calc_handles(Mask *mask)
{
	MaskLayer *masklay;
	for (masklay = mask->masklayers.first; masklay; masklay = masklay->next) {
		BKE_mask_layer_calc_handles(masklay);
	}
}

void BKE_mask_update_deform(Mask *mask)
{
	MaskLayer *masklay;

	for (masklay = mask->masklayers.first; masklay; masklay = masklay->next) {
		MaskSpline *spline;

		for (spline = masklay->splines.first; spline; spline = spline->next) {
			int i;

			for (i = 0; i < spline->tot_point; i++) {
				const int i_prev = (i - 1) % spline->tot_point;
				const int i_next = (i + 1) % spline->tot_point;

				BezTriple *bezt_prev = &spline->points[i_prev].bezt;
				BezTriple *bezt      = &spline->points[i].bezt;
				BezTriple *bezt_next = &spline->points[i_next].bezt;

				BezTriple *bezt_def_prev = &spline->points_deform[i_prev].bezt;
				BezTriple *bezt_def      = &spline->points_deform[i].bezt;
				BezTriple *bezt_def_next = &spline->points_deform[i_next].bezt;

				float w_src[4];
				int j;

				for (j = 0; j <= 2; j += 2) { /* (0, 2) */
					printf("--- %d %d, %d, %d\n", i, j, i_prev, i_next);
					barycentric_weights_v2(bezt_prev->vec[1], bezt->vec[1], bezt_next->vec[1],
					                       bezt->vec[j], w_src);
					interp_v3_v3v3v3(bezt_def->vec[j],
					                 bezt_def_prev->vec[1], bezt_def->vec[1], bezt_def_next->vec[1], w_src);
				}
			}
		}
	}
}

void BKE_mask_spline_ensure_deform(MaskSpline *spline)
{
	int allocated_points = (MEM_allocN_len(spline->points_deform) / sizeof(*spline->points_deform));
	// printf("SPLINE ALLOC %p %d\n", spline->points_deform, allocated_points);

	if (spline->points_deform == NULL || allocated_points != spline->tot_point) {
		// printf("alloc new deform spline\n");

		if (spline->points_deform) {
			int i;

			for (i = 0; i < allocated_points; i++) {
				MaskSplinePoint *point = &spline->points_deform[i];
				BKE_mask_point_free(point);
			}

			MEM_freeN(spline->points_deform);
		}

		spline->points_deform = MEM_callocN(sizeof(*spline->points_deform) * spline->tot_point, __func__);
	}
	else {
		// printf("alloc spline done\n");
	}
}

void BKE_mask_layer_evaluate(MaskLayer *masklay, const float ctime, const int do_newframe)
{
	/* animation if available */
	if (do_newframe) {
		MaskLayerShape *masklay_shape_a;
		MaskLayerShape *masklay_shape_b;
		int found;

		if ((found = BKE_mask_layer_shape_find_frame_range(masklay, ctime,
		                                                   &masklay_shape_a, &masklay_shape_b)))
		{
			if (found == 1) {
#if 0
				printf("%s: exact %d %d (%d)\n", __func__, (int)ctime, BLI_countlist(&masklay->splines_shapes),
				       masklay_shape_a->frame);
#endif

				BKE_mask_layer_shape_to_mask(masklay, masklay_shape_a);
			}
			else if (found == 2) {
				float w = masklay_shape_b->frame - masklay_shape_a->frame;
#if 0
				printf("%s: tween %d %d (%d %d)\n", __func__, (int)ctime, BLI_countlist(&masklay->splines_shapes),
				       masklay_shape_a->frame, masklay_shape_b->frame);
#endif
				BKE_mask_layer_shape_to_mask_interp(masklay, masklay_shape_a, masklay_shape_b,
				                                    (ctime - masklay_shape_a->frame) / w);
			}
			else {
				/* always fail, should never happen */
				BLI_assert(found == 2);
			}
		}
	}
	/* animation done... */

	BKE_mask_layer_calc_handles(masklay);

	/* update deform */
	{
		MaskSpline *spline;

		for (spline = masklay->splines.first; spline; spline = spline->next) {
			int i;
			int has_auto = FALSE;

			BKE_mask_spline_ensure_deform(spline);

			for (i = 0; i < spline->tot_point; i++) {
				MaskSplinePoint *point = &spline->points[i];
				MaskSplinePoint *point_deform = &spline->points_deform[i];
				float delta[2];

				BKE_mask_point_free(point_deform);

				*point_deform = *point;
				point_deform->uw = point->uw ? MEM_dupallocN(point->uw) : NULL;

				if (BKE_mask_evaluate_parent_delta(&point->parent, ctime, delta)) {
					add_v2_v2(point_deform->bezt.vec[0], delta);
					add_v2_v2(point_deform->bezt.vec[1], delta);
					add_v2_v2(point_deform->bezt.vec[2], delta);
				}

				if (point->bezt.h1 == HD_AUTO) {
					has_auto = TRUE;
				}
			}

			/* if the spline has auto handles, these need to be recalculated after deformation */
			if (has_auto) {
				for (i = 0; i < spline->tot_point; i++) {
					MaskSplinePoint *point_deform = &spline->points_deform[i];
					if (point_deform->bezt.h1 == HD_AUTO) {
						BKE_mask_calc_handle_point(spline, point_deform);
					}
				}
			}
			/* end extra calc handles loop */
		}
	}
}

void BKE_mask_evaluate(Mask *mask, const float ctime, const int do_newframe)
{
	MaskLayer *masklay;

	for (masklay = mask->masklayers.first; masklay; masklay = masklay->next) {
		BKE_mask_layer_evaluate(masklay, ctime, do_newframe);
	}
}

/* the purpose of this function is to ensure spline->points_deform is never out of date.
 * for now re-evaluate all. eventually this might work differently */
void BKE_mask_update_display(Mask *mask, float ctime)
{
#if 0
	MaskLayer *masklay;

	for (masklay = mask->masklayers.first; masklay; masklay = masklay->next) {
		MaskSpline *spline;

		for (spline = masklay->splines.first; spline; spline = spline->next) {
			if (spline->points_deform) {
				int i = 0;

				for (i = 0; i < spline->tot_point; i++) {
					MaskSplinePoint *point;

					if (spline->points_deform) {
						point = &spline->points_deform[i];
						BKE_mask_point_free(point);
					}
				}
				if (spline->points_deform) {
					MEM_freeN(spline->points_deform);
				}

				spline->points_deform = NULL;
			}
		}
	}
#endif

	BKE_mask_evaluate(mask, ctime, FALSE);
}

void BKE_mask_evaluate_all_masks(Main *bmain, float ctime, const int do_newframe)
{
	Mask *mask;

	for (mask = bmain->mask.first; mask; mask = mask->id.next) {
		BKE_mask_evaluate(mask, ctime, do_newframe);
	}
}

void BKE_mask_update_scene(Main *bmain, Scene *scene, const int do_newframe)
{
	Mask *mask;

	for (mask = bmain->mask.first; mask; mask = mask->id.next) {
		if (mask->id.flag & LIB_ID_RECALC) {
			BKE_mask_evaluate_all_masks(bmain, CFRA, do_newframe);
		}
	}
}

void BKE_mask_parent_init(MaskParent *parent)
{
	parent->id_type = ID_MC;
}


/* *** own animation/shapekey implimentation ***
 * BKE_mask_layer_shape_XXX */

int BKE_mask_layer_shape_totvert(MaskLayer *masklay)
{
	int tot = 0;
	MaskSpline *spline;

	for (spline = masklay->splines.first; spline; spline = spline->next) {
		tot += spline->tot_point;
	}

	return tot;
}

static void mask_layer_shape_from_mask_point(BezTriple *bezt, float fp[MASK_OBJECT_SHAPE_ELEM_SIZE])
{
	copy_v2_v2(&fp[0], bezt->vec[0]);
	copy_v2_v2(&fp[2], bezt->vec[1]);
	copy_v2_v2(&fp[4], bezt->vec[2]);
	fp[6] = bezt->weight;
	fp[7] = bezt->radius;
}

static void mask_layer_shape_to_mask_point(BezTriple *bezt, float fp[MASK_OBJECT_SHAPE_ELEM_SIZE])
{
	copy_v2_v2(bezt->vec[0], &fp[0]);
	copy_v2_v2(bezt->vec[1], &fp[2]);
	copy_v2_v2(bezt->vec[2], &fp[4]);
	bezt->weight = fp[6];
	bezt->radius = fp[7];
}

/* these functions match. copy is swapped */
void BKE_mask_layer_shape_from_mask(MaskLayer *masklay, MaskLayerShape *masklay_shape)
{
	int tot = BKE_mask_layer_shape_totvert(masklay);

	if (masklay_shape->tot_vert == tot) {
		float *fp = masklay_shape->data;

		MaskSpline *spline;
		for (spline = masklay->splines.first; spline; spline = spline->next) {
			int i;
			for (i = 0; i < spline->tot_point; i++) {
				mask_layer_shape_from_mask_point(&spline->points[i].bezt, fp);
				fp += MASK_OBJECT_SHAPE_ELEM_SIZE;
			}
		}
	}
	else {
		printf("%s: vert mismatch %d != %d (frame %d)\n",
		       __func__, masklay_shape->tot_vert, tot, masklay_shape->frame);
	}
}

void BKE_mask_layer_shape_to_mask(MaskLayer *masklay, MaskLayerShape *masklay_shape)
{
	int tot = BKE_mask_layer_shape_totvert(masklay);

	if (masklay_shape->tot_vert == tot) {
		float *fp = masklay_shape->data;

		MaskSpline *spline;
		for (spline = masklay->splines.first; spline; spline = spline->next) {
			int i;
			for (i = 0; i < spline->tot_point; i++) {
				mask_layer_shape_to_mask_point(&spline->points[i].bezt, fp);
				fp += MASK_OBJECT_SHAPE_ELEM_SIZE;
			}
		}
	}
	else {
		printf("%s: vert mismatch %d != %d (frame %d)\n",
		       __func__, masklay_shape->tot_vert, tot, masklay_shape->frame);
	}
}

BLI_INLINE void interp_v2_v2v2_flfl(float target[2], const float a[2], const float b[2],
                                    const float t, const float s)
{
	target[0] = s * a[0] + t * b[0];
	target[1] = s * a[1] + t * b[1];
}

/* linear interpolation only */
void BKE_mask_layer_shape_to_mask_interp(MaskLayer *masklay,
                                         MaskLayerShape *masklay_shape_a,
                                         MaskLayerShape *masklay_shape_b,
                                         const float fac)
{
	int tot = BKE_mask_layer_shape_totvert(masklay);
	if (masklay_shape_a->tot_vert == tot && masklay_shape_b->tot_vert == tot) {
		float *fp_a = masklay_shape_a->data;
		float *fp_b = masklay_shape_b->data;
		const float ifac = 1.0f - fac;

		MaskSpline *spline;
		for (spline = masklay->splines.first; spline; spline = spline->next) {
			int i;
			for (i = 0; i < spline->tot_point; i++) {
				BezTriple *bezt = &spline->points[i].bezt;
				/* *** BKE_mask_layer_shape_from_mask - swapped *** */
				interp_v2_v2v2_flfl(bezt->vec[0], fp_a, fp_b, fac, ifac); fp_a += 2; fp_b += 2;
				interp_v2_v2v2_flfl(bezt->vec[1], fp_a, fp_b, fac, ifac); fp_a += 2; fp_b += 2;
				interp_v2_v2v2_flfl(bezt->vec[2], fp_a, fp_b, fac, ifac); fp_a += 2; fp_b += 2;
				bezt->weight = (fp_a[0] * ifac) + (fp_b[0] * fac);
				bezt->radius = (fp_a[1] * ifac) + (fp_b[1] * fac); fp_a += 2; fp_b += 2;
			}
		}
	}
	else {
		printf("%s: vert mismatch %d != %d != %d (frame %d - %d)\n",
		       __func__, masklay_shape_a->tot_vert, masklay_shape_b->tot_vert, tot,
		       masklay_shape_a->frame, masklay_shape_b->frame);
	}
}

MaskLayerShape *BKE_mask_layer_shape_find_frame(MaskLayer *masklay, const int frame)
{
	MaskLayerShape *masklay_shape;

	for (masklay_shape = masklay->splines_shapes.first;
	     masklay_shape;
	     masklay_shape = masklay_shape->next)
	{
		if (frame == masklay_shape->frame) {
			return masklay_shape;
		}
		else if (frame < masklay_shape->frame) {
			break;
		}
	}

	return NULL;
}

/* when returning 2 - the frame isnt found but before/after frames are */
int BKE_mask_layer_shape_find_frame_range(MaskLayer *masklay, const float frame,
                                          MaskLayerShape **r_masklay_shape_a,
                                          MaskLayerShape **r_masklay_shape_b)
{
	MaskLayerShape *masklay_shape;

	for (masklay_shape = masklay->splines_shapes.first;
	     masklay_shape;
	     masklay_shape = masklay_shape->next)
	{
		if (frame == masklay_shape->frame) {
			*r_masklay_shape_a = masklay_shape;
			*r_masklay_shape_b = NULL;
			return 1;
		}
		else if (frame < masklay_shape->frame) {
			if (masklay_shape->prev) {
				*r_masklay_shape_a = masklay_shape->prev;
				*r_masklay_shape_b = masklay_shape;
				return 2;
			}
			else {
				*r_masklay_shape_a = masklay_shape;
				*r_masklay_shape_b = NULL;
				return 1;
			}
		}
	}

	if ((masklay_shape = masklay->splines_shapes.last)) {
		*r_masklay_shape_a = masklay_shape;
		*r_masklay_shape_b = NULL;
		return 1;
	}
	else {
		*r_masklay_shape_a = NULL;
		*r_masklay_shape_b = NULL;

		return 0;
	}
}

MaskLayerShape *BKE_mask_layer_shape_varify_frame(MaskLayer *masklay, const int frame)
{
	MaskLayerShape *masklay_shape;

	masklay_shape = BKE_mask_layer_shape_find_frame(masklay, frame);

	if (masklay_shape == NULL) {
		masklay_shape = BKE_mask_layer_shape_alloc(masklay, frame);
		BLI_addtail(&masklay->splines_shapes, masklay_shape);
		BKE_mask_layer_shape_sort(masklay);
	}

#if 0
	{
		MaskLayerShape *masklay_shape;
		int i = 0;
		for (masklay_shape = masklay->splines_shapes.first;
		     masklay_shape;
		     masklay_shape = masklay_shape->next)
		{
			printf("mask %d, %d\n", i++, masklay_shape->frame);
		}
	}
#endif

	return masklay_shape;
}

MaskLayerShape *BKE_mask_layer_shape_duplicate(MaskLayerShape *masklay_shape)
{
	MaskLayerShape *masklay_shape_copy;

	masklay_shape_copy = MEM_dupallocN(masklay_shape);

	if (LIKELY(masklay_shape_copy->data)) {
		masklay_shape_copy->data = MEM_dupallocN(masklay_shape_copy->data);
	}

	return masklay_shape_copy;
}

void BKE_mask_layer_shape_unlink(MaskLayer *masklay, MaskLayerShape *masklay_shape)
{
	BLI_remlink(&masklay->splines_shapes, masklay_shape);

	BKE_mask_layer_shape_free(masklay_shape);
}

static int mask_layer_shape_sort_cb(void *masklay_shape_a_ptr, void *masklay_shape_b_ptr)
{
	MaskLayerShape *masklay_shape_a = (MaskLayerShape *)masklay_shape_a_ptr;
	MaskLayerShape *masklay_shape_b = (MaskLayerShape *)masklay_shape_b_ptr;

	if      (masklay_shape_a->frame < masklay_shape_b->frame)  return -1;
	else if (masklay_shape_a->frame > masklay_shape_b->frame)  return  1;
	else                                                       return  0;
}

void BKE_mask_layer_shape_sort(MaskLayer *masklay)
{
	BLI_sortlist(&masklay->splines_shapes, mask_layer_shape_sort_cb);
}

int BKE_mask_layer_shape_spline_from_index(MaskLayer *masklay, int index,
                                           MaskSpline **r_masklay_shape, int *r_index)
{
	MaskSpline *spline;

	for (spline = masklay->splines.first; spline; spline = spline->next) {
		if (index < spline->tot_point) {
			*r_masklay_shape = spline;
			*r_index = index;
			return TRUE;
		}
		index -= spline->tot_point;
	}

	return FALSE;
}

int BKE_mask_layer_shape_spline_to_index(MaskLayer *masklay, MaskSpline *spline)
{
	MaskSpline *spline_iter;
	int i_abs = 0;
	for (spline_iter = masklay->splines.first;
	     spline_iter && spline_iter != spline;
	     i_abs += spline_iter->tot_point, spline_iter = spline_iter->next)
	{
		/* pass */
	}

	return i_abs;
}

/* basic 2D interpolation functions, could make more comprehensive later */
static void interp_weights_uv_v2_calc(float r_uv[2], const float pt[2], const float pt_a[2], const float pt_b[2])
{
	float pt_on_line[2];
	r_uv[0] = closest_to_line_v2(pt_on_line, pt, pt_a, pt_b);
	r_uv[1] = (len_v2v2(pt_on_line, pt) / len_v2v2(pt_a, pt_b)) *
	          ((line_point_side_v2(pt_a, pt_b, pt) < 0.0f) ? -1.0 : 1.0);  /* this line only sets the sign */
}


static void interp_weights_uv_v2_apply(const float uv[2], float r_pt[2], const float pt_a[2], const float pt_b[2])
{
	const float dvec[2] = {pt_b[0] - pt_a[0],
	                       pt_b[1] - pt_a[1]};

	/* u */
	madd_v2_v2v2fl(r_pt, pt_a, dvec, uv[0]);

	/* v */
	r_pt[0] += -dvec[1] * uv[1];
	r_pt[1] +=  dvec[0] * uv[1];
}

/* when a now points added - resize all shapekey array  */
void BKE_mask_layer_shape_changed_add(MaskLayer *masklay, int index,
                                      int do_init, int do_init_interpolate)
{
	MaskLayerShape *masklay_shape;

	/* spline index from masklay */
	MaskSpline *spline;
	int spline_point_index;

	if (BKE_mask_layer_shape_spline_from_index(masklay, index,
	                                           &spline, &spline_point_index))
	{
		/* sanity check */
		/* the point has already been removed in this array so subtract one when comparing with the shapes */
		int tot = BKE_mask_layer_shape_totvert(masklay) - 1;

		/* for interpolation */
		/* TODO - assumes closed curve for now */
		float uv[3][2]; /* 3x 2D handles */
		const int pi_curr =   spline_point_index;
		const int pi_prev = ((spline_point_index - 1) + spline->tot_point) % spline->tot_point;
		const int pi_next =  (spline_point_index + 1)                      % spline->tot_point;

		const int index_offset = index - spline_point_index;
		/* const int pi_curr_abs = index; */
		const int pi_prev_abs = pi_prev + index_offset;
		const int pi_next_abs = pi_next + index_offset;

		int i;
		if (do_init_interpolate) {
			for (i = 0; i < 3; i++) {
				interp_weights_uv_v2_calc(uv[i],
				                          spline->points[pi_curr].bezt.vec[i],
				                          spline->points[pi_prev].bezt.vec[i],
				                          spline->points[pi_next].bezt.vec[i]);
			}
		}

		for (masklay_shape = masklay->splines_shapes.first;
		     masklay_shape;
		     masklay_shape = masklay_shape->next)
		{
			if (tot == masklay_shape->tot_vert) {
				float *data_resized;

				masklay_shape->tot_vert++;
				data_resized = MEM_mallocN(masklay_shape->tot_vert * sizeof(float) * MASK_OBJECT_SHAPE_ELEM_SIZE, __func__);
				if (index > 0) {
					memcpy(data_resized,
					       masklay_shape->data,
					       index * sizeof(float) * MASK_OBJECT_SHAPE_ELEM_SIZE);
				}

				if (index != masklay_shape->tot_vert - 1) {
					memcpy(&data_resized[(index + 1) * MASK_OBJECT_SHAPE_ELEM_SIZE],
					       masklay_shape->data + (index * MASK_OBJECT_SHAPE_ELEM_SIZE),
					       (masklay_shape->tot_vert - (index + 1)) * sizeof(float) * MASK_OBJECT_SHAPE_ELEM_SIZE);
				}

				if (do_init) {
					float *fp = &data_resized[index * MASK_OBJECT_SHAPE_ELEM_SIZE];

					mask_layer_shape_from_mask_point(&spline->points[spline_point_index].bezt, fp);

					if (do_init_interpolate && spline->tot_point > 2) {
						for (i = 0; i < 3; i++) {
							interp_weights_uv_v2_apply(uv[i],
							                           &fp[i * 2],
							                           &data_resized[(pi_prev_abs * MASK_OBJECT_SHAPE_ELEM_SIZE) + (i * 2)],
							                           &data_resized[(pi_next_abs * MASK_OBJECT_SHAPE_ELEM_SIZE) + (i * 2)]);
						}
					}
				}
				else {
					memset(&data_resized[index * MASK_OBJECT_SHAPE_ELEM_SIZE],
					       0,
					       sizeof(float) * MASK_OBJECT_SHAPE_ELEM_SIZE);
				}

				MEM_freeN(masklay_shape->data);
				masklay_shape->data = data_resized;
			}
			else {
				printf("%s: vert mismatch %d != %d (frame %d)\n",
				       __func__, masklay_shape->tot_vert, tot, masklay_shape->frame);
			}
		}
	}
}


/* move array to account for removed point */
void BKE_mask_layer_shape_changed_remove(MaskLayer *masklay, int index, int count)
{
	MaskLayerShape *masklay_shape;

	/* the point has already been removed in this array so add one when comparing with the shapes */
	int tot = BKE_mask_layer_shape_totvert(masklay);

	for (masklay_shape = masklay->splines_shapes.first;
	     masklay_shape;
	     masklay_shape = masklay_shape->next)
	{
		if (tot == masklay_shape->tot_vert - count) {
			float *data_resized;

			masklay_shape->tot_vert -= count;
			data_resized = MEM_mallocN(masklay_shape->tot_vert * sizeof(float) * MASK_OBJECT_SHAPE_ELEM_SIZE, __func__);
			if (index > 0) {
				memcpy(data_resized,
				       masklay_shape->data,
				       index * sizeof(float) * MASK_OBJECT_SHAPE_ELEM_SIZE);
			}

			if (index != masklay_shape->tot_vert) {
				memcpy(&data_resized[index * MASK_OBJECT_SHAPE_ELEM_SIZE],
				       masklay_shape->data + ((index + count) * MASK_OBJECT_SHAPE_ELEM_SIZE),
				       (masklay_shape->tot_vert - index) * sizeof(float) * MASK_OBJECT_SHAPE_ELEM_SIZE);
			}

			MEM_freeN(masklay_shape->data);
			masklay_shape->data = data_resized;
		}
		else {
			printf("%s: vert mismatch %d != %d (frame %d)\n",
			       __func__, masklay_shape->tot_vert - count, tot, masklay_shape->frame);
		}
	}
}

int BKE_mask_get_duration(Mask *mask)
{
	return maxi(1, mask->efra - mask->sfra);
}

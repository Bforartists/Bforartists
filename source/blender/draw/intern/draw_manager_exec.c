/*
 * Copyright 2016, Blender Foundation.
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
 * Contributor(s): Blender Institute
 *
 */

/** \file blender/draw/intern/draw_manager_exec.c
 *  \ingroup draw
 */

#include "draw_manager.h"

#include "BLI_mempool.h"

#include "BIF_glutil.h"

#include "BKE_global.h"
#include "BKE_object.h"

#include "GPU_draw.h"
#include "GPU_extensions.h"

#ifdef USE_GPU_SELECT
#  include "ED_view3d.h"
#  include "ED_armature.h"
#  include "GPU_select.h"
#endif

#ifdef USE_GPU_SELECT
void DRW_select_load_id(unsigned int id)
{
	BLI_assert(G.f & G_PICKSEL);
	DST.select_id = id;
}
#endif

struct GPUUniformBuffer *view_ubo;

/* -------------------------------------------------------------------- */

/** \name Draw State (DRW_state)
 * \{ */

void drw_state_set(DRWState state)
{
	if (DST.state == state) {
		return;
	}

#define CHANGED_TO(f) \
	((DST.state_lock & (f)) ? 0 : \
	 (((DST.state & (f)) ? \
	   ((state & (f)) ?  0 : -1) : \
	   ((state & (f)) ?  1 :  0))))

#define CHANGED_ANY(f) \
	(((DST.state & (f)) != (state & (f))) && \
	 ((DST.state_lock & (f)) == 0))

#define CHANGED_ANY_STORE_VAR(f, enabled) \
	(((DST.state & (f)) != (enabled = (state & (f)))) && \
	 (((DST.state_lock & (f)) == 0)))

	/* Depth Write */
	{
		int test;
		if ((test = CHANGED_TO(DRW_STATE_WRITE_DEPTH))) {
			if (test == 1) {
				glDepthMask(GL_TRUE);
			}
			else {
				glDepthMask(GL_FALSE);
			}
		}
	}

	/* Color Write */
	{
		int test;
		if ((test = CHANGED_TO(DRW_STATE_WRITE_COLOR))) {
			if (test == 1) {
				glColorMask(GL_TRUE, GL_TRUE, GL_TRUE, GL_TRUE);
			}
			else {
				glColorMask(GL_FALSE, GL_FALSE, GL_FALSE, GL_FALSE);
			}
		}
	}

	/* Cull */
	{
		DRWState test;
		if (CHANGED_ANY_STORE_VAR(
		        DRW_STATE_CULL_BACK | DRW_STATE_CULL_FRONT,
		        test))
		{
			if (test) {
				glEnable(GL_CULL_FACE);

				if ((state & DRW_STATE_CULL_BACK) != 0) {
					glCullFace(GL_BACK);
				}
				else if ((state & DRW_STATE_CULL_FRONT) != 0) {
					glCullFace(GL_FRONT);
				}
				else {
					BLI_assert(0);
				}
			}
			else {
				glDisable(GL_CULL_FACE);
			}
		}
	}

	/* Depth Test */
	{
		DRWState test;
		if (CHANGED_ANY_STORE_VAR(
		        DRW_STATE_DEPTH_LESS | DRW_STATE_DEPTH_EQUAL | DRW_STATE_DEPTH_GREATER | DRW_STATE_DEPTH_ALWAYS,
		        test))
		{
			if (test) {
				glEnable(GL_DEPTH_TEST);

				if (state & DRW_STATE_DEPTH_LESS) {
					glDepthFunc(GL_LEQUAL);
				}
				else if (state & DRW_STATE_DEPTH_EQUAL) {
					glDepthFunc(GL_EQUAL);
				}
				else if (state & DRW_STATE_DEPTH_GREATER) {
					glDepthFunc(GL_GREATER);
				}
				else if (state & DRW_STATE_DEPTH_ALWAYS) {
					glDepthFunc(GL_ALWAYS);
				}
				else {
					BLI_assert(0);
				}
			}
			else {
				glDisable(GL_DEPTH_TEST);
			}
		}
	}

	/* Wire Width */
	{
		if (CHANGED_ANY(DRW_STATE_WIRE)) {
			if ((state & DRW_STATE_WIRE) != 0) {
				glLineWidth(1.0f);
			}
			else {
				/* do nothing */
			}
		}
	}

	/* Points Size */
	{
		int test;
		if ((test = CHANGED_TO(DRW_STATE_POINT))) {
			if (test == 1) {
				GPU_enable_program_point_size();
				glPointSize(5.0f);
			}
			else {
				GPU_disable_program_point_size();
			}
		}
	}

	/* Blending (all buffer) */
	{
		int test;
		if (CHANGED_ANY_STORE_VAR(
		        DRW_STATE_BLEND | DRW_STATE_ADDITIVE | DRW_STATE_MULTIPLY | DRW_STATE_TRANSMISSION |
		        DRW_STATE_ADDITIVE_FULL,
		        test))
		{
			if (test) {
				glEnable(GL_BLEND);

				if ((state & DRW_STATE_BLEND) != 0) {
					glBlendFuncSeparate(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA, /* RGB */
					                    GL_ONE, GL_ONE_MINUS_SRC_ALPHA); /* Alpha */
				}
				else if ((state & DRW_STATE_MULTIPLY) != 0) {
					glBlendFunc(GL_DST_COLOR, GL_ZERO);
				}
				else if ((state & DRW_STATE_TRANSMISSION) != 0) {
					glBlendFunc(GL_ONE, GL_SRC_ALPHA);
				}
				else if ((state & DRW_STATE_ADDITIVE) != 0) {
					/* Do not let alpha accumulate but premult the source RGB by it. */
					glBlendFuncSeparate(GL_SRC_ALPHA, GL_ONE, /* RGB */
					                    GL_ZERO, GL_ONE); /* Alpha */
				}
				else if ((state & DRW_STATE_ADDITIVE_FULL) != 0) {
					/* Let alpha accumulate. */
					glBlendFunc(GL_ONE, GL_ONE);
				}
				else {
					BLI_assert(0);
				}
			}
			else {
				glDisable(GL_BLEND);
			}
		}
	}

	/* Clip Planes */
	{
		int test;
		if ((test = CHANGED_TO(DRW_STATE_CLIP_PLANES))) {
			if (test == 1) {
				for (int i = 0; i < DST.num_clip_planes; ++i) {
					glEnable(GL_CLIP_DISTANCE0 + i);
				}
			}
			else {
				for (int i = 0; i < MAX_CLIP_PLANES; ++i) {
					glDisable(GL_CLIP_DISTANCE0 + i);
				}
			}
		}
	}

	/* Line Stipple */
	{
		int test;
		if (CHANGED_ANY_STORE_VAR(
		        DRW_STATE_STIPPLE_2 | DRW_STATE_STIPPLE_3 | DRW_STATE_STIPPLE_4,
		        test))
		{
			if (test) {
				if ((state & DRW_STATE_STIPPLE_2) != 0) {
					setlinestyle(2);
				}
				else if ((state & DRW_STATE_STIPPLE_3) != 0) {
					setlinestyle(3);
				}
				else if ((state & DRW_STATE_STIPPLE_4) != 0) {
					setlinestyle(4);
				}
				else {
					BLI_assert(0);
				}
			}
			else {
				setlinestyle(0);
			}
		}
	}

	/* Stencil */
	{
		DRWState test;
		if (CHANGED_ANY_STORE_VAR(
		        DRW_STATE_WRITE_STENCIL |
		        DRW_STATE_STENCIL_EQUAL,
		        test))
		{
			if (test) {
				glEnable(GL_STENCIL_TEST);

				/* Stencil Write */
				if ((state & DRW_STATE_WRITE_STENCIL) != 0) {
					glStencilMask(0xFF);
					glStencilOp(GL_KEEP, GL_KEEP, GL_REPLACE);
				}
				/* Stencil Test */
				else if ((state & DRW_STATE_STENCIL_EQUAL) != 0) {
					glStencilMask(0x00); /* disable write */
					DST.stencil_mask = 0;
				}
				else {
					BLI_assert(0);
				}
			}
			else {
				/* disable write & test */
				DST.stencil_mask = 0;
				glStencilMask(0x00);
				glStencilFunc(GL_ALWAYS, 1, 0xFF);
				glDisable(GL_STENCIL_TEST);
			}
		}
	}

#undef CHANGED_TO
#undef CHANGED_ANY
#undef CHANGED_ANY_STORE_VAR

	DST.state = state;
}

static void drw_stencil_set(unsigned int mask)
{
	if (DST.stencil_mask != mask) {
		/* Stencil Write */
		if ((DST.state & DRW_STATE_WRITE_STENCIL) != 0) {
			glStencilFunc(GL_ALWAYS, mask, 0xFF);
			DST.stencil_mask = mask;
		}
		/* Stencil Test */
		else if ((DST.state & DRW_STATE_STENCIL_EQUAL) != 0) {
			glStencilFunc(GL_EQUAL, mask, 0xFF);
			DST.stencil_mask = mask;
		}
	}
}

/* Reset state to not interfer with other UI drawcall */
void DRW_state_reset_ex(DRWState state)
{
	DST.state = ~state;
	drw_state_set(state);
}

/**
 * Use with care, intended so selection code can override passes depth settings,
 * which is important for selection to work properly.
 *
 * Should be set in main draw loop, cleared afterwards
 */
void DRW_state_lock(DRWState state)
{
	DST.state_lock = state;
}

void DRW_state_reset(void)
{
	/* Reset blending function */
	glBlendFuncSeparate(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA, GL_ONE, GL_ONE_MINUS_SRC_ALPHA);

	DRW_state_reset_ex(DRW_STATE_DEFAULT);
}

/* NOTE : Make sure to reset after use! */
void DRW_state_invert_facing(void)
{
	SWAP(GLenum, DST.backface, DST.frontface);
	glFrontFace(DST.frontface);
}

/**
 * This only works if DRWPasses have been tagged with DRW_STATE_CLIP_PLANES,
 * and if the shaders have support for it (see usage of gl_ClipDistance).
 * Be sure to call DRW_state_clip_planes_reset() after you finish drawing.
 **/
void DRW_state_clip_planes_count_set(unsigned int plane_ct)
{
	BLI_assert(plane_ct <= MAX_CLIP_PLANES);
	DST.num_clip_planes = plane_ct;
}

void DRW_state_clip_planes_reset(void)
{
	DST.num_clip_planes = 0;
}

/** \} */

/* -------------------------------------------------------------------- */

/** \name Clipping (DRW_clipping)
 * \{ */

/* Extract the 8 corners (world space).
 * Although less accurate, this solution can be simplified as follows:
 *
 * BKE_boundbox_init_from_minmax(&bbox, (const float[3]){-1.0f, -1.0f, -1.0f}, (const float[3]){1.0f, 1.0f, 1.0f});
 * for (int i = 0; i < 8; i++) {mul_project_m4_v3(viewprojinv, bbox.vec[i]);}
 */
static void draw_frustum_boundbox_calc(const float (*projmat)[4], const float (*viewinv)[4], BoundBox *r_bbox)
{
	float screenvecs[3][3], loc[3], near, far, w_half, h_half;
	bool is_persp = projmat[3][3] == 0.0f;
	copy_m3_m4(screenvecs, viewinv);
	copy_v3_v3(loc, viewinv[3]);

	/* get the values of the minimum and maximum clipping planes distances
	 * and half the width and height of the nearplane rectangle. */
	if (is_persp) {
		near = projmat[3][2] / (projmat[2][2] - 1.0f);
		far = projmat[3][2] / (projmat[2][2] + 1.0f);
		w_half = near / projmat[0][0];
		h_half = near / projmat[1][1];
	}
	else {
		near = (projmat[3][2] + 1.0f) / projmat[2][2];
		far = (projmat[3][2] - 1.0f) / projmat[2][2];
		w_half = 1.0f / projmat[0][0];
		h_half = 1.0f / projmat[1][1];
	}

	/* With vectors aligned to the screen, reconstruct
	 * the near plane from the dimensions obtained earlier. */
	float mid[3], hor[3], ver[3];
	mul_v3_v3fl(hor, screenvecs[0], w_half);
	mul_v3_v3fl(ver, screenvecs[1], h_half);
	madd_v3_v3v3fl(mid, loc, screenvecs[2], -near);

	/* The case below is for non-symmetric frustum. */
	if (is_persp) {
		madd_v3_v3fl(mid, hor, projmat[2][0]);
		madd_v3_v3fl(mid, ver, projmat[2][1]);
	}
	else {
		madd_v3_v3fl(mid, hor, projmat[3][0]);
		madd_v3_v3fl(mid, ver, projmat[3][1]);
	}

	r_bbox->vec[0][0] = mid[0] - ver[0] - hor[0];
	r_bbox->vec[0][1] = mid[1] - ver[1] - hor[1];
	r_bbox->vec[0][2] = mid[2] - ver[2] - hor[2];

	r_bbox->vec[3][0] = mid[0] + ver[0] - hor[0];
	r_bbox->vec[3][1] = mid[1] + ver[1] - hor[1];
	r_bbox->vec[3][2] = mid[2] + ver[2] - hor[2];

	r_bbox->vec[7][0] = mid[0] + ver[0] + hor[0];
	r_bbox->vec[7][1] = mid[1] + ver[1] + hor[1];
	r_bbox->vec[7][2] = mid[2] + ver[2] + hor[2];

	r_bbox->vec[4][0] = mid[0] - ver[0] + hor[0];
	r_bbox->vec[4][1] = mid[1] - ver[1] + hor[1];
	r_bbox->vec[4][2] = mid[2] - ver[2] + hor[2];

	/* Get the coordinates of the far plane. */
	if (is_persp) {
		float sca_far = far / near;
		mid[0] = mid[0] + (mid[0] - loc[0]) * sca_far;
		mid[1] = mid[1] + (mid[1] - loc[1]) * sca_far;
		mid[2] = mid[2] + (mid[2] - loc[2]) * sca_far;

		mul_v3_fl(hor, sca_far);
		mul_v3_fl(ver, sca_far);
	}
	else {
		madd_v3_v3v3fl(mid, loc, screenvecs[2], -far);

		/* Non-symmetric frustum. */
		madd_v3_v3fl(mid, hor, projmat[3][0]);
		madd_v3_v3fl(mid, ver, projmat[3][1]);
	}

	r_bbox->vec[1][0] = mid[0] - ver[0] - hor[0];
	r_bbox->vec[1][1] = mid[1] - ver[1] - hor[1];
	r_bbox->vec[1][2] = mid[2] - ver[2] - hor[2];

	r_bbox->vec[2][0] = mid[0] + ver[0] - hor[0];
	r_bbox->vec[2][1] = mid[1] + ver[1] - hor[1];
	r_bbox->vec[2][2] = mid[2] + ver[2] - hor[2];

	r_bbox->vec[6][0] = mid[0] + ver[0] + hor[0];
	r_bbox->vec[6][1] = mid[1] + ver[1] + hor[1];
	r_bbox->vec[6][2] = mid[2] + ver[2] + hor[2];

	r_bbox->vec[5][0] = mid[0] - ver[0] + hor[0];
	r_bbox->vec[5][1] = mid[1] - ver[1] + hor[1];
	r_bbox->vec[5][2] = mid[2] - ver[2] + hor[2];
}

static void draw_clipping_setup_from_view(void)
{
	if (DST.clipping.updated)
		return;

	float (*viewinv)[4] = DST.view_data.matstate.mat[DRW_MAT_VIEWINV];
	float (*projmat)[4] = DST.view_data.matstate.mat[DRW_MAT_WIN];
	float (*projinv)[4] = DST.view_data.matstate.mat[DRW_MAT_WININV];
	BoundSphere *bsphere = &DST.clipping.frustum_bsphere;

	/* Extract Clipping Planes */
	BoundBox bbox;
	draw_frustum_boundbox_calc(projmat, viewinv, &bbox);

	/* Compute clip planes using the world space frustum corners. */
	for (int p = 0; p < 6; p++) {
		int q, r;
		switch (p) {
			case 0:  q=1; r=2; break;
			case 1:  q=0; r=5; break;
			case 2:  q=1; r=5; break;
			case 3:  q=2; r=6; break;
			case 4:  q=0; r=3; break;
			default: q=4; r=7; break;
		}
		if (DST.frontface == GL_CW) {
			SWAP(int, q, r);
		}

		normal_tri_v3(DST.clipping.frustum_planes[p], bbox.vec[p], bbox.vec[q], bbox.vec[r]);
		DST.clipping.frustum_planes[p][3] = -dot_v3v3(DST.clipping.frustum_planes[p], bbox.vec[p]);
	}

	/* Extract Bounding Sphere */
	if (projmat[3][3] != 0.0f) {
		/* Orthographic */
		/* The most extreme points on the near and far plane. (normalized device coords). */
		float *nearpoint = bbox.vec[0];
		float *farpoint = bbox.vec[6];

		mul_project_m4_v3(projinv, nearpoint);
		mul_project_m4_v3(projinv, farpoint);

		/* just use median point */
		mid_v3_v3v3(bsphere->center, farpoint, nearpoint);
		bsphere->radius = len_v3v3(bsphere->center, farpoint);
	}
	else if (projmat[2][0] == 0.0f && projmat[2][1] == 0.0f) {
		/* Perspective with symmetrical frustum. */

		/* We obtain the center and radius of the circumscribed circle of the
		 * isosceles trapezoid composed by the diagonals of the near and far clipping plane */

		/* center of each clipping plane */
		float mid_min[3], mid_max[3];
		mid_v3_v3v3(mid_min, bbox.vec[3], bbox.vec[4]);
		mid_v3_v3v3(mid_max, bbox.vec[2], bbox.vec[5]);

		/* square length of the diagonals of each clipping plane */
		float a_sq = len_squared_v3v3(bbox.vec[3], bbox.vec[4]);
		float b_sq = len_squared_v3v3(bbox.vec[2], bbox.vec[5]);

		/* distance squared between clipping planes */
		float h_sq = len_squared_v3v3(mid_min, mid_max);

		float fac = (4 * h_sq + b_sq - a_sq) / (8 * h_sq);
		BLI_assert(fac >= 0.0f);

		/* The goal is to get the smallest sphere,
		 * not the sphere that passes through each corner */
		CLAMP(fac, 0.0f, 1.0f);

		interp_v3_v3v3(bsphere->center, mid_min, mid_max, fac);

		/* distance from the center to one of the points of the far plane (1, 2, 5, 6) */
		bsphere->radius = len_v3v3(bsphere->center, bbox.vec[1]);
	}
	else {
		/* Perspective with asymmetrical frustum. */

		/* We put the sphere center on the line that goes from origin
		 * to the center of the far clipping plane. */

		/* Detect which of the corner of the far clipping plane is the farthest to the origin */
		float nfar[4];       /* most extreme far point in NDC space */
		float farxy[2];      /* farpoint projection onto the near plane */
		float farpoint[3] = {0.0f}; /* most extreme far point in camera coordinate */
		float nearpoint[3];  /* most extreme near point in camera coordinate */
		float farcenter[3] = {0.0f}; /* center of far cliping plane in camera coordinate */
		float F = -1.0f, N;  /* square distance of far and near point to origin */
		float f, n;          /* distance of far and near point to z axis. f is always > 0 but n can be < 0 */
		float e, s;          /* far and near clipping distance (<0) */
		float c;             /* slope of center line = distance of far clipping center to z axis / far clipping distance */
		float z;             /* projection of sphere center on z axis (<0) */

		/* Find farthest corner and center of far clip plane. */
		float corner[3] = {1.0f, 1.0f, 1.0f}; /* in clip space */
		for (int i = 0; i < 4; i++) {
			float point[3];
			mul_v3_project_m4_v3(point, projinv, corner);
			float len = len_squared_v3(point);
			if (len > F) {
				copy_v3_v3(nfar, corner);
				copy_v3_v3(farpoint, point);
				F = len;
			}
			add_v3_v3(farcenter, point);
			/* rotate by 90 degree to walk through the 4 points of the far clip plane */
			float tmp = corner[0];
			corner[0] = -corner[1];
			corner[1] = tmp;
		}

		/* the far center is the average of the far clipping points */
		mul_v3_fl(farcenter, 0.25f);
		/* the extreme near point is the opposite point on the near clipping plane */
		copy_v3_fl3(nfar, -nfar[0], -nfar[1], -1.0f);
		mul_v3_project_m4_v3(nearpoint, projinv, nfar);
		/* this is a frustum projection */
		N = len_squared_v3(nearpoint);
		e = farpoint[2];
		s = nearpoint[2];
		/* distance to view Z axis */
		f = len_v2(farpoint);
		/* get corresponding point on the near plane */
		mul_v2_v2fl(farxy, farpoint, s/e);
		/* this formula preserve the sign of n */
		sub_v2_v2(nearpoint, farxy);
		n = f * s / e - len_v2(nearpoint);
		c = len_v2(farcenter) / e;
		/* the big formula, it simplifies to (F-N)/(2(e-s)) for the symmetric case */
		z = (F-N) / (2.0f * (e-s + c*(f-n)));

		bsphere->center[0] = farcenter[0] * z/e;
		bsphere->center[1] = farcenter[1] * z/e;
		bsphere->center[2] = z;
		bsphere->radius = len_v3v3(bsphere->center, farpoint);

		/* Transform to world space. */
		mul_m4_v3(viewinv, bsphere->center);
	}

	DST.clipping.updated = true;
}

/* Return True if the given BoundSphere intersect the current view frustum */
bool DRW_culling_sphere_test(BoundSphere *bsphere)
{
	draw_clipping_setup_from_view();

	/* Bypass test if radius is negative. */
	if (bsphere->radius < 0.0f)
		return true;

	/* Do a rough test first: Sphere VS Sphere intersect. */
	BoundSphere *frustum_bsphere = &DST.clipping.frustum_bsphere;
	float center_dist = len_squared_v3v3(bsphere->center, frustum_bsphere->center);
	if (center_dist > SQUARE(bsphere->radius + frustum_bsphere->radius))
		return false;

	/* Test against the 6 frustum planes. */
	for (int p = 0; p < 6; p++) {
		float dist = plane_point_side_v3(DST.clipping.frustum_planes[p], bsphere->center);
		if (dist < -bsphere->radius) {
			return false;
		}
	}

	return true;
}

/* Return True if the given BoundBox intersect the current view frustum.
 * bbox must be in world space. */
bool DRW_culling_box_test(BoundBox *bbox)
{
	draw_clipping_setup_from_view();

	/* 6 view frustum planes */
	for (int p = 0; p < 6; p++) {
		/* 8 box vertices. */
		for (int v = 0; v < 8 ; v++) {
			float dist = plane_point_side_v3(DST.clipping.frustum_planes[p], bbox->vec[v]);
			if (dist > 0.0f) {
				/* At least one point in front of this plane.
				 * Go to next plane. */
				break;
			}
			else if (v == 7) {
				/* 8 points behind this plane. */
				return false;
			}
		}
	}

	return true;
}

/** \} */

/* -------------------------------------------------------------------- */

/** \name Draw (DRW_draw)
 * \{ */

static void draw_matrices_model_prepare(DRWCallState *st)
{
	if (st->cache_id == DST.state_cache_id) {
		return; /* Values are already updated for this view. */
	}
	else {
		st->cache_id = DST.state_cache_id;
	}

	if (DRW_culling_sphere_test(&st->bsphere)) {
		st->flag &= ~DRW_CALL_CULLED;
	}
	else {
		st->flag |= DRW_CALL_CULLED;
		return; /* No need to go further the call will not be used. */
	}

	/* Order matters */
	if (st->matflag & (DRW_CALL_MODELVIEW | DRW_CALL_MODELVIEWINVERSE |
	                  DRW_CALL_NORMALVIEW | DRW_CALL_EYEVEC))
	{
		mul_m4_m4m4(st->modelview, DST.view_data.matstate.mat[DRW_MAT_VIEW], st->model);
	}
	if (st->matflag & DRW_CALL_MODELVIEWINVERSE) {
		invert_m4_m4(st->modelviewinverse, st->modelview);
	}
	if (st->matflag & DRW_CALL_MODELVIEWPROJECTION) {
		mul_m4_m4m4(st->modelviewprojection, DST.view_data.matstate.mat[DRW_MAT_PERS], st->model);
	}
	if (st->matflag & (DRW_CALL_NORMALVIEW | DRW_CALL_EYEVEC)) {
		copy_m3_m4(st->normalview, st->modelview);
		invert_m3(st->normalview);
		transpose_m3(st->normalview);
	}
	if (st->matflag & DRW_CALL_EYEVEC) {
		/* Used by orthographic wires */
		float tmp[3][3];
		copy_v3_fl3(st->eyevec, 0.0f, 0.0f, 1.0f);
		invert_m3_m3(tmp, st->normalview);
		/* set eye vector, transformed to object coords */
		mul_m3_v3(tmp, st->eyevec);
	}
	/* Non view dependant */
	if (st->matflag & DRW_CALL_MODELINVERSE) {
		invert_m4_m4(st->modelinverse, st->model);
		st->matflag &= ~DRW_CALL_MODELINVERSE;
	}
	if (st->matflag & DRW_CALL_NORMALWORLD) {
		copy_m3_m4(st->normalworld, st->model);
		invert_m3(st->normalworld);
		transpose_m3(st->normalworld);
		st->matflag &= ~DRW_CALL_NORMALWORLD;
	}
}

static void draw_geometry_prepare(DRWShadingGroup *shgroup, DRWCallState *state)
{
	/* step 1 : bind object dependent matrices */
	if (state != NULL) {
		GPU_shader_uniform_vector(shgroup->shader, shgroup->model, 16, 1, (float *)state->model);
		GPU_shader_uniform_vector(shgroup->shader, shgroup->modelinverse, 16, 1, (float *)state->modelinverse);
		GPU_shader_uniform_vector(shgroup->shader, shgroup->modelview, 16, 1, (float *)state->modelview);
		GPU_shader_uniform_vector(shgroup->shader, shgroup->modelviewinverse, 16, 1, (float *)state->modelviewinverse);
		GPU_shader_uniform_vector(shgroup->shader, shgroup->modelviewprojection, 16, 1, (float *)state->modelviewprojection);
		GPU_shader_uniform_vector(shgroup->shader, shgroup->normalview, 9, 1, (float *)state->normalview);
		GPU_shader_uniform_vector(shgroup->shader, shgroup->normalworld, 9, 1, (float *)state->normalworld);
		GPU_shader_uniform_vector(shgroup->shader, shgroup->orcotexfac, 3, 2, (float *)state->orcotexfac);
		GPU_shader_uniform_vector(shgroup->shader, shgroup->eye, 3, 1, (float *)state->eyevec);
	}
	else {
		BLI_assert((shgroup->normalview == -1) && (shgroup->normalworld == -1) && (shgroup->eye == -1));
		/* For instancing and batching. */
		float unitmat[4][4];
		unit_m4(unitmat);
		GPU_shader_uniform_vector(shgroup->shader, shgroup->model, 16, 1, (float *)unitmat);
		GPU_shader_uniform_vector(shgroup->shader, shgroup->modelinverse, 16, 1, (float *)unitmat);
		GPU_shader_uniform_vector(shgroup->shader, shgroup->modelview, 16, 1, (float *)DST.view_data.matstate.mat[DRW_MAT_VIEW]);
		GPU_shader_uniform_vector(shgroup->shader, shgroup->modelviewinverse, 16, 1, (float *)DST.view_data.matstate.mat[DRW_MAT_VIEWINV]);
		GPU_shader_uniform_vector(shgroup->shader, shgroup->modelviewprojection, 16, 1, (float *)DST.view_data.matstate.mat[DRW_MAT_PERS]);
		GPU_shader_uniform_vector(shgroup->shader, shgroup->orcotexfac, 3, 2, (float *)shgroup->instance_orcofac);
	}
}

static void draw_geometry_execute_ex(
        DRWShadingGroup *shgroup, Gwn_Batch *geom, unsigned int start, unsigned int count, bool draw_instance)
{
	/* Special case: empty drawcall, placement is done via shader, don't bind anything. */
	if (geom == NULL) {
		BLI_assert(shgroup->type == DRW_SHG_TRIANGLE_BATCH); /* Add other type if needed. */
		/* Shader is already bound. */
		GWN_draw_primitive(GWN_PRIM_TRIS, count);
		return;
	}

	/* step 2 : bind vertex array & draw */
	GWN_batch_program_set_no_use(geom, GPU_shader_get_program(shgroup->shader), GPU_shader_get_interface(shgroup->shader));
	/* XXX hacking gawain. we don't want to call glUseProgram! (huge performance loss) */
	geom->program_in_use = true;

	GWN_batch_draw_range_ex(geom, start, count, draw_instance);

	geom->program_in_use = false; /* XXX hacking gawain */
}

static void draw_geometry_execute(DRWShadingGroup *shgroup, Gwn_Batch *geom)
{
	draw_geometry_execute_ex(shgroup, geom, 0, 0, false);
}

enum {
	BIND_NONE = 0,
	BIND_TEMP = 1,         /* Release slot after this shading group. */
	BIND_PERSIST = 2,      /* Release slot only after the next shader change. */
};

static void bind_texture(GPUTexture *tex, char bind_type)
{
	int index;
	char *slot_flags = DST.RST.bound_tex_slots;
	int bind_num = GPU_texture_bound_number(tex);
	if (bind_num == -1) {
		for (int i = 0; i < GPU_max_textures(); ++i) {
			index = DST.RST.bind_tex_inc = (DST.RST.bind_tex_inc + 1) % GPU_max_textures();
			if (slot_flags[index] == BIND_NONE) {
				if (DST.RST.bound_texs[index] != NULL) {
					GPU_texture_unbind(DST.RST.bound_texs[index]);
				}
				GPU_texture_bind(tex, index);
				DST.RST.bound_texs[index] = tex;
				slot_flags[index] = bind_type;
				// printf("Binds Texture %d %p\n", DST.RST.bind_tex_inc, tex);
				return;
			}
		}
		printf("Not enough texture slots! Reduce number of textures used by your shader.\n");
	}
	slot_flags[bind_num] = bind_type;
}

static void bind_ubo(GPUUniformBuffer *ubo, char bind_type)
{
	int index;
	char *slot_flags = DST.RST.bound_ubo_slots;
	int bind_num = GPU_uniformbuffer_bindpoint(ubo);
	if (bind_num == -1) {
		for (int i = 0; i < GPU_max_ubo_binds(); ++i) {
			index = DST.RST.bind_ubo_inc = (DST.RST.bind_ubo_inc + 1) % GPU_max_ubo_binds();
			if (slot_flags[index] == BIND_NONE) {
				if (DST.RST.bound_ubos[index] != NULL) {
					GPU_uniformbuffer_unbind(DST.RST.bound_ubos[index]);
				}
				GPU_uniformbuffer_bind(ubo, index);
				DST.RST.bound_ubos[index] = ubo;
				slot_flags[index] = bind_type;
				return;
			}
		}
		/* printf so user can report bad behaviour */
		printf("Not enough ubo slots! This should not happen!\n");
		/* This is not depending on user input.
		 * It is our responsability to make sure there is enough slots. */
		BLI_assert(0);
	}
	slot_flags[bind_num] = bind_type;
}

static void release_texture_slots(bool with_persist)
{
	if (with_persist) {
		memset(DST.RST.bound_tex_slots, 0x0, sizeof(*DST.RST.bound_tex_slots) * GPU_max_textures());
	}
	else {
		for (int i = 0; i < GPU_max_textures(); ++i) {
			if (DST.RST.bound_tex_slots[i] != BIND_PERSIST)
				DST.RST.bound_tex_slots[i] = BIND_NONE;
		}
	}

	/* Reset so that slots are consistenly assigned for different shader
	 * draw calls, to avoid shader specialization/patching by the driver. */
	DST.RST.bind_tex_inc = 0;
}

static void release_ubo_slots(bool with_persist)
{
	if (with_persist) {
		memset(DST.RST.bound_ubo_slots, 0x0, sizeof(*DST.RST.bound_ubo_slots) * GPU_max_ubo_binds());
	}
	else {
		for (int i = 0; i < GPU_max_ubo_binds(); ++i) {
			if (DST.RST.bound_ubo_slots[i] != BIND_PERSIST)
				DST.RST.bound_ubo_slots[i] = BIND_NONE;
		}
	}

	/* Reset so that slots are consistenly assigned for different shader
	 * draw calls, to avoid shader specialization/patching by the driver. */
	DST.RST.bind_ubo_inc = 0;
}

static void draw_shgroup(DRWShadingGroup *shgroup, DRWState pass_state)
{
	BLI_assert(shgroup->shader);

	GPUTexture *tex;
	GPUUniformBuffer *ubo;
	int val;
	float fval;
	const bool shader_changed = (DST.shader != shgroup->shader);

	if (shader_changed) {
		if (DST.shader) GPU_shader_unbind();
		GPU_shader_bind(shgroup->shader);
		DST.shader = shgroup->shader;
	}

	release_ubo_slots(shader_changed);
	release_texture_slots(shader_changed);

	drw_state_set((pass_state & shgroup->state_extra_disable) | shgroup->state_extra);
	drw_stencil_set(shgroup->stencil_mask);

	/* Binding Uniform */
	/* Don't check anything, Interface should already contain the least uniform as possible */
	for (DRWUniform *uni = shgroup->uniforms; uni; uni = uni->next) {
		switch (uni->type) {
			case DRW_UNIFORM_SHORT_TO_INT:
				val = (int)*((short *)uni->value);
				GPU_shader_uniform_vector_int(
				        shgroup->shader, uni->location, uni->length, uni->arraysize, (int *)&val);
				break;
			case DRW_UNIFORM_SHORT_TO_FLOAT:
				fval = (float)*((short *)uni->value);
				GPU_shader_uniform_vector(
				        shgroup->shader, uni->location, uni->length, uni->arraysize, (float *)&fval);
				break;
			case DRW_UNIFORM_BOOL:
			case DRW_UNIFORM_INT:
				GPU_shader_uniform_vector_int(
				        shgroup->shader, uni->location, uni->length, uni->arraysize, (int *)uni->value);
				break;
			case DRW_UNIFORM_FLOAT:
				GPU_shader_uniform_vector(
				        shgroup->shader, uni->location, uni->length, uni->arraysize, (float *)uni->value);
				break;
			case DRW_UNIFORM_TEXTURE:
				tex = (GPUTexture *)uni->value;
				BLI_assert(tex);
				bind_texture(tex, BIND_TEMP);
				GPU_shader_uniform_texture(shgroup->shader, uni->location, tex);
				break;
			case DRW_UNIFORM_TEXTURE_PERSIST:
				tex = (GPUTexture *)uni->value;
				BLI_assert(tex);
				bind_texture(tex, BIND_PERSIST);
				GPU_shader_uniform_texture(shgroup->shader, uni->location, tex);
				break;
			case DRW_UNIFORM_TEXTURE_REF:
				tex = *((GPUTexture **)uni->value);
				BLI_assert(tex);
				bind_texture(tex, BIND_TEMP);
				GPU_shader_uniform_texture(shgroup->shader, uni->location, tex);
				break;
			case DRW_UNIFORM_BLOCK:
				ubo = (GPUUniformBuffer *)uni->value;
				bind_ubo(ubo, BIND_TEMP);
				GPU_shader_uniform_buffer(shgroup->shader, uni->location, ubo);
				break;
			case DRW_UNIFORM_BLOCK_PERSIST:
				ubo = (GPUUniformBuffer *)uni->value;
				bind_ubo(ubo, BIND_PERSIST);
				GPU_shader_uniform_buffer(shgroup->shader, uni->location, ubo);
				break;
		}
	}

#ifdef USE_GPU_SELECT
#  define GPU_SELECT_LOAD_IF_PICKSEL(_select_id) \
	if (G.f & G_PICKSEL) { \
		GPU_select_load_id(_select_id); \
	} ((void)0)

#  define GPU_SELECT_LOAD_IF_PICKSEL_CALL(_call) \
	if ((G.f & G_PICKSEL) && (_call)) { \
		GPU_select_load_id((_call)->select_id); \
	} ((void)0)

#  define GPU_SELECT_LOAD_IF_PICKSEL_LIST(_shgroup, _start, _count)  \
	_start = 0;                                                      \
	_count = _shgroup->instance_count;                     \
	int *select_id = NULL;                                           \
	if (G.f & G_PICKSEL) {                                           \
		if (_shgroup->override_selectid == -1) {                        \
			select_id = DRW_instance_data_get(_shgroup->inst_selectid); \
			switch (_shgroup->type) {                                             \
				case DRW_SHG_TRIANGLE_BATCH: _count = 3; break;                   \
				case DRW_SHG_LINE_BATCH: _count = 2; break;                       \
				default: _count = 1; break;                                       \
			}                                                                     \
		}                                                                         \
		else {                                                                    \
			GPU_select_load_id(_shgroup->override_selectid);            \
		}                                                                         \
	}                                                                \
	while (_start < _shgroup->instance_count) {            \
		if (select_id) {                                             \
			GPU_select_load_id(select_id[_start]);                   \
		}

# define GPU_SELECT_LOAD_IF_PICKSEL_LIST_END(_start, _count) \
		_start += _count;                                    \
	}

#else
#  define GPU_SELECT_LOAD_IF_PICKSEL(select_id)
#  define GPU_SELECT_LOAD_IF_PICKSEL_CALL(call)
#  define GPU_SELECT_LOAD_IF_PICKSEL_LIST_END(start, count)
#  define GPU_SELECT_LOAD_IF_PICKSEL_LIST(_shgroup, _start, _count) \
	_start = 0;                                                     \
	_count = _shgroup->interface.instance_count;

#endif

	/* Rendering Calls */
	if (!ELEM(shgroup->type, DRW_SHG_NORMAL)) {
		/* Replacing multiple calls with only one */
		if (ELEM(shgroup->type, DRW_SHG_INSTANCE, DRW_SHG_INSTANCE_EXTERNAL)) {
			if (shgroup->type == DRW_SHG_INSTANCE_EXTERNAL) {
				if (shgroup->instance_geom != NULL) {
					GPU_SELECT_LOAD_IF_PICKSEL(shgroup->override_selectid);
					draw_geometry_prepare(shgroup, NULL);
					draw_geometry_execute_ex(shgroup, shgroup->instance_geom, 0, 0, true);
				}
			}
			else {
				if (shgroup->instance_count > 0) {
					unsigned int count, start;
					draw_geometry_prepare(shgroup, NULL);
					GPU_SELECT_LOAD_IF_PICKSEL_LIST(shgroup, start, count)
					{
						draw_geometry_execute_ex(shgroup, shgroup->instance_geom, start, count, true);
					}
					GPU_SELECT_LOAD_IF_PICKSEL_LIST_END(start, count)
				}
			}
		}
		else { /* DRW_SHG_***_BATCH */
			/* Some dynamic batch can have no geom (no call to aggregate) */
			if (shgroup->instance_count > 0) {
				unsigned int count, start;
				draw_geometry_prepare(shgroup, NULL);
				GPU_SELECT_LOAD_IF_PICKSEL_LIST(shgroup, start, count)
				{
					draw_geometry_execute_ex(shgroup, shgroup->batch_geom, start, count, false);
				}
				GPU_SELECT_LOAD_IF_PICKSEL_LIST_END(start, count)
			}
		}
	}
	else {
		bool prev_neg_scale = false;
		for (DRWCall *call = shgroup->calls.first; call; call = call->next) {

			/* OPTI/IDEA(clem): Do this preparation in another thread. */
			draw_matrices_model_prepare(call->state);

			if ((call->state->flag & DRW_CALL_CULLED) != 0)
				continue;

			/* Negative scale objects */
			bool neg_scale = call->state->flag & DRW_CALL_NEGSCALE;
			if (neg_scale != prev_neg_scale) {
				glFrontFace((neg_scale) ? DST.backface : DST.frontface);
				prev_neg_scale = neg_scale;
			}

			GPU_SELECT_LOAD_IF_PICKSEL_CALL(call);
			draw_geometry_prepare(shgroup, call->state);

			switch (call->type) {
				case DRW_CALL_SINGLE:
					draw_geometry_execute(shgroup, call->single.geometry);
					break;
				case DRW_CALL_INSTANCES:
					draw_geometry_execute_ex(shgroup, call->instances.geometry, 0, *call->instances.count, true);
					break;
				case DRW_CALL_GENERATE:
					call->generate.geometry_fn(shgroup, draw_geometry_execute, call->generate.user_data);
					break;
				default:
					BLI_assert(0);
			}
		}
		/* Reset state */
		glFrontFace(DST.frontface);
	}

	/* TODO: remove, (currently causes alpha issue with sculpt, need to investigate) */
	DRW_state_reset();
}

static void drw_update_view(void)
{
	if (DST.dirty_mat) {
		DST.state_cache_id++;
		DST.dirty_mat = false;

		DRW_uniformbuffer_update(view_ubo, &DST.view_data);

		/* Catch integer wrap around. */
		if (UNLIKELY(DST.state_cache_id == 0)) {
			DST.state_cache_id = 1;
			/* We must reset all CallStates to ensure that not
			 * a single one stayed with cache_id equal to 1. */
			BLI_mempool_iter iter;
			DRWCallState *state;
			BLI_mempool_iternew(DST.vmempool->states, &iter);
			while ((state = BLI_mempool_iterstep(&iter))) {
				state->cache_id = 0;
			}
		}

		/* TODO dispatch threads to compute matrices/culling */
	}

	draw_clipping_setup_from_view();
}

static void drw_draw_pass_ex(DRWPass *pass, DRWShadingGroup *start_group, DRWShadingGroup *end_group)
{
	DST.shader = NULL;

	BLI_assert(DST.buffer_finish_called && "DRW_render_instance_buffer_finish had not been called before drawing");

	drw_update_view();

	drw_state_set(pass->state);

	DRW_stats_query_start(pass->name);

	for (DRWShadingGroup *shgroup = start_group; shgroup; shgroup = shgroup->next) {
		draw_shgroup(shgroup, pass->state);
		/* break if upper limit */
		if (shgroup == end_group) {
			break;
		}
	}

	/* Clear Bound textures */
	for (int i = 0; i < GPU_max_textures(); i++) {
		if (DST.RST.bound_texs[i] != NULL) {
			GPU_texture_unbind(DST.RST.bound_texs[i]);
			DST.RST.bound_texs[i] = NULL;
		}
	}

	/* Clear Bound Ubos */
	for (int i = 0; i < GPU_max_ubo_binds(); i++) {
		if (DST.RST.bound_ubos[i] != NULL) {
			GPU_uniformbuffer_unbind(DST.RST.bound_ubos[i]);
			DST.RST.bound_ubos[i] = NULL;
		}
	}

	if (DST.shader) {
		GPU_shader_unbind();
		DST.shader = NULL;
	}

	DRW_stats_query_end();
}

void DRW_draw_pass(DRWPass *pass)
{
	drw_draw_pass_ex(pass, pass->shgroups.first, pass->shgroups.last);
}

/* Draw only a subset of shgroups. Used in special situations as grease pencil strokes */
void DRW_draw_pass_subset(DRWPass *pass, DRWShadingGroup *start_group, DRWShadingGroup *end_group)
{
	drw_draw_pass_ex(pass, start_group, end_group);
}

/** \} */

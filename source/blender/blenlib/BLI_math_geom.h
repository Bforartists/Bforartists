/*
 * $Id$
 *
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
 * The Original Code is Copyright (C) 2001-2002 by NaN Holding BV.
 * All rights reserved.
 *
 * The Original Code is: some of this file.
 *
 * ***** END GPL LICENSE BLOCK *****
 * */

#ifndef BLI_MATH_GEOM_H
#define BLI_MATH_GEOM_H

/** \file BLI_math_geom.h
 *  \ingroup bli
 */

#ifdef __cplusplus
extern "C" {
#endif

#include "BLI_math_inline.h"

#ifdef BLI_MATH_INLINE_H
#include "intern/math_geom_inline.c"
#endif

/********************************** Polygons *********************************/

void cent_tri_v3(float r[3], const float a[3], const float b[3], const float c[3]);
void cent_quad_v3(float r[3], const float a[3], const float b[3], const float c[3], const float d[3]);

float normal_tri_v3(float r[3], const float a[3], const float b[3], const float c[3]);
float normal_quad_v3(float r[3], const float a[3], const float b[3], const float c[3], const float d[3]);

float area_tri_v2(const float a[2], const float b[2], const float c[2]);
float area_tri_signed_v2(const float v1[2], const float v2[2], const float v3[2]);
float area_tri_v3(const float a[3], const float b[3], const float c[3]);
float area_quad_v3(const float a[3], const float b[3], const float c[3], const float d[3]);
float area_poly_v3(int nr, float verts[][3], const float normal[3]);

/********************************* Distance **********************************/

float dist_to_line_v2(const float p[2], const float l1[2], const float l2[2]);
float dist_to_line_segment_v2(const float p[2], const float l1[2], const float l2[2]);

float dist_to_line_segment_v3(const float p[3], const float l1[3], const float l2[3]);
float closest_to_line_v3(float r[3], const float p[3], const float l1[3], const float l2[3]);
float closest_to_line_v2(float r[2], const float p[2], const float l1[2], const float l2[2]);
void closest_to_line_segment_v3(float r[3], const float p[3], const float l1[3], const float l2[3]);

/******************************* Intersection ********************************/

/* TODO int return value consistency */

/* line-line */
#define ISECT_LINE_LINE_COLINEAR	-1
#define ISECT_LINE_LINE_NONE		 0
#define ISECT_LINE_LINE_EXACT		 1
#define ISECT_LINE_LINE_CROSS		 2

int isect_line_line_v2(const float a1[2], const float a2[2], const float b1[2], const float b2[2]);
int isect_line_line_v2_short(const short a1[2], const short a2[2], const short b1[2], const short b2[2]);
int isect_seg_seg_v2_point(const float v1[2], const float v2[2], const float v3[2], const float v4[2], float vi[2]);

/* Returns the number of point of interests
 * 0 - lines are colinear
 * 1 - lines are coplanar, i1 is set to intersection
 * 2 - i1 and i2 are the nearest points on line 1 (v1, v2) and line 2 (v3, v4) respectively 
 * */

int isect_line_line_v3(float v1[3], float v2[3],
	float v3[3], float v4[3], float i1[3], float i2[3]);
int isect_line_line_strict_v3(float v1[3], float v2[3],
	float v3[3], float v4[3], float vi[3], float *lambda);

/* line/ray triangle */
int isect_line_tri_v3(const float p1[3], const float p2[3],
	const float v0[3], const float v1[3], const float v2[3], float *lambda, float uv[2]);
int isect_ray_tri_v3(const float p1[3], const float d[3],
	const float v0[3], const float v1[3], const float v2[3], float *lambda, float uv[2]);
int isect_ray_tri_threshold_v3(const float p1[3], const float d[3],
	const float v0[3], const float v1[3], const float v2[3], float *lambda, float uv[2], const float threshold);
int isect_ray_tri_epsilon_v3(const float p1[3], const float d[3],
	const float v0[3], const float v1[3], const float v2[3], float *lambda, float uv[2], const float epsilon);

/* point in polygon */
int isect_point_quad_v2(const float p[2], const float a[2], const float b[2], const float c[2], const float d[2]);

int isect_point_tri_v2(const float v1[2], const float v2[2], const float v3[2], const float pt[2]);
int isect_point_tri_v2_int(const int x1, const int y1, const int x2, const int y2, const int a, const int b);
int isect_point_tri_prism_v3(const float p[3], const float v1[3], const float v2[3], const float v3[3]);

void isect_point_quad_uv_v2(const float v0[2], const float v1[2], const float v2[2], const float v3[2],
	const float pt[2], float *uv);
void isect_point_face_uv_v2(const int isquad, const float v0[2], const float v1[2], const float v2[2],
	const float v3[2], const float pt[2], float *uv);

/* other */
int isect_sweeping_sphere_tri_v3(const float p1[3], const float p2[3], const float radius,
	const float v0[3], const float v1[3], const float v2[3], float *lambda, float ipoint[3]);

int isect_axial_line_tri_v3(const int axis, const float co1[3], const float co2[3],
	const float v0[3], const float v1[3], const float v2[3], float *lambda);

int isect_aabb_aabb_v3(const float min1[3], const float max1[3], const float min2[3], const float max2[3]);

int clip_line_plane(float p1[3], float p2[3], const float plane[4]);

void plot_line_v2v2i(const int p1[2], const int p2[2], int (*callback)(int, int, void *), void *userData);

/****************************** Interpolation ********************************/

/* tri or quad, d can be NULL */
void interp_weights_face_v3(float w[4],
	const float a[3], const float b[3], const float c[3], const float d[3], const float p[3]);
void interp_weights_poly_v3(float w[], float v[][3], const int n, const float p[3]);

void interp_cubic_v3(float x[3], float v[3],
	const float x1[3], const float v1[3], const float x2[3], const float v2[3], const float t);

int interp_sparse_array(float *array, const int list_size, const float invalid);

void barycentric_transform(float pt_tar[3], float const pt_src[3],
	const float tri_tar_p1[3], const float tri_tar_p2[3], const float tri_tar_p3[3],
	const float tri_src_p1[3], const float tri_src_p2[3], const float tri_src_p3[3]);

void barycentric_weights_v2(const float v1[2], const float v2[2], const float v3[2],
	const float co[2], float w[3]);

/***************************** View & Projection *****************************/

void lookat_m4(float mat[4][4], float vx, float vy, 
	float vz, float px, float py, float pz, float twist);
void polarview_m4(float mat[4][4], float dist, float azimuth,
	float incidence, float twist);

void perspective_m4(float mat[4][4], const float left, const float right,
	const float bottom, const float top, const float nearClip, const float farClip);
void orthographic_m4(float mat[4][4], const float left, const float right,
	const float bottom, const float top, const float nearClip, const float farClip);
void window_translate_m4(float winmat[][4], float perspmat[][4],
	const float x, const float y);

int box_clip_bounds_m4(float boundbox[2][3],
	const float bounds[4], float winmat[4][4]);
void box_minmax_bounds_m4(float min[3], float max[3],
	float boundbox[2][3], float mat[4][4]);

/********************************** Mapping **********************************/

void map_to_tube(float *u, float *v, const float x, const float y, const float z);
void map_to_sphere(float *u, float *v, const float x, const float y, const float z);

/********************************** Normals **********************************/

void accumulate_vertex_normals(float n1[3], float n2[3], float n3[3],
	float n4[3], const float f_no[3], const float co1[3], const float co2[3],
	const float co3[3], const float co4[3]);

/********************************* Tangents **********************************/

typedef struct VertexTangent {
	struct VertexTangent *next;
	float tang[3], uv[2];
} VertexTangent;

float *find_vertex_tangent(VertexTangent *vtang, const float uv[2]);
void sum_or_add_vertex_tangent(void *arena, VertexTangent **vtang,
	const float tang[3], const float uv[2]);
void tangent_from_uv(float uv1[2], float uv2[2], float uv3[2],
	float co1[3], float co2[3], float co3[3], float n[3], float tang[3]);

/******************************** Vector Clouds ******************************/

void vcloud_estimate_transform(int list_size, float (*pos)[3], float *weight,
	float (*rpos)[3], float *rweight,
	float lloc[3],float rloc[3],float lrot[3][3],float lscale[3][3]);

/****************************** Spherical Harmonics *************************/

/* Uses 2nd order SH => 9 coefficients, stored in this order:
   0 = (0,0),
   1 = (1,-1), 2 = (1,0), 3 = (1,1),
   4 = (2,-2), 5 = (2,-1), 6 = (2,0), 7 = (2,1), 8 = (2,2) */

MINLINE void zero_sh(float r[9]);
MINLINE void copy_sh_sh(float r[9], const float a[9]);
MINLINE void mul_sh_fl(float r[9], const float f);
MINLINE void add_sh_shsh(float r[9], const float a[9], const float b[9]);

MINLINE float eval_shv3(float r[9], const float v[3]);
MINLINE float diffuse_shv3(float r[9], const float v[3]);
MINLINE void vec_fac_to_sh(float r[9], const float v[3], const float f);
MINLINE void madd_sh_shfl(float r[9], const float sh[3], const float f);

/********************************* Form Factor *******************************/

float form_factor_hemi_poly(float p[3], float n[3],
	float v1[3], float v2[3], float v3[3], float v4[3]);

#ifdef __cplusplus
}
#endif

#endif /* BLI_MATH_GEOM_H */


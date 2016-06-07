/*
 * Copyright 2011-2013 Blender Foundation
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

#include "camera.h"
#include "mesh.h"

#include "subd_dice.h"
#include "subd_patch.h"

#include "util_debug.h"

CCL_NAMESPACE_BEGIN

/* EdgeDice Base */

EdgeDice::EdgeDice(const SubdParams& params_)
: params(params_)
{
	mesh_P = NULL;
	mesh_N = NULL;
	vert_offset = 0;

	params.mesh->attributes.add(ATTR_STD_VERTEX_NORMAL);

	if(params.ptex) {
		params.mesh->attributes.add(ATTR_STD_PTEX_UV);
		params.mesh->attributes.add(ATTR_STD_PTEX_FACE_ID);
	}
}

void EdgeDice::reserve(int num_verts)
{
	Mesh *mesh = params.mesh;

	vert_offset = mesh->verts.size();
	tri_offset = mesh->num_triangles();

	mesh->resize_mesh(vert_offset + num_verts, tri_offset);

	Attribute *attr_vN = mesh->attributes.add(ATTR_STD_VERTEX_NORMAL);

	mesh_P = &mesh->verts[0];
	mesh_N = attr_vN->data_float3();
}

int EdgeDice::add_vert(Patch *patch, float2 uv)
{
	float3 P, N;

	patch->eval(&P, NULL, NULL, &N, uv.x, uv.y);

	assert(vert_offset < params.mesh->verts.size());

	mesh_P[vert_offset] = P;
	mesh_N[vert_offset] = N;

	if(params.ptex) {
		Attribute *attr_ptex_uv = params.mesh->attributes.add(ATTR_STD_PTEX_UV);
		params.mesh->attributes.resize();

		float3 *ptex_uv = attr_ptex_uv->data_float3();
		ptex_uv[vert_offset] = make_float3(uv.x, uv.y, 0.0f);
	}

	return vert_offset++;
}

void EdgeDice::add_triangle(Patch *patch, int v0, int v1, int v2)
{
	Mesh *mesh = params.mesh;

	/* todo: optimize so we can reserve in advance, this is like push_back_slow() */
	if(mesh->triangles.size() == mesh->triangles.capacity())
		mesh->reserve_mesh(mesh->verts.size(), size_t(max(mesh->num_triangles() + 1, 1) * 1.2));

	mesh->add_triangle(v0, v1, v2, params.shader, params.smooth, false);

	if(params.ptex) {
		Attribute *attr_ptex_face_id = params.mesh->attributes.add(ATTR_STD_PTEX_FACE_ID);
		params.mesh->attributes.resize();

		float *ptex_face_id = attr_ptex_face_id->data_float();
		ptex_face_id[tri_offset] = (float)patch->ptex_face_id();
	}

	tri_offset++;
}

void EdgeDice::stitch_triangles(Patch *patch, vector<int>& outer, vector<int>& inner)
{
	if(inner.size() == 0 || outer.size() == 0)
		return; // XXX avoid crashes for Mu or Mv == 1, missing polygons

	/* stitch together two arrays of verts with triangles. at each step,
	 * we compare using the next verts on both sides, to find the split
	 * direction with the smallest diagonal, and use that in order to keep
	 * the triangle shape reasonable. */
	for(size_t i = 0, j = 0; i+1 < inner.size() || j+1 < outer.size();) {
		int v0, v1, v2;

		v0 = inner[i];
		v1 = outer[j];

		if(j+1 == outer.size()) {
			v2 = inner[++i];
		}
		else if(i+1 == inner.size()) {
			v2 = outer[++j];
		}
		else {
			/* length of diagonals */
			float len1 = len_squared(mesh_P[inner[i]] - mesh_P[outer[j+1]]);
			float len2 = len_squared(mesh_P[outer[j]] - mesh_P[inner[i+1]]);

			/* use smallest diagonal */
			if(len1 < len2)
				v2 = outer[++j];
			else
				v2 = inner[++i];
		}

		add_triangle(patch, v0, v1, v2);
	}
}

/* QuadDice */

QuadDice::QuadDice(const SubdParams& params_)
: EdgeDice(params_)
{
}

void QuadDice::reserve(EdgeFactors& ef, int Mu, int Mv)
{
	/* XXX need to make this also work for edge factor 0 and 1 */
	int num_verts = (ef.tu0 + ef.tu1 + ef.tv0 + ef.tv1) + (Mu - 1)*(Mv - 1);
	EdgeDice::reserve(num_verts);
}

float2 QuadDice::map_uv(SubPatch& sub, float u, float v)
{
	/* map UV from subpatch to patch parametric coordinates */
	float2 d0 = interp(sub.P00, sub.P01, v);
	float2 d1 = interp(sub.P10, sub.P11, v);
	return interp(d0, d1, u);
}

float3 QuadDice::eval_projected(SubPatch& sub, float u, float v)
{
	float2 uv = map_uv(sub, u, v);
	float3 P;

	sub.patch->eval(&P, NULL, NULL, NULL, uv.x, uv.y);
	if(params.camera)
		P = transform_perspective(&params.camera->worldtoraster, P);

	return P;
}

int QuadDice::add_vert(SubPatch& sub, float u, float v)
{
	return EdgeDice::add_vert(sub.patch, map_uv(sub, u, v));
}

void QuadDice::add_side_u(SubPatch& sub,
	vector<int>& outer, vector<int>& inner,
	int Mu, int Mv, int tu, int side, int offset)
{
	outer.clear();
	inner.clear();

	/* set verts on the edge of the patch */
	outer.push_back(offset + ((side)? 2: 0));

	for(int i = 1; i < tu; i++) {
		float u = i/(float)tu;
		float v = (side)? 1.0f: 0.0f;

		outer.push_back(add_vert(sub, u, v));
	}

	outer.push_back(offset + ((side)? 3: 1));

	/* set verts on the edge of the inner grid */
	for(int i = 0; i < Mu-1; i++) {
		int j = (side)? Mv-1-1: 0;
		inner.push_back(offset + 4 + i + j*(Mu-1));
	}
}

void QuadDice::add_side_v(SubPatch& sub,
	vector<int>& outer, vector<int>& inner,
	int Mu, int Mv, int tv, int side, int offset)
{
	outer.clear();
	inner.clear();

	/* set verts on the edge of the patch */
	outer.push_back(offset + ((side)? 1: 0));

	for(int j = 1; j < tv; j++) {
		float u = (side)? 1.0f: 0.0f;
		float v = j/(float)tv;

		outer.push_back(add_vert(sub, u, v));
	}

	outer.push_back(offset + ((side)? 3: 2));

	/* set verts on the edge of the inner grid */
	for(int j = 0; j < Mv-1; j++) {
		int i = (side)? Mu-1-1: 0;
		inner.push_back(offset + 4 + i + j*(Mu-1));
	}
}

float QuadDice::quad_area(const float3& a, const float3& b, const float3& c, const float3& d)
{
	return triangle_area(a, b, d) + triangle_area(a, d, c);
}

float QuadDice::scale_factor(SubPatch& sub, EdgeFactors& ef, int Mu, int Mv)
{
	/* estimate area as 4x largest of 4 quads */
	float3 P[3][3];

	for(int i = 0; i < 3; i++)
		for(int j = 0; j < 3; j++)
			P[i][j] = eval_projected(sub, i*0.5f, j*0.5f);

	float A1 = quad_area(P[0][0], P[1][0], P[0][1], P[1][1]);
	float A2 = quad_area(P[1][0], P[2][0], P[1][1], P[2][1]);
	float A3 = quad_area(P[0][1], P[1][1], P[0][2], P[1][2]);
	float A4 = quad_area(P[1][1], P[2][1], P[1][2], P[2][2]);
	float Apatch = max(A1, max(A2, max(A3, A4)))*4.0f;

	/* solve for scaling factor */
	float Atri = params.dicing_rate*params.dicing_rate*0.5f;
	float Ntris = Apatch/Atri;

	// XXX does the -sqrt solution matter
	// XXX max(D, 0.0) is highly suspicious, need to test cases
	// where D goes negative
	float N = 0.5f*(Ntris - (ef.tu0 + ef.tu1 + ef.tv0 + ef.tv1));
	float D = 4.0f*N*Mu*Mv + (Mu + Mv)*(Mu + Mv);
	float S = (Mu + Mv + sqrtf(max(D, 0.0f)))/(2*Mu*Mv);

	return S;
}

void QuadDice::add_corners(SubPatch& sub)
{
	/* add verts for patch corners */
	add_vert(sub, 0.0f, 0.0f);
	add_vert(sub, 1.0f, 0.0f);
	add_vert(sub, 0.0f, 1.0f);
	add_vert(sub, 1.0f, 1.0f);
}

void QuadDice::add_grid(SubPatch& sub, int Mu, int Mv, int offset)
{
	/* create inner grid */
	float du = 1.0f/(float)Mu;
	float dv = 1.0f/(float)Mv;

	for(int j = 1; j < Mv; j++) {
		for(int i = 1; i < Mu; i++) {
			float u = i*du;
			float v = j*dv;

			add_vert(sub, u, v);

			if(i < Mu-1 && j < Mv-1) {
				int i1 = offset + 4 + (i-1) + (j-1)*(Mu-1);
				int i2 = offset + 4 + i + (j-1)*(Mu-1);
				int i3 = offset + 4 + i + j*(Mu-1);
				int i4 = offset + 4 + (i-1) + j*(Mu-1);

				add_triangle(sub.patch, i1, i2, i3);
				add_triangle(sub.patch, i1, i3, i4);
			}
		}
	}
}

void QuadDice::dice(SubPatch& sub, EdgeFactors& ef)
{
	/* compute inner grid size with scale factor */
	int Mu = max(ef.tu0, ef.tu1);
	int Mv = max(ef.tv0, ef.tv1);

#if 0 /* Doesnt work very well, especially at grazing angles. */
	float S = scale_factor(sub, ef, Mu, Mv);
#else
	float S = 1.0f;
#endif

	Mu = max((int)ceil(S*Mu), 2); // XXX handle 0 & 1?
	Mv = max((int)ceil(S*Mv), 2); // XXX handle 0 & 1?

	/* reserve space for new verts */
	int offset = params.mesh->verts.size();
	reserve(ef, Mu, Mv);

	/* corners and inner grid */
	add_corners(sub);
	add_grid(sub, Mu, Mv, offset);

	/* bottom side */
	vector<int> outer, inner;

	add_side_u(sub, outer, inner, Mu, Mv, ef.tu0, 0, offset);
	stitch_triangles(sub.patch, outer, inner);

	/* top side */
	add_side_u(sub, outer, inner, Mu, Mv, ef.tu1, 1, offset);
	stitch_triangles(sub.patch, inner, outer);

	/* left side */
	add_side_v(sub, outer, inner, Mu, Mv, ef.tv0, 0, offset);
	stitch_triangles(sub.patch, inner, outer);

	/* right side */
	add_side_v(sub, outer, inner, Mu, Mv, ef.tv1, 1, offset);
	stitch_triangles(sub.patch, outer, inner);

	assert(vert_offset == params.mesh->verts.size());
}

/* TriangleDice */

TriangleDice::TriangleDice(const SubdParams& params_)
: EdgeDice(params_)
{
}

void TriangleDice::reserve(EdgeFactors& ef, int M)
{
	int num_verts = ef.tu + ef.tv + ef.tw;

	for(int m = M-2; m > 0; m -= 2)
		num_verts += 3 + (m-1)*3;
	
	if(!(M & 1))
		num_verts++;
	
	EdgeDice::reserve(num_verts);
}

float2 TriangleDice::map_uv(SubPatch& sub, float2 uv)
{
	/* map UV from subpatch to patch parametric coordinates */
	return uv.x*sub.Pu + uv.y*sub.Pv + (1.0f - uv.x - uv.y)*sub.Pw;
}

int TriangleDice::add_vert(SubPatch& sub, float2 uv)
{
	return EdgeDice::add_vert(sub.patch, map_uv(sub, uv));
}

void TriangleDice::add_grid(SubPatch& sub, EdgeFactors& ef, int M)
{
	// XXX normals are flipped, why?

	/* grid is constructed starting from the outside edges, and adding
	 * progressively smaller inner triangles that connected to the outer
	 * one, until M = 1 or 2, the we fill up the last part. */
	vector<int> outer_u, outer_v, outer_w;
	int m;

	/* add outer corners vertices */
	{
		float2 p_u = make_float2(1.0f, 0.0f);
		float2 p_v = make_float2(0.0f, 1.0f);
		float2 p_w = make_float2(0.0f, 0.0f);

		int corner_u = add_vert(sub, p_u);
		int corner_v = add_vert(sub, p_v);
		int corner_w = add_vert(sub, p_w);

		outer_u.push_back(corner_v);
		outer_v.push_back(corner_w);
		outer_w.push_back(corner_u);

		for(int i = 1; i < ef.tu; i++)
			outer_u.push_back(add_vert(sub, interp(p_v, p_w, i/(float)ef.tu)));
		for(int i = 1; i < ef.tv; i++)
			outer_v.push_back(add_vert(sub, interp(p_w, p_u, i/(float)ef.tv)));
		for(int i = 1; i < ef.tw; i++)
			outer_w.push_back(add_vert(sub, interp(p_u, p_v, i/(float)ef.tw)));

		outer_u.push_back(corner_w);
		outer_v.push_back(corner_u);
		outer_w.push_back(corner_v);
	}

	for(m = M-2; m > 0; m -= 2) {
		vector<int> inner_u, inner_v, inner_w;

		const float t0 = m / (float)M;
		float2 center = make_float2(1.0f/3.0f, 1.0f/3.0f);

		/* 3 corner vertices */
		float2 p_u = interp(center, make_float2(1.0f, 0.0f), t0);
		float2 p_v = interp(center, make_float2(0.0f, 1.0f), t0);
		float2 p_w = interp(center, make_float2(0.0f, 0.0f), t0);

		int corner_u = add_vert(sub, p_u);
		int corner_v = add_vert(sub, p_v);
		int corner_w = add_vert(sub, p_w);

		/* construct array of vertex indices for each side */
		inner_u.push_back(corner_v);
		inner_v.push_back(corner_w);
		inner_w.push_back(corner_u);

		for(int i = 1; i < m; i++) {
			/* add vertices between corners */
			const float t1 = i / (float)m;

			inner_u.push_back(add_vert(sub, interp(p_v, p_w, t1)));
			inner_v.push_back(add_vert(sub, interp(p_w, p_u, t1)));
			inner_w.push_back(add_vert(sub, interp(p_u, p_v, t1)));
		}

		inner_u.push_back(corner_w);
		inner_v.push_back(corner_u);
		inner_w.push_back(corner_v);

		/* stitch together inner/outer with triangles */
		stitch_triangles(sub.patch, outer_u, inner_u);
		stitch_triangles(sub.patch, outer_v, inner_v);
		stitch_triangles(sub.patch, outer_w, inner_w);

		outer_u = inner_u;
		outer_v = inner_v;
		outer_w = inner_w;
	}

	/* fill up last part */
	if(m == -1) {
		/* single triangle */
		add_triangle(sub.patch, outer_w[0], outer_u[0], outer_v[0]);
	}
	else {
		/* center vertex + up to 6 triangles */
		int center = add_vert(sub, make_float2(1.0f/3.0f, 1.0f/3.0f));

		add_triangle(sub.patch, outer_w[0], outer_w[1], center);
		/* if this is false then there is only one triangle on this side */
		if(outer_w.size() > 2)
			add_triangle(sub.patch, outer_w[1], outer_w[2], center);

		add_triangle(sub.patch, outer_u[0], outer_u[1], center);
		if(outer_u.size() > 2)
			add_triangle(sub.patch, outer_u[1], outer_u[2], center);

		add_triangle(sub.patch, outer_v[0], outer_v[1], center);
		if(outer_v.size() > 2)
			add_triangle(sub.patch, outer_v[1], outer_v[2], center);
	}
}

void TriangleDice::dice(SubPatch& sub, EdgeFactors& ef)
{
	/* todo: handle 2 1 1 resolution */
	int M = max(ef.tu, max(ef.tv, ef.tw));

	/* Due to the "slant" of the edges of a triangle compared to a quad, the internal
	 * triangles end up smaller, causing over-tessellation. This is to correct for this
	 * difference in area. Technically its only correct for equilateral triangles, but
	 * its better than how it was.
	 *
	 * (2*cos(radians(30))/3)**0.5
	 */
	float S = 0.7598356856515927f;
	M = max((int)ceil(S*M), 1);

	reserve(ef, M);
	add_grid(sub, ef, M);

	assert(vert_offset == params.mesh->verts.size());
}

CCL_NAMESPACE_END


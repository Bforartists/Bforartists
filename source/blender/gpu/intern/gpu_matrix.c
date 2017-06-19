/*
 * ***** BEGIN GPL LICENSE BLOCK *****
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the ipmlied warranty of
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
 * The Original Code is: all of this file.
 *
 * Contributor(s): Alexandr Kuznetsov, Jason Wilkins, Mike Erwin
 *
 * ***** END GPL LICENSE BLOCK *****
 */

/** \file source/blender/gpu/intern/gpu_matrix.c
 *  \ingroup gpu
 */

#define SUPPRESS_GENERIC_MATRIX_API
#include "GPU_matrix.h"

#include "BLI_math_matrix.h"
#include "BLI_math_rotation.h"
#include "BLI_math_vector.h"


#define DEBUG_MATRIX_BIND 0

#define MATRIX_STACK_DEPTH 32

typedef float Mat4[4][4];
typedef float Mat3[3][3];

typedef struct MatrixStack {
	Mat4 stack[MATRIX_STACK_DEPTH];
	unsigned int top;
} MatrixStack;

typedef struct {
	MatrixStack model_view_stack;
	MatrixStack projection_stack;

	bool dirty;

	/* TODO: cache of derived matrices (Normal, MVP, inverse MVP, etc)
	 * generate as needed for shaders, invalidate when original matrices change
	 *
	 * TODO: separate Model from View transform? Batches/objects have model,
	 * camera/eye has view & projection
	 */
} MatrixState;

#define MATRIX_4X4_IDENTITY {{1.0f, 0.0f, 0.0f, 0.0f}, \
                             {0.0f, 1.0f, 0.0f, 0.0f}, \
                             {0.0f, 0.0f, 1.0f, 0.0f}, \
                             {0.0f, 0.0f, 0.0f, 1.0f}}

static MatrixState state = {
	.model_view_stack = {{MATRIX_4X4_IDENTITY}, 0},
	.projection_stack = {{MATRIX_4X4_IDENTITY}, 0},
	.dirty = true
};

#undef MATRIX_4X4_IDENTITY

#define ModelViewStack state.model_view_stack
#define ModelView ModelViewStack.stack[ModelViewStack.top]

#define ProjectionStack state.projection_stack
#define Projection ProjectionStack.stack[ProjectionStack.top]

void gpuMatrixReset(void)
{
	state.model_view_stack.top = 0;
	state.projection_stack.top = 0;
	unit_m4(ModelView);
	unit_m4(Projection);
	state.dirty = true;
}

#ifdef WITH_GPU_SAFETY

/* Check if matrix is numerically good */
static void checkmat(cosnt float *m)
{
	const int n = 16;
	for (int i = 0; i < n; i++) {
#if _MSC_VER
		BLI_assert(_finite(m[i]));
#else
		BLI_assert(!isinf(m[i]));
#endif
	}
}

#define CHECKMAT(m) checkmat((const float*)m)

#else

#define CHECKMAT(m)

#endif


void gpuPushMatrix(void)
{
	BLI_assert(ModelViewStack.top < MATRIX_STACK_DEPTH);
	ModelViewStack.top++;
	copy_m4_m4(ModelView, ModelViewStack.stack[ModelViewStack.top - 1]);
}

void gpuPopMatrix(void)
{
	BLI_assert(ModelViewStack.top > 0);
	ModelViewStack.top--;
	state.dirty = true;
}

void gpuPushProjectionMatrix(void)
{
	BLI_assert(ProjectionStack.top < MATRIX_STACK_DEPTH);
	ProjectionStack.top++;
	copy_m4_m4(Projection, ProjectionStack.stack[ProjectionStack.top - 1]);
}

void gpuPopProjectionMatrix(void)
{
	BLI_assert(ProjectionStack.top > 0);
	ProjectionStack.top--;
	state.dirty = true;
}

void gpuLoadMatrix(const float m[4][4])
{
	copy_m4_m4(ModelView, m);
	CHECKMAT(ModelView3D);
	state.dirty = true;
}

void gpuLoadIdentityProjectionMatrix(void)
{
	unit_m4(Projection);
	CHECKMAT(Projection3D);
	state.dirty = true;
}

void gpuLoadProjectionMatrix(const float m[4][4])
{
	copy_m4_m4(Projection, m);
	CHECKMAT(Projection3D);
	state.dirty = true;
}

void gpuLoadIdentity(void)
{
	unit_m4(ModelView);
	state.dirty = true;
}

void gpuTranslate2f(float x, float y)
{
	Mat4 m;
	unit_m4(m);
	m[3][0] = x;
	m[3][1] = y;
	gpuMultMatrix(m);
}

void gpuTranslate2fv(const float vec[2])
{
	gpuTranslate2f(vec[0], vec[1]);
}

void gpuTranslate3f(float x, float y, float z)
{
#if 1
	translate_m4(ModelView, x, y, z);
	CHECKMAT(ModelView);
#else /* above works well in early testing, below is generic version */
	Mat4 m;
	unit_m4(m);
	m[3][0] = x;
	m[3][1] = y;
	m[3][2] = z;
	gpuMultMatrix(m);
#endif
	state.dirty = true;
}

void gpuTranslate3fv(const float vec[3])
{
	gpuTranslate3f(vec[0], vec[1], vec[2]);
}

void gpuScaleUniform(float factor)
{
	Mat4 m;
	scale_m4_fl(m, factor);
	gpuMultMatrix(m);
}

void gpuScale2f(float x, float y)
{
	Mat4 m = {{0.0f}};
	m[0][0] = x;
	m[1][1] = y;
	m[2][2] = 1.0f;
	m[3][3] = 1.0f;
	gpuMultMatrix(m);
}

void gpuScale2fv(const float vec[2])
{
	gpuScale2f(vec[0], vec[1]);
}

void gpuScale3f(float x, float y, float z)
{
	Mat4 m = {{0.0f}};
	m[0][0] = x;
	m[1][1] = y;
	m[2][2] = z;
	m[3][3] = 1.0f;
	gpuMultMatrix(m);
}

void gpuScale3fv(const float vec[3])
{
	gpuScale3f(vec[0], vec[1], vec[2]);
}

void gpuMultMatrix(const float m[4][4])
{
	mul_m4_m4_post(ModelView, m);
	CHECKMAT(ModelView);
	state.dirty = true;
}

void gpuRotate2D(float deg)
{
	/* essentially RotateAxis('Z')
	 * TODO: simpler math for 2D case
	 */
	rotate_m4(ModelView, 'Z', DEG2RADF(deg));
}

void gpuRotate3f(float deg, float x, float y, float z)
{
	const float axis[3] = {x, y, z};
	gpuRotate3fv(deg, axis);
}

void gpuRotate3fv(float deg, const float axis[3])
{
	Mat4 m;
	axis_angle_to_mat4(m, axis, DEG2RADF(deg));
	gpuMultMatrix(m);
}

void gpuRotateAxis(float deg, char axis)
{
	/* rotate_m4 works in place */
	rotate_m4(ModelView, axis, DEG2RADF(deg));
	CHECKMAT(ModelView);
	state.dirty = true;
}

static void mat4_ortho_set(float m[4][4], float left, float right, float bottom, float top, float near, float far)
{
	m[0][0] = 2.0f / (right - left);
	m[1][0] = 0.0f;
	m[2][0] = 0.0f;
	m[3][0] = -(right + left) / (right - left);

	m[0][1] = 0.0f;
	m[1][1] = 2.0f / (top - bottom);
	m[2][1] = 0.0f;
	m[3][1] = -(top + bottom) / (top - bottom);

	m[0][2] = 0.0f;
	m[1][2] = 0.0f;
	m[2][2] = -2.0f / (far - near);
	m[3][2] = -(far + near) / (far - near);

	m[0][3] = 0.0f;
	m[1][3] = 0.0f;
	m[2][3] = 0.0f;
	m[3][3] = 1.0f;

	state.dirty = true;
}

static void mat4_frustum_set(float m[4][4], float left, float right, float bottom, float top, float near, float far)
{
	m[0][0] = 2.0f * near / (right - left);
	m[1][0] = 0.0f;
	m[2][0] = (right + left) / (right - left);
	m[3][0] = 0.0f;

	m[0][1] = 0.0f;
	m[1][1] = 2.0f * near / (top - bottom);
	m[2][1] = (top + bottom) / (top - bottom);
	m[3][1] = 0.0f;

	m[0][2] = 0.0f;
	m[1][2] = 0.0f;
	m[2][2] = -(far + near) / (far - near);
	m[3][2] = -2.0f * far * near / (far - near);

	m[0][3] = 0.0f;
	m[1][3] = 0.0f;
	m[2][3] = -1.0f;
	m[3][3] = 0.0f;

	state.dirty = true;
}

static void mat4_look_from_origin(float m[4][4], float lookdir[3], float camup[3])
{
/* This function is loosely based on Mesa implementation.
 *
 * SGI FREE SOFTWARE LICENSE B (Version 2.0, Sept. 18, 2008)
 * Copyright (C) 1991-2000 Silicon Graphics, Inc. All Rights Reserved.
 *
 * Permission is hereby granted, free of charge, to any person obtaining a
 * copy of this software and associated documentation files (the "Software"),
 * to deal in the Software without restriction, including without limitation
 * the rights to use, copy, modify, merge, publish, distribute, sublicense,
 * and/or sell copies of the Software, and to permit persons to whom the
 * Software is furnished to do so, subject to the following conditions:
 *
 * The above copyright notice including the dates of first publication and
 * either this permission notice or a reference to
 * http://oss.sgi.com/projects/FreeB/
 * shall be included in all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
 * OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
 * SILICON GRAPHICS, INC. BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
 * WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF
 * OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 *
 * Except as contained in this notice, the name of Silicon Graphics, Inc.
 * shall not be used in advertising or otherwise to promote the sale, use or
 * other dealings in this Software without prior written authorization from
 * Silicon Graphics, Inc.
 */

	float side[3];

	normalize_v3(lookdir);

	cross_v3_v3v3(side, lookdir, camup);

	normalize_v3(side);

	cross_v3_v3v3(camup, side, lookdir);

	m[0][0] = side[0];
	m[1][0] = side[1];
	m[2][0] = side[2];
	m[3][0] = 0.0f;

	m[0][1] = camup[0];
	m[1][1] = camup[1];
	m[2][1] = camup[2];
	m[3][1] = 0.0f;

	m[0][2] = -lookdir[0];
	m[1][2] = -lookdir[1];
	m[2][2] = -lookdir[2];
	m[3][2] = 0.0f;

	m[0][3] = 0.0f;
	m[1][3] = 0.0f;
	m[2][3] = 0.0f;
	m[3][3] = 1.0f;

	state.dirty = true;
}

void gpuOrtho(float left, float right, float bottom, float top, float near, float far)
{
	mat4_ortho_set(Projection, left, right, bottom, top, near, far);
	CHECKMAT(Projection);
	state.dirty = true;
}

void gpuOrtho2D(float left, float right, float bottom, float top)
{
	Mat4 m;
	mat4_ortho_set(m, left, right, bottom, top, -1.0f, 1.0f);
	CHECKMAT(Projection2D);
	state.dirty = true;
}

void gpuFrustum(float left, float right, float bottom, float top, float near, float far)
{
	mat4_frustum_set(Projection, left, right, bottom, top, near, far);
	CHECKMAT(Projection);
	state.dirty = true;
}

void gpuPerspective(float fovy, float aspect, float near, float far)
{
	float half_height = tanf(fovy * (float)(M_PI / 360.0)) * near;
	float half_width = half_height * aspect;
	gpuFrustum(-half_width, +half_width, -half_height, +half_height, near, far);
}

void gpuLookAt(float eyeX, float eyeY, float eyeZ, float centerX, float centerY, float centerZ, float upX, float upY, float upZ)
{
	Mat4 cm;
	float lookdir[3];
	float camup[3] = {upX, upY, upZ};

	lookdir[0] = centerX - eyeX;
	lookdir[1] = centerY - eyeY;
	lookdir[2] = centerZ - eyeZ;

	mat4_look_from_origin(cm, lookdir, camup);

	gpuMultMatrix(cm);
	gpuTranslate3f(-eyeX, -eyeY, -eyeZ);
}

void gpuProject(const float world[3], const float model[4][4], const float proj[4][4], const int view[4], float win[3])
{
	float v[4];

	mul_v4_m4v3(v, model, world);
	mul_m4_v4(proj, v);

	if (v[3] != 0.0f) {
		mul_v3_fl(v, 1.0f / v[3]);
	}

	win[0] = view[0] + (view[2] * (v[0] + 1)) * 0.5f;
	win[1] = view[1] + (view[3] * (v[1] + 1)) * 0.5f;
	win[2] = (v[2] + 1) * 0.5f;
}

bool gpuUnProject(const float win[3], const float model[4][4], const float proj[4][4], const int view[4], float world[3])
{
	float pm[4][4];
	float in[4];
	float out[4];

	mul_m4_m4m4(pm, proj, model);

	if (!invert_m4(pm)) {
		zero_v3(world);
		return false;
	}

	in[0] = win[0];
	in[1] = win[1];
	in[2] = win[2];
	in[3] = 1;

	/* Map x and y from window coordinates */
	in[0] = (in[0] - view[0]) / view[2];
	in[1] = (in[1] - view[1]) / view[3];

	/* Map to range -1 to +1 */
	in[0] = 2 * in[0] - 1;
	in[1] = 2 * in[1] - 1;
	in[2] = 2 * in[2] - 1;

	mul_v4_m4v3(out, pm, in);

	if (out[3] == 0.0f) {
		copy_v3_v3(world, out);
		return false;
	}

	mul_v3_v3fl(world, out, 1.0f / out[3]);
	return true;
}

const float (*gpuGetModelViewMatrix(float m[4][4]))[4]
{
	if (m) {
		copy_m4_m4(m, ModelView);
		return m;
	}
	else {
		return ModelView;
	}
}

const float (*gpuGetProjectionMatrix(float m[4][4]))[4]
{
	if (m) {
		copy_m4_m4(m, Projection);
		return m;
	}
	else {
		return Projection;
	}
}

const float (*gpuGetModelViewProjectionMatrix(float m[4][4]))[4]
{
	if (m == NULL) {
		static Mat4 temp;
		m = temp;
	}

	mul_m4_m4m4(m, Projection, ModelView);
	return m;
}

const float (*gpuGetNormalMatrix(float m[3][3]))[3]
{
	if (m == NULL) {
		static Mat3 temp3;
		m = temp3;
	}

	copy_m3_m4(m, (const float (*)[4])gpuGetModelViewMatrix(NULL));

	invert_m3(m);
	transpose_m3(m);

	return m;
}

const float (*gpuGetNormalMatrixInverse(float m[3][3]))[3]
{
	if (m == NULL) {
		static Mat3 temp3;
		m = temp3;
	}

	gpuGetNormalMatrix(m);
	invert_m3(m);

	return m;
}

void gpuBindMatrices(const Gwn_ShaderInterface* shaderface)
{
	/* set uniform values to matrix stack values
	 * call this before a draw call if desired matrices are dirty
	 * call glUseProgram before this, as glUniform expects program to be bound
	 */

	const Gwn_ShaderInput *MV = GWN_shaderinterface_uniform_builtin(shaderface, GWN_UNIFORM_MODELVIEW);
	const Gwn_ShaderInput *P = GWN_shaderinterface_uniform_builtin(shaderface, GWN_UNIFORM_PROJECTION);
	const Gwn_ShaderInput *MVP = GWN_shaderinterface_uniform_builtin(shaderface, GWN_UNIFORM_MVP);

	const Gwn_ShaderInput *N = GWN_shaderinterface_uniform_builtin(shaderface, GWN_UNIFORM_NORMAL);
	const Gwn_ShaderInput *MV_inv = GWN_shaderinterface_uniform_builtin(shaderface, GWN_UNIFORM_MODELVIEW_INV);
	const Gwn_ShaderInput *P_inv = GWN_shaderinterface_uniform_builtin(shaderface, GWN_UNIFORM_PROJECTION_INV);

	if (MV) {
		#if DEBUG_MATRIX_BIND
		puts("setting MV matrix");
		#endif

		glUniformMatrix4fv(MV->location, 1, GL_FALSE, (const float *)gpuGetModelViewMatrix(NULL));
	}

	if (P) {
		#if DEBUG_MATRIX_BIND
		puts("setting P matrix");
		#endif

		glUniformMatrix4fv(P->location, 1, GL_FALSE, (const float *)gpuGetProjectionMatrix(NULL));
	}

	if (MVP) {
		#if DEBUG_MATRIX_BIND
		puts("setting MVP matrix");
		#endif

		glUniformMatrix4fv(MVP->location, 1, GL_FALSE, (const float *)gpuGetModelViewProjectionMatrix(NULL));
	}

	if (N) {
		#if DEBUG_MATRIX_BIND
		puts("setting normal matrix");
		#endif

		glUniformMatrix3fv(N->location, 1, GL_FALSE, (const float *)gpuGetNormalMatrix(NULL));
	}

	if (MV_inv) {
		Mat4 m;
		gpuGetModelViewMatrix(m);
		invert_m4(m);
		glUniformMatrix4fv(MV_inv->location, 1, GL_FALSE, (const float*) m);
	}

	if (P_inv) {
		Mat4 m;
		gpuGetProjectionMatrix(m);
		invert_m4(m);
		glUniformMatrix4fv(P_inv->location, 1, GL_FALSE, (const float*) m);
	}

	state.dirty = false;
}

bool gpuMatricesDirty(void)
{
	return state.dirty;
}

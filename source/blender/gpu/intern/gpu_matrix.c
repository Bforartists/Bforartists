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

#include "GPU_matrix.h"

#include "BLI_math_matrix.h"
#include "BLI_math_rotation.h"
#include "BLI_math_vector.h"


#define DEBUG_MATRIX_BIND 0

#define MATRIX_STACK_DEPTH 32

typedef float Mat4[4][4];
typedef float Mat3[3][3];

typedef struct {
	Mat4 ModelViewStack3D[MATRIX_STACK_DEPTH];
	Mat4 ProjectionMatrix3D;

	Mat3 ModelViewStack2D[MATRIX_STACK_DEPTH];
	Mat3 ProjectionMatrix2D;

	MatrixMode mode;
	unsigned top; /* of current stack (would have to replicate if gpuResume2D/3D are implemented) */
	
	/* TODO: cache of derived matrices (Normal, MVP, inverse MVP, etc)
	 * generate as needed for shaders, invalidate when original matrices change
	 *
	 * TODO: separate Model from View transform? Batches/objects have model,
	 * camera/eye has view & projection
	 */
} MatrixState;

static MatrixState state; /* TODO(merwin): make part of GPUContext, alongside immediate mode & state tracker */

#define ModelView3D state.ModelViewStack3D[state.top]
#define ModelView2D state.ModelViewStack2D[state.top]
#define Projection3D state.ProjectionMatrix3D
#define Projection2D state.ProjectionMatrix2D

void gpuMatrixInit()
{
	memset(&state, 0, sizeof(MatrixState));
}

void gpuMatrixBegin2D()
{
	state.mode = MATRIX_MODE_2D;
	state.top = 0;
	unit_m3(ModelView2D);
	gpuOrtho2D(-1.0f, +1.0f, -1.0f, +1.0f); // or identity?
}

void gpuMatrixBegin3D()
{
	state.mode = MATRIX_MODE_3D;
	state.top = 0;
	unit_m4(ModelView3D);
	gpuOrtho(-1.0f, +1.0f, -1.0f, +1.0f, -1.0f, +1.0f); // or identity?
}

#if SUPPORT_LEGACY_MATRIX
void gpuMatrixBegin3D_legacy() {
	/* copy top matrix from each legacy stack into new fresh stack */
	state.mode = MATRIX_MODE_3D;
	state.top = 0;
	glGetFloatv(GL_MODELVIEW_MATRIX, (float*)ModelView3D);
	glGetFloatv(GL_PROJECTION_MATRIX, (float*)Projection3D);
}
#endif

void gpuMatrixEnd()
{
	state.mode = MATRIX_MODE_INACTIVE;
}


#ifdef WITH_GPU_SAFETY

/* Check if matrix is numerically good */
static void checkmat(cosnt float *m)
{
	const int n = state.mode == MATRIX_MODE_3D ? 16 : 9;
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


void gpuPushMatrix()
{
	BLI_assert(state.mode != MATRIX_MODE_INACTIVE);
	BLI_assert(state.top < MATRIX_STACK_DEPTH);
	state.top++;
	if (state.mode == MATRIX_MODE_3D)
		copy_m4_m4(ModelView3D, state.ModelViewStack3D[state.top - 1]);
	else
		copy_m3_m3(ModelView2D, state.ModelViewStack2D[state.top - 1]);
}

void gpuPopMatrix()
{
	BLI_assert(state.mode != MATRIX_MODE_INACTIVE);
	BLI_assert(state.top > 0);
	state.top--;
}

void gpuLoadMatrix3D(const float m[4][4])
{
	BLI_assert(state.mode == MATRIX_MODE_3D);
	copy_m4_m4(ModelView3D, m);
	CHECKMAT(ModelView3D);
}

void gpuLoadMatrix2D(const float m[3][3])
{
	BLI_assert(state.mode == MATRIX_MODE_2D);
	copy_m3_m3(ModelView2D, m);
	CHECKMAT(ModelView2D);
}

void gpuLoadIdentity()
{
	switch (state.mode) {
		case MATRIX_MODE_3D:
			unit_m4(ModelView3D);
			break;
		case MATRIX_MODE_2D:
			unit_m3(ModelView2D);
			break;
		default:
			BLI_assert(false);
	}
}

void gpuTranslate2f(float x, float y)
{
	Mat3 m;
	unit_m3(m);
	m[2][0] = x;
	m[2][1] = y;
	gpuMultMatrix2D(m);
}

void gpuTranslate2fv(const float vec[2])
{
	gpuTranslate2f(vec[0], vec[1]);
}

void gpuTranslate3f(float x, float y, float z)
{
#if 1
	BLI_assert(state.mode == MATRIX_MODE_3D);
	translate_m4(ModelView3D, x, y, z);
	CHECKMAT(ModelView3D);
#else /* above works well in early testing, below is generic version */
	Mat4 m;
	unit_m4(m);
	m[3][0] = x;
	m[3][1] = y;
	m[3][2] = z;
	gpuMultMatrix3D(m);
#endif
}

void gpuTranslate3fv(const float vec[3])
{
	gpuTranslate3f(vec[0], vec[1], vec[2]);
}

void gpuScaleUniform(float factor)
{
	switch (state.mode) {
		case MATRIX_MODE_3D:
		{
			Mat4 m;
			scale_m4_fl(m, factor);
			gpuMultMatrix3D(m);
			break;
		}
		case MATRIX_MODE_2D:
		{
		#if 0
			Mat3 m;
			scale_m3_fl(m, factor);
			/* this does 3D scaling in a 3x3 matrix. Can 2D scaling use this safely, or must set m[2][2] = 1.0? */
		#else
			Mat3 m = {{0.0f}};
			m[0][0] = factor;
			m[1][1] = factor;
			m[2][2] = 1.0f;
		#endif
			gpuMultMatrix2D(m);
			break;
		}
		default:
			BLI_assert(false);
	}
}

void gpuScale2f(float x, float y)
{
	Mat3 m = {{0.0f}};
	m[0][0] = x;
	m[1][1] = y;
	m[2][2] = 1.0f;
	gpuMultMatrix2D(m);
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
	gpuMultMatrix3D(m);
}

void gpuScale3fv(const float vec[3])
{
	gpuScale3f(vec[0], vec[1], vec[2]);
}

void gpuMultMatrix3D(const float m[4][4])
{
	BLI_assert(state.mode == MATRIX_MODE_3D);
	mul_m4_m4_pre(ModelView3D, m);
	CHECKMAT(ModelView3D);
}

void gpuMultMatrix2D(const float m[3][3])
{
	BLI_assert(state.mode == MATRIX_MODE_2D);
	mul_m3_m3_pre(ModelView2D, m);
	CHECKMAT(ModelView2D);
}

void gpuRotate3fv(float deg, const float axis[3])
{
	Mat4 m;
	axis_angle_to_mat4(m, axis, DEG2RADF(deg));
	gpuMultMatrix3D(m);
}

void gpuRotateAxis(float deg, char axis)
{
#if 1 /* rotate_m4 works in place, right? */
	BLI_assert(state.mode == MATRIX_MODE_3D);
	rotate_m4(ModelView3D, axis, DEG2RADF(deg));
	CHECKMAT(ModelView3D);
#else /* rotate_m4 creates a new matrix */
	Mat4 m;
	rotate_m4(m, axis, DEG2RADF(deg));
	gpuMultMatrix3D(m);
#endif
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
}

static void mat4_frustum_set(float m[][4], float left, float right, float bottom, float top, float near, float far)
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
}

void gpuOrtho(float left, float right, float bottom, float top, float near, float far)
{
	BLI_assert(state.mode == MATRIX_MODE_3D);
	mat4_ortho_set(Projection3D, left, right, bottom, top, near, far);
	CHECKMAT(Projection3D);
}

void gpuOrtho2D(float left, float right, float bottom, float top)
{
	/* TODO: this function, but correct */
	BLI_assert(state.mode == MATRIX_MODE_2D);
	Mat4 m;
	mat4_ortho_set(m, left, right, bottom, top, -1.0f, 1.0f);
	copy_m3_m4(Projection2D, m);
	CHECKMAT(Projection2D);
}

void gpuFrustum(float left, float right, float bottom, float top, float near, float far)
{
	BLI_assert(state.mode == MATRIX_MODE_3D);
	mat4_frustum_set(Projection3D, left, right, bottom, top, near, far);
	CHECKMAT(Projection3D);
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

	gpuMultMatrix3D(cm);
	gpuTranslate3f(-eyeX, -eyeY, -eyeZ);
}

void gpuProject(const float obj[3], const float model[4][4], const float proj[4][4], const GLint view[4], float win[3])
{
	float v[4];

	mul_v4_m4v3(v, model, obj);
	mul_m4_v4(proj, v);

	win[0] = view[0] + (view[2] * (v[0] + 1)) * 0.5f;
	win[1] = view[1] + (view[3] * (v[1] + 1)) * 0.5f;
	win[2] = (v[2] + 1) * 0.5f;
}

bool gpuUnProject(const float win[3], const float model[4][4], const float proj[4][4], const GLint view[4], float obj[3])
{
	float pm[4][4];
	float in[4];
	float out[4];

	mul_m4_m4m4(pm, proj, model);

	if (!invert_m4(pm)) {
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
		return false;
	}
	else {
		out[0] /= out[3];
		out[1] /= out[3];
		out[2] /= out[3];

		obj[0] = out[0];
		obj[1] = out[1];
		obj[2] = out[2];

		return true;
	}
}

const float *gpuGetModelViewMatrix3D(float m[4][4])
{
#if SUPPORT_LEGACY_MATRIX
	if (state.mode == MATRIX_MODE_INACTIVE) {
		if (m == NULL) {
			static Mat4 temp;
			m = temp;
		}

		glGetFloatv(GL_MODELVIEW_MATRIX, (float*)m);
		return (const float*)m;		
	}
#endif

	BLI_assert(state.mode == MATRIX_MODE_3D);

	if (m) {
		copy_m4_m4(m, ModelView3D);
		return (const float*)m;
	}
	else {
		return (const float*)ModelView3D;
	}
}

const float *gpuGetProjectionMatrix3D(float m[4][4])
{
#if SUPPORT_LEGACY_MATRIX
	if (state.mode == MATRIX_MODE_INACTIVE) {
		if (m == NULL) {
			static Mat4 temp;
			m = temp;
		}

		glGetFloatv(GL_PROJECTION_MATRIX, (float*)m);
		return (const float*)m;
	}
#endif

	BLI_assert(state.mode == MATRIX_MODE_3D);

	if (m) {
		copy_m4_m4(m, ModelView3D);
		return (const float*)m;
	}
	else {
		return (const float*)ModelView3D;
	}
}

const float *gpuGetModelViewProjectionMatrix3D(float m[4][4])
{
#if SUPPORT_LEGACY_MATRIX
	if (state.mode == MATRIX_MODE_INACTIVE) {
		if (m == NULL) {
			static Mat4 temp;
			m = temp;
		}

		Mat4 proj;
		glGetFloatv(GL_MODELVIEW_MATRIX, (float*)proj);
		glGetFloatv(GL_PROJECTION_MATRIX, (float*)m);
		mul_m4_m4_post(m, proj);
		return (const float*)m;
	}
#endif

	BLI_assert(state.mode == MATRIX_MODE_3D);

	if (m == NULL) {
		static Mat4 temp;
		m = temp;
	}

	mul_m4_m4m4(m, Projection3D, ModelView3D);
	return (const float*)m;
}

void gpuBindMatrices(GLuint program)
{
	/* TODO: split this into 2 functions
	 * 1) get uniform locations & determine 2D or 3D
	 */
	GLint loc_MV = glGetUniformLocation(program, "ModelViewMatrix");
	GLint loc_P = glGetUniformLocation(program, "ProjectionMatrix");
	GLint loc_MVP = glGetUniformLocation(program, "ModelViewProjectionMatrix");

	/* 2) set uniform values to matrix stack values
	 * program needs to be bound
	 */
	glUseProgram(program);


	/* call this portion before a draw call if desired matrices are dirty */
	if (loc_MV != -1) {
		#if DEBUG_MATRIX_BIND
		puts("setting 3D MV matrix");
		#endif

		glUniformMatrix4fv(loc_MV, 1, GL_FALSE, gpuGetModelViewMatrix3D(NULL));
	}

	if (loc_P != -1) {
		#if DEBUG_MATRIX_BIND
		puts("setting 3D P matrix");
		#endif

		glUniformMatrix4fv(loc_P, 1, GL_FALSE, gpuGetProjectionMatrix3D(NULL));
	}

	if (loc_MVP != -1) {
		#if DEBUG_MATRIX_BIND
		puts("setting 3D MVP matrix");
		#endif

		glUniformMatrix4fv(loc_MVP, 1, GL_FALSE, gpuGetModelViewProjectionMatrix3D(NULL));
	}
}

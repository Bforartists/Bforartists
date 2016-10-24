#ifndef _GPU_MATRIX_H_
#define _GPU_MATRIX_H_

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
 * The Original Code is: all of this file.
 *
 * Contributor(s): Alexandr Kuznetsov, Jason Wilkins, Mike Erwin
 *
 * ***** END GPL LICENSE BLOCK *****
 */

/** \file source/blender/gpu/GPU_matrix.h
 *  \ingroup gpu
 */

#include "GPU_glew.h"
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

/* For now we support the legacy matrix stack in gpuGetMatrix functions.
 * Will remove this after switching to core profile, which can happen after
 * we convert all code to use the API in this file. */
#define SUPPORT_LEGACY_MATRIX 1


void gpuMatrixInit(void); /* called by system -- make private? */


/* MatrixMode is conceptually different from GL_MATRIX_MODE */

typedef enum {
	MATRIX_MODE_INACTIVE,
	MATRIX_MODE_2D,
	MATRIX_MODE_3D
} MatrixMode;

MatrixMode gpuMatrixMode(void);

void gpuMatrixBegin2D(void);
void gpuMatrixBegin3D(void);
void gpuMatrixEnd(void);
/* TODO: gpuMatrixResume2D & gpuMatrixResume3D to switch modes but not reset stack */


/* ModelView Matrix (2D or 3D) */

void gpuPushMatrix(void); /* TODO: PushCopy vs PushIdentity? */
void gpuPopMatrix(void);

void gpuLoadIdentity(void);

void gpuScaleUniform(float factor);


/* 3D ModelView Matrix */

void gpuLoadMatrix3D(const float m[4][4]);
void gpuMultMatrix3D(const float m[4][4]);
//const float *gpuGetMatrix3D(float m[4][4]);

void gpuTranslate3f(float x, float y, float z);
void gpuTranslate3fv(const float vec[3]);
void gpuScale3f(float x, float y, float z);
void gpuScale3fv(const float vec[3]);
void gpuRotate3fv(float deg, const float axis[3]); /* axis of rotation should be a unit vector */
void gpuRotateAxis(float deg, char axis); /* TODO: enum for axis? */

void gpuLookAt(float eyeX, float eyeY, float eyeZ, float centerX, float centerY, float centerZ, float upX, float upY, float upZ);
/* TODO: variant that takes eye[3], center[3], up[3] */


/* 2D ModelView Matrix */

void gpuLoadMatrix2D(const float m[3][3]);
void gpuMultMatrix2D(const float m[3][3]);

void gpuTranslate2f(float x, float y);
void gpuTranslate2fv(const float vec[2]);
void gpuScale2f(float x, float y);
void gpuScale2fv(const float vec[2]);
void gpuRotate2D(float deg);


/* 3D Projection Matrix */

void gpuOrtho(float left, float right, float bottom, float top, float near, float far);
void gpuFrustum(float left, float right, float bottom, float top, float near, float far);
void gpuPerspective(float fovy, float aspect, float near, float far);

/* pass vector through current transform (world --> screen) */
void gpuProject(const float obj[3], const float model[4][4], const float proj[4][4], const GLint view[4], float win[3]);

/* pass vector through inverse transform (world <-- screen) */
bool gpuUnProject(const float win[3], const float model[4][4], const float proj[4][4], const GLint view[4], float obj[3]);


/* 2D Projection Matrix */

void gpuOrtho2D(float left, float right, float bottom, float top);


/* functions to get matrix values */
const float *gpuGetModelViewMatrix3D(float m[4][4]);
const float *gpuGetProjectionMatrix3D(float m[4][4]);
const float *gpuGetModelViewProjectionMatrix3D(float m[4][4]);

const float *gpuGetNormalMatrix(float m[3][3]);
const float *gpuGetNormalMatrixInverse(float m[3][3]);


#if SUPPORT_LEGACY_MATRIX
/* copy top matrix from each legacy stack into new fresh stack */
void gpuMatrixBegin3D_legacy(void);
#endif


/* set uniform values for currently bound shader */
void gpuBindMatrices(GLuint program);
bool gpuMatricesDirty(void); /* since last bind */

#ifdef __cplusplus
}
#endif

#endif /* GPU_MATRIX_H */

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
 * The Original Code is Copyright (C) 2012 Blender Foundation.
 * All rights reserved.
 */

/** \file
 * \ingroup gpu
 */

#include "GPU_shader_interface.h"

#include "gpu_context_private.h"
#include "gpu_matrix_private.h"

#define SUPPRESS_GENERIC_MATRIX_API
#define USE_GPU_PY_MATRIX_API /* only so values are declared */
#include "GPU_matrix.h"
#undef USE_GPU_PY_MATRIX_API

#include "BLI_math_matrix.h"
#include "BLI_math_rotation.h"
#include "BLI_math_vector.h"

#include "MEM_guardedalloc.h"

#define DEBUG_MATRIX_BIND 0

#define MATRIX_STACK_DEPTH 32

typedef float Mat4[4][4];
typedef float Mat3[3][3];

typedef struct MatrixStack {
  Mat4 stack[MATRIX_STACK_DEPTH];
  uint top;
} MatrixStack;

typedef struct GPUMatrixState {
  MatrixStack model_view_stack;
  MatrixStack projection_stack;

  bool dirty;

  /* TODO: cache of derived matrices (Normal, MVP, inverse MVP, etc)
   * generate as needed for shaders, invalidate when original matrices change
   *
   * TODO: separate Model from View transform? Batches/objects have model,
   * camera/eye has view & projection
   */
} GPUMatrixState;

#define ModelViewStack gpu_context_active_matrix_state_get()->model_view_stack
#define ModelView ModelViewStack.stack[ModelViewStack.top]

#define ProjectionStack gpu_context_active_matrix_state_get()->projection_stack
#define Projection ProjectionStack.stack[ProjectionStack.top]

GPUMatrixState *GPU_matrix_state_create(void)
{
#define MATRIX_4X4_IDENTITY \
  { \
    {1.0f, 0.0f, 0.0f, 0.0f}, {0.0f, 1.0f, 0.0f, 0.0f}, {0.0f, 0.0f, 1.0f, 0.0f}, \
    { \
      0.0f, 0.0f, 0.0f, 1.0f \
    } \
  }

  GPUMatrixState *state = MEM_mallocN(sizeof(*state), __func__);
  const MatrixStack identity_stack = {{MATRIX_4X4_IDENTITY}, 0};

  state->model_view_stack = state->projection_stack = identity_stack;
  state->dirty = true;

#undef MATRIX_4X4_IDENTITY

  return state;
}

void GPU_matrix_state_discard(GPUMatrixState *state)
{
  MEM_freeN(state);
}

static void gpu_matrix_state_active_set_dirty(bool value)
{
  GPUMatrixState *state = gpu_context_active_matrix_state_get();
  state->dirty = value;
}

void GPU_matrix_reset(void)
{
  GPUMatrixState *state = gpu_context_active_matrix_state_get();
  state->model_view_stack.top = 0;
  state->projection_stack.top = 0;
  unit_m4(ModelView);
  unit_m4(Projection);
  gpu_matrix_state_active_set_dirty(true);
}

#ifdef WITH_GPU_SAFETY

/* Check if matrix is numerically good */
static void checkmat(cosnt float *m)
{
  const int n = 16;
  for (int i = 0; i < n; i++) {
#  if _MSC_VER
    BLI_assert(_finite(m[i]));
#  else
    BLI_assert(!isinf(m[i]));
#  endif
  }
}

#  define CHECKMAT(m) checkmat((const float *)m)

#else

#  define CHECKMAT(m)

#endif

void GPU_matrix_push(void)
{
  BLI_assert(ModelViewStack.top + 1 < MATRIX_STACK_DEPTH);
  ModelViewStack.top++;
  copy_m4_m4(ModelView, ModelViewStack.stack[ModelViewStack.top - 1]);
}

void GPU_matrix_pop(void)
{
  BLI_assert(ModelViewStack.top > 0);
  ModelViewStack.top--;
  gpu_matrix_state_active_set_dirty(true);
}

void GPU_matrix_push_projection(void)
{
  BLI_assert(ProjectionStack.top + 1 < MATRIX_STACK_DEPTH);
  ProjectionStack.top++;
  copy_m4_m4(Projection, ProjectionStack.stack[ProjectionStack.top - 1]);
}

void GPU_matrix_pop_projection(void)
{
  BLI_assert(ProjectionStack.top > 0);
  ProjectionStack.top--;
  gpu_matrix_state_active_set_dirty(true);
}

void GPU_matrix_set(const float m[4][4])
{
  copy_m4_m4(ModelView, m);
  CHECKMAT(ModelView3D);
  gpu_matrix_state_active_set_dirty(true);
}

void GPU_matrix_identity_projection_set(void)
{
  unit_m4(Projection);
  CHECKMAT(Projection3D);
  gpu_matrix_state_active_set_dirty(true);
}

void GPU_matrix_projection_set(const float m[4][4])
{
  copy_m4_m4(Projection, m);
  CHECKMAT(Projection3D);
  gpu_matrix_state_active_set_dirty(true);
}

void GPU_matrix_identity_set(void)
{
  unit_m4(ModelView);
  gpu_matrix_state_active_set_dirty(true);
}

void GPU_matrix_translate_2f(float x, float y)
{
  Mat4 m;
  unit_m4(m);
  m[3][0] = x;
  m[3][1] = y;
  GPU_matrix_mul(m);
}

void GPU_matrix_translate_2fv(const float vec[2])
{
  GPU_matrix_translate_2f(vec[0], vec[1]);
}

void GPU_matrix_translate_3f(float x, float y, float z)
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
  GPU_matrix_mul(m);
#endif
  gpu_matrix_state_active_set_dirty(true);
}

void GPU_matrix_translate_3fv(const float vec[3])
{
  GPU_matrix_translate_3f(vec[0], vec[1], vec[2]);
}

void GPU_matrix_scale_1f(float factor)
{
  Mat4 m;
  scale_m4_fl(m, factor);
  GPU_matrix_mul(m);
}

void GPU_matrix_scale_2f(float x, float y)
{
  Mat4 m = {{0.0f}};
  m[0][0] = x;
  m[1][1] = y;
  m[2][2] = 1.0f;
  m[3][3] = 1.0f;
  GPU_matrix_mul(m);
}

void GPU_matrix_scale_2fv(const float vec[2])
{
  GPU_matrix_scale_2f(vec[0], vec[1]);
}

void GPU_matrix_scale_3f(float x, float y, float z)
{
  Mat4 m = {{0.0f}};
  m[0][0] = x;
  m[1][1] = y;
  m[2][2] = z;
  m[3][3] = 1.0f;
  GPU_matrix_mul(m);
}

void GPU_matrix_scale_3fv(const float vec[3])
{
  GPU_matrix_scale_3f(vec[0], vec[1], vec[2]);
}

void GPU_matrix_mul(const float m[4][4])
{
  mul_m4_m4_post(ModelView, m);
  CHECKMAT(ModelView);
  gpu_matrix_state_active_set_dirty(true);
}

void GPU_matrix_rotate_2d(float deg)
{
  /* essentially RotateAxis('Z')
   * TODO: simpler math for 2D case
   */
  rotate_m4(ModelView, 'Z', DEG2RADF(deg));
}

void GPU_matrix_rotate_3f(float deg, float x, float y, float z)
{
  const float axis[3] = {x, y, z};
  GPU_matrix_rotate_3fv(deg, axis);
}

void GPU_matrix_rotate_3fv(float deg, const float axis[3])
{
  Mat4 m;
  axis_angle_to_mat4(m, axis, DEG2RADF(deg));
  GPU_matrix_mul(m);
}

void GPU_matrix_rotate_axis(float deg, char axis)
{
  /* rotate_m4 works in place */
  rotate_m4(ModelView, axis, DEG2RADF(deg));
  CHECKMAT(ModelView);
  gpu_matrix_state_active_set_dirty(true);
}

static void mat4_ortho_set(
    float m[4][4], float left, float right, float bottom, float top, float near, float far)
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

  gpu_matrix_state_active_set_dirty(true);
}

static void mat4_frustum_set(
    float m[4][4], float left, float right, float bottom, float top, float near, float far)
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

  gpu_matrix_state_active_set_dirty(true);
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

  gpu_matrix_state_active_set_dirty(true);
}

void GPU_matrix_ortho_set(float left, float right, float bottom, float top, float near, float far)
{
  mat4_ortho_set(Projection, left, right, bottom, top, near, far);
  CHECKMAT(Projection);
  gpu_matrix_state_active_set_dirty(true);
}

void GPU_matrix_ortho_set_z(float near, float far)
{
  CHECKMAT(Projection);
  Projection[2][2] = -2.0f / (far - near);
  Projection[3][2] = -(far + near) / (far - near);
  gpu_matrix_state_active_set_dirty(true);
}

void GPU_matrix_ortho_2d_set(float left, float right, float bottom, float top)
{
  Mat4 m;
  mat4_ortho_set(m, left, right, bottom, top, -1.0f, 1.0f);
  CHECKMAT(Projection2D);
  gpu_matrix_state_active_set_dirty(true);
}

void GPU_matrix_frustum_set(
    float left, float right, float bottom, float top, float near, float far)
{
  mat4_frustum_set(Projection, left, right, bottom, top, near, far);
  CHECKMAT(Projection);
  gpu_matrix_state_active_set_dirty(true);
}

void GPU_matrix_perspective_set(float fovy, float aspect, float near, float far)
{
  float half_height = tanf(fovy * (float)(M_PI / 360.0)) * near;
  float half_width = half_height * aspect;
  GPU_matrix_frustum_set(-half_width, +half_width, -half_height, +half_height, near, far);
}

void GPU_matrix_look_at(float eyeX,
                        float eyeY,
                        float eyeZ,
                        float centerX,
                        float centerY,
                        float centerZ,
                        float upX,
                        float upY,
                        float upZ)
{
  Mat4 cm;
  float lookdir[3];
  float camup[3] = {upX, upY, upZ};

  lookdir[0] = centerX - eyeX;
  lookdir[1] = centerY - eyeY;
  lookdir[2] = centerZ - eyeZ;

  mat4_look_from_origin(cm, lookdir, camup);

  GPU_matrix_mul(cm);
  GPU_matrix_translate_3f(-eyeX, -eyeY, -eyeZ);
}

void GPU_matrix_project(const float world[3],
                        const float model[4][4],
                        const float proj[4][4],
                        const int view[4],
                        float win[3])
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

/**
 * The same result could be obtained as follows:
 *
 * \code{.c}
 * float projinv[4][4];
 * invert_m4_m4(projinv, projmat);
 * co[0] = 2 * co[0] - 1;
 * co[1] = 2 * co[1] - 1;
 * co[2] = 2 * co[2] - 1;
 * mul_project_m4_v3(projinv, co);
 * \endcode
 *
 * But that solution loses much precision.
 * Therefore, get the same result without inverting the matrix.
 */
static void gpu_mul_invert_projmat_m4_unmapped_v3_with_precalc(
    const struct GPUMatrixUnproject_Precalc *precalc, float co[3])
{
  /* 'precalc->dims' is the result of 'projmat_dimensions(proj, ...)'. */
  co[0] = precalc->dims.xmin + co[0] * (precalc->dims.xmax - precalc->dims.xmin);
  co[1] = precalc->dims.ymin + co[1] * (precalc->dims.ymax - precalc->dims.ymin);

  if (precalc->is_persp) {
    co[2] = precalc->dims.zmax * precalc->dims.zmin /
            (precalc->dims.zmax + co[2] * (precalc->dims.zmin - precalc->dims.zmax));
    co[0] *= co[2];
    co[1] *= co[2];
  }
  else {
    co[2] = precalc->dims.zmin + co[2] * (precalc->dims.zmax - precalc->dims.zmin);
  }
  co[2] *= -1;
}

bool GPU_matrix_unproject_precalc(struct GPUMatrixUnproject_Precalc *precalc,
                                  const float model[4][4],
                                  const float proj[4][4],
                                  const int view[4])
{
  precalc->is_persp = proj[3][3] == 0.0f;
  projmat_dimensions(proj,
                     &precalc->dims.xmin,
                     &precalc->dims.xmax,
                     &precalc->dims.ymin,
                     &precalc->dims.ymax,
                     &precalc->dims.zmin,
                     &precalc->dims.zmax);
  if (isinf(precalc->dims.zmax)) {
    /* We cannot retrieve the actual value of the clip_end.
     * Use `FLT_MAX` to avoid nans. */
    precalc->dims.zmax = FLT_MAX;
  }
  for (int i = 0; i < 4; i++) {
    precalc->view[i] = (float)view[i];
  }
  if (!invert_m4_m4(precalc->model_inverted, model)) {
    unit_m4(precalc->model_inverted);
    return false;
  }
  return true;
}

void GPU_matrix_unproject_with_precalc(const struct GPUMatrixUnproject_Precalc *precalc,
                                       const float win[3],
                                       float r_world[3])
{
  float in[3] = {
      (win[0] - precalc->view[0]) / precalc->view[2],
      (win[1] - precalc->view[1]) / precalc->view[3],
      win[2],
  };
  gpu_mul_invert_projmat_m4_unmapped_v3_with_precalc(precalc, in);
  mul_v3_m4v3(r_world, precalc->model_inverted, in);
}

bool GPU_matrix_unproject(const float win[3],
                          const float model[4][4],
                          const float proj[4][4],
                          const int view[4],
                          float r_world[3])
{
  struct GPUMatrixUnproject_Precalc precalc;
  if (!GPU_matrix_unproject_precalc(&precalc, model, proj, view)) {
    zero_v3(r_world);
    return false;
  }
  GPU_matrix_unproject_with_precalc(&precalc, win, r_world);
  return true;
}

const float (*GPU_matrix_model_view_get(float m[4][4]))[4]
{
  if (m) {
    copy_m4_m4(m, ModelView);
    return m;
  }
  else {
    return ModelView;
  }
}

const float (*GPU_matrix_projection_get(float m[4][4]))[4]
{
  if (m) {
    copy_m4_m4(m, Projection);
    return m;
  }
  else {
    return Projection;
  }
}

const float (*GPU_matrix_model_view_projection_get(float m[4][4]))[4]
{
  if (m == NULL) {
    static Mat4 temp;
    m = temp;
  }

  mul_m4_m4m4(m, Projection, ModelView);
  return m;
}

const float (*GPU_matrix_normal_get(float m[3][3]))[3]
{
  if (m == NULL) {
    static Mat3 temp3;
    m = temp3;
  }

  copy_m3_m4(m, (const float(*)[4])GPU_matrix_model_view_get(NULL));

  invert_m3(m);
  transpose_m3(m);

  return m;
}

const float (*GPU_matrix_normal_inverse_get(float m[3][3]))[3]
{
  if (m == NULL) {
    static Mat3 temp3;
    m = temp3;
  }

  GPU_matrix_normal_get(m);
  invert_m3(m);

  return m;
}

void GPU_matrix_bind(const GPUShaderInterface *shaderface)
{
  /* set uniform values to matrix stack values
   * call this before a draw call if desired matrices are dirty
   * call glUseProgram before this, as glUniform expects program to be bound
   */

  int32_t MV = GPU_shaderinterface_uniform_builtin(shaderface, GPU_UNIFORM_MODELVIEW);
  int32_t P = GPU_shaderinterface_uniform_builtin(shaderface, GPU_UNIFORM_PROJECTION);
  int32_t MVP = GPU_shaderinterface_uniform_builtin(shaderface, GPU_UNIFORM_MVP);

  int32_t N = GPU_shaderinterface_uniform_builtin(shaderface, GPU_UNIFORM_NORMAL);
  int32_t MV_inv = GPU_shaderinterface_uniform_builtin(shaderface, GPU_UNIFORM_MODELVIEW_INV);
  int32_t P_inv = GPU_shaderinterface_uniform_builtin(shaderface, GPU_UNIFORM_PROJECTION_INV);

  if (MV != -1) {
#if DEBUG_MATRIX_BIND
    puts("setting MV matrix");
#endif

    glUniformMatrix4fv(MV, 1, GL_FALSE, (const float *)GPU_matrix_model_view_get(NULL));
  }

  if (P != -1) {
#if DEBUG_MATRIX_BIND
    puts("setting P matrix");
#endif

    glUniformMatrix4fv(P, 1, GL_FALSE, (const float *)GPU_matrix_projection_get(NULL));
  }

  if (MVP != -1) {
#if DEBUG_MATRIX_BIND
    puts("setting MVP matrix");
#endif

    glUniformMatrix4fv(
        MVP, 1, GL_FALSE, (const float *)GPU_matrix_model_view_projection_get(NULL));
  }

  if (N != -1) {
#if DEBUG_MATRIX_BIND
    puts("setting normal matrix");
#endif

    glUniformMatrix3fv(N, 1, GL_FALSE, (const float *)GPU_matrix_normal_get(NULL));
  }

  if (MV_inv != -1) {
    Mat4 m;
    GPU_matrix_model_view_get(m);
    invert_m4(m);
    glUniformMatrix4fv(MV_inv, 1, GL_FALSE, (const float *)m);
  }

  if (P_inv != -1) {
    Mat4 m;
    GPU_matrix_projection_get(m);
    invert_m4(m);
    glUniformMatrix4fv(P_inv, 1, GL_FALSE, (const float *)m);
  }

  gpu_matrix_state_active_set_dirty(false);
}

bool GPU_matrix_dirty_get(void)
{
  GPUMatrixState *state = gpu_context_active_matrix_state_get();
  return state->dirty;
}

/* -------------------------------------------------------------------- */
/** \name Python API Helpers
 * \{ */
BLI_STATIC_ASSERT(GPU_PY_MATRIX_STACK_LEN + 1 == MATRIX_STACK_DEPTH, "define mismatch");

/* Return int since caller is may subtract. */

int GPU_matrix_stack_level_get_model_view(void)
{
  GPUMatrixState *state = gpu_context_active_matrix_state_get();
  return (int)state->model_view_stack.top;
}

int GPU_matrix_stack_level_get_projection(void)
{
  GPUMatrixState *state = gpu_context_active_matrix_state_get();
  return (int)state->projection_stack.top;
}

/** \} */

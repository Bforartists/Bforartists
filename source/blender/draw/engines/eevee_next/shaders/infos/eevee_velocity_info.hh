/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#include "eevee_defines.hh"
#include "gpu_shader_create_info.hh"

/* -------------------------------------------------------------------- */
/** \name Surface Velocity
 *
 * Combined with the depth pre-pass shader.
 * Outputs the view motion vectors for animated objects.
 * \{ */

/* Pass world space deltas to the fragment shader.
 * This is to make sure that the resulting motion vectors are valid even with displacement. */
GPU_SHADER_NAMED_INTERFACE_INFO(eevee_velocity_surface_iface, motion)
SMOOTH(VEC3, prev)
SMOOTH(VEC3, next)
GPU_SHADER_NAMED_INTERFACE_END(motion)

GPU_SHADER_CREATE_INFO(eevee_velocity_camera)
DEFINE("VELOCITY_CAMERA")
UNIFORM_BUF(VELOCITY_CAMERA_PREV_BUF, CameraData, camera_prev)
UNIFORM_BUF(VELOCITY_CAMERA_CURR_BUF, CameraData, camera_curr)
UNIFORM_BUF(VELOCITY_CAMERA_NEXT_BUF, CameraData, camera_next)
GPU_SHADER_CREATE_END()

GPU_SHADER_CREATE_INFO(eevee_velocity_geom)
DEFINE("MAT_VELOCITY")
STORAGE_BUF(VELOCITY_OBJ_PREV_BUF_SLOT, READ, mat4, velocity_obj_prev_buf[])
STORAGE_BUF(VELOCITY_OBJ_NEXT_BUF_SLOT, READ, mat4, velocity_obj_next_buf[])
STORAGE_BUF(VELOCITY_GEO_PREV_BUF_SLOT, READ, vec4, velocity_geo_prev_buf[])
STORAGE_BUF(VELOCITY_GEO_NEXT_BUF_SLOT, READ, vec4, velocity_geo_next_buf[])
STORAGE_BUF(VELOCITY_INDIRECTION_BUF_SLOT, READ, VelocityIndex, velocity_indirection_buf[])
VERTEX_OUT(eevee_velocity_surface_iface)
FRAGMENT_OUT(0, VEC4, out_velocity)
ADDITIONAL_INFO(eevee_velocity_camera)
GPU_SHADER_CREATE_END()

GPU_SHADER_CREATE_INFO(eevee_vertex_copy)
COMPUTE_SOURCE("eevee_vertex_copy_comp.glsl")
LOCAL_GROUP_SIZE(VERTEX_COPY_GROUP_SIZE)
STORAGE_BUF(0, READ, float, in_buf[])
STORAGE_BUF(1, WRITE, vec4, out_buf[])
PUSH_CONSTANT(INT, start_offset)
PUSH_CONSTANT(INT, vertex_stride)
PUSH_CONSTANT(INT, vertex_count)
DO_STATIC_COMPILATION()
GPU_SHADER_CREATE_END()

/** \} */

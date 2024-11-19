/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#ifdef GPU_SHADER
#  pragma once

#  include "BLI_utildefines_variadic.h"

#  include "gpu_glsl_cpp_stubs.hh"

#  include "draw_object_infos_info.hh"
#  include "draw_view_info.hh"
#  include "gpu_index_load_info.hh"

#  include "workbench_shader_shared.h"
#  define DYNAMIC_PASS_SELECTION
#  define SHADOW_PASS
#  define SHADOW_FAIL
#  define DOUBLE_MANIFOLD
#endif

#include "draw_defines.hh"

#include "gpu_shader_create_info.hh"

/* -------------------------------------------------------------------- */
/** \name Common
 * \{ */

GPU_SHADER_CREATE_INFO(workbench_shadow_common)
STORAGE_BUF_FREQ(3, READ, float, pos[], GEOMETRY)
/* WORKAROUND: Needed to support OpenSubdiv vertex format. Should be removed. */
PUSH_CONSTANT(IVEC2, gpu_attr_3)
UNIFORM_BUF(1, ShadowPassData, pass_data)
TYPEDEF_SOURCE("workbench_shader_shared.h")
ADDITIONAL_INFO(gpu_index_buffer_load)
ADDITIONAL_INFO(draw_view)
ADDITIONAL_INFO(draw_modelmat_new)
ADDITIONAL_INFO(draw_resource_handle_new)
GPU_SHADER_CREATE_END()

GPU_SHADER_CREATE_INFO(workbench_shadow_visibility_compute_common)
LOCAL_GROUP_SIZE(DRW_VISIBILITY_GROUP_SIZE)
DEFINE_VALUE("DRW_VIEW_LEN", "64")
STORAGE_BUF(0, READ, ObjectBounds, bounds_buf[])
UNIFORM_BUF(2, ExtrudedFrustum, extruded_frustum)
PUSH_CONSTANT(INT, resource_len)
PUSH_CONSTANT(INT, view_len)
PUSH_CONSTANT(INT, visibility_word_per_draw)
PUSH_CONSTANT(BOOL, force_fail_method)
PUSH_CONSTANT(VEC3, shadow_direction)
TYPEDEF_SOURCE("workbench_shader_shared.h")
COMPUTE_SOURCE("workbench_shadow_visibility_comp.glsl")
ADDITIONAL_INFO(draw_view)
ADDITIONAL_INFO(draw_view_culling)
GPU_SHADER_CREATE_END()

GPU_SHADER_CREATE_INFO(workbench_shadow_visibility_compute_dynamic_pass_type)
ADDITIONAL_INFO(workbench_shadow_visibility_compute_common)
DEFINE("DYNAMIC_PASS_SELECTION")
STORAGE_BUF(1, READ_WRITE, uint, pass_visibility_buf[])
STORAGE_BUF(2, READ_WRITE, uint, fail_visibility_buf[])
DO_STATIC_COMPILATION()
GPU_SHADER_CREATE_END()

GPU_SHADER_CREATE_INFO(workbench_shadow_visibility_compute_static_pass_type)
ADDITIONAL_INFO(workbench_shadow_visibility_compute_common)
STORAGE_BUF(1, READ_WRITE, uint, visibility_buf[])
DO_STATIC_COMPILATION()
GPU_SHADER_CREATE_END()

/** \} */

/* -------------------------------------------------------------------- */
/** \name Debug Type
 * \{ */

GPU_SHADER_CREATE_INFO(workbench_shadow_no_debug)
FRAGMENT_SOURCE("gpu_shader_depth_only_frag.glsl")
GPU_SHADER_CREATE_END()

GPU_SHADER_CREATE_INFO(workbench_shadow_debug)
FRAGMENT_OUT(0, VEC4, out_debug_color)
FRAGMENT_SOURCE("workbench_shadow_debug_frag.glsl")
GPU_SHADER_CREATE_END()

/** \} */

/* -------------------------------------------------------------------- */
/** \name Variations Declaration
 * \{ */

#define WORKBENCH_SHADOW_VARIATIONS(common, prefix, suffix, ...) \
  GPU_SHADER_CREATE_INFO(prefix##_pass_manifold_no_caps##suffix) \
  DEFINE("SHADOW_PASS") \
  VERTEX_SOURCE("workbench_shadow_vert.glsl") \
  ADDITIONAL_INFO_EXPAND(common, __VA_ARGS__) \
  DO_STATIC_COMPILATION() \
  GPU_SHADER_CREATE_END() \
\
  GPU_SHADER_CREATE_INFO(prefix##_pass_no_manifold_no_caps##suffix) \
  DEFINE("SHADOW_PASS") \
  DEFINE("DOUBLE_MANIFOLD") \
  VERTEX_SOURCE("workbench_shadow_vert.glsl") \
  ADDITIONAL_INFO_EXPAND(common, __VA_ARGS__) \
  DO_STATIC_COMPILATION() \
  GPU_SHADER_CREATE_END() \
\
  GPU_SHADER_CREATE_INFO(prefix##_fail_manifold_caps##suffix) \
  DEFINE("SHADOW_FAIL") \
  VERTEX_SOURCE("workbench_shadow_caps_vert.glsl") \
  ADDITIONAL_INFO_EXPAND(common, __VA_ARGS__) \
  DO_STATIC_COMPILATION() \
  GPU_SHADER_CREATE_END() \
\
  GPU_SHADER_CREATE_INFO(prefix##_fail_manifold_no_caps##suffix) \
  DEFINE("SHADOW_FAIL") \
  VERTEX_SOURCE("workbench_shadow_vert.glsl") \
  ADDITIONAL_INFO_EXPAND(common, __VA_ARGS__) \
  DO_STATIC_COMPILATION() \
  GPU_SHADER_CREATE_END() \
\
  GPU_SHADER_CREATE_INFO(prefix##_fail_no_manifold_caps##suffix) \
  DEFINE("SHADOW_FAIL") \
  DEFINE("DOUBLE_MANIFOLD") \
  VERTEX_SOURCE("workbench_shadow_caps_vert.glsl") \
  ADDITIONAL_INFO_EXPAND(common, __VA_ARGS__) \
  DO_STATIC_COMPILATION() \
  GPU_SHADER_CREATE_END() \
\
  GPU_SHADER_CREATE_INFO(prefix##_fail_no_manifold_no_caps##suffix) \
  DEFINE("SHADOW_FAIL") \
  DEFINE("DOUBLE_MANIFOLD") \
  VERTEX_SOURCE("workbench_shadow_vert.glsl") \
  ADDITIONAL_INFO_EXPAND(common, __VA_ARGS__) \
  DO_STATIC_COMPILATION() \
  GPU_SHADER_CREATE_END()

WORKBENCH_SHADOW_VARIATIONS(workbench_shadow_common, workbench_shadow, , workbench_shadow_no_debug)

WORKBENCH_SHADOW_VARIATIONS(workbench_shadow_common,
                            workbench_shadow,
                            _debug,
                            workbench_shadow_debug)

/** \} */

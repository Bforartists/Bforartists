/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#ifdef GPU_SHADER
#  pragma once
#  include "gpu_shader_compat.hh"

#  include "draw_object_infos_infos.hh"
#  include "draw_view_infos.hh"
#  include "eevee_common_infos.hh"
#  include "eevee_debug_shared.hh"
#  include "eevee_fullscreen_infos.hh"
#  include "eevee_light_infos.hh"
#  include "eevee_lightprobe_infos.hh"
#  include "eevee_sampling_infos.hh"
#  include "eevee_shadow_infos.hh"
#  include "eevee_shadow_shared.hh"
#  include "eevee_uniform_infos.hh"
#endif

#ifdef GLSL_CPP_STUBS
#  define SPHERE_PROBE
#endif

#include "draw_defines.hh"
#include "eevee_defines.hh"

#include "gpu_shader_create_info.hh"

/* -------------------------------------------------------------------- */
/** \name Debug
 * \{ */

GPU_SHADER_CREATE_INFO(eevee_shadow_debug)
DO_STATIC_COMPILATION()
TYPEDEF_SOURCE("eevee_defines.hh")
TYPEDEF_SOURCE("eevee_debug_shared.hh")
TYPEDEF_SOURCE("eevee_shadow_shared.hh")
STORAGE_BUF(5, read, ShadowTileMapData, tilemaps_buf[])
STORAGE_BUF(6, read, uint, tiles_buf[])
FRAGMENT_OUT_DUAL(0, float4, out_color_add, SRC_0)
FRAGMENT_OUT_DUAL(0, float4, out_color_mul, SRC_1)
PUSH_CONSTANT(int, debug_mode)
PUSH_CONSTANT(int, debug_tilemap_index)
DEPTH_WRITE(DepthWrite::ANY)
FRAGMENT_SOURCE("eevee_shadow_debug_frag.glsl")
ADDITIONAL_INFO(eevee_fullscreen)
ADDITIONAL_INFO(draw_view)
ADDITIONAL_INFO(eevee_hiz_data)
ADDITIONAL_INFO(eevee_light_data)
ADDITIONAL_INFO(eevee_shadow_data)
GPU_SHADER_CREATE_END()

/** \} */

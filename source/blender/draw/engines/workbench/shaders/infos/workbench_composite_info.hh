/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#include "gpu_shader_create_info.hh"
#include "workbench_defines.hh"

/* -------------------------------------------------------------------- */
/** \name Base Composite
 * \{ */

GPU_SHADER_CREATE_INFO(workbench_composite)
    .sampler(3, ImageType::DEPTH_2D, "depth_tx")
    .sampler(4, ImageType::FLOAT_2D, "normal_tx")
    .sampler(5, ImageType::FLOAT_2D, "material_tx")
    .uniform_buf(WB_WORLD_SLOT, "WorldData", "world_data")
    .typedef_source("workbench_shader_shared.h")
    .push_constant(Type::BOOL, "forceShadowing")
    .fragment_out(0, Type::VEC4, "fragColor")
    .fragment_source("workbench_composite_frag.glsl")
    .additional_info("draw_fullscreen", "draw_view");

/* Lighting */

GPU_SHADER_CREATE_INFO(workbench_resolve_opaque_studio).define("WORKBENCH_LIGHTING_STUDIO");

GPU_SHADER_CREATE_INFO(workbench_resolve_opaque_matcap)
    .define("WORKBENCH_LIGHTING_MATCAP")
    .sampler(WB_MATCAP_SLOT, ImageType::FLOAT_2D_ARRAY, "matcap_tx");

GPU_SHADER_CREATE_INFO(workbench_resolve_opaque_flat).define("WORKBENCH_LIGHTING_FLAT");

/* Effects */

GPU_SHADER_CREATE_INFO(workbench_resolve_curvature)
    .define("WORKBENCH_CURVATURE")
    .sampler(6, ImageType::UINT_2D, "object_id_tx");

GPU_SHADER_CREATE_INFO(workbench_resolve_cavity)
    .define("WORKBENCH_CAVITY")
    /* TODO(@pragma37): GPU_SAMPLER_EXTEND_MODE_REPEAT is set in CavityEffect,
     * it doesn't work here? */
    .sampler(7, ImageType::FLOAT_2D, "jitter_tx")
    .uniform_buf(5, "vec4", "cavity_samples[512]");

GPU_SHADER_CREATE_INFO(workbench_resolve_shadow)
    .define("WORKBENCH_SHADOW")
    .sampler(8, ImageType::UINT_2D, "stencil_tx");

/* Variations */

#define WORKBENCH_FINAL_VARIATION(name, ...) \
  GPU_SHADER_CREATE_INFO(name).additional_info(__VA_ARGS__).do_static_compilation(true);

#define WORKBENCH_RESOLVE_SHADOW_VARIATION(prefix, ...) \
  WORKBENCH_FINAL_VARIATION(prefix##_shadow, "workbench_resolve_shadow", __VA_ARGS__) \
  WORKBENCH_FINAL_VARIATION(prefix##_no_shadow, __VA_ARGS__)

#define WORKBENCH_CURVATURE_VARIATIONS(prefix, ...) \
  WORKBENCH_RESOLVE_SHADOW_VARIATION( \
      prefix##_curvature, "workbench_resolve_curvature", __VA_ARGS__) \
  WORKBENCH_RESOLVE_SHADOW_VARIATION(prefix##_no_curvature, __VA_ARGS__)

#define WORKBENCH_CAVITY_VARIATIONS(prefix, ...) \
  WORKBENCH_CURVATURE_VARIATIONS(prefix##_cavity, "workbench_resolve_cavity", __VA_ARGS__) \
  WORKBENCH_CURVATURE_VARIATIONS(prefix##_no_cavity, __VA_ARGS__)

#define WORKBENCH_LIGHTING_VARIATIONS(prefix, ...) \
  WORKBENCH_CAVITY_VARIATIONS( \
      prefix##_opaque_studio, "workbench_resolve_opaque_studio", __VA_ARGS__) \
  WORKBENCH_CAVITY_VARIATIONS( \
      prefix##_opaque_matcap, "workbench_resolve_opaque_matcap", __VA_ARGS__) \
  WORKBENCH_CAVITY_VARIATIONS(prefix##_opaque_flat, "workbench_resolve_opaque_flat", __VA_ARGS__)

WORKBENCH_LIGHTING_VARIATIONS(workbench_resolve, "workbench_composite");

#undef WORKBENCH_FINAL_VARIATION
#undef WORKBENCH_CURVATURE_VARIATIONS
#undef WORKBENCH_CAVITY_VARIATIONS
#undef WORKBENCH_LIGHTING_VARIATIONS

/** \} */

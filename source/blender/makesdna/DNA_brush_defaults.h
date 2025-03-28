/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup DNA
 */

#pragma once

#include "DNA_texture_defaults.h"

/* clang-format off */

/* -------------------------------------------------------------------- */
/** \name Brush Struct
 * \{ */

#define _DNA_DEFAULT_Brush \
  { \
    .blend = 0, \
    .flag = (BRUSH_ALPHA_PRESSURE | BRUSH_SPACE | BRUSH_SPACE_ATTEN), \
    .sampling_flag = (BRUSH_PAINT_ANTIALIASING), \
 \
    .ob_mode = OB_MODE_ALL_PAINT, \
 \
    /* BRUSH SCULPT BRUSH SETTINGS */ \
    .weight = 1.0f, /* weight of brush 0 - 1.0 */ \
    .size = 35,     /* radius of the brush in pixels */ \
    .unprojected_radius = 0.05f, /* radius of the brush in Blender units */ \
    .alpha = 1.0f,  /* brush strength/intensity probably variable should be renamed? */ \
    .autosmooth_factor = 0.0f, \
    .topology_rake_factor = 0.0f, \
    .crease_pinch_factor = 0.5f, \
    .normal_radius_factor = 0.5f, \
    .wet_paint_radius_factor = 0.5f, \
    .area_radius_factor = 0.5f, \
    .disconnected_distance_max = 0.1f, \
    .sculpt_plane = SCULPT_DISP_DIR_AREA, \
    .cloth_damping = 0.01, \
    .cloth_mass = 1, \
    .cloth_sim_limit = 2.5f, \
    .cloth_sim_falloff = 0.75f, \
    /* How far above or below the plane that is found by averaging the faces. */ \
    .plane_offset = 0.0f, \
    .plane_trim = 0.5f, \
    .normal_weight = 0.0f, \
    .fill_threshold = 0.2f, \
 \
    /* BRUSH PAINT BRUSH SETTINGS */ \
    /* Default rgb color of the brush when painting - white. */ \
    .rgb = {1.0f, 1.0f, 1.0f}, \
 \
    .secondary_rgb = {0, 0, 0}, \
 \
    /* BRUSH STROKE SETTINGS */ \
    /* How far each brush dot should be spaced as a percentage of brush diameter. */ \
    .spacing = 10, \
 \
    .smooth_stroke_radius = 75, \
    .smooth_stroke_factor = 0.9f, \
 \
    /* Time delay between dots of paint or sculpting when doing airbrush mode. */ \
    .rate = 0.1f, \
 \
    .jitter = 0.0f, \
 \
    .input_samples = 1, \
    /* Dash */ \
    .dash_ratio = 1.0f, \
    .dash_samples = 20, \
 \
    .texture_sample_bias = 0, /* value to added to texture samples */ \
    .texture_overlay_alpha = 33, \
    .mask_overlay_alpha = 33, \
    .cursor_overlay_alpha = 33, \
    .overlay_flags = 0, \
 \
    /* Brush appearance. */ \
 \
    /* add mode color is light red */ \
    .add_col = {1.0, 0.39, 0.39, 0.9}, \
 \
    /* subtract mode color is light blue */ \
    .sub_col = {0.39, 0.39, 1.0, 0.9}, \
 \
    .stencil_pos = {256, 256}, \
    .stencil_dimension = {256, 256}, \
    .mask_stencil_pos = {256, 256}, \
    .mask_stencil_dimension = {256, 256}, \
 \
    /* sculpting defaults to the draw brush for new brushes */ \
    .sculpt_brush_type = SCULPT_BRUSH_TYPE_DRAW, \
    .pose_smooth_iterations = 4, \
    .pose_ik_segments = 1, \
    .hardness = 0.0f, \
 \
    .automasking_boundary_edges_propagation_steps = 1, \
    .automasking_start_normal_limit = 0.34906585f, /* 20 degrees */ \
    .automasking_start_normal_falloff = 0.25f, \
    .automasking_view_normal_limit = 1.570796, /* 90 degrees */ \
    .automasking_view_normal_falloff = 0.25f, \
    .automasking_cavity_blur_steps = 0,\
    .automasking_cavity_factor = 1.0f,\
 \
    /* A kernel radius of 1 has almost no effect (#63233). */ \
    .blur_kernel_radius = 2, \
 \
    .mtex = _DNA_DEFAULT_MTex, \
    .mask_mtex = _DNA_DEFAULT_MTex, \
    .falloff_shape = 0,\
    .tip_scale_x = 1.0f,\
    .tip_roundness = 1.0f,\
  }

/** \} */

/* clang-format on */

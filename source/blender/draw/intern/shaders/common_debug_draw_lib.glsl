/* SPDX-FileCopyrightText: 2022-2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#pragma once

#include "draw_debug_info.hh"

SHADER_LIBRARY_CREATE_INFO(draw_debug_draw)

/**
 * Debugging drawing library
 *
 * Quick way to draw debug geometry. All input should be in world space and
 * will be rendered in the default view. No additional setup required.
 */

#ifdef DRW_DEBUG_DRAW

/** Global switch option. */
bool drw_debug_draw_enable = true;
#  define drw_debug_default_color vec4(1.0, 0.0, 0.0, 1.0)
#  define drw_debug_default_lifetime 1
#  define drw_debug_persistent_lifetime (~0u)

/* -------------------------------------------------------------------- */
/** \name Internals
 * \{ */

uint drw_debug_start_draw(uint v_needed)
{
  uint vertid = atomicAdd(drw_debug_draw_v_count(drw_debug_lines_buf), v_needed);
  return vertid;
}

void drw_debug_line(inout uint vertid, vec3 v1, vec3 v2, uint v_color, uint lifetime)
{
  uint out_line_id = vertid / 2u;
  drw_debug_lines_buf[out_line_id + drw_debug_draw_offset] = debug_line_make(floatBitsToUint(v1.x),
                                                                             floatBitsToUint(v1.y),
                                                                             floatBitsToUint(v1.z),
                                                                             floatBitsToUint(v2.x),
                                                                             floatBitsToUint(v2.y),
                                                                             floatBitsToUint(v2.z),
                                                                             v_color,
                                                                             lifetime);
  vertid += 2;
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name API
 * \{ */

/**
 * Draw a line.
 */
void drw_debug_line(vec3 v1, vec3 v2, vec4 v_color, uint lifetime)
{
  if (!drw_debug_draw_enable) {
    return;
  }
  const uint v_needed = 2;
  uint vertid = drw_debug_start_draw(v_needed);
  if (vertid + v_needed < DRW_DEBUG_DRAW_VERT_MAX) {
    drw_debug_line(vertid, v1, v2, debug_color_pack(v_color), lifetime);
  }
}
void drw_debug_line(vec3 v1, vec3 v2, vec4 v_color)
{
  drw_debug_line(v1, v2, v_color, drw_debug_default_lifetime);
}
void drw_debug_line(vec3 v1, vec3 v2)
{
  drw_debug_line(v1, v2, drw_debug_default_color);
}

/**
 * Draw a quad contour.
 */
void drw_debug_quad(vec3 v1, vec3 v2, vec3 v3, vec3 v4, vec4 v_color, uint lifetime)
{
  if (!drw_debug_draw_enable) {
    return;
  }
  const uint v_needed = 8;
  uint vertid = drw_debug_start_draw(v_needed);
  if (vertid + v_needed < DRW_DEBUG_DRAW_VERT_MAX) {
    uint pcolor = debug_color_pack(v_color);
    drw_debug_line(vertid, v1, v2, pcolor, drw_debug_default_lifetime);
    drw_debug_line(vertid, v2, v3, pcolor, drw_debug_default_lifetime);
    drw_debug_line(vertid, v3, v4, pcolor, drw_debug_default_lifetime);
    drw_debug_line(vertid, v4, v1, pcolor, drw_debug_default_lifetime);
  }
}
void drw_debug_quad(vec3 v1, vec3 v2, vec3 v3, vec3 v4, vec4 v_color)
{
  drw_debug_quad(v1, v2, v3, v4, v_color, drw_debug_default_lifetime);
}
void drw_debug_quad(vec3 v1, vec3 v2, vec3 v3, vec3 v4)
{
  drw_debug_quad(v1, v2, v3, v4, drw_debug_default_color);
}

/**
 * Draw a point as octahedron wireframe.
 */
void drw_debug_point(vec3 p, float radius, vec4 v_color, uint lifetime)
{
  if (!drw_debug_draw_enable) {
    return;
  }
  vec3 c = vec3(radius, -radius, 0);
  vec3 v1 = p + c.xzz;
  vec3 v2 = p + c.zxz;
  vec3 v3 = p + c.yzz;
  vec3 v4 = p + c.zyz;
  vec3 v5 = p + c.zzx;
  vec3 v6 = p + c.zzy;

  const uint v_needed = 12 * 2;
  uint vertid = drw_debug_start_draw(v_needed);
  if (vertid + v_needed < DRW_DEBUG_DRAW_VERT_MAX) {
    uint pcolor = debug_color_pack(v_color);
    drw_debug_line(vertid, v1, v2, pcolor, lifetime);
    drw_debug_line(vertid, v2, v3, pcolor, lifetime);
    drw_debug_line(vertid, v3, v4, pcolor, lifetime);
    drw_debug_line(vertid, v4, v1, pcolor, lifetime);
    drw_debug_line(vertid, v1, v5, pcolor, lifetime);
    drw_debug_line(vertid, v2, v5, pcolor, lifetime);
    drw_debug_line(vertid, v3, v5, pcolor, lifetime);
    drw_debug_line(vertid, v4, v5, pcolor, lifetime);
    drw_debug_line(vertid, v1, v6, pcolor, lifetime);
    drw_debug_line(vertid, v2, v6, pcolor, lifetime);
    drw_debug_line(vertid, v3, v6, pcolor, lifetime);
    drw_debug_line(vertid, v4, v6, pcolor, lifetime);
  }
}
void drw_debug_point(vec3 p, float radius, vec4 v_color)
{
  drw_debug_point(p, radius, v_color, drw_debug_default_lifetime);
}
void drw_debug_point(vec3 p, float radius)
{
  drw_debug_point(p, radius, drw_debug_default_color);
}
void drw_debug_point(vec3 p)
{
  drw_debug_point(p, 0.01);
}

/**
 * Draw a sphere wireframe as 3 axes circle.
 */
void drw_debug_sphere(vec3 p, float radius, vec4 v_color, uint lifetime)
{
  if (!drw_debug_draw_enable) {
    return;
  }
  const int circle_resolution = 16;
  const uint v_needed = circle_resolution * 2 * 3;
  uint vertid = drw_debug_start_draw(v_needed);
  if (vertid + v_needed < DRW_DEBUG_DRAW_VERT_MAX) {
    uint pcolor = debug_color_pack(v_color);
    for (int axis = 0; axis < 3; axis++) {
      for (int edge = 0; edge < circle_resolution; edge++) {
        float angle1 = (2.0 * 3.141592) * float(edge + 0) / float(circle_resolution);
        vec3 p1 = vec3(cos(angle1), sin(angle1), 0.0) * radius;
        p1 = vec3(p1[(0 + axis) % 3], p1[(1 + axis) % 3], p1[(2 + axis) % 3]);

        float angle2 = (2.0 * 3.141592) * float(edge + 1) / float(circle_resolution);
        vec3 p2 = vec3(cos(angle2), sin(angle2), 0.0) * radius;
        p2 = vec3(p2[(0 + axis) % 3], p2[(1 + axis) % 3], p2[(2 + axis) % 3]);

        drw_debug_line(vertid, p + p1, p + p2, pcolor, lifetime);
      }
    }
  }
}
void drw_debug_sphere(vec3 p, float radius, vec4 v_color)
{
  drw_debug_sphere(p, radius, v_color, drw_debug_default_lifetime);
}
void drw_debug_sphere(vec3 p, float radius)
{
  drw_debug_sphere(p, radius, drw_debug_default_color);
}

/**
 * Draw a matrix transformation as 3 colored axes.
 */
void drw_debug_matrix(mat4 mat, uint lifetime)
{
  vec4 p[4] = float4_array(vec4(0, 0, 0, 1), vec4(1, 0, 0, 1), vec4(0, 1, 0, 1), vec4(0, 0, 1, 1));
  for (int i = 0; i < 4; i++) {
    p[i] = mat * p[i];
    p[i].xyz /= p[i].w;
  }
  drw_debug_line(p[0].xyz, p[0].xyz, vec4(1, 0, 0, 1), lifetime);
  drw_debug_line(p[0].xyz, p[1].xyz, vec4(0, 1, 0, 1), lifetime);
  drw_debug_line(p[0].xyz, p[2].xyz, vec4(0, 0, 1, 1), lifetime);
}
void drw_debug_matrix(mat4 mat)
{
  drw_debug_matrix(mat, drw_debug_default_lifetime);
}

/**
 * Draw a matrix as a 2 units length bounding box, centered on origin.
 */
void drw_debug_matrix_as_bbox(mat4 mat, vec4 v_color, uint lifetime)
{
  vec4 p[8] = float4_array(vec4(-1, -1, -1, 1),
                           vec4(1, -1, -1, 1),
                           vec4(1, 1, -1, 1),
                           vec4(-1, 1, -1, 1),
                           vec4(-1, -1, 1, 1),
                           vec4(1, -1, 1, 1),
                           vec4(1, 1, 1, 1),
                           vec4(-1, 1, 1, 1));
  for (int i = 0; i < 8; i++) {
    p[i] = mat * p[i];
    p[i].xyz /= p[i].w;
  }
  drw_debug_quad(p[0].xyz, p[1].xyz, p[2].xyz, p[3].xyz, v_color, lifetime);
  drw_debug_line(p[0].xyz, p[4].xyz, v_color, lifetime);
  drw_debug_line(p[1].xyz, p[5].xyz, v_color, lifetime);
  drw_debug_line(p[2].xyz, p[6].xyz, v_color, lifetime);
  drw_debug_line(p[3].xyz, p[7].xyz, v_color, lifetime);
  drw_debug_quad(p[4].xyz, p[5].xyz, p[6].xyz, p[7].xyz, v_color, lifetime);
}
void drw_debug_matrix_as_bbox(mat4 mat, vec4 v_color)
{
  drw_debug_matrix_as_bbox(mat, v_color, drw_debug_default_lifetime);
}
void drw_debug_matrix_as_bbox(mat4 mat)
{
  drw_debug_matrix_as_bbox(mat, drw_debug_default_color);
}

#endif

/** \} */

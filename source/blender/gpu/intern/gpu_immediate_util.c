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
 */

/** \file
 * \ingroup gpu
 *
 * GPU immediate mode drawing utilities
 */

#include <stdio.h>
#include <string.h>

#include "BLI_math.h"
#include "BLI_utildefines.h"

#include "GPU_immediate.h"
#include "GPU_immediate_util.h"

#include "UI_resources.h"

static const float cube_coords[8][3] = {
    {-1, -1, -1},
    {-1, -1, +1},
    {-1, +1, -1},
    {-1, +1, +1},
    {+1, -1, -1},
    {+1, -1, +1},
    {+1, +1, -1},
    {+1, +1, +1},
};
static const int cube_quad_index[6][4] = {
    {0, 1, 3, 2},
    {0, 2, 6, 4},
    {0, 4, 5, 1},
    {1, 5, 7, 3},
    {2, 3, 7, 6},
    {4, 6, 7, 5},
};
static const int cube_line_index[12][2] = {
    {0, 1},
    {0, 2},
    {0, 4},
    {1, 3},
    {1, 5},
    {2, 3},
    {2, 6},
    {3, 7},
    {4, 5},
    {4, 6},
    {5, 7},
    {6, 7},
};

void immRectf(uint pos, float x1, float y1, float x2, float y2)
{
  immBegin(GPU_PRIM_TRI_FAN, 4);
  immVertex2f(pos, x1, y1);
  immVertex2f(pos, x2, y1);
  immVertex2f(pos, x2, y2);
  immVertex2f(pos, x1, y2);
  immEnd();
}

void immRecti(uint pos, int x1, int y1, int x2, int y2)
{
  immBegin(GPU_PRIM_TRI_FAN, 4);
  immVertex2i(pos, x1, y1);
  immVertex2i(pos, x2, y1);
  immVertex2i(pos, x2, y2);
  immVertex2i(pos, x1, y2);
  immEnd();
}

void immRectf_fast(uint pos, float x1, float y1, float x2, float y2)
{
  immVertex2f(pos, x1, y1);
  immVertex2f(pos, x2, y1);
  immVertex2f(pos, x2, y2);

  immVertex2f(pos, x1, y1);
  immVertex2f(pos, x2, y2);
  immVertex2f(pos, x1, y2);
}

void immRectf_fast_with_color(
    uint pos, uint col, float x1, float y1, float x2, float y2, const float color[4])
{
  immAttr4fv(col, color);
  immVertex2f(pos, x1, y1);
  immAttr4fv(col, color);
  immVertex2f(pos, x2, y1);
  immAttr4fv(col, color);
  immVertex2f(pos, x2, y2);

  immAttr4fv(col, color);
  immVertex2f(pos, x1, y1);
  immAttr4fv(col, color);
  immVertex2f(pos, x2, y2);
  immAttr4fv(col, color);
  immVertex2f(pos, x1, y2);
}

void immRecti_fast_with_color(
    uint pos, uint col, int x1, int y1, int x2, int y2, const float color[4])
{
  immAttr4fv(col, color);
  immVertex2i(pos, x1, y1);
  immAttr4fv(col, color);
  immVertex2i(pos, x2, y1);
  immAttr4fv(col, color);
  immVertex2i(pos, x2, y2);

  immAttr4fv(col, color);
  immVertex2i(pos, x1, y1);
  immAttr4fv(col, color);
  immVertex2i(pos, x2, y2);
  immAttr4fv(col, color);
  immVertex2i(pos, x1, y2);
}

#if 0 /* more complete version in case we want that */
void immRecti_complete(int x1, int y1, int x2, int y2, const float color[4])
{
  GPUVertFormat *format = immVertexFormat();
  uint pos = add_attr(format, "pos", GPU_COMP_I32, 2, GPU_FETCH_INT_TO_FLOAT);
  immBindBuiltinProgram(GPU_SHADER_2D_UNIFORM_COLOR);
  immUniformColor4fv(color);
  immRecti(pos, x1, y1, x2, y2);
  immUnbindProgram();
}
#endif

/**
 * Pack color into 3 bytes
 *
 * This define converts a numerical value to the equivalent 24-bit
 * color, while not being endian-sensitive. On little-endian, this
 * is the same as doing a 'naive' indexing, on big-endian, it is not!
 *
 * \note BGR format (i.e. 0xBBGGRR)...
 *
 * \param x: color.
 */
void imm_cpack(uint x)
{
  immUniformColor3ub(((x)&0xFF), (((x) >> 8) & 0xFF), (((x) >> 16) & 0xFF));
}

static void imm_draw_circle(GPUPrimType prim_type,
                            const uint shdr_pos,
                            float x,
                            float y,
                            float rad_x,
                            float rad_y,
                            int nsegments)
{
  immBegin(prim_type, nsegments);
  for (int i = 0; i < nsegments; i++) {
    const float angle = (float)(2 * M_PI) * ((float)i / (float)nsegments);
    immVertex2f(shdr_pos, x + (rad_x * cosf(angle)), y + (rad_y * sinf(angle)));
  }
  immEnd();
}

/**
 * Draw a circle outline with the given \a radius.
 * The circle is centered at \a x, \a y and drawn in the XY plane.
 *
 * \param shdr_pos: The vertex attribute number for position.
 * \param x: Horizontal center.
 * \param y: Vertical center.
 * \param rad: The circle's radius.
 * \param nsegments: The number of segments to use in drawing (more = smoother).
 */
void imm_draw_circle_wire_2d(uint shdr_pos, float x, float y, float rad, int nsegments)
{
  imm_draw_circle(GPU_PRIM_LINE_LOOP, shdr_pos, x, y, rad, rad, nsegments);
}

/**
 * Draw a filled circle with the given \a radius.
 * The circle is centered at \a x, \a y and drawn in the XY plane.
 *
 * \param shdr_pos: The vertex attribute number for position.
 * \param x: Horizontal center.
 * \param y: Vertical center.
 * \param rad: The circle's radius.
 * \param nsegments: The number of segments to use in drawing (more = smoother).
 */
void imm_draw_circle_fill_2d(uint shdr_pos, float x, float y, float rad, int nsegments)
{
  imm_draw_circle(GPU_PRIM_TRI_FAN, shdr_pos, x, y, rad, rad, nsegments);
}

void imm_draw_circle_wire_aspect_2d(
    uint shdr_pos, float x, float y, float rad_x, float rad_y, int nsegments)
{
  imm_draw_circle(GPU_PRIM_LINE_LOOP, shdr_pos, x, y, rad_x, rad_y, nsegments);
}
void imm_draw_circle_fill_aspect_2d(
    uint shdr_pos, float x, float y, float rad_x, float rad_y, int nsegments)
{
  imm_draw_circle(GPU_PRIM_TRI_FAN, shdr_pos, x, y, rad_x, rad_y, nsegments);
}

static void imm_draw_circle_partial(GPUPrimType prim_type,
                                    uint pos,
                                    float x,
                                    float y,
                                    float rad,
                                    int nsegments,
                                    float start,
                                    float sweep)
{
  /* shift & reverse angle, increase 'nsegments' to match gluPartialDisk */
  const float angle_start = -(DEG2RADF(start)) + (float)(M_PI / 2);
  const float angle_end = -(DEG2RADF(sweep) - angle_start);
  nsegments += 1;
  immBegin(prim_type, nsegments);
  for (int i = 0; i < nsegments; i++) {
    const float angle = interpf(angle_start, angle_end, ((float)i / (float)(nsegments - 1)));
    const float angle_sin = sinf(angle);
    const float angle_cos = cosf(angle);
    immVertex2f(pos, x + rad * angle_cos, y + rad * angle_sin);
  }
  immEnd();
}

void imm_draw_circle_partial_wire_2d(
    uint pos, float x, float y, float rad, int nsegments, float start, float sweep)
{
  imm_draw_circle_partial(GPU_PRIM_LINE_STRIP, pos, x, y, rad, nsegments, start, sweep);
}

static void imm_draw_disk_partial(GPUPrimType prim_type,
                                  uint pos,
                                  float x,
                                  float y,
                                  float rad_inner,
                                  float rad_outer,
                                  int nsegments,
                                  float start,
                                  float sweep)
{
  /* to avoid artifacts */
  const float max_angle = 3 * 360;
  CLAMP(sweep, -max_angle, max_angle);

  /* shift & reverse angle, increase 'nsegments' to match gluPartialDisk */
  const float angle_start = -(DEG2RADF(start)) + (float)(M_PI / 2);
  const float angle_end = -(DEG2RADF(sweep) - angle_start);
  nsegments += 1;
  immBegin(prim_type, nsegments * 2);
  for (int i = 0; i < nsegments; i++) {
    const float angle = interpf(angle_start, angle_end, ((float)i / (float)(nsegments - 1)));
    const float angle_sin = sinf(angle);
    const float angle_cos = cosf(angle);
    immVertex2f(pos, x + rad_inner * angle_cos, y + rad_inner * angle_sin);
    immVertex2f(pos, x + rad_outer * angle_cos, y + rad_outer * angle_sin);
  }
  immEnd();
}

/**
 * Draw a filled arc with the given inner and outer radius.
 * The circle is centered at \a x, \a y and drawn in the XY plane.
 *
 * \note Arguments are `gluPartialDisk` compatible.
 *
 * \param pos: The vertex attribute number for position.
 * \param x: Horizontal center.
 * \param y: Vertical center.
 * \param rad_inner: The inner circle's radius.
 * \param rad_outer: The outer circle's radius (can be zero).
 * \param nsegments: The number of segments to use in drawing (more = smoother).
 * \param start: Specifies the starting angle, in degrees, of the disk portion.
 * \param sweep: Specifies the sweep angle, in degrees, of the disk portion.
 */
void imm_draw_disk_partial_fill_2d(uint pos,
                                   float x,
                                   float y,
                                   float rad_inner,
                                   float rad_outer,
                                   int nsegments,
                                   float start,
                                   float sweep)
{
  imm_draw_disk_partial(
      GPU_PRIM_TRI_STRIP, pos, x, y, rad_inner, rad_outer, nsegments, start, sweep);
}

static void imm_draw_circle_3D(
    GPUPrimType prim_type, uint pos, float x, float y, float rad, int nsegments)
{
  immBegin(prim_type, nsegments);
  for (int i = 0; i < nsegments; i++) {
    float angle = (float)(2 * M_PI) * ((float)i / (float)nsegments);
    immVertex3f(pos, x + rad * cosf(angle), y + rad * sinf(angle), 0.0f);
  }
  immEnd();
}

void imm_draw_circle_wire_3d(uint pos, float x, float y, float rad, int nsegments)
{
  imm_draw_circle_3D(GPU_PRIM_LINE_LOOP, pos, x, y, rad, nsegments);
}

void imm_draw_circle_dashed_3d(uint pos, float x, float y, float rad, int nsegments)
{
  imm_draw_circle_3D(GPU_PRIM_LINES, pos, x, y, rad, nsegments / 2);
}

void imm_draw_circle_fill_3d(uint pos, float x, float y, float rad, int nsegments)
{
  imm_draw_circle_3D(GPU_PRIM_TRI_FAN, pos, x, y, rad, nsegments);
}

/**
 * Draw a lined box.
 *
 * \param pos: The vertex attribute number for position.
 * \param x1: left.
 * \param y1: bottom.
 * \param x2: right.
 * \param y2: top.
 */
void imm_draw_box_wire_2d(uint pos, float x1, float y1, float x2, float y2)
{
  immBegin(GPU_PRIM_LINE_LOOP, 4);
  immVertex2f(pos, x1, y1);
  immVertex2f(pos, x1, y2);
  immVertex2f(pos, x2, y2);
  immVertex2f(pos, x2, y1);
  immEnd();
}

void imm_draw_box_wire_3d(uint pos, float x1, float y1, float x2, float y2)
{
  /* use this version when GPUVertFormat has a vec3 position */
  immBegin(GPU_PRIM_LINE_LOOP, 4);
  immVertex3f(pos, x1, y1, 0.0f);
  immVertex3f(pos, x1, y2, 0.0f);
  immVertex3f(pos, x2, y2, 0.0f);
  immVertex3f(pos, x2, y1, 0.0f);
  immEnd();
}

/**
 * Draw a standard checkerboard to indicate transparent backgrounds.
 */
void imm_draw_box_checker_2d_ex(float x1,
                                float y1,
                                float x2,
                                float y2,
                                const float color_primary[4],
                                const float color_secondary[4],
                                int checker_size)
{
  uint pos = GPU_vertformat_attr_add(immVertexFormat(), "pos", GPU_COMP_F32, 2, GPU_FETCH_FLOAT);

  immBindBuiltinProgram(GPU_SHADER_2D_CHECKER);

  immUniform4fv("color1", color_primary);
  immUniform4fv("color2", color_secondary);
  immUniform1i("size", checker_size);

  immRectf(pos, x1, y1, x2, y2);

  immUnbindProgram();
}
void imm_draw_box_checker_2d(float x1, float y1, float x2, float y2)
{
  float checker_primary[4];
  float checker_secondary[4];
  UI_GetThemeColor4fv(TH_TRANSPARENT_CHECKER_PRIMARY, checker_primary);
  UI_GetThemeColor4fv(TH_TRANSPARENT_CHECKER_SECONDARY, checker_secondary);
  int checker_size = UI_GetThemeValue(TH_TRANSPARENT_CHECKER_SIZE);
  imm_draw_box_checker_2d_ex(x1, y1, x2, y2, checker_primary, checker_secondary, checker_size);
}

void imm_draw_cube_fill_3d(uint pos, const float co[3], const float aspect[3])
{
  float coords[ARRAY_SIZE(cube_coords)][3];

  for (int i = 0; i < ARRAY_SIZE(cube_coords); i++) {
    madd_v3_v3v3v3(coords[i], co, cube_coords[i], aspect);
  }

  immBegin(GPU_PRIM_TRIS, ARRAY_SIZE(cube_quad_index) * 3 * 2);
  for (int i = 0; i < ARRAY_SIZE(cube_quad_index); i++) {
    immVertex3fv(pos, coords[cube_quad_index[i][0]]);
    immVertex3fv(pos, coords[cube_quad_index[i][1]]);
    immVertex3fv(pos, coords[cube_quad_index[i][2]]);

    immVertex3fv(pos, coords[cube_quad_index[i][0]]);
    immVertex3fv(pos, coords[cube_quad_index[i][2]]);
    immVertex3fv(pos, coords[cube_quad_index[i][3]]);
  }
  immEnd();
}

void imm_draw_cube_wire_3d(uint pos, const float co[3], const float aspect[3])
{
  float coords[ARRAY_SIZE(cube_coords)][3];

  for (int i = 0; i < ARRAY_SIZE(cube_coords); i++) {
    madd_v3_v3v3v3(coords[i], co, cube_coords[i], aspect);
  }

  immBegin(GPU_PRIM_LINES, ARRAY_SIZE(cube_line_index) * 2);
  for (int i = 0; i < ARRAY_SIZE(cube_line_index); i++) {
    immVertex3fv(pos, coords[cube_line_index[i][0]]);
    immVertex3fv(pos, coords[cube_line_index[i][1]]);
  }
  immEnd();
}

/**
 * Draw a cylinder. Replacement for gluCylinder.
 * _warning_ : Slow, better use it only if you no other choices.
 *
 * \param pos: The vertex attribute number for position.
 * \param nor: The vertex attribute number for normal.
 * \param base: Specifies the radius of the cylinder at z = 0.
 * \param top: Specifies the radius of the cylinder at z = height.
 * \param height: Specifies the height of the cylinder.
 * \param slices: Specifies the number of subdivisions around the z axis.
 * \param stacks: Specifies the number of subdivisions along the z axis.
 */
void imm_draw_cylinder_fill_normal_3d(
    uint pos, uint nor, float base, float top, float height, int slices, int stacks)
{
  immBegin(GPU_PRIM_TRIS, 6 * slices * stacks);
  for (int i = 0; i < slices; i++) {
    const float angle1 = (float)(2 * M_PI) * ((float)i / (float)slices);
    const float angle2 = (float)(2 * M_PI) * ((float)(i + 1) / (float)slices);
    const float cos1 = cosf(angle1);
    const float sin1 = sinf(angle1);
    const float cos2 = cosf(angle2);
    const float sin2 = sinf(angle2);

    for (int j = 0; j < stacks; j++) {
      float fac1 = (float)j / (float)stacks;
      float fac2 = (float)(j + 1) / (float)stacks;
      float r1 = base * (1.f - fac1) + top * fac1;
      float r2 = base * (1.f - fac2) + top * fac2;
      float h1 = height * ((float)j / (float)stacks);
      float h2 = height * ((float)(j + 1) / (float)stacks);

      float v1[3] = {r1 * cos2, r1 * sin2, h1};
      float v2[3] = {r2 * cos2, r2 * sin2, h2};
      float v3[3] = {r2 * cos1, r2 * sin1, h2};
      float v4[3] = {r1 * cos1, r1 * sin1, h1};
      float n1[3], n2[3];

      /* calc normals */
      sub_v3_v3v3(n1, v2, v1);
      normalize_v3(n1);
      n1[0] = cos1;
      n1[1] = sin1;
      n1[2] = 1 - n1[2];

      sub_v3_v3v3(n2, v3, v4);
      normalize_v3(n2);
      n2[0] = cos2;
      n2[1] = sin2;
      n2[2] = 1 - n2[2];

      /* first tri */
      immAttr3fv(nor, n2);
      immVertex3fv(pos, v1);
      immVertex3fv(pos, v2);
      immAttr3fv(nor, n1);
      immVertex3fv(pos, v3);

      /* second tri */
      immVertex3fv(pos, v3);
      immVertex3fv(pos, v4);
      immAttr3fv(nor, n2);
      immVertex3fv(pos, v1);
    }
  }
  immEnd();
}

void imm_draw_cylinder_wire_3d(
    uint pos, float base, float top, float height, int slices, int stacks)
{
  immBegin(GPU_PRIM_LINES, 6 * slices * stacks);
  for (int i = 0; i < slices; i++) {
    const float angle1 = (float)(2 * M_PI) * ((float)i / (float)slices);
    const float angle2 = (float)(2 * M_PI) * ((float)(i + 1) / (float)slices);
    const float cos1 = cosf(angle1);
    const float sin1 = sinf(angle1);
    const float cos2 = cosf(angle2);
    const float sin2 = sinf(angle2);

    for (int j = 0; j < stacks; j++) {
      float fac1 = (float)j / (float)stacks;
      float fac2 = (float)(j + 1) / (float)stacks;
      float r1 = base * (1.f - fac1) + top * fac1;
      float r2 = base * (1.f - fac2) + top * fac2;
      float h1 = height * ((float)j / (float)stacks);
      float h2 = height * ((float)(j + 1) / (float)stacks);

      float v1[3] = {r1 * cos2, r1 * sin2, h1};
      float v2[3] = {r2 * cos2, r2 * sin2, h2};
      float v3[3] = {r2 * cos1, r2 * sin1, h2};
      float v4[3] = {r1 * cos1, r1 * sin1, h1};

      immVertex3fv(pos, v1);
      immVertex3fv(pos, v2);

      immVertex3fv(pos, v2);
      immVertex3fv(pos, v3);

      immVertex3fv(pos, v1);
      immVertex3fv(pos, v4);
    }
  }
  immEnd();
}

void imm_draw_cylinder_fill_3d(
    uint pos, float base, float top, float height, int slices, int stacks)
{
  immBegin(GPU_PRIM_TRIS, 6 * slices * stacks);
  for (int i = 0; i < slices; i++) {
    const float angle1 = (float)(2 * M_PI) * ((float)i / (float)slices);
    const float angle2 = (float)(2 * M_PI) * ((float)(i + 1) / (float)slices);
    const float cos1 = cosf(angle1);
    const float sin1 = sinf(angle1);
    const float cos2 = cosf(angle2);
    const float sin2 = sinf(angle2);

    for (int j = 0; j < stacks; j++) {
      float fac1 = (float)j / (float)stacks;
      float fac2 = (float)(j + 1) / (float)stacks;
      float r1 = base * (1.f - fac1) + top * fac1;
      float r2 = base * (1.f - fac2) + top * fac2;
      float h1 = height * ((float)j / (float)stacks);
      float h2 = height * ((float)(j + 1) / (float)stacks);

      float v1[3] = {r1 * cos2, r1 * sin2, h1};
      float v2[3] = {r2 * cos2, r2 * sin2, h2};
      float v3[3] = {r2 * cos1, r2 * sin1, h2};
      float v4[3] = {r1 * cos1, r1 * sin1, h1};

      /* first tri */
      immVertex3fv(pos, v1);
      immVertex3fv(pos, v2);
      immVertex3fv(pos, v3);

      /* second tri */
      immVertex3fv(pos, v3);
      immVertex3fv(pos, v4);
      immVertex3fv(pos, v1);
    }
  }
  immEnd();
}

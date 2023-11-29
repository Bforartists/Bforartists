/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup spseq
 */

#include "sequencer_quads_batch.hh"

#include "BLI_color.hh"
#include "BLI_math_vector_types.hh"

#include "GPU_batch.h"
#include "GPU_index_buffer.h"
#include "GPU_vertex_buffer.h"

struct ColorVertex {
  blender::float2 pos;
  blender::ColorTheme4b color;
};
static_assert(sizeof(ColorVertex) == 12);

static GPUIndexBuf *create_quads_index_buffer(int quads_count)
{
  GPUIndexBufBuilder elb;
  GPU_indexbuf_init(&elb, GPU_PRIM_TRIS, quads_count * 2, quads_count * 4);
  for (int i = 0; i < quads_count; i++) {
    const uint i0 = i * 4 + 0;
    const uint i1 = i * 4 + 1;
    const uint i2 = i * 4 + 2;
    const uint i3 = i * 4 + 3;
    GPU_indexbuf_add_tri_verts(&elb, i0, i1, i2);
    GPU_indexbuf_add_tri_verts(&elb, i2, i1, i3);
  }
  return GPU_indexbuf_build(&elb);
}

SeqQuadsBatch::SeqQuadsBatch()
{
  ibo_quads = create_quads_index_buffer(MAX_QUADS);

  GPUVertFormat format;
  GPU_vertformat_clear(&format);
  GPU_vertformat_attr_add(&format, "pos", GPU_COMP_F32, 2, GPU_FETCH_FLOAT);
  GPU_vertformat_attr_add(&format, "color", GPU_COMP_U8, 4, GPU_FETCH_INT_TO_FLOAT_UNIT);

  vbo_quads = GPU_vertbuf_create_with_format_ex(&format, GPU_USAGE_STREAM);
  GPU_vertbuf_data_alloc(vbo_quads, MAX_QUADS * 4);

  vbo_lines = GPU_vertbuf_create_with_format_ex(&format, GPU_USAGE_STREAM);
  GPU_vertbuf_data_alloc(vbo_lines, MAX_LINES * 2);

  batch_quads = GPU_batch_create_ex(
      GPU_PRIM_TRIS, vbo_quads, ibo_quads, GPU_BATCH_OWNS_VBO | GPU_BATCH_OWNS_INDEX);
  GPU_batch_program_set_builtin(batch_quads, GPU_SHADER_3D_FLAT_COLOR);

  batch_lines = GPU_batch_create_ex(GPU_PRIM_LINES, vbo_lines, nullptr, GPU_BATCH_OWNS_VBO);
  GPU_batch_program_set_builtin(batch_lines, GPU_SHADER_3D_FLAT_COLOR);
}

SeqQuadsBatch::~SeqQuadsBatch()
{
  BLI_assert_msg(quads_num == 0 && lines_num == 0,
                 "SeqQuadsBatch is being destroyed without drawing quads/lines it contains");
  GPU_batch_discard(batch_quads);
  GPU_batch_discard(batch_lines);
}

void SeqQuadsBatch::draw()
{
  if (quads_num > 0) {
    GPU_vertbuf_tag_dirty(vbo_quads);
    GPU_vertbuf_use(vbo_quads);
    GPU_batch_draw_range(batch_quads, 0, quads_num * 6);
    quads_num = 0;
    verts_quads = nullptr;
  }
  if (lines_num > 0) {
    GPU_vertbuf_tag_dirty(vbo_lines);
    GPU_vertbuf_use(vbo_lines);
    GPU_batch_draw_range(batch_lines, 0, lines_num * 2);
    lines_num = 0;
    verts_lines = nullptr;
  }
}

void SeqQuadsBatch::add_quad(float x1,
                             float y1,
                             float x2,
                             float y2,
                             float x3,
                             float y3,
                             float x4,
                             float y4,
                             const uchar color[4])
{
  if (quads_num >= MAX_QUADS) {
    draw();
  }
  if (quads_num == 0) {
    verts_quads = static_cast<ColorVertex *>(GPU_vertbuf_get_data(vbo_quads));
    BLI_assert(verts_quads != nullptr);
  }

  ColorVertex v0 = {blender::float2(x1, y1), color};
  ColorVertex v1 = {blender::float2(x2, y2), color};
  ColorVertex v2 = {blender::float2(x3, y3), color};
  ColorVertex v3 = {blender::float2(x4, y4), color};

  *verts_quads++ = v0;
  *verts_quads++ = v1;
  *verts_quads++ = v2;
  *verts_quads++ = v3;

  quads_num++;
}

void SeqQuadsBatch::add_wire_quad(float x1, float y1, float x2, float y2, const uchar color[4])
{
  if (lines_num + 4 > MAX_LINES) {
    draw();
  }
  if (lines_num == 0) {
    verts_lines = static_cast<ColorVertex *>(GPU_vertbuf_get_data(vbo_lines));
    BLI_assert(verts_lines != nullptr);
  }

  ColorVertex v0 = {blender::float2(x1, y1), color};
  ColorVertex v1 = {blender::float2(x1, y2), color};
  ColorVertex v2 = {blender::float2(x2, y1), color};
  ColorVertex v3 = {blender::float2(x2, y2), color};

  /* Left */
  *verts_lines++ = v0;
  *verts_lines++ = v1;
  /* Right */
  *verts_lines++ = v2;
  *verts_lines++ = v3;
  /* Bottom */
  *verts_lines++ = v0;
  *verts_lines++ = v2;
  /* Top */
  *verts_lines++ = v1;
  *verts_lines++ = v3;

  lines_num += 4;
}

void SeqQuadsBatch::add_line(float x1, float y1, float x2, float y2, const uchar color[4])
{
  if (lines_num + 1 > MAX_LINES) {
    draw();
  }
  if (lines_num == 0) {
    verts_lines = static_cast<ColorVertex *>(GPU_vertbuf_get_data(vbo_lines));
    BLI_assert(verts_lines != nullptr);
  }

  ColorVertex v0 = {blender::float2(x1, y1), color};
  ColorVertex v1 = {blender::float2(x2, y2), color};

  *verts_lines++ = v0;
  *verts_lines++ = v1;

  lines_num++;
}

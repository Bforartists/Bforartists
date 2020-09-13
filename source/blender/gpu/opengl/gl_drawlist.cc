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
 * The Original Code is Copyright (C) 2016 by Mike Erwin.
 * All rights reserved.
 */

/** \file
 * \ingroup gpu
 *
 * Implementation of Multi Draw Indirect using OpenGL.
 * Fallback if the needed extensions are not supported.
 */

#include "BLI_assert.h"

#include "GPU_batch.h"
#include "GPU_capabilities.h"

#include "glew-mx.h"

#include "gpu_context_private.hh"
#include "gpu_drawlist_private.hh"
#include "gpu_vertex_buffer_private.hh"

#include "gl_backend.hh"
#include "gl_drawlist.hh"
#include "gl_primitive.hh"

#include <limits.h>

using namespace blender::gpu;

typedef struct GLDrawCommand {
  GLuint v_count;
  GLuint i_count;
  GLuint v_first;
  GLuint i_first;
} GLDrawCommand;

typedef struct GLDrawCommandIndexed {
  GLuint v_count;
  GLuint i_count;
  GLuint v_first;
  GLuint base_index;
  GLuint i_first;
} GLDrawCommandIndexed;

#define MDI_ENABLED (buffer_size_ != 0)
#define MDI_DISABLED (buffer_size_ == 0)
#define MDI_INDEXED (base_index_ != UINT_MAX)

GLDrawList::GLDrawList(int length)
{
  BLI_assert(length > 0);
  batch_ = NULL;
  buffer_id_ = 0;
  command_len_ = 0;
  command_offset_ = 0;
  data_offset_ = 0;
  data_size_ = 0;
  data_ = NULL;

  if (GLContext::multi_draw_indirect_support) {
    /* Alloc the biggest possible command list, which is indexed. */
    buffer_size_ = sizeof(GLDrawCommandIndexed) * length;
  }
  else {
    /* Indicates MDI is not supported. */
    buffer_size_ = 0;
  }
}

GLDrawList::~GLDrawList()
{
  GLContext::buf_free(buffer_id_);
}

void GLDrawList::init(void)
{
  BLI_assert(GLContext::get());
  BLI_assert(MDI_ENABLED);
  BLI_assert(data_ == NULL);
  batch_ = NULL;
  command_len_ = 0;

  if (buffer_id_ == 0) {
    /* Allocate on first use. */
    glGenBuffers(1, &buffer_id_);
    context_ = GLContext::get();
  }

  glBindBuffer(GL_DRAW_INDIRECT_BUFFER, buffer_id_);
  /* If buffer is full, orphan buffer data and start fresh. */
  // if (command_offset_ >= data_size_) {
  glBufferData(GL_DRAW_INDIRECT_BUFFER, buffer_size_, NULL, GL_DYNAMIC_DRAW);
  data_offset_ = 0;
  // }
  /* Map the remaining range. */
  GLbitfield flag = GL_MAP_WRITE_BIT | GL_MAP_UNSYNCHRONIZED_BIT | GL_MAP_FLUSH_EXPLICIT_BIT;
  data_size_ = buffer_size_ - data_offset_;
  data_ = (GLbyte *)glMapBufferRange(GL_DRAW_INDIRECT_BUFFER, data_offset_, data_size_, flag);
  command_offset_ = 0;
}

void GLDrawList::append(GPUBatch *gpu_batch, int i_first, int i_count)
{
  /* Fallback when MultiDrawIndirect is not supported/enabled. */
  if (MDI_DISABLED) {
    GPU_batch_draw_advanced(gpu_batch, 0, 0, i_first, i_count);
    return;
  }

  if (data_ == NULL) {
    this->init();
  }

  GLBatch *batch = static_cast<GLBatch *>(gpu_batch);
  if (batch != batch_) {
    // BLI_assert(batch->flag | GPU_BATCH_INIT);
    this->submit();
    batch_ = batch;
    /* Cached for faster access. */
    GLIndexBuf *el = batch_->elem_();
    base_index_ = el ? el->index_base_ : UINT_MAX;
    v_first_ = el ? el->index_start_ : 0;
    v_count_ = el ? el->index_len_ : batch->verts_(0)->vertex_len;
  }

  if (v_count_ == 0) {
    /* Nothing to draw. */
    return;
  }

  if (MDI_INDEXED) {
    GLDrawCommandIndexed *cmd = reinterpret_cast<GLDrawCommandIndexed *>(data_ + command_offset_);
    cmd->v_first = v_first_;
    cmd->v_count = v_count_;
    cmd->i_count = i_count;
    cmd->base_index = base_index_;
    cmd->i_first = i_first;
    command_offset_ += sizeof(GLDrawCommandIndexed);
  }
  else {
    GLDrawCommand *cmd = reinterpret_cast<GLDrawCommand *>(data_ + command_offset_);
    cmd->v_first = v_first_;
    cmd->v_count = v_count_;
    cmd->i_count = i_count;
    cmd->i_first = i_first;
    command_offset_ += sizeof(GLDrawCommand);
  }

  command_len_++;

  if (command_offset_ >= data_size_) {
    this->submit();
  }
}

void GLDrawList::submit(void)
{
  if (command_len_ == 0) {
    return;
  }
  /* Something's wrong if we get here without MDI support. */
  BLI_assert(MDI_ENABLED);
  BLI_assert(data_);
  BLI_assert(GLContext::get()->shader != NULL);

  /* Only do multi-draw indirect if doing more than 2 drawcall. This avoids the overhead of
   * buffer mapping if scene is not very instance friendly. BUT we also need to take into
   * account the case where only a few instances are needed to finish filling a call buffer. */
  const bool is_finishing_a_buffer = (command_offset_ >= data_size_);
  if (command_len_ > 2 || is_finishing_a_buffer) {
    GLenum prim = to_gl(batch_->prim_type);
    void *offset = (void *)data_offset_;

    glBindBuffer(GL_DRAW_INDIRECT_BUFFER, buffer_id_);
    glFlushMappedBufferRange(GL_DRAW_INDIRECT_BUFFER, 0, command_offset_);
    glUnmapBuffer(GL_DRAW_INDIRECT_BUFFER);
    data_ = NULL; /* Unmapped */
    data_offset_ += command_offset_;

    batch_->bind(0);

    if (MDI_INDEXED) {
      GLenum gl_type = to_gl(batch_->elem_()->index_type_);
      glMultiDrawElementsIndirect(prim, gl_type, offset, command_len_, 0);
    }
    else {
      glMultiDrawArraysIndirect(prim, offset, command_len_, 0);
    }
  }
  else {
    /* Fallback do simple drawcalls, and don't unmap the buffer. */
    if (MDI_INDEXED) {
      GLDrawCommandIndexed *cmd = (GLDrawCommandIndexed *)data_;
      for (int i = 0; i < command_len_; i++, cmd++) {
        /* Index start was already added. Avoid counting it twice. */
        cmd->v_first -= v_first_;
        batch_->draw(cmd->v_first, cmd->v_count, cmd->i_first, cmd->i_count);
      }
      /* Reuse the same data. */
      command_offset_ -= command_len_ * sizeof(GLDrawCommandIndexed);
    }
    else {
      GLDrawCommand *cmd = (GLDrawCommand *)data_;
      for (int i = 0; i < command_len_; i++, cmd++) {
        batch_->draw(cmd->v_first, cmd->v_count, cmd->i_first, cmd->i_count);
      }
      /* Reuse the same data. */
      command_offset_ -= command_len_ * sizeof(GLDrawCommand);
    }
  }
  /* Do not submit this buffer again. */
  command_len_ = 0;
  /* Avoid keeping reference to the batch. */
  batch_ = NULL;
}

/** \} */

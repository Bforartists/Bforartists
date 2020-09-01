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
 * Copyright 2020, Blender Foundation.
 * All rights reserved.
 */

/** \file
 * \ingroup gpu
 *
 * GPUBackend derived class contain allocators that do not need a context bound.
 * The backend is init at startup and is accessible using GPU_backend_get() */

#pragma once

struct GPUContext;

namespace blender {
namespace gpu {

class Batch;
class DrawList;
class FrameBuffer;
class Shader;
class UniformBuf;

class GPUBackend {
 public:
  virtual ~GPUBackend(){};

  static GPUBackend *get(void);

  virtual GPUContext *context_alloc(void *ghost_window) = 0;

  virtual Batch *batch_alloc(void) = 0;
  virtual DrawList *drawlist_alloc(int list_length) = 0;
  virtual FrameBuffer *framebuffer_alloc(const char *name) = 0;
  virtual Shader *shader_alloc(const char *name) = 0;
  // virtual Texture *texture_alloc(void) = 0;
  virtual UniformBuf *uniformbuf_alloc(int size, const char *name) = 0;
};

}  // namespace gpu
}  // namespace blender

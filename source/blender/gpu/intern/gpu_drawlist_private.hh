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
 * The Original Code is Copyright (C) 2020 Blender Foundation.
 * All rights reserved.
 */

/** \file
 * \ingroup gpu
 */

#pragma once

#include "MEM_guardedalloc.h"

#include "GPU_drawlist.h"

namespace blender {
namespace gpu {

/**
 * Implementation of Multi Draw Indirect.
 * Base class which is then specialized for each implementation (GL, VK, ...).
 */
class DrawList {
 public:
  virtual ~DrawList(){};

  virtual void append(GPUBatch *batch, int i_first, int i_count) = 0;
  virtual void submit() = 0;
};

/* Syntactic sugar. */
static inline GPUDrawList *wrap(DrawList *vert)
{
  return reinterpret_cast<GPUDrawList *>(vert);
}
static inline DrawList *unwrap(GPUDrawList *vert)
{
  return reinterpret_cast<DrawList *>(vert);
}
static inline const DrawList *unwrap(const GPUDrawList *vert)
{
  return reinterpret_cast<const DrawList *>(vert);
}

}  // namespace gpu
}  // namespace blender

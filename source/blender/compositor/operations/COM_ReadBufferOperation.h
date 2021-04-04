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
 * Copyright 2011, Blender Foundation.
 */

#pragma once

#include "COM_MemoryBuffer.h"
#include "COM_MemoryProxy.h"
#include "COM_NodeOperation.h"

namespace blender::compositor {

class ReadBufferOperation : public NodeOperation {
 private:
  MemoryProxy *m_memoryProxy;
  bool m_single_value; /* single value stored in buffer, copied from associated write operation */
  unsigned int m_offset;
  MemoryBuffer *m_buffer;

 public:
  ReadBufferOperation(DataType datatype);
  void setMemoryProxy(MemoryProxy *memoryProxy)
  {
    this->m_memoryProxy = memoryProxy;
  }

  MemoryProxy *getMemoryProxy() const
  {
    return this->m_memoryProxy;
  }

  void determineResolution(unsigned int resolution[2],
                           unsigned int preferredResolution[2]) override;

  void *initializeTileData(rcti *rect) override;
  void executePixelSampled(float output[4], float x, float y, PixelSampler sampler) override;
  void executePixelExtend(float output[4],
                          float x,
                          float y,
                          PixelSampler sampler,
                          MemoryBufferExtend extend_x,
                          MemoryBufferExtend extend_y);
  void executePixelFiltered(float output[4], float x, float y, float dx[2], float dy[2]) override;
  void setOffset(unsigned int offset)
  {
    this->m_offset = offset;
  }
  unsigned int getOffset() const
  {
    return this->m_offset;
  }
  bool determineDependingAreaOfInterest(rcti *input,
                                        ReadBufferOperation *readOperation,
                                        rcti *output) override;
  MemoryBuffer *getInputMemoryBuffer(MemoryBuffer **memoryBuffers) override
  {
    return memoryBuffers[this->m_offset];
  }
  void readResolutionFromWriteBuffer();
  void updateMemoryBuffer();
};

}  // namespace blender::compositor

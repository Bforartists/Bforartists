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
 * Copyright 2021, Blender Foundation.
 */

#pragma once

#include "COM_NodeOperation.h"

namespace blender::compositor {

class MultiThreadedOperation : public NodeOperation {
 protected:
  /**
   * Number of execution passes.
   */
  int m_num_passes;

 protected:
  MultiThreadedOperation();

  /**
   * Called before an update memory buffer pass is executed. Single-threaded calls.
   */
  virtual void update_memory_buffer_started(MemoryBuffer *UNUSED(output),
                                            const rcti &UNUSED(output_rect),
                                            blender::Span<MemoryBuffer *> UNUSED(inputs),
                                            ExecutionSystem &UNUSED(exec_system),
                                            int UNUSED(current_pass))
  {
  }

  /**
   * Executes operation updating output memory buffer on output_rect area. Multi-threaded calls.
   */
  virtual void update_memory_buffer_partial(MemoryBuffer *output,
                                            const rcti &output_rect,
                                            blender::Span<MemoryBuffer *> inputs,
                                            ExecutionSystem &exec_system,
                                            int current_pass) = 0;

  /**
   * Called after an update memory buffer pass is executed. Single-threaded calls.
   */
  virtual void update_memory_buffer_finished(MemoryBuffer *UNUSED(output),
                                             const rcti &UNUSED(output_rect),
                                             blender::Span<MemoryBuffer *> UNUSED(inputs),
                                             ExecutionSystem &UNUSED(exec_system),
                                             int UNUSED(current_pass))
  {
  }

 private:
  void update_memory_buffer(MemoryBuffer *output,
                            const rcti &output_area,
                            blender::Span<MemoryBuffer *> inputs,
                            ExecutionSystem &exec_system) override;
};

}  // namespace blender::compositor

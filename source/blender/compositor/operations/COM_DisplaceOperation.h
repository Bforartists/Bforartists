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

#include "COM_MultiThreadedOperation.h"

namespace blender::compositor {

class DisplaceOperation : public MultiThreadedOperation {
 private:
  /**
   * Cached reference to the inputProgram
   */
  SocketReader *m_inputColorProgram;

  float m_width_x4;
  float m_height_x4;

  int input_vector_width_;
  int input_vector_height_;

  std::function<void(float x, float y, float *out)> vector_read_fn_;
  std::function<void(float x, float y, float *out)> scale_x_read_fn_;
  std::function<void(float x, float y, float *out)> scale_y_read_fn_;

 public:
  DisplaceOperation();

  /**
   * we need a 2x2 differential filter for Vector Input and full buffer for the image
   */
  bool determineDependingAreaOfInterest(rcti *input,
                                        ReadBufferOperation *readOperation,
                                        rcti *output) override;

  /**
   * The inner loop of this operation.
   */
  void executePixelSampled(float output[4], float x, float y, PixelSampler sampler) override;

  void pixelTransform(const float xy[2], float r_uv[2], float r_deriv[2][2]);

  /**
   * Initialize the execution
   */
  void initExecution() override;

  /**
   * Deinitialize the execution
   */
  void deinitExecution() override;

  void get_area_of_interest(int input_idx, const rcti &output_area, rcti &r_input_area) override;
  void update_memory_buffer_started(MemoryBuffer *output,
                                    const rcti &area,
                                    Span<MemoryBuffer *> inputs) override;
  void update_memory_buffer_partial(MemoryBuffer *output,
                                    const rcti &area,
                                    Span<MemoryBuffer *> inputs) override;

 private:
  bool read_displacement(
      float x, float y, float xscale, float yscale, const float origin[2], float &r_u, float &r_v);
};

}  // namespace blender::compositor

/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#pragma once

#include "COM_MultiThreadedOperation.h"

namespace blender::compositor {

class KuwaharaClassicOperation : public MultiThreadedOperation {
  SocketReader *image_reader_;
  SocketReader *size_reader_;
  SocketReader *sat_reader_;
  SocketReader *sat_squared_reader_;

 public:
  KuwaharaClassicOperation();

  void init_execution() override;
  void deinit_execution() override;
  void execute_pixel_sampled(float output[4], float x, float y, PixelSampler sampler) override;

  void update_memory_buffer_partial(MemoryBuffer *output,
                                    const rcti &area,
                                    Span<MemoryBuffer *> inputs) override;
};

}  // namespace blender::compositor

/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#pragma once

#include "DNA_node_types.h"

#include "COM_MultiThreadedOperation.h"

namespace blender::compositor {

class KuwaharaAnisotropicOperation : public MultiThreadedOperation {
 public:
  float sharpness_;
  float eccentricity_;

  KuwaharaAnisotropicOperation();

  void update_memory_buffer_partial(MemoryBuffer *output,
                                    const rcti &area,
                                    Span<MemoryBuffer *> inputs) override;
  float get_sharpness();
  float get_eccentricity();
  void set_sharpness(float sharpness);
  void set_eccentricity(float eccentricity);
};

}  // namespace blender::compositor

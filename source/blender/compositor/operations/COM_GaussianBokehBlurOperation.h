/* SPDX-FileCopyrightText: 2011 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#pragma once

#include <memory>

#include "COM_BlurBaseOperation.h"
#include "COM_NodeOperation.h"
#include "COM_QualityStepHelper.h"

namespace blender::compositor {

class GaussianBokehBlurOperation : public BlurBaseOperation {
 private:
  float *gausstab_;
  int radx_, rady_;
  float radxf_;
  float radyf_;
  void update_gauss();

 public:
  GaussianBokehBlurOperation();
  void init_data() override;
  void init_execution() override;
  void deinit_execution() override;

  void get_area_of_interest(int input_idx, const rcti &output_area, rcti &r_input_area) override;
  void update_memory_buffer_partial(MemoryBuffer *output,
                                    const rcti &area,
                                    Span<MemoryBuffer *> inputs) override;
};

class GaussianBlurReferenceOperation : public BlurBaseOperation {
 private:
  std::unique_ptr<MemoryBuffer> weights_;

  void update_gauss();
  int filtersizex_;
  int filtersizey_;
  float radx_;
  float rady_;

 public:
  GaussianBlurReferenceOperation();
  void init_data() override;
  void init_execution() override;

  void get_area_of_interest(int input_idx, const rcti &output_area, rcti &r_input_area) override;
  void update_memory_buffer_partial(MemoryBuffer *output,
                                    const rcti &area,
                                    Span<MemoryBuffer *> inputs) override;
};

}  // namespace blender::compositor

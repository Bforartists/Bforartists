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

#include "COM_GaussianAlphaBlurBaseOperation.h"

namespace blender::compositor {

GaussianAlphaBlurBaseOperation::GaussianAlphaBlurBaseOperation(eDimension dim)
    : BlurBaseOperation(DataType::Value)
{
  this->m_gausstab = nullptr;
  this->m_filtersize = 0;
  this->m_falloff = -1; /* Intentionally invalid, so we can detect uninitialized values. */
  dimension_ = dim;
}

void GaussianAlphaBlurBaseOperation::init_data()
{
  BlurBaseOperation::init_data();
  if (execution_model_ == eExecutionModel::FullFrame) {
    rad_ = max_ff(m_size * this->get_blur_size(dimension_), 0.0f);
    rad_ = min_ff(rad_, MAX_GAUSSTAB_RADIUS);
    m_filtersize = min_ii(ceil(rad_), MAX_GAUSSTAB_RADIUS);
  }
}

void GaussianAlphaBlurBaseOperation::initExecution()
{
  BlurBaseOperation::initExecution();
  if (execution_model_ == eExecutionModel::FullFrame) {
    m_gausstab = BlurBaseOperation::make_gausstab(rad_, m_filtersize);
    m_distbuf_inv = BlurBaseOperation::make_dist_fac_inverse(rad_, m_filtersize, m_falloff);
  }
}

void GaussianAlphaBlurBaseOperation::deinitExecution()
{
  BlurBaseOperation::deinitExecution();

  if (this->m_gausstab) {
    MEM_freeN(this->m_gausstab);
    this->m_gausstab = nullptr;
  }

  if (this->m_distbuf_inv) {
    MEM_freeN(this->m_distbuf_inv);
    this->m_distbuf_inv = nullptr;
  }
}

void GaussianAlphaBlurBaseOperation::get_area_of_interest(const int input_idx,
                                                          const rcti &output_area,
                                                          rcti &r_input_area)
{
  if (input_idx != IMAGE_INPUT_INDEX) {
    BlurBaseOperation::get_area_of_interest(input_idx, output_area, r_input_area);
    return;
  }

  r_input_area = output_area;
  switch (dimension_) {
    case eDimension::X:
      r_input_area.xmin = output_area.xmin - m_filtersize - 1;
      r_input_area.xmax = output_area.xmax + m_filtersize + 1;
      break;
    case eDimension::Y:
      r_input_area.ymin = output_area.ymin - m_filtersize - 1;
      r_input_area.ymax = output_area.ymax + m_filtersize + 1;
      break;
  }
}

BLI_INLINE float finv_test(const float f, const bool test)
{
  return (LIKELY(test == false)) ? f : 1.0f - f;
}

void GaussianAlphaBlurBaseOperation::update_memory_buffer_partial(MemoryBuffer *output,
                                                                  const rcti &area,
                                                                  Span<MemoryBuffer *> inputs)
{
  MemoryBuffer *input = inputs[IMAGE_INPUT_INDEX];
  const rcti &input_rect = input->get_rect();
  BuffersIterator<float> it = output->iterate_with({input}, area);

  int min_input_coord = -1;
  int max_input_coord = -1;
  int elem_stride = -1;
  std::function<int()> get_current_coord;
  switch (dimension_) {
    case eDimension::X:
      min_input_coord = input_rect.xmin;
      max_input_coord = input_rect.xmax;
      get_current_coord = [&] { return it.x; };
      elem_stride = input->elem_stride;
      break;
    case eDimension::Y:
      min_input_coord = input_rect.ymin;
      max_input_coord = input_rect.ymax;
      get_current_coord = [&] { return it.y; };
      elem_stride = input->row_stride;
      break;
  }

  for (; !it.is_end(); ++it) {
    const int coord = get_current_coord();
    const int coord_min = max_ii(coord - m_filtersize, min_input_coord);
    const int coord_max = min_ii(coord + m_filtersize + 1, max_input_coord);

    /* *** This is the main part which is different to #GaussianBlurBaseOperation.  *** */
    /* Gauss. */
    float alpha_accum = 0.0f;
    float multiplier_accum = 0.0f;

    /* Dilate. */
    const bool do_invert = m_do_subtract;
    /* Init with the current color to avoid unneeded lookups. */
    float value_max = finv_test(*it.in(0), do_invert);
    float distfacinv_max = 1.0f; /* 0 to 1 */

    const int step = QualityStepHelper::getStep();
    const float *in = it.in(0) + ((intptr_t)coord_min - coord) * elem_stride;
    const int in_stride = elem_stride * step;
    int index = (coord_min - coord) + m_filtersize;
    const int index_end = index + (coord_max - coord_min);
    for (; index < index_end; in += in_stride, index += step) {
      float value = finv_test(*in, do_invert);

      /* Gauss. */
      float multiplier = m_gausstab[index];
      alpha_accum += value * multiplier;
      multiplier_accum += multiplier;

      /* Dilate - find most extreme color. */
      if (value > value_max) {
        multiplier = m_distbuf_inv[index];
        value *= multiplier;
        if (value > value_max) {
          value_max = value;
          distfacinv_max = multiplier;
        }
      }
    }

    /* Blend between the max value and gauss blue - gives nice feather. */
    const float value_blur = alpha_accum / multiplier_accum;
    const float value_final = (value_max * distfacinv_max) +
                              (value_blur * (1.0f - distfacinv_max));
    *it.out = finv_test(value_final, do_invert);
  }
}

}  // namespace blender::compositor

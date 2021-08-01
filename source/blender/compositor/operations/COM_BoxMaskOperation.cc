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

#include "COM_BoxMaskOperation.h"
#include "BLI_math.h"
#include "DNA_node_types.h"

namespace blender::compositor {

BoxMaskOperation::BoxMaskOperation()
{
  this->addInputSocket(DataType::Value);
  this->addInputSocket(DataType::Value);
  this->addOutputSocket(DataType::Value);
  this->m_inputMask = nullptr;
  this->m_inputValue = nullptr;
  this->m_cosine = 0.0f;
  this->m_sine = 0.0f;
}
void BoxMaskOperation::initExecution()
{
  this->m_inputMask = this->getInputSocketReader(0);
  this->m_inputValue = this->getInputSocketReader(1);
  const double rad = (double)this->m_data->rotation;
  this->m_cosine = cos(rad);
  this->m_sine = sin(rad);
  this->m_aspectRatio = ((float)this->getWidth()) / this->getHeight();
}

void BoxMaskOperation::executePixelSampled(float output[4], float x, float y, PixelSampler sampler)
{
  float inputMask[4];
  float inputValue[4];

  float rx = x / this->getWidth();
  float ry = y / this->getHeight();

  const float dy = (ry - this->m_data->y) / this->m_aspectRatio;
  const float dx = rx - this->m_data->x;
  rx = this->m_data->x + (this->m_cosine * dx + this->m_sine * dy);
  ry = this->m_data->y + (-this->m_sine * dx + this->m_cosine * dy);

  this->m_inputMask->readSampled(inputMask, x, y, sampler);
  this->m_inputValue->readSampled(inputValue, x, y, sampler);

  float halfHeight = this->m_data->height / 2.0f;
  float halfWidth = this->m_data->width / 2.0f;
  bool inside = (rx > this->m_data->x - halfWidth && rx < this->m_data->x + halfWidth &&
                 ry > this->m_data->y - halfHeight && ry < this->m_data->y + halfHeight);

  switch (this->m_maskType) {
    case CMP_NODE_MASKTYPE_ADD:
      if (inside) {
        output[0] = MAX2(inputMask[0], inputValue[0]);
      }
      else {
        output[0] = inputMask[0];
      }
      break;
    case CMP_NODE_MASKTYPE_SUBTRACT:
      if (inside) {
        output[0] = inputMask[0] - inputValue[0];
        CLAMP(output[0], 0, 1);
      }
      else {
        output[0] = inputMask[0];
      }
      break;
    case CMP_NODE_MASKTYPE_MULTIPLY:
      if (inside) {
        output[0] = inputMask[0] * inputValue[0];
      }
      else {
        output[0] = 0;
      }
      break;
    case CMP_NODE_MASKTYPE_NOT:
      if (inside) {
        if (inputMask[0] > 0.0f) {
          output[0] = 0;
        }
        else {
          output[0] = inputValue[0];
        }
      }
      else {
        output[0] = inputMask[0];
      }
      break;
  }
}

void BoxMaskOperation::update_memory_buffer_partial(MemoryBuffer *output,
                                                    const rcti &area,
                                                    Span<MemoryBuffer *> inputs)
{
  MaskFunc mask_func;
  switch (m_maskType) {
    case CMP_NODE_MASKTYPE_ADD:
      mask_func = [](const bool is_inside, const float *mask, const float *value) {
        return is_inside ? MAX2(mask[0], value[0]) : mask[0];
      };
      break;
    case CMP_NODE_MASKTYPE_SUBTRACT:
      mask_func = [](const bool is_inside, const float *mask, const float *value) {
        return is_inside ? CLAMPIS(mask[0] - value[0], 0, 1) : mask[0];
      };
      break;
    case CMP_NODE_MASKTYPE_MULTIPLY:
      mask_func = [](const bool is_inside, const float *mask, const float *value) {
        return is_inside ? mask[0] * value[0] : 0;
      };
      break;
    case CMP_NODE_MASKTYPE_NOT:
      mask_func = [](const bool is_inside, const float *mask, const float *value) {
        if (is_inside) {
          return mask[0] > 0.0f ? 0.0f : value[0];
        }
        return mask[0];
      };
      break;
  }
  apply_mask(output, area, inputs, mask_func);
}

void BoxMaskOperation::apply_mask(MemoryBuffer *output,
                                  const rcti &area,
                                  Span<MemoryBuffer *> inputs,
                                  MaskFunc mask_func)
{
  const float op_w = this->getWidth();
  const float op_h = this->getHeight();
  const float half_w = this->m_data->width / 2.0f;
  const float half_h = this->m_data->height / 2.0f;
  for (BuffersIterator<float> it = output->iterate_with(inputs, area); !it.is_end(); ++it) {
    const float op_ry = it.y / op_h;
    const float dy = (op_ry - this->m_data->y) / m_aspectRatio;
    const float op_rx = it.x / op_w;
    const float dx = op_rx - this->m_data->x;
    const float rx = this->m_data->x + (m_cosine * dx + m_sine * dy);
    const float ry = this->m_data->y + (-m_sine * dx + m_cosine * dy);

    const bool inside = (rx > this->m_data->x - half_w && rx < this->m_data->x + half_w &&
                         ry > this->m_data->y - half_h && ry < this->m_data->y + half_h);
    const float *mask = it.in(0);
    const float *value = it.in(1);
    *it.out = mask_func(inside, mask, value);
  }
}

void BoxMaskOperation::deinitExecution()
{
  this->m_inputMask = nullptr;
  this->m_inputValue = nullptr;
}

}  // namespace blender::compositor

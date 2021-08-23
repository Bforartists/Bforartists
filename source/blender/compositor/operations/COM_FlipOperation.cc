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

#include "COM_FlipOperation.h"

namespace blender::compositor {

FlipOperation::FlipOperation()
{
  this->addInputSocket(DataType::Color);
  this->addOutputSocket(DataType::Color);
  this->setResolutionInputSocketIndex(0);
  this->m_inputOperation = nullptr;
  this->m_flipX = true;
  this->m_flipY = false;
}
void FlipOperation::initExecution()
{
  this->m_inputOperation = this->getInputSocketReader(0);
}

void FlipOperation::deinitExecution()
{
  this->m_inputOperation = nullptr;
}

void FlipOperation::executePixelSampled(float output[4], float x, float y, PixelSampler sampler)
{
  float nx = this->m_flipX ? ((int)this->getWidth() - 1) - x : x;
  float ny = this->m_flipY ? ((int)this->getHeight() - 1) - y : y;

  this->m_inputOperation->readSampled(output, nx, ny, sampler);
}

bool FlipOperation::determineDependingAreaOfInterest(rcti *input,
                                                     ReadBufferOperation *readOperation,
                                                     rcti *output)
{
  rcti newInput;

  if (this->m_flipX) {
    const int w = (int)this->getWidth() - 1;
    newInput.xmax = (w - input->xmin) + 1;
    newInput.xmin = (w - input->xmax) - 1;
  }
  else {
    newInput.xmin = input->xmin;
    newInput.xmax = input->xmax;
  }
  if (this->m_flipY) {
    const int h = (int)this->getHeight() - 1;
    newInput.ymax = (h - input->ymin) + 1;
    newInput.ymin = (h - input->ymax) - 1;
  }
  else {
    newInput.ymin = input->ymin;
    newInput.ymax = input->ymax;
  }

  return NodeOperation::determineDependingAreaOfInterest(&newInput, readOperation, output);
}

void FlipOperation::get_area_of_interest(const int input_idx,
                                         const rcti &output_area,
                                         rcti &r_input_area)
{
  BLI_assert(input_idx == 0);
  UNUSED_VARS_NDEBUG(input_idx);
  if (this->m_flipX) {
    const int w = (int)this->getWidth() - 1;
    r_input_area.xmax = (w - output_area.xmin) + 1;
    r_input_area.xmin = (w - output_area.xmax) - 1;
  }
  else {
    r_input_area.xmin = output_area.xmin;
    r_input_area.xmax = output_area.xmax;
  }
  if (this->m_flipY) {
    const int h = (int)this->getHeight() - 1;
    r_input_area.ymax = (h - output_area.ymin) + 1;
    r_input_area.ymin = (h - output_area.ymax) - 1;
  }
  else {
    r_input_area.ymin = output_area.ymin;
    r_input_area.ymax = output_area.ymax;
  }
}

void FlipOperation::update_memory_buffer_partial(MemoryBuffer *output,
                                                 const rcti &area,
                                                 Span<MemoryBuffer *> inputs)
{
  const MemoryBuffer *input_img = inputs[0];
  for (BuffersIterator<float> it = output->iterate_with({}, area); !it.is_end(); ++it) {
    const int nx = this->m_flipX ? ((int)this->getWidth() - 1) - it.x : it.x;
    const int ny = this->m_flipY ? ((int)this->getHeight() - 1) - it.y : it.y;
    input_img->read_elem(nx, ny, it.out);
  }
}

}  // namespace blender::compositor

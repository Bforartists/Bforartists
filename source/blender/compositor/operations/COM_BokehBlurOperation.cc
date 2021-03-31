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

#include "COM_BokehBlurOperation.h"
#include "BLI_math.h"
#include "COM_OpenCLDevice.h"

#include "RE_pipeline.h"

namespace blender::compositor {

BokehBlurOperation::BokehBlurOperation()
{
  this->addInputSocket(DataType::Color);
  this->addInputSocket(DataType::Color, ResizeMode::None);
  this->addInputSocket(DataType::Value);
  this->addInputSocket(DataType::Value);
  this->addOutputSocket(DataType::Color);

  flags.complex = true;
  flags.open_cl = true;

  this->m_size = 1.0f;
  this->m_sizeavailable = false;
  this->m_inputProgram = nullptr;
  this->m_inputBokehProgram = nullptr;
  this->m_inputBoundingBoxReader = nullptr;

  this->m_extend_bounds = false;
}

void *BokehBlurOperation::initializeTileData(rcti * /*rect*/)
{
  lockMutex();
  if (!this->m_sizeavailable) {
    updateSize();
  }
  void *buffer = getInputOperation(0)->initializeTileData(nullptr);
  unlockMutex();
  return buffer;
}

void BokehBlurOperation::initExecution()
{
  initMutex();
  this->m_inputProgram = getInputSocketReader(0);
  this->m_inputBokehProgram = getInputSocketReader(1);
  this->m_inputBoundingBoxReader = getInputSocketReader(2);

  int width = this->m_inputBokehProgram->getWidth();
  int height = this->m_inputBokehProgram->getHeight();

  float dimension = MIN2(width, height);

  this->m_bokehMidX = width / 2.0f;
  this->m_bokehMidY = height / 2.0f;
  this->m_bokehDimension = dimension / 2.0f;
  QualityStepHelper::initExecution(COM_QH_INCREASE);
}

void BokehBlurOperation::executePixel(float output[4], int x, int y, void *data)
{
  float color_accum[4];
  float tempBoundingBox[4];
  float bokeh[4];

  this->m_inputBoundingBoxReader->readSampled(tempBoundingBox, x, y, PixelSampler::Nearest);
  if (tempBoundingBox[0] > 0.0f) {
    float multiplier_accum[4] = {0.0f, 0.0f, 0.0f, 0.0f};
    MemoryBuffer *inputBuffer = (MemoryBuffer *)data;
    const rcti &input_rect = inputBuffer->get_rect();
    float *buffer = inputBuffer->getBuffer();
    int bufferwidth = inputBuffer->getWidth();
    int bufferstartx = input_rect.xmin;
    int bufferstarty = input_rect.ymin;
    const float max_dim = MAX2(this->getWidth(), this->getHeight());
    int pixelSize = this->m_size * max_dim / 100.0f;
    zero_v4(color_accum);

    if (pixelSize < 2) {
      this->m_inputProgram->readSampled(color_accum, x, y, PixelSampler::Nearest);
      multiplier_accum[0] = 1.0f;
      multiplier_accum[1] = 1.0f;
      multiplier_accum[2] = 1.0f;
      multiplier_accum[3] = 1.0f;
    }
    int miny = y - pixelSize;
    int maxy = y + pixelSize;
    int minx = x - pixelSize;
    int maxx = x + pixelSize;
    miny = MAX2(miny, input_rect.ymin);
    minx = MAX2(minx, input_rect.xmin);
    maxy = MIN2(maxy, input_rect.ymax);
    maxx = MIN2(maxx, input_rect.xmax);

    int step = getStep();
    int offsetadd = getOffsetAdd() * COM_DATA_TYPE_COLOR_CHANNELS;

    float m = this->m_bokehDimension / pixelSize;
    for (int ny = miny; ny < maxy; ny += step) {
      int bufferindex = ((minx - bufferstartx) * COM_DATA_TYPE_COLOR_CHANNELS) +
                        ((ny - bufferstarty) * COM_DATA_TYPE_COLOR_CHANNELS * bufferwidth);
      for (int nx = minx; nx < maxx; nx += step) {
        float u = this->m_bokehMidX - (nx - x) * m;
        float v = this->m_bokehMidY - (ny - y) * m;
        this->m_inputBokehProgram->readSampled(bokeh, u, v, PixelSampler::Nearest);
        madd_v4_v4v4(color_accum, bokeh, &buffer[bufferindex]);
        add_v4_v4(multiplier_accum, bokeh);
        bufferindex += offsetadd;
      }
    }
    output[0] = color_accum[0] * (1.0f / multiplier_accum[0]);
    output[1] = color_accum[1] * (1.0f / multiplier_accum[1]);
    output[2] = color_accum[2] * (1.0f / multiplier_accum[2]);
    output[3] = color_accum[3] * (1.0f / multiplier_accum[3]);
  }
  else {
    this->m_inputProgram->readSampled(output, x, y, PixelSampler::Nearest);
  }
}

void BokehBlurOperation::deinitExecution()
{
  deinitMutex();
  this->m_inputProgram = nullptr;
  this->m_inputBokehProgram = nullptr;
  this->m_inputBoundingBoxReader = nullptr;
}

bool BokehBlurOperation::determineDependingAreaOfInterest(rcti *input,
                                                          ReadBufferOperation *readOperation,
                                                          rcti *output)
{
  rcti newInput;
  rcti bokehInput;
  const float max_dim = MAX2(this->getWidth(), this->getHeight());

  if (this->m_sizeavailable) {
    newInput.xmax = input->xmax + (this->m_size * max_dim / 100.0f);
    newInput.xmin = input->xmin - (this->m_size * max_dim / 100.0f);
    newInput.ymax = input->ymax + (this->m_size * max_dim / 100.0f);
    newInput.ymin = input->ymin - (this->m_size * max_dim / 100.0f);
  }
  else {
    newInput.xmax = input->xmax + (10.0f * max_dim / 100.0f);
    newInput.xmin = input->xmin - (10.0f * max_dim / 100.0f);
    newInput.ymax = input->ymax + (10.0f * max_dim / 100.0f);
    newInput.ymin = input->ymin - (10.0f * max_dim / 100.0f);
  }

  NodeOperation *operation = getInputOperation(1);
  bokehInput.xmax = operation->getWidth();
  bokehInput.xmin = 0;
  bokehInput.ymax = operation->getHeight();
  bokehInput.ymin = 0;
  if (operation->determineDependingAreaOfInterest(&bokehInput, readOperation, output)) {
    return true;
  }
  operation = getInputOperation(0);
  if (operation->determineDependingAreaOfInterest(&newInput, readOperation, output)) {
    return true;
  }
  operation = getInputOperation(2);
  if (operation->determineDependingAreaOfInterest(input, readOperation, output)) {
    return true;
  }
  if (!this->m_sizeavailable) {
    rcti sizeInput;
    sizeInput.xmin = 0;
    sizeInput.ymin = 0;
    sizeInput.xmax = 5;
    sizeInput.ymax = 5;
    operation = getInputOperation(3);
    if (operation->determineDependingAreaOfInterest(&sizeInput, readOperation, output)) {
      return true;
    }
  }
  return false;
}

void BokehBlurOperation::executeOpenCL(OpenCLDevice *device,
                                       MemoryBuffer *outputMemoryBuffer,
                                       cl_mem clOutputBuffer,
                                       MemoryBuffer **inputMemoryBuffers,
                                       std::list<cl_mem> *clMemToCleanUp,
                                       std::list<cl_kernel> * /*clKernelsToCleanUp*/)
{
  cl_kernel kernel = device->COM_clCreateKernel("bokehBlurKernel", nullptr);
  if (!this->m_sizeavailable) {
    updateSize();
  }
  const float max_dim = MAX2(this->getWidth(), this->getHeight());
  cl_int radius = this->m_size * max_dim / 100.0f;
  cl_int step = this->getStep();

  device->COM_clAttachMemoryBufferToKernelParameter(
      kernel, 0, -1, clMemToCleanUp, inputMemoryBuffers, this->m_inputBoundingBoxReader);
  device->COM_clAttachMemoryBufferToKernelParameter(
      kernel, 1, 4, clMemToCleanUp, inputMemoryBuffers, this->m_inputProgram);
  device->COM_clAttachMemoryBufferToKernelParameter(
      kernel, 2, -1, clMemToCleanUp, inputMemoryBuffers, this->m_inputBokehProgram);
  device->COM_clAttachOutputMemoryBufferToKernelParameter(kernel, 3, clOutputBuffer);
  device->COM_clAttachMemoryBufferOffsetToKernelParameter(kernel, 5, outputMemoryBuffer);
  clSetKernelArg(kernel, 6, sizeof(cl_int), &radius);
  clSetKernelArg(kernel, 7, sizeof(cl_int), &step);
  device->COM_clAttachSizeToKernelParameter(kernel, 8, this);

  device->COM_clEnqueueRange(kernel, outputMemoryBuffer, 9, this);
}

void BokehBlurOperation::updateSize()
{
  if (!this->m_sizeavailable) {
    float result[4];
    this->getInputSocketReader(3)->readSampled(result, 0, 0, PixelSampler::Nearest);
    this->m_size = result[0];
    CLAMP(this->m_size, 0.0f, 10.0f);
    this->m_sizeavailable = true;
  }
}

void BokehBlurOperation::determineResolution(unsigned int resolution[2],
                                             unsigned int preferredResolution[2])
{
  NodeOperation::determineResolution(resolution, preferredResolution);
  if (this->m_extend_bounds) {
    const float max_dim = MAX2(resolution[0], resolution[1]);
    resolution[0] += 2 * this->m_size * max_dim / 100.0f;
    resolution[1] += 2 * this->m_size * max_dim / 100.0f;
  }
}

}  // namespace blender::compositor

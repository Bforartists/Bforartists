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

#include "COM_ScaleOperation.h"
#include "COM_ConstantOperation.h"

namespace blender::compositor {

#define USE_FORCE_BILINEAR
/* XXX(campbell): ignore input and use default from old compositor,
 * could become an option like the transform node.
 *
 * NOTE: use bilinear because bicubic makes fuzzy even when not scaling at all (1:1)
 */

BaseScaleOperation::BaseScaleOperation()
{
#ifdef USE_FORCE_BILINEAR
  m_sampler = (int)PixelSampler::Bilinear;
#else
  m_sampler = -1;
#endif
  m_variable_size = false;
}

void BaseScaleOperation::set_scale_canvas_max_size(Size2f size)
{
  max_scale_canvas_size_ = size;
}

ScaleOperation::ScaleOperation() : ScaleOperation(DataType::Color)
{
}

ScaleOperation::ScaleOperation(DataType data_type) : BaseScaleOperation()
{
  this->addInputSocket(data_type, ResizeMode::None);
  this->addInputSocket(DataType::Value);
  this->addInputSocket(DataType::Value);
  this->addOutputSocket(data_type);
  this->m_inputOperation = nullptr;
  this->m_inputXOperation = nullptr;
  this->m_inputYOperation = nullptr;
}

float ScaleOperation::get_constant_scale(const int input_op_idx, const float factor)
{
  const bool is_constant = getInputOperation(input_op_idx)->get_flags().is_constant_operation;
  if (is_constant) {
    return ((ConstantOperation *)getInputOperation(input_op_idx))->get_constant_elem()[0] * factor;
  }

  return 1.0f;
}

float ScaleOperation::get_constant_scale_x(const float width)
{
  return get_constant_scale(X_INPUT_INDEX, get_relative_scale_x_factor(width));
}

float ScaleOperation::get_constant_scale_y(const float height)
{
  return get_constant_scale(Y_INPUT_INDEX, get_relative_scale_y_factor(height));
}

bool ScaleOperation::is_scaling_variable()
{
  return !get_input_operation(X_INPUT_INDEX)->get_flags().is_constant_operation ||
         !get_input_operation(Y_INPUT_INDEX)->get_flags().is_constant_operation;
}

void ScaleOperation::scale_area(rcti &area, float relative_scale_x, float relative_scale_y)
{
  const rcti src_area = area;
  const float center_x = BLI_rcti_size_x(&area) / 2.0f;
  const float center_y = BLI_rcti_size_y(&area) / 2.0f;
  area.xmin = floorf(scale_coord(area.xmin, center_x, relative_scale_x));
  area.xmax = ceilf(scale_coord(area.xmax, center_x, relative_scale_x));
  area.ymin = floorf(scale_coord(area.ymin, center_y, relative_scale_y));
  area.ymax = ceilf(scale_coord(area.ymax, center_y, relative_scale_y));

  float scale_offset_x, scale_offset_y;
  ScaleOperation::get_scale_offset(src_area, area, scale_offset_x, scale_offset_y);
  BLI_rcti_translate(&area, -scale_offset_x, -scale_offset_y);
}

void ScaleOperation::clamp_area_size_max(rcti &area, Size2f max_size)
{

  if (BLI_rcti_size_x(&area) > max_size.x) {
    area.xmax = area.xmin + max_size.x;
  }
  if (BLI_rcti_size_y(&area) > max_size.y) {
    area.ymax = area.ymin + max_size.y;
  }
}

void ScaleOperation::init_data()
{
  canvas_center_x_ = canvas_.xmin + getWidth() / 2.0f;
  canvas_center_y_ = canvas_.ymin + getHeight() / 2.0f;
}

void ScaleOperation::initExecution()
{
  this->m_inputOperation = this->getInputSocketReader(0);
  this->m_inputXOperation = this->getInputSocketReader(1);
  this->m_inputYOperation = this->getInputSocketReader(2);
}

void ScaleOperation::deinitExecution()
{
  this->m_inputOperation = nullptr;
  this->m_inputXOperation = nullptr;
  this->m_inputYOperation = nullptr;
}

void ScaleOperation::get_scale_offset(const rcti &input_canvas,
                                      const rcti &scale_canvas,
                                      float &r_scale_offset_x,
                                      float &r_scale_offset_y)
{
  r_scale_offset_x = (BLI_rcti_size_x(&input_canvas) - BLI_rcti_size_x(&scale_canvas)) / 2.0f;
  r_scale_offset_y = (BLI_rcti_size_y(&input_canvas) - BLI_rcti_size_y(&scale_canvas)) / 2.0f;
}

void ScaleOperation::get_scale_area_of_interest(const rcti &input_canvas,
                                                const rcti &scale_canvas,
                                                const float relative_scale_x,
                                                const float relative_scale_y,
                                                const rcti &output_area,
                                                rcti &r_input_area)
{
  const float scale_center_x = BLI_rcti_size_x(&input_canvas) / 2.0f;
  const float scale_center_y = BLI_rcti_size_y(&input_canvas) / 2.0f;
  float scale_offset_x, scale_offset_y;
  ScaleOperation::get_scale_offset(input_canvas, scale_canvas, scale_offset_x, scale_offset_y);

  r_input_area.xmin = floorf(
      scale_coord_inverted(output_area.xmin + scale_offset_x, scale_center_x, relative_scale_x));
  r_input_area.xmax = ceilf(
      scale_coord_inverted(output_area.xmax + scale_offset_x, scale_center_x, relative_scale_x));
  r_input_area.ymin = floorf(
      scale_coord_inverted(output_area.ymin + scale_offset_y, scale_center_y, relative_scale_y));
  r_input_area.ymax = ceilf(
      scale_coord_inverted(output_area.ymax + scale_offset_y, scale_center_y, relative_scale_y));
}

void ScaleOperation::get_area_of_interest(const int input_idx,
                                          const rcti &output_area,
                                          rcti &r_input_area)
{
  r_input_area = output_area;
  if (input_idx != 0 || is_scaling_variable()) {
    return;
  }

  NodeOperation *image_op = get_input_operation(IMAGE_INPUT_INDEX);
  const float scale_x = get_constant_scale_x(image_op->getWidth());
  const float scale_y = get_constant_scale_y(image_op->getHeight());

  get_scale_area_of_interest(
      image_op->get_canvas(), this->get_canvas(), scale_x, scale_y, output_area, r_input_area);
  expand_area_for_sampler(r_input_area, (PixelSampler)m_sampler);
}

void ScaleOperation::update_memory_buffer_partial(MemoryBuffer *output,
                                                  const rcti &area,
                                                  Span<MemoryBuffer *> inputs)
{
  NodeOperation *input_image_op = get_input_operation(IMAGE_INPUT_INDEX);
  const int input_image_width = input_image_op->getWidth();
  const int input_image_height = input_image_op->getHeight();
  const float scale_x_factor = get_relative_scale_x_factor(input_image_width);
  const float scale_y_factor = get_relative_scale_y_factor(input_image_height);
  const float scale_center_x = input_image_width / 2.0f;
  const float scale_center_y = input_image_height / 2.0f;
  float from_scale_offset_x, from_scale_offset_y;
  ScaleOperation::get_scale_offset(
      input_image_op->get_canvas(), this->get_canvas(), from_scale_offset_x, from_scale_offset_y);

  const MemoryBuffer *input_image = inputs[IMAGE_INPUT_INDEX];
  MemoryBuffer *input_x = inputs[X_INPUT_INDEX];
  MemoryBuffer *input_y = inputs[Y_INPUT_INDEX];
  BuffersIterator<float> it = output->iterate_with({input_x, input_y}, area);
  for (; !it.is_end(); ++it) {
    const float rel_scale_x = *it.in(0) * scale_x_factor;
    const float rel_scale_y = *it.in(1) * scale_y_factor;
    const float scaled_x = scale_coord_inverted(
        from_scale_offset_x + canvas_.xmin + it.x, scale_center_x, rel_scale_x);
    const float scaled_y = scale_coord_inverted(
        from_scale_offset_y + canvas_.ymin + it.y, scale_center_y, rel_scale_y);

    input_image->read_elem_sampled(
        scaled_x - canvas_.xmin, scaled_y - canvas_.ymin, (PixelSampler)m_sampler, it.out);
  }
}

void ScaleOperation::determine_canvas(const rcti &preferred_area, rcti &r_area)
{
  if (execution_model_ == eExecutionModel::Tiled) {
    NodeOperation::determine_canvas(preferred_area, r_area);
    return;
  }

  const bool image_determined =
      getInputSocket(IMAGE_INPUT_INDEX)->determine_canvas(preferred_area, r_area);
  if (image_determined) {
    rcti image_canvas = r_area;
    rcti unused;
    NodeOperationInput *x_socket = getInputSocket(X_INPUT_INDEX);
    NodeOperationInput *y_socket = getInputSocket(Y_INPUT_INDEX);
    x_socket->determine_canvas(image_canvas, unused);
    y_socket->determine_canvas(image_canvas, unused);
    if (is_scaling_variable()) {
      /* Do not scale canvas. */
      return;
    }

    /* Determine scaled canvas. */
    const float input_width = BLI_rcti_size_x(&r_area);
    const float input_height = BLI_rcti_size_y(&r_area);
    const float scale_x = get_constant_scale_x(input_width);
    const float scale_y = get_constant_scale_y(input_height);
    scale_area(r_area, scale_x, scale_y);
    const Size2f max_scale_size = {MAX2(input_width, max_scale_canvas_size_.x),
                                   MAX2(input_height, max_scale_canvas_size_.y)};
    clamp_area_size_max(r_area, max_scale_size);

    /* Re-determine canvases of x and y constant inputs with scaled canvas as preferred. */
    get_input_operation(X_INPUT_INDEX)->unset_canvas();
    get_input_operation(Y_INPUT_INDEX)->unset_canvas();
    x_socket->determine_canvas(r_area, unused);
    y_socket->determine_canvas(r_area, unused);
  }
}

ScaleRelativeOperation::ScaleRelativeOperation() : ScaleOperation()
{
}

ScaleRelativeOperation::ScaleRelativeOperation(DataType data_type) : ScaleOperation(data_type)
{
}

void ScaleRelativeOperation::executePixelSampled(float output[4],
                                                 float x,
                                                 float y,
                                                 PixelSampler sampler)
{
  PixelSampler effective_sampler = getEffectiveSampler(sampler);

  float scaleX[4];
  float scaleY[4];

  this->m_inputXOperation->readSampled(scaleX, x, y, effective_sampler);
  this->m_inputYOperation->readSampled(scaleY, x, y, effective_sampler);

  const float scx = scaleX[0];
  const float scy = scaleY[0];

  float nx = this->canvas_center_x_ + (x - this->canvas_center_x_) / scx;
  float ny = this->canvas_center_y_ + (y - this->canvas_center_y_) / scy;
  this->m_inputOperation->readSampled(output, nx, ny, effective_sampler);
}

bool ScaleRelativeOperation::determineDependingAreaOfInterest(rcti *input,
                                                              ReadBufferOperation *readOperation,
                                                              rcti *output)
{
  rcti newInput;
  if (!m_variable_size) {
    float scaleX[4];
    float scaleY[4];

    this->m_inputXOperation->readSampled(scaleX, 0, 0, PixelSampler::Nearest);
    this->m_inputYOperation->readSampled(scaleY, 0, 0, PixelSampler::Nearest);

    const float scx = scaleX[0];
    const float scy = scaleY[0];

    newInput.xmax = this->canvas_center_x_ + (input->xmax - this->canvas_center_x_) / scx + 1;
    newInput.xmin = this->canvas_center_x_ + (input->xmin - this->canvas_center_x_) / scx - 1;
    newInput.ymax = this->canvas_center_y_ + (input->ymax - this->canvas_center_y_) / scy + 1;
    newInput.ymin = this->canvas_center_y_ + (input->ymin - this->canvas_center_y_) / scy - 1;
  }
  else {
    newInput.xmax = this->getWidth();
    newInput.xmin = 0;
    newInput.ymax = this->getHeight();
    newInput.ymin = 0;
  }
  return BaseScaleOperation::determineDependingAreaOfInterest(&newInput, readOperation, output);
}

void ScaleAbsoluteOperation::executePixelSampled(float output[4],
                                                 float x,
                                                 float y,
                                                 PixelSampler sampler)
{
  PixelSampler effective_sampler = getEffectiveSampler(sampler);

  float scaleX[4];
  float scaleY[4];

  this->m_inputXOperation->readSampled(scaleX, x, y, effective_sampler);
  this->m_inputYOperation->readSampled(scaleY, x, y, effective_sampler);

  const float scx = scaleX[0]; /* Target absolute scale. */
  const float scy = scaleY[0]; /* Target absolute scale. */

  const float width = this->getWidth();
  const float height = this->getHeight();
  /* Divide. */
  float relativeXScale = scx / width;
  float relativeYScale = scy / height;

  float nx = this->canvas_center_x_ + (x - this->canvas_center_x_) / relativeXScale;
  float ny = this->canvas_center_y_ + (y - this->canvas_center_y_) / relativeYScale;

  this->m_inputOperation->readSampled(output, nx, ny, effective_sampler);
}

bool ScaleAbsoluteOperation::determineDependingAreaOfInterest(rcti *input,
                                                              ReadBufferOperation *readOperation,
                                                              rcti *output)
{
  rcti newInput;
  if (!m_variable_size) {
    float scaleX[4];
    float scaleY[4];

    this->m_inputXOperation->readSampled(scaleX, 0, 0, PixelSampler::Nearest);
    this->m_inputYOperation->readSampled(scaleY, 0, 0, PixelSampler::Nearest);

    const float scx = scaleX[0];
    const float scy = scaleY[0];
    const float width = this->getWidth();
    const float height = this->getHeight();
    /* Divide. */
    float relateveXScale = scx / width;
    float relateveYScale = scy / height;

    newInput.xmax = this->canvas_center_x_ +
                    (input->xmax - this->canvas_center_x_) / relateveXScale;
    newInput.xmin = this->canvas_center_x_ +
                    (input->xmin - this->canvas_center_x_) / relateveXScale;
    newInput.ymax = this->canvas_center_y_ +
                    (input->ymax - this->canvas_center_y_) / relateveYScale;
    newInput.ymin = this->canvas_center_y_ +
                    (input->ymin - this->canvas_center_y_) / relateveYScale;
  }
  else {
    newInput.xmax = this->getWidth();
    newInput.xmin = 0;
    newInput.ymax = this->getHeight();
    newInput.ymin = 0;
  }
  return ScaleOperation::determineDependingAreaOfInterest(&newInput, readOperation, output);
}

/* Absolute fixed size. */
ScaleFixedSizeOperation::ScaleFixedSizeOperation() : BaseScaleOperation()
{
  this->addInputSocket(DataType::Color, ResizeMode::None);
  this->addOutputSocket(DataType::Color);
  this->set_canvas_input_index(0);
  this->m_inputOperation = nullptr;
  this->m_is_offset = false;
}

void ScaleFixedSizeOperation::init_data(const rcti &input_canvas)
{
  const int input_width = BLI_rcti_size_x(&input_canvas);
  const int input_height = BLI_rcti_size_y(&input_canvas);
  this->m_relX = input_width / (float)this->m_newWidth;
  this->m_relY = input_height / (float)this->m_newHeight;

  /* *** all the options below are for a fairly special case - camera framing *** */
  if (this->m_offsetX != 0.0f || this->m_offsetY != 0.0f) {
    this->m_is_offset = true;

    if (this->m_newWidth > this->m_newHeight) {
      this->m_offsetX *= this->m_newWidth;
      this->m_offsetY *= this->m_newWidth;
    }
    else {
      this->m_offsetX *= this->m_newHeight;
      this->m_offsetY *= this->m_newHeight;
    }
  }

  if (this->m_is_aspect) {
    /* apply aspect from clip */
    const float w_src = input_width;
    const float h_src = input_height;

    /* destination aspect is already applied from the camera frame */
    const float w_dst = this->m_newWidth;
    const float h_dst = this->m_newHeight;

    const float asp_src = w_src / h_src;
    const float asp_dst = w_dst / h_dst;

    if (fabsf(asp_src - asp_dst) >= FLT_EPSILON) {
      if ((asp_src > asp_dst) == (this->m_is_crop == true)) {
        /* fit X */
        const float div = asp_src / asp_dst;
        this->m_relX /= div;
        this->m_offsetX += ((w_src - (w_src * div)) / (w_src / w_dst)) / 2.0f;
        if (m_is_crop && execution_model_ == eExecutionModel::FullFrame) {
          int fit_width = m_newWidth * div;
          if (fit_width > max_scale_canvas_size_.x) {
            fit_width = max_scale_canvas_size_.x;
          }

          const int added_width = fit_width - m_newWidth;
          m_newWidth += added_width;
          m_offsetX += added_width / 2.0f;
        }
      }
      else {
        /* fit Y */
        const float div = asp_dst / asp_src;
        this->m_relY /= div;
        this->m_offsetY += ((h_src - (h_src * div)) / (h_src / h_dst)) / 2.0f;
        if (m_is_crop && execution_model_ == eExecutionModel::FullFrame) {
          int fit_height = m_newHeight * div;
          if (fit_height > max_scale_canvas_size_.y) {
            fit_height = max_scale_canvas_size_.y;
          }

          const int added_height = fit_height - m_newHeight;
          m_newHeight += added_height;
          m_offsetY += added_height / 2.0f;
        }
      }

      this->m_is_offset = true;
    }
  }
  /* *** end framing options *** */
}

void ScaleFixedSizeOperation::initExecution()
{
  this->m_inputOperation = this->getInputSocketReader(0);
}

void ScaleFixedSizeOperation::deinitExecution()
{
  this->m_inputOperation = nullptr;
}

void ScaleFixedSizeOperation::executePixelSampled(float output[4],
                                                  float x,
                                                  float y,
                                                  PixelSampler sampler)
{
  PixelSampler effective_sampler = getEffectiveSampler(sampler);

  if (this->m_is_offset) {
    float nx = ((x - this->m_offsetX) * this->m_relX);
    float ny = ((y - this->m_offsetY) * this->m_relY);
    this->m_inputOperation->readSampled(output, nx, ny, effective_sampler);
  }
  else {
    this->m_inputOperation->readSampled(
        output, x * this->m_relX, y * this->m_relY, effective_sampler);
  }
}

bool ScaleFixedSizeOperation::determineDependingAreaOfInterest(rcti *input,
                                                               ReadBufferOperation *readOperation,
                                                               rcti *output)
{
  rcti newInput;

  newInput.xmax = (input->xmax - m_offsetX) * this->m_relX + 1;
  newInput.xmin = (input->xmin - m_offsetX) * this->m_relX;
  newInput.ymax = (input->ymax - m_offsetY) * this->m_relY + 1;
  newInput.ymin = (input->ymin - m_offsetY) * this->m_relY;

  return BaseScaleOperation::determineDependingAreaOfInterest(&newInput, readOperation, output);
}

void ScaleFixedSizeOperation::determine_canvas(const rcti &preferred_area, rcti &r_area)
{
  rcti local_preferred = preferred_area;
  local_preferred.xmax = local_preferred.xmin + m_newWidth;
  local_preferred.ymax = local_preferred.ymin + m_newHeight;
  rcti input_canvas;
  const bool input_determined = getInputSocket(0)->determine_canvas(local_preferred, input_canvas);
  if (input_determined) {
    init_data(input_canvas);
    r_area = input_canvas;
    if (execution_model_ == eExecutionModel::FullFrame) {
      r_area.xmin /= m_relX;
      r_area.ymin /= m_relY;
      r_area.xmin += m_offsetX;
      r_area.ymin += m_offsetY;
    }

    r_area.xmax = r_area.xmin + m_newWidth;
    r_area.ymax = r_area.ymin + m_newHeight;
  }
}

void ScaleFixedSizeOperation::get_area_of_interest(const int input_idx,
                                                   const rcti &output_area,
                                                   rcti &r_input_area)
{
  BLI_assert(input_idx == 0);
  UNUSED_VARS_NDEBUG(input_idx);

  r_input_area.xmax = ceilf((output_area.xmax - m_offsetX) * this->m_relX);
  r_input_area.xmin = floorf((output_area.xmin - m_offsetX) * this->m_relX);
  r_input_area.ymax = ceilf((output_area.ymax - m_offsetY) * this->m_relY);
  r_input_area.ymin = floorf((output_area.ymin - m_offsetY) * this->m_relY);
  expand_area_for_sampler(r_input_area, (PixelSampler)m_sampler);
}

void ScaleFixedSizeOperation::update_memory_buffer_partial(MemoryBuffer *output,
                                                           const rcti &area,
                                                           Span<MemoryBuffer *> inputs)
{
  const MemoryBuffer *input_img = inputs[0];
  PixelSampler sampler = (PixelSampler)m_sampler;
  BuffersIterator<float> it = output->iterate_with({}, area);
  if (this->m_is_offset) {
    for (; !it.is_end(); ++it) {
      const float nx = (canvas_.xmin + it.x - this->m_offsetX) * this->m_relX;
      const float ny = (canvas_.ymin + it.y - this->m_offsetY) * this->m_relY;
      input_img->read_elem_sampled(nx - canvas_.xmin, ny - canvas_.ymin, sampler, it.out);
    }
  }
  else {
    for (; !it.is_end(); ++it) {
      input_img->read_elem_sampled((canvas_.xmin + it.x) * this->m_relX - canvas_.xmin,
                                   (canvas_.ymin + it.y) * this->m_relY - canvas_.ymin,
                                   sampler,
                                   it.out);
    }
  }
}

}  // namespace blender::compositor

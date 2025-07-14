/* SPDX-FileCopyrightText: 2011-2022 Blender Foundation
 *
 * SPDX-License-Identifier: Apache-2.0 */

#pragma once

#include "util/image.h"
#include "util/math_base.h"

CCL_NAMESPACE_BEGIN

namespace {

template<typename T>
const T *util_image_read(const vector<T> &pixels,
                         const size_t width,
                         const size_t /*height*/,
                         const size_t components,
                         const size_t x,
                         const size_t y)
{
  const size_t index = ((size_t)y * width + (size_t)x) * components;
  return &pixels[index];
}

template<typename T>
void util_image_downscale_sample(const vector<T> &pixels,
                                 const size_t width,
                                 const size_t height,
                                 const size_t components,
                                 const size_t kernel_size,
                                 const float x,
                                 const float y,
                                 T *result)
{
  assert(components <= 4);
  const size_t ix = (size_t)x;
  const size_t iy = (size_t)y;
  /* TODO(sergey): Support something smarter than box filer. */
  float accum[4] = {0};
  size_t count = 0;
  for (size_t dy = 0; dy < kernel_size; ++dy) {
    for (size_t dx = 0; dx < kernel_size; ++dx) {
      const size_t nx = ix + dx;
      const size_t ny = iy + dy;
      if (nx >= width || ny >= height) {
        continue;
      }
      const T *pixel = util_image_read(pixels, width, height, components, nx, ny);
      for (size_t k = 0; k < components; ++k) {
        accum[k] += util_image_cast_to_float(pixel[k]);
      }
      ++count;
    }
  }
  if (count != 0) {
    const float inv_count = 1.0f / (float)count;
    for (size_t k = 0; k < components; ++k) {
      result[k] = util_image_cast_from_float<T>(accum[k] * inv_count);
    }
  }
  else {
    for (size_t k = 0; k < components; ++k) {
      result[k] = T(0.0f);
    }
  }
}

template<typename T>
void util_image_downscale_pixels(const vector<T> &input_pixels,
                                 const size_t input_width,
                                 const size_t input_height,
                                 const size_t components,
                                 const float inv_scale_factor,
                                 const size_t output_width,
                                 const size_t output_height,
                                 vector<T> *output_pixels)
{
  const size_t kernel_size = (size_t)(inv_scale_factor + 0.5f);
  for (size_t y = 0; y < output_height; ++y) {
    for (size_t x = 0; x < output_width; ++x) {
      const float input_x = (float)x * inv_scale_factor;
      const float input_y = (float)y * inv_scale_factor;
      const size_t output_index = (y * output_width + x) * components;
      util_image_downscale_sample(input_pixels,
                                  input_width,
                                  input_height,
                                  components,
                                  kernel_size,
                                  input_x,
                                  input_y,
                                  &output_pixels->at(output_index));
    }
  }
}

} /* namespace */

template<typename T>
void util_image_resize_pixels(const vector<T> &input_pixels,
                              const size_t input_width,
                              const size_t input_height,
                              const size_t components,
                              const float scale_factor,
                              vector<T> *output_pixels,
                              size_t *output_width,
                              size_t *output_height)
{
  /* Early output for case when no scaling is applied. */
  if (scale_factor == 1.0f) {
    *output_width = input_width;
    *output_height = input_height;
    *output_pixels = input_pixels;
    return;
  }
  /* First of all, we calculate output image dimensions.
   * We clamp them to be 1 pixel at least so we do not generate degenerate
   * image.
   */
  *output_width = max((size_t)((float)input_width * scale_factor), (size_t)1);
  *output_height = max((size_t)((float)input_height * scale_factor), (size_t)1);
  /* Prepare pixel storage for the result. */
  const size_t num_output_pixels = ((*output_width) * (*output_height)) * components;
  output_pixels->resize(num_output_pixels);
  if (scale_factor < 1.0f) {
    const float inv_scale_factor = 1.0f / scale_factor;
    util_image_downscale_pixels(input_pixels,
                                input_width,
                                input_height,
                                components,
                                inv_scale_factor,
                                *output_width,
                                *output_height,
                                output_pixels);
  }
  else {
    /* TODO(sergey): Needs implementation. */
  }
}

CCL_NAMESPACE_END

/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#include "BLI_assert.h"
#include "BLI_math_base.hh"
#include "BLI_math_vector.hh"
#include "BLI_math_vector_types.hh"

#include "GPU_shader.hh"
#include "GPU_texture.hh"

#include "COM_context.hh"
#include "COM_result.hh"
#include "COM_utilities.hh"

#include "COM_algorithm_symmetric_separable_blur.hh"

#include "COM_symmetric_separable_blur_weights.hh"

namespace blender::compositor {

template<typename T>
static void blur_pass(const Result &input,
                      const Result &weights,
                      Result &output,
                      const bool extend_bounds)
{
  /* Loads the input color of the pixel at the given texel. If bounds are extended, then the input
   * is treated as padded by a blur size amount of pixels of zero color, and the given texel is
   * assumed to be in the space of the image after padding. So we offset the texel by the blur
   * radius amount and fallback to a zero color if it is out of bounds. For instance, if the input
   * is padded by 5 pixels to the left of the image, the first 5 pixels should be out of bounds and
   * thus zero, hence the introduced offset. */
  auto load_input = [&](const int2 texel) {
    T color;
    if (extend_bounds) {
      /* Notice that we subtract 1 because the weights result have an extra center weight, see the
       * SymmetricBlurWeights class for more information. */
      int2 blur_radius = weights.domain().size - 1;
      color = input.load_pixel_zero<T>(texel - blur_radius);
    }
    else {
      color = input.load_pixel_extended<T>(texel);
    }

    return color;
  };

  /* Notice that the size is transposed, see the note on the horizontal pass method for more
   * information on the reasoning behind this. */
  const int2 size = int2(output.domain().size.y, output.domain().size.x);
  parallel_for(size, [&](const int2 texel) {
    T accumulated_color = T(0);

    /* First, compute the contribution of the center pixel. */
    T center_color = load_input(texel);
    accumulated_color += center_color * weights.load_pixel<float>(int2(0));

    /* Then, compute the contributions of the pixel to the right and left, noting that the
     * weights texture only stores the weights for the positive half, but since the filter is
     * symmetric, the same weight is used for the negative half and we add both of their
     * contributions. */
    for (int i = 1; i < weights.domain().size.x; i++) {
      float weight = weights.load_pixel<float>(int2(i, 0));
      accumulated_color += load_input(texel + int2(i, 0)) * weight;
      accumulated_color += load_input(texel + int2(-i, 0)) * weight;
    }

    /* Write the color using the transposed texel. See the horizontal_pass method for more
     * information on the rational behind this. */
    output.store_pixel(int2(texel.y, texel.x), accumulated_color);
  });
}

static const char *get_blur_shader(const ResultType type)
{
  switch (type) {
    case ResultType::Float:
      return "compositor_symmetric_separable_blur_float";
    case ResultType::Vector:
    case ResultType::Color:
      return "compositor_symmetric_separable_blur_float4";
    case ResultType::Float2:
    case ResultType::Float3:
    case ResultType::Int2:
      /* Not supported. */
      break;
  }

  BLI_assert_unreachable();
  return nullptr;
}

static Result horizontal_pass_gpu(Context &context,
                                  const Result &input,
                                  const float radius,
                                  const int filter_type,
                                  const bool extend_bounds)
{
  GPUShader *shader = context.get_shader(get_blur_shader(input.type()));
  GPU_shader_bind(shader);

  GPU_shader_uniform_1b(shader, "extend_bounds", extend_bounds);

  input.bind_as_texture(shader, "input_tx");

  const Result &weights = context.cache_manager().symmetric_separable_blur_weights.get(
      context, filter_type, radius);
  weights.bind_as_texture(shader, "weights_tx");

  Domain domain = input.domain();
  if (extend_bounds) {
    domain.size.x += int(math::ceil(radius)) * 2;
  }

  /* We allocate an output image of a transposed size, that is, with a height equivalent to the
   * width of the input and vice versa. This is done as a performance optimization. The shader
   * will blur the image horizontally and write it to the intermediate output transposed. Then
   * the vertical pass will execute the same horizontal blur shader, but since its input is
   * transposed, it will effectively do a vertical blur and write to the output transposed,
   * effectively undoing the transposition in the horizontal pass. This is done to improve
   * spatial cache locality in the shader and to avoid having two separate shaders for each blur
   * pass. */
  const int2 transposed_domain = int2(domain.size.y, domain.size.x);

  Result output = context.create_result(input.type());
  output.allocate_texture(transposed_domain);
  output.bind_as_image(shader, "output_img");

  compute_dispatch_threads_at_least(shader, domain.size);

  GPU_shader_unbind();
  input.unbind_as_texture();
  weights.unbind_as_texture();
  output.unbind_as_image();

  return output;
}

static Result horizontal_pass_cpu(Context &context,
                                  const Result &input,
                                  const float radius,
                                  const int filter_type,
                                  const bool extend_bounds)
{
  const Result &weights = context.cache_manager().symmetric_separable_blur_weights.get(
      context, filter_type, radius);

  Domain domain = input.domain();
  if (extend_bounds) {
    domain.size.x += int(math::ceil(radius)) * 2;
  }

  /* We allocate an output image of a transposed size, that is, with a height equivalent to the
   * width of the input and vice versa. This is done as a performance optimization. The shader
   * will blur the image horizontally and write it to the intermediate output transposed. Then
   * the vertical pass will execute the same horizontal blur shader, but since its input is
   * transposed, it will effectively do a vertical blur and write to the output transposed,
   * effectively undoing the transposition in the horizontal pass. This is done to improve
   * spatial cache locality in the shader and to avoid having two separate shaders for each blur
   * pass. */
  const int2 transposed_domain = int2(domain.size.y, domain.size.x);

  Result output = context.create_result(input.type());
  output.allocate_texture(transposed_domain);

  switch (input.type()) {
    case ResultType::Float:
      blur_pass<float>(input, weights, output, extend_bounds);
      break;
    case ResultType::Vector:
    case ResultType::Color:
      blur_pass<float4>(input, weights, output, extend_bounds);
      break;
    case ResultType::Float2:
    case ResultType::Float3:
    case ResultType::Int2:
      /* Not supported. */
      BLI_assert_unreachable();
      break;
  }

  return output;
}

static Result horizontal_pass(Context &context,
                              const Result &input,
                              const float radius,
                              const int filter_type,
                              const bool extend_bounds)
{
  if (context.use_gpu()) {
    return horizontal_pass_gpu(context, input, radius, filter_type, extend_bounds);
  }
  return horizontal_pass_cpu(context, input, radius, filter_type, extend_bounds);
}

static void vertical_pass_gpu(Context &context,
                              const Result &original_input,
                              const Result &horizontal_pass_result,
                              Result &output,
                              const float2 &radius,
                              const int filter_type,
                              const bool extend_bounds)
{
  GPUShader *shader = context.get_shader(get_blur_shader(original_input.type()));
  GPU_shader_bind(shader);

  GPU_shader_uniform_1b(shader, "extend_bounds", extend_bounds);

  horizontal_pass_result.bind_as_texture(shader, "input_tx");

  const Result &weights = context.cache_manager().symmetric_separable_blur_weights.get(
      context, filter_type, radius.y);
  weights.bind_as_texture(shader, "weights_tx");

  Domain domain = original_input.domain();
  if (extend_bounds) {
    /* Add a radius amount of pixels in both sides of the image, hence the multiply by 2. */
    domain.size += int2(math::ceil(radius)) * 2;
  }

  output.allocate_texture(domain);
  output.bind_as_image(shader, "output_img");

  /* Notice that the domain is transposed, see the note on the horizontal pass method for more
   * information on the reasoning behind this. */
  compute_dispatch_threads_at_least(shader, int2(domain.size.y, domain.size.x));

  GPU_shader_unbind();
  horizontal_pass_result.unbind_as_texture();
  output.unbind_as_image();
  weights.unbind_as_texture();
}

static void vertical_pass_cpu(Context &context,
                              const Result &original_input,
                              const Result &horizontal_pass_result,
                              Result &output,
                              const float2 &radius,
                              const int filter_type,
                              const bool extend_bounds)
{
  const Result &weights = context.cache_manager().symmetric_separable_blur_weights.get(
      context, filter_type, radius.y);

  Domain domain = original_input.domain();
  if (extend_bounds) {
    /* Add a radius amount of pixels in both sides of the image, hence the multiply by 2. */
    domain.size += int2(math::ceil(radius)) * 2;
  }
  output.allocate_texture(domain);

  switch (original_input.type()) {
    case ResultType::Float:
      blur_pass<float>(horizontal_pass_result, weights, output, extend_bounds);
      break;
    case ResultType::Vector:
    case ResultType::Color:
      blur_pass<float4>(horizontal_pass_result, weights, output, extend_bounds);
      break;
    case ResultType::Float2:
    case ResultType::Float3:
    case ResultType::Int2:
      /* Not supported. */
      BLI_assert_unreachable();
      break;
  }
}

static void vertical_pass(Context &context,
                          const Result &original_input,
                          const Result &horizontal_pass_result,
                          Result &output,
                          const float2 &radius,
                          const int filter_type,
                          const bool extend_bounds)
{
  if (context.use_gpu()) {
    vertical_pass_gpu(context,
                      original_input,
                      horizontal_pass_result,
                      output,
                      radius,
                      filter_type,
                      extend_bounds);
  }
  else {
    vertical_pass_cpu(context,
                      original_input,
                      horizontal_pass_result,
                      output,
                      radius,
                      filter_type,
                      extend_bounds);
  }
}

void symmetric_separable_blur(Context &context,
                              const Result &input,
                              Result &output,
                              const float2 &radius,
                              const int filter_type,
                              const bool extend_bounds)
{
  Result horizontal_pass_result = horizontal_pass(
      context, input, radius.x, filter_type, extend_bounds);

  vertical_pass(
      context, input, horizontal_pass_result, output, radius, filter_type, extend_bounds);

  horizontal_pass_result.release();
}

}  // namespace blender::compositor

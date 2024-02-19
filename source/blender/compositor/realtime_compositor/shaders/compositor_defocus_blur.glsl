/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#pragma BLENDER_REQUIRE(gpu_shader_common_math_utils.glsl)
#pragma BLENDER_REQUIRE(gpu_shader_compositor_blur_common.glsl)
#pragma BLENDER_REQUIRE(gpu_shader_compositor_texture_utilities.glsl)

/* Given the texel in the range [-radius, radius] in both axis, load the appropriate weight from
 * the weights texture, where the given texel (0, 0) corresponds the center of weights texture.
 * Note that we load the weights texture inverted along both directions to maintain the shape of
 * the weights if it was not symmetrical. To understand why inversion makes sense, consider a 1D
 * weights texture whose right half is all ones and whose left half is all zeros. Further, consider
 * that we are blurring a single white pixel on a black background. When computing the value of a
 * pixel that is to the right of the white pixel, the white pixel will be in the left region of the
 * search window, and consequently, without inversion, a zero will be sampled from the left side of
 * the weights texture and result will be zero. However, what we expect is that pixels to the right
 * of the white pixel will be white, that is, they should sample a weight of 1 from the right side
 * of the weights texture, hence the need for inversion. */
vec4 load_weight(ivec2 texel, float radius)
{
  /* Add the radius to transform the texel into the range [0, radius * 2], with an additional 0.5
   * to sample at the center of the pixels, then divide by the upper bound plus one to transform
   * the texel into the normalized range [0, 1] needed to sample the weights sampler. Finally,
   * invert the textures coordinates by subtracting from 1 to maintain the shape of the weights as
   * mentioned in the function description. */
  return texture(weights_tx, 1.0 - ((vec2(texel) + vec2(radius + 0.5)) / (radius * 2.0 + 1.0)));
}

void main()
{
  ivec2 texel = ivec2(gl_GlobalInvocationID.xy);

  float center_radius = max(0.0, texture_load(radius_tx, texel).x);
  vec4 center_color = texture_load(input_tx, texel);

  /* Go over the window of the given search radius and accumulate the colors multiplied by their
   * respective weights as well as the weights themselves, but only if both the radius of the
   * center pixel and the radius of the candidate pixel are less than both the x and y distances of
   * the candidate pixel. */
  vec4 accumulated_color = vec4(0.0);
  vec4 accumulated_weight = vec4(0.0);
  for (int y = -search_radius; y <= search_radius; y++) {
    for (int x = -search_radius; x <= search_radius; x++) {
      float candidate_radius = max(0.0, texture_load(radius_tx, texel + ivec2(x, y)).x);

      /* Skip accumulation if either the x or y distances of the candidate pixel are larger than
       * either the center or candidate pixel radius. Note that the max and min functions here
       * denote "either" in the aforementioned description. */
      float radius = min(center_radius, candidate_radius);
      if (max(abs(x), abs(y)) > radius) {
        continue;
      }

      vec4 weight = load_weight(ivec2(x, y), radius);
      vec4 input_color = texture_load(input_tx, texel + ivec2(x, y));

      if (gamma_correct) {
        input_color = gamma_correct_blur_input(input_color);
      }

      accumulated_color += input_color * weight;
      accumulated_weight += weight;
    }
  }

  accumulated_color = safe_divide(accumulated_color, accumulated_weight);

  if (gamma_correct) {
    accumulated_color = gamma_uncorrect_blur_output(accumulated_color);
  }

  imageStore(output_img, texel, accumulated_color);
}

/* SPDX-FileCopyrightText: 2022 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#include "common_math_lib.glsl"
#include "gpu_shader_compositor_texture_utilities.glsl"

void main()
{
  ivec2 texel = ivec2(gl_GlobalInvocationID.xy);
  ivec2 image_size = texture_size(input_tx);

  int radius_squared = radius * radius;

  /* Compute the start and end bounds of the window such that no out-of-bounds processing happen
   * in the loops. */
  ivec2 start = max(texel - radius, int2(0)) - texel;
  ivec2 end = min(texel + radius + 1, image_size) - texel;

  /* Find the minimum/maximum value in the circular window of the given radius around the pixel. By
   * circular window, we mean that pixels in the window whose distance to the center of window is
   * larger than the given radius are skipped and not considered. Consequently, the dilation or
   * erosion that take place produces round results as opposed to squarish ones. This is
   * essentially a morphological operator with a circular structuring element. The LIMIT value
   * should be FLT_MAX if OPERATOR is min and FLT_MIN if OPERATOR is max. */
  float value = LIMIT;
  for (int y = start.y; y < end.y; y++) {
    int yy = y * y;
    for (int x = start.x; x < end.y; x++) {
      if (x * x + yy > radius_squared) {
        continue;
      }
      value = OPERATOR(value, texture_load(input_tx, texel + ivec2(x, y)).x);
    }
  }

  imageStore(output_img, texel, vec4(value));
}

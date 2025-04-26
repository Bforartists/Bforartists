/* SPDX-FileCopyrightText: 2022 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#include "gpu_shader_compositor_texture_utilities.glsl"

void main()
{
  int2 texel = int2(gl_GlobalInvocationID.xy);

  /* Get the normalized coordinates of the pixel centers. */
  float2 normalized_texel = (float2(texel) + float2(0.5f)) / float2(texture_size(input_tx));

  /* Sample the red and blue channels shifted by the dispersion amount. */
  const float red = texture(input_tx, normalized_texel + float2(dispersion, 0.0f)).r;
  const float green = texture_load(input_tx, texel).g;
  const float blue = texture(input_tx, normalized_texel - float2(dispersion, 0.0f)).b;

  imageStore(output_img, texel, float4(red, green, blue, 1.0f));
}

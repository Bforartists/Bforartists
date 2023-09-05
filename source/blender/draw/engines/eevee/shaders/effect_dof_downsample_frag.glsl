/* SPDX-FileCopyrightText: 2021-2022 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/**
 * Downsample pass: CoC aware downsample to quarter resolution.
 *
 * Pretty much identical to the setup pass but get CoC from buffer. Also does not
 * weight luma for the bilateral weights.
 */

#pragma BLENDER_REQUIRE(effect_dof_lib.glsl)

void main()
{
  DEFINE_DOF_QUAD_OFFSETS
  vec2 halfres_texel_size = 1.0 / vec2(textureSize(colorBuffer, 0).xy);
  /* Center uv around the 4 half-resolution pixels. */
  vec2 quad_center = (floor(gl_FragCoord.xy) * 2.0 + 1.0) * halfres_texel_size;

  vec4 colors[4];
  vec4 cocs;
  for (int i = 0; i < 4; i++) {
    vec2 sample_uv = quad_center + quad_offsets[i] * halfres_texel_size;
    colors[i] = textureLod(colorBuffer, sample_uv, 0.0);
    cocs[i] = textureLod(cocBuffer, sample_uv, 0.0).r;
  }

  vec4 weights = dof_downsample_bilateral_coc_weights(cocs);
  /* Normalize so that the sum is 1. */
  weights *= safe_rcp(sum(weights));

  outColor = weighted_sum_array(colors, weights);
}

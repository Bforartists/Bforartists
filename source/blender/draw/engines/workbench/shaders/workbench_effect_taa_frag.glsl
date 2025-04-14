/* SPDX-FileCopyrightText: 2018-2022 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#include "infos/workbench_effect_antialiasing_info.hh"

FRAGMENT_SHADER_CREATE_INFO(workbench_taa)

void main()
{
  float2 texel_size = 1.0f / float2(textureSize(colorBuffer, 0));
  float2 uv = gl_FragCoord.xy * texel_size;

  fragColor = float4(0.0f);
  int i = 0;
  for (int x = -1; x <= 1; x++) {
    for (int y = -1; y <= 1; y++, i++) {
      float4 color = texture(colorBuffer, uv + float2(x, y) * texel_size);
      /* Clamp infinite inputs (See #112211). */
      color = clamp(color, float4(0.0f), float4(1e10f));
      /* Use log2 space to avoid highlights creating too much aliasing. */
      color = log2(color + 0.5f);

      fragColor += color * samplesWeights[i];
    }
  }
}

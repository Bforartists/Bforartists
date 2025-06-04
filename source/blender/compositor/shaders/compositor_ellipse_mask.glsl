/* SPDX-FileCopyrightText: 2022 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#include "gpu_shader_compositor_texture_utilities.glsl"

void main()
{
  int2 texel = int2(gl_GlobalInvocationID.xy);

  float2 uv = float2(texel) / float2(domain_size - int2(1));
  uv -= location;
  uv.y *= float(domain_size.y) / float(domain_size.x);
  uv = float2x2(cos_angle, -sin_angle, sin_angle, cos_angle) * uv;
  bool is_inside = length(uv / radius) < 1.0f;

  float base_mask_value = texture_load(base_mask_tx, texel).x;
  float value = texture_load(mask_value_tx, texel).x;

#if defined(CMP_NODE_MASKTYPE_ADD)
  float output_mask_value = is_inside ? max(base_mask_value, value) : base_mask_value;
#elif defined(CMP_NODE_MASKTYPE_SUBTRACT)
  float output_mask_value = is_inside ? clamp(base_mask_value - value, 0.0f, 1.0f) :
                                        base_mask_value;
#elif defined(CMP_NODE_MASKTYPE_MULTIPLY)
  float output_mask_value = is_inside ? base_mask_value * value : 0.0f;
#elif defined(CMP_NODE_MASKTYPE_NOT)
  float output_mask_value = is_inside ? (base_mask_value > 0.0f ? 0.0f : value) : base_mask_value;
#endif

  imageStore(output_mask_img, texel, float4(output_mask_value));
}

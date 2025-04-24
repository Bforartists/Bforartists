/* SPDX-FileCopyrightText: 2019-2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

void node_bsdf_sheen(float4 color, float roughness, float3 N, float weight, out Closure result)
{
  color = max(color, float4(0.0f));
  roughness = saturate(roughness);
  N = safe_normalize(N);

  /* Fallback to diffuse. */
  ClosureDiffuse diffuse_data;
  diffuse_data.weight = weight;
  diffuse_data.color = color.rgb;
  diffuse_data.N = N;

  result = closure_eval(diffuse_data);
}

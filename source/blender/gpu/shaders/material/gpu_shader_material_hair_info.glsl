/* SPDX-FileCopyrightText: 2019-2022 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#include "gpu_shader_common_hash.glsl"

void node_hair_info(float hair_intercept,
                    float hair_length,
                    out float is_strand,
                    out float out_intercept,
                    out float out_length,
                    out float thickness,
                    out float3 normal,
                    out float random)
{
  is_strand = float(g_data.is_strand);
  out_intercept = hair_intercept;
  out_length = hair_length;
  thickness = g_data.hair_diameter;
  normal = g_data.curve_N;
  /* TODO: could be precomputed per strand instead. */
  random = wang_hash_noise(uint(g_data.hair_strand_id));
}

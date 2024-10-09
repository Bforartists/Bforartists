/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#pragma once

#include "eevee_bxdf_sampling_lib.glsl"
#include "eevee_lightprobe_sphere_lib.glsl"
#include "eevee_sampling_lib.glsl"
#include "gpu_shader_codegen_lib.glsl"
#include "gpu_shader_math_base_lib.glsl"

#ifdef SPHERE_PROBE
int lightprobe_spheres_select(vec3 P, float random_probe)
{
  for (int index = 0; index < SPHERE_PROBE_MAX; index++) {
    SphereProbeData probe_data = lightprobe_sphere_buf[index];
    /* SphereProbeData doesn't contain any gap, exit at first item that is invalid. */
    if (probe_data.atlas_coord.layer == -1) {
      /* We hit the end of the array. Return last valid index. */
      return index - 1;
    }
    /* NOTE: The vector-matrix multiplication swapped on purpose to cancel the matrix transpose. */
    vec3 lP = vec4(P, 1.0) * probe_data.world_to_probe_transposed;
    float gradient = (probe_data.influence_shape == SHAPE_ELIPSOID) ?
                         length(lP) :
                         max(max(abs(lP.x), abs(lP.y)), abs(lP.z));
    float score = saturate(probe_data.influence_bias - gradient * probe_data.influence_scale);
    if (score > random_probe) {
      return index;
    }
  }
  /* This should never happen (world probe is always last). */
  return SPHERE_PROBE_MAX - 1;
}
#endif /* SPHERE_PROBE */

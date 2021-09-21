/*
 * Copyright 2011-2013 Blender Foundation
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

#pragma once

#include "kernel/kernel_differential.h"
#include "kernel/kernel_projection.h"
#include "kernel/kernel_shader.h"

#include "kernel/geom/geom.h"

CCL_NAMESPACE_BEGIN

ccl_device void kernel_displace_evaluate(const KernelGlobals *kg,
                                         ccl_global const KernelShaderEvalInput *input,
                                         ccl_global float4 *output,
                                         const int offset)
{
  /* Setup shader data. */
  const KernelShaderEvalInput in = input[offset];

  ShaderData sd;
  shader_setup_from_displace(kg, &sd, in.object, in.prim, in.u, in.v);

  /* Evaluate displacement shader. */
  const float3 P = sd.P;
  shader_eval_displacement(INTEGRATOR_STATE_PASS_NULL, &sd);
  float3 D = sd.P - P;

  object_inverse_dir_transform(kg, &sd, &D);

  /* Write output. */
  output[offset] += make_float4(D.x, D.y, D.z, 0.0f);
}

ccl_device void kernel_background_evaluate(const KernelGlobals *kg,
                                           ccl_global const KernelShaderEvalInput *input,
                                           ccl_global float4 *output,
                                           const int offset)
{
  /* Setup ray */
  const KernelShaderEvalInput in = input[offset];
  const float3 ray_P = zero_float3();
  const float3 ray_D = equirectangular_to_direction(in.u, in.v);
  const float ray_time = 0.5f;

  /* Setup shader data. */
  ShaderData sd;
  shader_setup_from_background(kg, &sd, ray_P, ray_D, ray_time);

  /* Evaluate shader.
   * This is being evaluated for all BSDFs, so path flag does not contain a specific type. */
  const int path_flag = PATH_RAY_EMISSION;
  shader_eval_surface<KERNEL_FEATURE_NODE_MASK_SURFACE_LIGHT>(
      INTEGRATOR_STATE_PASS_NULL, &sd, NULL, path_flag);
  const float3 color = shader_background_eval(&sd);

  /* Write output. */
  output[offset] += make_float4(color.x, color.y, color.z, 0.0f);
}

CCL_NAMESPACE_END

/*
 * Copyright 2011-2021 Blender Foundation
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

#include "kernel/film/write_passes.h"
#include "kernel/integrator/path_state.h"
#include "kernel/integrator/state_util.h"

CCL_NAMESPACE_BEGIN

/* Check whether current surface bounce is where path is to be split for the shadow catcher. */
ccl_device_inline bool kernel_shadow_catcher_is_path_split_bounce(KernelGlobals kg,
                                                                  IntegratorState state,
                                                                  const int object_flag)
{
#ifdef __SHADOW_CATCHER__
  if (!kernel_data.integrator.has_shadow_catcher) {
    return false;
  }

  /* Check the flag first, avoiding fetches form global memory. */
  if ((object_flag & SD_OBJECT_SHADOW_CATCHER) == 0) {
    return false;
  }
  if (object_flag & SD_OBJECT_HOLDOUT_MASK) {
    return false;
  }

  const uint32_t path_flag = INTEGRATOR_STATE(state, path, flag);

  if ((path_flag & PATH_RAY_TRANSPARENT_BACKGROUND) == 0) {
    /* Split only on primary rays, secondary bounces are to treat shadow catcher as a regular
     * object. */
    return false;
  }

  if (path_flag & PATH_RAY_SHADOW_CATCHER_HIT) {
    return false;
  }

  return true;
#else
  (void)object_flag;
  return false;
#endif
}

/* Check whether the current path can still split. */
ccl_device_inline bool kernel_shadow_catcher_path_can_split(KernelGlobals kg,
                                                            ConstIntegratorState state)
{
  if (INTEGRATOR_PATH_IS_TERMINATED) {
    return false;
  }

  const uint32_t path_flag = INTEGRATOR_STATE(state, path, flag);

  if (path_flag & PATH_RAY_SHADOW_CATCHER_HIT) {
    /* Shadow catcher was already hit and the state was split. No further split is allowed. */
    return false;
  }

  return (path_flag & PATH_RAY_TRANSPARENT_BACKGROUND) != 0;
}

#ifdef __SHADOW_CATCHER__

ccl_device_forceinline bool kernel_shadow_catcher_is_matte_path(const uint32_t path_flag)
{
  return (path_flag & PATH_RAY_SHADOW_CATCHER_HIT) == 0;
}

ccl_device_forceinline bool kernel_shadow_catcher_is_object_pass(const uint32_t path_flag)
{
  return path_flag & PATH_RAY_SHADOW_CATCHER_PASS;
}

/* Write shadow catcher passes on a bounce from the shadow catcher object. */
ccl_device_forceinline void kernel_write_shadow_catcher_bounce_data(
    KernelGlobals kg, IntegratorState state, ccl_global float *ccl_restrict render_buffer)
{
  kernel_assert(kernel_data.film.pass_shadow_catcher_sample_count != PASS_UNUSED);
  kernel_assert(kernel_data.film.pass_shadow_catcher_matte != PASS_UNUSED);

  const uint32_t render_pixel_index = INTEGRATOR_STATE(state, path, render_pixel_index);
  const uint64_t render_buffer_offset = (uint64_t)render_pixel_index *
                                        kernel_data.film.pass_stride;
  ccl_global float *buffer = render_buffer + render_buffer_offset;

  /* Count sample for the shadow catcher object. */
  kernel_write_pass_float(buffer + kernel_data.film.pass_shadow_catcher_sample_count, 1.0f);

  /* Since the split is done, the sample does not contribute to the matte, so accumulate it as
   * transparency to the matte. */
  const float3 throughput = INTEGRATOR_STATE(state, path, throughput);
  kernel_write_pass_float(buffer + kernel_data.film.pass_shadow_catcher_matte + 3,
                          average(throughput));
}

#endif /* __SHADOW_CATCHER__ */

CCL_NAMESPACE_END

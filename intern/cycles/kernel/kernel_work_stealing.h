/*
 * Copyright 2011-2015 Blender Foundation
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

#ifndef __KERNEL_WORK_STEALING_H__
#define __KERNEL_WORK_STEALING_H__

CCL_NAMESPACE_BEGIN

/*
 * Utility functions for work stealing
 */

/* Map global work index to tile, pixel X/Y and sample. */
ccl_device_inline void get_work_pixel(ccl_global const WorkTile *tile,
                                      uint global_work_index,
                                      ccl_private uint *x,
                                      ccl_private uint *y,
                                      ccl_private uint *sample)
{
#ifdef __KERNEL_CUDA__
  /* Keeping threads for the same pixel together improves performance on CUDA. */
  uint sample_offset = global_work_index % tile->num_samples;
  uint pixel_offset = global_work_index / tile->num_samples;
#else  /* __KERNEL_CUDA__ */
  uint tile_pixels = tile->w * tile->h;
  uint sample_offset = global_work_index / tile_pixels;
  uint pixel_offset = global_work_index - sample_offset * tile_pixels;
#endif /* __KERNEL_CUDA__ */
  uint y_offset = pixel_offset / tile->w;
  uint x_offset = pixel_offset - y_offset * tile->w;

  *x = tile->x + x_offset;
  *y = tile->y + y_offset;
  *sample = tile->start_sample + sample_offset;
}

#ifdef __KERNEL_OPENCL__
#  pragma OPENCL EXTENSION cl_khr_global_int32_base_atomics : enable
#endif

#ifdef __SPLIT_KERNEL__
/* Returns true if there is work */
ccl_device bool get_next_work_item(KernelGlobals *kg,
                                   ccl_global uint *work_pools,
                                   uint total_work_size,
                                   uint ray_index,
                                   ccl_private uint *global_work_index)
{
  /* With a small amount of work there may be more threads than work due to
   * rounding up of global size, stop such threads immediately. */
  if (ray_index >= total_work_size) {
    return false;
  }

  /* Increase atomic work index counter in pool. */
  uint pool = ray_index / WORK_POOL_SIZE;
  uint work_index = atomic_fetch_and_inc_uint32(&work_pools[pool]);

  /* Map per-pool work index to a global work index. */
  uint global_size = ccl_global_size(0) * ccl_global_size(1);
  kernel_assert(global_size % WORK_POOL_SIZE == 0);
  kernel_assert(ray_index < global_size);

  *global_work_index = (work_index / WORK_POOL_SIZE) * global_size + (pool * WORK_POOL_SIZE) +
                       (work_index % WORK_POOL_SIZE);

  /* Test if all work for this pool is done. */
  return (*global_work_index < total_work_size);
}

ccl_device bool get_next_work(KernelGlobals *kg,
                              ccl_global uint *work_pools,
                              uint total_work_size,
                              uint ray_index,
                              ccl_private uint *global_work_index)
{
  bool got_work = false;
  if (kernel_data.film.pass_adaptive_aux_buffer) {
    do {
      got_work = get_next_work_item(kg, work_pools, total_work_size, ray_index, global_work_index);
      if (got_work) {
        ccl_global WorkTile *tile = &kernel_split_params.tile;
        uint x, y, sample;
        get_work_pixel(tile, *global_work_index, &x, &y, &sample);
        uint buffer_offset = (tile->offset + x + y * tile->stride) * kernel_data.film.pass_stride;
        ccl_global float *buffer = kernel_split_params.tile.buffer + buffer_offset;
        ccl_global float4 *aux = (ccl_global float4 *)(buffer +
                                                       kernel_data.film.pass_adaptive_aux_buffer);
        if ((*aux).w == 0.0f) {
          break;
        }
      }
    } while (got_work);
  }
  else {
    got_work = get_next_work_item(kg, work_pools, total_work_size, ray_index, global_work_index);
  }
  return got_work;
}
#endif

CCL_NAMESPACE_END

#endif /* __KERNEL_WORK_STEALING_H__ */

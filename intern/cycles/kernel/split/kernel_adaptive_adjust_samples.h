/*
 * Copyright 2019 Blender Foundation
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

CCL_NAMESPACE_BEGIN

ccl_device void kernel_adaptive_adjust_samples(KernelGlobals *kg)
{
  int pixel_index = ccl_global_id(1) * ccl_global_size(0) + ccl_global_id(0);
  if (pixel_index < kernel_split_params.tile.w * kernel_split_params.tile.h) {
    int x = kernel_split_params.tile.x + pixel_index % kernel_split_params.tile.w;
    int y = kernel_split_params.tile.y + pixel_index / kernel_split_params.tile.w;
    int buffer_offset = (kernel_split_params.tile.offset + x +
                         y * kernel_split_params.tile.stride) *
                        kernel_data.film.pass_stride;
    ccl_global float *buffer = kernel_split_params.tile.buffer + buffer_offset;
    int sample = kernel_split_params.tile.start_sample + kernel_split_params.tile.num_samples;
    if (buffer[kernel_data.film.pass_sample_count] < 0.0f) {
      buffer[kernel_data.film.pass_sample_count] = -buffer[kernel_data.film.pass_sample_count];
      float sample_multiplier = sample / max((float)kernel_split_params.tile.start_sample + 1.0f,
                                             buffer[kernel_data.film.pass_sample_count]);
      if (sample_multiplier != 1.0f) {
        kernel_adaptive_post_adjust(kg, buffer, sample_multiplier);
      }
    }
    else {
      kernel_adaptive_post_adjust(kg, buffer, sample / (sample - 1.0f));
    }
  }
}

CCL_NAMESPACE_END

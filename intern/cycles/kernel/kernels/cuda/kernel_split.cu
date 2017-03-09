/*
 * Copyright 2011-2016 Blender Foundation
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

/* CUDA split kernel entry points */

#ifdef __CUDA_ARCH__

#define __SPLIT_KERNEL__

#include "../../kernel_compat_cuda.h"
#include "kernel_config.h"

#include "../../split/kernel_split_common.h"
#include "../../split/kernel_data_init.h"
#include "../../split/kernel_path_init.h"
#include "../../split/kernel_scene_intersect.h"
#include "../../split/kernel_lamp_emission.h"
#include "../../split/kernel_queue_enqueue.h"
#include "../../split/kernel_background_buffer_update.h"
#include "../../split/kernel_shader_eval.h"
#include "../../split/kernel_holdout_emission_blurring_pathtermination_ao.h"
#include "../../split/kernel_direct_lighting.h"
#include "../../split/kernel_shadow_blocked.h"
#include "../../split/kernel_next_iteration_setup.h"

#include "../../kernel_film.h"

/* kernels */
extern "C" __global__ void
CUDA_LAUNCH_BOUNDS(CUDA_THREADS_BLOCK_WIDTH, CUDA_KERNEL_MAX_REGISTERS)
kernel_cuda_state_buffer_size(uint num_threads, uint *size)
{
	*size = split_data_buffer_size(NULL, num_threads);
}

extern "C" __global__ void
CUDA_LAUNCH_BOUNDS(CUDA_THREADS_BLOCK_WIDTH, CUDA_KERNEL_MAX_REGISTERS)
kernel_cuda_path_trace_data_init(
        ccl_global void *split_data_buffer,
        int num_elements,
        ccl_global char *ray_state,
        ccl_global uint *rng_state,
        int start_sample,
        int end_sample,
        int sx, int sy, int sw, int sh, int offset, int stride,
        ccl_global int *Queue_index,
        int queuesize,
        ccl_global char *use_queues_flag,
        ccl_global unsigned int *work_pool_wgs,
        unsigned int num_samples,
        ccl_global float *buffer)
{
	kernel_data_init(NULL,
	                 NULL,
	                 split_data_buffer,
	                 num_elements,
	                 ray_state,
	                 rng_state,
	                 start_sample,
	                 end_sample,
	                 sx, sy, sw, sh, offset, stride,
	                 Queue_index,
	                 queuesize,
	                 use_queues_flag,
	                 work_pool_wgs,
	                 num_samples,
	                 buffer);
}

#define DEFINE_SPLIT_KERNEL_FUNCTION(name) \
	extern "C" __global__ void \
	CUDA_LAUNCH_BOUNDS(CUDA_THREADS_BLOCK_WIDTH, CUDA_KERNEL_MAX_REGISTERS) \
	kernel_cuda_##name() \
	{ \
		kernel_##name(NULL); \
	}

DEFINE_SPLIT_KERNEL_FUNCTION(path_init)
DEFINE_SPLIT_KERNEL_FUNCTION(scene_intersect)
DEFINE_SPLIT_KERNEL_FUNCTION(lamp_emission)
DEFINE_SPLIT_KERNEL_FUNCTION(queue_enqueue)
DEFINE_SPLIT_KERNEL_FUNCTION(background_buffer_update)
DEFINE_SPLIT_KERNEL_FUNCTION(shader_eval)
DEFINE_SPLIT_KERNEL_FUNCTION(holdout_emission_blurring_pathtermination_ao)
DEFINE_SPLIT_KERNEL_FUNCTION(direct_lighting)
DEFINE_SPLIT_KERNEL_FUNCTION(shadow_blocked)
DEFINE_SPLIT_KERNEL_FUNCTION(next_iteration_setup)

extern "C" __global__ void
CUDA_LAUNCH_BOUNDS(CUDA_THREADS_BLOCK_WIDTH, CUDA_KERNEL_MAX_REGISTERS)
kernel_cuda_convert_to_byte(uchar4 *rgba, float *buffer, float sample_scale, int sx, int sy, int sw, int sh, int offset, int stride)
{
	int x = sx + blockDim.x*blockIdx.x + threadIdx.x;
	int y = sy + blockDim.y*blockIdx.y + threadIdx.y;

	if(x < sx + sw && y < sy + sh)
		kernel_film_convert_to_byte(NULL, rgba, buffer, sample_scale, x, y, offset, stride);
}

extern "C" __global__ void
CUDA_LAUNCH_BOUNDS(CUDA_THREADS_BLOCK_WIDTH, CUDA_KERNEL_MAX_REGISTERS)
kernel_cuda_convert_to_half_float(uchar4 *rgba, float *buffer, float sample_scale, int sx, int sy, int sw, int sh, int offset, int stride)
{
	int x = sx + blockDim.x*blockIdx.x + threadIdx.x;
	int y = sy + blockDim.y*blockIdx.y + threadIdx.y;

	if(x < sx + sw && y < sy + sh)
		kernel_film_convert_to_half_float(NULL, rgba, buffer, sample_scale, x, y, offset, stride);
}

#endif


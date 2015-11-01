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

#include "split/kernel_shadow_blocked.h"

__kernel void kernel_ocl_path_trace_shadow_blocked(
        ccl_global char *kg,
        ccl_constant KernelData *data,
        ccl_global char *sd_shadow,            /* Required for shadow blocked */
        ccl_global PathState *PathState_coop,  /* Required for shadow blocked */
        ccl_global Ray *LightRay_dl_coop,      /* Required for direct lighting's shadow blocked */
        ccl_global Ray *LightRay_ao_coop,      /* Required for AO's shadow blocked */
        Intersection *Intersection_coop_AO,
        Intersection *Intersection_coop_DL,
        ccl_global char *ray_state,
        ccl_global int *Queue_data,            /* Queue memory */
        ccl_global int *Queue_index,           /* Tracks the number of elements in each queue */
        int queuesize,                         /* Size (capacity) of each queue */
        int total_num_rays)
{
#if 0
	/* We will make the Queue_index entries '0' in the next kernel. */
	if(get_global_id(0) == 0 && get_global_id(1) == 0) {
		/* We empty this queue here */
		Queue_index[QUEUE_SHADOW_RAY_CAST_AO_RAYS] = 0;
		Queue_index[QUEUE_SHADOW_RAY_CAST_DL_RAYS] = 0;
	}
#endif

	int lidx = get_local_id(1) * get_local_id(0) + get_local_id(0);

	ccl_local unsigned int ao_queue_length;
	ccl_local unsigned int dl_queue_length;
	if(lidx == 0) {
		ao_queue_length = Queue_index[QUEUE_SHADOW_RAY_CAST_AO_RAYS];
		dl_queue_length = Queue_index[QUEUE_SHADOW_RAY_CAST_DL_RAYS];
	}
	barrier(CLK_LOCAL_MEM_FENCE);

	/* flag determining if the current ray is to process shadow ray for AO or DL */
	char shadow_blocked_type = -1;

	int ray_index = QUEUE_EMPTY_SLOT;
	int thread_index = get_global_id(1) * get_global_size(0) + get_global_id(0);
	if(thread_index < ao_queue_length + dl_queue_length) {
		if(thread_index < ao_queue_length) {
			ray_index = get_ray_index(thread_index, QUEUE_SHADOW_RAY_CAST_AO_RAYS, Queue_data, queuesize, 1);
			shadow_blocked_type = RAY_SHADOW_RAY_CAST_AO;
		} else {
			ray_index = get_ray_index(thread_index - ao_queue_length, QUEUE_SHADOW_RAY_CAST_DL_RAYS, Queue_data, queuesize, 1);
			shadow_blocked_type = RAY_SHADOW_RAY_CAST_DL;
		}
	}

	if(ray_index == QUEUE_EMPTY_SLOT)
		return;

	kernel_shadow_blocked((KernelGlobals *)kg,
	                      (ShaderData *)sd_shadow,
	                      PathState_coop,
	                      LightRay_dl_coop,
	                      LightRay_ao_coop,
	                      Intersection_coop_AO,
	                      Intersection_coop_DL,
	                      ray_state,
	                      total_num_rays,
	                      shadow_blocked_type,
	                      ray_index);
}

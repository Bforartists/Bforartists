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

/* Templated common implementation part of all CPU kernels.
 *
 * The idea is that particular .cpp files sets needed optimization flags and
 * simply includes this file without worry of copying actual implementation over.
 */

#include "kernel/kernel_compat_cpu.h"

#ifndef __SPLIT_KERNEL__
#  include "kernel/kernel_math.h"
#  include "kernel/kernel_types.h"

#  include "kernel/split/kernel_split_data.h"
#  include "kernel/kernel_globals.h"

#  include "kernel/kernels/cpu/kernel_cpu_image.h"
#  include "kernel/kernel_film.h"
#  include "kernel/kernel_path.h"
#  include "kernel/kernel_path_branched.h"
#  include "kernel/kernel_bake.h"
#else
#  include "kernel/split/kernel_split_common.h"

#  include "kernel/split/kernel_data_init.h"
#  include "kernel/split/kernel_path_init.h"
#  include "kernel/split/kernel_scene_intersect.h"
#  include "kernel/split/kernel_lamp_emission.h"
#  include "kernel/split/kernel_do_volume.h"
#  include "kernel/split/kernel_queue_enqueue.h"
#  include "kernel/split/kernel_indirect_background.h"
#  include "kernel/split/kernel_shader_setup.h"
#  include "kernel/split/kernel_shader_sort.h"
#  include "kernel/split/kernel_shader_eval.h"
#  include "kernel/split/kernel_holdout_emission_blurring_pathtermination_ao.h"
#  include "kernel/split/kernel_subsurface_scatter.h"
#  include "kernel/split/kernel_direct_lighting.h"
#  include "kernel/split/kernel_shadow_blocked_ao.h"
#  include "kernel/split/kernel_shadow_blocked_dl.h"
#  include "kernel/split/kernel_next_iteration_setup.h"
#  include "kernel/split/kernel_indirect_subsurface.h"
#  include "kernel/split/kernel_buffer_update.h"
#endif

CCL_NAMESPACE_BEGIN

#ifndef __SPLIT_KERNEL__

/* Path Tracing */

void KERNEL_FUNCTION_FULL_NAME(path_trace)(KernelGlobals *kg,
                                           float *buffer,
                                           unsigned int *rng_state,
                                           int sample,
                                           int x, int y,
                                           int offset,
                                           int stride)
{
#ifdef __BRANCHED_PATH__
	if(kernel_data.integrator.branched) {
		kernel_branched_path_trace(kg,
		                           buffer,
		                           rng_state,
		                           sample,
		                           x, y,
		                           offset,
		                           stride);
	}
	else
#endif
	{
		kernel_path_trace(kg, buffer, rng_state, sample, x, y, offset, stride);
	}
}

/* Film */

void KERNEL_FUNCTION_FULL_NAME(convert_to_byte)(KernelGlobals *kg,
                                                uchar4 *rgba,
                                                float *buffer,
                                                float sample_scale,
                                                int x, int y,
                                                int offset,
                                                int stride)
{
	kernel_film_convert_to_byte(kg,
	                            rgba,
	                            buffer,
	                            sample_scale,
	                            x, y,
	                            offset,
	                            stride);
}

void KERNEL_FUNCTION_FULL_NAME(convert_to_half_float)(KernelGlobals *kg,
                                                      uchar4 *rgba,
                                                      float *buffer,
                                                      float sample_scale,
                                                      int x, int y,
                                                      int offset,
                                                      int stride)
{
	kernel_film_convert_to_half_float(kg,
	                                  rgba,
	                                  buffer,
	                                  sample_scale,
	                                  x, y,
	                                  offset,
	                                  stride);
}

/* Shader Evaluate */

void KERNEL_FUNCTION_FULL_NAME(shader)(KernelGlobals *kg,
                                       uint4 *input,
                                       float4 *output,
                                       float *output_luma,
                                       int type,
                                       int filter,
                                       int i,
                                       int offset,
                                       int sample)
{
	if(type >= SHADER_EVAL_BAKE) {
		kernel_assert(output_luma == NULL);
#ifdef __BAKING__
		kernel_bake_evaluate(kg,
		                     input,
		                     output,
		                     (ShaderEvalType)type,
		                     filter,
		                     i,
		                     offset,
		                     sample);
#endif
	}
	else {
		kernel_shader_evaluate(kg,
		                       input,
		                       output,
		                       output_luma,
		                       (ShaderEvalType)type,
		                       i,
		                       sample);
	}
}

#else  /* __SPLIT_KERNEL__ */

/* Split Kernel Path Tracing */

#define DEFINE_SPLIT_KERNEL_FUNCTION(name) \
	void KERNEL_FUNCTION_FULL_NAME(name)(KernelGlobals *kg, KernelData* /*data*/) \
	{ \
		kernel_##name(kg); \
	}

#define DEFINE_SPLIT_KERNEL_FUNCTION_LOCALS(name, type) \
	void KERNEL_FUNCTION_FULL_NAME(name)(KernelGlobals *kg, KernelData* /*data*/) \
	{ \
		ccl_local type locals; \
		kernel_##name(kg, &locals); \
	}

DEFINE_SPLIT_KERNEL_FUNCTION(path_init)
DEFINE_SPLIT_KERNEL_FUNCTION(scene_intersect)
DEFINE_SPLIT_KERNEL_FUNCTION(lamp_emission)
DEFINE_SPLIT_KERNEL_FUNCTION(do_volume)
DEFINE_SPLIT_KERNEL_FUNCTION_LOCALS(queue_enqueue, QueueEnqueueLocals)
DEFINE_SPLIT_KERNEL_FUNCTION(indirect_background)
DEFINE_SPLIT_KERNEL_FUNCTION_LOCALS(shader_setup, uint)
DEFINE_SPLIT_KERNEL_FUNCTION_LOCALS(shader_sort, ShaderSortLocals)
DEFINE_SPLIT_KERNEL_FUNCTION(shader_eval)
DEFINE_SPLIT_KERNEL_FUNCTION_LOCALS(holdout_emission_blurring_pathtermination_ao, BackgroundAOLocals)
DEFINE_SPLIT_KERNEL_FUNCTION(subsurface_scatter)
DEFINE_SPLIT_KERNEL_FUNCTION_LOCALS(direct_lighting, uint)
DEFINE_SPLIT_KERNEL_FUNCTION(shadow_blocked_ao)
DEFINE_SPLIT_KERNEL_FUNCTION(shadow_blocked_dl)
DEFINE_SPLIT_KERNEL_FUNCTION_LOCALS(next_iteration_setup, uint)
DEFINE_SPLIT_KERNEL_FUNCTION(indirect_subsurface)
DEFINE_SPLIT_KERNEL_FUNCTION_LOCALS(buffer_update, uint)

void KERNEL_FUNCTION_FULL_NAME(register_functions)(void(*reg)(const char* name, void* func))
{
#define REGISTER_NAME_STRING(name) #name
#define REGISTER_EVAL_NAME(name) REGISTER_NAME_STRING(name)
#define REGISTER(name) reg(REGISTER_EVAL_NAME(KERNEL_FUNCTION_FULL_NAME(name)), (void*)KERNEL_FUNCTION_FULL_NAME(name));

	REGISTER(path_trace);
	REGISTER(convert_to_byte);
	REGISTER(convert_to_half_float);
	REGISTER(shader);

	REGISTER(data_init);
	REGISTER(path_init);
	REGISTER(scene_intersect);
	REGISTER(lamp_emission);
	REGISTER(do_volume);
	REGISTER(queue_enqueue);
	REGISTER(indirect_background);
	REGISTER(shader_setup);
	REGISTER(shader_sort);
	REGISTER(shader_eval);
	REGISTER(holdout_emission_blurring_pathtermination_ao);
	REGISTER(subsurface_scatter);
	REGISTER(direct_lighting);
	REGISTER(shadow_blocked_ao);
	REGISTER(shadow_blocked_dl);
	REGISTER(next_iteration_setup);
	REGISTER(indirect_subsurface);
	REGISTER(buffer_update);

#undef REGISTER
#undef REGISTER_EVAL_NAME
#undef REGISTER_NAME_STRING
}

#endif  /* __SPLIT_KERNEL__ */

CCL_NAMESPACE_END

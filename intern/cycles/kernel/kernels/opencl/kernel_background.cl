
#include "kernel/kernel_compat_opencl.h"
#include "kernel/kernel_math.h"
#include "kernel/kernel_types.h"
#include "kernel/kernel_globals.h"
#include "kernel/kernel_color.h"
#include "kernel/kernels/opencl/kernel_opencl_image.h"

#include "kernel/kernel_path.h"
#include "kernel/kernel_path_branched.h"

#include "kernel/kernel_bake.h"

__kernel void kernel_ocl_background(
	ccl_constant KernelData *data,
	ccl_global uint4 *input,
	ccl_global float4 *output,

	KERNEL_BUFFER_PARAMS,

	int type, int sx, int sw, int offset, int sample)
{
	KernelGlobals kglobals, *kg = &kglobals;

	kg->data = data;

	kernel_set_buffer_pointers(kg, KERNEL_BUFFER_ARGS);
	kernel_set_buffer_info(kg);

	int x = sx + ccl_global_id(0);

	if(x < sx + sw) {
		kernel_background_evaluate(kg, input, output, x);
	}
}

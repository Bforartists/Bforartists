/*
 * Copyright 2011, Blender Foundation.
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software Foundation,
 * Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
 */

/* CUDA kernel entry points */

#include "kernel_compat_cuda.h"
#include "kernel_math.h"
#include "kernel_types.h"
#include "kernel_globals.h"
#include "kernel_film.h"
#include "kernel_path.h"
#include "kernel_displace.h"

extern "C" __global__ void kernel_cuda_path_trace(float4 *buffer, uint *rng_state, int pass, int sx, int sy, int sw, int sh)
{
	int x = sx + blockDim.x*blockIdx.x + threadIdx.x;
	int y = sy + blockDim.y*blockIdx.y + threadIdx.y;

	if(x < sx + sw && y < sy + sh)
		kernel_path_trace(NULL, buffer, rng_state, pass, x, y);
}

extern "C" __global__ void kernel_cuda_tonemap(uchar4 *rgba, float4 *buffer, int pass, int resolution, int sx, int sy, int sw, int sh)
{
	int x = sx + blockDim.x*blockIdx.x + threadIdx.x;
	int y = sy + blockDim.y*blockIdx.y + threadIdx.y;

	if(x < sx + sw && y < sy + sh)
		kernel_film_tonemap(NULL, rgba, buffer, pass, resolution, x, y);
}

extern "C" __global__ void kernel_cuda_displace(uint4 *input, float3 *offset, int sx)
{
	int x = sx + blockDim.x*blockIdx.x + threadIdx.x;

	kernel_displace(NULL, input, offset, x);
}


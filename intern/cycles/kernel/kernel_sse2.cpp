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

/* Optimized CPU kernel entry points. This file is compiled with SSE2
 * optimization flags and nearly all functions inlined, while kernel.cpp
 * is compiled without for other CPU's. */

#ifdef WITH_OPTIMIZED_KERNEL

#define __KERNEL_SSE2__

#include "kernel.h"
#include "kernel_compat_cpu.h"
#include "kernel_math.h"
#include "kernel_types.h"
#include "kernel_globals.h"
#include "kernel_film.h"
#include "kernel_path.h"
#include "kernel_displace.h"

CCL_NAMESPACE_BEGIN

/* Path Tracing */

void kernel_cpu_sse2_path_trace(KernelGlobals *kg, float *buffer, unsigned int *rng_state, int sample, int x, int y, int offset, int stride)
{
	kernel_path_trace(kg, buffer, rng_state, sample, x, y, offset, stride);
}

/* Tonemapping */

void kernel_cpu_sse2_tonemap(KernelGlobals *kg, uchar4 *rgba, float *buffer, int sample, int x, int y, int offset, int stride)
{
	kernel_film_tonemap(kg, rgba, buffer, sample, x, y, offset, stride);
}

/* Shader Evaluate */

void kernel_cpu_sse2_shader(KernelGlobals *kg, uint4 *input, float4 *output, int type, int i)
{
	kernel_shader_evaluate(kg, input, output, (ShaderEvalType)type, i);
}

CCL_NAMESPACE_END

#endif


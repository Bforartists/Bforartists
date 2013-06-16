/*
 * Adapted from Open Shading Language with this license:
 *
 * Copyright (c) 2009-2010 Sony Pictures Imageworks Inc., et al.
 * All Rights Reserved.
 *
 * Modifications Copyright 2013, Blender Foundation.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are
 * met:
 * * Redistributions of source code must retain the above copyright
 *   notice, this list of conditions and the following disclaimer.
 * * Redistributions in binary form must reproduce the above copyright
 *   notice, this list of conditions and the following disclaimer in the
 *   documentation and/or other materials provided with the distribution.
 * * Neither the name of Sony Pictures Imageworks nor the names of its
 *   contributors may be used to endorse or promote products derived from
 *   this software without specific prior written permission.
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
 * "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
 * LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
 * A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
 * OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
 * SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
 * LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
 * DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
 * THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
 * (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
 * OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

CCL_NAMESPACE_BEGIN

/* Blackbody Node */

__device void svm_node_blackbody(KernelGlobals *kg, ShaderData *sd, float *stack, uint temperature_offset, uint col_offset)
{
	/* ToDo: move those defines to kernel_types.h ? */
	float bb_drapper = 800.0f;
	float bb_max_table_range = 12000.0f;
	float bb_table_xpower = 1.5f;
	float bb_table_ypower = 5.0f;
	float bb_table_spacing = 2.0f;

	/* Output */
	float3 color_rgb = make_float3(0.0f, 0.0f, 0.0f);

	/* Input */
	float temperature = stack_load_float(stack, temperature_offset);

	if (temperature < bb_drapper) {
		/* just return very very dim red */
		color_rgb = make_float3(1.0e-6f,0.0f,0.0f);
	}
	else if (temperature <= bb_max_table_range) {
		/* This is the overall size of the table (317*3+3) */
		const int lookuptablesize = 954;
		const float lookuptablesizef = 954.0f;

		/* reconstruct a proper index for the table lookup, compared to OSL we don't look up two colors
		just one (the OSL-lerp is also automatically done for us by "lookup_table_read") */
		float t = powf ((temperature - bb_drapper) / bb_table_spacing, 1.0f/bb_table_xpower);

		int blackbody_table_offset = kernel_data.blackbody.table_offset;

		/* Retrieve colors from the lookup table */
		float lutval = t/lookuptablesizef;
		float R = lookup_table_read(kg, lutval, blackbody_table_offset, lookuptablesize);
		lutval = (t + 317.0f*1.0f)/lookuptablesizef;
		float G = lookup_table_read(kg, lutval, blackbody_table_offset, lookuptablesize);
		lutval = (t + 317.0f*2.0f)/lookuptablesizef;
		float B = lookup_table_read(kg, lutval, blackbody_table_offset, lookuptablesize);

		R = powf(R, bb_table_ypower);
		G = powf(G, bb_table_ypower);
		B = powf(B, bb_table_ypower);

		/* Luminance */
		float l = linear_rgb_to_gray(make_float3(R, G, B));

		color_rgb = make_float3(R, G, B);
		color_rgb /= l;
	}

	if (stack_valid(col_offset))
		stack_store_float3(stack, col_offset, color_rgb);
}

CCL_NAMESPACE_END

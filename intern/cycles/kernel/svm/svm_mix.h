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

#include "svm_hsv.h"

CCL_NAMESPACE_BEGIN

__device float3 svm_lerp(const float3 a, const float3 b, float t)
{
	return (a * (1.0f - t) + b * t);
}

__device float3 svm_mix_blend(float t, float3 col1, float3 col2)
{
	return svm_lerp(col1, col2, t);
}

__device float3 svm_mix_add(float t, float3 col1, float3 col2)
{
	return svm_lerp(col1, col1 + col2, t);
}

__device float3 svm_mix_mul(float t, float3 col1, float3 col2)
{
	return svm_lerp(col1, col1 * col2, t);
}

__device float3 svm_mix_screen(float t, float3 col1, float3 col2)
{
	float tm = 1.0f - t;
	float3 one = make_float3(1.0f, 1.0f, 1.0f);
	float3 tm3 = make_float3(tm, tm, tm);

	return one - (tm3 + t*(one - col2))*(one - col1);
}

__device float3 svm_mix_overlay(float t, float3 col1, float3 col2)
{
	float tm = 1.0f - t;

	float3 outcol = col1;

	if(outcol.x < 0.5f)
		outcol.x *= tm + 2.0f*t*col2.x;
	else
		outcol.x = 1.0f - (tm + 2.0f*t*(1.0f - col2.x))*(1.0f - outcol.x);

	if(outcol.y < 0.5f)
		outcol.y *= tm + 2.0f*t*col2.y;
	else
		outcol.y = 1.0f - (tm + 2.0f*t*(1.0f - col2.y))*(1.0f - outcol.y);

	if(outcol.z < 0.5f)
		outcol.z *= tm + 2.0f*t*col2.z;
	else
		outcol.z = 1.0f - (tm + 2.0f*t*(1.0f - col2.z))*(1.0f - outcol.z);
	
	return outcol;
}

__device float3 svm_mix_sub(float t, float3 col1, float3 col2)
{
	return svm_lerp(col1, col1 - col2, t);
}

__device float3 svm_mix_div(float t, float3 col1, float3 col2)
{
	float tm = 1.0f - t;

	float3 outcol = col1;

	if(col2.x != 0.0f) outcol.x = tm*outcol.x + t*outcol.x/col2.x;
	if(col2.y != 0.0f) outcol.y = tm*outcol.y + t*outcol.y/col2.y;
	if(col2.z != 0.0f) outcol.z = tm*outcol.z + t*outcol.z/col2.z;

	return outcol;
}

__device float3 svm_mix_diff(float t, float3 col1, float3 col2)
{
	return svm_lerp(col1, fabs(col1 - col2), t);
}

__device float3 svm_mix_dark(float t, float3 col1, float3 col2)
{
	return min(col1, col2*t);
}

__device float3 svm_mix_light(float t, float3 col1, float3 col2)
{
	return max(col1, col2*t);
}

__device float3 svm_mix_dodge(float t, float3 col1, float3 col2)
{
	float3 outcol = col1;

	if(outcol.x != 0.0f) {
		float tmp = 1.0f - t*col2.x;
		if(tmp <= 0.0f)
			outcol.x = 1.0f;
		else if((tmp = outcol.x/tmp) > 1.0f)
			outcol.x = 1.0f;
		else
			outcol.x = tmp;
	}
	if(outcol.y != 0.0f) {
		float tmp = 1.0f - t*col2.y;
		if(tmp <= 0.0f)
			outcol.y = 1.0f;
		else if((tmp = outcol.y/tmp) > 1.0f)
			outcol.y = 1.0f;
		else
			outcol.y = tmp;
	}
	if(outcol.z != 0.0f) {
		float tmp = 1.0f - t*col2.z;
		if(tmp <= 0.0f)
			outcol.z = 1.0f;
		else if((tmp = outcol.z/tmp) > 1.0f)
			outcol.z = 1.0f;
		else
			outcol.z = tmp;
	}

	return outcol;
}

__device float3 svm_mix_burn(float t, float3 col1, float3 col2)
{
	float tmp, tm = 1.0f - t;

	float3 outcol = col1;

	tmp = tm + t*col2.x;
	if(tmp <= 0.0f)
		outcol.x = 0.0f;
	else if((tmp = (1.0f - (1.0f - outcol.x)/tmp)) < 0.0f)
		outcol.x = 0.0f;
	else if(tmp > 1.0f)
		outcol.x = 1.0f;
	else
		outcol.x = tmp;

	tmp = tm + t*col2.y;
	if(tmp <= 0.0f)
		outcol.y = 0.0f;
	else if((tmp = (1.0f - (1.0f - outcol.y)/tmp)) < 0.0f)
		outcol.y = 0.0f;
	else if(tmp > 1.0f)
		outcol.y = 1.0f;
	else
		outcol.y = tmp;

	tmp = tm + t*col2.z;
	if(tmp <= 0.0f)
		outcol.z = 0.0f;
	else if((tmp = (1.0f - (1.0f - outcol.z)/tmp)) < 0.0f)
		outcol.z = 0.0f;
	else if(tmp > 1.0f)
		outcol.z = 1.0f;
	else
		outcol.z = tmp;
	
	return outcol;
}

__device float3 svm_mix_hue(float t, float3 col1, float3 col2)
{
	float3 outcol = col1;

	float3 hsv2 = rgb_to_hsv(col2);

	if(hsv2.y != 0.0f) {
		float3 hsv = rgb_to_hsv(outcol);
		hsv.x = hsv2.x;
		float3 tmp = hsv_to_rgb(hsv); 

		outcol = svm_lerp(outcol, tmp, t);
	}

	return outcol;
}

__device float3 svm_mix_sat(float t, float3 col1, float3 col2)
{
	float tm = 1.0f - t;

	float3 outcol = col1;

	float3 hsv = rgb_to_hsv(outcol);

	if(hsv.y != 0.0f) {
		float3 hsv2 = rgb_to_hsv(col2);

		hsv.y = tm*hsv.y + t*hsv2.y;
		outcol = hsv_to_rgb(hsv);
	}

	return outcol;
}

__device float3 svm_mix_val(float t, float3 col1, float3 col2)
{
	float tm = 1.0f - t;

	float3 hsv = rgb_to_hsv(col1);
	float3 hsv2 = rgb_to_hsv(col2);

	hsv.z = tm*hsv.z + t*hsv2.z;

	return hsv_to_rgb(hsv);
}

__device float3 svm_mix_color(float t, float3 col1, float3 col2)
{
	float3 outcol = col1;
	float3 hsv2 = rgb_to_hsv(col2);

	if(hsv2.y != 0.0f) {
		float3 hsv = rgb_to_hsv(outcol);
		hsv.x = hsv2.x;
		hsv.y = hsv2.y;
		float3 tmp = hsv_to_rgb(hsv); 

		outcol = svm_lerp(outcol, tmp, t);
	}

	return outcol;
}

__device float3 svm_mix_soft(float t, float3 col1, float3 col2)
{
	float tm = 1.0f - t;

	float3 one= make_float3(1.0f, 1.0f, 1.0f);
	float3 scr= one - (one - col2)*(one - col1);

	return tm*col1 + t*((one - col1)*col2*col1 + col1*scr);
}

__device float3 svm_mix_linear(float t, float3 col1, float3 col2)
{
	float3 outcol = col1;

	if(col2.x > 0.5f)
		outcol.x= col1.x + t*(2.0f*(col2.x - 0.5f));
	else
		outcol.x= col1.x + t*(2.0f*(col2.x) - 1.0f);

	if(col2.y > 0.5f)
		outcol.y= col1.y + t*(2.0f*(col2.y - 0.5f));
	else
		outcol.y= col1.y + t*(2.0f*(col2.y) - 1.0f);

	if(col2.z > 0.5f)
		outcol.z= col1.z + t*(2.0f*(col2.z - 0.5f));
	else
		outcol.z= col1.z + t*(2.0f*(col2.z) - 1.0f);
	
	return outcol;
}

__device float3 svm_mix(NodeMix type, float fac, float3 c1, float3 c2)
{
	float t = clamp(fac, 0.0f, 1.0f);

	switch(type) {
		case NODE_MIX_BLEND: return svm_mix_blend(t, c1, c2);
		case NODE_MIX_ADD: return svm_mix_add(t, c1, c2);
		case NODE_MIX_MUL: return svm_mix_mul(t, c1, c2);
		case NODE_MIX_SCREEN: return svm_mix_screen(t, c1, c2);
		case NODE_MIX_OVERLAY: return svm_mix_overlay(t, c1, c2);
		case NODE_MIX_SUB: return svm_mix_sub(t, c1, c2);
		case NODE_MIX_DIV: return svm_mix_div(t, c1, c2);
		case NODE_MIX_DIFF: return svm_mix_diff(t, c1, c2);
		case NODE_MIX_DARK: return svm_mix_dark(t, c1, c2);
		case NODE_MIX_LIGHT: return svm_mix_light(t, c1, c2);
		case NODE_MIX_DODGE: return svm_mix_dodge(t, c1, c2);
		case NODE_MIX_BURN: return svm_mix_burn(t, c1, c2);
		case NODE_MIX_HUE: return svm_mix_hue(t, c1, c2);
		case NODE_MIX_SAT: return svm_mix_sat(t, c1, c2);
		case NODE_MIX_VAL: return svm_mix_val (t, c1, c2);
		case NODE_MIX_COLOR: return svm_mix_color(t, c1, c2);
		case NODE_MIX_SOFT: return svm_mix_soft(t, c1, c2);
		case NODE_MIX_LINEAR: return svm_mix_linear(t, c1, c2);
	}

	return make_float3(0.0f, 0.0f, 0.0f);
}

/* Node */

__device void svm_node_mix(KernelGlobals *kg, ShaderData *sd, float *stack, uint fac_offset, uint c1_offset, uint c2_offset, int *offset)
{
	/* read extra data */
	uint4 node1 = read_node(kg, offset);

	float fac = stack_load_float(stack, fac_offset);
	float3 c1 = stack_load_float3(stack, c1_offset);
	float3 c2 = stack_load_float3(stack, c2_offset);
	float3 result = svm_mix((NodeMix)node1.y, fac, c1, c2);

	stack_store_float3(stack, node1.z, result);
}

CCL_NAMESPACE_END


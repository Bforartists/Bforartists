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

#ifndef __SVM_H__
#define __SVM_H__

/* Shader Virtual Machine
 *
 * A shader is a list of nodes to be executed. These are simply read one after
 * the other and executed, using an node counter. Each node and it's associated
 * data is encoded as one or more uint4's in a 1D texture. If the data is larger
 * than an uint4, the node can increase the node counter to compensate for this.
 * Floats are encoded as int and then converted to float again.
 *
 * Nodes write their output into a stack. All stack data in the stack is
 * floats, since it's all factors, colors and vectors. The stack will be stored
 * in local memory on the GPU, as it would take too many register and indexes in
 * ways not known at compile time. This seems the only solution even though it
 * may be slow, with two positive factors. If the same shader is being executed,
 * memory access will be coalesced, and on fermi cards, memory will actually be
 * cached.
 *
 * The result of shader execution will be a single closure. This means the
 * closure type, associated label, data and weight. Sampling from multiple
 * closures is supported through the mix closure node, the logic for that is
 * mostly taken care of in the SVM compiler.
 */

#include "svm_types.h"

CCL_NAMESPACE_BEGIN

/* Stack */

__device float3 stack_load_float3(float *stack, uint a)
{
	kernel_assert(a+2 < SVM_STACK_SIZE);

	return make_float3(stack[a+0], stack[a+1], stack[a+2]);
}

__device void stack_store_float3(float *stack, uint a, float3 f)
{
	kernel_assert(a+2 < SVM_STACK_SIZE);

	stack[a+0] = f.x;
	stack[a+1] = f.y;
	stack[a+2] = f.z;
}

__device float stack_load_float(float *stack, uint a)
{
	kernel_assert(a < SVM_STACK_SIZE);

	return stack[a];
}

__device float stack_load_float_default(float *stack, uint a, uint value)
{
	return (a == (uint)SVM_STACK_INVALID)? __int_as_float(value): stack_load_float(stack, a);
}

__device void stack_store_float(float *stack, uint a, float f)
{
	kernel_assert(a < SVM_STACK_SIZE);

	stack[a] = f;
}

__device bool stack_valid(uint a)
{
	return a != (uint)SVM_STACK_INVALID;
}

/* Reading Nodes */

__device uint4 read_node(KernelGlobals *kg, int *offset)
{
	uint4 node = kernel_tex_fetch(__svm_nodes, *offset);
	(*offset)++;
	return node;
}

__device float4 read_node_float(KernelGlobals *kg, int *offset)
{
	uint4 node = kernel_tex_fetch(__svm_nodes, *offset);
	float4 f = make_float4(__int_as_float(node.x), __int_as_float(node.y), __int_as_float(node.z), __int_as_float(node.w));
	(*offset)++;
	return f;
}

__device void decode_node_uchar4(uint i, uint *x, uint *y, uint *z, uint *w)
{
	if(x) *x = (i & 0xFF);
	if(y) *y = ((i >> 8) & 0xFF);
	if(z) *z = ((i >> 16) & 0xFF);
	if(w) *w = ((i >> 24) & 0xFF);
}

CCL_NAMESPACE_END

/* Nodes */

#include "svm_noise.h"
#include "svm_texture.h"

#include "svm_attribute.h"
#include "svm_blend.h"
#include "svm_closure.h"
#include "svm_clouds.h"
#include "svm_convert.h"
#include "svm_displace.h"
#include "svm_distorted_noise.h"
#include "svm_fresnel.h"
#include "svm_geometry.h"
#include "svm_image.h"
#include "svm_light_path.h"
#include "svm_magic.h"
#include "svm_mapping.h"
#include "svm_marble.h"
#include "svm_math.h"
#include "svm_mix.h"
#include "svm_musgrave.h"
#include "svm_noisetex.h"
#include "svm_sky.h"
#include "svm_stucci.h"
#include "svm_tex_coord.h"
#include "svm_value.h"
#include "svm_voronoi.h"
#include "svm_wood.h"

CCL_NAMESPACE_BEGIN

/* Main Interpreter Loop */

__device void svm_eval_nodes(KernelGlobals *kg, ShaderData *sd, ShaderType type, float randb, int path_flag)
{
	float stack[SVM_STACK_SIZE];
	float closure_weight = 1.0f;
	int offset = sd->shader;

	sd->svm_closure = NBUILTIN_CLOSURES;
	sd->svm_closure_weight = make_float3(0.0f, 0.0f, 0.0f);

	while(1) {
		uint4 node = read_node(kg, &offset);

		if(node.x == NODE_SHADER_JUMP) {
			if(type == SHADER_TYPE_SURFACE) offset = node.y;
			else if(type == SHADER_TYPE_VOLUME) offset = node.z;
			else if(type == SHADER_TYPE_DISPLACEMENT) offset = node.w;
			else return;
		}
		else if(node.x == NODE_CLOSURE_BSDF)
			svm_node_closure_bsdf(sd, stack, node, randb);
		else if(node.x == NODE_CLOSURE_EMISSION)
			svm_node_closure_emission(sd);
		else if(node.x == NODE_CLOSURE_BACKGROUND)
			svm_node_closure_background(sd);
		else if(node.x == NODE_CLOSURE_SET_WEIGHT)
			svm_node_closure_set_weight(sd, node.y, node.z, node.w);
		else if(node.x == NODE_CLOSURE_WEIGHT)
			svm_node_closure_weight(sd, stack, node.y);
		else if(node.x == NODE_EMISSION_WEIGHT)
			svm_node_emission_weight(kg, sd, stack, node);
		else if(node.x == NODE_MIX_CLOSURE)
			svm_node_mix_closure(sd, stack, node.y, node.z, &offset, &randb);
		else if(node.x == NODE_ADD_CLOSURE)
			svm_node_add_closure(sd, stack, node.y, node.z, &offset, &randb, &closure_weight);
		else if(node.x == NODE_JUMP)
			offset = node.y;
#ifdef __TEXTURES__
		else if(node.x == NODE_TEX_NOISE_F)
			svm_node_tex_noise_f(sd, stack, node.y, node.z);
		else if(node.x == NODE_TEX_NOISE_V)
			svm_node_tex_noise_v(sd, stack, node.y, node.z);
		else if(node.x == NODE_TEX_IMAGE)
			svm_node_tex_image(kg, sd, stack, node.y, node.z, node.w);
		else if(node.x == NODE_TEX_ENVIRONMENT)
			svm_node_tex_environment(kg, sd, stack, node.y, node.z, node.w);
		else if(node.x == NODE_TEX_SKY)
			svm_node_tex_sky(kg, sd, stack, node.y, node.z);
		else if(node.x == NODE_TEX_BLEND)
			svm_node_tex_blend(sd, stack, node);
		else if(node.x == NODE_TEX_CLOUDS)
			svm_node_tex_clouds(sd, stack, node);
		else if(node.x == NODE_TEX_VORONOI)
			svm_node_tex_voronoi(kg, sd, stack, node, &offset);
		else if(node.x == NODE_TEX_MUSGRAVE)
			svm_node_tex_musgrave(kg, sd, stack, node, &offset);
		else if(node.x == NODE_TEX_MARBLE)
			svm_node_tex_marble(kg, sd, stack, node, &offset);
		else if(node.x == NODE_TEX_MAGIC)
			svm_node_tex_magic(sd, stack, node);
		else if(node.x == NODE_TEX_STUCCI)
			svm_node_tex_stucci(kg, sd, stack, node, &offset);
		else if(node.x == NODE_TEX_DISTORTED_NOISE)
			svm_node_tex_distorted_noise(kg, sd, stack, node, &offset);
		else if(node.x == NODE_TEX_WOOD)
			svm_node_tex_wood(kg, sd, stack, node, &offset);
#endif
		else if(node.x == NODE_GEOMETRY)
			svm_node_geometry(sd, stack, node.y, node.z);
		else if(node.x == NODE_GEOMETRY_BUMP_DX)
			svm_node_geometry_bump_dx(sd, stack, node.y, node.z);
		else if(node.x == NODE_GEOMETRY_BUMP_DY)
			svm_node_geometry_bump_dy(sd, stack, node.y, node.z);
		else if(node.x == NODE_LIGHT_PATH)
			svm_node_light_path(sd, stack, node.y, node.z, path_flag);
		else if(node.x == NODE_CONVERT)
			svm_node_convert(sd, stack, node.y, node.z, node.w);
		else if(node.x == NODE_VALUE_F)
			svm_node_value_f(kg, sd, stack, node.y, node.z);
		else if(node.x == NODE_VALUE_V)
			svm_node_value_v(kg, sd, stack, node.y, &offset);
		else if(node.x == NODE_MIX)
			svm_node_mix(kg, sd, stack, node.y, node.z, node.w, &offset);
		else if(node.x == NODE_ATTR)
			svm_node_attr(kg, sd, stack, node);
		else if(node.x == NODE_ATTR_BUMP_DX)
			svm_node_attr_bump_dx(kg, sd, stack, node);
		else if(node.x == NODE_ATTR_BUMP_DY)
			svm_node_attr_bump_dy(kg, sd, stack, node);
		else if(node.x == NODE_FRESNEL)
			svm_node_fresnel(sd, stack, node.y, node.z, node.w);
		else if(node.x == NODE_SET_DISPLACEMENT)
			svm_node_set_displacement(sd, stack, node.y);
		else if(node.x == NODE_SET_BUMP)
			svm_node_set_bump(sd, stack, node.y, node.z, node.w);
		else if(node.x == NODE_MATH)
			svm_node_math(kg, sd, stack, node.y, node.z, node.w, &offset);
		else if(node.x == NODE_VECTOR_MATH)
			svm_node_vector_math(kg, sd, stack, node.y, node.z, node.w, &offset);
		else if(node.x == NODE_MAPPING)
			svm_node_mapping(kg, sd, stack, node.y, node.z, &offset);
		else if(node.x == NODE_TEX_COORD)
			svm_node_tex_coord(kg, sd, stack, node.y, node.z);
		else if(node.x == NODE_TEX_COORD_BUMP_DX)
			svm_node_tex_coord_bump_dx(kg, sd, stack, node.y, node.z);
		else if(node.x == NODE_TEX_COORD_BUMP_DY)
			svm_node_tex_coord_bump_dy(kg, sd, stack, node.y, node.z);
		else if(node.x == NODE_EMISSION_SET_WEIGHT_TOTAL)
			svm_node_emission_set_weight_total(kg, sd, node.y, node.z, node.w);
		else if(node.x == NODE_END)
			break;
		else
			return;
	}

	sd->svm_closure_weight *= closure_weight;
}

CCL_NAMESPACE_END

#endif /* __SVM_H__ */


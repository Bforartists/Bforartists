/**
 * $Id: SHD_output.c 32517 2010-10-16 14:32:17Z campbellbarton $
 *
 * ***** BEGIN GPL LICENSE BLOCK *****
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
 *
 * The Original Code is Copyright (C) 2005 Blender Foundation.
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): none yet.
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#include "../SHD_util.h"
#include "SHD_noise.h"

static float distorted_noise(float vec[3], float size, int basis, int distortion_basis, float distortion)
{
	float p[3], r[3], p_offset[3], p_noffset[3];
	float offset[3] = {13.5f, 13.5f, 13.5f};

	mul_v3_v3fl(p, vec, 1.0f/size);
	add_v3_v3v3(p_offset, p, offset);
	sub_v3_v3v3(p_noffset, p, offset);

	r[0] = noise_basis(p_offset, basis) * distortion;
	r[1] = noise_basis(p, basis) * distortion;
	r[2] = noise_basis(p_noffset, basis) * distortion;

	add_v3_v3(p, r);

	return noise_basis(p, distortion_basis); /* distorted-domain noise */
}

/* **************** OUTPUT ******************** */

static bNodeSocketType sh_node_tex_distnoise_in[]= {
	{	SOCK_VECTOR, 1, "Vector",		0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 1.0f, SOCK_NO_VALUE},
	{	SOCK_VALUE, 1, "Size",			1.0f, 0.0f, 0.0f, 0.0f, 0.0f, 1000.0f},
	{	SOCK_VALUE, 1, "Distortion",	1.0f, 0.0f, 0.0f, 0.0f, 0.0f, 1000.0f},
	{	-1, 0, ""	}
};

static bNodeSocketType sh_node_tex_distnoise_out[]= {
	{	SOCK_VALUE, 0, "Fac",		0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 1.0f},
	{	-1, 0, ""	}
};

static void node_shader_init_tex_distorted_noise(bNode *node)
{
	NodeTexDistortedNoise *tex = MEM_callocN(sizeof(NodeTexDistortedNoise), "NodeTexDistortedNoise");
	tex->basis = SHD_NOISE_PERLIN;
	tex->distortion_basis = SHD_NOISE_PERLIN;

	node->storage = tex;
}

static void node_shader_exec_tex_distnoise(void *data, bNode *node, bNodeStack **in, bNodeStack **out)
{
	ShaderCallData *scd= (ShaderCallData*)data;
	NodeTexDistortedNoise *tex= (NodeTexDistortedNoise*)node->storage;
	bNodeSocket *vecsock = node->inputs.first;
	float vec[3], size, distortion;
	
	if(vecsock->link)
		nodestack_get_vec(vec, SOCK_VECTOR, in[0]);
	else
		copy_v3_v3(vec, scd->co);

	nodestack_get_vec(&size, SOCK_VALUE, in[1]);
	nodestack_get_vec(&distortion, SOCK_VALUE, in[2]);

	out[0]->vec[0]= distorted_noise(vec, size, tex->basis, tex->distortion_basis, distortion);
}

static int node_shader_gpu_tex_distnoise(GPUMaterial *mat, bNode *UNUSED(node), GPUNodeStack *in, GPUNodeStack *out)
{
	if(!in[0].link)
		in[0].link = GPU_attribute(CD_ORCO, "");

	return GPU_stack_link(mat, "node_tex_distnoise", in, out);
}

/* node type definition */
void register_node_type_sh_tex_distnoise(ListBase *lb)
{
	static bNodeType ntype;

	node_type_base(&ntype, SH_NODE_TEX_DISTNOISE, "Distorted Noise Texture", NODE_CLASS_TEXTURE, 0,
		sh_node_tex_distnoise_in, sh_node_tex_distnoise_out);
	node_type_size(&ntype, 150, 60, 200);
	node_type_init(&ntype, node_shader_init_tex_distorted_noise);
	node_type_storage(&ntype, "NodeTexDistortedNoise", node_free_standard_storage, node_copy_standard_storage);
	node_type_exec(&ntype, node_shader_exec_tex_distnoise);
	node_type_gpu(&ntype, node_shader_gpu_tex_distnoise);

	nodeRegisterType(lb, &ntype);
};


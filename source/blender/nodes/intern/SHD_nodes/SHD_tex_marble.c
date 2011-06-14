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

static float marble(float vec[3], float size, int type, int wave, int basis, int hard, float turb, int depth)
{
	float p[3];
	float x = vec[0];
	float y = vec[1];
	float z = vec[2];
	float n = 5.0f * (x + y + z);
	float mi;

	mul_v3_v3fl(p, vec, 1.0f/size);

	mi = n + turb * noise_turbulence(p, basis, depth, hard);

	mi = noise_wave(wave, mi);

	if(type == SHD_MARBLE_SHARP)
		mi = sqrt(mi);
	else if(type == SHD_MARBLE_SHARPER)
		mi = sqrt(sqrt(mi));

	return mi;
}

/* **************** MARBLE ******************** */

static bNodeSocketType sh_node_tex_marble_in[]= {
	{	SOCK_VECTOR, 1, "Vector",		0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 1.0f, SOCK_NO_VALUE},
	{	SOCK_VALUE, 1, "Size",			0.25f, 0.0f, 0.0f, 0.0f, 0.0f, 1000.0f},
	{	SOCK_VALUE, 1, "Turbulence",	5.0f, 0.0f, 0.0f, 0.0f, 0.0f, 1000.0f},
	{	-1, 0, ""	}
};

static bNodeSocketType sh_node_tex_marble_out[]= {
	{	SOCK_VALUE, 0, "Fac",		0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 1.0f},
	{	-1, 0, ""	}
};

static void node_shader_init_tex_marble(bNode *node)
{
	NodeTexMarble *tex = MEM_callocN(sizeof(NodeTexMarble), "NodeTexMarble");
	tex->type = SHD_MARBLE_SOFT;
	tex->wave = SHD_WAVE_SINE;
	tex->basis = SHD_NOISE_PERLIN;
	tex->hard = 0;
	tex->depth = 2;

	node->storage = tex;
}

static void node_shader_exec_tex_marble(void *data, bNode *node, bNodeStack **in, bNodeStack **out)
{
	ShaderCallData *scd= (ShaderCallData*)data;
	NodeTexMarble *tex= (NodeTexMarble*)node->storage;
	bNodeSocket *vecsock = node->inputs.first;
	float vec[3], size, turbulence;
	
	if(vecsock->link)
		nodestack_get_vec(vec, SOCK_VECTOR, in[0]);
	else
		copy_v3_v3(vec, scd->co);

	nodestack_get_vec(&size, SOCK_VALUE, in[1]);
	nodestack_get_vec(&turbulence, SOCK_VALUE, in[2]);

	out[0]->vec[0]= marble(vec, size, tex->type, tex->wave, tex->basis, tex->hard, turbulence, tex->depth);
}

static int node_shader_gpu_tex_marble(GPUMaterial *mat, bNode *UNUSED(node), GPUNodeStack *in, GPUNodeStack *out)
{
	return GPU_stack_link(mat, "node_tex_marble", in, out);
}

/* node type definition */
void register_node_type_sh_tex_marble(ListBase *lb)
{
	static bNodeType ntype;

	node_type_base(&ntype, SH_NODE_TEX_MARBLE, "Marble Texture", NODE_CLASS_TEXTURE, 0,
		sh_node_tex_marble_in, sh_node_tex_marble_out);
	node_type_size(&ntype, 150, 60, 200);
	node_type_init(&ntype, node_shader_init_tex_marble);
	node_type_storage(&ntype, "NodeTexMarble", node_free_standard_storage, node_copy_standard_storage);
	node_type_exec(&ntype, node_shader_exec_tex_marble);
	node_type_gpu(&ntype, node_shader_gpu_tex_marble);

	nodeRegisterType(lb, &ntype);
};


/*
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

#include "../node_shader_util.h"

/* **************** OUTPUT ******************** */

static bNodeSocketTemplate sh_node_tex_brick_in[] = {
	{	SOCK_VECTOR, 1, N_("Vector"),		0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 1.0f, PROP_NONE, SOCK_HIDE_VALUE},
	{ 	SOCK_RGBA, 1, 	N_("Color1"), 		0.8f, 0.8f, 0.8f, 1.0f, 0.0f, 1.0f},
	{ 	SOCK_RGBA, 1, 	N_("Color2"), 		0.2f, 0.2f, 0.2f, 1.0f, 0.0f, 1.0f},
	{ 	SOCK_RGBA, 1, 	N_("Mortar"), 		0.0f, 0.0f, 0.0f, 1.0f, 0.0f, 1.0f},
	{	SOCK_FLOAT, 1,  N_("Scale"),		5.0f, 0.0f, 0.0f, 0.0f, -1000.0f, 1000.0f},
	{	SOCK_FLOAT, 1,  N_("Mortar Size"),	0.02f, 0.0f, 0.0f, 0.0f, 0.0f, 0.125f},
	{	SOCK_FLOAT, 1,  N_("Bias"),		    0.0f, 0.0f, 0.0f, 0.0f, -1.0f, 1.0f},
	{	SOCK_FLOAT, 1,  N_("Brick Width"),	0.5f, 0.0f, 0.0f, 0.0f, 0.01f, 100.0f},
	{	SOCK_FLOAT, 1,  N_("Row Height"),   0.25f, 0.0f, 0.0f, 0.0f, 0.01f, 100.0f},
	{	-1, 0, ""	}
};

static bNodeSocketTemplate sh_node_tex_brick_out[] = {
	{	SOCK_RGBA, 0, N_("Color"),		0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 1.0f},
	{	SOCK_FLOAT, 0, N_("Fac"),		0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 1.0f},
	{	-1, 0, ""	}
};

static void node_shader_init_tex_brick(bNodeTree *UNUSED(ntree), bNode* node, bNodeTemplate *UNUSED(ntemp))
{
	NodeTexBrick *tex = MEM_callocN(sizeof(NodeTexBrick), "NodeTexBrick");
	default_tex_mapping(&tex->base.tex_mapping);
	default_color_mapping(&tex->base.color_mapping);
	
	tex->offset = 0.5f;
	tex->squash = 1.0f;
	tex->offset_freq = 2;
	tex->squash_freq = 2;

	node->storage = tex;
}

static int node_shader_gpu_tex_brick(GPUMaterial *mat, bNode *node, GPUNodeStack *in, GPUNodeStack *out)
{
	if (!in[0].link)
		in[0].link = GPU_attribute(CD_ORCO, "");

	node_shader_gpu_tex_mapping(mat, node, in, out);

	return GPU_stack_link(mat, "node_tex_brick", in, out);
}

/* node type definition */
void register_node_type_sh_tex_brick(bNodeTreeType *ttype)
{
	static bNodeType ntype;

	node_type_base(ttype, &ntype, SH_NODE_TEX_BRICK, "Brick Texture", NODE_CLASS_TEXTURE, NODE_OPTIONS);
	node_type_compatibility(&ntype, NODE_NEW_SHADING);
	node_type_socket_templates(&ntype, sh_node_tex_brick_in, sh_node_tex_brick_out);
	node_type_size(&ntype, 150, 60, 200);
	node_type_init(&ntype, node_shader_init_tex_brick);
	node_type_storage(&ntype, "NodeTexBrick", node_free_standard_storage, node_copy_standard_storage);
	node_type_exec(&ntype, NULL);
	node_type_gpu(&ntype, node_shader_gpu_tex_brick);

	nodeRegisterType(ttype, &ntype);
}

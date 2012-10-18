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

/** \file blender/nodes/shader/nodes/node_shader_bump.c
 *  \ingroup shdnodes
 */



#include "node_shader_util.h"


/* **************** BUMP ******************** */ 
static bNodeSocketTemplate sh_node_bump_in[]= { 
        { SOCK_FLOAT, 1, "Strength",	0.1f, 0.0f, 0.0f, 0.0f, -1000.0f, 1000.0f},
        { SOCK_FLOAT, 1, "Height",		1.0f, 1.0f, 1.0f, 1.0f, -1000.0f, 1000.0f, PROP_NONE, SOCK_HIDE_VALUE},
		{ -1, 0, "" } 
};

static bNodeSocketTemplate sh_node_bump_out[]= {
	{	SOCK_VECTOR, 0, "Normal"},
	{ -1, 0, "" } 
};

static int gpu_shader_bump(GPUMaterial *mat, bNode *node, GPUNodeStack *in, GPUNodeStack *out)
{
	return GPU_stack_link(mat, "node_bump", in, out, GPU_builtin(GPU_VIEW_NORMAL));
}

/* node type definition */
void register_node_type_sh_bump(bNodeTreeType *ttype)
{
	static bNodeType ntype;

	node_type_base(ttype, &ntype, SH_NODE_BUMP, "Bump", NODE_CLASS_OP_VECTOR, NODE_OPTIONS);
	node_type_compatibility(&ntype, NODE_NEW_SHADING);
	node_type_socket_templates(&ntype, sh_node_bump_in, sh_node_bump_out);
	node_type_size(&ntype, 150, 60, 200);
	node_type_storage(&ntype, "BumpNode", node_free_standard_storage, node_copy_standard_storage);
	node_type_exec(&ntype, NULL);
	node_type_gpu(&ntype, gpu_shader_bump);

	nodeRegisterType(ttype, &ntype);
}

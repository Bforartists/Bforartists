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

/* **************** OUTPUT ******************** */

static bNodeSocketType sh_node_bsdf_glass_in[]= {
	{	SOCK_RGBA, 1, "Color",		0.8f, 0.8f, 0.8f, 1.0f, 0.0f, 1.0f},
	{	SOCK_VALUE, 1, "Roughness",	0.2f, 0.0f, 0.0f, 0.0f, 0.0f, 1.0f},
	{	SOCK_VALUE, 1, "Fresnel",	0.3f, 0.0f, 0.0f, 0.0f, 0.0f, 1.0f},
	{	-1, 0, ""	}
};

static bNodeSocketType sh_node_bsdf_glass_out[]= {
	{	SOCK_CLOSURE, 0, "BSDF",		0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 1.0f},
	{	-1, 0, ""	}
};

static void node_shader_exec_bsdf_glass(void *data, bNode *node, bNodeStack **in, bNodeStack **UNUSED(out))
{
}

bNodeType sh_node_bsdf_glass= {
	/* *next,*prev */	NULL, NULL,
	/* type code   */	SH_NODE_BSDF_GLASS,
	/* name        */	"Glass BSDF",
	/* width+range */	150, 60, 200,
	/* class+opts  */	NODE_CLASS_CLOSURE, 0,
	/* input sock  */	sh_node_bsdf_glass_in,
	/* output sock */	sh_node_bsdf_glass_out,
	/* storage     */	"",
	/* execfunc    */	node_shader_exec_bsdf_glass,
	/* butfunc     */	NULL,
	/* initfunc    */	NULL,
	/* freestoragefunc    */	NULL,
	/* copystoragefunc    */	NULL,
	/* id          */	NULL, NULL, NULL,
	/* gpufunc     */	NULL
	
};
/* node type definition */
void register_node_type_sh_bsdf_glass(ListBase *lb)
{
	static bNodeType ntype;

	node_type_base(&ntype, SH_NODE_BSDF_GLASS, "Glass BSDF", NODE_CLASS_CLOSURE, 0,
		sh_node_bsdf_glass_in, sh_node_bsdf_glass_out);
	node_type_size(&ntype, 150, 60, 200);
	node_type_init(&ntype, NULL);
	node_type_storage(&ntype, "", NULL, NULL);
	node_type_exec(&ntype, node_shader_exec_bsdf_glass);
	node_type_gpu(&ntype, NULL);

	nodeRegisterType(lb, &ntype);
};


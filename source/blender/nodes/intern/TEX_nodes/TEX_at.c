/**
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
 * Contributor(s): R Allen
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#include "../TEX_util.h"                                                   

static bNodeSocketType inputs[]= {
	{ SOCK_RGBA,   1, "Texture",     0.0f, 0.0f, 0.0f, 1.0f, 0.0f, 1.0f },
	{ SOCK_VECTOR, 1, "Coordinates", 0.0f, 0.0f, 0.0f, 0.0f, -1.0f, 1.0f },
	{ -1, 0, "" }
};
static bNodeSocketType outputs[]= {
	{ SOCK_RGBA,   0, "Texture",     0.0f, 0.0f, 0.0f, 1.0f, 0.0f, 1.0f },
	{ -1, 0, "" }
};

static void colorfn(float *out, TexParams *p, bNode *UNUSED(node), bNodeStack **in, short thread)
{
	TexParams np = *p;
	float new_co[3];
	np.co = new_co;
	
	tex_input_vec(new_co, in[1], p, thread);
	tex_input_rgba(out, in[0], &np, thread);
}

static void exec(void *data, bNode *node, bNodeStack **in, bNodeStack **out)
{
	tex_output(node, in, out[0], &colorfn, data);
}

void register_node_type_tex_at(ListBase *lb)
{
	static bNodeType ntype;
	
	node_type_base(&ntype, TEX_NODE_AT, "At", NODE_CLASS_DISTORT, 0,
				   inputs, outputs);
	node_type_size(&ntype, 140, 100, 320);
	node_type_exec(&ntype, exec);
	
	nodeRegisterType(lb, &ntype);
}

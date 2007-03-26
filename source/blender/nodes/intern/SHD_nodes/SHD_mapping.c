/**
 * $Id$
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
 * Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
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

/* **************** MAPPING  ******************** */
static bNodeSocketType sh_node_mapping_in[]= {
	{	SOCK_VECTOR, 1, "Vector",	0.0f, 0.0f, 0.0f, 1.0f, -1.0f, 1.0f},
	{	-1, 0, ""	}
};

static bNodeSocketType sh_node_mapping_out[]= {
	{	SOCK_VECTOR, 0, "Vector",	0.0f, 0.0f, 1.0f, 1.0f, -1.0f, 1.0f},
	{	-1, 0, ""	}
};

/* do the regular mapping options for blender textures */
static void node_shader_exec_mapping(void *data, bNode *node, bNodeStack **in, bNodeStack **out)
{
	TexMapping *texmap= node->storage;
	float *vec= out[0]->vec;
	
	/* stack order input:  vector */
	/* stack order output: vector */
	nodestack_get_vec(vec, SOCK_VECTOR, in[0]);
	Mat4MulVecfl(texmap->mat, vec);
	
	if(texmap->flag & TEXMAP_CLIP_MIN) {
		if(vec[0]<texmap->min[0]) vec[0]= texmap->min[0];
		if(vec[1]<texmap->min[1]) vec[1]= texmap->min[1];
		if(vec[2]<texmap->min[2]) vec[2]= texmap->min[2];
	}
	if(texmap->flag & TEXMAP_CLIP_MAX) {
		if(vec[0]>texmap->max[0]) vec[0]= texmap->max[0];
		if(vec[1]>texmap->max[1]) vec[1]= texmap->max[1];
		if(vec[2]>texmap->max[2]) vec[2]= texmap->max[2];
	}
}


static void node_shader_init_mapping(bNode *node)
{
   node->storage= add_mapping();
}

bNodeType sh_node_mapping= {
	/* *next,*prev */	NULL, NULL,
	/* type code   */	SH_NODE_MAPPING,
	/* name        */	"Mapping",
	/* width+range */	240, 160, 320,
	/* class+opts  */	NODE_CLASS_OP_VECTOR, NODE_OPTIONS,
	/* input sock  */	sh_node_mapping_in,
	/* output sock */	sh_node_mapping_out,
	/* storage     */	"TexMapping",
	/* execfunc    */	node_shader_exec_mapping,
	/* butfunc     */ 	NULL,
	/* initfunc    */   node_shader_init_mapping
	
};


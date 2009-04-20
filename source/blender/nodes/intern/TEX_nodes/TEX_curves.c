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

#include "../TEX_util.h"

/* **************** CURVE Time  ******************** */

/* custom1 = sfra, custom2 = efra */
static bNodeSocketType time_outputs[]= {
	{ SOCK_VALUE, 0, "Value",	1.0f, 0.0f, 1.0f, 1.0f, 0.0f, 1.0f },
	{ -1, 0, "" }
};

static void time_colorfn(float *out, float *coord, bNode *node, bNodeStack **in, short thread)
{
	/* stack order output: fac */
	float fac= 0.0f;
	
	if(node->custom1 < node->custom2)
		fac = (G.scene->r.cfra - node->custom1)/(float)(node->custom2-node->custom1);
	
	fac = curvemapping_evaluateF(node->storage, 0, fac);
	out[0] = CLAMPIS(fac, 0.0f, 1.0f);
}

static void time_exec(void *data, bNode *node, bNodeStack **in, bNodeStack **out)
{
	tex_output(node, in, out[0], &time_colorfn);
}


static void time_init(bNode* node)
{
   node->custom1= G.scene->r.sfra;
   node->custom2= G.scene->r.efra;
   node->storage= curvemapping_add(1, 0.0f, 0.0f, 1.0f, 1.0f);
}

bNodeType tex_node_curve_time= {
	/* *next,*prev */	NULL, NULL,
	/* type code   */	TEX_NODE_CURVE_TIME,
	/* name        */	"Time",
	/* width+range */	140, 100, 320,
	/* class+opts  */	NODE_CLASS_INPUT, NODE_OPTIONS,
	/* input sock  */	NULL,
	/* output sock */	time_outputs,
	/* storage     */	"CurveMapping",
	/* execfunc    */	time_exec,
	/* butfunc     */	NULL,
	/* initfunc    */	time_init,
	/* freestoragefunc    */	node_free_curves,
	/* copystoragefunc    */	node_copy_curves,
	/* id          */	NULL
};

/* **************** CURVE RGB  ******************** */
static bNodeSocketType rgb_inputs[]= {
	{	SOCK_RGBA, 1, "Color",	0.0f, 0.0f, 0.0f, 1.0f, -1.0f, 1.0f},
	{	-1, 0, ""	}
};

static bNodeSocketType rgb_outputs[]= {
	{	SOCK_RGBA, 0, "Color",	0.0f, 0.0f, 1.0f, 1.0f, -1.0f, 1.0f},
	{	-1, 0, ""	}
};

static void rgb_colorfn(float *out, float *coord, bNode *node, bNodeStack **in, short thread)
{
	float cin[4];
	tex_input_rgba(cin, in[0], coord, thread);
	
	curvemapping_evaluateRGBF(node->storage, out, cin);
	out[3] = cin[3];
}

static void rgb_exec(void *data, bNode *node, bNodeStack **in, bNodeStack **out)
{
	tex_output(node, in, out[0], &rgb_colorfn);
}

static void rgb_init(bNode *node)
{
	node->storage= curvemapping_add(4, 0.0f, 0.0f, 1.0f, 1.0f);
}

bNodeType tex_node_curve_rgb= {
	/* *next,*prev */    NULL, NULL,
	/* type code   */    TEX_NODE_CURVE_RGB,
	/* name        */    "RGB Curves",
	/* width+range */    200, 140, 320,
	/* class+opts  */    NODE_CLASS_OP_COLOR, NODE_OPTIONS,
	/* input sock  */    rgb_inputs,
	/* output sock */    rgb_outputs,
	/* storage     */    "CurveMapping",
	/* execfunc    */    rgb_exec,
	/* butfunc     */    NULL,      
	/* initfunc    */     rgb_init,
	/* freestoragefunc */ node_free_curves,
	/* copystoragefunc */ node_copy_curves,
	/* id          */     NULL
};


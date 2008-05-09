/**
 *
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
 * The Original Code is Copyright (C) 2006 Blender Foundation.
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): Juho Vepsäläinen
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#include "../SHD_util.h"


/* **************** Hue Saturation ******************** */
static bNodeSocketType sh_node_hue_sat_in[]= {
	{	SOCK_VALUE, 1, "Hue",			0.5f, 0.0f, 0.0f, 0.0f, 0.0f, 1.0f},
	{	SOCK_VALUE, 1, "Saturation",		1.0f, 0.0f, 0.0f, 0.0f, 0.0f, 2.0f},
	{	SOCK_VALUE, 1, "Value",			1.0f, 0.0f, 0.0f, 0.0f, 0.0f, 2.0f},
	{	SOCK_VALUE, 1, "Fac",			1.0f, 0.0f, 0.0f, 0.0f, 0.0f, 1.0f},
	{	SOCK_RGBA, 1, "Color",			0.8f, 0.8f, 0.8f, 1.0f, 0.0f, 1.0f},
	{	-1, 0, ""	}
};
static bNodeSocketType sh_node_hue_sat_out[]= {
	{	SOCK_RGBA, 0, "Color",			0.0f, 0.0f, 0.0f, 1.0f, 0.0f, 1.0f},
	{	-1, 0, ""	}
};

/* note: it would be possible to use CMP version for both nodes */
static void do_hue_sat_fac(bNode *node, float *out, float *hue, float *sat, float *val, float *in, float *fac)
{
	if(*fac!=0.0f && (*hue!=0.5f || *sat!=1.0 || *val!=1.0)) {
		float col[3], hsv[3], mfac= 1.0f - *fac;
		
		rgb_to_hsv(in[0], in[1], in[2], hsv, hsv+1, hsv+2);
		hsv[0]+= (*hue - 0.5f);
		if(hsv[0]>1.0) hsv[0]-=1.0; else if(hsv[0]<0.0) hsv[0]+= 1.0;
		hsv[1]*= *sat;
		hsv[2]*= *val;
		hsv_to_rgb(hsv[0], hsv[1], hsv[2], col, col+1, col+2);
		
		out[0]= mfac*in[0] + *fac*col[0];
		out[1]= mfac*in[1] + *fac*col[1];
		out[2]= mfac*in[2] + *fac*col[2];
	}
	else {
		QUATCOPY(out, in);
	}
}

static void node_shader_exec_hue_sat(void *data, bNode *node, bNodeStack **in, bNodeStack **out)
{	
	do_hue_sat_fac(node, out[0]->vec, in[0]->vec, in[1]->vec, in[2]->vec, in[4]->vec, in[3]->vec);
}

bNodeType sh_node_hue_sat= {
	/* *next,*prev */	NULL, NULL,
	/* type code   */	SH_NODE_HUE_SAT,
	/* name        */	"Hue Saturation Value",
	/* width+range */	150, 80, 250,
	/* class+opts  */	NODE_CLASS_OP_COLOR, NODE_OPTIONS,
	/* input sock  */	sh_node_hue_sat_in,
	/* output sock */	sh_node_hue_sat_out,
	/* storage     */	"", 
	/* execfunc    */	node_shader_exec_hue_sat,
	/* butfunc     */	NULL,
	/* initfunc    */	NULL,
	/* freestoragefunc    */	NULL,
	/* copystoragefunc    */	NULL,
	/* id          */	NULL
	
};



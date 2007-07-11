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
 * The Original Code is Copyright (C) 2006 Blender Foundation.
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): none yet.
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#include "../CMP_util.h"


/* **************** SCALAR MATH ******************** */ 
static bNodeSocketType cmp_node_math_in[]= { 
	{ SOCK_VALUE, 1, "Value", 0.5f, 0.5f, 0.5f, 1.0f, -10000.0f, 10000.0f}, 
	{ SOCK_VALUE, 1, "Value", 0.5f, 0.5f, 0.5f, 1.0f, -10000.0f, 10000.0f}, 
	{ -1, 0, "" } 
};

static bNodeSocketType cmp_node_math_out[]= { 
	{ SOCK_VALUE, 0, "Value", 0.0f, 0.0f, 0.0f, 1.0f, 0.0f, 1.0f}, 
	{ -1, 0, "" } 
};

static void do_math(bNode *node, float *out, float *in, float *in2)
{
	switch(node->custom1)
	{
	case 0: /* Add */
		out[0]= in[0] + in2[0]; 
		break; 
	case 1: /* Subtract */
		out[0]= in[0] - in2[0];
		break; 
	case 2: /* Multiply */
		out[0]= in[0] * in2[0]; 
		break; 
	case 3: /* Divide */
		{
			if(in[1]==0)	/* We don't want to divide by zero. */
				out[0]= 0.0;
			else
				out[0]= in[0] / in2[0];
			}
		break;
	case 4: /* Sine */
		out[0]= sin(in[0]);
		break;
	case 5: /* Cosine */
		out[0]= cos(in[0]);
		break;
	case 6: /* Tangent */
		out[0]= tan(in[0]);
		break;
	case 7: /* Arc-Sine */
		{
			/* Can't do the impossible... */
			if(in[0] <= 1 && in[0] >= -1 )
				out[0]= asin(in[0]);
			else
				out[0]= 0.0;
		}
		break;
	case 8: /* Arc-Cosine */
		{
			/* Can't do the impossible... */
			if( in[0] <= 1 && in[0] >= -1 )
				out[0]= acos(in[0]);
			else
				out[0]= 0.0;
		}
		break;
	case 9: /* Arc-Tangent */
		out[0]= atan(in[0]);
		break;
	case 10: /* Power */
		{
			/* Don't want any imaginary numbers... */
			if( in[0] >= 0 )
				out[0]= pow(in[0], in2[0]);
			else
				out[0]= 0.0;
		}
		break;
	case 11: /* Logarithm */
		{
			/* Don't want any imaginary numbers... */
			if( in[0] > 0  && in2[0] > 0 )
				out[0]= log(in[0]) / log(in2[0]);
			else
				out[0]= 0.0;
		}
		break;
	case 12: /* Minimum */
		{
			if( in[0] < in2[0] )
				out[0]= in[0];
			else
				out[0]= in2[0];
		}
		break;
	case 13: /* Maximum */
		{
			if( in[0] > in2[0] )
				out[0]= in[0];
			else
				out[0]= in2[0];
		}
		break;
	case 14: /* Round */
		{
				out[0]= (int)(in[0] + 0.5f);
		}
		break; 
	}
}

static void node_composit_exec_math(void *data, bNode *node, bNodeStack **in, bNodeStack **out)
{
	CompBuf *cbuf=in[0]->data;
	CompBuf *cbuf2=in[1]->data;
	CompBuf *stackbuf; 

	/* check for inputs and outputs for early out*/
	if(in[0]->hasinput==0 || in[1]->hasinput==0) return;
	if(in[0]->data==NULL && in[1]->data==NULL) return;
	if(out[0]->hasoutput==0) return;

	/*create output based on first input */
	if(cbuf) {
		stackbuf=alloc_compbuf(cbuf->x, cbuf->y, CB_VAL, 1);
	}
	/* and if it doesn't exist use the second input since we 
 	know that one of them must exist at this point*/
	else  {
		stackbuf=alloc_compbuf(cbuf2->x, cbuf2->y, CB_VAL, 1);
	}

	/* operate in case there's valid size */
	composit2_pixel_processor(node, stackbuf, in[0]->data, in[0]->vec, in[1]->data, in[1]->vec, do_math, CB_VAL, CB_VAL);
	out[0]->data= stackbuf;
}

bNodeType cmp_node_math= {
	/* *next,*prev */	NULL, NULL,
	/* type code   */	CMP_NODE_MATH,
	/* name        */	"Math",
	/* width+range */	120, 110, 160,
	/* class+opts  */	NODE_CLASS_CONVERTOR, NODE_OPTIONS,
	/* input sock  */	cmp_node_math_in,
	/* output sock */	cmp_node_math_out,
	/* storage     */	"",
	/* execfunc    */	node_composit_exec_math,
	/* butfunc     */	NULL,
	/* initfunc    */	NULL,
	/* freestoragefunc    */	NULL,
	/* copystoragefunc    */	NULL,
	/* id          */	NULL
};




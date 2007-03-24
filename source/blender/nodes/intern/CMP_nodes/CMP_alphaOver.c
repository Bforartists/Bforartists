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

/* **************** ALPHAOVER ******************** */
static bNodeSocketType cmp_node_alphaover_in[]= {
	{	SOCK_VALUE, 1, "Fac",			1.0f, 0.0f, 1.0f, 1.0f, 0.0f, 1.0f},
	{	SOCK_RGBA, 1, "Image",			0.8f, 0.8f, 0.8f, 1.0f, 0.0f, 1.0f},
	{	SOCK_RGBA, 1, "Image",			0.8f, 0.8f, 0.8f, 1.0f, 0.0f, 1.0f},
	{	-1, 0, ""	}
};
static bNodeSocketType cmp_node_alphaover_out[]= {
	{	SOCK_RGBA, 0, "Image",			0.0f, 0.0f, 0.0f, 1.0f, 0.0f, 1.0f},
	{	-1, 0, ""	}
};

static void do_alphaover_premul(bNode *node, float *out, float *src, float *over, float *fac)
{
	
	if(over[3]<=0.0f) {
		QUATCOPY(out, src);
	}
	else if(*fac==1.0f && over[3]>=1.0f) {
		QUATCOPY(out, over);
	}
	else {
		float mul= 1.0f - *fac*over[3];

		out[0]= (mul*src[0]) + *fac*over[0];
		out[1]= (mul*src[1]) + *fac*over[1];
		out[2]= (mul*src[2]) + *fac*over[2];
		out[3]= (mul*src[3]) + *fac*over[3];
	}	
}

/* result will be still premul, but the over part is premulled */
static void do_alphaover_key(bNode *node, float *out, float *src, float *over, float *fac)
{
	
	if(over[3]<=0.0f) {
		QUATCOPY(out, src);
	}
	else if(*fac==1.0f && over[3]>=1.0f) {
		QUATCOPY(out, over);
	}
	else {
		float premul= fac[0]*over[3];
		float mul= 1.0f - premul;

		out[0]= (mul*src[0]) + premul*over[0];
		out[1]= (mul*src[1]) + premul*over[1];
		out[2]= (mul*src[2]) + premul*over[2];
		out[3]= (mul*src[3]) + fac[0]*over[3];
	}
}


static void node_composit_exec_alphaover(void *data, bNode *node, bNodeStack **in, bNodeStack **out)
{
	/* stack order in: col col */
	/* stack order out: col */
	if(out[0]->hasoutput==0) 
		return;
	
	/* input no image? then only color operation */
	if(in[1]->data==NULL) {
		do_alphaover_premul(node, out[0]->vec, in[1]->vec, in[2]->vec, in[0]->vec);
	}
	else {
		/* make output size of input image */
		CompBuf *cbuf= in[1]->data;
		CompBuf *stackbuf= alloc_compbuf(cbuf->x, cbuf->y, CB_RGBA, 1); /* allocs */
		
		if(node->custom1)
			composit3_pixel_processor(node, stackbuf, in[1]->data, in[1]->vec, in[2]->data, in[2]->vec, in[0]->data, in[0]->vec, do_alphaover_key, CB_RGBA, CB_RGBA, CB_VAL);
		else
			composit3_pixel_processor(node, stackbuf, in[1]->data, in[1]->vec, in[2]->data, in[2]->vec, in[0]->data, in[0]->vec, do_alphaover_premul, CB_RGBA, CB_RGBA, CB_VAL);
		
		out[0]->data= stackbuf;
	}
}

static int node_composit_buts_alphaover(uiBlock *block, bNodeTree *ntree, bNode *node, rctf *butr)
{
   if(block) {

      /* alpha type */
      uiDefButS(block, TOG, B_NODE_EXEC+node->nr, "ConvertPremul",
         butr->xmin, butr->ymin, butr->xmax-butr->xmin, 19, 
         &node->custom1, 0, 0, 0, 0, "");
   }
   return 19;
}

bNodeType cmp_node_alphaover= {
	/* type code   */	CMP_NODE_ALPHAOVER,
	/* name        */	"AlphaOver",
	/* width+range */	80, 40, 120,
	/* class+opts  */	NODE_CLASS_OP_COLOR, NODE_OPTIONS,
	/* input sock  */	cmp_node_alphaover_in,
	/* output sock */	cmp_node_alphaover_out,
	/* storage     */	"",
	/* execfunc    */	node_composit_exec_alphaover,
   /* butfunc     */ node_composit_buts_alphaover
	
};
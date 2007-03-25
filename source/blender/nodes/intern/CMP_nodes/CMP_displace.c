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


/* **************** Displace  ******************** */

static bNodeSocketType cmp_node_displace_in[]= {
	{	SOCK_RGBA, 1, "Image",			0.8f, 0.8f, 0.8f, 1.0f, 0.0f, 1.0f},
	{	SOCK_VECTOR, 1, "Vector",			1.0f, 0.0f, 0.0f, 0.0f, 0.0f, 1.0f},
	{	SOCK_VALUE, 1, "X Scale",				0.0f, 0.0f, 0.0f, 0.0f, -1000.0f, 1000.0f},
	{	SOCK_VALUE, 1, "Y Scale",				0.0f, 0.0f, 0.0f, 0.0f, -1000.0f, 1000.0f},
	{	-1, 0, ""	}
};
static bNodeSocketType cmp_node_displace_out[]= {
	{	SOCK_RGBA, 0, "Image",			0.0f, 0.0f, 0.0f, 1.0f, 0.0f, 1.0f},
	{	-1, 0, ""	}
};

static void do_displace(CompBuf *stackbuf, CompBuf *cbuf, CompBuf *vecbuf, float *veccol, float *xscale, float *yscale)
{
	ImBuf *ibuf;
	int x, y, sx, sy;
	float dx=0.0, dy=0.0;
	float dspx, dspy;
	float uv[2];

	float *out= stackbuf->rect, *vec=vecbuf->rect, *in= cbuf->rect;
	float *vp, *vpnext, *vpprev;
	
	int row = 3*vecbuf->x;
	
	/* ibuf needed for sampling */
	ibuf= IMB_allocImBuf(cbuf->x, cbuf->y, 32, 0, 0);
	ibuf->rect_float= cbuf->rect;
	
	vec = vecbuf->rect;
	
	sx= stackbuf->x;
	sy= stackbuf->y;
	
	for(y=0; y<sy; y++) {
		for(x= 0; x< sx; x++, out+=4, in+=4, vec+=3) {
			
			/* the x-xrad stuff is a bit weird, but i seem to need it otherwise 
			 * my returned pixels are offset weirdly */
			vp = compbuf_get_pixel(vecbuf, veccol, x-vecbuf->xrad, y-vecbuf->yrad, vecbuf->xrad, vecbuf->yrad);
			
			/* find the new displaced co-ords, also correcting for translate offset */
			dspx = x - (*xscale * vp[0]);
			dspy = y - (*yscale * vp[1]);

			/* convert image space to 0.0-1.0 UV space for sampling, correcting for translate offset */
			uv[0] = dspx / (float)sx;
			uv[1] = dspy / (float)sy;
			
			if(x>0 && x< vecbuf->x-1 && y>0 && y< vecbuf->y-1)  {
				vpnext = vp+row;
				vpprev = vp-row;
			
				/* adaptive sampling, X channel */
				dx= 0.5f*(fabs(vp[0]-vp[-3]) + fabs(vp[0]-vp[3]));
				
				dx+= 0.25f*(fabs(vp[0]-vpprev[-3]) + fabs(vp[0]-vpnext[-3]));
				dx+= 0.25f*(fabs(vp[0]-vpprev[+3]) + fabs(vp[0]-vpnext[+3]));
				
				/* adaptive sampling, Y channel */
				dy= 0.5f*(fabs(vp[1]-vp[-row+1]) + fabs(vp[1]-vp[row+1]));
						 
				dy+= 0.25f*(fabs(vp[1]-vpprev[+1-3]) + fabs(vp[1]-vpnext[+1-3]));
				dy+= 0.25f*(fabs(vp[1]-vpprev[+1+3]) + fabs(vp[1]-vpnext[+1+3]));
				
				/* scaled down to prevent blurriness */
				/* 8: magic number, provides a good level of sharpness without getting too aliased */
				dx /= 8;
				dy /= 8;
			}

			/* should use mipmap */
			if(dx > 0.006f) dx= 0.006f;
			if(dy > 0.006f) dy= 0.006f;
			if ((vp[0]> 0.0) && (dx < 0.004)) dx = 0.004;
			if ((vp[1]> 0.0) && (dy < 0.004)) dy = 0.004;
			

			ibuf_sample(ibuf, uv[0], uv[1], dx, dy, out);
		}
	}

	IMB_freeImBuf(ibuf);	
}


static void node_composit_exec_displace(void *data, bNode *node, bNodeStack **in, bNodeStack **out)
{
	if(out[0]->hasoutput==0)
		return;
	
	if(in[0]->data && in[1]->data) {
		CompBuf *cbuf= in[0]->data;
		CompBuf *vecbuf= in[1]->data;
		CompBuf *stackbuf;
		
		cbuf= typecheck_compbuf(cbuf, CB_RGBA);
		vecbuf= typecheck_compbuf(vecbuf, CB_VEC3);
		stackbuf= alloc_compbuf(cbuf->x, cbuf->y, CB_RGBA, 1); /* allocs */

		do_displace(stackbuf, cbuf, vecbuf, in[1]->vec, in[2]->vec, in[3]->vec);
		
		out[0]->data= stackbuf;
		
		
		if(cbuf!=in[0]->data)
			free_compbuf(cbuf);
		if(vecbuf!=in[1]->data)
			free_compbuf(vecbuf);
	}
}

bNodeType cmp_node_displace= {
	/* type code   */	CMP_NODE_DISPLACE,
	/* name        */	"Displace",
	/* width+range */	140, 100, 320,
	/* class+opts  */	NODE_CLASS_DISTORT, NODE_OPTIONS,
	/* input sock  */	cmp_node_displace_in,
	/* output sock */	cmp_node_displace_out,
	/* storage     */	"",
	/* execfunc    */	node_composit_exec_displace, 
	/* butfunc     */ 	NULL,
	/* initfunc    */	NULL
};


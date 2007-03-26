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

/* **************** SPLIT VIEWER ******************** */
static bNodeSocketType cmp_node_splitviewer_in[]= {
	{	SOCK_RGBA, 1, "Image",		0.0f, 0.0f, 0.0f, 1.0f, 0.0f, 1.0f},
	{	SOCK_RGBA, 1, "Image",		0.0f, 0.0f, 0.0f, 1.0f, 0.0f, 1.0f},
	{	-1, 0, ""	}
};

static void do_copy_split_rgba(bNode *node, float *out, float *in1, float *in2, float *fac)
{
	if(*fac==0.0f) {
		QUATCOPY(out, in1);
	}
	else {
		QUATCOPY(out, in2);
	}
}

static void node_composit_exec_splitviewer(void *data, bNode *node, bNodeStack **in, bNodeStack **out)
{
	/* image assigned to output */
	/* stack order input sockets: image image */
	
	if(in[0]->data==NULL || in[1]->data==NULL)
		return;
	
	if(node->id && (node->flag & NODE_DO_OUTPUT)) {	/* only one works on out */
		Image *ima= (Image *)node->id;
		RenderData *rd= data;
		ImBuf *ibuf;
		CompBuf *cbuf, *buf1, *buf2, *mask;
		int x, y;
		float offset;
		
		buf1= typecheck_compbuf(in[0]->data, CB_RGBA);
		buf2= typecheck_compbuf(in[1]->data, CB_RGBA);
		
		BKE_image_user_calc_imanr(node->storage, rd->cfra, 0);
		
		/* always returns for viewer image, but we check nevertheless */
		ibuf= BKE_image_get_ibuf(ima, node->storage);
		if(ibuf==NULL) {
			printf("node_composit_exec_viewer error\n");
			return;
		}
		
		/* free all in ibuf */
		imb_freerectImBuf(ibuf);
		imb_freerectfloatImBuf(ibuf);
		IMB_freezbuffloatImBuf(ibuf);
		
		/* make ibuf, and connect to ima */
		ibuf->x= buf1->x;
		ibuf->y= buf1->y;
		imb_addrectfloatImBuf(ibuf);
		
		ima->ok= IMA_OK_LOADED;

		/* output buf */
		cbuf= alloc_compbuf(buf1->x, buf1->y, CB_RGBA, 0);	/* no alloc*/
		cbuf->rect= ibuf->rect_float;
		
		/* mask buf */
		mask= alloc_compbuf(buf1->x, buf1->y, CB_VAL, 1);
		
		
		/* Check which offset mode is selected and limit offset if needed */
		if(node->custom2 == 0) {
			offset = buf1->x / 100.0f * node->custom1;
			CLAMP(offset, 0, buf1->x);
		}
		else {
			offset = buf1->y / 100.0f * node->custom1;
			CLAMP(offset, 0, buf1->y);
		}
		
		if(node->custom2 == 0) {
			for(y=0; y<buf1->y; y++) {
				float *fac= mask->rect + y*buf1->x;
				for(x=offset; x>0; x--, fac++)
					*fac= 1.0f;
			}
		}
		else {
			for(y=0; y<offset; y++) {
				float *fac= mask->rect + y*buf1->x;
				for(x=buf1->x; x>0; x--, fac++)
					*fac= 1.0f;
			}
		}
		
		composit3_pixel_processor(node, cbuf, buf1, in[0]->vec, buf2, in[1]->vec, mask, NULL, do_copy_split_rgba, CB_RGBA, CB_RGBA, CB_VAL);
		
		generate_preview(node, cbuf);
		free_compbuf(cbuf);
		free_compbuf(mask);
		
		if(in[0]->data != buf1) 
			free_compbuf(buf1);
		if(in[1]->data != buf2) 
			free_compbuf(buf2);
	}
}

static void node_composit_init_splitviewer(bNode* node)
{
   ImageUser *iuser= MEM_callocN(sizeof(ImageUser), "node image user");
   node->storage= iuser;
   iuser->sfra= 1;
   iuser->fie_ima= 2;
   iuser->ok= 1;
   node->custom1= 50;	/* default 50% split */
}

bNodeType cmp_node_splitviewer= {
	/* *next,*prev */	NULL, NULL,
	/* type code   */	CMP_NODE_SPLITVIEWER,
	/* name        */	"SplitViewer",
	/* width+range */	140, 100, 320,
	/* class+opts  */	NODE_CLASS_OUTPUT, NODE_PREVIEW|NODE_OPTIONS,
	/* input sock  */	cmp_node_splitviewer_in,
	/* output sock */	NULL,
	/* storage     */	"ImageUser",
	/* execfunc    */	node_composit_exec_splitviewer,
	/* butfunc     */ 	NULL,
	/* initfunc    */   node_composit_init_splitviewer
};





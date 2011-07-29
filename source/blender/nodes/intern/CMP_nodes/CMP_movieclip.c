/*
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
 * Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
 *
 * The Original Code is Copyright (C) 2011 Blender Foundation.
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): Blender Foundation,
 *                 Sergey Sharybin
 *
 * ***** END GPL LICENSE BLOCK *****
 */

/** \file blender/nodes/intern/CMP_nodes/CMP_movieclip.c
 *  \ingroup cmpnodes
 */


#include "../CMP_util.h"

static bNodeSocketType cmp_node_rlayers_out[]= {
	{	SOCK_RGBA, 0, "Image",		0.0f, 0.0f, 0.0f, 1.0f, 0.0f, 1.0f},
	{	-1, 0, ""	}
};

static CompBuf *node_composit_get_movieclip(RenderData *rd, MovieClip *clip, MovieClipUser *user)
{
	ImBuf *ibuf;
	CompBuf *stackbuf;
	int type;

	float *rect;
	int alloc= FALSE;

	ibuf= BKE_movieclip_acquire_ibuf(clip, user);

	if(ibuf==NULL || (ibuf->rect==NULL && ibuf->rect_float==NULL)) {
		IMB_freeImBuf(ibuf);
		return NULL;
	}

	if (ibuf->rect_float == NULL || ibuf->userflags&IB_RECT_INVALID) {
		IMB_float_from_rect(ibuf);
		ibuf->userflags&= ~IB_RECT_INVALID;
	}

	/* now we need a float buffer from the image with matching color management */
	if(ibuf->channels == 4) {
		if(rd->color_mgt_flag & R_COLOR_MANAGEMENT) {
			if(ibuf->profile != IB_PROFILE_NONE) {
				rect= ibuf->rect_float;
			}
			else {
				rect= MEM_mapallocN(sizeof(float) * 4 * ibuf->x * ibuf->y, "node_composit_get_image");
				srgb_to_linearrgb_rgba_rgba_buf(rect, ibuf->rect_float, ibuf->x * ibuf->y);
				alloc= TRUE;
			}
		}
		else {
			if(ibuf->profile == IB_PROFILE_NONE) {
				rect= ibuf->rect_float;
			}
			else {
				rect= MEM_mapallocN(sizeof(float) * 4 * ibuf->x * ibuf->y, "node_composit_get_image");
				linearrgb_to_srgb_rgba_rgba_buf(rect, ibuf->rect_float, ibuf->x * ibuf->y);
				alloc= TRUE;
			}
		}
	}
	else {
		/* non-rgba passes can't use color profiles */
		rect= ibuf->rect_float;
	}
	/* done coercing into the correct color management */

	if(!alloc) {
		rect= MEM_dupallocN(rect);
		alloc= 1;
	}

	type= ibuf->channels;

	if(rd->scemode & R_COMP_CROP) {
		stackbuf= get_cropped_compbuf(&rd->disprect, rect, ibuf->x, ibuf->y, type);
		if(alloc)
			MEM_freeN(rect);
	}
	else {
		/* we put imbuf copy on stack, cbuf knows rect is from other ibuf when freed! */
		stackbuf= alloc_compbuf(ibuf->x, ibuf->y, type, FALSE);
		stackbuf->rect= rect;
		stackbuf->malloc= alloc;
	}

	IMB_freeImBuf(ibuf);

	return stackbuf;
}

static void node_composit_exec_movieclip(void *data, bNode *node, bNodeStack **UNUSED(in), bNodeStack **out)
{
	if(node->id) {
		RenderData *rd= data;
		MovieClip *clip= (MovieClip *)node->id;
		MovieClipUser *user= (MovieClipUser *)node->storage;
		CompBuf *stackbuf= NULL;

		BKE_movieclip_user_set_frame(user, rd->cfra);

		stackbuf= node_composit_get_movieclip(rd, clip, user);

		if (stackbuf) {
			/* put image on stack */
			out[0]->data= stackbuf;

			/* generate preview */
			generate_preview(data, node, stackbuf);
		}
	}
}

static void node_composit_init_movieclip(bNode* node)
{
	MovieClipUser *user= MEM_callocN(sizeof(MovieClipUser), "node movie clip user");
	node->storage= user;
	user->framenr= 1;
}

void register_node_type_cmp_movieclip(ListBase *lb)
{
	static bNodeType ntype;

	node_type_base(&ntype, CMP_NODE_MOVIECLIP, "Movie Clip", NODE_CLASS_INPUT, NODE_PREVIEW|NODE_OPTIONS,
		NULL, cmp_node_rlayers_out);
	node_type_size(&ntype, 120, 80, 300);
	node_type_init(&ntype, node_composit_init_movieclip);
	node_type_storage(&ntype, "MovieClipUser", node_free_standard_storage, node_copy_standard_storage);
	node_type_exec(&ntype, node_composit_exec_movieclip);

	nodeRegisterType(lb, &ntype);
}

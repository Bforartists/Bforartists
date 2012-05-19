/*
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
 * Contributor(s): David Millan Escriva, Juho Vepsäläinen, Bob Holcomb, Thomas Dinges
 *
 * ***** END GPL LICENSE BLOCK *****
 */

/** \file blender/editors/space_node/drawnode.c
 *  \ingroup spnode
 */


#include <math.h>
#include <stdio.h>
#include <string.h>

#include "BLI_blenlib.h"
#include "BLI_math.h"
#include "BLI_utildefines.h"

#include "DNA_node_types.h"
#include "DNA_material_types.h"
#include "DNA_object_types.h"
#include "DNA_scene_types.h"
#include "DNA_space_types.h"
#include "DNA_screen_types.h"

#include "BKE_context.h"
#include "BKE_curve.h"
#include "BKE_global.h"
#include "BKE_image.h"
#include "BKE_library.h"
#include "BKE_main.h"
#include "BKE_node.h"

#include "NOD_composite.h"
#include "NOD_shader.h"

#include "BIF_gl.h"
#include "BIF_glutil.h"

#include "BLF_api.h"

#include "MEM_guardedalloc.h"


#include "RNA_access.h"

#include "ED_node.h"

#include "WM_api.h"
#include "WM_types.h"

#include "UI_interface.h"
#include "UI_resources.h"

#include "IMB_imbuf.h"
#include "IMB_imbuf_types.h"

#include "node_intern.h"

/* ****************** SOCKET BUTTON DRAW FUNCTIONS ***************** */

static void node_sync_cb(bContext *UNUSED(C), void *snode_v, void *node_v)
{
	SpaceNode *snode= snode_v;
	
	if (snode->treetype==NTREE_SHADER) {
		nodeShaderSynchronizeID(node_v, 1);
		// allqueue(REDRAWBUTSSHADING, 0);
	}
}

static void node_socket_button_label(const bContext *UNUSED(C), uiBlock *block,
							  bNodeTree *UNUSED(ntree), bNode *UNUSED(node), bNodeSocket *sock,
							  const char *UNUSED(name), int x, int y, int width)
{
	uiDefBut(block, LABEL, 0, sock->name, x, y, width, NODE_DY, NULL, 0, 0, 0, 0, "");
}

static void node_socket_button_default(const bContext *C, uiBlock *block,
								bNodeTree *ntree, bNode *node, bNodeSocket *sock,
								const char *name, int x, int y, int width)
{
	if (sock->link || (sock->flag & SOCK_HIDE_VALUE))
		node_socket_button_label(C, block, ntree, node, sock, name, x, y, width);
	else {
		PointerRNA ptr;
		uiBut *bt;
		
		RNA_pointer_create(&ntree->id, &RNA_NodeSocket, sock, &ptr);
		
		bt = uiDefButR(block, NUM, B_NODE_EXEC, name,
					   x, y+1, width, NODE_DY-2, 
					   &ptr, "default_value", 0, 0, 0, -1, -1, NULL);
		if (node)
			uiButSetFunc(bt, node_sync_cb, CTX_wm_space_node(C), node);
	}
}

typedef struct SocketComponentMenuArgs {
	PointerRNA ptr;
	int x, y, width;
	uiButHandleFunc cb;
	void *arg1, *arg2;
} SocketComponentMenuArgs;
/* NOTE: this is a block-menu, needs 0 events, otherwise the menu closes */
static uiBlock *socket_component_menu(bContext *C, ARegion *ar, void *args_v)
{
	SocketComponentMenuArgs *args= (SocketComponentMenuArgs*)args_v;
	uiBlock *block;
	uiLayout *layout;
	
	block= uiBeginBlock(C, ar, __func__, UI_EMBOSS);
	uiBlockSetFlag(block, UI_BLOCK_KEEP_OPEN);
	
	layout= uiLayoutColumn(uiBlockLayout(block, UI_LAYOUT_VERTICAL, UI_LAYOUT_PANEL, args->x, args->y+2, args->width, NODE_DY, UI_GetStyle()), 0);
	
	uiItemR(layout, &args->ptr, "default_value", UI_ITEM_R_EXPAND, "", ICON_NONE);
	
	return block;
}
static void node_socket_button_components(const bContext *C, uiBlock *block,
								   bNodeTree *ntree, bNode *node, bNodeSocket *sock,
								   const char *name, int x, int y, int width)
{
	if (sock->link || (sock->flag & SOCK_HIDE_VALUE))
		node_socket_button_label(C, block, ntree, node, sock, name, x, y, width);
	else {
		PointerRNA ptr;
		SocketComponentMenuArgs *args;
		
		RNA_pointer_create(&ntree->id, &RNA_NodeSocket, sock, &ptr);
		
		args= MEM_callocN(sizeof(SocketComponentMenuArgs), "SocketComponentMenuArgs");
		
		args->ptr = ptr;
		args->x = x;
		args->y = y;
		args->width = width;
		args->cb = node_sync_cb;
		args->arg1 = CTX_wm_space_node(C);
		args->arg2 = node;
		
		uiDefBlockButN(block, socket_component_menu, args, name, x, y+1, width, NODE_DY-2, "");
	}
}

static void node_socket_button_color(const bContext *C, uiBlock *block,
							  bNodeTree *ntree, bNode *node, bNodeSocket *sock,
							  const char *name, int x, int y, int width)
{
	if (sock->link || (sock->flag & SOCK_HIDE_VALUE))
		node_socket_button_label(C, block, ntree, node, sock, name, x, y, width);
	else {
		PointerRNA ptr;
		uiBut *bt;
		int labelw= width - 40;
		RNA_pointer_create(&ntree->id, &RNA_NodeSocket, sock, &ptr);
		
		bt=uiDefButR(block, COL, B_NODE_EXEC, "",
					 x, y+2, (labelw>0 ? 40 : width), NODE_DY-2, 
					 &ptr, "default_value", 0, 0, 0, -1, -1, NULL);
		if (node)
			uiButSetFunc(bt, node_sync_cb, CTX_wm_space_node(C), node);
		
		if (name[0]!='\0' && labelw>0)
			uiDefBut(block, LABEL, 0, name, x + 40, y+2, labelw, NODE_DY-2, NULL, 0, 0, 0, 0, "");
	}
}

/* standard draw function, display the default input value */
static void node_draw_input_default(const bContext *C, uiBlock *block,
                                     bNodeTree *ntree, bNode *node, bNodeSocket *sock,
                                     const char *name, int x, int y, int width)
{
	bNodeSocketType *stype = ntreeGetSocketType(sock->type);
	if (stype->buttonfunc)
		stype->buttonfunc(C, block, ntree, node, sock, name, x, y, width);
	else
		node_socket_button_label(C, block, ntree, node, sock, name, x, y, width);
}

static void node_draw_output_default(const bContext *C, uiBlock *block,
                                     bNodeTree *UNUSED(ntree), bNode *node, bNodeSocket *sock,
                                     const char *name, int UNUSED(x), int UNUSED(y), int UNUSED(width))
{
	SpaceNode *snode = CTX_wm_space_node(C);
	float slen;
	int ofs = 0;
	UI_ThemeColor(TH_TEXT);
	slen= snode->aspect*UI_GetStringWidth(name);
	while (slen > node->width) {
		ofs++;
		slen= snode->aspect*UI_GetStringWidth(name+ofs);
	}
	uiDefBut(block, LABEL, 0, name+ofs, (short)(sock->locx-15.0f-slen), (short)(sock->locy-9.0f), 
             (short)(node->width-NODE_DY), NODE_DY,  NULL, 0, 0, 0, 0, "");
}

/* ****************** BASE DRAW FUNCTIONS FOR NEW OPERATOR NODES ***************** */

#if 0 /* UNUSED */
static void node_draw_socket_new(bNodeSocket *sock, float size)
{
	float x=sock->locx, y=sock->locy;
	
	/* 16 values of sin function */
	static float si[16] = {
		0.00000000f, 0.39435585f, 0.72479278f,0.93775213f,
		0.99871650f,0.89780453f,0.65137248f,0.29936312f,
		-0.10116832f,-0.48530196f,-0.79077573f,-0.96807711f,
		-0.98846832f,-0.84864425f,-0.57126821f,-0.20129852f
	};
	/* 16 values of cos function */
	static float co[16] ={
		1.00000000f,0.91895781f,0.68896691f,0.34730525f,
		-0.05064916f,-0.44039415f,-0.75875812f,-0.95413925f,
		-0.99486932f,-0.87434661f,-0.61210598f,-0.25065253f,
		0.15142777f,0.52896401f,0.82076344f,0.97952994f,
	};
	int a;
	
	glColor3ub(180, 180, 180);
	
	glBegin(GL_POLYGON);
	for (a=0; a<16; a++)
		glVertex2f(x+size*si[a], y+size*co[a]);
	glEnd();
	
	glColor4ub(0, 0, 0, 150);
	glEnable(GL_BLEND);
	glEnable(GL_LINE_SMOOTH);
	glBegin(GL_LINE_LOOP);
	for (a=0; a<16; a++)
		glVertex2f(x+size*si[a], y+size*co[a]);
	glEnd();
	glDisable(GL_LINE_SMOOTH);
	glDisable(GL_BLEND);
}
#endif

/* ****************** BUTTON CALLBACKS FOR ALL TREES ***************** */

static void node_buts_value(uiLayout *layout, bContext *UNUSED(C), PointerRNA *ptr)
{
	PointerRNA sockptr;
	PropertyRNA *prop;
	
	/* first socket stores value */
	prop = RNA_struct_find_property(ptr, "outputs");
	RNA_property_collection_lookup_int(ptr, prop, 0, &sockptr);
	
	uiItemR(layout, &sockptr, "default_value", 0, "", ICON_NONE);
}

static void node_buts_rgb(uiLayout *layout, bContext *UNUSED(C), PointerRNA *ptr)
{
	uiLayout *col;
	PointerRNA sockptr;
	PropertyRNA *prop;
	
	/* first socket stores value */
	prop = RNA_struct_find_property(ptr, "outputs");
	RNA_property_collection_lookup_int(ptr, prop, 0, &sockptr);
	
	col = uiLayoutColumn(layout, 0);
	uiTemplateColorWheel(col, &sockptr, "default_value", 1, 0, 0, 0);
	uiItemR(col, &sockptr, "default_value", 0, "", ICON_NONE);
}

static void node_buts_mix_rgb(uiLayout *layout, bContext *UNUSED(C), PointerRNA *ptr)
{	
	uiLayout *row;

	bNodeTree *ntree= (bNodeTree*)ptr->id.data;

	row= uiLayoutRow(layout, 1);
	uiItemR(row, ptr, "blend_type", 0, "", ICON_NONE);
	if (ntree->type == NTREE_COMPOSIT)
		uiItemR(row, ptr, "use_alpha", 0, "", ICON_IMAGE_RGB_ALPHA);
}

static void node_buts_time(uiLayout *layout, bContext *UNUSED(C), PointerRNA *ptr)
{
	uiLayout *row;
#if 0
	/* XXX no context access here .. */
	bNode *node= ptr->data;
	CurveMapping *cumap= node->storage;
	
	if (cumap) {
		cumap->flag |= CUMA_DRAW_CFRA;
		if (node->custom1<node->custom2)
			cumap->sample[0]= (float)(CFRA - node->custom1)/(float)(node->custom2-node->custom1);
	}
#endif

	uiTemplateCurveMapping(layout, ptr, "curve", 's', 0, 0);

	row= uiLayoutRow(layout, 1);
	uiItemR(row, ptr, "frame_start", 0, "Sta", ICON_NONE);
	uiItemR(row, ptr, "frame_end", 0, "End", ICON_NONE);
}

static void node_buts_colorramp(uiLayout *layout, bContext *UNUSED(C), PointerRNA *ptr)
{
	uiTemplateColorRamp(layout, ptr, "color_ramp", 0);
}

static void node_buts_curvevec(uiLayout *layout, bContext *UNUSED(C), PointerRNA *ptr)
{
	uiTemplateCurveMapping(layout, ptr, "mapping", 'v', 0, 0);
}

static float *_sample_col= NULL;	// bad bad, 2.5 will do better?
#if 0
static void node_curvemap_sample(float *col)
{
	_sample_col= col;
}
#endif

static void node_buts_curvecol(uiLayout *layout, bContext *UNUSED(C), PointerRNA *ptr)
{
	bNode *node= ptr->data;
	CurveMapping *cumap= node->storage;

	if (_sample_col) {
		cumap->flag |= CUMA_DRAW_SAMPLE;
		copy_v3_v3(cumap->sample, _sample_col);
	}
	else 
		cumap->flag &= ~CUMA_DRAW_SAMPLE;

	uiTemplateCurveMapping(layout, ptr, "mapping", 'c', 0, 0);
}

static void node_normal_cb(bContext *C, void *ntree_v, void *node_v)
{
	Main *bmain = CTX_data_main(C);

	ED_node_generic_update(bmain, ntree_v, node_v);
	WM_event_add_notifier(C, NC_NODE|NA_EDITED, ntree_v);
}

static void node_buts_normal(uiLayout *layout, bContext *UNUSED(C), PointerRNA *ptr)
{
	uiBlock *block= uiLayoutAbsoluteBlock(layout);
	bNodeTree *ntree= ptr->id.data;
	bNode *node= ptr->data;
	rctf *butr= &node->butr;
	bNodeSocket *sock= node->outputs.first;		/* first socket stores normal */
	float *nor= ((bNodeSocketValueVector*)sock->default_value)->value;
	uiBut *bt;
	
	bt= uiDefButF(block, BUT_NORMAL, B_NODE_EXEC, "", 
	              (short)butr->xmin, (short)butr->xmin,
	              butr->xmax-butr->xmin, butr->xmax-butr->xmin,
	              nor, 0.0f, 1.0f, 0, 0, "");
	uiButSetFunc(bt, node_normal_cb, ntree, node);
}
#if 0 // not used in 2.5x yet
static void node_browse_tex_cb(bContext *C, void *ntree_v, void *node_v)
{
	Main *bmain= CTX_data_main(C);
	bNodeTree *ntree= ntree_v;
	bNode *node= node_v;
	Tex *tex;
	
	if (node->menunr<1) return;
	
	if (node->id) {
		node->id->us--;
		node->id= NULL;
	}
	tex= BLI_findlink(&bmain->tex, node->menunr-1);

	node->id= &tex->id;
	id_us_plus(node->id);
	BLI_strncpy(node->name, node->id->name+2, sizeof(node->name));
	
	nodeSetActive(ntree, node);
	
	if ( ntree->type == NTREE_TEXTURE )
		ntreeTexCheckCyclics(ntree);
	
	// allqueue(REDRAWBUTSSHADING, 0);
	// allqueue(REDRAWNODE, 0);
	NodeTagChanged(ntree, node); 
	
	node->menunr= 0;
}
#endif
static void node_dynamic_update_cb(bContext *C, void *UNUSED(ntree_v), void *node_v)
{
	Main *bmain= CTX_data_main(C);
	Material *ma;
	bNode *node= (bNode *)node_v;
	ID *id= node->id;
	int error= 0;

	if (BTST(node->custom1, NODE_DYNAMIC_ERROR)) error= 1;

	/* Users only have to press the "update" button in one pynode
	 * and we also update all others sharing the same script */
	for (ma= bmain->mat.first; ma; ma= ma->id.next) {
		if (ma->nodetree) {
			bNode *nd;
			for (nd= ma->nodetree->nodes.first; nd; nd= nd->next) {
				if ((nd->type == NODE_DYNAMIC) && (nd->id == id)) {
					nd->custom1= 0;
					nd->custom1= BSET(nd->custom1, NODE_DYNAMIC_REPARSE);
					nd->menunr= 0;
					if (error)
						nd->custom1= BSET(nd->custom1, NODE_DYNAMIC_ERROR);
				}
			}
		}
	}

	// allqueue(REDRAWBUTSSHADING, 0);
	// allqueue(REDRAWNODE, 0);
	// XXX BIF_preview_changed(ID_MA);
}

static void node_buts_texture(uiLayout *layout, bContext *UNUSED(C), PointerRNA *ptr)
{
	bNode *node= ptr->data;

	short multi = (
		node->id &&
		((Tex*)node->id)->use_nodes &&
		(node->type != CMP_NODE_TEXTURE) &&
		(node->type != TEX_NODE_TEXTURE)
	);
	
	uiItemR(layout, ptr, "texture", 0, "", ICON_NONE);
	
	if (multi) {
		/* Number Drawing not optimal here, better have a list*/
		uiItemR(layout, ptr, "node_output", 0, "", ICON_NONE);
	}
}

static void node_buts_math(uiLayout *layout, bContext *UNUSED(C), PointerRNA *ptr)
{ 
	uiItemR(layout, ptr, "operation", 0, "", ICON_NONE);
}

static int node_resize_area_default(bNode *node, int x, int y)
{
	if (node->flag & NODE_HIDDEN) {
		rctf totr= node->totr;
		/* right part of node */
		totr.xmin = node->totr.xmax-20.0f;
		return BLI_in_rctf(&totr, x, y);
	}
	else {
		/* rect we're interested in is just the bottom right corner */
		rctf totr= node->totr;
		/* bottom right corner */
		totr.xmin = totr.xmax-10.0f;
		totr.ymax = totr.ymin+10.0f;
		return BLI_in_rctf(&totr, x, y);
	}
}

/* ****************** BUTTON CALLBACKS FOR COMMON NODES ***************** */

/* width of socket columns in group display */
#define NODE_GROUP_FRAME		120

/* based on settings in node, sets drawing rect info. each redraw! */
/* note: this assumes only 1 group at a time is drawn (linked data) */
/* in node->totr the entire boundbox for the group is stored */
static void node_update_group(const bContext *C, bNodeTree *ntree, bNode *gnode)
{
	if (!(gnode->flag & NODE_GROUP_EDIT)) {
		node_update_default(C, ntree, gnode);
	}
	else {
		bNodeTree *ngroup= (bNodeTree *)gnode->id;
		bNode *node;
		bNodeSocket *sock, *gsock;
		float locx, locy;
		rctf *rect= &gnode->totr;
		float node_group_frame= U.dpi*NODE_GROUP_FRAME/72;
		float group_header= 26*U.dpi/72;
		int counter;
		int dy;
		
		/* get "global" coords */
		nodeSpaceCoords(gnode, &locx, &locy);
		
		/* center them, is a bit of abuse of locx and locy though */
		node_update_nodetree(C, ngroup, locx, locy);
		
		rect->xmin = rect->xmax = locx;
		rect->ymin = rect->ymax = locy;
		
		counter= 1;
		for (node= ngroup->nodes.first; node; node= node->next) {
			if (counter) {
				*rect= node->totr;
				counter= 0;
			}
			else
				BLI_union_rctf(rect, &node->totr);
		}
		
		/* add some room for links to group sockets */
		rect->xmin -= 4*NODE_DY;
		rect->xmax += 4*NODE_DY;
		rect->ymin-= NODE_DY;
		rect->ymax+= NODE_DY;
		
		/* input sockets */
		dy = 0.5f*(rect->ymin+rect->ymax) + NODE_DY*(BLI_countlist(&gnode->inputs)-1);
		gsock=ngroup->inputs.first;
		sock=gnode->inputs.first;
		while (gsock || sock) {
			while (sock && !sock->groupsock) {
				sock->locx = rect->xmin - node_group_frame;
				sock->locy = dy;

				/* prevent long socket lists from growing out of the group box */
				if (dy-3*NODE_DYS < rect->ymin)
					rect->ymin = dy-3*NODE_DYS;
				if (dy+3*NODE_DYS > rect->ymax)
					rect->ymax = dy+3*NODE_DYS;
				dy -= 2*NODE_DY;
				
				sock = sock->next;
			}
			while (gsock && (!sock || sock->groupsock!=gsock)) {
				gsock->locx = rect->xmin;
				gsock->locy = dy;
				
				/* prevent long socket lists from growing out of the group box */
				if (dy-3*NODE_DYS < rect->ymin)
					rect->ymin = dy-3*NODE_DYS;
				if (dy+3*NODE_DYS > rect->ymax)
					rect->ymax = dy+3*NODE_DYS;
				dy -= 2*NODE_DY;
				
				gsock = gsock->next;
			}
			while (sock && gsock && sock->groupsock==gsock) {
				gsock->locx = rect->xmin;
				sock->locx = rect->xmin - node_group_frame;
				sock->locy = gsock->locy = dy;
				
				/* prevent long socket lists from growing out of the group box */
				if (dy-3*NODE_DYS < rect->ymin)
					rect->ymin = dy-3*NODE_DYS;
				if (dy+3*NODE_DYS > rect->ymax)
					rect->ymax = dy+3*NODE_DYS;
				dy -= 2*NODE_DY;
				
				sock = sock->next;
				gsock = gsock->next;
			}
		}
		
		/* output sockets */
		dy = 0.5f*(rect->ymin+rect->ymax) + NODE_DY*(BLI_countlist(&gnode->outputs)-1);
		gsock=ngroup->outputs.first;
		sock=gnode->outputs.first;
		while (gsock || sock) {
			while (sock && !sock->groupsock) {
				sock->locx = rect->xmax + node_group_frame;
				sock->locy = dy - NODE_DYS;
				
				/* prevent long socket lists from growing out of the group box */
				if (dy-3*NODE_DYS < rect->ymin)
					rect->ymin = dy-3*NODE_DYS;
				if (dy+3*NODE_DYS > rect->ymax)
					rect->ymax = dy+3*NODE_DYS;
				dy -= 2*NODE_DY;
				
				sock = sock->next;
			}
			while (gsock && (!sock || sock->groupsock!=gsock)) {
				gsock->locx = rect->xmax;
				gsock->locy = dy - NODE_DYS;
				
				/* prevent long socket lists from growing out of the group box */
				if (dy-3*NODE_DYS < rect->ymin)
					rect->ymin = dy-3*NODE_DYS;
				if (dy+3*NODE_DYS > rect->ymax)
					rect->ymax = dy+3*NODE_DYS;
				dy -= 2*NODE_DY;
				
				gsock = gsock->next;
			}
			while (sock && gsock && sock->groupsock==gsock) {
				gsock->locx = rect->xmax;
				sock->locx = rect->xmax + node_group_frame;
				sock->locy = gsock->locy = dy - NODE_DYS;
				
				/* prevent long socket lists from growing out of the group box */
				if (dy-3*NODE_DYS < rect->ymin)
					rect->ymin = dy-3*NODE_DYS;
				if (dy+3*NODE_DYS > rect->ymax)
					rect->ymax = dy+3*NODE_DYS;
				dy -= 2*NODE_DY;
				
				sock = sock->next;
				gsock = gsock->next;
			}
		}
		
		/* Set the block bounds to clip mouse events from underlying nodes.
		 * Add margin for header and input/output columns.
		 */
		uiExplicitBoundsBlock(gnode->block,
							  rect->xmin - node_group_frame,
							  rect->ymin,
							  rect->xmax + node_group_frame,
							  rect->ymax + group_header);
	}
}

static void update_group_input_cb(bContext *UNUSED(C), void *UNUSED(snode_v), void *ngroup_v)
{
	bNodeTree *ngroup= (bNodeTree*)ngroup_v;
	
	ngroup->update |= NTREE_UPDATE_GROUP_IN;
	ntreeUpdateTree(ngroup);
}

static void update_group_output_cb(bContext *UNUSED(C), void *UNUSED(snode_v), void *ngroup_v)
{
	bNodeTree *ngroup= (bNodeTree*)ngroup_v;
	
	ngroup->update |= NTREE_UPDATE_GROUP_OUT;
	ntreeUpdateTree(ngroup);
}

static void draw_group_socket_name(SpaceNode *snode, bNode *gnode, bNodeSocket *sock, int in_out, float xoffset, float yoffset)
{
	bNodeTree *ngroup= (bNodeTree*)gnode->id;
	uiBut *bt;
	
	if (sock->flag & SOCK_DYNAMIC) {
		bt = uiDefBut(gnode->block, TEX, 0, "", 
					  sock->locx+xoffset, sock->locy+1+yoffset, 72, NODE_DY,
					  sock->name, 0, sizeof(sock->name), 0, 0, "");
		if (in_out==SOCK_IN)
			uiButSetFunc(bt, update_group_input_cb, snode, ngroup);
		else
			uiButSetFunc(bt, update_group_output_cb, snode, ngroup);
	}
	else {
		uiDefBut(gnode->block, LABEL, 0, sock->name,
		         sock->locx+xoffset, sock->locy+1+yoffset, 72, NODE_DY,
		         NULL, 0, sizeof(sock->name), 0, 0, "");
	}
}

static void draw_group_socket(const bContext *C, SpaceNode *snode, bNodeTree *ntree, bNode *gnode, bNodeSocket *sock, bNodeSocket *gsock, int index, int in_out)
{
	bNodeTree *ngroup= (bNodeTree*)gnode->id;
	bNodeSocketType *stype= ntreeGetSocketType(gsock ? gsock->type : sock->type);
	uiBut *bt;
	float offset;
	int draw_value;
	float node_group_frame= U.dpi*NODE_GROUP_FRAME/72;
	float socket_size= NODE_SOCKSIZE*U.dpi/72;
	float arrowbutw= 0.8f*UI_UNIT_X;
	/* layout stuff for buttons on group left frame */
	float colw= 0.6f*node_group_frame;
	float col1= 6 - node_group_frame;
	float col2= col1 + colw+6;
	float col3= - arrowbutw - 6;
	/* layout stuff for buttons on group right frame */
	float cor1= 6;
	float cor2= cor1 + arrowbutw + 6;
	float cor3= cor2 + arrowbutw + 6;
	
	/* node and group socket circles */
	if (sock)
		node_socket_circle_draw(ntree, sock, socket_size);
	if (gsock)
		node_socket_circle_draw(ngroup, gsock, socket_size);
	
	/* socket name */
	offset = (in_out==SOCK_IN ? col1 : cor3);
	if (!gsock)
		offset += (in_out==SOCK_IN ? node_group_frame : -node_group_frame);
	
	/* draw both name and value button if:
	 * 1) input: not internal
	 * 2) output: (node type uses const outputs) and (group output is unlinked)
	 */
	draw_value = 0;
	switch (in_out) {
	case SOCK_IN:
		draw_value = !(gsock && (gsock->flag & SOCK_INTERNAL));
		break;
	case SOCK_OUT:
		if (gnode->typeinfo->flag & NODE_CONST_OUTPUT)
			draw_value = !(gsock && gsock->link);
		break;
	}
	if (draw_value) {
		/* both name and value buttons */
		if (gsock) {
			draw_group_socket_name(snode, gnode, gsock, in_out, offset, 0);
			if (stype->buttonfunc)
				stype->buttonfunc(C, gnode->block, ngroup, NULL, gsock, "", gsock->locx+offset, gsock->locy-NODE_DY, colw);
		}
		else {
			draw_group_socket_name(snode, gnode, sock, in_out, offset, 0);
			if (stype->buttonfunc)
				stype->buttonfunc(C, gnode->block, ngroup, NULL, sock, "", sock->locx+offset, sock->locy-NODE_DY, colw);
		}
	}
	else {
		/* only name, no value button */
		if (gsock)
			draw_group_socket_name(snode, gnode, gsock, in_out, offset, -NODE_DYS);
		else
			draw_group_socket_name(snode, gnode, sock, in_out, offset, -NODE_DYS);
	}
	
	if (gsock && (gsock->flag & SOCK_DYNAMIC)) {
		/* up/down buttons */
		offset = (in_out==SOCK_IN ? col2 : cor2);
		uiBlockSetDirection(gnode->block, UI_TOP);
		uiBlockBeginAlign(gnode->block);
		bt = uiDefIconButO(gnode->block, BUT, "NODE_OT_group_socket_move_up", 0, ICON_TRIA_UP,
						   gsock->locx+offset, gsock->locy, arrowbutw, arrowbutw, "");
		if (!gsock->prev || !(gsock->prev->flag & SOCK_DYNAMIC))
			uiButSetFlag(bt, UI_BUT_DISABLED);
		RNA_int_set(uiButGetOperatorPtrRNA(bt), "index", index);
		RNA_enum_set(uiButGetOperatorPtrRNA(bt), "in_out", in_out);
		bt = uiDefIconButO(gnode->block, BUT, "NODE_OT_group_socket_move_down", 0, ICON_TRIA_DOWN,
						   gsock->locx+offset, gsock->locy-arrowbutw, arrowbutw, arrowbutw, "");
		if (!gsock->next || !(gsock->next->flag & SOCK_DYNAMIC))
			uiButSetFlag(bt, UI_BUT_DISABLED);
		RNA_int_set(uiButGetOperatorPtrRNA(bt), "index", index);
		RNA_enum_set(uiButGetOperatorPtrRNA(bt), "in_out", in_out);
		uiBlockEndAlign(gnode->block);
		uiBlockSetDirection(gnode->block, 0);
		
		/* remove button */
		offset = (in_out==SOCK_IN ? col3 : cor1);
		uiBlockSetEmboss(gnode->block, UI_EMBOSSN);
		bt = uiDefIconButO(gnode->block, BUT, "NODE_OT_group_socket_remove", 0, ICON_X,
						   gsock->locx+offset, gsock->locy-0.5f*arrowbutw, arrowbutw, arrowbutw, "");
		RNA_int_set(uiButGetOperatorPtrRNA(bt), "index", index);
		RNA_enum_set(uiButGetOperatorPtrRNA(bt), "in_out", in_out);
		uiBlockSetEmboss(gnode->block, UI_EMBOSS);
	}
}

/* groups are, on creation, centered around 0,0 */
static void node_draw_group(const bContext *C, ARegion *ar, SpaceNode *snode, bNodeTree *ntree, bNode *gnode)
{
	if (!(gnode->flag & NODE_GROUP_EDIT)) {
		node_draw_default(C, ar, snode, ntree, gnode);
	}
	else {
		bNodeTree *ngroup= (bNodeTree *)gnode->id;
		bNodeSocket *sock, *gsock;
		uiLayout *layout;
		PointerRNA ptr;
		rctf rect= gnode->totr;
		float node_group_frame= U.dpi*NODE_GROUP_FRAME/72;
		float group_header= 26*U.dpi/72;
		
		int index;
		
		/* backdrop header */
		glEnable(GL_BLEND);
		uiSetRoundBox(UI_CNR_TOP_LEFT | UI_CNR_TOP_RIGHT);
		UI_ThemeColorShadeAlpha(TH_NODE_GROUP, 0, -70);
		uiDrawBox(GL_POLYGON, rect.xmin-node_group_frame, rect.ymax, rect.xmax+node_group_frame, rect.ymax+group_header, BASIS_RAD);
		
		/* backdrop body */
		UI_ThemeColorShadeAlpha(TH_BACK, -8, -70);
		uiSetRoundBox(UI_CNR_NONE);
		uiDrawBox(GL_POLYGON, rect.xmin, rect.ymin, rect.xmax, rect.ymax, BASIS_RAD);
	
		/* input column */
		UI_ThemeColorShadeAlpha(TH_BACK, 10, -50);
		uiSetRoundBox(UI_CNR_BOTTOM_LEFT);
		uiDrawBox(GL_POLYGON, rect.xmin-node_group_frame, rect.ymin, rect.xmin, rect.ymax, BASIS_RAD);
	
		/* output column */
		UI_ThemeColorShadeAlpha(TH_BACK, 10, -50);
		uiSetRoundBox(UI_CNR_BOTTOM_RIGHT);
		uiDrawBox(GL_POLYGON, rect.xmax, rect.ymin, rect.xmax+node_group_frame, rect.ymax, BASIS_RAD);
	
		/* input column separator */
		glColor4ub(200, 200, 200, 140);
		glBegin(GL_LINES);
		glVertex2f(rect.xmin, rect.ymin);
		glVertex2f(rect.xmin, rect.ymax);
		glEnd();
	
		/* output column separator */
		glColor4ub(200, 200, 200, 140);
		glBegin(GL_LINES);
		glVertex2f(rect.xmax, rect.ymin);
		glVertex2f(rect.xmax, rect.ymax);
		glEnd();
	
		/* group node outline */
		uiSetRoundBox(UI_CNR_ALL);
		glColor4ub(200, 200, 200, 140);
		glEnable(GL_LINE_SMOOTH);
		uiDrawBox(GL_LINE_LOOP, rect.xmin-node_group_frame, rect.ymin, rect.xmax+node_group_frame, rect.ymax+group_header, BASIS_RAD);
		glDisable(GL_LINE_SMOOTH);
		glDisable(GL_BLEND);
		
		/* backdrop title */
		UI_ThemeColor(TH_TEXT_HI);
	
		layout = uiBlockLayout(gnode->block, UI_LAYOUT_VERTICAL, UI_LAYOUT_PANEL, (short)(rect.xmin+15), (short)(rect.ymax+group_header),
		                       MIN2((int)(rect.xmax - rect.xmin-18.0f), node_group_frame+20), group_header, UI_GetStyle());
		RNA_pointer_create(&ntree->id, &RNA_Node, gnode, &ptr);
		uiTemplateIDBrowse(layout, (bContext*)C, &ptr, "node_tree", NULL, NULL, NULL);
		uiBlockLayoutResolve(gnode->block, NULL, NULL);
	
		/* draw the internal tree nodes and links */
		node_draw_nodetree(C, ar, snode, ngroup);
	
		/* group sockets */
		gsock=ngroup->inputs.first;
		sock=gnode->inputs.first;
		index = 0;
		while (gsock || sock) {
			while (sock && !sock->groupsock) {
				draw_group_socket(C, snode, ntree, gnode, sock, NULL, index, SOCK_IN);
				sock = sock->next;
			}
			while (gsock && (!sock || sock->groupsock!=gsock)) {
				draw_group_socket(C, snode, ntree, gnode, NULL, gsock, index, SOCK_IN);
				gsock = gsock->next;
				++index;
			}
			while (sock && gsock && sock->groupsock==gsock) {
				draw_group_socket(C, snode, ntree, gnode, sock, gsock, index, SOCK_IN);
				sock = sock->next;
				gsock = gsock->next;
				++index;
			}
		}
		gsock=ngroup->outputs.first;
		sock=gnode->outputs.first;
		index = 0;
		while (gsock || sock) {
			while (sock && !sock->groupsock) {
				draw_group_socket(C, snode, ntree, gnode, sock, NULL, index, SOCK_OUT);
				sock = sock->next;
			}
			while (gsock && (!sock || sock->groupsock!=gsock)) {
				draw_group_socket(C, snode, ntree, gnode, NULL, gsock, index, SOCK_OUT);
				gsock = gsock->next;
				++index;
			}
			while (sock && gsock && sock->groupsock==gsock) {
				draw_group_socket(C, snode, ntree, gnode, sock, gsock, index, SOCK_OUT);
				sock = sock->next;
				gsock = gsock->next;
				++index;
			}
		}
		
		uiEndBlock(C, gnode->block);
		uiDrawBlock(C, gnode->block);
		gnode->block= NULL;
	}
}

void node_uifunc_group(uiLayout *layout, bContext *C, PointerRNA *ptr)
{
	uiTemplateIDBrowse(layout, C, ptr, "node_tree", NULL, NULL, NULL);
}

static void node_common_buts_whileloop(uiLayout *layout, bContext *UNUSED(C), PointerRNA *ptr)
{
	uiItemR(layout, ptr, "max_iterations", 0, NULL, 0);
}

static void node_update_frame(const bContext *UNUSED(C), bNodeTree *UNUSED(ntree), bNode *node)
{
	float locx, locy;

	/* get "global" coords */
	nodeSpaceCoords(node, &locx, &locy);

	node->prvr.xmin = locx + NODE_DYS;
	node->prvr.xmax = locx + node->width- NODE_DYS;

	node->totr.xmin = locx;
	node->totr.xmax = locx + node->width;
	node->totr.ymax = locy;
	node->totr.ymin = locy - node->height;
}

static void node_common_set_butfunc(bNodeType *ntype)
{
	switch (ntype->type) {
		case NODE_GROUP:
			ntype->uifunc= node_uifunc_group;
			ntype->drawfunc= node_draw_group;
			ntype->drawupdatefunc= node_update_group;
			break;
		case NODE_FORLOOP:
//			ntype->uifunc= node_common_buts_group;
			ntype->drawfunc= node_draw_group;
			ntype->drawupdatefunc= node_update_group;
			break;
		case NODE_WHILELOOP:
			ntype->uifunc= node_common_buts_whileloop;
			ntype->drawfunc= node_draw_group;
			ntype->drawupdatefunc= node_update_group;
			break;
		case NODE_FRAME:
			ntype->drawupdatefunc= node_update_frame;
			break;
	}
}

/* ****************** BUTTON CALLBACKS FOR SHADER NODES ***************** */

static void node_browse_text_cb(bContext *C, void *ntree_v, void *node_v)
{
	Main *bmain= CTX_data_main(C);
	bNodeTree *ntree= ntree_v;
	bNode *node= node_v;
	/* ID *oldid; */ /* UNUSED */
	
	if (node->menunr<1) return;
	
	if (node->id) {
		node->id->us--;
	}
	/* oldid= node->id; */ /* UNUSED */
	node->id= BLI_findlink(&bmain->text, node->menunr-1);
	id_us_plus(node->id);
	BLI_strncpy(node->name, node->id->name+2, sizeof(node->name));

	node->custom1= BSET(node->custom1, NODE_DYNAMIC_NEW);
	
	nodeSetActive(ntree, node);

	// allqueue(REDRAWBUTSSHADING, 0);
	// allqueue(REDRAWNODE, 0);

	node->menunr= 0;
}

static void node_shader_buts_material(uiLayout *layout, bContext *C, PointerRNA *ptr)
{
	bNode *node= ptr->data;
	uiLayout *col;
	
	uiTemplateID(layout, C, ptr, "material", "MATERIAL_OT_new", NULL, NULL);
	
	if (!node->id) return;
	
	col= uiLayoutColumn(layout, 0);
	uiItemR(col, ptr, "use_diffuse", 0, NULL, ICON_NONE);
	uiItemR(col, ptr, "use_specular", 0, NULL, ICON_NONE);
	uiItemR(col, ptr, "invert_normal", 0, NULL, ICON_NONE);
}

static void node_shader_buts_mapping(uiLayout *layout, bContext *UNUSED(C), PointerRNA *ptr)
{
	uiLayout *row;
	
	uiItemL(layout, "Location:", ICON_NONE);
	row= uiLayoutRow(layout, 1);
	uiItemR(row, ptr, "translation", 0, "", ICON_NONE);
	
	uiItemL(layout, "Rotation:", ICON_NONE);
	row= uiLayoutRow(layout, 1);
	uiItemR(row, ptr, "rotation", 0, "", ICON_NONE);
	
	uiItemL(layout, "Scale:", ICON_NONE);
	row= uiLayoutRow(layout, 1);
	uiItemR(row, ptr, "scale", 0, "", ICON_NONE);
	
	row= uiLayoutRow(layout, 1);
	uiItemR(row, ptr, "use_min", 0, "Min", ICON_NONE);
	uiItemR(row, ptr, "min", 0, "", ICON_NONE);
	
	row= uiLayoutRow(layout, 1);
	uiItemR(row, ptr, "use_max", 0, "Max", ICON_NONE);
	uiItemR(row, ptr, "max", 0, "", ICON_NONE);
}

static void node_shader_buts_vect_math(uiLayout *layout, bContext *UNUSED(C), PointerRNA *ptr)
{ 
	uiItemR(layout, ptr, "operation", 0, "", ICON_NONE);
}

static void node_shader_buts_geometry(uiLayout *layout, bContext *C, PointerRNA *ptr)
{
	PointerRNA obptr= CTX_data_pointer_get(C, "active_object");
	uiLayout *col;

	col= uiLayoutColumn(layout, 0);

	if (obptr.data && RNA_enum_get(&obptr, "type") == OB_MESH) {
		PointerRNA dataptr= RNA_pointer_get(&obptr, "data");

		uiItemPointerR(col, ptr, "uv_layer", &dataptr, "uv_textures", "", ICON_NONE);
		uiItemPointerR(col, ptr, "color_layer", &dataptr, "vertex_colors", "", ICON_NONE);
	}
	else {
		uiItemR(col, ptr, "uv_layer", 0, "UV", ICON_NONE);
		uiItemR(col, ptr, "color_layer", 0, "VCol", ICON_NONE);
	}
}

static void node_shader_buts_attribute(uiLayout *layout, bContext *UNUSED(C), PointerRNA *ptr)
{
	uiItemR(layout, ptr, "attribute_name", 0, "Name", ICON_NONE);
}

static void node_shader_buts_tex_image(uiLayout *layout, bContext *C, PointerRNA *ptr)
{
	uiTemplateID(layout, C, ptr, "image", NULL, "IMAGE_OT_open", NULL);
	uiItemR(layout, ptr, "color_space", 0, "", ICON_NONE);
}


static void node_shader_buts_tex_environment(uiLayout *layout, bContext *C, PointerRNA *ptr)
{
	uiTemplateID(layout, C, ptr, "image", NULL, "IMAGE_OT_open", NULL);
	uiItemR(layout, ptr, "color_space", 0, "", ICON_NONE);
	uiItemR(layout, ptr, "projection", 0, "", ICON_NONE);
}

static void node_shader_buts_tex_sky(uiLayout *layout, bContext *UNUSED(C), PointerRNA *ptr)
{
	uiItemR(layout, ptr, "sun_direction", 0, "", ICON_NONE);
	uiItemR(layout, ptr, "turbidity", 0, NULL, ICON_NONE);
}

static void node_shader_buts_tex_gradient(uiLayout *layout, bContext *UNUSED(C), PointerRNA *ptr)
{
	uiItemR(layout, ptr, "gradient_type", 0, "", ICON_NONE);
}

static void node_shader_buts_tex_magic(uiLayout *layout, bContext *UNUSED(C), PointerRNA *ptr)
{
	uiItemR(layout, ptr, "turbulence_depth", 0, NULL, ICON_NONE);
}

static void node_shader_buts_tex_wave(uiLayout *layout, bContext *UNUSED(C), PointerRNA *ptr)
{
	uiItemR(layout, ptr, "wave_type", 0, "", ICON_NONE);
}

static void node_shader_buts_tex_musgrave(uiLayout *layout, bContext *UNUSED(C), PointerRNA *ptr)
{
	uiItemR(layout, ptr, "musgrave_type", 0, "", ICON_NONE);
}

static void node_shader_buts_tex_voronoi(uiLayout *layout, bContext *UNUSED(C), PointerRNA *ptr)
{
	uiItemR(layout, ptr, "coloring", 0, "", ICON_NONE);
}

static void node_shader_buts_glossy(uiLayout *layout, bContext *UNUSED(C), PointerRNA *ptr)
{
	uiItemR(layout, ptr, "distribution", 0, "", ICON_NONE);
}

static void node_shader_buts_dynamic(uiLayout *layout, bContext *C, PointerRNA *ptr)
{ 
	Main *bmain= CTX_data_main(C);
	uiBlock *block= uiLayoutAbsoluteBlock(layout);
	bNode *node= ptr->data;
	bNodeTree *ntree= ptr->id.data;
	rctf *butr= &node->butr;
	uiBut *bt;
	// XXX SpaceNode *snode= curarea->spacedata.first;
	short dy= (short)butr->ymin;
	int xoff=0;

	/* B_NODE_EXEC is handled in butspace.c do_node_buts */
	if (!node->id) {
			const char *strp;
			IDnames_to_pupstring(&strp, NULL, "", &(bmain->text), NULL, NULL);
			node->menunr= 0;
			bt= uiDefButS(block, MENU, B_NODE_EXEC/*+node->nr*/, strp, 
							butr->xmin, dy, 19, 19, 
							&node->menunr, 0, 0, 0, 0, "Browses existing choices");
			uiButSetFunc(bt, node_browse_text_cb, ntree, node);
			xoff=19;
			if (strp) MEM_freeN((void *)strp);
	}
	else {
		bt = uiDefBut(block, BUT, B_NOP, "Update",
				butr->xmin+xoff, butr->ymin+20, 50, 19,
				&node->menunr, 0.0, 19.0, 0, 0, "Refresh this node (and all others that use the same script)");
		uiButSetFunc(bt, node_dynamic_update_cb, ntree, node);

		if (BTST(node->custom1, NODE_DYNAMIC_ERROR)) {
			// UI_ThemeColor(TH_REDALERT);
			// XXX ui_rasterpos_safe(butr->xmin + xoff, butr->ymin + 5, snode->aspect);
			// XXX snode_drawstring(snode, "Error! Check console...", butr->xmax - butr->xmin);
			;
		}
	}
}

/* only once called */
static void node_shader_set_butfunc(bNodeType *ntype)
{
	ntype->uifuncbut = NULL;
	switch (ntype->type) {
		/* case NODE_GROUP:	 note, typeinfo for group is generated... see "XXX ugly hack" */

		case SH_NODE_MATERIAL:
		case SH_NODE_MATERIAL_EXT:
			ntype->uifunc= node_shader_buts_material;
			break;
		case SH_NODE_TEXTURE:
			ntype->uifunc= node_buts_texture;
			break;
		case SH_NODE_NORMAL:
			ntype->uifunc= node_buts_normal;
			break;
		case SH_NODE_CURVE_VEC:
			ntype->uifunc= node_buts_curvevec;
			break;
		case SH_NODE_CURVE_RGB:
			ntype->uifunc= node_buts_curvecol;
			break;
		case SH_NODE_MAPPING:
			ntype->uifunc= node_shader_buts_mapping;
			break;
		case SH_NODE_VALUE:
			ntype->uifunc= node_buts_value;
			break;
		case SH_NODE_RGB:
			ntype->uifunc= node_buts_rgb;
			break;
		case SH_NODE_MIX_RGB:
			ntype->uifunc= node_buts_mix_rgb;
			break;
		case SH_NODE_VALTORGB:
			ntype->uifunc= node_buts_colorramp;
			break;
		case SH_NODE_MATH: 
			ntype->uifunc= node_buts_math;
			break; 
		case SH_NODE_VECT_MATH: 
			ntype->uifunc= node_shader_buts_vect_math;
			break; 
		case SH_NODE_GEOMETRY:
			ntype->uifunc= node_shader_buts_geometry;
			break;
		case SH_NODE_ATTRIBUTE:
			ntype->uifunc= node_shader_buts_attribute;
			break;
		case SH_NODE_TEX_SKY:
			ntype->uifunc= node_shader_buts_tex_sky;
			break;
		case SH_NODE_TEX_IMAGE:
			ntype->uifunc= node_shader_buts_tex_image;
			break;
		case SH_NODE_TEX_ENVIRONMENT:
			ntype->uifunc= node_shader_buts_tex_environment;
			break;
		case SH_NODE_TEX_GRADIENT:
			ntype->uifunc= node_shader_buts_tex_gradient;
			break;
		case SH_NODE_TEX_MAGIC:
			ntype->uifunc= node_shader_buts_tex_magic;
			break;
		case SH_NODE_TEX_WAVE:
			ntype->uifunc= node_shader_buts_tex_wave;
			break;
		case SH_NODE_TEX_MUSGRAVE:
			ntype->uifunc= node_shader_buts_tex_musgrave;
			break;
		case SH_NODE_TEX_VORONOI:
			ntype->uifunc= node_shader_buts_tex_voronoi;
			break;
		case SH_NODE_BSDF_GLOSSY:
		case SH_NODE_BSDF_GLASS:
			ntype->uifunc= node_shader_buts_glossy;
			break;
		case NODE_DYNAMIC:
			ntype->uifunc= node_shader_buts_dynamic;
			break;
	}
		if (ntype->uifuncbut == NULL) ntype->uifuncbut = ntype->uifunc;
}

/* ****************** BUTTON CALLBACKS FOR COMPOSITE NODES ***************** */

static void node_composit_buts_image(uiLayout *layout, bContext *C, PointerRNA *ptr)
{
	uiLayout *col;
	bNode *node= ptr->data;
	PointerRNA imaptr;
	PropertyRNA *prop;
	int source;
	
	uiTemplateID(layout, C, ptr, "image", NULL, "IMAGE_OT_open", NULL);
	
	if (!node->id) return;
	
	prop = RNA_struct_find_property(ptr, "image");
	if (!prop || RNA_property_type(prop) != PROP_POINTER) return;
	imaptr= RNA_property_pointer_get(ptr, prop);
	
	col= uiLayoutColumn(layout, 0);
	
	uiItemR(col, &imaptr, "source", 0, NULL, ICON_NONE);
	
	source= RNA_enum_get(&imaptr, "source");

	if (source == IMA_SRC_SEQUENCE) {
		/* don't use iuser->framenr directly because it may not be updated if auto-refresh is off */
		Scene *scene= CTX_data_scene(C);
		ImageUser *iuser= node->storage;
		char numstr[32];
		const int framenr= BKE_image_user_frame_get(iuser, CFRA, 0);
		BLI_snprintf(numstr, sizeof(numstr), "Frame: %d", framenr);
		uiItemL(layout, numstr, ICON_NONE);
	}

	if (ELEM(source, IMA_SRC_SEQUENCE, IMA_SRC_MOVIE)) {
		col= uiLayoutColumn(layout, 1);
		uiItemR(col, ptr, "frame_duration", 0, NULL, ICON_NONE);
		uiItemR(col, ptr, "frame_start", 0, NULL, ICON_NONE);
		uiItemR(col, ptr, "frame_offset", 0, NULL, ICON_NONE);
		uiItemR(col, ptr, "use_cyclic", 0, NULL, ICON_NONE);
		uiItemR(col, ptr, "use_auto_refresh", UI_ITEM_R_ICON_ONLY, NULL, ICON_NONE);
	}

	col= uiLayoutColumn(layout, 0);

	if (RNA_enum_get(&imaptr, "type")== IMA_TYPE_MULTILAYER)
		uiItemR(col, ptr, "layer", 0, NULL, ICON_NONE);
}

static void node_composit_buts_renderlayers(uiLayout *layout, bContext *C, PointerRNA *ptr)
{
	bNode *node= ptr->data;
	uiLayout *col, *row;
	PointerRNA op_ptr;
	PointerRNA scn_ptr;
	PropertyRNA *prop;
	const char *layer_name;
	char scene_name[MAX_ID_NAME-2];
	wmOperatorType *ot = WM_operatortype_find("RENDER_OT_render", 1);

	BLI_assert(ot != 0);

	uiTemplateID(layout, C, ptr, "scene", NULL, NULL, NULL);
	
	if (!node->id) return;

	col= uiLayoutColumn(layout, 0);
	row = uiLayoutRow(col, 0);
	uiItemR(row, ptr, "layer", 0, "", ICON_NONE);
	
	prop = RNA_struct_find_property(ptr, "layer");
	if (!(RNA_property_enum_identifier(C, ptr, prop, RNA_property_enum_get(ptr, prop), &layer_name)))
		return;
	
	scn_ptr = RNA_pointer_get(ptr, "scene");
	RNA_string_get(&scn_ptr, "name", scene_name);
	
	WM_operator_properties_create_ptr(&op_ptr, ot);
	RNA_string_set(&op_ptr, "layer", layer_name);
	RNA_string_set(&op_ptr, "scene", scene_name);
	uiItemFullO_ptr(row, ot, "", ICON_RENDER_STILL, op_ptr.data, WM_OP_INVOKE_DEFAULT, 0);

}


static void node_composit_buts_blur(uiLayout *layout, bContext *UNUSED(C), PointerRNA *ptr)
{
	uiLayout *col, *row;
	
	col= uiLayoutColumn(layout, 0);
	
	uiItemR(col, ptr, "filter_type", 0, "", ICON_NONE);
	if (RNA_enum_get(ptr, "filter_type")!= R_FILTER_FAST_GAUSS) {
		uiItemR(col, ptr, "use_bokeh", 0, NULL, ICON_NONE);
		uiItemR(col, ptr, "use_gamma_correction", 0, NULL, ICON_NONE);
	}
	
	uiItemR(col, ptr, "use_relative", 0, NULL, ICON_NONE);
	
	if (RNA_boolean_get(ptr, "use_relative")) {
		uiItemL(col, "Aspect Correction", 0);
		row= uiLayoutRow(layout, 1);
		uiItemR(row, ptr, "aspect_correction", UI_ITEM_R_EXPAND, NULL, 0);
		
		col= uiLayoutColumn(layout, 1);
		uiItemR(col, ptr, "factor_x", 0, "X", ICON_NONE);
		uiItemR(col, ptr, "factor_y", 0, "Y", ICON_NONE);
	}
	else {
		col= uiLayoutColumn(layout, 1);
		uiItemR(col, ptr, "size_x", 0, "X", ICON_NONE);
		uiItemR(col, ptr, "size_y", 0, "Y", ICON_NONE);
	}
}

static void node_composit_buts_dblur(uiLayout *layout, bContext *UNUSED(C), PointerRNA *ptr)
{
	uiLayout *col;
	
	uiItemR(layout, ptr, "iterations", 0, NULL, ICON_NONE);
	uiItemR(layout, ptr, "use_wrap", 0, NULL, ICON_NONE);
	
	col= uiLayoutColumn(layout, 1);
	uiItemL(col, "Center:", ICON_NONE);
	uiItemR(col, ptr, "center_x", 0, "X", ICON_NONE);
	uiItemR(col, ptr, "center_y", 0, "Y", ICON_NONE);
	
	uiItemS(layout);
	
	col= uiLayoutColumn(layout, 1);
	uiItemR(col, ptr, "distance", 0, NULL, ICON_NONE);
	uiItemR(col, ptr, "angle", 0, NULL, ICON_NONE);
	
	uiItemS(layout);
	
	uiItemR(layout, ptr, "spin", 0, NULL, ICON_NONE);
	uiItemR(layout, ptr, "zoom", 0, NULL, ICON_NONE);
}

static void node_composit_buts_bilateralblur(uiLayout *layout, bContext *UNUSED(C), PointerRNA *ptr)
{	
	uiLayout *col;
	
	col= uiLayoutColumn(layout, 1);
	uiItemR(col, ptr, "iterations", 0, NULL, ICON_NONE);
	uiItemR(col, ptr, "sigma_color", 0, NULL, ICON_NONE);
	uiItemR(col, ptr, "sigma_space", 0, NULL, ICON_NONE);
}

static void node_composit_buts_defocus(uiLayout *layout, bContext *UNUSED(C), PointerRNA *ptr)
{
	uiLayout *sub, *col;
	
	col= uiLayoutColumn(layout, 0);
	uiItemL(col, "Bokeh Type:", ICON_NONE);
	uiItemR(col, ptr, "bokeh", 0, "", ICON_NONE);
	uiItemR(col, ptr, "angle", 0, NULL, ICON_NONE);

	uiItemR(layout, ptr, "use_gamma_correction", 0, NULL, ICON_NONE);

	col = uiLayoutColumn(layout, 0);
	uiLayoutSetActive(col, RNA_boolean_get(ptr, "use_zbuffer") == TRUE);
	uiItemR(col, ptr, "f_stop", 0, NULL, ICON_NONE);

	uiItemR(layout, ptr, "blur_max", 0, NULL, ICON_NONE);
	uiItemR(layout, ptr, "threshold", 0, NULL, ICON_NONE);

	col = uiLayoutColumn(layout, 0);
	uiItemR(col, ptr, "use_preview", 0, NULL, ICON_NONE);
	sub = uiLayoutColumn(col, 0);
	uiLayoutSetActive(sub, RNA_boolean_get(ptr, "use_preview"));
	uiItemR(sub, ptr, "samples", 0, NULL, ICON_NONE);
	
	col = uiLayoutColumn(layout, 0);
	uiItemR(col, ptr, "use_zbuffer", 0, NULL, ICON_NONE);
	sub = uiLayoutColumn(col, 0);
	uiLayoutSetActive(sub, RNA_boolean_get(ptr, "use_zbuffer") == FALSE);
	uiItemR(sub, ptr, "z_scale", 0, NULL, ICON_NONE);
}

/* qdn: glare node */
static void node_composit_buts_glare(uiLayout *layout, bContext *UNUSED(C), PointerRNA *ptr)
{	
	uiItemR(layout, ptr, "glare_type", 0, "", ICON_NONE);
	uiItemR(layout, ptr, "quality", 0, "", ICON_NONE);

	if (RNA_enum_get(ptr, "glare_type")!= 1) {
		uiItemR(layout, ptr, "iterations", 0, NULL, ICON_NONE);
	
		if (RNA_enum_get(ptr, "glare_type")!= 0) 
			uiItemR(layout, ptr, "color_modulation", UI_ITEM_R_SLIDER, NULL, ICON_NONE);
	}
	
	uiItemR(layout, ptr, "mix", 0, NULL, ICON_NONE);
	uiItemR(layout, ptr, "threshold", 0, NULL, ICON_NONE);

	if (RNA_enum_get(ptr, "glare_type")== 2) {
		uiItemR(layout, ptr, "streaks", 0, NULL, ICON_NONE);
		uiItemR(layout, ptr, "angle_offset", 0, NULL, ICON_NONE);
	}
	if (RNA_enum_get(ptr, "glare_type")== 0 || RNA_enum_get(ptr, "glare_type")== 2) {
		uiItemR(layout, ptr, "fade", UI_ITEM_R_SLIDER, NULL, ICON_NONE);
		
		if (RNA_enum_get(ptr, "glare_type")== 0) 
			uiItemR(layout, ptr, "use_rotate_45", 0, NULL, ICON_NONE);
	}
	if (RNA_enum_get(ptr, "glare_type")== 1) {
		uiItemR(layout, ptr, "size", 0, NULL, ICON_NONE);
	}
}

static void node_composit_buts_tonemap(uiLayout *layout, bContext *UNUSED(C), PointerRNA *ptr)
{	
	uiLayout *col;

	col = uiLayoutColumn(layout, 0);
	uiItemR(col, ptr, "tonemap_type", 0, "", ICON_NONE);
	if (RNA_enum_get(ptr, "tonemap_type")== 0) {
		uiItemR(col, ptr, "key", UI_ITEM_R_SLIDER, NULL, ICON_NONE);
		uiItemR(col, ptr, "offset", 0, NULL, ICON_NONE);
		uiItemR(col, ptr, "gamma", 0, NULL, ICON_NONE);
	}
	else {
		uiItemR(col, ptr, "intensity", 0, NULL, ICON_NONE);
		uiItemR(col, ptr, "contrast", UI_ITEM_R_SLIDER, NULL, ICON_NONE);
		uiItemR(col, ptr, "adaptation", UI_ITEM_R_SLIDER, NULL, ICON_NONE);
		uiItemR(col, ptr, "correction", UI_ITEM_R_SLIDER, NULL, ICON_NONE);
	}
}

static void node_composit_buts_lensdist(uiLayout *layout, bContext *UNUSED(C), PointerRNA *ptr)
{
	uiLayout *col;

	col= uiLayoutColumn(layout, 0);
	uiItemR(col, ptr, "use_projector", 0, NULL, ICON_NONE);

	col = uiLayoutColumn(col, 0);
	uiLayoutSetActive(col, RNA_boolean_get(ptr, "use_projector") == FALSE);
	uiItemR(col, ptr, "use_jitter", 0, NULL, ICON_NONE);
	uiItemR(col, ptr, "use_fit", 0, NULL, ICON_NONE);
}

static void node_composit_buts_vecblur(uiLayout *layout, bContext *UNUSED(C), PointerRNA *ptr)
{
	uiLayout *col;
	
	col= uiLayoutColumn(layout, 0);
	uiItemR(col, ptr, "samples", 0, NULL, ICON_NONE);
	uiItemR(col, ptr, "factor", 0, "Blur", ICON_NONE);
	
	col= uiLayoutColumn(layout, 1);
	uiItemL(col, "Speed:", ICON_NONE);
	uiItemR(col, ptr, "speed_min", 0, "Min", ICON_NONE);
	uiItemR(col, ptr, "speed_max", 0, "Max", ICON_NONE);

	uiItemR(layout, ptr, "use_curved", 0, NULL, ICON_NONE);
}

static void node_composit_buts_filter(uiLayout *layout, bContext *UNUSED(C), PointerRNA *ptr)
{
	uiItemR(layout, ptr, "filter_type", 0, "", ICON_NONE);
}

static void node_composit_buts_flip(uiLayout *layout, bContext *UNUSED(C), PointerRNA *ptr)
{
	uiItemR(layout, ptr, "axis", 0, "", ICON_NONE);
}

static void node_composit_buts_crop(uiLayout *layout, bContext *UNUSED(C), PointerRNA *ptr)
{
	uiLayout *col;

	uiItemR(layout, ptr, "use_crop_size", 0, NULL, ICON_NONE);
	uiItemR(layout, ptr, "relative", 0, NULL, ICON_NONE);

	col= uiLayoutColumn(layout, 1);
	if (RNA_boolean_get(ptr, "relative")) {
		uiItemR(col, ptr, "rel_min_x", 0, "Left", ICON_NONE);
		uiItemR(col, ptr, "rel_max_x", 0, "Right", ICON_NONE);
		uiItemR(col, ptr, "rel_min_y", 0, "Up", ICON_NONE);
		uiItemR(col, ptr, "rel_max_y", 0, "Down", ICON_NONE);
	}
	else {
		uiItemR(col, ptr, "min_x", 0, "Left", ICON_NONE);
		uiItemR(col, ptr, "max_x", 0, "Right", ICON_NONE);
		uiItemR(col, ptr, "min_y", 0, "Up", ICON_NONE);
		uiItemR(col, ptr, "max_y", 0, "Down", ICON_NONE);
	}
}

static void node_composit_buts_splitviewer(uiLayout *layout, bContext *UNUSED(C), PointerRNA *ptr)
{
	uiLayout *row, *col;
	
	col= uiLayoutColumn(layout, 0);
	row= uiLayoutRow(col, 0);
	uiItemR(row, ptr, "axis", UI_ITEM_R_EXPAND, NULL, ICON_NONE);
	uiItemR(col, ptr, "factor", 0, NULL, ICON_NONE);
}

static void node_composit_buts_double_edge_mask(uiLayout *layout, bContext *UNUSED(C), PointerRNA *ptr)
{
	uiLayout *col;

	col= uiLayoutColumn(layout, 0);

	uiItemL(col, "Inner Edge:", ICON_NONE);
	uiItemR(col, ptr, "inner_mode", 0, "", ICON_NONE);
	uiItemL(col, "Buffer Edge:", ICON_NONE);
	uiItemR(col, ptr, "edge_mode", 0, "", ICON_NONE);
}

static void node_composit_buts_map_value(uiLayout *layout, bContext *UNUSED(C), PointerRNA *ptr)
{
	uiLayout *sub, *col;
	
	col = uiLayoutColumn(layout, 1);
	uiItemR(col, ptr, "offset", 0, NULL, ICON_NONE);
	uiItemR(col, ptr, "size", 0, NULL, ICON_NONE);
	
	col = uiLayoutColumn(layout, 1);
	uiItemR(col, ptr, "use_min", 0, NULL, ICON_NONE);
	sub = uiLayoutColumn(col, 0);
	uiLayoutSetActive(sub, RNA_boolean_get(ptr, "use_min"));
	uiItemR(sub, ptr, "min", 0, "", ICON_NONE);
	
	col = uiLayoutColumn(layout, 1);
	uiItemR(col, ptr, "use_max", 0, NULL, ICON_NONE);
	sub = uiLayoutColumn(col, 0);
	uiLayoutSetActive(sub, RNA_boolean_get(ptr, "use_max"));
	uiItemR(sub, ptr, "max", 0, "", ICON_NONE);
}

static void node_composit_buts_alphaover(uiLayout *layout, bContext *UNUSED(C), PointerRNA *ptr)
{	
	uiLayout *col;
	
	col = uiLayoutColumn(layout, 1);
	uiItemR(col, ptr, "use_premultiply", 0, NULL, ICON_NONE);
	uiItemR(col, ptr, "premul", 0, NULL, ICON_NONE);
}

static void node_composit_buts_zcombine(uiLayout *layout, bContext *UNUSED(C), PointerRNA *ptr)
{	
	uiLayout *col;
	
	col = uiLayoutColumn(layout, 1);
	uiItemR(col, ptr, "use_alpha", 0, NULL, ICON_NONE);
}


static void node_composit_buts_hue_sat(uiLayout *layout, bContext *UNUSED(C), PointerRNA *ptr)
{
	uiLayout *col;
	
	col = uiLayoutColumn(layout, 0);
	uiItemR(col, ptr, "color_hue", UI_ITEM_R_SLIDER, NULL, ICON_NONE);
	uiItemR(col, ptr, "color_saturation", UI_ITEM_R_SLIDER, NULL, ICON_NONE);
	uiItemR(col, ptr, "color_value", UI_ITEM_R_SLIDER, NULL, ICON_NONE);
}

static void node_composit_buts_dilateerode(uiLayout *layout, bContext *UNUSED(C), PointerRNA *ptr)
{
	uiItemR(layout, ptr, "distance", 0, NULL, ICON_NONE);
}

static void node_composit_buts_diff_matte(uiLayout *layout, bContext *UNUSED(C), PointerRNA *ptr)
{
	uiLayout *col;
	
	col = uiLayoutColumn(layout, 1);
	uiItemR(col, ptr, "tolerance", UI_ITEM_R_SLIDER, NULL, ICON_NONE);
	uiItemR(col, ptr, "falloff", UI_ITEM_R_SLIDER, NULL, ICON_NONE);
}

static void node_composit_buts_distance_matte(uiLayout *layout, bContext *UNUSED(C), PointerRNA *ptr)
{
	uiLayout *col, *row;
	
	col = uiLayoutColumn(layout, 1);
   
	uiItemL(layout, "Color Space:", ICON_NONE);
	row= uiLayoutRow(layout, 0);
	uiItemR(row, ptr, "channel", UI_ITEM_R_EXPAND, NULL, ICON_NONE);

	uiItemR(col, ptr, "tolerance", UI_ITEM_R_SLIDER, NULL, ICON_NONE);
	uiItemR(col, ptr, "falloff", UI_ITEM_R_SLIDER, NULL, ICON_NONE);
}

static void node_composit_buts_color_spill(uiLayout *layout, bContext *UNUSED(C), PointerRNA *ptr)
{
	uiLayout *row, *col;
	
	uiItemL(layout, "Despill Channel:", ICON_NONE);
	row = uiLayoutRow(layout, 0);
	uiItemR(row, ptr, "channel", UI_ITEM_R_EXPAND, NULL, ICON_NONE);

	col= uiLayoutColumn(layout, 0);
	uiItemR(col, ptr, "limit_method", 0, NULL, ICON_NONE);

	if (RNA_enum_get(ptr, "limit_method")==0) {
		uiItemL(col, "Limiting Channel:", ICON_NONE);
		row=uiLayoutRow(col, 0);
		uiItemR(row, ptr, "limit_channel", UI_ITEM_R_EXPAND, NULL, ICON_NONE);
	}

	uiItemR(col, ptr, "ratio", UI_ITEM_R_SLIDER, NULL, ICON_NONE);
	uiItemR(col, ptr, "use_unspill", 0, NULL, ICON_NONE);
	if (RNA_boolean_get(ptr, "use_unspill") == TRUE) {
		uiItemR(col, ptr, "unspill_red", UI_ITEM_R_SLIDER, NULL, ICON_NONE);
		uiItemR(col, ptr, "unspill_green", UI_ITEM_R_SLIDER, NULL, ICON_NONE);
		uiItemR(col, ptr, "unspill_blue", UI_ITEM_R_SLIDER, NULL, ICON_NONE);
	}
}

static void node_composit_buts_chroma_matte(uiLayout *layout, bContext *UNUSED(C), PointerRNA *ptr)
{
	uiLayout *col;
	
	col= uiLayoutColumn(layout, 0);
	uiItemR(col, ptr, "tolerance", 0, NULL, ICON_NONE);
	uiItemR(col, ptr, "threshold", 0, NULL, ICON_NONE);
	
	col= uiLayoutColumn(layout, 1);
	/*uiItemR(col, ptr, "lift", UI_ITEM_R_SLIDER, NULL, ICON_NONE);  Removed for now */
	uiItemR(col, ptr, "gain", UI_ITEM_R_SLIDER, NULL, ICON_NONE);
	/*uiItemR(col, ptr, "shadow_adjust", UI_ITEM_R_SLIDER, NULL, ICON_NONE);  Removed for now*/
}

static void node_composit_buts_color_matte(uiLayout *layout, bContext *UNUSED(C), PointerRNA *ptr)
{
	uiLayout *col;
	
	col= uiLayoutColumn(layout, 1);
	uiItemR(col, ptr, "color_hue", UI_ITEM_R_SLIDER, NULL, ICON_NONE);
	uiItemR(col, ptr, "color_saturation", UI_ITEM_R_SLIDER, NULL, ICON_NONE);
	uiItemR(col, ptr, "color_value", UI_ITEM_R_SLIDER, NULL, ICON_NONE);
}

static void node_composit_buts_channel_matte(uiLayout *layout, bContext *UNUSED(C), PointerRNA *ptr)
{	
	uiLayout *col, *row;

	uiItemL(layout, "Color Space:", ICON_NONE);
	row= uiLayoutRow(layout, 0);
	uiItemR(row, ptr, "color_space", UI_ITEM_R_EXPAND, NULL, ICON_NONE);

	col=uiLayoutColumn(layout, 0);
	uiItemL(col, "Key Channel:", ICON_NONE);
	row= uiLayoutRow(col, 0);
	uiItemR(row, ptr, "matte_channel", UI_ITEM_R_EXPAND, NULL, ICON_NONE);

	col = uiLayoutColumn(layout, 0);

	uiItemR(col, ptr, "limit_method", 0, NULL, ICON_NONE);
	if (RNA_enum_get(ptr, "limit_method")==0) {
		uiItemL(col, "Limiting Channel:", ICON_NONE);
		row=uiLayoutRow(col, 0);
		uiItemR(row, ptr, "limit_channel", UI_ITEM_R_EXPAND, NULL, ICON_NONE);
	}

	uiItemR(col, ptr, "limit_max", UI_ITEM_R_SLIDER, NULL, ICON_NONE);
	uiItemR(col, ptr, "limit_min", UI_ITEM_R_SLIDER, NULL, ICON_NONE);
}

static void node_composit_buts_luma_matte(uiLayout *layout, bContext *UNUSED(C), PointerRNA *ptr)
{
	uiLayout *col;
	
	col= uiLayoutColumn(layout, 1);
	uiItemR(col, ptr, "limit_max", UI_ITEM_R_SLIDER, NULL, ICON_NONE);
	uiItemR(col, ptr, "limit_min", UI_ITEM_R_SLIDER, NULL, ICON_NONE);
}

static void node_composit_buts_map_uv(uiLayout *layout, bContext *UNUSED(C), PointerRNA *ptr)
{
	uiItemR(layout, ptr, "alpha", 0, NULL, ICON_NONE);
}

static void node_composit_buts_id_mask(uiLayout *layout, bContext *UNUSED(C), PointerRNA *ptr)
{
	uiItemR(layout, ptr, "index", 0, NULL, ICON_NONE);
	uiItemR(layout, ptr, "use_smooth_mask", 0, NULL, ICON_NONE);
}

/* draw function for file output node sockets, displays only sub-path and format, no value button */
static void node_draw_input_file_output(const bContext *C, uiBlock *block,
                                         bNodeTree *ntree, bNode *node, bNodeSocket *sock,
                                         const char *UNUSED(name), int x, int y, int width)
{
	uiLayout *layout, *row;
	PointerRNA nodeptr, inputptr, imfptr;
	int imtype;
	int rx, ry;
	RNA_pointer_create(&ntree->id, &RNA_Node, node, &nodeptr);
	
	layout = uiBlockLayout(block, UI_LAYOUT_VERTICAL, UI_LAYOUT_PANEL, x, y+NODE_DY, width, 20, UI_GetStyle());
	row = uiLayoutRow(layout, 0);
	
	imfptr = RNA_pointer_get(&nodeptr, "format");
	imtype = RNA_enum_get(&imfptr, "file_format");
	if (imtype == R_IMF_IMTYPE_MULTILAYER) {
		NodeImageMultiFileSocket *input = sock->storage;
		RNA_pointer_create(&ntree->id, &RNA_NodeOutputFileSlotLayer, input, &inputptr);
		
		uiItemL(row, input->layer, 0);
	}
	else {
		NodeImageMultiFileSocket *input = sock->storage;
		PropertyRNA *imtype_prop;
		const char *imtype_name;
		RNA_pointer_create(&ntree->id, &RNA_NodeOutputFileSlotFile, input, &inputptr);
		
		uiItemL(row, input->path, 0);
		
		if (!RNA_boolean_get(&inputptr, "use_node_format"))
			imfptr = RNA_pointer_get(&inputptr, "format");
		
		imtype_prop = RNA_struct_find_property(&imfptr, "file_format");
		RNA_property_enum_name((bContext*)C, &imfptr, imtype_prop, RNA_property_enum_get(&imfptr, imtype_prop), &imtype_name);
		uiBlockSetEmboss(block, UI_EMBOSSP);
		uiItemL(row, imtype_name, 0);
		uiBlockSetEmboss(block, UI_EMBOSSN);
	}
	
	uiBlockLayoutResolve(block, &rx, &ry);
}
static void node_composit_buts_file_output(uiLayout *layout, bContext *UNUSED(C), PointerRNA *ptr)
{
	PointerRNA imfptr = RNA_pointer_get(ptr, "format");
	int multilayer = (RNA_enum_get(&imfptr, "file_format") == R_IMF_IMTYPE_MULTILAYER);
	
	if (multilayer)
		uiItemL(layout, "Path:", 0);
	else
		uiItemL(layout, "Base Path:", 0);
	uiItemR(layout, ptr, "base_path", 0, "", ICON_NONE);
}
static void node_composit_buts_file_output_details(uiLayout *layout, bContext *C, PointerRNA *ptr)
{
	PointerRNA imfptr = RNA_pointer_get(ptr, "format");
	PointerRNA active_input_ptr, op_ptr;
	uiLayout *row;
	int active_index;
	int multilayer = (RNA_enum_get(&imfptr, "file_format") == R_IMF_IMTYPE_MULTILAYER);
	
	node_composit_buts_file_output(layout, C, ptr);
	uiTemplateImageSettings(layout, &imfptr);
	
	uiItemS(layout);
	
	uiItemO(layout, "Add Input", ICON_ZOOMIN, "NODE_OT_output_file_add_socket");
	
	active_index = RNA_int_get(ptr, "active_input_index");
	/* using different collection properties if multilayer format is enabled */
	if (multilayer) {
		uiTemplateList(layout, C, ptr, "layer_slots", ptr, "active_input_index", NULL, 0, 0, 0);
		RNA_property_collection_lookup_int(ptr, RNA_struct_find_property(ptr, "layer_slots"), active_index, &active_input_ptr);
	}
	else {
		uiTemplateList(layout, C, ptr, "file_slots", ptr, "active_input_index", NULL, 0, 0, 0);
		RNA_property_collection_lookup_int(ptr, RNA_struct_find_property(ptr, "file_slots"), active_index, &active_input_ptr);
	}
	/* XXX collection lookup does not return the ID part of the pointer, setting this manually here */
	active_input_ptr.id.data = ptr->id.data;
	
	row = uiLayoutRow(layout, 1);
	op_ptr = uiItemFullO(row, "NODE_OT_output_file_move_active_socket", "", ICON_TRIA_UP, NULL, WM_OP_INVOKE_DEFAULT, UI_ITEM_O_RETURN_PROPS);
	RNA_enum_set(&op_ptr, "direction", 1);
	op_ptr = uiItemFullO(row, "NODE_OT_output_file_move_active_socket", "", ICON_TRIA_DOWN, NULL, WM_OP_INVOKE_DEFAULT, UI_ITEM_O_RETURN_PROPS);
	RNA_enum_set(&op_ptr, "direction", 2);
	
	if (active_input_ptr.data) {
		if (multilayer) {
			uiLayout *row, *col;
			col = uiLayoutColumn(layout, 1);
			
			uiItemL(col, "Layer:", 0);
			row = uiLayoutRow(col, 0);
			uiItemR(row, &active_input_ptr, "name", 0, "", 0);
			uiItemFullO(row, "NODE_OT_output_file_remove_active_socket", "", ICON_X, NULL, WM_OP_EXEC_DEFAULT, UI_ITEM_R_ICON_ONLY);
		}
		else {
			uiLayout *row, *col;
			col = uiLayoutColumn(layout, 1);
			
			uiItemL(col, "File Path:", 0);
			row = uiLayoutRow(col, 0);
			uiItemR(row, &active_input_ptr, "path", 0, "", 0);
			uiItemFullO(row, "NODE_OT_output_file_remove_active_socket", "", ICON_X, NULL, WM_OP_EXEC_DEFAULT, UI_ITEM_R_ICON_ONLY);
			
			/* format details for individual files */
			imfptr = RNA_pointer_get(&active_input_ptr, "format");
			
			col = uiLayoutColumn(layout, 1);
			uiItemL(col, "Format:", 0);
			uiItemR(col, &active_input_ptr, "use_node_format", 0, NULL, 0);
			
			col= uiLayoutColumn(layout, 0);
			uiLayoutSetActive(col, RNA_boolean_get(&active_input_ptr, "use_node_format") == FALSE);
			uiTemplateImageSettings(col, &imfptr);
		}
	}
}

static void node_composit_buts_scale(uiLayout *layout, bContext *UNUSED(C), PointerRNA *ptr)
{
	uiItemR(layout, ptr, "space", 0, "", ICON_NONE);
}

static void node_composit_buts_rotate(uiLayout *layout, bContext *UNUSED(C), PointerRNA *ptr)
{
	uiItemR(layout, ptr, "filter_type", 0, "", ICON_NONE);
}

static void node_composit_buts_invert(uiLayout *layout, bContext *UNUSED(C), PointerRNA *ptr)
{
	uiLayout *col;
	
	col= uiLayoutColumn(layout, 0);
	uiItemR(col, ptr, "invert_rgb", 0, NULL, ICON_NONE);
	uiItemR(col, ptr, "invert_alpha", 0, NULL, ICON_NONE);
}

static void node_composit_buts_premulkey(uiLayout *layout, bContext *UNUSED(C), PointerRNA *ptr)
{
	uiItemR(layout, ptr, "mapping", 0, "", ICON_NONE);
}

static void node_composit_buts_view_levels(uiLayout *layout, bContext *UNUSED(C), PointerRNA *ptr)
{
	uiItemR(layout, ptr, "channel", UI_ITEM_R_EXPAND, NULL, ICON_NONE);
}

static void node_composit_buts_colorbalance(uiLayout *layout, bContext *UNUSED(C), PointerRNA *ptr)
{
	uiLayout *split, *col, *row;
	
	uiItemR(layout, ptr, "correction_method", 0, NULL, ICON_NONE);
	
	if (RNA_enum_get(ptr, "correction_method")== 0) {
	
		split = uiLayoutSplit(layout, 0, 0);
		col = uiLayoutColumn(split, 0);
		uiTemplateColorWheel(col, ptr, "lift", 1, 1, 0, 1);
		row = uiLayoutRow(col, 0);
		uiItemR(row, ptr, "lift", 0, NULL, ICON_NONE);
		
		col = uiLayoutColumn(split, 0);
		uiTemplateColorWheel(col, ptr, "gamma", 1, 1, 1, 1);
		row = uiLayoutRow(col, 0);
		uiItemR(row, ptr, "gamma", 0, NULL, ICON_NONE);
		
		col = uiLayoutColumn(split, 0);
		uiTemplateColorWheel(col, ptr, "gain", 1, 1, 1, 1);
		row = uiLayoutRow(col, 0);
		uiItemR(row, ptr, "gain", 0, NULL, ICON_NONE);

	}
	else {
		
		split = uiLayoutSplit(layout, 0, 0);
		col = uiLayoutColumn(split, 0);
		uiTemplateColorWheel(col, ptr, "offset", 1, 1, 0, 1);
		row = uiLayoutRow(col, 0);
		uiItemR(row, ptr, "offset", 0, NULL, ICON_NONE);
		
		col = uiLayoutColumn(split, 0);
		uiTemplateColorWheel(col, ptr, "power", 1, 1, 0, 1);
		row = uiLayoutRow(col, 0);
		uiItemR(row, ptr, "power", 0, NULL, ICON_NONE);
		
		col = uiLayoutColumn(split, 0);
		uiTemplateColorWheel(col, ptr, "slope", 1, 1, 0, 1);
		row = uiLayoutRow(col, 0);
		uiItemR(row, ptr, "slope", 0, NULL, ICON_NONE);
	}

}
static void node_composit_buts_colorbalance_but(uiLayout *layout, bContext *UNUSED(C), PointerRNA *ptr)
{
	uiItemR(layout, ptr, "correction_method", 0, NULL, ICON_NONE);

	if (RNA_enum_get(ptr, "correction_method")== 0) {

	uiTemplateColorWheel(layout, ptr, "lift", 1, 1, 0, 1);
		uiItemR(layout, ptr, "lift", 0, NULL, ICON_NONE);

		uiTemplateColorWheel(layout, ptr, "gamma", 1, 1, 1, 1);
		uiItemR(layout, ptr, "gamma", 0, NULL, ICON_NONE);

		uiTemplateColorWheel(layout, ptr, "gain", 1, 1, 1, 1);
		uiItemR(layout, ptr, "gain", 0, NULL, ICON_NONE);
	}
	else {
		uiTemplateColorWheel(layout, ptr, "offset", 1, 1, 0, 1);
		uiItemR(layout, ptr, "offset", 0, NULL, ICON_NONE);

		uiTemplateColorWheel(layout, ptr, "power", 1, 1, 0, 1);
		uiItemR(layout, ptr, "power", 0, NULL, ICON_NONE);

		uiTemplateColorWheel(layout, ptr, "slope", 1, 1, 0, 1);
		uiItemR(layout, ptr, "slope", 0, NULL, ICON_NONE);
	}
}


static void node_composit_buts_huecorrect(uiLayout *layout, bContext *UNUSED(C), PointerRNA *ptr)
{
	uiTemplateCurveMapping(layout, ptr, "mapping", 'h', 0, 0);
}

static void node_composit_buts_ycc(uiLayout *layout, bContext *UNUSED(C), PointerRNA *ptr)
{ 
	uiItemR(layout, ptr, "mode", 0, "", ICON_NONE);
}

static void node_composit_buts_movieclip(uiLayout *layout, bContext *C, PointerRNA *ptr)
{
	uiTemplateID(layout, C, ptr, "clip", NULL, "CLIP_OT_open", NULL);
}

static void node_composit_buts_stabilize2d(uiLayout *layout, bContext *C, PointerRNA *ptr)
{
	bNode *node= ptr->data;

	uiTemplateID(layout, C, ptr, "clip", NULL, "CLIP_OT_open", NULL);

	if (!node->id)
		return;

	uiItemR(layout, ptr, "filter_type", 0, "", 0);
}

static void node_composit_buts_transform(uiLayout *layout, bContext *UNUSED(C), PointerRNA *ptr)
{
	uiItemR(layout, ptr, "filter_type", 0, "", 0);
}

static void node_composit_buts_moviedistortion(uiLayout *layout, bContext *C, PointerRNA *ptr)
{
	bNode *node= ptr->data;

	uiTemplateID(layout, C, ptr, "clip", NULL, "CLIP_OT_open", NULL);

	if (!node->id)
		return;

	uiItemR(layout, ptr, "distortion_type", 0, "", 0);
}

static void node_composit_buts_colorcorrection(uiLayout *layout, bContext *UNUSED(C), PointerRNA *ptr)
{
	uiLayout *row;
	
	row = uiLayoutRow(layout, 0);
	uiItemR(row, ptr, "red", 0, NULL, ICON_NONE);
	uiItemR(row, ptr, "green", 0, NULL, ICON_NONE);
	uiItemR(row, ptr, "blue", 0, NULL, ICON_NONE);

	row = uiLayoutRow(layout, 0);
	uiItemR(row, ptr, "midtones_start", UI_ITEM_R_SLIDER, NULL, ICON_NONE);
	uiItemR(row, ptr, "midtones_end", UI_ITEM_R_SLIDER, NULL, ICON_NONE);

	row = uiLayoutRow(layout, 0);
	uiItemR(row, ptr, "master_saturation", UI_ITEM_R_SLIDER, NULL, ICON_NONE);
	uiItemR(row, ptr, "master_contrast", UI_ITEM_R_SLIDER, NULL, ICON_NONE);
	uiItemR(row, ptr, "master_gamma", UI_ITEM_R_SLIDER, NULL, ICON_NONE);
	uiItemR(row, ptr, "master_gain", UI_ITEM_R_SLIDER, NULL, ICON_NONE);
	uiItemR(row, ptr, "master_lift", UI_ITEM_R_SLIDER, NULL, ICON_NONE);

	row = uiLayoutRow(layout, 0);
	uiItemL(row, "Saturation", 0);
	uiItemL(row, "Contrast", 0);
	uiItemL(row, "Gamma", 0);
	uiItemL(row, "Gain", 0);
	uiItemL(row, "Lift", 0);

	row = uiLayoutRow(layout, 0);
	uiItemR(row, ptr, "highlights_saturation", UI_ITEM_R_SLIDER, NULL, ICON_NONE);
	uiItemR(row, ptr, "highlights_contrast", UI_ITEM_R_SLIDER, NULL, ICON_NONE);
	uiItemR(row, ptr, "highlights_gamma", UI_ITEM_R_SLIDER, NULL, ICON_NONE);
	uiItemR(row, ptr, "highlights_gain", UI_ITEM_R_SLIDER, NULL, ICON_NONE);
	uiItemR(row, ptr, "highlights_lift", UI_ITEM_R_SLIDER, NULL, ICON_NONE);

	row = uiLayoutRow(layout, 0);
	uiItemR(row, ptr, "midtones_saturation", UI_ITEM_R_SLIDER, NULL, ICON_NONE);
	uiItemR(row, ptr, "midtones_contrast", UI_ITEM_R_SLIDER, NULL, ICON_NONE);
	uiItemR(row, ptr, "midtones_gamma", UI_ITEM_R_SLIDER, NULL, ICON_NONE);
	uiItemR(row, ptr, "midtones_gain", UI_ITEM_R_SLIDER, NULL, ICON_NONE);
	uiItemR(row, ptr, "midtones_lift", UI_ITEM_R_SLIDER, NULL, ICON_NONE);

	row = uiLayoutRow(layout, 0);
	uiItemR(row, ptr, "shadows_saturation", UI_ITEM_R_SLIDER, NULL, ICON_NONE);
	uiItemR(row, ptr, "shadows_contrast", UI_ITEM_R_SLIDER, NULL, ICON_NONE);
	uiItemR(row, ptr, "shadows_gamma", UI_ITEM_R_SLIDER, NULL, ICON_NONE);
	uiItemR(row, ptr, "shadows_gain", UI_ITEM_R_SLIDER, NULL, ICON_NONE);
	uiItemR(row, ptr, "shadows_lift", UI_ITEM_R_SLIDER, NULL, ICON_NONE);
}
static void node_composit_buts_colorcorrection_but(uiLayout *layout, bContext *UNUSED(C), PointerRNA *ptr) {
	uiLayout *row;
	
	row = uiLayoutRow(layout, 0);
	uiItemR(row, ptr, "red", 0, NULL, ICON_NONE);
	uiItemR(row, ptr, "green", 0, NULL, ICON_NONE);
	uiItemR(row, ptr, "blue", 0, NULL, ICON_NONE);
	row = layout;
	uiItemL(row, "Saturation", 0);
	uiItemR(row, ptr, "master_saturation", UI_ITEM_R_SLIDER, NULL, ICON_NONE);
	uiItemR(row, ptr, "highlights_saturation", UI_ITEM_R_SLIDER, NULL, ICON_NONE);
	uiItemR(row, ptr, "midtones_saturation", UI_ITEM_R_SLIDER, NULL, ICON_NONE);
	uiItemR(row, ptr, "shadows_saturation", UI_ITEM_R_SLIDER, NULL, ICON_NONE);

	uiItemL(row, "Contrast", 0);
	uiItemR(row, ptr, "master_contrast", UI_ITEM_R_SLIDER, NULL, ICON_NONE);
	uiItemR(row, ptr, "highlights_contrast", UI_ITEM_R_SLIDER, NULL, ICON_NONE);
	uiItemR(row, ptr, "midtones_contrast", UI_ITEM_R_SLIDER, NULL, ICON_NONE);
	uiItemR(row, ptr, "shadows_contrast", UI_ITEM_R_SLIDER, NULL, ICON_NONE);

	uiItemL(row, "Gamma", 0);
	uiItemR(row, ptr, "master_gamma", UI_ITEM_R_SLIDER, NULL, ICON_NONE);
	uiItemR(row, ptr, "highlights_gamma", UI_ITEM_R_SLIDER, NULL, ICON_NONE);
	uiItemR(row, ptr, "midtones_gamma", UI_ITEM_R_SLIDER, NULL, ICON_NONE);
	uiItemR(row, ptr, "shadows_gamma", UI_ITEM_R_SLIDER, NULL, ICON_NONE);

	uiItemL(row, "Gain", 0);
	uiItemR(row, ptr, "master_gain", UI_ITEM_R_SLIDER, NULL, ICON_NONE);
	uiItemR(row, ptr, "highlights_gain", UI_ITEM_R_SLIDER, NULL, ICON_NONE);
	uiItemR(row, ptr, "midtones_gain", UI_ITEM_R_SLIDER, NULL, ICON_NONE);
	uiItemR(row, ptr, "shadows_gain", UI_ITEM_R_SLIDER, NULL, ICON_NONE);
	
	uiItemL(row, "Lift", 0);
	uiItemR(row, ptr, "master_lift", UI_ITEM_R_SLIDER, NULL, ICON_NONE);
	uiItemR(row, ptr, "highlights_lift", UI_ITEM_R_SLIDER, NULL, ICON_NONE);
	uiItemR(row, ptr, "midtones_lift", UI_ITEM_R_SLIDER, NULL, ICON_NONE);
	uiItemR(row, ptr, "shadows_lift", UI_ITEM_R_SLIDER, NULL, ICON_NONE);

	row = uiLayoutRow(layout, 0);
	uiItemR(row, ptr, "midtones_start", 0, NULL, ICON_NONE);
	uiItemR(row, ptr, "midtones_end", 0, NULL, ICON_NONE);
}

static void node_composit_buts_switch(uiLayout *layout, bContext *UNUSED(C), PointerRNA *ptr)
{
	uiItemR(layout, ptr, "check", 0, NULL, ICON_NONE);
}

static void node_composit_buts_boxmask(uiLayout *layout, bContext *UNUSED(C), PointerRNA *ptr)
{
	uiLayout *row;
	
	row= uiLayoutRow(layout, 1);
	uiItemR(row, ptr, "x", 0, "X", ICON_NONE);
	uiItemR(row, ptr, "y", 0, "Y", ICON_NONE);
	
	row= uiLayoutRow(layout, 1);
	uiItemR(row, ptr, "width", UI_ITEM_R_SLIDER, NULL, ICON_NONE);
	uiItemR(row, ptr, "height", UI_ITEM_R_SLIDER, NULL, ICON_NONE);

	uiItemR(layout, ptr, "rotation", 0, NULL, ICON_NONE);
	uiItemR(layout, ptr, "mask_type", 0, NULL, ICON_NONE);
}

static void node_composit_buts_bokehimage(uiLayout *layout, bContext *UNUSED(C), PointerRNA *ptr)
{
	uiItemR(layout, ptr, "flaps", 0, NULL, ICON_NONE);
	uiItemR(layout, ptr, "angle", 0, NULL, ICON_NONE);
	uiItemR(layout, ptr, "rounding", UI_ITEM_R_SLIDER, NULL, ICON_NONE);
	uiItemR(layout, ptr, "catadioptric", UI_ITEM_R_SLIDER, NULL, ICON_NONE);
	uiItemR(layout, ptr, "shift", UI_ITEM_R_SLIDER, NULL, ICON_NONE);
}

void node_composit_backdrop_viewer(SpaceNode* snode, ImBuf* backdrop, bNode* node, int x, int y)
{
//	node_composit_backdrop_canvas(snode, backdrop, node, x, y);
	if (node->custom1 == 0) { /// @todo: why did we need this one?
		const float backdropWidth = backdrop->x;
		const float backdropHeight = backdrop->y;
		const float cx  = x+snode->zoom*backdropWidth*node->custom3;
		const float cy = y+snode->zoom*backdropHeight*node->custom4;

		glColor3f(1.0, 1.0, 1.0);

		glBegin(GL_LINES);
		glVertex2f(cx-25, cy-25);
		glVertex2f(cx+25, cy+25);
		glVertex2f(cx+25, cy-25);
		glVertex2f(cx-25, cy+25);
		glEnd();
	}
}

void node_composit_backdrop_boxmask(SpaceNode* snode, ImBuf* backdrop, bNode* node, int x, int y)
{
	NodeBoxMask * boxmask = node->storage;
	const float backdropWidth = backdrop->x;
	const float backdropHeight = backdrop->y;
	const float aspect = backdropWidth/backdropHeight;
	const float rad = DEG2RAD(-boxmask->rotation);
	const float cosine = cos(rad);
	const float sine = sin(rad);
	const float halveBoxWidth = backdropWidth*(boxmask->width/2.0f);
	const float halveBoxHeight = backdropHeight*(boxmask->height/2.0f)*aspect;

	float cx, cy, x1, x2, x3, x4;
	float y1, y2, y3, y4;


	/* keep this, saves us from a version patch */
	if(snode->zoom==0.0f) snode->zoom= 1.0f;

	glColor3f(1.0, 1.0, 1.0);

	cx  = x+snode->zoom*backdropWidth*boxmask->x;
	cy = y+snode->zoom*backdropHeight*boxmask->y;

	x1 = cx - (cosine*halveBoxWidth+sine*halveBoxHeight)*snode->zoom;
	x2 = cx - (cosine*-halveBoxWidth+sine*halveBoxHeight)*snode->zoom;
	x3 = cx - (cosine*-halveBoxWidth+sine*-halveBoxHeight)*snode->zoom;
	x4 = cx - (cosine*halveBoxWidth+sine*-halveBoxHeight)*snode->zoom;
	y1 = cy - (-sine*halveBoxWidth + cosine*halveBoxHeight)*snode->zoom;
	y2 = cy - (-sine*-halveBoxWidth + cosine*halveBoxHeight)*snode->zoom;
	y3 = cy - (-sine*-halveBoxWidth + cosine*-halveBoxHeight)*snode->zoom;
	y4 = cy - (-sine*halveBoxWidth + cosine*-halveBoxHeight)*snode->zoom;

	glBegin(GL_LINE_LOOP);
	glVertex2f(x1, y1);
	glVertex2f(x2, y2);
	glVertex2f(x3, y3);
	glVertex2f(x4, y4);
	glEnd();
}

void node_composit_backdrop_ellipsemask(SpaceNode* snode, ImBuf* backdrop, bNode* node, int x, int y)
{
	NodeEllipseMask * ellipsemask = node->storage;
	const float backdropWidth = backdrop->x;
	const float backdropHeight = backdrop->y;
	const float aspect = backdropWidth/backdropHeight;
	const float rad = DEG2RAD(-ellipsemask->rotation);
	const float cosine = cos(rad);
	const float sine = sin(rad);
	const float halveBoxWidth = backdropWidth*(ellipsemask->width/2.0f);
	const float halveBoxHeight = backdropHeight*(ellipsemask->height/2.0f)*aspect;

	float cx, cy, x1, x2, x3, x4;
	float y1, y2, y3, y4;


	/* keep this, saves us from a version patch */
	if(snode->zoom==0.0f) snode->zoom= 1.0f;

	glColor3f(1.0, 1.0, 1.0);

	cx  = x+snode->zoom*backdropWidth*ellipsemask->x;
	cy = y+snode->zoom*backdropHeight*ellipsemask->y;

	x1 = cx - (cosine*halveBoxWidth+sine*halveBoxHeight)*snode->zoom;
	x2 = cx - (cosine*-halveBoxWidth+sine*halveBoxHeight)*snode->zoom;
	x3 = cx - (cosine*-halveBoxWidth+sine*-halveBoxHeight)*snode->zoom;
	x4 = cx - (cosine*halveBoxWidth+sine*-halveBoxHeight)*snode->zoom;
	y1 = cy - (-sine*halveBoxWidth + cosine*halveBoxHeight)*snode->zoom;
	y2 = cy - (-sine*-halveBoxWidth + cosine*halveBoxHeight)*snode->zoom;
	y3 = cy - (-sine*-halveBoxWidth + cosine*-halveBoxHeight)*snode->zoom;
	y4 = cy - (-sine*halveBoxWidth + cosine*-halveBoxHeight)*snode->zoom;

	glBegin(GL_LINE_LOOP);

	glVertex2f(x1, y1);
	glVertex2f(x2, y2);
	glVertex2f(x3, y3);
	glVertex2f(x4, y4);
	glEnd();
}

static void node_composit_buts_ellipsemask(uiLayout *layout, bContext *UNUSED(C), PointerRNA *ptr)
{
	uiLayout *row;
	row= uiLayoutRow(layout, 1);
	uiItemR(row, ptr, "x", 0, "X", ICON_NONE);
	uiItemR(row, ptr, "y", 0, "Y", ICON_NONE);
	row= uiLayoutRow(layout, 1);
	uiItemR(row, ptr, "width", UI_ITEM_R_SLIDER, NULL, ICON_NONE);
	uiItemR(row, ptr, "height", UI_ITEM_R_SLIDER, NULL, ICON_NONE);

	uiItemR(layout, ptr, "rotation", 0, NULL, ICON_NONE);
	uiItemR(layout, ptr, "mask_type", 0, NULL, ICON_NONE);
}

static void node_composit_buts_viewer_but(uiLayout *layout, bContext *UNUSED(C), PointerRNA *ptr)
{
	uiLayout *col;
	
	uiItemR(layout, ptr, "tile_order", 0, NULL, ICON_NONE);
	if (RNA_enum_get(ptr, "tile_order")==0) {
		col= uiLayoutColumn(layout, 1);
		uiItemR(col, ptr, "center_x", 0, NULL, ICON_NONE);
		uiItemR(col, ptr, "center_y", 0, NULL, ICON_NONE);
	}
}

/* only once called */
static void node_composit_set_butfunc(bNodeType *ntype)
{
	ntype->uifuncbut = NULL;
	switch (ntype->type) {
		/* case NODE_GROUP:	 note, typeinfo for group is generated... see "XXX ugly hack" */

		case CMP_NODE_IMAGE:
			ntype->uifunc= node_composit_buts_image;
			break;
		case CMP_NODE_R_LAYERS:
			ntype->uifunc= node_composit_buts_renderlayers;
			break;
		case CMP_NODE_NORMAL:
			ntype->uifunc= node_buts_normal;
			break;
		case CMP_NODE_CURVE_VEC:
			ntype->uifunc= node_buts_curvevec;
			break;
		case CMP_NODE_CURVE_RGB:
			ntype->uifunc= node_buts_curvecol;
			break;
		case CMP_NODE_VALUE:
			ntype->uifunc= node_buts_value;
			break;
		case CMP_NODE_RGB:
			ntype->uifunc= node_buts_rgb;
			break;
		case CMP_NODE_FLIP:
			ntype->uifunc= node_composit_buts_flip;
			break;
		case CMP_NODE_SPLITVIEWER:
			ntype->uifunc= node_composit_buts_splitviewer;
			break;
		case CMP_NODE_MIX_RGB:
			ntype->uifunc= node_buts_mix_rgb;
			break;
		case CMP_NODE_VALTORGB:
			ntype->uifunc= node_buts_colorramp;
			break;
		case CMP_NODE_CROP:
			ntype->uifunc= node_composit_buts_crop;
			break;
		case CMP_NODE_BLUR:
			ntype->uifunc= node_composit_buts_blur;
			break;
		case CMP_NODE_DBLUR:
			ntype->uifunc= node_composit_buts_dblur;
			break;
		case CMP_NODE_BILATERALBLUR:
			ntype->uifunc= node_composit_buts_bilateralblur;
			break;
		case CMP_NODE_DEFOCUS:
			ntype->uifunc = node_composit_buts_defocus;
			break;
		case CMP_NODE_GLARE:
			ntype->uifunc = node_composit_buts_glare;
			break;
		case CMP_NODE_TONEMAP:
			ntype->uifunc = node_composit_buts_tonemap;
			break;
		case CMP_NODE_LENSDIST:
			ntype->uifunc = node_composit_buts_lensdist;
			break;
		case CMP_NODE_VECBLUR:
			ntype->uifunc= node_composit_buts_vecblur;
			break;
		case CMP_NODE_FILTER:
			ntype->uifunc= node_composit_buts_filter;
			break;
		case CMP_NODE_MAP_VALUE:
			ntype->uifunc= node_composit_buts_map_value;
			break;
		case CMP_NODE_TIME:
			ntype->uifunc= node_buts_time;
			break;
		case CMP_NODE_ALPHAOVER:
			ntype->uifunc= node_composit_buts_alphaover;
			break;
		case CMP_NODE_HUE_SAT:
			ntype->uifunc= node_composit_buts_hue_sat;
			break;
		case CMP_NODE_TEXTURE:
			ntype->uifunc= node_buts_texture;
			break;
		case CMP_NODE_DILATEERODE:
			ntype->uifunc= node_composit_buts_dilateerode;
			break;
		case CMP_NODE_OUTPUT_FILE:
			ntype->uifunc= node_composit_buts_file_output;
			ntype->uifuncbut= node_composit_buts_file_output_details;
			ntype->drawinputfunc = node_draw_input_file_output;
			break;
		case CMP_NODE_DIFF_MATTE:
			ntype->uifunc=node_composit_buts_diff_matte;
			break;
		case CMP_NODE_DIST_MATTE:
			ntype->uifunc=node_composit_buts_distance_matte;
			break;
		case CMP_NODE_COLOR_SPILL:
			ntype->uifunc=node_composit_buts_color_spill;
			break;
		case CMP_NODE_CHROMA_MATTE:
			ntype->uifunc=node_composit_buts_chroma_matte;
			break;
		case CMP_NODE_COLOR_MATTE:
			ntype->uifunc=node_composit_buts_color_matte;
			break;
		case CMP_NODE_SCALE:
			ntype->uifunc= node_composit_buts_scale;
			break;
		case CMP_NODE_ROTATE:
			ntype->uifunc=node_composit_buts_rotate;
			break;
		case CMP_NODE_CHANNEL_MATTE:
			ntype->uifunc= node_composit_buts_channel_matte;
			break;
		case CMP_NODE_LUMA_MATTE:
			ntype->uifunc= node_composit_buts_luma_matte;
			break;
		case CMP_NODE_MAP_UV:
			ntype->uifunc= node_composit_buts_map_uv;
			break;
		case CMP_NODE_ID_MASK:
			ntype->uifunc= node_composit_buts_id_mask;
			break;
		case CMP_NODE_DOUBLEEDGEMASK:
			ntype->uifunc= node_composit_buts_double_edge_mask;
			break;
		case CMP_NODE_MATH:
			ntype->uifunc= node_buts_math;
			break;
		case CMP_NODE_INVERT:
			ntype->uifunc= node_composit_buts_invert;
			break;
		case CMP_NODE_PREMULKEY:
			ntype->uifunc= node_composit_buts_premulkey;
			break;
		case CMP_NODE_VIEW_LEVELS:
			ntype->uifunc=node_composit_buts_view_levels;
			break;
		case CMP_NODE_COLORBALANCE:
			ntype->uifunc=node_composit_buts_colorbalance;
			ntype->uifuncbut=node_composit_buts_colorbalance_but;
			break;
		case CMP_NODE_HUECORRECT:
			ntype->uifunc=node_composit_buts_huecorrect;
			break;
		case CMP_NODE_ZCOMBINE:
			ntype->uifunc=node_composit_buts_zcombine;
			break;
		case CMP_NODE_COMBYCCA:
		case CMP_NODE_SEPYCCA:
			ntype->uifunc=node_composit_buts_ycc;
			break;
		case CMP_NODE_MOVIECLIP:
			ntype->uifunc= node_composit_buts_movieclip;
			break;
		case CMP_NODE_STABILIZE2D:
			ntype->uifunc= node_composit_buts_stabilize2d;
			break;
		case CMP_NODE_TRANSFORM:
			ntype->uifunc= node_composit_buts_transform;
			break;
		case CMP_NODE_MOVIEDISTORTION:
			ntype->uifunc= node_composit_buts_moviedistortion;
			break;
		case CMP_NODE_COLORCORRECTION:
			ntype->uifunc=node_composit_buts_colorcorrection;
			ntype->uifuncbut=node_composit_buts_colorcorrection_but;
			break;
		case CMP_NODE_SWITCH:
			ntype->uifunc= node_composit_buts_switch;
			break;
		case CMP_NODE_MASK_BOX:
			ntype->uifunc= node_composit_buts_boxmask;
			ntype->uibackdropfunc = node_composit_backdrop_boxmask;
			break;
		case CMP_NODE_MASK_ELLIPSE:
			ntype->uifunc= node_composit_buts_ellipsemask;
			ntype->uibackdropfunc = node_composit_backdrop_ellipsemask;
			break;
		case CMP_NODE_BOKEHIMAGE:
			ntype->uifunc= node_composit_buts_bokehimage;
			break;
		case CMP_NODE_VIEWER:
			ntype->uifunc = NULL;
			ntype->uifuncbut= node_composit_buts_viewer_but;
			ntype->uibackdropfunc = node_composit_backdrop_viewer;
			break;

		default:
			ntype->uifunc= NULL;
	}
	if (ntype->uifuncbut == NULL) ntype->uifuncbut = ntype->uifunc;

}

/* ****************** BUTTON CALLBACKS FOR TEXTURE NODES ***************** */

static void node_texture_buts_bricks(uiLayout *layout, bContext *UNUSED(C), PointerRNA *ptr)
{
	uiLayout *col;
	
	col= uiLayoutColumn(layout, 1);
	uiItemR(col, ptr, "offset", 0, "Offset", ICON_NONE);
	uiItemR(col, ptr, "offset_frequency", 0, "Frequency", ICON_NONE);
	
	col= uiLayoutColumn(layout, 1);
	uiItemR(col, ptr, "squash", 0, "Squash", ICON_NONE);
	uiItemR(col, ptr, "squash_frequency", 0, "Frequency", ICON_NONE);
}

static void node_texture_buts_proc(uiLayout *layout, bContext *UNUSED(C), PointerRNA *ptr)
{
	PointerRNA tex_ptr;
	bNode *node= ptr->data;
	ID *id= ptr->id.data;
	Tex *tex = (Tex *)node->storage;
	uiLayout *col, *row;
	
	RNA_pointer_create(id, &RNA_Texture, tex, &tex_ptr);

	col= uiLayoutColumn(layout, 0);

	switch ( tex->type ) {
		case TEX_BLEND:
			uiItemR(col, &tex_ptr, "progression", 0, "", ICON_NONE);
			row= uiLayoutRow(col, 0);
			uiItemR(row, &tex_ptr, "use_flip_axis", UI_ITEM_R_EXPAND, NULL, ICON_NONE);
			break;

		case TEX_MARBLE:
			row= uiLayoutRow(col, 0);
			uiItemR(row, &tex_ptr, "marble_type", UI_ITEM_R_EXPAND, NULL, ICON_NONE);
			row= uiLayoutRow(col, 0);
			uiItemR(row, &tex_ptr, "noise_type", UI_ITEM_R_EXPAND, NULL, ICON_NONE);
			row= uiLayoutRow(col, 0);
			uiItemR(row, &tex_ptr, "noise_basis", 0, "", ICON_NONE);
			row= uiLayoutRow(col, 0);
			uiItemR(row, &tex_ptr, "noise_basis_2", UI_ITEM_R_EXPAND, NULL, ICON_NONE);
			break;

		case TEX_MAGIC:
			uiItemR(col, &tex_ptr, "noise_depth", 0, NULL, ICON_NONE);
			break;

		case TEX_STUCCI:
			row= uiLayoutRow(col, 0);
			uiItemR(row, &tex_ptr, "stucci_type", UI_ITEM_R_EXPAND, NULL, ICON_NONE);
			row= uiLayoutRow(col, 0);
			uiItemR(row, &tex_ptr, "noise_type", UI_ITEM_R_EXPAND, NULL, ICON_NONE);
			uiItemR(col, &tex_ptr, "noise_basis", 0, "", ICON_NONE);
			break;

		case TEX_WOOD:
			uiItemR(col, &tex_ptr, "noise_basis", 0, "", ICON_NONE);
			uiItemR(col, &tex_ptr, "wood_type", 0, "", ICON_NONE);
			row= uiLayoutRow(col, 0);
			uiItemR(row, &tex_ptr, "noise_basis_2", UI_ITEM_R_EXPAND, NULL, ICON_NONE);
			row= uiLayoutRow(col, 0);
			uiLayoutSetActive(row, !(RNA_enum_get(&tex_ptr, "wood_type")==TEX_BAND || RNA_enum_get(&tex_ptr, "wood_type")==TEX_RING)); 
			uiItemR(row, &tex_ptr, "noise_type", UI_ITEM_R_EXPAND, NULL, ICON_NONE);
			break;
			
		case TEX_CLOUDS:
			uiItemR(col, &tex_ptr, "noise_basis", 0, "", ICON_NONE);
			row= uiLayoutRow(col, 0);
			uiItemR(row, &tex_ptr, "cloud_type", UI_ITEM_R_EXPAND, NULL, ICON_NONE);
			row= uiLayoutRow(col, 0);
			uiItemR(row, &tex_ptr, "noise_type", UI_ITEM_R_EXPAND, NULL, ICON_NONE);
			uiItemR(col, &tex_ptr, "noise_depth", UI_ITEM_R_EXPAND, "Depth", ICON_NONE);
			break;
			
		case TEX_DISTNOISE:
			uiItemR(col, &tex_ptr, "noise_basis", 0, "", ICON_NONE);
			uiItemR(col, &tex_ptr, "noise_distortion", 0, "", ICON_NONE);
			break;

		case TEX_MUSGRAVE:
			uiItemR(col, &tex_ptr, "musgrave_type", 0, "", ICON_NONE);
			uiItemR(col, &tex_ptr, "noise_basis", 0, "", ICON_NONE);
			break;
		case TEX_VORONOI:
			uiItemR(col, &tex_ptr, "distance_metric", 0, "", ICON_NONE);
			if (tex->vn_distm == TEX_MINKOVSKY) {
				uiItemR(col, &tex_ptr, "minkovsky_exponent", 0, NULL, ICON_NONE);
			}
			uiItemR(col, &tex_ptr, "color_mode", 0, "", ICON_NONE);
			break;
	}
}

static void node_texture_buts_image(uiLayout *layout, bContext *C, PointerRNA *ptr)
{
	uiTemplateID(layout, C, ptr, "image", NULL, "IMAGE_OT_open", NULL);
}

static void node_texture_buts_output(uiLayout *layout, bContext *UNUSED(C), PointerRNA *ptr)
{
	uiItemR(layout, ptr, "filepath", 0, "", ICON_NONE);
}

/* only once called */
static void node_texture_set_butfunc(bNodeType *ntype)
{
	ntype->uifuncbut = NULL;
	if ( ntype->type >= TEX_NODE_PROC && ntype->type < TEX_NODE_PROC_MAX ) {
		ntype->uifunc = node_texture_buts_proc;
	}
	else {
		switch (ntype->type) {

		case TEX_NODE_MATH:
			ntype->uifunc = node_buts_math;
			break;

		case TEX_NODE_MIX_RGB:
			ntype->uifunc = node_buts_mix_rgb;
			break;

		case TEX_NODE_VALTORGB:
			ntype->uifunc = node_buts_colorramp;
			break;

		case TEX_NODE_CURVE_RGB:
			ntype->uifunc= node_buts_curvecol;
			break;

		case TEX_NODE_CURVE_TIME:
			ntype->uifunc = node_buts_time;
			break;

		case TEX_NODE_TEXTURE:
			ntype->uifunc = node_buts_texture;
			break;

		case TEX_NODE_BRICKS:
			ntype->uifunc = node_texture_buts_bricks;
			break;

		case TEX_NODE_IMAGE:
			ntype->uifunc = node_texture_buts_image;
			break;

		case TEX_NODE_OUTPUT:
			ntype->uifunc = node_texture_buts_output;
			break;
		}
	}

	if (ntype->uifuncbut == NULL) {
		ntype->uifuncbut = ntype->uifunc;
	}
}

/* ******* init draw callbacks for all tree types, only called in usiblender.c, once ************* */

void ED_init_node_butfuncs(void)
{
	bNodeTreeType *treetype;
	bNodeType *ntype;
	bNodeSocketType *stype;
	int i;
	
	/* node type ui functions */
	for (i=0; i < NUM_NTREE_TYPES; ++i) {
		treetype = ntreeGetType(i);
		if (treetype) {
			for (ntype= treetype->node_types.first; ntype; ntype= ntype->next) {
				/* default ui functions */
				ntype->drawfunc = node_draw_default;
				ntype->drawupdatefunc = node_update_default;
				ntype->uifunc = NULL;
				ntype->uifuncbut = NULL;
				ntype->drawinputfunc = node_draw_input_default;
				ntype->drawoutputfunc = node_draw_output_default;
				ntype->resize_area_func = node_resize_area_default;
				
				node_common_set_butfunc(ntype);
				
				switch (i) {
				case NTREE_COMPOSIT:
					node_composit_set_butfunc(ntype);
					break;
				case NTREE_SHADER:
					node_shader_set_butfunc(ntype);
					break;
				case NTREE_TEXTURE:
					node_texture_set_butfunc(ntype);
					break;
				}
			}
		}
	}
	
	/* socket type ui functions */
	for (i=0; i < NUM_SOCKET_TYPES; ++i) {
		stype = ntreeGetSocketType(i);
		if (stype) {
			switch (stype->type) {
			case SOCK_FLOAT:
			case SOCK_INT:
			case SOCK_BOOLEAN:
				stype->buttonfunc = node_socket_button_default;
				break;
			case SOCK_VECTOR:
				stype->buttonfunc = node_socket_button_components;
				break;
			case SOCK_RGBA:
				stype->buttonfunc = node_socket_button_color;
				break;
			case SOCK_SHADER:
				stype->buttonfunc = node_socket_button_label;
				break;
			default:
				stype->buttonfunc = NULL;
			}
		}
	}
}

/* ************** Generic drawing ************** */

void draw_nodespace_back_pix(ARegion *ar, SpaceNode *snode, int color_manage)
{
	
	if ((snode->flag & SNODE_BACKDRAW) && snode->treetype==NTREE_COMPOSIT) {
		Image *ima= BKE_image_verify_viewer(IMA_TYPE_COMPOSITE, "Viewer Node");
		void *lock;
		ImBuf *ibuf= BKE_image_acquire_ibuf(ima, NULL, &lock);
		if (ibuf) {
			float x, y; 
			
			glMatrixMode(GL_PROJECTION);
			glPushMatrix();
			glMatrixMode(GL_MODELVIEW);
			glPushMatrix();

			/* keep this, saves us from a version patch */
			if (snode->zoom==0.0f) snode->zoom= 1.0f;
			
			/* somehow the offset has to be calculated inverse */
			
			glaDefine2DArea(&ar->winrct);
			/* ortho at pixel level curarea */
			wmOrtho2(-0.375, ar->winx-0.375, -0.375, ar->winy-0.375);
			
			x = (ar->winx-snode->zoom*ibuf->x)/2 + snode->xof;
			y = (ar->winy-snode->zoom*ibuf->y)/2 + snode->yof;
			
			if (!ibuf->rect) {
				if (color_manage)
					ibuf->profile = IB_PROFILE_LINEAR_RGB;
				else
					ibuf->profile = IB_PROFILE_NONE;
				IMB_rect_from_float(ibuf);
			}

			if (ibuf->rect) {
				if (snode->flag & SNODE_SHOW_ALPHA) {
					glPixelZoom(snode->zoom, snode->zoom);
					/* swap bytes, so alpha is most significant one, then just draw it as luminance int */
					if (ENDIAN_ORDER == B_ENDIAN)
						glPixelStorei(GL_UNPACK_SWAP_BYTES, 1);
					
					glaDrawPixelsSafe(x, y, ibuf->x, ibuf->y, ibuf->x, GL_LUMINANCE, GL_UNSIGNED_INT, ibuf->rect);
					
					glPixelStorei(GL_UNPACK_SWAP_BYTES, 0);
					glPixelZoom(1.0f, 1.0f);
				}
				else if (snode->flag & SNODE_USE_ALPHA) {
					glEnable(GL_BLEND);
					glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
					glPixelZoom(snode->zoom, snode->zoom);
					
					glaDrawPixelsSafe(x, y, ibuf->x, ibuf->y, ibuf->x, GL_RGBA, GL_UNSIGNED_BYTE, ibuf->rect);
					
					glPixelZoom(1.0f, 1.0f);
					glDisable(GL_BLEND);
				}
				else {
					glPixelZoom(snode->zoom, snode->zoom);
					
					glaDrawPixelsSafe(x, y, ibuf->x, ibuf->y, ibuf->x, GL_RGBA, GL_UNSIGNED_BYTE, ibuf->rect);
					
					glPixelZoom(1.0f, 1.0f);
				}
			}

			/// @note draw selected info on backdrop
			if (snode->edittree) {
				bNode *node = snode->edittree->nodes.first;
				while (node) {
					if (node->flag & NODE_SELECT) {
						if (node->typeinfo->uibackdropfunc) {
							node->typeinfo->uibackdropfunc(snode, ibuf, node, x, y);
						}
					}
					node = node->next;
				}
			}
			
			glMatrixMode(GL_PROJECTION);
			glPopMatrix();
			glMatrixMode(GL_MODELVIEW);
			glPopMatrix();
		}

		BKE_image_release_ibuf(ima, lock);
	}
}

#if 0
/* note: needs to be userpref or opengl profile option */
static void draw_nodespace_back_tex(ScrArea *sa, SpaceNode *snode)
{

	draw_nodespace_grid(snode);
	
	if (snode->flag & SNODE_BACKDRAW) {
		Image *ima= BKE_image_verify_viewer(IMA_TYPE_COMPOSITE, "Viewer Node");
		ImBuf *ibuf= BKE_image_get_ibuf(ima, NULL);
		if (ibuf) {
			int x, y;
			float zoom = 1.0;

			glMatrixMode(GL_PROJECTION);
			glPushMatrix();
			glMatrixMode(GL_MODELVIEW);
			glPushMatrix();
			
			glaDefine2DArea(&sa->winrct);

			if (ibuf->x > sa->winx || ibuf->y > sa->winy) {
				float zoomx, zoomy;
				zoomx= (float)sa->winx/ibuf->x;
				zoomy= (float)sa->winy/ibuf->y;
				zoom = MIN2(zoomx, zoomy);
			}
			
			x = (sa->winx-zoom*ibuf->x)/2 + snode->xof;
			y = (sa->winy-zoom*ibuf->y)/2 + snode->yof;

			glPixelZoom(zoom, zoom);

			glColor4f(1.0, 1.0, 1.0, 1.0);
			if (ibuf->rect)
				glaDrawPixelsTex(x, y, ibuf->x, ibuf->y, GL_UNSIGNED_BYTE, ibuf->rect);
			else if (ibuf->channels==4)
				glaDrawPixelsTex(x, y, ibuf->x, ibuf->y, GL_FLOAT, ibuf->rect_float);

			glPixelZoom(1.0, 1.0);

			glMatrixMode(GL_PROJECTION);
			glPopMatrix();
			glMatrixMode(GL_MODELVIEW);
			glPopMatrix();
		}
	}
}
#endif

/* if v2d not NULL, it clips and returns 0 if not visible */
int node_link_bezier_points(View2D *v2d, SpaceNode *snode, bNodeLink *link, float coord_array[][2], int resol)
{
	float dist, vec[4][2];
	
	/* in v0 and v3 we put begin/end points */
	if (link->fromsock) {
		vec[0][0]= link->fromsock->locx;
		vec[0][1]= link->fromsock->locy;
	}
	else {
		if (snode==NULL) return 0;
		vec[0][0]= snode->mx;
		vec[0][1]= snode->my;
	}
	if (link->tosock) {
		vec[3][0]= link->tosock->locx;
		vec[3][1]= link->tosock->locy;
	}
	else {
		if (snode==NULL) return 0;
		vec[3][0]= snode->mx;
		vec[3][1]= snode->my;
	}

	dist= UI_GetThemeValue(TH_NODE_CURVING)*0.10f*ABS(vec[0][0] - vec[3][0]);
	
	/* check direction later, for top sockets */
	vec[1][0]= vec[0][0]+dist;
	vec[1][1]= vec[0][1];
	
	vec[2][0]= vec[3][0]-dist;
	vec[2][1]= vec[3][1];
	
	if (v2d && MIN4(vec[0][0], vec[1][0], vec[2][0], vec[3][0]) > v2d->cur.xmax); /* clipped */
	else if (v2d && MAX4(vec[0][0], vec[1][0], vec[2][0], vec[3][0]) < v2d->cur.xmin); /* clipped */
	else {
		
		/* always do all three, to prevent data hanging around */
		BKE_curve_forward_diff_bezier(vec[0][0], vec[1][0], vec[2][0], vec[3][0], coord_array[0], resol, sizeof(float)*2);
		BKE_curve_forward_diff_bezier(vec[0][1], vec[1][1], vec[2][1], vec[3][1], coord_array[0]+1, resol, sizeof(float)*2);
		
		return 1;
	}
	return 0;
}

#define LINK_RESOL	24
void node_draw_link_bezier(View2D *v2d, SpaceNode *snode, bNodeLink *link, int th_col1, int do_shaded, int th_col2, int do_triple, int th_col3 )
{
	float coord_array[LINK_RESOL+1][2];
	
	if (node_link_bezier_points(v2d, snode, link, coord_array, LINK_RESOL)) {
		float dist, spline_step = 0.0f;
		int i;
		
		/* store current linewidth */
		float linew;
		glGetFloatv(GL_LINE_WIDTH, &linew);
		
		/* we can reuse the dist variable here to increment the GL curve eval amount*/
		dist = 1.0f/(float)LINK_RESOL;
		
		glEnable(GL_LINE_SMOOTH);
		
		if (do_triple) {
			UI_ThemeColorShadeAlpha(th_col3, -80, -120);
			glLineWidth(4.0f);
			
			glBegin(GL_LINE_STRIP);
			for (i=0; i<=LINK_RESOL; i++) {
				glVertex2fv(coord_array[i]);
			}
			glEnd();
		}
		
		/* XXX using GL_LINES for shaded node lines is a workaround
		 * for Intel hardware, this breaks with GL_LINE_STRIP and
		 * changing color in begin/end blocks.
		 */
		glLineWidth(1.5f);
		if (do_shaded) {
			glBegin(GL_LINES);
			for (i=0; i<LINK_RESOL; i++) {
				UI_ThemeColorBlend(th_col1, th_col2, spline_step);
				glVertex2fv(coord_array[i]);
				
				UI_ThemeColorBlend(th_col1, th_col2, spline_step+dist);
				glVertex2fv(coord_array[i+1]);
				
				spline_step += dist;
			}
			glEnd();
		}
		else {
			UI_ThemeColor(th_col1);
			glBegin(GL_LINE_STRIP);
			for (i=0; i<=LINK_RESOL; i++) {
				glVertex2fv(coord_array[i]);
			}
			glEnd();
		}
		
		glDisable(GL_LINE_SMOOTH);
		
		/* restore previuos linewidth */
		glLineWidth(linew);
	}
}

static void node_link_straight_points(View2D *UNUSED(v2d), SpaceNode *snode, bNodeLink *link, float coord_array[][2])
{
	if (link->fromsock) {
		coord_array[0][0]= link->fromsock->locx;
		coord_array[0][1]= link->fromsock->locy;
	}
	else {
		if (snode==NULL) return;
		coord_array[0][0]= snode->mx;
		coord_array[0][1]= snode->my;
	}
	if (link->tosock) {
		coord_array[1][0]= link->tosock->locx;
		coord_array[1][1]= link->tosock->locy;
	}
	else {
		if (snode==NULL) return;
		coord_array[1][0]= snode->mx;
		coord_array[1][1]= snode->my;
	}
}

void node_draw_link_straight(View2D *v2d, SpaceNode *snode, bNodeLink *link, int th_col1, int do_shaded, int th_col2, int do_triple, int th_col3 )
{
	float coord_array[2][2];
	float linew;
	int i;
	
	node_link_straight_points(v2d, snode, link, coord_array);
	
	/* store current linewidth */
	glGetFloatv(GL_LINE_WIDTH, &linew);
	
	glEnable(GL_LINE_SMOOTH);
	
	if (do_triple) {
		UI_ThemeColorShadeAlpha(th_col3, -80, -120);
		glLineWidth(4.0f);
		
		glBegin(GL_LINES);
		glVertex2fv(coord_array[0]);
		glVertex2fv(coord_array[1]);
		glEnd();
	}
	
	UI_ThemeColor(th_col1);
	glLineWidth(1.5f);
	
	/* XXX using GL_LINES for shaded node lines is a workaround
	 * for Intel hardware, this breaks with GL_LINE_STRIP and
	 * changing color in begin/end blocks.
	 */
	if (do_shaded) {
		glBegin(GL_LINES);
		for (i=0; i < LINK_RESOL-1; ++i) {
			float t= (float)i/(float)(LINK_RESOL-1);
			UI_ThemeColorBlend(th_col1, th_col2, t);
			glVertex2f((1.0f-t)*coord_array[0][0]+t*coord_array[1][0], (1.0f-t)*coord_array[0][1]+t*coord_array[1][1]);
			
			t= (float)(i+1)/(float)(LINK_RESOL-1);
			UI_ThemeColorBlend(th_col1, th_col2, t);
			glVertex2f((1.0f-t)*coord_array[0][0]+t*coord_array[1][0], (1.0f-t)*coord_array[0][1]+t*coord_array[1][1]);
		}
		glEnd();
	}
	else {
		glBegin(GL_LINE_STRIP);
		for (i=0; i < LINK_RESOL; ++i) {
			float t= (float)i/(float)(LINK_RESOL-1);
			glVertex2f((1.0f-t)*coord_array[0][0]+t*coord_array[1][0], (1.0f-t)*coord_array[0][1]+t*coord_array[1][1]);
		}
		glEnd();
	}
	
	glDisable(GL_LINE_SMOOTH);
	
	/* restore previuos linewidth */
	glLineWidth(linew);
}

/* note; this is used for fake links in groups too */
void node_draw_link(View2D *v2d, SpaceNode *snode, bNodeLink *link)
{
	int do_shaded= FALSE, th_col1= TH_HEADER, th_col2= TH_HEADER;
	int do_triple= FALSE, th_col3= TH_WIRE;
	
	if (link->fromsock==NULL && link->tosock==NULL)
		return;
	
	/* new connection */
	if (!link->fromsock || !link->tosock) {
		th_col1 = TH_ACTIVE;
		do_triple = TRUE;
	}
	else {
		/* going to give issues once... */
		if (link->tosock->flag & SOCK_UNAVAIL)
			return;
		if (link->fromsock->flag & SOCK_UNAVAIL)
			return;
		
		/* a bit ugly... but thats how we detect the internal group links */
		if (!link->fromnode || !link->tonode) {
			UI_ThemeColorBlend(TH_BACK, TH_WIRE, 0.5f);
			do_shaded = FALSE;
		}
		else {
			/* check cyclic */
			if ((link->fromnode->level >= link->tonode->level && link->tonode->level!=0xFFF) && (link->flag & NODE_LINK_VALID)) {
				/* special indicated link, on drop-node */
				if (link->flag & NODE_LINKFLAG_HILITE) {
					th_col1= th_col2= TH_ACTIVE;
				}
				else {
					/* regular link */
					if (link->fromnode->flag & SELECT)
						th_col1= TH_EDGE_SELECT;
					if (link->tonode->flag & SELECT)
						th_col2= TH_EDGE_SELECT;
				}
				do_shaded = TRUE;
				do_triple = TRUE;
			}				
			else {
				th_col1 = TH_REDALERT;
			}
		}
	}
	
	node_draw_link_bezier(v2d, snode, link, th_col1, do_shaded, th_col2, do_triple, th_col3);
//	node_draw_link_straight(v2d, snode, link, th_col1, do_shaded, th_col2, do_triple, th_col3);
}

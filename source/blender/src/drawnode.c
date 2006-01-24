/**
 * $Id:
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

#include <math.h>
#include <stdio.h>
#include <string.h>

#include "BLI_blenlib.h"
#include "BLI_arithb.h"

#include "DNA_action_types.h"
#include "DNA_ipo_types.h"
#include "DNA_ID.h"
#include "DNA_material_types.h"
#include "DNA_node_types.h"
#include "DNA_object_types.h"
#include "DNA_scene_types.h"
#include "DNA_space_types.h"
#include "DNA_screen_types.h"
#include "DNA_texture_types.h"
#include "DNA_userdef_types.h"

#include "BKE_global.h"
#include "BKE_image.h"
#include "BKE_library.h"
#include "BKE_main.h"
#include "BKE_material.h"
#include "BKE_node.h"
#include "BKE_object.h"
#include "BKE_texture.h"
#include "BKE_utildefines.h"

#include "BIF_gl.h"
#include "BIF_glutil.h"
#include "BIF_interface.h"
#include "BIF_interface_icons.h"
#include "BIF_language.h"
#include "BIF_mywindow.h"
#include "BIF_previewrender.h"
#include "BIF_resources.h"
#include "BIF_screen.h"
#include "BIF_space.h"

#include "BSE_drawipo.h"
#include "BSE_node.h"
#include "BSE_view.h"

#include "BMF_Api.h"

#include "blendef.h"
#include "butspace.h"
#include "interface.h"	/* urm...  for rasterpos_safe, roundbox */
#include "mydevice.h"

#include "MEM_guardedalloc.h"

static void snode_drawstring(SpaceNode *snode, char *str, int okwidth)
{
	char drawstr[NODE_MAXSTR];
	int width;
	
	if(str[0]==0 || okwidth<4) return;
	
	BLI_strncpy(drawstr, str, NODE_MAXSTR);
	width= snode->aspect*BIF_GetStringWidth(snode->curfont, drawstr, 0);

	if(width > okwidth) {
		int len= strlen(drawstr)-1;
		
		while(width > okwidth && len>=0) {
			drawstr[len]= 0;
			
			width= snode->aspect*BIF_GetStringWidth(snode->curfont, drawstr, 0);
			len--;
		}
		if(len==0) return;
	}
	BIF_DrawString(snode->curfont, drawstr, 0);

}

/* **************  Socket callbacks *********** */

/* NOTE: this is a block-menu, needs 0 events, otherwise the menu closes */
static uiBlock *socket_vector_menu(void *butpoin_v)
{
	float *butpoin= butpoin_v;
	uiBlock *block;
	
	block= uiNewBlock(&curarea->uiblocks, "socket menu", UI_EMBOSS, UI_HELV, curarea->win);
	
	/* use this for a fake extra empy space around the buttons */
	uiDefBut(block, LABEL, 0, "",			-4, -4, 188, 68, NULL, 0, 0, 0, 0, "");
	
	uiBlockBeginAlign(block);
	uiDefButF(block, NUMSLI, 0, "X ",	 0,40,180,20, butpoin, -1.0, 1.0, 10, 0, "");
	uiDefButF(block, NUMSLI, 0, "Y ",	 0,20,180,20, butpoin+1, -1.0, 1.0, 10, 0, "");
	uiDefButF(block, NUMSLI, 0, "Z ",	 0,0,180,20, butpoin+2, -1.0, 1.0, 10, 0, "");
	
	uiBlockSetDirection(block, UI_TOP);
	
	allqueue(REDRAWNODE, 0);
	
	return block;
}

static void node_sync_cb(void *snode_v, void *node_v)
{
	SpaceNode *snode= snode_v;
	
	if(snode->treetype==NTREE_SHADER) {
		nodeShaderSynchronizeID(node_v, 1);
		allqueue(REDRAWBUTSSHADING, 0);
	}
}

/* ****************** GENERAL CALLBACKS FOR NODES ***************** */

static void node_ID_title_cb(void *node_v, void *unused_v)
{
	bNode *node= node_v;
	
	if(node->id) {
		test_idbutton(node->id->name+2);	/* library.c, verifies unique name */
		BLI_strncpy(node->name, node->id->name+2, 21);
		
		allqueue(REDRAWBUTSSHADING, 0);
		allqueue(REDRAWNODE, 0);
		allqueue(REDRAWOOPS, 0);
	}
}


static void node_but_title_cb(void *node_v, void *but_v)
{
	bNode *node= node_v;
	uiBut *bt= but_v;
	BLI_strncpy(node->name, bt->drawstr, NODE_MAXSTR);
	
	allqueue(REDRAWNODE, 0);
}


/* ****************** BUTTON CALLBACKS FOR ALL TREES ***************** */

static int node_buts_group(uiBlock *block, bNodeTree *ntree, bNode *node, rctf *butr)
{
	if(block && node->id) {
		uiBut *bt;
		short width;
		
		uiBlockBeginAlign(block);
		
		/* name button */
		width= (short)(butr->xmax-butr->xmin - (node->id->us>1?19.0f:0.0f));
		bt= uiDefBut(block, TEX, B_NOP, "NT:",
					 butr->xmin, butr->ymin, width, 19, 
					 node->id->name+2, 0.0, 19.0, 0, 0, "NodeTree name");
		uiButSetFunc(bt, node_ID_title_cb, node, NULL);
		
		/* user amount */
		if(node->id->us>1) {
			char str1[32];
			sprintf(str1, "%d", node->id->us);
			bt= uiDefBut(block, BUT, B_NOP, str1, 
						 butr->xmax-19, butr->ymin, 19, 19, 
						 NULL, 0, 0, 0, 0, "Displays number of users. Click to make a single-user copy.");
			//uiButSetFunc(bt, node_mat_alone_cb, node, NULL);
		}
		
		uiBlockEndAlign(block);
	}	
	return 19;
}

static int node_buts_value(uiBlock *block, bNodeTree *ntree, bNode *node, rctf *butr)
{
	if(block) {
		bNodeSocket *sock= node->outputs.first;		/* first socket stores value */
		
		uiDefButF(block, NUM, B_NODE_EXEC, "", 
				  butr->xmin, butr->ymin, butr->xmax-butr->xmin, 20, 
				  sock->ns.vec, 0.0f, 1.0f, 10, 2, "");
		
	}
	return 20;
}

static int node_buts_rgb(uiBlock *block, bNodeTree *ntree, bNode *node, rctf *butr)
{
	if(block) {
		bNodeSocket *sock= node->outputs.first;		/* first socket stores value */
		if(sock) {
			/* enforce square box drawing */
			uiBlockSetEmboss(block, UI_EMBOSSP);
			
			uiDefButF(block, HSVCUBE, B_NODE_EXEC, "", 
					  butr->xmin, butr->ymin, butr->xmax-butr->xmin, 12, 
					  sock->ns.vec, 0.0f, 1.0f, 3, 0, "");
			uiDefButF(block, HSVCUBE, B_NODE_EXEC, "", 
					  butr->xmin, butr->ymin+15, butr->xmax-butr->xmin, butr->ymax-butr->ymin -15 -15, 
					  sock->ns.vec, 0.0f, 1.0f, 2, 0, "");
			uiDefButF(block, COL, B_NOP, "",		
					  butr->xmin, butr->ymax-12, butr->xmax-butr->xmin, 12, 
					  sock->ns.vec, 0.0, 0.0, -1, 0, "");
			/* the -1 above prevents col button to popup a color picker */
			
			uiBlockSetEmboss(block, UI_EMBOSS);
		}
	}
	return 30 + (int)(node->width-NODE_DY);
}

static int node_buts_mix_rgb(uiBlock *block, bNodeTree *ntree, bNode *node, rctf *butr)
{
	if(block) {
		uiBut *bt;
		
		/* blend type */
		bt=uiDefButS(block, MENU, B_NODE_EXEC, "Mix %x0|Add %x1|Subtract %x3|Multiply %x2|Screen %x4|Divide %x5|Difference %x6|Darken %x7|Lighten %x8",
					 butr->xmin, butr->ymin, butr->xmax-butr->xmin, 20, 
					 &node->custom1, 0, 0, 0, 0, "");
		uiButSetFunc(bt, node_but_title_cb, node, bt);
	}
	return 20;
}

static int node_buts_valtorgb(uiBlock *block, bNodeTree *ntree, bNode *node, rctf *butr)
{
	if(block) {
		if(node->storage) {
			draw_colorband_buts_small(block, node->storage, butr, B_NODE_EXEC);
		}
	}
	return 40;
}

static int node_buts_curvevec(uiBlock *block, bNodeTree *ntree, bNode *node, rctf *butr)
{
	if(block) {
		curvemap_buttons(block, node->storage, 'v', B_NODE_EXEC, B_REDR, butr);
	}	
	return (int)(node->width-NODE_DY);
}

static int node_buts_curvecol(uiBlock *block, bNodeTree *ntree, bNode *node, rctf *butr)
{
	if(block) {
		curvemap_buttons(block, node->storage, 'c', B_NODE_EXEC, B_REDR, butr);
	}	
	return (int)(node->width-NODE_DY);
}

static int node_buts_normal(uiBlock *block, bNodeTree *ntree, bNode *node, rctf *butr)
{
	if(block) {
		bNodeSocket *sock= node->outputs.first;		/* first socket stores normal */
		
		uiDefButF(block, BUT_NORMAL, B_NODE_EXEC, "", 
				  butr->xmin, butr->ymin, butr->xmax-butr->xmin, butr->ymax-butr->ymin, 
				  sock->ns.vec, 0.0f, 1.0f, 0, 0, "");
		
	}	
	return (int)(node->width-NODE_DY);
}



/* ****************** BUTTON CALLBACKS FOR SHADER NODES ***************** */


static void node_mat_alone_cb(void *node_v, void *unused)
{
	bNode *node= node_v;
	
	node->id= (ID *)copy_material((Material *)node->id);
	
	BIF_undo_push("Single user material");
	allqueue(REDRAWBUTSSHADING, 0);
	allqueue(REDRAWNODE, 0);
	allqueue(REDRAWOOPS, 0);
}

static void node_browse_mat_cb(void *ntree_v, void *node_v)
{
	bNodeTree *ntree= ntree_v;
	bNode *node= node_v;
	
	if(node->menunr<1) return;
	
	if(node->menunr==32767) {	/* code for Add New */
		if(node->id) {
			/* make copy, but make sure it doesnt have the node tag nor nodes */
			Material *ma= (Material *)node->id;
			ma->id.us--;
			ma= copy_material(ma);
			ma->use_nodes= 0;
			if(ma->nodetree) {
				ntreeFreeTree(ma->nodetree);
				MEM_freeN(ma->nodetree);
			}
			ma->nodetree= NULL;
			node->id= (ID *)ma;
		}
		else node->id= (ID *)add_material("MatNode");
	}
	else {
		if(node->id) node->id->us--;
		node->id= BLI_findlink(&G.main->mat, node->menunr-1);
		id_us_plus(node->id);
	}
	BLI_strncpy(node->name, node->id->name+2, 21);
	
	nodeSetActive(ntree, node);

	allqueue(REDRAWBUTSSHADING, 0);
	allqueue(REDRAWNODE, 0);
	BIF_preview_changed(ID_MA);

	node->menunr= 0;
}

static void node_new_mat_cb(void *ntree_v, void *node_v)
{
	bNodeTree *ntree= ntree_v;
	bNode *node= node_v;
	
	node->id= (ID *)add_material("MatNode");
	BLI_strncpy(node->name, node->id->name+2, 21);

	nodeSetActive(ntree, node);

	allqueue(REDRAWBUTSSHADING, 0);
	allqueue(REDRAWNODE, 0);
	BIF_preview_changed(ID_MA);

}

static void node_texmap_cb(void *texmap_v, void *unused_v)
{
	init_mapping(texmap_v);
}

static int node_shader_buts_material(uiBlock *block, bNodeTree *ntree, bNode *node, rctf *butr)
{
	if(block) {
		uiBut *bt;
		short dx= (short)((butr->xmax-butr->xmin)/3.0f), has_us= (node->id && node->id->us>1);
		short dy= (short)butr->ymin;
		char *strp;
		
		/* WATCH IT: we use this callback in material buttons, but then only want first row */
		if(butr->ymax-butr->ymin > 21.0f) dy+= 19;
		
		uiBlockBeginAlign(block);
		if(node->id==NULL) uiBlockSetCol(block, TH_REDALERT);
		else if(has_us) uiBlockSetCol(block, TH_BUT_SETTING1);
		else uiBlockSetCol(block, TH_BUT_SETTING2);
		
		/* browse button */
		IDnames_to_pupstring(&strp, NULL, "ADD NEW %x32767", &(G.main->mat), NULL, NULL);
		node->menunr= 0;
		bt= uiDefButS(block, MENU, B_NOP, strp, 
				  butr->xmin, dy, 19, 19, 
				  &node->menunr, 0, 0, 0, 0, "Browses existing choices or adds NEW");
		uiButSetFunc(bt, node_browse_mat_cb, ntree, node);
		if(strp) MEM_freeN(strp);
		
		/* Add New button */
		if(node->id==NULL) {
			bt= uiDefBut(block, BUT, B_NOP, "Add New",
						 butr->xmin+19, dy, (short)(butr->xmax-butr->xmin-19.0f), 19, 
						 NULL, 0.0, 0.0, 0, 0, "Add new Material");
			uiButSetFunc(bt, node_new_mat_cb, ntree, node);
			uiBlockSetCol(block, TH_AUTO);
		}
		else {
			/* name button */
			short width= (short)(butr->xmax-butr->xmin-19.0f - (has_us?19.0f:0.0f));
			bt= uiDefBut(block, TEX, B_NOP, "MA:",
						  butr->xmin+19, dy, width, 19, 
						  node->id->name+2, 0.0, 19.0, 0, 0, "Material name");
			uiButSetFunc(bt, node_ID_title_cb, node, NULL);
			
			/* user amount */
			if(has_us) {
				char str1[32];
				sprintf(str1, "%d", node->id->us);
				bt= uiDefBut(block, BUT, B_NOP, str1, 
							  butr->xmax-19, dy, 19, 19, 
							  NULL, 0, 0, 0, 0, "Displays number of users. Click to make a single-user copy.");
				uiButSetFunc(bt, node_mat_alone_cb, node, NULL);
			}
			
			/* WATCH IT: we use this callback in material buttons, but then only want first row */
			if(butr->ymax-butr->ymin > 21.0f) {
				/* node options */
				uiBlockSetCol(block, TH_AUTO);
				uiDefButBitS(block, TOG, SH_NODE_MAT_DIFF, B_NODE_EXEC, "Diff",
							 butr->xmin, butr->ymin, dx, 19, 
							 &node->custom1, 0, 0, 0, 0, "Material Node outputs Diffuse");
				uiDefButBitS(block, TOG, SH_NODE_MAT_SPEC, B_NODE_EXEC, "Spec",
							 butr->xmin+dx, butr->ymin, dx, 19, 
							 &node->custom1, 0, 0, 0, 0, "Material Node outputs Specular");
				uiDefButBitS(block, TOG, SH_NODE_MAT_NEG, B_NODE_EXEC, "Neg Normal",
							 butr->xmax-dx, butr->ymin, dx, 19,
							 &node->custom1, 0, 0, 0, 0, "Material Node uses inverted Normal");
			}
		}
		uiBlockEndAlign(block);
	}	
	return 38;
}

static int node_shader_buts_texture(uiBlock *block, bNodeTree *ntree, bNode *node, rctf *butr)
{
	if(block) {
		uiBut *bt;
		
		bt= uiDefIDPoinBut(block, test_texpoin_but, ID_TE, B_NODE_EXEC, "",
						   butr->xmin, butr->ymin, butr->xmax-butr->xmin, 19, 
						   &node->id,  ""); 
		uiButSetFunc(bt, node_ID_title_cb, node, NULL);
		
	}	
	return 19;
}


static int node_shader_buts_mapping(uiBlock *block, bNodeTree *ntree, bNode *node, rctf *butr)
{
	if(block) {
		TexMapping *texmap= node->storage;
		short dx= (short)((butr->xmax-butr->xmin)/7.0f);
		short dy= (short)(butr->ymax-19);
		
		uiBlockSetFunc(block, node_texmap_cb, texmap, NULL);	/* all buttons get this */
		
		uiBlockBeginAlign(block);
		uiDefButF(block, NUM, B_NODE_EXEC, "", butr->xmin+dx, dy, 2*dx, 19, texmap->loc, -1000.0f, 1000.0f, 10, 2, "");
		uiDefButF(block, NUM, B_NODE_EXEC, "", butr->xmin+3*dx, dy, 2*dx, 19, texmap->loc+1, -1000.0f, 1000.0f, 10, 2, "");
		uiDefButF(block, NUM, B_NODE_EXEC, "", butr->xmin+5*dx, dy, 2*dx, 19, texmap->loc+2, -1000.0f, 1000.0f, 10, 2, "");
		dy-= 19;
		uiDefButF(block, NUM, B_NODE_EXEC, "", butr->xmin+dx, dy, 2*dx, 19, texmap->rot, -1000.0f, 1000.0f, 1000, 1, "");
		uiDefButF(block, NUM, B_NODE_EXEC, "", butr->xmin+3*dx, dy, 2*dx, 19, texmap->rot+1, -1000.0f, 1000.0f, 1000, 1, "");
		uiDefButF(block, NUM, B_NODE_EXEC, "", butr->xmin+5*dx, dy, 2*dx, 19, texmap->rot+2, -1000.0f, 1000.0f, 1000, 1, "");
		dy-= 19;
		uiDefButF(block, NUM, B_NODE_EXEC, "", butr->xmin+dx, dy, 2*dx, 19, texmap->size, -1000.0f, 1000.0f, 10, 2, "");
		uiDefButF(block, NUM, B_NODE_EXEC, "", butr->xmin+3*dx, dy, 2*dx, 19, texmap->size+1, -1000.0f, 1000.0f, 10, 2, "");
		uiDefButF(block, NUM, B_NODE_EXEC, "", butr->xmin+5*dx, dy, 2*dx, 19, texmap->size+2, -1000.0f, 1000.0f, 10, 2, "");
		dy-= 25;
		uiBlockBeginAlign(block);
		uiDefButF(block, NUM, B_NODE_EXEC, "", butr->xmin+dx, dy, 2*dx, 19, texmap->min, -10.0f, 10.0f, 100, 2, "");
		uiDefButF(block, NUM, B_NODE_EXEC, "", butr->xmin+3*dx, dy, 2*dx, 19, texmap->min+1, -10.0f, 10.0f, 100, 2, "");
		uiDefButF(block, NUM, B_NODE_EXEC, "", butr->xmin+5*dx, dy, 2*dx, 19, texmap->min+2, -10.0f, 10.0f, 100, 2, "");
		dy-= 19;
		uiDefButF(block, NUM, B_NODE_EXEC, "", butr->xmin+dx, dy, 2*dx, 19, texmap->max, -10.0f, 10.0f, 10, 2, "");
		uiDefButF(block, NUM, B_NODE_EXEC, "", butr->xmin+3*dx, dy, 2*dx, 19, texmap->max+1, -10.0f, 10.0f, 10, 2, "");
		uiDefButF(block, NUM, B_NODE_EXEC, "", butr->xmin+5*dx, dy, 2*dx, 19, texmap->max+2, -10.0f, 10.0f, 10, 2, "");
		uiBlockEndAlign(block);
		
		/* labels/options */
		
		dy= (short)(butr->ymax-19);
		uiDefBut(block, LABEL, B_NOP, "Loc", butr->xmin, dy, dx, 19, NULL, 0.0f, 0.0f, 0, 0, "");
		dy-= 19;
		uiDefBut(block, LABEL, B_NOP, "Rot", butr->xmin, dy, dx, 19, NULL, 0.0f, 0.0f, 0, 0, "");
		dy-= 19;
		uiDefBut(block, LABEL, B_NOP, "Size", butr->xmin, dy, dx, 19, NULL, 0.0f, 0.0f, 0, 0, "");
		dy-= 25;
		uiDefButBitI(block, TOG, TEXMAP_CLIP_MIN, B_NODE_EXEC, "Min", butr->xmin, dy, dx-4, 19, &texmap->flag, 0.0f, 0.0f, 0, 0, "");
		dy-= 19;
		uiDefButBitI(block, TOG, TEXMAP_CLIP_MAX, B_NODE_EXEC, "Max", butr->xmin, dy, dx-4, 19, &texmap->flag, 0.0f, 0.0f, 0, 0, "");
		
	}	
	return 5*19 + 6;
}


/* only once called */
static void node_shader_set_butfunc(bNodeType *ntype)
{
	switch(ntype->type) {
		case NODE_GROUP:	/* note, generic type, but put here because we call this function anyway */
			ntype->butfunc= node_buts_group;
			break;
		case SH_NODE_MATERIAL:
			ntype->butfunc= node_shader_buts_material;
			break;
		case SH_NODE_TEXTURE:
			ntype->butfunc= node_shader_buts_texture;
			break;
		case SH_NODE_NORMAL:
			ntype->butfunc= node_buts_normal;
			break;
		case SH_NODE_CURVE_VEC:
			ntype->butfunc= node_buts_curvevec;
			break;
		case SH_NODE_CURVE_RGB:
			ntype->butfunc= node_buts_curvecol;
			break;
		case SH_NODE_MAPPING:
			ntype->butfunc= node_shader_buts_mapping;
			break;
		case SH_NODE_VALUE:
			ntype->butfunc= node_buts_value;
			break;
		case SH_NODE_RGB:
			ntype->butfunc= node_buts_rgb;
			break;
		case SH_NODE_MIX_RGB:
			ntype->butfunc= node_buts_mix_rgb;
			break;
		case SH_NODE_VALTORGB:
			ntype->butfunc= node_buts_valtorgb;
			break;
		default:
			ntype->butfunc= NULL;
	}
}

/* ****************** BUTTON CALLBACKS FOR COMPOSIT NODES ***************** */



static void node_browse_image_cb(void *ntree_v, void *node_v)
{
	bNodeTree *ntree= ntree_v;
	bNode *node= node_v;
	
	nodeSetActive(ntree, node);
	
	if(node->menunr<1) return;
	if(node->menunr==32767) {	/* code for Load New */
		addqueue(curarea->win, UI_BUT_EVENT, B_NODE_LOADIMAGE);
	}
	else {
		if(node->id) node->id->us--;
		node->id= BLI_findlink(&G.main->image, node->menunr-1);
		id_us_plus(node->id);

		BLI_strncpy(node->name, node->id->name+2, 21);

		addqueue(curarea->win, RENDERPREVIEW, 1);
	}
	node->menunr= 0;
}

static void node_active_cb(void *ntree_v, void *node_v)
{
	nodeSetActive(ntree_v, node_v);
}

static int node_composit_buts_image(uiBlock *block, bNodeTree *ntree, bNode *node, rctf *butr)
{
	if(block) {
		uiBut *bt;
		short dy= (short)butr->ymin;
		char *strp;
		
		uiBlockBeginAlign(block);
		uiBlockSetCol(block, TH_BUT_SETTING2);
		
		/* browse button */
		IDnames_to_pupstring(&strp, NULL, "LOAD NEW %x32767", &(G.main->image), NULL, NULL);
		node->menunr= 0;
		bt= uiDefButS(block, MENU, B_NOP, strp, 
					  butr->xmin, dy, 19, 19, 
					  &node->menunr, 0, 0, 0, 0, "Browses existing choices");
		uiButSetFunc(bt, node_browse_image_cb, ntree, node);
		if(strp) MEM_freeN(strp);
		
		/* Add New button */
		if(node->id==NULL) {
			bt= uiDefBut(block, BUT, B_NODE_LOADIMAGE, "Load New",
						 butr->xmin+19, dy, (short)(butr->xmax-butr->xmin-19.0f), 19, 
						 NULL, 0.0, 0.0, 0, 0, "Add new Image");
			uiButSetFunc(bt, node_active_cb, ntree, node);
			uiBlockSetCol(block, TH_AUTO);
		}
		else {
			/* name button */
			short width= (short)(butr->xmax-butr->xmin-19.0f);
			bt= uiDefBut(block, TEX, B_NOP, "IMA:",
						 butr->xmin+19, dy, width, 19, 
						 node->id->name+2, 0.0, 19.0, 0, 0, "Image name");
			uiButSetFunc(bt, node_ID_title_cb, node, NULL);
		}			
		
	}	
	return 19;
}

static int node_composit_buts_blur(uiBlock *block, bNodeTree *ntree, bNode *node, rctf *butr)
{
	if(block) {
		uiBut *bt;
		
		uiBlockBeginAlign(block);
		bt=uiDefButS(block, NUM, B_NODE_EXEC, "X:",
					 butr->xmin, butr->ymin, (butr->xmax-butr->xmin)/2, 19, 
					 &node->custom1, 0, 256, 0, 0, "");
		bt=uiDefButS(block, NUM, B_NODE_EXEC, "Y:",
					 butr->xmin+(butr->xmax-butr->xmin)/2, butr->ymin, (butr->xmax-butr->xmin)/2, 19, 
					 &node->custom2, 0, 256, 0, 0, "");
	}
	return 19;
}

static int node_composit_buts_filter(uiBlock *block, bNodeTree *ntree, bNode *node, rctf *butr)
{
	if(block) {
		uiBut *bt;
		
		/* blend type */
		bt=uiDefButS(block, MENU, B_NODE_EXEC, "Soften %x0|Sharpen %x1|Laplace %x2|Sobel %x3|Prewitt %x4|Kirsch %x5|Shadow %x6",
					 butr->xmin, butr->ymin, butr->xmax-butr->xmin, 20, 
					 &node->custom1, 0, 0, 0, 0, "");
		uiButSetFunc(bt, node_but_title_cb, node, bt);
	}
	return 20;
}


/* only once called */
static void node_composit_set_butfunc(bNodeType *ntype)
{
	switch(ntype->type) {
		case NODE_GROUP:	/* note, generic type, but put here because we call this function anyway */
			ntype->butfunc= node_buts_group;
			break;
		case CMP_NODE_IMAGE:
			ntype->butfunc= node_composit_buts_image;
			break;
		case CMP_NODE_NORMAL:
			ntype->butfunc= node_buts_normal;
			break;
		case CMP_NODE_CURVE_VEC:
			ntype->butfunc= node_buts_curvevec;
			break;
		case CMP_NODE_CURVE_RGB:
			ntype->butfunc= node_buts_curvecol;
			break;
		case CMP_NODE_VALUE:
			ntype->butfunc= node_buts_value;
			break;
		case CMP_NODE_RGB:
			ntype->butfunc= node_buts_rgb;
			break;
		case CMP_NODE_MIX_RGB:
			ntype->butfunc= node_buts_mix_rgb;
			break;
		case CMP_NODE_VALTORGB:
			ntype->butfunc= node_buts_valtorgb;
			break;
		case CMP_NODE_BLUR:
			ntype->butfunc= node_composit_buts_blur;
			break;
		case CMP_NODE_FILTER:
			ntype->butfunc= node_composit_buts_filter;
			break;
		default:
			ntype->butfunc= NULL;
	}
}


/* ******* init draw callbacks for all tree types, only called in usiblender.c, once ************* */

void init_node_butfuncs(void)
{
	bNodeType **typedefs;
	
	/* shader nodes */
	typedefs= node_all_shaders;		/* BKE_node.h */
	while( *typedefs) {
		node_shader_set_butfunc(*typedefs);
		typedefs++;
	}
	/* composit nodes */
	typedefs= node_all_composit;		/* BKE_node.h */
	while( *typedefs) {
		node_composit_set_butfunc(*typedefs);
		typedefs++;
	}
}

/* ************** Generic drawing ************** */

static void draw_nodespace_grid(SpaceNode *snode)
{
	float start, step= 25.0f;

	BIF_ThemeColorShade(TH_BACK, -10);
	
	start= snode->v2d.cur.xmin -fmod(snode->v2d.cur.xmin, step);
	
	glBegin(GL_LINES);
	for(; start<snode->v2d.cur.xmax; start+=step) {
		glVertex2f(start, snode->v2d.cur.ymin);
		glVertex2f(start, snode->v2d.cur.ymax);
	}

	start= snode->v2d.cur.ymin -fmod(snode->v2d.cur.ymin, step);
	for(; start<snode->v2d.cur.ymax; start+=step) {
		glVertex2f(snode->v2d.cur.xmin, start);
		glVertex2f(snode->v2d.cur.xmax, start);
	}
	
	/* X and Y axis */
	BIF_ThemeColorShade(TH_BACK, -18);
	glVertex2f(0.0f, snode->v2d.cur.ymin);
	glVertex2f(0.0f, snode->v2d.cur.ymax);
	glVertex2f(snode->v2d.cur.xmin, 0.0f);
	glVertex2f(snode->v2d.cur.xmax, 0.0f);
	
	glEnd();
}


static void nodeshadow(rctf *rct, float radius, float aspect, int select)
{
	float rad;
	float a;
	char alpha= 2;
	
	glEnable(GL_BLEND);
	
	if(radius > (rct->ymax-rct->ymin-10.0f)/2.0f)
		rad= (rct->ymax-rct->ymin-10.0f)/2.0f;
	else
		rad= radius;
	
	if(select) a= 10.0f*aspect; else a= 7.0f*aspect;
	for(; a>0.0f; a-=aspect) {
		/* alpha ranges from 2 to 20 or so */
		glColor4ub(0, 0, 0, alpha);
		alpha+= 2;
		
		gl_round_box(GL_POLYGON, rct->xmin - a, rct->ymin - a, rct->xmax + a, rct->ymax-10.0f + a, rad+a);
	}
	
	/* outline emphasis */
	glEnable( GL_LINE_SMOOTH );
	glColor4ub(0, 0, 0, 100);
	gl_round_box(GL_LINE_LOOP, rct->xmin-0.5f, rct->ymin-0.5f, rct->xmax+0.5f, rct->ymax+0.5f, radius);
	glDisable( GL_LINE_SMOOTH );
	
	glDisable(GL_BLEND);
}

/* nice AA filled circle */
static void socket_circle_draw(float x, float y, float size, int type, int select)
{
	/* 16 values of sin function */
	static float si[16] = {
		0.00000000, 0.39435585,0.72479278,0.93775213,
		0.99871650,0.89780453,0.65137248,0.29936312,
		-0.10116832,-0.48530196,-0.79077573,-0.96807711,
		-0.98846832,-0.84864425,-0.57126821,-0.20129852
	};
	/* 16 values of cos function */
	static float co[16] ={
		1.00000000,0.91895781,0.68896691,0.34730525,
		-0.05064916,-0.44039415,-0.75875812,-0.95413925,
		-0.99486932,-0.87434661,-0.61210598,-0.25065253,
		0.15142777,0.52896401,0.82076344,0.97952994,
	};
	int a;
	
	if(select==0) {
		if(type==-1)
			glColor3ub(0, 0, 0);
		else if(type==SOCK_VALUE)
			glColor3ub(160, 160, 160);
		else if(type==SOCK_VECTOR)
			glColor3ub(100, 100, 200);
		else if(type==SOCK_RGBA)
			glColor3ub(200, 200, 40);
		else 
			glColor3ub(100, 200, 100);
	}
	else {
		if(type==SOCK_VALUE)
			glColor3ub(200, 200, 200);
		else if(type==SOCK_VECTOR)
			glColor3ub(140, 140, 240);
		else if(type==SOCK_RGBA)
			glColor3ub(240, 240, 100);
		else 
			glColor3ub(140, 240, 140);
	}
	
	glBegin(GL_POLYGON);
	for(a=0; a<16; a++)
		glVertex2f(x+size*si[a], y+size*co[a]);
	glEnd();
	
	glColor4ub(0, 0, 0, 150);
	glEnable(GL_BLEND);
	glEnable( GL_LINE_SMOOTH );
	glBegin(GL_LINE_LOOP);
	for(a=0; a<16; a++)
		glVertex2f(x+size*si[a], y+size*co[a]);
	glEnd();
	glDisable( GL_LINE_SMOOTH );
	glDisable(GL_BLEND);
}

/* not a callback */
static void node_draw_preview(bNodePreview *preview, rctf *prv)
{
	float scale= (prv->xmax-prv->xmin)/((float)preview->xsize);
	float centx= prv->xmin + 0.5*(prv->xmax-prv->xmin);
	float centy= prv->ymin + 0.5*(prv->ymax-prv->ymin);
	
	/* draw standard bacdrop to show alpha */
	glBegin(GL_TRIANGLES);
	glColor3f(0.625f, 0.625f, 0.625f);
	glVertex2f(prv->xmin, prv->ymin);
	glVertex2f(prv->xmax, prv->ymin);
	glVertex2f(centx, centy);
	glVertex2f(prv->xmin, prv->ymax);
	glVertex2f(prv->xmax, prv->ymax);
	glVertex2f(centx, centy);
	
	glColor3f(0.25f, 0.25f, 0.25f);
	glVertex2f(prv->xmin, prv->ymin);
	glVertex2f(prv->xmin, prv->ymax);
	glVertex2f(centx, centy);
	glVertex2f(prv->xmax, prv->ymin);
	glVertex2f(prv->xmax, prv->ymax);
	glVertex2f(centx, centy);
	glEnd();
	
	glPixelZoom(scale, scale);
	glEnable(GL_BLEND);
	
	glaDrawPixelsTex(prv->xmin, prv->ymin, preview->xsize, preview->ysize, GL_FLOAT, preview->rect);
	
	glDisable(GL_BLEND);
	glPixelZoom(1.0f, 1.0f);
	
}

/* based on settings in node, sets drawing rect info. each redraw! */
static void node_update_hidden(bNode *node)
{
	bNodeSocket *nsock;
	float rad, drad, hiddenrad= HIDDEN_RAD;
	int totin=0, totout=0, tot;
	
	/* calculate minimal radius */
	for(nsock= node->inputs.first; nsock; nsock= nsock->next)
		if(!(nsock->flag & SOCK_HIDDEN))
			totin++;
	for(nsock= node->outputs.first; nsock; nsock= nsock->next)
		if(!(nsock->flag & SOCK_HIDDEN))
			totout++;
	
	tot= MAX2(totin, totout);
	if(tot>4) {
		hiddenrad += 5.0*(float)(tot-4);
	}
	
	node->totr.xmin= node->locx;
	node->totr.xmax= node->locx + 3*hiddenrad + node->miniwidth;
	node->totr.ymax= node->locy + (hiddenrad - 0.5f*NODE_DY);
	node->totr.ymin= node->totr.ymax - 2*hiddenrad;
	
	/* output sockets */
	rad=drad= M_PI/(1.0f + (float)totout);
	
	for(nsock= node->outputs.first; nsock; nsock= nsock->next) {
		if(!(nsock->flag & SOCK_HIDDEN)) {
			nsock->locx= node->totr.xmax - hiddenrad + sin(rad)*hiddenrad;
			nsock->locy= node->totr.ymin + hiddenrad + cos(rad)*hiddenrad;
			rad+= drad;
		}
	}
	
	/* input sockets */
	rad=drad= - M_PI/(1.0f + (float)totin);
	
	for(nsock= node->inputs.first; nsock; nsock= nsock->next) {
		if(!(nsock->flag & SOCK_HIDDEN)) {
			nsock->locx= node->totr.xmin + hiddenrad + sin(rad)*hiddenrad;
			nsock->locy= node->totr.ymin + hiddenrad + cos(rad)*hiddenrad;
			rad+= drad;
		}
	}
}

/* based on settings in node, sets drawing rect info. each redraw! */
static void node_update(bNode *node)
{
	bNodeSocket *nsock;
	float dy= node->locy;
	
	/* header */
	dy-= NODE_DY;
	
	/* little bit space in top */
	if(node->outputs.first)
		dy-= NODE_DYS/2;
	
	/* output sockets */
	for(nsock= node->outputs.first; nsock; nsock= nsock->next) {
		if(!(nsock->flag & SOCK_HIDDEN)) {
			nsock->locx= node->locx + node->width;
			nsock->locy= dy - NODE_DYS;
			dy-= NODE_DY;
		}
	}
	
	node->prvr.xmin= node->butr.xmin= node->locx + NODE_DYS;
	node->prvr.xmax= node->butr.xmax= node->locx + node->width- NODE_DYS;
	
	/* preview rect? */
	if(node->flag & NODE_PREVIEW) {
		float aspect= 1.0f;
		
		if(node->preview && node->preview->xsize && node->preview->ysize) 
			aspect= (float)node->preview->ysize/(float)node->preview->xsize;
		
		dy-= NODE_DYS/2;
		node->prvr.ymax= dy;
		node->prvr.ymin= dy - aspect*(node->width-NODE_DY);
		dy= node->prvr.ymin - NODE_DYS/2;
	}
	
	/* buttons rect? */
	if((node->flag & NODE_OPTIONS) && node->typeinfo->butfunc) {
		dy-= NODE_DYS/2;
		node->butr.ymax= dy;
		node->butr.ymin= dy - (float)node->typeinfo->butfunc(NULL, NULL, node, NULL);
		dy= node->butr.ymin - NODE_DYS/2;
	}
	
	/* input sockets */
	for(nsock= node->inputs.first; nsock; nsock= nsock->next) {
		if(!(nsock->flag & SOCK_HIDDEN)) {
			nsock->locx= node->locx;
			nsock->locy= dy - NODE_DYS;
			dy-= NODE_DY;
		}
	}
	
	/* little bit space in end */
	if(node->inputs.first || (node->flag & (NODE_OPTIONS|NODE_PREVIEW))==0 )
		dy-= NODE_DYS/2;
	
	node->totr.xmin= node->locx;
	node->totr.xmax= node->locx + node->width;
	node->totr.ymax= node->locy;
	node->totr.ymin= dy;
}

/* based on settings in node, sets drawing rect info. each redraw! */
/* note: this assumes only 1 group at a time is drawn (linked data) */
/* in node->totr the entire boundbox for the group is stored */
static void node_update_group(bNode *gnode)
{
	bNodeTree *ngroup= (bNodeTree *)gnode->id;
	bNode *node;
	bNodeSocket *nsock;
	rctf *rect= &gnode->totr;
	int counter;
	
	/* center them, is a bit of abuse of locx and locy though */
	for(node= ngroup->nodes.first; node; node= node->next) {
		node->locx+= gnode->locx;
		node->locy+= gnode->locy;
		if(node->flag & NODE_HIDDEN)
			node_update_hidden(node);
		else
			node_update(node);
		node->locx-= gnode->locx;
		node->locy-= gnode->locy;
	}
	counter= 1;
	for(node= ngroup->nodes.first; node; node= node->next) {
		if(counter) {
			*rect= node->totr;
			counter= 0;
		}
		else
			BLI_union_rctf(rect, &node->totr);
	}
	if(counter==1) return;	/* should be prevented? */
	
	rect->xmin-= NODE_DY;
	rect->ymin-= NODE_DY;
	rect->xmax+= NODE_DY;
	rect->ymax+= NODE_DY;
	
	/* output sockets */
	for(nsock= gnode->outputs.first; nsock; nsock= nsock->next) {
		nsock->locx= rect->xmax;
		nsock->locy= nsock->tosock->locy;
	}
	
	/* input sockets */
	for(nsock= gnode->inputs.first; nsock; nsock= nsock->next) {
		nsock->locx= rect->xmin;
		nsock->locy= nsock->tosock->locy;
	}
}

static void node_scaling_widget(int color_id, float aspect, float xmin, float ymin, float xmax, float ymax)
{
	float dx;
	float dy;
	
	dx= 0.5f*(xmax-xmin);
	dy= 0.5f*(ymax-ymin);
	
	BIF_ThemeColorShade(color_id, +30);	
	fdrawline(xmin, ymin, xmax, ymax);
	fdrawline(xmin+dx, ymin, xmax, ymax-dy);
	
	BIF_ThemeColorShade(color_id, -10);
	fdrawline(xmin, ymin+aspect, xmax, ymax+aspect);
	fdrawline(xmin+dx, ymin+aspect, xmax, ymax-dy+aspect);
}

static int node_get_colorid(bNode *node)
{
	if(node->typeinfo->nclass==NODE_CLASS_INPUT)
		return TH_NODE_IN_OUT;
	if(node->typeinfo->nclass==NODE_CLASS_OUTPUT) {
		if(node->flag & NODE_DO_OUTPUT)
			return TH_NODE_IN_OUT;
		else
			return TH_NODE;
	}
	if(node->typeinfo->nclass==NODE_CLASS_GENERATOR)
		return TH_NODE_GENERATOR;
	if(node->typeinfo->nclass==NODE_CLASS_OPERATOR)
		return TH_NODE_OPERATOR;
	if(node->typeinfo->nclass==NODE_CLASS_GROUP)
		return TH_NODE_GROUP;
	return TH_NODE;
}

static void node_draw_basis(ScrArea *sa, SpaceNode *snode, bNode *node)
{
	bNodeSocket *sock;
	uiBut *bt;
	rctf *rct= &node->totr;
	float slen, iconofs;
	int ofs, color_id= node_get_colorid(node);
	
	uiSetRoundBox(15-4);
	nodeshadow(rct, BASIS_RAD, snode->aspect, node->flag & SELECT);
	
	/* header */
	if(color_id==TH_NODE)
		BIF_ThemeColorShade(color_id, -20);
	else
		BIF_ThemeColor(color_id);
		
	uiSetRoundBox(3);
	uiRoundBox(rct->xmin, rct->ymax-NODE_DY, rct->xmax, rct->ymax, BASIS_RAD);
	
	/* show/hide icons, note this sequence is copied in editnode.c */
	iconofs= rct->xmax;
	
	if(node->typeinfo->flag & NODE_PREVIEW) {
		int icon_id;
		
		if(node->flag & (NODE_ACTIVE_ID|NODE_DO_OUTPUT))
			icon_id= ICON_MATERIAL;
		else
			icon_id= ICON_MATERIAL_DEHLT;
		iconofs-= 18.0f;
		glEnable(GL_BLEND);
		BIF_icon_set_aspect(icon_id, snode->aspect);
		BIF_icon_draw_blended(iconofs, rct->ymax-NODE_DY+2, icon_id, 0, -60);
		glDisable(GL_BLEND);
	}
	if(node->type == NODE_GROUP) {
		iconofs-= 18.0f;
		glEnable(GL_BLEND);
		BIF_icon_set_aspect(ICON_NODE, snode->aspect);
		BIF_icon_draw_blended(iconofs, rct->ymax-NODE_DY+2, ICON_NODE, 0, -60);
		glDisable(GL_BLEND);
	}
	if(node->typeinfo->flag & NODE_OPTIONS) {
		iconofs-= 18.0f;
		glEnable(GL_BLEND);
		BIF_icon_set_aspect(ICON_BUTS, snode->aspect);
		BIF_icon_draw_blended(iconofs, rct->ymax-NODE_DY+2, ICON_BUTS, 0, -60);
		glDisable(GL_BLEND);
	}
	if(node->outputs.first) {
		int shade;
		/* socket selector */
		iconofs-= 18.0f;
		if(node_has_hidden_sockets(node))
			shade= -40;
		else
			shade= -90;
		glEnable(GL_BLEND);
		BIF_icon_set_aspect(ICON_PLUS, snode->aspect);
		BIF_icon_draw_blended(iconofs, rct->ymax-NODE_DY+2, ICON_PLUS, 0, shade);
		glDisable(GL_BLEND);
	}
	
	/* title */
	if(node->flag & SELECT) 
		BIF_ThemeColor(TH_TEXT_HI);
	else
		BIF_ThemeColorBlendShade(TH_TEXT, color_id, 0.4, 10);
	
	/* open/close entirely? */
	ui_draw_tria_icon(rct->xmin+8.0f, rct->ymax-NODE_DY+4.0f, snode->aspect, 'v');

	if(node->flag & SELECT) 
		BIF_ThemeColor(TH_TEXT_HI);
	else
		BIF_ThemeColor(TH_TEXT);
	
	ui_rasterpos_safe(rct->xmin+19.0f, rct->ymax-NODE_DY+5.0f, snode->aspect);
	snode_drawstring(snode, node->name, (int)(iconofs - rct->xmin-18.0f));
					 
	/* body */
	BIF_ThemeColor(TH_NODE);	
	uiSetRoundBox(8);
	uiRoundBox(rct->xmin, rct->ymin, rct->xmax, rct->ymax-NODE_DY, BASIS_RAD);
	
	/* scaling indicator */
	node_scaling_widget(TH_NODE, snode->aspect, rct->xmax-BASIS_RAD*snode->aspect, rct->ymin, rct->xmax, rct->ymin+BASIS_RAD*snode->aspect);

	/* outline active emphasis */
	if(node->flag & NODE_ACTIVE) {
		glEnable(GL_BLEND);
		glColor4ub(200, 200, 200, 140);
		uiSetRoundBox(15-4);
		gl_round_box(GL_LINE_LOOP, rct->xmin, rct->ymin, rct->xmax, rct->ymax, BASIS_RAD);
		glDisable(GL_BLEND);
	}
	
	/* we make buttons for input sockets, if... */
	if(node->flag & NODE_OPTIONS) {
		if(node->inputs.first || node->typeinfo->butfunc) {
			uiBlock *block= uiNewBlock(NULL, "node buttons", UI_EMBOSS, UI_HELV, sa->win);
			BLI_addtail(&sa->uiblocks, block);
			uiBlockSetFlag(block, UI_BLOCK_NO_HILITE);
			if(snode->id)
				uiSetButLock(snode->id->lib!=NULL, "Can't edit library data");
			node->block= block;
		}
	}
	
	/* hurmf... another candidate for callback, have to see how this works first */
	if(node->id && node->block && snode->treetype==NTREE_SHADER)
		nodeShaderSynchronizeID(node, 0);
	
	/* socket inputs, buttons */
	for(sock= node->inputs.first; sock; sock= sock->next) {
		if(!(sock->flag & SOCK_HIDDEN)) {
			socket_circle_draw(sock->locx, sock->locy, NODE_SOCKSIZE, sock->type, sock->flag & SELECT);
			
			if(node->block && sock->link==NULL) {
				float *butpoin= sock->ns.vec;
				
				if(node->type==NODE_GROUP && sock->tosock)
					butpoin= sock->tosock->ns.vec;
				
				if(sock->type==SOCK_VALUE) {
					bt= uiDefButF(node->block, NUM, B_NODE_EXEC, sock->name, 
						  (short)sock->locx+NODE_DYS, (short)(sock->locy)-9, (short)node->width-NODE_DY, 17, 
						  butpoin, 0.0f, 1.0f, 10, 2, "");
					uiButSetFunc(bt, node_sync_cb, snode, node);
				}
				else if(sock->type==SOCK_VECTOR) {
					uiDefBlockBut(node->block, socket_vector_menu, butpoin, sock->name, 
						  (short)sock->locx+NODE_DYS, (short)sock->locy-9, (short)node->width-NODE_DY, 17, 
						  "");
				}
				else if(node->block && sock->type==SOCK_RGBA) {
					short labelw= node->width-NODE_DY-40, width;
					
					if(labelw>0) width= 40; else width= node->width-NODE_DY;
					
					bt= uiDefButF(node->block, COL, B_NODE_EXEC, "", 
						(short)(sock->locx+NODE_DYS), (short)sock->locy-8, width, 15, 
						   butpoin, 0, 0, 0, 0, "");
					uiButSetFunc(bt, node_sync_cb, snode, node);
					
					if(labelw>0) uiDefBut(node->block, LABEL, 0, sock->name, 
										   (short)(sock->locx+NODE_DYS) + 40, (short)sock->locy-8, labelw, 15, 
										   NULL, 0, 0, 0, 0, "");
				}
			}
			else {
				BIF_ThemeColor(TH_TEXT);
				ui_rasterpos_safe(sock->locx+8.0f, sock->locy-5.0f, snode->aspect);
				BIF_DrawString(snode->curfont, sock->name, 0);
			}
		}
	}
	
	/* socket outputs */
	for(sock= node->outputs.first; sock; sock= sock->next) {
		if(!(sock->flag & SOCK_HIDDEN)) {
			socket_circle_draw(sock->locx, sock->locy, NODE_SOCKSIZE, sock->type, sock->flag & SELECT);
			
			BIF_ThemeColor(TH_TEXT);
			ofs= 0;
			slen= snode->aspect*BIF_GetStringWidth(snode->curfont, sock->name, 0);
			while(slen > node->width) {
				ofs++;
				slen= snode->aspect*BIF_GetStringWidth(snode->curfont, sock->name+ofs, 0);
			}
			ui_rasterpos_safe(sock->locx-8.0f-slen, sock->locy-5.0f, snode->aspect);
			BIF_DrawString(snode->curfont, sock->name+ofs, 0);
		}
	}
	
	/* preview */
	if(node->flag & NODE_PREVIEW)
		if(node->preview && node->preview->rect)
			node_draw_preview(node->preview, &node->prvr);
		
	/* buttons */
	if(node->flag & NODE_OPTIONS) {
		if(node->typeinfo->butfunc) {
			node->typeinfo->butfunc(node->block, snode->nodetree, node, &node->butr);
		}
		uiDrawBlock(node->block);
	}

}

void node_draw_hidden(SpaceNode *snode, bNode *node)
{
	bNodeSocket *sock;
	rctf *rct= &node->totr;
	float dx, centy= 0.5f*(rct->ymax+rct->ymin);
	float hiddenrad= 0.5f*(rct->ymax-rct->ymin);
	int color_id= node_get_colorid(node);
	
	/* shadow */
	uiSetRoundBox(15);
	nodeshadow(rct, hiddenrad, snode->aspect, node->flag & SELECT);

	/* body */
	BIF_ThemeColor(color_id);	
	uiRoundBox(rct->xmin, rct->ymin, rct->xmax, rct->ymax, hiddenrad);
	
	/* outline active emphasis */
	if(node->flag & NODE_ACTIVE) {
		glEnable(GL_BLEND);
		glColor4ub(200, 200, 200, 140);
		gl_round_box(GL_LINE_LOOP, rct->xmin, rct->ymin, rct->xmax, rct->ymax, hiddenrad);
		glDisable(GL_BLEND);
	}
	
	/* title */
	if(node->flag & SELECT) 
		BIF_ThemeColor(TH_TEXT_HI);
	else
		BIF_ThemeColorBlendShade(TH_TEXT, color_id, 0.4, 10);
	
	/* open entirely icon */
	ui_draw_tria_icon(rct->xmin+9.0f, centy-6.0f, snode->aspect, 'h');	
	
	if(node->flag & SELECT) 
		BIF_ThemeColor(TH_TEXT_HI);
	else
		BIF_ThemeColor(TH_TEXT);
	
	if(node->miniwidth>0.0f) {
		ui_rasterpos_safe(rct->xmin+21.0f, centy-4.0f, snode->aspect);
		snode_drawstring(snode, node->name, (int)(rct->xmax - rct->xmin-18.0f -12.0f));
	}	

	/* scale widget thing */
	BIF_ThemeColorShade(color_id, -10);	
	dx= 10.0f;
	fdrawline(rct->xmax-dx, centy-4.0f, rct->xmax-dx, centy+4.0f);
	fdrawline(rct->xmax-dx-3.0f*snode->aspect, centy-4.0f, rct->xmax-dx-3.0f*snode->aspect, centy+4.0f);
	
	BIF_ThemeColorShade(color_id, +30);
	dx-= snode->aspect;
	fdrawline(rct->xmax-dx, centy-4.0f, rct->xmax-dx, centy+4.0f);
	fdrawline(rct->xmax-dx-3.0f*snode->aspect, centy-4.0f, rct->xmax-dx-3.0f*snode->aspect, centy+4.0f);
	
	/* sockets */
	for(sock= node->inputs.first; sock; sock= sock->next) {
		if(!(sock->flag & SOCK_HIDDEN))
			socket_circle_draw(sock->locx, sock->locy, NODE_SOCKSIZE, sock->type, sock->flag & SELECT);
	}
	
	for(sock= node->outputs.first; sock; sock= sock->next) {
		if(!(sock->flag & SOCK_HIDDEN))
			socket_circle_draw(sock->locx, sock->locy, NODE_SOCKSIZE, sock->type, sock->flag & SELECT);
	}
}

/* note; this is used for fake links in groups too */
void node_draw_link(SpaceNode *snode, bNodeLink *link)
{
	float vec[4][3];
	float dist, spline_step, mx=0.0f, my=0.0f;
	int curve_res, do_shaded= 1, th_col1= TH_WIRE, th_col2= TH_WIRE;
	
	if(link->fromnode==NULL && link->tonode==NULL)
		return;
	
	/* this is dragging link */
	if(link->fromnode==NULL || link->tonode==NULL) {
		short mval[2];
		getmouseco_areawin(mval);
		areamouseco_to_ipoco(G.v2d, mval, &mx, &my);
		BIF_ThemeColor(TH_WIRE);
		do_shaded= 0;
	}
	else {
		/* a bit ugly... but thats how we detect the internal group links */
		if(link->fromnode==link->tonode) {
			BIF_ThemeColorBlend(TH_BACK, TH_WIRE, 0.25f);
			do_shaded= 0;
		}
		else {
			/* check cyclic */
			if(link->fromnode->level >= link->tonode->level && link->tonode->level!=0xFFF) {
				if(link->fromnode->flag & SELECT)
					th_col1= TH_EDGE_SELECT;
				if(link->tonode->flag & SELECT)
					th_col2= TH_EDGE_SELECT;
			}				
			else {
				BIF_ThemeColor(TH_REDALERT);
				do_shaded= 0;
			}
		}
	}
	
	vec[0][2]= vec[1][2]= vec[2][2]= vec[3][2]= 0.0; /* only 2d spline, set the Z to 0*/
	
	/* in v0 and v3 we put begin/end points */
	if(link->fromnode) {
		vec[0][0]= link->fromsock->locx;
		vec[0][1]= link->fromsock->locy;
	}
	else {
		vec[0][0]= mx;
		vec[0][1]= my;
	}
	if(link->tonode) {
		vec[3][0]= link->tosock->locx;
		vec[3][1]= link->tosock->locy;
	}
	else {
		vec[3][0]= mx;
		vec[3][1]= my;
	}
	
	dist= 0.5f*ABS(vec[0][0] - vec[3][0]);
	
	/* check direction later, for top sockets */
	vec[1][0]= vec[0][0]+dist;
	vec[1][1]= vec[0][1];
	
	vec[2][0]= vec[3][0]-dist;
	vec[2][1]= vec[3][1];
	
	if( MIN4(vec[0][0], vec[1][0], vec[2][0], vec[3][0]) > G.v2d->cur.xmax); /* clipped */	
	else if ( MAX4(vec[0][0], vec[1][0], vec[2][0], vec[3][0]) < G.v2d->cur.xmin); /* clipped */
	else {
		curve_res = 24;
		
		/* we can reuse the dist variable here to increment the GL curve eval amount*/
		dist = 1.0f/curve_res;
		spline_step = 0.0f;
		
		glMap1f(GL_MAP1_VERTEX_3, 0.0, 1.0, 3, 4, vec[0]);
		glBegin(GL_LINE_STRIP);
		while (spline_step < 1.000001f) {
			if(do_shaded)
				BIF_ThemeColorBlend(th_col1, th_col2, spline_step);
			glEvalCoord1f(spline_step);
			spline_step += dist;
		}
		glEnd();
	}
}

static void node_draw_nodetree(ScrArea *sa, SpaceNode *snode, bNodeTree *ntree)
{
	bNode *node;
	bNodeLink *link;
	
	if(ntree==NULL) return;		/* groups... */
	
	/* node lines */
	glEnable(GL_BLEND);
	glEnable( GL_LINE_SMOOTH );
	for(link= ntree->links.first; link; link= link->next)
		node_draw_link(snode, link);
	glDisable(GL_BLEND);
	glDisable( GL_LINE_SMOOTH );
	
	/* not selected first */
	for(node= ntree->nodes.first; node; node= node->next) {
		node->block= NULL;	/* were freed */
		if(!(node->flag & SELECT)) {
			if(node->flag & NODE_GROUP_EDIT);
			else if(node->flag & NODE_HIDDEN)
				node_draw_hidden(snode, node);
			else
				node_draw_basis(sa, snode, node);
		}
	}
	
	/* selected */
	for(node= ntree->nodes.first; node; node= node->next) {
		if(node->flag & SELECT) {
			if(node->flag & NODE_GROUP_EDIT);
			else if(node->flag & NODE_HIDDEN)
				node_draw_hidden(snode, node);
			else
				node_draw_basis(sa, snode, node);
		}
	}	
}

/* fake links from groupnode to internal nodes */
static void node_draw_group_links(SpaceNode *snode, bNode *gnode)
{
	bNodeLink fakelink;
	bNodeSocket *sock;
	
	glEnable(GL_BLEND);
	glEnable( GL_LINE_SMOOTH );
	
	fakelink.tonode= fakelink.fromnode= gnode;
	
	for(sock= gnode->inputs.first; sock; sock= sock->next) {
		if(!(sock->flag & SOCK_HIDDEN)) {
			if(sock->tosock) {
				fakelink.fromsock= sock;
				fakelink.tosock= sock->tosock;
				node_draw_link(snode, &fakelink);
			}
		}
	}
	
	for(sock= gnode->outputs.first; sock; sock= sock->next) {
		if(!(sock->flag & SOCK_HIDDEN)) {
			if(sock->tosock) {
				fakelink.tosock= sock;
				fakelink.fromsock= sock->tosock;
				node_draw_link(snode, &fakelink);
			}
		}
	}
	
	glDisable(GL_BLEND);
	glDisable( GL_LINE_SMOOTH );
}

/* groups are, on creation, centered around 0,0 */
static void node_draw_group(ScrArea *sa, SpaceNode *snode, bNode *gnode)
{
	bNodeTree *ngroup= (bNodeTree *)gnode->id;
	bNodeSocket *sock;
	rctf rect= gnode->totr;
	
	/* backdrop header */
	glEnable(GL_BLEND);
	uiSetRoundBox(3);
	BIF_ThemeColorShadeAlpha(TH_NODE_GROUP, 0, -70);
	gl_round_box(GL_POLYGON, rect.xmin, rect.ymax, rect.xmax, rect.ymax+NODE_DY, BASIS_RAD);
	
	/* backdrop body */
	BIF_ThemeColorShadeAlpha(TH_BACK, -8, -70);
	uiSetRoundBox(12);
	gl_round_box(GL_POLYGON, rect.xmin, rect.ymin, rect.xmax, rect.ymax, BASIS_RAD);
	
	/* selection outline */
	uiSetRoundBox(15);
	glColor4ub(200, 200, 200, 140);
	glEnable( GL_LINE_SMOOTH );
	gl_round_box(GL_LINE_LOOP, rect.xmin, rect.ymin, rect.xmax, rect.ymax+NODE_DY, BASIS_RAD);
	glDisable( GL_LINE_SMOOTH );
	glDisable(GL_BLEND);
	
	/* backdrop title */
	BIF_ThemeColor(TH_TEXT_HI);
	ui_rasterpos_safe(rect.xmin+8.0f, rect.ymax+5.0f, snode->aspect);
	BIF_DrawString(snode->curfont, ngroup->id.name+2, 0);
	
	/* links from groupsockets to the internal nodes */
	node_draw_group_links(snode, gnode);
	
	/* group sockets */
	for(sock= gnode->inputs.first; sock; sock= sock->next)
		if(!(sock->flag & SOCK_HIDDEN))
			socket_circle_draw(sock->locx, sock->locy, NODE_SOCKSIZE, sock->type, sock->flag & SELECT);
	for(sock= gnode->outputs.first; sock; sock= sock->next)
		if(!(sock->flag & SOCK_HIDDEN))
			socket_circle_draw(sock->locx, sock->locy, NODE_SOCKSIZE, sock->type, sock->flag & SELECT);

	/* and finally the whole tree */
	node_draw_nodetree(sa, snode, ngroup);
}


void drawnodespace(ScrArea *sa, void *spacedata)
{
	SpaceNode *snode= sa->spacedata.first;
	float col[3];
	
	BIF_GetThemeColor3fv(TH_BACK, col);
	glClearColor(col[0], col[1], col[2], 0.0);
	glClear(GL_COLOR_BUFFER_BIT);

	calc_scrollrcts(sa, &(snode->v2d), sa->winx, sa->winy);
	
	myortho2(snode->v2d.cur.xmin, snode->v2d.cur.xmax, snode->v2d.cur.ymin, snode->v2d.cur.ymax);
	bwin_clear_viewmat(sa->win);	/* clear buttons view */
	glLoadIdentity();
	
	/* always free, blocks here have no unique identifier (1 block per node) */
	uiFreeBlocksWin(&sa->uiblocks, sa->win);

	/* only set once */
	glBlendFunc( GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA );
	glEnable(GL_MAP1_VERTEX_3);

	/* aspect+font, set each time */
	snode->aspect= (snode->v2d.cur.xmax - snode->v2d.cur.xmin)/((float)sa->winx);
	snode->curfont= uiSetCurFont_ext(snode->aspect);

	/* backdrop */
	draw_nodespace_grid(snode);
	
	/* nodes */
	snode_set_context(snode);
	
	if(snode->nodetree) {
		bNode *node;
		
		/* for now, we set drawing coordinates on each redraw */
		for(node= snode->nodetree->nodes.first; node; node= node->next) {
			if(node->flag & NODE_GROUP_EDIT)
				node_update_group(node);
			else if(node->flag & NODE_HIDDEN)
				node_update_hidden(node);
			else
				node_update(node);
		}

		node_draw_nodetree(sa, snode, snode->nodetree);
			
		/* active group */
		for(node= snode->nodetree->nodes.first; node; node= node->next) {
			if(node->flag & NODE_GROUP_EDIT)
				node_draw_group(sa, snode, node);
		}
	}
	
	/* restore viewport (not needed yet) */
	mywinset(sa->win);

	/* ortho at pixel level curarea */
	myortho2(-0.375, sa->winx-0.375, -0.375, sa->winy-0.375);

	draw_area_emboss(sa);
	curarea->win_swap= WIN_BACK_OK;
	
	/* in the end, this is a delayed previewrender test, to allow buttons to be first */
	if(snode->flag & SNODE_DO_PREVIEW) {
		addafterqueue(sa->win, RENDERPREVIEW, 1);
		snode->flag &= ~SNODE_DO_PREVIEW;
	}
}

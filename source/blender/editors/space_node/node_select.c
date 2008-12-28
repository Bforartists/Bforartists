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
 * The Original Code is Copyright (C) 2008 Blender Foundation.
 * All rights reserved.
 *
 * 
 * Contributor(s): Blender Foundation, Nathan Letwory
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#include <stdio.h>

#include "DNA_node_types.h"
#include "DNA_scene_types.h"
#include "DNA_screen_types.h"
#include "DNA_space_types.h"

#include "BKE_context.h"
#include "BKE_node.h"
#include "BKE_global.h"

#include "BLI_rect.h"

#include "ED_space_api.h"
#include "ED_screen.h"
#include "ED_types.h"

#include "RNA_access.h"
#include "RNA_define.h"

#include "WM_api.h"
#include "WM_types.h"

#include "UI_view2d.h"
 
#include "node_intern.h"
 
/* ************************** Node generic ************** */

/* allows to walk the list in order of visibility */
static bNode *next_node(bNodeTree *ntree)
{
	static bNode *current=NULL, *last= NULL;
	
	if(ntree) {
		/* set current to the first selected node */
		for(current= ntree->nodes.last; current; current= current->prev)
			if(current->flag & NODE_SELECT)
				break;
		
		/* set last to the first unselected node */
		for(last= ntree->nodes.last; last; last= last->prev)
			if((last->flag & NODE_SELECT)==0)
				break;
		
		if(current==NULL)
			current= last;
		
		return NULL;
	}
	/* no nodes, or we are ready */
	if(current==NULL)
		return NULL;
	
	/* now we walk the list backwards, but we always return current */
	if(current->flag & NODE_SELECT) {
		bNode *node= current;
		
		/* find previous selected */
		current= current->prev;
		while(current && (current->flag & NODE_SELECT)==0)
			current= current->prev;
		
		/* find first unselected */
		if(current==NULL)
			current= last;
		
		return node;
	}
	else {
		bNode *node= current;
		
		/* find previous unselected */
		current= current->prev;
		while(current && (current->flag & NODE_SELECT))
			current= current->prev;
		
		return node;
	}
	
	return NULL;
}

static int do_header_node(SpaceNode *snode, bNode *node, float mx, float my)
{
	rctf totr= node->totr;
	
	totr.ymin= totr.ymax-20.0f;
	
	totr.xmax= totr.xmin+15.0f;
	if(BLI_in_rctf(&totr, mx, my)) {
		node->flag |= NODE_HIDDEN;
		// allqueue(REDRAWNODE, 0);
		return 1;
	}	
	
	totr.xmax= node->totr.xmax;
	totr.xmin= totr.xmax-18.0f;
	if(node->typeinfo->flag & NODE_PREVIEW) {
		if(BLI_in_rctf(&totr, mx, my)) {
			node->flag ^= NODE_PREVIEW;
			// allqueue(REDRAWNODE, 0);
			return 1;
		}
		totr.xmin-=18.0f;
	}
	if(node->type == NODE_GROUP) {
		if(BLI_in_rctf(&totr, mx, my)) {
			snode_make_group_editable(snode, node);
			return 1;
		}
		totr.xmin-=18.0f;
	}
	if(node->typeinfo->flag & NODE_OPTIONS) {
		if(BLI_in_rctf(&totr, mx, my)) {
			node->flag ^= NODE_OPTIONS;
			// allqueue(REDRAWNODE, 0);
			return 1;
		}
		totr.xmin-=18.0f;
	}
	/* hide unused sockets */
	if(BLI_in_rctf(&totr, mx, my)) {
		// XXX node_hide_unhide_sockets(snode, node);
	}
	
	
	totr= node->totr;
	totr.xmin= totr.xmax-10.0f;
	totr.ymax= totr.ymin+10.0f;
	if(BLI_in_rctf(&totr, mx, my)) {
		// XXX scale_node(snode, node);
		return 1;
	}
	return 0;
}

static int do_header_hidden_node(SpaceNode *snode, bNode *node, float mx, float my)
{
	rctf totr= node->totr;
	
	totr.xmax= totr.xmin+15.0f;
	if(BLI_in_rctf(&totr, mx, my)) {
		node->flag &= ~NODE_HIDDEN;
		// allqueue(REDRAWNODE, 0);
		return 1;
	}	
	
	totr.xmax= node->totr.xmax;
	totr.xmin= node->totr.xmax-15.0f;
	if(BLI_in_rctf(&totr, mx, my)) {
		scale_node(snode, node);
		return 1;
	}
	return 0;
}

static node_mouse_select(SpaceNode *snode, ARegion *ar, short *mval)
{
	bNode *node;
	float mx, my;
	
	mx= (float)mval[0];
	my= (float)mval[1];
	
	UI_view2d_region_to_view(&ar->v2d, mval[0], mval[1], &mx, &my);
	
	for(next_node(snode->edittree); (node=next_node(NULL));) {
		
		/* first check for the headers or scaling widget */
		/* XXX if(node->flag & NODE_HIDDEN) {
			if(do_header_hidden_node(snode, node, mx, my))
				return 1;
		}
		else {
			if(do_header_node(snode, node, mx, my))
				return 1;
		}*/
		
		/* node body */
		if(BLI_in_rctf(&node->totr, mx, my))
			break;
	}
	if(node) {
		// XXX if((G.qual & LR_SHIFTKEY)==0)
		//	node_deselectall(snode, 0);
		
		// XXX
		/*
		if(G.qual & LR_SHIFTKEY) {
			if(node->flag & SELECT)
				node->flag &= ~SELECT;
			else
				node->flag |= SELECT;
		}
		else */
			node->flag |= SELECT;
		
		node_set_active(snode, node);
		
		/* viewer linking */
		//if(G.qual & LR_CTRLKEY)
		//	node_link_viewer(snode, node);
		
		/* not so nice (no event), but function below delays redraw otherwise */
		//force_draw(0);
		
		//std_rmouse_transform(node_transform_ext);	/* does undo push for select */
		
		return 1;
	}
	return 0;
}

static int node_select_exec(bContext *C, wmOperator *op)
{
	SpaceNode *snode= (SpaceNode*)CTX_wm_space_data(C);
	ScrArea *sa= CTX_wm_area(C);
	ARegion *ar= CTX_wm_region(C);
	int select_type;
	short mval[2];

	select_type = RNA_enum_get(op->ptr, "select_type");
	
	switch (select_type) {
		case NODE_SELECT_MOUSE:
			mval[0] = RNA_int_get(op->ptr, "mx");
			mval[1] = RNA_int_get(op->ptr, "my");
			node_mouse_select(snode, ar, mval);
			break;
	}
	return OPERATOR_FINISHED;
}

static int node_select_invoke(bContext *C, wmOperator *op, wmEvent *event)
{
	ScrArea *sa= CTX_wm_area(C);
	ARegion *ar= CTX_wm_region(C);
	short mval[2];	
	
	mval[0]= event->x - ar->winrct.xmin;
	mval[1]= event->y - ar->winrct.ymin;
	
	RNA_int_set(op->ptr, "mx", mval[0]);
	RNA_int_set(op->ptr, "my", mval[1]);

	return node_select_exec(C,op);
}

/* operators */

static EnumPropertyItem prop_select_items[] = {
	{NODE_SELECT_MOUSE, "NORMAL", "Normal Select", "Select using the mouse"},
	{0, NULL, NULL, NULL}};

void NODE_OT_select(wmOperatorType *ot)
{
	PropertyRNA *prop;
	
	/* identifiers */
	ot->name= "Activate/Select";
	ot->idname= "NODE_OT_select";
	
	/* api callbacks */
	ot->invoke= node_select_invoke;
	ot->poll= ED_operator_node_active;
	
	prop = RNA_def_property(ot->srna, "select_type", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_items(prop, prop_select_items);
	
	prop = RNA_def_property(ot->srna, "mx", PROP_INT, PROP_NONE);
	prop = RNA_def_property(ot->srna, "my", PROP_INT, PROP_NONE);
}

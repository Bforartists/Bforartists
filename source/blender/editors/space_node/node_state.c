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


static int do_header_node(SpaceNode *snode, bNode *node, float mx, float my)
{
	rctf totr= node->totr;
	
	totr.ymin= totr.ymax-20.0f;
	
	totr.xmax= totr.xmin+15.0f;
	if(BLI_in_rctf(&totr, mx, my)) {
		node->flag |= NODE_HIDDEN;
		return 1;
	}	
	
	totr.xmax= node->totr.xmax;
	totr.xmin= totr.xmax-18.0f;
	if(node->typeinfo->flag & NODE_PREVIEW) {
		if(BLI_in_rctf(&totr, mx, my)) {
			node->flag ^= NODE_PREVIEW;
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

static void node_toggle_visibility(SpaceNode *snode, ARegion *ar, short *mval)
{
	bNode *node;
	float mx, my;
	
	mx= (float)mval[0];
	my= (float)mval[1];
	
	UI_view2d_region_to_view(&ar->v2d, mval[0], mval[1], &mx, &my);
	
	for(next_node(snode->edittree); (node=next_node(NULL));) {
		if(node->flag & NODE_HIDDEN) {
			if(do_header_hidden_node(snode, node, mx, my)) {
				ED_region_tag_redraw(ar);
				break;
			}
		}
		else {
			if(do_header_node(snode, node, mx, my)) {
				ED_region_tag_redraw(ar);
				break;
			}
		}
	}
}

static int node_toggle_visibility_exec(bContext *C, wmOperator *op)
{
	SpaceNode *snode= (SpaceNode*)CTX_wm_space_data(C);
	ARegion *ar= CTX_wm_region(C);
	short mval[2];

	mval[0] = RNA_int_get(op->ptr, "mx");
	mval[1] = RNA_int_get(op->ptr, "my");
	node_toggle_visibility(snode, ar, mval);

	return OPERATOR_FINISHED;
}

static int node_toggle_visibility_invoke(bContext *C, wmOperator *op, wmEvent *event)
{
	ARegion *ar= CTX_wm_region(C);
	short mval[2];	
	
	mval[0]= event->x - ar->winrct.xmin;
	mval[1]= event->y - ar->winrct.ymin;
	
	RNA_int_set(op->ptr, "mx", mval[0]);
	RNA_int_set(op->ptr, "my", mval[1]);

	return node_toggle_visibility_exec(C,op);
}

void NODE_OT_toggle_visibility(wmOperatorType *ot)
{
	PropertyRNA *prop;
	
	/* identifiers */
	ot->name= "Toggle Visibility";
	ot->idname= "NODE_OT_toggle_visibility";
	
	/* api callbacks */
	ot->invoke= node_toggle_visibility_invoke;
	ot->poll= ED_operator_node_active;
	
	prop = RNA_def_property(ot->srna, "mx", PROP_INT, PROP_NONE);
	prop = RNA_def_property(ot->srna, "my", PROP_INT, PROP_NONE);
}

static int node_fit_all_exec(bContext *C, wmOperator *op)
{
	ScrArea *sa= CTX_wm_area(C);
	ARegion *ar= CTX_wm_region(C);
	SpaceNode *snode= (SpaceNode *)CTX_wm_space_data(C);
	snode_home(sa, ar, snode);
	ED_region_tag_redraw(ar);
	return OPERATOR_FINISHED;
}

static int node_fit_all_invoke(bContext *C, wmOperator *op, wmEvent *event)
{
	return node_fit_all_exec(C, op);
}

void NODE_OT_fit_all(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Fit All";
	ot->idname= "NODE_OT_fit_all";
	
	/* api callbacks */
	ot->invoke= node_fit_all_invoke;
	ot->poll= ED_operator_node_active;
}
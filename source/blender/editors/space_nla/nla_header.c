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
 * The Original Code is Copyright (C) 2008 Blender Foundation.
 * All rights reserved.
 *
 * 
 * Contributor(s): Blender Foundation
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#include <string.h>
#include <stdio.h>

#include "DNA_anim_types.h"
#include "DNA_action_types.h"
#include "DNA_nla_types.h"
#include "DNA_object_types.h"
#include "DNA_space_types.h"
#include "DNA_scene_types.h"
#include "DNA_screen_types.h"
#include "DNA_windowmanager_types.h"

#include "MEM_guardedalloc.h"

#include "BLI_blenlib.h"
#include "BLI_arithb.h"
#include "BLI_rand.h"

#include "BKE_animsys.h"
#include "BKE_nla.h"
#include "BKE_context.h"
#include "BKE_report.h"
#include "BKE_screen.h"
#include "ED_types.h"
#include "ED_util.h"

#include "ED_anim_api.h"
#include "ED_space_api.h"
#include "ED_screen.h"

#include "BIF_gl.h"
#include "BIF_transform.h"

#include "RNA_access.h"

#include "WM_api.h"
#include "WM_types.h"

#include "UI_interface.h"
#include "UI_resources.h"
#include "UI_view2d.h"

#include "ED_markers.h"

#include "nla_intern.h"

/* button events */
enum {
	B_REDR 	= 0,
} eActHeader_ButEvents;

/* ************************ header area region *********************** */


static void nla_viewmenu(bContext *C, uiLayout *layout, void *arg_unused)
{
	bScreen *sc= CTX_wm_screen(C);
	ScrArea *sa= CTX_wm_area(C);
	Scene *scene= CTX_data_scene(C);
	SpaceNla *snla= (SpaceNla*)CTX_wm_space_data(C);
	PointerRNA spaceptr;
	
	/* retrieve state */
	RNA_pointer_create(&sc->id, &RNA_SpaceNLA, snla, &spaceptr);
	
	/* create menu */
	uiItemO(layout, NULL, ICON_MENU_PANEL, "NLA_OT_properties");
	
	uiItemS(layout);
	
	uiItemR(layout, NULL, 0, &spaceptr, "show_cframe_indicator", 0, 0, 0);
	
	if (snla->flag & SNLA_DRAWTIME)
		uiItemO(layout, "Show Frames", 0, "ANIM_OT_time_toggle");
	else
		uiItemO(layout, "Show Seconds", 0, "ANIM_OT_time_toggle");

	uiItemS(layout);
	
	if (scene->flag & SCE_NLA_EDIT_ON) 
		uiItemO(layout, NULL, 0, "NLA_OT_tweakmode_exit");
	else
		uiItemO(layout, NULL, 0, "NLA_OT_tweakmode_enter");
	
	uiItemS(layout);
	
	uiItemO(layout, NULL, 0, "ANIM_OT_previewrange_set");
	uiItemO(layout, NULL, 0, "ANIM_OT_previewrange_clear");
	
	uiItemS(layout);
	
	//uiItemO(layout, NULL, 0, "NLA_OT_view_all");
	
	if (sa->full) 
		uiItemO(layout, NULL, 0, "SCREEN_OT_screen_full_area"); // "Tile Window", Ctrl UpArrow
	else 
		uiItemO(layout, NULL, 0, "SCREEN_OT_screen_full_area"); // "Maximize Window", Ctr DownArrow
}

static void nla_selectmenu(bContext *C, uiLayout *layout, void *arg_unused)
{
	uiItemO(layout, NULL, 0, "NLA_OT_select_all_toggle");
	uiItemBooleanO(layout, "Invert All", 0, "NLA_OT_select_all_toggle", "invert", 1);
	
	uiItemS(layout);
	
	uiItemO(layout, NULL, 0, "NLA_OT_select_border");
	uiItemBooleanO(layout, "Border Axis Range", 0, "NLA_OT_select_border", "axis_range", 1);
}

static void nla_edit_transformmenu(bContext *C, uiLayout *layout, void *arg_unused)
{
	// XXX these operators may change for NLA...
	uiItemEnumO(layout, "Grab/Move", 0, "TFM_OT_transform", "mode", TFM_TIME_TRANSLATE);
	uiItemEnumO(layout, "Extend", 0, "TFM_OT_transform", "mode", TFM_TIME_EXTEND);
	uiItemEnumO(layout, "Scale", 0, "TFM_OT_transform", "mode", TFM_TIME_SCALE);
}

static void nla_edit_snapmenu(bContext *C, uiLayout *layout, void *arg_unused)
{
	uiItemEnumO(layout, NULL, 0, "NLA_OT_snap", "type", NLAEDIT_SNAP_CFRA);
	uiItemEnumO(layout, NULL, 0, "NLA_OT_snap", "type", NLAEDIT_SNAP_NEAREST_FRAME);
	uiItemEnumO(layout, NULL, 0, "NLA_OT_snap", "type", NLAEDIT_SNAP_NEAREST_SECOND);
	uiItemEnumO(layout, NULL, 0, "NLA_OT_snap", "type", NLAEDIT_SNAP_NEAREST_MARKER);
}

static void nla_editmenu(bContext *C, uiLayout *layout, void *arg_unused)
{
	uiItemMenuF(layout, "Transform", 0, nla_edit_transformmenu);
	uiItemMenuF(layout, "Snap", 0, nla_edit_snapmenu);
	
	uiItemS(layout);
	
	uiItemO(layout, NULL, 0, "NLA_OT_duplicate");
	uiItemO(layout, NULL, 0, "NLA_OT_split");
	
	uiItemS(layout);
	
	uiItemO(layout, NULL, 0, "NLA_OT_delete");
	
	uiItemS(layout);
	
	uiItemO(layout, NULL, 0, "NLA_OT_apply_scale");
	uiItemO(layout, NULL, 0, "NLA_OT_clear_scale");
	
	uiItemS(layout);
	
	uiItemO(layout, NULL, 0, "NLA_OT_move_up");
	uiItemO(layout, NULL, 0, "NLA_OT_move_down");
}

static void nla_addmenu(bContext *C, uiLayout *layout, void *arg_unused)
{
	uiItemO(layout, NULL, 0, "NLA_OT_add_actionclip");
	uiItemO(layout, NULL, 0, "NLA_OT_add_transition");
	
	uiItemS(layout);
	
	uiItemO(layout, NULL, 0, "NLA_OT_add_meta");
	uiItemO(layout, NULL, 0, "NLA_OT_remove_meta");
	
	uiItemS(layout);
	
	uiItemO(layout, NULL, 0, "NLA_OT_add_tracks");
	uiItemBooleanO(layout, "Add Tracks Above Selected", 0, "NLA_OT_add_tracks", "above_selected", 1);
}

/* ------------------ */

static void do_nla_buttons(bContext *C, void *arg, int event)
{
	switch (event) {
		case B_REDR:
			ED_area_tag_redraw(CTX_wm_area(C));
			break;
	}
}


void nla_header_buttons(const bContext *C, ARegion *ar)
{
	SpaceNla *snla= (SpaceNla *)CTX_wm_space_data(C);
	ScrArea *sa= CTX_wm_area(C);
	uiBlock *block;
	int xco, yco= 3;
	
	block= uiBeginBlock(C, ar, "header buttons", UI_EMBOSS);
	uiBlockSetHandleFunc(block, do_nla_buttons, NULL);
	
	xco= ED_area_header_standardbuttons(C, block, yco);
	
	if ((sa->flag & HEADER_NO_PULLDOWN)==0) {
		int xmax;
		
		xmax= GetButStringLength("View");
		uiDefMenuBut(block, nla_viewmenu, NULL, "View", xco, yco, xmax-3, 20, "");
		xco+= xmax;
		
		xmax= GetButStringLength("Select");
		uiDefMenuBut(block, nla_selectmenu, NULL, "Select", xco, yco, xmax-3, 20, "");
		xco+= xmax;
		
		xmax= GetButStringLength("Edit");
		uiDefMenuBut(block, nla_editmenu, NULL, "Edit", xco, yco, xmax-3, 20, "");
		xco+= xmax;
		
		xmax= GetButStringLength("Add");
		uiDefMenuBut(block, nla_addmenu, NULL, "Add", xco, yco, xmax-3, 20, "");
		xco+= xmax;
	}
	
	uiBlockSetEmboss(block, UI_EMBOSS);
	
	/* filtering buttons */
	if (snla->ads) {
		uiBlockBeginAlign(block);
			uiDefIconButBitI(block, TOG, ADS_FILTER_ONLYSEL, B_REDR, ICON_RESTRICT_SELECT_OFF,	(short)(xco+=XIC),yco,XIC,YIC, &(snla->ads->filterflag), 0, 0, 0, 0, "Only display selected Objects");
			uiDefIconButBitI(block, TOGN, ADS_FILTER_NLA_NOACT, B_REDR, ICON_ACTION,	(short)(xco+=XIC),yco,XIC,YIC, &(snla->ads->filterflag), 0, 0, 0, 0, "Include AnimData blocks with no NLA Data");
		uiBlockEndAlign(block);
		xco += 5;
		
		uiBlockBeginAlign(block);
			uiDefIconButBitI(block, TOGN, ADS_FILTER_NOSCE, B_REDR, ICON_SCENE_DATA,	(short)(xco+=XIC),yco,XIC,YIC, &(snla->ads->filterflag), 0, 0, 0, 0, "Display Scene Animation");
			uiDefIconButBitI(block, TOGN, ADS_FILTER_NOWOR, B_REDR, ICON_WORLD_DATA,	(short)(xco+=XIC),yco,XIC,YIC, &(snla->ads->filterflag), 0, 0, 0, 0, "Display World Animation");
			uiDefIconButBitI(block, TOGN, ADS_FILTER_NOSHAPEKEYS, B_REDR, ICON_SHAPEKEY_DATA,	(short)(xco+=XIC),yco,XIC,YIC, &(snla->ads->filterflag), 0, 0, 0, 0, "Display ShapeKeys");
			uiDefIconButBitI(block, TOGN, ADS_FILTER_NOMAT, B_REDR, ICON_MATERIAL_DATA,	(short)(xco+=XIC),yco,XIC,YIC, &(snla->ads->filterflag), 0, 0, 0, 0, "Display Materials");
			uiDefIconButBitI(block, TOGN, ADS_FILTER_NOLAM, B_REDR, ICON_LAMP_DATA,	(short)(xco+=XIC),yco,XIC,YIC, &(snla->ads->filterflag), 0, 0, 0, 0, "Display Lamps");
			uiDefIconButBitI(block, TOGN, ADS_FILTER_NOCAM, B_REDR, ICON_CAMERA_DATA,	(short)(xco+=XIC),yco,XIC,YIC, &(snla->ads->filterflag), 0, 0, 0, 0, "Display Cameras");
			uiDefIconButBitI(block, TOGN, ADS_FILTER_NOCUR, B_REDR, ICON_CURVE_DATA,	(short)(xco+=XIC),yco,XIC,YIC, &(snla->ads->filterflag), 0, 0, 0, 0, "Display Curves");
		uiBlockEndAlign(block);
		xco += 15;
	}
	else {
		// XXX this case shouldn't happen at all... for now, just pad out same amount of space
		xco += 7*XIC + 15;
	}
	xco += (XIC + 8);
	
	/* auto-snap selector */
	if (snla->flag & SNLA_DRAWTIME) {
		uiDefButS(block, MENU, B_REDR,
				"Auto-Snap Keyframes %t|No Time-Snap %x0|Nearest Second %x2|Nearest Marker %x3", 
				xco,yco,90,YIC, &snla->autosnap, 0, 1, 0, 0, 
				"Auto-snapping mode for times when transforming");
	}
	else {
		uiDefButS(block, MENU, B_REDR, 
				"Auto-Snap Keyframes %t|No Time-Snap %x0|Nearest Frame %x2|Nearest Marker %x3", 
				xco,yco,90,YIC, &snla->autosnap, 0, 1, 0, 0, 
				"Auto-snapping mode for times when transforming");
	}
	xco += 98;
	
	/* always as last  */
	UI_view2d_totRect_set(&ar->v2d, xco+XIC+80, ar->v2d.tot.ymax-ar->v2d.tot.ymin);
	
	uiEndBlock(C, block);
	uiDrawBlock(C, block);
}



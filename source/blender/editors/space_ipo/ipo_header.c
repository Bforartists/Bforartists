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
#include "DNA_space_types.h"
#include "DNA_scene_types.h"
#include "DNA_screen_types.h"
#include "DNA_windowmanager_types.h"

#include "MEM_guardedalloc.h"

#include "BLI_blenlib.h"

#include "BKE_context.h"
#include "BKE_screen.h"

#include "ED_anim_api.h"
#include "ED_screen.h"
#include "ED_types.h"
#include "ED_util.h"

#include "WM_api.h"
#include "WM_types.h"

#include "BIF_gl.h"
#include "BIF_glutil.h"

#include "UI_interface.h"
#include "UI_resources.h"
#include "UI_view2d.h"

#include "ipo_intern.h"

/* ********************************************************* */
/* Menu Defines... */

/* button events */
enum {
	B_REDR 	= 0,
	B_GRAPHCOPYKEYS,
	B_GRAPHPASTEKEYS,
} eActHeader_ButEvents;

/* ************************ header area region *********************** */

static void do_viewmenu(bContext *C, void *arg, int event)
{
	SpaceIpo *sipo= (SpaceIpo *)CTX_wm_space_data(C);
	
	switch (event) {
		case 1: /* Show time/frames */
			sipo->flag ^= SIPO_DRAWTIME;
			break;
		case 2: /* AutoMerge Keyframes */
			sipo->flag ^= SIPO_NOTRANSKEYCULL;
			break;
		case 3: /* Show/Hide handles */
			sipo->flag ^= SIPO_NOHANDLES;
			break;
		case 4: /* Show current frame number beside indicator */
			sipo->flag ^= SIPO_NODRAWCFRANUM;
			break;
	}
}

static uiBlock *graph_viewmenu(bContext *C, ARegion *ar, void *arg_unused)
{
	ScrArea *curarea= CTX_wm_area(C);
	SpaceIpo *sipo= (SpaceIpo *)CTX_wm_space_data(C);
	uiBlock *block;
	short yco= 0, menuwidth=120;
	
	block= uiBeginBlock(C, ar, "graph_viewmenu", UI_EMBOSSP, UI_HELV);
	uiBlockSetButmFunc(block, do_viewmenu, NULL);
	
		// XXX these options should use new menu-options
	
	if (sipo->flag & SIPO_DRAWTIME) {
		uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, 
					 "Show Frames|Ctrl T", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 1, "");
	}
	else {
		uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, 
					 "Show Seconds|Ctrl T", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 1, "");
	}
	
	
	uiDefIconTextBut(block, BUTM, 1, (sipo->flag & SIPO_NOTRANSKEYCULL)?ICON_CHECKBOX_DEHLT:ICON_CHECKBOX_HLT, 
					 "AutoMerge Keyframes|", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 2, "");
	uiDefIconTextBut(block, BUTM, 1, (sipo->flag & SIPO_NOHANDLES)?ICON_CHECKBOX_DEHLT:ICON_CHECKBOX_HLT, 
					 "Show Handles|Ctrl H", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 3, "");
	uiDefIconTextBut(block, BUTM, 1, (sipo->flag & SIPO_NODRAWCFRANUM)?ICON_CHECKBOX_DEHLT:ICON_CHECKBOX_HLT, 
					 "Show Current Frame Number|", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 4, "");
	
	if (curarea->headertype==HEADERTOP) {
		uiBlockSetDirection(block, UI_DOWN);
	}
	else {
		uiBlockSetDirection(block, UI_TOP);
		uiBlockFlipOrder(block);
	}
	
	uiTextBoundsBlock(block, 50);
	uiEndBlock(C, block);
	
	return block;
}

static void do_graph_buttons(bContext *C, void *arg, int event)
{
	switch (event) {
		case B_REDR:
			ED_area_tag_redraw(CTX_wm_area(C));
			break;
	}
}


void graph_header_buttons(const bContext *C, ARegion *ar)
{
	ScrArea *sa= CTX_wm_area(C);
	SpaceIpo *sipo= (SpaceIpo *)CTX_wm_space_data(C);
	uiBlock *block;
	int xco, yco= 3;
	
	block= uiBeginBlock(C, ar, "header buttons", UI_EMBOSS, UI_HELV);
	uiBlockSetHandleFunc(block, do_graph_buttons, NULL);
	
	xco= ED_area_header_standardbuttons(C, block, yco);
	
	if ((sa->flag & HEADER_NO_PULLDOWN)==0) {
		int xmax;
		
		/* pull down menus */
		uiBlockSetEmboss(block, UI_EMBOSSP);
		
		xmax= GetButStringLength("View");
		uiDefPulldownBut(block, graph_viewmenu, CTX_wm_area(C), 
						 "View", xco, yco-2, xmax-3, 24, "");
		xco+= xmax;
	}
	
	uiBlockSetEmboss(block, UI_EMBOSS);
	
	/* mode selector */
	uiDefButS(block, MENU, B_REDR, 
			"Editor Mode %t|F-Curve Editor %x0|Drivers %x1", 
			xco,yco,110,YIC, &sipo->mode, 0, 1, 0, 0, 
			"Editing modes for this editor");
	xco+= 120;
	
	/* filtering buttons */
	if (sipo->ads) {
		//uiBlockBeginAlign(block);
			uiDefIconButBitI(block, TOG, ADS_FILTER_ONLYSEL, B_REDR, ICON_RESTRICT_SELECT_OFF,	(short)(xco+=XIC),yco,XIC,YIC, &(sipo->ads->filterflag), 0, 0, 0, 0, "Only display selected Objects");
		//uiBlockEndAlign(block);
		xco += 5;
		
		uiBlockBeginAlign(block);
			//uiDefIconButBitI(block, TOGN, ADS_FILTER_NOOBJ, B_REDR, ICON_OBJECT,	(short)(xco+=XIC),yco,XIC,YIC, &(sipo->ads->filterflag), 0, 0, 0, 0, "Display Non-Armature Objects");
			//uiDefIconButBitI(block, TOGN, ADS_FILTER_NOARM, B_REDR, ICON_ARMATURE,	(short)(xco+=XIC),yco,XIC,YIC, &(sipo->ads->filterflag), 0, 0, 0, 0, "Display Armature Objects");
			uiDefIconButBitI(block, TOGN, ADS_FILTER_NOSHAPEKEYS, B_REDR, ICON_EDIT,	(short)(xco+=XIC),yco,XIC,YIC, &(sipo->ads->filterflag), 0, 0, 0, 0, "Display ShapeKeys");
			uiDefIconButBitI(block, TOGN, ADS_FILTER_NOMAT, B_REDR, ICON_MATERIAL,	(short)(xco+=XIC),yco,XIC,YIC, &(sipo->ads->filterflag), 0, 0, 0, 0, "Display Materials");
			uiDefIconButBitI(block, TOGN, ADS_FILTER_NOLAM, B_REDR, ICON_LAMP,	(short)(xco+=XIC),yco,XIC,YIC, &(sipo->ads->filterflag), 0, 0, 0, 0, "Display Lamps");
			uiDefIconButBitI(block, TOGN, ADS_FILTER_NOCAM, B_REDR, ICON_CAMERA,	(short)(xco+=XIC),yco,XIC,YIC, &(sipo->ads->filterflag), 0, 0, 0, 0, "Display Cameras");
			uiDefIconButBitI(block, TOGN, ADS_FILTER_NOCUR, B_REDR, ICON_CURVE,	(short)(xco+=XIC),yco,XIC,YIC, &(sipo->ads->filterflag), 0, 0, 0, 0, "Display Curves");
		uiBlockEndAlign(block);
		xco += 30;
	}
	else {
		// XXX this case shouldn't happen at all... for now, just pad out same amount of space
		xco += 6*XIC + 35;
	}
	
	/* copy + paste */
	uiBlockBeginAlign(block);
		uiDefIconBut(block, BUT, B_GRAPHCOPYKEYS, ICON_COPYDOWN,	xco,yco,XIC,YIC, 0, 0, 0, 0, 0, "Copies the selected keyframes from the selected channel(s) to the buffer");
		uiDefIconBut(block, BUT, B_GRAPHPASTEKEYS, ICON_PASTEDOWN,	xco+=XIC,yco,XIC,YIC, 0, 0, 0, 0, 0, "Pastes the keyframes from the buffer");
	uiBlockEndAlign(block);
	xco += (XIC + 8);
	
	/* auto-snap selector */
	if (sipo->flag & SIPO_DRAWTIME) {
		uiDefButS(block, MENU, B_REDR,
				"Auto-Snap Keyframes %t|No Time-Snap %x0|Nearest Second %x2|Nearest Marker %x3", 
				xco,yco,90,YIC, &sipo->autosnap, 0, 1, 0, 0, 
				"Auto-snapping mode for keyframe times when transforming");
	}
	else {
		uiDefButS(block, MENU, B_REDR, 
				"Auto-Snap Keyframes %t|No Time-Snap %x0|Nearest Frame %x2|Nearest Marker %x3", 
				xco,yco,90,YIC, &sipo->autosnap, 0, 1, 0, 0, 
				"Auto-snapping mode for keyframe times when transforming");
	}
	
	/* always as last  */
	UI_view2d_totRect_set(&ar->v2d, xco+XIC+80, (int)(ar->v2d.tot.ymax - ar->v2d.tot.ymin));
	
	uiEndBlock(C, block);
	uiDrawBlock(C, block);
}



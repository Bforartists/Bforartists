/**
 * header_nla.c oct-2003
 *
 * Functions to draw the "NLA Editor" window header
 * and handle user events sent to it.
 * 
 * $Id$
 *
 * ***** BEGIN GPL/BL DUAL LICENSE BLOCK *****
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version. The Blender
 * Foundation also sells licenses for use in proprietary software under
 * the Blender License.  See http://www.blender.org/BL/ for information
 * about this.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software Foundation,
 * Inc., 59 Temple Place - Suite 330, Boston, MA	02111-1307, USA.
 *
 * The Original Code is Copyright (C) 2001-2002 by NaN Holding BV.
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): none yet.
 *
 * ***** END GPL/BL DUAL LICENSE BLOCK *****
 */

#include <stdlib.h>
#include <string.h>
#include <stdio.h>

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

#include "DNA_ID.h"
#include "DNA_nla_types.h"
#include "DNA_scene_types.h"
#include "DNA_screen_types.h"
#include "DNA_space_types.h"

#include "BKE_global.h"
#include "BKE_main.h"
#include "BKE_utildefines.h"

#include "BIF_interface.h"
#include "BIF_resources.h"
#include "BIF_screen.h"
#include "BIF_space.h"
#include "BIF_editnla.h"
#include "BIF_editaction.h"
#include "BIF_toolbox.h"

#include "BSE_drawipo.h"
#include "BSE_headerbuttons.h"
#include "BSE_time.h"

//#include "nla.h"

#include "blendef.h"
#include "mydevice.h"

void do_nla_buttons(unsigned short event)
{
	View2D *v2d;

	switch(event){
	case B_NLAHOME:
		//	Find X extents
		v2d= &(G.snla->v2d);
		
		/* i tried to understand nla/action drawing to reveil a 'tot' rect, impossible code! (ton) */
		v2d->cur.xmin = G.scene->r.sfra-5;
		v2d->cur.xmax = G.scene->r.efra+5;
		v2d->cur.ymin= -SCROLLB;
		v2d->cur.ymax= 5; // at least stuff is visiable then?
		
		test_view2d(G.v2d, curarea->winx, curarea->winy);
		view2d_do_locks(curarea, V2D_LOCK_COPY);
		addqueue (curarea->win, REDRAW, 1);
		break;
	}
}


static void do_nla_viewmenu(void *arg, int event)
{
	extern int play_anim(int mode);
	
	switch(event) {
	case 0: /* Update Automatically */
		if(BTST(G.snla->lock, 0)) G.snla->lock = BCLR(G.snla->lock, 0);
		else G.snla->lock = BSET(G.snla->lock, 0);
		break;
	case 1: /* Play Back Animation */
		play_anim(0);
		break;
	case 2: /* Play Back Animation in 3D View */
		play_anim(1);
		break;
	case 3: /* View All */
		do_nla_buttons(B_NLAHOME);
		break;
	case 4: /* Maximize Window */
		/* using event B_FULL */
		break;
	case 5:
		G.v2d->flag ^= V2D_VIEWLOCK;
		if(G.v2d->flag & V2D_VIEWLOCK)
			view2d_do_locks(curarea, 0);
		break;			
	}
}

static uiBlock *nla_viewmenu(void *arg_unused)
{
/*	static short tog=0; */
	uiBlock *block;
	short yco= 0, menuwidth=120;
	
	block= uiNewBlock(&curarea->uiblocks, "nla_viewmenu", UI_EMBOSSP, UI_HELV, curarea->headwin);
	uiBlockSetButmFunc(block, do_nla_viewmenu, NULL);
		
	if(BTST(G.snla->lock, 0)) {
		uiDefIconTextBut(block, BUTM, 1, ICON_CHECKBOX_HLT, "Update Automatically|", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 0, "");
	} else {
		uiDefIconTextBut(block, BUTM, 1, ICON_CHECKBOX_DEHLT, "Update Automatically|", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 0, "");
	}

	uiDefBut(block, SEPR, 0, "",					0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Play Back Animation|Alt A", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 1, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Play Back Animation in 3D View|Alt Shift A", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 2, "");
	
	uiDefBut(block, SEPR, 0, "",					0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "View All|Home", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 3, "");
	uiDefIconTextBut(block, BUTM, 1, (G.v2d->flag & V2D_VIEWLOCK)?ICON_CHECKBOX_HLT:ICON_CHECKBOX_DEHLT, 
					 "Lock Time to Other Windows|", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 5, "");
	
	if(!curarea->full) uiDefIconTextBut(block, BUTM, B_FULL, ICON_BLANK1, "Maximize Window|Ctrl UpArrow", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 4, "");
	else uiDefIconTextBut(block, BUTM, B_FULL, ICON_BLANK1, "Tile Window|Ctrl DownArrow", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 4, "");
	
	if(curarea->headertype==HEADERTOP) {
		uiBlockSetDirection(block, UI_DOWN);
	}
	else {
		uiBlockSetDirection(block, UI_TOP);
		uiBlockFlipOrder(block);
	}

	uiTextBoundsBlock(block, 50);
	
	return block;
}

static void do_nla_selectmenu(void *arg, int event)
{	

	switch(event)
	{
	case 0: /* Border Select */
		borderselect_nla();
		break;
	case 1: /* Select/Deselect All Keys */
		deselect_nlachannel_keys(1);
		allqueue (REDRAWNLA, 0);
		allqueue (REDRAWIPO, 0);
		break;
	case 2: /* Select/Deselect All Channel */
		deselect_nlachannels(1);
		allqueue (REDRAWVIEW3D, 0);
		allqueue (REDRAWNLA, 0);
		allqueue (REDRAWIPO, 0);
		break;
	case 3: /* Select/Deselect All Markers */
		deselect_markers(1, 0);
		allqueue(REDRAWTIME, 0);
		allqueue(REDRAWIPO, 0);
		allqueue(REDRAWACTION, 0);
		allqueue(REDRAWNLA, 0);
		allqueue(REDRAWSOUND, 0);
		break;
	case 4: /* Borderselect markers */
		borderselect_markers();
		break;
	}
}

static uiBlock *nla_selectmenu(void *arg_unused)
{
	uiBlock *block;
	short yco= 0, menuwidth=120;

	block= uiNewBlock(&curarea->uiblocks, "nla_selectmenu", UI_EMBOSSP, UI_HELV, curarea->headwin);
	uiBlockSetButmFunc(block, do_nla_selectmenu, NULL);

	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Border Select|B", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 0, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Border Select Markers|Ctrl B", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 4, "");
	
	uiDefBut(block, SEPR, 0, "",        0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Select/Deselect All Keys|A", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 1, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Select/Deselect All Channels", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 2, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Select/Deselect All Markers|Ctrl A", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 3, "");

	if(curarea->headertype==HEADERTOP) {
		uiBlockSetDirection(block, UI_DOWN);
	}
	else {
		uiBlockSetDirection(block, UI_TOP);
		uiBlockFlipOrder(block);
	}

	uiTextBoundsBlock(block, 50);

	return block;
}

static void do_nla_strip_snapmenu(void *arg, int event)
{
	snap_action_strips(event);
	
	allqueue(REDRAWIPO, 0);
	allqueue(REDRAWACTION, 0);
	allqueue(REDRAWNLA, 0);	
}

static uiBlock *nla_strip_snapmenu(void *arg_unused)
{
	uiBlock *block;
	short yco = 20, menuwidth = 120;

	block= uiNewBlock(&curarea->uiblocks, "nla_strip_snapmenu", UI_EMBOSSP, UI_HELV, G.curscreen->mainwin);
	uiBlockSetButmFunc(block, do_nla_strip_snapmenu, NULL);
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Nearest Frame|Shift S, 1",		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 1, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Current Frame|Shift S, 2",		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 2, "");

	uiBlockSetDirection(block, UI_RIGHT);
	uiTextBoundsBlock(block, 60);
	return block;
}

static void do_nla_strip_transformmenu(void *arg, int event)
{
	switch(event) {
	case 0: /* grab/move */
		transform_nlachannel_keys ('g', 0);
			update_for_newframe_muted();
		break;
	case 1: /* scale */
		transform_nlachannel_keys ('s', 0);
			update_for_newframe_muted();
		break;
	}
	allqueue(REDRAWVIEW3D, 0);
}

static uiBlock *nla_strip_transformmenu(void *arg_unused)
{
	uiBlock *block;
	short yco = 20, menuwidth = 120;

	block= uiNewBlock(&curarea->uiblocks, "nla_strip_transformmenu", UI_EMBOSSP, UI_HELV, G.curscreen->mainwin);
	uiBlockSetButmFunc(block, do_nla_strip_transformmenu, NULL);
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Grab/Move|G",		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 0, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Scale|S",		0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 1, "");

	uiBlockSetDirection(block, UI_RIGHT);
	uiTextBoundsBlock(block, 60);
	return block;
}

static void do_nla_stripmenu(void *arg, int event)
{	
	switch(event)
	{
	case 0: /* Strip Properties */
		add_blockhandler(curarea, NLA_HANDLER_PROPERTIES, UI_PNL_UNSTOW);
		break;
	case 1: /* Add Action Strip */
		add_nlablock();
		break;
	case 2: /* Duplicate */
		duplicate_nlachannel_keys();
		update_for_newframe_muted();
		break;
	case 3: /* Delete Strips */
		if (okee("Erase selected strips and/or keys")) {
			delete_nlachannel_keys ();
			update_for_newframe_muted();
		}
		break;
	case 5: /* Convert Action to NLA Strip */
		break;
	case 6: /* Move Up */
		shift_nlastrips_up();
		break;
	case 7: /* Move Down */
		shift_nlastrips_down();
		break;
	case 8:	/* size */
		reset_action_strips(1);
		break;
	case 9:	/* reset start/end of action */
		reset_action_strips(2);
		break;
	}
}

static uiBlock *nla_stripmenu(void *arg_unused)
{
	uiBlock *block;
	short yco= 0, menuwidth=120;

	block= uiNewBlock(&curarea->uiblocks, "nla_stripmenu", UI_EMBOSSP, UI_HELV, curarea->headwin);
	uiBlockSetButmFunc(block, do_nla_stripmenu, NULL);

	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Strip Properties...|N", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 0, "");
	uiDefIconTextBlockBut(block, nla_strip_transformmenu, NULL, ICON_RIGHTARROW_THIN, "Transform", 0, yco-=20, 120, 20, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Reset Strip Size|Alt S", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 8, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Reset Action Start/End|Alt S", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 9, "");
	uiDefIconTextBlockBut(block, nla_strip_snapmenu, NULL, ICON_RIGHTARROW_THIN, "Snap To Frame", 0, yco-=20, 120, 20, "");
	
	uiDefBut(block, SEPR, 0, "",        0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Add Action Strip|Shift A", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 1, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Duplicate|Shift D", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 2, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Delete|X", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 3, "");
	
	uiDefBut(block, SEPR, 0, "",        0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");

	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Move Down|Ctrl Page Down", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 7, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Move Up|Ctrl Page Up", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 6, "");
		
	// uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Convert Action to NLA Strip|C", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 5, "");

	if(curarea->headertype==HEADERTOP) {
		uiBlockSetDirection(block, UI_DOWN);
	}
	else {
		uiBlockSetDirection(block, UI_TOP);
		uiBlockFlipOrder(block);
	}

	uiTextBoundsBlock(block, 50);

	return block;
}

static void do_nla_markermenu(void *arg, int event)
{	
	switch(event)
	{
		case 1:
			add_marker(CFRA);
			break;
		case 2:
			duplicate_marker();
			break;
		case 3:
			remove_marker();
			break;
		case 4:
			rename_marker();
			break;
		case 5:
			transform_markers('g', 0);
			break;
	}
	
	allqueue(REDRAWTIME, 0);
	allqueue(REDRAWIPO, 0);
	allqueue(REDRAWACTION, 0);
	allqueue(REDRAWNLA, 0);
	allqueue(REDRAWSOUND, 0);
}

static uiBlock *nla_markermenu(void *arg_unused)
{
	uiBlock *block;
	short yco= 0, menuwidth=120;

	block= uiNewBlock(&curarea->uiblocks, "nla_markermenu", 
					  UI_EMBOSSP, UI_HELV, curarea->headwin);
	uiBlockSetButmFunc(block, do_nla_markermenu, NULL);

	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Add Marker|M", 0, yco-=20, 
					 menuwidth, 19, NULL, 0.0, 0.0, 1, 1, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Duplicate Marker|Ctrl Shift D", 0, yco-=20, 
					 menuwidth, 19, NULL, 0.0, 0.0, 1, 2, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Delete Marker|X", 0, yco-=20,
					 menuwidth, 19, NULL, 0.0, 0.0, 1, 3, "");
					 
	uiDefBut(block, SEPR, 0, "",        0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");

	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "(Re)Name Marker|Ctrl M", 0, yco-=20,
					 menuwidth, 19, NULL, 0.0, 0.0, 1, 4, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Grab/Move Marker|Ctrl G", 0, yco-=20,
					 menuwidth, 19, NULL, 0.0, 0.0, 1, 5, "");
	
	if(curarea->headertype==HEADERTOP) {
		uiBlockSetDirection(block, UI_DOWN);
	}
	else {
		uiBlockSetDirection(block, UI_TOP);
		uiBlockFlipOrder(block);
	}

	uiTextBoundsBlock(block, 50);

	return block;
}

void nla_buttons(void)
{
	SpaceNla *snla;
	short xco, xmax;
	char naam[20];
	uiBlock *block;
	
	snla= curarea->spacedata.first;
	
	sprintf(naam, "header %d", curarea->headwin);
	block= uiNewBlock(&curarea->uiblocks, naam, UI_EMBOSS, UI_HELV, curarea->headwin);

	if(area_is_active_area(curarea)) uiBlockSetCol(block, TH_HEADER);
	else uiBlockSetCol(block, TH_HEADERDESEL);

	curarea->butspacetype= SPACE_NLA;
	
	xco = 8;
	
	uiDefIconTextButC(block, ICONTEXTROW,B_NEWSPACE, ICON_VIEW3D, windowtype_pup(), xco,0,XIC+10,YIC, &(curarea->butspacetype), 1.0, SPACEICONMAX, 0, 0, "Displays Current Window Type. Click for menu of available types.");

	xco+= XIC+14;

	uiBlockSetEmboss(block, UI_EMBOSSN);
	if(curarea->flag & HEADER_NO_PULLDOWN) {
		uiDefIconButBitS(block, TOG, HEADER_NO_PULLDOWN, B_FLIPINFOMENU, ICON_DISCLOSURE_TRI_RIGHT,
				xco,2,XIC,YIC-2,
				&(curarea->flag), 0, 0, 0, 0, "Show pulldown menus");
	} else {
		uiDefIconButBitS(block, TOG, HEADER_NO_PULLDOWN, B_FLIPINFOMENU, ICON_DISCLOSURE_TRI_DOWN,
				xco,2,XIC,YIC-2,
				&(curarea->flag), 0, 0, 0, 0, "Hide pulldown menus");
	}
	uiBlockSetEmboss(block, UI_EMBOSS);
	xco+=XIC;

	if((curarea->flag & HEADER_NO_PULLDOWN)==0) {
		/* pull down menus */
		uiBlockSetEmboss(block, UI_EMBOSSP);
	
		xmax= GetButStringLength("View");
		uiDefPulldownBut(block, nla_viewmenu, NULL, "View", xco, -2, xmax-3, 24, "");
		xco+= xmax;
		
		xmax= GetButStringLength("Select");
		uiDefPulldownBut(block, nla_selectmenu, NULL, "Select", xco, -2, xmax-3, 24, "");
		xco+= xmax;
	
		xmax= GetButStringLength("Marker");
		uiDefPulldownBut(block, nla_markermenu, NULL, "Marker", xco, -2, xmax-3, 24, "");
		xco+= xmax;
		
		xmax= GetButStringLength("Strip");
		uiDefPulldownBut(block, nla_stripmenu, NULL, "Strip", xco, -2, xmax-3, 24, "");
		xco+= xmax;
	
		
	}

	uiBlockSetEmboss(block, UI_EMBOSS);


	/* FULL WINDOW */
	
	
//	xco = 8;
	
//	uiDefIconTextButC(block, ICONTEXTROW,B_NEWSPACE, ICON_VIEW3D, windowtype_pup(), xco,0,XIC+10,YIC, &(curarea->butspacetype), 1.0, SPACEICONMAX, 0, 0, "Displays Current Window Type. Click for menu of available types.");

//	xco+= XIC+22;
	
	/* FULL WINDOW */
//	if(curarea->full) uiDefIconBut(block, BUT,B_FULL, ICON_SPLITSCREEN,	xco,0,XIC,YIC, 0, 0, 0, 0, 0, "Returns to multiple views window (CTRL+Up arrow)");
//	else uiDefIconBut(block, BUT,B_FULL, ICON_FULLSCREEN,	xco,0,XIC,YIC, 0, 0, 0, 0, 0, "Makes current window full screen (CTRL+Down arrow)");
	
	/* HOME */
//	uiDefIconBut(block, BUT, B_NLAHOME, ICON_HOME,	xco+=XIC,0,XIC,YIC, 0, 0, 0, 0, 0, "Zooms window to home view showing all items (HOMEKEY)");	
//	xco+= XIC;
	
	/* IMAGE */
//	uiDefIconButS(block, TOG, B_REDR, ICON_IMAGE_COL,	xco+=XIC,0,XIC,YIC, &sseq->mainb, 0, 0, 0, 0, "Toggles image display");

	/* ZOOM en BORDER */
//	xco+= XIC;
//	uiDefIconButI(block, TOG, B_VIEW2DZOOM, ICON_VIEWZOOM,	xco+=XIC,0,XIC,YIC, &viewmovetemp, 0, 0, 0, 0, "Zoom view (CTRL+MiddleMouse)");
//	uiDefIconBut(block, BUT, B_NLABORDER, ICON_BORDERMOVE,	xco+=XIC,0,XIC,YIC, 0, 0, 0, 0, 0, "Zoom view to area");

	/* draw LOCK */
//	xco+= XIC/2;

	xco += 8;

	uiDefIconButS(block, ICONTOG, 1, ICON_UNLOCKED,	xco,0,XIC,YIC, &(snla->lock), 0, 0, 0, 0, "Toggles forced redraw of other windows to reflect changes in real time");

	uiDrawBlock(block);
}

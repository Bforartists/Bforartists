/**
 *
 * $Id:
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
 * The Original Code is Copyright (C) 2005 Blender Foundation.
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
#include "DNA_screen_types.h"
#include "DNA_scene_types.h"
#include "DNA_space_types.h"
#include "DNA_view2d_types.h"
#include "DNA_userdef_types.h"

#include "BIF_gl.h"
#include "BIF_interface.h"
#include "BIF_resources.h"
#include "BIF_screen.h"
#include "BIF_space.h"
#include "BIF_toolbox.h"
#include "BIF_butspace.h"

#include "BKE_global.h"
#include "BKE_main.h"

#include "BSE_drawipo.h"
#include "BSE_drawview.h"
#include "BSE_editipo.h"
#include "BSE_filesel.h"
#include "BSE_headerbuttons.h"
#include "BSE_time.h"

#include "blendef.h"
#include "mydevice.h"

void do_time_buttons(ScrArea *sa, unsigned short event)
{

	switch(event) {

	case B_TL_REW:
		CFRA= SFRA;
		update_for_newframe();
		break;
	case B_TL_PLAY:
		play_anim(1);
		break;
	case B_TL_FF:
		/* end frame */
		CFRA= EFRA;
		update_for_newframe();
		break;
	case B_TL_PREVKEY:
		/* previous keyframe */
		nextprev_timeline_key(-1);
		break;
	case B_TL_NEXTKEY:
		/* next keyframe */
		nextprev_timeline_key(1);
		break;
	}
}

static void do_time_viewmenu(void *arg, int event)
{
	extern int play_anim(int mode);
	
	switch(event) {
		case 1: /* Play Back Animation */
			play_anim(0);
			break;
		case 2: /* Play Back Animation in All */
			play_anim(1);
			break;
		case 3: /* View All */
			G.v2d->tot.xmin= G.scene->r.sfra;
			G.v2d->tot.xmax= G.scene->r.efra;
			G.v2d->cur= G.v2d->tot;
			
			test_view2d(G.v2d, curarea->winx, curarea->winy);
			scrarea_queue_winredraw(curarea);
			break;
		case 4: /* Maximize Window */
				/* using event B_FULL */
			break;
	}
	allqueue(REDRAWVIEW3D, 0);
}

static uiBlock *time_viewmenu(void *arg_unused)
{
	uiBlock *block;
	short yco= 0, menuwidth=120;
	
	block= uiNewBlock(&curarea->uiblocks, "time_viewmenu", 
					  UI_EMBOSSP, UI_HELV, curarea->headwin);
	uiBlockSetButmFunc(block, do_time_viewmenu, NULL);
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Play Back Animation|Alt A", 0, yco-=20, 
					 menuwidth, 19, NULL, 0.0, 0.0, 1, 1, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Play Back Animation in 3D View|Alt Shift A", 0, yco-=20,
					 menuwidth, 19, NULL, 0.0, 0.0, 1, 2, "");

	uiDefBut(block, SEPR, 0, "",        0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "View All|Home", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 3, "");
		
	if (!curarea->full) 
		uiDefIconTextBut(block, BUTM, B_FULL, ICON_BLANK1, "Maximize Window|Ctrl UpArrow", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 4, "");
	else 
		uiDefIconTextBut(block, BUTM, B_FULL, ICON_BLANK1, "Tile Window|Ctrl DownArrow", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 4, "");
	
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

static void do_time_framemenu(void *arg, int event)
{
	switch(event) {
		case 1: /*Set as Start */
			G.scene->r.sfra = CFRA;
			allqueue(REDRAWALL, 1);
			break;
		case 2: /* Set as End */
			G.scene->r.efra = CFRA;
			allqueue(REDRAWALL, 1);
			break;
		case 3: /* Add Marker */
			add_timeline_marker(CFRA);
			break;
		case 4: /* Remove Marker */
			remove_timeline_marker();
			break;
		case 5: /* Rename Marker */
			rename_timeline_marker();
			break;
	}
	allqueue(REDRAWTIME, 0);
}

static uiBlock *time_framemenu(void *arg_unused)
{
	uiBlock *block;
	short yco= 0, menuwidth=120;
	
	block= uiNewBlock(&curarea->uiblocks, "time_framemenu", 
					  UI_EMBOSSP, UI_HELV, curarea->headwin);
	uiBlockSetButmFunc(block, do_time_framemenu, NULL);
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Add Marker|M", 0, yco-=20, 
					 menuwidth, 19, NULL, 0.0, 0.0, 1, 3, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Remove Marker|X", 0, yco-=20,
					 menuwidth, 19, NULL, 0.0, 0.0, 1, 4, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Name Marker|Ctrl M", 0, yco-=20,
					 menuwidth, 19, NULL, 0.0, 0.0, 1, 5, "");
					 
	uiDefBut(block, SEPR, 0, "", 0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Set as Start|S", 0, yco-=20, 
					 menuwidth, 19, NULL, 0.0, 0.0, 1, 1, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Set as End|E", 0, yco-=20,
					 menuwidth, 19, NULL, 0.0, 0.0, 1, 2, "");

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

void time_buttons(ScrArea *sa)
{
	uiBlock *block;
	short xco, xmax;
	char name[256];
	
	sprintf(name, "header %d", sa->headwin);
	block= uiNewBlock(&sa->uiblocks, name, UI_EMBOSS, UI_HELV, sa->headwin);

	if(area_is_active_area(sa)) uiBlockSetCol(block, TH_HEADER);
	else uiBlockSetCol(block, TH_HEADERDESEL);
	
	sa->butspacetype= SPACE_TIME;

	xco = 8;
	
	uiDefIconTextButC(block, ICONTEXTROW,B_NEWSPACE, ICON_VIEW3D, 
					  windowtype_pup(), xco, 0, XIC+10, YIC, 
					  &(sa->butspacetype), 1.0, SPACEICONMAX, 0, 0, 
					  "Displays Current Window Type. "
					  "Click for menu of available types.");

	xco += XIC + 14;

	uiBlockSetEmboss(block, UI_EMBOSSN);
	if (sa->flag & HEADER_NO_PULLDOWN) {
		uiDefIconButS(block, TOG|BIT|0, B_FLIPINFOMENU, 
					  ICON_DISCLOSURE_TRI_RIGHT,
					  xco,2,XIC,YIC-2,
					  &(sa->flag), 0, 0, 0, 0, 
					  "Show pulldown menus");
	}
	else {
		uiDefIconButS(block, TOG|BIT|0, B_FLIPINFOMENU, 
					  ICON_DISCLOSURE_TRI_DOWN,
					  xco,2,XIC,YIC-2,
					  &(sa->flag), 0, 0, 0, 0, 
					  "Hide pulldown menus");
	}
	uiBlockSetEmboss(block, UI_EMBOSS);
	xco+=XIC;

	if((sa->flag & HEADER_NO_PULLDOWN)==0) {
		/* pull down menus */
		uiBlockSetEmboss(block, UI_EMBOSSP);
	
		xmax= GetButStringLength("View");
		uiDefPulldownBut(block, time_viewmenu, NULL, 
					  "View", xco, -2, xmax-3, 24, "");
		xco+= xmax;
		xmax= GetButStringLength("Frame");
		uiDefPulldownBut(block, time_framemenu, NULL, 
					  "Frame", xco, -2, xmax-3, 24, "");
		xco+= xmax;

	}

	uiBlockSetEmboss(block, UI_EMBOSSX);
	xco += XIC;
	
	uiBlockBeginAlign(block);
	uiDefButS(block, NUM, REDRAWALL,"Start:",	
		xco,0, 4.5*XIC, YIC,
		&G.scene->r.sfra,MINFRAMEF, MAXFRAMEF, 0, 0,
		"The start frame of the animation");

	xco += 4.5*XIC;

	uiDefButS(block, NUM, REDRAWALL,"End:",	
		xco,0,4.5*XIC,YIC,
		&G.scene->r.efra,MINFRAMEF,MAXFRAMEF, 0, 0,
		"The end  frame of the animation");
	uiBlockEndAlign(block);

	xco += 4.5*XIC+16;
	
	uiDefButS(block, NUM, B_NEWFRAME, "",
		xco,0,3.5*XIC,YIC,
		&(G.scene->r.cfra), MINFRAMEF, MAXFRAMEF, 0, 0,
		"Displays Current Frame of animation. Click to change.");
	
	xco += 3.5*XIC+16;
	
	uiDefIconBut(block, BUT, B_TL_REW, ICON_REW,
			xco, 0, XIC, YIC, 0, 0, 0, 0, 0, "Skip to Start frame (Shift DownArrow)");
	xco+= XIC+4;
	uiDefIconBut(block, BUT, B_TL_PREVKEY, ICON_PREV_KEYFRAME,
			xco, 0, XIC, YIC, 0, 0, 0, 0, 0, "Skip to previous keyframe (Ctrl PageDown)");
	xco+= XIC+4;
	uiDefIconBut(block, BUT, B_TL_PLAY, ICON_PLAY,
			xco, 0, XIC, YIC, 0, 0, 0, 0, 0, "Play Timeline (Alt Shift A)");
	xco+= XIC+4;
	uiDefIconBut(block, BUT, B_TL_NEXTKEY, ICON_NEXT_KEYFRAME,
			xco, 0, XIC, YIC, 0, 0, 0, 0, 0, "Skip to next keyframe (Ctrl PageUp)");
	xco+= XIC+4;
	uiDefIconBut(block, BUT, B_TL_FF, ICON_FF,
			xco, 0, XIC, YIC, 0, 0, 0, 0, 0, "Skip to End frame (Shift UpArrow)");
	xco+= XIC+8;
	
	uiDefIconButBitI(block, TOG, G_RECORDKEYS, REDRAWINFO, ICON_REC,
			xco, 0, XIC, YIC, &(G.flags), 0, 0, 0, 0, "Automatically insert keyframes in Object and Action Ipo curves");
	
	xco+= XIC+16;

	/* always as last  */
	sa->headbutlen= xco+2*XIC;

	uiDrawBlock(block);
}

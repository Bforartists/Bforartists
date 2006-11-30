/**
 * header_action.c oct-2003
 *
 * Functions to draw the "Action Editor" window header
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

#include "DNA_action_types.h"
#include "DNA_curve_types.h"
#include "DNA_ID.h"
#include "DNA_ipo_types.h"
#include "DNA_key_types.h"
#include "DNA_object_types.h"
#include "DNA_scene_types.h"
#include "DNA_screen_types.h"
#include "DNA_space_types.h"

#include "BIF_editaction.h"
#include "BIF_interface.h"
#include "BIF_poseobject.h"
#include "BIF_resources.h"
#include "BIF_screen.h"
#include "BIF_space.h"

#include "BKE_action.h"
#include "BKE_armature.h"
#include "BKE_constraint.h"
#include "BKE_depsgraph.h"
#include "BKE_global.h"
#include "BKE_main.h"
#include "BKE_utildefines.h"

#include "BSE_drawipo.h"
#include "BSE_headerbuttons.h"
#include "BSE_time.h"

#include "nla.h"

#include "blendef.h"
#include "mydevice.h"

#define ACTMENU_VIEW_CENTERVIEW 0
#define ACTMENU_VIEW_AUTOUPDATE 1
#define ACTMENU_VIEW_PLAY3D     2
#define ACTMENU_VIEW_PLAYALL    3
#define ACTMENU_VIEW_ALL        4
#define ACTMENU_VIEW_MAXIMIZE   5
#define ACTMENU_VIEW_LOCK		6
#define ACTMENU_VIEW_SLIDERS	7
#define ACTMENU_VIEW_NEXTMARKER	8
#define ACTMENU_VIEW_PREVMARKER	9


#define ACTMENU_SEL_BORDER      		0
#define ACTMENU_SEL_ALL_KEYS    		1
#define ACTMENU_SEL_ALL_CHAN    		2
#define ACTMENU_SEL_COLUMN				3
#define ACTMENU_SEL_ALL_MARKERS			4
#define ACTMENU_SEL_MARKERS_KEYSBETWEEN 5
#define ACTMENU_SEL_MARKERS_KEYSCOLUMN	6

#define ACTMENU_KEY_DUPLICATE     0
#define ACTMENU_KEY_DELETE        1
#define ACTMENU_KEY_BAKE          2
#define ACTMENU_KEY_CLEAN		  3
#define ACTMENU_KEY_MIRROR		  4

#define ACTMENU_KEY_CHANPOS_MOVE_CHANNEL_UP		0
#define ACTMENU_KEY_CHANPOS_MOVE_CHANNEL_DOWN	1
#define ACTMENU_KEY_CHANPOS_MOVE_CHANNEL_TOP	2
#define ACTMENU_KEY_CHANPOS_MOVE_CHANNEL_BOTTOM	3

#define ACTMENU_KEY_TRANSFORM_MOVE	0
#define ACTMENU_KEY_TRANSFORM_SCALE	1
#define ACTMENU_KEY_TRANSFORM_SLIDE	2

#define ACTMENU_KEY_HANDLE_AUTO   0
#define ACTMENU_KEY_HANDLE_ALIGN  1
#define ACTMENU_KEY_HANDLE_FREE   2
#define ACTMENU_KEY_HANDLE_VECTOR 3

#define ACTMENU_KEY_INTERP_CONST  0
#define ACTMENU_KEY_INTERP_LINEAR 1
#define ACTMENU_KEY_INTERP_BEZIER 2

#define ACTMENU_KEY_EXTEND_CONST 0
#define ACTMENU_KEY_EXTEND_EXTRAPOLATION 1
#define ACTMENU_KEY_EXTEND_CYCLIC 2
#define ACTMENU_KEY_EXTEND_CYCLICEXTRAPOLATION 3

#define ACTMENU_KEY_SNAP_NEARFRAME  0
#define ACTMENU_KEY_SNAP_CURFRAME 1

#define ACTMENU_MARKERS_ADD 0
#define ACTMENU_MARKERS_DUPLICATE 1
#define ACTMENU_MARKERS_DELETE 2
#define ACTMENU_MARKERS_NAME 3
#define ACTMENU_MARKERS_MOVE 4

void do_action_buttons(unsigned short event)
{
	Object *ob= OBACT;

	switch(event){
		case B_ACTBAKE:
			bake_action_with_client (G.saction->action, ob, 0.01);
			break;
		case B_ACTCONT:
			set_exprap_action(IPO_HORIZ);
			break;
//	case B_ACTEXTRAP:
//		set_exprap_ipo(IPO_DIR);
//		break;
		case B_ACTCYCLIC:
			set_exprap_action(IPO_CYCL);
			break;
//	case B_ACTCYCLICX:
//		set_exprap_ipo(IPO_CYCLX);
//		break;
		case B_ACTHOME:
			//	Find X extents
			//v2d= &(G.saction->v2d);

			G.v2d->cur.xmin = 0;
			G.v2d->cur.ymin=-SCROLLB;

			if (!G.saction->action){	// here the mesh rvk?
				G.v2d->cur.xmax= -5;
				G.v2d->cur.xmax= 100;
			}
			else {
				float extra;
				
				calc_action_range(G.saction->action, &G.v2d->cur.xmin, &G.v2d->cur.xmax, 0);
				if(G.saction->pin==0 && ob) {
					G.v2d->cur.xmin= get_action_frame_inv(ob, G.v2d->cur.xmin);
					G.v2d->cur.xmax= get_action_frame_inv(ob, G.v2d->cur.xmax);
				}				
				extra= 0.05*(G.v2d->cur.xmax - G.v2d->cur.xmin);
				G.v2d->cur.xmin-= extra;
				G.v2d->cur.xmax+= extra;

				if(G.v2d->cur.xmin==G.v2d->cur.xmax) {
					G.v2d->cur.xmax= -5;
					G.v2d->cur.xmax= 100;
				}
			}
			G.v2d->cur.ymin= 0.0f;
			G.v2d->cur.ymax= 1000.0f;
			
			G.v2d->tot= G.v2d->cur;
			test_view2d(G.v2d, curarea->winx, curarea->winy);
			view2d_do_locks(curarea, V2D_LOCK_COPY);

			addqueue (curarea->win, REDRAW, 1);

			break;
		case B_ACTCOPY:
			copy_posebuf();
			allqueue(REDRAWVIEW3D, 1);
			break;
		case B_ACTPASTE:
			paste_posebuf(0);
			allqueue(REDRAWVIEW3D, 1);
			break;
		case B_ACTPASTEFLIP:
			paste_posebuf(1);
			allqueue(REDRAWVIEW3D, 1);
			break;

		case B_ACTPIN:	/* __PINFAKE */
/*		if (G.saction->flag & SACTION_PIN){
		if (G.saction->action)
		G.saction->action->id.us ++;
		
		}
		else {
			if (G.saction->action)
				G.saction->action->id.us --;
				}
*/		/* end PINFAKE */
			allqueue(REDRAWACTION, 1);
			break;

	}
}

static void do_action_viewmenu(void *arg, int event)
{
	extern int play_anim(int mode);

	switch(event) {
		case ACTMENU_VIEW_CENTERVIEW: /* Center View to Current Frame */
			center_currframe();
			break;
		case ACTMENU_VIEW_AUTOUPDATE: /* Update Automatically */
			if (BTST(G.saction->lock, 0)) 
				G.saction->lock = BCLR(G.saction->lock, 0);
			else 
				G.saction->lock = BSET(G.saction->lock, 0);
			break;
		case ACTMENU_VIEW_PLAY3D: /* Play Back Animation */
			play_anim(0);
			break;
		case ACTMENU_VIEW_PLAYALL: /* Play Back Animation in All */
			play_anim(1);
			break;	
		case ACTMENU_VIEW_ALL: /* View All */
			do_action_buttons(B_ACTHOME);
			break;
		case ACTMENU_VIEW_LOCK:
			G.v2d->flag ^= V2D_VIEWLOCK;
			if(G.v2d->flag & V2D_VIEWLOCK)
				view2d_do_locks(curarea, 0);
			break;
		case ACTMENU_VIEW_SLIDERS:	 /* Show sliders (when applicable) */
			G.saction->flag ^= SACTION_SLIDERS;
			break;
		case ACTMENU_VIEW_MAXIMIZE: /* Maximize Window */
			/* using event B_FULL */
			break;
		case ACTMENU_VIEW_NEXTMARKER: /* jump to next marker */
			nextprev_marker(1);
			break;
		case ACTMENU_VIEW_PREVMARKER: /* jump to previous marker */
			nextprev_marker(-1);
			break;
	}
	allqueue(REDRAWVIEW3D, 0);
}

static uiBlock *action_viewmenu(void *arg_unused)
{
	uiBlock *block;
	short yco= 0, menuwidth=120;
	
	block= uiNewBlock(&curarea->uiblocks, "action_viewmenu", 
					  UI_EMBOSSP, UI_HELV, curarea->headwin);
	uiBlockSetButmFunc(block, do_action_viewmenu, NULL);
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, 
					 "Center View to Current Frame|C", 0, yco-=20, 
					 menuwidth, 19, NULL, 0.0, 0.0, 1, 
					 ACTMENU_VIEW_CENTERVIEW, "");
		
	uiDefBut(block, SEPR, 0, "", 0, yco-=6, 
			 menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	
	uiDefIconTextBut(block, BUTM, 1, (G.saction->flag & SACTION_SLIDERS)?ICON_CHECKBOX_HLT:ICON_CHECKBOX_DEHLT, 
					 "Show Sliders|", 0, yco-=20, 
					 menuwidth, 19, NULL, 0.0, 0.0, 1, 
					 ACTMENU_VIEW_SLIDERS, "");
					 
	uiDefIconTextBut(block, BUTM, 1, (G.v2d->flag & V2D_VIEWLOCK)?ICON_CHECKBOX_HLT:ICON_CHECKBOX_DEHLT, 
					 "Lock Time to Other Windows|", 0, yco-=20, 
					 menuwidth, 19, NULL, 0.0, 0.0, 1, 
					 ACTMENU_VIEW_LOCK, "");
					 
	uiDefIconTextBut(block, BUTM, 1, BTST(G.saction->lock, 0)?ICON_CHECKBOX_HLT:ICON_CHECKBOX_DEHLT, 
					 "Update Automatically|", 0, yco-=20, 
					 menuwidth, 19, NULL, 0.0, 0.0, 1, 
					 ACTMENU_VIEW_AUTOUPDATE, "");

	uiDefBut(block, SEPR, 0, "", 0, yco-=6, 
					menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
					 
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, 
				"Jump To Next Marker|PageUp", 0, yco-=20,
				menuwidth, 19, NULL, 0.0, 0.0, 0, ACTMENU_VIEW_NEXTMARKER, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, 
				"Jump To Prev Marker|PageDown", 0, yco-=20, 
				menuwidth, 19, NULL, 0.0, 0.0, 0, ACTMENU_VIEW_PREVMARKER, "");
					 
	uiDefBut(block, SEPR, 0, "", 0, yco-=6, 
					menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
			
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, 
					 "Play Back Animation|Alt A", 0, yco-=20, 
					 menuwidth, 19, NULL, 0.0, 0.0, 1, 
					 ACTMENU_VIEW_PLAY3D, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, 
					 "Play Back Animation in 3D View|Alt Shift A", 0, yco-=20,
					 menuwidth, 19, NULL, 0.0, 0.0, 1, 
					 ACTMENU_VIEW_PLAYALL, "");

	uiDefBut(block, SEPR, 0, "", 0, yco-=6, 
			 menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, 
					 "View All|Home", 0, yco-=20, 
					 menuwidth, 19, NULL, 0.0, 0.0, 1, 
					 ACTMENU_VIEW_ALL, "");
	
	if (!curarea->full) 
		uiDefIconTextBut(block, BUTM, B_FULL, ICON_BLANK1, 
						 "Maximize Window|Ctrl UpArrow", 0, yco-=20, 
						 menuwidth, 19, NULL, 0.0, 0.0, 0, 
						 ACTMENU_VIEW_MAXIMIZE, "");
	else 
		uiDefIconTextBut(block, BUTM, B_FULL, ICON_BLANK1, 
						 "Tile Window|Ctrl DownArrow", 0, yco-=20, 
						 menuwidth, 19, NULL, 0.0, 0.0, 0, 
						 ACTMENU_VIEW_MAXIMIZE, "");
	
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

static void do_action_selectmenu(void *arg, int event)
{	
	SpaceAction *saction;
	bAction	*act;
	Key *key;
	
	saction = curarea->spacedata.first;
	if (!saction)
		return;

	act = saction->action;
	key = get_action_mesh_key();
	
	switch(event)
	{
		case ACTMENU_SEL_BORDER: /* Border Select */
			if (key) {
				borderselect_mesh(key);
			}
			else {
				borderselect_action();
			}
			break;

		case ACTMENU_SEL_ALL_KEYS: /* Select/Deselect All Keys */
			if (key) {
				deselect_meshchannel_keys(key, 1);
				allqueue (REDRAWACTION, 0);
				allqueue(REDRAWNLA, 0);
				allqueue (REDRAWIPO, 0);
			}
			else {
				deselect_actionchannel_keys (act, 1);
				allqueue (REDRAWACTION, 0);
				allqueue(REDRAWNLA, 0);
				allqueue (REDRAWIPO, 0);
			}
			break;

		case ACTMENU_SEL_ALL_CHAN: /* Select/Deselect All Channels */
			deselect_actionchannels (act, 1);
			allqueue (REDRAWVIEW3D, 0);
			allqueue (REDRAWACTION, 0);
			allqueue(REDRAWNLA, 0);
			allqueue (REDRAWIPO, 0);
			break;
			
		case ACTMENU_SEL_ALL_MARKERS: /* select/deselect all markers */
			deselect_markers(1, 0);
			allqueue(REDRAWTIME, 0);
			allqueue(REDRAWIPO, 0);
			allqueue(REDRAWACTION, 0);
			allqueue(REDRAWNLA, 0);
			allqueue(REDRAWSOUND, 0);
			break;
			
		case ACTMENU_SEL_COLUMN: /* select column */
			addqueue (curarea->win, KKEY, 1);
			break;
			
		case ACTMENU_SEL_MARKERS_KEYSBETWEEN: /* keys between 2 extreme selected markers */
			break;
			
		case ACTMENU_SEL_MARKERS_KEYSCOLUMN: /* keys on same frame as marker(s) */
			break;
	}
}

static uiBlock *action_selectmenu(void *arg_unused)
{
	uiBlock *block;
	short yco= 0, menuwidth=120;

	block= uiNewBlock(&curarea->uiblocks, "action_selectmenu", 
					  UI_EMBOSSP, UI_HELV, curarea->headwin);
	uiBlockSetButmFunc(block, do_action_selectmenu, NULL);

	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, 
					 "Border Select|B", 0, yco-=20, 
					 menuwidth, 19, NULL, 0.0, 0.0, 0, 
					 ACTMENU_SEL_BORDER, "");
					 
	uiDefBut(block, SEPR, 0, "", 0, yco-=6, 
			 menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
			 
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, 
					 "Select/Deselect All Keys|A", 0, yco-=20, 
					 menuwidth, 19, NULL, 0.0, 0.0, 0, 
					 ACTMENU_SEL_ALL_KEYS, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, 
					 "Select/Deselect All Markers|Ctrl A", 0, yco-=20, 
					 menuwidth, 19, NULL, 0.0, 0.0, 0, 
					 ACTMENU_SEL_ALL_MARKERS, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, 
					 "Select/Deselect All Channels", 0, yco-=20, 
					 menuwidth, 19, NULL, 0.0, 0.0, 0, 
					 ACTMENU_SEL_ALL_CHAN, "");
					 
	uiDefBut(block, SEPR, 0, "", 0, yco-=6, 
			 menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
			 
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, 
					 "Select Keys Column|K", 0, yco-=20, 
					 menuwidth, 19, NULL, 0.0, 0.0, 0, 
					 ACTMENU_SEL_COLUMN, "");
	
/*	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, 
					 "Select Keys At Markers|CTRL K", 0, yco-=20, 
					 menuwidth, 19, NULL, 0.0, 0.0, 0, 
					 ACTMENU_SEL_MARKERS_KEYSCOLUMN, "");
					
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, 
					 "Select Keys Between Markers|SHIFT K", 0, yco-=20, 
					 menuwidth, 19, NULL, 0.0, 0.0, 0, 
					 ACTMENU_SEL_MARKERS_KEYSBETWEEN, "");
*/
	
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

static void do_action_keymenu_transformmenu(void *arg, int event)
{
	SpaceAction *saction;
	bAction	*act;
	Key *key;
	
	key = get_action_mesh_key();
	saction= curarea->spacedata.first;
	
	act=saction->action;
	
	switch(event)
	{
		case ACTMENU_KEY_TRANSFORM_MOVE:
			if (key) {
				transform_meshchannel_keys('g', key);
			} 
			else if (act) {	
				transform_actionchannel_keys ('g', 0);
			}
			break;
		case ACTMENU_KEY_TRANSFORM_SCALE:
			if (key) {
				transform_meshchannel_keys('s', key);
			} 
			else if (act) {
				transform_actionchannel_keys ('s', 0);
			}
			break;
		case ACTMENU_KEY_TRANSFORM_SLIDE:
			if (key) {
				//transform_meshchannel_keys('t', key);
			} 
			else if (act) {
				transform_actionchannel_keys ('t', 0);
			}
			break;
	}

	scrarea_queue_winredraw(curarea);
}

static uiBlock *action_keymenu_transformmenu(void *arg_unused)
{
	uiBlock *block;
	short yco= 0, menuwidth=120;

	block= uiNewBlock(&curarea->uiblocks, "action_keymenu_transformmenu", 
					  UI_EMBOSSP, UI_HELV, G.curscreen->mainwin);
	uiBlockSetButmFunc(block, do_action_keymenu_transformmenu, NULL);

	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, 
					 "Grab/Move|G", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0,  
					 ACTMENU_KEY_TRANSFORM_MOVE, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, 
					 "Scale|S", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 
					 ACTMENU_KEY_TRANSFORM_SCALE, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, 
					 "Time Slide|T", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 
					 ACTMENU_KEY_TRANSFORM_SLIDE, "");
	
	
	uiBlockSetDirection(block, UI_RIGHT);
	uiTextBoundsBlock(block, 60);

	return block;
}

static void do_action_keymenu_handlemenu(void *arg, int event)
{
	Key *key;
	
	key = get_action_mesh_key();

	switch (event){
		case ACTMENU_KEY_HANDLE_AUTO:
			if (key) {
				sethandles_meshchannel_keys(HD_AUTO, key);
			} else {
				sethandles_actionchannel_keys(HD_AUTO);
			}
			break;

		case ACTMENU_KEY_HANDLE_ALIGN:
		case ACTMENU_KEY_HANDLE_FREE:
			/* OK, this is kinda dumb, need to fix the
			 * toggle crap in sethandles_ipo_keys() 
			 */
			if (key) {
				sethandles_meshchannel_keys(HD_ALIGN, key);
			} else {
				sethandles_actionchannel_keys(HD_ALIGN);
			}
			break;

		case ACTMENU_KEY_HANDLE_VECTOR:
			if (key) {
				sethandles_meshchannel_keys(HD_VECT, key);
			} else {
				sethandles_actionchannel_keys(HD_VECT);
			}
			break;
	}
}

static uiBlock *action_keymenu_handlemenu(void *arg_unused)
{
	uiBlock *block;
	short yco= 0, menuwidth=120;

	block= uiNewBlock(&curarea->uiblocks, "action_keymenu_handlemenu", UI_EMBOSSP, UI_HELV, G.curscreen->mainwin);
	uiBlockSetButmFunc(block, do_action_keymenu_handlemenu, NULL);

	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, 
					 "Auto|Shift H", 0, yco-=20, 
					 menuwidth, 19, NULL, 0.0, 0.0, 0, 
					 ACTMENU_KEY_HANDLE_AUTO, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, 
					 "Aligned|H", 0, yco-=20, 
					 menuwidth, 19, NULL, 0.0, 0.0, 0, 
					 ACTMENU_KEY_HANDLE_ALIGN, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, 
					 "Free|H", 0, yco-=20, menuwidth, 
					 19, NULL, 0.0, 0.0, 0, 
					 ACTMENU_KEY_HANDLE_FREE, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, 
					 "Vector|V", 0, yco-=20, 
					 menuwidth, 19, NULL, 0.0, 0.0, 0, 
					 ACTMENU_KEY_HANDLE_VECTOR, "");

	uiBlockSetDirection(block, UI_RIGHT);
	uiTextBoundsBlock(block, 60);

	return block;
}

static void do_action_keymenu_intpolmenu(void *arg, int event)
{
	Key *key;

	key = get_action_mesh_key();

	switch(event)
	{
		case ACTMENU_KEY_INTERP_CONST:
			if (key) {
				/* to do */
			}
			else {
				set_ipotype_actionchannels(SET_IPO_CONSTANT);
			}
			break;
		case ACTMENU_KEY_INTERP_LINEAR:
			if (key) {
				/* to do */
			}
			else {
				set_ipotype_actionchannels(SET_IPO_LINEAR);
			}
			break;
		case ACTMENU_KEY_INTERP_BEZIER:
			if (key) {
				/* to do */
			}
			else {
				set_ipotype_actionchannels(SET_IPO_BEZIER);
			}
			break;
	}

	scrarea_queue_winredraw(curarea);
}

static uiBlock *action_keymenu_intpolmenu(void *arg_unused)
{
	uiBlock *block;
	short yco= 0, menuwidth=120;

	block= uiNewBlock(&curarea->uiblocks, "action_keymenu_intpolmenu", 
					  UI_EMBOSSP, UI_HELV, G.curscreen->mainwin);
	uiBlockSetButmFunc(block, do_action_keymenu_intpolmenu, NULL);

	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, 
					 "Constant", 0, yco-=20, 
					 menuwidth, 19, NULL, 0.0, 0.0, 0, 
					 ACTMENU_KEY_INTERP_CONST, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, 
					 "Linear", 0, yco-=20, 
					 menuwidth, 19, NULL, 0.0, 0.0, 0, 
					 ACTMENU_KEY_INTERP_LINEAR, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, 
					 "Bezier", 0, yco-=20, 
					 menuwidth, 19, NULL, 0.0, 0.0, 0, 
					 ACTMENU_KEY_INTERP_BEZIER, "");

	uiBlockSetDirection(block, UI_RIGHT);
	uiTextBoundsBlock(block, 60);

	return block;
}

static void do_action_keymenu_extendmenu(void *arg, int event)
{
	Key *key;

	key = get_action_mesh_key();

	switch(event)
	{
		case ACTMENU_KEY_EXTEND_CONST:
			if (key) {
				/* to do */
			}
			else {
				set_extendtype_actionchannels(SET_EXTEND_CONSTANT);
			}
			break;
		case ACTMENU_KEY_EXTEND_EXTRAPOLATION:
			if (key) {
				/* to do */
			}
			else {
				set_extendtype_actionchannels(SET_EXTEND_EXTRAPOLATION);
			}
			break;
		case ACTMENU_KEY_EXTEND_CYCLIC:
			if (key) {
				/* to do */
			}
			else {
				set_extendtype_actionchannels(SET_EXTEND_CYCLIC);
			}
			break;
		case ACTMENU_KEY_EXTEND_CYCLICEXTRAPOLATION:
			if (key) {
				/* to do */
			}
			else {
				set_extendtype_actionchannels(SET_EXTEND_CYCLICEXTRAPOLATION);
			}
			break;
	}

	scrarea_queue_winredraw(curarea);
}

static uiBlock *action_keymenu_extendmenu(void *arg_unused)
{
	uiBlock *block;
	short yco= 0, menuwidth=120;

	block= uiNewBlock(&curarea->uiblocks, "action_keymenu_extendmenu", 
					  UI_EMBOSSP, UI_HELV, G.curscreen->mainwin);
	uiBlockSetButmFunc(block, do_action_keymenu_extendmenu, NULL);

	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, 
					 "Constant", 0, yco-=20, 
					 menuwidth, 19, NULL, 0.0, 0.0, 0, 
					 ACTMENU_KEY_EXTEND_CONST, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, 
					 "Extrapolation", 0, yco-=20, 
					 menuwidth, 19, NULL, 0.0, 0.0, 0, 
					 ACTMENU_KEY_EXTEND_EXTRAPOLATION, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, 
					 "Cyclic", 0, yco-=20, 
					 menuwidth, 19, NULL, 0.0, 0.0, 0, 
					 ACTMENU_KEY_EXTEND_CYCLIC, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, 
					 "Cyclic Extrapolation", 0, yco-=20, 
					 menuwidth, 19, NULL, 0.0, 0.0, 0, 
					 ACTMENU_KEY_EXTEND_CYCLICEXTRAPOLATION, "");

	uiBlockSetDirection(block, UI_RIGHT);
	uiTextBoundsBlock(block, 60);

	return block;
}

static void do_action_keymenu_chanposmenu(void *arg, int event)
{
	switch(event)
	{
		case ACTMENU_KEY_CHANPOS_MOVE_CHANNEL_DOWN:
			down_sel_action();
			break;
		case ACTMENU_KEY_CHANPOS_MOVE_CHANNEL_UP:
			up_sel_action();
			break;
		case ACTMENU_KEY_CHANPOS_MOVE_CHANNEL_TOP:
			top_sel_action();
			break;
		case ACTMENU_KEY_CHANPOS_MOVE_CHANNEL_BOTTOM:
			bottom_sel_action();
			break;
	}

	scrarea_queue_winredraw(curarea);
}

static uiBlock *action_keymenu_chanposmenu(void *arg_unused)
{
	uiBlock *block;
	short yco= 0, menuwidth=120;

	block= uiNewBlock(&curarea->uiblocks, "action_keymenu_chanposmenu", 
					  UI_EMBOSSP, UI_HELV, G.curscreen->mainwin);
	uiBlockSetButmFunc(block, do_action_keymenu_chanposmenu, NULL);

	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, 
					 "Move Up|Ctrl Page Up", 0, yco-=20, 
					 menuwidth, 19, NULL, 0.0, 0.0, 0, 
					 ACTMENU_KEY_CHANPOS_MOVE_CHANNEL_UP, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, 
					 "Move Down|Ctrl Page Down", 0, yco-=20, 
					 menuwidth, 19, NULL, 0.0, 0.0, 0, 
					 ACTMENU_KEY_CHANPOS_MOVE_CHANNEL_DOWN, "");
	
	uiDefBut(block, SEPR, 0, "", 0, yco-=6, 
					menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
					
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, 
					 "Move to Top|Shift Page Up", 0, yco-=20, 
					 menuwidth, 19, NULL, 0.0, 0.0, 0, 
					 ACTMENU_KEY_CHANPOS_MOVE_CHANNEL_TOP, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, 
					 "Move to Bottom|Shift Page Down", 0, yco-=20, 
					 menuwidth, 19, NULL, 0.0, 0.0, 0, 
					 ACTMENU_KEY_CHANPOS_MOVE_CHANNEL_BOTTOM, "");

	uiBlockSetDirection(block, UI_RIGHT);
	uiTextBoundsBlock(block, 60);

	return block;
}

static void do_action_keymenu_snapmenu(void *arg, int event)
{
	switch(event)
	{
		case ACTMENU_KEY_SNAP_NEARFRAME:
			snap_keys_to_frame(1);
			break;
		case ACTMENU_KEY_SNAP_CURFRAME:
			snap_keys_to_frame(2);
			break;
	}

	scrarea_queue_winredraw(curarea);
}

static uiBlock *action_keymenu_snapmenu(void *arg_unused)
{
	uiBlock *block;
	short yco= 0, menuwidth=120;

	block= uiNewBlock(&curarea->uiblocks, "action_keymenu_snapmenu", 
					  UI_EMBOSSP, UI_HELV, G.curscreen->mainwin);
	uiBlockSetButmFunc(block, do_action_keymenu_snapmenu, NULL);

	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, 
					 "Nearest Frame|Shift S, 1", 0, yco-=20, 
					 menuwidth, 19, NULL, 0.0, 0.0, 0, 
					 ACTMENU_KEY_SNAP_NEARFRAME, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, 
					 "Current Frame|Shift S, 2", 0, yco-=20, 
					 menuwidth, 19, NULL, 0.0, 0.0, 0, 
					 ACTMENU_KEY_SNAP_CURFRAME, "");

	uiBlockSetDirection(block, UI_RIGHT);
	uiTextBoundsBlock(block, 60);

	return block;
}

static void do_action_keymenu(void *arg, int event)
{	
	SpaceAction *saction;
	bAction	*act;
	Key *key;
	
	saction= curarea->spacedata.first;
	if (!saction)
		return;

	act = saction->action;
	key = get_action_mesh_key();

	switch(event)
	{
		case ACTMENU_KEY_DUPLICATE:
			if (key) {
				duplicate_meshchannel_keys(key);
			}
			else if (act) {
				duplicate_actionchannel_keys();
				remake_action_ipos(act);
			}
 			break;

		case ACTMENU_KEY_DELETE:
			if (key) {
				delete_meshchannel_keys(key);
			}
			else if (act) {
				delete_actionchannel_keys ();
			}
			break;
		case ACTMENU_KEY_BAKE:
			bake_action_with_client (G.saction->action, OBACT, 0.01);
			break;
		case ACTMENU_KEY_CLEAN:
			if (key) 
				clean_shapekeys(key);
			else if (act) 
				clean_actionchannels(act);
			break;
	}
}

static uiBlock *action_keymenu(void *arg_unused)
{
	uiBlock *block;
	short yco= 0, menuwidth=120;

	block= uiNewBlock(&curarea->uiblocks, "action_keymenu", 
					  UI_EMBOSSP, UI_HELV, curarea->headwin);
	uiBlockSetButmFunc(block, do_action_keymenu, NULL);
	
	uiDefIconTextBlockBut(block, action_keymenu_transformmenu, 
						  NULL, ICON_RIGHTARROW_THIN, "Transform", 0, yco-=20, 120, 20, "");
	
	uiDefIconTextBlockBut(block, action_keymenu_snapmenu, 
						  NULL, ICON_RIGHTARROW_THIN, "Snap", 0, yco-=20, 120, 20, "");
	
	uiDefBut(block, SEPR, 0, "", 0, yco-=6, 
					menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");

	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, 
					"Duplicate|Shift D", 0, yco-=20, 
					menuwidth, 19, NULL, 0.0, 0.0, 0, 
					ACTMENU_KEY_DUPLICATE, "");
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, 
					"Delete|X", 0, yco-=20, 
					menuwidth, 19, NULL, 0.0, 0.0, 0, 
					ACTMENU_KEY_DELETE, "");

	uiDefBut(block, SEPR, 0, "", 0, yco-=6, 
			 menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");

	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, 
					 "Clean Action|O", 0, yco-=20, 
					 menuwidth, 19, NULL, 0.0, 0.0, 0, 
					 ACTMENU_KEY_CLEAN, "");
			 
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, 
					 "Bake Action to Ipo Keys", 0, yco-=20, 
					 menuwidth, 19, NULL, 0.0, 0.0, 0, 
					 ACTMENU_KEY_BAKE, "");

	uiDefBut(block, SEPR, 0, "", 0, yco-=6, 
			 menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");

	uiDefIconTextBlockBut(block, action_keymenu_handlemenu, 
						  NULL, ICON_RIGHTARROW_THIN, 
						  "Handle Type", 0, yco-=20, 120, 20, "");
	
	uiDefBut(block, SEPR, 0, "", 0, yco-=6, 
			 menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");

	uiDefIconTextBlockBut(block, action_keymenu_extendmenu, 
						  NULL, ICON_RIGHTARROW_THIN, 
						  "Extend Mode", 0, yco-=20, 120, 20, "");
	uiDefIconTextBlockBut(block, action_keymenu_intpolmenu, 
						  NULL, ICON_RIGHTARROW_THIN, 
						  "Interpolation Mode", 0, yco-=20, 120, 20, "");
	uiDefIconTextBlockBut(block, action_keymenu_chanposmenu, 
						  NULL, ICON_RIGHTARROW_THIN, 
						  "Channel Ordering", 0, yco-=20, 120, 20, "");

	
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

static void do_action_markermenu(void *arg, int event)
{	
	switch(event)
	{
		case ACTMENU_MARKERS_ADD:
			add_marker(CFRA);
			break;
		case ACTMENU_MARKERS_DUPLICATE:
			duplicate_marker();
			break;
		case ACTMENU_MARKERS_DELETE:
			remove_marker();
			break;
		case ACTMENU_MARKERS_NAME:
			rename_marker();
			break;
		case ACTMENU_MARKERS_MOVE:
			transform_markers('g', 0);
			break;
	}
	
	allqueue(REDRAWTIME, 0);
	allqueue(REDRAWIPO, 0);
	allqueue(REDRAWACTION, 0);
	allqueue(REDRAWNLA, 0);
	allqueue(REDRAWSOUND, 0);
}

static uiBlock *action_markermenu(void *arg_unused)
{
	uiBlock *block;
	short yco= 0, menuwidth=120;

	block= uiNewBlock(&curarea->uiblocks, "action_markermenu", 
					  UI_EMBOSSP, UI_HELV, curarea->headwin);
	uiBlockSetButmFunc(block, do_action_markermenu, NULL);

	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Add Marker|M", 0, yco-=20, 
					 menuwidth, 19, NULL, 0.0, 0.0, 1, ACTMENU_MARKERS_ADD, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Duplicate Marker|Ctrl Shift D", 0, yco-=20, 
					 menuwidth, 19, NULL, 0.0, 0.0, 1, ACTMENU_MARKERS_DUPLICATE, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Delete Marker|X", 0, yco-=20,
					 menuwidth, 19, NULL, 0.0, 0.0, 1, ACTMENU_MARKERS_DELETE, "");
					 
	uiDefBut(block, SEPR, 0, "",        0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");

	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "(Re)Name Marker|Shift M", 0, yco-=20,
					 menuwidth, 19, NULL, 0.0, 0.0, 1, ACTMENU_MARKERS_NAME, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Grab/Move Marker|Shift G", 0, yco-=20,
					 menuwidth, 19, NULL, 0.0, 0.0, 1, ACTMENU_MARKERS_MOVE, "");
	
	
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

void action_buttons(void)
{
	uiBlock *block;
	short xco, xmax;
	char naam[256];
	Object *ob;
	ID *from;

	if (!G.saction)
		return;

	// copy from drawactionspace....
	if (!G.saction->pin) {
		if (OBACT)
			G.saction->action = OBACT->action;
		else
			G.saction->action=NULL;
	}

	sprintf(naam, "header %d", curarea->headwin);
	block= uiNewBlock(&curarea->uiblocks, naam, 
					  UI_EMBOSS, UI_HELV, curarea->headwin);

	if (area_is_active_area(curarea)) 
		uiBlockSetCol(block, TH_HEADER);
	else 
		uiBlockSetCol(block, TH_HEADERDESEL);

	curarea->butspacetype= SPACE_ACTION;
	
	xco = 8;
	
	uiDefIconTextButC(block, ICONTEXTROW,B_NEWSPACE, ICON_VIEW3D, 
					  windowtype_pup(), xco, 0, XIC+10, YIC, 
					  &(curarea->butspacetype), 1.0, SPACEICONMAX, 0, 0, 
					  "Displays Current Window Type. "
					  "Click for menu of available types.");

	xco += XIC + 14;

	uiBlockSetEmboss(block, UI_EMBOSSN);
	if (curarea->flag & HEADER_NO_PULLDOWN) {
		uiDefIconButBitS(block, TOG, HEADER_NO_PULLDOWN, B_FLIPINFOMENU, 
					  ICON_DISCLOSURE_TRI_RIGHT,
					  xco,2,XIC,YIC-2,
					  &(curarea->flag), 0, 0, 0, 0, 
					  "Show pulldown menus");
	}
	else {
		uiDefIconButBitS(block, TOG, HEADER_NO_PULLDOWN, B_FLIPINFOMENU, 
					  ICON_DISCLOSURE_TRI_DOWN,
					  xco,2,XIC,YIC-2,
					  &(curarea->flag), 0, 0, 0, 0, 
					  "Hide pulldown menus");
	}
	uiBlockSetEmboss(block, UI_EMBOSS);
	xco+=XIC;

	if((curarea->flag & HEADER_NO_PULLDOWN)==0) {
		/* pull down menus */
		uiBlockSetEmboss(block, UI_EMBOSSP);
	
		xmax= GetButStringLength("View");
		uiDefPulldownBut(block, action_viewmenu, NULL, 
					  "View", xco, -2, xmax-3, 24, "");
		xco+= xmax;
		
		xmax= GetButStringLength("Select");
		uiDefPulldownBut(block, action_selectmenu, NULL, 
					  "Select", xco, -2, xmax-3, 24, "");
		xco+= xmax;
		
		xmax= GetButStringLength("Marker");
		uiDefPulldownBut(block, action_markermenu, NULL, 
					  "Marker", xco, -2, xmax-3, 24, "");
		xco+= xmax;
		
		xmax= GetButStringLength("Key");
		uiDefPulldownBut(block, action_keymenu, NULL, 
					  "Key", xco, -2, xmax-3, 24, "");
		xco+= xmax;
	}

	uiBlockSetEmboss(block, UI_EMBOSS);
	
	/* NAME ETC */
	ob=OBACT;
	from = (ID*) ob;

	xco= std_libbuttons(block, xco, 0, B_ACTPIN, &G.saction->pin, 
						B_ACTIONBROWSE, ID_AC, 0, (ID*)G.saction->action, 
						from, &(G.saction->actnr), B_ACTALONE, 
						B_ACTLOCAL, B_ACTIONDELETE, 0, 0);	

		
	/* Draw action baker */
	xco+= 8;
	
	uiDefBut(block, BUT, B_ACTBAKE, 
			 "Bake", xco, 0, 64, YIC, 0, 0, 0, 0, 0, 
			 "Create an action with the constraint effects "
			 "converted into Ipo keys");
	xco+=64;

	uiClearButLock();

	/* draw LOCK */
	xco+= 8;
	uiDefIconButS(block, ICONTOG, 1, ICON_UNLOCKED,	xco, 0, XIC, YIC, 
				  &(G.saction->lock), 0, 0, 0, 0, 
				  "Updates other affected window spaces automatically "
				  "to reflect changes in real time");


	/* always as last  */
	curarea->headbutlen = xco + 2*XIC;

	uiDrawBlock(block);
}

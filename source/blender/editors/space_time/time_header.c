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
 * The Original Code is: all of this file.
 *
 * Contributor(s): none yet.
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#include <string.h>
#include <stdio.h>

#include "DNA_space_types.h"
#include "DNA_scene_types.h"
#include "DNA_screen_types.h"
#include "DNA_windowmanager_types.h"
#include "DNA_userdef_types.h"

#include "MEM_guardedalloc.h"

#include "BLI_blenlib.h"

#include "BKE_context.h"
#include "BKE_global.h"
#include "BKE_screen.h"

#include "ED_keyframing.h"
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

#include "ED_markers.h"

#include "time_intern.h"


/* ************************ header time area region *********************** */


static void do_time_redrawmenu(bContext *C, void *arg, int event)
{
	SpaceTime *stime= (SpaceTime*)CTX_wm_space_data(C);
	
	if(event < 1001) {
		
		stime->redraws ^= event;
		/* update handler when it's running */
//		if(has_screenhandler(G.curscreen, SCREEN_HANDLER_ANIM))
//			start_animated_screen(stime);
	}
	else {
		if(event==1001) {
//			button(&CTX_data_scene(C)->r.frs_sec,1,120,"FPS:");
		}
	}
}


static uiBlock *time_redrawmenu(bContext *C, ARegion *ar, void *arg_unused)
{
	ScrArea *curarea= CTX_wm_area(C);
	SpaceTime *stime= (SpaceTime*)CTX_wm_space_data(C);
	Scene *scene= CTX_data_scene(C);
	uiBlock *block;
	short yco= 0, menuwidth=120, icon;
	char str[32];
	
	block= uiBeginBlock(C, ar, "header time_redrawmenu", UI_EMBOSSP, UI_HELV);
	uiBlockSetButmFunc(block, do_time_redrawmenu, NULL);
	
	if(stime->redraws & TIME_LEFTMOST_3D_WIN) icon= ICON_CHECKBOX_HLT;
	else icon= ICON_CHECKBOX_DEHLT;
	uiDefIconTextBut(block, BUTM, 1, icon, "Top-Left 3D Window",	 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, TIME_LEFTMOST_3D_WIN, "");
	
	if(stime->redraws & TIME_ALL_3D_WIN) icon= ICON_CHECKBOX_HLT;
	else icon= ICON_CHECKBOX_DEHLT;
	uiDefIconTextBut(block, BUTM, 1, icon, "All 3D Windows",	 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, TIME_ALL_3D_WIN, "");
	
	if(stime->redraws & TIME_ALL_ANIM_WIN) icon= ICON_CHECKBOX_HLT;
	else icon= ICON_CHECKBOX_DEHLT;
	uiDefIconTextBut(block, BUTM, 1, icon, "Animation Windows",	 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, TIME_ALL_ANIM_WIN, "");
	
	if(stime->redraws & TIME_ALL_BUTS_WIN) icon= ICON_CHECKBOX_HLT;
	else icon= ICON_CHECKBOX_DEHLT;
	uiDefIconTextBut(block, BUTM, 1, icon, "Buttons Windows",	 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, TIME_ALL_BUTS_WIN, "");
	
	if(stime->redraws & TIME_ALL_IMAGE_WIN) icon= ICON_CHECKBOX_HLT;
	else icon= ICON_CHECKBOX_DEHLT;
	uiDefIconTextBut(block, BUTM, 1, icon, "Image Windows",      0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, TIME_ALL_IMAGE_WIN, "");
	
	/* Add sequencer only redraw*/
	if(stime->redraws & TIME_SEQ) icon= ICON_CHECKBOX_HLT;
	else icon= ICON_CHECKBOX_DEHLT;
	uiDefIconTextBut(block, BUTM, 1, icon, "Sequencer Windows",      0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, TIME_SEQ, "");
	
	uiDefBut(block, SEPR, 0, "",        0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	
	sprintf(str, "Set Frames/Sec (%d/%f)", scene->r.frs_sec, scene->r.frs_sec_base);
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, str,	 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 1001, "");
	
	uiDefBut(block, SEPR, 0, "",        0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	
	if(stime->redraws & TIME_CONTINUE_PHYSICS) icon= ICON_CHECKBOX_HLT;
	else icon= ICON_CHECKBOX_DEHLT;
	uiDefIconTextBut(block, BUTM, 1, icon, "Continue Physics",      0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, TIME_CONTINUE_PHYSICS, "During playblack, continue physics simulations regardless of the frame number");
	
	
	if(curarea->headertype==HEADERTOP) {
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

static void do_time_viewmenu(bContext *C, void *arg, int event)
{
	ScrArea *curarea= CTX_wm_area(C);
	SpaceTime *stime= (SpaceTime*)CTX_wm_space_data(C);
	View2D *v2d= UI_view2d_fromcontext_rwin(C);
	Scene *scene= CTX_data_scene(C);
	int first;
	
	switch(event) {
		case 2: /* Play Back Animation */
			//if(!has_screenhandler(G.curscreen, SCREEN_HANDLER_ANIM))
			//	start_animated_screen(stime);
			break;
		case 3: /* View All */
			if(v2d) {
				first= scene->r.sfra;
				if(first >= scene->r.efra) first= scene->r.efra;
					v2d->cur.xmin=v2d->tot.xmin= (float)first-2;
				v2d->cur.xmax=v2d->tot.xmax= (float)scene->r.efra+2;
			
				ED_area_tag_redraw(curarea);
			}
			break;
		case 4: /* Maximize Window */
			/* using event B_FULL */
			break;
		case 5:	/* show time or frames */
			stime->flag ^= TIME_DRAWFRAMES;
			ED_area_tag_redraw(curarea);
			break;
		case 6:
			//nextprev_marker(1);
			break;
		case 7:
			//nextprev_marker(-1);
			break;
		case 8:
			//nextprev_timeline_key(1);
			break;
		case 9:
			//nextprev_timeline_key(-1);
			break;
		case 10:
			//timeline_frame_to_center();
			break;
		case 11:
			if(v2d) {
				v2d->flag ^= V2D_VIEWSYNC_SCREEN_TIME;
				UI_view2d_sync(CTX_wm_screen(C), CTX_wm_area(C), v2d, V2D_LOCK_SET);
			}
			break;
		case 12: /* only show keyframes from selected data */
			stime->flag ^= TIME_ONLYACTSEL;
			ED_area_tag_redraw(curarea);
			break;
	}
}

static uiBlock *time_viewmenu(bContext *C, ARegion *ar, void *arg_unused)
{
	ScrArea *curarea= CTX_wm_area(C);
	SpaceTime *stime= (SpaceTime*)CTX_wm_space_data(C);
	View2D *v2d= UI_view2d_fromcontext_rwin(C);
	uiBlock *block;
	short yco= 0, menuwidth=120;
	
	block= uiBeginBlock(C, ar, "time_viewmenu", UI_EMBOSSP, UI_HELV);
	uiBlockSetButmFunc(block, do_time_viewmenu, NULL);
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Play Back Animation", 0, yco-=20,
					 menuwidth, 19, NULL, 0.0, 0.0, 1, 2, "");
	
	uiDefBut(block, SEPR, 0, "",        0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	
	if(stime->flag & TIME_DRAWFRAMES)
		uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Show Seconds|Ctrl T", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 5, "");
	else 
		uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Show Frames|Ctrl T", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 5, "");
	
	uiDefIconTextBut(block, BUTM, 1, (stime->flag & TIME_ONLYACTSEL)?ICON_CHECKBOX_HLT:ICON_CHECKBOX_DEHLT, 
					 "Only Selected Data Keys|", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 12, "");
	
	uiDefBut(block, SEPR, 0, "",        0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Jump To Next Marker|PageUp", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 6, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Jump To Prev Marker|PageDown", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 7, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Jump To Next Key|Ctrl PageUp", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 8, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Jump To Prev Key|Ctrl PageDown", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 9, "");
	
	uiDefBut(block, SEPR, 0, "",        0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Center View|C", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 10, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "View All|Home", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 3, "");
	uiDefIconTextBut(block, BUTM, 1, (v2d->flag & V2D_VIEWSYNC_SCREEN_TIME)?ICON_CHECKBOX_HLT:ICON_CHECKBOX_DEHLT, 
					 "Lock Time to Other Windows|", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 11, "");
	
//	if (!curarea->full) 
//		uiDefIconTextBut(block, BUTM, B_FULL, ICON_BLANK1, "Maximize Window|Ctrl UpArrow", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 4, "");
//	else 
//		uiDefIconTextBut(block, BUTM, B_FULL, ICON_BLANK1, "Tile Window|Ctrl DownArrow", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 4, "");
	
	if(curarea->headertype==HEADERTOP) {
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

static void do_time_framemenu(bContext *C, void *arg, int event)
{
	Scene *scene= CTX_data_scene(C);

	switch(event) {
		case 1: /*Set as Start */
			if (scene->r.psfra) {
				if (scene->r.pefra < scene->r.cfra)
					scene->r.pefra= scene->r.cfra;
				scene->r.psfra= scene->r.cfra;
			}				
			else
				scene->r.sfra = scene->r.cfra;
			WM_event_add_notifier(C, NC_SCENE|ND_RENDER_OPTIONS, scene);
			break;
		case 2: /* Set as End */
			if (scene->r.psfra) {
				if (scene->r.cfra < scene->r.psfra)
					scene->r.psfra= scene->r.cfra;
				scene->r.pefra= scene->r.cfra;
			}				
			else
				scene->r.efra = scene->r.cfra;
			WM_event_add_notifier(C, NC_SCENE|ND_RENDER_OPTIONS, scene);
			break;
		case 3: /* Rename Marker */
			//rename_marker();
			break;
	}
}

static uiBlock *time_framemenu(bContext *C, ARegion *ar, void *arg_unused)
{
	ScrArea *curarea= CTX_wm_area(C);
	uiBlock *block;
	short yco= 0, menuwidth=120;
	
	block= uiBeginBlock(C, ar, "time_framemenu", UI_EMBOSSP, UI_HELV);
	uiBlockSetButmFunc(block, do_time_framemenu, NULL);

	uiDefIconTextButO(block, BUTM, "MARKER_OT_add", WM_OP_EXEC_REGION_WIN, ICON_BLANK1, "Add Marker",
					  0, yco-=2, menuwidth, 19, "");
	uiDefIconTextButO(block, BUTM, "MARKER_OT_duplicate", WM_OP_EXEC_REGION_WIN, ICON_BLANK1, "Duplicate Marker",
					  0, yco-=20, menuwidth, 19, "");
	uiDefIconTextButO(block, BUTM, "MARKER_OT_delete", WM_OP_EXEC_REGION_WIN, ICON_BLANK1, "Delete Marker",
					  0, yco-=20, menuwidth, 19, "");
	
	uiDefBut(block, SEPR, 0, "",        0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Name Marker|Ctrl M",
					 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 3, "");
	uiDefIconTextButO(block, BUTM, "MARKER_OT_move", WM_OP_INVOKE_REGION_WIN, ICON_BLANK1, "Grab/Move Marker",
					  0, yco-=20, menuwidth, 19, "");
	
	uiDefBut(block, SEPR, 0, "", 0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Set as Start|S",
					 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 1, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Set as End|E",
					 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 1, 2, "");
	
	if(curarea->headertype==HEADERTOP) {
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


#define B_REDRAWALL		750
#define B_TL_REW		751
#define B_TL_PLAY		752
#define B_TL_FF			753
#define B_TL_PREVKEY	754
#define B_TL_NEXTKEY	755
#define B_TL_STOP		756
#define B_TL_PREVIEWON	757
#define B_TL_INSERTKEY	758
#define B_TL_DELETEKEY	759

#define B_FLIPINFOMENU 0
#define B_NEWFRAME 0
#define B_DIFF 0


void do_time_buttons(bContext *C, void *arg, int event)
{
//	SpaceTime *stime= (SpaceTime*)CTX_wm_space_data(C);
	Scene *scene= CTX_data_scene(C);
	
	switch(event) {
		case B_REDRAWALL:
			WM_event_add_notifier(C, NC_SCENE|ND_RENDER_OPTIONS, scene);
			break;
		case B_NEWFRAME:
			WM_event_add_notifier(C, NC_SCENE|ND_FRAME, scene);
			break;
		case B_TL_REW:
			scene->r.cfra= PSFRA;
			WM_event_add_notifier(C, NC_SCENE|ND_FRAME, scene);
			//update_for_newframe();
			break;
		case B_TL_PLAY:
			ED_screen_animation_timer(C, 1);
			break;
		case B_TL_STOP:
			ED_screen_animation_timer(C, 0);
			break;
		case B_TL_FF:
			/* end frame */
			scene->r.cfra= PEFRA;
			WM_event_add_notifier(C, NC_SCENE|ND_FRAME, scene);
			//update_for_newframe();
			break;
		case B_TL_PREVKEY:
			/* previous keyframe */
			//nextprev_timeline_key(-1);
			break;
		case B_TL_NEXTKEY:
			/* next keyframe */
			//nextprev_timeline_key(1);
			break;
			
		case B_TL_PREVIEWON:
			if (scene->r.psfra) {
				/* turn on preview range */
				scene->r.psfra= scene->r.sfra;
				scene->r.pefra= scene->r.efra;
			}
			else {
				/* turn off preview range */
				scene->r.psfra= 0;
				scene->r.pefra= 0;
			}
			//BIF_undo_push("Set anim-preview range");
			WM_event_add_notifier(C, NC_SCENE|ND_RENDER_OPTIONS, scene);
			break;
			
		case B_TL_INSERTKEY:
			/* insert keyframe */
			//common_insertkey();
			//allqueue(REDRAWTIME, 1);
			break;
		case B_TL_DELETEKEY:
			/* delete keyframe */
			//common_deletekey();
			//allqueue(REDRAWTIME, 1);
			break;
	}
}


void time_header_buttons(const bContext *C, ARegion *ar)
{
	ScrArea *sa= CTX_wm_area(C);
	SpaceTime *stime= (SpaceTime*)CTX_wm_space_data(C);
	Scene *scene= CTX_data_scene(C);
	uiBlock *block;
	int xco, yco= 3;
	char *menustr= NULL;
	
	block= uiBeginBlock(C, ar, "header buttons", UI_EMBOSS, UI_HELV);
	uiBlockSetHandleFunc(block, do_time_buttons, NULL);
	
	xco= ED_area_header_standardbuttons(C, block, yco);
	
	if((sa->flag & HEADER_NO_PULLDOWN)==0) {
		int xmax;
		
		/* pull down menus */
		uiBlockSetEmboss(block, UI_EMBOSSP);
		
		xmax= GetButStringLength("View");
		uiDefPulldownBut(block, time_viewmenu, sa, 
						 "View", xco, yco-2, xmax-3, 24, "");
		xco+= xmax;
		xmax= GetButStringLength("Frame");
		uiDefPulldownBut(block, time_framemenu, sa, 
						 "Frame", xco, yco-2, xmax-3, 24, "");
		xco+= xmax;
		
		xmax= GetButStringLength("Playback");
		uiDefPulldownBut(block, time_redrawmenu, sa, 
						 "Playback", xco, yco-2, xmax-3, 24, "");
		xco+= xmax;
	}
	
	uiBlockSetEmboss(block, UI_EMBOSS);
	
	uiBlockBeginAlign(block);
	
	uiDefButI(block, TOG, B_TL_PREVIEWON,"PR",	
			  xco,yco, XIC*2, YIC,
			  &scene->r.psfra,0, 1, 0, 0,
			  "Show settings for frame range of animation preview");
	
	xco += XIC*2;
	
	if (scene->r.psfra) {
		uiDefButI(block, NUM, B_REDRAWALL,"Start:",	
				  xco,yco, (int)4.5*XIC, YIC,
				  &scene->r.psfra,MINFRAMEF, MAXFRAMEF, 0, 0,
				  "The start frame of the animation preview (inclusive)");
		
		xco += (int)(4.5*XIC);
		
		uiDefButI(block, NUM, B_REDRAWALL,"End:",	
				  xco,yco, (int)4.5*XIC,YIC,
				  &scene->r.pefra,(float)PSFRA, MAXFRAMEF, 0, 0,
				  "The end frame of the animation preview (inclusive)");
	}
	else {
		uiDefButI(block, NUM, B_REDRAWALL,"Start:",	
				  xco,yco, (int)4.5*XIC, YIC,
				  &scene->r.sfra,MINFRAMEF, MAXFRAMEF, 0, 0,
				  "The start frame of the animation (inclusive)");
		
		xco += (short)(4.5*XIC);
		
		uiDefButI(block, NUM, B_REDRAWALL,"End:",	
				  xco,yco, (int)4.5*XIC,YIC,
				  &scene->r.efra,(float)SFRA, MAXFRAMEF, 0, 0,
				  "The end frame of the animation (inclusive)");
	}
	uiBlockEndAlign(block);
	
	xco += (short)(4.5 * XIC + 16);
	
	uiDefButI(block, NUM, B_NEWFRAME, "",
			  xco,yco, (int)3.5*XIC,YIC,
			  &(scene->r.cfra), MINFRAMEF, MAXFRAMEF, 0, 0,
			  "Displays Current Frame of animation");
	
	xco += (short)(3.5 * XIC + 16);
	
	uiDefIconBut(block, BUT, B_TL_REW, ICON_REW,
				 xco, yco, XIC, YIC, 0, 0, 0, 0, 0, "Skip to Start frame (Shift DownArrow)");
	xco+= XIC+4;
	uiDefIconBut(block, BUT, B_TL_PREVKEY, ICON_PREV_KEYFRAME,
				 xco, yco, XIC, YIC, 0, 0, 0, 0, 0, "Skip to previous keyframe (Ctrl PageDown)");
	xco+= XIC+4;
	
	if(CTX_wm_screen(C)->animtimer)
		uiDefIconBut(block, BUT, B_TL_STOP, ICON_PAUSE,
					 xco, yco, XIC, YIC, 0, 0, 0, 0, 0, "Stop Playing Timeline");
	else 	   
		uiDefIconBut(block, BUT, B_TL_PLAY, ICON_PLAY,
					 xco, yco, XIC, YIC, 0, 0, 0, 0, 0, "Play Timeline ");
	
	xco+= XIC+4;
	uiDefIconBut(block, BUT, B_TL_NEXTKEY, ICON_NEXT_KEYFRAME,
				 xco, yco, XIC, YIC, 0, 0, 0, 0, 0, "Skip to next keyframe (Ctrl PageUp)");
	xco+= XIC+4;
	uiDefIconBut(block, BUT, B_TL_FF, ICON_FF,
				 xco, yco, XIC, YIC, 0, 0, 0, 0, 0, "Skip to End frame (Shift UpArrow)");
	xco+= XIC+8;
	
	uiBlockBeginAlign(block);
		uiDefIconButBitS(block, TOG, AUTOKEY_ON, B_REDRAWALL, ICON_REC,
						 xco, yco, XIC, YIC, &(scene->autokey_mode), 0, 0, 0, 0, "Automatic keyframe insertion for Objects and Bones");
		xco+= XIC;
		if (IS_AUTOKEY_ON(scene)) {
			uiDefButS(block, MENU, B_REDRAWALL, 
					  "Auto-Keying Mode %t|Add/Replace Keys%x3|Replace Keys %x5", 
					  xco, yco, (int)5.5*XIC, YIC, &(scene->autokey_mode), 0, 1, 0, 0, 
					  "Mode of automatic keyframe insertion for Objects and Bones");
			xco+= (6*XIC);
		}
	uiBlockEndAlign(block);
	
	xco+= 16;
	
	
	menustr= ANIM_build_keyingsets_menu(&scene->keyingsets, 0);
	uiDefButI(block, MENU, B_DIFF, 
				  menustr, 
				  xco, yco, (int)5.5*XIC, YIC, &(scene->active_keyingset), 0, 1, 0, 0, 
				  "Active Keying Set (i.e. set of channels to Insert Keyframes for)");
	MEM_freeN(menustr);
	xco+= (6*XIC);
	
	uiBlockBeginAlign(block);
		uiDefIconButO(block, BUT, "ANIM_OT_delete_keyframe", WM_OP_INVOKE_REGION_WIN, ICON_KEY_DEHLT, xco,yco,XIC,YIC, "Delete Keyframes for the Active Keying Set (Alt-I)");
		xco += XIC;
		uiDefIconButO(block, BUT, "ANIM_OT_insert_keyframe", WM_OP_INVOKE_REGION_WIN, ICON_KEY_HLT, xco,yco,XIC,YIC, "Insert Keyframes for the Active Keying Set (I)");
		xco += XIC;
	uiBlockEndAlign(block);
	
	xco+= 16;
	
	uiDefIconButBitI(block, TOG, TIME_WITH_SEQ_AUDIO, B_DIFF, ICON_SPEAKER,
					 xco, yco, XIC, YIC, &(stime->redraws), 0, 0, 0, 0, "Play back and sync with audio from Sequence Editor");
	
	
	/* always as last  */
	UI_view2d_totRect_set(&ar->v2d, xco+XIC+80, (int)(ar->v2d.tot.ymax-ar->v2d.tot.ymin));
	
	uiEndBlock(C, block);
	uiDrawBlock(C, block);
}



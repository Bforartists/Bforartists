/**
 * header_seq.c oct-2003
 *
 * Functions to draw the "Video Sequence Editor" window header
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

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

#ifdef WIN32
#include "BLI_winstuff.h"
#endif

#include "BMF_Api.h"
#include "BIF_language.h"
#ifdef INTERNATIONAL
#include "FTF_Api.h"
#endif

#include "DNA_ID.h"
#include "DNA_scene_types.h"
#include "DNA_screen_types.h"
#include "DNA_sequence_types.h"
#include "DNA_space_types.h"
#include "BKE_global.h"
#include "BKE_main.h"
#include "BIF_interface.h"
#include "BIF_resources.h"
#include "BIF_screen.h"
#include "BIF_space.h"
#include "BIF_editseq.h"
#include "BSE_drawipo.h"
#include "BSE_headerbuttons.h"
#include "BSE_sequence.h"

#include "blendef.h"
#include "mydevice.h"

static int viewmovetemp = 0;

extern Sequence *last_seq;

static void do_seq_viewmenu(void *arg, int event)
{
	switch(event)
	{
	case 1:
		do_seq_buttons(B_SEQHOME);
		break;
	case 2:
		if(last_seq) {
				CFRA= last_seq->startdisp;
				G.v2d->cur.xmin= last_seq->startdisp- (last_seq->len/20);
				G.v2d->cur.xmax= last_seq->enddisp+ (last_seq->len/20);
				update_for_newframe();
		}
		break;
	}
}

static uiBlock *seq_viewmenu(void *arg_unused)
{
	uiBlock *block;
	short yco= 0, menuwidth=120;

	block= uiNewBlock(&curarea->uiblocks, "seq_viewmenu", UI_EMBOSSP, UI_HELV, curarea->headwin);
	uiBlockSetButmFunc(block, do_seq_viewmenu, NULL);

	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Frame All|Home", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 1, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Frame Selected|NumPad .", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 2, "");
	uiDefBut(block, SEPR, 0, "",        0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");

	if(!curarea->full) uiDefIconTextBut(block, BUTM, B_FULL, ICON_BLANK1, "Maximize Window|Ctrl UpArrow", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0,0, "");
	else uiDefIconTextBut(block, BUTM, B_FULL, ICON_BLANK1, "Tile Window|Ctrl DownArrow", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 0, "");

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

static void do_seq_selectmenu(void *arg, int event)
{
	switch(event)
	{
	case 0:
		borderselect_seq();
		break;
	case 1:
		swap_select_seq();
		break;
	}
}

static uiBlock *seq_selectmenu(void *arg_unused)
{
	uiBlock *block;
	short yco= 0, menuwidth=120;

	block= uiNewBlock(&curarea->uiblocks, "seq_selectmenu", UI_EMBOSSP, UI_HELV, curarea->headwin);
	uiBlockSetButmFunc(block, do_seq_selectmenu, NULL);

	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Border Select|B", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 0, "");
	uiDefBut(block, SEPR, 0, "",        0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Select/Deselect All|A", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 1, "");

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

static void do_seq_addmenu_effectmenu(void *arg, int event)
{
	switch(event)
	{
	case 0:
		add_sequence(SEQ_ADD);
		break;
	case 1:
		add_sequence(SEQ_SUB);
		break;
	case 2:
		add_sequence(SEQ_MUL);
		break;
	case 3:
		add_sequence(SEQ_CROSS);
		break;
	case 4:
		add_sequence(SEQ_GAMCROSS);
		break;
	case 5:
		add_sequence(SEQ_ALPHAOVER);
		break;
	case 6:
		add_sequence(SEQ_ALPHAUNDER);
		break;
	case 7:
		add_sequence(SEQ_OVERDROP);
		break;
	case 8:
		add_sequence(SEQ_PLUGIN);
		break;
	}
}

static uiBlock *seq_addmenu_effectmenu(void *arg_unused)
{
	uiBlock *block;
	short yco = 20, menuwidth = 120;

	block= uiNewBlock(&curarea->uiblocks, "seq_addmenu_effectmenu", UI_EMBOSSP, UI_HELV, G.curscreen->mainwin);
	uiBlockSetButmFunc(block, do_seq_addmenu_effectmenu, NULL);

	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Add", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 0, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Sub", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 1, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Mul", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 2, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Cross", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 3, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "GammaCross", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 4, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "AlphaOver", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 5, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "AlphaUnder", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 6, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "AlphaOverDrop", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 7, "");
	uiDefBut(block, SEPR, 0, "",        0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Plugin...", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 8, "");


	uiBlockSetDirection(block, UI_RIGHT);
	uiTextBoundsBlock(block, 60);
	
	return block;
}


static void do_seq_addmenu(void *arg, int event)
{
	switch(event)
	{
	case 0:
		add_sequence(SEQ_IMAGE);
		break;
	case 1:
		add_sequence(SEQ_MOVIE);
		break;
	case 2:
		add_sequence(SEQ_SOUND);
		break;
	case 3:
		add_sequence(SEQ_SCENE);
		break;
	}
}

static uiBlock *seq_addmenu(void *arg_unused)
{
	uiBlock *block;
	short yco = 20, menuwidth = 120;

	block= uiNewBlock(&curarea->uiblocks, "seq_addmenu", UI_EMBOSSP, UI_HELV, curarea->headwin);
	uiBlockSetButmFunc(block, do_seq_addmenu, NULL);

	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Images", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 0, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Movie", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 1, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Audio", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 2, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Scene", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 3, "");
	uiDefIconTextBlockBut(block, seq_addmenu_effectmenu, NULL, ICON_RIGHTARROW_THIN, "Effect", 0, yco-=20, 120, 19, "");	

	if(curarea->headertype==HEADERTOP) {
		uiBlockSetDirection(block, UI_DOWN);
	}
	else {
		uiBlockSetDirection(block, UI_TOP);
	}

	uiTextBoundsBlock(block, 50);

	return block;
}


static void do_seq_editmenu(void *arg, int event)
{
	SpaceSeq *sseq;

	sseq= curarea->spacedata.first;

	switch(event)
	{
	case 1: /* Change Strip... */
		change_sequence();
		break;
	case 2: /* Make Meta Strip */
		make_meta();
		break;
	case 3: /* Separate Meta Strip */
		un_meta();
		break;
	case 4: /* Meta Properties... */
		clever_numbuts_seq();
		break;
	case 5: /* Duplicate */
		add_duplicate_seq();
		break;
	case 6: /* Delete */
		del_seq();
		break;
	case 7: /* Snap menu */
		seq_snapmenu();
		break;
	case 8:
		set_filter_seq();
		break;
	case 9:
		enter_meta();
		break;
	case 10:
		exit_meta();
		break;
	}
}

static uiBlock *seq_editmenu(void *arg_unused)
{
	uiBlock *block;
	Editing *ed;
	short yco= 0, menuwidth=120;

	ed = G.scene->ed;

	block= uiNewBlock(&curarea->uiblocks, "seq_editmenu", UI_EMBOSSP, UI_HELV, curarea->headwin);
	uiBlockSetButmFunc(block, do_seq_editmenu, NULL);

	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Snap...|Shift S", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 7, "");

	uiDefBut(block, SEPR, 0, "",        0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");

	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Duplicate|Shift D", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 5, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Delete|X", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 6, "");

	if (last_seq != NULL && last_seq->type != SEQ_MOVIE) {
		uiDefBut(block, SEPR, 0, "",        0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");

		if(last_seq->type >= SEQ_EFFECT) uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Change Effect...|C", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 1, "");
		else if(last_seq->type == SEQ_IMAGE) uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Change Image...|C", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 1, "");
		else uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Change Scene...|C", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 1, "");
	}

/*	if (last_seq != NULL && last_seq->type == SEQ_MOVIE) {
		uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Set Filter Y|F", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 8, "");
	}
*/

	uiDefBut(block, SEPR, 0, "",        0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Make Meta Strip...|M", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 2, "");
	uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Separate Meta Strip...|Alt M", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 3, "");
	if ((ed != NULL) && (ed->metastack.first > 0)){
		uiDefBut(block, SEPR, 0, "",        0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
		uiDefIconTextBut(block, BUTM, 1, ICON_CHECKBOX_HLT, "Enter/Exit Meta Strip|Tab", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 10, "");
	}
	else {
		if (last_seq != NULL && last_seq->type == SEQ_META) {
			uiDefBut(block, SEPR, 0, "",        0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
			uiDefIconTextBut(block, BUTM, 1, ICON_CHECKBOX_DEHLT, "Enter/Exit Meta Strip|Tab", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 9, "");
		}
	}
	if(last_seq != NULL) {
		if(last_seq->type == SEQ_META) {
			uiDefBut(block, SEPR, 0, "",        0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
			uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Meta Properties...|N", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 4, "");
		}
		else if(last_seq->type == SEQ_PLUGIN) {
			uiDefBut(block, SEPR, 0, "",        0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
			uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Plugin Properties...|N", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 4, "");
		}
		else if(last_seq->type == SEQ_MOVIE) {
			uiDefBut(block, SEPR, 0, "",        0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
			uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Movie Properties...|N", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 4, "");
		}
		else if(last_seq->type == SEQ_SOUND) {
			uiDefBut(block, SEPR, 0, "",        0, yco-=6, menuwidth, 6, NULL, 0.0, 0.0, 0, 0, "");
			uiDefIconTextBut(block, BUTM, 1, ICON_BLANK1, "Sound Properties...|N", 0, yco-=20, menuwidth, 19, NULL, 0.0, 0.0, 0, 4, "");
		}

	}

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


void do_seq_buttons(short event)
{
	Editing *ed;

	ed= G.scene->ed;
	if(ed==0) return;

	switch(event) {
	case B_SEQHOME:
		G.v2d->cur= G.v2d->tot;
		test_view2d(G.v2d, curarea->winx, curarea->winy);
		scrarea_queue_winredraw(curarea);
		break;
	case B_SEQCLEAR:
		free_imbuf_seq();
		allqueue(REDRAWSEQ, 1);
		break;
	}
}

void seq_buttons()
{
	SpaceSeq *sseq;
	short xco;
	char naam[20];
	uiBlock *block;
	short xmax;

	sseq= curarea->spacedata.first;

	sprintf(naam, "header %d", curarea->headwin);
	block= uiNewBlock(&curarea->uiblocks, naam, UI_EMBOSS, UI_HELV, curarea->headwin);

	if(area_is_active_area(curarea)) uiBlockSetCol(block, TH_HEADER);
	else uiBlockSetCol(block, TH_HEADERDESEL);

	curarea->butspacetype= SPACE_SEQ;

	xco = 8;
	
	uiDefIconTextButC(block, ICONTEXTROW,B_NEWSPACE, ICON_VIEW3D, windowtype_pup(), xco,0,XIC+10,YIC, &(curarea->butspacetype), 1.0, SPACEICONMAX, 0, 0, "Displays Current Window Type. Click for menu of available types.");

	xco+= XIC+22;

	/* pull down menus */
	uiBlockSetEmboss(block, UI_EMBOSSP);

	xmax= GetButStringLength("View");
	uiDefBlockBut(block,seq_viewmenu, NULL, "View", xco, 0, xmax, 20, "");
	xco+=xmax;

	xmax= GetButStringLength("Select");
	uiDefBlockBut(block,seq_selectmenu, NULL, "Select", xco, 0, xmax, 20, "");
	xco+=xmax;

	xmax= GetButStringLength("Add");
	uiDefBlockBut(block, seq_addmenu, NULL, "Add", xco, 0, xmax, 20, "");
	xco+= xmax;

	xmax= GetButStringLength("Strip");
	uiDefBlockBut(block, seq_editmenu, NULL, "Strip", xco, 0, xmax, 20, "");
	xco+= xmax;

	/* end of pull down menus */
	uiBlockSetEmboss(block, UI_EMBOSSX);

	xco+= 10;
	
	/* IMAGE */
	uiDefIconButS(block, TOG, B_REDR, ICON_IMAGE_COL,	xco,0,XIC,YIC, &sseq->mainb, 0, 0, 0, 0, "Toggles image display");

	/* ZOOM and BORDER */
	xco+= XIC;
	uiDefIconButI(block, TOG, B_VIEW2DZOOM, ICON_VIEWZOOM,	xco+=XIC,0,XIC,YIC, &viewmovetemp, 0, 0, 0, 0, "Zooms view in and out (CTRL+MiddleMouse)");
	uiDefIconBut(block, BUT, B_IPOBORDER, ICON_BORDERMOVE,	xco+=XIC,0,XIC,YIC, 0, 0, 0, 0, 0, "Zooms view to fit area");

	/* CLEAR MEM */
	xco+= XIC;
	uiDefBut(block, BUT, B_SEQCLEAR, "Clear",	xco+=XIC,0,2*XIC,YIC, 0, 0, 0, 0, 0, "Forces a clear of all buffered images in memory");
	
	uiDrawBlock(block);
}

/**
 * $Id: file_header.c 21247 2009-06-29 21:50:53Z jaguarandi $
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

#include "DNA_space_types.h"
#include "DNA_scene_types.h"
#include "DNA_screen_types.h"
#include "DNA_windowmanager_types.h"

#include "MEM_guardedalloc.h"

#include "BLI_blenlib.h"

#include "BKE_context.h"
#include "BKE_screen.h"
#include "BKE_global.h"

#include "ED_screen.h"
#include "ED_types.h"
#include "ED_util.h"
#include "ED_fileselect.h"

#include "WM_api.h"
#include "WM_types.h"

#include "BIF_gl.h"
#include "BIF_glutil.h"

#include "UI_interface.h"
#include "UI_resources.h"
#include "UI_view2d.h"

#include "file_intern.h"
#include "filelist.h"

#define B_SORTIMASELLIST 1
#define B_RELOADIMASELDIR 2
#define B_FILTERIMASELDIR 3
#define B_HIDEDOTFILES 4

/* ************************ header area region *********************** */

static void do_file_header_buttons(bContext *C, void *arg, int event)
{
	SpaceFile *sfile= (SpaceFile*)CTX_wm_space_data(C);
	switch(event) {
		case B_SORTIMASELLIST:
			filelist_sort(sfile->files, sfile->params->sort);
			WM_event_add_notifier(C, NC_WINDOW, NULL);
			break;
		case B_RELOADIMASELDIR:
			WM_event_add_notifier(C, NC_WINDOW, NULL);
			break;
		case B_FILTERIMASELDIR:
			if(sfile->params) {
				if (sfile->params->flag & FILE_FILTER) {
					filelist_setfilter(sfile->files,sfile->params->filter);
					filelist_filter(sfile->files);
				} else {
					filelist_setfilter(sfile->files,0);
					filelist_filter(sfile->files);
				}
			}
			WM_event_add_notifier(C, NC_WINDOW, NULL);
			break;
		case B_HIDEDOTFILES:
			if(sfile->params) {
				filelist_free(sfile->files);
				filelist_hidedot(sfile->files, sfile->params->flag & FILE_HIDE_DOT);
				WM_event_add_notifier(C, NC_WINDOW, NULL);
			}
			break;
	}
}


void file_header_buttons(const bContext *C, ARegion *ar)
{
	SpaceFile *sfile= (SpaceFile*)CTX_wm_space_data(C);
	FileSelectParams* params = ED_fileselect_get_params(sfile);

	uiBlock *block;
	int xco, yco= 3;
	int xcotitle;
	
	block= uiBeginBlock(C, ar, "header buttons", UI_EMBOSS);
	uiBlockSetHandleFunc(block, do_file_header_buttons, NULL);
	
	xco= ED_area_header_standardbuttons(C, block, yco);
	
	/*
	if((sa->flag & HEADER_NO_PULLDOWN)==0) {
		int xmax;
		
		xmax= GetButStringLength("View");
		uiDefPulldownBut(block, dummy_viewmenu, CTX_wm_area(C), 
						 "View", xco, yco-2, xmax-3, 24, "");
		xco+=XIC+xmax;
	}
	 */
	
	xco += 5;

	uiBlockBeginAlign(block);
	uiDefIconButO(block, BUT, "FILE_OT_parent", WM_OP_INVOKE_DEFAULT, ICON_FILE_PARENT, xco+=XIC, yco, 20, 20, "Navigate to Parent Folder");
	uiDefIconButO(block, BUT, "FILE_OT_refresh", WM_OP_INVOKE_DEFAULT, ICON_FILE_REFRESH, xco+=XIC, yco, 20, 20, "Refresh List of Files");
	uiBlockEndAlign(block);

	xco += 5;
	
	uiBlockBeginAlign(block);
	uiDefIconButS(block, ROW, B_RELOADIMASELDIR, ICON_SHORTDISPLAY,	xco+=XIC, yco, XIC,YIC, &params->display, 1.0, FILE_SHORTDISPLAY, 0, 0, "Displays short file description");
	uiDefIconButS(block, ROW, B_RELOADIMASELDIR, ICON_LONGDISPLAY,	xco+=XIC, yco, XIC,YIC, &params->display, 1.0, FILE_LONGDISPLAY, 0, 0, "Displays long file description");
	uiDefIconButS(block, ROW, B_RELOADIMASELDIR, ICON_IMGDISPLAY,	xco+=XIC, yco, XIC,YIC, &params->display, 1.0, FILE_IMGDISPLAY, 0, 0, "Displays files as thumbnails");
	uiBlockEndAlign(block);
	
	xco+=XIC;

	
	uiBlockBeginAlign(block);
	uiDefIconButS(block, ROW, B_SORTIMASELLIST, ICON_SORTALPHA,	xco+=XIC, yco, XIC,YIC, &params->sort, 1.0, 0.0, 0, 0, "Sorts files alphabetically");
	uiDefIconButS(block, ROW, B_SORTIMASELLIST, ICON_SORTBYEXT,	xco+=XIC, yco, XIC,YIC, &params->sort, 1.0, 3.0, 0, 0, "Sorts files by extension");	
	uiDefIconButS(block, ROW, B_SORTIMASELLIST, ICON_SORTTIME,	xco+=XIC, yco, XIC,YIC, &params->sort, 1.0, 1.0, 0, 0, "Sorts files by time");
	uiDefIconButS(block, ROW, B_SORTIMASELLIST, ICON_SORTSIZE,	xco+=XIC, yco, XIC,YIC, &params->sort, 1.0, 2.0, 0, 0, "Sorts files by size");	
	uiBlockEndAlign(block);
	
	xco+=XIC;
	uiDefIconButBitS(block, TOG, FILE_HIDE_DOT, B_HIDEDOTFILES, ICON_GHOST,xco+=XIC,yco,XIC,YIC, &params->flag, 0, 0, 0, 0, "Hide dot files");
	xco+=XIC;
	uiDefIconButBitS(block, TOG, FILE_FILTER, B_FILTERIMASELDIR, ICON_FILTER,xco+=XIC,yco,XIC,YIC, &params->flag, 0, 0, 0, 0, "Filter files");

	if (params->flag & FILE_FILTER) {
		xco+=4;
		uiBlockBeginAlign(block);
		uiDefIconButBitS(block, TOG, IMAGEFILE, B_FILTERIMASELDIR, ICON_FILE_IMAGE,xco+=XIC,yco,XIC,YIC, &params->filter, 0, 0, 0, 0, "Show images");
		uiDefIconButBitS(block, TOG, BLENDERFILE, B_FILTERIMASELDIR, ICON_FILE_BLEND,xco+=XIC,yco,XIC,YIC, &params->filter, 0, 0, 0, 0, "Show .blend files");
		uiDefIconButBitS(block, TOG, MOVIEFILE, B_FILTERIMASELDIR, ICON_FILE_MOVIE,xco+=XIC,yco,XIC,YIC, &params->filter, 0, 0, 0, 0, "Show movies");
		uiDefIconButBitS(block, TOG, PYSCRIPTFILE, B_FILTERIMASELDIR, ICON_FILE_SCRIPT,xco+=XIC,yco,XIC,YIC, &params->filter, 0, 0, 0, 0, "Show python scripts");
		uiDefIconButBitS(block, TOG, FTFONTFILE, B_FILTERIMASELDIR, ICON_FILE_FONT,xco+=XIC,yco,XIC,YIC, &params->filter, 0, 0, 0, 0, "Show fonts");
		uiDefIconButBitS(block, TOG, SOUNDFILE, B_FILTERIMASELDIR, ICON_FILE_SOUND,xco+=XIC,yco,XIC,YIC, &params->filter, 0, 0, 0, 0, "Show sound files");
		uiDefIconButBitS(block, TOG, TEXTFILE, B_FILTERIMASELDIR, ICON_FILE_BLANK,xco+=XIC,yco,XIC,YIC, &params->filter, 0, 0, 0, 0, "Show text files");
		uiDefIconButBitS(block, TOG, FOLDERFILE, B_FILTERIMASELDIR, ICON_FILE_FOLDER,xco+=XIC,yco,XIC,YIC, &params->filter, 0, 0, 0, 0, "Show folders");
		uiBlockEndAlign(block);
		xco+=XIC;
	}

	xcotitle= xco;
	xco+= UI_GetStringWidth(params->title);

	uiBlockSetEmboss(block, UI_EMBOSS);

	/* always as last  */
	UI_view2d_totRect_set(&ar->v2d, xco+XIC+80, ar->v2d.tot.ymax-ar->v2d.tot.ymin);
	
	uiEndBlock(C, block);
	uiDrawBlock(C, block);
}




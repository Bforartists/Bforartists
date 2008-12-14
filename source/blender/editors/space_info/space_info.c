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
 * Contributor(s): Blender Foundation
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#include <string.h>
#include <stdio.h>

#include "DNA_object_types.h"
#include "DNA_space_types.h"
#include "DNA_scene_types.h"
#include "DNA_screen_types.h"

#include "MEM_guardedalloc.h"

#include "BLI_blenlib.h"
#include "BLI_arithb.h"
#include "BLI_rand.h"

#include "BKE_colortools.h"
#include "BKE_global.h"
#include "BKE_screen.h"

#include "ED_space_api.h"
#include "ED_screen.h"

#include "BIF_gl.h"

#include "WM_api.h"
#include "WM_types.h"

#include "UI_interface.h"
#include "UI_resources.h"
#include "UI_view2d.h"

#include "ED_markers.h"

#include "info_intern.h"	// own include

/* ******************** default callbacks for info space ***************** */

static SpaceLink *info_new(void)
{
	ARegion *ar;
	SpaceInfo *sinfo;
	
	sinfo= MEM_callocN(sizeof(SpaceInfo), "initinfo");
	sinfo->spacetype= SPACE_INFO;
	
	/* header */
	ar= MEM_callocN(sizeof(ARegion), "header for info");
	
	BLI_addtail(&sinfo->regionbase, ar);
	ar->regiontype= RGN_TYPE_HEADER;
	ar->alignment= RGN_ALIGN_BOTTOM;
	UI_view2d_header_default(&ar->v2d);
	
	/* main area */
	ar= MEM_callocN(sizeof(ARegion), "main area for info");
	
	BLI_addtail(&sinfo->regionbase, ar);
	ar->regiontype= RGN_TYPE_WINDOW;
	
	/* channel list region XXX */

	
	return (SpaceLink *)sinfo;
}

/* not spacelink itself */
static void info_free(SpaceLink *sl)
{	
//	SpaceInfo *sinfo= (SpaceInfo*) sl;
	
}


/* spacetype; init callback */
static void info_init(struct wmWindowManager *wm, ScrArea *sa)
{

}

static SpaceLink *info_duplicate(SpaceLink *sl)
{
	SpaceInfo *sinfon= MEM_dupallocN(sl);
	
	/* clear or remove stuff from old */
	
	return (SpaceLink *)sinfon;
}



/* add handlers, stuff you only do once or on area/region changes */
static void info_main_area_init(wmWindowManager *wm, ARegion *ar)
{
	ListBase *keymap;
	
	UI_view2d_size_update(&ar->v2d, ar->winx, ar->winy);
	
	/* own keymap */
	keymap= WM_keymap_listbase(wm, "info", SPACE_INFO, 0);	/* XXX weak? */
	WM_event_add_keymap_handler_bb(&ar->handlers, keymap, &ar->v2d.mask, &ar->winrct);
}

static void info_main_area_draw(const bContext *C, ARegion *ar)
{
	/* draw entirely, view changes should be handled here */
	// SpaceInfo *sinfo= C->area->spacedata.first;
	View2D *v2d= &ar->v2d;
	float col[3];
	
	/* clear and setup matrix */
	UI_GetThemeColor3fv(TH_BACK, col);
	glClearColor(col[0], col[1], col[2], 0.0);
	glClear(GL_COLOR_BUFFER_BIT);
	
	UI_view2d_view_ortho(C, v2d);
		
	/* data... */
	
	
	/* reset view matrix */
	UI_view2d_view_restore(C);
	
	/* scrollers? */
}

void info_operatortypes(void)
{
	
}

void info_keymap(struct wmWindowManager *wm)
{
	
}

/* add handlers, stuff you only do once or on area/region changes */
static void info_header_area_init(wmWindowManager *wm, ARegion *ar)
{
	UI_view2d_size_update(&ar->v2d, ar->winx, ar->winy);
}

static void info_header_area_draw(const bContext *C, ARegion *ar)
{
	float col[3];
	
	/* clear */
	if(ED_screen_area_active(C))
		UI_GetThemeColor3fv(TH_HEADER, col);
	else
		UI_GetThemeColor3fv(TH_HEADERDESEL, col);
	
	glClearColor(col[0], col[1], col[2], 0.0);
	glClear(GL_COLOR_BUFFER_BIT);
	
	/* set view2d view matrix for scrolling (without scrollers) */
	UI_view2d_view_ortho(C, &ar->v2d);
	
	info_header_buttons(C, ar);
	
	/* restore view matrix? */
	UI_view2d_view_restore(C);
}

static void info_main_area_listener(ARegion *ar, wmNotifier *wmn)
{
	/* context changes */
}

/* only called once, from space/spacetypes.c */
void ED_spacetype_info(void)
{
	SpaceType *st= MEM_callocN(sizeof(SpaceType), "spacetype info");
	ARegionType *art;
	
	st->spaceid= SPACE_INFO;
	
	st->new= info_new;
	st->free= info_free;
	st->init= info_init;
	st->duplicate= info_duplicate;
	st->operatortypes= info_operatortypes;
	st->keymap= info_keymap;
	
	/* regions: main window */
	art= MEM_callocN(sizeof(ARegionType), "spacetype info region");
	art->regionid = RGN_TYPE_WINDOW;
	art->init= info_main_area_init;
	art->draw= info_main_area_draw;
	art->listener= info_main_area_listener;
	art->keymapflag= ED_KEYMAP_VIEW2D;

	BLI_addhead(&st->regiontypes, art);
	
	/* regions: header */
	art= MEM_callocN(sizeof(ARegionType), "spacetype info region");
	art->regionid = RGN_TYPE_HEADER;
	art->minsizey= HEADERY;
	art->keymapflag= ED_KEYMAP_UI|ED_KEYMAP_VIEW2D;
	
	art->init= info_header_area_init;
	art->draw= info_header_area_draw;
	
	BLI_addhead(&st->regiontypes, art);
	
	
	BKE_spacetype_register(st);
}


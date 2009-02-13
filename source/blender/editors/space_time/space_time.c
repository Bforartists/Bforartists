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

#include "DNA_space_types.h"
#include "DNA_scene_types.h"
#include "DNA_screen_types.h"
#include "DNA_windowmanager_types.h"

#include "MEM_guardedalloc.h"

#include "BLI_blenlib.h"

#include "BKE_context.h"
#include "BKE_global.h"
#include "BKE_screen.h"

#include "ED_space_api.h"
#include "ED_screen.h"
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

/* ************************ main time area region *********************** */

/* draws a current frame indicator for the TimeLine */
static void time_draw_cfra_time(const bContext *C, SpaceTime *stime, ARegion *ar)
{
	Scene *scene= CTX_data_scene(C);
	float vec[2];
	
	vec[0]= scene->r.cfra*scene->r.framelen;

	UI_ThemeColor(TH_CFRAME);	// no theme, should be global color once...
	glLineWidth(3.0);

	glBegin(GL_LINES);
		vec[1]= ar->v2d.cur.ymin;
		glVertex2fv(vec);
		vec[1]= ar->v2d.cur.ymax;
		glVertex2fv(vec);
	glEnd();
	
	glLineWidth(1.0);
}

static void time_draw_sfra_efra(const bContext *C, SpaceTime *stime, ARegion *ar)
{
	View2D *v2d= UI_view2d_fromcontext(C);
	Scene *scene= CTX_data_scene(C);
	
	/* draw darkened area outside of active timeline 
	 * frame range used is preview range or scene range */
	UI_ThemeColorShade(TH_BACK, -25);

	if (PSFRA < PEFRA) {
		glRectf(v2d->cur.xmin, v2d->cur.ymin, (float)PSFRA, v2d->cur.ymax);
		glRectf((float)PEFRA, v2d->cur.ymin, v2d->cur.xmax, v2d->cur.ymax);
	}
	else {
		glRectf(v2d->cur.xmin, v2d->cur.ymin, v2d->cur.xmax, v2d->cur.ymax);
	}

	UI_ThemeColorShade(TH_BACK, -60);
	/* thin lines where the actual frames are */
	fdrawline((float)PSFRA, v2d->cur.ymin, (float)PSFRA, v2d->cur.ymax);
	fdrawline((float)PEFRA, v2d->cur.ymin, (float)PEFRA, v2d->cur.ymax);
}

/* add handlers, stuff you only do once or on area/region changes */
static void time_main_area_init(wmWindowManager *wm, ARegion *ar)
{
	ListBase *keymap;
	
	UI_view2d_region_reinit(&ar->v2d, V2D_COMMONVIEW_CUSTOM, ar->winx, ar->winy);
	
	/* own keymap */
	keymap= WM_keymap_listbase(wm, "TimeLine", SPACE_TIME, 0);	/* XXX weak? */
	WM_event_add_keymap_handler_bb(&ar->handlers, keymap, &ar->v2d.mask, &ar->winrct);
}


static void time_main_area_draw(const bContext *C, ARegion *ar)
{
	/* draw entirely, view changes should be handled here */
	SpaceTime *stime= (SpaceTime*)CTX_wm_space_data(C);
	View2D *v2d= &ar->v2d;
	View2DGrid *grid;
	View2DScrollers *scrollers;
	float col[3];
	int unit;
	
	/* clear and setup matrix */
	UI_GetThemeColor3fv(TH_BACK, col);
	glClearColor(col[0], col[1], col[2], 0.0);
	glClear(GL_COLOR_BUFFER_BIT);
	
	UI_view2d_view_ortho(C, v2d);

	/* start and end frame */
	time_draw_sfra_efra(C, stime, ar);

	/* grid */
	unit= (stime->flag & TIME_DRAWFRAMES)? V2D_UNIT_FRAMES: V2D_UNIT_SECONDS;
	grid= UI_view2d_grid_calc(C, v2d, unit, V2D_GRID_CLAMP, V2D_ARG_DUMMY, V2D_ARG_DUMMY, ar->winx, ar->winy);
	UI_view2d_grid_draw(C, v2d, grid, (V2D_VERTICAL_LINES|V2D_VERTICAL_AXIS));
	UI_view2d_grid_free(grid);

	/* current frame */
	time_draw_cfra_time(C, stime, ar);
	
	/* markers */
	UI_view2d_view_orthoSpecial(C, v2d, 1);
	draw_markers_time(C, 0);
	
	/* reset view matrix */
	UI_view2d_view_restore(C);
	
	/* scrollers */
	scrollers= UI_view2d_scrollers_calc(C, v2d, unit, V2D_GRID_CLAMP, V2D_ARG_DUMMY, V2D_ARG_DUMMY);
	UI_view2d_scrollers_draw(C, v2d, scrollers);
	UI_view2d_scrollers_free(scrollers);
}

static void time_main_area_listener(ARegion *ar, wmNotifier *wmn)
{
	/* context changes */
	switch(wmn->category) {
		
		case NC_SCENE:
			/* any scene change for now */
			ED_region_tag_redraw(ar);
			break;
	}
}

/* ************************ header time area region *********************** */

/* add handlers, stuff you only do once or on area/region changes */
static void time_header_area_init(wmWindowManager *wm, ARegion *ar)
{
	UI_view2d_region_reinit(&ar->v2d, V2D_COMMONVIEW_HEADER, ar->winx, ar->winy);
}

static void time_header_area_draw(const bContext *C, ARegion *ar)
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
	
	time_header_buttons(C, ar);
	
	/* restore view matrix? */
	UI_view2d_view_restore(C);
}

static void time_header_area_listener(ARegion *ar, wmNotifier *wmn)
{
	/* context changes */
	switch(wmn->category) {
		case NC_SCENE:
			switch (wmn->data) {
				case ND_FRAME:
				case ND_KEYINGSET:
					ED_region_tag_redraw(ar);
				break;
			}
	}
}

/* ******************** default callbacks for time space ***************** */

static SpaceLink *time_new(const bContext *C)
{
	Scene *scene= CTX_data_scene(C);
	ARegion *ar;
	SpaceTime *stime;

	stime= MEM_callocN(sizeof(SpaceTime), "inittime");

	stime->spacetype= SPACE_TIME;
	stime->redraws= TIME_ALL_3D_WIN|TIME_ALL_ANIM_WIN;
	stime->flag |= TIME_DRAWFRAMES;

	/* header */
	ar= MEM_callocN(sizeof(ARegion), "header for time");
	
	BLI_addtail(&stime->regionbase, ar);
	ar->regiontype= RGN_TYPE_HEADER;
	ar->alignment= RGN_ALIGN_BOTTOM;
	
	/* main area */
	ar= MEM_callocN(sizeof(ARegion), "main area for time");
	
	BLI_addtail(&stime->regionbase, ar);
	ar->regiontype= RGN_TYPE_WINDOW;
	
	ar->v2d.tot.xmin= (float)(SFRA - 4);
	ar->v2d.tot.ymin= 0.0f;
	ar->v2d.tot.xmax= (float)(EFRA + 4);
	ar->v2d.tot.ymax= 50.0f;
	
	ar->v2d.cur= ar->v2d.tot;

	ar->v2d.min[0]= 1.0f;
	ar->v2d.min[1]= 50.0f;

	ar->v2d.max[0]= MAXFRAMEF;
	ar->v2d.max[1]= 50.0; 

	ar->v2d.minzoom= 0.1f;
	ar->v2d.maxzoom= 10.0;

	ar->v2d.scroll |= (V2D_SCROLL_BOTTOM|V2D_SCROLL_SCALE_HORIZONTAL);
	ar->v2d.align |= V2D_ALIGN_NO_NEG_Y;
	ar->v2d.keepofs |= V2D_LOCKOFS_Y;
	ar->v2d.keepzoom |= V2D_LOCKZOOM_Y;


	return (SpaceLink*)stime;
}

/* not spacelink itself */
static void time_free(SpaceLink *sl)
{
}


/* spacetype; init callback in ED_area_initialize() */
/* init is called to (re)initialize an existing editor (file read, screen changes) */
/* validate spacedata, add own area level handlers */
static void time_init(wmWindowManager *wm, ScrArea *sa)
{
	
}

static SpaceLink *time_duplicate(SpaceLink *sl)
{
	SpaceTime *stime= (SpaceTime *)sl;
	SpaceTime *stimen= MEM_dupallocN(stime);
	
	return (SpaceLink *)stimen;
}

/* only called once, from space_api/spacetypes.c */
/* it defines all callbacks to maintain spaces */
void ED_spacetype_time(void)
{
	SpaceType *st= MEM_callocN(sizeof(SpaceType), "spacetype time");
	ARegionType *art;
	
	st->spaceid= SPACE_TIME;
	strncpy(st->name, "Timeline", BKE_ST_MAXNAME);
	
	st->new= time_new;
	st->free= time_free;
	st->init= time_init;
	st->duplicate= time_duplicate;
	st->operatortypes= time_operatortypes;
	st->keymap= NULL;
	
	/* regions: main window */
	art= MEM_callocN(sizeof(ARegionType), "spacetype time region");
	art->regionid = RGN_TYPE_WINDOW;
	art->keymapflag= ED_KEYMAP_VIEW2D|ED_KEYMAP_MARKERS|ED_KEYMAP_ANIMATION|ED_KEYMAP_FRAMES;
	
	art->init= time_main_area_init;
	art->draw= time_main_area_draw;
	art->listener= time_main_area_listener;
	art->keymap= time_keymap;
	BLI_addhead(&st->regiontypes, art);
	
	/* regions: header */
	art= MEM_callocN(sizeof(ARegionType), "spacetype time region");
	art->regionid = RGN_TYPE_HEADER;
	art->minsizey= HEADERY;
	art->keymapflag= ED_KEYMAP_UI|ED_KEYMAP_VIEW2D;
	
	art->init= time_header_area_init;
	art->draw= time_header_area_draw;
	art->listener= time_header_area_listener;
	BLI_addhead(&st->regiontypes, art);
		
	BKE_spacetype_register(st);
}


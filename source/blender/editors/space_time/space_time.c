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

#include "BKE_global.h"
#include "BKE_screen.h"

#include "ED_area.h"
#include "ED_screen.h"

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
	Scene *scene= C->scene;
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
	
	/* draw darkened area outside of active timeline 
	 * frame range used is preview range or scene range */
	UI_ThemeColorShade(TH_BACK, -25);

	if (PSFRA < PEFRA) {
		glRectf(v2d->cur.xmin, v2d->cur.ymin, PSFRA, v2d->cur.ymax);
		glRectf(PEFRA, v2d->cur.ymin, v2d->cur.xmax, v2d->cur.ymax);
	}
	else {
		glRectf(v2d->cur.xmin, v2d->cur.ymin, v2d->cur.xmax, v2d->cur.ymax);
	}

	UI_ThemeColorShade(TH_BACK, -60);
	/* thin lines where the actual frames are */
	fdrawline(PSFRA, v2d->cur.ymin, PSFRA, v2d->cur.ymax);
	fdrawline(PEFRA, v2d->cur.ymin, PEFRA, v2d->cur.ymax);
}

static void time_main_area_init(const bContext *C, ARegion *ar)
{
	/* add handlers, stuff you only do once or on area/region changes */
}

static void time_main_area_refresh(const bContext *C, ARegion *ar)
{
	/* refresh to match contextual changes */
}

static void time_main_area_draw(const bContext *C, ARegion *ar)
{
	/* draw entirely, windowsize changes should be handled here */
	SpaceTime *stime= C->area->spacedata.first;
	View2D *v2d= &ar->v2d;
	View2DGrid *grid;
	View2DScrollers *scrollers;
	float col[3];
	int unit, winx, winy;
	
	// XXX this should become stored in regions too...
	winx= ar->winrct.xmax - ar->winrct.xmin + 1;
	winy= ar->winrct.ymax - ar->winrct.ymin + 1;
	
	UI_view2d_size_update(v2d, winx, winy);

	/* clear and setup matrix */
	UI_GetThemeColor3fv(TH_BACK, col);
	glClearColor(col[0], col[1], col[2], 0.0);
	glClear(GL_COLOR_BUFFER_BIT);
	
	UI_view2d_view_ortho(C, v2d);

	/* start and end frame */
	time_draw_sfra_efra(C, stime, ar);

	/* grid */
	unit= (stime->flag & TIME_DRAWFRAMES)? V2D_UNIT_FRAMES: V2D_UNIT_SECONDS;
	grid= UI_view2d_grid_calc(C, v2d, unit, V2D_GRID_CLAMP, winx, winy);
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
	/* draw entirely, windowsize changes should be handled here */
}

/* ************************ header time area region *********************** */

static void time_header_area_draw(const bContext *C, ARegion *ar)
{
	float col[3];

	/* clear */
	UI_GetThemeColor3fv(TH_HEADER, col);
	glClearColor(col[0], col[1], col[2], 0.0);
	glClear(GL_COLOR_BUFFER_BIT);

	uiTestRegion(C);
}

static void time_header_area_free(ARegion *ar)
{
}

/* ******************** default callbacks for time space ***************** */

static SpaceLink *time_new(void)
{
	SpaceTime *stime;

	stime= MEM_callocN(sizeof(SpaceTime), "inittime");

	stime->spacetype= SPACE_TIME;
	stime->blockscale= 0.7;
	stime->redraws= TIME_ALL_3D_WIN|TIME_ALL_ANIM_WIN;

	// XXX move to region!
	stime->v2d.tot.xmin= -4.0;
	stime->v2d.tot.ymin=  0.0;
	stime->v2d.tot.xmax= (float)EFRA + 4.0;
	//stime->v2d.tot.ymax= (float)stime->winy;

	stime->v2d.cur= stime->v2d.tot;

	stime->v2d.min[0]= 1.0;
	//stime->v2d.min[1]= (float)stime->winy;

	stime->v2d.max[0]= 32000.0;
	//stime->v2d.max[1]= (float)stime->winy;

	stime->v2d.minzoom= 0.1f;
	stime->v2d.maxzoom= 10.0;

	stime->v2d.scroll= 0;
	stime->v2d.keepaspect= 0;
	stime->v2d.keepzoom= 0;
	stime->v2d.keeptot= 0;

	stime->flag |= TIME_DRAWFRAMES;

	return (SpaceLink*)stime;
}

/* not spacelink itself */
static void time_free(SpaceLink *sl)
{
}


/* spacetype; init callback in ED_area_initialize() */
/* init is called to (re)initialize an existing editor (file read, screen changes) */
static void time_init(wmWindowManager *wm, ScrArea *sa)
{
	ARegion *ar;
	
	/* add types to regions, check handlers */
	for(ar= sa->regionbase.first; ar; ar= ar->next) {
		
		ar->type= ED_regiontype_from_id(sa->type, ar->regiontype);
		
		if(ar->handlers.first==NULL) {
			ListBase *keymap;
			
			/* XXX fixme, should be smarter */
			
			UI_add_region_handlers(&ar->handlers);
			
			keymap= WM_keymap_listbase(wm, "View2D", 0, 0);
			WM_event_add_keymap_handler(&ar->handlers, keymap);
			
			/* own keymap */
			keymap= WM_keymap_listbase(wm, "TimeLine", sa->spacetype, 0);
			WM_event_add_keymap_handler(&ar->handlers, keymap);
		}
	}
}

/* spacetype; context changed */
static void time_refresh(bContext *C, ScrArea *sa)
{
	
}

static SpaceLink *time_duplicate(SpaceLink *sl)
{
	SpaceTime *stime= (SpaceTime *)sl;
	SpaceTime *stimen= MEM_dupallocN(stime);
	
	return (SpaceLink *)stimen;
}

/* only called once, from screen/spacetypes.c */
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
	st->refresh= time_refresh;
	st->duplicate= time_duplicate;
	st->operatortypes= time_operatortypes;
	st->keymap= time_keymap;
	
	/* regions: main window */
	art= MEM_callocN(sizeof(ARegionType), "spacetype time region");
	art->regionid = RGN_TYPE_WINDOW;

	art->init= time_main_area_init;
	art->refresh= time_main_area_refresh;
	art->draw= time_main_area_draw;
	art->listener= time_main_area_listener;
	BLI_addhead(&st->regiontypes, art);
	
	/* regions: header */
	art= MEM_callocN(sizeof(ARegionType), "spacetype time region");
	art->regionid = RGN_TYPE_HEADER;
	
	art->draw= time_header_area_draw;
	art->free= time_header_area_free;
	BLI_addhead(&st->regiontypes, art);
	
	
	BKE_spacetype_register(st);
}


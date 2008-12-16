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
 * Contributor(s): Blender Foundation, Joshua Leung
 *
 *
 * Generic 2d view with should allow drawing grids,
 * panning, zooming, scrolling, .. 
 * ***** END GPL LICENSE BLOCK *****
 */

#ifndef UI_VIEW2D_H
#define UI_VIEW2D_H

/* ------------------------------------------ */
/* Settings and Defines: 					*/

/* ---- General Defines ---- */

/* generic value to use when coordinate lies out of view when converting */
#define V2D_IS_CLIPPED	12000

/* common View2D view types */
enum {
		/* custom view type (region has defined all necessary flags already) */
	V2D_COMMONVIEW_CUSTOM = 0,
		/* view canvas ('standard' view, view limits/restrictions still need to be set first!) */
	V2D_COMMONVIEW_VIEWCANVAS,
		/* listview (i.e. Outliner) */
	V2D_COMMONVIEW_LIST,
		/* headers (this is basically the same as listview, but no y-panning) */
	V2D_COMMONVIEW_HEADER,
		/* timegrid (this sets the settings for x/horizontal, but y/vertical settings still need to be set first!) */
	V2D_COMMONVIEW_TIMELINE,
} eView2D_CommonViewTypes;

/* ---- Defines for Scroller/Grid Arguments ----- */

/* 'dummy' argument to pass when argument is irrelevant */
#define V2D_ARG_DUMMY		-1

/* Grid units */
enum {
	/* for drawing time */
	V2D_UNIT_SECONDS = 0,
	V2D_UNIT_FRAMES,
	
	/* for drawing values */
	V2D_UNIT_VALUES,
	V2D_UNIT_DEGREES,
	V2D_UNIT_TIME,
	V2D_UNIT_SECONDSSEQ,
} eView2D_Units;

/* clamping of grid values to whole numbers */
enum {
	V2D_GRID_NOCLAMP = 0,
	V2D_GRID_CLAMP,
} eView2D_Clamp;

/* flags for grid-lines to draw */
enum {
	V2D_HORIZONTAL_LINES		= (1<<0),
	V2D_VERTICAL_LINES			= (1<<1),
	V2D_HORIZONTAL_AXIS			= (1<<2),
	V2D_VERTICAL_AXIS			= (1<<3),
	V2D_HORIZONTAL_FINELINES	= (1<<4),
	
	V2D_GRIDLINES_MAJOR			= (V2D_VERTICAL_LINES|V2D_VERTICAL_AXIS|V2D_HORIZONTAL_LINES|V2D_HORIZONTAL_AXIS),
	V2D_GRIDLINES_ALL			= (V2D_GRIDLINES_MAJOR|V2D_HORIZONTAL_FINELINES),
} eView2D_Gridlines;

/* ------ Defines for Scrollers ----- */

/* scroller thickness */
#define V2D_SCROLL_HEIGHT	16
#define V2D_SCROLL_WIDTH	16

/* half the size (in pixels) of scroller 'handles' */
#define V2D_SCROLLER_HANDLE_SIZE	5

/* ------ Define for UI_view2d_sync ----- */

/* means copy it from the other v2d */
#define V2D_LOCK_COPY	1


/* ------------------------------------------ */
/* Macros:								*/

/* test if mouse in a scrollbar (assume that scroller availability has been tested) */
#define IN_2D_VERT_SCROLL(v2d, co) (BLI_in_rcti(&v2d->vert, co[0], co[1]))
#define IN_2D_HORIZ_SCROLL(v2d, co) (BLI_in_rcti(&v2d->hor, co[0], co[1]))

/* ------------------------------------------ */
/* Type definitions: 						*/

struct View2D;
struct View2DGrid;
struct View2DScrollers;

struct wmWindowManager;
struct bContext;

typedef struct View2DGrid View2DGrid;
typedef struct View2DScrollers View2DScrollers;

/* ----------------------------------------- */
/* Prototypes:						    */

/* refresh and validation (of view rects) */
void UI_view2d_region_reinit(struct View2D *v2d, short type, int winx, int winy);

void UI_view2d_curRect_validate(struct View2D *v2d);
void UI_view2d_curRect_reset(struct View2D *v2d);

void UI_view2d_totRect_set(struct View2D *v2d, int width, int height);

/* view matrix operations */
void UI_view2d_view_ortho(const struct bContext *C, struct View2D *v2d);
void UI_view2d_view_orthoSpecial(const struct bContext *C, struct View2D *v2d, short xaxis);
void UI_view2d_view_restore(const struct bContext *C);

/* grid drawing */
View2DGrid *UI_view2d_grid_calc(const struct bContext *C, struct View2D *v2d, short xunits, short xclamp, short yunits, short yclamp, int winx, int winy);
void UI_view2d_grid_draw(const struct bContext *C, struct View2D *v2d, View2DGrid *grid, int flag);
void UI_view2d_grid_free(View2DGrid *grid);

/* scrollbar drawing */
View2DScrollers *UI_view2d_scrollers_calc(const struct bContext *C, struct View2D *v2d, short xunits, short xclamp, short yunits, short yclamp);
void UI_view2d_scrollers_draw(const struct bContext *C, struct View2D *v2d, View2DScrollers *scrollers);
void UI_view2d_scrollers_free(View2DScrollers *scrollers);

/* coordinate conversion */
void UI_view2d_region_to_view(struct View2D *v2d, int x, int y, float *viewx, float *viewy);
void UI_view2d_view_to_region(struct View2D *v2d, float x, float y, short *regionx, short *regiony);
void UI_view2d_to_region_no_clip(struct View2D *v2d, float x, float y, short *regionx, short *region_y);

/* utilities */
struct View2D *UI_view2d_fromcontext(const struct bContext *C);
struct View2D *UI_view2d_fromcontext_rwin(const struct bContext *C);
void UI_view2d_getscale(struct View2D *v2d, float *x, float *y);
void UI_view2d_sync(struct View2D *v2d, struct View2D *v2dfrom, int flag);

/* operators */
void ui_view2d_operatortypes(void);
void UI_view2d_keymap(struct wmWindowManager *wm);

#endif /* UI_VIEW2D_H */


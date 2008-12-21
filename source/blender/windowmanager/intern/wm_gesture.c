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

#define _USE_MATH_DEFINES
#include <math.h>

#include "DNA_screen_types.h"
#include "DNA_vec_types.h"
#include "DNA_windowmanager_types.h"

#include "MEM_guardedalloc.h"

#include "BLI_blenlib.h"

#include "BKE_context.h"
#include "BKE_utildefines.h"

#include "WM_api.h"
#include "WM_types.h"

#include "wm_event_system.h"
#include "wm_subwindow.h"

#include "BIF_gl.h"
#include "BIF_glutil.h"


/* context checked on having screen, window and area */
wmGesture *WM_gesture_new(bContext *C, wmEvent *event, int type)
{
	wmGesture *gesture= MEM_callocN(sizeof(wmGesture), "new gesture");
	wmWindow *window= CTX_wm_window(C);
	bScreen *screen= CTX_wm_screen(C);
	int sx, sy;
	
	BLI_addtail(&window->gesture, gesture);
	
	gesture->type= type;
	gesture->event_type= event->type;
	gesture->swinid= screen->subwinactive;	/* means only in area-region context! */
	
	wm_subwindow_getorigin(window, gesture->swinid, &sx, &sy);
	
	if( ELEM4(type, WM_GESTURE_RECT, WM_GESTURE_CROSS_RECT, WM_GESTURE_TWEAK, WM_GESTURE_CIRCLE)) {
		rcti *rect= MEM_callocN(sizeof(rcti), "gesture rect new");
		
		gesture->customdata= rect;
		rect->xmin= event->x - sx;
		rect->ymin= event->y - sy;
		if(type==WM_GESTURE_CIRCLE)
			rect->xmax= 25;	// XXX temp
		else {
			rect->xmax= event->x - sx;
			rect->ymax= event->y - sy;
		}
	}
	
	return gesture;
}

void WM_gesture_end(bContext *C, wmGesture *gesture)
{
	BLI_remlink(&CTX_wm_window(C)->gesture, gesture);
	MEM_freeN(gesture->customdata);
	MEM_freeN(gesture);
}

/* for line, lasso, ... */
void wm_gesture_point_add(bContext *C, wmGesture *gesture)
{
	
}

/* tweak and line gestures */
#define TWEAK_THRESHOLD		10
int wm_gesture_evaluate(bContext *C, wmGesture *gesture)
{
	if(gesture->type==WM_GESTURE_TWEAK) {
		rcti *rect= gesture->customdata;
		int dx= rect->xmax - rect->xmin;
		int dy= rect->ymax - rect->ymin;
		if(ABS(dx)+ABS(dy) > TWEAK_THRESHOLD) {
			int theta= (int)floor(4.0f*atan2((float)dy, (float)dx)/M_PI + 0.5);
			int val= EVT_GESTURE_W;
			
			if(theta==0) val= EVT_GESTURE_E;
			else if(theta==1) val= EVT_GESTURE_NE;
			else if(theta==2) val= EVT_GESTURE_N;
			else if(theta==3) val= EVT_GESTURE_NW;
			else if(theta==-1) val= EVT_GESTURE_SE;
			else if(theta==-2) val= EVT_GESTURE_S;
			else if(theta==-3) val= EVT_GESTURE_SW;
			
#if 0
			/* debug */
			if(val==1) printf("tweak north\n");
			if(val==2) printf("tweak north-east\n");
			if(val==3) printf("tweak east\n");
			if(val==4) printf("tweak south-east\n");
			if(val==5) printf("tweak south\n");
			if(val==6) printf("tweak south-west\n");
			if(val==7) printf("tweak west\n");
			if(val==8) printf("tweak north-west\n");
#endif			
			return val;
		}
	}
	return 0;
}


/* ******************* gesture draw ******************* */

static void wm_gesture_draw_rect(wmWindow *win, wmGesture *gt)
{
	rcti *rect= (rcti *)gt->customdata;
	
	glEnable(GL_LINE_STIPPLE);
	glColor3ub(0, 0, 0);
	glLineStipple(1, 0xCCCC);
	sdrawbox(rect->xmin, rect->ymin, rect->xmax, rect->ymax);
	glColor3ub(255, 255, 255);
	glLineStipple(1, 0x3333);
	sdrawbox(rect->xmin, rect->ymin, rect->xmax, rect->ymax);
	glDisable(GL_LINE_STIPPLE);
}

static void wm_gesture_draw_line(wmWindow *win, wmGesture *gt)
{
	rcti *rect= (rcti *)gt->customdata;
	
	glEnable(GL_LINE_STIPPLE);
	glColor3ub(0, 0, 0);
	glLineStipple(1, 0xAAAA);
	sdrawline(rect->xmin, rect->ymin, rect->xmax, rect->ymax);
	glColor3ub(255, 255, 255);
	glLineStipple(1, 0x5555);
	sdrawline(rect->xmin, rect->ymin, rect->xmax, rect->ymax);

	glDisable(GL_LINE_STIPPLE);
	
}

static void wm_gesture_draw_circle(wmWindow *win, wmGesture *gt)
{
	rcti *rect= (rcti *)gt->customdata;

	glTranslatef((float)rect->xmin, (float)rect->ymin, 0.0f);

	glEnable(GL_LINE_STIPPLE);
	glColor3ub(0, 0, 0);
	glLineStipple(1, 0xAAAA);
	glutil_draw_lined_arc(0.0, M_PI*2.0, rect->xmax, 40);
	glColor3ub(255, 255, 255);
	glLineStipple(1, 0x5555);
	glutil_draw_lined_arc(0.0, M_PI*2.0, rect->xmax, 40);
	
	glDisable(GL_LINE_STIPPLE);
	glTranslatef((float)-rect->xmin, (float)-rect->ymin, 0.0f);
	
}


static void wm_gesture_draw_cross(wmWindow *win, wmGesture *gt)
{
	rcti *rect= (rcti *)gt->customdata;
	
	glEnable(GL_LINE_STIPPLE);
	glColor3ub(0, 0, 0);
	glLineStipple(1, 0xCCCC);
	sdrawline(rect->xmin - win->sizex, rect->ymin, rect->xmin + win->sizex, rect->ymin);
	sdrawline(rect->xmin, rect->ymin - win->sizey, rect->xmin, rect->ymin + win->sizey);
	
	glColor3ub(255, 255, 255);
	glLineStipple(1, 0x3333);
	sdrawline(rect->xmin - win->sizex, rect->ymin, rect->xmin + win->sizex, rect->ymin);
	sdrawline(rect->xmin, rect->ymin - win->sizey, rect->xmin, rect->ymin + win->sizey);
	glDisable(GL_LINE_STIPPLE);
}

/* called in wm_event_system.c */
void wm_gesture_draw(wmWindow *win)
{
	wmGesture *gt= (wmGesture *)win->gesture.first;
	
	for(; gt; gt= gt->next) {
		/* all in subwindow space */
		wmSubWindowSet(win, gt->swinid);
		
		if(gt->type==WM_GESTURE_RECT)
			wm_gesture_draw_rect(win, gt);
		else if(gt->type==WM_GESTURE_TWEAK)
			wm_gesture_draw_line(win, gt);
		else if(gt->type==WM_GESTURE_CIRCLE)
			wm_gesture_draw_circle(win, gt);
		else if(gt->type==WM_GESTURE_CROSS_RECT) {
			if(gt->mode==1)
				wm_gesture_draw_rect(win, gt);
			else
				wm_gesture_draw_cross(win, gt);
		}
	}
}



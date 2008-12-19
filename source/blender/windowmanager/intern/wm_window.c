/**
 * $Id: wm_window.c
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
 * The Original Code is Copyright (C) 2007 Blender Foundation but based 
 * on ghostwinlay.c (C) 2001-2002 by NaN Holding BV
 * All rights reserved.
 *
 * Contributor(s): Blender Foundation, 2008
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#include <stdlib.h>
#include <stdio.h>

#include "DNA_listBase.h"	
#include "DNA_screen_types.h"
#include "DNA_windowmanager_types.h"

#include "MEM_guardedalloc.h"

#include "GHOST_C-api.h"

#include "BLI_blenlib.h"

#include "BKE_blender.h"
#include "BKE_context.h"
#include "BKE_global.h"
#include "BKE_utildefines.h"

#include "BIF_gl.h"

#include "WM_api.h"
#include "WM_types.h"
#include "wm.h"
#include "wm_window.h"
#include "wm_subwindow.h"
#include "wm_event_system.h"

#include "ED_screen.h"

#include "GPU_draw.h"

/* the global to talk to ghost */
GHOST_SystemHandle g_system= NULL;

/* set by commandline */
static int prefsizx= 0, prefsizy= 0, prefstax= 0, prefstay= 0;


/* ******** win open & close ************ */


static void wm_get_screensize(int *width_r, int *height_r) 
{
	unsigned int uiwidth;
	unsigned int uiheight;
	
	GHOST_GetMainDisplayDimensions(g_system, &uiwidth, &uiheight);
	*width_r= uiwidth;
	*height_r= uiheight;
}

static void wm_ghostwindow_destroy(wmWindow *win) 
{
	if(win->ghostwin) {
		GHOST_DisposeWindow(g_system, win->ghostwin);
		win->ghostwin= NULL;
	}
}

/* including window itself, C can be NULL. 
   ED_screen_exit should have been called */
void wm_window_free(bContext *C, wmWindow *win)
{
	/* update context */
	if(C) {
		wmWindowManager *wm= CTX_wm_manager(C);

		if(wm->windrawable==win)
			wm->windrawable= NULL;
		if(wm->winactive==win)
			wm->winactive= NULL;
		if(CTX_wm_window(C)==win)
			CTX_wm_window_set(C, NULL);
	}	
	
	if(win->eventstate) MEM_freeN(win->eventstate);

	wm_event_free_all(win);
	wm_subwindows_free(win);
	
	wm_ghostwindow_destroy(win);
	
	MEM_freeN(win);
}

static int find_free_winid(wmWindowManager *wm)
{
	wmWindow *win;
	int id= 0;
	
	for(win= wm->windows.first; win; win= win->next)
		if(id <= win->winid)
			id= win->winid+1;
	
	return id;
}

/* dont change context itself */
wmWindow *wm_window_new(bContext *C)
{
	wmWindowManager *wm= CTX_wm_manager(C);
	wmWindow *win= MEM_callocN(sizeof(wmWindow), "window");
	
	BLI_addtail(&wm->windows, win);
	win->winid= find_free_winid(wm);

	return win;
}


/* part of wm_window.c api */
wmWindow *wm_window_copy(bContext *C, wmWindow *winorig)
{
	wmWindow *win= wm_window_new(C);
	
	win->posx= winorig->posx+10;
	win->posy= winorig->posy;
	win->sizex= winorig->sizex;
	win->sizey= winorig->sizey;
	
	win->screen= ED_screen_duplicate(win, winorig->screen);
	win->screen->do_refresh= 1;
	win->screen->do_draw= 1;
	
	return win;
}

/* this is event from ghost */
static void wm_window_close(bContext *C, wmWindow *win)
{
	wmWindowManager *wm= CTX_wm_manager(C);
	BLI_remlink(&wm->windows, win);
	
	WM_event_remove_handlers(C, &win->handlers);
	ED_screen_exit(C, win, win->screen);
	wm_window_free(C, win);
	
	if(wm->windows.first==NULL)
		WM_exit(C);
}

/* belongs to below */
static void wm_window_add_ghostwindow(wmWindowManager *wm, char *title, wmWindow *win)
{
	GHOST_WindowHandle ghostwin;
	GHOST_TWindowState inital_state;
	int scr_w, scr_h, posy;
	
	wm_get_screensize(&scr_w, &scr_h);
	posy= (scr_h - win->posy - win->sizey);
	
	//		inital_state = GHOST_kWindowStateFullScreen;
	//		inital_state = GHOST_kWindowStateMaximized;
	inital_state = GHOST_kWindowStateNormal;
	
#ifdef __APPLE__
	{
		extern int macPrefState; /* creator.c */
		inital_state += macPrefState;
	}
#endif
	
	ghostwin= GHOST_CreateWindow(g_system, title, 
								 win->posx, posy, win->sizex, win->sizey, 
								 inital_state, 
								 GHOST_kDrawingContextTypeOpenGL,
								 0 /* no stereo */);
	
	if (ghostwin) {
		ListBase *keymap;
		
		win->ghostwin= ghostwin;
		GHOST_SetWindowUserData(ghostwin, win);	/* pointer back */
		
		if(win->eventstate==NULL)
			win->eventstate= MEM_callocN(sizeof(wmEvent), "window event state");
		
		/* add keymap handlers (1 handler for all keys in map!) */
		keymap= WM_keymap_listbase(wm, "Window", 0, 0);
		WM_event_add_keymap_handler(&win->handlers, keymap);

		keymap= WM_keymap_listbase(wm, "Screen", 0, 0);
		WM_event_add_keymap_handler(&win->handlers, keymap);
		
		/* until screens get drawn, make it nice grey */
		glClearColor(.55, .55, .55, 0.0);
		glClear(GL_COLOR_BUFFER_BIT);
		wm_window_swap_buffers(win);
		
		/* standard state vars for window */
		glEnable(GL_SCISSOR_TEST);
		
		GPU_state_init();
	}
}

/* for wmWindows without ghostwin, open these and clear */
/* window size is read from window, if 0 it uses prefsize */
void wm_window_add_ghostwindows(wmWindowManager *wm)
{
	wmWindow *win;
	
	/* no commandline prefsize? then we set this */
	if (!prefsizx) {
		wm_get_screensize(&prefsizx, &prefsizy);
		
#ifdef __APPLE__
		{
			extern void wm_set_apple_prefsize(int, int);	/* wm_apple.c */
			
			wm_set_apple_prefsize(prefsizx, prefsizy);
		}
#else
		prefstax= 0;
		prefstay= 0;
		
#endif
	}
	
	for(win= wm->windows.first; win; win= win->next) {
		if(win->ghostwin==NULL) {
			if(win->sizex==0) {
				win->posx= prefstax;
				win->posy= prefstay;
				win->sizex= prefsizx;
				win->sizey= prefsizy;
				win->windowstate= 0;
			}
			wm_window_add_ghostwindow(wm, "Blender", win);
		}
	}
}

/* new window, no screen yet, but we open ghostwindow for it */
/* also gets the window level handlers */
/* area-rip calls this */
wmWindow *WM_window_open(bContext *C, rcti *rect)
{
	wmWindowManager *wm= CTX_wm_manager(C);
	wmWindow *win= wm_window_new(C);
	
	win->posx= rect->xmin;
	win->posy= rect->ymin;
	win->sizex= rect->xmax - rect->xmin;
	win->sizey= rect->ymax - rect->ymin;
	
	wm_window_add_ghostwindow(wm, "Blender", win);
	
	return win;
}


/* ****************** Operators ****************** */

/* operator callback */
int wm_window_duplicate_op(bContext *C, wmOperator *op)
{
	wm_window_copy(C, CTX_wm_window(C));
	wm_check(C);
	
	return OPERATOR_FINISHED;
}


/* fullscreen operator callback */
int wm_window_fullscreen_toggle_op(bContext *C, wmOperator *op)
{
	wmWindow *window= CTX_wm_window(C);
	GHOST_TWindowState state = GHOST_GetWindowState(window->ghostwin);
	if(state!=GHOST_kWindowStateFullScreen)
		GHOST_SetWindowState(window->ghostwin, GHOST_kWindowStateFullScreen);
	else
		GHOST_SetWindowState(window->ghostwin, GHOST_kWindowStateNormal);

	return OPERATOR_FINISHED;
	
}

	
/* exit blender */
int wm_exit_blender_op(bContext *C, wmOperator *op)
{
	wmWindowManager *wm= CTX_wm_manager(C);
	wmWindow *win= wm->windows.first;

	while(win) {
		wm_window_close(C, win);
		win= win->next;
	}

	return OPERATOR_FINISHED;
}


/* ************ events *************** */

static int query_qual(char qual) 
{
	GHOST_TModifierKeyMask left, right;
	int val= 0;
	
	if (qual=='s') {
		left= GHOST_kModifierKeyLeftShift;
		right= GHOST_kModifierKeyRightShift;
	} else if (qual=='c') {
		left= GHOST_kModifierKeyLeftControl;
		right= GHOST_kModifierKeyRightControl;
	} else if (qual=='C') {
		left= right= GHOST_kModifierKeyCommand;
	} else {
		left= GHOST_kModifierKeyLeftAlt;
		right= GHOST_kModifierKeyRightAlt;
	}
	
	GHOST_GetModifierKeyState(g_system, left, &val);
	if (!val)
		GHOST_GetModifierKeyState(g_system, right, &val);
	
	return val;
}

void wm_window_make_drawable(bContext *C, wmWindow *win) 
{
	wmWindowManager *wm= CTX_wm_manager(C);

	if (win != wm->windrawable && win->ghostwin) {
//		win->lmbut= 0;	/* keeps hanging when mousepressed while other window opened */
		
		wm->windrawable= win;
		if(G.f & G_DEBUG) printf("set drawable %d\n", win->winid);
		GHOST_ActivateWindowDrawingContext(win->ghostwin);
	}
}

/* called by ghost, here we handle events for windows themselves or send to event system */
static int ghost_event_proc(GHOST_EventHandle evt, GHOST_TUserDataPtr private) 
{
	bContext *C= private;
	GHOST_TEventType type= GHOST_GetEventType(evt);
	
	if (type == GHOST_kEventQuit) {
		WM_exit(C);
	} else {
		GHOST_WindowHandle ghostwin= GHOST_GetEventWindow(evt);
		GHOST_TEventDataPtr data= GHOST_GetEventData(evt);
		wmWindow *win;
		
		if (!ghostwin) {
			// XXX - should be checked, why are we getting an event here, and
			//	what is it?
			
			return 1;
		} else if (!GHOST_ValidWindow(g_system, ghostwin)) {
			// XXX - should be checked, why are we getting an event here, and
			//	what is it?
			
			return 1;
		} else {
			win= GHOST_GetWindowUserData(ghostwin);
		}
		
		switch(type) {
			case GHOST_kEventWindowDeactivate:
				win->active= 0; /* XXX */
				break;
			case GHOST_kEventWindowActivate: 
			{
				GHOST_TEventKeyData kdata;
				int cx, cy, wx, wy;
				
				CTX_wm_manager(C)->winactive= win; /* no context change! c->wm->windrawable is drawable, or for area queues */
				
				win->active= 1;
//				window_handle(win, INPUTCHANGE, win->active);
				
				/* bad ghost support for modifier keys... so on activate we set the modifiers again */
				kdata.ascii= 0;
				if (win->eventstate->shift && !query_qual('s')) {
					kdata.key= GHOST_kKeyLeftShift;
					wm_event_add_ghostevent(win, GHOST_kEventKeyUp, &kdata);
				}
				if (win->eventstate->ctrl && !query_qual('c')) {
					kdata.key= GHOST_kKeyLeftControl;
					wm_event_add_ghostevent(win, GHOST_kEventKeyUp, &kdata);
				}
				if (win->eventstate->alt && !query_qual('a')) {
					kdata.key= GHOST_kKeyLeftAlt;
					wm_event_add_ghostevent(win, GHOST_kEventKeyUp, &kdata);
				}
				if (win->eventstate->oskey && !query_qual('C')) {
					kdata.key= GHOST_kKeyCommand;
					wm_event_add_ghostevent(win, GHOST_kEventKeyUp, &kdata);
				}
				
				/* entering window, update mouse pos. but no event */
				GHOST_GetCursorPosition(g_system, &wx, &wy);
				
				GHOST_ScreenToClient(win->ghostwin, wx, wy, &cx, &cy);
				win->eventstate->x= cx;
				win->eventstate->y= (win->sizey-1) - cy;
				
				wm_window_make_drawable(C, win);
				break;
			}
			case GHOST_kEventWindowClose: {
				wm_window_close(C, win);
				break;
			}
			case GHOST_kEventWindowUpdate: {
				if(G.f & G_DEBUG) printf("ghost redraw\n");
				
				wm_window_make_drawable(C, win);
				WM_event_add_notifier(C, WM_NOTE_WINDOW_REDRAW, 0, NULL);

				break;
			}
			case GHOST_kEventWindowSize:
			case GHOST_kEventWindowMove: {
				GHOST_RectangleHandle client_rect;
				int l, t, r, b, scr_w, scr_h;
				
				client_rect= GHOST_GetClientBounds(win->ghostwin);
				GHOST_GetRectangle(client_rect, &l, &t, &r, &b);
				
				GHOST_DisposeRectangle(client_rect);
				
				wm_get_screensize(&scr_w, &scr_h);
				win->sizex= r-l;
				win->sizey= b-t;
				win->posx= l;
				win->posy= scr_h - t - win->sizey;

				/* debug prints */
				if(0) {
					GHOST_TWindowState state;
					state = GHOST_GetWindowState(win->ghostwin);

					if(state==GHOST_kWindowStateNormal) {
						if(G.f & G_DEBUG) printf("window state: normal\n");
					}
					else if(state==GHOST_kWindowStateMinimized) {
						if(G.f & G_DEBUG) printf("window state: minimized\n");
					}
					else if(state==GHOST_kWindowStateMaximized) {
						if(G.f & G_DEBUG) printf("window state: maximized\n");
					}
					else if(state==GHOST_kWindowStateFullScreen) {
						if(G.f & G_DEBUG) printf("window state: fullscreen\n");
					}
					
					if(type!=GHOST_kEventWindowSize) {
						if(G.f & G_DEBUG) printf("win move event pos %d %d size %d %d\n", win->posx, win->posy, win->sizex, win->sizey);
					}
					
				}
				
				wm_window_make_drawable(C, win);
				WM_event_add_notifier(C, WM_NOTE_SCREEN_CHANGED, 0, NULL);
				
				break;
			}
			default:
				wm_event_add_ghostevent(win, type, data);
				break;
		}

	}
	return 1;
}

void wm_window_process_events(int wait_for_event) 
{
	GHOST_ProcessEvents(g_system, wait_for_event);
	GHOST_DispatchEvents(g_system);
}

/* **************** init ********************** */

void wm_ghost_init(bContext *C)
{
	if (!g_system) {
		GHOST_EventConsumerHandle consumer= GHOST_CreateEventConsumer(ghost_event_proc, C);
		
		g_system= GHOST_CreateSystem();
		GHOST_AddEventConsumer(g_system, consumer);
	}	
}

/* **************** timer ********************** */

static void window_event_timer_proc(GHOST_TimerTaskHandle timer, GHOST_TUns64 time)
{
	wmWindow *window;

	window= GHOST_GetTimerTaskUserData(timer);

	wm_event_add_ghostevent(window, GHOST_kEventTimer, (wmTimerHandle*)timer);
}

wmTimerHandle *WM_event_add_window_timer(wmWindow *win, int delay_ms, int interval_ms)
{
	return (wmTimerHandle*)GHOST_InstallTimer(g_system, delay_ms, interval_ms,
		window_event_timer_proc, win);
}

void WM_event_remove_window_timer(wmWindow *wm, wmTimerHandle *handle)
{
	GHOST_RemoveTimer(g_system, (GHOST_TimerTaskHandle)handle);
}

/* ************************************ */

void wm_window_set_title(wmWindow *win, char *title) 
{
	GHOST_SetTitle(win->ghostwin, title);
}

void wm_window_get_position(wmWindow *win, int *posx_r, int *posy_r) 
{
	*posx_r= win->posx;
	*posy_r= win->posy;
}

void wm_window_get_size(wmWindow *win, int *width_r, int *height_r) 
{
	*width_r= win->sizex;
	*height_r= win->sizey;
}

void wm_window_set_size(wmWindow *win, int width, int height) 
{
	GHOST_SetClientSize(win->ghostwin, width, height);
}

void wm_window_lower(wmWindow *win) 
{
	GHOST_SetWindowOrder(win->ghostwin, GHOST_kWindowOrderBottom);
}

void wm_window_raise(wmWindow *win) 
{
	GHOST_SetWindowOrder(win->ghostwin, GHOST_kWindowOrderTop);
#ifdef _WIN32
//	markdirty_all(); /* to avoid redraw errors in fullscreen mode (aphex) */
#endif
}

void wm_window_swap_buffers(wmWindow *win)
{
	GHOST_SwapWindowBuffers(win->ghostwin);
}

/* ******************* exported api ***************** */


/* called whem no ghost system was initialized */
void WM_setprefsize(int stax, int stay, int sizx, int sizy)
{
	prefstax= stax;
	prefstay= stay;
	prefsizx= sizx;
	prefsizy= sizy;
}


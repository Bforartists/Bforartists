/**
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
 * Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
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
#include <stdio.h>

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

#ifdef WIN32
#include "BLI_winstuff.h"
#endif

#include "MEM_guardedalloc.h"

#include "DNA_listBase.h"	
#include "DNA_userdef_types.h"	/* U.flag & TWOBUTTONMOUSE */

#include "BLI_blenlib.h"

#include "GHOST_C-api.h"

#include "BKE_utildefines.h"
#include "BKE_global.h"

#include "BIF_gl.h"
#include "BIF_graphics.h"
#include "BIF_mywindow.h"
#include "BIF_screen.h"
#include "BIF_usiblender.h"
#include "BIF_cursors.h"

#include "mydevice.h"
#include "blendef.h"

#include "winlay.h"

#ifdef __APPLE__
#include <OpenGL/OpenGL.h>
#include <Carbon/Carbon.h>

/*declarations*/
int checkAppleVideoCard();
#endif
///

struct _Window {
	GHOST_WindowHandle	ghostwin;
	
		/* Handler and private data for handler */
	WindowHandlerFP		handler;
	void				*user_data;
	
		/* Window state */
	int		size[2], position[2];
	int		active, visible;
	
		/* Last known mouse/button/qualifier state */
	int		lmouse[2];
	int		lqual;		/* (LR_SHFTKEY, LR_CTRLKEY, LR_ALTKEY, LR_COMMANDKEY) */
	int		lmbut;		/* (L_MOUSE, M_MOUSE, R_MOUSE) */
	int		commandqual;

		/* Tracks the faked mouse button, if non-zero it is
		 * the event number of the last faked button.
		 */
	int		faked_mbut;

	GHOST_TimerTaskHandle	timer;
	int						timer_event;
};

///

#ifdef __APPLE__

/* to avoid killing small end comps, we want to allow
   blender to start maximised if all the followings are true :
		- Renderer is OpenGL capable
		- Hardware acceleration
		- VRAM > 16 Mo
		
   we will bail out if VRAM is less than 8Mo
		*/
		
static int macPrefState = 0;
		
int checkAppleVideoCard() {
	long theErr;
	unsigned long display_mask;
	CGLRendererInfoObj rend;
	long nrend;
	int j;
	long value;
	long maxvram = 0;   /* we get always more than 1 renderer, check one, at least, has 8 Mo */
	
	display_mask = CGDisplayIDToOpenGLDisplayMask (CGMainDisplayID() );	
	
	theErr = CGLQueryRendererInfo( display_mask, &rend, &nrend);
	if (theErr == 0) {
		theErr = CGLDescribeRenderer (rend, 0, kCGLRPRendererCount, &nrend);
		if (theErr == 0) {
			for (j = 0; j < nrend; j++) {
				theErr = CGLDescribeRenderer (rend, j, kCGLRPVideoMemory, &value); 
				if (value > maxvram)
					maxvram = value;
				if ((theErr == 0) && (value >= 20000000)) {
					theErr = CGLDescribeRenderer (rend, j, kCGLRPAccelerated, &value); 
					if ((theErr == 0) && (value != 0)) {
						theErr = CGLDescribeRenderer (rend, j, kCGLRPCompliant, &value); 
						if ((theErr == 0) && (value != 0)) {
							/*fprintf(stderr,"make it big\n");*/
							CGLDestroyRendererInfo (rend);
							macPrefState = 8;
							return 1;
						}
					}
				}
			}
		}
	}
	if (maxvram < 7500000 ) {       /* put a standard alert and quit*/ 
		SInt16 junkHit;
		char  inError[] = "* Not enough VRAM    ";
		char  inText[] = "* blender needs at least 8Mb    ";
		inError[0] = 16;
		inText[0] = 28;
				
		fprintf(stderr, " vram is %i. not enough, aborting\n", maxvram);
		StandardAlert (   kAlertStopAlert,  &inError,&inText,NULL,&junkHit);
		abort();
	}
	CGLDestroyRendererInfo (rend);
	return 0;
}

void getMacAvailableBounds(short *top, short *left, short *bottom, short *right) {
	Rect outAvailableRect;
	
	GetAvailableWindowPositioningBounds ( GetMainDevice(), &outAvailableRect);
	
	*top = outAvailableRect.top;  
    *left = outAvailableRect.left;
    *bottom = outAvailableRect.bottom; 
    *right = outAvailableRect.right;
}

#endif


static GHOST_SystemHandle g_system= 0;

	/* Some simple ghost <-> blender conversions */
	
static GHOST_TStandardCursor convert_cursor(int curs) {
	switch(curs) {
	default:
	case CURSOR_STD:		return GHOST_kStandardCursorDefault;
	case CURSOR_VPAINT:		return GHOST_kStandardCursorRightArrow;
	case CURSOR_FACESEL:		return GHOST_kStandardCursorRightArrow;
	case CURSOR_WAIT:		return GHOST_kStandardCursorWait;
	case CURSOR_EDIT:		return GHOST_kStandardCursorCrosshair;
	case CURSOR_HELP:		return GHOST_kStandardCursorHelp;
	case CURSOR_X_MOVE:		return GHOST_kStandardCursorLeftRight;
	case CURSOR_Y_MOVE:		return GHOST_kStandardCursorUpDown;
	case CURSOR_PENCIL:		return GHOST_kStandardCursorPencil;
	}
}

static int convert_mbut(GHOST_TButtonMask but) {
	if (but == GHOST_kButtonMaskLeft) {
		return LEFTMOUSE;
	} else if (but == GHOST_kButtonMaskRight) {
		return RIGHTMOUSE;
	} else {
		return MIDDLEMOUSE;
	}
}

static int convert_key(GHOST_TKey key) {
	if (key>=GHOST_kKeyA && key<=GHOST_kKeyZ) {
		return (AKEY + ((int) key - GHOST_kKeyA));
	} else if (key>=GHOST_kKey0 && key<=GHOST_kKey9) {
		return (ZEROKEY + ((int) key - GHOST_kKey0));
	} else if (key>=GHOST_kKeyNumpad0 && key<=GHOST_kKeyNumpad9) {
		return (PAD0 + ((int) key - GHOST_kKeyNumpad0));
	} else if (key>=GHOST_kKeyF1 && key<=GHOST_kKeyF12) {
		return (F1KEY + ((int) key - GHOST_kKeyF1));
	} else {
		switch (key) {
		case GHOST_kKeyBackSpace:		return BACKSPACEKEY;
		case GHOST_kKeyTab:				return TABKEY;
		case GHOST_kKeyLinefeed:		return LINEFEEDKEY;
		case GHOST_kKeyClear:			return 0;
		case GHOST_kKeyEnter:			return RETKEY;
	
		case GHOST_kKeyEsc:				return ESCKEY;
		case GHOST_kKeySpace:			return SPACEKEY;
		case GHOST_kKeyQuote:			return QUOTEKEY;
		case GHOST_kKeyComma:			return COMMAKEY;
		case GHOST_kKeyMinus:			return MINUSKEY;
		case GHOST_kKeyPeriod:			return PERIODKEY;
		case GHOST_kKeySlash:			return SLASHKEY;

		case GHOST_kKeySemicolon:		return SEMICOLONKEY;
		case GHOST_kKeyEqual:			return EQUALKEY;

		case GHOST_kKeyLeftBracket:		return LEFTBRACKETKEY;
		case GHOST_kKeyRightBracket:	return RIGHTBRACKETKEY;
		case GHOST_kKeyBackslash:		return BACKSLASHKEY;
		case GHOST_kKeyAccentGrave:		return ACCENTGRAVEKEY;

		case GHOST_kKeyLeftShift:		return LEFTSHIFTKEY;
		case GHOST_kKeyRightShift:		return RIGHTSHIFTKEY;
		case GHOST_kKeyLeftControl:		return LEFTCTRLKEY;
		case GHOST_kKeyRightControl:	return RIGHTCTRLKEY;
		case GHOST_kKeyCommand:			return COMMANDKEY;
		case GHOST_kKeyLeftAlt:			return LEFTALTKEY;
		case GHOST_kKeyRightAlt:		return RIGHTALTKEY;

		case GHOST_kKeyCapsLock:		return CAPSLOCKKEY;
		case GHOST_kKeyNumLock:			return 0;
		case GHOST_kKeyScrollLock:		return 0;

		case GHOST_kKeyLeftArrow:		return LEFTARROWKEY;
		case GHOST_kKeyRightArrow:		return RIGHTARROWKEY;
		case GHOST_kKeyUpArrow:			return UPARROWKEY;
		case GHOST_kKeyDownArrow:		return DOWNARROWKEY;

		case GHOST_kKeyPrintScreen:		return 0;
		case GHOST_kKeyPause:			return PAUSEKEY;

		case GHOST_kKeyInsert:			return INSERTKEY;
		case GHOST_kKeyDelete:			return DELKEY;
		case GHOST_kKeyHome:			return HOMEKEY;
		case GHOST_kKeyEnd:				return ENDKEY;
		case GHOST_kKeyUpPage:			return PAGEUPKEY;
		case GHOST_kKeyDownPage:		return PAGEDOWNKEY;

		case GHOST_kKeyNumpadPeriod:	return PADPERIOD;
		case GHOST_kKeyNumpadEnter:		return PADENTER;
		case GHOST_kKeyNumpadPlus:		return PADPLUSKEY;
		case GHOST_kKeyNumpadMinus:		return PADMINUS;
		case GHOST_kKeyNumpadAsterisk:	return PADASTERKEY;
		case GHOST_kKeyNumpadSlash:		return PADSLASHKEY;

		case GHOST_kKeyGrLess:		    return GRLESSKEY; 
			
		case GHOST_kKeyUnknown:			return UNKNOWNKEY;

		default:
			return 0;
		}
	}
}

	/***/
	

static Window *window_new(GHOST_WindowHandle ghostwin)
{
	Window *win= MEM_callocN(sizeof(*win), "Window");
	win->ghostwin= ghostwin;
	
	return win;
}

static void window_handle(Window *win, short event, short val)
{
	if (win->handler) {
		win->handler(win, win->user_data, event, val, 0);
	}
}

static void window_handle_ext(Window *win, short event, short val, short extra)
{
	if (win->handler) {
		win->handler(win, win->user_data, event, val, extra);
	}
}

static void window_free(Window *win) 
{
	MEM_freeN(win);
}

	/***/

static Window *active_gl_window= NULL;

Window *window_open(char *title, int posx, int posy, int sizex, int sizey, int start_maximized)
{
	GHOST_WindowHandle ghostwin;
	GHOST_TWindowState inital_state;
	int scr_w, scr_h;

	winlay_get_screensize(&scr_w, &scr_h);
	posy= (scr_h-posy-sizey);
	
	/* create a fullscreen window on unix by default*/
#if !defined(WIN32) && !defined(__APPLE__)
	inital_state= start_maximized?
		GHOST_kWindowStateFullScreen:GHOST_kWindowStateNormal;
#else
#ifdef _WIN32	// FULLSCREEN
	if (start_maximized == G_WINDOWSTATE_FULLSCREEN)
		inital_state= GHOST_kWindowStateFullScreen;
	else
		inital_state= start_maximized?GHOST_kWindowStateMaximized:GHOST_kWindowStateNormal;
#else			// APPLE
	inital_state= start_maximized?GHOST_kWindowStateMaximized:GHOST_kWindowStateNormal;
	inital_state += macPrefState;
#endif
#endif

	ghostwin= GHOST_CreateWindow(g_system, 
								title, 
								posx, posy, sizex, sizey, 
								inital_state, 
								GHOST_kDrawingContextTypeOpenGL,
								0 /* no stereo */);
	
	if (ghostwin) {
		Window *win= window_new(ghostwin);
		
		if (win) {
			GHOST_SetWindowUserData(ghostwin, win);
			
			win->position[0]= posx;
			win->position[1]= posy;
			win->size[0]= sizex;
			win->size[1]= sizey;
			
			win->lmouse[0]= win->size[0]/2;
			win->lmouse[1]= win->size[1]/2;
		} else {
			GHOST_DisposeWindow(g_system, ghostwin);
		}
		
		return win;
	} else {
		return NULL;
	}
}

void window_set_handler(Window *win, WindowHandlerFP handler, void *user_data)
{
	win->handler= handler;
	win->user_data= user_data;
}

static void window_timer_proc(GHOST_TimerTaskHandle timer, GHOST_TUns64 time)
{
	Window *win= GHOST_GetTimerTaskUserData(timer);

	win->handler(win, win->user_data, win->timer_event, 0, 0);
}

void window_set_timer(Window *win, int delay_ms, int event)
{
	if (win->timer) GHOST_RemoveTimer(g_system, win->timer);

	win->timer_event= event;
	win->timer= GHOST_InstallTimer(g_system, delay_ms, delay_ms, window_timer_proc, win);
}

void window_destroy(Window *win) {
	if (active_gl_window==win) {
		active_gl_window= NULL;
	}
	
	if (win->timer) {
		GHOST_RemoveTimer(g_system, win->timer);
		win->timer= NULL;
	}

	GHOST_DisposeWindow(g_system, win->ghostwin);
	window_free(win);
}

void window_set_cursor(Window *win, int curs) {
	if (curs==CURSOR_NONE) {
		GHOST_SetCursorVisibility(win->ghostwin, 0);
	} else {
		GHOST_SetCursorVisibility(win->ghostwin, 1);
		GHOST_SetCursorShape(win->ghostwin, convert_cursor(curs));
	}
}

void window_set_custom_cursor(Window *win, unsigned char mask[16][2], 
					unsigned char bitmap[16][2], int hotx, int hoty) {
	GHOST_SetCustomCursorShape(win->ghostwin, bitmap, mask, hotx, hoty);
}

void window_set_custom_cursor_ex(Window *win, BCursor *cursor, int useBig) {
	if (useBig) {
		GHOST_SetCustomCursorShapeEx(win->ghostwin, 
			cursor->big_bm, cursor->big_mask, 
			cursor->big_sizex,cursor->big_sizey,
			cursor->big_hotx,cursor->big_hoty,
			cursor->fg_color, cursor->bg_color);
	} else {
		GHOST_SetCustomCursorShapeEx(win->ghostwin, 
			cursor->small_bm, cursor->small_mask, 
			cursor->small_sizex,cursor->small_sizey,
			cursor->small_hotx,cursor->small_hoty,
			cursor->fg_color, cursor->bg_color);
	}
}

void window_make_active(Window *win) {
	if (win != active_gl_window) {
		active_gl_window= win;
		GHOST_ActivateWindowDrawingContext(win->ghostwin);
	}
}

void window_swap_buffers(Window *win) {
	GHOST_SwapWindowBuffers(win->ghostwin);
}

static int query_qual(char qual) {
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

static int change_bit(int val, int bit, int to_on) {
	return to_on?(val|bit):(val&~bit);
}

static int event_proc(GHOST_EventHandle evt, GHOST_TUserDataPtr private) 
{
	GHOST_TEventType type= GHOST_GetEventType(evt);

	if (type == GHOST_kEventQuit) {
		exit_usiblender();
	} else {
		GHOST_WindowHandle ghostwin= GHOST_GetEventWindow(evt);
		GHOST_TEventDataPtr data= GHOST_GetEventData(evt);
		Window *win;
		
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
		
		switch (type) {
		case GHOST_kEventCursorMove: {
			if(win->active == 1) {
				GHOST_TEventCursorData *cd= data;
				int cx, cy;
				
				GHOST_ScreenToClient(win->ghostwin, cd->x, cd->y, &cx, &cy);
				win->lmouse[0]= cx;
				win->lmouse[1]= (win->size[1]-1) - cy;
				
				window_handle(win, MOUSEX, win->lmouse[0]);
				window_handle(win, MOUSEY, win->lmouse[1]);
			}
			break;
		}
		case GHOST_kEventButtonDown:
		case GHOST_kEventButtonUp: {
			GHOST_TEventButtonData *bd= data;
			int val= (type==GHOST_kEventButtonDown);
			int bbut= convert_mbut(bd->button);
		
			if (bbut==LEFTMOUSE) {
				if (val) {
					if (win->commandqual) {
						bbut= win->faked_mbut= RIGHTMOUSE;
					} else if ((win->lqual & LR_ALTKEY) && (U.flag & USER_TWOBUTTONMOUSE)) {
						/* finally, it actually USES the userpref! :) -intrr */
						bbut= win->faked_mbut= MIDDLEMOUSE;
					}
				} else {
					if (win->faked_mbut) {
						bbut= win->faked_mbut;
						win->faked_mbut= 0;
					}
				}
			}

			if (bbut==LEFTMOUSE) {
				win->lmbut= change_bit(win->lmbut, L_MOUSE, val);
			} else if (bbut==MIDDLEMOUSE) {
				win->lmbut= change_bit(win->lmbut, M_MOUSE, val);
			} else {
				win->lmbut= change_bit(win->lmbut, R_MOUSE, val);
			}
			window_handle(win, bbut, val);
			
			break;
		}
	
		case GHOST_kEventKeyDown:
		case GHOST_kEventKeyUp: {
			GHOST_TEventKeyData *kd= data;
			int val= (type==GHOST_kEventKeyDown);
			int bkey= convert_key(kd->key);

			if (kd->key == GHOST_kKeyCommand) {
				win->commandqual= val;
			}

			if (bkey) {
				if (bkey==LEFTSHIFTKEY || bkey==RIGHTSHIFTKEY) {
					win->lqual= change_bit(win->lqual, LR_SHIFTKEY, val);
				} else if (bkey==LEFTCTRLKEY || bkey==RIGHTCTRLKEY) {
					win->lqual= change_bit(win->lqual, LR_CTRLKEY, val);
				} else if (bkey==LEFTALTKEY || bkey==RIGHTALTKEY) {
					win->lqual= change_bit(win->lqual, LR_ALTKEY, val);
				} else if (bkey==COMMANDKEY) {
					win->lqual= change_bit(win->lqual, LR_COMMANDKEY, val);
				}

				window_handle_ext(win, bkey, val, kd->ascii);
			}
			
			break;
		}

		case GHOST_kEventWheel:	{
			GHOST_TEventWheelData* wheelData = (GHOST_TEventWheelData*) data;
			if (wheelData->z > 0) {
				window_handle(win, WHEELUPMOUSE, 1);
			} else {
				window_handle(win, WHEELDOWNMOUSE, 1);
			}
			break;
		}

		case GHOST_kEventWindowDeactivate:
		case GHOST_kEventWindowActivate: {
			win->active= (type==GHOST_kEventWindowActivate);
			window_handle(win, INPUTCHANGE, win->active);
			
			if (win->active) {
				if ((win->lqual & LR_SHIFTKEY) && !query_qual('s')) {
					win->lqual= change_bit(win->lqual, LR_SHIFTKEY, 0);
					window_handle(win, LEFTSHIFTKEY, 0);
				}
				if ((win->lqual & LR_CTRLKEY) && !query_qual('c')) {
					win->lqual= change_bit(win->lqual, LR_CTRLKEY, 0);
					window_handle(win, LEFTCTRLKEY, 0);
				}
				if ((win->lqual & LR_ALTKEY) && !query_qual('a')) {
					win->lqual= change_bit(win->lqual, LR_ALTKEY, 0);
					window_handle(win, LEFTALTKEY, 0);
				}
				if ((win->lqual & LR_COMMANDKEY) && !query_qual('C')) {
					win->lqual= change_bit(win->lqual, LR_COMMANDKEY, 0);
					window_handle(win, LR_COMMANDKEY, 0);
				}
				/* probably redundant now (ton) */
				win->commandqual= query_qual('C');

				/* 
				 * XXX quick hack so OSX version works better
				 * when the window is clicked on (focused).
				 *
				 * it used to pass on the old win->lmouse value,
				 * which causes a wrong click in Blender.
				 * Actually, a 'focus' click should not be passed
				 * on to blender... (ton)
				 */
				if(1) { /* enables me to add locals */
					int cx, cy, wx, wy;
					GHOST_GetCursorPosition(g_system, &wx, &wy);

					GHOST_ScreenToClient(win->ghostwin, wx, wy, &cx, &cy);
					win->lmouse[0]= cx;
					win->lmouse[1]= (win->size[1]-1) - cy;
					window_handle(win, MOUSEX, win->lmouse[0]);
					window_handle(win, MOUSEY, win->lmouse[1]);
				}
			}
			
			break;
		}
		case GHOST_kEventWindowClose: {
			window_handle(win, WINCLOSE, 1);
			break;
		}
		case GHOST_kEventWindowUpdate: {
			window_handle(win, REDRAW, 1);
			break;
		}
		case GHOST_kEventWindowSize: {
			GHOST_RectangleHandle client_rect;
			int l, t, r, b, scr_w, scr_h;

			client_rect= GHOST_GetClientBounds(win->ghostwin);
			GHOST_GetRectangle(client_rect, &l, &t, &r, &b);
			
			GHOST_DisposeRectangle(client_rect);
			
			winlay_get_screensize(&scr_w, &scr_h);
			win->position[0]= l;
			win->position[1]= scr_h - b - 1;
			win->size[0]= r-l;
			win->size[1]= b-t;

			window_handle(win, RESHAPE, 1);
			break;
		}
	}
	}
	
	return 1;
}

char *window_get_title(Window *win) {
	char *title= GHOST_GetTitle(win->ghostwin);
	char *mem_title= BLI_strdup(title);
	free(title);

	return mem_title;
}

void window_set_title(Window *win, char *title) {
	GHOST_SetTitle(win->ghostwin, title);
}

short window_get_qual(Window *win) 
{
	int qual= 0;
	
	if( query_qual('s')) qual |= LR_SHIFTKEY;
	if( query_qual('a')) qual |= LR_ALTKEY;
	if( query_qual('c')) qual |= LR_CTRLKEY;
	return qual;
//	return win->lqual;
}

short window_get_mbut(Window *win) {
	return win->lmbut;
}

void window_get_mouse(Window *win, short *mval) {
	mval[0]= win->lmouse[0];
	mval[1]= win->lmouse[1];
}

void window_get_position(Window *win, int *posx_r, int *posy_r) {
	*posx_r= win->position[0];
	*posy_r= win->position[1];
}

void window_get_size(Window *win, int *width_r, int *height_r) {
	*width_r= win->size[0];
	*height_r= win->size[1];
}

void window_set_size(Window *win, int width, int height) {
	GHOST_SetClientSize(win->ghostwin, width, height);
}

void window_lower(Window *win) {
	GHOST_SetWindowOrder(win->ghostwin, GHOST_kWindowOrderBottom);
}

void window_raise(Window *win) {
	GHOST_SetWindowOrder(win->ghostwin, GHOST_kWindowOrderTop);
#ifdef _WIN32
	markdirty_all(); /* to avoid redraw errors in fullscreen mode (aphex) */
#endif
}

#ifdef _WIN32	//FULLSCREEN
void window_toggle_fullscreen(Window *win, int fullscreen) {
	/* these two lines make sure front and backbuffer are equal. for swapbuffers */
	markdirty_all();
	screen_swapbuffers();

	if(fullscreen)
		GHOST_SetWindowState(win->ghostwin, GHOST_kWindowStateFullScreen);
	else
		GHOST_SetWindowState(win->ghostwin, GHOST_kWindowStateMaximized);
}
#endif

void window_warp_pointer(Window *win, int x, int y) {
	int oldx=x, oldy=y;
	
	y= win->size[1] - y - 1;
	GHOST_ClientToScreen(win->ghostwin, x, y, &x, &y);
	GHOST_SetCursorPosition(g_system, x, y);
	
	/* on OSX (for example) the setcursor doesnt create event */
	win->lmouse[0]= oldx;
	win->lmouse[1]= oldy;
}

void window_queue_redraw(Window *win) {
	GHOST_InvalidateWindow(win->ghostwin); // ghost will send back a redraw to blender
}

/***/

void winlay_process_events(int wait_for_event) {
	GHOST_ProcessEvents(g_system, wait_for_event);
	GHOST_DispatchEvents(g_system);
}

void winlay_get_screensize(int *width_r, int *height_r) {
	unsigned int uiwidth;
	unsigned int uiheight;
	
	if (!g_system) {
		GHOST_EventConsumerHandle consumer= GHOST_CreateEventConsumer(event_proc, NULL);
	
		g_system= GHOST_CreateSystem();
		GHOST_AddEventConsumer(g_system, consumer);
	}
	
	GHOST_GetMainDisplayDimensions(g_system, &uiwidth, &uiheight);
	*width_r= uiwidth;
	*height_r= uiheight;
}

Window *winlay_get_active_window(void) {
	return active_gl_window;
}

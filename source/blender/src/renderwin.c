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
 
#ifdef WIN32
/* for the multimedia timer */
#include <windows.h>
#include <mmsystem.h>
#endif

#include <string.h>
#include <stdarg.h>
#include <math.h>

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

#ifdef WIN32
#include "BLI_winstuff.h"
#else
 /* for signal callback, not (fully) supported at windows */
#include <sys/time.h>
#include <signal.h>

#endif

#include <limits.h>

#include "BLI_blenlib.h"

#include "MEM_guardedalloc.h"

#include "BMF_Api.h"

#include "DNA_view3d_types.h"
#include "DNA_screen_types.h"
#include "DNA_vec_types.h"

#include "BKE_global.h"
#include "BKE_utildefines.h"

#include "BIF_gl.h"
#include "BIF_glutil.h"
#include "BIF_graphics.h"
#include "BIF_screen.h"
#include "BIF_space.h"
#include "BIF_mywindow.h"
#include "BIF_previewrender.h"
#include "BIF_renderwin.h"
#include "BIF_resources.h"
#include "BIF_toets.h"

#include "BDR_editobject.h"
#include "BPY_extern.h" /* for BPY_do_all_scripts */

#include "BSE_view.h"
#include "BSE_drawview.h"
#include "BSE_filesel.h"
#include "BSE_headerbuttons.h"

#include "blendef.h"
#include "mydevice.h"
#include "winlay.h"
#include "render.h"

/* ------------ renderwin struct, to prevent too much global vars --------- */
/* ------------ only used for display in a 2nd window  --------- */


/* flags escape presses during event handling
* so we can test for user break later.
*/
#define RW_FLAGS_ESCAPE		(1<<0)
/* old zoom style (2x, locked to mouse, exits
* when mouse leaves window), to be removed
* at some point.
*/
#define RW_FLAGS_OLDZOOM		(1<<1)
/* on when image is being panned with middlemouse
*/
#define RW_FLAGS_PANNING		(1<<2)
/* on when the mouse is dragging over the image
* to examine pixel values.
*/
#define RW_FLAGS_PIXEL_EXAMINING	(1<<3)

/* forces draw of alpha */
#define RW_FLAGS_ALPHA		(1<<4)

/* space for info text */
#define RW_HEADERY		18

typedef struct {
	Window *win;

	float zoom, zoomofs[2];
	int active;
	
	int mbut[3];
	int lmouse[2];
	
	unsigned int flags;
	
	float pan_mouse_start[2], pan_ofs_start[2];

	char *info_text;
	char *render_text, *render_text_spare;
	
} RenderWin;

static RenderWin *render_win= NULL;

/* --------------- help functions for RenderWin struct ---------------------------- */


/* only called in function open_renderwin */
static RenderWin *renderwin_alloc(Window *win)
{
	RenderWin *rw= MEM_mallocN(sizeof(*rw), "RenderWin");
	rw->win= win;
	rw->zoom= 1.0;
	rw->active= 0;
	rw->flags= 0;
	rw->zoomofs[0]= rw->zoomofs[1]= 0;
	rw->info_text= NULL;
	rw->render_text= rw->render_text_spare= NULL;

	rw->lmouse[0]= rw->lmouse[1]= 0;
	rw->mbut[0]= rw->mbut[1]= rw->mbut[2]= 0;

	return rw;
}


static void renderwin_queue_redraw(RenderWin *rw)
{
	window_queue_redraw(rw->win); // to ghost
}

static void renderwin_reshape(RenderWin *rw)
{
	;
}

static void renderwin_get_disprect(RenderWin *rw, float disprect_r[2][2])
{
	float display_w, display_h;
	float cent_x, cent_y;
	int w, h;

	window_get_size(rw->win, &w, &h);
	h-= RW_HEADERY;

	display_w= R.rectx*rw->zoom;
	display_h= R.recty*rw->zoom;
	cent_x= (rw->zoomofs[0] + R.rectx/2)*rw->zoom;
	cent_y= (rw->zoomofs[1] + R.recty/2)*rw->zoom;
	
	disprect_r[0][0]= w/2 - cent_x;
	disprect_r[0][1]= h/2 - cent_y;
	disprect_r[1][0]= disprect_r[0][0] + display_w;
	disprect_r[1][1]= disprect_r[0][1] + display_h;
}

	/** 
	 * Project window coordinate to image pixel coordinate.
	 * Returns true if resulting coordinate is within image.
	 */
static int renderwin_win_to_image_co(RenderWin *rw, int winco[2], int imgco_r[2])
{
	float disprect[2][2];
	
	renderwin_get_disprect(rw, disprect);
	
	imgco_r[0]= (int) ((winco[0]-disprect[0][0])/rw->zoom);
	imgco_r[1]= (int) ((winco[1]-disprect[0][1])/rw->zoom);
	
	return (imgco_r[0]>=0 && imgco_r[1]>=0 && imgco_r[0]<R.rectx && imgco_r[1]<R.recty);
}

	/**
	 * Project window coordinates to normalized device coordinates
	 * Returns true if resulting coordinate is within window.
	 */
static int renderwin_win_to_ndc(RenderWin *rw, int win_co[2], float ndc_r[2])
{
	int w, h;

	window_get_size(rw->win, &w, &h);
	h-= RW_HEADERY;

	ndc_r[0]=  ((float)(win_co[0]*2)/(w-1) - 1.0);
	ndc_r[1]=  ((float)(win_co[1]*2)/(h-1) - 1.0);

	return (fabs(ndc_r[0])<=1.0 && fabs(ndc_r[1])<=1.0);
}

static void renderwin_set_infotext(RenderWin *rw, char *info_text)
{
	if (rw->info_text) MEM_freeN(rw->info_text);
	rw->info_text= info_text?BLI_strdup(info_text):NULL;
}

static void renderwin_reset_view(RenderWin *rw)
{
	int w, h, rectx, recty;

	if (rw->info_text) renderwin_set_infotext(rw, NULL);

	/* now calculate a zoom for when image is larger than window */
	window_get_size(rw->win, &w, &h);
	h-= RW_HEADERY;
	
	/* at this point the r.rectx/y values are not correct yet */
	rectx= (G.scene->r.size*G.scene->r.xsch)/100;
	recty= (G.scene->r.size*G.scene->r.ysch)/100;
	
	/* crop option makes image smaller */
	if ((G.scene->r.mode & R_BORDER) && (G.scene->r.mode & R_MOVIECROP)) { 
		if(!(G.scene->r.scemode & R_OGL)) {
			rectx*= (G.scene->r.border.xmax-G.scene->r.border.xmin);
			recty*= (G.scene->r.border.ymax-G.scene->r.border.ymin);
		}
	}
	
	if(rectx>w || recty>h) {
		if(rectx-w > recty-h) rw->zoom= ((float)w)/((float)rectx);
		else rw->zoom= ((float)h)/((float)recty);
	}
	else rw->zoom= 1.0;

	rw->zoomofs[0]= rw->zoomofs[1]= 0;
	renderwin_queue_redraw(rw);
}

static void renderwin_draw_render_info(RenderWin *rw)
{
	/* render text is added to top */
	if(RW_HEADERY) {
		float colf[3];
		rcti rect;
		
		window_get_size(rw->win, &rect.xmax, &rect.ymax);
		rect.xmin= 0;
		rect.ymin= rect.ymax-RW_HEADERY;
		glEnable(GL_SCISSOR_TEST);
		glaDefine2DArea(&rect);
		
		/* clear header rect */
		BIF_SetTheme(NULL);	// sets view3d theme by default
		BIF_GetThemeColor3fv(TH_HEADER, colf);
		glClearColor(colf[0], colf[1], colf[2], 1.0); 
		glClear(GL_COLOR_BUFFER_BIT);
		
		if(rw->render_text) {
			BIF_ThemeColor(TH_TEXT);
			glRasterPos2i(12, 5);
			BMF_DrawString(G.fonts, rw->render_text);
		}
	}	
	
}

static void renderwin_draw(RenderWin *rw, int just_clear)
{
	float disprect[2][2];
	int set_back_mainwindow;
	rcti rect;
	
	/* since renderwin uses callbacks (controlled by ghost) it can
	   mess up active window output with redraw events after a render. 
	   this is patchy, still WIP */
	set_back_mainwindow = (winlay_get_active_window() != rw->win);
	window_make_active(rw->win);
	
	rect.xmin= rect.ymin= 0;
	window_get_size(rw->win, &rect.xmax, &rect.ymax);
	rect.ymax-= RW_HEADERY;
	
	renderwin_get_disprect(rw, disprect);
	
	/* do this first, so window ends with correct scissor */
	renderwin_draw_render_info(rw);
	
	glEnable(GL_SCISSOR_TEST);
	glaDefine2DArea(&rect);
	
	glClearColor(.1875, .1875, .1875, 1.0); 
	glClear(GL_COLOR_BUFFER_BIT);

	if (just_clear || !R.rectot) {
		glColor3ub(0, 0, 0);
		glRectfv(disprect[0], disprect[1]);
	} else {
		glPixelZoom(rw->zoom, rw->zoom);
		if(rw->flags & RW_FLAGS_ALPHA) {
			char *rect= (char *)R.rectot;
			
			glColorMask(1, 0, 0, 0);
			glaDrawPixelsSafe(disprect[0][0], disprect[0][1], R.rectx, R.recty, rect+3);
			glColorMask(0, 1, 0, 0);
			glaDrawPixelsSafe(disprect[0][0], disprect[0][1], R.rectx, R.recty, rect+2);
			glColorMask(0, 0, 1, 0);
			glaDrawPixelsSafe(disprect[0][0], disprect[0][1], R.rectx, R.recty, rect+1);
			glColorMask(1, 1, 1, 1);
			
		}
		else {
			glaDrawPixelsSafe(disprect[0][0], disprect[0][1], R.rectx, R.recty, R.rectot);
		}
		glPixelZoom(1.0, 1.0);
	}
	
	/* info text is overlayed on bottom */
	if (rw->info_text) {
		float w;
		glBlendFunc(GL_SRC_ALPHA,GL_ONE_MINUS_SRC_ALPHA);
		glEnable(GL_BLEND);
		w=186.0*strlen(rw->info_text)/30;
		glColor4f(.5,.5,.5,.25);
		glRectf(0.0,0.0,w,30.0);
		glDisable(GL_BLEND);
		glColor3ub(255, 255, 255);
		glRasterPos2i(10, 10);
		BMF_DrawString(G.font, rw->info_text);
	}
	
	window_swap_buffers(rw->win);
	
	if (set_back_mainwindow) mainwindow_make_active();	
}

/* ------ interactivity calls for RenderWin ------------- */

static void renderwin_mouse_moved(RenderWin *rw)
{
	if (rw->flags & RW_FLAGS_PIXEL_EXAMINING) {
		int imgco[2];
		char buf[64];
		int *pxlz;	// zbuffer is signed 
		char *pxl;

		if (R.rectot && renderwin_win_to_image_co(rw, rw->lmouse, imgco)) {
			pxl= (char*) &R.rectot[R.rectx*imgco[1] + imgco[0]];
			
			if (R.rectz) {
				pxlz= &R.rectz[R.rectx*imgco[1] + imgco[0]];			
				sprintf(buf, "R: %d, G: %d, B: %d, A: %d, Z: %f", pxl[0], pxl[1], pxl[2], pxl[3], 0.5+0.5*( ((float)*pxlz)/(float)INT_MAX) );
			}
			else {
				sprintf(buf, "R: %d, G: %d, B: %d, A: %d", pxl[0], pxl[1], pxl[2], pxl[3]);			
			}

			renderwin_set_infotext(rw, buf);
			renderwin_queue_redraw(rw);
		} else {
			renderwin_set_infotext(rw, NULL);
			renderwin_queue_redraw(rw);
		}
	} 
	else if (rw->flags & RW_FLAGS_PANNING) {
		int delta_x= rw->lmouse[0] - rw->pan_mouse_start[0];
		int delta_y= rw->lmouse[1] - rw->pan_mouse_start[1];
	
		rw->zoomofs[0]= rw->pan_ofs_start[0] - delta_x/rw->zoom;
		rw->zoomofs[1]= rw->pan_ofs_start[1] - delta_y/rw->zoom;
		rw->zoomofs[0]= CLAMPIS(rw->zoomofs[0], -R.rectx/2, R.rectx/2);
		rw->zoomofs[1]= CLAMPIS(rw->zoomofs[1], -R.recty/2, R.recty/2);

		renderwin_queue_redraw(rw);
	} 
	else if (rw->flags & RW_FLAGS_OLDZOOM) {
		float ndc[2];
		int w, h;

		window_get_size(rw->win, &w, &h);
		h-= RW_HEADERY;
		renderwin_win_to_ndc(rw, rw->lmouse, ndc);

		rw->zoomofs[0]= -0.5*ndc[0]*(w-R.rectx*rw->zoom)/rw->zoom;
		rw->zoomofs[1]= -0.5*ndc[1]*(h-R.recty*rw->zoom)/rw->zoom;

		renderwin_queue_redraw(rw);
	}
}

static void renderwin_mousebut_changed(RenderWin *rw)
{
	if (rw->mbut[0]) {
		rw->flags|= RW_FLAGS_PIXEL_EXAMINING;
	} 
	else if (rw->mbut[1]) {
		rw->flags|= RW_FLAGS_PANNING;
		rw->pan_mouse_start[0]= rw->lmouse[0];
		rw->pan_mouse_start[1]= rw->lmouse[1];
		rw->pan_ofs_start[0]= rw->zoomofs[0];
		rw->pan_ofs_start[1]= rw->zoomofs[1];
	} 
	else {
		if (rw->flags & RW_FLAGS_PANNING) {
			rw->flags &= ~RW_FLAGS_PANNING;
			renderwin_queue_redraw(rw);
		}
		if (rw->flags & RW_FLAGS_PIXEL_EXAMINING) {
			rw->flags&= ~RW_FLAGS_PIXEL_EXAMINING;
			renderwin_set_infotext(rw, NULL);
			renderwin_queue_redraw(rw);
		}
	}
}


/* handler for renderwin, passed on to Ghost */
static void renderwin_handler(Window *win, void *user_data, short evt, short val, char ascii)
{
	RenderWin *rw= user_data;

	// added this for safety, while render it's just creating bezerk results
	if(R.flag & R_RENDERING) {
		if(evt==ESCKEY && val) 
			rw->flags|= RW_FLAGS_ESCAPE;
		return;
	}
	
	if (evt==RESHAPE) {
		renderwin_reshape(rw);
	} 
	else if (evt==REDRAW) {
		renderwin_draw(rw, 0);
	} 
	else if (evt==WINCLOSE) {
		BIF_close_render_display();
	} 
	else if (evt==INPUTCHANGE) {
		rw->active= val;

		if (!val && (rw->flags&RW_FLAGS_OLDZOOM)) {
			rw->flags&= ~RW_FLAGS_OLDZOOM;
			renderwin_reset_view(rw);
		}
	} 
	else if (ELEM(evt, MOUSEX, MOUSEY)) {
		rw->lmouse[evt==MOUSEY]= val;
		renderwin_mouse_moved(rw);
	} 
	else if (ELEM3(evt, LEFTMOUSE, MIDDLEMOUSE, RIGHTMOUSE)) {
		int which= (evt==LEFTMOUSE)?0:(evt==MIDDLEMOUSE)?1:2;
		rw->mbut[which]= val;
		renderwin_mousebut_changed(rw);
	} 
	else if (val) {
		if (evt==ESCKEY) {
			if (rw->flags&RW_FLAGS_OLDZOOM) {
				rw->flags&= ~RW_FLAGS_OLDZOOM;
				renderwin_reset_view(rw);
			} 
			else {
				rw->flags|= RW_FLAGS_ESCAPE;
				mainwindow_raise();
				mainwindow_make_active();
				rw->active= 0;
			}
		} 
		else if( evt==AKEY) {
			rw->flags ^= RW_FLAGS_ALPHA;
			renderwin_queue_redraw(render_win);
		}
		else if (evt==JKEY) {
			if(R.flag==0) BIF_swap_render_rects();
		} 
		else if (evt==ZKEY) {
			if (rw->flags&RW_FLAGS_OLDZOOM) {
				rw->flags&= ~RW_FLAGS_OLDZOOM;
				renderwin_reset_view(rw);
			} else {
				rw->zoom= 2.0;
				rw->flags|= RW_FLAGS_OLDZOOM;
				renderwin_mouse_moved(rw);
			}
		} 
		else if (evt==PADPLUSKEY) {
			if (rw->zoom<15.9) {
				if(rw->zoom>0.5 && rw->zoom<1.0) rw->zoom= 1.0;
				else rw->zoom*= 2.0;
				renderwin_queue_redraw(rw);
			}
		} 
		else if (evt==PADMINUS) {
			if (rw->zoom>0.26) {
				if(rw->zoom>1.0 && rw->zoom<2.0) rw->zoom= 1.0;
				else rw->zoom*= 0.5;
				renderwin_queue_redraw(rw);
			}
		} 
		else if (evt==PADENTER || evt==HOMEKEY) {
			if (rw->flags&RW_FLAGS_OLDZOOM) {
				rw->flags&= ~RW_FLAGS_OLDZOOM;
			}
			renderwin_reset_view(rw);
		} 
		else if (evt==F3KEY) {
			if(R.flag==0) {
				mainwindow_raise();
				mainwindow_make_active();
				rw->active= 0;
				areawinset(find_biggest_area()->win);
				BIF_save_rendered_image();
			}
		} 
		else if (evt==F11KEY) {
			BIF_toggle_render_display();
		} 
		else if (evt==F12KEY) {
			/* if it's rendering, this flag is set */
			if(R.flag==0) BIF_do_render(0);
		}
	}
}

static char *renderwin_get_title(int doswap)
{
	static int swap= 0;
	char *title="";
	
	swap+= doswap;
	
	if(swap & 1) {
		if (G.scene->r.renderer==R_YAFRAY) title = "YafRay:Render (spare)";
		else title = "Blender:Render (spare)";
	}
	else {
		if (G.scene->r.renderer==R_YAFRAY) title = "YafRay:Render";
		else title = "Blender:Render";
	}

	return title;
}

/* opens window and allocs struct */
static void open_renderwin(int winpos[2], int winsize[2])
{
	extern void mywindow_build_and_set_renderwin( int orx, int ory, int sizex, int sizey); // mywindow.c
	Window *win;
	char *title;
	
	title= renderwin_get_title(0);	/* 0 = no swap */
	win= window_open(title, winpos[0], winpos[1], winsize[0], winsize[1]+RW_HEADERY, 0);

	render_win= renderwin_alloc(win);

	/* Ghost calls handler */
	window_set_handler(win, renderwin_handler, render_win);

	winlay_process_events(0);
	window_make_active(render_win->win);
	winlay_process_events(0);
	
	/* mywindow has to know about it too */
	mywindow_build_and_set_renderwin(winpos[0], winpos[1], winsize[0], winsize[1]+RW_HEADERY);
	/* and we should be able to draw 3d in it */
	init_gl_stuff();
	
	renderwin_draw(render_win, 1);
	renderwin_draw(render_win, 1);
}

/* -------------- callbacks for render loop: Window (RenderWin) ----------------------- */

/* calculations for window size and position */
void calc_renderwin_rectangle(int posmask, int renderpos_r[2], int rendersize_r[2]) 
{
	int scr_w, scr_h, x, y, div= 0;
	float ndc_x= 0.0, ndc_y= 0.0;

		/* XXX, we temporarily hack the screen size and position so
		 * the window is always 60 pixels away from a side, really need
		 * a GHOST_GetMaxWindowBounds or so - zr
		 */
	winlay_get_screensize(&scr_w, &scr_h);
	
	rendersize_r[0]= (G.scene->r.size*G.scene->r.xsch)/100;
	rendersize_r[1]= (G.scene->r.size*G.scene->r.ysch)/100;
	
	/* crop option makes image smaller */
	if ((G.scene->r.mode & R_BORDER) && (G.scene->r.mode & R_MOVIECROP)) { 
		rendersize_r[0]*= (G.scene->r.border.xmax-G.scene->r.border.xmin);
		rendersize_r[1]*= (G.scene->r.border.ymax-G.scene->r.border.ymin);
	}
	
	if(G.scene->r.mode & R_PANORAMA) {
		rendersize_r[0]*= G.scene->r.xparts;
		rendersize_r[1]*= G.scene->r.yparts;
	}
	/* increased size of clipping for OSX, should become an option instead */
	rendersize_r[0]= CLAMPIS(rendersize_r[0], 100, scr_w-120);
	rendersize_r[1]= CLAMPIS(rendersize_r[1], 100, scr_h-120);

	for (y=-1; y<=1; y++) {
		for (x=-1; x<=1; x++) {
			if (posmask & (1<<((y+1)*3 + (x+1)))) {
				ndc_x+= x;
				ndc_y+= y;
				div++;
			}
		}
	}

	if (div) {
		ndc_x/= div;
		ndc_y/= div;
	}
		
	renderpos_r[0]= 60 + (scr_w-90-rendersize_r[0])*(ndc_x*0.5 + 0.5);
	renderpos_r[1]= 30 + (scr_h-90-rendersize_r[1])*(ndc_y*0.5 + 0.5);
}
	
/* init renderwin, alloc/open/resize */
static void renderwin_init_display_cb(void) 
{
	if (G.afbreek == 0) {
		int rendersize[2], renderpos[2];

		calc_renderwin_rectangle(G.winpos, renderpos, rendersize);

		if (!render_win) {
			open_renderwin(renderpos, rendersize);
			renderwin_reset_view(render_win); // incl. autozoom for large images
		} else {
			int win_x, win_y;
			int win_w, win_h;

			window_get_position(render_win->win, &win_x, &win_y);
			window_get_size(render_win->win, &win_w, &win_h);
			win_h-= RW_HEADERY;

				/* XXX, this is nasty and I guess bound to cause problems,
				 * but to ensure the window is at the user specified position
				 * and size we reopen the window all the time... we need
				 * a ghost _set_position to fix this -zr
				 */
				 
				 /* XXX, well... it is nasty yes, and reopens windows each time on
				    subsequent renders. Better rule is to make it reopen only only
				    size change, and use the preferred position only on open_renderwin
					cases (ton)
				 */
			if(rendersize[0]!= win_w || rendersize[1]!= win_h) {
				BIF_close_render_display();
				open_renderwin(renderpos, rendersize);
			}
			else {
				window_raise(render_win->win);
				window_make_active(render_win->win);
				mywinset(2);	// to assign scissor/viewport again in mywindow.c. is hackish yes
			}

			renderwin_reset_view(render_win);
			render_win->flags&= ~RW_FLAGS_ESCAPE;
			render_win->active= 1;
		}
		/* make sure we are in normal draw again */
		render_win->flags &= ~RW_FLAGS_ALPHA;
	}
}

/* callback for redraw render win */
static void renderwin_clear_display_cb(short ignore) 
{
	if (render_win) {
		window_make_active(render_win->win);	
		renderwin_draw(render_win, 1);
	}
}

/* XXX, this is not good, we do this without any regard to state
* ... better is to make this an optimization of a more clear
* implementation. the bug shows up when you do something like
* open the window, then draw part of the progress, then get
* a redraw event. whatever can go wrong will. -zr
*
* Note: blocked queue handling while rendering to prevent that (ton)
*/

/* in render window; display a couple of scanlines of rendered image (see callback below) */
static void renderwin_progress(RenderWin *rw, int start_y, int nlines, int rect_w, int rect_h, unsigned char *rect)
{
	float disprect[2][2];
	rcti win_rct;

	win_rct.xmin= win_rct.ymin= 0;
	window_get_size(rw->win, &win_rct.xmax, &win_rct.ymax);
	win_rct.ymax-= RW_HEADERY;
	
	renderwin_get_disprect(rw, disprect);
	
	/* for efficiency & speed; not drawing in Blender UI while rendering */
	//window_make_active(rw->win);

	glEnable(GL_SCISSOR_TEST);
	glaDefine2DArea(&win_rct);

	glDrawBuffer(GL_FRONT);
	glPixelZoom(rw->zoom, rw->zoom);
	glaDrawPixelsSafe(disprect[0][0], disprect[0][1] + start_y*rw->zoom, rect_w, nlines, &rect[start_y*rect_w*4]);
	glPixelZoom(1.0, 1.0);
	glFlush();
	glDrawBuffer(GL_BACK);
}


/* in render window; display a couple of scanlines of rendered image */
static void renderwin_progress_display_cb(int y1, int y2, int w, int h, unsigned int *rect)
{
	if (render_win) {
		renderwin_progress(render_win, y1, y2-y1+1, w, h, (unsigned char*) rect);
	}
}


/* -------------- callbacks for render loop: in View3D ----------------------- */


static View3D *render_view3d = NULL;

/* init Render view callback */
static void renderview_init_display_cb(void)
{
	ScrArea *sa;

		/* Choose the first view with a persp camera,
		 * if one doesn't exist we will get the first
		 * View3D window.
		 */ 
	render_view3d= NULL;
	for (sa= G.curscreen->areabase.first; sa; sa= sa->next) {
		if (sa->win && sa->spacetype==SPACE_VIEW3D) {
			View3D *vd= sa->spacedata.first;
			
			if (vd->persp==2 && vd->camera==G.scene->camera) {
				render_view3d= vd;
				break;
			} else if (!render_view3d) {
				render_view3d= vd;
			}
		}
	}
}


/* in 3d view; display a couple of scanlines of rendered image */
static void renderview_progress_display_cb(int y1, int y2, int w, int h, unsigned int *rect)
{
	if (render_view3d) {
		View3D *v3d= render_view3d;
		int nlines= y2-y1+1;
		float sx, sy, facx, facy;
		rcti win_rct, vb;

		calc_viewborder(v3d, &vb);
		
		/* if border render  */
		if(G.scene->r.mode & R_BORDER) { 
			
			/* but, if image is full (at end of border render, without crop) we don't */
			if(R.rectx != (G.scene->r.size*G.scene->r.xsch)/100 ||
			   R.recty != (G.scene->r.size*G.scene->r.ysch)/100 ) {
			
				facx= (float) (vb.xmax-vb.xmin);
				facy= (float) (vb.ymax-vb.ymin);
				
				vb.xmax= vb.xmin + facx*G.scene->r.border.xmax;
				vb.ymax= vb.ymin + facy*G.scene->r.border.ymax;
				vb.xmin+= facx*G.scene->r.border.xmin;
				vb.ymin+= facy*G.scene->r.border.ymin;
			}
		}
			
		facx= (float) (vb.xmax-vb.xmin)/R.rectx;
		facy= (float) (vb.ymax-vb.ymin)/R.recty;

		bwin_get_rect(v3d->area->win, &win_rct);

		glaDefine2DArea(&win_rct);
	
		glDrawBuffer(GL_FRONT);
		
		sx= vb.xmin;
		sy= vb.ymin + facy*y1;

		glPixelZoom(facx, facy);
		glaDrawPixelsSafe(sx, sy, w, nlines, rect+w*y1);
		glPixelZoom(1.0, 1.0);

		glFlush();
		glDrawBuffer(GL_BACK);
		v3d->flag |= V3D_DISPIMAGE;
		v3d->area->win_swap= WIN_FRONT_OK;
		
	}
}

/* in 3d view; display stats of rendered image */
static void renderview_draw_render_info(char *str)
{
	if (render_view3d) {
		View3D *v3d= render_view3d;
		rcti vb, win_rct;
		
		calc_viewborder(v3d, &vb);
		
		bwin_get_rect(v3d->area->win, &win_rct);
		glaDefine2DArea(&win_rct);
		
		glDrawBuffer(GL_FRONT);
		
		/* clear header rect */
		BIF_ThemeColor(TH_HEADER);
		glRecti(vb.xmin, vb.ymax, vb.xmax, vb.ymax+RW_HEADERY);
		
		if(str) {
			BIF_ThemeColor(TH_TEXT);
			glRasterPos2i(vb.xmin+12, vb.ymax+5);
			BMF_DrawString(G.fonts, str);
		}
		
		glFlush();
		glDrawBuffer(GL_BACK);

		v3d->area->win_swap= WIN_FRONT_OK;
		
	}
}


/* -------------- callbacks for render loop: interactivity ----------------------- */


/* callback for print info in top header of renderwin */
/* time is only not zero on last call, we then don't update the other stats */ 
static void printrenderinfo_cb(double time, int sample)
{
	extern int mem_in_use;
	static int totvert=0, totvlak=0, tothalo=0, totlamp=0;
	static float megs_used_memory=0.0;
	char str[300], *spos= str;
		
	if(time==0.0) {
		megs_used_memory= mem_in_use/(1024.0*1024.0);
		totvert= R.totvert;
		totvlak= R.totvlak;
		totlamp= R.totlamp;
		tothalo= R.tothalo;
	}
	
	if(tothalo)
		spos+= sprintf(spos, "Fra:%d  Ve:%d Fa:%d Ha:%d La:%d Mem:%.2fM", (G.scene->r.cfra), totvert, totvlak, tothalo, totlamp, megs_used_memory);
	else 
		spos+= sprintf(spos, "Fra:%d  Ve:%d Fa:%d La:%d Mem:%.2fM", (G.scene->r.cfra), totvert, totvlak, totlamp, megs_used_memory);

	if(time==0.0) {
		if (R.r.mode & R_FIELDS) {
			spos+= sprintf(spos, "Field %c ", (R.flag&R_SEC_FIELD)?'B':'A');
		}
		if (sample!=-1) {
			spos+= sprintf(spos, "Sample: %d    ", sample);
		}
	}
	else {
		extern char info_time_str[32];	// header_info.c
		timestr(time, info_time_str);
		spos+= sprintf(spos, " Time:%s ", info_time_str);
	}
	
	if(render_win) {
		if(render_win->render_text) MEM_freeN(render_win->render_text);
		render_win->render_text= BLI_strdup(str);
		glDrawBuffer(GL_FRONT);
		renderwin_draw_render_info(render_win);
		glFlush();
		glDrawBuffer(GL_BACK);
	}
	else renderview_draw_render_info(str);
}

/* -------------- callback system to allow ESC from rendering ----------------------- */

/* POSIX & WIN32: this function is called all the time, and should not use cpu or resources */
static int test_break(void)
{

	if(G.afbreek==2) { /* code for testing queue */

		G.afbreek= 0;

		blender_test_break(); /* tests blender interface */

		if (G.afbreek==0 && render_win) { /* tests window */
			winlay_process_events(0);
			// render_win can be closed in winlay_process_events()
			if (render_win == 0 || (render_win->flags & RW_FLAGS_ESCAPE)) {
				G.afbreek= 1;
			}
		}
	}

	if(G.afbreek==1) return 1;
	else return 0;
}



#ifdef _WIN32
/* we use the multimedia time here */
static UINT uRenderTimerId;

void CALLBACK interruptESC(UINT uID, UINT uMsg, DWORD dwUser, DWORD dw1, DWORD dw2)
{
	if(G.afbreek==0) G.afbreek= 2;	/* code for read queue */
}

/* WIN32: init SetTimer callback */
static void init_test_break_callback()
{
	timeBeginPeriod(50);
	uRenderTimerId = timeSetEvent(250, 1, interruptESC, 0, TIME_PERIODIC);
}

/* WIN32: stop SetTimer callback */
static void end_test_break_callback()
{
	timeEndPeriod(50);
	timeKillEvent(uRenderTimerId);
}

#else
/* all other OS's support signal(SIGVTALRM) */

/* POSIX: this function goes in the signal() callback */
static void interruptESC(int sig)
{

	if(G.afbreek==0) G.afbreek= 2;	/* code for read queue */

	/* call again, timer was reset */
	signal(SIGVTALRM, interruptESC);
}

/* POSIX: initialize timer and signal */
static void init_test_break_callback()
{

	struct itimerval tmevalue;

	tmevalue.it_interval.tv_sec = 0;
	tmevalue.it_interval.tv_usec = 250000;
	/* wanneer de eerste ? */
	tmevalue.it_value.tv_sec = 0;
	tmevalue.it_value.tv_usec = 10000;

	signal(SIGVTALRM, interruptESC);
	setitimer(ITIMER_VIRTUAL, &tmevalue, 0);

}

/* POSIX: stop timer and callback */
static void end_test_break_callback()
{
	struct itimerval tmevalue;

	tmevalue.it_value.tv_sec = 0;
	tmevalue.it_value.tv_usec = 0;
	setitimer(ITIMER_VIRTUAL, &tmevalue, 0);
	signal(SIGVTALRM, SIG_IGN);

}


#endif



/* -------------- callbacks for render loop: init & run! ----------------------- */


/* - initialize displays
   - both opengl render as blender render
   - set callbacks
   - cleanup
*/

static void do_render(View3D *ogl_render_view3d, int anim, int force_dispwin)
{
	
	/* we set this flag to prevent renderwindow queue to execute another render */
	R.flag= R_RENDERING;

	if (G.displaymode == R_DISPLAYWIN || force_dispwin) {
		RE_set_initrenderdisplay_callback(NULL);
		RE_set_clearrenderdisplay_callback(renderwin_clear_display_cb);
		RE_set_renderdisplay_callback(renderwin_progress_display_cb);

		renderwin_init_display_cb();
	} 
	else {
		BIF_close_render_display();
		RE_set_initrenderdisplay_callback(renderview_init_display_cb);
		RE_set_clearrenderdisplay_callback(NULL);
		RE_set_renderdisplay_callback(renderview_progress_display_cb);
	}

	init_test_break_callback();
	RE_set_test_break_callback(test_break);
	
	RE_set_timecursor_callback(set_timecursor);
	RE_set_printrenderinfo_callback(printrenderinfo_cb);
	
	if (render_win) {
		window_set_cursor(render_win->win, CURSOR_WAIT);
		// when opening new window... not cross platform identical behaviour, so
		// for now call it each time
		// if(ogl_render_view3d) init_gl_stuff();
	}
	waitcursor(1);

	G.afbreek= 0;
	if(G.obedit && !(G.scene->r.scemode & R_OGL)) {
		exit_editmode(0);	/* 0 = no free data */
	}

	if(anim) {
		RE_animrender(ogl_render_view3d);
	}
	else {
		RE_initrender(ogl_render_view3d);
	}

	if(anim) update_for_newframe_muted();  // only when anim, causes redraw event which frustrates dispview
	
	if (render_win) window_set_cursor(render_win->win, CURSOR_STD);

	free_filesel_spec(G.scene->r.pic);

	G.afbreek= 0;
	end_test_break_callback();
	
	/* in dispiew it will destroy the image otherwise
	   window_make_active() raises window at osx and sends redraws */
	if(G.displaymode==R_DISPLAYWIN) {
		mainwindow_make_active();
	
		/* after an envmap creation...  */
		if(R.flag & R_REDRAW_PRV) {
			BIF_all_preview_changed();
		}
		allqueue(REDRAWBUTSSCENE, 0);	// visualize fbuf for example
	}
	
	R.flag= 0;
	waitcursor(0);	// waitcursor checks rendering R.flag...
}

/* finds area with a 'dispview' set */
static ScrArea *find_dispimage_v3d(void)
{
	ScrArea *sa;
	
	for (sa= G.curscreen->areabase.first; sa; sa= sa->next) {
		if (sa->spacetype==SPACE_VIEW3D) {
			View3D *vd= sa->spacedata.first;
			if (vd->flag & V3D_DISPIMAGE)
				return sa;
		}
	}
	
	return NULL;
}

/* used for swapping with spare buffer, when images are different size */
static void scalefastrect(unsigned int *recto, unsigned int *rectn, int oldx, int oldy, int newx, int newy)
{
	unsigned int *rect, *newrect;
	int x, y;
	int ofsx, ofsy, stepx, stepy;

	stepx = (int)((65536.0 * (oldx - 1.0) / (newx - 1.0)) + 0.5);
	stepy = (int)((65536.0 * (oldy - 1.0) / (newy - 1.0)) + 0.5);
	ofsy = 32768;
	newrect= rectn;
	
	for (y = newy; y > 0 ; y--){
		rect = recto;
		rect += (ofsy >> 16) * oldx;
		ofsy += stepy;
		ofsx = 32768;
		for (x = newx ; x>0 ; x--){
			*newrect++ = rect[ofsx >> 16];
			ofsx += stepx;
		}
	}
}

/* -------------- API: externally called --------------- */

/* not used anywhere ??? */
#if 0
void BIF_renderwin_make_active(void)
{
	if(render_win) {
		window_make_active(render_win->win);
		mywinset(2);
	}
}
#endif

/* set up display, render an image or scene */
void BIF_do_render(int anim)
{
	int slink_flag = 0;

	if (G.f & G_DOSCRIPTLINKS) {
		BPY_do_all_scripts(SCRIPT_RENDER);
		if (!anim) { /* avoid FRAMECHANGED slink in render callback */
			G.f &= ~G_DOSCRIPTLINKS;
			slink_flag = 1;
		}
	}

	/* if start render in 3d win, use layer from window (e.g also local view) */
	if(curarea && curarea->spacetype==SPACE_VIEW3D) {
		int lay= G.scene->lay;
		if(G.vd->lay & 0xFF000000)	// localview
			G.scene->lay |= G.vd->lay;
		else G.scene->lay= G.vd->lay;
		
		do_render(NULL, anim, 0);
		
		G.scene->lay= lay;
	}
	else do_render(NULL, anim, 0);

	if (slink_flag) G.f |= G_DOSCRIPTLINKS;
	if (G.f & G_DOSCRIPTLINKS) BPY_do_all_scripts(SCRIPT_POSTRENDER);
}

/* set up display, render the current area view in an image */
void BIF_do_ogl_render(View3D *ogl_render_view3d, int anim)
{
	G.scene->r.scemode |= R_OGL;
	do_render(ogl_render_view3d, anim, 1);
	G.scene->r.scemode &= ~R_OGL;
}

void BIF_redraw_render_rect(void)
{
	
	/* redraw */
	if (G.displaymode == R_DISPLAYWIN) {
		// don't open render_win if rendering has been
	    // canceled or the render_win has been actively closed
		if (render_win) {
			renderwin_queue_redraw(render_win);
		}
	} else {
		renderview_init_display_cb();
		renderview_progress_display_cb(0, R.recty-1, R.rectx, R.recty, R.rectot);
	}
}	

void BIF_swap_render_rects(void)
{
	unsigned int *temp;

	if(R.rectspare==0) {
		R.rectspare= (unsigned int *)MEM_callocN(sizeof(int)*R.rectx*R.recty, "rectot");
		R.sparex= R.rectx;
		R.sparey= R.recty;
	}
	else if(R.sparex!=R.rectx || R.sparey!=R.recty) {
		temp= (unsigned int *)MEM_callocN(sizeof(int)*R.rectx*R.recty, "rectot");
					
		scalefastrect(R.rectspare, temp, R.sparex, R.sparey, R.rectx, R.recty);
		MEM_freeN(R.rectspare);
		R.rectspare= temp;
					
		R.sparex= R.rectx;
		R.sparey= R.recty;
	}
	
	temp= R.rectot;
	R.rectot= R.rectspare;
	R.rectspare= temp;
	
	if (G.displaymode == R_DISPLAYWIN) {
		if (render_win) {
			char *tmp= render_win->render_text_spare;
			render_win->render_text_spare= render_win->render_text;
			render_win->render_text= tmp;
			
			window_set_title(render_win->win, renderwin_get_title(1));
			
		}
	}

	/* redraw */
	BIF_redraw_render_rect();
}				

/* called from usiblender.c too, to free and close renderwin */
void BIF_close_render_display(void)
{
	if (render_win) {

		if (render_win->info_text) MEM_freeN(render_win->info_text);
		if (render_win->render_text) MEM_freeN(render_win->render_text);
		if (render_win->render_text_spare) MEM_freeN(render_win->render_text_spare);

		window_destroy(render_win->win); /* ghost close window */
		MEM_freeN(render_win);

		render_win= NULL;
	}
}


/* typical with F11 key, show image or hide/close */
void BIF_toggle_render_display(void) 
{
	ScrArea *sa= find_dispimage_v3d();
	
	if(R.rectot==NULL);		// do nothing
	else if (render_win && G.displaymode==R_DISPLAYWIN) {
		if(render_win->active) {
			mainwindow_raise();
			mainwindow_make_active();
			render_win->active= 0;
		}
		else {
			window_raise(render_win->win);
			window_make_active(render_win->win);
			render_win->active= 1;
		}
	} 
	else if (sa && G.displaymode==R_DISPLAYVIEW) {
		View3D *vd= sa->spacedata.first;
		vd->flag &= ~V3D_DISPIMAGE;
		scrarea_queue_winredraw(sa);
	} 
	else {
		if (G.displaymode == R_DISPLAYWIN) {
			renderwin_init_display_cb();
		} else {
			if (render_win) {
				BIF_close_render_display();
			}
			renderview_init_display_cb();
			renderview_progress_display_cb(0, R.recty-1, R.rectx, R.recty, R.rectot);
		}
	}
}

void BIF_renderwin_set_custom_cursor(unsigned char mask[16][2], unsigned char bitmap[16][2])
{
	if (render_win) {
		window_set_custom_cursor(render_win->win, mask, bitmap, 7, 7);
	}
}

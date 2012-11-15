/*
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
 * The Original Code is Copyright (C) 2001-2002 by NaN Holding BV.
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): Campbell Barton
 *
 * ***** END GPL LICENSE BLOCK *****
 */

/** \file blender/windowmanager/intern/wm_playanim.c
 *  \ingroup wm
 *
 * \note This file uses ghost directly and none of the WM definitions.
 *       this could be made into its own module, alongside creator/
 */

#include <sys/types.h>
#include <fcntl.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

#ifndef WIN32
#  include <unistd.h>
#  include <sys/times.h>
#  include <sys/wait.h>
#else
#  include <io.h>
#endif
#include "MEM_guardedalloc.h"

#include "PIL_time.h"

#include "BLI_fileops.h"
#include "BLI_listbase.h"
#include "BLI_path_util.h"
#include "BLI_rect.h"
#include "BLI_string.h"
#include "BLI_utildefines.h"

#include "IMB_imbuf_types.h"
#include "IMB_imbuf.h"

#include "BKE_blender.h"
#include "BKE_global.h"
#include "BKE_image.h"

#include "BIF_gl.h"
#include "BIF_glutil.h"

#include "DNA_scene_types.h"
#include "ED_datafiles.h" /* for fonts */
#include "GHOST_C-api.h"
#include "BLF_api.h"

#include "wm_event_types.h"

#include "WM_api.h"  /* only for WM_main_playanim */

typedef struct PlayState {

	/* playback state */
	short direction;
	short next;
	short once;
	short turbo;
	short pingpong;
	short noskip;
	short sstep;
	short pause;
	short wait2;
	short stopped;
	short go;

	int fstep;

	/* current picture */
	struct PlayAnimPict *picture;

	/* set once at the start */
	int ibufx, ibufy;
	int fontid;

	/* saves passing args */
	struct ImBuf *curframe_ibuf;
} PlayState;

/* for debugging */
#if 0
void print_ps(PlayState *ps)
{
	printf("ps:\n");
	printf("    direction=%d,\n", (int)ps->direction);
	printf("    next=%d,\n", ps->next);
	printf("    once=%d,\n", ps->once);
	printf("    turbo=%d,\n", ps->turbo);
	printf("    pingpong=%d,\n", ps->pingpong);
	printf("    noskip=%d,\n", ps->noskip);
	printf("    sstep=%d,\n", ps->sstep);
	printf("    pause=%d,\n", ps->pause);
	printf("    wait2=%d,\n", ps->wait2);
	printf("    stopped=%d,\n", ps->stopped);
	printf("    go=%d,\n\n", ps->go);
	fflush(stdout);
}
#endif

/* global for window and events */
typedef enum eWS_Qual {
	WS_QUAL_LSHIFT  = (1 << 0),
	WS_QUAL_RSHIFT  = (1 << 1),
	WS_QUAL_SHIFT   = (WS_QUAL_LSHIFT | WS_QUAL_RSHIFT),
	WS_QUAL_LALT    = (1 << 2),
	WS_QUAL_RALT    = (1 << 3),
	WS_QUAL_ALT     = (WS_QUAL_LALT | WS_QUAL_RALT),
	WS_QUAL_LCTRL   = (1 << 4),
	WS_QUAL_RCTRL   = (1 << 5),
	WS_QUAL_LMOUSE  = (1 << 16),
	WS_QUAL_MMOUSE  = (1 << 17),
	WS_QUAL_RMOUSE  = (1 << 18),
	WS_QUAL_MOUSE   = (WS_QUAL_LMOUSE | WS_QUAL_MMOUSE | WS_QUAL_RMOUSE)
} eWS_Qual;

static struct WindowStateGlobal {
	GHOST_SystemHandle ghost_system;
	void *ghost_window;

	/* events */
	eWS_Qual qual;
} g_WS = {NULL};

static void playanim_window_get_size(int *width_r, int *height_r)
{
	GHOST_RectangleHandle bounds = GHOST_GetClientBounds(g_WS.ghost_window);
	*width_r = GHOST_GetWidthRectangle(bounds);
	*height_r = GHOST_GetHeightRectangle(bounds);
	GHOST_DisposeRectangle(bounds);
}

/* implementation */
static void playanim_event_qual_update(void)
{
	int val;

	/* Shift */
	GHOST_GetModifierKeyState(g_WS.ghost_system, GHOST_kModifierKeyLeftShift, &val);
	if (val) g_WS.qual |=  WS_QUAL_LSHIFT;
	else     g_WS.qual &= ~WS_QUAL_LSHIFT;

	GHOST_GetModifierKeyState(g_WS.ghost_system, GHOST_kModifierKeyRightShift, &val);
	if (val) g_WS.qual |=  WS_QUAL_RSHIFT;
	else     g_WS.qual &= ~WS_QUAL_RSHIFT;

	/* Control */
	GHOST_GetModifierKeyState(g_WS.ghost_system, GHOST_kModifierKeyLeftControl, &val);
	if (val) g_WS.qual |=  WS_QUAL_LCTRL;
	else     g_WS.qual &= ~WS_QUAL_LCTRL;

	GHOST_GetModifierKeyState(g_WS.ghost_system, GHOST_kModifierKeyRightControl, &val);
	if (val) g_WS.qual |=  WS_QUAL_RCTRL;
	else     g_WS.qual &= ~WS_QUAL_RCTRL;

	/* Alt */
	GHOST_GetModifierKeyState(g_WS.ghost_system, GHOST_kModifierKeyLeftAlt, &val);
	if (val) g_WS.qual |=  WS_QUAL_LCTRL;
	else     g_WS.qual &= ~WS_QUAL_LCTRL;

	GHOST_GetModifierKeyState(g_WS.ghost_system, GHOST_kModifierKeyRightAlt, &val);
	if (val) g_WS.qual |=  WS_QUAL_RCTRL;
	else     g_WS.qual &= ~WS_QUAL_RCTRL;

	/* LMB */
	GHOST_GetButtonState(g_WS.ghost_system, GHOST_kButtonMaskLeft, &val);
	if (val) g_WS.qual |=  WS_QUAL_LMOUSE;
	else     g_WS.qual &= ~WS_QUAL_LMOUSE;

	/* MMB */
	GHOST_GetButtonState(g_WS.ghost_system, GHOST_kButtonMaskMiddle, &val);
	if (val) g_WS.qual |=  WS_QUAL_MMOUSE;
	else     g_WS.qual &= ~WS_QUAL_MMOUSE;

	/* RMB */
	GHOST_GetButtonState(g_WS.ghost_system, GHOST_kButtonMaskRight, &val);
	if (val) g_WS.qual |=  WS_QUAL_RMOUSE;
	else     g_WS.qual &= ~WS_QUAL_RMOUSE;
}

typedef struct PlayAnimPict {
	struct PlayAnimPict *next, *prev;
	char *mem;
	int size;
	char *name;
	struct ImBuf *ibuf;
	struct anim *anim;
	int frame;
	int IB_flags;
} PlayAnimPict;

static struct ListBase picsbase = {NULL, NULL};
static int fromdisk = FALSE;
static float zoomx = 1.0, zoomy = 1.0;
static double ptottime = 0.0, swaptime = 0.04;

static int pupdate_time(void)
{
	static double ltime;
	double time;

	time = PIL_check_seconds_timer();

	ptottime += (time - ltime);
	ltime = time;
	return (ptottime < 0);
}

static void playanim_toscreen(PlayAnimPict *picture, struct ImBuf *ibuf, int fontid, int fstep)
{

	if (ibuf == NULL) {
		printf("no ibuf !\n");
		return;
	}
	if (ibuf->rect == NULL && ibuf->rect_float) {
		IMB_rect_from_float(ibuf);
		imb_freerectfloatImBuf(ibuf);
	}
	if (ibuf->rect == NULL)
		return;

	GHOST_ActivateWindowDrawingContext(g_WS.ghost_window);

	glRasterPos2f(0.0f, 0.0f);

	glDrawPixels(ibuf->x, ibuf->y, GL_RGBA, GL_UNSIGNED_BYTE, ibuf->rect);

	pupdate_time();

	if (picture && (g_WS.qual & (WS_QUAL_SHIFT | WS_QUAL_LMOUSE)) && (fontid != -1)) {
		int sizex, sizey;
		float fsizex_inv, fsizey_inv;
		char str[32 + FILE_MAX];
		cpack(-1);
		BLI_snprintf(str, sizeof(str), "%s | %.2f frames/s", picture->name, fstep / swaptime);

		playanim_window_get_size(&sizex, &sizey);
		fsizex_inv = 1.0f / sizex;
		fsizey_inv = 1.0f / sizey;

		BLF_enable(fontid, BLF_ASPECT);
		BLF_aspect(fontid, fsizex_inv, fsizey_inv, 1.0f);
		BLF_position(fontid, 10.0f * fsizex_inv, 10.0f * fsizey_inv, 0.0f);
		BLF_draw(fontid, str, sizeof(str));
	}

	GHOST_SwapWindowBuffers(g_WS.ghost_window);
}

static void build_pict_list(char *first, int totframes, int fstep, int fontid)
{
	char *mem, filepath[FILE_MAX];
//	short val;
	PlayAnimPict *picture = NULL;
	struct ImBuf *ibuf = NULL;
	char str[32 + FILE_MAX];
	struct anim *anim;

	if (IMB_isanim(first)) {
		/* OCIO_TODO: support different input color space */
		anim = IMB_open_anim(first, IB_rect, 0, NULL);
		if (anim) {
			int pic;
			ibuf = IMB_anim_absolute(anim, 0, IMB_TC_NONE, IMB_PROXY_NONE);
			if (ibuf) {
				playanim_toscreen(NULL, ibuf, fontid, fstep);
				IMB_freeImBuf(ibuf);
			}

			for (pic = 0; pic < IMB_anim_get_duration(anim, IMB_TC_NONE); pic++) {
				picture = (PlayAnimPict *)MEM_callocN(sizeof(PlayAnimPict), "Pict");
				picture->anim = anim;
				picture->frame = pic;
				picture->IB_flags = IB_rect;
				BLI_snprintf(str, sizeof(str), "%s : %4.d", first, pic + 1);
				picture->name = strdup(str);
				BLI_addtail(&picsbase, picture);
			}
		}
		else {
			printf("couldn't open anim %s\n", first);
		}
	}
	else {
		int count = 0;

		BLI_strncpy(filepath, first, sizeof(filepath));

		pupdate_time();
		ptottime = 1.0;

		/* O_DIRECT
		 *
		 * If set, all reads and writes on the resulting file descriptor will
		 * be performed directly to or from the user program buffer, provided
		 * appropriate size and alignment restrictions are met.  Refer to the
		 * F_SETFL and F_DIOINFO commands in the fcntl(2) manual entry for
		 * information about how to determine the alignment constraints.
		 * O_DIRECT is a Silicon Graphics extension and is only supported on
		 * local EFS and XFS file systems.
		 */

		while (IMB_ispic(filepath) && totframes) {
			size_t size;
			int file;

			file = open(filepath, O_BINARY | O_RDONLY, 0);
			if (file < 0) {
				/* print errno? */
				return;
			}

			picture = (PlayAnimPict *)MEM_callocN(sizeof(PlayAnimPict), "picture");
			if (picture == NULL) {
				printf("Not enough memory for pict struct '%s'\n", filepath);
				close(file);
				return;
			}
			size = BLI_file_descriptor_size(file);

			if (size < 1) {
				close(file);
				MEM_freeN(picture);
				return;
			}

			picture->size = size;
			picture->IB_flags = IB_rect;

			if (fromdisk == FALSE) {
				mem = (char *)MEM_mallocN(size, "build pic list");
				if (mem == NULL) {
					printf("Couldn't get memory\n");
					close(file);
					MEM_freeN(picture);
					return;
				}

				if (read(file, mem, size) != size) {
					printf("Error while reading %s\n", filepath);
					close(file);
					MEM_freeN(picture);
					MEM_freeN(mem);
					return;
				}
			}
			else {
				mem = NULL;
			}

			picture->mem = mem;
			picture->name = strdup(filepath);
			close(file);
			BLI_addtail(&picsbase, picture);
			count++;

			pupdate_time();

			if (ptottime > 1.0) {
				/* OCIO_TODO: support different input color space */
				if (picture->mem) {
					ibuf = IMB_ibImageFromMemory((unsigned char *)picture->mem, picture->size,
					                             picture->IB_flags, NULL, picture->name);
				}
				else {
					ibuf = IMB_loadiffname(picture->name, picture->IB_flags, NULL);
				}
				if (ibuf) {
					playanim_toscreen(picture, ibuf, fontid, fstep);
					IMB_freeImBuf(ibuf);
				}
				pupdate_time();
				ptottime = 0.0;
			}

			BLI_newname(filepath, +fstep);

#if 0 // XXX25
			while (qtest()) {
				switch (qreadN(&val)) {
					case ESCKEY:
						if (val) return;
						break;
				}
			}
#endif
			totframes--;
		}
	}
	return;
}

static int ghost_event_proc(GHOST_EventHandle evt, GHOST_TUserDataPtr ps_void)
{
	PlayState *ps = (PlayState *)ps_void;
	GHOST_TEventType type = GHOST_GetEventType(evt);
	int val;

	// print_ps(ps);

	playanim_event_qual_update();

	/* convert ghost event into value keyboard or mouse */
	val = ELEM(type, GHOST_kEventKeyDown, GHOST_kEventButtonDown);

	if (ps->wait2 && ps->stopped) {
		ps->stopped = FALSE;
	}

	switch (type) {
		case GHOST_kEventKeyDown:
		case GHOST_kEventKeyUp:
		{
			GHOST_TEventKeyData *key_data;

			key_data = (GHOST_TEventKeyData *)GHOST_GetEventData(evt);
			switch (key_data->key) {
				case GHOST_kKeyA:
					if (val) ps->noskip = !ps->noskip;
					break;
				case GHOST_kKeyP:
					if (val) ps->pingpong = !ps->pingpong;
					break;
				case GHOST_kKeyNumpad1:
					if (val) swaptime = ps->fstep / 60.0;
					break;
				case GHOST_kKeyNumpad2:
					if (val) swaptime = ps->fstep / 50.0;
					break;
				case GHOST_kKeyNumpad3:
					if (val) swaptime = ps->fstep / 30.0;
					break;
				case GHOST_kKeyNumpad4:
					if (g_WS.qual & WS_QUAL_SHIFT)
						swaptime = ps->fstep / 24.0;
					else
						swaptime = ps->fstep / 25.0;
					break;
				case GHOST_kKeyNumpad5:
					if (val) swaptime = ps->fstep / 20.0;
					break;
				case GHOST_kKeyNumpad6:
					if (val) swaptime = ps->fstep / 15.0;
					break;
				case GHOST_kKeyNumpad7:
					if (val) swaptime = ps->fstep / 12.0;
					break;
				case GHOST_kKeyNumpad8:
					if (val) swaptime = ps->fstep / 10.0;
					break;
				case GHOST_kKeyNumpad9:
					if (val) swaptime = ps->fstep / 6.0;
					break;
				case GHOST_kKeyLeftArrow:
					if (val) {
						ps->sstep = TRUE;
						ps->wait2 = FALSE;
						if (g_WS.qual & WS_QUAL_SHIFT) {
							ps->picture = picsbase.first;
							ps->next = 0;
						}
						else {
							ps->next = -1;
						}
					}
					break;
				case GHOST_kKeyDownArrow:
					if (val) {
						ps->wait2 = FALSE;
						if (g_WS.qual & WS_QUAL_SHIFT) {
							ps->next = ps->direction = -1;
						}
						else {
							ps->next = -10;
							ps->sstep = TRUE;
						}
					}
					break;
				case GHOST_kKeyRightArrow:
					if (val) {
						ps->sstep = TRUE;
						ps->wait2 = FALSE;
						if (g_WS.qual & WS_QUAL_SHIFT) {
							ps->picture = picsbase.last;
							ps->next = 0;
						}
						else {
							ps->next = 1;
						}
					}
					break;
				case GHOST_kKeyUpArrow:
					if (val) {
						ps->wait2 = FALSE;
						if (g_WS.qual & WS_QUAL_SHIFT) {
							ps->next = ps->direction = 1;
						}
						else {
							ps->next = 10;
							ps->sstep = TRUE;
						}
					}
					break;

				case GHOST_kKeySlash:
				case GHOST_kKeyNumpadSlash:
					if (val) {
						if (g_WS.qual & WS_QUAL_SHIFT) {
							if (ps->curframe_ibuf)
								printf(" Name: %s | Speed: %.2f frames/s\n", ps->curframe_ibuf->name, ps->fstep / swaptime);
						}
						else {
							swaptime = ps->fstep / 5.0;
						}
					}
					break;
				case GHOST_kKeyEqual:
					if (val) {
						if (g_WS.qual & WS_QUAL_SHIFT) {
							ps->pause++;
							printf("pause:%d\n", ps->pause);
						}
						else {
							swaptime /= 1.1;
						}
					}
					break;
				case GHOST_kKeyMinus:
					if (val) {
						if (g_WS.qual & WS_QUAL_SHIFT) {
							ps->pause--;
							printf("pause:%d\n", ps->pause);
						}
						else {
							swaptime *= 1.1;
						}
					}
					break;
				case GHOST_kKeyNumpad0:
					if (val) {
						if (ps->once) {
							ps->once = ps->wait2 = FALSE;
						}
						else {
							ps->picture = NULL;
							ps->once = TRUE;
							ps->wait2 = FALSE;
						}
					}
					break;
				case GHOST_kKeyEnter:
				case GHOST_kKeyNumpadEnter:
					if (val) {
						ps->wait2 = ps->sstep = FALSE;
					}
					break;
				case GHOST_kKeyNumpadPeriod:
					if (val) {
						if (ps->sstep) ps->wait2 = FALSE;
						else {
							ps->sstep = TRUE;
							ps->wait2 = !ps->wait2;
						}
					}
					break;
				case GHOST_kKeyNumpadPlus:
					if (val == 0) break;
					zoomx += 2.0f;
					zoomy += 2.0f;
					/* no break??? - is this intentional? - campbell XXX25 */
				case GHOST_kKeyNumpadMinus:
				{
					int sizex, sizey;
					/* int ofsx, ofsy; */ /* UNUSED */

					if (val == 0) break;
					if (zoomx > 1.0f) zoomx -= 1.0f;
					if (zoomy > 1.0f) zoomy -= 1.0f;
					// playanim_window_get_position(&ofsx, &ofsy);
					playanim_window_get_size(&sizex, &sizey);
					/* ofsx += sizex / 2; */ /* UNUSED */
					/* ofsy += sizey / 2; */ /* UNUSED */
					sizex = zoomx * ps->ibufx;
					sizey = zoomy * ps->ibufy;
					/* ofsx -= sizex / 2; */ /* UNUSED */
					/* ofsy -= sizey / 2; */ /* UNUSED */
					// window_set_position(g_WS.ghost_window,sizex,sizey);
					GHOST_SetClientSize(g_WS.ghost_window, sizex, sizey);
					break;
				}
				case GHOST_kKeyEsc:
					ps->go = FALSE;
					break;
				default:
					break;
			}
			break;
		}
		case GHOST_kEventCursorMove:
		{
			if (g_WS.qual & WS_QUAL_LMOUSE) {
				int sizex, sizey;
				int i;

				GHOST_TEventCursorData *cd = GHOST_GetEventData(evt);
				int cx, cy;

				GHOST_ScreenToClient(g_WS.ghost_window, cd->x, cd->y, &cx, &cy);

				playanim_window_get_size(&sizex, &sizey);
				ps->picture = picsbase.first;
				/* TODO - store in ps direct? */
				i = 0;
				while (ps->picture) {
					i++;
					ps->picture = ps->picture->next;
				}
				i = (i * cx) / sizex;
				ps->picture = picsbase.first;
				for (; i > 0; i--) {
					if (ps->picture->next == NULL) break;
					ps->picture = ps->picture->next;
				}
				ps->sstep = TRUE;
				ps->wait2 = FALSE;
				ps->next = 0;
			}
			break;
		}
		case GHOST_kEventWindowSize:
		case GHOST_kEventWindowMove:
		{
			int sizex, sizey;

			playanim_window_get_size(&sizex, &sizey);
			GHOST_ActivateWindowDrawingContext(g_WS.ghost_window);

			glViewport(0, 0, sizex, sizey);
			glScissor(0, 0, sizex, sizey);

			zoomx = (float) sizex / ps->ibufx;
			zoomy = (float) sizey / ps->ibufy;
			zoomx = floor(zoomx + 0.5f);
			zoomy = floor(zoomy + 0.5f);
			if (zoomx < 1.0f) zoomx = 1.0f;
			if (zoomy < 1.0f) zoomy = 1.0f;

			sizex = zoomx * ps->ibufx;
			sizey = zoomy * ps->ibufy;

			glPixelZoom(zoomx, zoomy);
			glEnable(GL_DITHER);
			ptottime = 0.0;
			playanim_toscreen(ps->picture, ps->curframe_ibuf, ps->fontid, ps->fstep);

			break;
		}
		case GHOST_kEventQuit:
		case GHOST_kEventWindowClose:
		{
			ps->go = FALSE;
			break;
		}
		default:
			/* quiet warnings */
			break;
	}

	return 1;
}

static void playanim_window_open(const char *title, int posx, int posy, int sizex, int sizey, int start_maximized)
{
	GHOST_TWindowState inital_state;
	GHOST_TUns32 scr_w, scr_h;

	GHOST_GetMainDisplayDimensions(g_WS.ghost_system, &scr_w, &scr_h);

	posy = (scr_h - posy - sizey);

	if (start_maximized == G_WINDOWSTATE_FULLSCREEN)
		inital_state = start_maximized ? GHOST_kWindowStateFullScreen : GHOST_kWindowStateNormal;
	else
		inital_state = start_maximized ? GHOST_kWindowStateMaximized : GHOST_kWindowStateNormal;

	g_WS.ghost_window = GHOST_CreateWindow(g_WS.ghost_system,
	                                       title,
	                                       posx, posy, sizex, sizey,
	                                       inital_state,
	                                       GHOST_kDrawingContextTypeOpenGL,
	                                       FALSE /* no stereo */, FALSE);
}


void WM_main_playanim(int argc, const char **argv)
{
	struct ImBuf *ibuf = NULL;
	char filepath[FILE_MAX];
	GHOST_TUns32 maxwinx, maxwiny;
	/* short c233 = FALSE, yuvx = FALSE; */ /* UNUSED */
	int i;
	/* This was done to disambiguate the name for use under c++. */
	struct anim *anim = NULL;
	int start_x = 0, start_y = 0;
	int sfra = -1;
	int efra = -1;
	int totblock;

	PlayState ps = {0};

	/* ps.doubleb   = TRUE;*/ /* UNUSED */
	ps.go        = TRUE;
	ps.direction = TRUE;
	ps.next      = TRUE;
	ps.once      = FALSE;
	ps.turbo     = FALSE;
	ps.pingpong  = FALSE;
	ps.noskip    = FALSE;
	ps.sstep     = FALSE;
	ps.pause     = FALSE;
	ps.wait2     = FALSE;
	ps.stopped   = FALSE;
	ps.picture   = NULL;
	/* resetmap = FALSE */

	ps.fstep     = 1;

	ps.fontid = -1;

	while (argc > 1) {
		if (argv[1][0] == '-') {
			switch (argv[1][1]) {
				case 'm':
					fromdisk = TRUE;
					break;
				case 'p':
					if (argc > 3) {
						start_x = atoi(argv[2]);
						start_y = atoi(argv[3]);
						argc -= 2;
						argv += 2;
					}
					else {
						printf("too few arguments for -p (need 2): skipping\n");
					}
					break;
				case 'f':
					if (argc > 3) {
						double fps = atof(argv[2]);
						double fps_base = atof(argv[3]);
						if (fps == 0.0) {
							fps = 1;
							printf("invalid fps,"
							       "forcing 1\n");
						}
						swaptime = fps_base / fps;
						argc -= 2;
						argv += 2;
					}
					else {
						printf("too few arguments for -f (need 2): skipping\n");
					}
					break;
				case 's':
					sfra = MIN2(MAXFRAME, MAX2(1, atoi(argv[2]) ));
					argc--;
					argv++;
					break;
				case 'e':
					efra = MIN2(MAXFRAME, MAX2(1, atoi(argv[2]) ));
					argc--;
					argv++;
					break;
				case 'j':
					ps.fstep = MIN2(MAXFRAME, MAX2(1, atoi(argv[2])));
					swaptime *= ps.fstep;
					argc--;
					argv++;
					break;
				default:
					printf("unknown option '%c': skipping\n", argv[1][1]);
					break;
			}
			argc--;
			argv++;
		}
		else {
			break;
		}
	}

	if (argc > 1) {
		BLI_strncpy(filepath, argv[1], sizeof(filepath));
	}
	else {
		BLI_current_working_dir(filepath, sizeof(filepath));
		BLI_add_slash(filepath);
	}

	if (IMB_isanim(filepath)) {
		/* OCIO_TODO: support different input color spaces */
		anim = IMB_open_anim(filepath, IB_rect, 0, NULL);
		if (anim) {
			ibuf = IMB_anim_absolute(anim, 0, IMB_TC_NONE, IMB_PROXY_NONE);
			IMB_close_anim(anim);
			anim = NULL;
		}
	}
	else if (!IMB_ispic(filepath)) {
		exit(1);
	}

	if (ibuf == NULL) {
		/* OCIO_TODO: support different input color space */
		ibuf = IMB_loadiffname(filepath, IB_rect, NULL);
	}

	if (ibuf == NULL) {
		printf("couldn't open %s\n", filepath);
		exit(1);
	}

#if 0 //XXX25
	#if !defined(WIN32) && !defined(__APPLE__)
	if (fork()) exit(0);
	#endif
#endif //XXX25

	/* XXX, fixme zr */
	{
//		extern void add_to_mainqueue(wmWindow *win, void *user_data, short evt, short val, char ascii);

		GHOST_EventConsumerHandle consumer = GHOST_CreateEventConsumer(ghost_event_proc, &ps);

		g_WS.ghost_system = GHOST_CreateSystem();
		GHOST_AddEventConsumer(g_WS.ghost_system, consumer);



		playanim_window_open("Blender:Anim", start_x, start_y, ibuf->x, ibuf->y, 0);
//XXX25		window_set_handler(g_WS.ghost_window, add_to_mainqueue, NULL);

		glMatrixMode(GL_PROJECTION);
		glLoadIdentity();
		glOrtho(0.0f, 1.0f, 0.0f, 1.0f, -1.0f, 1.0f);
		glMatrixMode(GL_MODELVIEW);
	}

	GHOST_GetMainDisplayDimensions(g_WS.ghost_system, &maxwinx, &maxwiny);

	//GHOST_ActivateWindowDrawingContext(g_WS.ghost_window);

	/* initialize the font */
	BLF_init(11, 72);
	ps.fontid = BLF_load_mem("monospace", (unsigned char *)datatoc_bmonofont_ttf, datatoc_bmonofont_ttf_size);
	BLF_size(ps.fontid, 11, 72);

	ps.ibufx = ibuf->x;
	ps.ibufy = ibuf->y;

	if (maxwinx % ibuf->x) maxwinx = ibuf->x * (1 + (maxwinx / ibuf->x));
	if (maxwiny % ibuf->y) maxwiny = ibuf->y * (1 + (maxwiny / ibuf->y));

	glClearColor(0.0, 0.0, 0.0, 0.0);
	glClear(GL_COLOR_BUFFER_BIT);

	GHOST_SwapWindowBuffers(g_WS.ghost_window);

	if (sfra == -1 || efra == -1) {
		/* one of the frames was invalid, just use all images */
		sfra = 1;
		efra = MAXFRAME;
	}

	build_pict_list(filepath, (efra - sfra) + 1, ps.fstep, ps.fontid);

	for (i = 2; i < argc; i++) {
		BLI_strncpy(filepath, argv[i], sizeof(filepath));
		build_pict_list(filepath, (efra - sfra) + 1, ps.fstep, ps.fontid);
	}

	IMB_freeImBuf(ibuf);
	ibuf = NULL;

	pupdate_time();
	ptottime = 0;

	/* newly added in 2.6x, without this images never get freed */
#define USE_IMB_CACHE

	while (ps.go) {
		if (ps.pingpong)
			ps.direction = -ps.direction;

		if (ps.direction == 1) {
			ps.picture = picsbase.first;
		}
		else {
			ps.picture = picsbase.last;
		}

		if (ps.picture == NULL) {
			printf("couldn't find pictures\n");
			ps.go = FALSE;
		}
		if (ps.pingpong) {
			if (ps.direction == 1) {
				ps.picture = ps.picture->next;
			}
			else {
				ps.picture = ps.picture->prev;
			}
		}
		if (ptottime > 0.0) ptottime = 0.0;

		while (ps.picture) {
#ifndef USE_IMB_CACHE
			if (ibuf != NULL && ibuf->ftype == 0) IMB_freeImBuf(ibuf);
#endif
			if (ps.picture->ibuf) {
				ibuf = ps.picture->ibuf;
			}
			else if (ps.picture->anim) {
				ibuf = IMB_anim_absolute(ps.picture->anim, ps.picture->frame, IMB_TC_NONE, IMB_PROXY_NONE);
			}
			else if (ps.picture->mem) {
				/* use correct colorspace here */
				ibuf = IMB_ibImageFromMemory((unsigned char *) ps.picture->mem, ps.picture->size,
				                             ps.picture->IB_flags, NULL, ps.picture->name);
			}
			else {
				/* use correct colorspace here */
				ibuf = IMB_loadiffname(ps.picture->name, ps.picture->IB_flags, NULL);
			}

			if (ibuf) {

#ifdef USE_IMB_CACHE
				ps.picture->ibuf = ibuf;
#endif

				BLI_strncpy(ibuf->name, ps.picture->name, sizeof(ibuf->name));

				/* why only windows? (from 2.4x) - campbell */
#ifdef _WIN32
				GHOST_SetTitle(g_WS.ghost_window, ps.picture->name);
#endif

				while (pupdate_time()) PIL_sleep_ms(1);
				ptottime -= swaptime;
				playanim_toscreen(ps.picture, ibuf, ps.fontid, ps.fstep);
			} /* else deleten */
			else {
				printf("error: can't play this image type\n");
				exit(0);
			}

			if (ps.once) {
				if (ps.picture->next == NULL) {
					ps.wait2 = TRUE;
				}
				else if (ps.picture->prev == NULL) {
					ps.wait2 = TRUE;
				}
			}

			ps.next = ps.direction;


			{
				int hasevent = GHOST_ProcessEvents(g_WS.ghost_system, 0);
				if (hasevent) {
					GHOST_DispatchEvents(g_WS.ghost_system);
				}
			}

			/* XXX25 - we should not have to do this, but it makes scrubbing functional! */
			if (g_WS.qual & WS_QUAL_LMOUSE) {
				ps.next = 0;
			}
			else {
				ps.sstep = 0;
			}

			ps.wait2 = ps.sstep;

			if (ps.wait2 == 0 && ps.stopped == 0) {
				ps.stopped = TRUE;
			}

			pupdate_time();

			if (ps.picture && ps.next) {
				/* always at least set one step */
				while (ps.picture) {
					if (ps.next < 0) {
						ps.picture = ps.picture->prev;
					}
					else {
						ps.picture = ps.picture->next;
					}

					if (ps.once && ps.picture != NULL) {
						if (ps.picture->next == NULL) {
							ps.wait2 = TRUE;
						}
						else if (ps.picture->prev == NULL) {
							ps.wait2 = TRUE;
						}
					}

					if (ps.wait2 || ptottime < swaptime || ps.turbo || ps.noskip) break;
					ptottime -= swaptime;
				}
				if (ps.picture == NULL && ps.sstep) {
					if (ps.next < 0) {
						ps.picture = picsbase.last;
					}
					else if (ps.next > 0) {
						ps.picture = picsbase.first;
					}
				}
			}
			if (ps.go == FALSE) {
				break;
			}
		}
	}
	ps.picture = picsbase.first;
	anim = NULL;
	while (ps.picture) {
		if (ps.picture && ps.picture->anim && (anim != ps.picture->anim)) {
			// to prevent divx crashes
			anim = ps.picture->anim;
			IMB_close_anim(anim);
		}

		if (ps.picture->ibuf) {
			IMB_freeImBuf(ps.picture->ibuf);
		}
		if (ps.picture->mem) {
			MEM_freeN(ps.picture->mem);
		}

		ps.picture = ps.picture->next;
	}

	/* cleanup */
#ifndef USE_IMB_CACHE
	if (ibuf) IMB_freeImBuf(ibuf);
#endif

	BLI_freelistN(&picsbase);
#if 0 // XXX25
	free_blender();
#else
	/* we still miss freeing a lot!,
	 * but many areas could skip initialization too for anim play */
	IMB_exit();
	BKE_images_exit();
	BLF_exit();
#endif
	GHOST_DisposeWindow(g_WS.ghost_system, g_WS.ghost_window);

	totblock = MEM_get_memory_blocks_in_use();
	if (totblock != 0) {
		/* prints many bAKey, bArgument's which are tricky to fix */
#if 0
		printf("Error Totblock: %d\n", totblock);
		MEM_printmemlist();
#endif
	}
}

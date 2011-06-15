/*
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
 * Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
 *
 * The Original Code is Copyright (C) 2008 Blender Foundation.
 * All rights reserved.
 *
 *
 * Contributor(s): Blender Foundation,
 *                 Sergey Sharybin
 *
 * ***** END GPL LICENSE BLOCK *****
 */

/** \file blender/editors/space_clip/clip_editor.c
 *  \ingroup spclip
 */

#include <stddef.h>

#include "BKE_main.h"
#include "BKE_movieclip.h"
#include "BKE_context.h"
#include "BKE_tracking.h"
#include "DNA_object_types.h"	/* SELECT */

#include "BLI_utildefines.h"
#include "BLI_math.h"

#include "IMB_imbuf_types.h"
#include "IMB_imbuf.h"

#include "ED_screen.h"
#include "ED_clip.h"

#include "BIF_gl.h"

#include "WM_api.h"
#include "WM_types.h"

void ED_space_clip_set(bContext *C, SpaceClip *sc, MovieClip *clip)
{
	sc->clip= clip;

	if(sc->clip && sc->clip->id.us==0)
		sc->clip->id.us= 1;

	if(C)
		WM_event_add_notifier(C, NC_MOVIECLIP|NA_SELECTED, sc->clip);
}

MovieClip *ED_space_clip(SpaceClip *sc)
{
	return sc->clip;
}

ImBuf *ED_space_clip_acquire_buffer(SpaceClip *sc)
{
	if(sc->clip) {
		ImBuf *ibuf;

		ibuf= BKE_movieclip_acquire_ibuf(sc->clip, &sc->user);

		if(ibuf && (ibuf->rect || ibuf->rect_float))
			return ibuf;
	}

	return NULL;
}

void ED_space_clip_size(SpaceClip *sc, int *width, int *height)
{
	if(!sc->clip) {
		*width= 0;
		*height= 0;
	} else
		BKE_movieclip_acquire_size(sc->clip, &sc->user, width, height);
}

void ED_space_clip_zoom(SpaceClip *sc, ARegion *ar, float *zoomx, float *zoomy)
{
	int width, height;

	ED_space_clip_size(sc, &width, &height);

	*zoomx= (float)(ar->winrct.xmax - ar->winrct.xmin + 1)/(float)((ar->v2d.cur.xmax - ar->v2d.cur.xmin)*width);
	*zoomy= (float)(ar->winrct.ymax - ar->winrct.ymin + 1)/(float)((ar->v2d.cur.ymax - ar->v2d.cur.ymin)*height);
}

void ED_clip_update_frame(const Main *mainp, int cfra)
{
	wmWindowManager *wm;
	wmWindow *win;

	/* image window, compo node users */
	for(wm=mainp->wm.first; wm; wm= wm->id.next) { /* only 1 wm */
		for(win= wm->windows.first; win; win= win->next) {
			ScrArea *sa;
			for(sa= win->screen->areabase.first; sa; sa= sa->next) {
				if(sa->spacetype==SPACE_CLIP) {
					SpaceClip *sc= sa->spacedata.first;
					BKE_movieclip_user_set_frame(&sc->user, cfra);
				}
			}
		}
	}
}

static int selected_boundbox(SpaceClip *sc, float min[2], float max[2])
{
	MovieClip *clip= ED_space_clip(sc);
	MovieTrackingTrack *track;
	int width, height, ok= 0;

	INIT_MINMAX2(min, max);

	ED_space_clip_size(sc, &width, &height);

	track= clip->tracking.tracks.first;
	while(track) {
		if(TRACK_SELECTED(track)) {
			MovieTrackingMarker *marker= BKE_tracking_get_marker(track, sc->user.framenr);

			if(marker) {
				float pos[2];

				pos[0]= marker->pos[0]*width;
				pos[1]= marker->pos[1]*height;

				DO_MINMAX2(pos, min, max);

				ok= 1;
			}
		}

		track= track->next;
	}

	return ok;
}

void ED_clip_view_selection(SpaceClip *sc, ARegion *ar, int fit)
{
	int w, h, width, height, frame_width, frame_height;
	float min[2], max[2];

	ED_space_clip_size(sc, &frame_width, &frame_height);

	if(frame_width==0 || frame_height==0) return;

	width= ar->winrct.xmax - ar->winrct.xmin + 1;
	height= ar->winrct.ymax - ar->winrct.ymin + 1;

	if(!selected_boundbox(sc, min, max)) return;

	w= max[0]-min[0];
	h= max[1]-min[1];

	/* center view */
	sc->xof= ((float)(max[0]+min[0]-frame_width))/2;
	sc->yof= ((float)(max[1]+min[1]-frame_height))/2;

	/* set zoom to see all selection */
	if(w>0 && h>0) {
		float zoomx, zoomy, newzoom;

		zoomx= (float)width/w;
		zoomy= (float)height/h;

		newzoom= 1.0f/power_of_2(1/MIN2(zoomx, zoomy));

		if(fit || sc->zoom>newzoom)
			sc->zoom= newzoom;
	}
}

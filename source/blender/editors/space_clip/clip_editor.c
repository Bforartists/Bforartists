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
 * Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
 *
 * The Original Code is Copyright (C) 2011 Blender Foundation.
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

#include "MEM_guardedalloc.h"

#include "BKE_main.h"
#include "BKE_mask.h"
#include "BKE_movieclip.h"
#include "BKE_context.h"
#include "BKE_tracking.h"

#include "DNA_mask_types.h"
#include "DNA_object_types.h"	/* SELECT */

#include "BLI_utildefines.h"
#include "BLI_math.h"

#include "GPU_extensions.h"

#include "IMB_imbuf_types.h"
#include "IMB_imbuf.h"

#include "ED_screen.h"
#include "ED_clip.h"

#include "BIF_gl.h"
#include "BIF_glutil.h"

#include "WM_api.h"
#include "WM_types.h"

#include "UI_view2d.h"

#include "clip_intern.h"	// own include

/* ******** operactor poll functions ******** */

int ED_space_clip_poll(bContext *C)
{
	SpaceClip *sc = CTX_wm_space_clip(C);

	if (sc && sc->clip)
		return TRUE;

	return FALSE;
}

int ED_space_clip_view_clip_poll(bContext *C)
{
	SpaceClip *sc = CTX_wm_space_clip(C);

	if (sc && sc->clip) {
		return sc->view == SC_VIEW_CLIP;
	}

	return FALSE;
}

int ED_space_clip_tracking_poll(bContext *C)
{
	SpaceClip *sc = CTX_wm_space_clip(C);

	if (sc && sc->clip)
		return ED_space_clip_check_show_trackedit(sc);

	return FALSE;
}

int ED_space_clip_maskedit_poll(bContext *C)
{
	SpaceClip *sc = CTX_wm_space_clip(C);

	if (sc && sc->clip) {
		return ED_space_clip_check_show_maskedit(sc);
	}

	return FALSE;
}

int ED_space_clip_maskedit_mask_poll(bContext *C)
{
	if (ED_space_clip_maskedit_poll(C)) {
		MovieClip *clip = CTX_data_edit_movieclip(C);

		if (clip) {
			SpaceClip *sc = CTX_wm_space_clip(C);

			return sc->mask_info.mask != NULL;
		}
	}

	return FALSE;
}

/* ******** common editing functions ******** */

void ED_space_clip_get_size(SpaceClip *sc, int *width, int *height)
{
	if (sc->clip) {
		BKE_movieclip_get_size(sc->clip, &sc->user, width, height);
	}
	else {
		*width = *height = IMG_SIZE_FALLBACK;
	}
}

void ED_space_clip_get_size_fl(SpaceClip *sc, float size[2])
{
	int size_i[2];
	ED_space_clip_get_size(sc, &size_i[0], &size_i[1]);
	size[0] = size_i[0];
	size[1] = size_i[1];
}

void ED_space_clip_get_zoom(SpaceClip *sc, ARegion *ar, float *zoomx, float *zoomy)
{
	int width, height;

	ED_space_clip_get_size(sc, &width, &height);

	*zoomx = (float)(ar->winrct.xmax - ar->winrct.xmin + 1) / (float)((ar->v2d.cur.xmax - ar->v2d.cur.xmin) * width);
	*zoomy = (float)(ar->winrct.ymax - ar->winrct.ymin + 1) / (float)((ar->v2d.cur.ymax - ar->v2d.cur.ymin) * height);
}

void ED_space_clip_get_aspect(SpaceClip *sc, float *aspx, float *aspy)
{
	MovieClip *clip = ED_space_clip_get_clip(sc);

	if (clip)
		BKE_movieclip_aspect(clip, aspx, aspy);
	else
		*aspx = *aspy = 1.0f;

	if (*aspx < *aspy) {
		*aspy = *aspy / *aspx;
		*aspx = 1.0f;
	}
	else {
		*aspx = *aspx / *aspy;
		*aspy = 1.0f;
	}
}

void ED_space_clip_get_aspect_dimension_aware(SpaceClip *sc, float *aspx, float *aspy)
{
	int w, h;

	/* most of tools does not require aspect to be returned with dimensions correction
	 * due to they're invariant to this stuff, but some transformation tools like rotation
	 * should be aware of aspect correction caused by different resolution in different
	 * directions.
	 * mainly this is sued for transformation stuff
	 */

	if (!sc->clip) {
		*aspx = 1.0f;
		*aspy = 1.0f;

		return;
	}

	ED_space_clip_get_aspect(sc, aspx, aspy);
	BKE_movieclip_get_size(sc->clip, &sc->user, &w, &h);

	*aspx *= (float) w;
	*aspy *= (float) h;

	if (*aspx < *aspy) {
		*aspy = *aspy / *aspx;
		*aspx = 1.0f;
	}
	else {
		*aspx = *aspx / *aspy;
		*aspy = 1.0f;
	}
}

/* return current frame number in clip space */
int ED_space_clip_get_clip_frame_number(SpaceClip *sc)
{
	MovieClip *clip = ED_space_clip_get_clip(sc);

	return BKE_movieclip_remap_scene_to_clip_frame(clip, sc->user.framenr);
}

ImBuf *ED_space_clip_get_buffer(SpaceClip *sc)
{
	if (sc->clip) {
		ImBuf *ibuf;

		ibuf = BKE_movieclip_get_postprocessed_ibuf(sc->clip, &sc->user, sc->postproc_flag);

		if (ibuf && (ibuf->rect || ibuf->rect_float))
			return ibuf;

		if (ibuf)
			IMB_freeImBuf(ibuf);
	}

	return NULL;
}

ImBuf *ED_space_clip_get_stable_buffer(SpaceClip *sc, float loc[2], float *scale, float *angle)
{
	if (sc->clip) {
		ImBuf *ibuf;

		ibuf = BKE_movieclip_get_stable_ibuf(sc->clip, &sc->user, loc, scale, angle, sc->postproc_flag);

		if (ibuf && (ibuf->rect || ibuf->rect_float))
			return ibuf;

		if (ibuf)
			IMB_freeImBuf(ibuf);
	}

	return NULL;
}

void ED_clip_update_frame(const Main *mainp, int cfra)
{
	wmWindowManager *wm;
	wmWindow *win;

	/* image window, compo node users */
	for (wm = mainp->wm.first; wm; wm = wm->id.next) { /* only 1 wm */
		for (win = wm->windows.first; win; win = win->next) {
			ScrArea *sa;

			for (sa = win->screen->areabase.first; sa; sa = sa->next) {
				if (sa->spacetype == SPACE_CLIP) {
					SpaceClip *sc = sa->spacedata.first;

					sc->scopes.ok = FALSE;

					BKE_movieclip_user_set_frame(&sc->user, cfra);
				}
			}
		}
	}
}

static int selected_boundbox(SpaceClip *sc, float min[2], float max[2])
{
	MovieClip *clip = ED_space_clip_get_clip(sc);
	MovieTrackingTrack *track;
	int width, height, ok = FALSE;
	ListBase *tracksbase = BKE_tracking_get_active_tracks(&clip->tracking);
	int framenr = ED_space_clip_get_clip_frame_number(sc);

	INIT_MINMAX2(min, max);

	ED_space_clip_get_size(sc, &width, &height);

	track = tracksbase->first;
	while (track) {
		if (TRACK_VIEW_SELECTED(sc, track)) {
			MovieTrackingMarker *marker = BKE_tracking_marker_get(track, framenr);

			if (marker) {
				float pos[3];

				pos[0] = marker->pos[0] + track->offset[0];
				pos[1] = marker->pos[1] + track->offset[1];
				pos[2] = 0.0f;

				/* undistortion happens for normalized coords */
				if (sc->user.render_flag & MCLIP_PROXY_RENDER_UNDISTORT) {
					/* undistortion happens for normalized coords */
					ED_clip_point_undistorted_pos(sc, pos, pos);
				}

				pos[0] *= width;
				pos[1] *= height;

				mul_v3_m4v3(pos, sc->stabmat, pos);

				DO_MINMAX2(pos, min, max);

				ok = TRUE;
			}
		}

		track = track->next;
	}

	return ok;
}

int ED_clip_view_selection(const bContext *C, ARegion *ar, int fit)
{
	SpaceClip *sc = CTX_wm_space_clip(C);
	int w, h, frame_width, frame_height;
	float min[2], max[2];

	ED_space_clip_get_size(sc, &frame_width, &frame_height);

	if (frame_width == 0 || frame_height == 0)
		return FALSE;

	if (!selected_boundbox(sc, min, max))
		return FALSE;

	/* center view */
	clip_view_center_to_point(sc, (max[0] + min[0]) / (2 * frame_width),
	                              (max[1] + min[1]) / (2 * frame_height));

	w = max[0] - min[0];
	h = max[1] - min[1];

	/* set zoom to see all selection */
	if (w > 0 && h > 0) {
		int width, height;
		float zoomx, zoomy, newzoom, aspx, aspy;

		ED_space_clip_get_aspect(sc, &aspx, &aspy);

		width = ar->winrct.xmax - ar->winrct.xmin + 1;
		height = ar->winrct.ymax - ar->winrct.ymin + 1;

		zoomx = (float)width / w / aspx;
		zoomy = (float)height / h / aspy;

		newzoom = 1.0f / power_of_2(1.0f / minf(zoomx, zoomy));

		if (fit || sc->zoom > newzoom)
			sc->zoom = newzoom;
	}

	return TRUE;
}

void ED_clip_point_undistorted_pos(SpaceClip *sc, const float co[2], float r_co[2])
{
	copy_v2_v2(r_co, co);

	if (sc->user.render_flag & MCLIP_PROXY_RENDER_UNDISTORT) {
		MovieClip *clip = ED_space_clip_get_clip(sc);
		float aspy = 1.0f / clip->tracking.camera.pixel_aspect;
		int width, height;

		BKE_movieclip_get_size(sc->clip, &sc->user, &width, &height);

		r_co[0] *= width;
		r_co[1] *= height * aspy;

		BKE_tracking_undistort_v2(&clip->tracking, r_co, r_co);

		r_co[0] /= width;
		r_co[1] /= height * aspy;
	}
}

void ED_clip_point_stable_pos(SpaceClip *sc, ARegion *ar, float x, float y, float *xr, float *yr)
{
	int sx, sy, width, height;
	float zoomx, zoomy, pos[3], imat[4][4];

	ED_space_clip_get_zoom(sc, ar, &zoomx, &zoomy);
	ED_space_clip_get_size(sc, &width, &height);

	UI_view2d_to_region_no_clip(&ar->v2d, 0.0f, 0.0f, &sx, &sy);

	pos[0] = (x - sx) / zoomx;
	pos[1] = (y - sy) / zoomy;
	pos[2] = 0.0f;

	invert_m4_m4(imat, sc->stabmat);
	mul_v3_m4v3(pos, imat, pos);

	*xr = pos[0] / width;
	*yr = pos[1] / height;

	if (sc->user.render_flag & MCLIP_PROXY_RENDER_UNDISTORT) {
		MovieClip *clip = ED_space_clip_get_clip(sc);
		MovieTracking *tracking = &clip->tracking;
		float aspy = 1.0f / tracking->camera.pixel_aspect;
		float tmp[2] = {*xr * width, *yr * height * aspy};

		BKE_tracking_distort_v2(tracking, tmp, tmp);

		*xr = tmp[0] / width;
		*yr = tmp[1] / (height * aspy);
	}
}

/**
 * \brief the reverse of ED_clip_point_stable_pos(), gets the marker region coords.
 * better name here? view_to_track / track_to_view or so?
 */
void ED_clip_point_stable_pos__reverse(SpaceClip *sc, ARegion *ar, const float co[2], float r_co[2])
{
	float zoomx, zoomy;
	float pos[3];
	int width, height;
	int sx, sy;

	UI_view2d_to_region_no_clip(&ar->v2d, 0.0f, 0.0f, &sx, &sy);
	ED_space_clip_get_size(sc, &width, &height);
	ED_space_clip_get_zoom(sc, ar, &zoomx, &zoomy);

	ED_clip_point_undistorted_pos(sc, co, pos);
	pos[2] = 0.0f;

	/* untested */
	mul_v3_m4v3(pos, sc->stabmat, pos);

	r_co[0] = (pos[0] * width  * zoomx) + (float)sx;
	r_co[1] = (pos[1] * height * zoomy) + (float)sy;
}

/* takes event->mval */
void ED_clip_mouse_pos(SpaceClip *sc, ARegion *ar, const int mval[2], float co[2])
{
	ED_clip_point_stable_pos(sc, ar, mval[0], mval[1], &co[0], &co[1]);
}

int ED_space_clip_check_show_trackedit(SpaceClip *sc)
{
	if (sc) {
		return ELEM3(sc->mode, SC_MODE_TRACKING, SC_MODE_RECONSTRUCTION, SC_MODE_DISTORTION);
	}

	return FALSE;
}

int ED_space_clip_check_show_maskedit(SpaceClip *sc)
{
	if (sc) {
		return sc->mode == SC_MODE_MASKEDIT;
	}

	return FALSE;
}

/* ******** clip editing functions ******** */

MovieClip *ED_space_clip_get_clip(SpaceClip *sc)
{
	return sc->clip;
}

void ED_space_clip_set_clip(bContext *C, bScreen *screen, SpaceClip *sc, MovieClip *clip)
{
	MovieClip *old_clip;

	if (!screen && C)
		screen = CTX_wm_screen(C);

	old_clip = sc->clip;
	sc->clip = clip;

	if (sc->clip && sc->clip->id.us == 0)
		sc->clip->id.us = 1;

	if (screen && sc->view == SC_VIEW_CLIP) {
		ScrArea *area;
		SpaceLink *sl;

		for (area = screen->areabase.first; area; area = area->next) {
			for (sl = area->spacedata.first; sl; sl = sl->next) {
				if (sl->spacetype == SPACE_CLIP) {
					SpaceClip *cur_sc = (SpaceClip *) sl;

					if (cur_sc != sc && cur_sc->view != SC_VIEW_CLIP) {
						if (cur_sc->clip == old_clip || cur_sc->clip == NULL) {
							cur_sc->clip = clip;
						}
					}
				}
			}
		}
	}

	if (C)
		WM_event_add_notifier(C, NC_MOVIECLIP | NA_SELECTED, sc->clip);
}

/* ******** masking editing functions ******** */

Mask *ED_space_clip_get_mask(SpaceClip *sc)
{
	return sc->mask_info.mask;
}

void ED_space_clip_set_mask(bContext *C, SpaceClip *sc, Mask *mask)
{
	sc->mask_info.mask = mask;

	if (sc->mask_info.mask && sc->mask_info.mask->id.us == 0) {
		sc->mask_info.mask->id.us = 1;
	}

	if (C) {
		WM_event_add_notifier(C, NC_MASK | NA_SELECTED, mask);
	}
}

/* OpenGL draw context */

typedef struct SpaceClipDrawContext {
	int support_checked, buffers_supported;

	GLuint texture;			/* OGL texture ID */
	short texture_allocated;	/* flag if texture was allocated by glGenTextures */
	struct ImBuf *texture_ibuf;	/* image buffer for which texture was created */
	int image_width, image_height;	/* image width and height for which texture was created */
	unsigned last_texture;		/* ID of previously used texture, so it'll be restored after clip drawing */

	/* fields to check if cache is still valid */
	int framenr, start_frame, frame_offset;
	short render_size, render_flag;
} SpaceClipDrawContext;

int ED_space_clip_texture_buffer_supported(SpaceClip *sc)
{
	SpaceClipDrawContext *context = sc->draw_context;

	if (!context) {
		context = MEM_callocN(sizeof(SpaceClipDrawContext), "SpaceClipDrawContext");
		sc->draw_context = context;
	}

	if (!context->support_checked) {
		context->support_checked = TRUE;
		if (GPU_type_matches(GPU_DEVICE_INTEL, GPU_OS_ANY, GPU_DRIVER_ANY)) {
			context->buffers_supported = FALSE;
		}
		else {
			context->buffers_supported = GPU_non_power_of_two_support();
		}
	}

	return context->buffers_supported;
}

int ED_space_clip_load_movieclip_buffer(SpaceClip *sc, ImBuf *ibuf)
{
	SpaceClipDrawContext *context = sc->draw_context;
	MovieClip *clip = ED_space_clip_get_clip(sc);
	int need_rebind = 0;

	context->last_texture = glaGetOneInteger(GL_TEXTURE_2D);

	/* image texture need to be rebinded if displaying another image buffer
	 * assuming displaying happens of footage frames only on which painting doesn't heppen.
	 * so not changed image buffer pointer means unchanged image content */
	need_rebind |= context->texture_ibuf != ibuf;
	need_rebind |= context->framenr != sc->user.framenr;
	need_rebind |= context->render_size != sc->user.render_size;
	need_rebind |= context->render_flag != sc->user.render_flag;
	need_rebind |= context->start_frame != clip->start_frame;
	need_rebind |= context->frame_offset != clip->frame_offset;

	if (need_rebind) {
		int width = ibuf->x, height = ibuf->y;
		int need_recreate = 0;

		if (width > GL_MAX_TEXTURE_SIZE || height > GL_MAX_TEXTURE_SIZE)
			return 0;

		/* if image resolution changed (e.g. switched to proxy display) texture need to be recreated */
		need_recreate = context->image_width != ibuf->x || context->image_height != ibuf->y;

		if (context->texture_ibuf && need_recreate) {
			glDeleteTextures(1, &context->texture);
			context->texture_allocated = 0;
		}

		if (need_recreate || !context->texture_allocated) {
			/* texture doesn't exist yet or need to be re-allocated because of changed dimensions */
			int filter = GL_LINEAR;

			/* non-scaled proxy shouldn;t use diltering */
			if ((clip->flag & MCLIP_USE_PROXY) == 0 ||
			    ELEM(sc->user.render_size, MCLIP_PROXY_RENDER_SIZE_FULL, MCLIP_PROXY_RENDER_SIZE_100))
			{
				filter = GL_NEAREST;
			}

			glGenTextures(1, &context->texture);
			glBindTexture(GL_TEXTURE_2D, context->texture);
			glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, filter);
			glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, filter);
			glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP);
			glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP);
		}
		else {
			/* if texture doesn't need to be reallocated itself, just bind it so
			 * loading of image will happen to a proper texture */
			glBindTexture(GL_TEXTURE_2D, context->texture);
		}

		if (ibuf->rect_float) {
			if (ibuf->rect == NULL)
				IMB_rect_from_float(ibuf);
		}

		if (ibuf->rect)
			glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA8, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, ibuf->rect);

		/* store settings */
		context->texture_allocated = 1;
		context->texture_ibuf = ibuf;
		context->image_width = ibuf->x;
		context->image_height = ibuf->y;
		context->framenr = sc->user.framenr;
		context->render_size = sc->user.render_size;
		context->render_flag = sc->user.render_flag;
		context->start_frame = clip->start_frame;
		context->frame_offset = clip->frame_offset;
	}
	else {
		/* displaying exactly the same image which was loaded t oa texture,
		 * just bint texture in this case */
		glBindTexture(GL_TEXTURE_2D, context->texture);
	}

	glEnable(GL_TEXTURE_2D);

	return TRUE;
}

void ED_space_clip_unload_movieclip_buffer(SpaceClip *sc)
{
	SpaceClipDrawContext *context = sc->draw_context;

	glBindTexture(GL_TEXTURE_2D, context->last_texture);
	glDisable(GL_TEXTURE_2D);
}

void ED_space_clip_free_texture_buffer(SpaceClip *sc)
{
	SpaceClipDrawContext *context = sc->draw_context;

	if (context) {
		glDeleteTextures(1, &context->texture);

		MEM_freeN(context);
	}
}

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

/** \file blender/editors/space_clip/clip_buttons.c
 *  \ingroup spclip
 */

#include <string.h>
#include <stdio.h>

#include "MEM_guardedalloc.h"

#include "DNA_scene_types.h"
#include "DNA_screen_types.h"
#include "DNA_space_types.h"

#include "BLI_math.h"
#include "BLI_utildefines.h"
#include "BLI_listbase.h"
#include "BLI_rect.h"

#include "BLF_translation.h"

#include "BKE_context.h"
#include "BKE_depsgraph.h"
#include "BKE_screen.h"
#include "BKE_movieclip.h"
#include "BKE_tracking.h"

#include "ED_clip.h"
#include "ED_gpencil.h"

#include "UI_interface.h"
#include "UI_resources.h"

#include "RNA_access.h"

#include "WM_api.h"
#include "WM_types.h"

#include "clip_intern.h"  /* own include */

/* Panels */

static int clip_grease_pencil_panel_poll(const bContext *C, PanelType *UNUSED(pt))
{
	SpaceClip *sc = CTX_wm_space_clip(C);

	return sc->view == SC_VIEW_CLIP;
}

void ED_clip_buttons_register(ARegionType *art)
{
	PanelType *pt;

	pt = MEM_callocN(sizeof(PanelType), "spacetype clip panel gpencil");
	strcpy(pt->idname, "CLIP_PT_gpencil");
	strcpy(pt->label, "Grease Pencil");
	pt->draw_header = gpencil_panel_standard_header;
	pt->draw = gpencil_panel_standard;
	pt->flag |= PNL_DEFAULT_CLOSED;
	pt->poll = clip_grease_pencil_panel_poll;
	BLI_addtail(&art->paneltypes, pt);
}

/********************* MovieClip Template ************************/

void uiTemplateMovieClip(uiLayout *layout, bContext *C, PointerRNA *ptr, const char *propname, int compact)
{
	PropertyRNA *prop;
	PointerRNA clipptr;
	MovieClip *clip;
	uiLayout *row, *split;
	uiBlock *block;

	if (!ptr->data)
		return;

	prop = RNA_struct_find_property(ptr, propname);
	if (!prop) {
		printf("%s: property not found: %s.%s\n",
		       __func__, RNA_struct_identifier(ptr->type), propname);
		return;
	}

	if (RNA_property_type(prop) != PROP_POINTER) {
		printf("%s: expected pointer property for %s.%s\n",
		       __func__, RNA_struct_identifier(ptr->type), propname);
		return;
	}

	clipptr = RNA_property_pointer_get(ptr, prop);
	clip = clipptr.data;

	uiLayoutSetContextPointer(layout, "edit_movieclip", &clipptr);

	if (!compact)
		uiTemplateID(layout, C, ptr, propname, NULL, "CLIP_OT_open", NULL);

	if (clip) {
		uiLayout *col;

		row = uiLayoutRow(layout, FALSE);
		block = uiLayoutGetBlock(row);
		uiDefBut(block, LABEL, 0, IFACE_("File Path:"), 0, 19, 145, 19, NULL, 0, 0, 0, 0, "");

		row = uiLayoutRow(layout, FALSE);
		split = uiLayoutSplit(row, 0.0f, FALSE);
		row = uiLayoutRow(split, TRUE);

		uiItemR(row, &clipptr, "filepath", 0, "", ICON_NONE);
		uiItemO(row, "", ICON_FILE_REFRESH, "clip.reload");

		col = uiLayoutColumn(layout, FALSE);
		uiTemplateColorspaceSettings(col, &clipptr, "colorspace_settings");
	}
}

/********************* Track Template ************************/

void uiTemplateTrack(uiLayout *layout, PointerRNA *ptr, const char *propname)
{
	PropertyRNA *prop;
	PointerRNA scopesptr;
	uiBlock *block;
	rctf rect;
	MovieClipScopes *scopes;

	if (!ptr->data)
		return;

	prop = RNA_struct_find_property(ptr, propname);
	if (!prop) {
		printf("%s: property not found: %s.%s\n",
		       __func__, RNA_struct_identifier(ptr->type), propname);
		return;
	}

	if (RNA_property_type(prop) != PROP_POINTER) {
		printf("%s: expected pointer property for %s.%s\n",
		       __func__, RNA_struct_identifier(ptr->type), propname);
		return;
	}

	scopesptr = RNA_property_pointer_get(ptr, prop);
	scopes = (MovieClipScopes *)scopesptr.data;

	rect.xmin = 0; rect.xmax = 10.0f * UI_UNIT_X;
	rect.ymin = 0; rect.ymax = 6.0f * UI_UNIT_Y;

	block = uiLayoutAbsoluteBlock(layout);

	scopes->track_preview_height =
		(scopes->track_preview_height <= 20) ? 20 : scopes->track_preview_height;

	uiDefBut(block, TRACKPREVIEW, 0, "", rect.xmin, rect.ymin, BLI_rctf_size_x(&rect),
	         scopes->track_preview_height * UI_DPI_FAC, scopes, 0, 0, 0, 0, "");
}

/********************* Marker Template ************************/

#define B_MARKER_POS            3
#define B_MARKER_OFFSET         4
#define B_MARKER_PAT_DIM        5
#define B_MARKER_SEARCH_POS     6
#define B_MARKER_SEARCH_DIM     7
#define B_MARKER_FLAG           8

typedef struct {
	int compact;                                /* compact mode */

	MovieClip *clip;
	MovieClipUser *user;                        /* user of clip */
	MovieTrackingTrack *track;
	MovieTrackingMarker *marker;

	int framenr;                                    /* current frame number */
	float marker_pos[2];                            /* position of marker in pixel coords */
	float marker_pat[2];                            /* position and dimensions of marker pattern in pixel coords */
	float track_offset[2];                          /* offset of "parenting" point */
	float marker_search_pos[2], marker_search[2];   /* position and dimensions of marker search in pixel coords */
	int marker_flag;                                /* marker's flags */
} MarkerUpdateCb;

static void to_pixel_space(float r[2], float a[2], int width, int height)
{
	copy_v2_v2(r, a);
	r[0] *= width;
	r[1] *= height;
}

static void marker_update_cb(bContext *C, void *arg_cb, void *UNUSED(arg))
{
	MarkerUpdateCb *cb = (MarkerUpdateCb *) arg_cb;
	MovieTrackingMarker *marker;

	if (!cb->compact)
		return;

	marker = BKE_tracking_marker_ensure(cb->track, cb->framenr);

	marker->flag = cb->marker_flag;

	WM_event_add_notifier(C, NC_MOVIECLIP | NA_EDITED, NULL);
}

static void marker_block_handler(bContext *C, void *arg_cb, int event)
{
	MarkerUpdateCb *cb = (MarkerUpdateCb *) arg_cb;
	MovieTrackingMarker *marker;
	int width, height, ok = FALSE;

	BKE_movieclip_get_size(cb->clip, cb->user, &width, &height);

	marker = BKE_tracking_marker_ensure(cb->track, cb->framenr);

	if (event == B_MARKER_POS) {
		marker->pos[0] = cb->marker_pos[0] / width;
		marker->pos[1] = cb->marker_pos[1] / height;

		/* to update position of "parented" objects */
		DAG_id_tag_update(&cb->clip->id, 0);
		WM_event_add_notifier(C, NC_SPACE | ND_SPACE_VIEW3D, NULL);

		ok = TRUE;
	}
	else if (event == B_MARKER_PAT_DIM) {
		float dim[2], pat_dim[2], pat_min[2], pat_max[2];
		float scale_x, scale_y;
		int a;

		BKE_tracking_marker_pattern_minmax(cb->marker, pat_min, pat_max);

		sub_v2_v2v2(pat_dim, pat_max, pat_min);

		dim[0] = cb->marker_pat[0] / width;
		dim[1] = cb->marker_pat[1] / height;

		scale_x = dim[0] / pat_dim[0];
		scale_y = dim[1] / pat_dim[1];

		for (a = 0; a < 4; a++) {
			cb->marker->pattern_corners[a][0] *= scale_x;
			cb->marker->pattern_corners[a][1] *= scale_y;
		}

		BKE_tracking_marker_clamp(cb->marker, CLAMP_PAT_DIM);

		ok = TRUE;
	}
	else if (event == B_MARKER_SEARCH_POS) {
		float delta[2], side[2];

		sub_v2_v2v2(side, cb->marker->search_max, cb->marker->search_min);
		mul_v2_fl(side, 0.5f);

		delta[0] = cb->marker_search_pos[0] / width;
		delta[1] = cb->marker_search_pos[1] / height;

		sub_v2_v2v2(cb->marker->search_min, delta, side);
		add_v2_v2v2(cb->marker->search_max, delta, side);

		BKE_tracking_marker_clamp(cb->marker, CLAMP_SEARCH_POS);

		ok = TRUE;
	}
	else if (event == B_MARKER_SEARCH_DIM) {
		float dim[2], search_dim[2];

		sub_v2_v2v2(search_dim, cb->marker->search_max, cb->marker->search_min);

		dim[0] = cb->marker_search[0] / width;
		dim[1] = cb->marker_search[1] / height;

		sub_v2_v2(dim, search_dim);
		mul_v2_fl(dim, 0.5f);

		cb->marker->search_min[0] -= dim[0];
		cb->marker->search_min[1] -= dim[1];

		cb->marker->search_max[0] += dim[0];
		cb->marker->search_max[1] += dim[1];

		BKE_tracking_marker_clamp(cb->marker, CLAMP_SEARCH_DIM);

		ok = TRUE;
	}
	else if (event == B_MARKER_FLAG) {
		marker->flag = cb->marker_flag;

		ok = TRUE;
	}
	else if (event == B_MARKER_OFFSET) {
		float offset[2], delta[2];
		int i;

		offset[0] = cb->track_offset[0] / width;
		offset[1] = cb->track_offset[1] / height;

		sub_v2_v2v2(delta, offset, cb->track->offset);
		copy_v2_v2(cb->track->offset, offset);

		for (i = 0; i < cb->track->markersnr; i++)
			sub_v2_v2(cb->track->markers[i].pos, delta);

		/* to update position of "parented" objects */
		DAG_id_tag_update(&cb->clip->id, 0);
		WM_event_add_notifier(C, NC_SPACE | ND_SPACE_VIEW3D, NULL);

		ok = TRUE;
	}

	if (ok)
		WM_event_add_notifier(C, NC_MOVIECLIP | NA_EDITED, cb->clip);
}

void uiTemplateMarker(uiLayout *layout, PointerRNA *ptr, const char *propname, PointerRNA *userptr,
                      PointerRNA *trackptr, int compact)
{
	PropertyRNA *prop;
	uiBlock *block;
	uiBut *bt;
	PointerRNA clipptr;
	MovieClip *clip;
	MovieClipUser *user;
	MovieTrackingTrack *track;
	MovieTrackingMarker *marker;
	MarkerUpdateCb *cb;
	const char *tip;
	float pat_min[2], pat_max[2];

	if (!ptr->data)
		return;

	prop = RNA_struct_find_property(ptr, propname);
	if (!prop) {
		printf("%s: property not found: %s.%s\n",
		       __func__, RNA_struct_identifier(ptr->type), propname);
		return;
	}

	if (RNA_property_type(prop) != PROP_POINTER) {
		printf("%s: expected pointer property for %s.%s\n",
		       __func__, RNA_struct_identifier(ptr->type), propname);
		return;
	}

	clipptr = RNA_property_pointer_get(ptr, prop);
	clip = (MovieClip *)clipptr.data;
	user = userptr->data;
	track = trackptr->data;

	marker = BKE_tracking_marker_get(track, user->framenr);

	cb = MEM_callocN(sizeof(MarkerUpdateCb), "uiTemplateMarker update_cb");
	cb->compact = compact;
	cb->clip = clip;
	cb->user = user;
	cb->track = track;
	cb->marker = marker;
	cb->marker_flag = marker->flag;
	cb->framenr = user->framenr;

	if (compact) {
		block = uiLayoutGetBlock(layout);

		if (cb->marker_flag & MARKER_DISABLED)
			tip = TIP_("Marker is disabled at current frame");
		else
			tip = TIP_("Marker is enabled at current frame");

		bt = uiDefIconButBitI(block, TOGN, MARKER_DISABLED, 0, ICON_RESTRICT_VIEW_OFF, 0, 0, UI_UNIT_X, UI_UNIT_Y,
		                      &cb->marker_flag, 0, 0, 1, 0, tip);
		uiButSetNFunc(bt, marker_update_cb, cb, NULL);
	}
	else {
		int width, height, step, digits;
		float pat_dim[2], search_dim[2], search_pos[2];
		uiLayout *col;

		BKE_movieclip_get_size(clip, user, &width, &height);

		if (track->flag & TRACK_LOCKED) {
			uiLayoutSetActive(layout, FALSE);
			block = uiLayoutAbsoluteBlock(layout);
			uiDefBut(block, LABEL, 0, IFACE_("Track is locked"), 0, 0, UI_UNIT_X * 15.0f, UI_UNIT_Y, NULL, 0, 0, 0, 0, "");

			return;
		}

		step = 100;
		digits = 2;

		BKE_tracking_marker_pattern_minmax(marker, pat_min, pat_max);

		sub_v2_v2v2(pat_dim, pat_max, pat_min);
		sub_v2_v2v2(search_dim, marker->search_max, marker->search_min);

		add_v2_v2v2(search_pos, marker->search_max, marker->search_min);
		mul_v2_fl(search_pos, 0.5);

		to_pixel_space(cb->marker_pos, marker->pos, width, height);
		to_pixel_space(cb->marker_pat, pat_dim, width, height);
		to_pixel_space(cb->marker_search, search_dim, width, height);
		to_pixel_space(cb->marker_search_pos, search_pos, width, height);
		to_pixel_space(cb->track_offset, track->offset, width, height);

		cb->marker_flag = marker->flag;

		block = uiLayoutAbsoluteBlock(layout);
		uiBlockSetHandleFunc(block, marker_block_handler, cb);
		uiBlockSetNFunc(block, marker_update_cb, cb, NULL);

		if (cb->marker_flag & MARKER_DISABLED)
			tip = TIP_("Marker is disabled at current frame");
		else
			tip = TIP_("Marker is enabled at current frame");

		uiDefButBitI(block, OPTIONN, MARKER_DISABLED, B_MARKER_FLAG, IFACE_("Enabled"), 10, 190, 145, 19,
		             &cb->marker_flag, 0, 0, 0, 0, tip);

		col = uiLayoutColumn(layout, TRUE);
		uiLayoutSetActive(col, (cb->marker_flag & MARKER_DISABLED) == 0);

		block = uiLayoutAbsoluteBlock(col);
		uiBlockBeginAlign(block);

		uiDefBut(block, LABEL, 0, IFACE_("Position:"), 0, 190, 300, 19, NULL, 0, 0, 0, 0, "");
		uiDefButF(block, NUM, B_MARKER_POS, IFACE_("X:"), 10, 171, 145, 19, &cb->marker_pos[0],
		          -10 * width, 10.0 * width, step, digits, TIP_("X-position of marker at frame in screen coordinates"));
		uiDefButF(block, NUM, B_MARKER_POS, IFACE_("Y:"), 165, 171, 145, 19, &cb->marker_pos[1],
		          -10 * height, 10.0 * height, step, digits,
		          TIP_("Y-position of marker at frame in screen coordinates"));

		uiDefBut(block, LABEL, 0, IFACE_("Offset:"), 0, 152, 300, 19, NULL, 0, 0, 0, 0, "");
		uiDefButF(block, NUM, B_MARKER_OFFSET, IFACE_("X:"), 10, 133, 145, 19, &cb->track_offset[0],
		          -10 * width, 10.0 * width, step, digits, TIP_("X-offset to parenting point"));
		uiDefButF(block, NUM, B_MARKER_OFFSET, IFACE_("Y:"), 165, 133, 145, 19, &cb->track_offset[1],
		          -10 * height, 10.0 * height, step, digits, TIP_("Y-offset to parenting point"));

		uiDefBut(block, LABEL, 0, IFACE_("Pattern Area:"), 0, 114, 300, 19, NULL, 0, 0, 0, 0, "");
		uiDefButF(block, NUM, B_MARKER_PAT_DIM, IFACE_("Width:"), 10, 95, 300, 19, &cb->marker_pat[0], 3.0f,
		          10.0 * width, step, digits, TIP_("Width of marker's pattern in screen coordinates"));
		uiDefButF(block, NUM, B_MARKER_PAT_DIM, IFACE_("Height:"), 10, 76, 300, 19, &cb->marker_pat[1], 3.0f,
		          10.0 * height, step, digits, TIP_("Height of marker's pattern in screen coordinates"));

		uiDefBut(block, LABEL, 0, IFACE_("Search Area:"), 0, 57, 300, 19, NULL, 0, 0, 0, 0, "");
		uiDefButF(block, NUM, B_MARKER_SEARCH_POS, IFACE_("X:"), 10, 38, 145, 19, &cb->marker_search_pos[0],
		          -width, width, step, digits, TIP_("X-position of search at frame relative to marker's position"));
		uiDefButF(block, NUM, B_MARKER_SEARCH_POS, IFACE_("Y:"), 165, 38, 145, 19, &cb->marker_search_pos[1],
		          -height, height, step, digits, TIP_("Y-position of search at frame relative to marker's position"));
		uiDefButF(block, NUM, B_MARKER_SEARCH_DIM, IFACE_("Width:"), 10, 19, 300, 19, &cb->marker_search[0], 3.0f,
		          10.0 * width, step, digits, TIP_("Width of marker's search in screen coordinates"));
		uiDefButF(block, NUM, B_MARKER_SEARCH_DIM, IFACE_("Height:"), 10, 0, 300, 19, &cb->marker_search[1], 3.0f,
		          10.0 * height, step, digits, TIP_("Height of marker's search in screen coordinates"));

		uiBlockEndAlign(block);
	}
}

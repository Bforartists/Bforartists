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
 * The Original Code is Copyright (C) 2011 Blender Foundation.
 * All rights reserved.
 *
 *
 * Contributor(s): Blender Foundation,
 *                 Sergey Sharybin
 *
 * ***** END GPL LICENSE BLOCK *****
 */

/** \file blender/editors/space_clip/space_clip.c
 *  \ingroup spclip
 */

#include <string.h>
#include <stdio.h>

#include "DNA_scene_types.h"
#include "DNA_movieclip_types.h"

#include "MEM_guardedalloc.h"

#include "BLI_blenlib.h"
#include "BLI_utildefines.h"

#include "BKE_main.h"
#include "BKE_context.h"
#include "BKE_screen.h"
#include "BKE_movieclip.h"
#include "BKE_tracking.h"

#include "IMB_imbuf_types.h"

#include "ED_screen.h"
#include "ED_clip.h"
#include "ED_transform.h"

#include "IMB_imbuf.h"

#include "BIF_gl.h"

#include "WM_api.h"
#include "WM_types.h"

#include "UI_interface.h"
#include "UI_resources.h"
#include "UI_view2d.h"

#include "RNA_access.h"


#include "clip_intern.h"	// own include

static void clip_scopes_tag_refresh(ScrArea *sa)
{
	SpaceClip *sc= (SpaceClip *)sa->spacedata.first;
	ARegion *ar;

	/* only while proeprties are visible */
	for (ar=sa->regionbase.first; ar; ar=ar->next) {
		if (ar->regiontype == RGN_TYPE_UI && ar->flag & RGN_FLAG_HIDDEN)
			return;
	}

	sc->scopes.ok= 0;
}

static void clip_stabilization_tag_refresh(ScrArea *sa)
{
	SpaceClip *sc= (SpaceClip *)sa->spacedata.first;
	MovieClip *clip= ED_space_clip(sc);

	if(clip) {
		MovieTrackingStabilization *stab= &clip->tracking.stabilization;

		stab->ok= 0;
	}
}

/* ******************** default callbacks for clip space ***************** */

static SpaceLink *clip_new(const bContext *UNUSED(C))
{
	ARegion *ar;
	SpaceClip *sc;

	sc= MEM_callocN(sizeof(SpaceClip), "initclip");
	sc->spacetype= SPACE_CLIP;
	sc->flag= SC_SHOW_MARKER_PATTERN|SC_SHOW_TRACK_PATH;
	sc->zoom= 1.0f;
	sc->path_length= 20;
	sc->scopes.track_preview_height= 120;

	/* header */
	ar= MEM_callocN(sizeof(ARegion), "header for clip");

	BLI_addtail(&sc->regionbase, ar);
	ar->regiontype= RGN_TYPE_HEADER;
	ar->alignment= RGN_ALIGN_BOTTOM;

	/* tools view */
	ar= MEM_callocN(sizeof(ARegion), "tools for logic");

	BLI_addtail(&sc->regionbase, ar);
	ar->regiontype= RGN_TYPE_TOOLS;
	ar->alignment= RGN_ALIGN_LEFT;

	/* tool properties */
	ar= MEM_callocN(sizeof(ARegion), "tool properties for clip");

	BLI_addtail(&sc->regionbase, ar);
	ar->regiontype= RGN_TYPE_TOOL_PROPS;
	ar->alignment= RGN_ALIGN_BOTTOM|RGN_SPLIT_PREV;

	/* properties view */
	ar= MEM_callocN(sizeof(ARegion), "properties for logic");

	BLI_addtail(&sc->regionbase, ar);
	ar->regiontype= RGN_TYPE_UI;
	ar->alignment= RGN_ALIGN_RIGHT;

	/* main area */
	ar= MEM_callocN(sizeof(ARegion), "main area for clip");

	BLI_addtail(&sc->regionbase, ar);
	ar->regiontype= RGN_TYPE_WINDOW;

	return (SpaceLink *)sc;
}

/* not spacelink itself */
static void clip_free(SpaceLink *sl)
{
	SpaceClip *sc= (SpaceClip*) sl;

	sc->clip= NULL;

	if(sc->scopes.track_preview)
		IMB_freeImBuf(sc->scopes.track_preview);
}

/* spacetype; init callback */
static void clip_init(struct wmWindowManager *UNUSED(wm), ScrArea *UNUSED(sa))
{

}

static SpaceLink *clip_duplicate(SpaceLink *sl)
{
	SpaceClip *scn= MEM_dupallocN(sl);

	/* clear or remove stuff from old */
	scn->scopes.track_preview= NULL;
	scn->scopes.ok= 0;

	return (SpaceLink *)scn;
}

static void clip_listener(ScrArea *sa, wmNotifier *wmn)
{
	/* context changes */
	switch(wmn->category) {
		case NC_SCENE:
			switch(wmn->data) {
				case ND_FRAME:
					clip_scopes_tag_refresh(sa);
					/* no break! */

				case ND_FRAME_RANGE:
					ED_area_tag_refresh(sa);
					ED_area_tag_redraw(sa);
					break;
			}
			break;
		case NC_MOVIECLIP:
			switch(wmn->data) {
				case ND_DISPLAY:
				case ND_SELECT:
					clip_scopes_tag_refresh(sa);
					ED_area_tag_redraw(sa);
					break;
			}
			switch(wmn->action) {
				case NA_REMOVED:
				case NA_EDITED:
				case NA_EVALUATED:
					clip_stabilization_tag_refresh(sa);
					/* no break! */

				case NA_SELECTED:
					clip_scopes_tag_refresh(sa);
					ED_area_tag_redraw(sa);
					break;
			}
			break;
		case NC_GEOM:
			switch(wmn->data) {
				case ND_SELECT:
					clip_scopes_tag_refresh(sa);
					ED_area_tag_redraw(sa);
					break;
			}
			break;
		 case NC_SCREEN:
			if(wmn->data==ND_ANIMPLAY) {
				ED_area_tag_redraw(sa);
			}
			break;
		case NC_SPACE:
			if(wmn->data==ND_SPACE_CLIP) {
				clip_scopes_tag_refresh(sa);
				clip_stabilization_tag_refresh(sa);
				ED_area_tag_redraw(sa);
			}
			break;
	}
}

static void clip_operatortypes(void)
{
	WM_operatortype_append(CLIP_OT_open);
	WM_operatortype_append(CLIP_OT_reload);
	WM_operatortype_append(CLIP_OT_tools);
	 WM_operatortype_append(CLIP_OT_properties);
	// WM_operatortype_append(CLIP_OT_unlink);
	WM_operatortype_append(CLIP_OT_view_pan);
	WM_operatortype_append(CLIP_OT_view_zoom);
	WM_operatortype_append(CLIP_OT_view_zoom_in);
	WM_operatortype_append(CLIP_OT_view_zoom_out);
	WM_operatortype_append(CLIP_OT_view_zoom_ratio);
	WM_operatortype_append(CLIP_OT_view_all);
	WM_operatortype_append(CLIP_OT_view_selected);
	WM_operatortype_append(CLIP_OT_change_frame);

	WM_operatortype_append(CLIP_OT_select);
	WM_operatortype_append(CLIP_OT_select_all);
	WM_operatortype_append(CLIP_OT_select_border);
	WM_operatortype_append(CLIP_OT_select_circle);
	WM_operatortype_append(CLIP_OT_select_grouped);

	WM_operatortype_append(CLIP_OT_add_marker);
	WM_operatortype_append(CLIP_OT_delete_track);
	WM_operatortype_append(CLIP_OT_delete_marker);

	WM_operatortype_append(CLIP_OT_track_markers);
	WM_operatortype_append(CLIP_OT_solve_camera);
	WM_operatortype_append(CLIP_OT_clear_reconstruction);

	WM_operatortype_append(CLIP_OT_disable_markers);
	WM_operatortype_append(CLIP_OT_hide_tracks);
	WM_operatortype_append(CLIP_OT_hide_tracks_clear);
	WM_operatortype_append(CLIP_OT_lock_tracks);

	WM_operatortype_append(CLIP_OT_set_origin);
	WM_operatortype_append(CLIP_OT_set_floor);
	WM_operatortype_append(CLIP_OT_set_axis);
	WM_operatortype_append(CLIP_OT_set_scale);

	WM_operatortype_append(CLIP_OT_set_center_principal);

	WM_operatortype_append(CLIP_OT_clear_track_path);
	WM_operatortype_append(CLIP_OT_join_tracks);
	WM_operatortype_append(CLIP_OT_track_copy_color);

	WM_operatortype_append(CLIP_OT_slide_marker);

	WM_operatortype_append(CLIP_OT_frame_jump);

	WM_operatortype_append(CLIP_OT_detect_features);

	WM_operatortype_append(CLIP_OT_stabilize_2d_add);
	WM_operatortype_append(CLIP_OT_stabilize_2d_remove);
	WM_operatortype_append(CLIP_OT_stabilize_2d_select);

	WM_operatortype_append(CLIP_OT_clean_tracks);
}

static void clip_keymap(struct wmKeyConfig *keyconf)
{
	wmKeyMap *keymap;
	wmKeyMapItem *kmi;

	/* ******** Global hotkeys avalaible for all regions ******** */

	keymap= WM_keymap_find(keyconf, "Clip Globals", SPACE_CLIP, 0);

	WM_keymap_add_item(keymap, "CLIP_OT_open", OKEY, KM_PRESS, KM_ALT, 0);

	WM_keymap_add_item(keymap, "CLIP_OT_tools", TKEY, KM_PRESS, 0, 0);
	WM_keymap_add_item(keymap, "CLIP_OT_properties", NKEY, KM_PRESS, 0, 0);

	kmi= WM_keymap_add_item(keymap, "CLIP_OT_track_markers", LEFTARROWKEY, KM_PRESS, KM_ALT, 0);
	RNA_boolean_set(kmi->ptr, "backwards", 1);
	WM_keymap_add_item(keymap, "CLIP_OT_track_markers", RIGHTARROWKEY, KM_PRESS, KM_ALT, 0);
	kmi= WM_keymap_add_item(keymap, "CLIP_OT_track_markers", TKEY, KM_PRESS, KM_CTRL, 0);
	RNA_boolean_set(kmi->ptr, "sequence", 1);
	kmi= WM_keymap_add_item(keymap, "CLIP_OT_track_markers", TKEY, KM_PRESS, KM_SHIFT|KM_CTRL, 0);
	RNA_boolean_set(kmi->ptr, "backwards", 1);
	RNA_boolean_set(kmi->ptr, "sequence", 1);

	/* ******** Hotkeys avalaible for main region only ******** */

	keymap= WM_keymap_find(keyconf, "Clip Editor", SPACE_CLIP, 0);

	/* View/navigation */

	WM_keymap_add_item(keymap, "CLIP_OT_view_pan", MIDDLEMOUSE, KM_PRESS, 0, 0);
	WM_keymap_add_item(keymap, "CLIP_OT_view_pan", MIDDLEMOUSE, KM_PRESS, KM_SHIFT, 0);
	WM_keymap_add_item(keymap, "CLIP_OT_view_pan", MOUSEPAN, 0, 0, 0);

	WM_keymap_add_item(keymap, "CLIP_OT_view_zoom", MIDDLEMOUSE, KM_PRESS, KM_CTRL, 0);
	WM_keymap_add_item(keymap, "CLIP_OT_view_zoom", MOUSEZOOM, 0, 0, 0);
	WM_keymap_add_item(keymap, "CLIP_OT_view_zoom_in", WHEELINMOUSE, KM_PRESS, 0, 0);
	WM_keymap_add_item(keymap, "CLIP_OT_view_zoom_out", WHEELOUTMOUSE, KM_PRESS, 0, 0);
	WM_keymap_add_item(keymap, "CLIP_OT_view_zoom_in", PADPLUSKEY, KM_PRESS, 0, 0);
	WM_keymap_add_item(keymap, "CLIP_OT_view_zoom_out", PADMINUS, KM_PRESS, 0, 0);

	RNA_float_set(WM_keymap_add_item(keymap, "CLIP_OT_view_zoom_ratio", PAD8, KM_PRESS, KM_SHIFT, 0)->ptr, "ratio", 8.0f);
	RNA_float_set(WM_keymap_add_item(keymap, "CLIP_OT_view_zoom_ratio", PAD4, KM_PRESS, KM_SHIFT, 0)->ptr, "ratio", 4.0f);
	RNA_float_set(WM_keymap_add_item(keymap, "CLIP_OT_view_zoom_ratio", PAD2, KM_PRESS, KM_SHIFT, 0)->ptr, "ratio", 2.0f);
	RNA_float_set(WM_keymap_add_item(keymap, "CLIP_OT_view_zoom_ratio", PAD1, KM_PRESS, 0, 0)->ptr, "ratio", 1.0f);
	RNA_float_set(WM_keymap_add_item(keymap, "CLIP_OT_view_zoom_ratio", PAD2, KM_PRESS, 0, 0)->ptr, "ratio", 0.5f);
	RNA_float_set(WM_keymap_add_item(keymap, "CLIP_OT_view_zoom_ratio", PAD4, KM_PRESS, 0, 0)->ptr, "ratio", 0.25f);
	RNA_float_set(WM_keymap_add_item(keymap, "CLIP_OT_view_zoom_ratio", PAD8, KM_PRESS, 0, 0)->ptr, "ratio", 0.125f);

	WM_keymap_add_item(keymap, "CLIP_OT_view_all", HOMEKEY, KM_PRESS, 0, 0);

	WM_keymap_add_item(keymap, "CLIP_OT_view_selected", PADPERIOD, KM_PRESS, 0, 0);

	WM_keymap_add_item(keymap, "CLIP_OT_select", SELECTMOUSE, KM_PRESS, 0, 0);
	RNA_boolean_set(WM_keymap_add_item(keymap, "CLIP_OT_select", SELECTMOUSE, KM_PRESS, KM_SHIFT, 0)->ptr, "extend", 1);
	WM_keymap_add_item(keymap, "CLIP_OT_select_all", AKEY, KM_PRESS, 0, 0);
	RNA_enum_set(WM_keymap_add_item(keymap, "CLIP_OT_select_all", IKEY, KM_PRESS, KM_CTRL, 0)->ptr, "action", SEL_INVERT);
	WM_keymap_add_item(keymap, "CLIP_OT_select_border", BKEY, KM_PRESS, 0, 0);
	WM_keymap_add_item(keymap, "CLIP_OT_select_circle", CKEY, KM_PRESS, 0, 0);
	WM_keymap_add_menu(keymap, "CLIP_MT_select_grouped", GKEY, KM_PRESS, KM_SHIFT, 0);

	WM_keymap_add_item(keymap, "CLIP_OT_add_marker_slide", LEFTMOUSE, KM_PRESS, KM_CTRL, 0);

	kmi= WM_keymap_add_item(keymap, "CLIP_OT_clear_track_path", TKEY, KM_PRESS, KM_ALT, 0);
	RNA_enum_set(kmi->ptr, "action", TRACK_CLEAR_REMAINED);
	kmi= WM_keymap_add_item(keymap, "CLIP_OT_clear_track_path", TKEY, KM_PRESS, KM_SHIFT, 0);
	RNA_enum_set(kmi->ptr, "action", TRACK_CLEAR_UPTO);
	kmi= WM_keymap_add_item(keymap, "CLIP_OT_clear_track_path", TKEY, KM_PRESS, KM_ALT|KM_SHIFT, 0);
	RNA_enum_set(kmi->ptr, "action", TRACK_CLEAR_ALL);

	WM_keymap_add_item(keymap, "CLIP_OT_delete_track", DELKEY, KM_PRESS, 0, 0);
	WM_keymap_add_item(keymap, "CLIP_OT_delete_track", XKEY, KM_PRESS, 0, 0);

	WM_keymap_add_item(keymap, "CLIP_OT_delete_marker", DELKEY, KM_PRESS, KM_SHIFT, 0);
	WM_keymap_add_item(keymap, "CLIP_OT_delete_marker", XKEY, KM_PRESS, KM_SHIFT, 0);

	kmi= WM_keymap_add_item(keymap, "WM_OT_context_toggle", LKEY, KM_PRESS, 0, 0);
	RNA_string_set(kmi->ptr, "data_path", "space_data.lock_selection");

	WM_keymap_add_menu(keymap, "CLIP_MT_tracking_specials", WKEY, KM_PRESS, 0, 0);

	WM_keymap_add_item(keymap, "CLIP_OT_slide_marker", LEFTMOUSE, KM_PRESS, 0, 0);

	WM_keymap_add_item(keymap, "CLIP_OT_hide_tracks", HKEY, KM_PRESS, 0, 0);
	kmi= WM_keymap_add_item(keymap, "CLIP_OT_hide_tracks", HKEY, KM_PRESS, KM_SHIFT, 0);
	RNA_boolean_set(kmi->ptr, "unselected", 1);
	WM_keymap_add_item(keymap, "CLIP_OT_hide_tracks_clear", HKEY, KM_PRESS, KM_ALT, 0);

	kmi= WM_keymap_add_item(keymap, "CLIP_OT_disable_markers", DKEY, KM_PRESS, 0, 0);
	RNA_enum_set(kmi->ptr, "action", 2);

	kmi= WM_keymap_add_item(keymap, "CLIP_OT_lock_tracks", LKEY, KM_PRESS, KM_CTRL, 0);
	RNA_enum_set(kmi->ptr, "action", 0);

	kmi= WM_keymap_add_item(keymap, "CLIP_OT_lock_tracks", LKEY, KM_PRESS, KM_ALT, 0);
	RNA_enum_set(kmi->ptr, "action", 1);

	kmi= WM_keymap_add_item(keymap, "CLIP_OT_frame_jump", LEFTARROWKEY, KM_PRESS, KM_CTRL|KM_SHIFT, 0);
	RNA_enum_set(kmi->ptr, "position", 0);

	kmi= WM_keymap_add_item(keymap, "CLIP_OT_frame_jump", RIGHTARROWKEY, KM_PRESS, KM_CTRL|KM_SHIFT, 0);
	RNA_enum_set(kmi->ptr, "position", 1);

	kmi= WM_keymap_add_item(keymap, "CLIP_OT_frame_jump", LEFTARROWKEY, KM_PRESS, KM_ALT|KM_SHIFT, 0);
	RNA_enum_set(kmi->ptr, "position", 2);

	kmi= WM_keymap_add_item(keymap, "CLIP_OT_frame_jump", RIGHTARROWKEY, KM_PRESS, KM_ALT|KM_SHIFT, 0);
	RNA_enum_set(kmi->ptr, "position", 3);

	WM_keymap_add_item(keymap, "CLIP_OT_join_tracks", JKEY, KM_PRESS, KM_CTRL, 0);

	kmi= WM_keymap_add_item(keymap, "WM_OT_context_toggle", MKEY, KM_PRESS, 0, 0);
	RNA_string_set(kmi->ptr, "data_path", "space_data.use_mute_footage");

	WM_keymap_add_item(keymap, "CLIP_OT_change_frame", LEFTMOUSE, KM_PRESS, 0, 0);

	transform_keymap_for_space(keyconf, keymap, SPACE_CLIP);
}

const char *clip_context_dir[]= {"edit_movieclip", NULL};

static int clip_context(const bContext *C, const char *member, bContextDataResult *result)
{
	SpaceClip *sc= CTX_wm_space_clip(C);

	if(CTX_data_dir(member)) {
		CTX_data_dir_set(result, clip_context_dir);
		return 1;
	}
	else if(CTX_data_equals(member, "edit_movieclip")) {
		CTX_data_id_pointer_set(result, &sc->clip->id);
		return 1;
	}

	return 0;
}

static void clip_refresh(const bContext *C, ScrArea *UNUSED(sa))
{
	SpaceClip *sc= CTX_wm_space_clip(C);

	BKE_movieclip_user_set_frame(&sc->user, CTX_data_scene(C)->r.cfra);
}

/********************* main region ********************/

/* sets up the fields of the View2D from zoom and offset */
static void movieclip_main_area_set_view2d(SpaceClip *sc, ARegion *ar)
{
	MovieClip *clip= ED_space_clip(sc);
	float x1, y1, w, h;
	int width, height, winx, winy;

	ED_space_clip_size(sc, &width, &height);

	w= width;
	h= height;

	if(clip)
		h*= clip->aspy/clip->aspx;

	winx= ar->winrct.xmax - ar->winrct.xmin + 1;
	winy= ar->winrct.ymax - ar->winrct.ymin + 1;

	ar->v2d.tot.xmin= 0;
	ar->v2d.tot.ymin= 0;
	ar->v2d.tot.xmax= w;
	ar->v2d.tot.ymax= h;

	ar->v2d.mask.xmin= ar->v2d.mask.ymin= 0;
	ar->v2d.mask.xmax= winx;
	ar->v2d.mask.ymax= winy;

	/* which part of the image space do we see? */
	x1= ar->winrct.xmin+(winx-sc->zoom*w)/2.0f;
	y1= ar->winrct.ymin+(winy-sc->zoom*h)/2.0f;

	x1-= sc->zoom*sc->xof;
	y1-= sc->zoom*sc->yof;

	/* relative display right */
	ar->v2d.cur.xmin= ((ar->winrct.xmin - (float)x1)/sc->zoom);
	ar->v2d.cur.xmax= ar->v2d.cur.xmin + ((float)winx/sc->zoom);

	/* relative display left */
	ar->v2d.cur.ymin= ((ar->winrct.ymin-(float)y1)/sc->zoom);
	ar->v2d.cur.ymax= ar->v2d.cur.ymin + ((float)winy/sc->zoom);

	/* normalize 0.0..1.0 */
	ar->v2d.cur.xmin /= w;
	ar->v2d.cur.xmax /= w;
	ar->v2d.cur.ymin /= h;
	ar->v2d.cur.ymax /= h;
}

/* add handlers, stuff you only do once or on area/region changes */
static void clip_main_area_init(wmWindowManager *wm, ARegion *ar)
{
	wmKeyMap *keymap;

	UI_view2d_region_reinit(&ar->v2d, V2D_COMMONVIEW_STANDARD, ar->winx, ar->winy);

	/* own keymap */
	keymap= WM_keymap_find(wm->defaultconf, "Clip Globals", SPACE_CLIP, 0);
	WM_event_add_keymap_handler_bb(&ar->handlers, keymap, &ar->v2d.mask, &ar->winrct);

	keymap= WM_keymap_find(wm->defaultconf, "Clip Editor", SPACE_CLIP, 0);
	WM_event_add_keymap_handler_bb(&ar->handlers, keymap, &ar->v2d.mask, &ar->winrct);
}

static void clip_main_area_draw(const bContext *C, ARegion *ar)
{
	/* draw entirely, view changes should be handled here */
	SpaceClip *sc= CTX_wm_space_clip(C);
	Scene *scene= CTX_data_scene(C);
	MovieClip *clip= ED_space_clip(sc);

	/* if trcking is in progress, we should sunchronize framenr from clipuser
	   so latest tracked frame would be shown */
	if(clip && clip->tracking_context)
		BKE_tracking_sync_user(&sc->user, clip->tracking_context);

	if(sc->flag&SC_LOCK_SELECTION) {
		ImBuf *tmpibuf= NULL;

		if(clip && clip->tracking.stabilization.flag&TRACKING_2D_STABILIZATION) {
			tmpibuf= ED_space_clip_acquire_stable_buffer(sc, NULL, NULL);
		}

		ED_clip_view_selection(sc, ar, 0);

		if(tmpibuf)
			IMB_freeImBuf(tmpibuf);
	}

	/* clear and setup matrix */
	UI_ThemeClearColor(TH_BACK);
	glClear(GL_COLOR_BUFFER_BIT);

	/* data... */
	movieclip_main_area_set_view2d(sc, ar);
	draw_clip_main(sc, ar, scene);

	/* reset view matrix */
	UI_view2d_view_restore(C);
}

/****************** header region ******************/

/* add handlers, stuff you only do once or on area/region changes */
static void clip_header_area_init(wmWindowManager *UNUSED(wm), ARegion *ar)
{
	ED_region_header_init(ar);
}

static void clip_header_area_draw(const bContext *C, ARegion *ar)
{
	ED_region_header(C, ar);
}

/****************** tools region ******************/

/* add handlers, stuff you only do once or on area/region changes */
static void clip_tools_area_init(wmWindowManager *wm, ARegion *ar)
{
	ED_region_panels_init(wm, ar);
}

static void clip_tools_area_draw(const bContext *C, ARegion *ar)
{
	ED_region_panels(C, ar, 1, NULL, -1);
}

/****************** tool properties region ******************/

static void clip_props_area_listener(ARegion *ar, wmNotifier *wmn)
{
	/* context changes */
	switch(wmn->category) {
		case NC_WM:
			if(wmn->data == ND_HISTORY)
				ED_region_tag_redraw(ar);
			break;
		case NC_SCENE:
			if(wmn->data == ND_MODE)
				ED_region_tag_redraw(ar);
			break;
		case NC_SPACE:
			if(wmn->data == ND_SPACE_VIEW3D)
				ED_region_tag_redraw(ar);
			break;
	}
}

/****************** properties region ******************/

/* add handlers, stuff you only do once or on area/region changes */
static void clip_properties_area_init(wmWindowManager *wm, ARegion *ar)
{
	wmKeyMap *keymap;

	ED_region_panels_init(wm, ar);

	keymap= WM_keymap_find(wm->defaultconf, "Clip Globals", SPACE_CLIP, 0);
	WM_event_add_keymap_handler(&ar->handlers, keymap);
}

static void clip_properties_area_draw(const bContext *C, ARegion *ar)
{
	SpaceClip *sc= CTX_wm_space_clip(C);

	BKE_movieclip_update_scopes(sc->clip, &sc->user, &sc->scopes);

	ED_region_panels(C, ar, 1, NULL, -1);
}

/********************* registration ********************/

/* only called once, from space/spacetypes.c */
void ED_spacetype_clip(void)
{
	SpaceType *st= MEM_callocN(sizeof(SpaceType), "spacetype clip");
	ARegionType *art;

	st->spaceid= SPACE_CLIP;
	strncpy(st->name, "Clip", BKE_ST_MAXNAME);

	st->new= clip_new;
	st->free= clip_free;
	st->init= clip_init;
	st->duplicate= clip_duplicate;
	st->operatortypes= clip_operatortypes;
	st->keymap= clip_keymap;
	st->listener= clip_listener;
	st->context= clip_context;
	st->refresh= clip_refresh;

	/* regions: main window */
	art= MEM_callocN(sizeof(ARegionType), "spacetype clip region");
	art->regionid= RGN_TYPE_WINDOW;
	art->init= clip_main_area_init;
	art->draw= clip_main_area_draw;
	art->keymapflag= ED_KEYMAP_FRAMES|ED_KEYMAP_UI;

	BLI_addhead(&st->regiontypes, art);

	/* regions: properties */
	art= MEM_callocN(sizeof(ARegionType), "spacetype clip region properties");
	art->regionid= RGN_TYPE_UI;
	art->prefsizex= UI_COMPACT_PANEL_WIDTH;
	art->keymapflag= ED_KEYMAP_FRAMES|ED_KEYMAP_UI;
	art->init= clip_properties_area_init;
	art->draw= clip_properties_area_draw;
	BLI_addhead(&st->regiontypes, art);
	ED_clip_buttons_register(art);

	/* regions: tools */
	art= MEM_callocN(sizeof(ARegionType), "spacetype clip region tools");
	art->regionid= RGN_TYPE_TOOLS;
	art->prefsizex= UI_COMPACT_PANEL_WIDTH;
	art->keymapflag= ED_KEYMAP_FRAMES|ED_KEYMAP_UI;
	art->init= clip_tools_area_init;
	art->draw= clip_tools_area_draw;

	BLI_addhead(&st->regiontypes, art);

	/* tool properties */
	art= MEM_callocN(sizeof(ARegionType), "spacetype clip tool properties region");
	art->regionid = RGN_TYPE_TOOL_PROPS;
	art->prefsizex= 0;
	art->prefsizey= 120;
	art->keymapflag= ED_KEYMAP_FRAMES|ED_KEYMAP_UI;
	art->listener= clip_props_area_listener;
	art->init= clip_tools_area_init;
	art->draw= clip_tools_area_draw;
	ED_clip_tool_props_register(art);

	BLI_addhead(&st->regiontypes, art);

	/* regions: header */
	art= MEM_callocN(sizeof(ARegionType), "spacetype clip region");
	art->regionid= RGN_TYPE_HEADER;
	art->prefsizey= HEADERY;
	art->keymapflag= ED_KEYMAP_FRAMES|ED_KEYMAP_UI|ED_KEYMAP_VIEW2D|ED_KEYMAP_HEADER;

	art->init= clip_header_area_init;
	art->draw= clip_header_area_draw;

	BLI_addhead(&st->regiontypes, art);

	BKE_spacetype_register(st);
}

/* SPDX-FileCopyrightText: 2008 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup spseq
 */

#include <cmath>
#include <cstdio>
#include <cstring>

#include "DNA_gpencil_legacy_types.h"
#include "DNA_mask_types.h"
#include "DNA_scene_types.h"

#include "MEM_guardedalloc.h"

#include "BLI_blenlib.h"
#include "BLI_ghash.h"
#include "BLI_math_base.h"

#include "BKE_global.h"
#include "BKE_lib_query.h"
#include "BKE_lib_remap.h"
#include "BKE_screen.hh"
#include "BKE_sequencer_offscreen.h"

#include "GPU_state.h"

#include "ED_markers.hh"
#include "ED_screen.hh"
#include "ED_space_api.hh"
#include "ED_time_scrub_ui.hh"
#include "ED_transform.hh"
#include "ED_view3d.hh"
#include "ED_view3d_offscreen.hh" /* Only for sequencer view3d drawing callback. */

#include "WM_api.hh"
#include "WM_message.hh"

#include "SEQ_sequencer.hh"
#include "SEQ_time.hh"
#include "SEQ_transform.hh"
#include "SEQ_utils.hh"

#include "UI_interface.hh"
#include "UI_view2d.hh"

#include "BLO_read_write.hh"

#include "IMB_imbuf.h"

/* Only for cursor drawing. */
#include "DRW_engine.h"

/* Own include. */
#include "sequencer_intern.hh"

/**************************** common state *****************************/

static void sequencer_scopes_tag_refresh(ScrArea *area)
{
  SpaceSeq *sseq = (SpaceSeq *)area->spacedata.first;

  sseq->scopes.reference_ibuf = nullptr;
}

/* ******************** manage regions ********************* */

static ARegion *sequencer_find_region(ScrArea *area, short type)
{

  LISTBASE_FOREACH (ARegion *, region, &area->regionbase) {
    if (region->regiontype == type) {
      return region;
    }
  }
  return nullptr;
}

/* ******************** default callbacks for sequencer space ***************** */

static SpaceLink *sequencer_create(const ScrArea * /*area*/, const Scene *scene)
{
  ARegion *region;
  SpaceSeq *sseq;

  sseq = MEM_cnew<SpaceSeq>("initsequencer");
  sseq->spacetype = SPACE_SEQ;
  sseq->chanshown = 0;
  sseq->view = SEQ_VIEW_SEQUENCE;
  sseq->mainb = SEQ_DRAW_IMG_IMBUF;
  sseq->flag = SEQ_USE_ALPHA | SEQ_SHOW_MARKERS | SEQ_ZOOM_TO_FIT | SEQ_SHOW_OVERLAY;
  sseq->preview_overlay.flag = SEQ_PREVIEW_SHOW_GPENCIL | SEQ_PREVIEW_SHOW_OUTLINE_SELECTED;
  sseq->timeline_overlay.flag = SEQ_TIMELINE_SHOW_STRIP_NAME | SEQ_TIMELINE_SHOW_STRIP_SOURCE |
                                SEQ_TIMELINE_SHOW_STRIP_DURATION | SEQ_TIMELINE_SHOW_GRID |
                                SEQ_TIMELINE_SHOW_FCURVES | SEQ_TIMELINE_SHOW_STRIP_COLOR_TAG |
                                SEQ_TIMELINE_SHOW_STRIP_RETIMING;

  BLI_rctf_init(&sseq->runtime.last_thumbnail_area, 0.0f, 0.0f, 0.0f, 0.0f);
  sseq->runtime.last_displayed_thumbnails = nullptr;

  /* Header. */
  region = MEM_cnew<ARegion>("header for sequencer");

  BLI_addtail(&sseq->regionbase, static_cast<void *>(region));
  region->regiontype = RGN_TYPE_HEADER;
  region->alignment = (U.uiflag & USER_HEADER_BOTTOM) ? RGN_ALIGN_BOTTOM : RGN_ALIGN_TOP;

  /* Tool header. */
  region = MEM_cnew<ARegion>("tool header for sequencer");

  BLI_addtail(&sseq->regionbase, static_cast<void *>(region));
  region->regiontype = RGN_TYPE_TOOL_HEADER;
  region->alignment = (U.uiflag & USER_HEADER_BOTTOM) ? RGN_ALIGN_BOTTOM : RGN_ALIGN_TOP;
  region->flag = RGN_FLAG_HIDDEN | RGN_FLAG_HIDDEN_BY_USER;

  /* Buttons/list view. */
  region = MEM_cnew<ARegion>("buttons for sequencer");

  BLI_addtail(&sseq->regionbase, static_cast<void *>(region));
  region->regiontype = RGN_TYPE_UI;
  region->alignment = RGN_ALIGN_RIGHT;
  region->flag = RGN_FLAG_HIDDEN;

  /* Toolbar. */
  region = MEM_cnew<ARegion>("tools for sequencer");

  BLI_addtail(&sseq->regionbase, static_cast<void *>(region));
  region->regiontype = RGN_TYPE_TOOLS;
  region->alignment = RGN_ALIGN_LEFT;
  region->flag = RGN_FLAG_HIDDEN;

  /* Channels. */
  region = MEM_cnew<ARegion>("channels for sequencer");

  BLI_addtail(&sseq->regionbase, static_cast<void *>(region));
  region->regiontype = RGN_TYPE_CHANNELS;
  region->alignment = RGN_ALIGN_LEFT;
  region->v2d.flag |= V2D_VIEWSYNC_AREA_VERTICAL;

  /* Preview region. */
  /* NOTE: if you change values here, also change them in sequencer_init_preview_region. */
  region = MEM_cnew<ARegion>("preview region for sequencer");
  BLI_addtail(&sseq->regionbase, static_cast<void *>(region));
  region->regiontype = RGN_TYPE_PREVIEW;
  region->alignment = RGN_ALIGN_TOP;
  /* For now, aspect ratio should be maintained, and zoom is clamped within sane default limits. */
  region->v2d.keepzoom = V2D_KEEPASPECT | V2D_KEEPZOOM | V2D_LIMITZOOM;
  region->v2d.minzoom = 0.001f;
  region->v2d.maxzoom = 1000.0f;
  region->v2d.tot.xmin = -960.0f; /* 1920 width centered. */
  region->v2d.tot.ymin = -540.0f; /* 1080 height centered. */
  region->v2d.tot.xmax = 960.0f;
  region->v2d.tot.ymax = 540.0f;
  region->v2d.min[0] = 0.0f;
  region->v2d.min[1] = 0.0f;
  region->v2d.max[0] = 12000.0f;
  region->v2d.max[1] = 12000.0f;
  region->v2d.cur = region->v2d.tot;
  region->v2d.align = V2D_ALIGN_FREE;
  region->v2d.keeptot = V2D_KEEPTOT_FREE;

  /* Main region. */
  region = MEM_cnew<ARegion>("main region for sequencer");

  BLI_addtail(&sseq->regionbase, static_cast<void *>(region));
  region->regiontype = RGN_TYPE_WINDOW;

  /* Seq space goes from (0,8) to (0, efra). */
  region->v2d.tot.xmin = 0.0f;
  region->v2d.tot.ymin = 0.0f;
  region->v2d.tot.xmax = scene->r.efra;
  region->v2d.tot.ymax = 8.5f;

  region->v2d.cur = region->v2d.tot;

  region->v2d.min[0] = 10.0f;
  region->v2d.min[1] = 1.0f;

  region->v2d.max[0] = MAXFRAMEF;
  region->v2d.max[1] = MAXSEQ;

  region->v2d.minzoom = 0.01f;
  region->v2d.maxzoom = 100.0f;

  region->v2d.scroll |= (V2D_SCROLL_BOTTOM | V2D_SCROLL_HORIZONTAL_HANDLES);
  region->v2d.scroll |= (V2D_SCROLL_RIGHT | V2D_SCROLL_VERTICAL_HANDLES);
  region->v2d.keepzoom = 0;
  region->v2d.keeptot = 0;
  region->v2d.flag |= V2D_VIEWSYNC_AREA_VERTICAL;
  region->v2d.align = V2D_ALIGN_NO_NEG_Y;

  sseq->runtime.last_displayed_thumbnails = nullptr;

  return (SpaceLink *)sseq;
}

/* Not spacelink itself. */
static void sequencer_free(SpaceLink *sl)
{
  SpaceSeq *sseq = (SpaceSeq *)sl;
  SequencerScopes *scopes = &sseq->scopes;

#if 0
  if (sseq->gpd) {
    BKE_gpencil_free_data(sseq->gpd);
  }
#endif

  if (scopes->zebra_ibuf) {
    IMB_freeImBuf(scopes->zebra_ibuf);
  }

  if (scopes->waveform_ibuf) {
    IMB_freeImBuf(scopes->waveform_ibuf);
  }

  if (scopes->sep_waveform_ibuf) {
    IMB_freeImBuf(scopes->sep_waveform_ibuf);
  }

  if (scopes->vector_ibuf) {
    IMB_freeImBuf(scopes->vector_ibuf);
  }

  if (scopes->histogram_ibuf) {
    IMB_freeImBuf(scopes->histogram_ibuf);
  }

  if (sseq->runtime.last_displayed_thumbnails) {
    BLI_ghash_free(
        sseq->runtime.last_displayed_thumbnails, nullptr, last_displayed_thumbnails_list_free);
    sseq->runtime.last_displayed_thumbnails = nullptr;
  }
}

/* Space-type init callback. */
static void sequencer_init(wmWindowManager * /*wm*/, ScrArea * /*area*/) {}

static void sequencer_refresh(const bContext *C, ScrArea *area)
{
  wmWindowManager *wm = CTX_wm_manager(C);
  wmWindow *window = CTX_wm_window(C);
  SpaceSeq *sseq = (SpaceSeq *)area->spacedata.first;
  ARegion *region_main = sequencer_find_region(area, RGN_TYPE_WINDOW);
  ARegion *region_preview = sequencer_find_region(area, RGN_TYPE_PREVIEW);
  bool view_changed = false;

  switch (sseq->view) {
    case SEQ_VIEW_PREVIEW:
      /* Reset scrolling when preview region just appears. */
      if (!(region_preview->v2d.flag & V2D_IS_INIT)) {
        region_preview->v2d.cur = region_preview->v2d.tot;
        /* Only redraw, don't re-init. */
        ED_area_tag_redraw(area);
      }
      if (region_preview->alignment != RGN_ALIGN_NONE) {
        region_preview->alignment = RGN_ALIGN_NONE;
        view_changed = true;
      }
      break;
    case SEQ_VIEW_SEQUENCE_PREVIEW: {
      /* Get available height (without DPI correction). */
      const float height = (area->winy - ED_area_headersize()) / UI_SCALE_FAC;

      /* We reuse hidden region's size, allows to find same layout as before if we just switch
       * between one 'full window' view and the combined one. This gets lost if we switch to both
       * 'full window' views before, though... Better than nothing. */
      if (!(region_preview->v2d.flag & V2D_IS_INIT)) {
        region_preview->v2d.cur = region_preview->v2d.tot;
        region_main->sizey = int(height - region_preview->sizey);
        region_preview->sizey = int(height - region_main->sizey);
        view_changed = true;
      }
      if (region_preview->alignment != RGN_ALIGN_TOP) {
        region_preview->alignment = RGN_ALIGN_TOP;
        view_changed = true;
      }
      /* Final check that both preview and main height are reasonable. */
      if (region_preview->sizey < 10 || region_main->sizey < 10 ||
          region_preview->sizey + region_main->sizey > height)
      {
        region_preview->sizey = roundf(height * 0.4f);
        region_main->sizey = int(height - region_preview->sizey);
        view_changed = true;
      }
      break;
    }
    case SEQ_VIEW_SEQUENCE:
      break;
  }

  if (view_changed) {
    ED_area_init(wm, window, area);
    ED_area_tag_redraw(area);
  }
}

static SpaceLink *sequencer_duplicate(SpaceLink *sl)
{
  SpaceSeq *sseqn = static_cast<SpaceSeq *>(MEM_dupallocN(sl));

  /* Clear or remove stuff from old. */
  // sseq->gpd = gpencil_data_duplicate(sseq->gpd, false);

  memset(&sseqn->scopes, 0, sizeof(sseqn->scopes));
  memset(&sseqn->runtime, 0, sizeof(sseqn->runtime));

  return (SpaceLink *)sseqn;
}

static void sequencer_listener(const wmSpaceTypeListenerParams *params)
{
  ScrArea *area = params->area;
  const wmNotifier *wmn = params->notifier;

  /* Context changes. */
  switch (wmn->category) {
    case NC_SCENE:
      switch (wmn->data) {
        case ND_FRAME:
        case ND_SEQUENCER:
          sequencer_scopes_tag_refresh(area);
          break;
      }
      break;
    case NC_WINDOW:
    case NC_SPACE:
      if (wmn->data == ND_SPACE_SEQUENCER) {
        sequencer_scopes_tag_refresh(area);
      }
      break;
    case NC_GPENCIL:
      if (wmn->data & ND_GPENCIL_EDITMODE) {
        ED_area_tag_redraw(area);
      }
      break;
  }
}

/* DO NOT make this static, this hides the symbol and breaks API generation script. */
extern "C" const char *sequencer_context_dir[]; /* Quiet warning. */
const char *sequencer_context_dir[] = {"edit_mask", nullptr};

static int /*eContextResult*/ sequencer_context(const bContext *C,
                                                const char *member,
                                                bContextDataResult *result)
{
  Scene *scene = CTX_data_scene(C);

  if (CTX_data_dir(member)) {
    CTX_data_dir_set(result, sequencer_context_dir);

    return CTX_RESULT_OK;
  }
  if (CTX_data_equals(member, "edit_mask")) {
    Mask *mask = SEQ_active_mask_get(scene);
    if (mask) {
      CTX_data_id_pointer_set(result, &mask->id);
    }
    return CTX_RESULT_OK;
  }

  return CTX_RESULT_MEMBER_NOT_FOUND;
}

static void SEQUENCER_GGT_navigate(wmGizmoGroupType *gzgt)
{
  VIEW2D_GGT_navigate_impl(gzgt, "SEQUENCER_GGT_navigate");
}

static void SEQUENCER_GGT_gizmo2d(wmGizmoGroupType *gzgt)
{
  gzgt->name = "Sequencer Transform Gizmo";
  gzgt->idname = "SEQUENCER_GGT_gizmo2d";

  gzgt->flag |= (WM_GIZMOGROUPTYPE_TOOL_FALLBACK_KEYMAP |
                 WM_GIZMOGROUPTYPE_DELAY_REFRESH_FOR_TWEAK);

  gzgt->gzmap_params.spaceid = SPACE_SEQ;
  gzgt->gzmap_params.regionid = RGN_TYPE_PREVIEW;

  ED_widgetgroup_gizmo2d_xform_callbacks_set(gzgt);
}

static void SEQUENCER_GGT_gizmo2d_translate(wmGizmoGroupType *gzgt)
{
  gzgt->name = "Sequencer Translate Gizmo";
  gzgt->idname = "SEQUENCER_GGT_gizmo2d_translate";

  gzgt->flag |= (WM_GIZMOGROUPTYPE_TOOL_FALLBACK_KEYMAP |
                 WM_GIZMOGROUPTYPE_DELAY_REFRESH_FOR_TWEAK);

  gzgt->gzmap_params.spaceid = SPACE_SEQ;
  gzgt->gzmap_params.regionid = RGN_TYPE_PREVIEW;

  ED_widgetgroup_gizmo2d_xform_no_cage_callbacks_set(gzgt);
}

static void SEQUENCER_GGT_gizmo2d_resize(wmGizmoGroupType *gzgt)
{
  gzgt->name = "Sequencer Transform Gizmo Resize";
  gzgt->idname = "SEQUENCER_GGT_gizmo2d_resize";

  gzgt->flag |= (WM_GIZMOGROUPTYPE_TOOL_FALLBACK_KEYMAP |
                 WM_GIZMOGROUPTYPE_DELAY_REFRESH_FOR_TWEAK);

  gzgt->gzmap_params.spaceid = SPACE_SEQ;
  gzgt->gzmap_params.regionid = RGN_TYPE_PREVIEW;

  ED_widgetgroup_gizmo2d_resize_callbacks_set(gzgt);
}

static void SEQUENCER_GGT_gizmo2d_rotate(wmGizmoGroupType *gzgt)
{
  gzgt->name = "Sequencer Transform Gizmo Resize";
  gzgt->idname = "SEQUENCER_GGT_gizmo2d_rotate";

  gzgt->flag |= (WM_GIZMOGROUPTYPE_TOOL_FALLBACK_KEYMAP |
                 WM_GIZMOGROUPTYPE_DELAY_REFRESH_FOR_TWEAK);

  gzgt->gzmap_params.spaceid = SPACE_SEQ;
  gzgt->gzmap_params.regionid = RGN_TYPE_PREVIEW;

  ED_widgetgroup_gizmo2d_rotate_callbacks_set(gzgt);
}

static void sequencer_gizmos()
{
  WM_gizmogrouptype_append(SEQUENCER_GGT_gizmo2d);
  WM_gizmogrouptype_append(SEQUENCER_GGT_gizmo2d_translate);
  WM_gizmogrouptype_append(SEQUENCER_GGT_gizmo2d_resize);
  WM_gizmogrouptype_append(SEQUENCER_GGT_gizmo2d_rotate);

  const wmGizmoMapType_Params params_preview = {SPACE_SEQ, RGN_TYPE_PREVIEW};
  wmGizmoMapType *gzmap_type_preview = WM_gizmomaptype_ensure(&params_preview);
  WM_gizmogrouptype_append_and_link(gzmap_type_preview, SEQUENCER_GGT_navigate);
}

/* *********************** sequencer (main) region ************************ */

static bool sequencer_main_region_poll(const RegionPollParams *params)
{
  const SpaceSeq *sseq = (SpaceSeq *)params->area->spacedata.first;
  return ELEM(sseq->view, SEQ_VIEW_SEQUENCE, SEQ_VIEW_SEQUENCE_PREVIEW);
}

/* Add handlers, stuff you only do once or on area/region changes. */
static void sequencer_main_region_init(wmWindowManager *wm, ARegion *region)
{
  wmKeyMap *keymap;
  ListBase *lb;

  UI_view2d_region_reinit(&region->v2d, V2D_COMMONVIEW_CUSTOM, region->winx, region->winy);

#if 0
  keymap = WM_keymap_ensure(wm->defaultconf, "Mask Editing", SPACE_EMPTY, RGN_TYPE_WINDOW);
  WM_event_add_keymap_handler_v2d_mask(&region->handlers, keymap);
#endif

  keymap = WM_keymap_ensure(wm->defaultconf, "SequencerCommon", SPACE_SEQ, RGN_TYPE_WINDOW);
  WM_event_add_keymap_handler_v2d_mask(&region->handlers, keymap);

  /* Own keymap. */
  keymap = WM_keymap_ensure(wm->defaultconf, "Sequencer", SPACE_SEQ, RGN_TYPE_WINDOW);
  WM_event_add_keymap_handler_v2d_mask(&region->handlers, keymap);

  /* Add drop boxes. */
  lb = WM_dropboxmap_find("Sequencer", SPACE_SEQ, RGN_TYPE_WINDOW);

  WM_event_add_dropbox_handler(&region->handlers, lb);
}

/* Strip editing timeline. */
static void sequencer_main_region_draw(const bContext *C, ARegion *region)
{
  draw_timeline_seq(C, region);
}

/* Strip editing timeline. */
static void sequencer_main_region_draw_overlay(const bContext *C, ARegion *region)
{
  draw_timeline_seq_display(C, region);
}

static void sequencer_main_clamp_view(const bContext *C, ARegion *region)
{
  SpaceSeq *sseq = CTX_wm_space_seq(C);

  if ((sseq->flag & SEQ_CLAMP_VIEW) == 0) {
    return;
  }

  View2D *v2d = &region->v2d;
  Scene *scene = CTX_data_scene(C);
  Editing *ed = SEQ_editing_get(scene);

  if (ed == nullptr) {
    return;
  }

  /* Transformation uses edge panning to move view. Also if smooth view is running, don't apply
   * clamping to prevent overriding this functionality. */
  if (G.moving || v2d->smooth_timer != nullptr) {
    return;
  }

  /* Initialize default view with 7 channels, that are visible even if empty. */
  rctf strip_boundbox;
  BLI_rctf_init(&strip_boundbox, 0.0f, 0.0f, 1.0f, 6.0f);
  SEQ_timeline_expand_boundbox(scene, ed->seqbasep, &strip_boundbox);

  /* Clamp Y max. Scrubbing area height must be added, so strips aren't occluded. */
  rcti scrub_rect;
  ED_time_scrub_region_rect_get(region, &scrub_rect);
  const float pixel_view_size_y = BLI_rctf_size_y(&v2d->cur) / BLI_rcti_size_y(&v2d->mask);
  const float scrub_bar_height = BLI_rcti_size_y(&scrub_rect) * pixel_view_size_y;

  /* Channel n has range of <n, n+1>, +1 for empty channel. */
  strip_boundbox.ymax += 2.0f + scrub_bar_height;

  /* Clamp Y min. Scroller and marker area height must be added, so strips aren't occluded. */
  float scroll_bar_height = v2d->hor.ymax * pixel_view_size_y;

  ListBase *markers = ED_context_get_markers(C);
  if (markers != nullptr && !BLI_listbase_is_empty(markers)) {
    float markers_size = UI_MARKER_MARGIN_Y * pixel_view_size_y;
    strip_boundbox.ymin -= markers_size;
  }
  else {
    strip_boundbox.ymin -= scroll_bar_height;
  }

  /* If strip is deleted, don't move view automatically, keep current range until it is changed. */
  strip_boundbox.ymax = max_ff(sseq->runtime.timeline_clamp_custom_range, strip_boundbox.ymax);

  rctf view_clamped = v2d->cur;

  const float range_y = BLI_rctf_size_y(&view_clamped);
  if (view_clamped.ymax > strip_boundbox.ymax) {
    view_clamped.ymax = strip_boundbox.ymax;
    view_clamped.ymin = max_ff(strip_boundbox.ymin, strip_boundbox.ymax - range_y);
  }
  if (view_clamped.ymin < strip_boundbox.ymin) {
    view_clamped.ymin = strip_boundbox.ymin;
    view_clamped.ymax = min_ff(strip_boundbox.ymax, strip_boundbox.ymin + range_y);
  }

  v2d->cur = view_clamped;
}

static void sequencer_main_region_clamp_custom_set(const bContext *C, ARegion *region)
{
  SpaceSeq *sseq = CTX_wm_space_seq(C);
  View2D *v2d = &region->v2d;

  if ((v2d->flag & V2D_IS_NAVIGATING) == 0) {
    sseq->runtime.timeline_clamp_custom_range = v2d->cur.ymax;
  }
}

static void sequencer_main_region_layout(const bContext *C, ARegion *region)
{
  sequencer_main_region_clamp_custom_set(C, region);
  sequencer_main_clamp_view(C, region);
}

static void sequencer_main_region_view2d_changed(const bContext *C, ARegion *region)
{
  sequencer_main_region_clamp_custom_set(C, region);
  sequencer_main_clamp_view(C, region);
}

static void sequencer_main_region_listener(const wmRegionListenerParams *params)
{
  ARegion *region = params->region;
  const wmNotifier *wmn = params->notifier;

  /* Context changes. */
  switch (wmn->category) {
    case NC_SCENE:
      switch (wmn->data) {
        case ND_FRAME:
        case ND_FRAME_RANGE:
        case ND_MARKERS:
        case ND_RENDER_OPTIONS: /* For FPS and FPS Base. */
        case ND_SEQUENCER:
        case ND_RENDER_RESULT:
          ED_region_tag_redraw(region);
          WM_gizmomap_tag_refresh(region->gizmo_map);
          break;
      }
      break;
    case NC_ANIMATION:
      switch (wmn->data) {
        case ND_KEYFRAME:
          ED_region_tag_redraw(region);
          break;
      }
      break;
    case NC_SPACE:
      if (wmn->data == ND_SPACE_SEQUENCER) {
        ED_region_tag_redraw(region);
        WM_gizmomap_tag_refresh(region->gizmo_map);
      }
      break;
    case NC_ID:
      if (wmn->action == NA_RENAME) {
        ED_region_tag_redraw(region);
      }
      break;
    case NC_SCREEN:
      if (ELEM(wmn->data, ND_ANIMPLAY)) {
        ED_region_tag_redraw(region);
        WM_gizmomap_tag_refresh(region->gizmo_map);
      }
      break;
  }
}

static void sequencer_main_region_message_subscribe(const wmRegionMessageSubscribeParams *params)
{
  wmMsgBus *mbus = params->message_bus;
  Scene *scene = params->scene;
  ARegion *region = params->region;

  wmMsgSubscribeValue msg_sub_value_region_tag_redraw{};
  msg_sub_value_region_tag_redraw.owner = region;
  msg_sub_value_region_tag_redraw.user_data = region;
  msg_sub_value_region_tag_redraw.notify = ED_region_do_msg_notify_tag_redraw;

  /* Timeline depends on scene properties. */
  {
    bool use_preview = (scene->r.flag & SCER_PRV_RANGE);
    const PropertyRNA *props[] = {
        use_preview ? &rna_Scene_frame_preview_start : &rna_Scene_frame_start,
        use_preview ? &rna_Scene_frame_preview_end : &rna_Scene_frame_end,
        &rna_Scene_use_preview_range,
        &rna_Scene_frame_current,
    };

    PointerRNA idptr = RNA_id_pointer_create(&scene->id);

    for (int i = 0; i < ARRAY_SIZE(props); i++) {
      WM_msg_subscribe_rna(mbus, &idptr, props[i], &msg_sub_value_region_tag_redraw, __func__);
    }
  }

  {
    StructRNA *type_array[] = {
        &RNA_SequenceEditor,

        &RNA_Sequence,
        /* Members of 'Sequence'. */
        &RNA_SequenceCrop,
        &RNA_SequenceTransform,
        &RNA_SequenceModifier,
        &RNA_SequenceColorBalanceData,
    };
    wmMsgParams_RNA msg_key_params = {{nullptr}};
    for (int i = 0; i < ARRAY_SIZE(type_array); i++) {
      msg_key_params.ptr.type = type_array[i];
      WM_msg_subscribe_rna_params(
          mbus, &msg_key_params, &msg_sub_value_region_tag_redraw, __func__);
    }
  }
}

/* *********************** header region ************************ */
/* Add handlers, stuff you only do once or on area/region changes. */
static void sequencer_header_region_init(wmWindowManager * /*wm*/, ARegion *region)
{
  ED_region_header_init(region);
}

static void sequencer_header_region_draw(const bContext *C, ARegion *region)
{
  ED_region_header(C, region);
}

/* *********************** toolbar region ************************ */
/* Add handlers, stuff you only do once or on area/region changes. */
static void sequencer_tools_region_init(wmWindowManager *wm, ARegion *region)
{
  wmKeyMap *keymap;

  region->v2d.scroll = V2D_SCROLL_RIGHT | V2D_SCROLL_VERTICAL_HIDE;
  ED_region_panels_init(wm, region);

  keymap = WM_keymap_ensure(wm->defaultconf, "SequencerCommon", SPACE_SEQ, RGN_TYPE_WINDOW);
  WM_event_add_keymap_handler_v2d_mask(&region->handlers, keymap);
}

static void sequencer_tools_region_draw(const bContext *C, ARegion *region)
{
  ED_region_panels(C, region);
}
/* *********************** preview region ************************ */

static bool sequencer_preview_region_poll(const RegionPollParams *params)
{
  const SpaceSeq *sseq = (SpaceSeq *)params->area->spacedata.first;
  return ELEM(sseq->view, SEQ_VIEW_PREVIEW, SEQ_VIEW_SEQUENCE_PREVIEW);
}

static void sequencer_preview_region_init(wmWindowManager *wm, ARegion *region)
{
  wmKeyMap *keymap;

  UI_view2d_region_reinit(&region->v2d, V2D_COMMONVIEW_CUSTOM, region->winx, region->winy);

#if 0
  keymap = WM_keymap_ensure(wm->defaultconf, "Mask Editing", SPACE_EMPTY, RGN_TYPE_WINDOW);
  WM_event_add_keymap_handler_v2d_mask(&region->handlers, keymap);
#endif

  keymap = WM_keymap_ensure(wm->defaultconf, "SequencerCommon", SPACE_SEQ, RGN_TYPE_WINDOW);
  WM_event_add_keymap_handler_v2d_mask(&region->handlers, keymap);

  /* Own keymap. */
  keymap = WM_keymap_ensure(wm->defaultconf, "SequencerPreview", SPACE_SEQ, RGN_TYPE_WINDOW);
  WM_event_add_keymap_handler_v2d_mask(&region->handlers, keymap);

  ListBase *lb = WM_dropboxmap_find("Sequencer", SPACE_SEQ, RGN_TYPE_PREVIEW);
  WM_event_add_dropbox_handler(&region->handlers, lb);
}

static void sequencer_preview_region_layout(const bContext *C, ARegion *region)
{
  SpaceSeq *sseq = CTX_wm_space_seq(C);

  if (sseq->flag & SEQ_ZOOM_TO_FIT) {
    View2D *v2d = &region->v2d;
    v2d->cur = v2d->tot;
  }
}

static void sequencer_preview_region_view2d_changed(const bContext *C, ARegion * /*region*/)
{
  SpaceSeq *sseq = CTX_wm_space_seq(C);
  sseq->flag &= ~SEQ_ZOOM_TO_FIT;
}

static bool is_cursor_visible(const SpaceSeq *sseq)
{
  if (G.moving & G_TRANSFORM_CURSOR) {
    return true;
  }

  if ((sseq->flag & SEQ_SHOW_OVERLAY) &&
      (sseq->preview_overlay.flag & SEQ_PREVIEW_SHOW_2D_CURSOR) != 0)
  {
    return true;
  }
  return false;
}

static void sequencer_preview_region_draw(const bContext *C, ARegion *region)
{
  ScrArea *area = CTX_wm_area(C);
  SpaceSeq *sseq = static_cast<SpaceSeq *>(area->spacedata.first);
  Scene *scene = CTX_data_scene(C);
  wmWindowManager *wm = CTX_wm_manager(C);
  const bool draw_overlay = sseq->flag & SEQ_SHOW_OVERLAY;
  const bool draw_frame_overlay = (scene->ed &&
                                   (scene->ed->overlay_frame_flag & SEQ_EDIT_OVERLAY_FRAME_SHOW) &&
                                   draw_overlay);
  const bool is_playing = ED_screen_animation_playing(wm);

  if (!(draw_frame_overlay && (sseq->overlay_frame_type == SEQ_OVERLAY_FRAME_TYPE_REFERENCE))) {
    sequencer_draw_preview(C, scene, region, sseq, scene->r.cfra, 0, false, false);
  }

  if (draw_frame_overlay && sseq->overlay_frame_type != SEQ_OVERLAY_FRAME_TYPE_CURRENT) {
    int over_cfra;

    if (scene->ed->overlay_frame_flag & SEQ_EDIT_OVERLAY_FRAME_ABS) {
      over_cfra = scene->ed->overlay_frame_abs;
    }
    else {
      over_cfra = scene->r.cfra + scene->ed->overlay_frame_ofs;
    }

    if ((over_cfra != scene->r.cfra) || (sseq->overlay_frame_type != SEQ_OVERLAY_FRAME_TYPE_RECT))
    {
      sequencer_draw_preview(
          C, scene, region, sseq, scene->r.cfra, over_cfra - scene->r.cfra, true, false);
    }
  }

  /* No need to show the cursor for scopes. */
  if ((is_playing == false) && (sseq->mainb == SEQ_DRAW_IMG_IMBUF) && is_cursor_visible(sseq)) {
    GPU_color_mask(true, true, true, true);
    GPU_depth_mask(false);
    GPU_depth_test(GPU_DEPTH_NONE);

    float cursor_pixel[2];
    SEQ_image_preview_unit_to_px(scene, sseq->cursor, cursor_pixel);

    DRW_draw_cursor_2d_ex(region, cursor_pixel);
  }

  if ((is_playing == false) && (sseq->gizmo_flag & SEQ_GIZMO_HIDE) == 0) {
    WM_gizmomap_draw(region->gizmo_map, C, WM_GIZMOMAP_DRAWSTEP_2D);
  }

  if ((U.uiflag & USER_SHOW_FPS) && ED_screen_animation_no_scrub(wm)) {
    const rcti *rect = ED_region_visible_rect(region);
    int xoffset = rect->xmin + U.widget_unit;
    int yoffset = rect->ymax;
    ED_scene_draw_fps(scene, xoffset, &yoffset);
  }
}

static void sequencer_preview_region_listener(const wmRegionListenerParams *params)
{
  ARegion *region = params->region;
  const wmNotifier *wmn = params->notifier;

  WM_gizmomap_tag_refresh(region->gizmo_map);

  /* Context changes. */
  switch (wmn->category) {
    case NC_GPENCIL:
      if (ELEM(wmn->action, NA_EDITED, NA_SELECTED)) {
        ED_region_tag_redraw(region);
      }
      break;
    case NC_SCENE:
      switch (wmn->data) {
        case ND_FRAME:
        case ND_MARKERS:
        case ND_SEQUENCER:
        case ND_RENDER_OPTIONS:
        case ND_DRAW_RENDER_VIEWPORT:
          ED_region_tag_redraw(region);
          break;
      }
      break;
    case NC_ANIMATION:
      switch (wmn->data) {
        case ND_KEYFRAME:
          ED_region_tag_redraw(region);
          break;
      }
      break;
    case NC_SPACE:
      if (wmn->data == ND_SPACE_SEQUENCER) {
        ED_region_tag_redraw(region);
      }
      break;
    case NC_ID:
      switch (wmn->data) {
        case NA_RENAME:
          ED_region_tag_redraw(region);
          break;
      }
      break;
    case NC_MASK:
      if (wmn->action == NA_EDITED) {
        ED_region_tag_redraw(region);
      }
      break;
  }
}

/* *********************** buttons region ************************ */

/* Add handlers, stuff you only do once or on area/region changes. */
static void sequencer_buttons_region_init(wmWindowManager *wm, ARegion *region)
{
  wmKeyMap *keymap;

  keymap = WM_keymap_ensure(wm->defaultconf, "SequencerCommon", SPACE_SEQ, RGN_TYPE_WINDOW);
  WM_event_add_keymap_handler_v2d_mask(&region->handlers, keymap);

  UI_panel_category_active_set_default(region, "Strip");
  ED_region_panels_init(wm, region);
}

static void sequencer_buttons_region_draw(const bContext *C, ARegion *region)
{
  ED_region_panels(C, region);
}

static void sequencer_buttons_region_listener(const wmRegionListenerParams *params)
{
  ARegion *region = params->region;
  const wmNotifier *wmn = params->notifier;

  /* Context changes. */
  switch (wmn->category) {
    case NC_GPENCIL:
      if (ELEM(wmn->action, NA_EDITED, NA_SELECTED)) {
        ED_region_tag_redraw(region);
      }
      break;
    case NC_SCENE:
      switch (wmn->data) {
        case ND_FRAME:
        case ND_SEQUENCER:
          ED_region_tag_redraw(region);
          break;
      }
      break;
    case NC_SPACE:
      if (wmn->data == ND_SPACE_SEQUENCER) {
        ED_region_tag_redraw(region);
      }
      break;
    case NC_ID:
      if (wmn->action == NA_RENAME) {
        ED_region_tag_redraw(region);
      }
      break;
  }
}

static void sequencer_id_remap(ScrArea * /*area*/, SpaceLink *slink, const IDRemapper *mappings)
{
  SpaceSeq *sseq = (SpaceSeq *)slink;
  BKE_id_remapper_apply(mappings, (ID **)&sseq->gpd, ID_REMAP_APPLY_DEFAULT);
}

static void sequencer_foreach_id(SpaceLink *space_link, LibraryForeachIDData *data)
{
  SpaceSeq *sseq = reinterpret_cast<SpaceSeq *>(space_link);
  BKE_LIB_FOREACHID_PROCESS_IDSUPER(data, sseq->gpd, IDWALK_CB_USER);
}

/* ************************************* */

static bool sequencer_channel_region_poll(const RegionPollParams *params)
{
  const SpaceSeq *sseq = (SpaceSeq *)params->area->spacedata.first;
  return ELEM(sseq->view, SEQ_VIEW_SEQUENCE);
}

/* add handlers, stuff you only do once or on area/region changes */
static void sequencer_channel_region_init(wmWindowManager *wm, ARegion *region)
{
  wmKeyMap *keymap;

  region->alignment = RGN_ALIGN_LEFT;

  UI_view2d_region_reinit(&region->v2d, V2D_COMMONVIEW_LIST, region->winx, region->winy);

  keymap = WM_keymap_ensure(wm->defaultconf, "Sequencer Channels", SPACE_SEQ, RGN_TYPE_WINDOW);
  WM_event_add_keymap_handler_v2d_mask(&region->handlers, keymap);
}

static void sequencer_channel_region_draw(const bContext *C, ARegion *region)
{
  draw_channels(C, region);
}

static void sequencer_space_blend_read_data(BlendDataReader * /*reader*/, SpaceLink *sl)
{
  SpaceSeq *sseq = (SpaceSeq *)sl;

  /* grease pencil data is not a direct data and can't be linked from direct_link*
   * functions, it should be linked from lib_link* functions instead
   *
   * otherwise it'll lead to lost grease data on open because it'll likely be
   * read from file after all other users of grease pencil and newdataadr would
   * simple return nullptr here (sergey)
   */
#if 0
  if (sseq->gpd) {
    sseq->gpd = newdataadr(fd, sseq->gpd);
    BKE_gpencil_blend_read_data(fd, sseq->gpd);
  }
#endif
  sseq->scopes.reference_ibuf = nullptr;
  sseq->scopes.zebra_ibuf = nullptr;
  sseq->scopes.waveform_ibuf = nullptr;
  sseq->scopes.sep_waveform_ibuf = nullptr;
  sseq->scopes.vector_ibuf = nullptr;
  sseq->scopes.histogram_ibuf = nullptr;
  memset(&sseq->runtime, 0x0, sizeof(sseq->runtime));
}

static void sequencer_space_blend_write(BlendWriter *writer, SpaceLink *sl)
{
  BLO_write_struct(writer, SpaceSeq, sl);
}

void ED_spacetype_sequencer()
{
  SpaceType *st = MEM_cnew<SpaceType>("spacetype sequencer");
  ARegionType *art;

  st->spaceid = SPACE_SEQ;
  STRNCPY(st->name, "Sequencer");

  st->create = sequencer_create;
  st->free = sequencer_free;
  st->init = sequencer_init;
  st->duplicate = sequencer_duplicate;
  st->operatortypes = sequencer_operatortypes;
  st->keymap = sequencer_keymap;
  st->context = sequencer_context;
  st->gizmos = sequencer_gizmos;
  st->dropboxes = sequencer_dropboxes;
  st->refresh = sequencer_refresh;
  st->listener = sequencer_listener;
  st->id_remap = sequencer_id_remap;
  st->foreach_id = sequencer_foreach_id;
  st->blend_read_data = sequencer_space_blend_read_data;
  st->blend_read_after_liblink = nullptr;
  st->blend_write = sequencer_space_blend_write;

  /* Create regions: */
  /* Main window. */
  art = MEM_cnew<ARegionType>("spacetype sequencer region");
  art->regionid = RGN_TYPE_WINDOW;
  art->poll = sequencer_main_region_poll;
  art->init = sequencer_main_region_init;
  art->draw = sequencer_main_region_draw;
  art->draw_overlay = sequencer_main_region_draw_overlay;
  art->layout = sequencer_main_region_layout;
  art->on_view2d_changed = sequencer_main_region_view2d_changed;
  art->listener = sequencer_main_region_listener;
  art->message_subscribe = sequencer_main_region_message_subscribe;
  art->keymapflag = ED_KEYMAP_TOOL | ED_KEYMAP_GIZMO | ED_KEYMAP_VIEW2D | ED_KEYMAP_FRAMES |
                    ED_KEYMAP_ANIMATION;
  BLI_addhead(&st->regiontypes, art);

  /* Preview. */
  art = MEM_cnew<ARegionType>("spacetype sequencer region");
  art->regionid = RGN_TYPE_PREVIEW;
  art->poll = sequencer_preview_region_poll;
  art->init = sequencer_preview_region_init;
  art->layout = sequencer_preview_region_layout;
  art->on_view2d_changed = sequencer_preview_region_view2d_changed;
  art->draw = sequencer_preview_region_draw;
  art->listener = sequencer_preview_region_listener;
  art->keymapflag = ED_KEYMAP_TOOL | ED_KEYMAP_GIZMO | ED_KEYMAP_VIEW2D | ED_KEYMAP_FRAMES |
                    ED_KEYMAP_GPENCIL;
  BLI_addhead(&st->regiontypes, art);

  /* List-view/buttons. */
  art = MEM_cnew<ARegionType>("spacetype sequencer region");
  art->regionid = RGN_TYPE_UI;
  art->prefsizex = UI_SIDEBAR_PANEL_WIDTH * 1.3f;
  art->keymapflag = ED_KEYMAP_UI | ED_KEYMAP_FRAMES;
  art->message_subscribe = ED_area_do_mgs_subscribe_for_tool_ui;
  art->listener = sequencer_buttons_region_listener;
  art->init = sequencer_buttons_region_init;
  art->draw = sequencer_buttons_region_draw;
  BLI_addhead(&st->regiontypes, art);

  sequencer_buttons_register(art);
  /* Toolbar. */
  art = MEM_cnew<ARegionType>("spacetype sequencer tools region");
  art->regionid = RGN_TYPE_TOOLS;
  art->prefsizex = int(UI_TOOLBAR_WIDTH);
  art->prefsizey = 50; /* XXX */
  art->keymapflag = ED_KEYMAP_UI | ED_KEYMAP_FRAMES;
  art->message_subscribe = ED_region_generic_tools_region_message_subscribe;
  art->snap_size = ED_region_generic_tools_region_snap_size;
  art->init = sequencer_tools_region_init;
  art->draw = sequencer_tools_region_draw;
  art->listener = sequencer_main_region_listener;
  BLI_addhead(&st->regiontypes, art);

  /* Channels. */
  art = MEM_cnew<ARegionType>("spacetype sequencer channels");
  art->regionid = RGN_TYPE_CHANNELS;
  art->prefsizex = UI_COMPACT_PANEL_WIDTH;
  art->keymapflag = ED_KEYMAP_UI;
  art->poll = sequencer_channel_region_poll;
  art->init = sequencer_channel_region_init;
  art->draw = sequencer_channel_region_draw;
  art->listener = sequencer_main_region_listener;
  BLI_addhead(&st->regiontypes, art);

  /* Tool header. */
  art = MEM_cnew<ARegionType>("spacetype sequencer tool header region");
  art->regionid = RGN_TYPE_TOOL_HEADER;
  art->prefsizey = HEADERY;
  art->keymapflag = ED_KEYMAP_UI | ED_KEYMAP_VIEW2D | ED_KEYMAP_FRAMES | ED_KEYMAP_HEADER;
  art->listener = sequencer_main_region_listener;
  art->init = sequencer_header_region_init;
  art->draw = sequencer_header_region_draw;
  art->message_subscribe = ED_area_do_mgs_subscribe_for_tool_header;
  BLI_addhead(&st->regiontypes, art);

  /* Header. */
  art = MEM_cnew<ARegionType>("spacetype sequencer region");
  art->regionid = RGN_TYPE_HEADER;
  art->prefsizey = HEADERY;
  art->keymapflag = ED_KEYMAP_UI | ED_KEYMAP_VIEW2D | ED_KEYMAP_FRAMES | ED_KEYMAP_HEADER;

  art->init = sequencer_header_region_init;
  art->draw = sequencer_header_region_draw;
  art->listener = sequencer_main_region_listener;
  BLI_addhead(&st->regiontypes, art);

  /* HUD. */
  art = ED_area_type_hud(st->spaceid);
  BLI_addhead(&st->regiontypes, art);

  BKE_spacetype_register(st);

  /* Set the sequencer callback when not in background mode. */
  if (G.background == 0) {
    sequencer_view3d_fn = reinterpret_cast<SequencerDrawView>(
        ED_view3d_draw_offscreen_imbuf_simple);
  }
}

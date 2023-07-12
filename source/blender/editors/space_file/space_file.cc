/* SPDX-FileCopyrightText: 2008 Blender Foundation
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup spfile
 */

#include <stdio.h>
#include <string.h>

#include "MEM_guardedalloc.h"

#include "BLI_blenlib.h"
#include "BLI_linklist.h"
#include "BLI_utildefines.h"

#include "BKE_appdir.h"
#include "BKE_context.h"
#include "BKE_global.h"
#include "BKE_lib_remap.h"
#include "BKE_main.h"
#include "BKE_screen.h"

#include "RNA_access.h"
#include "RNA_define.h"
#include "RNA_enum_types.h"

#include "WM_api.h"
#include "WM_message.h"
#include "WM_types.h"

#include "ED_asset.h"
#include "ED_asset_indexer.h"
#include "ED_fileselect.h"
#include "ED_screen.h"
#include "ED_space_api.h"

#include "IMB_imbuf_types.h"
#include "IMB_thumbs.h"

#include "UI_resources.h"
#include "UI_view2d.h"

#include "BLO_read_write.h"

#include "GPU_framebuffer.h"
#include "file_indexer.h"
#include "file_intern.h" /* own include */
#include "filelist.h"
#include "fsmenu.h"

/* ******************** default callbacks for file space ***************** */

static SpaceLink *file_create(const ScrArea * /*area*/, const Scene * /*scene*/)
{
  ARegion *region;
  SpaceFile *sfile;

  sfile = static_cast<SpaceFile *>(MEM_callocN(sizeof(SpaceFile), "initfile"));
  sfile->spacetype = SPACE_FILE;

  /* header */
  region = static_cast<ARegion *>(MEM_callocN(sizeof(ARegion), "header for file"));
  BLI_addtail(&sfile->regionbase, region);
  region->regiontype = RGN_TYPE_HEADER;
  /* Ignore user preference "USER_HEADER_BOTTOM" here (always show top for new types). */
  region->alignment = RGN_ALIGN_TOP;

  /* Tools region */
  region = static_cast<ARegion *>(MEM_callocN(sizeof(ARegion), "tools region for file"));
  BLI_addtail(&sfile->regionbase, region);
  region->regiontype = RGN_TYPE_TOOLS;
  region->alignment = RGN_ALIGN_LEFT;

  /* ui list region */
  region = static_cast<ARegion *>(MEM_callocN(sizeof(ARegion), "ui region for file"));
  BLI_addtail(&sfile->regionbase, region);
  region->regiontype = RGN_TYPE_UI;
  region->alignment = RGN_ALIGN_TOP;
  region->flag = RGN_FLAG_DYNAMIC_SIZE;

  /* execute region */
  region = static_cast<ARegion *>(MEM_callocN(sizeof(ARegion), "execute region for file"));
  BLI_addtail(&sfile->regionbase, region);
  region->regiontype = RGN_TYPE_EXECUTE;
  region->alignment = RGN_ALIGN_BOTTOM;
  region->flag = RGN_FLAG_DYNAMIC_SIZE;

  /* tools props region */
  region = static_cast<ARegion *>(MEM_callocN(sizeof(ARegion), "tool props for file"));
  BLI_addtail(&sfile->regionbase, region);
  region->regiontype = RGN_TYPE_TOOL_PROPS;
  region->alignment = RGN_ALIGN_RIGHT;
  region->flag = RGN_FLAG_HIDDEN;

  /* main region */
  region = static_cast<ARegion *>(MEM_callocN(sizeof(ARegion), "main region for file"));
  BLI_addtail(&sfile->regionbase, region);
  region->regiontype = RGN_TYPE_WINDOW;
  region->v2d.scroll = (V2D_SCROLL_RIGHT | V2D_SCROLL_BOTTOM);
  region->v2d.align = (V2D_ALIGN_NO_NEG_X | V2D_ALIGN_NO_POS_Y);
  region->v2d.keepzoom = (V2D_LOCKZOOM_X | V2D_LOCKZOOM_Y | V2D_LIMITZOOM | V2D_KEEPASPECT);
  region->v2d.keeptot = V2D_KEEPTOT_STRICT;
  region->v2d.minzoom = region->v2d.maxzoom = 1.0f;

  return (SpaceLink *)sfile;
}

/* Doesn't free the space-link itself. */
static void file_free(SpaceLink *sl)
{
  SpaceFile *sfile = (SpaceFile *)sl;

  BLI_assert(sfile->previews_timer == nullptr);

  if (sfile->files) {
    /* XXX would need to do thumbnails_stop here, but no context available */
    filelist_freelib(sfile->files);
    filelist_free(sfile->files);
    MEM_freeN(sfile->files);
    sfile->files = nullptr;
  }

  folder_history_list_free(sfile);

  MEM_SAFE_FREE(sfile->params);
  MEM_SAFE_FREE(sfile->asset_params);
  MEM_SAFE_FREE(sfile->runtime);

  MEM_SAFE_FREE(sfile->layout);
}

/* spacetype; init callback, area size changes, screen set, etc */
static void file_init(wmWindowManager * /*wm*/, ScrArea *area)
{
  SpaceFile *sfile = (SpaceFile *)area->spacedata.first;

  if (sfile->layout) {
    sfile->layout->dirty = true;
  }

  if (sfile->runtime == nullptr) {
    sfile->runtime = static_cast<SpaceFile_Runtime *>(
        MEM_callocN(sizeof(*sfile->runtime), __func__));
  }
  /* Validate the params right after file read. */
  fileselect_refresh_params(sfile);
}

static void file_exit(wmWindowManager *wm, ScrArea *area)
{
  SpaceFile *sfile = (SpaceFile *)area->spacedata.first;

  if (sfile->previews_timer) {
    WM_event_timer_remove_notifier(wm, nullptr, sfile->previews_timer);
    sfile->previews_timer = nullptr;
  }

  ED_fileselect_exit(wm, sfile);
}

static SpaceLink *file_duplicate(SpaceLink *sl)
{
  SpaceFile *sfileo = (SpaceFile *)sl;
  SpaceFile *sfilen = static_cast<SpaceFile *>(MEM_dupallocN(sl));

  /* clear or remove stuff from old */
  sfilen->op = nullptr; /* file window doesn't own operators */
  sfilen->runtime = nullptr;

  sfilen->previews_timer = nullptr;
  sfilen->smoothscroll_timer = nullptr;

  FileSelectParams *active_params_old = ED_fileselect_get_active_params(sfileo);
  if (active_params_old) {
    sfilen->files = filelist_new(active_params_old->type);
    filelist_setdir(sfilen->files, active_params_old->dir);
  }

  if (sfileo->params) {
    sfilen->params = static_cast<FileSelectParams *>(MEM_dupallocN(sfileo->params));
  }
  if (sfileo->asset_params) {
    sfilen->asset_params = static_cast<FileAssetSelectParams *>(
        MEM_dupallocN(sfileo->asset_params));
  }

  sfilen->folder_histories = folder_history_list_duplicate(&sfileo->folder_histories);

  if (sfileo->layout) {
    sfilen->layout = static_cast<FileLayout *>(MEM_dupallocN(sfileo->layout));
  }
  return (SpaceLink *)sfilen;
}

static void file_refresh(const bContext *C, ScrArea *area)
{
  wmWindowManager *wm = CTX_wm_manager(C);
  wmWindow *win = CTX_wm_window(C);
  SpaceFile *sfile = CTX_wm_space_file(C);
  FileSelectParams *params = ED_fileselect_ensure_active_params(sfile);
  FileAssetSelectParams *asset_params = ED_fileselect_get_asset_params(sfile);
  struct FSMenu *fsmenu = ED_fsmenu_get();

  fileselect_refresh_params(sfile);
  folder_history_list_ensure_for_active_browse_mode(sfile);

  if (sfile->files && (sfile->tags & FILE_TAG_REBUILD_MAIN_FILES) &&
      filelist_needs_reset_on_main_changes(sfile->files))
  {
    filelist_tag_force_reset_mainfiles(sfile->files);
  }
  sfile->tags &= ~FILE_TAG_REBUILD_MAIN_FILES;

  if (!sfile->files) {
    sfile->files = filelist_new(params->type);
    params->highlight_file = -1; /* added this so it opens nicer (ton) */
  }

  if (ED_fileselect_is_asset_browser(sfile)) {
    /* Ask the asset code for appropriate ID filter flags for the supported assets, and mask others
     * out. */
    params->filter_id &= ED_asset_types_supported_as_filter_flags();
  }

  filelist_settype(sfile->files, params->type);
  filelist_setdir(sfile->files, params->dir);
  filelist_setrecursion(sfile->files, params->recursion_level);
  filelist_setsorting(sfile->files, params->sort, params->flag & FILE_SORT_INVERT);
  filelist_setlibrary(sfile->files, asset_params ? &asset_params->asset_library_ref : nullptr);
  filelist_setfilter_options(
      sfile->files,
      (params->flag & FILE_FILTER) != 0,
      (params->flag & FILE_HIDE_DOT) != 0,
      true, /* Just always hide parent, prefer to not add an extra user option for this. */
      params->filter,
      params->filter_id,
      (params->flag & FILE_ASSETS_ONLY) != 0,
      params->filter_glob,
      params->filter_search);
  if (asset_params) {
    filelist_set_asset_catalog_filter_options(
        sfile->files,
        eFileSel_Params_AssetCatalogVisibility(asset_params->asset_catalog_visibility),
        &asset_params->catalog_id);
  }

  if (ED_fileselect_is_asset_browser(sfile)) {
    const bool use_asset_indexer = !USER_EXPERIMENTAL_TEST(&U, no_asset_indexing);
    filelist_setindexer(sfile->files,
                        use_asset_indexer ? &file_indexer_asset : &file_indexer_noop);
  }

  /* Update the active indices of bookmarks & co. */
  sfile->systemnr = fsmenu_get_active_indices(fsmenu, FS_CATEGORY_SYSTEM, params->dir);
  sfile->system_bookmarknr = fsmenu_get_active_indices(
      fsmenu, FS_CATEGORY_SYSTEM_BOOKMARKS, params->dir);
  sfile->bookmarknr = fsmenu_get_active_indices(fsmenu, FS_CATEGORY_BOOKMARKS, params->dir);
  sfile->recentnr = fsmenu_get_active_indices(fsmenu, FS_CATEGORY_RECENT, params->dir);

  if (filelist_needs_force_reset(sfile->files)) {
    filelist_readjob_stop(sfile->files, wm);
    filelist_clear_from_reset_tag(sfile->files);
  }

  if (filelist_needs_reading(sfile->files)) {
    if (!filelist_pending(sfile->files)) {
      filelist_readjob_start(sfile->files, NC_SPACE | ND_SPACE_FILE_LIST, C);
    }
  }

  filelist_sort(sfile->files);
  filelist_filter(sfile->files);

  if (params->display == FILE_IMGDISPLAY) {
    filelist_cache_previews_set(sfile->files, true);
  }
  else {
    filelist_cache_previews_set(sfile->files, false);
    if (sfile->previews_timer) {
      WM_event_timer_remove_notifier(wm, win, sfile->previews_timer);
      sfile->previews_timer = nullptr;
    }
  }

  if (params->rename_flag != 0) {
    file_params_renamefile_activate(sfile, params);
  }

  if (sfile->layout) {
    sfile->layout->dirty = true;
  }

  if (area) {
    ARegion *region_props = BKE_area_find_region_type(area, RGN_TYPE_TOOL_PROPS);
    const short region_flag_old = region_props->flag;
    if (!(region_props->v2d.flag & V2D_IS_INIT)) {
      if (ED_fileselect_is_asset_browser(sfile)) {
        /* Hide by default in asset browser. */
        region_props->flag |= RGN_FLAG_HIDDEN;
      }
      else {
        if (params->flag & FILE_HIDE_TOOL_PROPS) {
          region_props->flag |= RGN_FLAG_HIDDEN;
        }
        else {
          region_props->flag &= ~RGN_FLAG_HIDDEN;
        }
      }
    }
    if (region_flag_old != region_props->flag) {
      ED_region_visibility_change_update((bContext *)C, area, region_props);
    }
  }

  ED_area_tag_redraw(area);
}

void file_on_reload_callback_register(SpaceFile *sfile,
                                      onReloadFn callback,
                                      onReloadFnData custom_data)
{
  sfile->runtime->on_reload = callback;
  sfile->runtime->on_reload_custom_data = custom_data;
}

static void file_on_reload_callback_call(SpaceFile *sfile)
{
  if (sfile->runtime->on_reload == nullptr) {
    return;
  }

  sfile->runtime->on_reload(sfile, sfile->runtime->on_reload_custom_data);

  sfile->runtime->on_reload = nullptr;
  sfile->runtime->on_reload_custom_data = nullptr;
}

static void file_reset_filelist_showing_main_data(ScrArea *area, SpaceFile *sfile)
{
  if (sfile->files && filelist_needs_reset_on_main_changes(sfile->files)) {
    filelist_tag_force_reset_mainfiles(sfile->files);
    ED_area_tag_refresh(area);
  }
}

static void file_listener(const wmSpaceTypeListenerParams *listener_params)
{
  ScrArea *area = listener_params->area;
  const wmNotifier *wmn = listener_params->notifier;
  SpaceFile *sfile = (SpaceFile *)area->spacedata.first;

  /* context changes */
  switch (wmn->category) {
    case NC_SPACE:
      switch (wmn->data) {
        case ND_SPACE_FILE_LIST:
          ED_area_tag_refresh(area);
          break;
        case ND_SPACE_FILE_PARAMS:
          ED_area_tag_refresh(area);
          break;
        case ND_SPACE_FILE_PREVIEW:
          if (sfile->files && filelist_cache_previews_update(sfile->files)) {
            ED_area_tag_refresh(area);
          }
          break;
        case ND_SPACE_ASSET_PARAMS:
          if (sfile->browse_mode == FILE_BROWSE_MODE_ASSETS) {
            ED_area_tag_refresh(area);
          }
          break;
        case ND_SPACE_CHANGED:
          /* If the space was just turned into a file/asset browser, the file-list may need to be
           * updated to reflect latest changes in main data. */
          file_reset_filelist_showing_main_data(area, sfile);
          break;
      }
      switch (wmn->action) {
        case NA_JOB_FINISHED:
          file_on_reload_callback_call(sfile);
          break;
      }
      break;
    case NC_ID: {
      switch (wmn->action) {
        case NA_RENAME: {
          const ID *active_file_id = ED_fileselect_active_asset_get(sfile);
          /* If a renamed ID is active in the file browser, update scrolling to keep it in view. */
          if (active_file_id && (wmn->reference == active_file_id)) {
            FileSelectParams *params = ED_fileselect_get_active_params(sfile);
            params->rename_id = active_file_id;
            file_params_invoke_rename_postscroll(
                static_cast<wmWindowManager *>(G_MAIN->wm.first), listener_params->window, sfile);
          }

          /* Force list to update sorting (with a full reset for now). */
          file_reset_filelist_showing_main_data(area, sfile);
          break;
        }
      }
      break;
    }
    case NC_ASSET: {
      switch (wmn->action) {
        case NA_SELECTED:
        case NA_ACTIVATED:
          ED_area_tag_refresh(area);
          break;
        case NA_ADDED:
        case NA_REMOVED:
        case NA_EDITED:
          file_reset_filelist_showing_main_data(area, sfile);
          break;
      }
      break;
    }
  }
}

/* add handlers, stuff you only do once or on area/region changes */
static void file_main_region_init(wmWindowManager *wm, ARegion *region)
{
  wmKeyMap *keymap;

  UI_view2d_region_reinit(&region->v2d, V2D_COMMONVIEW_LIST, region->winx, region->winy);

  /* own keymaps */
  keymap = WM_keymap_ensure(wm->defaultconf, "File Browser", SPACE_FILE, 0);
  WM_event_add_keymap_handler_v2d_mask(&region->handlers, keymap);

  keymap = WM_keymap_ensure(wm->defaultconf, "File Browser Main", SPACE_FILE, 0);
  WM_event_add_keymap_handler_v2d_mask(&region->handlers, keymap);
}

static void file_main_region_listener(const wmRegionListenerParams *listener_params)
{
  ARegion *region = listener_params->region;
  const wmNotifier *wmn = listener_params->notifier;

  /* context changes */
  switch (wmn->category) {
    case NC_SPACE:
      switch (wmn->data) {
        case ND_SPACE_FILE_LIST:
          ED_region_tag_redraw(region);
          break;
        case ND_SPACE_FILE_PARAMS:
          ED_region_tag_redraw(region);
          break;
      }
      break;
    case NC_ID:
      if (ELEM(wmn->action, NA_SELECTED, NA_ACTIVATED, NA_RENAME)) {
        ED_region_tag_redraw(region);
      }
      break;
  }
}

static void file_main_region_message_subscribe(const wmRegionMessageSubscribeParams *params)
{
  struct wmMsgBus *mbus = params->message_bus;
  bScreen *screen = params->screen;
  ScrArea *area = params->area;
  ARegion *region = params->region;
  SpaceFile *sfile = static_cast<SpaceFile *>(area->spacedata.first);

  FileSelectParams *file_params = ED_fileselect_ensure_active_params(sfile);
  /* This is a bit odd that a region owns the subscriber for an area,
   * keep for now since all subscribers for WM are regions.
   * May be worth re-visiting later. */
  wmMsgSubscribeValue msg_sub_value_area_tag_refresh{};
  msg_sub_value_area_tag_refresh.owner = region;
  msg_sub_value_area_tag_refresh.user_data = area;
  msg_sub_value_area_tag_refresh.notify = ED_area_do_msg_notify_tag_refresh;

  /* SpaceFile itself. */
  {
    PointerRNA ptr;
    RNA_pointer_create(&screen->id, &RNA_SpaceFileBrowser, sfile, &ptr);

    /* All properties for this space type. */
    WM_msg_subscribe_rna(mbus, &ptr, nullptr, &msg_sub_value_area_tag_refresh, __func__);
  }

  /* FileSelectParams */
  {
    PointerRNA ptr;
    RNA_pointer_create(&screen->id, &RNA_FileSelectParams, file_params, &ptr);

    /* All properties for this space type. */
    WM_msg_subscribe_rna(mbus, &ptr, nullptr, &msg_sub_value_area_tag_refresh, __func__);
  }

  /* Experimental Asset Browser features option. */
  {
    PointerRNA ptr;
    RNA_pointer_create(nullptr, &RNA_PreferencesExperimental, &U.experimental, &ptr);
    PropertyRNA *prop = RNA_struct_find_property(&ptr, "use_extended_asset_browser");

    /* All properties for this space type. */
    WM_msg_subscribe_rna(mbus, &ptr, prop, &msg_sub_value_area_tag_refresh, __func__);
  }
}

static bool file_main_region_needs_refresh_before_draw(SpaceFile *sfile)
{
  /* Needed, because filelist is not initialized on loading */
  if (!sfile->files || filelist_needs_reading(sfile->files)) {
    return true;
  }

  /* File reading tagged the space because main data changed that may require a filelist reset. */
  if (filelist_needs_reset_on_main_changes(sfile->files) &&
      (sfile->tags & FILE_TAG_REBUILD_MAIN_FILES))
  {
    return true;
  }

  return false;
}

static void file_main_region_draw(const bContext *C, ARegion *region)
{
  /* draw entirely, view changes should be handled here */
  SpaceFile *sfile = CTX_wm_space_file(C);
  FileSelectParams *params = ED_fileselect_ensure_active_params(sfile);

  View2D *v2d = &region->v2d;

  if (file_main_region_needs_refresh_before_draw(sfile)) {
    file_refresh(C, nullptr);
  }

  /* clear and setup matrix */
  UI_ThemeClearColor(TH_BACK);

  /* Allow dynamically sliders to be set, saves notifiers etc. */

  if (params->display == FILE_IMGDISPLAY) {
    v2d->scroll = V2D_SCROLL_RIGHT;
    v2d->keepofs &= ~V2D_LOCKOFS_Y;
    v2d->keepofs |= V2D_LOCKOFS_X;
  }
  else if (params->display == FILE_VERTICALDISPLAY) {
    v2d->scroll = V2D_SCROLL_RIGHT;
    v2d->keepofs &= ~V2D_LOCKOFS_Y;
    v2d->keepofs |= V2D_LOCKOFS_X;
  }
  else {
    v2d->scroll = V2D_SCROLL_BOTTOM;
    v2d->keepofs &= ~V2D_LOCKOFS_X;
    v2d->keepofs |= V2D_LOCKOFS_Y;

    /* XXX this happens on scaling down Screen (like from startup.blend) */
    /* view2d has no type specific for file-window case, which doesn't scroll vertically. */
    if (v2d->cur.ymax < 0) {
      v2d->cur.ymin -= v2d->cur.ymax;
      v2d->cur.ymax = 0;
    }
  }
  /* v2d has initialized flag, so this call will only set the mask correct */
  UI_view2d_region_reinit(v2d, V2D_COMMONVIEW_LIST, region->winx, region->winy);

  /* sets tile/border settings in sfile */
  file_calc_previews(C, region);

  /* set view */
  UI_view2d_view_ortho(v2d);

  /* on first read, find active file */
  if (params->highlight_file == -1) {
    wmEvent *event = CTX_wm_window(C)->eventstate;
    file_highlight_set(sfile, region, event->xy[0], event->xy[1]);
  }

  if (!file_draw_hint_if_invalid(C, sfile, region)) {
    file_draw_list(C, region);
  }

  /* reset view matrix */
  UI_view2d_view_restore(C);

  /* scrollers */
  rcti view_rect;
  ED_fileselect_layout_maskrect(sfile->layout, v2d, &view_rect);
  UI_view2d_scrollers_draw(v2d, &view_rect);
}

static void file_operatortypes()
{
  WM_operatortype_append(FILE_OT_select);
  WM_operatortype_append(FILE_OT_select_walk);
  WM_operatortype_append(FILE_OT_select_all);
  WM_operatortype_append(FILE_OT_select_box);
  WM_operatortype_append(FILE_OT_select_bookmark);
  WM_operatortype_append(FILE_OT_highlight);
  WM_operatortype_append(FILE_OT_sort_column_ui_context);
  WM_operatortype_append(FILE_OT_execute);
  WM_operatortype_append(FILE_OT_mouse_execute);
  WM_operatortype_append(FILE_OT_cancel);
  WM_operatortype_append(FILE_OT_parent);
  WM_operatortype_append(FILE_OT_previous);
  WM_operatortype_append(FILE_OT_next);
  WM_operatortype_append(FILE_OT_refresh);
  WM_operatortype_append(FILE_OT_bookmark_add);
  WM_operatortype_append(FILE_OT_bookmark_delete);
  WM_operatortype_append(FILE_OT_bookmark_cleanup);
  WM_operatortype_append(FILE_OT_bookmark_move);
  WM_operatortype_append(FILE_OT_reset_recent);
  WM_operatortype_append(FILE_OT_hidedot);
  WM_operatortype_append(FILE_OT_filenum);
  WM_operatortype_append(FILE_OT_directory_new);
  WM_operatortype_append(FILE_OT_delete);
  WM_operatortype_append(FILE_OT_rename);
  WM_operatortype_append(FILE_OT_smoothscroll);
  WM_operatortype_append(FILE_OT_filepath_drop);
  WM_operatortype_append(FILE_OT_start_filter);
  WM_operatortype_append(FILE_OT_edit_directory_path);
  WM_operatortype_append(FILE_OT_view_selected);
  WM_operatortype_append(FILE_OT_external_operation);
}

/* NOTE: do not add .blend file reading on this level */
static void file_keymap(wmKeyConfig *keyconf)
{
  /* keys for all regions */
  WM_keymap_ensure(keyconf, "File Browser", SPACE_FILE, 0);

  /* keys for main region */
  WM_keymap_ensure(keyconf, "File Browser Main", SPACE_FILE, 0);

  /* keys for button region (top) */
  WM_keymap_ensure(keyconf, "File Browser Buttons", SPACE_FILE, 0);
}

static bool file_ui_region_poll(const RegionPollParams *params)
{
  const SpaceFile *sfile = (SpaceFile *)params->area->spacedata.first;
  /* Always visible except when browsing assets. */
  return sfile->browse_mode != FILE_BROWSE_MODE_ASSETS;
}

static bool file_tool_props_region_poll(const RegionPollParams *params)
{
  const SpaceFile *sfile = (SpaceFile *)params->area->spacedata.first;
  return (sfile->browse_mode == FILE_BROWSE_MODE_ASSETS) || (sfile->op != nullptr);
}

static bool file_execution_region_poll(const RegionPollParams *params)
{
  const SpaceFile *sfile = (SpaceFile *)params->area->spacedata.first;
  return sfile->op != nullptr;
}

static void file_tools_region_init(wmWindowManager *wm, ARegion *region)
{
  wmKeyMap *keymap;

  region->v2d.scroll = V2D_SCROLL_RIGHT | V2D_SCROLL_VERTICAL_HIDE;
  ED_region_panels_init(wm, region);

  /* own keymaps */
  keymap = WM_keymap_ensure(wm->defaultconf, "File Browser", SPACE_FILE, 0);
  WM_event_add_keymap_handler_v2d_mask(&region->handlers, keymap);
}

static void file_tools_region_draw(const bContext *C, ARegion *region)
{
  ED_region_panels(C, region);
}

static void file_tools_region_listener(const wmRegionListenerParams *listener_params)
{
  const wmNotifier *wmn = listener_params->notifier;
  ARegion *region = listener_params->region;

  switch (wmn->category) {
    case NC_SCENE:
      if (ELEM(wmn->data, ND_MODE)) {
        ED_region_tag_redraw(region);
      }
      break;
  }
}

static void file_tool_props_region_listener(const wmRegionListenerParams *listener_params)
{
  const wmNotifier *wmn = listener_params->notifier;
  ARegion *region = listener_params->region;

  switch (wmn->category) {
    case NC_ID:
      if (ELEM(wmn->action, NA_RENAME)) {
        /* In case the filelist shows ID names. */
        ED_region_tag_redraw(region);
      }
      break;
    case NC_SCENE:
      if (ELEM(wmn->data, ND_MODE)) {
        ED_region_tag_redraw(region);
      }
      break;
  }
}

/* add handlers, stuff you only do once or on area/region changes */
static void file_header_region_init(wmWindowManager *wm, ARegion *region)
{
  wmKeyMap *keymap;

  ED_region_header_init(region);

  keymap = WM_keymap_ensure(wm->defaultconf, "File Browser", SPACE_FILE, 0);
  WM_event_add_keymap_handler_v2d_mask(&region->handlers, keymap);
}

static void file_header_region_draw(const bContext *C, ARegion *region)
{
  ED_region_header(C, region);
}

/* add handlers, stuff you only do once or on area/region changes */
static void file_ui_region_init(wmWindowManager *wm, ARegion *region)
{
  wmKeyMap *keymap;

  ED_region_panels_init(wm, region);
  region->v2d.keepzoom |= V2D_LOCKZOOM_X | V2D_LOCKZOOM_Y;

  /* own keymap */
  keymap = WM_keymap_ensure(wm->defaultconf, "File Browser", SPACE_FILE, 0);
  WM_event_add_keymap_handler_v2d_mask(&region->handlers, keymap);

  keymap = WM_keymap_ensure(wm->defaultconf, "File Browser Buttons", SPACE_FILE, 0);
  WM_event_add_keymap_handler_v2d_mask(&region->handlers, keymap);
}

static void file_ui_region_draw(const bContext *C, ARegion *region)
{
  ED_region_panels(C, region);
}

static void file_execution_region_init(wmWindowManager *wm, ARegion *region)
{
  wmKeyMap *keymap;

  ED_region_panels_init(wm, region);
  region->v2d.keepzoom |= V2D_LOCKZOOM_X | V2D_LOCKZOOM_Y;

  /* own keymap */
  keymap = WM_keymap_ensure(wm->defaultconf, "File Browser", SPACE_FILE, 0);
  WM_event_add_keymap_handler_v2d_mask(&region->handlers, keymap);
}

static void file_execution_region_draw(const bContext *C, ARegion *region)
{
  ED_region_panels(C, region);
}

static void file_ui_region_listener(const wmRegionListenerParams *listener_params)
{
  ARegion *region = listener_params->region;
  const wmNotifier *wmn = listener_params->notifier;

  /* context changes */
  switch (wmn->category) {
    case NC_SPACE:
      switch (wmn->data) {
        case ND_SPACE_FILE_LIST:
          ED_region_tag_redraw(region);
          break;
      }
      break;
  }
}

static bool filepath_drop_poll(bContext *C, wmDrag *drag, const wmEvent * /*event*/)
{
  if (drag->type == WM_DRAG_PATH) {
    SpaceFile *sfile = CTX_wm_space_file(C);
    if (sfile) {
      return true;
    }
  }
  return false;
}

static void filepath_drop_copy(bContext * /*C*/, wmDrag *drag, wmDropBox *drop)
{
  RNA_string_set(drop->ptr, "filepath", WM_drag_get_path(drag));
}

/* region dropbox definition */
static void file_dropboxes()
{
  ListBase *lb = WM_dropboxmap_find("Window", SPACE_EMPTY, RGN_TYPE_WINDOW);

  WM_dropbox_add(
      lb, "FILE_OT_filepath_drop", filepath_drop_poll, filepath_drop_copy, nullptr, nullptr);
}

static int file_space_subtype_get(ScrArea *area)
{
  SpaceFile *sfile = static_cast<SpaceFile *>(area->spacedata.first);
  return sfile->browse_mode;
}

static void file_space_subtype_set(ScrArea *area, int value)
{
  SpaceFile *sfile = static_cast<SpaceFile *>(area->spacedata.first);
  /* Force re-init. */
  LISTBASE_FOREACH (ARegion *, region, &area->regionbase) {
    region->v2d.flag &= ~V2D_IS_INIT;
  }
  sfile->browse_mode = value;
}

static void file_space_subtype_item_extend(bContext * /*C*/, EnumPropertyItem **item, int *totitem)
{
  RNA_enum_items_add(item, totitem, rna_enum_space_file_browse_mode_items);
}

const char *file_context_dir[] = {
    "active_file",
    "selected_files",
    "asset_library_ref",
    "selected_asset_files",
    "id",
    "selected_ids",
    nullptr,
};

static int /*eContextResult*/ file_context(const bContext *C,
                                           const char *member,
                                           bContextDataResult *result)
{
  bScreen *screen = CTX_wm_screen(C);
  SpaceFile *sfile = CTX_wm_space_file(C);
  FileSelectParams *params = ED_fileselect_get_active_params(sfile);

  BLI_assert(!ED_area_is_global(CTX_wm_area(C)));

  if (CTX_data_dir(member)) {
    CTX_data_dir_set(result, file_context_dir);
    return CTX_RESULT_OK;
  }

  /* The following member checks return file-list data, check if that needs refreshing first. */
  if (file_main_region_needs_refresh_before_draw(sfile)) {
    return CTX_RESULT_NO_DATA;
  }

  if (CTX_data_equals(member, "active_file")) {
    FileDirEntry *file = filelist_file(sfile->files, params->active_file);
    if (file == nullptr) {
      return CTX_RESULT_NO_DATA;
    }

    CTX_data_pointer_set(result, &screen->id, &RNA_FileSelectEntry, file);
    return CTX_RESULT_OK;
  }
  if (CTX_data_equals(member, "selected_files")) {
    const int num_files_filtered = filelist_files_ensure(sfile->files);

    for (int file_index = 0; file_index < num_files_filtered; file_index++) {
      if (filelist_entry_is_selected(sfile->files, file_index)) {
        FileDirEntry *entry = filelist_file(sfile->files, file_index);
        CTX_data_list_add(result, &screen->id, &RNA_FileSelectEntry, entry);
      }
    }

    CTX_data_type_set(result, CTX_DATA_TYPE_COLLECTION);
    return CTX_RESULT_OK;
  }

  if (CTX_data_equals(member, "asset_library_ref")) {
    FileAssetSelectParams *asset_params = ED_fileselect_get_asset_params(sfile);
    if (!asset_params) {
      return CTX_RESULT_NO_DATA;
    }

    CTX_data_pointer_set(
        result, &screen->id, &RNA_AssetLibraryReference, &asset_params->asset_library_ref);
    return CTX_RESULT_OK;
  }
  /** TODO temporary AssetHandle design: For now this returns the file entry. Would be better if it
   * was `"selected_assets"` and returned the assets (e.g. as `AssetHandle`) directly. See comment
   * for #AssetHandle for more info. */
  if (CTX_data_equals(member, "selected_asset_files")) {
    const int num_files_filtered = filelist_files_ensure(sfile->files);

    for (int file_index = 0; file_index < num_files_filtered; file_index++) {
      if (filelist_entry_is_selected(sfile->files, file_index)) {
        FileDirEntry *entry = filelist_file(sfile->files, file_index);
        if (entry->asset) {
          CTX_data_list_add(result, &screen->id, &RNA_FileSelectEntry, entry);
        }
      }
    }

    CTX_data_type_set(result, CTX_DATA_TYPE_COLLECTION);
    return CTX_RESULT_OK;
  }
  if (CTX_data_equals(member, "id")) {
    const FileDirEntry *file = filelist_file(sfile->files, params->active_file);
    if (file == nullptr) {
      return CTX_RESULT_NO_DATA;
    }

    ID *id = filelist_file_get_id(file);
    if (id == nullptr) {
      return CTX_RESULT_NO_DATA;
    }

    CTX_data_id_pointer_set(result, id);
    return CTX_RESULT_OK;
  }
  if (CTX_data_equals(member, "selected_ids")) {
    const int num_files_filtered = filelist_files_ensure(sfile->files);

    for (int file_index = 0; file_index < num_files_filtered; file_index++) {
      if (!filelist_entry_is_selected(sfile->files, file_index)) {
        continue;
      }
      ID *id = filelist_entry_get_id(sfile->files, file_index);
      if (!id) {
        continue;
      }

      CTX_data_id_list_add(result, id);
    }

    CTX_data_type_set(result, CTX_DATA_TYPE_COLLECTION);
    return CTX_RESULT_OK;
  }

  return CTX_RESULT_MEMBER_NOT_FOUND;
}

static void file_id_remap(ScrArea *area, SpaceLink *sl, const IDRemapper * /*mappings*/)
{
  SpaceFile *sfile = (SpaceFile *)sl;

  /* If the file shows main data (IDs), tag it for reset.
   * Full reset of the file list if main data was changed, don't even attempt remap pointers.
   * We could give file list types a id-remap callback, but it's probably not worth it.
   * Refreshing local file lists is relatively cheap. */
  file_reset_filelist_showing_main_data(area, sfile);
}

static void file_space_blend_read_data(BlendDataReader *reader, SpaceLink *sl)
{
  SpaceFile *sfile = (SpaceFile *)sl;

  /* this sort of info is probably irrelevant for reloading...
   * plus, it isn't saved to files yet!
   */
  sfile->folders_prev = sfile->folders_next = nullptr;
  BLI_listbase_clear(&sfile->folder_histories);
  sfile->files = nullptr;
  sfile->layout = nullptr;
  sfile->op = nullptr;
  sfile->previews_timer = nullptr;
  sfile->tags = 0;
  sfile->runtime = nullptr;
  BLO_read_data_address(reader, &sfile->params);
  BLO_read_data_address(reader, &sfile->asset_params);
  if (sfile->params) {
    sfile->params->rename_id = nullptr;
  }
  if (sfile->asset_params) {
    sfile->asset_params->base_params.rename_id = nullptr;
  }
}

static void file_space_blend_read_lib(BlendLibReader * /*reader*/,
                                      ID * /*parent_id*/,
                                      SpaceLink *sl)
{
  SpaceFile *sfile = (SpaceFile *)sl;
  sfile->tags |= FILE_TAG_REBUILD_MAIN_FILES;
}

static void file_space_blend_write(BlendWriter *writer, SpaceLink *sl)
{
  SpaceFile *sfile = (SpaceFile *)sl;

  BLO_write_struct(writer, SpaceFile, sl);
  if (sfile->params) {
    BLO_write_struct(writer, FileSelectParams, sfile->params);
  }
  if (sfile->asset_params) {
    BLO_write_struct(writer, FileAssetSelectParams, sfile->asset_params);
  }
}

void ED_spacetype_file()
{
  SpaceType *st = static_cast<SpaceType *>(MEM_callocN(sizeof(SpaceType), "spacetype file"));
  ARegionType *art;

  st->spaceid = SPACE_FILE;
  STRNCPY(st->name, "File");

  st->create = file_create;
  st->free = file_free;
  st->init = file_init;
  st->exit = file_exit;
  st->duplicate = file_duplicate;
  st->refresh = file_refresh;
  st->listener = file_listener;
  st->operatortypes = file_operatortypes;
  st->keymap = file_keymap;
  st->dropboxes = file_dropboxes;
  st->space_subtype_item_extend = file_space_subtype_item_extend;
  st->space_subtype_get = file_space_subtype_get;
  st->space_subtype_set = file_space_subtype_set;
  st->context = file_context;
  st->id_remap = file_id_remap;
  st->blend_read_data = file_space_blend_read_data;
  st->blend_read_lib = file_space_blend_read_lib;
  st->blend_write = file_space_blend_write;

  /* regions: main window */
  art = static_cast<ARegionType *>(MEM_callocN(sizeof(ARegionType), "spacetype file region"));
  art->regionid = RGN_TYPE_WINDOW;
  art->init = file_main_region_init;
  art->draw = file_main_region_draw;
  art->listener = file_main_region_listener;
  art->message_subscribe = file_main_region_message_subscribe;
  art->keymapflag = ED_KEYMAP_UI | ED_KEYMAP_VIEW2D;
  BLI_addhead(&st->regiontypes, art);

  /* regions: header */
  art = static_cast<ARegionType *>(MEM_callocN(sizeof(ARegionType), "spacetype file region"));
  art->regionid = RGN_TYPE_HEADER;
  art->prefsizey = HEADERY;
  art->keymapflag = ED_KEYMAP_UI | ED_KEYMAP_VIEW2D | ED_KEYMAP_HEADER;
  art->init = file_header_region_init;
  art->draw = file_header_region_draw;
  // art->listener = file_header_region_listener;
  BLI_addhead(&st->regiontypes, art);

  /* regions: ui */
  art = static_cast<ARegionType *>(MEM_callocN(sizeof(ARegionType), "spacetype file region"));
  art->regionid = RGN_TYPE_UI;
  art->keymapflag = ED_KEYMAP_UI;
  art->poll = file_ui_region_poll;
  art->listener = file_ui_region_listener;
  art->init = file_ui_region_init;
  art->draw = file_ui_region_draw;
  BLI_addhead(&st->regiontypes, art);

  /* regions: execution */
  art = static_cast<ARegionType *>(MEM_callocN(sizeof(ARegionType), "spacetype file region"));
  art->regionid = RGN_TYPE_EXECUTE;
  art->keymapflag = ED_KEYMAP_UI;
  art->poll = file_execution_region_poll;
  art->listener = file_ui_region_listener;
  art->init = file_execution_region_init;
  art->draw = file_execution_region_draw;
  BLI_addhead(&st->regiontypes, art);
  file_execute_region_panels_register(art);

  /* regions: channels (directories) */
  art = static_cast<ARegionType *>(MEM_callocN(sizeof(ARegionType), "spacetype file region"));
  art->regionid = RGN_TYPE_TOOLS;
  art->prefsizex = 240;
  art->prefsizey = 60;
  art->keymapflag = ED_KEYMAP_UI;
  art->listener = file_tools_region_listener;
  art->init = file_tools_region_init;
  art->draw = file_tools_region_draw;
  BLI_addhead(&st->regiontypes, art);
  file_tools_region_panels_register(art);

  /* regions: tool properties */
  art = static_cast<ARegionType *>(
      MEM_callocN(sizeof(ARegionType), "spacetype file operator region"));
  art->regionid = RGN_TYPE_TOOL_PROPS;
  art->prefsizex = 240;
  art->prefsizey = 60;
  art->keymapflag = ED_KEYMAP_UI;
  art->poll = file_tool_props_region_poll;
  art->listener = file_tool_props_region_listener;
  art->init = file_tools_region_init;
  art->draw = file_tools_region_draw;
  BLI_addhead(&st->regiontypes, art);
  file_tool_props_region_panels_register(art);
  file_external_operations_menu_register();

  BKE_spacetype_register(st);
}

void ED_file_init()
{
  ED_file_read_bookmarks();

  if (G.background == false) {
    filelist_init_icons();
  }

  IMB_thumb_makedirs();
}

void ED_file_exit()
{
  fsmenu_free();

  if (G.background == false) {
    filelist_free_icons();
  }
}

void ED_file_read_bookmarks()
{
  const char *const cfgdir = BKE_appdir_folder_id(BLENDER_USER_CONFIG, nullptr);

  fsmenu_free();

  fsmenu_read_system(ED_fsmenu_get(), true);

  if (cfgdir) {
    char filepath[FILE_MAX];
    BLI_path_join(filepath, sizeof(filepath), cfgdir, BLENDER_BOOKMARK_FILE);
    fsmenu_read_bookmarks(ED_fsmenu_get(), filepath);
  }
}

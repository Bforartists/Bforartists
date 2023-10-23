/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup edasset
 *
 * General asset shelf code, mostly region callbacks, drawing and context stuff.
 */

#include <algorithm>

#include "AS_asset_catalog_path.hh"
#include "AS_asset_library.hh"

#include "BLI_string.h"

#include "BKE_context.h"
#include "BKE_main.h"
#include "BKE_screen.hh"

#include "BLT_translation.h"

#include "DNA_screen_types.h"

#include "ED_asset_list.h"
#include "ED_screen.hh"

#include "RNA_prototypes.h"

#include "UI_interface.hh"
#include "UI_resources.hh"
#include "UI_tree_view.hh"
#include "UI_view2d.hh"

#include "WM_api.hh"

#include "ED_asset_shelf.h"
#include "asset_shelf.hh"

using namespace blender;
using namespace blender::ed::asset;

static int asset_shelf_default_tile_height();

namespace blender::ed::asset::shelf {

void send_redraw_notifier(const bContext &C)
{
  WM_event_add_notifier(&C, NC_SPACE | ND_REGIONS_ASSET_SHELF, nullptr);
}

}  // namespace blender::ed::asset::shelf

/* -------------------------------------------------------------------- */
/** \name Shelf Type
 * \{ */

static bool asset_shelf_type_poll(const bContext &C,
                                  const SpaceType &space_type,
                                  AssetShelfType *shelf_type)
{
  if (!shelf_type) {
    return false;
  }

  BLI_assert_msg(BLI_findindex(&space_type.asset_shelf_types, shelf_type) != -1,
                 "Asset shelf type is not registered");
  UNUSED_VARS_NDEBUG(space_type);

  return !shelf_type->poll || shelf_type->poll(&C, shelf_type);
}

static AssetShelfType *asset_shelf_type_ensure(const SpaceType &space_type, AssetShelf &shelf)
{
  if (shelf.type) {
    return shelf.type;
  }

  LISTBASE_FOREACH (AssetShelfType *, shelf_type, &space_type.asset_shelf_types) {
    if (STREQ(shelf.idname, shelf_type->idname)) {
      shelf.type = shelf_type;
      return shelf_type;
    }
  }

  return nullptr;
}

static AssetShelf *create_shelf_from_type(AssetShelfType &type)
{
  AssetShelf *shelf = MEM_new<AssetShelf>(__func__);
  *shelf = dna::shallow_zero_initialize();
  shelf->settings.preview_size = shelf::DEFAULT_TILE_SIZE;
  shelf->settings.asset_library_reference = asset_system::all_library_reference();
  shelf->type = &type;
  shelf->preferred_row_count = 1;
  STRNCPY(shelf->idname, type.idname);
  return shelf;
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Active Shelf Management
 * \{ */

/**
 * Activating a shelf means assigning it to #RegionAssetShelf.active_shelf and (re-)inserting it at
 * the beginning of the #RegionAssetShelf.shelves list. This implies that after calling this, \a
 * shelf is guaranteed to be owned by the shelves list.
 */
static void activate_shelf(RegionAssetShelf &shelf_regiondata, AssetShelf &shelf)
{
  shelf_regiondata.active_shelf = &shelf;
  BLI_assert(BLI_findindex(&shelf_regiondata.shelves, &shelf) > -1);
  BLI_remlink(&shelf_regiondata.shelves, &shelf);
  BLI_addhead(&shelf_regiondata.shelves, &shelf);
}

/**
 * Determine and set the currently active asset shelf, creating a new shelf if needed.
 *
 * The heuristic works as follows:
 * 1) If the currently active shelf is still valid (poll succeeds), keep it active.
 * 2) Otherwise, check for previously activated shelves in \a shelf_regiondata and activate the
 *    first valid one (first with a succeeding poll).
 * 3) If none is valid, check all shelf-types available for \a space_type, create a new shelf for
 *    the first type that is valid (poll succeeds), and activate it.
 * 4) If no shelf-type is valid, #RegionAssetShelf.active_shelf is set to null.
 *
 * When activating a shelf, it is moved to the beginning of the #RegionAssetShelf.shelves list, so
 * that recently activated shelves are also the first ones to be reactivated.
 *
 * The returned shelf is guaranteed to have its #AssetShelf.type pointer set.
 *
 * \return A non-owning pointer to the now active shelf. Might be null if no shelf is valid in
 *         current context (all polls failed).
 */
static AssetShelf *update_active_shelf(const bContext &C,
                                       const SpaceType &space_type,
                                       RegionAssetShelf &shelf_regiondata)
{
  /* Note: Don't access #AssetShelf.type directly, use #asset_shelf_type_ensure(). */

  /* Case 1: */
  if (shelf_regiondata.active_shelf &&
      asset_shelf_type_poll(
          C, space_type, asset_shelf_type_ensure(space_type, *shelf_regiondata.active_shelf)))
  {
    /* Not a strong precondition, but if this is wrong something weird might be going on. */
    BLI_assert(shelf_regiondata.active_shelf == shelf_regiondata.shelves.first);
    return shelf_regiondata.active_shelf;
  }

  /* Case 2 (no active shelf or the poll of it isn't succeeding anymore. Poll all shelf types to
   * determine a new active one): */
  LISTBASE_FOREACH (AssetShelf *, shelf, &shelf_regiondata.shelves) {
    if (shelf == shelf_regiondata.active_shelf) {
      continue;
    }

    if (asset_shelf_type_poll(C, space_type, asset_shelf_type_ensure(space_type, *shelf))) {
      /* Found a valid previously activated shelf, reactivate it. */
      activate_shelf(shelf_regiondata, *shelf);
      return shelf;
    }
  }

  /* Case 3: */
  LISTBASE_FOREACH (AssetShelfType *, shelf_type, &space_type.asset_shelf_types) {
    if (asset_shelf_type_poll(C, space_type, shelf_type)) {
      AssetShelf *new_shelf = create_shelf_from_type(*shelf_type);
      BLI_addhead(&shelf_regiondata.shelves, new_shelf);
      /* Moves ownership to the regiondata. */
      activate_shelf(shelf_regiondata, *new_shelf);
      return new_shelf;
    }
  }

  shelf_regiondata.active_shelf = nullptr;
  return nullptr;
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Asset Shelf Regions
 * \{ */

void *ED_asset_shelf_region_duplicate(void *regiondata)
{
  const RegionAssetShelf *shelf_regiondata = static_cast<RegionAssetShelf *>(regiondata);
  if (!shelf_regiondata) {
    return nullptr;
  }

  return shelf::regiondata_duplicate(shelf_regiondata);
}

void ED_asset_shelf_region_free(ARegion *region)
{
  RegionAssetShelf *shelf_regiondata = RegionAssetShelf::get_from_asset_shelf_region(*region);
  if (shelf_regiondata) {
    shelf::regiondata_free(&shelf_regiondata);
  }
  region->regiondata = nullptr;
}

/**
 * Check if there is any asset shelf type in this space returning true in its poll. If not, no
 * asset shelf region should be displayed.
 */
static bool asset_shelf_space_poll(const bContext *C, const SpaceLink *space_link)
{
  const SpaceType *space_type = BKE_spacetype_from_id(space_link->spacetype);

  /* Is there any asset shelf type registered that returns true for it's poll? */
  LISTBASE_FOREACH (AssetShelfType *, shelf_type, &space_type->asset_shelf_types) {
    if (asset_shelf_type_poll(*C, *space_type, shelf_type)) {
      return true;
    }
  }

  return false;
}

bool ED_asset_shelf_regions_poll(const RegionPollParams *params)
{
  return asset_shelf_space_poll(params->context,
                                static_cast<SpaceLink *>(params->area->spacedata.first));
}

static void asset_shelf_region_listen(const wmRegionListenerParams *params)
{
  ARegion *region = params->region;
  const wmNotifier *wmn = params->notifier;

  switch (wmn->category) {
    case NC_SPACE:
      if (wmn->data == ND_REGIONS_ASSET_SHELF) {
        ED_region_tag_redraw(region);
      }
      break;
    case NC_SCENE:
      /* Asset shelf polls typically check the mode. */
      if (ELEM(wmn->data, ND_MODE)) {
        ED_region_tag_redraw(region);
      }
      break;
  }
}

void ED_asset_shelf_region_listen(const wmRegionListenerParams *params)
{
  if (ED_assetlist_listen(params->notifier)) {
    ED_region_tag_redraw_no_rebuild(params->region);
  }
  /* If the asset list didn't catch the notifier, let the region itself listen. */
  else {
    asset_shelf_region_listen(params);
  }
}

void ED_asset_shelf_region_init(wmWindowManager *wm, ARegion *region)
{
  if (!region->regiondata) {
    region->regiondata = MEM_cnew<RegionAssetShelf>("RegionAssetShelf");
  }
  RegionAssetShelf &shelf_regiondata = *RegionAssetShelf::get_from_asset_shelf_region(*region);

  /* Active shelf is only set on draw, so this may be null! */
  AssetShelf *active_shelf = shelf_regiondata.active_shelf;

  UI_view2d_region_reinit(&region->v2d, V2D_COMMONVIEW_PANELS_UI, region->winx, region->winy);

  wmKeyMap *keymap = WM_keymap_ensure(
      wm->defaultconf, "View2D Buttons List", SPACE_EMPTY, RGN_TYPE_WINDOW);
  WM_event_add_keymap_handler(&region->handlers, keymap);

  region->v2d.scroll = V2D_SCROLL_RIGHT | V2D_SCROLL_VERTICAL_HIDE;
  region->v2d.keepzoom |= V2D_LOCKZOOM_X | V2D_LOCKZOOM_Y;
  region->v2d.keepofs |= V2D_KEEPOFS_Y;
  region->v2d.keeptot |= V2D_KEEPTOT_STRICT;

  region->v2d.flag |= V2D_SNAP_TO_PAGESIZE_Y;
  region->v2d.page_size_y = active_shelf ? ED_asset_shelf_tile_height(active_shelf->settings) :
                                           asset_shelf_default_tile_height();

  /* Ensure the view is snapped to a page still, especially for DPI changes. */
  UI_view2d_offset_y_snap_to_closest_page(&region->v2d);
}

static int main_region_padding_y()
{
  const uiStyle *style = UI_style_get_dpi();
  return style->buttonspacey / 2;
}

static int main_region_padding_x()
{
  /* Use the same as the height, equal padding looks nice. */
  return main_region_padding_y();
}

static int current_tile_draw_height(const ARegion *region)
{
  const RegionAssetShelf *shelf_regiondata = RegionAssetShelf::get_from_asset_shelf_region(
      *region);
  const AssetShelf *active_shelf = shelf_regiondata->active_shelf;

  const float aspect = BLI_rctf_size_y(&region->v2d.cur) /
                       (BLI_rcti_size_y(&region->v2d.mask) + 1);

  return (active_shelf ? ED_asset_shelf_tile_height(active_shelf->settings) :
                         asset_shelf_default_tile_height()) /
         (IS_EQF(aspect, 0) ? 1.0f : aspect);
}

/**
 * How many rows fit into the region (accounting for padding).
 */
static int calculate_row_count_from_tile_draw_height(const int region_height_scaled,
                                                     const int tile_draw_height)
{
  return std::max(1, int((region_height_scaled - 2 * main_region_padding_y()) / tile_draw_height));
}

static int calculate_scaled_region_height_from_row_count(const int row_count,
                                                         const int tile_draw_height)
{
  return (row_count * tile_draw_height + 2 * main_region_padding_y());
}

int ED_asset_shelf_region_snap(const ARegion *region, const int size, const int axis)
{
  /* Only on Y axis. */
  if (axis != 1) {
    return size;
  }

  /* Using scaled values only simplifies things. Simply divide the result by the scale again. */

  const int tile_height = current_tile_draw_height(region);

  const int row_count = calculate_row_count_from_tile_draw_height(size * UI_SCALE_FAC,
                                                                  tile_height);

  const int new_size_scaled = calculate_scaled_region_height_from_row_count(row_count,
                                                                            tile_height);
  return new_size_scaled / UI_SCALE_FAC;
}

/**
 * Ensure the region height matches the preferred row count (see #AssetShelf.preferred_row_count).
 * In any case, this will ensure the region height is snapped to a multiple of the row count (plus
 * region padding).
 */
static void region_resize_to_preferred(ScrArea *area, ARegion *region)
{
  const RegionAssetShelf *shelf_regiondata = RegionAssetShelf::get_from_asset_shelf_region(
      *region);
  const AssetShelf *active_shelf = shelf_regiondata->active_shelf;

  BLI_assert(active_shelf->preferred_row_count > 0);

  const int tile_height = current_tile_draw_height(region);
  const int new_size_y = calculate_scaled_region_height_from_row_count(
                             active_shelf->preferred_row_count, tile_height) /
                         UI_SCALE_FAC;

  if (region->sizey != new_size_y) {
    region->sizey = new_size_y;
    ED_area_tag_region_size_update(area, region);
  }
}

void ED_asset_shelf_region_on_user_resize(const ARegion *region)
{
  const RegionAssetShelf *shelf_regiondata = RegionAssetShelf::get_from_asset_shelf_region(
      *region);
  AssetShelf *active_shelf = shelf_regiondata->active_shelf;
  if (!active_shelf) {
    return;
  }

  const int tile_height = current_tile_draw_height(region);
  active_shelf->preferred_row_count = calculate_row_count_from_tile_draw_height(
      region->sizey * UI_SCALE_FAC, tile_height);
}

int ED_asset_shelf_tile_width(const AssetShelfSettings &settings)
{
  return UI_preview_tile_size_x(settings.preview_size);
}

int ED_asset_shelf_tile_height(const AssetShelfSettings &settings)
{
  return (settings.display_flag & ASSETSHELF_SHOW_NAMES) ?
             UI_preview_tile_size_y(settings.preview_size) :
             UI_preview_tile_size_y_no_label(settings.preview_size);
}

static int asset_shelf_default_tile_height()
{
  return UI_preview_tile_size_x(shelf::DEFAULT_TILE_SIZE);
}

int ED_asset_shelf_region_prefsizey()
{
  /* One row by default (plus padding). */
  return asset_shelf_default_tile_height() + 2 * main_region_padding_y();
}

void ED_asset_shelf_region_layout(const bContext *C, ARegion *region)
{
  const SpaceLink *space = CTX_wm_space_data(C);
  const SpaceType *space_type = BKE_spacetype_from_id(space->spacetype);

  RegionAssetShelf *shelf_regiondata = RegionAssetShelf::get_from_asset_shelf_region(*region);
  if (!shelf_regiondata) {
    /* Region-data should've been created by a previously called #ED_asset_shelf_region_init(). */
    BLI_assert_unreachable();
    return;
  }

  AssetShelf *active_shelf = update_active_shelf(*C, *space_type, *shelf_regiondata);
  if (!active_shelf) {
    return;
  }

  uiBlock *block = UI_block_begin(C, region, __func__, UI_EMBOSS);

  const uiStyle *style = UI_style_get_dpi();
  const int padding_y = main_region_padding_y();
  const int padding_x = main_region_padding_x();
  uiLayout *layout = UI_block_layout(block,
                                     UI_LAYOUT_VERTICAL,
                                     UI_LAYOUT_PANEL,
                                     padding_x,
                                     -padding_y,
                                     region->winx - 2 * padding_x,
                                     0,
                                     0,
                                     style);

  shelf::build_asset_view(
      *layout, active_shelf->settings.asset_library_reference, *active_shelf, *C, *region);

  int layout_height;
  UI_block_layout_resolve(block, nullptr, &layout_height);
  BLI_assert(layout_height <= 0);
  UI_view2d_totRect_set(&region->v2d, region->winx - 1, layout_height - padding_y);
  UI_view2d_curRect_validate(&region->v2d);

  region_resize_to_preferred(CTX_wm_area(C), region);

  UI_block_end(C, block);
}

void ED_asset_shelf_region_draw(const bContext *C, ARegion *region)
{
  ED_region_clear(C, region, TH_BACK);

  /* Set view2d view matrix for scrolling. */
  UI_view2d_view_ortho(&region->v2d);

  /* View2D matrix might have changed due to dynamic sized regions. */
  UI_blocklist_update_window_matrix(C, &region->uiblocks);

  UI_blocklist_draw(C, &region->uiblocks);

  /* Restore view matrix. */
  UI_view2d_view_restore(C);

  UI_view2d_scrollers_draw(&region->v2d, nullptr);
}

void ED_asset_shelf_header_region_listen(const wmRegionListenerParams *params)
{
  asset_shelf_region_listen(params);
}

void ED_asset_shelf_header_region_init(wmWindowManager * /*wm*/, ARegion *region)
{
  ED_region_header_init(region);
  region->alignment |= RGN_SPLIT_SCALE_PREV;
  region->flag |= RGN_FLAG_RESIZE_RESPECT_BUTTON_SECTIONS;
}

void ED_asset_shelf_header_region(const bContext *C, ARegion *region)
{
  const SpaceLink *space = CTX_wm_space_data(C);
  const SpaceType *space_type = BKE_spacetype_from_id(space->spacetype);
  const ARegion *main_shelf_region = BKE_area_find_region_type(CTX_wm_area(C),
                                                               RGN_TYPE_ASSET_SHELF);

  RegionAssetShelf *shelf_regiondata = RegionAssetShelf::get_from_asset_shelf_region(
      *main_shelf_region);
  update_active_shelf(*C, *space_type, *shelf_regiondata);

  ED_region_header_with_button_sections(C, region, uiButtonSectionsAlign::Bottom);
}

int ED_asset_shelf_header_region_size()
{
  /* Use a height that lets widgets sit just on top of the separator line drawn at the lower edge
   * of the region (widgets will be centered).
   *
   * Note that this is usually a bit less than the header size. The asset shelf tends to look like
   * a separate area, so making the shelf header smaller than a header helps. */
  return UI_UNIT_Y + (UI_BUTTON_SECTION_SEPERATOR_LINE_WITH * 2);
}

void ED_asset_shelf_region_blend_read_data(BlendDataReader *reader, ARegion *region)
{
  RegionAssetShelf *shelf_regiondata = RegionAssetShelf::get_from_asset_shelf_region(*region);
  if (!shelf_regiondata) {
    return;
  }
  shelf::regiondata_blend_read_data(reader, &shelf_regiondata);
  region->regiondata = shelf_regiondata;
}

void ED_asset_shelf_region_blend_write(BlendWriter *writer, ARegion *region)
{
  RegionAssetShelf *shelf_regiondata = RegionAssetShelf::get_from_asset_shelf_region(*region);
  if (!shelf_regiondata) {
    return;
  }
  shelf::regiondata_blend_write(writer, shelf_regiondata);
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Asset Shelf Context
 * \{ */

static AssetShelf *active_shelf_from_area(const ScrArea *area)
{
  const ARegion *shelf_region = BKE_area_find_region_type(area, RGN_TYPE_ASSET_SHELF);
  if (!shelf_region) {
    /* Called in wrong context, area doesn't have a shelf. */
    BLI_assert_unreachable();
    return nullptr;
  }

  if (shelf_region->flag & RGN_FLAG_POLL_FAILED) {
    /* Don't return data when the region "doesn't exist" (poll failed). */
    return nullptr;
  }

  const RegionAssetShelf *shelf_regiondata = RegionAssetShelf::get_from_asset_shelf_region(
      *shelf_region);
  if (!shelf_regiondata) {
    return nullptr;
  }

  return shelf_regiondata->active_shelf;
}

int ED_asset_shelf_context(const bContext *C, const char *member, bContextDataResult *result)
{
  static const char *context_dir[] = {
      "asset_shelf",
      "asset_library_reference",
      "active_file", /* XXX yuk... */
      nullptr,
  };

  if (CTX_data_dir(member)) {
    CTX_data_dir_set(result, context_dir);
    return CTX_RESULT_OK;
  }

  bScreen *screen = CTX_wm_screen(C);

  if (CTX_data_equals(member, "asset_shelf")) {
    AssetShelf *active_shelf = active_shelf_from_area(CTX_wm_area(C));
    if (!active_shelf) {
      return CTX_RESULT_NO_DATA;
    }

    CTX_data_pointer_set(result, &screen->id, &RNA_AssetShelf, active_shelf);
    return CTX_RESULT_OK;
  }

  if (CTX_data_equals(member, "asset_library_reference")) {
    AssetShelf *active_shelf = active_shelf_from_area(CTX_wm_area(C));
    if (!active_shelf) {
      return CTX_RESULT_NO_DATA;
    }

    CTX_data_pointer_set(result,
                         &screen->id,
                         &RNA_AssetLibraryReference,
                         &active_shelf->settings.asset_library_reference);
    return CTX_RESULT_OK;
  }

  /* XXX hack. Get the asset from the active item, but needs to be the file... */
  if (CTX_data_equals(member, "active_file")) {
    const ARegion *region = CTX_wm_region(C);
    const uiBut *but = UI_region_views_find_active_item_but(region);
    if (!but) {
      return CTX_RESULT_NO_DATA;
    }

    const bContextStore *but_context = UI_but_context_get(but);
    if (!but_context) {
      return CTX_RESULT_NO_DATA;
    }

    const PointerRNA *file_ptr = CTX_store_ptr_lookup(
        but_context, "active_file", &RNA_FileSelectEntry);
    if (!file_ptr) {
      return CTX_RESULT_NO_DATA;
    }

    CTX_data_pointer_set_ptr(result, file_ptr);
    return CTX_RESULT_OK;
  }

  return CTX_RESULT_MEMBER_NOT_FOUND;
}

namespace blender::ed::asset::shelf {

static PointerRNA active_shelf_ptr_from_context(const bContext *C)
{
  return CTX_data_pointer_get_type(C, "asset_shelf", &RNA_AssetShelf);
}

AssetShelf *active_shelf_from_context(const bContext *C)
{
  PointerRNA shelf_settings_ptr = active_shelf_ptr_from_context(C);
  return static_cast<AssetShelf *>(shelf_settings_ptr.data);
}

}  // namespace blender::ed::asset::shelf

/** \} */

/* -------------------------------------------------------------------- */
/** \name Catalog toggle buttons
 * \{ */

static uiBut *add_tab_button(uiBlock &block, StringRefNull name)
{
  const uiStyle *style = UI_style_get_dpi();
  const int string_width = UI_fontstyle_string_width(&style->widget, name.c_str());
  const int pad_x = UI_UNIT_X * 0.3f;
  const int but_width = std::min(string_width + 2 * pad_x, UI_UNIT_X * 8);

  uiBut *but = uiDefBut(&block,
                        UI_BTYPE_TAB,
                        0,
                        name.c_str(),
                        0,
                        0,
                        but_width,
                        UI_UNIT_Y,
                        nullptr,
                        0,
                        0,
                        0,
                        0,
                        "Enable catalog, making contained assets visible in the asset shelf");

  UI_but_drawflag_enable(but, UI_BUT_ALIGN_DOWN);
  UI_but_flag_disable(but, UI_BUT_UNDO);

  return but;
}

static void add_catalog_tabs(AssetShelfSettings &shelf_settings, uiLayout &layout)
{
  uiBlock *block = uiLayoutGetBlock(&layout);

  /* "All" tab. */
  {
    uiBut *but = add_tab_button(*block, IFACE_("All"));
    UI_but_func_set(but, [&shelf_settings](bContext &C) {
      shelf::settings_set_all_catalog_active(shelf_settings);
      shelf::send_redraw_notifier(C);
    });
    UI_but_func_pushed_state_set(but, [&shelf_settings](const uiBut &) -> bool {
      return shelf::settings_is_all_catalog_active(shelf_settings);
    });
  }

  uiItemS(&layout);

  /* Regular catalog tabs. */
  shelf::settings_foreach_enabled_catalog_path(
      shelf_settings, [&shelf_settings, block](const asset_system::AssetCatalogPath &path) {
        uiBut *but = add_tab_button(*block, path.name());

        UI_but_func_set(but, [&shelf_settings, path](bContext &C) {
          shelf::settings_set_active_catalog(shelf_settings, path);
          shelf::send_redraw_notifier(C);
        });
        UI_but_func_pushed_state_set(but, [&shelf_settings, path](const uiBut &) -> bool {
          return shelf::settings_is_active_catalog(shelf_settings, path);
        });
      });
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Asset Shelf Header Region
 *
 * Implemented as HeaderType for #RGN_TYPE_ASSET_SHELF_HEADER.
 * \{ */

static void asset_shelf_header_draw(const bContext *C, Header *header)
{
  uiLayout *layout = header->layout;
  uiBlock *block = uiLayoutGetBlock(layout);
  const AssetLibraryReference *library_ref = CTX_wm_asset_library_ref(C);

  ED_assetlist_storage_fetch(library_ref, C);

  UI_block_emboss_set(block, UI_EMBOSS_NONE);
  uiItemPopoverPanel(layout, C, "ASSETSHELF_PT_catalog_selector", "", ICON_COLLAPSEMENU);
  UI_block_emboss_set(block, UI_EMBOSS);

  uiItemS(layout);

  PointerRNA shelf_ptr = shelf::active_shelf_ptr_from_context(C);
  AssetShelf *shelf = static_cast<AssetShelf *>(shelf_ptr.data);
  if (shelf) {
    add_catalog_tabs(shelf->settings, *layout);
  }

  uiItemSpacer(layout);

  uiItemPopoverPanel(layout, C, "ASSETSHELF_PT_display", "", ICON_IMGDISPLAY);
  uiLayout *sub = uiLayoutRow(layout, false);
  /* Same as file/asset browser header. */
  uiLayoutSetUnitsX(sub, 8);
  uiItemR(sub, &shelf_ptr, "search_filter", UI_ITEM_NONE, "", ICON_VIEWZOOM);
}

void ED_asset_shelf_header_regiontype_register(ARegionType *region_type, const int space_type)
{
  HeaderType *ht = MEM_cnew<HeaderType>(__func__);
  STRNCPY(ht->idname, "ASSETSHELF_HT_settings");
  ht->space_type = space_type;
  ht->region_type = RGN_TYPE_ASSET_SHELF_HEADER;
  ht->draw = asset_shelf_header_draw;
  ht->poll = [](const bContext *C, HeaderType *) {
    return asset_shelf_space_poll(C, CTX_wm_space_data(C));
  };

  BLI_addtail(&region_type->headertypes, ht);

  shelf::catalog_selector_panel_register(region_type);
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Asset Shelf Type (un)registration
 * \{ */

void ED_asset_shelf_type_unlink(const Main &bmain, const AssetShelfType &shelf_type)
{
  LISTBASE_FOREACH (bScreen *, screen, &bmain.screens) {
    LISTBASE_FOREACH (ScrArea *, area, &screen->areabase) {
      LISTBASE_FOREACH (SpaceLink *, sl, &area->spacedata) {
        ListBase *regionbase = (sl == area->spacedata.first) ? &area->regionbase : &sl->regionbase;
        LISTBASE_FOREACH (ARegion *, region, regionbase) {
          if (region->regiontype != RGN_TYPE_ASSET_SHELF) {
            continue;
          }

          RegionAssetShelf *shelf_regiondata = RegionAssetShelf::get_from_asset_shelf_region(
              *region);
          if (!shelf_regiondata) {
            continue;
          }
          LISTBASE_FOREACH (AssetShelf *, shelf, &shelf_regiondata->shelves) {
            if (shelf->type == &shelf_type) {
              shelf->type = nullptr;
            }
          }

          BLI_assert((shelf_regiondata->active_shelf == nullptr) ||
                     (shelf_regiondata->active_shelf->type != &shelf_type));
        }
      }
    }
  }
}

/** \} */

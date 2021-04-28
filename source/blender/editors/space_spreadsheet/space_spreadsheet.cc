/*
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
 */

#include <cstring>

#include "BLI_listbase.h"

#include "BKE_screen.h"

#include "ED_screen.h"
#include "ED_space_api.h"
#include "ED_spreadsheet.h"

#include "DNA_scene_types.h"
#include "DNA_screen_types.h"
#include "DNA_space_types.h"

#include "MEM_guardedalloc.h"

#include "UI_interface.h"
#include "UI_resources.h"
#include "UI_view2d.h"

#include "DEG_depsgraph_query.h"

#include "RNA_access.h"

#include "WM_api.h"
#include "WM_types.h"

#include "BLF_api.h"

#include "spreadsheet_intern.hh"

#include "spreadsheet_context.hh"
#include "spreadsheet_data_source_geometry.hh"
#include "spreadsheet_intern.hh"
#include "spreadsheet_layout.hh"

using namespace blender;
using namespace blender::ed::spreadsheet;

static SpaceLink *spreadsheet_create(const ScrArea *UNUSED(area), const Scene *UNUSED(scene))
{
  SpaceSpreadsheet *spreadsheet_space = (SpaceSpreadsheet *)MEM_callocN(sizeof(SpaceSpreadsheet),
                                                                        "spreadsheet space");
  spreadsheet_space->spacetype = SPACE_SPREADSHEET;

  {
    /* Header. */
    ARegion *region = (ARegion *)MEM_callocN(sizeof(ARegion), "spreadsheet header");
    BLI_addtail(&spreadsheet_space->regionbase, region);
    region->regiontype = RGN_TYPE_HEADER;
    region->alignment = (U.uiflag & USER_HEADER_BOTTOM) ? RGN_ALIGN_BOTTOM : RGN_ALIGN_TOP;
  }

  {
    /* Footer. */
    ARegion *region = (ARegion *)MEM_callocN(sizeof(ARegion), "spreadsheet footer region");
    BLI_addtail(&spreadsheet_space->regionbase, region);
    region->regiontype = RGN_TYPE_FOOTER;
    region->alignment = (U.uiflag & USER_HEADER_BOTTOM) ? RGN_ALIGN_TOP : RGN_ALIGN_BOTTOM;
  }

  {
    /* Main window. */
    ARegion *region = (ARegion *)MEM_callocN(sizeof(ARegion), "spreadsheet main region");
    BLI_addtail(&spreadsheet_space->regionbase, region);
    region->regiontype = RGN_TYPE_WINDOW;
  }

  return (SpaceLink *)spreadsheet_space;
}

static void spreadsheet_free(SpaceLink *sl)
{
  SpaceSpreadsheet *sspreadsheet = (SpaceSpreadsheet *)sl;
  MEM_SAFE_FREE(sspreadsheet->runtime);

  LISTBASE_FOREACH_MUTABLE (SpreadsheetColumn *, column, &sspreadsheet->columns) {
    spreadsheet_column_free(column);
  }
  LISTBASE_FOREACH_MUTABLE (SpreadsheetContext *, context, &sspreadsheet->context_path) {
    spreadsheet_context_free(context);
  }
}

static void spreadsheet_init(wmWindowManager *UNUSED(wm), ScrArea *area)
{
  SpaceSpreadsheet *sspreadsheet = (SpaceSpreadsheet *)area->spacedata.first;
  if (sspreadsheet->runtime == nullptr) {
    sspreadsheet->runtime = (SpaceSpreadsheet_Runtime *)MEM_callocN(
        sizeof(SpaceSpreadsheet_Runtime), __func__);
  }
}

static SpaceLink *spreadsheet_duplicate(SpaceLink *sl)
{
  const SpaceSpreadsheet *sspreadsheet_old = (SpaceSpreadsheet *)sl;
  SpaceSpreadsheet *sspreadsheet_new = (SpaceSpreadsheet *)MEM_dupallocN(sspreadsheet_old);
  sspreadsheet_new->runtime = (SpaceSpreadsheet_Runtime *)MEM_dupallocN(sspreadsheet_old->runtime);

  BLI_listbase_clear(&sspreadsheet_new->columns);
  LISTBASE_FOREACH (SpreadsheetColumn *, src_column, &sspreadsheet_old->columns) {
    SpreadsheetColumn *new_column = spreadsheet_column_copy(src_column);
    BLI_addtail(&sspreadsheet_new->columns, new_column);
  }

  BLI_listbase_clear(&sspreadsheet_new->context_path);
  LISTBASE_FOREACH_MUTABLE (SpreadsheetContext *, src_context, &sspreadsheet_old->context_path) {
    SpreadsheetContext *new_context = spreadsheet_context_copy(src_context);
    BLI_addtail(&sspreadsheet_new->context_path, new_context);
  }

  return (SpaceLink *)sspreadsheet_new;
}

static void spreadsheet_keymap(wmKeyConfig *UNUSED(keyconf))
{
}

static void spreadsheet_id_remap(ScrArea *UNUSED(area), SpaceLink *slink, ID *old_id, ID *new_id)
{
  SpaceSpreadsheet *sspreadsheet = (SpaceSpreadsheet *)slink;
  LISTBASE_FOREACH (SpreadsheetContext *, context, &sspreadsheet->context_path) {
    if (context->type == SPREADSHEET_CONTEXT_OBJECT) {
      SpreadsheetContextObject *object_context = (SpreadsheetContextObject *)context;
      if ((ID *)object_context->object == old_id) {
        if (new_id && GS(new_id->name) == ID_OB) {
          object_context->object = (Object *)new_id;
        }
        else {
          object_context->object = nullptr;
        }
      }
    }
  }
}

static void spreadsheet_main_region_init(wmWindowManager *wm, ARegion *region)
{
  region->v2d.scroll = V2D_SCROLL_RIGHT | V2D_SCROLL_BOTTOM;
  region->v2d.align = V2D_ALIGN_NO_NEG_X | V2D_ALIGN_NO_POS_Y;
  region->v2d.keepzoom = V2D_LOCKZOOM_X | V2D_LOCKZOOM_Y | V2D_LIMITZOOM | V2D_KEEPASPECT;
  region->v2d.keeptot = V2D_KEEPTOT_STRICT;
  region->v2d.minzoom = region->v2d.maxzoom = 1.0f;

  UI_view2d_region_reinit(&region->v2d, V2D_COMMONVIEW_LIST, region->winx, region->winy);

  wmKeyMap *keymap = WM_keymap_ensure(wm->defaultconf, "View2D Buttons List", 0, 0);
  WM_event_add_keymap_handler(&region->handlers, keymap);
}

ID *ED_spreadsheet_get_current_id(struct SpaceSpreadsheet *sspreadsheet)
{
  if (BLI_listbase_is_empty(&sspreadsheet->context_path)) {
    return nullptr;
  }
  SpreadsheetContext *root_context = (SpreadsheetContext *)sspreadsheet->context_path.first;
  if (root_context->type != SPREADSHEET_CONTEXT_OBJECT) {
    return nullptr;
  }
  SpreadsheetContextObject *object_context = (SpreadsheetContextObject *)root_context;
  return (ID *)object_context->object;
}

/* Check if the pinned context still exists. If it doesn't try to find a new context. */
static void update_pinned_context_path_if_outdated(const bContext *C)
{
  SpaceSpreadsheet *sspreadsheet = CTX_wm_space_spreadsheet(C);

  /* Currently, this only checks if the object has been deleted. In the future we can have a more
   * sophisticated check for the entire context (including modifier and nodes). */
  LISTBASE_FOREACH (SpreadsheetContext *, context, &sspreadsheet->context_path) {
    if (context->type == SPREADSHEET_CONTEXT_OBJECT) {
      SpreadsheetContextObject *object_context = (SpreadsheetContextObject *)context;
      if (object_context->object == nullptr) {
        ED_spreadsheet_context_path_clear(sspreadsheet);
        break;
      }
    }
  }
  if (BLI_listbase_is_empty(&sspreadsheet->context_path)) {
    Object *active_object = CTX_data_active_object(C);
    if (active_object != nullptr) {
      SpreadsheetContext *new_context = spreadsheet_context_new(SPREADSHEET_CONTEXT_OBJECT);
      ((SpreadsheetContextObject *)new_context)->object = active_object;
      BLI_addtail(&sspreadsheet->context_path, new_context);
    }
  }

  if (BLI_listbase_is_empty(&sspreadsheet->context_path)) {
    /* Don't pin empty context_path, that could be annoying. */
    sspreadsheet->flag &= ~SPREADSHEET_FLAG_PINNED;
  }
}

static void update_context_path_from_context(const bContext *C)
{
  SpaceSpreadsheet *sspreadsheet = CTX_wm_space_spreadsheet(C);
  Object *active_object = CTX_data_active_object(C);
  if (active_object == nullptr) {
    ED_spreadsheet_context_path_clear(sspreadsheet);
    return;
  }
  if (!BLI_listbase_is_empty(&sspreadsheet->context_path)) {
    SpreadsheetContext *root_context = (SpreadsheetContext *)sspreadsheet->context_path.first;
    if (root_context->type == SPREADSHEET_CONTEXT_OBJECT) {
      SpreadsheetContextObject *object_context = (SpreadsheetContextObject *)root_context;
      if (object_context->object != active_object) {
        ED_spreadsheet_context_path_clear(sspreadsheet);
      }
    }
  }
  if (BLI_listbase_is_empty(&sspreadsheet->context_path)) {
    SpreadsheetContext *new_context = spreadsheet_context_new(SPREADSHEET_CONTEXT_OBJECT);
    ((SpreadsheetContextObject *)new_context)->object = active_object;
    BLI_addtail(&sspreadsheet->context_path, new_context);
  }
}

static void update_context_path(const bContext *C)
{
  SpaceSpreadsheet *sspreadsheet = CTX_wm_space_spreadsheet(C);
  if (sspreadsheet->flag & SPREADSHEET_FLAG_PINNED) {
    update_pinned_context_path_if_outdated(C);
  }
  else {
    update_context_path_from_context(C);
  }
}

static std::unique_ptr<DataSource> get_data_source(const bContext *C)
{
  Depsgraph *depsgraph = CTX_data_depsgraph_pointer(C);
  SpaceSpreadsheet *sspreadsheet = CTX_wm_space_spreadsheet(C);
  ID *used_id = ED_spreadsheet_get_current_id(sspreadsheet);
  if (used_id == nullptr) {
    return {};
  }
  const ID_Type id_type = GS(used_id->name);
  if (id_type != ID_OB) {
    return {};
  }
  Object *object_orig = (Object *)used_id;
  if (!ELEM(object_orig->type, OB_MESH, OB_POINTCLOUD, OB_VOLUME)) {
    return {};
  }
  Object *object_eval = DEG_get_evaluated_object(depsgraph, object_orig);
  if (object_eval == nullptr) {
    return {};
  }

  return data_source_from_geometry(C, object_eval);
}

static float get_column_width(const ColumnValues &values)
{
  if (values.default_width > 0) {
    return values.default_width;
  }
  const int fontid = UI_style_get()->widget.uifont_id;
  BLF_size(fontid, UI_DEFAULT_TEXT_POINTS, U.dpi);
  const StringRefNull name = values.name();
  const float name_width = BLF_width(fontid, name.data(), name.size());
  return std::max<float>(name_width / UI_UNIT_X + 1.0f, 3.0f);
}

static float get_column_width_in_pixels(const ColumnValues &values)
{
  return get_column_width(values) * SPREADSHEET_WIDTH_UNIT;
}

static int get_index_column_width(const int tot_rows)
{
  const int fontid = UI_style_get()->widget.uifont_id;
  BLF_size(fontid, UI_style_get_dpi()->widget.points * U.pixelsize, U.dpi);
  return std::to_string(std::max(0, tot_rows - 1)).size() * BLF_width(fontid, "0", 1) +
         UI_UNIT_X * 0.75;
}

static void update_visible_columns(ListBase &columns, DataSource &data_source)
{
  Set<SpreadsheetColumnID> used_ids;
  LISTBASE_FOREACH_MUTABLE (SpreadsheetColumn *, column, &columns) {
    std::unique_ptr<ColumnValues> values = data_source.get_column_values(*column->id);
    /* Remove columns that don't exist anymore. */
    if (!values) {
      BLI_remlink(&columns, column);
      spreadsheet_column_free(column);
      continue;
    }

    if (!used_ids.add(*column->id)) {
      /* Remove duplicate columns for now. */
      BLI_remlink(&columns, column);
      spreadsheet_column_free(column);
      continue;
    }
  }

  data_source.foreach_default_column_ids([&](const SpreadsheetColumnID &column_id) {
    std::unique_ptr<ColumnValues> values = data_source.get_column_values(column_id);
    if (values) {
      if (used_ids.add(column_id)) {
        SpreadsheetColumnID *new_id = spreadsheet_column_id_copy(&column_id);
        SpreadsheetColumn *new_column = spreadsheet_column_new(new_id);
        BLI_addtail(&columns, new_column);
      }
    }
  });
}

static void spreadsheet_main_region_draw(const bContext *C, ARegion *region)
{
  SpaceSpreadsheet *sspreadsheet = CTX_wm_space_spreadsheet(C);
  update_context_path(C);

  std::unique_ptr<DataSource> data_source = get_data_source(C);
  if (!data_source) {
    data_source = std::make_unique<DataSource>();
  }

  update_visible_columns(sspreadsheet->columns, *data_source);

  SpreadsheetLayout spreadsheet_layout;
  ResourceScope scope;

  LISTBASE_FOREACH (SpreadsheetColumn *, column, &sspreadsheet->columns) {
    std::unique_ptr<ColumnValues> values_ptr = data_source->get_column_values(*column->id);
    /* Should have been removed before if it does not exist anymore. */
    BLI_assert(values_ptr);
    const ColumnValues *values = scope.add(std::move(values_ptr), __func__);
    const int width = get_column_width_in_pixels(*values);
    spreadsheet_layout.columns.append({values, width});
  }

  const int tot_rows = data_source->tot_rows();
  spreadsheet_layout.index_column_width = get_index_column_width(tot_rows);
  spreadsheet_layout.row_indices = IndexRange(tot_rows).as_span();

  if (const GeometryDataSource *geometry_data_source = dynamic_cast<const GeometryDataSource *>(
          data_source.get())) {
    Object *object_eval = geometry_data_source->object_eval();
    Object *object_orig = DEG_get_original_object(object_eval);
    if (object_orig->type == OB_MESH) {
      if (object_orig->mode == OB_MODE_EDIT) {
        if (sspreadsheet->filter_flag & SPREADSHEET_FILTER_SELECTED_ONLY) {
          spreadsheet_layout.row_indices = geometry_data_source->get_selected_element_indices();
        }
      }
    }
  }

  sspreadsheet->runtime->tot_columns = spreadsheet_layout.columns.size();
  sspreadsheet->runtime->tot_rows = tot_rows;
  sspreadsheet->runtime->visible_rows = spreadsheet_layout.row_indices.size();

  std::unique_ptr<SpreadsheetDrawer> drawer = spreadsheet_drawer_from_layout(spreadsheet_layout);
  draw_spreadsheet_in_region(C, region, *drawer);

  /* Tag footer for redraw, because the main region updates data for the footer. */
  ARegion *footer = BKE_area_find_region_type(CTX_wm_area(C), RGN_TYPE_FOOTER);
  ED_region_tag_redraw(footer);
}

static void spreadsheet_main_region_listener(const wmRegionListenerParams *params)
{
  ARegion *region = params->region;
  wmNotifier *wmn = params->notifier;

  switch (wmn->category) {
    case NC_SCENE: {
      switch (wmn->data) {
        case ND_MODE:
        case ND_FRAME:
        case ND_OB_ACTIVE: {
          ED_region_tag_redraw(region);
          break;
        }
      }
      break;
    }
    case NC_OBJECT: {
      ED_region_tag_redraw(region);
      break;
    }
    case NC_SPACE: {
      if (wmn->data == ND_SPACE_SPREADSHEET) {
        ED_region_tag_redraw(region);
      }
      break;
    }
    case NC_TEXTURE:
    case NC_GEOM: {
      ED_region_tag_redraw(region);
      break;
    }
  }
}

static void spreadsheet_header_region_init(wmWindowManager *UNUSED(wm), ARegion *region)
{
  ED_region_header_init(region);
}

static void spreadsheet_header_region_draw(const bContext *C, ARegion *region)
{
  update_context_path(C);
  ED_region_header(C, region);
}

static void spreadsheet_header_region_free(ARegion *UNUSED(region))
{
}

static void spreadsheet_header_region_listener(const wmRegionListenerParams *params)
{
  ARegion *region = params->region;
  wmNotifier *wmn = params->notifier;

  switch (wmn->category) {
    case NC_SCENE: {
      switch (wmn->data) {
        case ND_MODE:
        case ND_OB_ACTIVE: {
          ED_region_tag_redraw(region);
          break;
        }
      }
      break;
    }
    case NC_OBJECT: {
      ED_region_tag_redraw(region);
      break;
    }
    case NC_SPACE: {
      if (wmn->data == ND_SPACE_SPREADSHEET) {
        ED_region_tag_redraw(region);
      }
      break;
    }
    case NC_GEOM: {
      ED_region_tag_redraw(region);
      break;
    }
  }
}

static void spreadsheet_footer_region_init(wmWindowManager *UNUSED(wm), ARegion *region)
{
  ED_region_header_init(region);
}

static void spreadsheet_footer_region_draw(const bContext *C, ARegion *region)
{
  SpaceSpreadsheet *sspreadsheet = CTX_wm_space_spreadsheet(C);
  SpaceSpreadsheet_Runtime *runtime = sspreadsheet->runtime;
  std::stringstream ss;
  ss << "Rows: ";
  if (runtime->visible_rows != runtime->tot_rows) {
    char visible_rows_str[16];
    BLI_str_format_int_grouped(visible_rows_str, runtime->visible_rows);
    ss << visible_rows_str << " / ";
  }
  char tot_rows_str[16];
  BLI_str_format_int_grouped(tot_rows_str, runtime->tot_rows);
  ss << tot_rows_str << "   |   Columns: " << runtime->tot_columns;
  std::string stats_str = ss.str();

  UI_ThemeClearColor(TH_BACK);

  uiBlock *block = UI_block_begin(C, region, __func__, UI_EMBOSS);
  const uiStyle *style = UI_style_get_dpi();
  uiLayout *layout = UI_block_layout(block,
                                     UI_LAYOUT_HORIZONTAL,
                                     UI_LAYOUT_HEADER,
                                     UI_HEADER_OFFSET,
                                     region->winy - (region->winy - UI_UNIT_Y) / 2.0f,
                                     region->sizex,
                                     1,
                                     0,
                                     style);
  uiItemSpacer(layout);
  uiLayoutSetAlignment(layout, UI_LAYOUT_ALIGN_RIGHT);
  uiItemL(layout, stats_str.c_str(), ICON_NONE);
  UI_block_layout_resolve(block, nullptr, nullptr);
  UI_block_align_end(block);
  UI_block_end(C, block);
  UI_block_draw(C, block);
}

static void spreadsheet_footer_region_free(ARegion *UNUSED(region))
{
}

static void spreadsheet_footer_region_listener(const wmRegionListenerParams *UNUSED(params))
{
}

void ED_spacetype_spreadsheet(void)
{
  SpaceType *st = (SpaceType *)MEM_callocN(sizeof(SpaceType), "spacetype spreadsheet");
  ARegionType *art;

  st->spaceid = SPACE_SPREADSHEET;
  strncpy(st->name, "Spreadsheet", BKE_ST_MAXNAME);

  st->create = spreadsheet_create;
  st->free = spreadsheet_free;
  st->init = spreadsheet_init;
  st->duplicate = spreadsheet_duplicate;
  st->operatortypes = spreadsheet_operatortypes;
  st->keymap = spreadsheet_keymap;
  st->id_remap = spreadsheet_id_remap;

  /* regions: main window */
  art = (ARegionType *)MEM_callocN(sizeof(ARegionType), "spacetype spreadsheet region");
  art->regionid = RGN_TYPE_WINDOW;
  art->keymapflag = ED_KEYMAP_UI | ED_KEYMAP_VIEW2D;

  art->init = spreadsheet_main_region_init;
  art->draw = spreadsheet_main_region_draw;
  art->listener = spreadsheet_main_region_listener;
  BLI_addhead(&st->regiontypes, art);

  /* regions: header */
  art = (ARegionType *)MEM_callocN(sizeof(ARegionType), "spacetype spreadsheet header region");
  art->regionid = RGN_TYPE_HEADER;
  art->prefsizey = HEADERY;
  art->keymapflag = 0;
  art->keymapflag = ED_KEYMAP_UI | ED_KEYMAP_VIEW2D | ED_KEYMAP_HEADER;

  art->init = spreadsheet_header_region_init;
  art->draw = spreadsheet_header_region_draw;
  art->free = spreadsheet_header_region_free;
  art->listener = spreadsheet_header_region_listener;
  BLI_addhead(&st->regiontypes, art);

  /* regions: footer */
  art = (ARegionType *)MEM_callocN(sizeof(ARegionType), "spacetype spreadsheet footer region");
  art->regionid = RGN_TYPE_FOOTER;
  art->prefsizey = HEADERY;
  art->keymapflag = 0;
  art->keymapflag = ED_KEYMAP_UI | ED_KEYMAP_VIEW2D | ED_KEYMAP_HEADER;

  art->init = spreadsheet_footer_region_init;
  art->draw = spreadsheet_footer_region_draw;
  art->free = spreadsheet_footer_region_free;
  art->listener = spreadsheet_footer_region_listener;
  BLI_addhead(&st->regiontypes, art);

  BKE_spacetype_register(st);
}

/* SPDX-FileCopyrightText: 2008 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file blender/editors/space_toolbar/space_toolbar.c
 *  \ingroup sptoolbar
 */

#include "MEM_guardedalloc.h"

#include "BLI_listbase.h"
#include "BLI_string.h"

#include "BKE_context.hh"
#include "BKE_screen.hh"

#include "ED_screen.hh"
#include "ED_space_api.hh"

#include "WM_types.hh"

#include "UI_resources.hh"
#include "UI_view2d.hh"

#include "BLO_read_write.hh"

/* ******************** default callbacks for toolbar space ***************** */

static SpaceLink *toolbar_create(const ScrArea * /*area*/, const Scene * /*scene*/)
{
  ARegion *region;
  SpaceToolbar *stoolbar;

  stoolbar = static_cast<SpaceToolbar *>(MEM_callocN(sizeof(SpaceToolbar), "inittoolbar"));
  stoolbar->spacetype = SPACE_TOOLBAR;

  /* header */
  region = BKE_area_region_new();

  BLI_addtail(&stoolbar->regionbase, region);
  region->regiontype = RGN_TYPE_HEADER;
  region->alignment = RGN_ALIGN_TOP;

  /* main region */
  region = BKE_area_region_new();

  BLI_addtail(&stoolbar->regionbase, region);
  region->regiontype = RGN_TYPE_WINDOW;

  return (SpaceLink *)stoolbar;
}

static SpaceLink *toolbar_duplicate(SpaceLink *sl)
{
  SpaceToolbar *stoolbarn = static_cast<SpaceToolbar *>(MEM_dupallocN(sl));

  /* clear or remove stuff from old */

  return (SpaceLink *)stoolbarn;
}

/* add handlers, stuff you only do once or on area/region changes */
static void toolbar_main_region_init(wmWindowManager * /*wm*/, ARegion *region)
{
  UI_view2d_region_reinit(&region->v2d, V2D_COMMONVIEW_CUSTOM, region->winx, region->winy);
}

static void toolbar_main_region_draw(const bContext *C, ARegion *region)
{
  /* draw entirely, view changes should be handled here */
  View2D *v2d = &region->v2d;

  /* clear and setup matrix */
  UI_ThemeClearColor(TH_BACK);

  /* Works best with no view2d matrix set */
  UI_view2d_view_ortho(v2d);

  /* reset view matrix */
  UI_view2d_view_restore(C);

  /* scrollers */
  UI_view2d_scrollers_draw(v2d, nullptr);
}

static void toolbar_header_region_init(wmWindowManager * /*wm*/, ARegion *region)
{
  ED_region_header_init(region);
}

static void toolbar_header_region_draw(const bContext *C, ARegion *region)
{
  ED_region_header(C, region);
}

static void toolbar_main_region_listener(const wmRegionListenerParams *params)
{
  ARegion *region = params->region;
  const wmNotifier *wmn = params->notifier;

  /* context changes */
  switch (wmn->category) {
    case NC_SPACE:
      if (wmn->data == ND_SPACE_INFO_REPORT) {
        /* redraw also but only for report view, could do less redraws by checking the type */
        ED_region_tag_redraw(region);
      }
      break;
  }
}

static void toolbar_header_listener(const wmRegionListenerParams *params)
{
  ARegion *region = params->region;
  const wmNotifier *wmn = params->notifier;

  /* context changes */
  switch (wmn->category) {
    case NC_WM:
      if (wmn->data == ND_JOB) {
        ED_region_tag_redraw(region);
      }
      break;
    case NC_SCENE:
      if (wmn->data == ND_RENDER_RESULT) {
        ED_region_tag_redraw(region);
      }
      break;
    case NC_SPACE:
      if (wmn->data == ND_SPACE_INFO) {
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

static void toolbar_space_blend_write(BlendWriter *writer, SpaceLink *sl)
{
  BLO_write_struct(writer, SpaceToolbar, sl);
}

/********************* registration ********************/

void ED_spacetype_toolbar(void)
{
  std::unique_ptr<SpaceType> st = std::make_unique<SpaceType>();

  ARegionType *art;

  st->spaceid = SPACE_TOOLBAR;
  STRNCPY(st->name, "Toolbar");

  st->create = toolbar_create;
  st->duplicate = toolbar_duplicate;
  st->blend_write = toolbar_space_blend_write;

  /* regions: main window */
  art = static_cast<ARegionType *>(MEM_callocN(sizeof(ARegionType), "spacetype toolbar region"));
  art->regionid = RGN_TYPE_WINDOW;

  art->init = toolbar_main_region_init;
  art->draw = toolbar_main_region_draw;
  art->listener = toolbar_main_region_listener;

  BLI_addhead(&st->regiontypes, art);

  /* regions: header */
  art = static_cast<ARegionType *>(MEM_callocN(sizeof(ARegionType), "spacetype toolbar region"));
  art->regionid = RGN_TYPE_HEADER;
  art->prefsizey = HEADERY;
  art->keymapflag = ED_KEYMAP_UI | ED_KEYMAP_VIEW2D | ED_KEYMAP_HEADER;
  art->listener = toolbar_header_listener;
  art->init = toolbar_header_region_init;
  art->draw = toolbar_header_region_draw;

  BLI_addhead(&st->regiontypes, art);

  BKE_spacetype_register(std::move(st));
}

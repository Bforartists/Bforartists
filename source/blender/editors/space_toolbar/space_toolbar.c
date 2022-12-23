/* SPDX-License-Identifier: GPL-2.0-or-later
 */

/** \file blender/editors/space_toolbar/space_toolbar.c
 *  \ingroup sptoolbar
 */

// BFA - barebone

#include <string.h>

#include "MEM_guardedalloc.h"

#include "BLI_blenlib.h"

#include "BKE_context.h"
#include "BKE_screen.h"

#include "ED_screen.h"
#include "ED_space_api.h"

#include "WM_api.h"
#include "WM_types.h"

#include "GPU_framebuffer.h"
#include "UI_resources.h"
#include "UI_view2d.h"

#include "BLO_read_write.h"

static SpaceLink *toolbar_create(const ScrArea *UNUSED(area), const Scene *UNUSED(scene))
{
  ARegion *region;
  SpaceToolbar *stoolbar;

  stoolbar = MEM_callocN(sizeof(SpaceToolbar), "inittoolbar");
  stoolbar->spacetype = SPACE_TOOLBAR;

  /* header */
  region = MEM_callocN(sizeof(ARegion), "header for toolbar");

  BLI_addtail(&stoolbar->regionbase, region);
  region->regiontype = RGN_TYPE_HEADER;
  region->alignment = RGN_ALIGN_TOP;

  /* main area */
  region = MEM_callocN(sizeof(ARegion), "main area for toolbar");

  BLI_addtail(&stoolbar->regionbase, region);
  region->regiontype = RGN_TYPE_WINDOW;

  return (SpaceLink *)stoolbar;
}

/* add handlers, stuff you only do once or on area/region changes */
static void toolbar_main_area_init(wmWindowManager *UNUSED(wm), ARegion *region)
{
  UI_view2d_region_reinit(&region->v2d, V2D_COMMONVIEW_CUSTOM, region->winx, region->winy);
}

static void toolbar_main_area_draw(const bContext *C, ARegion *region)
{
  /* draw entirely, view changes should be handled here */
  /*SpaceToolbar *stoolbar = CTX_wm_space_toolbar(C);*/ /*bfa - commented out. variable not needed
                                                           yet*/
  View2D *v2d = &region->v2d;

  /* clear and setup matrix */
  UI_ThemeClearColor(TH_BACK);

  /* works best with no view2d matrix set */
  UI_view2d_view_ortho(v2d);

  /* reset view matrix */
  UI_view2d_view_restore(C);

  /* scrollers */
  UI_view2d_scrollers_draw(v2d, NULL);
}

static void toolbar_header_area_init(wmWindowManager *UNUSED(wm), ARegion *region)
{
  ED_region_header_init(region);
}

static void toolbar_header_area_draw(const bContext *C, ARegion *region)
{
  ED_region_header(C, region);
}

static void toolbar_main_area_listener(const wmRegionListenerParams *params)
{
  ScrArea *area = params->area;
  const wmNotifier *wmn = params->notifier;
  // SpaceInfo *sinfo = sa->spacedata.first;

  /* context changes */
  switch (wmn->category) {
    case NC_SPACE:
      if (wmn->data == ND_SPACE_INFO_REPORT) {
        /* redraw also but only for report view, could do less redraws by checking the type */
        ED_area_tag_redraw(area);
      }
      break;
  }
}

static void toolbar_header_listener(const wmRegionListenerParams *params)
{
  ScrArea *area = params->area;
  const wmNotifier *wmn = params->notifier;
  /* context changes */
  switch (wmn->category) {
    case NC_WM:
      if (wmn->data == ND_JOB) {
        ED_area_tag_redraw(area);
      }
      break;
    case NC_SCENE:
      if (wmn->data == ND_RENDER_RESULT) {
        ED_area_tag_redraw(area);
      }
      break;
    case NC_SPACE:
      if (wmn->data == ND_SPACE_INFO) {
        ED_area_tag_redraw(area);
      }
      break;
    case NC_ID:
      if (wmn->action == NA_RENAME) {
        ED_area_tag_redraw(area);
      }
      break;
  }
}

static void toolbar_blend_write(BlendWriter *writer, SpaceLink *sl)
{
  BLO_write_struct(writer, SpaceToolbar, sl);
}

/********************* registration ********************/

static void info_blend_write(BlendWriter *writer, SpaceLink *sl)
{
  BLO_write_struct(writer, SpaceToolbar, sl);
}

/* only called once, from space/spacetypes.c */
void ED_spacetype_toolbar(void)
{
  SpaceType *st = MEM_callocN(sizeof(SpaceType), "spacetype toolbar");
  ARegionType *art;

  st->spaceid = SPACE_TOOLBAR;
  STRNCPY(st->name, "Toolbar");

  st->create = toolbar_create;
  st->blend_read_data = NULL;
  st->blend_read_lib = NULL;
  st->blend_write = toolbar_blend_write;

  /* regions: main window */
  art = MEM_callocN(sizeof(ARegionType), "spacetype toolbar region");
  art->regionid = RGN_TYPE_WINDOW;

  art->init = toolbar_main_area_init;
  art->draw = toolbar_main_area_draw;
  art->listener = toolbar_main_area_listener;

  BLI_addhead(&st->regiontypes, art);

  /* regions: header */
  art = MEM_callocN(sizeof(ARegionType), "spacetype toolbar region");
  art->regionid = RGN_TYPE_HEADER;
  art->prefsizey = HEADERY;
  art->keymapflag = ED_KEYMAP_UI | ED_KEYMAP_VIEW2D | ED_KEYMAP_HEADER;
  art->listener = toolbar_header_listener;
  art->init = toolbar_header_area_init;
  art->draw = toolbar_header_area_draw;

  BLI_addhead(&st->regiontypes, art);

  BKE_spacetype_register(st);
}

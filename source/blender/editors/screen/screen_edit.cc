/* SPDX-FileCopyrightText: 2008 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup edscr
 */

#include <cmath>
#include <cstring>

#include "MEM_guardedalloc.h"

#include "DNA_object_types.h"
#include "DNA_scene_types.h"
#include "DNA_userdef_types.h"
#include "DNA_workspace_types.h"

#include "BLI_blenlib.h"
#include "BLI_utildefines.h"

#include "BKE_context.h"
#include "BKE_global.h"
#include "BKE_icons.h"
#include "BKE_image.h"
#include "BKE_layer.h"
#include "BKE_lib_id.h"
#include "BKE_main.h"
#include "BKE_scene.h"
#include "BKE_screen.hh"
#include "BKE_sound.h"
#include "BKE_workspace.h"

#include "WM_api.hh"
#include "WM_types.hh"

#include "ED_clip.hh"
#include "ED_node.hh"
#include "ED_screen.hh"
#include "ED_screen_types.hh"

#include "UI_interface.hh"

#include "WM_message.hh"
#include "WM_toolsystem.h"

#include "DEG_depsgraph_query.hh"

#include "screen_intern.h" /* own module include */

/* adds no space data */
static ScrArea *screen_addarea_ex(ScrAreaMap *area_map,
                                  ScrVert *bottom_left,
                                  ScrVert *top_left,
                                  ScrVert *top_right,
                                  ScrVert *bottom_right,
                                  const eSpace_Type space_type)
{
  ScrArea *area = static_cast<ScrArea *>(MEM_callocN(sizeof(ScrArea), "addscrarea"));

  area->v1 = bottom_left;
  area->v2 = top_left;
  area->v3 = top_right;
  area->v4 = bottom_right;
  area->spacetype = space_type;

  BLI_addtail(&area_map->areabase, area);

  return area;
}
static ScrArea *screen_addarea(bScreen *screen,
                               ScrVert *left_bottom,
                               ScrVert *left_top,
                               ScrVert *right_top,
                               ScrVert *right_bottom,
                               const eSpace_Type space_type)
{
  return screen_addarea_ex(
      AREAMAP_FROM_SCREEN(screen), left_bottom, left_top, right_top, right_bottom, space_type);
}

static void screen_delarea(bContext *C, bScreen *screen, ScrArea *area)
{

  ED_area_exit(C, area);

  BKE_screen_area_free(area);

  BLI_remlink(&screen->areabase, area);
  MEM_freeN(area);
}

ScrArea *area_split(const wmWindow *win,
                    bScreen *screen,
                    ScrArea *area,
                    const eScreenAxis dir_axis,
                    const float fac,
                    const bool merge)
{
  ScrArea *newa = nullptr;

  if (area == nullptr) {
    return nullptr;
  }

  rcti window_rect;
  WM_window_rect_calc(win, &window_rect);

  short split = screen_geom_find_area_split_point(area, &window_rect, dir_axis, fac);
  if (split == 0) {
    return nullptr;
  }

  /* NOTE(@ideasman42): regarding (fac > 0.5f) checks below.
   * normally it shouldn't matter which is used since the copy should match the original
   * however with viewport rendering and python console this isn't the case. */

  if (dir_axis == SCREEN_AXIS_H) {
    /* new vertices */
    ScrVert *sv1 = screen_geom_vertex_add(screen, area->v1->vec.x, split);
    ScrVert *sv2 = screen_geom_vertex_add(screen, area->v4->vec.x, split);

    /* new edges */
    screen_geom_edge_add(screen, area->v1, sv1);
    screen_geom_edge_add(screen, sv1, area->v2);
    screen_geom_edge_add(screen, area->v3, sv2);
    screen_geom_edge_add(screen, sv2, area->v4);
    screen_geom_edge_add(screen, sv1, sv2);

    if (fac > 0.5f) {
      /* new areas: top */
      newa = screen_addarea(screen, sv1, area->v2, area->v3, sv2, eSpace_Type(area->spacetype));

      /* area below */
      area->v2 = sv1;
      area->v3 = sv2;
    }
    else {
      /* new areas: bottom */
      newa = screen_addarea(screen, area->v1, sv1, sv2, area->v4, eSpace_Type(area->spacetype));

      /* area above */
      area->v1 = sv1;
      area->v4 = sv2;
    }

    ED_area_data_copy(newa, area, true);
  }
  else {
    /* new vertices */
    ScrVert *sv1 = screen_geom_vertex_add(screen, split, area->v1->vec.y);
    ScrVert *sv2 = screen_geom_vertex_add(screen, split, area->v2->vec.y);

    /* new edges */
    screen_geom_edge_add(screen, area->v1, sv1);
    screen_geom_edge_add(screen, sv1, area->v4);
    screen_geom_edge_add(screen, area->v2, sv2);
    screen_geom_edge_add(screen, sv2, area->v3);
    screen_geom_edge_add(screen, sv1, sv2);

    if (fac > 0.5f) {
      /* new areas: right */
      newa = screen_addarea(screen, sv1, sv2, area->v3, area->v4, eSpace_Type(area->spacetype));

      /* area left */
      area->v3 = sv2;
      area->v4 = sv1;
    }
    else {
      /* new areas: left */
      newa = screen_addarea(screen, area->v1, area->v2, sv2, sv1, eSpace_Type(area->spacetype));

      /* area right */
      area->v1 = sv1;
      area->v2 = sv2;
    }

    ED_area_data_copy(newa, area, true);
  }

  /* remove double vertices en edges */
  if (merge) {
    BKE_screen_remove_double_scrverts(screen);
  }
  BKE_screen_remove_double_scredges(screen);
  BKE_screen_remove_unused_scredges(screen);

  return newa;
}

bScreen *screen_add(Main *bmain, const char *name, const rcti *rect)
{
  bScreen *screen = static_cast<bScreen *>(BKE_libblock_alloc(bmain, ID_SCR, name, 0));
  screen->do_refresh = true;
  screen->redraws_flag = TIME_ALL_3D_WIN | TIME_ALL_ANIM_WIN;

  ScrVert *sv1 = screen_geom_vertex_add(screen, rect->xmin, rect->ymin);
  ScrVert *sv2 = screen_geom_vertex_add(screen, rect->xmin, rect->ymax - 1);
  ScrVert *sv3 = screen_geom_vertex_add(screen, rect->xmax - 1, rect->ymax - 1);
  ScrVert *sv4 = screen_geom_vertex_add(screen, rect->xmax - 1, rect->ymin);

  screen_geom_edge_add(screen, sv1, sv2);
  screen_geom_edge_add(screen, sv2, sv3);
  screen_geom_edge_add(screen, sv3, sv4);
  screen_geom_edge_add(screen, sv4, sv1);

  /* dummy type, no spacedata */
  screen_addarea(screen, sv1, sv2, sv3, sv4, SPACE_EMPTY);

  return screen;
}

void screen_data_copy(bScreen *to, bScreen *from)
{
  /* Free contents of 'to', is from blenkernel `screen.cc`. */
  BKE_screen_free_data(to);

  to->flag = from->flag;

  BLI_duplicatelist(&to->vertbase, &from->vertbase);
  BLI_duplicatelist(&to->edgebase, &from->edgebase);
  BLI_duplicatelist(&to->areabase, &from->areabase);
  BLI_listbase_clear(&to->regionbase);

  ScrVert *s2 = static_cast<ScrVert *>(to->vertbase.first);
  for (ScrVert *s1 = static_cast<ScrVert *>(from->vertbase.first); s1;
       s1 = s1->next, s2 = s2->next) {
    s1->newv = s2;
  }

  LISTBASE_FOREACH (ScrEdge *, se, &to->edgebase) {
    se->v1 = se->v1->newv;
    se->v2 = se->v2->newv;
    BKE_screen_sort_scrvert(&(se->v1), &(se->v2));
  }

  ScrArea *from_area = static_cast<ScrArea *>(from->areabase.first);
  LISTBASE_FOREACH (ScrArea *, area, &to->areabase) {
    area->v1 = area->v1->newv;
    area->v2 = area->v2->newv;
    area->v3 = area->v3->newv;
    area->v4 = area->v4->newv;

    BLI_listbase_clear(&area->spacedata);
    BLI_listbase_clear(&area->regionbase);
    BLI_listbase_clear(&area->actionzones);
    BLI_listbase_clear(&area->handlers);

    ED_area_data_copy(area, from_area, true);

    from_area = from_area->next;
  }

  /* put at zero (needed?) */
  LISTBASE_FOREACH (ScrVert *, s1, &from->vertbase) {
    s1->newv = nullptr;
  }
}

void screen_new_activate_prepare(const wmWindow *win, bScreen *screen_new)
{
  screen_new->winid = win->winid;
  screen_new->do_refresh = true;
  screen_new->do_draw = true;
}

eScreenDir area_getorientation(ScrArea *sa_a, ScrArea *sa_b)
{
  if (sa_a == nullptr || sa_b == nullptr || sa_a == sa_b) {
    return SCREEN_DIR_NONE;
  }

  short left_a = sa_a->v1->vec.x;
  short right_a = sa_a->v3->vec.x;
  short top_a = sa_a->v3->vec.y;
  short bottom_a = sa_a->v1->vec.y;

  short left_b = sa_b->v1->vec.x;
  short right_b = sa_b->v3->vec.x;
  short top_b = sa_b->v3->vec.y;
  short bottom_b = sa_b->v1->vec.y;

  /* How much these areas share a common edge. */
  short overlapx = MIN2(right_a, right_b) - MAX2(left_a, left_b);
  short overlapy = MIN2(top_a, top_b) - MAX2(bottom_a, bottom_b);

  /* Minimum overlap required. */
  const short minx = MIN3(AREAJOINTOLERANCEX, right_a - left_a, right_b - left_b);
  const short miny = MIN3(AREAJOINTOLERANCEY, top_a - bottom_a, top_b - bottom_b);

  if (top_a == bottom_b && overlapx >= minx) {
    return eScreenDir(1); /* sa_a to bottom of sa_b = N */
  }
  if (bottom_a == top_b && overlapx >= minx) {
    return eScreenDir(3); /* sa_a on top of sa_b = S */
  }
  if (left_a == right_b && overlapy >= miny) {
    return eScreenDir(0); /* sa_a to right of sa_b = W */
  }
  if (right_a == left_b && overlapy >= miny) {
    return eScreenDir(2); /* sa_a to left of sa_b = E */
  }

  return eScreenDir(-1);
}

void area_getoffsets(
    ScrArea *sa_a, ScrArea *sa_b, const eScreenDir dir, int *r_offset1, int *r_offset2)
{
  if (sa_a == nullptr || sa_b == nullptr) {
    *r_offset1 = INT_MAX;
    *r_offset2 = INT_MAX;
  }
  else if (dir == SCREEN_DIR_W) { /* West: sa on right and sa_b to the left. */
    *r_offset1 = sa_b->v3->vec.y - sa_a->v2->vec.y;
    *r_offset2 = sa_b->v4->vec.y - sa_a->v1->vec.y;
  }
  else if (dir == SCREEN_DIR_N) { /* North: sa below and sa_b above. */
    *r_offset1 = sa_a->v2->vec.x - sa_b->v1->vec.x;
    *r_offset2 = sa_a->v3->vec.x - sa_b->v4->vec.x;
  }
  else if (dir == SCREEN_DIR_E) { /* East: sa on left and sa_b to the right. */
    *r_offset1 = sa_b->v2->vec.y - sa_a->v3->vec.y;
    *r_offset2 = sa_b->v1->vec.y - sa_a->v4->vec.y;
  }
  else if (dir == SCREEN_DIR_S) { /* South: sa above and sa_b below. */
    *r_offset1 = sa_a->v1->vec.x - sa_b->v2->vec.x;
    *r_offset2 = sa_a->v4->vec.x - sa_b->v3->vec.x;
  }
  else {
    BLI_assert(dir == SCREEN_DIR_NONE);
    *r_offset1 = INT_MAX;
    *r_offset2 = INT_MAX;
  }
}

/* Screen verts with horizontal position equal to from_x are moved to to_x. */
static void screen_verts_halign(const wmWindow *win,
                                const bScreen *screen,
                                const short from_x,
                                const short to_x)
{
  ED_screen_verts_iter(win, screen, v1)
  {
    if (v1->vec.x == from_x) {
      v1->vec.x = to_x;
    }
  }
}

/* Screen verts with vertical position equal to from_y are moved to to_y. */
static void screen_verts_valign(const wmWindow *win,
                                const bScreen *screen,
                                const short from_y,
                                const short to_y)
{
  ED_screen_verts_iter(win, screen, v1)
  {
    if (v1->vec.y == from_y) {
      v1->vec.y = to_y;
    }
  }
}

/* Test if two adjoining areas can be aligned by having their screen edges adjusted. */
static bool screen_areas_can_align(bScreen *screen, ScrArea *sa1, ScrArea *sa2, eScreenDir dir)
{
  if (dir == SCREEN_DIR_NONE) {
    return false;
  }

  int offset1;
  int offset2;
  area_getoffsets(sa1, sa2, dir, &offset1, &offset2);

  const int tolerance = SCREEN_DIR_IS_HORIZONTAL(dir) ? AREAJOINTOLERANCEY : AREAJOINTOLERANCEX;
  if ((abs(offset1) >= tolerance) || (abs(offset2) >= tolerance)) {
    /* Misalignment is too great. */
    return false;
  }

  /* Areas that are _smaller_ than minimum sizes, sharing an edge to be moved. See #100772. */
  if (SCREEN_DIR_IS_VERTICAL(dir)) {
    const short xmin = MIN2(sa1->v1->vec.x, sa2->v1->vec.x);
    const short xmax = MAX2(sa1->v3->vec.x, sa2->v3->vec.x);
    LISTBASE_FOREACH (ScrArea *, area, &screen->areabase) {
      if (ELEM(area, sa1, sa2)) {
        continue;
      }
      if (area->v3->vec.x - area->v1->vec.x < tolerance &&
          (area->v1->vec.x == xmin || area->v3->vec.x == xmax))
      {
        WM_report(RPT_ERROR, "A narrow vertical area interferes with this operation");
        return false;
      }
    }
  }
  else {
    const short ymin = MIN2(sa1->v1->vec.y, sa2->v1->vec.y);
    const short ymax = MAX2(sa1->v3->vec.y, sa2->v3->vec.y);
    LISTBASE_FOREACH (ScrArea *, area, &screen->areabase) {
      if (ELEM(area, sa1, sa2)) {
        continue;
      }
      if (area->v3->vec.y - area->v1->vec.y < tolerance &&
          (area->v1->vec.y == ymin || area->v3->vec.y == ymax))
      {
        WM_report(RPT_ERROR, "A narrow horizontal area interferes with this operation");
        return false;
      }
    }
  }

  return true;
}

/* Adjust all screen edges to allow joining two areas. 'dir' value is like area_getorientation().
 */
static bool screen_areas_align(
    bContext *C, bScreen *screen, ScrArea *sa1, ScrArea *sa2, const eScreenDir dir)
{
  if (!screen_areas_can_align(screen, sa1, sa2, dir)) {
    return false;
  }

  wmWindow *win = CTX_wm_window(C);

  if (SCREEN_DIR_IS_HORIZONTAL(dir)) {
    /* horizontal join, use average for new top and bottom. */
    int top = (sa1->v2->vec.y + sa2->v2->vec.y) / 2;
    int bottom = (sa1->v4->vec.y + sa2->v4->vec.y) / 2;

    /* Move edges exactly matching source top and bottom. */
    screen_verts_valign(win, screen, sa1->v2->vec.y, top);
    screen_verts_valign(win, screen, sa1->v4->vec.y, bottom);

    /* Move edges exactly matching target top and bottom. */
    screen_verts_valign(win, screen, sa2->v2->vec.y, top);
    screen_verts_valign(win, screen, sa2->v4->vec.y, bottom);
  }
  else {
    /* Vertical join, use averages for new left and right. */
    int left = (sa1->v1->vec.x + sa2->v1->vec.x) / 2;
    int right = (sa1->v3->vec.x + sa2->v3->vec.x) / 2;

    /* Move edges exactly matching source left and right. */
    screen_verts_halign(win, screen, sa1->v1->vec.x, left);
    screen_verts_halign(win, screen, sa1->v3->vec.x, right);

    /* Move edges exactly matching target left and right */
    screen_verts_halign(win, screen, sa2->v1->vec.x, left);
    screen_verts_halign(win, screen, sa2->v3->vec.x, right);
  }

  return true;
}

/* Simple join of two areas without any splitting. Will return false if not possible. */
static bool screen_area_join_aligned(bContext *C, bScreen *screen, ScrArea *sa1, ScrArea *sa2)
{
  const eScreenDir dir = area_getorientation(sa1, sa2);

  /* Ensure that the area edges are exactly aligned. */
  if (!screen_areas_align(C, screen, sa1, sa2, dir)) {
    return false;
  }

  if (dir == SCREEN_DIR_W) { /* sa1 to right of sa2 = West. */
    sa1->v1 = sa2->v1;       /* BL */
    sa1->v2 = sa2->v2;       /* TL */
    screen_geom_edge_add(screen, sa1->v2, sa1->v3);
    screen_geom_edge_add(screen, sa1->v1, sa1->v4);
  }
  else if (dir == SCREEN_DIR_N) { /* sa1 to bottom of sa2 = North. */
    sa1->v2 = sa2->v2;            /* TL */
    sa1->v3 = sa2->v3;            /* TR */
    screen_geom_edge_add(screen, sa1->v1, sa1->v2);
    screen_geom_edge_add(screen, sa1->v3, sa1->v4);
  }
  else if (dir == SCREEN_DIR_E) { /* sa1 to left of sa2 = East. */
    sa1->v3 = sa2->v3;            /* TR */
    sa1->v4 = sa2->v4;            /* BR */
    screen_geom_edge_add(screen, sa1->v2, sa1->v3);
    screen_geom_edge_add(screen, sa1->v1, sa1->v4);
  }
  else if (dir == SCREEN_DIR_S) { /* sa1 on top of sa2 = South. */
    sa1->v1 = sa2->v1;            /* BL */
    sa1->v4 = sa2->v4;            /* BR */
    screen_geom_edge_add(screen, sa1->v1, sa1->v2);
    screen_geom_edge_add(screen, sa1->v3, sa1->v4);
  }

  screen_delarea(C, screen, sa2);
  BKE_screen_remove_double_scrverts(screen);
  /* Update preview thumbnail */
  BKE_icon_changed(screen->id.icon_id);

  return true;
}

/* Slice off and return new area. "Reverse" gives right/bottom, rather than left/top. */
static ScrArea *screen_area_trim(
    bContext *C, bScreen *screen, ScrArea **area, int size, eScreenDir dir, bool reverse)
{
  const bool vertical = SCREEN_DIR_IS_VERTICAL(dir);
  if (abs(size) < (vertical ? AREAJOINTOLERANCEX : AREAJOINTOLERANCEY)) {
    return nullptr;
  }

  /* Measurement with ScrVerts because winx and winy might not be correct at this time. */
  float fac = abs(size) / float(vertical ? ((*area)->v3->vec.x - (*area)->v1->vec.x) :
                                           ((*area)->v3->vec.y - (*area)->v1->vec.y));
  fac = (reverse == vertical) ? 1.0f - fac : fac;
  ScrArea *newsa = area_split(
      CTX_wm_window(C), screen, *area, vertical ? SCREEN_AXIS_V : SCREEN_AXIS_H, fac, true);

  /* area_split always returns smallest of the two areas, so might have to swap. */
  if (((fac > 0.5f) == vertical) != reverse) {
    ScrArea *temp = *area;
    *area = newsa;
    newsa = temp;
  }

  return newsa;
}

/* Join any two neighboring areas. Might create new areas, kept if over min_remainder. */
static bool screen_area_join_ex(
    bContext *C, bScreen *screen, ScrArea *sa1, ScrArea *sa2, bool close_all_remainders)
{
  const eScreenDir dir = area_getorientation(sa1, sa2);
  if (dir == SCREEN_DIR_NONE) {
    return false;
  }

  int offset1;
  int offset2;
  area_getoffsets(sa1, sa2, dir, &offset1, &offset2);

  /* Split Left/Top into new area if overhanging. */
  ScrArea *side1 = screen_area_trim(C, screen, (offset1 > 0) ? &sa2 : &sa1, offset1, dir, false);

  /* Split Right/Bottom into new area if overhanging. */
  ScrArea *side2 = screen_area_trim(C, screen, (offset2 > 0) ? &sa1 : &sa2, offset2, dir, true);

  /* The two areas now line up, so join them. */
  screen_area_join_aligned(C, screen, sa1, sa2);

  if (close_all_remainders || offset1 < 0 || offset2 > 0) {
    /* Close both if trimming `sa1`. */
    screen_area_close(C, screen, side1);
    screen_area_close(C, screen, side2);
  }

  BKE_icon_changed(screen->id.icon_id);
  return true;
}

int screen_area_join(bContext *C, bScreen *screen, ScrArea *sa1, ScrArea *sa2)
{
  return screen_area_join_ex(C, screen, sa1, sa2, false);
}

bool screen_area_close(bContext *C, bScreen *screen, ScrArea *area)
{
  if (area == nullptr) {
    return false;
  }

  ScrArea *sa2 = nullptr;
  float best_alignment = 0.0f;

  LISTBASE_FOREACH (ScrArea *, neighbor, &screen->areabase) {
    const eScreenDir dir = area_getorientation(area, neighbor);
    /* Must at least partially share an edge and not be a global area. */
    if ((dir != SCREEN_DIR_NONE) && (neighbor->global == nullptr)) {
      /* Winx/Winy might not be updated yet, so get lengths from verts. */
      const bool vertical = SCREEN_DIR_IS_VERTICAL(dir);
      const int area_length = vertical ? (area->v3->vec.x - area->v1->vec.x) :
                                         (area->v3->vec.y - area->v1->vec.y);
      const int ar_length = vertical ? (neighbor->v3->vec.x - neighbor->v1->vec.x) :
                                       (neighbor->v3->vec.y - neighbor->v1->vec.y);
      /* Calculate the ratio of the lengths of the shared edges. */
      float alignment = MIN2(area_length, ar_length) / float(MAX2(area_length, ar_length));
      if (alignment > best_alignment) {
        best_alignment = alignment;
        sa2 = neighbor;
      }
    }
  }

  /* Join from neighbor into this area to close it. */
  return screen_area_join_ex(C, screen, sa2, area, true);
}

void screen_area_spacelink_add(const Scene *scene, ScrArea *area, eSpace_Type space_type)
{
  SpaceType *stype = BKE_spacetype_from_id(space_type);
  SpaceLink *slink = stype->create(area, scene);

  area->regionbase = slink->regionbase;

  BLI_addhead(&area->spacedata, slink);
  BLI_listbase_clear(&slink->regionbase);
}

/* ****************** EXPORTED API TO OTHER MODULES *************************** */

/* screen sets cursor based on active region */
static void region_cursor_set_ex(wmWindow *win, ScrArea *area, ARegion *region, bool swin_changed)
{
  BLI_assert(WM_window_get_active_screen(win)->active_region == region);
  if (win->tag_cursor_refresh || swin_changed || (region->type && region->type->event_cursor)) {
    win->tag_cursor_refresh = false;
    ED_region_cursor_set(win, area, region);
  }
}

static void region_cursor_set(wmWindow *win, bool swin_changed)
{
  bScreen *screen = WM_window_get_active_screen(win);

  ED_screen_areas_iter (win, screen, area) {
    LISTBASE_FOREACH (ARegion *, region, &area->regionbase) {
      if (region == screen->active_region) {
        region_cursor_set_ex(win, area, region, swin_changed);
        return;
      }
    }
  }
}

void ED_screen_do_listen(bContext *C, const wmNotifier *note)
{
  wmWindow *win = CTX_wm_window(C);
  bScreen *screen = CTX_wm_screen(C);

  /* generic notes */
  switch (note->category) {
    case NC_WM:
      if (note->data == ND_FILEREAD) {
        screen->do_draw = true;
      }
      break;
    case NC_WINDOW:
      screen->do_draw = true;
      break;
    case NC_SCREEN:
      if (note->action == NA_EDITED) {
        screen->do_draw = screen->do_refresh = true;
      }
      break;
    case NC_SCENE:
      if (note->data == ND_MODE) {
        region_cursor_set(win, true);
      }
      break;
  }
}

void ED_screen_refresh(wmWindowManager *wm, wmWindow *win)
{
  bScreen *screen = WM_window_get_active_screen(win);

  /* Exception for background mode, we only need the screen context. */
  if (!G.background) {

    /* Called even when creating the ghost window fails in #WM_window_open. */
    if (win->ghostwin) {
      /* Header size depends on DPI, let's verify. */
      WM_window_set_dpi(win);
    }

    ED_screen_global_areas_refresh(win);

    screen_geom_vertices_scale(win, screen);

    ED_screen_areas_iter (win, screen, area) {
      /* Set space-type and region callbacks, calls init() */
      /* Sets sub-windows for regions, adds handlers. */
      ED_area_init(wm, win, area);
    }

    /* wake up animtimer */
    if (screen->animtimer) {
      WM_event_timer_sleep(wm, win, screen->animtimer, false);
    }
  }

  if (G.debug & G_DEBUG_EVENTS) {
    printf("%s: set screen\n", __func__);
  }
  screen->do_refresh = false;
  /* Prevent multi-window errors. */
  screen->winid = win->winid;

  screen->context = reinterpret_cast<void *>(ed_screen_context);
}

void ED_screens_init(Main *bmain, wmWindowManager *wm)
{
  LISTBASE_FOREACH (wmWindow *, win, &wm->windows) {
    if (BKE_workspace_active_get(win->workspace_hook) == nullptr) {
      BKE_workspace_active_set(win->workspace_hook,
                               static_cast<WorkSpace *>(bmain->workspaces.first));
    }

    ED_screen_refresh(wm, win);
    if (win->eventstate) {
      ED_screen_set_active_region(nullptr, win, win->eventstate->xy);
    }
  }

  if (U.uiflag & USER_HEADER_FROM_PREF) {
    LISTBASE_FOREACH (bScreen *, screen, &bmain->screens) {
      BKE_screen_header_alignment_reset(screen);
    }
  }
}

static bool region_poll(const bContext *C,
                        const bScreen *screen,
                        const ScrArea *area,
                        const ARegion *region)
{
  if (!region->type || !region->type->poll) {
    /* Show region by default. */
    return true;
  }

  RegionPollParams params = {nullptr};
  params.screen = screen;
  params.area = area;
  params.region = region;
  params.context = C;

  return region->type->poll(&params);
}

static void screen_regions_poll(bContext *C, const wmWindow *win, bScreen *screen)
{
  ScrArea *prev_area = CTX_wm_area(C);
  ARegion *prev_region = CTX_wm_region(C);

  bool any_changed = false;
  ED_screen_areas_iter (win, screen, area) {
    CTX_wm_area_set(C, area);

    LISTBASE_FOREACH (ARegion *, region, &area->regionbase) {
      const int old_region_flag = region->flag;

      region->flag &= ~RGN_FLAG_POLL_FAILED;

      CTX_wm_region_set(C, region);
      if (region_poll(C, screen, area, region) == false) {
        region->flag |= RGN_FLAG_POLL_FAILED;
      }

      if (old_region_flag != region->flag) {
        any_changed = true;

        /* Enforce complete re-init. */
        region->v2d.flag &= ~V2D_IS_INIT;
        ED_region_visibility_change_update(C, area, region);
      }
    }
  }

  if (any_changed) {
    screen->do_refresh = true;
  }

  CTX_wm_area_set(C, prev_area);
  CTX_wm_region_set(C, prev_region);
}

void ED_screen_ensure_updated(bContext *C, wmWindowManager *wm, wmWindow *win, bScreen *screen)
{
  screen_regions_poll(C, win, screen);
  if (screen->do_refresh) {
    ED_screen_refresh(wm, win);
  }
}

void ED_region_remove(bContext *C, ScrArea *area, ARegion *region)
{
  ED_region_exit(C, region);
  BKE_area_region_free(area->type, region);
  BLI_freelinkN(&area->regionbase, region);
}

/* *********** exit calls are for closing running stuff ******** */

void ED_region_exit(bContext *C, ARegion *region)
{
  wmWindowManager *wm = CTX_wm_manager(C);
  wmWindow *win = CTX_wm_window(C);
  ARegion *prevar = CTX_wm_region(C);

  if (region->type && region->type->exit) {
    region->type->exit(wm, region);
  }

  CTX_wm_region_set(C, region);

  WM_event_remove_handlers(C, &region->handlers);
  WM_event_modal_handler_region_replace(win, region, nullptr);
  WM_draw_region_free(region);
  /* The region is not in a state that it can be visible in anymore. Reinitializing is needed. */
  region->visible = false;

  MEM_SAFE_FREE(region->headerstr);

  if (region->regiontimer) {
    WM_event_timer_remove(wm, win, region->regiontimer);
    region->regiontimer = nullptr;
  }

  WM_msgbus_clear_by_owner(wm->message_bus, region);

  CTX_wm_region_set(C, prevar);
}

void ED_area_exit(bContext *C, ScrArea *area)
{
  wmWindowManager *wm = CTX_wm_manager(C);
  wmWindow *win = CTX_wm_window(C);
  ScrArea *prevsa = CTX_wm_area(C);

  if (area->type && area->type->exit) {
    area->type->exit(wm, area);
  }

  CTX_wm_area_set(C, area);

  LISTBASE_FOREACH (ARegion *, region, &area->regionbase) {
    ED_region_exit(C, region);
  }

  WM_event_remove_handlers(C, &area->handlers);
  WM_event_modal_handler_area_replace(win, area, nullptr);

  CTX_wm_area_set(C, prevsa);
}

void ED_screen_exit(bContext *C, wmWindow *window, bScreen *screen)
{
  wmWindowManager *wm = CTX_wm_manager(C);
  wmWindow *prevwin = CTX_wm_window(C);

  CTX_wm_window_set(C, window);

  if (screen->animtimer) {
    WM_event_timer_remove(wm, window, screen->animtimer);

    Depsgraph *depsgraph = CTX_data_depsgraph_pointer(C);
    Scene *scene = WM_window_get_active_scene(prevwin);
    Scene *scene_eval = (Scene *)DEG_get_evaluated_id(depsgraph, &scene->id);
    BKE_sound_stop_scene(scene_eval);
  }
  screen->animtimer = nullptr;
  screen->scrubbing = false;

  screen->active_region = nullptr;

  LISTBASE_FOREACH (ARegion *, region, &screen->regionbase) {
    ED_region_exit(C, region);
  }
  LISTBASE_FOREACH (ScrArea *, area, &screen->areabase) {
    ED_area_exit(C, area);
  }
  /* Don't use ED_screen_areas_iter here, it skips hidden areas. */
  LISTBASE_FOREACH (ScrArea *, area, &window->global_areas.areabase) {
    ED_area_exit(C, area);
  }

  /* mark it available for use for other windows */
  screen->winid = 0;

  if (!WM_window_is_temp_screen(prevwin)) {
    /* use previous window if possible */
    CTX_wm_window_set(C, prevwin);
  }
  else {
    /* none otherwise */
    CTX_wm_window_set(C, nullptr);
  }
}

/* *********************************** */

/* case when on area-edge or in azones, or outside window */
static void screen_cursor_set(wmWindow *win, const int xy[2])
{
  const bScreen *screen = WM_window_get_active_screen(win);
  AZone *az = nullptr;
  ScrArea *area = nullptr;

  LISTBASE_FOREACH (ScrArea *, area_iter, &screen->areabase) {
    az = ED_area_actionzone_find_xy(area_iter, xy);
    /* Scrollers use default cursor and their zones extend outside of their
     * areas. Ignore here so we can always detect screen edges - #110085. */
    if (az && az->type != AZONE_REGION_SCROLL) {
      area = area_iter;
      break;
    }
  }

  if (area) {
    if (az->type == AZONE_AREA) {
      WM_cursor_set(win, WM_CURSOR_EDIT);
    }
    else if (az->type == AZONE_REGION) {
      if (ELEM(az->edge, AE_LEFT_TO_TOPRIGHT, AE_RIGHT_TO_TOPLEFT)) {
        WM_cursor_set(win, WM_CURSOR_X_MOVE);
      }
      else {
        WM_cursor_set(win, WM_CURSOR_Y_MOVE);
      }
    }
  }
  else {
    ScrEdge *actedge = screen_geom_find_active_scredge(win, screen, xy[0], xy[1]);

    if (actedge) {
      if (screen_geom_edge_is_horizontal(actedge)) {
        WM_cursor_set(win, WM_CURSOR_Y_MOVE);
      }
      else {
        WM_cursor_set(win, WM_CURSOR_X_MOVE);
      }
    }
    else {
      WM_cursor_set(win, WM_CURSOR_DEFAULT);
    }
  }
}

void ED_screen_set_active_region(bContext *C, wmWindow *win, const int xy[2])
{
  bScreen *screen = WM_window_get_active_screen(win);
  if (screen == nullptr) {
    return;
  }

  ScrArea *area = nullptr;
  ARegion *region_prev = screen->active_region;

  ED_screen_areas_iter (win, screen, area_iter) {
    if (xy[0] > (area_iter->totrct.xmin + BORDERPADDING) &&
        xy[0] < (area_iter->totrct.xmax - BORDERPADDING))
    {
      if (xy[1] > (area_iter->totrct.ymin + BORDERPADDING) &&
          xy[1] < (area_iter->totrct.ymax - BORDERPADDING))
      {
        if (ED_area_azones_update(area_iter, xy) == nullptr) {
          area = area_iter;
          break;
        }
      }
    }
  }
  if (area) {
    /* Make overlap active when mouse over. */
    LISTBASE_FOREACH (ARegion *, region, &area->regionbase) {
      if (ED_region_contains_xy(region, xy)) {
        screen->active_region = region;
        break;
      }
    }
  }
  else {
    screen->active_region = nullptr;
  }

  /* Check for redraw headers. */
  if (region_prev != screen->active_region) {

    ED_screen_areas_iter (win, screen, area_iter) {
      bool do_draw = false;

      LISTBASE_FOREACH (ARegion *, region, &area_iter->regionbase) {
        /* Call old area's deactivate if assigned. */
        if (region == region_prev && area_iter->type && area_iter->type->deactivate) {
          area_iter->type->deactivate(area_iter);
        }

        if (region == region_prev && region != screen->active_region) {
          wmGizmoMap *gzmap = region_prev->gizmo_map;
          if (gzmap) {
            if (WM_gizmo_highlight_set(gzmap, nullptr)) {
              ED_region_tag_redraw_no_rebuild(region_prev);
            }
          }
        }

        if (ELEM(region, region_prev, screen->active_region)) {
          do_draw = true;
        }
      }

      if (do_draw) {
        LISTBASE_FOREACH (ARegion *, region, &area_iter->regionbase) {
          if (ELEM(region->regiontype, RGN_TYPE_HEADER, RGN_TYPE_TOOL_HEADER)) {
            ED_region_tag_redraw_no_rebuild(region);
          }
        }
      }
    }

    /* Ensure test-motion values are never shared between regions. */
    const int mval[2] = {-1, -1};
    const bool use_cycle = !WM_cursor_test_motion_and_update(mval);
    UNUSED_VARS(use_cycle);
  }

  /* Cursors, for time being set always on edges,
   * otherwise the active region doesn't switch. */
  if (screen->active_region == nullptr) {
    screen_cursor_set(win, xy);
  }
  else {
    /* Notifier invokes freeing the buttons... causing a bit too much redraws. */
    region_cursor_set_ex(win, area, screen->active_region, region_prev != screen->active_region);

    if (region_prev != screen->active_region) {
      /* This used to be a notifier, but needs to be done immediate
       * because it can undo setting the right button as active due
       * to delayed notifier handling. */
      if (C) {
        UI_screen_free_active_but_highlight(C, screen);
      }
    }
  }
}

int ED_screen_area_active(const bContext *C)
{
  wmWindow *win = CTX_wm_window(C);
  bScreen *screen = CTX_wm_screen(C);
  ScrArea *area = CTX_wm_area(C);

  if (win && screen && area) {
    AZone *az = ED_area_actionzone_find_xy(area, win->eventstate->xy);

    if (az && az->type == AZONE_REGION) {
      return 1;
    }

    LISTBASE_FOREACH (ARegion *, region, &area->regionbase) {
      if (region == screen->active_region) {
        return 1;
      }
    }
  }
  return 0;
}

/**
 * Add an area and geometry (screen-edges and -vertices) for it to \a area_map,
 * with coordinates/dimensions matching \a rect.
 */
static ScrArea *screen_area_create_with_geometry(ScrAreaMap *area_map,
                                                 const rcti *rect,
                                                 eSpace_Type space_type)
{
  ScrVert *bottom_left = screen_geom_vertex_add_ex(area_map, rect->xmin, rect->ymin);
  ScrVert *top_left = screen_geom_vertex_add_ex(area_map, rect->xmin, rect->ymax);
  ScrVert *top_right = screen_geom_vertex_add_ex(area_map, rect->xmax, rect->ymax);
  ScrVert *bottom_right = screen_geom_vertex_add_ex(area_map, rect->xmax, rect->ymin);

  screen_geom_edge_add_ex(area_map, bottom_left, top_left);
  screen_geom_edge_add_ex(area_map, top_left, top_right);
  screen_geom_edge_add_ex(area_map, top_right, bottom_right);
  screen_geom_edge_add_ex(area_map, bottom_right, bottom_left);

  return screen_addarea_ex(area_map, bottom_left, top_left, top_right, bottom_right, space_type);
}

static void screen_area_set_geometry_rect(ScrArea *area, const rcti *rect)
{
  area->v1->vec.x = rect->xmin;
  area->v1->vec.y = rect->ymin;
  area->v2->vec.x = rect->xmin;
  area->v2->vec.y = rect->ymax;
  area->v3->vec.x = rect->xmax;
  area->v3->vec.y = rect->ymax;
  area->v4->vec.x = rect->xmax;
  area->v4->vec.y = rect->ymin;
}

static void screen_global_area_refresh(wmWindow *win,
                                       bScreen *screen,
                                       const eSpace_Type space_type,
                                       GlobalAreaAlign align,
                                       const rcti *rect,
                                       const short height_cur,
                                       const short height_min,
                                       const short height_max)
{
  /* Full-screens shouldn't have global areas. Don't touch them. */
  if (screen->state == SCREENFULL) {
    return;
  }

  ScrArea *area = nullptr;
  LISTBASE_FOREACH (ScrArea *, area_iter, &win->global_areas.areabase) {
    if (area_iter->spacetype == space_type) {
      area = area_iter;
      break;
    }
  }

  if (area) {
    screen_area_set_geometry_rect(area, rect);
  }
  else {
    area = screen_area_create_with_geometry(&win->global_areas, rect, space_type);
    screen_area_spacelink_add(WM_window_get_active_scene(win), area, space_type);

    /* Data specific to global areas. */
    area->global = static_cast<ScrGlobalAreaData *>(MEM_callocN(sizeof(*area->global), __func__));
    area->global->size_max = height_max;
    area->global->size_min = height_min;
    area->global->align = align;
  }

  if (area->global->cur_fixed_height != height_cur) {
    /* Refresh layout if size changes. */
    area->global->cur_fixed_height = height_cur;
    screen->do_refresh = true;
  }
}

static int screen_global_header_size()
{
  return int(ceilf(ED_area_headersize() / UI_SCALE_FAC));
}

static void screen_global_topbar_area_refresh(wmWindow *win, bScreen *screen)
{
  const short size = screen_global_header_size();
  rcti rect;

  BLI_rcti_init(&rect, 0, WM_window_pixels_x(win) - 1, 0, WM_window_pixels_y(win) - 1);
  rect.ymin = rect.ymax - size;

  screen_global_area_refresh(
      win, screen, SPACE_TOPBAR, GLOBAL_AREA_ALIGN_TOP, &rect, size, size, size);
}

static void screen_global_statusbar_area_refresh(wmWindow *win, bScreen *screen)
{
  const short size_min = 1;
  const short size_max = 0.8f * screen_global_header_size();
  const short size = (screen->flag & SCREEN_COLLAPSE_STATUSBAR) ? size_min : size_max;
  rcti rect;

  BLI_rcti_init(&rect, 0, WM_window_pixels_x(win) - 1, 0, WM_window_pixels_y(win) - 1);
  rect.ymax = rect.ymin + size_max;

  screen_global_area_refresh(
      win, screen, SPACE_STATUSBAR, GLOBAL_AREA_ALIGN_BOTTOM, &rect, size, size_min, size_max);
}

void ED_screen_global_areas_sync(wmWindow *win)
{
  /* Update screen flags from height in window, this is weak and perhaps
   * global areas should just become part of the screen instead. */
  bScreen *screen = BKE_workspace_active_screen_get(win->workspace_hook);

  screen->flag &= ~SCREEN_COLLAPSE_STATUSBAR;

  LISTBASE_FOREACH (ScrArea *, area, &win->global_areas.areabase) {
    if (area->global->cur_fixed_height == area->global->size_min) {
      if (area->spacetype == SPACE_STATUSBAR) {
        screen->flag |= SCREEN_COLLAPSE_STATUSBAR;
      }
    }
  }
}

void ED_screen_global_areas_refresh(wmWindow *win)
{
  /* Don't create global area for child and temporary windows. */
  bScreen *screen = BKE_workspace_active_screen_get(win->workspace_hook);
  if ((win->parent != nullptr) || screen->temp) {
    if (win->global_areas.areabase.first) {
      screen->do_refresh = true;
      BKE_screen_area_map_free(&win->global_areas);
    }
    return;
  }

  screen_global_topbar_area_refresh(win, screen);
  screen_global_statusbar_area_refresh(win, screen);
}

/* -------------------------------------------------------------------- */
/* Screen changing */

void screen_change_prepare(
    bScreen *screen_old, bScreen *screen_new, Main *bmain, bContext *C, wmWindow *win)
{
  UNUSED_VARS_NDEBUG(bmain);
  BLI_assert(BLI_findindex(&bmain->screens, screen_new) != -1);

  if (screen_old != screen_new) {
    wmTimer *wt = screen_old->animtimer;

    /* remove handlers referencing areas in old screen */
    LISTBASE_FOREACH (ScrArea *, area, &screen_old->areabase) {
      WM_event_remove_area_handler(&win->modalhandlers, area);
    }

    /* we put timer to sleep, so screen_exit has to think there's no timer */
    screen_old->animtimer = nullptr;
    if (wt) {
      WM_event_timer_sleep(CTX_wm_manager(C), win, wt, true);
    }
    ED_screen_exit(C, win, screen_old);

    /* Same scene, "transfer" playback to new screen. */
    if (wt) {
      screen_new->animtimer = wt;
    }
  }
}

void screen_change_update(bContext *C, wmWindow *win, bScreen *screen)
{
  Scene *scene = WM_window_get_active_scene(win);
  WorkSpace *workspace = BKE_workspace_active_get(win->workspace_hook);
  WorkSpaceLayout *layout = BKE_workspace_layout_find(workspace, screen);

  CTX_wm_window_set(C, win); /* stores C->wm.screen... hrmf */

  ED_screen_refresh(CTX_wm_manager(C), win);

  BKE_screen_view3d_scene_sync(screen, scene); /* sync new screen with scene data */
  WM_event_add_notifier(C, NC_WINDOW, nullptr);
  WM_event_add_notifier(C, NC_SCREEN | ND_LAYOUTSET, layout);

  /* Makes button highlights work. */
  WM_event_add_mousemove(win);
}

bool ED_screen_change(bContext *C, bScreen *screen)
{
  Main *bmain = CTX_data_main(C);
  wmWindow *win = CTX_wm_window(C);
  WorkSpace *workspace = BKE_workspace_active_get(win->workspace_hook);
  WorkSpaceLayout *layout = BKE_workspace_layout_find(workspace, screen);
  bScreen *screen_old = CTX_wm_screen(C);

  /* Get the actual layout/screen to be activated (guaranteed to be unused, even if that means
   * having to duplicate an existing one). */
  WorkSpaceLayout *layout_new = ED_workspace_screen_change_ensure_unused_layout(
      bmain, workspace, layout, layout, win);
  bScreen *screen_new = BKE_workspace_layout_screen_get(layout_new);

  screen_change_prepare(screen_old, screen_new, bmain, C, win);

  if (screen_old != screen_new) {
    WM_window_set_active_screen(win, workspace, screen_new);
    screen_change_update(C, win, screen_new);

    return true;
  }

  return false;
}

static void screen_set_3dview_camera(Scene *scene,
                                     ViewLayer *view_layer,
                                     ScrArea *area,
                                     View3D *v3d)
{
  /* fix any cameras that are used in the 3d view but not in the scene */
  BKE_screen_view3d_sync(v3d, scene);

  BKE_view_layer_synced_ensure(scene, view_layer);
  if (!v3d->camera || !BKE_view_layer_base_find(view_layer, v3d->camera)) {
    v3d->camera = BKE_view_layer_camera_find(scene, view_layer);
    // XXX if (screen == curscreen) handle_view3d_lock();
    if (!v3d->camera) {
      ListBase *regionbase;

      /* regionbase is in different place depending if space is active */
      if (v3d == area->spacedata.first) {
        regionbase = &area->regionbase;
      }
      else {
        regionbase = &v3d->regionbase;
      }

      LISTBASE_FOREACH (ARegion *, region, regionbase) {
        if (region->regiontype == RGN_TYPE_WINDOW) {
          RegionView3D *rv3d = static_cast<RegionView3D *>(region->regiondata);
          if (rv3d->persp == RV3D_CAMOB) {
            rv3d->persp = RV3D_PERSP;
          }
        }
      }
    }
  }
}

void ED_screen_scene_change(bContext *C,
                            wmWindow *win,
                            Scene *scene,
                            const bool refresh_toolsystem)
{
#if 0
  ViewLayer *view_layer_old = WM_window_get_active_view_layer(win);
#endif

  /* Switch scene. */
  win->scene = scene;
  if (CTX_wm_window(C) == win) {
    CTX_data_scene_set(C, scene);
  }

  /* Ensure the view layer name is updated. */
  WM_window_ensure_active_view_layer(win);
  ViewLayer *view_layer = WM_window_get_active_view_layer(win);

#if 0
  /* Mode Syncing. */
  if (view_layer_old) {
    WorkSpace *workspace = CTX_wm_workspace(C);
    Object *obact_new = BKE_view_layer_active_object_get(view_layer);
    UNUSED_VARS(obact_new);
    eObjectMode object_mode_old = workspace->object_mode;
    Object *obact_old = BKE_view_layer_active_object_get(view_layer_old);
    UNUSED_VARS(obact_old, object_mode_old);
  }
#endif

  /* Update 3D view cameras. */
  const bScreen *screen = WM_window_get_active_screen(win);
  LISTBASE_FOREACH (ScrArea *, area, &screen->areabase) {
    LISTBASE_FOREACH (SpaceLink *, sl, &area->spacedata) {
      if (sl->spacetype == SPACE_VIEW3D) {
        View3D *v3d = (View3D *)sl;
        screen_set_3dview_camera(scene, view_layer, area, v3d);
      }
    }
  }

  if (refresh_toolsystem) {
    WM_toolsystem_refresh_screen_window(win);
  }
}

ScrArea *ED_screen_full_newspace(bContext *C, ScrArea *area, int type)
{
  bScreen *newscreen = nullptr;
  ScrArea *newsa = nullptr;
  SpaceLink *newsl;

  if (!area || area->full == nullptr) {
    newscreen = ED_screen_state_maximized_create(C);
    newsa = static_cast<ScrArea *>(newscreen->areabase.first);
    BLI_assert(newsa->spacetype == SPACE_EMPTY);
  }

  if (!newsa) {
    newsa = area;
  }

  BLI_assert(newsa);
  newsl = static_cast<SpaceLink *>(newsa->spacedata.first);

  /* Tag the active space before changing, so we can identify it when user wants to go back. */
  if (newsl && (newsl->link_flag & SPACE_FLAG_TYPE_TEMPORARY) == 0) {
    newsl->link_flag |= SPACE_FLAG_TYPE_WAS_ACTIVE;
  }

  ED_area_newspace(C, newsa, type, (newsl && newsl->link_flag & SPACE_FLAG_TYPE_TEMPORARY));

  if (newscreen) {
    ED_screen_change(C, newscreen);
  }

  return newsa;
}

void ED_screen_full_prevspace(bContext *C, ScrArea *area)
{
  BLI_assert(area->full);

  if (area->flag & AREA_FLAG_STACKED_FULLSCREEN) {
    /* Stacked full-screen -> only go back to previous area and don't toggle out of full-screen. */
    ED_area_prevspace(C, area);
  }
  else {
    ED_screen_restore_temp_type(C, area);
  }
}

void ED_screen_restore_temp_type(bContext *C, ScrArea *area)
{
  SpaceLink *sl = static_cast<SpaceLink *>(area->spacedata.first);

  /* In case nether functions below run. */
  ED_area_tag_redraw(area);

  if (sl->link_flag & SPACE_FLAG_TYPE_TEMPORARY) {
    ED_area_prevspace(C, area);
  }

  if (area->full) {
    ED_screen_state_toggle(C, CTX_wm_window(C), area, SCREENMAXIMIZED);
  }
}

void ED_screen_full_restore(bContext *C, ScrArea *area)
{
  wmWindow *win = CTX_wm_window(C);
  SpaceLink *sl = static_cast<SpaceLink *>(area->spacedata.first);
  bScreen *screen = CTX_wm_screen(C);
  short state = (screen ? screen->state : short(SCREENMAXIMIZED));

  /* If full-screen area has a temporary space (such as a file browser or full-screen render
   * overlaid on top of an existing setup) then return to the previous space. */

  if (sl->next) {
    if (sl->link_flag & SPACE_FLAG_TYPE_TEMPORARY) {
      ED_screen_full_prevspace(C, area);
    }
    else {
      ED_screen_state_toggle(C, win, area, state);
    }
    /* WARNING: 'area' may be freed */
  }
  /* otherwise just tile the area again */
  else {
    ED_screen_state_toggle(C, win, area, state);
  }
}

/**
 * \param toggle_area: If this is set, its space data will be swapped with the one of the new empty
 *                     area, when toggling back it can be swapped back again.
 * \return The newly created screen with the non-normal area.
 *
 * \note The caller must run #ED_screen_change this is not done in this function
 * as it would attempt to initialize areas that don't yet have a space-type assigned
 * (converting them to 3D view without creating the space-data).
 */
static bScreen *screen_state_to_nonnormal(bContext *C,
                                          wmWindow *win,
                                          ScrArea *toggle_area,
                                          int state)
{
  Main *bmain = CTX_data_main(C);
  WorkSpace *workspace = WM_window_get_active_workspace(win);

  /* change from SCREENNORMAL to new state */
  WorkSpaceLayout *layout_new;
  ScrArea *newa;
  char newname[MAX_ID_NAME - 2];

  BLI_assert(ELEM(state, SCREENMAXIMIZED, SCREENFULL));

  bScreen *oldscreen = WM_window_get_active_screen(win);

  oldscreen->state = state;
  SNPRINTF(newname, "%s-%s", oldscreen->id.name + 2, "nonnormal");

  layout_new = ED_workspace_layout_add(bmain, workspace, win, newname);

  bScreen *screen = BKE_workspace_layout_screen_get(layout_new);
  screen->state = state;
  screen->redraws_flag = oldscreen->redraws_flag;
  screen->temp = oldscreen->temp;
  screen->flag = oldscreen->flag;

  /* timer */
  screen->animtimer = oldscreen->animtimer;
  oldscreen->animtimer = nullptr;

  newa = (ScrArea *)screen->areabase.first;

  /* swap area */
  if (toggle_area) {
    ED_area_data_swap(newa, toggle_area);
    newa->flag = toggle_area->flag; /* mostly for AREA_FLAG_WASFULLSCREEN */
  }

  if (state == SCREENFULL) {
    /* temporarily hide global areas */
    LISTBASE_FOREACH (ScrArea *, glob_area, &win->global_areas.areabase) {
      glob_area->global->flag |= GLOBAL_AREA_IS_HIDDEN;
    }
    /* temporarily hide the side panels/header */
    LISTBASE_FOREACH (ARegion *, region, &newa->regionbase) {
      region->flagfullscreen = region->flag;

      if (ELEM(region->regiontype,
               RGN_TYPE_UI,
               RGN_TYPE_HEADER,
               RGN_TYPE_TOOL_HEADER,
               RGN_TYPE_FOOTER,
               RGN_TYPE_TOOLS,
               RGN_TYPE_NAV_BAR,
               RGN_TYPE_EXECUTE,
               RGN_TYPE_ASSET_SHELF,
               RGN_TYPE_ASSET_SHELF_HEADER))
      {
        region->flag |= RGN_FLAG_HIDDEN;
      }
    }
  }

  if (toggle_area) {
    toggle_area->full = oldscreen;
  }
  newa->full = oldscreen;

  ED_area_tag_refresh(newa);

  return screen;
}

bScreen *ED_screen_state_maximized_create(bContext *C)
{
  return screen_state_to_nonnormal(C, CTX_wm_window(C), nullptr, SCREENMAXIMIZED);
}

ScrArea *ED_screen_state_toggle(bContext *C, wmWindow *win, ScrArea *area, const short state)
{
  wmWindowManager *wm = CTX_wm_manager(C);
  WorkSpace *workspace = WM_window_get_active_workspace(win);

  if (area) {
    /* ensure we don't have a button active anymore, can crash when
     * switching screens with tooltip open because region and tooltip
     * are no longer in the same screen */
    LISTBASE_FOREACH (ARegion *, region, &area->regionbase) {
      UI_blocklist_free(C, region);
      if (region->regiontimer) {
        WM_event_timer_remove(wm, nullptr, region->regiontimer);
        region->regiontimer = nullptr;
      }
    }

    /* prevent hanging status prints */
    ED_area_status_text(area, nullptr);
    ED_workspace_status_text(C, nullptr);
  }
  bScreen *screen;
  if (area && area->full) {
    WorkSpaceLayout *layout_old = WM_window_get_active_layout(win);
    /* restoring back to SCREENNORMAL */
    screen = area->full;                                   /* the old screen to restore */
    bScreen *oldscreen = WM_window_get_active_screen(win); /* the one disappearing */

    BLI_assert(BKE_workspace_layout_screen_get(layout_old) != screen);
    BLI_assert(BKE_workspace_layout_screen_get(layout_old)->state != SCREENNORMAL);

    screen->state = SCREENNORMAL;
    screen->flag = oldscreen->flag;

    /* Find old area we may have swapped dummy space data to. It's swapped back here. */
    ScrArea *fullsa = nullptr;
    LISTBASE_FOREACH (ScrArea *, old, &screen->areabase) {
      /* area to restore from is always first */
      if (old->full && !fullsa) {
        fullsa = old;
      }

      /* clear full screen state */
      old->full = nullptr;
    }

    area->full = nullptr;

    if (state == SCREENFULL) {
      /* unhide global areas */
      LISTBASE_FOREACH (ScrArea *, glob_area, &win->global_areas.areabase) {
        glob_area->global->flag &= ~GLOBAL_AREA_IS_HIDDEN;
      }
      /* restore the old side panels/header visibility */
      LISTBASE_FOREACH (ARegion *, region, &area->regionbase) {
        region->flag = region->flagfullscreen;
      }
    }

    if (fullsa) {
      ED_area_data_swap(fullsa, area);
      ED_area_tag_refresh(fullsa);
    }

    /* animtimer back */
    screen->animtimer = oldscreen->animtimer;
    oldscreen->animtimer = nullptr;

    ED_screen_change(C, screen);

    BKE_workspace_layout_remove(CTX_data_main(C), workspace, layout_old);

    /* After we've restored back to SCREENNORMAL, we have to wait with
     * screen handling as it uses the area coords which aren't updated yet.
     * Without doing so, the screen handling gets wrong area coords,
     * which in worst case can lead to crashes (see #43139) */
    screen->skip_handling = true;
  }
  else {
    ScrArea *toggle_area = area;

    /* use random area when we have no active one, e.g. when the
     * mouse is outside of the window and we open a file browser */
    if (!toggle_area || toggle_area->global) {
      bScreen *oldscreen = WM_window_get_active_screen(win);
      toggle_area = static_cast<ScrArea *>(oldscreen->areabase.first);
    }

    screen = screen_state_to_nonnormal(C, win, toggle_area, state);

    ED_screen_change(C, screen);
  }

  BLI_assert(CTX_wm_screen(C) == screen);
  BLI_assert(CTX_wm_area(C) == nullptr); /* May have been freed. */

  /* Setting the area is only needed for Python scripts that call
   * operators in succession before returning to the main event loop.
   * Without this, scripts can't run any operators that require
   * an area after toggling full-screen for example (see: #89526).
   * NOTE: an old comment stated this was "bad code",
   * however it doesn't cause problems so leave as-is. */
  CTX_wm_area_set(C, static_cast<ScrArea *>(screen->areabase.first));

  return static_cast<ScrArea *>(screen->areabase.first);
}

ScrArea *ED_screen_temp_space_open(bContext *C,
                                   const char *title,
                                   const rcti *rect_unscaled,
                                   eSpace_Type space_type,
                                   int display_type,
                                   bool dialog)
{
  ScrArea *area = nullptr;

  switch (display_type) {
    case USER_TEMP_SPACE_DISPLAY_WINDOW:
      if (WM_window_open(C,
                         title,
                         rect_unscaled,
                         int(space_type),
                         false,
                         dialog,
                         true,
                         WIN_ALIGN_LOCATION_CENTER,
                         nullptr,
                         nullptr))
      {
        area = CTX_wm_area(C);
      }
      break;
    case USER_TEMP_SPACE_DISPLAY_FULLSCREEN: {
      ScrArea *ctx_area = CTX_wm_area(C);

      if (ctx_area != nullptr && ctx_area->full) {
        area = ctx_area;
        ED_area_newspace(C, ctx_area, space_type, true);
        area->flag |= AREA_FLAG_STACKED_FULLSCREEN;
        ((SpaceLink *)area->spacedata.first)->link_flag |= SPACE_FLAG_TYPE_TEMPORARY;
      }
      else {
        area = ED_screen_full_newspace(C, ctx_area, int(space_type));
        ((SpaceLink *)area->spacedata.first)->link_flag |= SPACE_FLAG_TYPE_TEMPORARY;
      }
      break;
    }
  }

  return area;
}

void ED_screen_animation_timer(bContext *C, int redraws, int sync, int enable)
{
  bScreen *screen = CTX_wm_screen(C);
  wmWindowManager *wm = CTX_wm_manager(C);
  wmWindow *win = CTX_wm_window(C);
  Scene *scene = CTX_data_scene(C);
  bScreen *stopscreen = ED_screen_animation_playing(wm);

  if (stopscreen) {
    WM_event_timer_remove(wm, win, stopscreen->animtimer);
    stopscreen->animtimer = nullptr;
  }

  if (enable) {
    ScreenAnimData *sad = static_cast<ScreenAnimData *>(
        MEM_callocN(sizeof(ScreenAnimData), "ScreenAnimData"));

    screen->animtimer = WM_event_timer_add(wm, win, TIMER0, (1.0 / FPS));

    sad->region = CTX_wm_region(C);
    /* If start-frame is larger than current frame, we put current-frame on start-frame.
     * NOTE(ton): first frame then is not drawn! */
    if (PRVRANGEON) {
      if (scene->r.psfra > scene->r.cfra) {
        sad->sfra = scene->r.cfra;
        scene->r.cfra = scene->r.psfra;
      }
      else {
        sad->sfra = scene->r.cfra;
      }
    }
    else {
      if (scene->r.sfra > scene->r.cfra) {
        sad->sfra = scene->r.cfra;
        scene->r.cfra = scene->r.sfra;
      }
      else {
        sad->sfra = scene->r.cfra;
      }
    }
    sad->redraws = redraws;
    sad->flag |= (enable < 0) ? ANIMPLAY_FLAG_REVERSE : 0;
    sad->flag |= (sync == 0) ? ANIMPLAY_FLAG_NO_SYNC : (sync == 1) ? ANIMPLAY_FLAG_SYNC : 0;

    ScrArea *area = CTX_wm_area(C);

    char spacetype = -1;

    if (area) {
      spacetype = area->spacetype;
    }

    sad->from_anim_edit = ELEM(spacetype, SPACE_GRAPH, SPACE_ACTION, SPACE_NLA);

    screen->animtimer->customdata = sad;

    /* Seek audio to ensure playback in preview range with AV sync. */
    DEG_id_tag_update(&scene->id, ID_RECALC_FRAME_CHANGE);
  }

  /* Notifier caught by top header, for button. */
  WM_event_add_notifier(C, NC_SCREEN | ND_ANIMPLAY, nullptr);
}

/* helper for screen_animation_play() - only to be used for TimeLine */
static ARegion *time_top_left_3dwindow(bScreen *screen)
{
  ARegion *region_top_left = nullptr;
  int min = 10000;

  LISTBASE_FOREACH (ScrArea *, area, &screen->areabase) {
    if (area->spacetype == SPACE_VIEW3D) {
      LISTBASE_FOREACH (ARegion *, region, &area->regionbase) {
        if (region->regiontype == RGN_TYPE_WINDOW) {
          if (region->winrct.xmin - region->winrct.ymin < min) {
            region_top_left = region;
            min = region->winrct.xmin - region->winrct.ymin;
          }
        }
      }
    }
  }

  return region_top_left;
}

void ED_screen_animation_timer_update(bScreen *screen, int redraws)
{
  if (screen && screen->animtimer) {
    wmTimer *wt = screen->animtimer;
    ScreenAnimData *sad = static_cast<ScreenAnimData *>(wt->customdata);

    sad->redraws = redraws;
    sad->region = nullptr;
    if (redraws & TIME_REGION) {
      sad->region = time_top_left_3dwindow(screen);
    }
  }
}

void ED_update_for_newframe(Main *bmain, Depsgraph *depsgraph)
{
  Scene *scene = DEG_get_input_scene(depsgraph);

  DEG_time_tag_update(bmain);

#ifdef DURIAN_CAMERA_SWITCH
  void *camera = BKE_scene_camera_switch_find(scene);
  if (camera && scene->camera != camera) {
    scene->camera = static_cast<Object *>(camera);
    /* are there cameras in the views that are not in the scene? */
    LISTBASE_FOREACH (bScreen *, screen, &bmain->screens) {
      BKE_screen_view3d_scene_sync(screen, scene);
    }
    DEG_id_tag_update(&scene->id, ID_RECALC_COPY_ON_WRITE);
  }
#endif

  ED_clip_update_frame(bmain, scene->r.cfra);

  /* this function applies the changes too */
  BKE_scene_graph_update_for_newframe(depsgraph);
}

bool ED_screen_stereo3d_required(const bScreen *screen, const Scene *scene)
{
  const bool is_multiview = (scene->r.scemode & R_MULTIVIEW) != 0;

  LISTBASE_FOREACH (ScrArea *, area, &screen->areabase) {
    switch (area->spacetype) {
      case SPACE_VIEW3D: {
        View3D *v3d;

        if (!is_multiview) {
          continue;
        }

        v3d = static_cast<View3D *>(area->spacedata.first);
        if (v3d->camera && v3d->stereo3d_camera == STEREO_3D_ID) {
          LISTBASE_FOREACH (ARegion *, region, &area->regionbase) {
            if (region->regiondata && region->regiontype == RGN_TYPE_WINDOW) {
              RegionView3D *rv3d = static_cast<RegionView3D *>(region->regiondata);
              if (rv3d->persp == RV3D_CAMOB) {
                return true;
              }
            }
          }
        }
        break;
      }
      case SPACE_IMAGE: {
        SpaceImage *sima;

        /* images should always show in stereo, even if
         * the file doesn't have views enabled */
        sima = static_cast<SpaceImage *>(area->spacedata.first);
        if (sima->image && BKE_image_is_stereo(sima->image) &&
            (sima->iuser.flag & IMA_SHOW_STEREO)) {
          return true;
        }
        break;
      }
      case SPACE_NODE: {
        SpaceNode *snode;

        if (!is_multiview) {
          continue;
        }

        snode = static_cast<SpaceNode *>(area->spacedata.first);
        if ((snode->flag & SNODE_BACKDRAW) && ED_node_is_compositor(snode)) {
          return true;
        }
        break;
      }
      case SPACE_SEQ: {
        SpaceSeq *sseq;

        if (!is_multiview) {
          continue;
        }

        sseq = static_cast<SpaceSeq *>(area->spacedata.first);
        if (ELEM(sseq->view, SEQ_VIEW_PREVIEW, SEQ_VIEW_SEQUENCE_PREVIEW)) {
          return true;
        }

        if (sseq->draw_flag & SEQ_DRAW_BACKDROP) {
          return true;
        }

        break;
      }
    }
  }

  return false;
}

Scene *ED_screen_scene_find_with_window(const bScreen *screen,
                                        const wmWindowManager *wm,
                                        wmWindow **r_window)
{
  LISTBASE_FOREACH (wmWindow *, win, &wm->windows) {
    if (WM_window_get_active_screen(win) == screen) {
      if (r_window) {
        *r_window = win;
      }
      return WM_window_get_active_scene(win);
    }
  }

  /* Can by nullptr when accessing a screen that isn't active. */
  return nullptr;
}

ScrArea *ED_screen_area_find_with_spacedata(const bScreen *screen,
                                            const SpaceLink *sl,
                                            const bool only_visible)
{
  if (only_visible) {
    LISTBASE_FOREACH (ScrArea *, area, &screen->areabase) {
      if (area->spacedata.first == sl) {
        return area;
      }
    }
  }
  else {
    LISTBASE_FOREACH (ScrArea *, area, &screen->areabase) {
      if (BLI_findindex(&area->spacedata, sl) != -1) {
        return area;
      }
    }
  }
  return nullptr;
}

Scene *ED_screen_scene_find(const bScreen *screen, const wmWindowManager *wm)
{
  return ED_screen_scene_find_with_window(screen, wm, nullptr);
}

wmWindow *ED_screen_window_find(const bScreen *screen, const wmWindowManager *wm)
{
  LISTBASE_FOREACH (wmWindow *, win, &wm->windows) {
    if (WM_window_get_active_screen(win) == screen) {
      return win;
    }
  }
  return nullptr;
}

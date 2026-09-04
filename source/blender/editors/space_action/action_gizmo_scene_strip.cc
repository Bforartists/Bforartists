/* SPDX-FileCopyrightText: 2026 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/* BFA - this is a Bforartists exclusive feature (3D Sequencer). */

/** \file
 * \ingroup spaction
 *
 * Interactive scene-strip gizmos for the dope-sheet, driven by the 3D Sequencer
 * scene-time sync. Provides green/red retime handles, a move bar, a slip bar and
 * a master-timeline scrub area. The group renders its own visuals (in the draw
 * callback of the first gizmo) and provides the hit-areas plus the modal
 * operators that edit the strip.
 */

#include <algorithm>
#include <utility>

#include "BLI_listbase.hh"
#include "BLI_math_base.hh"
#include "BLI_math_base_c.hh"
#include "BLI_rect.hh"
#include "BLI_string.hh"
#include "BLI_utildefines.hh"
#include "BLI_vector.hh"

#include "BLT_translation.hh"

#include "DNA_action_types.h"
#include "DNA_scene_types.h"
#include "DNA_screen_types.h"
#include "DNA_sequence_types.h"
#include "DNA_windowmanager_types.h"
#include "DNA_workspace_types.h"

#include "BKE_context.hh"

#include "ED_anim_api.hh"
#include "ED_sequencer.hh"
#include "ED_screen.hh"

#include "GPU_immediate.hh"
#include "GPU_state.hh"

#include "MEM_guardedalloc.h"

#include "RNA_access.hh"
#include "RNA_define.hh"
#include "RNA_path.hh"
#include "RNA_prototypes.hh"

#include "SEQ_sequencer.hh"
#include "SEQ_time.hh"
#include "SEQ_transform.hh"

#include "UI_interface_c.hh"
#include "UI_resources.hh"
#include "UI_view2d.hh"

#include "WM_api.hh"
#include "WM_types.hh"

#include "action_intern.hh"

namespace blender {

/* -------------------------------------------------------------------- */
/** \name Sync helpers
 * \{ */

/* Minimum region height (in pixels) to display the strip bar and gizmos. */
#define ACTION_STRIP_GIZMO_MIN_REGION_HEIGHT 112

/* Which part of the scene strip a gizmo controls. */
enum eSceneStripGizmoPart {
  GZ_PART_LEFT = 0,
  GZ_PART_RIGHT = 1,
  GZ_PART_MOVE = 2,
  GZ_PART_SLIP = 3,
};

/* Strip bar geometry in region pixels (y up from the region bottom). */
struct SceneStripGizmoRects {
  rcti left;
  rcti right;
  rcti move;
  rcti slip;
  rcti scrub;
};

/* Resolve the 3D Sequencer sync settings (window_manager.timeline_sync_settings).
 * These are registered by the bfa_3Dsequencer addon; when the addon is disabled
 * the functions below simply report the built-in defaults. */
static bool timeline_sync_settings_ptr(const bContext *C, PointerRNA *r_settings)
{
  wmWindowManager *wm = CTX_wm_manager(C);
  if (!wm) {
    return false;
  }
  PointerRNA wm_ptr = RNA_pointer_create_discrete(&wm->id, RNA_WindowManager, wm);
  PropertyRNA *settings_prop = nullptr;
  return RNA_path_resolve_property(&wm_ptr, "timeline_sync_settings", r_settings, &settings_prop);
}

static Scene *timeline_sync_master_scene_get(const bContext *C)
{
  PointerRNA settings;
  if (!timeline_sync_settings_ptr(C, &settings)) {
    return nullptr;
  }
  PointerRNA master_ptr = RNA_pointer_get(&settings, "master_scene");
  return static_cast<Scene *>(master_ptr.data);
}

/* Returns the master scene strip used by the scene-time sync, and optionally the
 * master scene itself. Works with both the built-in sync (workspace sequencer
 * scene) and the legacy 3D Sequencer addon sync (addon master scene). */
static const Strip *scene_strip_master_get(const bContext *C, Scene **r_master_scene)
{
  WorkSpace *workspace = CTX_wm_workspace(C);
  if (!workspace || (workspace->flags & WORKSPACE_SYNC_SCENE_BFA) == 0) {
    return nullptr;
  }
  Scene *master_scene = workspace->sequencer_scene;
  if (!master_scene) {
    /* Legacy 3D Sequencer sync: master scene is stored on the addon settings. */
    master_scene = timeline_sync_master_scene_get(C);
    if (!master_scene) {
      return nullptr;
    }
  }
  const Strip *strip = ed::vse::get_scene_strip_for_time_sync(master_scene);
  if (!strip || !strip->scene) {
    return nullptr;
  }
  if (r_master_scene) {
    *r_master_scene = master_scene;
  }
  return strip;
}

/* Frame range of a scene strip in the dope-sheet time reference (same mapping as
 * `ANIM_draw_scene_strip_range`). */
static void scene_strip_frame_range(const Scene *master_scene,
                                    const Strip *strip,
                                    float *r_frame_in,
                                    float *r_frame_out)
{
  const float left_handle = strip->left_handle();
  const float right_handle = strip->right_handle(master_scene);
  float frame_in = seq::give_frame_index(master_scene, strip, left_handle) +
                   strip->scene->r.sfra + strip->anim_startofs;
  float frame_out = seq::give_frame_index(master_scene, strip, right_handle - 1) +
                    strip->scene->r.sfra + strip->anim_startofs;
  if (frame_in > frame_out) {
    std::swap(frame_in, frame_out);
  }
  *r_frame_in = frame_in;
  *r_frame_out = frame_out;
}

/* Compute the hit-areas of the master strip bar in region pixels. Returns false
 * when there is no usable strip (or the region is too small). */
static bool scene_strip_gizmo_rects_get(const bContext *C, SceneStripGizmoRects *rects)
{
  Scene *master_scene = nullptr;
  const Strip *strip = scene_strip_master_get(C, &master_scene);
  if (!strip) {
    return false;
  }
  ARegion *region = CTX_wm_region(C);
  if (!region || region->winy < ACTION_STRIP_GIZMO_MIN_REGION_HEIGHT) {
    return false;
  }
  const Scene *active_scene = CTX_data_scene(C);
  if (strip->scene != active_scene) {
    return false;
  }

  const float ui_scale = UI_SCALE_FAC;
  const bool has_markers = !BLI_listbase_is_empty(&active_scene->markers);
  const int baseline = int(has_markers ? UI_MARKER_MARGIN_Y : 14.0f * ui_scale);
  const int timeline_height = int(28.0f * ui_scale);
  const int strip_height = int(26.0f * ui_scale);
  const int y_strip = baseline + int(14.0f * ui_scale);

  float frame_in, frame_out;
  scene_strip_frame_range(master_scene, strip, &frame_in, &frame_out);

  View2D *v2d = &region->v2d;
  int x_in, x_out, y_dummy;
  ui::view2d_view_to_region(v2d, frame_in, 0.0f, &x_in, &y_dummy);
  ui::view2d_view_to_region(v2d, frame_out, 0.0f, &x_out, &y_dummy);

  const int handle_width = int(8.0f * ui_scale);
  /* bfa 3d sequencer: the move bar (strip location) is the bottom half and the
   * slip bar (strip content) the top half - split 50/50 so both zones stay easy
   * to grab (the move bar was too thin to hit comfortably before). */
  const int move_bar_height = int(strip_height * 0.5f);

  BLI_rcti_init(&rects->left,
                x_in - handle_width / 2,
                x_in + handle_width / 2,
                y_strip,
                y_strip + strip_height);
  BLI_rcti_init(&rects->right,
                x_out - handle_width / 2,
                x_out + handle_width / 2,
                y_strip,
                y_strip + strip_height);
  BLI_rcti_init(&rects->move, x_in, x_out, y_strip, y_strip + move_bar_height);
  BLI_rcti_init(&rects->slip, x_in, x_out, y_strip + move_bar_height, y_strip + strip_height);
  BLI_rcti_init(&rects->scrub, 0, region->winx, baseline, baseline + timeline_height);
  return true;
}

/* Overlap mode of the master timeline - the same setting the VSE header cycles
 * (expand, overwrite, shuffle). Falls back to the file default when no sequencer
 * tool settings exist yet. */
static eSeqOverlapMode scene_strip_overlap_mode_get(const Scene *master_scene)
{
  if (master_scene->toolsettings != nullptr &&
      master_scene->toolsettings->sequencer_tool_settings != nullptr)
  {
    return eSeqOverlapMode(
        master_scene->toolsettings->sequencer_tool_settings->overlap_mode);
  }
  return SEQ_OVERLAP_EXPAND;
}

/* True while the moved strip overlaps another strip on the same channel (the "bump"
 * the gizmo warns about). Same condition the VSE flags while a strip is grabbed. */
static bool strip_move_bump_active(const Scene *master_scene, const Strip *strip)
{
  const Editing *ed = seq::editing_get(master_scene);
  if (ed == nullptr) {
    return false;
  }
  for (const Strip &other : ed->seqbase) {
    if (&other == strip || other.channel != strip->channel) {
      continue;
    }
    if (other.left_handle() < strip->right_handle(master_scene) &&
        strip->left_handle() < other.right_handle(master_scene))
    {
      return true;
    }
  }
  return false;
}

/* Color that flags a move bump by the master timeline's overlap mode: green expand
 * (the bumped strip is pushed along the same lane), sky blue shuffle (the strip
 * slides to the nearest free spot), red overwrite (the bumped strip is trimmed). */
static void strip_move_bump_color(const Scene *master_scene, float r_color[4])
{
  switch (scene_strip_overlap_mode_get(master_scene)) {
    case SEQ_OVERLAP_EXPAND:
      r_color[0] = 0.3f;
      r_color[1] = 0.9f;
      r_color[2] = 0.45f;
      r_color[3] = 0.9f;
      break;
    case SEQ_OVERLAP_OVERWRITE:
      r_color[0] = 0.95f;
      r_color[1] = 0.3f;
      r_color[2] = 0.4f;
      r_color[3] = 0.9f;
      break;
    case SEQ_OVERLAP_SHUFFLE:
      r_color[0] = 0.35f;
      r_color[1] = 0.78f;
      r_color[2] = 1.0f;
      r_color[3] = 0.9f;
      break;
  }
}

/* Resolve overlaps left by a move drag, like the VSE does when a strip grab is
 * released: the master timeline's overlap mode decides - expand pushes the bumped
 * strips along, shuffle slides this strip to the nearest free spot, overwrite trims
 * the bumped strips. The dope-sheet move never leaves its track: if the sequencer's
 * last-resort fallback channel-shuffled the strip away, slide it back into the
 * nearest free time spot on the original channel instead. */
static void resolve_move_overlap(Scene *master_scene, Strip *strip)
{
  Editing *ed = seq::editing_get(master_scene);
  if (ed == nullptr) {
    return;
  }
  const int orig_channel = strip->channel;
  Vector<Strip *> source;
  source.append(strip);
  seq::transform_handle_overlap(master_scene, &ed->seqbase, source, false);
  if (strip->channel != orig_channel) {
    strip->channel_set(orig_channel);
    seq::transform_seqbase_shuffle_time(
        source, &ed->seqbase, master_scene, &master_scene->markers, false);
  }
}

/** \} */

/* Shared per-region state of the gizmo group (gizmo hit-areas and scrub area).
 * The visuals of the whole group are rendered by the draw callback of
 * gizmos[0], see #action_gizmo_scene_strip_draw. */
struct SceneStripWidgetGroup {
  wmGizmo *gizmos[4]; /* left, right, move, slip */
  wmGizmo *scrub;
};

/* -------------------------------------------------------------------- */
/** \name Scene strip gizmo types
 * \{ */

static void action_gizmo_scene_strip_draw(const bContext *C, wmGizmo *gz)
{
  /* Only the first gizmo of the group renders the bar, the other gizmos only
   * provide their own hit-areas (test_select) and cursor feedback. */
  wmGizmoGroup *parent_gzgroup = gz->parent_gzgroup;
  SceneStripWidgetGroup *group = (parent_gzgroup != nullptr) ?
                                     static_cast<SceneStripWidgetGroup *>(parent_gzgroup->customdata) :
                                     nullptr;
  if (group == nullptr || gz != group->gizmos[0]) {
    return;
  }

  /* Mirrors WIDGETGROUP_scene_strip_poll, in case the overlay flags or the sync
   * state changed without the gizmo-map being refreshed. */
  SpaceAction *space_action = CTX_wm_space_action(C);
  if (space_action == nullptr || (space_action->overlays.flag & ADS_OVERLAY_SHOW_OVERLAYS) == 0 ||
      (space_action->overlays.flag & ADS_SHOW_SCENE_STRIP_GIZMOS) == 0)
  {
    return;
  }
  Scene *master_scene = nullptr;
  const Strip *strip = scene_strip_master_get(C, &master_scene);
  if (strip == nullptr || strip->scene == nullptr) {
    return;
  }
  const Scene *active_scene = CTX_data_scene(C);
  if (strip->scene != active_scene) {
    return;
  }
  ARegion *region = CTX_wm_region(C);
  if (region == nullptr || region->winy < ACTION_STRIP_GIZMO_MIN_REGION_HEIGHT) {
    return;
  }
  View2D *v2d = &region->v2d;

  /* The highlight state is fresh here: the gizmo-map runs the draw_prepare of all
   * groups before any gizmo draw call. This replaces the previous cross-file
   * caching through SpaceAction_Runtime (which lagged one redraw behind). */
  int highlight = -1;
  int modal_part = -1;
  for (int i = 0; i < 4; i++) {
    if (group->gizmos[i]->state & WM_GIZMO_STATE_HIGHLIGHT) {
      highlight = i;
    }
    /* A gizmo keeps WM_GIZMO_STATE_MODAL while its operator runs (grab). */
    if (group->gizmos[i]->state & WM_GIZMO_STATE_MODAL) {
      modal_part = i;
    }
  }

  const float ui_scale = UI_SCALE_FAC;
  const bool has_markers = !BLI_listbase_is_empty(&active_scene->markers);
  const float baseline = has_markers ? float(UI_MARKER_MARGIN_Y) : 14.0f * ui_scale;
  const float strip_height = 26.0f * ui_scale;

  GPU_blend(GPU_BLEND_ALPHA);

  GPUVertFormat *format = immVertexFormat();
  uint pos = GPU_vertformat_attr_add(format, "pos", gpu::VertAttrType::SFLOAT_32_32);

  immBindBuiltinProgram(GPU_SHADER_3D_UNIFORM_COLOR);

  /* The gizmos draw in region pixel space, so view (frame) coordinates need to
   * be mapped to region pixels for the x-axis (y is already in region pixels,
   * same space as the marker margin and the hit-areas). */
  const auto region_x_from_view = [v2d](float frame) {
    int x = 0, y = 0;
    ui::view2d_view_to_region(v2d, frame, 0.0f, &x, &y);
    return float(x);
  };

  /* BFA (#6780): no playhead line is drawn on or above the strip bar - the earlier
   * in-bar master-frame cursor read as a stray blue line artifact, so playhead
   * position is only communicated by the master timeline itself. */

  /* Other scene strips referencing the same scene. */
  const Editing *ed = seq::editing_get(master_scene);
  if (ed != nullptr) {
    for (const Strip &other : ed->seqbase) {
      if (&other == strip || other.type != STRIP_TYPE_SCENE || other.scene != active_scene) {
        continue;
      }
      const float left_handle = other.left_handle();
      const float right_handle = other.right_handle(master_scene);
      float frame_in = seq::give_frame_index(master_scene, &other, left_handle) +
                       other.scene->r.sfra + other.anim_startofs;
      float frame_out = seq::give_frame_index(master_scene, &other, right_handle - 1) +
                        other.scene->r.sfra + other.anim_startofs;
      if (frame_in > frame_out) {
        std::swap(frame_in, frame_out);
      }
      const float x_in = region_x_from_view(frame_in);
      const float x_out = region_x_from_view(frame_out);
      const float y = baseline + 4.0f * ui_scale;
      immUniformColor4f(0.1f, 0.1f, 0.1f, 0.5f);
      immRectf(pos, x_in, y, x_out, y + strip_height);
      immUniformColor4f(0.3f, 0.3f, 0.3f, 0.7f);
      immRectf(pos, x_in, y, x_in + 2.0f * ui_scale, y + strip_height);
      immRectf(pos, x_out - 2.0f * ui_scale, y, x_out, y + strip_height);
    }
  }

  /* Master strip: base, move/slip zones and handles. The rects are shared with
   * the hit-areas, so what is drawn always matches what can be grabbed. */
  SceneStripGizmoRects rects;
  if (scene_strip_gizmo_rects_get(C, &rects)) {
    const float x_in = float(rects.move.xmin);
    const float x_out = float(rects.move.xmax);
    const float y_strip = float(rects.left.ymin);
    const float y_top = y_strip + strip_height;
    const float y_move_max = float(rects.move.ymax); /* boundary: bottom move | top slip */

    /* BFA (#6780): minimap-style bar. The rounded chip is drawn from the same
     * hit-area rects used for grabbing; hovering lights an outline around the whole
     * gizmo (handles included) plus a wash of the hovered zone. Colors are
     * theme-driven with a translucent body. */
    const float border_w = 1.5f * ui_scale;
    const float chip_rad = 3.0f * ui_scale;
    const float lx0 = float(rects.left.xmin);
    const float lx1 = float(rects.left.xmax);
    const float rx0 = float(rects.right.xmin);
    const float rx1 = float(rects.right.xmax);
    const bool left_hovered = (highlight == GZ_PART_LEFT);
    const bool right_hovered = (highlight == GZ_PART_RIGHT);
    const bool slip_hovered = (highlight == GZ_PART_SLIP);
    const bool move_hovered = (highlight == GZ_PART_MOVE);
    const bool left_grabbed = (modal_part == GZ_PART_LEFT);
    const bool right_grabbed = (modal_part == GZ_PART_RIGHT);

    float backdrop_color[4];
    float backdrop_color_outline[4];
    ui::theme::get_color_shade_alpha_4fv(TH_BACK, -45, 0, backdrop_color);
    ui::theme::get_color_shade_alpha_4fv(TH_BACK, 30, 0, backdrop_color_outline);
    /* Semi-transparent body; the border stays subtle at rest, the hover ring below
     * carries the highlight instead. */
    backdrop_color[3] = 0.75f;
    backdrop_color_outline[3] = 0.55f;
    rctf bar_rect;
    BLI_rctf_init(&bar_rect, x_in, x_out, y_strip, y_top);
    ui::draw_roundbox_corner_set(ui::CNR_ALL);
    ui::draw_roundbox_4fv_ex(
        &bar_rect, backdrop_color, nullptr, 1.0f, backdrop_color_outline, border_w, chip_rad);
    GPU_blend(GPU_BLEND_NONE);

    /* BFA - `draw_roundbox_4fv_ex` renders through a batch which unbinds the GPU
     * program but leaves the immediate-mode shader state bound, so end it before
     * rebinding here (a second bind asserts `imm->shader == nullptr`). */
    immUnbindProgram();
    immBindBuiltinProgram(GPU_SHADER_3D_UNIFORM_COLOR);
    GPU_blend(GPU_BLEND_ALPHA);

    /* The grip handles cap the strip ends, so the zones only run between their
     * inner edges - exactly the area a zone drag can grab. */
    const float zone_x0 = lx1;
    const float zone_x1 = rx0;
    if (zone_x1 > zone_x0) {
      /* Zone shading: slip (top, content) lighter, move (bottom, location) darker,
       * with a thin seam in between so both areas read even without hovering. */
      float zone_slip[4];
      float zone_move[4];
      ui::theme::get_color_shade_alpha_4fv(TH_BACK, 12, 0, zone_slip);
      ui::theme::get_color_shade_alpha_4fv(TH_BACK, -60, 0, zone_move);
      zone_slip[3] = 0.85f;
      zone_move[3] = 0.85f;
      immUniformColor4f(zone_slip[0], zone_slip[1], zone_slip[2], zone_slip[3]);
      /* Inset from the chip top/bottom so the rounded border band stays visible. */
      immRectf(pos, zone_x0, y_move_max, zone_x1, y_top - border_w);
      immUniformColor4f(zone_move[0], zone_move[1], zone_move[2], zone_move[3]);
      immRectf(pos, zone_x0, y_strip + border_w, zone_x1, y_move_max);
      immUniformColor4f(0.55f, 0.58f, 0.66f, 0.6f);
      immRectf(pos, zone_x0, y_move_max - 0.5f, zone_x1, y_move_max + 0.5f);

      /* Hover: translucent accent wash over the whole active zone. */
      if (slip_hovered) {
        immUniformColor4f(0.42f, 0.62f, 0.95f, 0.4f);
        immRectf(pos, zone_x0, y_move_max, zone_x1, y_top - border_w);
      }
      else if (move_hovered) {
        immUniformColor4f(0.42f, 0.62f, 0.95f, 0.4f);
        immRectf(pos, zone_x0, y_strip + border_w, zone_x1, y_move_max);
      }
    }

    /* Grip handles: green/red caps with a soft halo. The halo is white on hover
     * and switches to the accent color while the handle is grabbed (modal). */
    if (left_hovered || left_grabbed) {
      if (left_grabbed) {
        immUniformColor4f(0.3f, 0.95f, 0.45f, 0.5f);
      }
      else {
        immUniformColor4f(1.0f, 1.0f, 1.0f, 0.45f);
      }
      immRectf(pos, lx0 - 2.0f * ui_scale, y_strip - 1.0f, lx1 + 2.0f * ui_scale, y_top + 1.0f);
    }
    if (right_hovered || right_grabbed) {
      if (right_grabbed) {
        immUniformColor4f(0.95f, 0.35f, 0.42f, 0.5f);
      }
      else {
        immUniformColor4f(1.0f, 1.0f, 1.0f, 0.45f);
      }
      immRectf(pos, rx0 - 2.0f * ui_scale, y_strip - 1.0f, rx1 + 2.0f * ui_scale, y_top + 1.0f);
    }
    immUniformColor4f(0.3f, 0.92f, 0.45f, (left_hovered || left_grabbed) ? 0.95f : 0.8f);
    immRectf(pos, lx0, y_strip, lx1, y_top);
    immUniformColor4f(0.95f, 0.33f, 0.4f, (right_hovered || right_grabbed) ? 0.95f : 0.8f);
    immRectf(pos, rx0, y_strip, rx1, y_top);
    /* White wash over the hovered cap (hover = white, grab = accent). */
    if (left_hovered && !left_grabbed) {
      immUniformColor4f(1.0f, 1.0f, 1.0f, 0.8f);
      immRectf(pos, lx0, y_strip, lx1, y_top);
    }
    if (right_hovered && !right_grabbed) {
      immUniformColor4f(1.0f, 1.0f, 1.0f, 0.8f);
      immRectf(pos, rx0, y_strip, rx1, y_top);
    }
    /* Detach the grip caps from the zones with a subtle 1px dark seam. */
    immUniformColor4f(0.0f, 0.0f, 0.0f, 0.4f);
    immRectf(pos, lx1 - 1.0f, y_strip, lx1, y_top);
    immRectf(pos, rx0, y_strip, rx0 + 1.0f, y_top);

    /* Hover / grab ring around the whole gizmo (caps included): near-white on
     * hover, accent color while a handle is grabbed. */
    if (highlight != -1 || modal_part != -1) {
      float ring_color[4] = {0.82f, 0.82f, 0.85f, 0.9f};
      if (modal_part == GZ_PART_LEFT) {
        ring_color[0] = 0.3f;
        ring_color[1] = 0.95f;
        ring_color[2] = 0.45f;
        ring_color[3] = 0.95f;
      }
      else if (modal_part == GZ_PART_RIGHT) {
        ring_color[0] = 0.95f;
        ring_color[1] = 0.33f;
        ring_color[2] = 0.4f;
        ring_color[3] = 0.95f;
      }
      /* bfa 3d sequencer: dragging the move or slip zone rings the bar in a
       * blue accent so a zone drag reads differently from a handle grab. */
      else if (ELEM(modal_part, GZ_PART_MOVE, GZ_PART_SLIP)) {
        ring_color[0] = 0.45f;
        ring_color[1] = 0.65f;
        ring_color[2] = 0.95f;
        ring_color[3] = 0.95f;
      }
      rctf ring_rect;
      BLI_rctf_init(&ring_rect, lx0, rx1, y_strip, y_top);
      ui::draw_roundbox_corner_set(ui::CNR_ALL);
      ui::draw_roundbox_4fv_ex(
          &ring_rect, nullptr, nullptr, 1.0f, ring_color, 1.5f * ui_scale, chip_rad);
    }

    /* BFA - overlap-mode bump feedback: while a move drag leaves the strip
     * overlapping a strip on the same channel, ring the bar in the color of the
     * master timeline's overlap mode so the user sees what releasing will do to
     * the bumped strip (green expand, sky blue shuffle, red overwrite). */
    if (strip_move_bump_active(master_scene, strip)) {
      float bump_color[4];
      strip_move_bump_color(master_scene, bump_color);
      ui::draw_roundbox_corner_set(ui::CNR_ALL);
      ui::draw_roundbox_4fv_ex(
          &bar_rect, nullptr, nullptr, 1.0f, bump_color, 2.0f * ui_scale, 3.0f * ui_scale);
    }
  }

  immUnbindProgram();

  GPU_blend(GPU_BLEND_NONE);
}

static int action_gizmo_scene_strip_test_select(bContext *C, wmGizmo *gz, const int mval[2])
{
  SceneStripGizmoRects rects;
  if (!scene_strip_gizmo_rects_get(C, &rects)) {
    return -1;
  }
  const int mode = RNA_int_get(gz->ptr, "mode");
  const rcti *rect = [&]() -> const rcti * {
    switch (mode) {
      case GZ_PART_LEFT:
        return &rects.left;
      case GZ_PART_RIGHT:
        return &rects.right;
      case GZ_PART_MOVE:
        return &rects.move;
      default:
        return &rects.slip;
    }
  }();
  return BLI_rcti_isect_pt_v(rect, mval) ? 0 : -1;
}

static int action_gizmo_scene_strip_cursor_get(wmGizmo * /*gz*/)
{
  return WM_CURSOR_X_MOVE;
}

void ACTION_GT_scene_strip_gizmo(wmGizmoType *gzt)
{
  gzt->idname = "ACTION_GT_scene_strip_gizmo";

  /* api callbacks */
  gzt->draw = action_gizmo_scene_strip_draw;
  gzt->test_select = action_gizmo_scene_strip_test_select;
  gzt->cursor_get = action_gizmo_scene_strip_cursor_get;

  gzt->struct_size = sizeof(wmGizmo);

  RNA_def_int(gzt->srna,
              "mode",
              GZ_PART_LEFT,
              GZ_PART_LEFT,
              GZ_PART_SLIP,
              "Mode",
              "Which part of the scene strip this gizmo controls",
              GZ_PART_LEFT,
              GZ_PART_SLIP);
}

static int action_gizmo_scene_strip_scrub_test_select(bContext *C, wmGizmo * /*gz*/, const int mval[2])
{
  SceneStripGizmoRects rects;
  if (!scene_strip_gizmo_rects_get(C, &rects)) {
    return -1;
  }
  return BLI_rcti_isect_pt_v(&rects.scrub, mval) ? 0 : -1;
}

static int action_gizmo_scene_strip_scrub_cursor_get(wmGizmo * /*gz*/)
{
  return WM_CURSOR_HAND;
}

void ACTION_GT_scene_strip_scrub(wmGizmoType *gzt)
{
  gzt->idname = "ACTION_GT_scene_strip_scrub";

  /* api callbacks */
  gzt->draw = action_gizmo_scene_strip_draw;
  gzt->test_select = action_gizmo_scene_strip_scrub_test_select;
  gzt->cursor_get = action_gizmo_scene_strip_scrub_cursor_get;

  gzt->struct_size = sizeof(wmGizmo);
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Scene strip gizmo group
 * \{ */

static bool WIDGETGROUP_scene_strip_poll(const bContext *C, wmGizmoGroupType * /*gzgt*/)
{
  SpaceAction *saction = CTX_wm_space_action(C);
  if (!saction || (saction->overlays.flag & ADS_OVERLAY_SHOW_OVERLAYS) == 0 ||
      (saction->overlays.flag & ADS_SHOW_SCENE_STRIP_GIZMOS) == 0)
  {
    return false;
  }
  const Strip *strip = scene_strip_master_get(C, nullptr);
  if (!strip) {
    return false;
  }
  /* Only show the gizmos when the dope-sheet displays the strip's scene. */
  const Scene *active_scene = CTX_data_scene(C);
  return strip->scene == active_scene;
}

static void WIDGETGROUP_scene_strip_setup(const bContext * /*C*/, wmGizmoGroup *gzgroup)
{
  SceneStripWidgetGroup *group = MEM_new_zeroed<SceneStripWidgetGroup>(__func__);
  wmOperatorType *ot = WM_operatortype_find("ACTION_OT_scene_strip_timing", false);
  wmOperatorType *ot_scrub = WM_operatortype_find("ACTION_OT_scene_strip_scrub", false);

  const int modes[4] = {GZ_PART_LEFT, GZ_PART_RIGHT, GZ_PART_MOVE, GZ_PART_SLIP};
  for (int i = 0; i < 4; i++) {
    wmGizmo *gz = WM_gizmo_new("ACTION_GT_scene_strip_gizmo", gzgroup, nullptr);
    RNA_int_set(gz->ptr, "mode", modes[i]);
    gz->flag |= (WM_GIZMO_MOVE_CURSOR | WM_GIZMO_DRAW_MODAL);
    gz->color[3] = 0.0f;
    gz->color_hi[3] = 0.0f;
    gz->scale_basis = 1.0f;

    if (ot != nullptr) {
      PointerRNA *op_ptr = WM_gizmo_operator_set(gz, 0, ot, nullptr);
      RNA_enum_set(op_ptr, "mode", modes[i]);
    }
    group->gizmos[i] = gz;
  }

  wmGizmo *scrub = WM_gizmo_new("ACTION_GT_scene_strip_scrub", gzgroup, nullptr);
  scrub->flag |= (WM_GIZMO_MOVE_CURSOR | WM_GIZMO_DRAW_MODAL);
  scrub->color[3] = 0.0f;
  scrub->color_hi[3] = 0.0f;
  scrub->scale_basis = 1.0f;

  if (ot_scrub != nullptr) {
    WM_gizmo_operator_set(scrub, 0, ot_scrub, nullptr);
  }
  group->scrub = scrub;

  gzgroup->customdata = group;
  gzgroup->customdata_free = [](void *customdata) {
    MEM_delete(static_cast<SceneStripWidgetGroup *>(customdata));
  };
}

static void WIDGETGROUP_scene_strip_draw_prepare(const bContext *C, wmGizmoGroup *gzgroup)
{
  SceneStripWidgetGroup *group = static_cast<SceneStripWidgetGroup *>(gzgroup->customdata);
  if (group == nullptr) {
    return;
  }

  /* BFA (#6780): mirror the poll gates here too - set WM_GIZMO_HIDDEN while the
   * overlays or the "Scene Strip Gizmo" toggle are off, so the gizmos are neither
   * drawn nor hover/click-able even if the gizmo-map refresh lags the toggle. */
  const SpaceAction *saction = CTX_wm_space_action(C);
  const bool enabled = (saction != nullptr) &&
                       (saction->overlays.flag & ADS_OVERLAY_SHOW_OVERLAYS) != 0 &&
                       (saction->overlays.flag & ADS_SHOW_SCENE_STRIP_GIZMOS) != 0;

  SceneStripGizmoRects rects;
  const bool has_rects = enabled && scene_strip_gizmo_rects_get(C, &rects);

  for (int i = 0; i < 4; i++) {
    WM_gizmo_set_flag(group->gizmos[i], WM_GIZMO_HIDDEN, !has_rects);
  }
  WM_gizmo_set_flag(group->scrub, WM_GIZMO_HIDDEN, !has_rects);
}

void ACTION_GGT_scene_strip_gizmos(wmGizmoGroupType *gzgt)
{
  gzgt->name = "Scene Strip Gizmos";
  gzgt->idname = "ACTION_GGT_scene_strip_gizmos";

  /* BFA - UI pass: on-top overlay gizmo, mirrors unflagged/Python gizmo-group behavior. */
  gzgt->flag |= WM_GIZMOGROUPTYPE_PERSISTENT | WM_GIZMOGROUPTYPE_2D_UI;

  gzgt->poll = WIDGETGROUP_scene_strip_poll;
  gzgt->setup = WIDGETGROUP_scene_strip_setup;
  gzgt->draw_prepare = WIDGETGROUP_scene_strip_draw_prepare;
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Strip editing helpers
 *
 * Port of the legacy 3D Sequencer addon logic (`scene/core.py`) using the
 * native sequencer transform helpers, with undo support.
 * \{ */

/* Strips on the same channel whose final start is after `strip`'s final start,
 * sorted by start frame (same as the addon's `impacted_strips`). */
static Vector<Strip *> strips_after_same_channel(Scene *master_scene, const Strip *strip)
{
  Vector<Strip *> result;
  const Editing *ed = seq::editing_get(master_scene);
  if (!ed) {
    return result;
  }
  for (Strip &s : ed->seqbase) {
    if (&s == strip || s.channel != strip->channel ||
        s.left_handle() <= strip->left_handle())
    {
      continue;
    }
    result.append(&s);
  }
  std::ranges::sort(result, [](const Strip *a, const Strip *b) {
    return a->left_handle() < b->left_handle();
  });
  return result;
}

/* Re-evaluate the scene strip content length from its scene's frame range,
 * preserving the current handles. Same as `bpy.ops.sequencer.reload()`. */
static void scene_strip_reload_range(Scene *master_scene, Strip *strip)
{
  const int prev_left = strip->left_handle();
  const int prev_right = strip->right_handle(master_scene);
  const int new_len = max_ii(strip->scene->r.efra - strip->scene->r.sfra + 1 -
                                 strip->anim_startofs - strip->anim_endofs,
                             0);
  strip->content_length_set(new_len);
  strip->handles_set(master_scene, prev_left, prev_right);
}

/* Ensure the strip's internal range is contained in its scene's frame range
 * (only ever extends the scene's end frame). */
static void adapt_scene_range(Scene *master_scene, Strip *strip)
{
  const int new_frame_end = strip->right_handle(master_scene) - 1 - strip->start +
                            strip->scene->r.sfra;
  if (new_frame_end <= strip->scene->r.efra) {
    return;
  }
  strip->scene->r.efra = new_frame_end;
  scene_strip_reload_range(master_scene, strip);
}

/* Map a master-timeline frame to the strip's scene frame reference. */
static int remap_frame_value(const Strip *strip, int frame)
{
  return frame - strip->start + strip->scene->r.sfra;
}

static void adjust_shot_duration_right(Scene *master_scene,
                                    Strip *strip,
                                    const int frame_offset,
                                    const bool allow_scene_range)
{
  const int duration = strip->right_handle(master_scene) - strip->left_handle();
  const int new_duration = max_ii(duration + frame_offset, 1);
  const int new_frame_offset = new_duration - duration;
  if (new_frame_offset == 0) {
    return;
  }
  Vector<Strip *> impacted = strips_after_same_channel(master_scene, strip);
  if (new_frame_offset > 0) {
    /* Extend: move impacted strips to the right first (reversed order). */
    for (int i = impacted.size() - 1; i >= 0; i--) {
      seq::transform_translate_strip(master_scene, impacted[i], new_frame_offset);
    }
    strip->endofs -= new_frame_offset;
  }
  else {
    /* Shrink: adjust the strip first, then move impacted strips to the left. */
    strip->endofs -= new_frame_offset;
    for (Strip *s : impacted) {
      seq::transform_translate_strip(master_scene, s, new_frame_offset);
    }
  }
  /* BFA (#6780): only extend the scene frame range when the dope-sheet "Set Scene
   * Range" toggle is on; otherwise the gizmo only changes the strip itself. */
  if (allow_scene_range) {
    adapt_scene_range(master_scene, strip);
  }
}

/* The exclusive end frame of the last strip on the same channel before `strip`
 * (0 when no strip precedes it). Used to clamp the master start edge so an
 * extended strip never overlaps its left neighbour. */
static int previous_strip_end_frame(Scene *master_scene, const Strip *strip)
{
  int prev_end = 0;
  const Editing *ed = seq::editing_get(master_scene);
  if (ed != nullptr) {
    for (const Strip &s : ed->seqbase) {
      if (&s == strip || s.channel != strip->channel ||
          s.left_handle() >= strip->left_handle())
      {
        continue;
      }
      prev_end = max_ii(prev_end, s.right_handle(master_scene));
    }
  }
  return prev_end;
}

/* bfa 3d sequencer: retime from the left handle. Dragging to the left moves the
 * master-timeline start edge (and the dope-sheet bar edge) back in lockstep while
 * the end edge stays put, so the strip feels "in sync" with the dope-sheet. First
 * the trimmed content is consumed; once that runs out, the scene's start frame is
 * extended (only when the "Set Scene Range" toggle allows it), never past
 * the preceding strip on the same channel. */
static void adjust_shot_duration_left(Scene *master_scene,
                                      Strip *strip,
                                      const int frame_offset,
                                      const bool allow_scene_range)
{
  const int duration = strip->right_handle(master_scene) - strip->left_handle();
  const int new_duration = max_ii(duration + frame_offset, 1);
  const int new_frame_offset = new_duration - duration;
  if (new_frame_offset == 0) {
    return;
  }
  if (new_frame_offset > 0) {
    /* Extend: first consume trimmed content (master start edge moves left), then
     * optionally extend the scene's start frame. Following strips never move. */
    const int trim = min_ii(new_frame_offset, int(strip->startofs));
    strip->startofs -= trim;
    const int remaining = new_frame_offset - trim;
    if (remaining > 0 && allow_scene_range) {
      /* Only extend into free room before the previous strip on this channel. */
      const int room = max_ii(
          strip->left_handle() - previous_strip_end_frame(master_scene, strip), 0);
      const int scene_extend = min_ii(remaining, room);
      if (scene_extend > 0) {
        strip->start -= scene_extend;
        strip->scene->r.sfra -= scene_extend;
        /* Re-evaluate the content length for the extended scene, keeping the
         * (already moved) handles so the end edge stays fixed. */
        const int left = strip->left_handle();
        const int right = strip->right_handle(master_scene);
        const int new_len = max_ii(strip->scene->r.efra - strip->scene->r.sfra + 1 -
                                       strip->anim_startofs - strip->anim_endofs,
                                   0);
        strip->content_length_set(new_len);
        strip->handles_set(master_scene, left, right);
      }
    }
  }
  else {
    /* Shrink: the master start edge moves right; the end edge (and any following
     * strips) stay put. */
    strip->startofs -= new_frame_offset;
  }
  /* BFA (#6780): only extend the scene frame range when the dope-sheet "Set Scene
   * Range" toggle is on; otherwise the gizmo only changes the strip itself. */
  if (allow_scene_range) {
    adapt_scene_range(master_scene, strip);
  }
}

static void move_shot(Scene *master_scene,
                       Strip *strip,
                       const int frame_offset,
                       const bool allow_scene_range)
{
  if (frame_offset == 0) {
    return;
  }
  seq::transform_translate_strip(master_scene, strip, frame_offset);
  /* BFA (#6780): only extend the scene frame range when the dope-sheet "Set Scene
   * Range" toggle is on; otherwise the gizmo only changes the strip itself. */
  if (allow_scene_range) {
    adapt_scene_range(master_scene, strip);
  }
}

static void slip_shot_content(Scene *master_scene,
                              Strip *strip,
                              const int frame_offset,
                              const bool allow_scene_range)
{
  const int remapped_start = remap_frame_value(strip, strip->left_handle());
  const int new_start = max_ii(remapped_start + frame_offset, strip->scene->r.sfra);
  const int new_frame_offset = new_start - remapped_start;
  if (new_frame_offset == 0) {
    return;
  }
  strip->startofs += new_frame_offset;
  strip->start -= new_frame_offset;
  /* BFA (#6780): the end offset must move the opposite way too, otherwise the
   * strip end edge (and its duration) changes and the slip "extends" the shot
   * instead of offsetting both edges of the internal range (same math as
   * seq::time_slip_strip and the addon slip_shot_content). */
  strip->endofs -= new_frame_offset;
  /* BFA (#6780): only extend the scene frame range when the dope-sheet "Set Scene
   * Range" toggle is on; otherwise the gizmo only changes the strip itself. */
  if (allow_scene_range) {
    adapt_scene_range(master_scene, strip);
  }
}

/* Update the strip's scene preview range to match the strip (dope-sheet overlay toggle). */
static void update_preview_range(Scene *master_scene, Strip *strip)
{
  if (!strip->scene) {
    return;
  }
  if ((strip->scene->r.flag & SCER_PRV_RANGE) == 0) {
    strip->scene->r.flag |= SCER_PRV_RANGE;
  }
  const int start = remap_frame_value(strip, strip->left_handle());
  const int end = remap_frame_value(strip, strip->right_handle(master_scene) - 1);
  strip->scene->r.psfra = start;
  strip->scene->r.pefra = end;
}

/* bfa 3d sequencer: the "Set Scene Range" dope-sheet toggle makes the strip scene's
 * frame range follow the strip in both directions (only ever extending, so scene
 * data is never discarded). Extending the left edge is what makes the dope-sheet
 * frame start follow the gizmo; extending the right edge makes the end follow. */
static void update_scene_frame_range(Scene *master_scene, Strip *strip)
{
  if (!strip->scene) {
    return;
  }
  const int start = remap_frame_value(strip, strip->left_handle());
  const int end = remap_frame_value(strip, strip->right_handle(master_scene) - 1);
  if (start < strip->scene->r.sfra) {
    strip->scene->r.sfra = start;
  }
  if (end > strip->scene->r.efra) {
    strip->scene->r.efra = end;
  }
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name ACTION_OT_scene_strip_timing operator
 *
 * Modal operator invoked by the scene strip gizmos. Retimes (LEFT/RIGHT),
 * moves (MOVE) or slips (SLIP) the master scene strip.
 * \{ */

struct SceneStripTimingOp {
  Strip *strip;
  Scene *master_scene;
  int mode;
  int start_view_x;
  int offset;
  /* Original state for the offset delta tracking. */
  int orig_duration;
  float orig_start;
  float orig_startofs;
  /* Original frame ranges to restore/keep on cancel. */
  int orig_master_efra;
  int orig_scene_efra;
};

static const EnumPropertyItem rna_enum_scene_strip_timing_mode_items[] = {
    {GZ_PART_LEFT, "LEFT", 0, "Left Handle", "Shift the shot's start frame in the master timeline"},
    {GZ_PART_RIGHT, "RIGHT", 0, "Right Handle", "Shift the shot's end frame in the master timeline"},
    {GZ_PART_MOVE, "MOVE", 0, "Move", "Move the strip in the master timeline"},
    {GZ_PART_SLIP, "SLIP", 0, "Slip", "Slip the shot content in the scene"},
    {0, nullptr, 0, nullptr, nullptr},
};

/* bfa 3d sequencer: per-zone tooltips (each gizmo of the group shares the same
 * operator but carries a different "mode" property). */
static std::string scene_strip_timing_get_description(bContext * /*C*/,
                                                      wmOperatorType * /*ot*/,
                                                      PointerRNA *ptr)
{
  switch (RNA_enum_get(ptr, "mode")) {
    case GZ_PART_LEFT:
      return TIP_("Retime the shot start: shift the start frame in the master timeline, "
                  "keeping the end frame fixed");
    case GZ_PART_RIGHT:
      return TIP_("Retime the shot end: shift the end frame in the master timeline, "
                  "keeping the start frame fixed");
    case GZ_PART_MOVE:
      return TIP_("Move the strip in the master timeline. When it bumps into another "
                  "strip the sequencer overlap mode applies on release: expand pushes "
                  "the strip, shuffle slides to the nearest free space, overwrite trims it");
    case GZ_PART_SLIP:
      return TIP_("Slip the shot content: shift which scene frames are shown without "
                  "moving the strip in the master timeline");
    default:
      return "";
  }
}

/* dope-sheet overlay toggles that let the gizmos adjust the scene and preview frame
 * range (BFA - built-in, works without the 3D Sequencer addon). */
static bool scene_strip_use_preview_range_get(const bContext *C)
{
  const SpaceAction *space_action = CTX_wm_space_action(C);
  return space_action != nullptr &&
         (space_action->overlays.flag & ADS_SHOW_USE_PREVIEW_RANGE) != 0;
}

static bool scene_strip_use_scene_range_get(const bContext *C)
{
  const SpaceAction *space_action = CTX_wm_space_action(C);
  return space_action != nullptr &&
         (space_action->overlays.flag & ADS_SHOW_USE_SCENE_RANGE) != 0;
}

/* bfa 3d sequencer: keep the master playhead and frame range, and the strip scene's
 * preview/scene frame range, in sync with the strip (per the dope-sheet overlay
 * toggles). Runs after every drag update and again when a move resolves overlaps. */
static void scene_strip_timing_sync_ranges(bContext *C, wmOperator *op)
{
  SceneStripTimingOp *data = static_cast<SceneStripTimingOp *>(op->customdata);
  Scene *master_scene = data->master_scene;
  Strip *strip = data->strip;
  const bool use_preview_range = scene_strip_use_preview_range_get(C);
  const bool use_scene_range = scene_strip_use_scene_range_get(C);

  /* Keep the master playhead and frame range in sync with the strip. */
  const bool from_frame_start = (data->mode == GZ_PART_LEFT);
  const int frame_end = strip->right_handle(master_scene) - 1;
  if (from_frame_start || ELEM(data->mode, GZ_PART_SLIP, GZ_PART_MOVE)) {
    int update_frame;
    if (data->mode == GZ_PART_MOVE) {
      update_frame = clamp_i(master_scene->r.cfra, strip->left_handle(), frame_end);
    }
    else {
      update_frame = strip->left_handle();
    }
    master_scene->r.cfra = update_frame;
  }
  else {
    master_scene->r.cfra = frame_end;
  }
  master_scene->r.efra = max_ii(frame_end, data->orig_master_efra);
  /* BFA (#6780): the strip scene's own frame range only follows the gizmo when
   * the dope-sheet "Set Scene Range" toggle is on (see update_scene_frame_range
   * below); otherwise the gizmo only changes the strip itself. */

  if (use_preview_range) {
    update_preview_range(master_scene, strip);
  }
  if (use_scene_range) {
    update_scene_frame_range(master_scene, strip);
  }

  WM_event_add_notifier(C, NC_SCENE | ND_SEQUENCER, master_scene);
  WM_event_add_notifier(C, NC_SCENE | ND_FRAME, master_scene);
  ED_region_tag_redraw(CTX_wm_region(C));
}

static void scene_strip_timing_apply(bContext *C, wmOperator *op)
{
  SceneStripTimingOp *data = static_cast<SceneStripTimingOp *>(op->customdata);
  Strip *strip = data->strip;
  Scene *master_scene = data->master_scene;
  const int offset = data->offset;
  int delta = 0;

  const int duration = strip->right_handle(master_scene) - strip->left_handle();
  /* BFA (#6780): scene-range writes are gated on the dope-sheet "Set Scene
   * Range" toggle, so with it off the gizmo only retimes/moves/slips the strip. */
  const bool use_scene_range = scene_strip_use_scene_range_get(C);
  switch (data->mode) {
    case GZ_PART_LEFT:
      delta = duration - data->orig_duration;
      adjust_shot_duration_left(master_scene, strip, -offset - delta, use_scene_range);
      break;
    case GZ_PART_RIGHT:
      delta = duration - data->orig_duration;
      adjust_shot_duration_right(master_scene, strip, offset - delta, use_scene_range);
      break;
    case GZ_PART_MOVE:
      delta = int(strip->start) - int(data->orig_start);
      move_shot(master_scene, strip, offset - delta, use_scene_range);
      break;
    case GZ_PART_SLIP:
      delta = int(strip->startofs) - int(data->orig_startofs);
      slip_shot_content(master_scene, strip, offset - delta, use_scene_range);
      break;
  }

  scene_strip_timing_sync_ranges(C, op);
}

static void scene_strip_timing_ui_cleanup(bContext *C, wmOperator *op)
{
  ED_area_status_text(CTX_wm_area(C), nullptr);
  WM_cursor_modal_restore(CTX_wm_window(C));
  MEM_delete(static_cast<SceneStripTimingOp *>(op->customdata));
  op->customdata = nullptr;
}

/* bfa 3d sequencer: end of a drag. A move can leave the strip overlapping its
 * neighbours; resolve it with the master timeline's overlap mode - the same as
 * releasing a strip grab in the VSE - before the undo step is recorded. */
static void scene_strip_timing_finish(bContext *C, wmOperator *op)
{
  SceneStripTimingOp *data = static_cast<SceneStripTimingOp *>(op->customdata);
  if (data->mode == GZ_PART_MOVE) {
    resolve_move_overlap(data->master_scene, data->strip);
    scene_strip_timing_sync_ranges(C, op);
  }
  scene_strip_timing_ui_cleanup(C, op);
}

static wmOperatorStatus scene_strip_timing_invoke(bContext *C,
                                                  wmOperator *op,
                                                  const wmEvent *event)
{
  Scene *master_scene = nullptr;
  Strip *strip = const_cast<Strip *>(scene_strip_master_get(C, &master_scene));
  if (!strip || !strip->scene) {
    return OPERATOR_CANCELLED;
  }

  SceneStripTimingOp *data = MEM_new<SceneStripTimingOp>(__func__);
  data->strip = strip;
  data->master_scene = master_scene;
  data->mode = RNA_enum_get(op->ptr, "mode");
  data->offset = 0;
  data->orig_duration = strip->right_handle(master_scene) - strip->left_handle();
  data->orig_start = strip->start;
  data->orig_startofs = strip->startofs;
  data->orig_master_efra = master_scene->r.efra;
  data->orig_scene_efra = strip->scene->r.efra;

  ARegion *region = CTX_wm_region(C);
  if (region != nullptr) {
    View2D *v2d = &region->v2d;
    data->start_view_x = round_fl_to_int(
        ui::view2d_region_to_view_x(v2d, float(event->mval[0])));
  }

  op->customdata = data;
  WM_cursor_modal_set(CTX_wm_window(C), WM_CURSOR_X_MOVE);
  WM_event_add_modal_handler(C, op);

  return OPERATOR_RUNNING_MODAL;
}

static wmOperatorStatus scene_strip_timing_modal(bContext *C,
                                                 wmOperator *op,
                                                 const wmEvent *event)
{
  SceneStripTimingOp *data = static_cast<SceneStripTimingOp *>(op->customdata);
  if (!data) {
    return OPERATOR_CANCELLED;
  }

  char header_text[64];
  if (data->mode == GZ_PART_MOVE && strip_move_bump_active(data->master_scene, data->strip)) {
    const char *bump_name = "";
    switch (scene_strip_overlap_mode_get(data->master_scene)) {
      case SEQ_OVERLAP_EXPAND:
        bump_name = "expand";
        break;
      case SEQ_OVERLAP_OVERWRITE:
        bump_name = "overwrite";
        break;
      case SEQ_OVERLAP_SHUFFLE:
        bump_name = "shuffle";
        break;
    }
    SNPRINTF(header_text, "Offset: %d - bump (%s)", data->offset, bump_name);
  }
  else {
    SNPRINTF(header_text, "Offset: %d", data->offset);
  }
  ED_area_status_text(CTX_wm_area(C), header_text);

  switch (event->type) {
    case MOUSEMOVE: {
      ARegion *region = CTX_wm_region(C);
      if (region != nullptr) {
        View2D *v2d = &region->v2d;
        const int view_x = round_fl_to_int(
            ui::view2d_region_to_view_x(v2d, float(event->mval[0])));
        const int offset = view_x - data->start_view_x;
        if (offset != data->offset) {
          data->offset = offset;
          scene_strip_timing_apply(C, op);
        }
      }
      break;
    }
    case LEFTMOUSE:
      if (event->val == KM_RELEASE) {
        scene_strip_timing_finish(C, op);
        return OPERATOR_FINISHED;
      }
      break;
    case EVT_RETKEY:
    case EVT_PADENTER:
      if (event->val == KM_PRESS) {
        scene_strip_timing_finish(C, op);
        return OPERATOR_FINISHED;
      }
      break;
    case RIGHTMOUSE:
    case EVT_ESCKEY:
      if (event->val == KM_PRESS) {
        /* Restore the strip by re-applying with a zero offset, then restore the
         * frame ranges that were possibly extended. */
        data->offset = 0;
        scene_strip_timing_apply(C, op);
        data->master_scene->r.efra = data->orig_master_efra;
        data->strip->scene->r.efra = data->orig_scene_efra;
        scene_strip_timing_ui_cleanup(C, op);
        return OPERATOR_CANCELLED;
      }
      break;
    default:
      break;
  }

  return OPERATOR_RUNNING_MODAL;
}

void ACTION_OT_scene_strip_timing(wmOperatorType *ot)
{
  ot->name = "Adjust Scene Strip Timing";
  ot->idname = "ACTION_OT_scene_strip_timing";
  ot->description = "Adjust the timing of the active scene strip interactively";

  ot->invoke = scene_strip_timing_invoke;
  ot->modal = scene_strip_timing_modal;
  ot->get_description = scene_strip_timing_get_description;

  ot->flag |= OPTYPE_UNDO | OPTYPE_BLOCKING | OPTYPE_GRAB_CURSOR_X;

  RNA_def_enum(ot->srna,
               "mode",
               rna_enum_scene_strip_timing_mode_items,
               GZ_PART_RIGHT,
               "Mode",
               "Which part of the scene strip to adjust");
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name ACTION_OT_scene_strip_scrub operator
 *
 * Scrubs the master sequence timeline from the dope-sheet strip bar.
 * \{ */

static wmOperatorStatus scene_strip_scrub_invoke(bContext *C, wmOperator *op, const wmEvent * /*event*/)
{
  Scene *master_scene = nullptr;
  if (!scene_strip_master_get(C, &master_scene)) {
    return OPERATOR_CANCELLED;
  }
  op->customdata = master_scene;
  WM_event_add_modal_handler(C, op);
  return OPERATOR_RUNNING_MODAL;
}

static wmOperatorStatus scene_strip_scrub_modal(bContext *C, wmOperator *op, const wmEvent *event)
{
  Scene *master_scene = static_cast<Scene *>(op->customdata);
  if (!master_scene) {
    return OPERATOR_CANCELLED;
  }

  switch (event->type) {
    case MOUSEMOVE: {
      ARegion *region = CTX_wm_region(C);
      if (region != nullptr) {
        View2D *v2d = &region->v2d;
        const int frame = round_fl_to_int(
            ui::view2d_region_to_view_x(v2d, float(event->mval[0])));
        if (frame != master_scene->r.cfra) {
          master_scene->r.cfra = frame;
          Scene *active_scene = CTX_data_scene(C);
          if (active_scene && active_scene != master_scene && active_scene->r.cfra != frame) {
            active_scene->r.cfra = frame;
            WM_event_add_notifier(C, NC_SCENE | ND_FRAME, active_scene);
          }
          WM_event_add_notifier(C, NC_SCENE | ND_FRAME, master_scene);
        }
      }
      break;
    }
    case LEFTMOUSE:
      if (event->val == KM_RELEASE) {
        op->customdata = nullptr;
        return OPERATOR_FINISHED;
      }
      break;
    case RIGHTMOUSE:
    case EVT_ESCKEY:
      if (event->val == KM_PRESS) {
        op->customdata = nullptr;
        return OPERATOR_CANCELLED;
      }
      break;
    default:
      break;
  }

  return OPERATOR_RUNNING_MODAL;
}

void ACTION_OT_scene_strip_scrub(wmOperatorType *ot)
{
  ot->name = "Scrub Master Sequence";
  ot->idname = "ACTION_OT_scene_strip_scrub";
  ot->description = "Scrub through the master sequence timeline";

  ot->invoke = scene_strip_scrub_invoke;
  ot->modal = scene_strip_scrub_modal;

  ot->flag |= OPTYPE_UNDO | OPTYPE_BLOCKING;
}

/** \} */

void action_widgets()
{
  /* Create the widget-map for the area here. */
  wmGizmoMapType_Params params{SPACE_ACTION, RGN_TYPE_WINDOW};
  wmGizmoMapType *gzmap_type = WM_gizmomaptype_ensure(&params);
  WM_gizmogrouptype_append_and_link(gzmap_type, ACTION_GGT_scene_strip_gizmos);
  WM_gizmotype_append(ACTION_GT_scene_strip_gizmo);
  WM_gizmotype_append(ACTION_GT_scene_strip_scrub);
}

}  // namespace blender
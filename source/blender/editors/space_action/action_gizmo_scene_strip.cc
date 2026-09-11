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
#include "DNA_space_types.h"
#include "DNA_userdef_types.h"
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

/* Returns the master scene strip the gizmos operate on, and optionally the
 * master scene itself. Works with both the built-in sync (workspace sequencer
 * scene) and the legacy 3D Sequencer addon sync (addon master scene).
 * BFA (#6780): the gizmos are sync-agnostic - they operate whenever a master
 * sequencer timeline is configured, whether or not scene time sync is on
 * (the sync only drives the playhead, not the gizmos). The strip is found by
 * iterating the master timeline's scene strips (the one referencing the active
 * scene), NOT by the playhead position, so the gizmos always draw regardless of
 * where the playhead is. */
static const Strip *scene_strip_master_get(const bContext *C, Scene **r_master_scene)
{
  WorkSpace *workspace = CTX_wm_workspace(C);
  const Scene *active_scene = CTX_data_scene(C);
  if (active_scene == nullptr) {
    return nullptr;
  }
  /* BFA (#6780, §2.8): consider BOTH master stores and pick whichever actually
   * holds a scene strip for the active scene. The old first-wins logic bailed
   * as soon as `workspace->sequencer_scene` was set, even when it had no strip
   * for the active scene; that masked the legacy 3D Sequencer store (whose
   * `master_scene` is a transient WindowManager property, cleared on file load
   * by the addon and only repopulated when the sync toggle runs). With the
   * sync-agnostic scan below the gizmos initialize on load regardless of the
   * sync state. Precedence is unchanged when both stores resolve. */
  const Scene *candidates[2] = {
      workspace ? workspace->sequencer_scene : nullptr,
      timeline_sync_master_scene_get(C),
  };
  for (const Scene *master_scene : candidates) {
    if (master_scene == nullptr) {
      continue;
    }
    const Editing *ed = seq::editing_get(master_scene);
    if (ed == nullptr) {
      continue;
    }
    for (const Strip &s : ed->seqbase) {
      if (s.type == STRIP_TYPE_SCENE && s.scene == active_scene) {
        if (r_master_scene) {
          *r_master_scene = const_cast<Scene *>(master_scene);
        }
        return &s;
      }
    }
  }
  return nullptr;
}

/* Resolved dopesheet x-range of the scene strip gizmo: always the strip's own
 * range (the scene frames the strip plays), regardless of the influence toggles.
 *
 * BFA (#6780) §2.1 (user-corrected): the green/red handles and the move/slip
 * zones cover "basically what's the strip" - they never stretch to the preview
 * or scene range. Those ranges are already drawn by the dope-sheet overlays
 * (preview in orange, the scene render range in grey, the out-of-strip area
 * darkened by `ANIM_draw_scene_strip_range`), so the gizmo must not redraw them;
 * a separate empty-extension band is redundant and was removed. The toggles only
 * decide *which ranges follow the strip's edits* (handled by the operator), not
 * how wide the gizmo is drawn. */
struct SceneStripGizmoExtent {
  float frame_in;
  float frame_out;
};

/* BFA (#6780) §2.7: linear, UNCLAMPED handle -> strip-scene frame map.
 *
 * `give_frame_index()` saturates the content index into `[0, content_length-1]`
 * (`strip_time.cc`), so a strip extended beyond its scene range via hold frames
 * (negative startofs/endofs) collapses onto the scene-range boundary and the
 * gizmo "clamps to the scene range" instead of spanning the strip. Scene strips
 * never play media at a rate (the media playback factor is 1.0 for them) and
 * retiming does not apply to a live scene, so the plain linear form is exact -
 * and critically it does not clamp, so it yields the strip's full extent. */
static float scene_strip_frame_from_handle(const Strip *strip, float handle)
{
  return (handle - strip->content_start()) + strip->scene->r.sfra + strip->anim_startofs;
}

static SceneStripGizmoExtent scene_strip_gizmo_extent(const bContext * /*C*/,
                                                       const Scene *master_scene,
                                                       const Strip *strip)
{
  /* The strip's own extent, mapped linearly (unclamped) so hold frames beyond
   * the scene range stay part of the bar (§2.7). */
  const float left_handle = strip->left_handle();
  const float right_handle = strip->right_handle(master_scene);
  SceneStripGizmoExtent ext{};
  ext.frame_in = scene_strip_frame_from_handle(strip, left_handle);
  ext.frame_out = scene_strip_frame_from_handle(strip, right_handle - 1);
  if (ext.frame_in > ext.frame_out) {
    std::swap(ext.frame_in, ext.frame_out);
  }
  return ext;
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
  const int y_strip = baseline + int(2.0f * ui_scale);

  const SceneStripGizmoExtent ext = scene_strip_gizmo_extent(C, master_scene, strip);

  View2D *v2d = &region->v2d;
  int x_in, x_out, y_dummy;
  ui::view2d_view_to_region(v2d, ext.frame_in, 0.0f, &x_in, &y_dummy);
  ui::view2d_view_to_region(v2d, ext.frame_out, 0.0f, &x_out, &y_dummy);

  const int handle_width = int(8.0f * ui_scale);
  /* bfa 3d sequencer: the move bar (strip location) is the TOP half and the
   * slip bar (strip content) the BOTTOM half - split 50/50 so both zones stay
   * easy to grab. The top zone moves the strip (and, with clamp on, the scene
   * range in lockstep); the bottom zone slips the shot content in the sequencer
   * only. */
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
  /* Move (strip location) on top, slip (strip content) on the bottom. */
  BLI_rcti_init(&rects->move, x_in, x_out, y_strip + move_bar_height, y_strip + strip_height);
  BLI_rcti_init(&rects->slip, x_in, x_out, y_strip, y_strip + move_bar_height);
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
 * the bumped strips. BFA (#6780): shuffle never leaves its lane - it seeks the
 * nearest free spot at the start/end of the same lane (transform_seqbase_shuffle_time)
 * or bounces back, matching the VSE; the previous "never leaves its track" fallback
 * forced the strip back to its original channel and re-shuffled in time, which fought
 * the shuffle mode and could re-create the overlap it just resolved. */
static void resolve_move_overlap(Scene *master_scene, Strip *strip)
{
  Editing *ed = seq::editing_get(master_scene);
  if (ed == nullptr) {
    return;
  }
  Vector<Strip *> source;
  source.append(strip);
  if (scene_strip_overlap_mode_get(master_scene) == SEQ_OVERLAP_SHUFFLE) {
    /* Lane-only shuffle: seek the nearest free spot at the start/end of the same
     * lane, never move to another channel. */
    seq::transform_seqbase_shuffle_time(
        source, &ed->seqbase, master_scene, &master_scene->markers, false);
    strip->runtime->flag &= ~seq::StripRuntimeFlag::Overlap;
    return;
  }
  seq::transform_handle_overlap(master_scene, &ed->seqbase, source, false);
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

/* BFA (#6780): the strip's color the same way the VSE shows it - the strip's
 * color tag when set, else the scene-strip theme color - so the dope-sheet bar
 * and the layered strip indicators match the sequencer strips. */
static void scene_strip_color_get(const Strip *strip, float r_col[4])
{
  uchar col[3] = {180, 180, 180};
  if (strip->color_tag >= STRIP_COLOR_01 && strip->color_tag < STRIP_COLOR_TOT) {
    const bTheme *btheme = ui::theme::theme_get();
    const ThemeStripColor *strip_color = &btheme->strip_color[strip->color_tag];
    col[0] = strip_color->color[0];
    col[1] = strip_color->color[1];
    col[2] = strip_color->color[2];
  }
  else {
    /* BFA (#6780): the active theme is not the sequencer theme when drawing from
     * the dope-sheet, so swap the sequencer theme in for the lookup - same as the
     * VSE's color3ubv_from_seq does - or TH_SEQ_SCENE resolves to the wrong color. */
    ui::theme::bThemeState theme_state;
    ui::theme::theme_store(&theme_state);
    ui::theme::theme_set(SPACE_SEQ, RGN_TYPE_WINDOW);
    ui::theme::get_color_3ubv(TH_SEQ_SCENE, col);
    ui::theme::theme_restore(&theme_state);
  }
  r_col[0] = col[0] / 255.0f;
  r_col[1] = col[1] / 255.0f;
  r_col[2] = col[2] / 255.0f;
  r_col[3] = 1.0f;
}

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

  /* BFA (#6780): dope-sheet overlay toggles for the layered strip indicators -
   * "Show All Strips" draws every scene strip on the master timeline (not just
   * same-scene ones); "Show Strip Names" / "Show Scene Names" control the strip
   * and scene name labels; "All Strips Opacity" scales the indicator alpha. */
  const bool show_all_strips =
      (space_action->overlays.flag & ADS_SHOW_SCENE_STRIP_ALL) != 0;
  const bool show_strip_names =
      (space_action->overlays.flag & ADS_SHOW_SCENE_STRIP_STRIP_NAME) != 0;
  const bool show_scene_names =
      (space_action->overlays.flag & ADS_SHOW_SCENE_STRIP_SCENE_NAME) != 0;

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

  /* BFA (#6780): layered-strip row snug on the marker row - other scene strips
   * referencing the same scene are always shown as full rounded chips, tinted
   * with each strip's own color (color tag or scene-strip theme color), like the
   * sequencer strips. With the opt-in "Show All Strips" overlay toggle, every
   * scene strip on the master timeline is drawn instead, so the full layout
   * (overlaps, pushes, alignment) is visible. Chips that overlap the bar or
   * another chip stack snugly in a lane above (the bar row is lane 0), so
   * crossing/stacking layers pile up instead of overpainting each other. The
   * "All Strips Opacity" overlay setting scales the chip alpha. */
  const Editing *ed = seq::editing_get(master_scene);
  if (ed != nullptr) {
    const float all_opacity = clamp_f(space_action->overlays.all_strips_opacity, 0.0f, 1.0f);
    struct LayeredStripDraw {
      float x_in, x_out;
      float col[4];
      const Strip *strip;
    };
    blender::Vector<LayeredStripDraw> layered_strips;
    for (const Strip &other : ed->seqbase) {
      if (&other == strip || other.type != STRIP_TYPE_SCENE || other.scene == nullptr) {
        continue;
      }
      if (!show_all_strips && other.scene != active_scene) {
        continue;
      }
      const float left_handle = other.left_handle();
      const float right_handle = other.right_handle(master_scene);
      /* BFA (#6780) §2.7: unclamped extent so chips match the bar over its full
       * strip range (hold frames included). */
      float frame_in = scene_strip_frame_from_handle(&other, left_handle);
      float frame_out = scene_strip_frame_from_handle(&other, right_handle - 1);
      if (frame_in > frame_out) {
        std::swap(frame_in, frame_out);
      }
      LayeredStripDraw item;
      item.x_in = region_x_from_view(frame_in);
      item.x_out = region_x_from_view(frame_out);
      item.strip = &other;
      scene_strip_color_get(&other, item.col);
      layered_strips.append(item);
    }

    /* Lane packing: lane 0 is the bar's own row (occupied by the bar over its
     * span), so chips overlapping it or each other are placed one lane up -
     * stacked snug (1 px apart) on top of whatever they cross. */
    constexpr int lane_max = 8;
    struct LaneInterval {
      float x_in, x_out;
    };
    blender::Vector<LaneInterval> lane_intervals[lane_max + 1];
    /* BFA (#6780) §2.7: the bar's lane occupancy uses the same unclamped strip
     * extent the bar itself is drawn with. */
    float bar_frame_in = scene_strip_frame_from_handle(strip, strip->left_handle());
    float bar_frame_out = scene_strip_frame_from_handle(
        strip, strip->right_handle(master_scene) - 1);
    if (bar_frame_in > bar_frame_out) {
      std::swap(bar_frame_in, bar_frame_out);
    }
    lane_intervals[0].append({region_x_from_view(bar_frame_in), region_x_from_view(bar_frame_out)});

    const float lane_gap = 1.0f * ui_scale;
    for (const LayeredStripDraw &item : layered_strips) {
      int lane = 0;
      for (; lane <= lane_max; lane++) {
        bool overlaps = false;
        for (const LaneInterval &occupant : lane_intervals[lane]) {
          if (item.x_in < occupant.x_out + lane_gap && occupant.x_in - lane_gap < item.x_out) {
            overlaps = true;
            break;
          }
        }
        if (!overlaps) {
          break;
        }
      }
      if (lane > lane_max) {
        lane = lane_max;
      }
      lane_intervals[lane].append({item.x_in, item.x_out});

      const float y = baseline + 2.0f * ui_scale + float(lane) * strip_height;
      const float y_top_other = y + strip_height;
      /* BFA (#6780): full rounded chip with outline, matching the master bar and
       * the sequencer scene strips - the strip's own color (color tag or
       * scene-strip theme color) shaded for the body and outline. */
      uchar other_uc[3] = {uchar(item.col[0] * 255.0f),
                           uchar(item.col[1] * 255.0f),
                           uchar(item.col[2] * 255.0f)};
      uchar other_body_uc[3], other_outline_uc[3];
      ui::theme::get_color_shade_3ubv(other_uc, -35, other_body_uc);
      ui::theme::get_color_shade_3ubv(other_uc, 25, other_outline_uc);
      float other_body[4] = {other_body_uc[0] / 255.0f,
                             other_body_uc[1] / 255.0f,
                             other_body_uc[2] / 255.0f,
                             0.45f * all_opacity};
      float other_outline[4] = {other_outline_uc[0] / 255.0f,
                                other_outline_uc[1] / 255.0f,
                                other_outline_uc[2] / 255.0f,
                                0.6f * all_opacity};
      rctf other_rect;
      BLI_rctf_init(&other_rect, item.x_in, item.x_out, y, y_top_other);
      ui::draw_roundbox_corner_set(ui::CNR_ALL);
      ui::draw_roundbox_4fv_ex(&other_rect,
                               other_body,
                               nullptr,
                               1.0f,
                               other_outline,
                               1.5f * ui_scale,
                               3.0f * ui_scale);
      GPU_blend(GPU_BLEND_NONE);
      /* BFA - `draw_roundbox_4fv_ex` renders through a batch which unbinds the GPU
       * program but leaves the immediate-mode shader state bound, so end it before
       * rebinding here (a second bind asserts `imm->shader == nullptr`). */
      immUnbindProgram();
      immBindBuiltinProgram(GPU_SHADER_3D_UNIFORM_COLOR);
      GPU_blend(GPU_BLEND_ALPHA);
      /* BFA (#6780): label per the "Show Strip Names" / "Show Scene Names"
       * overlay toggles, drawn inside the chip when wide enough. */
      if ((show_strip_names || show_scene_names) && item.x_out - item.x_in > 14.0f * ui_scale) {
        char label[128];
        if (show_strip_names && show_scene_names) {
          SNPRINTF(label, "%s | %s", item.strip->name + 2, item.strip->scene->id.name + 2);
        }
        else if (show_strip_names) {
          SNPRINTF(label, "%s", item.strip->name + 2);
        }
        else {
          SNPRINTF(label, "%s", item.strip->scene->id.name + 2);
        }
        const uiStyle *style = ui::style_get();
        uiFontStyle fs = style->widget;
        rcti text_rect;
        BLI_rcti_init(&text_rect,
                      int(item.x_in) + int(4.0f * ui_scale),
                      int(item.x_out) - int(4.0f * ui_scale),
                      int(y),
                      int(y_top_other));
        uchar text_col[4] = {235, 238, 245, uchar(210.0f * all_opacity)};
        ui::FontStyleDrawParams text_params{};
        text_params.align = ui::UI_STYLE_TEXT_CENTER;
        text_params.word_clip = false;
        ui::fontstyle_draw(&fs,
                           &text_rect,
                           label,
                           int(BLI_strnlen(label, sizeof(label))),
                           text_col,
                           &text_params);
      }
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
    /* Seam between the two zones: move (strip location) on top, slip (strip
     * content) on the bottom. */
    const float y_seam = float(rects.slip.ymax);

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

    /* BFA (#6780): the bar body uses the strip's color - the same color tag or
     * scene-strip theme color the VSE shows - shaded for the body and outline. */
    float strip_col[4];
    scene_strip_color_get(strip, strip_col);
    uchar col_uc[3] = {uchar(strip_col[0] * 255.0f),
                       uchar(strip_col[1] * 255.0f),
                       uchar(strip_col[2] * 255.0f)};
    uchar body_uc[3], outline_uc[3];
    ui::theme::get_color_shade_3ubv(col_uc, -35, body_uc);
    ui::theme::get_color_shade_3ubv(col_uc, 25, outline_uc);
    float backdrop_color[4] = {body_uc[0] / 255.0f,
                               body_uc[1] / 255.0f,
                               body_uc[2] / 255.0f,
                               0.8f};
    float backdrop_color_outline[4] = {outline_uc[0] / 255.0f,
                                       outline_uc[1] / 255.0f,
                                       outline_uc[2] / 255.0f,
                                       0.6f};
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
      /* Zone shading: move (top, location) lighter, slip (bottom, content)
       * darker, with a thin seam in between so both areas read even without
       * hovering. */
      /* BFA (#6780): shade the strip color instead of gray, keeping the
       * move-lighter / slip-darker two-tone affordance on the colored body. */
      uchar move_uc[3], slip_uc[3];
      ui::theme::get_color_shade_3ubv(col_uc, 45, move_uc);
      ui::theme::get_color_shade_3ubv(col_uc, -55, slip_uc);
      float zone_move[4] = {move_uc[0] / 255.0f,
                            move_uc[1] / 255.0f,
                            move_uc[2] / 255.0f,
                            0.85f};
      float zone_slip[4] = {slip_uc[0] / 255.0f,
                            slip_uc[1] / 255.0f,
                            slip_uc[2] / 255.0f,
                            0.85f};
      immUniformColor4f(zone_move[0], zone_move[1], zone_move[2], zone_move[3]);
      /* Inset from the chip top/bottom so the rounded border band stays visible. */
      immRectf(pos, zone_x0, y_seam, zone_x1, y_top - border_w);
      immUniformColor4f(zone_slip[0], zone_slip[1], zone_slip[2], zone_slip[3]);
      immRectf(pos, zone_x0, y_strip + border_w, zone_x1, y_seam);
      immUniformColor4f(0.55f, 0.58f, 0.66f, 0.6f);
      immRectf(pos, zone_x0, y_seam - 0.5f, zone_x1, y_seam + 0.5f);

      /* Hover: translucent accent wash over the whole active zone. */
      if (move_hovered) {
        immUniformColor4f(0.42f, 0.62f, 0.95f, 0.4f);
        immRectf(pos, zone_x0, y_seam, zone_x1, y_top - border_w);
      }
      else if (slip_hovered) {
        immUniformColor4f(0.42f, 0.62f, 0.95f, 0.4f);
        immRectf(pos, zone_x0, y_strip + border_w, zone_x1, y_seam);
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

    /* BFA (#6780): the layered strip chips above no longer draw in-bar bands or
     * edge ticks - the lane-stacked chips carry that information instead. */

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
    /* BFA (#6780): label per the "Show Strip Names" / "Show Scene Names"
     * overlay toggles, centered in the top (move) zone so the bar always
     * identifies the shot it belongs to ("Name | Scene" when both are on).
     * Dark label for contrast on the lightened top zone; drawn last (BLF manages
     * its own GPU state, nothing imm follows). */
    if ((show_strip_names || show_scene_names) && zone_x1 - zone_x0 > 6.0f * ui_scale) {
      char label[128];
      if (show_strip_names && show_scene_names && strip->scene) {
        SNPRINTF(label, "%s | %s", strip->name + 2, strip->scene->id.name + 2);
      }
      else if (show_strip_names) {
        SNPRINTF(label, "%s", strip->name + 2);
      }
      else if (strip->scene) {
        SNPRINTF(label, "%s", strip->scene->id.name + 2);
      }
      else {
        SNPRINTF(label, "%s", strip->name + 2);
      }
      const uiStyle *style = ui::style_get();
      uiFontStyle fs = style->widget;
      rcti text_rect;
      BLI_rcti_init(&text_rect,
                    int(zone_x0) + int(2.0f * ui_scale),
                    int(zone_x1) - int(2.0f * ui_scale),
                    int(y_seam),
                    int(y_top));
      uchar text_col[4] = {30, 33, 40, 235};
      ui::FontStyleDrawParams text_params{};
      text_params.align = ui::UI_STYLE_TEXT_CENTER;
      /* BFA (#6780): verbatim strip name - no clipping, show the full name. The
       * name field reserves its first two bytes for the ID_SEQ ("SQ") code, so
       * the actual name starts at name + 2 (same as the RNA Strip.name getter). */
      text_params.word_clip = false;
      ui::fontstyle_draw(&fs,
                         &text_rect,
                         label,
                         int(BLI_strnlen(label, sizeof(label))),
                         text_col,
                         &text_params);
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

/* Map a master-timeline frame to the strip's scene frame reference. */
static int remap_frame_value(const Strip *strip, int frame)
{
  return frame - strip->start + strip->scene->r.sfra;
}

/* bfa 3d sequencer: retime from the right handle. Dragging to the right moves
 * the master-timeline end edge (and the dope-sheet bar edge) forward in lockstep
 * while the start edge stays put. First the trimmed content (a positive end
 * offset) is consumed; once that runs out, the scene's end frame is extended
 * live (when `clamp` is on) or the strip extends via hold frames (when off) so
 * the bar keeps following the mouse instead of stopping at the scene's efra.
 * Like the left handle, the strips after this one on the channel move with the
 * end edge (pushed right when extending, pulled left when shrinking), so the
 * drag never desyncs neighbors. The scene's end frame is bounded by the highest
 * representable frame (#MAXFRAME). */
static int adjust_shot_duration_right(Scene *master_scene,
                                      Strip *strip,
                                      const int frame_offset,
                                      const bool clamp)
{
  const int duration = strip->right_handle(master_scene) - strip->left_handle();
  const int new_duration = max_ii(duration + frame_offset, 1);
  const int new_frame_offset = new_duration - duration;
  if (new_frame_offset == 0) {
    return 0;
  }
  Vector<Strip *> impacted = strips_after_same_channel(master_scene, strip);
  if (new_frame_offset > 0) {
    /* Extend: first absorb the trimmed end content (a positive end offset, i.e.
     * the right handle sits left of the content end), then extend the scene's
     * end frame for the overflow (clamp) or the strip's hold frames (non-clamp),
     * bounded at #MAXFRAME. Following strips are pushed right by the total
     * actually moved (absorb + scene_extend + hold_extend), not the requested
     * offset, so neighbors stay in sync at the bound. */
    const int absorb = min_ii(new_frame_offset, max_ii(int(strip->endofs), 0));
    const int scene_extend = clamp ?
                                 min_ii(new_frame_offset - absorb,
                                        max_ii(MAXFRAME - strip->scene->r.efra, 0)) :
                                 0;
    const int hold_extend = clamp ? 0 : (new_frame_offset - absorb);
    const int moved = absorb + scene_extend + hold_extend;
    if (moved <= 0) {
      return 0;
    }
    for (int i = impacted.size() - 1; i >= 0; i--) {
      seq::transform_translate_strip(master_scene, impacted[i], moved);
    }
    if (absorb != 0) {
      strip->endofs -= absorb;
    }
    if (hold_extend != 0) {
      /* Non-clamp: extend the strip's end edge via hold frames (negative
       * endofs) without touching the scene range. */
      strip->endofs -= hold_extend;
    }
    if (scene_extend > 0) {
      /* Capture the left edge and the right edge *after* the absorb, then extend
       * the scene's end frame and re-derive the content length. Writing efra
       * changes the live content length, which would otherwise shift the handles;
       * re-pin both edges - the left where it was, the right at its absorbed
       * position plus the scene extension - so the end edge lands exactly where
       * the drag asked (same recipe the left side uses when extending sfra). */
      const int left = strip->left_handle();
      const int right_after_absorb = strip->right_handle(master_scene);
      strip->scene->r.efra += scene_extend;
      const int new_len = max_ii(strip->scene->r.efra - strip->scene->r.sfra + 1 -
                                     strip->anim_startofs - strip->anim_endofs,
                                 0);
      strip->content_length_set(new_len);
      strip->handles_set(master_scene, left, right_after_absorb + scene_extend);
    }
    return moved;
  }
  else {
    /* Shrink: adjust the strip first, then move impacted strips to the left. */
    strip->endofs -= new_frame_offset;
    for (Strip *s : impacted) {
      seq::transform_translate_strip(master_scene, s, new_frame_offset);
    }
    return new_frame_offset;
  }
}

/* BFA (#6780): strips on the same channel whose end is entirely before `strip`'s
 * start edge, sorted by start frame (the mirror of `strips_after_same_channel`).
 * The left handle pushes these strips leftwards when extending, just like the
 * right handle pushes the following strips rightwards. */
static Vector<Strip *> strips_before_same_channel(Scene *master_scene, const Strip *strip)
{
  Vector<Strip *> result;
  const Editing *ed = seq::editing_get(master_scene);
  if (!ed) {
    return result;
  }
  for (Strip &s : ed->seqbase) {
    if (&s == strip || s.channel != strip->channel ||
        s.right_handle(master_scene) >= strip->left_handle())
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

/* bfa 3d sequencer: retime from the left handle. Dragging to the left moves the
 * master-timeline start edge (and the dope-sheet bar edge) back in lockstep while
 * the end edge stays put, so the strip feels "in sync" with the dope-sheet. First
 * the trimmed content is consumed; once that runs out, the scene's start frame is
 * extended (when `clamp` is on) or the strip extends via hold frames (when off).
 * Like the right handle, the strips before this one on the channel move with the
 * start edge (pushed left when extending, pulled right when shrinking), so the
 * drag keeps going into earlier frames instead of getting stuck at the previous
 * strip or at frame 0. Both the start edge and the scene's start frame are
 * bounded by the lowest representable frame (#MINAFRAME).
 * Returns the signed displacement applied to the preceding strips (positive when
 * they were pushed left), so the modal operator can undo it on cancel. */
static int adjust_shot_duration_left(Scene *master_scene,
                                      Strip *strip,
                                      const int frame_offset,
                                      const bool clamp)
{
  const int duration = strip->right_handle(master_scene) - strip->left_handle();
  const int new_duration = max_ii(duration + frame_offset, 1);
  const int new_frame_offset = new_duration - duration;
  if (new_frame_offset == 0) {
    return 0;
  }
  if (new_frame_offset > 0) {
    /* Extend: first consume trimmed content (master start edge moves left), then
     * optionally extend the scene's start frame (clamp) or the strip's hold
     * frames (non-clamp). Both move the start edge, so the preceding strips on
     * the channel are pushed left by the same total amount - mirrored from
     * adjust_shot_duration_right(), which pushes the following strips right when
     * extending. */
    const int trim = min_ii(new_frame_offset,
                            min_ii(int(strip->startofs),
                                   max_ii(strip->left_handle() - MINAFRAME, 0)));
    /* Extending the scene's start frame is bounded by the lowest representable
     * frame, like every scene frame range (BFA) - both for the scene's start
     * frame itself and for the master start edge that follows it. In non-clamp
     * mode the scene range is left untouched and the strip extends via hold
     * frames (negative startofs). */
    const int scene_extend = clamp ?
                                 min_ii(new_frame_offset - trim,
                                        min_ii(max_ii(strip->scene->r.sfra - MINAFRAME, 0),
                                               max_ii(strip->left_handle() - trim - MINAFRAME, 0))) :
                                 0;
    const int hold_extend = clamp ? 0 : (new_frame_offset - trim);
    const int moved = trim + scene_extend + hold_extend;
    if (moved <= 0) {
      return 0;
    }
    for (Strip *impacted : strips_before_same_channel(master_scene, strip)) {
      seq::transform_translate_strip(master_scene, impacted, -moved);
    }
    if (trim != 0) {
      strip->startofs -= trim;
    }
    if (hold_extend != 0) {
      /* Non-clamp: extend the strip's start edge via hold frames (negative
       * startofs) without touching the scene range. */
      strip->startofs -= hold_extend;
    }
    if (scene_extend > 0) {
      /* Capture the end edge before the start moves: the scene-strip content
       * length is derived live from the scene range, so moving `start` without
       * this snapshot would drag the end edge along (the handles are re-pinned
       * below to the captured end edge). */
      const int right = strip->right_handle(master_scene);
      strip->start -= scene_extend;
      strip->scene->r.sfra -= scene_extend;
      /* Re-evaluate the content length for the extended scene, keeping the
       * (already moved) start edge and the captured end edge. */
      const int left = strip->left_handle();
      const int new_len = max_ii(strip->scene->r.efra - strip->scene->r.sfra + 1 -
                                     strip->anim_startofs - strip->anim_endofs,
                                 0);
      strip->content_length_set(new_len);
      strip->handles_set(master_scene, left, right);
    }
    return moved;
  }
  /* Shrink: the master start edge moves right; the end edge (and any following
   * strips) stay put. The strips before this one follow the edge - mirrored from
   * adjust_shot_duration_right(), whose following strips follow on shrink. */
  const int pulled = -new_frame_offset;
  strip->startofs -= new_frame_offset;
  for (Strip *impacted : strips_before_same_channel(master_scene, strip)) {
    seq::transform_translate_strip(master_scene, impacted, pulled);
  }
  return -pulled;
}

static void move_shot(Scene *master_scene,
                       Strip *strip,
                       const int frame_offset)
{
  if (frame_offset == 0) {
    return;
  }
  seq::transform_translate_strip(master_scene, strip, frame_offset);
}

/* Update the strip's scene preview range to match the strip (dope-sheet overlay
 * toggle). If the scene has no preview range yet (#SCER_PRV_RANGE), the first
 * gizmo write enables it and seeds it from the render range (BFA #6780, §2.4):
 * "Set Preview Range" implies preview mode, otherwise the written values would
 * be invisible. The flag rides the operator's undo step and is restored on
 * cancel (see the snapshot in #SceneStripTimingOp). */
static void update_preview_range(Scene *master_scene, Strip *strip)
{
  if (!strip->scene) {
    return;
  }
  if ((strip->scene->r.flag & SCER_PRV_RANGE) == 0) {
    strip->scene->r.flag |= SCER_PRV_RANGE;
    strip->scene->r.psfra = strip->scene->r.sfra;
    strip->scene->r.pefra = strip->scene->r.efra;
  }
  const int start = remap_frame_value(strip, strip->left_handle());
  const int end = remap_frame_value(strip, strip->right_handle(master_scene) - 1);
  strip->scene->r.psfra = start;
  strip->scene->r.pefra = end;
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
  /* Original frame range to restore/keep on cancel. */
  int orig_master_efra;
  int orig_master_sfra;
  /* BFA (#6780): LEFT/RIGHT-drag snapshot for an exact cancel - extending the
   * start/end consumes trims, extends the scene's start/end frame and pushes the
   * preceding/following strips; re-applying a zero offset cannot undo those. */
  int orig_left_handle;
  int orig_right_handle;
  float orig_endofs;
  int orig_len;
  /* BFA (#6780, §2.4): the slip mechanism moves the strip's anim offsets when
   * the preview toggle is off (seq::time_slip_strip) - cancel must restore
   * them exactly or a cancelled slip leaves the bar shifted. */
  int orig_anim_startofs;
  int orig_anim_endofs;
  int orig_sfra;
  int orig_efra;
  /* BFA (#6780): preview-range snapshot for the range-window mover (top middle
   * gizmo) - it translates psfra/pefra (and, with clamp on, sfra/efra) while the
   * strip stays locked. */
  int orig_psfra;
  int orig_pefra;
  /* BFA (#6780): the scene's render flags - "Set Preview Range" may enable
   * #SCER_PRV_RANGE mid-drag (update_preview_range); cancel must undo that. */
  short orig_scene_flag;
  /* BFA (#6780): middle-bar range coupling, captured at invoke (§2.4). The
   * drag must not re-evaluate the toggles mid-flight: a toggle change during
   * an active drag would switch the slip mechanism under the servo. The
   * preview coupling only applies when the scene actually has a preview
   * range (#SCER_PRV_RANGE) - without it there is nothing to translate. */
  bool preview_coupled;
  bool clamp_coupled;
  /* Signed displacement applied to the preceding strips by
   * adjust_shot_duration_left (positive when they were pushed left). */
  int pushed_before_total;
  /* Signed displacement applied to the following strips by
   * adjust_shot_duration_right (positive when they were pushed right). */
  int pushed_following_total;
  /* BFA (#6780): whether the strip was selected before the drag, so the
   * temporary SEQ_SELECT set during the drag can be restored on release. */
  bool orig_select;
};

static const EnumPropertyItem rna_enum_scene_strip_timing_mode_items[] = {
    {GZ_PART_LEFT, "LEFT", 0, "Left Handle", "Shift the shot's start frame in the master timeline"},
    {GZ_PART_RIGHT, "RIGHT", 0, "Right Handle", "Shift the shot's end frame in the master timeline"},
    {GZ_PART_MOVE, "MOVE", 0, "Move Range", "Move the scene/preview range window"},
    {GZ_PART_SLIP, "SLIP", 0, "Move Strip", "Move the strip in the sequencer timeline"},
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
      return TIP_("Move the range window: shift the strip scene's preview range "
                  "(and, with Clamp to Scene Strip on, the scene range) while the "
                  "strip stays locked in the sequencer");
    case GZ_PART_SLIP:
      return TIP_("Move the strip in the sequencer timeline. The preview range "
                  "stays locked unless Set Preview Range is on; with Clamp to "
                  "Scene Strip on, the scene range moves with the strip and "
                  "snaps to it with lead-in/out on release. When it bumps into "
                  "another strip the sequencer overlap mode applies on release: "
                  "expand pushes the strip, shuffle slides to the nearest free "
                  "space, overwrite trims it");
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

/* BFA (#6780): when the dope-sheet "Set Preview Range" toggle is off, the gizmo
 * must never touch the strip scene's preview range. The sequencer scene-time
 * sync loop can re-derive psfra/pefra as a side effect of a clamp-mode
 * sfra/efra write (the master-scene/shot coupling refreshes the preview range
 * from the render range), so re-assert the pre-drag preview range after every
 * range write. Gated on the toggle: when it is on, update_preview_range() owns
 * the preview range and this is a no-op. */
static void restore_preview_range(bContext *C, wmOperator *op)
{
  SceneStripTimingOp *data = static_cast<SceneStripTimingOp *>(op->customdata);
  if (scene_strip_use_preview_range_get(C)) {
    return;
  }
  if (!data->strip->scene) {
    return;
  }
  data->strip->scene->r.psfra = data->orig_psfra;
  data->strip->scene->r.pefra = data->orig_pefra;
}

/* BFA (#6780): "Clamp to Scene Strip" opt-in toggle - when on, the gizmo clamps
 * the strip scene's frame range (sfra/efra) to the strip's visible extent after
 * editing it. */
static bool scene_strip_clamp_to_strip_get(const bContext *C)
{
  const SpaceAction *space_action = CTX_wm_space_action(C);
  return space_action != nullptr &&
         (space_action->overlays.flag & ADS_SHOW_CLAMP_TO_SCENE_STRIP) != 0;
}

/* BFA (#6780): clamp the strip scene's frame range to the strip's visible extent.
 * Only sfra/efra (the render range) are touched - the preview range, the strip's
 * position in the master timeline and the strip's internal time range all stay
 * unchanged. The start is floored at #MINAFRAME (matching adjust_shot_duration_left,
 * which extends the scene start into earlier frames on the green handle); the end
 * is never clamped down below the start.
 *
 * BFA (#6780): SET semantics (1:1), matching the addon's
 * SEQUENCER_OT_sync_scene_strip_ranges operator - the scene range is set to the
 * strip's visible extent (with lead-in/out padding), not extend-only. Extend-only
 * never shrinks, which made the range drift ("cuts/compresses at edges then pushes
 * out on release") and blocked the left handle from moving the start frame forward.
 *
 * BFA (#6780): the scene frame shown at a master-timeline frame is
 * `frame - strip->start + sfra`, so sfra feeds back into the remap. Setting
 * sfra alone would shift the displayed content by the strip's trim offset on the
 * next evaluation (the start edge "jumps" like a cyclic dependency; the end edge
 * is unaffected because efra is not part of the remap). To keep the displayed
 * content fixed we shift sfra and strip->start in lockstep (same delta) and
 * compensate startofs so the master left_handle stays put.
 *
 * BFA (#6780): for scene strips the content length is derived live from the scene
 * range, so writing sfra/efra auto-derives a new content length and would shift the
 * strip's handles (the Set-Scene-Range lesson). The handles are snapshotted before
 * the write and re-pinned afterwards (same as adjust_shot_duration_left does when
 * it extends the scene) so the strip's master position and displayed content stay
 * exactly where they were. */
static void clamp_scene_strip_range(const bContext *C, Scene *master_scene, Strip *strip)
{
  if (!strip->scene) {
    return;
  }
  const SpaceAction *space_action = CTX_wm_space_action(C);
  const int lead_in = space_action ? space_action->overlays.clamp_lead_in : 0;
  const int lead_out = space_action ? space_action->overlays.clamp_lead_out : 0;
  const int left = strip->left_handle();
  const int right = strip->right_handle(master_scene);
  const int visible_start = remap_frame_value(strip, left);
  const int visible_end = remap_frame_value(strip, right - 1);
  /* SET (1:1): align the scene range to the strip's visible extent, with lead
   * padding. BFA (#6780): the start is floored at #MINAFRAME (not 0) so the
   * green handle can set render ranges into the earlier (negative) frames,
   * mirroring the red handle where efra has no upper clamp. */
  const int new_sfra = max_ii(visible_start - lead_in, MINAFRAME);
  const int new_efra = visible_end + lead_out;
  if (new_sfra == strip->scene->r.sfra && new_efra == strip->scene->r.efra) {
    return;
  }
  /* Shift sfra and strip->start in lockstep so the remap (displayed content) stays
   * constant, and compensate startofs so the master left_handle stays put. */
  const int delta_sfra = new_sfra - strip->scene->r.sfra;
  strip->scene->r.sfra = new_sfra;
  strip->scene->r.efra = new_efra;
  strip->start += delta_sfra;
  strip->startofs -= delta_sfra;
  /* Re-evaluate the content length for the new scene range and re-pin the handles
   * so the strip's master position stays fixed. */
  const int new_len = max_ii(new_efra - new_sfra + 1 - strip->anim_startofs -
                                 strip->anim_endofs,
                             0);
  strip->content_length_set(new_len);
  strip->handles_set(master_scene, left, right);
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

  /* Keep the master playhead and frame range in sync with the strip. */
  const bool from_frame_start = (data->mode == GZ_PART_LEFT);
  const int frame_end = strip->right_handle(master_scene) - 1;
  if (from_frame_start || ELEM(data->mode, GZ_PART_SLIP, GZ_PART_MOVE)) {
    int update_frame;
    if (data->mode == GZ_PART_SLIP) {
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
  /* BFA (#6780): with "Clamp to Scene Strip" on, the SLIP bar (strip mover)
   * also lowers the master start frame to keep the view following a leftward
   * drag, mirroring the efra follow above. Only the master range is touched
   * (never strip->start), so the SLIP delta tracking stays stable. Floored at
   * #MINAFRAME like every scene frame range (BFA) - the mirror of the red
   * handle's MAXFRAME-bound efra. */
  if (data->mode == GZ_PART_SLIP && scene_strip_clamp_to_strip_get(C)) {
    master_scene->r.sfra = min_ii(master_scene->r.sfra,
                                  max_ii(strip->left_handle(), MINAFRAME));
  }
  /* BFA (#6780): the strip scene's preview range follows the gizmo when the
   * dope-sheet "Set Preview Range" toggle is on - in all modes. When the toggle
   * is off, only the strip range (and, with clamp on, the scene range) is
   * affected. */

  /* BFA (#6780): the strip scene's preview range follows the retime handles
   * (LEFT/RIGHT) when the dope-sheet "Set Preview Range" toggle is on: the
   * preview window is the strip's visible extent, so it is recomputed. The
   * middle bars translate the preview range 1:1 in their apply branches
   * instead (§2.4): a recompute is a no-op for the content-window move (the
   * strip's visible extent does not change) and could not keep the preview
   * window glued to a slip/move that the recompute never sees. */
  if (use_preview_range && ELEM(data->mode, GZ_PART_LEFT, GZ_PART_RIGHT)) {
    update_preview_range(master_scene, strip);
  }
  /* BFA (#6780): when the "Set Preview Range" toggle is off, the gizmo must
   * never touch the strip scene's preview range. The sequencer scene-time sync
   * loop can re-derive psfra/pefra as a side effect of a clamp-mode sfra/efra
   * write (the master-scene/shot coupling refreshes the preview range from the
   * render range), so re-assert the pre-drag preview range after every range
   * write. No-op when the toggle is on (update_preview_range owns it). */
  restore_preview_range(C, op);
  /* BFA (#6780): "Clamp to Scene Strip" is intentionally NOT applied during the
   * drag - clamp_scene_strip_range() shifts strip->start/startofs, which feeds
   * back into the modal drag's delta tracking and makes the strip race/exponentially
   * accelerate (the end handle is unaffected because efra is not in the remap
   * formula). The clamp runs once on release (scene_strip_timing_finish), where it
   * cannot fight the drag. Only the render range (sfra/efra) is touched then. */

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
  switch (data->mode) {
    case GZ_PART_LEFT:
      delta = duration - data->orig_duration;
      data->pushed_before_total += adjust_shot_duration_left(
          master_scene, strip, -offset - delta, scene_strip_clamp_to_strip_get(C));
      break;
    case GZ_PART_RIGHT:
      delta = duration - data->orig_duration;
      data->pushed_following_total += adjust_shot_duration_right(
          master_scene, strip, offset - delta, scene_strip_clamp_to_strip_get(C));
      break;
    case GZ_PART_MOVE: {
      /* BFA (#6780): the top middle gizmo moves the strip's content window (its
       * start/end in the dopesheet) while the sequencer position stays locked.
       * In clamp mode this shifts the scene range (sfra/efra); in non-clamp mode
       * it shifts the strip's handles (startofs/endofs). The preview range
       * translates 1:1 here when preview-coupled (captured at invoke, §2.4). */
      const bool clamp = data->clamp_coupled;
      delta = clamp ? strip->scene->r.sfra - data->orig_sfra :
                      int(strip->startofs) - int(data->orig_startofs);
      int moved = offset - delta;
      if (moved != 0) {
        if (clamp && strip->scene) {
          /* Translate the scene range only as far as the representable frame
           * bounds allow (BFA) - the range is the window's only stop. */
          moved = clamp_i(moved,
                          MINAFRAME - strip->scene->r.sfra,
                          MAXFRAME - strip->scene->r.efra);
          strip->scene->r.sfra += moved;
          strip->scene->r.efra += moved;
        }
        else if (!clamp) {
          strip->startofs += moved;
          strip->endofs -= moved;
        }
      }
      /* BFA (#6780): the preview range translates 1:1 with the window move
       * when the drag is preview-coupled (captured at invoke), so the preview
       * window slips with the content (§2.4) - the recompute used before was
       * a no-op here (the strip's visible extent does not change) and left
       * the preview range behind. */
      if (data->preview_coupled && strip->scene && moved != 0) {
        strip->scene->r.psfra = clamp_i(
            strip->scene->r.psfra + moved, MINAFRAME, MAXFRAME);
        strip->scene->r.pefra = clamp_i(
            strip->scene->r.pefra + moved, MINAFRAME, MAXFRAME);
      }
      break;
    }
    case GZ_PART_SLIP: {
      /* BFA (#6780): the bottom middle gizmo moves the STRIP in the sequencer
       * (its start/end in the master timeline). With "Clamp to Scene Strip"
       * on, the strip scene's range (sfra/efra) translates 1:1 in lockstep -
       * the strip stays glued to the master sequencer range (§2.5); without
       * clamp the scene range stays locked. The preview range translates 1:1
       * here when preview-coupled (captured at invoke, §2.4). */
      const bool clamp = data->clamp_coupled;
      /* BFA (#6780) §2.5: apply only the increment since the last mousemove.
       * The servo derives the already-applied displacement from the strip's
       * state (like the MOVE branch derives it from the scene range), so a
       * partially-applied increment cannot accumulate - re-applying the
       * cumulative mouse offset on every move made the strip race ahead of
       * the cursor. */
      int moved_request = offset - int(strip->start - data->orig_start);
      if (clamp && strip->scene) {
        /* The strip stays glued to the scene range, so it can only move as
         * far as the range can follow - its only two stops are the scene
         * frame bounds (BFA), the same bounds the MOVE branch uses. */
        moved_request = clamp_i(moved_request,
                                MINAFRAME - strip->scene->r.sfra,
                                MAXFRAME - strip->scene->r.efra);
      }
      const int start_before = int(strip->start);
      if (moved_request != 0) {
        move_shot(master_scene, strip, moved_request);
      }
      const int moved = int(strip->start) - start_before;
      if (moved != 0) {
        if (clamp && strip->scene) {
          /* Lockstep: the scene range follows the strip exactly (its length
           * is preserved; the release SET clamp adds the lead padding). */
          strip->scene->r.sfra += moved;
          strip->scene->r.efra += moved;
        }
        /* BFA (#6780): the preview range translates 1:1 with the strip move
         * when the drag is preview-coupled (captured at invoke): the preview
         * window slides with the strip (§2.4). */
        if (data->preview_coupled && strip->scene) {
          strip->scene->r.psfra = clamp_i(
              strip->scene->r.psfra + moved, MINAFRAME, MAXFRAME);
          strip->scene->r.pefra = clamp_i(
              strip->scene->r.pefra + moved, MINAFRAME, MAXFRAME);
        }
      }
      /* BFA (#6780): live overlap feedback during the drag, same as the VSE -
       * set the Overlap runtime flag while the moved strip overlaps a neighbour
       * so the dope-sheet bar shows the red outline; cleared on release after
       * resolve_move_overlap() applies the overlap mode. */
      strip->runtime->flag &= ~seq::StripRuntimeFlag::Overlap;
      if (Editing *ed = seq::editing_get(master_scene)) {
        if (seq::transform_test_overlap(master_scene, &ed->seqbase, strip)) {
          strip->runtime->flag |= seq::StripRuntimeFlag::Overlap;
        }
      }
      break;
    }
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
  if (data->mode == GZ_PART_SLIP) {
    /* BFA (#6780) §2.5: with "Clamp to Scene Strip" on, the strip mover snaps
     * the scene range to the strip on release (lead-in/out padding), like the
     * retime handles. The clamp runs BEFORE the overlap resolution because its
     * lockstep compensation shifts the strip by the lead padding - a shift
     * that could push it into a neighbour; the overlap mode then settles that
     * collision, exactly like a plain move release. */
    if (scene_strip_clamp_to_strip_get(C)) {
      clamp_scene_strip_range(C, data->master_scene, data->strip);
    }
    resolve_move_overlap(data->master_scene, data->strip);
    scene_strip_timing_sync_ranges(C, op);
  }
  /* BFA (#6780): "Clamp to Scene Strip" runs once on release, never during the
   * drag - clamp_scene_strip_range() shifts strip->start/startofs which feeds
   * back into the modal drag's delta tracking and would make the strip race.
   * At release the strip's final geometry is settled, so the clamp only touches
   * the scene render range (sfra/efra) and keeps everything else fixed.
   * BFA (#6780): the retime handles (LEFT/RIGHT) and the strip mover (SLIP,
   * §2.5) run the release clamp. MOVE (range window) already translated
   * sfra/efra live in clamp mode, so snapping it again would only re-pad the
   * same range. */
  if (scene_strip_clamp_to_strip_get(C) && ELEM(data->mode, GZ_PART_LEFT, GZ_PART_RIGHT)) {
    clamp_scene_strip_range(C, data->master_scene, data->strip);
    scene_strip_timing_sync_ranges(C, op);
  }
  /* BFA (#6780): restore the strip's selection state from before the drag. */
  if (!data->orig_select) {
    data->strip->flag &= ~SEQ_SELECT;
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
  data->orig_master_sfra = master_scene->r.sfra;
  /* BFA (#6780): exact-drag snapshot for a cancel (see the modal handler). */
  data->orig_left_handle = strip->left_handle();
  data->orig_right_handle = strip->right_handle(master_scene);
  data->orig_endofs = strip->endofs;
  data->orig_len = strip->len;
  data->orig_anim_startofs = strip->anim_startofs;
  data->orig_anim_endofs = strip->anim_endofs;
  data->orig_sfra = strip->scene->r.sfra;
  data->orig_efra = strip->scene->r.efra;
  data->orig_psfra = strip->scene->r.psfra;
  data->orig_pefra = strip->scene->r.pefra;
  data->orig_scene_flag = strip->scene->r.flag;
  /* BFA (#6780): capture the middle-bar coupling state at invoke (§2.4) -
   * the drag ignores toggle changes mid-flight. */
  data->preview_coupled = scene_strip_use_preview_range_get(C) &&
                          (strip->scene->r.flag & SCER_PRV_RANGE) != 0;
  data->clamp_coupled = scene_strip_clamp_to_strip_get(C);
  data->pushed_before_total = 0;
  data->pushed_following_total = 0;

  /* BFA (#6780): mark the dragged strip as selected for the duration of the
   * drag, like the VSE does. The overlap resolution (query_overwrite_targets)
   * excludes selected strips, so without this the overwrite mode would target
   * the dragged strip itself and fall back to a shuffle. */
  data->orig_select = (strip->flag & SEQ_SELECT) != 0;
  strip->flag |= SEQ_SELECT;

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
  if (data->mode == GZ_PART_SLIP && strip_move_bump_active(data->master_scene, data->strip)) {
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
        /* BFA (#6780): exact restore for all drag modes. LEFT and RIGHT push
         * same-channel neighbors and extend the strip scene's start/end frame;
         * MOVE (range window) translates the preview/scene range; SLIP (strip
         * mover) translates the strip and may lower the master sfra when clamp
         * follows live. Re-applying a zero offset cannot undo any of these, so
         * the snapshot restores them exactly. */
        {
          Strip *strip = data->strip;
          if (data->mode == GZ_PART_LEFT && data->pushed_before_total != 0) {
            for (Strip *impacted :
                 strips_before_same_channel(data->master_scene, data->strip))
            {
              seq::transform_translate_strip(
                  data->master_scene, impacted, data->pushed_before_total);
            }
          }
          if (data->mode == GZ_PART_RIGHT && data->pushed_following_total != 0) {
            for (Strip *impacted :
                 strips_after_same_channel(data->master_scene, data->strip))
            {
              seq::transform_translate_strip(
                  data->master_scene, impacted, -data->pushed_following_total);
            }
          }
          strip->start = data->orig_start;
          strip->startofs = data->orig_startofs;
          strip->endofs = data->orig_endofs;
          strip->anim_startofs = data->orig_anim_startofs;
          strip->anim_endofs = data->orig_anim_endofs;
          strip->content_length_set(data->orig_len);
          if (strip->scene) {
            strip->scene->r.sfra = data->orig_sfra;
            strip->scene->r.efra = data->orig_efra;
            strip->scene->r.psfra = data->orig_psfra;
            strip->scene->r.pefra = data->orig_pefra;
            strip->scene->r.flag = data->orig_scene_flag;
          }
          strip->handles_set(
              data->master_scene, data->orig_left_handle, data->orig_right_handle);
          scene_strip_timing_sync_ranges(C, op);
          data->master_scene->r.efra = data->orig_master_efra;
          data->master_scene->r.sfra = data->orig_master_sfra;
        }
        /* BFA (#6780): restore the strip's selection state from before the drag. */
        if (!data->orig_select) {
          data->strip->flag &= ~SEQ_SELECT;
        }
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
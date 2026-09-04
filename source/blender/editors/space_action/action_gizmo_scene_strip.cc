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

static bool timeline_sync_bool_get(const bContext *C, const char *prop_name)
{
  PointerRNA settings;
  if (!timeline_sync_settings_ptr(C, &settings)) {
    return false;
  }
  return RNA_boolean_get(&settings, prop_name);
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
  const int strip_height = int(20.0f * ui_scale);
  const int y_strip = baseline + int(14.0f * ui_scale);

  float frame_in, frame_out;
  scene_strip_frame_range(master_scene, strip, &frame_in, &frame_out);

  View2D *v2d = &region->v2d;
  int x_in, x_out, y_dummy;
  ui::view2d_view_to_region(v2d, frame_in, 0.0f, &x_in, &y_dummy);
  ui::view2d_view_to_region(v2d, frame_out, 0.0f, &x_out, &y_dummy);

  const int handle_width = int(8.0f * ui_scale);
  const int move_bar_height = int(strip_height * 0.7f);
  const int slip_bar_height = int(strip_height * 0.3f);

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
  BLI_rcti_init(&rects->move,
                x_in,
                x_out,
                y_strip + strip_height - move_bar_height,
                y_strip + strip_height);
  BLI_rcti_init(&rects->slip, x_in, x_out, y_strip, y_strip + slip_bar_height);
  BLI_rcti_init(&rects->scrub, 0, region->winx, baseline, baseline + timeline_height);
  return true;
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
  for (int i = 0; i < 4; i++) {
    if (group->gizmos[i]->state & WM_GIZMO_STATE_HIGHLIGHT) {
      highlight = i;
      break;
    }
  }

  const float ui_scale = UI_SCALE_FAC;
  const bool has_markers = !BLI_listbase_is_empty(&active_scene->markers);
  const float baseline = has_markers ? float(UI_MARKER_MARGIN_Y) : 14.0f * ui_scale;
  const float timeline_height = 28.0f * ui_scale;
  const float strip_height = 20.0f * ui_scale;

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

  /* Current master-frame highlight (scrub position). */
  immUniformColor4f(0.1f, 0.5f, 0.8f, 0.6f);
  const float cfra_x = region_x_from_view(float(master_scene->r.cfra));
  immRectf(pos, cfra_x, baseline, cfra_x + 1.0f, baseline + timeline_height);

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

    immUniformColor4f(0.1f, 0.1f, 0.1f, 0.8f);
    immRectf(pos, x_in, y_strip, x_out, y_strip + strip_height);

    if (highlight == GZ_PART_MOVE) {
      immUniformColor4f(0.35f, 0.55f, 0.75f, 0.55f);
      immRectf(pos, x_in, float(rects.move.ymin), x_out, float(rects.move.ymax));
    }
    else if (highlight == GZ_PART_SLIP) {
      immUniformColor4f(0.35f, 0.55f, 0.75f, 0.55f);
      immRectf(pos, x_in, float(rects.slip.ymin), x_out, float(rects.slip.ymax));
    }

    if (highlight == GZ_PART_LEFT) {
      immUniformColor4f(0.3f, 0.95f, 0.4f, 0.95f);
    }
    else {
      immUniformColor4f(0.3f, 0.95f, 0.4f, 0.6f);
    }
    immRectf(pos, float(rects.left.xmin), y_strip, float(rects.left.xmax), y_strip + strip_height);

    if (highlight == GZ_PART_RIGHT) {
      immUniformColor4f(0.95f, 0.3f, 0.4f, 0.95f);
    }
    else {
      immUniformColor4f(0.95f, 0.3f, 0.4f, 0.6f);
    }
    immRectf(pos, float(rects.right.xmin), y_strip, float(rects.right.xmax), y_strip + strip_height);
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

  SceneStripGizmoRects rects;
  const bool has_rects = scene_strip_gizmo_rects_get(C, &rects);

  for (int i = 0; i < 4; i++) {
    WM_gizmo_set_flag(group->gizmos[i], WM_GIZMO_HIDDEN, !has_rects);
  }
  WM_gizmo_set_flag(group->scrub, WM_GIZMO_HIDDEN, !has_rects);
}

void ACTION_GGT_scene_strip_gizmos(wmGizmoGroupType *gzgt)
{
  gzgt->name = "Scene Strip Gizmos";
  gzgt->idname = "ACTION_GGT_scene_strip_gizmos";

  gzgt->flag |= WM_GIZMOGROUPTYPE_PERSISTENT;

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

static void adjust_shot_duration_right(Scene *master_scene, Strip *strip, const int frame_offset)
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
  adapt_scene_range(master_scene, strip);
}

static void adjust_shot_duration_left(Scene *master_scene, Strip *strip, const int frame_offset)
{
  const int duration = strip->right_handle(master_scene) - strip->left_handle();
  const int new_duration = max_ii(duration + frame_offset, 1);
  int new_frame_offset = new_duration - duration;
  /* Clamp so the strip's start never goes before the internal scene's frame start. */
  const int remapped = remap_frame_value(strip, strip->left_handle());
  const int new_start = max_ii(remapped - new_frame_offset, strip->scene->r.sfra);
  new_frame_offset = new_start - remapped;
  if (new_frame_offset == 0) {
    return;
  }
  Vector<Strip *> impacted = strips_after_same_channel(master_scene, strip);
  if (new_frame_offset > 0) {
    /* Extend to the left: adjust the strip, then move impacted strips to the left. */
    strip->startofs += new_frame_offset;
    strip->start -= new_frame_offset;
    for (Strip *s : impacted) {
      seq::transform_translate_strip(master_scene, s, -new_frame_offset);
    }
  }
  else {
    /* Shrink from the left: move impacted strips to the right first (reversed order). */
    for (int i = impacted.size() - 1; i >= 0; i--) {
      seq::transform_translate_strip(master_scene, impacted[i], -new_frame_offset);
    }
    strip->start -= new_frame_offset;
    strip->startofs += new_frame_offset;
  }
  adapt_scene_range(master_scene, strip);
}

static void move_shot(Scene *master_scene, Strip *strip, const int frame_offset)
{
  if (frame_offset == 0) {
    return;
  }
  seq::transform_translate_strip(master_scene, strip, frame_offset);
  adapt_scene_range(master_scene, strip);
}

static void slip_shot_content(Scene *master_scene, Strip *strip, const int frame_offset)
{
  const int remapped_start = remap_frame_value(strip, strip->left_handle());
  const int new_start = max_ii(remapped_start + frame_offset, strip->scene->r.sfra);
  const int new_frame_offset = new_start - remapped_start;
  if (new_frame_offset == 0) {
    return;
  }
  strip->startofs += new_frame_offset;
  strip->start -= new_frame_offset;
  adapt_scene_range(master_scene, strip);
}

/* Update the strip's scene preview range to match the strip (addon setting). */
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

/* Extend the strip's scene frame range to cover the strip (addon setting). */
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
    {GZ_PART_LEFT, "LEFT", 0, "Left Handle", "Adjust the strip's start frame"},
    {GZ_PART_RIGHT, "RIGHT", 0, "Right Handle", "Adjust the strip's end frame"},
    {GZ_PART_MOVE, "MOVE", 0, "Move", "Move the strip in the timeline"},
    {GZ_PART_SLIP, "SLIP", 0, "Slip", "Slip the strip's content"},
    {0, nullptr, 0, nullptr, nullptr},
};

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
      adjust_shot_duration_left(master_scene, strip, -offset - delta);
      break;
    case GZ_PART_RIGHT:
      delta = duration - data->orig_duration;
      adjust_shot_duration_right(master_scene, strip, offset - delta);
      break;
    case GZ_PART_MOVE:
      delta = int(strip->start) - int(data->orig_start);
      move_shot(master_scene, strip, offset - delta);
      break;
    case GZ_PART_SLIP:
      delta = int(strip->startofs) - int(data->orig_startofs);
      slip_shot_content(master_scene, strip, offset - delta);
      break;
  }

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
  strip->scene->r.efra = max_ii(remap_frame_value(strip, frame_end), data->orig_scene_efra);

  /* Range sync per the 3D Sequencer addon settings (built-in defaults when the
   * addon is disabled). */
  if (timeline_sync_bool_get(C, "use_preview_range")) {
    update_preview_range(master_scene, strip);
  }
  if (timeline_sync_bool_get(C, "use_scene_range")) {
    update_scene_frame_range(master_scene, strip);
  }

  WM_event_add_notifier(C, NC_SCENE | ND_SEQUENCER, master_scene);
  WM_event_add_notifier(C, NC_SCENE | ND_FRAME, master_scene);
  ED_region_tag_redraw(CTX_wm_region(C));
}

static void scene_strip_timing_ui_cleanup(bContext *C, wmOperator *op)
{
  ED_area_status_text(CTX_wm_area(C), nullptr);
  WM_cursor_modal_restore(CTX_wm_window(C));
  MEM_delete(static_cast<SceneStripTimingOp *>(op->customdata));
  op->customdata = nullptr;
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
  SNPRINTF(header_text, "Offset: %d", data->offset);
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
        scene_strip_timing_ui_cleanup(C, op);
        return OPERATOR_FINISHED;
      }
      break;
    case EVT_RETKEY:
    case EVT_PADENTER:
      if (event->val == KM_PRESS) {
        scene_strip_timing_ui_cleanup(C, op);
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
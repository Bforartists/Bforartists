/* SPDX-FileCopyrightText: 2009 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup editors
 */

#pragma once

#include "BLI_vector_set.hh"

namespace blender {

struct Scene;
struct Strip;
struct SpaceSeq;
struct bContext;
struct View2D;
struct wmEvent;

namespace ed::vse {

enum eStripHandle {
  STRIP_HANDLE_NONE,
  STRIP_HANDLE_LEFT,
  STRIP_HANDLE_RIGHT,
};

struct StripSelection {
  /** Closest strip in the selection to the mouse cursor. */
  Strip *strip1 = nullptr;
  /** Farthest strip in the selection from the mouse cursor. */
  Strip *strip2 = nullptr;
  /** Handle of `strip1`. */
  eStripHandle handle = STRIP_HANDLE_NONE;
};

void select_strip_single(Scene *scene, Strip *strip, bool deselect_all);
/**
 * Iterates over a scene's strips and deselects all of them.
 *
 * \param scene: scene containing strips to be deselected.
 * \return true if any strips were deselected; false otherwise.
 */
bool deselect_all_strips(const Scene *scene);

bool maskedit_mask_poll(bContext *C);
bool check_show_maskedit(SpaceSeq *sseq, Scene *scene);
bool maskedit_poll(bContext *C);

/**
 * Are we displaying the seq output (not channels or histogram).
 */
bool check_show_imbuf(const SpaceSeq &sseq);

bool check_show_strip(const SpaceSeq &sseq);
/**
 * Check if there is animation shown during playback.
 *
 * - Colors of color strips are displayed on the strip itself.
 * - Backdrop is drawn.
 */
bool has_playback_animation(const Scene *scene);

void ED_operatormacros_sequencer();

Strip *special_preview_get();
void special_preview_set(bContext *C, const int mval[2]);
void special_preview_clear();
/**
 * Returns collection with selected strips presented to user. If operation is done in preview,
 * collection is limited to selected presented strips, that can produce image output at current
 * frame.
 *
 * \param C: context
 * \return collection of strips (`Strip`)
 */
VectorSet<Strip *> selected_strips_from_context(bContext *C);
StripSelection pick_strip_and_handle(const struct Scene *scene,
                                     const View2D *v2d,
                                     float mouse_co[2]);
bool can_select_handle(const Scene *scene, const Strip *strip);
bool handle_is_selected(const Strip *strip, eStripHandle handle);

bool is_scene_time_sync_needed(const bContext &C);
/**
 * Returns the scene strip (if any) that should be used for the scene synchronization feature.
 * This is the top-most visible scene strip at the current time of the \a sequencer_scene.
 */
const Strip *get_scene_strip_for_time_sync(const Scene *sequencer_scene);
void sync_active_scene_and_time_with_scene_strip(bContext &C);

/* BFA (#6780): deferred timeline switching during dopesheet playhead scrubs.
 * While a dopesheet scrub is held down, the sync seam records the would-be
 * switch target instead of switching scenes live; the ghost highlight reads
 * the target and the mouse release applies it. */
void sync_scene_strip_scrub_begin(bContext &C, const wmEvent *event);
void sync_scene_strip_scrub_end(bContext &C);
void sync_scene_strip_scrub_cancel();
/**
 * Returns the recorded switch target while a dopesheet scrub is deferred, or
 * null when nothing is pending. \a r_master_scene gets the sequencer (master)
 * scene, \a r_master_frame the master playhead frame the target was recorded
 * at, and \a r_is_master_fallback is true when the target is the master
 * timeline itself (no scene strip under the playhead).
 */
const Strip *sync_scene_strip_scrub_target_get(const bContext &C,
                                               Scene **r_master_scene,
                                               int *r_master_frame,
                                               bool *r_is_master_fallback,
                                               const Strip **r_drag_strip);

}  // namespace ed::vse
}  // namespace blender

# #6780 — Playhead: deferred timeline switching (ghost highlight)

## Problem

With sync on, scrubbing the dopesheet playhead switches the active timeline
**live**:

1. **Master fallback oscillation.** When the active scene is the master
   (pinned/empty lane fallback) and the playhead leaves a scene strip's range,
   the forward sync rewrites the master playhead from the strip mapping, the
   reverse sync then maps the shot playhead back, and the two fight — the
   playhead jumps between the strip range and the master range back and forth
   while scrolling on an empty lane.
2. **Unpredictable strip swapping.** Scrubbing past the current strip's edge
   instantly switches the dopesheet to whichever scene strip is now under the
   master playhead (different scene, different range, different gizmos). The
   full-sequencer bidirectional flow from the dopesheet feels jarring and
   unpredictable.

## UX decision (user-confirmed)

Top-level full-sequence control belongs in the **sequencer**, not the
dopesheet. Within the dopesheet, the playhead stays **unclamped and
bidirectional inside the current timeline's range**, but must **not switch
timelines while the mouse is held down**:

1. Select and drag the playhead in the current dopesheet timeline.
2. Going beyond the timeline's range **never switches timelines while
   pressed** — the playhead follows the mouse unclamped (keeping the §5.7
   linear, non-bouncing behavior).
3. If the playhead would land on the master scene (empty lane fallback) or on
   another scene strip, that target timeline is shown as a **ghost highlight**
   on the dopesheet.
4. **On release**, the switch to the target timeline happens.

## Root cause (verified in code)

- `change_frame_apply()` (anim_ops.cc) calls
  `sync_active_scene_and_time_with_scene_strip()` on **every** mouse move.
- The forward path (`sequencer_edit.cc:468`) switches the window's active
  scene whenever the master playhead is over a different scene strip, and — in
  master-fallback mode (active scene == sequencer scene) — rewrites
  `sequencer_scene->r.cfra` from the strip mapping, which is the oscillation
  source.
- The reverse path (§5.7) is correct and stays.

## Fix design

**A new scrub-defer state lives next to the sync seam**
(`sequencer_edit.cc`, exported via `ED_sequencer.hh`):

- `sync_scene_strip_scrub_begin(bContext &C, const wmEvent *event)` — invoke:
  remembers `is_deferred = true`, the scene the drag **started** in, and a
  recorded `target` (scene + master frame), initialized to "no switch".
- `sync_scene_strip_scrub_end(bContext &C)` — release: `is_deferred = false`,
  then, if a `target` was recorded, **switch to it now**: `WM_window_set_active_scene`
  when the target scene differs, and re-apply the forward sync so the shot
  playhead derives from the target strip.
- `sync_scene_strip_scrub_cancel()` — Esc/cancel: `is_deferred = false`, drop
  the recorded target.
- `sync_scene_strip_scrub_target_get()` — read access for the draw callback
  (ghost highlight): returns the recorded target or `nullptr`.

In `sync_active_scene_and_time_with_scene_strip()`:

- **Forward path while deferred:** keep mapping the master playhead to the
  shot time **only when the master playhead stays inside the strip the drag
  started in** (no scene switch, no master cfra rewrite in fallback mode).
  The moment the playhead leaves that strip's coverage (or finds no strip),
  do not apply — instead **record the switch target**: the top-most scene
  strip at that master frame (or "master scene" when none), plus the master
  frame. Draw code uses the recorded target; release applies it.
- **Reverse path while deferred:** unchanged — shot playhead still drives the
  master playhead (that is the in-range bidirectional flow). The target
  recording above wins if both sides moved, since the release applies the
  target.

In the dopesheet scrub operator (`anim_ops.cc`, `ANIM_OT_change_frame` —
SPACE_ACTION only):

- `change_frame_invoke` → `sync_scene_strip_scrub_begin()` before the first
  apply.
- Modal `MOUSEMOVE`/apply → untouched (deferral happens inside the seam).
- Release (`OPERATOR_FINISHED` path) → `sync_scene_strip_scrub_end()` after
  scrubbing state is restored. Esc → `sync_scene_strip_scrub_cancel()`.
- Only for the dopesheet: the sequencer's own playhead operator keeps the
  live behavior (there the switching is the feature).

## Ghost highlight (the "where will I land" preview)

New `ANIM_draw_scene_strip_scrub_target(const bContext *C, View2D *v2d)`
(animation/anim_draw.cc, declared in `ED_anim_api.hh`, drawn from
`space_action.cc` right after `ANIM_draw_scene_strip_range`):

- Active only while a dopesheet scrub is deferred **and** a target was
  recorded (`sync_scene_strip_scrub_target_get()`), and the target differs
  from the current timeline.
- **Different scene strip target:** tint the dopesheet background with a
  translucent highlight between the target strip's mapped start/end (same
  mapping as `ANIM_draw_scene_strip_range`: `give_frame_index(...) +
  sfra + anim_startofs`), i.e. a "ghost" of the range the playhead will land
  in, plus a vertical center line.
- **Master (fallback) target:** a full-width translucent tint — "release to
  switch to the full master timeline".
- Color: re-use the scene-strip-range theme color (`TH_ANIM_SCENE_STRIP_RANGE`)
  with a stronger alpha so it reads distinctly against the grey out-of-range
  shading.

## Sequencer playhead in the dopesheet

Unchanged: the playhead can go before/behind the scene range (unclamped,
§5.7 linear follow), it just no longer drags a timeline switch with it while
pressed.

## Test plan

1. Sync on, master pinned. Dopesheet on a scene strip: drag playhead left
   past the strip edge — no switch while pressed; ghost tint of the next
   strip / master appears past the edge; release lands in that timeline.
2. Master (fallback) timeline: scrub the playhead across the empty lane — no
   oscillation while pressed; the playhead follows the mouse linearly.
3. Esc during the drag: playhead restores (existing scrub cancel), no switch.
4. Scrub inside the strip range: bidirectional sync behaves exactly as
   before (no deferral visible).
5. Sequencer scrubbing is unaffected (live switching retained).

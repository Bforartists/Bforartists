# 6780 — Strip-mover gizmo: vertical channel drag

**Status:** LANDED — cherry-picked as `255aabf3a44` on
`6780-3d-sequencer---fix-timeline-gizmos-to-retime-shots` (worktree + temp branch
cleaned up). Awaiting build + test checklist below.
**Scope:** one file — `source/blender/editors/space_action/action_gizmo_scene_strip.cc`.

## Feature

While dragging the **bottom middle bar** (`GZ_PART_SLIP` — the strip mover), vertical
mouse motion moves the strip **between sequencer channels**: dragging up steps to
higher channels, dragging down to lower ones (one bar-height = one channel step).
Horizontal motion keeps driving the timeline position exactly as today. The green/red
handles and the top bar (range window) keep channels locked.

## Verified mechanics

- `Strip::channel_set(int)` (`strip_time.cc:630`) clamps 1..`MAX_CHANNELS` — no extra bounds code.
- The modal handler already receives `event->mval[1]` on every `MOUSEMOVE`.
- The SLIP release path already calls `resolve_move_overlap()`; overlap is
  channel-based, so a channel-jump collision settles via the sequencer's overlap
  mode (expand/shuffle/overwrite) exactly like a VSE grab release.
- Live overlap feedback idiom (set/clear `StripRuntimeFlag::Overlap` via
  `transform_test_overlap`) already exists in the SLIP apply branch.
- File is CRLF; Python is NOT installed on this machine — apply edits with Perl.
- Cursor constants live in `wm_cursors.hh` (`WM_CURSOR_MOVE`, `WM_CURSOR_X_MOVE`).

## Changes

1. **`SceneStripTimingOp` struct**: add `int start_view_y;` (vertical drag baseline)
   and `int orig_channel;` (snapshot for exact cancel), next to `start_view_x`/`offset`.
2. **Invoke, strip branch**: `data->orig_channel = strip->channel;`
3. **Invoke, no-strip fallback branch**: init `start_view_y = 0; orig_channel = 0;`
   (never read in that mode — keeps the servo dead there).
4. **Invoke**: capture `data->start_view_y = event->mval[1];` next to `start_view_x`.
5. **Invoke, cursor**: `data->mode == GZ_PART_SLIP ? WM_CURSOR_MOVE : WM_CURSOR_X_MOVE`
   (the strip mover now drags in both axes).
6. **Modal `MOUSEMOVE`** (after the horizontal apply, before `break`): when mode is
   SLIP and `strip != nullptr`:
   - `channel = orig_channel − (mval[1] − start_view_y) / (26·UI_SCALE_FAC)`
     (screen Y grows downward → invert so dragging up = higher channels);
   - on change: `channel_set(channel)`, set/clear the `Overlap` runtime flag via
     `transform_test_overlap` (same idiom as the horizontal move), notify
     `NC_SCENE | ND_SEQUENCER`, `ED_region_tag_redraw`.
   - Release keeps resolving via the existing `resolve_move_overlap()` — no change.
7. **Cancel (Esc/right-click)**: `strip->channel = data->orig_channel;` alongside the
   other snapshot restores — exact cancel of both axes.
8. **Tooltip** for SLIP: append "Vertical motion steps the strip between sequencer channels".

## Process

1. `git worktree add ../bfa-6780-channel-drag -b 6780-strip-mover-channel-drag`
2. Apply the edits there (Perl one-shot with per-anchor uniqueness assertions).
3. Read back each edited region to verify.
4. Commit the source file only in the worktree (`_misc/` stays untracked).
5. Build `bf::editor_space_action` (user side — no build dir in this checkout), then
   merge/cherry-pick `6780-strip-mover-channel-drag`.

## Test checklist (after build)

- Drag bottom bar up/down → strip hops channels in the VSE; red overlap outline when
  landing on a neighbor; release resolves with the sequencer overlap mode.
- Esc mid-drag → strip returns to its original channel AND frame position exactly.
- Green/red handles + top bar → channels never change (regression).
- No-strip fallback mode → unaffected.
- Clamp-to-scene-strip on → horizontal clamp/lockstep behavior unchanged by vertical motion.

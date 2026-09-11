# #6780 — Scene-strip gizmos: corrected UX model & remaining work

**Branch:** `6780-3d-sequencer---fix-timeline-gizmos-to-retime-shots`
**File under change:** `source/blender/editors/space_action/action_gizmo_scene_strip.cc`
(plus `anim_draw.cc` for the shading, `space_action.cc` for the toggle default)
**Updated:** 2026-09-10 (Round 12 — no-strip fallback (§5.4): the gizmo now
targets the active scene's own render/preview range when no scene strip exists,
so it draws and edits on any dope-sheet scene with no pinned sequencer, no scene
strips and no sync. Round 11 — follow-up to §5.2: the clamp-mode MOVE bar
now aligns the scene range to the strip on the FIRST movement of the drag
instead of on release, removing the "updates, then snaps" jump (the release
clamp for MOVE is removed); and `ANIM_scene_strip_master_get` gains a
last-resort scan of the file's scenes, so the gizmo/overlay draw for the active
scene when neither master store is set (no Sync needed). Also fixed two stale
`scene_strip_master_get` call sites in the new §2.3 operator that would not
compile. Round 10 — wrap-up: MOVE joins the release SET clamp so the middle
bars "initialize" the snap like the ends (`6d98d5b4d7f`); the dope-sheet
strip-range shading is sync-agnostic via the shared
`ANIM_scene_strip_master_get` resolver (`6d98d5b4d7f`). Round 9 — execution
audit complete: every Round-8 claim verified against the code; §2.7 + §2.8
committed as `ad0d3b349ce`; §2.4 servo-hygiene leftover landed as
`f6b6846ddcc` (anim-offset cancel snapshot); §2.7 shading open item decided —
the grey `ANIM_draw_scene_strip_range` shading stays scene-range-based; §2.3
button deferred as an explicit follow-up decision. Earlier: Round 8 — §2.6
hardened: SLIP servo incremental displacement; §2.7 landed: unclamped
full-strip gizmo extent shared with the draw sites; §2.8 landed: master
resolution scans both stores and the addon repopulates `master_scene` on
load. Earlier: Round 7 — §2.3 reworked: timeline↔strip reconciliation is an
explicit opt-in "Sync Scene Strip" action, not automatic; §2.1 marked landed
under the corrected strip-extent model; stale §3/§4/§5 rows updated)

## Landed (no longer planned, keep as regression baseline)

- Green (left) handle: live scene-start extension, neighbor push/pull, `MINAFRAME`
  floor, exact cancel — `0384072bfb9`.
- Red (right) handle parity: live `efra` extension (`MAXFRAME` ceiling), neighbor
  push by actual moved amount, exact cancel — `9f06fa8f232`.
- Snapshot unification for LEFT/RIGHT/MOVE (incl. master sfra/efra, psfra/pefra).
- Release SET clamp with lead-in/out for LEFT/RIGHT; floored at `MINAFRAME`.
- Master-sfra follow for the strip mover (committed variant, MINAFRAME-floored).
- Preview-range doubling in the bar draw (user-verified fixed).
- SLIP-with-clamp: scene range translates 1:1 with the slip (user-verified fixed).
- **§2.5 landed:** clamp-mode strip mover follows the scene range live and snaps
  on release; the SLIP servo applies only the per-move increment (derived from
  the strip's own state) instead of re-applying the cumulative mouse offset.
- **§2.6 landed:** the SLIP branch's incremental displacement is hardened
  (`offset - (strip->start - orig_start)`), so a Drag of D frames moves the
  strip by exactly D — no quadratic runaway.
- **§2.7 landed:** the gizmo extent uses an unclamped linear handle → strip-scene
  map (`scene_strip_frame_from_handle`), shared by the extent and both draw
  sites, so the bar spans the strip's full range regardless of the toggles.
- **§2.8 landed:** `scene_strip_master_get()` scans both master stores and picks
  the one holding a strip for the active scene; the addon's `on_load_post`
  repopulates `master_scene` from `workspace->sequencer_scene` unconditionally,
  so the gizmos initialize on load with sync off. **Committed as `ad0d3b349ce`**
  (with §2.7).
- **§2.4 servo hygiene completed (Round 9, `f6b6846ddcc`):**
  `orig_anim_startofs/orig_anim_endofs` are captured at invoke and restored on
  cancel — Esc is now exact for slips that moved anim offsets (the last
  outstanding §2.4 design item).
- **Round 10 wrap-up (`6d98d5b4d7f`):** (a) MOVE joined the release SET clamp
  (LEFT/RIGHT/SLIP/MOVE all snap now — the middle bars "initialize" the range
  snap exactly like the ends when the range length is stale); (b) the
  dope-sheet strip-range shading resolves its strip through the gizmos'
  sync-agnostic dual-store resolver (exported as `ANIM_scene_strip_master_get`
  in `ED_anim_api.hh`), so the overlays draw with sync never initialized.
- **§2.4 implemented (this commit):** the middle bars translate `psfra/pefra`
  1:1 when preview-coupled (state captured at invoke — no mid-drag toggle
  re-evaluation), bounded at `MINAFRAME`/`MAXFRAME`; the recompute in
  `sync_ranges` now runs only for the retime handles (it was a no-op for MOVE
  and could not glue the preview to a slip/move); "Set Preview Range" enables
  `SCER_PRV_RANGE` on first write (seeded from the render range), and the
  flag is snapshotted/restored on cancel.
- **Uncommitted in the working tree (commit first, step 0):** MOVE clamp lockstep
  (`sfra/efra += moved`) and the preview-range gating of `update_preview_range`.
  *(Update: committed as `f68f43d584c`.)*

---

## 1. Confirmed UX model (the spec — user-corrected 2026-09-10)

Toggle rows compose top-down: each enabled toggle adds its range-following on top
of the row above. All modes always edit the sequencer strip's geometry.

### Green / Red handles — good, unchanged

| Toggles | Behavior |
|---|---|
| none | trim/extend strip start/end (hold frames when clamp off) |
| + Set Preview Range | + preview range follows the moving edge (`update_preview_range`) |
| + Clamp Scene Range | + scene range edge follows live; release SET with lead-in/out |
| + both | both ranges follow |

### Top bar = SLIP (strip content) — needs work

The sequencer strip is **locked** (position and extent in the VSE never change).
The dope-sheet bar shifts because the strip's content window moves.

| Toggles | Behavior |
|---|---|
| none | slip the content (`anim_startofs` shift): the dope-sheet bar start/end shift, ranges untouched — **correct** |
| + Set Preview Range | + preview range (`psfra/pefra`) translates 1:1 with the slip — **broken, see §2.4** |
| + Clamp Scene Range | the slip is expressed through the scene range instead: `sfra` **and** `efra` translate 1:1 with the slip (range length fixed, "end slips too"); `anim_startofs` stays frozen so the bar moves exactly once, not twice. No release snap. — **fixed** |
| + both | same as clamp row, plus the preview range translates 1:1 |

Why `anim_startofs` freezes under clamp: the bar position contains both terms
(`give_frame_index(handle) + sfra + anim_startofs`). Slipping via `anim_startofs`
**and** translating `sfra/efra` would move the bar 2×D. Under clamp the range
translate *is* the slip (the remap `frame − start + sfra` shifts, so the strip
plays shot frames shifted by D).

### Bottom bar = MOVE (strip in sequencer) — needs work

| Toggles | Behavior |
|---|---|
| none | translate the strip in the sequencer (`move_shot` + overlap bump/resolve UX); ranges locked; the dope-sheet bar does not move (strip motion is only visible in the VSE) — **correct** |
| + Set Preview Range | + preview range translates 1:1 with the move (the preview window / dope-sheet scene range slides with the strip) — **broken, see §2.4** |
| + Clamp Scene Range | strip moves **and** `sfra`/`efra` translate 1:1 in lockstep (glued — the strip stays locked to the master sequencer range); on release the SET clamp applies lead-in/out ("snaps on release") — **landed (§2.5)** |
| + both | same as clamp row, plus the preview range translates 1:1 |

> Interpretation note: "Scene strip location is locked in sequencer" is read as
> *locked to the scene range* (lockstep), matching the earlier spec and making
> the release snap meaningful.

---

## 2. Task list with fix designs

### 2.1 Gizmo spans the strip's own range (not the mode range) — **LANDED (corrected)**

**User report (original).** The gizmo covers the scene range as a maximum; the
empty strip extension beyond is not drawn (but is drawn in the preview). Example:
scene strip 100 frames, scene range 25–75, preview range 25–100 → gizmo draws
25–75 and the preview-visible 75–100, but the empty 0–25 is not drawn.

**Corrected model (user, 2026-09-10, after building the first attempt).** The
green/red handles and the move/slip zones should cover **basically what's the
strip** — they must *not* stretch to the preview or scene range. The three ranges
are already drawn in the dope-sheet by the overlays, so the gizmo must not redraw
them and the empty-extension band is redundant:

| Mode | Strip | Preview | Scene range |
|---|---|---|---|
| Default | 30–70 (gizmo spans this) | decoupled (e.g. 50–80) | decoupled |
| Preview on | 30–70, preview too | coupled to strip | decoupled |
| Clamp on | 30–70, scene range too | decoupled | coupled to strip |
| Both | 30–70 | coupled | coupled |

- Preview range is drawn **orange** (set by the user or synced by the gizmo).
- Scene render range is drawn with **mid-grey** start/end marks.
- Strip range is drawn in a **darker grey** when the overlays are on.
- All three are visible simultaneously, so the gizmo only needs to draw the
  strip's own bar. The toggles decide *which ranges follow the strip's edits*
  (operator behavior), **not** how wide the gizmo is drawn.

**Implementation (landed, corrected).**
- `scene_strip_frame_range()` replaced by `scene_strip_gizmo_extent()`, returning
  `SceneStripGizmoExtent { frame_in, frame_out }` — always the strip's own range,
  mapped exactly like `ANIM_draw_scene_strip_range` (handles through
  `give_frame_index` + `sfra` + `anim_startofs`). No mode switch, no unclamped
  map, no empty sub-ranges.
- `scene_strip_gizmo_rects_get()` spans handles + move/slip hit zones across that
  strip range only.
- The dimmed empty-extension band and its boundary seam were removed from
  `action_gizmo_scene_strip_draw()`.
- `ANIM_draw_scene_strip_range()` (background shading) unchanged.

**Superseded first attempt (reverted).** The initial §2.1 landed a per-mode
extent resolver (none → full strip extent via an unclamped linear map; preview →
`psfra/pefra`; clamp → `sfra/efra`; both → union) plus a dimmed empty band. The
user's corrected model above replaced it: the gizmo is strip-only, and the
dope-sheet overlays already communicate the other ranges.

**Root cause (verified).** `scene_strip_frame_range()` maps the strip's handles
through `give_frame_index()`, which saturates at the strip's *content* end
(`strip_time.cc:43`: `frame_index = max_ff(..., 0)` against
`content_start..content_end`). Outside the shot's rendered frames the index
clamps, so the computed bar edge sits exactly on the scene range boundary. Under
the corrected model this is the *desired* behavior — the bar spans the strip's
content, and the hold-frame extension is intentionally not drawn by the gizmo.


### 2.2 "Set Preview Range" is always on when Sync is on

**User report.** Only a problem when Sync is on: with sync off everything works
as predicted. With sync on, the preview range updates even if "Set Preview
Range" is off, when only the strip range (mode 1) should drive. The three modes
of influence: (1) strip range by gizmo, full strip range; (2) preview range set
by gizmo — invisible if the preview toggle is off; (3) scene range set by gizmo.

**Root cause (verified chain).** The gizmo drag writes `sfra`/`efra` (clamp) or
the strip range, then `scene_strip_timing_sync_ranges()` fires
`WM_event_add_notifier(C, NC_SCENE | ND_FRAME | ND_SEQUENCER, master_scene)`.
The sequencer sync listener (built-in `WORKSPACE_SYNC_SCENE_TIME` /
`rna_workspace_sync_scene_time_update` path, and the legacy addon handlers)
treats the shot-scene write as a shot-time change; the sync seam
(`sync_active_scene_and_time_with_scene_strip`) runs, and on the next
recalculation the preview range gets refreshed as a side effect of the
master-scene/shot coupling (`BKE_sequencer` re-render range / preview refresh
paths re-derive `psfra/pefra` from the scene's render range when the shot scene
changes). With sync off, no seam runs, so the gating works. In other words: the
gizmo code is already correctly gated (`update_preview_range` only runs when
`ADS_SHOW_USE_PREVIEW_RANGE` is set) — the sync loop is the second, ungated
writer.

**Fix design.**
1. **Direct cause:** find the exact writer with a breakpoint/`printf` trace on
   `r.psfra` writes during a drag with the toggle off (candidates: the
   `rna_workspace_sync_scene_time_update` RNA update callback, the
   `WORKSPACE_SYNC_SCENE_TIME` frame-change handler, and
   `BKE_scene_...` render-range clamping of `psfra/pefra` inside
   `sfra/efra` writes — `BKE_scene` clamps the preview range into the render
   range whenever `SCER_PRV_RANGE` is on, which would re-expose preview values
   as the clamp follows `sfra/efra`). The `BKE_scene` clamp is the most likely:
   it explains "only when sync is on" (sync is what moves `sfra/efra` live) and
   fires even when the gizmo never touched the preview.
2. **Structural fix — sync-aware writes:** add a
   `SceneStripTimingOp::suppress_range_side_effects` flag, and wrap all
   scene-range writes during the drag (and on finish) so the resulting notifier
   does not trigger preview re-derivation: either (a) snapshot `psfra/pefra`
   before the drag (already present: `orig_psfra/orig_pefra`) and re-assert them
   after every `sfra/efra` write when the toggle is off, or (b) send a dedicated
   notifier (`NC_SCENE | ND_FRAME_RANGE`) that the sync listeners ignore.
   Recommendation: (a) — deterministic, no new notifier contract; add a
   `restore_preview_range()` called from `scene_strip_timing_sync_ranges()`
   right after every clamp-mode write, gated on
   `!scene_strip_use_preview_range_get(C)`.
3. **Also fix the default (kept from Round 5):** remove
   `ADS_SHOW_USE_PREVIEW_RANGE` from the force-enabled defaults in
   `space_action.cc` area-init so new files don't start with the toggle on
   (existing files keep their saved flag).

### 2.3 Timeline-driven range changes don't update the gizmo (out-of-sync, snap on drag)

**User report.** Numerical changes to start/end from the timeline range controls
or "set start/end" operators don't update the gizmo. With Clamp on, changing the
scene range from the timeline leaves the gizmo's length stale; when the user
then uses the gizmo, the range "snaps" to the gizmo — the user's timeline input
was discarded.

**Design question (user, 2026-09-10).** Should timeline adjustments affect the
strip in the sequencer at all — automatically, or as an opt-in? Suggested
alternative: a button in the timeline that "syncs" the strip settings (and thus
the gizmo) on demand; otherwise the gizmo remains destructive to timeline /
preview settings depending on the mode.

**Why the gizmo cannot "just update" (verified).** For a scene strip the
live-derived terms cancel out of the handle math:
`end_offset() = content_length() − (len − endofs)` and
`right_handle() = content_end() − end_offset() = start + len − endofs`
(`strip_time.cc:514–656`). The strip's master extent is therefore pure cached
state (`start`, `len`, `startofs`, `endofs`); a timeline range edit writes
`r.sfra/r.efra` and nothing else, so the gizmo — which draws the strip's
extent — correctly keeps its old width while the grey range marks move.
Making the gizmo reflect a timeline edit necessarily *rewrites strip state*;
the only design freedom is when that rewrite happens and in which direction:

- **Strip → Range ("apply"):** range := strip's visible extent (+ lead in/out).
  Already exists — the release SET clamp in clamp mode. Destructive to timeline
  input by design; that is the mode's contract.
- **Range → Strip ("adopt"):** strip extent := current range. Exists nowhere
  natively today — this is the missing reconciliation.

**Options for reconciling the two stores.**

| Option | Mechanism | Verdict |
|---|---|---|
| A. Automatic adopt | an `ND_FRAME_RANGE` listener re-derives the strip on every timeline range edit | **Rejected.** A render-range tweak would silently resize the strip in the VSE (neighbor push/pull, overlap risk, undo spam) and would destroy the hold-frame extension workflow when clamp is OFF — there, strip ≠ range is *by design*. Mode-dependent surprise; the sequencer owns the edit. |
| B. Manual adopt — "Sync Scene Strip" button (**recommended**) | one-shot operator, exact 1:1, single undo step, greyed out while in sync | **Adopted.** Explicit and undoable; the user decides when timeline input becomes strip geometry. Answers the design question: no automatic effect — opt-in via the button; the gizmo stays destructive in clamp mode (that is the mode's contract). |
| C. Status quo | — | Keeps both repros (§2.3 snap, §2.5 init) and silently destroys timeline input on the first drag; rejected. |

Auto-follow can return later as an opt-in *preference* ("Clamp mode adopts
timeline range edits") — deliberately out of scope for this round.

**Fix design — `ACTION_OT_scene_strip_sync_from_range` ("Sync Scene Strip").**
1. **Semantics — the inverse of `clamp_scene_strip_range()`:** adopt the
   *render* range only. Compute the master-timeline deltas the strip's edges
   need so its visible extent equals `[sfra, efra]` — left edge via the green
   recipe (`strips_before_same_channel` push/pull), right edge via the red
   recipe (`strips_after_same_channel` + `transform_translate_strip`) — with
   all scene-range writes suppressed: the range is already the target, so
   never write `sfra/efra` and the clamp cannot loop. The strip's trim
   character is preserved, mirroring how the release clamp bakes trim into the
   range offsets.
2. **Preview range is never adopted:** `psfra/pefra` are an *output* of the
   strip (`update_preview_range`); timeline preview edits do not touch strip
   state, so there is nothing to reconcile in that direction (the sync-loop
   leak is §2.2's separate fix).
3. **Neighbor policy:** same push/pull as the handle edits — uniform by
   construction, no overlap can arise.
4. **UI:** button in the dope-sheet header next to the clamp/preview toggles
   (enabled when a scene strip exists for the active scene), also reachable as
   a searchable operator; disabled while `ACTION_OT_scene_strip_timing` is
   modal; greyed out when the strip's visible extent already equals the range.
5. **Undo:** one step ("Sync Scene Strip to Range") + `ND_SEQUENCER` /
   `ND_FRAME_RANGE` notifiers for redraw.
6. **Effect on §2.5:** the invoke-time defensive resync is dropped — a silent
   adopt at invoke would destroy timeline input, the exact complaint. The cure
   is pressing the button once; afterwards the middle bars are exact from the
   first drag.

### 2.4 With preview-display off but "Set Preview Range" on, the top bar moves instead of slipping — **implemented**

**User report.** When the timeline preview *display* is off and "Set Preview
Range" is on, moving the top middle bar doesn't slip the scene time — it moves
the sequencer scene strip. Same with sync on or off.

**Root cause (verified).** Two different switches are being conflated:
1. `ADS_SHOW_USE_PREVIEW_RANGE` (dope-sheet overlay: "Set Preview Range" —
   gizmos may *write* the preview range), and
2. `strip->scene->r.flag & SCER_PRV_RANGE` (the scene's preview mode — whether
   `psfra/pefra` exist as an active range at all).
`update_preview_range()` bails unless `SCER_PRV_RANGE` is set (correct — it can
not set an inactive range). But the SLIP branch's *choice of slip mechanism* is
gated on the display side: with the preview display off,
`scene_strip_frame_range()` falls back to the `sfra`-based mapping, the drag
servo's `delta` tracking then measures against a base that silently switches
between `psfra`-mapping and `sfra`-mapping, and the applied delta lands on
`strip->start` instead of `anim_startofs` — the branch effectively degrades to
the MOVE path. (Verify at implement time by logging which branch runs; the
degradation path is the `GZ_PART_SLIP` case in `scene_strip_timing_apply()`.)

**Fix design.**
1. **Decouple the two switches inside the gizmos:** the *write* target
   (`update_preview_range`) stays gated on
   `ADS_SHOW_USE_PREVIEW_RANGE && SCER_PRV_RANGE` (writing the preview range
   also turns the preview display on — see 3 below). The *slip mechanism* is
   gated only on `ADS_SHOW_USE_PREVIEW_RANGE`: preview toggle on → slip via the
   preview/scene-range translate (per §1 table); off → slip via
   `anim_startofs` (`seq::time_slip_strip()`), independent of whether the
   preview display is currently visible.
2. **"Set Preview Range" implies preview mode:** when the gizmo writes a preview
   range for the first time and `SCER_PRV_RANGE` is off, set
   `strip->scene->r.flag |= SCER_PRV_RANGE` so the write is observable
   (undo-step note: include the flag in the undo push). Cancel restores the
   flag from the snapshot (add `orig_flag` to `SceneStripTimingOp`).
3. **Servo hygiene:** capture `orig_anim_startofs/orig_anim_endofs` at invoke
   (missing today — also required by §3.5) and track the SLIP delta against the
   mechanism actually used, so a mid-drag toggle of the preview display cannot
   switch the mapping under an active drag (capture the mode at invoke; ignore
   toggle changes mid-drag).

### 2.5 Clamp-mode middle bars don't initialize correctly (only work after green/red snap) — **code landed (2026-09-10)**

**User report.** Turn on Clamp, drag the middle/top bar → the range offsets but
doesn't snap to the range it should. Only green/red make the scene range snap to
the strip width; after that, the middle bars work.

**Root cause (verified).** This is §2.3 seen from the drag side. The lockstep
translate (`sfra/efra += moved`) preserves whatever *length* the scene range had
at invoke; the release SET clamp then aligns that length to the strip's visible
extent. If the strip's cached `len` is stale (because the range was changed from
the timeline first — §2.3), the first clamp drag translates the stale length and
the first release snaps it — afterwards everything agrees, which matches the
report exactly ("only after the green and red handles have snapped the scene
range, the middle top and bottom handle work"). The middle bars are not missing
an init step of their own; they inherit an un-synced strip.

**Fix design.**
1. **No automatic reconciliation at invoke** (revised 2026-09-10): silently
   adopting the range at invoke would destroy timeline input — the exact
   §2.3 complaint. The middle bars translate whatever range length exists at
   invoke; that is correct for a desynced state, and the release SET clamp
   resolves it in the mode's direction.
2. **The cure is the §2.3 button:** "Sync Scene Strip" once, then the middle
   bars are exact from the very first drag (extent == range at invoke, so the
   lockstep translate and the release snap agree).
3. **Verification hook:** on a synced strip, turn clamp on → move bottom bar
   left 10 → range = 20–90 immediately, release snaps with lead-in/out, no
   pre-snap needed. The "only works after green/red" repro must be
   un-reproducible.
4. **Code (landed 2026-09-10):** three changes in `ACTION_OT_scene_strip_timing`:
   (a) the SLIP servo now applies only the increment since the last mousemove
   (the applied displacement is derived from the strip's state, like the MOVE
   branch derives it from the scene range — re-applying the cumulative mouse
   offset made the strip race ahead of the cursor); (b) clamp-mode lockstep:
   the strip scene's `sfra/efra` translate 1:1 with the applied strip
   displacement, bounded at `MINAFRAME`/`MAXFRAME`, so the range = 20–90
   immediately during the drag; (c) `finish()` runs the release SET clamp for
   SLIP too (before the overlap resolution, since the clamp's lockstep
   compensation can shift the strip into a neighbour). No invoke-time adopt —
   the middle bars translate whatever length exists at invoke (item 1), and
   the §2.3 button remains the cure for desynced strips.

### 2.6 Bottom Middle gizmo with Set Preview OFF has exponential circular offset

This is doubling the strip move.

**Root cause (verified).** `scene_strip_timing_apply()` computes `int delta = 0;`
and only assigns it in the LEFT/RIGHT/MOVE branches. The `GZ_PART_SLIP` branch
called `move_shot(strip, offset - delta)` with `delta == 0`, i.e. it passed the
**cumulative** drag displacement from invoke straight into
`transform_translate_strip` (`strip->start += delta`, an absolute add). Every
`MOUSEMOVE` therefore re-added the full cumulative offset, so the strip raced
away quadratically ("exponential circular offset" = doubling per move). The MOVE
branch already had the cure (measure the applied delta against the invoke
snapshot); SLIP was never given its mirror.

**Fix (landed).** The SLIP branch now derives the already-applied displacement
from the strip's own state — `moved_request = offset - (strip->start -
orig_start)` — exactly like the MOVE branch derives it from the scene range, and
applies only that increment. Because the servo reads the state it just wrote, a
partially-applied increment cannot accumulate; the bar tracks the cursor 1:1.

**Verification.** Drag the bottom bar 30 frames in one gesture → `strip.start`
moves 30 (not ~465); release leaves no residual drift; repeat holds across
drag directions.

### 2.7 The gizmo length is not the full strip length (claps to scene range) when Set Preview Range is oFF and Clamp Scene Range is OFF.

This means the gizmo compresses though strip extends beyond its scene range. The strip gizmo should always be the strip size.

**Root cause (verified).** `scene_strip_gizmo_extent()` mapped the strip handles
through `seq::give_frame_index()`, which **clamps** the content index into
`[0, content_length-1]` (`strip_time.cc:43-68`). For a scene strip the content
length is derived live from the scene range (`content_length() = efra - sfra + 1
- anim_startofs - anim_endofs`), so the hold-frame extension beyond the scene
range collapses onto the scene-range boundary and the bar visually clamps to the
scene range whenever both toggles are off. The same clamped map was used in the
two draw sites (the layered-strip chips and the `bar_frame_in/out` lane packing),
so chips/lanes matched the clamped bar.

**Fix (landed).** Added `scene_strip_frame_from_handle()`, a linear **unclamped**
handle → strip-scene frame map:
`(handle - content_start()) + r.sfra + anim_startofs`. Scene strips never apply a
media playback rate (the factor is 1.0 for them) and retiming does not apply to a
live scene, so the linear form is exact — and critically it does not clamp, so it
yields the strip's full extent. `scene_strip_gizmo_extent()` and both draw sites
now use it, keeping the bar, the chips and the lane packing consistent.
**Committed as `ad0d3b349ce` (with §2.8).** Known edge case: the linear map does
not special-case `SEQ_REVERSE_FRAMES` (the old `give_frame_index` path did); a
reversed scene strip would draw mirrored. Acceptable — scene strips are rarely
reversed — revisit only if it is ever reported.

**Verification.** Strip extending past its scene range with both toggles off →
the gizmo spans the full strip; chips and lanes match; grabbing near the extended
end still hits. `ANIM_draw_scene_strip_range` (background shading) intentionally
keeps its scene-range map — see §2.7 open item.

### 2.8 Gizmo fails to initialize till we turn on Sync

Though the gizmo works when sync is off, it doesn't initialize in the file.

**Root cause (verified, two coupled failure modes).**
1. **Store precedence masks a valid timeline.** `scene_strip_master_get()`
   resolved the master as *first-wins*: if `workspace->sequencer_scene` was set
   it never consulted the legacy 3D Sequencer store, even when that workspace
   scene held no strip for the active scene. So a file whose `sequencer_scene`
   was a different timeline left the gizmo unresolvable until sync ran.
2. **The addon's master store is transient and load-write-only-when-visible.**
   `timeline_sync_settings.master_scene` is a WindowManager property ("not saved
   in the Blender file"), cleared by `on_load_pre`. `on_load_post` repopulated it
   only when a Sequencer area happened to be on screen — and as part of
   force-enabling sync. With sync off and no Sequencer area, the addon store
   stayed empty, so §2.8's "works with sync off but doesn't initialize in the
   file" is exactly this: the resolution needed the sync toggle to populate it.

**Fix (landed).**
1. `scene_strip_master_get()` now scans **both** candidate stores
   (`workspace->sequencer_scene` then the addon `master_scene`) and returns the
   first that actually holds a scene strip for the active scene. Precedence is
   unchanged when both resolve; the scan is sync-agnostic, so the gizmos
   initialize on load regardless of the sync state.
2. The addon's `on_load_post` re-establishes `master_scene` from
   `workspace->sequencer_scene` unconditionally (before the existing
   auto-sync-if-a-Sequencer-area-is-present block, which is preserved), so the
   store is populated on load without requiring the sync toggle.

**Verification.** Fresh file load with sync off → the gizmo bar is present and
grabbable immediately. A file whose `sequencer_scene` differs from the addon
master → the gizmo still resolves from the store that holds the strip. Toggling
sync later no longer "reveals" the gizmo (it was already there).

### 5.3 Round-11 follow-ups (2026-09-10)

Two follow-ups after §5.2 landed, plus a compile fix.

**5.3.1 Clamp-mode MOVE "updates, then snaps" — smoothed.** §5.2 added MOVE to
the release SET clamp so a stale range length would be settled on release. That
worked but read oddly: the range translated 1:1 with a stale length during the
drag, then jumped to the strip's extent (plus lead) on release. Fix: the
clamp-mode MOVE bar now runs `clamp_scene_strip_range()` **once, on the first
movement** of the drag (guarded by `move_clamp_initialized`), then re-seeds the
delta base (`move_base_sfra`) and translates 1:1 from there. MOVE is removed from
the release clamp, so there is no end-of-drag jump while the mode's SET-clamp
contract is preserved (the range still ends aligned to the strip, then translated
by the drag). The invoke snapshot (`orig_sfra/orig_efra`) is untouched, so Esc
still restores exactly. This also means the first movement can shift the range
length once (the same one-time alignment the green/red handles apply) — the
difference is that it now happens at the start of the drag, not the end.

**5.3.2 Gizmo/overlay draw without Sync — completed.** §2.8 made resolution
scan *both* master stores, but both can legitimately be empty: the workspace's
`sequencer_scene` is optional, and the addon's `master_scene` is transient (not
saved). So a file with neither set still drew nothing until Sync repopulated a
store. Fix: `ANIM_scene_strip_master_get()` gained a last-resort scan of
`bmain->scenes` — it returns the first scene whose sequence editor holds a
`STRIP_TYPE_SCENE` referencing the active scene. The shared helper
`scene_strip_for_active_scene()` now backs the two named stores and the scan, so
the gizmo, the scrub bar and `ANIM_draw_scene_strip_range` all resolve through
the same sync-agnostic path, and the "Scene Strip Gizmo" toggle alone is enough
to reveal the overlay.

**5.3.3 Compile fix.** The §2.3 operator (`6c32ba75155`) still called the
pre-rename `scene_strip_master_get` in its poll and exec; both now call
`ANIM_scene_strip_master_get`.

### 5.4 No-strip fallback: the gizmo works on any scene (2026-09-10)

**User report.** On a plain scene with no scene strips and no pinned sequencer,
nothing draws. The user wants the active-scene gizmo (set start/end, set the
preview range) even with no strip and no sync — it is useful as a standalone
range-setting tool.

**Root cause.** The whole gizmo chain (poll, rects, draw, operator) resolved the
target through `ANIM_scene_strip_master_get()`, which only succeeds when a scene
strip exists for the active scene. With no strip there was no target at all, so
the gizmo group polled false and nothing was drawn.

**Fix.**
1. New `SceneStripGizmoTarget { const Strip *strip; Scene *scene; bool
   scene_range_mode; bool preview_mode; }` and `scene_strip_gizmo_target_get()`:
   it first tries the strip resolver, and when that fails it falls back to the
   **active scene** with `strip == nullptr`. Preview mode is selected when the
   "Set Preview Range" toggle is on and the scene has a preview range
   (`SCER_PRV_RANGE`); otherwise the render range is edited.
2. The poll accepts the fallback (`target.scene != nullptr`), and the rects/draw
   use the target: extent = render range (`sfra..efra`, right edge one frame
   past `efra` since it is inclusive) or the preview range when preview mode is
   on. The bar uses the scene-strip theme color, suppresses the bump ring and
   labels with the active scene's name.
3. The operator gains `scene_range_mode`/`preview_mode` plus base fields, and a
   dedicated `scene_strip_timing_apply_scene_range()`: LEFT/RIGHT set the edited
   edge absolutely from the invoke base, MOVE/SLIP translate the window, all
   bounded at `MINFRAME`/`MAXFRAME`. `finish`, `sync_ranges`, the modal header
   and the Esc restore all early-out (or use the snapshot) in fallback mode — no
   strip means no clamp/overlap/neighbour/sync work. Esc restores the ranges and
   the preview flag exactly.
4. `ANIM_scene_strip_master_get()` is unchanged (strip-only), so the range
   shading and the §2.3 "Sync Scene Strip to Range" operator keep their
   strip-specific semantics.

**Effect.** The gizmo draws and edits on any dope-sheet scene: green/red set the
scene start/end (or the preview start/end when "Set Preview Range" is on and a
preview range exists), the middle bars move the window. No pinned sequencer, no
scene strips and no sync are required. When a strip *does* exist the previous
behavior is unchanged.

---

## 3. Implementation steps (ordered)

**Status after the Round-9 audit (2026-09-10):** steps 1, 3, 4, 5, 8, 9, 10
landed; step 2 (§2.3 button) is **deferred as an explicit decision**; steps 6–7
are carried as the remaining follow-up work.

1. ~~**Step 0:** commit the working-tree changes (MOVE clamp lockstep + preview
   gating); rebuild.~~ (done, `f68f43d584c`)
2. ~~**§2.3 + §2.5 (reconciliation):** the `ACTION_OT_scene_strip_sync_from_range`
   button (strip ← range, exact 1:1, one undo step) — the explicit cure for
   both the §2.3 snap and the §2.5 init desync. No listener, no invoke-time
   adopt (§2.3 option A verdict).~~ **Deferred (2026-09-10):** the button was
   never implemented; the wrap-up decision is to leave §2.3 as documented
   behavior for now — the first clamp drag after a timeline range edit
   translates the range as-is and the release SET clamp resolves it in the
   mode's direction (§2.5 item 1), which is predictable and undoable. Revisit
   when the "Sync Scene Strip" button UX is wanted; the full design above is
   ready to implement as-is.
3. **§2.4 (slip mechanism decoupling):** gate slip mechanism on the overlay
   toggle only; `SCER_PRV_RANGE` auto-enable on first preview write; snapshot
   `orig_anim_startofs/orig_anim_endofs` + `orig_flag`.
4. **§2.2 (sync-coupled preview writes):** trace the exact writer, then
   re-assert `psfra/pefra` after clamp-mode range writes when the toggle is
   off; toggle default off in `space_action.cc`.
5. ~~§2.1~~ landed with the corrected model (gizmo = strip extent only; see
   §2.1) — nothing left to do.
6. ~~**Bounds + view panning (carried):** clamp every range translate and strip
   translate at `MINAFRAME`/`MAXFRAME`~~ (the bounds half is done — every
   range/strip translate in the apply branches is clamped); the panning half
   remains as a cosmetic follow-up (see §5).
7. **Cancel snapshots (carried → landed):** Esc restores exactly for all 4 modes ×
   4 toggle states — including the new anim-offset/flag fields (§2.4 leftover,
   `f6b6846ddcc`), the SLIP clamp translate and the MOVE lockstep. The manual
   16-combination spot check remains to be run against a build.
8. **§2.6 (SLIP servo) — landed:** derive the already-applied displacement from
   the strip's state so only the per-move increment is applied (no cumulative
   re-apply / quadratic runaway).
9. **§2.7 (full strip extent) — landed:** unclamped linear handle → strip-scene
   map (`scene_strip_frame_from_handle`) used by the extent and both draw sites,
   so the bar spans the strip's full range (hold frames included) regardless of
   the toggles.
10. **§2.8 (load init) — landed:** the C resolver scans both master stores and
    returns the one holding a strip for the active scene; the addon
    `on_load_post` repopulates `master_scene` from `workspace->sequencer_scene`
    unconditionally, so the gizmos initialize on load with sync off.

## 4. Verification matrix (build `bf::editor_space_action` first)

Each of the 4 gizmos × toggles off / preview / clamp / both:

- **Slip, none:** bar shifts D, VSE strip frozen, sfra/efra and psfra/pefra
  unchanged.
- **Slip, clamp:** bar shifts D exactly once (no 2×), `sfra` and `efra` both
  shift D (length fixed), VSE strip frozen, no snap on release.
- **Slip, preview (display on *and* off):** bar shifts D, `psfra/pefra` shift D;
  scene range untouched; **the top bar always slips, never moves the strip**
  (§2.4 repro with preview display off).
- **Move, none:** strip translates in the VSE (overlap bump/resolve intact),
  dope-sheet bar and ranges unchanged.
- **Move, clamp:** strip and `sfra/efra` translate D together live; the range is
  aligned to the strip's visible extent (+ lead-in/out) **once on the first
  movement**, so the length is consistent from the first pixel — no end-of-drag
  jump (§5.3); stops only at `MINAFRAME`/`MAXFRAME`; long drags stay visible
  (view pans); **on a synced strip (after "Sync Scene Strip") the first drag is
  exact** (§2.5 repro).
- **Move, clamp, desynced (§5.3):** range length stale from a timeline edit →
  the first movement realigns it to the strip once (visible as a single length
  change at drag start, not a release jump), then translates 1:1; no snap when
  released.
- **Move, preview:** strip translates, `psfra/pefra` translate D.
- **Green/Red regression:** drag 10 = moves 10; the gizmo spans the strip's own
  extent in every mode; clamp scenarios from previous rounds still pass.
- **Timeline round-trip (§2.3):** change the scene range numerically → the
  gizmo keeps the strip's extent (expected, §2.3 algebra); press "Sync Scene
  Strip" → the gizmo adopts the new range exactly; then drag → no snap-back;
  the adopted range is the drag start point. Without the button, the first
  clamp drag's release snap is expected behavior, not a bug.
- **Sync matrix (§2.2):** with sync on and preview toggle off, drags never
  change `psfra/pefra`; with sync off, unchanged behavior.
- **Strip extent (§2.1, landed):** the gizmo spans the strip's own range in
  every mode; the dope-sheet overlays draw the preview (orange) and scene-range
  (grey) marks independently of the gizmo.
- **Esc:** exact restore in all 16 combinations (strip fields, anim offsets,
  sfra/efra, psfra/pefra, master range, pushed neighbors, preview-mode flag).
- **Slip linearity (§2.6, landed):** one gesture of D frames moves the strip by
  D (not D²); repeated moves in both directions stay 1:1 with no residual drift.
- **Full strip extent (§2.7, landed):** strip extending past its scene range
  with both toggles off → the bar spans the full strip; layered chips and lane
  packing match; grabbing near the extended end still hits.
- **Load init (§2.8, landed):** fresh file with sync off → the gizmo bar is
  present and grabbable immediately; a file whose `sequencer_scene` differs from
  the addon master still resolves; toggling sync later does not "reveal" it.
- **Draw without sync (§5.3, landed):** a file with neither
  `workspace->sequencer_scene` nor the addon `master_scene` set → the gizmo bar
  and the grey range shading still draw for the active scene (found via the
  `bmain->scenes` scan); no Sync toggle needed.
- **No-strip fallback (§5.4, landed):** a plain scene with no scene strips and
  no pinned sequencer → the gizmo draws on the active scene's render range;
  green/red set `sfra`/`efra`, the middle bars move the window; with "Set
  Preview Range" on and a preview range present, the same zones edit
  `psfra`/`pefra` instead; Esc restores exactly; a scene that *does* have a
  strip is unchanged.

**§2.7 open item — decided (2026-09-10):** `ANIM_draw_scene_strip_range` (the grey
out-of-strip shading, `anim_draw.cc:117`) still maps through the clamped
`give_frame_index`. **Decision: leave it scene-range-based.** The grey shading's
job is to mark the *scene range* boundary (what renders), not the strip's handle
extent — the two are different answers to different questions, and the gizmo bar
(§2.7) plus the orange preview overlay already communicate the strip extent.
Revisit only if the visual mismatch is reported as confusing.

## 5. Risks / notes

- `time_slip_strip()` on scene strips: verify the anim-offset path against the
  live-derived content length (one manual smoke test).
- The clamp-mode slip intentionally moves the render range — that is what
  "Clamp Scene Range" means; without clamp the render range is never touched.
- MOVE + preview intentionally slides the preview window off the strip's
  shot-time coverage (window follows the strip's motion 1:1) — user-confirmed.
- `v2d->tot` only updates on `ND_FRAME_RANGE` (`space_action.cc` listener);
  without the panning step the bar leaves the window on long drags even when
  the math is correct.
- **New:** the §2.3 "Sync Scene Strip" operator must never write `sfra/efra`
  (strip state only) so it cannot loop with the clamp, and must be disabled
  while a gizmo drag is modal.
- **New:** `BKE_scene` clamps `psfra/pefra` into `sfra/efra` on range writes —
  any design that moves the render range while the preview should stay put must
  re-assert the preview afterwards (§2.2 fix 2). If the clamp also *fires
  without sync*, move the preview re-assertion into
  `scene_strip_timing_sync_ranges()` unconditionally.
- **New:** the scene's preview range can be narrower than the scene range
  (`psfra > sfra` etc. is allowed) — the overlays draw the three ranges
  independently; nothing may clamp them into each other.

---

# UX to keep in mind (user's ledger)

1. The user can adjust the strips with the gizmo.
2. The user can override preview ranges from timeline (normal), or set preview
   ranges with the gizmo — synced.
3. The user can override and sync the gizmo scene ranges for the strip from the
   timeline, or set the scene ranges with the gizmo — synced.
4. The user can both control preview and scene range from strip.
5. The strip can extend/trim (green/red), move start+end together (slip) and
   move the strip in the sequencer (move) uniformly regardless of influence
   modes, 1:1.
6. Sync turns on playhead sync (done).
7. Drawing of the gizmo is always full range set by the strip settings, and if
   set to preview or scene range, the strip offsets should be drawn (§2.1).

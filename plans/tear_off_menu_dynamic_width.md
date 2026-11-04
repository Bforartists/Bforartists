# BFA - Tear-Off Menu/Panel: Dynamic Width of Torn-Off Menus

**Status:** Proposed / Planned
**Branch:** `tear_off`
**Sibling docs:**
- `_misc/tear_off_panel_vertical_resize.md` (vertical resize + scrollbar)
- `_misc/tear_off_panel_dynamic_width.md` — **superseded by this document** for the menu
  width work; its popover content remains valid as a *rejection note* (see §1.3).

---

## 1. Motivation / Scope

### 1.1 User story

> Torn-off menus currently have a fixed width, and are not dynamic to their contents at
> all. They should **shrink to the widest text** so we get no empty real estate.

Rules:

- **R1 — No truncation:** the longest row (icon + text + shortcut) fits fully, at every
  font scale, DPI, and translation.
- **R2 — No dead space:** the menu is never wider than the widest row needs (plus
  standard menu padding).
- **R3 — Stable:** the width does not jitter during interaction; it changes only when
  content changes, and changes are anchored at the top-left.

### 1.2 Scope decision: menus only

- **Torn-off menus** (`LayoutType::Menu` blocks created by
  `popup_menu_create_block()`) — **in scope**. This is where the fixed width lives.
- **Torn-off popover panels** — **out of scope.** Their width is set by the interface
  (panel-type `ui_units_x` hints resolved in `interface_region_popover.cc`); overriding
  it would fight the interface's own sizing. Rejected for a solid UX. See the sibling
  doc for the full analysis and rejection note.
- Regular (non-tear-off) menus and popovers: **unchanged** in every code path touched.

### 1.3 Why torn-off menus are fixed-width today (root cause)

Found in the code, three contributing factors:

1. **Hardcoded 200px root layout width.**
   `popup_menu_create_block()` (`interface_region_menu_popup.cc` ~line 204):
   ```cpp
   pup->layout = &block_layout(pup->block,
                               LayoutDirection::Vertical,
                               LayoutType::Menu,
                               0, 0,
                               200,          /* <-- fixed width */
                               0,
                               UI_MENU_PADDING,
                               style);
   ```
   All rows resolve *inside* a 200px-wide layout, so the resolved button rects never
   describe content narrower or wider than that constraint.

2. **`block_bounds_calc_text()` is widen-only.**
   `interface.cc` ~502. Per column it computes `i = max(BLF_width(drawstr))` and sets
   `xmax = max(x1addval + i + block->bounds, offset + block->minbounds)`. The `max_ff`
   against `minbounds` means a block can only grow relative to the floor — it can never
   shrink below the width the 200px layout produced. For short menus the 200px stands,
   leaving empty right real estate.

3. **The `minwidth` floor in `block_func_POPUP()`.**
   `interface_region_menu_popup.cc` ~230–267: `minwidth` = invoking button width, or a
   layout `ui_units_x` hint, or `UI_MENU_WIDTH_MIN` (`9 * UI_UNIT_Y`,
   `interface_intern.hh` line 74). This floor is reasonable for *attached* popups (the
   menu aligns with its button) but for a **pinned tear-off** there is no button to
   align with — the floor just forces width.

Net effect: a torn-off menu is `max(200px-layout width, minwidth, widest text)`, which
in practice is 200px (plus bounds padding) regardless of content.

### 1.4 Target behavior

- Width = `max(widest BLF-measured row, header row, min width for tear-offs)` + menu
  bounds padding.
- Recomputed on every layout/refresh (width is **derived, not stored** — no new
  `PopupBlockHandle` state).
- Can **shrink and grow** between refreshes, anchored at the top-left corner.
- `UI_MENU_WIDTH_MIN` semantics are kept for attached popups; tear-offs use the same
  floor initially but it stops dominating (see 3.2): the floor remains as a safety
  minimum, while the *content* is measured without the 200px constraint.

---

## 2. UX Specification

### 2.1 Width rule

- Widest row = BLF-measured `drawstr` width (same measurement
  `block_bounds_calc_text()` uses: `fontstyle_set(&style->widget)`, `BLF_width(...)`)
  plus icon width, right-aligned shortcut/hint columns, and the tear-off header row
  (label + pin/close icons — the header is just another row for measurement purposes;
  `block_tear_off_align_header()` then right-aligns the icons at the final width).
- Plus the standard `block->bounds` menu padding (unchanged).
- **Minimum:** `UI_MENU_WIDTH_MIN` floor is kept, but since it is `9 * UI_UNIT_Y` and
  typical menus are wider, the content measurement will usually dominate. If a menu is
  *narrower* than the floor, the floor wins — consistent with attached menus.
- **Maximum:** window width via the existing `popup_block_clip()` clamp. No horizontal
  scrollbar (out of scope; truncation should not occur at window-scale widths for menu
  text).

### 2.2 Resting-state & stability (R3)

- Measure from `drawstr` (neutral state), not hover/focus-modified state.
- **Tolerance band:** on refresh, if the newly measured width differs from the current
  width by less than ~`0.25 * UI_UNIT_X`, keep the current width. Prevents 1px font
  rounding at odd DPI scales from looking like a live resize.

### 2.3 Visual continuity

- **Top-left anchored:** width changes apply to the right edge only; the top-left corner
  (and therefore `tear_off_pin_xy` and the drag anchor) does not move. Extend the
  existing refresh-stability logic in `popup_block_position()` (the
  `prev_block_rect`/`prev_butrct` handling) to pin `xmin` for tear-offs.
- `block_tear_off_align_header()` runs after the final width (it already runs
  post-bounds in `interface.cc` ~2347) — no ordering change needed, just verify.
- Submenus that slide out of a torn-off menu (`pup->slideout`, `UI_DIR_RIGHT`) keep
  their own sizing behavior.

---

## 3. Technical Design

### 3.1 Overview of the change

Three touch points, all guarded by tear-off checks so nothing else changes:

```
popup_menu_create_block()   -> don't constrain tear-off menus to the 200px layout width
block_func_POPUP()          -> tear-off minwidth: content-measured, floor kept
block_bounds_calc_text()    -> allow shrinking below the resolved width for tear-offs
```

### 3.2 Step 1 — unconstrain the root layout width for tear-offs

`popup_menu_create_block()` does not know whether the menu will be torn off at creation
time (tearing off happens *after* the first popup creation, via `wm_menu_tear_off_exec`
setting `handle->is_tear_off = true` and re-invoking `popup_menu_invoke`). However:

- Every subsequent **refresh** of a torn-off menu re-runs `block_func_POPUP()` with
  `handle->is_tear_off == true` (the handle is passed through). So the width fix can key
  off `handle->is_tear_off` in `block_func_POPUP()` / `popup_menu_create_block()` via
  the `PopupBlockHandle` already threaded through `block_func_POPUP()` (its `handle`
  parameter).
- First-open (attached) menus keep 200px; after tear-off, the first refresh re-lays-out
  at the dynamic width. This also means the tear-off transition itself visually
  re-fits the menu once — acceptable, and it is the moment the user expects a change.

Implementation:

- Thread a "measure/loose layout" width into `popup_menu_create_block()`:
  - Attached: `200` (unchanged).
  - Tear-off (`handle->is_tear_off`): lay out at the same width the block will be
    measured to. Because `block_bounds_calc_text()` measures text independently of the
    layout width (BLF on `drawstr`), the layout width can be left at `200` for the
    *resolve*, with the *bounds* step shrinking the block afterwards (step 3). If it
    turns out rows mis-resolve at 200 for tear-offs (e.g. `template_list`-style rows
    inside menus), fall back to a two-pass resolve at the measured width; menu items
    rarely contain such rows, so this is a contingency, not the plan of record.

### 3.3 Step 2 — `block_func_POPUP()` minwidth for tear-offs

In `block_func_POPUP()` (`interface_region_menu_popup.cc` ~362/378 where
`block->minbounds = minwidth`):

- For `handle->is_tear_off`: keep `minwidth = UI_MENU_WIDTH_MIN` as the floor (it flows
  into `block_bounds_calc_text()`'s `max_ff`), so behavior is conservative; the dynamic
  part comes from step 3. No change may be needed here at all if step 3 is implemented
  as a shrink-capable final pass — verify during implementation. Keep this step as
  "verify, adjust only if the floor dominates."

### 3.4 Step 3 — shrink-capable bounds for tear-off menus (the core)

Add a tear-off-aware post-pass (or extend `block_bounds_calc_text()`) so the final
block width is the **measured natural width**:

1. Measure the widest row with BLF exactly like `block_bounds_calc_text()` does
   (`fontstyle_set(&style->widget)`; for each non-separator button:
   `BLF_width(style->widget.uifont_id, drawstr)` + icon width + per-row padding;
   honor alignment groups via `but->alignnr` like the existing function; include the
   tear-off header row buttons).
2. `W_target = max(W_rows, UI_MENU_WIDTH_MIN, header width) + block->bounds` padding.
3. Apply the **tolerance band** vs the previous refresh's width (`handle->prev_block_rect`
   already stores it): if `|W_target - W_prev| < 0.25 * UI_UNIT_X`, use `W_prev`.
4. Resize the block: for tear-offs, set every column's `xmax = xmin + W_target` (mirroring
   how `block_bounds_calc_text()` assigns columns), run `button_update()` on affected
   buttons ("clips text again" — needed to re-clip/un-clip draw strings at the new
   width), then `block_bounds_calc()` to recompute rect + safety.
5. Anchor: translate so `xmin` stays fixed relative to the previous rect (top-left
   anchoring, see 2.3).

Placement: a new static helper in `interface.cc` next to `block_bounds_calc_text()`
(e.g. `block_bounds_calc_text_dynamic_width()`), called from the
`BLOCK_BOUNDS_POPUP_MENU` path (`block_bounds_calc_popup()`, `interface.cc` ~670) only
when `block->handle && block->handle->is_tear_off`. This keeps the widen-only function
byte-for-byte identical for all existing menus.

### 3.5 Refresh & state safety

- Width is derived per layout; nothing stored on the handle → no state to carry through
  `block_update_from_old()`.
- `popup_translate()` / `tear_off_pin_xy` sync: unaffected — top-left fixed.
- Collapse/expand (`tear_off_set_collapsed`): width persists trivially (re-derived).
- The refresh-stability offset logic in `popup_block_position()`
  (`handle->prev_block_rect.ymax - block->rect.ymax > 1.0f` translate) must not fight
  the new width changes: extend it to also compare/anchor `xmin` for tear-offs.

### 3.6 Interaction with sibling features

- **Vertical resize doc:** width (derived) and user height (user state) compose; the
  bottom grip/scrollbar draw inside the block rect that now has the dynamic width.
- **Collapsed pin widget:** position is top-left based → unaffected.

---

## 4. Implementation Steps

1. **[ ] Baseline verification:** confirm the root cause (log measured width vs 200px
   for a torn-off short menu). No code change.
2. **[ ] Measure helper:** add the BLF widest-row measurement + `W_target` computation
   (with tolerance band) as `block_bounds_calc_text_dynamic_width()` in `interface.cc`,
   modeled on `block_bounds_calc_text()`. `/* BFA - Tear-Off Menu/Panel */` tags.
3. **[ ] Hook the path:** call it from `block_bounds_calc_popup()` for tear-off handles
   only; verify short menus shrink and long menus grow on refresh.
4. **[ ] Anchor & refresh:** extend `popup_block_position()` refresh logic to pin
   `xmin` for tear-offs; verify no fight with the existing ymax-stability translate.
5. **[ ] Verify step 2 floor:** check `block_func_POPUP()` `minwidth` behavior for
   tear-offs; adjust only if the floor dominates unexpectedly.
6. **[ ] Tests & polish:** run the matrix in §5; build clean.

**Files touched (expected):**

- `source/blender/editors/interface/interface.cc` — measure/bounds helper + hook in
  `block_bounds_calc_popup()`
- `source/blender/editors/interface/regions/interface_region_popup.cc` — refresh xmin
  anchoring
- `source/blender/editors/interface/regions/interface_region_menu_popup.cc` — only if
  step 5 shows the floor must change
- `source/blender/editors/interface/interface_intern.hh` — helper declaration

---

## 5. Test Matrix

| # | Scenario | Expected |
| --- | --- | --- |
| 1 | Tear off a menu with short items | Menu shrinks below 200px to the widest item; no empty right space. |
| 2 | Tear off a menu with a long item | Widest item fits fully; no truncation. |
| 3 | Refresh changes an item string (toggle label, dynamic items) | Width re-fits, shrink **and** grow; top-left anchored. |
| 4 | Menu with right-aligned shortcut hints / icons | Shortcut column included in measurement. |
| 5 | Tear-off header row (label + pin/close) | Header fits; icons right-aligned at final width; SeprLine spans width. |
| 6 | German / Japanese translation (longer strings) | No truncation; width fits that language. |
| 7 | DPI / font scale change | Correct width at all scales; no 1px jitter on refresh (tolerance band). |
| 8 | Collapse (pin) → expand | Width re-derived; pin widget unaffected. |
| 9 | Drag by header | Moves rigidly; crop/pin state intact. |
| 10 | Submenu sliding out of a torn-off menu | Submenu behavior unchanged. |
| 11 | Same menu attached (not torn off) | Unchanged: still 200px-based, `minbounds` floor as today. |
| 12 | Regular popovers / popover panels torn off | Unchanged (out of scope). |
| 13 | Menu wider than window | Clamped by existing window clip. |
| 14 | With vertical-resize feature enabled | Dynamic width + user height crop coexist. |

---

## 6. Regression Watch-list

- `block_bounds_calc_popup()` mouse-offset scaling (`oldwidth/oldheight` ratio) — verify
  offsets remain sane when the width changes between refreshes.
- `update_flexible_spacing()` (already skipped for tear-off blocks).
- `block_tear_off_align_header()` clamp behavior for very short menus.
- `BLOCK_POPUP_MEMORY` last-item mouse offset (uses button rect widths).
- Attached popup menus of every editor (View3D, outliner, node editors) — must be
  bit-identical behavior.
- Themes/translations at high DPI.

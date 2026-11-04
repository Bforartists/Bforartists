# BFA - Tear-Off Menu/Panel: Vertical Resize & Scroll

**Status:** Proposed / Planned
**Branch:** `tear_off`
**Related work:** Tear-off implementation (pinned tear-off panels, collapse pin widget, workspace scoping)

---

## 1. Motivation / User Story

Torn-off panels can be very long (e.g. tall item menus, property popovers). Once torn off
and pinned, the panel always occupies its **full content height**, which can dominate the
screen or overlap other UI.

A user should be able to **"crop" a torn-off panel vertically** — shrink it to show only a
section — and then **scroll through the rest of the content** inside the cropped window,
exactly like resizing and scrolling any normal viewport.

> **User story:** *As a user, I want to drag the bottom edge of a torn-off panel upward so
> only the section I care about is visible, and scroll inside it to reach the content that
> is cropped away.*

---

## 2. UX Specification

### 2.1 Resize affordance (bottom grip)

- A **bottom resize handle** is drawn as a thin grip strip along the bottom edge of a
  **pinned tear-off panel only** (not regular popups/menus).
- **Visual target: the editor area-edge / sidebar resize experience.** The strip should
  look and feel like the draggable border between two editors or the sidebar splitter:
  a subtle interactive zone at the panel's bottom edge that is nearly invisible at rest
  and reveals itself on hover.
- Height of the strip: ~`1.5 * U.widget_unit` hit area (generous hotspot, thin visual).
- **Hover:** cursor changes to `WM_CURSOR_EDIT` — the same up/down resize cursor used
  when hovering a horizontal editor border in `screen_ops.cc` (`area_join_cursor()` / the
  border-resize operator set this) — and the strip highlights using the theme's widget
  hover colors, fading in like an action zone (`AZone`-style alpha ramp rather than an
  instant on/off).
- **While dragging:** the highlight stays lit and the panel edge follows the mouse with
  the same direct-manipulation feel as dragging an editor border (no rubber-band, live
  geometry update per mousemove).
- **Drag up:** shrinks the panel height (minimum height = header height + one
  `U.widget_unit` of content).
- **Drag down:** grows the panel up to its **full natural content height** (never larger
  than needed) and never beyond the window bounds.
- **Double-click** on the handle: reset to full height (clears the user height) — the
  same convention as double-clicking editor borders to snap them.

### 2.2 Scrollbar (right edge)

- When the user height is smaller than the content height, a **thin vertical scrollbar is
  drawn on the right edge** of the panel, in the **exact format and look of every other
  Blender scrollbar** (the View2D scrollers used in editors, list views, outliner, etc.).
  It must not be a custom-designed bar.
- Drawn through the standard widget pipeline: `wcol_scroll` theme colors rendered with
  `draw_widget_scroll()` — identical track/thumb/emboss treatment to
  `view2d_scrollers_draw()`.
- **Auto-fade behavior (ties into the existing interface feel):**
  - At rest the bar sits at the dimmed rest alpha; on mouse-over of the scrollbar zone it
    expands/fades up to full opacity, exactly like View2D scrollers do via
    `v2d->alpha_vert` (the `alpha_fac = (alpha/255) * (1 - V2D_SCROLL_MIN_ALPHA) +
    V2D_SCROLL_MIN_ALPHA` ramp with `V2D_SCROLL_MIN_ALPHA = 0.4`).
  - While dragging the thumb, the bar enters the pressed state (`SCROLL_PRESSED`, driven
    by the `V2D_SCROLL_V_ACTIVE` flag in View2D) and stays fully lit.
  - Fading animates smoothly (per-redraw alpha ramp) rather than popping between states.
- Thumb proportional to `visible_height / content_height`, respecting
  `V2D_SCROLL_THUMB_SIZE_MIN` so it never becomes invisibly small.
- Hidden when the full content fits (no user crop, or content shrank below the user
  height).

### 2.3 Scrolling interactions (inside the cropped region)

- **Mouse wheel / trackpad pan** scrolls the cropped content, clamped to
  `[scrollmin, scrollmax]`.
- **Edge auto-scroll** while dragging buttons near the top/bottom edge of the cropped
  region, reusing the `menu_scroll_test()`-style edge zones.
- Scroll offset is preserved across refreshes (popup blocks refresh frequently when a
  panel's properties change).

### 2.4 Persistence

- The user height is **session-only**: it survives popup refreshes, collapse/expand
  (pin-widget) cycles, and dragging; it resets when Blender restarts.
- No `.blend` or preference changes in this iteration.

### 2.5 Interaction with existing tear-off behavior

| Existing behavior | Interaction with resize |
| --- | --- |
| Drag panel by header (`popup_translate`) | Unaffected; pin-widget position stays in sync. |
| Collapse to pin widget (`tear_off_set_collapsed`) | Height is remembered; expanding restores the cropped height. |
| Hide/restore by editor domain & mode (`tear_off_is_visible`) | Unaffected; resize state persists while hidden. |
| Refresh (`block_update_from_old`) | User height and scroll offset carried over to the new block. |
| Keyboard pass-through, click-outside exemptions | Unaffected. |

---

## 3. Technical Design

### 3.1 State — `PopupBlockHandle` (`interface_intern.hh`)

Add next to the existing `tear_off_*` fields (~line 1117–1159):

```cpp
/** BFA - Tear-Off Menu/Panel: user-cropped height of the torn-off panel in window
 * pixels. 0 means "no user resize" (panel uses its full natural height). */
int tear_off_user_height = 0;

/** BFA - Tear-Off Menu/Panel: full natural content height, recomputed on every layout.
 * Used to clamp `tear_off_user_height` and to size the scrollbar thumb. */
int tear_off_content_height = 0;

/** BFA - Tear-Off Menu/Panel: set while the bottom resize grip is being dragged. */
bool tear_off_resize_dragging = false;

/** BFA - Tear-Off Menu/Panel: hover state for the bottom resize grip. */
bool tear_off_resize_hover = false;

/** BFA - Tear-Off Menu/Panel: offset between the mouse and the grip's y while dragging. */
int tear_off_resize_drag_ofs_y = 0;

/** BFA - Tear-Off Menu/Panel: hover state for the right-edge scrollbar (drives fade-in). */
bool tear_off_scroll_hover = false;
/** BFA - Tear-Off Menu/Panel: set while the scrollbar thumb is being dragged. */
bool tear_off_scroll_dragging = false;
/** BFA - Tear-Off Menu/Panel: animated scrollbar alpha (0..255), ramps toward
 * 255 on hover/drag and back down on leave — View2D `v2d->alpha_vert` equivalent. */
uchar tear_off_scroll_alpha = 0;
/** BFA - Tear-Off Menu/Panel: grab offset between mouse and thumb while scrolling. */
int tear_off_scroll_drag_ofs_y = 0;
```

Everything is per-handle, so it dies with the popup — no DNA changes, no session file
changes (matches the "session-only" decision).

### 3.2 Size override — `popup_block_position()`
(`regions/interface_region_popup.cc`)

Today the region rect is set from the block's natural rect (~lines 1088–1091):

```cpp
region->winrct.xmin = block->rect.xmin - margin;
region->winrct.xmax = block->rect.xmax + margin;
region->winrct.ymin = block->rect.ymin - margin;
region->winrct.ymax = block->rect.ymax + UI_POPUP_MENU_TOP;
```

Insert a **resize step between `popup_block_clip()` and this winrct computation**:

1. Record the natural height: `handle->tear_off_content_height = BLI_rctf_size_y(&block->rect)`.
2. If `handle->tear_off_user_height > 0`:
   - Clamp the user height to `[min_height, tear_off_content_height]` and to the window
     height available at the panel's current position.
   - Keep the **top edge fixed** (`block->rect.ymax` unchanged — the header stays put,
     which is what users expect when cropping) and raise `block->rect.ymin`:
     `block->rect.ymin = block->rect.ymax - user_height`.
   - Translate every button below the new crop by the delta (same pattern as
     `menu_scroll_apply_offset_y()`, but here it is a *base* offset before scrolling).
3. The existing winrct computation then automatically produces a smaller region — no
   changes needed to the region sizing itself.
4. The collapsed full-window override (~lines 1099–1102) keeps working as-is; resize
   state simply persists underneath it.

Because `popup_block_position()` already recomputes `scrollmin/scrollmax` from the final
button rects (~lines 1113–1117), the existing scroll machinery picks up the cropped rect
without modification **once `scrollmin` is allowed to be positive** (see 3.3).

### 3.3 Scrolling — reuse the existing popup scroll machinery

The popup scroll fields already exist on the handle and are maintained by
`popup_block_position()`:

- `handle->scrollmin` / `handle->scrollmax` — clamped scroll range
- `handle->scrolloffset` — current offset
- `popup_block_scrolltest()` (~line 727) — sets `UI_SCROLLED` / `BLOCK_CLIPTOP` /
  `BLOCK_CLIPBOTTOM` per button

For non-tear-offs, `scrollmin` is forced `<= 0` (it only accounts for window-clip
overflow). For tear-offs with a user height:

```cpp
/* BFA - Tear-Off Menu/Panel: a user-cropped tear-off can scroll its hidden content. */
if (handle->is_tear_off && handle->tear_off_user_height > 0) {
  handle->scrollmin = ...; /* positive: content hidden below the crop */
}
```

Wheel events already flow through `ui_handle_menus_recursive()` →
`menu_scroll_apply_offset_y()` (`interface_handlers.cc` ~11216, wheel dispatch ~11776).
`menu_scroll_apply_offset_y()` clamps to `[scrollmin, scrollmax]` and calls
`layout_panel_popup_scroll_apply()` for layout panels — so once `scrollmin` reflects the
crop, wheel scrolling works with **little to no handler changes**. Verify the wheel
dispatch isn't gated on `BLOCK_CLIPTOP/CLIPBOTTOM` in a way that excludes the resize case
(`popup_block_scrolltest()` must mark clipped buttons for the cropped tear-off too).

### 3.4 Resize grip interaction — `interface_handlers.cc`

Follow the exact pattern of the collapsed pin widget dragging (`tear_off_pin_dragging`):

1. **Hover test** (in the tear-off mousemove path, alongside
   `tear_off_pin_widget_rect()` consumers): a helper
   `tear_off_resize_grip_rect(const PopupBlockHandle *handle, rctf *r_rect)` builds the
   strip rect from `block->rect` (bottom edge, full width, grip height). Set
   `handle->tear_off_resize_hover` and `WM_cursor_set(win, WM_CURSOR_Y_MOVE)`.
2. **Press:** on `LEFTMOUSE` press inside the grip, set `tear_off_resize_dragging` and
   record `tear_off_resize_drag_ofs_y = event->xy[1] - block->rect.ymin`.
3. **Drag:** on mousemove, recompute
   `user_height = clamp(event->xy[1] - ofs ...)` and tag the popup region for re-run of
   `popup_block_position()` (the same refresh path used when the panel content changes —
   the geometry step is idempotent because the natural content height is re-derived every
   layout).
4. **Double-click:** detect two presses within the double-click time on the grip and reset
   `tear_off_user_height = 0` (and `scrolloffset = 0`).

Note: unlike the collapsed pin widget (which is drawn when the region covers the whole
window), the grip exists in the expanded state, so the interaction hooks into the normal
button-event path for tear-off blocks — the same place the header collapse/close operators
already run.

### 3.5 Drawing — scrollbar & grip
(`regions/interface_region_popup.cc`, tear-off draw path next to `tear_off_pin_widget_draw()`)

#### Scrollbar — reuse the standard widget drawing

- Use the **same code path as View2D scrollers**: `uiWidgetColors wcol =
  theme::theme_get()->tui.wcol_scroll;` and `draw_widget_scroll(&wcol, &vert, &slider,
  state)` (as done in `view2d_scrollers_draw()`, `view2d.cc` ~1487). This guarantees the
  bar looks identical to all other scrollbars in every theme, including custom themes.
- `state` mirrors View2D: `SCROLL_PRESSED` when the user is dragging the thumb
  (`tear_off_scroll_dragging`), plain otherwise. Do not set `SCROLL_ARROWS` (zoom
  handles) — the crop has no zoom dimension.
- **Alpha / fade animation:** replicate the View2D fade using an alpha value animated on
  the popup handle (see state fields in 3.1). Per redraw compute
  `alpha_fac = (alpha/255) * (1 - V2D_SCROLL_MIN_ALPHA) + V2D_SCROLL_MIN_ALPHA`, multiply
  into `wcol.inner[3]` / `wcol.item[3]`, zero `wcol.outline[3]` and the emboss alpha
  exactly as `view2d_scrollers_draw()` does (it temporarily zeroes
  `tui.widget_emboss[3]` and restores it after).
- **Hover expansion:** when the mouse is within the scrollbar zone, ramp the handle's
  alpha toward 255 over a few redraws; when the mouse leaves (and no drag is active),
  ramp back down. This is the same distance/alpha model used by the auto-hide scroller
  action zones in `screen_ops.cc` (`az->alpha` / `v2d->alpha_vert` with
  `V2D_SCROLL_HIDE_WIDTH`), just driven by hover instead of a zone.
- Geometry: track on the right edge, width from `V2D_SCROLL_WIDTH`
  (`0.55 * U.widget_unit + 2 * U.pixelsize`), thumb length
  `visible/content` clamped by `V2D_SCROLL_THUMB_SIZE_MIN`, offset by
  `scrolloffset / scrollmin`.
- Thumb dragging: hit-test the thumb (View2D divides bar into `SCROLLHANDLE_BAR` /
  `MIN` / `MAX` handles — for the popup a plain thumb-drag plus track jump-to is
  sufficient), converting mouse y to `scrolloffset` and reusing
  `menu_scroll_apply_offset_y()` for the actual scroll.

#### Grip strip — editor-border look

- Drawn as a subtle interactive zone at the bottom edge: essentially invisible at rest
  (track color at low alpha), fading in on hover with an alpha ramp — the same
  progressive-reveal treatment action zones use (`AZone` alpha in
  `screen_edit.cc`/`area.cc`).
- Hover/drag highlight uses the theme's widget hover/inner colors (`wcol_num` or the
  neutral widget set used by splitter handles) rather than inventing new colors.
- While hovering, set `WM_CURSOR_EDIT` (same cursor as horizontal editor borders in
  `screen_ops.cc`); while dragging, keep it and keep the zone lit.
- The grip is a *hit zone + highlight*, not a visible widget bar: after the user resizes
  once, the affordance remains discoverable by hover, matching how area edges behave.

#### Theme settings tie-in

Everything the feature draws comes from the existing theme — **no new theme fields**:

| Visual element | Source |
| --- | --- |
| Scrollbar track/thumb/outline | `bTheme::tui.wcol_scroll` (existing scrollbar colors) |
| Scrollbar rest/hover/pressed alpha | `V2D_SCROLL_MIN_ALPHA` + animated alpha on the handle |
| Grip hover/drag highlight | neutral widget colors (`tui` widget set used by splitters) |
| Corner radius / rounding | existing popup corner radius (`block->bounds`, roundbox widget settings) |
| Cursor | `WM_CURSOR_EDIT` (existing editor-border cursor) |

If a future iteration wants user control (e.g. "always show scrollbar"), it should be a
preference applied to the shared drawing helper — not a separate look for tear-offs.

### 3.6 Refresh & state safety

`block_update_from_old()` copies flags (`BLOCK_TEAR_OFF`, etc. ~lines 1143–1153) but
handles are per-block. Ensure across refreshes:

- `tear_off_user_height`, `tear_off_resize_dragging`, and `scrolloffset` are copied from
  the old handle to the new one (mirroring how `prev_block_rect` / `scrolloffset` already
  survive refreshes today).
- Re-clamp the user height after every layout: content may shrink below the stored height
  (then behave as full-height) or grow (crop unchanged, scrollbar appears).
- `popup_translate()` keeps `tear_off_pin_xy` in sync — extend it to also translate the
  grip rect implicitly (derived from `block->rect`, so free) and to keep the collapsed
  restore position consistent with the cropped height.
- While collapsed (`tear_off_set_collapsed`), skip grip hover/drag handling entirely —
  only the pin widget is interactive.

### 3.7 Edge cases

| Case | Handling |
| --- | --- |
| Content shrinks below user height | Crop becomes a no-op; scrollbar hidden; height re-clamped. |
| Content grows while cropped | Scrollbar appears; `scrollmin` grows; offset clamped. |
| Window resized / DPI change | Re-clamp height to window; re-run `popup_block_clip()` naturally on next position pass. |
| Panel dragged while cropped | Top edge follows the drag; crop height constant. |
| Collapse → expand while cropped | Height preserved; expand restores crop, not full height. |
| Hide by mode/workspace while cropped | No change; state persists on restore. |
| Refresh mid-drag | Dragging flag carried to the new handle; drag continues against updated geometry. |
| Minimum size | Header + one widget unit of content; never 0. |
| Scroll while at full height | No-op (`scrollmin == 0`). |

---

## 4. Implementation Steps

Ordered checklist (each step compiles and is testable on its own):

1. **[ ] State fields** — add the five `tear_off_*` fields to `PopupBlockHandle`
   (`interface_intern.hh`).
2. **[ ] Content-height bookkeeping** — record `tear_off_content_height` and apply the
   top-anchored crop in `popup_block_position()`
   (`regions/interface_region_popup.cc`).
3. **[ ] Scroll range** — extend the `scrollmin` computation for cropped tear-offs so the
   existing `scrolloffset` machinery scrolls the hidden content; verify wheel scrolling
   works via `menu_scroll_apply_offset_y()` (`interface_handlers.cc`) with no functional
   change, adjusting the wheel dispatch gate if needed.
4. **[ ] Grip interaction** — add `tear_off_resize_grip_rect()`, hover + cursor change,
   press/drag/double-click handling in `interface_handlers.cc` (pin-widget pattern).
5. **[ ] Drawing** — grip strip (editor-border look, `WM_CURSOR_EDIT`) + right-edge
   scrollbar via `draw_widget_scroll()` with `wcol_scroll` and animated alpha in the
   tear-off draw path of `regions/interface_region_popup.cc`.
6. **[ ] Refresh hardening** — copy resize/drag/scroll state in
   `block_update_from_old()`; re-clamp on every layout; suppress grip while collapsed.
7. **[ ] Edge cases & polish** — window resize re-clamp, drag-while-cropped sync in
   `popup_translate()`, min-height clamp, scrollbar thumb math.

Files touched (expected):

- `source/blender/editors/interface/interface_intern.hh`
- `source/blender/editors/interface/regions/interface_region_popup.cc`
- `source/blender/editors/interface/interface_handlers.cc`
- (possibly) `source/blender/editors/interface/interface_layout.cc` — only if the grip
  ends up as a layout-drawn element rather than a direct draw (decide in step 5).

All code carries the `/* BFA - Tear-Off Menu/Panel: ... */` comment tag, consistent with
the branch.

---

## 5. Test Plan

No unit tests exist for this area; verification is manual + build checks.

### Build

- Configure/compile the affected targets, e.g.
  `ninja blender` (or the project's standard build), ensuring zero new warnings in the
  touched files.

### Manual test matrix

| # | Scenario | Expected |
| --- | --- | --- |
| 1 | Tear off a tall panel, drag bottom grip up | Panel crops, top edge stays fixed, cursor `Y_MOVE` on hover. |
| 2 | Drag grip back down past content height | Stops at full natural height, scrollbar disappears. |
| 3 | Mouse wheel inside cropped panel | Content scrolls, clamped at both ends, scrollbar thumb tracks. |
| 3a | Mouse over the scrollbar zone | Bar fades in/expands to full alpha smoothly; fades back out on leave. |
| 3b | Drag the scrollbar thumb | Thumb enters pressed state (`SCROLL_PRESSED` look), content follows, bar stays lit. |
| 4 | Refresh while cropped (change a property driving the panel) | Crop height and scroll offset preserved. |
| 5 | Collapse (pin) → expand while cropped | Pin widget unaffected; expand restores cropped height. |
| 6 | Switch workspace / object mode so panel hides, then restore | Crop state intact. |
| 7 | Drag panel by header while cropped | Moves rigidly; pin position stays in sync. |
| 8 | Double-click grip | Resets to full height, scroll resets. |
| 9 | Resize window smaller than the panel | Panel re-clamped to window. |
| 10 | Regular (non-tear-off) popup/menu | No grip, no scrollbar, behavior unchanged. |
| 11 | Keymap smoke test with panel open (hotkeys still reach the editor) | Pass-through behavior unchanged. |

### Regression watch-list

- Scrollbar look matches View2D scrollers in **every theme**, incl. themes with
  transparent (`wcol_scroll.inner[3] == 0`) tracks — handle the 0.25-alpha fallback like
  `view2d_scrollers_draw()` does.
- Popover arrow offset path (`BLOCK_POPOVER`).
- Pie menus (`BLOCK_PIE_MENU` winrct override).
- Collapsed pin-widget drag (`tear_off_pin_xy` sync).
- `menu_scroll_test()` auto-scroll edge zones for regular menus.

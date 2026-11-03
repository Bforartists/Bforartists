# Tear-Off Menus and Panels: Completion Plan (#6821)

**Branch:** `tear_off`. Every phase or step is its own commit, tagged `#6821`.

**Detail docs, still valid except where corrected below:**
- `_misc/tear_off_menu_dynamic_width.md`
- `_misc/tear_off_panel_vertical_resize.md`

Line numbers are from the mid-merge tree and will drift.

## Progress log

| Phase | Status | Commits | Checked by |
|---|---|---|---|
| 0. Merge conflict | Done | `b61865f64fa` | Built with no errors. Copy Python Command and Edit Source still need a hand test |
| 1. Bug fixes, first series | Done | `c9eb2d90783`..`1848c80ea57` (20 fixes) | Built with no errors, scripted GUI suite |
| 1. Reload Scripts crash | Done | `91f52f1a813` | Crash reproduced in the app, gone after the fix |
| 1. Review findings | Done | `f40393e8038`..`4b55dee679f` (6 commits) | Built with no errors. Written after the hand test build, so not hand tested |
| 1. Hand test | Done | | Maintainer, on the `91f52f1a813` build |
| 2. Shared cleanup and related fixes | Committed | `a14f3d0e234`, `440b786824e`, `35b9d9bf6fc`, `ab1209481c2`, `63438649de9`, `40348728360` | Built with no errors at `5f6a82d0ff4`. Not hand tested |
| 3. Preference toggle | Committed | `99c93ab4370`, `d800b242ae2` | Built with no errors at `5f6a82d0ff4`. Not hand tested |
| 2 and 3. Review findings | Committed, not built yet | `9851fa1a14b`, `babd3140507`, `7846ed92b8e` | Code review only so far |
| 4. Enum tear-offs | Done | `e0b8b93c0da`..`a255c080db4` | Built with no errors. Full GUI suite passes: 33 scenarios, no crashes. Needs a hand test: Transform Pivot, Set Keyframe Type, toolbar Keyframe Type |
| 5. Tear off any panel | Done | `769cde7b580`..`f0f014951d6` (6 commits), `d4753f7e807`, review fixes `6419db72fe1`..`bfa156ed802` (4 commits) | Built with no errors at `780e9363f02`. Full GUI suite passes: 59 scenarios, no crashes. Needs a hand test: Shift+double-click, real Cycles and node panels, tree views |
| 6. Tool shelf | Done | `ff3c405326d`, `062c8f43a0a`, `85166c8e111`, `23c3c3ac026`, `e6cd5c1dde1` | Built with no errors at `780e9363f02`. Scenarios `p6_*` pass at 1 to 4 columns. Needs a side-by-side hand test in each editor |
| 7. Dynamic width | Committed, not built yet | `b3545d24156`..`402c43aa474` (6 commits) | Code review only. Scenarios `p7_*` written, not run. No hand test |
| 8. Vertical resize and scroll | Committed, not built yet | `fc9a8fb6547`, `781307e4f37`, `82ca5a551ee`, `b34059e410d`, review fixes `02f42967a43`..`235d8011651` (7 commits) | Code review only. Scenarios `p8_*` written, not run. No hand test |

**Scripted GUI suite:** `_misc/6821-sim/` drives the real app with `--enable-event-simulate`, using `--factory-startup` and a temporary config. It runs each scenario in its own process with `--debug-memory`, and finds popups by diffing screenshots. Click positions assume a 1600x1000 window at 100% scale. Simulated events can't be double-clicks, so those stay hand tests.

**Reference shots:** `p7_attached` and `p8_regular` compare attached menus and popovers with a build that doesn't have Phases 7 and 8, because a build compared with itself passes whatever it does. Record them on such a build with `SIM_RECORD_REF=1 run.sh p7_attached p8_regular` (`SIM_EXE` picks the build). Without a recording those steps only log `INCONCLUSIVE`.

## Context

Menus and popovers can already be torn off, collapsed, moved, clamped to the window and scoped to a workspace, editor and mode. Seven items remain. The audit also found bugs in the existing code that the new features would inherit, so those get fixed first.

**Decisions made:**
- Build items 3, 5 and 6 fresh. Blenux's drag-out and resize work isn't on `origin/tear_off`, `tear_off_dynwidth` (an older copy of this branch) or Blenux's fork. Ask Blenux once before starting, in case it can still be shared.
- Panels tear off with **Shift+drag**. Shift+click keeps its current behaviour.
- The tool shelf tears off **one panel at a time**, not as a whole shelf with tabs.

| Your item | Phase |
|---|---|
| 1. Merge conflict in `interface_ops.cc` | 0 |
| 2. Tear off enum menus | 4 |
| 3. Tear off any panel | 5 |
| 4. Tool shelf keeps its look and width | 6 |
| 5. Dynamic menu width, resizable pinned panels | 7 |
| 6. Vertical resize with scroll | 8 |
| 7. Preferences toggle | 3 |
| Audit fixes (added) | 1, 2 |

## Phase 0: Resolve the conflict

This is the only unmerged file (markers at `interface_ops.cc:357-361` and `372-405`). Nothing else changes while `MERGE_HEAD` exists.

**Keep the HEAD side of both hunks.** Upstream's single line can't be taken alone: `context_restored` is declared in the HEAD hunk and used outside the markers at lines 416 and 429, so it wouldn't compile.

**Carry upstream's fix into the helper.** Upstream's #151170 makes operators in a popup's context menu use `context_active_but_get_respect_popup()`. `button_under_cursor_or_active()` (line 294) checks the button under the cursor *first*, which goes wrong here: when Copy Python Command is clicked in a context menu, the cursor is over whatever sits beneath that menu item, so the wrong button's command could be copied.

New lookup order in the helper:
1. `context_active_but_get_respect_popup(C)`, which covers the #151170 case
2. The context-store lookup (`button_pointer` / `button_prop`), which identifies the exact button
3. The button under the cursor, only as a last resort for a tear-off with no active button

Also remove the `COPY_PYTHON_CMD` `printf` at line 396.

**Then:**
1. Confirm no markers remain.
2. Build, because the other interface files auto-merged and have not been compiled together yet.
3. Test Copy Python Command from a main-region button, a popover button and a torn-off button.
4. Conclude the merge with a commit.

## Phase 1: Fix existing bugs

**Status: implemented.** A read-only review tested the table below and found more bugs, so the table is the original audit and "What changed after review" is what actually shipped. Each commit message says what it fixed and how to test it.

**What changed after review:**
- **b:** a modal check alone leaks when the cursor is outside, so a click that ends a modal state also stays with the tear-off.
- **c:** a title test alone isn't enough, so double-click also checks for modal state and for a button under the cursor.
- **d:** the dedicated region type is the real fix. Passing state at creation (d1) is separate, and useful for the pin position. It does not remove a wrong frame, because refresh runs before draw.
- **e:** `tear_off_context_ensure()` alone isn't enough, because the event handler stores its own area and region. Those are now cleared on area and region exit, and hidden tear-offs defer their refresh.
- **f:** the plan's force-close was wrong. `wm_window.cc:2117` only runs on macOS. Tear-offs now re-lay out whenever the UI scale changes, on any platform.
- **File load is safe:** `wm_files.cc` removes all handlers first.

**New bugs found and fixed:**
- Reading freed popups after delayed callbacks, which also affected regular dialogs and File > New.
- Reload Scripts leaving the context window unset. Removing that force-close exposed a crash on freed types, fixed in `91f52f1a813`.
- X on a collapsed pin not closing it.
- An open tear-off blocking the mouse wheel, ending IME sessions, and clearing tooltips elsewhere.
- Top bar tear-offs vanishing, and tear-offs of a deleted workspace being stranded.
- Tear Off Panel from a nested popover closing the parent.
- The Tear Off row taking the `T` key and appearing mid-menu. It now only draws at the menu entry point, so pie menus, tab and appended context menus, tree-view context menus, the search menu, the splash and hold menus have no row.
- Tear-offs treated as modal popups for the paint cursor and IME, and stacking order flipping on a screen change.
- A modal state in an older tear-off being stolen by a newer one, and a double-click reaching a covered tear-off.
- Closing an area leaving a tear-off's buttons pointing at freed space data, and leaving Quad View leaving a freed region in the handler.

**Known gaps, none blocking:**
- Grab offset lost at the window edge, an arrow cursor left behind, and a stale hit rectangle. Polish.
- Possible playback stall while hovering a tear-off, refresh cost during playback, and the paint cursor while hovering one. These need the hand test.

**Original audit:**

| # | Bug, confirmed by reading the code | Where | Fix |
|---|---|---|---|
| a | Dragging a **regular** popup no longer updates `popup_create_vars.event_xy`, so regular dialogs can jump back when they refresh | `interface_handlers.cc:11688`, `interface_region_popup.cc:68-72` | Update it for every popup in `popup_translate()` |
| b | All keyboard events bypass torn-off popups, so **text fields inside them shouldn't accept typing** (popups have no separate modal handler, see `interface_handlers.cc:9636-9638`) | `popup_handler` early return | Pass through only when no button is in a modal state |
| c | Double-clicking **anywhere** in a tear-off collapses it, including double-clicking a number field to type | `popup_handler` | Limit it to the header row |
| d | The tear-off window listener never gets set: `is_tear_off` is assigned after `popup_block_create()` returns, and the `static ARegionType` is shared and wiped by the next popup | `interface_region_popup.cc:1351-1401` | Pass tear-off state in at creation (d1) and use a dedicated region type |
| e | `ctx_area` / `ctx_region` go stale after a workspace switch or when the source area is closed, and refresh then restores them. This is a crash and wrong-context risk | `interface_region_popup.cc:530-538`, `interface_handlers.cc:11442-11445` | New `tear_off_context_ensure()`, validate against the current screen (e1) |
| f | DPI changes used to close popups because their layout bakes in the pixel size, but tear-offs now survive with wrong geometry | `wm_window.cc:2117` | Force-close them, or refresh with rescaled positions |
| g | Debug output: active `EDITSOURCE_*` `printf`s, commented `MENUDBG` lines, and a stray `}        if (` | `interface_ops.cc:2433-2655`, `interface_handlers.cc` | Remove. Apply the Phase 0 lookup order to the edit-source path too |

**d1. Set the state before the first layout.** Add an `is_tear_off` argument through `popup_block_create()`, `popup_menu_invoke()` and `popover_panel_invoke()`.

**e1. `tear_off_context_ensure()`.** If the stored area isn't in the active screen, re-resolve it to an area with the same `spacetype` and a region of the same type. If none exists, keep the tear-off hidden (`tear_off_is_visible` already covers this case).

**Recheck in Phase 5:** `BLOCK_POPOVER_ONCE` applies to panels created on a press, which is what Shift+drag will do.

## Phase 2: Shared cleanup

Merge the duplicated code before adding a third tear-off type:
- The menu and panel close and collapse operators are near-identical. Keep one handle-lookup helper.
- Move the post-creation setup (flags, mode, space type, workspace, label, pin position) into `tear_off_handle_init()`.

**Also fixed in this phase**, both known gaps left by Phase 1:
- Hover shortcuts in tear-offs (Ctrl+C and Ctrl+V over a button), in `35b9d9bf6fc`.
- A dropdown left open under a tear-off on a screen change, in `ab1209481c2`.

## Phase 3: Preference toggle (item 7)

This comes before the new entry points, so each one is gated from the start.

**Storage:** take one byte from BFA's `_pad_custom[4]` in `DNA_userdef_types.h`: `char bfa_ui_flag` with a *disabled* bit, leaving `_pad_custom[3]`. Zero means enabled, so existing preference files default to on and need no versioning.

**RNA:** `Preferences.use_tear_off` using a negative sdna bit, next to `disable_search_on_keypress` in `rna_userdef.cc`. The default of true already comes from DNA through that bit, so it isn't set again.

**Closing:** the update callback frees nothing, because it runs during handler dispatch. It only wakes each window with `WM_event_add_mousemove()`, and each tear-off closes itself in `popup_handler` once `tear_off_enabled()` is false. All tear-offs in a window close on one event, and that event carries on to its target. A tear-off under a regular popup waits until that popup closes, because the popup can hold raw pointers into it.

**UI:** a left-aligned checkbox in `space_userpref.py:259-262`, labelled "Tear-Off Menus and Panels".

**When off:** no tear-off rows, no context menu entry, Shift+drag does nothing special, and tear-off operators fail their poll. Behaviour should match pre-feature Bforartists.

## Phase 4: Enum menus (item 2)

**Status: implemented as below, not built yet.** The logic is in `interface_region_tear_off_enum.cc`, and `WM_OT_enum_tear_off` is in `wm_operators.cc`.

**Why it needs different handling:** an enum dropdown depends on its source `Button`. `def_but_rna__menu` reads it directly, and items write to `handle->retvalue`, which is only applied back through that active button. Once detached, the button can be freed on redraw and clicks wouldn't change the property.

**Design:**
- New `WM_OT_enum_tear_off` stores identifiers, not a button: `id_type`, `session_uid` and `data_path`, or `use_context` and `data_path` for data of the context's scene. The session UID avoids raw ID pointers across undo. Scene data follows the window's scene, as the source button does.
- Re-resolve the property on every refresh and every click, so no RNA pointer is kept between the two. If it no longer resolves, show a grayed "Not available" row and keep the header.
- Factor the item, column and heading logic out of `def_but_rna__menu` into `enum_menu_draw()`, so both paths share it and the torn-off version looks identical. Torn-off items are `ButMenu` buttons with no RNA, like attached ones, not live property buttons. Each has an `apply_func` that resolves the path again on click, then sets the value, with autokey, update and undo as the attached path does. The highlight comes from `UI_SELECT_DRAW` on each refresh.
- Use the same tear-off row and `tear_off_header_draw()` as menus, and reuse the menu close and collapse operators.
- **File load closes the tear-off,** with no crash and no gray row (`wm_files.cc` removes all handlers first). Keeping one open would mean changing load for all tear-offs.

**Fixes this phase needed first:**
- Delayed callbacks now run in the tear-off's own area.
- The row writes no value. It used to set a dropdown to its first item, because the return value was still 0.
- The row no longer takes the number keys.
- The header stays intact in multi-column menus.

**Scope:**
- **In:** RNA property dropdowns. `operator_menu_enum` too, storing the operator name, property and call context so each click runs the operator.
- **Out for now,** with no tear-off row: enum search popups, flag enums, dropdowns in operator dialogs, source buttons or blocks with callbacks, operator menus with preset properties or a context pointer, Screen or Window Manager owned properties, and properties with no ID-based path (preferences, operator redo properties).

## Phase 5: Tear off any panel (item 3)

**Gesture**, in `handler_panel_region` (`interface_panel.cc:2963`):
- Shift+press on a header no longer acts immediately. It waits.
- Release without moving does today's Shift+click: pin in tabbed regions, plain click elsewhere.
- Moving past `WM_event_drag_threshold` calls the operator, then sets `menu->is_grab` so the new float stays attached to the cursor until release.

**Other entry point:** add "Tear Off Panel" to `popup_context_menu_for_panel`. That function used to return early for regions without tabs and for subpanels. It now continues when the panel is eligible, and shows only the tear-off entry (`interface_context_menu.cc:1409-1411`).

The source panel stays where it is. The tear-off is a second live view of it, which also leaves panel order and `.blend` data untouched.

**Blockers to fix:**

| Problem | Fix |
|---|---|
| Most C panels aren't in `WM_paneltype_find` (they're only on `art->paneltypes`) | Resolve from the source region type first; add a `popover_panel_invoke` variant that takes a `PanelType *` |
| Refresh doesn't re-poll the root panel, so `draw` can run with a poll-guarded `None` (`interface_layout.cc:6756` only polls children) | Poll before drawing a tear-off; on failure show a grayed "Not available" row |
| The header's `draw_header` is skipped, so **enable checkboxes in panel headers disappear** | Call it inside `tear_off_header_draw()` for panels. Do the same for `draw_header_preset` if it fits |
| `pt->draw` is called unguarded (`interface_layout.cc:6730`) | Add a null check |

**Excluded:** `PANEL_TYPE_INSTANCED` panels (modifiers, constraints, and similar), since they need `custom_data_ptr` per instance. Their entries won't appear.

**As written, where it differs from the above:**
- The gesture has its own threshold, the mouse value from the Preferences. `WM_event_drag_threshold` reads the Shift key press and picks the keyboard value.
- `draw_header` and `draw_header_preset` go in a new `tear_off_panel_header_draw()`, not in `tear_off_header_draw()`, which menus also use.
- A panel torn off a region has `is_popover == False` and shows full region content. Row tear-offs keep `True`.
- A torn-off Properties panel shows "Not available" on other tabs and comes back with its tab.
- A tear-off re-polls on an allow-list of space notifiers: Properties, Image, Node, Sequencer, Clip, Dope Sheet and Graph. The Sequencer's `view_type` sent no notifier, so it now does. The 3D View and Info report notifiers stay out, because they fire too often.
- A popup's preview job and `Render` belong to its region, and are freed when it closes. The free is skipped while any job is running, because the `Render` list has no lock. That rare case keeps the `Render` until exit, as upstream does for a closed area.
- A screen or workspace change during the Shift+press wait ends the gesture first (`panel_tear_off_gesture_cancel_all`). Otherwise the handler is dropped by area and its state leaks.

**Memory checks for Phase 5:**
- The exit report can't catch a kept preview `Render`, because `RE_FreeAllRender` empties the list before it runs. A non-undo file load also drops the result buffers, though the `Render` itself stays until exit. So compare the count during the session, with no file load in between: `p5_preview_close` prints `new render` from `wm.memory_statistics`, and the count must stay the same across its rounds.
- `harness.py` ends with `os._exit`, which skips the exit report and loses buffered stdout, so `--debug-memory` alone shows nothing for a scenario. Scenarios that check memory end with `finish_with_memory_report`, which quits for real, and `run.sh` prints the lines to compare. `p5_workspace_gone` must print no `panel_tear_off_gesture_begin` line.

## Phase 6: Tool shelf (item 4)

Uses Phase 5. Shelf panels poll and draw against the origin region through the restored context, so `region.type` checks keep working and the content matches. What's missing is width:

- `toolsystem_column_count()` (`space_toolsystem_common.py:1266-1298`) measures the **origin region**, so a torn-off shelf panel would change columns when the real shelf is resized, and the popup itself defaults to 10 units wide.
- **Capture:** at tear-off, store the source width with View2D zoom removed (`tear_off_source_width`), and size the popup from it through `pup->ui_size_x`, less the tab strip when tabs are shown.
- **Expose:** add a read-only `UILayout.tear_off_width` (0 when not torn off). `toolsystem_column_count(region, layout=None)` uses it instead of the region width. Pass the layout from `_layout_generator_detect_from_region` (`:657`), `draw_entries` (`:1369`), `space_sequencer_tabs.py:171` and the `bfa_brush_panel`, `bfa_power_user_tools` and `edit_dimensions` add-ons.
- **Thresholds stay the same**, so 1, 2, 3 columns and the text list look the same as they did in the shelf.
- **Width is remembered** for the life of the tear-off, including through collapse and expand. The Phase 7 width grip changes it, and snaps to the shelf's column steps.
- **Headerless panels:** a shelf panel with no visible header needs the context-menu entry, because there's no header to Shift+drag. Confirm this in `VIEW3D_PT_tools_active` and each tabs file.
- **Background:** popups use the menu theme color, not the shelf's. Compare side by side and match if it's noticeably different.

Test in the 3D View, Image/UV, Node and Sequencer editors.

**As written, where it differs from the above:**
- The handle keeps `tear_off_width` and `tear_off_width_chrome`, not `tear_off_source_width`. The width includes the 20 units Python takes off the thresholds when tabs are hidden, so toggling the source shelf's tabs can't change the column count.
- Only panels torn off a `TOOLS` region of the four shelf editors get a width, through `tear_off_init_from_region` (`interface_region_popover.cc`). Clip and File Browser `TOOLS` panels keep their normal width and color.
- A one-column panel has a floor of 3 units so the header fits, so it can be slightly wider than the shelf's layout.
- `block_is_tear_off_shelf` turns off the popover treatment of tool buttons: small icons, text padding, icon alignment, and no quick tooltip. Sub-tool menus open to the right.
- A tool change only publishes on the message bus, so tear-offs subscribe to `WorkSpace.tools` and rebuild.
- Background: shelf color, forced opaque, with the regular widget style. This is its own commit, so it can be dropped if the side by side disagrees.

## Phase 7: Dynamic width (item 5)

**Menus:** follow `_misc/tear_off_menu_dynamic_width.md`. Torn-off menus fit their widest row in `block_bounds_calc_popup()`, and attached menus don't change. Width is derived, never stored.
- Correction to that doc: it accepts a one-time re-fit after tearing off. Phase 1's d1 makes that unnecessary, so the first layout is already correct.
- Enum tear-offs use the same path.

**Panels:** popovers keep their designed width by default. Pinned panels get a right-edge grip:
- New `tear_off_user_width` on the handle.
- It feeds `pup->ui_size_x`, then refreshes, so the layout really reflows rather than stretching.
- Minimum is the panel's designed width (or the shelf's narrowest column step). Maximum is the window.
- Double-clicking the grip resets it. The cursor is `WM_CURSOR_X_MOVE`.

**As written, where it differs from the above:**
- One width field, not two: `tear_off_width`, where 0 means the designed width. `tear_off_width_default` above 0 means a shelf panel and holds the reset value. This replaces `tear_off_user_width`.
- The grips are handled in `popup_handler` by `tear_off_edges_handle`, not in `popup_block_position`, and run before button handling.
- Torn-off menus have no `UI_MENU_WIDTH_MIN` floor. Explicit `ui_units_x` still counts, and submenus of a torn-off menu keep the floor.
- The panel corner resizes both axes with `WM_CURSOR_NSEW_SCROLL`, because no diagonal cursor exists.
- Shelf steps are the real snap points, `tabs + n*40 + 32`, and the width is free above the last one.
- A narrow shelf gives up the grip first, then a clipped title, below 2.5 units of room.

## Phase 8: Vertical resize and scroll (item 6)

Follow `_misc/tear_off_panel_vertical_resize.md`, with these corrections:

1. **Scope includes torn-off menus**, not just panels, since you specifically want to trim large menus. The doc only covers panels.
2. **Wheel scrolling mostly works already.** The clipped branch runs before the `BLOCK_TEAR_OFF` breaks in `handle_menu_event`. The actual problem is the reverse: wheel *outside* a clipped tear-off also scrolls it, so add `(block->flag & BLOCK_TEAR_OFF) && !inside` to break out.
3. **No state copying across refreshes.** The handle persists through refresh, as `tear_off_collapsed` already shows, so §3.6's copy step isn't needed.
4. **Use `WM_CURSOR_Y_MOVE`** throughout. The doc mixes it with `WM_CURSOR_EDIT`.
5. **Collapse:** `tear_off_expanded_size` must remain consistent with the cropped height, so clamping stays correct on expand. Nothing ever read that field, so it was removed. Expand gets its height from `tear_off_user_height` through `tear_off_height_apply`, and clamps through `popup_block_clip`, using the live `block->rect`.
6. **Sticky header (maintainer request, 2026-11-03).** The tear-off header (label, pin, close and its separator) stays visible and usable at any scroll position, so the panel can always be moved, collapsed or closed. `menu_scroll_apply_offset_y()` moves every button in the block and `popup_block_scrolltest()` hides what's out of bounds, so:
   - Tag the header's buttons when `tear_off_header_draw()` creates them. Identifying them by operator idname, as `block_tear_off_align_header()` does, misses the label and separator.
   - Don't move tagged buttons when scrolling, and never hide them.
   - Treat the bottom of the header as the top edge of the scrolling content, for hiding buttons, the scroll arrows, the scroll range, the scrollbar track and `layout_panel_popup_scroll_apply()`.
   - Applies whenever a tear-off scrolls, including one clipped by the window with no user crop.
   - Buttons are hidden whole rather than clipped by pixel, so check that smooth trackpad scrolling doesn't look jumpy under the header. If it does, scissor the content instead.
   - Gate all of this on `is_tear_off`. Regular popups stay as upstream.

Keep the bottom-edge grip, top-anchored crop, `draw_widget_scroll()` with theme colors and View2D-style fade. Grip hit areas (right and bottom) must stay out of button hit-testing. Height stays session-only.

**As written, where it differs from the above:**
- The fade is the real View2D model: alpha comes from the cursor's distance on each mouse move, with no timer. The doc's redraw ramp isn't how View2D works.
- Minimum height is the header, one row and both arrow zones. A pin parked at the window bottom lifts the block to that height when expanded, and the pin stays at the lifted spot.
- The content has its own scissor and the header draws in a separate pass, so a row half under the header is cut by the pixel. Curve and scope widgets replace the scissor, so six sites in `interface_draw.cc` now limit it through `but_scissor_limit`, and the curve points are limited too. `draw_but_TRACKPREVIEW`'s two later scissors go through `but_scissor_set`, and the scope outlines, drawn with the test off, through `but_scope_end`.
- Menus gain a gutter for the bar only while overflowing. Panels get none, and their bar is capped to fit their margin.
- Esc or right-click during a grip drag restores the previous size, and input is swallowed until the left button's release.
- The scroll arrows stay alongside the bar. Tab between fields scrolls to the field. Arrow keys stay with the editor.
- A middle mouse pan keeps the keys, as a grip drag does, and ends if its tear-off hides or collapses another way. Esc during a pan does nothing, because Esc never closes a tear-off. Scenario `p8_pan_hidden`.
- A refresh moves a block whose pin is above the popup clip's limit, instead of trimming it, which would invent a scroll range. Scenario `p8_top_band`.
- A tear-off's arrow zones stop at its real edge, without the theme's shadow margin, and its auto-scroll stops while a newer popup is under the cursor. Scenarios `p8_shadow_band`, `p8_fractional_crop`, `p8_covered_scroll`. Histogram outline: `p8_scope`. The track preview needs a real clip, so it's a hand test.

## Files

| Area | Files (`source/blender/` unless noted) |
|---|---|
| Popup core | `editors/interface/regions/interface_region_popup.cc`, `interface_region_popover.cc`, `interface_region_menu_popup.cc`, `interface_region_tear_off_enum.cc`, `editors/interface/interface_intern.hh`, `editors/include/UI_interface_c.hh` |
| Events | `editors/interface/interface_handlers.cc`, `interface_panel.cc`, `interface_context_menu.cc` |
| Layout | `editors/interface/interface.cc`, `interface_layout.cc`, `interface_ops.cc` |
| Operators | `windowmanager/intern/wm_operators.cc`, `wm_window.cc` |
| RNA and prefs | `makesrna/intern/rna_userdef.cc`, `rna_ui_api.cc`, `makesdna/DNA_userdef_types.h` |
| Python | `scripts/startup/bl_ui/space_toolsystem_common.py`, `space_userpref.py` |

## Verification

There are no automated tests for this area, and CI only checks that it compiles. Build every phase with `.\make.bat` in a visible terminal, logged to a file, then test by hand.

| Phase | Check |
|---|---|
| 0 | Copy Python Command from main region, popover and tear-off, including when the context menu item sits over another button. Edit Source still works |
| 1 | Move a regular dialog, then trigger a refresh: it stays put. Type in a text field in a torn-off panel. Double-click a number field: it edits, not collapses. Hotkeys still reach the editor. Resize the window. Switch workspace, close the source area, then interact. Change the resolution scale. File > New and Open with tear-offs open |
| 3 | Toggle off: no rows or entries, open tear-offs close, and the setting survives a restart. An old preferences file comes up enabled. The file opens in Blender |
| 4 | Tear off an enum, click items: the property changes and the highlight follows. Change the value elsewhere: it updates. Undo and redo. Delete the owning object: "Not available", no crash. Load a file: it closes, no crash. Multi-column enum looks the same |
| 5 | Shift+click still pins. Shift+drag tears off and follows the cursor. Context menu entry works, including in regions without tabs. Header checkbox works. Move to a context where poll fails: "Not available", no Python errors. Modifier panels offer no tear-off |
| 6 | Compare side by side at each column count, in each shelf editor. Resize the real shelf: the tear-off doesn't change. Width survives collapse and expand. Tool switching works |
| 7 | The test matrix in the width doc. Translations and high DPI. Panel grip reflows content. Regular menus unchanged |
| 8 | The test matrix in the vertical doc, on menus as well as panels. Wheel, trackpad and thumb drag. Crop survives refresh and collapse |

Regression pass at the end: pie menus, regular popovers, dialogs, the search popup and Ctrl+click panel header.

## Delivery

- **Commits:** the merge first, then one commit per phase on `tear_off`, tagged `#6821`. Each phase compiles alone, so stopping partway is safe.
- **PR:** a single one for #6821 at the end, using the wiki title format, with a manual update and the `_misc` plan docs removed before merging.
- **Check in after Phase 1:** those fixes change the behaviour of what's already there, so test before stacking features on top.

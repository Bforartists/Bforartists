# Tear-Off Menus and Panels: Completion Plan (#6821)

**Delivery:** on approval, save this as `_misc/6821-tear-off-completion-plan.md`. Don't stage it during the merge. Implementation starts only after a separate go-ahead.

**Branch:** `tear_off`, currently merging `master` (week 43).

**Detail docs, still valid except where corrected below:**
- `_misc/tear_off_menu_dynamic_width.md`
- `_misc/tear_off_panel_vertical_resize.md`

Line numbers are from the mid-merge tree and will drift.

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

| # | Bug, confirmed by reading the code | Where | Fix |
|---|---|---|---|
| a | Dragging a **regular** popup no longer updates `popup_create_vars.event_xy`, so regular dialogs can jump back when they refresh | `interface_handlers.cc:11688`, `interface_region_popup.cc:68-72` | Update it for every popup in `popup_translate()` |
| b | All keyboard events bypass torn-off popups, so **text fields inside them shouldn't accept typing** (popups have no separate modal handler, see `interface_handlers.cc:9636-9638`) | `popup_handler` early return | Pass through only when no button is in a modal state |
| c | Double-clicking **anywhere** in a tear-off collapses it, including double-clicking a number field to type | `popup_handler` | Limit it to the header row |
| d | The tear-off window listener never gets set: `is_tear_off` is assigned after `popup_block_create()` returns, and the `static ARegionType` is shared and wiped by the next popup | `interface_region_popup.cc:1351-1401` | Pass tear-off state in at creation (d1) and use a dedicated region type |
| e | `ctx_area` / `ctx_region` go stale after a workspace switch or when the source area is closed, and refresh then restores them. This is a crash and wrong-context risk | `interface_region_popup.cc:530-538`, `interface_handlers.cc:11442-11445` | New `tear_off_context_ensure()`, validate against the current screen (e1) |
| f | DPI changes used to close popups because their layout bakes in the pixel size, but tear-offs now survive with wrong geometry | `wm_window.cc:2117` | Force-close them, or refresh with rescaled positions |
| g | Debug output: active `EDITSOURCE_*` `printf`s, commented `MENUDBG` lines, and a stray `}        if (` | `interface_ops.cc:2433-2655`, `interface_handlers.cc` | Remove. Apply the Phase 0 lookup order to the edit-source path too |

**d1. Set the state before the first layout.** Add an `is_tear_off` argument through `popup_block_create()`, `popup_menu_invoke()` and `popover_panel_invoke()`. This also removes the one-frame wrong layout, which Phase 7 depends on.

**e1. `tear_off_context_ensure()`.** If the stored area isn't in the active screen, re-resolve it to an area with the same `spacetype` and a region of the same type. If none exists, keep the tear-off hidden (`tear_off_is_visible` already covers this case).

**To test:** whether tear-offs survive File > New/Open safely, since `tear_off_workspace` is a raw pointer; and whether `BLOCK_POPOVER_ONCE` affects tear-offs.

## Phase 2: Shared cleanup

Merge the duplicated code before adding a third tear-off type:
- The menu and panel close and collapse operators are near-identical. Keep one handle-lookup helper.
- Move the post-creation setup (flags, mode, space type, workspace, label, pin position) into `tear_off_handle_init()`.

## Phase 3: Preference toggle (item 7)

This comes before the new entry points, so each one is gated from the start.

**Storage:** take one byte from BFA's `_pad_custom[4]` in `DNA_userdef_types.h`: `char bfa_ui_flag` with a *disabled* bit, leaving `_pad_custom[3]`. Zero means enabled, so existing preference files default to on and need no versioning.

**RNA:** `Preferences.use_tear_off` using a negative sdna bit, next to `disable_search_on_keypress` in `rna_userdef.cc:8436`. It gets an update callback that force-closes open tear-offs through `popup_handlers_remove_all_force()`.

**UI:** a left-aligned checkbox in `space_userpref.py:259-262`, labelled "Tear-Off Menus and Panels".

**When off:** no tear-off rows, no context menu entry, Shift+drag does nothing special, and tear-off operators fail their poll. Behaviour should match pre-feature Bforartists.

## Phase 4: Enum menus (item 2)

**Why it needs different handling:** an enum dropdown depends on its source `Button`. `def_but_rna__menu` reads it directly (`interface.cc:4779-4806`), and items write to `handle->retvalue`, which is only applied back through that active button. Once detached, the button can be freed on redraw and clicks wouldn't change the property.

**Design:**
- New `WM_OT_enum_tear_off` stores `id_session_uid`, `data_path` and `prop_name`, not a button. The session UID avoids raw ID pointers across undo and file load.
- Re-resolve the property on every refresh. If it no longer resolves, show a grayed "Not available" row and keep the header.
- Factor the item, column and heading logic out of `def_but_rna__menu` so both paths share it and the torn-off version looks identical. The torn-off path uses live property buttons, which write directly and highlight the current value.
- Use the same tear-off row and `tear_off_header_draw()` as menus, and reuse the menu close and collapse operators.
- Don't set `BLOCK_MOVEMOUSE_QUIT` on tear-offs (`interface.cc:4784`).

**Scope:**
- **In:** RNA property dropdowns. `operator_menu_enum` too, storing the operator name and property so each click runs the operator; check `interface_layout.cc:3809` first.
- **Out for now:** enum search popups, and properties with no ID-based path (preferences, operator redo properties). These get no tear-off row.

## Phase 5: Tear off any panel (item 3)

**Gesture**, in `handler_panel_region` (`interface_panel.cc:2355-2375`):
- Shift+press on a header no longer acts immediately. It waits.
- Release without moving does today's Shift+click: pin in tabbed regions, plain click elsewhere.
- Moving past `WM_event_drag_threshold` calls the operator, then sets `menu->is_grab` so the new float stays attached to the cursor until release.

**Other entry point:** add "Tear Off Panel" to `popup_context_menu_for_panel`. That function currently returns early for regions without tabs and for subpanels (`interface_context_menu.cc:1405-1417`). It needs to continue when the panel is eligible, and show only the tear-off entry.

The source panel stays where it is. The tear-off is a second live view of it, which also leaves panel order and `.blend` data untouched.

**Blockers to fix:**

| Problem | Fix |
|---|---|
| Most C panels aren't in `WM_paneltype_find` (they're only on `art->paneltypes`) | Resolve from the source region type first; add a `popover_panel_invoke` variant that takes a `PanelType *` |
| Refresh doesn't re-poll the root panel, so `draw` can run with a poll-guarded `None` (`interface_layout.cc:6610` only polls children) | Poll before drawing a tear-off; on failure show a grayed "Not available" row |
| The header's `draw_header` is skipped, so **enable checkboxes in panel headers disappear** | Call it inside `tear_off_header_draw()` for panels. Do the same for `draw_header_preset` if it fits |
| `pt->draw` is called unguarded (`interface_layout.cc:6598`) | Add a null check |

**Excluded:** `PANEL_TYPE_INSTANCED` panels (modifiers, constraints, and similar), since they need `custom_data_ptr` per instance. Their entries won't appear.

## Phase 6: Tool shelf (item 4)

Uses Phase 5. Shelf panels poll and draw against the origin region through the restored context, so `region.type` checks keep working and the content matches. What's missing is width:

- `toolsystem_column_count()` (`space_toolsystem_common.py:1264-1289`) measures the **origin region**, so a torn-off shelf panel would change columns when the real shelf is resized, and the popup itself defaults to 10 units wide.
- **Capture:** at tear-off, store the source width with View2D zoom removed (`tear_off_source_width`), and size the popup from it through `pup->ui_size_x`, less the tab strip when tabs are shown.
- **Expose:** add a read-only `UILayout.tear_off_width` (0 when not torn off). `toolsystem_column_count(region, layout=None)` uses it instead of the region width. Pass the layout from `draw_cls` (`:694`) and `draw_entries` (`:1360`).
- **Thresholds stay the same**, so 1, 2, 3 columns and the text list look the same as they did in the shelf.
- **Width is remembered** for the life of the tear-off, including through collapse and expand. The Phase 7 width grip changes it, and snaps to the shelf's column steps.
- **Headerless panels:** a shelf panel with no visible header needs the context-menu entry, because there's no header to Shift+drag. Confirm this in `VIEW3D_PT_tools_active` and each tabs file.
- **Background:** popups use the menu theme color, not the shelf's. Compare side by side and match if it's noticeably different.

Test in the 3D View, Image/UV, Node and Sequencer editors.

## Phase 7: Dynamic width (item 5)

**Menus:** follow `_misc/tear_off_menu_dynamic_width.md`. Torn-off menus fit their widest row in `block_bounds_calc_popup()`, and attached menus don't change. Width is derived, never stored.
- Correction to that doc: it accepts a one-time re-fit after tearing off. Phase 1's d1 makes that unnecessary, so the first layout is already correct.
- Enum tear-offs use the same path.

**Panels:** popovers keep their designed width by default. Pinned panels get a right-edge grip:
- New `tear_off_user_width` on the handle.
- It feeds `pup->ui_size_x`, then refreshes, so the layout really reflows rather than stretching.
- Minimum is the panel's designed width (or the shelf's narrowest column step). Maximum is the window.
- Double-clicking the grip resets it. The cursor is `WM_CURSOR_X_MOVE`.

## Phase 8: Vertical resize and scroll (item 6)

Follow `_misc/tear_off_panel_vertical_resize.md`, with these corrections:

1. **Scope includes torn-off menus**, not just panels, since you specifically want to trim large menus. The doc only covers panels.
2. **The branch currently blocks wheel scrolling.** The `BLOCK_TEAR_OFF` breaks in the wheel cases of `handle_menu_event` must only apply when the block isn't clipped, or the doc's "little to no handler changes" won't hold.
3. **No state copying across refreshes.** The handle persists through refresh, as `tear_off_collapsed` already shows, so §3.6's copy step isn't needed.
4. **Use `WM_CURSOR_Y_MOVE`** throughout. The doc mixes it with `WM_CURSOR_EDIT`.
5. **Collapse:** `tear_off_expanded_size` must remain consistent with the cropped height, so clamping stays correct on expand.

Keep the bottom-edge grip, top-anchored crop, `draw_widget_scroll()` with theme colors and View2D-style fade. Grip hit areas (right and bottom) must stay out of button hit-testing. Height stays session-only.

## Files

| Area | Files (`source/blender/` unless noted) |
|---|---|
| Popup core | `editors/interface/regions/interface_region_popup.cc`, `interface_region_popover.cc`, `interface_region_menu_popup.cc`, `editors/interface/interface_intern.hh`, `editors/include/UI_interface_c.hh` |
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
| 4 | Tear off an enum, click items: the property changes and the highlight follows. Change the value elsewhere: it updates. Undo and redo. Delete the owning object: "Not available", no crash. Multi-column enum looks the same |
| 5 | Shift+click still pins. Shift+drag tears off and follows the cursor. Context menu entry works, including in regions without tabs. Header checkbox works. Move to a context where poll fails: "Not available", no Python errors. Modifier panels offer no tear-off |
| 6 | Compare side by side at each column count, in each shelf editor. Resize the real shelf: the tear-off doesn't change. Width survives collapse and expand. Tool switching works |
| 7 | The test matrix in the width doc. Translations and high DPI. Panel grip reflows content. Regular menus unchanged |
| 8 | The test matrix in the vertical doc, on menus as well as panels. Wheel, trackpad and thumb drag. Crop survives refresh and collapse |

Regression pass at the end: pie menus, regular popovers, dialogs, the search popup and Ctrl+click panel header.

## Delivery

- **Commits:** the merge first, then one commit per phase on `tear_off`, tagged `#6821`. Each phase compiles alone, so stopping partway is safe.
- **PR:** a single one for #6821 at the end, using the wiki title format, with a manual update and the `_misc` plan docs removed before merging.
- **Check in after Phase 1:** those fixes change the behaviour of what's already there, so test before stacking features on top.

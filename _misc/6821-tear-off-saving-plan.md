# Saving Pinned Panels in the File and Startup: Plan (#6821)

**Status:** plan only, nothing built. A test user asked for it, so this replaces the "not built" note in `_misc/6821-tear-off-completion-plan.md`.

**The request:**
- With **Load UI on**, opening a file brings back the panels pinned in that file.
- With **Load UI off**, you keep the workspaces you have, and their pinned panels.
- Save Startup File keeps pins too.
- Files must keep working in Blender.

Line numbers are from `tear_off` at `c1a16d7a8bf` and will drift.

## The idea

**Store the pins on the workspace, as a custom property.**

Blender already decides where workspaces come from, and this rule matches the request, so nothing has to check Load UI:

| Action | Workspaces come from (`setup_app_data`, `blendfile.cc:923`) | Pins you get |
|---|---|---|
| Open, Load UI on | The file | The file's |
| Open, Load UI off | Kept from the session | The ones you have now |
| Start the app, File > New | The startup file | The startup file's |
| Load Factory Settings | Factory startup | None |
| Open an old file, or one saved in Blender | The file | None, as today |
| Library or asset file | Kept from the session (treated as Load UI off) | The ones you have now |

## Blender compatibility

- **No DNA change, no versioning and no version bump.** A custom property is ordinary data that `BKE_id_blend_write` writes for every ID (`workspace.cc:136`).
- **Opened in Blender:** the pins don't appear, and the file works normally. Blender keeps the property and writes it back when it saves, so the pins are still there when the file returns to Bforartists.
- **One visible trace:** in Blender, the property shows in the Workspace tab's Custom Properties panel. Bforartists hides it there.

This comes from reading the code. I didn't find a stock Blender on this machine to confirm the round trip, so it's a hand test below.

### Alternatives ruled out

| Option | Why not |
|---|---|
| New DNA list on `WorkSpace` | Blender would drop it on save, it needs versioning code, and it adds merge conflicts every week. `CLAUDE.md` says to avoid BFA-only DNA where it can be avoided |
| On `wmWindow` | Load UI off discards the file's windows, so pins couldn't follow the workspace, and there is no idprop slot anyway |
| In Preferences | Not per file, and it can't differ between Load UI on and off |
| In a Text data-block or from Python | Visible clutter for users, and the panel state lives in C++ |

## How it works

### Storage

`workspace["bfa_tear_offs"]`: a list with one group per pin, oldest first, so they stack as they did.

| Field | Meaning |
|---|---|
| `version` | Format number. An unknown version is left alone, not read |
| `kind` | Menu, panel or enum |
| `idname` | Menu or panel type |
| `from_region` | Torn off a region, not a popover's row |
| `space`, `region`, `mode` | `tear_off_spacetype`, `tear_off_ctx_region_type`, `tear_off_mode` |
| `x`, `y` | Top left, without UI scale. `y` counts from the window's top, so a shorter window keeps pins near the top |
| `collapsed` | `tear_off_collapsed` |
| `width`, `width_default`, `width_chrome` | The width fields, already without UI scale |
| `height` | `tear_off_user_height` |
| `scroll` | `scrolloffset`, without UI scale |
| `enum_*` | ID type and name, data path and property (enums only) |

An enum can't keep `id_session_uid`, since it changes every session, so it stores the ID's name and looks it up on restore. If the ID is gone, the pin is dropped.

### Saving: three moments

`ui::tear_off_store_all(C)` writes each workspace's list from the open pins, plus any not yet restored (below). It runs at the first two moments, and the third stores one pin at a time.

1. **Before a save:** in `wm_file_write` and `wm_homefile_write_exec`, right after `BKE_CB_EVT_SAVE_PRE` (`wm_files.cc:2228`, `:2683`).
2. **Before a load:** in the first loop of `wm_file_read_setup_wm_init` (`wm_files.cc:246`), before `WM_event_remove_handlers` closes every popup. This is what keeps your pins through a Load UI off open, because every load closes them today.
3. **When the preference turns off:** in the branch of `popup_handler` that closes each pin (`interface_handlers.cc:13900`), the pin goes on the list first. Otherwise a pin restored from the file, which has already left the list, would be lost on the next save. Closing a pin with its X doesn't store it, because that's the user removing it.

Moving or pinning a panel doesn't mark the file as changed, the same as resizing an area.

### Restoring: when a workspace is shown

The stored list is a to-do list. When a workspace becomes active in a window, its entries become real pins and leave the list. The open pins are the truth after that.

This keeps restoring simple and avoids the riskiest case. A workspace that isn't showing has a screen with no laid-out regions, which is no base for creating a popup. It's also why the source's context is always real here.

- **After a load:** `wm_file_read_post` sets a flag, and the event loop handles it once the windows are ready. At startup there is no window yet when the file loads, so this can't run directly.
- **On a workspace change:** a call at the end of `ED_workspace_change`.
- **When the preference turns on:** `rna_userdef_tear_off_update` (`rna_userdef.cc:386`) sets the same flag as a load, so the pins return right away, with no need to reopen the file.
- **Creating a pin:** through the existing `WM_OT_menu_tear_off`, `WM_OT_panel_tear_off` and `WM_OT_enum_tear_off`, called with the source's area and region. They already take `source_xy`, so this adds no second way to create one. The other fields are set on the handle afterwards, then it refreshes.

### Staying on the list

Each of these stays on the list and is saved again, so nothing is lost:

- **The panel doesn't exist right now:** for example, its add-on is off.
- **The workspace has no matching editor:** it tries again on the next workspace change.
- **The preference is off:** nothing is restored and nothing is erased, including pins that were open when it was turned off. Saving writes the same list back.

## Size of the change

| Where | What | About |
|---|---|---|
| `regions/interface_region_tear_off_store.cc` (new) | Store and restore | 300 lines |
| `wm_files.cc` | Two save hooks, one load hook, one flag | 10 lines |
| `wm_event_system.cc` | Run the flag | 5 lines |
| `workspace_edit.cc` | Restore on a workspace change | 3 lines |
| `interface_handlers.cc` | Store a pin before the preference closes it | 1 line |
| `rna_userdef.cc` | Restore when the preference turns on | 3 lines |
| `wm_operators.cc` | Enums accept an ID by name | 15 lines |
| `scripts/modules/rna_prop_ui.py` | Hide the property in the Custom Properties panel | 3 lines |
| `_misc/6821-sim/` | New scenarios | 200 lines |

No changes to layout or drawing, and that one line in event handling. Almost all of it sits in one new file, so it's cheap to merge each week and easy to remove.

## Build order

Each step compiles alone and gets its own commit.

1. **Store:** write and read the list, with its validation. Nothing calls it yet.
2. **Save hooks:** check the property's contents from Python.
3. **Restore:** the flag and workspace change, for menus and row popovers.
4. **Region and shelf panels:** their width fields.
5. **Enums:** lookup by ID name.
6. **Hide the property.** Docs and manual.

## Risks

| Risk | Answer |
|---|---|
| A file asks for a panel or path it shouldn't | It only names registered types and resolves RNA paths, with no evaluation, so it runs nothing that isn't already loaded. Every field is type-checked and clamped, and a bad entry is skipped |
| Window smaller, or another monitor | `tear_off_clamp_to_window` already handles it |
| UI scale differs | Values are stored without scale, as the handle already keeps them |
| Splash at startup | `tear_off_under_regular_popup` already handles a pin under a regular popup |
| Slow startup | Only the active workspace's pins are created, which is usually a few |
| Undo | Nothing is stored during undo steps, and the code that closes popups on load isn't part of undo. To be confirmed by the test below |
| Duplicating a workspace | The copy gets entries not yet restored, but not open pins, as those are only written on save. Acceptable for a first version |
| Autosave and Recover | Autosave can write from the undo memory without running the save hook, so a recovered file can have older pins. Acceptable |

## Testing

**Scripted, in `_misc/6821-sim/`:**

| Scenario | Check |
|---|---|
| Round trip | Pin a menu, popover, region panel, shelf panel and enum. Save and open with `load_ui=True`: same place, size, crop, scroll and collapsed state |
| Load UI off | Pins from file A, open file B with `load_ui=False`: A's pins stay, B's don't appear |
| Load UI on | Same files with `load_ui=True`: B's pins appear, A's are gone |
| Workspaces | Pins on an inactive workspace appear on first switch, and only once |
| Startup | Save Startup File with a temporary config, restart: pins are back. Load Factory: none |
| Missing add-on | Pin an add-on's panel, save, disable it, open, save, enable it, open: the pin is back |
| Preference off | Open with it off, save, turn it on: the pin is back right away, and after reopening too |
| Preference off, pins restored | Open with it on so the pins restore, turn it off, save, turn it on: they're back, and after reopening too |
| Bad data | Wrong types and an unknown version in the property: no crash, and skipped |
| Undo | Pin, undo, redo: nothing moves or closes |
| Memory | No leaks under `--debug-memory` |

**By hand:**
- Save a file with pins, open it in stock Blender, save it there, and open it in Bforartists: the pins return.
- Two windows on different workspaces.
- A file from a larger monitor on a smaller one.

## Decisions for the maintainer

These have recommended defaults, and the plan assumes them unless you say otherwise.

1. **Load UI off keeps the current session's pins.** This is how I read "the workspace pinned panels". They first came from the startup file, and any you've added since stay too. The alternative is resetting to what the startup file holds, which would throw away pins you just made.
2. **Everything is saved, not only panels:** menus and enums too, because they look the same to a user.
3. **No new preference.** Load UI is already the switch. It's easy to add one later if someone asks.

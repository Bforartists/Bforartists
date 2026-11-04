# Saving Pinned Panels in the File and Startup: Plan (#6821)

**Status:** built, on `tear_off`, waiting for its hand tests. A test user asked for this. The first draft was checked against the code by independent reviews, which found one blocker and twelve major problems. Two reviews of the finished code found twenty more, all fixed (`f47662b5f49`, `53d0841ff2d`).

**Bforartists' factory default is Load UI off.** With default settings a file's own pins don't load: you keep the workspaces you have, and their pins. Pins in the startup file load at the start of a session either way. Recover Last Session follows Load UI too.

**The request:**
- With **Load UI on**, opening a file brings back the panels pinned in that file.
- With **Load UI off**, you keep the workspaces you have, and their pinned panels.
- Save Startup File keeps pins too.
- Files must keep working in Blender.

## The idea

**Store the pins on the workspace, as a system property.**

Blender already decides where workspaces come from, and this rule matches the request, so nothing has to check Load UI:

| Action | Workspaces come from (`setup_app_data`) | Pins you get |
|---|---|---|
| Open, Load UI on | The file | The file's |
| Open, Load UI off | Kept from the session | The ones you have now |
| Start the app | The startup file | The startup file's |
| File > New | Follows Load UI, as above | The startup file's, or the ones you have now |
| Load Factory Settings | Factory startup | None |
| Open an old file, or one saved in Blender | The file | None, as today |
| Library or asset file | Kept from the session (treated as Load UI off) | The ones you have now |

## Blender compatibility

- **No DNA change, no versioning and no version bump.** `ID.system_properties` is ordinary data, written, read, copied and freed for every ID like custom properties, and every 5.x version has it.
- **It isn't visible.** System properties aren't listed in the Custom Properties panel or in `keys()`, so Bforartists and Blender both show nothing, with no change to `rna_prop_ui.py`.
- **Opened in Blender with Load UI on:** the pins don't appear and the file works normally. Blender keeps the property and writes it back when it saves, so the pins are still there when the file returns to Bforartists. This comes from reading the code, so it's a hand test below.
- **A save with Load UI off** writes the session's pins, because those are the workspaces in that file.

### Alternatives ruled out

| Option | Why not |
|---|---|
| Custom properties (`id.properties`) | They show in the Custom Properties panel, in the sidebar's and Properties editor's Tool tabs, and need a change there |
| New DNA list on `WorkSpace` | Blender would drop it on save, it needs versioning code, and it adds merge conflicts every week |
| On `wmWindow` | Load UI off discards the file's windows, so pins couldn't follow the workspace |
| In Preferences | Not per file, and it can't differ between Load UI on and off |

## How it works

### Storage

`workspace.id.system_properties["bfa_tear_offs"]`: a group of groups named by a decimal counter, oldest first, so they stack as they did. Not an `IDP_IDPARRAY`, which can't remove from the middle. A file with no pins has no property.

| Field | Type | Kinds | Meaning and validation |
|---|---|---|---|
| `version` | int | all | 1. An unknown version is kept unread and saved again, for a later Bforartists |
| `kind` | string | all | `MENU`, `PANEL` or `ENUM` |
| `winid` | int | all | Preferred window |
| `space` | int | all | `tear_off_spacetype`. 0 means none |
| `region` | int | all | `tear_off_ctx_region_type`. -1 means none. No space or no region means it waits, so C code never draws with no context. A stored type that isn't found counts as no matching editor |
| `area_index` | int | all | Which editor when there are two of a type. -1 means the first match |
| `mode` | string | all | `CTX_data_mode_string`, because the enum's numbers aren't stable. Empty means none |
| `x` | float | all | `pin_x / UI_SCALE_FAC`. Finite, within ±100000 |
| `y` | float | all | `(win_h - pin_y) / UI_SCALE_FAC`, using the owner window's height, so a shorter window keeps pins near the top |
| `collapsed` | bool | all | |
| `height` | float | all | `tear_off_user_height`, ≥ 0 |
| `scroll` | float | all | `scrolloffset / tear_off_scale_fac`, restored as `stored * UI_SCALE_FAC` |
| `idname` | string | menu, panel | Within `MAX_NAME` |
| `from_region` | bool | panel | |
| `width`, `width_default`, `width_chrome` | float | panel | ≥ 0. From a very narrow shelf, `width_chrome` can be more than `width` |
| `use_context` | bool | enum | |
| `id_type`, `id_name`, `lib_name` | int, string, string | enum | A valid type, not `ID_SCR` or `ID_WM`. The library's ID name, because a file path is machine-specific. Empty means local |
| `data_path` | string | enum | Up to 1024 |
| `op_idname`, `op_propname`, `op_context` | string, string, int | enum | `op_context` clamped to its range |

**Not stored:** `tear_off_hidden`, `tear_off_scale_fac`, `tear_off_workspace` (it owns the list), hover and drag state, enum labels and session IDs, and which inner layout sections are open.

**Reading is treated as untrusted**, as a file can hold anything:
- Root, list and entry are checked as sound groups before any lookup, on the save path too. Duplicate names could hang a removal.
- Strings go through a local reader that checks the pointer, length and terminator.
- Every number is checked with `std::isfinite` and its bounds.
- A known version with invalid fields is dropped.

### Saving

`ui::TearOffSaveScope scope(bmain, wm)` sits directly around each `BLO_write_file`: `wm_file_write`, `wm_homefile_write_exec`, `WM_autosave_write` and the `quit.blend` write. Not `write_crash_blend`.

It detaches the workspace's list, attaches a temporary one (the list's entries, then the open pins), and puts the original back afterwards. **The file gets the open pins, but the session's list stays only what's still to restore.** Otherwise a save would leave open pins on the list, and they'd come back duplicated, or after you closed them.

Moving or pinning a panel doesn't mark the file as changed, the same as resizing an area.

### When pins close without being removed

Each of these puts the pin on the list first. The list then holds what would otherwise be lost:

1. **A file load**, once, before `WM_event_remove_handlers` closes every popup in `wm_file_read_setup_wm_init`. This is what keeps your pins through a Load UI off open. It runs only after the file was read, so a failed open loses nothing.
2. **The preference turning off**, in the branch of `popup_handler` that closes each pin. It goes at the front of the list, which keeps their order.
3. **A panel or menu type being unregistered**, in `refresh_or_remove_handler`: Reload Scripts, disabling an add-on, Load Preferences.

**These remove a pin for good**, as they aren't stored: closing it with the X, deleting its workspace by any route, and closing a secondary window. A pin made in a temporary window, such as Preferences, is never stored, or it would come back as junk forever.

### Restoring

The list is a to-do list. When a workspace is showing in a window, its entries become real pins and leave the list. The open pins are the truth after that.

**One route:** `ui::tear_off_restore_tag(wm)` sets `WindowManagerRuntime::tear_off_restore_pending`, and `tear_off_restore_pending_run(C, wm)` runs from `wm_event_do_notifiers`, after the depsgraph update and before drawing, so no frame shows without them. At startup there's no window yet when the file loads, so this can't run directly. Creating them inside `ED_workspace_change` would also fire inside `context.temp_override(screen=...)`.

**Tagged by:** `wm_file_read_post` (including Load Preferences), the preference turning on, `screen_change_update` (a workspace change, or leaving a maximized area), `ED_area_newspace`, the `ND_MODE` listener, a panel or menu type registering, an unregister, and any notifier except a frame change, because a poll could depend on anything. A pass costs nothing with no entries waiting.

**For each window:**
1. Skip it with no ghost window, or a temporary screen.
2. If the workspace has entries and a blocking popup such as the splash is up, or the interface is locked, keep the flag and try again next pass.
3. Set the window, and bring the screen up to date.
4. For each entry, up to 64:
   - Read it into plain values, as the list can change during the operator.
   - Resolve the area, by `area_index` if it still matches, otherwise the first match.
   - If it has a `space` and the mode differs, keep it for later.
   - Look the type up strictly in that region type, then globally. A crafted entry naming a panel from another editor could crash a C poll.
   - Call the operator with the area and region set, using `ExecDefault`, because the region variants force the window region.
   - Find the handle by comparing the newest popup before and after.
   - Set widths, height and scroll, then `tear_off_collapsed` directly, then the pin position, then clamp if collapsed. The existing refresh tag moves it into place before anything draws.
   - Look the entry up again by name and free it.

### Staying on the list

Each of these stays on the list and is saved again, so nothing is lost:

- **The panel or menu doesn't exist right now:** for example, its add-on is off. It returns when the type registers, and no error is reported.
- **The workspace has no matching editor:** it returns when one appears.
- **It was pinned in another mode:** it returns on entering that mode.
- **A menu whose poll fails.** It returns on the next change after it passes. A panel in the same situation is created and shows "Not available", as a live pin does, so its X still works.
- **An enum whose ID isn't in this file,** as with Load UI off. It returns when the ID does, such as after an append.
- **The preference is off:** nothing is restored and nothing is erased.

## Build order

Each phase compiles alone, has its own tests and gets its own commits.

| Phase | What | Status |
|---|---|---|
| 0 | Collapsed fade | Done, `993d02c194a`. Scenarios `p13_pin_fade_stale`, `p13_pin_fade_bright` and the collapse set pass |
| 1 | Store and save scope. Writes only, nothing restores yet | Done, `7c14ecfa020`, `dd2f7151fbd`, `4a8d0cce927`. Scenarios `store_*` pass, including across a restart |
| 2 | Entries that survive closing | Done, `80661d8cf07`. Scenarios `close_*` |
| 3 | Restore menus and row popovers | Done, `ddaff87d562`, `1d0b590c447`. Scenarios `restore_*`, and `restore_startup` across a restart |
| 4 | Region and shelf panels, crop, scroll, collapse | Done, `f6777df3c7f` |
| 5 | Enums | Done, `8a55802a781` |
| 6 | Docs and hand tests | Hand tests below. The manual's still to do |

**The harness gains, in Phase 1:** `SIM_CONFIG`, `SIM_FACTORY=0` and `SIM_ARGS` in `run.sh`, and a new `run_chain.sh name` for what spans a restart: it runs `name_a`, then `name_b` on the same temporary config. Tests read a file's list by opening it with the preference off.

## Risks and accepted limits

| Risk | Answer |
|---|---|
| A file names a panel, menu or path it shouldn't | It only names registered types and resolves RNA paths with no evaluation, so it runs nothing that isn't already loaded. A pin needs a real area and region, the type lookup is strict, instanced panels and context menus are refused, `ID_SCR` and `ID_WM` are rejected, and operator enums need their poll to pass. Item functions and draw code are upstream's, so one that trusts its context can still misbehave: Data Transfer's did, and was fixed |
| Window smaller, or another monitor | `tear_off_clamp_to_window` already handles it |
| UI scale differs | Stored scale-free and rounded on restore. A same-scale round trip stays exact |
| Splash at startup | Pins wait until it closes |
| Slow startup | Only the showing workspaces' pins are created, up to 64 per pass, with the rest in the next pass |
| Undo | Workspaces aren't part of memfile undo, and undo doesn't close popups. Tested in Phase 2 |
| Two windows on one workspace | Their pins merge on save, and return to the preferred window |
| Duplicating a workspace | The copy gets entries not yet restored, but not open pins. Acceptable for a first version |
| A live enum whose ID is already gone | It has no name to store, so a save drops it |
| Inner layout sections | They reset to their defaults |
| Auto-save | Goes through the same scope as saving and quitting. Not tested on its own, because the sim can't mark a file as changed. A hand test |
| Blender_Light's menu strip at rest | Stays under 3:1 over a dark viewport. Accepted |

## Decisions

Accepted by the maintainer:
1. Load UI off keeps the current session's pins, not a reset to what the startup file holds.
2. Everything is saved, not only panels: menus and enums too.
3. No new preference. Load UI is already the switch.

For the maintainer to overrule:
4. The collapsed strip rests at 60% color and 80% title, not a flat 50%. At 50%, a title over a white viewport drops to about 2.2:1 contrast. At 60% it's about 3:1. It's one constant.
5. Closing a secondary window counts as removing its pins, as the X does, because that's what it does today.

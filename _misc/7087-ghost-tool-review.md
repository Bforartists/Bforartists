# Audit: Ghost Tool

Reviewed 2026-11-24 against PR head `de1deac`, by Axleonex. Section 11 updated 2026-11-25. Split out of the closed combined proposal #7067.
Companion reviews: `7086-anim-assist-review.md`, `7088-bonecraft-review.md`.

**⚠️ How this review was done.** The code was read and cross-checked against the native Bforartists
source on `Bfa5v5.3.0`. Nothing was built or run. Every statement about runtime behaviour
(speed, undo, how crowded a header looks) is a prediction from the code and still needs a hands-on test.
Section 10 lists what was not checked.

## 1. Verdict

This is the most promising of the three and it fits where Bforartists wants to take animation: see the motion in the viewport and edit it there. Mesh onion skin and motion paths you can drag are both missing from Blender, and this PR shows how they should feel, with one or two clicks to a result and a small, careful code base. Because a Python add-on can only make ghosts by moving the playhead or adding objects to the scene, we plan to build both features natively in C++, with Ghost Tool as the reference for their behaviour. Until that ships, a reduced version with the listed blockers fixed is welcome as an opt-in add-on, and whether to do that work is your call. Either way the design will be credited!

🗒️ Future alternative plans will be submitting under the `/_misc/anim-rig` plans as markdown files.

**Changes requested. Fits the Bforartists vision and is the most promising of the three addons, but cannot merge as submitted.**

| | |
|---|---|
| What it is | Onion skin for meshes, and motion paths you can drag to edit the animation |
| Size | 30 files, 22,500 lines, 46 operators, 10 panels |
| Genuinely new for artists | About half, and it is the important half |
| Duplicates native tools | A little (motion path display, easing) |
| Point and click first | Yes, but it overloads the tool header and shadows two native hotkeys |
| BFA design standards | Partly |
| Code state | The most careful of the three, but the ghost generation method is risky |
| Recommendation | The ideas are wanted and will be built into Bforartists natively in C++ (section 11). A reduced addon with the blockers fixed is welcome until then (section 9) |

## 2. What it does

Shows where a character has been and will be, and lets the animator fix the motion in the viewport.

| Group | What the artist gets | Operators |
|---|---|---|
| Mesh onion skin | Faded copies of the deformed character before and after the current frame, by frame step or by keyframe, as wire or solid | 4 |
| Motion paths | Paths for objects and bones with key dots, frame numbers, spacing ticks and speed colouring, managed in a list | 11 |
| Editable markers | Drag a point on the path and the animation curves follow, with falloff to neighbouring frames, pinning and box select | ~10 |
| Path handle drag | Drag the curve handles of a key directly on the path | 1 |
| Draw to Keys | Turn an annotation stroke into location keys | 1 |
| Easing presets | Ease in, ease out, overshoot, anticipate, bounce on a path segment | 1 |
| Physics Feel | Preset curves (pendulum, bounce, settle) and a gravity arc suggestion | 2 |
| Diff mode | Colour overlay comparing the pose with a reference frame | 2 |
| Snapshots, export, import | Store and restore curve states, JSON files | 8 |
| Interface plumbing | Toolbar toggles, floating toolbar, separate window, a "Settings Editor (Prototype)" | ~20 |

## 3. Why we should have it

**Onion skin for 3D meshes does not exist in Blender or Bforartists.** Native onion skin is Grease
Pencil only, and armature ghosts were removed in 2.8. **Editing motion by dragging the path** does not
exist either. Both are things animators coming from other packages ask for, both are visual and
mouse-driven, and both fit the Bforartists audience well.

## 4. Redundancy

| Feature | Verdict | Note |
|---|---|---|
| Mesh onion skin | **New** | The main reason to want this addon |
| Editable markers, handle drag | **New** | The second reason |
| Motion path display | Partly redundant | Native Motion Paths exist. The addon's are live and richer, but its own path list with folders is more than needed |
| Easing presets | Partly redundant | Native interpolation and easing types. Only "apply to a path segment" is new |
| Snapshots | Partly redundant | Different from the Pose Library, but a second place to store animation states |
| Physics Feel | New, not needed | The code itself calls it a "stretch-goal" and labels it "(Preview)" |
| Draw to Keys, Diff mode | New, niche | |
| Export / import, public API | Not needed | The API is written for other third-party addons and has no user in the repo |
| Floating toolbar, separate window, Settings Editor (Prototype) | Not needed | Three more ways to show the same controls |

## 5. Pros

- Two features with no native equivalent, both aimed squarely at artists.
- One or two clicks to a result: select the character, switch on Ghosts.
- Native icons on the main buttons and good tooltips on most operators.
- The drag mode is discoverable: it is a button, the status bar explains it, Esc leaves it.
- Correct Blender 5 action handling and correct GPU shader names, no removed APIs.
- No network access, no external programs.
- Smallest and most focused code base of the three, with a documented register order and careful unregister.
- Live updates are off by default, so the cost is mostly on demand, and updates pause during playback.

## 6. Cons

### 6.1 Blockers

- **Raw memory writes into Bforartists.** `shelf_width.py:47-66` uses `ctypes` to read 448 bytes of
  the internal region struct, guesses where the width is stored, and writes a new value straight into
  memory to widen the Tool Shelf. It runs on a one-second timer for the whole session, even when the
  Tool Shelf location is not in use. The guess depends on the exact struct layout of one build, and
  that layout can change with any weekly merge. This is a crash risk and cannot ship in a bundled addon.
- **Ghosts are built by moving the playhead.** For each ghost frame the addon calls
  `scene.frame_set`, copies the mesh, and moves on (`mesh_ghosts.py:449`, `619`, `1102`).
  This re-evaluates the whole scene per ghost, fires every other addon's frame handlers, and wipes any
  pose the animator has not keyed yet. The addon knows: it snapshots the transform of every object and
  bone in the scene beforehand so it can put unkeyed poses back (`utils.py:709-760`). That is slow on
  heavy scenes and fragile exactly when an animator is mid-pose.
- **Ghosts are real objects in the user's scene.** Each ghost is a mesh object with its own material,
  in a real "GhostTool" collection (`mesh_ghosts.py:272`, `498`). They are marked hidden for render,
  but nothing removes them before saving or exporting. A save or a crash with ghosts on leaves them in
  the file, visible in the Outliner and open to being exported. Opened in Blender, the file carries the leftovers.
- **About 15 controls are added to the 3D View tool header** in Object and Pose mode, about 12 to the
  Timeline header and more to the Graph Editor (`ui_panel.py:1394-1440`). The manual admits the row
  needs scrolling in a narrow viewport.
- **It shadows two native hotkeys.** Shift+G (Select Grouped) and Shift+B (Zoom Border in the BFA
  keymap) are taken in Object and Pose mode, and a left-click entry is added to both modes for handle
  dragging (`preferences.py:385-432`, `path_handle_drag.py:302`).
- **It refuses to run in Blender.** Outside Bforartists it registers only a stub panel
  (`__init__.py:28-45`, `330-340`). A bundled addon has no need for this.

### 6.2 Should fix

- **It marks user data.** Bones get tracking custom properties and the file gets a hidden text
  datablock (`target_binding.py:31`, `110-123`).
- **Settings hidden behind press-and-hold.** Several buttons open their options only on a long press,
  which is hard to discover.
- **Display toggles land on the undo stack**, so Ctrl+Z will step through "show ghosts" clicks
  (`ui_panel.py:1685` and seven more).
- **Tied to the other two addons.** It hard-codes an Anim Assist operator name (`utils.py:677`) and
  copies `shelf_width.py` from BoneCraft.
- **No SPDX license headers** in any of the 30 files. A GPL v2 `LICENSE` text is included.
- **Folder name and metadata.** The folder is `ghost_tool`, not `bfa_ghost_tool`. There is no
  `blender_manifest.toml`, only legacy `bl_info`, which names the author as "GoingGhost", targets
  Blender 4.0 and has empty documentation and tracker links.
- **Errors are swallowed.** 91 catch-all error handlers, 15 of which drop the error silently.
- **Private development notes in the code**: "design §8 decision 15", "plan Task G1",
  "review 976236d6", and a reference to a test file that is not in the PR. No tests are included.
- **Unusual reload logic.** At every register it reloads 25 modules and deletes its own `__pycache__`
  folder (`__init__.py:50-110`), which is unnecessary for a bundled addon and fails on read-only installs.
- **Manual in the wrong place.** The PR adds a manual in seven languages under `doc/bforartists/`,
  as Markdown and PDF, with 98 screenshots through Git LFS.
- **PR housekeeping.** No CI checks ran, there is no linked issue, the title does not follow the wiki
  format, and the manual still describes the addon as on by default.

## 7. Bforartists ethos and point and click

- **Point and click:** good. The hotkeys are accelerators only, everything has a button.
- **Design standards:** partly. Icons and tooltips are mostly right, panel titles are plain text.
  Against the standards:
  - the overloaded tool header;
  - option menus that use the split layout, so checkboxes are not left-aligned (`ui_panel.py:1850`);
  - buttons without icons: "Bind to Active Target", "Save Variant", "Hide/Show", "All on/All off", "Drag Path Handle";
  - one-letter "T"/"H" text buttons in the path list;
  - labels such as "Settings Editor (Prototype)" and "Physics Suggest (Preview)".
- **Where it should live:** onion skin on/off and frame counts belong in the Viewport Overlays popover
  next to Motion Paths. Path settings belong with the native Motion Paths panel. A sidebar tab can hold the rest.
- **Colours** are addon preferences, not theme colours.

## 8. Do the controls and settings work

From the code, yes for the main features, and this addon has the fewest loose ends. Open points:

- Thick path lines use a shader that may ignore line width on Vulkan and Metal. Needs a test on both.
- Whether the playhead and the unkeyed pose are restored in every case needs testing with a real rig.
- The left-click keymap entry passes clicks through when no handle is hit, but click-select in Object
  and Pose mode should be tested with the addon on.
- Every frame change re-colours every ghost material (`mesh_ghosts.py:920`). Check scrubbing speed with many ghosts.

## 9. Recommendations



**Decision: changes requested. This is the addon we want first.** Mesh onion skin and editing motion
by dragging its path are missing from Bforartists and fit its direction. The PR cannot merge at its
current size or with the blockers below. Section 11 explains that both features are planned as native
C++ features, so a reduced addon would be the version that ships until then.

**Keep:**

- Mesh onion skin.
- Live motion paths.
- Editable markers and path handle drag.

**Fix before merge:**

1. **Remove `shelf_width.py`.** It writes into Bforartists' memory through `ctypes` on a one-second timer. That is a crash risk after any merge.
2. **Remove the Bforartists-only guard** in `__init__.py`. A bundled addon does not need it.
3. **Stop creating ghosts as scene objects.** Draw them in the viewport instead. Nothing may be left in the user's file: no objects, materials, collection, bone properties or hidden text datablock.
4. **Stop moving the playhead to build ghosts.** `scene.frame_set` per ghost wipes unkeyed poses and fires every frame handler. Capture shapes as the playhead visits frames, plus a refresh the artist asks for.
5. **Move the controls out of the headers.** Remove the additions to the 3D View tool header, the Timeline header and the Graph Editor header. Put Ghosts and Paths in the Overlays popover and the detailed options in one sidebar tab.
6. **Remove the Shift+G, Shift+B and left-click keymap entries.** They shadow Select Grouped and Zoom Border.
7. **Draw thick lines with the polyline shaders,** and test on OpenGL and Vulkan.
8. **Take display toggles off the undo stack.**
9. **Remove the hard-coded reference to Anim Assist** (`utils.py:677`) and the module reload and `__pycache__` deletion at register.
10. **Test on a production-weight character** and report playback and scrubbing speed with ghosts on.

**Remove from this PR:**

- Physics Feel, Diff mode, Draw to Keys, easing presets.
- Snapshots, export and import, the public API.
- The floating toolbar, the separate window and the Settings Editor.
- Press-and-hold option menus. Use normal popovers.

**For any resubmission:**

- Name the folder with the `bfa_` prefix, and add a complete `blender_manifest.toml` with a real maintainer and working documentation and tracker links.
- Add an SPDX licence header to every file.
- Use standard panels and layouts. Put an icon and a tooltip on every operator. Left-align checkboxes. Keep panel titles as plain text.
- Make every string translatable through `locale/po`.
- Do not add default hotkeys that replace native ones.
- Remove the manual, PDFs and translations from the source repository. Manual pages go to the Bforartists documentation.
- Remove comments that point to private notes, and remove references to tests that are not in the PR.
- Keep the addon opt-in.
- Open a tracker issue, link it, and title the PR in the wiki format: `<Type>: <Editor> > <Context> - <Title> #<issue>`.

## 10. What was not checked

- Nothing was run. No build, no hands-on test, no performance measurement.
- Whether the memory-write hack works or crashes on the current build.
- Not every button reference and not every preference was traced one by one.
- Whether every timer, handler and draw callback is removed on disable and on file load.
- Drawing on Vulkan and Metal.
- Keymap collisions were checked against the Bforartists keymap and the Blender default for the two keys named, not exhaustively.
- The manual's translations and screenshots.

## 11. Where this goes next



**Mesh onion skin and editing motion on its path will be built into Bforartists natively, in C++.**
This PR showed that both are wanted and how they should feel, and it is the reference for their behaviour.

The reason is in blockers 3 and 4. A Python addon can only make a ghost by moving the playhead or by
adding objects to the scene. Native code can evaluate the character at other frames privately, the
way native motion paths already do, and draw the result in the viewport without touching the file.

| Idea from Ghost Tool | Why native | Where it will live |
|---|---|---|
| Mesh onion skin | Other frames are evaluated without moving the playhead, so unkeyed poses are safe and no frame handlers fire. Drawn with the other viewport overlays, with nothing stored in the file | Viewport Overlays popover, next to Motion Paths. Colours in the theme |
| Live motion paths | Native motion paths are already C++. They get live updates, key dots, spacing ticks and speed colouring | The native Motion Paths panel |
| Editing motion by dragging the path | Uses the native transform tools, so snapping, proportional editing and undo work as they do everywhere else | The 3D View, on the native motion path |

**What this means for this PR.** The native features will replace the Python ones when they ship.
Until then a reduced addon that follows section 9 is still welcome as an opt-in addon. Whether that
is worth your time, knowing it is the interim version, is your call. If you would rather not, say so
and we will close the PR with thanks and credit the design.

| Ghost Tool piece | Decision |
|---|---|
| Editable motion paths, marker and handle drag | Wanted. The best gesture feature in the three PRs. Native in the long run |
| Path drawing | Wanted. Native in the long run |
| Onion skin features and options | Keep the design. Native in the long run, because of how ghosts must be made |
| Physics Feel | Not now. It returns later as part of in-between suggestions |
| Everything else | Remove |

**Two new addons are planned around that native work.** Both are small Python addons, bundled and opt-in.

| Addon | In one line | What is in it |
|---|---|---|
| `bfa_rigging` | Rig by dragging | Rig parts are assets. They are dragged from the asset shelf onto the model, snap together through sockets and fit themselves inside the mesh. Gizmos for markers and limb lengths, Build and Rebuild, guided weights, a rig check with Fix buttons, a guide panel for new users. Bipeds first, then creatures and machines |
| `bfa_animation` | Animate by touching | Pose by grabbing the mesh, pin one part and pull another, matching and mirror pairs, animation clips dragged from the asset shelf onto a rig or into the NLA, and in-between suggestions that are previewed as ghosts and written as plain keys |

**How the work is split:**

- **Native C++** for anything that has to be fast on a heavy character or has to sit inside the editors: evaluating other frames, drawing in the viewport, picking on the mesh, drop targets, menu operators.
- **Python addons** for setup and guidance: rig part recipes, the guide panel, checks, presets.

**Rules for everything in this area:**

- **Setup or handling only.** A tool either builds ordinary Blender data (bones, constraints, weights, shape keys, keyframes) or helps the artist work with it. The character never needs the addon in order to play or render.
- **Vanilla compatible.** A file opens in Blender with the addons absent and renders the same.
- **Bforartists interface standards.** Standard panels, an icon and a tooltip on every operator, left-aligned checkboxes, translations through `locale/po`.
- **Small.** Each addon stays small enough for one maintainer to read fully and carry through the weekly Blender merges.

**Timing.** None of this has started. It is on the Bforartists roadmap for 2027, after the asset and
product milestones that come first. Tracker issues will be opened when the work begins, one per
feature. Contributions are welcome from that point, as small PRs of one feature each.

# Audit: BoneCraft

Reviewed 2026-11-24 against PR head `9de42e1`, by Axleonex. Section 11 updated 2026-11-25. Split out of the closed combined proposal #7067.
Companion reviews: `7086-anim-assist-review.md`, `7087-ghost-tool-review.md`.

**⚠️ How this review was done.** The code was read and cross-checked against the native Bforartists source on `Bfa5v5.3.0`. Nothing was built or run. Every statement about runtime behaviour is a prediction from the code and still needs a hands-on test.
Section 10 lists what was not checked.

## 👀 1. Verdict

The auto-rig wizard in BoneCraft is the best single feature across all three PRs: a clear step-by-step flow with validation and rollback, artist-friendly tooltips and an extensive manual. We cannot merge the add-on as submitted because of its size, its overlap with existing tools and some blockers listed in the review. The rigging ideas are wanted, though. Marker placement, the part builders, the mechanisms and the validator are planned as the base of a new rigging add-on, where rig parts are dragged from the asset shelf onto the model and snap together. The pieces that need viewport speed, such as highlighting drop targets and posing on the mesh, are planned natively in C++. The VRChat, VRM and MMD tools would do well published as their own extension. Work is planned to start in 2027, with credit for what comes from BoneCraft.

**Close as submitted. It has blockers beyond design.** The auto-rig wizard is the best single
feature in all three PRs and is worth having on its own.

| | |
|---|---|
| What it is | Auto-rig wizard, rig tools, weights, mechanisms, plus VRChat / VRM / MMD pipelines |
| Size | 221 files, 83,800 lines, ~320 operators, 117 panels |
| Genuinely new for artists | About a third |
| Duplicates native tools | Heavily (weights, pose library, breakdowner, correctives) |
| Point and click first | Yes, the wizard is a good click-through |
| BFA design standards | No |
| Code state | Orderly structure, but dead stubs, a broken headline feature and unsafe extras |
| Recommendation | Close this PR. Placement, part builders, mechanisms and the validator are wanted in the planned `bfa_rigging` addon (section 11). Publish the VRChat, VRM and MMD tools separately. See section 9 |

## 2. What it does

A rigging suite that is really several products in one folder.

| Group | What the artist gets | Lines | Operators |
|---|---|---|---|
| Auto-rig | Wizard, Quick Rig, starter rig catalogue, mannequin, retargeting | 20,600 | ~56 |
| Advanced rigging | Rig validator, space switching, Spline IK builder, ribbons, chain dynamics, driver builder, rig notes, a viseme library | 4,900 | ~35 |
| Weights | Mirror, transfer, weight table, flood, smart automatic weights, Delta Mush and Proximity Wrap helpers, control shapes | 4,000 | ~26 |
| Animation | Its own pose library, breakdowner, Euler filter and tangent buttons, corrective shape keys, Rigify add-ons | 2,800 | ~24 |
| Control UI | Clickable picker for generated rigs, selection sets | 1,000 | ~14 |
| Bone collection panels | Coloured collections, visibility bookmarks, popup | 1,700 | ~24 |
| Mechanisms | Hinge, slide, telescope, piston, gear and follow joints for props and machines, with a sweep test | 4,600 | ~20 |
| VRChat suite | Avatar fixing, bone-name translation, mesh joining, a 4,400-line material atlas baker, eye tracking, visemes, clothing merge, hair chains, performance rank, decimation, Unity sidecar export | 20,600 | ~86 |
| VRM and MMD | Import and export through third-party addons, VRoid projects, physics conversion | 5,000 | ~25 |
| Import / Export hub | Game export profiles for Unity and Unreal, "Install All Format Bridges" | 2,200 | ~7 |
| Task board | Overview hub, task list, bone inspector | 3,300 | ~4 |
| Own translation system | Dictionaries for seven languages | 6,300 | 0 |

**The wizard, step by step:**

1. Rig Builder tab, **Start Auto-Rig**.
2. Pick the mesh from a list.
3. Choose the rig type: Body + Face, Body Only, or Face Only.
4. Place body markers: **Detect Markers** (with confidence ratings), **Guess Markers from Mesh**,
   or click each one on the mesh. Symmetry and mirror left to right are available.
5. Finger markers, then face markers.
6. Review and options: IK/FK, control shapes, twist bones, skirt bones.
7. **Generate Rig**: body, fingers, face and skin weights.
8. Optional **Build Control Rig**, then close. Cancel rolls the scene back.

## 3. Why we might want it

- **The auto-rig wizard.** Rigify starts from a metarig and assumes rigging knowledge. This starts
  from the mesh: click the markers or let it detect them, review, generate, with automatic skinning.
  That is the kind of rigging answer an artist-first application should have.
- **Mechanisms** has no native equivalent and is neatly scoped: pistons, gears and hinges for props.
- The rig validator, space switching and a simple control picker are useful smaller pieces.

## 4. Redundancy

| Feature | Verdict | Already in Bforartists |
|---|---|---|
| Auto-rig wizard with auto skin | **New** | Rigify covers generation from metarigs only |
| Mechanisms | **New** | |
| Rig validator, chain dynamics, ribbons | New | |
| Weight table | New, minor | Native shows weights for the active vertex only |
| Retargeting | New, **but broken** | See section 6.1 |
| Quick Rig, starter catalogue | Partly redundant | Rigify metarigs in Add > Armature. Only the thumbnail catalogue and one 19-bone humanoid are new |
| Control picker, Rigify add-ons | Partly redundant | Rigify generates its own rig UI |
| Space switching | Partly redundant | Rigify has parent and IK/FK switching for its own rigs |
| Bone collection panel, bookmarks | Partly redundant | Native bone collections |
| Pose library | **Redundant** | The bundled Pose Library, and this one stores poses in an incompatible way |
| Breakdowner, Delta Move | **Redundant** | Native Pose Breakdowner, Push, Relax, Blend to Neighbor |
| Euler filter, tangent buttons | **Redundant** | Native Graph Editor operators |
| Weight mirror, transfer, normalize, flood | **Redundant** | Native vertex group and weight tools, Data Transfer |
| Corrective shape keys | Redundant | Already bundled as a default add-on |
| Delta Mush, Proximity Wrap | Thin wrappers | Corrective Smooth and Surface Deform modifiers |
| Driver builder, Spline IK builder | Convenience wrappers | Native drivers and Spline IK constraint |
| Game export | Partly redundant | Native FBX and glTF exporters. Only the profiles are new |
| VRChat suite, VRM, MMD, atlas baker, bone-name translation | New, **niche** | Community pipelines, not general rigging |
| Task board | Not rigging | |
| Visemes | Duplicated three times inside the addon | And a fourth lip sync lives in Anim Assist |

About half the code is VRChat, VRM, MMD and supporting framework. Of the rest, a large part repeats native tools.

## 5. Pros

- The wizard is a well-built linear flow with validation at each step and rollback.
- Tidy architecture: each tool has a manifest and is truly unregistered when switched off.
- Every button points at a real operator (cross-checked, no dangling references).
- No telemetry and nothing that phones home.
- Downloads ask for confirmation first and show the source.
- The header-menu entries it adds follow BFA rules: an icon on each entry, plain titles.
- Mechanism tooltips are clear and written for artists.
- Extensive manual.

## 6. Cons

### 6.1 Blockers

- **Raw memory writes into Bforartists.** `core/shelf_width.py` uses `ctypes` to read 448 bytes of the
  internal region struct, guesses where the width is stored, and writes a new value straight into
  memory to widen the Tool Shelf. It runs on a one-second timer and is on by default. The guess
  depends on the exact struct layout of one build, and that layout can change with any weekly merge.
  This is a crash risk and cannot ship in a bundled addon. If a wider Tool Shelf is wanted, that is a
  small core change.
- **It downloads and runs third-party code.** The MMD and VRM "bridges" fetch whatever the *latest*
  GitHub release of two outside projects is, with no pinned version and no checksum, then install and
  enable it inside Bforartists (`mmd/bridge.py:152-157, 311-360`, `vrm/bridge.py`,
  `core/addon_installer.py`). It never checks the "Allow Online Access" preference, and the download
  blocks the interface for up to two minutes. Both projects are on the Blender Extensions platform,
  which is the proper channel.
- **Licensing and origin are unclear.** The VRChat tools credit CATS (MIT), Material Combiner
  (GPL 3 only) and UVToolkit (GPL 3 or later) and call themselves a reimplementation
  (`vrchat/cats/uv_tools/CREDITS.md`). GPL 3-only code cannot be combined with GPL 2-only, and none of
  the 221 files carries a license header, so this needs a clear written statement from the author.
  The code was not compared against the originals.
- **Third-party franchise content in the manual.** Chapter 12 is a 52-screenshot tutorial rigging
  "Crescent Rose", a weapon from RWBY. The manual credits the fan model (CC BY 4.0, Sketchfab) and
  states the design belongs to Rooster Teeth. That should not ship in Bforartists documentation.
- **Retargeting does not work on Bforartists 5.** The function still writes animation with the API
  that Blender 5 removed. A guard was added to return early, but it was pasted *inside the function's
  description text*, so it never runs (`autorig/retarget.py:559-565`). The manual presents retargeting
  as working. This is also the clearest sign that changes went in without being read or run.
- **It switches itself off outside Bforartists.** `bfa_guard.py` checks the host at start, then
  re-checks every ten minutes and unregisters the whole addon at runtime if the check fails
  (`__init__.py:297-319`). A bundled addon has no need for this, and a renamed or portable install
  could trip it.
- **Scope.** A VRChat avatar pipeline is a legitimate product, but it is a community-specific
  extension, not a core rigging feature for every Bforartists user.

### 6.2 Should fix

- **It replaces parts of the interface system.**
  - `core/wrap_layout.py` swaps out the draw function of every panel in its tabs to re-flow buttons.
  - Panels are mirrored into the Properties editor: 18 extra panels in Object Data and Scene.
  - A preference moves tabs between the left and right side.
- **Its own translation system.** 934 strings go through a private dictionary chosen by an addon
  preference. The panels ignore the Bforartists interface language and cannot use `locale/po`, so the
  BFA translation workflow does not apply.
- **Three sidebar tabs and 117 panels.** One tab is named "CATS", which clashes with the real CATS addon.
- **Blank panel names.** Most panels use `bl_label = " "` and draw the title by hand, which breaks
  panel search and translation.
- **Icons on about 55 % of operator buttons** (173 of 317), tooltips written for about 30 % of operators.
- **Naming.** The product is BoneCraft, the folder is `boneforge`, all 337 operators are `boneforge.*`,
  and class prefixes mix `BF_` and `BC_`. BFA core addons use the `bfa_` prefix. There is no
  `blender_manifest.toml`, and documentation and tracker links are empty.
- **Dead weight:**
  - three stub files kept "because the filesystem layer cannot delete files";
  - about 50 operators with no button;
  - 27 `enable_*` preferences that look unused;
  - internal changelogs shipped in the addon folder;
  - comments that refer to private notes ("BF-DATA-01", "R3", "spec §7.1").
- **It deletes `__pycache__` folders inside the install directory** on reload
  (`core/lifecycle.py:239-312`), which fails on read-only installs.
- **Errors are swallowed.** 255 catch-all error handlers, and registration continues after a failure,
  so the addon can end up half-loaded without telling anyone.
- **Three chord hotkeys** (Ctrl+Shift+B, D, R). No collision found in the BFA keymap, but BFA prefers single plain keys.
- **No tests** are included, although comments describe modules as unit-tested.
- **Manual in the wrong place.** The PR adds a 12-chapter manual in seven languages under
  `doc/bforartists/`, as Markdown and PDF, with 156 screenshots through Git LFS.
- **PR housekeeping.** No CI checks ran, there is no linked issue, the title does not follow the wiki
  format, and the manual still describes the addon as on by default.

## 7. Bforartists ethos and point and click

- **Point and click:** good. The wizard is a guided click-through and nothing is hotkey-only.
  The Ctrl+Shift+R popup also has a menu entry.
- **Design standards:** fails, mainly because it brings its own layout engine, its own translation
  system and its own tab management instead of using what Bforartists provides.
- **Less is more:** the opposite. Three tabs, 117 panels, a mirrored Scene tab, a task board and a
  12-chapter manual.
- **Menus it adds to:** Add > Armature, the Pose context menu (at the top), the Object menu, and the
  BFA Pose and Weights Tool Shelf tabs.

## 8. Do the controls and settings work

- Retargeting: no, see 6.1.
- The wizard, mechanisms and validator read as complete. Needs a hands-on run on a real character.
- About 50 operators have no button, and the `enable_*` preferences probably do nothing.
- Left-aligned checkboxes: no consistent pattern found. Needs a look in a build.
- The performance-rank tool recalculates on every scene update. Whether it is throttled was not confirmed.

## 9. Recommendations



**Decision: close this PR.** It cannot merge in this form. About half of it is VRChat, VRM and MMD
pipelines, much of the rest repeats native tools, and it has blockers that are not about design.
The auto-rig work and the mechanisms are wanted and should come back as contributions to the rigging addon.

**Blockers. None of these may appear in a resubmission:**

1. **`core/shelf_width.py`.** It writes into Bforartists' memory through `ctypes` on a one-second timer.
2. **The MMD and VRM installers.** They download the latest release of outside projects with no pinned version and no checksum, install and enable it, ignore the "Allow Online Access" preference, and block the interface while downloading.
3. **`bfa_guard.py` and the ten-minute re-check** that unregisters the addon at runtime.
4. **Code of unclear origin.** State in writing where the `vrchat/cats/` code and `assets/quick_rigs.blend` come from. The credits name a GPL 3-only project.
5. **The Crescent Rose chapter** and its screenshots. Franchise content cannot ship in Bforartists documentation.
6. **Broken retargeting.** The Blender 5 guard in `autorig/retarget.py:559-565` sits inside the function's description text and never runs. Fix it for Blender 5 actions or leave retargeting out.

**Wanted, as new contributions once the rigging addon is open (section 11):**

- Marker detection and placement.
- The part builders: limb, spine, tail, digit, face, foot, spline.
- Mechanisms: hinge, slide, telescope, piston, gear, follow.
- The rig validator, including the sweep test.
- Skin generation, if it beats native automatic weights in a side-by-side test.

**Not accepted:**

- Tools that repeat native ones: pose library, breakdowner and Delta Move, Euler filter and tangent buttons, weight mirror, transfer, normalize and flood, corrective shape keys, the Delta Mush, Proximity Wrap, driver and Spline IK wrappers.
- The control picker. Posing directly on the mesh replaces it. Though the addon could introduce a new synoptics system.
- The task board, bone inspector and rig notes.
- The private layout engine (`core/wrap_layout.py`), the panels mirrored into the Properties editor, and the tab mover.
- The private translation dictionaries. Use `locale/po`.
- The three stub files, the operators with no button, the unused `enable_*` preferences and the internal changelogs.

**Publish separately:**

- The VRChat, VRM and MMD tools, including the material atlas baker, belong on the Blender Extensions platform under your own name. There the VRM and MMD add-ons can be declared as dependencies and no installer is needed.

**Fix in whatever is resubmitted:**

1. **Use one name.** The product is BoneCraft, the folder is `boneforge` and every operator is `boneforge.*`.
2. **Give every panel a real name.** `bl_label = " "` breaks search and translation.
3. **Give every operator an icon and a tooltip.** About 45 % have no icon and 70 % have no written tooltip today.
4. **Do not delete files in the install folder** on reload.
5. **Report errors,** and do not continue registering after a failure.
6. **Include the tests** the comments refer to, or remove the claims.

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

- Nothing was run. No build, no hands-on test.
- Whether the memory-write hack works or crashes on the current build.
- Whether any code was copied from CATS or Material Combiner. Only the credits were read.
- Where `assets/quick_rigs.blend` comes from (it is an LFS file and was not opened).
- Whether the Unity and Unreal bone-name maps copy engine assets.
- Checkbox alignment panel by panel.
- Whether every timer and handler is removed when the addon is disabled or a file is loaded.
- Whether each of the roughly 50 unreferenced operators is truly unreachable.
- Keymap collisions were checked against the Bforartists keymap, not against every Blender default.
- The manual's translations and screenshots.

## 11. Where this goes next



Bforartists is planning its rigging work around the viewport and the asset shelf. The rigging addon
is not a wizard. **Rig parts are dragged from the asset shelf onto the model, snap together through
sockets, and fit themselves inside the mesh.** A small guide panel helps new users, and the options
of each part use the asset wizard system Bforartists already has.

**Some of this will be built into Bforartists natively, in C++,** where speed or a place inside the
editors matters:

| Idea | Why native | Where it will live |
|---|---|---|
| A wider Tool Shelf | The addon does this by writing into memory (blocker 1). As a native setting it is a small, safe change | Preferences |
| Dropping a rig part onto the model | The part under the cursor and the socket it will snap to have to light up while dragging, at viewport speed | Asset shelf and 3D View |
| Posing on the mesh, which replaces the control picker | Hovering has to highlight the right part of a heavy character without delay | 3D View, Pose Mode |
| Animation clips as assets, the home for retargeting later | Dropping a clip onto a rig or into the NLA needs drop targets that only the editors themselves can provide | Asset shelf, 3D View and NLA |

**The rest goes into a new addon:**

| BoneCraft piece | Decision |
|---|---|
| Marker detection and guessing | Rigging addon, as the smart placement behind drag and drop. Needs a hands-on test first |
| Part builders | Rigging addon, as the reference for light part recipes |
| Mechanisms | Rigging addon, as utility parts with sockets and simple 0 to 1 controls |
| Wizard flow | Rigging addon, as the guide panel |
| Skin generation | Rigging addon, only if it beats native automatic weights |
| Rig validator and sweep test | Rigging addon |
| Chain dynamics | Not ported. It needs a script running during playback. The simulated chain will be set up on Blender's own cloth and baked to keys |
| Retargeting | Later, with the clip library, after the Blender 5 fix |
| Control picker | Not accepted initially, but maybe a new editor could be built for this |
| Visemes (three systems) | Not now. One shared system is planned for a late phase |
| VRChat, VRM, MMD, atlas baker | Publish separately |
| Everything else | Not accepted |

**Every rig the addon builds must meet these rules:**

- **Light and simple.** Mostly bones and constraints, few or no drivers, no more than four levels deep.
- **Modular.** Each part attaches to the nearest compatible parent socket on build.
- **Flexible.** A few markers move everything. Markers can be switched back on for a built rig, and a rebuild keeps the animation.
- **Consistent.** One colour scheme, one set of control shapes and one bone collection layout on every rig.
- **Described.** Each part writes the shared rig description, so the animation addon's posing, pins and mirroring work on these rigs.

Measure the existing part builders against the first rule before porting them.

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

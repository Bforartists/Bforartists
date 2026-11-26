# Audit: Anim Assist
Reviewed 2026-11-24 against PR head `a44792c`, by Axleonex. Section 11 updated 2026-11-25. Split out of the closed combined proposal #7067.
Companion reviews: `7087-ghost-tool-review.md`, `7088-bonecraft-review.md`.

**⚠️ How this review was done.** The code was read and cross-checked against the native Bforartists
source on `Bfa5v5.3.0`. Nothing was built or run. Every statement about runtime behaviour
(speed, undo, how crowded a header looks) is a prediction from the code and still needs a hands-on test.
Section 10 lists what was not checked.

## 1. Verdict

Thank you for this. Anim Assist makes it clear how much everyday animation work in Blender is slowed down by operators hidden in menus, and it fills three real gaps: matching, mirror pairs and proxy bake sessions. We read the code closely and every button points at a working operator, with no network access and a hotkey that is free in our keymap.

I will _not_ be merging it as one large add-on, because much of it overlaps tools Bforartists already has. Its best ideas are going onto our roadmap instead. Ripple and gap retiming, live motion paths and a new tabbed Tool Shelf for the Dope Sheet, Graph Editor and NLA are planned natively in C++, and matching, mirror pairs and proxy baking are planned for a new animation add-on or integrated operators. Work is planned to start in 2027 after asset and product milestones, and you will be credited for the ideas that came from here! For spearheading the initiative.

While the initiative is good, some of the execution for the UX could either be improved, or better built in natively for performance, consistency and integrated UX sake (to feel less redundant or aggregate). So I went ahead and started a series of plan docs for an animation and rigging milestone to work on throughout next year for Bforartists, where some of it could be more performant and stable if done in C++ instead of Python.

👀 TLDR: Some of these key features could be developed as a tier based feature campaign or granular feature developed per operator built into Bforartists natively, with new tabbed toolshelves in animation editors, powerful viewport overlays and modal operators, smart rigging assets, or a consolidated features with a new Animation / Rigging addon built from these ideas.

🗒️ Future alternative plans will be submitting under the `/_misc/anim-rig` plans as markdown files.

**Close as submitted. Three of its tool groups are wanted and should come back as contributions to the animation addon.**

| | |
|---|---|
| What it is | Keyframe, timing, breakdown, matching, mirroring, baking, layers and lip sync tools |
| Size | 214 files, 66,900 lines, ~400 operators, 39 panels |
| Genuinely new for artists | About a third |
| Duplicates native tools | Heavily (graph and pose sliders, interpolation, bake, paths) |
| Point and click first | Mostly, but the main toolbar is a custom-drawn overlay, not real buttons |
| BFA design standards | No |
| Code state | Works on paper, heavy with scaffolding, unfinished parts |
| Recommendation | Close this PR. Matching, mirror pairs and proxy bake are wanted in the planned `bfa_animation` addon, retiming as native operators. See sections 9 and 11 |

## 2. What it does

A large animation toolbox. It adds:

- a custom tool row along the bottom of the Timeline, grouped into the stages All, Block, Spline, Polish and Deliver;
- sidebar tabs in the Dope Sheet, Graph Editor, NLA and 3D View;
- extra button strips in the Dope Sheet, Graph Editor and 3D View headers;
- a section in Scene Properties, header menus and an optional pie menu.

| Group | What the artist gets | Operators |
|---|---|---|
| Key and channel helpers | Select visible, first or last keys, grow selection, set key type, isolate channels, tag keys | ~45 |
| Breakdowns | 25 / 50 / 75 % buttons, weighted breakdown, favour previous or next, push and pull, drag breakdown, masks, presets, pose compare | ~36 |
| Offsets | Offset keys or a pose with falloff and mirroring, repeat or invert the last offset | ~23 |
| Trajectory | Motion trail overlay with arc problem highlighting | ~11 |
| Retiming | Move, scale, insert and remove time, ripple, close gaps, spacing presets | ~38 |
| Proxies and bake | Locator proxies, bake sessions, smart bake, key reduction | ~48 |
| Matching | World, parent and target matching, IK/FK switch detection and compensation | ~53 |
| Mirror | Mirror pose, swap sides, match the opposite side, automatic left/right pair detection | ~43 |
| Animation layers | Offset layers over an action with weight, mute, solo, merge and flatten | ~31 |
| Lip sync | Audio to mouth shapes on shape keys or bones, optionally through the external Rhubarb program | ~15 |
| Curve tools | Blend to neighbour, ease, push and pull, smooth, batch interpolation and handle type | ~10 |
| NLA and drivers | Arrange clips, bake keeping the stack, driver inspector | ~18 |
| "Orchestration" | User macros, quick shelf, profiles, snapshots, audit, diagnostics, recovery, deep uninstall | ~70 |

## 3. Why we might want it

Bforartists animation tooling has gaps, and three of these groups fill them with no native equivalent:

- **Matching** that works on any rig. Today only Rigify rigs get IK/FK snapping.
- **Mirror-pair tools**: swap sides and match the opposite side, with pair detection.
- **Proxy bake sessions** for working through constraints and IK.

Ripple and gap retiming is a smaller fourth candidate.

## 4. Redundancy

| Group | Verdict | Native tool that already does it |
|---|---|---|
| Curve tools (blend, ease, push/pull, smooth) | **Redundant** | Graph Editor sliders: Blend to Neighbor, Blend to Default, Blend Offset, Ease, Push Pull, Gaussian and Butterworth Smooth |
| Batch interpolation, handle type, key type | **Redundant** | Native interpolation, handle type and keyframe type operators. The addon even hides its own copies on Bforartists (`ui/headers.py:34`) |
| Breakdowns | Mostly redundant | Pose Breakdowner, Push, Relax, Blend to Neighbor, Graph Breakdown. Extra: fixed percent buttons, masks, presets |
| Trajectory overlay | **Redundant** | Native Motion Paths, and the same author's Ghost Tool |
| Retiming | Partly redundant | Native insert and remove frames (already in the BFA Timeline), time scale, snap. Extra: ripple, gaps, spacing presets |
| Bake | Partly redundant | NLA Bake, Bake Channels, Bake Keys, Decimate, Clean. Extra: proxies and sessions |
| Key selection helpers | Partly redundant | Native select before/after, column, box. Extra: grow, visible-only, tags |
| NLA tools, driver inspector | Partly redundant | Native NLA operators and Drivers editor |
| Offsets | Mostly new | |
| Matching | **New** outside Rigify | |
| Mirror pairs | Mostly new | Paste Flipped and Select Mirror cover the basics |
| Animation layers | New, but a name clash | Blender 5 has its own layered actions. A second, different "Animation Layers" will confuse |
| Lip sync | New, out of scope | BoneCraft also ships three viseme systems of its own |
| Macros, profiles, audit, recovery, help browser | Not animation tools | |

By operator count, well over half the addon either repeats a native tool or is housekeeping.

## 5. Pros

- Fills three real gaps (matching, mirror pairs, proxy bake).
- Every button points at an operator that exists (cross-checked: no dangling references).
- Uses the Blender 5 slotted-action API through one compatibility layer and avoids removed APIs.
- No network access.
- The pie hotkey is off by default and uses a key (Shift+Alt+D) that is free in the BFA keymap.
- The Timeline overlay takes its colours from the theme.
- Header additions are tracked and removed on disable.
- Has unit tests, though only for ten pure-maths modules. No operator, UI or curve tool is tested.

## 6. Cons

### 6.1 Blockers

- **The Timeline tool row is not a real toolbar.** It is drawn by hand on top of the Timeline with its
  own click detection (`ui/timeline_overlay.py:1383`). To make that work the addon:
  - listens to every mouse move and left click in the whole window through Screen keymap entries (`:1388-1396`);
  - keeps a hidden always-running operator per window, restarted by a one-second timer (`:1291-1316`);
  - moves the user's area dividers by itself to make the Timeline taller (`:1266-1288`).

  Its buttons are drawn text with no icons, are not affected by BFA layout rules, and do not get native
  tooltips, so the addon draws its own. This is the opposite of what Bforartists stands for.
- **Native duplicates.** See section 4. The earlier request on #7067 to remove redundant tools has not been applied.
- **Origin unclear.** The first line of the addon says it "complements Animaide", the curve tools
  carry the comment `AnimAide "Tween Machine"` (`operators/curve_tool_ops.py:355`), and
  `core/p4_falloff.py:12` mentions an "excluded Animaide" category. Whether any of it derives from
  AnimAide code needs a statement from the author.
- **Files stop being portable.** Lip sync creates scripted drivers that call a function only the
  addon provides (`core/p12_driver_engine.py:185`). Opened in Blender, or with auto-run scripts off,
  those drivers are broken.
- **It refuses to run in Blender.** `register()` raises an error outside Bforartists
  (`__init__.py:101`), and the manifest tagline says "not compatible with standard Blender" while
  declaring Blender 4.2 as the minimum version. A bundled addon has no need for this guard.
- **No SPDX license headers** in any of the 214 files, and a placeholder maintainer:
  `Developer <dev@example.com>`. A GPL v2 `LICENSE` text is included.

### 6.2 Should fix

- **Three native headers get extra button strips by default**: Dope Sheet, Graph Editor and 3D View.
- **A "?" button after nearly every tool**, feeding a private help browser built from twelve files and
  5,400 lines, while 123 operators have no normal tooltip.
- **Icons are missing on about 60 % of operator buttons** in the panels (114 of 291 have one).
- **Roughly 10,000 lines exist to manage the addon itself**: recovery, audit, leak checks,
  zombie-class purging, migration, deep uninstall. That this is needed says the addon does not trust
  its own registration.
- **Unfinished parts:**
  - 36 operators are defined but never drawn anywhere, including layer solo, mute and lock, macro
    steps and viseme capture, which the manual documents;
  - the `enable_layers` preference does nothing;
  - `ui/pie_menus.py` is never loaded, so its two pies never exist;
  - pivot and trajectory modes are commented out as "not yet implemented".
- **Lip sync** blocks the interface for up to two minutes while the external Rhubarb program runs,
  and the manifest does not declare that it launches a program.
- **Errors are swallowed.** 262 catch-all error handlers, 51 of which drop the error silently, so a
  failing tool often does nothing and says nothing.
- **Folder and file names.** The folder is `B4_anim_assist`, not `bfa_*`. Files are named by
  development phase (`p2_` to `p12_`), and comments refer to private notes ("R2 audit fix").
- **Manual in the wrong place.** The PR adds a manual in seven languages under `doc/bforartists/`,
  as Markdown and PDF, with 325 screenshots through Git LFS.
- **PR housekeeping.** No CI checks ran, there is no linked issue, and the title does not follow the wiki format.

## 7. Bforartists ethos and point and click

- **Point and click:** every tool is reachable from a panel, menu or the Timeline row, and nothing is
  hotkey-only. In that narrow sense it passes. Modal tools show their controls in the status bar in
  the modules checked.
- **Design standards:** it fails.
  - The headline feature bypasses the UI system.
  - Icons are incomplete.
  - Section labels inside panels carry icons.
  - Internal words leak into tooltips and search: "P7 session", "Zombie", "Safe Disable", `p10_leak_check`.
  - The same action is offered in up to five places.
- **Less is more:** 39 panels, a 96-tool catalogue and five stages on first enable is overwhelming.

## 8. Do the controls and settings work

From the code, the main tools should function. Things to expect trouble with:

- Features in the manual with no button (see unfinished parts above).
- Failures that show nothing, because errors are caught and dropped.
- The diagnostics panel reads `target.fcurves` directly in two places
  (`operators/diagnostics_ops.py:32`, `ui/diagnostics_panel.py:60`), which may fail on Blender 5 actions.
- 118 operators have no undo flag. Many are read-only reports, but they were not audited one by one.
- Left-aligned checkboxes: the addon never sets its own alignment, so this depends on the host. Needs a look in a build.
- "Deep uninstall" deletes the addon's own sound strips and speakers from the file. It only touches
  items with the addon's name prefix, but it is a data-deleting button worth testing.

## 9. Recommendations

**Decision: close this PR.** The addon cannot merge in this form, and reducing it in place is not
practical: well over half repeats native tools or manages the addon itself. Three parts are wanted
and should come back as contributions to the animation addon.

**Wanted, as new contributions once the animation addon is open (section 11):**

- **Matching:** IK/FK, world, parent and target match, with switch compensation.
- **Mirror pairs:** mirror, swap, match the opposite side, with pair detection.
- **Proxy bake:** work in a temporary space and bake back to plain keys.

**Wanted, natively:**

- Ripple and gap retiming, as native C++ operators in the Dope Sheet menus. See section 11.

**Not accepted:**

- The Timeline tool row. It is drawn by hand with its own click detection, listens to every mouse move in the window, runs a hidden operator per window and moves the user's area dividers.
- The button strips in the Dope Sheet, Graph Editor and 3D View headers.
- Tools that repeat native ones: blend to neighbour, ease, push and pull, smooth, breakdown percentages, batch interpolation, handle type, key type, the trajectory overlay.
- Macros, profiles, snapshots, audit, diagnostics, recovery and deep uninstall.
- The help browser and the "?" buttons. Use tooltips.
- Animation layers. Blender 5 has layered actions, and a second system with the same name will confuse.
- Lip sync. It blocks the interface while an external program runs, and its scripted drivers break the file in Blender.

**Fix in whatever is resubmitted:**

1. **Remove the Bforartists-only guard.** `register()` must not raise an error in Blender. We don't want to trip anything, as Bforartits is Blender at the end of the day.
2. **Write only plain keyframes** on the rig's normal controls. No scripted drivers, no helper data left in the file. This will allow 1:1 rendering with Blender and Render Farms.
3. **State in writing how this code relates to AnimAide.** The source refers to it in three places but it's not clear how we are targetting these tools. We may be able to hit these goals with better graph editor and dopesheet gizmos and better animation handling in the 3D Viewport.
4. **Give every operator a button, an icon and a tooltip.** 36 operators have no button and 123 have no tooltip today.
5. **Report errors.** Remove the handlers that catch an error and drop it.
6. **Name files for what they do,** not by development phase.

**For any resubmission:**

- Check the new milestone tasks for animation and rigging I'll start building soon - then we can contribute in a granular way.
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
- Whether the 36 unreferenced operators are reachable some other way (for example through the Timeline catalogue's dispatch).
- Whether every timer and handler is removed when the addon is disabled.
- How crowded the headers look at normal widths, and the cost of redrawing the overlay with many keys.
- Whether any code was copied from AnimAide. Only the comments were read.
- Keymap collisions were checked against the Bforartists keymap, not against every Blender default.
- The manual's translations and screenshots.

## 11. Where this goes next

Bforartists is planning its animation work around the viewport: see the motion, touch the character, spend less time in the Dope Sheet and Graph Editor. Anim Assist is built the other way round, as more buttons for the animation editors, which is why most of it is not accepted. The parts that are wanted are the ones that make posing in the viewport work.

**Some of these ideas will be built into Bforartists natively, in C++,** where speed or a place
inside the editors matters:

| Idea from Anim Assist | Why native | Where it will live |
|---|---|---|
| Ripple and gap retiming | They belong beside the native insert and remove frame operators, with the same undo and the same behaviour in every animation editor | Dope Sheet and Timeline menus |
| Motion trail with arc highlighting | Native motion paths are already C++. They get live updates, spacing ticks and speed colouring, and can be edited by dragging | The native Motion Paths panel and the 3D View |
| Quick access to common key, channel and marker operators | A large part of Anim Assist is a faster route to operators that already exist in the header menus. A tabbed Tool Shelf, like the one in the 3D View, solves that for every operator | A new Tool Shelf in the Dope Sheet, Graph Editor and NLA |
| Seeing neighbouring poses while posing | Mesh onion skin, evaluated without moving the playhead | Viewport Overlays popover |

**The rest goes into a new addon:**

| Anim Assist piece | Decision |
|---|---|
| Matching | Animation addon, with pins. Later the base for full body posing |
| Mirror pairs | Animation addon. Pair detection also feeds the shared rig description |
| Proxy bake sessions | Animation addon, simplified. Always baked back to plain keys |
| Ripple and gap retiming | Native operators |
| Lip sync | Not now. One shared system is planned for a late phase. It must write plain keys, with no scripted drivers |
| Everything else | Not accepted |

Each contribution should read which controls belong together from the shared rig description where a
rig has one, and fall back to its own detection where not.

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

# 12.11.2 Lipsync setup compatibility

- Set up the speaker sound strip with current or older Sequence Editor collections.
- Create the first strip in an empty editor and keep occupied channels clear.
- Local candidate; publication is pending.

# 12.11.1 Timeline Undo history

- Find and native menu actions use the underlying tool's native Undo entry, avoiding a second entry for the same edit.
- Direct canvas actions retain their required checkpoint. Slider completion and cancellation keep their existing handling.

# 12.11.0 Adaptive Drivers editor

- Drivers mode has its own Driver & Target, Variables & Expression, Response Curve, and Diagnostics sections. Its Anim Assist header menu follows the same layout.
- Inspect the active driver and its driven property; frame curves, select channels or the owning object, and mute or lock the active driver.
- Open the native Drivers and Modifiers tabs for variables, expressions and modifier settings.
- Edit interpolation, selected handles and extrapolation only on selected visible editable driver channels. Add modifiers only to the active editable driver. Action keys and unrelated drivers are excluded.
- Check selected visible drivers for evaluation errors, missing targets, unresolved property paths and missing bones. Refresh owner dependencies without automatic repairs or deletion.
- Existing Action Graph, Dope Sheet, NLA and Timeline layouts are preserved. Switching out of Drivers mode restores the Action Graph sections.

# 12.10.3 Timeline hover help and performance

- Show one Anim Assist tooltip in the Timeline under the cursor. Toolbar hover takes priority over the Scene Strip Gizmo beneath it.
- Keep hover help, stage choices, and slider popouts above the toolbar buttons.
- Reuse toolbar layout and key selection checks, and skip redundant slider previews and pose updates.

# 12.10.2 Fixed Timeline toolbar height and clicks

- Keep the toolbar buttons and their click areas at full height. The Timeline divider pulls back up when released below the minimum height.
- Handle toolbar clicks before they can move the playhead or select keys underneath.
- Close Toolbar Settings when you click outside it.

# 12.10.1 ? Timeline toolbar click targets

- Reserve space above the native horizontal scrollbar as the Timeline is resized.
- Grow the buttons and their click areas together when the Timeline is tall enough.
- Keep stage choices inside the usable canvas on a short Timeline.

# 12.10.0 — Stage toolsets

- Block, Spline, Polish and Deliver each have their own toolset on the bottom
  Timeline row. Each starts from a fixed default set: the Recommended tools for
  its families plus phase-specific ones (for example Inbetween, Push/Pull and key types
  in Block; To Spline, Neighbors, Ease, reference tools, handle types and
  Show/Hide Trails in Spline; spacing presets, Timing Offset, Ripple and Snap in
  Polish; Bake Preview Range, Smart Bake, Reduce, Bake Keys to Integer Frames,
  One-Click Proxy & Bake, the four proxy types and Remove All Proxy Sessions in
  Deliver).
- Stage families: Spline starts with Curves and Motion (arc checking), Deliver
  with Bake. These are each stage's home families; any row can also hold tools
  from other families.
- Bake Preview Range, Bake Keys to Integer Frames, One-Click Proxy & Bake,
  Remove All Proxy Sessions, To Spline and To Stepped join the Timeline
  catalogue (95 actions).
- Row labels: Set Reference, To Reference, Amplify (was Push/Pull), Show Trails
  Location Proxy, Rotation Proxy and Clamped (Auto Clamped).
- Scales and icons (version B): Block's Breakdown slider carries stage presets
  -25/25/50/75/125, replacing the 25/50/75% and Push/Pull Prev/Next buttons on the
  row (same results at default strengths); Polish's Timing Scale becomes an
  inline slider with presets 80/90/110/120, replacing the spacing buttons. Stage
  presets may exceed the standard range up to the tool limit; All keeps its
  own presets. Icons for grow, Copy/Paste, To Spline, handle types (theme handle
  colours) and nudges; Show/Hide Trails become one Trails eye toggle (96
  actions).
- Compact All row (Recommended): 25/50/75 as ticks on Breakdown; -1f/+1f,
  Copy, Paste, Mirror, Bake Object and the Trails eye as icons, so the row is
  about 200 px shorter. Tool Settings gains Presets as Ticks for any
  slider, in All and in stages. Saved or edited layouts keep their All row.
- Compact rows: stage sliders draw presets as click ticks on a wider track
  (the drag snaps onto ticks; a popout falls back to preset buttons). Icons for
  Inbetween, Distribute, Set Reference, Opposite, Mirror, Mirror Active, Swap,
  Bake Object and the four proxy types. Spline shows To Reference and Amplify
  inline. Every stage row fits 1,397 px with all tools and named sliders.
- Reduce and Ripple become sliders with live preview (ten numeric tools): Deliver
  shows Reduce with presets 0.001/0.01/0.05, Polish shows Ripple with -1/1; the
  0.01 and 1 presets equal the old buttons. Fixed: cancelling a preview that had
  removed keys crashed Bforartists; the slider now rebuilds the curve's keys.
- Block shows Mark Key/Breakdown/Extreme/Hold as key-type diamonds in the
  theme's Dope Sheet key colours and relative sizes. Icon is offered only for
  tools that have one (key types, nudges, Copy, Paste); an Icon choice saved on
  another tool shows its name.
- Fixed: icons of unavailable row tools (nudges, Copy, Paste in Icon mode) were
  drawn at full strength instead of faded.
- A tight row first shortens inline slider tracks and keeps their names; names
  are dropped only when that still does not fit.
- Fixed: hover text on the Timeline row kept only three lines, so longer
  descriptions (often the reason a tool is greyed out) were cut off. It now shows
  the full text as short lines: name, what it does, why it is unavailable (in
  orange), what it works on and what it needs. It widens to fit and stays clear
  of the playhead.
- Fixed: One-Click Proxy & Bake flattened the object's motion (the proxy did not
  move) and removed every helper of an open proxy session. It now records the
  object's world motion on the proxy before baking and works in a session of
  its own.
- The row sits above the Timeline's horizontal scrollbar instead of under it, and
  when it reaches the Timeline's left or right edge (channels or sidebar closed) its
  end buttons are inset from Blender's area corner handles, so clicks on All and
  Settings land on the buttons.
- Family and More lists are drawn by the add-on: one click opens them, they stay
  open while the pointer moves, a click runs a tool, and clicking the same button,
  anywhere else or Esc closes them. A clicked popout slider stays open; double-click
  or click away applies, Esc cancels.
- When the row is tight, the single stage button opens a stage list: one click
  opens it and it stays open while you hover; click a stage to switch. Clicking
  the button again, clicking elsewhere or pressing Esc closes it. A short
  Timeline shows the five stages as one row above the button instead. Ctrl+Wheel
  still cycles.
- Toolbar Settings edits one row at a time: the Row dropdown (All, Block,
  Spline, Polish, Deliver) picks the row, and the Timeline switches to it.
  Every row lists all 96 tools, grouped under family headers (Tween, Timing,
  Curves, Keys, Pose, Bake, Motion) that open and close and show how many of
  their tools are on the row; a stage opens on its home families. Find filters
  by name. Add any tool to any row, or take a default off it: set it Hidden,
  Button, Popout or Inline, and move it up or down within its family. A tool
  from another family brings its family menu onto the row. Changes apply to the row at once, with no OK button: click outside or
  press Esc to close and keep them, or Revert Changes to undo everything since
  the dialog opened. Reset <Stage> to Defaults restores one stage; Restore
  Recommended restores all.
- Saved layouts store All and all four stages together. Amounts (range,
  default, presets, width and so on) stay shared by every stage.
- The stage is always one dropdown button at the left of the row, named for
  the stage shown (All, Block, Spline, Polish, Deliver); the five tabs no
  longer sit side by side. Click it to choose a stage; Ctrl+Wheel over it
  cycles. The freed space goes to tools.
- Find and More each have one job. Find is a magnifier icon that reaches all
  96 tools: type to search, or with nothing typed browse them by family tabs;
  click to run, pin to add to the row. More appears only when the row's tools
  do not fit, labelled with how many (for example +3), and lists just those.
  The row gains about 60 px when everything fits.
- Find and Toolbar Settings share one saved layout: a pin made in Find shows in
  Toolbar Settings (even while it is open), and Settings changes light or clear
  the pins in Find.
- Tool Settings, Find pins and +N follow the shown row. A Find pin goes to
  the shown row, whatever the tool's family.
- Hover Explainers (Preferences > Add-ons > Anim Assist > General): Full (the
  whole explanation), Short (name and one line) or Off. It covers the Timeline
  row and every Anim Assist button. Off removes the row's hover text entirely;
  Bforartists buttons then show only their name, because Bforartists always
  prints a description line. Hover text adds a Shortcut line only when a key is
  already bound to that tool (none are by default); it reads the live keymap,
  so keys you bind later appear.
- Hover text also names Bforartists' own key for a command that does the same
  job, labelled "Bforartists key", only when Bforartists binds one: Copy (Ctrl
  C), Paste (Ctrl V), All Keys (A), Grow both sides (Ctrl Numpad +), timing
  scale tools (R, Scale Keys in Time) and timing offset and nudges (W, Move
  Keys in Time). Key types, handles, interpolation and others have Bforartists
  equivalents without default keys; a key you bind to one appears.
- Stages start from a fixed default set, not from a layout's All tools: tools
  you added to All stay in All until you add them to a stage. Older 12.9.x
  layout records are upgraded in memory and saved in the new format on the
  next change; 12.9.x cannot read the new format.

# 12.9.1 — Stage tab fixes

- The All tab no longer behaves like the Keys tool Select All Visible: it is
  not dimmed, always switches stage, and right-click no longer opens that
  tool's settings.
- Switching stage never swaps the tabs for the cycle button, so controls stay
  under the cursor. Tabs show only when every stage fits beside them in full.
- The cycle button keeps its highlight and tooltip after a click.
- Row Stage in Toolbar Settings opened outside a Timeline (for example from
  Preferences) shows a note instead of changing an unrelated screen.
- The stage is stored per workspace, so a maximized Timeline and extra windows
  of the same workspace keep it. Stages chosen in 12.9.0 start on All once.

# 12.9.0 — Timeline stage tabs

- Adds stage tabs to the bottom Timeline band: All, Block (Tween, Keys),
  Spline (Curves), Polish (Timing, Pose) and Deliver (Bake, Motion). A stage
  filters the families shown from the active layout; saved layouts, tool modes
  and slider settings are unchanged. All shows every family.
- Each workspace keeps its own stage, saved with the file. Click a tab,
  Ctrl+Wheel over the tabs, or use View > Anim Assist Stage.
- When the band is tight, the tabs collapse into one button that cycles stages
  before any slider is compacted.
- Toolbar Settings (the row's Settings button) shows a Row Stage dropdown and
  says when the family being configured is hidden by the current stage. Add-on
  Preferences note that each workspace picks its stage with the row's tabs.
- Settings text and the Timeline Tool Row preference now say the row sits at
  the bottom of the Timeline.
- Timing tooltips now describe key spacing: 80%/90% sit keys closer (faster),
  110%/120% spread them apart (slower). Timing Scale says the same.

# 12.8.0 — Editor-specific sidebars

- Adds an NLA sidebar for clip arrangement, neutral Combine transform corrections,
  source editing, shared Actions, track ordering and preserved evaluated baking.
- Refines Graph and Dope Sheet groups and exposes common actions directly.
- Fixes selected-key interpolation scope and editor filtering for Key Manager
  timing commands. Identifies unsupported pinned/non-object sources explicitly.
- Retains the bottom-only Timeline implementation and saved toolbar layouts.

# 12.7.1 — Timeline keyframes no longer hidden

- Fixes keyframing in the Timeline: with the header on top (the Bforartists
  default), the tool row covered the keyframe row, hid the keys and turned
  clicks on them into tool presses. The row now sits at the bottom of the
  Timeline canvas, below the scrub ruler and keys, and above the marker strip
  when there is room.
- No tool, dispatch, setting or layout changes.

# 12.7.0 — Timeline toolbar overhaul

- Consolidates the configurable inline/popout toolbar, per-tool settings and
  user-named layouts as a minor overhaul release.
- Qualifies fresh-start row visibility and an animator workflow through direct
  gestures, settings, layout switching, native navigation and normal restart.
- Retains the animation algorithms, 89 dispatch mappings and lifecycle repairs
  from 12.6.2; the version consolidation changes no tool math or selection scope.

# 12.6.2 — Configurable sliders and named toolbar layouts

- Keeps the add-on-only second Timeline row, with Tween, Timing, Curves, Keys,
  Pose, Bake and Motion followed by right-side Search, More and Settings.
- Starts with Breakdown and Smooth inline; Timing Scale uses direct-drag popout
  feedback. All eight numeric tools can be hidden, buttons, popouts or inline.
- Adds staged Toolbar Settings and individual tool settings for supported
  ranges, defaults, sensitivity, precision, snapping and presets.
- Adds user-named layout Save As, Load, Update, Rename and Delete. Recommended
  reset keeps the library. Layout changes do not edit animation or scene scope.
- Fits the row to width without changing saved configuration or adding editors.
- Repairs bilateral Mirror Selected source overwriting, fast object-trail spatial
  offset, and missing committed redo state in immediate toolbar dispatch.
- Validates layout settings before import; persists named layouts in preferences.

# 12.6.1 — Add-on Timeline tool row

- Adds a tool row inside the Timeline canvas in standard Bforartists; no
  separate application, helper editor or long appended playback-header toolbar.
- Uses native keymaps for toolbar clicks and preserves normal input outside it.
- Keeps seven families, 89 searchable/pinnable actions and 13 default quick tools.
- Fits quick tools to the available width; More contains overflow actions.
- Preserves the frame ruler when the native header is at the top.
- Gives a collapsed Timeline space once on initial startup when native resizing
  is available. Later manual resizing is preserved; there is no layout-repair loop.
- Adds hover help, reversible visibility and saved quick selection.

# 12.6.0 — Historical native Timeline experiment

The custom application was withdrawn; 12.6.1 is an add-on-only implementation.

- Supplies an Anim Assist TOOL_HEADER in the patched Bforartists Timeline.
- Adds 19 existing action presets for clipboard, reference bookmarks, object
  matching and configured numeric rig switches; 89 presets are searchable and
  pinnable, retaining the previous 70 dispatch mappings and 13 quick defaults.
- Adds nearby family options and direct access without mandatory submenus.
- Removes Text Editor strip creation and recurring split/join height repair.
- Respects native toolbar hiding and handles explicit preference updates across
  workspaces. Unpatched Bforartists shows the tools in its existing header.
- The genuine second row requires the matching custom Bforartists application.
  Compilation and manual native qualification are recorded with the local build;
  this source update alone does not establish runtime or AnimBot parity.
- Fix native toolbar re-enable while the Timeline is maximized.
- Explain Ease's two-key prerequisite before invocation.
- Preserve handles, key types, selection and custom easing on Action Offset
  cancellation, including newly inserted keys. Read fast-mode preferences from
  the installed package and translate Bezier handles with offset values.

# 12.5.1 — Timeline layout repair

- Keep the second toolbar thin after resizing by rebuilding only its owned Timeline pair.
- Preserve a native frame ruler and editable key area when creating the strip; short Timelines retain the native header until enlarged.
- Require an upper split copy, repair inverted owned pairs, and retry transient layout failures instead of blacklisting a Timeline for the session.
- Use normal-session join/split operations; avoid timer-driven border moves whose poll requires the actual mouse to be on a border.

# 12.5.0 — Inline family clusters

- Each of seven Timeline family menus now sits beside its selected quick tools.
- Select any of 70 existing presets through native, global preference checkboxes.
- Gear opens Timeline Quick Tools; empty selection and all-family reset are supported.
- Native header panning retains selected tools at narrow widths.
- Quick selections transfer through settings export/import; legacy files retain current pins.
- Legacy scene category switches continue to control other editor headers.
- Fix Debug Mode callback binding exposed by settings import.
- Local candidate; actual Bforartists and owner acceptance remain pending. See qualification report for recovery/display limits.

# Anim Assist Changelog

## Versioning policy

Anim Assist follows a phase-aligned semantic version scheme:

- **Major (X.0.0)** - new phase added (e.g. v11.0.0 = Phase 12 lipsync layer).
- **Minor (X.Y.0)** - minor additional tool or drastic change within an existing phase.
- **Patch (X.Y.Z)** - bug fix or implementation update with no new feature surface.

Each release updates four places in lockstep: `bl_info` in `__init__.py`,
`ADDON_VERSION` and `ADDON_VERSION_STRING` in `constants.py`, and `version`
in `blender_manifest.toml`.

## v12.4.0 - Compact Council Timeline Toolbar

Local release, 2026-10-12; not published to GitHub.

- Build the approved full Brainstorm Council design: seven fixed family menus,
  prominent percentage/Drag shortcuts and grouped More containing all 17
  original shortcuts. Timing/Keys expand at wider widths; Tools consolidates
  families at narrow widths. Selection changes affect availability in place.
- Share scope, prerequisite, gesture and permanent family-path tooltips across
  inline buttons, menus and More. Name object bake/proxies, key-time rounding
  and Action value offset according to their actual behavior.
- Include the owner's requested Breakdown anchor explanation in percentage
  and Drag tooltips and Help, with an empty-frame/existing-key numeric example.
- Repair Opposite selection through the existing pose-selection compatibility
  helper; Drag cancellation restores key selection, type and easing metadata.
- Show native Drag factor feedback and captured Offset object/Action/live mask.
- Scale the native editor-border pairing tolerance with UI scale, preventing
  repeated strip creation at 150% and keeping dispatch paired to the Timeline.
- Explicitly enable target undo in Python toolbar dispatch, repairing the
  measured missing redo step for a percentage Breakdown.
- Preserve all 70 preset IDs, operator targets/arguments and seven families.
  Actual Bforartists compatibility and owner usability require that host.

## v12.3.1 - Clearer Timeline Toolbar Gear

Local release, 2026-10-12; not published to GitHub.

- Match the owned Timeline strip's gear labels to Tween, Curves, Timing, Keys,
  Motion and Pose menus using contextual labels on the existing properties.
- Identify Timeline placement as an add-on preference and category visibility
  as a scene setting shared across editor headers.
- Implement the council's winning Team C base recommendation. Preserve the
  existing menu targets, shortcuts, visibility behavior and animation math.
- Actual Bforartists compatibility and the owner's usability walkthrough remain
  unverified. No automated tests or animation action/Undo checks were run.

## v12.3.0 - Grouped Animation Tools in the Timeline Toolbar

Local release, 2026-10-12; not published to GitHub.

- Add Tween, Curves, Timing, Keys, Pose, Bake and Motion menus to the second
  Timeline row, preserving the current quick buttons.
- Expose existing tools corresponding to animBot concepts: tweening, neighbor
  and frame blending, easing, smoothing, timing nudges, native handles, key
  types, mirroring, matching, transform baking, proxies and motion trails.
- Distinguish selected-key nudges from Action timing offsets, and reference
  value scaling from neighbor Push/Pull. Partial matches have accurate labels
  and tooltips; no new animation math or claims of full animBot parity.
- Fixed +/-1-frame nudges execute immediately using the existing undoable tool.
- Pose and Motion menus follow the existing matching and trajectory visibility
  settings. The gear heading now describes both toolbar uses.
- See `docs/anim_assist/releases/12.3.0/animbot-matches.md` for the match table.
  Native preview uses a Blender stand-in; interactive behavior and actual
  Bforartists compatibility remain unverified.

## v12.2.0 - Toolbar Above Timeline

Local release, 2026-10-12; not published to GitHub.

- Move existing Timeline shortcuts into a thin editor strip above the native
  Timeline controls: Breakdown, Push/Pull, Timing, Selection and Anim Offset.
- Toolbar buttons use the adjacent Timeline's context and the existing tool
  implementations. Graph Editor and Dope Sheet shortcuts retain their placement.
- Add “Toolbar Above Timeline” in preferences and the toolbar gear popover.
  Turning it off rejoins the strip and restores native-header shortcuts.
- Saved strips reconnect by an owned Text datablock. Add-on disable rejoins
  adjacent owned strips; manually rearranged strips become ordinary Text editors.
- Use native-header fallback when the Timeline is too short to split or the
  host's Text header hook is unavailable. Native theme and scrolling apply.
- Layout API and visual inspection used a Blender 5.1.2 stand-in. Actual
  Bforartists use and interactive tool/undo behavior remain unverified.

## v12.1.3 - Lipsync Layer Slot and Recents Order Fixes

Local release, 2026-10-11; not published to GitHub.

- Lipsync Bake and Rebake on an Animation Layers layer Action reuse that
  action's only slot. Previously a second slot was created on Blender 5.x, so
  baked keys were invisible to the layer stack. Clear Auto Keys and Mark
  Manual no longer create slots.
- Recents and Repeat Last follow each entry's timestamp. Files saved by
  12.1.0 and earlier stored Recents oldest-first; Repeat Last now runs the
  newest tool for them as well.
- No interface, tool ID, setting or default changes.
- Tested on a Blender 5.1.2 stand-in host (the Bforartists check passes by
  install path). Not yet re-run on Bforartists.

## v12.1.2 - Workflow Reliability and Lipsync Guidance

Local release, 2026-10-11; not published to GitHub.

- Lipsync bake, rebake, clearing and manual overrides use the correct modern
  Action slot. New keyframes are inserted correctly; manual keys survive.
- Reopening a file preserves explicit Lipsync target and preview/baked settings.
- Toggle Shelf Mode correctly cycles Compact, Expanded and Favorites.
- Lipsync shows the next setup step for a missing layer or WAV file, uses an
  enable checkbox, and displays readable Live Preview / Baked mode labels.
- Graph Editor, Dope Sheet and Scene Properties homes, tool IDs, settings and
  defaults are preserved. No action promotion or confirmation removal.
- Verified on Bforartists 5.2.0 (Blender 5.3.0 Alpha, build 0a1ca45552db)
  with internal tests, host regressions, native Undo/Redo and clean installation.
  Optional Rhubarb and every legacy interactive tool were not individually exercised.

## v12.1.1 - Search and Matching Repair Candidate

Local candidate, 2026-10-10. Runtime and interactive acceptance testing is
pending; this build has not been published to GitHub.

- Search is populated from registered public Anim Assist operators on enable
  and restart. First Run Setup restores the catalogue and reports its tool
  count; repeated setup preserves existing settings, favorites and recents.
- Demo configuration uses real tools instead of nonexistent sample IDs.
- The missing context-warning helper is restored so matching panels can draw
  their selection guidance in the Graph Editor, Dope Sheet and Scene Properties.
- Search and Repeat use the tools' invoke paths, respecting their setup,
  dialogs and modal behavior. Cancelled tools no longer produce false success
  reports; tools waiting for a dialog or modal input are not recorded as completed.
- Completed Search tools enter Recents with the newest at index zero, which
  is the item Repeat Last reads. Clearing Recents leaves the list empty.
- Explicit Scale Keys and Offset Keys values survive invocation; scene
  settings initialize only properties that were not explicitly supplied.
- Common Breakdown, Retime, Match and Mirror polls now explain missing
  selection, animation or mode prerequisites. Lipsync Bake explains missing
  scene settings. Existing layout and operator identifiers are retained.

## v12.1.0 - Three Organised Homes, No Viewport Tab

Minor: Anim Assist no longer adds tabs to the 3D Viewport sidebar (it
added six). Its panels now live in three homes, each organised for the
editor it sits in and each headed "Anim Assist":

- Graph Editor sidebar, one "Anim Assist" tab, by action: Select, Shape
  Curves, Retime, Clean Up, Pose & Rig, Quick Shelf.
- Dope Sheet sidebar, one "Anim Assist" tab, by stage: Block, Inbetween,
  Time, Mirror & Match, Keys & Channels, Shelf & Macros.
- Properties editor, Scene tab, "Anim Assist" section, by scope: This
  Pose, Whole Animation, Rig, Face, then Setup (First Run Setup, pair and
  switch detection, lipsync setup), Settings and Help & Diagnostics. The
  former 3D Viewport panels moved here.

New: an "Anim Assist" menu in the 3D Viewport, Graph Editor and Dope Sheet
headers, following each editor's structure and ending with Open Anim Assist
Panel, Anim Assist Workspace and Open in Separate Window. "Anim Assist
Workspace" adds a copy of the Animation workspace with a Graph Editor and
every home open; the stock Animation workspace is not changed. An optional
Anim Assist pie (Shift Alt D, off by default, free in every default keymap)
gathers the existing pies; turn it on and rebind it in Settings. Each
header menu can be hidden per editor in Settings.

Fixes: Anim Offset works from the Properties editor (it needed an object in
context, which the Scene tab does not provide). Error messages that sent
you to the removed Workspace tab now point to Properties > Scene > Anim
Assist > Setup. The README no longer claims First Run Setup creates
hotkeys: Anim Assist registered none before this release.

Scene migrations now run. Blender enables add-ons with scene data locked,
so the migration at registration always failed (printing an error trace at
every startup and whenever the add-on was ticked on), and nothing migrated
files opened later, so v11 lipsync links never received the v12 fix.
Migration and the "saved with a newer Anim Assist" check now run as soon as
scene data is readable after enabling, and again after every file open.

## v12.0.4 - Every Panel Draws, Clearer Sidebar

Patch: fixes 11 sidebar panels that drew empty under a normal header
(Dope Sheet Retime, Bake, Match & Switch, Mirror and Quick Shelf; Graph
Editor Key Selection, Channels, Metadata, Diagnostics and Key Utilities) -
editor copies were built as subclasses of registered panels, which detached
the originals. Fixes a layer-reorder check that raised an error on every
redraw with no layers. Every error now says what to do next and never shows
a raw Python exception. Destructive actions are undoable or ask first with
the consequence stated. Sidebar labels no longer clip at default width,
abbreviations are spelled out, the Layers and Match & Switch panels explain
their empty and disabled states, and the README lists the real tabs and the
First Run Setup step. Verified on Bforartists 5.1.2 by running every
editor-only tool inside a real Graph Editor and Dope Sheet.

## v12.0.3 - Blender 5.x Compatibility and Correctness

Patch: restores every "selected bones" operator on Blender 5.x (Bone.select
moved to PoseBone), makes all app handlers persistent so undo/redo cache
invalidation survives file loads, and adds undo to Anim Offset and the
remove-item operators. Matching, space-switch compensation and mirroring
now accept pose bones and honour each bone's rotation mode (quaternion and
axis-angle rigs mirror, swap, match and layer correctly). Range
compensation persists through keys and records the true pre-switch pose per
frame. Layer actions get a slot on 4.4+ instead of crashing. Fixes Remove
Time deleting the playhead and window-edge keys, bake truncating fractional
keys and dropping the subframe, breakdown tangent matching and key counts,
curve tools moving keys without their handles, Remove Proxy orphaning other
proxies' records, "Match to Opposite" writing the wrong bone, Restore Switch
calling a missing function, preview restore doing nothing, bone-targeted
operators skipping custom-property keys, and bone-name escaping in data
paths. Bforartists 5.1.2 verified headless.

## v12.0.2 - Onboarding Reliability

Patch: fixes First Run Setup under Blender's string-based enum API, surfaces
the setup action when the shelf is empty, and makes the invalid-audio prompt
version-independent. Completes native hover descriptions for all exposed
operators, buttons, toggles, and directly drawn properties. Extended `?` help
popups can be hidden independently from native Bforartists hover tooltips.

## v12.0.1 - Low-Jitter Trajectory Overlay Defaults

Patch: makes the ghost/trajectory overlay safer to leave on while animating.

- Constraint evaluation remains opt-in and is ignored during playback so the
  overlay does not call `scene.frame_set()` while the animator is posing or
  playing the timeline.
- Enabling or refreshing the overlay now rebuilds only the visible trajectory
  draw data. Arc diagnostics run only from the explicit Run Diagnostics
  command.
- Default overlay load is lighter: max samples reduced to 160, frame ticks
  hidden by default, and multi-target display capped at 3 targets.

## v12.0.0 - Hybrid PREVIEW/SHIPPED Lipsync + Shape Key Support

Major: introduces a new evaluation paradigm for lipsync. Lipsync layers now
choose between two modes:

- **PREVIEW**: live Blender drivers on shape keys read the cue table per
  frame and respond to scrubbing/playback instantly. No fcurves written -
  fast iteration during blocking.
- **SHIPPED**: drivers torn down, cue table baked into shape key fcurves.
  Render-ready, NLA-safe, exportable to game engines that don't support
  drivers. Manual override sanctuary applies to shape key fcurves identical
  to bone fcurves in v11.

Single operator `Toggle Live Preview <-> Shipped Bake` does both transitions
including driver install/remove and key clear/bake.

### New surface
- `core/p12_cue_table.py` - typed (time_seconds, viseme_name) list stored
  on each layer link; shared by drivers (PREVIEW) and bake (SHIPPED).
- `core/p12_driver_engine.py` - registers `aa_p12_viseme_value` in
  `bpy.app.driver_namespace`, install/remove drivers per link, load_post
  handler to re-register namespace after every file open.
- `core/p12_shape_key_wiring.py` - autofill heuristic that name-matches
  viseme names against shape key blocks on the wired mesh.
- `core/p12_lipsync_engine.py` - extended with `bake_shape_keys()` and
  `clear_auto_shape_key_keys()` mirroring the bone path; same manual
  override sanctuary mechanism keyed by frame number.
- `operators/p12_mode_ops.py` - `animassist.p12_toggle_mode`,
  `animassist.p12_install_drivers`, `animassist.p12_remove_drivers`,
  `render_pre` warning handler if a render starts in PREVIEW mode.
- `operators/p12_shape_key_ops.py` - `animassist.p12_autofill_shape_key_wiring`,
  `animassist.p12_pick_mesh`, `animassist.p12_capture_viseme_shape`.
- `ui/p12_panels.py` - PREVIEW/SHIPPED toggle button on the active link,
  Target dropdown (Shape Keys/Bones/Both), Mesh picker, Shape Key Wiring
  section, explicit "audio waveform shows in dope sheet" callout.

### New per-link fields
- `mode`: PREVIEW | SHIPPED
- `target_kind`: SHAPE_KEYS | BONES | BOTH
- `mesh_name`: object whose shape keys are driven
- `cue_table`: collection of `(time_seconds, viseme_name)` rows

### Migration v3
- Backward-compat: existing v11 layer links are migrated to
  `target_kind=BONES, mode=SHIPPED` so behavior is preserved. New v12 links
  default to `SHAPE_KEYS, PREVIEW`.

### Recommended workflow
1. Create lipsync layer; pick mesh; autofill shape key wiring.
2. Bake. Layer enters PREVIEW: scrub the timeline -> mouth responds live.
3. Polish: hand-edit shape key keyframes; click Lock Selected Keys.
4. Before render: click Toggle to switch to SHIPPED. Drivers gone, fcurves
   written. Render normally.
5. If audio changes: refresh -> rebake -> manual edits preserved.

### Notable dissents addressed
- Engineer: load_post handler re-registers driver namespace on every file
  open; drivers wrapped in try/except so any error returns 0.0 silently
  (mouth at rest, never a crash).
- Mythologist: panel includes explicit "Audio waveform shows in Dope
  Sheet/Timeline as a speaker overlay" callout so the user's mental
  model is surfaced rather than discovered.
- Anthropologist (mode toggle cognitive load): render_pre handler warns
  when rendering in PREVIEW so animators can opt into auto-bake-on-render
  later if desired (config: `warn_on_render_in_preview`).

## v11.1.2 - Restore Blender 4.x defensive None-handling

Fixes a regression introduced when packaging v11.0.0 from a stale working
directory: two defensive patches in v10's `core/key_utils.py` and
`core/breakdown_core.py` were silently rolled back.

Both patches guard against `keyframe_points.insert()` returning `None` in
Blender 4.x edge cases (NEEDED flag with a duplicate-frame value). Without
them, paste-key and breakdown-insert operators can raise `AttributeError`
when the insert call hits a same-value duplicate.

Restored:

- `core/key_utils.py` lines 65-69 - `if kp is None: continue` guard in the
  paste loop, so a single skipped row doesn't abort the rest of the paste.
- `core/breakdown_core.py` lines 241-253 - fallback that recovers the
  existing keyframe at the requested frame when `insert()` returns None,
  rather than letting downstream attribute access crash.

How this got missed: my v11 packaging started from `B4_anim_assist/` on
disk, which was older than the `B4_anim_assist_v10.0.0.zip` archive
(the zip contained later patches that weren't synced back to the working
directory). v11.1.2 verifies file equality against the v10 zip before
shipping going forward.

No other Phase 1-11 logic was modified. Phase 12 lipsync code is
unchanged from v11.1.1.

## v11.1.1 - Restore truncated Phase 12 constants

Fixes a register-time crash in v11.1.0:

```
module 'bl_ext.user_default.anim_assist.constants' has no attribute
'P12_KEY_MANUAL_OVERRIDE_KEY'
```

The Phase 12 constants block (`P12_SCENE_ATTR`, `P12_KEY_MANUAL_OVERRIDE_KEY`,
`P12_KEY_AUTO_BAKED_KEY`, `P12_DEFAULT_BACKEND`, `P12_DEFAULT_FACE_GROUP`,
`P12_STALE_SUFFIX`) was truncated out of `constants.py` during packaging.
The new lifecycle module added in v11.1 imported these constants at module
load time, so the truncation surfaced immediately on enable. All six
constants are restored.

No behaviour change vs v11.1.0 - this is purely a packaging fix.

## v11.1.0 - Install / Uninstall Hygiene

Adds three lifecycle tools so installs, uninstalls, and reinstalls leave a
clean .blend behind.

**New module `core/lifecycle.py`**

- `purge_zombie_classes()` - runs at the top of `register()`. Walks
  `bpy.types` for any AA / ANIMASSIST class left over from a prior
  crashed register cycle and force-unregisters them. Catches the "class
  already registered" error class without requiring a Bforartists restart.
- `check_saved_versions()` - runs at the end of `register()`. Walks open
  scenes and warns if any was saved with a schema version newer than the

# Ghost Tool 4.3.3 user guide

Ghost Tool displays ghost meshes, motion paths and editable motion markers in Bforartists. Ghost meshes, also called onion skins, show a target at other animation times. Motion paths show its movement. Motion markers are editable points on these paths. This guide describes version 4.3.3.

Screenshots show Ghost Tool 4.3.3 in the supplied Bforartists 5.2.3 build. The native settings panels can show Tear Off Panel in their title bar.

Version 4.3.2 added Timeline collapse and a gap between the two ghost icons. Version 4.3.3 can generate previews while Anim Assist's Timeline pointer is idle. Active editing gestures still pause sampling.

The [Ghost Tool 4.3.3 installation ZIP](https://github.com/Axleonex/B4Artists_Toolkit/releases/download/ghost-v4.3.3/b4_ghost_tool_v4.3.3.zip) installs the standalone add-on. The [4.3.3 release notes](https://github.com/Axleonex/B4Artists_Toolkit/blob/a8b6b12d4f9ae7b2cd00c14af9f2f90301420c7a/docs/ghost_tool/releases/4.3.3/RELEASE-NOTES.md) and [package receipt](https://github.com/Axleonex/B4Artists_Toolkit/blob/a8b6b12d4f9ae7b2cd00c14af9f2f90301420c7a/docs/ghost_tool/releases/4.3.3/package-receipt.json) contain release evidence and the checksum.

## Install and find Ghost Tool

The supplied custom/native test build includes Ghost Tool 4.3.3. Its factory preferences enable the add-on. This build requires no separate ZIP installation or manual enabling. The viewport toolbar, Tool Shelf, sidebar and Preferences locations below also apply to this build.

For a standalone installation:

1. Download `b4_ghost_tool_v4.3.3.zip`.

2. Open Edit > Preferences > Add-ons > Install from Disk.

3. Select the ZIP.

4. Enable Ghost Tool.

5. After replacing an installed version, restart Bforartists.

6. Check that Preferences reports version 4.3.3.

Changes in the repository do not automatically update an installed add-on. An older ZIP installs its original version.

These instructions install the standalone add-on. The proposed built-in version depends on Bforartists PR [7067](https://github.com/Bforartists/Bforartists/pull/7067). That PR remains unmerged as of 2026-11-19. Released official Bforartists builds do not yet include this proposed integration.

Ghost Tool defaults to Top Toolbar in the native 3D Viewport Tool Settings row. When native headers are at the top, this row is below the main viewport header. The row follows native header alignment.

Preferences also offer Right Sidebar (N) and Left Tool Shelf (T). Ghost Tool changes older saved Top Header choices to Top Toolbar.

![Ghost Tool 4.3.3 preferences](images/4.3.3-preferences.png)

*Figure 1. The supplied build enables Ghost Tool 4.3.3. Display Location shows Top Toolbar.*

Native tool and mode controls remain available. Narrow or split viewports keep all Ghost toolbar controls in the same order.

1. Middle-mouse drag the native row horizontally to reach controls outside the visible width.

2. If Ghost controls are hidden, select View > Show Ghost Toolbar.

3. Save preferences to retain display choices.

## Set the interface language

The Ghost Tool localization candidate supports English, Japanese, Korean, Simplified Chinese, Portuguese, Spanish and French. These language instructions apply to that candidate.
Bforartists language controls require a build with translation support.

1. Open Edit > Preferences > Interface.

2. In Language, select the required language.

3. For a non-English language, enable Interface, Tooltips and Reports under Translate.

4. Open Ghost Tool's add-on preferences.

5. Set Language to Interface Language.

Interface Language makes Ghost Tool's custom text follow the application's interface language.
Disabling Interface returns automatic custom text to English.
An explicit Ghost Tool language changes custom text. Native controls and tooltips still use the application's language.
Use matching language settings for the complete interface.
Existing object names, bone names and saved data identifiers retain their original text.

## Quick start: inspect an animated target

1. Select an animated object or pose bone.

2. Enable the first ghost icon.

3. Click Ghosts to show mesh previews.

4. Set Before and Ahead independently.

5. Select Wire or Solid for the mesh appearance.

6. Hold Ghosts to adjust sampling and appearance.

7. Click Paths to display a motion path.

8. Click Add Selected Path to retain another selected target.

9. Enable Markers Display to show editable points on an added path.

10. Click Drag.

11. Select a marker in the 3D Viewport.

12. Move the marker.

13. Confirm the move.

14. Select another marker to continue editing.

15. To leave Drag Markers mode, click Drag again or press Escape.

![Animated cube with ghost mesh previews](images/4.3.3-overview.png)

*Figure 2. Cached ghost meshes surround the animated cube. The first ghost icon enables Ghost Tool.*

When no path target exists, Paths can add the selected animated target. Follow Selection displays the current selection. Targets added with Add Selected Path remain in the path list.

## Read the top toolbar from left to right

![Full Ghost Tool top toolbar](images/4.3.3-toolbar-wide.png)

*Figure 3. The top toolbar keeps the listed control order, from the overall ghost icon to Settings.*

| Control | Action |
| --- | --- |
| Ghost Tool | Enable or disable the overall tool. Hold for update settings. |
| Ghosts | Show or hide ghost meshes. Hold for sampling and appearance. |
| Before / Ahead beside Ghosts | Set independent mesh sample counts. Each number has minus and plus buttons. |
| Wire / Solid | Select the mesh display style. |
| Paths | Show or hide motion paths. Hold for sampling and line settings. |
| Before / Ahead beside Paths | Set independent path sample counts. Each number has minus and plus buttons. |
| Add Selected Path | Keep the selected target in the path list. |
| Follow Selection | Display a path for the current selection. Hold for Highlight Active Path. |
| Drag | Enable Drag Markers mode for repeated edits. Hold for motion editing settings. |
| Pin | Select a marker to pin or unpin. Hold for Unpin All Markers. |
| Markers Display | Show or hide editable path markers. Hold for sampling and labels. |
| Arc Style | Open Solid, Speed Colored and Fade choices. |
| Spacing Ticks | Show or hide spacing indicators. Hold for Acceleration Indicators. |
| Settings | Open the advanced controls. |

The first ghost icon controls the overall tool. Ghosts controls mesh visibility separately. Disabling the overall tool also disables marker and handle editing.

Hidden meshes keep the selected style. Wire or Solid selects a style. Ghosts controls whether meshes are visible.

Markers Display is the diamond immediately right of Pin. Labels appear when the pointer is over a control.

Arc Style controls the ghost motion arc. Wire/Solid controls mesh display. The Paths Line Style setting controls path display.

Settings includes marker generation, targets, range, editing, Compare, Physics and appearance options. Generate and Clear have no additional top-row icons.

## Set Before and Ahead counts

Each display has two independent counts. Before requests samples earlier than the playhead. Ahead requests samples later than the playhead.

1. Set a count with its number field or minus and plus buttons in the top toolbar.

2. Set a count to zero to disable samples on that side.

Onion Skin options uses After for the toolbar's Ahead count.

![Onion Skin options for mesh counts and sampling](images/4.3.3-skin-options.png)

*Figure 4. Onion Skin options shows mesh counts, sampling, opacity and Live Update Skin.*

Counts specify how many samples to request. Sampling specifies their positions.

For this example:

1. Set the playhead to frame 20.

2. Set Ghosts Before to 3.

3. Set Ahead to 2.

4. Set the frame step to 2.

Earlier samples request frames 18, 16 and 14. Later samples request frames 22 and 24. Available animation and range limits can restrict these requests. The current pose is not a Before or Ahead sample.

By Keyframe uses animation keys instead of evenly spaced frames. Its interval can skip keys. A change to the Paths count fields selects a window around the playhead based on those counts. Advanced range modes use their own rules.

## Hold a tool for its settings

A supported button has two actions:

1. For the main action, click the button.

2. For its parameter menu, press and hold the button.

Arc Style and Settings open with an ordinary click.

| Hold this control | Available settings |
| --- | --- |
| Ghost Tool | Update Meshes While Scrubbing, Update Markers While Scrubbing, Freeze Updates |
| Ghosts | Sampling, Every (Frames), Keyframe Interval, Opacity, In Front, Fade |
| Paths | Sampling and interval, Line Style, Frame Numbers, Bezier Handles |
| Markers Display | Shared Paths sampling, Keyframe Dots, Marker Frame Numbers |
| Drag | When Released, Curve Shape or Smooth Neighbours, Nearby Frame Reach, Falloff |
| Pin | Pin instructions and Unpin All Markers |
| Follow Selection | Highlight Active Path |
| Spacing Ticks | Acceleration Indicators |

Frame-step sampling uses Every (Frames). A value of 1 samples every frame. Keyframe sampling uses the keyframe interval controls. Some controls offer custom intervals.

Markers and Motion Paths share sampling. A sampling change through Markers Display also changes Paths sampling.

Settings > Onion Skin options opens the mesh controls in Figure 4. Settings > Motion Paths opens the target and handle controls in Figure 7.

## Use the bottom Timeline toolbar

The compact strip is beside the native Timeline buttons in the same row. It adds no row beneath the Timeline toolbar.

1. Enable the left ghost icon to reveal the remaining controls.

2. Disable that icon to collapse the strip.

With Ghost Tool enabled, a visible gap separates the overall on/off icon from the mesh Ghosts icon. These behaviors started in 4.3.2.

![Expanded Ghost Tool Timeline strip](images/4.3.3-timeline-enabled.png)

*Figure 5. The enabled Timeline strip shows mesh counts, display styles, marker editing and path controls.*

![Collapsed Ghost Tool Timeline strip](images/4.3.3-timeline-collapsed.png)

*Figure 6. With Ghost Tool disabled, only its overall ghost icon remains beside the native Timeline controls.*

The enabled strip has this order from left to right:

1. Overall Ghost Tool on/off.

2. Mesh Ghosts display.

3. Before and Ahead mesh counts.

4. Wire and Solid mesh styles.

5. Drag Markers.

6. Editable-marker diamond.

7. Paths display.

8. Before and Ahead path counts.

Each count pair follows the same earlier/later order as the top toolbar. The Timeline uses compact native number fields.

1. For sampling and display settings, hold Timeline Ghosts or Paths.

The menu includes Frame by Frame, By Keyframe and sampling intervals. More Ghost Settings opens the full options.

The bottom diamond shows or hides editable markers. Its separate hold menu is on the top toolbar's Markers Display button. Compare contains snapshot controls in advanced settings.

The Graph Editor header also provides the overall toggle and a motion-path segment when Ghost Tool is active.

## Drag markers repeatedly

1. Enable Ghost Tool.

2. Enable editable markers for an animated target.

3. Click Drag.

4. Click a visible marker in the 3D Viewport.

5. Move the marker.

6. Confirm the move.

If you click empty space, the picker waits. After a confirmed move, Drag remains active for another edit. All Drag Markers buttons share this mode.

To stop:

1. Click Drag again or press Escape.

During a move, Escape cancels that move. Ghost Tool restores the original curves and marker positions for that move. Earlier confirmed moves remain separate edits.

1. To reverse earlier confirmed moves, use Undo.

Disabling Ghost Tool ends editing. A lost target, file change, history change or add-on shutdown also ends or cancels affected sessions.

Path-handle dragging also supports repeated selections.

![Motion Paths target and handle controls](images/4.3.3-path-targets.png)

*Figure 7. Motion Paths retains the animated cube as a target. This example enables Markers and Handles.*

1. Enable Bezier Handles in Paths settings.

2. Start the handle-drag action.

3. Select a visible handle.

4. Move the handle.

5. Confirm the move.

6. Select another handle to continue.

Shift+G access remains available. During handle dragging, Alt switches aligned-handle behavior on or off. Escape cancels an active handle move and exits the mode.

## Choose smooth or sharp motion edits

1. Hold Drag.

2. Inspect When Released.

3. Select Reshape Handles or Insert Keyframe.

Reshape Handles changes existing Bezier handles to make the curve pass through the moved sample. It adds no keyframe.

Curve Shape offers three choices:

| Choice | Effect |
| --- | --- |
| Free | Handles adjust without angle restrictions. |
| Locked | Handle angles remain fixed. Handle lengths can change. |
| Smooth | Handle influence redistributes across the segment. |

Settings > Edit Motion contains the same release and curve shape choices as the Drag hold menu.

![Reshape Handles settings in Edit Motion](images/4.3.3-reshape-options.png)

*Figure 8. Edit Motion shows Reshape Handles with Free curve handling. Reach controls the influence on nearby frames.*

Insert Keyframe writes a key at the marker's frame. After insertion, Smooth Neighbours can smooth adjacent key handles. Nearby Frame Reach and Falloff control the influence on surrounding frames.

![Edit Motion keyframe editing and pin controls](images/4.3.3-edit-motion.png)

*Figure 9. Edit Motion shows Insert Keyframe, Smooth Neighbours, easing and pin controls. Draw to Keys needs an annotation stroke.*

The distance between samples also affects the visible line. Widely spaced samples produce a coarse line even when the animation curve is smooth.

1. To inspect the result, select a smaller frame step.

Additional display samples do not change animation interpolation or handle shape.

## Pin markers and manage path targets

1. Click Pin.

2. Click a visible marker to toggle its pinned state.

3. To select another marker, click Pin again.

Pin selects one marker at a time. It does not remain active like Drag. Multiple markers can remain pinned at the same time.

Pinned markers remain fixed while reshaping. A refresh preserves matching pinned marker records.

To release all pinned markers:

1. Hold Pin.

2. Select Unpin All Markers.

An added path target keeps an object or bone in the path list. It does not freeze all animation samples. Follow Selection changes the selection preview. Targets added with Add Selected Path remain in the path list.

The path list in Settings contains the target controls. Markers Display shows editable points along added paths. Keyframe Dots provide a separate display aid.

Figure 7 shows the path list. Figure 9 shows Pin and Unpin All in Edit Motion.

## Live updates and native animation editing

Live Update Markers and Live Update Skin default off. Existing scenes keep their saved values. With these options off, the last refreshed preview remains during scrubbing.

1. For Update Markers While Scrubbing and Update Meshes While Scrubbing, hold the master ghost icon.

These controls use the same marker and mesh update settings. Freeze Updates pauses automatic updates.

Settings > Marker options contains the same marker update controls. Figure 4 shows Live Update Skin in Onion Skin options.

![Marker options with live-update controls](images/4.3.3-marker-options.png)

*Figure 10. Marker options contains Live Update Markers, Freeze and the update delay.*

During native move, rotate, scale and gizmo gestures, Ghost Tool keeps the last preview. It does not step through animation frames during those gestures. After confirmation or cancellation, it waits for edits to settle. Then it refreshes existing ghosts.

Auto-key can remain enabled. Without auto-key:

1. Confirm the pose.

2. Insert the intended key.

Generate in advanced marker controls regenerates the previews when requested.

In 4.3.3, Ghost Tool can generate markers and onion skins while Anim Assist's Timeline pointer is idle. This exception applies only to that passive pointer handler.

Active Anim Assist sliders, transforms, gizmos, frame scrubbing and unknown modal operations still pause sampling.

1. Before generating again, finish the active gesture.

The fix does not change preview update defaults or source animation behavior.

The advanced controls still contain Marker Targets, onion-skin sources, range, subdivision and appearance settings. Cached marker and skin visibility controls hide or show existing previews without rebuilding them.

Clear All Ghosts removes markers and onion skins.

1. To hide previews without removing them, use visibility controls.

You cannot select hidden markers with a click or box selection.

## Save, compare and restore snapshots

1. Open Settings.

2. Open Compare.

3. Select the intended Scope.

4. Confirm the displayed capture target.

5. Enable markers for the selected target.

6. Click Save Snapshot.

![Compare with a saved Motion reference snapshot](images/4.3.3-compare.png)

*Figure 11. Compare contains the saved Motion reference snapshot and its Hide, Restore, Save Variant and Delete controls.*

Scope offers Active Object / Selected Bones, Selected Path, Selected Marker Channels and All Scene Markers.

Snapshots keep frozen samples and captured keyframes and handles. Snapshots remain with the scene after saving and reopening. Disabling and re-enabling the add-on also preserves them.

Hide or Show changes the snapshot overlay without changing animation. Save Variant creates an independent alternate snapshot and records its origin. The alternate remains if you delete the parent snapshot.

The scene can keep ten snapshots.

1. At capacity, delete unwanted records before saving another snapshot.

Capture, variants, binding, visibility, deletion and restoration support native Undo and Redo.

Before writing, Restore validates scene, object, action, slot, bone and channel identity. It restores captured curves and marker records for the snapshot's scope. It also refreshes the display when live updates are off or frozen.

Restore does not change unrelated objects or arbitrary Action modifiers. Older sample-only references restore suitable sampled values when Ghost Tool can reshape the curves.

Replaced targets require explicit binding. Binding associates a reference with its target. Shared action slots prevent binding.

1. Before binding, make animation single-user.

Bind to Active Target supports one original object and its named bone channels per reference. Imported references with multiple objects remain viewable and unbound. Ghost Tool cannot bind those objects to one target.

Bindings follow bone renames. After saving and reopening, channel identity identifies the curve. Rollback restores original curve values after cancellation. During a gesture, Ghost Tool does not apply rollback writes for original curves to replacement curves.

## Transfer snapshots and use advanced tools

1. To transfer comparison data, export snapshots to JSON.

Import validates and merges records. If IDs match existing records, Import assigns new IDs. It rejects unsupported versions or records beyond capacity. A rejected import adds no partial records.

Imported and legacy references remain viewable. Restoration requires explicit binding because JSON cannot prove the original object's identity. A failed import preserves unreadable existing scene records.

![Ghost Tool JSON export and import settings](images/4.3.3-transfer-settings.png)

*Figure 12. Settings contains Export and Import for Ghost Tool JSON data.*

Edit Motion contains easing presets and custom easing controls. Easing controls how motion changes speed. Draw to Keys converts the longest annotation stroke into a location path. Crossing dashes identify keys. The Draw to Keys dialog keeps the selected target.

Settings, the sidebar and the shelf contain Physics Feel, Look, Compare and other advanced tools.

Figure 9 shows easing and Draw to Keys in Edit Motion.

![Physics preview and stamping controls](images/4.3.3-physics.png)

*Figure 13. Physics shows throw-path previews and Physics feel controls. Stamp to Keys writes the preview to animation keys.*

![Look controls for marker colors and path display](images/4.3.3-look.png)

*Figure 14. Look controls marker colors, Arc Lines, Spacing Ticks and frame labels.*

## Troubleshooting and version evidence

| Problem | Check or action |
| --- | --- |
| No preview appears | Enable Ghost Tool. Check target animation, display visibility and nonzero counts. |
| Editable points are missing | Add the target to Paths. Enable Markers Display. |
| Samples appear too sparse | Reduce the frame step or change the keyframe interval. |
| Timeline shows only one ghost icon | Enable that icon to expand the strip. |
| Toolbar is hidden | Select Top Toolbar in preferences. Select View > Show Ghost Toolbar. |
| Controls extend beyond a split viewport | Middle-mouse drag the native row horizontally. |
| Sampling waits during editing | Confirm or cancel the active editing gesture. |
| Generation remains blocked with Anim Assist idle | Install Ghost Tool 4.3.3. Restart Bforartists. |

Figure 1 shows Ghost Tool preferences. Figures 5 and 6 show the expanded and collapsed Timeline strip states.

Marker sampling follows Paths sampling. Left shelf width preferences remain available. Full width and scale verification was incomplete in 4.2.11. This guide does not claim a new shelf-width fix.

The earlier direct-toolbar implementation received 188 targeted background checks. Those results apply to that implementation. They do not come from a new test run for this manual.

The [4.3.3 release notes](https://github.com/Axleonex/B4Artists_Toolkit/blob/a8b6b12d4f9ae7b2cd00c14af9f2f90301420c7a/docs/ghost_tool/releases/4.3.3/RELEASE-NOTES.md) record targeted regression and GUI checks on official Bforartists 5.2.3. The GUI check used Anim Assist 12.11.0 and isolated user resources. It verified nine markers and three mesh previews. The source keys and playhead remained unchanged.

That release evidence does not certify every operator, production rig or future host. The [package receipt](https://github.com/Axleonex/B4Artists_Toolkit/blob/a8b6b12d4f9ae7b2cd00c14af9f2f90301420c7a/docs/ghost_tool/releases/4.3.3/package-receipt.json) records ZIP integrity, version and source matching.

1. Report the target, operation and failed step in the [issue tracker](https://github.com/Axleonex/B4Artists_Toolkit/issues).

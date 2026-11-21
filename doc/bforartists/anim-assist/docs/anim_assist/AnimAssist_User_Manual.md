# Anim Assist 12.11.2 candidate user guide

This guide covers the local, unpublished Anim Assist 12.11.2 candidate. It includes the sound-strip setup fix at revision `7ec664d`. Published downloads remain at 12.11.1. The November 20, 2026 review covered source and documentation.

See the [current changelog](../../../../../scripts/addons_core/B4_anim_assist/CHANGELOG.md) and [documentation index](README.md) for release information.

Each screenshot appears beside its instructions. Each caption gives the capture version or recorded qualification date. Older screenshots identify controls. They do not record new acceptance tests.

Most panel figures show Anim Assist 12.11.1 in the supplied Bforartists 5.2.3 build, with a Blender 5.4 Alpha base. The new Lipsync figure shows the 12.11.2 candidate on official Bforartists 5.2.3, with a Blender 5.3 Alpha base. Native panel popovers show the registered controls clearly. To use a tool, open its editor home as described below.

Use Dope Sheet for poses and timing. Use Graph Editor for Action curves or Drivers. Use NLA Editor for clips and corrections. Help controls explain each tool. Control names in this guide match the English interface.

## Install and find the tools

### Install the standalone add-on

1. Download the [published 12.11.1 add-on ZIP](https://raw.githubusercontent.com/Axleonex/B4Artists_Toolkit/main/releases/b4_anim_assist_v12.11.1.zip).

2. In Bforartists, open **Edit > Preferences > Add-ons > Install from Disk**.

3. Select the ZIP.

4. Enable **Anim Assist**.

5. After updating, restart Bforartists.

The standalone package is `B4_anim_assist`. During installation, keep the ZIP intact.

The following figure shows the bundled entry in the supplied build. For a standalone copy, use the ZIP installation steps above.

![Bundled Anim Assist preferences, version 12.11.1. The enabled entry and General hover options appear here.](images/12.11.1-preferences.png)

### Use a proposed built-in integration

The supplied custom/native test build includes Anim Assist. Its factory preferences enable the add-on. This proposed integration needs no separate ZIP installation. This description does not establish that official Bforartists releases include Anim Assist.

1. Start the supplied custom build.

2. Open the editor paths below.

3. Open **Edit > Preferences > Add-ons > Anim Assist** for its preferences.

Do not install a second standalone copy over the bundled integration.

The preferences figure above shows the bundled entry. The **Scene home** and **First-run setup** figures below locate its setup controls.

### Find the editor homes

Earlier runtime qualification used stock Bforartists 5.2.0, Blender 5.3.0 Alpha base, build `0a1ca45552db`, OpenGL. This historical evidence applies to that host. Standard Blender is unsupported. These results do not validate all other host builds.

- **Timeline:** Anim Assist's tool row appears at the bottom of the canvas. See **Timeline: the bottom tool row** below. Playback and keyframing controls remain in the native header.
- **Dope Sheet, Graph Editor and NLA Editor:** the sidebar has an **Anim Assist** tab. Its position relative to native tabs can vary. The header's **Anim Assist** menu also gives access.
- **Drivers:** the **Anim Assist** sidebar tab and header menu adapt to driver work in Graph Editor's **Drivers** mode.
- **Scene Properties > Anim Assist:** this home contains character setup, broader animation tools, macros, settings and help. The 3D Viewport sidebar has no Anim Assist tab.

To open the sidebar tools:

1. Move the pointer into Dope Sheet, Graph Editor or NLA Editor.

2. Press N.

3. Select the **Anim Assist** tab.

For driver work, switch Graph Editor to **Drivers** mode.

**Scene Properties > Anim Assist > Setup (once per rig) > Run First Run Setup** creates the general Quick Shelf. Setup also offers a workspace. The optional **Shift Alt D** pie starts disabled. To enable or rebind the pie, use **Settings**.

![Scene home and tool groups. Native panel popover, Anim Assist 12.11.1. The Quick Shelf and groups share the Scene Properties home.](images/12.11.1-scene-home.png)

![First-run setup. Native panel popover, Anim Assist 12.11.1. Run First Run Setup and Add Anim Assist Workspace appear at the top.](images/12.11.1-scene-setup.png)

## Timeline: the bottom tool row

The tool row appears at the bottom of the Timeline, above the native horizontal scrollbar. It adds no header, region or workspace split. Playback and keying controls remain in the native header. To show or hide the row, use **Timeline > View > Show Anim Assist Tool Row**.

Buttons keep their full height and matching click areas. Resizing reserves space above the scrollbar. If you release the divider below the minimum height, the Timeline restores enough height for the row. The toolbar handles row clicks before the native playhead and key-selection controls. Keep enough height above the row to inspect keys.

From left to right the row holds:

| Control | What it does |
|---|---|
| **Stage button** (for example **All**, with a small arrow) | Shows the current stage and opens the stage list. |
| **Family buttons** (Tween, Timing, Curves, Keys, Pose, Bake, Motion) | Coloured names open each family's full tool list. The row's tools follow each family name. |
| **Tools** | Buttons, icons and sliders run tools. Hover text explains each tool. |
| **+N** | Opens the list of N tools that do not fit the row. |
| **Find** (magnifier) | Searches or lists all 96 tools. Each result has controls to run or pin the tool. |
| **Settings** | Opens Toolbar Settings to configure each row. |

1. Click a stage button, family button or **+N** to open its list.

2. Click an item to use it.

The list remains open as the pointer moves, including over another editor. Clicking another family button switches the list to that family.

To close the list, click the same button again, click elsewhere or press **Esc**.

![Bottom Timeline row. Historical Anim Assist 12.10.0 capture. The stage, family names, tools, Find and Settings share one row.](releases/12.10.0/evidence/images/stage-all.png)

### Tool families

Each family groups commands by their function. Each tool's hover text states its scope and requirements.

| Family | Available work |
|---|---|
| **Tween** | Breakdown percentages and dragging, inbetweens, distribution, and pushes or pulls toward neighboring poses. |
| **Timing** | Frame nudges, spacing presets, timing sliders, ripple, time insertion/removal, distribution, reversal and rounding. |
| **Curves** | Spline/stepped interpolation, neighbor/reference/ease blending, amplification, smoothing, handle types and reference bookmarks. |
| **Keys** | Visible-key, range and endpoint selection, selection growth, key types, breakdown selection, Copy and Paste. |
| **Pose** | Mirroring, opposite selection, swapping, alignment, world/parent/target matching and configured rig-property switching. |
| **Bake** | Object/preview baking, Smart Bake, reduction, integer timing, proxy creation, session baking and cleanup. |
| **Motion** | World motion trails, refresh, arc diagnostics, active-Action offset and its range mask. |

![Pose family commands, left columns. Historical Anim Assist 12.10.0 capture. Open another family name to inspect its commands.](images/12.10.0-pose-family-left.png)

![Pose family commands, right columns. Historical Anim Assist 12.10.0 capture. These columns continue the same open family list.](images/12.10.0-pose-family-right.png)

### Choose a stage

A stage contains tools for one phase of animation:

- **All:** an overview with tools from every family.
- **Block:** Tween and Keys tools for blocking poses.

- **Spline:** Curves and Motion tools for splining and checking arcs.

- **Polish:** Timing and Pose tools for spacing and symmetry.

- **Deliver:** Bake tools for finishing and export.

To change the stage:

1. Click the stage button at the left of the row.

2. Click a stage in the list above it.

The list closes when you select a stage. If the Timeline is short, the five choices appear in one row inside the usable canvas.

Alternatively, select a stage with **Timeline > View > Anim Assist Stage**.

To move through stages with the wheel:

1. Hold **Ctrl** over the stage button.

2. Scroll the wheel.

Each workspace keeps its own stage in the saved file.

![Stage choices above the toolbar. Historical Anim Assist 12.10.0 capture. Click a stage name to select its row.](images/12.10.0-stage-choices.png)

### Use the tools

Buttons and icons run a tool when you click them. Key-type icons use your theme's Dope Sheet key colours. Breakdown diamonds are smaller. Extreme diamonds are larger. Handle icons use Graph Editor handle colours.

1. Hover an icon to read its name.

2. If a tool is greyed, hover it to read its requirement, such as selected keys.

3. Click an available button or icon to run its tool.

**Inline sliders** remain on the row. A click without a drag changes nothing.

1. Drag the track to preview a change.

2. Release the pointer button to apply the change.

During a drag, press **Esc** or right-click to cancel. Cancellation restores the original keys.

- For finer movement, hold **Shift** during the drag.
- To snap to the tool's step, hold **Ctrl** during the drag.

For an exact amount during a drag:

1. Type the number.

2. Press **Enter** to apply it.

**Ticks** are presets on a slider track. A drag snaps to nearby ticks. To apply a preset's exact amount, click its tick.

The number at an inline slider's right opens an exact-value field. To apply the tool's default amount, press **R**.

**Popout sliders** show their name on the row. A drag and a click open different popout modes.

For a temporary popout:

1. Drag the name to open the slider.

2. Release the pointer button to apply the change.

To keep the popout open:

1. Click the name once.

2. Drag the track to preview a change.

3. Double-click or click elsewhere to apply the change.

To cancel a popout change, press **Esc**.

To open a tool's **Tool Settings**, right-click the tool.

The ten numeric sliders are Breakdown, Smooth, Neighbors, To Reference, Ease, Amplify, Timing Scale, Timing Offset, Ripple and Reduce.

- **Breakdown** blends between the previous and next pose. Values below 0% or above 100% extend beyond those poses.
- **Timing Scale** changes key spacing. Below 100%, keys move closer and playback becomes faster. Above 100%, keys move farther apart and playback becomes slower. **Timing Offset** shifts the active object's Action in time.
- **Ripple** moves keys after the playhead by the selected frame amount. Movement toward earlier frames stops one frame after the playhead.
- **Reduce** removes keys if the resulting curve change stays below the selected tolerance. Keys disappear during preview. Press **Esc** to restore them.
- **To Reference** blends toward the reference frame. **Set Reference** stores that frame. **Amplify** scales motion around that reference.

Action-wide tools such as Timing Offset affect more than selected keys. Before changing a whole Action, check the hover text and scene options.

![Timing Scale popout. Historical Anim Assist 12.10.0 capture. The temporary slider opens above its toolbar control.](images/12.10.0-timing-popout.png)

### Default rows

Each row has a fixed default set. The following lists give the controls from left to right, in workflow order.

- **All:** The row starts with the Breakdown slider, with ticks at 25, 50 and 75%. The Smooth slider, -1f/+1f nudge icons and Timing Scale popout follow. Next are the Mirror Selected, Bake Object, Trails, Copy and Paste icons. The Trails eye shows or hides world motion trails.

![All row, left detail. Historical Anim Assist 12.10.0 capture. The full-row overview above locates Find and Settings.](images/12.10.0-all-row-left.png)

![All row, right detail. Historical Anim Assist 12.10.0 capture. The overlap joins this detail to the same row's left side.](images/12.10.0-all-row-right.png)

- **Block:** The Breakdown slider ranges from -25% to 125%. Its ticks are -25, 25, 50, 75 and 125. The -25 and 125 ticks extend beyond the bounding poses. The 25 and 75 ticks blend toward them. Inbetween and Distribute icons follow the slider. Next are Select Range, All Keys and Ends, followed by the Grow left and right icons. The Mark Keyframe, Breakdown, Extreme and Moving Hold diamonds follow. Copy and Paste icons finish the row.

![Block row, left detail. Historical Anim Assist 12.10.0 capture. Read this stage's controls beside their descriptions.](images/12.10.0-block-row-left.png)

![Block row, right detail. Historical Anim Assist 12.10.0 capture. The overlap joins this detail to the same row's left side.](images/12.10.0-block-row-right.png)

- **Spline:** The To Spline curve icon comes first. Neighbors, Ease and Smooth sliders follow. Next is the Set Reference target icon, followed by To Reference and Amplify sliders. Auto Clamped, Vector and Free handle icons follow. Trails finishes the row.

![Spline row, left detail. Historical Anim Assist 12.10.0 capture. Read this stage's controls beside their descriptions.](images/12.10.0-spline-row-left.png)

![Spline row, right detail. Historical Anim Assist 12.10.0 capture. The overlap joins this detail to the same row's left side.](images/12.10.0-spline-row-right.png)

- **Polish:** The row starts with -1f/+1f. The Timing Scale slider follows, with ticks at 80, 90, 110 and 120%. Next are the Timing Offset slider and Ripple slider. Ripple has ticks at -1 and 1. Snap follows and rounds key times. Select Opposite, Mirror Selected, Mirror Active and Swap icons finish the row.

![Polish row, left detail. Historical Anim Assist 12.10.0 capture. Read this stage's controls beside their descriptions.](images/12.10.0-polish-row-left.png)

![Polish row, right detail. Historical Anim Assist 12.10.0 capture. The overlap joins this detail to the same row's left side.](images/12.10.0-polish-row-right.png)

- **Deliver:** The Bake Object icon comes first, followed by Bake Preview Range and Smart Bake. The Reduce slider follows, with ticks at 0.001, 0.01 and 0.05. Bake Keys to Integer Frames comes next and retains a Reset Timing snapshot. One-Click Proxy & Bake follows. Next are Location, Rotation, World and Parent proxy icons. Bake Session and Remove Proxies follows those icons. Remove All Proxy Sessions finishes the row.

![Deliver row, left detail. Historical Anim Assist 12.10.0 capture. Read this stage's controls beside their descriptions.](images/12.10.0-deliver-row-left.png)

![Deliver row, right detail. Historical Anim Assist 12.10.0 capture. The overlap joins this detail to the same row's left side.](images/12.10.0-deliver-row-right.png)

**Find** includes tools that do not appear on the row. Examples include **To Stepped** and the **25/50/75% Breakdown** buttons.

**Copy** includes handles. Anim Assist's **Paste** uses the copied times. Native Paste can align with the playhead instead. Before using a native shortcut in place of these tools, check its tooltip.

The full-row overview above shows the control locations. Each row's detail figures overlap so the button labels remain readable. The family-list figures show additional commands.

### Find and More

**Find** (the magnifier) includes every tool.

1. Click the magnifier.

2. Type part of a tool name, family name or search term, such as "spacing" or "arc".

3. Click a tool to run it.

To browse instead of searching:

1. Leave the search field empty.

2. Select a family tab.

To add or remove a tool from the current row, click its pin.

A lit pin shows that the tool is on the current row.

Pinning affects the current row, regardless of the tool's family. **Find** and **Toolbar Settings** share one layout. Changes in either appear in both.

If N tools do not fit the Timeline's width, **More** appears as **+N** before Find. If all tools fit, More disappears.

To run a tool from More:

1. Click **+N**.

2. Click the tool.

To make more room, widen the Timeline or shorten inline sliders. Alternatively, display less frequently used tools as popout sliders or buttons.

![Find browses tools and their pins. Historical Anim Assist 12.10.0 capture. A lit pin places the tool on this row.](images/12.10.0-find-tools.png)

![More commands, left columns. Historical Anim Assist 12.10.0 capture. These tools did not fit the row.](images/12.10.0-more-left.png)

![More commands, middle columns. Historical Anim Assist 12.10.0 capture. These columns continue the same overflow list.](images/12.10.0-more-middle.png)

![More commands, right column and +N button. Historical Anim Assist 12.10.0 capture. Click +N to open this list.](images/12.10.0-more-right.png)

### Undo from Find, menus and the toolbar

In 12.11.1, **Find** and native menu actions use the tool's native Undo entry. They do not add a second entry for the same edit. Direct canvas toolbar actions keep their required Undo checkpoint. Slider completion and cancellation still use separate handling.

1. Finish the action or slider gesture.

2. Use native **Undo** to restore the previous result.

3. Inspect the keys and motion before continuing.

Some selection, settings navigation and other non-editing controls create no animation Undo entry. History entries differ between controls.

![Native Edit menu shows Undo, Redo and Undo History. Bforartists 5.2.3 capture. This capture has no available Undo entry.](images/5.2.3-native-undo-menu.png)

### Change what a row shows

1. Click **Settings** at the right of the row.

2. In **Row**, select **All**, **Block**, **Spline**, **Polish** or **Deliver**.

3. Click a family header to open its tools.

4. For each tool, select its **Display** mode.

5. For tools with an icon, select **Label or Icon**.

6. For an inline slider, set **Width** in the second field instead.

7. To move a tool within its family, click its **up and down arrows**.

8. To open the tool's Tool Settings, click its **gear**.

9. Click outside the panel or press **Esc** to close it.

Ordinary tools offer Hidden and Button display modes. Hidden removes the tool from the row. Sliders also offer Popout slider and Inline slider modes.

**Toolbar Settings** opens on the current row. Its **Row** selector previews another row during editing. Each family header shows its visible-tool count. A stage initially opens its home families. To filter tools by name, use **Find Tool** above the families.

Changes appear immediately. Closing the panel with an outside click or Esc keeps those changes. The panel has no OK button. **Revert Changes** restores every row to its state when the panel opened. Any row can contain any tool. Adding a tool from another family also adds that family's button to the row.

Icon display supports key types, handle types, grow selection, -1f/+1f, Inbetween, Distribute, To Spline, To Stepped, Set Reference, Copy and Paste. It also supports Mirror Selected, Mirror Active, Select Opposite, Swap, Bake Object, the four proxy types and Trails. Other tools show their names.

The gear or a right-click on a row tool opens **Tool Settings**. This panel configures display, range, default, width, precision, drag sensitivity, snapping, presets and **Presets as Ticks**. **Custom Range / Overshoot** permits a custom range within the tool's limits.

Each stage stores its own display, label, presets and ticks. All rows share the other amounts. Scene settings store masks, targets and breakdown anchors. **Scene Tool Options** opens these settings.

| Setting | Limit |
|---|---|
| Slider Width | 80–240 logical pixels. Narrow rows can shorten the drawn track. |
| Precision | 0–4 decimal places. |
| Sensitivity | 10–2,000 pixels across a popout slider range. |
| Presets | At most 12 finite amounts within the permitted range. |
| Breakdown custom range | -100% to 200%. |
| Timing Scale custom range | Minimum 1%. |
| Ripple custom range | -500 to 500 frames. |
| Reduce custom range | 0 to 1 tolerance units. |

The standard range on display can be narrower than the permitted custom range. These toolbar configuration limits do not recommend tolerances for production rigs.

![Toolbar Settings edits the Block row. Historical Anim Assist 12.10.0 capture. Display, width, ordering and tool gears appear together.](images/12.10.0-toolbar-settings.png)

![Tool Settings for Drag Breakdown. Anim Assist 12.11.1. Ranges, snapping and Presets as Ticks configure this slider.](images/12.11.1-tool-settings.png)

### Save, load and reset layouts

A layout contains all rows: All and the four stages.

| Control | Result |
|---|---|
| **Save As** | Names and saves the current layout. |
| **Load** | Restores a saved layout. |
| **Update Saved** | Replaces the saved layout with the current rows. |
| **Rename** and **Delete** | Rename or delete saved layouts. |
| **Recommended** | Identifies the fixed built-in layout. |
| **Reset Block to Defaults** | Restores that stage's default set. The control name changes to match the row under edit. |
| **Restore Recommended Layout** | Restores All and every stage. Saved layouts remain available. |

The add-on preferences store layouts. Layouts apply to every Timeline.

If Preferences do not save automatically, click **Save Preferences** in Toolbar Settings. This keeps changes after a restart.

Saved layout names contain 1–64 characters. The library supports at most 100 saved layouts. Loading a layout replaces the working arrangement. Before replacing a modified arrangement, read the unsaved-change control.

Stages start with fixed defaults. Adding a tool to All does not add it to a stage. Add the tool separately to each required stage. Add-on Preferences have no stage control. Each workspace uses the row's stage button.

The **Toolbar Settings** figure above shows the saved-layout controls. Use that same panel for row configuration and layout management.

### Hover explanations and shortcuts

To see a control's explanation, hold the pointer over it for about half a second. **Hover Explainers** controls the amount of help text. Its location is Edit > Preferences > Add-ons > Anim Assist > General.

Hover help, stage choices and slider popouts remain above the toolbar buttons. The Timeline shows one Anim Assist tooltip under the pointer. Toolbar help takes priority over the Scene Strip Gizmo beneath the row.

- **Full:** The text explains the tool's function, scope, requirements and use.
- **Short:** The text gives the name and one explanation line. For a greyed tool, it also gives the reason.
- **Off:** The row shows no Anim Assist hover text. Native Bforartists buttons in Anim Assist panels and menus still show the tool's name. Bforartists always prints a description line there. Setting fields retain their own one-line tooltip.

To disable every tooltip, use **Edit > Preferences > Interface > Tooltips**.

Hover text lists shortcuts only when a binding exists:

- **Shortcut:** This key binds to that exact Anim Assist tool. Row tools have no default shortcuts. To show a shortcut here, bind one in **Edit > Preferences > Keymap**.
- **Bforartists key:** This key runs a native command for the same function. Dope Sheet defaults include **Ctrl C** for Copy and **Ctrl V** for Paste. **A** selects all keys. **Ctrl Numpad +** grows selection on both sides. **R** scales key timing. **W** moves keys in time. Native commands can behave differently from Anim Assist tools. Native Paste uses the playhead instead of the copied times.

![Full hover explanation. Historical Anim Assist 12.10.0 capture. Current versions correct help positioning and priority. This capture's configured shortcut is not a default binding.](images/12.10.0-hover-explanation.png)

The **Bundled Anim Assist preferences** figure near installation shows **Full**, **Short** and **Off**. The **Settings** figure later in this guide shows shortcut and menu options.

## Dope Sheet: poses and key timing

The summary counts visible owners, editable curves and selected keys. It includes All/None selection controls. **Block & Tween** starts open. The remaining groups are **Timing, Keys & Channels, Pose & Match, Bake & Finish and Quick Shelf**.

1. Select an animated object or pose bones.

2. Show the Action channels.

3. Select the keys to edit.

4. Use **Block & Tween** for breakdown percentages, inbetweens and drag tools.

5. Expand the **Block & Tween** options for masks, presets and sampling choices.

6. Use **Timing** for spacing, offsets and ripple.

7. Use **Keys & Channels** for selection, key management and metadata.

8. Use **Pose & Match** for matching and mirroring.

9. Use **Bake & Finish** for bake and diagnostic tools.

To select handle sides, use Graph Editor. Dope Sheet retains advanced handle types. Scene Properties contains macro authoring and setup.

![Dope Sheet Block & Tween tools. Historical Anim Assist 12.8.0 capture. Select editable keys before using the actions.](images/12.8.0-dopesheet-tools.png)

### Breakdown anchors

At an empty frame, the surrounding keys anchor the blend. For example, values 0 and 10 produce 5 at 50%.

If the playhead already has a key, that key becomes the previous anchor. A current value of 5 and next value of 10 produce 7.5 at 50%. Repeating the operation can change the existing key again.

Before applying a breakdown, check the playhead, keys and masks.

The Dope Sheet figure above shows the breakdown actions and their options. Each numeric example describes a different playhead and key arrangement.

## Graph Editor: curve shaping

**Shape Curves** starts open with direct shaping, interpolation and handle actions. The groups are **Select & Channels, Shape Curves, Retime, Clean Up, Pose & Bake and Quick Shelf**. **Select & Channels** includes handle selection. **Clean Up** contains key management and diagnostics. **Pose & Bake** includes matching, mirroring, breakdowns and baking. Its collapsed **Breakdown Options** configure breakdown sampling. They do not configure general curve interpolation.

1. Select visible editable Action keys.

2. Apply the shaping or interpolation action.

3. Inspect the resulting curve and viewport.

Selected-key interpolation affects only selected, editable, visible keys. Key Manager timing commands respect editor visibility and channel locks. **Move Keys** and **Insert Frames** run immediately. To adjust their values, use native **Adjust Last Operation**.

Action selection helpers support **object Actions**. If the scope is empty, the helpers do not select from the entire active Action. They exclude detached pinned Actions and non-object sources. The sidebar explains these exclusions. Before using Action-wide tools, check their descriptions.

![Graph Editor curve-shaping tools. Historical Anim Assist 12.8.0 capture. Shape Curves groups shaping, interpolation and handle actions.](images/12.8.0-graph-tools.png)

## Drivers: inspect and shape driver responses

For driver tools, switch Graph Editor to **Drivers** mode. The **Anim Assist** sidebar and header menu show four driver-specific sections. Switching back to Action curves restores the Action groups described above. Drivers mode uses driver channels instead of Action-key tools.

### Driver & Target

This section counts selected visible drivers. For an active driver, it also shows **Owner**, **Property** and **Current value**. It shows an **Array index** when applicable. An unresolved property produces a warning.

1. Select a visible driver channel in the channel list.

2. Inspect its owner and driven property in **Driver & Target**.

3. Click **Frame Selected** to frame the selected curves.

4. To see the whole driver view, click **Frame All**.

**All Channels** and **None** change channel selection. **Select Owner** makes the driver-owning object active. Other selected objects remain selected. The owner must belong to the current view layer and permit visible object selection. Drivers on other datablocks cannot use this object-selection action.

If the owner is editable, **Muted** and **Locked** change the active driver's native channel settings. A single selected visible driver remains available for inspection after locking. To unlock it, disable **Locked**. If several selected channels make the active driver ambiguous, select the intended channel explicitly.

With an empty selection, all four sections remain visible and show guidance. They do not create a driver.

Before using these sections:

1. Create drivers with Bforartists' native driver workflow.

2. Connect those drivers.

![Selected driver and response controls. Historical Anim Assist 12.11.0 capture. Owner, property, channel selection and response actions share the sidebar.](images/12.11.0-selected-driver.png)

### Variables & Expression

This section counts variables. Scripted drivers show **Expression**. Other driver types show **Type**. The native **Drivers** tab contains the full editable variable and expression settings.

1. Unlock the intended driver channel.

2. Click that channel to make it the native active editable driver.

3. Open **Variables & Expression**.

4. Click **Open Driver Settings**.

5. Edit the variables, targets, driver type or expression in the native **Drivers** tab.

6. Return to **Anim Assist** for response actions and diagnostics.

The button opens the native sidebar category. It does not open a separate copy of the settings dialog. A locked driver can remain available for inspection without making native settings editable. Native sidebar tabs can appear in different orders. Identify **Drivers**, **Modifiers** and **Anim Assist** by name.

![Native Drivers settings after Open Driver Settings. Historical Anim Assist 12.11.0 capture. Variables, property targets and expression remain native controls.](images/12.11.0-native-driver-settings.png)

### Response Curve

The horizontal axis represents driver input. The vertical axis represents driven output. Response points map input to output. They differ from Action keys, which use animation time.

1. Select the visible driver channels to edit.

2. Unlock those channels.

3. Check that their owners are editable.

4. For point-level changes, select response points or handle sides.

5. Select **Interpolation** or **Handles** in **Response Curve**.

6. Inspect the resulting response and driven property.

| Control | Scope and result |
|---|---|
| **Interpolation** | Changes selected response points in selected visible editable driver channels. Choices are Constant, Linear and Bezier. |
| **Handles** | Changes selected handle sides in those channels. If a control point is selected, the action changes both handles. |
| **Extrapolation** | Changes selected visible editable driver channels outside their endpoint range. Constant holds output. Linear continues the endpoint slope. |
| **Add Modifier (Active)** | Adds the chosen response modifier to the active editable driver only. It does not affect every selected channel. |
| **Open Modifier Settings** | Opens the active driver's native **Modifiers** tab. |

Point actions require selected points or handles. Extrapolation requires selected editable channels. Modifier actions require an active unlocked driver with an editable owner. Opening native settings also requires an editable driver that is natively active. If a control is disabled, hover it to read its requirement.

Interpolation, handles, extrapolation and modifier creation support native **Undo** and **Adjust Last Operation**. These actions affect only the specified drivers. They exclude Action keys and unrelated drivers. Runtime qualification does not cover every native modifier type separately.

The selected-driver figure above locates **Interpolation**, **Handles**, **Extrapolation** and **Add Modifier (Active)**. The native modifier destination appears below.

![Native Modifiers settings for the active driver. Historical Anim Assist 12.11.0 capture. Open Modifier Settings selects this native tab.](images/12.11.0-native-modifier-settings.png)

### Diagnostics

1. Select the visible driver channels to inspect.

2. Open **Diagnostics**.

3. Click **Check Selected Drivers**.

4. Read the result popup.

5. Correct the reported targets, paths, bones or expression in the appropriate native settings.

6. After correcting a dependency, click **Update Dependencies**.

**Check Selected Drivers** checks evaluation validity, missing targets, unresolved property paths and missing bones. It also reports linked/read-only owners, locked channels and muted drivers. If a property target has an enabled fallback value, the check does not report an unresolved-path failure for that target.

Checks inspect only selected visible drivers. They do not scan the entire file. They do not prove that every expression produces the intended motion. **Update Dependencies** refreshes the selected drivers' owners and reevaluates the view layer. It does not repair expressions, reconnect targets, change response points or delete drivers.

![Selected-driver diagnostic results. Historical Anim Assist 12.11.0 capture. Read each reported issue before editing its native target or expression.](images/12.11.0-driver-diagnostics.png)

## NLA: arrange clips and blend corrections

**Arrange & Time** and **Blend & Corrections** start open. **Actions & Tracks, Bake & Finish and Quick Shelf** start closed. The summary shows the owner, active clip, source Action, selected clip count, scene range and source range. Scene frames give the clip's position. Source frames give the Action interval inside the clip.

### Arrange clips

1. Select the Action clips to change.

2. Click the reference clip's body to make it active.

3. Check that the reference clip remains selected.

4. Click **-1f/+1f** to nudge, or **Move Selected Clips** for a native move.

5. To align clips with the active selected clip, use **Align Starts/Ends**.

6. To place clips consecutively from the reference clip's start, use **Sequence Clips**.

7. Change the step or sequence gap in **Adjust Last Operation**.

8. Expand **Timing Options** for active-clip scale, repeat, reverse and scene start/end.

Timing uses scene frames. The tools reject locked or overlapping batches without partial changes. Arrangement pauses during source editing. These tools cannot edit transition, meta or sound strips.

![NLA arrangement and correction controls. Historical Anim Assist 12.8.0 capture. The selected correction clip uses Combine blending and animated influence.](images/12.8.0-nla-arrange.png)

Before using active-clip actions, check that the summary shows the clip's owner, clip and Action.

### Edit sources and manage sharing

**Edit Action** enters native NLA Tweak Mode. **Open Dope Sheet/Open Graph Editor** reuses a suitable unpinned editor or switches the current area. Native Tweak Mode maps source time for moved, scaled, repeated and reversed clips.

To return to arrangement after editing:

1. Use the editor selector to return to NLA.

2. Click **Finish Editing**.

Editing a shared Action can affect other clips. The summary warns about sharing and reports excluded sources. Mute and Solo affect evaluation.

| Control | Result |
|---|---|
| **Make Selected Clips Unique** | Separates the selected clips' source Actions. |
| **Duplicate Independent** | Copies the Action. |
| **Duplicate Linked** | Shares the Action. |
| **Move Selected Tracks Up/Down** | Reorders tracks. It does not move clips between tracks. |

**Push Down Active Action/Stash Active Action** operate on the active owner's assigned Action. Push Down requires enabled NLA evaluation. If no clip is selected, the summary offers **Add Existing Action Clip** for an editable active object.

![Actions and Tracks. Native panel popover, Anim Assist 12.11.1. The clip is selected and active. Duplication and Make Selected Clips Unique are available.](images/12.11.1-nla-actions.png)

### Add a transform correction

1. Select one supported source Action clip.

2. Click **New Transform Correction**.

3. Select the new correction clip.

4. Click **Edit Correction**.

5. Edit its transform keys in native Tweak Mode.

6. After editing, click **Finish Editing**.

7. Keep unmodified channels neutral: location zero, rotation zero/identity, scale one.

8. At the playhead, click **0%, 50% or 100%** to key the active clip's influence.

Native **Combine** blending applies the correction over the source motion. To use another influence value, enter it in **Adjust Last Operation**. At zero influence, the correction contributes no motion.

Creation adds an independent correction Action and track above the source. Corrections support object and pose-bone transforms. Creation blocks constrained/driven rigs, unresolved bones and non-transform source channels. It explains the reason. These corrections are separate from the general Animation Layers tools in Scene Properties.

Blend and Animated Influence are native strip settings. If Animated Influence is disabled, the sidebar identifies the automatic blend envelope. **Blend Options** shows Automatic Blend, blend-in/out and extrapolation. Influence buttons create native influence keys. They do not create pose keys in the source Action.

The **NLA arrangement and correction controls** figure above shows the correction track, **Edit Correction**, **Combine** blending and influence buttons.

### Bake while retaining the source stack

1. Select a clip for the owner to bake.

2. Open **Bake & Finish**.

3. Check the owner and scene range on display.

4. Click **Bake to New Action**.

5. If required, adjust the range and step in **Adjust Last Operation**.

6. Check the output name and range.

7. Before activating the bake, mute or remove active constraints that would apply again.

8. Select **Use Latest Bake (NLA Off)**.

The bake writes evaluated object/pose transforms into a new Action and retains it. The new Action initially remains **unassigned**. Original Actions, clips, parents and constraints remain. Activating the bake is a separate operation. **Use Latest Bake (NLA Off)** assigns the result and disables source-stack evaluation.

Save the source scene for comparison. Renaming does not change output ownership. Another object that takes the old name cannot receive that output. **Remove Empty Tracks** removes empty tracks separately.

NLA Quick Shelf shortcuts make sources unique, edit the active source and bake the owner. They do not run general key-editing macros against strips.

![Retained NLA bake. Native panel popover, Anim Assist 12.11.1. Output covers frames 1 to 24 at step 1.](images/12.11.1-nla-retained-bake.png)

## Scene Properties and broader tools

**Scene Properties > Anim Assist** contains **Quick Shelf, This Pose, Whole Animation, Rig, Face, Setup (once per rig), Settings, Help & Diagnostics**.

| Group | Work |
|---|---|
| **This Pose** | Transform offsets, matching, space switching and pose mirroring. |
| **Whole Animation** | Active-Action offsets, motion trails and Animation Layers. |
| **Rig** | Locators, proxies, bake settings and session cleanup. |
| **Face** | Lipsync setup, target wiring, preview and bake controls. |
| **Setup (once per rig)** | First-run setup and workspace/system procedures. |
| **Settings** | Shared settings, optional pie shortcut and macro authoring. |
| **Help & Diagnostics** | Tool help, diagnostic reports and recovery guidance. |

**Search** finds existing tools. **Recents** lists completed tools, newest first. **Repeat Last** uses the newest entry. Canceled or unfinished commands do not enter Recents. Older files sort Recents by timestamp. **Toggle Shelf Mode** cycles shelf modes.

To configure macros, open **Scene Properties > Anim Assist > Settings**.

The **Scene home** and **First-run setup** figures near installation show the shared entry points. The following figures show each registered panel in a native popover.

![Settings. Native panel popover, Anim Assist 12.11.1. The optional pie shortcut starts disabled. Header menu switches control each editor.](images/12.11.1-settings.png)

![Macro settings. Native panel popover, Anim Assist 12.11.1. Preset macros, Add Macro and Batch Mode appear together.](images/12.11.1-macros.png)

### Offset, match and mirror

1. Select the animated owner and the intended keys or pose bones.

2. Open **Dope Sheet > Anim Assist > Block & Tween > Transform Offset** for key offsets.

3. Select the channel mask.

4. Select the offset scope.

5. Set the offset amounts.

6. Select the transform space.

7. Use **Nudge Current Frame**, **Offset Selected Keys** or **Interactive Drag** for the intended scope.

8. Before using **Reapply Last** or **Invert Last**, inspect the result.

![Transform Offset controls. Native panel popover, Anim Assist 12.11.1. Amounts, channels, scope and falloff belong to the Dope Sheet panel.](images/12.11.1-transform-offset.png)

**Scene Properties > Anim Assist > This Pose > Pose Offset** nudges selected pose bones or moves them with interactive dragging. Pose Offset requires **Pose Mode**.

Current Frame, Selected Keys and Frame Range are separate offset scopes. Frame-range falloff distributes the offset over time. Ease In/Out falloff does not change curve tangents. These tools use the **Individual Origins** pivot. They do not orbit around the median or cursor.

Matching offers World, Parent, Target, channel-specific, visual/evaluated and local-matrix actions. Target matching generally needs two selected objects.

For target matching:

1. Select the target first.

2. Select the object to change.

**Align Selected Objects to Active** uses the active object as its reference. These controls do not automatically understand every rig.

Before using compensated space-switch or IK/FK workflows:

1. Configure the switch-property mappings.

2. Configure the chains.

Mirror tools require an armature in **Pose Mode**. **Select Opposite** changes selection. Frame/range mirror actions can also insert keys.

Before using **Mirror Pose**, **Selected** or **Swap**:

1. Check pair detection and naming exceptions.

2. Check mirror space and axis.

3. Check channel filters.

4. Read the tool's description.

![Transform Match. Native panel popover, Anim Assist 12.11.1. Target actions require the appropriate selected target objects. Open Settings for channels and axes.](images/12.11.1-transform-match.png)

Open **Dope Sheet > Anim Assist > Pose & Match** for the full matching and mirror settings.

![Pose Offset with an animated armature. Native panel popover, Anim Assist 12.11.1. These quick controls nudge selected pose bones.](images/12.11.1-pose-offset.png)

![Quick mirror controls with an active pose bone. Native panel popover, Anim Assist 12.11.1. Mirror Pose, Mirror Selected and Swap Poses are available.](images/12.11.1-pose-mirror.png)

### Action offsets and motion trails

**Whole Animation** includes active-Action offsets and an optional range mask. These offsets can affect more than selected keys.

Before enabling an Action-wide edit:

1. Configure the mask.

2. Configure the range.

To use motion trails:

1. Select the object or pose-bone targets for the trail settings.

2. Open **Whole Animation > Trajectory Overlay**.

3. Select the display mode.

4. Select the sample scope.

5. Set the sample step.

6. Click **Enable Overlay**, or use the Timeline **Trails** eye.

7. After changes, refresh the trails when required.

8. Run arc diagnostics to identify motion for inspection.

9. Inspect the flagged motion.

Trail options include frame/key ticks, frame numbers, velocity, tangent, ghost and colour displays. Around-current and custom ranges limit sampling. **Max Samples** limits the sample count. Arc diagnostics identify motion that needs inspection. They do not certify animation quality or automatically solve a rig.

![Action offset mask. Native panel popover, Anim Assist 12.11.1. Use Mask limits the Action offset to the configured range and blends.](images/12.11.1-action-offset.png)

![Trajectory Overlay settings. Native panel popover, Anim Assist 12.11.1. Choose the display mode, sampling range and step before enabling the overlay.](images/12.11.1-motion-trails.png)

### Locators, proxies and bake sessions

1. Open **Rig > Proxy & Bake**.

2. Select the intended object.

3. Select a locator or a Translation, Orientation, World-Space or Parent-Space proxy.

4. Set the bake range for the selected bake command.

5. Set the bake step.

6. Select the bake channels.

7. Run the bake command.

8. Inspect the baked motion.

9. Only after checking the baked result, use session cleanup.

Locator controls create locators at targets, selection averages or the cursor. They also parent, constrain, match and bake between locators and targets. Before using paired controls, read their arrow direction.

**Smart Bake** combines transform baking with key reduction. **Reduce Keys** simplifies existing keys according to its tolerance. Available ranges are scene, Action, custom, selected-key and preview. These general bake commands differ from NLA's retained **Bake to New Action** workflow.

**One-Click Proxy & Bake** records world motion in its own proxy session before baking. **Bake Session and Remove Proxies** cleans that session. **Remove All Proxy Sessions** affects a broader scope. Existing qualification does not certify every parented, constrained or production-rig case. Before removing helpers, compare the result.

![Proxy and bake setup. Native panel popover, Anim Assist 12.11.1. No active proxy session is shown. Expand Bake Settings before baking.](images/12.11.1-proxy-bake.png)

The figure shows setup controls before session creation. An active session makes cleanup available.

### Animation Layers

1. Open **Whole Animation > Animation Layers**.

2. Enable the layer system.

3. Click **Create Base Layer** for the current animation.

4. Add a working layer.

5. Select the working layer.

6. Select its blend mode.

7. Set its weight.

8. Configure its bone assignments.

9. Before inserting keys, select the intended working layer.

10. Preview with the layer's Solo, Mute and Lock controls.

An empty assignment list includes all bones. In Pose Mode, the visible panel offers **Assign**, **Remove** and **Select** for bone assignments. Each layer row contains weight, Solo, Mute, Lock and Auto Key.

This registered panel does not show **Edit Active Only**, **Auto-Assign on Key** or all advanced layer controls. Native operator search offers registered actions such as **Assign by Pattern**, **Merge Down** and **Flatten All Layers**. Before merging or flattening, inspect the stack. These layers are separate from NLA transform-correction clips.

![Animation Layers. Native panel popover, Anim Assist 12.11.1. The layer rows expose weight, Solo, Mute, Lock and Auto Key.](images/12.11.1-animation-layers.png)

### Lipsync

1. Open **Face > Lipsync**.

2. Enable lipsync.

3. Add a lipsync layer with **+**.

4. Select the layer.

5. In **Audio**, bind a **WAV** file.

6. Select **Shape Keys**, **Bones** or **Both** as the target.

7. Select the mesh or armature target.

8. Configure **Shape Key Wiring** or **Bone Rig Wiring** for the selected viseme library.

9. Verify the wiring entries' target names.

10. Check anticipation, frame offset and the analysis backend.

11. Click **Bake**.

12. Inspect the mouth motion.

Before **Rebake**, use **Lock Selected Keys** to preserve selected manual work.

**Live Preview/Baked** shows the layer's state. Shape-key output requires a mesh with wired shape keys. Bone output requires a valid animation layer, armature and wiring. **Autofill** supplies wiring entries. **Viseme Captures > Capture** stores a custom pose.

For the required preview or baked workflow, use the state control.

Amplitude analysis requires no external phoneme executable. Optional Rhubarb analysis requires a configured **Rhubarb Path**. Before relying on output, read backend-fallback and missing-layer reports. If a speaker strip exists, the speaker overlay shows audio in Dope Sheet/Timeline.

The sidebar's **Clear** removes automatic output and keeps marked manual work. **Rebake** also keeps manual overrides. **Highlight Manual Keys** shows protected edits. Changing the audio marks the layer stale. Before baking again, resolve the reported WAV, target and layer issues.

![Lipsync after setup. Native panel popover, Anim Assist 12.11.2 candidate on official Bforartists 5.2.3, Blender 5.3 Alpha base. Audio is assigned. Mesh and jaw targets remain blank. The cue table is empty before target wiring and baking.](images/12.11.2-lipsync-setup.png)

## Troubleshooting and verification limits

If a key operation does nothing:

1. Check the active editor.

2. Check selected editable keys and visible channels.

3. Check locks, owner and Action.

4. Inspect Action data and editor filters.

Toolbar visibility alone does not prove that the operation inserted keys. Native Insert Keyframe remains the normal mesh/object keying workflow.

For an issue report, include the add-on version, Bforartists build, exact command and a small reproducible scene.

If an NLA action is unavailable:

1. Check track locks and mute/Solo exclusions.

2. Check for a missing Action, disabled NLA evaluation or active Tweak Mode.

3. Before arranging clips, click **Finish Editing**.

4. For correction creation, read the unsupported-rig/channel explanation.

After changing timing or baking:

1. Inspect the motion.

2. If needed, use native Undo.

3. Save the scene.

4. Reopen it before relying on the result.

If driver settings are unavailable, select an unlocked driver channel to make it natively active. A locked driver can remain visible for inspection and unlocking. If several selected drivers have no clear active target, the tools do not choose one. Point-editing actions require selected response points.

The [12.11.1 release notes](https://github.com/Axleonex/B4Artists_Toolkit/blob/a8b6b12d4f9ae7b2cd00c14af9f2f90301420c7a/docs/anim_assist/releases/12.11.1/RELEASE-NOTES.md) describe the Timeline Undo dispatch correction. The [12.11.0 qualification](https://github.com/Axleonex/B4Artists_Toolkit/blob/a8b6b12d4f9ae7b2cd00c14af9f2f90301420c7a/docs/anim_assist/releases/12.11.0/qualification.md) records targeted Drivers tests and native cursor observations on Bforartists 5.2.0. These cover channel scope, native settings navigation and modifier Undo/Redo. The records also cover layout registration and 11 animation-editor regression scenarios. These results come from earlier tests. The manual update did not repeat those tests.

The [12.10.0 qualification](https://github.com/Axleonex/B4Artists_Toolkit/blob/a8b6b12d4f9ae7b2cd00c14af9f2f90301420c7a/docs/anim_assist/releases/12.10.0/qualification.md) covers stage toolsets. The [12.9.1 qualification](https://github.com/Axleonex/B4Artists_Toolkit/blob/a8b6b12d4f9ae7b2cd00c14af9f2f90301420c7a/docs/anim_assist/releases/12.9.1/qualification.md) covers the stage tab fixes. The [12.8.0 qualification](https://github.com/Axleonex/B4Artists_Toolkit/blob/a8b6b12d4f9ae7b2cd00c14af9f2f90301420c7a/docs/anim_assist/releases/12.8.0/qualification.md) records 16 native interaction groups, Undo/Redo and workspace reload. It also records 98 panel registrations and five Timeline layout regressions. Its evidence includes mesh key insertion and sidebar captures at 220, 280 and 360 px.

These tests do not certify every operator, modifier, production rig or host build. Older slider and lipsync evidence remains historical. The November 20 documentation review checks current source, links and PDF presentation. It does not provide formal STE dictionary certification.

The 12.11.2 candidate's **Setup Lipsync** completed on official Bforartists 5.2.3, Blender 5.3 Alpha base. It created a sound strip. The new figure shows the resulting layer before target wiring and baking. It does not demonstrate baked mouth motion.

If setup reports **compiled without Audaspace support**, use a Bforartists build with audio support. Setup can finish without creating its sound strip. The supplied custom build, with a Blender 5.4 Alpha base, produced this result.

Use the **Dope Sheet**, **Graph Editor** and **Selected driver** figures to locate scope and selection summaries.

## Screenshot sources and limits

The Timeline and toolbar-setting screenshots retain their historical capture labels. The selected-driver captures come from 12.11.0 qualification. The editor overview captures come from 12.8.0 qualification. The 12.5.0 separate-strip screenshots remain historical evidence.

The user-supplied native 12.11.1 captures show empty scopes. They document the visible layout. They do not demonstrate a completed edit:

- [Drivers sidebar with no selected driver](images/12.11.1-native-drivers-empty.png).
- [Action Graph sidebar with no editable curves in scope](images/12.11.1-native-action-graph.png).

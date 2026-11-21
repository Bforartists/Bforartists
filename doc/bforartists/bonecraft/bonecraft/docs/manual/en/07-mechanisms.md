# Mechanisms

[← Contents](index.md)

## What Mechanisms does

Mechanisms builds mechanical rigs from hard-surface parts. It supports hinges,
slides, telescopes, pistons, gears, followers and complete transformations controlled
by one slider. It builds ordinary Blender bones and constraints. You can inspect
and change everything it builds. The rig works in Blender without scripts.
Engines receive the `DEF-` bones. Export of baked mechanism motion to engines
comes later (see Limits of this version).

BoneCraft supplies the tools. You supply the weapon parts.

A complete worked example, with a screenshot for every step, is [Tutorial: Crescent Rose with Mechanisms](12-crescent-rose.md).

Words used in the panels and in this page:

| Word | Meaning |
|---|---|
| *Part* | A piece that moves as one solid block: an object, or a loose piece of one mesh. A part can ride on another part. |
| *Joint* | How a part may move: Hinge (turns), Slide (moves), Telescope (extends nested segments). |
| *Link* | What moves a part for you: Piston, Gear Link, Follow. |
| *Handle* | The bone you drag in the viewport. Each joint has one. Its value is also a slider in the panel. |
| *Sequence* | A transformation played by one slider, made of steps. |
| *Form* | A saved set of handle and Sequence values, such as "Stowed" or "Rifle". |

## Where it is

- **BoneCraft tab → Mechanisms** in the 3D Viewport. The BoneCraft tab is on
  the left Tool Shelf (press **T**) unless you moved it to the right sidebar
  (**N**) in Preferences. It sits between Skin and Review. It shows when a mesh
  is active (to start a rig) or when an armature with mechanisms is active. Otherwise,
  it explains what to select.
- **Properties editor → Scene tab → Mechanisms**, right after Rig Builder. It is
  shown while Preferences → Tabs → Scene Properties → Show is on. With nothing
  usable selected it shows one line: "Select a mesh
  to start, or an armature with mechanisms." Switching the BoneCraft viewport tab
  off does not remove it. The Scene Properties switch hides the Scene copy only.
  The `mechanisms` tool switch (**Preferences → Add-ons → BoneCraft → Tools**)
  removes the tool from every location.
  Scene-tab sections start collapsed, so click **Mechanisms** to expand it.
- **Object menu → Mechanisms** gives shortcuts to add parts, joints and links,
  and to test motion.
- **Viewport toolbar → Build Mechanism** starts a guided joint or link from a
  click on a part, in Object Mode or Pose Mode.

To prepare Build Mechanism:

1. Add the parts.
2. Select the mechanism rig or one of its parts.
3. In the tool header, select the type.

Inside Mechanisms there are four subsections: **1. Parts**, **2. Joints &
Links**, **3. Sequences** and **4. Controls**. They appear once the rig has
parts. Before that you see only **Add Parts from Selection**.

Every button is one undo step. If a build fails, BoneCraft restores everything
the build changed. The panel shows the reason.

![Mechanisms in the BoneCraft tab.](../images/crescent-rose/en/03-mechanisms-section.png){style="max-width:100%;max-height:155mm;width:auto;height:auto"}

*Historical workshop capture. Mechanisms in the BoneCraft tab.*

## Parts

1. Select the part objects (or one mesh made of loose pieces) in Object Mode.
2. Click **Add Parts from Selection**.
   - Several objects: one part per object. Each object is parented to its part's
     bone and stays where it is.
   - One mesh with loose pieces: one part per piece. Each piece gets a vertex
     group for its bone and the mesh gets an Armature modifier.
   - The first time, BoneCraft makes the rig (an armature) for you.
3. Select a part in the list to edit it.

For each part:

- **Rides on:** choose the part this one moves with. A child part follows its
  parent part. "the rig" means it rides on the rig's root.
- **Size** sets the bone length, which sets the handle size.
- **Edit Pivot** puts a marker on the part. **Apply Pivot** moves the part's
  bones to the marker. The object stays in place.
- **Apply Transforms** appears when an object part has unapplied rotation or
  scale. Unapplied transforms tilt the axes. When this button appears, click **Apply Transforms**.
- The **X** button removes the part. It refuses while a joint, link or other
  part uses it, and names them.
- **Merge for VRChat** requires two or more object parts. Merge only parts rigged to
  the mechanism rig alone. Do this last. The action joins the object parts into
  one mesh with one vertex group per former object and an Armature modifier.
  The joined parts become loose parts of that one mesh. The merge removes vertex groups
  named after this armature's bones, except the part's own `DEF-` bone.

To change a part's pivot:

1. Select **Edit Pivot**.
2. Drag the marker to where the part should turn or slide from.
3. Click **Apply Pivot**.

You can rename a part's object: parts are tagged on their objects, so the part
finds its object again. A copy of the object (Shift+D) does not take over the
part. If a part's object is deleted, the part shows "Part '<name>' is missing"
with **Reassign** and **Delete**. Other mechanisms keep working.

- **Reassign** uses the mesh you have selected. It refuses a non-mesh, and it
  refuses an object that another object part already uses. Loose parts of one
  mesh may share that mesh.
- **Delete** removes the part (see Editing below for when it is refused).

![Added parts and the selected part's pivot controls.](../images/crescent-rose/en/04-add-parts.png){style="max-width:100%;max-height:155mm;width:auto;height:auto"}

![Added parts and the selected part's pivot controls.](../images/crescent-rose/en/06-edit-pivot.png){style="max-width:100%;max-height:155mm;width:auto;height:auto"}

*Historical workshop capture. Added parts and the selected part's pivot controls.*

## Joints and links, one example each

**Add Joint** starts a guided joint build. **Add Link** starts a guided link build.
Both work from the viewport tab and the Properties editor's Scene tab.
From the Scene tab, the guide uses the largest 3D Viewport on the screen.

Alternatively, use the toolbar:

1. Activate Build Mechanism in the viewport toolbar.
2. In the tool header, select the joint or link type.
3. Click its first part.

That click starts the same guide and supplies its first pick. Continue with the picks
and axis choices requested in the viewport. The Add Joint and Add Link menus remain available.

**Align to Selection** supports angled hinges. It requires the part's mesh in
Edit Mode with one edge or face selected when you press **A**. The guide ignores **Tab**.
Before using **Align to Selection**, prepare the mesh:

1. On the part's mesh, enter Edit Mode.
2. Select one edge or face.
3. While remaining in Edit Mode, start **Add Joint → Hinge**.
4. Click the part.
5. Press **A**.

If nothing usable is selected, the guide shows a message. You can then press another key.

Short rules for every guided build:

- Click parts in the viewport. Clicked parts get an outline and a number.
- When a step needs an axis, press **X**, **Y** or **Z**.
- With **Align to Selection** prepared as above, press **A** to align to the selection.
- The last step previews the mechanism moving in a loop. **Enter** keeps it.
  **Esc** removes it.
- The header and status bar show a full sentence for each step. With Show
  Helpers off they show a short label.

Each row of the Joints & Links list has four icon buttons: **Test** (play
triangle), **Edit** (pencil, shows the settings), **Detach** (broken chain) and
**Delete** (X).

After the build, the selected item in the list shows only the settings its
type uses.

### Hinge

Blade Hinge, 0°…90°:

1. Use Add Parts from Selection with a Blade part.
2. Select **Add Joint → Hinge**.
3. Click the Blade.
4. Press **X**.
5. Press **Enter**.

The build creates a half-circle handle, `CTRL-Blade`, and a *Blade Hinge* in the list.

6. Set **Min** to 0.
7. Set **Max** to 90 (° for a Hinge).
8. To test the hinge, drag the half-circle handle.

The handle stops at 90°. **Set Min** and **Set Max** copy the handle's current pose into the limits.

A limit that is under a full turn must stay within −180°…180°. Limits such as
170°…190° are refused with a message. A range of a full turn or more (for
example −180°…180°) spins freely with no limit.

![Hinge limits and handle controls.](../images/crescent-rose/en/10-head-hinge-limits.png){style="max-width:100%;max-height:155mm;width:auto;height:auto"}

*Historical workshop capture. Hinge limits and handle controls.*

### Slide

Barrel Slide, 0…0.3:

1. Select **Add Joint → Slide**.
2. Click the Barrel part.
3. Press **Y**.
4. Press **Enter**.

The build creates an arrow handle.

5. Set **Min** to 0.
6. Set **Max** to 0.3 (scene units).
7. To test the slide, drag the arrow.

The barrel slides and stops at 0.3.

![Slide travel limits for the selected part.](../images/crescent-rose/en/20-bolt-slide.png){style="max-width:100%;max-height:155mm;width:auto;height:auto"}

*Historical workshop capture. Slide travel limits for the selected part.*

### Telescope

Mast with three segments:

1. Make the base and three segment parts.
2. Select **Add Joint → Telescope**.
3. Click the base.
4. Click each segment, in order from the base outwards.
5. Press **Enter**.
6. Press the axis key.
7. To keep the build, press **Enter**.

The build creates one arrow handle on the base. **Length** is the total travel.
**Shares (empty = even)** splits that travel between the segments.

To test custom shares:

1. Set **Length** to 1.
2. Type `0.5, 0.25, 0.25` in **Shares (empty = even)**.
3. Drag the arrow handle.

All three segments extend by their shares. The shares must total Length, so the tip travels the full length.
Invalid text such as `0.5, abc` produces a message. Each segment needs one numerical share, and the shares must total Length.
**Set Max** sets Length from the handle's pose.

![Telescope length and segment shares.](../images/crescent-rose/en/22-telescope.png){style="max-width:100%;max-height:155mm;width:auto;height:auto"}

*Historical workshop capture. Telescope length and segment shares.*

### Piston

Lift: cylinder on the frame, rod on the arm.

1. Give the arm a Hinge.
2. Set the arm to ride on the frame.
3. Select **Add Link → Piston**.
4. Click the cylinder part on the frame.
5. Click the rod part on the arm.

The build creates a Piston with no handle. Each part points at the other's attach point.
Optional **Stretch** stretches the rod for springs and cables.

6. To test the Piston, move the arm's handle.

The piston follows. If nothing moves the Piston yet, the build works but has no preview. **Test** reports that condition.

![Piston settings for the connected parts.](../images/crescent-rose/en/18-piston-settings.png){style="max-width:100%;max-height:155mm;width:auto;height:auto"}

*Historical workshop capture. Piston settings for the connected parts.*

### Gear Link

Gear 20:40:

Both parts need a joint first. The driving part needs a Hinge.
For Gear and Belt, the driven part needs a Hinge. For Rack, it needs a Slide.

1. Select **Add Link → Gear Link**.
2. Click the driving part.
3. Click the driven part.

For the tooth-count method:

1. In the link's settings, set **Source Teeth** to 20.
2. Set **Target Teeth** to 40.

Alternatively, type a **Ratio**. **Kind** is Gear, Belt or Rack. **Reverse** flips the direction.
To test the link, turn the source.

With **Kind** Gear, the target turns −0.5× as far (+0.5× with Belt).
A Gear reverses direction. A Belt keeps the direction. A Rack converts rotation into a slide.
Its distance per radian equals **Ratio** × **Pinion Radius**.

How BoneCraft builds it depends on the source Hinge's range:

- Under a full turn: a Transform constraint. It follows everything that moves
  the source, Sequences included.
- A full turn or more: a driver that needs no Python. The target spins forever
  with the source. It follows handles and gears only. The Rig Validator warns
  when a Sequence or Follow would be lost.

![Gear Link controls before entering the 20:40 example. The pictured ratio is 1.00 and both tooth counts are 0.](images/screenshots/bc38-gear-link.png){style="max-width:100%;max-height:155mm;width:auto;height:auto"}

*Native test-build popover, BoneCraft 9.2.19 candidate. Bforartists 5.2.3, Blender 5.4 Alpha. Gear Link controls before entering the 20:40 example. The pictured ratio is 1.00 and both tooth counts are 0.*

### Follow

Blade 0–90° lifts Cover 0–40°:

Both parts need a Hinge or a Slide. A source Hinge needs limits under a full turn.
BoneCraft refuses a free-spinning source.

1. Select **Add Link → Follow**.
2. Click the leading part (Blade).
3. Click the following part (Cover).

Initially, each mapping range spans its joint's full range.

4. Set **Source Range** to 0…90.
5. Set **Target Range** to 0…40.
6. To test Follow, move the Blade handle.

The Cover follows. Past either range end, the target holds.
To reshape the mapping in the Graph Editor, enable **Curve**.
BoneCraft never overwrites your curve (see Editing below).

![Follow source and target ranges.](../images/crescent-rose/en/16-follow-ranges.png){style="max-width:100%;max-height:155mm;width:auto;height:auto"}

*Historical workshop capture. Follow source and target ranges.*

### Sequence

Record steps to fold a weapon:

1. In **3. Sequences**, click **Add Sequence**.

This creates a slider handle named `CTRL-SEQ-<name>`.

2. Click **Move Slider to End**.

The slider jumps to its end (1). The button becomes Record Step followed by the next step number.

3. Pose the joint handles for the first step.
4. Click Record Step 1.

Each moved handle becomes a step with its target value. The handles return to zero.

For each additional recording:

1. Click **Move Slider to End**.
2. Pose the joint handles for the next step.
3. Click the current numbered Record Step button.

By default, each new step takes the next quarter of the slider. For each recorded step:

1. Set **Target**.
2. Select the ease: Linear, Ease In, Ease Out, Ease In Out or Snap.
3. Set **Start**.
4. Set **End**.

Outside its slice, a step holds its end value. Several Sequences can stack.
To test the Sequence, click **Test**. The slider plays 0 → 1 → 0.

Next to the step-recording button and **Test**, the selected Sequence has **Detach**
(broken chain) and **Delete** (X). A held Sequence (for example a step whose
curve you reshaped) shows its message and a **Restore** button. Restore
regenerates the steps from the record. Keep mine is not offered for a Sequence.

![Sequence creation, recorded steps and timing.](../images/crescent-rose/en/23-add-sequence.png){style="max-width:100%;max-height:155mm;width:auto;height:auto"}

![Sequence creation, recorded steps and timing.](../images/crescent-rose/en/25-sequence-steps.png){style="max-width:100%;max-height:155mm;width:auto;height:auto"}

*Historical workshop capture. Sequence creation, recorded steps and timing.*

## Test

**Test** (the play button in the list, and in 3. Sequences) sweeps one
mechanism through its full range and back. It writes no keys and puts the pose
back when it ends. To stop the test early, press **Esc**. This also restores the pose.
For a Gear Link or Follow, Test sweeps the source. For a Piston, Test sweeps the
joint that moves it. BoneCraft does not detect collisions. Watch for parts that clash.

![Test the selected mechanism through its movement range.](../images/crescent-rose/en/11-test-head.png){style="max-width:100%;max-height:155mm;width:auto;height:auto"}

*Historical workshop capture. Test the selected mechanism through its movement range.*

## Forms

In **4. Controls**:

- Every joint and Sequence has one slider. It is the handle's own channel, so
  dragging the handle and using the slider are the same thing.
- **Save Form** records every handle and Sequence slider value under a name.
  Rename it in the list.
- **Go to Form** sets every control to the saved values.
- **Go and Key** does the same and also inserts keys on the current frame.
- The **X** next to the list removes a form.

**Older saved files:** BoneCraft 9.2.18 reads and applies forms captured by earlier versions. Opening or applying a form does not resave it. **Save Form** captures the current control values using the current format. Saving with an existing form name replaces that form's captured values.

The controls stay in **Mechanisms → 4. Controls**. The compatibility repair does not change the rig's handles, Sequence sliders or panel locations.

![Forms controls show sliders, Save Form, Go to Form and Go and Key.](../images/crescent-rose/en/27-save-form.png){style="max-width:100%;max-height:155mm;width:auto;height:auto"}

*Historical workshop capture. Forms controls show sliders, Save Form, Go to Form and Go and Key.*

## What BoneCraft builds

For each part:

| Bone | Job | Visible |
|---|---|---|
| `CTRL-<part>` | The handle. Its value is the panel slider. Only Hinge, Slide and Telescope make one. | Yes |
| `MCH-<part>` | Adds the handle and every link, then applies the limits. | Hidden |
| `DEF-<part>` | Copies `MCH-<part>`. The mesh is bound to it. Engines receive this bone. | Hidden |

The bones sit in the collections `Mechanism Controls`, `Mechanism MCH` and
`Mechanism DEF`. A part with no joint has only `MCH-` and `DEF-` bones. A
Telescope's handle is `CTRL-<telescope name>`. A Sequence's is
`CTRL-SEQ-<name>`. A Piston adds `MCH-<part>-aim` and `MCH-<part>-target` bones
for each of its two parts.

The constraints on `MCH-<part>` always come in the same order: Copy Transforms
from the handle, then each link's contribution, then the joint's Limit Rotation
or Limit Location. `DEF-<part>` has one Copy Transforms from `MCH-<part>`.

Everything BoneCraft builds is tagged with its record: constraint names start
with `BC·<id>·<role>`, and bones carry the properties `bc_mech_id` and
`bc_mech_role`. BoneCraft finds its bones by tag, not by name, so you can
rename any bone. A rebuild finds it again and makes no duplicate.

With Show Helpers on, each joint and link has a **How this works** note. It
lists the constraints by name, says what each does, and has a **Select**
button (an arrow icon) to inspect the bone.

Your own constraints, drivers and bones are never touched. A constraint you add
to an MCH bone stays below BoneCraft's after a rebuild.

## Editing and hand edits

- **Value edits** (limits, ratio, ranges, timing, ease, handle look) update the
  existing constraints in place. There is no rebuild.
- **Structural edits** (a Gear Link's **Kind**, a Follow's **Curve**, a
  Piston's **Stretch**) replace that mechanism's constraints and rebuild only
  that mechanism.
- **Changed by hand.** After you edit a BoneCraft constraint, such as a Limit,
  the mechanism's message ends with "(changed by hand)". BoneCraft never overwrites
  the edit silently. Select one option:
  - **Keep mine** copies your values into the record. It refuses what it cannot
  read back. Its message tells you to use Restore or Detach.
  - **Restore** throws your edit away and rebuilds from the record.
- A held mechanism also holds every mechanism that uses its bones, until you
  settle it.
- The same protection applies to a reshaped curve. With **Curve** enabled, you can
  reshape a Follow's curve in the Graph Editor. A later change such as Target Range
  would replace the curve. That change makes the Follow's message end with "(changed by hand)".
  **Keep mine** keeps your curve. **Restore** regenerates it.
- A held Sequence shows its message and **Restore** in **3. Sequences**, with
  **Detach** and **Delete** next to it. Keep mine is not offered for Sequences.
- **Detach** (broken-chain button) deletes the record and the tags but keeps the bones and
  constraints as your own hand-made rig. Detach and Delete both refuse a record
  that another record uses, and name the users.
- **Delete** (X button) removes the record and everything BoneCraft built for it.
- A link loop is refused before anything is built, and the loop is named, for
  example "Blade Hinge → Cover Follow → Blade Hinge would loop."

The Rig Validator and Task Board report:

- Link loops.
- Missing parts.
- DEF bones moved from outside their mechanism.
- Drivers that need Python.
- Gear Links that lose a Sequence or Follow.

The validator's naming check accepts hyphens (`CTRL-`, `MCH-`, `DEF-`).
Its drivers check warns only on expressions that need Python.
A clean Mechanisms rig shows no validation errors. It shows only the `root` bone
warning described in Limits of this version.

## Show Helpers

**Show Helpers** is one preference for all of BoneCraft: **Preferences →
Add-ons → BoneCraft → Helpers**. Off hides the teaching text everywhere: the what / when
lines, the **How this works** notes and the full guided-step sentences (those
become short labels). The steps themselves, the lists, Test, warnings and
Blender's hover tooltips always stay.

The VRChat **Compact Mode** button is its shortcut: Compact Mode on means Show
Helpers off.

## Limits of this version

- Click Turn, Track and Linkage mechanisms come later.
- Engine export of baked mechanism motion comes later, after the desktop hand
  check. Until then the `DEF-` bones are the bones to export.
- BoneCraft does not detect collisions. To check for collisions:
  1. Use Test.
  2. Watch the parts.
- A free-spinning Gear Link follows handles and gears only.
- The rig's `root` bone is in no bone collection, so the Rig Validator's
  collections check warns about it and the Task Board shows "Rig validation
  warnings (1)".

Next: [VRChat Tools](08-vrchat.md)

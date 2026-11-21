# Rig Tools

[← Contents](index.md)

This chapter explains BoneCraft's rigging, animation and weight tools. Use it for feature details or situations that the guides do not cover.

Each entry explains the tool's purpose, uses, main controls and location. Its "Where to find it" line names the required mode. Rig controls need Pose Mode. Weight Mirror and Weight Transfer need Weight Paint mode. Delta Mush needs Object Mode. When a tool cannot run, some sections remain visible with a selection message.

Since 9.1, many tools run immediately and show their options in the Adjust Last Operation panel. Before running another operation, change those options immediately after the click. Common operations have shortcuts in the Pose → BoneCraft and Weights → BoneCraft menus. Bforartists' Pose and Weights Tool Shelf tabs also have BoneCraft button panels. [Getting Started](01-start.md#where-things-are) lists these access points.

The pictures show example rigs and tool settings. Follow each tool's path to open its controls.

For engine export, use [VRChat Tools: Game Engine Export](08-vrchat.md#game-engine-export). **Bone Names** presets change export copies. They serve a different purpose from tools that rename the working rig.

---

## Rig UI Tools

These tools control bone visibility, bone organization and quick access when you work with armatures.

---

### Bone Collections

**What it does:** Shows your skeleton's bone collections as rows. Click a collection's name to select its bones. The eye icon shows or hides the collection.

> A bone collection is a named group of bones — for example "IK Controls", "Face Bones" and "Deform Bones". Hiding a collection hides those bones in the viewport, so you can focus on one part of the rig.

**Key controls:**

- Each row: accent color, **Toggle Collection Visibility** (eye icon), the collection's name, **Solo Collection** and **Rename Collection Display**. The collection's name selects its bones. **Rename Collection Display** sets a custom display name for the row. To identify an icon-only button, hover over it for its tooltip
- **Show All Collections** and **Hide All Collections** (open and closed eye icons above the list) — everything at once
- Sections — group several collections under a collapsible header

**Where to find it:** BoneCraft tab → Review → Collections

![Bone collections and their visibility, selection, solo and display-name controls.](images/screenshots/bc03-collections.png){style="max-width:100%;max-height:155mm;width:auto;height:auto"}

*Native test-build popover, BoneCraft 9.2.19 candidate. Bforartists 5.2.3, Blender 5.4 Alpha. Bone collections and their visibility, selection, solo and display-name controls.*

---

### Visibility Bookmarks

**What it does:** Saves which bone collections are visible, so you can switch between saved views at once.

**Example use:** "Face Only" can store a view of only the face bones for expression work. "Full Rig" can store a view of all bones for weight painting. One click switches between the saved views.

**Key controls:** each slot is a row.

- The bookmark's name — click it to apply the saved view
- **Save Bookmark** — saves the current visibility in the slot. To see the tooltip, hover over its icon
- The color swatch — color-codes the bookmark
- **Clear Bookmark** and **Remove Bookmark** (close icons) — empty the slot, or remove an added one
- **Add Bookmark** — adds a slot

**Default bookmarks:** FK Arms, IK Body, Face Only, Full Rig

**Where to find it:** BoneCraft tab → Review → Collections → Visibility Bookmarks

![Visibility Bookmarks with one saved Full Rig view and three available slots.](images/screenshots/bc03-bookmarks.png){style="max-width:100%;max-height:155mm;width:auto;height:auto"}

*Native test-build popover, BoneCraft 9.2.19 candidate. Bforartists 5.2.3, Blender 5.4 Alpha. Visibility Bookmarks with one saved Full Rig view and three available slots.*

---

### Hotkey Quick Panel

**What it does:** Opens BoneCraft's rig panel (collections and bookmarks) as a pop-up wherever your cursor is.

**How to use:**

1. In the 3D viewport, press **Ctrl+Shift+R**.
2. To close the pop-up, click outside it.

**Where to find it:** the **Ctrl+Shift+R** shortcut in the 3D viewport (it has no panel of its own)

The quick panel uses the [bookmark controls pictured above](#visibility-bookmarks).

---

## Animation Tools

---

### Pose Library

**What it does:** Stores named poses with thumbnails that you can apply to your rig with one click.

**Key controls:**

- **Save** — stores the current bone positions as a named pose, with a thumbnail of the viewport
- **Apply** — snaps the bones to the saved pose
- **Blend** — applies the pose at partial strength, mixed with the current position
- **Mirror** — applies the pose flipped left to right
- **Delete**, **Rename** and **Category** — manage the list. **Filter** shows one category
- **Export** and **Import** — save to or load from a `.bfpose` file

Blend applies immediately. After clicking Blend, set the blend strength in Adjust Last Operation.

**Where to find it:** BoneCraft tab → Review → Pose Library

![A saved example pose exposes Apply, Mirror, Blend and library controls.](images/screenshots/bc05-pose-library.png){style="max-width:100%;max-height:155mm;width:auto;height:auto"}

*Native panel popover, BoneCraft 9.2.18. A saved example pose exposes Apply, Mirror, Blend and library controls.*

---

### Control Picker

**What it does:** A clickable map of your rig's controls. Click a shape to select its bone. The picker highlights the selected controls.

**Key controls:**

- **Generate Picker** — builds the layout from your rig
- **Edit Layout** — layout editing. Each control's row has icons for **Move Picker Control**, **Resize Picker Control** and **Relabel Picker Control**. **Snap** aligns controls to a grid. **Rebuild Layout** builds the layout again
- **Mirror Selection** — selects the mirrored controls
- **Pop-up Picker** — opens the picker in a floating window, which also has **Add Selection Set**

**Where to find it:** BoneCraft tab → Review → Control Picker

![The generated Control Picker shows example controls, layout editing, mirrored selection and the pop-up picker action.](images/screenshots/bc05-picker.png){style="max-width:100%;max-height:155mm;width:auto;height:auto"}

*Native panel popover, BoneCraft 9.2.18. The generated Control Picker shows example controls, layout editing, mirrored selection and the pop-up picker action.*

---

### Control Layer (IK/FK)

For an illustrated hands-on comparison, follow [Test weights and use IK/FK](06-rig-builder.md#part-c-test-weights-and-use-ikfk).

**What it does:** Controls the limbs of a rig made by **Build Control Rig**. It switches a limb between IK and FK without a jump. It also converts IK animation to FK, or FK animation to IK, over a frame range.

**Key controls:**

- **IK** and **FK** — switch the limb and snap the new controls to its current position. The elbow or knee does not jump
- **Bake IK** and **Bake FK** — convert the animation over a frame range to IK or to FK
- **Pole Follow**, **Pin** and **Lock-Free**, and **Global Rig Scale**, which keeps protected locks

**Where to find it:** BoneCraft tab → Review → Control Layer (with a rig made by **Build Control Rig** selected; see [Rig Builder](06-rig-builder.md))

![Control Layer shows limb IK/FK switches, bake actions and rig settings.](../images/rig-builder/en/c02-control-layer.png){style="max-width:100%;max-height:155mm;width:auto;height:auto"}

*Historical workshop capture. Control Layer shows limb IK/FK switches, bake actions and rig settings.*

---

### Rigify Tools

**What it does:** Detects a Rigify control rig and connects BoneCraft's collection panel, bookmarks and property sliders to Rigify's standard controls.

> Rigify is Bforartists' built-in system for generating animation-ready rigs. If you built your rig with Rigify, this connects BoneCraft's UI to Rigify's IK/FK controls.

**Key controls:**

- **Auto-Enhance** — sets up BoneCraft's panels for the selected Rigify rig
- **Re-run Enhancement** — rebuilds them from scratch
- **Enable Rigify** is in Quick Rig. Its Troubleshooting fold contains **Generate Control Rig (active metarig)** (see [Rig Builder](06-rig-builder.md))
- Rigify Properties — the rig's IK/FK, stretch, parent-space and head/neck follow sliders

**Where to find it:** BoneCraft tab → Setup Rigging → Rigify Tools (and the Rigify Properties section)

![Rigify Tools shows its enhancement entry point. Select a generated Rigify rig to use the applicable controls.](images/screenshots/bc06-rigify.png){style="max-width:100%;max-height:155mm;width:auto;height:auto"}

*Native panel popover, BoneCraft 9.2.18. Rigify Tools shows its enhancement entry point. Select a generated Rigify rig to use the applicable controls.*

---

### Retarget

**What it does:** Transfers animation between skeletons, such as a motion-capture clip onto your avatar. It matches bones by name and direction to preserve limb orientation. Loose collarbone matching prevents excessive shoulder rotation.

**Key controls:**

- **Import Clip** and **Browse Library** — load a clip or set a library folder. Click a clip's name to select it
- **Auto-Match Bones** (check mark on a clip's row) — pairs source and target bones. The Bone Mapping list shows the pairs
- **Preview** and **Stop Preview** — try the result
- **Apply** — bakes the clip onto your rig

**Where to find it:** BoneCraft tab → Setup Rigging → Retarget

![Retarget starts with Import Clip and Browse Library. Clip mapping and preview appear after loading a clip.](images/screenshots/bc06-retarget.png){style="max-width:100%;max-height:155mm;width:auto;height:auto"}

*Native panel popover, BoneCraft 9.2.18. Retarget starts with Import Clip and Browse Library. Clip mapping and preview appear after loading a clip.*

---

### Corrective Shape Keys

**What it does:** Shape keys that switch on when a bone reaches an angle, to fix pinching or collapsing at extreme poses.

**Example use:** Your character's elbow collapses when fully bent. A sculpted elbow correction linked to the arm bone applies automatically as the elbow bends.

**Key controls:**

- New Corrective — settings for the **Shape Key**, **Driver Bone**, rotation axis, full-strength angle and gradual fade-in
- The list of correctives — **Edit** and **Delete** under the list act on the selected corrective

The armature's child mesh must have a basis shape key. Select the armature to show New Corrective. Its child mesh supplies the shape keys.

To create a corrective:

1. Select the **Shape Key**.
2. Select the **Driver Bone**.
3. Select the rotation axis.
4. Set the angle at which the shape reaches full strength.
5. Set how gradually the shape fades in.
6. Select **Create Corrective**.

To select an existing corrective, click its shape key name in the list.

Edit starts from the corrective's current values. After clicking Edit:

1. In Adjust Last Operation, change the angle.
2. Change the falloff.

**Where to find it:** BoneCraft tab → Skin → Correctives (the mesh needs a basis shape key)

![Select the armature to show New Corrective. Its child mesh supplies the shape keys.](images/screenshots/bc08-correctives.png){style="max-width:100%;max-height:155mm;width:auto;height:auto"}

*Native panel popover, BoneCraft 9.2.18. Select the armature to show New Corrective. Its child mesh supplies the shape keys.*

---

### Graph Tools

**What it does:** Animation refinement tools for keyframes and curves.

- **Interactive Breakdown** (Breakdowner) — blends the current pose between the nearest keyframes as you drag left and right. Its 3D viewport shortcut is **Ctrl+Shift+B**
- **Apply Delta** (Delta Mover) — offsets selected bones by an exact amount in screen space or world space. Its 3D viewport shortcut is **Ctrl+Shift+D**
- **Capture** and **Swap** (Buffer Curves) — keep a copy of the curves and swap between it and your edits
- **Smart Bake** — bakes constraint-driven animation to keys, dropping redundant keys (**Tol** sets how much)
- **Euler Filter** — fixes rotation flips caused by gimbal lock
- Tangent Handles — set handle types on selected keys: **Auto**, **Vector**, **Aligned**, **Free** or **Auto Clamped**

**Where to find it:** BoneCraft tab → Review → Graph Tools

![Interactive Breakdown starts a drag on the selected pose bones.](images/screenshots/bc09-breakdown.png){style="max-width:100%;max-height:155mm;width:auto;height:auto"}

*Native panel popover, BoneCraft 9.2.18. Interactive Breakdown starts a drag on the selected pose bones.*

![Apply Delta and its offset options.](images/screenshots/bc09-delta.png){style="max-width:100%;max-height:155mm;width:auto;height:auto"}

*Native panel popover, BoneCraft 9.2.18. Apply Delta and its offset options.*

![Buffer Curves, Euler Filter and Smart Bake. The Options fold is closed.](images/screenshots/bc09-buffer-bake.png){style="max-width:100%;max-height:155mm;width:auto;height:auto"}

*Native panel popover, BoneCraft 9.2.18. Buffer Curves, Euler Filter and Smart Bake. The Options fold is closed.*

![Tangent Handles offers Auto, Vector, Aligned, Free and Auto Clamped.](images/screenshots/bc09-tangents.png){style="max-width:100%;max-height:155mm;width:auto;height:auto"}

*Native panel popover, BoneCraft 9.2.18. Tangent Handles offers Auto, Vector, Aligned, Free and Auto Clamped.*

---

## Weight Tools

These tools control how your mesh deforms when bones move. Weights tell each part of your mesh which bones to follow, and how much.

---

### Automatic Bone Weight Recalculation

**What it does:** Recalculates the weights of a mesh from the existing rig, without changing the mesh. On dense meshes it works through a lighter proxy mesh, so it does not fail silently.

**Key controls:** Body calculates weights from the existing rig. Clothing transfers weights from a correctly weighted source mesh. The settings are above the button.

1. In **Mesh to Reweight**, select the target mesh.
2. In **Existing Armature**, select the armature.
3. Select Body or Clothing mode.

For Body mode, select the method.

For Clothing mode:

1. In **Weighted Body**, select the correctly weighted source mesh.
2. Select the method.

For either mode:

1. Set the blend.
2. Set the smoothing.
3. Set the maximum number of bone influences per vertex.
4. Set the minimum weight.
5. Select whether to keep a backup.
6. Select **Automatic Bone Weight Recalculation**.

The CATS shortcut, **Smart Automatic Weights**, opens a dialog for the target mesh, armature and mode. In Clothing mode, the dialog also includes the source mesh.

**Where to find it:** BoneCraft tab → Skin → Weight Tools

![Automatic Bone Weight Recalculation settings with the example mesh and armature selected.](images/screenshots/bc10-weight-tools.png){style="max-width:100%;max-height:155mm;width:auto;height:auto"}

*Native test-build popover, BoneCraft 9.2.19 candidate. Bforartists 5.2.3, Blender 5.4 Alpha. Automatic Bone Weight Recalculation settings with the example mesh and armature selected.*

---

### Weight Mirror

**What it does:** Copies weights from one side of your avatar to the other. Use it for symmetrical characters.

**Key controls:**

- **Mirror All Weights** — mirrors every bone group to its opposite side
- **Mirror Active Weight** — mirrors only the active bone group
- **Axis** and **Direction** — choose the reflection axis and which side supplies weights
- **Search Distance** — the allowed distance from a reflected vertex position to its spatial match
- **Select Unmatched** — selects vertices without a partner. **Normalize Weights** makes the weights sum to 1.0 afterwards

The mirror uses spatial positions, not mesh topology.

1. Click a mirror button.
2. In Adjust Last Operation, select **Axis**.
3. Select **Direction**.
4. Set **Search Distance**.

**Mirror Active Weight** is also in Weights → BoneCraft and the Weights Tool Shelf tab.

**Where to find it:** BoneCraft tab, in Weight Paint mode → Weight Mirror

![Weight Mirror actions. After the click, set the axis in Adjust Last Operation. Set the search options there.](images/screenshots/bc11-mirror.png){style="max-width:100%;max-height:155mm;width:auto;height:auto"}

*Native panel popover, BoneCraft 9.2.18. Weight Mirror actions. After the click, set the axis in Adjust Last Operation. Set the search options there.*

---

### Weight Transfer

**What it does:** Copies weights from a source mesh to the active mesh. Used when attaching clothing to a body, or moving weights from a high-resolution mesh to a lower one.

**Key controls:** **Normalize** in Adjust Last Operation keeps the weights summing to 1.0. **Select Problem Vertices** selects vertices with poor matches.

Keep the target mesh active in Weight Paint mode.

1. In **Source Mesh**, select the source mesh.
2. Click **Transfer Weights**.
3. In Adjust Last Operation, select the transfer method.
4. Select the bone filter.

The result shows mean and maximum distance.

**Where to find it:** BoneCraft tab, in Weight Paint mode → Weight Transfer (also under Skin → Weight Tools)

![Choose a Source Mesh before Transfer Weights. The distance fields remain at their initial values in this example.](images/screenshots/bc11-transfer.png){style="max-width:100%;max-height:155mm;width:auto;height:auto"}

*Native panel popover, BoneCraft 9.2.18. Choose a Source Mesh before Transfer Weights. The distance fields remain at their initial values in this example.*

---

### Weight Table

**What it does:** Shows the selected vertex's exact weight for each bone. You can set precise weight values.

**How to use:**

1. Enter Weight Paint mode.
2. Enable **vertex-selection masking**.
3. Select one vertex.

The table lists the selected vertex's bones and weights.

4. Click the hand icon on a bone's row.
5. In Adjust Last Operation, set **Weight**.

Add Influence uses the bone you select. After Add Influence, set its new weight in Adjust Last Operation too. With several vertices selected, **Normalize All Vertices** normalizes all selected vertices.

**Where to find it:** BoneCraft tab, in Weight Paint mode → Weight Table

![Weight Table with several vertices selected. Select one vertex for detailed weight editing.](images/screenshots/bc11-table.png){style="max-width:100%;max-height:155mm;width:auto;height:auto"}

*Native panel popover, BoneCraft 9.2.18. Weight Table with several vertices selected. Select one vertex for detailed weight editing.*

---

### Flood Fill

**What it does:** Changes the active vertex group's weights across the whole mesh, including unselected vertices.

Before using any Flood Fill action:

1. Select the mesh.
2. Enter Weight Paint mode.
3. Make the required vertex group active.

**Actions:**

- **Flood to 0.0** removes positive assigned weights from the active group across the mesh. Other vertex groups remain unchanged.
- **Flood to 1.0** assigns 1.0 to the active group on every vertex. For each vertex, it removes other positive weights if their total exceeds 1e-6.
- **Flood to Custom** assigns a positive **Value** to the active group on every vertex. With **Normalize** enabled, it also normalizes weights across the whole mesh. A **Value** of 0 performs no assignments or normalization. To clear weights, use **Flood to 0.0**.

The Weights menu and shelf call the fixed-value buttons Flood to Zero and Flood to One.

For a custom fill:

1. Select **Flood to Custom**.
2. Immediately afterwards, set **Value** in Adjust Last Operation.
3. Enable or disable **Normalize**.

**Where to find it:** In Weight Paint mode: BoneCraft tab → Skin → Weight Tools; also Weights → BoneCraft and Tool Shelf → Weights → BoneCraft

![Flood Fill actions. After the click, set the custom value in Adjust Last Operation.](images/screenshots/bc11-flood.png){style="max-width:100%;max-height:155mm;width:auto;height:auto"}

*Native panel popover, BoneCraft 9.2.18. Flood Fill actions. After the click, set the custom value in Adjust Last Operation.*

---

### Deform vs Control

**What it does:** Separates deform bones from control bones. Deform bones move the mesh. The animator moves control bones. The tool tags deform bones and renames them to a deform naming. It also exports a deform-only skeleton.

**Where to find it:** BoneCraft tab, in Pose Mode → Deform vs Control

![Deform and Control lists on the example rig. This rig has 19 deform bones and no control bones.](images/screenshots/bc13-deform-control.png){style="max-width:100%;max-height:155mm;width:auto;height:auto"}

*Native test-build popover, BoneCraft 9.2.19 candidate. Bforartists 5.2.3, Blender 5.4 Alpha. Deform and Control lists on the example rig. This rig has 19 deform bones and no control bones.*

---

### Delta Mush

**What it does:** A smoothing deformation that reduces pinching at joints. The mesh keeps its shape at rest but deforms more cleanly in motion.

**How to use:** These actions require Object Mode and an active mesh.

1. Click **Add Delta Mush**.

The tool adds the modifier and binds it to the rest shape. Immediately after this operation, adjust its options:

2. In Adjust Last Operation, set **Iterations**.
3. Set **Smooth Strength**.
4. Enable or disable **Pin Borders**.
5. Enable or disable **Only Smooth Deform**.

Once the modifier exists, the panel shows **Rebind** and **Remove**. Its Settings fold contains the modifier's iterations, smoothing strength and border pinning controls.

**Where to find it:** BoneCraft → Skin → Delta Mush (Object Mode; Mesh)

![Add Delta Mush starts the setup. Adjust its options immediately after the click.](images/screenshots/bc14-delta-mush.png){style="max-width:100%;max-height:155mm;width:auto;height:auto"}

*Native panel popover, BoneCraft 9.2.18. Add Delta Mush starts the setup. Adjust its options immediately after the click.*

---

### Proximity Wrap

**What it does:** Makes one mesh follow the surface of another, like a second skin. Useful for clothing that hugs the body.

**How to use:** These actions require Object Mode and an active target mesh. Keep the driver's armature in its rest pose when binding.

1. Select the target mesh.
2. Select a different **Driver Mesh**.
3. Click **Bind Proximity Wrap**.

The Options fold below the button lists **Falloff Type** and **Max Distance**. In 9.1.2, the setup stores these values, but they do not change its Surface Deform binding. After binding, the panel shows **Rebind** and **Unbind**. Unbind disables the modifier in the viewport and render. It does not remove the modifier.

**Where to find it:** BoneCraft → Skin → Proximity Wrap (Object Mode; Mesh)

![Choose a Driver Mesh before Bind Proximity Wrap. The Options fold is closed.](images/screenshots/bc14-proximity-wrap.png){style="max-width:100%;max-height:155mm;width:auto;height:auto"}

*Native panel popover, BoneCraft 9.2.18. Choose a Driver Mesh before Bind Proximity Wrap. The Options fold is closed.*

---

## Rig Controls

These tools appear in the BoneCraft tab in Pose Mode.

---

### Space Switch

**What it does:** Changes which space a bone follows during animation. A hand holding a prop can switch from following the body to staying still in the world with one click.

**Key controls:**

- **Add Space** and **Remove Space** (X icon under Manage Spaces) — the spaces a bone can follow (World, Origin or another bone)
- One button per space, named after that space. The current space has a ● mark. To switch the bone, click another space's button

**Where to find it:** BoneCraft tab, in Pose Mode → Space Switch

![Space Switch before any space is defined. Add Space starts the setup.](images/screenshots/bc15-space-switch.png){style="max-width:100%;max-height:155mm;width:auto;height:auto"}

*Native panel popover, BoneCraft 9.2.18. Space Switch before any space is defined. Add Space starts the setup.*

---

### Spline IK

**What it does:** Makes a chain of bones follow a curve. Used for tails, tentacles, ropes, long hair and spines that need smooth, sweeping motion.

**How to use:**

1. Make the starting bone active.
2. Click **Generate Spline IK**.
3. In Adjust Last Operation, set **Chain Length**.
4. Set **Curve Resolution**.
5. Set **Stretch**.
6. Set **Volume Preservation**.

**Remove Spline IK** removes the setup.

**Where to find it:** BoneCraft tab, in Pose Mode → Spline IK

![Spline IK actions. Set chain options in Adjust Last Operation after generation.](images/screenshots/bc15-spline-ik.png){style="max-width:100%;max-height:155mm;width:auto;height:auto"}

*Native panel popover, BoneCraft 9.2.18. Spline IK actions. Set chain options in Adjust Last Operation after generation.*

---

### Chain Dynamics

**What it does:** Adds physics-like secondary motion to a bone chain. Bones lag behind a moving parent and bounce back when it stops. Uses include hair strands, tails and accessories.

**How to use:**

1. Select the bone chain.
2. Click **Add Chain Dynamics**.
3. In Adjust Last Operation, set **Stiffness**.
4. Set **Damping**.
5. Set **Mass**.
6. Set **Gravity Scale**.

The Settings fold below the action also lists these parameters. Once dynamics exist, the panel shows **Bake** and **Remove**. Collision uses a simplified sphere shape, so concave surfaces may not collide correctly.

**Where to find it:** BoneCraft tab, in Pose Mode → Chain Dynamics

![Add Chain Dynamics starts the setup. Expand Settings when you need its parameters.](images/screenshots/bc15-dynamics.png){style="max-width:100%;max-height:155mm;width:auto;height:auto"}

*Native panel popover, BoneCraft 9.2.18. Add Chain Dynamics starts the setup. Expand Settings when you need its parameters.*

---

### Ribbon

**What it does:** Builds a ribbon of Bendy Bones — bones that curve and twist smoothly — for lips, eyebrows, belts and other soft curved areas.

**How to use:**

1. Select the bone chain.
2. Click **Generate Ribbon**.
3. In Adjust Last Operation, set **Control Bones**.
4. Set **Ribbon Width**.

**Remove Ribbon** removes the setup.

**Where to find it:** BoneCraft tab, in Pose Mode → Ribbon

![Ribbon actions and chain length. Adjust the generated ribbon immediately after the click.](images/screenshots/bc15-ribbon.png){style="max-width:100%;max-height:155mm;width:auto;height:auto"}

*Native panel popover, BoneCraft 9.2.18. Ribbon actions and chain length. Adjust the generated ribbon immediately after the click.*

---

### Viseme Library

**What it does:** Creates and manages viseme sets (mouth shapes) linked to shape keys. It also generates lip-sync keys from text. For VRChat viseme mapping, use VRChat Viseme Mapping. To generate new visemes, use the CATS Visemes section.

**Key controls:**

- **New Set** and **Delete** — create or remove a viseme set
- In each set, one button per viseme (with a speaker icon) previews it
- Lip Sync — text to viseme keys, with frames per phoneme and smoothing

**Where to find it:** CATS → Avatar Tools → Viseme Library (Armature); Lip Sync (Pose Mode)

![Viseme Library starts with New Set. Switch to Pose Mode to use Lip Sync.](images/screenshots/bc20-viseme-library.png){style="max-width:100%;max-height:155mm;width:auto;height:auto"}

*Native panel popover, BoneCraft 9.2.18. Viseme Library starts with New Set. Switch to Pose Mode to use Lip Sync.*

![Lip Sync text and Generate Lip Sync. Expand Options for timing and smoothing settings.](images/screenshots/bc20-lip-sync.png){style="max-width:100%;max-height:155mm;width:auto;height:auto"}

*Native panel popover, BoneCraft 9.2.18. Lip Sync text and Generate Lip Sync. Expand Options for timing and smoothing settings.*

---

### Set Driven Key

**What it does:** Links one bone-transform value to another without Python expressions. For example, moving a control bone along X can raise a target bone along Z. This panel authors bone-transform targets.

1. Select **Driver Bone**.
2. Select **Driver Attribute**.
3. Select **Target Bone**.
4. Select **Target Attribute**.
5. Pose the bones.
6. Record each point.
7. Select **Create SDK**.

**Key controls:**

- **Driver Bone** and **Driver Attribute** — what drives
- **Target Bone** and **Target Attribute** — what is driven
- **Set Value** and **Record Point** — record a point on the curve
- **Create SDK** — builds the driver

**Where to find it:** BoneCraft tab, in Pose Mode → Set Driven Key

![Choose the driver and target bones before recording a driven-key point. These fields are unassigned in the example.](images/screenshots/bc16-driven-key.png){style="max-width:100%;max-height:155mm;width:auto;height:auto"}

*Native panel popover, BoneCraft 9.2.18. Choose the driver and target bones before recording a driven-key point. These fields are unassigned in the example.*

---

### Rig Validator

**What it does:** Checks your rig against rules and reports problems. Checks cover naming, missing bones, broken constraints, hierarchy, weights, drivers that need Python, and the Mechanisms rules. Bone names with hyphens (such as `DEF-upper_arm.L`) pass.

**Key controls:**

- **Run Validation** — runs every check and lists the results
- **Export Report** — saves the results to a file

The Task Board (BoneCraft tab → Overview → Task Board) shows a validator task when a check fails.

**Where to find it:** BoneCraft tab → Review → Rig Validator

![Validation reports one collection warning. With no parented mesh on the example rig, validation skips the weight check.](images/screenshots/bc17-validator.png){style="max-width:100%;max-height:155mm;width:auto;height:auto"}

*Native test-build popover, BoneCraft 9.2.19 candidate. Bforartists 5.2.3, Blender 5.4 Alpha. Validation reports one collection warning. With no parented mesh on the example rig, validation skips the weight check.*

---

### Rig Notes

**What it does:** Written notes attached to the rig's bones — what you set up, reminders, notes for collaborators.

**Key controls:** **Add Note**, and **Remove** on each note. Rig Readme shows the rig's notes as a read-only page.

**Where to find it:** BoneCraft tab → Overview → Rig Notes, and Review → Rig Readme

![A note attached to Hips in Pose Mode. Add Note creates an annotation. Remove deletes that annotation.](images/screenshots/bc17-notes.png){style="max-width:100%;max-height:155mm;width:auto;height:auto"}

*Native test-build popover, BoneCraft 9.2.19 candidate. Bforartists 5.2.3, Blender 5.4 Alpha. A note attached to Hips in Pose Mode. Add Note creates an annotation. Remove deletes that annotation.*

Next: [Rig Builder](06-rig-builder.md)

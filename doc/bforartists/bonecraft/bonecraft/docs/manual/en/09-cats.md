# CATS Tools

[← Contents](index.md)

The CATS tools are in the right sidebar's **CATS → CATS** section. Press **N** to show the sidebar.

The tools also appear in **Properties → Scene** when Preferences → Tabs → Scene Properties → Show is enabled. The CATS viewport switch and the Scene Properties switch control their copies independently.

The tools follow [The CATS Pipeline](04-cats-pipeline.md). At the top of the section, select the armature to process.

In 9.1, several panels contain optional settings in a fold below their action buttons. Required inputs remain above the action buttons. These include Fix Model's cleanup switches, Translate Bone Names' source language, mouth shapes and eye bones.

Bone tools with Adjust Last Operation run immediately. After the operation, adjust their options there. Hover over a button or option to read its tooltip.

---

## Fix Model

**Pipeline phase:** 1 (recommended cleanup review)

**What it does:** Runs enabled cleanup operations on the selected mesh. A clean avatar may not need these changes.

**Options (each can be switched off):**

- Apply modifiers
- Remove doubles — merge duplicate vertices at the same position
- Recalculate normals — fix inside-out surfaces
- Remove loose geometry — faces not attached to the body
- Remove empty vertex groups
- Remove zero-weight bones — bones that move no vertex
- Remove constraints and rigid bodies VRChat cannot use

1. Review the cleanup options.

2. Enable only the operations your avatar needs.

3. Save a file checkpoint.

4. Select **Fix Model** to run the enabled operations on the selected mesh in one pass.

5. Inspect the result before continuing.

![Fix Model options and action. Review these choices before the first pipeline phase.](images/screenshots/bc24-fix-model.png){style="max-width:100%;max-height:155mm;width:auto;height:auto"}

*Native panel popover, BoneCraft 9.2.18. Fix Model options and action. Review these choices before the first pipeline phase.*

---

## Translate Bone Names

**What it does:** Translates your skeleton's bone names to English VRChat names. It works offline, from a built-in dictionary of known bone names.

**Supported languages:** Japanese (日本語, the most common, from MMD and many community models), Chinese (中文), Korean (한국어), Portuguese (Português), Spanish (Español) and French (Français).

**Key controls:**

1. Select the source names' **Language**.

2. Select **Translate Bone Names**.

Language identifies the model's bone-name language. It does not identify the interface language. For a Japanese MMD model, select Japanese regardless of Bforartists' interface language.

![Choose the source naming language before Translate Bone Names. No matching names have been detected in this example.](images/screenshots/bc24-translate.png){style="max-width:100%;max-height:155mm;width:auto;height:auto"}

*Native panel popover, BoneCraft 9.2.18. Choose the source naming language before Translate Bone Names. No matching names have been detected in this example.*

---

## Join Meshes

**What it does:** Combines your avatar's mesh objects into one mesh. VRChat performs best with one mesh per avatar. If source meshes have different shape keys, CATS fills missing keys with neutral shapes. The joined mesh has one consistent set.

**Key controls:** the mesh list, its refresh button and **Join Meshes**.

**When to use:** after attaching and weighting clothing and accessories.

1. Inspect the source meshes.

2. Select any cleanup the source meshes need before joining.

3. Save a file checkpoint.

4. If the mesh list needs updating, refresh it with the button beside it.

5. Select **Join Meshes**.

6. Inspect the joined mesh, shape keys and weights.

![After Refresh Mesh List, the list contains one checked mesh with six polygons. Review it before choosing Join Meshes.](images/screenshots/bc24-join-meshes.png){style="max-width:100%;max-height:155mm;width:auto;height:auto"}

*Native test-build popover, BoneCraft 9.2.19 candidate. Bforartists 5.2.3, Blender 5.4 Alpha. After Refresh Mesh List, the list contains one checked mesh with six polygons. Review it before choosing Join Meshes.*

---

## Material Atlas Combiner

**Pipeline phase:** 2 (optional)

**What it does:** Bakes several materials into one texture sheet (an atlas). Fewer materials give a better VRChat performance rank.

**Location:** **CATS → CATS → Material Atlas**. The panel divides the work into **1. Choose Target**, **2. Choose Materials and Textures**, and **3. Bake and Review**.

### Analyze and choose sources

![Material Atlas before analysis. Choose the target, keep a backup, then Analyze Materials.](images/screenshots/bc25-material-atlas.png){style="max-width:100%;max-height:155mm;width:auto;height:auto"}

*Native panel popover, BoneCraft 9.2.18. Material Atlas before analysis. Choose the target, keep a backup, then Analyze Materials.*

**Target** offers **Active Avatar**, **Selected Meshes** and **Visible Scene**. Active Avatar uses the active armature's mesh children. If no armature is active, it uses the active mesh. Visible Scene uses visible meshes. For a specific set, select Selected Meshes.

1. Save a copy of the file.

2. Select the required scope in **Target**.

3. Keep **Preserve Backup Duplicate** enabled.

4. Select **Analyze Materials**.

5. Select an atlas group.

6. To bake that group, enable its checkbox.

7. Under **Materials to combine**, enable the materials to include.

8. Under **Texture images**, enable the images to include.

9. Repeat the source review for each enabled group.

**Analyze Materials** creates the source lists. Its label becomes **Refresh Analysis** after groups exist. Refresh rebuilds the lists and their choices. Review them again after refreshing.

Each list has **Select All** and **Deselect All**. These buttons change **Include** checkboxes in that list for the active group. They do not change the highlighted row. The material and texture lists remain independent. Other groups retain their choices. Missing textures stay unchecked. Bulk selection does not enable a disabled group.

The same bulk actions are available under **Object → Atlas Source Selection**. Accept or Revert a pending atlas preview before changing its source selection.

An enabled group needs at least two checked materials. The bake skips disabled groups and single-material groups. Excluded material slots and shared material references remain separate. Excluding an image omits that image from baking. It does not exclude its whole material.

Transparent and emissive materials start in separate groups. Alpha Blend groups start disabled to preserve draw order. If you accept possible draw-order changes, enable these groups.

**Source Details** starts disabled. Enable it to inspect mesh diagnostics, shape-key and UV warnings, material sizing, texture roles and duplicate-source groups. A material's **Override Size** exposes its size choice. Custom sizing uses **Width** and **Height**. Color-only materials use **Fallback** sizing.

The group list offers **Resolution** and add/remove controls. **Add Group** and **Remove Group** manage groups. They do not bake by themselves.

![Analyzed sources from two example meshes. Review the group, material and image checkboxes, including the UV warning.](images/screenshots/bc25-atlas-sources.png){style="max-width:100%;max-height:155mm;width:auto;height:auto"}

*BoneCraft 9.2.19 candidate. Native Bforartists 5.2.3 test build, Blender 5.4 Alpha. Analyzed sources from two example meshes. Review the group, material and image checkboxes, including the UV warning.*

### Bake and review

1. After reviewing the source lists, select **Bake Checked Sources**.

2. Read the preflight summary.

3. Correct any reported source or setting error.

4. When the planned changes are correct, confirm the bake.

5. Inspect the atlas, transparency, shape keys and exported UV channel.

6. If the result is correct, select **Accept — Delete Backup**.

If you need the original result, select **Revert — Restore Originals** instead. Accept deletes the backup. Revert restores original objects, materials and visibility. Revert also resets material-count results.

![One 2048-pixel Opaque group baked from two example meshes. The panel still reports 2 to 2 materials and Excellent rank. Inspect the UV warning before Accept or Revert.](images/screenshots/bc25-atlas-baked.png){style="max-width:100%;max-height:155mm;width:auto;height:auto"}

*BoneCraft 9.2.19 candidate. Official Bforartists 5.2.3, Blender 5.3 Alpha. One 2048-pixel Opaque group baked from two example meshes. The panel still reports 2 to 2 materials and Excellent rank. Inspect the UV warning before Accept or Revert.*

**Preserve Backup Duplicate** starts enabled. It keeps a visible pre-atlas duplicate for review and Revert. Disabling it removes originals after atlasing and leaves no Revert backup. Before disabling this option, save a separate file.

Accept or Revert the current preview before another analysis or bake. If an analyzed object, material slot or render classification changes, preflight can cancel before creating a backup.

Before baking again:

1. Select **Refresh Analysis**.

2. Review the rebuilt choices.

**Smart Combine Materials** is the initial automatic shortcut before analysis exists. With **Auto Analyze** enabled, it rebuilds analysis before baking. Use **Bake Checked Sources** to bake your reviewed choices without automatic reanalysis. Older instructions call this operator **Bake Atlas**.

**If baking cannot start:** Atlas baking requires Cycles. If Bforartists reports that Cycles is unavailable, use a full build that includes Cycles.

### Advanced Options

**Advanced Options** replaces the older Override Inherited Settings wording. It holds optional workflow, bake, UV and output controls.

| Setting | Use |
| --- | --- |
| Auto Analyze | Rebuilds groups for the automatic Smart Combine shortcut. |
| Debug Report / Copy Debug Report | Enables diagnostics and copies the latest report for troubleshooting. |
| Albedo (Color) | Required base-color bake pass. Keep it enabled. |
| Normal Map / Emission / Roughness | Optional separate output passes. Inspect the supported source data and bake results. |
| Metallic / Pack ORM Channels | Preflight blocks these options in this build. Leave them disabled. |
| Packing Preset / Bake Padding / UV Margin | Sets padding and spacing between atlas islands. |
| Pixel Art No-Bleed / Preserve Island Orientation | Controls padding behavior and supported island orientation handling. |
| UV Method / UV Seed / Rotation Step | Chooses packing and variation. Seed and rotation controls appear only for methods that use them. |
| Keep Source UV Maps | Retains source UV layers on the output mesh. It starts disabled. |
| Fallback Size | Sets the atlas allocation size for color-only materials without images. |
| Format Output | Chooses PNG, TGA or EXR. EXR preserves emission above 1.0. PNG and TGA clamp it. |
| Material Output Type / Surface Output | Chooses the generated material's render type and surface shader. |
| Path Output | Sets the output texture folder. |

With **Keep Source UV Maps** disabled, the final atlas mesh uses `atlas_uv` as UV0 for FBX, Unity and VRChat. Enabling it can leave `atlas_uv` on UV1. Check the engine's UV channel when retaining source maps. Color-only meshes without authored UVs also receive the generated atlas UV layer.

### Preservation and limits

The combiner preserves connected Principled tint, texture mapping and alpha during baking. It handles render-hidden source meshes through temporary bake copies. Excluded material references stay shared with other objects. Geometry positions, shape keys and parenting remain protected during assembly.

VRM / MToon materials retain their dedicated fallback path. Transparency classification considers the actual alpha graph and texture alpha. The DITHERED render setting alone does not classify a material as transparent. Problem tiles can appear magenta after baking. Inspect these tiles before accepting.

The documented repairs have generated-fixture host checks. They do not certify every production avatar or shader graph. Visible file-browser behavior, real-window layout and interactive undo/redo retain their recorded test limits. See the historical [repair record](https://github.com/Axleonex/B4Artists_Toolkit/blob/main/bonecraft/docs/material-combiner-fixes-2026-10-23.md) and [9.2.15 UI review](https://github.com/Axleonex/B4Artists_Toolkit/blob/main/bonecraft/docs/material-combiner-ui-review-9.2.15.md).

**Lineage credits:** this workflow continues the CATS integration lineage and credits the original Cats Blender Plugin. The Material Combiner lineage credits Grim-es/material-combiner-addon. UV workflow inspiration comes from UV Toolkit by Alexander Belyakov and the oRazeD/UVToolkit archival repository. BoneCraft implements its own atlas UV helpers. It does not include UVToolkit source.

---

## Visemes

**Pipeline phase:** 3

**What it does:** Creates the 15 VRChat visemes from three base mouth shapes.

**Before generation:** each of **A Shape**, **O Shape** and **CH Shape** needs a source assignment. Each source field must name an existing mouth shape key.

**Manual source selection:**

1. Select the source key in **A Shape**.

2. Select the source key in **O Shape**.

3. Select the source key in **CH Shape**.

**Automatic alternative:** select **Auto-Detect** instead.

**After either source-selection route:**

1. Check that all three source fields name existing keys.

2. If necessary, expand Options below the buttons.

3. If necessary, change whether to overwrite existing visemes.

4. Select **Generate Visemes**.

See [Guide 13, Phase 2](03-guides-b.md#phase-2--viseme-generation).

![CATS Visemes: select the A, O and CH source shapes, or use Auto-Detect, before Generate Visemes.](images/screenshots/bc29-visemes.png){style="max-width:100%;max-height:155mm;width:auto;height:auto"}

*Native panel popover, BoneCraft 9.2.18. CATS Visemes: select the A, O and CH source shapes, or use Auto-Detect, before Generate Visemes.*

---

## Eye Tracking

**Pipeline phase:** 4 (run after Fix Model)

Auto-Detect searches common eye-bone names. It does not use mesh geometry or bone positions.

1. Check **Left Eye** and **Right Eye**.

2. If an assignment is missing, select that bone manually.

If you rename the bones:

1. Rerun detection.

2. Check both assignments again.

If eye motion is wrong, inspect bone orientation, constraints and the exported avatar.

**What it does:** Finds the eye bones and names them `LeftEye` and `RightEye` as VRChat requires. It creates the rotation constraints for eye movement in VRChat.

**Key controls:**

- **Auto-Detect** — searches common left and right eye-bone names
- **Left Eye** and **Right Eye** — the eye bones, if you pick them yourself
- **Up Limit**, **Down Limit** and **Side Limit** — how far the eyes may turn, in degrees
- **Create Eye Tracking** — renames the bones and creates the constraints

![Eye Tracking before bone detection. The example limits are 30 degrees up, 20 down and 30 sideways.](images/screenshots/bc29-eyes.png){style="max-width:100%;max-height:155mm;width:auto;height:auto"}

*Native test-build popover, BoneCraft 9.2.19 candidate. Bforartists 5.2.3, Blender 5.4 Alpha. Eye Tracking before bone detection. The example limits are 30 degrees up, 20 down and 30 sideways.*

---

## Pose & Shape Keys

**Pipeline phase:** 5 (optional)

### Pose to Shape Key

The current button captures the selected mesh's **current shape-key mix**. It does not bake armature-bone deformation.

1. Switch to Object Mode.

2. Select the target mesh.

3. Set its existing shape-key values to the blend you want to capture.

4. Select **Pose to Shape Key**.

5. Enter a name.

6. Confirm the operation.

7. Reset the original shape-key values to 0.

8. Inspect the new key alone.

The tool sets the new key to 1 and leaves the original keys active. Leaving the original values active adds their deformation again.

### Save a Bone-Deformed Pose

Use this native workflow when you need to store deformation from armature bones. The modifier must preserve mesh topology.

**Save as Shape Key** keeps the Armature modifier. **Apply as Shape Key** removes it.

1. Pose the armature.

2. Save a file checkpoint.

3. Return to Object Mode.

4. Select the deformed mesh.

5. Open **Properties → Modifiers**.

6. Open the Armature modifier's dropdown menu.

7. Select **Save as Shape Key**.

8. Reset the bone pose.

9. Reset any original shape-key values.

10. Set the new key's value to 1.

11. Review the new key on its own.

If the bone pose or source mix remains active, it adds deformation again. This native operation does not update BoneCraft's Pose To Shape pipeline checkmark.

![The native Armature modifier menu offers Save as Shape Key separately from Apply as Shape Key.](images/screenshots/bc30-native-save-shape-key.png){style="max-width:100%;max-height:155mm;width:auto;height:auto"}

*Local preview, BoneCraft 9.2.19 candidate. Bforartists 5.2.3, Blender 5.4 Alpha. Native Armature modifier menu before execution. Save as Shape Key keeps the modifier; this picture does not show a captured pose result.*

### Shape Key to Basis

Makes the active non-Basis shape key the new Basis. It adjusts the other keys relative to that Basis.

1. Before this operation, save a file checkpoint.

2. After the operation, review the remaining keys.

![Pose to Shape Key captures the current key mix. Shape Key to Basis makes the active key the new Basis.](images/screenshots/bc30-pose-shape.png){style="max-width:100%;max-height:155mm;width:auto;height:auto"}

*Native panel popover, BoneCraft 9.2.18. Pose to Shape Key captures the current key mix. Shape Key to Basis makes the active key the new Basis.*

---

## Transforms & FBT

**Pipeline phase:** 6 (last)

### Apply All Transforms

Applies position, rotation and scale to the mesh and armature, resetting their transform channels. Earlier tools remain available.

1. Before this operation, save a file checkpoint.

2. Compare the avatar before and after the operation.

If the size differs after export, inspect mesh transforms, armature transforms, export scale settings and import scale settings.

### Fix FBT

A transform correction for Full Body Tracking setups: moves the root bone to floor level.

### Remove FBT

Removes the Fix FBT correction again.

![Apply All Transforms, Fix FBT and Remove FBT are the final pipeline actions.](images/screenshots/bc30-transforms.png){style="max-width:100%;max-height:155mm;width:auto;height:auto"}

*Native panel popover, BoneCraft 9.2.18. Apply All Transforms, Fix FBT and Remove FBT are the final pipeline actions.*

---

## Bone Tools

- **Create Root Bone** — adds a root bone (named by **Root Name**) at the bottom of the hierarchy
- **Merge Bones** — merges bones shorter than the **Merge Threshold** into their parents
- **Duplicate Bones** — duplicates the selected bones

![Create Root Bone, Merge Bones and Duplicate Bones. Adjust root names and thresholds after the action.](images/screenshots/bc30-bone-tools.png){style="max-width:100%;max-height:155mm;width:auto;height:auto"}

*Native panel popover, BoneCraft 9.2.18. Create Root Bone, Merge Bones and Duplicate Bones. Adjust root names and thresholds after the action.*

---

## Armature Tools

**What it does:** Merges one armature into another, for example an outfit's armature into the body's.

**Key controls:**

- **Base / Root** — the armature that stays (the result keeps its name)
- **Incoming** — the armature that merges into the base. Bones with the same name merge into the base.
- Naming Prep — matches the two rigs' bone names before merging. It works on any rig, including rigs from sources other than Mixamo.
- Options to parent the bones automatically and to join the meshes afterwards
- **Merge Incoming Into Base** — merges

For Naming Prep:

1. Select Mixamo Prefixed.

2. Select **Normalize Merge Names**.

3. Select Mixamo Stripped.

4. Select **Normalize Merge Names** again.

Both rigs end with the same names.

For a staged merge with previews, use Bone Merge (see [Rig Builder](06-rig-builder.md#bone-merge)).

![Choose Base and Incoming armatures, review Naming Prep, then Merge Incoming Into Base.](images/screenshots/bc30-armature-tools.png){style="max-width:100%;max-height:155mm;width:auto;height:auto"}

*Native panel popover, BoneCraft 9.2.18. Choose Base and Incoming armatures, review Naming Prep, then Merge Incoming Into Base.*

---

## Mesh Tools

- **Separate by Materials** — one mesh per material
- **Separate by Loose Parts** — one mesh per connected piece
- **Separate by Shape Keys** — splits off the parts that shape keys move

![Separate meshes by materials, loose parts or shape keys.](images/screenshots/bc30-mesh-tools.png){style="max-width:100%;max-height:155mm;width:auto;height:auto"}

*Native panel popover, BoneCraft 9.2.18. Separate meshes by materials, loose parts or shape keys.*

---

## Smart Automatic Weights

**Smart Automatic Weights** opens a dialog with smart defaults and a hidden backup.

1. Check the target mesh and armature.

2. To recalculate weights from the existing rig, select Body.

3. To transfer weights from a weighted source mesh, select Clothing instead.

**Advanced Recalculation** expands a location hint for **BoneCraft → Skin → Weight Tools**. It does not open the full controls here. See [Rig Tools](05-rig-tools.md#automatic-bone-weight-recalculation).

![Smart Automatic Weights opens its setup dialog. Advanced Recalculation points to the full weight controls.](images/screenshots/bc30-smart-weights.png){style="max-width:100%;max-height:155mm;width:auto;height:auto"}

*Native panel popover, BoneCraft 9.2.18. Smart Automatic Weights opens its setup dialog. Advanced Recalculation points to the full weight controls.*

---

## Pipeline Status and Operation Ledger

Pipeline Status shows which of the six phases are complete. The Operation Ledger lists each CATS operation with its time and outcome: Changed, Clean or Failed. **Copy** copies the ledger to the clipboard. **Clear** empties the ledger. See [The CATS Pipeline](04-cats-pipeline.md).

Next: [Quick Fixes and Glossary](10-reference.md)

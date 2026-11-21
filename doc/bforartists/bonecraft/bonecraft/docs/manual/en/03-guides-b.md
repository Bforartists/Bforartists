# Guides 8–13

[← Contents](index.md)

## Guide 8: Set Up Lip Sync

> **Time:** About 10–20 minutes
> **Result:** Your avatar's mouth moving correctly when you speak in VRChat

**Before you begin — check these:**

- [ ] Your avatar's head mesh has mouth shape keys (also called blend shapes or morph targets — the different mouth positions for speaking)
- [ ] You know roughly what the shape keys are named (look in the Shape Keys list of the mesh's Object Data properties)

> Viseme = a mouth shape for a sound. `aa` is the "ahh" sound, `O` the "ohh" sound, and so on. VRChat uses 15 visemes to drive your avatar's lip sync.
>
> Shape key (blend shape) = a saved version of your mesh in another position. Your mouth-open shape key is your mesh with the mouth open.

---

### Step 1 — Open VRChat Viseme Mapping

See the [Viseme Mapping and Face Tracking controls](08-vrchat.md#vrchat-viseme-mapping).

Open **CATS → VRChat Tools → Facial → VRChat Viseme Mapping**.

---

### Step 2 — Auto-Map Visemes

Click **Auto-Map All Visemes**. BoneCraft reads your mesh's shape keys and matches them to VRChat's 15 viseme slots by name.

**What you should be seeing:** The viseme list, with most slots showing a mapped shape key.

---

### Step 3 — Fill in Missing Slots

An empty slot shows "(unmapped)".

1. Select the slot's button to open the mesh's shape-key search list.

2. Type to filter the list.

3. Select the closest shape key.

To clear a slot, select "(unmapped)". Common matches:

| VRChat viseme | What it sounds like | Shape key to look for |
|---|---|---|
| `aa` | "ahh" | mouth_open, A, aa |
| `O` | "ohh" | mouth_o, OH, oh |
| `CH` | "ch" / "sh" | mouth_ch, CH |
| `PP` | lips together (P, B, M) | mouth_m, MM, lips_together |
| `SS` | "sss" / "zzz" | mouth_s, SS |

**Missing viseme shape keys:** CATS → **Visemes** creates all 15 keys from three base shapes: A, O and CH. If the mesh has no mouth shapes, create those three first. See [Guide 13, Phase 2](#phase-2--viseme-generation).

---

### Step 4 — Check a Mouth Shape

1. In **Properties → Object Data → Shape Keys**, set the mapped key's value to 1.0.

2. Inspect the mouth shape.

3. Reset the value to 0.

---

### Step 5 — Face Tracking (Optional)

Below the viseme list, **Face Tracking (SteamVR)** prepares expression shapes for face-tracking hardware. It is optional: most users do not need it.

**What This Unlocks:** Your avatar's mouth moves when you talk in VRChat. Expressions build on the shape keys you just mapped.

---

## Guide 9: Improve Your Avatar's Performance

> **Time:** About 15–25 minutes
> **Result:** A better VRChat performance rank and faster loading for other players

**Before you begin — check these:**

- [ ] Your avatar is complete (rigged, clothed, lip sync set up)
- [ ] You know your target rank (Good or Excellent for most users)

> Performance rank = VRChat's rating of how demanding your avatar is. Very Poor avatars may be hidden by other players. Good and Excellent avatars load fast and are always shown.

---

### Step 1 — Check the Current Rank

1. Open **CATS → VRChat Tools**.

2. In Performance, select **Calculate Performance Rank**.

BoneCraft reports the overall rank and each metric's distance from the next tier. Metrics include polygons, skinned meshes, material slots, bones, PhysBones and contacts.

See the [Performance controls](08-vrchat.md#check-performance).

---

### Step 2 — Clean Up

The VRChat Optimizer in the same section lists cleanup tools. **What-If Mode** starts enabled. Each fix reports its proposed changes without applying them.

1. Run the required fix in What-If Mode.

2. Review the report.

3. To apply those changes, disable What-If Mode.

4. Run the fix again.

Available fixes:

1. **Remove Zero-Weight Bones** — deletes bones that move no part of the mesh
2. **Merge Same-Material Meshes** — joins meshes that share a material
3. **Remove Unused Shape Keys** — removes empty shape keys whose deformation matches Basis. It does not check references from other tools.
4. **Remove Unused Vertex Groups** — removes empty weight groups

---

### Step 3 — Reduce the Polygon Count (If Needed)

See the [Performance and Decimation controls](08-vrchat.md#check-performance).

If the polygon count is too high:

1. Select the mesh.

2. In VRChat Decimation, set the target ratio.

3. Select **Preview**.

4. Inspect the result.

5. To keep the result, select **Apply**.

A ratio of 0.5 halves the polygon count. A ratio of 0.8 removes 20%. Decimation protects shape keys.

> Start at 0.8. Reduce the ratio gradually while checking the avatar's appearance. Small reductions can improve performance with little visible change.

---

### Step 4 — Merge Materials (Optional)

If your avatar uses many materials, combine them into one texture sheet (an atlas). In the **CATS** tab → **CATS** → **Material Atlas**:

1. Save a copy of the file.
2. Set **Target** to the meshes you want to process.
3. Keep **Preserve Backup Duplicate** enabled.
4. Click **Analyze Materials**.
5. Select an atlas group.
6. Check at least two materials in that enabled group.
7. Check the texture images to include.
8. Use **Select All** or **Deselect All** above either list when needed.
9. Click **Bake Checked Sources**.
10. Review the preflight summary before confirming the bake.
11. Inspect the baked materials, transparency and UVs.
12. Click **Accept — Delete Backup** to keep the result.

Use **Revert — Restore Originals** instead when the result needs changes. Accept deletes the backup. Disabling **Preserve Backup Duplicate** removes the Revert option.

Bulk selection affects only its source list in the active group. Missing textures stay unchecked. The other list and other groups remain unchanged.

**Refresh Analysis** rebuilds the source lists and their choices. Use **Bake Checked Sources** after reviewing your choices. **Smart Combine Materials** is the initial automatic shortcut.

[CATS Tools: Material Atlas Combiner](09-cats.md#material-atlas-combiner) explains every setting.

---

### Step 5 — Check the Rank Again

Click **Calculate Performance Rank** again to see the improvement.

**What This Unlocks:** A better rank means more players see your avatar. A Good or Excellent avatar loads quickly, uses less GPU, and is shown to other players by default.

---

## Guide 10: Save and Reuse Poses

> **Time:** About 5–10 minutes
> **Result:** A saved library of poses you can apply with one click

**Before you begin — check these:**

- [ ] Your avatar has a finished skeleton
- [ ] You are in **Pose Mode**

To enter Pose Mode:

1. Select the armature.

2. Press Ctrl+Tab.

Alternatively, select **Pose Mode** in the viewport's top-left mode dropdown.

---

### Step 1 — Open the Pose Library

In the **BoneCraft** tab on the left Tool Shelf, expand **Review** → **Pose Library**.

See the [Pose Library controls](05-rig-tools.md#pose-library).

---

### Step 2 — Pose Your Avatar

Move the bones into the pose you want to save. A pose can combine arm rotations, head tilt and other bone positions.

---

### Step 3 — Save the Pose

1. Select **Save**.

2. Enter a pose name, such as "Peace Sign" or "Thinking".

**Category** groups poses under names such as "Greetings". **Filter** shows one category at a time. The saved pose includes a viewport thumbnail.

---

### Step 4 — Apply a Saved Pose

1. Select a pose.

2. Select **Apply**.

- **Blend** — applies the pose at partial strength, to mix two poses
- **Mirror** — applies the pose flipped left to right

**Rename** and **Delete** manage the list.

---

### Step 5 — Export and Import Poses

**Export** saves your pose library to a `.bfpose` file you can keep with the project or share. **Import** loads poses from a `.bfpose` file.

**What This Unlocks:** A personal pose library you can reuse across projects, blend for animation keys, or share with other BoneCraft users.

---

## Guide 11: Merge Two Rigs Together

> **Time:** About 25–40 minutes depending on complexity
> **Result:** Two skeletons combined into one, with all weights kept

**Before you begin — check these:**

- [ ] The base avatar and the second rig (a clothing or accessory rig) are in the same file
- [ ] Both are rigged and weighted

> Rig merge = absorbing one skeleton into another, so you end up with one combined skeleton. Useful when a body rig and a hair or outfit rig must become one.

---

### Step 1 — Open Bone Merge

Open **BoneCraft → Setup Rigging → Bone Merge**. Its three stages open in order as you complete them.

See the [staged Bone Merge controls](06-rig-builder.md#bone-merge).

---

### Step 2 — Stage 1: Scope

1. Select the **Base** armature, the body skeleton that remains.

2. Select the incoming clothing or hair armature.

3. Select **Analyze**.

During the final merge, the incoming armature merges into the base and then becomes hidden.

Analyze compares the two skeletons and lists:

- ✓ Matched — bones that exist in both and line up
- \+ Source only — bones of the merging rig with no match in the base
- − Target only — base bones the merging rig does not have

When you have read the list, click **Acknowledge Scope — Proceed to Rename**.

---

### Step 3 — Stage 2: Rename

For each source-only bone, choose the applicable branch.

If the bone has an equivalent in the base:

1. Enter that base bone's name.

2. Select **Apply Rename**.

If the bone has no equivalent, select **Mark as Unique** instead. It joins the base without a name change.

**Normalize Both Armatures** renames recognized standard bones, such as spine, arms and legs, in both rigs. **Auto-Propose Renames** suggests names for other bones from their positions. **Apply Batch Pattern** renames multiple bones with one pattern.

When every source-only bone is resolved, click **Verify Rename — Proceed to Merge**.

---

### Step 4 — Stage 3: Merge

Click **Run Merge Preview** first: it reports what the merge will do without changing anything.

When the report looks right, click **Merge Armatures**. BoneCraft backs up both armatures, then combines them.

**What you should be seeing:** One armature containing all bones of both skeletons, with every mesh weighted to it.

**What This Unlocks:** A single rig that is easier to export and edit. Needed for any avatar with separate clothing or accessory rigs.

---

## Guide 12: Fix Upload Problems

> **Time:** About 5–15 minutes depending on the issue

**Before you begin:** Find your problem in the list below and go to that section.

---

### "Upload failed — bones not recognized"

Your bones have names VRChat does not understand. → [Guide 4: Fix Your Avatar's Bone Names](02-guides-a.md#guide-4-fix-your-avatars-bone-names)

---

### "Avatar is in T-pose / not moving with me in VRChat"

The humanoid mapping is missing or wrong. → [Guide 5: Map Your Avatar to VRChat's Body System](02-guides-a.md#guide-5-map-your-avatar-to-vrchats-body-system)

---

### "Mesh is deforming weirdly / skin stretching wrong"

The bone weights need adjusting. → See Weight Transfer and Weight Mirror in [Rig Tools](05-rig-tools.md), or run **Smart Automatic Weights** in the CATS tab.

---

### "Hair is clipping through the head"

Hair colliders are missing or too small. → [Guide 6: Add Hair Physics](02-guides-a.md#guide-6-add-hair-physics), Step 5.

---

### "Avatar is Very Poor performance and being blocked by other players"

→ [Guide 9: Improve Your Avatar's Performance](#guide-9-improve-your-avatars-performance)

---

### "Lip sync not working"

The visemes are not mapped correctly. → [Guide 8: Set Up Lip Sync](#guide-8-set-up-lip-sync)

---

### "Rig validator shows errors"

1. Open **BoneCraft → Review → Rig Validator**.

2. Select **Run Validation**.

3. Follow the result's suggestion or check the [Quick-Fix Index](10-reference.md#quick-fix-index).

Each result names the problem and bone. **Export Report** saves the results to a file.

---

### "VRM import not working"

The VRM add-on may not be installed. → [Guide 2](02-guides-a.md#guide-2-bring-a-vroid-avatar-into-vrchat), Step 1.

---

### "MMD import not working"

Check whether **mmd_tools** is installed and enabled. The bridge supports modern Extensions and legacy packages. Review the installation message before retrying. See [Guide 3](02-guides-a.md#guide-3-bring-an-mmd-avatar-into-vrchat), Step 1.

---

## Guide 13: Get Your Avatar VRChat-Ready with CATS

> **Time:** About 20–35 minutes for a full pipeline run
> **Result:** A clean, optimized avatar with lip sync, eye tracking, and correct transforms — ready for VRChat upload

**Before you begin — read this first:**

The CATS tools have a recommended pipeline. Pipeline Status marks completed phases: Fix Model, Material Atlas, Visemes, Eye Tracking, Pose To Shape and Apply Transforms. The Operation Ledger records each CATS operation.

Tools still run when an earlier phase is incomplete. They show a warning such as "Run Fix Model first for best results".

Start by reviewing Fix Model's cleanup options. Save a file checkpoint before changing the avatar.

Before continuing, read [The CATS Pipeline](04-cats-pipeline.md).

**Before you begin — check these:**

- [ ] Your avatar is imported and visible in the 3D viewport
- [ ] The CATS tab is open on the right sidebar (press N if the sidebar is hidden)
- [ ] Your avatar is selected (click it in the viewport or the outliner)

---

### Phase 1 — Fix Model

Fix Model is the recommended cleanup phase. Review its options for your imported avatar, then inspect the result before continuing.

**What Fix Model does** (each part can be switched off in its options):

- Applies modifiers
- Removes duplicate vertices and loose geometry (triangles floating away from the body)
- Recalculates normals (the directions that decide which side of the mesh faces outward)
- Removes empty vertex groups and zero-weight bones
- Removes constraints and rigid bodies VRChat cannot use

**Steps:**

1. Open **CATS → CATS → Fix Model**.

2. Select your avatar's mesh.

3. Select **Fix Model**.

4. Wait for the operation to finish.

5. Check that Pipeline Status marks Fix Model with ✓.

Large meshes can take a few seconds.

**What you should be seeing:** Your avatar looks the same or slightly cleaner. Pipeline Status checks Fix Model, and the Operation Ledger lists the run.

**If your model disappears or looks inside-out after Fix Model:**

The symptom alone does not identify the cause.

1. Inspect the enabled cleanup options, object visibility, geometry and normals.

2. If restoration is necessary, use Undo or a saved checkpoint to restore the earlier state.

3. Before retrying, correct the identified problem.

See the [Fix Model controls](09-cats.md#fix-model).

---

### Phase 2 — Viseme Generation

Run after: Fix Model ✓

The Visemes section creates all 15 VRChat lip-sync mouth shapes from three base shapes you already have. If your avatar already has complete viseme shape keys, you can skip this phase — but check them in VRChat Viseme Mapping (Guide 8).

VRChat needs 15 mouth shapes (visemes) to drive your avatar's lips when you speak. Most avatars have only a few basic mouth shapes. CATS combines your base shapes to make the rest.

The three base shapes:

- **A Shape** — wide open mouth (the "ahh" shape)
- **O Shape** — rounded mouth (the "ohh" shape)
- **CH Shape** — narrow open mouth with teeth showing (the "ch" / "sh" shape)

**If your avatar has no mouth shape keys:** sculpt or edit A, O and CH as shape keys first. CATS uses these to generate the remaining shapes. See the Glossary entry for Shape Key.

**Steps:**

1. Open **CATS → CATS → Visemes**.

2. Choose automatic or manual source selection below.

   For automatic selection, select **Auto-Detect** to fill the three source shapes.

   For manual selection, select the closest match for each of the three source shapes.

   Example key names include `mouth_open`, `vrc.v_O` and `mouth_wide`.

3. Select **Generate Visemes**.

4. Check that Pipeline Status shows Visemes ✓.

CATS creates 15 shape keys with VRChat names, including `vrc.v_aa`, `vrc.v_O` and `vrc.v_CH`.

**What you should be seeing:** 15 new shape keys in the mesh's Shape Keys list (Properties → Object Data → Shape Keys).

See the [CATS Visemes controls](09-cats.md#visemes).

---

### Phase 3 — Eye Tracking

Run after: Fix Model ✓

Eye Tracking configures the eye bones for VRChat's built-in eye tracking. The eyes can then move and look at other players.

**What it does:**

- Finds the left and right eye bones
- Names them as VRChat requires (`LeftEye` and `RightEye`)
- Adds the rotation constraints VRChat needs to move the eyes
- Limits eye rotation to a natural range (up, down and to the side)

Auto-Detect searches common eye-bone names. It does not inspect mesh geometry or bone positions.

If you rename the bones:

1. Rerun detection.

2. Check both eye-bone assignments.

If eye motion is wrong, inspect bone orientation, constraints and the exported avatar.

**Steps:**

1. Open **CATS → CATS → Eye Tracking**.

2. Select **Auto-Detect** to search common left and right eye-bone names.

3. Check the **Left Eye** and **Right Eye** fields.

4. If an assignment is wrong, select the correct bone manually.

5. If necessary, set **Up Limit**, **Down Limit** and **Side Limit**.

6. Select **Create Eye Tracking**.

7. Check that Pipeline Status shows Eye Tracking ✓.

**What you should be seeing:** Both eye bones renamed, with rotation constraints in the Bone Constraints panel.

> **If CATS cannot find eye bones:** your skeleton may have none. Some formats (especially older MMD models) blink with shape keys instead of bones. Skip this phase: VRChat falls back to shape-key eye animation when there are no eye bones.

---

### Phase 4 — Pose to Shape Key

Run after: Fix Model ✓

The current **Pose to Shape Key** button captures the selected mesh's current shape-key mix. It does not bake deformation from armature bones. For a bone-deformed pose, use the verified [native Save as Shape Key workflow](09-cats.md#save-a-bone-deformed-pose).

**Steps:**

1. Switch to Object Mode.

2. Select the target mesh.

3. Set its existing shape-key values to the blend you want to capture.

4. Keep the mesh active.

5. Open **CATS → CATS → Pose & Shape Keys**.

6. Select **Pose to Shape Key**.

7. Enter the new shape key's name.

8. Confirm the operation.

9. Reset the original shape-key values to 0.

10. Inspect the new key alone.

11. Check that Pipeline Status shows Pose To Shape ✓.

The tool already sets the new key to 1.

**What you should be seeing:** A new shape key that reproduces the captured shape-key mix. Leaving the original keys active adds their deformation again.

> **Shape Key to Basis:** makes the active non-Basis shape key the new Basis. It adjusts the other keys relative to that Basis. Before this operation, save a checkpoint. Afterwards, review the remaining keys.

See the [Pose to Shape Key controls](09-cats.md#pose-to-shape-key).

---

### Phase 5 — Apply Transforms

Run after: every earlier phase you need

Apply Transforms is the recommended final preparation phase. It applies position, rotation and scale to the mesh and skeleton. The channels reset to 0, 0 and 1 respectively.

Save a checkpoint before this operation. Compare the avatar before and after the operation. Earlier tools remain available.

If the exported avatar has the wrong size, inspect mesh and armature transforms and the export and import scale settings. Use Undo or a saved checkpoint when you need to restore an earlier state.

**The tools in Transforms & FBT:**

- **Apply All Transforms** — applies position, rotation and scale to the mesh and the armature together
- **Fix FBT** — a transform correction for Full Body Tracking setups (moves the root bone to floor level)
- **Remove FBT** — removes that correction again

Material Atlas and Pose To Shape are optional. If you mapped existing visemes, Visemes remains unchecked.

**Steps:**

1. In Pipeline Status, confirm that the phases your avatar needs are checked.

2. Open **CATS → CATS → Transforms & FBT**.

3. Select **Apply All Transforms**.

4. Check that Pipeline Status shows Apply Transforms ✓.

5. Export through **CATS → Import / Export → Game Engine Export → Unity / VRChat** (Guide 1, Step 9).

**What you should be seeing:** Apply Transforms checked, after the phases you needed. Review the exported avatar in the VRChat Creator Companion.

See the [transform and FBT controls](09-cats.md#apply-all-transforms).

---

**What This Unlocks:** An avatar prepared for export checks, with the cleanup, mouth shapes, eye tracking and expressions you chose. Validate it in the target application before upload.

Next: [The CATS Pipeline](04-cats-pipeline.md)

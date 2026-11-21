# Guides 1–7

[← Contents](index.md)

## Guide 1: Get Your First Avatar Into VRChat

For a practice mesh, follow the [illustrated mannequin workshop](06-rig-builder.md#illustrated-mannequin-workshop). Its stages are Simple Human, a rigless mannequin, Auto-Rig and IK/FK.

> **Time:** About 45–60 minutes for a complete first run
> **Result:** A rigged, VRChat-ready avatar exported for the VRChat SDK

**Before you begin — check these:**

- [ ] Your 3D model is imported into Bforartists (File > Import, choose your format)
- [ ] The model is in a T-pose (arms out to the sides, body upright) — or close to it
- [ ] The model has no obvious broken geometry (no random floating triangles)
- [ ] You can see your model in the 3D viewport as a solid grey shape

---

### Step 1 — Open the Rig Builder

1. In the 3D Viewport, press **T** to show the left Tool Shelf.

2. Open **Rig Builder**.

Rig Builder also appears in **Properties → Scene** when Preferences → Tabs → Scene Properties → Show is enabled. Its three parts are **Auto-Rig Wizard**, Quick Rig (premade armatures) and **Mannequin**.

3. Expand **Auto-Rig Wizard**.

4. Select **Start Auto-Rig**.

You can also start the wizard from the 3D Viewport's Add → Armature → Auto-Rig Wizard menu, then continue in Rig Builder.

![Auto-Rig Wizard in the Rig Builder tab.](../images/rig-builder/en/b06-start-wizard.png){style="max-width:100%;max-height:155mm;width:auto;height:auto"}

*Historical workshop capture. Auto-Rig Wizard in the Rig Builder tab.*

---

### Step 2 — Select Your Mesh

The wizard lists the scene's meshes.

1. Select your avatar's mesh in the list.

2. Select **Next**.

**What you should be seeing:** A line "Selected:" with your mesh's name, then the rig type step.

![Choose the input mesh for the Auto-Rig Wizard.](../images/rig-builder/en/b07-select-input.png){style="max-width:100%;max-height:155mm;width:auto;height:auto"}

*Historical workshop capture. Choose the input mesh for the Auto-Rig Wizard.*

---

### Step 3 — Choose the Rig Type

1. For blinks, expressions and lip sync, select **Body + Face**.

2. For a body without facial controls, select **Body Only** instead.

3. Under Generation Options, set **Kinematics** to IK/FK, IK only or FK only.

4. Select **Next**.

![Choose the body rig type and IK/FK methods.](../images/rig-builder/en/b08-body-ikfk.png){style="max-width:100%;max-height:155mm;width:auto;height:auto"}

*Historical workshop capture. Choose the body rig type and IK/FK methods.*

---

### Step 4 — Place Body Markers

Markers identify the pelvis, spine, neck, head, shoulders, arms, hands, legs and feet. BoneCraft uses these positions to build the bones. Check each marker carefully.

**Smart Detection:**

1. Select **Detect Markers**.

2. Select **Accept High** to retain high-confidence markers.

3. Select **Reset Low** to clear low-confidence markers for manual placement.

BoneCraft traces the mesh limbs and assigns a confidence to each marker. **Guess Markers from Mesh** estimates positions from mesh proportions instead.

**With the viewport tool:**

1. In Object Mode, activate Place Rig Markers in the viewport toolbar.

2. Click the mesh to place and confirm the marker named in the tool header.

3. Repeat for the next unconfirmed marker.

4. When the marker step is complete, select **Next** in the wizard.

The tool header also contains axis locks and a mirror switch.

**One marker at a time:** each marker has a row of icon buttons. Hover a button to read its tooltip.

1. Select **Place Marker**, the arrow icon on the marker's row.

2. Click the required position on your avatar.

3. When the position is correct, select **Confirm Marker**, the check mark.

**Reset Marker**, the circular arrow, clears a placed marker for placement again.

**Symmetry:** **Toggle Symmetry** places the opposite marker whenever you place a marker. It is the first icon on each left or right marker row. **Mirror L to R** and **Mirror R to L** copy every confirmed marker to the opposite side.

1. When every marker is placed, select **Confirm All Placed**.

2. Select **Next**.

![Review the detected body markers before adjusting them.](../images/rig-builder/en/b10-review-markers.png){style="max-width:100%;max-height:155mm;width:auto;height:auto"}

*Historical workshop capture. Review the detected body markers before adjusting them.*

---

### Step 5 — Place Finger Markers

1. Under Finger Detail, select the finger count from "0 — No Fingers" to "5 — Full Human Hand".

2. Select **Guess Finger Markers**.

3. Adjust incorrect marker positions.

4. Select **Next**.

BoneCraft traces each finger from knuckle to fingertip using the hand's shape. A standard hand uses "5 — Full Human Hand".

---

### Step 6 — Place Face Markers (Body + Face only)

1. Select **Guess Face Markers**.

2. Adjust the eyes, lids, brows, mouth corners and jaw as necessary.

3. Select **Next**.

Eye markers retain their manually assigned positions.

---

### Step 7 — Review and Generate

The review step lists any warnings and the generation options. Click **Generate Rig**.

**What you should be seeing:** Orange bones inside your avatar, including IK/FK limbs and finger bones. A Body + Face rig also contains a face rig. The attached skin deforms when the bones move.

The final step offers **Build Control Rig** and **Close Wizard**. Build Control Rig applies the review options that Generate Rig does not apply. [Rig Builder](06-rig-builder.md) describes both controls.

> **Skin weights** define which bones move each part of the mesh. BoneCraft sets weights automatically. For refinements, use the Weight Tools in [Rig Tools](05-rig-tools.md).

![Review the rig settings before generation.](../images/rig-builder/en/b19-review-generate.png){style="max-width:100%;max-height:155mm;width:auto;height:auto"}

*Historical workshop capture. Review the rig settings before generation.*

---

### Step 8 — Map to VRChat's Humanoid Bones

1. Press **N** to show the right sidebar.

2. Open **CATS → Avatar Tools → Set Up Humanoid Bones**.

3. Select **Auto-Map All**.

4. Select **Normalize Names**.

5. Select **Validate**.

Auto-Map All connects bones to VRChat's body slots. Normalize Names gives the mapped bones VRChat's expected names.

**What you should be seeing:** The required slots (Hips, Spine, Head, LeftUpperArm and so on) each show a bone. Guide 5 explains the slots.

See the [humanoid mapping controls](08-vrchat.md#set-up-humanoid-bones).

---

### Step 9 — Export for VRChat

See the [Unity / VRChat export settings](08-vrchat.md#export-to-vrchat).

1. Select the avatar armature.
2. Open **CATS → Import / Export → Game Engine Export → Unity / VRChat**.
3. Set **Folder**.
4. Set **Avatar** to the export name.
5. Choose **Bone Names**.
6. Review the naming preview when using a preset.
7. Click **Export to VRChat (Unity)**.

**Keep Original Names** is the default. **Unity-Preset** and **Unreal-Preset** rename recognized bones on export copies. The working rig keeps its names.

The main Unity and Unreal export buttons accept Object, Pose and Edit Mode. They restore the previous mode and selection.

See [export naming and limits](08-vrchat.md#export-bone-naming) for conflicts, mapping and animation restrictions.

**What you should be seeing:** The exported avatar in your chosen folder, ready for the VRChat Creator Companion and the VRChat SDK in Unity.

---

**What This Unlocks:** A rigged VRChat avatar. Next options include hair physics (Guide 6), clothing (Guide 7), lip sync (Guide 8) and performance checks (Guide 9). For CATS cleanup and VRChat setup, see [Guide 13](03-guides-b.md#guide-13-get-your-avatar-vrchat-ready-with-cats).

---

## Guide 2: Bring a VRoid Avatar into VRChat

> **Time:** About 15–25 minutes
> **Result:** Your VRoid avatar ready for VRChat export

**Before you begin — check these:**

- [ ] You have exported your avatar from VRoid Studio as a `.vrm` file, or downloaded it from VRoid Hub as a `.zip`
- [ ] BoneCraft is installed and enabled

---

### Step 1 — Install the VRM Add-on

BoneCraft needs the VRM add-on to read `.vrm` files.

1. Open **CATS → Import / Export → VRM / VRoid**.

2. Install the dependency before importing.

3. Enable the dependency.

The inactive bridge offers **Auto-Install Latest from GitHub**, **Open Add-on Preferences**, **Website** and **Show Manual Instructions**.

For an offline package:

1. Open native Preferences.

2. For a legacy add-on ZIP, install it through **Add-ons → Install from Disk…**.

3. For a modern extension package, use the native Extensions installation menu instead.

4. Return to the bridge.

5. Confirm that the bridge reports **Active**.

See the [format bridge installation controls](08-vrchat.md#vrm-bridge).

---

### Step 2 — Import Your Avatar

1. In **VRM / VRoid**, select **Import VRM…**.

2. Select your `.vrm` file.

For a VRoid download:

1. Select **Import VRoid (.vroid / .zip)…** instead.

2. Select the downloaded `.zip` file.

If you select a VRoid Studio project file (`.vroid`), BoneCraft shows a "VRoid Studio Project" card. A project is not an avatar yet.

For that project file:

1. Export the project to VRM in VRoid Studio.

2. Import that VRM file.

**What you should be seeing:** Your VRoid character in the viewport with its skeleton in place.

---

### Step 3 — Map to VRChat's Humanoid Bones

1. Open **CATS → Avatar Tools → Set Up Humanoid Bones**.

2. Select **Auto-Map All**.

VRoid skeletons follow a standard layout, so this usually fills every slot. If a slot is wrong, select **Fix Humanoid Map** under Lint in **VRM / VRoid**. This repairs common VRoid name-mapping errors.

---

### Step 4 — Fix Bone Names

In **Set Up Humanoid Bones**, select **Normalize Names**. This replaces VRoid names on mapped bones with VRChat's expected names.

---

### Step 5 — Set Up Visemes (Lip Sync)

VRoid avatars already have the mouth shapes for lip sync. In the **VRM / VRoid** section, click **Map VRoid Visemes**. BoneCraft matches VRoid's shape keys to VRChat's lip-sync shapes.

---

### Step 6 — Hair Physics (Optional)

VRoid hair uses SpringBones. **Convert SpringBones → PhysBones** in the **VRM / VRoid** section turns them into VRChat PhysBones. Guide 6 covers hair physics in more detail.

---

### Step 7 — Export

Export as in Guide 1, Step 9.

**What This Unlocks:** Your VRoid avatar is ready for the VRChat Creator Companion. You can also check performance (Guide 9) before uploading.

---

## Guide 3: Bring an MMD Avatar into VRChat

> **Time:** About 20–30 minutes
> **Result:** Your MMD `.pmx` model ready for VRChat

**Before you begin — check these:**

- [ ] You have a `.pmx` or `.pmd` MMD model file
- [ ] BoneCraft is installed

---

### Step 1 — Install mmd_tools

BoneCraft requires **mmd_tools** to read MMD files. It recognizes both legacy add-ons and modern Blender Extensions.

1. Open **CATS → Import / Export → MMD / PMX**.
2. Click **Auto-Install Latest from GitHub** when the bridge reports a missing dependency.
3. Use **Open Add-on Preferences** to enable an installed, disabled copy.
4. Confirm that the bridge reports **Active** before importing.

For manual installation:

1. In the inactive bridge card, select **Website** or **Show Manual Instructions**.

2. Install the official MMD extension through **Preferences → Get Extensions**.

For an offline ZIP:

1. For a modern extension package, use the extension installation menu.

2. For a legacy add-on package, use **Add-ons → Install from Disk…** instead.

The standalone bridge content also offers **Install from .zip on Disk...** when shown.

If installation reports no local extension repository:

1. Open **Preferences → Get Extensions → Repositories**.

2. Add or enable a local repository.

3. Retry installation.

Use the upstream release package. An installation error or cancelled import does not count as a successful import.

See the [format bridge installation controls](08-vrchat.md#vrm-bridge).

---

### Step 2 — Import Your PMX File

1. In **MMD / PMX**, select **Import PMX / PMD...**.

2. Select your model.

**What you should be seeing:** Your MMD character in the viewport with Japanese bone names.

---

### Step 3 — Fix Bone Names

Map the MMD bones to Unity humanoid slots before VRChat export.

1. In **MMD / PMX**, select **Convert Bone Names -> Unity**.

For names in another language:

1. Open **CATS → CATS → Translate Bone Names**.

2. Select the source **Language**.

3. Select **Translate Bone Names**.

---

### Step 4 — Clean Up the Model

MMD models often contain extra geometry and separate parts.

1. Open **CATS → CATS**.

2. Review the **Fix Model** options.

3. Select the cleanup operations your avatar needs.

4. Run **Fix Model**.

5. Select **Join Meshes** to combine the body parts into one mesh, as recommended for VRChat.

[Guide 13](03-guides-b.md#guide-13-get-your-avatar-vrchat-ready-with-cats) explains the complete CATS pipeline.

---

### Step 5 — Map to VRChat's Humanoid Bones

1. Open **CATS → Avatar Tools → Set Up Humanoid Bones**.

2. Select **Auto-Map All**.

3. For an empty slot, select its button.

4. Select the corresponding bone.

MMD skeletons resemble VRChat skeletons, so most slots fill automatically.

---

### Step 6 — Physics and Export

**Convert Physics -> PhysBones** in the **MMD / PMX** section turns MMD's rigid-body hair and skirt physics into VRChat PhysBones. Then export as in Guide 1, Step 9.

**What This Unlocks:** Your MMD avatar is ready for VRChat. You can add hair physics (Guide 6) and set up lip sync (Guide 8) before uploading.

---

## Guide 4: Fix Your Avatar's Bone Names

> **Time:** About 5–15 minutes
> **Result:** The bones VRChat needs renamed to VRChat-compatible names

**Before you begin — check these:**

- [ ] Your avatar is open with its skeleton (armature) visible

---

### Step 1 — Detect the Current Naming Style

See the [Naming controls](08-vrchat.md#vrchat-naming-extras).

1. Open **CATS → VRChat Tools**.

2. In Naming, select **Detect**.

3. After name changes, select **Force Rescan** to check again.

BoneCraft reports the detected naming style, such as Mixamo, VRoid or Unity, and a score.

For Japanese, Chinese, Korean, Portuguese, Spanish or French bone names:

1. Open **CATS → CATS → Translate Bone Names**.

2. Select the source **Language**.

3. Select **Translate Bone Names**.

This converts recognized names to English.

---

### Step 2 — Rename to VRChat Names

For export-only naming, keep the working names and choose **Unity-Preset** in the export section instead. See [Export bone naming](08-vrchat.md#export-bone-naming).

1. Map the bones as described in Guide 5, Step 2.

2. In **Set Up Humanoid Bones**, select **Normalize Names**.

Every mapped bone receives VRChat's expected name.

**What you should be seeing:** Bone names such as `Hips`, `Spine`, `Chest` and `LeftUpperArm`.

---

### Step 3 — Manual Fixes (If Needed)

The Naming group in **VRChat Tools** also has batch tools for the bones that are left:

- **Find and Replace** — replace one piece of text with another in every bone name
- **Add Prefix** and **Add Suffix** — add text to the start or end of every bone name
- **Remove Prefix** and **Remove Suffix** — strip it again
- **Regex Replace** — the same, with a regular expression

**What This Unlocks:** Correct bone names let the humanoid mapping (Guide 5) work automatically. Without them, VRChat cannot tell how your character should move.

---

## Guide 5: Map Your Avatar to VRChat's Body System

> **Time:** About 10–15 minutes
> **Result:** Your avatar's skeleton connected to VRChat's humanoid movement system

**Before you begin — check these:**

- [ ] Your avatar's bones are named sensibly (see Guide 4 if not)
- [ ] The skeleton is selected
- [ ] You are in **Object Mode** (check the dropdown in the top-left of the viewport)

---

### Step 1 — Open Set Up Humanoid Bones

In the **CATS** tab, expand **Avatar Tools** → **Set Up Humanoid Bones**.

---

### Step 2 — Auto-Map

Click **Auto-Map All**. BoneCraft scans your skeleton and fills the body slots.

> A humanoid slot identifies a body part, such as Hips, Head or Left Hand. BoneCraft assigns bones to these slots. Saved humanoid mappings load correctly when you reopen a file.

**What you should be seeing:** Bone assignments and the proportion of required slots filled. There are 15 required slots: Hips, Spine, Head, both upper arms, lower arms, hands, upper legs, lower legs and feet. Optional slots include Chest, UpperChest and Neck.

---

### Step 3 — Check the Mapping

Click **Validate**. BoneCraft checks that every required slot has a bone and that the hierarchy makes sense.

---

### Step 4 — Fill Empty Slots by Hand

An empty slot shows "(click to map)".

1. Select the empty slot.

2. Select the correct bone.

3. Select **Validate** again.

4. Select **Normalize Names** to give mapped bones VRChat's names.

---

### Step 5 — Set Up Eye Tracking (Optional)

If your avatar has eye bones:

1. Open **CATS → CATS → Eye Tracking**.

2. Select **Auto-Detect** to search eye-bone names.

3. Check the **Left Eye** and **Right Eye** assignments.

4. If necessary, select the correct bones manually.

5. Set the rotation limits.

6. Select **Create Eye Tracking**.

[Guide 13, Phase 3](03-guides-b.md#phase-3--eye-tracking) explains the settings.

**What This Unlocks:** Humanoid mapping lets the avatar follow your movements in VRChat. IK (inverse kinematics) makes the in-game hands follow your controllers.

---

## Guide 6: Add Hair Physics

> **Time:** About 15–25 minutes
> **Result:** Your avatar's hair (and other soft parts) swinging naturally in VRChat

**Before you begin — check these:**

- [ ] Your avatar is open with the skeleton selected
- [ ] Set Up Humanoid Bones is done (Guide 5)

> PhysBone = VRChat's component that makes bones bounce and swing as if they had weight. BoneCraft sets them up on chains of bones: hair, ears, tails, skirts and accessories.

---

### Step 1 — Open Add Hair Physics

In the **CATS** tab, expand **Avatar Tools** → **Add Hair Physics**. It has four parts: Hair Chain Detection, Hair Chain Generation, PhysBone Configuration and Hair Physics Colliders.

---

### Step 2 — Find the Hair Chains

If your hair already has bones, select **Detect Hair Physics Chains**. BoneCraft searches for hair-like bone chains linked end to end from a root. The list shows each chain's root bone and length.

If your hair has no bones:

1. Select the hair meshes.

2. In Hair Chain Generation, select **Generate**.

3. Immediately set **Chain Density** to Low, Medium or High in **Adjust Last Operation**.

**Replace** asks for confirmation and currently creates new chains without removing earlier chains.

Before generating again:

1. Review the bone list.

2. If unwanted chains exist, remove them.

---

### Step 3 — Choose a PhysBone Preset

1. Select a bone in the chain.

2. Under PhysBone Configuration, select **Hair**, **Skirt** or **Tail**.

Skirt suits skirts and capes. Tail suits tails and ropes.

**What you should be seeing:** The chain's parameters: Pull, Spring, Stiffness, Gravity and Max Angle.

---

### Step 4 — Fine-Tune (Optional)

The panel displays the chain's values but cannot edit them. Higher Stiffness reduces bending. Higher Gravity pulls the chain down. A smaller Max Angle restricts its swing. To change values, select another preset. Alternatively, after importing the avatar, edit its PhysBone component in Unity.

---

### Step 5 — Add Colliders (Recommended)

Colliders are invisible shapes that prevent hair from passing through the head and body. In Hair Physics Colliders, select **Place Default Colliders**. This adds colliders to the head, shoulders and chest. **Add Collider** and **Remove Collider** add or remove one collider at a time.

**What This Unlocks:** Your avatar's hair now moves naturally in VRChat when you turn your head, jump or dance. The same steps work for tails, ears, skirts and dangling accessories.

---

## Guide 7: Attach Clothing That Moves With Your Body

> **Time:** About 20–30 minutes
> **Result:** A clothing item attached to your avatar's skeleton, moving with your body

**Before you begin — check these:**

- [ ] Your base avatar has a finished skeleton, and its body is weight painted
- [ ] The clothing item is in the same file (with its own armature if it came with one)
- [ ] The clothing roughly fits around your avatar's body

---

### Step 1 — Open Attach Clothing

See the [Clothing controls and selection order](08-vrchat.md#attach-clothing).

In the **CATS** tab, expand **VRChat Tools** and find its Clothing group. It has three parts: Bone Matching, Collision Detection and Clothing Merge.

---

### Step 2 — Match Bones

If the clothing has an armature:

1. Switch to Object Mode.

2. Select both the clothing armature and the avatar armature.

3. Select **Match Bones** to compare their bone names.

**What you should be seeing:** Reported HIGH, MEDIUM, LOW and UNMATCHED match counts. The panel does not display a list of bone pairs. For clothing without an armature, skip this step.

Before merging two armatures:

1. Select **Detect Collisions** to check for conflicting bone names.

2. Review the proposed renames.

3. Make the clothing armature active.

4. Select **Resolve Collisions** to apply the renames to that armature.

Detect Collisions checks names only. It does not check mesh intersections.

---

### Step 3 — Merge the Clothing

1. If the clothing has an armature, select that armature and its meshes.

2. If the clothing has no armature, select only its meshes.

3. Shift-click the avatar's armature last to make it active.

4. Select **Merge Clothing**.

With a clothing armature, BoneCraft moves the clothing onto the avatar skeleton and merges the bones. Without a clothing armature, it transfers the body's weights to the clothing meshes.

> Weights (weight painting) = numbers that tell each point of a mesh how much each bone moves it. If your left sleeve has weight on the left arm bone, moving that bone pulls the sleeve with it.

**What you should be seeing:** The clothing under your avatar's skeleton. Moving a bone moves both the body and the clothing.

---

### Step 4 — Check for Clipping

1. Pose the avatar.

2. Inspect places where the clothing passes through the body.

3. If clipping occurs, adjust the clothing fit or weights at those locations.

See the Weight Tools in [Rig Tools](05-rig-tools.md). **Detect Collisions** does not check physical clipping.

**What This Unlocks:** Clothing that moves naturally with your body. Repeat for each outfit piece.

Next: [Guides 8–13](03-guides-b.md)

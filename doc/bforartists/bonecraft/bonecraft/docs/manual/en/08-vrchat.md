# VRChat Tools

[← Contents](index.md)

## VRChat Tools

The VRChat tools are in the **CATS** tab's **Avatar Tools** section on the right sidebar. Press **N** to show the sidebar. Avatar Tools covers humanoid bones, hair physics and Viseme Library / Lip Sync. VRChat export is under CATS → Import / Export → Unity / VRChat. The separate **VRChat Tools** section below it groups Check Performance, Attach Clothing, Facial and VRChat Naming Extras. When Preferences → Tabs → Scene Properties → Show is on, this section also appears in the **Properties** editor's **Scene** tab. This switch does not hide the CATS viewport tab.

---

### Set Up Humanoid Bones

Maps your skeleton's bones to VRChat's humanoid slots and checks the mapping.

See [Guide 5: Map Your Avatar to VRChat's Body System](02-guides-a.md#guide-5-map-your-avatar-to-vrchats-body-system).

![Required humanoid slots before Auto-Map All. After mapping, review each slot. Fill any remaining gaps.](images/screenshots/bc18-humanoid.png){style="max-width:100%;max-height:155mm;width:auto;height:auto"}

*Native panel popover, BoneCraft 9.2.18. Required humanoid slots before Auto-Map All. After mapping, review each slot. Fill any remaining gaps.*

---

### Add Hair Physics

Sets up PhysBone chains on hair, ears, tails and accessories, with colliders.

See [Guide 6: Add Hair Physics](02-guides-a.md#guide-6-add-hair-physics).

![Hair Physics chains, generation actions, presets and collider controls. Review the detected chains before applying physics.](images/screenshots/bc19-hair.png){style="max-width:100%;max-height:155mm;width:auto;height:auto"}

*Native test-build popover, BoneCraft 9.2.19 candidate. Bforartists 5.2.3, Blender 5.4 Alpha. Hair Physics chains, generation actions, presets and collider controls. Review the detected chains before applying physics.*

---

### Attach Clothing

**Where to find it:** CATS tab → VRChat Tools → Clothing

Merges clothing onto your avatar's skeleton and transfers its weights.

See [Guide 7: Attach Clothing That Moves With Your Body](02-guides-a.md#guide-7-attach-clothing-that-moves-with-your-body).

![Clothing controls and the Pre-Merge selection order. Before merging clothing, match the bones. Check bone-name conflicts.](images/screenshots/bc21-clothing.png){style="max-width:100%;max-height:155mm;width:auto;height:auto"}

*Local preview, BoneCraft 9.2.19 candidate. Bforartists 5.2.3, Blender 5.4 Alpha. Clothing controls and the Pre-Merge selection order. Before merging clothing, match the bones. Check bone-name conflicts.*

---

### VRChat Naming Extras

**Where to find it:** CATS tab → VRChat Tools → Naming

**What it does:** Detects your skeleton's naming style and renames bones in bulk.

See [Guide 4: Fix Your Avatar's Bone Names](02-guides-a.md#guide-4-fix-your-avatars-bone-names).

**Batch tools:** **Find and Replace**, **Add Prefix**, **Remove Prefix**, **Add Suffix**, **Remove Suffix** and **Regex Replace**

![Naming detects Unity Humanoid with a confidence of 16/24 in this example. Review names before using the batch actions.](images/screenshots/bc21-naming.png){style="max-width:100%;max-height:155mm;width:auto;height:auto"}

*Local preview, BoneCraft 9.2.19 candidate. Bforartists 5.2.3, Blender 5.4 Alpha. Naming detects Unity Humanoid with a confidence of 16/24 in this example. Review names before using the batch actions.*

---

### VRChat Viseme Mapping

**Where to find it:** CATS → VRChat Tools → Facial. Face Tracking is in the same section.

**What it does:** Maps your mesh's shape keys to VRChat's 15 lip-sync visemes.

See [Guide 8: Set Up Lip Sync](03-guides-b.md#guide-8-set-up-lip-sync). To create visemes your avatar does not have yet, see [CATS Tools: Visemes](09-cats.md#visemes).

**VRChat's 15 viseme slots:** `sil`, `PP`, `FF`, `TH`, `DD`, `kk`, `CH`, `SS`, `nn`, `RR`, `aa`, `E`, `I`, `O`, `U`

![Viseme slots and Face Tracking before mapping. This example has unmapped visemes and 0 of 55 expressions mapped.](images/screenshots/bc21-facial.png){style="max-width:100%;max-height:175mm;width:auto;height:auto"}

*Local preview, BoneCraft 9.2.19 candidate. Bforartists 5.2.3, Blender 5.4 Alpha. Viseme slots and Face Tracking before mapping. This example has unmapped visemes and 0 of 55 expressions mapped.*

---

### Check Performance

**Where to find it:** CATS tab → VRChat Tools → Performance

**What it does:** Measures your avatar's VRChat performance rank and offers fixes.

See [Guide 9: Improve Your Avatar's Performance](03-guides-b.md#guide-9-improve-your-avatars-performance).

**Performance tiers (best to worst):** Excellent → Good → Medium → Poor → Very Poor

**Tools:**

- **Calculate Performance Rank** — the current rank, with a breakdown by polygons, skinned meshes, material slots, bones, PhysBones and contacts
- The optimizer offers **Remove Zero-Weight Bones**, **Merge Same-Material Meshes**, **Remove Unused Shape Keys** and **Remove Unused Vertex Groups**. **What-If Mode** shows what these fixes would change
- VRChat Decimation — reduces the polygon count by a ratio while protecting shape keys

For VRChat Decimation:

1. Select the avatar mesh.
2. Select **Preview**.
3. Select **Apply**.

![Performance metrics and What-If controls. Select an avatar mesh to use the mesh cleanup actions.](images/screenshots/bc21-vrchat-tools.png){style="max-width:100%;max-height:155mm;width:auto;height:auto"}

*Native panel popover, BoneCraft 9.2.18. Performance metrics and What-If controls. Select an avatar mesh to use the mesh cleanup actions.*

![Decimation settings before Preview or Apply. The example uses Ratio 0.50 and Shape Key Safety. What-If Mode is enabled for the cleanup actions below.](images/screenshots/bc21-decimation.png){style="max-width:100%;max-height:155mm;width:auto;height:auto"}

*Local preview, BoneCraft 9.2.19 candidate. Bforartists 5.2.3, Blender 5.4 Alpha. Decimation settings before Preview or Apply. The example uses Ratio 0.50 and Shape Key Safety. What-If Mode is enabled for the cleanup actions below.*

---

### Export to VRChat

**What it does:** Exports your finished avatar as an FBX for the VRChat SDK in Unity. Unless **Remove Shape Keys** is on, the export keeps shape keys (blend shapes).

**Settings:**

- **Folder** — where the export goes
- **Avatar** — the exported file name
- **Sidecar** — also writes a `.bfvrc` settings file for BoneCraft's Unity importer
- **Merge Meshes** — joins the meshes of the export copy into one
- **Separate Clothing** — keeps clothing as separate meshes
- **Remove Shape Keys** — applies the shape keys to the export copy's basis
- **Embed Textures** — packs the textures into the FBX, so Unity finds them
- **Helper Meshes** — includes hidden or helper meshes. For normal avatars, leave it off
- **Bone Names** — **Keep Original Names**, **Unity-Preset** or **Unreal-Preset**, applied to export copies

**Location:** CATS → Import / Export → Game Engine Export → Unity / VRChat.

Before export:

1. If required slots are missing, run **Auto-Map Humanoid** here.
2. Review the slots.

For a performance check before export, select **Check Performance Rank**. Before using a **Bone Names** preset, correct mapping or naming conflicts. The **Export bone naming** section below explains these conflicts. Before export, make linked objects local. To write the FBX, select **Export to VRChat (Unity)**.

**Normalize Names** renames the working rig. **Bone Names** presets rename export copies.

The Unity/VRChat exporter writes the rest pose without animation. The main Unity and Unreal export buttons accept Object, Pose and Edit Mode. They temporarily use Object Mode, then restore the previous mode and selection.

![Unity / VRChat settings before configuring the folder and humanoid mapping. This example shows 0 of 15 required slots mapped.](images/screenshots/bc31-unity-export.png){style="max-width:100%;max-height:155mm;width:auto;height:auto"}

*Local preview, BoneCraft 9.2.19 candidate. Bforartists 5.2.3, Blender 5.4 Alpha. Unity / VRChat settings before configuring the folder and humanoid mapping. This example shows 0 of 15 required slots mapped.*

---

### Cleanup

Mesh cleanup before export lives in the CATS tools: **Fix Model**, **Join Meshes** and **Apply All Transforms**. See [CATS Tools](09-cats.md).

---

## VRM Bridge

The VRM tools are in the **CATS** tab → **Import / Export** → **VRM / VRoid**. They need the VRM add-on. An inactive bridge offers **Auto-Install Latest from GitHub**, **Open Add-on Preferences**, **Website** and **Show Manual Instructions**.

For an offline package, use native Preferences. A legacy add-on ZIP uses **Add-ons → Install from Disk…**. A modern extension package uses the native Extensions installation menu.

1. Through the appropriate native menu, install the package.
2. Enable the dependency.
3. Confirm that the bridge reports **Active**.

The inactive hub card has no ZIP installation button.

![The example has neither format bridge enabled. Install the required bridge before its import and export controls appear.](images/screenshots/bc31-import-export.png){style="max-width:100%;max-height:155mm;width:auto;height:auto"}

*Local preview, BoneCraft 9.2.19 candidate. Bforartists 5.2.3, Blender 5.4 Alpha. The example has neither format bridge enabled. Install the required bridge before its import and export controls appear.*

---

### VRM and VRoid Import

**What it does:** Imports `.vrm` avatars (VRoid Studio, Virtual Cast and other VRM avatars) with their materials, skeleton and shape keys.

- **Import VRM…** — a `.vrm` file
- **Import VRoid (.vroid / .zip)…** — a VRoid Hub download (`.zip`). A VRoid Studio project (`.vroid`) shows a card that explains how to export it to VRM first.

---

### VRM Export

**What it does:** Exports your rigged character to VRM, or to a target app's format.

**Settings:**

- **Folder** and **File** — destination and file name. The extension follows the target
- **Target** — VRM 1.0, VRM 0.x, VRChat FBX, VSeeFace, Warudo or Resonite
- **Scope** — the active armature, or every armature with VRM data
- Skip lint — exports without the target check. Only use this option if you understand the reported risk

Click **Export…**.

---

### VRM Lint

**What it does:** Checks the armature against the selected target before export. Checks cover humanoid mapping, VRM metadata, target visemes and the target app's expectations.

**Lint Now** runs the check without changing anything. Unless you skip lint, errors block export. Warnings identify content that the target app may import with reduced performance.

If lint reports missing humanoid bones that exist, click **Fix Humanoid Map**. BoneCraft detects the humanoid slots again and saves the mapping. It does not rename bones.

**Also here:** **Convert SpringBones → PhysBones** (VRoid hair physics to VRChat) and **Map VRoid Visemes**.

---

## MMD Bridge

The MMD tools are in **CATS → Import / Export → MMD / PMX**. They need **mmd_tools**, installed and enabled. BoneCraft recognizes legacy packages and modern Blender Extensions.

An inactive bridge offers **Auto-Install Latest from GitHub**, **Open Add-on Preferences**, **Website** and **Show Manual Instructions**. The standalone bridge content also offers **Install from .zip on Disk...** when shown. See [Guide 3](02-guides-a.md#step-1--install-mmd_tools) for installation and local extension repository checks.

---

### MMD Import

- **Import PMX / PMD...** — MMD models
- **Import VMD Motion...** — MMD animations
- **Import VPD Pose...** — MMD poses

Confirm that the import finishes successfully. A cancelled PMX import or installation error leaves the task incomplete. Imported models can need material and bone-mapping checks before conversion.

---

### MMD Export

**Settings:** **Folder** sets the destination. Each format has file-name and scope settings:

- **PMX File** and **PMX Scope**.
- **VMD File** and **VMD Scope**.
- **VPD File** and **VPD Scope**.

Each scope selects the active model or every MMD model in the scene.

**Buttons:** **Export PMX...**, **Export VMD Motion...** and **Export VPD Pose...**

**Also here:** **Convert Bone Names -> Unity** and **Convert Physics -> PhysBones**.

---

## Game Engine Export

**Game Engine Export** is the inline area under **CATS → Import / Export**. It contains **Unity / VRChat** and **Unreal Engine 5**. The separate **Game Export** child panel offers validated profile export.

### Unreal Engine 5

With **Bake Anim** enabled, the exporter bakes the active action. A separate NLA strip is not required. It does not export every unrelated action.

Before using a **Bone Names** preset, correct mapping or naming conflicts. The **Export bone naming** section below explains these conflicts. Before export, make linked objects local.

1. Select the armature and its meshes.
2. Open **CATS → Import / Export → Game Engine Export → Unreal Engine 5**.
3. Set **Folder**.
4. Set **File** to the FBX name.
5. Review **Bone Names** and its preview.
6. If the export needs the active animation, enable **Bake Anim**.
7. Click **Export to Unreal (FBX)**.

**Selected Only** starts enabled. Include the armature with its meshes. **Unit Scale** starts enabled, **Leaf Bones** starts disabled, and **Embed Textures** starts enabled. The panel abbreviates **Bake Animation** to **Bake Anim**.

**Import from Unreal (FBX)** opens the import file browser.

![Unreal Engine 5 settings before choosing an output folder. Review Bone Names, Selected Only and Bake Anim before exporting.](images/screenshots/bc31-unreal-export.png){style="max-width:100%;max-height:155mm;width:auto;height:auto"}

*Local preview, BoneCraft 9.2.19 candidate. Bforartists 5.2.3, Blender 5.4 Alpha. Unreal Engine 5 settings before choosing an output folder. Review Bone Names, Selected Only and Bake Anim before exporting.*

### Export bone naming

Both engine sections offer the same **Bone Names** choices:

| Choice | Export result |
| --- | --- |
| Keep Original Names | Retains the existing bone names. This is the default. |
| Unity-Preset | Uses recognized Unity Humanoid names, including `Hips`, `LeftUpperArm` and `LeftIndexProximal`. |
| Unreal-Preset | Uses recognized Unreal humanoid names, including `pelvis`, `spine_01`, `upperarm_l`, `index_01_l` and `ball_l`. |

Select an armature to see the preview. It shows **Recognized / renamed** counts and up to three proposed changes. Unrecognized bones keep their names.

Saved humanoid mappings take precedence over name detection. Recognized optional chest, neck, shoulder, eye, jaw, finger and toe bones also participate. A separate recognized `Root` becomes `root` with **Unreal-Preset**.

Conflicting target names, ambiguous bones and reused humanoid slots block renaming. Correct the mapping or naming conflict before exporting. BoneCraft does not add `.001` suffixes to resolve these conflicts.

Before export, make linked objects local. Presets rename temporary export copies. The working rig keeps its bone names. Exported vertex groups, animation channels and Unity sidecar bone references follow the selected names. Cleanup removes temporary data on success or failure.

These presets change names only. They keep the hierarchy, bone orientations and rest pose. They do not add missing joints or construct a complete Manny/Quinn skeleton. Unity Avatar mapping or Unreal retargeting can still be necessary.

### Validated profile export

**What it does:** Exports with a validated profile: Unreal humanoid or universal, Unity humanoid, Godot humanoid, generic FBX or GLB. The findings list shows available fixes. Fixes require your explicit action.

Use Object Mode for this profile workflow. The Object/Pose/Edit restoration guarantee applies to the two main engine export buttons.

Before using a **Bone Names** preset, correct mapping or naming conflicts. The **Export bone naming** section above explains these conflicts. Before export, make linked objects local.

**File-browser settings:** **Profile**, **Animation**, **Bone Names**, **Root Motion**, **Interpolation** and **T-Pose**. **Bone Names** initially follows the Unreal section's selection. The export-format profile remains a separate choice.

For a naming preset, select **Active Action** or **No Animation**. **All Actions** requires **Keep Original Names** because it can include actions from other rigs.

The default **T-Pose** follows the profile. Unity humanoid and VRChat profiles use a T-pose. T-pose export includes the rest pose without animation. If you need the modelled rest pose, select **Export as modelled**.

1. Select the armature and its meshes.
2. Open **CATS → Import / Export → Game Export**.
3. Click **Check for Export**.
4. Review the findings and any explicit fixes.
5. Click **Export (Profile)**.
6. Select the settings in the file browser.
7. Select the output file.
8. Confirm the export.

![Profile export options before confirmation. This example uses Generic FBX, Active Action and Keep Original Names.](images/screenshots/bc36-profile-options.png){style="max-width:100%;max-height:155mm;width:auto;height:auto"}

*Local preview, BoneCraft 9.2.19 candidate. Bforartists 5.2.3, Blender 5.4 Alpha. Profile export options before confirmation. This example uses Generic FBX, Active Action and Keep Original Names.*

**Buttons:**

- **Check for Export** — checks the rig against the profile and lists findings
- **Apply Transforms (Fix)** — one of the explicit fixes the check can offer
- **Export (Profile)** — exports with the profile

**Where to find it:** **CATS** tab → **Import / Export** → **Game Export**

See the [standalone export naming guide](https://github.com/Axleonex/B4Artists_Toolkit/blob/main/bonecraft/docs/export-bone-naming.md) for additional naming details and historical host verification.

![Check for Export, explicit fixes and Export (Profile). The example has no profile check results yet.](images/screenshots/bc36-profile-export.png){style="max-width:100%;max-height:155mm;width:auto;height:auto"}

*Native panel popover, BoneCraft 9.2.18. Check for Export, explicit fixes and Export (Profile). The example has no profile check results yet.*

---

## Task Board

**What it does:** Summarizes the current rig with a health score, quick wins and tasks grouped by category. Tasks include missing humanoid bones, unresolved names, missing visemes and rig validator warnings. **Quick Wins** shows up to three recommended tasks. **Remaining Tasks** contains only the other tasks. **Open Health Check** runs validation and opens its results. **Refresh Task Board** checks again.

**Where to find it:** **BoneCraft** tab → **Overview** → **Task Board**

![The Task Board lists health findings and quick actions for the active example rig.](images/screenshots/bc17-taskboard.png){style="max-width:100%;max-height:155mm;width:auto;height:auto"}

*Native panel popover, BoneCraft 9.2.18. The Task Board lists health findings and quick actions for the active example rig.*

---

### Bone Inspector

**What it does:** Shows the active pose bone's rest dimensions, parent, constraints, custom data, drivers and skin weights.

The information is read-only. With an active bone in Pose Mode, open this panel. To copy the bone's name, select **Copy Name** in the header.

**Where to find it:** **BoneCraft** tab → **Review** → **Bone Inspector**

![Bone Inspector shows rest-bone details, constraints, custom data, drivers and skin weights. The header includes Copy Name.](images/screenshots/bc17-inspector.png){style="max-width:100%;max-height:155mm;width:auto;height:auto"}

*Native test-build popover, BoneCraft 9.2.19 candidate. Bforartists 5.2.3, Blender 5.4 Alpha. Bone Inspector shows rest-bone details, constraints, custom data, drivers and skin weights. The header includes Copy Name.*

Next: [CATS Tools](09-cats.md)

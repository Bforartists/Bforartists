# Getting Started

[← Contents](index.md)

## What is BoneCraft?

BoneCraft is an add-on for Bforartists. It rigs characters and props and prepares 3D avatars for VRChat, VRoid / VRM and MMD. Its panels automate rig creation, weight painting, bone naming, lip sync, eye tracking and export.

**What BoneCraft cannot do:**

- It cannot model or sculpt your avatar's body shape
- It cannot create textures or materials from scratch
- It cannot upload to VRChat directly (you still need the VRChat Creator Companion / SDK)

---

## BoneCraft and BoneForge

BoneCraft runs only in Bforartists, a Blender fork. BoneForge is a separate add-on for standard Blender with fewer tools. Install only one of these add-ons. In standard Blender, BoneCraft shows a notice and a button to get Bforartists. It does not load its tools.

BoneForge 9.0.0 and later target standard Blender. BoneCraft is the separate Bforartists add-on. Both have Auto-Rig Wizard, Quick Rig, Mannequin and the shared CATS/Material Atlas tools. BoneCraft also has Mechanisms, the Control Picker and its production control-rig, joint-detection and profile-export tools. Similar placement does not add those tools to BoneForge.

## Supplied build quick start

The original supplied Bforartists build includes BoneCraft 9.2.18. The new local preview includes the 9.2.19 candidate. Both enable BoneCraft through factory settings. You do not install a ZIP or enable BoneCraft manually in these builds.

1. Open the supplied Bforartists build.
2. Press **T** to show the left Tool Shelf.
3. Select **BoneCraft** or **Rig Builder**.
4. Press **N** to show the right sidebar.
5. Select **CATS** for avatar tools and **Import / Export**.

Use the same interface paths and settings in this manual. Optional tool packages and dependencies retain their requirements. Rigify starters and VRM/MMD bridges still need their listed dependencies.

These instructions describe the local contribution preview. The official Bforartists 5.2.3 package does not include this bundle. See the [contribution proposal](https://github.com/Bforartists/Bforartists/pull/7067) for its review history.

## Installing BoneCraft

Use this section for the standalone Toolkit ZIP. Supplied-build users can start with the existing tabs above.

The linked public ZIP is 9.2.18. Use the local preview for the 9.2.19 candidate fixes until publication.

**What you need:**

- Bforartists (BoneCraft is tested on Bforartists 5.2)
- The standalone [BoneCraft-BFA-9.2.18.zip](https://github.com/Axleonex/B4Artists_Toolkit/releases/download/bonecraft-v9.2.18/BoneCraft-BFA-9.2.18.zip) file

**Steps:**

For an update:

1. Save your work.

2. Disable the older standalone BoneCraft add-on.

3. Remove the older standalone BoneCraft add-on.

4. Restart Bforartists before installing the new ZIP.

For a first installation, start here:

1. Open Bforartists.
2. Open **Edit** → **Preferences** → **Add-ons**.
3. Select **Install from Disk…**.

4. Select the BoneCraft `.zip` file.

5. Enable the checkbox next to BoneCraft.
6. Confirm that Preferences reports **9.2.18** for the linked published ZIP.

7. Expand BoneCraft's entry to see **Language**, **Tabs**, **Shelf Width**, **Show Helpers** and **Tools**.

These steps install the standalone Toolkit ZIP. Use the supplied-build quick start when your provided build already includes BoneCraft. Avoid enabling duplicate standalone and built-in copies.

**You should see:** the BoneCraft and Rig Builder tabs on the left Tool Shelf (press **T**) and the CATS tab on the right sidebar (press **N**).

## Where things are

Each tab contains a workspace group. Setup Rigging, Skin, Review, Avatar Tools and Facial are expandable sections inside tabs. The paths below use English UI labels. Translated labels depend on the Language preference.

| Tab | Default location | Sections |
| --- | --- | --- |
| Rig Builder | Left Tool Shelf (T) | Auto-Rig Wizard, Quick Rig - premade armatures, Mannequin |
| BoneCraft | Left Tool Shelf (T) | Overview, Setup Rigging, Skin, Mechanisms, Review |
| CATS | Right sidebar (N) | CATS, Avatar Tools, VRChat Tools, Import / Export |

![BoneCraft is selected on the left Tool Shelf and CATS on the right sidebar. Press T or N to show those sides.](images/screenshots/bc02-tab-placement.png){style="max-width:100%;max-height:155mm;width:auto;height:auto"}

*Local preview, BoneCraft 9.2.19 candidate. Bforartists 5.2.3, Blender 5.4 Alpha. BoneCraft is selected on the left Tool Shelf and CATS on the right sidebar. Press T or N to show those sides.*

| Tool | Open this path |
| --- | --- |
| Bone Merge | BoneCraft → Setup Rigging → Bone Merge |
| Delta Mush / Proximity Wrap | BoneCraft → Skin → Delta Mush / Proximity Wrap |
| Viseme Library / Lip Sync | CATS → Avatar Tools → Viseme Library → Lip Sync |
| VRChat Viseme Mapping / Face Tracking | CATS → VRChat Tools → Facial |
| Humanoid / Hair | CATS → Avatar Tools → Set Up Humanoid Bones / Add Hair Physics |
| VRChat export | CATS → Import / Export → Game Engine Export → Unity / VRChat |
| Unreal export and Bone Names | CATS → Import / Export → Game Engine Export → Unreal Engine 5 |
| Validated profile export | CATS → Import / Export → Game Export → Export (Profile) |
| Material Atlas | CATS → CATS → Material Atlas → Analyze Materials / Refresh Analysis → Bake Checked Sources |
| VRM / MMD / I/O Hub | CATS → Import / Export → VRM / VRoid, MMD / PMX, Game Engine Export |
| Performance / Clothing / Naming | CATS → VRChat Tools → Check Performance / Attach Clothing / VRChat Naming Extras |

For rig and viseme-library controls, select an armature. For Delta Mush and Proximity Wrap, select a mesh in Object Mode. Lip Sync requires an armature in Pose Mode. Expand the section triangle to show its buttons. Options folds contain optional settings. If a tool runs immediately, adjust it in Adjust Last Operation before another operation.

The three facial workflows have different purposes. CATS viseme generation creates mouth shape keys. Viseme Library / Lip Sync stores poses and keys animation. Facial maps existing shape keys for VRChat or configures face tracking.

UV packing controls are under **CATS → CATS → Material Atlas → Advanced Options → UV Packing**. Older instructions call this fold Override Inherited Settings. BoneCraft supplies shared atlas UV helpers, rather than the full standalone UVToolkit add-on.

**Starter Rigs:**

1. Enable **Starter Rigs** in the bottom asset shelf's catalog menu.

2. If necessary, select **All** libraries.

Version 9.2.5 removed the old top-left Starter Rigs controls. **Add → Armature → Starter Rig Catalog** provides fitting and generation with dependency checks.

**Move a tab:**

1. Open **Edit** → **Preferences** → **Add-ons** → BoneCraft → **Tabs**.

2. Select **Left** or **Right** for the tab.

Each tab also has a show switch. Changes apply immediately. When a tab is hidden, its Left and Right buttons turn grey but still work.

**Properties editor:** **Scene Properties**, under Preferences → Tabs, starts enabled. It shows Rig Builder, Mechanisms, CATS, Avatar Tools, VRChat Tools and Import / Export in the Properties editor's Scene tab.

Select **Show** to hide or show these sections. Blue means the sections are visible. This switch does not change the viewport tabs or the Armature data tab.

With an armature selected, BoneCraft's armature tools also appear in the Armature data tab. These tools do not follow the visibility switches. Rig Builder, Mechanisms and the CATS sections use the Scene tab.

To remove a tool from all locations, disable its package in **Tools**. Alternatively, disable the add-on.

**Shelf Width:** Widen Narrow Shelves starts enabled. It widens shelves that contain BoneCraft tabs once when their widths are below the Left or Right minimum. At 1× UI scale, the defaults are 240 pixels for Left and 260 pixels for Right. If you then drag a shelf narrower, it keeps your chosen width. To control widths manually, disable the switch. Its width fields become inactive.

![Tabs place BoneCraft and Rig Builder on the left and CATS on the right. Shelf Width and Show Helpers are below.](images/screenshots/bc01-layout-settings.png){style="max-width:100%;max-height:155mm;width:auto;height:auto"}

*Local preview, BoneCraft 9.2.19 candidate. Bforartists 5.2.3, Blender 5.4 Alpha. Tabs place BoneCraft and Rig Builder on the left and CATS on the right. Shelf Width and Show Helpers are below.*

**Menus and built-in Tool Shelf tabs:** you can also reach tools from the 3D Viewport's header menus:

| Location | Tools |
| --- | --- |
| Add → Armature | Quick Rig, Auto-Rig Wizard, Mannequin for Active Rig |
| Pose → BoneCraft (Pose Mode) | Pose tools, the picker, bone collections, rig setup and checks |
| Weights → BoneCraft (Weight Paint mode) | Flood fill, mirror and normalize weights |
| Object → Mechanisms (Object Mode) | Add parts, joints and links; test motion |
| Tool Shelf → Pose or Weights → BoneCraft | Buttons for common pose or weight operations |

The Pose and Weights shelf buttons show text in a wide shelf. A narrow shelf shows an icon grid. Hover over an icon to read its tooltip. These locations use the same tools as BoneCraft's tabs. Only enabled tool packages are available.

**Viewport tools:** Place Rig Markers places the Auto-Rig Wizard's next marker when you click the mesh. Build Mechanism starts a guided joint or link when you click a part. See [Rig Builder](06-rig-builder.md#auto-rig-wizard) and [Mechanisms](07-mechanisms.md#joints-and-links-one-example-each) for setup and controls.

**Run first, adjust afterwards:** Quick Rig, Fit Dropped Rig, Weight Mirror, Weight Transfer, Flood to Custom, Ribbon, Spline IK and Delta Mush run immediately.

1. Select the tool.

2. Immediately adjust its options in the viewport's Adjust Last Operation panel.

3. Complete the adjustments before another operation.

Other panels contain optional settings in a fold below the action buttons. To use those settings, expand the fold. If a panel needs a different selection, it can remain visible and explain what to select.

**Show Helpers:** BoneCraft explains sections with short "what / when" lines and "How this works" notes. To hide these notes, disable **Show Helpers** in the add-on's preferences. In Avatar Tools, **Compact Mode** controls the same switch.

**Language:** the **Language** setting in the add-on's preferences changes BoneCraft's own panels to English, 日本語, 한국어, 中文, Français, Português or Español.

![The local preview reports BoneCraft 9.2.19 and English as its Language.](images/screenshots/bc01-preferences.png){style="max-width:100%;max-height:155mm;width:auto;height:auto"}

*Local preview, BoneCraft 9.2.19 candidate. Bforartists 5.2.3, Blender 5.4 Alpha. The local preview reports BoneCraft 9.2.19 and English as its Language.*

**Review cleanup first:**

1. Inspect Fix Model's options.

2. Select the operations your avatar needs.

3. Save a file checkpoint before changes.

4. After the operation, inspect the result.

Pipeline Status and the Operation Ledger record progress. See [The CATS Pipeline](04-cats-pipeline.md).

**Quick panel:** press **Ctrl+Shift+R** in the 3D Viewport to open BoneCraft's rig panel as a pop-up under the cursor.

---

## Where Should I Start?

Select the guide for your task:

> **Rig a new FBX, OBJ or Blender model for VRChat.**
> → Go to [Guide 1: Get Your First Avatar Into VRChat](02-guides-a.md#guide-1-get-your-first-avatar-into-vrchat)

> **Prepare a VRM avatar exported from VRoid Studio.**
> → Go to [Guide 2: Bring a VRoid Avatar into VRChat](02-guides-a.md#guide-2-bring-a-vroid-avatar-into-vrchat)

> **Prepare an MMD model (PMX file) for VRChat.**
> → Go to [Guide 3: Bring an MMD Avatar into VRChat](02-guides-a.md#guide-3-bring-an-mmd-avatar-into-vrchat)

> **Correct bone names that prevent a rigged avatar from uploading.**
> → Go to [Guide 4: Fix Your Avatar's Bone Names](02-guides-a.md#guide-4-fix-your-avatars-bone-names)

> **Prepare a rigged avatar's lip sync, eye tracking and mesh for VRChat.**
> → Go to [Guide 13: Get Your Avatar VRChat-Ready with CATS](03-guides-b.md#guide-13-get-your-avatar-vrchat-ready-with-cats)

> **Find a solution to a specific problem.**
> → Go to the [Quick-Fix Index](10-reference.md#quick-fix-index)

Next: [Guides 1–7](02-guides-a.md)

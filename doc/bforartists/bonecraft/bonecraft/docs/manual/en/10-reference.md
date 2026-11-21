# Quick Fixes and Glossary

[← Contents](index.md)

## Quick-Fix Index

Use this index to find guidance for a problem.

| Problem | Where to look |
|---|---|
| Upload fails — bones not recognized | [Guide 4](02-guides-a.md#guide-4-fix-your-avatars-bone-names) + [VRChat Naming Extras](08-vrchat.md#vrchat-naming-extras) |
| Avatar in T-pose / doesn't track movement | [Guide 5](02-guides-a.md#guide-5-map-your-avatar-to-vrchats-body-system) + [Set Up Humanoid Bones](08-vrchat.md#set-up-humanoid-bones) |
| Mesh deforming weirdly / skin stretching | [Weight Transfer](05-rig-tools.md#weight-transfer) + [Weight Mirror](05-rig-tools.md#weight-mirror), or recalculate with [Automatic Bone Weight Recalculation](05-rig-tools.md#automatic-bone-weight-recalculation) |
| One side of the body has different weights | [Weight Mirror](05-rig-tools.md#weight-mirror) |
| Hair clips through the head | [Guide 6, Step 5](02-guides-a.md#step-5--add-colliders-recommended) — add colliders |
| Hair physics not moving | [Guide 6](02-guides-a.md#guide-6-add-hair-physics) — check chain detection and the PhysBone preset |
| Clothing clips through the body | [Guide 7](02-guides-a.md#guide-7-attach-clothing-that-moves-with-your-body): <ol><li>Inspect the posed mesh.</li><li>If clipping occurs, adjust fit or weights.</li></ol> **Detect Collisions** checks bone names only. |
| Lip sync not working | [Guide 8](03-guides-b.md#guide-8-set-up-lip-sync) + [VRChat Viseme Mapping](08-vrchat.md#vrchat-viseme-mapping) |
| Avatar is Very Poor performance | [Guide 9](03-guides-b.md#guide-9-improve-your-avatars-performance) + [Check Performance](08-vrchat.md#check-performance) |
| VRM import fails | [Guide 2, Step 1](02-guides-a.md#step-1--install-the-vrm-add-on) — install the VRM add-on |
| MMD import fails | [Guide 3, Step 1](02-guides-a.md#step-1--install-mmd_tools) — install mmd_tools |
| MMD is installed but its bridge is inactive | Enable mmd_tools through **Open Add-on Preferences**. Review the installation message in [Guide 3](02-guides-a.md#step-1--install-mmd_tools). |
| Atlas selection changes after refreshing | **Refresh Analysis** rebuilds choices. <ol><li>Review the sources.</li><li>Select Bake Checked Sources.</li></ol> See [Material Atlas Combiner](09-cats.md#material-atlas-combiner). |
| Select All leaves a texture unchecked | Missing textures stay excluded. Bulk selection changes only its list in the active group — [source selection](09-cats.md#analyze-and-choose-sources) |
| Atlas reports a changed source | <ol><li>Refresh the analysis.</li><li>Review the sources again.</li></ol> Preflight rejects stale analyzed sources before backup creation. |
| Atlas has no Revert option | **Preserve Backup Duplicate** was disabled, or Accept deleted the backup. Use your saved file checkpoint. |
| Metallic or ORM atlas bake is blocked | Leave **Metallic** and **Pack ORM Channels** disabled. These passes remain blocked in 9.2.18. |
| Atlas texture looks scrambled in the engine | Check UV0. **Keep Source UV Maps** can leave `atlas_uv` on UV1 — [UV settings](09-cats.md#advanced-options) |
| Export fails from Pose or Edit Mode | Use the current main Unity or Unreal button. It restores mode and selection. Use Object Mode for **Export (Profile)**. |
| Export naming reports a conflict | Correct the target name or humanoid mapping — [Export bone naming](08-vrchat.md#export-bone-naming) |
| All Actions is blocked with a naming preset | Select **Active Action**, **No Animation** or **Keep Original Names** — [Validated profile export](08-vrchat.md#validated-profile-export). |
| Older mechanism forms need a current version | 9.2.18 reads and applies earlier forms without resaving them — [Forms](07-mechanisms.md#forms) |
| Rig validator shows errors | [Rig Validator](05-rig-tools.md#rig-validator): <ol><li>Run validation.</li><li>Follow the messages.</li></ol> |
| Bones vanished / can't see any bones | [Bone Collections](05-rig-tools.md#bone-collections) → **Show All Collections** |
| Can't find BoneCraft's panels | BoneCraft and Rig Builder use the left Tool Shelf (**T**). CATS uses the right sidebar (**N**). See [Where things are](01-start.md#where-things-are). |
| I want a complete Mechanisms example | [Tutorial: Crescent Rose](12-crescent-rose.md) — 8 preparation steps and 30 Mechanisms steps with screenshots, and the finished file in `examples/crescent-rose/` |
| A tab is on the wrong side | Preferences → Add-ons → BoneCraft → Tabs → Left or Right |
| BoneCraft's sections are missing from Properties → Scene | Preferences → Add-ons → BoneCraft → Tabs → Scene Properties → Show. Blue means enabled. Also check the tool packages in Tools. |
| I want to hide BoneCraft in Properties → Scene | Disable Scene Properties → Show in Preferences → Tabs. Viewport tabs and the Armature data tab remain unchanged. |
| A tool runs before I can choose its options | In 9.1, adjust its options immediately afterwards in the viewport's Adjust Last Operation panel, before running another operation |
| Place Rig Markers does not place a marker | <ol><li>Start the Auto-Rig Wizard.</li><li>Advance to a marker step.</li><li>Switch to Object Mode.</li><li>Click the wizard's selected mesh.</li></ol> See [Rig Builder](06-rig-builder.md#auto-rig-wizard). |
| Build Mechanism does not know which parts to use | <ol><li>Use Add Parts from Selection first.</li><li>Select the mechanism rig or one of its parts.</li><li>Select the type in the tool header.</li><li>Click the first part.</li></ol> See [Mechanisms](07-mechanisms.md#joints-and-links-one-example-each). |
| Export blocked: humanoid bones reported missing although they exist | If a required bone does not exist, the rig needs it first. If the required bones exist: <ol><li>Run Auto-Map All.</li><li>Run Fix Humanoid Map under lint in VRM / VRoid.</li></ol> See [Guide 5](02-guides-a.md#guide-5-map-your-avatar-to-vrchats-body-system). |
| Exported FBX shows giant helper shapes or tubes | If you do not need control or custom-shape meshes, keep **Helper Meshes** disabled. |
| Unity or Unreal imports grey materials | <ol><li>Export with Embed Textures enabled.</li><li>Use Unity's material import/extract options or Unreal's FBX material import.</li></ol> |
| Weights are all on the wrong bones | Re-run the wizard's Generate Rig, use [Weight Transfer](05-rig-tools.md#weight-transfer), or **Smart Automatic Weights** in the CATS tab |
| Two rigs need to be one | [Guide 11: Merge Two Rigs Together](03-guides-b.md#guide-11-merge-two-rigs-together) |
| Corrective shape not switching on | Check the bone axis and angle in [Corrective Shape Keys](05-rig-tools.md#corrective-shape-keys) |
| Animation looks wrong on a different rig | [Retarget](05-rig-tools.md#retarget) — check the bone mapping |
| A CATS tool warns "Run Fix Model first" | <ol><li>Review the cleanup options.</li><li>Decide whether the avatar needs them.</li></ol> The warning does not lock the tools. See [The CATS Pipeline](04-cats-pipeline.md). |
| Mouth tears apart or splits when speaking | Inspect the source mouth keys, mesh topology and modifiers — [CATS: Visemes](09-cats.md#visemes) |
| Avatar's eyes stuck looking down in VRChat | <ol><li>Check left/right bone assignments, orientation and constraints.</li><li>Inspect the exported avatar.</li></ol> See [CATS: Eye Tracking](09-cats.md#eye-tracking). |
| Shape key makes the mesh explode when triggered | <ol><li>Test the key alone.</li><li>Inspect topology, source key values and modifiers.</li></ol> BoneCraft captures a key mix, not bone deformation. See [CATS: Pose & Shape Keys](09-cats.md#pose--shape-keys). |
| Avatar spawns at the wrong size in VRChat | Check mesh transforms, armature transforms and export/import scale settings. If restoration is necessary, use Undo or a saved checkpoint. See [Apply All Transforms](09-cats.md#apply-all-transforms). |
| Bone names are Japanese / Chinese / Korean | [CATS: Translate Bone Names](09-cats.md#translate-bone-names) |
| Avatar has no lip sync and no mouth shape keys | [CATS: Visemes](09-cats.md#visemes): Create the base mouth shapes first. CATS generates 15 visemes from three source assignments: A, O and CH. |
| A mechanism shows "changed by hand" | [Mechanisms](07-mechanisms.md) — use **Keep mine** or **Restore** |

## Glossary

**Adjust Last Operation:** The viewport panel for changing the last operation's options. Many BoneCraft 9.1 tools run first and show their options here. Adjust these options before another operation.

**Armature:** Bforartists' word for a skeleton: a set of bones that can be posed and animated.

**Blend shape:** See Shape key.

**Bone:** One segment of a skeleton. Bones form a hierarchy (parent → child) in which child bones follow their parents.

**Bone collection:** A named group of bones. You can show or hide a whole collection at once.

**Bone Names:** The export naming choice. Keep Original Names retains names. Unity-Preset and Unreal-Preset rename recognized bones on export copies.

**Bake Checked Sources:** The atlas action that bakes the reviewed group and source choices without automatically rebuilding analysis.

**CATS:** The CATS tools: model preparation for VRChat with a guided pipeline (cleanup, visemes, eye tracking, transforms). They are in the CATS tab.

**CATS pipeline:** The six-phase order of the CATS tools: Fix Model → Material Atlas → Visemes → Eye Tracking → Pose to Shape → Apply Transforms. Tools warn when an earlier phase they depend on is not done.

**Corrective shape key:** A shape key that switches on when a bone reaches an angle, to fix the mesh at extreme poses.

**Deform bone:** A bone that moves the mesh. Some bones are controls only and do not deform the mesh.

**Eye tracking:** The CATS tool that sets up the eye bones (`LeftEye`, `RightEye`) and the rotation constraints VRChat uses to move the eyes.

**FBT (Full Body Tracking):** A VRChat feature that tracks your whole body, including hips and feet, with extra hardware such as Vive Trackers. Fix FBT adjusts the root bone for this feature.

**FBX:** A file format that carries 3D models, skeletons and animation between programs. The standard format for VRChat.

**Fix Model:** Selectable CATS cleanup operations for duplicate vertices, loose geometry, normals and other data.

1. Review the options.

2. Run only the operations your avatar needs.

**FK (Forward Kinematics):** Posing by rotating each bone of a chain in turn: shoulder, then elbow, then wrist. Natural for broad body poses.

**IK (Inverse Kinematics):** Posing by placing a chain's endpoint, such as a hand or foot. The intermediate bones follow. This method suits precise hand and foot placement.

**Humanoid:** VRChat's avatar system that maps bones to standard body slots, so every avatar uses the same movement controls.

**Mechanism:** A prop or machine rig built from ordinary bones and constraints. It can be a joint (Hinge, Slide, Telescope) or a link (Piston, Gear Link, Follow). See [Mechanisms](07-mechanisms.md).

**Mesh:** The 3D surface that makes up your avatar's visible body.

**MMD (MikuMikuDance):** Free 3D animation software popular in Japan and the anime community. Uses `.pmx` model files and `.vmd` animation files.

**Morph target:** See Shape key.

**Operation Ledger:** The CATS list of every operation you ran, with its time and outcome.

**PhysBone:** VRChat's component that makes bones swing, bounce and collide. Used for hair, tails and dangling accessories.

**Pipeline Status:** The CATS list of the six phases, with a checkmark for each phase that is done.

**PMX:** MikuMikuDance's main 3D model format.

**Pose Mode:** The mode for posing and animating bones.

1. Select the armature.

2. Press Ctrl+Tab.

Alternatively, select Pose Mode in the viewport's top-left mode dropdown.

**Rig / rigging:** Building a skeleton inside a 3D model and connecting the mesh to it so it can be posed and animated.

**Shape key:** A saved version of a mesh in a deformed position. Shape keys blend at different strengths. They drive facial expressions, lip sync and body morphs.

**SDK (Software Development Kit):** For VRChat, the VRChat Creator Companion and its Unity tools for uploading avatars.

**Spline IK:** A chain of bones that follows a curve. Used for tails, tentacles, long hair and spines.

**T-pose:** A reference pose: standing upright with the arms out to the sides.

**Tool Shelf:** The left panel of the 3D Viewport (**T**). BoneCraft and Rig Builder use this panel by default.

**Vertex:** A single point in 3D space. Meshes are made of many vertices joined by edges and faces.

**Vertex group:** A named set of vertices that defines which vertices a bone moves.

**Viseme:** A mouth shape for a speech sound. VRChat uses 15 visemes for lip sync.

**Weight / weight painting:** Values from 0.0 to 1.0 that say how strongly each bone moves each vertex. Weight painting is the visual way to adjust them.

**Wizard:** The Rig Builder's Auto-Rig Wizard: places markers on your mesh and builds the rig from them.

**Zero-weight bone:** A bone that moves no vertex. It reduces performance without changing the avatar's appearance. Fix Model and the performance optimizer remove these bones.

Next: [What's New](11-whats-new.md)

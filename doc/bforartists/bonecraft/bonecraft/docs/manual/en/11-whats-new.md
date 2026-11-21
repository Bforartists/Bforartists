# What's New

[← Contents](index.md)

Newest first.

## 9.2.19 — Panel controls (local candidate)

This local candidate has not been published. The standalone release remains 9.2.18.

- Collections and Visibility Bookmarks initialize their settings outside panel drawing.
- Grouped panels use their own controls and check the current selection and mode.
- Hair Physics reads the selected pose bones in current hosts.
- Bone Inspector displays rest-bone roll and copies names through its header button.
- Eye Tracking displays degree values while preserving saved settings.

The English manual adds matching pictures for the tools and settings. Earlier pictures retain their original version labels.

## 9.2.18 — Saved mechanism forms

Earlier saved forms remain readable and usable in current Bforartists builds. Opening or applying a form does not resave it. **Save Form** captures the current values using the current format. Existing handles, sliders and panel locations remain unchanged.

The release fixes compatibility diagnostics on newer hosts. The diagnostic alone did not prove that earlier hosts could not use saved forms. See [Forms](07-mechanisms.md#forms) and the [release notes](https://github.com/Axleonex/B4Artists_Toolkit/blob/main/docs/bonecraft/releases/9.2.18/RELEASE-NOTES.md).

This is the standalone Toolkit release. It does not establish acceptance into official Bforartists. Historical screenshot and tutorial test limits remain in their chapters.

## 9.2.17 — Export naming and mode restoration

**Unity / VRChat** and **Unreal Engine 5** now offer **Bone Names**: **Keep Original Names**, **Unity-Preset** and **Unreal-Preset**. The preview shows recognized bones and proposed names. Naming affects export copies, including vertex groups, animation channels and Unity sidecar references. The working rig retains its names.

The two main engine export buttons now accept Object, Pose and Edit Mode. They restore the original mode and selection after export or cleanup. Active-action FBX baking no longer requires a separate NLA strip.

Recognized optional humanoid bones, fingers and toes participate in naming. Conflicting names or ambiguous mappings block renaming. These profiles retain hierarchy, orientation and rest pose. They do not construct a Manny/Quinn skeleton.

Renamed **Export (Profile)** output supports **Active Action** and **No Animation**. **All Actions** requires **Keep Original Names**. See [Game Engine Export](08-vrchat.md#game-engine-export) and the [9.2.17 notes](https://github.com/Axleonex/B4Artists_Toolkit/blob/main/docs/bonecraft/releases/9.2.17/RELEASE-NOTES.md).

## 9.2.15 — Reviewed material-atlas workflow

The panel now presents three stages: target selection, material and texture selection, then baking and review. **Smart Combine Materials** is the initial automatic shortcut. After analysis, **Refresh Analysis** rebuilds the lists. **Bake Checked Sources** bakes the reviewed choices.

Both source lists have **Select All** and **Deselect All**. They change Include checkboxes only within the active group and source list. Missing textures stay unchecked. Bulk selection does not enable a disabled group. **Object → Atlas Source Selection** offers the same actions.

**Source Details** starts collapsed. **Copy Debug Report** is under **Advanced Options**. Backup, Accept and Revert remain visible. These UI changes retain the existing bake workflow and preservation constraints.

## 9.2.14 — Color-only meshes

Color-only meshes without authored UVs receive the baked atlas UV layer during final assembly.

## 9.2.13 — Material counts

Material estimates and results count atlas slots on every output mesh. Revert resets those results.

## 9.2.12 — Export UV0

The rebuilt atlas mesh exports `atlas_uv` as UV0 while **Keep Source UV Maps** is disabled. Retaining source maps can leave the atlas on UV1.

## 9.2.11 — Changed-source checks

Preflight rejects missing or changed analyzed material sources before creating an atlas backup.

1. Refresh the analysis.

2. Review the source choices again.

## 9.2.10 — Excluded materials

Atlas assembly preserves excluded materials and shared material references.

## 9.2.9 — Render-hidden sources

The combiner bakes render-hidden sources through temporary copies. Revert restores original visibility.

## 9.2.8 — Connected shader inputs

The combiner preserves connected Principled tint, mapping and alpha graphs during baking. MToon retains its fallback path. **Metallic** and **Pack ORM Channels** remain blocked by preflight.

## 9.2.7 — Transparency classification

Material classification handles modern DITHERED opacity and linked or constant alpha. The render setting alone no longer forces an opaque material into a transparent group.

## 9.2.6 — MMD and PMX installation

The installer recognizes modern MMD Extensions and legacy add-ons. Extension installation preserves its dependencies and reports unavailable local repositories. An enabled extension is recognized even without legacy add-on metadata. Cancelled PMX imports remain cancelled instead of reporting success.

The [dated repair record](https://github.com/Axleonex/B4Artists_Toolkit/blob/main/bonecraft/docs/material-combiner-fixes-2026-10-23.md) covers 9.2.6–9.2.15 and their generated-fixture checks. The [9.2.15 UI review](https://github.com/Axleonex/B4Artists_Toolkit/blob/main/bonecraft/docs/material-combiner-ui-review-9.2.15.md) records operator checks and visual-testing limits. These historical records do not claim a fresh full-manual replay in 9.2.18.

## 9.2.5 — Starter Rigs catalog tab

Starter Rigs now uses one catalog tab in the native bottom asset shelf. This replaces the top-left viewport controls. To show the tab beside other catalogs, enable **Starter Rigs** in the shelf's catalog menu once. Native asset import and **Add → Armature → Starter Rig Catalog** remain available.

## 9.2.4 — Task Board and native tools

**Open Health Check** now runs rig validation and opens its results. Before using it, select an armature or its bound mesh. **Quick Wins** shows up to three recommendations. **Remaining Tasks** excludes those cards. **Refresh Task Board** checks again.

Place Rig Markers and Build Mechanism remain available as viewport tools. Their registration no longer breaks native Grab/Move or tool cycling in Object and Pose modes.

## 9.2.3 — VRChat export location

Removes the duplicate Export to VRChat panel from Avatar Tools. Export remains under CATS → Import / Export → Unity / VRChat.

## 9.2.2 — Current interface

Each tab contains a workspace group. Setup Rigging, Skin, Review, Avatar Tools and Facial are expandable sections inside tabs. The paths below use English UI labels. Translated labels depend on the Language preference.

- Bone Merge → BoneCraft → Setup Rigging
- Delta Mush / Proximity Wrap → BoneCraft → Skin
- Viseme Library / Lip Sync → CATS → Avatar Tools
- VRChat Viseme Mapping / Face Tracking → CATS → VRChat Tools → Facial

## 9.2.0 (October 2026)

- **Complete starter catalog:** all nine bundled skeletons/metarigs have thumbnails from the start. They are Basic Humanoid, Simple Human, Full Human, Basic Quadruped, Cat, Horse, Wolf, Bird and Shark. The catalog selector groups Humans, Quadrupeds and Other Animals.
- **Rigify when needed:** Basic Humanoid works independently. Rigify starters remain visible while Rigify is disabled. Selecting one offers **Enable Rigify & Add Rig** or Cancel. Cancellation, activation failure or an unavailable preset adds no rig.
- **Optional shelf, historical 9.2.0 location:** the viewport header's **Starter Rigs** switch returned to the regular asset shelf. The choice persisted in preferences. Version 9.2.5 replaces this switch with a native catalog tab. **Add → Armature → Starter Rig Catalog** still opens the chooser as a popup.
- **Click or drag:** clicking a starter adds it, as does dropping it inside the viewport. Mesh fitting starts enabled. Weighting and control generation start disabled. Adjust Last Operation controls these options. Native click, drop, cancellation and undo/redo checks used Bforartists 5.2.0.

## 9.1.2 (October 2026)

- **Scene Properties switch:** Preferences > Tabs has a new Scene Properties row. Its Show button controls all BoneCraft sections in the Properties > Scene tab. These are Rig Builder, Mechanisms, CATS, Avatar Tools, VRChat Tools and Import / Export. The switch starts enabled and shows blue while enabled. It does not disable the add-on or change the viewport tabs or Armature tab. See [Where things are](01-start.md#where-things-are).

## 9.1.1 (October 2026)

- **Clearer icons:** each icon now has one meaning throughout the interface. About 60 buttons received Bforartists icons that better match their functions. Examples include Apply All Transforms, Decimate, Normalize Names, Translate, Merge, Separate, Blend Pose and Lip Sync. Each button uses the same icon in every panel.
- **Calmer panels:** headings and fixed text no longer carry topic icons. Hints that report a state show the info, warning or check icon.
- **Readable icon grid:** every button in the Pose and Weights Tool Shelf tabs has its own icon, so a narrow shelf stays readable.

## 9.1.0 (October 2026)

- **Tools where Bforartists puts its own:** BoneCraft adds entries to Add → Armature and the Pose, Weights and Object menus. It also adds button panels to Bforartists' Pose and Weights Tool Shelf tabs.
- **Act first, tune after:** Quick Rig, Fit Dropped Rig and weight tools run immediately with their last-used values. Ribbon, Spline IK, Delta Mush and CATS bone tools also run immediately with their last-used values. Adjust Last Operation controls their options afterwards. The tools use fewer confirmation pop-ups.
- **Actions first, options folded:** several panels show buttons above a fold containing optional settings. Required inputs and Fix Model's cleanup switches remain above the action. Settings use checkboxes rather than buttons. Panel headers have no icons.
- **Gesture tools:** Place Rig Markers and Build Mechanism are in the viewport toolbar. Place Rig Markers places the Auto-Rig Wizard's next marker when you click the mesh. Build Mechanism starts a joint or link when you click a part.
- **Avatar sections, historical 9.1.0 location:** Avatar Tools held humanoid mapping, hair, visemes and export. The separate VRChat Tools section groups Performance, Clothing and Naming utilities. Export now lives under **Import / Export → Game Engine Export → Unity / VRChat**.
- **Tooltips:** every operator and every option explains itself.
- **Show, don't hide:** when no rig is available, sections stay visible and explain what to select. Auto-Rig Wizard appears first in Rig Builder. Shelves start wide enough to read.
- **Fixes:** Generate Spline IK works again. Add Influence uses the chosen bone. Viseme previews use their set.

## 9.0.0 (October 2026)

- **Mechanisms:** a new section in the BoneCraft tab and Properties Scene tab rigs props and machines. Its types are Hinge, Slide, Telescope, Piston, Gear Link, Follow and Sequence. Guided steps build them. Test checks their motion. BoneCraft never overwrites a manual edit automatically. **Keep mine** retains the edit. **Restore** rebuilds the mechanism. See [Mechanisms](07-mechanisms.md).
- **Example file:** `examples/crescent-rose/` holds Crescent Rose rigged with Mechanisms (scythe, rifle and compact forms), and the manual's [chapter 12](12-crescent-rose.md) builds it step by step.
- **Tab sides:** each viewport tab can sit on the left Tool Shelf or the right sidebar (Preferences → Tabs → Left / Right). BoneCraft and Rig Builder start on the left, CATS on the right.
- **Rig Builder:** always appears in the Properties Scene tab and also has its own viewport tab. A compact layout fits a narrow Tool Shelf. The BoneCraft Rigs asset library includes Basic Humanoid. Fit Dropped Rig fits a rig dropped from the asset shelf.
- **CATS tab:** Import / Export moved into the CATS tab. CATS, VRChat and Import / Export are also always in the Scene tab.
- **Show Helpers:** one preference shows or hides BoneCraft's teaching text. Compact Mode controls the same preference.
- **Rig Validator:** bone names with hyphens pass. Drivers warn only for expressions that need Python. Checks also cover Mechanisms rigs. The Task Board's validator task reports again.
- **Name:** the add-on is called BoneCraft.

## 8.9.x (September–October 2026)

- **8.9.6:** the whole dress piece follows skirt bones without hip clipping. Jaw-open corner correctives support sticky lips.
- **8.9.5:** the IK/FK elbow switch preserves the pose without a jump. Shoulder detection is symmetric. Eye markers no longer snap. Control Picker shows the selection. Other changes include rounder mouth corners, a dress-over-thigh correction, relaxed retarget collarbones and T-pose export.
- **8.9.4:** correctives replace Preserve Volume for rounder knees. This version also adds contact keys for deep bends and a shoulder seam blend.
- **8.9.3:** two-segment skirt bones follow the legs. The legs also push these bones.
- **8.9.2:** shape keys create blinks without lid folds. The mouth opening is oval.
- **8.9.1:** dense-mesh skinning is faster (678,000 vertices: 232 s to 57 s). Bone heat uses a lighter proxy mesh instead of failing silently.
- **8.9.0:** this version adds joint corrective shape keys and face controls for eye aim, blink and lip follow. Clothing bends with the joints.
- Version 8.9 also adds automatic bone weight recalculation and clearer atlas selection.

## 8.7–8.8 (September 2026)

- **8.8.0:** the retarget panel works on Blender 5 hosts. Finger-marker placement uses the hand's shape. Other changes include IK stretch to the skin, a Preserve Volume option and a Delta Mush bind fix.
- **8.7.0:** this version adds an integrated control rig, limb-traced joint detection, direction-matched retargeting and twist bones.

## 8.5–8.6 (July 2026)

- **8.6.1–8.6.3:** Material Atlas adds tile diagnostics after baking and better partitioning of mixed materials. It checks MToon transparency against actual texture alpha and preserves that transparency during atlasing.
- **8.5.5–8.5.10:** VRM / MToon materials respect alpha mode. Alpha works on Blender 5 hosts. Other changes prevent excessive emission and add magenta diagnostics and safe atlas names.
- **8.5.4:** humanoid mappings load correctly. This version also adds Naming Prep guidance.
- **8.5.2–8.5.3:** these versions add VRoid download (.zip) import and a VRoid project hand-off card.
- **8.5.1:** FBX export preserves blend shapes.

## Earlier versions

**8.5.0:** after baking, Smart Combine makes `atlas_uv` the export UV0 by default. Unless **Keep Source UV Maps** is enabled in Advanced settings, it removes the pre-atlas source UV map from the generated atlas mesh. The open Blender build now shares the CATS / Material Combiner / UVToolkit-derived controls. Production rigging, control, retarget/export and B4Artists-only release systems remain exclusive to B4Artists.

8.5.0 also updates export and validation. VRChat, VRM, MMD and Unreal exports now have folder and file-name controls in BoneCraft panels. Export settings no longer depend only on Blender's file-browser defaults. VRChat/Unity and Unreal FBX exports enable **Embed Textures** by default to simplify material import. Unless **Helper Meshes** is enabled, VRChat export excludes helper/control-shape meshes from the FBX. The VRM panel adds **Lint Now** and **Fix Humanoid Map**. Fix Humanoid Map repairs stale humanoid alias mappings before export without renaming bones.

**8.4.5:** during baking, Smart Combine makes source textures sample the preserved pre-atlas UV. It validates the generated atlas mesh before hiding originals. It resets all atlas faces to the final atlas material slot. This prevents gray or scrambled robe/clothing sections.

**8.4.4:** the Material Atlas Combiner adds inspection controls before baking for quality parity. These include shader/material diagnostics, texture-role labels, duplicate/shared source markers, per-material size overrides and packing presets. Optional output bakes cover Normal/Emission/Roughness. Preflight blocks Metallic/ORM channel packing until that path is verified.

**8.4.3:** the Material Atlas Combiner adds selectable UV packing methods to the existing workflow. Choices include Smart Pack, Grid Pack, Seeded Variation, Oriented Pack, Fit 0-1 Bounds, Advanced Variation and Rotation Step. The debug report and bake ledger record UV method details.

**8.4.2:** during baking, the Material Atlas Combiner targets the generated atlas UV. Copied source texture nodes explicitly read the pre-atlas UV. This fixes robe/clothing atlas errors caused by source textures and the baked atlas sampling different UV maps. Selectable material and texture rows from 8.4.1 remain available.

**7.1.3 (preference label cleanup):** two add-on preference switches have new labels matching their sidebar tabs. "VRChat Avatar Tools" becomes **CATS**, matching the CATS sidebar tab. "Task Board & Sidebar" becomes **Rig Builder**, matching the Rig Builder sidebar tab. Only switch labels in Edit > Preferences > Add-ons > BoneCraft changed. No tools were removed.

**7.1.1:** BoneCraft adds the complete CATS suite for VRChat avatar cleanup, optimization and configuration. CATS has its own sidebar tab. Its pipeline guides the order of operations.

Next: [Tutorial: Crescent Rose with Mechanisms](12-crescent-rose.md)

# Rig Builder

[← Contents](index.md)

For a narrated demonstration of both rig types, see the [IK/FK beginner walkthrough and practice file](https://github.com/Axleonex/B4Artists_Toolkit/blob/main/bonecraft/docs/tutorials/ikfk-beginner.md).

## Building a New Rig

The Rig Builder makes a new rig for a character. Its **Rig Builder** tab is on the left Tool Shelf. Press **T** to show the shelf. When Preferences → Tabs → Scene Properties → Show is on, Rig Builder also appears in the **Properties** editor's **Scene** tab. A narrow Tool Shelf uses a compact layout with short labels. The Auto-Rig Wizard comes first, followed by Quick Rig and Mannequin. The viewport's Add → Armature menu also offers the wizard and Quick Rig.

---

### Auto-Rig Wizard

**What it does:** A step-by-step guide that places markers on your mesh and builds a complete rig with weights from them. The main way to rig a character from scratch.

[Guide 1](02-guides-a.md#guide-1-get-your-first-avatar-into-vrchat) walks through it step by step.

**Steps:** Select Mesh → Rig Type → Body Markers → Finger Markers → Face Markers → Review → Generate

**Key controls:**

- **Start Auto-Rig** opens the wizard. **Back** and **Cancel** are at the top. **Next** is at the bottom of the mesh, rig-type and marker steps. Review uses **Generate Rig** instead of Next. The final step uses **Close Wizard**
- The mesh list — click your mesh here. The next step offers **Body + Face**, **Body Only** or **Face Only** (for an existing armature)
- **Detect Markers** (in Smart Detection) — traces the mesh limbs and places every body marker with a confidence rating. **Accept High** keeps high-confidence markers. **Reset Low** clears low-confidence markers
- **Guess Markers from Mesh** and **Guess Precision** (body), **Guess Finger Markers** (finger markers are placed from the shape of the hand) and **Guess Face Markers**
- Finger Detail — how many fingers to build, from "0 — No Fingers" to "5 — Full Human Hand"
- Each marker's row: **Place Marker** (arrow icon), **Confirm Marker** (check mark) and **Reset Marker** (circular arrow). Left and right markers also have **Toggle Symmetry** as the first icon
- **Mirror L to R** and **Mirror R to L** — copy confirmed markers across the centre line
- **Confirm All Placed** — confirms every placed marker of the step
- **Generate Rig** — builds the rig from the confirmed markers. The last step offers **Build Control Rig** (see below) and **Close Wizard**

**What Generate Rig builds:**

- A body rig with the spine and neck segments you chose, and IK/FK, IK-only or FK-only arms and legs (the **Kinematics** option)
- Finger bones for the finger count you chose
- For **Body + Face**: a face rig, with control shapes when **Generate Control Shapes** is on
- Skin weights at the chosen quality. Dense meshes are weighted through a lighter proxy mesh, so a 678,000-vertex character takes about a minute instead of failing silently.

**Build Control Rig:** the review step also shows **Twist Bones**, **Skirt Bones**, **Face Controls** and **Joint Correctives**. Generate Rig does not apply these options. They belong to the engine control rig. This rig includes twist bones, skirt bones that follow the legs, eye aim and blink controls, and joint corrective shape keys. After Generate Rig, the last step offers **Build Control Rig**. This command builds the control rig on the generated armature with your selected options. Before **Close Wizard**, click **Build Control Rig**. Closing resets the wizard's options. The Control Layer panel (Rig Tools) appears only on a rig built this way.

**Where to find it:** Rig Builder → Auto-Rig Wizard

**Place several markers with the viewport tool:**

1. Start the wizard.
2. Advance to a body, finger or face marker step.
3. In Object Mode, activate Place Rig Markers in the viewport toolbar.

The tool header names the next unconfirmed marker and shows axis locks and a mirror switch.

4. Click the wizard's mesh to place and confirm that marker.
5. When the tool says the step is done, press **Next** in the wizard.

Symmetry follows the wizard's settings. The per-marker Place buttons still work. Clicking elsewhere does not place a marker.

---

### Quick Rig

**What it does:** Adds BoneCraft's Basic Humanoid or one of Rigify's metarigs in one click. Basic Humanoid has 19 bones and needs no Rigify. Quick Rig is faster than the wizard but less tailored to the mesh.

**Key controls:**

- The Basic Humanoid button and the Rigify metarigs. For a Rigify preset with Rigify off, select **Enable Rigify** first
- A rig button adds its rig immediately. Adjust Last Operation contains fitting, automatic weights, **Add IK/FK Controllers** and **Initial Pose**
- **T-Pose** and **A-Pose** — switch the selected rig's rest pose
- Expand Troubleshooting for **Diagnose Quick Rig (print to console)**. With a non-metarig armature active it also shows **Inspect Active Rig Controls**
- With a Rigify metarig active, Troubleshooting shows **Generate Control Rig (active metarig)** instead of Inspect Active Rig Controls. This generates the Rigify control rig

**The BoneCraft Rigs starter catalog:** all nine bundled starters share a **Starter Rigs** catalog in the native bottom asset shelf.

1. Open the shelf's catalog menu at the left.
2. Select **All** libraries.
3. Enable **Starter Rigs** once to add its tab beside the existing catalog tabs.
4. Select that tab to browse the starters.

**Add → Armature → Starter Rig Catalog** opens the dependency-aware popup for fitting and adding a starter.

Basic Humanoid needs no Rigify. The other thumbnails have the **Rigify** label. When Rigify is inactive, selecting or dropping one in the catalog popup offers **Enable Rigify & Add Rig** and Cancel. Accepting enables the installed Rigify and continues with that starter. Cancelling adds nothing. **Quick Rig** also offers **Enable Rigify**. The catalog popup's context menu offers it when Rigify is unavailable. A missing dependency or preset produces an explanation. The popup does not add a substitute rig when your installed version lacks that preset.

The native bottom asset shelf imports armature assets. Use **Add → Armature → Starter Rig Catalog** for the dependency-aware workflow below.

With a mesh selected, the tool fits the starter to that mesh when you add it. In the popup, click a thumbnail to add a starter, or drag it into the viewport. Automatic weighting and control generation start off. Adjust these options afterwards in **Adjust Last Operation**.

If no mesh was selected:

1. Select the new starter.
2. In Quick Rig, select the **Mesh**.
3. Click **Fit Dropped Rig**.

Fitting scales and positions the skeleton. Before generating controls or weights:

1. Inspect joint placement.
2. Edit joint placement as needed.

Dragging outside the viewport, pressing Esc, or right-clicking cancels without adding anything.

**Where to find it:** Rig Builder → Quick Rig; Add → Armature → Quick Rig also adds the premade rigs

---

### Mannequin

**What it does:** Builds a preview mesh around an existing rig so you can inspect its deformation without a finished character mesh. If you have no rig yet, add one with Quick Rig. Before using Mannequin, select the armature or a mesh parented to it. The mannequin is a preview only: replace it with your own mesh before final use.

**Key controls:**

- **Quick Mannequin** — builds a preview with fixed defaults, replacing the previous mannequin for this rig
- **Add Mannequin** — builds a preview using the scene settings. By default, it replaces an existing mannequin. Replace Existing is in Adjust Last Operation after the click
- **Regenerate** — rebuilds the existing preview using its saved settings
- **Remove** — deletes the mannequin mesh and keeps the armature
- Options below the buttons contains **Mode**, **Body Type**, density and **Radius Scale**. Advanced inside Options holds the region scales and output settings. To use changed scene settings, click **Add Mannequin** again

**Where to find it:** Rig Builder → Mannequin

---

## Illustrated mannequin workshop

<!-- Keep each illustrated step together and preserve the manual's print scale. -->
<style>
section.chapter:has(#ch-06-rig-builder) img { max-width: 100%; max-height: 155mm; width: auto; height: auto; }
@media print {
  [id="06-rig-builder--illustrated-mannequin-workshop"] { break-before: page; break-after: avoid; }
  h4[id^="06-rig-builder--"] { break-before: page; break-after: avoid; }
  h3[id^="06-rig-builder--part-"] { break-before: page; break-after: avoid; }
  h3[id^="06-rig-builder--part-"] + h4 { break-before: avoid; }
  section.chapter:has(#ch-06-rig-builder) h4 + p { break-after: avoid; }
  section.chapter:has(#ch-06-rig-builder) p:has(> img) { break-before: avoid; break-after: avoid; }
  section.chapter:has(#ch-06-rig-builder) p:has(> img) + p { break-before: avoid; }
}
</style>

Follow these three parts in order:

1. [A — Simple Human to mannequin](#part-a-simple-human-to-mannequin).
2. [B — rigless mannequin through Auto-Rig](#part-b-rigless-mannequin-through-auto-rig).
3. [C — test weights and use IK/FK](#part-c-test-weights-and-use-ikfk).

Every numbered workshop step has a real interface screenshot. Red numbers match the caption. Screenshots were captured with the **BoneCraft 9.1.2 release** in `Bforartists 5.2.0`. Blender’s panel arrangement and shortcuts can differ. Use the named commands as the reference.

The screenshots retain their 9.1.2 capture labels. Current navigation is **Rig Builder → Quick Rig**, **Rig Builder → Auto-Rig Wizard**, and **BoneCraft → Skin → Weight Tools**. Starter Rigs now uses the native bottom catalog tab. This source update does not claim a fresh 9.2.18 replay.

This exercise produces a simple capsule preview for learning rigging. Its head, hands and torso are placeholders. It is not a finished character model. Begin in a new file. Keep both saved checkpoints to repeat the conversion without losing the original metarig.

The repository includes both checkpoints in `examples/mannequin/`: `SimpleHuman_Mannequin.blend` is the neutral Part A result, and `Mannequin_AutoRig.blend` is the completed, posed Part C example with corrected weights.

### Part A: Simple Human to mannequin

#### A1. Enable Rigify

1. Start in a new scene.
2. Open **Scene Properties → Rig Builder → Quick Rig**.
3. If the Rigify presets are unavailable, click **Enable Rigify**.

This tutorial uses the Rigify `Simple Human` metarig. **BoneCraft Basic Humanoid (19 bones)** is a different preset.

![A1: Enable Rigify](../images/rig-builder/en/a01-enable-rigify.png)

*1 — Scene Properties. 2 — Enable Rigify.*

#### A2. Add Simple Human

Click `Simple Human` under Quick Rig. The result is an editable metarig, not yet a mesh. It has 29 bones in this release.

![A2: Add Simple Human](../images/rig-builder/en/a02-simple-human.png)

*1 — Simple Human preset.*

#### A3. Inspect the metarig

1. Move the pointer into the viewport.
2. Press `Numpad 1` for Front Orthographic.
3. Check that the whole skeleton is visible.
4. Use the mouse wheel to frame the skeleton.

The new metarig may start in Pose Mode.

![A3: Inspect the metarig](../images/rig-builder/en/a03-metarig.png)

*1 — Front view. 2 — Simple Human skeleton.*

#### A4. Return to Object Mode

Before changing the rest pose or generating the mannequin:

1. In the viewport mode dropdown, select **Object Mode**.
2. Keep `SimpleHumanArmature` selected.

![A4: Return to Object Mode](../images/rig-builder/en/a04-object-mode.png)

*1 — Mode dropdown. 2 — Object Mode.*

#### A5. Use a T-pose

In Quick Rig, click **T-Pose**. The arms extend horizontally. For a custom body, fit the metarig in Edit Mode before generating its preview. For this exercise, keep left and right joints symmetric.

![A5: Use a T-pose](../images/rig-builder/en/a05-t-pose.png)

*1 — T-Pose command.*

#### A6. Generate the mannequin

1. Expand **Mannequin → Options**.
2. Set `Mode: Universal`.
3. Set `Body Type: Neutral`.
4. Select **Medium**.
5. Set `Radius Scale: 1.00`.
6. Under Advanced, keep region scales at 1.00.
7. Select `Joined (non-manifold)`.
8. Select **Flat colour**.
9. Enable **Joint Smoothing**.
10. Leave Unified Volume off.
11. Click **Add Mannequin**.

The screenshot shows the resulting capsule mesh. Add uses the current options. Regenerate reuses the saved mannequin settings.

![A6: Generate the mannequin](../images/rig-builder/en/a06-final-settings.png)

*1 — Add Mannequin. 2 — Universal and body settings. 3 — Joined output and smoothing.*

#### A7. Try a bone pose

The character’s left is on your right in front view.

1. Select the armature.
2. Switch to **Pose Mode**.
3. Click the left forearm bone.
4. With the Rotate tool, rotate the bone slightly.

The attached mannequin follows. This is a weighted preview on the metarig. It does not yet have the animator controls used in Part C.

![A7: Try a bone pose](../images/rig-builder/en/a07-select-forearm.png)

*1 — Pose Mode. 2 — Selected forearm and its transform gizmo.*

#### A8. Restore and save the preview

1. With the pointer in the viewport, select all pose bones.
2. Press **F3**.
3. Search for `Clear Pose Transforms`.
4. Select **All**.
5. Confirm the mannequin returns to its T-pose.
6. Open **File → Save As**.
7. Save the file as `SimpleHuman_Mannequin.blend`.

Keep this checkpoint before continuing.

![A8: Restore and save the preview](../images/rig-builder/en/a09-clear-pose.png)

*1 — Clear Pose Transforms search. 2 — All resets the selected pose bones.*

### Part B: Rigless mannequin through Auto-Rig

#### B1. Select the mannequin mesh

Continue from the neutral checkpoint in Part A. This part deliberately removes the mannequin's rig before running the wizard.

1. Switch to **Object Mode**.
2. In the Outliner, select `SimpleHumanArmature_Mannequin`.

To preserve Part A, save the result under a different filename.

![B1: Select the mannequin mesh](../images/rig-builder/en/b01-select-mesh.png)

*1 — Select the mesh, not the armature.*

#### B2. Bake the preview into a mesh

Keep the mannequin in its restored T-pose. Keep only the mannequin selected.

1. Press **F3**.
2. Search for `Convert Mesh`.
3. Execute `Convert Mesh`.

This keeps the visible neutral geometry and removes the Armature modifier.

![B2: Bake the preview into a mesh](../images/rig-builder/en/b02-convert-mesh.png)

*1 — Convert Mesh command.*

#### B3. Clear the parent

1. Press **Alt+P**.
2. Select `Clear and Keep Transformation`.

This detaches the mesh from the old metarig without moving it.

![B3: Clear the parent](../images/rig-builder/en/b03-clear-parent.png)

*1 — Clear and Keep Transformation.*

#### B4. Remove the old weights

This action is for this disposable training mesh. The groups belong to the old metarig. The wizard will create new groups.

1. Open **Object Data Properties → Vertex Groups**.
2. In the list’s dropdown menu, select `Delete All Groups`.

![B4: Remove the old weights](../images/rig-builder/en/b04-clear-groups.png)

*1 — Vertex Groups menu. 2 — Delete All Groups.*

#### B5. Verify the rigless checkpoint

1. With its Outliner eye icon, hide the old `SimpleHumanArmature`.
2. Check that the mannequin remains visible.
3. Check that its Modifiers panel has no Armature modifier.
4. Check that its Vertex Groups list is empty.

This is the rigless mannequin input. BoneCraft 9.1.2 generates mannequins from an armature. Detaching this preview supplies a rigless training mesh.

![B5: Verify the rigless checkpoint](../images/rig-builder/en/b05-rigless-check.png)

*1 — Hide the old metarig. 2 — Empty modifier stack.*

#### B6. Enable the viewport Rig Builder tab

In the tested 9.1.2 host, Place Marker started from Scene Properties did not accept viewport clicks. Use the viewport tab for marker placement.

1. Open **Edit → Preferences → Add-ons → BoneCraft → Tabs**.
2. Enable **Rig Builder**.
3. Select **Left**.
4. Close Preferences.
5. Place the pointer over the viewport.
6. If the left Tool Shelf is hidden, press **T**.

![B6: Enable the viewport Rig Builder tab](../images/rig-builder/en/b10a-enable-rig-builder-tab.png)

*1 — Enable Rig Builder. 2 — Left Tool Shelf placement.*

#### B7. Start Auto-Rig

With the rigless mannequin selected, click **Start Auto-Rig**. The screenshot shows the equivalent Scene Properties button. The viewport Rig Builder tab enabled in the previous step has the same command at the top.

![B7: Start Auto-Rig](../images/rig-builder/en/b06-start-wizard.png)

*1 — Start Auto-Rig.*

#### B8. Choose the input mesh

Do not select a widget or another preview object.

1. In `Select Mesh`, select the mannequin.
2. Verify the selected-mesh check.
3. Click **Next**.

![B8: Choose the input mesh](../images/rig-builder/en/b07-select-input.png)

*1 — Mannequin input. 2 — Next.*

#### B9. Choose a body rig with both methods

This capsule mannequin has no facial topology, so Body + Face is unnecessary.

1. Select **Body Only**.
2. Select `Kinematics: IK + FK`.
3. Keep **Generate Control Shapes** enabled.
4. Click **Next**.

![B9: Choose a body rig with both methods](../images/rig-builder/en/b08-body-ikfk.png)

*1 — Body Only. 2 — IK + FK. 3 — Next.*

#### B10. Detect initial body markers

Detection guesses are a starting point. Do not accept guesses without checking them.

1. For this symmetric mannequin, keep **Mirror Symmetry** enabled.
2. In Body Markers, click **Detect Markers** under Smart Detection.

![B10: Detect initial body markers](../images/rig-builder/en/b09-detect-markers.png)

*1 — Detect Markers. 2 — Mirror Symmetry.*

#### B11. Review the detected positions

This segmented preview produces several low-confidence guesses. Before generating:

1. Check head top, neck base, pelvis, wrists and ankles against the visible mesh.
2. Review the main landmarks and optional precision landmarks.
3. Correct the landmarks as needed.

The confidence labels describe the original detection. A green check at the start of a row indicates that the current placement is confirmed.

![B11: Review the detected positions](../images/rig-builder/en/b10-review-markers.png)

*1 — Detection confidence summary. 2 — Body marker rows.*

#### B12. Place a wrist on the mesh

In front view, the character’s left wrist is on the screen’s right.

1. If the marker is already confirmed, reset its row to expose the placement button.
2. In the viewport **Rig Builder** tab, click the **Place Marker** eyedropper on Wrist Left.
3. Click the wrist surface in the viewport.

![B12: Place a wrist on the mesh](../images/rig-builder/en/b11-place-wrist.png)

*1 — Wrist Left placement control. 2 — Click the wrist surface.*

#### B13. Check the mirrored wrist and ankles

1. Verify that both wrist rows show green checks and opposite X coordinates.
2. Repeat placement for `Ankle Left` at its joint, not at the toe.

Symmetry supplies Ankle Right. Check symmetry against the mesh. Do not copy the example coordinates onto a differently sized character.

![B13: Check the mirrored wrist and ankles](../images/rig-builder/en/b12-mirrored-wrist.png)

*1 — Confirmed wrist pair. 2 — Mirrored wrist on the mesh.*

#### B14. Refine shoulders and elbows

1. Scroll to Precision Markers.
2. Reset `Shoulder Left`.
3. Place `Shoulder Left` at the upper-arm pivot.
4. Reset `Elbow Left`.
5. Place `Elbow Left` at the elbow gap.
6. Confirm their mirrored partners.
7. Keep the wrist at the hand end of the forearm.

These points determine the arm chain. Correct a shoulder or elbow guessed on the wrong capsule.

![B14: Refine shoulders and elbows](../images/rig-builder/en/b13-arm-precision.png)

*1 — Shoulder and elbow marker rows. 2 — Shoulder. 3 — Elbow.*

#### B15. Refine hips and knees

1. Place `Hip Left` at the top of the thigh.
2. Place `Knee Left` at the thigh/shin gap.
3. Check the opposite side supplied by symmetry.
4. Keep the pelvis on the centre line, between the hips.

![B15: Refine hips and knees](../images/rig-builder/en/b14-leg-precision.png)

*1 — Hip and knee rows. 2 — Hip surface. 3 — Knee gap.*

#### B16. Check depth and toes from the side

1. With the pointer over the viewport, press `Numpad 3`.
2. Check the landmarks in Right Orthographic as well as from the front.
3. Place `Toe Left` near the front of the foot.
4. Verify its mirrored partner.

A marker can appear correct from the front yet be too far forward or behind the body.

![B16: Check depth and toes from the side](../images/rig-builder/en/b15-side-depth.png)

*1 — Right Orthographic. 2 — Toe marker row. 3 — Foot surface.*

#### B17. Place the heels

1. If a heel was guessed incorrectly, reset that heel.
2. In side view, place `Heel Left` near the back of the foot.
3. Verify Heel Right.

These markers are optional. Leaving both at zero produced a proximity warning in the tested release. Placing them on the feet cleared that warning.

![B17: Place the heels](../images/rig-builder/en/b16-place-heels.png)

*1 — Confirmed heel pair. 2 — Heel location.*

#### B18. Confirm and continue

1. Review head top, neck base and pelvis, and every paired landmark.
2. Click **Confirm All Placed**.
3. Click **Next**.

The green checks beside the names show the confirmation state. The original REVIEW/ADJUST confidence labels may remain visible in 9.1.2.

![B18: Confirm and continue](../images/rig-builder/en/b17-confirm-markers.png)

*1 — Confirm All Placed. 2 — Next.*

#### B19. Skip fingers for this mesh

This mannequin has hand capsules but no finger geometry.

1. Select `0 — No Fingers`.
2. Click **Next**.

For a real hand mesh instead:

1. Select the appropriate finger count.
2. Place the finger markers.

![B19: Skip fingers for this mesh](../images/rig-builder/en/b18-no-fingers.png)

*1 — No Fingers. 2 — Next.*

#### B20. Review and generate

Before proceeding, require **All checks passed**. These settings apply to this simple training mannequin. They are not universal export requirements.

1. Select **IK + FK**.
2. Enable control shapes.
3. Set `Spine Segments: 3`.
4. Set `Neck Segments: 1`.
5. Select `No Fingers`.
6. Select **Game Ready**.
7. Disable Twist Bones.
8. Disable Skirt Bones.
9. Disable Preserve Volume.
10. Disable Joint Correctives.
11. Click **Generate Rig**.

![B20: Review and generate](../images/rig-builder/en/b19-review-generate.png)

*1 — Marker checks. 2 — Generation settings. 3 — Generate Rig.*

#### B21. Build the animator controls

After generation, click **Build Control Rig**. Generate Rig supplies the body rig and weights. Build Control Rig adds the control layer used below. The input mesh is already present, even if the completion panel displays its generic mannequin offer. Do not click Quick Mannequin again.

![B21: Build the animator controls](../images/rig-builder/en/b20-build-controls.png)

*1 — Build Control Rig.*

#### B22. Finish the wizard

1. Wait for the control-rig completion message.
2. Click **Close Wizard**.
3. Keep the old Simple Human metarig hidden.

The new armature appears in the Outliner. The new rig must deform the mesh. Visible bones alone do not prove that deformation works.

![B22: Finish the wizard](../images/rig-builder/en/b21-close-wizard.png)

*1 — Build button is now disabled. 2 — Close Wizard.*

### Part C: Test weights and use IK/FK

The generated armature has this object name in the tested release (use it in the Outliner and the weight tool):

```text
BoneForge_Rig
```

`FK (Forward Kinematics)` follows rotations down a hierarchy. Upper-arm rotation affects the forearm, followed by the hand. It suits broad swings and freely moving limbs. `IK (Inverse Kinematics)` starts at an endpoint. When you move a wrist or ankle target, the solver bends the chain to reach it. It suits planted feet and hands that must meet a surface.

| Task | Control to use | What to watch |
|---|---|---|
| Swing an arm | FK shoulder and elbow controls | Child controls follow their parent |
| Place a hand | IK wrist target | Shoulder and elbow solve toward the target |
| Plant a foot | IK ankle target for that leg | Move the body while the reachable target stays placed |
| Aim an elbow or knee bend | IK pole control | The pole sets the bend direction; it is not the wrist/ankle target |
| Change method | The limb’s IK/FK buttons | Check the snapped pose before keying animation |

The exercise below compares one arm in both modes. Each limb has its own switch. `Bake IK / Bake FK` are animation conversion tools. A single-pose switch does not replace baking or keying an animation. See [Control Layer](05-rig-tools.md#control-layer-ikfk) for the other controls.

#### C1. Open the control layer

1. Select **generated armature**.
2. Select **Pose Mode**.
3. Open **BoneCraft → Review → Control Layer**.
4. Select **arm-L → FK**.

Each arm and leg has a separate IK/FK switch. Left and right refer to the character. In front view, arm-L appears on your right.

![C1: Open the control layer](../images/rig-builder/en/c02-control-layer.png)

*1 — Pose Mode. 2 — Control Layer and arm-L switch.*

#### C2. Show the animator controls

1. Open the armature’s **Object Data Properties → Bone Collections**.
2. Select the Solo star for `Controls`.
3. Select the Solo star for **FK**.
4. If the mesh obscures controls, enable **In Front** under Viewport Display.
5. When using targets later, include **IK**.

The Solo selections isolate those control shapes. This native collection list also works if the BoneCraft Collections panel fails to draw in this host.

![C2: Show the animator controls](../images/rig-builder/en/c03-visible-controls.png)

*1 — Controls and FK Solo stars. 2 — In Front.*

#### C3. Select the forearm FK control

1. In front view, click the circular control at the character’s left elbow.
2. Check that the viewport selection name is **forearm.fk-L**.

An FK forearm control rotates around the elbow. Selecting the shoulder control would rotate the upper arm and its children instead.

![C3: Select the forearm FK control](../images/rig-builder/en/c04-select-fk.png)

*1 — Selected forearm.fk-L control. 2 — FK is active for arm-L.*

#### C4. Rotate and inspect the deformation

The goal is a rotation of approximately `−45°` about global **Y** for this front-view example. Use one of these methods:

- With the Rotate tool, rotate the selected FK control.
- For the shown Bforartists keymap, follow these steps:

1. Press **Ctrl+E**.
2. Press **Y**.
3. Type **-45**.
4. Press **Enter**.

Blender’s default rotate shortcut is **R**. The screenshot deliberately shows the initial weight problem: the upper-arm capsule tilts with the forearm. Do not accept this as a finished rig.

![C4: Rotate and inspect the deformation](../images/rig-builder/en/c05-fk-weight-check.png)

*1 — Incorrect upper-arm movement during the FK test.*

#### C5. Recalculate the mannequin weights

If the pose test above fails, follow these steps:

1. Switch to **Object Mode**.
2. Select the mesh.
3. Open **BoneCraft → Skin → Weight Tools → Automatic Bone Weight Recalculation**.
4. Set Mesh to Reweight to the mannequin.
5. Set Existing Armature to **generated armature**.
6. Select **Body**.
7. Select `Body Method: Bone Heat`.
8. Set `New Weight Strength: 1.00`.
9. Set `Smooth Passes: 0`.
10. Set `Max Bones per Vertex: 0`.
11. Set `Minimum Weight: 0.001`.
12. Keep **Keep Weight Backup** enabled.
13. Run **Automatic Bone Weight Recalculation**.

This repaired the segmented preview in the tested release.

![C5: Recalculate the mannequin weights](../images/rig-builder/en/b23-recalculate-weights.png)

*1 — Mesh and armature. 2 — Bone Heat. 3 — Replacement settings and backup. 4 — Recalculate.*

#### C6. Verify the repaired FK bend

1. Select the generated armature again.
2. Return to **Pose Mode**.

The upper arm should now stay horizontal from shoulder to elbow while the forearm rises from the elbow. The hidden `WEIGHTS_BACKUP_…` object preserves the old weights. Before animating your own character, test other limbs too. A generated skeleton alone does not prove that skinning is correct.

![C6: Verify the repaired FK bend](../images/rig-builder/en/c05-fk-result.png)

*1 — Upper arm stays in place. 2 — Forearm bends at the elbow.*

#### C7. Switch the same arm to IK

Click **arm-L → IK**. The switch snaps the target to the current pose, so the arm should remain raised. If the targets are hidden, add **IK** to the visible Solo collections. Switching changes which controls drive the chain. It does not record a new animation.

![C7: Switch the same arm to IK](../images/rig-builder/en/c06-switch-ik.png)

*1 — arm-L IK switch. 2 — Pose retained when switching.*

#### C8. Select the wrist IK target

1. Click the control at the wrist.
2. Check that the selection name is **forearm.ik-L**.

Despite its forearm name, this is the endpoint target for the arm chain. Move this target to place the hand. The solver changes shoulder and elbow angles to reach the target.

![C8: Select the wrist IK target](../images/rig-builder/en/c07-select-ik.png)

*1 — Selected wrist target. 2 — Selection name.*

#### C9. Move the target and compare

Keep the target within the arm’s reach. The goal is a slight inward movement of the wrist target along global **X**. In this example, `−0.15 m` creates a visibly different bend. Use one of these methods:

- Drag the Move tool’s X arrow.
- For the shown keymap, follow these steps:

1. Press **Ctrl+W**.
2. Press **X**.
3. Type `-0.15`.
4. Press **Enter**.

Blender’s default move shortcut is **G**. Compare the whole arm with the FK example. The endpoint leads and both arm segments follow.

![C9: Move the target and compare](../images/rig-builder/en/c08-move-ik.png)

*1 — Wrist endpoint. 2 — Chain responds. 3 — Example X movement.*

#### C10. Switch back and save the example

1. Click **arm-L → FK** again.

The FK controls snap to the current IK pose.

2. Verify that the mesh does not jump.
3. Open **File → Save As**.
4. Save `Mannequin_AutoRig.blend`.

The screenshot shows the saved example with FK active. For a neutral training copy:

1. Keep all four limbs in FK.
2. Select all visible pose controls.
3. Press **F3**.
4. Search for `Clear Pose Transforms`, as in Part A.
5. Select **All**.
6. Save the neutral copy under a separate name.

![C10: Switch back and save the example](../images/rig-builder/en/c10-save-complete.png)

*1 — FK active again. 2 — Pose preserved. 3 — Saved file name.*

**Completion check:** The original metarig preview remains saved. The detached mannequin has a new body rig and controls. The preview weights are corrected. You have compared an FK rotation with an IK target move. Keep the saved rig as a learning example. For production, replace the preview with suitable character geometry.

---

### Animation Retargeting

Moving animation from one skeleton to another is covered in [Rig Tools: Retarget](05-rig-tools.md#retarget).

See the [Retarget picture](05-rig-tools.md#retarget) for its clip controls.

---

## Bone Merge

**What it does:** Combines two armatures into one — for example a body rig and a clothing or hair rig — keeping every weight.

[Guide 11](03-guides-b.md#guide-11-merge-two-rigs-together) walks through it step by step.

**The three stages:**

- Scope — selection of the two armatures and review of their differences
- Rename — resolution of name conflicts and identification of new bones
- Merge — preview followed by the final merge

**Key controls:**

- **Base** — the armature that stays. The other armature merges into it and is then hidden
- **Analyze** — compares the two skeletons. **Acknowledge Scope — Proceed to Rename** opens stage 2
- **Normalize Both Armatures** — renames the standard bones of both rigs to one naming standard (Mixamo Prefixed, Mixamo Stripped or custom)
- **Auto-Propose Renames** — suggests names for the merging rig's own bones
- **Apply Rename** — renames one entry (one undo step). **Apply Batch Pattern** renames many with a pattern (with `{bone}`, `{side}` and `{index}`)
- **Mark as Unique** — keeps a bone as a new bone instead of merging it
- **Verify Rename — Proceed to Merge** — opens stage 3
- **Run Merge Preview** — reports what the merge would do, without changing anything
- **Merge Armatures** — backs up both armatures and merges them

**Where to find it:** BoneCraft → Setup Rigging → Bone Merge

![Bone Merge starts with Stage 1: Scope. The later stages remain locked until their earlier checks finish.](images/screenshots/bc07-bone-merge.png){style="max-width:100%;max-height:155mm;width:auto;height:auto"}

*Native panel popover, BoneCraft 9.2.18. Bone Merge starts with Stage 1: Scope. The later stages remain locked until their earlier checks finish.*

Next: [Mechanisms](07-mechanisms.md)

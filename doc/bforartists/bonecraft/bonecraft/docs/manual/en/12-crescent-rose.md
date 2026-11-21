# Tutorial: Crescent Rose with Mechanisms

[← Contents](index.md)

<!-- Print layout is scoped to this illustrated chapter; the shared renderer is unchanged. -->
<style>
@media print {
  h3[id^="12-crescent-rose--"] { break-before: page; break-after: avoid; }
  h2:has(+ h3[id^="12-crescent-rose--"]) { break-before: page; break-after: avoid; }
  h2 + h3[id^="12-crescent-rose--"] { break-before: avoid; }
  section.chapter:has(#ch-12-crescent-rose) p:has(> img) { break-after: avoid; }
  section.chapter:has(#ch-12-crescent-rose) p:has(> img) + p { break-before: avoid; }
  section.chapter:has(#ch-12-crescent-rose) table { break-inside: avoid; }
  [id="12-crescent-rose--what-you-built"] { break-before: page; break-after: avoid; }
}
</style>

## What you will build

Crescent Rose combines a scythe and a rifle. This tutorial rigs the model with Mechanisms. One slider converts the scythe to a rifle. A second slider folds the rifle into its compact form.

The tutorial uses every current joint and link except Gear Link. It includes eight Hinges, three Slides, a Telescope, a Piston and a Follow. It also creates two Sequences and three Forms.

The forms are teaching poses for this fan-made model. Mechanisms does not detect collisions or produce a physically engineered replica. When adapting the rig, inspect clearances.

The result is the file `examples/crescent-rose/CrescentRose_Mechanisms.blend`. Open it any time to compare.

## Before you start

- The files: `examples/crescent-rose/CrescentRose_parts.blend` contains the model split into 15 part objects. Start the tutorial from this file. `CrescentRose_Mechanisms.blend` is the finished rig.
- Time: allow one session for FBX preparation and another for the Mechanisms lesson. These are substantial exercises. Save checkpoints between stages.
- Words: first read "What Mechanisms does" in [Mechanisms](07-mechanisms.md). It defines part, joint, link, handle, Sequence and Form.
- Language: screenshots show Bforartists and BoneCraft's panels in English. BoneCraft panels follow the **Language** preference. The rest of Bforartists follows its interface language. If BoneCraft does not support your Bforartists language, its panels remain English. This English edition still applies.
- Starting route: use P1-P8 below for the original FBX, or skip to Step 1 with the prepared file. Both routes use the same 15 parts.
- Version: instructions and genuine interface captures were checked with BoneCraft `9.1.2` in Bforartists `5.2.0`, using its default keymap.

**Current navigation:** in 9.2.18, use **BoneCraft → Mechanisms** or **Properties → Scene → Mechanisms**. If the Scene sections are hidden, enable **Tabs → Scene Properties → Show**. Parts, Joints & Links, Sequences and Controls retain their names. Older screenshots can show an earlier arrangement around these sections.

This edition retains the original 9.1.2 capture and replay limits. The 9.2.18 source review does not replace them with a new tutorial replay. Older saved Forms remain readable and usable. Opening or applying them does not resave their values. See [Forms](07-mechanisms.md#forms).

Red numbered marks identify what to click, type into or inspect. Follow each image's numbered action key in order (1, then 2, then 3). Numbers restart in each image. A box marks a result to check. A circle marks a part or button to use.

## Prepare the original FBX (P1-P8)

If you use `CrescentRose_parts.blend`, skip this section.

1. Work in a new file.

2. Keep the source FBX and its `CrescentRoseTextures` folder together.

These steps were replayed in Bforartists 5.2.0 with the default keymap. Use the visible mode menu. In this keymap, Tab can toggle overlays instead of entering Edit Mode.

### P1 - Import the FBX

Use the Legacy importer for this recipe.

1. Start with an empty scene.

2. Select **File > Import > FBX (.fbx) (Legacy)**.

3. Select `CrescentRose.fbx`.

4. Keep import Scale at `1.00`.

5. Select Import FBX.

6. Press Numpad 3 for Right view.

7. Press Home to frame the imported objects.

The Outliner contains a root and three material meshes: `Black01`, `Blades01` and `Red01`.

![P1: Legacy FBX import options with Scale 1.00](../images/crescent-rose/en/prep-01-import-fbx.png){style="max-width:100%;max-height:155mm;width:auto;height:auto"}

*1: Select CrescentRose.fbx. 2: Keep Scale at 1.00. 3: Click Import FBX; use the Legacy importer.*

### P2 - Preserve placement and set the size

The imported weapon is approximately `0.32 m` tall. The prepared shortcut is already scaled. Perform this resizing procedure only once on the imported meshes.

1. Switch to Object Mode.

2. Select all three meshes.

3. Select **Object > Parent > Clear and Keep Transformation**.

4. Remove the now-unused root from the working scene.

5. With all three meshes selected, select **Object > Apply > Rotation & Scale**.

6. Press Ctrl+R to start Scale in this Bforartists keymap.

7. Type `6.25` to scale all three meshes together.

8. Confirm the scale.

9. Select **Object > Apply > Rotation & Scale** again.

The complete weapon is now approximately `1.997 m` tall.

![P2: clear parenting while preserving placement](../images/crescent-rose/en/prep-02-unparent-command.png){style="max-width:100%;max-height:135mm;width:auto;height:auto"}

*1: Press F3 and search Clear Parent Keep Transform. 2: Choose Clear and Keep Transformation. Repeat for all three meshes before removing the root.*

![P2: applied rotation and scale on the imported weapon](../images/crescent-rose/en/prep-02-scale.png){style="max-width:100%;max-height:115mm;width:auto;height:auto"}

*1: After scaling the three meshes together by 6.25, apply Rotation & Scale; Rotation must read 0. 2: Scale must read 1 on all axes.*

An individual object's Dimensions field measures only that material mesh. Check the combined bottom-to-top extent when measuring the weapon. All three objects must show rotation zero and scale 1 before separation.

### P3 - Connect the materials

1. Switch to the Shading workspace.

2. Select Material Preview.

Each of the three materials uses four images from `CrescentRoseTextures`:

| Image | Color space |
|---|---|
| `BaseColor` | **sRGB** |
| `Metallic` | `Non-Color` |
| `Roughness` | `Non-Color` |
| `Normal` | `Non-Color` |

For each material, process one image at a time:

1. Load the matching image from `CrescentRoseTextures`.

2. Set that image's color space using the table.

3. For a BaseColor, Metallic or Roughness image, connect Image Texture Color to the matching Principled BSDF input.

For each Normal image, use this separate connection branch:

1. Insert a **Normal Map** node.

2. Keep the Normal Map node in `Tangent Space`.

3. Connect Normal image Color to Normal Map Color.

4. Connect Normal Map Normal to Principled BSDF Normal.

Keep the existing UVs.

![P3: four texture maps and Tangent Space Normal Map connected for the black material](../images/crescent-rose/en/prep-03-materials.png){style="max-width:100%;max-height:155mm;width:auto;height:auto"}

*1: Connect BaseColor Color to BSDF Base Color. 2: Keep BaseColor on sRGB. 3: Set all data maps to Non-Color. 4: Connect Normal image > Normal Map > BSDF Normal, using Tangent Space.*

![P3: all three materials in Material Preview](../images/crescent-rose/en/prep-03-shaded.png){style="max-width:100%;max-height:155mm;width:auto;height:auto"}

*1: Check the blade material. 2: Check the red/black body materials in Material Preview; no pink missing textures.*

The procedure applies to the black, blade and red materials. After selecting each image, check its color space. The color-space setting belongs to the image. The weapon should be red, black and metallic, with no pink missing textures.

### P4 - Separate loose pieces

1. Select all three material meshes.

2. Select **Edit Mode** from the viewport mode menu.

3. Select all geometry.

4. Select **Mesh > Separate > By Loose Parts**.

5. Return to Object Mode.

There are now **37** mesh objects. Generated numeric suffixes can vary. Identify the objects by position and shape.

![P4: enter Edit Mode and choose By Loose Parts](../images/crescent-rose/en/prep-04-separate-command.png){style="max-width:100%;max-height:135mm;width:auto;height:auto"}

*1: Switch to Edit Mode and select all geometry. 2: Press F3, search Separate Loose, and choose By Loose Parts.*

![P4: the 37 loose pieces after separation](../images/crescent-rose/en/prep-04-separate.png){style="max-width:100%;max-height:155mm;width:auto;height:auto"}

*1: Check the object total is 37 after separation. 2: Use the Outliner to select pieces by shape and location; suffixes can vary.*

### P5 - Join the 15 moving groups

The table lists every source island. Material names describe appearance, not final object names.

| Final object | Pieces to combine | Mesh vertices after joining |
|---|---|---:|
| `BladeTip` | Black tip-joint knob and metal tip spike | 252 |
| `Blade2` | Two metal second-segment plates and two red covers | 1000 |
| `Blade1` | Two metal first-segment plates nearest the head | 512 |
| `HeadMount` | Black rear block, top cap and core; two red inner plates and two thin top covers | 1395 |
| `PlateL` | One red outer head plate on negative X | 676 |
| `PlateR` | One red outer head plate on positive X | 676 |
| `RearSpike` | Two metal spike blades, two red pivot caps and two red mount plates | 1194 |
| `Receiver` | Black body and small knob, metal ring above the bolt, long red housing | 2609 |
| `Grip` | Red grip block below the receiver | 194 |
| `Magazine` | Black tube beneath the body | 96 |
| `Bolt` | Red bolt cylinder and its two knob pieces | 362 |
| `Pole` | Metal lower shaft and red collar | 148 |
| `ButtSpike` | Metal bottom spike | 110 |
| `StrutBase` | Thin red rod between receiver and head | 34 |
| `StrutRod` | Black notched sleeve around that rod | 108 |

Do not merge the outer plates into Blade1. Do not merge the two strut pieces together. The strut already has two separate pieces. No bisect is needed.

Work from the blade tip inward, then through the receiver and pole. For each moving group:

1. Select the pieces that must move together.

2. For paired pieces on opposite sides, orbit the view to select both.

3. Check the selection before joining.

4. Select **Object > Join** (Ctrl+J).

5. Rename the joined object in the Outliner.

There must be **15 meshes and 9,366 vertices** in total. Step 2 repeats the finished part names and their later parenting.

![P5: all 15 moving groups named in the Outliner](../images/crescent-rose/en/prep-05-group-parts.png){style="max-width:100%;max-height:155mm;width:auto;height:auto"}

*1: Rename every joined group in the Outliner to match the 15 names in the table.*

![P5: the two Blade1 source plates selected before joining](../images/crescent-rose/en/prep-05-blade1.png){style="max-width:100%;max-height:155mm;width:auto;height:auto"}

*1: Select the two metal Blade1 plates on opposite sides. 2: Verify both objects are selected, then use Join and rename the result Blade1.*

![P5: Object menu Join command](../images/crescent-rose/en/prep-05-join-command.png){style="max-width:100%;max-height:135mm;width:auto;height:auto"}

*1: Open Object after selecting only the pieces of one group. 2: Choose Join (Ctrl+J). This menu crop identifies the command; use the two-piece selection shown above.*

### P6 - Centre the origins

1. Switch to Object Mode.

2. Select all 15 meshes.

3. Select **Object > Set Origin > Origin to Geometry**.

4. Set the operation's Center option to `Bounds Center`.

5. Check that rotation is zero and scale is 1.

The objects still have no parents. There is no armature. These origins are for preparation. Step 6 moves mechanism pivots to the actual joints.

![P6: Object > Set Origin > Origin to Geometry](../images/crescent-rose/en/prep-06-origin-command.png){style="max-width:100%;max-height:135mm;width:auto;height:auto"}

*1: Open Object. 2: Hover Set Origin. 3: Choose Origin to Geometry; set Bounds Center in the operation options.*

![P6: the centred Blade1 origin with applied transforms](../images/crescent-rose/en/prep-06-origins.png){style="max-width:100%;max-height:155mm;width:auto;height:auto"}

*1: The orange origin is now centred on the mesh. 2: Confirm Rotation 0. 3: Confirm Scale 1. Mechanism pivots are moved later.*

### P7 - Resize and pack the textures

There are **12 used maps**, four per material. Do not overwrite the source JPEGs. For each used map:

1. Select the map in the Image Editor.

2. Select **Image > Resize**.

3. Set width to **1024**.

4. Set height to **1024**.

5. Confirm the resize.

6. Select **Image > Pack**.

Packing preserves the resized pixels inside the blend. After processing every map, check Material Preview.

![P7: Image menu packing a resized 1024 by 1024 texture](../images/crescent-rose/en/prep-07-pack-textures.png){style="max-width:100%;max-height:155mm;width:auto;height:auto"}

*1: Choose Image > Resize and enter 1024 for width and height. 2: Check the resulting 1024 x 1024 dimensions. 3: Choose Pack. Repeat for all 12 used maps.*

### P8 - Save and reopen the prepared file

1. Save the working copy as `CrescentRose_parts.blend`.

2. Reopen that file.

3. Check the 15 named meshes, their transforms and the red/black materials.

4. Select Right view again.

5. Press Home.

6. Continue with Step 1.

All 12 maps should remain available without the original texture directory.

![P8: the prepared file reopened with the textured weapon intact](../images/crescent-rose/en/prep-08-save-parts.png){style="max-width:100%;max-height:155mm;width:auto;height:auto"}

*1: Open File for Save As, then Open to reload your working copy. 2: Confirm the 15 named meshes survived. 3: Check the materials; the title bar identifies the reopened file.*

## A. Open the file

### Step 1 — Open the parts file

1. Open `examples/crescent-rose/CrescentRose_parts.blend`.

2. Select Material Preview shading in the viewport.

3. Press Numpad 3 for Right view.

4. Press Home to frame the weapon.

The blade points left and the butt spike points down.

![Step 1: the parts file in the Right view](../images/crescent-rose/en/01-open-file.png){style="max-width:100%;max-height:155mm;width:auto;height:auto"}

*1: Click Material Preview. 2: Press Numpad 3 until the view says Right Orthographic; press Home to frame the weapon.*

**What you should be seeing:** The scythe in red and black, about 2 m tall, with nothing selected.

### Step 2 — Meet the parts

The Outliner lists the 15 objects. Each one is a piece that moves as one block:

| Object | What it is | Rides on |
|---|---|---|
| `Receiver` | The rifle body with the scope, trigger and sight | the rig |
| `Grip` | The grip under the receiver | `Receiver` |
| `Magazine` | The cylinder magazine | `Receiver` |
| `Bolt` | The bolt | `Receiver` |
| `Pole` | The lower shaft and its collar | `Receiver` |
| `ButtSpike` | The spike at the bottom | `Pole` |
| `HeadMount` | The head block the blade hangs from | `Receiver` |
| `Blade1` | The first blade segment, nearest the head | `HeadMount` |
| `Blade2` | The second segment | `Blade1` |
| `BladeTip` | The tip | `Blade2` |
| `RearSpike` | The spike on the back of the head | `HeadMount` |
| `PlateL`, `PlateR` | The outer side plates of the head | `HeadMount` |
| `StrutBase` | The thin rod between the receiver and the head | `Receiver` |
| `StrutRod` | The notched sleeve around that rod | `HeadMount` |

![Step 2: the 15 part objects in the Outliner](../images/crescent-rose/en/02-the-parts.png){style="max-width:100%;max-height:155mm;width:auto;height:auto"}

*1: Identify the three blade segments. 2: Match the body, head and pole names to the table. 3: Keep StrutBase and StrutRod as separate objects.*

For the original FBX, follow P1-P8 above. Those interface actions produced the supplied prepared file. The repository preparation script provides a reference grouping table.

### Step 3 — Find Mechanisms

If the left Tool Shelf is hidden:

1. With the pointer over the viewport, press T.

2. Select Tools from the Region Toggle menu.

Then:

1. Open the BoneCraft tab on the left Tool Shelf.

2. Expand **Mechanisms**.

3. Drag the shelf's right edge to make the panel text readable.

The same section appears in **Properties > Scene** when Scene Properties is set to Show in BoneCraft preferences. The screenshots use the Tool Shelf.

With a mesh active and no rig, **Add Parts from Selection** appears at the top. Before using it, select all parts as described in Step 4. Numbered subsections become usable after adding parts.

![Step 3: the Mechanisms section of the BoneCraft tab](../images/crescent-rose/en/03-mechanisms-section.png){style="max-width:100%;max-height:155mm;width:auto;height:auto"}

*1: Click the BoneCraft tab. 2: Expand Mechanisms. 3: Find Add Parts from Selection; select the meshes before using it.*

## B. Parts

### Step 4 — Add Parts from Selection

1. With the pointer over the viewport, press A to select all 15 objects.

2. Select **Add Parts from Selection**.

![Step 4: all parts selected, Add Parts from Selection](../images/crescent-rose/en/04-add-parts.png){style="max-width:100%;max-height:155mm;width:auto;height:auto"}

*1: Hover the viewport and press A to select the 15 meshes. 2: Click Add Parts from Selection.*

**What you should be seeing:** A new armature, "Mechanism Rig", appears in the Outliner with the parts under it. The mesh objects remain selected. **1. Parts** lists the 15 parts. The BoneCraft tab now starts with the rig's collapsible Overview.

### Step 5 — Rides on

A part rides on the part it is attached to.

1. Select `Blade1` in **1. Parts**.

2. Open the "Rides on" menu below the list.

3. Select `HeadMount`.

4. Repeat for each part using the table in Step 2.

`Receiver` keeps "the rig".

![Step 5: Blade1 rides on HeadMount](../images/crescent-rose/en/05-rides-on.png){style="max-width:100%;max-height:155mm;width:auto;height:auto"}

*1: Select Blade1 in the Parts list. 2: Open Rides on and choose HeadMount. Repeat using the parent table.*

### Step 6 — Pivots

A hinge turns around its part's pivot. The blade segments, head and grip must turn at their joints rather than their centres. Work in the orthographic side view to preserve the sideways pivot position.

1. Select `Blade1` in the list.

2. Select **Edit Pivot**.

3. Select the marker.

4. Press Ctrl+W for Move in Bforartists.

5. Click where the segment meets the head.

6. Select **Apply Pivot**.

7. Repeat the pivot procedure for the parts below.

| Part | Pivot position |
|---|---|
| `Blade2` | Where it meets `Blade1` |
| `BladeTip` | Where it meets `Blade2` |
| `HeadMount` | Its lowest point, where the strut meets it |
| `Grip` | Its top edge |
| `RearSpike` | Where it meets the head |
| `PlateL` and `PlateR` | The round bolt's centre, where Blade1 meets the head |
| `StrutBase` | Its bottom |
| `StrutRod` | Its top |

The screenshot's marker position is a guide. A few millimetres make no visible difference.

![Step 6: select the part and click Edit Pivot](../images/crescent-rose/en/06-edit-pivot-button.png){style="max-width:100%;max-height:135mm;width:auto;height:auto"}

*1: Select Blade1 in Parts. 2: Click Edit Pivot; then move and apply the marker as shown next.*

![Step 6: Blade1's pivot marker at the joint, Apply Pivot](../images/crescent-rose/en/06-edit-pivot.png){style="max-width:100%;max-height:155mm;width:auto;height:auto"}

*1: Move the pivot marker to the blade joint with Ctrl+W. 2: Click Apply Pivot to keep that location.*

## C. The head

### Step 7 — Add Joint → Hinge

If an obstruction needs hiding, hide it before starting the guide.

Open **Add Joint → Hinge**. The guided build's header and status bar explain each step.

![Step 7: the Add Joint menu, Hinge](../images/crescent-rose/en/07-head-hinge.png){style="max-width:100%;max-height:155mm;width:auto;height:auto"}

*1: Open Add Joint. 2: Click Hinge. The guided build now waits for a part.*

### Step 8 — Click the head

The header says "click the part that turns". In Right view, the outer plate obscures the head. Click the head's rear block behind the plates, at the circle.

If the header names `PlateR`:

1. Press Esc.

2. Restart **Add Joint > Hinge**.

3. Click further back on the head.

While active, the guide consumes ordinary keyboard shortcuts.

![Step 8: click the head's rear block](../images/crescent-rose/en/08-head-hinge-click.png){style="max-width:100%;max-height:155mm;width:auto;height:auto"}

*1: Click the rear black block of HeadMount, behind the red outer plate. Check the guide names HeadMount.*

### Step 9 — Press X, then Enter

The header asks for the axis.

1. Press X.

2. Inspect the looping preview.

3. Press Enter to keep the hinge.

The head turns around the sideways axis.

![Step 9: the axis step](../images/crescent-rose/en/09-head-hinge-axis.png){style="max-width:100%;max-height:155mm;width:auto;height:auto"}

*1: Follow the axis prompt: press X, then Enter. 2: Watch the head rotate around its pivot before confirming.*

**What you should be seeing:** `HeadMount Hinge` in **2. Joints & Links**, with its slider in **4. Controls**. Use these sliders in Object Mode.

To use viewport bone handles:

1. Select the armature.

2. Switch to Pose Mode.

### Step 10 — Limits

1. Select `HeadMount Hinge` in the list.

2. Set **Min** to 0.

3. Set **Max** to 120.

Positive values turn the head down and back. Keep the 120-degree travel limit. The Rifle sequence uses a 90-degree target together with the blade hinges.

![Step 10: Min 0, Max 120](../images/crescent-rose/en/10-head-hinge-limits.png){style="max-width:100%;max-height:155mm;width:auto;height:auto"}

*1: Select HeadMount Hinge. 2: Set Min to 0. 3: Set Max to 120; double-click the number, type, and press Enter.*

### Step 11 — Test

Click the row's play button. The head sweeps to 120° and back, and the pose is restored.

![Step 11: Test on the hinge's row](../images/crescent-rose/en/11-test-head.png){style="max-width:100%;max-height:155mm;width:auto;height:auto"}

*1: Click the small play triangle on the HeadMount Hinge row. Watch the sweep and return.*

## D. The blade chain

### Step 12 — Three more hinges

For each of `Blade1`, `Blade2` and `BladeTip`, repeat Steps 7 to 10:

1. Open **Add Joint → Hinge**.

2. Click the segment.

3. Press X.

4. Press Enter.

5. Set **Max** to 120.

Each segment rides on the previous segment. The three hinges form a chain.

![Step 12: the three blade-segment hinges and the separate head hinge in the list](../images/crescent-rose/en/12-blade-hinges.png){style="max-width:100%;max-height:155mm;width:auto;height:auto"}

*1: Create and select each blade hinge: Blade1, Blade2, BladeTip. 2: Set Max to 120 for each; use X as its axis.*

### Step 13 — Try the chain

1. Collapse **2. Joints & Links** to make room.

2. Expand **4. Controls**.

3. In Object Mode, set each of `Blade1 Hinge`, `Blade2 Hinge` and `BladeTip Hinge` to 60 degrees.

To enter each value:

1. Double-click its numeric field.

2. Press Ctrl+A.

3. Type the value.

4. Press Enter.

The later segments move with the earlier segments, curling the chain. Before continuing, reset all three values to 0.

![Step 13: the three blade hinges at 60 degrees in Controls](../images/crescent-rose/en/13-blade-chain.png){style="max-width:100%;max-height:155mm;width:auto;height:auto"}

*1: Enter 60 in each of the three blade sliders. 2: Check the chain curls together. Return all three sliders to 0.*

## E. Plates and strut

### Step 14 — Hinges on the plates

`PlateL` is hidden behind the head in Right view.

1. Add a Hinge on `PlateR` using the same procedure.

2. Set its **Max** to 30.

3. Press Ctrl+Numpad 3 for Left view.

4. Add a Hinge on `PlateL`.

5. Set its **Max** to 30.

6. Press Numpad 3 to return to Right view.

![Step 14: PlateL Hinge and PlateR Hinge](../images/crescent-rose/en/14-plate-hinges.png){style="max-width:100%;max-height:155mm;width:auto;height:auto"}

*1: Make both PlateR and PlateL hinges; use the opposite side view to reach PlateL. 2: Set each Max to 30.*

### Step 15 — Add Link → Follow

One handle should move both plates. Set the view before starting the guide:

1. Press Numpad 1 for Front view.

2. Select `Blade2`.

3. Use F3 > Frame Selected to bring the head close.

The two outer plates appear at the left and right edges.

1. Open **Add Link > Follow**.

2. Click `PlateL` at the left edge as the leading part.

3. Click `PlateR` at the right edge as the following part.

4. Press Enter.

![Step 15: Front view exposes both outer plates for the Follow picks](../images/crescent-rose/en/15-follow.png){style="max-width:100%;max-height:155mm;width:auto;height:auto"}

*1: Click PlateL first, the leading part. 2: Click PlateR second, the following part. Press Enter.*

### Step 16 — Ranges

1. Select the new Follow.

2. Check the automatically populated **Source Range** 0…30 and **Target Range** 0…30.

3. In **Name**, rename the link `PlateR Follow`.

![Step 16: Source Range and Target Range](../images/crescent-rose/en/16-follow-ranges.png){style="max-width:100%;max-height:155mm;width:auto;height:auto"}

*1: Name the link PlateR Follow. 2: Check Source Range is 0 to 30. 3: Check Target Range is 0 to 30.*

### Step 17 — Add Link → Piston

The strut must point between the receiver and head while the head folds. The guide consumes navigation shortcuts while active. Before starting the guide:

1. Press Numpad 3 for Right view.

2. Select `StrutRod` in the Outliner.

3. Use F3 > Frame Selected for a close view.

4. Open **Add Link > Piston**.

![Step 17: the Add Link menu, Piston](../images/crescent-rose/en/17-piston.png){style="max-width:100%;max-height:155mm;width:auto;height:auto"}

*1: Open Add Link after framing StrutRod. 2: Choose Piston; the guide asks for the cylinder first.*

### Step 18 — The cylinder and the rod

The guide's cylinder/rod roles describe the link ends. The model's object names describe its source pieces. `StrutBase` is the exposed thin red rod in the sleeve's notches. `StrutRod` is the black sleeve.

1. In the close view, click `StrutBase` first as the cylinder part.

2. Click `StrutRod` second as the rod part.

3. Press Enter to accept.

4. Rename the link `Head Strut`.

5. Keep **Stretch** disabled.

1. Change `HeadMount Hinge` in Controls.

2. Inspect the strut.

3. Reset the value to zero.

**What you should be seeing:** The strut follows the head. Each part aims at the other.

![Step 18: the piston guide, exposed red cylinder then black sleeve](../images/crescent-rose/en/18-piston-parts.png){style="max-width:100%;max-height:100mm;width:auto;height:auto"}

*1: Click the exposed red StrutBase first. 2: Click the black StrutRod sleeve second. Press Enter.*

![Step 18: Head Strut settings with Stretch off](../images/crescent-rose/en/18-piston-settings.png){style="max-width:100%;max-height:70mm;width:auto;height:auto"}

*1: Rename the link Head Strut. 2: Leave Stretch unchecked; then test HeadMount Hinge and restore 0.*

## F. The rifle

### Step 19 — Grip and rear-spike hinges

For each of `Grip` and `RearSpike`:

1. Open **Add Joint → Hinge**.

2. Click the part.

3. Press X.

4. Press Enter.

5. Set **Min** to 0.

6. Set **Max** to 90.

Then:

1. Select `RearSpike Hinge` in the list.

2. Set its Axis X to -1.

3. Keep Y and Z at 0.

4. Keep Grip on positive X.

5. Confirm that `Grip Hinge` and `RearSpike Hinge` appear in the joint list.

Reversing RearSpike's X axis folds it toward the folded head in Compact. These controls fold the grip and rear spike for the compact form in Step 25.

![Step 19: Grip Hinge, Max 90](../images/crescent-rose/en/19-grip-hinge.png){style="max-width:100%;max-height:110mm;width:auto;height:auto"}

*1: Select Grip Hinge. 2: Keep Axis X at 1, Y and Z at 0. 3: Set Max to 90; keep Min at 0.*

![Step 19: RearSpike Hinge with Axis X -1 and Max 90](../images/crescent-rose/en/19-rear-hinge.png){style="max-width:100%;max-height:155mm;width:auto;height:auto"}

*1: Select RearSpike Hinge. 2: Set Axis X to -1. 3: Set Max to 90; keep Min at 0.*

### Step 20 — Magazine and Bolt Slides

For `Magazine`, then `Bolt`:

1. Open **Add Joint → Slide**.

2. Click the part.

3. Press Z.

4. Press Enter.

5. Set **Max** to 0.04 for Magazine or 0.06 for Bolt.

Slides use scene units. A value of 0.06 is 6 cm.

![Step 20: Magazine Slide, Z axis and Max 0.04](../images/crescent-rose/en/20-slides.png){style="max-width:100%;max-height:155mm;width:auto;height:auto"}

*1: Select Magazine Slide after Add Joint > Slide. 2: Use the Z axis (Z = 1, X = Y = 0). 3: Set Max to 0.04; keep Min at 0.*

![Step 20: Bolt Slide, Z axis and Max 0.06](../images/crescent-rose/en/20-bolt-slide.png){style="max-width:100%;max-height:155mm;width:auto;height:auto"}

*1: Select Bolt Slide after Add Joint > Slide. 2: Use the Z axis (Z = 1, X = Y = 0). 3: Set Max to 0.06; keep Min at 0.*

### Step 21 — Pole Slide

1. Open **Add Joint → Slide**.

2. Click `Pole`.

3. Press Z.

4. Press Enter.

5. Set **Max** to 0.6.

6. In **4. Controls**, set `Pole Slide` to 0.6.

7. Inspect the retracted shaft.

8. Reset the control to zero.

Positive values move the pole up into the receiver.

![Step 21: Pole Slide settings, Z axis and Max 0.6](../images/crescent-rose/en/21-pole-slide.png){style="max-width:100%;max-height:155mm;width:auto;height:auto"}

*1: Select Pole Slide after Add Joint > Slide. 2: Use the Z axis (Z = 1, X = Y = 0). 3: Set Max to 0.6; keep Min at 0.*

### Step 22 — Pole Telescope

1. Open **Add Joint → Telescope**.

2. Click `Pole` as the base.

3. Click `ButtSpike` as the segment.

4. Press Enter.

5. Press Z.

6. Press Enter.

7. Set **Length** to 0.2.

8. Test the separate control.

9. Reset the control to zero.

The control moves the spike up to 20 cm along positive Z, into this model's pole.

![Step 22: guided Telescope picks, Pole as base and ButtSpike as segment](../images/crescent-rose/en/22-telescope-pick.png){style="max-width:100%;max-height:155mm;width:auto;height:auto"}

*1: Click Pole as the base. 2: Click ButtSpike as its segment. Press Enter, then Z, then Enter.*

![Step 22: Pole Telescope settings, Z axis and Length 0.2](../images/crescent-rose/en/22-telescope.png){style="max-width:100%;max-height:155mm;width:auto;height:auto"}

*1: Select Pole Telescope. 2: Check Z is its axis. 3: Enter Length 0.2; test the control and restore zero.*

## G. Sequences

### Step 23 — Add Sequence

1. In **3. Sequences**, select **Add Sequence**.

2. Double-click the sequence's name in the list.

3. Type `Scythe to Rifle`.

4. Press Enter.

![Step 23: Add Sequence](../images/crescent-rose/en/23-add-sequence.png){style="max-width:100%;max-height:155mm;width:auto;height:auto"}

*1: Click Add Sequence. 2: Double-click the new name and type Scythe to Rifle. Press Enter.*

### Step 24 — Record a motion group

1. Select **Move Slider to End**.

The sequence slider moves to `100%`. The button becomes Record Step 1.

1. In **4. Controls**, set `BladeTip Hinge` to 70.

2. Set `Blade2 Hinge` to 120.

3. Select Record Step 1.

This stores two target entries, one per moved handle. Both joint sliders reset to zero.

![Step 24: Move Slider to End before posing the first group](../images/crescent-rose/en/24-capture-step.png){style="max-width:100%;max-height:155mm;width:auto;height:auto"}

*1: Click Move Slider to End once. The button changes to Record Step 1.*

![Step 24: Record Step 1 with Blade2 at 120 and BladeTip at 70 degrees](../images/crescent-rose/en/24-record-step.png){style="max-width:100%;max-height:155mm;width:auto;height:auto"}

*1: Enter Blade2 = 120 and BladeTip = 70. 2: Click Record Step 1; both targets are stored and the joint sliders reset.*

*Remaining motion groups.* Recording remains armed after each capture. Do not arm it again. For each remaining group below:

1. Pose the group's handles at the listed values.

2. Select the displayed Record Step button.

| Motion group | Pose these handles | Record button after the preceding groups |
|---|---|---|
| 2 | `Blade1 Hinge` 10 and `PlateL Hinge` 30 | Record Step 3 |
| 3 | `HeadMount Hinge` 90 | Record Step 5 |
| 4 | `Pole Slide` 0.6 | Record Step 6 |

The button number equals the stored target-entry count plus one. Recording two handles advances the number by two. It does not count recording clicks. The four motion groups produce six target entries. If you change which handles move, use the displayed button number.

### Step 25 — The steps

Each recorded target has an entry under the sequence. The entry shows **Target**, ease, **Start** and **End**. Start/End fields use 0-1. Controls sliders show 0-100%.

| Motion | Start | End |
|---|---:|---:|
| Blade folds first | 0 | 0.25 |
| Plates and first segment follow | 0.25 | 0.5 |
| Head folds third | 0.5 | 0.8 |
| Pole moves last | 0.8 | 1 |

Entries in the same motion group use the same Start and End values. For each `Scythe to Rifle` entry:

1. Set **Start** to its motion group's Start value in the table.

2. Set **End** to its motion group's End value in the table.

3. Keep the entry on `Ease In Out`.

Before a step's interval, it keeps its starting value. After the interval, it keeps its end value.

When each sequence is complete, select **Cancel** in the capture banner. Cancel ends recording, retains stored entries and returns that sequence slider to zero. While recording is armed, an overlap warning describes the proposed next recording interval. Do not add an extra empty group.

For the second sequence, use the recording procedure from Step 24:

1. Add `Rifle to Compact`.

2. Select **Move Slider to End** once to arm recording.

3. Set `Grip Hinge` to 90 for the first group.

4. Set `RearSpike Hinge` to 90.

5. Select Record Step 1.

6. For each entry in the first group:

   1. Set **Start** to 0.

   2. Set **End** to 0.5.

7. Set `Magazine Slide` to 0.04 for the second group.

8. Set `Bolt Slide` to 0.06.

9. Select Record Step 3.

10. For each entry in the second group:

    1. Set **Start** to 0.5.

    2. Set **End** to 1.

11. Keep each entry on `Ease In Out`.

12. Select **Cancel** in the capture banner to end recording.

Each group creates two entries. For the second group, the recording button changes from Record Step 1 to Record Step 3.

![Step 25: all six targets and time slices in Scythe to Rifle](../images/crescent-rose/en/25-sequence-steps.png){style="max-width:100%;max-height:155mm;width:auto;height:auto"}

*1: Target is the recorded joint value. 2: Choose Ease In Out. 3: Enter Start. 4: Enter End. Repeat these fields for all six entries using the shown values.*

![Step 25: all four targets and time slices in Rifle to Compact](../images/crescent-rose/en/25-compact-steps.png){style="max-width:100%;max-height:155mm;width:auto;height:auto"}

*1: Grip and RearSpike use Target 90, Start 0, End 0.5. 2: Magazine and Bolt use 0.04 / 0.06, Start 0.5, End 1. Keep Ease In Out.*

![Step 25: end recording with Cancel in the capture banner](../images/crescent-rose/en/25-cancel-capture.png){style="max-width:100%;max-height:135mm;width:auto;height:auto"}

*1: After finishing a sequence, click Cancel in this capture banner to end recording. This keeps the entries and returns the sequence to zero.*

### Step 26 — Test the sequence

**Test**, beside the step-recording button, sweeps the slider from 0% to 100% to 0%. It then restores the slider's value from before the test.

1. From Scythe, select **Test** for `Scythe to Rifle`.

2. With the first sequence at 100%, select **Test** for `Rifle to Compact`.

3. After testing, reset both sequences to 0%.

![Step 26: the sequence Test button during the fold](../images/crescent-rose/en/26-sequence-test.png){style="max-width:100%;max-height:155mm;width:auto;height:auto"}

*1: Click Test beside the recording button. 2: Watch the fold and return. Test Compact with Scythe to Rifle at 100%.*

**What you should be seeing:** The blade curls, the plates close, the head folds down along the receiver, and the pole slides up. Then everything comes back.

## H. Forms

### Step 27 — Save Form

Keep all individual joint sliders at zero. Sequences provide their motion. Setting the selected sequence to its end can arm recording again. Saving a Form does not record another step. Unless you intend to add another target, do not select Record Step.

In **4. Controls**:

1. With every slider at 0, select **Save Form**.

2. Double-click the new list entry.

3. Name it `Scythe`.

4. Set `Scythe to Rifle` to `100%`.

5. Select **Save Form**.

6. Name the new entry `Rifle` using the same naming procedure.

7. Set `Rifle to Compact` to `100%` as well.

8. Select **Save Form**.

9. Name the new entry `Compact`.

To clear the armed state:

1. Select `Scythe` in the form list.

2. Select **Go to Form**.

Both sequences return to zero. Going to Rifle or Compact can arm recording again because the selected sequence is at 100%.

![Step 27: Save Form with every slider at 0](../images/crescent-rose/en/27-save-form.png){style="max-width:100%;max-height:155mm;width:auto;height:auto"}

*1: Start with both sequences and every joint at 0. 2: Click Save Form. 3: Double-click the new list entry and name it Scythe; repeat for Rifle and Compact.*

### Step 28 — Go to Form

1. Select a form in the list.

2. Select **Go to Form**.

**Go and Key** also inserts keys for every control on the current frame. These keys animate the transformation.

![Step 28: Rifle selected, Go to Form](../images/crescent-rose/en/28-go-to-form.png){style="max-width:100%;max-height:155mm;width:auto;height:auto"}

*1: Select the saved form. 2: Click Go to Form. Go and Key also inserts animation keys.*

### Step 29 — The rifle

![Step 29: the Rifle form](../images/crescent-rose/en/29-result-rifle.png){style="max-width:100%;max-height:155mm;width:auto;height:auto"}

*1: Select Rifle. 2: Click Go to Form. 3: Check the sequence percentages against the pictured pose.*

### Step 30 — Compact

![Step 30: the Compact form](../images/crescent-rose/en/30-result-compact.png){style="max-width:100%;max-height:155mm;width:auto;height:auto"}

*1: Select Compact. 2: Click Go to Form. 3: Check the sequence percentages against the pictured pose.*

1. Return to `Scythe`.

2. Save the file.

## What you built

| Record | Bones | What it does |
|---|---|---|
| 15 parts | `MCH-<part>` and `DEF-<part>` | The mesh of each part is parented to its `DEF-` bone |
| 8 Hinges, 3 Slides, 1 Telescope | `CTRL-<part>` | The handles; their values are the sliders in **4. Controls** |
| 1 Piston | `MCH-<part>-aim` and `MCH-<part>-target` | Keep the strut's two parts aimed at each other |
| 1 Follow | none | `PlateR` turns with `PlateL` |
| 2 Sequences | `CTRL-SEQ-<name>` | One slider each |
| 3 Forms | none | Saved slider values |

The refreshed example passed the Rig Validator with no reported issues. It also passed reload checks with Auto Run Python Scripts off, including every individual control and all three Forms.

## Try next

To edit the Follow mapping:

1. Enable **Curve** on `PlateR Follow`.

2. Reshape the mapping in the Graph Editor.

For another pose, save a fourth form, `Carry`, with the blade folded and the head up.

To animate and export:

1. Key the forms over frames with **Go and Key**.

2. Export the `DEF-` bones (see [VRChat Tools](08-vrchat.md)).

## Gear Link

Crescent Rose has no geared pair, so this rig has no Gear Link. A Gear Link turns one Hinge when another turns, according to a tooth ratio. Examples include a crank and wheel or a rack that converts rotation to a slide. See [Gear Link](07-mechanisms.md#gear-link).

## Credits

Crescent Rose model by amandangm, https://sketchfab.com/3d-models/crescent-rose-dcb6bfbb3b824c01a182fa131fe35824, CC BY 4.0. This tutorial uses a split, scaled and rigged version. Crescent Rose is a design of Rooster Teeth Productions. This is a fan-made tutorial asset.

[← Contents](index.md)

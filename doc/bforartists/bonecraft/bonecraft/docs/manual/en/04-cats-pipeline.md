# The CATS Pipeline

[← Contents](index.md)

**Read this before using any CATS tool for the first time.**

The CATS tools provide a recommended preparation workflow. Review the phases in this order. Skip phases your avatar does not need. Before changing mesh or rig data, save a file checkpoint. Inspect each result. Tools remain available when an earlier phase is incomplete.

---

## The Six Phases, In Order

The CATS tab's Pipeline Status lists the phases and checks each one off when it is done:

1. **Fix Model** — Review cleanup options, such as removing duplicates and correcting normals. Inspect the mesh after the operation.

2. **Material Atlas** — Combine the avatar's materials into one texture sheet (optional, for performance).

   1. Keep **Preserve Backup Duplicate** enabled until you review the result.

   2. Select **Analyze Materials**.

   3. Select the sources.

   4. Select **Bake Checked Sources**.

   5. Review the result.

   6. Accept or Revert before another bake.

   See [Material Atlas Combiner](09-cats.md#material-atlas-combiner).

3. **Visemes** — Generate the 15 VRChat lip-sync mouth shapes from your three base shapes (A, O, CH).

4. **Eye Tracking** — Set up VRChat's eye movement with your avatar's eye bones.

5. **Pose to Shape Key** — Capture the mesh's current shape-key mix as a new key. This button does not bake armature-bone deformation. See the [native bone-pose workflow](09-cats.md#save-a-bone-deformed-pose) for that task.

6. **Apply All Transforms** — Apply position, rotation and scale to the mesh and armature. Compare the result before exporting.

---

## Pipeline Status and the Operation Ledger

Pipeline Status shows one line per phase. When a phase finishes, its line shows a checkmark. The scene stores this status with your file.

The Operation Ledger lists each CATS operation, newest last, with its time and outcome. Changed means the operation changed the model. Clean means no changes were necessary. Failed means the operation failed. **Copy** copies the ledger to the clipboard for support requests. **Clear** empties it.

The order is advisory. If an earlier phase is incomplete, tools still run with a warning such as "Run Fix Model first for best results". Review the warning before continuing.

![Pipeline Status lists the six phases in their recommended order.](images/screenshots/bc24-pipeline.png){style="max-width:100%;max-height:155mm;width:auto;height:auto"}

*Native panel popover, BoneCraft 9.2.18. Pipeline Status lists the six phases in their recommended order.*

![Operation Ledger before any entries exist. Copy and Clear act on recorded entries.](images/screenshots/bc24-ledger.png){style="max-width:100%;max-height:155mm;width:auto;height:auto"}

*Native panel popover, BoneCraft 9.2.18. Operation Ledger before any entries exist. Copy and Clear act on recorded entries.*

---

## Why This Order

This order makes it easier to review one type of change at a time:

- **Review cleanup first.** Fix Model can change geometry or remove data, depending on its options. Check the mesh and its existing shape keys before generating more data.

- **Review mouth shapes, then eyes.** Test the generated or mapped visemes. Eye Auto-Detect searches bone names. Check Left Eye and Right Eye assignments separately from bone orientation and constraints.

- **Review expression capture next.** Pose to Shape Key captures a shape-key mix, not bone deformation.

  1. Reset the original key values to 0.

  2. Test the new key at 1.

  To save a bone-deformed pose, use the native workflow linked above.

- **Review transforms before export.** Applying transforms changes object data and resets transform channels. Earlier tools remain available. Compare the result and export settings. To restore the earlier state, use Undo or a saved checkpoint.

---

## Before Skipping a Phase

**Skip Fix Model:**
Inspect the imported geometry, normals, weights, modifiers and existing shape keys. Select the cleanup operations your avatar needs. Check mouth-shape and eye-motion problems separately. An unchecked pipeline phase alone does not identify their cause.

**Skip Visemes:**
Without generated or mapped visemes, your avatar has no lip sync. If viseme shape keys already exist, map them in VRChat Viseme Mapping (Guide 8). Do not generate replacements unnecessarily. Pipeline Status then leaves Visemes unchecked. This is expected.

**Skip Eye Tracking:**
Your avatar has no eye movement in VRChat and stares straight ahead. That is acceptable when it has no eye bones.

**Skip Pose to Shape:**
Optional: skip it if you do not need a snapshot of the current shape-key mix. Existing expressions can be reviewed and used without creating another key.

Next: [Rig Tools](05-rig-tools.md)

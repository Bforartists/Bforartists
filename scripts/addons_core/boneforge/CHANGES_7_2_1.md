# BoneCraft 7.2.1 — Source Reorganization

This release is **non-functional**: every feature, panel, operator,
and scene property behaves identically to 7.1.3. The change set is
entirely about source-tree readability so the next contributor (or
returning author) can find their way around in 30 seconds rather
than 30 minutes.

## What changed

### Folder rename — descriptive categories instead of phase numbers

| 7.1.3 path  | 7.2.1 path             | Owns                                           |
|-------------|------------------------|-----------------------------------------------|
| `phase1/`   | `ui_panels/`           | Bone-collection panel, bookmarks, hotkey popup |
| `phase2/`   | `animation/`           | Pose library, graph tools, Rigify enhance, correctives |
| `phase2b/`  | `weights/`             | Weight mirror / transfer / table, deform control, mush, proximity wrap, shapes lib |
| `phase2c/`  | `advanced_rigging/`    | Rig validator, space-switch, spline IK, ribbons, chain dynamics, viseme, SDK, rig notes |
| `phase3/`   | `autorig/`             | Auto-rigging wizard, retarget, mannequin, skin pipeline |

The other top-level folders (`core`, `i18n`, `io_hub`, `mmd`, `vrm`,
`vrchat`, `taskboard`) were already descriptive and were left alone.

### Manifest IDs preserved

`ToolManifest.id` values (`phase1_panels`, `phase2_animation`,
`phase2b_weights`, `phase2c_advanced`, `phase3_autorig`) are
unchanged. That means the comma-separated list of enabled tools the
add-on persists into `BoneForgePreferences.enabled_tools_csv`
continues to enable the right packages on existing installs.

### Operator and panel `bl_idname` values preserved

No `bl_idname`, no `bl_label`, no scene property name changed. User
hotkeys, saved Asset Browser pose presets, and per-armature custom
properties carry over without migration.

### Bug fix: `ui_panels/__init__.py` (formerly `phase1/__init__.py`)

The `register()` function referenced `collection_ui`, `bookmarks`,
and `hotkey_popup` as bare names without ever importing them, which
would NameError on first register. The function now uses the same
`__import__("{__package__}.{name}", fromlist=[name])` pattern as
every other feature package.

### Documentation

* Top-level `__init__.py` carries a full architecture map of every
  feature package, manifest ids, and the `register` /
  `unregister` sequence with rationale for each step.
* Every feature-package `__init__.py` (`ui_panels`, `animation`,
  `weights`, `advanced_rigging`, `autorig`) carries an inventory of
  its sub-modules and the dependency reason for the registration
  order.
* `core/__init__.py` documents the public API surface, custom-check
  registry, and handler-chain registry.
* Stale `phase1` / `phase2` / `phase2b` / `phase2c` / `phase3`
  references inside docstrings, comments, and string-literal log
  paths were swept to the new package names. Manifest ids are
  intentionally NOT swept (they are stable identifiers).

## What did NOT change

* `bl_info["version"]` bumped from `(7, 1, 3)` to `(7, 2, 1)`.
* All operator `execute()` bodies are byte-for-byte identical to
  7.1.3 except for the import path rewrites.
* No external script that imports `boneforge.core.*` needs to
  change.

## Migration notes for studio code

If a downstream script imports a feature module by its old path:

```python
# 7.1.3
from boneforge.phase2c.rig_validator import run_validate
```

update to:

```python
# 7.2.1+
from boneforge.advanced_rigging.rig_validator import run_validate
```

The `_PHASE_NAMES` constant in the top-level `__init__.py` is still
defined as an alias of `_FEATURE_PACKAGES` so any script that read
the constant by its old name still works.

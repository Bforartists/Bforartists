# Bforartists Merge Week 37 — Documentation & PR Task Sheet

**Merge:** `blender/main` → `merge-week37`
**Merge base:** `669492c955a3a2789efeb69d928b3334dcebb7af`
**Upstream tip merged:** `1fd06ddba68098d2b07466a209b8a7d8a39ffe42`
**BFA HEAD:** `650fc15f790b012419cd188f76b3a4213f9cee7e`
**Scope:** 2,562 files changed, +66,796 / −25,310
**Status:** ✅ Builds clean (`bforartists.exe` + `BlendThumb.dll` link with no errors)

---

## 1. Purpose of this document

This sheet is the working checklist for turning the week-37 upstream merge into:

1. A **pull request** against `bforartists/bforartists` (the code side).
2. **Manual documentation tasks** for `bforartists/manual` (the user-facing side).

> ℹ️ **Automation note:** The workflow `.github/workflows/create_manual_issue.yml` automatically
> opens an issue in `bforartists/manual` when a PR is **merged**. It copies the PR **title** and
> **body** verbatim. Therefore the PR body below must be written so it reads well as a manual
> issue — keep the "Documentation" section explicit and self-contained.

---

## 2. What to report in the PR

### 2.1 PR title (suggested)

```
Merge upstream Blender main into Bforartists (week 37)
```

### 2.2 PR body — copy/paste template

```markdown
## Summary

Weekly upstream sync of `blender/main` into Bforartists.

- Merge base: `669492c955a3a2789efeb69d928b3334dcebb7af`
- Upstream tip: `1fd06ddba68098d2b07466a209b8a7d8a39ffe42`
- Scope: 2,562 files changed (+66,796 / −25,310)
- Build status: ✅ Windows x64 Release builds clean

## Upstream highlights pulled in

- **Core:** type-safe `ListBaseT<T>` first/last accessors (large internal API migration).
- **Paint:** experimental 3D Texture Paint brush migrated out of Sculpt Mode into Texture Paint.
- **UI:** search added to side regions; viewport compositing enabled by default.
- **UI:** markdown labels, `SpaceType` pre/post draw callbacks, enum shortcut assignment.
- **Compositor:** node tree zones in scheduler; text info overlay in node editor.
- **Shader Nodes:** Boolean Math + Integer Math nodes in EEVEE/Cycles.
- **Cycles:** DLSS Ray Reconstruction viewport denoising, anisotropic glass, thin-film dielectric.
- **VSE:** drag-and-drop for text/colors, "Middle" thumbnail option, interactive status bar.
- **glTF:** point-cloud material/vertex-color import, import operator presets.

## Bforartists-specific changes preserved / adapted

- Import/export menus now use upstream `FileHandler.label_with_extensions()` while keeping
  BFA icons and BFA ordering (FBX before OBJ).
- Outliner: kept BFA "Pose Bones (Per Bone)" filter **and** adopted upstream's whole-group
  "Pose Bones" filter — two separate checkboxes with distinct tooltips.
- Outliner: BFA search-visibility preference (`outliner_show_search`) preserved alongside the
  new upstream side-region search.
- Brush: BFA "sync brush size with surface offset" preserved and adapted to the new
  `bke::paint::invalidate_overlay_all(Scene&)` API.
- Region flags: BFA `RGN_FLAG_HIDE_CATEGORY_TABS` moved to bit 14; upstream
  `RGN_FLAG_SEARCH_FILTER_SHOW` kept at bit 13.
- Node overlay: BFA `SN_OVERLAY_SHOW_WORLD_CENTER` moved to bit 10; upstream
  `SN_OVERLAY_SHOW_TEXT_INFO` kept at bit 9.

## Documentation

See the "Documentation tasks" section below — these are the user-facing changes that need
manual updates.

## Testing

- [x] Windows x64 Release build (clean)
- [ ] Linux build
- [ ] macOS build
- [ ] Smoke test: Outliner filters (both Pose Bones checkboxes)
- [ ] Smoke test: import/export menus show file name + extension
- [ ] Smoke test: Texture Paint 3D brush
- [ ] Smoke test: side-region search + BFA category tab hide
```

---

## 3. Documentation tasks (for `bforartists/manual`)

Each task is written so it can be lifted directly into a manual issue. Priority:
🔴 must document · 🟡 should document · 🟢 optional / internal.

### 🔴 TASK-1 — Outliner: two "Pose Bones" filters

**What changed:** The Outliner filter panel now has **two** separate checkboxes:

| Checkbox | RNA property | Behaviour |
|---|---|---|
| **Pose Bones** | `use_filter_pose_bones` | Hides the **entire** Pose Bones group of armatures. |
| **Pose Bones (Per Bone)** | `use_filter_pose_bones_per_bone` | Hides **individual** pose bones, each controlled by its own "Hide in Outliner" toggle in the Bone properties. |

**Why:** BFA already had a per-bone filter; upstream added a whole-group filter. Both are kept
because they do different things.

**Manual action:**
- Update the Outliner → Filter documentation to describe **both** checkboxes.
- Add the tooltips verbatim:
  - *Pose Bones* — "Show or hide the entire Pose Bones group of armatures in the Outliner."
  - *Pose Bones (Per Bone)* — "Hide individual pose bones in the Outliner. Each bone is
    controlled by its own 'Hide in Outliner' toggle in the Bone properties."
- Add a screenshot of the filter panel showing both rows.

**Files:** `scripts/startup/bl_ui/space_outliner.py`,
`source/blender/makesrna/intern/rna_space.cc`,
`source/blender/makesdna/DNA_space_enums.h`

---

### 🔴 TASK-2 — Import/Export menus: file name + extension

**What changed:** All import/export entries in the Topbar **File** menu now use upstream's
`FileHandler.label_with_extensions()` helper. The visible text is unchanged (file name +
extension), but it is now generated dynamically instead of hard-coded.

**Manual action:**
- Verify the manual's File → Import / File → Export lists still match the on-screen labels.
- No wording change expected, but confirm FBX-before-OBJ ordering is still documented as BFA
  order.

**Files:** `scripts/startup/bl_ui/space_topbar.py`,
`scripts/addons_core/io_scene_gltf2/__init__.py`

---

### 🔴 TASK-3 — Texture Paint: experimental 3D brush

**What changed:** The experimental **3D Texture Paint brush** moved **out of Sculpt Mode** and
into **Texture Paint mode**. It also gained support for filtering by face selection.

**Manual action:**
- Move/duplicate the 3D brush documentation from the Sculpt section to the Texture Paint
  section.
- Document the new **face-selection filtering** option.
- Note that the feature is still **experimental** and must be enabled.

**Files:** `scripts/startup/bl_ui/space_view3d_toolbar.py` (upstream feature)

---

### 🔴 TASK-4 — Search in side regions + BFA category tab hide

**What changed:** Upstream added a **search filter** to side regions (Properties, Preferences,
and side panels). BFA additionally keeps its own **category tab region hide** feature.

**Manual action:**
- Document the new side-region search: floating search button, hidden by default, activated
  via shortcut or the panel context menu → **Search**.
- Document BFA's category tab hide separately so the two are not confused.
- Clarify that BFA's Outliner search-visibility preference (`outliner_show_search`) still
  controls the Outliner header search field.

**Files:** `source/blender/makesdna/DNA_screen_types.h`,
`scripts/startup/bl_ui/space_outliner.py`

---

### 🟡 TASK-5 — Brush: sync size with surface offset

**What changed:** BFA's "sync brush size with surface offset" behaviour was preserved and
adapted to the new upstream `bke::paint::invalidate_overlay_all(Scene&)` API. No user-visible
behaviour change.

**Manual action:**
- Confirm the existing Grease Pencil brush documentation for "Sync Radius with Surface Offset"
  is still accurate.
- No new text required unless the option moved in the UI.

**Files:** `source/blender/makesrna/intern/rna_brush.cc`

---

### 🟡 TASK-6 — Properties tabs / Outliner filter list

**What changed:** The Properties editor tab list (`filter_items`) was re-synced with upstream
(21 entries, including the new **Compositor** tab). BFA's stale "Tool tab is hidden" comment
was removed.

**Manual action:**
- Verify the Properties editor tab documentation lists all current tabs in the correct order.
- Add the **Compositor** tab if it is missing.

**Files:** `source/blender/makesrna/intern/rna_space.cc`

---

### 🟢 TASK-7 — Upstream features worth a manual mention

These are upstream-only additions pulled in by the merge. Document only if the manual tracks
them:

- **Viewport compositing enabled by default** (new/empty files & factory settings).
- **Markdown labels** in the UI (`layout.label_markdown`).
- **Boolean Math** and **Integer Math** nodes now available in EEVEE/Cycles shader nodes.
- **Cycles DLSS Ray Reconstruction** for viewport denoising.
- **VSE:** drag-and-drop for text datablocks/files and colors; "Middle" thumbnail option;
  interactive status bar when moving strips.
- **glTF:** point-cloud material & vertex-color import; import operator presets.
- **Viewport:** new `Flip View` operator under View → Navigation.

---

### 🟢 TASK-8 — Internal only (no manual entry)

- `ListBaseT<T>` API migration (`.first`/`.last` members → `first()`/`last()` methods).
- Removal of BFA-local `LISTBASE_FOREACH` macro redefinitions.
- Region/overlay flag bit renumbering.

**Manual action:** none.

---

## 4. Work cut-out checklist

### Code / PR
- [x] Delete leftover merge artifacts: `space_topbar.py.REMOTE.py`, `.LOCAL.py`, `.BASE.py`
- [x] Confirm no conflict markers remain: `git grep -n "^<<<<<<< HEAD"` → empty
- [x] Confirm no unmerged files: `git diff --name-only --diff-filter=U` → empty
- [x] Windows x64 Release build clean
- [ ] Run `clang-format` on touched C/C++ files
- [ ] Run `make format` / `autopep8` on touched Python files
- [ ] Final clean build on Linux + macOS
- [ ] Open PR with the body from §2.2

### Documentation
- [ ] TASK-1 Outliner dual Pose Bones filters 🔴
- [ ] TASK-2 Import/Export menu labels 🔴
- [ ] TASK-3 Texture Paint 3D brush 🔴
- [ ] TASK-4 Side-region search + category tab hide 🔴
- [ ] TASK-5 Brush sync size with surface offset 🟡
- [ ] TASK-6 Properties tabs / filter list 🟡
- [ ] TASK-7 Upstream feature mentions 🟢
- [ ] TASK-8 Internal-only — no action 🟢

---

## 5. Verification commands

```powershell
# No conflict markers anywhere
git grep -n "^<<<<<<< HEAD"

# No unmerged files
git diff --name-only --diff-filter=U

# Files where BFA diverges from upstream (review these for BFA markers)
git diff MERGE_HEAD --name-only -- scripts/startup/bl_ui source/blender/makesdna source/blender/makesrna

# Clean build (Windows)
cmd /c '"C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat" && cd /d C:\3D_Stuff\bfa_build_windows_x64_vc17_Release && ninja'
```

---

## 6. Notes for the next merge

- Upstream removed **all** local `LISTBASE_FOREACH` redefinitions; the macro now lives only in
  `source/blender/blenlib/intern/listbase.cc`. Do not re-add local copies.
- `ListBaseT<T>` range-for yields `T&`, **not** `T*`. Use `for (T &item : list)`.
- Use `list.first_as<U>()` instead of `static_cast<U*>(list.first())`.
- BFA marker comments (`# BFA`, `#bfa`, `/*bfa*/`, `/* bfa*/`) must be added to every
  significant divergence so future merges can find them.

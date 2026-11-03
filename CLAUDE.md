# CLAUDE.md

This repository is **Bforartists**, a fork of Blender focused on UI/usability: its own keymap,
cleaned-up and extended menus, colored icons, left-aligned checkboxes and better defaults.
Files stay fully compatible with Blender. Upstream Blender is merged in roughly weekly.

## Branches and remotes (read this first)

| Branch   | Tracks           | Contents |
|----------|------------------|----------|
| `master` | `origin/master`  | **Bforartists.** All BFA work, PR target. |
| `main`   | `blender/main`   | **Pure upstream Blender**, used only as the merge source. |
| `merge-weekNN` | —          | Temporary branch where `blender/main` is merged into `master`. |
| `<issue#>-<slug>` | —       | Feature/fix branches, e.g. `6093-topbar---workspaces---...` |

- `origin` = https://github.com/Bforartists/Bforartists, `blender` = https://projects.blender.org/blender/blender
- The checkout regularly moves between `master`, `main` and `merge-weekNN` while a merge is in
  progress, so **check `git branch --show-current` (and `git status` for a merge in progress)
  before editing or drawing conclusions.** While `main` is checked out the tree is plain Blender
  (no `bfa_*` add-ons, no merge script, `project(Blender)` in CMake). That's expected mid-merge,
  but BFA changes must never be committed to `main` or pushed from it.
- The merge script runs `git reset --hard` and `git clean -fd` on `main`, which deletes untracked,
  non-ignored files such as an uncommitted `CLAUDE.md`. Commit such files to `master` or list them in
  `.git/info/exclude` first.
- During conflict resolution (`MERGE_HEAD` present), only resolve conflicts. Don't start unrelated
  edits, run `git merge --abort`, or reset without asking.
- `lib/<platform>` are Git submodules with precompiled libraries (`update = none`); a dirty
  `lib/windows_x64` in `git status` is normal and should not be committed.
- Large binaries (`.blend`, images, test files) use **Git LFS**.

## Weekly Blender merge

Automated by `tools/utils/bforartists_merge_blender.py` (exists on `master` and merge branches):

```sh
python tools/utils/bforartists_merge_blender.py --week-number 40              # full run
python tools/utils/bforartists_merge_blender.py --week-number 40 --dry-run    # show phases
python tools/utils/bforartists_merge_blender.py --week-number 40 --resume     # after resolving conflicts
# also: --force (no confirm), --skip-master-update, --blender-remote, --origin-remote
```

Phases: preflight (clean tree, remotes, git-lfs) → update `master` + `make update` → create
`merge-weekNN` from master → reset `main` to `blender/main` + `make update` → `git lfs fetch`
from both remotes → `git merge blender/main` (pauses for conflict resolution; type `ok`) →
`git lfs checkout blender main` then `git lfs checkout origin master` (**BFA version wins** for
shared LFS files) + `git lfs fsck` → status report. Then build, test, `git push origin merge-weekNN`
and `git lfs push --all origin merge-weekNN`, and open a PR into `master`.

When resolving conflicts: keep upstream logic changes, but preserve every hunk carrying a BFA
marker comment (see below). Blender often moves/renames UI code, so BFA edits may need to be
re-applied at the new location rather than simply kept. For interface files, Bforartists (`HEAD`)
wins by default. Frequent conflict hotspots are `scripts/startup/bl_ui/space_view3d.py`,
`source/blender/makesrna/intern/rna_nodetree.cc` and theme files. If a build misbehaves after a
merge, clean the submodules (`git submodule foreach --recursive git reset --hard` / `git clean -fd`).

## Bforartists change conventions

- **Mark every divergence from Blender** with a comment explaining why. Forms used:
  `# BFA - <reason>`, `#bfa`, `# bfa menu`, `// bfa`, `/*bfa*/`, `/* bfa */`, `// bfa end`.
  For any significant change, the comment should say *why* it diverges from Blender, not just
  mark it. That rationale is the only record future mergers have.
  Common examples: `# BFA - Icon Added`, `# BFA - menu`, `# BFA - align left`, `# BFA - not used`.
  These markers are how merges preserve BFA work, so don't drop them and don't make unmarked edits
  to upstream code.
- Upstream code BFA doesn't use is typically commented out with a note (`# BFA - not used`,
  `# BFA - Legacy`) rather than deleted, which keeps merges readable.
- **Checkboxes float left** (checkbox before its label) in both Python and C++ layout code;
  copy the pattern from neighbouring BFA-marked code in the same file.
- Most BFA work is in UI code: `scripts/startup/bl_ui/` (Python menus/panels/headers),
  `scripts/startup/bl_operators/`, `source/blender/editors/`, `source/blender/makesrna/`
  (RNA UI strings/icons), `source/blender/windowmanager/`.
- Icons: SVG sources in `release/datafiles/icons_svg/` (many BFA-only icons), plus
  `release/datafiles/icons/`; geometry icons via `make icons_geom`.
- Keymap: `scripts/presets/keyconfig/Bforartists.py` and `Bforartists-macOS.py`.
- BFA add-ons in `scripts/addons_core/`: `bfa_default_addons` (bundled add-ons/extensions),
  `bfa_default_library` (node asset libraries), `bfa_3Dsequencer`, `bfa_brush_panel`,
  `bfa_find_and_replace`, `bfa_power_user_tools`, `bfa_presentation_slider`,
  `bfa_xray_weight_paint_button`, `smartdelete_bfa.py`. BFA assets live in `assets_bfa/`.
- Versioning: `BFORARTISTS_VERSION`, `_PATCH`, `_CYCLE` in
  `source/blender/blenkernel/BKE_blender_version.h`, alongside Blender's own version (keep both).
- Branding: user-visible "Blender" strings are generally renamed to "Bforartists" (CMake
  project, executable, thumbnailer, app IDs). Keep that in mind when upstream adds new strings.
- Design notes for in-progress features may live in `_misc/` (e.g. `_misc/6780-*.md`).

## Building

Same process as Blender (see https://developer.blender.org/docs/handbook/building_blender/),
but output directories are renamed:

```sh
make update            # fetch lib submodules + LFS (Windows: .\make.bat update)
make                   # Linux/macOS -> ../bfa_build_<os>/bin/bforartists
.\make.bat             # Windows (MSVC) -> ..\bfa_build_windows_<arch>_vc<ver>_<type>\ (Bforartists.sln)
make debug | release | lite | full | ninja   # also usable as make.bat arguments on Windows
make format            # clang-format (C/C++) + autopep8 (Python, config in pyproject.toml)
```

- CMake: out-of-source builds only. On `master`, `enable_testing()` is commented out
  (`# BFA - disable testing`), so CTest/`make test` don't run by default.
- CI (`.github/workflows/{linux,mac,windows}.yml` → `nightly-build.yml`) only checks that
  `master` and PRs into it compile. The `.gitea/` folder is upstream Blender's and unused here.
- Python changes in `scripts/` are copied into the build's install dir on build; rebuild (fast,
  no recompilation) before testing them.

## Code layout (inherited from Blender)

- `source/blender/` — core: `makesdna` (DNA, `.blend` structs; changes need versioning in
  `blenloader`), `makesrna` (RNA / `bpy` property definitions), `blenkernel` (BKE), `blenlib` (BLI),
  `editors` (all editor UI + operators), `windowmanager` (WM), `modifiers`, `nodes`, `draw`, `gpu`,
  `animrig`, `sequencer`, `geometry`, `python`.
- `intern/` — standalone-ish libraries (Cycles, GHOST windowing, guardedalloc, …).
- `extern/` — vendored third-party code. `lib/` — precompiled deps (submodules).
- `scripts/` — Python: `startup/bl_ui` (the UI layout), `startup/bl_operators`, `modules`,
  `addons_core`, `presets`.
- `release/` — datafiles (icons, themes, fonts, splash), platform packaging (`windows/msix`,
  `darwin/Bforartists.app`).
- `tools/` — maintenance/dev scripts; `build_files/` — CMake modules and platform build scripts.
- DNA changes (`DNA_*.h`) are persisted in `.blend` files: they need versioning code in
  `blenloader` and must keep files loadable in Blender, since BFA promises file compatibility.
  Avoid BFA-only DNA changes where a UI-level change suffices.
- Modifiers: `source/blender/modifiers/intern/MOD_*.cc`, each implementing the `ModifierTypeInfo`
  callbacks; copy an existing one as a template.
- Code style: C++ in `blender::` namespace, module prefixes (`BKE_`, `BLI_`, `ED_`, `UI_`, `WM_`,
  `RNA_`), SPDX license header in every file, `.clang-format` / `.editorconfig` at the root.
- Upstream developer docs: https://developer.blender.org/docs/ (most of it applies directly).

## Commits and PRs

Full guide: https://github.com/Bforartists/Bforartists/wiki/Git-Workflow

- Never commit directly to `master`. One branch per task, created from an up-to-date `master` and
  named after the GitHub issue: in practice `<issue#>-<issue-title-slug>` (GitHub's "create branch"
  name, e.g. `6781-3d-view---add---lattive-menu-needs-icon`). One focused task per branch.
- Flow: assign yourself to the issue → branch → implement → **compile to verify** → commit with the
  issue number → PR into `master` → resolve conflicts → update the manual/docs → close the issue
  with the "Fixed" label.
- **PR title:** `<Type>: <Editor> > <Context> > <Location> - <Issue title> #<issue>`, e.g.
  `Icon: 3D View > GreasePencil > Edit Mode - New Deselect Linked operator #6679`.
- **Commit title:** `<Type>: <Title> #<issue>`. PRs are squash-merged, so the PR title becomes the
  commit on `master`.
- Type tags: `Fix:`, `Clean:` (cleanup/refactor), `Feat:`, `Icon:`, `Theme:`, `Asset:`, `Merge:`.
  Upstream commits arriving via merges use Blender's own style (`Fix #123:`, `Cleanup:`, `UI:`);
  don't copy that style for BFA commits.
- Keep history linear when updating a branch (`git pull --rebase`).
- Issue tracker: https://github.com/Bforartists/Bforartists/issues. Issue templates are in
  `.github/ISSUE_TEMPLATE/`. `.github/pull_request_template.md` is currently empty.

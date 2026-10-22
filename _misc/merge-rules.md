# 📏 Merge rules: the reasons

`tools/utils/merge_rules.toml` says **what** happens to a conflicted file; this page says **why**.
When a maintainer decides a 🔴 conflict that could come back, it becomes a rule here, so next week it's 🟢.

| Files | Rule | Why |
|---|---|---|
| `.github/*`, `README.md`, `release/datafiles/splash*` | 🟢 ours | Bforartists identity: our docs, templates and branding |
| `release/datafiles/userdef/userdef_default_theme.c` | 🟢 regenerate | Never merged by hand: regenerate from `Bforartists.xml` (see *Compiling Theme Changes*) |
| `locale/po/*.po` | 🟡 po-splice | Our English strings drifted from Blender's over the years ([#5701](https://github.com/Bforartists/Bforartists/issues/5701)). Keep the Bforartists English entries and take Blender's translation improvements. A Bforartists translation is kept only where Blender's is empty or fuzzy |
| `scripts/addons_core/bl_pkg/*` | 🔴 splice | Bforartists greatly reworked the Extensions UX. Keep it and splice in only Blender's logic. Escalate Blender UX changes |
| `scripts/startup/bl_ui/space_view3d.py` | 🔴 splice | The most-changed file. Start from HEAD and splice Blender's changes in |
| `scripts/startup/bl_ui/*` | 🟡 splice | Interface: Bforartists layout, menu order, icons and left-aligned checkboxes win; Blender's logic is spliced in |
| `scripts/presets/keyconfig/*` | 🔴 splice | The Bforartists keymap is its own |
| `source/blender/makesrna/intern/rna_nodetree.cc` | 🟡 splice | Always conflicts over node header icons: keep ours |
| `source/blender/editors/include/UI_icons.hh` | 🟡 splice | Keep every Bforartists icon entry and add Blender's new ones |
| `source/blender/blenkernel/BKE_blender_version.h` | 🔴 splice | `BFORARTISTS_VERSION*` lives next to Blender's version |
| `release/datafiles/icons_svg/*`, `release/datafiles/icons/*` | 🟡 ours | Bforartists icon art wins. Blender icon changes are reported as 🎨 Art work |
| everything else | 🔴 splice | No rule yet: splice carefully, then add a rule if it repeats |

## How a splice is done

1. Start from Blender's change and work out its **intent**: new logic, renamed property, moved code.
2. Re-apply **every** hunk marked `# BFA` / `// bfa` / `/* bfa */`, at its new location if Blender moved the code.
3. If Blender changed something Bforartists deliberately redesigned (layout, wording, UX), that's a 🔴: **ask**, don't guess.
4. Log what was kept and why in `_merge_runs/weekNN/conflict-log.md` (it goes into the PR).

The guard (`check`) blocks any file that ends up with fewer BFA markers than our side had. To drop a marker on
purpose (for example Blender removed the feature), pass `--allow-marker-loss PATH="reason"`. The reason is logged.

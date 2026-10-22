# 🔀 Weekly Blender merge automation (experimental) · #6930

> **Status:** 🧪 Experimental · **Branch:** [`6930-development---tools---merge---automate-the-weekly-blender-merge-experimental`](https://github.com/Bforartists/Bforartists/tree/6930-development---tools---merge---automate-the-weekly-blender-merge-experimental) · **Tracker:** #6930
> **Started:** 2026-10-21 · The normal manual merge keeps running every week until this proves itself.

> 📍 **Where we are (Oct 21):** phase 1 is written and passes the cloud tests. Next: a shadow merge in a separate checkout on your PC. See [▶️ How to run it](#️-how-to-run-it) and the [✅ Checklist](#-checklist).

## 🎯 Goals

1. **Easy to run, hands off by default.** The script does the work and resolves the conflicts that are clearly easy. It only stops for the ones that need a person, then finishes, pushes and is done. Reporting stays a separate step afterwards, as today.
2. **Easier reporting, easier merging, safer merging.** Keep the Bforartists interface and usability vision alive while taking in Blender's power, so the two stay married and symbiotic.
3. **Dominoes.** Each step starts the next one by itself. A maintainer only steps in where a decision is needed.
4. **Docs that are easy to digest and explicit.** For every step: what starts it, what it does, what it leaves behind, and when you step in.

## 🧭 Principles

- 🧱 **Fewest moving parts.** The existing merge script stays the engine. Only one new script and one rules file are added.
- 🚦 **Gates, not babysitting.** The chain runs until it reaches a gate, and there are only four gates (below).
- 🛡️ **The Bforartists vision is guarded mechanically.** Lost `# BFA` hunks are counted and blocked; they don't depend on someone noticing.
- 🔁 **Every step can be re-run.** Run it again and it continues from where it stopped.
- 🚫 **Never:** commit to `main`, push to `master`, force-push, merge a PR, or abort/reset a merge without asking.

## 🁢 The domino chain

| # | Domino | Starts when | Does | Leaves behind | 🙋 You step in when |
|---|---|---|---|---|---|
| 1 | 🔀 **Merge** | Saturday schedule (or you run it) | Updates `master`, creates `merge-weekNN`, merges `blender/main` (existing script, new `--no-prompt`) | conflict list | never |
| 2 | 📏 **Auto-resolve** | conflicts exist | Applies `merge_rules.toml` (ours / theirs / regenerate). Splice files: Blender's logic plus every BFA-marked hunk, re-applied where code moved | `conflict-log.md` | a 🔴 conflict: a design or usability call |
| 3 | 🛡️ **Guard** | all files resolved | No conflict markers, BFA marker count kept per file, `.py` compiles | `check.md` | never (a failing file goes back to 2) |
| 4 | ✅ **Finish merge** | guard passes | `--resume` (submodules, LFS with BFA winning, `lfs fsck`), commit `Merge: Week NN` | merge commit | never |
| 5 | 🔨 **Build + launch** | merge committed | Deletes the old build folder, `make ninja` (fallback `lite`), launches and opens each workspace, collects Python tracebacks | `build.log`, `smoke.md` | a build error that isn't obviously caused by the merge |
| 6 | ⬆️ **Push** | build + launch OK | `git push origin merge-weekNN` + `git lfs push --all origin merge-weekNN` | pushed branch | never |
| 7 | 📣 **Report** (separate step) | push done | Drafts the PR body (#6835 layout + conflict log), issue and Manual task drafts with screenshots in context | `pr_body.md`, `issues/` drafts | you post, or approve Claude posting |
| 8 | 👀 **Review + merge** | PR open | You test and merge. Claude never merges | | always: this is yours |

### 🚦 The four gates

1. 🔴 A conflict that needs a design or usability decision
2. 🔨 A build error that isn't obviously caused by the merge
3. 📣 Report approval (optional; default stays manual reporting)
4. 👀 PR review and merge

## 🧩 Moving parts

| Part | Change |
|---|---|
| `tools/utils/bforartists_merge_blender.py` | ➕ `--no-prompt`: at conflicts, save state and exit with code 2 instead of waiting at `Ready? [ok/quit]` |
| `tools/utils/bforartists_merge_auto.py` | 🆕 Dominoes 2–7: `run` (the whole chain), plus `resolve`, `check`, `finish`, `build`, `push`, `report`, `status` for re-running one step |
| `tools/utils/merge_rules.toml` | 🆕 Path pattern → `ours` / `theirs` / `splice` / `regenerate` + risk, seeded from the wiki troublemaker table |
| `_merge_runs/weekNN/` | 📁 Generated, git-ignored: `status.json`, conflict copies (base / ours / theirs), logs, drafts |

Plus `_misc/merge-rules.md`: the reason behind every rule.

Later phases add `tools/utils/bfa_ui_probe.py` (screenshots from inside Bforartists, using `screen.screenshot` + `screen.screenshot_area`) and the Saturday scheduling.

## ▶️ How to run it

Run everything from the repo root. `install` copies the tools into `_merge_runs/_tools/`, so they survive the
merge script switching to `main` (which doesn't have them).

```sh
python tools/utils/bforartists_merge_auto.py install              # once, and after updating the tools
python _merge_runs/_tools/bforartists_merge_auto.py run -w 43     # the whole chain; stops at a gate
python _merge_runs/_tools/bforartists_merge_auto.py status        # where are we, what is waiting
python _merge_runs/_tools/bforartists_merge_auto.py run           # continue after you fixed what the gate asked
```

**At a gate** (exit code 3), `_merge_runs/week43/triage.md` lists every conflicted file:

| Icon | Meaning | What to do |
|---|---|---|
| 🤖 | resolved by rule | nothing |
| ✂️ | splice | resolve in place (Blender logic + every BFA hunk), then `run` |
| 🙋 | needs a decision (e.g. one side deleted the file) | resolve, then `decide PATH --note "what and why"`, then `run` |
| ✅ | passed the guard | nothing |

**Useful extras**

- `adopt -w NN`: take over a merge you already started by hand and that's paused at conflicts. It works on your normal merge too.
- `check --allow-marker-loss PATH="reason"`: drop a BFA marker on purpose (logged in the PR).
- `build --target lite` · `build --clean full` (delete the whole build folder) · `build --build-dir PATH`.
- `push`: only when you say so. While experimental, `run` never pushes unless you add `--push`.

**What lands in `_merge_runs/week43/`:** `status.json` · `triage.md` · `conflicts/` (base / ours / theirs) ·
`check.md` · `merge.log` · `build.log` · `smoke.log` + `smoke.md` (launch test) · `pr_body.md` (draft PR text).

## 🛡️ Guard rails for the Bforartists vision

- 🔢 **BFA marker guard:** a file with fewer `# BFA` / `#bfa` / `// bfa` / `/* bfa */` markers than the Bforartists side is blocked.
- 🖼️ **Interface files:** the Bforartists layout wins by default; Blender's logic changes are spliced in.
- 🎨 **Theme:** `userdef_default_theme.c` is never merged; it's regenerated from `Bforartists.xml`.
- 🆕 **New Blender UI** (missing icons, right-aligned checkboxes, new menus) is **reported as work**, never silently restyled during the merge.
- 🔍 **Launch sweep:** Python draw errors from renamed upstream properties are caught before the push.

## 🧪 Test plan (this week)

Your normal merge continues untouched. All testing happens in a **separate checkout**.

| When | What | Who |
|---|---|---|
| ✅ Oct 21 | Write `--no-prompt`, `bforartists_merge_auto.py` (dominoes 1–7), `merge_rules.toml`, `_misc/merge-rules.md` | Claude |
| ✅ Oct 21 | Cloud tests (results below) | Claude |
| Fri Oct 23 | Set up a second checkout (`git worktree` or clone, e.g. `C:\3D_Stuff\bfa_merge_test`) and give Claude folder access | You (5 min) |
| Fri Oct 23 | **Shadow merge:** run the chain on the same week you merged by hand, **no push** | Claude |
| Fri Oct 23 | **Compare** the automated result with your manual merge, file by file → list of misses → new rules | Claude + you |
| Sat Oct 24 | Optional: run the chain again on week 43 in the test checkout, still no push | Claude |
| Later this week | Review together; decide what's next | You |

**Cloud test results (Oct 21)**, on a fake Blender + Bforartists pair with 6 planted conflicts:

- ✅ 3 of 6 resolved by rule: README (ours), theme (regenerate + to-do), `sv.po` (Blender's improved translation, the BFA translation where Blender's was empty, and the BFA-only English entry kept)
- ✅ 2 left to splice (`space_view3d.py`, `bl_pkg`), and 1 delete-vs-modify sent for a decision
- ✅ A splice that dropped a `# BFA` hunk was **blocked**: "BFA markers dropped: 1 in Bforartists, 0 now"
- ✅ After a proper splice + `decide`: staged → `--resume` → `Merge: Week 43` (2 parents) → build → launch test caught a planted Python error → `pr_body.md` drafted → not pushed
- ✅ Re-running finished steps is safe · `adopt` takes over a merge started by hand

**Pass criteria for the shadow merge**

- [ ] Zero lost BFA markers
- [ ] Every 🟢 file matches your manual resolution
- [ ] Every real decision was escalated as 🔴, not guessed
- [ ] Build + launch OK

## 🗺️ Phases

1. 🧱 **Chain core:** dominoes 1–6, shadow-merge tested *(this week)*
2. 📣 **Reporting:** PR body, issue drafts, screenshots in context via `bfa_ui_probe.py`
3. ⏰ **Schedule:** Saturday run + escalations pinged in chat
4. 🗂️ **Assets:** core assets keep BFA thumbnails and usability changes; then online essential assets
5. 🌍 **Share:** PR into `master` and a wiki page, after 2–3 clean weeks

## 📚 Docs plan

- **Wiki page "Weekly Merge Automation"**, one card per domino: *Starts when · Does · Leaves behind · You step in when*.
- The Maintenance page links to it, and its troublemaker table becomes `merge_rules.toml`; each rule's reason lives in `_misc/merge-rules.md`.
- **Weekly Reports page:** add the PR-body and issue-draft steps.

## ❓ Open questions

- ✅ `locale/po/*.po`: keep the Bforartists English, take Blender's translations → `po-splice` rule (#5701)
- ✅ `scripts/addons_core/bl_pkg/*`: heavily reworked Extensions UX → 🔴 `splice`, escalate Blender UX changes
- ⬜ Test checkout location and disk space (a second build folder is large)
- ⬜ `tools/utils/weekly_report.py` exists only in the local checkout. The report step uses it when present: commit it here or on `master`?

## ✅ Checklist

- [x] Tracker issue (#6930, Experimental)
- [x] Branch + this plan
- [x] `--no-prompt` in the merge script
- [x] `bforartists_merge_auto.py` dominoes 1–7 (push off by default)
- [x] `merge_rules.toml` + `_misc/merge-rules.md`
- [x] Cloud tests pass
- [ ] Test checkout + folder access
- [ ] Shadow merge + compare
- [ ] Review together

#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Bforartists Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""
Weekly Blender -> Bforartists merge, as a chain of dominoes (experimental, #6930).

Each step starts the next one by itself. The chain only stops at a gate, where a
maintainer is needed:

    1 merge     -> runs bforartists_merge_blender.py --force --no-prompt
    2 resolve   -> applies merge_rules.toml (ours / theirs / regenerate / po-splice)
                   GATE: files marked "splice" or "escalate" wait for a person (or Claude)
    3 check     -> no conflict markers, no lost BFA markers, .py compiles, .po parses
                   a failing file goes back to step 2
    4 finish    -> merge script --resume (submodules, LFS with BFA winning, fsck),
                   commit "Merge: Week NN"
    5 build     -> clears the old CMake cache, make ninja (or lite), launches Bforartists
                   and visits every workspace and editor, collecting Python errors
                   GATE: build failure or crash on launch
    6 push      -> git push + git lfs push (only with --push)
    7 report    -> drafts pr_body.md (reporting stays a separate, manual step)

Everything for a week lands in _merge_runs/weekNN/ (ignored by git through
.git/info/exclude, so branch switches and `git clean` don't touch it).

Usage:
    python tools/utils/bforartists_merge_auto.py install            # copy tools to _merge_runs/_tools (once per update)
    python _merge_runs/_tools/bforartists_merge_auto.py run -w 43   # the whole chain, stops at a gate
    python _merge_runs/_tools/bforartists_merge_auto.py run         # continue after a gate
    python _merge_runs/_tools/bforartists_merge_auto.py status

    Single steps: merge, adopt (use a merge already in progress), resolve, check [--stage],
    finish, build, push, report.

Exit codes: 0 = done or step finished, 3 = waiting at a gate, 1 = error.
"""

import argparse
import datetime
import fnmatch
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # Python < 3.11
    tomllib = None

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

EXIT_OK = 0
EXIT_ERROR = 1
EXIT_GATE = 3
EXIT_MERGE_CONFLICTS = 2  # from bforartists_merge_blender.py --no-prompt

RUNS_DIR = "_merge_runs"
TOOLS = ("bforartists_merge_blender.py", "bforartists_merge_auto.py", "merge_rules.toml", "weekly_report.py")

# Comment markers that flag a Bforartists change: "# BFA", "#bfa", "// bfa", "/* bfa */" ...
BFA_MARKER = re.compile(r"(?:#|//|/\*)\s*bfa\b", re.IGNORECASE)
CONFLICT_MARKER = re.compile(r"^(?:<{7} |>{7} |<{7}$|>{7}$)", re.MULTILINE)
LFS_POINTER = b"version https://git-lfs.github.com/spec"

AUTO_ACTIONS = ("ours", "theirs", "regenerate", "po-splice")
MANUAL_ACTIONS = ("splice", "escalate")

# Area types visited by the launch test (Bforartists editors).
UI_TYPES = (
    "VIEW_3D", "IMAGE_EDITOR", "UV", "ShaderNodeTree", "CompositorNodeTree", "TextureNodeTree",
    "GeometryNodeTree", "SEQUENCE_EDITOR", "CLIP_EDITOR", "DOPESHEET", "TIMELINE", "FCURVES",
    "DRIVERS", "NLA_EDITOR", "TEXT_EDITOR", "CONSOLE", "INFO", "OUTLINER", "PROPERTIES",
    "FILES", "ASSETS", "SPREADSHEET", "PREFERENCES",
)


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------

def say(icon, text):
    print(f"{icon}  {text}", flush=True)


def now():
    return datetime.datetime.now().isoformat(timespec="seconds")


def git(*args, check=True, binary=False, input=None, cwd=None):
    """Run git and return stdout (str, or bytes when binary=True)."""
    proc = subprocess.run(
        ["git", *args], cwd=cwd, input=input, capture_output=True,
        **({} if binary else {"text": True, "encoding": "utf-8", "errors": "replace"}),
    )
    if check and proc.returncode != 0:
        err = proc.stderr if not binary else proc.stderr.decode("utf-8", "replace")
        raise RuntimeError(f"git {' '.join(args)} failed:\n{err}")
    return proc.stdout


def stream(cmd, log_path, cwd=None, timeout=None):
    """Run a command, echo its output and append it to a log file. Returns the exit code."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "a", encoding="utf-8") as log:
        log.write(f"\n### {now()} $ {' '.join(map(str, cmd))}\n")
        proc = subprocess.Popen(
            [str(c) for c in cmd], cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL, text=True, encoding="utf-8", errors="replace",
        )
        try:
            for line in proc.stdout:
                sys.stdout.write(line)
                log.write(line)
            return proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            proc.kill()
            log.write("\n### TIMEOUT\n")
            return 124


def repo_root():
    return Path(git("rev-parse", "--show-toplevel").strip())


def unmerged_files(root):
    out = git("diff", "--name-only", "--diff-filter=U", cwd=root)
    return [l for l in out.splitlines() if l]


def merge_in_progress(root):
    return subprocess.run(["git", "rev-parse", "-q", "--verify", "MERGE_HEAD"], cwd=root,
                          capture_output=True).returncode == 0


# ---------------------------------------------------------------------------
# Run folder and state
# ---------------------------------------------------------------------------

class Run:
    """Everything about one week's merge, persisted in _merge_runs/weekNN/status.json."""

    def __init__(self, root, week):
        self.root = root
        self.week = week
        self.dir = root / RUNS_DIR / f"week{week}"
        self.dir.mkdir(parents=True, exist_ok=True)
        self.status_path = self.dir / "status.json"
        if self.status_path.exists():
            self.data = json.loads(self.status_path.read_text(encoding="utf-8"))
        else:
            self.data = {"week": week, "branch": f"merge-week{week}", "state": "new",
                         "conflicts": {}, "allow_marker_loss": {}, "gates": [], "history": []}

    @property
    def state(self):
        return self.data["state"]

    def set_state(self, state, note=""):
        self.data["state"] = state
        self.data["gates"] = []
        self.data["history"].append({"at": now(), "state": state, "note": note})
        self.save()
        (self.root / RUNS_DIR / "current.json").write_text(json.dumps({"week": self.week}), encoding="utf-8")

    def gate(self, reason, items=()):
        self.data["gates"] = [{"at": now(), "reason": reason, "items": list(items)}]
        self.save()

    def save(self):
        tmp = self.status_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.data, indent=2, ensure_ascii=False), encoding="utf-8")
        tmp.replace(self.status_path)

    def conflict_copy(self, path, stage):
        return self.dir / "conflicts" / f"{path}.{stage}"


def current_week(root):
    p = root / RUNS_DIR / "current.json"
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))["week"]
    return None


def ensure_excluded(root):
    """Keep _merge_runs/ out of git on every branch (survives checkout of main + git clean -fd)."""
    exclude = Path(git("rev-parse", "--git-path", "info/exclude", cwd=root).strip())
    if not exclude.is_absolute():
        exclude = root / exclude
    exclude.parent.mkdir(parents=True, exist_ok=True)
    text = exclude.read_text(encoding="utf-8") if exclude.exists() else ""
    if f"/{RUNS_DIR}/" not in text.splitlines():
        with open(exclude, "a", encoding="utf-8") as f:
            f.write(("" if text.endswith("\n") or not text else "\n") + f"/{RUNS_DIR}/\n")


def tools_dir(root):
    return root / RUNS_DIR / "_tools"


def merge_script(root):
    p = tools_dir(root) / "bforartists_merge_blender.py"
    return p if p.exists() else root / "tools" / "utils" / "bforartists_merge_blender.py"


# ---------------------------------------------------------------------------
# Rules
# ---------------------------------------------------------------------------

def load_rules(root):
    for p in (tools_dir(root) / "merge_rules.toml", root / "tools" / "utils" / "merge_rules.toml"):
        if p.exists():
            if tomllib is None:
                raise SystemExit("Python 3.11+ is needed to read merge_rules.toml")
            with open(p, "rb") as f:
                return tomllib.load(f)
    return {"rule": [], "default": {"action": "splice", "risk": "high"}}


def match_rule(rules, path):
    for rule in rules.get("rule", []):
        if fnmatch.fnmatchcase(path, rule["path"]):
            return rule
    d = dict(rules.get("default", {"action": "splice", "risk": "high"}))
    d.setdefault("path", "(default)")
    return d


# ---------------------------------------------------------------------------
# .po splice: Bforartists English entries stay, Blender's translations win
# ---------------------------------------------------------------------------

def po_entries(text):
    entries, cur = [], []
    for line in text.splitlines():
        if line.strip():
            cur.append(line)
        elif cur:
            entries.append(cur)
            cur = []
    if cur:
        entries.append(cur)
    return entries


def po_key(entry):
    obsolete, parts = False, []
    for line in entry:
        s = line
        if s.startswith("#~"):
            obsolete, s = True, s[2:].lstrip()
        elif s.startswith("#"):
            continue
        if s.startswith("msgstr"):
            break
        parts.append(s)
    return obsolete, "\n".join(parts)


def po_translated(entry):
    in_str, text = False, ""
    for line in entry:
        s = line[2:].lstrip() if line.startswith("#~") else line
        if s.startswith("#"):
            continue
        if s.startswith("msgstr"):
            in_str = True
            s = s.split(" ", 1)[1] if " " in s else ""
        elif not s.startswith('"'):
            in_str = False
        if in_str:
            text += s.strip().strip('"')
    return bool(text) and not any(l.startswith("#,") and "fuzzy" in l for l in entry)


def po_splice(ours, theirs):
    """Blender's file and translations, plus Bforartists-only English entries."""
    ours_e, theirs_e = po_entries(ours), po_entries(theirs)
    ours_by_key = {po_key(e): e for e in ours_e}
    theirs_keys = set()
    out, stats = [], {"blender": 0, "bfa_translation_kept": 0, "bfa_only_added": 0}
    for e in theirs_e:
        k = po_key(e)
        theirs_keys.add(k)
        o = ours_by_key.get(k)
        if o is not None and not po_translated(e) and po_translated(o) and k[1] != 'msgid ""':
            out.append(o)
            stats["bfa_translation_kept"] += 1
        else:
            out.append(e)
            stats["blender"] += 1
    for e in ours_e:
        k = po_key(e)
        if k not in theirs_keys and not k[0] and k[1]:
            out.append(e)
            stats["bfa_only_added"] += 1
    return "\n\n".join("\n".join(e) for e in out) + "\n", stats


def po_sane(text):
    """Cheap structural check when msgfmt is not installed."""
    for i, e in enumerate(po_entries(text)):
        lines = [l for l in e if not l.startswith("#") or l.startswith("#~")]
        if lines and not any(re.match(r"(#~\s*)?msgid\b", l) for l in lines):
            return f"entry {i + 1} has no msgid"
        for l in lines:
            s = l[2:].lstrip() if l.startswith("#~") else l
            if len(re.findall(r'(?<!\\)"', s)) % 2:
                return f"entry {i + 1}: unbalanced quotes: {l[:60]}"
    return None


# ---------------------------------------------------------------------------
# Domino 1: merge (or adopt a merge already in progress)
# ---------------------------------------------------------------------------

def export_conflicts(run):
    root = run.root
    files = unmerged_files(root)
    rules = load_rules(root)
    for path in files:
        entry = {"stages": {}, "rule": None, "state": "open", "by": "", "note": ""}
        for num, name in ((1, "base"), (2, "ours"), (3, "theirs")):
            proc = subprocess.run(["git", "show", f":{num}:{path}"], cwd=root, capture_output=True)
            if proc.returncode != 0:
                entry["stages"][name] = False
                continue
            data = proc.stdout
            if data.startswith(LFS_POINTER):
                smudged = subprocess.run(["git", "lfs", "smudge", "--", path], cwd=root,
                                         input=data, capture_output=True)
                if smudged.returncode == 0:
                    data = smudged.stdout
            dest = run.conflict_copy(path, name)
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(data)
            entry["stages"][name] = True
        rule = match_rule(rules, path)
        entry["rule"] = {k: rule.get(k, "") for k in ("path", "action", "risk", "note")}
        ours = run.conflict_copy(path, "ours")
        entry["bfa_markers_ours"] = (len(BFA_MARKER.findall(ours.read_text("utf-8", "replace")))
                                     if ours.exists() else 0)
        run.data["conflicts"][path] = entry
    run.save()
    return files


def step_merge(run, args):
    root = run.root
    ensure_excluded(root)
    if merge_in_progress(root):
        return step_adopt(run, args)
    cmd = [sys.executable, merge_script(root), "--week-number", run.week, "--force", "--no-prompt"]
    if args.skip_master_update:
        cmd.append("--skip-master-update")
    for opt in ("blender_remote", "origin_remote"):
        if getattr(args, opt, None):
            cmd += [f"--{opt.replace('_', '-')}", getattr(args, opt)]
    say("🔀", f"Domino 1 · merge Blender main into {run.data['branch']}")
    code = stream(cmd, run.dir / "merge.log", cwd=root)
    if code == EXIT_MERGE_CONFLICTS:
        files = export_conflicts(run)
        run.set_state("conflicts", f"{len(files)} conflicted files")
        say("⚠️", f"{len(files)} conflicted files saved to {run.dir / 'conflicts'}")
        return EXIT_OK
    if code != 0:
        run.set_state("error", f"merge script exited with {code}")
        run.gate("merge script failed, see merge.log")
        say("❌", f"Merge script failed (exit {code}), see {run.dir / 'merge.log'}")
        return EXIT_GATE
    run.set_state("merged-clean", "no conflicts")
    say("✅", "Merged with no conflicts")
    return EXIT_OK


def step_adopt(run, args):
    """Take over a merge that is already paused at conflicts (e.g. started by hand)."""
    root = run.root
    ensure_excluded(root)
    if not merge_in_progress(root):
        say("❌", "No merge in progress to adopt")
        return EXIT_ERROR
    files = export_conflicts(run)
    run.set_state("conflicts", f"adopted merge in progress, {len(files)} conflicted files")
    say("📥", f"Adopted the merge in progress: {len(files)} conflicted files")
    return EXIT_OK


# ---------------------------------------------------------------------------
# Domino 2: resolve by rule
# ---------------------------------------------------------------------------

def take_side(root, path, side, present):
    if present:
        git("checkout", f"--{side}", "--", path, cwd=root)
    else:
        target = root / path
        if target.exists():
            target.unlink()


def step_resolve(run, args):
    root = run.root
    say("📏", "Domino 2 · resolve by rule")
    log = []
    for path, c in sorted(run.data["conflicts"].items()):
        if c["state"] != "open":
            continue
        action = c["rule"]["action"]
        st = c["stages"]
        one_side_deleted = not (st.get("ours") and st.get("theirs"))
        if one_side_deleted and action not in ("ours", "theirs"):
            gone = "Bforartists" if not st.get("ours") else "Blender"
            c.update(state="needs-you", note=f"{gone} deleted this file, the other side changed it")
            continue
        try:
            if action in ("ours", "regenerate"):
                take_side(root, path, "ours", st.get("ours"))
                c.update(state="auto", by="rules")
                if action == "regenerate":
                    c["note"] = c["rule"].get("note") or "Kept ours; regenerate from source after the merge"
            elif action == "theirs":
                take_side(root, path, "theirs", st.get("theirs"))
                c.update(state="auto", by="rules")
            elif action == "po-splice":
                if True:
                    ours = run.conflict_copy(path, "ours").read_text("utf-8")
                    theirs = run.conflict_copy(path, "theirs").read_text("utf-8")
                    merged, stats = po_splice(ours, theirs)
                    (root / path).write_text(merged, encoding="utf-8", newline="\n")
                    c.update(state="auto", by="rules",
                             note=(f"Blender translations: {stats['blender']}, BFA translations kept: "
                                   f"{stats['bfa_translation_kept']}, BFA-only English entries: "
                                   f"{stats['bfa_only_added']}"))
            elif action == "splice":
                c.update(state="to-splice")
            else:
                c.update(state="needs-you", note=c["rule"].get("note", ""))
        except Exception as ex:  # keep going; this file becomes a gate
            c.update(state="needs-you", note=f"auto-resolve failed: {ex}")
        log.append((path, c))
    run.save()
    waiting = [p for p, c in run.data["conflicts"].items() if c["state"] in ("to-splice", "needs-you")]
    auto = sum(1 for c in run.data["conflicts"].values() if c["state"] == "auto")
    say("✅", f"{auto} resolved by rule")
    if waiting:
        run.set_state("needs-resolution", f"{len(waiting)} files need splicing or a decision")
        run.gate("Splice or decide these files, then run `run` again", waiting)
        write_triage(run)
        say("🙋", f"{len(waiting)} files wait for a person or Claude, see {run.dir / 'triage.md'}")
        return EXIT_GATE
    run.set_state("resolved", "all files resolved by rule")
    write_triage(run)
    return EXIT_OK


RISK_ICON = {"low": "🟢", "medium": "🟡", "high": "🔴"}
STATE_ICON = {"open": "⬜", "auto": "🤖", "to-splice": "✂️", "needs-you": "🙋", "decided": "🗳️", "passed": "✅"}


def write_triage(run):
    rows = []
    for path, c in sorted(run.data["conflicts"].items(), key=lambda kv: (kv[1]["rule"]["risk"] != "high", kv[0])):
        r = c["rule"]
        rows.append(f"| {STATE_ICON.get(c['state'], '')} {c['state']} | `{path}` | {RISK_ICON.get(r['risk'], '')} "
                    f"{r['risk']} | {r['action']} | {c.get('by', '')} | {c.get('note') or r.get('note', '')} |")
    text = (f"# Week {run.week} · conflict triage\n\n"
            f"Updated {now()} · state `{run.state}`\n\n"
            "Legend: 🤖 resolved by rule · ✂️ splice (Blender logic + every BFA-marked hunk) · "
            "🙋 needs a decision · 🗳️ decided · ✅ passed check\n\n"
            "| State | File | Risk | Rule | By | Note |\n|---|---|---|---|---|---|\n" + "\n".join(rows) + "\n\n"
            "✂️ files: resolve in place, then `run`. 🙋 files: resolve, then "
            "`decide PATH --note \"what was kept and why\"`, then `run`.\n")
    (run.dir / "triage.md").write_text(text, encoding="utf-8")


# ---------------------------------------------------------------------------
# Domino 3: guard
# ---------------------------------------------------------------------------

def check_file(run, path, c):
    root = run.root
    target = root / path
    problems = []
    if not target.exists():
        if c["state"] not in ("auto", "decided", "passed"):
            problems.append("file is missing; record it with `decide` if the deletion is intended")
        return problems
    raw = target.read_bytes()
    if raw.startswith(LFS_POINTER) or b"\0" in raw[:8000]:
        return problems  # binary / LFS: nothing to read
    text = raw.decode("utf-8", "replace")
    if CONFLICT_MARKER.search(text):
        problems.append("conflict markers left")
    ours_n = c.get("bfa_markers_ours", 0)
    now_n = len(BFA_MARKER.findall(text))
    if now_n < ours_n and path not in run.data["allow_marker_loss"]:
        problems.append(f"BFA markers dropped: {ours_n} in Bforartists, {now_n} now")
    if path.endswith(".py") and not problems:
        try:
            compile(text, path, "exec")
        except SyntaxError as ex:
            problems.append(f"Python syntax error line {ex.lineno}: {ex.msg}")
    if path.endswith(".po") and not problems:
        if shutil.which("msgfmt"):
            p = subprocess.run(["msgfmt", "--check-format", "-o", os.devnull, str(target)],
                               capture_output=True, text=True, encoding="utf-8", errors="replace")
            if p.returncode != 0:
                problems.append("msgfmt: " + p.stderr.strip().splitlines()[0][:200])
        else:
            err = po_sane(text)
            if err:
                problems.append(err)
    return problems


def step_check(run, args):
    root = run.root
    say("🛡️", "Domino 3 · guard")
    for spec in getattr(args, "allow_marker_loss", None) or []:
        path, _, reason = spec.partition("=")
        run.data["allow_marker_loss"][path] = reason or "approved"
    failed, passed = {}, []
    for path, c in sorted(run.data["conflicts"].items()):
        if c["state"] in ("needs-you", "open"):
            failed[path] = ["waiting for a decision: " + (c.get("note") or "record it with `decide`")]
            continue
        problems = check_file(run, path, c)
        c["check"] = problems
        if problems:
            failed[path] = problems
        else:
            c["state"] = "passed"
            passed.append(path)
    run.save()
    lines = [f"# Week {run.week} · check\n", f"{now()} · {len(passed)} passed · {len(failed)} not ready\n"]
    for path, probs in failed.items():
        lines.append(f"- ❌ `{path}`: " + "; ".join(probs))
    if run.data["allow_marker_loss"]:
        lines.append("\n## Approved BFA marker loss\n")
        lines += [f"- `{p}`: {r}" for p, r in run.data["allow_marker_loss"].items()]
    (run.dir / "check.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    write_triage(run)

    if args.stage and passed:
        for path in passed:
            if (root / path).exists():
                git("add", "--", path, cwd=root)
            else:
                git("rm", "-q", "--cached", "--ignore-unmatch", "--", path, cwd=root)
        say("➕", f"Staged {len(passed)} files")
    if failed:
        run.set_state("needs-resolution", f"{len(failed)} files not ready")
        run.gate("Fix these files, then run `run` again", list(failed))
        for path, probs in failed.items():
            say("❌", f"{path}: {'; '.join(probs)}")
        return EXIT_GATE
    if args.stage and unmerged_files(root):
        left = unmerged_files(root)
        run.gate("Unmerged files that were not in the conflict list", left)
        say("❌", f"Still unmerged: {left[:10]}")
        return EXIT_GATE
    if args.stage:
        run.set_state("checked", f"{len(passed)} files passed and staged")
    say("✅", f"{len(passed)} files passed")
    return EXIT_OK


# ---------------------------------------------------------------------------
# Domino 4: finish the merge
# ---------------------------------------------------------------------------

def step_finish(run, args):
    root = run.root
    say("✅", "Domino 4 · finish the merge")
    if unmerged_files(root):
        say("❌", "Unmerged files remain; run check --stage first")
        return EXIT_GATE
    clean_merge = run.state == "merged-clean"
    if not clean_merge:
        cmd = [sys.executable, merge_script(root), "--week-number", run.week, "--resume", "--force", "--no-prompt"]
        code = stream(cmd, run.dir / "merge.log", cwd=root)
        if code != 0:
            run.gate(f"merge script --resume exited with {code}, see merge.log")
            return EXIT_GATE
    # Stage what LFS checkout (BFA bias) rewrote; never the precompiled lib submodules.
    git("add", "-u", "--", ".", ":(exclude)lib", cwd=root)
    message = f"Merge: Week {run.week}"
    if merge_in_progress(root):
        git("commit", "-q", "-m", message, cwd=root)
    elif git("status", "--porcelain", "-uno", "--", ".", ":(exclude)lib", cwd=root).strip() or clean_merge:
        # Clean merge: git already committed; fold the LFS bias in and use our title.
        git("commit", "-q", "--amend", "-m", message, cwd=root)
    head = git("rev-parse", "--short", "HEAD", cwd=root).strip()
    run.data["merge_commit"] = head
    run.set_state("committed", f"{message} at {head}")
    say("📌", f"{message} committed at {head}")
    return EXIT_OK


# ---------------------------------------------------------------------------
# Domino 5: build + launch test
# ---------------------------------------------------------------------------

SMOKE_SCRIPT = r'''
import bpy, traceback
UI_TYPES = %(ui_types)r
plan = [("workspace", w.name) for w in bpy.data.workspaces] + [("editor", t) for t in UI_TYPES]
state = {"i": 0}

def log(msg):
    print("BFA_SMOKE: " + msg, flush=True)

def step():
    try:
        win = bpy.context.window_manager.windows[0]
        if state["i"] < len(plan):
            kind, value = plan[state["i"]]
            state["i"] += 1
            if kind == "workspace":
                win.workspace = bpy.data.workspaces[value]
            else:
                area = max(win.screen.areas, key=lambda a: a.width * a.height)
                try:
                    area.ui_type = value
                except Exception as ex:
                    log("cannot open editor %%s: %%s" %% (value, ex))
            log("%%s %%s" %% (kind, value))
            return 0.6
        log("DONE")
    except Exception:
        traceback.print_exc()
        log("DONE-WITH-ERROR")
    bpy.ops.wm.quit_blender()
    return None

bpy.app.timers.register(step, first_interval=3.0)
'''


def build_dir_for(root, target, override=None):
    if override:
        return Path(override)
    parent = root.parent
    if sys.platform == "win32":
        pattern = "bfa_build_windows_Lite_x64_vc*_Release" if target == "lite" else "bfa_build_windows_x64_vc*_Release"
    elif sys.platform == "darwin":
        pattern = "bfa_build_darwin_lite" if target == "lite" else "bfa_build_darwin"
    else:
        pattern = "bfa_build_linux_lite" if target == "lite" else "bfa_build_linux"
    found = sorted(parent.glob(pattern))
    return found[-1] if found else None


def find_binary(build_dir):
    names = ("bforartists.exe", "Bforartists.exe") if sys.platform == "win32" else ("bforartists", "Bforartists")
    for name in names:
        for p in sorted((build_dir / "bin").rglob(name)):
            if p.is_file():
                return p
    return None


def step_build(run, args):
    root = run.root
    target = args.target or "ninja"
    say("🔨", f"Domino 5 · clean build ({target}) + launch test")
    bdir = build_dir_for(root, target, args.build_dir)
    if bdir and bdir.exists() and args.clean != "none":
        if args.clean == "full":
            say("🧹", f"Deleting {bdir}")
            shutil.rmtree(bdir, ignore_errors=True)
        else:
            for pat in ("CMakeCache.txt", "build.ninja", "*.sln"):
                for p in bdir.glob(pat):
                    say("🧹", f"Removing {p}")
                    p.unlink(missing_ok=True)
    targets = ["lite", "ninja"] if target == "lite" else ["ninja"]
    cmd = (["cmd", "/c", "make.bat", *targets] if sys.platform == "win32" else ["make", *targets])
    code = stream(cmd, run.dir / "build.log", cwd=root)
    if code != 0:
        tail = (run.dir / "build.log").read_text("utf-8", "replace").splitlines()[-40:]
        run.data["build"] = {"ok": False, "exit": code, "tail": tail}
        run.set_state("build-failed", f"make exited with {code}")
        run.gate("Build failed: fix if caused by the merge, otherwise decide", tail[-10:])
        say("❌", f"Build failed (exit {code}), see {run.dir / 'build.log'}")
        return EXIT_GATE
    bdir = build_dir_for(root, target, args.build_dir)
    exe = find_binary(bdir) if bdir else None
    run.data["build"] = {"ok": True, "dir": str(bdir), "exe": str(exe) if exe else ""}
    if not exe:
        run.set_state("build-failed", "no Bforartists binary found")
        run.gate("Build finished but no binary was found; pass --build-dir")
        return EXIT_GATE
    return smoke_test(run, exe)


def smoke_test(run, exe):
    script = run.dir / "smoke_test.py"
    script.write_text(SMOKE_SCRIPT % {"ui_types": UI_TYPES}, encoding="utf-8")
    log_path = run.dir / "smoke.log"
    log_path.unlink(missing_ok=True)
    say("🚀", f"Launching {exe.name} for the UI sweep")
    code = stream([exe, "--factory-startup", "--python", script], log_path, timeout=900)
    text = log_path.read_text("utf-8", "replace")
    errors, lines = [], text.splitlines()
    for i, line in enumerate(lines):
        if line.startswith("Traceback (most recent call last)"):
            j = i + 1
            while j < len(lines) and (lines[j].startswith(" ") or not lines[j].strip()):
                j += 1
            where = next((l.strip() for l in reversed(lines[i:j]) if l.strip().startswith('File "')), "")
            errors.append(f"{lines[j].strip() if j < len(lines) else '?'} ({where})")
    done = "BFA_SMOKE: DONE" in text
    unique = sorted(set(errors))
    md = [f"# Week {run.week} · launch test\n", f"Binary: `{exe}` · exit {code} · finished: {'yes' if done else 'NO'}\n",
          f"Python errors: {len(errors)} ({len(unique)} unique)\n"]
    md += [f"- `{e}`" for e in unique]
    (run.dir / "smoke.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    run.data["smoke"] = {"exit": code, "done": done, "errors": unique}
    if not done:
        run.set_state("build-failed", "Bforartists did not finish the launch test")
        run.gate("Launch test did not finish (crash or hang), see smoke.log")
        say("❌", "Launch test did not finish")
        return EXIT_GATE
    run.set_state("built", f"build OK, {len(unique)} unique Python errors on launch")
    say("✅" if not unique else "⚠️", f"Build OK · launch test finished · {len(unique)} unique Python errors (smoke.md)")
    return EXIT_OK


# ---------------------------------------------------------------------------
# Domino 6: push  ·  Domino 7: report draft
# ---------------------------------------------------------------------------

def step_push(run, args):
    root = run.root
    branch = run.data["branch"]
    remote = args.origin_remote or "origin"
    say("⬆️", f"Domino 6 · push {branch}")
    for cmd in (["git", "push", remote, branch], ["git", "lfs", "push", "--all", remote, branch]):
        code = stream(cmd, run.dir / "push.log", cwd=root)
        if code != 0:
            code = stream(cmd, run.dir / "push.log", cwd=root)  # one retry
        if code != 0:
            run.gate(f"`{' '.join(cmd)}` failed twice, see push.log (never force-pushed)")
            return EXIT_GATE
    run.set_state("pushed", f"{branch} pushed to {remote}")
    return EXIT_OK


def step_report(run, args):
    root = run.root
    say("📣", "Domino 7 · draft the PR text")
    rows, todo = [], []
    for path, c in sorted(run.data["conflicts"].items()):
        r = c["rule"]
        rows.append(f"| `{path}` | {RISK_ICON.get(r['risk'], '')} {r['action']} | {c.get('by') or 'manual'} | "
                    f"{c.get('note') or r.get('note', '')} |")
        if r["action"] == "regenerate":
            todo.append(f"- [ ] Regenerate `{path}` ({c.get('note')})")
    smoke = run.data.get("smoke", {})
    for e in smoke.get("errors", []):
        todo.append(f"- [ ] Launch error: `{e}`")
    log_extra = (run.dir / "conflict-log.md")
    changelog = ""
    wr = next((p for p in (tools_dir(root) / "weekly_report.py", root / "tools" / "utils" / "weekly_report.py")
               if p.exists()), None)
    if wr:
        p = subprocess.run([sys.executable, wr, "--print"], cwd=root, capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
        changelog = p.stdout.strip() if p.returncode == 0 else ""
    body = [
        f"Merge of Blender main into Bforartists, week {run.week}.",
        "",
        "## ✨ New Features (from Blender)",
        "_Fill in from the changelog below._",
        "",
        "## 🧡 Bforartists Changes",
        "_What the merge kept or adapted._",
        "",
        "## 🧪 Please Test",
        "- [ ] Opens with factory settings and your own startup file",
        "- [ ] Menus and panels touched by the conflicts below",
        "",
        "## 📌 Small To-Dos",
        *(todo or ["- [ ] None found automatically"]),
        "",
        "## 🔀 Conflict log",
        "| File | Rule | Resolved by | Note |",
        "|---|---|---|---|",
        *rows,
        "",
        log_extra.read_text("utf-8") if log_extra.exists() else "",
        "## 🔨 Build and launch",
        f"- Build: {'OK' if run.data.get('build', {}).get('ok') else 'not run / failed'}",
        f"- Launch test: {'finished' if smoke.get('done') else 'not run'} · "
        f"{len(smoke.get('errors', []))} unique Python errors",
        "",
        "## 📰 Upstream changelog",
        changelog or "_Run tools/utils/weekly_report.py and paste the result._",
    ]
    (run.dir / "pr_body.md").write_text("\n".join(body) + "\n", encoding="utf-8")
    run.set_state("reported", "pr_body.md drafted")
    say("📝", f"PR text drafted: {run.dir / 'pr_body.md'} · title: Merge: Week {run.week}")
    return EXIT_OK


# ---------------------------------------------------------------------------
# The chain
# ---------------------------------------------------------------------------

def step_run(run, args):
    """Topple dominoes until done or a gate."""
    steps = {
        "new": step_merge,
        "error": step_merge,
        "conflicts": step_resolve,
        "needs-resolution": lambda r, a: step_check(r, _with(a, stage=True)),
        "resolved": lambda r, a: step_check(r, _with(a, stage=True)),
        "checked": step_finish,
        "merged-clean": step_finish,
        "committed": step_build,
        "build-failed": step_build,
        "built": (step_push if args.push else step_report),
        "pushed": step_report,
    }
    seen = 0
    while run.state in steps and seen < 12:
        seen += 1
        code = steps[run.state](run, args)
        if code != EXIT_OK:
            print_gate(run)
            return code
    if not args.push and run.state == "reported" and "pushed" not in [h["state"] for h in run.data["history"]]:
        say("⏸️", "Not pushed (experimental default). Run `push` when you're happy with it.")
    say("🏁", f"Week {run.week}: {run.state}")
    return EXIT_OK


def _with(ns, **kw):
    d = dict(vars(ns))
    d.update(kw)
    return argparse.Namespace(**d)


def print_gate(run):
    for g in run.data.get("gates", []):
        say("🚦", f"GATE: {g['reason']}")
        for item in g["items"][:30]:
            print(f"      · {item}")


def step_decide(run, args):
    """Record a decision on files that wait for one (or a note on a spliced file)."""
    if not args.paths:
        say("❌", "Name the file(s): decide PATH [PATH...] --note \"what was kept and why\"")
        return EXIT_ERROR
    for path in args.paths:
        c = run.data["conflicts"].get(path)
        if c is None:
            say("❌", f"{path} is not in this week's conflicts")
            return EXIT_ERROR
        c.update(state="decided", by=args.by or os.environ.get("USERNAME") or os.environ.get("USER") or "",
                 note=args.note or c.get("note", ""))
        say("🗳️", f"{path}: decided by {c['by']}")
    run.save()
    write_triage(run)
    return EXIT_OK


def step_status(run, args):
    counts = {}
    for c in run.data["conflicts"].values():
        counts[c["state"]] = counts.get(c["state"], 0) + 1
    say("📍", f"Week {run.week} · {run.data['branch']} · state: {run.state}")
    if counts:
        say("🧮", ", ".join(f"{STATE_ICON.get(k, '')} {k}: {v}" for k, v in sorted(counts.items())))
    print_gate(run)
    return EXIT_OK


def step_install(root, args):
    src = Path(__file__).resolve().parent
    dest = tools_dir(root)
    dest.mkdir(parents=True, exist_ok=True)
    ensure_excluded(root)
    for name in TOOLS:
        if (src / name).exists():
            shutil.copy2(src / name, dest / name)
            say("📦", f"{name} → {dest}")
    say("✅", f"Run the chain with: python {RUNS_DIR}/_tools/bforartists_merge_auto.py run -w <week>")
    return EXIT_OK


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args(argv=None):
    p = argparse.ArgumentParser(description="Weekly Blender merge as a chain of dominoes (experimental, #6930)",
                                formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    p.add_argument("command", choices=("install", "run", "status", "merge", "adopt", "resolve", "check",
                                       "decide", "finish", "build", "push", "report"))
    p.add_argument("paths", nargs="*", help="decide: the file(s) the decision is about")
    p.add_argument("--by", help="decide: who decided (default: your user name)")
    p.add_argument("--note", help="decide: what was kept and why (goes into the PR)")
    p.add_argument("-w", "--week-number", type=int, help="ISO week; defaults to the last week used")
    p.add_argument("--push", action="store_true", help="run: push after a good build (off while experimental)")
    p.add_argument("--stage", action="store_true", help="check: git add files that pass")
    p.add_argument("--allow-marker-loss", action="append", metavar="PATH=REASON",
                   help="check: accept fewer BFA markers in PATH, with the reason logged in the PR")
    p.add_argument("--target", choices=("ninja", "lite"), default="ninja", help="build: make target")
    p.add_argument("--clean", choices=("cache", "full", "none"), default="cache",
                   help="build: remove the old CMake cache/solution (default), the whole build folder, or nothing")
    p.add_argument("--build-dir", help="build: build folder, if not the make.bat/make default")
    p.add_argument("--skip-master-update", action="store_true", help="merge: passed to the merge script")
    p.add_argument("--blender-remote", help="merge: passed to the merge script")
    p.add_argument("--origin-remote", help="merge/push: passed to the merge script")
    return p.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    root = repo_root()
    if args.command == "install":
        return step_install(root, args)
    week = args.week_number or current_week(root)
    if week is None:
        say("❌", "Pass --week-number (-w) the first time")
        return EXIT_ERROR
    run = Run(root, week)
    commands = {
        "run": step_run, "status": step_status, "merge": step_merge, "adopt": step_adopt,
        "resolve": step_resolve, "check": step_check, "decide": step_decide, "finish": step_finish, "build": step_build,
        "push": step_push, "report": step_report,
    }
    try:
        return commands[args.command](run, args)
    except RuntimeError as ex:
        say("❌", str(ex))
        run.gate(f"error in {args.command}: {str(ex).splitlines()[0]}")
        return EXIT_ERROR


if __name__ == "__main__":
    sys.exit(main())

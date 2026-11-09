#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Bforartists Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""
List Bforartists UI strings that no translation file knows (#5701). Read only, no build needed.

Blender finds a translation by its exact English text, the msgid in `locale/po/<lang>.po`.
When Bforartists rewords a label or tooltip, search and replace the old English text in the
whole repository, `locale/po` included. Every language then keeps its translation.

This tool finds the strings that slipped through: UI strings in code Bforartists changed against
Blender that no `.po` file has. When the same diff hunk removed a Blender string that has a
translation, it shows that string too ("Blender:"). Search and replace it in `locale/po` to get the
translation back, if the meaning is still the same. The others are new strings that stay English
until someone translates them.

Usage, from the repository root:
    python tools/utils/bforartists_i18n_audit.py                       # All BFA changes.
    python tools/utils/bforartists_i18n_audit.py --since origin/master  # Only lines changed since a ref.
    python tools/utils/bforartists_i18n_audit.py --summary              # Counts only.
"""

__all__ = (
    "main",
)

import argparse
import ast
import bisect
import difflib
import glob
import inspect
import os
import re
import subprocess
import sys

for stream in (sys.stdout, sys.stderr):
    try:
        stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Bundled third-party add-ons are not part of the main translation catalog.
PATHSPECS = ("source/blender", "scripts/startup", "scripts/modules", "scripts/addons_core",
             ":(exclude)scripts/addons_core/bfa_default_addons")
C_EXT = (".c", ".cc", ".cpp", ".h", ".hh")
PY_EXT = (".py",)


def git(*args, root=None, data=None):
    return subprocess.run(["git", *args], cwd=root, input=data, capture_output=True, check=True).stdout


# -----------------------------------------------------------------------------
# Translation files.

def _unescape(s):
    return re.sub(r'\\(.)', lambda m: {"n": "\n", "t": "\t"}.get(m.group(1), m.group(1)), s)


def po_msgids(po_dir):
    """All msgids that have a (non fuzzy) translation in at least one `.po` file."""
    known = set()
    for path in glob.glob(os.path.join(po_dir, "*.po")):
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
        for entry in re.split(r"\n\s*\n", text):
            if "#, fuzzy" in entry:
                continue
            m = re.search(r'^msgid ((?:".*"\s*)+)^msgstr ((?:".*"\s*)+)', entry, re.M)
            if m and m.group(2).strip() != '""':
                known.add(_unescape("".join(re.findall(r'"(.*)"', m.group(1)))))
    return known


# -----------------------------------------------------------------------------
# UI strings in code: yield (text, first_line, last_line).

C_TOKEN = re.compile(r'//[^\n]*|/\*.*?\*/|"(?:[^"\\\n]|\\.)*"|\'(?:[^\'\\\n]|\\.)*\'', re.S)
C_GAP = re.compile(r'(?:\s|//[^\n]*|/\*.*?\*/)*', re.S)
# Code right before a C/C++ string that makes it a UI string.
C_UI = re.compile(
    r'\bot->(?:name|description)\s*=|_ui_(?:text|description)\s*\(|\bRNA_def_\w+\s*\(|'
    r'\b(?:CTX_)?(?:IFACE|TIP|RPT|DATA|N)_\s*\(')
# A row of an `EnumPropertyItem` array: {VALUE, "IDENTIFIER", ICON, "Name", "Description"}.
C_ENUM_ROW = re.compile(r'^\s*[\w:]+\s*,\s*"[^"]*"\s*,\s*\w+\s*,\s*(?:"(?:[^"\\]|\\.)*"\s*,\s*)?$')
PY_UI_KEYWORDS = {"text", "name", "description", "heading"}
PY_UI_CALLS = {"iface_", "tip_", "rpt_", "pgettext", "pgettext_iface", "pgettext_tip", "pgettext_rpt"}
PY_UI_ATTRS = {"bl_label", "bl_description"}


def looks_like_ui(s):
    s = s.strip()
    if len(s) < 2 or not re.search(r"[A-Za-z]{2}", s):
        return False
    if " " not in s:
        # Identifiers, constants, paths, CamelCase type names.
        if re.fullmatch(r"[a-z0-9_.\-/:*%]+|[A-Z0-9_]+", s) or any(c in s for c in "._/"):
            return False
        if re.fullmatch(r"[A-Z]?[a-z0-9]+(?:[A-Z][a-z0-9]*)+", s):
            return False
    return True


def c_strings(text):
    groups = []
    for m in C_TOKEN.finditer(text):
        tok = m.group()
        if tok[0] != '"':
            continue
        if groups and C_GAP.fullmatch(text, groups[-1][2], m.start()):
            groups[-1][1] += _unescape(tok[1:-1])
            groups[-1][2] = m.end()
        else:
            groups.append([m.start(), _unescape(tok[1:-1]), m.end()])
    lines = [i for i, c in enumerate(text) if c == "\n"]
    for start, s, end in groups:
        before = text[max(0, start - 400):start]
        cut = max(before.rfind(";"), before.rfind("{"), before.rfind("}"))
        before = before[cut + 1:]
        if (C_UI.search(before) or C_ENUM_ROW.match(before)) and looks_like_ui(s):
            yield s, bisect.bisect_left(lines, start) + 1, bisect.bisect_left(lines, end) + 1


def py_strings(text):
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return

    def const(node):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            yield node.value, node.lineno, node.end_lineno

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func.attr if isinstance(node.func, ast.Attribute) else getattr(node.func, "id", "")
            if func in PY_UI_CALLS and node.args:
                yield from const(node.args[0])
            if func == "report" and len(node.args) > 1:
                yield from const(node.args[1])
            for kw in node.keywords:
                if kw.arg in PY_UI_KEYWORDS:
                    yield from const(kw.value)
                elif kw.arg == "items" and isinstance(kw.value, (ast.List, ast.Tuple)):
                    for item in kw.value.elts:
                        if isinstance(item, ast.Tuple):
                            for elt in item.elts[1:3]:
                                yield from const(elt)
        elif isinstance(node, ast.ClassDef):
            body = node.body
            attrs = {t.id for n in body if isinstance(n, ast.Assign) for t in n.targets if isinstance(t, ast.Name)}
            if body and "bl_idname" in attrs:
                # Operator and menu docstrings are their tooltips.
                yield from const(getattr(body[0], "value", None) if isinstance(body[0], ast.Expr) else None)
            for n in body:
                if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id in PY_UI_ATTRS
                                                     for t in n.targets):
                    yield from const(n.value)


def ui_strings(path, text):
    found = c_strings(text) if path.endswith(C_EXT) else py_strings(text)
    for s, first, last in found:
        if looks_like_ui(s):
            yield s, first, last


def known_variants(s):
    # Python docstrings reach Blender cleaned up, compare all plausible forms.
    return {s, s.strip(), inspect.cleandoc(s)}


# -----------------------------------------------------------------------------
# Diff.

HUNK = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@", re.M)


def diff_hunks(root, base, pathspecs):
    """``{path: [(old_first, old_count, new_first, new_count)]}`` of worktree changes against ``base``."""
    out = git("diff", "-U0", "--no-color", "--no-ext-diff", "--no-renames", "--diff-filter=AM",
              base, "--", *pathspecs, root=root).decode("utf-8", "replace")
    result = {}
    path = None
    for line in out.splitlines():
        if line.startswith("+++ "):
            path = line[6:] if line.startswith("+++ b/") else None
            if path and not path.endswith(C_EXT + PY_EXT):
                path = None
            if path:
                result[path] = []
        elif path and line.startswith("@@"):
            m = HUNK.match(line)
            o1, oc, n1, nc = m.group(1), m.group(2), m.group(3), m.group(4)
            result[path].append((int(o1), 1 if oc is None else int(oc), int(n1), 1 if nc is None else int(nc)))
    return result


def added_lines(hunks):
    return {n for _o1, _oc, n1, nc in hunks for n in range(n1, n1 + nc)}


def blobs(root, ref, paths):
    """``{path: text}`` of ``paths`` at ``ref``, read in one `git cat-file` run."""
    data = git("cat-file", "--batch", root=root, data="".join("{}:{}\n".format(ref, p) for p in paths).encode())
    result = {}
    pos = 0
    for p in paths:
        header_end = data.index(b"\n", pos)
        header = data[pos:header_end].split()
        if header[-1] == b"missing":
            pos = header_end + 1
            continue
        size = int(header[2])
        result[p] = data[header_end + 1:header_end + 1 + size].decode("utf-8", "replace")
        pos = header_end + 1 + size + 1
    return result


# -----------------------------------------------------------------------------

def audit(root, base, po_dir, since=None):
    known = po_msgids(po_dir)
    hunks = diff_hunks(root, base, PATHSPECS)
    if since:
        recent = diff_hunks(root, since, PATHSPECS)
        hunks = {p: h for p, h in hunks.items() if p in recent}
    old_texts = blobs(root, base, [p for p, h in hunks.items() if any(oc for _o1, oc, _n1, _nc in h)])

    reworded, new = [], []
    for path, file_hunks in sorted(hunks.items()):
        with open(os.path.join(root, path), encoding="utf-8", errors="replace") as fh:
            text = fh.read()
        lines = added_lines(file_hunks)
        if since:
            lines &= added_lines(recent[path])
        if not lines:
            continue
        found = list(ui_strings(path, text))
        now = [(s, a, b) for s, a, b in found
               if not known_variants(s) & known and any(n in lines for n in range(a, b + 1))]
        if not now:
            continue
        now_all = {s for s, _a, _b in found}
        old = [(s, a, b) for s, a, b in ui_strings(path, old_texts.get(path, "")) if s not in now_all]
        for s, a, _b in now:
            hunk = next((h for h in file_hunks if h[2] <= a < h[2] + max(h[3], 1)), None)
            best, best_ratio = None, 0.0
            if hunk and hunk[1]:
                for o, oa, ob in old:
                    if oa < hunk[0] + hunk[1] and ob >= hunk[0]:
                        ratio = difflib.SequenceMatcher(None, s, o).ratio()
                        if ratio > best_ratio:
                            best, best_ratio = o, ratio
            if best and best_ratio >= 0.4:
                # Rewording a string Blender doesn't translate either loses nothing.
                if best in known:
                    reworded.append((path, a, s, best))
            else:
                new.append((path, a, s))
    return reworded, new


def quote(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--blender-ref", default="blender/main",
                        help="Pure Blender ref, compared at its merge base with HEAD (default: blender/main).")
    parser.add_argument("--since", help="Only report lines changed since this ref (e.g. origin/master).")
    parser.add_argument("--po-dir", help="Translation files (default: locale/po).")
    parser.add_argument("--summary", action="store_true", help="Print the counts only.")
    args = parser.parse_args()

    root = git("rev-parse", "--show-toplevel").decode().strip()
    base = git("merge-base", "HEAD", args.blender_ref, root=root).decode().strip()
    po_dir = args.po_dir or os.path.join(root, "locale", "po")
    reworded, new = audit(root, base, po_dir, args.since)

    if not args.summary:
        if reworded:
            print("Reworded Blender strings. If the meaning is the same, search and replace the Blender")
            print("text in locale/po with the new text to keep its translations:\n")
            for path, line, s, old in reworded:
                print("  {}:{}\n      now:     {}\n      Blender: {}".format(path, line, quote(s), quote(old)))
            print()
        if new:
            print("New strings without a translation (they show in English):\n")
            for path, line, s in new:
                print("  {}:{}  {}".format(path, line, quote(s)))
            print()
    print("Translations audit against Blender {}{}: {} reworded, {} new without translation.".format(
        base[:11], " since " + args.since if args.since else "", len(reworded), len(new)))
    return 0


if __name__ == "__main__":
    sys.exit(main())

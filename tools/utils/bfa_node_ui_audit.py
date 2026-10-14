#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Bforartists Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""
Bforartists Node UI Audit

Compares the node Add menus with the Bforartists node toolshelf (sidebar "Add" tab)
and the node icon table, and reports what is out of sync. Read-only: no file is changed.

Sources:
  scripts/startup/bl_ui/node_add_menu_*.py         Add menus (follow Blender upstream)
  scripts/startup/bl_ui/space_node_toolshelf.py    Bforartists toolshelf
  source/blender/makesrna/intern/rna_nodetree.cc   Node icons (ICON_NONE = no icon)

Reports, per node editor:
  1. Missing from toolshelf:   in the Add menu, not in the toolshelf.
  2. Not in Add menu:          in the toolshelf, no longer in the Add menu (removed or renamed upstream).
  3. Different category:       in both, but under a different category.
  4. No icon:                  nodes shown in this editor that have ICON_NONE.

Usage:
  python tools/utils/bfa_node_ui_audit.py
  python tools/utils/bfa_node_ui_audit.py --editor geometry
  python tools/utils/bfa_node_ui_audit.py --markdown > report.md

Needs only Python 3 (standard library). No build or Bforartists install required.
Run it after each Blender merge, and paste the --markdown output into issues or PRs.
"""

import argparse
import ast
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BL_UI = ROOT / "scripts" / "startup" / "bl_ui"
TOOLSHELF_FILE = BL_UI / "space_node_toolshelf.py"
RNA_NODETREE_FILE = ROOT / "source" / "blender" / "makesrna" / "intern" / "rna_nodetree.cc"

# Editor key: (display name, Add menu file, toolshelf panel class prefix).
EDITORS = {
    "shader": ("Shader", "node_add_menu_shader.py", "NODES_PT_toolshelf_shader_add"),
    "geometry": ("Geometry Nodes", "node_add_menu_geometry.py", "NODES_PT_toolshelf_gn_add"),
    "compositor": ("Compositor", "node_add_menu_compositor.py", "NODES_PT_toolshelf_compositor_add"),
    "texture": ("Texture", "node_add_menu_texture.py", "NODES_PT_toolshelf_texture_add"),
}

# Nodes that are left out of the toolshelf (or Add menu) on purpose: (editor or "*", node) -> reason.
# Add an entry here instead of "fixing" a gap that is intended.
IGNORE = {
    ("geometry", "NodeGroupInput"): "Shown in the Relations tab > Group panel.",
    ("shader", "ShaderNodeScript"): "Has its own Script panel in the toolshelf.",
}

# (editor, Add menu category) -> toolshelf category, where Bforartists uses a different name on purpose.
CATEGORY_ALIASES = {
    ("geometry", "Utilities/List"): "Utilities/Lists",
    ("texture", "Texture"): "Textures",
}

NODE_ID_RE = re.compile(r"^(?:Shader|Geometry|Function|Compositor|Texture)?Node[A-Z]\w*$")

# Add menu helpers that add something other than a plain node, mapped to the toolshelf operator.
ZONE_HELPERS = {
    "simulation_zone": "node.add_simulation_zone",
    "repeat_zone": "node.add_repeat_zone",
    "for_each_element_zone": "node.add_foreach_geometry_element_zone",
    "closure_zone": "node.add_closure_zone",
}
# Add menu helpers with an implicit node type.
IMPLICIT_NODE_HELPERS = {
    "color_mix_node": "ShaderNodeMix",
}


def _class_str_attr(cls_node, name):
    for stmt in cls_node.body:
        if isinstance(stmt, ast.Assign) and isinstance(stmt.value, ast.Constant):
            for target in stmt.targets:
                if isinstance(target, ast.Name) and target.id == name:
                    return stmt.value.value
    return None


def _class_method(cls_node, name):
    for stmt in cls_node.body:
        if isinstance(stmt, ast.FunctionDef) and stmt.name == name:
            return stmt
    return None


def _calls_in_order(func_node):
    calls = [n for n in ast.walk(func_node) if isinstance(n, ast.Call)]
    calls.sort(key=lambda n: (n.lineno, n.col_offset))
    return calls


def _call_name(call):
    func = call.func
    if isinstance(func, ast.Attribute):
        return func.attr
    if isinstance(func, ast.Name):
        return func.id
    return None


def _string_args(call):
    values = [a.value for a in call.args if isinstance(a, ast.Constant) and isinstance(a.value, str)]
    values += [k.value.value for k in call.keywords
               if isinstance(k.value, ast.Constant) and isinstance(k.value.value, str)]
    return values


def _add_entry(entries, key, category):
    """Keep the first position of each key, but remember every category it appears in."""
    if key not in entries:
        entries[key] = []
    if category not in entries[key]:
        entries[key].append(category)


def parse_add_menu(path):
    """Return {node_or_operator_id: [category, ...]} in menu order."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    entries = {}
    for cls in (n for n in tree.body if isinstance(n, ast.ClassDef)):
        if not cls.name.endswith("_base") or cls.name.endswith("_all_base"):
            continue
        draw = _class_method(cls, "draw")
        if draw is None:
            continue
        category = _class_str_attr(cls, "menu_path") or _class_str_attr(cls, "bl_label") or cls.name
        for call in _calls_in_order(draw):
            name = _call_name(call)
            if name in ZONE_HELPERS:
                _add_entry(entries, ZONE_HELPERS[name], category)
            elif name in IMPLICIT_NODE_HELPERS:
                _add_entry(entries, IMPLICIT_NODE_HELPERS[name], category)
            elif name and name.startswith("node_operator"):
                for value in _string_args(call):
                    if NODE_ID_RE.match(value):
                        _add_entry(entries, value, category)
                        break
    return entries


def parse_toolshelf(path, class_prefix):
    """Return {node_or_operator_id: [category, ...]} in panel order, for one editor."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    classes = {n.name: n for n in tree.body if isinstance(n, ast.ClassDef)}

    def category_of(cls):
        label = _class_str_attr(cls, "bl_label") or cls.name
        parent = _class_str_attr(cls, "bl_parent_id")
        if parent and parent in classes:
            return category_of(classes[parent]) + "/" + label
        return label

    entries = {}
    for cls in classes.values():
        if not cls.name.startswith(class_prefix):
            continue
        draw = _class_method(cls, "draw")
        if draw is None:
            continue
        category = category_of(cls)
        for call in _calls_in_order(draw):
            if _call_name(call) != "OperatorEntry":
                continue
            node = None
            if call.args and isinstance(call.args[0], ast.Constant):
                node = call.args[0].value
            operator = None
            for k in call.keywords:
                if isinstance(k.value, ast.Constant):
                    if k.arg == "node":
                        node = k.value.value
                    elif k.arg == "operator":
                        operator = k.value.value
            if node:
                _add_entry(entries, node, category)
            elif operator and operator in ZONE_HELPERS.values():
                _add_entry(entries, operator, category)
    return entries


def parse_icons(path):
    """Return {node_id: (icon, comment)} from the define(brna, ...) table."""
    define_re = re.compile(
        r'define\(\s*brna\s*,\s*"\w+"\s*,\s*"(\w+)"\s*,\s*[^,]+,\s*(ICON_\w+)\s*\)\s*;\s*(?:/[/*]\s*(.*?)\s*(?:\*/)?)?$')
    icons = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        match = define_re.search(line)
        if match:
            icons[match.group(1)] = (match.group(2), (match.group(3) or "").strip())
    return icons


def _is_ignored(editor, key):
    return (editor, key) in IGNORE or ("*", key) in IGNORE


def _norm_category(editor, category):
    return CATEGORY_ALIASES.get((editor, category), category)


def _display(key):
    """Readable name for zone operators, node ids stay as they are (they are what you search for in code)."""
    for helper, operator in ZONE_HELPERS.items():
        if key == operator:
            return "Zone: " + helper.replace("_zone", "").replace("_", " ").title()
    return key


def audit_editor(editor, icons):
    _name, menu_file, class_prefix = EDITORS[editor]
    menu = parse_add_menu(BL_UI / menu_file)
    shelf = parse_toolshelf(TOOLSHELF_FILE, class_prefix)

    missing = [(k, cats) for k, cats in menu.items() if k not in shelf and not _is_ignored(editor, k)]
    extra = [(k, cats) for k, cats in shelf.items() if k not in menu and not _is_ignored(editor, k)]
    moved = []
    for key, menu_cats in menu.items():
        if key in shelf and not _is_ignored(editor, key):
            if not {_norm_category(editor, c) for c in menu_cats} & set(shelf[key]):
                moved.append((key, menu_cats, shelf[key]))
    shown = list(dict.fromkeys(list(menu) + list(shelf)))
    no_icon = [(k, icons[k][1]) for k in shown if k in icons and icons[k][0] == "ICON_NONE"]
    return {"missing": missing, "extra": extra, "moved": moved, "no_icon": no_icon}


def print_text(results):
    for editor, res in results.items():
        print(f"== {EDITORS[editor][0]} ==")
        print(f"Missing from toolshelf ({len(res['missing'])}):")
        for key, cats in res["missing"]:
            print(f"  {_display(key):<45} Add menu: {', '.join(cats)}")
        print(f"Not in Add menu ({len(res['extra'])}):")
        for key, cats in res["extra"]:
            print(f"  {_display(key):<45} toolshelf: {', '.join(cats)}")
        print(f"Different category ({len(res['moved'])}):")
        for key, menu_cats, shelf_cats in res["moved"]:
            print(f"  {_display(key):<45} Add menu: {', '.join(menu_cats)}  |  toolshelf: {', '.join(shelf_cats)}")
        print(f"No icon ({len(res['no_icon'])}):")
        for key, comment in res["no_icon"]:
            print(f"  {key:<45} {comment}")
        print()


def print_markdown(results):
    for editor, res in results.items():
        print(f"## {EDITORS[editor][0]}\n")
        if res["missing"]:
            print("**Missing from toolshelf**\n\n| Node | Add menu category |\n|---|---|")
            for key, cats in res["missing"]:
                print(f"| `{_display(key)}` | {', '.join(cats)} |")
            print()
        if res["extra"]:
            print("**Not in Add menu**\n\n| Node | Toolshelf category |\n|---|---|")
            for key, cats in res["extra"]:
                print(f"| `{_display(key)}` | {', '.join(cats)} |")
            print()
        if res["moved"]:
            print("**Different category**\n\n| Node | Add menu | Toolshelf |\n|---|---|---|")
            for key, menu_cats, shelf_cats in res["moved"]:
                print(f"| `{_display(key)}` | {', '.join(menu_cats)} | {', '.join(shelf_cats)} |")
            print()
        if res["no_icon"]:
            print("**No icon**\n\n| Node | Note in rna_nodetree.cc |\n|---|---|")
            for key, comment in res["no_icon"]:
                print(f"| `{key}` | {comment} |")
            print()
        if not any(res.values()):
            print("Nothing to report.\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[1].strip())
    parser.add_argument("--editor", choices=sorted(EDITORS), help="Only report this node editor")
    parser.add_argument("--markdown", action="store_true", help="Print Markdown tables for issues and PRs")
    args = parser.parse_args()

    icons = parse_icons(RNA_NODETREE_FILE)
    editors = [args.editor] if args.editor else list(EDITORS)
    results = {editor: audit_editor(editor, icons) for editor in editors}

    if args.markdown:
        print_markdown(results)
    else:
        print_text(results)
    return 0


if __name__ == "__main__":
    sys.exit(main())

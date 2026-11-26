# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""
Persistent metadata for the Keymap Editor (labels, custom item names, and
items/operators hidden from the usage history), stored in a JSON file in the
user configuration directory instead of DNA/UserDef structs.
"""

__all__ = (
    "custom_name_get",
    "custom_name_set",
    "custom_names_map",
    "hidden_list",
    "hidden_set",
    "item_forget",
    "label_add",
    "label_filter_set",
    "label_filter_toggle",
    "label_item_set",
    "label_items_all",
    "label_remove",
    "labels_list",
    "operator_hidden_set",
)

import json
import os
import bpy

_DEFAULT_HIDDEN_OPERATORS = (
    # View navigation.
    ("view2d.pan", ""),
    ("view2d.scroll_up", ""),
    ("view2d.scroll_down", ""),
    # Keymap editor's own operators.
    ("preferences.keyitem_add", ""),
    ("preferences.keyitem_add_for_operator", ""),
    ("preferences.keyitem_copy", ""),
    ("preferences.keyitem_expand", ""),
    ("preferences.keyitem_flash_conflict", ""),
    ("preferences.keyitem_paste", ""),
    ("preferences.keyitem_remove", ""),
    ("preferences.keyitem_rename", ""),
    ("preferences.keyitem_restore", ""),
    ("preferences.keyitem_reveal", ""),
    ("preferences.keyitem_select", ""),
    ("preferences.keyitem_unshadow", ""),
    ("preferences.keymap_activity_clear", ""),
    ("preferences.keymap_activity_find", ""),
    ("preferences.keymap_activity_reveal", ""),
    ("preferences.keymap_conflicts_check", ""),
    ("preferences.keymap_filter_refresh", ""),
    ("preferences.keymap_hide_item", ""),
    ("preferences.keymap_hide_operator", ""),
    ("preferences.keymap_isolate", ""),
    ("preferences.keymap_label_assign", ""),
    ("preferences.keymap_label_filter_toggle", ""),
    ("preferences.keymap_label_new", ""),
    ("preferences.keymap_label_remove", ""),
    ("preferences.keymap_redo", ""),
    ("preferences.keymap_restore", ""),
    ("preferences.keymap_select_all", ""),
    ("preferences.keymap_undo", ""),
    ("preferences.keymap_view_back", ""),
    ("wm.context_toggle", "space_data.use_filter_addon"),
    ("wm.context_toggle", "space_data.use_filter_conflicts"),
    ("wm.context_toggle", "space_data.use_filter_user_modified"),
    ("wm.context_set_enum", "space_data.filter_type=KEY"),
    ("wm.context_set_enum", "space_data.filter_type=NAME"),
)

_data = None
_meta_filename = "keymap_editor_meta.json"


def _meta_path(*, create=False):
    config_dir = bpy.utils.user_resource('CONFIG', create=create)
    if not config_dir:
        return None
    return os.path.join(config_dir, _meta_filename)


def _default_data():
    return {
        "labels": [],
        "label_items": [],
        "custom_names": {},
        "hidden": [
            {"idname": idname, "variant": variant}
            for idname, variant in _DEFAULT_HIDDEN_OPERATORS
        ],
    }


def _ensure_loaded():
    global _data
    if _data is not None:
        return _data
    path = _meta_path(create=False)
    if path and os.path.isfile(path):
        try:
            with open(path, "r", encoding="utf-8") as fh:
                loaded = json.load(fh)
            if isinstance(loaded, dict):
                _data = {
                    "labels": list(loaded.get("labels", [])),
                    "label_items": list(loaded.get("label_items", [])),
                    "custom_names": dict(loaded.get("custom_names", {})),
                    "hidden": list(loaded.get("hidden", [])),
                }
                return _data
        except Exception:
            pass
    _data = _default_data()
    return _data


def _save():
    data = _ensure_loaded()
    path = _meta_path(create=True)
    if not path:
        return
    try:
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2)
        os.replace(tmp, path)
    except Exception:
        pass


def _item_key_str(km, kmi):
    return f"{km.name}\t{km.space_type}\t{km.region_type}\t{kmi.id}"


def _parse_item_key_str(key_str):
    parts = key_str.split("\t")
    if len(parts) != 4:
        return None
    try:
        return parts[0], parts[1], parts[2], int(parts[3])
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# Labels

def labels_list():
    """Return list of (name, use_filter) tuples."""
    return [(entry["name"], bool(entry.get("use_filter", False))) for entry in _ensure_loaded()["labels"]]


def label_add(name):
    name = name.strip()
    if not name:
        return False
    data = _ensure_loaded()
    for entry in data["labels"]:
        if entry["name"] == name:
            return False
    data["labels"].append({"name": name, "use_filter": False})
    _save()
    return True


def label_remove(name):
    data = _ensure_loaded()
    before = len(data["labels"])
    data["labels"] = [entry for entry in data["labels"] if entry["name"] != name]
    if len(data["labels"]) == before:
        return False
    data["label_items"] = [entry for entry in data["label_items"] if entry[4] != name]
    _save()
    return True


def label_filter_set(name, value):
    data = _ensure_loaded()
    for entry in data["labels"]:
        if entry["name"] == name:
            if bool(entry.get("use_filter", False)) != bool(value):
                entry["use_filter"] = bool(value)
                _save()
            return True
    return False


def label_filter_toggle(name):
    data = _ensure_loaded()
    for entry in data["labels"]:
        if entry["name"] == name:
            entry["use_filter"] = not bool(entry.get("use_filter", False))
            _save()
            return True
    return False


def label_items_all():
    """Return list of (km_name, space_type, region_type, item_id, label)."""
    return [tuple(entry) for entry in _ensure_loaded()["label_items"] if len(entry) == 5]


def label_item_set(label, km, kmi, value):
    label = label.strip()
    if not label:
        return False
    data = _ensure_loaded()
    record = [km.name, km.space_type, km.region_type, kmi.id, label]
    exists = record in data["label_items"]
    if bool(value) == exists:
        return False
    if value:
        if not any(entry["name"] == label for entry in data["labels"]):
            data["labels"].append({"name": label, "use_filter": False})
        data["label_items"].append(record)
    else:
        data["label_items"] = [e for e in data["label_items"] if e != record]
    _save()
    return True


# ---------------------------------------------------------------------------
# Custom Names

def custom_names_map():
    """Return dict {(km_name, space_type, region_type): {item_id: name}}."""
    cache = {}
    for key_str, name in _ensure_loaded()["custom_names"].items():
        parsed = _parse_item_key_str(key_str)
        if parsed is None or not name:
            continue
        km_name, space_type, region_type, item_id = parsed
        cache.setdefault((km_name, space_type, region_type), {})[item_id] = name
    return cache


def custom_name_get(km, kmi):
    return _ensure_loaded()["custom_names"].get(_item_key_str(km, kmi), "")


def custom_name_set(km, kmi, name):
    data = _ensure_loaded()
    key = _item_key_str(km, kmi)
    name = (name or "").strip()
    if not name:
        if key in data["custom_names"]:
            del data["custom_names"][key]
            _save()
            return True
        return False
    if data["custom_names"].get(key) == name:
        return False
    data["custom_names"][key] = name
    _save()
    return True


# ---------------------------------------------------------------------------
# Hidden from Usage History

def hidden_list():
    """Return list of hidden entry dicts."""
    return list(_ensure_loaded()["hidden"])


def hidden_set(km, kmi, value):
    data = _ensure_loaded()
    match_idx = None
    for i, entry in enumerate(data["hidden"]):
        if (
            not entry.get("idname") and
            entry.get("keymap_name") == km.name and
            entry.get("space_type") == km.space_type and
            entry.get("region_type") == km.region_type and
            entry.get("item_id") == kmi.id
        ):
            match_idx = i
            break
    if bool(value) == (match_idx is not None):
        return False
    if value:
        data["hidden"].append({
            "keymap_name": km.name,
            "space_type": km.space_type,
            "region_type": km.region_type,
            "item_id": kmi.id,
        })
    else:
        data["hidden"].pop(match_idx)
    _save()
    return True


def operator_hidden_set(idname, variant, value):
    variant = variant or ""
    data = _ensure_loaded()
    match_idx = None
    for i, entry in enumerate(data["hidden"]):
        if entry.get("idname") == idname and entry.get("variant", "") == variant:
            match_idx = i
            break
    if bool(value) == (match_idx is not None):
        return False
    if value:
        data["hidden"].append({"idname": idname, "variant": variant})
    else:
        data["hidden"].pop(match_idx)
    _save()
    return True


def item_forget(km, kmi):
    changed = custom_name_set(km, kmi, "")
    data = _ensure_loaded()
    before = len(data["label_items"])
    data["label_items"] = [
        e for e in data["label_items"]
        if not (e[0] == km.name and e[1] == km.space_type and e[2] == km.region_type and e[3] == kmi.id)
    ]
    if len(data["label_items"]) != before:
        changed = True
    changed |= hidden_set(km, kmi, False)
    if changed:
        _save()
    return changed

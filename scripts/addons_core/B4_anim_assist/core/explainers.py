"""Hover explainers: Full, Short or Off, plus shortcuts that already exist.

Bforartists shows an operator's static description in every tooltip and falls
back to it whenever a dynamic description is empty, so it could never be
switched off. Anim Assist operators are therefore registered with an empty
static description; their text comes from a ``description`` callback that
follows the ``explainer_mode`` preference (owner request 2026-10-18). The
Python attribute ``bl_description`` is restored after registration, so code
reading it still sees the full text.
"""

from __future__ import annotations

import re
import time

import bpy

__all__ = [
    "MODES", "mode", "short", "register_class", "operator_text", "raw_description",
    "shortcuts", "shortcut_lines", "native_lines",
]

MODES = (
    ("FULL", "Full", "Show the full explanation when the pointer rests on an Anim Assist control"),
    ("SHORT", "Short", "Show the name and a one-line summary"),
    ("OFF", "Off", "Show no Anim Assist explanations on hover; Bforartists buttons show only their name"),
)
SHORT_LIMIT = 120
# Where a long first sentence may be cut, from the latest acceptable point.
_CUTS = (", ", " using ", " with ", " so ", " and ", " on ", " for ")

_full: dict[type, str] = {}      # operator class -> original description
_by_idname: dict[str, type] = {}


def mode(context=None) -> str:
    try:
        from ..prefs import get_prefs
        prefs = get_prefs(context or bpy.context)
    except Exception:
        prefs = None
    value = getattr(prefs, "explainer_mode", "FULL")
    return value if value in {"FULL", "SHORT", "OFF"} else "FULL"


def short(text: str, limit: int = SHORT_LIMIT) -> str:
    """First sentence, at most ``limit`` characters, without a closing period.
    A longer sentence is cut at a clause boundary (or a word), never mid-word."""
    text = " ".join((text or "").split())
    match = re.search(r"(?<=[.;!?])\s", text)
    first = text[:match.start()] if match else text
    first = first.rstrip(".;")
    if len(first) > limit:
        head = first[:limit]
        points = [head.rfind(cut) for cut in _CUTS if head.rfind(cut) > 40]
        first = head[:max(points)] if points else head.rsplit(" ", 1)[0]
        first = first.rstrip(",;: ")
    return first


def _original(cls) -> str:
    for klass in cls.__mro__:
        if klass in _full:
            return _full[klass]
        text = klass.__dict__.get("bl_description")
        if text:
            return text
    return (cls.__dict__.get("__doc__") or "").strip()


def _describe(cls, context, properties):
    current = mode(context)
    if current == "OFF":
        # Bforartists always prints a description line (an empty one reads
        # "(undocumented operator)"), so Off leaves just the tool's name.
        return getattr(cls, "bl_label", "") or " "
    if current == "SHORT":
        brief = cls.__dict__.get("_aa_short")
        if brief is not None:
            return brief.__func__(cls, context, properties) or ""
    raw = cls.__dict__.get("_aa_raw")
    text = (raw(cls, context, properties) if raw else "") or _full.get(cls, "")
    return text if current == "FULL" else short(text)


def register_class(cls) -> None:
    """Register a class; an operator's hover text then follows the explainer mode."""
    if isinstance(cls, type) and issubclass(cls, bpy.types.Operator):
        if cls not in _full:
            _full[cls] = _original(cls)
            own = cls.__dict__.get("description")
            if own is not None and "_aa_raw" not in cls.__dict__:
                cls._aa_raw = own.__func__ if isinstance(own, classmethod) else own
            cls.description = classmethod(_describe)
        cls.bl_description = ""
        try:
            bpy.utils.register_class(cls)
        finally:
            cls.bl_description = _full[cls]
        _by_idname[getattr(cls, "bl_idname", "")] = cls
        return
    bpy.utils.register_class(cls)


def operator_text(idname: str) -> str:
    """Full description of a registered Anim Assist operator ('animassist.name')."""
    cls = _by_idname.get(idname)
    if cls is not None:
        return _full.get(cls, "")
    try:
        module, name = idname.split(".", 1)
        return getattr(getattr(bpy.ops, module), name).get_rna_type().description
    except Exception:
        return ""


def raw_description(cls, context, properties) -> str:
    """The full dynamic text of an operator, whatever the explainer mode."""
    raw = cls.__dict__.get("_aa_raw")
    return (raw(cls, context, properties) if raw else "") or _full.get(cls, "") or (cls.__doc__ or "")


# --- Shortcuts that already exist -------------------------------------------

_cache: dict[tuple, tuple[float, list]] = {}
_CACHE_SECONDS = 2.0


def _same(value, wanted) -> bool:
    if isinstance(wanted, float) or isinstance(value, float):
        try:
            return abs(float(value) - float(wanted)) < 1e-6
        except (TypeError, ValueError):
            return False
    return value == wanted


def shortcuts(idname: str, properties: dict | None = None, keys_only: bool = False) -> list[tuple[str, str]]:
    """Active key bindings to ``idname`` whose properties match: [(keys, keymap name)].

    Reads the live user and add-on key configurations, so a binding appears only
    when one really exists (a default one or one the user added)."""
    key = (idname, tuple(sorted((properties or {}).items())), keys_only)
    now = time.monotonic()
    hit = _cache.get(key)
    if hit and now - hit[0] < _CACHE_SECONDS:
        return hit[1]
    found: list[tuple[str, str]] = []
    wm = getattr(bpy.context, "window_manager", None)
    configs = getattr(wm, "keyconfigs", None)
    for config in (getattr(configs, "user", None), getattr(configs, "addon", None)):
        for keymap in getattr(config, "keymaps", ()):
            for item in keymap.keymap_items:
                if item.idname != idname or not item.active or item.map_type not in {"KEYBOARD", "MOUSE"}:
                    continue
                if keys_only and (item.map_type != "KEYBOARD" or item.value not in {"PRESS", "RELEASE", "CLICK"}):
                    continue  # a key press, not a drag or double-click
                if properties and not all(
                        hasattr(item.properties, name) and _same(getattr(item.properties, name), value)
                        for name, value in properties.items()):
                    continue
                entry = (item.to_string(), keymap.name)
                if entry[0] and entry not in found:
                    found.append(entry)
    _cache[key] = (now, found)
    return found


def shortcut_lines(bindings: list[tuple[str, str]]) -> list[str]:
    places = {"Window", "Screen"}
    text = ", ".join(keys if place in places else f"{keys} ({_PLACES.get(place, place)})" for keys, place in bindings[:3])
    return [f"Shortcut: {text}."] if text else []


_PLACES = {"Dopesheet": "Dope Sheet", "Dopesheet Generic": "Dope Sheet", "Graph Editor Generic": "Graph Editor",
           "Pose": "3D View, Pose Mode", "Object Mode": "3D View, Object Mode"}


# Clearer names where Bforartists' own is generic or lists two variants.
_NATIVE_NAMES = {("transform.transform", "TIME_SCALE"): "Scale Keys in Time",
                 ("transform.transform", "TIME_TRANSLATE"): "Move Keys in Time",
                 ("action.paste", ""): "Paste Keyframes", ("graph.paste", ""): "Paste Keyframes"}


def _native_name(idname: str, properties: dict | None = None) -> str:
    named = _NATIVE_NAMES.get((idname, (properties or {}).get("mode", "")))
    if named:
        return named
    try:
        module, name = idname.split(".", 1)
        return getattr(getattr(bpy.ops, module), name).get_rna_type().name
    except Exception:
        return idname


def native_lines(pairs) -> list[str]:
    """'Bforartists key' lines for Bforartists' own commands that do the same job,
    only for keys Bforartists really has bound (keyboard presses, not drags)."""
    grouped: dict[tuple[str, str], list[str]] = {}
    for idname, properties in pairs:
        for keys, place in shortcuts(idname, properties, keys_only=True):
            places = grouped.setdefault((keys, _native_name(idname, properties)), [])
            place = _PLACES.get(place, place)
            if place not in places:
                places.append(place)
    parts = [f"{keys} ({', '.join(places)}: {name})" for (keys, name), places in list(grouped.items())[:3]]
    return [f"Bforartists key: {'; '.join(parts)}."] if parts else []


def clear() -> None:
    _cache.clear()

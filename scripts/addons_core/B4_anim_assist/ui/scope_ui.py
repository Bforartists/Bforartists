# --- UI/UX FOUNDATION ---
"""Shared scope UX for Anim Assist operators.

A scope is the *what* an operator acts on. Operators expose a single
``scope`` ``EnumProperty`` whose items come from ``scope_enum_items()``.
The corresponding panel UI is drawn through ``draw_scope_selector()``,
which renders the enum as a labelled radio column inside the standard
scope block.

This file contains no operator definitions itself — only the enum item
factory and drawing helpers — so it can be imported without dragging
operators along.
"""

from __future__ import annotations

from typing import Iterable, Optional

import bpy

from ..core import ui_naming
from . import ui_helpers


# ---------------------------------------------------------------------------
# Scope identifier constants
# ---------------------------------------------------------------------------

SCOPE_SELECTED_KEYS: str = "SELECTED_KEYS"
SCOPE_VISIBLE_KEYS: str = "VISIBLE_KEYS"
SCOPE_CURRENT_FRAME: str = "CURRENT_FRAME"
SCOPE_FRAME_RANGE: str = "FRAME_RANGE"
SCOPE_PLAYBACK_RANGE: str = "PLAYBACK_RANGE"
SCOPE_PREVIEW_RANGE: str = "PREVIEW_RANGE"
SCOPE_SELECTED_CHANNELS: str = "SELECTED_CHANNELS"
SCOPE_VISIBLE_CHANNELS: str = "VISIBLE_CHANNELS"
SCOPE_ALL_CHANNELS: str = "ALL_CHANNELS"
SCOPE_SELECTED_OBJECTS: str = "SELECTED_OBJECTS"
SCOPE_SELECTED_BONES: str = "SELECTED_BONES"
SCOPE_MATCHING_TARGETS: str = "MATCHING_TARGETS"


#: Master ordered list. Operators pick a subset via ``scope_enum_items``.
ALL_SCOPES: tuple[str, ...] = (
    SCOPE_SELECTED_KEYS,
    SCOPE_VISIBLE_KEYS,
    SCOPE_CURRENT_FRAME,
    SCOPE_FRAME_RANGE,
    SCOPE_PLAYBACK_RANGE,
    SCOPE_PREVIEW_RANGE,
    SCOPE_SELECTED_CHANNELS,
    SCOPE_VISIBLE_CHANNELS,
    SCOPE_ALL_CHANNELS,
    SCOPE_SELECTED_OBJECTS,
    SCOPE_SELECTED_BONES,
    SCOPE_MATCHING_TARGETS,
)


_SCOPE_LABELS: dict[str, str] = {
    SCOPE_SELECTED_KEYS: ui_naming.LABEL_SCOPE_SELECTED_KEYS,
    SCOPE_VISIBLE_KEYS: ui_naming.LABEL_SCOPE_VISIBLE_KEYS,
    SCOPE_CURRENT_FRAME: ui_naming.LABEL_SCOPE_CURRENT_FRAME,
    SCOPE_FRAME_RANGE: ui_naming.LABEL_SCOPE_FRAME_RANGE,
    SCOPE_PLAYBACK_RANGE: ui_naming.LABEL_SCOPE_PLAYBACK_RANGE,
    SCOPE_PREVIEW_RANGE: ui_naming.LABEL_SCOPE_PREVIEW_RANGE,
    SCOPE_SELECTED_CHANNELS: ui_naming.LABEL_SCOPE_SELECTED_CHANNELS,
    SCOPE_VISIBLE_CHANNELS: ui_naming.LABEL_SCOPE_VISIBLE_CHANNELS,
    SCOPE_ALL_CHANNELS: ui_naming.LABEL_SCOPE_ALL_CHANNELS,
    SCOPE_SELECTED_OBJECTS: ui_naming.LABEL_SCOPE_SELECTED_OBJECTS,
    SCOPE_SELECTED_BONES: ui_naming.LABEL_SCOPE_SELECTED_BONES,
    SCOPE_MATCHING_TARGETS: ui_naming.LABEL_SCOPE_MATCHING_TARGETS,
}


_SCOPE_TOOLTIPS: dict[str, str] = {
    SCOPE_SELECTED_KEYS:    "Operate on every key currently selected in the active editor",
    SCOPE_VISIBLE_KEYS:     "Operate on every key whose channel is visible in the active editor",
    SCOPE_CURRENT_FRAME:    "Operate only on keys at the scene's current frame",
    SCOPE_FRAME_RANGE:      "Operate on keys whose time falls inside an explicit start/end range",
    SCOPE_PLAYBACK_RANGE:   "Operate on keys inside the scene playback range",
    SCOPE_PREVIEW_RANGE:    "Operate on keys inside the scene preview range",
    SCOPE_SELECTED_CHANNELS:"Operate on keys belonging to the currently selected FCurve channels",
    SCOPE_VISIBLE_CHANNELS: "Operate on keys belonging to every visible FCurve channel",
    SCOPE_ALL_CHANNELS:     "Operate on keys across every animated channel of the active object",
    SCOPE_SELECTED_OBJECTS: "Operate on every selected object's animation data",
    SCOPE_SELECTED_BONES:   "Operate on FCurves driving currently selected pose bones",
    SCOPE_MATCHING_TARGETS: "Operate on identically-named channels across selected targets",
}


# ---------------------------------------------------------------------------
# Enum item factory
# ---------------------------------------------------------------------------

def scope_enum_items(
    scopes: Optional[Iterable[str]] = None,
) -> tuple[tuple[str, str, str], ...]:
    """Return a Blender ``EnumProperty`` items tuple for the given scopes.

    Pass an iterable of ``SCOPE_*`` identifiers to constrain the menu to
    a meaningful subset (e.g. a key-deletion operator only needs key
    scopes, not channel scopes). Order is preserved.

    With no argument, returns every scope in ``ALL_SCOPES`` order.
    """
    chosen: tuple[str, ...] = tuple(scopes) if scopes is not None else ALL_SCOPES
    items: list[tuple[str, str, str]] = []
    for s in chosen:
        if s not in _SCOPE_LABELS:
            continue
        items.append((s, _SCOPE_LABELS[s], _SCOPE_TOOLTIPS[s]))
    return tuple(items)


# ---------------------------------------------------------------------------
# Panel drawing helper
# ---------------------------------------------------------------------------

def draw_scope_selector(
    layout: bpy.types.UILayout,
    context: bpy.types.Context,
    data,
    prop_name: str,
    *,
    panel_id: str,
    title: str = "Scope",
    expand_radio: bool = False,
) -> None:
    """Draw the standard scope selector inside a scope subsection.

    ``data`` is any RNA holder (operator instance, scene PropertyGroup,
    addon prefs) and ``prop_name`` is the EnumProperty attribute. The
    selector renders inside the panel's collapsible scope block so the
    layout matches every other Anim Assist panel.

    ``expand_radio=True`` draws the enum as labelled radio buttons; the
    default uses Blender's compact dropdown.
    """
    body = ui_helpers.scope_block(
        layout,
        context,
        panel_id=panel_id,
        title=title,
    )
    if expand_radio:
        body.prop(data, prop_name, expand=True)
    else:
        body.prop(data, prop_name, text="")


__all__ = [
    "ALL_SCOPES",
    "SCOPE_SELECTED_KEYS",
    "SCOPE_VISIBLE_KEYS",
    "SCOPE_CURRENT_FRAME",
    "SCOPE_FRAME_RANGE",
    "SCOPE_PLAYBACK_RANGE",
    "SCOPE_PREVIEW_RANGE",
    "SCOPE_SELECTED_CHANNELS",
    "SCOPE_VISIBLE_CHANNELS",
    "SCOPE_ALL_CHANNELS",
    "SCOPE_SELECTED_OBJECTS",
    "SCOPE_SELECTED_BONES",
    "SCOPE_MATCHING_TARGETS",
    "scope_enum_items",
    "draw_scope_selector",
]

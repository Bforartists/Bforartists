# --- EXPLAINER SYSTEM EXTENSION ---
"""Draw helpers for inline explainer icons.

Both functions early-exit when the ``show_explainer_help`` preference is
disabled so panels that call them incur zero overhead beyond a single dict
lookup. Panels may safely call these helpers during draw even if the help
registry has not yet been populated — the helpers silently skip unknown
``help_id`` values rather than raising.
"""

from __future__ import annotations

import bpy

from .. import constants
from . import help_registry
from .logging import get_logger

__all__ = [
    "draw_explainer_icon",
    "draw_explainer_label",
]

_log = get_logger(__name__)


def _get_prefs(context: bpy.types.Context):
    addons = getattr(getattr(context, "preferences", None), "addons", None)
    if addons is None:
        return None
    addon = addons.get(constants.ADDON_PACKAGE)
    if addon is None:
        return None
    return getattr(addon, "preferences", None)


def _is_enabled(context: bpy.types.Context) -> bool:
    prefs = _get_prefs(context)
    if prefs is None:
        return False
    return bool(getattr(prefs, "show_explainer_help", False))


def _is_compact(context: bpy.types.Context) -> bool:
    prefs = _get_prefs(context)
    if prefs is None:
        return False
    return bool(getattr(prefs, "compact_ui_mode", False))


def draw_explainer_icon(
    layout: bpy.types.UILayout,
    context: bpy.types.Context,
    help_id: str,
) -> None:
    """Draw a small question-mark icon that opens the help popup for ``help_id``.

    Intended to be placed in a horizontal ``row()`` next to a control. In
    compact mode the icon is still drawn (icons are small); the caller
    decides whether to suppress the neighbouring label.
    """
    if not _is_enabled(context):
        return
    entry = help_registry.get_help(help_id)
    if entry is None:
        return

    sub = layout.row(align=True)
    sub.alignment = "RIGHT"
    op = sub.operator(
        "anim_assist.show_help_popup",
        text="",
        icon=constants.HELP_ICON,
        emboss=False,
    )
    op.help_id = help_id


def draw_explainer_label(
    layout: bpy.types.UILayout,
    context: bpy.types.Context,
    help_id: str,
    text: str | None = None,
) -> None:
    """Draw ``text`` (or the entry label) followed by the explainer icon.

    In compact mode only the icon is drawn so panel density stays tight.
    """
    if not _is_enabled(context):
        if text:
            layout.label(text=text)
        return
    entry = help_registry.get_help(help_id)
    if entry is None:
        if text:
            layout.label(text=text)
        return

    row = layout.row(align=True)
    if not _is_compact(context):
        row.label(text=text if text is not None else entry.label)
    draw_explainer_icon(row, context, help_id)

# --- UI/UX FOUNDATION ---
"""Reusable UI drawing primitives shared across all Anim Assist panels.

Every helper accepts ``(layout, context, …)`` and degrades gracefully if
optional infrastructure (preferences, UI state, help registry) is not yet
available. None of these helpers raise from inside ``draw()``.

Helpers are intentionally thin wrappers around the standard
``layout.prop()`` / ``layout.operator()`` calls so they compose with
plain Blender layout code. Future phases can mix-and-match.

Public API:

* ``section_header(layout, label, *, icon=None)``
* ``subsection(layout, context, panel_id, key, label, *, icon=None,
  default_open=True)`` → ``(body_col, expanded)``
* ``explained_op(layout, context, op_id, *, text=None, icon=None,
  help_id=None)``
* ``explained_prop(layout, context, data, prop, *, help_id=None,
  text=None)``
* ``danger_box(layout, context, *, label="Destructive Actions")``
* ``analysis_box(layout, context, *, title, count=None, details=None,
  panel_id=None)``
* ``scope_block(layout, context, *, panel_id, key="scope",
  title="Scope")``
* ``separator(layout, *, factor=1.0)``
* ``is_compact_mode(context)``
* ``is_help_enabled(context)``
"""

from __future__ import annotations


def wrapped_label(layout, context, text, *, icon="NONE"):
    """Fit explanatory text and target names to a native sidebar's width."""
    import textwrap
    width = getattr(getattr(context, "region", None), "width", 280)
    scale = context.preferences.system.ui_scale
    chars = max(18, int((width - 40) / (7 * max(scale, .5))))
    for index, line in enumerate(textwrap.wrap(text, width=chars) or [""]):
        layout.label(text=line, icon=icon if index == 0 else "NONE")

from typing import Iterable, Optional

import bpy

from .. import constants
from ..core import ui_state as ui_state_mod
from ..core.help_draw import draw_explainer_icon
from ..core.help_registry import get_help


# ---------------------------------------------------------------------------
# Preference probes (cheap, draw-safe)
# ---------------------------------------------------------------------------

def _get_prefs(context: bpy.types.Context):
    addons = getattr(getattr(context, "preferences", None), "addons", None)
    if addons is None:
        return None
    addon = addons.get(constants.ADDON_PACKAGE)
    if addon is None:
        return None
    return getattr(addon, "preferences", None)


def is_compact_mode(context: bpy.types.Context) -> bool:
    """Return True if either the addon-pref *or* the per-session toggle is on."""
    prefs = _get_prefs(context)
    if prefs is not None and bool(getattr(prefs, "compact_ui_mode", False)):
        return True
    state = ui_state_mod.get_ui_state(context)
    if state is not None and bool(getattr(state, "prefer_compact", False)):
        return True
    return False


def is_help_enabled(context: bpy.types.Context) -> bool:
    """Return True when explainer icons should be drawn."""
    prefs = _get_prefs(context)
    if prefs is None:
        return False
    return bool(getattr(prefs, "show_explainer_help", False))


# ---------------------------------------------------------------------------
# Section header / subsection
# ---------------------------------------------------------------------------

def section_header(
    layout: bpy.types.UILayout,
    label: str,
    *,
    icon: Optional[str] = None,
) -> bpy.types.UILayout:
    """Draw a flat section header row and return its layout for chaining."""
    row = layout.row(align=True)
    if icon:
        row.label(text=label, icon=icon)
    else:
        row.label(text=label)
    return row


def subsection(
    layout: bpy.types.UILayout,
    context: bpy.types.Context,
    panel_id: str,
    key: str,
    label: str,
    *,
    icon: Optional[str] = None,
    default_open: bool = True,
) -> tuple[bpy.types.UILayout, bool]:
    """Draw a collapsible subsection.

    Returns ``(body_col, expanded)``. Callers should populate ``body_col``
    only when ``expanded`` is True so collapsed sections do not pay for
    their own draw cost.

    The collapse state is persisted on the WindowManager-scoped UI state
    PropertyGroup. If that PropertyGroup is not available the section
    falls back to ``default_open`` and is always drawn.
    """
    box = layout.box()
    header = box.row(align=True)

    state_row = ui_state_mod.get_section_state(
        context, panel_id, key, default_open=default_open
    )

    if state_row is None:
        # Fallback: no state available, behave as a plain always-open box.
        if icon:
            header.label(text=label, icon=icon)
        else:
            header.label(text=label)
        return box.column(align=True), True

    expanded = bool(state_row.expanded)
    arrow = "DISCLOSURE_TRI_DOWN" if expanded else "DISCLOSURE_TRI_RIGHT"
    header.prop(
        state_row,
        "expanded",
        text="",
        icon=arrow,
        emboss=False,
    )
    if icon:
        header.label(text=label, icon=icon)
    else:
        header.label(text=label)

    if not expanded:
        return box.column(align=True), False
    return box.column(align=True), True


# ---------------------------------------------------------------------------
# Explained operator / property rows
# ---------------------------------------------------------------------------

def explained_op(
    layout: bpy.types.UILayout,
    context: bpy.types.Context,
    op_id: str,
    *,
    text: Optional[str] = None,
    icon: Optional[str] = None,
    help_id: Optional[str] = None,
):
    """Draw a single operator button with a trailing explainer ``?`` icon.

    Returns the operator-properties handle so callers can set additional
    fields, mirroring ``layout.operator(...)``.

    The icon is suppressed automatically when help is disabled or compact
    mode is on **and** the help entry is missing — the button is always
    drawn either way. ``help_id`` defaults to ``"op.<op_id>"`` which
    matches the convention used by ``help_phaseN_entries`` modules.

    Important: do not nest this call inside another ``row(align=True)``;
    the helper creates its own aligned row to keep button + icon glued.
    """
    row = layout.row(align=True)
    kwargs: dict = {}
    if text is not None:
        kwargs["text"] = text
    if icon is not None:
        kwargs["icon"] = icon
    op_props = row.operator(op_id, **kwargs)

    resolved_help = help_id or f"op.{op_id}"
    draw_explainer_icon(row, context, resolved_help)
    return op_props


def explained_prop(
    layout: bpy.types.UILayout,
    context: bpy.types.Context,
    data,
    prop: str,
    *,
    help_id: Optional[str] = None,
    text: Optional[str] = None,
) -> None:
    """Draw a single property control with a trailing explainer icon.

    ``data`` is any RNA-bearing object (Scene, Preferences, PropertyGroup,
    operator instance). ``prop`` is the property name string.
    """
    row = layout.row(align=True)
    rna = getattr(getattr(data, "bl_rna", None), "properties", {}).get(prop) if hasattr(data, "bl_rna") else None
    if rna is not None and rna.type == "ENUM" and not rna.is_enum_flag and text != "":
        # A dropdown in a row shares width with its label and the explainer
        # icon; without a fixed split, even "Preset" clips at sidebar width.
        split = row.split(factor=0.4, align=True)
        split.label(text=(text if text is not None else rna.name) + ":")
        split.prop(data, prop, text="")
    elif text is None:
        row.prop(data, prop)
    else:
        row.prop(data, prop, text=text)
    if help_id:
        draw_explainer_icon(row, context, help_id)


# ---------------------------------------------------------------------------
# Risk hierarchy: danger box
# ---------------------------------------------------------------------------

def danger_box(
    layout: bpy.types.UILayout,
    context: bpy.types.Context,
    *,
    label: str = "Destructive Actions",
) -> bpy.types.UILayout:
    """Return a visually-separated container for destructive operators.

    Future-phase panels should always draw safe alternatives (Mute,
    Hide, Bookmark, Tag) ABOVE the danger box and reserve the box for
    irreversible operators (Delete, Clear All, Reset).

    The container is a ``box`` with a red ``ERROR`` heading. Compact
    mode keeps the icon but drops the heading text.
    """
    box = layout.box()
    header = box.row(align=True)
    if is_compact_mode(context):
        header.label(text="", icon="ERROR")
    else:
        header.label(text=label, icon="ERROR")
    body = box.column(align=True)
    return body


# ---------------------------------------------------------------------------
# Analysis / report box
# ---------------------------------------------------------------------------

def analysis_box(
    layout: bpy.types.UILayout,
    context: bpy.types.Context,
    *,
    title: str,
    count: Optional[int] = None,
    details: Optional[Iterable[str]] = None,
    panel_id: Optional[str] = None,
) -> bpy.types.UILayout:
    """Draw a non-destructive summary box for diagnostic / report tools.

    The body returned can be appended to with extra rows (e.g. ``Jump To``
    operators that select-and-frame the affected items). Detail lines are
    only drawn if the WindowManager UI state's ``show_analysis_details``
    toggle is on, so animators can collapse noise during playback.
    """
    box = layout.box()
    header = box.row(align=True)
    title_text = title if count is None else f"{title}  ({count})"
    header.label(text=title_text, icon="VIEWZOOM")

    state = ui_state_mod.get_ui_state(context)
    show_details = bool(
        state is not None and getattr(state, "show_analysis_details", True)
    )
    if state is not None:
        header.prop(
            state,
            "show_analysis_details",
            text="",
            icon="HIDE_OFF" if show_details else "HIDE_ON",
            emboss=False,
        )

    body = box.column(align=True)
    if details and show_details:
        for line in details:
            body.label(text=line)

    return body


# ---------------------------------------------------------------------------
# Scope / filter block
# ---------------------------------------------------------------------------

def scope_block(
    layout: bpy.types.UILayout,
    context: bpy.types.Context,
    *,
    panel_id: str,
    key: str = "scope",
    title: str = "Scope",
) -> bpy.types.UILayout:
    """Return a collapsible body for the panel's scope/filter controls.

    A thin wrapper around ``subsection`` whose only purpose is to fix the
    icon and title so every Anim Assist panel renders its scope block in
    a recognisable way.
    """
    body, expanded = subsection(
        layout,
        context,
        panel_id,
        key,
        title,
        icon="RESTRICT_SELECT_OFF",
        default_open=True,
    )
    if not expanded:
        # Subsection already drew the collapsed header.
        return body
    return body


# ---------------------------------------------------------------------------
# Spacing
# ---------------------------------------------------------------------------

def draw_context_warning(layout: bpy.types.UILayout, message: str) -> None:
    """Draw missing-selection guidance without hiding the matching panel."""
    layout.label(text=message, icon="INFO")


def separator(layout: bpy.types.UILayout, *, factor: float = 1.0) -> None:
    """Insert a consistent vertical separator."""
    layout.separator(factor=factor)


# ---------------------------------------------------------------------------
# Help-system passthrough re-exports
# ---------------------------------------------------------------------------

#: Re-exported for one-stop import in panels: ``from .ui_helpers import draw_explainer_icon``.
__all__ = [
    "is_compact_mode",
    "is_help_enabled",
    "section_header",
    "subsection",
    "explained_op",
    "explained_prop",
    "danger_box",
    "analysis_box",
    "scope_block",
    "draw_context_warning",
    "separator",
    "draw_explainer_icon",
    "get_help",
]

# --- UI/UX FOUNDATION ---
"""Transient UI state for Anim Assist panels.

This module owns ``AA_UIState``, a ``PropertyGroup`` mounted on
``WindowManager`` under the attribute named by ``constants.UI_STATE_ATTR``.

It is intentionally **separate** from ``core.properties`` so that the UI/UX
foundation layer can be loaded, registered, and torn down independently of
the long-lived scene-level property groups. WindowManager scope is the
right home for collapse/expand state because:

* It is per-session — animators don't want their tweaks to a panel layout
  to be saved into every .blend file they touch.
* It survives addon hot-reload, which keeps the panels stable while a
  developer iterates on Anim Assist itself.
* It is cheap to mutate from ``draw()`` callbacks via the standard
  ``layout.prop()`` machinery (Blender will not redraw extra times).

Public API:

* ``AA_UISectionState`` — one collection row per ``(panel_id, section_key)``.
* ``AA_UIState`` — the parent PropertyGroup.
* ``CLASSES`` — registration tuple consumed by the top-level ``__init__``.
* ``register_properties()`` / ``unregister_properties()`` — attribute
  attachment helpers, mirroring ``core.properties``.
* ``get_ui_state(context)`` — safe accessor that returns ``None`` if
  registration has not yet completed.
* ``get_section_state(context, panel_id, section_key, default_open)`` —
  lazy lookup that creates the row on first access.
"""

from __future__ import annotations

import bpy
from bpy.props import (
    BoolProperty,
    CollectionProperty,
    PointerProperty,
    StringProperty,
)

from .. import constants
from .logging import get_logger

__all__ = [
    "AA_UISectionState",
    "AA_UIState",
    "CLASSES",
    "get_ui_state",
    "get_section_state",
    "register_properties",
    "unregister_properties",
]

_log = get_logger(__name__)


# ---------------------------------------------------------------------------
# Property groups
# ---------------------------------------------------------------------------

class AA_UISectionState(bpy.types.PropertyGroup):
    """One collapse/expand record keyed by ``(panel_id, section_key)``.

    Stored as a collection rather than a dict because Blender's
    ``CollectionProperty`` is the only persistence-friendly mapping
    primitive available to ``PropertyGroup``.
    """

    panel_id: StringProperty(  # type: ignore[valid-type]
        name="Panel",
        description="bl_idname of the owning panel",
        default="",
    )
    section_key: StringProperty(  # type: ignore[valid-type]
        name="Section",
        description="Stable identifier for the subsection within its panel",
        default="",
    )
    expanded: BoolProperty(  # type: ignore[valid-type]
        name="Expanded",
        description="Whether this subsection is currently expanded",
        default=True,
    )


class AA_UIState(bpy.types.PropertyGroup):
    """Parent PropertyGroup mounted on ``WindowManager``.

    Top-level toggles act as global UX preferences that apply to every
    Anim Assist panel that opts into the foundation helpers. Section-level
    state lives inside ``sections``.
    """

    prefer_compact: BoolProperty(  # type: ignore[valid-type]
        name="Prefer Compact",
        description=(
            "Default to a compact layout for foundation-aware panels. "
            "Independent of the addon-pref Compact UI Mode toggle so it "
            "can be flipped per-session without touching preferences"
        ),
        default=False,
    )
    show_analysis_details: BoolProperty(  # type: ignore[valid-type]
        name="Show Analysis Details",
        description=(
            "Show the details list under analysis/report boxes. When "
            "disabled only the summary line and counts are drawn"
        ),
        default=True,
    )
    show_advanced_default: BoolProperty(  # type: ignore[valid-type]
        name="Show Advanced By Default",
        description=(
            "Open Advanced subsections automatically the first time a "
            "panel is drawn in a session"
        ),
        default=False,
    )

    sections: CollectionProperty(type=AA_UISectionState)  # type: ignore[valid-type]


# ---------------------------------------------------------------------------
# Accessors
# ---------------------------------------------------------------------------

def get_ui_state(context: bpy.types.Context | None = None) -> AA_UIState | None:
    """Return the WindowManager-scoped UI state, or ``None`` if missing.

    Safe to call from ``draw()`` callbacks: returns ``None`` rather than
    raising if the property has not yet been attached (e.g. during a
    half-completed unregister).
    """
    ctx = context or bpy.context
    wm = getattr(ctx, "window_manager", None)
    if wm is None:
        return None
    return getattr(wm, constants.UI_STATE_ATTR, None)


def get_section_state(
    context: bpy.types.Context,
    panel_id: str,
    section_key: str,
    default_open: bool = True,
) -> AA_UISectionState | None:
    """Return the collapse-state row for ``(panel_id, section_key)``.

    Creates a new row on first access. Returns ``None`` only if the parent
    UI state PropertyGroup itself is missing.
    """
    state = get_ui_state(context)
    if state is None:
        return None

    for row in state.sections:
        if row.panel_id == panel_id and row.section_key == section_key:
            return row

    try:
        row = state.sections.add()
    except (RuntimeError, AttributeError):
        # The collection may be temporarily read-only mid-unregister.
        _log.debug(
            "ui_state: could not add section row %s/%s",
            panel_id,
            section_key,
        )
        return None

    row.panel_id = panel_id
    row.section_key = section_key
    row.expanded = bool(default_open)
    return row


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

# Order matters: AA_UISectionState must be registered before AA_UIState
# because the parent PropertyGroup references it via CollectionProperty.
CLASSES: tuple[type, ...] = (
    AA_UISectionState,
    AA_UIState,
)


def register_properties() -> None:
    """Attach the UI-state PointerProperty onto WindowManager (idempotent)."""
    if not hasattr(bpy.types.WindowManager, constants.UI_STATE_ATTR):
        setattr(
            bpy.types.WindowManager,
            constants.UI_STATE_ATTR,
            PointerProperty(type=AA_UIState),
        )


def unregister_properties() -> None:
    """Detach the UI-state PointerProperty from WindowManager."""
    try:
        delattr(bpy.types.WindowManager, constants.UI_STATE_ATTR)
    except AttributeError:
        pass

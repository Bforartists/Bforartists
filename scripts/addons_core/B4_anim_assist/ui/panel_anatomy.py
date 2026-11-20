# --- UI/UX FOUNDATION ---
"""Standard panel anatomy: section ordering and the ``PanelAnatomyMixin``.

The animator-facing decision flow is:

    1. Primary Actions      — what do you want to do?
    2. Scope                — narrow what it applies to
    3. Advanced             — optional tweaks
    4. Analysis             — optional inspection of results
    5. Destructive Actions  — irreversible operations, last by design
    6. Help & Notes         — links and explainer surfaces

All panels should follow this ordering by either:

* Calling the section helpers in ``ui_helpers`` in the canonical order, or
* Subclassing ``PanelAnatomyMixin`` and overriding the per-section
  ``draw_<section>`` hooks. ``PanelAnatomyMixin`` is opt-in: existing
  key editing panels keep working without it.

Not every panel needs every section. The mixin skips a section whose
``draw_<section>`` hook is not overridden.
"""

from __future__ import annotations

from typing import Callable

import bpy

from ..core import ui_naming


# ---------------------------------------------------------------------------
# Section enumeration
# ---------------------------------------------------------------------------

#: Canonical, ordered tuple of section keys.
STANDARD_SECTIONS: tuple[str, ...] = (
    "primary",
    "scope",
    "advanced",
    "analysis",
    "destructive",
    "help",
)

#: Mapping of section key → animator-facing section title.
SECTION_TITLES: dict[str, str] = {
    "primary": ui_naming.SECTION_PRIMARY,
    "scope": ui_naming.SECTION_SCOPE,
    "advanced": ui_naming.SECTION_ADVANCED,
    "analysis": ui_naming.SECTION_ANALYSIS,
    "destructive": ui_naming.SECTION_DESTRUCTIVE,
    "help": ui_naming.SECTION_HELP,
}

#: Mapping of section key → matching Blender icon name.
SECTION_ICONS: dict[str, str] = {
    "primary": "PLAY",
    "scope": "RESTRICT_SELECT_OFF",
    "advanced": "PREFERENCES",
    "analysis": "VIEWZOOM",
    "destructive": "ERROR",
    "help": "QUESTION",
}


# ---------------------------------------------------------------------------
# Mixin
# ---------------------------------------------------------------------------

class PanelAnatomyMixin:
    """Mixin that provides a canonical ``draw()`` honouring section order.

    Subclasses override one or more ``draw_<section>`` hooks. Any hook
    that has not been overridden is skipped, so a panel that only needs
    Primary + Destructive does not draw empty boxes.

    Subclasses MUST also call ``super().draw(context)`` if they override
    ``draw`` directly. Most panels should leave ``draw`` alone and only
    implement the per-section hooks.
    """

    # Default no-op hooks. Subclasses override only the sections they need.
    def draw_primary(self, context: bpy.types.Context) -> None: ...  # noqa: E704
    def draw_scope(self, context: bpy.types.Context) -> None: ...  # noqa: E704
    def draw_advanced(self, context: bpy.types.Context) -> None: ...  # noqa: E704
    def draw_analysis(self, context: bpy.types.Context) -> None: ...  # noqa: E704
    def draw_destructive(self, context: bpy.types.Context) -> None: ...  # noqa: E704
    def draw_help(self, context: bpy.types.Context) -> None: ...  # noqa: E704

    def draw(self, context: bpy.types.Context) -> None:
        for section in STANDARD_SECTIONS:
            hook: Callable[[bpy.types.Context], None] | None = getattr(
                self, f"draw_{section}", None
            )
            if hook is None:
                continue
            # Skip the no-op base implementation; only run real overrides.
            base_hook = getattr(PanelAnatomyMixin, f"draw_{section}", None)
            if hook.__func__ is base_hook:  # type: ignore[attr-defined]
                continue
            hook(context)


__all__ = [
    "STANDARD_SECTIONS",
    "SECTION_TITLES",
    "SECTION_ICONS",
    "PanelAnatomyMixin",
]

# --- EXPLAINER SYSTEM EXTENSION ---
"""Collapsible Help Browser.

Provides a reusable :func:`draw_help_browser` function that can be embedded in
any panel (notably ``AA_AddonPreferences.draw``) plus a standalone sidebar
panel ``AA_PT_help_browser`` for the 3D viewport.
"""

from __future__ import annotations

import bpy

from .. import constants
from ..core import help_registry
from ..core.logging import get_logger

_log = get_logger(__name__)


def _get_prefs(context: bpy.types.Context):
    addons = getattr(getattr(context, "preferences", None), "addons", None)
    if addons is None:
        return None
    addon = addons.get(constants.ADDON_PACKAGE)
    if addon is None:
        return None
    return getattr(addon, "preferences", None)


def draw_help_browser(
    layout: bpy.types.UILayout,
    context: bpy.types.Context,
) -> None:
    """Render the Help Browser into ``layout``.

    Groups every registered :class:`HelpEntry` by category. Each row is a
    label plus an icon button that opens the popup operator with the matching
    ``help_id``. The browser is gated on the ``show_explainer_help``
    preference but always renders the master toggle so users can re-enable it
    from inside the browser if they ever turn it off.
    """
    box = layout.box()
    title = box.row()
    title.label(text="Help Browser", icon=constants.HELP_ICON)

    prefs = _get_prefs(context)
    if prefs is None:
        box.label(text="Preferences unavailable", icon="ERROR")
        return

    title.prop(prefs, "show_explainer_help", text="Extended Help")
    title.prop(prefs, "compact_ui_mode", text="Compact")

    groups = help_registry.get_help_by_category()
    if not groups:
        box.label(text="No help entries registered yet", icon="INFO")
        return

    for category, entries in groups.items():
        cat_box = box.box()
        cat_box.label(text=category, icon="DOT")
        col = cat_box.column(align=True)
        for entry in entries:
            row = col.row(align=True)
            row.label(text=entry.label)
            op = row.operator(
                "anim_assist.show_help_popup",
                text="",
                icon=constants.HELP_ICON,
                emboss=False,
            )
            op.help_id = entry.id


class AA_PT_help_browser(bpy.types.Panel):
    """Standalone sidebar panel exposing the Help Browser."""

    bl_label = "AnimAssist Help"
    bl_idname = "AA_PT_help_browser"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "AnimAssist"
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return True

    def draw(self, context: bpy.types.Context) -> None:
        draw_help_browser(self.layout, context)


classes: tuple[type, ...] = (AA_PT_help_browser,)

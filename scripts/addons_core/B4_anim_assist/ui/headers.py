"""Header appends for Graph Editor and Dope Sheet.

Adds curve-editing shortcuts (interpolation types, blend operators) to
the Graph Editor header, and animation-offset / key-type menus to the
Dope Sheet header.  Bforartists-specific items are conditionally hidden
to keep that fork's header uncluttered.
"""

from __future__ import annotations

from typing import Callable

import bpy
from . import is_bforartists
from . import timeline_strip

_appended: list[tuple[type, Callable]] = []


def _draw_graph_header(self, context: bpy.types.Context) -> None:
    """Append interpolation-type buttons and curve-blend operators to the
    Graph Editor header row.

    In stock Blender the row includes batch-interpolation toggles
    (Constant / Linear / Bezier) and a handle-type menu.  These are
    hidden in Bforartists to avoid duplicating its built-in controls.
    """
    layout = self.layout
    row = layout.row(align=True)
    row.separator()

    if not is_bforartists():
        for interp_type, label in (("CONSTANT", "C"), ("LINEAR", "L"), ("BEZIER", "B")):
            op = row.operator("animassist.batch_interpolation", text=label)
            op.interp_type = interp_type
        row.separator()
        row.menu("ANIMASSIST_MT_handle_type", text="", icon="HANDLE_AUTO")

    row.operator("animassist.blend_neighbor", text="", icon="TRACKING_FORWARDS_SINGLE")
    row.operator("animassist.blend_frame", text="", icon="IPO_BEZIER")
    row.operator("animassist.push_pull", text="", icon="FULLSCREEN_EXIT")
    row.operator("animassist.ease_to_ease", text="", icon="IPO_EASE_IN_OUT")
    row.operator("animassist.smooth_keys", text="", icon="SMOOTHCURVE")
    row.operator("animassist.blend_offset", text="", icon="ARROW_LEFTRIGHT")


def _draw_dopesheet_header(self, context: bpy.types.Context) -> None:
    """Append animation-offset toggle and key-type menus to the Dope Sheet
    header row.

    The offset toggle acts as a play/pause for the live animation offset
    mode.  Key-type and interpolation menus are hidden in Bforartists.
    """
    # The Timeline draws the shared configurable catalogue inside its canvas
    # beside the native header; avoid a second copy of the old shortcuts.
    if timeline_strip.is_timeline(context.area):
        return
    layout = self.layout
    row = layout.row(align=True)
    row.separator()

    scene_props = context.scene.anim_assist
    offset_active = scene_props.anim_offset_active
    row.operator(
        "animassist.anim_offset",
        text="",
        icon="PAUSE" if offset_active else "PLAY",
        depress=offset_active,
    )

    if not is_bforartists():
        row.separator()
        row.menu("ANIMASSIST_MT_key_type", text="", icon="KEYTYPE_KEYFRAME_VEC")
        row.menu("ANIMASSIST_MT_interpolation", text="", icon="IPO_BEZIER")


def register() -> None:
    """Append header draw functions to the Graph Editor and Dope Sheet."""
    bpy.types.GRAPH_HT_header.append(_draw_graph_header)
    _appended.append((bpy.types.GRAPH_HT_header, _draw_graph_header))

    bpy.types.DOPESHEET_HT_header.append(_draw_dopesheet_header)
    _appended.append((bpy.types.DOPESHEET_HT_header, _draw_dopesheet_header))


def unregister() -> None:
    """Remove all appended header draw functions."""
    for header_cls, draw_func in reversed(_appended):
        header_cls.remove(draw_func)
    _appended.clear()


classes: list[type] = []

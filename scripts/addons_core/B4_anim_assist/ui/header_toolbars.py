# --- EDITOR HEADER TOOLBARS ---
"""Compact toolbar strips appended to editor headers for rapid-fire tools.

These toolbars surface the most frequently-used animation actions directly
in the header bar of each editor, eliminating the need to open the sidebar
for routine operations like breakdown percentages, retime presets, and
transform matching.

Placement rationale
-------------------
Animators perform these actions hundreds of times per shot.  Burying them
in sidebar panels forces a mouse trip away from the working area.  Header
toolbars keep the controls one click away while eyes stay on the curves,
keys, or viewport.

Category toggles
----------------
Each toolbar group (breakdown, push/pull, retime, selection, trajectory,
matching) can be hidden via scene-level BoolProperties on
``scene.anim_assist.header_show_*``.  A popover gear menu in each header
lets the animator toggle groups on/off to save space.

Registration
------------
Each ``_draw_*`` function is appended to the corresponding Blender header
class.  ``register()`` / ``unregister()`` manage the lifecycle and track
appended functions for clean removal.
"""

from __future__ import annotations

import bpy
from . import timeline_strip

# Track appended draw functions for clean unregister.
_appended_header_draws: list[tuple[type, object]] = []


# ---------------------------------------------------------------------------
# Popover panel for category visibility
# ---------------------------------------------------------------------------

class ANIMASSIST_PT_header_toolbar_options(bpy.types.Panel):
    """Popover panel to toggle which toolbar groups are visible."""

    bl_label = "Toolbar Categories"
    bl_space_type = "PROPERTIES"
    bl_region_type = "HEADER"

    def draw(self, context: bpy.types.Context) -> None:
        """Draw toggle checkboxes for each toolbar category."""
        from ..prefs import get_prefs
        props = context.scene.anim_assist
        layout = self.layout
        prefs = get_prefs(context)
        timeline = timeline_strip.is_timeline(context.area)
        if prefs is not None:
            if timeline:
                layout.label(text="Timeline Placement")
                layout.label(text="Add-on preference")
            layout.prop(prefs, "timeline_toolbar_row")
            layout.separator()
        if timeline:
            layout.label(text="Category Visibility / This Scene")
            layout.label(text="Shared across editor headers")
            for property_name, label in (
                ("header_show_breakdown", "Tween"),
                ("header_show_pushpull", "Curves"),
                ("header_show_retime", "Timing"),
                ("header_show_selection", "Keys"),
                ("header_show_trajectory", "Motion"),
                ("header_show_matching", "Pose"),
            ):
                layout.prop(props, property_name, text=label)
            return
        layout.label(text="Show in Header:")
        layout.prop(props, "header_show_breakdown")
        layout.prop(props, "header_show_pushpull")
        layout.prop(props, "header_show_retime")
        layout.prop(props, "header_show_selection")
        layout.separator()
        layout.label(text="Motion / Matching:")
        layout.prop(props, "header_show_trajectory")
        layout.prop(props, "header_show_matching")


# ---------------------------------------------------------------------------
# Shared toolbar row builders (DRY helpers used by multiple editors)
# ---------------------------------------------------------------------------

def _draw_breakdown_row(layout: bpy.types.UILayout) -> None:
    """Draw breakdown percentage buttons (25/50/75) and a drag-breakdown icon.

    Used identically in both the Dope Sheet and Graph Editor headers so
    animators retain muscle memory when switching editors.
    """
    row = layout.row(align=True)
    row.separator()

    for percent_value, label in ((25, "25"), (50, "50"), (75, "75")):
        op = row.operator(
            "animassist.breakdown_percentage",
            text=label,
        )
        op.percent = percent_value

    row.operator(
        "animassist.modal_drag_breakdown",
        text="",
        icon="MOUSE_MOVE",
    )


def _draw_pushpull_row(layout: bpy.types.UILayout) -> None:
    """Draw push/pull buttons that nudge the current key toward neighbours.

    Four directional buttons: push toward previous, pull toward previous,
    pull toward next, push toward next.
    """
    row = layout.row(align=True)
    row.separator()

    row.operator("animassist.breakdown_push_prev", text="", icon="TRIA_LEFT")
    row.operator("animassist.breakdown_pull_prev", text="", icon="BACK")
    row.operator("animassist.breakdown_pull_next", text="", icon="FORWARD")
    row.operator("animassist.breakdown_push_next", text="", icon="TRIA_RIGHT")


def _draw_retime_row(layout: bpy.types.UILayout) -> None:
    """Draw speed-scaling preset buttons (80/90/110/120%) and a ripple button.

    Each number represents the playback-speed percentage applied to selected
    keys.  The ripple button shifts all downstream keys to accommodate the
    new timing.
    """
    row = layout.row(align=True)
    row.separator()

    for speed_factor, label in ((0.8, "80"), (0.9, "90"), (1.1, "110"), (1.2, "120")):
        op = row.operator(
            "animassist.p6_scale_keys",
            text=label,
        )
        op.scale_factor = speed_factor

    row.operator(
        "animassist.p6_ripple_forward",
        text="",
        icon="TRACKING_FORWARDS_SINGLE",
    )


# ---------------------------------------------------------------------------
# Dope Sheet header toolbar
# ---------------------------------------------------------------------------

def _draw_dopesheet_toolbar(self, context: bpy.types.Context) -> None:
    """Append breakdown, push/pull, retime, and selection shortcuts to the
    Dope Sheet header.

    Each group respects the corresponding ``header_show_*`` scene property
    so the animator can hide categories to save header space.
    """
    if timeline_strip.is_timeline(context.area):
        return
    props = context.scene.anim_assist
    layout = self.layout

    if props.header_show_breakdown:
        _draw_breakdown_row(layout)

    if props.header_show_pushpull:
        _draw_pushpull_row(layout)

    if props.header_show_retime:
        _draw_retime_row(layout)

    # Key selection shortcuts (Dope Sheet only).
    if props.header_show_selection:
        select_row = layout.row(align=True)
        select_row.separator()

        select_row.operator(
            "animassist.select_frame_range",
            text="",
            icon="TRIA_LEFT",
        )
        select_row.operator(
            "animassist.select_all_visible",
            text="",
            icon="KEYFRAME",
        )
        select_row.operator(
            "animassist.select_first_last",
            text="",
            icon="TRIA_RIGHT",
        )

    # Gear icon opens a popover to toggle categories.
    layout.popover(
        panel="ANIMASSIST_PT_header_toolbar_options",
        text="",
        icon="PREFERENCES",
    )


# ---------------------------------------------------------------------------
# Graph Editor header toolbar
# ---------------------------------------------------------------------------

def _draw_graph_editor_toolbar(self, context: bpy.types.Context) -> None:
    """Append breakdown and retime shortcuts to the Graph Editor header.

    Mirrors the Dope Sheet toolbar so muscle memory transfers between editors.
    Omits key-selection shortcuts (Graph Editor has its own selection tools).
    """
    props = context.scene.anim_assist
    layout = self.layout

    if props.header_show_breakdown:
        _draw_breakdown_row(layout)

    if props.header_show_pushpull:
        _draw_pushpull_row(layout)

    if props.header_show_retime:
        _draw_retime_row(layout)

    layout.popover(
        panel="ANIMASSIST_PT_header_toolbar_options",
        text="",
        icon="PREFERENCES",
    )


# ---------------------------------------------------------------------------
# 3D Viewport header toolbar
# ---------------------------------------------------------------------------

def _draw_viewport_toolbar(self, context: bpy.types.Context) -> None:
    """Append trajectory toggle, issue navigation, and quick-match buttons
    to the 3D Viewport header.

    Only draws when the active object is an armature, so it stays invisible
    during modelling or other non-animation work.
    """
    active_object = context.active_object
    if active_object is None or active_object.type != "ARMATURE":
        return

    props = context.scene.anim_assist
    layout = self.layout

    # Trajectory overlay toggle + issue nav.
    if props.header_show_trajectory:
        trajectory_row = layout.row(align=True)
        trajectory_row.separator()

        trajectory_row.operator(
            "animassist.p5_enable_overlay",
            text="",
            icon="CURVE_PATH",
        )
        trajectory_row.operator(
            "animassist.p5_disable_overlay",
            text="",
            icon="PANEL_CLOSE",
        )

        issue_nav_row = layout.row(align=True)
        issue_nav_row.operator(
            "animassist.p5_jump_prev_issue",
            text="",
            icon="TRIA_LEFT",
        )
        issue_nav_row.operator(
            "animassist.p5_run_diagnostics",
            text="",
            icon="VIEWZOOM",
        )
        issue_nav_row.operator(
            "animassist.p5_jump_next_issue",
            text="",
            icon="TRIA_RIGHT",
        )

    # Quick match (only in Pose Mode).
    if props.header_show_matching and context.mode == "POSE":
        match_row = layout.row(align=True)
        match_row.separator()

        match_row.operator("animassist.p8_match_to_world", text="W")
        match_row.operator("animassist.p8_match_to_parent", text="P")
        match_row.operator("animassist.p8_visual_match", text="V")

    layout.popover(
        panel="ANIMASSIST_PT_header_toolbar_options",
        text="",
        icon="PREFERENCES",
    )


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

_classes: list[type] = [
    ANIMASSIST_PT_header_toolbar_options,
]


def register() -> None:
    """Register the popover panel and append toolbar draw functions."""
    from ..core import explainers
    for cls in _classes:
        explainers.register_class(cls)

    _append_pairs = (
        (bpy.types.DOPESHEET_HT_header, _draw_dopesheet_toolbar),
        (bpy.types.GRAPH_HT_header, _draw_graph_editor_toolbar),
        (bpy.types.VIEW3D_HT_header, _draw_viewport_toolbar),
    )

    for header_class, draw_function in _append_pairs:
        header_class.append(draw_function)
        _appended_header_draws.append((header_class, draw_function))
    timeline_strip.register()


def unregister() -> None:
    """Remove all appended toolbar draw functions and unregister panels."""
    timeline_strip.unregister()
    for header_class, draw_function in reversed(_appended_header_draws):
        header_class.remove(draw_function)
    _appended_header_draws.clear()

    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)

# --- TRAJECTORY VISUALIZATION ---
"""Sidebar panels for trajectory visualization and arc diagnostics in 3D viewport.

Two panels, both in VIEW_3D:

1. **Trajectory Overlay** — master enable, display mode, sampling scope,
   visual options (ticks, velocity, tangent, ghost, heatmaps), and
   palette selector. Follows the Primary → Scope → Advanced → Analysis
   section ordering via ``PanelAnatomyMixin``.

2. **Arc Diagnostics** — child panel with detector toggles, threshold
   sliders, navigation (next/prev issue, select bad-arc keys,
   candidate key suggestions), and comparison mode. Renders under the
   parent panel via ``bl_parent_id``.
"""

from __future__ import annotations

import bpy

from ..core.p5_properties import get_p5
from . import ui_helpers as uh
from .editor_placement import View3DSidebarPanel
from .panel_anatomy import PanelAnatomyMixin


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _p5_available(context: bpy.types.Context) -> bool:
    """Return True if trajectory properties are accessible."""
    return get_p5(context) is not None


def _draw_context_warning(layout, context) -> None:
    if get_p5(context) is None:
        layout.label(text="Trajectory property group unavailable.", icon="ERROR")
        return
    obj = getattr(context, "active_object", None)
    if obj is None:
        layout.label(text="No active object.", icon="INFO")


# ---------------------------------------------------------------------------
# Trajectory Overlay panel
# ---------------------------------------------------------------------------

class ANIMASSIST_PT_p5_trajectory(PanelAnatomyMixin, View3DSidebarPanel):
    """Primary trajectory overlay controls."""

    bl_category = "Motion"
    bl_order = 40
    bl_idname = "ANIMASSIST_PT_p5_trajectory"
    bl_label = "Trajectory Overlay"

    def draw_primary(self, context):
        layout = self.layout
        p5 = get_p5(context)
        if p5 is None:
            _draw_context_warning(layout, context)
            return

        # --- Master toggle ---
        row = layout.row(align=True)
        if p5.overlay_enabled:
            row.operator("animassist.p5_disable_overlay",
                         text="Disable Overlay", icon="HIDE_ON")
            row.operator("animassist.p5_refresh_overlay",
                         text="", icon="FILE_REFRESH")
        else:
            row.operator("animassist.p5_enable_overlay",
                         text="Enable Overlay", icon="HIDE_OFF")

        uh.separator(layout)

        # --- Display mode ---
        uh.section_header(layout, "Display Mode", icon="VIS_SEL_11")
        layout.prop(p5, "display_mode", text="")

        if p5.display_mode == "ISOLATE":
            layout.prop(p5, "isolate_target", text="Target", icon="BONE_DATA")

        uh.separator(layout)

        # --- Color preset ---
        layout.prop(p5, "color_preset", text="Palette")

    def draw_scope(self, context):
        layout = self.layout
        p5 = get_p5(context)
        if p5 is None:
            return

        uh.section_header(layout, "Scope", icon="RESTRICT_SELECT_OFF")
        layout.prop(p5, "scope_mode", text="")

        if p5.scope_mode == "AROUND_CURRENT":
            row = layout.row(align=True)
            row.prop(p5, "window_before", text="Before")
            row.prop(p5, "window_after", text="After")
        elif p5.scope_mode == "CUSTOM":
            row = layout.row(align=True)
            row.prop(p5, "custom_start", text="Start")
            row.prop(p5, "custom_end", text="End")

        uh.separator(layout)

        layout.prop(p5, "sample_step", text="Step")
        layout.prop(p5, "max_samples", text="Max Samples")

    def draw_advanced(self, context):
        layout = self.layout
        p5 = get_p5(context)
        if p5 is None:
            return

        uh.section_header(layout, "Visual Options", icon="PREFERENCES")

        col = layout.column(align=True)
        col.prop(p5, "show_frame_ticks")
        col.prop(p5, "show_keyframe_ticks")
        col.prop(p5, "show_frame_numbers")
        col.prop(p5, "show_velocity")
        col.prop(p5, "show_tangent")
        col.prop(p5, "show_ghost_points")
        col.prop(p5, "show_spacing_color")
        col.prop(p5, "show_deviation_heatmap")

        uh.separator(layout)

        layout.prop(p5, "path_width", text="Path Width")
        # space_mode hidden — only WORLD is implemented.
        # Uncomment when Camera/Local modes are implemented:
        # layout.prop(p5, "space_mode", text="Space")

        uh.separator(layout)

        uh.section_header(layout, "Sampling", icon="MOD_WAVE")
        layout.prop(p5, "use_subframe")
        layout.prop(p5, "use_constraints")

    def draw_analysis(self, context):
        layout = self.layout
        p5 = get_p5(context)
        if p5 is None:
            return

        uh.section_header(layout, "Quick Actions", icon="VIEWZOOM")

        row = layout.row(align=True)
        row.operator("animassist.p5_mute_unselected",
                     text="Mute Unselected", icon="RESTRICT_VIEW_ON")

        if p5.display_mode != "ISOLATE":
            obj = getattr(context, "active_object", None)
            bone = getattr(context, "active_pose_bone", None)
            if bone and obj:
                op = layout.operator("animassist.p5_isolate_target",
                                     text=f"Isolate: {bone.name}",
                                     icon="BONE_DATA")
                op.target_key = f"{obj.name}::{bone.name}"
            elif obj:
                op = layout.operator("animassist.p5_isolate_target",
                                     text=f"Isolate: {obj.name}",
                                     icon="OBJECT_DATA")
                op.target_key = f"{obj.name}::"


# ---------------------------------------------------------------------------
# Arc Diagnostics child panel
# ---------------------------------------------------------------------------

class ANIMASSIST_PT_p5_diagnostics(PanelAnatomyMixin, View3DSidebarPanel):
    """Arc and motion diagnostic controls."""

    bl_idname = "ANIMASSIST_PT_p5_diagnostics"
    bl_label = "Arc Diagnostics"
    bl_parent_id = "ANIMASSIST_PT_p5_trajectory"
    bl_options = {"DEFAULT_CLOSED"}

    def draw_primary(self, context):
        layout = self.layout
        p5 = get_p5(context)
        if p5 is None:
            return

        # Run diagnostics button.
        layout.operator("animassist.p5_run_diagnostics",
                        text="Run Diagnostics", icon="ZOOM_ALL")

        uh.separator(layout)

        # --- Navigation ---
        uh.section_header(layout, "Issue Navigation", icon="TRACKING")

        row = layout.row(align=True)
        row.operator("animassist.p5_jump_prev_issue",
                     text="", icon="PREV_KEYFRAME")
        row.operator("animassist.p5_jump_next_issue",
                     text="", icon="NEXT_KEYFRAME")

        layout.operator("animassist.p5_select_bad_arc_keys",
                        text="Select Bad-Arc Keys", icon="KEYFRAME_HLT")
        layout.operator("animassist.p5_suggest_candidates",
                        text="Suggest Candidates", icon="LIGHT")

    def draw_advanced(self, context):
        layout = self.layout
        p5 = get_p5(context)
        if p5 is None:
            return

        # --- Detector toggles ---
        uh.section_header(layout, "Detectors", icon="FILTER")

        col = layout.column(align=True)
        col.prop(p5, "enable_drift_detect")
        col.prop(p5, "enable_flat_detect")
        col.prop(p5, "enable_zigzag_detect")
        col.prop(p5, "enable_pop_detect")
        col.prop(p5, "enable_spacing_detect")
        col.prop(p5, "enable_reversal_detect")
        col.prop(p5, "enable_stop_detect")
        col.prop(p5, "enable_apex_contact_detect")

        uh.separator(layout)

        # --- Thresholds ---
        uh.section_header(layout, "Thresholds", icon="DRIVER")

        col = layout.column(align=True)
        col.prop(p5, "drift_tolerance")
        col.prop(p5, "pop_ratio")
        col.prop(p5, "spacing_hi")
        col.prop(p5, "spacing_lo")

    def draw_analysis(self, context):
        layout = self.layout
        p5 = get_p5(context)
        if p5 is None:
            return

        # --- Comparison mode ---
        uh.section_header(layout, "Comparison", icon="MOD_MIRROR")

        layout.prop(p5, "comparison_enabled")
        if p5.comparison_enabled:
            layout.prop(p5, "comparison_target", text="Compare To", icon="BONE_DATA")


CLASSES: tuple[type, ...] = (
    ANIMASSIST_PT_p5_trajectory,
    ANIMASSIST_PT_p5_diagnostics,
)

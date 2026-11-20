# --- BREAKDOWN AND INBETWEEN TOOLS ---
"""Sidebar panels for breakdown, inbetween, and pose comparison.

Placement:

* ``Breakdown``, ``Subsets``, ``Inbetween``, ``Pose Compare``,
  ``Presets``, and ``Modal`` panels live in the Dope Sheet sidebar — the
  editor animators use for pose-to-pose workflows.
* ``Interpolation`` lives in the Graph Editor sidebar where the
  quaternion / euler / visual-transform toggles are most relevant.

Every panel inherits from :class:`PanelAnatomyMixin` so the canonical
Primary → Scope → Advanced → Analysis → Destructive → Help ordering is
respected, and uses :mod:`..ui.ui_helpers` instead of raw
``layout.operator`` / ``layout.prop`` calls.

No panel is registered in ``VIEW_3D`` (directive rule 2): keyframe and
channel tools do not belong in the viewport sidebar.
"""

from __future__ import annotations

import bpy

from ..core.p3_properties import get_p3
from . import ui_helpers as uh
from .editor_placement import (
    DopeSheetSidebarPanel,
    GraphEditorSidebarPanel,
)
from .panel_anatomy import PanelAnatomyMixin


# ---------------------------------------------------------------------------
# Shared draw helpers
# ---------------------------------------------------------------------------

def _p3_available(context: bpy.types.Context) -> bool:
    """Return True when the breakdown PropertyGroup and an action are present."""
    if get_p3(context) is None:
        return False
    obj = getattr(context, "active_object", None)
    if obj is None:
        return False
    adata = getattr(obj, "animation_data", None)
    return adata is not None and adata.action is not None


def _draw_context_warning(layout, context) -> None:
    obj = getattr(context, "active_object", None)
    if obj is None:
        layout.label(text="No active object.", icon="INFO")
        return
    adata = getattr(obj, "animation_data", None)
    if adata is None or adata.action is None:
        layout.label(text=f"{obj.name} has no animation data.", icon="INFO")
        return
    if get_p3(context) is None:
        layout.label(text="Breakdown property group unavailable.", icon="ERROR")


# ---------------------------------------------------------------------------
# Breakdown Core panel
# ---------------------------------------------------------------------------

class ANIMASSIST_PT_p3_breakdown(PanelAnatomyMixin, DopeSheetSidebarPanel):
    """Primary weighted-breakdown controls."""

    bl_category = "Pose"
    bl_order = 10
    bl_idname = "ANIMASSIST_PT_p3_breakdown"
    bl_label = "Breakdown"

    def draw_primary(self, context):
        layout = self.layout
        if not _p3_available(context):
            _draw_context_warning(layout, context)
            return
        p3 = get_p3(context)

        uh.section_header(layout, "Quick Breakdowns", icon="KEYFRAME_HLT")
        row = layout.row(align=True)
        op = row.operator("animassist.breakdown_percentage", text="25%")
        op.percent = 25
        op = row.operator("animassist.breakdown_percentage", text="50%")
        op.percent = 50
        op = row.operator("animassist.breakdown_percentage", text="75%")
        op.percent = 75

        col = layout.column(align=True)
        uh.explained_op(col, context, "animassist.breakdown_current_frame",
                        text="Breakdown Here", icon="KEY_HLT")
        uh.explained_op(col, context, "animassist.breakdown_weighted", text="Weighted Breakdown")
        uh.explained_op(col, context, "animassist.breakdown_midpoint")
        row = col.row(align=True)
        uh.explained_op(row, context, "animassist.breakdown_favor_prev",
                        text="Favor Prev")
        uh.explained_op(row, context, "animassist.breakdown_favor_next",
                        text="Favor Next")

    def draw_scope(self, context):
        p3 = get_p3(context)
        if p3 is None:
            return
        header, body = self.layout.panel("aa_breakdown_factor", default_closed=True)
        header.label(text="Breakdown Options")
        if body:
            body.prop(p3, "factor", slider=True)
            body.prop(p3, "mode", text="Mode")
            for name in ("quaternion_aware", "euler_wrap_aware", "match_tangents", "auto_key_missing"):
                body.prop(p3, name)

    def draw_advanced(self, context):
        layout = self.layout
        if not _p3_available(context):
            return
        p3 = get_p3(context)
        body, expanded = uh.subsection(
            layout, context, self.bl_idname, "advanced", "Push / Pull",
            icon="FORCE_CHARGE", default_open=False,
        )
        if not expanded:
            return
        row = body.row(align=True)
        row.prop(p3, "push_strength")
        row.prop(p3, "pull_strength")
        grid = body.grid_flow(row_major=True, columns=2, align=True)
        uh.explained_op(grid, context, "animassist.breakdown_push_prev",
                        text="Push Prev")
        uh.explained_op(grid, context, "animassist.breakdown_push_next",
                        text="Push Next")
        uh.explained_op(grid, context, "animassist.breakdown_pull_prev",
                        text="Pull Prev")
        uh.explained_op(grid, context, "animassist.breakdown_pull_next",
                        text="Pull Next")

        body.separator()
        body.prop(p3, "offset_amount")
        uh.explained_op(body, context, "animassist.breakdown_offset",
                        icon="TRANSFORM_ORIGINS")
        uh.explained_op(body, context, "animassist.breakdown_batch_frames",
                        icon="KEYFRAME")
        uh.explained_op(body, context, "animassist.breakdown_numeric",
                        icon="DRIVER")
        uh.explained_op(body, context, "animassist.breakdown_repeat_last",
                        icon="FILE_REFRESH")


# ---------------------------------------------------------------------------
# Subsets panel
# ---------------------------------------------------------------------------

class ANIMASSIST_PT_p3_subsets(PanelAnatomyMixin, DopeSheetSidebarPanel):
    """Channel-kind and axis subset controls."""

    bl_category = "Pose"
    bl_order = 30
    bl_idname = "ANIMASSIST_PT_p3_subsets"
    bl_label = "Breakdown Subsets"

    def draw_primary(self, context):
        layout = self.layout
        if not _p3_available(context):
            _draw_context_warning(layout, context)
            return
        p3 = get_p3(context)

        uh.section_header(layout, "Kind-Only Breakdowns", icon="MODIFIER")
        col = layout.column(align=True)
        uh.explained_op(col, context, "animassist.breakdown_transform_only",
                        icon="OBJECT_DATA")
        uh.explained_op(col, context, "animassist.breakdown_rotation_only",
                        icon="ORIENTATION_GIMBAL")
        uh.explained_op(col, context, "animassist.breakdown_location_only",
                        icon="TRANSFORM_ORIGINS")
        uh.explained_op(col, context, "animassist.breakdown_scale_only",
                        icon="FULLSCREEN_ENTER")
        uh.explained_op(col, context, "animassist.breakdown_selected_controls",
                        icon="RESTRICT_SELECT_OFF")
        uh.explained_op(col, context, "animassist.breakdown_channel_subset",
                        icon="FILTER")

    def draw_scope(self, context):
        layout = self.layout
        if not _p3_available(context):
            return
        p3 = get_p3(context)
        body = uh.scope_block(layout, context, panel_id=self.bl_idname)
        col = body.column(align=True)
        row = col.row(align=True)
        row.prop(p3, "mask_location", toggle=True)
        row.prop(p3, "mask_rotation", toggle=True)
        row = col.row(align=True)
        row.prop(p3, "mask_scale", toggle=True)
        row.prop(p3, "mask_custom", toggle=True)
        axis_header = uh.section_header(col, "Axes")
        from ..core.help_draw import draw_explainer_icon
        draw_explainer_icon(axis_header, context, "prop.p3_mask_axis")
        axis_row = col.row(align=True)
        axis_row.prop(p3, "mask_axis_x", toggle=True)
        axis_row.prop(p3, "mask_axis_y", toggle=True)
        axis_row.prop(p3, "mask_axis_z", toggle=True)
        axis_row.prop(p3, "mask_axis_w", toggle=True)

        uh.explained_prop(col, context, p3, "skip_locked",
                          help_id="prop.p3_skip_locked")
        uh.explained_prop(col, context, p3, "respect_exclusions",
                          help_id="prop.p3_respect_exclusions")


# ---------------------------------------------------------------------------
# Inbetween panel
# ---------------------------------------------------------------------------

class ANIMASSIST_PT_p3_inbetween(PanelAnatomyMixin, DopeSheetSidebarPanel):
    """Inbetween insertion controls."""

    bl_category = "Pose"
    bl_order = 40
    bl_idname = "ANIMASSIST_PT_p3_inbetween"
    bl_label = "Inbetween Tools"

    def draw_primary(self, context):
        layout = self.layout
        if not _p3_available(context):
            _draw_context_warning(layout, context)
            return
        p3 = get_p3(context)

        col = layout.column(align=True)
        uh.explained_op(col, context, "animassist.inbetween_selected_gap",
                        text="Inbetween Gap", icon="KEYTYPE_BREAKDOWN_VEC")
        uh.explained_op(col, context, "animassist.inbetween_distribute",
                        text="Distribute Inbetweens", icon="MOD_ARRAY")
        uh.explained_op(col, context, "animassist.inbetween_on_clusters",
                        text="Inbetween Clusters", icon="STICKY_UVS_LOC")
        header, body = layout.panel("aa_inbetween_options", default_closed=True)
        header.label(text="Inbetween Options")
        if body:
            body.prop(p3, "inbetween_count")


# ---------------------------------------------------------------------------
# Pose compare panel
# ---------------------------------------------------------------------------

class ANIMASSIST_PT_p3_pose_compare(PanelAnatomyMixin, DopeSheetSidebarPanel):
    """Pose snapshot capture + diff + blend controls."""

    bl_category = "Pose"
    bl_order = 70
    bl_idname = "ANIMASSIST_PT_p3_pose_compare"
    bl_label = "Pose Compare"

    def draw_primary(self, context):
        layout = self.layout
        if not _p3_available(context):
            _draw_context_warning(layout, context)
            return

        uh.section_header(layout, "Capture", icon="ARMATURE_DATA")
        col = layout.column(align=True)
        uh.explained_op(col, context, "animassist.pose_snapshot_prev",
                        text="Set Previous Pose", icon="TRACKING_BACKWARDS")
        uh.explained_op(col, context, "animassist.pose_snapshot_next",
                        text="Set Next Pose", icon="TRACKING_FORWARDS")
        uh.explained_op(col, context, "animassist.pose_snapshot_reference",
                        text="Set Reference Pose", icon="OUTLINER_OB_EMPTY")

        uh.section_header(layout, "Apply", icon="POSE_HLT")
        col = layout.column(align=True)
        op = uh.explained_op(col, context, "animassist.breakdown_from_clipboard",
                             text="Breakdown → Previous")
        op.slot = "PREV"
        op = uh.explained_op(col, context, "animassist.breakdown_from_clipboard",
                             text="Breakdown → Next")
        op.slot = "NEXT"
        uh.explained_op(col, context, "animassist.blend_toward_reference",
                        icon="EMPTY_SINGLE_ARROW")

    def draw_analysis(self, context):
        layout = self.layout
        if not _p3_available(context):
            return
        from ..core import pose_compare as pc
        state = pc.get_state()
        count = len(state.last_report) if state.last_report else None
        body = uh.analysis_box(
            layout, context,
            title="Pose Compare Report",
            count=count,
            details=state.last_report[:20] if state.last_report else None,
            panel_id=self.bl_idname,
        )
        uh.explained_op(body, context, "animassist.pose_compare_report",
                        icon="VIEWZOOM")


# ---------------------------------------------------------------------------
# Presets panel
# ---------------------------------------------------------------------------

class ANIMASSIST_PT_p3_presets(PanelAnatomyMixin, DopeSheetSidebarPanel):
    """Built-in + user breakdown presets and exclusion set management."""

    bl_category = "Pose"
    bl_order = 20
    bl_idname = "ANIMASSIST_PT_p3_presets"
    bl_label = "Breakdown Presets"

    def draw_primary(self, context):
        layout = self.layout
        if not _p3_available(context):
            _draw_context_warning(layout, context)
            return
        p3 = get_p3(context)

        uh.section_header(layout, "Built-in Presets", icon="PRESET")
        row = layout.row(align=True)
        row.prop(p3, "active_preset", text="")
        uh.explained_op(row, context, "animassist.apply_preset",
                        text="Apply", icon="PLAY")

    def draw_advanced(self, context):
        layout = self.layout
        if not _p3_available(context):
            return
        p3 = get_p3(context)
        body, expanded = uh.subsection(
            layout, context, self.bl_idname, "user_presets",
            "User Presets", icon="BOOKMARKS", default_open=False,
        )
        if expanded:
            body.template_list(
                "UI_UL_list", "aa_p3_user_presets",
                p3, "user_presets", p3, "user_preset_index", rows=3,
            )
            row = body.row(align=True)
            uh.explained_op(row, context, "animassist.save_preset",
                            text="Save", icon="ADD")
            uh.explained_op(row, context, "animassist.delete_preset",
                            text="Delete", icon="REMOVE")

        body2, expanded2 = uh.subsection(
            layout, context, self.bl_idname, "exclusions",
            "Exclusion Set", icon="FILTER", default_open=False,
        )
        if expanded2:
            body2.template_list(
                "UI_UL_list", "aa_p3_exclusions",
                p3, "exclusion_patterns", p3, "exclusion_index", rows=3,
            )
            row = body2.row(align=True)
            op = uh.explained_op(row, context, "animassist.manage_exclusion_set",
                                 text="Add", icon="ADD")
            op.action = "ADD"
            op = uh.explained_op(row, context, "animassist.manage_exclusion_set",
                                 text="Remove", icon="REMOVE")
            op.action = "REMOVE"
            op = uh.explained_op(row, context, "animassist.manage_exclusion_set",
                                 text="Clear", icon="TRASH")
            op.action = "CLEAR"


# ---------------------------------------------------------------------------
# Modal panel
# ---------------------------------------------------------------------------

class ANIMASSIST_PT_p3_modal(PanelAnatomyMixin, DopeSheetSidebarPanel):
    """Preview-before-commit and modal drag breakdown."""

    bl_category = "Pose"
    bl_order = 60
    bl_idname = "ANIMASSIST_PT_p3_modal"
    bl_label = "Modal Breakdown"

    def draw_primary(self, context):
        layout = self.layout
        if not _p3_available(context):
            _draw_context_warning(layout, context)
            return
        p3 = get_p3(context)

        uh.explained_op(layout, context, "animassist.modal_drag_breakdown",
                        icon="GRIP")
        layout.prop(p3, "modal_sensitivity")

        row = layout.row(align=True)
        uh.explained_op(row, context, "animassist.preview_breakdown",
                        text="Preview", icon="HIDE_OFF")
        uh.explained_op(row, context, "animassist.commit_preview",
                        text="Commit", icon="CHECKMARK")

        if p3.preview_active:
            info = layout.box()
            info.label(
                text=f"Preview staged @ frame {p3.preview_frame:.1f}",
                icon="INFO",
            )


# ---------------------------------------------------------------------------
# Interpolation Options panel — Graph Editor
# ---------------------------------------------------------------------------

class ANIMASSIST_PT_p3_interpolation(PanelAnatomyMixin, GraphEditorSidebarPanel):
    """Quaternion / Euler / visual-transform interpolation options."""

    bl_category = "Keys"
    bl_order = 40
    bl_idname = "ANIMASSIST_PT_p3_interpolation"
    bl_label = "Breakdown Options"

    def draw_primary(self, context):
        layout = self.layout
        if not _p3_available(context):
            _draw_context_warning(layout, context)
            return
        p3 = get_p3(context)

        col = layout.column(align=True)
        uh.explained_prop(col, context, p3, "quaternion_aware",
                          help_id="prop.p3_quaternion_aware")
        uh.explained_prop(col, context, p3, "euler_wrap_aware",
                          help_id="prop.p3_euler_wrap_aware")
        uh.explained_prop(col, context, p3, "match_tangents",
                          help_id="prop.p3_match_tangents")
        uh.explained_prop(col, context, p3, "auto_key_missing",
                          help_id="prop.p3_auto_key_missing")

    def draw_advanced(self, context):
        layout = self.layout
        if not _p3_available(context):
            return
        p3 = get_p3(context)
        body, expanded = uh.subsection(
            layout, context, self.bl_idname, "visual_xform",
            "Visual Transform", icon="CON_TRANSFORM", default_open=False,
        )
        if not expanded:
            return
        uh.explained_prop(body, context, p3, "visual_transform",
                          help_id="prop.p3_visual_transform")
        uh.explained_prop(body, context, p3, "space",
                          help_id="prop.p3_space_toggle")
        uh.explained_prop(body, context, p3, "preserve_world_contact",
                          help_id="prop.p3_preserve_world_contact")
        uh.explained_prop(body, context, p3, "preserve_child_contact",
                          help_id="prop.p3_preserve_child_contact")


# ---------------------------------------------------------------------------
# Registration tuple
# ---------------------------------------------------------------------------

class ANIMASSIST_PT_graph_breakdown(GraphEditorSidebarPanel):
    bl_idname = "ANIMASSIST_PT_graph_breakdown"
    bl_label = "Breakdown"

    def draw(self, context):
        self.layout.operator("animassist.breakdown_current_frame", text="Breakdown at Current Frame")
        self.layout.operator("animassist.breakdown_midpoint", text="Midpoint Breakdown")


class ANIMASSIST_PT_p3_options_dope(PanelAnatomyMixin, DopeSheetSidebarPanel):
    bl_idname = "ANIMASSIST_PT_p3_options_dope"
    bl_label = "Visual Breakdown Options"
    draw_primary = ANIMASSIST_PT_p3_interpolation.draw_advanced


CLASSES: tuple[type, ...] = (
    ANIMASSIST_PT_p3_breakdown,
    ANIMASSIST_PT_p3_subsets,
    ANIMASSIST_PT_p3_inbetween,
    ANIMASSIST_PT_p3_pose_compare,
    ANIMASSIST_PT_p3_presets,
    ANIMASSIST_PT_p3_modal,
    ANIMASSIST_PT_p3_interpolation,
    ANIMASSIST_PT_graph_breakdown,
    ANIMASSIST_PT_p3_options_dope,
)

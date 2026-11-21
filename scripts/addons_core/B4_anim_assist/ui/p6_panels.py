# --- RETIMING AND TIMING DIAGNOSTICS ---
"""Sidebar panels for retiming controls and timing diagnostics in Dope Sheet and Graph Editor.

Two panels, both appearing in Dope Sheet (primary) and Graph Editor
(secondary via ``make_editor_variants``):

1. **Retime** — master retiming controls: anchor/pivot, scale, offset,
   time warp, ripple edit, timing range, gap tools, snap/clean. Follows
   the Primary → Scope → Advanced → Analysis section ordering via
   ``PanelAnatomyMixin``.

2. **Timing Diagnostics** — child panel (DEFAULT_CLOSED) with gap/cluster
   reporting, navigation, and report copy. Rendered under the parent panel
   via ``bl_parent_id``.
"""

from __future__ import annotations

import bpy

from ..core.p6_properties import get_p6
from ..operators.p6_gap_ops import get_cached_gaps
from ..operators.p6_diag_ops import get_cached_diag
from . import ui_helpers as uh
from .editor_placement import DopeSheetSidebarPanel, make_editor_variants
from .panel_anatomy import PanelAnatomyMixin


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _p6_available(context: bpy.types.Context) -> bool:
    return get_p6(context) is not None


def _has_active_action(context: bpy.types.Context) -> bool:
    obj = getattr(context, "active_object", None)
    if obj is None:
        return False
    adata = getattr(obj, "animation_data", None)
    return adata is not None and getattr(adata, "action", None) is not None


def _draw_no_action_warning(layout: bpy.types.UILayout, context: bpy.types.Context) -> None:
    if not _p6_available(context):
        layout.label(text="Retiming properties unavailable.", icon="ERROR")
        return
    if not _has_active_action(context):
        layout.label(text="No active action.", icon="INFO")


# ---------------------------------------------------------------------------
# Parent panel: Retime
# ---------------------------------------------------------------------------

class ANIMASSIST_PT_p6_retime(PanelAnatomyMixin, DopeSheetSidebarPanel):
    """Retiming controls for scaling, offsetting, and manipulating keyframe timing."""

    bl_category = "Motion"
    bl_order = 30
    bl_idname = "ANIMASSIST_PT_p6_retime"
    bl_label = "Retime"

    # ---- Primary: scale and offset actions ----

    def draw_primary(self, context: bpy.types.Context) -> None:
        layout = self.layout
        p6 = get_p6(context)
        if p6 is None or not _has_active_action(context):
            _draw_no_action_warning(layout, context)
            return

        layout.label(text=f"Target: {context.active_object.name} · {p6.range_mode.title()} range")
        for op, label in (("p6_scale_keys", "Scale Keys"), ("p6_modal_scale", "Interactive Scale"),
                          ("p6_time_warp", "Time Warp"), ("p6_offset_keys", "Offset Keys"),
                          ("p6_modal_offset", "Interactive Offset"), ("p6_reverse_keys", "Reverse Keys"),
                          ("p6_bake_timing", "Bake Timing"), ("p6_match_timing", "Match Timing"),
                          ("p6_reset_timing", "Reset Timing")):
            layout.operator(f"animassist.{op}", text=label)
        header, body = layout.panel("aa_retime_options", default_closed=True)
        header.label(text="Retime Options")
        if body:
            body.prop(p6, "anchor_mode", text="Anchor")
            if p6.anchor_mode == "CUSTOM":
                body.prop(p6, "pivot_frame")
            body.operator("animassist.p6_set_pivot", text="Set Pivot from Playhead")
            body.prop(p6, "scale_factor", text="Scale Factor")
            body.prop(p6, "offset_frames", text="Offset Frames")

    # ---- Scope: timing range ----

    def draw_scope(self, context: bpy.types.Context) -> None:
        layout = self.layout
        p6 = get_p6(context)
        if p6 is None:
            return

        body, expanded = uh.subsection(
            layout, context,
            "p6_retime", "timing_range",
            "Timing Range",
            icon="MOD_LINEART",
            default_open=False,
        )
        if not expanded:
            return

        body.prop(p6, "range_mode", text="")

        if p6.range_mode == "CUSTOM":
            row = body.row(align=True)
            row.prop(p6, "range_start", text="Start")
            row.prop(p6, "range_end",   text="End")

            row2 = body.row(align=True)
            row2.operator("animassist.p6_set_range_start", text="", icon="TRIA_LEFT")
            row2.operator("animassist.p6_set_range_end",   text="", icon="TRIA_RIGHT")

        elif p6.range_mode == "SELECTION":
            body.label(text="Range from selected keys", icon="RESTRICT_SELECT_OFF")

        row3 = body.row(align=True)
        row3.operator("animassist.p6_store_range",          text="Store",    icon="BOOKMARKS")
        row3.operator("animassist.p6_restore_range",        text="Restore",  icon="RECOVER_LAST")
        row3.operator("animassist.p6_clear_range",          text="Clear",    icon="X")

        body.operator("animassist.p6_select_keys_in_range", text="Select Keys in Range",
                      icon="RESTRICT_SELECT_OFF")

        row4 = body.row(align=True)
        row4.operator("animassist.p6_scale_range",  text="Scale Range",  icon="CON_SIZELIKE")
        row4.operator("animassist.p6_offset_range", text="Offset Range", icon="NEXT_KEYFRAME")

    # ---- Advanced: ripple and compression ----

    def draw_advanced(self, context: bpy.types.Context) -> None:
        layout = self.layout
        p6 = get_p6(context)
        if p6 is None:
            return

        body, expanded = uh.subsection(
            layout, context,
            "p6_retime", "ripple",
            "Ripple Edit",
            icon="FORCE_MAGNETIC",
            default_open=False,
        )
        if not expanded:
            return

        body.prop(p6, "ripple_delta", text="Ripple Amount")

        row = body.row(align=True)
        uh.explained_op(
            row, context,
            "animassist.p6_ripple_forward",
            text="Forward",
            icon="FRAME_NEXT",
            help_id="op.animassist.p6_ripple_forward",
        )
        uh.explained_op(
            row, context,
            "animassist.p6_ripple_backward",
            text="Backward",
            icon="FRAME_PREV",
            help_id="op.animassist.p6_ripple_backward",
        )
        body.operator("animassist.p6_ripple_to_end", text="Ripple to End", icon="TRACKING_FORWARDS")

        body.separator(factor=0.5)
        body.prop(p6, "insert_frames", text="Frame Count")
        row2 = body.row(align=True)
        uh.explained_op(
            row2, context,
            "animassist.p6_insert_time",
            text="Insert Time",
            icon="ADD",
            help_id="op.animassist.p6_insert_time",
        )
        uh.explained_op(
            row2, context,
            "animassist.p6_remove_time",
            text="Remove Time",
            icon="REMOVE",
            help_id="op.animassist.p6_remove_time",
        )
        body.operator("animassist.p6_compress_timing", text="Compress Timing…", icon="FULLSCREEN_EXIT")

        # Gap tools sub-section.
        body.separator(factor=0.5)
        body.label(text="Gap Tools", icon="SEQ_SPLITVIEW")
        body.prop(p6, "gap_threshold",  text="Gap Threshold")
        body.prop(p6, "cluster_radius", text="Cluster Radius")
        body.prop(p6, "gap_fill_mode",  text="Fill Mode")

        row3 = body.row(align=True)
        row3.operator("animassist.p6_detect_gaps", text="Detect Gaps",   icon="VIEWZOOM")
        row3.operator("animassist.p6_fill_gaps",   text="Fill Gaps",     icon="FIXED_SIZE")
        body.operator("animassist.p6_collapse_gap", text="Collapse Gap at Playhead",
                      icon="GRIP")

        row4 = body.row(align=True)
        row4.operator("animassist.p6_distribute_keys",  text="Distribute", icon="ALIGN_JUSTIFY")
        row4.operator("animassist.p6_normalize_spacing", text="Normalize",  icon="NLA_PUSHDOWN")

        # Snap & clean.
        body.separator(factor=0.5)
        body.label(text="Snap & Clean", icon="SNAP_ON")
        row5 = body.row(align=True)
        uh.explained_op(
            row5, context,
            "animassist.p6_snap_to_frames",
            text="Snap",
            icon="SNAP_GRID",
            help_id="op.animassist.p6_snap_to_frames",
        )
        uh.explained_op(
            row5, context,
            "animassist.p6_clear_doubles",
            text="Dedup",
            icon="PARTICLES",
            help_id="op.animassist.p6_clear_doubles",
        )

        # Modal preferences.
        body.separator(factor=0.5)
        body.label(text="Modal Preferences", icon="PREFERENCES")
        body.prop(p6, "modal_snap",        text="Snap to Frames")
        body.prop(p6, "modal_show_header", text="Show Header Delta")


# ---------------------------------------------------------------------------
# Child panel: Timing Diagnostics
# ---------------------------------------------------------------------------

class ANIMASSIST_PT_p6_retime_diag(DopeSheetSidebarPanel):
    """Timing diagnostics sub-panel for analyzing gaps and timing clusters."""

    bl_idname      = "ANIMASSIST_PT_p6_retime_diag"
    bl_label       = "Timing Diagnostics"
    bl_parent_id   = "ANIMASSIST_PT_p6_retime"
    bl_options     = {"DEFAULT_CLOSED"}

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        p6 = get_p6(context)
        if p6 is None:
            layout.label(text="Retiming properties unavailable.", icon="ERROR")
            return

        # Run / Clear row.
        row = layout.row(align=True)
        uh.explained_op(
            row, context,
            "animassist.p6_run_diagnostics",
            text="Run Diagnostics",
            icon="VIEWZOOM",
            help_id="op.animassist.p6_run_diagnostics",
        )
        if get_cached_diag() is not None:
            row.operator("animassist.p6_clear_diagnostics", text="", icon="X")

        # Result summary.
        result = p6.last_diag_result
        if result != "NONE":
            box = layout.box()
            col = box.column(align=True)

            # Score badge.
            score = p6.last_diag_score
            if score >= 0:
                score_row = col.row(align=True)
                if score >= 80:
                    icon = "CHECKMARK"
                elif score >= 50:
                    icon = "ERROR"
                else:
                    icon = "CANCEL"
                score_row.label(text=f"Score: {score:.0f}/100", icon=icon)

            # Counts.
            if p6.last_diag_gap_count > 0:
                col.label(text=f"Gaps: {p6.last_diag_gap_count}", icon="SEQ_SPLITVIEW")
            if p6.last_diag_cluster_count > 0:
                col.label(text=f"Clusters: {p6.last_diag_cluster_count}", icon="PARTICLES")
            if result == "CLEAN":
                col.label(text="No issues found", icon="CHECKMARK")

            # Gap navigation.
            if get_cached_gaps():
                box.separator(factor=0.3)
                nav_row = box.row(align=True)
                nav_row.operator("animassist.p6_jump_prev_gap", text="", icon="PREV_KEYFRAME")
                nav_row.operator("animassist.p6_jump_next_gap", text="", icon="NEXT_KEYFRAME")
                nav_row.label(text="Gap navigation")

            # Cluster navigation.
            d = get_cached_diag()
            if d is not None and d.clusters:
                cluster_row = box.row(align=True)
                cluster_row.label(text="", icon="PARTICLES")
                cluster_row.operator("animassist.p6_jump_next_cluster",
                                     text="Next Cluster", icon="NEXT_KEYFRAME")

            # Detail listing (collapsible).
            box.prop(p6, "show_diag_details",
                     text="Details",
                     icon="DISCLOSURE_TRI_DOWN" if p6.show_diag_details else "DISCLOSURE_TRI_RIGHT",
                     toggle=True)

            if p6.show_diag_details and d is not None:
                detail_col = box.column(align=True)
                for gap in d.gaps:
                    detail_col.label(
                        text=f"  Gap {gap.start_frame:.0f}→{gap.end_frame:.0f} "
                             f"({gap.size:.0f}f)",
                        icon="SEQ_SPLITVIEW",
                    )
                for cluster in d.clusters:
                    detail_col.label(
                        text=f"  Cluster ~{cluster.center:.0f}f "
                             f"({len(cluster.frames)} keys)",
                        icon="PARTICLES",
                    )

            # Copy report button.
            box.separator(factor=0.3)
            uh.explained_op(
                box, context,
                "animassist.p6_copy_diag_report",
                text="Copy Report",
                icon="COPYDOWN",
                help_id="op.animassist.p6_copy_diag_report",
            )

        else:
            layout.label(text="No results yet — click Run Diagnostics.", icon="INFO")

        # Threshold controls.
        layout.separator(factor=0.5)
        layout.label(text="Thresholds", icon="PREFERENCES")
        layout.prop(p6, "gap_threshold",  text="Gap Threshold")
        layout.prop(p6, "cluster_radius", text="Cluster Radius")


# ---------------------------------------------------------------------------
# Cross-editor variants — also appear in Graph Editor sidebar
# ---------------------------------------------------------------------------

# Build Dope Sheet variants (base class already targets DOPESHEET_EDITOR).
_DS_CLASSES: tuple[type, ...] = (
    ANIMASSIST_PT_p6_retime,
    ANIMASSIST_PT_p6_retime_diag,
)

# Build Graph Editor variants — share the same draw() but with GE space.
_GE_PARENT, _GE_DIAG = make_editor_variants(
    ANIMASSIST_PT_p6_retime,      ["GRAPH_EDITOR"]
), make_editor_variants(
    ANIMASSIST_PT_p6_retime_diag, ["GRAPH_EDITOR"]
)

# Patch the child panel's bl_parent_id to reference the GE parent.
# make_editor_variants produces a dynamically-created type; we adjust it.
if _GE_DIAG:
    _ge_diag_cls = _GE_DIAG[0]
    _ge_diag_cls.bl_parent_id = _GE_PARENT[0].bl_idname if _GE_PARENT else ANIMASSIST_PT_p6_retime.bl_idname


CLASSES: tuple[type, ...] = (
    *_DS_CLASSES,
    *(_GE_PARENT or ()),
    *(_GE_DIAG   or ()),
)

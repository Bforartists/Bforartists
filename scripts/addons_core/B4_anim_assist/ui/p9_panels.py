# --- MIRRORING AND PAIR DETECTION PANELS ---
"""Sidebar panels for pose mirroring, pair detection, and symmetry helpers.

Panel placement:
    Dope Sheet — primary home (keyframe-centric mirror workflows)
    Graph Editor — lightweight variant via make_editor_variants()
    View 3D — secondary for pose-oriented mirror tools

Uses PanelAnatomyMixin section hooks:
    draw_primary   — mirror buttons, quick actions, swap L/R
    draw_scope     — channel filters, axis mask, mirror space, naming pattern
    draw_advanced  — pair manager, naming exceptions, presets, diagnostics
"""

from __future__ import annotations

import bpy

from ..core.p9_properties import get_p9
from ..ui import ui_helpers as uh
from ..ui.panel_anatomy import PanelAnatomyMixin
from ..ui.editor_placement import (
    DopeSheetSidebarPanel,
    View3DSidebarPanel,
    make_editor_variants,
)


# ---------------------------------------------------------------------------
# Availability helpers
# ---------------------------------------------------------------------------

def _p9_available(context: bpy.types.Context) -> bool:
    return get_p9(context) is not None


def _has_active_armature(context: bpy.types.Context) -> bool:
    obj = context.active_object
    return obj is not None and obj.type == "ARMATURE"


def _in_pose_mode(context: bpy.types.Context) -> bool:
    return context.mode == "POSE" and _has_active_armature(context)


# ---------------------------------------------------------------------------
# Main panel — Dope Sheet
# ---------------------------------------------------------------------------

class ANIMASSIST_PT_p9_mirror(PanelAnatomyMixin, DopeSheetSidebarPanel):
    """Pose mirroring and symmetry tools for L/R bone pairs."""

    bl_category = "Pose"
    bl_order = 50
    bl_idname = "ANIMASSIST_PT_p9_mirror"
    bl_label = "Mirror & Symmetry"

    # ── Primary: mirror buttons, quick actions ────────────────────────

    def draw_primary(self, context: bpy.types.Context) -> None:
        layout = self.layout

        # ── Quick mirror ──
        uh.section_header(layout, "Quick Mirror", icon="MOD_MIRROR")
        if not _in_pose_mode(context):
            layout.label(text="Enter Pose Mode to use mirror tools", icon="INFO")
            return

        uh.explained_op(
            layout, context,
            "animassist.p9_mirror_pose",
            text="Mirror Pose", icon="MOD_MIRROR",
            help_id="op.animassist.p9_mirror_pose",
        )

        row = layout.row(align=True)
        uh.explained_op(
            row, context,
            "animassist.p9_mirror_selected",
            text="Selected", icon="EDITMODE_HLT",
            help_id="op.animassist.p9_mirror_selected",
        )
        uh.explained_op(
            row, context,
            "animassist.p9_swap_poses",
            text="Swap", icon="LOOP_BACK",
            help_id="op.animassist.p9_swap_poses",
        )

        uh.separator(layout)

        # ── Selection ──
        uh.section_header(layout, "Selection", icon="RESTRICT_SELECT_OFF")
        uh.explained_op(
            layout, context,
            "animassist.p9_select_opposite",
            text="Select Opposite", icon="RESTRICT_SELECT_OFF",
            help_id="op.animassist.p9_select_opposite",
        )

        row = layout.row(align=True)
        uh.explained_op(
            row, context,
            "animassist.p9_add_opposite",
            text="Add Opposite", icon="ADD",
            help_id="op.animassist.p9_add_opposite",
        )
        uh.explained_op(
            row, context,
            "animassist.p9_swap_selection",
            text="Swap", icon="LOOP_BACK",
            help_id="op.animassist.p9_swap_selection",
        )

    # ── Scope: channel filters, axis toggles ──────────────────────────

    def draw_scope(self, context: bpy.types.Context) -> None:
        layout = self.layout
        p9 = get_p9(context)
        if p9 is None:
            return

        uh.section_header(layout, "Mirror Settings", icon="SETTINGS")

        uh.explained_prop(
            layout, context, p9, "mirror_axis",
            help_id="p9_axis_mask",
        )

        uh.explained_prop(
            layout, context, p9, "mirror_space",
        )

        uh.separator(layout)

        # ── Channel filters ──
        uh.section_header(layout, "Channel Filters", icon="FILTER")
        row = layout.row(align=True)
        row.prop(p9, "mirror_location", text="Loc", toggle=True)
        row.prop(p9, "mirror_rotation", text="Rot", toggle=True)
        row.prop(p9, "mirror_scale", text="Scale", toggle=True)

        uh.explained_prop(
            layout, context, p9, "axis_mask", text="Axes",
        )

        uh.separator(layout)

        row = layout.row(align=True)
        row.prop(p9, "mirror_keyed_only", text="Keyed Only")
        row.prop(p9, "mirror_visible_only", text="Visible Only")

        row = layout.row(align=True)
        row.prop(p9, "respect_locks", text="Respect Locks")
        row.prop(p9, "respect_drivers", text="Respect Drivers")

        row = layout.row(align=True)
        row.prop(p9, "auto_key_mirror", text="Auto Key")
        row.prop(p9, "maintain_offset", text="Maintain Offset")

    # ── Advanced: pair manager, naming exceptions, presets, diagnostics ─

    def draw_advanced(self, context: bpy.types.Context) -> None:
        layout = self.layout
        p9 = get_p9(context)
        if p9 is None:
            return

        # ── Naming Pattern ──
        body, expanded = uh.subsection(
            layout, context,
            "p9_mirror", "naming_pattern",
            "Naming Pattern",
            icon="TEXT",
            default_open=False,
        )
        if expanded:
            uh.explained_prop(
                body, context, p9, "naming_pattern",
                help_id="op.animassist.p9_custom_pattern",
            )
            if p9.naming_pattern == "CUSTOM":
                body.prop(p9, "custom_left_pattern", text="Left")
                body.prop(p9, "custom_right_pattern", text="Right")

            uh.separator(body)
            row = body.row(align=True)
            uh.explained_op(
                row, context,
                "animassist.p9_build_cache",
                text="Build Cache", icon="FILE_REFRESH",
                help_id="op.animassist.p9_build_cache",
            )
            if p9.naming_pattern == "CUSTOM":
                uh.explained_op(
                    row, context,
                    "animassist.p9_custom_pattern",
                    text="Apply Pattern", icon="CHECKMARK",
                    help_id="op.animassist.p9_custom_pattern",
                )

        # ── Pair Overrides ──
        body, expanded = uh.subsection(
            layout, context,
            "p9_mirror", "pair_overrides",
            "Pair Overrides",
            icon="BONE_DATA",
            default_open=False,
        )
        if expanded:
            if p9.pair_overrides:
                for i, override in enumerate(p9.pair_overrides):
                    row = body.row(align=True)
                    row.label(text=f"{override.bone_a} ↔ {override.bone_b}")
                    row.operator("animassist.p9_remove_pair_override", text="", icon="X").index = i
            else:
                body.label(text="No pair overrides")

            uh.separator(body)
            row = body.row(align=True)
            uh.explained_op(
                row, context,
                "animassist.p9_add_pair_override",
                text="Add", icon="ADD",
                help_id="op.animassist.p9_add_pair_override",
            )
            uh.explained_op(
                row, context,
                "animassist.p9_save_pair_preset",
                text="Save Preset", icon="FILE_TICK",
                help_id="op.animassist.p9_save_pair_preset",
            )
            uh.explained_op(
                row, context,
                "animassist.p9_load_pair_preset",
                text="Load Preset", icon="FILE_FOLDER",
                help_id="op.animassist.p9_load_pair_preset",
            )

        # ── Naming Exceptions ──
        body, expanded = uh.subsection(
            layout, context,
            "p9_mirror", "naming_exceptions",
            "Naming Exceptions",
            icon="PINNED",
            default_open=False,
        )
        if expanded:
            if p9.naming_exceptions:
                for i, exception in enumerate(p9.naming_exceptions):
                    row = body.row(align=True)
                    row.label(text=f"{exception.original} → {exception.opposite}")
                    row.operator("animassist.p9_remove_naming_exception", text="", icon="X").index = i
            else:
                body.label(text="No naming exceptions")

            uh.separator(body)
            row = body.row(align=True)
            uh.explained_op(
                row, context,
                "animassist.p9_add_naming_exception",
                text="Add", icon="ADD",
                help_id="op.animassist.p9_add_naming_exception",
            )

        # ── Advanced Operations ──
        body, expanded = uh.subsection(
            layout, context,
            "p9_mirror", "advanced_ops",
            "Advanced Operations",
            icon="MODIFIER",
            default_open=False,
        )
        if expanded:
            uh.explained_op(
                body, context,
                "animassist.p9_mirror_frame",
                text="Mirror Frame", icon="FRAME_PREV",
                help_id="op.animassist.p9_mirror_frame",
            )
            uh.explained_op(
                body, context,
                "animassist.p9_mirror_range",
                text="Mirror Range", icon="RENDER_ANIMATION",
                help_id="op.animassist.p9_mirror_range",
            )
            uh.explained_op(
                body, context,
                "animassist.p9_mirror_preview",
                text="Preview Mirror", icon="HIDE_OFF",
                help_id="op.animassist.p9_mirror_preview",
            )

            uh.separator(body)

            row = body.row(align=True)
            uh.explained_op(
                row, context,
                "animassist.p9_visual_mirror",
                text="Visual", icon="HIDE_OFF",
                help_id="op.animassist.p9_visual_mirror",
            )
            uh.explained_op(
                row, context,
                "animassist.p9_mirror_with_offset",
                text="With Offset", icon="ADD",
                help_id="op.animassist.p9_mirror_with_offset",
            )
            uh.explained_op(
                row, context,
                "animassist.p9_mirror_without_offset",
                text="No Offset", icon="REMOVE",
                help_id="op.animassist.p9_mirror_without_offset",
            )

            uh.separator(body)

            uh.explained_op(
                body, context,
                "animassist.p9_batch_mirror",
                text="Batch Mirror", icon="GROUP",
                help_id="op.animassist.p9_batch_mirror",
            )
            uh.explained_op(
                body, context,
                "animassist.p9_batch_mirror_active_side",
                text="Batch Mirror Active Side", icon="GROUP",
                help_id="op.animassist.p9_batch_mirror_active_side",
            )
            uh.explained_op(
                body, context,
                "animassist.p9_repeat_mirror",
                text="Repeat Mirror", icon="FILE_REFRESH",
                help_id="op.animassist.p9_repeat_mirror",
            )

        # ── Diagnostics ──
        body, expanded = uh.subsection(
            layout, context,
            "p9_mirror", "diagnostics",
            "Diagnostics",
            icon="INFO",
            default_open=False,
        )
        if expanded:
            row = body.row(align=True)
            uh.explained_op(
                row, context,
                "animassist.p9_validate_pairs",
                text="Validate Pairs", icon="CHECKMARK",
                help_id="op.animassist.p9_validate_pairs",
            )
            uh.explained_op(
                row, context,
                "animassist.p9_nav_next_unpaired",
                text="Next Unpaired", icon="TRIA_RIGHT",
                help_id="op.animassist.p9_nav_next_unpaired",
            )

            uh.separator(body)

            uh.explained_op(
                body, context,
                "animassist.p9_mirror_report",
                text="Mirror Report", icon="TEXT",
                help_id="op.animassist.p9_mirror_report",
            )
            uh.explained_op(
                body, context,
                "animassist.p9_missing_warning",
                text="Check Missing Pairs", icon="ERROR",
                help_id="op.animassist.p9_missing_warning",
            )
            uh.explained_op(
                body, context,
                "animassist.p9_ambiguous_warning",
                text="Check Ambiguous Names", icon="ERROR",
                help_id="op.animassist.p9_ambiguous_warning",
            )
            uh.explained_op(
                body, context,
                "animassist.p9_channel_resolver",
                text="Channel Resolver", icon="CONSOLE",
                help_id="op.animassist.p9_channel_resolver",
            )


# ---------------------------------------------------------------------------
# View 3D lightweight panel (pose mirror tools)
# ---------------------------------------------------------------------------

class ANIMASSIST_PT_p9_mirror_v3d(PanelAnatomyMixin, View3DSidebarPanel):
    """Pose mirroring tools for the 3D viewport."""

    bl_category = "Pose"
    bl_order = 50
    bl_idname = "ANIMASSIST_PT_p9_mirror_v3d"
    bl_label = "Mirror & Symmetry"

    def draw_primary(self, context: bpy.types.Context) -> None:
        layout = self.layout

        if not _in_pose_mode(context):
            layout.label(text="Enter Pose Mode to use mirror tools", icon="INFO")
            return

        uh.section_header(layout, "Quick Mirror", icon="MOD_MIRROR")
        uh.explained_op(
            layout, context,
            "animassist.p9_mirror_pose",
            text="Mirror Pose", icon="MOD_MIRROR",
            help_id="op.animassist.p9_mirror_pose",
        )
        uh.explained_op(
            layout, context,
            "animassist.p9_mirror_selected",
            text="Mirror Selected", icon="EDITMODE_HLT",
            help_id="op.animassist.p9_mirror_selected",
        )
        uh.explained_op(
            layout, context,
            "animassist.p9_swap_poses",
            text="Swap Poses", icon="LOOP_BACK",
            help_id="op.animassist.p9_swap_poses",
        )

        uh.separator(layout)

        uh.section_header(layout, "Selection", icon="RESTRICT_SELECT_OFF")
        uh.explained_op(
            layout, context,
            "animassist.p9_select_opposite",
            text="Select Opposite", icon="RESTRICT_SELECT_OFF",
            help_id="op.animassist.p9_select_opposite",
        )
        uh.explained_op(
            layout, context,
            "animassist.p9_add_opposite",
            text="Add Opposite", icon="ADD",
            help_id="op.animassist.p9_add_opposite",
        )


# ---------------------------------------------------------------------------
# Cross-editor variants — Graph Editor
# ---------------------------------------------------------------------------

_DS_CLASSES: tuple[type, ...] = (
    ANIMASSIST_PT_p9_mirror,
)

_GE_VARIANTS = make_editor_variants(
    ANIMASSIST_PT_p9_mirror,
    ["GRAPH_EDITOR"],
)

CLASSES: tuple[type, ...] = (
    *_DS_CLASSES,
    ANIMASSIST_PT_p9_mirror_v3d,
    *(_GE_VARIANTS or ()),
)

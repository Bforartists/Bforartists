# --- ORCHESTRATION AND RECOVERY PANELS ---
"""Sidebar panels for tool shelf, macro orchestration, system management and recovery.

Panel placement:
    Dope Sheet — primary home (orchestration, batch processing, recovery)
    Graph Editor — lightweight variants via make_editor_variants()
    View 3D — lightweight shelf variant for quick access

Uses PanelAnatomyMixin section hooks:
    draw_primary   — quick shelf, macro presets, recovery snapshots
    draw_scope     — shelf filters, batch mode settings, workspace profiles
    draw_advanced  — pie menus, custom macros, audit trail, diagnostics, setup
"""

from __future__ import annotations

import bpy

from ..core.p10_properties import get_p10, recents_newest_first
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

def _p10_available(context: bpy.types.Context) -> bool:
    return get_p10(context) is not None


# ---------------------------------------------------------------------------
# Quick Shelf Panel — Dope Sheet
# ---------------------------------------------------------------------------

class ANIMASSIST_PT_p10_shelf(PanelAnatomyMixin, DopeSheetSidebarPanel):
    """Quick shelf for rapid tool access, favorites, and recent tools."""

    bl_category = "Workspace"
    bl_order = 20
    bl_idname = "ANIMASSIST_PT_p10_shelf"
    bl_label = "Quick Shelf"

    # ── Primary: shelf display and favorites ────────────────────────────

    def draw_primary(self, context: bpy.types.Context) -> None:
        layout = self.layout
        p10 = get_p10(context)
        if p10 is None:
            layout.label(text="Orchestration tools not available", icon="INFO")
            return

        if not p10.first_run_complete:
            start = layout.box()
            start.label(text="New here? Start with sensible defaults.", icon="INFO")
            start.operator(
                "animassist.p10_first_run_setup",
                text="First Run Setup",
                icon="SETTINGS",
            )

        # ── Shelf header and controls ──
        uh.section_header(layout, "Quick Shelf", icon="ASSET_MANAGER")

        row = layout.row(align=True)
        row.prop(p10, "shelf_mode", text="", icon_only=True)
        uh.explained_op(
            row, context,
            "animassist.p10_search_tools",
            text="Search", icon="VIEWZOOM",
            help_id="op.animassist.p10_search_tools",
        )

        # ── Favorites or Recents ──
        if p10.shelf_mode == "FAVORITES":
            # Show favorites list
            if p10.favorites:
                for i, fav in enumerate(p10.favorites):
                    row = layout.row(align=True)
                    row.label(text=fav.label, icon=fav.icon)
                    row.operator(
                        "animassist.p10_remove_favorite",
                        text="", icon="X"
                    ).index = i
            else:
                layout.label(text="No favorites yet", icon="BLANK1")
        else:
            # Show recent tools (up to 5 most recent)
            ordered_recents = recents_newest_first(p10)
            recent_count = min(5, len(ordered_recents))
            if recent_count > 0:
                for i in range(recent_count):
                    recent = ordered_recents[i]
                    row = layout.row(align=True)
                    uh.explained_op(
                        row, context,
                        recent.op_id,
                        text=recent.label, icon="NONE",
                        help_id=f"op.{recent.op_id}",
                    )
            else:
                layout.label(text="No recent tools yet", icon="BLANK1")

        uh.separator(layout)

        # ── Quick action row ──
        row = layout.row(align=True)
        uh.explained_op(
            row, context,
            "animassist.p10_repeat_last",
            text="Repeat Last", icon="FILE_REFRESH",
            help_id="op.animassist.p10_repeat_last",
        )
        uh.explained_op(
            row, context,
            "animassist.p10_clear_recents",
            text="Clear", icon="TRASH",
            help_id="op.animassist.p10_clear_recents",
        )

    # ── Scope: shelf filtering ───────────────────────────────────────────

    def draw_scope(self, context: bpy.types.Context) -> None:
        layout = self.layout
        p10 = get_p10(context)
        if p10 is None:
            return

        uh.section_header(layout, "Shelf Filter", icon="FILTER")

        uh.explained_prop(
            layout, context, p10, "shelf_filter_phase", text="Tool Group",
            help_id="p10_shelf_filter_phase",
        )

        uh.explained_prop(
            layout, context, p10, "shelf_search_query", text="Search",
            help_id="p10_shelf_search_query",
        )

    # ── Advanced: pie menus and quick actions ────────────────────────────

    def draw_advanced(self, context: bpy.types.Context) -> None:
        layout = self.layout
        p10 = get_p10(context)
        if p10 is None:
            return

        # ── Pie Menus ──
        body, expanded = uh.subsection(
            layout, context,
            "p10_shelf", "pie_menus",
            "Pie Menus",
            icon="MESH_CIRCLE",
            default_open=False,
        )
        if expanded:
            # Row 1: Key Tools, Breakdown, Transform
            row = body.row(align=True)
            uh.explained_op(
                row, context,
                "animassist.p10_pie_key_tools",
                text="Key Tools", icon="KEY_HLT",
                help_id="op.animassist.p10_pie_key_tools",
            )
            uh.explained_op(
                row, context,
                "animassist.p10_pie_breakdown",
                text="Breakdown", icon="KEYFRAME",
                help_id="op.animassist.p10_pie_breakdown",
            )
            uh.explained_op(
                row, context,
                "animassist.p10_pie_transform",
                text="Transform", icon="CON_ROTLIKE",
                help_id="op.animassist.p10_pie_transform",
            )

            # Row 2: Proxy, Switch, Symmetry
            row = body.row(align=True)
            uh.explained_op(
                row, context,
                "animassist.p10_pie_proxy",
                text="Proxy", icon="OUTLINER_OB_ARMATURE",
                help_id="op.animassist.p10_pie_proxy",
            )
            uh.explained_op(
                row, context,
                "animassist.p10_pie_switch",
                text="Switch", icon="FILE_REFRESH",
                help_id="op.animassist.p10_pie_switch",
            )
            uh.explained_op(
                row, context,
                "animassist.p10_pie_symmetry",
                text="Symmetry", icon="MOD_MIRROR",
                help_id="op.animassist.p10_pie_symmetry",
            )

        # ── Quick Actions ──
        body, expanded = uh.subsection(
            layout, context,
            "p10_shelf", "quick_actions",
            "Quick Actions",
            icon="PLAY",
            default_open=False,
        )
        if expanded:
            uh.explained_op(
                body, context,
                "animassist.p10_repeat_last",
                text="Repeat Last", icon="FILE_REFRESH",
                help_id="op.animassist.p10_repeat_last",
            )
            uh.explained_op(
                body, context,
                "animassist.p10_record_recent",
                text="Record Recent", icon="REC",
                help_id="op.animassist.p10_record_recent",
            )


# ---------------------------------------------------------------------------
# Macros & Batch Panel — Dope Sheet
# ---------------------------------------------------------------------------

class ANIMASSIST_PT_p10_macros(PanelAnatomyMixin, DopeSheetSidebarPanel):
    """Macro presets and batch processing controls for automation."""

    bl_category = "Workspace"
    bl_order = 10
    bl_idname = "ANIMASSIST_PT_p10_macros"
    bl_label = "Macros & Batch"

    # ── Primary: preset macros and custom macros ────────────────────────

    def draw_primary(self, context: bpy.types.Context) -> None:
        layout = self.layout
        p10 = get_p10(context)
        if p10 is None:
            layout.label(text="Orchestration tools not available", icon="INFO")
            return

        # ── Preset Macros ──
        uh.section_header(layout, "Preset Macros", icon="SEQUENCE")

        # 5 preset macro buttons
        row = layout.row(align=True)
        uh.explained_op(
            row, context,
            "animassist.p10_macro_breakdown_offset",
            text="Breakdown+Offset", icon="KEY_HLT",
            help_id="op.animassist.p10_macro_breakdown_offset",
        )
        row = layout.row(align=True)
        uh.explained_op(
            row, context,
            "animassist.p10_macro_proxy_workflow",
            text="Proxy Workflow", icon="OUTLINER_OB_ARMATURE",
            help_id="op.animassist.p10_macro_proxy_workflow",
        )
        row = layout.row(align=True)
        uh.explained_op(
            row, context,
            "animassist.p10_macro_switch_compensate",
            text="Switch+Compensate", icon="FILE_REFRESH",
            help_id="op.animassist.p10_macro_switch_compensate",
        )
        row = layout.row(align=True)
        uh.explained_op(
            row, context,
            "animassist.p10_macro_diagnose_jump",
            text="Diagnose+Jump", icon="INFO",
            help_id="op.animassist.p10_macro_diagnose_jump",
        )
        row = layout.row(align=True)
        uh.explained_op(
            row, context,
            "animassist.p10_macro_mirror_match",
            text="Mirror+Match", icon="MOD_MIRROR",
            help_id="op.animassist.p10_macro_mirror_match",
        )

        uh.separator(layout)

        # ── Custom Macros ──
        uh.section_header(layout, "Custom Macros", icon="FILE_SCRIPT")

        if p10.macros:
            for i, macro in enumerate(p10.macros):
                row = layout.row(align=True)
                row.label(text=macro.name, icon=macro.icon)
                uh.explained_op(
                    row, context,
                    "animassist.p10_run_custom_macro",
                    text="Run", icon="PLAY",
                    help_id="op.animassist.p10_run_custom_macro",
                ).index = i
                row.operator(
                    "animassist.p10_remove_macro",
                    text="", icon="X"
                ).index = i
        else:
            layout.label(text="No custom macros yet", icon="BLANK1")

        uh.separator(layout)

        uh.explained_op(
            layout, context,
            "animassist.p10_add_macro",
            text="Add Macro", icon="ADD",
            help_id="op.animassist.p10_add_macro",
        )

    # ── Scope: batch mode settings ───────────────────────────────────────

    def draw_scope(self, context: bpy.types.Context) -> None:
        layout = self.layout
        p10 = get_p10(context)
        if p10 is None:
            return

        uh.section_header(layout, "Batch Mode", icon="GROUP")

        uh.explained_prop(
            layout, context, p10, "batch_mode",
            help_id="p10_batch_mode",
        )

        # Show frame range controls if FRAME_STEPS mode
        if p10.batch_mode == "FRAME_STEPS":
            row = layout.row(align=True)
            row.prop(p10, "batch_frame_start", text="Start")
            row.prop(p10, "batch_frame_end", text="End")

            row = layout.row(align=True)
            row.prop(p10, "batch_frame_step", text="Step")

        uh.separator(layout)

        # Batch action buttons
        row = layout.row(align=True)
        uh.explained_op(
            row, context,
            "animassist.p10_batch_selected",
            text="Selected", icon="EDITMODE_HLT",
            help_id="op.animassist.p10_batch_selected",
        )
        uh.explained_op(
            row, context,
            "animassist.p10_batch_bookmarked",
            text="Bookmarked", icon="PINNED",
            help_id="op.animassist.p10_batch_bookmarked",
        )

        row = layout.row(align=True)
        uh.explained_op(
            row, context,
            "animassist.p10_batch_frame_steps",
            text="Frame Steps", icon="FRAME_PREV",
            help_id="op.animassist.p10_batch_frame_steps",
        )


# ---------------------------------------------------------------------------
# System & Recovery Panel — Dope Sheet
# ---------------------------------------------------------------------------

class ANIMASSIST_PT_p10_system(PanelAnatomyMixin, DopeSheetSidebarPanel):
    """System recovery, workspace profiles, audit trail, and diagnostics."""

    bl_category = "Workspace"
    bl_order = 30
    bl_idname = "ANIMASSIST_PT_p10_system"
    bl_label = "System & Recovery"

    # ── Primary: recovery snapshots ──────────────────────────────────────

    def draw_primary(self, context: bpy.types.Context) -> None:
        layout = self.layout
        p10 = get_p10(context)
        if p10 is None:
            layout.label(text="Orchestration tools not available", icon="INFO")
            return

        # ── Recovery ──
        uh.section_header(layout, "Recovery", icon="FILE_BACKUP")

        row = layout.row(align=True)
        uh.explained_op(
            row, context,
            "animassist.p10_take_snapshot",
            text="Take Snapshot", icon="FILE_BACKUP",
            help_id="op.animassist.p10_take_snapshot",
        )
        uh.explained_op(
            row, context,
            "animassist.p10_restore_snapshot",
            text="Restore", icon="LOOP_BACK",
            help_id="op.animassist.p10_restore_snapshot",
        )
        uh.explained_op(
            row, context,
            "animassist.p10_list_snapshots",
            text="List", icon="TEXT",
            help_id="op.animassist.p10_list_snapshots",
        )

        uh.separator(layout)

        row = layout.row(align=True)
        row.prop(p10, "recovery_enabled", text="Enabled", toggle=True)

        uh.explained_prop(
            layout, context, p10, "max_snapshots",
            help_id="p10_max_snapshots",
        )

    # ── Scope: workspace profiles ────────────────────────────────────────

    def draw_scope(self, context: bpy.types.Context) -> None:
        layout = self.layout
        p10 = get_p10(context)
        if p10 is None:
            return

        uh.section_header(layout, "Workspace", icon="WORKSPACE")

        row = layout.row(align=True)
        uh.explained_op(
            row, context,
            "animassist.p10_export_workspace",
            text="Export", icon="EXPORT",
            help_id="op.animassist.p10_export_workspace",
        )
        uh.explained_op(
            row, context,
            "animassist.p10_import_workspace",
            text="Import", icon="IMPORT",
            help_id="op.animassist.p10_import_workspace",
        )

        uh.separator(layout)

        # Profile list
        if p10.profiles:
            for i, profile in enumerate(p10.profiles):
                row = layout.row(align=True)
                row.label(text=profile.name, icon="WORKSPACE")
                uh.explained_op(
                    row, context,
                    "animassist.p10_load_profile",
                    text="Load", icon="CHECKMARK",
                    help_id="op.animassist.p10_load_profile",
                ).index = i
                row.operator(
                    "animassist.p10_remove_profile",
                    text="", icon="X"
                ).index = i
        else:
            layout.label(text="No profiles saved", icon="BLANK1")

        uh.separator(layout)

        uh.explained_op(
            layout, context,
            "animassist.p10_save_profile",
            text="Save Profile", icon="ADD",
            help_id="op.animassist.p10_save_profile",
        )

    # ── Advanced: audit trail, diagnostics, setup ────────────────────────

    def draw_advanced(self, context: bpy.types.Context) -> None:
        layout = self.layout
        p10 = get_p10(context)
        if p10 is None:
            return

        # ── Audit Trail ──
        body, expanded = uh.subsection(
            layout, context,
            "p10_system", "audit_trail",
            "Audit Trail",
            icon="TEXT",
            default_open=False,
        )
        if expanded:
            row = body.row(align=True)
            uh.explained_op(
                row, context,
                "animassist.p10_show_history",
                text="History", icon="TIME",
                help_id="op.animassist.p10_show_history",
            )
            uh.explained_op(
                row, context,
                "animassist.p10_show_errors",
                text="Errors", icon="ERROR",
                help_id="op.animassist.p10_show_errors",
            )
            uh.explained_op(
                row, context,
                "animassist.p10_show_stats",
                text="Stats", icon="GRAPH",
                help_id="op.animassist.p10_show_stats",
            )

            uh.separator(body)

            row = body.row(align=True)
            uh.explained_op(
                row, context,
                "animassist.p10_clear_history",
                text="Clear History", icon="TRASH",
                help_id="op.animassist.p10_clear_history",
            )
            uh.explained_op(
                row, context,
                "animassist.p10_clear_errors",
                text="Clear Errors", icon="TRASH",
                help_id="op.animassist.p10_clear_errors",
            )

            uh.separator(body)

            row = body.row(align=True)
            row.prop(p10, "audit_enabled", text="Enabled", toggle=True)

            uh.explained_prop(
                body, context, p10, "max_audit_entries",
                help_id="p10_max_audit_entries",
            )

        # ── Diagnostics ──
        body, expanded = uh.subsection(
            layout, context,
            "p10_system", "diagnostics",
            "Diagnostics",
            icon="INFO",
            default_open=False,
        )
        if expanded:
            row = body.row(align=True)
            uh.explained_op(
                row, context,
                "animassist.p10_system_diagnostics",
                text="System Diagnostics", icon="SCRIPT",
                help_id="op.animassist.p10_system_diagnostics",
            )
            uh.explained_op(
                row, context,
                "animassist.p10_leak_check",
                text="Leak Check", icon="MEMORY",
                help_id="op.animassist.p10_leak_check",
            )
            uh.explained_op(
                row, context,
                "animassist.p10_stale_cleanup",
                text="Stale Cleanup", icon="TRASH",
                help_id="op.animassist.p10_stale_cleanup",
            )

            uh.separator(body)

            row = body.row(align=True)
            uh.explained_op(
                row, context,
                "animassist.p10_metadata_cleanup",
                text="Metadata", icon="OUTLINER",
                help_id="op.animassist.p10_metadata_cleanup",
            )
            uh.explained_op(
                row, context,
                "animassist.p10_rebuild_caches",
                text="Rebuild Caches", icon="FILE_REFRESH",
                help_id="op.animassist.p10_rebuild_caches",
            )
            uh.explained_op(
                row, context,
                "animassist.p10_reset_ui",
                text="Reset UI", icon="LOOP_BACK",
                help_id="op.animassist.p10_reset_ui",
            )

            uh.separator(body)

            uh.explained_op(
                body, context,
                "animassist.p10_validate_registration",
                text="Validate Registration", icon="CHECKMARK",
                help_id="op.animassist.p10_validate_registration",
            )

        # ── Setup ──
        body, expanded = uh.subsection(
            layout, context,
            "p10_system", "setup",
            "Setup",
            icon="PREFERENCES",
            default_open=False,
        )
        if expanded:
            row = body.row(align=True)
            uh.explained_op(
                row, context,
                "animassist.p10_safe_disable",
                text="Safe Disable", icon="CANCEL",
                help_id="op.animassist.p10_safe_disable",
            )
            uh.explained_op(
                row, context,
                "animassist.p10_check_hotkey_conflicts",
                text="Check Hotkeys", icon="OPTIONS",
                help_id="op.animassist.p10_check_hotkey_conflicts",
            )

            uh.separator(body)

            row = body.row(align=True)
            uh.explained_op(
                row, context,
                "animassist.p10_first_run_setup",
                text="First Run Setup", icon="SETTINGS",
                help_id="op.animassist.p10_first_run_setup",
            )
            uh.explained_op(
                row, context,
                "animassist.p10_load_demo_config",
                text="Load Demo", icon="OUTLINER_COLLECTION",
                help_id="op.animassist.p10_load_demo_config",
            )

            uh.separator(body)

            row = body.row(align=True)
            row.prop(p10, "show_debug_panel", text="Debug", toggle=True)

            uh.explained_op(
                body, context,
                "animassist.p10_final_validation",
                text="Final Validation", icon="CHECKMARK",
                help_id="op.animassist.p10_final_validation",
            )


# ---------------------------------------------------------------------------
# Quick Shelf Panel — View 3D (lightweight variant)
# ---------------------------------------------------------------------------

class ANIMASSIST_PT_p10_shelf_v3d(PanelAnatomyMixin, View3DSidebarPanel):
    """Quick shelf for 3D viewport with recent tools and pie menus."""

    bl_category = "Workspace"
    bl_order = 20
    bl_idname = "ANIMASSIST_PT_p10_shelf_v3d"
    bl_label = "Quick Shelf"

    def draw_primary(self, context: bpy.types.Context) -> None:
        layout = self.layout
        p10 = get_p10(context)
        if p10 is None:
            layout.label(text="Orchestration tools not available", icon="INFO")
            return

        uh.section_header(layout, "Quick Shelf", icon="ASSET_MANAGER")

        # Show recent tools (up to 5 most recent)
        ordered_recents = recents_newest_first(p10)
        recent_count = min(5, len(ordered_recents))
        if recent_count > 0:
            for i in range(recent_count):
                recent = ordered_recents[i]
                uh.explained_op(
                    layout, context,
                    recent.op_id,
                    text=recent.label, icon="NONE",
                    help_id=f"op.{recent.op_id}",
                )
        else:
            layout.label(text="No recent tools yet", icon="BLANK1")

        uh.separator(layout)

        # Pie menu buttons
        uh.section_header(layout, "Pie Menus", icon="MESH_CIRCLE")

        row = layout.row(align=True)
        uh.explained_op(
            row, context,
            "animassist.p10_pie_key_tools",
            text="Key Tools", icon="KEY_HLT",
            help_id="op.animassist.p10_pie_key_tools",
        )
        uh.explained_op(
            row, context,
            "animassist.p10_pie_breakdown",
            text="Breakdown", icon="KEYFRAME",
            help_id="op.animassist.p10_pie_breakdown",
        )

        row = layout.row(align=True)
        uh.explained_op(
            row, context,
            "animassist.p10_pie_transform",
            text="Transform", icon="CON_ROTLIKE",
            help_id="op.animassist.p10_pie_transform",
        )
        uh.explained_op(
            row, context,
            "animassist.p10_pie_proxy",
            text="Proxy", icon="OUTLINER_OB_ARMATURE",
            help_id="op.animassist.p10_pie_proxy",
        )

        row = layout.row(align=True)
        uh.explained_op(
            row, context,
            "animassist.p10_pie_switch",
            text="Switch", icon="FILE_REFRESH",
            help_id="op.animassist.p10_pie_switch",
        )
        uh.explained_op(
            row, context,
            "animassist.p10_pie_symmetry",
            text="Symmetry", icon="MOD_MIRROR",
            help_id="op.animassist.p10_pie_symmetry",
        )


# ---------------------------------------------------------------------------
# Cross-editor variants — Graph Editor
# ---------------------------------------------------------------------------

_DS_CLASSES: tuple[type, ...] = (
    ANIMASSIST_PT_p10_shelf,
    ANIMASSIST_PT_p10_macros,
    ANIMASSIST_PT_p10_system,
)

_GE_VARIANTS = make_editor_variants(
    ANIMASSIST_PT_p10_shelf,
    ["GRAPH_EDITOR"],
)

CLASSES: tuple[type, ...] = (
    *_DS_CLASSES,
    ANIMASSIST_PT_p10_shelf_v3d,
    *(_GE_VARIANTS or ()),
)

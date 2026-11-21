# --- ANIMATION LAYER PANELS ---
"""Sidebar panels for animation layer stack management and blending.

Panel placement:
    Dope Sheet — primary home (layer stack, assignments, blending)
    Graph Editor — lightweight variant via make_editor_variants()
    View 3D — secondary for pose-oriented layer tools

Uses a Blender UIList for the layer stack (Maya/After Effects-style
scrollable list with inline solo/mute/lock toggles and weight sliders).

Uses PanelAnatomyMixin section hooks:
    draw_primary   — UIList layer stack, add/remove, active layer info
    draw_scope     — assignment, scope, blend mode, editing mode
    draw_advanced  — channel overrides, presets, blend-between, merge
"""

from __future__ import annotations

import bpy

from ..core.p11_properties import get_p11
from ..ui import ui_helpers as uh
from ..ui.panel_anatomy import PanelAnatomyMixin
from ..ui.editor_placement import (
    DopeSheetSidebarPanel,
    View3DSidebarPanel,
)


# ---------------------------------------------------------------------------
# Availability helpers
# ---------------------------------------------------------------------------

def _p11_available(context: bpy.types.Context) -> bool:
    return get_p11(context) is not None


def _has_active_armature(context: bpy.types.Context) -> bool:
    obj = context.active_object
    return obj is not None and obj.type == "ARMATURE"


def _in_pose_mode(context: bpy.types.Context) -> bool:
    return context.mode == "POSE" and _has_active_armature(context)


# ---------------------------------------------------------------------------
# Layer icon helper
# ---------------------------------------------------------------------------

def _layer_icon(layer) -> str:
    """Return an appropriate icon for a layer's state."""
    if layer.is_base_layer:
        return "OBJECT_DATA"
    if layer.locked:
        return "LOCKED"
    if layer.mute:
        return "HIDE_ON"
    if layer.solo:
        return "SOLO_ON"
    return "ACTION"


# ---------------------------------------------------------------------------
# UIList — The core layer stack widget (Maya/AE-style)
# ---------------------------------------------------------------------------

class ANIMASSIST_UL_p11_layer_stack(bpy.types.UIList):
    """UIList that draws each animation layer as a row.

    Each row shows:
        [Icon] [Layer Name]  [Weight slider]  [Solo] [Mute] [Lock] [AutoKey]

    Toggle meanings:
        Solo     — isolate this layer for preview (mutes all others).
        Mute     — temporarily disable this layer's contribution.
        Lock     — prevent edits (keyframing, weight changes) on this layer.
        Auto-Key — auto-insert keyframes on this layer when posing.

    The active (selected) layer is highlighted automatically by Blender.
    """

    bl_idname = "ANIMASSIST_UL_p11_layer_stack"

    def draw_item(
        self, context, layout, data, item, icon, active_data, active_property,
        index=0, flt_flag=0,
    ):
        layer = item

        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            row = layout.row(align=True)

            # Layer icon and name (editable inline).
            row.prop(layer, "name", text="", icon=_layer_icon(layer), emboss=False)

            # Weight slider — compact, narrower to leave room for toggles.
            weight_sub = row.row(align=True)
            weight_sub.scale_x = 0.38
            weight_sub.prop(layer, "weight", text="", slider=True)

            # State toggles — Solo, Mute, Lock, Auto-Key.
            # Sized large enough to be clickable (0.85 of remaining width
            # shared across 4 icons ≈ 0.21 each, vs. prior 0.14).
            toggle_sub = row.row(align=True)
            toggle_sub.scale_x = 0.85

            toggle_sub.prop(
                layer, "solo", text="",
                icon="SOLO_ON" if layer.solo else "SOLO_OFF",
                toggle=True,
            )
            toggle_sub.prop(
                layer, "mute", text="",
                icon="HIDE_ON" if layer.mute else "HIDE_OFF",
                toggle=True,
            )
            toggle_sub.prop(
                layer, "locked", text="",
                icon="LOCKED" if layer.locked else "UNLOCKED",
                toggle=True,
            )
            toggle_sub.prop(
                layer, "auto_key", text="",
                icon="REC" if layer.auto_key else "RADIOBUT_OFF",
                toggle=True,
            )

        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text=layer.name, icon=_layer_icon(layer))

    def draw_filter(self, context, layout):
        # No filtering needed for animation layers.
        pass

    def filter_items(self, context, data, propname):
        layers = getattr(data, propname)
        # Show all layers, reverse order (top layer = last in list = top visually).
        # UIList shows items top-to-bottom, and we want the highest layer
        # (last in collection) at the TOP of the list — so we reverse the order.
        order = list(range(len(layers) - 1, -1, -1))
        flags = [self.bitflag_filter_item] * len(layers)
        return flags, order


# ---------------------------------------------------------------------------
# Main panel — Dope Sheet
# ---------------------------------------------------------------------------

class ANIMASSIST_PT_p11_layers(PanelAnatomyMixin, DopeSheetSidebarPanel):
    """Animation layer stack and management with blending controls."""

    bl_category = "Layers"
    bl_order = 10
    bl_idname = "ANIMASSIST_PT_p11_layers"
    bl_label = "Animation Layers"

    # ── Primary: UIList layer stack, add/remove, active layer info ────

    def draw_primary(self, context: bpy.types.Context) -> None:
        layout = self.layout

        # Wrap everything in try/except so any error shows as readable text
        # instead of leaving the panel blank.
        try:
            self._draw_primary_inner(context, layout)
        except Exception as exc:  # noqa: BLE001
            layout.label(text=f"Layer panel error: {exc}", icon="ERROR")

    def _draw_primary_inner(
        self, context: bpy.types.Context, layout
    ) -> None:
        p11 = get_p11(context)
        if p11 is None:
            layout.label(text="Layer system unavailable.", icon="ERROR")
            layout.label(text="Save & re-open the file, or reload the addon.")
            return

        # ── Master toggle ──
        row = layout.row(align=True)
        row.prop(p11, "layers_enabled", text="Enable Layers")
        uh.draw_explainer_icon(row, context, "p11.layers_enabled")

        if not p11.layers_enabled:
            layout.label(text="Turn on to animate in layers", icon="INFO")
            return

        uh.separator(layout)

        # ── Layer stack — UIList ──
        if len(p11.layers) == 0:
            layout.label(text="Next: add a base layer", icon="INFO")
            layout.label(text="from the current animation.")
            # Use plain operator() so a missing operator shows disabled
            # rather than crashing the entire draw.
            col = layout.column()
            col.operator(
                "animassist.p11_init_layers",
                text="Create Base Layer",
                icon="FILE_NEW",
            )
            return

        # The UIList widget with +/- buttons on the right side.
        row = layout.row()
        row.template_list(
            "ANIMASSIST_UL_p11_layer_stack",  # UIList class name
            "",                                # list_id (unique within panel)
            p11,                               # data pointer (has the collection)
            "layers",                          # collection property name
            p11,                               # active data pointer
            "active_layer_index",              # active index property name
            rows=4,                            # min visible rows
            maxrows=8,                         # max visible rows before scroll
        )

        # Side buttons column (add/remove/move).
        col = row.column(align=True)
        col.operator("animassist.p11_add_layer", text="", icon="ADD")
        col.operator("animassist.p11_remove_layer", text="", icon="REMOVE")
        col.separator()
        col.operator("animassist.p11_move_layer_up", text="", icon="TRIA_UP")
        col.operator("animassist.p11_move_layer_down", text="", icon="TRIA_DOWN")
        col.separator()
        col.operator("animassist.p11_duplicate_layer", text="", icon="DUPLICATE")

        uh.separator(layout)

        # ── Active layer details ──
        if 0 <= p11.active_layer_index < len(p11.layers):
            active = p11.layers[p11.active_layer_index]
            info_box = layout.box()

            # Header row: name + rename button.
            header = info_box.row(align=True)
            header.label(text=f"Active: {active.name}", icon=_layer_icon(active))
            header.operator("animassist.p11_rename_layer", text="", icon="GREASEPENCIL")

            # Blend mode.
            row = info_box.row(align=True)
            row.prop(active, "blend_mode", text="")
            uh.draw_explainer_icon(row, context, "p11.blend_mode")

            # Weight slider (larger, more visible).
            row = info_box.row(align=True)
            row.prop(active, "weight", text="Weight", slider=True)
            uh.draw_explainer_icon(row, context, "p11.weight")

            # Color + auto-key.
            row = info_box.row(align=True)
            row.prop(active, "layer_color", text="Color")
            row.prop(active, "auto_key", text="Auto Key", icon="REC", toggle=True)

    # ── Scope: assignments, scope filter, editing mode ───────────────

    def draw_scope(self, context: bpy.types.Context) -> None:
        layout = self.layout
        try:
            p11 = get_p11(context)
            if p11 is None or not p11.layers_enabled:
                return
        except Exception as exc:  # noqa: BLE001
            layout.label(text=f"Scope error: {exc}", icon="ERROR")
            return

        # ── Editing mode ──
        uh.section_header(layout, "Editing Mode", icon="TOOL_SETTINGS")

        row = layout.row(align=True)
        row.prop(p11, "edit_active_only", text="Edit Active Only")
        uh.draw_explainer_icon(row, context, "p11.edit_active_only")

        row = layout.row(align=True)
        row.prop(p11, "auto_assign_on_key", text="Auto-Assign on Key")
        uh.draw_explainer_icon(row, context, "p11.auto_assign_on_key")

        row = layout.row(align=True)
        row.prop(p11, "show_layer_colors", text="Show Colors")
        row.prop(p11, "show_unassigned_warning", text="Warn Unassigned")

        uh.separator(layout)

        # ── Part assignment ──
        if 0 <= p11.active_layer_index < len(p11.layers):
            active = p11.layers[p11.active_layer_index]

            uh.section_header(layout, "Assigned Parts", icon="BONE_DATA")

            if len(active.assigned_bones) == 0:
                layout.label(
                    text="No assignments (all bones)",
                    icon="INFO",
                )
            else:
                bone_box = layout.box()
                for i, ba in enumerate(active.assigned_bones):
                    row = bone_box.row(align=True)
                    row.label(text=ba.bone_name, icon="BONE_DATA")
                    op = row.operator(
                        "animassist.p11_remove_bone",
                        text="", icon="X",
                    )
                    op.index = i

            uh.separator(layout)

            row = layout.row(align=True)
            uh.explained_op(
                row, context,
                "animassist.p11_assign_selected",
                text="Assign Selected", icon="ADD",
                help_id="p11.assigned_bones",
            )
            uh.explained_op(
                row, context,
                "animassist.p11_remove_selected",
                text="Remove Selected", icon="REMOVE",
                help_id="p11.assigned_bones",
            )

            row = layout.row(align=True)
            row.operator(
                "animassist.p11_assign_by_pattern",
                text="By Pattern", icon="FILTER",
            )
            row.operator(
                "animassist.p11_clear_assignments",
                text="Clear All", icon="X",
            )
            row.operator(
                "animassist.p11_select_assigned",
                text="Select", icon="RESTRICT_SELECT_OFF",
            )

            uh.separator(layout)

            # ── Layer scope ──
            uh.section_header(layout, "Layer Scope", icon="FILTER")
            uh.explained_prop(
                layout, context, active, "layer_scope",
                help_id="p11.layer_scope",
            )
            if active.layer_scope == "CUSTOM":
                layout.prop(active, "custom_filter", text="Filter")

    # ── Advanced: channel overrides, presets, blending, merge ────────

    def draw_advanced(self, context: bpy.types.Context) -> None:
        layout = self.layout
        try:
            p11 = get_p11(context)
            if p11 is None or not p11.layers_enabled:
                return
        except Exception as exc:  # noqa: BLE001
            layout.label(text=f"Advanced error: {exc}", icon="ERROR")
            return

        # ── Auto-Partition ──
        body, expanded = uh.subsection(
            layout, context,
            "p11_layers", "auto_partition",
            "Auto-Partition",
            icon="MESH_GRID",
            default_open=False,
        )
        if expanded:
            uh.explained_op(
                body, context,
                "animassist.p11_auto_partition",
                text="Apply Preset", icon="PRESET",
                help_id="p11.preset_upper_lower",
            )

        # ── Channel Overrides ──
        if 0 <= p11.active_layer_index < len(p11.layers):
            active = p11.layers[p11.active_layer_index]

            body, expanded = uh.subsection(
                layout, context,
                "p11_layers", "channel_overrides",
                "Channel Overrides",
                icon="MODIFIER",
                default_open=False,
            )
            if expanded:
                if active.channel_overrides:
                    for i, ovr in enumerate(active.channel_overrides):
                        ovr_box = body.box()
                        row = ovr_box.row(align=True)
                        row.label(text=ovr.bone_name, icon="BONE_DATA")
                        op = row.operator(
                            "animassist.p11_remove_channel_override",
                            text="", icon="X",
                        )
                        op.index = i
                        row = ovr_box.row(align=True)
                        row.prop(ovr, "location_weight", text="Loc")
                        row.prop(ovr, "rotation_weight", text="Rot")
                        row.prop(ovr, "scale_weight", text="Sca")
                else:
                    body.label(text="No channel overrides", icon="INFO")

                uh.separator(body)
                body.operator(
                    "animassist.p11_add_channel_override",
                    text="Add Override", icon="ADD",
                )

        # ── Blend Between Layers ──
        body, expanded = uh.subsection(
            layout, context,
            "p11_layers", "blend_between",
            "Blend Between Layers",
            icon="MOD_HUE_SATURATION",
            default_open=False,
        )
        if expanded:
            body.prop(p11, "blend_source_index", text="Source")
            body.prop(p11, "blend_target_index", text="Target")
            body.prop(p11, "blend_factor", text="Factor", slider=True)

            row = body.row(align=True)
            uh.explained_op(
                row, context,
                "animassist.p11_blend_layers",
                text="Interactive Blend", icon="DRIVER",
                help_id="op.animassist.p11_blend_layers",
            )
            uh.explained_op(
                row, context,
                "animassist.p11_set_blend_factor",
                text="Apply", icon="CHECKMARK",
                help_id="op.animassist.p11_blend_layers",
            )

        # ── Merge / Flatten ──
        body, expanded = uh.subsection(
            layout, context,
            "p11_layers", "merge_flatten",
            "Merge & Flatten",
            icon="FULLSCREEN_EXIT",
            default_open=False,
        )
        if expanded:
            uh.explained_op(
                body, context,
                "animassist.p11_merge_down",
                text="Merge Down", icon="TRIA_DOWN_BAR",
                help_id="op.animassist.p11_merge_down",
            )
            uh.explained_op(
                body, context,
                "animassist.p11_flatten_all",
                text="Flatten All", icon="FULLSCREEN_EXIT",
                help_id="op.animassist.p11_flatten_all",
            )

        # ── Evaluate ──
        body, expanded = uh.subsection(
            layout, context,
            "p11_layers", "evaluate",
            "Evaluate",
            icon="PLAY",
            default_open=False,
        )
        if expanded:
            body.operator(
                "animassist.p11_evaluate_stack",
                text="Evaluate Stack", icon="PLAY",
            )

        # ── Presets ──
        body, expanded = uh.subsection(
            layout, context,
            "p11_layers", "presets",
            "Layer Presets",
            icon="PRESET",
            default_open=False,
        )
        if expanded:
            if p11.user_presets:
                for i, preset in enumerate(p11.user_presets):
                    row = body.row(align=True)
                    is_active = (i == p11.user_presets_index)
                    row.label(
                        text=preset.name,
                        icon="RADIOBUT_ON" if is_active else "RADIOBUT_OFF",
                    )
                body.prop(p11, "user_presets_index", text="Active")
            else:
                body.label(text="No saved presets", icon="INFO")

            uh.separator(body)
            row = body.row(align=True)
            row.operator(
                "animassist.p11_save_preset",
                text="Save", icon="FILE_TICK",
            )
            row.operator(
                "animassist.p11_load_preset",
                text="Load", icon="FILE_FOLDER",
            )
            row.operator(
                "animassist.p11_remove_preset",
                text="", icon="X",
            )


# ---------------------------------------------------------------------------
# View 3D lightweight panel (pose-oriented layer tools)
# ---------------------------------------------------------------------------

class ANIMASSIST_PT_p11_layers_v3d(PanelAnatomyMixin, View3DSidebarPanel):
    """Animation layer management and assignment tools for the 3D viewport."""

    bl_category = "Layers"
    bl_order = 10
    bl_idname = "ANIMASSIST_PT_p11_layers_v3d"
    bl_label = "Animation Layers"

    def draw_primary(self, context: bpy.types.Context) -> None:
        layout = self.layout
        p11 = get_p11(context)
        if p11 is None:
            layout.label(text="Layer system unavailable", icon="ERROR")
            return

        row = layout.row(align=True)
        row.prop(p11, "layers_enabled", text="Enable Layers", icon="RENDERLAYERS")

        if not p11.layers_enabled:
            layout.label(text="Turn on to animate in layers", icon="INFO")
            return
        if len(p11.layers) == 0:
            layout.label(text="Next: add a base layer", icon="INFO")
            layout.label(text="from the current animation.")
            layout.operator(
                "animassist.p11_init_layers",
                text="Create Base Layer", icon="FILE_NEW",
            )
            return

        uh.separator(layout)

        # Same UIList in the 3D viewport.
        row = layout.row()
        row.template_list(
            "ANIMASSIST_UL_p11_layer_stack",
            "v3d",
            p11,
            "layers",
            p11,
            "active_layer_index",
            rows=3,
            maxrows=6,
        )

        col = row.column(align=True)
        col.operator("animassist.p11_add_layer", text="", icon="ADD")
        col.operator("animassist.p11_remove_layer", text="", icon="REMOVE")
        col.separator()
        col.operator("animassist.p11_move_layer_up", text="", icon="TRIA_UP")
        col.operator("animassist.p11_move_layer_down", text="", icon="TRIA_DOWN")

        uh.separator(layout)

        # Active layer quick info.
        if 0 <= p11.active_layer_index < len(p11.layers):
            active = p11.layers[p11.active_layer_index]
            row = layout.row(align=True)
            row.prop(active, "blend_mode", text="")
            row.prop(active, "auto_key", text="", icon="REC", toggle=True)

        uh.separator(layout)

        if not _in_pose_mode(context):
            layout.label(text="Enter Pose Mode for assignment tools", icon="INFO")
            return

        row = layout.row(align=True)
        row.operator(
            "animassist.p11_assign_selected",
            text="Assign", icon="ADD",
        )
        row.operator(
            "animassist.p11_remove_selected",
            text="Remove", icon="REMOVE",
        )
        row.operator(
            "animassist.p11_select_assigned",
            text="Select", icon="RESTRICT_SELECT_OFF",
        )


# ---------------------------------------------------------------------------
# Registered classes — Animation Layers lives in the 3D Viewport only.
# The DS/GE variants are defined above but intentionally not registered:
# the Dope Sheet context causes blank rendering and the V3D panel covers
# all layer management needs while the animator is posing.
# ---------------------------------------------------------------------------

CLASSES: tuple[type, ...] = (
    ANIMASSIST_UL_p11_layer_stack,
    ANIMASSIST_PT_p11_layers_v3d,
)

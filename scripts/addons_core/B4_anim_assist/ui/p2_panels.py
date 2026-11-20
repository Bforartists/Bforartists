"""Sidebar panels for Graph Editor and Dope Sheet key editing.

These panels live under the "AnimAssist" category of the Graph/Dope Sheet
sidebars so they do not collide with the existing 3D viewport panels that
already use ``ui/panels.py``.
"""

from __future__ import annotations

from bpy.types import Panel

from ..operators.p2_diag_ops import get_last_summary
# --- EXPLAINER HELP INTEGRATION ---
from ..core.help_draw import draw_explainer_icon
from .editor_placement import detached_panel_clone


_CATEGORY = "Keys"


# --- EXPLAINER HELP INTEGRATION ---
def _op_with_help(layout, context, op_id: str, *, text: str | None = None, icon: str | None = None):
    """Draw an operator button with a trailing explainer ``?`` icon.

    Returns the operator properties so the caller can set additional fields
    just as it would on a normal ``layout.operator(...)`` call.
    """
    row = layout.row(align=True)
    kwargs = {}
    if text is not None:
        kwargs["text"] = text
    if icon is not None:
        kwargs["icon"] = icon
    op_props = row.operator(op_id, **kwargs)
    draw_explainer_icon(row, context, f"op.{op_id}")
    return op_props


class _P2Panel(Panel):
    bl_space_type = "GRAPH_EDITOR"
    bl_region_type = "UI"
    bl_category = _CATEGORY


class ANIMASSIST_PT_p2_selection(_P2Panel):
    bl_idname = "ANIMASSIST_PT_p2_selection"
    bl_label = "Key Selection"
    bl_order = 80

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)
        col.operator("animassist.select_all_visible", icon="RESTRICT_SELECT_OFF")
        col.operator("animassist.deselect_all_visible")
        col.operator("animassist.invert_selection")

        box = layout.box()
        box.label(text="By Type")
        # --- EXPLAINER HELP INTEGRATION ---
        _op_with_help(box, context, "animassist.select_by_key_type_adv")
        _op_with_help(box, context, "animassist.select_by_interpolation")
        _op_with_help(box, context, "animassist.select_by_handle_type_adv")

        box = layout.box()
        box.label(text="Range")
        # --- EXPLAINER HELP INTEGRATION ---
        _op_with_help(box, context, "animassist.select_frame_range")
        box.operator("animassist.select_playback_range")
        box.operator("animassist.select_preview_range")

        box = layout.box()
        box.label(text="Structural")
        # --- EXPLAINER HELP INTEGRATION ---
        _op_with_help(box, context, "animassist.select_every_nth")
        _op_with_help(box, context, "animassist.select_neighbors")
        box.operator("animassist.select_between_selected")
        _op_with_help(box, context, "animassist.select_first_last")
        _op_with_help(box, context, "animassist.select_local_extremes")
        _op_with_help(box, context, "animassist.select_flat_segments")
        _op_with_help(box, context, "animassist.select_by_value_range")

        box = layout.box()
        box.label(text="Metadata")
        # --- EXPLAINER HELP INTEGRATION ---
        _op_with_help(box, context, "animassist.select_by_tag")
        _op_with_help(box, context, "animassist.select_protected")


class ANIMASSIST_PT_p2_channels(_P2Panel):
    bl_idname = "ANIMASSIST_PT_p2_channels"
    bl_label = "Channel Isolation"
    bl_order = 20

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)
        # --- EXPLAINER HELP INTEGRATION ---
        _op_with_help(col, context, "animassist.isolate_selected_channels")
        _op_with_help(col, context, "animassist.isolate_transform")
        _op_with_help(col, context, "animassist.isolate_selected_bones")
        _op_with_help(col, context, "animassist.isolate_custom_props")
        _op_with_help(col, context, "animassist.isolate_by_regex")

        col = layout.column(align=True)
        col.operator("animassist.show_all_channels")
        col.operator("animassist.invert_channel_visibility")
        # --- EXPLAINER HELP INTEGRATION ---
        _op_with_help(col, context, "animassist.mute_unselected_channels")

        # --- EXPLAINER HELP INTEGRATION ---
        row = layout.row(align=True)
        row.operator("animassist.push_channel_isolation", text="Save")
        row.operator("animassist.pop_channel_isolation", text="Restore")
        draw_explainer_icon(row, context, "op.animassist.push_channel_isolation")


class ANIMASSIST_PT_p2_metadata(_P2Panel):
    bl_idname = "ANIMASSIST_PT_p2_metadata"
    bl_label = "Key Metadata"
    bl_order = 70

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)
        # --- EXPLAINER HELP INTEGRATION ---
        _op_with_help(col, context, "animassist.tag_selected_keys")
        _op_with_help(col, context, "animassist.clear_tag_selected_keys")
        _op_with_help(col, context, "animassist.set_key_note")
        _op_with_help(col, context, "animassist.set_key_flavor")

        # --- EXPLAINER HELP INTEGRATION ---
        row = layout.row(align=True)
        op = row.operator("animassist.protect_selected_keys", text="Protect")
        op.protected = True
        op = row.operator("animassist.protect_selected_keys", text="Unprotect")
        op.protected = False
        draw_explainer_icon(row, context, "op.animassist.protect_selected_keys")

        col = layout.column(align=True)
        col.operator("animassist.prune_orphan_key_metadata")
        col.operator("animassist.clear_all_key_metadata")


class ANIMASSIST_PT_p2_diagnostics(_P2Panel):
    bl_idname = "ANIMASSIST_PT_p2_diagnostics"
    bl_label = "Key Diagnostics"
    bl_order = 50

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)
        # --- EXPLAINER HELP INTEGRATION ---
        _op_with_help(col, context, "animassist.scan_dense_keys")
        _op_with_help(col, context, "animassist.scan_redundant_keys")
        _op_with_help(col, context, "animassist.scan_spike_keys")

        summary = get_last_summary()
        if summary and summary.get("TOTAL"):
            box = layout.box()
            box.label(text="Last scan:")
            for k in ("DENSE", "REDUNDANT", "SPIKE"):
                if summary.get(k):
                    box.label(text=f"{k.title()}: {summary[k]}")


class ANIMASSIST_PT_p2_keyutils(_P2Panel):
    bl_idname = "ANIMASSIST_PT_p2_keyutils"
    bl_label = "Key Utilities"
    bl_order = 90

    def draw(self, context):
        layout = self.layout
        # --- EXPLAINER HELP INTEGRATION ---
        row = layout.row(align=True)
        row.operator("animassist.copy_selected_keys", text="Copy")
        row.operator("animassist.paste_keys_at_frame", text="Paste")
        draw_explainer_icon(row, context, "op.animassist.paste_keys_at_frame")

        col = layout.column(align=True)
        # --- EXPLAINER HELP INTEGRATION ---
        _op_with_help(col, context, "animassist.offset_selected_frames")
        _op_with_help(col, context, "animassist.offset_selected_values")
        _op_with_help(col, context, "animassist.snap_keys_to_integer_frames")
        _op_with_help(col, context, "animassist.mirror_selected_keys")
        col.separator()
        # --- EXPLAINER HELP INTEGRATION ---
        _op_with_help(col, context, "animassist.safe_delete_selected_keys", icon="X")


# Dope Sheet copies of the same panels. Built as independent classes, not
# subclasses: a registered subclass would detach the Graph Editor originals.

ANIMASSIST_PT_p2_selection_ds = detached_panel_clone(
    ANIMASSIST_PT_p2_selection, "ANIMASSIST_PT_p2_selection_ds",
    bl_idname="ANIMASSIST_PT_p2_selection_ds", bl_space_type="DOPESHEET_EDITOR",
)


ANIMASSIST_PT_p2_channels_ds = detached_panel_clone(
    ANIMASSIST_PT_p2_channels, "ANIMASSIST_PT_p2_channels_ds",
    bl_idname="ANIMASSIST_PT_p2_channels_ds", bl_space_type="DOPESHEET_EDITOR",
)


ANIMASSIST_PT_p2_metadata_ds = detached_panel_clone(
    ANIMASSIST_PT_p2_metadata, "ANIMASSIST_PT_p2_metadata_ds",
    bl_idname="ANIMASSIST_PT_p2_metadata_ds", bl_space_type="DOPESHEET_EDITOR",
)


ANIMASSIST_PT_p2_diagnostics_ds = detached_panel_clone(
    ANIMASSIST_PT_p2_diagnostics, "ANIMASSIST_PT_p2_diagnostics_ds",
    bl_idname="ANIMASSIST_PT_p2_diagnostics_ds", bl_space_type="DOPESHEET_EDITOR",
)


ANIMASSIST_PT_p2_keyutils_ds = detached_panel_clone(
    ANIMASSIST_PT_p2_keyutils, "ANIMASSIST_PT_p2_keyutils_ds",
    bl_idname="ANIMASSIST_PT_p2_keyutils_ds", bl_space_type="DOPESHEET_EDITOR",
)


classes: tuple[type, ...] = (
    ANIMASSIST_PT_p2_selection,
    ANIMASSIST_PT_p2_channels,
    ANIMASSIST_PT_p2_metadata,
    ANIMASSIST_PT_p2_diagnostics,
    ANIMASSIST_PT_p2_keyutils,
    ANIMASSIST_PT_p2_selection_ds,
    ANIMASSIST_PT_p2_channels_ds,
    ANIMASSIST_PT_p2_metadata_ds,
    ANIMASSIST_PT_p2_diagnostics_ds,
    ANIMASSIST_PT_p2_keyutils_ds,
)

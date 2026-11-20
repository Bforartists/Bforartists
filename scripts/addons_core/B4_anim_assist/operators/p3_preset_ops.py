# --- BREAKDOWN TOOLS ---
"""Preset + exclusion-set operators (features 27, 43, 44)."""

from __future__ import annotations

import bpy
from bpy.props import EnumProperty, StringProperty

from ..core import breakdown_presets as bp
from ..core.breakdown_masks import BreakdownMask
from ..core.p3_properties import get_p3
from .p3_breakdown_ops import (
    _options_from_scene,
    _poll_animated,
    _run,
)


def _mask_from_kind_str(kind: str) -> BreakdownMask:
    if kind == "LOCATION":
        return BreakdownMask.location_only()
    if kind == "ROTATION":
        return BreakdownMask.rotation_only()
    if kind == "SCALE":
        return BreakdownMask.scale_only()
    if kind == "TRANSFORM":
        return BreakdownMask.transform_only()
    return BreakdownMask()


class AA_OT_apply_preset(bpy.types.Operator):
    """Apply the active built-in breakdown preset at the current frame."""

    bl_idname = "animassist.apply_preset"
    bl_label = "Apply Preset"
    bl_description = (
        "Run a breakdown using the parameters of the currently selected "
        "built-in breakdown preset at the current frame"
    )
    bl_options = {"REGISTER", "UNDO"}

    preset_name: StringProperty(  # type: ignore[valid-type]
        name="Preset Name",
        description="Name of the built-in preset to apply. Leave empty to use the active preset from the property group.",
        default="",
    )

    @classmethod
    def poll(cls, context):
        return _poll_animated(cls, context)

    def execute(self, context):
        p3 = get_p3(context)
        name = self.preset_name.strip() or (p3.active_preset if p3 else "Midpoint")
        preset = bp.find_builtin_preset(name)
        if preset is None:
            self.report({"WARNING"}, f"Unknown preset '{name}'.")
            return {"CANCELLED"}

        mask = _mask_from_kind_str(preset.mask_kind)
        options = _options_from_scene(
            context,
            factor=preset.factor,
            mode=preset.mode,
            mask_override=mask,
        )
        return _run(self, context, options)


class AA_OT_save_preset(bpy.types.Operator):
    """Save the current breakdown settings as a new user preset."""

    bl_idname = "animassist.save_preset"
    bl_label = "Save Preset"
    bl_description = (
        "Append a new row to the user preset list capturing the current "
        "factor, mode, and active mask kind from the property group"
    )
    bl_options = {"REGISTER", "UNDO"}

    preset_name: StringProperty(  # type: ignore[valid-type]
        name="Preset Name",
        description="Human-readable name for the new user preset.",
        default="Custom Preset",
    )

    def execute(self, context):
        p3 = get_p3(context)
        if p3 is None:
            self.report({"WARNING"}, "Property group unavailable.")
            return {"CANCELLED"}
        row = p3.user_presets.add()
        row.name = self.preset_name or "Custom Preset"
        row.factor = float(p3.factor)
        row.mode = str(p3.mode)
        # Infer a mask kind from the current mask toggles.
        kind = "ALL"
        if p3.mask_location and not (p3.mask_rotation or p3.mask_scale or p3.mask_custom):
            kind = "LOCATION"
        elif p3.mask_rotation and not (p3.mask_location or p3.mask_scale or p3.mask_custom):
            kind = "ROTATION"
        elif p3.mask_scale and not (p3.mask_location or p3.mask_rotation or p3.mask_custom):
            kind = "SCALE"
        elif (
            p3.mask_location and p3.mask_rotation and p3.mask_scale and not p3.mask_custom
        ):
            kind = "TRANSFORM"
        row.mask_kind = kind
        p3.user_preset_index = len(p3.user_presets) - 1
        self.report({"INFO"}, f"Saved preset '{row.name}'.")
        return {"FINISHED"}


class AA_OT_delete_preset(bpy.types.Operator):
    """Delete the selected row from the user preset list."""

    bl_idname = "animassist.delete_preset"
    bl_label = "Delete Preset"
    bl_description = "Remove the currently selected row from the user preset list"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        p3 = get_p3(context)
        if p3 is None or not p3.user_presets:
            self.report({"WARNING"}, "No user presets to delete.")
            return {"CANCELLED"}
        idx = max(0, min(int(p3.user_preset_index), len(p3.user_presets) - 1))
        name = p3.user_presets[idx].name
        p3.user_presets.remove(idx)
        p3.user_preset_index = max(0, idx - 1)
        self.report({"INFO"}, f"Deleted preset '{name}'.")
        return {"FINISHED"}


class AA_OT_manage_exclusion_set(bpy.types.Operator):
    """Add or remove rows in the exclusion pattern list."""

    bl_idname = "animassist.manage_exclusion_set"
    bl_label = "Manage Exclusion Set"
    bl_description = (
        "Add or remove an entry in the exclusion pattern list. "
        "Patterns are matched as substrings against fcurve data_paths"
    )
    bl_options = {"REGISTER", "UNDO"}

    action: EnumProperty(  # type: ignore[valid-type]
        name="Action",
        description="Whether to add a new empty pattern row or remove the currently selected one.",
        items=(
            ("ADD", "Add", "Append a new empty exclusion pattern row."),
            ("REMOVE", "Remove", "Remove the currently selected exclusion pattern row."),
            ("CLEAR", "Clear", "Remove every exclusion pattern row."),
        ),
        default="ADD",
    )

    def execute(self, context):
        p3 = get_p3(context)
        if p3 is None:
            self.report({"WARNING"}, "Property group unavailable.")
            return {"CANCELLED"}

        if self.action == "ADD":
            row = p3.exclusion_patterns.add()
            row.pattern = ""
            p3.exclusion_index = len(p3.exclusion_patterns) - 1
            self.report({"INFO"}, "Added exclusion pattern row.")
        elif self.action == "REMOVE":
            if not p3.exclusion_patterns:
                self.report({"WARNING"}, "Nothing to remove.")
                return {"CANCELLED"}
            idx = max(0, min(int(p3.exclusion_index), len(p3.exclusion_patterns) - 1))
            p3.exclusion_patterns.remove(idx)
            p3.exclusion_index = max(0, idx - 1)
            self.report({"INFO"}, "Removed exclusion pattern row.")
        else:
            p3.exclusion_patterns.clear()
            p3.exclusion_index = 0
            self.report({"INFO"}, "Cleared exclusion patterns.")
        return {"FINISHED"}


CLASSES: tuple[type, ...] = (
    AA_OT_apply_preset,
    AA_OT_save_preset,
    AA_OT_delete_preset,
    AA_OT_manage_exclusion_set,
)

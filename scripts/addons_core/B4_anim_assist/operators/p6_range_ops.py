# --- RETIMING TOOLS ---
"""Timing-range operators.

Operators for defining, selecting, scaling, offsetting, storing, restoring,
and clearing the active timing range.  All range mutations write to the
``AA_P6_Properties`` PropertyGroup and are undo-safe (REGISTER + UNDO or
no RNA changes at all for pure-query ops).
"""

from __future__ import annotations

import bpy

from ..core.logging import get_logger
from ..core.p6_properties import get_p6
from ..core import p6_retime_math as rm
from ..core.fcurve_compat import get_fcurves

_log = get_logger(__name__)


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _get_fcurves(context: bpy.types.Context):
    obj = getattr(context, "active_object", None)
    if obj is None:
        return [], ""
    adata = getattr(obj, "animation_data", None)
    action = getattr(adata, "action", None) if adata else None
    if action is None:
        return [], getattr(obj, "name", "")
    return get_fcurves(action, anim_data=adata), obj.name


def _tag_redraw(context: bpy.types.Context) -> None:
    if getattr(context, "screen", None) is None:
        return
    for area in context.screen.areas:
        area.tag_redraw()


def _p6_base_poll(context: bpy.types.Context) -> bool:
    if not hasattr(context, "scene") or context.scene is None:
        return False
    obj = getattr(context, "active_object", None)
    if obj is None:
        return False
    adata = getattr(obj, "animation_data", None)
    return adata is not None and getattr(adata, "action", None) is not None


def _scene_poll(context: bpy.types.Context) -> bool:
    return hasattr(context, "scene") and context.scene is not None


# ---------------------------------------------------------------------------
# 1. Set Range Start
# ---------------------------------------------------------------------------

class AA_OT_p6_set_range_start(bpy.types.Operator):
    """Capture the current scene frame as the custom range start."""

    bl_idname = "animassist.p6_set_range_start"
    bl_label = "Set Range Start"
    bl_description = "Set the custom timing range start to the current frame"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return _scene_poll(context) and get_p6(context) is not None

    def execute(self, context):
        p6 = get_p6(context)
        if p6 is None:
            self.report({"WARNING"}, "Retiming properties not available")
            return {"CANCELLED"}
        p6.range_start = float(context.scene.frame_current)
        # Clamp end to be >= start.
        if p6.range_end < p6.range_start:
            p6.range_end = p6.range_start
        p6.range_mode = "CUSTOM"
        self.report({"INFO"}, f"Range start = {p6.range_start:.1f}")
        return {"FINISHED"}


# ---------------------------------------------------------------------------
# 2. Set Range End
# ---------------------------------------------------------------------------

class AA_OT_p6_set_range_end(bpy.types.Operator):
    """Capture the current scene frame as the custom range end."""

    bl_idname = "animassist.p6_set_range_end"
    bl_label = "Set Range End"
    bl_description = "Set the custom timing range end to the current frame"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return _scene_poll(context) and get_p6(context) is not None

    def execute(self, context):
        p6 = get_p6(context)
        if p6 is None:
            self.report({"WARNING"}, "Retiming properties not available")
            return {"CANCELLED"}
        p6.range_end = float(context.scene.frame_current)
        # Clamp start to be <= end.
        if p6.range_start > p6.range_end:
            p6.range_start = p6.range_end
        p6.range_mode = "CUSTOM"
        self.report({"INFO"}, f"Range end = {p6.range_end:.1f}")
        return {"FINISHED"}


# ---------------------------------------------------------------------------
# 3. Select Keys in Range
# ---------------------------------------------------------------------------

class AA_OT_p6_select_keys_in_range(bpy.types.Operator):
    """Select all keyframes whose timing falls within the active range."""

    bl_idname = "animassist.p6_select_keys_in_range"
    bl_label = "Select Keys in Range"
    bl_description = "Select all keys inside the active timing range"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return _p6_base_poll(context)

    def execute(self, context):
        p6 = get_p6(context)
        if p6 is None:
            self.report({"WARNING"}, "Retiming properties not available")
            return {"CANCELLED"}

        fcurves, _ = _get_fcurves(context)
        if not fcurves:
            self.report({"WARNING"}, "No action on active object")
            return {"CANCELLED"}

        lo, hi = rm.resolve_active_range(p6, context)
        selected = 0
        for fc in fcurves:
            for kp in fc.keyframe_points:
                in_range = lo <= kp.co.x <= hi
                kp.select_control_point = in_range
                if in_range:
                    selected += 1

        _tag_redraw(context)
        self.report({"INFO"}, f"Selected {selected} key(s) in [{lo:.0f}, {hi:.0f}]")
        return {"FINISHED"}


# ---------------------------------------------------------------------------
# 4. Scale Range
# ---------------------------------------------------------------------------

class AA_OT_p6_scale_range(bpy.types.Operator):
    """Scale only the keys inside the active timing range."""

    bl_idname = "animassist.p6_scale_range"
    bl_label = "Scale Range"
    bl_description = "Scale keyframe timing within the active range only"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return _p6_base_poll(context)

    def execute(self, context):
        p6 = get_p6(context)
        if p6 is None:
            self.report({"WARNING"}, "Retiming properties not available")
            return {"CANCELLED"}

        fcurves, obj_name = _get_fcurves(context)
        if not fcurves:
            self.report({"WARNING"}, "No action on active object")
            return {"CANCELLED"}

        lo, hi = rm.resolve_active_range(p6, context)
        in_range = rm.collect_key_frames(fcurves)
        in_range = [f for f in in_range if lo <= f <= hi]
        pivot = rm.resolve_pivot(
            p6.anchor_mode,
            in_range,
            float(context.scene.frame_current),
            custom_frame=p6.pivot_frame,
        )

        rm.apply_scale(fcurves, pivot, p6.scale_factor, frame_range=(lo, hi))

        _tag_redraw(context)
        self.report(
            {"INFO"},
            f"Scale ×{p6.scale_factor:.3f} in range [{lo:.0f}, {hi:.0f}]",
        )
        return {"FINISHED"}


# ---------------------------------------------------------------------------
# 5. Offset Range
# ---------------------------------------------------------------------------

class AA_OT_p6_offset_range(bpy.types.Operator):
    """Shift only the keys inside the active timing range."""

    bl_idname = "animassist.p6_offset_range"
    bl_label = "Offset Range"
    bl_description = "Offset keyframes within the active range by the configured amount"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return _p6_base_poll(context)

    def execute(self, context):
        p6 = get_p6(context)
        if p6 is None:
            self.report({"WARNING"}, "Retiming properties not available")
            return {"CANCELLED"}

        fcurves, _ = _get_fcurves(context)
        if not fcurves:
            self.report({"WARNING"}, "No action on active object")
            return {"CANCELLED"}

        lo, hi = rm.resolve_active_range(p6, context)
        rm.apply_offset(fcurves, p6.offset_frames, frame_range=(lo, hi))

        _tag_redraw(context)
        sign = "+" if p6.offset_frames >= 0 else ""
        self.report(
            {"INFO"},
            f"Offset {sign}{p6.offset_frames:.1f}f in range [{lo:.0f}, {hi:.0f}]",
        )
        return {"FINISHED"}


# ---------------------------------------------------------------------------
# 6. Store Range
# ---------------------------------------------------------------------------

class AA_OT_p6_store_range(bpy.types.Operator):
    """Save the current range as a reusable preset on the scene."""

    bl_idname = "animassist.p6_store_range"
    bl_label = "Store Range"
    bl_description = "Save the current timing range start/end as a scene preset"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return _scene_poll(context) and get_p6(context) is not None

    def execute(self, context):
        p6 = get_p6(context)
        if p6 is None:
            self.report({"WARNING"}, "Retiming properties not available")
            return {"CANCELLED"}

        lo, hi = rm.resolve_active_range(p6, context)
        p6.stored_range_start = lo
        p6.stored_range_end   = hi
        p6.has_stored_range   = True

        self.report({"INFO"}, f"Range stored: [{lo:.1f}, {hi:.1f}]")
        return {"FINISHED"}


# ---------------------------------------------------------------------------
# 7. Restore Range
# ---------------------------------------------------------------------------

class AA_OT_p6_restore_range(bpy.types.Operator):
    """Load the previously stored range preset."""

    bl_idname = "animassist.p6_restore_range"
    bl_label = "Restore Range"
    bl_description = "Restore the previously stored timing range"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        p6 = get_p6(context)
        return p6 is not None and bool(p6.has_stored_range)

    def execute(self, context):
        p6 = get_p6(context)
        if p6 is None or not p6.has_stored_range:
            self.report({"WARNING"}, "No stored range available")
            return {"CANCELLED"}

        p6.range_start = p6.stored_range_start
        p6.range_end   = p6.stored_range_end
        p6.range_mode  = "CUSTOM"

        self.report(
            {"INFO"},
            f"Range restored: [{p6.range_start:.1f}, {p6.range_end:.1f}]",
        )
        return {"FINISHED"}


# ---------------------------------------------------------------------------
# 8. Clear Range
# ---------------------------------------------------------------------------

class AA_OT_p6_clear_range(bpy.types.Operator):
    """Reset range to the scene's playback range and clear stored preset."""

    bl_idname = "animassist.p6_clear_range"
    bl_label = "Clear Range"
    bl_description = "Reset timing range to scene playback range and clear stored preset"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return _scene_poll(context) and get_p6(context) is not None

    def execute(self, context):
        p6 = get_p6(context)
        if p6 is None:
            self.report({"WARNING"}, "Retiming properties not available")
            return {"CANCELLED"}

        scene = context.scene
        p6.range_start      = float(scene.frame_start)
        p6.range_end        = float(scene.frame_end)
        p6.range_mode       = "SCENE"
        p6.has_stored_range = False

        self.report(
            {"INFO"},
            f"Range cleared → [{p6.range_start:.0f}, {p6.range_end:.0f}]",
        )
        return {"FINISHED"}


# ---------------------------------------------------------------------------
# Class list
# ---------------------------------------------------------------------------

CLASSES: tuple[type, ...] = (
    AA_OT_p6_set_range_start,
    AA_OT_p6_set_range_end,
    AA_OT_p6_select_keys_in_range,
    AA_OT_p6_scale_range,
    AA_OT_p6_offset_range,
    AA_OT_p6_store_range,
    AA_OT_p6_restore_range,
    AA_OT_p6_clear_range,
)

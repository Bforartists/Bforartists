# --- RETIMING TOOLS ---
"""Ripple edit operators.

Operators for inserting/removing time and ripple-shifting all keys on one
side of the playhead.  All mutations go through ``p6_retime_math`` pure
functions and are wrapped in ``bl_options = {"REGISTER", "UNDO"}``.
"""

from __future__ import annotations

import bpy
from bpy.props import FloatProperty, IntProperty

from ..core.logging import get_logger
from ..core.p6_properties import get_p6
from ..core import p6_retime_math as rm
from ..core.fcurve_compat import get_fcurves

_log = get_logger(__name__)


# ---------------------------------------------------------------------------
# Shared helpers (mirrors p6_retime_ops helpers — minimal cross-import)
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


# ---------------------------------------------------------------------------
# 1. Ripple Forward
# ---------------------------------------------------------------------------

class AA_OT_p6_ripple_forward(bpy.types.Operator):
    """Push all keys after the playhead forward by the ripple amount."""

    bl_idname = "animassist.p6_ripple_forward"
    bl_label = "Ripple Forward"
    bl_description = "Shift all keys after the current frame forward by Ripple Amount"
    bl_options = {"REGISTER", "UNDO"}

    ripple_delta: FloatProperty(  # type: ignore[valid-type]
        name="Ripple Amount",
        description="Number of frames to shift keys after the playhead",
        default=1.0,
        soft_min=-500.0,
        soft_max=500.0,
        step=100,
        precision=1,
    )

    @classmethod
    def poll(cls, context):
        return _p6_base_poll(context)

    def execute(self, context):
        fcurves, _ = _get_fcurves(context)
        if not fcurves:
            self.report({"WARNING"}, "No action on active object")
            return {"CANCELLED"}

        threshold = float(context.scene.frame_current)
        rm.apply_ripple(fcurves, threshold, self.ripple_delta, direction="FORWARD")

        _tag_redraw(context)
        self.report(
            {"INFO"},
            f"Ripple forward {self.ripple_delta:+.1f}f from frame {threshold:.0f}",
        )
        return {"FINISHED"}

    def invoke(self, context, event):
        p6 = get_p6(context)
        if p6 is not None:
            self.ripple_delta = abs(p6.ripple_delta)
        return self.execute(context)


# ---------------------------------------------------------------------------
# 2. Ripple Backward
# ---------------------------------------------------------------------------

class AA_OT_p6_ripple_backward(bpy.types.Operator):
    """Pull all keys before the playhead backward by the ripple amount."""

    bl_idname = "animassist.p6_ripple_backward"
    bl_label = "Ripple Backward"
    bl_description = "Shift all keys before the current frame backward by Ripple Amount"
    bl_options = {"REGISTER", "UNDO"}

    ripple_delta: FloatProperty(  # type: ignore[valid-type]
        name="Ripple Amount",
        description="Number of frames to shift keys before the playhead",
        default=1.0,
        soft_min=0.0,
        soft_max=500.0,
        step=100,
        precision=1,
    )

    @classmethod
    def poll(cls, context):
        return _p6_base_poll(context)

    def execute(self, context):
        fcurves, _ = _get_fcurves(context)
        if not fcurves:
            self.report({"WARNING"}, "No action on active object")
            return {"CANCELLED"}

        threshold = float(context.scene.frame_current)
        # Backward ripple uses a negative delta internally.
        rm.apply_ripple(
            fcurves, threshold, -abs(self.ripple_delta), direction="BACKWARD"
        )

        _tag_redraw(context)
        self.report(
            {"INFO"},
            f"Ripple backward {self.ripple_delta:.1f}f from frame {threshold:.0f}",
        )
        return {"FINISHED"}

    def invoke(self, context, event):
        p6 = get_p6(context)
        if p6 is not None:
            self.ripple_delta = abs(p6.ripple_delta)
        return self.execute(context)


# ---------------------------------------------------------------------------
# 3. Insert Time
# ---------------------------------------------------------------------------

class AA_OT_p6_insert_time(bpy.types.Operator):
    """Insert N blank frames at the playhead; later keys slide forward."""

    bl_idname = "animassist.p6_insert_time"
    bl_label = "Insert Time"
    bl_description = "Insert blank frames at playhead, ripple-shifting later keys forward"
    bl_options = {"REGISTER", "UNDO"}

    insert_frames: IntProperty(  # type: ignore[valid-type]
        name="Frames",
        description="Number of blank frames to insert at the playhead",
        default=1,
        min=1,
        soft_max=500,
    )

    @classmethod
    def poll(cls, context):
        return _p6_base_poll(context)

    def execute(self, context):
        fcurves, _ = _get_fcurves(context)
        if not fcurves:
            self.report({"WARNING"}, "No action on active object")
            return {"CANCELLED"}

        threshold = float(context.scene.frame_current)
        rm.apply_ripple(
            fcurves, threshold, float(self.insert_frames), direction="FORWARD"
        )

        _tag_redraw(context)
        self.report(
            {"INFO"},
            f"Inserted {self.insert_frames}f at frame {threshold:.0f}",
        )
        return {"FINISHED"}

    def invoke(self, context, event):
        p6 = get_p6(context)
        if p6 is not None:
            self.insert_frames = p6.insert_frames
        return self.execute(context)


# ---------------------------------------------------------------------------
# 4. Remove Time
# ---------------------------------------------------------------------------

class AA_OT_p6_remove_time(bpy.types.Operator):
    """Remove N frames at the playhead; later keys slide backward."""

    bl_idname = "animassist.p6_remove_time"
    bl_label = "Remove Time"
    bl_description = "Delete keys in window and ripple-shift later keys backward"
    bl_options = {"REGISTER", "UNDO"}

    remove_frames: IntProperty(  # type: ignore[valid-type]
        name="Frames",
        default=1,
        min=1,
        soft_max=500,
    )

    @classmethod
    def poll(cls, context):
        return _p6_base_poll(context)

    def execute(self, context):
        fcurves, _ = _get_fcurves(context)
        if not fcurves:
            self.report({"WARNING"}, "No action on active object")
            return {"CANCELLED"}

        threshold = float(context.scene.frame_current)
        window_end = threshold + float(self.remove_frames)

        # First delete keys inside the removed window.
        deleted = 0
        for fc in fcurves:
            # Exclusive on both ends: the key on the playhead and the key at
            # the window's far edge survive (the latter ripples back below).
            to_remove = [
                kp for kp in fc.keyframe_points
                if threshold < kp.co.x < window_end
            ]
            for kp in reversed(to_remove):
                fc.keyframe_points.remove(kp)
                deleted += 1
            if to_remove:
                fc.update()

        # Then ripple-shift keys after the window's end backward.
        rm.apply_ripple(
            fcurves, window_end, -float(self.remove_frames), direction="FORWARD",
            inclusive=True,
        )

        _tag_redraw(context)
        self.report(
            {"INFO"},
            f"Removed {self.remove_frames}f at frame {threshold:.0f} "
            f"(deleted {deleted} key(s))",
        )
        return {"FINISHED"}

    def invoke(self, context, event):
        p6 = get_p6(context)
        if p6 is not None:
            self.remove_frames = p6.insert_frames
        return self.execute(context)


# ---------------------------------------------------------------------------
# 5. Ripple to End
# ---------------------------------------------------------------------------

class AA_OT_p6_ripple_to_end(bpy.types.Operator):
    """Shift all keys from the playhead to the last key by the ripple amount."""

    bl_idname = "animassist.p6_ripple_to_end"
    bl_label = "Ripple to End"
    bl_description = "Shift keys from playhead to the last key by Ripple Amount"
    bl_options = {"REGISTER", "UNDO"}

    ripple_delta: FloatProperty(  # type: ignore[valid-type]
        name="Ripple Amount",
        description="Number of frames to shift keys from the playhead to the end",
        default=1.0,
        soft_min=-500.0,
        soft_max=500.0,
        step=100,
        precision=1,
    )

    @classmethod
    def poll(cls, context):
        return _p6_base_poll(context)

    def execute(self, context):
        fcurves, _ = _get_fcurves(context)
        if not fcurves:
            self.report({"WARNING"}, "No action on active object")
            return {"CANCELLED"}

        threshold = float(context.scene.frame_current)
        all_frames = rm.collect_key_frames(fcurves)
        if not all_frames:
            self.report({"WARNING"}, "No keys found")
            return {"CANCELLED"}

        last_frame = all_frames[-1]
        # Shift keys that are >= threshold and <= last_frame.
        for fc in fcurves:
            for kp in fc.keyframe_points:
                x = kp.co.x
                if x < threshold or x > last_frame:
                    continue
                new_x = x + self.ripple_delta
                dx = new_x - x
                kp.co.x            = new_x
                kp.handle_left.x  += dx
                kp.handle_right.x += dx
            fc.update()

        _tag_redraw(context)
        self.report(
            {"INFO"},
            f"Ripple to end {self.ripple_delta:+.1f}f from frame {threshold:.0f}",
        )
        return {"FINISHED"}

    def invoke(self, context, event):
        p6 = get_p6(context)
        if p6 is not None:
            self.ripple_delta = p6.ripple_delta
        return self.execute(context)


# ---------------------------------------------------------------------------
# 6. Compress Timing
# ---------------------------------------------------------------------------

class AA_OT_p6_compress_timing(bpy.types.Operator):
    """Scale down timing in the active range to fit a shorter duration."""

    bl_idname = "animassist.p6_compress_timing"
    bl_label = "Compress Timing"
    bl_description = "Scale timing in the active range to fit a target duration"
    bl_options = {"REGISTER", "UNDO"}

    target_duration: FloatProperty(  # type: ignore[valid-type]
        name="Target Duration (frames)",
        description="Desired duration of the active range after compression",
        default=24.0,
        min=1.0,
        soft_max=5000.0,
        precision=1,
    )

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
        current_span = hi - lo
        if current_span < 1e-6:
            self.report({"WARNING"}, "Active range has zero span")
            return {"CANCELLED"}

        factor = self.target_duration / current_span
        rm.apply_scale(fcurves, lo, factor, frame_range=(lo, hi))

        _tag_redraw(context)
        self.report(
            {"INFO"},
            f"Compressed {current_span:.0f}f → {self.target_duration:.0f}f "
            f"(×{factor:.3f})",
        )
        return {"FINISHED"}

    def invoke(self, context, event):
        p6 = get_p6(context)
        if p6 is not None:
            lo, hi = rm.resolve_active_range(p6, context)
            self.target_duration = max(1.0, (hi - lo) * 0.75)
        return context.window_manager.invoke_props_dialog(self, width=260)

    def draw(self, context):
        self.layout.prop(self, "target_duration")


# ---------------------------------------------------------------------------
# Class list
# ---------------------------------------------------------------------------

CLASSES: tuple[type, ...] = (
    AA_OT_p6_ripple_forward,
    AA_OT_p6_ripple_backward,
    AA_OT_p6_insert_time,
    AA_OT_p6_remove_time,
    AA_OT_p6_ripple_to_end,
    AA_OT_p6_compress_timing,
)

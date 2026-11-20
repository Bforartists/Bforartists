# --- RETIMING TOOLS ---
"""Retiming operators: scale, offset, time-warp, reverse, bake, reset, match.

All operators:
* Use ``bl_options = {"REGISTER", "UNDO"}`` for Blender undo integration.
* Check ``poll()`` before offering themselves in the UI.
* Pull defaults from the ``AA_P6_Properties`` PropertyGroup via ``get_p6()``.
* Delegate FCurve mutation to ``p6_retime_math`` pure functions so the
  business logic stays testable without a Blender session.
"""

from __future__ import annotations

import bpy
from bpy.props import FloatProperty

from ..core.logging import get_logger
from ..core.p6_properties import get_p6
from ..core import p6_retime_math as rm
from ..core.fcurve_compat import get_fcurves

_log = get_logger(__name__)


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _get_fcurves(context: bpy.types.Context):
    """Return (fcurves, obj_name) for the active object's action, or ([], '')."""
    obj = getattr(context, "active_object", None)
    if obj is None:
        return [], ""
    adata = getattr(obj, "animation_data", None)
    action = getattr(adata, "action", None) if adata else None
    if action is None:
        return [], obj.name
    return get_fcurves(action, anim_data=adata), obj.name


def _tag_redraw(context: bpy.types.Context) -> None:
    if getattr(context, "screen", None) is None:
        return
    for area in context.screen.areas:
        area.tag_redraw()


def _p6_base_poll(context: bpy.types.Context, cls=None) -> bool:
    """Base poll: need a scene with an active object that has an action."""
    if not hasattr(context, "scene") or context.scene is None:
        if cls is not None:
            cls.poll_message_set("Open a scene to use retiming tools")
        return False
    obj = getattr(context, "active_object", None)
    if obj is None:
        if cls is not None:
            cls.poll_message_set("Select an animated object to retime its keys")
        return False
    adata = getattr(obj, "animation_data", None)
    if adata is None or getattr(adata, "action", None) is None:
        if cls is not None:
            cls.poll_message_set("Add keyframes to the active object before retiming")
        return False
    return True


# Module-level timing snapshot (last backup before a retime op).
_last_backup: list[dict] | None = None
_last_backup_obj: str = ""


def _store_backup(fcurves, obj_name: str) -> None:
    global _last_backup, _last_backup_obj
    _last_backup = rm.backup_fcurves(fcurves)
    _last_backup_obj = obj_name


def clear_last_backup() -> None:
    """Clear the timing snapshot cache.  Called on file load and addon disable."""
    global _last_backup, _last_backup_obj
    _last_backup = None
    _last_backup_obj = ""


# ---------------------------------------------------------------------------
# 1. Scale Keys
# ---------------------------------------------------------------------------

class AA_OT_p6_scale_keys(bpy.types.Operator):
    """Scale keyframe timing around the configured pivot point."""

    bl_idname = "animassist.p6_scale_keys"
    bl_label = "Scale Keys"
    bl_description = "Scale keyframe timing around the chosen pivot (anchor mode)"
    bl_options = {"REGISTER", "UNDO"}

    scale_factor: FloatProperty(  # type: ignore[valid-type]
        name="Scale Factor",
        description="Timing multiplier applied around the chosen pivot",
        default=1.0,
        min=0.01,
        max=100.0,
        soft_min=0.1,
        soft_max=10.0,
        step=10,
        precision=3,
    )

    @classmethod
    def poll(cls, context):
        return _p6_base_poll(context, cls)

    def execute(self, context):
        p6 = get_p6(context)
        if p6 is None:
            self.report({"WARNING"}, "Retiming properties not available")
            return {"CANCELLED"}

        fcurves, obj_name = _get_fcurves(context)
        if not fcurves:
            self.report({"WARNING"}, "No action on active object")
            return {"CANCELLED"}

        # Blender skips invoke in background execution. Resolve an unset
        # option here so menu, Search and script routes share the same default.
        if not self.properties.is_property_set("scale_factor"):
            self.scale_factor = p6.scale_factor
        factor = self.scale_factor
        all_frames = rm.collect_key_frames(fcurves)
        pivot = rm.resolve_pivot(
            p6.anchor_mode,
            all_frames,
            float(context.scene.frame_current),
            custom_frame=p6.pivot_frame,
        )

        range_filter = None
        if p6.range_mode != "SCENE":
            # Apply a range filter for SELECTION or CUSTOM mode; in SCENE mode
            # all keys are scaled (range_filter stays None).
            lo, hi = rm.resolve_active_range(p6, context)
            range_filter = (lo, hi)

        _store_backup(fcurves, obj_name)
        rm.apply_scale(fcurves, pivot, factor, frame_range=range_filter)

        _tag_redraw(context)
        self.report({"INFO"}, f"Scaled ×{factor:.3f} around frame {pivot:.1f}")
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


# ---------------------------------------------------------------------------
# 2. Offset Keys
# ---------------------------------------------------------------------------

class AA_OT_p6_offset_keys(bpy.types.Operator):
    """Shift all keys (or a range of keys) by a fixed number of frames."""

    bl_idname = "animassist.p6_offset_keys"
    bl_label = "Offset Keys"
    bl_description = "Shift keyframes by the configured frame offset"
    bl_options = {"REGISTER", "UNDO"}

    offset_frames: FloatProperty(  # type: ignore[valid-type]
        name="Offset",
        description="Number of frames to shift the affected keyframes",
        default=1.0,
        soft_min=-500.0,
        soft_max=500.0,
        step=100,
        precision=1,
    )

    @classmethod
    def poll(cls, context):
        return _p6_base_poll(context, cls)

    def execute(self, context):
        p6 = get_p6(context)
        if p6 is None:
            self.report({"WARNING"}, "Retiming properties not available")
            return {"CANCELLED"}

        fcurves, obj_name = _get_fcurves(context)
        if not fcurves:
            self.report({"WARNING"}, "No action on active object")
            return {"CANCELLED"}

        range_filter = None
        if p6.range_mode != "SCENE":
            lo, hi = rm.resolve_active_range(p6, context)
            range_filter = (lo, hi)

        _store_backup(fcurves, obj_name)
        if not self.properties.is_property_set("offset_frames"):
            self.offset_frames = p6.offset_frames
        rm.apply_offset(fcurves, self.offset_frames, frame_range=range_filter)

        _tag_redraw(context)
        sign = "+" if self.offset_frames >= 0 else ""
        self.report({"INFO"}, f"Offset keys {sign}{self.offset_frames:.1f}f")
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


# ---------------------------------------------------------------------------
# 3. Set Pivot from Playhead
# ---------------------------------------------------------------------------

class AA_OT_p6_set_pivot(bpy.types.Operator):
    """Store the current scene frame as the custom pivot."""

    bl_idname = "animassist.p6_set_pivot"
    bl_label = "Set Pivot from Playhead"
    bl_description = "Store the current frame as the custom scale pivot"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return hasattr(context, "scene") and context.scene is not None

    def execute(self, context):
        p6 = get_p6(context)
        if p6 is None:
            self.report({"WARNING"}, "Retiming properties not available")
            return {"CANCELLED"}
        p6.pivot_frame = float(context.scene.frame_current)
        self.report({"INFO"}, f"Pivot set to frame {p6.pivot_frame:.1f}")
        return {"FINISHED"}


# ---------------------------------------------------------------------------
# 4. Time Warp (by percentage)
# ---------------------------------------------------------------------------

class AA_OT_p6_time_warp(bpy.types.Operator):
    """Scale timing by a percentage (100 % = unchanged)."""

    bl_idname = "animassist.p6_time_warp"
    bl_label = "Time Warp %"
    bl_description = "Scale keyframe timing by a percentage value (100 = unchanged)"
    bl_options = {"REGISTER", "UNDO"}

    warp_percent: FloatProperty(  # type: ignore[valid-type]
        name="Warp %",
        description="Timing percentage where 100 percent leaves timing unchanged",
        default=100.0,
        min=1.0,
        max=10000.0,
        soft_min=10.0,
        soft_max=500.0,
        step=100,
        precision=1,
    )

    @classmethod
    def poll(cls, context):
        return _p6_base_poll(context, cls)

    def execute(self, context):
        p6 = get_p6(context)
        if p6 is None:
            self.report({"WARNING"}, "Retiming properties not available")
            return {"CANCELLED"}

        fcurves, obj_name = _get_fcurves(context)
        if not fcurves:
            self.report({"WARNING"}, "No action on active object")
            return {"CANCELLED"}

        factor = self.warp_percent / 100.0
        all_frames = rm.collect_key_frames(fcurves)
        pivot = rm.resolve_pivot(
            p6.anchor_mode,
            all_frames,
            float(context.scene.frame_current),
            custom_frame=p6.pivot_frame,
        )

        _store_backup(fcurves, obj_name)
        rm.apply_scale(fcurves, pivot, factor)

        _tag_redraw(context)
        self.report({"INFO"}, f"Time warp {self.warp_percent:.1f}% (×{factor:.3f})")
        return {"FINISHED"}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=260)

    def draw(self, context):
        self.layout.prop(self, "warp_percent")


# ---------------------------------------------------------------------------
# 5. Reverse Keys
# ---------------------------------------------------------------------------

class AA_OT_p6_reverse_keys(bpy.types.Operator):
    """Mirror keyframe timing within the active range."""

    bl_idname = "animassist.p6_reverse_keys"
    bl_label = "Reverse Keys"
    bl_description = "Mirror keyframe timing within the active range (values unchanged)"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return _p6_base_poll(context, cls)

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
        _store_backup(fcurves, obj_name)
        rm.reverse_keys_in_range(fcurves, lo, hi)

        _tag_redraw(context)
        self.report({"INFO"}, f"Reversed keys in range {lo:.0f}–{hi:.0f}")
        return {"FINISHED"}


# ---------------------------------------------------------------------------
# 6. Bake to Integer Frames
# ---------------------------------------------------------------------------

class AA_OT_p6_bake_timing(bpy.types.Operator):
    """Snap all keyframe positions to the nearest integer frame."""

    bl_idname = "animassist.p6_bake_timing"
    bl_label = "Bake to Integer Frames"
    bl_description = "Round all sub-frame key positions to nearest integer frame"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return _p6_base_poll(context, cls)

    def execute(self, context):
        fcurves, obj_name = _get_fcurves(context)
        if not fcurves:
            self.report({"WARNING"}, "No action on active object")
            return {"CANCELLED"}

        _store_backup(fcurves, obj_name)
        moved = rm.snap_keys_to_frames(fcurves)

        _tag_redraw(context)
        self.report({"INFO"}, f"Baked {moved} key(s) to integer frames")
        return {"FINISHED"}


# ---------------------------------------------------------------------------
# 7. Reset Timing (restore last backup)
# ---------------------------------------------------------------------------

class AA_OT_p6_reset_timing(bpy.types.Operator):
    """Restore key positions from the last timing snapshot."""

    bl_idname = "animassist.p6_reset_timing"
    bl_label = "Reset Timing"
    bl_description = "Restore keyframes from the last auto-saved timing snapshot"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if not _p6_base_poll(context, cls):
            return False
        if _last_backup is None:
            cls.poll_message_set("Run a retiming operation before resetting its timing")
            return False
        return True

    def execute(self, context):
        if _last_backup is None:
            self.report({"WARNING"}, "No timing snapshot available")
            return {"CANCELLED"}

        fcurves, obj_name = _get_fcurves(context)
        if not fcurves:
            self.report({"WARNING"}, "No action on active object")
            return {"CANCELLED"}

        if obj_name != _last_backup_obj:
            self.report(
                {"WARNING"},
                f"Snapshot is for '{_last_backup_obj}', not '{obj_name}'",
            )
            return {"CANCELLED"}

        rm.restore_fcurves(fcurves, _last_backup)
        _tag_redraw(context)
        self.report({"INFO"}, "Timing restored from snapshot")
        return {"FINISHED"}


# ---------------------------------------------------------------------------
# 8. Match Timing (active → reference duration)
# ---------------------------------------------------------------------------

class AA_OT_p6_match_timing(bpy.types.Operator):
    """Scale the active object's timing to match a reference object's duration."""

    bl_idname = "animassist.p6_match_timing"
    bl_label = "Match Timing"
    bl_description = "Scale the active object's timing to match the reference object's span"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if not _p6_base_poll(context, cls):
            return False
        selected = getattr(context, "selected_objects", []) or []
        if len(selected) < 2:
            cls.poll_message_set("Select a source and a target object to match timing")
            return False
        return True

    def execute(self, context):
        selected = list(getattr(context, "selected_objects", []) or [])
        active = getattr(context, "active_object", None)
        if active is None or len(selected) < 2:
            self.report({"WARNING"}, "Need at least 2 selected objects")
            return {"CANCELLED"}

        # Reference = any selected object that is not the active one.
        ref_obj = next((o for o in selected if o is not active), None)
        if ref_obj is None:
            self.report({"WARNING"}, "Could not identify reference object")
            return {"CANCELLED"}

        ref_adata = getattr(ref_obj, "animation_data", None)
        ref_action = getattr(ref_adata, "action", None) if ref_adata else None
        if ref_action is None:
            self.report({"WARNING"}, f"Reference '{ref_obj.name}' has no action")
            return {"CANCELLED"}

        ref_frames = rm.collect_key_frames(get_fcurves(ref_action))
        if len(ref_frames) < 2:
            self.report({"WARNING"}, "Reference action has fewer than 2 keyframes")
            return {"CANCELLED"}
        ref_span = ref_frames[-1] - ref_frames[0]

        fcurves, obj_name = _get_fcurves(context)
        if not fcurves:
            self.report({"WARNING"}, "No action on active object")
            return {"CANCELLED"}

        active_frames = rm.collect_key_frames(fcurves)
        if len(active_frames) < 2:
            self.report({"WARNING"}, "Active action has fewer than 2 keyframes")
            return {"CANCELLED"}
        active_span = active_frames[-1] - active_frames[0]

        if active_span < 1e-6:
            self.report({"WARNING"}, "Active action has zero-length span")
            return {"CANCELLED"}

        factor = ref_span / active_span
        pivot = active_frames[0]  # FIRST anchor

        _store_backup(fcurves, obj_name)
        rm.apply_scale(fcurves, pivot, factor)

        _tag_redraw(context)
        self.report(
            {"INFO"},
            f"Matched timing to '{ref_obj.name}' (×{factor:.3f})",
        )
        return {"FINISHED"}


# ---------------------------------------------------------------------------
# Class list
# ---------------------------------------------------------------------------

CLASSES: tuple[type, ...] = (
    AA_OT_p6_scale_keys,
    AA_OT_p6_offset_keys,
    AA_OT_p6_set_pivot,
    AA_OT_p6_time_warp,
    AA_OT_p6_reverse_keys,
    AA_OT_p6_bake_timing,
    AA_OT_p6_reset_timing,
    AA_OT_p6_match_timing,
)

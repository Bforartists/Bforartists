"""Key utility workflow operators (7 ops).

Covers: copy/paste keys with handles, frame offset, value offset, snap to
integer frames, mirror, protection-aware delete, and bake to range.
"""

from __future__ import annotations

import bpy
from bpy.props import FloatProperty
from bpy.types import Operator

from ..core import key_utils as ku
from ..core import key_metadata as meta
from ..core.context_utils import (
    in_anim_editor,
    iter_selected_keys,
    iter_visible_fcurves,
    key_identity,
)
from ..core.logging import get_logger

_log = get_logger(__name__)


class _AnimEditorOp(Operator):
    @classmethod
    def poll(cls, context):
        return in_anim_editor(context)


class ANIMASSIST_OT_copy_keys(_AnimEditorOp):
    bl_idname = "animassist.copy_selected_keys"
    bl_label = "Copy Selected Keys"
    # --- EXPLAINER HELP INTEGRATION ---
    bl_description = "Copy every selected keyframe (with handles) into the Anim Assist clipboard"
    bl_options = {"REGISTER"}

    def execute(self, context):
        n = ku.copy_selected_keys(context)
        self.report({"INFO"}, f"Copied {n} keys")
        return {"FINISHED"}


class ANIMASSIST_OT_paste_keys(_AnimEditorOp):
    bl_idname = "animassist.paste_keys_at_frame"
    bl_label = "Paste Keys at Frame"
    # --- EXPLAINER HELP INTEGRATION ---
    bl_description = "Paste the Anim Assist clipboard back onto the matching FCurves at the current frame plus offset"
    bl_options = {"REGISTER", "UNDO"}

    frame_offset: FloatProperty(  # type: ignore[valid-type]
        name="Frame Offset",
        description="Frames added to each pasted key relative to the current frame",
        default=0.0,
    )

    def execute(self, context):
        if ku.clipboard_size() == 0:
            self.report({"WARNING"}, "Clipboard empty")
            return {"CANCELLED"}
        n = ku.paste_keys(context, self.frame_offset)
        self.report({"INFO"}, f"Pasted {n} keys at offset +{self.frame_offset}")
        return {"FINISHED"}


class ANIMASSIST_OT_offset_selected_frames(_AnimEditorOp):
    bl_idname = "animassist.offset_selected_frames"
    bl_label = "Offset Selected Keys (Frame)"
    # --- EXPLAINER HELP INTEGRATION ---
    bl_description = "Shift every selected key along the time axis by the supplied frame delta"
    bl_options = {"REGISTER", "UNDO"}

    dx: FloatProperty(  # type: ignore[valid-type]
        name="Frame Delta",
        description="Number of frames to add to each selected key's time",
        default=1.0,
    )

    def execute(self, context):
        n = ku.offset_selected(context, dx=self.dx)
        self.report({"INFO"}, f"Offset {n} keys by {self.dx}")
        return {"FINISHED"}


class ANIMASSIST_OT_offset_selected_values(_AnimEditorOp):
    bl_idname = "animassist.offset_selected_values"
    bl_label = "Offset Selected Keys (Value)"
    # --- EXPLAINER HELP INTEGRATION ---
    bl_description = "Shift every selected key along the value axis by the supplied delta"
    bl_options = {"REGISTER", "UNDO"}

    dy: FloatProperty(  # type: ignore[valid-type]
        name="Value Delta",
        description="Amount to add to each selected key's value (co.y)",
        default=0.1,
    )

    def execute(self, context):
        n = ku.offset_selected(context, dy=self.dy)
        self.report({"INFO"}, f"Offset {n} keys by {self.dy}")
        return {"FINISHED"}


class ANIMASSIST_OT_snap_integer_frames(_AnimEditorOp):
    bl_idname = "animassist.snap_keys_to_integer_frames"
    bl_label = "Snap Selected Keys to Integer Frames"
    # --- EXPLAINER HELP INTEGRATION ---
    bl_description = "Round every selected key's frame to the nearest whole number"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        n = ku.snap_selected_to_integer_frames(context)
        self.report({"INFO"}, f"Snapped {n} keys")
        return {"FINISHED"}


class ANIMASSIST_OT_mirror_keys(_AnimEditorOp):
    bl_idname = "animassist.mirror_selected_keys"
    bl_label = "Mirror Selected Keys at Current Frame"
    # --- EXPLAINER HELP INTEGRATION ---
    bl_description = "Mirror selected keys in time around the current frame as the pivot"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        pivot = float(context.scene.frame_current)
        n = ku.mirror_selected(context, pivot)
        self.report({"INFO"}, f"Mirrored {n} keys around frame {pivot}")
        return {"FINISHED"}


class ANIMASSIST_OT_safe_delete_selected(_AnimEditorOp):
    bl_idname = "animassist.safe_delete_selected_keys"
    bl_label = "Safe Delete Selected Keys"
    bl_description = "Delete selected keys except those marked as protected"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        scene = context.scene
        victims: list[tuple[bpy.types.FCurve, int]] = []
        skipped = 0
        for obj, _a, fc, i, kp in iter_selected_keys(context):
            ident = key_identity(obj.name, fc, kp.co.x)
            if meta.is_protected(scene, ident):
                skipped += 1
                continue
            victims.append((fc, i))
        # Delete from the end so indices stay valid.
        victims.sort(key=lambda v: v[1], reverse=True)
        for fc, i in victims:
            try:
                fc.keyframe_points.remove(fc.keyframe_points[i], fast=True)
            except (IndexError, RuntimeError):
                _log.debug("safe delete skipped stale index %s", i)
        for _o, _a, fc in iter_visible_fcurves(context):
            fc.update()
        self.report({"INFO"}, f"Deleted {len(victims)} keys ({skipped} protected)")
        return {"FINISHED"}


classes: tuple[type, ...] = (
    ANIMASSIST_OT_copy_keys,
    ANIMASSIST_OT_paste_keys,
    ANIMASSIST_OT_offset_selected_frames,
    ANIMASSIST_OT_offset_selected_values,
    ANIMASSIST_OT_snap_integer_frames,
    ANIMASSIST_OT_mirror_keys,
    ANIMASSIST_OT_safe_delete_selected,
)

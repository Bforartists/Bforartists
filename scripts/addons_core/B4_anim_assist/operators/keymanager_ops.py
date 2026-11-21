"""Key Manager operators."""

from __future__ import annotations

import bpy
from bpy.props import BoolProperty, EnumProperty, IntProperty
from bpy.types import Operator

from ..core.fcurve_compat import get_fcurves


_FRAME_HALF: float = 0.5
_KEY_EPSILON: float = 1e-6


_INTERPOLATION_ITEMS: list[tuple[str, str, str]] = [
    ("CONSTANT", "Constant", "No interpolation"),
    ("LINEAR", "Linear", "Linear interpolation"),
    ("BEZIER", "Bezier", "Bezier interpolation"),
]

_KEY_TYPE_ITEMS: list[tuple[str, str, str]] = [
    ("KEYFRAME", "Keyframe", ""),
    ("BREAKDOWN", "Breakdown", ""),
    ("MOVING_HOLD", "Moving Hold", ""),
    ("EXTREME", "Extreme", ""),
    ("JITTER", "Jitter", ""),
]

_HANDLE_TYPE_ITEMS: list[tuple[str, str, str]] = [
    ("FREE", "Free", ""),
    ("ALIGNED", "Aligned", ""),
    ("VECTOR", "Vector", ""),
    ("AUTO", "Auto", ""),
    ("AUTO_CLAMPED", "Auto Clamped", ""),
]


def _object_fcurves(context: bpy.types.Context) -> list:
    obj = context.object
    if obj and obj.animation_data and obj.animation_data.action:
        return get_fcurves(obj.animation_data.action, anim_data=obj.animation_data)
    return []


def _visible_fcurves(context: bpy.types.Context) -> list:
    from ..core.context_utils import in_anim_editor, iter_visible_fcurves
    if in_anim_editor(context):
        return [fc for _obj, _action, fc in iter_visible_fcurves(context)]
    if getattr(getattr(context, "space_data", None), "type", "") == "NLA_EDITOR":
        return []
    return [fc for fc in _object_fcurves(context) if not fc.lock and not fc.hide]


class ANIMASSIST_OT_batch_interpolation(Operator):
    """Set interpolation only on selected, editable, visible keys."""

    bl_idname = "animassist.batch_interpolation"
    bl_label = "Batch Set Interpolation"
    bl_description = "Set all selected keyframes to the chosen interpolation type (Constant, Linear, or Bezier)"
    bl_options = {"REGISTER", "UNDO"}

    interp_type: EnumProperty(name="Interpolation", description="Interpolation to assign to selected editable keys", items=_INTERPOLATION_ITEMS, default="BEZIER")  # type: ignore[assignment]

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return context.object is not None

    def execute(self, context: bpy.types.Context):
        # ACCESS_GATE_HERE
        fcs = _visible_fcurves(context)
        if not fcs:
            self.report({"WARNING"}, "Show editable Action channels in this editor")
            return {"CANCELLED"}

        count = 0
        for fc in fcs:
            for kp in fc.keyframe_points:
                if not kp.select_control_point:
                    continue
                kp.interpolation = self.interp_type
                count += 1
            fc.update()

        if not count:
            self.report({"WARNING"}, "Select editable keys in this editor")
            return {"CANCELLED"}
        self.report({"INFO"}, f"{count} keys → {self.interp_type}")
        return {"FINISHED"}


class ANIMASSIST_OT_select_handles(Operator):
    bl_idname = "animassist.select_handles"
    bl_label = "Select Handles"
    bl_description = "Select the left, right, or both handles of selected keyframes"
    bl_options = {"REGISTER", "UNDO"}

    side: EnumProperty(  # type: ignore[assignment]
        name="Side",
        description="Which handles to select on each selected keyframe",
        items=[
            ("LEFT", "Left", "Select left handles"),
            ("RIGHT", "Right", "Select right handles"),
            ("BOTH", "Both", "Select both handles"),
        ],
        default="LEFT",
    )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        space = context.space_data
        return space is not None and space.type in {"GRAPH_EDITOR", "DOPESHEET_EDITOR"}

    def execute(self, context: bpy.types.Context):
        # ACCESS_GATE_HERE
        fcs = _visible_fcurves(context)
        if not fcs:
            self.report({"WARNING"}, "No FCurves available")
            return {"CANCELLED"}

        count = 0
        for fc in fcs:
            for kp in fc.keyframe_points:
                if not kp.select_control_point:
                    continue
                if self.side in {"LEFT", "BOTH"}:
                    kp.select_left_handle = True
                    count += 1
                if self.side in {"RIGHT", "BOTH"}:
                    kp.select_right_handle = True
                    count += 1

        if context.area:
            context.area.tag_redraw()
        self.report({"INFO"}, f"Selected {count} handles")
        return {"FINISHED"}


class ANIMASSIST_OT_set_key_type(Operator):
    bl_idname = "animassist.set_key_type"
    bl_label = "Set Key Type"
    bl_description = "Assign the chosen semantic key type to selected keyframes"
    bl_options = {"REGISTER", "UNDO"}

    key_type: EnumProperty(name="Key Type", description="Semantic type to assign to selected keys", items=_KEY_TYPE_ITEMS, default="KEYFRAME")  # type: ignore[assignment]

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return context.object is not None

    def execute(self, context: bpy.types.Context):
        # ACCESS_GATE_HERE
        count = 0
        for fc in _visible_fcurves(context):
            for kp in fc.keyframe_points:
                if kp.select_control_point:
                    kp.type = self.key_type
                    count += 1
        self.report({"INFO"}, f"{count} keys → {self.key_type}")
        return {"FINISHED"}


class ANIMASSIST_OT_set_handle_type(Operator):
    bl_idname = "animassist.set_handle_type"
    bl_label = "Set Handle Type"
    bl_description = "Set both Bezier handle types on selected keyframes"
    bl_options = {"REGISTER", "UNDO"}

    handle_type: EnumProperty(name="Handle Type", description="Bezier handle behavior to apply to selected keys", items=_HANDLE_TYPE_ITEMS, default="AUTO_CLAMPED")  # type: ignore[assignment]

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return context.object is not None

    def execute(self, context: bpy.types.Context):
        # ACCESS_GATE_HERE
        count = 0
        for fc in _visible_fcurves(context):
            for kp in fc.keyframe_points:
                if kp.select_control_point:
                    kp.handle_left_type = self.handle_type
                    kp.handle_right_type = self.handle_type
                    count += 1
            fc.update()
        self.report({"INFO"}, f"{count} keys handles → {self.handle_type}")
        return {"FINISHED"}


class ANIMASSIST_OT_select_by_key_type(Operator):
    bl_idname = "animassist.select_by_key_type"
    bl_label = "Select by Key Type"
    bl_description = "Select or deselect every keyframe of the chosen semantic type"
    bl_options = {"REGISTER", "UNDO"}

    key_type: EnumProperty(name="Key Type", description="Semantic key type to find", items=_KEY_TYPE_ITEMS, default="BREAKDOWN")  # type: ignore[assignment]
    deselect: BoolProperty(name="Deselect", description="Deselect matching keys instead of selecting them", default=False)  # type: ignore[assignment]

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return context.object is not None

    def execute(self, context: bpy.types.Context):
        # ACCESS_GATE_HERE
        count = 0
        for fc in _visible_fcurves(context):
            for kp in fc.keyframe_points:
                if kp.type == self.key_type:
                    kp.select_control_point = not self.deselect
                    count += 1

        verb = "Deselected" if self.deselect else "Selected"
        self.report({"INFO"}, f"{verb} {count} {self.key_type} keys")
        if context.area:
            context.area.tag_redraw()
        return {"FINISHED"}


class ANIMASSIST_OT_delete_by_key_type(Operator):
    bl_idname = "animassist.delete_by_key_type"
    bl_label = "Delete by Key Type"
    bl_description = "Delete every keyframe of the chosen semantic type"
    bl_options = {"REGISTER", "UNDO"}

    key_type: EnumProperty(name="Key Type", description="Semantic key type to delete", items=_KEY_TYPE_ITEMS, default="JITTER")  # type: ignore[assignment]

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return context.object is not None

    def execute(self, context: bpy.types.Context):
        # ACCESS_GATE_HERE
        total = 0
        for fc in _visible_fcurves(context):
            indices = [i for i, kp in enumerate(fc.keyframe_points) if kp.type == self.key_type]
            for i in reversed(indices):
                fc.keyframe_points.remove(fc.keyframe_points[i])
                total += 1
            if indices:
                fc.update()

        self.report({"INFO"}, f"Deleted {total} {self.key_type} keys")
        return {"FINISHED"}


class ANIMASSIST_OT_insert_frames(Operator):
    bl_idname = "animassist.insert_frames"
    bl_label = "Insert Frames"
    bl_description = "Make room in the animation by shifting later keyframes forward"
    bl_options = {"REGISTER", "UNDO"}

    count: IntProperty(name="Frame Count", description="Number of frames to insert", default=1, min=1, soft_max=100)  # type: ignore[assignment]
    mode: EnumProperty(  # type: ignore[assignment]
        name="Insert Mode",
        description="Where the inserted time begins",
        items=[
            ("AT_CURSOR", "At Cursor", "Insert at current frame"),
            ("BETWEEN_SELECTED", "Between Selected", "Insert after first selected key"),
        ],
        default="AT_CURSOR",
    )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return context.object is not None

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event):
        # ACCESS_GATE_HERE
        return self.execute(context)

    def execute(self, context: bpy.types.Context):
        # ACCESS_GATE_HERE
        fcs = _visible_fcurves(context)
        if not fcs:
            self.report({"WARNING"}, "No animation data")
            return {"CANCELLED"}

        if self.mode == "AT_CURSOR":
            threshold = float(context.scene.frame_current)
        else:
            sel_frames: list[float] = []
            for fc in fcs:
                for kp in fc.keyframe_points:
                    if kp.select_control_point:
                        sel_frames.append(kp.co[0])
            if len(sel_frames) < 2:
                self.report({"WARNING"}, "Need ≥ 2 selected keys for 'Between Selected'")
                return {"CANCELLED"}
            threshold = min(sel_frames)

        offset = float(self.count)
        moved = 0
        for fc in fcs:
            for kp in fc.keyframe_points:
                if kp.co[0] > threshold + _FRAME_HALF:
                    kp.co[0] += offset
                    kp.handle_left[0] += offset
                    kp.handle_right[0] += offset
                    moved += 1
            fc.update()

        self.report({"INFO"}, f"Inserted {self.count} frames — shifted {moved} keys")
        return {"FINISHED"}


# ---------------------------------------------------------------------------
# Move Keys  (Key repositioning tool)
# ---------------------------------------------------------------------------


class ANIMASSIST_OT_move_keys(Operator):
    bl_idname = "animassist.move_keys"
    bl_label = "Move Keys"
    bl_description = "Shift selected keyframes by a frame offset"
    bl_options = {"REGISTER", "UNDO"}

    offset: IntProperty(name="Frame Offset", default=1, soft_min=-100, soft_max=100)  # type: ignore[assignment]

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return context.object is not None

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event):
        # ACCESS_GATE_HERE
        return self.execute(context)

    def execute(self, context: bpy.types.Context):
        # ACCESS_GATE_HERE
        fcs = _visible_fcurves(context)
        if not fcs:
            self.report({"WARNING"}, "No animation data")
            return {"CANCELLED"}

        frame_offset = float(self.offset)
        moved = 0
        for fc in fcs:
            for kp in fc.keyframe_points:
                if kp.select_control_point:
                    kp.co[0] += frame_offset
                    kp.handle_left[0] += frame_offset
                    kp.handle_right[0] += frame_offset
                    moved += 1
            fc.update()

        self.report({"INFO"}, f"Moved {moved} keys by {self.offset} frames")
        return {"FINISHED"}


classes: list[type] = [
    ANIMASSIST_OT_batch_interpolation,
    ANIMASSIST_OT_select_handles,
    ANIMASSIST_OT_set_key_type,
    ANIMASSIST_OT_set_handle_type,
    ANIMASSIST_OT_select_by_key_type,
    ANIMASSIST_OT_delete_by_key_type,
    ANIMASSIST_OT_insert_frames,
    ANIMASSIST_OT_move_keys,
]

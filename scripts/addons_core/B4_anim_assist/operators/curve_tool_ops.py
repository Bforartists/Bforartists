"""Curve Tools operators + frame bookmarks."""

from __future__ import annotations

import bpy
from bpy.props import FloatProperty, IntProperty, StringProperty
from bpy.types import Operator

from ..core import curve_tools
from ..core.fcurve_compat import get_fcurves
from ..core.utils import KeyData, get_selected_indices


_DEFAULT_DRAG_SENSITIVITY: int = 200


def _addon_prefs(context: bpy.types.Context):
    from ..prefs import get_prefs
    return get_prefs(context)


def _drag_sensitivity(context: bpy.types.Context) -> int:
    p = _addon_prefs(context)
    return p.animassist_drag_sensitivity if p else _DEFAULT_DRAG_SENSITIVITY


def _editable_fcurves(context: bpy.types.Context) -> list:
    from ..core.context_utils import in_anim_editor, iter_visible_fcurves
    if in_anim_editor(context):
        return [fc for _obj, _action, fc in iter_visible_fcurves(context, only_selected=True)]
    if getattr(getattr(context, "space_data", None), "type", "") == "NLA_EDITOR":
        return []
    obj = context.object
    if obj and obj.animation_data and obj.animation_data.action:
        return [fc for fc in get_fcurves(obj.animation_data.action, anim_data=obj.animation_data)
                if not fc.lock and not fc.hide]
    return []


def _snapshot_keys(fcurve) -> list[KeyData]:
    return [
        KeyData(
            frame=kp.co[0],
            value=kp.co[1],
            selected=kp.select_control_point,
            handle_left=(kp.handle_left[0], kp.handle_left[1]),
            handle_right=(kp.handle_right[0], kp.handle_right[1]),
        )
        for kp in fcurve.keyframe_points
    ]


def _write_values(fcurve, indices: list[int], values: list[float]) -> None:
    kps = fcurve.keyframe_points
    for idx, val in zip(indices, values):
        kp = kps[idx]
        # Move handles with the key so FREE/ALIGNED/VECTOR tangents keep their shape.
        delta = val - kp.co[1]
        kp.co[1] = val
        kp.handle_left[1] += delta
        kp.handle_right[1] += delta
    fcurve.update()


# ---------------------------------------------------------------------------
# Blend Frame
# ---------------------------------------------------------------------------


class ANIMASSIST_OT_blend_frame(Operator):
    bl_idname = "animassist.blend_frame"
    bl_label = "Blend Frame"
    bl_description = "Blend selected keys toward the value at the reference frame"
    bl_options = {"REGISTER", "UNDO"}

    factor: FloatProperty(name="Factor", description="Strength of the blend toward the reference-frame value", default=0.0, soft_min=0.0, soft_max=1.0)  # type: ignore[assignment]

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        space = context.space_data
        return space is not None and space.type in {"GRAPH_EDITOR", "DOPESHEET_EDITOR", "VIEW_3D"}

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event):
        # ACCESS_GATE_HERE
        try:
            settings = context.scene.anim_assist
            ref_frame = settings.reference_frame or context.scene.frame_current
            self._initial_mouse_x = event.mouse_x
            self._sensitivity = _drag_sensitivity(context)

            fcurves = _editable_fcurves(context)
            if not fcurves:
                self.report({"WARNING"}, "No editable FCurves found")
                return {"CANCELLED"}

            self._data: list[dict] = []
            for fc in fcurves:
                keys = _snapshot_keys(fc)
                sel = get_selected_indices(keys)
                if not sel:
                    continue
                self._data.append(
                    {
                        "fc": fc,
                        "sel": sel,
                        "sel_keys": [keys[i] for i in sel],
                        "orig": [keys[i].value for i in sel],
                        "ref": fc.evaluate(ref_frame),
                    }
                )

            if not self._data:
                self.report({"WARNING"}, "No selected keyframes")
                return {"CANCELLED"}

            self.factor = 0.0
            context.window_manager.modal_handler_add(self)
            return {"RUNNING_MODAL"}
        except Exception as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}

    def modal(self, context: bpy.types.Context, event: bpy.types.Event):
        if event.type == "MOUSEMOVE":
            dx = event.mouse_x - self._initial_mouse_x
            self.factor = dx / self._sensitivity
            self._apply()
            if context.area:
                context.area.header_text_set(f"Blend Frame: {self.factor:.3f}")
                context.area.tag_redraw()

        elif event.type in {"LEFTMOUSE", "RET", "NUMPAD_ENTER"} and event.value == "PRESS":
            if context.area:
                context.area.header_text_set(None)
            return {"FINISHED"}

        elif event.type in {"RIGHTMOUSE", "ESC"} and event.value == "PRESS":
            self._restore()
            if context.area:
                context.area.header_text_set(None)
                context.area.tag_redraw()
            return {"CANCELLED"}

        return {"RUNNING_MODAL"}

    def _apply(self) -> None:
        for d in self._data:
            vals = curve_tools.blend_toward_value(d["sel_keys"], d["ref"], self.factor)
            _write_values(d["fc"], d["sel"], vals)

    def _restore(self) -> None:
        for d in self._data:
            _write_values(d["fc"], d["sel"], d["orig"])

    def execute(self, context: bpy.types.Context):
        # ACCESS_GATE_HERE
        ref = context.scene.anim_assist.reference_frame or context.scene.frame_current
        for fc in _editable_fcurves(context):
            keys = _snapshot_keys(fc)
            sel = get_selected_indices(keys)
            if not sel:
                continue
            vals = curve_tools.blend_toward_value([keys[i] for i in sel], fc.evaluate(ref), self.factor)
            _write_values(fc, sel, vals)
        return {"FINISHED"}


# ---------------------------------------------------------------------------
# Blend Offset
# ---------------------------------------------------------------------------


class ANIMASSIST_OT_blend_offset(Operator):
    bl_idname = "animassist.blend_offset"
    bl_label = "Blend Offset"
    bl_description = "Offset selected keys using the difference between their neighboring keys"
    bl_options = {"REGISTER", "UNDO"}

    factor: FloatProperty(name="Factor", description="Signed strength of the neighboring-key offset", default=0.0, soft_min=-1.0, soft_max=1.0)  # type: ignore[assignment]

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        space = context.space_data
        return space is not None and space.type in {"GRAPH_EDITOR", "DOPESHEET_EDITOR", "VIEW_3D"}

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event):
        # ACCESS_GATE_HERE
        try:
            self._initial_mouse_x = event.mouse_x
            self._sensitivity = _drag_sensitivity(context)

            fcurves = _editable_fcurves(context)
            if not fcurves:
                self.report({"WARNING"}, "No editable FCurves found")
                return {"CANCELLED"}

            self._data: list[dict] = []
            for fc in fcurves:
                keys = _snapshot_keys(fc)
                sel = get_selected_indices(keys)
                if not sel:
                    continue
                self._data.append({"fc": fc, "keys": keys, "sel": sel, "orig": [keys[i].value for i in sel]})

            if not self._data:
                self.report({"WARNING"}, "No selected keyframes")
                return {"CANCELLED"}

            self.factor = 0.0
            context.window_manager.modal_handler_add(self)
            return {"RUNNING_MODAL"}
        except Exception as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}

    def modal(self, context: bpy.types.Context, event: bpy.types.Event):
        if event.type == "MOUSEMOVE":
            dx = event.mouse_x - self._initial_mouse_x
            self.factor = dx / self._sensitivity
            self._apply()
            if context.area:
                context.area.header_text_set(f"Blend Offset: {self.factor:.3f}")
                context.area.tag_redraw()

        elif event.type in {"LEFTMOUSE", "RET", "NUMPAD_ENTER"} and event.value == "PRESS":
            if context.area:
                context.area.header_text_set(None)
            return {"FINISHED"}

        elif event.type in {"RIGHTMOUSE", "ESC"} and event.value == "PRESS":
            self._restore()
            if context.area:
                context.area.header_text_set(None)
                context.area.tag_redraw()
            return {"CANCELLED"}

        return {"RUNNING_MODAL"}

    def _apply(self) -> None:
        for d in self._data:
            offset = curve_tools.blend_offset(d["keys"], d["sel"], self.factor)
            _write_values(d["fc"], d["sel"], [v + offset for v in d["orig"]])

    def _restore(self) -> None:
        for d in self._data:
            _write_values(d["fc"], d["sel"], d["orig"])

    def execute(self, context: bpy.types.Context):
        # ACCESS_GATE_HERE
        for fc in _editable_fcurves(context):
            keys = _snapshot_keys(fc)
            sel = get_selected_indices(keys)
            if not sel:
                continue
            orig = [keys[i].value for i in sel]
            offset = curve_tools.blend_offset(keys, sel, self.factor)
            _write_values(fc, sel, [v + offset for v in orig])
        return {"FINISHED"}


# ---------------------------------------------------------------------------
# Ease To Ease
# ---------------------------------------------------------------------------


class ANIMASSIST_OT_ease_to_ease(Operator):
    bl_idname = "animassist.ease_to_ease"
    bl_label = "Ease To Ease"
    bl_description = "Blend selected keys from linear spacing toward a smooth ease-in/ease-out curve"
    bl_options = {"REGISTER", "UNDO"}

    factor: FloatProperty(name="Factor", description="Strength of the ease-in/ease-out shaping", default=0.0, soft_min=0.0, soft_max=1.0)  # type: ignore[assignment]

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        space = context.space_data
        return space is not None and space.type in {"GRAPH_EDITOR", "DOPESHEET_EDITOR", "VIEW_3D"}

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event):
        # ACCESS_GATE_HERE
        try:
            self._initial_mouse_x = event.mouse_x
            self._sensitivity = _drag_sensitivity(context)

            fcurves = _editable_fcurves(context)
            if not fcurves:
                self.report({"WARNING"}, "No editable FCurves found")
                return {"CANCELLED"}

            self._data: list[dict] = []
            for fc in fcurves:
                keys = _snapshot_keys(fc)
                sel = get_selected_indices(keys)
                if len(sel) < 2:
                    continue
                sel_keys = [keys[i] for i in sel]
                self._data.append({"fc": fc, "sel": sel, "sel_keys": sel_keys, "orig": [k.value for k in sel_keys]})

            if not self._data:
                self.report({"WARNING"}, "Need ≥ 2 selected keys per FCurve")
                return {"CANCELLED"}

            self.factor = 0.0
            context.window_manager.modal_handler_add(self)
            return {"RUNNING_MODAL"}
        except Exception as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}

    def modal(self, context: bpy.types.Context, event: bpy.types.Event):
        if event.type == "MOUSEMOVE":
            dx = event.mouse_x - self._initial_mouse_x
            self.factor = dx / self._sensitivity
            self._apply()
            if context.area:
                context.area.header_text_set(f"Ease To Ease: {self.factor:.3f}")
                context.area.tag_redraw()

        elif event.type in {"LEFTMOUSE", "RET", "NUMPAD_ENTER"} and event.value == "PRESS":
            if context.area:
                context.area.header_text_set(None)
            return {"FINISHED"}

        elif event.type in {"RIGHTMOUSE", "ESC"} and event.value == "PRESS":
            self._restore()
            if context.area:
                context.area.header_text_set(None)
                context.area.tag_redraw()
            return {"CANCELLED"}

        return {"RUNNING_MODAL"}

    def _apply(self) -> None:
        for d in self._data:
            vals = curve_tools.ease_to_ease(d["sel_keys"], self.factor)
            _write_values(d["fc"], d["sel"], vals)

    def _restore(self) -> None:
        for d in self._data:
            _write_values(d["fc"], d["sel"], d["orig"])

    def execute(self, context: bpy.types.Context):
        # ACCESS_GATE_HERE
        for fc in _editable_fcurves(context):
            keys = _snapshot_keys(fc)
            sel = get_selected_indices(keys)
            if len(sel) < 2:
                continue
            vals = curve_tools.ease_to_ease([keys[i] for i in sel], self.factor)
            _write_values(fc, sel, vals)
        return {"FINISHED"}


# ---------------------------------------------------------------------------
# Blend to Neighbor  (AnimAide "Tween Machine")
# ---------------------------------------------------------------------------


class ANIMASSIST_OT_blend_neighbor(Operator):
    bl_idname = "animassist.blend_neighbor"
    bl_label = "Blend to Neighbor"
    bl_description = "Blend selected keys toward the line between their unselected neighbors"
    bl_options = {"REGISTER", "UNDO"}

    factor: FloatProperty(name="Factor", description="Strength of the blend toward neighboring keys", default=0.0, soft_min=0.0, soft_max=1.0)  # type: ignore[assignment]

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        space = context.space_data
        return space is not None and space.type in {"GRAPH_EDITOR", "DOPESHEET_EDITOR", "VIEW_3D"}

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event):
        # ACCESS_GATE_HERE
        try:
            self._initial_mouse_x = event.mouse_x
            self._sensitivity = _drag_sensitivity(context)

            fcurves = _editable_fcurves(context)
            if not fcurves:
                self.report({"WARNING"}, "No editable FCurves found")
                return {"CANCELLED"}

            self._data: list[dict] = []
            for fc in fcurves:
                keys = _snapshot_keys(fc)
                sel = get_selected_indices(keys)
                if not sel:
                    continue
                self._data.append(
                    {
                        "fc": fc,
                        "keys": keys,
                        "sel": sel,
                        "orig": [keys[i].value for i in sel],
                    }
                )

            if not self._data:
                self.report({"WARNING"}, "No selected keyframes")
                return {"CANCELLED"}

            self.factor = 0.0
            context.window_manager.modal_handler_add(self)
            return {"RUNNING_MODAL"}
        except Exception as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}

    def modal(self, context: bpy.types.Context, event: bpy.types.Event):
        if event.type == "MOUSEMOVE":
            dx = event.mouse_x - self._initial_mouse_x
            self.factor = dx / self._sensitivity
            self._apply()
            if context.area:
                context.area.header_text_set(f"Blend to Neighbor: {self.factor:.3f}")
                context.area.tag_redraw()

        elif event.type in {"LEFTMOUSE", "RET", "NUMPAD_ENTER"} and event.value == "PRESS":
            if context.area:
                context.area.header_text_set(None)
            return {"FINISHED"}

        elif event.type in {"RIGHTMOUSE", "ESC"} and event.value == "PRESS":
            self._restore()
            if context.area:
                context.area.header_text_set(None)
                context.area.tag_redraw()
            return {"CANCELLED"}

        return {"RUNNING_MODAL"}

    def _apply(self) -> None:
        for d in self._data:
            vals = curve_tools.blend_to_neighbor(d["keys"], d["sel"], self.factor)
            _write_values(d["fc"], d["sel"], vals)

    def _restore(self) -> None:
        for d in self._data:
            _write_values(d["fc"], d["sel"], d["orig"])

    def execute(self, context: bpy.types.Context):
        # ACCESS_GATE_HERE
        for fc in _editable_fcurves(context):
            keys = _snapshot_keys(fc)
            sel = get_selected_indices(keys)
            if not sel:
                continue
            vals = curve_tools.blend_to_neighbor(keys, sel, self.factor)
            _write_values(fc, sel, vals)
        return {"FINISHED"}


# ---------------------------------------------------------------------------
# Push / Pull  (Value adjustment tool)
# ---------------------------------------------------------------------------


class ANIMASSIST_OT_push_pull(Operator):
    bl_idname = "animassist.push_pull"
    bl_label = "Push / Pull"
    bl_description = "Scale selected keys away from or toward the reference frame value"
    bl_options = {"REGISTER", "UNDO"}

    factor: FloatProperty(name="Factor", description="Amount to push away from or pull toward the reference value", default=0.0, soft_min=-1.0, soft_max=2.0)  # type: ignore[assignment]

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        space = context.space_data
        return space is not None and space.type in {"GRAPH_EDITOR", "DOPESHEET_EDITOR", "VIEW_3D"}

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event):
        # ACCESS_GATE_HERE
        try:
            settings = context.scene.anim_assist
            ref_frame = settings.reference_frame or context.scene.frame_current
            self._initial_mouse_x = event.mouse_x
            self._sensitivity = _drag_sensitivity(context)

            fcurves = _editable_fcurves(context)
            if not fcurves:
                self.report({"WARNING"}, "No editable FCurves found")
                return {"CANCELLED"}

            self._data: list[dict] = []
            for fc in fcurves:
                keys = _snapshot_keys(fc)
                sel = get_selected_indices(keys)
                if not sel:
                    continue
                self._data.append(
                    {
                        "fc": fc,
                        "sel": sel,
                        "sel_keys": [keys[i] for i in sel],
                        "orig": [keys[i].value for i in sel],
                        "ref": fc.evaluate(ref_frame),
                    }
                )

            if not self._data:
                self.report({"WARNING"}, "No selected keyframes")
                return {"CANCELLED"}

            self.factor = 0.0
            context.window_manager.modal_handler_add(self)
            return {"RUNNING_MODAL"}
        except Exception as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}

    def modal(self, context: bpy.types.Context, event: bpy.types.Event):
        if event.type == "MOUSEMOVE":
            dx = event.mouse_x - self._initial_mouse_x
            self.factor = dx / self._sensitivity
            self._apply()
            if context.area:
                context.area.header_text_set(f"Push/Pull: {self.factor:.3f}")
                context.area.tag_redraw()

        elif event.type in {"LEFTMOUSE", "RET", "NUMPAD_ENTER"} and event.value == "PRESS":
            if context.area:
                context.area.header_text_set(None)
            return {"FINISHED"}

        elif event.type in {"RIGHTMOUSE", "ESC"} and event.value == "PRESS":
            self._restore()
            if context.area:
                context.area.header_text_set(None)
                context.area.tag_redraw()
            return {"CANCELLED"}

        return {"RUNNING_MODAL"}

    def _apply(self) -> None:
        for d in self._data:
            vals = curve_tools.push_pull(d["sel_keys"], d["ref"], self.factor)
            _write_values(d["fc"], d["sel"], vals)

    def _restore(self) -> None:
        for d in self._data:
            _write_values(d["fc"], d["sel"], d["orig"])

    def execute(self, context: bpy.types.Context):
        # ACCESS_GATE_HERE
        ref = context.scene.anim_assist.reference_frame or context.scene.frame_current
        for fc in _editable_fcurves(context):
            keys = _snapshot_keys(fc)
            sel = get_selected_indices(keys)
            if not sel:
                continue
            vals = curve_tools.push_pull([keys[i] for i in sel], fc.evaluate(ref), self.factor)
            _write_values(fc, sel, vals)
        return {"FINISHED"}


# ---------------------------------------------------------------------------
# Smooth Keys  (Key smoothing tool)
# ---------------------------------------------------------------------------


class ANIMASSIST_OT_smooth_keys(Operator):
    bl_idname = "animassist.smooth_keys"
    bl_label = "Smooth Keys"
    bl_description = "Blend selected keys toward the average of their immediate neighbors"
    bl_options = {"REGISTER", "UNDO"}

    factor: FloatProperty(name="Factor", description="Strength of smoothing toward neighboring-key averages", default=0.0, soft_min=0.0, soft_max=1.0)  # type: ignore[assignment]

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        space = context.space_data
        return space is not None and space.type in {"GRAPH_EDITOR", "DOPESHEET_EDITOR", "VIEW_3D"}

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event):
        # ACCESS_GATE_HERE
        try:
            self._initial_mouse_x = event.mouse_x
            self._sensitivity = _drag_sensitivity(context)

            fcurves = _editable_fcurves(context)
            if not fcurves:
                self.report({"WARNING"}, "No editable FCurves found")
                return {"CANCELLED"}

            self._data: list[dict] = []
            for fc in fcurves:
                keys = _snapshot_keys(fc)
                sel = get_selected_indices(keys)
                if not sel:
                    continue
                self._data.append(
                    {
                        "fc": fc,
                        "keys": keys,
                        "sel": sel,
                        "orig": [keys[i].value for i in sel],
                    }
                )

            if not self._data:
                self.report({"WARNING"}, "No selected keyframes")
                return {"CANCELLED"}

            self.factor = 0.0
            context.window_manager.modal_handler_add(self)
            return {"RUNNING_MODAL"}
        except Exception as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}

    def modal(self, context: bpy.types.Context, event: bpy.types.Event):
        if event.type == "MOUSEMOVE":
            dx = event.mouse_x - self._initial_mouse_x
            self.factor = dx / self._sensitivity
            self._apply()
            if context.area:
                context.area.header_text_set(f"Smooth Keys: {self.factor:.3f}")
                context.area.tag_redraw()

        elif event.type in {"LEFTMOUSE", "RET", "NUMPAD_ENTER"} and event.value == "PRESS":
            if context.area:
                context.area.header_text_set(None)
            return {"FINISHED"}

        elif event.type in {"RIGHTMOUSE", "ESC"} and event.value == "PRESS":
            self._restore()
            if context.area:
                context.area.header_text_set(None)
                context.area.tag_redraw()
            return {"CANCELLED"}

        return {"RUNNING_MODAL"}

    def _apply(self) -> None:
        for d in self._data:
            vals = curve_tools.smooth_keys(d["keys"], d["sel"], self.factor)
            _write_values(d["fc"], d["sel"], vals)

    def _restore(self) -> None:
        for d in self._data:
            _write_values(d["fc"], d["sel"], d["orig"])

    def execute(self, context: bpy.types.Context):
        # ACCESS_GATE_HERE
        for fc in _editable_fcurves(context):
            keys = _snapshot_keys(fc)
            sel = get_selected_indices(keys)
            if not sel:
                continue
            vals = curve_tools.smooth_keys(keys, sel, self.factor)
            _write_values(fc, sel, vals)
        return {"FINISHED"}


# ---------------------------------------------------------------------------
# Reference Frame & Bookmarks  (unchanged)
# ---------------------------------------------------------------------------


class ANIMASSIST_OT_set_reference_frame(Operator):
    bl_idname = "animassist.set_reference_frame"
    bl_label = "Set Reference Frame"
    bl_description = "Use the current playhead frame as the reference for blend tools"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context: bpy.types.Context):
        # ACCESS_GATE_HERE
        s = context.scene.anim_assist
        s.reference_frame = context.scene.frame_current
        self.report({"INFO"}, f"Reference frame → {s.reference_frame}")
        return {"FINISHED"}


class ANIMASSIST_OT_add_bookmark(Operator):
    bl_idname = "animassist.add_bookmark"
    bl_label = "Add Frame Bookmark"
    bl_description = "Save the current reference frame as a named bookmark"
    bl_options = {"REGISTER", "UNDO"}

    name: StringProperty(name="Name", description="Display name for the new frame bookmark", default="Bookmark")  # type: ignore[assignment]

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event):
        # ACCESS_GATE_HERE
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context: bpy.types.Context):
        # ACCESS_GATE_HERE
        s = context.scene.anim_assist
        bm = s.bookmarks.add()
        bm.name = self.name
        bm.frame = s.reference_frame
        s.active_bookmark_index = len(s.bookmarks) - 1
        return {"FINISHED"}


class ANIMASSIST_OT_remove_bookmark(Operator):
    bl_idname = "animassist.remove_bookmark"
    bl_label = "Remove Frame Bookmark"
    bl_description = "Delete the active frame bookmark"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context: bpy.types.Context):
        # ACCESS_GATE_HERE
        s = context.scene.anim_assist
        idx = s.active_bookmark_index
        if 0 <= idx < len(s.bookmarks):
            s.bookmarks.remove(idx)
            s.active_bookmark_index = min(idx, max(0, len(s.bookmarks) - 1))
        return {"FINISHED"}


class ANIMASSIST_OT_recall_bookmark(Operator):
    bl_idname = "animassist.recall_bookmark"
    bl_label = "Recall Bookmark"
    bl_description = "Set the reference frame from a saved bookmark"
    bl_options = {"REGISTER", "UNDO"}

    index: IntProperty(name="Index", description="Stored bookmark index to recall", default=0)  # type: ignore[assignment]

    def execute(self, context: bpy.types.Context):
        # ACCESS_GATE_HERE
        s = context.scene.anim_assist
        if 0 <= self.index < len(s.bookmarks):
            s.reference_frame = s.bookmarks[self.index].frame
            s.active_bookmark_index = self.index
        return {"FINISHED"}


classes: list[type] = [
    ANIMASSIST_OT_blend_frame,
    ANIMASSIST_OT_blend_offset,
    ANIMASSIST_OT_ease_to_ease,
    ANIMASSIST_OT_blend_neighbor,
    ANIMASSIST_OT_push_pull,
    ANIMASSIST_OT_smooth_keys,
    ANIMASSIST_OT_set_reference_frame,
    ANIMASSIST_OT_add_bookmark,
    ANIMASSIST_OT_remove_bookmark,
    ANIMASSIST_OT_recall_bookmark,


]

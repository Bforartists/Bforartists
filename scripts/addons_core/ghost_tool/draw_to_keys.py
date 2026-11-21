"""draw_to_keys.py — Draw to Keys (design §8 decision 15): annotation strokes to location keys.

Reads annotation strokes the way the Annotate tool stores them in Bforartists 5.1.2 (plan Task G1):
``scene.annotation`` is a ``bpy.types.Annotation``; the active layer is ``layers[layers.active_index]``
(``layers.active_note`` is only its name, a string); a layer's
frame for the playhead is the last frame at or before it; each stroke's ``points[i].co`` is a world-space
point when ``display_mode`` is '3DSPACE' (Surface or 3D Cursor placement). A View-placed stroke in the 3D
viewport is screen-locked ('2DSPACE'), has no depth, and is refused. The geometry is in
draw_to_keys_math (no bpy).
"""

from __future__ import annotations

from typing import Optional

import bpy
from mathutils import Vector

from . import draw_to_keys_math as dm
from . import motion_paths as mp
from .session_state import SessionState
from .target_binding import object_reason, slot_handle, ensure_bone_uid, find_bone
from .utils import get_fcurves_from_action, scene_sampling, tag_viewport_redraw


def _frame_at(layer, frame_current: int):
    """The annotation frame shown at ``frame_current``: the last one at or before it (frames hold), or None
    before the first frame (nothing is drawn there yet). Always computed from the frame list:
    ``layer.active_frame`` is None headless and is not checked against the playhead (review 976236d6)."""
    frames = sorted(layer.frames, key=lambda fr: fr.frame_number)
    if not frames:
        return None
    held = [fr for fr in frames if fr.frame_number <= frame_current]
    return held[-1] if held else None


def _active_layer_frame(scene):
    """The active annotation layer's frame at the playhead, or None (no annotation, hidden layer, or before
    its first frame). Reading and clearing both go through here, so they always see the same strokes."""
    annotation = getattr(scene, "annotation", None)
    layer: Optional[bpy.types.AnnotationLayer] = None
    if annotation is not None and 0 <= annotation.layers.active_index < len(annotation.layers):
        layer = annotation.layers[annotation.layers.active_index]
    if layer is None or layer.annotation_hide:
        return None
    return _frame_at(layer, scene.frame_current)


def annotation_strokes(scene) -> tuple[list[list[Vector]], int]:
    """(3D strokes of the active annotation layer at the playhead, number of strokes refused for not being
    in 3D space). Hidden layers and strokes with fewer than two points are skipped."""
    frame = _active_layer_frame(scene)
    if frame is None:
        return [], 0
    strokes, refused = [], 0
    for stroke in frame.strokes:
        if stroke.display_mode != '3DSPACE':
            refused += 1
            continue
        if _usable(stroke):
            strokes.append([Vector(p.co) for p in stroke.points])
    return strokes, refused


def _usable(stroke) -> bool:
    """A stroke Draw to Keys reads: in 3D space and at least two points."""
    return stroke.display_mode == '3DSPACE' and len(stroke.points) >= 2


def clear_annotation_frame(scene) -> int:
    """Remove the strokes Draw to Keys read (the active layer's frame at the playhead), and only those: a dot
    or any stroke it skipped stays (review 07547b99). Returns how many were removed."""
    frame = _active_layer_frame(scene)   # a hidden layer is never read, so it is never cleared (review ec38136d)
    if frame is None:
        return 0
    used = [stroke for stroke in frame.strokes if _usable(stroke)]
    for stroke in used:
        frame.strokes.remove(stroke)
    return len(used)


def _target(context):
    """(object, bone name) Draw to Keys keys: the active pose bone in Pose mode, else the active object."""
    if context.mode == 'POSE' and getattr(context, "active_pose_bone", None) is not None:
        pb = context.active_pose_bone
        return pb.id_data, pb.name
    obj = getattr(context, "active_object", None)
    return (obj, "") if obj is not None else (None, "")


def _key_interpolation(obj, data_path: str, index: int, frame: float, interpolation: str) -> None:
    action = obj.animation_data.action if obj.animation_data else None
    for fc in get_fcurves_from_action(action, obj) if action else ():
        if fc.data_path == data_path and fc.array_index == index:
            for key in fc.keyframe_points:
                if abs(key.co.x - frame) < 1e-4:
                    key.interpolation = interpolation
            return


AXES = (('X', "X", "Key location X"), ('Y', "Y", "Key location Y"), ('Z', "Z", "Key location Z"))


class GHOST_OT_paths_draw_to_keys(bpy.types.Operator):
    """Turn annotation strokes into location keys: the longest stroke is the path, every other stroke a timing
    dash; each crossing becomes a key at Start, Start + Step, ... on the chosen axes"""

    bl_idname = "ghost_tool.paths_draw_to_keys"
    bl_label = "Draw to Keys"
    bl_options = {'REGISTER', 'UNDO'}

    axes: bpy.props.EnumProperty(
        name="Axes", description="Location axes to key", items=AXES, options={'ENUM_FLAG'}, default={'X', 'Y', 'Z'},
    )  # type: ignore[assignment]
    use_current_frame: bpy.props.BoolProperty(
        name="Start at Playhead", description="Start at the current frame instead of the Start field", default=True,
    )  # type: ignore[assignment]
    start_frame: bpy.props.IntProperty(
        name="Start", description="Frame of the first crossing's key", default=1,
    )  # type: ignore[assignment]
    frame_step: bpy.props.IntProperty(
        name="Step", description="Frames between the keys of neighbouring crossings", default=4, min=1,
    )  # type: ignore[assignment]
    interpolation: bpy.props.EnumProperty(
        name="Interpolation", description="Interpolation of the new keys",
        items=[('CONSTANT', "Constant", "Hold each key until the next"),
               ('LINEAR', "Linear", "Straight lines between keys"),
               ('BEZIER', "Bezier", "Smooth curves between keys"),
               ('SCENE', "Preferences", "Use the interpolation set in the preferences")],
        default='BEZIER',
    )  # type: ignore[assignment]
    write_stroke_value: bpy.props.BoolProperty(
        name="Stroke Value", description="Also key a stroke_value custom property with the distance along the path",
        default=False,
    )  # type: ignore[assignment]
    crossing_tolerance: bpy.props.FloatProperty(
        name="Tolerance", description="How near a dash must come to the path, as a fraction of the path length",
        default=0.02, min=0.0001, max=0.5,
    )  # type: ignore[assignment]
    clear_annotations_after: bpy.props.BoolProperty(
        name="Clear Strokes", description="Remove the strokes after keying", default=False,
    )  # type: ignore[assignment]

    @classmethod
    def poll(cls, context):
        obj, _bone = _target(context)
        if obj is None:
            cls.poll_message_set("Select an object, or a bone in Pose mode")
            return False
        if not annotation_strokes(context.scene)[0]:
            cls.poll_message_set("Draw a path and timing dashes with the Annotate tool (Surface or 3D Cursor)")
            return False
        return SessionState.poll_available(cls)

    def invoke(self, context, event):
        obj, bone = _target(context)
        original_bone = obj.data.bones.get(bone) if bone else None
        bone_uid = ensure_bone_uid(obj, original_bone) if original_bone is not None else ''
        self._dialog_target = (context.scene, obj, bone_uid, bone or '')
        self._dialog_action = obj.animation_data.action if obj.animation_data else None
        self._dialog_slot = slot_handle(obj) if obj.animation_data else 0
        return context.window_manager.invoke_props_dialog(self, width=280)

    def execute(self, context):
        scene = context.scene
        if not SessionState.available(self):
            self.report({'WARNING'}, 'Finish or cancel the current Ghost Tool gesture first')
            return {'CANCELLED'}
        obj, bone = _target(context)
        target = getattr(self, '_dialog_target', None)
        if target is not None:
            source_scene, obj, bone_uid, bone_name = target
            reason = object_reason(scene, obj, source_scene)
            if not reason:
                action = obj.animation_data.action if obj.animation_data else None
                slot = slot_handle(obj) if obj.animation_data else 0
                if action != self._dialog_action or slot != self._dialog_slot:
                    reason = 'Original animation assignment changed; open Draw to Keys again'
                original = find_bone(obj, bone_uid, bone_name) if bone_uid else None
                bone = original.name if original is not None else ''
                if bone_uid and original is None:
                    reason = 'Original bone is missing or ambiguous'
            if reason:
                self.report({'WARNING'}, reason)
                return {'CANCELLED'}
        if obj is None or not self.axes:
            self.report({'WARNING'}, "Nothing to key: pick a target and at least one axis")
            return {'CANCELLED'}
        if bone and obj.pose.bones[bone].bone.use_connect:
            self.report({'WARNING'}, f"{bone} is connected to its parent: its location cannot move")
            return {'CANCELLED'}
        strokes, refused = annotation_strokes(scene)
        if refused:
            self.report({'WARNING'}, f"{refused} stroke(s) were drawn with View placement and have no depth; "
                                     "redraw them with Placement Surface or 3D Cursor")
            return {'CANCELLED'}
        index = dm.longest_stroke(strokes)
        path = [tuple(p) for p in strokes[index]] if index >= 0 else []
        dashes = [[tuple(p) for p in s] for i, s in enumerate(strokes) if i != index]
        hits = dm.crossings(path, dashes, self.crossing_tolerance)
        if len(hits) < 2:
            self.report({'WARNING'}, f"Found {len(hits)} crossing(s): draw at least two dashes across the path")
            return {'CANCELLED'}
        start = scene.frame_current if self.use_current_frame else self.start_frame
        frames = dm.frames_from_crossings(len(hits), start, self.frame_step)
        length = dm.polyline_length(path)
        axes = [i for i, name in enumerate("XYZ") if name in self.axes]
        holder = obj.pose.bones[bone] if bone else obj
        # This operation writes animation, so return to the newly keyed pose.
        with scene_sampling(scene, preserve_pose=False):
            for (t, point), frame in zip(hits, frames):
                scene.frame_set(int(frame))   # the parent's pose at this key's frame
                data_path, to_world, offset, _current = mp.location_world_map(obj, bone)
                local = to_world.inverted() @ Vector(point) - offset
                for axis in axes:
                    holder.location[axis] = local[axis]
                    holder.keyframe_insert("location", index=axis, frame=frame)
                    if self.interpolation != 'SCENE':
                        _key_interpolation(obj, data_path, axis, frame, self.interpolation)
                if self.write_stroke_value:
                    holder["stroke_value"] = t * length
                    holder.keyframe_insert('["stroke_value"]', frame=frame)
        if self.clear_annotations_after:
            clear_annotation_frame(scene)
        mp.mark_dirty_for_id(obj)   # pinned paths of this object (and its followers) show the new motion
        if scene.ghost_tool.paths_enabled:
            mp.refresh_paths(context)
        tag_viewport_redraw(context)
        self.report({'INFO'}, f"Keyed {len(hits)} crossings at frames {frames[0]:g} to {frames[-1]:g}")
        return {'FINISHED'}


CLASSES: tuple[type, ...] = (GHOST_OT_paths_draw_to_keys,)


def register() -> None:
    for cls in CLASSES:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(CLASSES):
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError:
            pass

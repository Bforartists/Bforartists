# SPDX-License-Identifier: GPL-2.0-or-later

"""
Copy Global Transform

Simple add-on for copying world-space transforms.

It's called "global" to avoid confusion with the Blender World data-block.
"""

bl_info = {
    "name": "Copy Global Transform",
    "author": "Sybren A. Stüvel",
    "version": (2, 0),
    "blender": (3, 1, 0),
    "location": "N-panel in the 3D Viewport",
    "category": "Animation",
    "support": 'OFFICIAL',
    "doc_url": "{BLENDER_MANUAL_URL}/addons/animation/copy_global_transform.html",
}

import ast
from typing import Iterable, Optional, Union, Any

import bpy
from bpy.types import Context, Object, Operator, Panel, PoseBone
from mathutils import Matrix


class AutoKeying:
    """Auto-keying support.

    Based on Rigify code by Alexander Gavrilov.
    """

    @classmethod
    def keying_options(cls, context: Context) -> set[str]:
        """Retrieve the general keyframing options from user preferences."""

        prefs = context.preferences
        ts = context.scene.tool_settings
        options = set()

        if prefs.edit.use_visual_keying:
            options.add('INSERTKEY_VISUAL')
        if prefs.edit.use_keyframe_insert_needed:
            options.add('INSERTKEY_NEEDED')
        if prefs.edit.use_insertkey_xyz_to_rgb:
            options.add('INSERTKEY_XYZ_TO_RGB')
        if ts.use_keyframe_cycle_aware:
            options.add('INSERTKEY_CYCLE_AWARE')
        return options

    @classmethod
    def autokeying_options(cls, context: Context) -> Optional[set[str]]:
        """Retrieve the Auto Keyframe options, or None if disabled."""

        ts = context.scene.tool_settings

        if not ts.use_keyframe_insert_auto:
            return None

        if ts.use_keyframe_insert_keyingset:
            # No support for keying sets (yet).
            return None

        prefs = context.preferences
        options = cls.keying_options(context)

        if prefs.edit.use_keyframe_insert_available:
            options.add('INSERTKEY_AVAILABLE')
        if ts.auto_keying_mode == 'REPLACE_KEYS':
            options.add('INSERTKEY_REPLACE')
        return options

    @staticmethod
    def get_4d_rotlock(bone: PoseBone) -> Iterable[bool]:
        "Retrieve the lock status for 4D rotation."
        if bone.lock_rotations_4d:
            return [bone.lock_rotation_w, *bone.lock_rotation]
        else:
            return [all(bone.lock_rotation)] * 4

    @staticmethod
    def keyframe_channels(
        target: Union[Object, PoseBone],
        options: set[str],
        data_path: str,
        group: str,
        locks: Iterable[bool],
    ) -> None:
        if all(locks):
            return

        if not any(locks):
            target.keyframe_insert(data_path, group=group, options=options)
            return

        for index, lock in enumerate(locks):
            if lock:
                continue
            target.keyframe_insert(data_path, index=index, group=group, options=options)

    @classmethod
    def key_transformation(
        cls,
        target: Union[Object, PoseBone],
        options: set[str],
    ) -> None:
        """Keyframe transformation properties, avoiding keying locked channels."""

        is_bone = isinstance(target, PoseBone)
        if is_bone:
            group = target.name
        else:
            group = "Object Transforms"

        def keyframe(data_path: str, locks: Iterable[bool]) -> None:
            cls.keyframe_channels(target, options, data_path, group, locks)

        if not (is_bone and target.bone.use_connect):
            keyframe("location", target.lock_location)

        if target.rotation_mode == 'QUATERNION':
            keyframe("rotation_quaternion", cls.get_4d_rotlock(target))
        elif target.rotation_mode == 'AXIS_ANGLE':
            keyframe("rotation_axis_angle", cls.get_4d_rotlock(target))
        else:
            keyframe("rotation_euler", target.lock_rotation)

        keyframe("scale", target.lock_scale)

    @classmethod
    def autokey_transformation(cls, context: Context, target: Union[Object, PoseBone]) -> None:
        """Auto-key transformation properties."""

        options = cls.autokeying_options(context)
        if options is None:
            return
        cls.key_transformation(target, options)


def get_matrix(context: Context) -> Matrix:
    bone = context.active_pose_bone
    if bone:
        # Convert matrix to world space
        arm = context.active_object
        mat = arm.matrix_world @ bone.matrix
    else:
        mat = context.active_object.matrix_world

    return mat


def set_matrix(context: Context, mat: Matrix) -> None:
    bone = context.active_pose_bone
    if bone:
        # Convert matrix to local space
        arm_eval = context.active_object.evaluated_get(context.view_layer.depsgraph)
        bone.matrix = arm_eval.matrix_world.inverted() @ mat
        AutoKeying.autokey_transformation(context, bone)
    else:
        context.active_object.matrix_world = mat
        AutoKeying.autokey_transformation(context, context.active_object)


def _selected_keyframes(context: Context) -> list[float]:
    """Return the list of frame numbers that have a selected key.

    Only keys on the active bone/object are considered.
    """
    bone = context.active_pose_bone
    if bone:
        return _selected_keyframes_for_bone(context.active_object, bone)
    return _selected_keyframes_for_object(context.active_object)


def _selected_keyframes_for_bone(object: Object, bone: PoseBone) -> list[float]:
    """Return the list of frame numbers that have a selected key.

    Only keys on the given pose bone are considered.
    """
    name = bpy.utils.escape_identifier(bone.name)
    return _selected_keyframes_in_action(object, f'pose.bones["{name}"].')


def _selected_keyframes_for_object(object: Object) -> list[float]:
    """Return the list of frame numbers that have a selected key.

    Only keys on the given object are considered.
    """
    return _selected_keyframes_in_action(object, "")


def _selected_keyframes_in_action(object: Object, rna_path_prefix: str) -> list[float]:
    """Return the list of frame numbers that have a selected key.

    Only keys on the given object's Action on FCurves starting with rna_path_prefix are considered.
    """

    action = object.animation_data and object.animation_data.action
    if action is None:
        return []

    keyframes = set()
    for fcurve in action.fcurves:
        if not fcurve.data_path.startswith(rna_path_prefix):
            continue

        for kp in fcurve.keyframe_points:
            if not kp.select_control_point:
                continue
            keyframes.add(kp.co.x)
    return sorted(keyframes)


class OBJECT_OT_copy_global_transform(Operator):
    bl_idname = "object.copy_global_transform"
    bl_label = "Copy Global Transform"
    bl_description = (
        "Copies the matrix of the currently active object or pose bone to the clipboard. Uses world-space matrices"
    )
    # This operator cannot be un-done because it manipulates data outside Blender.
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context: Context) -> bool:
        return bool(context.active_pose_bone) or bool(context.active_object)

    def execute(self, context: Context) -> set[str]:
        mat = get_matrix(context)
        rows = [f"    {tuple(row)!r}," for row in mat]
        as_string = "\n".join(rows)
        context.window_manager.clipboard = f"Matrix((\n{as_string}\n))"
        return {'FINISHED'}


class OBJECT_OT_paste_transform(Operator):
    bl_idname = "object.paste_transform"
    bl_label = "Paste Global Transform"
    bl_description = (
        "Pastes the matrix from the clipboard to the currently active pose bone or object. Uses world-space matrices"
    )
    bl_options = {'REGISTER', 'UNDO'}

    _method_items = [
        (
            'CURRENT',
            "Current Transform",
            "Paste onto the current values only, only manipulating the animation data if auto-keying is enabled",
        ),
        (
            'EXISTING_KEYS',
            "Selected Keys",
            "Paste onto frames that have a selected key, potentially creating new keys on those frames",
        ),
        (
            'BAKE',
            "Bake on Key Range",
            "Paste onto all frames between the first and last selected key, creating new keyframes if necessary",
        ),
    ]
    method: bpy.props.EnumProperty(  # type: ignore
        items=_method_items,
        name="Paste Method",
        description="Update the current transform, selected keyframes, or even create new keys",
    )
    bake_step: bpy.props.IntProperty(  # type: ignore
        name="Frame Step",
        description="Only used for baking. Step=1 creates a key on every frame, step=2 bakes on 2s, etc",
        min=1,
        soft_min=1,
        soft_max=5,
    )

    @classmethod
    def poll(cls, context: Context) -> bool:
        if not context.active_pose_bone and not context.active_object:
            cls.poll_message_set("Select an object or pose bone")
            return False
        if not context.window_manager.clipboard.startswith("Matrix("):
            cls.poll_message_set("Clipboard does not contain a valid matrix")
            return False
        return True

    @staticmethod
    def parse_print_m4(value: str) -> Optional[Matrix]:
        """Parse output from Blender's print_m4() function.

        Expects four lines of space-separated floats.
        """

        lines = value.strip().splitlines()
        if len(lines) != 4:
            return None

        floats = tuple(tuple(float(item) for item in line.split()) for line in lines)
        return Matrix(floats)

    def execute(self, context: Context) -> set[str]:
        clipboard = context.window_manager.clipboard
        if clipboard.startswith("Matrix"):
            mat = Matrix(ast.literal_eval(clipboard[6:]))
        else:
            mat = self.parse_print_m4(clipboard)

        if mat is None:
            self.report({'ERROR'}, "Clipboard does not contain a valid matrix")
            return {'CANCELLED'}

        applicator = {
            'CURRENT': self._paste_current,
            'EXISTING_KEYS': self._paste_existing_keys,
            'BAKE': self._paste_bake,
        }[self.method]
        return applicator(context, mat)

    @staticmethod
    def _paste_current(context: Context, matrix: Matrix) -> set[str]:
        set_matrix(context, matrix)
        return {'FINISHED'}

    def _paste_existing_keys(self, context: Context, matrix: Matrix) -> set[str]:
        if not context.scene.tool_settings.use_keyframe_insert_auto:
            self.report({'ERROR'}, "This mode requires auto-keying to work properly")
            return {'CANCELLED'}

        frame_numbers = _selected_keyframes(context)
        if not frame_numbers:
            self.report({'WARNING'}, "No selected frames found")
            return {'CANCELLED'}

        self._paste_on_frames(context, frame_numbers, matrix)
        return {'FINISHED'}

    def _paste_bake(self, context: Context, matrix: Matrix) -> set[str]:
        if not context.scene.tool_settings.use_keyframe_insert_auto:
            self.report({'ERROR'}, "This mode requires auto-keying to work properly")
            return {'CANCELLED'}

        bake_step = max(1, self.bake_step)
        # Put the clamped bake step back into RNA for the redo panel.
        self.bake_step = bake_step

        frame_start, frame_end = self._determine_bake_range(context)
        frame_range = range(round(frame_start), round(frame_end) + bake_step, bake_step)
        self._paste_on_frames(context, frame_range, matrix)
        return {'FINISHED'}

    def _determine_bake_range(self, context: Context) -> tuple[float, float]:
        frame_numbers = _selected_keyframes(context)
        if frame_numbers:
            # Note that these could be the same frame, if len(frame_numbers) == 1:
            return frame_numbers[0], frame_numbers[-1]

        if context.scene.use_preview_range:
            self.report({'INFO'}, "No selected keys, pasting over preview range")
            return context.scene.frame_preview_start, context.scene.frame_preview_end

        self.report({'INFO'}, "No selected keys, pasting over scene range")
        return context.scene.frame_start, context.scene.frame_end

    def _paste_on_frames(self, context: Context, frame_numbers: Iterable[float], matrix: Matrix) -> None:
        current_frame = context.scene.frame_current_final
        try:
            for frame in frame_numbers:
                context.scene.frame_set(int(frame), subframe=frame % 1.0)
                set_matrix(context, matrix)
        finally:
            context.scene.frame_set(int(current_frame), subframe=current_frame % 1.0)


class VIEW3D_PT_copy_global_transform(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Animation"
    bl_label = "Global Transform"

    def draw(self, context: Context) -> None:
        layout = self.layout

        # No need to put "Global Transform" in the operator text, given that it's already in the panel title.
        layout.operator("object.copy_global_transform", text="Copy", icon='COPYDOWN')

        paste_col = layout.column(align=True)
        paste_col.operator("object.paste_transform", text="Paste", icon='PASTEDOWN').method = 'CURRENT'
        wants_autokey_col = paste_col.column(align=True)
        has_autokey = context.scene.tool_settings.use_keyframe_insert_auto
        wants_autokey_col.enabled = has_autokey
        if not has_autokey:
            wants_autokey_col.label(text="These require auto-key:")

        wants_autokey_col.operator(
            "object.paste_transform",
            text="Paste to Selected Keys",
            icon='PASTEDOWN',
        ).method = 'EXISTING_KEYS'
        wants_autokey_col.operator(
            "object.paste_transform",
            text="Paste and Bake",
            icon='PASTEDOWN',
        ).method = 'BAKE'


### Messagebus subscription to monitor changes & refresh panels.
_msgbus_owner = object()


def _refresh_3d_panels():
    refresh_area_types = {'VIEW_3D'}
    for win in bpy.context.window_manager.windows:
        for area in win.screen.areas:
            if area.type not in refresh_area_types:
                continue
            area.tag_redraw()


classes = (
    OBJECT_OT_copy_global_transform,
    OBJECT_OT_paste_transform,
    VIEW3D_PT_copy_global_transform,
)
_register, _unregister = bpy.utils.register_classes_factory(classes)


def _register_message_bus() -> None:
    bpy.msgbus.subscribe_rna(
        key=(bpy.types.ToolSettings, "use_keyframe_insert_auto"),
        owner=_msgbus_owner,
        args=(),
        notify=_refresh_3d_panels,
        options={'PERSISTENT'},
    )


def _unregister_message_bus() -> None:
    bpy.msgbus.clear_by_owner(_msgbus_owner)


@bpy.app.handlers.persistent  # type: ignore
def _on_blendfile_load_post(none: Any, other_none: Any) -> None:
    # The parameters are required, but both are None.
    _register_message_bus()


def register():
    _register()
    bpy.app.handlers.load_post.append(_on_blendfile_load_post)


def unregister():
    _unregister()
    _unregister_message_bus()
    bpy.app.handlers.load_post.remove(_on_blendfile_load_post)

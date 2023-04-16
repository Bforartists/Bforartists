# SPDX-License-Identifier: GPL-2.0-or-later

"""
Copy Global Transform

Simple add-on for copying world-space transforms.

It's called "global" to avoid confusion with the Blender World data-block.
"""

bl_info = {
    "name": "Copy Global Transform",
    "author": "Sybren A. Stüvel",
    "version": (2, 1),
    "blender": (3, 5, 0),
    "location": "N-panel in the 3D Viewport",
    "category": "Animation",
    "support": 'OFFICIAL',
    "doc_url": "{BLENDER_MANUAL_URL}/addons/animation/copy_global_transform.html",
    "tracker_url": "https://projects.blender.org/blender/blender-addons/issues",
}

import ast
from typing import Iterable, Optional, Union, Any

import bpy
from bpy.types import Context, Object, Operator, Panel, PoseBone, UILayout
from mathutils import Matrix


_axis_enum_items = [
    ("x", "X", "", 1),
    ("y", "Y", "", 2),
    ("z", "Z", "", 3),
]


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


class UnableToMirrorError(Exception):
    """Raised when mirroring is enabled but no mirror object/bone is set."""


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

    use_mirror: bpy.props.BoolProperty(  # type: ignore
        name="Mirror Transform",
        description="When pasting, mirror the transform relative to a specific object or bone",
        default=False,
    )

    mirror_axis_loc: bpy.props.EnumProperty(  # type: ignore
        items=_axis_enum_items,
        name="Location Axis",
        description="Coordinate axis used to mirror the location part of the transform",
        default='x',
    )
    mirror_axis_rot: bpy.props.EnumProperty(  # type: ignore
        items=_axis_enum_items,
        name="Rotation Axis",
        description="Coordinate axis used to mirror the rotation part of the transform",
        default='z',
    )

    @classmethod
    def poll(cls, context: Context) -> bool:
        if not context.active_pose_bone and not context.active_object:
            cls.poll_message_set("Select an object or pose bone")
            return False

        clipboard = context.window_manager.clipboard.strip()
        if not (clipboard.startswith("Matrix(") or clipboard.startswith("<Matrix 4x4")):
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

    @staticmethod
    def parse_repr_m4(value: str) -> Optional[Matrix]:
        """Four lines of (a, b, c, d) floats."""

        lines = value.strip().splitlines()
        if len(lines) != 4:
            return None

        floats = tuple(tuple(float(item.strip()) for item in line.strip()[1:-1].split(',')) for line in lines)
        return Matrix(floats)

    def execute(self, context: Context) -> set[str]:
        clipboard = context.window_manager.clipboard.strip()
        if clipboard.startswith("Matrix"):
            mat = Matrix(ast.literal_eval(clipboard[6:]))
        elif clipboard.startswith("<Matrix 4x4"):
            mat = self.parse_repr_m4(clipboard[12:-1])
        else:
            mat = self.parse_print_m4(clipboard)

        if mat is None:
            self.report({'ERROR'}, "Clipboard does not contain a valid matrix")
            return {'CANCELLED'}

        try:
            mat = self._maybe_mirror(context, mat)
        except UnableToMirrorError:
            self.report({'ERROR'}, "Unable to mirror, no mirror object/bone configured")
            return {'CANCELLED'}

        applicator = {
            'CURRENT': self._paste_current,
            'EXISTING_KEYS': self._paste_existing_keys,
            'BAKE': self._paste_bake,
        }[self.method]
        return applicator(context, mat)

    def _maybe_mirror(self, context: Context, matrix: Matrix) -> Matrix:
        if not self.use_mirror:
            return matrix

        mirror_ob = context.scene.addon_copy_global_transform_mirror_ob
        mirror_bone = context.scene.addon_copy_global_transform_mirror_bone

        # No mirror object means "current armature object".
        ctx_ob = context.object
        if not mirror_ob and mirror_bone and ctx_ob and ctx_ob.type == 'ARMATURE':
            mirror_ob = ctx_ob

        if not mirror_ob:
            raise UnableToMirrorError()

        if mirror_ob.type == 'ARMATURE' and mirror_bone:
            return self._mirror_over_bone(matrix, mirror_ob, mirror_bone)
        return self._mirror_over_ob(matrix, mirror_ob)

    def _mirror_over_ob(self, matrix: Matrix, mirror_ob: bpy.types.Object) -> Matrix:
        mirror_matrix = mirror_ob.matrix_world
        return self._mirror_over_matrix(matrix, mirror_matrix)

    def _mirror_over_bone(self, matrix: Matrix, mirror_ob: bpy.types.Object, mirror_bone_name: str) -> Matrix:
        bone = mirror_ob.pose.bones[mirror_bone_name]
        mirror_matrix = mirror_ob.matrix_world @ bone.matrix
        return self._mirror_over_matrix(matrix, mirror_matrix)

    def _mirror_over_matrix(self, matrix: Matrix, mirror_matrix: Matrix) -> Matrix:
        # Compute the matrix in the space of the mirror matrix:
        mat_local = mirror_matrix.inverted() @ matrix

        # Decompose the matrix, as we don't want to touch the scale. This
        # operator should only mirror the translation and rotation components.
        trans, rot_q, scale = mat_local.decompose()

        # Mirror the translation component:
        axis_index = ord(self.mirror_axis_loc) - ord('x')
        trans[axis_index] *= -1

        # Flip the rotation, and use a rotation order that applies the to-be-flipped axes first.
        match self.mirror_axis_rot:
            case 'x':
                rot_e = rot_q.to_euler('XYZ')
                rot_e.x *= -1  # Flip the requested rotation axis.
                rot_e.y *= -1  # Also flip the bone roll.
            case 'y':
                rot_e = rot_q.to_euler('YZX')
                rot_e.y *= -1  # Flip the requested rotation axis.
                rot_e.z *= -1  # Also flip another axis? Not sure how to handle this one.
            case 'z':
                rot_e = rot_q.to_euler('ZYX')
                rot_e.z *= -1  # Flip the requested rotation axis.
                rot_e.y *= -1  # Also flip the bone roll.

        # Recompose the local matrix:
        mat_local = Matrix.LocRotScale(trans, rot_e, scale)

        # Go back to world space:
        mirrored_world = mirror_matrix @ mat_local
        return mirrored_world

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


class PanelMixin:
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Animation"


class VIEW3D_PT_copy_global_transform(PanelMixin, Panel):
    bl_label = "Global Transform"

    def draw(self, context: Context) -> None:
        layout = self.layout

        # No need to put "Global Transform" in the operator text, given that it's already in the panel title.
        layout.operator("object.copy_global_transform", text="Copy", icon='COPYDOWN')

        paste_col = layout.column(align=True)

        paste_row = paste_col.row(align=True)
        paste_props = paste_row.operator("object.paste_transform", text="Paste", icon='PASTEDOWN')
        paste_props.method = 'CURRENT'
        paste_props.use_mirror = False
        paste_props = paste_row.operator("object.paste_transform", text="Mirrored", icon='PASTEFLIPDOWN')
        paste_props.method = 'CURRENT'
        paste_props.use_mirror = True

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


class VIEW3D_PT_copy_global_transform_mirror(PanelMixin, Panel):
    bl_label = "Mirror Options"
    bl_parent_id = "VIEW3D_PT_copy_global_transform"

    def draw(self, context: Context) -> None:
        layout = self.layout
        scene = context.scene
        layout.prop(scene, 'addon_copy_global_transform_mirror_ob', text="Object")

        mirror_ob = scene.addon_copy_global_transform_mirror_ob
        if mirror_ob is None:
            # No explicit mirror object means "the current armature", so then the bone name should be editable.
            if context.object and context.object.type == 'ARMATURE':
                self._bone_search(layout, scene, context.object)
            else:
                self._bone_entry(layout, scene)
        elif mirror_ob.type == 'ARMATURE':
            self._bone_search(layout, scene, mirror_ob)

    def _bone_search(self, layout: UILayout, scene: bpy.types.Scene, armature_ob: bpy.types.Object) -> None:
        """Search within the bones of the given armature."""
        assert armature_ob and armature_ob.type == 'ARMATURE'

        layout.prop_search(
            scene,
            "addon_copy_global_transform_mirror_bone",
            armature_ob.data,
            "edit_bones" if armature_ob.mode == 'EDIT' else "bones",
            text="Bone",
        )

    def _bone_entry(self, layout: UILayout, scene: bpy.types.Scene) -> None:
        """Allow manual entry of a bone name."""
        layout.prop(scene, "addon_copy_global_transform_mirror_bone", text="Bone")


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
    VIEW3D_PT_copy_global_transform_mirror,
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

    # The mirror object & bone name are stored on the scene, and not on the
    # operator. This makes it possible to set up the operator for use in a
    # certain scene, while keeping hotkey assignments working as usual.
    #
    # The goal is to allow hotkeys for "copy", "paste", and "paste mirrored",
    # while keeping the other choices in a more global place.
    bpy.types.Scene.addon_copy_global_transform_mirror_ob = bpy.props.PointerProperty(
        type=bpy.types.Object,
        name="Mirror Object",
        description="Object to mirror over. Leave empty and name a bone to always mirror "
        "over that bone of the active armature",
    )
    bpy.types.Scene.addon_copy_global_transform_mirror_bone = bpy.props.StringProperty(
        name="Mirror Bone",
        description="Bone to use for the mirroring",
    )


def unregister():
    _unregister()
    _unregister_message_bus()
    bpy.app.handlers.load_post.remove(_on_blendfile_load_post)

    del bpy.types.Scene.addon_copy_global_transform_mirror_ob
    del bpy.types.Scene.addon_copy_global_transform_mirror_bone

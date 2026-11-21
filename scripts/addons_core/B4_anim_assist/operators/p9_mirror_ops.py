import math
from types import SimpleNamespace

import bpy
from ..core.p9_properties import get_p9
from ..core import p9_pair_detect as det
from ..core import p9_mirror_math as mm
from ..core import p8_match_math as p8mm
from ..core.logging import get_logger
from ..core.fcurve_compat import get_fcurves
from ..core.bone_utils import pose_bone_selected, set_pose_bone_selected

_log = get_logger(__name__)


def _pose_poll(context, cls=None):
    obj = context.active_object
    if obj is None or obj.type != "ARMATURE":
        if cls is not None:
            cls.poll_message_set("Select an armature to use pose mirroring")
        return False
    if context.mode != "POSE":
        if cls is not None:
            cls.poll_message_set("Switch to Pose Mode to mirror bones")
        return False
    if obj.data.bones.active is None:
        if cls is not None:
            cls.poll_message_set("Select an active pose bone to mirror")
        return False
    return True


def _get_overrides(p9):
    overrides = {}
    if p9 and p9.pair_overrides:
        for item in p9.pair_overrides:
            if item.bone_a and item.bone_b:
                overrides[item.bone_a] = item.bone_b
                overrides[item.bone_b] = item.bone_a
    return overrides


def _get_exceptions(p9):
    exceptions = {}
    if p9 and p9.naming_exceptions:
        for item in p9.naming_exceptions:
            if item.original and item.opposite:
                exceptions[item.original] = item.opposite
                exceptions[item.opposite] = item.original
    return exceptions


def _build_channel_filter(p9):
    if p9 is None:
        return p8mm.ChannelFilter.all()
    return p8mm.ChannelFilter(
        location=p8mm.AxisMask(x=p9.mirror_location and p9.axis_mask[0],
                                y=p9.mirror_location and p9.axis_mask[1],
                                z=p9.mirror_location and p9.axis_mask[2]),
        rotation=p8mm.AxisMask(x=p9.mirror_rotation and p9.axis_mask[0],
                                y=p9.mirror_rotation and p9.axis_mask[1],
                                z=p9.mirror_rotation and p9.axis_mask[2]),
        scale=p8mm.AxisMask(x=p9.mirror_scale and p9.axis_mask[0],
                             y=p9.mirror_scale and p9.axis_mask[1],
                             z=p9.mirror_scale and p9.axis_mask[2]),
    )


def _restore_frame(scene, frame: float) -> None:
    """Restore a possibly fractional frame without truncating the subframe."""
    base = math.floor(frame)
    try:
        scene.frame_set(base, subframe=float(frame) - base)
    except TypeError:  # pragma: no cover - very old Blender
        scene.frame_set(base)


class AA_OT_p9_match_to_opposite(bpy.types.Operator):
    """Match active bone's transform to opposite bone (no mirroring)"""
    bl_idname = "animassist.p9_match_to_opposite"
    bl_label = "Match to Opposite"
    bl_description = "Apply opposite bone's transform to active bone without mirroring"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return _pose_poll(context, cls)

    def execute(self, context):
        obj = context.active_object
        p9 = get_p9(context)
        active_bone = context.active_pose_bone

        overrides = _get_overrides(p9)
        exceptions = _get_exceptions(p9)

        opposite_name = det.find_opposite(active_bone.name, overrides=overrides, exceptions=exceptions)
        if not opposite_name or opposite_name not in obj.pose.bones:
            self.report({'ERROR'}, f"No opposite bone found for {active_bone.name}. Use .L/.R naming or add a pair override under Mirror & Symmetry")
            return {'FINISHED'}

        opposite_bone = obj.pose.bones[opposite_name]
        channel_filter = _build_channel_filter(p9)

        try:
            # "Match to opposite": the ACTIVE bone takes the opposite's pose.
            # Was mirror_bone_pose(active, opposite): wrong bone, and mirrored.
            mm.copy_bone_pose(opposite_bone, active_bone, channel_filter)
            self.report({'INFO'}, f"Matched {active_bone.name} to {opposite_name}")
        except Exception as e:
            _log.error(f"match_to_opposite failed: {e}")
            self.report({'ERROR'}, str(e))
            return {'FINISHED'}

        return {'FINISHED'}


class AA_OT_p9_match_opposite_to_active(bpy.types.Operator):
    """Match opposite bone's transform to active bone (no mirroring)"""
    bl_idname = "animassist.p9_match_opposite_to_active"
    bl_label = "Match Opposite to Active"
    bl_description = "Apply active bone's transform to opposite bone without mirroring"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return _pose_poll(context, cls)

    def execute(self, context):
        obj = context.active_object
        p9 = get_p9(context)
        active_bone = context.active_pose_bone

        overrides = _get_overrides(p9)
        exceptions = _get_exceptions(p9)

        opposite_name = det.find_opposite(active_bone.name, overrides=overrides, exceptions=exceptions)
        if not opposite_name or opposite_name not in obj.pose.bones:
            self.report({'ERROR'}, f"No opposite bone found for {active_bone.name}. Use .L/.R naming or add a pair override under Mirror & Symmetry")
            return {'FINISHED'}

        opposite_bone = obj.pose.bones[opposite_name]
        channel_filter = _build_channel_filter(p9)

        try:
            # "Match opposite to active": the OPPOSITE bone takes the active's pose.
            mm.copy_bone_pose(active_bone, opposite_bone, channel_filter)
            self.report({'INFO'}, f"Matched {opposite_name} to {active_bone.name}")
        except Exception as e:
            _log.error(f"match_opposite_to_active failed: {e}")
            self.report({'ERROR'}, str(e))
            return {'FINISHED'}

        return {'FINISHED'}


class AA_OT_p9_mirror_pose(bpy.types.Operator):
    """Mirror active bone's transform to opposite bone"""
    bl_idname = "animassist.p9_mirror_pose"
    bl_label = "Mirror Pose"
    bl_description = "Mirror active bone's transform to its opposite"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return _pose_poll(context, cls)

    def execute(self, context):
        obj = context.active_object
        p9 = get_p9(context)
        active_bone = context.active_pose_bone

        overrides = _get_overrides(p9)
        exceptions = _get_exceptions(p9)

        opposite_name = det.find_opposite(active_bone.name, overrides=overrides, exceptions=exceptions)
        if not opposite_name or opposite_name not in obj.pose.bones:
            self.report({'ERROR'}, f"No opposite bone found for {active_bone.name}. Use .L/.R naming or add a pair override under Mirror & Symmetry")
            return {'FINISHED'}

        opposite_bone = obj.pose.bones[opposite_name]
        axis = p9.mirror_axis if p9 else "X"
        channel_filter = _build_channel_filter(p9)
        mirror_space = p9.mirror_space if p9 else "LOCAL"

        try:
            if mirror_space == "VISUAL":
                mm.mirror_bone_visual(active_bone, opposite_bone, obj, axis=axis, channel_filter=channel_filter)
            else:
                mm.mirror_bone_pose(active_bone, opposite_bone, axis, channel_filter)
            self.report({'INFO'}, f"Mirrored {active_bone.name} to {opposite_name}")
        except Exception as e:
            _log.error(f"mirror_pose failed: {e}")
            self.report({'ERROR'}, str(e))
            return {'FINISHED'}

        return {'FINISHED'}


class AA_OT_p9_mirror_selected(bpy.types.Operator):
    """Mirror all selected bones to their opposites"""
    bl_idname = "animassist.p9_mirror_selected"
    bl_label = "Mirror Selected"
    bl_description = "Mirror all selected pose bones to their opposite sides"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return _pose_poll(context, cls)

    def execute(self, context):
        obj = context.active_object
        p9 = get_p9(context)

        overrides = _get_overrides(p9)
        exceptions = _get_exceptions(p9)
        axis = p9.mirror_axis if p9 else "X"
        channel_filter = _build_channel_filter(p9)
        mirror_space = p9.mirror_space if p9 else "LOCAL"

        selected_bones = [b for b in obj.pose.bones if pose_bone_selected(b)]
        if not selected_bones:
            self.report({'WARNING'}, "No bones selected")
            return {'FINISHED'}

        count = 0
        try:
            # Capture every source before writing any opposite: selecting both
            # sides must not read back the pose just written by the first bone.
            sources = {bone.name: SimpleNamespace(
                name=bone.name, location=tuple(bone.location),
                rotation_euler=tuple(bone.rotation_euler),
                rotation_quaternion=tuple(bone.rotation_quaternion),
                rotation_axis_angle=tuple(bone.rotation_axis_angle),
                rotation_mode=bone.rotation_mode, scale=tuple(bone.scale),
            ) for bone in selected_bones}
            worlds = {bone.name: p8mm.visual_world_matrix(bone).copy()
                      for bone in selected_bones} if mirror_space == "VISUAL" else {}
            for bone in selected_bones:
                opposite_name = det.find_opposite(bone.name, overrides=overrides, exceptions=exceptions)
                if not opposite_name or opposite_name not in obj.pose.bones:
                    continue

                opposite_bone = obj.pose.bones[opposite_name]

                if mirror_space == "VISUAL":
                    mm.mirror_bone_visual(bone, opposite_bone, obj, axis=axis,
                                          channel_filter=channel_filter, source_world=worlds[bone.name])
                else:
                    mm.mirror_bone_pose(sources[bone.name], opposite_bone, axis, channel_filter)
                count += 1

            self.report({'INFO'}, f"Mirrored {count} bones")
        except Exception as e:
            _log.error(f"mirror_selected failed: {e}")
            self.report({'ERROR'}, str(e))

        return {'FINISHED'}


class AA_OT_p9_mirror_location(bpy.types.Operator):
    """Mirror location channels only"""
    bl_idname = "animassist.p9_mirror_location"
    bl_label = "Mirror Location"
    bl_description = "Mirror location channels only to opposite bone"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return _pose_poll(context, cls)

    def execute(self, context):
        obj = context.active_object
        p9 = get_p9(context)
        active_bone = context.active_pose_bone

        overrides = _get_overrides(p9)
        exceptions = _get_exceptions(p9)

        opposite_name = det.find_opposite(active_bone.name, overrides=overrides, exceptions=exceptions)
        if not opposite_name or opposite_name not in obj.pose.bones:
            self.report({'ERROR'}, f"No opposite bone found for {active_bone.name}. Use .L/.R naming or add a pair override under Mirror & Symmetry")
            return {'FINISHED'}

        opposite_bone = obj.pose.bones[opposite_name]
        axis = p9.mirror_axis if p9 else "X"

        # Force location-only channel filter
        loc_only = p8mm.ChannelFilter(
            location=p8mm.AxisMask(x=True, y=True, z=True),
            rotation=p8mm.AxisMask(x=False, y=False, z=False),
            scale=p8mm.AxisMask(x=False, y=False, z=False),
        )

        mirror_space = p9.mirror_space if p9 else "LOCAL"

        try:
            if mirror_space == "VISUAL":
                mm.mirror_bone_visual(active_bone, opposite_bone, obj, axis=axis, channel_filter=loc_only)
            else:
                mm.mirror_bone_pose(active_bone, opposite_bone, axis, loc_only)
            self.report({'INFO'}, f"Mirrored location of {active_bone.name}")
        except Exception as e:
            _log.error(f"mirror_location failed: {e}")
            self.report({'ERROR'}, str(e))

        return {'FINISHED'}


class AA_OT_p9_mirror_rotation(bpy.types.Operator):
    """Mirror rotation channels only"""
    bl_idname = "animassist.p9_mirror_rotation"
    bl_label = "Mirror Rotation"
    bl_description = "Mirror rotation channels only to opposite bone"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return _pose_poll(context, cls)

    def execute(self, context):
        obj = context.active_object
        p9 = get_p9(context)
        active_bone = context.active_pose_bone

        overrides = _get_overrides(p9)
        exceptions = _get_exceptions(p9)

        opposite_name = det.find_opposite(active_bone.name, overrides=overrides, exceptions=exceptions)
        if not opposite_name or opposite_name not in obj.pose.bones:
            self.report({'ERROR'}, f"No opposite bone found for {active_bone.name}. Use .L/.R naming or add a pair override under Mirror & Symmetry")
            return {'FINISHED'}

        opposite_bone = obj.pose.bones[opposite_name]
        axis = p9.mirror_axis if p9 else "X"

        # Force rotation-only channel filter
        rot_only = p8mm.ChannelFilter(
            location=p8mm.AxisMask(x=False, y=False, z=False),
            rotation=p8mm.AxisMask(x=True, y=True, z=True),
            scale=p8mm.AxisMask(x=False, y=False, z=False),
        )

        mirror_space = p9.mirror_space if p9 else "LOCAL"

        try:
            if mirror_space == "VISUAL":
                mm.mirror_bone_visual(active_bone, opposite_bone, obj, axis=axis, channel_filter=rot_only)
            else:
                mm.mirror_bone_pose(active_bone, opposite_bone, axis, rot_only)
            self.report({'INFO'}, f"Mirrored rotation of {active_bone.name}")
        except Exception as e:
            _log.error(f"mirror_rotation failed: {e}")
            self.report({'ERROR'}, str(e))

        return {'FINISHED'}


class AA_OT_p9_mirror_scale(bpy.types.Operator):
    """Mirror scale channels only"""
    bl_idname = "animassist.p9_mirror_scale"
    bl_label = "Mirror Scale"
    bl_description = "Mirror scale channels only to opposite bone"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return _pose_poll(context, cls)

    def execute(self, context):
        obj = context.active_object
        p9 = get_p9(context)
        active_bone = context.active_pose_bone

        overrides = _get_overrides(p9)
        exceptions = _get_exceptions(p9)

        opposite_name = det.find_opposite(active_bone.name, overrides=overrides, exceptions=exceptions)
        if not opposite_name or opposite_name not in obj.pose.bones:
            self.report({'ERROR'}, f"No opposite bone found for {active_bone.name}. Use .L/.R naming or add a pair override under Mirror & Symmetry")
            return {'FINISHED'}

        opposite_bone = obj.pose.bones[opposite_name]
        axis = p9.mirror_axis if p9 else "X"

        # Force scale-only channel filter
        scale_only = p8mm.ChannelFilter(
            location=p8mm.AxisMask(x=False, y=False, z=False),
            rotation=p8mm.AxisMask(x=False, y=False, z=False),
            scale=p8mm.AxisMask(x=True, y=True, z=True),
        )

        mirror_space = p9.mirror_space if p9 else "LOCAL"

        try:
            if mirror_space == "VISUAL":
                mm.mirror_bone_visual(active_bone, opposite_bone, obj, axis=axis, channel_filter=scale_only)
            else:
                mm.mirror_bone_pose(active_bone, opposite_bone, axis, scale_only)
            self.report({'INFO'}, f"Mirrored scale of {active_bone.name}")
        except Exception as e:
            _log.error(f"mirror_scale failed: {e}")
            self.report({'ERROR'}, str(e))

        return {'FINISHED'}


class AA_OT_p9_mirror_frame(bpy.types.Operator):
    """Mirror selected bones at current frame and insert keyframes"""
    bl_idname = "animassist.p9_mirror_frame"
    bl_label = "Mirror Frame"
    bl_description = "Mirror all selected bones at current frame and insert keyframes"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return _pose_poll(context, cls)

    def execute(self, context):
        obj = context.active_object
        p9 = get_p9(context)

        overrides = _get_overrides(p9)
        exceptions = _get_exceptions(p9)
        axis = p9.mirror_axis if p9 else "X"
        channel_filter = _build_channel_filter(p9)
        mirror_space = p9.mirror_space if p9 else "LOCAL"

        selected_bones = [b for b in obj.pose.bones if pose_bone_selected(b)]
        if not selected_bones:
            self.report({'WARNING'}, "No bones selected")
            return {'FINISHED'}

        count = 0
        try:
            for bone in selected_bones:
                opposite_name = det.find_opposite(bone.name, overrides=overrides, exceptions=exceptions)
                if not opposite_name or opposite_name not in obj.pose.bones:
                    continue

                opposite_bone = obj.pose.bones[opposite_name]

                if mirror_space == "VISUAL":
                    mm.mirror_bone_visual(bone, opposite_bone, obj, axis=axis, channel_filter=channel_filter)
                else:
                    mm.mirror_bone_pose(bone, opposite_bone, axis, channel_filter)

                # Insert keyframe for opposite bone
                opposite_bone.keyframe_insert(data_path="location")
                opposite_bone.keyframe_insert(data_path="rotation_euler")
                opposite_bone.keyframe_insert(data_path="scale")
                count += 1

            self.report({'INFO'}, f"Mirrored and keyed {count} bones at frame {context.scene.frame_current}")
        except Exception as e:
            _log.error(f"mirror_frame failed: {e}")
            self.report({'ERROR'}, str(e))

        return {'FINISHED'}


class AA_OT_p9_mirror_range(bpy.types.Operator):
    """Mirror selected bones across a frame range"""
    bl_idname = "animassist.p9_mirror_range"
    bl_label = "Mirror Range"
    bl_description = "Mirror selected bones across a frame range and insert keyframes"
    bl_options = {'REGISTER', 'UNDO'}

    start_frame: bpy.props.IntProperty(
        name="Start Frame",
        description="First frame of range to mirror",
        default=1,
        min=0
    )
    end_frame: bpy.props.IntProperty(
        name="End Frame",
        description="Last frame of range to mirror",
        default=100,
        min=0
    )

    @classmethod
    def poll(cls, context):
        return _pose_poll(context, cls)

    def execute(self, context):
        obj = context.active_object
        p9 = get_p9(context)

        overrides = _get_overrides(p9)
        exceptions = _get_exceptions(p9)
        axis = p9.mirror_axis if p9 else "X"
        channel_filter = _build_channel_filter(p9)
        mirror_space = p9.mirror_space if p9 else "LOCAL"

        selected_bones = [b for b in obj.pose.bones if pose_bone_selected(b)]
        if not selected_bones:
            self.report({'WARNING'}, "No bones selected")
            return {'FINISHED'}

        frame_count = 0
        original_frame = float(context.scene.frame_current_final)
        try:
            for frame in range(self.start_frame, self.end_frame + 1):
                context.scene.frame_set(frame)

                for bone in selected_bones:
                    opposite_name = det.find_opposite(bone.name, overrides=overrides, exceptions=exceptions)
                    if not opposite_name or opposite_name not in obj.pose.bones:
                        continue

                    opposite_bone = obj.pose.bones[opposite_name]

                    if mirror_space == "VISUAL":
                        mm.mirror_bone_visual(bone, opposite_bone, obj, axis=axis, channel_filter=channel_filter)
                    else:
                        mm.mirror_bone_pose(bone, opposite_bone, axis, channel_filter)

                    # Insert keyframe for opposite bone
                    opposite_bone.keyframe_insert(data_path="location")
                    opposite_bone.keyframe_insert(data_path="rotation_euler")
                    opposite_bone.keyframe_insert(data_path="scale")

                frame_count += 1

            self.report({'INFO'}, f"Mirrored across {frame_count} frames ({self.start_frame}-{self.end_frame})")
        except Exception as e:
            _log.error(f"mirror_range failed: {e}")
            self.report({'ERROR'}, str(e))
        finally:
            # The loop scrubs the playhead; always put it back, even on error.
            _restore_frame(context.scene, original_frame)

        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


class AA_OT_p9_mirror_preview(bpy.types.Operator):
    """Mirror selected bones across preview range (or scene range)"""
    bl_idname = "animassist.p9_mirror_preview"
    bl_label = "Mirror Preview"
    bl_description = "Mirror selected bones across preview frame range"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return _pose_poll(context, cls)

    def execute(self, context):
        obj = context.active_object
        p9 = get_p9(context)
        scene = context.scene

        overrides = _get_overrides(p9)
        exceptions = _get_exceptions(p9)
        axis = p9.mirror_axis if p9 else "X"
        channel_filter = _build_channel_filter(p9)
        mirror_space = p9.mirror_space if p9 else "LOCAL"

        selected_bones = [b for b in obj.pose.bones if pose_bone_selected(b)]
        if not selected_bones:
            self.report({'WARNING'}, "No bones selected")
            return {'FINISHED'}

        # Use preview range if available, else fall back to scene range
        if scene.use_preview_range:
            start_frame = scene.frame_preview_start
            end_frame = scene.frame_preview_end
        else:
            start_frame = scene.frame_start
            end_frame = scene.frame_end

        frame_count = 0
        original_frame = float(context.scene.frame_current_final)
        try:
            for frame in range(start_frame, end_frame + 1):
                context.scene.frame_set(frame)

                for bone in selected_bones:
                    opposite_name = det.find_opposite(bone.name, overrides=overrides, exceptions=exceptions)
                    if not opposite_name or opposite_name not in obj.pose.bones:
                        continue

                    opposite_bone = obj.pose.bones[opposite_name]

                    if mirror_space == "VISUAL":
                        mm.mirror_bone_visual(bone, opposite_bone, obj, axis=axis, channel_filter=channel_filter)
                    else:
                        mm.mirror_bone_pose(bone, opposite_bone, axis, channel_filter)

                    # Insert keyframe for opposite bone
                    opposite_bone.keyframe_insert(data_path="location")
                    opposite_bone.keyframe_insert(data_path="rotation_euler")
                    opposite_bone.keyframe_insert(data_path="scale")

                frame_count += 1

            self.report({'INFO'}, f"Mirrored across {frame_count} frames ({start_frame}-{end_frame})")
        except Exception as e:
            _log.error(f"mirror_preview failed: {e}")
            self.report({'ERROR'}, str(e))
        finally:
            # The loop scrubs the playhead; always put it back, even on error.
            _restore_frame(context.scene, original_frame)

        return {'FINISHED'}


class AA_OT_p9_mirror_keyed_only(bpy.types.Operator):
    """Mirror selected bones, only channels with keyframes"""
    bl_idname = "animassist.p9_mirror_keyed_only"
    bl_label = "Mirror Keyed Only"
    bl_description = "Mirror only channels that have keyframes at current frame"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return _pose_poll(context, cls)

    def execute(self, context):
        obj = context.active_object
        p9 = get_p9(context)

        overrides = _get_overrides(p9)
        exceptions = _get_exceptions(p9)
        axis = p9.mirror_axis if p9 else "X"
        channel_filter = _build_channel_filter(p9)
        mirror_space = p9.mirror_space if p9 else "LOCAL"

        selected_bones = [b for b in obj.pose.bones if pose_bone_selected(b)]
        if not selected_bones:
            self.report({'WARNING'}, "No bones selected")
            return {'FINISHED'}

        current_frame = context.scene.frame_current
        count = 0

        try:
            for bone in selected_bones:
                opposite_name = det.find_opposite(bone.name, overrides=overrides, exceptions=exceptions)
                if not opposite_name or opposite_name not in obj.pose.bones:
                    continue

                opposite_bone = obj.pose.bones[opposite_name]

                # Check for keyframes on source bone at current frame
                # Check animation data on the armature object, not the bone
                has_keyframe = False
                if obj.animation_data and obj.animation_data.action:
                    for fcurve in get_fcurves(obj.animation_data.action, anim_data=obj.animation_data):
                        # Pose bone fcurves look like "pose.bones["BoneName"].location" etc
                        if f'pose.bones["{bpy.utils.escape_identifier(bone.name)}"]' in fcurve.data_path:
                            for keyframe_point in fcurve.keyframe_points:
                                if abs(keyframe_point.co[0] - current_frame) < 0.01:
                                    has_keyframe = True
                                    break
                            if has_keyframe:
                                break

                if not has_keyframe:
                    continue

                if mirror_space == "VISUAL":
                    mm.mirror_bone_visual(bone, opposite_bone, obj, axis=axis, channel_filter=channel_filter)
                else:
                    mm.mirror_bone_pose(bone, opposite_bone, axis, channel_filter)

                count += 1

            self.report({'INFO'}, f"Mirrored {count} keyed bones")
        except Exception as e:
            _log.error(f"mirror_keyed_only failed: {e}")
            self.report({'ERROR'}, str(e))

        return {'FINISHED'}


class AA_OT_p9_mirror_visible_only(bpy.types.Operator):
    """Mirror selected bones visible in dopesheet only"""
    bl_idname = "animassist.p9_mirror_visible_only"
    bl_label = "Mirror Visible Only"
    bl_description = "Mirror only channels visible in dopesheet"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return _pose_poll(context, cls)

    def execute(self, context):
        obj = context.active_object
        p9 = get_p9(context)

        overrides = _get_overrides(p9)
        exceptions = _get_exceptions(p9)
        axis = p9.mirror_axis if p9 else "X"
        channel_filter = _build_channel_filter(p9)
        mirror_space = p9.mirror_space if p9 else "LOCAL"

        selected_bones = [b for b in obj.pose.bones if pose_bone_selected(b)]
        if not selected_bones:
            self.report({'WARNING'}, "No bones selected")
            return {'FINISHED'}

        count = 0
        try:
            for bone in selected_bones:
                opposite_name = det.find_opposite(bone.name, overrides=overrides, exceptions=exceptions)
                if not opposite_name or opposite_name not in obj.pose.bones:
                    continue

                opposite_bone = obj.pose.bones[opposite_name]

                # Check if bone has visible fcurves
                # Check animation data on the armature object, not the bone
                visible = False
                if obj.animation_data and obj.animation_data.action:
                    for fcurve in get_fcurves(obj.animation_data.action, anim_data=obj.animation_data):
                        # Pose bone fcurves look like "pose.bones["BoneName"].location" etc
                        if f'pose.bones["{bpy.utils.escape_identifier(bone.name)}"]' in fcurve.data_path and not fcurve.hide:
                            visible = True
                            break

                if not visible:
                    continue

                if mirror_space == "VISUAL":
                    mm.mirror_bone_visual(bone, opposite_bone, obj, axis=axis, channel_filter=channel_filter)
                else:
                    mm.mirror_bone_pose(bone, opposite_bone, axis, channel_filter)

                count += 1

            self.report({'INFO'}, f"Mirrored {count} visible bones")
        except Exception as e:
            _log.error(f"mirror_visible_only failed: {e}")
            self.report({'ERROR'}, str(e))

        return {'FINISHED'}


class AA_OT_p9_mirror_local(bpy.types.Operator):
    """Mirror in local space (regardless of property setting)"""
    bl_idname = "animassist.p9_mirror_local"
    bl_label = "Mirror Local"
    bl_description = "Mirror selected bones in local space"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return _pose_poll(context, cls)

    def execute(self, context):
        obj = context.active_object
        p9 = get_p9(context)

        overrides = _get_overrides(p9)
        exceptions = _get_exceptions(p9)
        axis = p9.mirror_axis if p9 else "X"
        channel_filter = _build_channel_filter(p9)

        selected_bones = [b for b in obj.pose.bones if pose_bone_selected(b)]
        if not selected_bones:
            self.report({'WARNING'}, "No bones selected")
            return {'FINISHED'}

        count = 0
        try:
            for bone in selected_bones:
                opposite_name = det.find_opposite(bone.name, overrides=overrides, exceptions=exceptions)
                if not opposite_name or opposite_name not in obj.pose.bones:
                    continue

                opposite_bone = obj.pose.bones[opposite_name]
                mm.mirror_bone_pose(bone, opposite_bone, axis, channel_filter)
                count += 1

            self.report({'INFO'}, f"Mirrored {count} bones in local space")
        except Exception as e:
            _log.error(f"mirror_local failed: {e}")
            self.report({'ERROR'}, str(e))

        return {'FINISHED'}


class AA_OT_p9_mirror_world(bpy.types.Operator):
    """Mirror in world space (regardless of property setting)"""
    bl_idname = "animassist.p9_mirror_world"
    bl_label = "Mirror World"
    bl_description = "Mirror selected bones in world space"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return _pose_poll(context, cls)

    def execute(self, context):
        obj = context.active_object
        p9 = get_p9(context)

        overrides = _get_overrides(p9)
        exceptions = _get_exceptions(p9)
        axis = p9.mirror_axis if p9 else "X"
        channel_filter = _build_channel_filter(p9)

        selected_bones = [b for b in obj.pose.bones if pose_bone_selected(b)]
        if not selected_bones:
            self.report({'WARNING'}, "No bones selected")
            return {'FINISHED'}

        count = 0
        try:
            for bone in selected_bones:
                opposite_name = det.find_opposite(bone.name, overrides=overrides, exceptions=exceptions)
                if not opposite_name or opposite_name not in obj.pose.bones:
                    continue

                opposite_bone = obj.pose.bones[opposite_name]
                mm.mirror_bone_visual(bone, opposite_bone, obj, axis=axis, channel_filter=channel_filter)
                count += 1

            self.report({'INFO'}, f"Mirrored {count} bones in world space")
        except Exception as e:
            _log.error(f"mirror_world failed: {e}")
            self.report({'ERROR'}, str(e))

        return {'FINISHED'}


class AA_OT_p9_visual_mirror(bpy.types.Operator):
    """Mirror for constrained rigs using visual transforms"""
    bl_idname = "animassist.p9_visual_mirror"
    bl_label = "Visual Mirror"
    bl_description = "Mirror selected bones using evaluated (visual) transforms for constrained rigs"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return _pose_poll(context, cls)

    def execute(self, context):
        obj = context.active_object
        p9 = get_p9(context)

        overrides = _get_overrides(p9)
        exceptions = _get_exceptions(p9)
        axis = p9.mirror_axis if p9 else "X"
        channel_filter = _build_channel_filter(p9)

        selected_bones = [b for b in obj.pose.bones if pose_bone_selected(b)]
        if not selected_bones:
            self.report({'WARNING'}, "No bones selected")
            return {'FINISHED'}

        count = 0
        try:
            for bone in selected_bones:
                opposite_name = det.find_opposite(bone.name, overrides=overrides, exceptions=exceptions)
                if not opposite_name or opposite_name not in obj.pose.bones:
                    continue

                opposite_bone = obj.pose.bones[opposite_name]
                mm.mirror_bone_visual(bone, opposite_bone, obj, axis=axis, channel_filter=channel_filter)
                count += 1

            self.report({'INFO'}, f"Visually mirrored {count} bones")
        except Exception as e:
            _log.error(f"visual_mirror failed: {e}")
            self.report({'ERROR'}, str(e))

        return {'FINISHED'}


class AA_OT_p9_mirror_with_offset(bpy.types.Operator):
    """Mirror while preserving existing offset between bones"""
    bl_idname = "animassist.p9_mirror_with_offset"
    bl_label = "Mirror with Offset"
    bl_description = "Mirror while preserving the existing offset between bones"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return _pose_poll(context, cls)

    def execute(self, context):
        obj = context.active_object
        p9 = get_p9(context)

        overrides = _get_overrides(p9)
        exceptions = _get_exceptions(p9)
        axis = p9.mirror_axis if p9 else "X"
        channel_filter = _build_channel_filter(p9)
        mirror_space = p9.mirror_space if p9 else "LOCAL"

        selected_bones = [b for b in obj.pose.bones if pose_bone_selected(b)]
        if not selected_bones:
            self.report({'WARNING'}, "No bones selected")
            return {'FINISHED'}

        count = 0
        try:
            for bone in selected_bones:
                opposite_name = det.find_opposite(bone.name, overrides=overrides, exceptions=exceptions)
                if not opposite_name or opposite_name not in obj.pose.bones:
                    continue

                opposite_bone = obj.pose.bones[opposite_name]

                # Store original offset
                original_location = opposite_bone.location.copy()

                if mirror_space == "VISUAL":
                    mm.mirror_bone_visual(bone, opposite_bone, obj, axis=axis, channel_filter=channel_filter)
                else:
                    mm.mirror_bone_pose(bone, opposite_bone, axis, channel_filter)

                # Apply offset back
                opposite_bone.location = original_location

                count += 1

            self.report({'INFO'}, f"Mirrored {count} bones with offset preservation")
        except Exception as e:
            _log.error(f"mirror_with_offset failed: {e}")
            self.report({'ERROR'}, str(e))

        return {'FINISHED'}


class AA_OT_p9_mirror_without_offset(bpy.types.Operator):
    """Mirror with exact value match (no offset preservation)"""
    bl_idname = "animassist.p9_mirror_without_offset"
    bl_label = "Mirror without Offset"
    bl_description = "Mirror with exact value matching (no offset preservation)"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return _pose_poll(context, cls)

    def execute(self, context):
        obj = context.active_object
        p9 = get_p9(context)

        overrides = _get_overrides(p9)
        exceptions = _get_exceptions(p9)
        axis = p9.mirror_axis if p9 else "X"
        channel_filter = _build_channel_filter(p9)
        mirror_space = p9.mirror_space if p9 else "LOCAL"

        selected_bones = [b for b in obj.pose.bones if pose_bone_selected(b)]
        if not selected_bones:
            self.report({'WARNING'}, "No bones selected")
            return {'FINISHED'}

        count = 0
        try:
            for bone in selected_bones:
                opposite_name = det.find_opposite(bone.name, overrides=overrides, exceptions=exceptions)
                if not opposite_name or opposite_name not in obj.pose.bones:
                    continue

                opposite_bone = obj.pose.bones[opposite_name]

                if mirror_space == "VISUAL":
                    mm.mirror_bone_visual(bone, opposite_bone, obj, axis=axis, channel_filter=channel_filter)
                else:
                    mm.mirror_bone_pose(bone, opposite_bone, axis, channel_filter)

                count += 1

            self.report({'INFO'}, f"Mirrored {count} bones without offset")
        except Exception as e:
            _log.error(f"mirror_without_offset failed: {e}")
            self.report({'ERROR'}, str(e))

        return {'FINISHED'}


class AA_OT_p9_swap_poses(bpy.types.Operator):
    """Swap poses of all left and right bone pairs"""
    bl_idname = "animassist.p9_swap_poses"
    bl_label = "Swap Poses"
    bl_description = "Swap transforms between all left and right bone pairs"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return _pose_poll(context, cls)

    def execute(self, context):
        obj = context.active_object
        p9 = get_p9(context)

        overrides = _get_overrides(p9)
        exceptions = _get_exceptions(p9)

        # Get all pose bones and find unique pairs
        processed = set()
        count = 0

        try:
            for bone in obj.pose.bones:
                if bone.name in processed:
                    continue

                opposite_name = det.find_opposite(bone.name, overrides=overrides, exceptions=exceptions)
                if not opposite_name or opposite_name not in obj.pose.bones:
                    continue

                opposite_bone = obj.pose.bones[opposite_name]

                # Mark both as processed
                processed.add(bone.name)
                processed.add(opposite_name)

                mm.swap_bone_poses(bone, opposite_bone)

                count += 1

            self.report({'INFO'}, f"Swapped poses for {count} bone pairs")
        except Exception as e:
            _log.error(f"swap_poses failed: {e}")
            self.report({'ERROR'}, str(e))

        return {'FINISHED'}


CLASSES = (
    AA_OT_p9_match_to_opposite,
    AA_OT_p9_match_opposite_to_active,
    AA_OT_p9_mirror_pose,
    AA_OT_p9_mirror_selected,
    AA_OT_p9_mirror_location,
    AA_OT_p9_mirror_rotation,
    AA_OT_p9_mirror_scale,
    AA_OT_p9_mirror_frame,
    AA_OT_p9_mirror_range,
    AA_OT_p9_mirror_preview,
    AA_OT_p9_mirror_keyed_only,
    AA_OT_p9_mirror_visible_only,
    AA_OT_p9_mirror_local,
    AA_OT_p9_mirror_world,
    AA_OT_p9_visual_mirror,
    AA_OT_p9_mirror_with_offset,
    AA_OT_p9_mirror_without_offset,
    AA_OT_p9_swap_poses,
)

"""Transform matching operators."""

import bpy
from mathutils import Matrix

from ..core.logging import get_logger
from ..core.p8_properties import get_p8
from ..core import p8_match_math as mm

_log = get_logger(__name__)


def _match_poll(context, cls=None):
    """At least one selected object with an active object."""
    if context.active_object is None:
        if cls is not None:
            cls.poll_message_set("Select an object or pose bone to use matching tools")
        return False
    if context.mode not in {'OBJECT', 'POSE'}:
        if cls is not None:
            cls.poll_message_set("Switch to Object Mode or Pose Mode to match transforms")
        return False
    return True


def _build_channel_filter(p8):
    """Build ChannelFilter from PropertyGroup settings."""
    if p8 is None:
        return mm.ChannelFilter.all()

    mode = p8.match_channels
    if mode == "LOCATION":
        return mm.ChannelFilter.loc_only()
    elif mode == "ROTATION":
        return mm.ChannelFilter.rot_only()
    elif mode == "SCALE":
        return mm.ChannelFilter.scale_only()
    elif mode == "LOC_ROT":
        return mm.ChannelFilter.loc_rot()
    return mm.ChannelFilter.all()


def _build_axis_filter(p8):
    """Build ChannelFilter with per-axis filtering from PropertyGroup."""
    if p8 is None:
        return mm.ChannelFilter.all()

    ax = mm.AxisMask(p8.match_axis[0], p8.match_axis[1], p8.match_axis[2])
    mode = p8.match_channels

    if mode == "LOCATION":
        return mm.ChannelFilter(location=ax, rotation=mm.MATCH_NONE, scale=mm.MATCH_NONE)
    elif mode == "ROTATION":
        return mm.ChannelFilter(location=mm.MATCH_NONE, rotation=ax, scale=mm.MATCH_NONE)
    elif mode == "SCALE":
        return mm.ChannelFilter(location=mm.MATCH_NONE, rotation=mm.MATCH_NONE, scale=ax)
    elif mode == "LOC_ROT":
        return mm.ChannelFilter(location=ax, rotation=ax, scale=mm.MATCH_NONE)
    return mm.ChannelFilter(location=ax, rotation=ax, scale=ax)


class AA_OT_p8_match_to_world(bpy.types.Operator):
    """Match the active object's transform to world origin."""
    bl_idname = "animassist.p8_match_to_world"
    bl_label = "Match to World"
    bl_description = "Set the active object's transform so it visually sits at the world origin."
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return _match_poll(context, cls)

    def execute(self, context):
        p8 = get_p8(context)
        obj = context.active_object

        cf = _build_channel_filter(p8)
        source_world = Matrix.Identity(4)

        result = mm.compute_match(
            source_world=source_world,
            target_obj=obj,
            channel_filter=cf,
            maintain_offset=p8.maintain_offset if p8 else False,
            respect_locks=p8.respect_locks if p8 else True,
            respect_drivers=p8.respect_drivers if p8 else True,
        )
        mm.apply_match_result(obj, result)

        if p8 and p8.auto_key_switch:
            mm.key_match_result(obj, result, context.scene.frame_current)

        self.report({"INFO"}, f"Matched '{obj.name}' to world ({len(result.channels_written)} channels)")
        return {"FINISHED"}


class AA_OT_p8_match_to_parent(bpy.types.Operator):
    """Match the active object to its parent's transform."""
    bl_idname = "animassist.p8_match_to_parent"
    bl_label = "Match to Parent"
    bl_description = "Set the active object's transform to match its parent's transform."
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        if not _match_poll(context, cls):
            return False
        if obj.parent is None:
            cls.poll_message_set("Select an object with a parent to match its parent's transform")
            return False
        return True

    def execute(self, context):
        p8 = get_p8(context)
        obj = context.active_object
        parent = obj.parent

        cf = _build_channel_filter(p8)
        source_world = mm.visual_world_matrix(parent)

        result = mm.compute_match(
            source_world=source_world,
            target_obj=obj,
            channel_filter=cf,
            maintain_offset=p8.maintain_offset if p8 else False,
            respect_locks=p8.respect_locks if p8 else True,
            respect_drivers=p8.respect_drivers if p8 else True,
        )
        mm.apply_match_result(obj, result)

        if p8 and p8.auto_key_switch:
            mm.key_match_result(obj, result, context.scene.frame_current)

        self.report({"INFO"}, f"Matched '{obj.name}' to parent ({len(result.channels_written)} channels)")
        return {"FINISHED"}


class AA_OT_p8_match_to_target(bpy.types.Operator):
    """Match the active object to another selected object."""
    bl_idname = "animassist.p8_match_to_target"
    bl_label = "Match to Target"
    bl_description = "Match the active object's transform to the other selected object's transform."
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if not _match_poll(context, cls):
            return False
        selected = context.selected_objects
        if len(selected) < 2:
            cls.poll_message_set("Select a target, then the object to match")
            return False
        return True

    def execute(self, context):
        p8 = get_p8(context)
        active = context.active_object

        # Get source from non-active selected objects
        sources = [o for o in context.selected_objects if o != active]
        if not sources:
            self.report({"ERROR"}, "Select the target object as well as the active object")
            return {"CANCELLED"}

        source = sources[0]

        cf = _build_channel_filter(p8)
        source_world = mm.visual_world_matrix(source)

        result = mm.compute_match(
            source_world=source_world,
            target_obj=active,
            channel_filter=cf,
            maintain_offset=p8.maintain_offset if p8 else False,
            respect_locks=p8.respect_locks if p8 else True,
            respect_drivers=p8.respect_drivers if p8 else True,
        )
        mm.apply_match_result(active, result)

        if p8 and p8.auto_key_switch:
            mm.key_match_result(active, result, context.scene.frame_current)

        self.report({"INFO"}, f"Matched '{active.name}' to '{source.name}' ({len(result.channels_written)} channels)")
        return {"FINISHED"}


class AA_OT_p8_match_selected_to_active(bpy.types.Operator):
    """Match all selected objects to the active object."""
    bl_idname = "animassist.p8_match_selected_to_active"
    bl_label = "Match Selected to Active"
    bl_description = "Match all other selected objects to the active object's transform."
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if not _match_poll(context, cls):
            return False
        selected = context.selected_objects
        if len(selected) < 2:
            cls.poll_message_set("Select a target, then the object to match")
            return False
        return True

    def execute(self, context):
        p8 = get_p8(context)
        active = context.active_object

        cf = _build_channel_filter(p8)
        source_world = mm.visual_world_matrix(active)

        count = 0
        for target in context.selected_objects:
            if target == active:
                continue

            result = mm.compute_match(
                source_world=source_world,
                target_obj=target,
                channel_filter=cf,
                maintain_offset=p8.maintain_offset if p8 else False,
                respect_locks=p8.respect_locks if p8 else True,
                respect_drivers=p8.respect_drivers if p8 else True,
            )
            mm.apply_match_result(target, result)

            if p8 and p8.auto_key_switch:
                mm.key_match_result(target, result, context.scene.frame_current)

            count += 1

        self.report({"INFO"}, f"Matched {count} object(s) to '{active.name}'")
        return {"FINISHED"}


class AA_OT_p8_visual_match(bpy.types.Operator):
    """Match active to selection using visual (evaluated) matrix."""
    bl_idname = "animassist.p8_visual_match"
    bl_label = "Visual Match"
    bl_description = "Match the active object using its visual (evaluated depsgraph) matrix."
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return _match_poll(context, cls)

    def execute(self, context):
        p8 = get_p8(context)
        obj = context.active_object

        cf = _build_channel_filter(p8)
        source_world = mm.visual_world_matrix(obj)

        result = mm.compute_match(
            source_world=source_world,
            target_obj=obj,
            channel_filter=cf,
            maintain_offset=p8.maintain_offset if p8 else False,
            respect_locks=p8.respect_locks if p8 else True,
            respect_drivers=p8.respect_drivers if p8 else True,
        )
        mm.apply_match_result(obj, result)

        if p8 and p8.auto_key_switch:
            mm.key_match_result(obj, result, context.scene.frame_current)

        self.report({"INFO"}, f"Visual matched '{obj.name}' ({len(result.channels_written)} channels)")
        return {"FINISHED"}


class AA_OT_p8_match_location(bpy.types.Operator):
    """Match location only."""
    bl_idname = "animassist.p8_match_location"
    bl_label = "Match Location"
    bl_description = "Match only the location (position) of the active object."
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if not _match_poll(context, cls):
            return False
        selected = context.selected_objects
        if len(selected) < 2:
            cls.poll_message_set("Select a target, then the object to match")
            return False
        return True

    def execute(self, context):
        p8 = get_p8(context)
        active = context.active_object

        sources = [o for o in context.selected_objects if o != active]
        if not sources:
            self.report({"ERROR"}, "Select the target object as well as the active object")
            return {"CANCELLED"}

        source = sources[0]

        cf = mm.ChannelFilter.loc_only()
        source_world = mm.visual_world_matrix(source)

        result = mm.compute_match(
            source_world=source_world,
            target_obj=active,
            channel_filter=cf,
            maintain_offset=p8.maintain_offset if p8 else False,
            respect_locks=p8.respect_locks if p8 else True,
            respect_drivers=p8.respect_drivers if p8 else True,
        )
        mm.apply_match_result(active, result)

        if p8 and p8.auto_key_switch:
            mm.key_match_result(active, result, context.scene.frame_current)

        self.report({"INFO"}, f"Matched location of '{active.name}' ({len(result.channels_written)} channels)")
        return {"FINISHED"}


class AA_OT_p8_match_rotation(bpy.types.Operator):
    """Match rotation only."""
    bl_idname = "animassist.p8_match_rotation"
    bl_label = "Match Rotation"
    bl_description = "Match only the rotation of the active object."
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if not _match_poll(context, cls):
            return False
        selected = context.selected_objects
        if len(selected) < 2:
            cls.poll_message_set("Select a target, then the object to match")
            return False
        return True

    def execute(self, context):
        p8 = get_p8(context)
        active = context.active_object

        sources = [o for o in context.selected_objects if o != active]
        if not sources:
            self.report({"ERROR"}, "Select the target object as well as the active object")
            return {"CANCELLED"}

        source = sources[0]

        cf = mm.ChannelFilter.rot_only()
        source_world = mm.visual_world_matrix(source)

        result = mm.compute_match(
            source_world=source_world,
            target_obj=active,
            channel_filter=cf,
            maintain_offset=p8.maintain_offset if p8 else False,
            respect_locks=p8.respect_locks if p8 else True,
            respect_drivers=p8.respect_drivers if p8 else True,
        )
        mm.apply_match_result(active, result)

        if p8 and p8.auto_key_switch:
            mm.key_match_result(active, result, context.scene.frame_current)

        self.report({"INFO"}, f"Matched rotation of '{active.name}' ({len(result.channels_written)} channels)")
        return {"FINISHED"}


class AA_OT_p8_match_scale(bpy.types.Operator):
    """Match scale only."""
    bl_idname = "animassist.p8_match_scale"
    bl_label = "Match Scale"
    bl_description = "Match only the scale of the active object."
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if not _match_poll(context, cls):
            return False
        selected = context.selected_objects
        if len(selected) < 2:
            cls.poll_message_set("Select a target, then the object to match")
            return False
        return True

    def execute(self, context):
        p8 = get_p8(context)
        active = context.active_object

        sources = [o for o in context.selected_objects if o != active]
        if not sources:
            self.report({"ERROR"}, "Select the target object as well as the active object")
            return {"CANCELLED"}

        source = sources[0]

        cf = mm.ChannelFilter.scale_only()
        source_world = mm.visual_world_matrix(source)

        result = mm.compute_match(
            source_world=source_world,
            target_obj=active,
            channel_filter=cf,
            maintain_offset=p8.maintain_offset if p8 else False,
            respect_locks=p8.respect_locks if p8 else True,
            respect_drivers=p8.respect_drivers if p8 else True,
        )
        mm.apply_match_result(active, result)

        if p8 and p8.auto_key_switch:
            mm.key_match_result(active, result, context.scene.frame_current)

        self.report({"INFO"}, f"Matched scale of '{active.name}' ({len(result.channels_written)} channels)")
        return {"FINISHED"}


class AA_OT_p8_match_trs(bpy.types.Operator):
    """Match full TRS (translation, rotation, scale)."""
    bl_idname = "animassist.p8_match_trs"
    bl_label = "Match TRS"
    bl_description = "Match the full transform (translation, rotation, and scale) of the active object."
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if not _match_poll(context, cls):
            return False
        selected = context.selected_objects
        if len(selected) < 2:
            cls.poll_message_set("Select a target, then the object to match")
            return False
        return True

    def execute(self, context):
        p8 = get_p8(context)
        active = context.active_object

        sources = [o for o in context.selected_objects if o != active]
        if not sources:
            self.report({"ERROR"}, "Select the target object as well as the active object")
            return {"CANCELLED"}

        source = sources[0]

        cf = mm.ChannelFilter.all()
        source_world = mm.visual_world_matrix(source)

        result = mm.compute_match(
            source_world=source_world,
            target_obj=active,
            channel_filter=cf,
            maintain_offset=p8.maintain_offset if p8 else False,
            respect_locks=p8.respect_locks if p8 else True,
            respect_drivers=p8.respect_drivers if p8 else True,
        )
        mm.apply_match_result(active, result)

        if p8 and p8.auto_key_switch:
            mm.key_match_result(active, result, context.scene.frame_current)

        self.report({"INFO"}, f"Matched TRS of '{active.name}' ({len(result.channels_written)} channels)")
        return {"FINISHED"}


class AA_OT_p8_match_axis_filtered(bpy.types.Operator):
    """Match with per-axis filtering."""
    bl_idname = "animassist.p8_match_axis_filtered"
    bl_label = "Match Axis Filtered"
    bl_description = "Match the active object using per-axis filtering settings."
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if not _match_poll(context, cls):
            return False
        selected = context.selected_objects
        if len(selected) < 2:
            cls.poll_message_set("Select a target, then the object to match")
            return False
        return True

    def execute(self, context):
        p8 = get_p8(context)
        active = context.active_object

        sources = [o for o in context.selected_objects if o != active]
        if not sources:
            self.report({"ERROR"}, "Select the target object as well as the active object")
            return {"CANCELLED"}

        source = sources[0]

        cf = _build_axis_filter(p8)
        source_world = mm.visual_world_matrix(source)

        result = mm.compute_match(
            source_world=source_world,
            target_obj=active,
            channel_filter=cf,
            maintain_offset=p8.maintain_offset if p8 else False,
            respect_locks=p8.respect_locks if p8 else True,
            respect_drivers=p8.respect_drivers if p8 else True,
        )
        mm.apply_match_result(active, result)

        if p8 and p8.auto_key_switch:
            mm.key_match_result(active, result, context.scene.frame_current)

        self.report({"INFO"}, f"Matched '{active.name}' with axis filtering ({len(result.channels_written)} channels)")
        return {"FINISHED"}


class AA_OT_p8_match_with_offset(bpy.types.Operator):
    """Match while maintaining current offset."""
    bl_idname = "animassist.p8_match_with_offset"
    bl_label = "Match with Offset"
    bl_description = "Match the active object while maintaining its current offset from the target."
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if not _match_poll(context, cls):
            return False
        selected = context.selected_objects
        if len(selected) < 2:
            cls.poll_message_set("Select a target, then the object to match")
            return False
        return True

    def execute(self, context):
        p8 = get_p8(context)
        active = context.active_object

        sources = [o for o in context.selected_objects if o != active]
        if not sources:
            self.report({"ERROR"}, "Select the target object as well as the active object")
            return {"CANCELLED"}

        source = sources[0]

        cf = _build_channel_filter(p8)
        source_world = mm.visual_world_matrix(source)

        result = mm.compute_match(
            source_world=source_world,
            target_obj=active,
            channel_filter=cf,
            maintain_offset=True,
            respect_locks=p8.respect_locks if p8 else True,
            respect_drivers=p8.respect_drivers if p8 else True,
        )
        mm.apply_match_result(active, result)

        if p8 and p8.auto_key_switch:
            mm.key_match_result(active, result, context.scene.frame_current)

        self.report({"INFO"}, f"Matched '{active.name}' with offset ({len(result.channels_written)} channels)")
        return {"FINISHED"}


class AA_OT_p8_match_without_offset(bpy.types.Operator):
    """Match without maintaining offset."""
    bl_idname = "animassist.p8_match_without_offset"
    bl_label = "Match without Offset"
    bl_description = "Match the active object without maintaining any offset from the target."
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if not _match_poll(context, cls):
            return False
        selected = context.selected_objects
        if len(selected) < 2:
            cls.poll_message_set("Select a target, then the object to match")
            return False
        return True

    def execute(self, context):
        p8 = get_p8(context)
        active = context.active_object

        sources = [o for o in context.selected_objects if o != active]
        if not sources:
            self.report({"ERROR"}, "Select the target object as well as the active object")
            return {"CANCELLED"}

        source = sources[0]

        cf = _build_channel_filter(p8)
        source_world = mm.visual_world_matrix(source)

        result = mm.compute_match(
            source_world=source_world,
            target_obj=active,
            channel_filter=cf,
            maintain_offset=False,
            respect_locks=p8.respect_locks if p8 else True,
            respect_drivers=p8.respect_drivers if p8 else True,
        )
        mm.apply_match_result(active, result)

        if p8 and p8.auto_key_switch:
            mm.key_match_result(active, result, context.scene.frame_current)

        self.report({"INFO"}, f"Matched '{active.name}' without offset ({len(result.channels_written)} channels)")
        return {"FINISHED"}


class AA_OT_p8_match_visual_matrix(bpy.types.Operator):
    """Match using visual (evaluated depsgraph) matrix."""
    bl_idname = "animassist.p8_match_visual_matrix"
    bl_label = "Match Visual Matrix"
    bl_description = "Match the active object using its visual matrix from the evaluated depsgraph."
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if not _match_poll(context, cls):
            return False
        selected = context.selected_objects
        if len(selected) < 2:
            cls.poll_message_set("Select a target, then the object to match")
            return False
        return True

    def execute(self, context):
        p8 = get_p8(context)
        active = context.active_object

        sources = [o for o in context.selected_objects if o != active]
        if not sources:
            self.report({"ERROR"}, "Select the target object as well as the active object")
            return {"CANCELLED"}

        source = sources[0]

        cf = _build_channel_filter(p8)
        source_world = mm.visual_world_matrix(source)

        result = mm.compute_match(
            source_world=source_world,
            target_obj=active,
            channel_filter=cf,
            maintain_offset=p8.maintain_offset if p8 else False,
            respect_locks=p8.respect_locks if p8 else True,
            respect_drivers=p8.respect_drivers if p8 else True,
        )
        mm.apply_match_result(active, result)

        if p8 and p8.auto_key_switch:
            mm.key_match_result(active, result, context.scene.frame_current)

        self.report({"INFO"}, f"Matched visual matrix of '{active.name}' ({len(result.channels_written)} channels)")
        return {"FINISHED"}


class AA_OT_p8_match_local_matrix(bpy.types.Operator):
    """Match using local matrix (unevaluated)."""
    bl_idname = "animassist.p8_match_local_matrix"
    bl_label = "Match Local Matrix"
    bl_description = "Match the active object using its local matrix without depsgraph evaluation."
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if not _match_poll(context, cls):
            return False
        selected = context.selected_objects
        if len(selected) < 2:
            cls.poll_message_set("Select a target, then the object to match")
            return False
        return True

    def execute(self, context):
        p8 = get_p8(context)
        active = context.active_object

        sources = [o for o in context.selected_objects if o != active]
        if not sources:
            self.report({"ERROR"}, "Select the target object as well as the active object")
            return {"CANCELLED"}

        source = sources[0]

        cf = _build_channel_filter(p8)
        # Use local matrix converted to world
        source_world = source.matrix_local.copy()

        result = mm.compute_match(
            source_world=source_world,
            target_obj=active,
            channel_filter=cf,
            maintain_offset=p8.maintain_offset if p8 else False,
            respect_locks=p8.respect_locks if p8 else True,
            respect_drivers=p8.respect_drivers if p8 else True,
        )
        mm.apply_match_result(active, result)

        if p8 and p8.auto_key_switch:
            mm.key_match_result(active, result, context.scene.frame_current)

        self.report({"INFO"}, f"Matched local matrix of '{active.name}' ({len(result.channels_written)} channels)")
        return {"FINISHED"}


class AA_OT_p8_match_opposite(bpy.types.Operator):
    """Match to the opposite-side bone by mirror naming."""
    bl_idname = "animassist.p8_match_opposite"
    bl_label = "Match Opposite"
    bl_description = "Match the active bone to its opposite-side mirror bone using naming conventions."
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if context.mode != 'POSE':
            return False
        return context.active_pose_bone is not None

    def execute(self, context):
        p8 = get_p8(context)
        bone = context.active_pose_bone

        if not bone:
            self.report({"ERROR"}, "No active bone. Select a bone in Pose mode")
            return {"CANCELLED"}

        # Find the mirror bone
        mirror_name = mm.mirror_name(bone.name)
        if not mirror_name:
            self.report({"ERROR"}, f"No mirror bone found for '{bone.name}'. Use .L/.R naming or add a pair override under Mirror & Symmetry")
            return {"CANCELLED"}

        obj = context.active_object
        arm = obj.data
        if mirror_name not in arm.bones:
            self.report({"ERROR"}, f"Mirror bone '{mirror_name}' is not in this armature. Add a pair override under Mirror & Symmetry")
            return {"CANCELLED"}

        cf = _build_channel_filter(p8)
        mirror_pb = obj.pose.bones[mirror_name]

        # Get mirror bone's visual world matrix
        source_world = mm.visual_world_matrix(mirror_pb)

        result = mm.compute_match(
            source_world=source_world,
            target_obj=bone,
            channel_filter=cf,
            maintain_offset=p8.maintain_offset if p8 else False,
            respect_locks=p8.respect_locks if p8 else True,
            respect_drivers=p8.respect_drivers if p8 else True,
        )
        mm.apply_match_result(bone, result)

        if p8 and p8.auto_key_switch:
            mm.key_match_result(bone, result, context.scene.frame_current)

        self.report({"INFO"}, f"Matched '{bone.name}' to opposite '{mirror_name}' ({len(result.channels_written)} channels)")
        return {"FINISHED"}


CLASSES: tuple[type, ...] = (
    AA_OT_p8_match_to_world,
    AA_OT_p8_match_to_parent,
    AA_OT_p8_match_to_target,
    AA_OT_p8_match_selected_to_active,
    AA_OT_p8_visual_match,
    AA_OT_p8_match_location,
    AA_OT_p8_match_rotation,
    AA_OT_p8_match_scale,
    AA_OT_p8_match_trs,
    AA_OT_p8_match_axis_filtered,
    AA_OT_p8_match_with_offset,
    AA_OT_p8_match_without_offset,
    AA_OT_p8_match_visual_matrix,
    AA_OT_p8_match_local_matrix,
    AA_OT_p8_match_opposite,
)

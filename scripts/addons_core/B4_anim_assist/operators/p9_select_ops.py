import bpy
from ..core.p9_properties import get_p9
from ..core import p9_pair_detect as det
from ..core.logging import get_logger
from ..core.bone_utils import set_pose_bone_selected


log = get_logger(__name__)


def _pose_poll(context):
    """Check we have an armature in pose mode with an active bone."""
    obj = context.active_object
    return (obj is not None and obj.type == "ARMATURE"
            and context.mode == "POSE" and obj.data.bones.active is not None)


def _get_opposite_name(context, bone_name):
    """Get opposite bone name using cache and properties."""
    p9 = get_p9(context)

    # Build overrides dict from properties
    overrides = {}
    if p9 and p9.pair_overrides:
        for item in p9.pair_overrides:
            if item.bone_a and item.bone_b:
                overrides[item.bone_a] = item.bone_b
                overrides[item.bone_b] = item.bone_a

    exceptions = {}
    if p9 and p9.naming_exceptions:
        for item in p9.naming_exceptions:
            if item.original and item.opposite:
                exceptions[item.original] = item.opposite
                exceptions[item.opposite] = item.original

    return det.find_opposite(bone_name, overrides=overrides, exceptions=exceptions)


class AA_OT_p9_select_opposite(bpy.types.Operator):
    """Deselect all and select the opposite-side bone of the currently active bone."""
    bl_idname = "animassist.p9_select_opposite"
    bl_label = "Select Opposite"
    bl_description = "Deselect all and select the opposite-side bone of the currently active bone."
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return _pose_poll(context)

    def execute(self, context):
        obj = context.active_object
        active_bone = obj.data.bones.active

        if not active_bone:
            self.report({"ERROR"}, "No active bone. Select a bone in Pose mode")
            return {"CANCELLED"}

        opposite_name = _get_opposite_name(context, active_bone.name)

        if not opposite_name:
            self.report({"ERROR"}, f"No opposite bone found for '{active_bone.name}'. Use .L/.R naming or add a pair override under Mirror & Symmetry")
            return {"CANCELLED"}

        # Check opposite bone exists
        if opposite_name not in obj.data.bones:
            self.report({"ERROR"}, f"Opposite bone '{opposite_name}' is not in this armature. Add a pair override under Mirror & Symmetry")
            return {"CANCELLED"}

        # Deselect all
        bpy.ops.pose.select_all(action="DESELECT")

        # Select opposite
        set_pose_bone_selected(obj.pose.bones[opposite_name], True)
        obj.data.bones.active = obj.data.bones[opposite_name]

        self.report({"INFO"}, f"Selected opposite: {opposite_name}")
        return {"FINISHED"}


class AA_OT_p9_add_opposite(bpy.types.Operator):
    """Add the opposite-side bones of all selected bones to the current selection."""
    bl_idname = "animassist.p9_add_opposite"
    bl_label = "Add Opposite to Selection"
    bl_description = "Add the opposite-side bones of all selected bones to the current selection."
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return _pose_poll(context)

    def execute(self, context):
        obj = context.active_object

        # Get all selected pose bones
        selected_bones = [pb.bone.name for pb in context.selected_pose_bones]

        if not selected_bones:
            self.report({"WARNING"}, "No bones selected")
            return {"FINISHED"}

        added_count = 0

        for bone_name in selected_bones:
            opposite_name = _get_opposite_name(context, bone_name)

            if opposite_name and opposite_name in obj.data.bones:
                set_pose_bone_selected(obj.pose.bones[opposite_name], True)
                added_count += 1

        self.report({"INFO"}, f"Added {added_count} opposite bones to selection")
        return {"FINISHED"}


class AA_OT_p9_swap_selection(bpy.types.Operator):
    """Replace the current selection with the opposite-side bones, swapping active and opposite."""
    bl_idname = "animassist.p9_swap_selection"
    bl_label = "Swap Selection"
    bl_description = "Replace the current selection with the opposite-side bones, swapping active and opposite."
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return _pose_poll(context)

    def execute(self, context):
        obj = context.active_object

        # Record current selection and active bone
        selected_bones = [pb.bone.name for pb in context.selected_pose_bones]
        active_bone_name = obj.data.bones.active.name if obj.data.bones.active else None

        if not selected_bones:
            self.report({"WARNING"}, "No bones selected")
            return {"FINISHED"}

        # Find opposites
        opposite_mapping = {}
        swapped_count = 0

        for bone_name in selected_bones:
            opposite_name = _get_opposite_name(context, bone_name)
            if opposite_name and opposite_name in obj.data.bones:
                opposite_mapping[bone_name] = opposite_name
                swapped_count += 1

        # Deselect all
        bpy.ops.pose.select_all(action="DESELECT")

        # Select all opposites
        for opposite_name in opposite_mapping.values():
            set_pose_bone_selected(obj.pose.bones[opposite_name], True)

        # Set active to opposite of previous active
        if active_bone_name and active_bone_name in opposite_mapping:
            opposite_active = opposite_mapping[active_bone_name]
            obj.data.bones.active = obj.data.bones[opposite_active]

        self.report({"INFO"}, f"Swapped {swapped_count} bones")
        return {"FINISHED"}


CLASSES: tuple[type, ...] = (
    AA_OT_p9_select_opposite,
    AA_OT_p9_add_opposite,
    AA_OT_p9_swap_selection,
)

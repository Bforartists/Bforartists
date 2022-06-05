# SPDX-License-Identifier: GPL-2.0-or-later

import bpy
import importlib

from ..utils.naming import Side, get_name_base_and_sides, mirror_name
from ..utils.misc import property_to_python

from ..utils.rig import get_rigify_type
from ..rig_lists import get_rig_class


# =============================================
# Single parameter copy button

class POSE_OT_rigify_copy_single_parameter(bpy.types.Operator):
    bl_idname = "pose.rigify_copy_single_parameter"
    bl_label = "Copy Option To Selected Rigs"
    bl_description = "Copy this property value to all selected rigs of the appropriate type"
    bl_options = {'UNDO', 'INTERNAL'}

    property_name: bpy.props.StringProperty(name='Property Name')
    mirror_bone: bpy.props.BoolProperty(name='Mirror As Bone Name')

    module_name: bpy.props.StringProperty(name='Module Name')
    class_name: bpy.props.StringProperty(name='Class Name')

    @classmethod
    def poll(cls, context):
        return (
            context.active_object and context.active_object.type == 'ARMATURE'
            and context.active_pose_bone
            and context.active_object.data.get('rig_id') is None
            and get_rigify_type(context.active_pose_bone)
        )

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        try:
            module = importlib.import_module(self.module_name)
            filter_rig_class = getattr(module, self.class_name)
        except (KeyError, AttributeError, ImportError):
            self.report(
                {'ERROR'}, f"Cannot find class {self.class_name} in {self.module_name}")
            return {'CANCELLED'}

        active_pbone = context.active_pose_bone
        active_split = get_name_base_and_sides(active_pbone.name)

        value = getattr(active_pbone.rigify_parameters, self.property_name)
        num_copied = 0

        # Copy to different bones of appropriate rig types
        for sel_pbone in context.selected_pose_bones:
            rig_type = get_rigify_type(sel_pbone)

            if rig_type and sel_pbone != active_pbone:
                rig_class = get_rig_class(rig_type)

                if rig_class and issubclass(rig_class, filter_rig_class):
                    new_value = value

                    # If mirror requested and copying to a different side bone, mirror the value
                    if self.mirror_bone and active_split.side != Side.MIDDLE and value:
                        sel_split = get_name_base_and_sides(sel_pbone.name)

                        if sel_split.side == -active_split.side:
                            new_value = mirror_name(value)

                    # Assign the final value
                    setattr(sel_pbone.rigify_parameters,
                            self.property_name, new_value)
                    num_copied += 1

        if num_copied:
            self.report({'INFO'}, f"Copied the value to {num_copied} bones.")
            return {'FINISHED'}
        else:
            self.report({'WARNING'}, "No suitable selected bones to copy to.")
            return {'CANCELLED'}


def make_copy_parameter_button(layout, property_name, *, base_class, mirror_bone=False):
    """Displays a button that copies the property to selected rig of the specified base type."""
    props = layout.operator(
        POSE_OT_rigify_copy_single_parameter.bl_idname, icon='DUPLICATE', text='')
    props.property_name = property_name
    props.mirror_bone = mirror_bone
    props.module_name = base_class.__module__
    props.class_name = base_class.__name__


def recursive_mirror(value):
    """Mirror strings(.L/.R) in any mixed structure of dictionaries/lists."""

    if isinstance(value, dict):
        return { key: recursive_mirror(val) for key, val in value.items() }

    elif isinstance(value, list):
        return [recursive_mirror(elem) for elem in value]

    elif isinstance(value, str):
        return mirror_name(value)

    else:
        return value


def copy_rigify_params(from_bone: bpy.types.PoseBone, to_bone: bpy.types.PoseBone, *, match_type=False, x_mirror=False) -> bool:
    rig_type = to_bone.rigify_type
    if match_type and to_bone.rigify_type != from_bone.rigify_type:
        return False
    else:
        rig_type = to_bone.rigify_type = get_rigify_type(from_bone)

    from_params = from_bone.get('rigify_parameters')
    if from_params and rig_type:
        param_dict = property_to_python(from_params)
        if x_mirror:
            param_dict = recursive_mirror(param_dict)
        to_bone['rigify_parameters'] = param_dict
    else:
        try:
            del to_bone['rigify_parameters']
        except KeyError:
            pass
    return True


class POSE_OT_rigify_mirror_parameters(bpy.types.Operator):
    """Mirror Rigify type and parameters of selected bones to the opposite side. Names should end in L/R"""

    bl_idname = "pose.rigify_mirror_parameters"
    bl_label = "Mirror Rigify Parameters"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.object
        if not obj or obj.type != 'ARMATURE' or obj.mode != 'POSE':
            return False
        sel_bones = context.selected_pose_bones
        if not sel_bones:
            return False
        for pb in sel_bones:
            mirrored_name = mirror_name(pb.name)
            if mirrored_name != pb.name and mirrored_name in obj.pose.bones:
                return True
        return False

    def execute(self, context):
        rig = context.object

        num_mirrored = 0

        # First make sure that all selected bones can be mirrored unambiguously.
        for pb in context.selected_pose_bones:
            flip_bone = rig.pose.bones.get(mirror_name(pb.name))
            if not flip_bone:
                # Bones without an opposite will just be ignored.
                continue
            if flip_bone != pb and flip_bone.bone.select:
                self.report(
                    {'ERROR'}, f"Bone {pb.name} selected on both sides, mirroring would be ambiguous, aborting. Only select the left or right side, not both!")
                return {'CANCELLED'}

        # Then mirror the parameters.
        for pb in context.selected_pose_bones:
            flip_bone = rig.pose.bones.get(mirror_name(pb.name))
            if flip_bone == pb or not flip_bone:
                # Bones without an opposite will just be ignored.
                continue

            num_mirrored += copy_rigify_params(pb, flip_bone, match_type=False, x_mirror=True)

        self.report({'INFO'}, f"Mirrored parameters of {num_mirrored} bones.")

        return {'FINISHED'}


class POSE_OT_rigify_copy_parameters(bpy.types.Operator):
    """Copy Rigify type and parameters from active to selected bones"""

    bl_idname = "pose.rigify_copy_parameters"
    bl_label = "Copy Rigify Parameters to Selected"
    bl_options = {'REGISTER', 'UNDO'}

    match_type: bpy.props.BoolProperty(
        name = "Match Type",
        description = "Only mirror rigify parameters to selected bones which have the same rigify type as the active bone",
        default = False
    )

    @classmethod
    def poll(cls, context):
        obj = context.object
        if not obj or obj.type != 'ARMATURE' or obj.mode != 'POSE':
            return False

        active = context.active_pose_bone
        if not active or not active.rigify_type:
            return False

        select = context.selected_pose_bones
        if len(select) < 2 or active not in select:
            return False

        return True

    def execute(self, context):
        active_bone = context.active_pose_bone

        num_copied = 0
        for pb in context.selected_pose_bones:
            if pb == active_bone:
                continue
            num_copied += copy_rigify_params(active_bone, pb, match_type=self.match_type)

        self.report({'INFO'}, f"Copied {active_bone.rigify_type} parameters to {num_copied} bones.")

        return {'FINISHED'}


def draw_copy_mirror_ops(self, context):
    layout = self.layout
    if context.mode == 'POSE':
        layout.separator()
        op = layout.operator(POSE_OT_rigify_copy_parameters.bl_idname,
                        icon='DUPLICATE', text="Copy Only Parameters")
        op.match_type = True
        op = layout.operator(POSE_OT_rigify_copy_parameters.bl_idname,
                        icon='DUPLICATE', text="Copy Type & Parameters")
        op.match_type = False
        layout.operator(POSE_OT_rigify_mirror_parameters.bl_idname,
                        icon='MOD_MIRROR', text="Mirror Type & Parameters")

# =============================================
# Registration

classes = (
    POSE_OT_rigify_copy_single_parameter,
    POSE_OT_rigify_mirror_parameters,
    POSE_OT_rigify_copy_parameters
)


def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

    bpy.types.VIEW3D_MT_rigify.append(draw_copy_mirror_ops)

def unregister():
    from bpy.utils import unregister_class
    for cls in classes:
        unregister_class(cls)

    bpy.types.VIEW3D_MT_rigify.remove(draw_copy_mirror_ops)

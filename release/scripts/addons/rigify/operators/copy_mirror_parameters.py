# ====================== BEGIN GPL LICENSE BLOCK ======================
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ======================= END GPL LICENSE BLOCK ========================

# <pep8 compliant>

import bpy
import importlib

from ..utils.naming import Side, get_name_base_and_sides, mirror_name

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


# =============================================
# Registration

classes = (
    POSE_OT_rigify_copy_single_parameter,
)


def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)


def unregister():
    from bpy.utils import unregister_class
    for cls in classes:
        unregister_class(cls)

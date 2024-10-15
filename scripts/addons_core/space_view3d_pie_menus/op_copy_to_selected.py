# SPDX-FileCopyrightText: 2016-2024 Blender Foundation
#
# SPDX-License-Identifier: GPL-3.0-or-later

from bpy.types import Operator
from bpy.props import StringProperty


class VIEW3D_OT_copy_property_to_selected(Operator):
    """Copy a property from active to all selected objects which have that property"""

    bl_idname = "view3d.copy_property_to_selected"
    bl_label = "Copy Property to Selected"
    bl_options = {'REGISTER', 'INTERNAL'}

    rna_path: StringProperty(
        name="RNA Path",
        description="RNA path to the property to be copied, relative to the object",
        default="",
        options={'SKIP_SAVE'}
    )

    @classmethod
    def poll(cls, context):
        if not context.active_object:
            cls.poll_message_set("No active object.")
            return False
        if list(context.selected_objects) == [context.active_object]:
            cls.poll_message_set("No selected objects.")
            return False
        return True

    def execute(self, context):
        active_obj = context.active_object

        try:
            prop_value = active_obj.path_resolve(self.rna_path)
        except ValueError:
            self.report({'ERROR'}, f"Property '{self.rna_path}' not found on active object.")
            return {'CANCELLED'}

        success_counter = 0
        for sel_obj in context.selected_objects:
            if sel_obj == active_obj:
                continue
            try:
                sel_obj.path_resolve(self.rna_path)
                parts = self.rna_path.split(".")
                owner = sel_obj
                for part in parts[:-1]:
                    owner = getattr(sel_obj, part)
                setattr(owner, parts[-1], prop_value)
                success_counter += 1
            except ValueError:
                # This object doesn't have this property.
                continue

        if success_counter > 0:
            self.report({'INFO'}, f"Copied property to {success_counter} objects.")
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, f"Property `{self.rna_path}` doesn't exist on any selected objects.")
            return {'CANCELLED'}

registry = [
    VIEW3D_OT_copy_property_to_selected,
]
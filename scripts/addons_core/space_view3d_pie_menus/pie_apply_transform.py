# SPDX-FileCopyrightText: 2016-2024 Blender Foundation
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy
from bpy.types import Menu, Operator
from .op_pie_wrappers import WM_OT_call_menu_pie_drag_only


class PIE_MT_apply_transforms(Menu):
    bl_idname = "PIE_MT_apply_transforms"
    bl_label = "Apply Transforms"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()
        # 4 - LEFT
        props = pie.operator("object.transform_apply", text="Rot/Scale", icon='CON_SIZELIKE')
        props.location, props.rotation, props.scale = (False, True, True)
        # 6 - RIGHT
        props = pie.operator(
            "object.transform_apply", text="Loc/Rot/Scale", icon='APPLYALL' #BFA - Icon Added
        )
        props.location, props.rotation, props.scale = (True, True, True)
        # 2 - BOTTOM
        pie.operator("object.apply_transforms_of_constraints", text="Soft-Apply Constraints", icon='CONSTRAINT')

        # 8 - TOP
        props = pie.operator(
            "object.transform_apply", text="Rotation", icon='APPLYROTATE' #BFA - Icon Added
        )
        props.location, props.rotation, props.scale = (False, True, False)
        # 7 - TOP - LEFT
        props = pie.operator(
            "object.transform_apply", text="Location", icon='APPLYMOVE' #BFA - Icon Added
        )
        props.location, props.rotation, props.scale = (True, False, False)
        # 9 - TOP - RIGHT
        props = pie.operator(
            "object.transform_apply", text="Scale", icon='APPLYSCALE' #BFA - Icon Added
        )
        props.location, props.rotation, props.scale = (False, False, True)
        # 1 - BOTTOM - LEFT
        if (
            context.active_object
            and context.active_object.type == 'EMPTY'
            and context.active_object.instance_type == 'COLLECTION'
            and context.active_object.instance_collection
        ):
            pie.operator('object.instancer_empty_to_collection', icon='LINKED')
        else:
            pie.operator(
                "object.make_single_user", text="Make Single-User", icon='DUPLICATE'
            ).obdata = True
        # 3 - BOTTOM - RIGHT
        pie.menu("PIE_MT_clear_transforms", text="Clear Transform Menu", icon='CLEAR') #BFA - Icon Added


class OBJECT_OT_apply_transforms_of_constraints(Operator):
    """Apply constraint transformation results to the object's local transformation matrix, such that the object won't move if its constraints are removed"""

    bl_idname = "object.apply_transforms_of_constraints"
    bl_label = "Apply Transforms of Constraints"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        if not any(
            [
                any([c.enabled and c.influence > 0 for c in obj.constraints])
                for obj in context.selected_objects
            ]
        ):
            cls.poll_message_set("No selected objects with enabled constraints.")
            return False
        return True

    def execute(self, context):
        # This is just a wrapper operator, to add a better tooltip and poll message.
        return bpy.ops.object.visual_transform_apply()


class OBJECT_OT_make_meshes_single_user(Operator):
    """Make real duplicates of multi-user meshes on selected objects"""

    bl_idname = "object.make_meshes_single_user"
    bl_label = "Make Meshes Single User"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        if not any(
            [obj.data and obj.data.users > 1 for obj in context.selected_objects]
        ):
            cls.poll_message_set("No selected objects with multi-user meshes.")
            return False
        return True

    def execute(self, context):
        # This is just a wrapper operator, to add a better tooltip and poll message.
        return bpy.ops.object.duplicates_make_real()


class OBJECT_OT_clear_all_transforms(Operator):
    bl_idname = "clear.all"
    bl_label = "Clear All Transforms"
    bl_description = "Clear All Transforms"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        bpy.ops.object.location_clear()
        bpy.ops.object.rotation_clear()
        bpy.ops.object.scale_clear()
        return {'FINISHED'}


class PIE_MT_clear_transforms(Menu):
    bl_idname = "PIE_MT_clear_menu"
    bl_label = "Clear Transforms"

    def draw(self, context):
        layout = self.layout
        layout.operator("object.clear_all_transforms", text="Clear All", icon='CLEAR') #BFA - Icon Added
        layout.operator("object.location_clear", text="Clear Location", icon='CLEARMOVE') #BFA - Icon Added
        layout.operator("object.rotation_clear", text="Clear Rotation", icon='CLEARROTATE') #BFA - Icon Added
        layout.operator("object.scale_clear", text="Clear Scale", icon='CLEARORIGIN') #BFA - Icon Added
        layout.operator("object.origin_clear", text="Clear Origin", icon='CLEARSCALE') #BFA - Icon Added



registry = (
    PIE_MT_apply_transforms,
    OBJECT_OT_apply_transforms_of_constraints,
    OBJECT_OT_make_meshes_single_user,
    OBJECT_OT_clear_all_transforms,
    PIE_MT_clear_transforms,
)


def register():
    WM_OT_call_menu_pie_drag_only.register_drag_hotkey(
        keymap_name="Object Mode",
        pie_name=PIE_MT_apply_transforms.bl_idname,
        hotkey_kwargs={'type': "A", 'value': "PRESS", 'ctrl': True},
        on_drag=False,
    )

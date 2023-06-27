# SPDX-FileCopyrightText: 2019-2023 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

import bpy
from bpy.types import (
        Operator,
        Menu,
        )
from bpy.props import (
        BoolProperty,
        StringProperty,
        )
from .object_menus import *

# ********** Object Armature Interactive Mode **********
class VIEW3D_MT_InteractiveModeArmature(Menu):
    bl_idname = "VIEW3D_MT_Object_Interactive_Armature"
    bl_label = "Interactive Mode"
    bl_description = "Menu of objects interactive mode"

    def draw(self, context):
        layout = self.layout

        layout.operator(VIEW3D_OT_SetObjectMode.bl_idname, text="Object", icon="OBJECT_DATAMODE").mode = "OBJECT"
        layout.operator(VIEW3D_OT_SetObjectMode.bl_idname, text="Edit", icon="EDITMODE_HLT").mode = "EDIT"
        layout.operator(VIEW3D_OT_SetObjectMode.bl_idname, text="Pose", icon="POSE_HLT").mode = "POSE"


# Armature Menu's #

class VIEW3D_MT_Edit_Armature(Menu):
    bl_label = "Armature"

    def draw(self, context):
        layout = self.layout
        toolsettings = context.tool_settings

#        layout.prop_menu_enum(toolsettings, "proportional_edit", icon="PROP_CON")
        layout.prop_menu_enum(toolsettings, "proportional_edit_falloff", icon="SMOOTHCURVE")
        layout.separator()

        layout.menu("VIEW3D_MT_bone_options_toggle", text="Bone Settings")
        layout.operator("armature.merge")
        layout.operator("armature.fill")
        layout.operator("armature.split")
        layout.operator("armature.separate")
        layout.operator("armature.switch_direction", text="Switch Direction")

        layout.operator_context = 'EXEC_AREA'
        layout.operator("armature.symmetrize")
        layout.separator()

        layout.operator("armature.delete")
        layout.separator()

        layout.operator_context = 'INVOKE_DEFAULT'
        layout.operator("armature.armature_layers")
        layout.operator("armature.bone_layers")


class VIEW3D_MT_EditArmatureTK(Menu):
    bl_label = "Armature Tools"

    def draw(self, context):
        layout = self.layout
        layout.operator("armature.subdivide", text="Subdivide")
        layout.operator("armature.extrude_move")
        layout.operator("armature.extrude_forked")
        layout.operator("armature.duplicate_move")
        layout.separator()
        layout.menu("VIEW3D_MT_edit_armature_delete")
        layout.separator()
        layout.operator("transform.transform",
                        text="Scale Envelope Distance").mode = 'BONE_SIZE'
        layout.operator("transform.transform",
                        text="Scale B-Bone Width").mode = 'BONE_SIZE'


# Armature Pose Menu's #

class VIEW3D_MT_Pose(Menu):
    bl_label = "Pose"

    def draw(self, context):
        layout = self.layout

        layout.menu("VIEW3D_MT_object_animation")
        layout.menu("VIEW3D_MT_pose_slide")
        layout.menu("VIEW3D_MT_pose_propagate")
        layout.menu("VIEW3D_MT_pose_motion")
        layout.separator()
        layout.menu("VIEW3D_MT_pose_group")
        layout.menu("VIEW3D_MT_object_parent")
        layout.separator()
        layout.menu("VIEW3D_MT_pose_ik")
        layout.menu("VIEW3D_MT_pose_constraints")
        layout.menu("VIEW3D_MT_PoseNames")
        layout.operator("pose.quaternions_flip")
        layout.operator_context = 'INVOKE_AREA'
        layout.separator()
        layout.operator("armature.armature_layers", text="Change Armature Layers...")
        layout.operator("pose.bone_layers", text="Change Bone Layers...")
        layout.separator()
        layout.menu("VIEW3D_MT_pose_showhide")
        layout.menu("VIEW3D_MT_bone_options_toggle", text="Bone Settings")


class VIEW3D_MT_PoseCopy(Menu):
    bl_label = "Pose Copy"

    def draw(self, context):
        layout = self.layout
        layout.operator("pose.copy")
        layout.operator("pose.paste")
        layout.operator("pose.paste",
                        text="Paste X-Flipped Pose").flipped = True


class VIEW3D_MT_PoseNames(Menu):
    bl_label = "Pose Names"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'EXEC_AREA'
        layout.operator("pose.autoside_names",
                        text="AutoName Left/Right").axis = 'XAXIS'
        layout.operator("pose.autoside_names",
                        text="AutoName Front/Back").axis = 'YAXIS'
        layout.operator("pose.autoside_names",
                        text="AutoName Top/Bottom").axis = 'ZAXIS'
        layout.operator("pose.flip_names")


# List The Classes #

classes = (
    VIEW3D_MT_Pose,
    VIEW3D_MT_PoseCopy,
    VIEW3D_MT_PoseNames,
    VIEW3D_MT_Edit_Armature,
    VIEW3D_MT_EditArmatureTK,
    VIEW3D_MT_InteractiveModeArmature,
)


# Register Classes & Hotkeys #
def register():
    for cls in classes:
        bpy.utils.register_class(cls)


# Unregister Classes & Hotkeys #
def unregister():

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()

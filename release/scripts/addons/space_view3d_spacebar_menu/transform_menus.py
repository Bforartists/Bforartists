# ##### BEGIN GPL LICENSE BLOCK #####
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
# ##### END GPL LICENSE BLOCK #####
# Contributed to by: meta-androcto, JayDez, sim88, sam, lijenstina, mkb, wisaac, CoDEmanX #


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


# Transform Menu's #
class VIEW3D_MT_TransformMenu(Menu):
    bl_label = "Transform"

    def draw(self, context):
        layout = self.layout
        layout.operator("transform.translate", text="Move")
        layout.operator("transform.rotate", text="Rotate")
        layout.operator("transform.resize", text="Scale")
        layout.separator()
        layout.menu("VIEW3D_MT_object_clear")
        layout.menu("VIEW3D_MT_object_apply")
        layout.separator()
        layout.operator("transform.translate", text="Move Texture Space").texture_space = True
        layout.operator("transform.resize", text="Scale Texture Space").texture_space = True
        layout.separator()
        layout.operator("object.randomize_transform")
        layout.operator("transform.tosphere", text="To Sphere")
        layout.operator("transform.shear", text="Shear")
        layout.operator("transform.bend", text="Bend")
        layout.operator("transform.push_pull", text="Push/Pull")
        layout.separator()
        layout.operator("object.align")
        layout.operator_context = 'EXEC_REGION_WIN'
        layout.operator("transform.transform",
                        text="Align to Transform Orientation").mode = 'ALIGN'


# ********** Transform Lite/Short **********
class VIEW3D_MT_TransformMenuLite(Menu):
    bl_label = "Transform"

    def draw(self, context):
        layout = self.layout
        layout.operator("transform.translate", text="Move")
        layout.operator("transform.rotate", text="Rotate")
        layout.operator("transform.resize", text="Scale")
        layout.separator()
        layout.menu("VIEW3D_MT_object_clear")
        layout.menu("VIEW3D_MT_object_apply")
        layout.separator()
        layout.operator("transform.transform",
                        text="Align to Transform Orientation").mode = 'ALIGN'


# ********** Transform Camera **********
class VIEW3D_MT_TransformMenuCamera(Menu):
    bl_label = "Transform"

    def draw(self, context):
        layout = self.layout
        layout.menu("VIEW3D_MT_object_clear")
        layout.menu("VIEW3D_MT_object_apply")
        layout.operator("transform.translate", text="Move")
        layout.operator("transform.rotate", text="Rotate")
        layout.operator("transform.resize", text="Scale")
        layout.operator("object.align")
        layout.operator_context = 'EXEC_REGION_WIN'
        layout.separator()
        layout.operator("transform.transform",
                        text="Align to Transform Orientation").mode = 'ALIGN'


# ********** Transform Armature  **********
class VIEW3D_MT_TransformMenuArmature(Menu):
    bl_label = "Transform"

    def draw(self, context):
        layout = self.layout
        layout.operator("transform.translate", text="Move")
        layout.operator("transform.rotate", text="Rotate")
        layout.operator("transform.resize", text="Scale")
        layout.separator()
        layout.operator("armature.align")
        layout.operator("object.align")
        layout.operator_context = 'EXEC_AREA'
        layout.separator()
        layout.operator("object.origin_set",
                        text="Geometry to Origin").type = 'GEOMETRY_ORIGIN'
        layout.operator("object.origin_set",
                        text="Origin to Geometry").type = 'ORIGIN_GEOMETRY'
        layout.operator("object.origin_set",
                        text="Origin to 3D Cursor").type = 'ORIGIN_CURSOR'
        layout.operator("object.origin_set",
                        text="Origin to Center of Mass").type = 'ORIGIN_CENTER_OF_MASS'


# ********** Transform Armature Edit **********
class VIEW3D_MT_TransformMenuArmatureEdit(Menu):
    bl_label = "Transform"

    def draw(self, context):
        layout = self.layout
        layout.operator("transform.translate", text="Move")
        layout.operator("transform.rotate", text="Rotate")
        layout.operator("transform.resize", text="Scale")
        layout.separator()
        layout.operator("transform.tosphere", text="To Sphere")
        layout.operator("transform.shear", text="Shear")
        layout.operator("transform.bend", text="Bend")
        layout.operator("transform.push_pull", text="Push/Pull")
        layout.operator("transform.vertex_warp", text="Warp")
        layout.separator()
        layout.operator("transform.vertex_random", text="Randomize")
        layout.operator("armature.align")
        layout.operator_context = 'EXEC_AREA'


# ********** Transform Armature Pose **********
class VIEW3D_MT_TransformMenuArmaturePose(Menu):
    bl_label = "Transform"

    def draw(self, context):
        layout = self.layout
        layout.operator("transform.translate", text="Move")
        layout.operator("transform.rotate", text="Rotate")
        layout.operator("transform.resize", text="Scale")
        layout.separator()
        layout.operator("pose.transforms_clear", text="Clear All")
        layout.operator("pose.loc_clear", text="Location")
        layout.operator("pose.rot_clear", text="Rotation")
        layout.operator("pose.scale_clear", text="Scale")

        layout.separator()

        layout.operator("pose.user_transforms_clear", text="Reset unkeyed")
        obj = context.object
        if obj.type == 'ARMATURE' and obj.mode in {'EDIT', 'POSE'}:
            if obj.data.display_type == 'BBONE':
                layout.operator("transform.transform", text="Scale BBone").mode = 'BONE_SIZE'
            elif obj.data.display_type == 'ENVELOPE':
                layout.operator("transform.transform", text="Scale Envelope Distance").mode = 'BONE_SIZE'
                layout.operator("transform.transform", text="Scale Radius").mode = 'BONE_ENVELOPE'


# List The Classes #

classes = (
    VIEW3D_MT_TransformMenu,
    VIEW3D_MT_TransformMenuArmature,
    VIEW3D_MT_TransformMenuArmatureEdit,
    VIEW3D_MT_TransformMenuArmaturePose,
    VIEW3D_MT_TransformMenuLite,
    VIEW3D_MT_TransformMenuCamera,
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

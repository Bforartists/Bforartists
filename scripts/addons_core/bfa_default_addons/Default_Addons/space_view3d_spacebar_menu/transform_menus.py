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
        layout.separator()
        layout.operator("object.align")
        layout.operator_context = 'EXEC_REGION_WIN'
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


# List The Classes #

classes = (
    VIEW3D_MT_TransformMenu,
    VIEW3D_MT_TransformMenuArmature,
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

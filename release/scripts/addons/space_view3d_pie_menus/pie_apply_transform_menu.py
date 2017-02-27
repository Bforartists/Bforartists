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

# <pep8 compliant>

bl_info = {
    "name": "Hotkey: 'Ctrl A'",
    "description": "Apply Transform Menu",
    #    "author": "pitiwazou, meta-androcto",
    #    "version": (0, 1, 0),
    "blender": (2, 77, 0),
    "location": "3D View",
    "warning": "",
    "wiki_url": "",
    "category": "Apply Transform Pie"
    }

import bpy
from bpy.types import (
        Menu,
        Operator,
        )

# Pie Apply Transforms - Ctrl + A


class PieApplyTransforms(Menu):
    bl_idname = "pie.applytranforms"
    bl_label = "Pie Apply Transforms"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()
        # 4 - LEFT
        pie.operator("apply.transformall", text="Apply All", icon='FREEZE')
        # 6 - RIGHT
        pie.operator("clear.all", text="Clear All", icon='MANIPUL')
        # 2 - BOTTOM
        pie.menu("applymore.menu", text="More")
        # 8 - TOP
        pie.operator("apply.transformrotation", text="Rotation", icon='MAN_ROT')
        # 7 - TOP - LEFT
        pie.operator("apply.transformlocation", text="Location", icon='MAN_TRANS')
        # 9 - TOP - RIGHT
        pie.operator("apply.transformscale", text="Scale", icon='MAN_SCALE')
        # 1 - BOTTOM - LEFT
        pie.operator("apply.transformrotationscale", text="Rotation/Scale")
        # 3 - BOTTOM - RIGHT
        pie.menu("clear.menu", text="Clear Transforms")

# Apply Transforms


class ApplyTransformLocation(Operator):
    bl_idname = "apply.transformlocation"
    bl_label = "Apply Transform Location"
    bl_description = "Apply Transform Location"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        bpy.ops.object.transform_apply(location=True, rotation=False, scale=False)
        return {'FINISHED'}

# Apply Transforms


class ApplyTransformRotation(Operator):
    bl_idname = "apply.transformrotation"
    bl_label = "Apply Transform Rotation"
    bl_description = "Apply Transform Rotation"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
        return {'FINISHED'}

# Apply Transforms


class ApplyTransformScale(Operator):
    bl_idname = "apply.transformscale"
    bl_label = "Apply Transform Scale"
    bl_description = "Apply Transform Scale"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        return {'FINISHED'}

# Apply Transforms


class ApplyTransformRotationScale(Operator):
    bl_idname = "apply.transformrotationscale"
    bl_label = "Apply Transform Rotation Scale"
    bl_description = "Apply Transform Rotation Scale"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
        return {'FINISHED'}

# Apply Transforms


class ApplyTransformAll(Operator):
    bl_idname = "apply.transformall"
    bl_label = "Apply All Transforms"
    bl_description = "Apply Transform All"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        return {'FINISHED'}

# More Menu


class TransformApplyMore(Menu):
    bl_idname = "applymore.menu"
    bl_label = "More Menu"

    def draw(self, context):
        layout = self.layout
        layout.operator("object.visual_transform_apply", text="Visual Transforms")
        layout.operator("object.duplicates_make_real", text="Make Duplicates Real")

# Clear Menu


class ClearMenu(Menu):
    bl_idname = "clear.menu"
    bl_label = "Clear Menu"

    def draw(self, context):
        layout = self.layout
        layout.operator("object.location_clear", text="Clear Location", icon='MAN_TRANS')
        layout.operator("object.rotation_clear", text="Clear Rotation", icon='MAN_ROT')
        layout.operator("object.scale_clear", text="Clear Scale", icon='MAN_SCALE')
        layout.operator("object.origin_clear", text="Clear Origin", icon='MANIPUL')

# Clear all


class ClearAll(Operator):
    bl_idname = "clear.all"
    bl_label = "Clear All"
    bl_description = "Clear All Transforms"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        bpy.ops.object.location_clear()
        bpy.ops.object.rotation_clear()
        bpy.ops.object.scale_clear()
        return {'FINISHED'}

classes = (
    PieApplyTransforms,
    ApplyTransformLocation,
    ApplyTransformRotation,
    ApplyTransformScale,
    ApplyTransformRotationScale,
    ApplyTransformAll,
    ClearMenu,
    ClearAll,
    TransformApplyMore,
    )

addon_keymaps = []


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    wm = bpy.context.window_manager

    if wm.keyconfigs.addon:
        # Apply Transform
        km = wm.keyconfigs.addon.keymaps.new(name='Object Mode')
        kmi = km.keymap_items.new('wm.call_menu_pie', 'A', 'PRESS', ctrl=True)
        kmi.properties.name = "pie.applytranforms"
#        kmi.active = True
        addon_keymaps.append((km, kmi))


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    wm = bpy.context.window_manager

    kc = wm.keyconfigs.addon
    if kc:
        km = kc.keymaps['Object Mode']
        for kmi in km.keymap_items:
            if kmi.idname == 'wm.call_menu_pie':
                if kmi.properties.name == "pie.applytranforms":
                    km.keymap_items.remove(kmi)

if __name__ == "__main__":
    register()

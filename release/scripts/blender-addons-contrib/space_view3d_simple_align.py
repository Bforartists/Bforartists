# AlingTools.py (c) 2009, 2010 Gabriel Beaudin (gabhead)
#
# ***** BEGIN GPL LICENSE BLOCK *****
#
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ***** END GPL LICENCE BLOCK *****

bl_info = {
    "name": "Simple Align",
    "author": "Gabriel Beaudin (gabhead)",
    "version": (0,1),
    "blender": (2, 75, 0),
    "location": "View3D > Tool Shelf > Addons",
    "description": "Align Selected Objects to Active Object",
    "warning": "",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/"
        "Scripts/3D interaction/Align_Tools",
    "tracker_url": "https://developer.blender.org/T22389",
    "category": "3D View"}

"""Align Selected Objects"""

import bpy


class AlignUi(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_label = "Simple Align"
    bl_context = "objectmode"
    bl_category = 'Tools'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        obj = context.object

        if obj != None:
            row = layout.row()
            row.label(text="Active object is: ", icon='OBJECT_DATA')
            row = layout.row()
            row.label(obj.name, icon='EDITMODE_HLT')

        layout.separator()

        col = layout.column()
        col.label(text="Align Loc + Rot:", icon='MANIPUL')


        col = layout.column(align=False)
        col.operator("object.align",text="XYZ")

        col = layout.column()
        col.label(text="Align Location:", icon='MAN_TRANS')

        col = layout.column_flow(columns=5,align=True)
        col.operator("object.align_location_x",text="X")
        col.operator("object.align_location_y",text="Y")
        col.operator("object.align_location_z",text="Z")
        col.operator("object.align_location_all",text="All")

        col = layout.column()
        col.label(text="Align Rotation:", icon='MAN_ROT')

        col = layout.column_flow(columns=5,align=True)
        col.operator("object.align_rotation_x",text="X")
        col.operator("object.align_rotation_y",text="Y")
        col.operator("object.align_rotation_z",text="Z")
        col.operator("object.align_rotation_all",text="All")

        col = layout.column()
        col.label(text="Align Scale:", icon='MAN_SCALE')

        col = layout.column_flow(columns=5,align=True)
        col.operator("object.align_objects_scale_x",text="X")
        col.operator("object.align_objects_scale_y",text="Y")
        col.operator("object.align_objects_scale_z",text="Z")
        col.operator("object.align_objects_scale_all",text="All")


##Align all
def main(context):
    for i in bpy.context.selected_objects:
        i.location = bpy.context.active_object.location
        i.rotation_euler = bpy.context.active_object.rotation_euler

## Align Location

def LocAll(context):
    for i in bpy.context.selected_objects:
        i.location = bpy.context.active_object.location

def LocX(context):
    for i in bpy.context.selected_objects:
        i.location.x = bpy.context.active_object.location.x

def LocY(context):
    for i in bpy.context.selected_objects:
        i.location.y = bpy.context.active_object.location.y

def LocZ(context):
    for i in bpy.context.selected_objects:
        i.location.z = bpy.context.active_object.location.z

## Aling Rotation
def RotAll(context):
    for i in bpy.context.selected_objects:
        i.rotation_euler = bpy.context.active_object.rotation_euler

def RotX(context):
    for i in bpy.context.selected_objects:
        i.rotation_euler.x = bpy.context.active_object.rotation_euler.x

def RotY(context):
    for i in bpy.context.selected_objects:
        i.rotation_euler.y = bpy.context.active_object.rotation_euler.y

def RotZ(context):
    for i in bpy.context.selected_objects:
        i.rotation_euler.z = bpy.context.active_object.rotation_euler.z
## Aling Scale
def ScaleAll(context):
    for i in bpy.context.selected_objects:
        i.scale = bpy.context.active_object.scale

def ScaleX(context):
    for i in bpy.context.selected_objects:
        i.scale.x = bpy.context.active_object.scale.x

def ScaleY(context):
    for i in bpy.context.selected_objects:
        i.scale.y = bpy.context.active_object.scale.y

def ScaleZ(context):
    for i in bpy.context.selected_objects:
        i.scale.z = bpy.context.active_object.scale.z

## Classes

## Align All Rotation And Location
class AlignOperator(bpy.types.Operator):
    """"""
    bl_idname = "object.align"
    bl_label = "Align Selected To Active"

    @classmethod
    def poll(cls, context):
        return context.active_object != None

    def execute(self, context):
        main(context)
        return {'FINISHED'}

#######################Align Location########################
## Align LocationAll
class AlignLocationOperator(bpy.types.Operator):
    """"""
    bl_idname = "object.align_location_all"
    bl_label = "Align Selected Location To Active"

    @classmethod
    def poll(cls, context):
        return context.active_object != None

    def execute(self, context):
        LocAll(context)
        return {'FINISHED'}
## Align LocationX
class AlignLocationXOperator(bpy.types.Operator):
    """"""
    bl_idname = "object.align_location_x"
    bl_label = "Align Selected Location X To Active"

    @classmethod
    def poll(cls, context):
        return context.active_object != None

    def execute(self, context):
        LocX(context)
        return {'FINISHED'}
## Align LocationY
class AlignLocationYOperator(bpy.types.Operator):
    """"""
    bl_idname = "object.align_location_y"
    bl_label = "Align Selected Location Y To Active"

    @classmethod
    def poll(cls, context):
        return context.active_object != None

    def execute(self, context):
        LocY(context)
        return {'FINISHED'}
## Align LocationZ
class AlignLocationZOperator(bpy.types.Operator):
    """"""
    bl_idname = "object.align_location_z"
    bl_label = "Align Selected Location Z To Active"

    @classmethod
    def poll(cls, context):
        return context.active_object != None

    def execute(self, context):
        LocZ(context)
        return {'FINISHED'}

#######################Align Rotation########################
## Align RotationAll
class AlignRotationOperator(bpy.types.Operator):
    """"""
    bl_idname = "object.align_rotation_all"
    bl_label = "Align Selected Rotation To Active"

    @classmethod
    def poll(cls, context):
        return context.active_object != None

    def execute(self, context):
        RotAll(context)
        return {'FINISHED'}
## Align RotationX
class AlignRotationXOperator(bpy.types.Operator):
    """"""
    bl_idname = "object.align_rotation_x"
    bl_label = "Align Selected Rotation X To Active"

    @classmethod
    def poll(cls, context):
        return context.active_object != None

    def execute(self, context):
        RotX(context)
        return {'FINISHED'}
## Align RotationY
class AlignRotationYOperator(bpy.types.Operator):
    """"""
    bl_idname = "object.align_rotation_y"
    bl_label = "Align Selected Rotation Y To Active"

    @classmethod
    def poll(cls, context):
        return context.active_object != None

    def execute(self, context):
        RotY(context)
        return {'FINISHED'}
## Align RotationZ
class AlignRotationZOperator(bpy.types.Operator):
    """"""
    bl_idname = "object.align_rotation_z"
    bl_label = "Align Selected Rotation Z To Active"

    @classmethod
    def poll(cls, context):
        return context.active_object != None

    def execute(self, context):
        RotZ(context)
        return {'FINISHED'}
#######################Align Scale########################
## Scale All
class AlignScaleOperator(bpy.types.Operator):
    """"""
    bl_idname = "object.align_objects_scale_all"
    bl_label = "Align Selected Scale To Active"

    @classmethod
    def poll(cls, context):
        return context.active_object != None

    def execute(self, context):
        ScaleAll(context)
        return {'FINISHED'}
## Align ScaleX
class AlignScaleXOperator(bpy.types.Operator):
    """"""
    bl_idname = "object.align_objects_scale_x"
    bl_label = "Align Selected Scale X To Active"

    @classmethod
    def poll(cls, context):
        return context.active_object != None

    def execute(self, context):
        ScaleX(context)
        return {'FINISHED'}
## Align ScaleY
class AlignScaleYOperator(bpy.types.Operator):
    """"""
    bl_idname = "object.align_objects_scale_y"
    bl_label = "Align Selected Scale Y To Active"

    @classmethod
    def poll(cls, context):
        return context.active_object != None

    def execute(self, context):
        ScaleY(context)
        return {'FINISHED'}
## Align ScaleZ
class AlignScaleZOperator(bpy.types.Operator):
    """"""
    bl_idname = "object.align_objects_scale_z"
    bl_label = "Align Selected Scale Z To Active"

    @classmethod
    def poll(cls, context):
        return context.active_object != None

    def execute(self, context):
        ScaleZ(context)
        return {'FINISHED'}

## registring
def register():
    bpy.utils.register_module(__name__)

    pass

def unregister():
    bpy.utils.unregister_module(__name__)

    pass

if __name__ == "__main__":
    register()

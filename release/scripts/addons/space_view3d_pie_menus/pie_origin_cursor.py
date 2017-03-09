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
    "name": "Hotkey: 'Shift S'",
    "description": "Cursor & Origin Snap/Place Menu",
    #    "author": "pitiwazou, meta-androcto",
    #    "version": (0, 1, 0),
    "blender": (2, 77, 0),
    "location": "3D View",
    "warning": "",
    "wiki_url": "",
    "category": "Cursor/Origin Pie"
    }

import bpy
from bpy.types import (
        Menu,
        Operator,
        )

# SnapCursSelToCenter1 thanks to Isaac Weaver (wisaac) D1963


class SnapCursSelToCenter1(Operator):
    """Snap 3D cursor and selected objects to the center \n"""\
        """Works only in Object Mode"""
    bl_idname = "view3d.snap_cursor_selected_to_center1"
    bl_label = "Snap Cursor & Selection to Center"

    @classmethod
    def poll(cls, context):
        return (context.mode == "OBJECT")

    def execute(self, context):
        context.space_data.cursor_location = (0, 0, 0)
        for obj in context.selected_objects:
            obj.location = (0, 0, 0)
        return {'FINISHED'}

# Pivot to selection


class PivotToSelection(Operator):
    bl_idname = "object.pivot2selection"
    bl_label = "Pivot To Selection"
    bl_description = "Pivot Point To Selection"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        saved_location = context.scene.cursor_location.copy()
        bpy.ops.view3d.snap_cursor_to_selected()
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
        context.scene.cursor_location = saved_location
        return {'FINISHED'}

# Pivot to Bottom


class PivotBottom(Operator):
    bl_idname = "object.pivotobottom"
    bl_label = "Pivot To Bottom"
    bl_description = "Set the Pivot Point To Lowest Point"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):

        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY')
        o = context.active_object
        init = 0
        for x in o.data.vertices:
            if init == 0:
                a = x.co.z
                init = 1
            elif x.co.z < a:
                a = x.co.z

        for x in o.data.vertices:
            x.co.z -= a

        o.location.z += a
        bpy.ops.object.mode_set(mode='EDIT')
        return {'FINISHED'}

# Pie Origin/Pivot - Shift + S


class PieOriginPivot(Menu):
    bl_idname = "pie.originpivot"
    bl_label = "Origin Menu"

    def draw(self, context):
        layout = self.layout
        obj = context.object
        pie = layout.menu_pie()
        if obj and obj.type == 'MESH':
            # 4 - LEFT
            pie.operator("object.origin_set", text="Origin to Center of Mass",
                         icon='BBOX').type = 'ORIGIN_CENTER_OF_MASS'
            # 6 - RIGHT
            pie.operator("object.origin_set", text="Origin To 3D Cursor", icon='CURSOR').type = 'ORIGIN_CURSOR'
            # 2 - BOTTOM
            pie.operator("object.pivotobottom", text="Origin to Bottom", icon='TRIA_DOWN')
            # 8 - TOP
            pie.operator("object.pivot2selection", text="Origin To Selection", icon='SNAP_INCREMENT')
            # 7 - TOP - LEFT
            pie.operator("object.origin_set", text="Geometry To Origin", icon='BBOX').type = 'GEOMETRY_ORIGIN'
            # 9 - TOP - RIGHT
            pie.operator("object.origin_set", text="Origin To Geometry", icon='ROTATE').type = 'ORIGIN_GEOMETRY'

        else:
            # 4 - LEFT
            pie.operator("object.origin_set", text="Origin to Center of Mass",
                         icon='BBOX').type = 'ORIGIN_CENTER_OF_MASS'
            # 6 - RIGHT
            pie.operator("object.origin_set", text="Origin To 3D Cursor", icon='CURSOR').type = 'ORIGIN_CURSOR'
            # 2 - BOTTOM
            pie.operator("object.pivot2selection", text="Origin To Selection", icon='SNAP_INCREMENT')
            # 8 - TOP
            pie.operator("object.origin_set", text="Origin To Geometry", icon='ROTATE').type = 'ORIGIN_GEOMETRY'
            # 7 - TOP - LEFT
            pie.operator("object.origin_set", text="Geometry To Origin", icon='BBOX').type = 'GEOMETRY_ORIGIN'


# Origin/Pivot menu1  - Shift + S
class OriginPivotMenu(Menu):
    bl_idname = "origin.pivotmenu"
    bl_label = "Cursor Menu"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()
        # 4 - LEFT
        pie.operator("view3d.snap_selected_to_cursor", text="Selection to Cursor",
                     icon='CLIPUV_HLT').use_offset = False
        # 6 - RIGHT
        pie.operator("view3d.snap_selected_to_cursor",
                     text="Selection to Cursor (Offset)", icon='CURSOR').use_offset = True
        # 2 - BOTTOM
        pie.operator("wm.call_menu_pie", text="Origin Pie", icon='ROTATECOLLECTION').name = "pie.originpivot"
        # 8 - TOP
        pie.operator("view3d.snap_cursor_to_center", text="Cursor to Center", icon='CLIPUV_DEHLT')
        # 7 - TOP - LEFT
        pie.operator("view3d.snap_cursor_to_selected", text="Cursor to Selected", icon='ROTACTIVE')
        # 9 - TOP - RIGHT
        pie.operator("view3d.snap_cursor_to_active", text="Cursor to Active", icon='BBOX')
        # 1 - BOTTOM - LEFT
        pie.operator("view3d.snap_cursor_selected_to_center1", text="Selected & Cursor to Center", icon='ALIGN')
        # 3 - BOTTOM - RIGHT
        pie.menu("snapgrid.menu", text="Snap Grid", icon='GRID')

# More Menu


class Snap_CursorGrid(Menu):
    bl_idname = "snapgrid.menu"
    bl_label = "More Menu"

    def draw(self, context):
        layout = self.layout
        layout.operator("view3d.snap_selected_to_grid", text="Selection to Grid", icon='GRID')
        layout.operator("view3d.snap_cursor_to_grid", text="Cursor to Grid", icon='GRID')

classes = (
    OriginPivotMenu,
    PieOriginPivot,
    PivotToSelection,
    PivotBottom,
    SnapCursSelToCenter1,
    Snap_CursorGrid,
    )

addon_keymaps = []


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    wm = bpy.context.window_manager

    if wm.keyconfigs.addon:
        # Origin/Pivot
        km = wm.keyconfigs.addon.keymaps.new(name='3D View Generic', space_type='VIEW_3D')
        kmi = km.keymap_items.new('wm.call_menu_pie', 'S', 'PRESS', shift=True)
        kmi.properties.name = "origin.pivotmenu"
#        kmi.active = True
        addon_keymaps.append((km, kmi))


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    wm = bpy.context.window_manager

    kc = wm.keyconfigs.addon
    if kc:
        km = kc.keymaps['3D View Generic']
        for kmi in km.keymap_items:
            if kmi.idname == 'wm.call_menu_pie':
                if kmi.properties.name == "origin.pivotmenu":
                    km.keymap_items.remove(kmi)


if __name__ == "__main__":
    register()

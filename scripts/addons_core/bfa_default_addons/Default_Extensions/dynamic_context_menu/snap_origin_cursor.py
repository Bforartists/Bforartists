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

# ********** Object Snap Cursor **********
class VIEW3D_MT_Snap_Context(Menu):
    bl_label = "Snapping"

    def draw(self, context):
        layout = self.layout
        toolsettings = context.tool_settings
        layout.prop(toolsettings, "use_snap")
        layout.prop(toolsettings, "snap_elements", expand=True)


class VIEW3D_MT_Snap_Origin(Menu):
    bl_label = "Snap Origin"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'EXEC_AREA'
        layout.operator("object.origin_set",
                        text="Geometry to Origin").type = 'GEOMETRY_ORIGIN'
        layout.separator()
        layout.operator("object.origin_set",
                        text="Origin to Geometry").type = 'ORIGIN_GEOMETRY'
        layout.operator("object.origin_set",
                        text="Origin to 3D Cursor").type = 'ORIGIN_CURSOR'
        layout.operator("object.origin_set",
                        text="Origin to Center of Mass").type = 'ORIGIN_CENTER_OF_MASS'


class VIEW3D_MT_CursorMenu(Menu):
    bl_label = "Snap To"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'
        layout.menu("VIEW3D_MT_Snap_Origin")
        layout.menu("VIEW3D_MT_Snap_Context")
        layout.separator()
        layout.operator("view3d.snap_cursor_to_selected",
                        text="Cursor to Selected")
        layout.operator("view3d.snap_cursor_to_center",
                        text="Cursor to World Origin")
        layout.operator("view3d.snap_cursor_to_grid",
                        text="Cursor to Grid")
        layout.operator("view3d.snap_cursor_to_active",
                        text="Cursor to Active")
        layout.separator()
        layout.operator("view3d.snap_selected_to_cursor",
                        text="Selection to Cursor").use_offset = False
        layout.operator("view3d.snap_selected_to_cursor",
                        text="Selection to Cursor (Keep Offset)").use_offset = True
        layout.operator("view3d.snap_selected_to_grid",
                        text="Selection to Grid")
        layout.operator("view3d.snap_cursor_selected_to_center",
                        text="Selection and Cursor to World Origin")


class VIEW3D_MT_CursorMenuLite(Menu):
    bl_label = "Snap to"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'
        layout.menu("VIEW3D_MT_Snap_Origin")
        layout.separator()
        layout.operator("view3d.snap_cursor_to_selected",
                        text="Cursor to Selected")
        layout.operator("view3d.snap_cursor_to_center",
                        text="Cursor to World Origin")
        layout.operator("view3d.snap_cursor_to_grid",
                        text="Cursor to Grid")
        layout.operator("view3d.snap_cursor_to_active",
                        text="Cursor to Active")
        layout.separator()
        layout.operator("view3d.snap_selected_to_cursor",
                        text="Selection to Cursor").use_offset = False
        layout.operator("view3d.snap_selected_to_cursor",
                        text="Selection to Cursor (Keep Offset)").use_offset = True
        layout.operator("view3d.snap_selected_to_grid",
                        text="Selection to Grid")
        layout.operator("view3d.snap_cursor_selected_to_center",
                        text="Selection and Cursor to World Origin")


# Code thanks to Isaac Weaver (wisaac) D1963
class VIEW3D_OT_SnapCursSelToCenter(Operator):
    bl_idname = "view3d.snap_cursor_selected_to_center"
    bl_label = "Snap Cursor & Selection to World Origin"
    bl_description = ("Snap 3D cursor and selected objects to the center \n"
                    "Works only in Object Mode")

    @classmethod
    def poll(cls, context):
        return (context.area.type == "VIEW_3D" and context.mode == "OBJECT")

    def execute(self, context):
        context.scene.cursor.location = (0, 0, 0)
        for obj in context.selected_objects:
            obj.location = (0, 0, 0)
        return {'FINISHED'}


# Cursor Edge Intersection Defs #

def abs(val):
    if val > 0:
        return val
    return -val


def edgeIntersect(context, operator):
    from mathutils.geometry import intersect_line_line

    obj = context.active_object

    if (obj.type != "MESH"):
        operator.report({'ERROR'}, "Object must be a mesh")
        return None

    edges = []
    mesh = obj.data
    verts = mesh.vertices

    is_editmode = (obj.mode == 'EDIT')
    if is_editmode:
        bpy.ops.object.mode_set(mode='OBJECT')

    for e in mesh.edges:
        if e.select:
            edges.append(e)

            if len(edges) > 2:
                break

    if is_editmode:
        bpy.ops.object.mode_set(mode='EDIT')

    if len(edges) != 2:
        operator.report({'ERROR'},
                        "Operator requires exactly 2 edges to be selected")
        return

    line = intersect_line_line(verts[edges[0].vertices[0]].co,
                            verts[edges[0].vertices[1]].co,
                            verts[edges[1].vertices[0]].co,
                            verts[edges[1].vertices[1]].co)

    if line is None:
        operator.report({'ERROR'}, "Selected edges do not intersect")
        return

    point = line[0].lerp(line[1], 0.5)
    context.scene.cursor.location = obj.matrix_world @ point


# Cursor Edge Intersection Operator #
class VIEW3D_OT_CursorToEdgeIntersection(Operator):
    bl_idname = "view3d.snap_cursor_to_edge_intersection"
    bl_label = "Cursor to Edge Intersection"
    bl_description = "Finds the mid-point of the shortest distance between two edges"

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj is not None and obj.type == 'MESH')

    def execute(self, context):
        # Prevent unsupported Execution in Local View modes
        space = bpy.context.space_data
        if space.local_view:
            self.report({'INFO'}, 'Global Perspective modes only unable to continue.')
            return {'FINISHED'}
        edgeIntersect(context, self)
        return {'FINISHED'}


# Origin To Selected Edit Mode #
def vfeOrigin(context):
    try:
        cursorPositionX = context.scene.cursor.location[0]
        cursorPositionY = context.scene.cursor.location[1]
        cursorPositionZ = context.scene.cursor.location[2]
        bpy.ops.view3d.snap_cursor_to_selected()
        bpy.ops.object.mode_set()
        bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')
        bpy.ops.object.mode_set(mode='EDIT')
        context.scene.cursor.location[0] = cursorPositionX
        context.scene.cursor.location[1] = cursorPositionY
        context.scene.cursor.location[2] = cursorPositionZ
        return True
    except:
        return False


class VIEW3D_OT_SetOriginToSelected(Operator):
    bl_idname = "object.setorigintoselected"
    bl_label = "Set Origin to Selected"
    bl_description = "Set Origin to Selected"

    @classmethod
    def poll(cls, context):
        return (context.area.type == "VIEW_3D" and context.active_object is not None)

    def execute(self, context):
        check = vfeOrigin(context)
        if not check:
            self.report({"ERROR"}, "Set Origin to Selected could not be performed")
            return {'CANCELLED'}

        return {'FINISHED'}

# ********** Edit Mesh Cursor **********
class VIEW3D_MT_EditCursorMenu(Menu):
    bl_label = "Snap To"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'
        layout.operator("object.setorigintoselected",
                        text="Origin to Selected V/F/E")
        layout.separator()
        layout.menu("VIEW3D_MT_Snap_Origin")
        layout.menu("VIEW3D_MT_Snap_Context")
        layout.separator()
        layout.operator("view3d.snap_cursor_to_selected",
                        text="Cursor to Selected")
        layout.operator("view3d.snap_cursor_to_center",
                        text="Cursor to World Origin")
        layout.operator("view3d.snap_cursor_to_grid",
                        text="Cursor to Grid")
        layout.operator("view3d.snap_cursor_to_active",
                        text="Cursor to Active")
        layout.operator("view3d.snap_cursor_to_edge_intersection",
                        text="Cursor to Edge Intersection")
        layout.separator()
        layout.operator("view3d.snap_selected_to_cursor",
                        text="Selection to Cursor").use_offset = False
        layout.operator("view3d.snap_selected_to_cursor",
                        text="Selection to Cursor (Keep Offset)").use_offset = True
        layout.operator("view3d.snap_selected_to_grid",
                        text="Selection to Grid")


# List The Classes #

classes = (
    VIEW3D_MT_CursorMenu,
    VIEW3D_MT_CursorMenuLite,
    VIEW3D_MT_Snap_Context,
    VIEW3D_MT_Snap_Origin,
    VIEW3D_OT_SnapCursSelToCenter,
    VIEW3D_OT_CursorToEdgeIntersection,
    VIEW3D_OT_SetOriginToSelected,
    VIEW3D_MT_EditCursorMenu,
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

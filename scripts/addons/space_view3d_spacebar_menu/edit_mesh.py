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
from .snap_origin_cursor import *


# Edit Mode Menu's #

# ********** Edit Multiselect **********
class VIEW3D_MT_Edit_Multi(Menu):
    bl_label = "Mode Select"

    def draw(self, context):
        layout = self.layout

        layout.operator("selectedit.vertex", text="Vertex", icon='VERTEXSEL')
        layout.operator("selectedit.edge", text="Edge", icon='EDGESEL')
        layout.operator("selectedit.face", text="Face", icon='FACESEL')
        layout.operator("selectedit.vertsfaces", text="Vertex/Faces", icon='VERTEXSEL')
        layout.operator("selectedit.vertsedges", text="Vertex/Edges", icon='EDGESEL')
        layout.operator("selectedit.edgesfaces", text="Edges/Faces", icon='FACESEL')
        layout.operator("selectedit.vertsedgesfaces", text="Vertex/Edges/Faces", icon='OBJECT_DATAMODE')


# ********** Edit Mesh Edge **********
class VIEW3D_MT_EditM_Edge(Menu):
    bl_label = "Edges"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'

        layout.operator("mesh.mark_seam")
        layout.operator("mesh.mark_seam", text="Clear Seam").clear = True
        layout.separator()

        layout.operator("mesh.mark_sharp")
        layout.operator("mesh.mark_sharp", text="Clear Sharp").clear = True
        layout.operator("mesh.extrude_move_along_normals", text="Extrude")
        layout.separator()

        layout.operator("mesh.edge_rotate",
                        text="Rotate Edge CW").direction = 'CW'
        layout.operator("mesh.edge_rotate",
                        text="Rotate Edge CCW").direction = 'CCW'
        layout.separator()

        layout.operator("TFM_OT_edge_slide", text="Edge Slide")
        layout.operator("mesh.loop_multi_select", text="Edge Loop")
        layout.operator("mesh.loop_multi_select", text="Edge Ring").ring = True
        layout.operator("mesh.loop_to_region")
        layout.operator("mesh.region_to_loop")


# multiple edit select modes.
class VIEW3D_OT_selecteditVertex(Operator):
    bl_idname = "selectedit.vertex"
    bl_label = "Vertex Mode"
    bl_description = "Vert Select"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if context.object.mode != "EDIT":
            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
        if bpy.ops.mesh.select_mode != "EDGE, FACE":
            bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
            return {'FINISHED'}


class VIEW3D_OT_selecteditEdge(Operator):
    bl_idname = "selectedit.edge"
    bl_label = "Edge Mode"
    bl_description = "Edge Select"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if context.object.mode != "EDIT":
            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='EDGE')
        if bpy.ops.mesh.select_mode != "VERT, FACE":
            bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='EDGE')
            return {'FINISHED'}


class VIEW3D_OT_selecteditFace(Operator):
    bl_idname = "selectedit.face"
    bl_label = "Multiedit Face"
    bl_description = "Face Mode"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if context.object.mode != "EDIT":
            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')
        if bpy.ops.mesh.select_mode != "VERT, EDGE":
            bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')
            return {'FINISHED'}


# Components Multi Selection Mode
class VIEW3D_OT_selecteditVertsEdges(Operator):
    bl_idname = "selectedit.vertsedges"
    bl_label = "Verts Edges Mode"
    bl_description = "Vert/Edge Select"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if context.object.mode != "EDIT":
            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
        if bpy.ops.mesh.select_mode != "VERT, EDGE, FACE":
            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
            bpy.ops.mesh.select_mode(use_extend=True, use_expand=False, type='EDGE')
            return {'FINISHED'}


class VIEW3D_OT_selecteditEdgesFaces(Operator):
    bl_idname = "selectedit.edgesfaces"
    bl_label = "Edges Faces Mode"
    bl_description = "Edge/Face Select"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if context.object.mode != "EDIT":
            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='EDGE')
        if bpy.ops.mesh.select_mode != "VERT, EDGE, FACE":
            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='EDGE')
            bpy.ops.mesh.select_mode(use_extend=True, use_expand=False, type='FACE')
            return {'FINISHED'}


class VIEW3D_OT_selecteditVertsFaces(Operator):
    bl_idname = "selectedit.vertsfaces"
    bl_label = "Verts Faces Mode"
    bl_description = "Vert/Face Select"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if context.object.mode != "EDIT":
            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
        if bpy.ops.mesh.select_mode != "VERT, EDGE, FACE":
            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
            bpy.ops.mesh.select_mode(use_extend=True, use_expand=False, type='FACE')
            return {'FINISHED'}


class VIEW3D_OT_selecteditVertsEdgesFaces(Operator):
    bl_idname = "selectedit.vertsedgesfaces"
    bl_label = "Verts Edges Faces Mode"
    bl_description = "Vert/Edge/Face Select"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if context.object.mode != "EDIT":
            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
        if bpy.ops.mesh.select_mode != "VERT, EDGE, FACE":
            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
            bpy.ops.mesh.select_mode(use_extend=True, use_expand=False, type='EDGE')
            bpy.ops.mesh.select_mode(use_extend=True, use_expand=False, type='FACE')
            return {'FINISHED'}


# List The Classes #

classes = (
    VIEW3D_MT_Edit_Multi,
    VIEW3D_MT_EditM_Edge,
    VIEW3D_OT_selecteditVertex,
    VIEW3D_OT_selecteditEdge,
    VIEW3D_OT_selecteditFace,
    VIEW3D_OT_selecteditVertsEdges,
    VIEW3D_OT_selecteditEdgesFaces,
    VIEW3D_OT_selecteditVertsFaces,
    VIEW3D_OT_selecteditVertsEdgesFaces,
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

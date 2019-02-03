# -*- coding: utf-8 -*-
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


import bpy
from bpy.types import (
        Panel,
        Menu,
        )
from .ui_utils import GUI


class VIEW3D_PT_cursor(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = "Cursor Target"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(self, context):
        # Display in object or edit mode.
        if (context.area.type == 'VIEW_3D' and
                (context.mode == 'EDIT_MESH' or
                 context.mode == 'OBJECT')):
            return True

        return False

    def draw_header(self, context):
        pass

    def draw(self, context):
        layout = self.layout
        sce = context.scene

        cc = sce.cursor_control
        (tvs, tes, tfs, edit_mode) = cc.guiStates(context)

        # Mesh data elements
        if edit_mode:
            row = layout.row()
            GUI.drawIconButton(
                    tvs >= 1, row, 'STICKY_UVS_DISABLE',
                    "view3d.cursor_to_vertex"
                    )
            GUI.drawIconButton(
                    tvs == 2 or tes >= 1, row, 'MESH_DATA',
                    "view3d.cursor_to_line"
                    )
            GUI.drawIconButton(
                    tvs == 2 or tes >= 1, row, 'OUTLINER_OB_MESH',
                    "view3d.cursor_to_edge"
                    )
            GUI.drawIconButton(
                    tvs == 3 or tfs >= 1, row, 'SNAP_FACE',
                    "view3d.cursor_to_plane"
                    )
            GUI.drawIconButton(
                    tvs == 3 or tfs >= 1, row, 'FACESEL',
                    "view3d.cursor_to_face"
                    )

        # Geometry from mesh
        if edit_mode:
            row = layout.row()
            GUI.drawIconButton(
                    tvs <= 3 or tfs == 1, row, 'MOD_MIRROR',
                    "view3d.cursor_to_sl_mirror"
                    )
            GUI.drawIconButton(
                    tes == 2, row, 'PARTICLE_TIP',
                    "view3d.cursor_to_linex"
                    )
            GUI.drawIconButton(
                    tvs > 1, row, 'ROTATECENTER',
                    "view3d.cursor_to_vertex_median"
                    )  # EDITMODE_HLT
            GUI.drawIconButton(
                    tvs == 3 or tvs == 4, row, 'FORCE_FORCE',
                    "view3d.cursor_to_spherecenter"
                    )
            GUI.drawIconButton(
                    tvs == 3 or tvs == 4, row, 'MATERIAL',
                    "view3d.cursor_to_perimeter"
                    )

        # Objects
        """
        row = layout.row()

        GUI.drawIconButton(
                context.active_object is not None, row, 'ROTATE',
                "view3d.cursor_to_active_object_center"
                )
        GUI.drawIconButton(
                len(context.selected_objects) > 1, row, 'ROTATECOLLECTION',
                "view3d.cursor_to_selection_midpoint"
                )
        GUI.drawIconButton(
                len(context.selected_objects) > 1, row, 'ROTATECENTER',
                "view3d.cursor_to_selection_midpoint"
                )
        """
        # References World Origin, Object Origin, SL and CL
        row = layout.row()
        GUI.drawIconButton(True, row, 'WORLD_DATA', "view3d.cursor_to_origin")
        GUI.drawIconButton(
                context.active_object is not None, row, 'ROTACTIVE',
                "view3d.cursor_to_active_object_center"
                )
        GUI.drawIconButton(True, row, 'CURSOR', "view3d.cursor_to_sl")

        """
        GUI.drawIconButton(True, row, 'GRID', "view3d.cursor_sl_recall")
        GUI.drawIconButton(True, row, 'SNAP_INCREMENT', "view3d.cursor_sl_recall")
        row.label("(" + str(cc.linexChoice) + ")")
        """
        cc = context.scene.cursor_control
        if cc.linexChoice >= 0:
            col = row.column()
            col.enabled = False
            col.prop(cc, "linexChoice")

        # Limit/Clamping Properties
        row = layout.row()
        row.prop(cc, "stepLengthEnable")
        if (cc.stepLengthEnable):
            row = layout.row()
            row.prop(cc, "stepLengthMode")
            row.prop(cc, "stepLengthValue")
            row = layout.row()
            GUI.drawTextButton(True, row, '1/Phi', "view3d.cursor_stepval_phinv")
            GUI.drawTextButton(True, row, 'Phi', "view3d.cursor_stepval_phi")
            GUI.drawTextButton(True, row, 'Phi²', "view3d.cursor_stepval_phi2")
            GUI.drawIconButton(tvs == 2, row, 'EDGESEL', "view3d.cursor_stepval_vvdist")


class VIEW3D_PT_ccDelta(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = "Cursor Delta"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(self, context):
        # Display in object or edit mode.
        if (context.area.type == 'VIEW_3D' and
                (context.mode == 'EDIT_MESH' or
                 context.mode == 'OBJECT')):
            return True

        return False

    def draw_header(self, context):
        pass

    def draw(self, context):
        layout = self.layout

        cc = context.scene.cursor_control
        (tvs, tes, tfs, edit_mode) = cc.guiStates(context)

        row = layout.row()
        col = row.column()
        GUI.drawIconButton(True, col, 'FF', "view3d.ccdelta_add")
        GUI.drawIconButton(True, col, 'REW', "view3d.ccdelta_sub")
        GUI.drawIconButton(tvs <= 2, col, 'FORWARD', "view3d.ccdelta_vvdist")

        col = row.column()
        col.prop(cc, "deltaVector")

        col = row.column()
        GUI.drawIconButton(True, col, 'MOD_MIRROR', "view3d.ccdelta_invert")
        GUI.drawIconButton(True, col, 'SNAP_NORMAL', "view3d.ccdelta_normalize")


class CursorControlMenu(Menu):
    bl_idname = "cursor_control_calls"
    bl_label = "Cursor Control"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'

        """
        layout.operator(VIEW3D_OT_cursor_to_vertex.bl_idname, text = "Vertex")
        layout.operator(VIEW3D_OT_cursor_to_line.bl_idname, text = "Line")
        obj = context.active_object
        if (context.mode == 'EDIT_MESH'):
            if (obj and obj.type=='MESH' and obj.data):
        """
        cc = context.scene.cursor_control
        (tvs, tes, tfs, edit_mode) = cc.guiStates(context)

        if(edit_mode):
            if (tvs >= 1):
                layout.operator("view3d.cursor_to_vertex", text="Closest Vertex")
            if (tvs == 2 or tes >= 1):
                layout.operator("view3d.cursor_to_line", text="Closest Line")
            if (tvs == 2 or tes >= 1):
                layout.operator("view3d.cursor_to_edge", text="Closest Edge")
            if (tvs == 3 or tfs >= 1):
                layout.operator("view3d.cursor_to_plane", text="Closest Plane")
            if (tvs == 3 or tfs >= 1):
                layout.operator("view3d.cursor_to_face", text="Closest Face")

        if(edit_mode):
            if (tvs <= 3 or tfs == 1):
                layout.operator("view3d.cursor_to_sl_mirror", text="Mirror")
            if (tes == 2):
                layout.operator("view3d.cursor_to_linex", text="Line Intersection")
            if (tvs > 1):
                layout.operator("view3d.cursor_to_vertex_median", text="Vertex Median")
            if (tvs == 3 or tvs == 4):
                layout.operator("view3d.cursor_to_spherecenter", text="Circle Center")
            if (tvs == 3 or tvs == 4):
                layout.operator("view3d.cursor_to_perimeter", text="Circle Perimeter")

        layout.operator("view3d.cursor_to_origin", text="World Origin")
        layout.operator("view3d.cursor_to_active_object_center", text="Active Object")
        layout.operator("view3d.cursor_to_sl", text="Cursor Memory")


def menu_callback(self, context):
    self.layout.menu(CursorControlMenu.bl_idname, icon="PLUGIN")

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

"""
  TODO:

      IDEAS:
      Add/Subtract

      LATER:

      ISSUES:
          Bugs:
          Mites:
          CTRL-Z forces memory to world origin (0,0,0)... why??
          Happens only if undo reaches 'default world state'
          How to Reproduce:
              1. File->New
              2. Move 3D-cursor
              3. Set memory
              4. Move cube
              5. CTRL-Z

      QUESTIONS:
"""

import bpy
import bgl
from bpy.props import (
        BoolProperty,
        FloatVectorProperty,
        )
from bpy.types import (
        Operator,
        PropertyGroup,
        Panel,
        )
from mathutils import Vector
from .misc_utils import (
        BlenderFake,
        region3d_get_2d_coordinates,
        )
from .constants_utils import PHI_INV
from .cursor_utils import CursorAccess
from .ui_utils import GUI

PRECISION = 4


class CursorMemoryData(PropertyGroup):
    savedLocationDraw = BoolProperty(
            description="Draw SL cursor in 3D view",
            default=1
            )
    savedLocation = FloatVectorProperty(
            name="",
            description="Saved Location",
            precision=PRECISION
            )


class VIEW3D_OT_cursor_memory_save(Operator):
    """Save cursor location"""
    bl_idname = "view3d.cursor_memory_save"
    bl_label = "Save cursor location"
    bl_options = {'REGISTER'}

    def modal(self, context, event):
        return {'FINISHED'}

    def execute(self, context):
        if CursorAccess.getCursor() is None:
            self.report({'WARNING'},
                        "Cursor location cannot be retrieved. Operation Cancelled")
            return {"CANCELLED"}

        cc = context.scene.cursor_memory
        cc.savedLocation = CursorAccess.getCursor()
        CursorAccess.setCursor(cc.savedLocation)
        return {'FINISHED'}


class VIEW3D_OT_cursor_memory_swap(Operator):
    """Swap cursor location"""
    bl_idname = "view3d.cursor_memory_swap"
    bl_label = "Swap cursor location"
    bl_options = {'REGISTER'}

    def modal(self, context, event):
        return {'FINISHED'}

    def execute(self, context):

        if CursorAccess.getCursor() is None:
            self.report({'WARNING'},
                        "Cursor location cannot be retrieved. Operation Cancelled")
            return {"CANCELLED"}

        location = CursorAccess.getCursor().copy()
        cc = context.scene.cursor_memory
        CursorAccess.setCursor(cc.savedLocation)
        cc.savedLocation = location
        return {'FINISHED'}


class VIEW3D_OT_cursor_memory_recall(Operator):
    """Recall cursor location"""
    bl_idname = "view3d.cursor_memory_recall"
    bl_label = "Recall cursor location"
    bl_options = {'REGISTER'}

    def modal(self, context, event):
        return {'FINISHED'}

    def execute(self, context):
        cc = context.scene.cursor_memory
        CursorAccess.setCursor(cc.savedLocation)
        return {'FINISHED'}


class VIEW3D_OT_cursor_memory_show(Operator):
    """Show cursor memory"""
    bl_idname = "view3d.cursor_memory_show"
    bl_label = "Show cursor memory"
    bl_options = {'REGISTER'}

    def modal(self, context, event):
        return {'FINISHED'}

    def execute(self, context):
        cc = context.scene.cursor_memory
        cc.savedLocationDraw = True
        BlenderFake.forceRedraw()
        return {'FINISHED'}


class VIEW3D_OT_cursor_memory_hide(Operator):
    """Hide cursor memory"""
    bl_idname = "view3d.cursor_memory_hide"
    bl_label = "Hide cursor memory"
    bl_options = {'REGISTER'}

    def modal(self, context, event):
        return {'FINISHED'}

    def execute(self, context):
        cc = context.scene.cursor_memory
        cc.savedLocationDraw = False
        BlenderFake.forceRedraw()
        return {'FINISHED'}


class VIEW3D_PT_cursor_memory(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = "Cursor Memory"
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
        layout = self.layout
        cc = context.scene.cursor_memory
        if cc.savedLocationDraw:
            GUI.drawIconButton(True, layout, 'RESTRICT_VIEW_OFF', "view3d.cursor_memory_hide", False)
        else:
            GUI.drawIconButton(True, layout, 'RESTRICT_VIEW_ON', "view3d.cursor_memory_show", False)
        # layout.prop(sce, "cursor_memory.savedLocationDraw")

    def draw(self, context):
        layout = self.layout
        cc = context.scene.cursor_memory

        row = layout.row()
        col = row.column()
        row2 = col.row()
        GUI.drawIconButton(True, row2, 'FORWARD', "view3d.cursor_memory_save")
        row2 = col.row()
        GUI.drawIconButton(True, row2, 'FILE_REFRESH', "view3d.cursor_memory_swap")
        row2 = col.row()
        GUI.drawIconButton(True, row2, 'BACK', "view3d.cursor_memory_recall")
        col = row.column()
        col.prop(cc, "savedLocation")


class VIEW3D_PT_cursor_memory_init(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = "Register callback"
    bl_options = {'DEFAULT_CLOSED'}

    initDone = False
    _handle = None

    @staticmethod
    def handle_add(self, context):
        VIEW3D_PT_cursor_memory_init._handle = \
                bpy.types.SpaceView3D.draw_handler_add(
                        cursor_memory_draw, (self, context),
                        'WINDOW', 'POST_PIXEL'
                        )

    @staticmethod
    def handle_remove():
        if VIEW3D_PT_cursor_memory_init._handle is not None:
            bpy.types.SpaceView3D.draw_handler_remove(
                    VIEW3D_PT_cursor_memory_init._handle, 'WINDOW'
                    )
        VIEW3D_PT_cursor_memory_init._handle = None

    @classmethod
    def poll(cls, context):
        try:
            if VIEW3D_PT_cursor_memory_init.initDone:
                return False

            if context.area.type == 'VIEW_3D':
                VIEW3D_PT_cursor_memory_init.handle_add(cls, context)
                VIEW3D_PT_cursor_memory_init.initDone = True
            else:
                print("\n[Cursor Control]\nClass:VIEW3D_PT_cursor_memory_init\n"
                     "Error: View3D not found, cannot initialize the handler draw")
        except Exception as e:
            print("\n[Cursor Control]\nClass:VIEW3D_PT_cursor_memory_init\n"
                 "Error: {}\n".format(e))

        return False

    def draw_header(self, context):
        pass

    def draw(self, context):
        pass


def cursor_memory_draw(cls, context):
    cc = context.scene.cursor_memory

    draw = 0
    if hasattr(cc, "savedLocationDraw"):
        draw = cc.savedLocationDraw

    if draw:
        bgl.glEnable(bgl.GL_BLEND)
        bgl.glShadeModel(bgl.GL_FLAT)
        p1 = Vector(cc.savedLocation)
        location = region3d_get_2d_coordinates(context, p1)
        alpha = 1 - PHI_INV
        # Circle
        color = ([0.33, 0.33, 0.33],
            [1, 1, 1],
            [0.33, 0.33, 0.33],
            [1, 1, 1],
            [0.33, 0.33, 0.33],
            [1, 1, 1],
            [0.33, 0.33, 0.33],
            [1, 1, 1],
            [0.33, 0.33, 0.33],
            [1, 1, 1],
            [0.33, 0.33, 0.33],
            [1, 1, 1],
            [0.33, 0.33, 0.33],
            [1, 1, 1])
        offset = ([-4.480736161291701, -8.939966636005579],
            [-0.158097634992133, -9.998750178787843],
            [4.195854066857877, -9.077158622037636],
            [7.718765411993642, -6.357724476147943],
            [9.71288060283854, -2.379065025383466],
            [9.783240669628, 2.070797430975971],
            [7.915909938224691, 6.110513059466902],
            [4.480736161291671, 8.939966636005593],
            [0.15809763499209872, 9.998750178787843],
            [-4.195854066857908, 9.077158622037622],
            [-7.718765411993573, 6.357724476148025],
            [-9.712880602838549, 2.379065025383433],
            [-9.783240669627993, -2.070797430976005],
            [-7.915909938224757, -6.110513059466818])
        bgl.glBegin(bgl.GL_LINE_LOOP)
        for i in range(14):
            bgl.glColor4f(color[i][0], color[i][1], color[i][2], alpha)
            bgl.glVertex2f(location[0] + offset[i][0], location[1] + offset[i][1])
        bgl.glEnd()

        # Crosshair
        offset2 = 20
        offset = 5
        bgl.glColor4f(0, 0, 0, alpha)
        bgl.glBegin(bgl.GL_LINE_STRIP)
        bgl.glVertex2f(location[0] - offset2, location[1])
        bgl.glVertex2f(location[0] - offset, location[1])
        bgl.glEnd()
        bgl.glBegin(bgl.GL_LINE_STRIP)
        bgl.glVertex2f(location[0] + offset, location[1])
        bgl.glVertex2f(location[0] + offset2, location[1])
        bgl.glEnd()
        bgl.glBegin(bgl.GL_LINE_STRIP)
        bgl.glVertex2f(location[0], location[1] - offset2)
        bgl.glVertex2f(location[0], location[1] - offset)
        bgl.glEnd()
        bgl.glBegin(bgl.GL_LINE_STRIP)
        bgl.glVertex2f(location[0], location[1] + offset)
        bgl.glVertex2f(location[0], location[1] + offset2)
        bgl.glEnd()

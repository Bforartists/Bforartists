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

      LATER:

      ISSUES:
          Bugs:
              Seg-faults when unregistering addon...
          Mites:
            * History back button does not light up on first cursor move.
              It does light up on the second, or when mouse enters the tool-area
            * Switching between local and global view triggers new cursor position in history trace.
            * Each consecutive click on the linex operator triggers new cursor position in history trace.
                 (2011-01-16) Was not able to fix this because of some strange script behaviour
                              while trying to clear linexChoice from addHistoryLocation

      QUESTIONS:
"""

import bpy
import bgl
from bpy.types import (
        Operator,
        Panel,
        PropertyGroup,
        )
from bpy.props import BoolProperty
from .misc_utils import (
        BlenderFake,
        region3d_get_2d_coordinates,
        )
from .constants_utils import PHI_INV
from .cursor_utils import CursorAccess
from .ui_utils import GUI


class CursorHistoryData(PropertyGroup):
    # History tracker
    historyDraw = BoolProperty(
            description="Draw history trace in 3D view",
            default=True
            )
    historyDepth = 144
    historyWindow = 12
    historyPosition = [-1]  # Integer must be in a list or else it can not be written to
    historyLocation = []
    # historySuppression = [False]  # Boolean must be in a list or else it can not be written to

    def addHistoryLocation(self, l):
        if(self.historyPosition[0] == -1):
            self.historyLocation.append(l.copy())
            self.historyPosition[0] = 0
            return
        if(l == self.historyLocation[self.historyPosition[0]]):
            return
        """
        if self.historySuppression[0]:
            self.historyPosition[0] = self.historyPosition[0] - 1
        else:
            self.hideLinexChoice()
        """
        while (len(self.historyLocation) > self.historyPosition[0] + 1):
            self.historyLocation.pop(self.historyPosition[0] + 1)
        # self.historySuppression[0] = False
        self.historyLocation.append(l.copy())

        if (len(self.historyLocation) > self.historyDepth):
            self.historyLocation.pop(0)
        self.historyPosition[0] = len(self.historyLocation) - 1
        # print (self.historyLocation)

    """
    def enableHistorySuppression(self):
        self.historySuppression[0] = True
    """

    def previousLocation(self):
        if self.historyPosition[0] <= 0:
            return
        self.historyPosition[0] = self.historyPosition[0] - 1
        CursorAccess.setCursor(self.historyLocation[self.historyPosition[0]].copy())

    def nextLocation(self):
        if (self.historyPosition[0] < 0):
            return
        if (self.historyPosition[0] + 1 == len(self.historyLocation)):
            return
        self.historyPosition[0] = self.historyPosition[0] + 1
        CursorAccess.setCursor(self.historyLocation[self.historyPosition[0]].copy())


class VIEW3D_OT_cursor_previous(Operator):
    bl_idname = "view3d.cursor_previous"
    bl_label = "Previous cursor location"
    bl_description = ("Previous cursor location\n"
                      "Red color means no further steps are available")
    bl_options = {'REGISTER'}

    no_skip = BoolProperty(
            options={"HIDDEN"},
            default=True
            )

    def modal(self, context, event):
        return {'FINISHED'}

    def execute(self, context):
        if self.no_skip:
            cc = context.scene.cursor_history
            cc.previousLocation()

        return {'FINISHED'}


class VIEW3D_OT_cursor_next(Operator):
    bl_idname = "view3d.cursor_next"
    bl_label = "Next cursor location"
    bl_description = ("Next cursor location\n"
                      "Red color means no further steps are available")
    bl_options = {'REGISTER'}

    no_skip = BoolProperty(
            options={"HIDDEN"},
            default=True
            )

    def modal(self, context, event):
        return {'FINISHED'}

    def execute(self, context):
        cc = context.scene.cursor_history
        if self.no_skip:
            cc.nextLocation()

        return {'FINISHED'}


class VIEW3D_OT_cursor_history_show(Operator):
    """Show cursor trace"""
    bl_idname = "view3d.cursor_history_show"
    bl_label = "Show cursor trace"
    bl_options = {'REGISTER'}

    def modal(self, context, event):
        return {'FINISHED'}

    def execute(self, context):
        cc = context.scene.cursor_history
        cc.historyDraw = True
        BlenderFake.forceRedraw()

        return {'FINISHED'}


class VIEW3D_OT_cursor_history_hide(Operator):
    """Hide cursor trace"""
    bl_idname = "view3d.cursor_history_hide"
    bl_label = "Hide cursor trace"
    bl_options = {'REGISTER'}

    def modal(self, context, event):
        return {'FINISHED'}

    def execute(self, context):
        cc = context.scene.cursor_history
        cc.historyDraw = False
        BlenderFake.forceRedraw()

        return {'FINISHED'}


class VIEW3D_PT_cursor_history(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = "Cursor History"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(self, context):
        # Display in object or edit mode
        cc = context.scene.cursor_history
        if CursorAccess.getCursor() is None:
            return False

        cc.addHistoryLocation(CursorAccess.getCursor())
        if (context.area.type == 'VIEW_3D' and
                (context.mode == 'EDIT_MESH' or
                 context.mode == 'OBJECT')):
            return True

        return False

    def draw_header(self, context):
        layout = self.layout
        cc = context.scene.cursor_history
        if cc.historyDraw:
            GUI.drawIconButton(
                    True, layout, 'RESTRICT_VIEW_OFF',
                    "view3d.cursor_history_hide", False
                    )
        else:
            GUI.drawIconButton(
                    True, layout, 'RESTRICT_VIEW_ON',
                    "view3d.cursor_history_show", False
                    )

    def draw(self, context):
        layout = self.layout
        cc = context.scene.cursor_history

        row = layout.row()
        row.label("Navigation: ")

        GUI.drawIconButton_poll(
                cc.historyPosition[0] > 0, row, 'PLAY_REVERSE',
                "view3d.cursor_previous"
                )
        GUI.drawIconButton_poll(
                cc.historyPosition[0] < len(cc.historyLocation) - 1,
                row, 'PLAY', "view3d.cursor_next"
                )

        row = layout.row()
        col = row.column()
        if CursorAccess.findSpace():
            col.prop(CursorAccess.findSpace(), "cursor_location")


class VIEW3D_PT_cursor_history_init(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_label = "Register callback"
    bl_options = {'DEFAULT_CLOSED'}

    initDone = False
    _handle = None

    @staticmethod
    def handle_add(self, context):
        VIEW3D_PT_cursor_history_init._handle = \
                bpy.types.SpaceView3D.draw_handler_add(
                        cursor_history_draw, (self, context),
                        'WINDOW', 'POST_PIXEL'
                        )

    @staticmethod
    def handle_remove():
        if VIEW3D_PT_cursor_history_init._handle is not None:
            bpy.types.SpaceView3D.draw_handler_remove(
                    VIEW3D_PT_cursor_history_init._handle, 'WINDOW'
                    )
        VIEW3D_PT_cursor_history_init._handle = None

    @classmethod
    def poll(cls, context):
        if VIEW3D_PT_cursor_history_init.initDone:
            return False

        try:
            if context.area.type == 'VIEW_3D':
                VIEW3D_PT_cursor_history_init.handle_add(cls, context)
                VIEW3D_PT_cursor_history_init.initDone = True
            else:
                print("\n[Cursor Control]\nClass:VIEW3D_PT_cursor_history_init\n"
                     "Error: View3D not found, cannot initialize the handler draw")
        except Exception as e:
            print("\n[Cursor Control]\nClass:VIEW3D_PT_cursor_history_init\n"
                 "Error: {}\n".format(e))

        return False

    def draw_header(self, context):
        pass

    def draw(self, context):
        pass


def cursor_history_draw(cls, context):
    cc = context.scene.cursor_history

    draw = 0
    if hasattr(cc, "historyDraw"):
        draw = cc.historyDraw

    if draw:
        bgl.glEnable(bgl.GL_BLEND)
        bgl.glShadeModel(bgl.GL_FLAT)
        alpha = 1 - PHI_INV
        # History Trace
        if cc.historyPosition[0] < 0:
            return
        bgl.glBegin(bgl.GL_LINE_STRIP)
        ccc = 0
        for iii in range(cc.historyWindow + 1):
            ix_rel = iii - int(cc.historyWindow / 2)
            ix = cc.historyPosition[0] + ix_rel
            if (ix < 0 or ix >= len(cc.historyLocation)):
                continue
            ppp = region3d_get_2d_coordinates(context, cc.historyLocation[ix])
            if ix_rel <= 0:
                bgl.glColor4f(0, 0, 0, alpha)
            else:
                bgl.glColor4f(1, 0, 0, alpha)
            bgl.glVertex2f(ppp[0], ppp[1])
            ccc = ccc + 1
        bgl.glEnd()

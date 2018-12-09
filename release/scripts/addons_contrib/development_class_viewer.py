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

bl_info = {
    "name": "Class Viewer",
    "author": "Mackraken", "batFinger"
    "version": (0, 1, 3),
    "blender": (2, 58, 0),
    "location": "Text Editor > Toolbar, Text Editor > Right Click",
    "warning": "",
    "description": "List classes and definitions of a text block",
    "wiki_url": "https://sites.google.com/site/aleonserra/home/scripts/class-viewer",
    "tracker_url": "https://developer.blender.org/maniphest/task/edit/form/2/",
    "category": "Development"}


import bpy
from bpy.types import (
        Operator,
        Menu,
        )
from bpy.props import IntProperty

# lists all defs, comment or classes
# space = current text editor
# sort = sort result
# tipo = kind of struct to look for
# escape = character right next to the class or def name
# note: GPL license block is skipped from the comment entries now


def getfunc(space, sort, tipo="def ", escape=""):
    defs, license_clean, return_lists = [], [], []

    if space.type == "TEXT_EDITOR" and space.text is not None:
        txt = space.text
        line_block_start, line_block_end = None, None

        for i, l in enumerate(txt.lines):
            try:
                line = l.body
            except:
                line = ""
            if tipo == "# ":
                linex, line_c = "", ""
                if tipo in line:
                    # find the license block
                    block_start = line.find("BEGIN GPL LICENSE BLOCK")
                    if block_start != -1:
                        line_block_start = i + 1

                    block_end = line.find("END GPL LICENSE BLOCK")
                    if block_end != -1:
                        line_block_end = i + 1

                    end = line.find(escape)
                    # use line partition, get the last tuple element as it is the comment
                    line_c = line.partition("#")[2]
                    # strip the spaces from the left if any and
                    # cut the comment at the 60 characters length max
                    linex = line_c[:60].lstrip() if len(line_c) > 60 else line_c.lstrip()
                    if end == 0:
                        func = linex
                    else:
                        func = linex.rstrip(escape)

                    defs.append([func, i + 1])

            elif line[0: len(tipo)] == tipo:
                end = line.find(escape)
                if end == 0:
                    func = line[len(tipo)::]
                else:
                    func = line[len(tipo):end]
                defs.append([func, i + 1])

        if line_block_start and line_block_end:
            # note : the slice should keep the first line of the license block
            license_clean = defs[line_block_start: line_block_end]

        return_lists = [line for line in defs if line not in license_clean] if license_clean else defs
        if sort:
            return_lists.sort()

    return return_lists


def draw_menus(layout, space, tipo, escape):

    items = getfunc(space, 1, tipo, escape)
    if not items:
        layout.label(text="Not found", icon="INFO")
        return

    for it in items:
        layout.operator("text.jumptoline", text="{}".format(it[0])).line = it[1]


class BaseCheckPoll():
    @classmethod
    def poll(cls, context):
        if context.area.spaces[0].type != "TEXT_EDITOR":
            return False
        else:
            return context.area.spaces[0].text is not None


class TEXT_OT_Jumptoline(Operator, BaseCheckPoll):
    bl_label = "Jump"
    bl_idname = "text.jumptoline"
    bl_description = "Jump to line containing the text"
    __doc__ = "Jump to line containing the passed line integer. Used by the Class Viewer add-on"

    line = IntProperty(default=-1)

    def execute(self, context):
        if self.line == -1:
            self.report({'WARNING'}, "No valid line found. Operation Cancelled")
            return {'CANCELLED'}

        bpy.ops.text.jump(line=self.line)
        self.report({'INFO'}, "Jump to line: {}".format(self.line))

        return {'FINISHED'}


class CommentsMenu(Menu, BaseCheckPoll):
    bl_idname = "OBJECT_MT_select_comments"
    bl_label = "Comments"

    def draw(self, context):
        layout = self.layout
        space = context.area.spaces[0]
        draw_menus(layout, space, "# ", "\n")


class DefsMenu(Menu, BaseCheckPoll):
    bl_idname = "OBJECT_MT_select_defs"
    bl_label = "Definitions"

    def draw(self, context):
        layout = self.layout
        space = context.area.spaces[0]
        draw_menus(layout, space, "def ", "(")


class ClassesMenu(Menu, BaseCheckPoll):
    bl_idname = "OBJECT_MT_select_classes"
    bl_label = "Classes"

    def draw(self, context):
        layout = self.layout
        space = context.area.spaces[0]
        draw_menus(layout, space, "class ", "(")


def menu_development_class_view(self, context):
    self.layout.separator()

    self.layout.menu("OBJECT_MT_select_comments", icon='SHORTDISPLAY')
    self.layout.menu("OBJECT_MT_select_defs", icon='FILE_TEXT')
    self.layout.menu("OBJECT_MT_select_classes", icon='SCRIPTPLUGINS')


classes = (
    TEXT_OT_Jumptoline,
    ClassesMenu,
    DefsMenu,
    CommentsMenu,
    )


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.TEXT_MT_toolbox.append(menu_development_class_view)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    bpy.types.TEXT_MT_toolbox.remove(menu_development_class_view)


if __name__ == "__main__":
    register()

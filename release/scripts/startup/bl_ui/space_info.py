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
import bpy
from bpy.types import Header, Menu


class INFO_HT_header(Header):
    bl_space_type = 'INFO'

    def draw(self, context):
        layout = self.layout

        ALL_MT_editormenu.draw_hidden(context, layout) # bfa - show hide the editormenu
        INFO_MT_editor_menus.draw_collapsible(context, layout)


class INFO_MT_editor_menus(Menu):
    bl_idname = "INFO_MT_editor_menus"
    bl_label = ""

    def draw(self, _context):
        layout = self.layout
        layout.menu("INFO_MT_info")


class INFO_MT_info(Menu):
    bl_label = "Info"

    def draw(self, _context):
        layout = self.layout

        layout.operator("info.select_all", text="All", icon = "SELECT_ALL").action = 'SELECT'
        layout.operator("info.select_all", text="None", icon = "SELECT_NONE").action = 'DESELECT'
        layout.operator("info.select_all", text="Inverse", icon = "INVERSE").action = 'INVERT'
        layout.operator("info.select_all", text="Toggle Selection", icon = "RESTRICT_SELECT_OFF").action = 'TOGGLE'

        layout.separator()

        layout.operator("info.select_box", icon = 'BORDER_RECT')

        layout.separator()

        # Disabled because users will likely try this and find
        # it doesn't work all that well in practice.
        # Mainly because operators needs to run in the right context.

        # layout.operator("info.report_replay")
        # layout.separator()

        layout.operator("info.report_delete", text="Delete", icon = "DELETE")
        layout.operator("info.report_copy", text="Copy", icon='COPYDOWN')


# bfa - show hide the editormenu
class ALL_MT_editormenu(Menu):
    bl_label = ""

    def draw(self, context):
        self.draw_menus(self.layout, context)

    @staticmethod
    def draw_menus(layout, context):

        row = layout.row(align=True)
        row.template_header() # editor type menus


class INFO_MT_context_menu(Menu):
    bl_label = "Info Context Menu"

    def draw(self, _context):
        layout = self.layout

        layout.operator("info.report_copy", text="Copy", icon='COPYDOWN')
        layout.operator("info.report_delete", text="Delete", icon='DELETE')


classes = (
    ALL_MT_editormenu,
    INFO_HT_header,
    INFO_MT_editor_menus,
    INFO_MT_info,
    INFO_MT_context_menu,
)

if __name__ == "__main__":  # only for live edit.
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

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
from bpy.types import Header, Panel, Menu


class PROPERTIES_HT_header(Header):
    bl_space_type = 'PROPERTIES'

    def draw(self, _context):
        layout = self.layout

        ALL_MT_editormenu.draw_hidden(_context, layout) # bfa - show hide the editormenu

        # bfa - The tabs to switch between the four animation editors. The classes are in the space_outliner.py
        row = layout.row(align=True)
        row.operator("wm.switch_editor_to_outliner", text="", icon='OOPS')


class PROPERTIES_PT_navigation_bar(Panel):
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'NAVIGATION_BAR'
    bl_label = "Navigation Bar"
    bl_options = {'HIDE_HEADER'}

    def draw(self, context):
        layout = self.layout

        view = context.space_data

        layout.scale_x = 1.4
        layout.scale_y = 1.4
        layout.prop_tabs_enum(view, "context", icon_only=True)

# bfa - show hide the editormenu
class ALL_MT_editormenu(Menu):
    bl_label = ""

    def draw(self, context):
        self.draw_menus(self.layout, context)

    @staticmethod
    def draw_menus(layout, context):

        row = layout.row(align=True)
        row.template_header() # editor type menus


classes = (
    PROPERTIES_HT_header,
    PROPERTIES_PT_navigation_bar,
    ALL_MT_editormenu,
)

if __name__ == "__main__":  # only for live edit.
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

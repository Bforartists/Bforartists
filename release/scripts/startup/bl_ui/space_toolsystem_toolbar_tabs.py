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
from bpy.types import Panel

class VIEW3D_tabs_HelloWorldPanel(Panel):
    """Creates a Panel in the Object properties window"""
    bl_label = "Hello World Panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_category = "Object"

    def draw(self, context):
        layout = self.layout

        row = layout.row()
        row.label(text="Hello world!", icon='WORLD') # bfa - removed icon WORLD_DATA


class VIEW3D_PT_snappanel_toolshelf(Panel):
    bl_label = "Snap"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_category = "Object"

    @staticmethod
    def ts_width(layout, region, scale_y):
        """
        Choose an appropriate layout for the toolbar.
        """
        # Currently this just checks the width,
        # we could have different layouts as preferences too.
        system = bpy.context.preferences.system
        view2d = region.view2d
        view2d_scale = (
            view2d.region_to_view(1.0, 0.0)[0] -
            view2d.region_to_view(0.0, 0.0)[0]
        )
        width_scale = region.width * view2d_scale / system.ui_scale

        if width_scale > 160.0:
            show_text = True
        else:
            show_text = False

        return show_text

    def draw(self, _context):
        layout = self.layout

        show_text = self.ts_width(layout, _context.region, scale_y= 1.75)   # Get the state of the show_text flag

        if show_text is True:

            layout.operator("view3d.snap_selected_to_cursor", text="Selection to Cursor", icon = "SELECTIONTOCURSOR").use_offset = False
            layout.operator("view3d.snap_selected_to_cursor", text="Selection to Cursor (Keep Offset)", icon = "SELECTIONTOCURSOROFFSET").use_offset = True
            layout.operator("view3d.snap_selected_to_active", text="Selection to Active", icon = "SELECTIONTOACTIVE")
            layout.operator("view3d.snap_selected_to_grid", text="Selection to Grid", icon = "SELECTIONTOGRID")

            layout.separator()

            layout.operator("view3d.snap_cursor_to_selected", text="Cursor to Selected", icon = "CURSORTOSELECTION")
            layout.operator("view3d.snap_cursor_to_center", text="Cursor to World Origin", icon = "CURSORTOCENTER")
            layout.operator("view3d.snap_cursor_to_active", text="Cursor to Active", icon = "CURSORTOACTIVE")
            layout.operator("view3d.snap_cursor_to_grid", text="Cursor to Grid", icon = "CURSORTOGRID")

        else:

            col = layout.column(align=True)
            col.label(text="Selection to :")
            col.scale_x = 1.75
            col.scale_y = 1.75

            row = col.row(align=True)
            row.alignment = 'CENTER'
            row.operator("view3d.snap_selected_to_cursor", text = "", icon = "SELECTIONTOCURSOR").use_offset = False
            row.operator("view3d.snap_selected_to_cursor", text = "", icon = "SELECTIONTOCURSOROFFSET").use_offset = True

            row = col.row(align=True)
            row.alignment = 'CENTER'
            row.operator("view3d.snap_selected_to_active", text = "", icon = "SELECTIONTOACTIVE")
            row.operator("view3d.snap_selected_to_grid", text = "", icon = "SELECTIONTOGRID")

            col.label(text="Cursor to :")
            row = col.row(align=True)
            row.alignment = 'CENTER'
            row.operator("view3d.snap_cursor_to_selected", text = "", icon = "CURSORTOSELECTION")
            row.operator("view3d.snap_cursor_to_center", text = "", icon = "CURSORTOCENTER")

            row = col.row(align=True)
            row.alignment = 'CENTER'
            row.operator("view3d.snap_cursor_to_active", text = "", icon = "CURSORTOACTIVE")
            row.operator("view3d.snap_cursor_to_grid", text = "", icon = "CURSORTOGRID")


classes = (
    VIEW3D_tabs_HelloWorldPanel,
    VIEW3D_PT_snappanel_toolshelf,
)

if __name__ == "__main__":  # only for live edit.
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

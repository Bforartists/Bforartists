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


class toolshelf_calculate( Panel):

    @staticmethod
    def ts_width(layout, region, scale_y):

        # Currently this just checks the width,
        # we could have different layouts as preferences too.
        system = bpy.context.preferences.system
        view2d = region.view2d
        view2d_scale = (
            view2d.region_to_view(1.0, 0.0)[0] -
            view2d.region_to_view(0.0, 0.0)[0]
        )
        width_scale = region.width * view2d_scale / system.ui_scale

        # how many rows. 4 is text buttons.

        if width_scale > 160.0:
            column_count = 4
        elif width_scale > 120.0:
            column_count = 3
        elif width_scale > 80:
            column_count = 2
        else:
            column_count = 1

        return column_count

class VIEW3D_PT_snappanel_transform(toolshelf_calculate, Panel):
    bl_label = "Transform"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_category = "Object"

    # just show when the toolshelf tabs toggle in the view menu is on.
    @classmethod
    def poll(cls, context):
        view = context.space_data
        overlay = view.overlay
        return overlay.show_toolshelf_tabs == True

    def draw(self, context):
        layout = self.layout

        column_count = self.ts_width(layout, context.region, scale_y= 1.75)

        obj = context.object

        #text buttons
        if column_count == 4:

            col = layout.column(align=True)
            col.scale_y = 2

            col.operator("transform.tosphere", text="To Sphere", icon = "TOSPHERE")
            col.operator("transform.shear", text="Shear", icon = "SHEAR")
            col.operator("transform.bend", text="Bend", icon = "BEND")
            col.operator("transform.push_pull", text="Push/Pull", icon = 'PUSH_PULL')

            if context.mode in {'EDIT_MESH', 'EDIT_ARMATURE', 'EDIT_SURFACE', 'EDIT_CURVE',
                                'EDIT_LATTICE', 'EDIT_METABALL'}:
                col.operator("transform.vertex_warp", text="Warp", icon = "MOD_WARP")
                col.operator_context = 'EXEC_REGION_WIN'
                col.operator("transform.vertex_random", text="Randomize", icon = 'RANDOMIZE').offset = 0.1
                col.operator_context = 'INVOKE_REGION_WIN'

        # icon buttons
        else:

            col = layout.column(align=True)
            col.scale_x = 2
            col.scale_y = 2

            if column_count == 3:

                row = col.row(align=True)
                row.operator("transform.tosphere", text="", icon = "TOSPHERE")
                row.operator("transform.shear", text="", icon = "SHEAR")
                row.operator("transform.bend", text="", icon = "BEND")

                row = col.row(align=True)
                row.operator("transform.push_pull", text="", icon = 'PUSH_PULL')

                if context.mode in {'EDIT_MESH', 'EDIT_ARMATURE', 'EDIT_SURFACE', 'EDIT_CURVE',
                                    'EDIT_LATTICE', 'EDIT_METABALL'}:
                    row = col.row(align=True)
                    row.operator("transform.vertex_warp", text="", icon = "MOD_WARP")
                    row.operator_context = 'EXEC_REGION_WIN'
                    row.operator("transform.vertex_random", text="", icon = 'RANDOMIZE').offset = 0.1
                    row.operator_context = 'INVOKE_REGION_WIN'

            elif column_count == 2:

                row = col.row(align=True)
                row.operator("transform.tosphere", text="", icon = "TOSPHERE")
                row.operator("transform.shear", text="", icon = "SHEAR")

                row = col.row(align=True)
                row.operator("transform.bend", text="", icon = "BEND")
                row.operator("transform.push_pull", text="", icon = 'PUSH_PULL')

                if context.mode in {'EDIT_MESH', 'EDIT_ARMATURE', 'EDIT_SURFACE', 'EDIT_CURVE',
                                    'EDIT_LATTICE', 'EDIT_METABALL'}:
                    row = col.row(align=True)
                    row.operator("transform.vertex_warp", text="", icon = "MOD_WARP")
                    row.operator_context = 'EXEC_REGION_WIN'
                    row.operator("transform.vertex_random", text="", icon = 'RANDOMIZE').offset = 0.1
                    row.operator_context = 'INVOKE_REGION_WIN'

            elif column_count == 1:

                col.operator("transform.tosphere", text="", icon = "TOSPHERE")
                col.operator("transform.shear", text="", icon = "SHEAR")
                col.operator("transform.bend", text="", icon = "BEND")
                col.operator("transform.push_pull", text="", icon = 'PUSH_PULL')

                if context.mode in {'EDIT_MESH', 'EDIT_ARMATURE', 'EDIT_SURFACE', 'EDIT_CURVE',
                                    'EDIT_LATTICE', 'EDIT_METABALL'}:
                    col.operator("transform.vertex_warp", text="", icon = "MOD_WARP")
                    col.operator_context = 'EXEC_REGION_WIN'
                    col.operator("transform.vertex_random", text="", icon = 'RANDOMIZE').offset = 0.1
                    col.operator_context = 'INVOKE_REGION_WIN'


class VIEW3D_PT_snappanel_toolshelf(toolshelf_calculate, Panel):
    bl_label = "Snap"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_category = "Object"

    # just show when the toolshelf tabs toggle in the view menu is on.
    @classmethod
    def poll(cls, context):
        view = context.space_data
        overlay = view.overlay
        return overlay.show_toolshelf_tabs == True

    def draw(self, _context):
        layout = self.layout

        column_count = self.ts_width(layout, _context.region, scale_y= 1.75)

        #text buttons
        if column_count == 4:

            col = layout.column(align=True)
            col.scale_y = 2

            col.operator("view3d.snap_selected_to_cursor", text="Selection to Cursor", icon = "SELECTIONTOCURSOR").use_offset = False
            col.operator("view3d.snap_selected_to_cursor", text="Selection to Cursor (Keep Offset)", icon = "SELECTIONTOCURSOROFFSET").use_offset = True
            col.operator("view3d.snap_selected_to_active", text="Selection to Active", icon = "SELECTIONTOACTIVE")
            col.operator("view3d.snap_selected_to_grid", text="Selection to Grid", icon = "SELECTIONTOGRID")

            col.separator()

            col.operator("view3d.snap_cursor_to_selected", text="Cursor to Selected", icon = "CURSORTOSELECTION")
            col.operator("view3d.snap_cursor_to_center", text="Cursor to World Origin", icon = "CURSORTOCENTER")
            col.operator("view3d.snap_cursor_to_active", text="Cursor to Active", icon = "CURSORTOACTIVE")
            col.operator("view3d.snap_cursor_to_grid", text="Cursor to Grid", icon = "CURSORTOGRID")

        # icon buttons
        else:

            col = layout.column(align=True)
            col.scale_x = 2
            col.scale_y = 2

            if column_count == 3:

                row = col.row(align=True)
                row.operator("view3d.snap_selected_to_cursor", text = "", icon = "SELECTIONTOCURSOR").use_offset = False
                row.operator("view3d.snap_selected_to_cursor", text = "", icon = "SELECTIONTOCURSOROFFSET").use_offset = True
                row.operator("view3d.snap_selected_to_active", text = "", icon = "SELECTIONTOACTIVE")

                row = col.row(align=True)
                row.operator("view3d.snap_selected_to_grid", text = "", icon = "SELECTIONTOGRID")

                col.separator(factor = 0.5)

                row = col.row(align=True)
                row.operator("view3d.snap_cursor_to_selected", text = "", icon = "CURSORTOSELECTION")
                row.operator("view3d.snap_cursor_to_center", text = "", icon = "CURSORTOCENTER")
                row.operator("view3d.snap_cursor_to_active", text = "", icon = "CURSORTOACTIVE")

                row = col.row(align=True)
                row.operator("view3d.snap_cursor_to_grid", text = "", icon = "CURSORTOGRID")

            elif column_count == 2:

                row = col.row(align=True)

                row.operator("view3d.snap_selected_to_cursor", text = "", icon = "SELECTIONTOCURSOR").use_offset = False
                row.operator("view3d.snap_selected_to_cursor", text = "", icon = "SELECTIONTOCURSOROFFSET").use_offset = True

                row = col.row(align=True)

                row.operator("view3d.snap_selected_to_active", text = "", icon = "SELECTIONTOACTIVE")
                row.operator("view3d.snap_selected_to_grid", text = "", icon = "SELECTIONTOGRID")

                col.separator(factor = 0.5)

                row = col.row(align=True)
                row.operator("view3d.snap_cursor_to_selected", text = "", icon = "CURSORTOSELECTION")
                row.operator("view3d.snap_cursor_to_center", text = "", icon = "CURSORTOCENTER")

                row = col.row(align=True)
                row.operator("view3d.snap_cursor_to_active", text = "", icon = "CURSORTOACTIVE")
                row.operator("view3d.snap_cursor_to_grid", text = "", icon = "CURSORTOGRID")

            elif column_count == 1:

                col.operator("view3d.snap_selected_to_cursor", text = "", icon = "SELECTIONTOCURSOR").use_offset = False
                col.operator("view3d.snap_selected_to_cursor", text = "", icon = "SELECTIONTOCURSOROFFSET").use_offset = True
                col.operator("view3d.snap_selected_to_active", text = "", icon = "SELECTIONTOACTIVE")
                col.operator("view3d.snap_selected_to_grid", text = "", icon = "SELECTIONTOGRID")

                col.separator(factor = 0.5)

                col.operator("view3d.snap_cursor_to_selected", text = "", icon = "CURSORTOSELECTION")
                col.operator("view3d.snap_cursor_to_center", text = "", icon = "CURSORTOCENTER")
                col.operator("view3d.snap_cursor_to_active", text = "", icon = "CURSORTOACTIVE")
                col.operator("view3d.snap_cursor_to_grid", text = "", icon = "CURSORTOGRID")

classes = (
    VIEW3D_PT_snappanel_transform,
    VIEW3D_PT_snappanel_toolshelf,
)

if __name__ == "__main__":  # only for live edit.
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

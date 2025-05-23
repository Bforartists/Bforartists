# SPDX-FileCopyrightText: 2009-2023 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

import bpy


class SPREADSHEET_HT_header(bpy.types.Header):
    bl_space_type = 'SPREADSHEET'

    def draw(self, context):
        layout = self.layout
        space = context.space_data

        layout.template_header()
        SPREADSHEET_MT_editor_menus.draw_collapsible(context, layout)
        layout.separator_spacer()

        row = layout.row(align=True)
        sub = row.row(align=True)
        sub.active = self.selection_filter_available(space)
        sub.prop(space, "show_only_selected", text="")
        row.prop(space, "use_filter", toggle=True, icon='FILTER', icon_only=True)

    def selection_filter_available(self, space):
        root_context = space.viewer_path.path[0]
        if root_context.type != 'ID':
            return False
        if not isinstance(root_context.id, bpy.types.Object):
            return False
        obj = root_context.id
        if obj is None:
            return False
        if obj.type == 'MESH':
            return obj.mode == 'EDIT'
        if obj.type == 'CURVES':
            return obj.mode in {'SCULPT_CURVES', 'EDIT'}
        if obj.type == 'POINTCLOUD':
            return obj.mode == 'EDIT'
        return False


class SPREADSHEET_MT_editor_menus(bpy.types.Menu):
    bl_idname = "SPREADSHEET_MT_editor_menus"
    bl_label = ""

    def draw(self, context):
        del context
        layout = self.layout
        layout.menu("SPREADSHEET_MT_view")


class SPREADSHEET_MT_view(bpy.types.Menu):
    bl_label = "View"

    def draw(self, context):
        layout = self.layout
        sspreadsheet = context.space_data

        layout.prop(sspreadsheet, "show_region_toolbar")
        layout.prop(sspreadsheet, "show_region_ui")

        layout.separator()

        layout.menu("INFO_MT_area")


classes = (
    SPREADSHEET_HT_header,

    SPREADSHEET_MT_editor_menus,
    SPREADSHEET_MT_view,
)

if __name__ == "__main__":  # Only for live edit.
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

# SPDX-License-Identifier: GPL-2.0-or-later
from bpy.types import Header, Menu

from bpy.app.translations import contexts as i18n_contexts


class INFO_HT_header(Header):
    bl_space_type = 'INFO'

    def draw(self, context):
        layout = self.layout

        ALL_MT_editormenu.draw_hidden(context, layout)  # bfa - show hide the editormenu
        INFO_MT_editor_menus.draw_collapsible(context, layout)


class INFO_MT_editor_menus(Menu):
    bl_idname = "INFO_MT_editor_menus"
    bl_label = ""

    def draw(self, _context):
        layout = self.layout
        layout.menu("INFO_MT_view")
        layout.menu("INFO_MT_info")


class INFO_MT_view(Menu):
    bl_label = "View"

    def draw(self, _context):
        layout = self.layout

        layout.menu("INFO_MT_area")


class INFO_MT_info(Menu):
    bl_label = "Info"

    def draw(self, _context):
        layout = self.layout

        layout.operator("info.select_all", text="All", icon="SELECT_ALL").action = 'SELECT'
        layout.operator("info.select_all", text="None", icon="SELECT_NONE").action = 'DESELECT'
        layout.operator("info.select_all", text="Inverse", icon="INVERSE").action = 'INVERT'
        layout.operator("info.select_all", text="Toggle Selection", icon="RESTRICT_SELECT_OFF").action = 'TOGGLE'

        layout.separator()

        layout.operator("info.select_box", icon='BORDER_RECT')

        layout.separator()

        # Disabled because users will likely try this and find
        # it doesn't work all that well in practice.
        # Mainly because operators needs to run in the right context.

        # layout.operator("info.report_replay")
        # layout.separator()

        layout.operator("info.report_delete", text="Delete", icon="DELETE")
        layout.operator("info.report_copy", text="Copy", icon='COPYDOWN')


# bfa - show hide the editormenu
class ALL_MT_editormenu(Menu):
    bl_label = ""

    def draw(self, context):
        self.draw_menus(self.layout, context)

    @staticmethod
    def draw_menus(layout, context):

        row = layout.row(align=True)
        row.template_header()  # editor type menus


class INFO_MT_area(Menu):
    bl_label = "Area"
    bl_translation_context = i18n_contexts.id_windowmanager

    def draw(self, context):
        layout = self.layout

        layout.operator("screen.area_split", text="Horizontal Split", icon="SPLIT_HORIZONTAL").direction = 'HORIZONTAL'
        layout.operator("screen.area_split", text="Vertical Split", icon="SPLIT_VERTICAL").direction = 'VERTICAL'

        layout.separator()

        layout.operator("screen.area_dupli", icon="NEW_WINDOW")

        layout.separator()

        layout.operator("screen.screen_full_area", icon='MAXIMIZE_AREA')
        layout.operator(
            "screen.screen_full_area",
            text="Toggle Fullscreen Area",
            icon='FULLSCREEN_ENTER').use_hide_panels = True

        layout.separator()

        layout.operator("screen.area_close", icon="PANEL_CLOSE")


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
    INFO_MT_area,
    INFO_MT_view,
    INFO_MT_info,
    INFO_MT_context_menu,
)

if __name__ == "__main__":  # only for live edit.
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

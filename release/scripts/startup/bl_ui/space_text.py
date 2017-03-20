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

# <pep8-80 compliant>
import bpy
from bpy.types import Header, Menu, Panel
from bpy.app.translations import pgettext_iface as iface_


class TEXT_HT_header(Header):
    bl_space_type = 'TEXT_EDITOR'

    def draw(self, context):
        layout = self.layout

        st = context.space_data
        text = st.text

        row = layout.row(align=True)

        ALL_MT_editormenu.draw_hidden(context, layout) # bfa - show hide the editormenu
        TEXT_MT_editor_menus.draw_collapsible(context, layout)

        if text and text.is_modified:
            sub = row.row(align=True)
            sub.alert = True
            sub.operator("text.resolve_conflict", text="", icon='HELP')

        row = layout.row(align=True)
        row.template_ID(st, "text", new="text.new", unlink="text.unlink", open="text.open")

        row = layout.row(align=True)
        row.prop(st, "show_line_numbers", text="")
        row.prop(st, "show_word_wrap", text="")
        row.prop(st, "show_syntax_highlight", text="")

        if text:
            osl = text.name.endswith(".osl") or text.name.endswith(".oso")

            if osl:
                row = layout.row()
                row.operator("node.shader_script_update")
            else:
                row = layout.row()
                row.operator("text.run_script")

                row = layout.row()
                row.active = text.name.endswith(".py")
                row.prop(text, "use_module")

            row = layout.row()
            if text.filepath:
                if text.is_dirty:
                    row.label(text=iface_("File: *%r (unsaved)") %
                              text.filepath, translate=False)
                else:
                    row.label(text=iface_("File: %r") %
                              text.filepath, translate=False)
            else:
                row.label(text="Text: External"
                          if text.library
                          else "Text: Internal")

# bfa - show hide the editormenu
class ALL_MT_editormenu(Menu):
    bl_label = ""

    def draw(self, context):
        self.draw_menus(self.layout, context)

    @staticmethod
    def draw_menus(layout, context):

        row = layout.row(align=True)
        row.template_header() # editor type menus


class TEXT_MT_editor_menus(Menu):
    bl_idname = "TEXT_MT_editor_menus"
    bl_label = ""

    def draw(self, context):
        self.draw_menus(self.layout, context)

    @staticmethod
    def draw_menus(layout, context):
        st = context.space_data
        text = st.text

        layout.menu("TEXT_MT_File")
        layout.menu("TEXT_MT_view")

        if text:
            layout.menu("TEXT_MT_edit")
            layout.menu("TEXT_MT_format")


class TEXT_PT_properties(Panel):
    bl_space_type = 'TEXT_EDITOR'
    bl_region_type = 'UI'
    bl_label = "Properties"

    def draw(self, context):
        layout = self.layout

        st = context.space_data

        flow = layout.column_flow()
        flow.prop(st, "show_line_highlight")
        flow.prop(st, "use_live_edit")

        flow = layout.column_flow()
        flow.prop(st, "font_size")
        flow.prop(st, "tab_width")

        text = st.text
        if text:
            flow.prop(text, "use_tabs_as_spaces")

        flow.prop(st, "show_margin")
        col = flow.column()
        col.active = st.show_margin
        col.prop(st, "margin_column")


class TEXT_PT_find(Panel):
    bl_space_type = 'TEXT_EDITOR'
    bl_region_type = 'UI'
    bl_label = "Find"

    def draw(self, context):
        layout = self.layout

        st = context.space_data

        # find
        col = layout.column(align=True)
        row = col.row(align=True)
        row.prop(st, "find_text", text="")
        row.operator("text.find_set_selected", text="", icon='TEXT')
        col.operator("text.find")

        # replace
        col = layout.column(align=True)
        row = col.row(align=True)
        row.prop(st, "replace_text", text="")
        row.operator("text.replace_set_selected", text="", icon='TEXT')
        col.operator("text.replace")

        # settings
        layout.prop(st, "use_match_case")
        row = layout.row(align=True)
        row.prop(st, "use_find_wrap", text="Wrap")
        row.prop(st, "use_find_all", text="All")

# Workaround to separate the tooltips for Toggle Maximize Area
# Note that this id name also gets used in the other editors now.

class TEXT_Toggle_Maximize_Area(bpy.types.Operator):
    """Toggle Maximize Area\nToggle display selected area as maximized"""      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "screen.toggle_maximized_area"        # unique identifier for buttons and menu items to reference.
    bl_label = "Toggle Maximize Area"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.screen.screen_full_area(use_hide_panels = False)
        return {'FINISHED'}  

class TEXT_MT_view(Menu):
    bl_label = "View"

    def draw(self, context):
        layout = self.layout

        layout.operator("text.properties", icon='MENU_PANEL')

        layout.separator()

        layout.operator("text.move",
                        text="Top of File",
                        ).type = 'FILE_TOP'
        layout.operator("text.move",
                        text="Bottom of File",
                        ).type = 'FILE_BOTTOM'

        layout.separator()

        layout.operator("screen.area_dupli")
        layout.operator("screen.toggle_maximized_area", text="Toggle Maximize Area") # bfa - the new separated tooltip. Class is in space_text.py
        layout.operator("screen.screen_full_area", text="Toggle Fullscreen Area").use_hide_panels = True


class TEXT_MT_File(Menu):
    bl_label = "File"

    def draw(self, context):
        layout = self.layout

        st = context.space_data
        text = st.text

        layout.operator("text.new", text = "New Text", icon='NEW')
        layout.operator("text.open", text = "Open Text", icon='FILE_FOLDER')

        if text:
            layout.operator("text.reload")

            layout.column()
            layout.operator("text.save", icon='FILE_TICK')
            layout.operator("text.save_as", icon='SAVE_AS')

            if text.filepath:
                layout.operator("text.make_internal")

            layout.column()
            layout.operator("text.run_script")

        layout.separator()

        layout.menu("TEXT_MT_templates")


class TEXT_MT_templates_py(Menu):
    bl_label = "Python"

    def draw(self, context):
        self.path_menu(bpy.utils.script_paths("templates_py"),
                       "text.open",
                       {"internal": True},
                       )


class TEXT_MT_templates_osl(Menu):
    bl_label = "Open Shading Language"

    def draw(self, context):
        self.path_menu(bpy.utils.script_paths("templates_osl"),
                       "text.open",
                       {"internal": True},
                       )


class TEXT_MT_templates(Menu):
    bl_label = "Templates"

    def draw(self, context):
        layout = self.layout
        layout.menu("TEXT_MT_templates_py")
        layout.menu("TEXT_MT_templates_osl")


class TEXT_MT_edit_select(Menu):
    bl_label = "Select"

    def draw(self, context):
        layout = self.layout

        layout.operator("text.select_all")
        layout.operator("text.select_line")


class TEXT_MT_format(Menu):
    bl_label = "Format"

    def draw(self, context):
        layout = self.layout

        layout.operator("text.indent")
        layout.operator("text.unindent")

        layout.separator()

        layout.operator("text.comment")
        layout.operator("text.uncomment")

        layout.separator()

        layout.operator_menu_enum("text.convert_whitespace", "type")


class TEXT_MT_edit_to3d(Menu):
    bl_label = "Text To 3D Object"

    def draw(self, context):
        layout = self.layout

        layout.operator("text.to_3d_object",
                        text="One Object",
                        ).split_lines = False
        layout.operator("text.to_3d_object",
                        text="One Object Per Line",
                        ).split_lines = True


class TEXT_MT_edit(Menu):
    bl_label = "Edit"

    @classmethod
    def poll(cls, context):
        return (context.space_data.text)

    def draw(self, context):
        layout = self.layout

        layout.operator("ed.undo")
        layout.operator("ed.redo")

        layout.separator()

        layout.operator("text.cut")
        layout.operator("text.copy")
        layout.operator("text.paste")
        layout.operator("text.duplicate_line")

        layout.separator()

        layout.operator("text.move_lines", text="Move line(s) up").direction = 'UP'
        layout.operator("text.move_lines", text="Move line(s) down").direction = 'DOWN'

        layout.separator()

        layout.operator("text.select_all")
        layout.operator("text.select_line")
        layout.operator_menu_enum("text.delete", "type")

        layout.separator()

        layout.operator("text.jump")
        layout.operator("text.start_find", text="Find...")
        layout.operator("text.autocomplete")

        layout.separator()

        layout.menu("TEXT_MT_edit_to3d")


class TEXT_MT_toolbox(Menu):
    bl_label = ""

    def draw(self, context):
        layout = self.layout

        layout.operator_context = 'INVOKE_DEFAULT'

        layout.operator("text.cut")
        layout.operator("text.copy")
        layout.operator("text.paste")

        layout.separator()

        layout.operator("text.run_script")

if __name__ == "__main__":  # only for live edit.
    bpy.utils.register_module(__name__)

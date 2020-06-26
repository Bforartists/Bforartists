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
        is_syntax_highlight_supported = st.is_syntax_highlight_supported()

        ALL_MT_editormenu.draw_hidden(context, layout) # bfa - show hide the editormenu
        TEXT_MT_editor_menus.draw_collapsible(context, layout)

        row = layout.row(align=True)
        if text and text.is_modified:
            row = layout.row(align=True)
            row.alert = True
            row.operator("text.resolve_conflict", text="", icon='HELP')

        row = layout.row(align=True)
        row.template_ID(st, "text", new="text.new",
                        unlink="text.unlink", open="text.open")

        if text:
            text_name = text.name
            is_osl = text_name.endswith((".osl", ".oso"))

            row = layout.row()
            if is_osl:
                row = layout.row()
                row.operator("node.shader_script_update")
            else:

                row = layout.row()
                row.active = is_syntax_highlight_supported
                row.operator("text.run_script", text="", icon='PLAY')

                row = layout.row()
                row.active = text_name.endswith(".py")
                row.prop(text, "use_module")

        layout.separator_spacer()

        row = layout.row(align=True)
        row.prop(st, "show_line_numbers", text="")
        row.prop(st, "show_word_wrap", text="")

        syntax = row.row(align=True)
        syntax.active = is_syntax_highlight_supported
        syntax.prop(st, "show_syntax_highlight", text="")


class TEXT_HT_footer(Header):
    bl_space_type = 'TEXT_EDITOR'
    bl_region_type = 'FOOTER'

    def draw(self, context):
        layout = self.layout

        st = context.space_data
        text = st.text
        if text:
            row = layout.row()
            if text.filepath:
                if text.is_dirty:
                    row.label(
                        text=iface_("File: *%s (unsaved)" % text.filepath),
                        translate=False,
                    )
                else:
                    row.label(
                        text=iface_("File: %s" % text.filepath),
                        translate=False,
                    )
            else:
                row.label(
                    text=iface_("Text: External")
                    if text.library
                    else iface_("Text: Internal"),
                )


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

        layout.menu("TEXT_MT_text")
        layout.menu("TEXT_MT_view")

        if text:
            layout.menu("TEXT_MT_edit")
            layout.menu("TEXT_MT_format")


class TEXT_PT_properties(Panel):
    bl_space_type = 'TEXT_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Text"
    bl_label = "Properties"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        st = context.space_data

        flow = layout.column_flow()
        flow.use_property_split = False
        flow.prop(st, "show_line_highlight")
        flow.prop(st, "use_live_edit")
        layout.use_property_split = True

        flow = layout.column_flow()

        flow.prop(st, "font_size")
        flow.prop(st, "tab_width")

        text = st.text
        if text:
            layout.prop(text, "indentation")
        flow.use_property_split = False
        flow.prop(st, "show_margin")
        flow.use_property_split = True
        if st.show_margin:

            col = flow.column()
            col.active = st.show_margin
            col.prop(st, "margin_column")


class TEXT_PT_find(Panel):
    bl_space_type = 'TEXT_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Text"
    bl_label = "Find & Replace"

    def draw(self, context):
        layout = self.layout
        st = context.space_data

        # find
        col = layout.column(align=True)
        row = col.row(align=True)
        row.prop(st, "find_text", text="", icon='VIEWZOOM')
        row.operator("text.find_set_selected", text="", icon='EYEDROPPER')
        col.operator("text.find")

        # replace
        col = layout.column(align=True)
        row = col.row(align=True)
        row.prop(st, "replace_text", text="", icon='DECORATE_OVERRIDE')
        row.operator("text.replace_set_selected", text="", icon='EYEDROPPER')

        row = col.row(align=True)
        row.operator("text.replace")
        row.operator("text.replace", text = "Replace all").all = True

        # settings
        row = layout.row(align=True)
        if not st.text:
            row.active = False
        row.prop(st, "use_match_case", text="Case", toggle=True)
        row.prop(st, "use_find_wrap", text="Wrap", toggle=True)
        row.prop(st, "use_find_all", text="All", toggle=True)


class TEXT_MT_view(Menu):
    bl_label = "View"

    def draw(self, context):
        layout = self.layout

        st = context.space_data

        layout.prop(st, "show_region_ui")

        layout.separator()

        layout.operator("text.move", text="Top of File", icon = "MOVE_UP").type = 'FILE_TOP'
        layout.operator("text.move", text="Bottom of File",icon = "MOVE_DOWN").type = 'FILE_BOTTOM'

        layout.separator()

        layout.menu("INFO_MT_area")


#Redraw timer sub menu - Debug stuff
class TEXT_MT_redraw_timer(Menu):
    bl_label = "Redraw Timer"

    def draw(self, context):
        layout = self.layout

        layout.operator("wm.redraw_timer", text = 'Draw Region').type ='DRAW'
        layout.operator("wm.redraw_timer", text = 'Draw Region  Swap').type ='DRAW_SWAP'
        layout.operator("wm.redraw_timer", text = 'Draw Window').type ='DRAW_WIN'
        layout.operator("wm.redraw_timer", text = 'Draw Window  Swap').type ='DRAW_WIN_SWAP'
        layout.operator("wm.redraw_timer", text = 'Anim Step').type ='ANIM_STEP'
        layout.operator("wm.redraw_timer", text = 'Anim Play').type ='ANIM_PLAY'
        layout.operator("wm.redraw_timer", text = 'Undo/Redo').type ='UNDO'


class TEXT_MT_text(Menu):
    bl_label = "File"

    def draw(self, context):
        layout = self.layout

        st = context.space_data
        text = st.text

        layout.operator("text.new", text = "New Text", icon='NEW')
        layout.operator("text.open", text = "Open Text", icon='FILE_FOLDER')

        if text:
            layout.operator("text.reload", icon = "FILE_REFRESH")

            layout.column()
            layout.operator("text.save", icon='FILE_TICK')
            layout.operator("text.save_as", icon='SAVE_AS')

            if text.filepath:
                layout.separator()
                layout.operator("text.make_internal", icon = "MAKE_INTERNAL")

        layout.separator()

        layout.menu("TEXT_MT_templates")

        layout.separator()

        layout.menu("TEXT_MT_redraw_timer", icon='TIME') #Redraw timer sub menu - Debug stuff
        layout.operator("wm.debug_menu", icon='DEBUG') # debug menu
        layout.operator("script.reload", icon='FILE_REFRESH') # Reload all python scripts. Mainly meant for the UI scripts.

        layout.separator()

        layout.operator("screen.spacedata_cleanup", icon = "APPTEMPLATE")
        layout.operator("wm.memory_statistics", icon = "SYSTEM")


class TEXT_MT_templates_py(Menu):
    bl_label = "Python"

    def draw(self, _context):
        self.path_menu(
            bpy.utils.script_paths("templates_py"),
            "text.open",
            props_default={"internal": True},
            filter_ext=lambda ext: (ext.lower() == ".py")
        )


class TEXT_MT_templates_osl(Menu):
    bl_label = "Open Shading Language"

    def draw(self, _context):
        self.path_menu(
            bpy.utils.script_paths("templates_osl"),
            "text.open",
            props_default={"internal": True},
            filter_ext=lambda ext: (ext.lower() == ".osl")
        )


class TEXT_MT_templates(Menu):
    bl_label = "Templates"

    def draw(self, _context):
        layout = self.layout
        layout.menu("TEXT_MT_templates_py")
        layout.menu("TEXT_MT_templates_osl")


class TEXT_MT_format(Menu):
    bl_label = "Format"

    def draw(self, _context):
        layout = self.layout

        layout.operator("text.indent", icon = "INDENT")
        layout.operator("text.unindent", icon = "UNINDENT")

        layout.separator()

        layout.operator("text.comment_toggle", text = "Comment", icon = "COMMENT").type = 'COMMENT'
        layout.operator("text.comment_toggle", text = "Un-Comment", icon = "COMMENT").type = 'UNCOMMENT'
        layout.operator("text.comment_toggle", icon = "COMMENT")

        layout.separator()

        layout.operator("text.convert_whitespace", text = "Whitespace to Spaces", icon = "WHITESPACE_SPACES").type = 'SPACES'
        layout.operator("text.convert_whitespace", text = "Whitespace to Tabs", icon = "WHITESPACE_TABS").type = 'TABS'


class TEXT_MT_edit_to3d(Menu):
    bl_label = "Text To 3D Object"

    def draw(self, _context):
        layout = self.layout

        layout.operator("text.to_3d_object", text="One Object", icon = "OUTLINER_OB_FONT").split_lines = False
        layout.operator("text.to_3d_object",text="One Object Per Line", icon = "OUTLINER_OB_FONT").split_lines = True


class TEXT_MT_edit(Menu):
    bl_label = "Edit"

    @classmethod
    def poll(cls, context):
        return context.space_data.text is not None

    def draw(self, _context):
        layout = self.layout

        layout.operator("text.cut", icon = "CUT")
        layout.operator("text.copy", icon = "COPYDOWN")
        layout.operator("text.paste", icon = "PASTEDOWN")
        layout.operator("text.duplicate_line", icon = "DUPLICATE")

        layout.separator()

        layout.operator("text.move_lines", text="Move Line(s) Up", icon = "MOVE_UP").direction = 'UP'
        layout.operator("text.move_lines", text="Move Line(s) Down", icon = "MOVE_DOWN").direction = 'DOWN'

        layout.separator()

        layout.menu("TEXT_MT_edit_move_select")

        layout.separator()

        layout.menu("TEXT_MT_edit_delete")

        layout.separator()

        layout.operator("text.select_all", icon = "SELECT_ALL")
        layout.operator("text.select_line", icon = "SELECT_LINE")

        layout.separator()

        layout.operator("text.jump", text = "Go to line", icon = "GOTO")
        layout.operator("text.start_find", text="Find", icon = "ZOOM_SET")
        layout.operator("text.autocomplete", icon = "AUTOCOMPLETE")

        layout.separator()

        layout.menu("TEXT_MT_edit_to3d")


# move_select submenu
class TEXT_MT_edit_move_select(Menu):
    bl_label = "Select Text"

    def draw(self, context):
        layout = self.layout

        layout.operator("text.move_select", text = "Line End", icon = "HAND").type = 'LINE_END'
        layout.operator("text.move_select", text = "Line Begin", icon = "HAND").type = 'LINE_BEGIN'
        layout.operator("text.move_select", text = "Previous Character", icon = "HAND").type = 'PREVIOUS_CHARACTER'
        layout.operator("text.move_select", text = "Next Character", icon = "HAND").type = 'NEXT_CHARACTER'
        layout.operator("text.move_select", text = "Previous Word", icon = "HAND").type = 'PREVIOUS_WORD'
        layout.operator("text.move_select", text = "Next Word", icon = "HAND").type = 'NEXT_WORD'
        layout.operator("text.move_select", text = "Previous Line", icon = "HAND").type = 'PREVIOUS_LINE'
        layout.operator("text.move_select", text = "Next Line", icon = "HAND").type = 'NEXT_LINE'
        layout.operator("text.move_select", text = "Previous Character", icon = "HAND").type = 'PREVIOUS_CHARACTER'
        layout.operator("text.move_select", text = "Next Character", icon = "HAND").type = 'NEXT_CHARACTER'


class TEXT_MT_context_menu(Menu):
    bl_label = ""

    def draw(self, _context):
        layout = self.layout

        layout.operator_context = 'INVOKE_DEFAULT'

        layout.operator("text.cut", icon = "CUT")
        layout.operator("text.copy", icon = "COPYDOWN")
        layout.operator("text.paste", icon = "PASTEDOWN")

        layout.separator()

        layout.operator("text.move_lines", text="Move Line(s) Up", icon = "MOVE_UP").direction = 'UP'
        layout.operator("text.move_lines", text="Move Line(s) Down", icon = "MOVE_DOWN").direction = 'DOWN'

        layout.separator()

        layout.operator("text.indent", icon = "INDENT")
        layout.operator("text.unindent", icon = "UNINDENT")

        layout.separator()

        layout.operator("text.comment_toggle", icon = "COMMENT")

        layout.separator()

        layout.operator("text.autocomplete", icon = "AUTOCOMPLETE")


class TEXT_MT_edit_delete(Menu):
    bl_label = "Delete"

    def draw(self, context):
        layout = self.layout

        layout.operator("text.delete", text = "Next Character", icon = "DELETE").type = 'NEXT_CHARACTER'
        layout.operator("text.delete", text = "Previous Character", icon = "DELETE").type = 'PREVIOUS_CHARACTER'
        layout.operator("text.delete", text = "Next Word", icon = "DELETE").type = 'NEXT_WORD'
        layout.operator("text.delete", text = "Previous Word", icon = "DELETE").type = 'PREVIOUS_WORD'


classes = (
    ALL_MT_editormenu,
    TEXT_HT_header,
    TEXT_HT_footer,
    TEXT_MT_editor_menus,
    TEXT_PT_properties,
    TEXT_PT_find,
    TEXT_MT_view,
    TEXT_MT_redraw_timer,
    TEXT_MT_text,
    TEXT_MT_templates,
    TEXT_MT_templates_py,
    TEXT_MT_templates_osl,
    TEXT_MT_format,
    TEXT_MT_edit_to3d,
    TEXT_MT_context_menu,
    TEXT_MT_edit,
    TEXT_MT_edit_move_select,
    TEXT_MT_edit_delete,
)

if __name__ == "__main__":  # only for live edit.
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

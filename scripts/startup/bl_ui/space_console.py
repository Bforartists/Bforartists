# SPDX-License-Identifier: GPL-2.0-or-later
import bpy
from bpy.types import Header, Menu


class CONSOLE_HT_header(Header):
    bl_space_type = 'CONSOLE'

    def draw(self, context):
        layout = self.layout.row()

        ALL_MT_editormenu.draw_hidden(context, layout) # bfa - show hide the editormenu
        CONSOLE_MT_editor_menus.draw_collapsible(context, layout)

        layout.operator("console.autocomplete", text="Autocomplete")

# bfa - show hide the editormenu
class ALL_MT_editormenu(Menu):
    bl_label = ""

    def draw(self, context):
        self.draw_menus(self.layout, context)

    @staticmethod
    def draw_menus(layout, context):

        row = layout.row(align=True)
        row.template_header() # editor type menus

class CONSOLE_MT_editor_menus(Menu):
    bl_idname = "CONSOLE_MT_editor_menus"
    bl_label = ""

    def draw(self, _context):
        layout = self.layout
        layout.menu("CONSOLE_MT_console")
        layout.menu("CONSOLE_MT_edit")


class CONSOLE_MT_console(Menu):
    bl_label = "Console"

    def draw(self, _context):
        layout = self.layout

        layout.operator("console.execute", icon = "PLAY").interactive = True

        layout.separator()

        layout.operator("console.clear", icon = "DELETE")
        layout.operator("console.clear_line", icon = "DELETE")

        layout.separator()

        layout.operator("console.copy_as_script", text = "Copy as Script", icon = "COPYDOWN")
        layout.operator("console.copy", text ="Copy", icon = "COPYDOWN")
        layout.operator("console.paste", text = "Paste", icon = "PASTEDOWN")

        layout.separator()

        layout.menu("CONSOLE_MT_language")

        layout.separator()

        myvar = layout.operator("wm.context_cycle_int", text = "Zoom Text in", icon = "ZOOM_IN")
        myvar.data_path = "space_data.font_size"
        myvar.reverse = False

        myvar = layout.operator("wm.context_cycle_int", text = "Zoom Text Out", icon = "ZOOM_OUT")
        myvar.data_path = "space_data.font_size"
        myvar.reverse = True

        layout.separator()

        layout.menu("INFO_MT_area")

class CONSOLE_MT_edit(Menu):
    bl_label = "Edit"

    def draw(self, context):
        layout = self.layout

        layout.operator("console.indent", icon = "INDENT")
        layout.operator("console.unindent", icon = "UNINDENT")

        layout.separator()

        layout.operator("console.move", text ="Cursor to Previous Word", icon = "CARET_PREV_WORD").type = "PREVIOUS_WORD"
        layout.operator("console.move", text ="Cursor to Next Word", icon = "CARET_NEXT_WORD").type = "NEXT_WORD"
        layout.operator("console.move", text ="Cursor to Line Begin", icon = "CARET_LINE_BEGIN").type = "LINE_BEGIN"
        layout.operator("console.move", text ="Cursor to Line End", icon = "CARET_LINE_END").type = "LINE_END"
        layout.operator("console.move", text ="Cursor to Previous Character", icon = "CARET_PREV_CHAR").type = "PREVIOUS_CHARACTER"
        layout.operator("console.move", text ="Cursor to Next Character", icon = "CARET_NEXT_CHAR").type = "NEXT_CHARACTER"

        layout.separator()

        layout.menu("CONSOLE_MT_edit_delete")

        layout.separator()

        layout.operator("console.history_cycle", text = "Forward in History", icon = "HISTORY_CYCLE_FORWARD").reverse = False
        layout.operator("console.history_cycle", text = "Backward in History", icon = "HISTORY_CYCLE_BACK").reverse = True


class CONSOLE_MT_language(Menu):
    bl_label = "Languages..."

    def draw(self, _context):
        import sys

        layout = self.layout
        layout.column()

        # Collect modules with `console_*.execute`.
        languages = []
        for modname, mod in sys.modules.items():
            if modname.startswith("console_") and hasattr(mod, "execute"):
                languages.append(modname.split("_", 1)[-1])

        languages.sort()

        for language in languages:
            layout.operator("console.language",
                            text=language.title(),
                            translate=False).language = language

class CONSOLE_MT_edit_delete(Menu):
    bl_label = "Delete"

    def draw(self, context):
        layout = self.layout

        layout.operator("console.delete", text = "Next Character", icon = "DELETE").type = 'NEXT_CHARACTER'
        layout.operator("console.delete", text = "Previous Character", icon = "DELETE").type = 'PREVIOUS_CHARACTER'
        layout.operator("console.delete", text = "Next Word", icon = "DELETE").type = 'NEXT_WORD'
        layout.operator("console.delete", text = "Previous Word", icon = "DELETE").type = 'PREVIOUS_WORD'


class CONSOLE_MT_context_menu(Menu):
    bl_label = "Console Context Menu"

    def draw(self, _context):
        layout = self.layout

        layout.operator("console.clear", icon = "DELETE")
        layout.operator("console.clear_line", icon = "DELETE")
        layout.operator("console.delete", text="Delete Previous Word", icon = "DELETE").type = 'PREVIOUS_WORD'
        layout.operator("console.delete", text="Delete Next Word", icon = "DELETE").type = 'NEXT_WORD'

        layout.separator()

        layout.operator("console.copy_as_script", text="Copy as Script", icon = "COPYDOWN")
        layout.operator("console.copy", text="Copy", icon = "COPYDOWN")
        layout.operator("console.paste", text="Paste", icon = "PASTEDOWN")

        layout.separator()

        layout.operator("console.indent", icon = "INDENT")
        layout.operator("console.unindent", icon = "UNINDENT")

        layout.separator()

        layout.operator("console.history_cycle", text="Backward in History", icon = "HISTORY_CYCLE_BACK").reverse = True
        layout.operator("console.history_cycle", text="Forward in History", icon = "HISTORY_CYCLE_FORWARD").reverse = False

        layout.separator()

        layout.operator("console.autocomplete", text="Autocomplete", icon = "AUTOCOMPLETE")


def add_scrollback(text, text_type):
    for l in text.split("\n"):
        bpy.ops.console.scrollback_append(text=l.expandtabs(4),
                                          type=text_type)


classes = (
    CONSOLE_HT_header,
    ALL_MT_editormenu,
    CONSOLE_MT_edit,
    CONSOLE_MT_editor_menus,
    CONSOLE_MT_console,
    CONSOLE_MT_language,
    CONSOLE_MT_edit_delete,
    CONSOLE_MT_context_menu,
)

if __name__ == "__main__":  # only for live edit.
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

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

    def draw(self, context):
        self.draw_menus(self.layout, context)

    @staticmethod
    def draw_menus(layout, context):
        layout.menu("CONSOLE_MT_console")
        layout.menu("CONSOLE_MT_edit")


class CONSOLE_MT_console(Menu):
    bl_label = "Console"

    def draw(self, context):
        layout = self.layout
        
        layout.operator("console.execute").interactive = True
        
        layout.separator()

        layout.operator("console.clear")
        layout.operator("console.clear_line")

        layout.separator()

        layout.operator("console.copy_as_script", text = "Copy as Script")
        layout.operator("console.copy", text ="Copy")
        layout.operator("console.paste", text = "Paste")
        
        layout.separator()

        layout.menu("CONSOLE_MT_language")
        
        layout.separator()
        
        myvar = layout.operator("wm.context_cycle_int", text = "Zoom Text in")
        myvar.data_path = "space_data.font_size"
        myvar.reverse = False
        
        myvar = layout.operator("wm.context_cycle_int", text = "Zoom Text Out")
        myvar.data_path = "space_data.font_size"
        myvar.reverse = True

        layout.separator()

        layout.operator("screen.area_dupli")
        layout.operator("screen.toggle_maximized_area", text="Toggle Maximize Area") # bfa - the separated tooltip. Class is in space_text.py
        layout.operator("screen.screen_full_area", text="Toggle Fullscreen Area").use_hide_panels = True
        
class CONSOLE_MT_edit(Menu):
    bl_label = "Edit"

    def draw(self, context):
        layout = self.layout

        layout.operator("console.indent")
        layout.operator("console.unindent")
        
        layout.separator()
        
        layout.operator("console.move", text ="Cursor to Previous Word").type = "PREVIOUS_WORD"
        layout.operator("console.move", text ="Cursor to Next Word").type = "NEXT_WORD"
        layout.operator("console.move", text ="Cursor to Line Begin").type = "LINE_BEGIN"
        layout.operator("console.move", text ="Cursor to Line Begin").type = "LINE_END"     
        layout.operator("console.move", text ="Cursor to Previous Character").type = "PREVIOUS_CHARACTER"
        layout.operator("console.move", text ="Cursor to Next Character").type = "NEXT_CHARACTER"
        
        layout.separator()
        
        layout.operator_menu_enum("console.delete", "type")
        
        layout.separator()
        
        layout.operator("console.history_cycle").reverse = False
        layout.operator("console.history_cycle").reverse = True


class CONSOLE_MT_language(Menu):
    bl_label = "Languages..."

    def draw(self, context):
        import sys

        layout = self.layout
        layout.column()

        # Collect modules with 'console_*.execute'
        languages = []
        for modname, mod in sys.modules.items():
            if modname.startswith("console_") and hasattr(mod, "execute"):
                languages.append(modname.split("_", 1)[-1])

        languages.sort()

        for language in languages:
            layout.operator("console.language",
                            text=language.title(),
                            translate=False).language = language


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
)

if __name__ == "__main__":  # only for live edit.
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

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
"""
Shortcut: Ctrl+Tab to switch between Dopesheet/Graph Editor

Hit Ctrl + Tab to switch between Dopesheet and the Graph Editor.
Developed during Caminandes Open Movie Project
"""


import bpy

KEYMAPS = list()


def register():
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon

    km = kc.keymaps.new(name="Graph Editor", space_type="GRAPH_EDITOR")
    kmi = km.keymap_items.new("wm.context_set_enum", "TAB", "PRESS", ctrl=True)
    kmi.properties.data_path = "area.type"
    kmi.properties.value = "DOPESHEET_EDITOR"
    KEYMAPS.append((km, kmi))

    km = kc.keymaps.new(name="Dopesheet", space_type="DOPESHEET_EDITOR")
    kmi = km.keymap_items.new("wm.context_set_enum", "TAB", "PRESS", ctrl=True)
    kmi.properties.data_path = "area.type"
    kmi.properties.value = "GRAPH_EDITOR"
    KEYMAPS.append((km, kmi))

    km = kc.keymaps.new(name="Dopesheet", space_type="DOPESHEET_EDITOR")
    kmi = km.keymap_items.new("wm.context_toggle_enum",
                              "TAB", "PRESS", shift=True)
    kmi.properties.data_path = "space_data.mode"
    kmi.properties.value_1 = "ACTION"
    kmi.properties.value_2 = "DOPESHEET"
    KEYMAPS.append((km, kmi))


def unregister():
    for km, kmi in KEYMAPS:
        km.keymap_items.remove(kmi)
    KEYMAPS.clear()

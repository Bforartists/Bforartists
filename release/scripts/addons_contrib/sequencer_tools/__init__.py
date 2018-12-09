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

bl_info = {
    "name": "Sequencer Tools",
    "author": "mont29",
    "version": (0, 0, 5),
    "blender": (2, 78, 0),
    "location": "Sequencer menus/UI",
    "description": "Various Sequencer tools.",
    "warning": "",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/"
        "Scripts/Sequencer/Tools",
    "tracker_url": "https://developer.blender.org/maniphest/task/edit/form/2/",
    "support": 'TESTING',
    "category": "Sequencer",
}

if "bpy" in locals():
    import imp
    imp.reload(export_strips)
else:
    import bpy
    import bpy_extras.keyconfig_utils
    from . import export_strips


classes = export_strips.classes


KEYMAPS = (
    # First, keymap identifiers (last bool is True for modal km).
    (('Sequencer', 'SEQUENCE_EDITOR', 'WINDOW', False), (
    # Then a tuple of keymap items, defined by a dict of kwargs for the km new func, and a tuple of tuples (name, val)
    # for ops properties, if needing non-default values.
        ({"idname": export_strips.SEQExportStrip.bl_idname, "type": 'P', "value": 'PRESS', "shift": True, "ctrl": True},
         ()),
    )),
)


def menu_func(self, context):
    self.layout.operator(export_strips.SEQExportStrip.bl_idname, text="Export Selected")


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.SEQUENCER_MT_strip.append(menu_func)

    bpy_extras.keyconfig_utils.addon_keymap_register(bpy.context.window_manager, KEYMAPS)


def unregister():
    bpy_extras.keyconfig_utils.addon_keymap_unregister(bpy.context.window_manager, KEYMAPS)

    bpy.types.SEQUENCER_MT_strip.remove(menu_func)
    for cls in classes:
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()

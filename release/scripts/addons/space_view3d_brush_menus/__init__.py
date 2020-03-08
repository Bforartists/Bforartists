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
# Modified by Meta-Androcto

""" Copyright 2011 GPL licence applies"""

bl_info = {
    "name": "Dynamic Brush Menus",
    "description": "Fast access to brushes & tools in Sculpt and Paint Modes",
    "author": "Ryan Inch (Imaginer)",
    "version": (1, 1, 8),
    "blender": (2, 80, 0),
    "location": "Spacebar in Sculpt/Paint Modes",
    "warning": '',
    "doc_url": "{BLENDER_MANUAL_URL}/addons/interface/brush_menus.html",
    "category": "Interface",
}


if "bpy" in locals():
    import importlib
    importlib.reload(utils_core)
    importlib.reload(brush_menu)
    importlib.reload(brushes)
    importlib.reload(curve_menu)
    importlib.reload(dyntopo_menu)
    importlib.reload(stroke_menu)
    importlib.reload(symmetry_menu)
    importlib.reload(texture_menu)
else:
    from . import utils_core
    from . import brush_menu
    from . import brushes
    from . import curve_menu
    from . import dyntopo_menu
    from . import stroke_menu
    from . import symmetry_menu
    from . import texture_menu


import bpy
from bpy.types import AddonPreferences
from bpy.props import (
        EnumProperty,
        IntProperty,
        )


addon_files = (
    brush_menu,
    brushes,
    curve_menu,
    dyntopo_menu,
    stroke_menu,
    symmetry_menu,
    texture_menu,
    )



class VIEW3D_MT_Brushes_Pref(AddonPreferences):
    bl_idname = __name__

    column_set: IntProperty(
        name="Number of Columns",
        description="Number of columns used for the brushes menu",
        default=2,
        min=1,
        max=10
        )

    def draw(self, context):
        layout = self.layout

        col = layout.column(align=True)
        col.prop(self, "column_set", slider=True)


# New hotkeys and registration

addon_keymaps = []


def register():
    # register all files
    for addon_file in addon_files:
        addon_file.register()

    # set the add-on name variable to access the preferences
    utils_core.get_addon_name = __name__

    # register preferences
    bpy.utils.register_class(VIEW3D_MT_Brushes_Pref)

    # register hotkeys
    wm = bpy.context.window_manager
    modes = ('Sculpt', 'Vertex Paint', 'Weight Paint', 'Image Paint', 'Particle')

    for mode in modes:
        km = wm.keyconfigs.addon.keymaps.new(name=mode)
        kmi = km.keymap_items.new('wm.call_menu', 'SPACE', 'PRESS')
        kmi.properties.name = "VIEW3D_MT_sv3_brush_options"
        addon_keymaps.append((km, kmi))


def unregister():
    # unregister all files
    for addon_file in addon_files:
        addon_file.unregister()

    # unregister preferences
    bpy.utils.unregister_class(VIEW3D_MT_Brushes_Pref)

    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()


if __name__ == "__main__":
    register()

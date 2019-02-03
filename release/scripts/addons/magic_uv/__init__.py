# <pep8-80 compliant>

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

__author__ = "Nutti <nutti.metro@gmail.com>"
__status__ = "production"
__version__ = "6.0"
__date__ = "26 Jan 2019"


bl_info = {
    "name": "Magic UV",
    "author": "Nutti, Mifth, Jace Priester, kgeogeo, mem, imdjs"
              "Keith (Wahooney) Boshoff, McBuff, MaxRobinot, "
              "Alexander Milovsky",
    "version": (6, 0, 0),
    "blender": (2, 80, 0),
    "location": "See Add-ons Preferences",
    "description": "UV Toolset. See Add-ons Preferences for details",
    "warning": "",
    "support": "COMMUNITY",
    "wiki_url": "https://wiki.blender.org/index.php/Extensions:2.6/"
                "Py/Scripts/UV/Magic_UV",
    "tracker_url": "https://github.com/nutti/Magic-UV",
    "category": "UV"
}


if "bpy" in locals():
    import importlib
    importlib.reload(common)
    importlib.reload(utils)
    utils.bl_class_registry.BlClassRegistry.cleanup()
    importlib.reload(op)
    importlib.reload(ui)
    importlib.reload(properites)
    importlib.reload(preferences)
    importlib.reload(updater)
else:
    import bpy
    from . import common
    from . import utils
    from . import op
    from . import ui
    from . import properites
    from . import preferences
    from . import updater

import bpy


def register():
    updater.register_updater(bl_info)

    utils.bl_class_registry.BlClassRegistry.register()
    properites.init_props(bpy.types.Scene)
    user_prefs = utils.compatibility.get_user_preferences(bpy.context)
    if user_prefs.addons['magic_uv'].preferences.enable_builtin_menu:
        preferences.add_builtin_menu()


def unregister():
    user_prefs = utils.compatibility.get_user_preferences(bpy.context)
    if user_prefs.addons['magic_uv'].preferences.enable_builtin_menu:
        preferences.remove_builtin_menu()
    properites.clear_props(bpy.types.Scene)
    utils.bl_class_registry.BlClassRegistry.unregister()


if __name__ == "__main__":
    register()

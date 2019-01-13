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
__version__ = "5.2"
__date__ = "17 Nov 2018"


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

def check_version(major, minor, _):
    """
    Check blender version
    """

    if bpy.app.version[0] == major and bpy.app.version[1] == minor:
        return 0
    if bpy.app.version[0] > major:
        return 1
    if bpy.app.version[1] > minor:
        return 1
    return -1


if "bpy" in locals():
    import importlib
    importlib.reload(common)
    importlib.reload(utils)
    utils.bl_class_registry.BlClassRegistry.cleanup()
    if check_version(2, 80, 0) >= 0:
        importlib.reload(lib)
        importlib.reload(op)
        importlib.reload(ui)
        importlib.reload(properites)
        importlib.reload(preferences)
    else:
        importlib.reload(legacy)
    importlib.reload(impl)
else:
    import bpy
    from . import common
    from . import utils
    if check_version(2, 80, 0) >= 0:
        from . import lib
        from . import op
        from . import ui
        from . import properites
        from . import preferences
    else:
        from . import legacy
    from . import impl

import os

import bpy


def register_updater(bl_info):
    config = utils.addon_updator.AddonUpdatorConfig()
    config.owner = "nutti"
    config.repository = "Magic-UV"
    config.current_addon_path = os.path.dirname(os.path.realpath(__file__))
    config.branches = ["master", "develop"]
    config.addon_directory = config.current_addon_path[:config.current_addon_path.rfind("/")]
    #config.min_release_version = bl_info["version"]
    config.min_release_version = (5, 1)
    config.target_addon_path = "uv_magic_uv"
    updater = utils.addon_updator.AddonUpdatorManager.get_instance()
    updater.init(bl_info, config)


def register():
    register_updater(bl_info)

    if common.check_version(2, 80, 0) >= 0:
        utils.bl_class_registry.BlClassRegistry.register()
        properites.init_props(bpy.types.Scene)
        if bpy.context.user_preferences.addons['uv_magic_uv'].preferences.enable_builtin_menu:
            preferences.add_builtin_menu()
    else:
        utils.bl_class_registry.BlClassRegistry.register()
        legacy.properites.init_props(bpy.types.Scene)
        if legacy.preferences.Preferences.enable_builtin_menu:
            legacy.preferences.add_builtin_menu()


def unregister():
    if common.check_version(2, 80, 0) >= 0:
        if bpy.context.user_preferences.addons['uv_magic_uv'].preferences.enable_builtin_menu:
            preferences.remove_builtin_menu()
        properites.clear_props(bpy.types.Scene)
        utils.bl_class_registry.BlClassRegistry.unregister()
    else:
        if legacy.preferences.Preferences.enable_builtin_menu:
            legacy.preferences.remove_builtin_menu()
        legacy.properites.clear_props(bpy.types.Scene)
        utils.bl_class_registry.BlClassRegistry.unregister()


if __name__ == "__main__":
    register()

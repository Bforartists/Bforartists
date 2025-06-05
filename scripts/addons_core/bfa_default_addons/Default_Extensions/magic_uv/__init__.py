# SPDX-FileCopyrightText: 2017-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

__author__ = "Nutti <nutti.metro@gmail.com>"
__status__ = "production"
__version__ = "6.7.1"
__date__ = "22 Sep 2022"


if "bpy" in locals():
    import importlib
    importlib.reload(common)
    importlib.reload(utils)
    utils.bl_class_registry.BlClassRegistry.cleanup()
    importlib.reload(op)
    importlib.reload(ui)
    importlib.reload(properties)
    importlib.reload(preferences)
else:
    import bpy
    from . import common
    from . import utils
    from . import op
    from . import ui
    from . import properties
    from . import preferences

import bpy


def register():
    utils.bl_class_registry.BlClassRegistry.register()
    properties.init_props(bpy.types.Scene)
    user_prefs = utils.compatibility.get_user_preferences(bpy.context)
    if user_prefs.addons[__package__].preferences.enable_builtin_menu:
        preferences.add_builtin_menu()


def unregister():
    preferences.remove_builtin_menu()
    properties.clear_props(bpy.types.Scene)
    utils.bl_class_registry.BlClassRegistry.unregister()


if __name__ == "__main__":
    register()

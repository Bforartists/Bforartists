# SPDX-FileCopyrightText: 2016-2024 Blender Foundation
#
# SPDX-License-Identifier: GPL-3.0-or-later

bl_info = {
    "name":"Extra Pie Menus",
    "description": "A set of handy pie menus to enhance various workflows",
    "author": "pitiwazou, meta-androcto, Demeter Dzadik",
    "version": (1, 6, 12),
    "blender": (4, 2, 0),
    "description": "See Add-on Preferences for shortcut list",
    "location": "Addons Preferences",
    "warning": "Bforartists version: Disable first if you wish to use the online Extension version", #BFA - warning added
    "doc_url": "{BLENDER_MANUAL_URL}/addons/interface/viewport_pies.html",
    'tracker_url': "https://projects.blender.org/extensions/space_view3d_pie_menus",
    'support': 'COMMUNITY',
    "category": "Interface",
}
bl_info_copy = bl_info.copy()

import bpy
from bpy.utils import register_class, unregister_class
import importlib

module_names = (
    "op_pie_wrappers",
    "op_copy_to_selected",
    "hotkeys",
    "prefs",
    "sidebar",
    "tweak_builtin_pies",

    "pie_animation",
    "pie_apply_transform",
    "pie_camera",
    "pie_preferences",
    "pie_editor_split_merge",
    "pie_editor_switch",
    "pie_file",
    "pie_manipulator",
    "pie_mesh_delete",
    "pie_mesh_flatten",
    "pie_mesh_merge",
    "pie_object_add",
    "pie_object_display",
    "pie_object_parenting",
    "pie_proportional_editing",
    "pie_relationship_delete",
    "pie_sculpt_brush_select",
    "pie_selection",
    "pie_set_origin",
    "pie_view_3d",
    "pie_window",
)


modules = [
    __import__(__package__ + "." + submod, {}, {}, submod)
    for submod in module_names
]


def register_unregister_modules(modules: list, register: bool):
    """Recursively register or unregister modules by looking for either
    un/register() functions or lists named `registry` which should be a list of
    registerable classes.
    """
    register_func = register_class if register else unregister_class
    un = 'un' if not register else ''

    for m in modules:
        if register:
            importlib.reload(m)
        if hasattr(m, 'registry'):
            for c in m.registry:
                try:
                    register_func(c)
                except Exception as e:
                    print(
                        f"Warning: Pie Menus failed to {un}register class: {c.__name__}"
                    )
                    print(e)

        if hasattr(m, 'modules'):
            register_unregister_modules(m.modules, register)

        if register and hasattr(m, 'register'):
            m.register()
        elif hasattr(m, 'unregister'):
            m.unregister()


def delayed_register(_scene=None):
    # Register whole add-on with a slight delay,
    # to make sure Keymap data we need already exists on Blender launch.
    # Otherwise, keyconfigs.user.keymaps is an empty list, we can't find fallback ops.
    register_unregister_modules(modules, True)


def register():
    if bpy.app.version >= (4, 5, 0):
        register_unregister_modules(modules, True)
    else:
        # NOTE: persistent=True must be set, otherwise this doesn't work when opening a .blend file directly from a file browser.
        bpy.app.timers.register(delayed_register, first_interval=0.5, persistent=True)

def unregister():
    # We need to save add-on prefs to file before unregistering anything, 
    # otherwise things can fail in various ways, like hard errors or just
    # data getting saved as integers instead of bools or enums.
    from . import prefs
    addon_prefs = prefs.get_addon_prefs()
    if addon_prefs:
        # Disabled auto-saving for now, since sometimes hotkeys fail to load properly, 
        # and then they get overwritten with that incomplete data.
        # prefs.update_prefs_on_file()
        register_unregister_modules(reversed(modules), False)

# SPDX-FileCopyrightText: 2016-2020 by Nathan Lovato, Daniel Oakey, Razvan Radulescu, and contributors
#
# SPDX-License-Identifier: GPL-3.0-or-later

from typing import List, Tuple, Type

import bpy

from .addon_preferences import register_preferences, unregister_preferences
from .addon_properties import register_properties, unregister_properties
from .handlers import register_handlers, unregister_handlers
from .operators import get_operator_classes
from .tools import get_tool_classes
from .ui import register_ui, unregister_ui
from .utils import addon_auto_imports
from .utils.register_shortcuts import register_shortcuts

# load and reload submodules
##################################
modules = addon_auto_imports.setup_addon_modules(
    __path__, __name__, ignore_packages=[".utils", ".audiosync"]
)


bl_info = {
    "name": "Power Sequencer",
    "description": "Video editing tools for content creators",
    "author": "Nathan Lovato",
    "version": (2, 0, 2),
    "blender": (2, 93, 3),
    "location": "Sequencer",
    "tracker_url": "https://github.com/GDquest/Blender-power-sequencer/issues",
    "wiki_url": "https://www.gdquest.com/docs/documentation/power-sequencer/",
    "support": "COMMUNITY",
    "category": "Sequencer",
}


# We use globals to cache loaded keymaps, operators, and tools
addon_keymaps: List[Type] = []
classes_operator: List[Type] = []
classes_tool: List[Type] = []


def register():
    global addon_keymaps
    global classes_operator
    global classes_tool

    register_preferences()
    register_properties()
    register_handlers()
    register_ui()

    # Register operators
    classes_operator = get_operator_classes()
    for cls in classes_operator:
        bpy.utils.register_class(cls)

    # Register tools
    classes_tool = get_tool_classes()
    last_tool = {"builtin.blade"}
    for index, cls in enumerate(classes_tool):
        bpy.utils.register_tool(cls, after=last_tool, separator=index == 0)
        last_tool = {cls.bl_idname}

    # Register keymaps
    keymaps = register_shortcuts(classes_operator)
    addon_keymaps += keymaps

    print("Registered {} with {} modules".format(bl_info["name"], len(modules)))


def unregister():
    """Unregister"""
    global addon_keymaps
    global classes_operator
    global classes_tool

    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

    for cls in classes_operator:
        bpy.utils.unregister_class(cls)

    for cls in classes_tool:
        bpy.utils.unregister_tool(cls)

    unregister_ui()
    unregister_preferences()
    unregister_properties()
    unregister_handlers()

    print("Unregistered {}".format(bl_info["name"]))

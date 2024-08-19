# SPDX-License-Identifier: GPL-2.0-or-later

import bpy
from .operators import register as operators_register, unregister as operators_unregister
from .tools import register as tools_register, unregister as tools_unregister
from . import (
    preferences,
    properties,
    ui,
    versioning,
)


#### ------------------------------ REGISTRATION ------------------------------ ####

modules = [
    preferences,
    properties,
    ui,
    versioning,
]

def register():
    for module in modules:
        module.register()
    
    operators_register()
    tools_register()


def unregister():
    for module in reversed(modules):
        module.unregister()

    operators_unregister()
    tools_unregister()

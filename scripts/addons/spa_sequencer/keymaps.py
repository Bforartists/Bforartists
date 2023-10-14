# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2023, The SPA Studios. All rights reserved.

"""
Addon's keymap registration.
"""

from typing import Any

import bpy

addon_keymaps = []


def register_keymap(
    operator: str,
    key: str,
    shift: bool = False,
    ctrl: bool = False,
    alt: bool = False,
    space_type: str = "VIEW_3D",
    category_name: str = "3D View Generic",
    value: str = "PRESS",
    properties: dict[str, Any] = {},
):
    """
    Register a new keymap in the preferences.

    :param operator: the operator to call
    :param key: the shortcut's key name
    :param shift: enable shift modifier
    :param ctrl: enable ctrl modifier
    :param alt: enable alt modifier
    :param space_type: the Blender space type where this shortcut applies
    :param category_name: the category name (used in Blender preferences)
    :param properties: operator's properties
    """
    wm = bpy.context.window_manager

    # Keymaps fail to register when using Blender in background mode
    if bpy.app.background or not wm:
        return

    # Register a new keymap
    km = wm.keyconfigs.addon.keymaps.new(name=category_name, space_type=space_type)
    # Register a new keymap item
    kmi = km.keymap_items.new(operator, key, value, shift=shift, ctrl=ctrl, alt=alt)
    # Set the keymap active
    kmi.active = True
    addon_keymaps.append((km, kmi))
    # Set operator properties
    for name, value in properties.items():
        setattr(kmi.properties, name, value)

    return kmi


def register():
    pass


def unregister():
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

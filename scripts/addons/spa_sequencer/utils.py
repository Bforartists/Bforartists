# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2023, The SPA Studios. All rights reserved.
# This whole document is for the BFA - 3D Sequencer
"""
Addon level utility functions.
"""

import logging
import os
import re
from typing import Type

import bpy

import spa_sequencer
from spa_sequencer.keymaps import register_keymap

BlenderTypeClass = Type[bpy.types.bpy_struct]
BlenderOperatorTypeClass = Type[bpy.types.Operator]

log = logging.getLogger(__name__)


def register_classes(classes: tuple[BlenderTypeClass, ...]):
    """
    Register multiple subclasses of a Blender type class.

    For operators, if:

        * `bl_keymaps`: list of keymaps definitions as dicts
        * `bl_keymaps_defaults`: optional, keymap definition dict for common values

    are specified within the class definition, create the corresponding keymaps.
    Keymap definitions keys are the parameters of spa_sequencer.keymaps.register_keymap.

    For instance, the code sample below binds 2 keymaps to an operator:

    .. code-block:: python

        SEQUENCER_OT_operator_example(bpy.Types.Operator):
            bl_idname = "sequencer.operator_example"
            ...
            bl_keymaps_defaults = {
                "space_type": "SEQUENCE_EDITOR", "category_name": "Sequencer"
            }
            bl_keymaps = [
                {"key": "F", "ctrl": True, "properties": {"value" : 10}}
                {"key": "F", "alt": True, "properties": {"value" : -10}}
            ]
            value: bpy.props.IntProperty(...)


    :param classes: the classes to register
    """

    def register_operator_keymaps(op: BlenderOperatorTypeClass):
        """Register the keymaps attached to an operator class."""
        keymaps = getattr(op, "bl_keymaps", [])
        defaults = getattr(op, "bl_keymaps_defaults", {})

        if not isinstance(keymaps, list):
            raise TypeError("bl_keymaps: expected a list")

        if not isinstance(defaults, dict):
            raise TypeError("bl_keymaps_defaults: expected a dict")

        for keymap in keymaps:
            kwargs = defaults.copy()
            # Add operator's name to the arguments
            keymap["operator"] = op.bl_idname
            # Update defaults with current keymap arguments
            kwargs.update(keymap)
            try:
                register_keymap(**kwargs)
            except Exception as e:
                log.warning(f"Failed to register {op.bl_idname} keymap: {e}")
                continue

    for c in classes:
        bpy.utils.register_class(c)
        if issubclass(c, (bpy.types.Operator, bpy.types.Macro)):
            try:
                register_operator_keymaps(c)
            except Exception as e:
                log.warning(f"Failed to register {c.bl_idname} keymaps: {e}")


def unregister_classes(classes: tuple[BlenderTypeClass, ...], reverse=True):
    """Unregister multiple subclasses of a Blender type class.

    :param classes: the classes to unregister
    """
    for c in reversed(classes) if reverse else classes:
        bpy.utils.unregister_class(c)


def remove_auto_numbering_suffix(name: str) -> str:
    """Remove Blender's auto numbering suffix from `name`.

    :param name: The name to consider
    :return: The name without numbering suffix if any
    """
    return re.sub(r".\d{3}$", "", name)


def get_addon_directory() -> str:
    return os.path.dirname(spa_sequencer.__file__)

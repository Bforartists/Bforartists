# SPDX-FileCopyrightText: 2021-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""Declare pov native file syntax properties controllable in UI hooks and text blocks"""

import bpy
from bpy.utils import register_class, unregister_class
from bpy.types import PropertyGroup
from bpy.props import EnumProperty, PointerProperty

# ---------------------------------------------------------------- #
# Text POV properties.
# ---------------------------------------------------------------- #


class RenderPovSettingsText(PropertyGroup):

    """Declare text properties to use UI as an IDE or render text snippets to POV."""

    custom_code: EnumProperty(
        name="Custom Code",
        description="rendered source: Both adds text at the " "top of the exported POV file",
        items=(("3dview", "View", ""), ("text", "Text", ""), ("both", "Both", "")),
        default="3dview",
    )


classes = (RenderPovSettingsText,)


def register():
    for cls in classes:
        register_class(cls)
    bpy.types.Text.pov = PointerProperty(type=RenderPovSettingsText)


def unregister():
    del bpy.types.Text.pov
    for cls in reversed(classes):
        unregister_class(cls)

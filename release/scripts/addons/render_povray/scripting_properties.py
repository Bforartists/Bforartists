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

# <pep8 compliant>

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
        default="text",
    )


classes = (
    RenderPovSettingsText,
)


def register():
    for cls in classes:
        register_class(cls)
    bpy.types.Text.pov = PointerProperty(type=RenderPovSettingsText)


def unregister():
    del bpy.types.Text.pov
    for cls in reversed(classes):
        unregister_class(cls)

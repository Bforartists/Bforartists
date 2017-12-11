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

import bpy
from bpy.props import (
        StringProperty,
        BoolProperty,
        IntProperty,
        CollectionProperty,
        )

########################################################################################################################
# Global properties for the script, for UI (as there’s no way to let them in the operator…).
########################################################################################################################

class RenderCopySettingsDataScene(bpy.types.PropertyGroup):
    allowed = BoolProperty(default=True)


class RenderCopySettingsDataSetting(bpy.types.PropertyGroup):
    strid = StringProperty(default="")
    copy = BoolProperty(default=False)


class RenderCopySettingsData(bpy.types.PropertyGroup):
    # XXX: The consistency of this collection is delegated to the UI code.
    #      It should only contain one element for each render setting.
    affected_settings = CollectionProperty(type=RenderCopySettingsDataSetting,
                                           name="Affected Settings",
                                           description="The list of all available render settings")
    # XXX Unused, but needed for template_list…
    affected_settings_idx = IntProperty()

    # XXX: The consistency of this collection is delegated to the UI code.
    #      It should only contain one element for each scene.
    allowed_scenes = CollectionProperty(type=RenderCopySettingsDataScene,
                                        name="Allowed Scenes",
                                        description="The list all scenes in the file")
    # XXX Unused, but needed for template_list…
    allowed_scenes_idx = IntProperty()

    filter_scene = StringProperty(name="Filter Scene",
                                  description="Regex to only affect scenes which name matches it",
                                  default="")


classes = (
    RenderCopySettingsDataScene,
    RenderCopySettingsDataSetting,
    RenderCopySettingsData,
)

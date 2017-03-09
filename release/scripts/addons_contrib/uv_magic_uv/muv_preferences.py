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
__version__ = "4.1"
__date__ = "13 Nov 2016"


import bpy
from bpy.props import *
from bpy.types import AddonPreferences

class MUV_Preferences(AddonPreferences):
    """Preferences class: Preferences for this add-on"""

    bl_idname = __package__

    enable_texproj = BoolProperty(
            name="Enable feature: Texture Projection",
            default=False,
            )

    enable_uvbb = BoolProperty(
            name="Enable feature: UV Bounding Box",
            default=False,
            )

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "enable_uvbb")
        layout.prop(self, "enable_texproj")

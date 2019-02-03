### BEGIN GPL LICENSE BLOCK #####
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

# --------------------------------------------------------------------------
# The sun positioning algorithms are based on the National Oceanic
# and Atmospheric Administration's (NOAA) Solar Position Calculator
# which rely on calculations of Jean Meeus' book "Astronomical Algorithms."
# Use of NOAA data and products are in the public domain and may be used
# freely by the public as outlined in their policies at
#               www.nws.noaa.gov/disclaimer.php
# --------------------------------------------------------------------------
# The world map images have been composited from two NASA images.
# NASA's image use policy can be found at:
# http://www.nasa.gov/audience/formedia/features/MP_Photo_Guidelines.html
# --------------------------------------------------------------------------

# <pep8 compliant>

bl_info = {
    "name": "Sun Position",
    "author": "Michael Martin",
    "version": (3, 0, 1),
    "blender": (2, 65, 0),
    "api": 53207,
    "location": "World > Sun Position",
    "description": "Show sun position with objects and/or sky texture",
    "warning": "",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/"
    "Scripts/3D_interaction/Sun_Position",
    "tracker_url": "https://projects.blender.org/tracker/"
    "index.php?func=detail&aid=29714",
    "category": "Lighting"}

import bpy
from . properties import *
from . ui_sun import *
from . map import SunPos_Help
from . hdr import SunPos_HdrHelp

############################################################################


def register():
    bpy.utils.register_class(SunPosSettings)
    bpy.types.Scene.SunPos_property = (
        bpy.props.PointerProperty(type=SunPosSettings,
                                  name="Sun Position",
                                  description="Sun Position Settings"))
    bpy.utils.register_class(SunPosPreferences)
    bpy.types.Scene.SunPos_pref_property = (
        bpy.props.PointerProperty(type=SunPosPreferences,
                                  name="Sun Position Preferences",
                                  description="SP Preferences"))

    bpy.utils.register_class(SunPos_OT_Controller)
    bpy.utils.register_class(SunPos_OT_Preferences)
    bpy.utils.register_class(SunPos_OT_PreferencesDone)
    bpy.utils.register_class(SunPos_OT_DayRange)
    bpy.utils.register_class(SunPos_OT_SetObjectGroup)
    bpy.utils.register_class(SunPos_OT_ClearObjectGroup)
    bpy.utils.register_class(SunPos_OT_TimePlace)
    bpy.utils.register_class(SunPos_OT_Map)
    bpy.utils.register_class(SunPos_OT_Hdr)
    bpy.utils.register_class(SunPos_Panel)
    bpy.utils.register_class(SunPos_OT_MapChoice)
    bpy.utils.register_class(SunPos_Help)
    bpy.utils.register_class(SunPos_HdrHelp)


def unregister():
    bpy.utils.unregister_class(SunPos_HdrHelp)
    bpy.utils.unregister_class(SunPos_Help)
    bpy.utils.unregister_class(SunPos_OT_MapChoice)
    bpy.utils.unregister_class(SunPos_Panel)
    bpy.utils.unregister_class(SunPos_OT_Hdr)
    bpy.utils.unregister_class(SunPos_OT_Map)
    bpy.utils.unregister_class(SunPos_OT_TimePlace)
    bpy.utils.unregister_class(SunPos_OT_ClearObjectGroup)
    bpy.utils.unregister_class(SunPos_OT_SetObjectGroup)
    bpy.utils.unregister_class(SunPos_OT_DayRange)
    bpy.utils.unregister_class(SunPos_OT_PreferencesDone)
    bpy.utils.unregister_class(SunPos_OT_Preferences)
    bpy.utils.unregister_class(SunPos_OT_Controller)
    del bpy.types.Scene.SunPos_pref_property
    bpy.utils.unregister_class(SunPosPreferences)
    del bpy.types.Scene.SunPos_property
    bpy.utils.unregister_class(SunPosSettings)

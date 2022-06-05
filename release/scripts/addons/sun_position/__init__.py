# SPDX-License-Identifier: GPL-2.0-or-later

# --------------------------------------------------------------------------
# The sun positioning algorithms are based on the National Oceanic
# and Atmospheric Administration's (NOAA) Solar Position Calculator
# which rely on calculations of Jean Meeus' book "Astronomical Algorithms."
# Use of NOAA data and products are in the public domain and may be used
# freely by the public as outlined in their policies at
#               www.nws.noaa.gov/disclaimer.php
# --------------------------------------------------------------------------
# The geo parser script is by Maximilian Högner, released
# under the GNU GPL license:
# http://hoegners.de/Maxi/geo/
# --------------------------------------------------------------------------

bl_info = {
    "name": "Sun Position",
    "author": "Michael Martin",
    "version": (3, 1, 2),
    "blender": (3, 0, 0),
    "location": "World > Sun Position",
    "description": "Show sun position with objects and/or sky texture",
    "doc_url": "{BLENDER_MANUAL_URL}/addons/lighting/sun_position.html",
    "category": "Lighting",
}

if "bpy" in locals():
    import importlib
    importlib.reload(properties)
    importlib.reload(ui_sun)
    importlib.reload(hdr)

else:
    from . import properties, ui_sun, hdr

import bpy


def register():
    bpy.utils.register_class(properties.SunPosProperties)
    bpy.types.Scene.sun_pos_properties = (
        bpy.props.PointerProperty(type=properties.SunPosProperties,
                        name="Sun Position",
                        description="Sun Position Settings"))
    bpy.utils.register_class(properties.SunPosAddonPreferences)
    bpy.utils.register_class(ui_sun.SUNPOS_OT_AddPreset)
    bpy.utils.register_class(ui_sun.SUNPOS_MT_Presets)
    bpy.utils.register_class(ui_sun.SUNPOS_PT_Panel)
    bpy.utils.register_class(ui_sun.SUNPOS_PT_Location)
    bpy.utils.register_class(ui_sun.SUNPOS_PT_Time)
    bpy.utils.register_class(hdr.SUNPOS_OT_ShowHdr)

    bpy.app.handlers.frame_change_post.append(sun_calc.sun_handler)


def unregister():
    bpy.utils.unregister_class(hdr.SUNPOS_OT_ShowHdr)
    bpy.utils.unregister_class(ui_sun.SUNPOS_PT_Panel)
    bpy.utils.unregister_class(ui_sun.SUNPOS_PT_Location)
    bpy.utils.unregister_class(ui_sun.SUNPOS_PT_Time)
    bpy.utils.unregister_class(ui_sun.SUNPOS_MT_Presets)
    bpy.utils.unregister_class(ui_sun.SUNPOS_OT_AddPreset)
    bpy.utils.unregister_class(properties.SunPosAddonPreferences)
    del bpy.types.Scene.sun_pos_properties
    bpy.utils.unregister_class(properties.SunPosProperties)

    bpy.app.handlers.frame_change_post.remove(sun_calc.sun_handler)

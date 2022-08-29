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
    importlib.reload(translations)

else:
    from . import properties, ui_sun, hdr, translations

import bpy


register_classes, unregister_classes = bpy.utils.register_classes_factory(
    (properties.SunPosProperties,
     properties.SunPosAddonPreferences, ui_sun.SUNPOS_OT_AddPreset,
     ui_sun.SUNPOS_MT_Presets, ui_sun.SUNPOS_PT_Panel,
     ui_sun.SUNPOS_PT_Location, ui_sun.SUNPOS_PT_Time, hdr.SUNPOS_OT_ShowHdr))


def register():
    register_classes()
    bpy.types.Scene.sun_pos_properties = (
        bpy.props.PointerProperty(type=properties.SunPosProperties,
                                  name="Sun Position",
                                  description="Sun Position Settings"))
    bpy.app.handlers.frame_change_post.append(sun_calc.sun_handler)
    bpy.app.translations.register(__name__, translations.translations_dict)

def unregister():
    bpy.app.translations.unregister(__name__)
    bpy.app.handlers.frame_change_post.remove(sun_calc.sun_handler)
    del bpy.types.Scene.sun_pos_properties
    unregister_classes()

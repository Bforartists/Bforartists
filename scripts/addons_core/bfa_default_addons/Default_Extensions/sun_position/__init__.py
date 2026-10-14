# SPDX-FileCopyrightText: 2011-2012 Michael Martin
# SPDX-FileCopyrightText: 2019-2025 Damien Picard
#
# SPDX-License-Identifier: GPL-3.0-or-later

# --------------------------------------------------------------------------
# The sun positioning algorithms are based on the National Oceanic and
# Atmospheric Administration's (NOAA) Solar Calculator which relies on
# calculations from Jean Meeus' book "Astronomical Algorithms."
# Use of NOAA data and products are in the public domain and may be used freely
# by the public as outlined in their policies at:
# https://gml.noaa.gov/about/disclaimer.html
# --------------------------------------------------------------------------
# The geo parser script is by Maximilian Högner, released
# under the GNU GPL license:
# https://hoegners.de/Maxi/geo/
# --------------------------------------------------------------------------


if "bpy" in locals():
    import importlib

    importlib.reload(draw)
    importlib.reload(environment)
    importlib.reload(operators)
    importlib.reload(properties)
    importlib.reload(sun_calc)
    importlib.reload(translations)
    importlib.reload(ui_sun)
else:
    from . import (
        draw,
        environment,
        operators,
        properties,
        sun_calc,
        translations,
        ui_sun,
    )

import bpy
from bpy.app.handlers import persistent


register_classes, unregister_classes = bpy.utils.register_classes_factory(
    (
        properties.SunPosProperties,
        properties.SunPosAddonPreferences,
        operators.SUNPOS_OT_Create_Analemmas_Object,
        operators.SUNPOS_OT_Create_Surface_Object,
        ui_sun.SUNPOS_OT_AddPreset,
        ui_sun.SUNPOS_PT_Presets,
        ui_sun.SUNPOS_PT_Panel,
        ui_sun.SUNPOS_PT_Location,
        ui_sun.SUNPOS_PT_Time,
        environment.SUNPOS_OT_ShowEnvironment,
    )
)


@persistent
def sun_frame_handler(scene):
    sun_props = scene.sun_pos_properties
    if sun_props.usage_mode == "ENVIRONMENT":
        sun_calc.move_sun_env(scene)
    else:
        sun_calc.move_sun(scene)

    if not (bpy.app.is_job_running("RENDER") or bpy.app.is_job_running("OBJECT_BAKE")):
        if sun_props.show_surface or sun_props.show_analemmas:
            draw.analemmas_surface_update(scene)
        if sun_props.show_north:
            draw.north_update(scene)


@persistent
def sun_scene_handler(_filename):
    """Update drawing on file load."""
    scene = bpy.context.scene
    sun_props = scene.sun_pos_properties

    # Force drawing update
    draw.analemmas_surface_update(scene)
    draw.north_update(scene)

    # Force coordinates update
    if sun_props.usage_mode == "NORMAL":
        sun_props.latitude = sun_props.latitude


def register():
    import os

    register_classes()
    bpy.types.Scene.sun_pos_properties = bpy.props.PointerProperty(
        type=properties.SunPosProperties,
        name="Sun Position",
        description="Sun Position Settings",
    )
    bpy.app.handlers.frame_change_post.append(sun_frame_handler)
    bpy.app.handlers.load_post.append(sun_scene_handler)
    bpy.app.translations.register(__name__, translations.translations_dict)
    bpy.utils.register_preset_path(os.path.dirname(__file__))


def unregister():
    import os

    bpy.utils.unregister_preset_path(os.path.dirname(__file__))
    bpy.app.translations.unregister(__name__)
    bpy.app.handlers.frame_change_post.remove(sun_frame_handler)
    bpy.app.handlers.load_post.remove(sun_scene_handler)
    del bpy.types.Scene.sun_pos_properties
    unregister_classes()

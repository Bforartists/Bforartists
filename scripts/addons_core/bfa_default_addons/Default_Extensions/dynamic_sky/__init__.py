# SPDX-FileCopyrightText: 2015 Pratik Solanki (Draguu)
#
# SPDX-License-Identifier: GPL-2.0-or-later

import os

import bpy
from bpy.props import BoolProperty, EnumProperty, FloatProperty, IntProperty, StringProperty

from . import presets, sky, sun, ui


_classes = (
    sky.dsky,
    sky.DYNSKY_OT_use_world,
    sky.DYNSKY_OT_migrate,
    sky.DYNSKY_OT_bake_world,
    sky.DYNSKY_OT_export_hdri,
    presets.DYNSKY_MT_presets,
    presets.DYNSKY_OT_preset_add,
    presets.DYNSKY_OT_preset_apply,
    presets.DYNSKY_OT_preset_save,
    presets.DYNSKY_OT_preset_delete,
    presets.DYNSKY_OT_preset_duplicate,
    presets.DYNSKY_OT_preset_export,
    presets.DYNSKY_OT_preset_import,
    presets.DYNSKY_OT_sky_reset,
    sun.DYNSKY_OT_sun_add,
    sun.DYNSKY_OT_sun_remove,
    sun.DYNSKY_OT_sun_select,
    sun.DYNSKY_GGT_sun,
    ui.DYNSKY_OT_world_remove,
    # parent panel before its children
    ui.DYNSKY_PT_main,
    ui.DYNSKY_PT_presets,
    ui.DYNSKY_PT_time,
    ui.DYNSKY_PT_sun,
    ui.DYNSKY_PT_background,
    ui.DYNSKY_PT_atmosphere,
    ui.DYNSKY_PT_clouds,
    ui.DYNSKY_PT_night,
    ui.DYNSKY_PT_footer,
)


def register():
    for cls in _classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.dynamic_sky_name = StringProperty(
            name="",
            default="Dynamic"
            )
    bpy.types.World.dynamic_sky_time = FloatProperty(
            name="Time of Day",
            description="Drive the sky sun along a simple arc "
                        "(rise 6:00, noon 12:00, set 18:00); keyframeable",
            min=0.0, max=24.0, default=12.0,
            get=sun._time_get, set=sun._time_set,
            )
    bpy.types.Scene.dynamic_sky_sun_index = IntProperty(default=0, min=0)
    bpy.types.Scene.dynamic_sky_elevation = FloatProperty(
            name="Elevation",
            description="Height of the selected sun above the horizon",
            subtype='ANGLE', soft_min=-1.5708, soft_max=1.5708,
            get=sun._elevation_get, set=sun._elevation_set,
            )
    bpy.types.Scene.dynamic_sky_azimuth = FloatProperty(
            name="Azimuth",
            description="Compass direction of the selected sun (0 = north)",
            subtype='ANGLE', soft_min=0.0, soft_max=6.2832,
            get=sun._azimuth_get, set=sun._azimuth_set,
            )
    bpy.types.Scene.dynamic_sky_show_gizmo = BoolProperty(
            name="Sun gizmo in viewport",
            description="Show elevation/azimuth dials in the 3D view",
            default=False,
            )
    bpy.types.World.dynsky_background_mode = EnumProperty(
            name="Background",
            description="What fills the sky background",
            items=(('PROCEDURAL', "Procedural", "The procedural sky only"),
                   ('HDRI', "HDRI", "The environment image only"),
                   ('HYBRID', "Hybrid", "Blend of procedural sky and image")),
            default='PROCEDURAL',
            update=ui._background_mode_update,
            )
    bpy.types.World.dynsky_hybrid_blend = FloatProperty(
            name="Hybrid Blend",
            description="Last used Hybrid blend, restored on re-entering Hybrid",
            default=0.5, min=0.0, max=1.0,
            )
    bpy.types.World.dynsky_clouds_over_hdri = BoolProperty(
            name="Procedural clouds over",
            description="Composite the procedural clouds over the HDRI",
            get=ui._clouds_over_get, set=ui._clouds_over_set,
            )
    bpy.app.handlers.load_post.append(sky._migrate_all)
    bpy.app.handlers.frame_change_post.append(sun._sun_time_frame)
    # register() runs in a restricted context; a one-shot timer covers
    # "extension enabled while a file is already open"
    bpy.app.timers.register(sky._migrate_all, first_interval=0)
    # Bundled starter presets (presets/dynamic_sky/) join the user's own
    # in the menu
    bpy.utils.register_preset_path(os.path.dirname(__file__))


def unregister():
    bpy.utils.unregister_preset_path(os.path.dirname(__file__))
    if sky._migrate_all in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(sky._migrate_all)
    if sun._sun_time_frame in bpy.app.handlers.frame_change_post:
        bpy.app.handlers.frame_change_post.remove(sun._sun_time_frame)
    if bpy.app.timers.is_registered(sky._migrate_all):
        bpy.app.timers.unregister(sky._migrate_all)
    for cls in _classes:
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.dynamic_sky_name
    del bpy.types.World.dynamic_sky_time
    del bpy.types.Scene.dynamic_sky_sun_index
    del bpy.types.Scene.dynamic_sky_elevation
    del bpy.types.Scene.dynamic_sky_azimuth
    del bpy.types.Scene.dynamic_sky_show_gizmo
    del bpy.types.World.dynsky_background_mode
    del bpy.types.World.dynsky_hybrid_blend
    del bpy.types.World.dynsky_clouds_over_hdri
    presets.clear_thumbs()


if __name__ == "__main__":
    register()

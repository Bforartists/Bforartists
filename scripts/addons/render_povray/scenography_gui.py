# SPDX-FileCopyrightText: 2021-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""User interface to camera frame, optics distortions, and environment

with world, sky, atmospheric effects such as rainbows or smoke """

import bpy
from bpy.utils import register_class, unregister_class
from bpy.types import Operator, Menu, Panel
from bl_operators.presets import AddPresetBase

from bl_ui import properties_data_camera

for member in dir(properties_data_camera):
    subclass = getattr(properties_data_camera, member)
    if hasattr(subclass, "COMPAT_ENGINES"):
        subclass.COMPAT_ENGINES.add("POVRAY_RENDER")
del properties_data_camera

# -------- Use only a subset of the world panels
# from bl_ui import properties_world

# # TORECREATE##DEPRECATED#properties_world.WORLD_PT_preview.COMPAT_ENGINES.add('POVRAY_RENDER')
# properties_world.WORLD_PT_context_world.COMPAT_ENGINES.add('POVRAY_RENDER')
# # TORECREATE##DEPRECATED#properties_world.WORLD_PT_world.COMPAT_ENGINES.add('POVRAY_RENDER')
# del properties_world

# -------- #
# Physics Main wrapping every class 'as is'
from bl_ui import properties_physics_common

for member in dir(properties_physics_common):
    subclass = getattr(properties_physics_common, member)
    if hasattr(subclass, "COMPAT_ENGINES"):
        subclass.COMPAT_ENGINES.add("POVRAY_RENDER")
del properties_physics_common

# Physics Rigid Bodies wrapping every class 'as is'
from bl_ui import properties_physics_rigidbody

for member in dir(properties_physics_rigidbody):
    subclass = getattr(properties_physics_rigidbody, member)
    if hasattr(subclass, "COMPAT_ENGINES"):
        subclass.COMPAT_ENGINES.add("POVRAY_RENDER")
del properties_physics_rigidbody

# Physics Rigid Body Constraint wrapping every class 'as is'
from bl_ui import properties_physics_rigidbody_constraint

for member in dir(properties_physics_rigidbody_constraint):
    subclass = getattr(properties_physics_rigidbody_constraint, member)
    if hasattr(subclass, "COMPAT_ENGINES"):
        subclass.COMPAT_ENGINES.add("POVRAY_RENDER")
del properties_physics_rigidbody_constraint

# Physics Smoke and fluids wrapping every class 'as is'
from bl_ui import properties_physics_fluid

for member in dir(properties_physics_fluid):
    subclass = getattr(properties_physics_fluid, member)
    if hasattr(subclass, "COMPAT_ENGINES"):
        subclass.COMPAT_ENGINES.add("POVRAY_RENDER")
del properties_physics_fluid

# Physics softbody wrapping every class 'as is'
from bl_ui import properties_physics_softbody

for member in dir(properties_physics_softbody):
    subclass = getattr(properties_physics_softbody, member)
    if hasattr(subclass, "COMPAT_ENGINES"):
        subclass.COMPAT_ENGINES.add("POVRAY_RENDER")
del properties_physics_softbody

# Physics Field wrapping every class 'as is'
from bl_ui import properties_physics_field

for member in dir(properties_physics_field):
    subclass = getattr(properties_physics_field, member)
    if hasattr(subclass, "COMPAT_ENGINES"):
        subclass.COMPAT_ENGINES.add("POVRAY_RENDER")
del properties_physics_field

# Physics Cloth wrapping every class 'as is'
from bl_ui import properties_physics_cloth

for member in dir(properties_physics_cloth):
    subclass = getattr(properties_physics_cloth, member)
    if hasattr(subclass, "COMPAT_ENGINES"):
        subclass.COMPAT_ENGINES.add("POVRAY_RENDER")
del properties_physics_cloth

# Physics Dynamic Paint wrapping every class 'as is'
from bl_ui import properties_physics_dynamicpaint

for member in dir(properties_physics_dynamicpaint):
    subclass = getattr(properties_physics_dynamicpaint, member)
    if hasattr(subclass, "COMPAT_ENGINES"):
        subclass.COMPAT_ENGINES.add("POVRAY_RENDER")
del properties_physics_dynamicpaint

from bl_ui import properties_particle

for member in dir(properties_particle):  # add all "particle" panels from blender
    subclass = getattr(properties_particle, member)
    if hasattr(subclass, "COMPAT_ENGINES"):
        subclass.COMPAT_ENGINES.add("POVRAY_RENDER")
del properties_particle


class CameraDataButtonsPanel:
    """Use this class to define buttons from the camera data tab of
    properties window."""

    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "data"
    COMPAT_ENGINES = {"POVRAY_RENDER"}

    @classmethod
    def poll(cls, context):
        cam = context.camera
        rd = context.scene.render
        return cam and (rd.engine in cls.COMPAT_ENGINES)


class WorldButtonsPanel:
    """Use this class to define buttons from the world tab of
    properties window."""

    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "world"
    COMPAT_ENGINES = {"POVRAY_RENDER"}

    @classmethod
    def poll(cls, context):
        wld = context.world
        rd = context.scene.render
        return wld and (rd.engine in cls.COMPAT_ENGINES)


# ---------------------------------------------------------------- #
# Camera Settings
# ---------------------------------------------------------------- #
class CAMERA_PT_POV_cam_dof(CameraDataButtonsPanel, Panel):
    """Use this class for camera depth of field focal blur buttons."""

    bl_label = "POV Aperture"
    COMPAT_ENGINES = {"POVRAY_RENDER"}
    bl_parent_id = "DATA_PT_camera_dof_aperture"
    bl_options = {"HIDE_HEADER"}
    # def draw_header(self, context):
    # cam = context.camera

    # self.layout.prop(cam.pov, "dof_enable", text="")

    def draw(self, context):
        layout = self.layout

        cam = context.camera

        layout.active = cam.dof.use_dof
        layout.use_property_split = True  # Active single-column layout

        flow = layout.grid_flow(
            row_major=True, columns=0, even_columns=True, even_rows=False, align=False
        )

        col = flow.column()
        col.label(text="F-Stop value will export as")
        col.label(text="POV aperture : " + "%.3f" % (1 / cam.dof.aperture_fstop * 1000))

        col = flow.column()
        col.prop(cam.pov, "dof_samples_min")
        col.prop(cam.pov, "dof_samples_max")
        col.prop(cam.pov, "dof_variance")
        col.prop(cam.pov, "dof_confidence")


class CAMERA_PT_POV_cam_nor(CameraDataButtonsPanel, Panel):
    """Use this class for camera normal perturbation buttons."""

    bl_label = "POV Perturbation"
    COMPAT_ENGINES = {"POVRAY_RENDER"}

    def draw_header(self, context):
        cam = context.camera

        self.layout.prop(cam.pov, "normal_enable", text="")

    def draw(self, context):
        layout = self.layout

        cam = context.camera

        layout.active = cam.pov.normal_enable

        layout.prop(cam.pov, "normal_patterns")
        layout.prop(cam.pov, "cam_normal")
        layout.prop(cam.pov, "turbulence")
        layout.prop(cam.pov, "scale")


class CAMERA_PT_POV_replacement_text(CameraDataButtonsPanel, Panel):
    """Use this class for camera text replacement field."""

    bl_label = "Custom POV Code"
    COMPAT_ENGINES = {"POVRAY_RENDER"}

    def draw(self, context):
        layout = self.layout

        cam = context.camera

        col = layout.column()
        col.label(text="Replace properties with:")
        col.prop(cam.pov, "replacement_text", text="")


# ---------------------------------------------------------------- #
# World background and sky sphere Settings
# ---------------------------------------------------------------- #


class WORLD_PT_POV_world(WorldButtonsPanel, Panel):
    """Use this class to define pov world buttons"""

    bl_label = "World"

    COMPAT_ENGINES = {"POVRAY_RENDER"}

    def draw(self, context):
        layout = self.layout

        world = context.world.pov

        row = layout.row(align=True)
        row.menu(WORLD_MT_POV_presets.__name__, text=WORLD_MT_POV_presets.bl_label)
        row.operator(WORLD_OT_POV_add_preset.bl_idname, text="", icon="ADD")
        row.operator(WORLD_OT_POV_add_preset.bl_idname, text="", icon="REMOVE").remove_active = True

        row = layout.row()
        row.prop(world, "use_sky_paper")
        row.prop(world, "use_sky_blend")
        row.prop(world, "use_sky_real")

        row = layout.row()
        row.column().prop(world, "horizon_color")
        col = row.column()
        col.prop(world, "zenith_color")
        col.active = world.use_sky_blend
        row.column().prop(world, "ambient_color")

        # row = layout.row()
        # row.prop(world, "exposure") #Re-implement later as a light multiplier
        # row.prop(world, "color_range")


class WORLD_PT_POV_mist(WorldButtonsPanel, Panel):
    """Use this class to define pov mist buttons."""

    bl_label = "Mist"
    bl_options = {"DEFAULT_CLOSED"}
    COMPAT_ENGINES = {"POVRAY_RENDER"}

    def draw_header(self, context):
        world = context.world

        self.layout.prop(world.mist_settings, "use_mist", text="")

    def draw(self, context):
        layout = self.layout

        world = context.world

        layout.active = world.mist_settings.use_mist

        split = layout.split()

        col = split.column()
        col.prop(world.mist_settings, "intensity")
        col.prop(world.mist_settings, "start")

        col = split.column()
        col.prop(world.mist_settings, "depth")
        col.prop(world.mist_settings, "height")

        layout.prop(world.mist_settings, "falloff")


class WORLD_MT_POV_presets(Menu):
    """Apply world preset to all concerned properties"""

    bl_label = "World Presets"
    preset_subdir = "pov/world"
    preset_operator = "script.execute_preset"
    draw = bpy.types.Menu.draw_preset


class WORLD_OT_POV_add_preset(AddPresetBase, Operator):
    """Add a World Preset recording current values"""

    bl_idname = "object.world_preset_add"
    bl_label = "Add World Preset"
    preset_menu = "WORLD_MT_POV_presets"

    # variable used for all preset values
    preset_defines = ["scene = bpy.context.scene"]

    # properties to store in the preset
    preset_values = [
        "scene.world.use_sky_blend",
        "scene.world.horizon_color",
        "scene.world.zenith_color",
        "scene.world.ambient_color",
        "scene.world.mist_settings.use_mist",
        "scene.world.mist_settings.intensity",
        "scene.world.mist_settings.depth",
        "scene.world.mist_settings.start",
        "scene.pov.media_enable",
        "scene.pov.media_scattering_type",
        "scene.pov.media_samples",
        "scene.pov.media_diffusion_scale",
        "scene.pov.media_diffusion_color",
        "scene.pov.media_absorption_scale",
        "scene.pov.media_absorption_color",
        "scene.pov.media_eccentricity",
    ]

    # where to store the preset
    preset_subdir = "pov/world"


class RENDER_PT_POV_media(WorldButtonsPanel, Panel):
    """Use this class to define a pov global atmospheric media buttons."""

    bl_label = "Atmosphere Media"
    COMPAT_ENGINES = {"POVRAY_RENDER"}

    def draw_header(self, context):
        scene = context.scene

        self.layout.prop(scene.pov, "media_enable", text="")

    def draw(self, context):
        layout = self.layout

        scene = context.scene

        layout.active = scene.pov.media_enable

        col = layout.column()
        col.prop(scene.pov, "media_scattering_type", text="")
        col = layout.column()
        col.prop(scene.pov, "media_samples", text="Samples")
        split = layout.split()
        col = split.column(align=True)
        col.label(text="Scattering:")
        col.prop(scene.pov, "media_diffusion_scale")
        col.prop(scene.pov, "media_diffusion_color", text="")
        col = split.column(align=True)
        col.label(text="Absorption:")
        col.prop(scene.pov, "media_absorption_scale")
        col.prop(scene.pov, "media_absorption_color", text="")
        if scene.pov.media_scattering_type == "5":
            col = layout.column()
            col.prop(scene.pov, "media_eccentricity", text="Eccentricity")


# ---------------------------------------------------------------- #
# Lights settings
# ---------------------------------------------------------------- #

# ----------------------------------------------------------------
# from bl_ui import properties_data_light
# for member in dir(properties_data_light):
# subclass = getattr(properties_data_light, member)
# try:
# subclass.COMPAT_ENGINES.add('POVRAY_RENDER')
# except BaseException as e:
# print e.__doc__
# print('An exception occurred: {}'.format(e))
# pass
# del properties_data_light
# -------- LIGHTS -------- #

from bl_ui import properties_data_light

# -------- These panels are kept
# properties_data_light.DATA_PT_custom_props_light.COMPAT_ENGINES.add('POVRAY_RENDER')
# properties_data_light.DATA_PT_context_light.COMPAT_ENGINES.add('POVRAY_RENDER')

# make some native panels contextual to some object variable
# by recreating custom panels inheriting their properties


class PovLightButtonsPanel(properties_data_light.DataButtonsPanel):
    """Use this class to define buttons from the light data tab of
    properties window."""

    COMPAT_ENGINES = {"POVRAY_RENDER"}
    POV_OBJECT_TYPES = {"RAINBOW"}

    @classmethod
    def poll(cls, context):
        obj = context.object
        # We use our parent class poll func too, avoids to re-define too much things...
        return (
            super(PovLightButtonsPanel, cls).poll(context)
            and obj
            and obj.pov.object_as not in cls.POV_OBJECT_TYPES
        )


# We cannot inherit from RNA classes (like e.g. properties_data_mesh.DATA_PT_vertex_groups).
# Complex py/bpy/rna interactions (with metaclass and all) simply do not allow it to work.
# So we simply have to explicitly copy here the interesting bits. ;)
from bl_ui import properties_data_light

# for member in dir(properties_data_light):
# subclass = getattr(properties_data_light, member)
# try:
# subclass.COMPAT_ENGINES.add('POVRAY_RENDER')
# except BaseException as e:
# print(e.__doc__)
# print('An exception occurred: {}'.format(e))
# pass

# Now only These panels are kept
properties_data_light.DATA_PT_custom_props_light.COMPAT_ENGINES.add("POVRAY_RENDER")
properties_data_light.DATA_PT_context_light.COMPAT_ENGINES.add("POVRAY_RENDER")


class LIGHT_PT_POV_preview(PovLightButtonsPanel, Panel):
    # XXX Needs update and docstring
    bl_label = properties_data_light.DATA_PT_preview.bl_label

    draw = properties_data_light.DATA_PT_preview.draw


class LIGHT_PT_POV_light(PovLightButtonsPanel, Panel):
    """UI panel to main pov light parameters"""

    # bl_label = properties_data_light.DATA_PT_light.bl_label

    # draw = properties_data_light.DATA_PT_light.draw
    # class DATA_PT_POV_light(DataButtonsPanel, Panel):
    bl_label = "Light"
    # COMPAT_ENGINES = {'POVRAY_RENDER'}

    def draw(self, context):
        layout = self.layout

        light = context.light

        layout.row().prop(light, "type", expand=True)

        split = layout.split()

        col = split.column()
        sub = col.column()
        sub.prop(light, "color", text="")
        sub.prop(light, "energy")

        if light.type in {"POINT", "SPOT"}:
            sub.prop(light, "shadow_soft_size", text="Radius")

        if light.type == "AREA":
            col.prop(light, "shape")

            sub = col.column(align=True)

            if light.shape in {'SQUARE', 'DISK'}:
                sub.prop(light, "size")
            elif light.shape in {'RECTANGLE', 'ELLIPSE'}:
                sub.prop(light, "size", text="Size X")
                sub.prop(light, "size_y", text="Y")

        # restore later as interface to POV light groups ?
        # col = split.column()
        # col.prop(light, "use_own_layer", text="This Layer Only")


class LIGHT_MT_POV_presets(Menu):
    """Use this class to define preset menu for pov lights."""

    bl_label = "Lamp Presets"
    preset_subdir = "pov/light"
    preset_operator = "script.execute_preset"
    draw = bpy.types.Menu.draw_preset


class LIGHT_OT_POV_add_preset(AddPresetBase, Operator):
    """Operator to add a Light Preset"""

    bl_idname = "object.light_preset_add"
    bl_label = "Add Light Preset"
    preset_menu = "LIGHT_MT_POV_presets"

    # variable used for all preset values
    preset_defines = ["lightdata = bpy.context.object.data"]

    # properties to store in the preset
    preset_values = ["lightdata.type", "lightdata.color"]

    # where to store the preset
    preset_subdir = "pov/light"


# Draw into the existing light panel
def light_panel_func(self, context):
    """Menu to browse and add light preset"""
    layout = self.layout

    row = layout.row(align=True)
    row.menu(LIGHT_MT_POV_presets.__name__, text=LIGHT_MT_POV_presets.bl_label)
    row.operator(LIGHT_OT_POV_add_preset.bl_idname, text="", icon="ADD")
    row.operator(LIGHT_OT_POV_add_preset.bl_idname, text="", icon="REMOVE").remove_active = True


"""#TORECREATE##DEPRECATED#
class LIGHT_PT_POV_sunsky(PovLightButtonsPanel, Panel):
    bl_label = properties_data_light.DATA_PT_sunsky.bl_label

    @classmethod
    def poll(cls, context):
        lamp = context.light
        engine = context.scene.render.engine
        return (lamp and lamp.type == 'SUN') and (engine in cls.COMPAT_ENGINES)

    draw = properties_data_light.DATA_PT_sunsky.draw

"""


class LIGHT_PT_POV_shadow(PovLightButtonsPanel, Panel):
    # Todo : update and docstring
    bl_label = "Shadow"

    @classmethod
    def poll(cls, context):
        light = context.light
        engine = context.scene.render.engine
        return light and (engine in cls.COMPAT_ENGINES)

    def draw(self, context):
        layout = self.layout

        light = context.light

        layout.row().prop(light.pov, "shadow_method", expand=True)

        split = layout.split()
        col = split.column()

        col.prop(light.pov, "use_halo")
        sub = col.column(align=True)
        sub.active = light.pov.use_halo
        sub.prop(light.pov, "halo_intensity", text="Intensity")

        if light.pov.shadow_method == "NOSHADOW" and light.type == "AREA":
            split = layout.split()

            col = split.column()
            col.label(text="Form factor sampling:")

            sub = col.row(align=True)

            if light.shape == "SQUARE":
                sub.prop(light, "shadow_ray_samples_x", text="Samples")
            elif light.shape == "RECTANGLE":
                sub.prop(light.pov, "shadow_ray_samples_x", text="Samples X")
                sub.prop(light.pov, "shadow_ray_samples_y", text="Samples Y")

        if light.pov.shadow_method != "NOSHADOW":
            split = layout.split()

            col = split.column()
            col.prop(light, "shadow_color", text="")

            # col = split.column()
            # col.prop(light.pov, "use_shadow_layer", text="This Layer Only")
            # col.prop(light.pov, "use_only_shadow")

        if light.pov.shadow_method == "RAY_SHADOW":
            split = layout.split()

            col = split.column()
            col.label(text="Sampling:")

            if light.type in {"POINT", "SUN", "SPOT"}:
                sub = col.row()

                sub.prop(light.pov, "shadow_ray_samples_x", text="Samples")
                # any equivalent in pov?
                # sub.prop(light, "shadow_soft_size", text="Soft Size")

            elif light.type == "AREA":
                sub = col.row(align=True)

                if light.shape == "SQUARE":
                    sub.prop(light.pov, "shadow_ray_samples_x", text="Samples")
                elif light.shape == "RECTANGLE":
                    sub.prop(light.pov, "shadow_ray_samples_x", text="Samples X")
                    sub.prop(light.pov, "shadow_ray_samples_y", text="Samples Y")


class LIGHT_PT_POV_spot(PovLightButtonsPanel, Panel):
    bl_label = properties_data_light.DATA_PT_spot.bl_label
    bl_parent_id = "LIGHT_PT_POV_light"
    bl_context = "data"

    @classmethod
    def poll(cls, context):
        lamp = context.light
        engine = context.scene.render.engine
        return (lamp and lamp.type == "SPOT") and (engine in cls.COMPAT_ENGINES)

    draw = properties_data_light.DATA_PT_spot.draw


class OBJECT_PT_POV_rainbow(PovLightButtonsPanel, Panel):
    """Use this class to define buttons from the rainbow panel of
    properties window. inheriting lamp buttons panel class"""

    bl_label = "POV-Ray Rainbow"
    COMPAT_ENGINES = {"POVRAY_RENDER"}
    # bl_options = {'HIDE_HEADER'}

    @classmethod
    def poll(cls, context):
        engine = context.scene.render.engine
        obj = context.object
        return obj and obj.pov.object_as == "RAINBOW" and (engine in cls.COMPAT_ENGINES)

    def draw(self, context):
        layout = self.layout

        obj = context.object

        col = layout.column()

        if obj.pov.object_as == "RAINBOW":
            if not obj.pov.unlock_parameters:
                col.prop(
                    obj.pov, "unlock_parameters", text="Exported parameters below", icon="LOCKED"
                )
                col.label(text="Rainbow projection angle: " + str(obj.data.spot_size))
                col.label(text="Rainbow width: " + str(obj.data.spot_blend))
                col.label(text="Rainbow distance: " + str(obj.data.shadow_buffer_clip_start))
                col.label(text="Rainbow arc angle: " + str(obj.pov.arc_angle))
                col.label(text="Rainbow falloff angle: " + str(obj.pov.falloff_angle))

            else:
                col.prop(
                    obj.pov, "unlock_parameters", text="Edit exported parameters", icon="UNLOCKED"
                )
                col.label(text="3D view proxy may get out of synch")
                col.active = obj.pov.unlock_parameters

                layout.operator("pov.cone_update", text="Update", icon="MESH_CONE")

                # col.label(text="Parameters:")
                col.prop(obj.data, "spot_size", text="Rainbow Projection Angle")
                col.prop(obj.data, "spot_blend", text="Rainbow width")
                col.prop(obj.data, "shadow_buffer_clip_start", text="Visibility distance")
                col.prop(obj.pov, "arc_angle")
                col.prop(obj.pov, "falloff_angle")


del properties_data_light


classes = (
    WORLD_PT_POV_world,
    WORLD_MT_POV_presets,
    WORLD_OT_POV_add_preset,
    WORLD_PT_POV_mist,
    RENDER_PT_POV_media,
    LIGHT_PT_POV_preview,
    LIGHT_PT_POV_light,
    LIGHT_PT_POV_shadow,
    LIGHT_PT_POV_spot,
    LIGHT_MT_POV_presets,
    LIGHT_OT_POV_add_preset,
    OBJECT_PT_POV_rainbow,
    CAMERA_PT_POV_cam_dof,
    CAMERA_PT_POV_cam_nor,
    CAMERA_PT_POV_replacement_text,
)


def register():

    for cls in classes:
        register_class(cls)
    LIGHT_PT_POV_light.prepend(light_panel_func)


def unregister():
    LIGHT_PT_POV_light.remove(light_panel_func)
    for cls in reversed(classes):
        unregister_class(cls)

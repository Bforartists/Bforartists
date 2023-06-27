# SPDX-FileCopyrightText: 2021-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""Declare rendering properties controllable in UI"""

import bpy
from bpy.utils import register_class, unregister_class
from bpy.types import PropertyGroup, Scene
from bpy.props import (
    BoolProperty,
    IntProperty,
    FloatProperty,
    FloatVectorProperty,
    StringProperty,
    EnumProperty,
    PointerProperty,
)


# ---------------------------------------------------------------- #
# Scene POV properties.
# ---------------------------------------------------------------- #
class RenderPovSettingsScene(PropertyGroup):

    """Declare scene level properties controllable in UI and translated to POV"""

    # Linux SDL-window enable
    sdl_window_enable: BoolProperty(
        name="Enable SDL window", description="Enable the SDL window in Linux OS", default=True
    )
    # File Options
    text_block: StringProperty(
        name="Text Scene Name",
        description="Name of POV scene to use. "
        "Set when clicking Run to render current text only",
        maxlen=1024,
    )
    tempfiles_enable: BoolProperty(
        name="Enable Tempfiles",
        description="Enable the OS-Tempfiles. Otherwise set the path where to save the files",
        default=True,
    )
    pov_editor: BoolProperty(
        name="POV editor",
        description="Don't Close POV editor after rendering (Overridden by /EXIT command)",
        default=False,
    )
    deletefiles_enable: BoolProperty(
        name="Delete files",
        description="Delete files after rendering. Doesn't work with the image",
        default=True,
    )
    scene_name: StringProperty(
        name="Scene Name",
        description="Name of POV scene to create. Empty name will use "
        "the name of the blend file",
        maxlen=1024,
    )
    scene_path: StringProperty(
        name="Export scene path",
        # Bug in POV-Ray RC3
        # description="Path to directory where the exported scene "
        # "(POV and INI) is created",
        description="Path to directory where the files are created",
        maxlen=1024,
        subtype="DIR_PATH",
    )
    renderimage_path: StringProperty(
        name="Rendered image path",
        description="Full path to directory where the rendered image is saved",
        maxlen=1024,
        subtype="DIR_PATH",
    )
    list_lf_enable: BoolProperty(
        name="LF in lists",
        description="Enable line breaks in lists (vectors and indices). "
        "Disabled: lists are exported in one line",
        default=False,
    )

    # Not a real pov option, just to know if we should write
    radio_enable: BoolProperty(
        name="Enable Radiosity", description="Enable POV radiosity calculation", default=True
    )

    radio_display_advanced: BoolProperty(
        name="Advanced Options", description="Show advanced options", default=False
    )

    media_enable: BoolProperty(
        name="Enable Media", description="Enable POV atmospheric media", default=False
    )

    media_samples: IntProperty(
        name="Samples",
        description="Number of samples taken from camera to first object "
        "encountered along ray path for media calculation",
        min=1,
        max=100,
        default=35,
    )

    media_scattering_type: EnumProperty(
        name="Scattering Type",
        description="Scattering model",
        items=(
            (
                "1",
                "1 Isotropic",
                "The simplest form of scattering because it is independent of direction.",
            ),
            (
                "2",
                "2 Mie haze ",
                "For relatively small particles such as "
                "minuscule water droplets of fog, cloud "
                "particles, and particles responsible "
                "for the polluted sky. In this model the"
                " scattering is extremely directional in"
                " the forward direction i.e. the amount "
                "of scattered light is largest when the "
                "incident light is anti-parallel to the "
                "viewing direction (the light goes "
                "directly to the viewer). It is smallest"
                " when the incident light is parallel to"
                " the viewing direction. ",
            ),
            ("3", "3 Mie murky", "Like haze but much more directional"),
            (
                "4",
                "4 Rayleigh",
                "For extremely small particles such as "
                "molecules of the air. The amount of "
                "scattered light depends on the incident"
                " light angle. It is largest when the "
                "incident light is parallel or "
                "anti-parallel to the viewing direction "
                "and smallest when the incident light is "
                "perpendicular to viewing direction.",
            ),
            (
                "5",
                "5 Henyey-Greenstein",
                "The default eccentricity value "
                "of zero defines isotropic "
                "scattering while positive "
                "values lead to scattering in "
                "the direction of the light and "
                "negative values lead to "
                "scattering in the opposite "
                "direction of the light. Larger "
                "values of e (or smaller values "
                "in the negative case) increase "
                "the directional property of the"
                " scattering.",
            ),
        ),
        default="1",
    )

    media_diffusion_scale: FloatProperty(
        name="Scale",
        description="Scale factor of Media Diffusion Color",
        precision=6,
        step=0.00000001,
        min=0.000000001,
        max=1.0,
        default=1.0,
    )

    media_diffusion_color: FloatVectorProperty(
        name="Media Diffusion Color",
        description="The atmospheric media color",
        precision=4,
        step=0.01,
        min=0,
        soft_max=1,
        default=(0.001, 0.001, 0.001),
        options={"ANIMATABLE"},
        subtype="COLOR",
    )

    media_absorption_scale: FloatProperty(
        name="Scale",
        description="Scale factor of Media Absorption Color. "
        "use 1/depth of media volume in meters",
        precision=6,
        step=0.000001,
        min=0.000000001,
        max=1.0,
        default=0.00002,
    )

    media_absorption_color: FloatVectorProperty(
        name="Media Absorption Color",
        description="The atmospheric media absorption color",
        precision=4,
        step=0.01,
        min=0,
        soft_max=1,
        default=(0.0, 0.0, 0.0),
        options={"ANIMATABLE"},
        subtype="COLOR",
    )

    media_eccentricity: FloatProperty(
        name="Media Eccenticity Factor",
        description="Positive values lead"
        " to scattering in the direction of the light and negative "
        "values lead to scattering in the opposite direction of the "
        "light. Larger values of e (or smaller values in the negative"
        " case) increase the directional property of the scattering",
        precision=2,
        step=0.01,
        min=-1.0,
        max=1.0,
        default=0.0,
        options={"ANIMATABLE"},
    )

    baking_enable: BoolProperty(
        name="Enable Baking", description="Enable POV texture baking", default=False
    )

    indentation_character: EnumProperty(
        name="Indentation",
        description="Select the indentation type",
        items=(
            ("NONE", "None", "No indentation"),
            ("TAB", "Tabs", "Indentation with tabs"),
            ("SPACE", "Spaces", "Indentation with spaces"),
        ),
        default="SPACE",
    )

    indentation_spaces: IntProperty(
        name="Quantity of spaces",
        description="The number of spaces for indentation",
        min=1,
        max=10,
        default=4,
    )

    comments_enable: BoolProperty(
        name="Enable Comments", description="Add comments to pov file", default=True
    )

    # Real pov options
    command_line_switches: StringProperty(
        name="Command Line Switches",
        description="Command line switches consist of a + (plus) or - "
        "(minus) sign, followed by one or more alphabetic "
        "characters and possibly a numeric value",
        maxlen=500,
    )

    antialias_enable: BoolProperty(
        name="Anti-Alias", description="Enable Anti-Aliasing", default=True
    )

    antialias_method: EnumProperty(
        name="Method",
        description="AA-sampling method. Type 1 is an adaptive, "
        "non-recursive, super-sampling (as in the plain old render "
        "bigger and scale down trick. Type 2 is a slightly "
        "more efficient adaptive and recursive super-sampling. "
        "Type 3 is a stochastic halton based super-sampling method so "
        "rather artifact free and sampling rays so depth of field can "
        "use them at no additional cost, as do area lights and "
        "subsurface scattering materials, making it the best "
        "quality / time trade-off in complex scenes",
        items=(
            ("0", "non-recursive AA", "Type 1 Sampling in POV"),
            ("1", "recursive AA", "Type 2 Sampling in POV"),
            ("2", "stochastic AA", "Type 3 Sampling in POV"),
        ),
        default="1",
    )

    antialias_confidence: FloatProperty(
        name="Antialias Confidence",
        description="how surely the computed color "
        "of a given pixel is indeed"
        "within the threshold error margin",
        min=0.0001,
        max=1.0000,
        default=0.9900,
        precision=4,
    )

    antialias_depth: IntProperty(
        name="Antialias Depth", description="Depth of pixel for sampling", min=1, max=9, default=2
    )

    antialias_threshold: FloatProperty(
        name="Antialias Threshold",
        description="Tolerance for sub-pixels",
        min=0.0,
        max=1.0,
        soft_min=0.05,
        soft_max=0.5,
        default=0.03,
    )

    jitter_enable: BoolProperty(
        name="Jitter",
        description="Enable Jittering. Adds noise into the sampling "
        "process (it should be avoided to use jitter in "
        "animation)",
        default=False,
    )

    jitter_amount: FloatProperty(
        name="Jitter Amount",
        description="Amount of jittering",
        min=0.0,
        max=1.0,
        soft_min=0.01,
        soft_max=1.0,
        default=1.0,
    )

    antialias_gamma: FloatProperty(
        name="Antialias Gamma",
        description="POV-Ray compares gamma-adjusted values for super "
        "sampling. Antialias Gamma sets the Gamma before "
        "comparison",
        min=0.0,
        max=5.0,
        soft_min=0.01,
        soft_max=2.5,
        default=2.5,
    )

    alpha_filter: FloatProperty(
        name="Alpha",
        description="User defined color associated background alpha",
        min=0.0,
        max=1.0,
        soft_min=0.01,
        soft_max=1.0,
        default=0.75,
    )

    alpha_mode: EnumProperty(
        name="Alpha",
        description="Representation of alpha information in the RGBA pixels",
        items=(
            ("SKY", "Sky", "Transparent pixels are filled with sky color"),
            ("STRAIGHT", "Straight", "Transparent pixels are not premultiplied"),
            (
                "TRANSPARENT",
                "Transparent",
                "World background has user defined  premultiplied alpha",
            ),
        ),
        default="SKY",
    )

    use_shadows: BoolProperty(
        name="Shadows", description="Calculate shadows while rendering", default=True
    )

    max_trace_level: IntProperty(
        name="Max Trace Level",
        description="Number of reflections/refractions allowed on ray " "path",
        min=1,
        max=256,
        default=5,
    )

    adc_bailout_enable: BoolProperty(name="Enable", description="", default=False)

    adc_bailout: FloatProperty(
        name="ADC Bailout",
        description="Adaptive Depth Control (ADC) to stop computing additional"
        "reflected or refracted rays when their contribution is insignificant."
        "The default value is 1/255, or approximately 0.0039, since a change "
        "smaller than that could not be visible in a 24 bit image. Generally "
        "this value is fine and should be left alone."
        "Setting adc_bailout to 0 will disable ADC, relying completely on "
        "max_trace_level to set an upper limit on the number of rays spawned. ",
        min=0.0,
        max=1000.0,
        default=0.00392156862745,
        precision=3,
    )

    ambient_light_enable: BoolProperty(name="Enable", description="", default=False)

    ambient_light: FloatVectorProperty(
        name="Ambient Light",
        description="Ambient light is used to simulate the effect of inter-diffuse reflection",
        precision=4,
        step=0.01,
        min=0,
        soft_max=1,
        default=(1, 1, 1),
        options={"ANIMATABLE"},
        subtype="COLOR",
    )
    global_settings_advanced: BoolProperty(name="Advanced", description="", default=False)

    irid_wavelength_enable: BoolProperty(name="Enable", description="", default=False)

    irid_wavelength: FloatVectorProperty(
        name="Irid Wavelength",
        description=(
            "Iridescence calculations depend upon the dominant "
            "wavelengths of the primary colors of red, green and blue light"
        ),
        precision=4,
        step=0.01,
        min=0,
        soft_max=1,
        default=(0.25, 0.18, 0.14),
        options={"ANIMATABLE"},
        subtype="COLOR",
    )

    number_of_waves_enable: BoolProperty(name="Enable", description="", default=False)

    number_of_waves: IntProperty(
        name="Number Waves",
        description=(
            "The waves and ripples patterns are generated by summing a series of waves, "
            "each with a slightly different center and size"
        ),
        min=1,
        max=10,
        default=1000,
    )

    noise_generator_enable: BoolProperty(name="Enable", description="", default=False)

    noise_generator: IntProperty(
        name="Noise Generator",
        description="There are three noise generators implemented",
        min=1,
        max=3,
        default=2,
    )

    # -------- PHOTONS -------- #
    photon_enable: BoolProperty(name="Photons", description="Enable global photons", default=False)

    photon_enable_count: BoolProperty(
        name="Spacing / Count", description="Enable count photons", default=False
    )

    photon_count: IntProperty(
        name="Count", description="Photons count", min=1, max=100000000, default=20000
    )

    photon_spacing: FloatProperty(
        name="Spacing",
        description="Average distance between photons on surfaces. half "
        "this get four times as many surface photons",
        min=0.001,
        max=1.000,
        soft_min=0.001,
        soft_max=1.000,
        precision=3,
        default=0.005,
    )

    photon_max_trace_level: IntProperty(
        name="Max Trace Level",
        description="Number of reflections/refractions allowed on ray " "path",
        min=1,
        max=256,
        default=5,
    )

    photon_adc_bailout: FloatProperty(
        name="ADC Bailout",
        description="The adc_bailout for photons. Use adc_bailout = "
        "0.01 / brightest_ambient_object for good results",
        min=0.0,
        max=1000.0,
        soft_min=0.0,
        soft_max=1.0,
        precision=3,
        default=0.1,
    )

    photon_gather_min: IntProperty(
        name="Gather Min",
        description="Minimum number of photons gathered" "for each point",
        min=1,
        max=256,
        default=20,
    )

    photon_gather_max: IntProperty(
        name="Gather Max",
        description="Maximum number of photons gathered for each point",
        min=1,
        max=256,
        default=100,
    )

    photon_map_file_save_load: EnumProperty(
        name="Operation",
        description="Load or Save photon map file",
        items=(("NONE", "None", ""), ("save", "Save", ""), ("load", "Load", "")),
        default="NONE",
    )

    photon_map_filename: StringProperty(name="Filename", description="", maxlen=1024)

    photon_map_dir: StringProperty(
        name="Directory", description="", maxlen=1024, subtype="DIR_PATH"
    )

    photon_map_file: StringProperty(name="File", description="", maxlen=1024, subtype="FILE_PATH")

    # -------- RADIOSITY -------- #
    radio_adc_bailout: FloatProperty(
        name="ADC Bailout",
        description="The adc_bailout for radiosity rays. Use "
        "adc_bailout = 0.01 / brightest_ambient_object for good results",
        min=0.0,
        max=1000.0,
        soft_min=0.0,
        soft_max=1.0,
        default=0.0039,
        precision=4,
    )

    radio_always_sample: BoolProperty(
        name="Always Sample",
        description="Only use the data from the pretrace step and not gather "
        "any new samples during the final radiosity pass",
        default=False,
    )

    radio_brightness: FloatProperty(
        name="Brightness",
        description="Amount objects are brightened before being returned "
        "upwards to the rest of the system",
        min=0.0,
        max=1000.0,
        soft_min=0.0,
        soft_max=10.0,
        default=1.0,
    )

    radio_count: IntProperty(
        name="Ray Count",
        description="Number of rays for each new radiosity value to be calculated "
        "(halton sequence over 1600)",
        min=1,
        max=10000,
        soft_max=1600,
        default=35,
    )

    radio_error_bound: FloatProperty(
        name="Error Bound",
        description="One of the two main speed/quality tuning values, "
        "lower values are more accurate",
        min=0.0,
        max=1000.0,
        soft_min=0.1,
        soft_max=10.0,
        default=10.0,
    )

    radio_gray_threshold: FloatProperty(
        name="Gray Threshold",
        description="One of the two main speed/quality tuning values, "
        "lower values are more accurate",
        min=0.0,
        max=1.0,
        soft_min=0,
        soft_max=1,
        default=0.0,
    )

    radio_low_error_factor: FloatProperty(
        name="Low Error Factor",
        description="Just enough samples is slightly blotchy. Low error changes error "
        "tolerance for less critical last refining pass",
        min=0.000001,
        max=1.0,
        soft_min=0.000001,
        soft_max=1.0,
        default=0.5,
    )

    radio_media: BoolProperty(
        name="Media", description="Radiosity estimation can be affected by media", default=True
    )

    radio_subsurface: BoolProperty(
        name="Subsurface",
        description="Radiosity estimation can be affected by Subsurface Light Transport",
        default=False,
    )

    radio_minimum_reuse: FloatProperty(
        name="Minimum Reuse",
        description="Fraction of the screen width which sets the minimum radius of reuse "
        "for each sample point (At values higher than 2% expect errors)",
        min=0.0,
        max=1.0,
        soft_min=0.1,
        soft_max=0.1,
        default=0.015,
        precision=3,
    )

    radio_maximum_reuse: FloatProperty(
        name="Maximum Reuse",
        description="The maximum reuse parameter works in conjunction with, and is similar to that of minimum reuse, "
        "the only difference being that it is an upper bound rather than a lower one",
        min=0.0,
        max=1.0,
        default=0.2,
        precision=3,
    )

    radio_nearest_count: IntProperty(
        name="Nearest Count",
        description="Number of old ambient values blended together to "
        "create a new interpolated value",
        min=1,
        max=20,
        default=1,
    )

    radio_normal: BoolProperty(
        name="Normals", description="Radiosity estimation can be affected by normals", default=False
    )

    radio_recursion_limit: IntProperty(
        name="Recursion Limit",
        description="how many recursion levels are used to calculate "
        "the diffuse inter-reflection",
        min=1,
        max=20,
        default=1,
    )

    radio_pretrace_start: FloatProperty(
        name="Pretrace Start",
        description="Fraction of the screen width which sets the size of the "
        "blocks in the mosaic preview first pass",
        min=0.005,
        max=1.00,
        soft_min=0.02,
        soft_max=1.0,
        default=0.04,
    )
    # XXX TODO set automatically to  pretrace_end = 8 / max (image_width, image_height)
    # for non advanced mode
    radio_pretrace_end: FloatProperty(
        name="Pretrace End",
        description="Fraction of the screen width which sets the size of the blocks "
        "in the mosaic preview last pass",
        min=0.000925,
        max=1.00,
        soft_min=0.01,
        soft_max=1.00,
        default=0.004,
        precision=3,
    )


classes = (RenderPovSettingsScene,)


def register():
    for cls in classes:
        register_class(cls)
    Scene.pov = PointerProperty(type=RenderPovSettingsScene)


def unregister():
    del Scene.pov
    for cls in reversed(classes):
        unregister_class(cls)

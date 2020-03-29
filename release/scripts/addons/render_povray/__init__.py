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

"""Import, export and render to POV engines.

These engines can be POV-Ray or Uberpov but others too, since POV is a
Scene Description Language. The script has been split in as few files
as possible :

___init__.py :
    Initialize variables

update_files.py
    Update new variables to values from older API. This file needs an update.

ui.py :
    Provide property buttons for the user to set up the variables.

primitives.py :
    Display some POV native primitives in 3D view for input and output.

shading.py
    Translate shading properties to declared textures at the top of a pov file

nodes.py
    Translate node trees to the pov file

df3.py
    Render smoke to *.df3 files

render.py :
    Translate geometry and UI properties (Blender and POV native) to the POV file


Along these essential files also coexist a few additional libraries to help make
Blender stand up to other POV IDEs such as povwin or QTPOV.
    presets :
        Material (sss)
            apple.py ; chicken.py ; cream.py ; Ketchup.py ; marble.py ;
            potato.py ; skim_milk.py ; skin1.py ; skin2.py ; whole_milk.py
        Radiosity
            01_Debug.py ; 02_Fast.py ; 03_Normal.py ; 04_Two_Bounces.py ;
            05_Final.py ; 06_Outdoor_Low_Quality.py ; 07_Outdoor_High_Quality.py ;
            08_Outdoor(Sun)Light.py ; 09_Indoor_Low_Quality.py ;
            10_Indoor_High_Quality.py ;
        World
            01_Clear_Blue_Sky.py ; 02_Partly_Hazy_Sky.py ; 03_Overcast_Sky.py ;
            04_Cartoony_Sky.py ; 05_Under_Water.py ;
        Light
            01_(5400K)_Direct_Sun.py ; 02_(5400K)_High_Noon_Sun.py ;
            03_(6000K)_Daylight_Window.py ;
            04_(6000K)_2500W_HMI_(Halogen_Metal_Iodide).py ;
            05_(4000K)_100W_Metal_Halide.py ; 06_(3200K)_100W_Quartz_Halogen.py ;
            07_(2850K)_100w_Tungsten.py ; 08_(2600K)_40w_Tungsten.py ;
            09_(5000K)_75W_Full_Spectrum_Fluorescent_T12.py ;
            10_(4300K)_40W_Vintage_Fluorescent_T12.py ;
            11_(5000K)_18W_Standard_Fluorescent_T8 ;
            12_(4200K)_18W_Cool_White_Fluorescent_T8.py ;
            13_(3000K)_18W_Warm_Fluorescent_T8.py ;
            14_(6500K)_54W_Grow_Light_Fluorescent_T5-HO.py ;
            15_(3200K)_40W_Induction_Fluorescent.py ;
            16_(2100K)_150W_High_Pressure_Sodium.py ;
            17_(1700K)_135W_Low_Pressure_Sodium.py ;
            18_(6800K)_175W_Mercury_Vapor.py ; 19_(5200K)_700W_Carbon_Arc.py ;
            20_(6500K)_15W_LED_Spot.py ; 21_(2700K)_7W_OLED_Panel.py ;
            22_(30000K)_40W_Black_Light_Fluorescent.py ;
            23_(30000K)_40W_Black_Light_Bulb.py; 24_(1850K)_Candle.py
    templates:
        abyss.pov ; biscuit.pov ; bsp_Tango.pov ; chess2.pov ;
        cornell.pov ; diffract.pov ; diffuse_back.pov ; float5 ;
        gamma_showcase.pov ; grenadine.pov ; isocacti.pov ;
        mediasky.pov ; patio-radio.pov ; subsurface.pov ; wallstucco.pov
"""


bl_info = {
    "name": "Persistence of Vision",
    "author": "Campbell Barton, "
    "Maurice Raybaud, "
    "Leonid Desyatkov, "
    "Bastien Montagne, "
    "Constantin Rahn, "
    "Silvio Falcinelli",
    "version": (0, 1, 0),
    "blender": (2, 81, 0),
    "location": "Render Properties > Render Engine > Persistence of Vision",
    "description": "Persistence of Vision integration for blender",
    "doc_url": "{BLENDER_MANUAL_URL}/addons/render/povray.html",
    "category": "Render",
}

if "bpy" in locals():
    import importlib

    importlib.reload(ui)
    importlib.reload(render)
    importlib.reload(shading)
    importlib.reload(update_files)

else:
    import bpy
    from bpy.utils import register_class, unregister_class
    # import addon_utils  # To use some other addons
    import nodeitems_utils  # for Nodes
    from nodeitems_utils import NodeCategory, NodeItem  # for Nodes
    from bl_operators.presets import AddPresetBase
    from bpy.types import AddonPreferences, PropertyGroup
    from bpy.props import (
        StringProperty,
        BoolProperty,
        IntProperty,
        FloatProperty,
        FloatVectorProperty,
        EnumProperty,
        PointerProperty,
        CollectionProperty,
    )
    from . import ui, render, update_files


def string_strip_hyphen(name):

    """Remove hyphen characters from a string to avoid POV errors."""

    return name.replace("-", "")


def active_texture_name_from_uilist(self, context):
    mat = context.scene.view_layers["View Layer"].objects.active.active_material
    index = mat.pov.active_texture_index
    name = mat.pov_texture_slots[index].name
    newname = mat.pov_texture_slots[index].texture
    tex = bpy.data.textures[name]
    tex.name = newname
    mat.pov_texture_slots[index].name = newname


def active_texture_name_from_search(self, context):
    mat = context.scene.view_layers["View Layer"].objects.active.active_material
    index = mat.pov.active_texture_index
    name = mat.pov_texture_slots[index].texture_search
    try:
        tex = bpy.data.textures[name]
        mat.pov_texture_slots[index].name = name
        mat.pov_texture_slots[index].texture = name
    except:
        pass


###############################################################################
# Scene POV properties.
###############################################################################
class RenderPovSettingsScene(PropertyGroup):

    """Declare scene level properties controllable in UI and translated to POV."""

    # Linux SDL-window enable
    sdl_window_enable: BoolProperty(
        name="Enable SDL window",
        description="Enable the SDL window in Linux OS",
        default=True,
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
        description="Enable the OS-Tempfiles. Otherwise set the path where"
        " to save the files",
        default=True,
    )
    pov_editor: BoolProperty(
        name="POV editor",
        description="Don't Close POV editor after rendering (Overridden"
        " by /EXIT command)",
        default=False,
    )
    deletefiles_enable: BoolProperty(
        name="Delete files",
        description="Delete files after rendering. "
        "Doesn't work with the image",
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
        description="Full path to directory where the rendered image is "
        "saved",
        maxlen=1024,
        subtype="DIR_PATH",
    )
    list_lf_enable: BoolProperty(
        name="LF in lists",
        description="Enable line breaks in lists (vectors and indices). "
        "Disabled: lists are exported in one line",
        default=True,
    )

    # Not a real pov option, just to know if we should write
    radio_enable: BoolProperty(
        name="Enable Radiosity",
        description="Enable POV radiosity calculation",
        default=True,
    )

    radio_display_advanced: BoolProperty(
        name="Advanced Options",
        description="Show advanced options",
        default=False,
    )

    media_enable: BoolProperty(
        name="Enable Media",
        description="Enable POV atmospheric media",
        default=False,
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
                '1',
                "1 Isotropic",
                "The simplest form of scattering because"
                " it is independent of direction."
            ),
            (
                '2',
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
                " the viewing direction. "
            ),
            (
                '3',
                "3 Mie murky",
                "Like haze but much more directional"
            ),
            (
                '4',
                "4 Rayleigh",
                "For extremely small particles such as "
                "molecules of the air. The amount of "
                "scattered light depends on the incident"
                " light angle. It is largest when the "
                "incident light is parallel or "
                "anti-parallel to the viewing direction "
                "and smallest when the incident light is "
                "perpendicular to viewing direction."
            ),
            (
                '5',
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
                " scattering."
            )
        ),
        default='1',
    )

    media_diffusion_scale: FloatProperty(
        name="Scale",
        description="Scale factor of Media Diffusion Color",
        precision=12, step=0.00000001, min=0.000000001, max=1.0,
        default=(1.0),
    )

    media_diffusion_color: FloatVectorProperty(
        name="Media Diffusion Color",
        description="The atmospheric media color",
        precision=4, step=0.01, min=0, soft_max=1,
        default=(0.001, 0.001, 0.001),
        options={'ANIMATABLE'},
        subtype='COLOR',
    )

    media_absorption_scale: FloatProperty(
        name="Scale",
        description="Scale factor of Media Absorption Color. "
        "use 1/depth of media volume in meters",
        precision=12,
        step=0.000001,
        min=0.000000001,
        max=1.0,
        default=(0.00002),
    )

    media_absorption_color: FloatVectorProperty(
        name="Media Absorption Color",
        description="The atmospheric media absorption color",
        precision=4, step=0.01, min=0, soft_max=1,
        default=(0.0, 0.0, 0.0),
        options={'ANIMATABLE'},
        subtype='COLOR',
    )

    media_eccentricity: FloatProperty(
        name="Media Eccenticity Factor",
        description="Positive values lead"
        " to scattering in the direction of the light and negative "
        "values lead to scattering in the opposite direction of the "
        "light. Larger values of e (or smaller values in the negative"
        " case) increase the directional property of the scattering.",
        precision=2,
        step=0.01,
        min=-1.0,
        max=1.0,
        default=(0.0),
        options={'ANIMATABLE'},
    )

    baking_enable: BoolProperty(
        name="Enable Baking",
        description="Enable POV texture baking",
        default=False
    )

    indentation_character: EnumProperty(
        name="Indentation",
        description="Select the indentation type",
        items=(
            ('NONE', "None", "No indentation"),
            ('TAB', "Tabs", "Indentation with tabs"),
            ('SPACE', "Spaces", "Indentation with spaces")
        ),
        default='SPACE'
    )

    indentation_spaces: IntProperty(
        name="Quantity of spaces",
        description="The number of spaces for indentation",
        min=1,
        max=10,
        default=4,
    )

    comments_enable: BoolProperty(
        name="Enable Comments",
        description="Add comments to pov file",
        default=True,
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
        name="Anti-Alias", description="Enable Anti-Aliasing",
        default=True,
    )

    antialias_method: EnumProperty(
        name="Method",
        description="AA-sampling method. Type 1 is an adaptive, "
        "non-recursive, super-sampling method. Type 2 is an "
        "adaptive and recursive super-sampling method. Type 3 "
        "is a stochastic halton based super-sampling method",
        items=(
            ("0", "non-recursive AA", "Type 1 Sampling in POV"),
            ("1", "recursive AA", "Type 2 Sampling in POV"),
            ("2", "stochastic AA", "Type 3 Sampling in POV")
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
        precision=4
    )

    antialias_depth: IntProperty(
        name="Antialias Depth",
        description="Depth of pixel for sampling",
        min=1,
        max=9,
        default=3
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

    alpha_mode: EnumProperty(
        name="Alpha",
        description="Representation of alpha information in the RGBA pixels",
        items=(
            ("SKY", "Sky", "Transparent pixels are filled with sky color"),
            (
            "TRANSPARENT",
            "Transparent",
            "Transparent, World background is transparent with premultiplied alpha",
            ),
        ),
        default="SKY",
    )

    use_shadows: BoolProperty(
        name="Shadows",
        description="Calculate shadows while rendering",
        default=True,
    )

    max_trace_level: IntProperty(
        name="Max Trace Level",
        description="Number of reflections/refractions allowed on ray "
        "path",
        min=1,
        max=256,
        default=5
    )

    adc_bailout_enable: BoolProperty(
        name="Enable",
        description="",
        default=False,
    )

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
        precision=3
    )

    ambient_light_enable: BoolProperty(
        name="Enable",
        description="",
        default=False,
    )

    ambient_light: FloatVectorProperty(
        name="Ambient Light",
        description="Ambient light is used to simulate the effect of inter-diffuse reflection",
        precision=4, step=0.01, min=0, soft_max=1,
        default=(1, 1, 1), options={'ANIMATABLE'}, subtype='COLOR',
    )
    global_settings_advanced: BoolProperty(
        name="Advanced",
        description="",
        default=False,
    )

    irid_wavelength_enable: BoolProperty(
        name="Enable",
        description="",
        default=False,
    )

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
        default=(0.25,0.18,0.14),
        options={'ANIMATABLE'},
        subtype='COLOR'
    )
    # Deprecated (autodetected in pov3.8):
    # charset: EnumProperty(
        # name="Charset",
        # description="This allows you to specify the assumed character set of all text strings",
        # items=(
            # ("ascii", "ASCII", ""),
            # ("utf8", "UTF-8", ""),
            # ("sys", "SYS", "")
        # ),
        # default="utf8",
    # )

    max_intersections_enable: BoolProperty(
        name="Enable",
        description="",
        default=False,
    )

    max_intersections: IntProperty(
        name="Max Intersections",
        description="POV-Ray uses a set of internal stacks to collect ray/object intersection points",
        min=2,
        max=1024,
        default=64,
    )

    number_of_waves_enable: BoolProperty(
        name="Enable",
        description="",
        default=False,
    )

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

    noise_generator_enable: BoolProperty(
        name="Enable",
        description="",
        default=False,
    )

    noise_generator: IntProperty(
        name="Noise Generator",
        description="There are three noise generators implemented",
        min=1,
        max=3,
        default=2,
    )

    ########################### PHOTONS #######################################
    photon_enable: BoolProperty(
        name="Photons",
        description="Enable global photons",
        default=False,
    )

    photon_enable_count: BoolProperty(
        name="Spacing / Count",
        description="Enable count photons",
        default=False,
    )

    photon_count: IntProperty(
        name="Count",
        description="Photons count",
        min=1,
        max=100000000,
        default=20000
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
        description="Number of reflections/refractions allowed on ray "
        "path",
        min=1,
        max=256,
        default=5
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
        name="Gather Min", description="Minimum number of photons gathered"
        "for each point",
        min=1, max=256, default=20
    )

    photon_gather_max: IntProperty(
        name="Gather Max", description="Maximum number of photons gathered for each point",
        min=1, max=256, default=100
    )

    photon_map_file_save_load: EnumProperty(
        name="Operation",
        description="Load or Save photon map file",
        items=(
            ("NONE", "None", ""),
            ("save", "Save", ""),
            ("load", "Load", "")
        ),
        default="NONE",
    )

    photon_map_filename: StringProperty(
        name="Filename",
        description="",
        maxlen=1024
    )

    photon_map_dir: StringProperty(
        name="Directory",
        description="",
        maxlen=1024,
        subtype="DIR_PATH",
    )

    photon_map_file: StringProperty(
        name="File",
        description="",
        maxlen=1024,
        subtype="FILE_PATH"
    )

    #########RADIOSITY########
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
        min=0.0, max=1000.0, soft_min=0.0, soft_max=10.0, default=1.0
    )

    radio_count: IntProperty(
        name="Ray Count",
        description="Number of rays for each new radiosity value to be calculated "
        "(halton sequence over 1600)",
        min=1, max=10000, soft_max=1600, default=35
    )

    radio_error_bound: FloatProperty(
        name="Error Bound",
        description="One of the two main speed/quality tuning values, "
        "lower values are more accurate",
        min=0.0, max=1000.0, soft_min=0.1, soft_max=10.0, default=1.8
    )

    radio_gray_threshold: FloatProperty(
        name="Gray Threshold",
        description="One of the two main speed/quality tuning values, "
        "lower values are more accurate",
        min=0.0, max=1.0, soft_min=0, soft_max=1, default=0.0
    )

    radio_low_error_factor: FloatProperty(
        name="Low Error Factor",
        description="Just enough samples is slightly blotchy. Low error changes error "
        "tolerance for less critical last refining pass",
        min=0.000001, max=1.0, soft_min=0.000001, soft_max=1.0, default=0.5
    )

    radio_media: BoolProperty(
        name="Media",
        description="Radiosity estimation can be affected by media",
        default=True,
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
        min=0.0, max=1.0, soft_min=0.1, soft_max=0.1, default=0.015, precision=3
    )

    radio_maximum_reuse: FloatProperty(
        name="Maximum Reuse",
        description="The maximum reuse parameter works in conjunction with, and is similar to that of minimum reuse, "
        "the only difference being that it is an upper bound rather than a lower one",
        min=0.0, max=1.0,default=0.2, precision=3
    )

    radio_nearest_count: IntProperty(
        name="Nearest Count",
        description="Number of old ambient values blended together to "
        "create a new interpolated value",
        min=1, max=20, default=1
    )

    radio_normal: BoolProperty(
        name="Normals",
        description="Radiosity estimation can be affected by normals",
        default=False,
    )

    radio_recursion_limit: IntProperty(
        name="Recursion Limit",
        description="how many recursion levels are used to calculate "
        "the diffuse inter-reflection",
        min=1, max=20, default=1
    )

    radio_pretrace_start: FloatProperty(
        name="Pretrace Start",
        description="Fraction of the screen width which sets the size of the "
        "blocks in the mosaic preview first pass",
        min=0.01, max=1.00, soft_min=0.02, soft_max=1.0, default=0.08
    )

    radio_pretrace_end: FloatProperty(
        name="Pretrace End",
        description="Fraction of the screen width which sets the size of the blocks "
        "in the mosaic preview last pass",
        min=0.000925, max=1.00, soft_min=0.01, soft_max=1.00, default=0.04, precision=3
    )

###############################################################################
# Material POV properties.
###############################################################################
class MaterialTextureSlot(PropertyGroup):
    """Declare material texture slot level properties for UI and translated to POV."""

    bl_idname="pov_texture_slots",
    bl_description="Texture_slots from Blender-2.79",

    texture : StringProperty(update=active_texture_name_from_uilist)
    texture_search : StringProperty(update=active_texture_name_from_search)

    alpha_factor: FloatProperty(
        name="Alpha",
        description="Amount texture affects alpha",
        default = 0.0,
    )

    ambient_factor: FloatProperty(
        name="",
        description="Amount texture affects ambient",
        default = 0.0,
    )

    bump_method: EnumProperty(
        name="",
        description="Method to use for bump mapping",
        items=(
            ("BUMP_ORIGINAL", "Bump Original", ""),
            ("BUMP_COMPATIBLE", "Bump Compatible", ""),
            ("BUMP_DEFAULT", "Bump Default", ""),
            ("BUMP_BEST_QUALITY", "Bump Best Quality", "")
        ),
        default="BUMP_ORIGINAL",
    )

    bump_objectspace: EnumProperty(
        name="",
        description="Space to apply bump mapping in",
        items=(
            ("BUMP_VIEWSPACE", "Bump Viewspace", ""),
            ("BUMP_OBJECTSPACE", "Bump Objectspace", ""),
            ("BUMP_TEXTURESPACE", "Bump Texturespace", "")
        ),
        default="BUMP_VIEWSPACE",
    )

    density_factor: FloatProperty(
        name="",
        description="Amount texture affects density",
        default = 0.0,
    )

    diffuse_color_factor: FloatProperty(
        name="",
        description="Amount texture affects diffuse color",
        default = 0.0,
    )

    diffuse_factor: FloatProperty(
        name="",
        description="Amount texture affects diffuse reflectivity",
        default = 0.0,
    )

    displacement_factor: FloatProperty(
        name="",
        description="Amount texture displaces the surface",
        default = 0.0,
    )

    emission_color_factor: FloatProperty(
        name="",
        description="Amount texture affects emission color",
        default = 0.0,
    )

    emission_factor: FloatProperty(
        name="",
        description="Amount texture affects emission",
        default = 0.0,
    )

    emit_factor: FloatProperty(
        name="",
        description="Amount texture affects emission",
        default = 0.0,
    )

    hardness_factor: FloatProperty(
        name="",
        description="Amount texture affects hardness",
        default = 0.0,
    )

    mapping: EnumProperty(
        name="",
        description="",
        items=(("FLAT", "Flat", ""),
               ("CUBE", "Cube", ""),
               ("TUBE", "Tube", ""),
               ("SPHERE", "Sphere", "")),
        default="FLAT",
    )

    mapping_x: EnumProperty(
        name="",
        description="",
        items=(("NONE", "", ""),
               ("X", "", ""),
               ("Y", "", ""),
               ("Z", "", "")),
        default="NONE",
    )

    mapping_y: EnumProperty(
        name="",
        description="",
        items=(("NONE", "", ""),
               ("X", "", ""),
               ("Y", "", ""),
               ("Z", "", "")),
        default="NONE",
    )

    mapping_z: EnumProperty(
        name="",
        description="",
        items=(("NONE", "", ""),
               ("X", "", ""),
               ("Y", "", ""),
               ("Z", "", "")),
        default="NONE",
    )

    mirror_factor: FloatProperty(
        name="",
        description="Amount texture affects mirror color",
        default = 0.0,
    )

    normal_factor: FloatProperty(
        name="",
        description="Amount texture affects normal values",
        default = 0.0,
    )

    normal_map_space: EnumProperty(
        name="",
        description="Sets space of normal map image",
        items=(("CAMERA", "Camera", ""),
               ("WORLD", "World", ""),
               ("OBJECT", "Object", ""),
               ("TANGENT", "Tangent", "")),
        default="CAMERA",
    )

    object: StringProperty(
        name="Object",
        description="Object to use for mapping with Object texture coordinates",
        default ="",
    )

    raymir_factor: FloatProperty(
        name="",
        description="Amount texture affects ray mirror",
        default = 0.0,
    )

    reflection_color_factor: FloatProperty(
        name="",
        description="Amount texture affects color of out-scattered light",
        default = 0.0,
    )

    reflection_factor: FloatProperty(
        name="",
        description="Amount texture affects brightness of out-scattered light",
        default = 0.0,
    )

    scattering_factor: FloatProperty(
        name="",
        description="Amount texture affects scattering",
        default = 0.0,
    )

    specular_color_factor: FloatProperty(
        name="",
        description="Amount texture affects specular color",
        default = 0.0,
    )

    specular_factor: FloatProperty(
        name="",
        description="Amount texture affects specular reflectivity",
        default = 0.0,
    )

    texture_coords: EnumProperty(
        name="",
        description="",
        items=(
            ("GLOBAL", "Global", ""),
            ("OBJECT", "Object", ""),
            ("UV", "UV", ""),
            ("ORCO", "Original Coordinates", ""),
            ("STRAND", "Strand", ""),
            ("STICKY", "Sticky", ""),
            ("WINDOW", "Window", ""),
            ("NORMAL", "Normal", ""),
            ("REFLECTION", "Reflection", ""),
            ("STRESS", "Stress", ""),
            ("TANGENT", "Tangent", "")
        ),
        default="GLOBAL",
    )

    translucency_factor: FloatProperty(
        name="",
        description="Amount texture affects translucency",
        default = 0.0,
    )

    transmission_color_factor: FloatProperty(
        name="",
        description="Amount texture affects result color after light has been scattered/absorbed",
        default = 0.0,
    )

    use: BoolProperty(
        name="",
        description="Enable this material texture slot",
        default = True,
    )

    use_from_dupli: BoolProperty(
        name="",
        description="Dupli’s instanced from verts, faces or particles, inherit texture coordinate from their parent",
        default = False,
    )

    use_from_original: BoolProperty(
        name="",
        description="Dupli’s derive their object coordinates from the original objects transformation",
        default = False,
    )

    use_map_alpha: BoolProperty(
        name="",
        description="Causes the texture to affect the alpha value",
        default = False,
    )

    use_map_ambient: BoolProperty(
        name="",
        description="Causes the texture to affect the value of ambient",
        default = False,
    )

    use_map_color_diffuse: BoolProperty(
        name="",
        description="Causes the texture to affect basic color of the material",
        default = False,
    )

    use_map_color_emission: BoolProperty(
        name="",
        description="Causes the texture to affect the color of emission",
        default = False,
    )

    use_map_color_reflection: BoolProperty(
        name="",
        description="Causes the texture to affect the color of scattered light",
        default = False,
    )

    use_map_color_spec: BoolProperty(
        name="",
        description="Causes the texture to affect the specularity color",
        default = False,
    )

    use_map_color_transmission: BoolProperty(
        name="",
        description="Causes the texture to affect the result color after other light has been scattered/absorbed",
        default = False,
    )

    use_map_density: BoolProperty(
        name="",
        description="Causes the texture to affect the volume’s density",
        default = False,
    )

    use_map_diffuse: BoolProperty(
        name="",
        description="Causes the texture to affect the value of the materials diffuse reflectivity",
        default = False,
    )

    use_map_displacement: BoolProperty(
        name="",
        description="Let the texture displace the surface",
        default = False,
    )

    use_map_emission: BoolProperty(
        name="",
        description="Causes the texture to affect the volume’s emission",
        default = False,
    )

    use_map_emit: BoolProperty(
        name="",
        description="Causes the texture to affect the emit value",
        default = False,
    )

    use_map_hardness: BoolProperty(
        name="",
        description="Causes the texture to affect the hardness value",
        default = False,
    )

    use_map_mirror: BoolProperty(
        name="",
        description="Causes the texture to affect the mirror color",
        default = False,
    )

    use_map_normal: BoolProperty(
        name="",
        description="Causes the texture to affect the rendered normal",
        default = False,
    )

    use_map_raymir: BoolProperty(
        name="",
        description="Causes the texture to affect the ray-mirror value",
        default = False,
    )

    use_map_reflect: BoolProperty(
        name="",
        description="Causes the texture to affect the reflected light’s brightness",
        default = False,
    )

    use_map_scatter: BoolProperty(
        name="",
        description="Causes the texture to affect the volume’s scattering",
        default = False,
    )

    use_map_specular: BoolProperty(
        name="",
        description="Causes the texture to affect the value of specular reflectivity",
        default = False,
    )

    use_map_translucency: BoolProperty(
        name="",
        description="Causes the texture to affect the translucency value",
        default = False,
    )

    use_map_warp: BoolProperty(
        name="",
        description="Let the texture warp texture coordinates of next channels",
        default = False,
    )

    uv_layer: StringProperty(
        name="",
        description="UV layer to use for mapping with UV texture coordinates",
        default = "",
    )

    warp_factor: FloatProperty(
        name="",
        description="Amount texture affects texture coordinates of next channels",
        default = 0.0,
    )


#######################################"

    blend_factor: FloatProperty(
        name="Blend",
        description="Amount texture affects color progression of the "
        "background",
        soft_min=0.0, soft_max=1.0, default=1.0,
    )

    horizon_factor: FloatProperty(
        name="Horizon",
        description="Amount texture affects color of the horizon"
                    "",
        soft_min=0.0, soft_max=1.0, default=1.0
    )

    object: StringProperty(
        name="Object",
        description="Object to use for mapping with Object texture coordinates",
        default="",
    )

    texture_coords: EnumProperty(
        name="Coordinates",
        description="Texture coordinates used to map the texture onto the background",
        items=(
            ("VIEW", "View", "Use view vector for the texture coordinates"),
            ("GLOBAL", "Global", "Use global coordinates for the texture coordinates (interior mist)"),
            ("ANGMAP", "AngMap", "Use 360 degree angular coordinates, e.g. for spherical light probes"),
            ("SPHERE", "Sphere", "For 360 degree panorama sky, spherical mapped, only top half"),
            ("EQUIRECT", "Equirectangular", "For 360 degree panorama sky, equirectangular mapping"),
            ("TUBE", "Tube", "For 360 degree panorama sky, cylindrical mapped, only top half"),
            ("OBJECT", "Object", "Use linked object’s coordinates for texture coordinates")
        ),
        default="VIEW",
    )

    use_map_blend: BoolProperty(
        name="Blend Map",
        description="Affect the color progression of the background",
        default=True,
    )

    use_map_horizon: BoolProperty(
        name="Horizon Map",
        description="Affect the color of the horizon",
        default=False,
    )

    use_map_zenith_down: BoolProperty(
        name="", description="Affect the color of the zenith below",
        default=False,
    )

    use_map_zenith_up: BoolProperty(
        name="Zenith Up Map", description="Affect the color of the zenith above",
        default=False,
    )

    zenith_down_factor: FloatProperty(
        name="Zenith Down",
        description="Amount texture affects color of the zenith below",
        soft_min=0.0, soft_max=1.0, default=1.0
    )

    zenith_up_factor: FloatProperty(
        name="Zenith Up",
        description="Amount texture affects color of the zenith above",
        soft_min=0.0, soft_max=1.0, default=1.0
    )


# former Space properties from  removed Blender Internal added below at superclass level
# so as to be available in World, Material, Light for texture slots use

bpy.types.ID.use_limited_texture_context = BoolProperty(
    name="",
    description="Use the limited version of texture user (for ‘old shading’ mode)",
    default=True,
)
bpy.types.ID.texture_context = EnumProperty(
    name="Texture context",
    description="Type of texture data to display and edit",
    items=(
        ('MATERIAL', "", "Show material textures", "MATERIAL",0), # "Show material textures"
        ('WORLD', "", "Show world textures", "WORLD",1), # "Show world textures"
        ('LIGHT', "", "Show lamp textures", "LIGHT",2), # "Show lamp textures"
        ('PARTICLES', "", "Show particles textures", "PARTICLES",3), # "Show particles textures"
        ('LINESTYLE', "", "Show linestyle textures", "LINE_DATA",4), # "Show linestyle textures"
        ('OTHER', "", "Show other data textures", "TEXTURE_DATA",5) # "Show other data textures"
    ),
    default = 'MATERIAL',
)

bpy.types.ID.active_texture_index = IntProperty(
    name = "Index for texture_slots",
    default = 0,
)

class RenderPovSettingsMaterial(PropertyGroup):
    """Declare material level properties controllable in UI and translated to POV."""

    ######################Begin Old Blender Internal Props#########################
    # former Space properties from  removed Blender Internal
    use_limited_texture_context: BoolProperty(
        name="",
        description="Use the limited version of texture user (for ‘old shading’ mode)",
        default=True,
    )
    texture_context: EnumProperty(
        name="Texture context",
        description="Type of texture data to display and edit",
        items=(
            ('MATERIAL', "", "Show material textures", "MATERIAL",0), # "Show material textures"
            ('WORLD', "", "Show world textures", "WORLD",1), # "Show world textures"
            ('LAMP', "", "Show lamp textures", "LIGHT",2), # "Show lamp textures"
            ('PARTICLES', "", "Show particles textures", "PARTICLES",3), # "Show particles textures"
            ('LINESTYLE', "", "Show linestyle textures", "LINE_DATA",4), # "Show linestyle textures"
            ('OTHER', "", "Show other data textures", "TEXTURE_DATA",5) # "Show other data textures"
        ),
        default = 'MATERIAL',
    )

    active_texture_index: IntProperty(
        name = "Index for texture_slots",
        default = 0,
    )

    transparency_method: EnumProperty(
        name="Specular Shader Model",
        description="Method to use for rendering transparency",
        items=(
            ("MASK", "Mask", "Mask the background"),
            ("Z_TRANSPARENCY", "Z Transparency", "Use alpha buffer for transparent faces"),
            ("RAYTRACE", "Raytrace", "Use raytracing for transparent refraction rendering")
        ),
        default="MASK",
    )

    use_transparency: BoolProperty(
        name="Transparency",
        description="Render material as transparent",
        default=False,
    )

    alpha: FloatProperty(
        name="Alpha",
        description="Alpha transparency of the material",
        min=0.0, max=1.0, soft_min=0.0, soft_max=1.0, default=1.0, precision=3,
    )

    specular_alpha: FloatProperty(
        name="Specular alpha",
        description="Alpha transparency for specular areas",
        min=0.0, max=1.0, soft_min=0.0, soft_max=1.0, default=1.0, precision=3,
    )

    ambient: FloatProperty(
        name="Ambient",
        description="Amount of global ambient color the material receives",
        min=0.0, max=1.0, soft_min=0.0, soft_max=1.0, default=1.0, precision=3,
    )

    diffuse_color: FloatVectorProperty(
        name="Diffuse color",
        description=("Diffuse color of the material"),
        precision=4, step=0.01, min=0, # max=inf, soft_max=1,
        default=(0.6,0.6,0.6), options={'ANIMATABLE'}, subtype='COLOR',
    )

    darkness: FloatProperty(
        name="Darkness",
        description="Minnaert darkness",
        min=0.0, max=2.0, soft_min=0.0, soft_max=2.0, default=1.0, precision=3,
    )

    diffuse_fresnel: FloatProperty(
        name="Diffuse fresnel",
        description="Power of Fresnel",
        min=0.0, max=5.0, soft_min=0.0, soft_max=5.0, default=1.0, precision=3,
    )

    diffuse_fresnel_factor: FloatProperty(
        name="Diffuse fresnel factor",
        description="Blending factor of Fresnel",
        min=0.0, max=5.0, soft_min=0.0, soft_max=5.0, default=0.5, precision=3,
    )

    diffuse_intensity: FloatProperty(
        name="Diffuse intensity",
        description="Amount of diffuse reflection multiplying color",
        min=0.0, max=1.0, soft_min=0.0, soft_max=1.0, default=0.8, precision=3,
    )

    diffuse_ramp_blend: EnumProperty(
        name="Diffuse ramp blend",
        description="Blending method of the ramp and the diffuse color",
        items=(
            ("MIX", "Mix", ""),
            ("ADD", "Add", ""),
            ("MULTIPLY", "Multiply", ""),
            ("SUBTRACT", "Subtract", ""),
            ("SCREEN", "Screen", ""),
            ("DIVIDE", "Divide", ""),
            ("DIFFERENCE", "Difference", ""),
            ("DARKEN", "Darken", ""),
            ("LIGHTEN", "Lighten", ""),
            ("OVERLAY", "Overlay", ""),
            ("DODGE", "Dodge", ""),
            ("BURN", "Burn", ""),
            ("HUE", "Hue", ""),
            ("SATURATION", "Saturation", ""),
            ("VALUE", "Value", ""),
            ("COLOR", "Color", ""),
            ("SOFT_LIGHT", "Soft light", ""),
            ("LINEAR_LIGHT", "Linear light", "")
        ),
        default="MIX",
    )

    diffuse_ramp_factor: FloatProperty(
        name="Factor",
        description="Blending factor (also uses alpha in Colorband)",
        min=0.0, max=1.0, soft_min=0.0, soft_max=1.0, default=1.0, precision=3,
    )

    diffuse_ramp_input: EnumProperty(
        name="Input",
        description="How the ramp maps on the surface",
        items=(
            ("SHADER", "Shader", ""),
            ("ENERGY", "Energy", ""),
            ("NORMAL", "Normal", ""),
            ("RESULT", "Result", "")
        ),
            default="SHADER",
    )

    diffuse_shader: EnumProperty(
        name="Diffuse Shader Model",
        description="How the ramp maps on the surface",
        items=(
            ("LAMBERT", "Lambert", "Use a Lambertian shader"),
            ("OREN_NAYAR", "Oren-Nayar", "Use an Oren-Nayar shader"),
            ("MINNAERT", "Minnaert", "Use a Minnaert shader"),
            ("FRESNEL", "Fresnel", "Use a Fresnel shader")
        ),
        default="LAMBERT",
    )

    diffuse_toon_size: FloatProperty(
        name="Size",
        description="Size of diffuse toon area",
        min=0.0, max=3.14, soft_min=0.0, soft_max=3.14, default=0.5, precision=3,
    )

    diffuse_toon_smooth: FloatProperty(
        name="Smooth",
        description="Smoothness of diffuse toon area",
        min=0.0, max=1.0, soft_min=0.0, soft_max=1.0, default=0.1, precision=3,
    )

    emit: FloatProperty(
        name="Emit",
        description="Amount of light to emit",
        min=0.0, soft_min=0.0, # max=inf, soft_max=inf,
        default=0.0, precision=3,
        )

    mirror_color: FloatVectorProperty(
        name="Mirror color",
        description=("Mirror color of the material"),
        precision=4, step=0.01, min=0, # max=inf, soft_max=1,
        default=(0.6,0.6,0.6), options={'ANIMATABLE'}, subtype='COLOR'
    )

    roughness: FloatProperty(
        name="Roughness",
        description="Oren-Nayar Roughness",
        min=0.0, max=3.14, soft_min=0.0, soft_max=3.14,
        precision=3,
        default=0.5,
    )

    halo: BoolProperty(
        name="Halo",
        description=" Halo settings for the material",
        default=False,
    )
            # (was readonly in Blender2.79, never None)

    line_color: FloatVectorProperty(
        name="Line color",
        description=("Line color used for Freestyle line rendering"),
        precision=4, step=0.01, min=0, # max=inf, soft_max=1,
        default=(0.0,0.0,0.0), options={'ANIMATABLE'}, subtype='COLOR'
    )

    # diffuse_ramp:
    ## Color ramp used to affect diffuse shading
            ## Type:	ColorRamp, (readonly)

            # cr_node = bpy.data.materials['Material'].node_tree.nodes['ColorRamp']
            # layout.template_color_ramp(cr_node, "color_ramp", expand=True)

            # ou

            # class bpy.types.ColorRamp(bpy_struct)

    line_priority: IntProperty(
        name="Recursion Limit",
        description="The line color of a higher priority is used at material boundaries",
        min=0, max=32767, default=0,
    )

    specular_color: FloatVectorProperty(
        name="Specular color",
        description=("Specular color of the material "),
        precision=4, step=0.01, min=0, # max=inf, soft_max=1,
        default=(1.0,1.0,1.0), options={'ANIMATABLE'}, subtype='COLOR'
    )

    specular_hardness: IntProperty(
        name="Hardness",
        description="How hard (sharp) the specular reflection is",
        min=1, max=511, default=50,
    )

    specular_intensity: FloatProperty(
        name="Intensity",
        description="How intense (bright) the specular reflection is",
        min=0.0, max=1.0, soft_min=0.0, soft_max=1.0, default=0.5, precision=3
    )

    specular_ior: FloatProperty(
        name="IOR",
        description="Specular index of refraction",
        min=-10.0, max=10.0, soft_min=0.0, soft_max=10.0, default=1.0, precision=3
    )

    ior: FloatProperty(
        name="IOR",
        description="Index of refraction",
        min=-10.0, max=10.0, soft_min=0.0, soft_max=10.0, default=1.0, precision=3
    )

    specular_shader: EnumProperty(
        name="Specular Shader Model",
        description="How the ramp maps on the surface",
        items=(
            ("COOKTORR", "CookTorr", "Use a Cook-Torrance shader"),
            ("PHONG", "Phong", "Use a Phong shader"),
            ("BLINN", "Blinn", "Use a Blinn shader"),
            ("TOON", "Toon", "Use a Toon shader"),
            ("WARDISO", "WardIso", "Use a Ward anisotropic shader")
        ),
        default="COOKTORR",
    )

    specular_slope: FloatProperty(
        name="Slope",
        description="The standard deviation of surface slope",
        min=0.0, max=0.4, soft_min=0.0, soft_max=0.4, default=0.1, precision=3
    )

    specular_toon_size: FloatProperty(
        name="Size",
        description="Size of specular toon area",
        min=0.0, max=0.53, soft_min=0.0, soft_max=0.53, default=0.5, precision=3
    )

    specular_toon_smooth: FloatProperty(
        name="Smooth",
        description="Smoothness of specular toon area",
        min=0.0, max=1.0, soft_min=0.0, soft_max=1.0, default=0.1, precision=3
    )


    translucency: FloatProperty(
        name="Translucency",
        description="Amount of diffuse shading on the back side",
        min=0.0, max=1.0, soft_min=0.0, soft_max=1.0, default=0.0, precision=3
    )

    transparency_method: EnumProperty(
        name="Specular Shader Model",
        description="Method to use for rendering transparency",
        items=(
            ("MASK", "Mask", "Mask the background"),
            ("Z_TRANSPARENCY", "Z Transparency", "Use an ior of 1 for transparent faces"),
            ("RAYTRACE", "Raytrace", "Use raytracing for transparent refraction rendering")
        ),
        default="MASK",
    )

    type: EnumProperty(
        name="Type",
        description="Material type defining how the object is rendered",
        items=(
            ("SURFACE", "Surface", "Render object as a surface"),
            ("WIRE", "Wire", "Render the edges of faces as wires (not supported in raytracing)"),# TO UPDATE > USE MACRO AND CHANGE DESCRIPTION
            ("VOLUME", "Volume", "Render object as a volume"),
            ("‘HALO’", "Halo", "Render object as halo particles")
        ), # TO UPDATE > USE MACRO AND CHANGE DESCRIPTION
        default="SURFACE",
    )

    use_cast_shadows: BoolProperty(
        name="Cast",
        description="Allow this material to cast shadows",
        default=True,
    )

    use_cast_shadows_only: BoolProperty(
        name="Cast Only",
        description="Make objects with this material "
        "appear invisible (not rendered), only "
        "casting shadows",
        default=False,
    )

    use_cubic: BoolProperty(
        name="Cubic Interpolation",
        description="Use cubic interpolation for diffuse "
        "values, for smoother transitions",
        default=False,
    )

    use_diffuse_ramp: BoolProperty(
        name="Ramp",
        description="Toggle diffuse ramp operations",
        default=False,
    )

    use_light_group_exclusive: BoolProperty(
        name="Exclusive",
        description="Material uses the light group exclusively"
        "- these lamps are excluded from other "
        "scene lighting",
        default=False,
    )

    use_light_group_local: BoolProperty(
        name="Local",
        description="When linked in, material uses local light"
        " group with the same name",
        default=False,
    )

    use_mist: BoolProperty(
        name="Use Mist",
        description="Use mist with this material "
        "(in world settings)",
        default=True,
        )

    use_nodes: BoolProperty(
        name="Nodes",
        description="Use shader nodes to render the material",# Add Icon in UI or here? icon='NODES'
        default=False,
    )

    use_object_color: BoolProperty(
        name="Object Color",
        description="Modulate the result with a per-object color",
        default=False,
    )

    use_only_shadow: BoolProperty(
        name="Shadows Only",
        description="Render shadows as the material’s alpha "
        "value, making the material transparent "
        "except for shadowed areas",
        default=False,
    )

    use_shadeless: BoolProperty(
        name="Shadeless",
        description="Make this material insensitive to "
        "light or shadow",
        default=False,
    )

    use_shadows: BoolProperty(
        name="Receive",
        description="Allow this material to receive shadows",
        default=True,
    )

    use_sky: BoolProperty(
        name="Sky",
        description="Render this material with zero alpha, "
        "with sky background in place (scanline only)",
        default=False,
    )

    use_specular_ramp: BoolProperty(
        name="Ramp",
        description="Toggle specular ramp operations",
        default=False,
    )

    use_tangent_shading: BoolProperty(
        name="Tangent Shading",
        description="Use the material’s tangent vector instead"
        "of the normal for shading - for "
        "anisotropic shading effects",
        default=False,
    )

    use_transparent_shadows: BoolProperty(
        name="Receive Transparent",
        description="Allow this object to receive transparent "
        "shadows cast through other object",
        default=False,
    ) # linked to fake caustics

    use_vertex_color_light: BoolProperty(
        name="Vertex Color Light",
        description="Add vertex colors as additional lighting",
        default=False,
    )

    use_vertex_color_paint: BoolProperty(
        name="Vertex Color Paint", description="Replace object base color with vertex "
        "colors (multiply with ‘texture face’ "
        "face assigned textures)",
        default=False,
    )


    specular_ramp_blend: EnumProperty(
        name="Specular ramp blend",
        description="Blending method of the ramp and the specular color",
        items=(
            ("MIX", "Mix", ""),
            ("ADD", "Add", ""),
            ("MULTIPLY", "Multiply", ""),
            ("SUBTRACT", "Subtract", ""),
            ("SCREEN", "Screen", ""),
            ("DIVIDE", "Divide", ""),
            ("DIFFERENCE", "Difference", ""),
            ("DARKEN", "Darken", ""),
            ("LIGHTEN", "Lighten", ""),
            ("OVERLAY", "Overlay", ""),
            ("DODGE", "Dodge", ""),
            ("BURN", "Burn", ""),
            ("HUE", "Hue", ""),
            ("SATURATION", "Saturation", ""),
            ("VALUE", "Value", ""),
            ("COLOR", "Color", ""),
            ("SOFT_LIGHT", "Soft light", ""),
            ("LINEAR_LIGHT", "Linear light", "")
        ),
        default="MIX",
    )

    specular_ramp_factor: FloatProperty(
        name="Factor",
        description="Blending factor (also uses alpha in Colorband)",
        min=0.0, max=1.0, soft_min=0.0, soft_max=1.0, default=1.0, precision=3,
    )

    specular_ramp_input: EnumProperty(
        name="Input",
        description="How the ramp maps on the surface",
        items=(
            ("SHADER", "Shader", ""),
            ("ENERGY", "Energy", ""),
            ("NORMAL", "Normal", ""),
            ("RESULT", "Result", "")
        ),
        default="SHADER",
    )


    irid_enable: BoolProperty(
        name="Iridescence coating",
        description="Newton's thin film interference (like an oil slick on a puddle of "
        "water or the rainbow hues of a soap bubble.)",
        default=False,
    )

    mirror_use_IOR: BoolProperty(
        name="Correct Reflection",
        description="Use same IOR as raytrace transparency to calculate mirror reflections. "
        "More physically correct",
        default=False,
    )

    mirror_metallic: BoolProperty(
        name="Metallic Reflection",
        description="mirror reflections get colored as diffuse (for metallic materials)",
        default=False,
    )

    conserve_energy: BoolProperty(
        name="Conserve Energy",
        description="Light transmitted is more correctly reduced by mirror reflections, "
        "also the sum of diffuse and translucency gets reduced below one ",
        default=True,
    )

    irid_amount: FloatProperty(
        name="amount",
        description="Contribution of the iridescence effect to the overall surface color. "
        "As a rule of thumb keep to around 0.25 (25% contribution) or less, "
        "but experiment. If the surface is coming out too white, try lowering "
        "the diffuse and possibly the ambient values of the surface",
        min=0.0, max=1.0, soft_min=0.01, soft_max=1.0, default=0.25,
    )

    irid_thickness: FloatProperty(
        name="thickness",
        description="A very thin film will have a high frequency of color changes while a "
        "thick film will have large areas of color",
        min=0.0, max=1000.0, soft_min=0.1, soft_max=10.0, default=1,
    )

    irid_turbulence: FloatProperty(
        name="turbulence",
        description="This parameter varies the thickness",
        min=0.0, max=10.0, soft_min=0.000, soft_max=1.0, default=0
    )

    interior_fade_color: FloatVectorProperty(
        name="Interior Fade Color",
        description="Color of filtered attenuation for transparent "
        "materials",
        precision=4, step=0.01, min=0.0, soft_max=1.0,
        default=(0, 0, 0), options={'ANIMATABLE'}, subtype='COLOR'
    )

    caustics_enable: BoolProperty(
        name="Caustics",
        description="use only fake refractive caustics (default) or photon based "
                    "reflective/refractive caustics",
        default=True,
    )

    fake_caustics: BoolProperty(
        name="Fake Caustics",
        description="use only (Fast) fake refractive caustics",
        default=True,
    )

    fake_caustics_power: FloatProperty(
        name="Fake caustics power",
        description="Values typically range from 0.0 to 1.0 or higher. Zero is no caustics. "
        "Low, non-zero values give broad hot-spots while higher values give "
        "tighter, smaller simulated focal points",
        min=0.00, max=10.0, soft_min=0.00, soft_max=5.0, default=0.15
    )

    refraction_caustics: BoolProperty(
        name="Refractive Caustics",
        description="hotspots of light focused when going through the material",
        default=True,
    )

    photons_dispersion: FloatProperty(
        name="Chromatic Dispersion",
        description="Light passing through will be separated according to wavelength. "
        "This ratio of refractive indices for violet to red controls how much "
        "the colors are spread out 1 = no dispersion, good values are 1.01 to 1.1",
        min=1.0000, max=10.000, soft_min=1.0000, soft_max=1.1000, precision=4,
        default=1.0000,
    )

    photons_dispersion_samples: IntProperty(
        name="Dispersion Samples",
        description="Number of color-steps for dispersion",
        min=2, max=128, default=7,
    )

    photons_reflection: BoolProperty(
        name="Reflective Photon Caustics",
        description="Use this to make your Sauron's ring ;-P",
        default=False,
    )

    refraction_type: EnumProperty(
        items=[
               ("1", "Z Transparency Fake Caustics", "use fake caustics"),
               ("2", "Raytrace Photons Caustics", "use photons for refractive caustics")],
        name="Refraction Type:",
        description="use fake caustics (fast) or true photons for refractive Caustics",
        default="1",
    )

    ##################################CustomPOV Code############################
    replacement_text: StringProperty(
        name="Declared name:",
        description="Type the declared name in custom POV code or an external "
        ".inc it points at. texture {} expected",
        default="",
    )


            # NODES

    def use_material_nodes_callback(self, context):
        if hasattr(context.space_data, "tree_type"):
            context.space_data.tree_type = 'ObjectNodeTree'
        mat=context.object.active_material
        if mat.pov.material_use_nodes:
            mat.use_nodes=True
            tree = mat.node_tree
            tree.name=mat.name
            links = tree.links
            default = True
            if len(tree.nodes) == 2:
                o = 0
                m = 0
                for node in tree.nodes:
                    if node.type in {"OUTPUT","MATERIAL"}:
                        tree.nodes.remove(node)
                        default = True
                for node in tree.nodes:
                    if node.bl_idname == 'PovrayOutputNode':
                        o+=1
                    if node.bl_idname == 'PovrayTextureNode':
                        m+=1
                if o == 1 and m == 1:
                    default = False
            elif len(tree.nodes) == 0:
                default = True
            else:
                default = False
            if default:
                output = tree.nodes.new('PovrayOutputNode')
                output.location = 200,200
                tmap = tree.nodes.new('PovrayTextureNode')
                tmap.location = 0,200
                links.new(tmap.outputs[0],output.inputs[0])
                tmap.select = True
                tree.nodes.active = tmap
        else:
            mat.use_nodes=False


    def use_texture_nodes_callback(self, context):
        tex=context.object.active_material.active_texture
        if tex.pov.texture_use_nodes:
            tex.use_nodes=True
            if len(tex.node_tree.nodes)==2:
                for node in tex.node_tree.nodes:
                    if node.type in {"OUTPUT","CHECKER"}:
                        tex.node_tree.nodes.remove(node)
        else:
            tex.use_nodes=False

    def node_active_callback(self, context):
        items = []
        mat=context.material
        mat.node_tree.nodes
        for node in mat.node_tree.nodes:
            node.select=False
        for node in mat.node_tree.nodes:
            if node.name==mat.pov.material_active_node:
                node.select=True
                mat.node_tree.nodes.active=node

                return node

    def node_enum_callback(self, context):
        items = []
        mat=context.material
        nodes=mat.node_tree.nodes
        for node in nodes:
            items.append(("%s"%node.name,"%s"%node.name,""))
        return items

    def pigment_normal_callback(self, context):
        render = context.scene.pov.render
        items = [("pigment", "Pigment", ""),("normal", "Normal", "")]
        if render == 'hgpovray':
            items = [("pigment", "Pigment", ""),("normal", "Normal", ""),("modulation", "Modulation", "")]
        return items

    def glow_callback(self, context):
        scene = context.scene
        ob = context.object
        ob.pov.mesh_write_as_old = ob.pov.mesh_write_as
        if scene.pov.render == 'uberpov' and ob.pov.glow:
            ob.pov.mesh_write_as = 'NONE'
        else:
            ob.pov.mesh_write_as = ob.pov.mesh_write_as_old

    material_use_nodes: BoolProperty(
        name="Use nodes",
        description="",
        update=use_material_nodes_callback,
        default=False,
    )

    material_active_node: EnumProperty(
        name="Active node",
        description="",
        items=node_enum_callback,
        update=node_active_callback
    )

    preview_settings: BoolProperty(
        name="Preview Settings",
        description="",
        default=False,
    )

    object_preview_transform: BoolProperty(
        name="Transform object",
        description="",
        default=False,
    )

    object_preview_scale: FloatProperty(
        name="XYZ",
        min=0.5,
        max=2.0,
        default=1.0,
    )

    object_preview_rotate: FloatVectorProperty(
        name="Rotate",
        description="",
        min=-180.0,
        max=180.0,
        default=(0.0,0.0,0.0),
        subtype='XYZ',
    )

    object_preview_bgcontrast: FloatProperty(
        name="Contrast",
        min=0.0,
        max=1.0,
        default=0.5,
    )


class MaterialRaytraceTransparency(PropertyGroup):
    """Declare transparency panel properties controllable in UI and translated to POV."""

    depth: IntProperty(
        name="Depth",
        description="Maximum allowed number of light inter-refractions",
        min=0, max=32767, default=2
    )

    depth_max: FloatProperty(
        name="Depth",
        description="Maximum depth for light to travel through the "
        "transparent material before becoming fully filtered (0.0 is disabled)",
        min=0, max=100, default=0.0,
    )

    falloff: FloatProperty(
        name="Falloff",
        description="Falloff power for transmissivity filter effect (1.0 is linear)",
        min=0.1, max=10.0, default=1.0, precision=3
    )

    filter: FloatProperty(
        name="Filter",
        description="Amount to blend in the material’s diffuse color in raytraced "
        "transparency (simulating absorption)",
        min=0.0, max=1.0, default=0.0, precision=3
    )

    fresnel: FloatProperty(
        name="Fresnel",
        description="Power of Fresnel for transparency (Ray or ZTransp)",
        min=0.0, max=5.0, soft_min=0.0, soft_max=5.0, default=0.0, precision=3
    )

    fresnel_factor: FloatProperty(
        name="Blend",
        description="Blending factor for Fresnel",
        min=0.0, max=5.0, soft_min=0.0, soft_max=5.0, default=1.250, precision=3
    )

    gloss_factor: FloatProperty(
        name="Amount",
        description="The clarity of the refraction. "
        "(values < 1.0 give diffuse, blurry refractions)",
        min=0.0, max=1.0, soft_min=0.0, soft_max=1.0, default=1.0, precision=3
    )

    gloss_samples: IntProperty(
        name="Samples",
        description="Number of cone samples averaged for blurry refractions",
        min=0, max=1024, default=18
    )

    gloss_threshold: FloatProperty(
        name="Threshold",
        description="Threshold for adaptive sampling (if a sample "
        "contributes less than this amount [as a percentage], "
        "sampling is stopped)",
        min=0.0, max=1.0, soft_min=0.0, soft_max=1.0, default=0.005, precision=3
    )

    ior: FloatProperty(
        name="IOR",
        description="Sets angular index of refraction for raytraced refraction",
        min=-0.0, max=10.0, soft_min=0.25, soft_max=4.0, default=1.3
    )

class MaterialRaytraceMirror(PropertyGroup):
    """Declare reflection panel properties controllable in UI and translated to POV."""

    bl_description = "Raytraced reflection settings for the Material",

    use: BoolProperty(
        name="Mirror",
        description="Enable raytraced reflections",
        default=False,
    )


    depth: IntProperty(
        name="Depth",
        description="Maximum allowed number of light inter-reflections",
        min=0, max=32767, default=2
    )

    distance: FloatProperty(
        name="Max Dist",
        description="Maximum distance of reflected rays "
        "(reflections further than this range "
        "fade to sky color or material color)",
        min=0.0, max=100000.0, soft_min=0.0, soft_max=10000.0, default=0.0, precision=3
    )

    fade_to: EnumProperty(
        items=[
               ("FADE_TO_SKY", "Fade to sky", ""),
               ("FADE_TO_MATERIAL", "Fade to material color", "")],
        name="Fade-out Color",
        description="The color that rays with no intersection within the "
        "Max Distance take (material color can be best for "
        "indoor scenes, sky color for outdoor)",
        default="FADE_TO_SKY",
    )

    fresnel: FloatProperty(
        name="Fresnel",
        description="Power of Fresnel for mirror reflection",
        min=0.0, max=5.0, soft_min=0.0, soft_max=5.0, default=0.0, precision=3,
    )

    fresnel_factor: FloatProperty(
        name="Blend",
        description="Blending factor for Fresnel",
        min=0.0, max=5.0, soft_min=0.0, soft_max=5.0, default=1.250, precision=3
    )

    gloss_anisotropic: FloatProperty(
        name="Anisotropic",
        description="The shape of the reflection, from 0.0 (circular) "
        "to 1.0 (fully stretched along the tangent",
        min=0.0, max=1.0, soft_min=0.0, soft_max=1.0, default=1.0, precision=3
    )

    gloss_factor: FloatProperty(
        name="Amount",
        description="The shininess of the reflection  "
        "(values < 1.0 give diffuse, blurry reflections)",
        min=0.0, max=1.0, soft_min=0.0, soft_max=1.0, default=1.0, precision=3
    )

    gloss_samples: IntProperty(
        name="Samples",
        description="Number of cone samples averaged for blurry reflections",
        min=0, max=1024, default=18,
    )

    gloss_threshold: FloatProperty(
        name="Threshold",
        description="Threshold for adaptive sampling (if a sample "
        "contributes less than this amount [as a percentage], "
        "sampling is stopped)",
        min=0.0, max=1.0, soft_min=0.0, soft_max=1.0, default=0.005, precision=3
    )

    mirror_color: FloatVectorProperty(
        name="Mirror color",
        description=("Mirror color of the material"),
        precision=4, step=0.01,
        default=(1.0,1.0,1.0), options={'ANIMATABLE'}, subtype='COLOR'
    )

    reflect_factor: FloatProperty(
        name="Reflectivity",
        description="Amount of mirror reflection for raytrace",
        min=0.0, max=1.0, soft_min=0.0, soft_max=1.0, default=1.0, precision=3
    )


class MaterialSubsurfaceScattering(PropertyGroup):
    r"""Declare SSS/SSTL properties controllable in UI and translated to POV."""

    bl_description = "Subsurface scattering settings for the material",

    use: BoolProperty(
        name="Subsurface Scattering",
        description="Enable diffuse subsurface scatting "
        "effects in a material",
        default=False,
    )

    back: FloatProperty(
        name="Back",
        description="Back scattering weight",
        min=0.0, max=10.0, soft_min=0.0, soft_max=10.0, default=1.0, precision=3
    )

    color: FloatVectorProperty(
        name="Scattering color",
        description=("Scattering color"),
        precision=4, step=0.01,
        default=(0.604,0.604,0.604), options={'ANIMATABLE'}, subtype='COLOR'
    )

    color_factor: FloatProperty(
        name="Color",
        description="Blend factor for SSS colors",
        min=0.0, max=1.0, soft_min=0.0, soft_max=1.0, default=1.0, precision=3
    )

    error_threshold: FloatProperty(
        name="Error",
        description="Error tolerance (low values are slower and higher quality)",
        default=0.050, precision=3
    )

    front: FloatProperty(
        name="Front",
        description="Front scattering weight",
        min=0.0, max=2.0, soft_min=0.0, soft_max=2.0, default=1.0, precision=3
    )

    ior: FloatProperty(
        name="IOR",
        description="Index of refraction (higher values are denser)",
        min=-0.0, max=10.0, soft_min=0.1, soft_max=2.0, default=1.3
    )

    radius: FloatVectorProperty(
        name="RGB Radius",
        description=("Mean red/green/blue scattering path length"),
        precision=4, step=0.01, min=0.001,
        default=(1.0,1.0,1.0), options={'ANIMATABLE'}
    )

    scale: FloatProperty(
        name="Scale",
        description="Object scale factor",
        default=0.100, precision=3
    )

    texture_factor: FloatProperty(
        name="Texture",
        description="Texture scattering blend factor",
        min=0.0, max=1.0, soft_min=0.0, soft_max=1.0, default=0.0, precision=3
    )


class MaterialStrandSettings(PropertyGroup):
    """Declare strand properties controllable in UI and translated to POV."""

    bl_description = "Strand settings for the material",

    blend_distance: FloatProperty(
        name="Distance",
        description="Worldspace distance over which to blend in the surface normal",
        min=0.0, max=10.0, soft_min=0.0, soft_max=10.0, default=0.0, precision=3
    )

    root_size: FloatProperty(
        name="Root",
        description="Start size of strands in pixels or Blender units",
        min=0.25, default=1.0, precision=5
    )

    shape: FloatProperty(
        name="Shape",
        description="Positive values make strands rounder, negative ones make strands spiky",
        min=-0.9, max=0.9, default=0.0, precision=3
    )

    size_min: FloatProperty(
        name="Minimum",
        description="Minimum size of strands in pixels",
        min=0.001, max=10.0, default=1.0, precision=3
    )

    tip_size: FloatProperty(
        name="Tip",
        description="End size of strands in pixels or Blender units",
        min=0.0, default=1.0, precision=5
    )

    use_blender_units: BoolProperty(
        name="Blender Units",
        description="Use Blender units for widths instead of pixels",
        default=False,
    )

    use_surface_diffuse: BoolProperty(
        name="Surface diffuse",
        description="Make diffuse shading more similar to shading the surface",
        default=False,
    )

    use_tangent_shading: BoolProperty(
        name="Tangent Shading",
        description="Use direction of strands as normal for tangent-shading",
        default=True,
    )

    uv_layer: StringProperty(
        name="UV Layer",
        # icon="GROUP_UVS",
        description="Name of UV map to override",
        default="",
    )

    width_fade: FloatProperty(
        name="Width Fade",
        description="Transparency along the width of the strand",
        min=0.0, max=2.0, default=0.0, precision=3
    )

            # halo

                # Halo settings for the material
                # Type:	MaterialHalo, (readonly, never None)

            # ambient

                # Amount of global ambient color the material receives
                # Type:	float in [0, 1], default 0.0

            # darkness

                # Minnaert darkness
                # Type:	float in [0, 2], default 0.0

            # diffuse_color

                # Diffuse color of the material
                # Type:	float array of 3 items in [0, inf], default (0.0, 0.0, 0.0)

            # diffuse_fresnel

                # Power of Fresnel
                # Type:	float in [0, 5], default 0.0

            # diffuse_fresnel_factor

                # Blending factor of Fresnel
                # Type:	float in [0, 5], default 0.0

            # diffuse_intensity

                # Amount of diffuse reflection
                # Type:	float in [0, 1], default 0.0

            # diffuse_ramp

                # Color ramp used to affect diffuse shading
                # Type:	ColorRamp, (readonly)

            # diffuse_ramp_blend

                # Blending method of the ramp and the diffuse color
                # Type:	enum in [‘MIX’, ‘ADD’, ‘MULTIPLY’, ‘SUBTRACT’, ‘SCREEN’, ‘DIVIDE’, ‘DIFFERENCE’, ‘DARKEN’, ‘LIGHTEN’, ‘OVERLAY’, ‘DODGE’, ‘BURN’, ‘HUE’, ‘SATURATION’, ‘VALUE’, ‘COLOR’, ‘SOFT_LIGHT’, ‘LINEAR_LIGHT’], default ‘MIX’

            # diffuse_ramp_factor

                # Blending factor (also uses alpha in Colorband)
                # Type:	float in [0, 1], default 0.0

            # diffuse_ramp_input

                # How the ramp maps on the surface
                # Type:	enum in [‘SHADER’, ‘ENERGY’, ‘NORMAL’, ‘RESULT’], default ‘SHADER’

            # diffuse_shader

                    # LAMBERT Lambert, Use a Lambertian shader.
                    # OREN_NAYAR Oren-Nayar, Use an Oren-Nayar shader.
                    # TOON Toon, Use a toon shader.
                    # MINNAERT Minnaert, Use a Minnaert shader.
                    # FRESNEL Fresnel, Use a Fresnel shader.

                # Type:	enum in [‘LAMBERT’, ‘OREN_NAYAR’, ‘TOON’, ‘MINNAERT’, ‘FRESNEL’], default ‘LAMBERT’

            # diffuse_toon_size

                # Size of diffuse toon area
                # Type:	float in [0, 3.14], default 0.0

            # diffuse_toon_smooth

                # Smoothness of diffuse toon area
                # Type:	float in [0, 1], default 0.0

            # emit

                # Amount of light to emit
                # Type:	float in [0, inf], default 0.0

            # game_settings

                # Game material settings
                # Type:	MaterialGameSettings, (readonly, never None)

            # halo

                # Halo settings for the material
                # Type:	MaterialHalo, (readonly, never None)

            # invert_z

                # Render material’s faces with an inverted Z buffer (scanline only)
                # Type:	boolean, default False

            # light_group

                # Limit lighting to lamps in this Group
                # Type:	Group

            # line_color

                # Line color used for Freestyle line rendering
                # Type:	float array of 4 items in [0, inf], default (0.0, 0.0, 0.0, 0.0)

            # line_priority

                # The line color of a higher priority is used at material boundaries
                # Type:	int in [0, 32767], default 0

            # mirror_color

                # Mirror color of the material
                # Type:	float array of 3 items in [0, inf], default (0.0, 0.0, 0.0)

            # node_tree

                # Node tree for node based materials
                # Type:	NodeTree, (readonly)

            # offset_z

                # Give faces an artificial offset in the Z buffer for Z transparency
                # Type:	float in [-inf, inf], default 0.0

            # paint_active_slot

                # Index of active texture paint slot
                # Type:	int in [0, 32767], default 0

            # paint_clone_slot

                # Index of clone texture paint slot
                # Type:	int in [0, 32767], default 0

            # pass_index

                # Index number for the “Material Index” render pass
                # Type:	int in [0, 32767], default 0

            # physics

                # Game physics settings
                # Type:	MaterialPhysics, (readonly, never None)

            # preview_render_type

                # Type of preview render

                    # FLAT Flat, Flat XY plane.
                    # SPHERE Sphere, Sphere.
                    # CUBE Cube, Cube.
                    # MONKEY Monkey, Monkey.
                    # HAIR Hair, Hair strands.
                    # SPHERE_A World Sphere, Large sphere with sky.

                # Type:	enum in [‘FLAT’, ‘SPHERE’, ‘CUBE’, ‘MONKEY’, ‘HAIR’, ‘SPHERE_A’], default ‘FLAT’

            # raytrace_mirror

                # Raytraced reflection settings for the material
                # Type:	MaterialRaytraceMirror, (readonly, never None)

            # raytrace_transparency

                # Raytraced transparency settings for the material
                # Type:	MaterialRaytraceTransparency, (readonly, never None)

            # roughness

                # Oren-Nayar Roughness
                # Type:	float in [0, 3.14], default 0.0

            # shadow_buffer_bias

                # Factor to multiply shadow buffer bias with (0 is ignore)
                # Type:	float in [0, 10], default 0.0

            # shadow_cast_alpha

                # Shadow casting alpha, in use for Irregular and Deep shadow buffer
                # Type:	float in [0.001, 1], default 0.0

            # shadow_only_type

                # How to draw shadows

                    # SHADOW_ONLY_OLD Shadow and Distance, Old shadow only method.
                    # SHADOW_ONLY Shadow Only, Improved shadow only method.
                    # SHADOW_ONLY_SHADED Shadow and Shading, Improved shadow only method which also renders lightless areas as shadows.

                # Type:	enum in [‘SHADOW_ONLY_OLD’, ‘SHADOW_ONLY’, ‘SHADOW_ONLY_SHADED’], default ‘SHADOW_ONLY_OLD’

            # shadow_ray_bias

                # Shadow raytracing bias to prevent terminator problems on shadow boundary
                # Type:	float in [0, 0.25], default 0.0


            # specular_color

                # Specular color of the material
                # Type:	float array of 3 items in [0, inf], default (0.0, 0.0, 0.0)

            # specular_hardness

                # How hard (sharp) the specular reflection is
                # Type:	int in [1, 511], default 0

            # specular_intensity

                # How intense (bright) the specular reflection is
                # Type:	float in [0, 1], default 0.0

            # specular_ior

                # Specular index of refraction
                # Type:	float in [1, 10], default 0.0

            # specular_ramp

                # Color ramp used to affect specular shading
                # Type:	ColorRamp, (readonly)

            # specular_ramp_blend

                # Blending method of the ramp and the specular color
                # Type:	enum in [‘MIX’, ‘ADD’, ‘MULTIPLY’, ‘SUBTRACT’, ‘SCREEN’, ‘DIVIDE’, ‘DIFFERENCE’, ‘DARKEN’, ‘LIGHTEN’, ‘OVERLAY’, ‘DODGE’, ‘BURN’, ‘HUE’, ‘SATURATION’, ‘VALUE’, ‘COLOR’, ‘SOFT_LIGHT’, ‘LINEAR_LIGHT’], default ‘MIX’

            # specular_ramp_factor

                # Blending factor (also uses alpha in Colorband)
                # Type:	float in [0, 1], default 0.0

            # specular_ramp_input

                # How the ramp maps on the surface
                # Type:	enum in [‘SHADER’, ‘ENERGY’, ‘NORMAL’, ‘RESULT’], default ‘SHADER’
            # specular_shader

                    # COOKTORR CookTorr, Use a Cook-Torrance shader.
                    # PHONG Phong, Use a Phong shader.
                    # BLINN Blinn, Use a Blinn shader.
                    # TOON Toon, Use a toon shader.
                    # WARDISO WardIso, Use a Ward anisotropic shader.

                # Type:	enum in [‘COOKTORR’, ‘PHONG’, ‘BLINN’, ‘TOON’, ‘WARDISO’], default ‘COOKTORR’

            # specular_slope

                # The standard deviation of surface slope
                # Type:	float in [0, 0.4], default 0.0

            # specular_toon_size

                # Size of specular toon area
                # Type:	float in [0, 1.53], default 0.0

            # specular_toon_smooth

                # Smoothness of specular toon area
                # Type:	float in [0, 1], default 0.0

            # strand

                # Strand settings for the material
                # Type:	MaterialStrand, (readonly, never None)

            # subsurface_scattering

                # Subsurface scattering settings for the material
                # Type:	MaterialSubsurfaceScattering, (readonly, never None)

            # texture_paint_images

                # Texture images used for texture painting
                # Type:	bpy_prop_collection of Image, (readonly)

            # texture_paint_slots

                # Texture slots defining the mapping and influence of textures
                # Type:	bpy_prop_collection of TexPaintSlot, (readonly)

            # texture_slots

                # Texture slots defining the mapping and influence of textures
                # Type:	MaterialTextureSlots bpy_prop_collection of MaterialTextureSlot, (readonly)

            # translucency

                # Amount of diffuse shading on the back side
                # Type:	float in [0, 1], default 0.0

            # transparency_method

                # Method to use for rendering transparency

                    # MASK Mask, Mask the background.
                    # Z_TRANSPARENCY Z Transparency, Use alpha buffer for transparent faces.
                    # RAYTRACE Raytrace, Use raytracing for transparent refraction rendering.

                # Type:	enum in [‘MASK’, ‘Z_TRANSPARENCY’, ‘RAYTRACE’], default ‘MASK’

            # type

                # Material type defining how the object is rendered

                    # SURFACE Surface, Render object as a surface.
                    # WIRE Wire, Render the edges of faces as wires (not supported in raytracing).
                    # VOLUME Volume, Render object as a volume.
                    # HALO Halo, Render object as halo particles.

                # Type:	enum in [‘SURFACE’, ‘WIRE’, ‘VOLUME’, ‘HALO’], default ‘SURFACE’

            # use_cast_approximate

                # Allow this material to cast shadows when using approximate ambient occlusion
                # Type:	boolean, default False

            # use_cast_buffer_shadows

                # Allow this material to cast shadows from shadow buffer lamps
                # Type:	boolean, default False

            # use_cast_shadows

                # Allow this material to cast shadows
                # Type:	boolean, default False

            # use_cast_shadows_only

                # Make objects with this material appear invisible (not rendered), only casting shadows
                # Type:	boolean, default False

            # use_cubic

                # Use cubic interpolation for diffuse values, for smoother transitions
                # Type:	boolean, default False

            # use_diffuse_ramp

                # Toggle diffuse ramp operations
                # Type:	boolean, default False

            # use_face_texture

                # Replace the object’s base color with color from UV map image textures
                # Type:	boolean, default False

            # use_face_texture_alpha

                # Replace the object’s base alpha value with alpha from UV map image textures
                # Type:	boolean, default False

            # use_full_oversampling

                # Force this material to render full shading/textures for all anti-aliasing samples
                # Type:	boolean, default False

            # use_light_group_exclusive

                # Material uses the light group exclusively - these lamps are excluded from other scene lighting
                # Type:	boolean, default False

            # use_light_group_local

                # When linked in, material uses local light group with the same name
                # Type:	boolean, default False

            # use_mist

                # Use mist with this material (in world settings)
                # Type:	boolean, default False

            # use_nodes

                # Use shader nodes to render the material
                # Type:	boolean, default False

            # use_object_color

                # Modulate the result with a per-object color
                # Type:	boolean, default False

            # use_only_shadow

                # Render shadows as the material’s alpha value, making the material transparent except for shadowed areas
                # Type:	boolean, default False

            # use_ray_shadow_bias

                # Prevent raytraced shadow errors on surfaces with smooth shaded normals (terminator problem)
                # Type:	boolean, default False

            # use_raytrace

                # Include this material and geometry that uses it in raytracing calculations
                # Type:	boolean, default False

            # use_shadeless

                # Make this material insensitive to light or shadow
                # Type:	boolean, default False

            # use_shadows

                # Allow this material to receive shadows
                # Type:	boolean, default False

            # use_sky

                # Render this material with zero alpha, with sky background in place (scanline only)
                # Type:	boolean, default False

            # use_specular_ramp

                # Toggle specular ramp operations
                # Type:	boolean, default False

            # use_tangent_shading

                # Use the material’s tangent vector instead of the normal for shading - for anisotropic shading effects
                # Type:	boolean, default False

            # use_textures

                # Enable/Disable each texture
                # Type:	boolean array of 18 items, default (False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False)

            # use_transparency

                # Render material as transparent
                # Type:	boolean, default False

            # use_transparent_shadows

                # Allow this object to receive transparent shadows cast through other objects
                # Type:	boolean, default False

            # use_uv_project

                # Use to ensure UV interpolation is correct for camera projections (use with UV project modifier)
                # Type:	boolean, default False

            # use_vertex_color_light

                # Add vertex colors as additional lighting
                # Type:	boolean, default False

            # use_vertex_color_paint

                # Replace object base color with vertex colors (multiply with ‘texture face’ face assigned textures)
                # Type:	boolean, default False

            # volume

                # Volume settings for the material
                # Type:	MaterialVolume, (readonly, never None)
    '''
    (mat.type in {'SURFACE', 'WIRE', 'VOLUME'})
     "use_transparency")



    mat.use_transparency and mat.transparency_method == 'Z_TRANSPARENCY'




            col.prop(mat, "use_raytrace")
            col.prop(mat, "use_full_oversampling")

            sub.prop(mat, "use_sky")


            col.prop(mat, "use_cast_shadows", text="Cast")
            col.prop(mat, "use_cast_shadows_only", text="Cast Only")
            col.prop(mat, "use_cast_buffer_shadows")

            sub.active = mat.use_cast_buffer_shadows
            sub.prop(mat, "shadow_cast_alpha", text="Casting Alpha")
            col.prop(mat, "use_cast_approximate")



            col.prop(mat, "diffuse_color", text="")

            sub.active = (not mat.use_shadeless)

            sub.prop(mat, "diffuse_intensity", text="Intensity")


            col.prop(mat, "diffuse_shader", text="")
            col.prop(mat, "use_diffuse_ramp", text="Ramp")


            if mat.diffuse_shader == 'OREN_NAYAR':
                col.prop(mat, "roughness")
            elif mat.diffuse_shader == 'MINNAERT':
                col.prop(mat, "darkness")
            elif mat.diffuse_shader == 'TOON':

                row.prop(mat, "diffuse_toon_size", text="Size")
                row.prop(mat, "diffuse_toon_smooth", text="Smooth")
            elif mat.diffuse_shader == 'FRESNEL':

                row.prop(mat, "diffuse_fresnel", text="Fresnel")
                row.prop(mat, "diffuse_fresnel_factor", text="Factor")

            if mat.use_diffuse_ramp:

                col.template_color_ramp(mat, "diffuse_ramp", expand=True)



                row.prop(mat, "diffuse_ramp_input", text="Input")
                row.prop(mat, "diffuse_ramp_blend", text="Blend")

                col.prop(mat, "diffuse_ramp_factor", text="Factor")




            col.prop(mat, "specular_color", text="")
            col.prop(mat, "specular_intensity", text="Intensity")

            col.prop(mat, "specular_shader", text="")
            col.prop(mat, "use_specular_ramp", text="Ramp")

            if mat.specular_shader in {'COOKTORR', 'PHONG'}:
                col.prop(mat, "specular_hardness", text="Hardness")
            elif mat.specular_shader == 'BLINN':

                row.prop(mat, "specular_hardness", text="Hardness")
                row.prop(mat, "specular_ior", text="IOR")
            elif mat.specular_shader == 'WARDISO':
                col.prop(mat, "specular_slope", text="Slope")
            elif mat.specular_shader == 'TOON':

                row.prop(mat, "specular_toon_size", text="Size")
                row.prop(mat, "specular_toon_smooth", text="Smooth")

            if mat.use_specular_ramp:
                layout.separator()
                layout.template_color_ramp(mat, "specular_ramp", expand=True)
                layout.separator()

                row = layout.row()
                row.prop(mat, "specular_ramp_input", text="Input")
                row.prop(mat, "specular_ramp_blend", text="Blend")

                layout.prop(mat, "specular_ramp_factor", text="Factor")


    class MATERIAL_PT_shading(MaterialButtonsPanel, Panel):
        bl_label = "Shading"
        COMPAT_ENGINES = {'BLENDER_RENDER', 'BLENDER_GAME'}

        @classmethod
        def poll(cls, context):
            mat = context.material
            engine = context.scene.render.engine
            return check_material(mat) and (mat.type in {'SURFACE', 'WIRE'}) and (engine in cls.COMPAT_ENGINES)

        def draw(self, context):
            layout = self.layout

            mat = active_node_mat(context.material)

            if mat.type in {'SURFACE', 'WIRE'}:
                split = layout.split()

                col = split.column()
                sub = col.column()
                sub.active = not mat.use_shadeless
                sub.prop(mat, "emit")
                sub.prop(mat, "ambient")
                sub = col.column()
                sub.prop(mat, "translucency")

                col = split.column()
                col.prop(mat, "use_shadeless")
                sub = col.column()
                sub.active = not mat.use_shadeless
                sub.prop(mat, "use_tangent_shading")
                sub.prop(mat, "use_cubic")


    class MATERIAL_PT_transp(MaterialButtonsPanel, Panel):
        bl_label = "Transparency"
        COMPAT_ENGINES = {'BLENDER_RENDER'}

        @classmethod
        def poll(cls, context):
            mat = context.material
            engine = context.scene.render.engine
            return check_material(mat) and (mat.type in {'SURFACE', 'WIRE'}) and (engine in cls.COMPAT_ENGINES)

        def draw_header(self, context):
            mat = context.material

            if simple_material(mat):
                self.layout.prop(mat, "use_transparency", text="")

        def draw(self, context):
            layout = self.layout

            base_mat = context.material
            mat = active_node_mat(context.material)
            rayt = mat.raytrace_transparency

            if simple_material(base_mat):
                row = layout.row()
                row.active = mat.use_transparency
                row.prop(mat, "transparency_method", expand=True)

            split = layout.split()
            split.active = base_mat.use_transparency

            col = split.column()
            col.prop(mat, "alpha")
            row = col.row()
            row.active = (base_mat.transparency_method != 'MASK') and (not mat.use_shadeless)
            row.prop(mat, "specular_alpha", text="Specular")

            col = split.column()
            col.active = (not mat.use_shadeless)
            col.prop(rayt, "fresnel")
            sub = col.column()
            sub.active = (rayt.fresnel > 0.0)
            sub.prop(rayt, "fresnel_factor", text="Blend")

            if base_mat.transparency_method == 'RAYTRACE':
                layout.separator()
                split = layout.split()
                split.active = base_mat.use_transparency

                col = split.column()
                col.prop(rayt, "ior")
                col.prop(rayt, "filter")
                col.prop(rayt, "falloff")
                col.prop(rayt, "depth_max")
                col.prop(rayt, "depth")

                col = split.column()
                col.label(text="Gloss:")
                col.prop(rayt, "gloss_factor", text="Amount")
                sub = col.column()
                sub.active = rayt.gloss_factor < 1.0
                sub.prop(rayt, "gloss_threshold", text="Threshold")
                sub.prop(rayt, "gloss_samples", text="Samples")


    class MATERIAL_PT_mirror(MaterialButtonsPanel, Panel):
        bl_label = "Mirror"
        bl_options = {'DEFAULT_CLOSED'}
        COMPAT_ENGINES = {'BLENDER_RENDER'}

        @classmethod
        def poll(cls, context):
            mat = context.material
            engine = context.scene.render.engine
            return check_material(mat) and (mat.type in {'SURFACE', 'WIRE'}) and (engine in cls.COMPAT_ENGINES)

        def draw_header(self, context):
            raym = active_node_mat(context.material).raytrace_mirror

            self.layout.prop(raym, "use", text="")

        def draw(self, context):
            layout = self.layout

            mat = active_node_mat(context.material)
            raym = mat.raytrace_mirror

            layout.active = raym.use

            split = layout.split()

            col = split.column()
            col.prop(raym, "reflect_factor")
            col.prop(mat, "mirror_color", text="")

            col = split.column()
            col.prop(raym, "fresnel")
            sub = col.column()
            sub.active = (raym.fresnel > 0.0)
            sub.prop(raym, "fresnel_factor", text="Blend")

            split = layout.split()

            col = split.column()
            col.separator()
            col.prop(raym, "depth")
            col.prop(raym, "distance", text="Max Dist")
            col.separator()
            sub = col.split(percentage=0.4)
            sub.active = (raym.distance > 0.0)
            sub.label(text="Fade To:")
            sub.prop(raym, "fade_to", text="")

            col = split.column()
            col.label(text="Gloss:")
            col.prop(raym, "gloss_factor", text="Amount")
            sub = col.column()
            sub.active = (raym.gloss_factor < 1.0)
            sub.prop(raym, "gloss_threshold", text="Threshold")
            sub.prop(raym, "gloss_samples", text="Samples")
            sub.prop(raym, "gloss_anisotropic", text="Anisotropic")


    class MATERIAL_PT_sss(MaterialButtonsPanel, Panel):
        bl_label = "Subsurface Scattering"
        bl_options = {'DEFAULT_CLOSED'}
        COMPAT_ENGINES = {'BLENDER_RENDER'}

        @classmethod
        def poll(cls, context):
            mat = context.material
            engine = context.scene.render.engine
            return check_material(mat) and (mat.type in {'SURFACE', 'WIRE'}) and (engine in cls.COMPAT_ENGINES)

        def draw_header(self, context):
            mat = active_node_mat(context.material)
            sss = mat.subsurface_scattering

            self.layout.active = (not mat.use_shadeless)
            self.layout.prop(sss, "use", text="")

        def draw(self, context):
            layout = self.layout

            mat = active_node_mat(context.material)
            sss = mat.subsurface_scattering

            layout.active = (sss.use) and (not mat.use_shadeless)

            row = layout.row().split()
            sub = row.row(align=True).split(align=True, percentage=0.75)
            sub.menu("MATERIAL_MT_sss_presets", text=bpy.types.MATERIAL_MT_sss_presets.bl_label)
            sub.operator("material.sss_preset_add", text="", icon='ZOOMIN')
            sub.operator("material.sss_preset_add", text="", icon='ZOOMOUT').remove_active = True

            split = layout.split()

            col = split.column()
            col.prop(sss, "ior")
            col.prop(sss, "scale")
            col.prop(sss, "color", text="")
            col.prop(sss, "radius", text="RGB Radius", expand=True)

            col = split.column()
            sub = col.column(align=True)
            sub.label(text="Blend:")
            sub.prop(sss, "color_factor", text="Color")
            sub.prop(sss, "texture_factor", text="Texture")
            sub.label(text="Scattering Weight:")
            sub.prop(sss, "front")
            sub.prop(sss, "back")
            col.separator()
            col.prop(sss, "error_threshold", text="Error")


    class MATERIAL_PT_halo(MaterialButtonsPanel, Panel):
        bl_label = "Halo"
        COMPAT_ENGINES = {'BLENDER_RENDER'}

        @classmethod
        def poll(cls, context):
            mat = context.material
            engine = context.scene.render.engine
            return mat and (mat.type == 'HALO') and (engine in cls.COMPAT_ENGINES)

        def draw(self, context):
            layout = self.layout

            mat = context.material  # don't use node material
            halo = mat.halo

            def number_but(layout, toggle, number, name, color):
                row = layout.row(align=True)
                row.prop(halo, toggle, text="")
                sub = row.column(align=True)
                sub.active = getattr(halo, toggle)
                sub.prop(halo, number, text=name, translate=False)
                if not color == "":
                    sub.prop(mat, color, text="")

            split = layout.split()

            col = split.column()
            col.prop(mat, "alpha")
            col.prop(mat, "diffuse_color", text="")
            col.prop(halo, "seed")

            col = split.column()
            col.prop(halo, "size")
            col.prop(halo, "hardness")
            col.prop(halo, "add")

            layout.label(text="Options:")

            split = layout.split()
            col = split.column()
            col.prop(halo, "use_texture")
            col.prop(halo, "use_vertex_normal")
            col.prop(halo, "use_extreme_alpha")
            col.prop(halo, "use_shaded")
            col.prop(halo, "use_soft")

            col = split.column()
            number_but(col, "use_ring", "ring_count", iface_("Rings"), "mirror_color")
            number_but(col, "use_lines", "line_count", iface_("Lines"), "specular_color")
            number_but(col, "use_star", "star_tip_count", iface_("Star Tips"), "")


    class MATERIAL_PT_flare(MaterialButtonsPanel, Panel):
        bl_label = "Flare"
        COMPAT_ENGINES = {'BLENDER_RENDER'}

        @classmethod
        def poll(cls, context):
            mat = context.material
            engine = context.scene.render.engine
            return mat and (mat.type == 'HALO') and (engine in cls.COMPAT_ENGINES)

        def draw_header(self, context):
            halo = context.material.halo

            self.layout.prop(halo, "use_flare_mode", text="")

        def draw(self, context):
            layout = self.layout

            mat = context.material  # don't use node material
            halo = mat.halo

            layout.active = halo.use_flare_mode

            split = layout.split()

            col = split.column()
            col.prop(halo, "flare_size", text="Size")
            col.prop(halo, "flare_boost", text="Boost")
            col.prop(halo, "flare_seed", text="Seed")

            col = split.column()
            col.prop(halo, "flare_subflare_count", text="Subflares")
            col.prop(halo, "flare_subflare_size", text="Subsize")

    '''
#######################End Old Blender Internal Props##########################
###############################################################################
# Povray Nodes
###############################################################################

class PovraySocketUniversal(bpy.types.NodeSocket):
    bl_idname = 'PovraySocketUniversal'
    bl_label = 'Povray Socket'
    value_unlimited: bpy.props.FloatProperty(default=0.0)
    value_0_1: bpy.props.FloatProperty(min=0.0,max=1.0,default=0.0)
    value_0_10: bpy.props.FloatProperty(min=0.0,max=10.0,default=0.0)
    value_000001_10: bpy.props.FloatProperty(min=0.000001,max=10.0,default=0.0)
    value_1_9: bpy.props.IntProperty(min=1,max=9,default=1)
    value_0_255: bpy.props.IntProperty(min=0,max=255,default=0)
    percent: bpy.props.FloatProperty(min=0.0,max=100.0,default=0.0)
    def draw(self, context, layout, node, text):
        space = context.space_data
        tree = space.edit_tree
        links=tree.links
        if self.is_linked:
            value=[]
            for link in links:
                if link.from_node==node:
                    inps=link.to_node.inputs
                    for inp in inps:
                        if inp.bl_idname=="PovraySocketFloat_0_1" and inp.is_linked:
                            prop="value_0_1"
                            if prop not in value:
                                value.append(prop)
                        if inp.bl_idname=="PovraySocketFloat_000001_10" and inp.is_linked:
                            prop="value_000001_10"
                            if prop not in value:
                                value.append(prop)
                        if inp.bl_idname=="PovraySocketFloat_0_10" and inp.is_linked:
                            prop="value_0_10"
                            if prop not in value:
                                value.append(prop)
                        if inp.bl_idname=="PovraySocketInt_1_9" and inp.is_linked:
                            prop="value_1_9"
                            if prop not in value:
                                value.append(prop)
                        if inp.bl_idname=="PovraySocketInt_0_255" and inp.is_linked:
                            prop="value_0_255"
                            if prop not in value:
                                value.append(prop)
                        if inp.bl_idname=="PovraySocketFloatUnlimited" and inp.is_linked:
                            prop="value_unlimited"
                            if prop not in value:
                                value.append(prop)
            if len(value)==1:
                layout.prop(self, "%s"%value[0], text=text)
            else:
                layout.prop(self, "percent", text="Percent")
        else:
            layout.prop(self, "percent", text=text)
    def draw_color(self, context, node):
        return (1, 0, 0, 1)

class PovraySocketFloat_0_1(bpy.types.NodeSocket):
    bl_idname = 'PovraySocketFloat_0_1'
    bl_label = 'Povray Socket'
    default_value: bpy.props.FloatProperty(description="Input node Value_0_1",min=0,max=1,default=0)
    def draw(self, context, layout, node, text):
        if self.is_linked:
            layout.label(text)
        else:
            layout.prop(self, "default_value", text=text, slider=True)

    def draw_color(self, context, node):
        return (0.5, 0.7, 0.7, 1)

class PovraySocketFloat_0_10(bpy.types.NodeSocket):
    bl_idname = 'PovraySocketFloat_0_10'
    bl_label = 'Povray Socket'
    default_value: bpy.props.FloatProperty(description="Input node Value_0_10",min=0,max=10,default=0)
    def draw(self, context, layout, node, text):
        if node.bl_idname == 'ShaderNormalMapNode' and node.inputs[2].is_linked:
            layout.label(text='')
            self.hide_value=True
        if self.is_linked:
            layout.label(text)
        else:
            layout.prop(self, "default_value", text=text, slider=True)
    def draw_color(self, context, node):
        return (0.65, 0.65, 0.65, 1)

class PovraySocketFloat_10(bpy.types.NodeSocket):
    bl_idname = 'PovraySocketFloat_10'
    bl_label = 'Povray Socket'
    default_value: bpy.props.FloatProperty(description="Input node Value_10",min=-10,max=10,default=0)
    def draw(self, context, layout, node, text):
        if node.bl_idname == 'ShaderNormalMapNode' and node.inputs[2].is_linked:
            layout.label(text='')
            self.hide_value=True
        if self.is_linked:
            layout.label(text)
        else:
            layout.prop(self, "default_value", text=text, slider=True)
    def draw_color(self, context, node):
        return (0.65, 0.65, 0.65, 1)

class PovraySocketFloatPositive(bpy.types.NodeSocket):
    bl_idname = 'PovraySocketFloatPositive'
    bl_label = 'Povray Socket'
    default_value: bpy.props.FloatProperty(description="Input Node Value Positive", min=0.0, default=0)
    def draw(self, context, layout, node, text):
        if self.is_linked:
            layout.label(text)
        else:
            layout.prop(self, "default_value", text=text, slider=True)
    def draw_color(self, context, node):
        return (0.045, 0.005, 0.136, 1)

class PovraySocketFloat_000001_10(bpy.types.NodeSocket):
    bl_idname = 'PovraySocketFloat_000001_10'
    bl_label = 'Povray Socket'
    default_value: bpy.props.FloatProperty(min=0.000001,max=10,default=0.000001)
    def draw(self, context, layout, node, text):
        if self.is_output or self.is_linked:
            layout.label(text)
        else:
            layout.prop(self, "default_value", text=text, slider=True)
    def draw_color(self, context, node):
        return (1, 0, 0, 1)

class PovraySocketFloatUnlimited(bpy.types.NodeSocket):
    bl_idname = 'PovraySocketFloatUnlimited'
    bl_label = 'Povray Socket'
    default_value: bpy.props.FloatProperty(default = 0.0)
    def draw(self, context, layout, node, text):
        if self.is_linked:
            layout.label(text)
        else:
            layout.prop(self, "default_value", text=text, slider=True)
    def draw_color(self, context, node):
        return (0.7, 0.7, 1, 1)

class PovraySocketInt_1_9(bpy.types.NodeSocket):
    bl_idname = 'PovraySocketInt_1_9'
    bl_label = 'Povray Socket'
    default_value: bpy.props.IntProperty(description="Input node Value_1_9",min=1,max=9,default=6)
    def draw(self, context, layout, node, text):
        if self.is_linked:
            layout.label(text)
        else:
            layout.prop(self, "default_value", text=text)
    def draw_color(self, context, node):
        return (1, 0.7, 0.7, 1)

class PovraySocketInt_0_256(bpy.types.NodeSocket):
    bl_idname = 'PovraySocketInt_0_256'
    bl_label = 'Povray Socket'
    default_value: bpy.props.IntProperty(min=0,max=255,default=0)
    def draw(self, context, layout, node, text):
        if self.is_linked:
            layout.label(text)
        else:
            layout.prop(self, "default_value", text=text)
    def draw_color(self, context, node):
        return (0.5, 0.5, 0.5, 1)


class PovraySocketPattern(bpy.types.NodeSocket):
    bl_idname = 'PovraySocketPattern'
    bl_label = 'Povray Socket'

    default_value: bpy.props.EnumProperty(
            name="Pattern",
            description="Select the pattern",
            items=(
                ('boxed', "Boxed", ""),
                ('brick', "Brick", ""),
                ('cells', "Cells", ""),
                ('checker', "Checker", ""),
                ('granite', "Granite", ""),
                ('leopard', "Leopard", ""),
                ('marble', "Marble", ""),
                ('onion', "Onion", ""),
                ('planar', "Planar", ""),
                ('quilted', "Quilted", ""),
                ('ripples', "Ripples", ""),
                ('radial', "Radial", ""),
                ('spherical', "Spherical", ""),
                ('spotted', "Spotted", ""),
                ('waves', "Waves", ""),
                ('wood', "Wood", ""),
                ('wrinkles', "Wrinkles", "")
            ),
            default='granite')

    def draw(self, context, layout, node, text):
        if self.is_output or self.is_linked:
            layout.label(text="Pattern")
        else:
            layout.prop(self, "default_value", text=text)

    def draw_color(self, context, node):
        return (1, 1, 1, 1)

class PovraySocketColor(bpy.types.NodeSocket):
    bl_idname = 'PovraySocketColor'
    bl_label = 'Povray Socket'

    default_value: bpy.props.FloatVectorProperty(
            precision=4, step=0.01, min=0, soft_max=1,
            default=(0.0, 0.0, 0.0), options={'ANIMATABLE'}, subtype='COLOR')

    def draw(self, context, layout, node, text):
        if self.is_output or self.is_linked:
            layout.label(text)
        else:
            layout.prop(self, "default_value", text=text)

    def draw_color(self, context, node):
        return (1, 1, 0, 1)

class PovraySocketColorRGBFT(bpy.types.NodeSocket):
    bl_idname = 'PovraySocketColorRGBFT'
    bl_label = 'Povray Socket'

    default_value: bpy.props.FloatVectorProperty(
            precision=4, step=0.01, min=0, soft_max=1,
            default=(0.0, 0.0, 0.0), options={'ANIMATABLE'}, subtype='COLOR')
    f: bpy.props.FloatProperty(default = 0.0,min=0.0,max=1.0)
    t: bpy.props.FloatProperty(default = 0.0,min=0.0,max=1.0)
    def draw(self, context, layout, node, text):
        if self.is_output or self.is_linked:
            layout.label(text)
        else:
            layout.prop(self, "default_value", text=text)

    def draw_color(self, context, node):
        return (1, 1, 0, 1)

class PovraySocketTexture(bpy.types.NodeSocket):
    bl_idname = 'PovraySocketTexture'
    bl_label = 'Povray Socket'
    default_value: bpy.props.IntProperty()
    def draw(self, context, layout, node, text):
        layout.label(text)

    def draw_color(self, context, node):
        return (0, 1, 0, 1)



class PovraySocketTransform(bpy.types.NodeSocket):
    bl_idname = 'PovraySocketTransform'
    bl_label = 'Povray Socket'
    default_value: bpy.props.IntProperty(min=0,max=255,default=0)
    def draw(self, context, layout, node, text):
        layout.label(text)

    def draw_color(self, context, node):
        return (99/255, 99/255, 199/255, 1)

class PovraySocketNormal(bpy.types.NodeSocket):
    bl_idname = 'PovraySocketNormal'
    bl_label = 'Povray Socket'
    default_value: bpy.props.IntProperty(min=0,max=255,default=0)
    def draw(self, context, layout, node, text):
        layout.label(text)

    def draw_color(self, context, node):
        return (0.65, 0.65, 0.65, 1)

class PovraySocketSlope(bpy.types.NodeSocket):
    bl_idname = 'PovraySocketSlope'
    bl_label = 'Povray Socket'
    default_value: bpy.props.FloatProperty(min = 0.0, max = 1.0)
    height: bpy.props.FloatProperty(min = 0.0, max = 10.0)
    slope: bpy.props.FloatProperty(min = -10.0, max = 10.0)
    def draw(self, context, layout, node, text):
        if self.is_output or self.is_linked:
            layout.label(text)
        else:
            layout.prop(self,'default_value',text='')
            layout.prop(self,'height',text='')
            layout.prop(self,'slope',text='')
    def draw_color(self, context, node):
        return (0, 0, 0, 1)

class PovraySocketMap(bpy.types.NodeSocket):
    bl_idname = 'PovraySocketMap'
    bl_label = 'Povray Socket'
    default_value: bpy.props.StringProperty()
    def draw(self, context, layout, node, text):
        layout.label(text)
    def draw_color(self, context, node):
        return (0.2, 0, 0.2, 1)

class PovrayShaderNodeCategory(NodeCategory):
    @classmethod
    def poll(cls, context):
        return context.space_data.tree_type == 'ObjectNodeTree'

class PovrayTextureNodeCategory(NodeCategory):
    @classmethod
    def poll(cls, context):
        return context.space_data.tree_type == 'TextureNodeTree'

class PovraySceneNodeCategory(NodeCategory):
    @classmethod
    def poll(cls, context):
        return context.space_data.tree_type == 'CompositorNodeTree'

node_categories = [

    PovrayShaderNodeCategory("SHADEROUTPUT", "Output", items=[
        NodeItem("PovrayOutputNode"),
        ]),

    PovrayShaderNodeCategory("SIMPLE", "Simple texture", items=[
        NodeItem("PovrayTextureNode"),
        ]),

    PovrayShaderNodeCategory("MAPS", "Maps", items=[
        NodeItem("PovrayBumpMapNode"),
        NodeItem("PovrayColorImageNode"),
        NodeItem("ShaderNormalMapNode"),
        NodeItem("PovraySlopeNode"),
        NodeItem("ShaderTextureMapNode"),
        NodeItem("ShaderNodeValToRGB"),
        ]),

    PovrayShaderNodeCategory("OTHER", "Other patterns", items=[
        NodeItem("PovrayImagePatternNode"),
        NodeItem("ShaderPatternNode"),
        ]),

    PovrayShaderNodeCategory("COLOR", "Color", items=[
        NodeItem("PovrayPigmentNode"),
        ]),

    PovrayShaderNodeCategory("TRANSFORM", "Transform", items=[
        NodeItem("PovrayMappingNode"),
        NodeItem("PovrayMultiplyNode"),
        NodeItem("PovrayModifierNode"),
        NodeItem("PovrayTransformNode"),
        NodeItem("PovrayValueNode"),
        ]),

    PovrayShaderNodeCategory("FINISH", "Finish", items=[
        NodeItem("PovrayFinishNode"),
        NodeItem("PovrayDiffuseNode"),
        NodeItem("PovraySpecularNode"),
        NodeItem("PovrayPhongNode"),
        NodeItem("PovrayAmbientNode"),
        NodeItem("PovrayMirrorNode"),
        NodeItem("PovrayIridescenceNode"),
        NodeItem("PovraySubsurfaceNode"),
        ]),

    PovrayShaderNodeCategory("CYCLES", "Cycles", items=[
        NodeItem("ShaderNodeAddShader"),
        NodeItem("ShaderNodeAmbientOcclusion"),
        NodeItem("ShaderNodeAttribute"),
        NodeItem("ShaderNodeBackground"),
        NodeItem("ShaderNodeBlackbody"),
        NodeItem("ShaderNodeBrightContrast"),
        NodeItem("ShaderNodeBsdfAnisotropic"),
        NodeItem("ShaderNodeBsdfDiffuse"),
        NodeItem("ShaderNodeBsdfGlass"),
        NodeItem("ShaderNodeBsdfGlossy"),
        NodeItem("ShaderNodeBsdfHair"),
        NodeItem("ShaderNodeBsdfRefraction"),
        NodeItem("ShaderNodeBsdfToon"),
        NodeItem("ShaderNodeBsdfTranslucent"),
        NodeItem("ShaderNodeBsdfTransparent"),
        NodeItem("ShaderNodeBsdfVelvet"),
        NodeItem("ShaderNodeBump"),
        NodeItem("ShaderNodeCameraData"),
        NodeItem("ShaderNodeCombineHSV"),
        NodeItem("ShaderNodeCombineRGB"),
        NodeItem("ShaderNodeCombineXYZ"),
        NodeItem("ShaderNodeEmission"),
        NodeItem("ShaderNodeExtendedMaterial"),
        NodeItem("ShaderNodeFresnel"),
        NodeItem("ShaderNodeGamma"),
        NodeItem("ShaderNodeGeometry"),
        NodeItem("ShaderNodeGroup"),
        NodeItem("ShaderNodeHairInfo"),
        NodeItem("ShaderNodeHoldout"),
        NodeItem("ShaderNodeHueSaturation"),
        NodeItem("ShaderNodeInvert"),
        NodeItem("ShaderNodeLampData"),
        NodeItem("ShaderNodeLayerWeight"),
        NodeItem("ShaderNodeLightFalloff"),
        NodeItem("ShaderNodeLightPath"),
        NodeItem("ShaderNodeMapping"),
        NodeItem("ShaderNodeMaterial"),
        NodeItem("ShaderNodeMath"),
        NodeItem("ShaderNodeMixRGB"),
        NodeItem("ShaderNodeMixShader"),
        NodeItem("ShaderNodeNewGeometry"),
        NodeItem("ShaderNodeNormal"),
        NodeItem("ShaderNodeNormalMap"),
        NodeItem("ShaderNodeObjectInfo"),
        NodeItem("ShaderNodeOutput"),
        NodeItem("ShaderNodeOutputLamp"),
        NodeItem("ShaderNodeOutputLineStyle"),
        NodeItem("ShaderNodeOutputMaterial"),
        NodeItem("ShaderNodeOutputWorld"),
        NodeItem("ShaderNodeParticleInfo"),
        NodeItem("ShaderNodeRGB"),
        NodeItem("ShaderNodeRGBCurve"),
        NodeItem("ShaderNodeRGBToBW"),
        NodeItem("ShaderNodeScript"),
        NodeItem("ShaderNodeSeparateHSV"),
        NodeItem("ShaderNodeSeparateRGB"),
        NodeItem("ShaderNodeSeparateXYZ"),
        NodeItem("ShaderNodeSqueeze"),
        NodeItem("ShaderNodeSubsurfaceScattering"),
        NodeItem("ShaderNodeTangent"),
        NodeItem("ShaderNodeTexBrick"),
        NodeItem("ShaderNodeTexChecker"),
        NodeItem("ShaderNodeTexCoord"),
        NodeItem("ShaderNodeTexEnvironment"),
        NodeItem("ShaderNodeTexGradient"),
        NodeItem("ShaderNodeTexImage"),
        NodeItem("ShaderNodeTexMagic"),
        NodeItem("ShaderNodeTexMusgrave"),
        NodeItem("ShaderNodeTexNoise"),
        NodeItem("ShaderNodeTexPointDensity"),
        NodeItem("ShaderNodeTexSky"),
        NodeItem("ShaderNodeTexVoronoi"),
        NodeItem("ShaderNodeTexWave"),
        NodeItem("ShaderNodeTexture"),
        NodeItem("ShaderNodeUVAlongStroke"),
        NodeItem("ShaderNodeUVMap"),
        NodeItem("ShaderNodeValToRGB"),
        NodeItem("ShaderNodeValue"),
        NodeItem("ShaderNodeVectorCurve"),
        NodeItem("ShaderNodeVectorMath"),
        NodeItem("ShaderNodeVectorTransform"),
        NodeItem("ShaderNodeVolumeAbsorption"),
        NodeItem("ShaderNodeVolumeScatter"),
        NodeItem("ShaderNodeWavelength"),
        NodeItem("ShaderNodeWireframe"),
        ]),

    PovrayTextureNodeCategory("TEXTUREOUTPUT", "Output", items=[
        NodeItem("TextureNodeValToRGB"),
        NodeItem("TextureOutputNode"),
        ]),

    PovraySceneNodeCategory("ISOSURFACE", "Isosurface", items=[
        NodeItem("IsoPropsNode"),
        ]),

    PovraySceneNodeCategory("FOG", "Fog", items=[
        NodeItem("PovrayFogNode"),

        ]),
    ]
############### end nodes

###############################################################################
# Texture POV properties.
###############################################################################

class RenderPovSettingsTexture(PropertyGroup):
    """Declare texture level properties controllable in UI and translated to POV."""

    # former Space properties from removed Blender Internal
    active_texture_index: IntProperty(
        name = "Index for texture_slots",
        min=0,
        max=17,
        default=0,
    )

    use_limited_texture_context: BoolProperty(
        name="",
        description="Use the limited version of texture user (for ‘old shading’ mode)",
        default=True,
    )

    texture_context: EnumProperty(
        name="Texture context",
        description="Type of texture data to display and edit",
        items=(
            ('MATERIAL', "", "Show material textures", "MATERIAL",0), # "Show material textures"
            ('WORLD', "", "Show world textures", "WORLD",1), # "Show world textures"
            ('LAMP', "", "Show lamp textures", "LIGHT",2), # "Show lamp textures"
            ('PARTICLES', "", "Show particles textures", "PARTICLES",3), # "Show particles textures"
            ('LINESTYLE', "", "Show linestyle textures", "LINE_DATA",4), # "Show linestyle textures"
            ('OTHER', "", "Show other data textures", "TEXTURE_DATA",5), # "Show other data textures"
        ),
        default = 'MATERIAL',
    )

    # Custom texture gamma
    tex_gamma_enable: BoolProperty(
        name="Enable custom texture gamma",
        description="Notify some custom gamma for which texture has been precorrected "
        "without the file format carrying it and only if it differs from your "
        "OS expected standard (see pov doc)",
        default=False,
    )

    tex_gamma_value: FloatProperty(
        name="Custom texture gamma",
        description="value for which the file was issued e.g. a Raw photo is gamma 1.0",
        min=0.45, max=5.00, soft_min=1.00, soft_max=2.50, default=1.00
    )

    ##################################CustomPOV Code############################
    # commented out below if we wanted custom pov code in texture only, inside exported material:
    # replacement_text = StringProperty(
    #        name="Declared name:",
    #        description="Type the declared name in custom POV code or an external .inc "
    #                    "it points at. pigment {} expected",
    #        default="")

    tex_pattern_type: EnumProperty(
        name="Texture_Type",
        description="Choose between Blender or POV parameters to specify texture",
        items= (
            ('agate', 'Agate', '','PLUGIN', 0),
            ('aoi', 'Aoi', '', 'PLUGIN', 1),
            ('average', 'Average', '', 'PLUGIN', 2),
            ('boxed', 'Boxed', '', 'PLUGIN', 3),
            ('bozo', 'Bozo', '', 'PLUGIN', 4),
            ('bumps', 'Bumps', '', 'PLUGIN', 5),
            ('cells', 'Cells', '', 'PLUGIN', 6),
            ('crackle', 'Crackle', '', 'PLUGIN', 7),
            ('cubic', 'Cubic', '', 'PLUGIN', 8),
            ('cylindrical', 'Cylindrical', '', 'PLUGIN', 9),
            ('density_file', 'Density', '(.df3)', 'PLUGIN', 10),
            ('dents', 'Dents', '', 'PLUGIN', 11),
            ('fractal', 'Fractal', '', 'PLUGIN', 12),
            ('function', 'Function', '', 'PLUGIN', 13),
            ('gradient', 'Gradient', '', 'PLUGIN', 14),
            ('granite', 'Granite', '', 'PLUGIN', 15),
            ('image_pattern', 'Image pattern', '', 'PLUGIN', 16),
            ('leopard', 'Leopard', '', 'PLUGIN', 17),
            ('marble', 'Marble', '', 'PLUGIN', 18),
            ('onion', 'Onion', '', 'PLUGIN', 19),
            ('pigment_pattern', 'pigment pattern', '', 'PLUGIN', 20),
            ('planar', 'Planar', '', 'PLUGIN', 21),
            ('quilted', 'Quilted', '', 'PLUGIN', 22),
            ('radial', 'Radial', '', 'PLUGIN', 23),
            ('ripples', 'Ripples', '', 'PLUGIN', 24),
            ('slope', 'Slope', '', 'PLUGIN', 25),
            ('spherical', 'Spherical', '', 'PLUGIN', 26),
            ('spiral1', 'Spiral1', '', 'PLUGIN', 27),
            ('spiral2', 'Spiral2', '', 'PLUGIN', 28),
            ('spotted', 'Spotted', '', 'PLUGIN', 29),
            ('waves', 'Waves', '', 'PLUGIN', 30),
            ('wood', 'Wood', '', 'PLUGIN', 31),
            ('wrinkles', 'Wrinkles', '', 'PLUGIN', 32),
            ('brick', "Brick", "", 'PLUGIN', 33),
            ('checker', "Checker", "", 'PLUGIN', 34),
            ('hexagon', "Hexagon", "", 'PLUGIN', 35),
            ('object', "Mesh", "", 'PLUGIN', 36),
            ('emulator', "Internal Emulator", "", 'PLUG', 37)
        ),
        default='emulator',
    )

    magnet_style: EnumProperty(
        name="Magnet style",
        description="magnet or julia",
        items=(('mandel', "Mandelbrot", ""),('julia', "Julia", "")),
        default='julia',
    )

    magnet_type: IntProperty(
        name="Magnet_type",
        description="1 or 2",
        min=1,
        max=2,
        default=2,
    )

    warp_types: EnumProperty(
        name="Warp Types",
        description="Select the type of warp",
        items=(('PLANAR', "Planar", ""), ('CUBIC', "Cubic", ""),
               ('SPHERICAL', "Spherical", ""), ('TOROIDAL', "Toroidal", ""),
               ('CYLINDRICAL', "Cylindrical", ""), ('NONE', "None", "No indentation")),
        default='NONE'
    )

    warp_orientation: EnumProperty(
        name="Warp Orientation",
        description="Select the orientation of warp",
        items=(('x', "X", ""), ('y', "Y", ""), ('z', "Z", "")),
        default='y',
    )

    wave_type: EnumProperty(
        name="Waves type",
        description="Select the type of waves",
        items=(('ramp', "Ramp", ""), ('sine', "Sine", ""), ('scallop', "Scallop", ""),
               ('cubic', "Cubic", ""), ('poly', "Poly", ""), ('triangle', 'Triangle', "")),
        default='ramp',
    )

    gen_noise: IntProperty(
        name="Noise Generators",
        description="Noise Generators",
        min=1, max=3, default=1,
    )

    warp_dist_exp: FloatProperty(
        name="Distance exponent",
        description="Distance exponent",
        min=0.0, max=100.0, default=1.0,
    )

    warp_tor_major_radius: FloatProperty(
        name="Major radius",
        description="Torus is distance from major radius",
        min=0.0, max=5.0, default=1.0,
    )

    warp_turbulence_x: FloatProperty(
        name="Turbulence X",
        description="Turbulence X",
        min=0.0, max=5.0, default=0.0,
    )

    warp_turbulence_y: FloatProperty(
        name="Turbulence Y",
        description="Turbulence Y",
        min=0.0, max=5.0, default=0.0
    )

    warp_turbulence_z: FloatProperty(
        name="Turbulence Z",
        description="Turbulence Z",
        min=0.0, max=5.0, default=0.0
    )

    modifier_octaves: IntProperty(
        name="Turbulence octaves",
        description="Turbulence octaves",
        min=1, max=10, default=1
    )

    modifier_lambda: FloatProperty(
        name="Turbulence lambda",
        description="Turbulence lambda",
        min=0.0, max=5.0, default=1.00
    )

    modifier_omega: FloatProperty(
        name="Turbulence omega",
        description="Turbulence omega",
        min=0.0, max=10.0, default=1.00
    )

    modifier_phase: FloatProperty(
        name="Phase",
        description="The phase value causes the map entries to be shifted so that the map "
        "starts and ends at a different place",
        min=0.0, max=2.0, default=0.0
    )

    modifier_frequency: FloatProperty(
        name="Frequency",
        description="The frequency keyword adjusts the number of times that a color map "
        "repeats over one cycle of a pattern",
        min=0.0, max=25.0, default=2.0
    )

    modifier_turbulence: FloatProperty(
        name="Turbulence",
        description="Turbulence",
        min=0.0, max=5.0, default=2.0
    )

    modifier_numbers: IntProperty(
        name="Numbers",
        description="Numbers",
        min=1, max=27, default=2
    )

    modifier_control0: IntProperty(
        name="Control0",
        description="Control0",
        min=0, max=100, default=1
    )

    modifier_control1: IntProperty(
        name="Control1",
        description="Control1",
        min=0, max=100, default=1
    )

    brick_size_x: FloatProperty(
        name="Brick size x",
        description="",
        min=0.0000, max=1.0000, default=0.2500
    )

    brick_size_y: FloatProperty(
        name="Brick size y",
        description="",
        min=0.0000, max=1.0000, default=0.0525
    )

    brick_size_z: FloatProperty(
        name="Brick size z",
        description="",
        min=0.0000, max=1.0000, default=0.1250
    )

    brick_mortar: FloatProperty(
        name="Mortar",
        description="Mortar",
        min=0.000, max=1.500, default=0.01
    )

    julia_complex_1: FloatProperty(
        name="Julia Complex 1",
        description="",
        min=0.000, max=1.500, default=0.360
    )

    julia_complex_2: FloatProperty(
        name="Julia Complex 2",
        description="",
        min=0.000, max=1.500, default=0.250
    )

    f_iter: IntProperty(
        name="Fractal Iteration",
        description="",
        min=0, max=100, default=20
    )

    f_exponent: IntProperty(
        name="Fractal Exponent",
        description="",
        min=2, max=33, default=2
    )

    f_ior: IntProperty(
        name="Fractal Interior",
        description="",
        min=1, max=6, default=1
    )

    f_ior_fac: FloatProperty(
        name="Fractal Interior Factor",
        description="",
        min=0.0, max=10.0, default=1.0
    )

    f_eor: IntProperty(
        name="Fractal Exterior",
        description="",
        min=1, max=8, default=1
    )

    f_eor_fac: FloatProperty(
        name="Fractal Exterior Factor",
        description="",
        min=0.0, max=10.0, default=1.0
    )

    grad_orient_x: IntProperty(
        name="Gradient orientation X",
        description="",
        min=0, max=1, default=0
    )

    grad_orient_y: IntProperty(
        name="Gradient orientation Y",
        description="",
        min=0, max=1, default=1
    )

    grad_orient_z: IntProperty(
        name="Gradient orientation Z",
        description="",
        min=0, max=1, default=0
    )

    pave_sides: EnumProperty(
        name="Pavement sides",
        description="",
        items=(
            ('3', "3", ""),
            ('4', "4", ""),
            ('6', "6", "")
        ),
        default='3'
    )

    pave_pat_2: IntProperty(
        name="Pavement pattern 2",
        description="maximum: 2",
        min=1, max=2, default=2
    )

    pave_pat_3: IntProperty(
        name="Pavement pattern 3",
        description="maximum: 3",
        min=1, max=3, default=3
    )

    pave_pat_4: IntProperty(
        name="Pavement pattern 4",
        description="maximum: 4",
        min=1, max=4, default=4
    )

    pave_pat_5: IntProperty(
        name="Pavement pattern 5",
        description="maximum: 5",
        min=1, max=5, default=5
    )

    pave_pat_7: IntProperty(
        name="Pavement pattern 7",
        description="maximum: 7",
        min=1, max=7, default=7
    )

    pave_pat_12: IntProperty(
        name="Pavement pattern 12",
        description="maximum: 12",
        min=1, max=12, default=12
    )

    pave_pat_22: IntProperty(
        name="Pavement pattern 22",
        description="maximum: 22",
        min=1, max=22, default=22
    )

    pave_pat_35: IntProperty(
        name="Pavement pattern 35",
        description="maximum: 35",
        min=1, max=35, default=35,
    )

    pave_tiles: IntProperty(
        name="Pavement tiles",
        description="If sides = 6, maximum tiles 5!!!",
        min=1, max=6, default=1
    )

    pave_form: IntProperty(
        name="Pavement form",
        description="",
        min=0, max=4, default=0
    )

    #########FUNCTIONS#############################################################################
    #########FUNCTIONS#############################################################################

    func_list: EnumProperty(
        name="Functions",
        description="Select the function for create pattern",
        items=(
            ('NONE', "None", "No indentation"),
            ("f_algbr_cyl1","Algbr cyl1",""), ("f_algbr_cyl2","Algbr cyl2",""),
            ("f_algbr_cyl3","Algbr cyl3",""), ("f_algbr_cyl4","Algbr cyl4",""),
            ("f_bicorn","Bicorn",""), ("f_bifolia","Bifolia",""),
            ("f_blob","Blob",""), ("f_blob2","Blob2",""),
            ("f_boy_surface","Boy surface",""), ("f_comma","Comma",""),
            ("f_cross_ellipsoids","Cross ellipsoids",""),
            ("f_crossed_trough","Crossed trough",""), ("f_cubic_saddle","Cubic saddle",""),
            ("f_cushion","Cushion",""), ("f_devils_curve","Devils curve",""),
            ("f_devils_curve_2d","Devils curve 2d",""),
            ("f_dupin_cyclid","Dupin cyclid",""), ("f_ellipsoid","Ellipsoid",""),
            ("f_enneper","Enneper",""), ("f_flange_cover","Flange cover",""),
            ("f_folium_surface","Folium surface",""),
            ("f_folium_surface_2d","Folium surface 2d",""), ("f_glob","Glob",""),
            ("f_heart","Heart",""), ("f_helical_torus","Helical torus",""),
            ("f_helix1","Helix1",""), ("f_helix2","Helix2",""), ("f_hex_x","Hex x",""),
            ("f_hex_y","Hex y",""), ("f_hetero_mf","Hetero mf",""),
            ("f_hunt_surface","Hunt surface",""),
            ("f_hyperbolic_torus","Hyperbolic torus",""),
            ("f_isect_ellipsoids","Isect ellipsoids",""),
            ("f_kampyle_of_eudoxus","Kampyle of eudoxus",""),
            ("f_kampyle_of_eudoxus_2d","Kampyle of eudoxus 2d",""),
            ("f_klein_bottle","Klein bottle",""),
            ("f_kummer_surface_v1","Kummer surface v1",""),
            ("f_kummer_surface_v2","Kummer surface v2",""),
            ("f_lemniscate_of_gerono","Lemniscate of gerono",""),
            ("f_lemniscate_of_gerono_2d","Lemniscate of gerono 2d",""),
            ("f_mesh1","Mesh1",""), ("f_mitre","Mitre",""),
            ("f_nodal_cubic","Nodal cubic",""), ("f_noise3d","Noise3d",""),
            ("f_noise_generator","Noise generator",""), ("f_odd","Odd",""),
            ("f_ovals_of_cassini","Ovals of cassini",""), ("f_paraboloid","Paraboloid",""),
            ("f_parabolic_torus","Parabolic torus",""), ("f_ph","Ph",""),
            ("f_pillow","Pillow",""), ("f_piriform","Piriform",""),
            ("f_piriform_2d","Piriform 2d",""), ("f_poly4","Poly4",""),
            ("f_polytubes","Polytubes",""), ("f_quantum","Quantum",""),
            ("f_quartic_paraboloid","Quartic paraboloid",""),
            ("f_quartic_saddle","Quartic saddle",""),
            ("f_quartic_cylinder","Quartic cylinder",""), ("f_r","R",""),
            ("f_ridge","Ridge",""), ("f_ridged_mf","Ridged mf",""),
            ("f_rounded_box","Rounded box",""), ("f_sphere","Sphere",""),
            ("f_spikes","Spikes",""), ("f_spikes_2d","Spikes 2d",""),
            ("f_spiral","Spiral",""), ("f_steiners_roman","Steiners roman",""),
            ("f_strophoid","Strophoid",""), ("f_strophoid_2d","Strophoid 2d",""),
            ("f_superellipsoid","Superellipsoid",""), ("f_th","Th",""),
            ("f_torus","Torus",""), ("f_torus2","Torus2",""),
            ("f_torus_gumdrop","Torus gumdrop",""), ("f_umbrella","Umbrella",""),
            ("f_witch_of_agnesi","Witch of agnesi",""),
            ("f_witch_of_agnesi_2d","Witch of agnesi 2d","")
        ),

        default='NONE',
    )

    func_x: FloatProperty(
        name="FX",
        description="",
        min=0.0, max=25.0, default=1.0
    )

    func_plus_x: EnumProperty(
        name="Func plus x",
        description="",
        items=(('NONE', "None", ""), ('increase', "*", ""), ('plus', "+", "")),
        default='NONE',
    )

    func_y: FloatProperty(
        name="FY",
        description="",
        min=0.0, max=25.0, default=1.0
    )

    func_plus_y: EnumProperty(
        name="Func plus y",
        description="",
        items=(('NONE', "None", ""), ('increase', "*", ""), ('plus', "+", "")),
        default='NONE',
    )

    func_z: FloatProperty(
        name="FZ",
        description="",
        min=0.0, max=25.0, default=1.0
    )

    func_plus_z: EnumProperty(
        name="Func plus z",
        description="",
        items=(
            ('NONE', "None", ""),
            ('increase', "*", ""),
            ('plus', "+", "")
        ),
        default='NONE',
    )

    func_P0: FloatProperty(
        name="P0",
        description="",
        min=0.0, max=25.0, default=1.0
    )

    func_P1: FloatProperty(
        name="P1",
        description="",
        min=0.0, max=25.0, default=1.0
    )

    func_P2: FloatProperty(
        name="P2",
        description="",
        min=0.0, max=25.0, default=1.0
    )

    func_P3: FloatProperty(
        name="P3",
        description="",
        min=0.0, max=25.0, default=1.0
    )

    func_P4: FloatProperty(
        name="P4",
        description="",
        min=0.0, max=25.0, default=1.0
    )

    func_P5: FloatProperty(
        name="P5",
        description="",
        min=0.0, max=25.0, default=1.0
    )

    func_P6: FloatProperty(
        name="P6",
        description="",
        min=0.0, max=25.0, default=1.0
    )

    func_P7: FloatProperty(
        name="P7",
        description="",
        min=0.0, max=25.0, default=1.0
    )

    func_P8: FloatProperty(
        name="P8",
        description="",
        min=0.0, max=25.0, default=1.0
    )

    func_P9: FloatProperty(
        name="P9",
        description="",
        min=0.0, max=25.0, default=1.0
    )

    #########################################
    tex_rot_x: FloatProperty(
        name="Rotate X",
        description="",
        min=-180.0, max=180.0, default=0.0
    )

    tex_rot_y: FloatProperty(
        name="Rotate Y",
        description="",
        min=-180.0, max=180.0, default=0.0
    )

    tex_rot_z: FloatProperty(
        name="Rotate Z",
        description="",
        min=-180.0, max=180.0, default=0.0
    )

    tex_mov_x: FloatProperty(
        name="Move X",
        description="",
        min=-100000.0, max=100000.0, default=0.0
    )

    tex_mov_y: FloatProperty(
        name="Move Y",
        description="",
        min=-100000.0,
        max=100000.0,
        default=0.0,
    )

    tex_mov_z: FloatProperty(
        name="Move Z",
        description="",
        min=-100000.0,
        max=100000.0,
        default=0.0,
    )

    tex_scale_x: FloatProperty(
        name="Scale X",
        description="",
        min=0.0,
        max=10000.0,
        default=1.0,
    )

    tex_scale_y: FloatProperty(
        name="Scale Y",
        description="",
        min=0.0,
        max=10000.0,
        default=1.0,
    )

    tex_scale_z: FloatProperty(
        name="Scale Z",
        description="",
        min=0.0,
        max=10000.0,
        default=1.0,
    )

###############################################################################
# Object POV properties.
###############################################################################

class RenderPovSettingsObject(PropertyGroup):
    """Declare object and primitives level properties controllable in UI and translated to POV."""

    # Pov inside_vector used for CSG
    inside_vector: FloatVectorProperty(
        name="CSG Inside Vector",
        description="Direction to shoot CSG inside test rays at",
        precision=4,
        step=0.01,
        min=0,
        soft_max=1,
        default=(0.001, 0.001, 0.5),
        options={'ANIMATABLE'},
        subtype='XYZ'
    )

    # Importance sampling
    importance_value: FloatProperty(
        name="Radiosity Importance",
        description="Priority value relative to other objects for sampling radiosity rays. "
        "Increase to get more radiosity rays at comparatively small yet "
        "bright objects",
        min=0.01, max=1.00, default=0.50
    )

    # Collect photons
    collect_photons: BoolProperty(
        name="Receive Photon Caustics",
        description="Enable object to collect photons from other objects caustics. Turn "
        "off for objects that don't really need to receive caustics (e.g. objects"
        " that generate caustics often don't need to show any on themselves)",
        default=True,
    )

    # Photons spacing_multiplier
    spacing_multiplier: FloatProperty(
        name="Photons Spacing Multiplier",
        description="Multiplier value relative to global spacing of photons. "
        "Decrease by half to get 4x more photons at surface of "
        "this object (or 8x media photons than specified in the globals",
        min=0.01, max=1.00, default=1.00)

    ##################################CustomPOV Code############################
    # Only DUMMIES below for now:
    replacement_text: StringProperty(
        name="Declared name:",
        description="Type the declared name in custom POV code or an external .inc "
        "it points at. Any POV shape expected e.g: isosurface {}",
        default="",
    )

    #############POV specific object properties.############################
    object_as: StringProperty(maxlen=1024)

    imported_loc: FloatVectorProperty(
        name="Imported Pov location",
        precision=6,
        default=(0.0, 0.0, 0.0),
    )

    imported_loc_cap: FloatVectorProperty(
        name="Imported Pov location",
        precision=6,
        default=(0.0, 0.0, 2.0),
    )

    unlock_parameters: BoolProperty(name="Lock",default = False)

    # not in UI yet but used for sor (lathe) / prism... pov primitives
    curveshape: EnumProperty(
        name="Povray Shape Type",
        items=(("birail", "Birail", ""),
               ("cairo", "Cairo", ""),
               ("lathe", "Lathe", ""),
               ("loft", "Loft", ""),
               ("prism", "Prism", ""),
               ("sphere_sweep", "Sphere Sweep", "")),
        default="sphere_sweep",
    )

    mesh_write_as: EnumProperty(
        name="Mesh Write As",
        items=(("blobgrid", "Blob Grid", ""),
               ("grid", "Grid", ""),
               ("mesh", "Mesh", "")),
        default="mesh",
    )

    object_ior: FloatProperty(
        name="IOR", description="IOR",
        min=1.0, max=10.0,default=1.0
    )

    # shape_as_light = StringProperty(name="Light",maxlen=1024)
    # fake_caustics_power = FloatProperty(
            # name="Power", description="Fake caustics power",
            # min=0.0, max=10.0,default=0.0)
    # target = BoolProperty(name="Target",description="",default=False)
    # target_value = FloatProperty(
            # name="Value", description="",
            # min=0.0, max=1.0,default=1.0)
    # refraction = BoolProperty(name="Refraction",description="",default=False)
    # dispersion = BoolProperty(name="Dispersion",description="",default=False)
    # dispersion_value = FloatProperty(
            # name="Dispersion", description="Good values are 1.01 to 1.1. ",
            # min=1.0, max=1.2,default=1.01)
    # dispersion_samples = IntProperty(name="Samples",min=2, max=100,default=7)
    # reflection = BoolProperty(name="Reflection",description="",default=False)
    # pass_through = BoolProperty(name="Pass through",description="",default=False)
    no_shadow: BoolProperty(name="No Shadow",default=False)

    no_image: BoolProperty(name="No Image",default=False)

    no_reflection: BoolProperty(name="No Reflection",default=False)

    no_radiosity: BoolProperty(name="No Radiosity",default=False)

    inverse: BoolProperty(name="Inverse",default=False)

    sturm: BoolProperty(name="Sturm",default=False)

    double_illuminate: BoolProperty(name="Double Illuminate",default=False)

    hierarchy: BoolProperty(name="Hierarchy",default=False)

    hollow: BoolProperty(name="Hollow",default=False)

    boundorclip: EnumProperty(
        name="Boundorclip",
        items=(("none", "None", ""),
               ("bounded_by", "Bounded_by", ""),
               ("clipped_by", "Clipped_by", "")),
        default="none",
    )

    boundorclipob: StringProperty(maxlen=1024)

    addboundorclip: BoolProperty(description="",default=False)

    blob_threshold: FloatProperty(name="Threshold",min=0.00, max=10.0, default=0.6)

    blob_strength: FloatProperty(name="Strength",min=-10.00, max=10.0, default=1.00)

    res_u: IntProperty(name="U",min=100, max=1000, default=500)

    res_v: IntProperty(name="V",min=100, max=1000, default=500)

    contained_by: EnumProperty(
        name="Contained by",
        items=(("box", "Box", ""),
               ("sphere", "Sphere", "")),
        default="box",
    )

    container_scale: FloatProperty(name="Container Scale",min=0.0, max=10.0, default=1.00)

    threshold: FloatProperty(name="Threshold",min=0.0, max=10.0, default=0.00)

    accuracy: FloatProperty(name="Accuracy",min=0.0001, max=0.1, default=0.001)

    max_gradient: FloatProperty(name="Max Gradient",min=0.0, max=100.0, default=5.0)

    all_intersections: BoolProperty(name="All Intersections",default=False)

    max_trace: IntProperty(name="Max Trace",min=1, max=100,default=1)


    def prop_update_cylinder(self, context):
        """Update POV cylinder primitive parameters not only at creation but anytime they are changed in UI."""
        if bpy.ops.pov.cylinder_update.poll():
            bpy.ops.pov.cylinder_update()

    cylinder_radius: FloatProperty(
        name="Cylinder R",min=0.00, max=10.0, default=0.04, update=prop_update_cylinder)

    cylinder_location_cap: FloatVectorProperty(
        name="Cylinder Cap Location", subtype='TRANSLATION',
        description="The position of the 'other' end of the cylinder (relative to object location)",
        default=(0.0, 0.0, 2.0), update=prop_update_cylinder
    )

    imported_cyl_loc: FloatVectorProperty(
        name="Imported Pov location",
        precision=6,
        default=(0.0, 0.0, 0.0)
    )

    imported_cyl_loc_cap: FloatVectorProperty(
        name="Imported Pov location",
        precision=6,
        default=(0.0, 0.0, 2.0)
    )

    def prop_update_sphere(self, context):

        """Update POV sphere primitive parameters not only at creation but anytime they are changed in UI."""

        bpy.ops.pov.sphere_update()

    sphere_radius: FloatProperty(
        name="Sphere radius",min=0.00, max=10.0, default=0.5, update=prop_update_sphere)

    def prop_update_cone(self, context):

        """Update POV cone primitive parameters not only at creation but anytime they are changed in UI."""

        bpy.ops.pov.cone_update()

    cone_base_radius: FloatProperty(
        name = "Base radius",
        description = "The first radius of the cone",
        default = 1.0, min = 0.01, max = 100.0, update=prop_update_cone
    )

    cone_cap_radius: FloatProperty(
        name = "Cap radius",
        description = "The second radius of the cone",
        default = 0.3, min = 0.0, max = 100.0, update=prop_update_cone
    )

    cone_segments: IntProperty(
        name = "Segments",
        description = "Radial segmentation of proxy mesh",
        default = 16, min = 3, max = 265, update=prop_update_cone
    )

    cone_height: FloatProperty(
        name = "Height",
        description = "Height of the cone",
        default = 2.0, min = 0.01, max = 100.0, update=prop_update_cone
    )

    cone_base_z: FloatProperty()

    cone_cap_z: FloatProperty()

###########Parametric
    def prop_update_parametric(self, context):

        """Update POV parametric surface primitive parameters not only at creation but anytime they are changed in UI."""

        bpy.ops.pov.parametric_update()

    u_min: FloatProperty(
        name = "U Min",
        description = "",
        default = 0.0, update=prop_update_parametric
    )

    v_min: FloatProperty(
        name = "V Min",
        description = "",
        default = 0.0,
        update=prop_update_parametric
    )

    u_max: FloatProperty(
        name = "U Max",
        description = "",
        default = 6.28,
        update=prop_update_parametric
    )

    v_max: FloatProperty(
        name = "V Max",
        description = "",
        default = 12.57, update=prop_update_parametric
    )

    x_eq: StringProperty(
        maxlen=1024,
        default = "cos(v)*(1+cos(u))*sin(v/8)",
        update=prop_update_parametric
    )

    y_eq: StringProperty(
        maxlen=1024,
        default = "sin(u)*sin(v/8)+cos(v/8)*1.5",
        update=prop_update_parametric
    )

    z_eq: StringProperty(
        maxlen=1024,
        default = "sin(v)*(1+cos(u))*sin(v/8)",
        update=prop_update_parametric
    )

    ###########Torus

    def prop_update_torus(self, context):

        """Update POV torus primitive parameters not only at creation but anytime they are changed in UI."""

        bpy.ops.pov.torus_update()

    torus_major_segments: IntProperty(
        name = "Segments",
        description = "Radial segmentation of proxy mesh",
        default = 48, min = 3, max = 720, update=prop_update_torus
    )

    torus_minor_segments: IntProperty(
        name = "Segments",
        description = "Cross-section segmentation of proxy mesh",
        default = 12, min = 3, max = 720, update=prop_update_torus
    )

    torus_major_radius: FloatProperty(
        name="Major radius",
        description="Major radius",
        min=0.00, max=100.00, default=1.0, update=prop_update_torus
    )

    torus_minor_radius: FloatProperty(
        name="Minor radius",
        description="Minor radius",
        min=0.00, max=100.00, default=0.25, update=prop_update_torus
    )


    ###########Rainbow
    arc_angle: FloatProperty(
        name = "Arc angle",
        description = "The angle of the raynbow arc in degrees",
        default = 360, min = 0.01, max = 360.0
    )

    falloff_angle: FloatProperty(
        name = "Falloff angle",
        description = "The angle after which rainbow dissolves into background",
        default = 360, min = 0.0, max = 360
    )

    ###########HeightFields

    quality: IntProperty(
        name = "Quality",
        description = "",
        default = 100, min = 1, max = 100
    )

    hf_filename: StringProperty(maxlen = 1024)

    hf_gamma: FloatProperty(
        name="Gamma",
        description="Gamma",
        min=0.0001, max=20.0, default=1.0
    )

    hf_premultiplied: BoolProperty(
        name="Premultiplied",
        description="Premultiplied",
        default=True,
    )

    hf_smooth: BoolProperty(
        name="Smooth",
        description="Smooth",
        default=False,
    )

    hf_water: FloatProperty(
        name="Water Level",
        description="Wather Level",
        min=0.00, max=1.00, default=0.0,
    )

    hf_hierarchy: BoolProperty(
        name="Hierarchy",
        description="Height field hierarchy",
        default=True,
    )

    ##############Superellipsoid
    def prop_update_superellipsoid(self, context):

        """Update POV superellipsoid primitive parameters not only at creation but anytime they are changed in UI."""

        bpy.ops.pov.superellipsoid_update()

    se_param1: FloatProperty(
        name="Parameter 1",
        description="",
        min=0.00, max=10.0, default=0.04
    )

    se_param2: FloatProperty(
        name="Parameter 2",
        description="",
        min=0.00, max=10.0, default=0.04
    )

    se_u: IntProperty(
        name = "U-segments",
        description = "radial segmentation",
        default = 20, min = 4, max = 265,
        update=prop_update_superellipsoid
    )

    se_v: IntProperty(
        name = "V-segments",
        description = "lateral segmentation",
        default = 20, min = 4, max = 265,
        update=prop_update_superellipsoid
    )

    se_n1: FloatProperty(
        name = "Ring manipulator",
        description = "Manipulates the shape of the Ring",
        default = 1.0, min = 0.01, max = 100.0,
        update=prop_update_superellipsoid
    )

    se_n2: FloatProperty(name = "Cross manipulator",
        description = "Manipulates the shape of the cross-section",
        default = 1.0, min = 0.01, max = 100.0,
        update=prop_update_superellipsoid
    )

    se_edit: EnumProperty(items=[("NOTHING", "Nothing", ""),
                                ("NGONS", "N-Gons", ""),
                                ("TRIANGLES", "Triangles", "")],
        name="Fill up and down",
        description="",
        default='TRIANGLES',
        update=prop_update_superellipsoid
    )

    #############Used for loft and Superellipsoid, etc.
    curveshape: EnumProperty(
        name="Povray Shape Type",
        items=(
            ("birail", "Birail", ""),
            ("cairo", "Cairo", ""),
            ("lathe", "Lathe", ""),
            ("loft", "Loft", ""),
            ("prism", "Prism", ""),
            ("sphere_sweep", "Sphere Sweep", ""),
            ("sor", "Surface of Revolution", "")
        ),
        default="sphere_sweep",
    )

#############Supertorus
    def prop_update_supertorus(self, context):

        """Update POV supertorus primitive parameters not only at creation but anytime they are changed in UI."""

        bpy.ops.pov.supertorus_update()

    st_major_radius: FloatProperty(
        name="Major radius",
        description="Major radius",
        min=0.00,
        max=100.00,
        default=1.0,
        update=prop_update_supertorus
    )

    st_minor_radius: FloatProperty(
        name="Minor radius",
        description="Minor radius",
        min=0.00, max=100.00, default=0.25,
        update=prop_update_supertorus
    )

    st_ring: FloatProperty(
        name="Ring",
        description="Ring manipulator",
        min=0.0001, max=100.00, default=1.00,
        update=prop_update_supertorus
    )

    st_cross: FloatProperty(
        name="Cross",
        description="Cross manipulator",
        min=0.0001, max=100.00, default=1.00,
        update=prop_update_supertorus
    )

    st_accuracy: FloatProperty(
        name="Accuracy",
        description="Supertorus accuracy",
        min=0.00001, max=1.00, default=0.001
    )

    st_max_gradient: FloatProperty(
        name="Gradient",
        description="Max gradient",
        min=0.0001, max=100.00, default=10.00,
        update=prop_update_supertorus
    )

    st_R: FloatProperty(
        name = "big radius",
        description = "The radius inside the tube",
        default = 1.0, min = 0.01, max = 100.0,
        update=prop_update_supertorus
    )

    st_r: FloatProperty(
        name = "small radius",
        description = "The radius of the tube",
        default = 0.3, min = 0.01, max = 100.0,
        update=prop_update_supertorus
    )

    st_u: IntProperty(
        name = "U-segments",
        description = "radial segmentation",
        default = 16, min = 3, max = 265,
        update=prop_update_supertorus
    )

    st_v: IntProperty(
        name = "V-segments",
        description = "lateral segmentation",
        default = 8, min = 3, max = 265,
        update=prop_update_supertorus
    )

    st_n1: FloatProperty(
        name = "Ring manipulator",
        description = "Manipulates the shape of the Ring",
        default = 1.0, min = 0.01, max = 100.0,
        update=prop_update_supertorus
    )

    st_n2: FloatProperty(
        name = "Cross manipulator",
        description = "Manipulates the shape of the cross-section",
        default = 1.0, min = 0.01, max = 100.0,
        update=prop_update_supertorus
    )

    st_ie: BoolProperty(
        name = "Use Int.+Ext. radii",
        description = "Use internal and external radii",
        default = False,
        update=prop_update_supertorus
    )

    st_edit: BoolProperty(
        name="",
        description="",
        default=False,
        options={'HIDDEN'},
        update=prop_update_supertorus
    )

    ########################Loft
    loft_n: IntProperty(
        name = "Segments",
        description = "Vertical segments",
        default = 16, min = 3, max = 720
    )

    loft_rings_bottom: IntProperty(
        name = "Bottom",
        description = "Bottom rings",
        default = 5, min = 2, max = 100
    )

    loft_rings_side: IntProperty(
        name = "Side",
        description = "Side rings",
        default = 10, min = 2, max = 100
    )

    loft_thick: FloatProperty(
        name = "Thickness",
        description = "Manipulates the shape of the Ring",
        default = 0.3, min = 0.01, max = 1.0
    )

    loft_r: FloatProperty(
        name = "Radius",
        description = "Radius",
        default = 1, min = 0.01, max = 10
    )

    loft_height: FloatProperty(
        name = "Height",
        description = "Manipulates the shape of the Ring",
        default = 2, min = 0.01, max = 10.0
    )

    ###################Prism
    prism_n: IntProperty(
        name = "Sides",
        description = "Number of sides",
        default = 5, min = 3, max = 720
    )

    prism_r: FloatProperty(
        name = "Radius",
        description = "Radius",
        default = 1.0
    )

    ##################Isosurface
    iso_function_text: StringProperty(
        name="Function Text",
        maxlen=1024
    ) #,update=iso_props_update_callback)

    ##################PolygonToCircle
    polytocircle_resolution: IntProperty(
        name = "Resolution",
        description = "",
        default = 3, min = 0, max = 256
    )

    polytocircle_ngon: IntProperty(
        name = "NGon",
        description = "",
        min = 3, max = 64,default = 5
    )

    polytocircle_ngonR: FloatProperty(
        name = "NGon Radius",
        description = "",
        default = 0.3
    )

    polytocircle_circleR: FloatProperty(
        name = "Circle Radius",
        description = "",
        default = 1.0
    )


###############################################################################
# Modifiers POV properties.
###############################################################################
# class RenderPovSettingsModifier(PropertyGroup):
    boolean_mod: EnumProperty(
        name="Operation",
        description="Choose the type of calculation for Boolean modifier",
        items=(
            ("BMESH", "Use the BMesh Boolean Solver", ""),
            ("CARVE", "Use the Carve Boolean Solver", ""),
            ("POV", "Use POV Constructive Solid Geometry", "")
        ),
        default="BMESH",
    )

    #################Avogadro
    # filename_ext = ".png"

    # filter_glob = StringProperty(
            # default="*.exr;*.gif;*.hdr;*.iff;*.jpeg;*.jpg;*.pgm;*.png;*.pot;*.ppm;*.sys;*.tga;*.tiff;*.EXR;*.GIF;*.HDR;*.IFF;*.JPEG;*.JPG;*.PGM;*.PNG;*.POT;*.PPM;*.SYS;*.TGA;*.TIFF",
            # options={'HIDDEN'},
            # )

###############################################################################
# Camera POV properties.
###############################################################################
class RenderPovSettingsCamera(PropertyGroup):

    """Declare camera properties controllable in UI and translated to POV."""

    # DOF Toggle
    dof_enable: BoolProperty(
        name="Depth Of Field",
        description="Enable POV Depth Of Field ",
        default=False,
    )

    # Aperture (Intensity of the Blur)
    dof_aperture: FloatProperty(
        name="Aperture",
        description="Similar to a real camera's aperture effect over focal blur (though not "
        "in physical units and independent of focal length). "
        "Increase to get more blur",
        min=0.01, max=1.00, default=0.50
    )

    # Aperture adaptive sampling
    dof_samples_min: IntProperty(
        name="Samples Min",
        description="Minimum number of rays to use for each pixel",
        min=1, max=128, default=3
    )

    dof_samples_max: IntProperty(
        name="Samples Max",
        description="Maximum number of rays to use for each pixel",
        min=1, max=128, default=9
    )

    dof_variance: IntProperty(
        name="Variance",
        description="Minimum threshold (fractional value) for adaptive DOF sampling (up "
        "increases quality and render time). The value for the variance should "
        "be in the range of the smallest displayable color difference",
        min=1, max=100000, soft_max=10000, default=8192
    )

    dof_confidence: FloatProperty(
        name="Confidence",
        description="Probability to reach the real color value. Larger confidence values "
        "will lead to more samples, slower traces and better images",
        min=0.01, max=0.99, default=0.20
    )

    normal_enable: BoolProperty(
        name="Perturbated Camera",
        default=False,
    )

    cam_normal: FloatProperty(
        name="Normal Strength",
        min=0.0,
        max=1.0,
        default=0.0,
    )

    normal_patterns: EnumProperty(
        name="Pattern",
        description="",
        items=(
            ('agate', "Agate", ""),
            ('boxed', "Boxed", ""),
            ('bumps', "Bumps", ""),
            ('cells', "Cells", ""),
            ('crackle', "Crackle", ""),
            ('dents', "Dents", ""),
            ('granite', "Granite", ""),
            ('leopard', "Leopard", ""),
            ('marble', "Marble", ""),
            ('onion', "Onion", ""),
            ('pavement', "Pavement", ""),
            ('planar', "Planar", ""),
            ('quilted', "Quilted", ""),
            ('ripples', "Ripples", ""),
            ('radial', "Radial", ""),
            ('spherical', "Spherical", ""),
            ('spiral1', "Spiral1", ""),
            ('spiral2', "Spiral2", ""),
            ('spotted', "Spotted", ""),
            ('square', "Square", ""),
            ('tiling', "Tiling", ""),
            ('waves', "Waves", ""),
            ('wood', "Wood", ""),
            ('wrinkles', "Wrinkles", "")
        ),
        default='agate',
    )

    turbulence: FloatProperty(name="Turbulence", min=0.0, max=100.0, default=0.1)

    scale: FloatProperty(name="Scale", min=0.0,default=1.0)

    ##################################CustomPOV Code############################
    # Only DUMMIES below for now:
    replacement_text: StringProperty(
        name="Texts in blend file",
        description="Type the declared name in custom POV code or an external .inc "
        "it points at. camera {} expected",
        default="",
    )
###############################################################################
# Light POV properties.
###############################################################################
class RenderPovSettingsLight(PropertyGroup):

    """Declare light properties controllable in UI and translated to POV."""

    # former Space properties from  removed Blender Internal
    use_limited_texture_context: BoolProperty(
        name="",
        description="Use the limited version of texture user (for ‘old shading’ mode)",
        default=True,
    )

    texture_context: EnumProperty(
        name="Texture context",
        description="Type of texture data to display and edit",
        items=(
            ('MATERIAL', "", "Show material textures", "MATERIAL",0), # "Show material textures"
            ('WORLD', "", "Show world textures", "WORLD",1), # "Show world textures"
            ('LAMP', "", "Show lamp textures", "LIGHT",2), # "Show lamp textures"
            ('PARTICLES', "", "Show particles textures", "PARTICLES",3), # "Show particles textures"
            ('LINESTYLE', "", "Show linestyle textures", "LINE_DATA",4), # "Show linestyle textures"
            ('OTHER', "", "Show other data textures", "TEXTURE_DATA",5), # "Show other data textures"
        ),
        default = 'MATERIAL',
    )

    shadow_method: EnumProperty(
        name="Shadow",
        description="",
        items=(("NOSHADOW", "No Shadow", "No Shadow"),
               ("RAY_SHADOW", "Ray Shadow", "Ray Shadow, Use ray tracing for shadow")),
        default="RAY_SHADOW",
    )

    active_texture_index: IntProperty(
        name = "Index for texture_slots",
        default = 0
    )

    use_halo: BoolProperty(
        name="Halo",
        description="Render spotlight with a volumetric halo",
        default=False,
    )

    halo_intensity: FloatProperty(
        name="Halo intensity",
        description="Brightness of the spotlight halo cone",
        soft_min=0.0, soft_max=1.0, default=1.0
    )

    shadow_ray_samples_x: IntProperty(
        name = "Number of samples taken extra (samples x samples)",
        min=1, soft_max=64,
        default = 1,
    )

    shadow_ray_samples_y: IntProperty(
        name = "Number of samples taken extra (samples x samples)",
        min=1, soft_max=64,
        default = 1,
    )

    shadow_ray_sample_method: EnumProperty(
        name="",
        description="Method for generating shadow samples: Adaptive QMC is fastest, Constant QMC is less noisy but slower",
        items=(
            ('ADAPTIVE_QMC', "", "Halton samples distribution", "",0),
            ('CONSTANT_QMC', "", "QMC samples distribution", "",1),
            ('CONSTANT_JITTERED', "", "Uses POV jitter keyword", "",2) # "Show other data textures"
        ),
        default = 'CONSTANT_JITTERED',
    )

    use_jitter: BoolProperty(
        name="Jitter",
        description="Use noise for sampling (Constant Jittered sampling)",
        default=False,
    )

###############################################################################
# World POV properties.
###############################################################################
class RenderPovSettingsWorld(PropertyGroup):

    """Declare world properties controllable in UI and translated to POV."""

    # former Space properties from  removed Blender Internal
    use_limited_texture_context: BoolProperty(
        name="",
        description="Use the limited version of texture user (for ‘old shading’ mode)",
        default=True,
    )

    texture_context: EnumProperty(
        name="Texture context",
        description="Type of texture data to display and edit",
        items=(
            ('MATERIAL', "", "Show material textures", "MATERIAL",0), # "Show material textures"
            ('WORLD', "", "Show world textures", "WORLD",1), # "Show world textures"
            ('LAMP', "", "Show lamp textures", "LIGHT",2), # "Show lamp textures"
            ('PARTICLES', "", "Show particles textures", "PARTICLES",3), # "Show particles textures"
            ('LINESTYLE', "", "Show linestyle textures", "LINE_DATA",4), # "Show linestyle textures"
            ('OTHER', "", "Show other data textures", "TEXTURE_DATA",5), # "Show other data textures"
        ),
        default = 'MATERIAL',
    )

    use_sky_blend: BoolProperty(
        name="Blend Sky",
        description="Render background with natural progression from horizon to zenith",
        default=False,
    )

    use_sky_paper: BoolProperty(
        name="Paper Sky",
        description="Flatten blend or texture coordinates",
        default=False,
    )

    use_sky_real: BoolProperty(
        name="Real Sky",
        description="Render background with a real horizon, relative to the camera angle",
        default=False,
    )

    horizon_color: FloatVectorProperty(
        name="Horizon Color",
        description="Color at the horizon",
        precision=4, step=0.01, min=0, soft_max=1,
        default=(0.0, 0.0, 0.0), options={'ANIMATABLE'}, subtype='COLOR',
    )

    zenith_color: FloatVectorProperty(
        name="Zenith Color",
        description="Color at the zenith",
        precision=4, step=0.01, min=0, soft_max=1,
        default=(0.0, 0.0, 0.0), options={'ANIMATABLE'}, subtype='COLOR',
    )

    ambient_color: FloatVectorProperty(
        name="Ambient Color",
        description="Ambient color of the world",
        precision=4, step=0.01, min=0, soft_max=1,
        default=(0.0, 0.0, 0.0), options={'ANIMATABLE'}, subtype='COLOR',
    )
    active_texture_index: IntProperty(
        name = "Index for texture_slots",
        default = 0
    )


class WorldTextureSlot(PropertyGroup):
    """Declare world texture slot properties controllable in UI and translated to POV."""

    blend_factor: FloatProperty(
        name="Blend",
        description="Amount texture affects color progression of the "
        "background",
        soft_min=0.0, soft_max=1.0, default=1.0
    )

    horizon_factor: FloatProperty(
        name="Horizon",
        description="Amount texture affects color of the horizon",
        soft_min=0.0, soft_max=1.0, default=1.0,
    )

    object: StringProperty(
        name="Object",
        description="Object to use for mapping with Object texture coordinates",
        default="",
    )

    texture_coords: EnumProperty(
        name="Coordinates",
        description="Texture coordinates used to map the texture onto the background",
        items=(
            ("VIEW", "View", "Use view vector for the texture coordinates"),
            ("GLOBAL", "Global", "Use global coordinates for the texture coordinates (interior mist)"),
            ("ANGMAP", "AngMap", "Use 360 degree angular coordinates, e.g. for spherical light probes"),
            ("SPHERE", "Sphere", "For 360 degree panorama sky, spherical mapped, only top half"),
            ("EQUIRECT", "Equirectangular", "For 360 degree panorama sky, equirectangular mapping"),
            ("TUBE", "Tube", "For 360 degree panorama sky, cylindrical mapped, only top half"),
            ("OBJECT", "Object", "Use linked object’s coordinates for texture coordinates")
        ),
        default="VIEW",
    )

    use_map_blend: BoolProperty(
        name="Blend Map",
        description="Affect the color progression of the background",
        default=True,
    )

    use_map_horizon: BoolProperty(
        name="Horizon Map",
        description="Affect the color of the horizon",
        default=False,
    )

    use_map_zenith_down: BoolProperty(
        name="",
        description="Affect the color of the zenith below",
        default=False,
    )

    use_map_zenith_up: BoolProperty(
        name="Zenith Up Map",
        description="Affect the color of the zenith above",
        default=False,
    )

    zenith_down_factor: FloatProperty(
        name="Zenith Down",
        description="Amount texture affects color of the zenith below",
        soft_min=0.0, soft_max=1.0, default=1.0
    )

    zenith_up_factor: FloatProperty(
        name="Zenith Up",
        description="Amount texture affects color of the zenith above",
        soft_min=0.0, soft_max=1.0, default=1.0
    )

'''
# class WORLD_TEXTURE_SLOTS_UL_layerlist(bpy.types.UIList):
#    texture_slots:

class WorldTextureSlots(bpy.props.PropertyGroup):
    index = bpy.prop.PropertyInt(name='index')
    # foo  = random prop

bpy.types.World.texture_slots = bpy.props.CollectionProperty(type=PropertyGroup)

for i in range(18):  # length of world texture slots
    world.texture_slots.add()
'''

class MATERIAL_TEXTURE_SLOTS_UL_POV_layerlist(bpy.types.UIList):
    # texture_slots:
    index: bpy.props.IntProperty(name='index')
    # foo  = random prop
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        ob = data
        slot = item
        # ma = slot.name
        # draw_item must handle the three layout types... Usually 'DEFAULT' and 'COMPACT' can share the same code.
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            # You should always start your row layout by a label (icon + text), or a non-embossed text field,
            # this will also make the row easily selectable in the list! The later also enables ctrl-click rename.
            # We use icon_value of label, as our given icon is an integer value, not an enum ID.
            # Note "data" names should never be translated!
            if slot:
                layout.prop(item, "texture", text="", emboss=False, icon='TEXTURE')
            else:
                layout.label(text="New", translate=False, icon_value=icon)
        # 'GRID' layout type should be as compact as possible (typically a single icon!).
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon_value=icon)


###############################################################################
# Text POV properties.
###############################################################################


class RenderPovSettingsText(PropertyGroup):

    """Declare text properties to use UI as an IDE or render text snippets to POV."""

    custom_code: EnumProperty(
        name="Custom Code",
        description="rendered source: Both adds text at the "
        "top of the exported POV file",
        items=(
            ("3dview", "View", ""),
            ("text", "Text", ""),
            ("both", "Both", "")
        ),
        default="text",
    )

###############################################################################
# Povray Preferences.
###############################################################################


class PovrayPreferences(AddonPreferences):

    """Declare preference variables to set up POV binary."""

    bl_idname = __name__

    branch_feature_set_povray: EnumProperty(
        name="Feature Set",
        description="Choose between official (POV-Ray) or (UberPOV) "
        "development branch features to write in the pov file",
        items= (
            ('povray', 'Official POV-Ray', '','PLUGIN', 0),
            ('uberpov', 'Unofficial UberPOV', '', 'PLUGIN', 1)
        ),
        default='povray',
    )

    filepath_povray: StringProperty(
        name="Binary Location",
        description="Path to renderer executable",
        subtype='FILE_PATH',
    )

    docpath_povray: StringProperty(
        name="Includes Location",
        description="Path to Insert Menu files",
        subtype='FILE_PATH',
    )

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "branch_feature_set_povray")
        layout.prop(self, "filepath_povray")
        layout.prop(self, "docpath_povray")


classes = (
    PovrayPreferences,
    RenderPovSettingsCamera,
    RenderPovSettingsLight,
    RenderPovSettingsWorld,
    MaterialTextureSlot,
    WorldTextureSlot,
    RenderPovSettingsMaterial,
    MaterialRaytraceTransparency,
    MaterialRaytraceMirror,
    MaterialSubsurfaceScattering,
    MaterialStrandSettings,
    RenderPovSettingsObject,
    RenderPovSettingsScene,
    RenderPovSettingsText,
    RenderPovSettingsTexture,
)


def register():

    # bpy.utils.register_module(__name__) # DEPRECATED Now imported from bpy.utils import register_class

    for cls in classes:
        register_class(cls)

    render.register()
    ui.register()
    primitives.register()
    nodes.register()

    '''
        bpy.types.VIEW3D_MT_add.prepend(ui.menu_func_add)
        bpy.types.TOPBAR_MT_file_import.append(ui.menu_func_import)
        bpy.types.TEXT_MT_templates.append(ui.menu_func_templates)
        bpy.types.RENDER_PT_POV_radiosity.prepend(ui.rad_panel_func)
        bpy.types.LIGHT_PT_POV_light.prepend(ui.light_panel_func)
        bpy.types.WORLD_PT_world.prepend(ui.world_panel_func)
        # was used for parametric objects but made the other addon unreachable on
        # unregister for other tools to use created a user action call instead
        # addon_utils.enable("add_mesh_extra_objects", default_set=False, persistent=True)

        # bpy.types.TEXTURE_PT_context_texture.prepend(TEXTURE_PT_povray_type)
    '''
    bpy.types.NODE_HT_header.append(ui.menu_func_nodes)
    nodeitems_utils.register_node_categories("POVRAYNODES", node_categories)
    bpy.types.Scene.pov = PointerProperty(type=RenderPovSettingsScene)
    # bpy.types.Modifier.pov = PointerProperty(type=RenderPovSettingsModifier)
    bpy.types.Material.pov_raytrace_transparency = PointerProperty(type=MaterialRaytraceTransparency)
    bpy.types.Material.pov = PointerProperty(type=RenderPovSettingsMaterial)
    bpy.types.Material.pov_subsurface_scattering = PointerProperty(type=MaterialSubsurfaceScattering)
    bpy.types.Material.strand = PointerProperty(type=MaterialStrandSettings)
    bpy.types.Material.pov_raytrace_mirror = PointerProperty(type=MaterialRaytraceMirror)
    bpy.types.Texture.pov = PointerProperty(type=RenderPovSettingsTexture)
    bpy.types.Object.pov = PointerProperty(type=RenderPovSettingsObject)
    bpy.types.Camera.pov = PointerProperty(type=RenderPovSettingsCamera)
    bpy.types.Light.pov = PointerProperty(type=RenderPovSettingsLight)
    bpy.types.World.pov = PointerProperty(type=RenderPovSettingsWorld)
    bpy.types.Material.pov_texture_slots = CollectionProperty(type=MaterialTextureSlot)
    bpy.types.World.texture_slots = CollectionProperty(type=WorldTextureSlot)
    bpy.types.Text.pov = PointerProperty(type=RenderPovSettingsText)


def unregister():
    del bpy.types.Scene.pov
    del bpy.types.Material.pov
    del bpy.types.Material.pov_subsurface_scattering
    del bpy.types.Material.strand
    del bpy.types.Material.pov_raytrace_mirror
    del bpy.types.Material.pov_raytrace_transparency
    # del bpy.types.Modifier.pov
    del bpy.types.Texture.pov
    del bpy.types.Object.pov
    del bpy.types.Camera.pov
    del bpy.types.Light.pov
    del bpy.types.World.pov
    del bpy.types.Material.pov_texture_slots
    del bpy.types.Text.pov

    nodeitems_utils.unregister_node_categories("POVRAYNODES")
    bpy.types.NODE_HT_header.remove(ui.menu_func_nodes)
    '''
    # bpy.types.TEXTURE_PT_context_texture.remove(TEXTURE_PT_povray_type)
    # addon_utils.disable("add_mesh_extra_objects", default_set=False)
    bpy.types.WORLD_PT_POV_world.remove(ui.world_panel_func)
    bpy.types.LIGHT_PT_POV_light.remove(ui.light_panel_func)
    bpy.types.RENDER_PT_POV_radiosity.remove(ui.rad_panel_func)
    bpy.types.TEXT_MT_templates.remove(ui.menu_func_templates)
    bpy.types.TOPBAR_MT_file_import.remove(ui.menu_func_import)
    bpy.types.VIEW3D_MT_add.remove(ui.menu_func_add)
    '''
    # bpy.utils.unregister_module(__name__)

    nodes.unregister()
    primitives.unregister()
    ui.unregister()
    render.unregister()

    for cls in reversed(classes):
        unregister_class(cls)



if __name__ == "__main__":
    register()

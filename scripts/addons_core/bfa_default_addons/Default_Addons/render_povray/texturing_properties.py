# SPDX-FileCopyrightText: 2021-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""Declare texturing properties controllable in UI."""

import bpy
from bpy.utils import register_class, unregister_class
from bpy.types import PropertyGroup
from bpy.props import (
    FloatVectorProperty,
    StringProperty,
    BoolProperty,
    IntProperty,
    FloatProperty,
    EnumProperty,
    PointerProperty,
    CollectionProperty,
)

from .shading_properties import active_texture_name_from_uilist, active_texture_name_from_search

# ---------------------------------------------------------------- #
# Texture slots (Material context) exported as POV texture properties.
# ---------------------------------------------------------------- #


class MaterialTextureSlot(PropertyGroup):
    """Declare material texture slot level properties for UI and translated to POV."""

    bl_idname = ("pov_texture_slots",)
    bl_description = ("Nodeless texture slots",)

    # Adding a "real" texture datablock as property is not possible
    # (or at least not easy through a dynamically populated EnumProperty).
    # That's why we'll use a prop_search() UILayout function in texturing_gui.py.
    # So we'll assign the name of the needed texture datablock to the below StringProperty.
    texture: StringProperty(update=active_texture_name_from_uilist)
    # and use another temporary StringProperty to change the linked data
    texture_search: StringProperty(
        name="", update=active_texture_name_from_search, description="Browse Texture to be linked"
    )

    alpha_factor: FloatProperty(
        name="Alpha", description="Amount texture affects alpha", default=1.0
    )

    ambient_factor: FloatProperty(
        name="", description="Amount texture affects ambient", default=1.0
    )

    bump_method: EnumProperty(
        name="",
        description="Method to use for bump mapping",
        items=(
            ("BUMP_ORIGINAL", "Bump Original", ""),
            ("BUMP_COMPATIBLE", "Bump Compatible", ""),
            ("BUMP_DEFAULT", "Bump Default", ""),
            ("BUMP_BEST_QUALITY", "Bump Best Quality", ""),
        ),
        default="BUMP_ORIGINAL",
    )

    bump_objectspace: EnumProperty(
        name="",
        description="Space to apply bump mapping in",
        items=(
            ("BUMP_VIEWSPACE", "Bump Viewspace", ""),
            ("BUMP_OBJECTSPACE", "Bump Objectspace", ""),
            ("BUMP_TEXTURESPACE", "Bump Texturespace", ""),
        ),
        default="BUMP_VIEWSPACE",
    )

    density_factor: FloatProperty(
        name="", description="Amount texture affects density", default=1.0
    )

    diffuse_color_factor: FloatProperty(
        name="", description="Amount texture affects diffuse color", default=1.0
    )

    diffuse_factor: FloatProperty(
        name="", description="Amount texture affects diffuse reflectivity", default=1.0
    )

    displacement_factor: FloatProperty(
        name="", description="Amount texture displaces the surface", default=0.2
    )

    emission_color_factor: FloatProperty(
        name="", description="Amount texture affects emission color", default=1.0
    )

    emission_factor: FloatProperty(
        name="", description="Amount texture affects emission", default=1.0
    )

    emit_factor: FloatProperty(name="", description="Amount texture affects emission", default=1.0)

    hardness_factor: FloatProperty(
        name="", description="Amount texture affects hardness", default=1.0
    )

    mapping: EnumProperty(
        name="",
        description="",
        items=(
            ("FLAT", "Flat", ""),
            ("CUBE", "Cube", ""),
            ("TUBE", "Tube", ""),
            ("SPHERE", "Sphere", ""),
        ),
        default="FLAT",
    )

    mapping_x: EnumProperty(
        name="",
        description="",
        items=(("NONE", "", ""), ("X", "", ""), ("Y", "", ""), ("Z", "", "")),
        default="NONE",
    )

    mapping_y: EnumProperty(
        name="",
        description="",
        items=(("NONE", "", ""), ("X", "", ""), ("Y", "", ""), ("Z", "", "")),
        default="NONE",
    )

    mapping_z: EnumProperty(
        name="",
        description="",
        items=(("NONE", "", ""), ("X", "", ""), ("Y", "", ""), ("Z", "", "")),
        default="NONE",
    )

    mirror_factor: FloatProperty(
        name="", description="Amount texture affects mirror color", default=1.0
    )

    normal_factor: FloatProperty(
        name="", description="Amount texture affects normal values", default=1.0
    )

    normal_map_space: EnumProperty(
        name="",
        description="Sets space of normal map image",
        items=(
            ("CAMERA", "Camera", ""),
            ("WORLD", "World", ""),
            ("OBJECT", "Object", ""),
            ("TANGENT", "Tangent", ""),
        ),
        default="CAMERA",
    )

    object: StringProperty(
        name="Object",
        description="Object to use for mapping with Object texture coordinates",
        default="",
    )

    raymir_factor: FloatProperty(
        name="", description="Amount texture affects ray mirror", default=1.0
    )

    reflection_color_factor: FloatProperty(
        name="", description="Amount texture affects color of out-scattered light", default=1.0
    )

    reflection_factor: FloatProperty(
        name="", description="Amount texture affects brightness of out-scattered light", default=1.0
    )

    scattering_factor: FloatProperty(
        name="", description="Amount texture affects scattering", default=1.0
    )

    specular_color_factor: FloatProperty(
        name="", description="Amount texture affects specular color", default=1.0
    )

    specular_factor: FloatProperty(
        name="", description="Amount texture affects specular reflectivity", default=1.0
    )

    offset: FloatVectorProperty(
        name="Offset",
        description="Fine tune of the texture mapping X, Y and Z locations ",
        precision=4,
        step=0.1,
        soft_min=-100.0,
        soft_max=100.0,
        default=(0.0, 0.0, 0.0),
        options={"ANIMATABLE"},
        subtype="TRANSLATION",
    )

    scale: FloatVectorProperty(
        name="Size",
        subtype="XYZ",
        size=3,
        description="Set scaling for the texture’s X, Y and Z sizes ",
        precision=4,
        step=0.1,
        soft_min=-100.0,
        soft_max=100.0,
        default=(1.0, 1.0, 1.0),
        options={"ANIMATABLE"},
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
            ("TANGENT", "Tangent", ""),
        ),
        default="GLOBAL",
    )

    translucency_factor: FloatProperty(
        name="", description="Amount texture affects translucency", default=1.0
    )

    transmission_color_factor: FloatProperty(
        name="",
        description="Amount texture affects result color after light has been scattered/absorbed",
        default=1.0,
    )

    use: BoolProperty(name="", description="Enable this material texture slot", default=True)

    use_from_dupli: BoolProperty(
        name="",
        description="Dupli’s instanced from verts, faces or particles, "
        "inherit texture coordinate from their parent",
        default=False,
    )

    use_from_original: BoolProperty(
        name="",
        description="Dupli’s derive their object coordinates from the "
        "original objects transformation",
        default=False,
    )

    use_interpolation: BoolProperty(
        name="", description="Interpolates pixels using selected filter ", default=False
    )

    use_map_alpha: BoolProperty(
        name="", description="Causes the texture to affect the alpha value", default=False
    )

    use_map_ambient: BoolProperty(
        name="", description="Causes the texture to affect the value of ambient", default=False
    )

    use_map_color_diffuse: BoolProperty(
        name="",
        description="Causes the texture to affect basic color of the material",
        default=True,
    )

    use_map_color_emission: BoolProperty(
        name="", description="Causes the texture to affect the color of emission", default=False
    )

    use_map_color_reflection: BoolProperty(
        name="",
        description="Causes the texture to affect the color of scattered light",
        default=False,
    )

    use_map_color_spec: BoolProperty(
        name="", description="Causes the texture to affect the specularity color", default=False
    )

    use_map_color_transmission: BoolProperty(
        name="",
        description="Causes the texture to affect the result color after "
        "other light has been scattered/absorbed",
        default=False,
    )

    use_map_density: BoolProperty(
        name="", description="Causes the texture to affect the volume’s density", default=False
    )

    use_map_diffuse: BoolProperty(
        name="",
        description="Causes the texture to affect the value of the materials diffuse reflectivity",
        default=False,
    )

    use_map_displacement: BoolProperty(
        name="", description="Let the texture displace the surface", default=False
    )

    use_map_emission: BoolProperty(
        name="", description="Causes the texture to affect the volume’s emission", default=False
    )

    use_map_emit: BoolProperty(
        name="", description="Causes the texture to affect the emit value", default=False
    )

    use_map_hardness: BoolProperty(
        name="", description="Causes the texture to affect the hardness value", default=False
    )

    use_map_mirror: BoolProperty(
        name="", description="Causes the texture to affect the mirror color", default=False
    )

    use_map_normal: BoolProperty(
        name="", description="Causes the texture to affect the rendered normal", default=False
    )

    use_map_raymir: BoolProperty(
        name="", description="Causes the texture to affect the ray-mirror value", default=False
    )

    use_map_reflect: BoolProperty(
        name="",
        description="Causes the texture to affect the reflected light’s brightness",
        default=False,
    )

    use_map_scatter: BoolProperty(
        name="", description="Causes the texture to affect the volume’s scattering", default=False
    )

    use_map_specular: BoolProperty(
        name="",
        description="Causes the texture to affect the value of specular reflectivity",
        default=False,
    )

    use_map_translucency: BoolProperty(
        name="", description="Causes the texture to affect the translucency value", default=False
    )

    use_map_warp: BoolProperty(
        name="",
        description="Let the texture warp texture coordinates of next channels",
        default=False,
    )

    uv_layer: StringProperty(
        name="", description="UV layer to use for mapping with UV texture coordinates", default=""
    )

    warp_factor: FloatProperty(
        name="",
        description="Amount texture affects texture coordinates of next channels",
        default=0.0,
    )
    # ---------------------------------------------------------------- #
    # so that its for loop stays one level less nested
    # used_texture_slots generator expression requires :
    def __iter__(self):
        return self
    def __next__(self):
        tex = bpy.data.textures[self.texture]
        while tex.pov.active_texture_index < len(bpy.data.textures): # XXX should use slots count
            tex.pov.active_texture_index += 1
        raise StopIteration
    # ---------------------------------------------------------------- #

# ---------------------------------------------------------------- #
# Texture slots (World context) exported as POV texture properties.
# ---------------------------------------------------------------- #
class WorldTextureSlot(PropertyGroup):
    """Declare world texture slot level properties for UI and translated to POV."""

    bl_idname = ("pov_texture_slots",)
    bl_description = ("Texture_slots from Blender-2.79",)

    # Adding a "real" texture datablock as property is not possible
    # (or at least not easy through a dynamically populated EnumProperty).
    # That's why we'll use a prop_search() UILayout function in ui.py.
    # So we'll assign the name of the needed texture datablock to the below StringProperty.
    texture: StringProperty(update=active_texture_name_from_uilist)
    # and use another temporary StringProperty to change the linked data
    texture_search: StringProperty(
        name="", update=active_texture_name_from_search, description="Browse Texture to be linked"
    )

    blend_factor: FloatProperty(
        name="Blend",
        description="Amount texture affects color progression of the " "background",
        soft_min=0.0,
        soft_max=1.0,
        default=1.0,
    )

    horizon_factor: FloatProperty(
        name="Horizon",
        description="Amount texture affects color of the horizon",
        soft_min=0.0,
        soft_max=1.0,
        default=1.0,
    )

    object: StringProperty(
        name="Object",
        description="Object to use for mapping with Object texture coordinates",
        default="",
    )

    offset: FloatVectorProperty(
        name="Offset",
        description="Fine tune of the texture mapping X, Y and Z locations ",
        precision=4,
        step=0.1,
        soft_min=-100.0,
        soft_max=100.0,
        default=(0.0, 0.0, 0.0),
        options={"ANIMATABLE"},
        subtype="TRANSLATION",
    )

    scale: FloatVectorProperty(
        name="Size",
        subtype="XYZ",
        size=3,
        description="Set scaling for the texture’s X, Y and Z sizes ",
        precision=4,
        step=0.1,
        soft_min=-100.0,
        soft_max=100.0,
        default=(1.0, 1.0, 1.0),
        options={"ANIMATABLE"},
    )

    texture_coords: EnumProperty(
        name="Coordinates",
        description="Texture coordinates used to map the texture onto the background",
        items=(
            ("VIEW", "View", "Use view vector for the texture coordinates"),
            (
                "GLOBAL",
                "Global",
                "Use global coordinates for the texture coordinates (interior mist)",
            ),
            (
                "ANGMAP",
                "AngMap",
                "Use 360 degree angular coordinates, e.g. for spherical light probes",
            ),
            ("SPHERE", "Sphere", "For 360 degree panorama sky, spherical mapped, only top half"),
            ("EQUIRECT", "Equirectangular", "For 360 degree panorama sky, equirectangular mapping"),
            ("TUBE", "Tube", "For 360 degree panorama sky, cylindrical mapped, only top half"),
            ("OBJECT", "Object", "Use linked object’s coordinates for texture coordinates"),
        ),
        default="VIEW",
    )

    use_map_blend: BoolProperty(
        name="Blend Map", description="Affect the color progression of the background", default=True
    )

    use_map_horizon: BoolProperty(
        name="Horizon Map", description="Affect the color of the horizon", default=False
    )

    use_map_zenith_down: BoolProperty(
        name="", description="Affect the color of the zenith below", default=False
    )

    use_map_zenith_up: BoolProperty(
        name="Zenith Up Map", description="Affect the color of the zenith above", default=False
    )

    zenith_down_factor: FloatProperty(
        name="Zenith Down",
        description="Amount texture affects color of the zenith below",
        soft_min=0.0,
        soft_max=1.0,
        default=1.0,
    )

    zenith_up_factor: FloatProperty(
        name="Zenith Up",
        description="Amount texture affects color of the zenith above",
        soft_min=0.0,
        soft_max=1.0,
        default=1.0,
    )


# ---------------------------------------------------------------- #
# Space properties from  removed former Blender Internal
# ---------------------------------------------------------------- #

# added below at superclass level so as to be available in World, Material,
# and Light, for texture slots use

bpy.types.ID.use_limited_texture_context = BoolProperty(
    name="",
    description="Use the limited version of texture user (for ‘old shading’ mode)",
    default=True,
)
bpy.types.ID.texture_context = EnumProperty(
    name="Texture context",
    description="Type of texture data to display and edit",
    items=(
        ("MATERIAL", "", "Show material textures", "MATERIAL", 0),  # "Show material textures"
        ("WORLD", "", "Show world textures", "WORLD", 1),  # "Show world textures"
        ("LIGHT", "", "Show lamp textures", "LIGHT", 2),  # "Show lamp textures"
        ("PARTICLES", "", "Show particles textures", "PARTICLES", 3),  # "Show particles textures"
        ("LINESTYLE", "", "Show linestyle textures", "LINE_DATA", 4),  # "Show linestyle textures"
        ("OTHER", "", "Show other data textures", "TEXTURE_DATA", 5),  # "Show other data textures"
    ),
    default="MATERIAL",
)
# bpy.types.ID.active_texture_index = IntProperty(
# name = "Index for texture_slots",
# default = 0,
# )


# ---------------------------------------------------------------- #
# Texture POV properties.
# ---------------------------------------------------------------- #


class RenderPovSettingsTexture(PropertyGroup):
    """Declare texture level properties controllable in UI and translated to POV."""

    # former Space properties from removed Blender Internal
    active_texture_index: IntProperty(name="Index for texture_slots", min=0, max=17, default=0)

    use_limited_texture_context: BoolProperty(
        name="",
        description="Use the limited version of texture user (for ‘old shading’ mode)",
        default=True,
    )

    texture_context: EnumProperty(
        name="Texture context",
        description="Type of texture data to display and edit",
        items=(
            ("MATERIAL", "", "Show material textures", "MATERIAL", 0),  # "Show material textures"
            ("WORLD", "", "Show world textures", "WORLD", 1),  # "Show world textures"
            ("LAMP", "", "Show lamp textures", "LIGHT", 2),  # "Show lamp textures"
            (
                "PARTICLES",
                "",
                "Show particles textures",
                "PARTICLES",
                3,
            ),  # "Show particles textures"
            (
                "LINESTYLE",
                "",
                "Show linestyle textures",
                "LINE_DATA",
                4,
            ),  # "Show linestyle textures"
            (
                "OTHER",
                "",
                "Show other data textures",
                "TEXTURE_DATA",
                5,
            ),  # "Show other data textures"
        ),
        default="MATERIAL",
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
        min=0.45,
        max=5.00,
        soft_min=1.00,
        soft_max=2.50,
        default=1.00,
    )

    # ----------------------------------- CustomPOV Code ----------------------------------- #
    # commented out below if we wanted custom pov code in texture only, inside exported material:
    # replacement_text = StringProperty(
    #        name="Declared name:",
    #        description="Type the declared name in custom POV code or an external .inc "
    #                    "it points at. pigment {} expected",
    #        default="")

    tex_pattern_type: EnumProperty(
        name="Texture_Type",
        description="Choose between Blender or POV parameters to specify texture",
        items=(
            ("agate", "Agate", "", "PLUGIN", 0),
            ("aoi", "Aoi", "", "PLUGIN", 1),
            ("average", "Average", "", "PLUGIN", 2),
            ("boxed", "Boxed", "", "PLUGIN", 3),
            ("bozo", "Bozo", "", "PLUGIN", 4),
            ("bumps", "Bumps", "", "PLUGIN", 5),
            ("cells", "Cells", "", "PLUGIN", 6),
            ("crackle", "Crackle", "", "PLUGIN", 7),
            ("cubic", "Cubic", "", "PLUGIN", 8),
            ("cylindrical", "Cylindrical", "", "PLUGIN", 9),
            ("density_file", "Density", "(.df3)", "PLUGIN", 10),
            ("dents", "Dents", "", "PLUGIN", 11),
            ("fractal", "Fractal", "", "PLUGIN", 12),
            ("function", "Function", "", "PLUGIN", 13),
            ("gradient", "Gradient", "", "PLUGIN", 14),
            ("granite", "Granite", "", "PLUGIN", 15),
            ("image_pattern", "Image pattern", "", "PLUGIN", 16),
            ("leopard", "Leopard", "", "PLUGIN", 17),
            ("marble", "Marble", "", "PLUGIN", 18),
            ("onion", "Onion", "", "PLUGIN", 19),
            ("pigment_pattern", "pigment pattern", "", "PLUGIN", 20),
            ("planar", "Planar", "", "PLUGIN", 21),
            ("quilted", "Quilted", "", "PLUGIN", 22),
            ("radial", "Radial", "", "PLUGIN", 23),
            ("ripples", "Ripples", "", "PLUGIN", 24),
            ("slope", "Slope", "", "PLUGIN", 25),
            ("spherical", "Spherical", "", "PLUGIN", 26),
            ("spiral1", "Spiral1", "", "PLUGIN", 27),
            ("spiral2", "Spiral2", "", "PLUGIN", 28),
            ("spotted", "Spotted", "", "PLUGIN", 29),
            ("waves", "Waves", "", "PLUGIN", 30),
            ("wood", "Wood", "", "PLUGIN", 31),
            ("wrinkles", "Wrinkles", "", "PLUGIN", 32),
            ("brick", "Brick", "", "PLUGIN", 33),
            ("checker", "Checker", "", "PLUGIN", 34),
            ("hexagon", "Hexagon", "", "PLUGIN", 35),
            ("object", "Mesh", "", "PLUGIN", 36),
            ("emulator", "Blender Type Emulator", "", "SCRIPTPLUGINS", 37),
        ),
        default="emulator",
    )

    magnet_style: EnumProperty(
        name="Magnet style",
        description="magnet or julia",
        items=(("mandel", "Mandelbrot", ""), ("julia", "Julia", "")),
        default="julia",
    )

    magnet_type: IntProperty(name="Magnet_type", description="1 or 2", min=1, max=2, default=2)

    warp_types: EnumProperty(
        name="Warp Types",
        description="Select the type of warp",
        items=(
            ("PLANAR", "Planar", ""),
            ("CUBIC", "Cubic", ""),
            ("SPHERICAL", "Spherical", ""),
            ("TOROIDAL", "Toroidal", ""),
            ("CYLINDRICAL", "Cylindrical", ""),
            ("NONE", "None", "No indentation"),
        ),
        default="NONE",
    )

    warp_orientation: EnumProperty(
        name="Warp Orientation",
        description="Select the orientation of warp",
        items=(("x", "X", ""), ("y", "Y", ""), ("z", "Z", "")),
        default="y",
    )

    wave_type: EnumProperty(
        name="Waves type",
        description="Select the type of waves",
        items=(
            ("ramp", "Ramp", ""),
            ("sine", "Sine", ""),
            ("scallop", "Scallop", ""),
            ("cubic", "Cubic", ""),
            ("poly", "Poly", ""),
            ("triangle", "Triangle", ""),
        ),
        default="ramp",
    )

    gen_noise: IntProperty(
        name="Noise Generators", description="Noise Generators", min=1, max=3, default=1
    )

    warp_dist_exp: FloatProperty(
        name="Distance exponent", description="Distance exponent", min=0.0, max=100.0, default=1.0
    )

    warp_tor_major_radius: FloatProperty(
        name="Major radius",
        description="Torus is distance from major radius",
        min=0.0,
        max=5.0,
        default=1.0,
    )

    warp_turbulence_x: FloatProperty(
        name="Turbulence X", description="Turbulence X", min=0.0, max=5.0, default=0.0
    )

    warp_turbulence_y: FloatProperty(
        name="Turbulence Y", description="Turbulence Y", min=0.0, max=5.0, default=0.0
    )

    warp_turbulence_z: FloatProperty(
        name="Turbulence Z", description="Turbulence Z", min=0.0, max=5.0, default=0.0
    )

    modifier_octaves: IntProperty(
        name="Turbulence octaves", description="Turbulence octaves", min=1, max=10, default=1
    )

    modifier_lambda: FloatProperty(
        name="Turbulence lambda", description="Turbulence lambda", min=0.0, max=5.0, default=1.00
    )

    modifier_omega: FloatProperty(
        name="Turbulence omega", description="Turbulence omega", min=0.0, max=10.0, default=1.00
    )

    modifier_phase: FloatProperty(
        name="Phase",
        description="The phase value causes the map entries to be shifted so that the map "
        "starts and ends at a different place",
        min=0.0,
        max=2.0,
        default=0.0,
    )

    modifier_frequency: FloatProperty(
        name="Frequency",
        description="The frequency keyword adjusts the number of times that a color map "
        "repeats over one cycle of a pattern",
        min=0.0,
        max=25.0,
        default=2.0,
    )

    modifier_turbulence: FloatProperty(
        name="Turbulence", description="Turbulence", min=0.0, max=5.0, default=2.0
    )

    modifier_numbers: IntProperty(name="Numbers", description="Numbers", min=1, max=27, default=2)

    modifier_control0: IntProperty(
        name="Control0", description="Control0", min=0, max=100, default=1
    )

    modifier_control1: IntProperty(
        name="Control1", description="Control1", min=0, max=100, default=1
    )

    brick_size_x: FloatProperty(
        name="Brick size x", description="", min=0.0000, max=1.0000, default=0.2500
    )

    brick_size_y: FloatProperty(
        name="Brick size y", description="", min=0.0000, max=1.0000, default=0.0525
    )

    brick_size_z: FloatProperty(
        name="Brick size z", description="", min=0.0000, max=1.0000, default=0.1250
    )

    brick_mortar: FloatProperty(
        name="Mortar", description="Mortar", min=0.000, max=1.500, default=0.01
    )

    julia_complex_1: FloatProperty(
        name="Julia Complex 1", description="", min=0.000, max=1.500, default=0.360
    )

    julia_complex_2: FloatProperty(
        name="Julia Complex 2", description="", min=0.000, max=1.500, default=0.250
    )

    f_iter: IntProperty(name="Fractal Iteration", description="", min=0, max=100, default=20)

    f_exponent: IntProperty(name="Fractal Exponent", description="", min=2, max=33, default=2)

    f_ior: IntProperty(name="Fractal Interior", description="", min=1, max=6, default=1)

    f_ior_fac: FloatProperty(
        name="Fractal Interior Factor", description="", min=0.0, max=10.0, default=1.0
    )

    f_eor: IntProperty(name="Fractal Exterior", description="", min=1, max=8, default=1)

    f_eor_fac: FloatProperty(
        name="Fractal Exterior Factor", description="", min=0.0, max=10.0, default=1.0
    )

    grad_orient_x: IntProperty(
        name="Gradient orientation X", description="", min=0, max=1, default=0
    )

    grad_orient_y: IntProperty(
        name="Gradient orientation Y", description="", min=0, max=1, default=1
    )

    grad_orient_z: IntProperty(
        name="Gradient orientation Z", description="", min=0, max=1, default=0
    )

    pave_sides: EnumProperty(
        name="Pavement sides",
        description="",
        items=(("3", "3", ""), ("4", "4", ""), ("6", "6", "")),
        default="3",
    )

    pave_pat_2: IntProperty(
        name="Pavement pattern 2", description="maximum: 2", min=1, max=2, default=2
    )

    pave_pat_3: IntProperty(
        name="Pavement pattern 3", description="maximum: 3", min=1, max=3, default=3
    )

    pave_pat_4: IntProperty(
        name="Pavement pattern 4", description="maximum: 4", min=1, max=4, default=4
    )

    pave_pat_5: IntProperty(
        name="Pavement pattern 5", description="maximum: 5", min=1, max=5, default=5
    )

    pave_pat_7: IntProperty(
        name="Pavement pattern 7", description="maximum: 7", min=1, max=7, default=7
    )

    pave_pat_12: IntProperty(
        name="Pavement pattern 12", description="maximum: 12", min=1, max=12, default=12
    )

    pave_pat_22: IntProperty(
        name="Pavement pattern 22", description="maximum: 22", min=1, max=22, default=22
    )

    pave_pat_35: IntProperty(
        name="Pavement pattern 35", description="maximum: 35", min=1, max=35, default=35
    )

    pave_tiles: IntProperty(
        name="Pavement tiles",
        description="If sides = 6, maximum tiles 5!!!",
        min=1,
        max=6,
        default=1,
    )

    pave_form: IntProperty(name="Pavement form", description="", min=0, max=4, default=0)

    # -------- FUNCTIONS# ---------------------------------------------------------------- #

    func_list: EnumProperty(
        name="Functions",
        description="Select the function for create pattern",
        items=(
            ("NONE", "None", "No indentation"),
            ("f_algbr_cyl1", "Algbr cyl1", ""),
            ("f_algbr_cyl2", "Algbr cyl2", ""),
            ("f_algbr_cyl3", "Algbr cyl3", ""),
            ("f_algbr_cyl4", "Algbr cyl4", ""),
            ("f_bicorn", "Bicorn", ""),
            ("f_bifolia", "Bifolia", ""),
            ("f_blob", "Blob", ""),
            ("f_blob2", "Blob2", ""),
            ("f_boy_surface", "Boy surface", ""),
            ("f_comma", "Comma", ""),
            ("f_cross_ellipsoids", "Cross ellipsoids", ""),
            ("f_crossed_trough", "Crossed trough", ""),
            ("f_cubic_saddle", "Cubic saddle", ""),
            ("f_cushion", "Cushion", ""),
            ("f_devils_curve", "Devils curve", ""),
            ("f_devils_curve_2d", "Devils curve 2d", ""),
            ("f_dupin_cyclid", "Dupin cyclid", ""),
            ("f_ellipsoid", "Ellipsoid", ""),
            ("f_enneper", "Enneper", ""),
            ("f_flange_cover", "Flange cover", ""),
            ("f_folium_surface", "Folium surface", ""),
            ("f_folium_surface_2d", "Folium surface 2d", ""),
            ("f_glob", "Glob", ""),
            ("f_heart", "Heart", ""),
            ("f_helical_torus", "Helical torus", ""),
            ("f_helix1", "Helix1", ""),
            ("f_helix2", "Helix2", ""),
            ("f_hex_x", "Hex x", ""),
            ("f_hex_y", "Hex y", ""),
            ("f_hetero_mf", "Hetero mf", ""),
            ("f_hunt_surface", "Hunt surface", ""),
            ("f_hyperbolic_torus", "Hyperbolic torus", ""),
            ("f_isect_ellipsoids", "Isect ellipsoids", ""),
            ("f_kampyle_of_eudoxus", "Kampyle of eudoxus", ""),
            ("f_kampyle_of_eudoxus_2d", "Kampyle of eudoxus 2d", ""),
            ("f_klein_bottle", "Klein bottle", ""),
            ("f_kummer_surface_v1", "Kummer surface v1", ""),
            ("f_kummer_surface_v2", "Kummer surface v2", ""),
            ("f_lemniscate_of_gerono", "Lemniscate of gerono", ""),
            ("f_lemniscate_of_gerono_2d", "Lemniscate of gerono 2d", ""),
            ("f_mesh1", "Mesh1", ""),
            ("f_mitre", "Mitre", ""),
            ("f_nodal_cubic", "Nodal cubic", ""),
            ("f_noise3d", "Noise3d", ""),
            ("f_noise_generator", "Noise generator", ""),
            ("f_odd", "Odd", ""),
            ("f_ovals_of_cassini", "Ovals of cassini", ""),
            ("f_paraboloid", "Paraboloid", ""),
            ("f_parabolic_torus", "Parabolic torus", ""),
            ("f_ph", "Ph", ""),
            ("f_pillow", "Pillow", ""),
            ("f_piriform", "Piriform", ""),
            ("f_piriform_2d", "Piriform 2d", ""),
            ("f_poly4", "Poly4", ""),
            ("f_polytubes", "Polytubes", ""),
            ("f_quantum", "Quantum", ""),
            ("f_quartic_paraboloid", "Quartic paraboloid", ""),
            ("f_quartic_saddle", "Quartic saddle", ""),
            ("f_quartic_cylinder", "Quartic cylinder", ""),
            ("f_r", "R", ""),
            ("f_ridge", "Ridge", ""),
            ("f_ridged_mf", "Ridged mf", ""),
            ("f_rounded_box", "Rounded box", ""),
            ("f_sphere", "Sphere", ""),
            ("f_spikes", "Spikes", ""),
            ("f_spikes_2d", "Spikes 2d", ""),
            ("f_spiral", "Spiral", ""),
            ("f_steiners_roman", "Steiners roman", ""),
            ("f_strophoid", "Strophoid", ""),
            ("f_strophoid_2d", "Strophoid 2d", ""),
            ("f_superellipsoid", "Superellipsoid", ""),
            ("f_th", "Th", ""),
            ("f_torus", "Torus", ""),
            ("f_torus2", "Torus2", ""),
            ("f_torus_gumdrop", "Torus gumdrop", ""),
            ("f_umbrella", "Umbrella", ""),
            ("f_witch_of_agnesi", "Witch of agnesi", ""),
            ("f_witch_of_agnesi_2d", "Witch of agnesi 2d", ""),
        ),
        default="NONE",
    )

    func_x: FloatProperty(name="FX", description="", min=0.0, max=25.0, default=1.0)

    func_plus_x: EnumProperty(
        name="Func plus x",
        description="",
        items=(("NONE", "None", ""), ("increase", "*", ""), ("plus", "+", "")),
        default="NONE",
    )

    func_y: FloatProperty(name="FY", description="", min=0.0, max=25.0, default=1.0)

    func_plus_y: EnumProperty(
        name="Func plus y",
        description="",
        items=(("NONE", "None", ""), ("increase", "*", ""), ("plus", "+", "")),
        default="NONE",
    )

    func_z: FloatProperty(name="FZ", description="", min=0.0, max=25.0, default=1.0)

    func_plus_z: EnumProperty(
        name="Func plus z",
        description="",
        items=(("NONE", "None", ""), ("increase", "*", ""), ("plus", "+", "")),
        default="NONE",
    )

    func_P0: FloatProperty(name="P0", description="", min=0.0, max=25.0, default=1.0)

    func_P1: FloatProperty(name="P1", description="", min=0.0, max=25.0, default=1.0)

    func_P2: FloatProperty(name="P2", description="", min=0.0, max=25.0, default=1.0)

    func_P3: FloatProperty(name="P3", description="", min=0.0, max=25.0, default=1.0)

    func_P4: FloatProperty(name="P4", description="", min=0.0, max=25.0, default=1.0)

    func_P5: FloatProperty(name="P5", description="", min=0.0, max=25.0, default=1.0)

    func_P6: FloatProperty(name="P6", description="", min=0.0, max=25.0, default=1.0)

    func_P7: FloatProperty(name="P7", description="", min=0.0, max=25.0, default=1.0)

    func_P8: FloatProperty(name="P8", description="", min=0.0, max=25.0, default=1.0)

    func_P9: FloatProperty(name="P9", description="", min=0.0, max=25.0, default=1.0)

    # ----------------------------------- #
    tex_rot_x: FloatProperty(name="Rotate X", description="", min=-180.0, max=180.0, default=0.0)

    tex_rot_y: FloatProperty(name="Rotate Y", description="", min=-180.0, max=180.0, default=0.0)

    tex_rot_z: FloatProperty(name="Rotate Z", description="", min=-180.0, max=180.0, default=0.0)

    tex_mov_x: FloatProperty(
        name="Move X", description="", min=-100000.0, max=100000.0, default=0.0
    )

    tex_mov_y: FloatProperty(
        name="Move Y", description="", min=-100000.0, max=100000.0, default=0.0
    )

    tex_mov_z: FloatProperty(
        name="Move Z", description="", min=-100000.0, max=100000.0, default=0.0
    )

    tex_scale_x: FloatProperty(name="Scale X", description="", min=0.0, max=10000.0, default=1.0)

    tex_scale_y: FloatProperty(name="Scale Y", description="", min=0.0, max=10000.0, default=1.0)

    tex_scale_z: FloatProperty(name="Scale Z", description="", min=0.0, max=10000.0, default=1.0)


classes = (
    MaterialTextureSlot,
    WorldTextureSlot,
    RenderPovSettingsTexture,
)


def register():
    for cls in classes:
        register_class(cls)

    bpy.types.Material.pov_texture_slots = CollectionProperty(type=MaterialTextureSlot)
    bpy.types.World.pov_texture_slots = CollectionProperty(type=WorldTextureSlot)
    bpy.types.Texture.pov = PointerProperty(type=RenderPovSettingsTexture)


def unregister():
    del bpy.types.Texture.pov
    del bpy.types.World.pov_texture_slots
    del bpy.types.Material.pov_texture_slots

    for cls in reversed(classes):
        unregister_class(cls)

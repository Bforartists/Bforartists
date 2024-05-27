# SPDX-FileCopyrightText: 2021-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""Declare shading properties exported to POV textures."""
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
)


def check_material(mat):
    """Check that material node tree is not empty if use node button is on"""
    if mat is not None:
        return not mat.node_tree if mat.use_nodes else True
    return False


def pov_context_tex_datablock(context):
    """Texture context type recreated as deprecated in blender 2.8"""

    idblock = context.brush
    if idblock and context.scene.texture_context == "OTHER":
        return idblock

    # idblock = bpy.context.active_object.active_material
    idblock = context.view_layer.objects.active.active_material
    if idblock and context.scene.texture_context == "MATERIAL":
        return idblock

    idblock = context.scene.world
    if idblock and context.scene.texture_context == "WORLD":
        return idblock

    idblock = context.light
    if idblock and context.scene.texture_context == "LIGHT":
        return idblock

    if context.particle_system and context.scene.texture_context == "PARTICLES":
        idblock = context.particle_system.settings

    idblock = context.line_style
    if idblock and context.scene.texture_context == "LINESTYLE":
        return idblock

    return idblock


def active_texture_name_from_uilist(self, context):
    """Name created texture slots the same as created texture"""
    idblock = pov_context_tex_datablock(context)
    # mat = context.view_layer.objects.active.active_material
    if idblock is not None:
        index = idblock.pov.active_texture_index
        name = idblock.pov_texture_slots[index].name
        newname = idblock.pov_texture_slots[index].texture
        tex = bpy.data.textures[name]
        tex.name = newname
        idblock.pov_texture_slots[index].name = newname


def active_texture_name_from_search(self, context):
    """Texture rolldown to change the data linked by an existing texture"""
    idblock = pov_context_tex_datablock(context)
    # mat = context.view_layer.objects.active.active_material
    if idblock is not None:
        index = idblock.pov.active_texture_index
        slot = idblock.pov_texture_slots[index]
        name = slot.texture_search

    try:
        # tex = bpy.data.textures[name]
        slot.name = name
        slot.texture = name
        # Switch paint brush to this texture so settings remain contextual
        # bpy.context.tool_settings.image_paint.brush.texture = tex
        # bpy.context.tool_settings.image_paint.brush.mask_texture = tex
    except BaseException as e:
        print(e.__doc__)
        print("An exception occurred: {}".format(e))


def brush_texture_update(self, context):

    """Brush texture rolldown must show active slot texture props"""
    idblock = pov_context_tex_datablock(context)
    if idblock is not None:
        # mat = context.view_layer.objects.active.active_material
        idblock = pov_context_tex_datablock(context)
        slot = idblock.pov_texture_slots[idblock.pov.active_texture_index]
        if tex := slot.texture:
            # Switch paint brush to active texture so slot and settings remain contextual
            # bpy.ops.pov.textureslotupdate()
            bpy.context.tool_settings.image_paint.brush.texture = bpy.data.textures[tex]
            bpy.context.tool_settings.image_paint.brush.mask_texture = bpy.data.textures[tex]


class RenderPovSettingsMaterial(PropertyGroup):
    """Declare material level properties controllable in UI and translated to POV."""

    # --------------------------- Begin Old Blender Internal Props --------------------------- #
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

    active_texture_index: IntProperty(
        name="Index for texture_slots", default=0, update=brush_texture_update
    )

    transparency_method: EnumProperty(
        name="Specular Shader Model",
        description="Method to use for rendering transparency",
        items=(
            ("MASK", "Mask", "Mask the background"),
            ("Z_TRANSPARENCY", "Z Transparency", "Use alpha buffer for transparent faces"),
            ("RAYTRACE", "Raytrace", "Use raytracing for transparent refraction rendering"),
        ),
        default="MASK",
    )

    use_transparency: BoolProperty(
        name="Transparency", description="Render material as transparent", default=False
    )

    alpha: FloatProperty(
        name="Alpha",
        description="Alpha transparency of the material",
        min=0.0,
        max=1.0,
        soft_min=0.0,
        soft_max=1.0,
        default=1.0,
        precision=3,
    )

    specular_alpha: FloatProperty(
        name="Specular alpha",
        description="Alpha transparency for specular areas",
        min=0.0,
        max=1.0,
        soft_min=0.0,
        soft_max=1.0,
        default=1.0,
        precision=3,
    )

    ambient: FloatProperty(
        name="Ambient",
        description="Amount of global ambient color the material receives",
        min=0.0,
        max=1.0,
        soft_min=0.0,
        soft_max=1.0,
        default=1.0,
        precision=3,
    )
    # TODO: replace by newer agnostic Material.diffuse_color and remove from pov panel
    diffuse_color: FloatVectorProperty(
        name="Diffuse color",
        description="Diffuse color of the material",
        precision=4,
        step=0.01,
        min=0,  # max=inf, soft_max=1,
        default=(0.6, 0.6, 0.6),
        options={"ANIMATABLE"},
        subtype="COLOR",
    )

    darkness: FloatProperty(
        name="Darkness",
        description="Minnaert darkness",
        min=0.0,
        max=2.0,
        soft_min=0.0,
        soft_max=2.0,
        default=1.0,
        precision=3,
    )

    diffuse_fresnel: FloatProperty(
        name="Diffuse fresnel",
        description="Power of Fresnel",
        min=0.0,
        max=5.0,
        soft_min=0.0,
        soft_max=5.0,
        default=1.0,
        precision=3,
    )

    diffuse_fresnel_factor: FloatProperty(
        name="Diffuse fresnel factor",
        description="Blending factor of Fresnel",
        min=0.0,
        max=5.0,
        soft_min=0.0,
        soft_max=5.0,
        default=0.5,
        precision=3,
    )

    diffuse_intensity: FloatProperty(
        name="Diffuse intensity",
        description="Amount of diffuse reflection multiplying color",
        min=0.0,
        max=1.0,
        soft_min=0.0,
        soft_max=1.0,
        default=0.8,
        precision=3,
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
            ("LINEAR_LIGHT", "Linear light", ""),
        ),
        default="MIX",
    )

    diffuse_ramp_factor: FloatProperty(
        name="Factor",
        description="Blending factor (also uses alpha in Colorband)",
        min=0.0,
        max=1.0,
        soft_min=0.0,
        soft_max=1.0,
        default=1.0,
        precision=3,
    )

    diffuse_ramp_input: EnumProperty(
        name="Input",
        description="How the ramp maps on the surface",
        items=(
            ("SHADER", "Shader", ""),
            ("ENERGY", "Energy", ""),
            ("NORMAL", "Normal", ""),
            ("RESULT", "Result", ""),
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
            ("FRESNEL", "Fresnel", "Use a Fresnel shader"),
        ),
        default="LAMBERT",
    )

    diffuse_toon_size: FloatProperty(
        name="Size",
        description="Size of diffuse toon area",
        min=0.0,
        max=3.14,
        soft_min=0.0,
        soft_max=3.14,
        default=0.5,
        precision=3,
    )

    diffuse_toon_smooth: FloatProperty(
        name="Smooth",
        description="Smoothness of diffuse toon area",
        min=0.0,
        max=1.0,
        soft_min=0.0,
        soft_max=1.0,
        default=0.1,
        precision=3,
    )

    emit: FloatProperty(
        name="Emit",
        description="Amount of light to emit",
        min=0.0,
        soft_min=0.0,  # max=inf, soft_max=inf,
        default=0.0,
        precision=3,
    )

    mirror_color: FloatVectorProperty(
        name="Mirror color",
        description="Mirror color of the material",
        precision=4,
        step=0.01,
        min=0,  # max=inf, soft_max=1,
        default=(0.6, 0.6, 0.6),
        options={"ANIMATABLE"},
        subtype="COLOR",
    )

    roughness: FloatProperty(
        name="Roughness",
        description="Oren-Nayar Roughness",
        min=0.0,
        max=3.14,
        soft_min=0.0,
        soft_max=3.14,
        precision=3,
        default=0.5,
    )

    halo: BoolProperty(name="Halo", description=" Halo settings for the material", default=False)
    # (was readonly in Blender2.79, never None)

    line_color: FloatVectorProperty(
        name="Line color",
        description="Line color used for Freestyle line rendering",
        precision=4,
        step=0.01,
        min=0,  # max=inf, soft_max=1,
        default=(0.0, 0.0, 0.0),
        options={"ANIMATABLE"},
        subtype="COLOR",
    )

    # diffuse_ramp:
    ## Color ramp used to affect diffuse shading
    ## Type:    ColorRamp, (readonly)

    # cr_node = bpy.data.materials['Material'].node_tree.nodes['ColorRamp']
    # layout.template_color_ramp(cr_node, "color_ramp", expand=True)

    # ou

    # class bpy.types.ColorRamp(bpy_struct)

    line_priority: IntProperty(
        name="Recursion Limit",
        description="The line color of a higher priority is used at material boundaries",
        min=0,
        max=32767,
        default=0,
    )

    specular_color: FloatVectorProperty(
        name="Specular color",
        description="Specular color of the material ",
        precision=4,
        step=0.01,
        min=0.0,
        soft_max=1.0,
        default=(1.0, 1.0, 1.0),
        options={"ANIMATABLE"},
        subtype="COLOR",
    )
    specular_hardness: IntProperty(
        name="Hardness",
        description="How hard (sharp) the specular reflection is",
        min=1,
        max=511,
        default=30,
    )
    # TODO: replace by newer agnostic Material.specular_intensity and remove from pov panel
    specular_intensity: FloatProperty(
        name="Intensity",
        description="How intense (bright) the specular reflection is",
        min=0.0,
        max=1.0,
        soft_min=0.0,
        soft_max=1.0,
        default=0.1,
        precision=3,
    )

    specular_ior: FloatProperty(
        name="IOR",
        description="Specular index of refraction",
        min=-10.0,
        max=10.0,
        soft_min=0.0,
        soft_max=10.0,
        default=1.0,
        precision=3,
    )

    ior: FloatProperty(
        name="IOR",
        description="Index of refraction",
        min=-10.0,
        max=10.0,
        soft_min=0.0,
        soft_max=10.0,
        default=1.0,
        precision=3,
    )

    specular_shader: EnumProperty(
        name="Specular Shader Model",
        description="How the ramp maps on the surface",
        items=(
            ("COOKTORR", "CookTorr", "Use a Cook-Torrance shader"),
            ("PHONG", "Phong", "Use a Phong shader"),
            ("BLINN", "Blinn", "Use a Blinn shader"),
            ("TOON", "Toon", "Use a Toon shader"),
            ("WARDISO", "WardIso", "Use a Ward anisotropic shader"),
        ),
        default="COOKTORR",
    )

    specular_slope: FloatProperty(
        name="Slope",
        description="The standard deviation of surface slope",
        min=0.0,
        max=0.4,
        soft_min=0.0,
        soft_max=0.4,
        default=0.1,
        precision=3,
    )

    specular_toon_size: FloatProperty(
        name="Size",
        description="Size of specular toon area",
        min=0.0,
        max=0.53,
        soft_min=0.0,
        soft_max=0.53,
        default=0.5,
        precision=3,
    )

    specular_toon_smooth: FloatProperty(
        name="Smooth",
        description="Smoothness of specular toon area",
        min=0.0,
        max=1.0,
        soft_min=0.0,
        soft_max=1.0,
        default=0.1,
        precision=3,
    )

    translucency: FloatProperty(
        name="Translucency",
        description="Amount of diffuse shading on the back side",
        min=0.0,
        max=1.0,
        soft_min=0.0,
        soft_max=1.0,
        default=0.0,
        precision=3,
    )

    transparency_method: EnumProperty(
        name="Specular Shader Model",
        description="Method to use for rendering transparency",
        items=(
            ("MASK", "Mask", "Mask the background"),
            ("Z_TRANSPARENCY", "Z Transparency", "Use an ior of 1 for transparent faces"),
            ("RAYTRACE", "Raytrace", "Use raytracing for transparent refraction rendering"),
        ),
        default="MASK",
    )

    type: EnumProperty(
        name="Type",
        description="Material type defining how the object is rendered",
        items=(
            ("SURFACE", "Surface", "Render object as a surface"),
            # TO UPDATE > USE wire MACRO AND CHANGE DESCRIPTION
            ("WIRE", "Wire", "Render the edges of faces as wires (not supported in raytracing)"),
            ("VOLUME", "Volume", "Render object as a volume"),
            # TO UPDATE > USE halo MACRO AND CHANGE DESCRIPTION
            ("HALO", "Halo", "Render object as halo particles"),
        ),
        default="SURFACE",
    )

    use_cast_shadows: BoolProperty(
        name="Cast", description="Allow this material to cast shadows", default=True
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
        description="Use cubic interpolation for diffuse " "values, for smoother transitions",
        default=False,
    )

    use_diffuse_ramp: BoolProperty(
        name="Ramp", description="Toggle diffuse ramp operations", default=False
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
        description="When linked in, material uses local light" " group with the same name",
        default=False,
    )

    use_mist: BoolProperty(
        name="Use Mist",
        description="Use mist with this material " "(in world settings)",
        default=True,
    )

    use_nodes: BoolProperty(
        name="Nodes",
        # Add Icon in UI or here? icon='NODES'
        description="Use shader nodes to render the material",
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
        description="Make this material insensitive to " "light or shadow",
        default=False,
    )

    use_shadows: BoolProperty(
        name="Receive", description="Allow this material to receive shadows", default=True
    )

    use_sky: BoolProperty(
        name="Sky",
        description="Render this material with zero alpha, "
        "with sky background in place (scanline only)",
        default=False,
    )

    use_specular_ramp: BoolProperty(
        name="Ramp", description="Toggle specular ramp operations", default=False
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
        description="Allow this object to receive transparent " "shadows cast through other object",
        default=False,
    )  # linked to fake caustics

    use_vertex_color_light: BoolProperty(
        name="Vertex Color Light",
        description="Add vertex colors as additional lighting",
        default=False,
    )

    # TODO create interface:
    use_vertex_color_paint: BoolProperty(
        name="Vertex Color Paint",
        description="Replace object base color with vertex "
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
            ("LINEAR_LIGHT", "Linear light", ""),
        ),
        default="MIX",
    )

    specular_ramp_factor: FloatProperty(
        name="Factor",
        description="Blending factor (also uses alpha in Colorband)",
        min=0.0,
        max=1.0,
        soft_min=0.0,
        soft_max=1.0,
        default=1.0,
        precision=3,
    )

    specular_ramp_input: EnumProperty(
        name="Input",
        description="How the ramp maps on the surface",
        items=(
            ("SHADER", "Shader", ""),
            ("ENERGY", "Energy", ""),
            ("NORMAL", "Normal", ""),
            ("RESULT", "Result", ""),
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
        min=0.0,
        max=1.0,
        soft_min=0.01,
        soft_max=1.0,
        default=0.25,
    )

    irid_thickness: FloatProperty(
        name="thickness",
        description="A very thin film will have a high frequency of color changes while a "
        "thick film will have large areas of color",
        min=0.0,
        max=1000.0,
        soft_min=0.1,
        soft_max=10.0,
        default=1,
    )

    irid_turbulence: FloatProperty(
        name="turbulence",
        description="This parameter varies the thickness",
        min=0.0,
        max=10.0,
        soft_min=0.000,
        soft_max=1.0,
        default=0,
    )

    interior_fade_color: FloatVectorProperty(
        name="Interior Fade Color",
        description="Color of filtered attenuation for transparent " "materials",
        precision=4,
        step=0.01,
        min=0.0,
        soft_max=1.0,
        default=(0, 0, 0),
        options={"ANIMATABLE"},
        subtype="COLOR",
    )

    caustics_enable: BoolProperty(
        name="Caustics",
        description="use only fake refractive caustics (default) or photon based "
        "reflective/refractive caustics",
        default=True,
    )

    fake_caustics: BoolProperty(
        name="Fake Caustics",
        description="use only (Fast) fake refractive caustics based on transparent shadows",
        default=True
    )

    fake_caustics_power: FloatProperty(
        name="Fake caustics power",
        description="Values typically range from 0.0 to 1.0 or higher. Zero is no caustics. "
        "Low, non-zero values give broad hot-spots while higher values give "
        "tighter, smaller simulated focal points",
        min=0.00,
        max=10.0,
        soft_min=0.00,
        soft_max=5.0,
        default=0.15,
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
        min=1.0000,
        max=10.000,
        soft_min=1.0000,
        soft_max=1.1000,
        precision=4,
        default=1.0000,
    )

    photons_dispersion_samples: IntProperty(
        name="Dispersion Samples",
        description="Number of color-steps for dispersion",
        min=2,
        max=128,
        default=7,
    )

    photons_reflection: BoolProperty(
        name="Reflective Photon Caustics",
        description="Use this to make your Sauron's ring ;-P",
        default=False,
    )

    refraction_type: EnumProperty(
        items=[
            ("1", "Z Transparency Fake Caustics", "use fake caustics"),
            ("2", "Raytrace Photons Caustics", "use photons for refractive caustics"),
        ],
        name="Refraction Type:",
        description="use fake caustics (fast) or true photons for refractive Caustics",
        default="1",
    )

    # ------------------------------ CustomPOV Code ------------------------------ #
    replacement_text: StringProperty(
        name="Declared name:",
        description="Type the variable name as declared either directly inlined "
        "in your custom POV code from the text editor datablock (checked as a "
        "source to render in it's side property panel), or this declaration can be "
        "from an external .inc it points at. Here, name = texture {} expected",
        default="",
    )

    # NODES

    def use_material_nodes_callback(self, context):
        """Identify if node has been added and if it is used yet or default"""

        if hasattr(context.space_data, "tree_type"):
            context.space_data.tree_type = "ObjectNodeTree"
        mat = context.object.active_material
        if mat.pov.material_use_nodes:
            mat.use_nodes = True
            tree = mat.node_tree
            # tree.name = mat.name # XXX READONLY
            links = tree.links
            default = True
            if len(tree.nodes) == 2:
                o = 0
                m = 0
                for node in tree.nodes:
                    if node.type in {"OUTPUT", "MATERIAL"}:
                        tree.nodes.remove(node)
                        default = True
                for node in tree.nodes:
                    if node.bl_idname == "PovrayOutputNode":
                        o += 1
                    elif node.bl_idname == "PovrayTextureNode":
                        m += 1
                if o == 1 and m == 1:
                    default = False
            elif len(tree.nodes) == 0:
                default = True
            else:
                default = False
            if default:
                output = tree.nodes.new("PovrayOutputNode")
                output.location = 200, 200
                tmap = tree.nodes.new("PovrayTextureNode")
                tmap.location = 0, 200
                links.new(tmap.outputs[0], output.inputs[0])
                tmap.select = True
                tree.nodes.active = tmap
        else:
            mat.use_nodes = False

    def use_texture_nodes_callback(self, context):
        """Identify texture nodes by filtering out output and composite ones"""

        tex = context.object.active_material.active_texture
        if tex.pov.texture_use_nodes:
            tex.use_nodes = True
            if len(tex.node_tree.nodes) == 2:
                for node in tex.node_tree.nodes:
                    if node.type in {"OUTPUT", "CHECKER"}:
                        tex.node_tree.nodes.remove(node)
        else:
            tex.use_nodes = False

    def node_active_callback(self, context):
        """Synchronize active node with material before getting it"""

        items = []  # XXX comment out > remove?
        mat = context.material
        mat.node_tree.nodes  # XXX comment out > remove?
        for node in mat.node_tree.nodes:
            node.select = False
        for node in mat.node_tree.nodes:
            if node.name == mat.pov.material_active_node:
                node.select = True
                mat.node_tree.nodes.active = node

                return node

    def node_enum_callback(self, context):
        mat = context.material
        nodes = mat.node_tree.nodes
        return [("%s" % node.name, "%s" % node.name, "") for node in nodes]

    def pigment_normal_callback(self, context):
        render = context.scene.pov.render  # XXX comment out > remove?
        return (
            [("pigment", "Pigment", ""), ("normal", "Normal", "")]
            # XXX Find any other such traces of hgpovray experiment > remove or deploy ?
            if render != "hgpovray"
            else [
                ("pigment", "Pigment", ""),
                ("normal", "Normal", ""),
                ("modulation", "Modulation", ""),
            ]
        )

    def glow_callback(self, context):
        scene = context.scene
        ob = context.object
        ob.pov.mesh_write_as_old = ob.pov.mesh_write_as
        if scene.pov.render == "uberpov" and ob.pov.glow:
            ob.pov.mesh_write_as = "NONE"
        else:
            ob.pov.mesh_write_as = ob.pov.mesh_write_as_old

    material_use_nodes: BoolProperty(
        name="Use nodes", description="", update=use_material_nodes_callback, default=False
    )

    material_active_node: EnumProperty(
        name="Active node", description="", items=node_enum_callback, update=node_active_callback
    )

    preview_settings: BoolProperty(name="Preview Settings", description="", default=False)

    object_preview_transform: BoolProperty(name="Transform object", description="", default=False)

    object_preview_scale: FloatProperty(name="XYZ", min=0.5, max=2.0, default=1.0)

    object_preview_rotate: FloatVectorProperty(
        name="Rotate", description="", min=-180.0, max=180.0, default=(0.0, 0.0, 0.0), subtype="XYZ"
    )

    object_preview_bgcontrast: FloatProperty(name="Contrast", min=0.0, max=1.0, default=0.5)



# ------------------------------ End Old Blender Internal Props ------------------------------ #


classes = (
    RenderPovSettingsMaterial,
)


def register():
    for cls in classes:
        register_class(cls)

    bpy.types.Material.pov = PointerProperty(type=RenderPovSettingsMaterial)


def unregister():
    del bpy.types.Material.pov

    for cls in reversed(classes):
        unregister_class(cls)

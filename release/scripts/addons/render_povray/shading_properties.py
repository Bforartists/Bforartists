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
        if mat.use_nodes:
            if not mat.node_tree:  # FORMERLY : #mat.active_node_material is not None:
                return True
            return False
        return True
    return False


def pov_context_tex_datablock(context):
    """Texture context type recreated as deprecated in blender 2.8"""

    idblock = context.brush
    if idblock and context.scene.texture_context == 'OTHER':
        return idblock

    # idblock = bpy.context.active_object.active_material
    idblock = context.view_layer.objects.active.active_material
    if idblock and context.scene.texture_context == 'MATERIAL':
        return idblock

    idblock = context.scene.world
    if idblock and context.scene.texture_context == 'WORLD':
        return idblock

    idblock = context.light
    if idblock and context.scene.texture_context == 'LIGHT':
        return idblock

    if context.particle_system and context.scene.texture_context == 'PARTICLES':
        idblock = context.particle_system.settings

    return idblock

    idblock = context.line_style
    if idblock and context.scene.texture_context == 'LINESTYLE':
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
        print('An exception occurred: {}'.format(e))
        pass


def brush_texture_update(self, context):

    """Brush texture rolldown must show active slot texture props"""
    idblock = pov_context_tex_datablock(context)
    if idblock is not None:
        # mat = context.view_layer.objects.active.active_material
        idblock = pov_context_tex_datablock(context)
        slot = idblock.pov_texture_slots[idblock.pov.active_texture_index]
        tex = slot.texture

        if tex:
            # Switch paint brush to active texture so slot and settings remain contextual
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

    diffuse_color: FloatVectorProperty(
        name="Diffuse color",
        description=("Diffuse color of the material"),
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
        description=("Mirror color of the material"),
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
        description=("Line color used for Freestyle line rendering"),
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
        description=("Specular color of the material "),
        precision=4,
        step=0.01,
        min=0,  # max=inf, soft_max=1,
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
        name="Fake Caustics", description="use only (Fast) fake refractive caustics", default=True
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
                    if node.bl_idname == "PovrayTextureNode":
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
        items = [("pigment", "Pigment", ""), ("normal", "Normal", "")]
        # XXX Find any other such traces of hgpovray experiment > remove or deploy ?
        if render == "hgpovray":
            items = [
                ("pigment", "Pigment", ""),
                ("normal", "Normal", ""),
                ("modulation", "Modulation", ""),
            ]
        return items

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


class MaterialRaytraceTransparency(PropertyGroup):
    """Declare transparency panel properties controllable in UI and translated to POV."""

    depth: IntProperty(
        name="Depth",
        description="Maximum allowed number of light inter-refractions",
        min=0,
        max=32767,
        default=2,
    )

    depth_max: FloatProperty(
        name="Depth",
        description="Maximum depth for light to travel through the "
        "transparent material before becoming fully filtered (0.0 is disabled)",
        min=0,
        max=100,
        default=0.0,
    )

    falloff: FloatProperty(
        name="Falloff",
        description="Falloff power for transmissivity filter effect (1.0 is linear)",
        min=0.1,
        max=10.0,
        default=1.0,
        precision=3,
    )

    filter: FloatProperty(
        name="Filter",
        description="Amount to blend in the material’s diffuse color in raytraced "
        "transparency (simulating absorption)",
        min=0.0,
        max=1.0,
        default=0.0,
        precision=3,
    )

    fresnel: FloatProperty(
        name="Fresnel",
        description="Power of Fresnel for transparency (Ray or ZTransp)",
        min=0.0,
        max=5.0,
        soft_min=0.0,
        soft_max=5.0,
        default=0.0,
        precision=3,
    )

    fresnel_factor: FloatProperty(
        name="Blend",
        description="Blending factor for Fresnel",
        min=0.0,
        max=5.0,
        soft_min=0.0,
        soft_max=5.0,
        default=1.250,
        precision=3,
    )

    gloss_factor: FloatProperty(
        name="Amount",
        description="The clarity of the refraction. "
        "(values < 1.0 give diffuse, blurry refractions)",
        min=0.0,
        max=1.0,
        soft_min=0.0,
        soft_max=1.0,
        default=1.0,
        precision=3,
    )

    gloss_samples: IntProperty(
        name="Samples",
        description="frequency of the noise sample used for blurry refractions",
        min=0,
        max=1024,
        default=18,
    )

    gloss_threshold: FloatProperty(
        name="Threshold",
        description="Threshold for adaptive sampling (if a sample "
        "contributes less than this amount [as a percentage], "
        "sampling is stopped)",
        min=0.0,
        max=1.0,
        soft_min=0.0,
        soft_max=1.0,
        default=0.005,
        precision=3,
    )

    ior: FloatProperty(
        name="IOR",
        description="Sets angular index of refraction for raytraced refraction",
        min=-0.0,
        max=10.0,
        soft_min=0.25,
        soft_max=4.0,
        default=1.3,
    )


class MaterialRaytraceMirror(PropertyGroup):
    """Declare reflection panel properties controllable in UI and translated to POV."""

    bl_description = ("Raytraced reflection settings for the Material",)

    use: BoolProperty(name="Mirror", description="Enable raytraced reflections", default=False)

    depth: IntProperty(
        name="Depth",
        description="Maximum allowed number of light inter-reflections",
        min=0,
        max=32767,
        default=2,
    )

    distance: FloatProperty(
        name="Max Dist",
        description="Maximum distance of reflected rays "
        "(reflections further than this range "
        "fade to sky color or material color)",
        min=0.0,
        max=100000.0,
        soft_min=0.0,
        soft_max=10000.0,
        default=0.0,
        precision=3,
    )

    fade_to: EnumProperty(
        items=[
            ("FADE_TO_SKY", "Fade to sky", ""),
            ("FADE_TO_MATERIAL", "Fade to material color", ""),
        ],
        name="Fade-out Color",
        description="The color that rays with no intersection within the "
        "Max Distance take (material color can be best for "
        "indoor scenes, sky color for outdoor)",
        default="FADE_TO_SKY",
    )

    fresnel: FloatProperty(
        name="Fresnel",
        description="Power of Fresnel for mirror reflection",
        min=0.0,
        max=5.0,
        soft_min=0.0,
        soft_max=5.0,
        default=0.0,
        precision=3,
    )

    fresnel_factor: FloatProperty(
        name="Blend",
        description="Blending factor for Fresnel",
        min=0.0,
        max=5.0,
        soft_min=0.0,
        soft_max=5.0,
        default=1.250,
        precision=3,
    )

    gloss_anisotropic: FloatProperty(
        name="Anisotropic",
        description="The shape of the reflection, from 0.0 (circular) "
        "to 1.0 (fully stretched along the tangent",
        min=0.0,
        max=1.0,
        soft_min=0.0,
        soft_max=1.0,
        default=1.0,
        precision=3,
    )

    gloss_factor: FloatProperty(
        name="Amount",
        description="The shininess of the reflection  "
        "(values < 1.0 give diffuse, blurry reflections)",
        min=0.0,
        max=1.0,
        soft_min=0.0,
        soft_max=1.0,
        default=1.0,
        precision=3,
    )

    gloss_samples: IntProperty(
        name="Noise",
        description="Frequency of the noise pattern bumps averaged for blurry reflections",
        min=0,
        max=1024,
        default=18,
    )

    gloss_threshold: FloatProperty(
        name="Threshold",
        description="Threshold for adaptive sampling (if a sample "
        "contributes less than this amount [as a percentage], "
        "sampling is stopped)",
        min=0.0,
        max=1.0,
        soft_min=0.0,
        soft_max=1.0,
        default=0.005,
        precision=3,
    )

    mirror_color: FloatVectorProperty(
        name="Mirror color",
        description=("Mirror color of the material"),
        precision=4,
        step=0.01,
        default=(1.0, 1.0, 1.0),
        options={"ANIMATABLE"},
        subtype="COLOR",
    )

    reflect_factor: FloatProperty(
        name="Reflectivity",
        description="Amount of mirror reflection for raytrace",
        min=0.0,
        max=1.0,
        soft_min=0.0,
        soft_max=1.0,
        default=1.0,
        precision=3,
    )


class MaterialSubsurfaceScattering(PropertyGroup):
    r"""Declare SSS/SSTL properties controllable in UI and translated to POV."""

    bl_description = ("Subsurface scattering settings for the material",)

    use: BoolProperty(
        name="Subsurface Scattering",
        description="Enable diffuse subsurface scatting " "effects in a material",
        default=False,
    )

    back: FloatProperty(
        name="Back",
        description="Back scattering weight",
        min=0.0,
        max=10.0,
        soft_min=0.0,
        soft_max=10.0,
        default=1.0,
        precision=3,
    )

    color: FloatVectorProperty(
        name="Scattering color",
        description=("Scattering color"),
        precision=4,
        step=0.01,
        default=(0.604, 0.604, 0.604),
        options={"ANIMATABLE"},
        subtype="COLOR",
    )

    color_factor: FloatProperty(
        name="Color",
        description="Blend factor for SSS colors",
        min=0.0,
        max=1.0,
        soft_min=0.0,
        soft_max=1.0,
        default=1.0,
        precision=3,
    )

    error_threshold: FloatProperty(
        name="Error",
        description="Error tolerance (low values are slower and higher quality)",
        default=0.050,
        precision=3,
    )

    front: FloatProperty(
        name="Front",
        description="Front scattering weight",
        min=0.0,
        max=2.0,
        soft_min=0.0,
        soft_max=2.0,
        default=1.0,
        precision=3,
    )

    ior: FloatProperty(
        name="IOR",
        description="Index of refraction (higher values are denser)",
        min=-0.0,
        max=10.0,
        soft_min=0.1,
        soft_max=2.0,
        default=1.3,
    )

    radius: FloatVectorProperty(
        name="RGB Radius",
        description=("Mean red/green/blue scattering path length"),
        precision=4,
        step=0.01,
        min=0.001,
        default=(1.0, 1.0, 1.0),
        options={"ANIMATABLE"},
    )

    scale: FloatProperty(
        name="Scale", description="Object scale factor", default=0.100, precision=3
    )

    texture_factor: FloatProperty(
        name="Texture",
        description="Texture scattering blend factor",
        min=0.0,
        max=1.0,
        soft_min=0.0,
        soft_max=1.0,
        default=0.0,
        precision=3,
    )


class MaterialStrandSettings(PropertyGroup):
    """Declare strand properties controllable in UI and translated to POV."""

    bl_description = ("Strand settings for the material",)

    blend_distance: FloatProperty(
        name="Distance",
        description="Worldspace distance over which to blend in the surface normal",
        min=0.0,
        max=10.0,
        soft_min=0.0,
        soft_max=10.0,
        default=0.0,
        precision=3,
    )

    root_size: FloatProperty(
        name="Root",
        description="Start size of strands in pixels or Blender units",
        min=0.25,
        default=1.0,
        precision=5,
    )

    shape: FloatProperty(
        name="Shape",
        description="Positive values make strands rounder, negative ones make strands spiky",
        min=-0.9,
        max=0.9,
        default=0.0,
        precision=3,
    )

    size_min: FloatProperty(
        name="Minimum",
        description="Minimum size of strands in pixels",
        min=0.001,
        max=10.0,
        default=1.0,
        precision=3,
    )

    tip_size: FloatProperty(
        name="Tip",
        description="End size of strands in pixels or Blender units",
        min=0.0,
        default=1.0,
        precision=5,
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
        min=0.0,
        max=2.0,
        default=0.0,
        precision=3,
    )

    # halo

    # Halo settings for the material
    # Type: MaterialHalo, (readonly, never None)

    # ambient

    # Amount of global ambient color the material receives
    # Type: float in [0, 1], default 0.0

    # darkness

    # Minnaert darkness
    # Type: float in [0, 2], default 0.0

    # diffuse_color

    # Diffuse color of the material
    # Type: float array of 3 items in [0, inf], default (0.0, 0.0, 0.0)

    # diffuse_fresnel

    # Power of Fresnel
    # Type: float in [0, 5], default 0.0

    # diffuse_fresnel_factor

    # Blending factor of Fresnel
    # Type: float in [0, 5], default 0.0

    # diffuse_intensity

    # Amount of diffuse reflection
    # Type: float in [0, 1], default 0.0

    # diffuse_ramp

    # Color ramp used to affect diffuse shading
    # Type: ColorRamp, (readonly)

    # diffuse_ramp_blend

    # Blending method of the ramp and the diffuse color
    # Type: enum in [‘MIX’, ‘ADD’, ‘MULTIPLY’, ‘SUBTRACT’, ‘SCREEN’, ‘DIVIDE’, ‘DIFFERENCE’, ‘DARKEN’, ‘LIGHTEN’, ‘OVERLAY’, ‘DODGE’, ‘BURN’, ‘HUE’, ‘SATURATION’, ‘VALUE’, ‘COLOR’, ‘SOFT_LIGHT’, ‘LINEAR_LIGHT’], default ‘MIX’

    # diffuse_ramp_factor

    # Blending factor (also uses alpha in Colorband)
    # Type: float in [0, 1], default 0.0

    # diffuse_ramp_input

    # How the ramp maps on the surface
    # Type: enum in [‘SHADER’, ‘ENERGY’, ‘NORMAL’, ‘RESULT’], default ‘SHADER’

    # diffuse_shader

    # LAMBERT Lambert, Use a Lambertian shader.
    # OREN_NAYAR Oren-Nayar, Use an Oren-Nayar shader.
    # TOON Toon, Use a toon shader.
    # MINNAERT Minnaert, Use a Minnaert shader.
    # FRESNEL Fresnel, Use a Fresnel shader.

    # Type: enum in [‘LAMBERT’, ‘OREN_NAYAR’, ‘TOON’, ‘MINNAERT’, ‘FRESNEL’], default ‘LAMBERT’

    # diffuse_toon_size

    # Size of diffuse toon area
    # Type: float in [0, 3.14], default 0.0

    # diffuse_toon_smooth

    # Smoothness of diffuse toon area
    # Type: float in [0, 1], default 0.0

    # emit

    # Amount of light to emit
    # Type: float in [0, inf], default 0.0

    # game_settings

    # Game material settings
    # Type: MaterialGameSettings, (readonly, never None)

    # halo

    # Halo settings for the material
    # Type: MaterialHalo, (readonly, never None)

    # invert_z

    # Render material’s faces with an inverted Z buffer (scanline only)
    # Type: boolean, default False

    # light_group

    # Limit lighting to lamps in this Group
    # Type: Group

    # line_color

    # Line color used for Freestyle line rendering
    # Type: float array of 4 items in [0, inf], default (0.0, 0.0, 0.0, 0.0)

    # line_priority

    # The line color of a higher priority is used at material boundaries
    # Type: int in [0, 32767], default 0

    # mirror_color

    # Mirror color of the material
    # Type: float array of 3 items in [0, inf], default (0.0, 0.0, 0.0)

    # node_tree

    # Node tree for node based materials
    # Type: NodeTree, (readonly)

    # offset_z

    # Give faces an artificial offset in the Z buffer for Z transparency
    # Type: float in [-inf, inf], default 0.0

    # paint_active_slot

    # Index of active texture paint slot
    # Type: int in [0, 32767], default 0

    # paint_clone_slot

    # Index of clone texture paint slot
    # Type: int in [0, 32767], default 0

    # pass_index

    # Index number for the “Material Index” render pass
    # Type: int in [0, 32767], default 0

    # physics

    # Game physics settings
    # Type: MaterialPhysics, (readonly, never None)

    # preview_render_type

    # Type of preview render

    # FLAT Flat, Flat XY plane.
    # SPHERE Sphere, Sphere.
    # CUBE Cube, Cube.
    # MONKEY Monkey, Monkey.
    # HAIR Hair, Hair strands.
    # SPHERE_A World Sphere, Large sphere with sky.

    # Type: enum in [‘FLAT’, ‘SPHERE’, ‘CUBE’, ‘MONKEY’, ‘HAIR’, ‘SPHERE_A’], default ‘FLAT’

    # raytrace_mirror

    # Raytraced reflection settings for the material
    # Type: MaterialRaytraceMirror, (readonly, never None)

    # raytrace_transparency

    # Raytraced transparency settings for the material
    # Type: MaterialRaytraceTransparency, (readonly, never None)

    # roughness

    # Oren-Nayar Roughness
    # Type: float in [0, 3.14], default 0.0

    # shadow_buffer_bias

    # Factor to multiply shadow buffer bias with (0 is ignore)
    # Type: float in [0, 10], default 0.0

    # shadow_cast_alpha

    # Shadow casting alpha, in use for Irregular and Deep shadow buffer
    # Type: float in [0.001, 1], default 0.0

    # shadow_only_type

    # How to draw shadows

    # SHADOW_ONLY_OLD Shadow and Distance, Old shadow only method.
    # SHADOW_ONLY Shadow Only, Improved shadow only method.
    # SHADOW_ONLY_SHADED Shadow and Shading, Improved shadow only method which also renders lightless areas as shadows.

    # Type: enum in [‘SHADOW_ONLY_OLD’, ‘SHADOW_ONLY’, ‘SHADOW_ONLY_SHADED’], default ‘SHADOW_ONLY_OLD’

    # shadow_ray_bias

    # Shadow raytracing bias to prevent terminator problems on shadow boundary
    # Type: float in [0, 0.25], default 0.0

    # specular_color

    # Specular color of the material
    # Type: float array of 3 items in [0, inf], default (0.0, 0.0, 0.0)

    # specular_hardness

    # How hard (sharp) the specular reflection is
    # Type: int in [1, 511], default 0

    # specular_intensity

    # How intense (bright) the specular reflection is
    # Type: float in [0, 1], default 0.0

    # specular_ior

    # Specular index of refraction
    # Type: float in [1, 10], default 0.0

    # specular_ramp

    # Color ramp used to affect specular shading
    # Type: ColorRamp, (readonly)

    # specular_ramp_blend

    # Blending method of the ramp and the specular color
    # Type: enum in [‘MIX’, ‘ADD’, ‘MULTIPLY’, ‘SUBTRACT’, ‘SCREEN’, ‘DIVIDE’, ‘DIFFERENCE’, ‘DARKEN’, ‘LIGHTEN’, ‘OVERLAY’, ‘DODGE’, ‘BURN’, ‘HUE’, ‘SATURATION’, ‘VALUE’, ‘COLOR’, ‘SOFT_LIGHT’, ‘LINEAR_LIGHT’], default ‘MIX’

    # specular_ramp_factor

    # Blending factor (also uses alpha in Colorband)
    # Type: float in [0, 1], default 0.0

    # specular_ramp_input

    # How the ramp maps on the surface
    # Type: enum in [‘SHADER’, ‘ENERGY’, ‘NORMAL’, ‘RESULT’], default ‘SHADER’
    # specular_shader

    # COOKTORR CookTorr, Use a Cook-Torrance shader.
    # PHONG Phong, Use a Phong shader.
    # BLINN Blinn, Use a Blinn shader.
    # TOON Toon, Use a toon shader.
    # WARDISO WardIso, Use a Ward anisotropic shader.

    # Type: enum in [‘COOKTORR’, ‘PHONG’, ‘BLINN’, ‘TOON’, ‘WARDISO’], default ‘COOKTORR’

    # specular_slope

    # The standard deviation of surface slope
    # Type: float in [0, 0.4], default 0.0

    # specular_toon_size

    # Size of specular toon area
    # Type: float in [0, 1.53], default 0.0

    # specular_toon_smooth

    # Smoothness of specular toon area
    # Type: float in [0, 1], default 0.0

    # strand

    # Strand settings for the material
    # Type: MaterialStrand, (readonly, never None)

    # subsurface_scattering

    # Subsurface scattering settings for the material
    # Type: MaterialSubsurfaceScattering, (readonly, never None)

    # texture_paint_images

    # Texture images used for texture painting
    # Type: bpy_prop_collection of Image, (readonly)

    # texture_paint_slots

    # Texture slots defining the mapping and influence of textures
    # Type: bpy_prop_collection of TexPaintSlot, (readonly)

    # texture_slots

    # Texture slots defining the mapping and influence of textures
    # Type: MaterialTextureSlots bpy_prop_collection of MaterialTextureSlot, (readonly)

    # translucency

    # Amount of diffuse shading on the back side
    # Type: float in [0, 1], default 0.0

    # transparency_method

    # Method to use for rendering transparency

    # MASK Mask, Mask the background.
    # Z_TRANSPARENCY Z Transparency, Use alpha buffer for transparent faces.
    # RAYTRACE Raytrace, Use raytracing for transparent refraction rendering.

    # Type: enum in [‘MASK’, ‘Z_TRANSPARENCY’, ‘RAYTRACE’], default ‘MASK’

    # type

    # Material type defining how the object is rendered

    # SURFACE Surface, Render object as a surface.
    # WIRE Wire, Render the edges of faces as wires (not supported in raytracing).
    # VOLUME Volume, Render object as a volume.
    # HALO Halo, Render object as halo particles.

    # Type: enum in [‘SURFACE’, ‘WIRE’, ‘VOLUME’, ‘HALO’], default ‘SURFACE’

    # use_cast_approximate

    # Allow this material to cast shadows when using approximate ambient occlusion
    # Type: boolean, default False

    # use_cast_buffer_shadows

    # Allow this material to cast shadows from shadow buffer lamps
    # Type: boolean, default False

    # use_cast_shadows

    # Allow this material to cast shadows
    # Type: boolean, default False

    # use_cast_shadows_only

    # Make objects with this material appear invisible (not rendered), only casting shadows
    # Type: boolean, default False

    # use_cubic

    # Use cubic interpolation for diffuse values, for smoother transitions
    # Type: boolean, default False

    # use_diffuse_ramp

    # Toggle diffuse ramp operations
    # Type: boolean, default False

    # use_face_texture

    # Replace the object’s base color with color from UV map image textures
    # Type: boolean, default False

    # use_face_texture_alpha

    # Replace the object’s base alpha value with alpha from UV map image textures
    # Type: boolean, default False

    # use_full_oversampling

    # Force this material to render full shading/textures for all anti-aliasing samples
    # Type: boolean, default False

    # use_light_group_exclusive

    # Material uses the light group exclusively - these lamps are excluded from other scene lighting
    # Type: boolean, default False

    # use_light_group_local

    # When linked in, material uses local light group with the same name
    # Type: boolean, default False

    # use_mist

    # Use mist with this material (in world settings)
    # Type: boolean, default False

    # use_nodes

    # Use shader nodes to render the material
    # Type: boolean, default False

    # use_object_color

    # Modulate the result with a per-object color
    # Type: boolean, default False

    # use_only_shadow

    # Render shadows as the material’s alpha value, making the material transparent except for shadowed areas
    # Type: boolean, default False

    # use_ray_shadow_bias

    # Prevent raytraced shadow errors on surfaces with smooth shaded normals (terminator problem)
    # Type: boolean, default False

    # use_raytrace

    # Include this material and geometry that uses it in raytracing calculations
    # Type: boolean, default False

    # use_shadeless

    # Make this material insensitive to light or shadow
    # Type: boolean, default False

    # use_shadows

    # Allow this material to receive shadows
    # Type: boolean, default False

    # use_sky

    # Render this material with zero alpha, with sky background in place (scanline only)
    # Type: boolean, default False

    # use_specular_ramp

    # Toggle specular ramp operations
    # Type: boolean, default False

    # use_tangent_shading

    # Use the material’s tangent vector instead of the normal for shading - for anisotropic shading effects
    # Type: boolean, default False

    # use_textures

    # Enable/Disable each texture
    # Type: boolean array of 18 items, default (False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False, False)

    # use_transparency

    # Render material as transparent
    # Type: boolean, default False

    # use_transparent_shadows

    # Allow this object to receive transparent shadows cast through other objects
    # Type: boolean, default False

    # use_uv_project

    # Use to ensure UV interpolation is correct for camera projections (use with UV project modifier)
    # Type: boolean, default False

    # use_vertex_color_light

    # Add vertex colors as additional lighting
    # Type: boolean, default False

    # use_vertex_color_paint

    # Replace object base color with vertex colors (multiply with ‘texture face’ face assigned textures)
    # Type: boolean, default False

    # volume

    # Volume settings for the material
    # Type: MaterialVolume, (readonly, never None)
    """
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

    """


# ------------------------------ End Old Blender Internal Props ------------------------------ #


classes = (
    RenderPovSettingsMaterial,
    MaterialRaytraceTransparency,
    MaterialRaytraceMirror,
    MaterialSubsurfaceScattering,
    MaterialStrandSettings,
)


def register():
    for cls in classes:
        register_class(cls)

    bpy.types.Material.pov = PointerProperty(type=RenderPovSettingsMaterial)
    bpy.types.Material.pov_raytrace_transparency = PointerProperty(
        type=MaterialRaytraceTransparency
    )
    bpy.types.Material.pov_subsurface_scattering = PointerProperty(
        type=MaterialSubsurfaceScattering
    )
    bpy.types.Material.strand = PointerProperty(type=MaterialStrandSettings)
    bpy.types.Material.pov_raytrace_mirror = PointerProperty(type=MaterialRaytraceMirror)


def unregister():
    del bpy.types.Material.pov_subsurface_scattering
    del bpy.types.Material.strand
    del bpy.types.Material.pov_raytrace_mirror
    del bpy.types.Material.pov_raytrace_transparency
    del bpy.types.Material.pov

    for cls in reversed(classes):
        unregister_class(cls)

# SPDX-FileCopyrightText: 2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""Declare shading properties exported to POV textures."""
import bpy
from bpy.utils import register_class, unregister_class
from bpy.types import PropertyGroup
from bpy.props import (
    StringProperty,
    BoolProperty,
    FloatProperty,
    PointerProperty,
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

    # type

    # Material type defining how the object is rendered

    # SURFACE Surface, Render object as a surface.
    # WIRE Wire, Render the edges of faces as wires (not supported in raytracing).
    # VOLUME Volume, Render object as a volume.
    # HALO Halo, Render object as halo particles.

    # Type: enum in [‘SURFACE’, ‘WIRE’, ‘VOLUME’, ‘HALO’], default ‘SURFACE’

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



    mat.use_transparency and mat.pov.transparency_method == 'Z_TRANSPARENCY'




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

            if mat.pov.specular_shader in {'COOKTORR', 'PHONG'}:
                col.prop(mat, "specular_hardness", text="Hardness")
            elif mat.pov.specular_shader == 'BLINN':

                row.prop(mat, "specular_hardness", text="Hardness")
                row.prop(mat, "specular_ior", text="IOR")
            elif mat.pov.specular_shader == 'WARDISO':
                col.prop(mat, "specular_slope", text="Slope")
            elif mat.pov.specular_shader == 'TOON':

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


    XXX remove unused props and relayout as done for transparent sky


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
            halo = mat.pov.halo

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
            halo = context.material.pov.halo

            self.layout.prop(halo, "use_flare_mode", text="")

        def draw(self, context):
            layout = self.layout

            mat = context.material  # don't use node material
            halo = mat.pov.halo

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


classes = (
    MaterialStrandSettings,
)


def register():
    for cls in classes:
        register_class(cls)

    bpy.types.Material.strand = PointerProperty(type=MaterialStrandSettings)


def unregister():
    del bpy.types.Material.strand

    for cls in reversed(classes):
        unregister_class(cls)

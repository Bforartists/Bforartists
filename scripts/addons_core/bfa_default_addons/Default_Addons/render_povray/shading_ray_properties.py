# SPDX-FileCopyrightText: 2022 Blender Foundation
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
        description="Mirror color of the material",
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
    """Declare SSS/SSTL properties controllable in UI and translated to POV."""

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
        description="Scattering color",
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
        description="Mean red/green/blue scattering path length",
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

classes = (
    MaterialRaytraceTransparency,
    MaterialRaytraceMirror,
    MaterialSubsurfaceScattering,
)

def register():
    for cls in classes:
        register_class(cls)

    bpy.types.Material.pov_raytrace_transparency = PointerProperty(
        type=MaterialRaytraceTransparency
    )
    bpy.types.Material.pov_subsurface_scattering = PointerProperty(
        type=MaterialSubsurfaceScattering
    )
    bpy.types.Material.pov_raytrace_mirror = PointerProperty(type=MaterialRaytraceMirror)


def unregister():
    del bpy.types.Material.pov_subsurface_scattering
    del bpy.types.Material.pov_raytrace_mirror
    del bpy.types.Material.pov_raytrace_transparency

    for cls in reversed(classes):
        unregister_class(cls)

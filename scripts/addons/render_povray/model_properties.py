# SPDX-FileCopyrightText: 2021-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""Declare object level properties controllable in UI and translated to POV"""
import bpy
from bpy.utils import register_class, unregister_class
from bpy.types import PropertyGroup
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
# Object POV properties.
# ---------------------------------------------------------------- #


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
        options={"ANIMATABLE"},
        subtype="XYZ",
    )

    # Importance sampling
    importance_value: FloatProperty(
        name="Radiosity Importance",
        description="Priority value relative to other objects for sampling radiosity rays. "
        "Increase to get more radiosity rays at comparatively small yet "
        "bright objects",
        min=0.01,
        max=1.00,
        default=0.50,
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
        min=0.01,
        max=1.00,
        default=1.00,
    )

    # ----------------------------------- CustomPOV Code ----------------------------------- #
    # Only DUMMIES below for now:
    replacement_text: StringProperty(
        name="Declared name:",
        description="Type the declared name in custom POV code or an external .inc "
        "it points at. Any POV shape expected e.g: isosurface {}",
        default="",
    )

    # -------- POV specific object properties. -------- #
    object_as: StringProperty(maxlen=1024)

    imported_loc: FloatVectorProperty(
        name="Imported Pov location", precision=6, default=(0.0, 0.0, 0.0)
    )

    imported_loc_cap: FloatVectorProperty(
        name="Imported Pov location", precision=6, default=(0.0, 0.0, 2.0)
    )

    unlock_parameters: BoolProperty(name="Lock", default=False)

    # not in UI yet but used for sor (lathe) / prism... pov primitives
    curveshape: EnumProperty(
        name="Povray Shape Type",
        items=(
            ("birail", "Birail", ""),
            ("cairo", "Cairo", ""),
            ("lathe", "Lathe", ""),
            ("loft", "Loft", ""),
            ("prism", "Prism", ""),
            ("sphere_sweep", "Sphere Sweep", ""),
        ),
        default="sphere_sweep",
    )

    mesh_write_as: EnumProperty(
        name="Mesh Write As",
        items=(("blobgrid", "Blob Grid", ""), ("grid", "Grid", ""), ("mesh", "Mesh", "")),
        default="mesh",
    )

    object_ior: FloatProperty(name="IOR", description="IOR", min=1.0, max=10.0, default=1.0)

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
    no_shadow: BoolProperty(name="No Shadow", default=False)

    no_image: BoolProperty(name="No Image", default=False)

    no_reflection: BoolProperty(name="No Reflection", default=False)

    no_radiosity: BoolProperty(name="No Radiosity", default=False)

    inverse: BoolProperty(name="Inverse", default=False)

    sturm: BoolProperty(name="Sturm", default=False)

    double_illuminate: BoolProperty(name="Double Illuminate", default=False)

    hierarchy: BoolProperty(name="Hierarchy", default=False)

    hollow: BoolProperty(name="Hollow", default=False)

    boundorclip: EnumProperty(
        name="Boundorclip",
        items=(
            ("none", "None", ""),
            ("bounded_by", "Bounded_by", ""),
            ("clipped_by", "Clipped_by", ""),
        ),
        default="none",
    )

    boundorclipob: StringProperty(maxlen=1024)

    addboundorclip: BoolProperty(description="", default=False)

    blob_threshold: FloatProperty(name="Threshold", min=0.00, max=10.0, default=0.6)

    blob_strength: FloatProperty(name="Strength", min=-10.00, max=10.0, default=1.00)

    res_u: IntProperty(name="U", min=100, max=1000, default=500)

    res_v: IntProperty(name="V", min=100, max=1000, default=500)

    contained_by: EnumProperty(
        name="Contained by", items=(("box", "Box", ""), ("sphere", "Sphere", "")), default="box"
    )

    container_scale: FloatProperty(name="Container Scale", min=0.0, max=10.0, default=1.00)

    threshold: FloatProperty(name="Threshold", min=0.0, max=10.0, default=0.00)

    accuracy: FloatProperty(name="Accuracy", min=0.0001, max=0.1, default=0.001)

    max_gradient: FloatProperty(name="Max Gradient", min=0.0, max=100.0, default=5.0)

    all_intersections: BoolProperty(name="All Intersections", default=False)

    max_trace: IntProperty(name="Max Trace", min=1, max=100, default=1)

    # -------- Cylinder
    def prop_update_cylinder(self, context):
        """Update POV cylinder primitive parameters at creation and anytime they change in UI."""
        if bpy.ops.pov.cylinder_update.poll():
            bpy.ops.pov.cylinder_update()

    cylinder_radius: FloatProperty(
        name="Cylinder R", min=0.00, max=10.0, default=0.04, update=prop_update_cylinder
    )

    cylinder_location_cap: FloatVectorProperty(
        name="Cylinder Cap Location",
        subtype="TRANSLATION",
        description="Position of the 'other' end of the cylinder (relative to object location)",
        default=(0.0, 0.0, 2.0),
        update=prop_update_cylinder,
    )

    imported_cyl_loc: FloatVectorProperty(
        name="Imported Pov location", precision=6, default=(0.0, 0.0, 0.0)
    )

    imported_cyl_loc_cap: FloatVectorProperty(
        name="Imported Pov location", precision=6, default=(0.0, 0.0, 2.0)
    )

    # -------- Sphere
    def prop_update_sphere(self, context):

        """Update POV sphere primitive parameters at creation and anytime they change in UI."""

        if bpy.ops.pov.sphere_update.poll():
            bpy.ops.pov.sphere_update()

    sphere_radius: FloatProperty(
        name="Sphere radius", min=0.00, max=10.0, default=0.5, update=prop_update_sphere
    )

    # -------- Cone
    def prop_update_cone(self, context):

        """Update POV cone primitive parameters at creation and anytime they change in UI."""

        if bpy.ops.pov.cone_update.poll():
            bpy.ops.pov.cone_update()

    cone_base_radius: FloatProperty(
        name="Base radius",
        description="The first radius of the cone",
        default=1.0,
        min=0.01,
        max=100.0,
        update=prop_update_cone,
    )

    cone_cap_radius: FloatProperty(
        name="Cap radius",
        description="The second radius of the cone",
        default=0.3,
        min=0.0,
        max=100.0,
        update=prop_update_cone,
    )

    cone_segments: IntProperty(
        name="Segments",
        description="Radial segmentation of proxy mesh",
        default=16,
        min=3,
        max=265,
        update=prop_update_cone,
    )

    cone_height: FloatProperty(
        name="Height",
        description="Height of the cone",
        default=2.0,
        min=0.01,
        max=100.0,
        update=prop_update_cone,
    )

    cone_base_z: FloatProperty()

    cone_cap_z: FloatProperty()
    # -------- Generic isosurface
    isosurface_eq: StringProperty(
        name="f (x,y,z)=",
        description="Type the POV Isosurface function syntax for equation, "
        "pattern,etc. ruling an implicit surface to be rendered",
        default="sqrt(pow(x,2) + pow(y,2) + pow(z,2)) - 1.5",
    )
    # -------- Parametric
    def prop_update_parametric(self, context):

        """Update POV parametric surface primitive settings at creation and on any UI change."""

        if bpy.ops.pov.parametric_update.poll():
            bpy.ops.pov.parametric_update()

    u_min: FloatProperty(name="U Min", description="", default=0.0, update=prop_update_parametric)

    v_min: FloatProperty(name="V Min", description="", default=0.0, update=prop_update_parametric)

    u_max: FloatProperty(name="U Max", description="", default=6.28, update=prop_update_parametric)

    v_max: FloatProperty(name="V Max", description="", default=12.57, update=prop_update_parametric)

    x_eq: StringProperty(
        maxlen=1024, default="cos(v)*(1+cos(u))*sin(v/8)", update=prop_update_parametric
    )

    y_eq: StringProperty(
        maxlen=1024, default="sin(u)*sin(v/8)+cos(v/8)*1.5", update=prop_update_parametric
    )

    z_eq: StringProperty(
        maxlen=1024, default="sin(v)*(1+cos(u))*sin(v/8)", update=prop_update_parametric
    )

    # -------- Torus

    def prop_update_torus(self, context):

        """Update POV torus primitive parameters at creation and anytime they change in UI."""

        if bpy.ops.pov.torus_update.poll():
            bpy.ops.pov.torus_update()

    torus_major_segments: IntProperty(
        name="Segments",
        description="Radial segmentation of proxy mesh",
        default=48,
        min=3,
        max=720,
        update=prop_update_torus,
    )

    torus_minor_segments: IntProperty(
        name="Segments",
        description="Cross-section segmentation of proxy mesh",
        default=12,
        min=3,
        max=720,
        update=prop_update_torus,
    )

    torus_major_radius: FloatProperty(
        name="Major radius",
        description="Major radius",
        min=0.00,
        max=100.00,
        default=1.0,
        update=prop_update_torus,
    )

    torus_minor_radius: FloatProperty(
        name="Minor radius",
        description="Minor radius",
        min=0.00,
        max=100.00,
        default=0.25,
        update=prop_update_torus,
    )

    # -------- Rainbow
    arc_angle: FloatProperty(
        name="Arc angle",
        description="The angle of the raynbow arc in degrees",
        default=360,
        min=0.01,
        max=360.0,
    )

    falloff_angle: FloatProperty(
        name="Falloff angle",
        description="The angle after which rainbow dissolves into background",
        default=360,
        min=0.0,
        max=360,
    )

    # -------- HeightFields

    quality: IntProperty(name="Quality", description="", default=100, min=1, max=100)

    hf_filename: StringProperty(maxlen=1024)

    hf_gamma: FloatProperty(name="Gamma", description="Gamma", min=0.0001, max=20.0, default=1.0)

    hf_premultiplied: BoolProperty(name="Premultiplied", description="Premultiplied", default=True)

    hf_smooth: BoolProperty(name="Smooth", description="Smooth", default=False)

    hf_water: FloatProperty(
        name="Water Level", description="Wather Level", min=0.00, max=1.00, default=0.0
    )

    hf_hierarchy: BoolProperty(name="Hierarchy", description="Height field hierarchy", default=True)

    # -------- Superellipsoid
    def prop_update_superellipsoid(self, context):

        """Update POV superellipsoid primitive settings at creation and on any UI change."""

        if bpy.ops.pov.superellipsoid_update.poll():
            bpy.ops.pov.superellipsoid_update()

    se_param1: FloatProperty(name="Parameter 1", description="", min=0.00, max=10.0, default=0.04)

    se_param2: FloatProperty(name="Parameter 2", description="", min=0.00, max=10.0, default=0.04)

    se_u: IntProperty(
        name="U-segments",
        description="radial segmentation",
        default=20,
        min=4,
        max=265,
        update=prop_update_superellipsoid,
    )

    se_v: IntProperty(
        name="V-segments",
        description="lateral segmentation",
        default=20,
        min=4,
        max=265,
        update=prop_update_superellipsoid,
    )

    se_n1: FloatProperty(
        name="Ring manipulator",
        description="Manipulates the shape of the Ring",
        default=1.0,
        min=0.01,
        max=100.0,
        update=prop_update_superellipsoid,
    )

    se_n2: FloatProperty(
        name="Cross manipulator",
        description="Manipulates the shape of the cross-section",
        default=1.0,
        min=0.01,
        max=100.0,
        update=prop_update_superellipsoid,
    )

    se_edit: EnumProperty(
        items=[("NOTHING", "Nothing", ""), ("NGONS", "N-Gons", ""), ("TRIANGLES", "Triangles", "")],
        name="Fill up and down",
        description="",
        default="TRIANGLES",
        update=prop_update_superellipsoid,
    )

    # -------- Used for loft but also Superellipsoid, etc.
    curveshape: EnumProperty(
        name="Povray Shape Type",
        items=(
            ("birail", "Birail", ""),
            ("cairo", "Cairo", ""),
            ("lathe", "Lathe", ""),
            ("loft", "Loft", ""),
            ("prism", "Prism", ""),
            ("sphere_sweep", "Sphere Sweep", ""),
            ("sor", "Surface of Revolution", ""),
        ),
        default="sphere_sweep",
    )

    # -------- Supertorus
    def prop_update_supertorus(self, context):

        """Update POV supertorus primitive parameters not only at creation and on any UI change."""

        if bpy.ops.pov.supertorus_update.poll():
            bpy.ops.pov.supertorus_update()

    st_major_radius: FloatProperty(
        name="Major radius",
        description="Major radius",
        min=0.00,
        max=100.00,
        default=1.0,
        update=prop_update_supertorus,
    )

    st_minor_radius: FloatProperty(
        name="Minor radius",
        description="Minor radius",
        min=0.00,
        max=100.00,
        default=0.25,
        update=prop_update_supertorus,
    )

    st_ring: FloatProperty(
        name="Ring",
        description="Ring manipulator",
        min=0.0001,
        max=100.00,
        default=1.00,
        update=prop_update_supertorus,
    )

    st_cross: FloatProperty(
        name="Cross",
        description="Cross manipulator",
        min=0.0001,
        max=100.00,
        default=1.00,
        update=prop_update_supertorus,
    )

    st_accuracy: FloatProperty(
        name="Accuracy", description="Supertorus accuracy", min=0.00001, max=1.00, default=0.001
    )

    st_max_gradient: FloatProperty(
        name="Gradient",
        description="Max gradient",
        min=0.0001,
        max=100.00,
        default=10.00,
        update=prop_update_supertorus,
    )

    st_R: FloatProperty(
        name="big radius",
        description="The radius inside the tube",
        default=1.0,
        min=0.01,
        max=100.0,
        update=prop_update_supertorus,
    )

    st_r: FloatProperty(
        name="small radius",
        description="The radius of the tube",
        default=0.3,
        min=0.01,
        max=100.0,
        update=prop_update_supertorus,
    )

    st_u: IntProperty(
        name="U-segments",
        description="radial segmentation",
        default=16,
        min=3,
        max=265,
        update=prop_update_supertorus,
    )

    st_v: IntProperty(
        name="V-segments",
        description="lateral segmentation",
        default=8,
        min=3,
        max=265,
        update=prop_update_supertorus,
    )

    st_n1: FloatProperty(
        name="Ring manipulator",
        description="Manipulates the shape of the Ring",
        default=1.0,
        min=0.01,
        max=100.0,
        update=prop_update_supertorus,
    )

    st_n2: FloatProperty(
        name="Cross manipulator",
        description="Manipulates the shape of the cross-section",
        default=1.0,
        min=0.01,
        max=100.0,
        update=prop_update_supertorus,
    )

    st_ie: BoolProperty(
        name="Use Int.+Ext. radii",
        description="Use internal and external radii",
        default=False,
        update=prop_update_supertorus,
    )

    st_edit: BoolProperty(
        name="", description="", default=False, options={"HIDDEN"}, update=prop_update_supertorus
    )

    # -------- Loft
    loft_n: IntProperty(
        name="Segments", description="Vertical segments", default=16, min=3, max=720
    )

    loft_rings_bottom: IntProperty(
        name="Bottom", description="Bottom rings", default=5, min=2, max=100
    )

    loft_rings_side: IntProperty(name="Side", description="Side rings", default=10, min=2, max=100)

    loft_thick: FloatProperty(
        name="Thickness",
        description="Manipulates the shape of the Ring",
        default=0.3,
        min=0.01,
        max=1.0,
    )

    loft_r: FloatProperty(name="Radius", description="Radius", default=1, min=0.01, max=10)

    loft_height: FloatProperty(
        name="Height",
        description="Manipulates the shape of the Ring",
        default=2,
        min=0.01,
        max=10.0,
    )

    # -------- Prism
    prism_n: IntProperty(name="Sides", description="Number of sides", default=5, min=3, max=720)

    prism_r: FloatProperty(name="Radius", description="Radius", default=1.0)

    # -------- Isosurface
    iso_function_text: StringProperty(
        name="Function Text", maxlen=1024
    )  # ,update=iso_props_update_callback)

    # -------- PolygonToCircle
    polytocircle_resolution: IntProperty(
        name="Resolution", description="", default=3, min=0, max=256
    )

    polytocircle_ngon: IntProperty(name="NGon", description="", min=3, max=64, default=5)

    polytocircle_ngonR: FloatProperty(name="NGon Radius", description="", default=0.3)

    polytocircle_circleR: FloatProperty(name="Circle Radius", description="", default=1.0)

    # ---------------------------------------------------------------- #
    # Modifiers POV properties.
    # ---------------------------------------------------------------- #
    # class RenderPovSettingsModifier(PropertyGroup):
    boolean_mod: EnumProperty(
        name="Operation",
        description="Choose the type of calculation for Boolean modifier",
        items=(
            ("BMESH", "Use the BMesh Boolean Solver", ""),
            ("CARVE", "Use the Carve Boolean Solver", ""),
            ("POV", "Use POV Constructive Solid Geometry", ""),
        ),
        default="BMESH",
    )

    # -------- Avogadro
    # filename_ext = ".png"

    # filter_glob = StringProperty(
    # default="*.exr;*.gif;*.hdr;*.iff;*.jpeg;*.jpg;*.pgm;*.png;*.pot;*.ppm;*.sys;*.tga;*.tiff;*.EXR;*.GIF;*.HDR;*.IFF;*.JPEG;*.JPG;*.PGM;*.PNG;*.POT;*.PPM;*.SYS;*.TGA;*.TIFF",
    # options={'HIDDEN'},
    # )


classes = (RenderPovSettingsObject,)


def register():
    for cls in classes:
        register_class(cls)
    bpy.types.Object.pov = PointerProperty(type=RenderPovSettingsObject)


def unregister():
    del bpy.types.Object.pov
    for cls in reversed(classes):
        unregister_class(cls)

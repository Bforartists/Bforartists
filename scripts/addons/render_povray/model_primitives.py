# SPDX-FileCopyrightText: 2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

""" Get POV-Ray specific objects In and Out of Blender """
from math import pi, cos, sin
import os.path
import bpy
from bpy_extras.object_utils import object_data_add
from bpy_extras.io_utils import ImportHelper
from bpy.utils import register_class, unregister_class
from bpy.types import Operator

from bpy.props import (
    StringProperty,
    BoolProperty,
    IntProperty,
    FloatProperty,
    FloatVectorProperty,
    EnumProperty,
)

from mathutils import Vector, Matrix


# import collections


def write_object_modifiers(ob, File):
    """Translate some object level POV statements from Blender UI
    to POV syntax and write to exported file"""

    # Maybe return that string to be added instead of directly written.

    """XXX WIP
    # import .model_all.write_object_csg_inside_vector
    write_object_csg_inside_vector(ob, file)
    """

    if ob.pov.hollow:
        File.write("\thollow\n")
    if ob.pov.double_illuminate:
        File.write("\tdouble_illuminate\n")
    if ob.pov.sturm:
        File.write("\tsturm\n")
    if ob.pov.no_shadow:
        File.write("\tno_shadow\n")
    if ob.pov.no_image:
        File.write("\tno_image\n")
    if ob.pov.no_reflection:
        File.write("\tno_reflection\n")
    if ob.pov.no_radiosity:
        File.write("\tno_radiosity\n")
    if ob.pov.inverse:
        File.write("\tinverse\n")
    if ob.pov.hierarchy:
        File.write("\thierarchy\n")

    # XXX, Commented definitions
    """
    if scene.pov.photon_enable:
        File.write("photons {\n")
        if ob.pov.target:
            File.write("target %.4g\n"%ob.pov.target_value)
        if ob.pov.refraction:
            File.write("refraction on\n")
        if ob.pov.reflection:
            File.write("reflection on\n")
        if ob.pov.pass_through:
            File.write("pass_through\n")
        File.write("}\n")
    if ob.pov.object_ior > 1:
        File.write("interior {\n")
        File.write("ior %.4g\n"%ob.pov.object_ior)
        if scene.pov.photon_enable and ob.pov.target and ob.pov.refraction and ob.pov.dispersion:
            File.write("ior %.4g\n"%ob.pov.dispersion_value)
            File.write("ior %s\n"%ob.pov.dispersion_samples)
        if scene.pov.photon_enable == False:
            File.write("caustics %.4g\n"%ob.pov.fake_caustics_power)
    """


def pov_define_mesh(mesh, verts, edges, faces, name, hide_geometry=True):
    """Generate proxy mesh."""
    if mesh is None:
        mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, edges, faces)
    # Function Arguments change : now bpy.types.Mesh.update (calc_edges, calc_edges_loose,
    # calc_loop_triangles), was (calc_edges, calc_tessface)


    mesh.update()
    mesh.validate(
        verbose=False
    )  # Set it to True to see debug messages (helps ensure you generate valid geometry).
    if hide_geometry:
        mesh.vertices.foreach_set("hide", [True] * len(mesh.vertices))
        mesh.edges.foreach_set("hide", [True] * len(mesh.edges))
        mesh.polygons.foreach_set("hide", [True] * len(mesh.polygons))
    return mesh


class POV_OT_plane_add(Operator):
    """Add the representation of POV infinite plane using just a very big Blender Plane.

    Flag its primitive type with a specific pov.object_as attribute and lock edit mode
    to keep proxy consistency by hiding edit geometry."""

    bl_idname = "pov.addplane"
    bl_label = "Plane"
    bl_description = "Add Plane"
    bl_options = {'REGISTER', 'UNDO'}
    COMPAT_ENGINES = {"POVRAY_RENDER"}

    def execute(self, context):
        # layers = 20*[False]
        # layers[0] = True
        bpy.ops.mesh.primitive_plane_add(size=10000)
        ob = context.object
        ob.name = ob.data.name = "PovInfinitePlane"
        bpy.ops.object.mode_set(mode="EDIT")
        self.report(
            {"INFO"}, "This native POV-Ray primitive " "won't have any vertex to show in edit mode"
        )
        bpy.ops.mesh.hide(unselected=False)
        bpy.ops.object.mode_set(mode="OBJECT")
        bpy.ops.object.shade_smooth()
        ob.pov.object_as = "PLANE"
        ob.update_tag() # as prop set via python not updated in depsgraph
        return {"FINISHED"}


class POV_OT_box_add(Operator):
    """Add the representation of POV box using a simple Blender mesh cube.

    Flag its primitive type with a specific pov.object_as attribute and lock edit mode
    to keep proxy consistency by hiding edit geometry."""

    bl_idname = "pov.addbox"
    bl_label = "Box"
    bl_description = "Add Box"
    bl_options = {'REGISTER', 'UNDO'}
    COMPAT_ENGINES = {"POVRAY_RENDER"}

    def execute(self, context):
        # layers = 20*[False]
        # layers[0] = True
        bpy.ops.mesh.primitive_cube_add()
        ob = context.object
        ob.name = ob.data.name = "PovBox"
        bpy.ops.object.mode_set(mode="EDIT")
        self.report(
            {"INFO"}, "This native POV-Ray primitive " "won't have any vertex to show in edit mode"
        )
        bpy.ops.mesh.hide(unselected=False)
        bpy.ops.object.mode_set(mode="OBJECT")
        ob.pov.object_as = "BOX"
        ob.update_tag() # as prop set via python not updated in depsgraph
        return {"FINISHED"}


def pov_cylinder_define(context, op, ob, radius, loc, loc_cap):
    """Pick POV cylinder properties either from creation operator, import, or data update"""
    if op:
        cy_rad = op.cy_rad
        loc = bpy.context.scene.cursor.location
        loc_cap[0] = loc[0]
        loc_cap[1] = loc[1]
        loc_cap[2] = loc[2] + 2
    vec = Vector(loc_cap) - Vector(loc)
    depth = vec.length
    rot = Vector((0, 0, 1)).rotation_difference(vec)  # Rotation from Z axis.
    trans = rot @ Vector(
        (0, 0, depth / 2)
    )  # Such that origin is at center of the base of the cylinder.
    roteuler = rot.to_euler()
    if not ob:
        bpy.ops.object.add(type="MESH", location=loc)
        ob = context.object
        ob.name = ob.data.name = "PovCylinder"
        ob.pov.cylinder_radius = radius
        ob.pov.cylinder_location_cap = vec
        ob.data.use_auto_smooth = True
        ob.pov.object_as = "CYLINDER"
        ob.update_tag() # as prop set via python not updated in depsgraph

    else:
        ob.location = loc

    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.reveal()
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.delete(type="VERT")
    bpy.ops.mesh.primitive_cylinder_add(
        radius=radius, depth=depth, location=loc, rotation=roteuler, end_fill_type="NGON"
    )  # 'NOTHING'
    bpy.ops.transform.translate(value=trans)

    bpy.ops.mesh.hide(unselected=False)
    bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.shade_smooth()


class POV_OT_cylinder_add(Operator):
    """Add the representation of POV cylinder using pov_cylinder_define() function.

    Use imported_cyl_loc when this operator is run by POV importer."""
    bl_options = {'REGISTER', 'UNDO'}
    bl_idname = "pov.addcylinder"
    bl_label = "Cylinder"
    bl_description = "Add Cylinder"

    COMPAT_ENGINES = {"POVRAY_RENDER"}

    # Keep in sync within model_properties.py section Cylinder
    # as this allows interactive update
    cy_rad: FloatProperty(name="Cylinder radius", min=0.00, max=10.0, default=1.0)

    imported_cyl_loc: FloatVectorProperty(
        name="Imported Pov base location", precision=6, default=(0.0, 0.0, 0.0)
    )

    imported_cyl_loc_cap: FloatVectorProperty(
        name="Imported Pov cap location", precision=6, default=(0.0, 0.0, 2.0)
    )

    def execute(self, context):
        props = self.properties
        cy_rad = props.cy_rad
        if ob := context.object:
            if ob.pov.imported_cyl_loc:
                LOC = ob.pov.imported_cyl_loc
            if ob.pov.imported_cyl_loc_cap:
                LOC_CAP = ob.pov.imported_cyl_loc_cap
        elif not props.imported_cyl_loc:
            LOC_CAP = LOC = bpy.context.scene.cursor.location
            LOC_CAP[2] += 2.0
        else:
            LOC = props.imported_cyl_loc
            LOC_CAP = props.imported_cyl_loc_cap
            self.report(
                {"INFO"},
                "This native POV-Ray primitive " "won't have any vertex to show in edit mode",
            )

        pov_cylinder_define(context, self, None, self.cy_rad, LOC, LOC_CAP)

        return {"FINISHED"}


class POV_OT_cylinder_update(Operator):
    """Update the POV cylinder.

    Delete its previous proxy geometry and rerun pov_cylinder_define() function
    with the new parameters"""

    bl_idname = "pov.cylinder_update"
    bl_label = "Update"
    bl_description = "Update Cylinder"
    bl_options = {'REGISTER', 'UNDO'}
    COMPAT_ENGINES = {"POVRAY_RENDER"}

    @classmethod
    def poll(cls, context):
        engine = context.scene.render.engine
        ob = context.object
        return (
            ob
            and ob.data
            and ob.type == "MESH"
            and ob.pov.object_as == "CYLINDER"
            and engine in cls.COMPAT_ENGINES
        )

    def execute(self, context):
        ob = context.object
        radius = ob.pov.cylinder_radius
        loc = ob.location
        loc_cap = loc + ob.pov.cylinder_location_cap

        pov_cylinder_define(context, None, ob, radius, loc, loc_cap)

        return {"FINISHED"}


# ----------------------------------- SPHERE---------------------------------- #
def pov_sphere_define(context, op, ob, loc):
    """create the representation of POV sphere using a Blender icosphere.

    Its nice platonic solid curvature better represents pov rendertime
    tessellation than a UV sphere"""

    if op:
        sphe_rad = op.sphe_rad
        loc = bpy.context.scene.cursor.location
    else:
        assert ob
        sphe_rad = ob.pov.sphere_radius

        # keep object rotation and location for the add object operator
        obrot = ob.rotation_euler
        # obloc = ob.location
        obscale = ob.scale

        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.reveal()
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.mesh.delete(type="VERT")
        bpy.ops.mesh.primitive_ico_sphere_add(
            subdivisions=4, radius=ob.pov.sphere_radius, location=loc, rotation=obrot
        )
        # bpy.ops.transform.rotate(axis=obrot,orient_type='GLOBAL')
        bpy.ops.transform.resize(value=obscale)
        # bpy.ops.transform.rotate(axis=obrot, proportional_size=1)

        bpy.ops.mesh.hide(unselected=False)
        bpy.ops.object.mode_set(mode="OBJECT")

        # bpy.ops.transform.rotate(axis=obrot,orient_type='GLOBAL')

    if not ob:
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=4, radius=sphe_rad, location=loc)
        ob = context.object
        ob.name = ob.data.name = "PovSphere"
        ob.pov.sphere_radius = sphe_rad
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.hide(unselected=False)
        bpy.ops.object.mode_set(mode="OBJECT")
        ob.data.use_auto_smooth = True
        bpy.ops.object.shade_smooth()
        ob.pov.object_as = "SPHERE"
        ob.update_tag() # as prop set via python not updated in depsgraph


class POV_OT_sphere_add(Operator):
    """Add the representation of POV sphere using pov_sphere_define() function.

    Use imported_loc when this operator is run by POV importer."""

    bl_idname = "pov.addsphere"
    bl_label = "Sphere"
    bl_description = "Add Sphere Shape"
    bl_options = {'REGISTER', 'UNDO'}
    COMPAT_ENGINES = {"POVRAY_RENDER"}

    # Keep in sync within model_properties.py section Sphere
    # as this allows interactive update
    sphe_rad: FloatProperty(name="Sphere radius", min=0.00, max=10.0, default=0.5)

    imported_loc: FloatVectorProperty(
        name="Imported Pov location", precision=6, default=(0.0, 0.0, 0.0)
    )

    def execute(self, context):
        props = self.properties
        sphe_rad = props.sphe_rad
        if ob := context.object:
            if ob.pov.imported_loc:
                LOC = ob.pov.imported_loc
        elif not props.imported_loc:
            LOC = bpy.context.scene.cursor.location

        else:
            LOC = props.imported_loc
            self.report(
                {"INFO"},
                "This native POV-Ray primitive " "won't have any vertex to show in edit mode",
            )
        pov_sphere_define(context, self, None, LOC)

        return {"FINISHED"}

    # def execute(self,context):
    #  layers = 20*[False]
    #  layers[0] = True

    # bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=4, radius=ob.pov.sphere_radius)
    # ob = context.object
    # bpy.ops.object.mode_set(mode="EDIT")
    # self.report({'INFO'}, "This native POV-Ray primitive "
    # "won't have any vertex to show in edit mode")
    # bpy.ops.mesh.hide(unselected=False)
    # bpy.ops.object.mode_set(mode="OBJECT")
    # bpy.ops.object.shade_smooth()
    # ob.pov.object_as = "SPHERE"
    # ob.update_tag() # as prop set via python not updated in depsgraph
    # ob.name = ob.data.name = 'PovSphere'
    # return {'FINISHED'}


class POV_OT_sphere_update(Operator):
    """Update the POV sphere.

    Delete its previous proxy geometry and rerun pov_sphere_define() function
    with the new parameters"""

    bl_idname = "pov.sphere_update"
    bl_label = "Update"
    bl_description = "Update Sphere"
    bl_options = {'REGISTER', 'UNDO'}
    COMPAT_ENGINES = {"POVRAY_RENDER"}

    @classmethod
    def poll(cls, context):
        engine = context.scene.render.engine
        ob = context.object
        return (
            ob
            and ob.data
            and ob.type == "MESH"
            and ob.pov.object_as == "SPHERE"
            and engine in cls.COMPAT_ENGINES
        )
    def execute(self, context):

        pov_sphere_define(context, None, context.object, context.object.location)

        return {"FINISHED"}


# ----------------------------------- CONE ---------------------------------- #
def pov_cone_define(context, op, ob):
    """Add the representation of POV cone using pov_define_mesh() function.

    Blender cone does not offer the same features such as a second radius."""
    verts = []
    faces = []
    if op:
        mesh = None
        base = op.base
        cap = op.cap
        seg = op.seg
        height = op.height
    else:
        assert ob
        mesh = ob.data
        base = ob.pov.cone_base_radius
        cap = ob.pov.cone_cap_radius
        seg = ob.pov.cone_segments
        height = ob.pov.cone_height

    zc = height / 2
    zb = -zc
    angle = 2 * pi / seg
    t = 0
    for i in range(seg):
        xb = base * cos(t)
        yb = base * sin(t)
        xc = cap * cos(t)
        yc = cap * sin(t)
        verts.extend([(xb, yb, zb), (xc, yc, zc)])
        t += angle
    for i in range(seg):
        f = i * 2
        if i == seg - 1:
            faces.append([0, 1, f + 1, f])
        else:
            faces.append([f + 2, f + 3, f + 1, f])
    if base != 0:
        base_face = [i * 2 for i in range(seg - 1, -1, -1)]
        faces.append(base_face)
    if cap != 0:
        cap_face = [i * 2 + 1 for i in range(seg)]
        faces.append(cap_face)

    mesh = pov_define_mesh(mesh, verts, [], faces, "PovCone", True)
    if not ob:
        ob = object_data_add(context, mesh, operator=None)
        ob.pov.cone_base_radius = base
        ob.pov.cone_cap_radius = cap
        ob.pov.cone_height = height
        ob.pov.cone_base_z = zb
        ob.pov.cone_cap_z = zc
        ob.data.use_auto_smooth = True
        bpy.ops.object.shade_smooth()
        ob.pov.object_as = "CONE"
        ob.update_tag() # as prop set via python not updated in depsgraph

class POV_OT_cone_add(Operator):
    """Add the representation of POV cone using pov_cone_define() function."""

    bl_idname = "pov.addcone"
    bl_label = "Cone"
    bl_description = "Add Cone"
    bl_options = {'REGISTER', 'UNDO'}
    COMPAT_ENGINES = {"POVRAY_RENDER"}

    # Keep in sync within model_properties.py section Cone
    #     If someone knows how to define operators' props from a func, I'd be delighted to learn it!
    base: FloatProperty(
        name="Base radius",
        description="The first radius of the cone",
        default=1.0,
        min=0.01,
        max=100.0,
    )
    cap: FloatProperty(
        name="Cap radius",
        description="The second radius of the cone",
        default=0.3,
        min=0.0,
        max=100.0,
    )
    seg: IntProperty(
        name="Segments",
        description="Radial segmentation of the proxy mesh",
        default=16,
        min=3,
        max=265,
    )
    height: FloatProperty(
        name="Height", description="Height of the cone", default=2.0, min=0.01, max=100.0
    )

    @classmethod
    def poll(cls, context):
        engine = context.scene.render.engine
        return engine in cls.COMPAT_ENGINES

    def execute(self, context):
        pov_cone_define(context, self, None)

        self.report(
            {"INFO"}, "This native POV-Ray primitive" "won't have any vertex to show in edit mode"
        )
        return {"FINISHED"}


class POV_OT_cone_update(Operator):
    """Update the POV cone.

    Delete its previous proxy geometry and rerun pov_cone_define() function
    with the new parameters"""

    bl_idname = "pov.cone_update"
    bl_label = "Update"
    bl_description = "Update Cone"
    bl_options = {'REGISTER', 'UNDO'}
    COMPAT_ENGINES = {"POVRAY_RENDER"}

    @classmethod
    def poll(cls, context):
        engine = context.scene.render.engine
        ob = context.object

        return (
            ob
            and ob.data
            and ob.type == "MESH"
            and ob.pov.object_as == "CONE"
            and engine in cls.COMPAT_ENGINES
        )
    def execute(self, context):
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.reveal()
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.mesh.delete(type="VERT")
        bpy.ops.object.mode_set(mode="OBJECT")

        pov_cone_define(context, None, context.object)

        return {"FINISHED"}


class POV_OT_rainbow_add(Operator):
    """Add the representation of POV rainbow using a Blender spot light.

    Rainbows indeed propagate along a visibility cone.
    Flag its primitive type with a specific ob.pov.object_as attribute
    and leave access to edit mode to keep user editable handles.
    Add a constraint to orient it towards camera because POV Rainbows
    are view dependant and having it always initially visible is less
    confusing"""

    bl_idname = "pov.addrainbow"
    bl_label = "Rainbow"
    bl_description = "Add Rainbow"
    bl_options = {'REGISTER', 'UNDO'}
    COMPAT_ENGINES = {"POVRAY_RENDER"}

    def execute(self, context):
        cam = context.scene.camera
        bpy.ops.object.light_add(type="SPOT", radius=1)
        ob = context.object
        ob.data.show_cone = False
        ob.data.spot_blend = 0.5
        # ob.data.shadow_buffer_clip_end = 0 # deprecated in 2.8
        ob.data.shadow_buffer_clip_start = 4 * cam.location.length
        ob.data.distance = cam.location.length
        ob.data.energy = 0
        ob.name = ob.data.name = "PovRainbow"
        ob.pov.object_as = "RAINBOW"
        ob.update_tag() # as prop set via python not updated in depsgraph

        # obj = context.object
        bpy.ops.object.constraint_add(type="DAMPED_TRACK")

        ob.constraints["Damped Track"].target = cam
        ob.constraints["Damped Track"].track_axis = "TRACK_NEGATIVE_Z"
        ob.location = -cam.location

        # refocus on the actual rainbow
        bpy.context.view_layer.objects.active = ob
        ob.select_set(True)

        return {"FINISHED"}


# ----------------------------------- TORUS ----------------------------------- #
def pov_torus_define(context, op, ob):
    """Add the representation of POV torus using just a Blender torus.

    Picking properties either from creation operator, import, or data update.
    But flag its primitive type with a specific pov.object_as attribute and lock edit mode
    to keep proxy consistency by hiding edit geometry."""

    if op:
        mas = op.mas
        mis = op.mis
        mar = op.mar
        mir = op.mir
    else:
        assert ob
        mas = ob.pov.torus_major_segments
        mis = ob.pov.torus_minor_segments
        mar = ob.pov.torus_major_radius
        mir = ob.pov.torus_minor_radius

        # keep object rotation and location for the add object operator
        obrot = ob.rotation_euler
        obloc = ob.location

        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.reveal()
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.mesh.delete(type="VERT")
        bpy.ops.mesh.primitive_torus_add(
            rotation=obrot,
            location=obloc,
            major_segments=mas,
            minor_segments=mis,
            major_radius=mar,
            minor_radius=mir,
        )

        bpy.ops.mesh.hide(unselected=False)
        bpy.ops.object.mode_set(mode="OBJECT")

    if not ob:
        bpy.ops.mesh.primitive_torus_add(
            major_segments=mas, minor_segments=mis, major_radius=mar, minor_radius=mir
        )
        ob = context.object
        ob.name = ob.data.name = "PovTorus"
        ob.pov.torus_major_segments = mas
        ob.pov.torus_minor_segments = mis
        ob.pov.torus_major_radius = mar
        ob.pov.torus_minor_radius = mir
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.hide(unselected=False)
        bpy.ops.object.mode_set(mode="OBJECT")
        ob.data.use_auto_smooth = True
        ob.data.auto_smooth_angle = 0.6
        bpy.ops.object.shade_smooth()
        ob.pov.object_as = "TORUS"
        ob.update_tag() # as prop set via python not updated in depsgraph

class POV_OT_torus_add(Operator):
    """Add the representation of POV torus using using pov_torus_define() function."""

    bl_idname = "pov.addtorus"
    bl_label = "Torus"
    bl_description = "Add Torus"
    bl_options = {'REGISTER', 'UNDO'}
    COMPAT_ENGINES = {"POVRAY_RENDER"}

    # Keep in sync within model_properties.py section Torus
    # as this allows interactive update
    mas: IntProperty(name="Major Segments", description="", default=48, min=3, max=720)
    mis: IntProperty(name="Minor Segments", description="", default=12, min=3, max=720)
    mar: FloatProperty(name="Major Radius", description="", default=1.0)
    mir: FloatProperty(name="Minor Radius", description="", default=0.25)

    def execute(self, context):
        props = self.properties
        mar = props.mar
        mir = props.mir
        mas = props.mas
        mis = props.mis
        pov_torus_define(context, self, None)
        self.report(
            {"INFO"}, "This native POV-Ray primitive " "won't have any vertex to show in edit mode"
        )
        return {"FINISHED"}


class POV_OT_torus_update(Operator):
    """Update the POV torus.

    Delete its previous proxy geometry and rerun pov_torus_define() function
    with the new parameters"""

    bl_idname = "pov.torus_update"
    bl_label = "Update"
    bl_description = "Update Torus"
    bl_options = {'REGISTER', 'UNDO'}
    COMPAT_ENGINES = {"POVRAY_RENDER"}

    @classmethod
    def poll(cls, context):
        engine = context.scene.render.engine
        ob = context.object
        return (
            ob
            and ob.data
            and ob.type == "MESH"
            and ob.pov.object_as == "TORUS"
            and engine in cls.COMPAT_ENGINES
        )

    def execute(self, context):

        pov_torus_define(context, None, context.object)

        return {"FINISHED"}


# -----------------------------------------------------------------------------


class POV_OT_prism_add(Operator):
    """Add the representation of POV prism using using an extruded curve."""

    bl_idname = "pov.addprism"
    bl_label = "Prism"
    bl_description = "Create Prism"
    bl_options = {'REGISTER', 'UNDO'}
    COMPAT_ENGINES = {"POVRAY_RENDER"}

    prism_n: IntProperty(name="Sides", description="Number of sides", default=5, min=3, max=720)
    prism_r: FloatProperty(name="Radius", description="Radius", default=1.0)

    def execute(self, context):

        props = self.properties
        loft_data = bpy.data.curves.new("Prism", type="CURVE")
        loft_data.dimensions = "2D"
        loft_data.resolution_u = 2
        # loft_data.show_normal_face = False
        loft_data.extrude = 2
        n = props.prism_n
        r = props.prism_r
        coords = []
        z = 0
        angle = 0
        for p in range(n):
            x = r * cos(angle)
            y = r * sin(angle)
            coords.append((x, y, z))
            angle += pi * 2 / n
        poly = loft_data.splines.new("POLY")
        poly.points.add(len(coords) - 1)
        for i, coord in enumerate(coords):
            x, y, z = coord
            poly.points[i].co = (x, y, z, 1)
        poly.use_cyclic_u = True

        ob = bpy.data.objects.new("Prism_shape", loft_data)
        scn = bpy.context.scene
        scn.collection.objects.link(ob)
        context.view_layer.objects.active = ob
        ob.select_set(True)
        bpy.ops.object.mode_set(mode="OBJECT")
        bpy.ops.object.shade_flat()
        ob.data.fill_mode = 'BOTH'
        ob.pov.curveshape = "prism"
        ob.name = ob.data.name = "Prism"
        return {"FINISHED"}


classes = (
    POV_OT_plane_add,
    POV_OT_box_add,
    POV_OT_cylinder_add,
    POV_OT_cylinder_update,
    POV_OT_sphere_add,
    POV_OT_sphere_update,
    POV_OT_cone_add,
    POV_OT_cone_update,
    POV_OT_rainbow_add,
    POV_OT_torus_add,
    POV_OT_torus_update,
    POV_OT_prism_add,
)


def register():
    for cls in classes:
        register_class(cls)


def unregister():
    for cls in reversed(classes):
        unregister_class(cls)

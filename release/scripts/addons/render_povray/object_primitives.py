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


def write_object_modifiers(scene, ob, File):
    """Translate some object level POV statements from Blender UI
    to POV syntax and write to exported file """

    # Maybe return that string to be added instead of directly written.

    '''XXX WIP
    onceCSG = 0
    for mod in ob.modifiers:
        if onceCSG == 0:
            if mod :
                if mod.type == 'BOOLEAN':
                    if ob.pov.boolean_mod == "POV":
                        File.write("\tinside_vector <%.6g, %.6g, %.6g>\n" %
                                   (ob.pov.inside_vector[0],
                                    ob.pov.inside_vector[1],
                                    ob.pov.inside_vector[2]))
                        onceCSG = 1
    '''

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
    '''
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
    '''


def pov_define_mesh(mesh, verts, edges, faces, name, hide_geometry=True):
    """Generate proxy mesh."""
    if mesh is None:
        mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, edges, faces)
    mesh.update()
    mesh.validate(
        verbose=False
    )  # Set it to True to see debug messages (helps ensure you generate valid geometry).
    if hide_geometry:
        mesh.vertices.foreach_set("hide", [True] * len(mesh.vertices))
        mesh.edges.foreach_set("hide", [True] * len(mesh.edges))
        mesh.polygons.foreach_set("hide", [True] * len(mesh.polygons))
    return mesh


class POVRAY_OT_lathe_add(Operator):
    """Add the representation of POV lathe using a screw modifier."""

    bl_idname = "pov.addlathe"
    bl_label = "Lathe"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "adds lathe"

    def execute(self, context):
        # ayers=[False]*20
        # layers[0]=True
        bpy.ops.curve.primitive_bezier_curve_add(
            location=context.scene.cursor.location,
            rotation=(0, 0, 0),
            # layers=layers,
        )
        ob = context.view_layer.objects.active
        ob_data = ob.data
        ob.name = ob_data.name = "PovLathe"
        ob_data.dimensions = '2D'
        ob_data.transform(Matrix.Rotation(-pi / 2.0, 4, 'Z'))
        ob.pov.object_as = 'LATHE'
        self.report(
            {'INFO'}, "This native POV-Ray primitive" "won't have any vertex to show in edit mode"
        )
        ob.pov.curveshape = "lathe"
        bpy.ops.object.modifier_add(type='SCREW')
        mod = ob.modifiers[-1]
        mod.axis = 'Y'
        mod.show_render = False
        return {'FINISHED'}


def pov_superellipsoid_define(context, op, ob):
    """Create the proxy mesh of a POV superellipsoid using pov_superellipsoid_define()."""

    if op:
        mesh = None

        u = op.se_u
        v = op.se_v
        n1 = op.se_n1
        n2 = op.se_n2
        edit = op.se_edit
        se_param1 = n2  # op.se_param1
        se_param2 = n1  # op.se_param2

    else:
        assert ob
        mesh = ob.data

        u = ob.pov.se_u
        v = ob.pov.se_v
        n1 = ob.pov.se_n1
        n2 = ob.pov.se_n2
        edit = ob.pov.se_edit
        se_param1 = ob.pov.se_param1
        se_param2 = ob.pov.se_param2

    verts = []
    r = 1

    stepSegment = 360 / v * pi / 180
    stepRing = pi / u
    angSegment = 0
    angRing = -pi / 2

    step = 0
    for ring in range(0, u - 1):
        angRing += stepRing
        for segment in range(0, v):
            step += 1
            angSegment += stepSegment
            x = r * (abs(cos(angRing)) ** n1) * (abs(cos(angSegment)) ** n2)
            if (cos(angRing) < 0 and cos(angSegment) > 0) or (
                cos(angRing) > 0 and cos(angSegment) < 0
            ):
                x = -x
            y = r * (abs(cos(angRing)) ** n1) * (abs(sin(angSegment)) ** n2)
            if (cos(angRing) < 0 and sin(angSegment) > 0) or (
                cos(angRing) > 0 and sin(angSegment) < 0
            ):
                y = -y
            z = r * (abs(sin(angRing)) ** n1)
            if sin(angRing) < 0:
                z = -z
            x = round(x, 4)
            y = round(y, 4)
            z = round(z, 4)
            verts.append((x, y, z))
    if edit == 'TRIANGLES':
        verts.append((0, 0, 1))
        verts.append((0, 0, -1))

    faces = []

    for i in range(0, u - 2):
        m = i * v
        for p in range(0, v):
            if p < v - 1:
                face = (m + p, 1 + m + p, v + 1 + m + p, v + m + p)
            if p == v - 1:
                face = (m + p, m, v + m, v + m + p)
            faces.append(face)
    if edit == 'TRIANGLES':
        indexUp = len(verts) - 2
        indexDown = len(verts) - 1
        indexStartDown = len(verts) - 2 - v
        for i in range(0, v):
            if i < v - 1:
                face = (indexDown, i, i + 1)
                faces.append(face)
            if i == v - 1:
                face = (indexDown, i, 0)
                faces.append(face)
        for i in range(0, v):
            if i < v - 1:
                face = (indexUp, i + indexStartDown, i + indexStartDown + 1)
                faces.append(face)
            if i == v - 1:
                face = (indexUp, i + indexStartDown, indexStartDown)
                faces.append(face)
    if edit == 'NGONS':
        face = []
        for i in range(0, v):
            face.append(i)
        faces.append(face)
        face = []
        indexUp = len(verts) - 1
        for i in range(0, v):
            face.append(indexUp - i)
        faces.append(face)
    mesh = pov_define_mesh(mesh, verts, [], faces, "SuperEllipsoid")

    if not ob:
        ob = object_data_add(context, mesh, operator=None)
        # engine = context.scene.render.engine what for?
        ob = context.object
        ob.name = ob.data.name = "PovSuperellipsoid"
        ob.pov.object_as = 'SUPERELLIPSOID'
        ob.pov.se_param1 = n2
        ob.pov.se_param2 = n1

        ob.pov.se_u = u
        ob.pov.se_v = v
        ob.pov.se_n1 = n1
        ob.pov.se_n2 = n2
        ob.pov.se_edit = edit

        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.hide(unselected=False)
        bpy.ops.object.mode_set(mode="OBJECT")


class POVRAY_OT_superellipsoid_add(Operator):
    """Add the representation of POV superellipsoid using the pov_superellipsoid_define()."""

    bl_idname = "pov.addsuperellipsoid"
    bl_label = "Add SuperEllipsoid"
    bl_description = "Create a SuperEllipsoid"
    bl_options = {'REGISTER', 'UNDO'}
    COMPAT_ENGINES = {'POVRAY_RENDER'}

    # Keep in sync within object_properties.py section Superellipsoid
    # as this allows interactive update
    #     If someone knows how to define operators' props from a func, I'd be delighted to learn it!
    se_param1: FloatProperty(name="Parameter 1", description="", min=0.00, max=10.0, default=0.04)

    se_param2: FloatProperty(name="Parameter 2", description="", min=0.00, max=10.0, default=0.04)

    se_u: IntProperty(
        name="U-segments", description="radial segmentation", default=20, min=4, max=265
    )
    se_v: IntProperty(
        name="V-segments", description="lateral segmentation", default=20, min=4, max=265
    )
    se_n1: FloatProperty(
        name="Ring manipulator",
        description="Manipulates the shape of the Ring",
        default=1.0,
        min=0.01,
        max=100.0,
    )
    se_n2: FloatProperty(
        name="Cross manipulator",
        description="Manipulates the shape of the cross-section",
        default=1.0,
        min=0.01,
        max=100.0,
    )
    se_edit: EnumProperty(
        items=[("NOTHING", "Nothing", ""), ("NGONS", "N-Gons", ""), ("TRIANGLES", "Triangles", "")],
        name="Fill up and down",
        description="",
        default='TRIANGLES',
    )

    @classmethod
    def poll(cls, context):
        engine = context.scene.render.engine
        return engine in cls.COMPAT_ENGINES

    def execute(self, context):
        pov_superellipsoid_define(context, self, None)

        self.report(
            {'INFO'}, "This native POV-Ray primitive" "won't have any vertex to show in edit mode"
        )

        return {'FINISHED'}


class POVRAY_OT_superellipsoid_update(Operator):
    """Update the superellipsoid.

    Delete its previous proxy geometry and rerun pov_superellipsoid_define() function
    with the new parameters"""

    bl_idname = "pov.superellipsoid_update"
    bl_label = "Update"
    bl_description = "Update Superellipsoid"
    bl_options = {'REGISTER', 'UNDO'}
    COMPAT_ENGINES = {'POVRAY_RENDER'}

    @classmethod
    def poll(cls, context):
        engine = context.scene.render.engine
        ob = context.object
        return ob and ob.data and ob.type == 'MESH' and engine in cls.COMPAT_ENGINES

    def execute(self, context):
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.reveal()
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.delete(type='VERT')
        bpy.ops.object.mode_set(mode="OBJECT")

        pov_superellipsoid_define(context, None, context.object)

        return {'FINISHED'}


def create_faces(vert_idx_1, vert_idx_2, closed=False, flipped=False):
    """Generate viewport proxy mesh data for some pov primitives"""
    faces = []
    if not vert_idx_1 or not vert_idx_2:
        return None
    if len(vert_idx_1) < 2 and len(vert_idx_2) < 2:
        return None
    fan = False
    if len(vert_idx_1) != len(vert_idx_2):
        if len(vert_idx_1) == 1 and len(vert_idx_2) > 1:
            fan = True
        else:
            return None
    total = len(vert_idx_2)
    if closed:
        if flipped:
            face = [vert_idx_1[0], vert_idx_2[0], vert_idx_2[total - 1]]
            if not fan:
                face.append(vert_idx_1[total - 1])
            faces.append(face)

        else:
            face = [vert_idx_2[0], vert_idx_1[0]]
            if not fan:
                face.append(vert_idx_1[total - 1])
            face.append(vert_idx_2[total - 1])
            faces.append(face)
    for num in range(total - 1):
        if flipped:
            if fan:
                face = [vert_idx_2[num], vert_idx_1[0], vert_idx_2[num + 1]]
            else:
                face = [vert_idx_2[num], vert_idx_1[num], vert_idx_1[num + 1], vert_idx_2[num + 1]]
            faces.append(face)
        else:
            if fan:
                face = [vert_idx_1[0], vert_idx_2[num], vert_idx_2[num + 1]]
            else:
                face = [vert_idx_1[num], vert_idx_2[num], vert_idx_2[num + 1], vert_idx_1[num + 1]]
            faces.append(face)

    return faces


def power(a, b):
    """Workaround to negative a, where the math.pow() method would return a ValueError."""
    if a < 0:
        return -((-a) ** b)
    return a ** b


def supertoroid(R, r, u, v, n1, n2):
    a = 2 * pi / u
    b = 2 * pi / v
    verts = []
    faces = []
    for i in range(u):
        s = power(sin(i * a), n1)
        c = power(cos(i * a), n1)
        for j in range(v):
            c2 = R + r * power(cos(j * b), n2)
            s2 = r * power(sin(j * b), n2)
            verts.append((c * c2, s * c2, s2))  # type as a (mathutils.Vector(c*c2,s*c2,s2))?
        if i > 0:
            f = create_faces(range((i - 1) * v, i * v), range(i * v, (i + 1) * v), closed=True)
            faces.extend(f)
    f = create_faces(range((u - 1) * v, u * v), range(v), closed=True)
    faces.extend(f)
    return verts, faces


def pov_supertorus_define(context, op, ob):
    """Get POV supertorus properties from operator (object creation/import) or data update."""
    if op:
        mesh = None
        st_R = op.st_R
        st_r = op.st_r
        st_u = op.st_u
        st_v = op.st_v
        st_n1 = op.st_n1
        st_n2 = op.st_n2
        st_ie = op.st_ie
        st_edit = op.st_edit

    else:
        assert ob
        mesh = ob.data
        st_R = ob.pov.st_major_radius
        st_r = ob.pov.st_minor_radius
        st_u = ob.pov.st_u
        st_v = ob.pov.st_v
        st_n1 = ob.pov.st_ring
        st_n2 = ob.pov.st_cross
        st_ie = ob.pov.st_ie
        st_edit = ob.pov.st_edit

    if st_ie:
        rad1 = (st_R + st_r) / 2
        rad2 = (st_R - st_r) / 2
        if rad2 > rad1:
            [rad1, rad2] = [rad2, rad1]
    else:
        rad1 = st_R
        rad2 = st_r
        if rad2 > rad1:
            rad1 = rad2
    verts, faces = supertoroid(rad1, rad2, st_u, st_v, st_n1, st_n2)
    mesh = pov_define_mesh(mesh, verts, [], faces, "PovSuperTorus", True)
    if not ob:
        ob = object_data_add(context, mesh, operator=None)
        ob.pov.object_as = 'SUPERTORUS'
        ob.pov.st_major_radius = st_R
        ob.pov.st_minor_radius = st_r
        ob.pov.st_u = st_u
        ob.pov.st_v = st_v
        ob.pov.st_ring = st_n1
        ob.pov.st_cross = st_n2
        ob.pov.st_ie = st_ie
        ob.pov.st_edit = st_edit


class POVRAY_OT_supertorus_add(Operator):
    """Add the representation of POV supertorus using the pov_supertorus_define() function."""

    bl_idname = "pov.addsupertorus"
    bl_label = "Add Supertorus"
    bl_description = "Create a SuperTorus"
    bl_options = {'REGISTER', 'UNDO'}
    COMPAT_ENGINES = {'POVRAY_RENDER'}

    st_R: FloatProperty(
        name="big radius",
        description="The radius inside the tube",
        default=1.0,
        min=0.01,
        max=100.0,
    )
    st_r: FloatProperty(
        name="small radius", description="The radius of the tube", default=0.3, min=0.01, max=100.0
    )
    st_u: IntProperty(
        name="U-segments", description="radial segmentation", default=16, min=3, max=265
    )
    st_v: IntProperty(
        name="V-segments", description="lateral segmentation", default=8, min=3, max=265
    )
    st_n1: FloatProperty(
        name="Ring manipulator",
        description="Manipulates the shape of the Ring",
        default=1.0,
        min=0.01,
        max=100.0,
    )
    st_n2: FloatProperty(
        name="Cross manipulator",
        description="Manipulates the shape of the cross-section",
        default=1.0,
        min=0.01,
        max=100.0,
    )
    st_ie: BoolProperty(
        name="Use Int.+Ext. radii", description="Use internal and external radii", default=False
    )
    st_edit: BoolProperty(name="", description="", default=False, options={'HIDDEN'})

    @classmethod
    def poll(cls, context):
        engine = context.scene.render.engine
        return engine in cls.COMPAT_ENGINES

    def execute(self, context):
        pov_supertorus_define(context, self, None)

        self.report(
            {'INFO'}, "This native POV-Ray primitive" "won't have any vertex to show in edit mode"
        )
        return {'FINISHED'}


class POVRAY_OT_supertorus_update(Operator):
    """Update the supertorus.

    Delete its previous proxy geometry and rerun pov_supetorus_define() function
    with the new parameters"""

    bl_idname = "pov.supertorus_update"
    bl_label = "Update"
    bl_description = "Update SuperTorus"
    bl_options = {'REGISTER', 'UNDO'}
    COMPAT_ENGINES = {'POVRAY_RENDER'}

    @classmethod
    def poll(cls, context):
        engine = context.scene.render.engine
        ob = context.object
        return ob and ob.data and ob.type == 'MESH' and engine in cls.COMPAT_ENGINES

    def execute(self, context):
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.reveal()
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.delete(type='VERT')
        bpy.ops.object.mode_set(mode="OBJECT")

        pov_supertorus_define(context, None, context.object)

        return {'FINISHED'}


# -----------------------------------------------------------------------------
class POVRAY_OT_loft_add(Operator):
    """Create the representation of POV loft using Blender curves."""

    bl_idname = "pov.addloft"
    bl_label = "Add Loft Data"
    bl_description = "Create a Curve data for Meshmaker"
    bl_options = {'REGISTER', 'UNDO'}
    COMPAT_ENGINES = {'POVRAY_RENDER'}

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

    def execute(self, context):

        props = self.properties
        loft_data = bpy.data.curves.new('Loft', type='CURVE')
        loft_data.dimensions = '3D'
        loft_data.resolution_u = 2
        # loft_data.show_normal_face = False # deprecated in 2.8
        n = props.loft_n
        thick = props.loft_thick
        side = props.loft_rings_side
        bottom = props.loft_rings_bottom
        h = props.loft_height
        r = props.loft_r
        distB = r / bottom
        r0 = 0.00001
        z = -h / 2
        print("New")
        for i in range(bottom + 1):
            coords = []
            angle = 0
            for p in range(n):
                x = r0 * cos(angle)
                y = r0 * sin(angle)
                coords.append((x, y, z))
                angle += pi * 2 / n
            r0 += distB
            nurbs = loft_data.splines.new('NURBS')
            nurbs.points.add(len(coords) - 1)
            for c, coord in enumerate(coords):
                x, y, z = coord
                nurbs.points[c].co = (x, y, z, 1)
            nurbs.use_cyclic_u = True
        for i in range(side):
            z += h / side
            coords = []
            angle = 0
            for p in range(n):
                x = r * cos(angle)
                y = r * sin(angle)
                coords.append((x, y, z))
                angle += pi * 2 / n
            nurbs = loft_data.splines.new('NURBS')
            nurbs.points.add(len(coords) - 1)
            for c, coord in enumerate(coords):
                x, y, z = coord
                nurbs.points[c].co = (x, y, z, 1)
            nurbs.use_cyclic_u = True
        r -= thick
        for i in range(side):
            coords = []
            angle = 0
            for p in range(n):
                x = r * cos(angle)
                y = r * sin(angle)
                coords.append((x, y, z))
                angle += pi * 2 / n
            nurbs = loft_data.splines.new('NURBS')
            nurbs.points.add(len(coords) - 1)
            for c, coord in enumerate(coords):
                x, y, z = coord
                nurbs.points[c].co = (x, y, z, 1)
            nurbs.use_cyclic_u = True
            z -= h / side
        z = (-h / 2) + thick
        distB = (r - 0.00001) / bottom
        for i in range(bottom + 1):
            coords = []
            angle = 0
            for p in range(n):
                x = r * cos(angle)
                y = r * sin(angle)
                coords.append((x, y, z))
                angle += pi * 2 / n
            r -= distB
            nurbs = loft_data.splines.new('NURBS')
            nurbs.points.add(len(coords) - 1)
            for c, coord in enumerate(coords):
                x, y, z = coord
                nurbs.points[c].co = (x, y, z, 1)
            nurbs.use_cyclic_u = True
        ob = bpy.data.objects.new('Loft_shape', loft_data)
        scn = bpy.context.scene
        scn.collection.objects.link(ob)
        context.view_layer.objects.active = ob
        ob.select_set(True)
        ob.pov.curveshape = "loft"
        return {'FINISHED'}


class POVRAY_OT_plane_add(Operator):
    """Add the representation of POV infinite plane using just a very big Blender Plane.

    Flag its primitive type with a specific pov.object_as attribute and lock edit mode
    to keep proxy consistency by hiding edit geometry."""

    bl_idname = "pov.addplane"
    bl_label = "Plane"
    bl_description = "Add Plane"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        # layers = 20*[False]
        # layers[0] = True
        bpy.ops.mesh.primitive_plane_add(size=100000)
        ob = context.object
        ob.name = ob.data.name = 'PovInfinitePlane'
        bpy.ops.object.mode_set(mode="EDIT")
        self.report(
            {'INFO'}, "This native POV-Ray primitive " "won't have any vertex to show in edit mode"
        )
        bpy.ops.mesh.hide(unselected=False)
        bpy.ops.object.mode_set(mode="OBJECT")
        bpy.ops.object.shade_smooth()
        ob.pov.object_as = "PLANE"
        return {'FINISHED'}


class POVRAY_OT_box_add(Operator):
    """Add the representation of POV box using a simple Blender mesh cube.

    Flag its primitive type with a specific pov.object_as attribute and lock edit mode
    to keep proxy consistency by hiding edit geometry."""

    bl_idname = "pov.addbox"
    bl_label = "Box"
    bl_description = "Add Box"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        # layers = 20*[False]
        # layers[0] = True
        bpy.ops.mesh.primitive_cube_add()
        ob = context.object
        ob.name = ob.data.name = 'PovBox'
        bpy.ops.object.mode_set(mode="EDIT")
        self.report(
            {'INFO'}, "This native POV-Ray primitive " "won't have any vertex to show in edit mode"
        )
        bpy.ops.mesh.hide(unselected=False)
        bpy.ops.object.mode_set(mode="OBJECT")
        ob.pov.object_as = "BOX"
        return {'FINISHED'}


def pov_cylinder_define(context, op, ob, radius, loc, loc_cap):
    """Pick POV cylinder properties either from creation operator, import, or data update """
    if op:
        R = op.R
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
        bpy.ops.object.add(type='MESH', location=loc)
        ob = context.object
        ob.name = ob.data.name = "PovCylinder"
        ob.pov.cylinder_radius = radius
        ob.pov.cylinder_location_cap = vec
        ob.pov.object_as = "CYLINDER"
    else:
        ob.location = loc

    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.reveal()
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.delete(type='VERT')
    bpy.ops.mesh.primitive_cylinder_add(
        radius=radius, depth=depth, location=loc, rotation=roteuler, end_fill_type='NGON'
    )  # 'NOTHING'
    bpy.ops.transform.translate(value=trans)

    bpy.ops.mesh.hide(unselected=False)
    bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.shade_smooth()


class POVRAY_OT_cylinder_add(Operator):
    """Add the representation of POV cylinder using pov_cylinder_define() function.

    Use imported_cyl_loc when this operator is run by POV importer."""

    bl_idname = "pov.addcylinder"
    bl_label = "Cylinder"
    bl_description = "Add Cylinder"
    bl_options = {'REGISTER', 'UNDO'}

    # Keep in sync within object_properties.py section Cylinder
    # as this allows interactive update
    R: FloatProperty(name="Cylinder radius", min=0.00, max=10.0, default=1.0)

    imported_cyl_loc: FloatVectorProperty(
        name="Imported Pov base location", precision=6, default=(0.0, 0.0, 0.0)
    )

    imported_cyl_loc_cap: FloatVectorProperty(
        name="Imported Pov cap location", precision=6, default=(0.0, 0.0, 2.0)
    )

    def execute(self, context):
        props = self.properties
        R = props.R
        ob = context.object
        # layers = 20*[False]
        # layers[0] = True
        if ob:
            if ob.pov.imported_cyl_loc:
                LOC = ob.pov.imported_cyl_loc
            if ob.pov.imported_cyl_loc_cap:
                LOC_CAP = ob.pov.imported_cyl_loc_cap
        else:
            if not props.imported_cyl_loc:
                LOC_CAP = LOC = bpy.context.scene.cursor.location
                LOC_CAP[2] += 2.0
            else:
                LOC = props.imported_cyl_loc
                LOC_CAP = props.imported_cyl_loc_cap
            self.report(
                {'INFO'},
                "This native POV-Ray primitive " "won't have any vertex to show in edit mode",
            )

        pov_cylinder_define(context, self, None, self.R, LOC, LOC_CAP)

        return {'FINISHED'}


class POVRAY_OT_cylinder_update(Operator):
    """Update the POV cylinder.

    Delete its previous proxy geometry and rerun pov_cylinder_define() function
    with the new parameters"""

    bl_idname = "pov.cylinder_update"
    bl_label = "Update"
    bl_description = "Update Cylinder"
    bl_options = {'REGISTER', 'UNDO'}
    COMPAT_ENGINES = {'POVRAY_RENDER'}

    @classmethod
    def poll(cls, context):
        engine = context.scene.render.engine
        ob = context.object
        return (
            ob
            and ob.data
            and ob.type == 'MESH'
            and ob.pov.object_as == "CYLINDER"
            and engine in cls.COMPAT_ENGINES
        )

    def execute(self, context):
        ob = context.object
        radius = ob.pov.cylinder_radius
        loc = ob.location
        loc_cap = loc + ob.pov.cylinder_location_cap

        pov_cylinder_define(context, None, ob, radius, loc, loc_cap)

        return {'FINISHED'}


# ----------------------------------- SPHERE---------------------------------- #
def pov_sphere_define(context, op, ob, loc):
    """create the representation of POV sphere using a Blender icosphere.

    Its nice platonic solid curvature better represents pov rendertime
    tesselation than a UV sphere"""

    if op:
        R = op.R
        loc = bpy.context.scene.cursor.location
    else:
        assert ob
        R = ob.pov.sphere_radius

        # keep object rotation and location for the add object operator
        obrot = ob.rotation_euler
        # obloc = ob.location
        obscale = ob.scale

        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.reveal()
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.delete(type='VERT')
        bpy.ops.mesh.primitive_ico_sphere_add(
            subdivisions=4, radius=ob.pov.sphere_radius, location=loc, rotation=obrot
        )
        # bpy.ops.transform.rotate(axis=obrot,orient_type='GLOBAL')
        bpy.ops.transform.resize(value=obscale)
        # bpy.ops.transform.rotate(axis=obrot, proportional_size=1)

        bpy.ops.mesh.hide(unselected=False)
        bpy.ops.object.mode_set(mode="OBJECT")
        bpy.ops.object.shade_smooth()
        # bpy.ops.transform.rotate(axis=obrot,orient_type='GLOBAL')

    if not ob:
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=4, radius=R, location=loc)
        ob = context.object
        ob.name = ob.data.name = "PovSphere"
        ob.pov.object_as = "SPHERE"
        ob.pov.sphere_radius = R
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.hide(unselected=False)
        bpy.ops.object.mode_set(mode="OBJECT")


class POVRAY_OT_sphere_add(Operator):
    """Add the representation of POV sphere using pov_sphere_define() function.

    Use imported_loc when this operator is run by POV importer."""

    bl_idname = "pov.addsphere"
    bl_label = "Sphere"
    bl_description = "Add Sphere Shape"
    bl_options = {'REGISTER', 'UNDO'}

    # Keep in sync within object_properties.py section Sphere
    # as this allows interactive update
    R: FloatProperty(name="Sphere radius", min=0.00, max=10.0, default=0.5)

    imported_loc: FloatVectorProperty(
        name="Imported Pov location", precision=6, default=(0.0, 0.0, 0.0)
    )

    def execute(self, context):
        props = self.properties
        R = props.R
        ob = context.object

        if ob:
            if ob.pov.imported_loc:
                LOC = ob.pov.imported_loc
        else:
            if not props.imported_loc:
                LOC = bpy.context.scene.cursor.location

            else:
                LOC = props.imported_loc
                self.report(
                    {'INFO'},
                    "This native POV-Ray primitive " "won't have any vertex to show in edit mode",
                )
        pov_sphere_define(context, self, None, LOC)

        return {'FINISHED'}

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
    # ob.name = ob.data.name = 'PovSphere'
    # return {'FINISHED'}


class POVRAY_OT_sphere_update(Operator):
    """Update the POV sphere.

    Delete its previous proxy geometry and rerun pov_sphere_define() function
    with the new parameters"""

    bl_idname = "pov.sphere_update"
    bl_label = "Update"
    bl_description = "Update Sphere"
    bl_options = {'REGISTER', 'UNDO'}
    COMPAT_ENGINES = {'POVRAY_RENDER'}

    @classmethod
    def poll(cls, context):
        engine = context.scene.render.engine
        ob = context.object
        return ob and ob.data and ob.type == 'MESH' and engine in cls.COMPAT_ENGINES

    def execute(self, context):

        pov_sphere_define(context, None, context.object, context.object.location)

        return {'FINISHED'}


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
        verts.append((xb, yb, zb))
        verts.append((xc, yc, zc))
        t += angle
    for i in range(seg):
        f = i * 2
        if i == seg - 1:
            faces.append([0, 1, f + 1, f])
        else:
            faces.append([f + 2, f + 3, f + 1, f])
    if base != 0:
        base_face = []
        for i in range(seg - 1, -1, -1):
            p = i * 2
            base_face.append(p)
        faces.append(base_face)
    if cap != 0:
        cap_face = []
        for i in range(seg):
            p = i * 2 + 1
            cap_face.append(p)
        faces.append(cap_face)

    mesh = pov_define_mesh(mesh, verts, [], faces, "PovCone", True)
    if not ob:
        ob = object_data_add(context, mesh, operator=None)
        ob.pov.object_as = "CONE"
        ob.pov.cone_base_radius = base
        ob.pov.cone_cap_radius = cap
        ob.pov.cone_height = height
        ob.pov.cone_base_z = zb
        ob.pov.cone_cap_z = zc


class POVRAY_OT_cone_add(Operator):
    """Add the representation of POV cone using pov_cone_define() function."""

    bl_idname = "pov.cone_add"
    bl_label = "Cone"
    bl_description = "Add Cone"
    bl_options = {'REGISTER', 'UNDO'}
    COMPAT_ENGINES = {'POVRAY_RENDER'}

    # Keep in sync within object_properties.py section Cone
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
            {'INFO'}, "This native POV-Ray primitive" "won't have any vertex to show in edit mode"
        )
        return {'FINISHED'}


class POVRAY_OT_cone_update(Operator):
    """Update the POV cone.

    Delete its previous proxy geometry and rerun pov_cone_define() function
    with the new parameters"""

    bl_idname = "pov.cone_update"
    bl_label = "Update"
    bl_description = "Update Cone"
    bl_options = {'REGISTER', 'UNDO'}
    COMPAT_ENGINES = {'POVRAY_RENDER'}

    @classmethod
    def poll(cls, context):
        engine = context.scene.render.engine
        ob = context.object
        return ob and ob.data and ob.type == 'MESH' and engine in cls.COMPAT_ENGINES

    def execute(self, context):
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.reveal()
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.delete(type='VERT')
        bpy.ops.object.mode_set(mode="OBJECT")

        pov_cone_define(context, None, context.object)

        return {'FINISHED'}


# ----------------------------------- ISOSURFACES ----------------------------------- #


class POVRAY_OT_isosurface_box_add(Operator):
    """Add the representation of POV isosurface box using also just a Blender mesh cube.

    Flag its primitive type with a specific pov.object_as attribute and lock edit mode
    to keep proxy consistency by hiding edit geometry."""

    bl_idname = "pov.addisosurfacebox"
    bl_label = "Isosurface Box"
    bl_description = "Add Isosurface contained by Box"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        # layers = 20*[False]
        # layers[0] = True
        bpy.ops.mesh.primitive_cube_add()
        ob = context.object
        bpy.ops.object.mode_set(mode="EDIT")
        self.report(
            {'INFO'}, "This native POV-Ray primitive " "won't have any vertex to show in edit mode"
        )
        bpy.ops.mesh.hide(unselected=False)
        bpy.ops.object.mode_set(mode="OBJECT")
        ob.pov.object_as = "ISOSURFACE"
        ob.pov.contained_by = 'box'
        ob.name = 'PovIsosurfaceBox'
        return {'FINISHED'}


class POVRAY_OT_isosurface_sphere_add(Operator):
    """Add the representation of POV isosurface sphere by a Blender mesh icosphere.

    Flag its primitive type with a specific pov.object_as attribute and lock edit mode
    to keep proxy consistency by hiding edit geometry."""

    bl_idname = "pov.addisosurfacesphere"
    bl_label = "Isosurface Sphere"
    bl_description = "Add Isosurface contained by Sphere"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        # layers = 20*[False]
        # layers[0] = True
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=4)
        ob = context.object
        bpy.ops.object.mode_set(mode="EDIT")
        self.report(
            {'INFO'}, "This native POV-Ray primitive " "won't have any vertex to show in edit mode"
        )
        bpy.ops.mesh.hide(unselected=False)
        bpy.ops.object.mode_set(mode="OBJECT")
        bpy.ops.object.shade_smooth()
        ob.pov.object_as = "ISOSURFACE"
        ob.pov.contained_by = 'sphere'
        ob.name = 'PovIsosurfaceSphere'
        return {'FINISHED'}


class POVRAY_OT_sphere_sweep_add(Operator):
    """Add the representation of POV sphere_sweep using a Blender NURBS curve.

    Flag its primitive type with a specific ob.pov.curveshape attribute and
    leave access to edit mode to keep user editable handles."""

    bl_idname = "pov.addspheresweep"
    bl_label = "Sphere Sweep"
    bl_description = "Create Sphere Sweep along curve"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        # layers = 20*[False]
        # layers[0] = True
        bpy.ops.curve.primitive_nurbs_curve_add()
        ob = context.object
        ob.name = ob.data.name = "PovSphereSweep"
        ob.pov.curveshape = "sphere_sweep"
        ob.data.bevel_depth = 0.02
        ob.data.bevel_resolution = 4
        ob.data.fill_mode = 'FULL'
        # ob.data.splines[0].order_u = 4

        return {'FINISHED'}


class POVRAY_OT_blob_add(Operator):
    """Add the representation of POV blob using a Blender meta ball.

    No need to flag its primitive type as meta are exported to blobs
    and leave access to edit mode to keep user editable thresholds."""

    bl_idname = "pov.addblobsphere"
    bl_label = "Blob Sphere"
    bl_description = "Add Blob Sphere"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        # layers = 20*[False]
        # layers[0] = True
        bpy.ops.object.metaball_add(type='BALL')
        ob = context.object
        ob.name = "PovBlob"
        return {'FINISHED'}


class POVRAY_OT_rainbow_add(Operator):
    """Add the representation of POV rainbow using a Blender spot light.

    Rainbows indeed propagate along a visibility cone.
    Flag its primitive type with a specific ob.pov.object_as attribute
    and leave access to edit mode to keep user editable handles.
    Add a constraint to orient it towards camera because POV Rainbows
    are view dependant and having it always initially visible is less
    confusing """

    bl_idname = "pov.addrainbow"
    bl_label = "Rainbow"
    bl_description = "Add Rainbow"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        cam = context.scene.camera
        bpy.ops.object.light_add(type='SPOT', radius=1)
        ob = context.object
        ob.data.show_cone = False
        ob.data.spot_blend = 0.5
        # ob.data.shadow_buffer_clip_end = 0 # deprecated in 2.8
        ob.data.shadow_buffer_clip_start = 4 * cam.location.length
        ob.data.distance = cam.location.length
        ob.data.energy = 0
        ob.name = ob.data.name = "PovRainbow"
        ob.pov.object_as = "RAINBOW"

        # obj = context.object
        bpy.ops.object.constraint_add(type='DAMPED_TRACK')

        ob.constraints["Damped Track"].target = cam
        ob.constraints["Damped Track"].track_axis = 'TRACK_NEGATIVE_Z'
        ob.location = -cam.location

        # refocus on the actual rainbow
        bpy.context.view_layer.objects.active = ob
        ob.select_set(True)

        return {'FINISHED'}


class POVRAY_OT_height_field_add(bpy.types.Operator, ImportHelper):
    """Add the representation of POV height_field using a displaced grid.

    texture slot fix and displace modifier will be needed because noise
    displace operator was deprecated in 2.8"""

    bl_idname = "pov.addheightfield"
    bl_label = "Height Field"
    bl_description = "Add Height Field"
    bl_options = {'REGISTER', 'UNDO'}

    # Keep in sync within object_properties.py section HeightFields
    # as this allows interactive update

    # filename_ext = ".png"

    # filter_glob = StringProperty(
    # default="*.exr;*.gif;*.hdr;*.iff;*.jpeg;*.jpg;*.pgm;*.png;*.pot;*.ppm;*.sys;*.tga;*.tiff;*.EXR;*.GIF;*.HDR;*.IFF;*.JPEG;*.JPG;*.PGM;*.PNG;*.POT;*.PPM;*.SYS;*.TGA;*.TIFF",
    # options={'HIDDEN'},
    # )
    quality: IntProperty(name="Quality", description="", default=100, min=1, max=100)
    hf_filename: StringProperty(maxlen=1024)

    hf_gamma: FloatProperty(name="Gamma", description="Gamma", min=0.0001, max=20.0, default=1.0)

    hf_premultiplied: BoolProperty(name="Premultiplied", description="Premultiplied", default=True)

    hf_smooth: BoolProperty(name="Smooth", description="Smooth", default=False)

    hf_water: FloatProperty(
        name="Water Level", description="Wather Level", min=0.00, max=1.00, default=0.0
    )

    hf_hierarchy: BoolProperty(name="Hierarchy", description="Height field hierarchy", default=True)

    def execute(self, context):
        props = self.properties
        impath = bpy.path.abspath(self.filepath)
        img = bpy.data.images.load(impath)
        im_name = img.name
        im_name, file_extension = os.path.splitext(im_name)
        hf_tex = bpy.data.textures.new('%s_hf_image' % im_name, type='IMAGE')
        hf_tex.image = img
        mat = bpy.data.materials.new('Tex_%s_hf' % im_name)
        hf_slot = mat.pov_texture_slots.add()
        hf_slot.texture = hf_tex.name
        # layers = 20*[False]
        # layers[0] = True
        quality = props.quality
        res = 100 / quality
        w, h = hf_tex.image.size[:]
        w = int(w / res)
        h = int(h / res)
        bpy.ops.mesh.primitive_grid_add(x_subdivisions=w, y_subdivisions=h, size=0.5)
        ob = context.object
        ob.name = ob.data.name = '%s' % im_name
        ob.data.materials.append(mat)
        bpy.ops.object.mode_set(mode="EDIT")
        # bpy.ops.mesh.noise(factor=1) # TODO replace by displace modifier, noise deprecated in 2.8
        bpy.ops.object.mode_set(mode="OBJECT")

        # needs a loop to select by index?
        # bpy.ops.object.material_slot_remove()
        # material just left there for now

        mat.pov_texture_slots.clear()
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.hide(unselected=False)
        bpy.ops.object.mode_set(mode="OBJECT")
        ob.pov.object_as = 'HEIGHT_FIELD'
        # POV-Ray will soon use only forwards slashes on every OS and already can
        forward_impath = impath.replace(os.sep, '/')
        ob.pov.hf_filename = forward_impath
        return {'FINISHED'}


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
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.delete(type='VERT')
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
        ob.pov.object_as = "TORUS"
        ob.pov.torus_major_segments = mas
        ob.pov.torus_minor_segments = mis
        ob.pov.torus_major_radius = mar
        ob.pov.torus_minor_radius = mir
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.hide(unselected=False)
        bpy.ops.object.mode_set(mode="OBJECT")


class POVRAY_OT_torus_add(Operator):
    """Add the representation of POV torus using using pov_torus_define() function."""

    bl_idname = "pov.addtorus"
    bl_label = "Torus"
    bl_description = "Add Torus"
    bl_options = {'REGISTER', 'UNDO'}

    # Keep in sync within object_properties.py section Torus
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
            {'INFO'}, "This native POV-Ray primitive " "won't have any vertex to show in edit mode"
        )
        return {'FINISHED'}


class POVRAY_OT_torus_update(Operator):
    """Update the POV torus.

    Delete its previous proxy geometry and rerun pov_torus_define() function
    with the new parameters"""

    bl_idname = "pov.torus_update"
    bl_label = "Update"
    bl_description = "Update Torus"
    bl_options = {'REGISTER', 'UNDO'}
    COMPAT_ENGINES = {'POVRAY_RENDER'}

    @classmethod
    def poll(cls, context):
        engine = context.scene.render.engine
        ob = context.object
        return ob and ob.data and ob.type == 'MESH' and engine in cls.COMPAT_ENGINES

    def execute(self, context):

        pov_torus_define(context, None, context.object)

        return {'FINISHED'}


# -----------------------------------------------------------------------------


class POVRAY_OT_prism_add(Operator):
    """Add the representation of POV prism using using an extruded curve."""

    bl_idname = "pov.addprism"
    bl_label = "Prism"
    bl_description = "Create Prism"
    bl_options = {'REGISTER', 'UNDO'}

    prism_n: IntProperty(name="Sides", description="Number of sides", default=5, min=3, max=720)
    prism_r: FloatProperty(name="Radius", description="Radius", default=1.0)

    def execute(self, context):

        props = self.properties
        loft_data = bpy.data.curves.new('Prism', type='CURVE')
        loft_data.dimensions = '2D'
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
        poly = loft_data.splines.new('POLY')
        poly.points.add(len(coords) - 1)
        for i, coord in enumerate(coords):
            x, y, z = coord
            poly.points[i].co = (x, y, z, 1)
        poly.use_cyclic_u = True

        ob = bpy.data.objects.new('Prism_shape', loft_data)
        scn = bpy.context.scene
        scn.collection.objects.link(ob)
        context.view_layer.objects.active = ob
        ob.select_set(True)
        ob.pov.curveshape = "prism"
        ob.name = ob.data.name = "Prism"
        return {'FINISHED'}


# ----------------------------------- PARAMETRIC ----------------------------------- #
def pov_parametric_define(context, op, ob):
    """Add the representation of POV parametric surfaces by math surface from add mesh extra objects addon.

    Picking properties either from creation operator, import, or data update.
    But flag its primitive type with a specific pov.object_as attribute and lock edit mode
    to keep proxy consistency by hiding edit geometry."""
    if op:
        u_min = op.u_min
        u_max = op.u_max
        v_min = op.v_min
        v_max = op.v_max
        x_eq = op.x_eq
        y_eq = op.y_eq
        z_eq = op.z_eq

    else:
        assert ob
        u_min = ob.pov.u_min
        u_max = ob.pov.u_max
        v_min = ob.pov.v_min
        v_max = ob.pov.v_max
        x_eq = ob.pov.x_eq
        y_eq = ob.pov.y_eq
        z_eq = ob.pov.z_eq

        # keep object rotation and location for the updated object
        obloc = ob.location
        obrot = ob.rotation_euler  # In radians
        # Parametric addon has no loc rot, some extra work is needed
        # in case cursor has moved
        curloc = bpy.context.scene.cursor.location

        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.reveal()
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.delete(type='VERT')
        bpy.ops.mesh.primitive_xyz_function_surface(
            x_eq=x_eq,
            y_eq=y_eq,
            z_eq=z_eq,
            range_u_min=u_min,
            range_u_max=u_max,
            range_v_min=v_min,
            range_v_max=v_max,
        )
        bpy.ops.mesh.select_all(action='SELECT')
        # extra work:
        bpy.ops.transform.translate(value=(obloc - curloc), proportional_size=1)
        # XXX TODO : https://devtalk.blender.org/t/bpy-ops-transform-rotate-option-axis/6235/7
        # to complete necessary extra work rotation, after updating from blender version > 2.92
        # update and uncomment below, but simple axis deprecated since 2.8
        # bpy.ops.transform.rotate(axis=obrot, proportional_size=1)

        bpy.ops.mesh.hide(unselected=False)
        bpy.ops.object.mode_set(mode="OBJECT")

    if not ob:
        bpy.ops.mesh.primitive_xyz_function_surface(
            x_eq=x_eq,
            y_eq=y_eq,
            z_eq=z_eq,
            range_u_min=u_min,
            range_u_max=u_max,
            range_v_min=v_min,
            range_v_max=v_max,
        )
        ob = context.object
        ob.name = ob.data.name = "PovParametric"
        ob.pov.object_as = "PARAMETRIC"

        ob.pov.u_min = u_min
        ob.pov.u_max = u_max
        ob.pov.v_min = v_min
        ob.pov.v_max = v_max
        ob.pov.x_eq = x_eq
        ob.pov.y_eq = y_eq
        ob.pov.z_eq = z_eq

        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.hide(unselected=False)
        bpy.ops.object.mode_set(mode="OBJECT")


class POVRAY_OT_parametric_add(Operator):
    """Add the representation of POV parametric surfaces using pov_parametric_define() function."""

    bl_idname = "pov.addparametric"
    bl_label = "Parametric"
    bl_description = "Add Paramertic"
    bl_options = {'REGISTER', 'UNDO'}

    # Keep in sync within object_properties.py section Parametric primitive
    # as this allows interactive update
    u_min: FloatProperty(name="U Min", description="", default=0.0)
    v_min: FloatProperty(name="V Min", description="", default=0.0)
    u_max: FloatProperty(name="U Max", description="", default=6.28)
    v_max: FloatProperty(name="V Max", description="", default=12.57)
    x_eq: StringProperty(maxlen=1024, default="cos(v)*(1+cos(u))*sin(v/8)")
    y_eq: StringProperty(maxlen=1024, default="sin(u)*sin(v/8)+cos(v/8)*1.5")
    z_eq: StringProperty(maxlen=1024, default="sin(v)*(1+cos(u))*sin(v/8)")

    def execute(self, context):
        props = self.properties
        u_min = props.u_min
        v_min = props.v_min
        u_max = props.u_max
        v_max = props.v_max
        x_eq = props.x_eq
        y_eq = props.y_eq
        z_eq = props.z_eq

        pov_parametric_define(context, self, None)
        self.report(
            {'INFO'}, "This native POV-Ray primitive " "won't have any vertex to show in edit mode"
        )
        return {'FINISHED'}


class POVRAY_OT_parametric_update(Operator):
    """Update the representation of POV parametric surfaces.

    Delete its previous proxy geometry and rerun pov_parametric_define() function
    with the new parameters"""

    bl_idname = "pov.parametric_update"
    bl_label = "Update"
    bl_description = "Update parametric object"
    bl_options = {'REGISTER', 'UNDO'}
    COMPAT_ENGINES = {'POVRAY_RENDER'}

    @classmethod
    def poll(cls, context):
        engine = context.scene.render.engine
        ob = context.object
        return ob and ob.data and ob.type == 'MESH' and engine in cls.COMPAT_ENGINES

    def execute(self, context):

        pov_parametric_define(context, None, context.object)

        return {'FINISHED'}


# -----------------------------------------------------------------------------


class POVRAY_OT_shape_polygon_to_circle_add(Operator):
    """Add the proxy mesh for POV Polygon to circle lofting macro"""

    bl_idname = "pov.addpolygontocircle"
    bl_label = "Polygon To Circle Blending"
    bl_description = "Add Polygon To Circle Blending Surface"
    bl_options = {'REGISTER', 'UNDO'}
    COMPAT_ENGINES = {'POVRAY_RENDER'}

    # Keep in sync within object_properties.py section PolygonToCircle properties
    # as this allows interactive update
    polytocircle_resolution: IntProperty(
        name="Resolution", description="", default=3, min=0, max=256
    )
    polytocircle_ngon: IntProperty(name="NGon", description="", min=3, max=64, default=5)
    polytocircle_ngonR: FloatProperty(name="NGon Radius", description="", default=0.3)
    polytocircle_circleR: FloatProperty(name="Circle Radius", description="", default=1.0)

    def execute(self, context):
        props = self.properties
        ngon = props.polytocircle_ngon
        ngonR = props.polytocircle_ngonR
        circleR = props.polytocircle_circleR
        resolution = props.polytocircle_resolution
        # layers = 20*[False]
        # layers[0] = True
        bpy.ops.mesh.primitive_circle_add(
            vertices=ngon, radius=ngonR, fill_type='NGON', enter_editmode=True
        )
        bpy.ops.transform.translate(value=(0, 0, 1))
        bpy.ops.mesh.subdivide(number_cuts=resolution)
        numCircleVerts = ngon + (ngon * resolution)
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.ops.mesh.primitive_circle_add(
            vertices=numCircleVerts, radius=circleR, fill_type='NGON', enter_editmode=True
        )
        bpy.ops.transform.translate(value=(0, 0, -1))
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.bridge_edge_loops()
        if ngon < 5:
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.mesh.primitive_circle_add(
                vertices=ngon, radius=ngonR, fill_type='TRIFAN', enter_editmode=True
            )
            bpy.ops.transform.translate(value=(0, 0, 1))
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.remove_doubles()
        bpy.ops.object.mode_set(mode='OBJECT')
        ob = context.object
        ob.name = "Polygon_To_Circle"
        ob.pov.object_as = 'POLYCIRCLE'
        ob.pov.ngon = ngon
        ob.pov.ngonR = ngonR
        ob.pov.circleR = circleR
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.hide(unselected=False)
        bpy.ops.object.mode_set(mode="OBJECT")
        return {'FINISHED'}


classes = (
    POVRAY_OT_lathe_add,
    POVRAY_OT_superellipsoid_add,
    POVRAY_OT_superellipsoid_update,
    POVRAY_OT_supertorus_add,
    POVRAY_OT_supertorus_update,
    POVRAY_OT_loft_add,
    POVRAY_OT_plane_add,
    POVRAY_OT_box_add,
    POVRAY_OT_cylinder_add,
    POVRAY_OT_cylinder_update,
    POVRAY_OT_sphere_add,
    POVRAY_OT_sphere_update,
    POVRAY_OT_cone_add,
    POVRAY_OT_cone_update,
    POVRAY_OT_isosurface_box_add,
    POVRAY_OT_isosurface_sphere_add,
    POVRAY_OT_sphere_sweep_add,
    POVRAY_OT_blob_add,
    POVRAY_OT_rainbow_add,
    POVRAY_OT_height_field_add,
    POVRAY_OT_torus_add,
    POVRAY_OT_torus_update,
    POVRAY_OT_prism_add,
    POVRAY_OT_parametric_add,
    POVRAY_OT_parametric_update,
    POVRAY_OT_shape_polygon_to_circle_add,
)


def register():
    for cls in classes:
        register_class(cls)


def unregister():
    for cls in reversed(classes):
        unregister_class(cls)

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


bl_info = {
    "name": "Extrude Along Curve",
    "author": "Andrew Hale (TrumanBlending)",
    "version": (0, 1),
    "blender": (2, 63, 0),
    "location": "",
    "description": "Extrude a face along a Bezier Curve",
    "warning": "",
    'wiki_url': "",
    "tracker_url": "https://developer.blender.org/maniphest/task/edit/form/2/",
    "category": "Mesh"}


import bpy
import bmesh
from mathutils import Vector, Quaternion
from math import ceil, floor, pi


def eval_bez_tan(mat, points, t):
    num = len(points)
    t *= num - 1
    upper = ceil(t)
    lower = floor(t)
    if upper == lower:
        if upper == 0:
            return (mat * (points[upper].handle_right - points[upper].co)).normalized()
        elif upper == num - 1:
            return (mat * (points[upper].co - points[upper].handle_left)).normalized()
        else:
            return (mat * (points[upper].co - points[upper].handle_left)).normalized()
    else:
        t -= lower
        pupper = points[upper]
        plower = points[lower]
        tangent = -3 * (1 - t) ** 2 * plower.co + (-6 * (1 - t) * t + 3 * (1 - t) ** 2) * plower.handle_right + (-3 * t ** 2 + 3 * (1 - t) * 2 * t) * pupper.handle_left + 3 * t ** 2 * pupper.co
        tangent = mat * tangent
        tangent.normalize()
        return tangent


def eval_bez(mat, points, t):
    num = len(points)
    t *= num - 1
    upper = ceil(t)
    lower = floor(t)
    if upper == lower:
        return mat * points[upper].co
    else:
        t -= lower
        pupper = points[upper]
        plower = points[lower]
        pos = (1 - t) ** 3 * plower.co + 3 * (1 - t) ** 2 * t * plower.handle_right + 3 * (1 - t) * t ** 2 * pupper.handle_left + t ** 3 * pupper.co
        return mat * pos


def curve_ob_enum(self, context):
    if context is None:
        return []
    obs = context.scene.objects
    cuobs = [(str(i), ob.name, ob.name) for i, ob in enumerate(obs) if ob.type == 'CURVE']
    curve_ob_enum.temp = cuobs
    return cuobs


class ExtrudeAlongCurve(bpy.types.Operator):
    bl_idname = "mesh.extrude_along_curve"
    bl_label = "Extrude Along Curve"
    bl_options = {'REGISTER', 'UNDO'}

    resolution: bpy.props.IntProperty(name="Resolution", default=1, min=1, soft_max=100)
    scale: bpy.props.FloatProperty(name="Scale", default=1.0, soft_min=0.0, soft_max=5.0)
    rotation: bpy.props.FloatProperty(name="Rotation", default=0.0, soft_min=-2 * pi, soft_max=2 * pi, subtype='ANGLE')
    splineidx: bpy.props.IntProperty(name="Spline Index", default=0, min=0)
    snapto: bpy.props.BoolProperty(name="Snap To Face", default=True)
    curveob: bpy.props.EnumProperty(name="Curve", items=curve_ob_enum)

    @classmethod
    def poll(self, context):
        ob = context.active_object
        for cuob in context.scene.objects:
            if cuob.type == 'CURVE':
                break
        else:
            return False

        return (ob is not None) and (ob.type == 'MESH') and (context.mode == 'EDIT_MESH')

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "curveob", text="", icon='CURVE_DATA')
        layout.prop(self, "resolution")
        layout.prop(self, "scale")
        layout.prop(self, "rotation")
        layout.prop(self, "splineidx")
        layout.prop(self, "snapto")

    def execute(self, context):
        ob = bpy.context.active_object
        me = ob.data
        bm = bmesh.from_edit_mesh(me)

        # Get the selected curve object and the required spline
        cuob = context.scene.objects[int(self.curveob)]
        cu = cuob.data

        self.splineidx = min(self.splineidx, len(cu.splines) - 1)
        p = cu.splines[self.splineidx].bezier_points

        # Get the property values
        res = self.resolution
        scale = self.scale
        rotation = self.rotation
        dscale = (1 - scale) / res
        drot = rotation / res

        # Get the matrices to convert between spaces
        cmat = ob.matrix_world.inverted() * cuob.matrix_world
        ctanmat = cmat.to_3x3().inverted().transposed()

        # The list of parameter values to evaluate the bezier curve at
        tvals = [t / res for t in range(res + 1)]

        # Get the first selected face, if none, cancel
        for f in bm.faces:
            if f.select:
                break
        else:
            return {'CANCELLED'}

        # Get the position vecs on the curve and tangent values
        bezval = [eval_bez(cmat, p, t) for t in tvals]
        beztan = [eval_bez_tan(ctanmat, p, t) for t in tvals]
        bezquat = [0] * len(tvals)

        # Using curve only
        bezquat[0] = beztan[0].to_track_quat('Z', 'Y')
        fquat = bezquat[0].inverted()

        # Calculate the min twist orientations
        for i in range(1, res + 1):
            ang = beztan[i - 1].angle(beztan[i], 0.0)
            if ang > 0.0:
                axis = beztan[i - 1].cross(beztan[i])
                q = Quaternion(axis, ang)
                bezquat[i] = q * bezquat[i - 1]
            else:
                bezquat[i] = bezquat[i - 1].copy()

        # Get the faces to be modified
        fprev = f
        # no = f.normal.copy()
        faces = [f.copy() for i in range(res)]

        # Offset if we need to snap to the face
        offset = Vector() if not self.snapto else (f.calc_center_median() - bezval[0])

        # For each of the faces created, set their vert positions and create side faces
        for i, data in enumerate(zip(faces, bezval[1:], bezquat[1:])):

            fn, pos, quat = data
            cen = fn.calc_center_median()

            rotquat = Quaternion((0, 0, 1), i * drot)

            for v in fn.verts:
                v.co = quat * rotquat * fquat * (v.co - cen) * (1 - (i + 1) * dscale) + pos + offset

            for ll, ul in zip(fprev.loops, fn.loops):
                ff = bm.faces.new((ll.vert, ll.link_loop_next.vert, ul.link_loop_next.vert, ul.vert))
                ff.normal_update()

            bm.faces.remove(fprev)
            fprev = fn

        me.calc_tessface()
        me.calc_normals()
        me.update()

        return {'FINISHED'}


def register():
    bpy.utils.register_module(__name__)


def unregister():
    bpy.utils.unregister_module(__name__)


if __name__ == "__main__":
    register()

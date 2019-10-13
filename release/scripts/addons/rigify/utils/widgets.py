#====================== BEGIN GPL LICENSE BLOCK ======================
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
#======================= END GPL LICENSE BLOCK ========================

# <pep8 compliant>

import bpy
import math

from mathutils import Matrix

from .errors import MetarigError
from .collections import ensure_widget_collection

WGT_PREFIX = "WGT-"  # Prefix for widget objects

#=============================================
# Widget creation
#=============================================


def obj_to_bone(obj, rig, bone_name, bone_transform_name=None):
    """ Places an object at the location/rotation/scale of the given bone.
    """
    if bpy.context.mode == 'EDIT_ARMATURE':
        raise MetarigError("obj_to_bone(): does not work while in edit mode")

    bone = rig.pose.bones[bone_name]
    scale = bone.custom_shape_scale

    if bone.use_custom_shape_bone_size:
        scale *= bone.length

    if bone_transform_name is not None:
        bone = rig.pose.bones[bone_transform_name]
    elif bone.custom_shape_transform:
        bone = bone.custom_shape_transform

    obj.rotation_mode = 'XYZ'
    obj.matrix_basis = rig.matrix_world @ bone.bone.matrix_local @ Matrix.Scale(scale, 4)


def create_widget(rig, bone_name, bone_transform_name=None):
    """ Creates an empty widget object for a bone, and returns the object.
    """
    obj_name = WGT_PREFIX + rig.name + '_' + bone_name
    scene = bpy.context.scene
    collection = ensure_widget_collection(bpy.context)

    # Check if it already exists in the scene
    if obj_name in scene.objects:
        # Move object to bone position, in case it changed
        obj = scene.objects[obj_name]
        obj_to_bone(obj, rig, bone_name, bone_transform_name)

        return None
    else:
        # Delete object if it exists in blend data but not scene data.
        # This is necessary so we can then create the object without
        # name conflicts.
        if obj_name in bpy.data.objects:
            bpy.data.objects[obj_name].user_clear()
            bpy.data.objects.remove(bpy.data.objects[obj_name])

        # Create mesh object
        mesh = bpy.data.meshes.new(obj_name)
        obj = bpy.data.objects.new(obj_name, mesh)
        collection.objects.link(obj)

        # Move object to bone position and set layers
        obj_to_bone(obj, rig, bone_name, bone_transform_name)
        wgts_group_name = 'WGTS_' + rig.name
        if wgts_group_name in bpy.data.objects.keys():
            obj.parent = bpy.data.objects[wgts_group_name]

        return obj


def create_circle_polygon(number_verts, axis, radius=1.0, head_tail=0.0):
    """ Creates a basic circle around of an axis selected.
        number_verts: number of vertices of the polygon
        axis: axis normal to the circle
        radius: the radius of the circle
        head_tail: where along the length of the bone the circle is (0.0=head, 1.0=tail)
    """
    verts = []
    edges = []
    angle = 2 * math.pi / number_verts
    i = 0

    assert(axis in 'XYZ')

    while i < (number_verts):
        a = math.cos(i * angle)
        b = math.sin(i * angle)

        if axis == 'X':
            verts.append((head_tail, a * radius, b * radius))
        elif axis == 'Y':
            verts.append((a * radius, head_tail, b * radius))
        elif axis == 'Z':
            verts.append((a * radius, b * radius, head_tail))

        if i < (number_verts - 1):
            edges.append((i , i + 1))

        i += 1

    edges.append((0, number_verts - 1))

    return verts, edges


def adjust_widget_axis(obj, axis='y', offset=0.0):
    mesh = obj.data

    if axis[0] == '-':
        s = -1.0
        axis = axis[1]
    else:
        s = 1.0

    trans_matrix = Matrix.Translation((0.0, offset, 0.0))
    rot_matrix = Matrix.Diagonal((1.0, s, 1.0, 1.0))

    if axis == "x":
        rot_matrix = Matrix.Rotation(-s*math.pi/2, 4, 'Z')
        trans_matrix = Matrix.Translation((offset, 0.0, 0.0))

    elif axis == "z":
        rot_matrix = Matrix.Rotation(s*math.pi/2, 4, 'X')
        trans_matrix = Matrix.Translation((0.0, 0.0, offset))

    matrix = trans_matrix @ rot_matrix

    for vert in mesh.vertices:
        vert.co = matrix @ vert.co


def adjust_widget_transform_mesh(obj, matrix, local=None):
    """Adjust the generated widget by applying a correction matrix to the mesh.
       If local is false, the matrix is in world space.
       If local is True, it's in the local space of the widget.
       If local is a bone, it's in the local space of the bone.
    """
    if obj:
        if local is not True:
            if local:
                assert isinstance(local, bpy.types.PoseBone)
                bonemat = local.id_data.matrix_world @ local.bone.matrix_local
                matrix = bonemat @ matrix @ bonemat.inverted()

            obmat = obj.matrix_basis
            matrix = obmat.inverted() @ matrix @ obmat

        obj.data.transform(matrix)


def write_widget(obj):
    """ Write a mesh object as a python script for widget use.
    """
    script = ""
    script += "def create_thing_widget(rig, bone_name, size=1.0, bone_transform_name=None):\n"
    script += "    obj = create_widget(rig, bone_name, bone_transform_name)\n"
    script += "    if obj is not None:\n"

    # Vertices
    script += "        verts = ["
    for i, v in enumerate(obj.data.vertices):
        script += "({:g}*size, {:g}*size, {:g}*size),".format(v.co[0], v.co[1], v.co[2])
        script += "\n                 " if i % 2 == 1 else " "
    script += "]\n"

    # Edges
    script += "        edges = ["
    for i, e in enumerate(obj.data.edges):
        script += "(" + str(e.vertices[0]) + ", " + str(e.vertices[1]) + "),"
        script += "\n                 " if i % 10 == 9 else " "
    script += "]\n"

    # Faces
    script += "        faces = ["
    for i, f in enumerate(obj.data.polygons):
        script += "("
        for v in f.vertices:
            script += str(v) + ", "
        script += "),"
        script += "\n                 " if i % 10 == 9 else " "
    script += "]\n"

    # Build mesh
    script += "\n        mesh = obj.data\n"
    script += "        mesh.from_pydata(verts, edges, faces)\n"
    script += "        mesh.update()\n"
    script += "        return obj\n"
    script += "    else:\n"
    script += "        return None\n"

    return script

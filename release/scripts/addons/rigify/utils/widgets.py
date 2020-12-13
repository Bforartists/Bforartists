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
import inspect
import functools

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


def create_widget(rig, bone_name, bone_transform_name=None, *, widget_name=None, widget_force_new=False):
    """ Creates an empty widget object for a bone, and returns the object.
    """
    assert rig.mode != 'EDIT'

    obj_name = widget_name or WGT_PREFIX + rig.name + '_' + bone_name
    scene = bpy.context.scene
    collection = ensure_widget_collection(bpy.context, 'WGTS_' + rig.name)
    reuse_mesh = None

    # Check if it already exists in the scene
    if not widget_force_new:
        if obj_name in scene.objects:
            # Move object to bone position, in case it changed
            obj = scene.objects[obj_name]
            obj_to_bone(obj, rig, bone_name, bone_transform_name)

            return None

        # Delete object if it exists in blend data but not scene data.
        # This is necessary so we can then create the object without
        # name conflicts.
        if obj_name in bpy.data.objects:
            bpy.data.objects.remove(bpy.data.objects[obj_name])

        # Create a linked duplicate of the widget assigned in the metarig
        reuse_widget = rig.pose.bones[bone_name].custom_shape
        if reuse_widget:
            reuse_mesh = reuse_widget.data

    # Create mesh object
    mesh = reuse_mesh or bpy.data.meshes.new(obj_name)
    obj = bpy.data.objects.new(obj_name, mesh)
    collection.objects.link(obj)

    # Move object to bone position and set layers
    obj_to_bone(obj, rig, bone_name, bone_transform_name)

    if reuse_mesh:
        return None

    return obj


#=============================================
# Widget choice dropdown
#=============================================

_registered_widgets = {}


def _get_valid_args(callback, skip):
    spec = inspect.getfullargspec(callback)
    return set(spec.args[skip:] + spec.kwonlyargs)


def register_widget(name, callback, **default_args):
    unwrapped = inspect.unwrap(callback)
    if unwrapped != callback:
        valid_args = _get_valid_args(unwrapped, 1)
    else:
        valid_args = _get_valid_args(callback, 2)

    _registered_widgets[name] = (callback, valid_args, default_args)


def layout_widget_dropdown(layout, props, prop_name, **kwargs):
    "Create a UI dropdown to select a widget from the known list."

    id_store = bpy.context.window_manager
    rigify_widgets = id_store.rigify_widgets

    rigify_widgets.clear()

    for name in sorted(_registered_widgets):
        item = rigify_widgets.add()
        item.name = name

    layout.prop_search(props, prop_name, id_store, "rigify_widgets", **kwargs)


def create_registered_widget(obj, bone_name, widget_id, **kwargs):
    try:
        callback, valid_args, default_args = _registered_widgets[widget_id]
    except KeyError:
        raise MetarigError("Unknown widget name: " + widget_id)

    # Convert between radius and size
    if kwargs.get('size') and 'size' not in valid_args:
        if 'radius' in valid_args and not kwargs.get('radius'):
            kwargs['radius'] = kwargs['size'] / 2

    elif kwargs.get('radius') and 'radius' not in valid_args:
        if 'size' in valid_args and not kwargs.get('size'):
            kwargs['size'] = kwargs['radius'] * 2

    args = { **default_args, **kwargs }

    return callback(obj, bone_name, **{ k:v for k,v in args.items() if k in valid_args})


#=============================================
# Widget geometry
#=============================================

class GeometryData:
    def __init__(self):
        self.verts = []
        self.edges = []
        self.faces = []


def widget_generator(generate_func=None, *, register=None, subsurf=0):
    if generate_func is None:
        return functools.partial(widget_generator, register=register, subsurf=subsurf)

    """
    Decorator that encapsulates a call to create_widget, and only requires
    the actual function to fill the provided vertex and edge lists.

    Accepts parameters of create_widget, plus any keyword arguments the
    wrapped function has.
    """
    @functools.wraps(generate_func)
    def wrapper(rig, bone_name, bone_transform_name=None, widget_name=None, widget_force_new=False, **kwargs):
        obj = create_widget(rig, bone_name, bone_transform_name, widget_name=widget_name, widget_force_new=widget_force_new)
        if obj is not None:
            geom = GeometryData()

            generate_func(geom, **kwargs)

            mesh = obj.data
            mesh.from_pydata(geom.verts, geom.edges, geom.faces)
            mesh.update()

            if subsurf:
                mod = obj.modifiers.new("subsurf", 'SUBSURF')
                mod.levels = subsurf

            return obj
        else:
            return None

    if register:
        register_widget(register, wrapper)

    return wrapper


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


def write_widget(obj, name='thing', use_size=True):
    """ Write a mesh object as a python script for widget use.
    """
    script = ""
    script += "@widget_generator\n"
    script += "def create_"+name+"_widget(geom";
    if use_size:
        script += ", *, size=1.0"
    script += "):\n"

    # Vertices
    szs = "*size" if use_size else ""
    width = 2 if use_size else 3

    script += "    geom.verts = ["
    for i, v in enumerate(obj.data.vertices):
        script += "({:g}{}, {:g}{}, {:g}{}),".format(v.co[0], szs, v.co[1], szs, v.co[2], szs)
        script += "\n                  " if i % width == (width - 1) else " "
    script += "]\n"

    # Edges
    script += "    geom.edges = ["
    for i, e in enumerate(obj.data.edges):
        script += "(" + str(e.vertices[0]) + ", " + str(e.vertices[1]) + "),"
        script += "\n                  " if i % 10 == 9 else " "
    script += "]\n"

    # Faces
    if obj.data.polygons:
        script += "    geom.faces = ["
        for i, f in enumerate(obj.data.polygons):
            script += "(" + ", ".join(str(v) for v in f.vertices) + "),"
            script += "\n                  " if i % 10 == 9 else " "
        script += "]\n"

    return script

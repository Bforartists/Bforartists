# SPDX-FileCopyrightText: 2015-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

# Original by Fourmadmen

import bpy
from mathutils import (
        Vector,
        Quaternion,
        )
from math import pi
from bpy.props import (
        IntProperty,
        FloatProperty,
        StringProperty,
        BoolProperty,
        )
from bpy_extras import object_utils

# Create a new mesh (object) from verts/edges/faces.
# verts/edges/faces ... List of vertices/edges/faces for the
#                       new mesh (as used in from_pydata)
# name ... Name of the new mesh (& object)

def create_mesh_object(context, verts, edges, faces, name):

    # Create new mesh
    mesh = bpy.data.meshes.new(name)

    # Make a mesh from a list of verts/edges/faces.
    mesh.from_pydata(verts, edges, faces)

    # Update mesh geometry after adding stuff.
    mesh.update()

    from bpy_extras import object_utils
    return object_utils.object_data_add(context, mesh, operator=None)


# A very simple "bridge" tool.

def createFaces(vertIdx1, vertIdx2, closed=False, flipped=False):
    faces = []

    if not vertIdx1 or not vertIdx2:
        return None

    if len(vertIdx1) < 2 and len(vertIdx2) < 2:
        return None

    fan = False
    if (len(vertIdx1) != len(vertIdx2)):
        if (len(vertIdx1) == 1 and len(vertIdx2) > 1):
            fan = True
        else:
            return None

    total = len(vertIdx2)

    if closed:
        # Bridge the start with the end.
        if flipped:
            face = [
                vertIdx1[0],
                vertIdx2[0],
                vertIdx2[total - 1]]
            if not fan:
                face.append(vertIdx1[total - 1])
            faces.append(face)

        else:
            face = [vertIdx2[0], vertIdx1[0]]
            if not fan:
                face.append(vertIdx1[total - 1])
            face.append(vertIdx2[total - 1])
            faces.append(face)

    # Bridge the rest of the faces.
    for num in range(total - 1):
        if flipped:
            if fan:
                face = [vertIdx2[num], vertIdx1[0], vertIdx2[num + 1]]
            else:
                face = [vertIdx2[num], vertIdx1[num],
                        vertIdx1[num + 1], vertIdx2[num + 1]]
            faces.append(face)
        else:
            if fan:
                face = [vertIdx1[0], vertIdx2[num], vertIdx2[num + 1]]
            else:
                face = [vertIdx1[num], vertIdx2[num],
                        vertIdx2[num + 1], vertIdx1[num + 1]]
            faces.append(face)

    return faces


# @todo Clean up vertex&face creation process a bit.

def add_star(points, outer_radius, inner_radius, height):
    PI_2 = pi * 2
    z_axis = (0, 0, 1)

    verts = []
    faces = []

    segments = points * 2

    half_height = height / 2.0

    vert_idx_top = len(verts)
    verts.append(Vector((0.0, 0.0, half_height)))

    vert_idx_bottom = len(verts)
    verts.append(Vector((0.0, 0.0, -half_height)))

    edgeloop_top = []
    edgeloop_bottom = []

    for index in range(segments):
        quat = Quaternion(z_axis, (index / segments) * PI_2)

        if index % 2:
            # Uneven
            radius = outer_radius
        else:
            # Even
            radius = inner_radius

        edgeloop_top.append(len(verts))
        vec = quat @ Vector((radius, 0, half_height))
        verts.append(vec)

        edgeloop_bottom.append(len(verts))
        vec = quat @ Vector((radius, 0, -half_height))
        verts.append(vec)

    faces_top = createFaces([vert_idx_top], edgeloop_top, closed=True)
    faces_outside = createFaces(edgeloop_top, edgeloop_bottom, closed=True)
    faces_bottom = createFaces([vert_idx_bottom], edgeloop_bottom,
        flipped=True, closed=True)

    faces.extend(faces_top)
    faces.extend(faces_outside)
    faces.extend(faces_bottom)

    return verts, faces


class AddStar(bpy.types.Operator, object_utils.AddObjectHelper):
    bl_idname = "mesh.primitive_star_add"
    bl_label = "Simple Star"
    bl_description = "Construct a star mesh"
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}

    Star : BoolProperty(name = "Star",
                default = True,
                description = "Star")
    change : BoolProperty(name = "Change",
                default = False,
                description = "change Star")

    points: IntProperty(
        name="Points",
        description="Number of points for the star",
        min=2,
        max=256,
        default=5
        )
    outer_radius: FloatProperty(
        name="Outer Radius",
        description="Outer radius of the star",
        min=0.01,
        max=9999.0,
        default=1.0
        )
    innter_radius: FloatProperty(
        name="Inner Radius",
        description="Inner radius of the star",
        min=0.01,
        max=9999.0,
        default=0.5
        )
    height: FloatProperty(name="Height",
        description="Height of the star",
        min=0.01,
        max=9999.0,
        default=0.5
        )

    def draw(self, context):
        layout = self.layout

        layout.prop(self, 'points', expand=True)
        layout.prop(self, 'outer_radius', expand=True)
        layout.prop(self, 'innter_radius', expand=True)
        layout.prop(self, 'height', expand=True)

        if self.change == False:
            col = layout.column(align=True)
            col.prop(self, 'align', expand=True)
            col = layout.column(align=True)
            col.prop(self, 'location', expand=True)
            col = layout.column(align=True)
            col.prop(self, 'rotation', expand=True)

    def execute(self, context):
        # turn off 'Enter Edit Mode'
        use_enter_edit_mode = bpy.context.preferences.edit.use_enter_edit_mode
        bpy.context.preferences.edit.use_enter_edit_mode = False

        if bpy.context.mode == "OBJECT":
            if context.selected_objects != [] and context.active_object and \
                (context.active_object.data is not None) and ('Star' in context.active_object.data.keys()) and \
                (self.change == True):
                obj = context.active_object
                oldmesh = obj.data
                oldmeshname = obj.data.name
                verts, faces = add_star(
                        self.points,
                        self.outer_radius,
                        self.innter_radius,
                        self.height
                        )
                mesh = bpy.data.meshes.new('Star')
                mesh.from_pydata(verts, [], faces)
                obj.data = mesh
                for material in oldmesh.materials:
                    obj.data.materials.append(material)
                bpy.data.meshes.remove(oldmesh)
                obj.data.name = oldmeshname
            else:
                verts, faces = add_star(
                        self.points,
                        self.outer_radius,
                        self.innter_radius,
                        self.height
                        )
                mesh = bpy.data.meshes.new('Star')
                mesh.from_pydata(verts, [], faces)
                obj = object_utils.object_data_add(context, mesh, operator=self)

            obj.data["Star"] = True
            obj.data["change"] = False
            for prm in StarParameters():
                obj.data[prm] = getattr(self, prm)

        if bpy.context.mode == "EDIT_MESH":
            active_object = context.active_object
            name_active_object = active_object.name
            bpy.ops.object.mode_set(mode='OBJECT')
            verts, faces = add_star(
                        self.points,
                        self.outer_radius,
                        self.innter_radius,
                        self.height
                        )
            mesh = bpy.data.meshes.new('Star')
            mesh.from_pydata(verts, [], faces)
            obj = object_utils.object_data_add(context, mesh, operator=self)
            obj.select_set(True)
            active_object.select_set(True)
            bpy.context.view_layer.objects.active = active_object
            bpy.ops.object.join()
            context.active_object.name = name_active_object
            bpy.ops.object.mode_set(mode='EDIT')

        if use_enter_edit_mode:
            bpy.ops.object.mode_set(mode = 'EDIT')

        # restore pre operator state
        bpy.context.preferences.edit.use_enter_edit_mode = use_enter_edit_mode

        return {'FINISHED'}

def StarParameters():
    StarParameters = [
        "points",
        "outer_radius",
        "innter_radius",
        "height",
        ]
    return StarParameters

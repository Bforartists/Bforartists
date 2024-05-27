# SPDX-FileCopyrightText: 2010-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

# Author: Paulo_Gomes

import bpy
from mathutils import Quaternion, Vector
from math import cos, sin, pi
from bpy.props import (
        FloatProperty,
        IntProperty,
        BoolProperty,
        StringProperty,
        )
from bpy_extras import object_utils


# Create a new mesh (object) from verts/edges/faces
# verts/edges/faces ... List of vertices/edges/faces for the
#                       new mesh (as used in from_pydata)
# name ... Name of the new mesh (& object)

def create_mesh_object(context, verts, edges, faces, name):

    # Create new mesh
    mesh = bpy.data.meshes.new(name)

    # Make a mesh from a list of verts/edges/faces
    mesh.from_pydata(verts, edges, faces)

    # Update mesh geometry after adding stuff
    mesh.update()

    from bpy_extras import object_utils
    return object_utils.object_data_add(context, mesh, operator=None)


# A very simple "bridge" tool

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
        # Bridge the start with the end
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

    # Bridge the rest of the faces
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


def add_twisted_torus(major_rad, minor_rad, major_seg, minor_seg, twists):
    PI_2 = pi * 2.0
    z_axis = (0.0, 0.0, 1.0)

    verts = []
    faces = []

    edgeloop_prev = []
    for major_index in range(major_seg):
        quat = Quaternion(z_axis, (major_index / major_seg) * PI_2)
        rot_twists = PI_2 * major_index / major_seg * twists

        edgeloop = []

        # Create section ring
        for minor_index in range(minor_seg):
            angle = (PI_2 * minor_index / minor_seg) + rot_twists

            vec = Vector((
                major_rad + (cos(angle) * minor_rad),
                0.0,
                sin(angle) * minor_rad))
            vec = quat @ vec

            edgeloop.append(len(verts))
            verts.append(vec)

        # Remember very first edgeloop
        if major_index == 0:
            edgeloop_first = edgeloop

        # Bridge last with current ring
        if edgeloop_prev:
            f = createFaces(edgeloop_prev, edgeloop, closed=True)
            faces.extend(f)

        edgeloop_prev = edgeloop

    # Bridge first and last ring
    f = createFaces(edgeloop_prev, edgeloop_first, closed=True)
    faces.extend(f)

    return verts, faces


class AddTwistedTorus(bpy.types.Operator, object_utils.AddObjectHelper):
    bl_idname = "mesh.primitive_twisted_torus_add"
    bl_label = "Add Twisted Torus"
    bl_description = "Construct a twisted torus mesh"
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}

    TwistedTorus : BoolProperty(name = "TwistedTorus",
                default = True,
                description = "TwistedTorus")
    change : BoolProperty(name = "Change",
                default = False,
                description = "change TwistedTorus")

    major_radius: FloatProperty(
        name="Major Radius",
        description="Radius from the origin to the"
                    " center of the cross section",
        min=0.01,
        max=100.0,
        default=1.0
        )
    minor_radius: FloatProperty(
        name="Minor Radius",
        description="Radius of the torus' cross section",
        min=0.01,
        max=100.0,
        default=0.25
        )
    major_segments: IntProperty(
        name="Major Segments",
        description="Number of segments for the main ring of the torus",
        min=3,
        max=256,
        default=48
        )
    minor_segments: IntProperty(
        name="Minor Segments",
        description="Number of segments for the minor ring of the torus",
        min=3,
        max=256,
        default=12
        )
    twists: IntProperty(
        name="Twists",
        description="Number of twists of the torus",
        min=0,
        max=256,
        default=1
        )
    use_abso: BoolProperty(
        name="Use Int/Ext Controls",
        description="Use the Int/Ext controls for torus dimensions",
        default=False
        )
    abso_major_rad: FloatProperty(
        name="Exterior Radius",
        description="Total Exterior Radius of the torus",
        min=0.01,
        max=100.0,
        default=1.0
        )
    abso_minor_rad: FloatProperty(
        name="Inside Radius",
        description="Total Interior Radius of the torus",
        min=0.01,
        max=100.0,
        default=0.5
        )

    def draw(self, context):
        layout = self.layout

        layout.prop(self, 'major_radius', expand=True)
        layout.prop(self, 'minor_radius', expand=True)
        layout.prop(self, 'major_segments', expand=True)
        layout.prop(self, 'minor_segments', expand=True)
        layout.prop(self, 'twists', expand=True)
        layout.prop(self, 'use_abso', expand=True)
        layout.prop(self, 'abso_major_rad', expand=True)
        layout.prop(self, 'abso_minor_rad', expand=True)

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

        if self.use_abso is True:
            extra_helper = (self.abso_major_rad - self.abso_minor_rad) * 0.5
            self.major_radius = self.abso_minor_rad + extra_helper
            self.minor_radius = extra_helper

        if bpy.context.mode == "OBJECT":
            if context.selected_objects != [] and context.active_object and \
                (context.active_object.data is not None) and ('TwistedTorus' in context.active_object.data.keys()) and \
                (self.change == True):
                obj = context.active_object
                oldmesh = obj.data
                oldmeshname = obj.data.name
                verts, faces = add_twisted_torus(
                            self.major_radius,
                            self.minor_radius,
                            self.major_segments,
                            self.minor_segments,
                            self.twists
                            )
                mesh = bpy.data.meshes.new('TwistedTorus')
                mesh.from_pydata(verts, [], faces)
                obj.data = mesh
                for material in oldmesh.materials:
                    obj.data.materials.append(material)
                bpy.data.meshes.remove(oldmesh)
                obj.data.name = oldmeshname
            else:
                verts, faces = add_twisted_torus(
                            self.major_radius,
                            self.minor_radius,
                            self.major_segments,
                            self.minor_segments,
                            self.twists
                            )
                mesh = bpy.data.meshes.new('TwistedTorus')
                mesh.from_pydata(verts, [], faces)
                obj = object_utils.object_data_add(context, mesh, operator=self)

            obj.data["TwistedTorus"] = True
            obj.data["change"] = False
            for prm in TwistedTorusParameters():
                obj.data[prm] = getattr(self, prm)

        if bpy.context.mode == "EDIT_MESH":
            active_object = context.active_object
            name_active_object = active_object.name
            bpy.ops.object.mode_set(mode='OBJECT')
            verts, faces = add_twisted_torus(
                            self.major_radius,
                            self.minor_radius,
                            self.major_segments,
                            self.minor_segments,
                            self.twists
                            )
            mesh = bpy.data.meshes.new('TwistedTorus')
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

def TwistedTorusParameters():
    TwistedTorusParameters = [
        "major_radius",
        "minor_radius",
        "major_segments",
        "minor_segments",
        "twists",
        "use_abso",
        "abso_major_rad",
        "abso_minor_rad",
        ]
    return TwistedTorusParameters

# SPDX-FileCopyrightText: 2010-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

# Author: Pontiac, Fourmadmen, Dreampainter

import bpy
from bpy.types import Operator
from mathutils import (
        Vector,
        Quaternion,
        )
from math import cos, sin, pi
from bpy.props import (
        FloatProperty,
        IntProperty,
        BoolProperty,
        StringProperty,
        )
from bpy_extras import object_utils

# Create a new mesh (object) from verts/edges/faces.
# verts/edges/faces ... List of vertices/edges/faces for the
#                       new mesh (as used in from_pydata)
# name ... Name of the new mesh (& object)

def create_mesh_object(context, self, verts, edges, faces, name):

    # Create new mesh
    mesh = bpy.data.meshes.new(name)

    # Make a mesh from a list of verts/edges/faces.
    mesh.from_pydata(verts, edges, faces)

    # Update mesh geometry after adding stuff.
    mesh.update()

    from bpy_extras import object_utils
    return object_utils.object_data_add(context, mesh, operator=self)


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


# @todo Clean up vertex&face creation process a bit.
def add_gem(r1, r2, seg, h1, h2):
    """
    r1 = pavilion radius
    r2 = crown radius
    seg = number of segments
    h1 = pavilion height
    h2 = crown height
    Generates the vertices and faces of the gem
    """

    verts = []

    a = 2.0 * pi / seg             # Angle between segments
    offset = a / 2.0               # Middle between segments

    r3 = ((r1 + r2) / 2.0) / cos(offset)  # Middle of crown
    r4 = (r1 / 2.0) / cos(offset)  # Middle of pavilion
    h3 = h2 / 2.0                  # Middle of crown height
    h4 = -h1 / 2.0                 # Middle of pavilion height

    # Tip
    vert_tip = len(verts)
    verts.append(Vector((0.0, 0.0, -h1)))

    # Middle vertex of the flat side (crown)
    vert_flat = len(verts)
    verts.append(Vector((0.0, 0.0, h2)))

    edgeloop_flat = []
    for i in range(seg):
        s1 = sin(i * a)
        s2 = sin(offset + i * a)
        c1 = cos(i * a)
        c2 = cos(offset + i * a)

        verts.append((r4 * s1, r4 * c1, h4))    # Middle of pavilion
        verts.append((r1 * s2, r1 * c2, 0.0))   # Pavilion
        verts.append((r3 * s1, r3 * c1, h3))    # Middle crown
        edgeloop_flat.append(len(verts))
        verts.append((r2 * s2, r2 * c2, h2))    # Crown

    faces = []

    for index in range(seg):
        i = index * 4
        j = ((index + 1) % seg) * 4

        faces.append([j + 2, vert_tip, i + 2, i + 3])  # Tip -> Middle of pav
        faces.append([j + 2, i + 3, j + 3])            # Middle of pav -> pav
        faces.append([j + 3, i + 3, j + 4])            # Pav -> Middle crown
        faces.append([j + 4, i + 3, i + 4, i + 5])     # Crown quads
        faces.append([j + 4, i + 5, j + 5])            # Middle crown -> crown

    faces_flat = createFaces([vert_flat], edgeloop_flat, closed=True, flipped=True)
    faces.extend(faces_flat)

    return verts, faces


def add_diamond(segments, girdle_radius, table_radius,
                crown_height, pavilion_height):

    PI_2 = pi * 2.0
    z_axis = (0.0, 0.0, -1.0)

    verts = []
    faces = []

    height_flat = crown_height
    height_middle = 0.0
    height_tip = -pavilion_height

    # Middle vertex of the flat side (crown)
    vert_flat = len(verts)
    verts.append(Vector((0.0, 0.0, height_flat)))

    # Tip
    vert_tip = len(verts)
    verts.append(Vector((0.0, 0.0, height_tip)))

    verts_flat = []
    verts_girdle = []

    for index in range(segments):
        quat = Quaternion(z_axis, (index / segments) * PI_2)

        # angle = PI_2 * index / segments  # UNUSED

        # Row for flat side
        verts_flat.append(len(verts))
        vec = quat @ Vector((table_radius, 0.0, height_flat))
        verts.append(vec)

        # Row for the middle/girdle
        verts_girdle.append(len(verts))
        vec = quat @ Vector((girdle_radius, 0.0, height_middle))
        verts.append(vec)

    # Flat face
    faces_flat = createFaces([vert_flat], verts_flat, closed=True,
        flipped=True)
    # Side face
    faces_side = createFaces(verts_girdle, verts_flat, closed=True)
    # Tip faces
    faces_tip = createFaces([vert_tip], verts_girdle, closed=True)

    faces.extend(faces_tip)
    faces.extend(faces_side)
    faces.extend(faces_flat)

    return verts, faces


class AddDiamond(Operator, object_utils.AddObjectHelper):
    bl_idname = "mesh.primitive_diamond_add"
    bl_label = "Add Diamond"
    bl_description = "Construct a diamond mesh"
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}

    Diamond : BoolProperty(name = "Diamond",
                default = True,
                description = "Diamond")

    #### change properties
    name : StringProperty(name = "Name",
                    description = "Name")

    change : BoolProperty(name = "Change",
                default = False,
                description = "change Diamond")

    segments: IntProperty(
            name="Segments",
            description="Number of segments for the diamond",
            min=3,
            max=256,
            default=32
            )
    girdle_radius: FloatProperty(
            name="Girdle Radius",
            description="Girdle radius of the diamond",
            min=0.01,
            max=9999.0,
            default=1.0
            )
    table_radius: FloatProperty(
            name="Table Radius",
            description="Girdle radius of the diamond",
            min=0.01,
            max=9999.0,
            default=0.6
            )
    crown_height: FloatProperty(
            name="Crown Height",
            description="Crown height of the diamond",
            min=0.01,
            max=9999.0,
            default=0.35
            )
    pavilion_height: FloatProperty(
            name="Pavilion Height",
            description="Pavilion height of the diamond",
            min=0.01,
            max=9999.0,
            default=0.8
            )

    def draw(self, context):
        layout = self.layout
        box = layout.box()
        box.prop(self, "segments")
        box.prop(self, "girdle_radius")
        box.prop(self, "table_radius")
        box.prop(self, "crown_height")
        box.prop(self, "pavilion_height")

        if self.change == False:
            # generic transform props
            box = layout.box()
            box.prop(self, 'align', expand=True)
            box.prop(self, 'location', expand=True)
            box.prop(self, 'rotation', expand=True)

    def execute(self, context):
        # turn off 'Enter Edit Mode'
        use_enter_edit_mode = bpy.context.preferences.edit.use_enter_edit_mode
        bpy.context.preferences.edit.use_enter_edit_mode = False

        if bpy.context.mode == "OBJECT":
            if context.selected_objects != [] and context.active_object and \
                (context.active_object.data is not None) and ('Diamond' in context.active_object.data.keys()) and \
                (self.change == True):
                obj = context.active_object
                oldmesh = obj.data
                oldmeshname = obj.data.name

                verts, faces = add_diamond(self.segments,
                    self.girdle_radius,
                    self.table_radius,
                    self.crown_height,
                    self.pavilion_height)
                mesh = bpy.data.meshes.new("TMP")
                mesh.from_pydata(verts, [], faces)
                mesh.update()
                obj.data = mesh

                for material in oldmesh.materials:
                    obj.data.materials.append(material)

                bpy.data.meshes.remove(oldmesh)
                obj.data.name = oldmeshname
            else:
                verts, faces = add_diamond(self.segments,
                    self.girdle_radius,
                    self.table_radius,
                    self.crown_height,
                    self.pavilion_height)

                obj = create_mesh_object(context, self, verts, [], faces, "Diamond")

            obj.data["Diamond"] = True
            obj.data["change"] = False
            for prm in DiamondParameters():
                obj.data[prm] = getattr(self, prm)

        if bpy.context.mode == "EDIT_MESH":
            active_object = context.active_object
            name_active_object = active_object.name
            bpy.ops.object.mode_set(mode='OBJECT')
            verts, faces = add_diamond(self.segments,
                self.girdle_radius,
                self.table_radius,
                self.crown_height,
                self.pavilion_height)

            obj = create_mesh_object(context, self, verts, [], faces, "TMP")

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

def DiamondParameters():
    DiamondParameters = [
        "segments",
        "girdle_radius",
        "table_radius",
        "crown_height",
        "pavilion_height",
        ]
    return DiamondParameters


class AddGem(Operator, object_utils.AddObjectHelper):
    bl_idname = "mesh.primitive_gem_add"
    bl_label = "Add Gem"
    bl_description = "Construct an offset faceted gem mesh"
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}

    Gem : BoolProperty(name = "Gem",
                default = True,
                description = "Gem")

    #### change properties
    name : StringProperty(name = "Name",
                    description = "Name")

    change : BoolProperty(name = "Change",
                default = False,
                description = "change Gem")

    segments: IntProperty(
            name="Segments",
            description="Longitudial segmentation",
            min=3,
            max=265,
            default=8
            )
    pavilion_radius: FloatProperty(
            name="Radius",
            description="Radius of the gem",
            min=0.01,
            max=9999.0,
            default=1.0
            )
    crown_radius: FloatProperty(
            name="Table Radius",
            description="Radius of the table(top)",
            min=0.01,
            max=9999.0,
            default=0.6
            )
    crown_height: FloatProperty(
            name="Table height",
            description="Height of the top half",
            min=0.01,
            max=9999.0,
            default=0.35
            )
    pavilion_height: FloatProperty(
            name="Pavilion height",
            description="Height of bottom half",
            min=0.01,
            max=9999.0,
            default=0.8
            )

    def draw(self, context):
        layout = self.layout
        box = layout.box()
        box.prop(self, "segments")
        box.prop(self, "pavilion_radius")
        box.prop(self, "crown_radius")
        box.prop(self, "crown_height")
        box.prop(self, "pavilion_height")

        if self.change == False:
            # generic transform props
            box = layout.box()
            box.prop(self, 'align', expand=True)
            box.prop(self, 'location', expand=True)
            box.prop(self, 'rotation', expand=True)

    def execute(self, context):
        # turn off 'Enter Edit Mode'
        use_enter_edit_mode = bpy.context.preferences.edit.use_enter_edit_mode
        bpy.context.preferences.edit.use_enter_edit_mode = False

        if bpy.context.mode == "OBJECT":
            if context.selected_objects != [] and context.active_object and \
                (context.active_object.data is not None) and ('Gem' in context.active_object.data.keys()) and \
                (self.change == True):
                obj = context.active_object
                oldmesh = obj.data
                oldmeshname = obj.data.name
                verts, faces = add_gem(
                    self.pavilion_radius,
                    self.crown_radius,
                    self.segments,
                    self.pavilion_height,
                    self.crown_height)
                mesh = bpy.data.meshes.new("TMP")
                mesh.from_pydata(verts, [], faces)
                mesh.update()
                obj.data = mesh
                for material in oldmesh.materials:
                    obj.data.materials.append(material)
                bpy.data.meshes.remove(oldmesh)
                obj.data.name = oldmeshname
            else:
                verts, faces = add_gem(
                    self.pavilion_radius,
                    self.crown_radius,
                    self.segments,
                    self.pavilion_height,
                    self.crown_height)

                obj = create_mesh_object(context, self, verts, [], faces, "Gem")

            obj.data["Gem"] = True
            obj.data["change"] = False
            for prm in GemParameters():
                obj.data[prm] = getattr(self, prm)

        if bpy.context.mode == "EDIT_MESH":
            active_object = context.active_object
            name_active_object = active_object.name
            bpy.ops.object.mode_set(mode='OBJECT')
            verts, faces = add_gem(
                self.pavilion_radius,
                self.crown_radius,
                self.segments,
                self.pavilion_height,
                self.crown_height)

            obj = create_mesh_object(context, self, verts, [], faces, "TMP")

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

def GemParameters():
    GemParameters = [
        "segments",
        "pavilion_radius",
        "crown_radius",
        "crown_height",
        "pavilion_height",
        ]
    return GemParameters

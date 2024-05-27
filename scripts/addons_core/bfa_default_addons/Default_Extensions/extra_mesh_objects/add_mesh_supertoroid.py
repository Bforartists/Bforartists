# SPDX-FileCopyrightText: 2011-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

# Author: DreamPainter

import bpy
from bpy.props import (
        FloatProperty,
        BoolProperty,
        IntProperty,
        StringProperty,
        )
from math import pi, cos, sin
from mathutils import Vector
from bpy_extras import object_utils


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


def power(a, b):
    if a < 0:
        return -((-a) ** b)
    return a ** b


def supertoroid(R, r, u, v, n1, n2):
    """
    R = big radius
    r = small radius
    u = lateral segmentation
    v = radial segmentation
    n1 = value determines the shape of the torus
    n2 = value determines the shape of the cross-section
    """
    # create the necessary constants
    a = 2 * pi / u
    b = 2 * pi / v

    verts = []
    faces = []

    # create each cross-section by calculating each vector on the
    # the wannabe circle
    # x = (cos(theta) ** n1)*(R + r * (cos(phi) ** n2))
    # y = (sin(theta) ** n1)*(R + r * (cos(phi) ** n2))
    # z = (r * sin(phi) ** n2)
    # with theta and phi ranging from 0 to 2pi

    for i in range(u):
        s = power(sin(i * a), n1)
        c = power(cos(i * a), n1)
        for j in range(v):
            c2 = R + r * power(cos(j * b), n2)
            s2 = r * power(sin(j * b), n2)
            verts.append(Vector((c * c2, s * c2, s2)))

        # bridge the last circle with the previous circle
        if i > 0:   # but not for the first circle, 'cus there's no previous before the first
            f = createFaces(range((i - 1) * v, i * v), range(i * v, (i + 1) * v), closed=True)
            faces.extend(f)
    # bridge the last circle with the first
    f = createFaces(range((u - 1) * v, u * v), range(v), closed=True)
    faces.extend(f)

    return verts, faces


class add_supertoroid(bpy.types.Operator, object_utils.AddObjectHelper):
    bl_idname = "mesh.primitive_supertoroid_add"
    bl_label = "Add SuperToroid"
    bl_description = "Construct a supertoroid mesh"
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}

    SuperToroid : BoolProperty(name = "SuperToroid",
                default = True,
                description = "SuperToroid")
    change : BoolProperty(name = "Change",
                default = False,
                description = "change SuperToroid")

    R: FloatProperty(
            name="Big radius",
            description="The radius inside the tube",
            default=1.0,
            min=0.01, max=100.0
            )
    r: FloatProperty(
            name="Small radius",
            description="The radius of the tube",
            default=0.3,
            min=0.01, max=100.0
            )
    u: IntProperty(
            name="U-segments",
            description="Radial segmentation",
            default=16,
            min=3, max=265
            )
    v: IntProperty(
            name="V-segments",
            description="Lateral segmentation",
            default=8,
            min=3, max=265
            )
    n1: FloatProperty(
            name="Ring manipulator",
            description="Manipulates the shape of the Ring",
            default=1.0,
            min=0.01, max=100.0
            )
    n2: FloatProperty(
            name="Cross manipulator",
            description="Manipulates the shape of the cross-section",
            default=1.0,
            min=0.01, max=100.0
            )
    ie: BoolProperty(
            name="Use Int. and Ext. radii",
            description="Use internal and external radii",
            default=False
            )
    edit: BoolProperty(
            name="",
            description="",
            default=False,
            options={'HIDDEN'}
            )

    def draw(self, context):
        layout = self.layout

        layout.prop(self, 'R', expand=True)
        layout.prop(self, 'r', expand=True)
        layout.prop(self, 'u', expand=True)
        layout.prop(self, 'v', expand=True)
        layout.prop(self, 'n1', expand=True)
        layout.prop(self, 'n2', expand=True)
        layout.prop(self, 'ie', expand=True)

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

        props = self.properties

        # check how the radii properties must be used
        if props.ie:
            rad1 = (props.R + props.r) / 2
            rad2 = (props.R - props.r) / 2
            # for consistency in the mesh, ie no crossing faces, make the largest of the two
            # the outer radius
            if rad2 > rad1:
                [rad1, rad2] = [rad2, rad1]
        else:
            rad1 = props.R
            rad2 = props.r
            # again for consistency, make the radius in the tube,
            # at least as big as the radius of the tube
            if rad2 > rad1:
                rad1 = rad2

        if bpy.context.mode == "OBJECT":
            if context.selected_objects != [] and context.active_object and \
                (context.active_object.data is not None) and ('SuperToroid' in context.active_object.data.keys()) and \
                (self.change == True):
                obj = context.active_object
                oldmesh = obj.data
                oldmeshname = obj.data.name
                verts, faces = supertoroid(rad1,
                                  rad2,
                                  props.u,
                                  props.v,
                                  props.n1,
                                  props.n2
                                  )
                mesh = bpy.data.meshes.new('SuperToroid')
                mesh.from_pydata(verts, [], faces)
                obj.data = mesh
                for material in oldmesh.materials:
                    obj.data.materials.append(material)
                bpy.data.meshes.remove(oldmesh)
                obj.data.name = oldmeshname
            else:
                verts, faces = supertoroid(rad1,
                                  rad2,
                                  props.u,
                                  props.v,
                                  props.n1,
                                  props.n2
                                  )
                mesh = bpy.data.meshes.new('SuperToroid')
                mesh.from_pydata(verts, [], faces)
                obj = object_utils.object_data_add(context, mesh, operator=self)

            obj.data["SuperToroid"] = True
            obj.data["change"] = False
            for prm in SuperToroidParameters():
                obj.data[prm] = getattr(self, prm)

        if bpy.context.mode == "EDIT_MESH":
            active_object = context.active_object
            name_active_object = active_object.name
            bpy.ops.object.mode_set(mode='OBJECT')
            verts, faces = supertoroid(rad1,
                                  rad2,
                                  props.u,
                                  props.v,
                                  props.n1,
                                  props.n2
                                  )
            mesh = bpy.data.meshes.new('SuperToroid')
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

def SuperToroidParameters():
    SuperToroidParameters = [
        "R",
        "r",
        "u",
        "v",
        "n1",
        "n2",
        "ie",
        "edit",
        ]
    return SuperToroidParameters

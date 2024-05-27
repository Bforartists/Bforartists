# SPDX-FileCopyrightText: 2012-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

# Author: Anthony D'Agostino

import bpy
from mathutils import Vector
from math import sin, cos, pi
from bpy.props import (
        BoolProperty,
        IntProperty,
        StringProperty,
        )
from bpy_extras import object_utils


def create_mesh_object(context, verts, edges, faces, name):
    # Create new mesh
    mesh = bpy.data.meshes.new(name)
    # Make a mesh from a list of verts/edges/faces.
    mesh.from_pydata(verts, edges, faces)
    # Update mesh geometry after adding stuff.
    mesh.update()
    from bpy_extras import object_utils
    return object_utils.object_data_add(context, mesh, operator=None)


# ========================
# === Torus Knot Block ===
# ========================

def k1(t):
    x = cos(t) - 2 * cos(2 * t)
    y = sin(t) + 2 * sin(2 * t)
    z = sin(3 * t)
    return Vector([x, y, z])


def k2(t):
    x = 10 * (cos(t) + cos(3 * t)) + cos(2 * t) + cos(4 * t)
    y = 6 * sin(t) + 10 * sin(3 * t)
    z = 4 * sin(3 * t) * sin(5 * t / 2) + 4 * sin(4 * t) - 2 * sin(6 * t)
    return Vector([x, y, z]) * 0.2


def k3(t):
    x = 2.5 * cos(t + pi) / 3 + 2 * cos(3 * t)
    y = 2.5 * sin(t) / 3 + 2 * sin(3 * t)
    z = 1.5 * sin(4 * t) + sin(2 * t) / 3
    return Vector([x, y, z])


def make_verts(ures, vres, r2, knotfunc):
    verts = []
    for i in range(ures):
        t1 = (i + 0) * 2 * pi / ures
        t2 = (i + 1) * 2 * pi / ures
        a = knotfunc(t1)        # curr point
        b = knotfunc(t2)        # next point
        a, b = map(Vector, (a, b))
        e = a - b
        f = a + b
        g = e.cross(f)
        h = e.cross(g)
        g.normalize()
        h.normalize()
        for j in range(vres):
            k = j * 2 * pi / vres
            l = (cos(k), 0.0, sin(k))
            l = Vector(l)
            m = l * r2
            x, y, z = m
            n = h * x
            o = g * z
            p = n + o
            q = a + p
            verts.append(q)
    return verts


def make_faces(ures, vres):
    faces = []
    for u in range(0, ures):
        for v in range(0, vres):
            p1 = v + u * vres
            p2 = v + ((u + 1) % ures) * vres
            p4 = (v + 1) % vres + u * vres
            p3 = (v + 1) % vres + ((u + 1) % ures) * vres
            faces.append([p4, p3, p2, p1])
    return faces


def make_knot(knotidx, ures):
    knots = [k1, k2, k3]
    knotfunc = knots[knotidx - 1]
    vres = ures // 10
    r2 = 0.5
    verts = make_verts(ures, vres, r2, knotfunc)
    faces = make_faces(ures, vres)
    return (verts, faces)


class AddTorusKnot(bpy.types.Operator, object_utils.AddObjectHelper):
    bl_idname = "mesh.primitive_torusknot_add"
    bl_label = "Add Torus Knot"
    bl_description = "Construct a torus knot mesh"
    bl_options = {"REGISTER", "UNDO"}

    TorusKnot : BoolProperty(name = "TorusKnot",
                default = True,
                description = "TorusKnot")
    change : BoolProperty(name = "Change",
                default = False,
                description = "change TorusKnot")

    resolution: IntProperty(
        name="Resolution",
        description="Resolution of the Torus Knot",
        default=80,
        min=30, max=256
        )
    objecttype: IntProperty(
        name="Knot Type",
        description="Type of Knot",
        default=1,
        min=1, max=3
        )

    def draw(self, context):
        layout = self.layout

        layout.prop(self, 'resolution', expand=True)
        layout.prop(self, 'objecttype', expand=True)

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
                (context.active_object.data is not None) and ('TorusKnot' in context.active_object.data.keys()) and \
                (self.change == True):
                obj = context.active_object
                oldmesh = obj.data
                oldmeshname = obj.data.name
                verts, faces = make_knot(self.objecttype, self.resolution)
                mesh = bpy.data.meshes.new('TorusKnot')
                mesh.from_pydata(verts, [], faces)
                obj.data = mesh
                for material in oldmesh.materials:
                    obj.data.materials.append(material)
                bpy.data.meshes.remove(oldmesh)
                obj.data.name = oldmeshname
            else:
                verts, faces = make_knot(self.objecttype, self.resolution)
                mesh = bpy.data.meshes.new('TorusKnot')
                mesh.from_pydata(verts, [], faces)
                obj = object_utils.object_data_add(context, mesh, operator=self)

            obj.data["TorusKnot"] = True
            obj.data["change"] = False
            for prm in TorusKnotParameters():
                obj.data[prm] = getattr(self, prm)

        if bpy.context.mode == "EDIT_MESH":
            active_object = context.active_object
            name_active_object = active_object.name
            bpy.ops.object.mode_set(mode='OBJECT')
            verts, faces = make_knot(self.objecttype, self.resolution)
            mesh = bpy.data.meshes.new('TorusKnot')
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

def TorusKnotParameters():
    TorusKnotParameters = [
        "resolution",
        "objecttype",
        ]
    return TorusKnotParameters

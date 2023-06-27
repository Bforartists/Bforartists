# SPDX-FileCopyrightText: 2019-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

bl_info = {
    "name": "Edit Mesh Tools",
    "author": "Meta-Androcto",
    "version": (0, 3, 6),
    "blender": (2, 80, 0),
    "location": "View3D > Sidebar > Edit Tab / Edit Mode Context Menu",
    "warning": "",
    "description": "Mesh modelling toolkit. Several tools to aid modelling",
    "doc_url": "{BLENDER_MANUAL_URL}/addons/mesh/edit_mesh_tools.html",
    "category": "Mesh",
}

# Import From Files
if "bpy" in locals():
    import importlib
    importlib.reload(mesh_offset_edges)
    importlib.reload(split_solidify)
    importlib.reload(mesh_filletplus)
    importlib.reload(mesh_vertex_chamfer)
    importlib.reload(random_vertices)
#    importlib.reload(mesh_extrude_and_reshape)
    importlib.reload(mesh_edge_roundifier)
    importlib.reload(mesh_edgetools)
    importlib.reload(mesh_edges_floor_plan)
    importlib.reload(mesh_edges_length)
    importlib.reload(pkhg_faces)
    importlib.reload(mesh_cut_faces)
    importlib.reload(mesh_relax)

else:
    from . import mesh_offset_edges
    from . import split_solidify
    from . import mesh_filletplus
    from . import mesh_vertex_chamfer
    from . import random_vertices
#    from . import mesh_extrude_and_reshape
    from . import mesh_edge_roundifier
    from . import mesh_edgetools
    from . import mesh_edges_floor_plan
    from . import mesh_edges_length
    from . import pkhg_faces
    from . import mesh_cut_faces
    from . import mesh_relax


import bmesh
import bpy
import collections
import mathutils
import random
from math import (
        sin, cos, tan,
        degrees, radians, pi,
        )
from random import gauss
from mathutils import Matrix, Euler, Vector
from bpy_extras import view3d_utils
from bpy.types import (
        Operator,
        Menu,
        Panel,
        PropertyGroup,
        AddonPreferences,
        )
from bpy.props import (
        BoolProperty,
        BoolVectorProperty,
        EnumProperty,
        FloatProperty,
        FloatVectorProperty,
        IntVectorProperty,
        PointerProperty,
        StringProperty,
        IntProperty
        )

# ########################################
# ##### General functions ################
# ########################################


# Multi extrude
def gloc(self, r):
    return Vector((self.offx, self.offy, self.offz))


def vloc(self, r):
    random.seed(self.ran + r)
    return self.off * (1 + gauss(0, self.var1 / 3))


def nrot(self, n):
    return Euler((radians(self.nrotx) * n[0],
                  radians(self.nroty) * n[1],
                  radians(self.nrotz) * n[2]), 'XYZ')


def vrot(self, r):
    random.seed(self.ran + r)
    return Euler((radians(self.rotx) + gauss(0, self.var2 / 3),
                  radians(self.roty) + gauss(0, self.var2 / 3),
                  radians(self.rotz) + gauss(0, self.var2 / 3)), 'XYZ')


def vsca(self, r):
    random.seed(self.ran + r)
    return self.sca * (1 + gauss(0, self.var3 / 3))


class ME_OT_MExtrude(Operator):
    bl_idname = "object.mextrude"
    bl_label = "Multi Extrude"
    bl_description = ("Extrude selected Faces with Rotation,\n"
                      "Scaling, Variation, Randomization")
    bl_options = {"REGISTER", "UNDO", "PRESET"}

    off : FloatProperty(
            name="Offset",
            soft_min=0.001, soft_max=10,
            min=-100, max=100,
            default=1.0,
            description="Translation"
            )
    offx : FloatProperty(
            name="Loc X",
            soft_min=-10.0, soft_max=10.0,
            min=-100.0, max=100.0,
            default=0.0,
            description="Global Translation X"
            )
    offy : FloatProperty(
            name="Loc Y",
            soft_min=-10.0, soft_max=10.0,
            min=-100.0, max=100.0,
            default=0.0,
            description="Global Translation Y"
            )
    offz : FloatProperty(
            name="Loc Z",
            soft_min=-10.0, soft_max=10.0,
            min=-100.0, max=100.0,
            default=0.0,
            description="Global Translation Z"
            )
    rotx : FloatProperty(
            name="Rot X",
            min=-85, max=85,
            soft_min=-30, soft_max=30,
            default=0,
            description="X Rotation"
            )
    roty : FloatProperty(
            name="Rot Y",
            min=-85, max=85,
            soft_min=-30,
            soft_max=30,
            default=0,
            description="Y Rotation"
            )
    rotz : FloatProperty(
            name="Rot Z",
            min=-85, max=85,
            soft_min=-30, soft_max=30,
            default=-0,
            description="Z Rotation"
            )
    nrotx : FloatProperty(
            name="N Rot X",
            min=-85, max=85,
            soft_min=-30, soft_max=30,
            default=0,
            description="Normal X Rotation"
            )
    nroty : FloatProperty(
            name="N Rot Y",
            min=-85, max=85,
            soft_min=-30, soft_max=30,
            default=0,
            description="Normal Y Rotation"
            )
    nrotz : FloatProperty(
            name="N Rot Z",
            min=-85, max=85,
            soft_min=-30, soft_max=30,
            default=-0,
            description="Normal Z Rotation"
            )
    sca : FloatProperty(
            name="Scale",
            min=0.01, max=10,
            soft_min=0.5, soft_max=1.5,
            default=1.0,
            description="Scaling of the selected faces after extrusion"
            )
    var1 : FloatProperty(
            name="Offset Var", min=-10, max=10,
            soft_min=-1, soft_max=1,
            default=0,
            description="Offset variation"
            )
    var2 : FloatProperty(
            name="Rotation Var",
            min=-10, max=10,
            soft_min=-1, soft_max=1,
            default=0,
            description="Rotation variation"
            )
    var3 : FloatProperty(
            name="Scale Noise",
            min=-10, max=10,
            soft_min=-1, soft_max=1,
            default=0,
            description="Scaling noise"
            )
    var4 : IntProperty(
            name="Probability",
            min=0, max=100,
            default=100,
            description="Probability, chance of extruding a face"
            )
    num : IntProperty(
            name="Repeat",
            min=1, max=500,
            soft_max=100,
            default=1,
            description="Repetitions"
            )
    ran : IntProperty(
            name="Seed",
            min=-9999, max=9999,
            default=0,
            description="Seed to feed random values"
            )
    opt1 : BoolProperty(
            name="Polygon coordinates",
            default=True,
            description="Polygon coordinates, Object coordinates"
            )
    opt2 : BoolProperty(
            name="Proportional offset",
            default=False,
            description="Scale * Offset"
            )
    opt3 : BoolProperty(
            name="Per step rotation noise",
            default=False,
            description="Per step rotation noise, Initial rotation noise"
            )
    opt4 : BoolProperty(
            name="Per step scale noise",
            default=False,
            description="Per step scale noise, Initial scale noise"
            )

    @classmethod
    def poll(cls, context):
        obj = context.object
        return (obj and obj.type == 'MESH')

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)
        col.label(text="Transformations:")
        col.prop(self, "off", slider=True)
        col.prop(self, "offx", slider=True)
        col.prop(self, "offy", slider=True)
        col.prop(self, "offz", slider=True)

        col = layout.column(align=True)
        col.prop(self, "rotx", slider=True)
        col.prop(self, "roty", slider=True)
        col.prop(self, "rotz", slider=True)
        col.prop(self, "nrotx", slider=True)
        col.prop(self, "nroty", slider=True)
        col.prop(self, "nrotz", slider=True)
        col = layout.column(align=True)
        col.prop(self, "sca", slider=True)

        col = layout.column(align=True)
        col.label(text="Variation settings:")
        col.prop(self, "var1", slider=True)
        col.prop(self, "var2", slider=True)
        col.prop(self, "var3", slider=True)
        col.prop(self, "var4", slider=True)
        col.prop(self, "ran")
        col = layout.column(align=False)
        col.prop(self, 'num')

        col = layout.column(align=True)
        col.label(text="Options:")
        col.prop(self, "opt1")
        col.prop(self, "opt2")
        col.prop(self, "opt3")
        col.prop(self, "opt4")

    def execute(self, context):
        obj = bpy.context.object
        om = obj.mode
        bpy.context.tool_settings.mesh_select_mode = [False, False, True]
        origin = Vector([0.0, 0.0, 0.0])

        # bmesh operations
        bpy.ops.object.mode_set()
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        sel = [f for f in bm.faces if f.select]

        after = []

        # faces loop
        for i, of in enumerate(sel):
            nro = nrot(self, of.normal)
            off = vloc(self, i)
            loc = gloc(self, i)
            of.normal_update()

            # initial rotation noise
            if self.opt3 is False:
                rot = vrot(self, i)
            # initial scale noise
            if self.opt4 is False:
                s = vsca(self, i)

            # extrusion loop
            for r in range(self.num):
                # random probability % for extrusions
                if self.var4 > int(random.random() * 100):
                    nf = of.copy()
                    nf.normal_update()
                    no = nf.normal.copy()

                    # face/obj coordinates
                    if self.opt1 is True:
                        ce = nf.calc_center_bounds()
                    else:
                        ce = origin

                    # per step rotation noise
                    if self.opt3 is True:
                        rot = vrot(self, i + r)
                    # per step scale noise
                    if self.opt4 is True:
                        s = vsca(self, i + r)

                    # proportional, scale * offset
                    if self.opt2 is True:
                        off = s * off

                    for v in nf.verts:
                        v.co -= ce
                        v.co.rotate(nro)
                        v.co.rotate(rot)
                        v.co += ce + loc + no * off
                        v.co = v.co.lerp(ce, 1 - s)

                    # extrude code from TrumanBlending
                    for a, b in zip(of.loops, nf.loops):
                        sf = bm.faces.new((a.vert, a.link_loop_next.vert,
                                           b.link_loop_next.vert, b.vert))
                        sf.normal_update()
                    bm.faces.remove(of)
                    of = nf

            after.append(of)

        for v in bm.verts:
            v.select = False
        for e in bm.edges:
            e.select = False

        for f in after:
            if f not in sel:
                f.select = True
            else:
                f.select = False

        bm.to_mesh(obj.data)
        obj.data.update()

        # restore user settings
        bpy.ops.object.mode_set(mode=om)

        if not len(sel):
            self.report({"WARNING"},
                        "No suitable Face selection found. Operation cancelled")
            return {'CANCELLED'}

        return {'FINISHED'}

# Face inset fillet
def edit_mode_out():
    bpy.ops.object.mode_set(mode='OBJECT')


def edit_mode_in():
    bpy.ops.object.mode_set(mode='EDIT')


def angle_rotation(rp, q, axis, angle):
    # returns the vector made by the rotation of the vector q
    # rp by angle around axis and then adds rp

    return (Matrix.Rotation(angle, 3, axis) @ (q - rp)) + rp


def face_inset_fillet(bme, face_index_list, inset_amount, distance,
                      number_of_sides, out, radius, type_enum, kp):
    list_del = []

    for faceindex in face_index_list:

        bme.faces.ensure_lookup_table()
        # loops through the faces...
        f = bme.faces[faceindex]
        f.select_set(False)
        list_del.append(f)
        f.normal_update()
        vertex_index_list = [v.index for v in f.verts]
        dict_0 = {}
        orientation_vertex_list = []
        n = len(vertex_index_list)
        for i in range(n):
            # loops through the vertices
            dict_0[i] = []
            bme.verts.ensure_lookup_table()
            p = (bme.verts[vertex_index_list[i]].co).copy()
            p1 = (bme.verts[vertex_index_list[(i - 1) % n]].co).copy()
            p2 = (bme.verts[vertex_index_list[(i + 1) % n]].co).copy()
            # copies some vert coordinates, always the 3 around i
            dict_0[i].append(bme.verts[vertex_index_list[i]])
            # appends the bmesh vert of the appropriate index to the dict
            vec1 = p - p1
            vec2 = p - p2
            # vectors for the other corner points to the cornerpoint
            # corresponding to i / p
            angle = vec1.angle(vec2)

            adj = inset_amount / tan(angle * 0.5)
            h = (adj ** 2 + inset_amount ** 2) ** 0.5
            if round(degrees(angle)) == 180 or round(degrees(angle)) == 0.0:
                # if the corner is a straight line...
                # I think this creates some new points...
                if out is True:
                    val = ((f.normal).normalized() * inset_amount)
                else:
                    val = -((f.normal).normalized() * inset_amount)
                p6 = angle_rotation(p, p + val, vec1, radians(90))
            else:
                # if the corner is an actual corner
                val = ((f.normal).normalized() * h)
                if out is True:
                    # this -(p - (vec2.normalized() * adj))) is just the freaking axis afaik...
                    p6 = angle_rotation(
                                p, p + val,
                                -(p - (vec2.normalized() * adj)),
                                -radians(90)
                                )
                else:
                    p6 = angle_rotation(
                                p, p - val,
                                ((p - (vec1.normalized() * adj)) - (p - (vec2.normalized() * adj))),
                                -radians(90)
                                )

                orientation_vertex_list.append(p6)

        new_inner_face = []
        orientation_vertex_list_length = len(orientation_vertex_list)
        ovll = orientation_vertex_list_length

        for j in range(ovll):
            q = orientation_vertex_list[j]
            q1 = orientation_vertex_list[(j - 1) % ovll]
            q2 = orientation_vertex_list[(j + 1) % ovll]
            # again, these are just vectors between somewhat displaced corner vertices
            vec1_ = q - q1
            vec2_ = q - q2
            ang_ = vec1_.angle(vec2_)

            # the angle between them
            if round(degrees(ang_)) == 180 or round(degrees(ang_)) == 0.0:
                # again... if it's really a line...
                v = bme.verts.new(q)
                new_inner_face.append(v)
                dict_0[j].append(v)
            else:
                # s.a.
                if radius is False:
                    h_ = distance * (1 / cos(ang_ * 0.5))
                    d = distance
                elif radius is True:
                    h_ = distance / sin(ang_ * 0.5)
                    d = distance / tan(ang_ * 0.5)
                # max(d) is vec1_.magnitude * 0.5
                # or vec2_.magnitude * 0.5 respectively

                # only functional difference v
                if d > vec1_.magnitude * 0.5:
                    d = vec1_.magnitude * 0.5

                if d > vec2_.magnitude * 0.5:
                    d = vec2_.magnitude * 0.5
                # only functional difference ^

                q3 = q - (vec1_.normalized() * d)
                q4 = q - (vec2_.normalized() * d)
                # these are new verts somewhat offset from the corners
                rp_ = q - ((q - ((q3 + q4) * 0.5)).normalized() * h_)
                # reference point inside the curvature
                axis_ = vec1_.cross(vec2_)
                # this should really be just the face normal
                vec3_ = rp_ - q3
                vec4_ = rp_ - q4
                rot_ang = vec3_.angle(vec4_)
                cornerverts = []

                for o in range(number_of_sides + 1):
                    # this calculates the actual new vertices
                    q5 = angle_rotation(rp_, q4, axis_, rot_ang * o / number_of_sides)
                    v = bme.verts.new(q5)

                    # creates new bmesh vertices from it
                    bme.verts.index_update()

                    dict_0[j].append(v)
                    cornerverts.append(v)

                cornerverts.reverse()
                new_inner_face.extend(cornerverts)

        if out is False:
            f = bme.faces.new(new_inner_face)
            f.select_set(True)
        elif out is True and kp is True:
            f = bme.faces.new(new_inner_face)
            f.select_set(True)

        n2_ = len(dict_0)
        # these are the new side faces, those that don't depend on cornertype
        for o in range(n2_):
            list_a = dict_0[o]
            list_b = dict_0[(o + 1) % n2_]
            bme.faces.new([list_a[0], list_b[0], list_b[-1], list_a[1]])
            bme.faces.index_update()
        # cornertype 1 - ngon faces
        if type_enum == 'opt0':
            for k in dict_0:
                if len(dict_0[k]) > 2:
                    bme.faces.new(dict_0[k])
                    bme.faces.index_update()
        # cornertype 2 - triangulated faces
        if type_enum == 'opt1':
            for k_ in dict_0:
                q_ = dict_0[k_][0]
                dict_0[k_].pop(0)
                n3_ = len(dict_0[k_])
                for kk in range(n3_ - 1):
                    bme.faces.new([dict_0[k_][kk], dict_0[k_][(kk + 1) % n3_], q_])
                    bme.faces.index_update()

    del_ = [bme.faces.remove(f) for f in list_del]

    if del_:
        del del_


# Operator

class MESH_OT_face_inset_fillet(Operator):
    bl_idname = "mesh.face_inset_fillet"
    bl_label = "Face Inset Fillet"
    bl_description = ("Inset selected and Fillet (make round) the corners \n"
                     "of the newly created Faces")
    bl_options = {"REGISTER", "UNDO"}

    # inset amount
    inset_amount : bpy.props.FloatProperty(
            name="Inset amount",
            description="Define the size of the Inset relative to the selection",
            default=0.04,
            min=0, max=100.0,
            step=1,
            precision=3
            )
    # number of sides
    number_of_sides : bpy.props.IntProperty(
            name="Number of sides",
            description="Define the roundness of the corners by specifying\n"
                        "the subdivision count",
            default=4,
            min=1, max=100,
            step=1
            )
    distance : bpy.props.FloatProperty(
            name="",
            description="Use distance or radius for corners' size calculation",
            default=0.04,
            min=0.00001, max=100.0,
            step=1,
            precision=3
            )
    out : bpy.props.BoolProperty(
            name="Outside",
            description="Inset the Faces outwards in relation to the selection\n"
                        "Note: depending on the geometry, can give unsatisfactory results",
            default=False
            )
    radius : bpy.props.BoolProperty(
            name="Radius",
            description="Use radius for corners' size calculation",
            default=False
            )
    type_enum : bpy.props.EnumProperty(
            items=[('opt0', "N-gon", "N-gon corners - Keep the corner Faces uncut"),
                   ('opt1', "Triangle", "Triangulate corners")],
            name="Corner Type",
            default="opt0"
            )
    kp : bpy.props.BoolProperty(
            name="Keep faces",
            description="Do not delete the inside Faces\n"
                        "Only available if the Out option is checked",
            default=False
            )

    def draw(self, context):
        layout = self.layout

        layout.label(text="Corner Type:")

        row = layout.row()
        row.prop(self, "type_enum", text="")

        row = layout.row(align=True)
        row.prop(self, "out")

        if self.out is True:
            row.prop(self, "kp")

        row = layout.row()
        row.prop(self, "inset_amount")

        row = layout.row()
        row.prop(self, "number_of_sides")

        row = layout.row()
        row.prop(self, "radius")

        row = layout.row()
        dist_rad = "Radius" if self.radius else "Distance"
        row.prop(self, "distance", text=dist_rad)

    def execute(self, context):
        # this really just prepares everything for the main function
        inset_amount = self.inset_amount
        number_of_sides = self.number_of_sides
        distance = self.distance
        out = self.out
        radius = self.radius
        type_enum = self.type_enum
        kp = self.kp

        edit_mode_out()
        ob_act = context.active_object
        bme = bmesh.new()
        bme.from_mesh(ob_act.data)
        # this
        face_index_list = [f.index for f in bme.faces if f.select and f.is_valid]

        if len(face_index_list) == 0:
            self.report({'WARNING'},
                        "No suitable Face selection found. Operation cancelled")
            edit_mode_in()

            return {'CANCELLED'}

        elif len(face_index_list) != 0:
            face_inset_fillet(bme, face_index_list,
                              inset_amount, distance, number_of_sides,
                              out, radius, type_enum, kp)

        bme.to_mesh(ob_act.data)
        edit_mode_in()

        return {'FINISHED'}

# ********** Edit Multiselect **********
class VIEW3D_MT_Edit_MultiMET(Menu):
    bl_label = "Multi Select"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'

        layout.operator("multiedit.allselect", text="All Select Modes", icon='RESTRICT_SELECT_OFF')


# Select Tools
class VIEW3D_MT_Select_Vert(Menu):
    bl_label = "Select Vert"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'

        layout.operator("multiedit.vertexselect", text="Vertex Select Mode", icon='VERTEXSEL')
        layout.operator("multiedit.vertedgeselect", text="Vert & Edge Select", icon='EDGESEL')
        layout.operator("multiedit.vertfaceselect", text="Vert & Face Select", icon='FACESEL')


class VIEW3D_MT_Select_Edge(Menu):
    bl_label = "Select Edge"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'

        layout.operator("multiedit.edgeselect", text="Edge Select Mode", icon='EDGESEL')
        layout.operator("multiedit.vertedgeselect", text="Edge & Vert Select", icon='VERTEXSEL')
        layout.operator("multiedit.edgefaceselect", text="Edge & Face Select", icon='FACESEL')


class VIEW3D_MT_Select_Face(Menu):
    bl_label = "Select Face"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'

        layout.operator("multiedit.faceselect", text="Face Select Mode", icon='FACESEL')
        layout.operator("multiedit.vertfaceselect", text="Face & Vert Select", icon='VERTEXSEL')
        layout.operator("multiedit.edgefaceselect", text="Face & Edge Select", icon='EDGESEL')


 # multiple edit select modes.
class VIEW3D_OT_multieditvertex(Operator):
    bl_idname = "multiedit.vertexselect"
    bl_label = "Vertex Mode"
    bl_description = "Vert Select Mode On"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if context.object.mode != "EDIT":
            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
        if bpy.ops.mesh.select_mode != "EDGE, FACE":
            bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
            return {'FINISHED'}


class VIEW3D_OT_multieditedge(Operator):
    bl_idname = "multiedit.edgeselect"
    bl_label = "Edge Mode"
    bl_description = "Edge Select Mode On"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if context.object.mode != "EDIT":
            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='EDGE')
        if bpy.ops.mesh.select_mode != "VERT, FACE":
            bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='EDGE')
            return {'FINISHED'}


class VIEW3D_OT_multieditface(Operator):
    bl_idname = "multiedit.faceselect"
    bl_label = "Multiedit Face"
    bl_description = "Face Select Mode On"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if context.object.mode != "EDIT":
            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')
        if bpy.ops.mesh.select_mode != "VERT, EDGE":
            bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')
            return {'FINISHED'}

class VIEW3D_OT_multieditvertedge(Operator):
    bl_idname = "multiedit.vertedgeselect"
    bl_label = "Multiedit Face"
    bl_description = "Vert & Edge Select Modes On"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if context.object.mode != "EDIT":
            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
        if bpy.ops.mesh.select_mode != "VERT, EDGE, FACE":
            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
            bpy.ops.mesh.select_mode(use_extend=True, use_expand=False, type='EDGE')
            return {'FINISHED'}

class VIEW3D_OT_multieditvertface(Operator):
    bl_idname = "multiedit.vertfaceselect"
    bl_label = "Multiedit Face"
    bl_description = "Vert & Face Select Modes On"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if context.object.mode != "EDIT":
            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
        if bpy.ops.mesh.select_mode != "VERT, EDGE, FACE":
            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
            bpy.ops.mesh.select_mode(use_extend=True, use_expand=False, type='FACE')
            return {'FINISHED'}


class VIEW3D_OT_multieditedgeface(Operator):
    bl_idname = "multiedit.edgefaceselect"
    bl_label = "Mode Face Edge"
    bl_description = "Edge & Face Select Modes On"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if context.object.mode != "EDIT":
            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='EDGE')
        if bpy.ops.mesh.select_mode != "VERT, EDGE, FACE":
            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='EDGE')
            bpy.ops.mesh.select_mode(use_extend=True, use_expand=False, type='FACE')
            return {'FINISHED'}


class VIEW3D_OT_multieditall(Operator):
    bl_idname = "multiedit.allselect"
    bl_label = "All Edit Select Modes"
    bl_description = "Vert & Edge & Face Select Modes On"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if context.object.mode != "EDIT":
            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
        if bpy.ops.mesh.select_mode != "VERT, EDGE, FACE":
            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='VERT')
            bpy.ops.mesh.select_mode(use_extend=True, use_expand=False, type='EDGE')
            bpy.ops.mesh.select_mode(use_extend=True, use_expand=False, type='FACE')
            return {'FINISHED'}


# ########################################
# ##### GUI and registration #############
# ########################################

# menu containing all tools
class VIEW3D_MT_edit_mesh_tools(Menu):
    bl_label = "Mesh Tools"

    def draw(self, context):
        layout = self.layout
        layout.operator("mesh.remove_doubles")
        layout.operator("mesh.dissolve_limited")
        layout.operator("mesh.flip_normals")
        props = layout.operator("mesh.quads_convert_to_tris")
        props.quad_method = props.ngon_method = 'BEAUTY'
        layout.operator("mesh.tris_convert_to_quads")
        layout.operator('mesh.vertex_chamfer', text="Vertex Chamfer")
        layout.operator("mesh.bevel", text="Bevel Vertices").affect = 'VERTICES'
        layout.operator('mesh.offset_edges', text="Offset Edges")
        layout.operator('mesh.fillet_plus', text="Fillet Edges")
        layout.operator("mesh.face_inset_fillet",
                            text="Face Inset Fillet")
#        layout.operator("mesh.extrude_reshape",
#                        text="Push/Pull Faces")
        layout.operator("object.mextrude",
                        text="Multi Extrude")
        layout.operator('mesh.split_solidify', text="Split Solidify")



# panel containing all tools
class VIEW3D_PT_edit_mesh_tools(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Edit'
    bl_context = "mesh_edit"
    bl_label = "Mesh Tools"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)
        et = context.window_manager.edittools

        # vert - first line
        split = col.split(factor=0.80, align=True)
        if et.display_vert:
            split.prop(et, "display_vert", text="Vert Tools", icon='DOWNARROW_HLT')
        else:
            split.prop(et, "display_vert", text="Vert tools", icon='RIGHTARROW')
        split.menu("VIEW3D_MT_Select_Vert", text="", icon='VERTEXSEL')
        # vert - settings
        if et.display_vert:
            box = col.column(align=True).box().column()
            col_top = box.column(align=True)
            row = col_top.row(align=True)
            row.operator('mesh.vertex_chamfer', text="Vertex Chamfer")
            row = col_top.row(align=True)
            row.operator("mesh.extrude_vertices_move", text="Extrude Vertices")
            row = col_top.row(align=True)
            row.operator("mesh.random_vertices", text="Random Vertices")
            row = col_top.row(align=True)
            row.operator("mesh.bevel", text="Bevel Vertices").affect = 'VERTICES'

        # edge - first line
        split = col.split(factor=0.80, align=True)
        if et.display_edge:
            split.prop(et, "display_edge", text="Edge Tools", icon='DOWNARROW_HLT')
        else:
            split.prop(et, "display_edge", text="Edge Tools", icon='RIGHTARROW')
        split.menu("VIEW3D_MT_Select_Edge", text="", icon='EDGESEL')
        # Edge - settings
        if et.display_edge:
            box = col.column(align=True).box().column()
            col_top = box.column(align=True)
            row = col_top.row(align=True)
            row.operator('mesh.offset_edges', text="Offset Edges")
            row = col_top.row(align=True)
            row.operator('mesh.fillet_plus', text="Fillet Edges")
            row = col_top.row(align=True)
            row.operator('mesh.edge_roundifier', text="Edge Roundify")
            row = col_top.row(align=True)
            row.operator('object.mesh_edge_length_set', text="Set Edge Length")
            row = col_top.row(align=True)
            row.operator('mesh.edges_floor_plan', text="Edges Floor Plan")
            row = col_top.row(align=True)
            row.operator("mesh.extrude_edges_move", text="Extrude Edges")
            row = col_top.row(align=True)
            row.operator("mesh.bevel", text="Bevel Edges").affect = 'EDGES'

        # face - first line
        split = col.split(factor=0.80, align=True)
        if et.display_face:
            split.prop(et, "display_face", text="Face Tools", icon='DOWNARROW_HLT')
        else:
            split.prop(et, "display_face", text="Face Tools", icon='RIGHTARROW')
        split.menu("VIEW3D_MT_Select_Face", text="", icon='FACESEL')
        # face - settings
        if et.display_face:
            box = col.column(align=True).box().column()
            col_top = box.column(align=True)
            row = col_top.row(align=True)
            row.operator("mesh.face_inset_fillet",
                            text="Face Inset Fillet")
            row = col_top.row(align=True)
            row.operator("mesh.ext_cut_faces",
                            text="Cut Faces")
            row = col_top.row(align=True)
#            row.operator("mesh.extrude_reshape",
#                            text="Push/Pull Faces")
            row = col_top.row(align=True)
            row.operator("object.mextrude",
                            text="Multi Extrude")
            row = col_top.row(align=True)
            row.operator('mesh.split_solidify', text="Split Solidify")
            row = col_top.row(align=True)
            row.operator('mesh.add_faces_to_object', text="Face Shape")
            row = col_top.row(align=True)
            row.operator("mesh.inset")
            row = col_top.row(align=True)
            row.operator("mesh.extrude_faces_move", text="Extrude Individual Faces")

        # util - first line
        split = col.split(factor=0.80, align=True)
        if et.display_util:
            split.prop(et, "display_util", text="Utility Tools", icon='DOWNARROW_HLT')
        else:
            split.prop(et, "display_util", text="Utility Tools", icon='RIGHTARROW')
        split.menu("VIEW3D_MT_Edit_MultiMET", text="", icon='RESTRICT_SELECT_OFF')
        # util - settings
        if et.display_util:
            box = col.column(align=True).box().column()
            col_top = box.column(align=True)
            row = col_top.row(align=True)
            row.operator("mesh.subdivide")
            row = col_top.row(align=True)
            row.operator("mesh.remove_doubles")
            row = col_top.row(align=True)
            row.operator("mesh.dissolve_limited")
            row = col_top.row(align=True)
            row.operator("mesh.flip_normals")
            row = col_top.row(align=True)
            props = row.operator("mesh.quads_convert_to_tris")
            props.quad_method = props.ngon_method = 'BEAUTY'
            row = col_top.row(align=True)
            row.operator("mesh.tris_convert_to_quads")
            row = col_top.row(align=True)
            row.operator("mesh.relax")

# property group containing all properties for the gui in the panel
class EditToolsProps(PropertyGroup):
    """
    Fake module like class
    bpy.context.window_manager.edittools
    """
    # general display properties
    display_vert: BoolProperty(
        name="Bridge settings",
        description="Display settings of the Vert tool",
        default=False
        )
    display_edge: BoolProperty(
        name="Edge settings",
        description="Display settings of the Edge tool",
        default=False
        )
    display_face: BoolProperty(
        name="Face settings",
        description="Display settings of the Face tool",
        default=False
        )
    display_util: BoolProperty(
        name="Face settings",
        description="Display settings of the Face tool",
        default=False
        )

# draw function for integration in menus
def menu_func(self, context):
    self.layout.menu("VIEW3D_MT_edit_mesh_tools")
    self.layout.separator()

# Add-ons Preferences Update Panel

# Define Panel classes for updating
panels = (
        VIEW3D_PT_edit_mesh_tools,
        )


def update_panel(self, context):
    message = "LoopTools: Updating Panel locations has failed"
    try:
        for panel in panels:
            if "bl_rna" in panel.__dict__:
                bpy.utils.unregister_class(panel)

        for panel in panels:
            panel.bl_category = context.preferences.addons[__name__].preferences.category
            bpy.utils.register_class(panel)

    except Exception as e:
        print("\n[{}]\n{}\n\nError:\n{}".format(__name__, message, e))
        pass


class EditToolsPreferences(AddonPreferences):
    # this must match the addon name, use '__package__'
    # when defining this in a submodule of a python package.
    bl_idname = __name__

    category: StringProperty(
            name="Tab Category",
            description="Choose a name for the category of the panel",
            default="Edit",
            update=update_panel
            )

    def draw(self, context):
        layout = self.layout

        row = layout.row()
        col = row.column()
        col.label(text="Tab Category:")
        col.prop(self, "category", text="")


# define classes for registration
classes = (
    VIEW3D_MT_edit_mesh_tools,
    VIEW3D_PT_edit_mesh_tools,
    VIEW3D_MT_Edit_MultiMET,
    VIEW3D_MT_Select_Vert,
    VIEW3D_MT_Select_Edge,
    VIEW3D_MT_Select_Face,
    EditToolsProps,
    EditToolsPreferences,
    MESH_OT_face_inset_fillet,
    ME_OT_MExtrude,
    VIEW3D_OT_multieditvertex,
    VIEW3D_OT_multieditedge,
    VIEW3D_OT_multieditface,
    VIEW3D_OT_multieditvertedge,
    VIEW3D_OT_multieditvertface,
    VIEW3D_OT_multieditedgeface,
    VIEW3D_OT_multieditall
    )


# registering and menu integration
def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.VIEW3D_MT_edit_mesh_context_menu.prepend(menu_func)
    bpy.types.WindowManager.edittools = PointerProperty(type=EditToolsProps)
    update_panel(None, bpy.context)

    mesh_filletplus.register()
    mesh_offset_edges.register()
    split_solidify.register()
    mesh_vertex_chamfer.register()
    random_vertices.register()
#    mesh_extrude_and_reshape.register()
    mesh_edge_roundifier.register()
    mesh_edgetools.register()
    mesh_edges_floor_plan.register()
    mesh_edges_length.register()
    pkhg_faces.register()
    mesh_cut_faces.register()
    mesh_relax.register()


# unregistering and removing menus
def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    bpy.types.VIEW3D_MT_edit_mesh_context_menu.remove(menu_func)
    try:
        del bpy.types.WindowManager.edittools
    except Exception as e:
        print('unregister fail:\n', e)
        pass

    mesh_filletplus.unregister()
    mesh_offset_edges.unregister()
    split_solidify.unregister()
    mesh_vertex_chamfer.unregister()
    random_vertices.unregister()
#    mesh_extrude_and_reshape.unregister()
    mesh_edge_roundifier.unregister()
    mesh_edgetools.unregister()
    mesh_edges_floor_plan.unregister()
    mesh_edges_length.unregister()
    pkhg_faces.unregister()
    mesh_cut_faces.unregister()
    mesh_relax.unregister()


if __name__ == "__main__":
    register()

# SPDX-FileCopyrightText: 2016-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later


import math

import bpy
import bmesh
import mathutils
from mathutils import geometry
from mathutils import Vector


def generate_bmesh_repr(p1, v1, axis, num_verts):
    '''
        p1:     center of circle (local coordinates)
        v1:     first vertex of circle in (local coordinates)
        axis:   orientation matrix
        origin: obj.location
    '''
    props = bpy.context.scene.tinycad_props
    rescale = props.rescale

    # generate geometry up front
    chain = []
    gamma = 2 * math.pi / num_verts
    for i in range(num_verts + 1):
        theta = gamma * i
        mat_rot = mathutils.Matrix.Rotation(theta, 4, axis)
        local_point = (mat_rot @ ((v1 - p1) * rescale))
        chain.append(local_point + p1)

    obj = bpy.context.edit_object
    me = obj.data
    bm = bmesh.from_edit_mesh(me)

    # add verts
    v_refs = []
    for p in chain:
        v = bm.verts.new(p)
        v.select = False  # this might be a default.. redundant?
        v_refs.append(v)

    # join verts, daisy chain
    num_verts = len(v_refs)
    for i in range(num_verts):
        idx1 = i
        idx2 = (i + 1) % num_verts
        bm.edges.new([v_refs[idx1], v_refs[idx2]])

    bmesh.update_edit_mesh(me, loop_triangles=True)


def generate_3PT(pts, obj, nv, mode=1):
    mw = obj.matrix_world
    V = Vector
    nv = max(3, nv)

    # construction
    v1, v2, v3, v4 = V(pts[0]), V(pts[1]), V(pts[1]), V(pts[2])
    edge1_mid = v1.lerp(v2, 0.5)
    edge2_mid = v3.lerp(v4, 0.5)
    axis = geometry.normal(v1, v2, v4)
    mat_rot = mathutils.Matrix.Rotation(math.radians(90.0), 4, axis)

    # triangle edges
    v1_ = ((v1 - edge1_mid) @ mat_rot) + edge1_mid
    v2_ = ((v2 - edge1_mid) @ mat_rot) + edge1_mid
    v3_ = ((v3 - edge2_mid) @ mat_rot) + edge2_mid
    v4_ = ((v4 - edge2_mid) @ mat_rot) + edge2_mid

    r = geometry.intersect_line_line(v1_, v2_, v3_, v4_)
    if r:
        p1, _ = r
        cp = mw @ p1
        bpy.context.scene.cursor.location = cp

        if mode == 0:
            pass

        elif mode == 1:
            generate_bmesh_repr(p1, v1, axis, nv)

    else:
        print('not on a circle')


def get_three_verts_from_selection(obj):
    me = obj.data
    bm = bmesh.from_edit_mesh(me)

    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()

    return [v.co[:] for v in bm.verts if v.select]


def dispatch(context, mode=0):
    try:
        obj = context.edit_object
        pts = get_three_verts_from_selection(obj)
        props = context.scene.tinycad_props
        generate_3PT(pts, obj, props.num_verts, mode)
    except:
        print('dispatch failed', mode)


class TCCallBackCCEN(bpy.types.Operator):
    bl_idname = 'tinycad.reset_circlescale'
    bl_label = 'CCEN circle reset'
    bl_options = {'REGISTER'}

    def execute(self, context):
        context.scene.tinycad_props.rescale = 1
        return {'FINISHED'}


class TCCircleCenter(bpy.types.Operator):
    '''Recreate a Circle from 3 selected verts, move 3dcursor to its center'''

    bl_idname = 'tinycad.circlecenter'
    bl_label = 'CCEN circle center from selected'
    bl_options = {'REGISTER', 'UNDO'}

    def draw(self, context):
        scn = context.scene
        l = self.layout
        col = l.column()

        col.prop(scn.tinycad_props, 'num_verts', text='num verts')
        row = col.row(align=True)
        row.prop(scn.tinycad_props, 'rescale', text='rescale')
        row.operator('tinycad.reset_circlescale', text="", icon="PIVOT_CURSOR")

    @classmethod
    def poll(cls, context):
        obj = context.edit_object
        return obj is not None and obj.type == 'MESH'

    def execute(self, context):
        dispatch(context, mode=1)
        return {'FINISHED'}

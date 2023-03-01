# gpl: author Nobuyuki Hirakata

import bpy

import bmesh
from random import (
        gauss,
        seed,
        )
from math import radians, pi
from mathutils import Euler


# Join fractures into an object
def make_join(cells):

    # Execute join
    bpy.context.view_layer.objects.active = cells[0]
    cells[0].select_set(state=True)
    bpy.ops.object.join()

    bpy.ops.object.origin_set(type='GEOMETRY_ORIGIN')

    joined = bpy.context.active_object

    suffix_index = joined.name.rfind("_cell")
    if suffix_index != -1:
        joined.name = joined.name[:suffix_index] + "_crack"

    return bpy.context.active_object


# Add modifier and setting
def add_modifiers(decimate_val=0.4, smooth_val=0.5):
    bpy.ops.object.modifier_add(type='DECIMATE')
    decimate = bpy.context.object.modifiers[-1]
    decimate.name = 'DECIMATE_crackit'
    decimate.ratio = decimate_val

    bpy.ops.object.modifier_add(type='SUBSURF')
    subsurf = bpy.context.object.modifiers[-1]
    subsurf.name = 'SUBSURF_crackit'

    bpy.ops.object.modifier_add(type='SMOOTH')
    smooth = bpy.context.object.modifiers[-1]
    smooth.name = 'SMOOTH_crackit'
    smooth.factor = smooth_val


# -------------- multi extrude --------------------
# var1=random offset, var2=random rotation, var3=random scale
def multiExtrude(off=0.1, rotx=0, roty=0, rotz=0, sca=0.0,
                var1=0.01, var2=0.01, var3=0.01, num=1, ran=0):

    obj = bpy.context.object
    bpy.context.tool_settings.mesh_select_mode = [False, False, True]

    # bmesh operations
    bpy.ops.object.mode_set()
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    sel = [f for f in bm.faces if f.select]

    # faces loop
    for i, of in enumerate(sel):
        rot = _vrot(r=i, ran=ran, rotx=rotx, var2=var2, roty=roty, rotz=rotz)
        off = _vloc(r=i, ran=ran, off=off, var1=var1)
        of.normal_update()

        # extrusion loop
        for r in range(num):
            nf = of.copy()
            nf.normal_update()
            no = nf.normal.copy()
            ce = nf.calc_center_bounds()
            s = _vsca(r=i + r, ran=ran, var3=var3, sca=sca)

            for v in nf.verts:
                v.co -= ce
                v.co.rotate(rot)
                v.co += ce + no * off
                v.co = v.co.lerp(ce, 1 - s)

            # extrude code from TrumanBlending
            for a, b in zip(of.loops, nf.loops):
                sf = bm.faces.new((a.vert, a.link_loop_next.vert,
                                   b.link_loop_next.vert, b.vert))
                sf.normal_update()

            bm.faces.remove(of)
            of = nf

    for v in bm.verts:
        v.select = False

    for e in bm.edges:
        e.select = False

    bm.to_mesh(obj.data)
    obj.data.update()


def _vloc(r, ran, off, var1):
    seed(ran + r)
    return off * (1 + gauss(0, var1 / 3))

def _vrot(r, ran, rotx, var2, roty, rotz):
    seed(ran + r)
    return Euler((radians(rotx) + gauss(0, var2 / 3),
                radians(roty) + gauss(0, var2 / 3),
                radians(rotz) + gauss(0, var2 / 3)), 'XYZ')

def _vsca(r, ran, sca, var3):
    seed(ran + r)
    return sca * (1 + gauss(0, var3 / 3))

# Centroid of a selection of vertices
'''
def _centro(ver):
    vvv = [v for v in ver if v.select]
    if not vvv or len(vvv) == len(ver):
        return ('error')

    x = sum([round(v.co[0], 4) for v in vvv]) / len(vvv)
    y = sum([round(v.co[1], 4) for v in vvv]) / len(vvv)
    z = sum([round(v.co[2], 4) for v in vvv]) / len(vvv)

    return (x, y, z)
'''

# Retrieve the original state of the object
'''
def _volver(obj, copia, om, msm, msv):
    for i in copia:
        obj.data.vertices[i].select = True
    bpy.context.tool_settings.mesh_select_mode = msm

    for i in range(len(msv)):
        obj.modifiers[i].show_viewport = msv[i]
'''

# ##### BEGIN GPL LICENSE BLOCK #####
#
#  SCA Tree Generator, a Blender addon
#  (c) 2013 Michel J. Anders (varkenvarken)
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
# ##### END GPL LICENSE BLOCK #####

# <pep8 compliant>

bl_info = {
    "name": "SCA Tree Generator",
    "author": "michel anders (varkenvarken)",
    "version": (0, 1, 2),
    "blender": (2, 66, 0),
    "location": "View3D > Add > Mesh",
    "description": "Adds a tree created with the space colonization algorithm starting at the 3D cursor",
    "warning": "",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/Scripts/Add_Mesh/Add_Space_Tree",
    "tracker_url": "",
    "category": "Add Mesh"}

from time import time
from random import random, gauss
from functools import partial
from math import sin, cos

import bpy
from bpy.props import FloatProperty, IntProperty, BoolProperty, EnumProperty
from mathutils import Vector, Euler, Matrix, Quaternion

from .simplefork import simplefork, simplefork2, quadfork, bridgequads  # simple skinning algorithm building blocks
from .sca import SCA, Branchpoint  # the core class that implements the space colonization algorithm and the definition of a segment
from .timer import Timer


def availableGroups(self, context):
    return [(name, name, name, n) for n, name in enumerate(bpy.data.groups.keys())]


def availableGroupsOrNone(self, context):
    groups = [('None', 'None', 'None', 1)]
    return groups + [(name, name, name, n + 1) for n, name in enumerate(bpy.data.groups.keys())]


def availableObjects(self, context):
    return [(name, name, name, n + 1) for n, name in enumerate(bpy.data.objects.keys())]


def ellipsoid(r=5, rz=5, p=Vector((0, 0, 8)), taper=0):
    r2 = r * r
    z2 = rz * rz
    if rz > r:
        r = rz
    while True:
        x = (random() * 2 - 1) * r
        y = (random() * 2 - 1) * r
        z = (random() * 2 - 1) * r
        f = (z + r) / (2 * r)
        f = 1 + f * taper if taper >= 0 else (1 - f) * -taper
        if f * x * x / r2 + f * y * y / r2 + z * z / z2 <= 1:
            yield p + Vector((x, y, z))


def pointInsideMesh(pointrelativetocursor, ob):
    # adapted from http://blenderartists.org/forum/showthread.php?195605-Detecting-if-a-point-is-inside-a-mesh-2-5-API&p=1691633&viewfull=1#post1691633
    mat = ob.matrix_world.inverted()
    orig = mat * (pointrelativetocursor + bpy.context.scene.cursor_location)
    count = 0
    axis = Vector((0, 0, 1))
    while True:
        location, normal, index = ob.ray_cast(orig, orig + axis * 10000.0)
        if index == -1:
            break
        count += 1
        orig = location + axis * 0.00001
    if count % 2 == 0:
        return False
    return True


def ellipsoid2(rxy=5, rz=5, p=Vector((0, 0, 8)), surfacebias=1, topbias=1):
    while True:
        phi = 6.283 * random()
        theta = 3.1415 * (random() - 0.5)
        r = random() ** (surfacebias / 2)
        x = r * rxy * cos(theta) * cos(phi)
        y = r * rxy * cos(theta) * sin(phi)
        st = sin(theta)
        st = (((st + 1) / 2) ** topbias) * 2 - 1
        z = r * rz * st
        #print(">>>%.2f %.2f %.2f "%(x,y,z))
        m = p + Vector((x, y, z))
        reject = False
        for ob in bpy.context.selected_objects:
            # probably we should check if each object is a mesh
            if pointInsideMesh(m, ob):
                reject = True
                break
        if not reject:
            yield m


def halton3D(index):
    """
    return a quasi random 3D vector R3 in [0,1].
    each component is based on a halton sequence.
    quasi random is good enough for our purposes and is
    more evenly distributed then pseudo random sequences.
    See en.m.wikipedia.org/wiki/Halton_sequence
    """

    def halton(index, base):
        result = 0
        f = 1.0 / base
        I = index
        while I > 0:
            result += f * (I % base)
            I = int(I / base)
            f /= base
        return result
    return Vector((halton(index, 2), halton(index, 3), halton(index, 5)))


def insidegroup(pointrelativetocursor, group):
    if bpy.data.groups.find(group) < 0:
        return False
    for ob in bpy.data.groups[group].objects:
        if pointInsideMesh(pointrelativetocursor, ob):
            return True
    return False


def groupdistribution(crowngroup, shadowgroup=None, seed=0, size=Vector((1, 1, 1)), pointrelativetocursor=Vector((0, 0, 0))):
    if crowngroup == shadowgroup:
        shadowgroup = None  # safeguard otherwise every marker would be rejected
    nocrowngroup = bpy.data.groups.find(crowngroup) < 0
    noshadowgroup = (shadowgroup is None) or (bpy.data.groups.find(shadowgroup) < 0) or (shadowgroup == 'None')
    index = 100 + seed
    nmarkers = 0
    nyield = 0
    while True:
        nmarkers += 1
        v = halton3D(index)
        v[0] *= size[0]
        v[1] *= size[1]
        v[2] *= size[2]
        v += pointrelativetocursor
        index += 1
        insidecrown = nocrowngroup or insidegroup(v, crowngroup)
        outsideshadow = noshadowgroup or not insidegroup(v, shadowgroup)
        # if shadowgroup overlaps all or a significant part of the crowngroup
        # no markers will be yielded and we would be in an endless loop.
        # so if we yield too few correct markers we start yielding them anyway.
        lowyieldrate = (nmarkers > 200) and (nyield / nmarkers < 0.01)
        if (insidecrown and outsideshadow) or lowyieldrate:
            nyield += 1
            yield v


def groupExtends(group):
    """
    return a size,minimum tuple both Vector elements, describing the size and position
    of the bounding box in world space that encapsulates all objects in a group.
    """
    bb = []
    if bpy.data.groups.find(group) >= 0:
        for ob in bpy.data.groups[group].objects:
            rot = ob.matrix_world.to_quaternion()
            scale = ob.matrix_world.to_scale()
            translate = ob.matrix_world.translation
            for v in ob.bound_box:  # v is not a vector but an array of floats
                p = ob.matrix_world * Vector(v[0:3])
                bb.extend(p[0:3])
    mx = Vector((max(bb[0::3]), max(bb[1::3]), max(bb[2::3])))
    mn = Vector((min(bb[0::3]), min(bb[1::3]), min(bb[2::3])))
    return mx - mn, mn


def createLeaves(tree, probability=0.5, size=0.5, randomsize=0.1, randomrot=0.1, maxconnections=2, bunchiness=1.0, connectoffset=-0.1):
    p = bpy.context.scene.cursor_location

    verts = []
    faces = []
    c1 = Vector((connectoffset, -size / 2, 0))
    c2 = Vector((size+connectoffset, -size / 2, 0))
    c3 = Vector((size+connectoffset, size / 2, 0))
    c4 = Vector((connectoffset, size / 2, 0))
    t = gauss(1.0 / probability, 0.1)
    bpswithleaves = 0
    for bp in tree.branchpoints:
        if bp.connections < maxconnections:

            dv = tree.branchpoints[bp.parent].v - bp.v if bp.parent else Vector((0, 0, 0))
            dvp = Vector((0, 0, 0))

            bpswithleaves += 1
            nleavesonbp = 0
            while t < bpswithleaves:
                nleavesonbp += 1
                rx = (random() - 0.5) * randomrot * 6.283  # TODO vertical tilt in direction of tropism
                ry = (random() - 0.5) * randomrot * 6.283
                rot = Euler((rx, ry, random() * 6.283), 'ZXY')
                scale = 1 + (random() - 0.5) * randomsize
                v = c1.copy()
                v.rotate(rot)
                verts.append(v * scale + bp.v + dvp)
                v = c2.copy()
                v.rotate(rot)
                verts.append(v * scale + bp.v + dvp)
                v = c3.copy()
                v.rotate(rot)
                verts.append(v * scale + bp.v + dvp)
                v = c4.copy()
                v.rotate(rot)
                verts.append(v * scale + bp.v + dvp)
                n = len(verts)
                faces.append((n - 1, n - 4, n - 3, n - 2))
                t += gauss(1.0 / probability, 0.1)                      # this is not the best choice of distribution because we might get negative values especially if sigma is large
                dvp = nleavesonbp * (dv / (probability ** bunchiness))  # TODO add some randomness to the offset

    mesh = bpy.data.meshes.new('Leaves')
    mesh.from_pydata(verts, [], faces)
    mesh.update(calc_edges=True)
    mesh.uv_textures.new()
    return mesh


def createMarkers(tree, scale=0.05):
    #not used as markers are parented to tree object that is created at the cursor position
    #p=bpy.context.scene.cursor_location

    verts = []
    faces = []

    tetraeder = [Vector((-1, 1, -1)), Vector((1, -1, -1)), Vector((1, 1, 1)), Vector((-1, -1, 1))]
    tetraeder = [v * scale for v in tetraeder]
    tfaces = [(0, 1, 2), (0, 1, 3), (1, 2, 3), (0, 3, 2)]

    for ep in tree.endpoints:
        verts.extend([ep + v for v in tetraeder])
        n = len(faces)
        faces.extend([(f1 + n, f2 + n, f3 + n) for f1, f2, f3 in tfaces])

    mesh = bpy.data.meshes.new('Markers')
    mesh.from_pydata(verts, [], faces)
    mesh.update(calc_edges=True)
    return mesh


def createObjects(tree, parent=None, objectname=None, probability=0.5, size=0.5, randomsize=0.1, randomrot=0.1, maxconnections=2, bunchiness=1.0):

    if (parent is None) or (objectname is None) or (objectname == 'None'):
        return

    # not necessary, we parent the new objects: p=bpy.context.scene.cursor_location

    theobject = bpy.data.objects[objectname]

    t = gauss(1.0 / probability, 0.1)
    bpswithleaves = 0
    for bp in tree.branchpoints:
        if bp.connections < maxconnections:

            dv = tree.branchpoints[bp.parent].v - bp.v if bp.parent else Vector((0, 0, 0))
            dvp = Vector((0, 0, 0))

            bpswithleaves += 1
            nleavesonbp = 0
            while t < bpswithleaves:
                nleavesonbp += 1
                rx = (random() - 0.5) * randomrot * 6.283  # TODO vertical tilt in direction of tropism
                ry = (random() - 0.5) * randomrot * 6.283
                rot = Euler((rx, ry, random() * 6.283), 'ZXY')
                scale = size + (random() - 0.5) * randomsize

                # add new object and parent it
                obj = bpy.data.objects.new(objectname, theobject.data)
                obj.location = bp.v + dvp
                obj.rotation_mode = 'ZXY'
                obj.rotation_euler = rot[:]
                obj.scale = [scale, scale, scale]
                obj.parent = parent
                bpy.context.scene.objects.link(obj)

                t += gauss(1.0 / probability, 0.1)                      # this is not the best choice of distribution because we might get negative values especially if sigma is large
                dvp = nleavesonbp * (dv / (probability ** bunchiness))  # TODO add some randomness to the offset


def vertextend(v, dv):
    n = len(v)
    v.extend(dv)
    return tuple(range(n, n + len(dv)))


def vertcopy(loopa, v, p):
    dv = [v[i] + p for i in loopa]
    #print(loopa,p,dv)
    return vertextend(v, dv)


def bend(p0, p1, p2, loopa, loopb, verts):
    # will extend this with a tri centered at p0
    #print('bend')
    return bridgequads(loopa, loopb, verts)


def extend(p0, p1, p2, loopa, verts):
    # will extend this with a tri centered at p0
    #print('extend')
    #print(p0,p1,p2,[verts[i] for i in loopa])

    # both difference point upward, we extend to the second
    d1 = p1 - p0
    d2 = p0 - p2
    p = (verts[loopa[0]] + verts[loopa[1]] + verts[loopa[2]] + verts[loopa[3]]) / 4
    a = d1.angle(d2, 0)
    if abs(a) < 0.05:
        #print('small angle')
        loopb = vertcopy(loopa, verts, p0 - d2 / 2 - p)
        # all verts in loopb are displaced the same amount so no need to find the minimum distance
        n = 4
        return ([(loopa[(i) % n], loopa[(i + 1) % n], loopb[(i + 1) % n], loopb[(i) % n]) for i in range(n)], loopa, loopb)

    r = d2.cross(d1)
    q = Quaternion(r, -a)
    dverts = [verts[i] - p for i in loopa]
    #print('large angle',dverts,'axis',r)
    for dv in dverts:
        dv.rotate(q)
    #print('rotated',dverts)
    for dv in dverts:
        dv += (p0 - d2 / 2)
    #print('moved',dverts)
    loopb = vertextend(verts, dverts)
    # none of the verts in loopb are rotated so no need to find the minimum distance
    n = 4
    return ([(loopa[(i) % n], loopa[(i + 1) % n], loopb[(i + 1) % n], loopb[(i) % n]) for i in range(n)], loopa, loopb)


def nonfork(bp, parent, apex, verts, p, branchpoints):
    #print('nonfork bp    ',bp.index,bp.v,bp.loop if hasattr(bp,'loop') else None)
    #print('nonfork parent',parent.index,parent.v,parent.loop if hasattr(parent,'loop') else None)
    #print('nonfork apex  ',apex.index,apex.v,apex.loop if hasattr(apex,'loop') else None)
    if hasattr(bp, 'loop'):
        if hasattr(apex, 'loop'):
            #print('nonfork bend bp->apex')
            return bend(bp.v + p, parent.v + p, apex.v + p, bp.loop, apex.loop, verts)
        else:
            #print('nonfork extend bp->apex')
            faces, loop1, loop2 = extend(bp.v + p, parent.v + p, apex.v + p, bp.loop, verts)
            apex.loop = loop2
            return faces, loop1, loop2
    else:
        if hasattr(parent, 'loop'):
            #print('nonfork extend from bp->parent')
            #faces,loop1,loop2 =  extend(bp.v+p, apex.v+p, parent.v+p, parent.loop, verts)
            if parent.parent is None:
                return None, None, None
            grandparent = branchpoints[parent.parent]
            faces, loop1, loop2 = extend(grandparent.v + p, parent.v + p, bp.v + p, parent.loop, verts)
            bp.loop = loop2
            return faces, loop1, loop2
        else:
            #print('nonfork no loop')
            # neither parent nor apex already have a loop calculated
            # will fill this later ...
            return None, None, None


def endpoint(bp, parent, verts, p):
    # extrapolate to tip of branch. we do not close the tip for now
    faces, loop1, loop2 = extend(bp.v + p, parent.v + p, bp.v + (bp.v - parent.v) + p, bp.loop, verts)
    return faces, loop1, loop2


def root(bp, apex, verts, p):
    # extrapolate non-forked roots
    faces, loop1, loop2 = extend(bp.v + p, bp.v - (apex.v - bp.v) + p, apex.v + p, bp.loop, verts)
    apex.loop = loop2
    return faces, loop1, loop2


def skin(aloop, bloop, faces):
    n = len(aloop)
    for i in range(n):
        faces.append((aloop[i], aloop[(i + 1) % n], bloop[(i + 1) % n], bloop[i]))


def createGeometry(tree, power=0.5, scale=0.01, addleaves=False, pleaf=0.5, leafsize=0.5, leafrandomsize=0.1, leafrandomrot=0.1,
    nomodifiers=True, skinmethod='NATIVE', subsurface=False,
    maxleafconnections=2, bleaf=1.0, connectoffset=-0.1,
    timeperf=True):

    timings = Timer()

    p = bpy.context.scene.cursor_location
    verts = []
    edges = []
    faces = []
    radii = []
    roots = set()

    # Loop over all branchpoints and create connected edges
    for n, bp in enumerate(tree.branchpoints):
        verts.append(bp.v + p)
        radii.append(bp.connections)
        bp.index = n
        if not (bp.parent is None):
            edges.append((len(verts) - 1, bp.parent))
        else:
            nv = len(verts)
            roots.add(nv - 1)

    timings.add('skeleton')

    # native skinning method
    if nomodifiers is False and skinmethod == 'NATIVE':
        # add a quad edge loop to all roots
        for r in roots:
            rootp = verts[r]
            nv = len(verts)
            radius = 0.7071 * ((tree.branchpoints[r].connections + 1) ** power) * scale
            verts.extend([rootp + Vector((-radius, -radius, 0)), rootp + Vector((radius, -radius, 0)), rootp + Vector((radius, radius, 0)), rootp + Vector((-radius, radius, 0))])
            tree.branchpoints[r].loop = (nv, nv + 1, nv + 2, nv + 3)
            #print('root verts',tree.branchpoints[r].loop)
            #faces.append((nv,nv+1,nv+2))
            edges.extend([(nv, nv + 1), (nv + 1, nv + 2), (nv + 2, nv + 3), (nv + 3, nv)])

        # skin all forked branchpoints, no attempt is yet made to adjust the radius
        forkfork = set()
        for bpi, bp in enumerate(tree.branchpoints):
            if not(bp.apex is None or bp.shoot is None):
                apex = tree.branchpoints[bp.apex]
                shoot = tree.branchpoints[bp.shoot]
                p0 = bp.v
                r0 = ((bp.connections + 1) ** power) * scale
                p2 = apex.v
                r2 = ((apex.connections + 1) ** power) * scale
                p3 = shoot.v
                r3 = ((shoot.connections + 1) ** power) * scale

                if bp.parent is not None:
                    parent = tree.branchpoints[bp.parent]
                    p1 = parent.v
                    r1 = (parent.connections ** power) * scale
                else:
                    p1 = p0 - (p2 - p0)
                    r1 = r0

                skinverts, skinfaces = quadfork(p0, p1, p2, p3, r0, r1, r2, r3)
                nv = len(verts)
                verts.extend([v + p for v in skinverts])
                faces.extend([tuple(v + nv for v in f) for f in skinfaces])

                # the vertices of the quads at the end of the internodes are returned as the first 12 vertices of a total of 22
                # we store them for reuse by non-forked internodes but first check if we have a fork to fork connection
                nv = len(verts)
                if hasattr(bp, 'loop') and not (bpi in forkfork):  # already assigned by another fork
                    faces.extend(bridgequads(bp.loop, [nv - 22, nv - 21, nv - 20, nv - 19], verts)[0])
                    forkfork.add(bpi)
                else:
                    bp.loop = [nv - 22, nv - 21, nv - 20, nv - 19]

                if hasattr(apex, 'loop') and not (bp.apex in forkfork):  # already assigned by another fork but not yet skinned
                    faces.extend(bridgequads(apex.loop, [nv - 18, nv - 17, nv - 16, nv - 15], verts)[0])
                    forkfork.add(bp.apex)
                else:
                    apex.loop = [nv - 18, nv - 17, nv - 16, nv - 15]

                if hasattr(shoot, 'loop') and not (bp.shoot in forkfork):  # already assigned by another fork but not yet skinned
                    faces.extend(bridgequads(shoot.loop, [nv - 14, nv - 13, nv - 12, nv - 11], verts)[0])
                    forkfork.add(bp.shoot)
                else:
                    shoot.loop = [nv - 14, nv - 13, nv - 12, nv - 11]

        # skin the roots that are not forks
        for r in roots:
            bp = tree.branchpoints[r]
            if bp.apex is not None and bp.parent is None and bp.shoot is None:
                bfaces, apexloop, parentloop = root(bp, tree.branchpoints[bp.apex], verts, p)
                if bfaces is not None:
                    faces.extend(bfaces)

        # skin all non-forking branchpoints, that is those not a root or and endpoint
        skinnednonforks = set()
        start = -1
        while(start != len(skinnednonforks)):
            start = len(skinnednonforks)
            #print('-'*20,start)
            for bp in tree.branchpoints:
                if bp.shoot is None and not (bp.parent is None or bp.apex is None or bp in skinnednonforks):
                    bfaces, apexloop, parentloop = nonfork(bp, tree.branchpoints[bp.parent], tree.branchpoints[bp.apex], verts, p, tree.branchpoints)
                    if bfaces is not None:
                        #print(bfaces,apexloop,parentloop)
                        faces.extend(bfaces)
                        skinnednonforks.add(bp)

        # skin endpoints
        for bp in tree.branchpoints:
            if bp.apex is None and bp.parent is not None:
                bfaces, apexloop, parentloop = endpoint(bp, tree.branchpoints[bp.parent], verts, p)
                if bfaces is not None:
                    faces.extend(bfaces)
    # end of native skinning section
    timings.add('nativeskin')

    # create the tree mesh
    mesh = bpy.data.meshes.new('Tree')
    mesh.from_pydata(verts, edges, faces)
    mesh.update(calc_edges=True)

    # create the tree object an make it the only selected and active object in the scene
    obj_new = bpy.data.objects.new(mesh.name, mesh)
    base = bpy.context.scene.objects.link(obj_new)
    for ob in bpy.context.scene.objects:
        ob.select = False
    base.select = True
    bpy.context.scene.objects.active = obj_new
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR')

    timings.add('createmesh')

    # add a subsurf modifier to smooth the branches
    if nomodifiers is False:
        if subsurface:
            bpy.ops.object.modifier_add(type='SUBSURF')
            bpy.context.active_object.modifiers[0].levels = 1
            bpy.context.active_object.modifiers[0].render_levels = 1

        # add a skin modifier
        if skinmethod == 'BLENDER':
            bpy.ops.object.modifier_add(type='SKIN')
            bpy.context.active_object.modifiers[-1].use_smooth_shade = True
            bpy.context.active_object.modifiers[-1].use_x_symmetry = True
            bpy.context.active_object.modifiers[-1].use_y_symmetry = True
            bpy.context.active_object.modifiers[-1].use_z_symmetry = True

            skinverts = bpy.context.active_object.data.skin_vertices[0].data

            for i, v in enumerate(skinverts):
                v.radius = [(radii[i] ** power) * scale, (radii[i] ** power) * scale]
                if i in roots:
                    v.use_root = True

            # add an extra subsurf modifier to smooth the skin
            bpy.ops.object.modifier_add(type='SUBSURF')
            bpy.context.active_object.modifiers[-1].levels = 1
            bpy.context.active_object.modifiers[-1].render_levels = 2

    timings.add('modifiers')

    # create the leaves object
    if addleaves:
        mesh = createLeaves(tree, pleaf, leafsize, leafrandomsize, leafrandomrot, maxleafconnections, bleaf, connectoffset)
        obj_leaves = bpy.data.objects.new(mesh.name, mesh)
        base = bpy.context.scene.objects.link(obj_leaves)
        obj_leaves.parent = obj_new
        bpy.context.scene.objects.active = obj_leaves
        bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
        bpy.context.scene.objects.active = obj_new

    timings.add('leaves')

    if timeperf:
        print(timings)

    return obj_new


class SCATree(bpy.types.Operator):
    bl_idname = "mesh.sca_tree"
    bl_label = "SCATree"
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}

    internodeLength = FloatProperty(name="Internode Length",
                    description="Internode length in Blender Units",
                    default=0.75,
                    min=0.01,
                    soft_max=3.0,
                    subtype='DISTANCE',
                    unit='LENGTH')
    killDistance = FloatProperty(name="Kill Distance",
                    description="Kill Distance as a multiple of the internode length",
                    default=3,
                    min=0.01,
                    soft_max=100.0)
    influenceRange = FloatProperty(name="Influence Range",
                    description="Influence Range as a multiple of the internode length",
                    default=15,
                    min=0.01,
                    soft_max=100.0)
    tropism = FloatProperty(name="Tropism",
                    description="The tendency of branches to bend up or down",
                    default=0,
                    min=-1.0,
                    soft_max=1.0)
    power = FloatProperty(name="Power",
                    description="Tapering power of branch connections",
                    default=0.3,
                    min=0.01,
                    soft_max=1.0)
    scale = FloatProperty(name="Scale",
                    description="Branch size",
                    default=0.01,
                    min=0.0001,
                    soft_max=1.0)

    # the group related properties are not saved as presets because on reload no groups with the same names might exist, causing an exception
    useGroups = BoolProperty(name="Use object groups",
                    options={'ANIMATABLE', 'SKIP_SAVE'},
                    description="Use groups of objects to specify marker distribution",
                    default=False)

    crownGroup = EnumProperty(items=availableGroups,
                    options={'ANIMATABLE', 'SKIP_SAVE'},
                    name='Crown Group',
                    description='Group of objects that specify crown shape')

    shadowGroup = EnumProperty(items=availableGroupsOrNone,
                    options={'ANIMATABLE', 'SKIP_SAVE'},
                    name='Shadow Group',
                    description='Group of objects subtracted from the crown shape')

    exclusionGroup = EnumProperty(items=availableGroupsOrNone,
                    options={'ANIMATABLE', 'SKIP_SAVE'},
                    name='Exclusion Group',
                    description='Group of objects that will not be penetrated by growing branches')

    useTrunkGroup = BoolProperty(name="Use trunk group",
                    options={'ANIMATABLE', 'SKIP_SAVE'},
                    description="Use the locations of a group of objects to specify trunk starting points instead of 3d cursor",
                    default=False)

    trunkGroup = EnumProperty(items=availableGroups,
                    options={'ANIMATABLE', 'SKIP_SAVE'},
                    name='Trunk Group',
                    description='Group of objects whose locations specify trunk starting points')

    crownSize = FloatProperty(name="Crown Size",
                    description="Crown size",
                    default=5,
                    min=1,
                    soft_max=29)
    crownShape = FloatProperty(name="Crown Shape",
                    description="Crown shape",
                    default=1,
                    min=0.2,
                    soft_max=5)
    crownOffset = FloatProperty(name="Crown Offset",
                    description="Crown offset (the length of the bole)",
                    default=3,
                    min=0,
                    soft_max=20.0)
    surfaceBias = FloatProperty(name="Surface Bias",
                    description="Surface bias (how much markers are favored near the surface)",
                    default=1,
                    min=-10,
                    soft_max=10)
    topBias = FloatProperty(name="Top Bias",
                    description="Top bias (how much markers are favored near the top)",
                    default=1,
                    min=-10,
                    soft_max=10)
    randomSeed = IntProperty(name="Random Seed",
                    description="The seed governing random generation",
                    default=0,
                    min=0)
    maxIterations = IntProperty(name="Maximum Iterations",
                    description="The maximum number of iterations allowed for tree generation",
                    default=40,
                    min=0)
    numberOfEndpoints = IntProperty(name="Number of Endpoints",
                    description="The number of endpoints generated in the growing volume",
                    default=100,
                    min=0)
    newEndPointsPer1000 = IntProperty(name="Number of new Endpoints",
                    description="The number of new endpoints generated in the growing volume per thousand iterations",
                    default=0,
                    min=0)
    maxTime = FloatProperty(name="Maximum Time",
                    description=("The maximum time to run the generation for "
                                "in seconds/generation (0.0 = Disabled). Currently ignored"),
                    default=0.0,
                    min=0.0,
                    soft_max=10)
    pLeaf = FloatProperty(name="Leaves per internode",
                    description=("The average number of leaves per internode"),
                    default=0.5,
                    min=0.0,
                    soft_max=4)
    bLeaf = FloatProperty(name="Leaf clustering",
                    description=("How much leaves cluster to the end of the internode"),
                    default=1,
                    min=1,
                    soft_max=4)
    leafSize = FloatProperty(name="Leaf Size",
                    description=("The leaf size"),
                    default=0.5,
                    min=0.0,
                    soft_max=1)
    leafRandomSize = FloatProperty(name="Leaf Random Size",
                    description=("The amount of randomness to add to the leaf size"),
                    default=0.1,
                    min=0.0,
                    soft_max=10)
    leafRandomRot = FloatProperty(name="Leaf Random Rotation",
                    description=("The amount of random rotation to add to the leaf"),
                    default=0.1,
                    min=0.0,
                    soft_max=1)
    connectoffset = FloatProperty(name="Connect Offset",
                    description=("Offset of leaf to twig"),
                    default=-0.1)
    leafMaxConnections = IntProperty(name="Max Connections",
                    description="The maximum number of connections of an internode elegible for a leaf",
                    default=2,
                    min=0)
    addLeaves = BoolProperty(name="Add Leaves", default=False)

    objectName = EnumProperty(items=availableObjects,
                    options={'ANIMATABLE', 'SKIP_SAVE'},
                    name='Object Name',
                    description='Name of additional objects to duplicate at the branchpoints')
    pObject = FloatProperty(name="Objects per internode",
                    description=("The average number of objects per internode"),
                    default=0.3,
                    min=0.0,
                    soft_max=1)
    bObject = FloatProperty(name="Object clustering",
                    description=("How much objects cluster to the end of the internode"),
                    default=1,
                    min=1,
                    soft_max=4)
    objectSize = FloatProperty(name="Object Size",
                    description=("The object size"),
                    default=1,
                    min=0.0,
                    soft_max=2)
    objectRandomSize = FloatProperty(name="Object Random Size",
                    description=("The amount of randomness to add to the object size"),
                    default=0.1,
                    min=0.0,
                    soft_max=10)
    objectRandomRot = FloatProperty(name="Object Random Rotation",
                    description=("The amount of random rotation to add to the object"),
                    default=0.1,
                    min=0.0,
                    soft_max=1)
    objectMaxConnections = IntProperty(name="Max Connections for Object",
                    description="The maximum number of connections of an internode elegible for a object",
                    default=1,
                    min=0)
    addObjects = BoolProperty(name="Add Objects", default=False)

    updateTree = BoolProperty(name="Update Tree", default=False)

    noModifiers = BoolProperty(name="No Modifers", default=True)
    subSurface = BoolProperty(name="Sub Surface", default=False, description="Add subsurface modifier to trunk skin")
    skinMethod = EnumProperty(items=[('NATIVE', 'Native', 'Built in skinning method', 1), ('BLENDER', 'Skin modifier', 'Use Blenders skin modifier', 2)],
                    options={'ANIMATABLE', 'SKIP_SAVE'},
                    name='Skinning method',
                    description='How to add a surface to the trunk skeleton')

    showMarkers = BoolProperty(name="Show Markers", default=False)
    markerScale = FloatProperty(name="Marker Scale",
                    description=("The size of the markers"),
                    default=0.05,
                    min=0.001,
                    soft_max=0.2)
    timePerformance = BoolProperty(name="Time performance", default=False, description="Show duration of generation steps on console")

    @classmethod
    def poll(self, context):
        # Check if we are in object mode
        return context.mode == 'OBJECT'

    def execute(self, context):

        if not self.updateTree:
            return {'PASS_THROUGH'}

        timings = Timer()

        # necessary otherwize ray casts toward these objects may fail. However if nothing is selected, we get a runtime error ...
        try:
            bpy.ops.object.mode_set(mode='EDIT', toggle=False)
            bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
        except RuntimeError:
            pass

        if self.useGroups:
            size, minp = groupExtends(self.crownGroup)
            volumefie = partial(groupdistribution, self.crownGroup, self.shadowGroup, self.randomSeed, size, minp - bpy.context.scene.cursor_location)
        else:
            volumefie = partial(ellipsoid2, self.crownSize * self.crownShape, self.crownSize, Vector((0, 0, self.crownSize + self.crownOffset)), self.surfaceBias, self.topBias)

        startingpoints = []
        if self.useTrunkGroup:
            if bpy.data.groups.find(self.trunkGroup) >= 0:
                for ob in bpy.data.groups[self.trunkGroup].objects:
                    p = ob.location - context.scene.cursor_location
                    startingpoints.append(Branchpoint(p, None))

        timings.add('scastart')
        sca = SCA(NBP=self.maxIterations,
            NENDPOINTS=self.numberOfEndpoints,
            d=self.internodeLength,
            KILLDIST=self.killDistance,
            INFLUENCE=self.influenceRange,
            SEED=self.randomSeed,
            TROPISM=self.tropism,
            volume=volumefie,
            exclude=lambda p: insidegroup(p, self.exclusionGroup),
            startingpoints=startingpoints)
        timings.add('sca')

        if self.showMarkers:
            mesh = createMarkers(sca, self.markerScale)
            obj_markers = bpy.data.objects.new(mesh.name, mesh)
            base = bpy.context.scene.objects.link(obj_markers)
        timings.add('showmarkers')

        sca.iterate2(newendpointsper1000=self.newEndPointsPer1000, maxtime=self.maxTime)
        timings.add('iterate')

        obj_new = createGeometry(sca, self.power, self.scale, self.addLeaves, self.pLeaf, self.leafSize, self.leafRandomSize, self.leafRandomRot,
            self.noModifiers, self.skinMethod, self.subSurface,
            self.leafMaxConnections, self.bLeaf, self.connectoffset,
            self.timePerformance)

        timings.add('objcreationstart')
        if self.addObjects:
            createObjects(sca, obj_new,
                objectname=self.objectName,
                probability=self.pObject,
                size=self.objectSize,
                randomsize=self.objectRandomSize,
                randomrot=self.objectRandomRot,
                maxconnections=self.objectMaxConnections,
                bunchiness=self.bObject)
        timings.add('objcreation')

        if self.showMarkers:
            obj_markers.parent = obj_new

        self.updateTree = False

        if self.timePerformance:
            timings.add('Total')
            print(timings)

        return {'FINISHED'}

    def draw(self, context):
        layout = self.layout

        layout.prop(self, 'updateTree', icon='MESH_DATA')

        columns = layout.row()
        col1 = columns.column()
        col2 = columns.column()

        box = col1.box()
        box.label("Generation Settings:")
        box.prop(self, 'randomSeed')
        box.prop(self, 'maxIterations')

        box = col1.box()
        box.label("Shape Settings:")
        box.prop(self, 'numberOfEndpoints')
        box.prop(self, 'internodeLength')
        box.prop(self, 'influenceRange')
        box.prop(self, 'killDistance')
        box.prop(self, 'power')
        box.prop(self, 'scale')
        box.prop(self, 'tropism')

        newbox = col2.box()
        newbox.label("Crown shape")
        newbox.prop(self, 'useGroups')
        if self.useGroups:
            newbox.label("Object groups defining crown shape")
            groupbox = newbox.box()
            groupbox.prop(self, 'crownGroup')
            groupbox = newbox.box()
            groupbox.alert = (self.shadowGroup == self.crownGroup)
            groupbox.prop(self, 'shadowGroup')
            groupbox = newbox.box()
            groupbox.alert = (self.exclusionGroup == self.crownGroup)
            groupbox.prop(self, 'exclusionGroup')
        else:
            newbox.label("Simple ellipsoid defining crown shape")
            newbox.prop(self, 'crownSize')
            newbox.prop(self, 'crownShape')
            newbox.prop(self, 'crownOffset')
        newbox = col2.box()
        newbox.prop(self, 'useTrunkGroup')
        if self.useTrunkGroup:
            newbox.prop(self, 'trunkGroup')

        box.prop(self, 'surfaceBias')
        box.prop(self, 'topBias')
        box.prop(self, 'newEndPointsPer1000')

        box = col2.box()
        box.label("Skin options:")
        box.prop(self, 'noModifiers')
        if not self.noModifiers:
            box.prop(self, 'skinMethod')
            box.prop(self, 'subSurface')

        layout.prop(self, 'addLeaves', icon='MESH_DATA')
        if self.addLeaves:
            box = layout.box()
            box.label("Leaf Settings:")
            box.prop(self, 'pLeaf')
            box.prop(self, 'bLeaf')
            box.prop(self, 'leafSize')
            box.prop(self, 'leafRandomSize')
            box.prop(self, 'leafRandomRot')
            box.prop(self, 'connectoffset')
            box.prop(self, 'leafMaxConnections')

        layout.prop(self, 'addObjects', icon='MESH_DATA')
        if self.addObjects:
            box = layout.box()
            box.label("Object Settings:")
            box.prop(self, 'objectName')
            box.prop(self, 'pObject')
            box.prop(self, 'bObject')
            box.prop(self, 'objectSize')
            box.prop(self, 'objectRandomSize')
            box.prop(self, 'objectRandomRot')
            box.prop(self, 'objectMaxConnections')

        box = layout.box()
        box.label("Debug Settings:")
        box.prop(self, 'showMarkers')
        if self.showMarkers:
            box.prop(self, 'markerScale')
        box.prop(self, 'timePerformance')


def menu_func(self, context):
    self.layout.operator(SCATree.bl_idname, text="Add Tree to Scene",
                                                icon='PLUGIN').updateTree = True


def register():
    bpy.utils.register_module(__name__)
    bpy.types.INFO_MT_mesh_add.append(menu_func)


def unregister():
    bpy.types.INFO_MT_mesh_add.remove(menu_func)
    bpy.utils.unregister_module(__name__)


if __name__ == "__main__":
    register()

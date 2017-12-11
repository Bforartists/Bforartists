bl_info = {"name": "Snowflake Generator",
           "author": "Eoin Brennan (Mayeoin Bread)",
           "version": (1, 2),
           "blender": (2, 7, 4),
           "location": "View3D > Add > Mesh",
           "descrition": "Adds a randomly generated snowflake",
           "warning": "",
           "wiki_url": "",
           "tracker_url": "",
           "category": "Add Mesh"}

# imports
import bpy
import bmesh
from mathutils import Vector
from bpy.props import IntProperty, BoolProperty
from math import pi, sin, cos, asin, acos, atan
from random import *


class SnowflakeGen(bpy.types.Operator):
    """Snowflake Generator"""
    bl_idname = "mesh.snowflake"
    bl_label = "Snowflake"
    bl_options = {"REGISTER", "UNDO"}

    # User-changeable variables
    numR = IntProperty(name="Number of outer rings", default=1, min=0, max=2)
    numV = IntProperty(name="Vertices", default=6, min=3, max=12)
    fill = BoolProperty(name="Fill center", default=True)

    def execute(self, context):
        bpy.context.space_data.pivot_point = 'CURSOR'
        bpy.ops.view3d.snap_cursor_to_center()
        # add new object if non-existant

        def create_mesh_object(context, verts, edges, faces, name):
            mesh = bpy.data.meshes.new(name)
            mesh.from_pydate(vers, edges, faces)
            mesh.update()
            from byp_extras import object_utils
            return object_utils.object_data_add(context, mesh, operator=None)

        def addObj():
            obj = bpy.context.object
            if obj == None:
                bpy.ops.object.add(type='MESH', enter_editmode=True, view_align=False, location=(0.0, 0.0, 0.0), rotation=(0.0, 0.0, 0.0))
                obj = bpy.context.object
                obj.name = "Snowflake"
            else:
                obj = bpy.context.object
                obj.name = "Snowflake"
            return obj
        # select a single vert

        def selVert(par):
            bm.verts.ensure_lookup_table()
            bpy.ops.mesh.select_all(action='DESELECT')
            bm.verts[par].select = True
        # select a single edge

        def selEdge(par):
            bm.edges.ensure_lookup_table()
            bpy.ops.mesh.select_all(action='DESELECT')
            bm.edges[par].select = True
        # select last added vert

        def selLasVert():
            for v in bm.verts:
                bpy.ops.mesh.select_all(action='DESELECT')
                v.select = True
        # select last added edge

        def selLasEdge():
            for e in bm.edges:
                bpy.ops.mesh.select_all(action='DESELECT')
                e.select = True
        # extrude and move along vector

        def extMov(vec):
            bpy.ops.mesh.extrude_region_move(TRANSFORM_OT_translate={"value": vec})
        # rotate around z-axis origin

        def rotate(ang):
            bpy.ops.transform.rotate(value=(-ang), axis=(0.0, 0.0, 0.1))
        # subdivide

        def subdiv(num):
            if num > 0:
                bpy.ops.mesh.subdivide(number_cuts=num)
        # get number of verts

        def numVerts():
            vco = 0
            for v in bm.verts:
                vco += 1
            return vco - 1
        # get number of edges

        def numEdges():
            eco = 0
            for e in bm.edges:
                eco += 1
            return eco - 1
        # duplicate and move along vector

        def dupMove(vec):
            bpy.ops.mesh.duplicate_move(TRANSFORM_OT_translate={"value": vec})

        def extLeg(vert, length, minus):
            selVert(vert)
            if minus == 0:
                legVec = Vector((length * cos(pi / 4), length * sin(pi / 4), 0.0))
                extMov(legVec)
            else:
                legVec = Vector((-length * cos(pi / 4), length * sin(pi / 4), 0.0))
                extMov(legVec)

        def extLeg2(vert, length, angle):
            selVert(vert)
            legVec = Vector((length * sin(angle), length * cos(angle), 0.0))
            extMov(legVec)
        obj = addObj()
        bm = bmesh.from_edit_mesh(obj.data)
        if obj.type == "MESH":
            if obj.mode == "OBJECT":
                bpy.ops.object.mode_set(mode="EDIT")
            if obj.mode == "EDIT":
                # delete all verts
                bpy.ops.mesh.select_all(action='SELECT')
                bpy.ops.mesh.delete(type='VERT')
                bm.verts.ensure_lookup_table()
                bm.edges.ensure_lookup_table()
                # add circle (base for snowflake)
                bpy.ops.mesh.primitive_circle_add(
                    vertices=self.numV,
                    radius=1.0,
                    fill_type='NOTHING',
                    location=(0.0, 0.0, 0.0),
                    rotation=(0.0, 0.0, 0.0),
                    view_align=False,
                    enter_editmode=True)
                bm.verts.ensure_lookup_table()
                bm.edges.ensure_lookup_table()
                # variables...
                rnum = randint(0, 1)
                if rnum == 0:
                    s1 = 1
                    s2 = 2
                else:
                    s1 = 2
                    s2 = 1
                fillC = self.fill
                vCount = 0
                oVerts = []
                rand1 = 2
    #            rando = uniform(0.5,1.0)
                rando = uniform(0.2, 1.0) * 2
                nullV = Vector((0.0, 0.0, 0.0))
                randleg = randint(1, 3)
                randInternal = randint(0, randleg)
                numRings = self.numR
                # count + store number of verts in base circle
                for v in bm.verts:
                    vCount += 1
                    oVerts.append(v.index)
                oVerts.pop(0)
                # vectors for length of edge and angles
                bm.verts.ensure_lookup_table()
                root = bm.verts[0].co
                x = bm.verts[1].co
                y = bm.verts[vCount - 1].co
                # length of arm
                d = ((root.x - x.x)**2 + (root.y - x.y)**2)**0.5
                x = x + root
                y = y + root
                # vector dot product
                ab = (x.x * y.x) + (x.y * y.y) + (x.z * y.z)
                aa = ((x.x**2) + (x.y**2) + (x.z**2))**0.5
                bb = ((y.x**2) + (y.y**2) + (y.z**2))**0.5
                angle = acos(ab / (aa * bb))
                # Extrude top vert upwards
                selVert(0)
                myVec = Vector((0.0, d * rando * 2, 0.0))
                extMov(myVec)
                # Subdivide
                selLasEdge()
                subdiv(1)
                # Save d, randomise new d for legs
                dd = d
                d = d * uniform(0.4, 1.0)
                # Position new vert
                bm.verts.ensure_lookup_table()
                lastVert = numVerts()
                bm.verts[lastVert].co = root
                bm.verts[lastVert].co.y = root.y + (vCount - 1) * (d * rando * 2) / vCount
                # Extrude right leg
                extLeg(lastVert, (4 * dd / d) / vCount, 0)
                # Extrude left leg
                bm.verts.ensure_lookup_table()
                extLeg(lastVert, (4 * dd / d) / vCount, 1)
                ##
                #   if d < 0.8*dd, add 1 or two more sets of legs on end
                ##
                # Extrude outer ring
                ringEdge = numEdges() - 2
                length = ((4 * dd / d) / vCount)
                if d < 0.6 * dd:
                    mlva = []
                    lastEdge = numEdges()
                    selEdge(ringEdge - 1)
                    subdiv(randleg)
                    bm.verts.ensure_lookup_table()
                    bm.edges.ensure_lookup_table()
                    lastVert = numVerts()
                    for l in range(randleg):
                        mlva.append(bm.verts[lastVert].index - l)
                    hg = (4 * dd / d) / vCount - len(mlva) * (d / 2)
                    for l in range(len(mlva)):
                        bm.verts.ensure_lookup_table()
                        extLeg(mlva[l], hg, 0)
                        bm.verts.ensure_lookup_table()
                        extLeg(mlva[l], hg, 1)
                        hg = hg + d / 2
                    s3 = 0
                else:
                    s3 = 1
                # Extrude outer ring
                lastEdge = numEdges()
                selEdge(ringEdge)
                subdiv(numRings)
                bm.verts.ensure_lookup_table()
                bm.edges.ensure_lookup_table()
                lastVert = numVerts()
                outerRingLoops = []
                for i in range(numRings):
                    outerRingLoops.append(lastVert - i)
                for j in range(len(outerRingLoops)):
                    selVert(outerRingLoops[j])
                    # extrude and rotate based on rand1 number
                    for i in range(rand1):
                        bm.verts.ensure_lookup_table()
                        extMov(nullV)
                        rotate(angle / rand1)
                    lastVert = numVerts()
                    # if it's the inner ring
                    if j == 0:
                        # select middle vert
                        selVert(lastVert - 1)
                        upVec = Vector((0.0, dd * rando * 2, 0.0))
                        # snap cursor to rotate around the vert
                        bpy.ops.view3d.snap_cursor_to_selected()
                        # extrude and rotate around vert
                        bm.verts.ensure_lookup_table()
                        bm.edges.ensure_lookup_table()
                        extMov(upVec)
                        rotate(angle / 2)
                        bpy.ops.view3d.snap_cursor_to_center()
                        selLasEdge()
                        hg = d / s1
                        if s3 == 0:
                            subdiv(s1)
                            bm.verts.ensure_lookup_table()
                            bm.edges.ensure_lookup_table()
                            lastVert = numVerts()
                            extLeg2(lastVert, hg, angle / 2 + (pi / 4))
                            bm.verts.ensure_lookup_table()
                            bm.edges.ensure_lookup_table()
                            extLeg2(lastVert, hg, angle / 2 - (pi / 4))
                            lastEdge = numEdges()
                            if s1 == 1:
                                if randInternal == 0:
                                    selEdge(lastEdge - 2)
                                else:
                                    selEdge(lastEdge - 3)
                            else:
                                if randInternal == 0:
                                    selEdge(lastEdge - 4)
                                else:
                                    selEdge(lastEdge - 3)
                            subdiv(randleg)
                            bm.verts.ensure_lookup_table()
                            bm.edges.ensure_lookup_table()
                            lastVert = numVerts()
                            mlvb = []
                            for l in range(randleg):
                                bm.verts.ensure_lookup_table()
                                bm.edges.ensure_lookup_table()
                                mlvb.append(bm.verts[lastVert].index - l)
                            randrev = randint(0, 1)
                            if randrev == 1:
                                mlvb.reverse()
                            for l in range(len(mlvb)):
                                hg = hg - (d / (randleg + 1))
                                extLeg2(mlvb[l], hg, (angle / 2) + (pi / 4))
                                extLeg2(mlvb[l], hg, (angle / 2) - (pi / 4))
                    # if it's second ring
                    if j == 1:
                        # select two verts
                        # rest as before except with two legs this time
                        selVert(lastVert - 1)
                        upVec = Vector((0.0, dd * rando * 2, 0.0))
                        bpy.ops.view3d.snap_cursor_to_selected()
                        extMov(upVec)
                        rotate(2 * angle / 3)
                        selVert(lastVert - 2)
                        bpy.ops.view3d.snap_cursor_to_selected()
                        extMov(upVec)
                        rotate(angle / 3)
                        bpy.ops.view3d.snap_cursor_to_center()
                        lasEdg = numEdges()
                        lledg = lasEdg - 1
                        selEdge(lasEdg)
                        subdiv(s2)
                        mlvc = []
                        if s3 == 1:
                            lastVert = numVerts()
                            extLeg2(lastVert, (d / dd) / s1, angle / 3 + (pi / 4))
                            extLeg2(lastVert, (d / dd) / s1, angle / 3 - (pi / 4))
                            lastEdge = numEdges() - 4
                        selEdge(lledg)
                        subdiv(s2)
                        if s3 == 1:
                            lastVert = numVerts()
                            extLeg2(lastVert, (d / dd) / s1, 2 * angle / 3 + (pi / 4))
                            extLeg2(lastVert, (d / dd) / s1, 2 * angle / 3 - (pi / 4))
                            lastEdge = numEdges() - 4
                    rand1 = rand1 + 1
                ##
                #   Select all new verts and duplicate
                ##
                bpy.ops.mesh.select_all(action='SELECT')
                bm.verts.ensure_lookup_table()
                bm.edges.ensure_lookup_table()
                for o in oVerts:
                    bm.verts[o].select = False
                for i in range(vCount - 1):
                    # duplicate around origin
                    dupMove(nullV)
                    rotate(angle)
                    dupVert = []
                    dupEdge = []
                    for v in bm.verts:
                        if v.select:
                            dupVert.append(v.index)
                    for e in bm.edges:
                        if e.select:
                            dupEdge.append(e.index)
                    bpy.ops.mesh.select_all(action='DESELECT')
                    for r in range(len(dupVert)):
                        bm.verts.ensure_lookup_table()
                        bm.edges.ensure_lookup_table()
                        bm.verts[dupVert[r]].select = True
                    for r in range(len(dupEdge)):
                        bm.verts.ensure_lookup_table()
                        bm.edges.ensure_lookup_table()
                        bm.edges[dupEdge[r]].select = True
                ##
                #   Fill center
                ##
                if fillC:
                    selVert(0)
                    for o in oVerts:
                        bm.verts.ensure_lookup_table()
                        bm.edges.ensure_lookup_table()
                        bm.verts[o].select = True
                    extMov(nullV)
                    bpy.ops.view3d.snap_selected_to_cursor(use_offset=False)
                # Remove doubles
                bpy.ops.mesh.select_all(action='SELECT')
                bpy.ops.mesh.remove_doubles()
                bm.verts.ensure_lookup_table()
                bm.edges.ensure_lookup_table()
        return {'FINISHED'}


def menu_func(self, context):
    self.layout.operator(SnowflakeGen.bl_idname, text="Snowflake", icon="PLUGIN")


def register():
    bpy.utils.register_class(SnowflakeGen)
    bpy.types.INFO_MT_mesh_add.append(menu_func)


def unregister():
    bpy.utils.unregister_class(SnowflakeGen)
    bpy.types.INFO_MT_mesh_add.remove(menu_func)

if __name__ == "__main__":
    register()

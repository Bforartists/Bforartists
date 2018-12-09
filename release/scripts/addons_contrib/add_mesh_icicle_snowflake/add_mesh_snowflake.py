bl_info = {
    "name": "Snowflake Generator",
    "author": "Eoin Brennan (Mayeoin Bread)",
    "version": (1, 3, 1),
    "blender": (2, 7, 4),
    "location": "View3D > Add > Mesh",
    "descrition": "Construct a randomly generated snowflake",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Add Mesh"
    }


import bpy
import bmesh
from mathutils import (
        Matrix,
        Vector,
        )
from bpy.types import (
        Operator,
        Menu,
        )
from bpy.props import (
        BoolProperty,
        FloatProperty,
        IntProperty,
        )
from math import (
        pi, sin,
        cos, acos,
        )
from random import (
        randint,
        uniform,
        )
from bl_operators.presets import AddPresetBase


class MESH_MT_snowflakes_presets(Menu):
    '''Presets for mesh.snowflake'''
    bl_label = "Spiral Curve Presets"
    bl_idname = "MESH_MT_snowflakes_presets"
    preset_subdir = "mesh_snowflake_presets/mesh.snowflake"
    preset_operator = "script.execute_preset"

    draw = bpy.types.Menu.draw_preset


class SnowflakeGen_presets(AddPresetBase, Operator):
    bl_idname = "mesh.snowflake_presets"
    bl_label = "Snowflakes"
    bl_description = "Snowflakes Presets"
    preset_menu = "MESH_MT_snowflakes_presets"
    preset_subdir = "mesh_snowflake_presets/mesh.snowflake"

    preset_defines = [
        "op = bpy.context.active_operator",
    ]
    preset_values = [
        "op.rnums",
        "op.randlegs",
        "op.randInternals",
        "op.ds",
        "op.dds",
        "op.randos",
        "op.radius",
        "op.numV",
        "op.fill",
        "op.numR",
        "op.updateS"
    ]


class SnowflakeGen(Operator):
    bl_idname = "mesh.snowflake"
    bl_label = "Snowflake"
    bl_description = ("Construct snowflakes with randomized shapes.\n"
                      "Note: It will replace the existing active Mesh Object")
    bl_options = {"REGISTER", "UNDO"}

    numR = IntProperty(
            name="Outer rings",
            description="Number of outer rings",
            default=1,
            min=0,
            max=4
            )
    rnums = IntProperty(
            name="Random value seed 1",
            default=0,
            min=0,
            max=20,
            options={"HIDDEN"}
            )
    randlegs = IntProperty(
            name="Random value seed 2",
            default=0,
            min=0,
            max=20,
            options={"HIDDEN"}
            )
    randInternals = IntProperty(
            name="Random value seed 3",
            default=0,
            min=0,
            max=20,
            options={"HIDDEN"}
            )
    randos = FloatProperty(
            name="Random seed value 4",
            description="Size of the initial circle",
            min=0.2,
            max=10.0,
            precision=9,
            default=1.0,
            options={"HIDDEN"}
            )
    ds = FloatProperty(
            name="Random seed value 5",
            min=0.2,
            max=10.0,
            precision=9,
            default=1.0,
            options={"HIDDEN"}
            )
    dds = FloatProperty(
            name="Random seed value 6",
            min=0.2,
            max=10.0,
            precision=9,
            default=1.0,
            options={"HIDDEN"}
            )
    radius = FloatProperty(
            name="Base Radius",
            description="Size of the initial circle",
            min=0.1,
            max=3.0,
            precision=4,
            default=1.0
            )
    numV = IntProperty(
            name="Vertices",
            description="Number of vertices around the circle",
            default=6,
            min=3,
            max=24
            )
    fill = BoolProperty(
            name="Fill center",
            description="Connect the inside circle's vertices with the center one",
            default=True
            )
    updateS = BoolProperty(
            name="Update",
            description="Update the shape based on the current settings used as a seed for randomization",
            default=True
            )
    presetS = BoolProperty(
            name="Use preset",
            description="Update the shape based on the preset used as a seed for randomization",
            default=False,
            options={"SKIP_SAVE"}
            )

    def draw(self, context):
        layout = self.layout

        row = layout.row(align=True)
        row.prop(self, "updateS", toggle=True)
        row.prop(self, "presetS", toggle=True)

        if self.presetS:
            row = layout.row(align=True)
            row.menu("MESH_MT_snowflakes_presets")
            row.operator("mesh.snowflake_presets", text="", icon='ZOOMIN')
            row.operator("mesh.snowflake_presets", text="", icon='ZOOMOUT').remove_active = True
        else:
            col = layout.column(align=True)
            col.prop(self, "numR")
            col.prop(self, "radius")

            col.prop(self, "numV")
            col.prop(self, "fill")

    def addMeshObject(self, context):
        old_obj = context.active_object
        if not old_obj or old_obj.type != "MESH":
            bpy.ops.object.add(
                type='MESH', enter_editmode=False,
                view_align=False,
                location=(0.0, 0.0, 0.0),
                rotation=(0.0, 0.0, 0.0)
                )
            context.scene.update()
            obj = context.scene.objects.active
            obj.name = "Snowflake"
            return obj

        return old_obj

    def invoke(self, context, event):
        self.updateS = True
        return self.execute(context)

    def execute(self, context):
        if not self.updateS:
            return {"PASS_THROUGH"}

        bpy.context.space_data.pivot_point = 'CURSOR'
        bpy.ops.view3d.snap_cursor_to_center()

        # --- Nested utility functions START --- #

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

        # --- Nested utility functions END --- #

        obj = None
        obj = self.addMeshObject(context)

        if not obj:
            self.report({'INFO'}, "No Mesh Object found. Operation Cancelled")

            return {"CANCELLED"}

        bpy.ops.object.mode_set(mode="OBJECT")
        bpy.ops.object.mode_set(mode="EDIT")

        me = obj.data
        bm = bmesh.from_edit_mesh(me)
        bm.clear()  # Note: this is important - if not done, causes a memory leak on exit
        bm.verts.ensure_lookup_table()
        bm.edges.ensure_lookup_table()

        # add circle (base for snowflake)
        if bpy.app.version >= (2, 79, 1):
            bmesh.ops.create_circle(
                    bm, cap_ends=False, cap_tris=False, segments=self.numV,
                    radius=self.radius, matrix=Matrix(obj.matrix_world),
                    calc_uvs=False
                    )
        else:
            bmesh.ops.create_circle(
                    bm, cap_ends=False, cap_tris=False, segments=self.numV,
                    diameter=self.radius, matrix=Matrix(obj.matrix_world),
                    calc_uvs=False
                    )

        bm.verts.ensure_lookup_table()
        bm.edges.ensure_lookup_table()

        # variables...
        rnum = randint(0, 1) if not self.presetS else self.rnums
        self.rnums = rnum
        s1, s2 = (1, 2) if rnum == 0 else (2, 1)
        fillC = self.fill
        vCount = 0
        oVerts = []
        rand1 = 2
        rando = uniform(0.2, 1.0) * 2 if not self.presetS else self.randos
        self.randos = rando
        nullV = Vector((0.0, 0.0, 0.0))
        randleg = randint(1, 3) if not self.presetS else self.randlegs
        self.randlegs = randleg
        randInternal = randint(0, randleg) if not self.presetS else self.randInternals
        self.randInternals = randInternal
        numRings = self.numR

        # count + store number of verts in base circle
        oVerts = [v.index for v in bm.verts]
        vCount = len(oVerts)
        oVerts.pop(0)

        # vectors for length of edge and angles
        bm.verts.ensure_lookup_table()
        bm.edges.ensure_lookup_table()
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
        dd = d if not self.presetS else self.dds
        d = d * uniform(0.4, 1.0) if not self.presetS else self.ds
        self.ds = d
        self.dds = dd

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

        # if d < 0.8 * dd, add 1 or two more sets of legs on end

        # Extrude outer ring
        ringEdge = numEdges() - 2

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

        # Select all new verts and duplicate
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

        # Fill center
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
        bpy.ops.mesh.remove_doubles(threshold=0.003)
        bm.verts.ensure_lookup_table()
        bm.edges.ensure_lookup_table()

        bmesh.update_edit_mesh(me, destructive=True)

        self.updateS = False

        return {'FINISHED'}


def menu_func(self, context):
    self.layout.operator(SnowflakeGen.bl_idname, text="Snowflake")


def register():
    bpy.utils.register_class(SnowflakeGen)
    bpy.utils.register_class(MESH_MT_snowflakes_presets)
    bpy.utils.register_class(SnowflakeGen_presets)
    bpy.types.VIEW3D_MT_mesh_add.append(menu_func)


def unregister():
    bpy.utils.unregister_class(SnowflakeGen)
    bpy.utils.unregister_class(MESH_MT_snowflakes_presets)
    bpy.utils.unregister_class(SnowflakeGen_presets)
    bpy.types.VIEW3D_MT_mesh_add.remove(menu_func)


if __name__ == "__main__":
    register()

bl_info = {
    "name": "Icicle Generator",
    "author": "Eoin Brennan (Mayeoin Bread)",
    "version": (2, 2, 1),
    "blender": (2, 7, 4),
    "location": "View3D > Add > Mesh",
    "description": "Construct a linear string of icicles of different sizes",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Add Mesh"
    }

import bpy
import bmesh
from mathutils import Vector
from math import (
        pi, sin,
        cos, atan,
        )
from bpy.props import (
        EnumProperty,
        FloatProperty,
        IntProperty,
        )
import random


class IcicleGenerator(bpy.types.Operator):
    bl_idname = "mesh.icicle_gen"
    bl_label = "Icicle Generator"
    bl_description = ("Create Icicles on selected Edges of an existing Mesh Object\n"
                      "Note: doesn't work with vertical Edges")
    bl_options = {"REGISTER", "UNDO"}

    # Maximum radius
    maxR = FloatProperty(
            name="Max",
            description="Maximum radius of a cone",
            default=0.15,
            min=0.01,
            max=1.0,
            unit="LENGTH"
            )
    # Minimum radius
    minR = FloatProperty(
            name="Min",
            description="Minimum radius of a cone",
            default=0.025,
            min=0.01,
            max=1.0,
            unit="LENGTH"
            )
    # Maximum depth
    maxD = FloatProperty(
            name="Max",
            description="Maximum depth (height) of cone",
            default=2.0,
            min=0.2,
            max=2.0,
            unit="LENGTH"
            )
    # Minimum depth
    minD = FloatProperty(
            name="Min",
            description="Minimum depth (height) of cone",
            default=1.5,
            min=0.2,
            max=2.0,
            unit="LENGTH"
            )
    # Number of verts at base of cone
    verts = IntProperty(
            name="Vertices",
            description="Number of vertices at the icicle base",
            default=8,
            min=3,
            max=24
            )
    addCap = EnumProperty(
            name="Fill cap",
            description="Fill the icicle cone base",
            items=[
                ('NGON', "Ngon", "Fill with Ngons"),
                ('NOTHING', "None", "Do not fill"),
                ('TRIFAN', "Triangle fan", "Fill with triangles")
            ],
            default='NGON',
            )
    # Number of iterations before giving up trying to add cones
    # Prevents crashes and freezes
    # Obviously, the more iterations, the more time spent calculating.
    # Max value (10,000) is safe but can be slow,
    # 2000 to 5000 should be adequate for 95% of cases
    its = IntProperty(
            name="Iterations",
            description="Number of iterations before giving up, prevents freezing/crashing",
            default=2000,
            min=1,
            max=10000
            )
    verticalEdges = False

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and obj.type == "MESH"

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)

        col.label("Radius:")
        col.prop(self, "minR")
        col.prop(self, "maxR")

        col.label("Depth:")
        col.prop(self, "minD")
        col.prop(self, "maxD")

        col.label("Base:")
        col.prop(self, "verts")
        col.prop(self, "addCap", text="")

        layout.prop(self, "its")

    def execute(self, context):
        # Variables
        if self.minR > self.maxR:
            self.maxR = self.minR

        if self.minD > self.maxD:
            self.maxD = self.minD

        rad = self.maxR
        radM = self.minR
        depth = self.maxD
        minD = self.minD
        addCap = self.addCap
        self.verticalEdges = False

        # --- Nested utility functions START --- #

        def test_data(obj):
            me = obj.data
            is_edges = bool(len(me.edges) > 0)
            is_selected = False

            for edge in me.edges:
                if edge.select:
                    is_selected = True
                    break

            return (is_edges and is_selected)

        def flip_to_edit_mode():
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.mode_set(mode='EDIT')

        # Add cone function
        def add_cone(x, y, z, randrad, rd, fill="NGON"):
            bpy.ops.mesh.primitive_cone_add(
                    vertices=self.verts,
                    radius1=randrad,
                    radius2=0.0,
                    depth=rd,
                    end_fill_type=fill,
                    view_align=False,
                    location=(x, y, z),
                    rotation=(pi, 0.0, 0.0)
                    )

        # Add icicle function
        def add_icicles(rad, radM, depth, minD):
            pos1 = Vector((0.0, 0.0, 0.0))
            pos2 = Vector((0.0, 0.0, 0.0))
            pos = 0
            obj = bpy.context.active_object
            bm = bmesh.from_edit_mesh(obj.data)
            wm = obj.matrix_world

            # Vectors for selected verts
            for v in bm.verts:
                if v.select:
                    if pos == 0:
                        p1 = v.co
                        pos = 1
                    elif pos == 1:
                        p2 = v.co
                        pos = 2

            # Set first to left most vert on X-axis...
            if(p1.x > p2.x):
                pos1 = p2
                pos2 = p1
            # Or bottom-most on Y-axis if X-axis not used
            elif(p1.x == p2.x):
                if(p1.y > p2.y):
                    pos1 = p2
                    pos2 = p1
                else:
                    pos1 = p1
                    pos2 = p2
            else:
                pos1 = p1
                pos2 = p2
            # World matrix for positioning
            pos1 = pos1 * wm
            pos2 = pos2 * wm

            # X values not equal, working on X-Y-Z planes
            if pos1.x != pos2.x:
                # Get the angle of the line
                if (pos2.y != pos1.y):
                    angle = atan((pos2.x - pos1.x) / (pos2.y - pos1.y))
                else:
                    angle = pi / 2
                # Total length of line, neglect Z-value (Z only affects height)
                xLength = (((pos2.x - pos1.x)**2) + ((pos2.y - pos1.y)**2))**0.5
                # Slopes if lines
                zSlope = (pos2.z - pos1.z) / (pos2.x - pos1.x)

                # Fixes positioning error with some angles
                if (angle < 0):
                    i = pos2.x
                    j = pos2.y
                    k = pos2.z
                else:
                    i = pos1.x
                    j = pos1.y
                    k = pos1.z
                l = 0.0

                # Z axis' intercept
                zInt = k - (zSlope * i)

                # if equal values, radius should be that size otherwise randomize it
                randrad = rad if (radM == rad) else (rad - radM) * random.random()

                # Depth, as with radius above
                rd = depth if (depth == minD) else (depth - minD) * random.random()

                # Get user iterations
                iterations = self.its
                # Counter for iterations
                c = 0
                while (l < xLength) and (c < iterations):
                    rr = randrad if (radM == rad) else randrad + radM
                    dd = rd if (depth == minD) else rd + minD

                    # Icicles generally taller than wider, check if true
                    if (dd > rr):
                        # If the new icicle won't exceed line length
                        # Fix for overshooting lines
                        if (l + rr + rr <= xLength):
                            # Using sine/cosine of angle keeps icicles consistently spaced
                            i = i + (rr) * sin(angle)
                            j = j + (rr) * cos(angle)
                            l = l + rr

                            # Add a cone in new position
                            add_cone(i, j, (i * zSlope) + (zInt - (dd) / 2), rr, dd, addCap)

                            # Add another radius to i and j to prevent overlap
                            i = i + (rr) * sin(angle)
                            j = j + (rr) * cos(angle)
                            l = l + rr

                            # New values for rad and depth
                            randrad = rad if (radM == rad) else (rad - radM) * random.random()
                            rd = depth if (depth == minD) else (depth - minD) * random.random()

                        # If overshoot, try find smaller cone
                        else:
                            randrad = rad if (radM == rad) else (rad - radM) * random.random()
                            rd = depth if (depth == minD) else (depth - minD) * random.random()

                    # If wider than taller, try find taller than wider
                    else:
                        randrad = rad if (radM == rad) else (rad - radM) * random.random()
                        rd = depth if (depth == minD) else (depth - minD) * random.random()

                    # Increase iterations by 1
                    c = c + 1

            # If X values equal, then just working in Y-Z plane,
            # Provided Y values not equal
            elif (pos1.x == pos2.x) and (pos1.y != pos2.y):
                # Absolute length of Y line
                xLength = ((pos2.y - pos1.y)**2)**0.5
                i = pos1.x
                j = pos1.y
                k = pos1.z
                l = 0.0
                # Z-slope and intercept
                zSlope = (pos2.z - pos1.z) / (pos2.y - pos1.y)
                zInt = k - (zSlope * j)

                # Same as above for X-Y-Z plane, just X values don't change
                randrad = rad if (radM == rad) else (rad - radM) * random.random()
                rd = depth if (depth == minD) else (depth - minD) * random.random()

                iterations = self.its
                c = 0
                while(l < xLength) and (c < iterations):
                    rr = randrad if (radM == rad) else randrad + radM
                    dd = rd if (depth == minD) else rd + minD

                    if (dd > rr):
                        if (l + rr + rr <= xLength):
                            j = j + (rr)
                            l = l + (rr)

                            add_cone(i, j, (i * zSlope) + (zInt - (dd) / 2), rr, dd, addCap)

                            j = j + (rr)
                            l = l + (rr)

                            randrad = rad if (radM == rad) else (rad - radM) * random.random()
                            rd = depth if (depth == minD) else (depth - minD) * random.random()

                        else:
                            randrad = rad if (radM == rad) else (rad - radM) * random.random()
                            rd = depth if (depth == minD) else (depth - minD) * random.random()
                    else:
                        randrad = rad if (radM == rad) else (rad - radM) * random.random()
                        rd = depth if (depth == minD) else (depth - minD) * random.random()

                    c = c + 1
            else:
                # Otherwise X and Y values the same, so either verts are on top of each other
                # Or its a vertical line. Either way, we don't like it
                self.verticalEdges = True

        # Run function
        def runIt(rad, radM, depth, minD):
            # Check that min values are less than max values
            if not((rad >= radM) and (depth >= minD)):
                return False

            obj = bpy.context.active_object
            if obj.mode == 'EDIT':
                # List of initial edges
                oEdge = []
                bm = bmesh.from_edit_mesh(obj.data)
                bm.edges.ensure_lookup_table()

                for e in bm.edges:
                    if e.select:
                        # Append selected edges to list
                        oEdge.append(e.index)

                # For every initially selected edge, add cones
                for e in oEdge:
                    bpy.ops.mesh.select_all(action='DESELECT')
                    bm.edges.ensure_lookup_table()
                    bm.edges[e].select = True
                    add_icicles(rad, radM, depth, minD)
                return True

            return False

        # --- Nested utility functions END --- #

        # Run the function
        obj = context.active_object

        if obj and obj.type == 'MESH':
            flip_to_edit_mode()
            if not test_data(obj):
                self.report({'INFO'},
                            "Active Mesh has to have at least one selected Edge. Operation Cancelled")
                return {"CANCELLED"}

            check = runIt(rad, radM, depth, minD)

            if check is False:
                self.report({'INFO'}, "Operation could not be completed")

            if self.verticalEdges:
                self.report({'INFO'},
                            "Some selected vertical Edges were skipped during icicles creation")

        return {'FINISHED'}


# Add to menu and register/unregister stuff
def menu_func(self, context):
    self.layout.operator(IcicleGenerator.bl_idname, text="Icicle")


def register():
    bpy.utils.register_class(IcicleGenerator)
    bpy.types.VIEW3D_MT_mesh_add.append(menu_func)


def unregister():
    bpy.utils.unregister_class(IcicleGenerator)
    bpy.types.VIEW3D_MT_mesh_add.remove(menu_func)


if __name__ == "__main__":
    register()

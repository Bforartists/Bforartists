# SPDX-FileCopyrightText: 2010-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

bl_info = {
    "name": "Simplify Curves+",
    "author": "testscreenings, Michael Soluyanov",
    "version": (1, 1, 2),
    "blender": (2, 80, 0),
    "location": "3D View, Dopesheet & Graph Editors",
    "description": "Simplify Curves: 3dview, Dopesheet, Graph. Distance Merge: 3d view curve edit",
    "warning": "",
    "doc_url": "{BLENDER_MANUAL_URL}/addons/add_curve/simplify_curves.html",
    "category": "Add Curve",
}

"""
This script simplifies Curve objects and animation F-Curves
This script will also Merge by Distance 3d view curves in edit mode
"""

import bpy
from bpy.props import (
    BoolProperty,
    EnumProperty,
    FloatProperty,
    IntProperty,
)
import mathutils
from math import (
    sin,
    pow,
)
from bpy.types import Operator


def error_handlers(self, op_name, errors, reports="ERROR"):
    if self and reports:
        self.report({'INFO'},
                    reports + ": some operations could not be performed "
                    "(See Console for more info)")

    print("\n[Simplify Curves]\nOperator: {}\nErrors: {}\n".format(op_name, errors))


# Check for curve

# ### simplipoly algorithm ###

# get SplineVertIndices to keep
def simplypoly(splineVerts, options):
    # main vars
    newVerts = []           # list of vertindices to keep
    points = splineVerts    # list of 3dVectors
    pointCurva = []         # table with curvatures
    curvatures = []         # averaged curvatures per vert
    for p in points:
        pointCurva.append([])
    order = options[3]      # order of sliding beziercurves
    k_thresh = options[2]   # curvature threshold
    dis_error = options[6]  # additional distance error

    # get curvatures per vert
    for i, point in enumerate(points[: -(order - 1)]):
        BVerts = points[i: i + order]
        for b, BVert in enumerate(BVerts[1: -1]):
            deriv1 = getDerivative(BVerts, 1 / (order - 1), order - 1)
            deriv2 = getDerivative(BVerts, 1 / (order - 1), order - 2)
            curva = getCurvature(deriv1, deriv2)
            pointCurva[i + b + 1].append(curva)

    # average the curvatures
    for i in range(len(points)):
        avgCurva = sum(pointCurva[i]) / (order - 1)
        curvatures.append(avgCurva)

    # get distancevalues per vert - same as Ramer-Douglas-Peucker
    # but for every vert
    distances = [0.0]  # first vert is always kept
    for i, point in enumerate(points[1: -1]):
        dist = altitude(points[i], points[i + 2], points[i + 1])
        distances.append(dist)
    distances.append(0.0)  # last vert is always kept

    # generate list of vert indices to keep
    # tested against averaged curvatures and distances of neighbour verts
    newVerts.append(0)  # first vert is always kept
    for i, curv in enumerate(curvatures):
        if (curv >= k_thresh * 0.01 or distances[i] >= dis_error * 0.1):
            newVerts.append(i)
    newVerts.append(len(curvatures) - 1)  # last vert is always kept

    return newVerts


# get binomial coefficient
def binom(n, m):
    b = [0] * (n + 1)
    b[0] = 1
    for i in range(1, n + 1):
        b[i] = 1
        j = i - 1
        while j > 0:
            b[j] += b[j - 1]
            j -= 1
    return b[m]


# get nth derivative of order(len(verts)) bezier curve
def getDerivative(verts, t, nth):
    order = len(verts) - 1 - nth
    QVerts = []

    if nth:
        for i in range(nth):
            if QVerts:
                verts = QVerts
            derivVerts = []
            for i in range(len(verts) - 1):
                derivVerts.append(verts[i + 1] - verts[i])
            QVerts = derivVerts
    else:
        QVerts = verts

    if len(verts[0]) == 3:
        point = Vector((0, 0, 0))
    if len(verts[0]) == 2:
        point = Vector((0, 0))

    for i, vert in enumerate(QVerts):
        point += binom(order, i) * pow(t, i) * pow(1 - t, order - i) * vert
    deriv = point

    return deriv


# get curvature from first, second derivative
def getCurvature(deriv1, deriv2):
    if deriv1.length == 0:  # in case of points in straight line
        curvature = 0
        return curvature
    curvature = (deriv1.cross(deriv2)).length / pow(deriv1.length, 3)
    return curvature


# ### Ramer-Douglas-Peucker algorithm ###

# get altitude of vert
def altitude(point1, point2, pointn):
    edge1 = point2 - point1
    edge2 = pointn - point1
    if edge2.length == 0:
        altitude = 0
        return altitude
    if edge1.length == 0:
        altitude = edge2.length
        return altitude
    alpha = edge1.angle(edge2)
    altitude = sin(alpha) * edge2.length
    return altitude


# iterate through verts
def iterate(points, newVerts, error):
    new = []
    for newIndex in range(len(newVerts) - 1):
        bigVert = 0
        alti_store = 0
        for i, point in enumerate(points[newVerts[newIndex] + 1: newVerts[newIndex + 1]]):
            alti = altitude(points[newVerts[newIndex]], points[newVerts[newIndex + 1]], point)
            if alti > alti_store:
                alti_store = alti
                if alti_store >= error:
                    bigVert = i + 1 + newVerts[newIndex]
        if bigVert:
            new.append(bigVert)
    if new == []:
        return False
    return new


# get SplineVertIndices to keep
def simplify_RDP(splineVerts, options):
    # main vars
    error = options[4]

    # set first and last vert
    newVerts = [0, len(splineVerts) - 1]

    # iterate through the points
    new = 1
    while new is not False:
        new = iterate(splineVerts, newVerts, error)
        if new:
            newVerts += new
            newVerts.sort()
    return newVerts


# ### CURVE GENERATION ###

# set bezierhandles to auto
def setBezierHandles(newCurve):
    # Faster:
    for spline in newCurve.data.splines:
        for p in spline.bezier_points:
            p.handle_left_type = 'AUTO'
            p.handle_right_type = 'AUTO'


# get array of new coords for new spline from vertindices
def vertsToPoints(newVerts, splineVerts, splineType):
    # main vars
    newPoints = []

    # array for BEZIER spline output
    if splineType == 'BEZIER':
        for v in newVerts:
            newPoints += splineVerts[v].to_tuple()

    # array for nonBEZIER output
    else:
        for v in newVerts:
            newPoints += (splineVerts[v].to_tuple())
            if splineType == 'NURBS':
                newPoints.append(1)  # for nurbs w = 1
            else:                    # for poly w = 0
                newPoints.append(0)
    return newPoints


# ### MAIN OPERATIONS ###

def main(context, obj, options, curve_dimension):
    mode = options[0]
    output = options[1]
    degreeOut = options[5]
    keepShort = options[7]
    bpy.ops.object.select_all(action='DESELECT')
    scene = context.scene
    splines = obj.data.splines.values()

    # create curvedatablock
    curve = bpy.data.curves.new("Simple_" + obj.name, type='CURVE')
    curve.dimensions = curve_dimension

    # go through splines
    for spline_i, spline in enumerate(splines):
        # test if spline is a long enough
        if len(spline.points) >= 3 or keepShort:
            # check what type of spline to create
            if output == 'INPUT':
                splineType = spline.type
            else:
                splineType = output

            # get vec3 list to simplify
            if spline.type == 'BEZIER':  # get bezierverts
                splineVerts = [splineVert.co.copy()
                               for splineVert in spline.bezier_points.values()]

            else:  # verts from all other types of curves
                splineVerts = [splineVert.co.to_3d()
                               for splineVert in spline.points.values()]

            # simplify spline according to mode
            if mode == 'DISTANCE':
                newVerts = simplify_RDP(splineVerts, options)

            if mode == 'CURVATURE':
                newVerts = simplypoly(splineVerts, options)

            # convert indices into vectors3D
            newPoints = vertsToPoints(newVerts, splineVerts, splineType)

            # create new spline
            newSpline = curve.splines.new(type=splineType)

            # put newPoints into spline according to type
            if splineType == 'BEZIER':
                newSpline.bezier_points.add(int(len(newPoints) * 0.33))
                newSpline.bezier_points.foreach_set('co', newPoints)
            else:
                newSpline.points.add(int(len(newPoints) * 0.25 - 1))
                newSpline.points.foreach_set('co', newPoints)

            # set degree of outputNurbsCurve
            if output == 'NURBS':
                newSpline.order_u = degreeOut

            # splineoptions
            newSpline.use_endpoint_u = spline.use_endpoint_u

    # create new object and put into scene
    newCurve = bpy.data.objects.new("Simple_" + obj.name, curve)
    coll = context.view_layer.active_layer_collection.collection
    coll.objects.link(newCurve)
    newCurve.select_set(True)

    context.view_layer.objects.active = newCurve
    newCurve.matrix_world = obj.matrix_world

    # set bezierhandles to auto
    setBezierHandles(newCurve)

    return


# get preoperator fcurves
def getFcurveData(obj):
    fcurves = []
    for fc in obj.animation_data.action.fcurves:
        if fc.select:
            fcVerts = [vcVert.co.to_3d()
                       for vcVert in fc.keyframe_points.values()]
            fcurves.append(fcVerts)
    return fcurves


def selectedfcurves(obj):
    fcurves_sel = []
    for i, fc in enumerate(obj.animation_data.action.fcurves):
        if fc.select:
            fcurves_sel.append(fc)
    return fcurves_sel


# fCurves Main
def fcurves_simplify(context, obj, options, fcurves):
    # main vars
    mode = options[0]

    # get indices of selected fcurves
    fcurve_sel = selectedfcurves(obj)

    # go through fcurves
    for fcurve_i, fcurve in enumerate(fcurves):
        # test if fcurve is long enough
        if len(fcurve) >= 3:
            # simplify spline according to mode
            if mode == 'DISTANCE':
                newVerts = simplify_RDP(fcurve, options)

            if mode == 'CURVATURE':
                newVerts = simplypoly(fcurve, options)

            # convert indices into vectors3D
            newPoints = []

            # this is different from the main() function for normal curves, different api...
            for v in newVerts:
                newPoints.append(fcurve[v])

            # remove all points from curve first
            for i in range(len(fcurve) - 1, 0, -1):
                fcurve_sel[fcurve_i].keyframe_points.remove(fcurve_sel[fcurve_i].keyframe_points[i])
            # put newPoints into fcurve
            for v in newPoints:
                fcurve_sel[fcurve_i].keyframe_points.insert(frame=v[0], value=v[1])
    return


# ### MENU append ###

def menu_func(self, context):
    self.layout.operator("graph.simplify")


def menu(self, context):
    self.layout.operator("curve.simplify", text="Curve Simplify", icon="CURVE_DATA")



# ### ANIMATION CURVES OPERATOR ###

class GRAPH_OT_simplify(Operator):
    bl_idname = "graph.simplify"
    bl_label = "Simplify F-Curves"
    bl_description = ("Simplify selected Curves\n"
                      "Does not operate on short Splines (less than 3 points)")
    bl_options = {'REGISTER', 'UNDO'}

    # Properties
    opModes = [
            ('DISTANCE', 'Distance', 'Distance-based simplification (Poly)'),
            ('CURVATURE', 'Curvature', 'Curvature-based simplification (RDP)')]
    mode: EnumProperty(
            name="Mode",
            description="Choose algorithm to use",
            items=opModes
            )
    k_thresh: FloatProperty(
            name="k",
            min=0, soft_min=0,
            default=0, precision=5,
            description="Threshold"
            )
    pointsNr: IntProperty(
            name="n",
            min=5, soft_min=5,
            max=16, soft_max=9,
            default=5,
            description="Degree of curve to get averaged curvatures"
            )
    error: FloatProperty(
            name="Error",
            description="Maximum allowed distance error",
            min=0.0, soft_min=0.0,
            default=0, precision=5,
            step = 0.1
            )
    degreeOut: IntProperty(
            name="Degree",
            min=3, soft_min=3,
            max=7, soft_max=7,
            default=5,
            description="Degree of new curve"
            )
    dis_error: FloatProperty(
            name="Distance error",
            description="Maximum allowed distance error in Blender Units",
            min=0, soft_min=0,
            default=0.0, precision=5
            )
    fcurves = []

    def draw(self, context):
        layout = self.layout
        col = layout.column()

        col.label(text="Distance Error:")
        col.prop(self, "error", expand=True)

    @classmethod
    def poll(cls, context):
        # Check for animdata
        obj = context.active_object
        fcurves = False
        if obj:
            animdata = obj.animation_data
            if animdata:
                act = animdata.action
                if act:
                    fcurves = act.fcurves
        return (obj and fcurves)

    def execute(self, context):
        options = [
                self.mode,       # 0
                self.mode,       # 1
                self.k_thresh,   # 2
                self.pointsNr,   # 3
                self.error,      # 4
                self.degreeOut,  # 6
                self.dis_error   # 7
                ]

        obj = context.active_object

        if not self.fcurves:
            self.fcurves = getFcurveData(obj)

        fcurves_simplify(context, obj, options, self.fcurves)

        return {'FINISHED'}


# ### Curves OPERATOR ###
class CURVE_OT_simplify(Operator):
    bl_idname = "curve.simplify"
    bl_label = "Simplify Curves"
    bl_description = ("Simplify the existing Curve based upon the chosen settings\n"
                      "Notes: Needs an existing Curve object,\n"
                      "Outputs a new Curve with the Simple prefix in the name")
    bl_options = {'REGISTER', 'UNDO'}

    # Properties
    opModes = [
            ('DISTANCE', 'Distance', 'Distance-based simplification (Poly)'),
            ('CURVATURE', 'Curvature', 'Curvature-based simplification (RDP)')
            ]
    mode: EnumProperty(
            name="Mode",
            description="Choose algorithm to use",
            items=opModes
            )
    SplineTypes = [
            ('INPUT', 'Input', 'Same type as input spline'),
            ('NURBS', 'Nurbs', 'NURBS'),
            ('BEZIER', 'Bezier', 'BEZIER'),
            ('POLY', 'Poly', 'POLY')
            ]
    output: EnumProperty(
            name="Output splines",
            description="Type of splines to output",
            items=SplineTypes
            )
    k_thresh: FloatProperty(
            name="k",
            min=0, soft_min=0,
            default=0, precision=5,
            description="Threshold"
            )
    pointsNr: IntProperty(
            name="n",
            min=5, soft_min=5,
            max=9, soft_max=9,
            default=5,
            description="Degree of curve to get averaged curvatures"
            )
    error: FloatProperty(
            name="Error",
            description="Maximum allowed distance error in Blender Units",
            min=0, soft_min=0,
            default=0.0, precision=5,
            step = 0.1
            )
    degreeOut: IntProperty(
            name="Degree",
            min=3, soft_min=3,
            max=7, soft_max=7,
            default=5,
            description="Degree of new curve"
            )
    dis_error: FloatProperty(
            name="Distance error",
            description="Maximum allowed distance error in Blender Units",
            min=0, soft_min=0,
            default=0.0
            )
    keepShort: BoolProperty(
            name="Keep short splines",
            description="Keep short splines (less than 3 points)",
            default=True
            )

    def draw(self, context):
        layout = self.layout
        col = layout.column()

        col.label(text="Distance Error:")
        col.prop(self, "error", expand=True)
        col.prop(self, "output", text="Output", icon="OUTLINER_OB_CURVE")
        if self.output == "NURBS":
            col.prop(self, "degreeOut", expand=True)
        col.separator()
        col.prop(self, "keepShort", expand=True)

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj and obj.type == 'CURVE')

    def execute(self, context):
        options = [
                self.mode,       # 0
                self.output,     # 1
                self.k_thresh,   # 2
                self.pointsNr,   # 3
                self.error,      # 4
                self.degreeOut,  # 5
                self.dis_error,  # 6
                self.keepShort   # 7
                ]
        try:
            bpy.ops.object.mode_set(mode='OBJECT')
            obj = context.active_object
            curve_dimension = obj.data.dimensions

            main(context, obj, options, curve_dimension)
        except Exception as e:
            error_handlers(self, "curve.simplify", e, "Simplify Curves")
            return {'CANCELLED'}

        return {'FINISHED'}

## Initial use Curve Remove Doubles ##

def main_rd(context, distance = 0.01):

    selected_Curves = context.selected_objects
    if bpy.ops.object.mode_set.poll():
        bpy.ops.object.mode_set(mode='EDIT')

    bezier_dellist = []
    dellist = []

    for curve in selected_Curves:
        for spline in curve.data.splines:
            if spline.type == 'BEZIER':
                if len(spline.bezier_points) > 1:
                    for i in range(0, len(spline.bezier_points)):

                        if i == 0:
                            ii = len(spline.bezier_points) - 1
                        else:
                            ii = i - 1

                        dot = spline.bezier_points[i];
                        dot1 = spline.bezier_points[ii];

                        while dot1 in bezier_dellist and i != ii:
                            ii -= 1
                            if ii < 0:
                                ii = len(spline.bezier_points)-1
                            dot1 = spline.bezier_points[ii]

                        if dot.select_control_point and dot1.select_control_point and (i!=0 or spline.use_cyclic_u):

                            if (dot.co-dot1.co).length < distance:
                                # remove points and recreate hangles
                                dot1.handle_right_type = "FREE"
                                dot1.handle_right = dot.handle_right
                                dot1.co = (dot.co + dot1.co) / 2
                                bezier_dellist.append(dot)

                            else:
                                # Handles that are on main point position converts to vector,
                                # if next handle are also vector
                                if dot.handle_left_type == 'VECTOR' and (dot1.handle_right - dot1.co).length < distance:
                                    dot1.handle_right_type = "VECTOR"
                                if dot1.handle_right_type == 'VECTOR' and (dot.handle_left - dot.co).length < distance:
                                    dot.handle_left_type = "VECTOR"
            else:
                if len(spline.points) > 1:
                    for i in range(0, len(spline.points)):

                        if i == 0:
                            ii = len(spline.points) - 1
                        else:
                            ii = i - 1

                        dot = spline.points[i];
                        dot1 = spline.points[ii];

                        while dot1 in dellist and i != ii:
                            ii -= 1
                            if ii < 0:
                                ii = len(spline.points)-1
                            dot1 = spline.points[ii]

                        if dot.select and dot1.select and (i!=0 or spline.use_cyclic_u):

                            if (dot.co-dot1.co).length < distance:
                                dot1.co = (dot.co + dot1.co) / 2
                                dellist.append(dot)

    bpy.ops.curve.select_all(action = 'DESELECT')

    for dot in bezier_dellist:
        dot.select_control_point = True

    for dot in dellist:
        dot.select = True

    bezier_count = len(bezier_dellist)
    count = len(dellist)

    bpy.ops.curve.delete(type = 'VERT')

    bpy.ops.curve.select_all(action = 'DESELECT')

    return bezier_count + count



class Curve_OT_CurveRemvDbs(bpy.types.Operator):
    """Merge consecutive points that are near to each other"""
    bl_idname = 'curve.remove_double'
    bl_label = 'Merge By Distance'
    bl_options = {'REGISTER', 'UNDO'}

    distance: bpy.props.FloatProperty(name = 'Distance', default = 0.01, soft_min = 0.001, step = 0.1)

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj and obj.type == 'CURVE')

    def execute(self, context):
        removed=main_rd(context, self.distance)
        self.report({'INFO'}, "Removed %d bezier points" % removed)
        return {'FINISHED'}

def menu_func_rd(self, context):
    self.layout.operator(Curve_OT_CurveRemvDbs.bl_idname, text='Merge By Distance')

# Register
classes = [
    GRAPH_OT_simplify,
    CURVE_OT_simplify,
    Curve_OT_CurveRemvDbs,
]


def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

    #bpy.types.GRAPH_MT_channel.append(menu_func)
    #bpy.types.DOPESHEET_MT_channel.append(menu_func)
    bpy.types.VIEW3D_MT_curve_add.append(menu)
    bpy.types.VIEW3D_MT_edit_curve_context_menu.prepend(menu)
    bpy.types.VIEW3D_MT_edit_curve_context_menu.prepend(menu_func_rd)


def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)

    #bpy.types.GRAPH_MT_channel.remove(menu_func)
    #bpy.types.DOPESHEET_MT_channel.remove(menu_func)
    bpy.types.VIEW3D_MT_curve_add.remove(menu)
    bpy.types.VIEW3D_MT_edit_curve_context_menu.remove(menu)
    bpy.types.VIEW3D_MT_edit_curve_context_menu.remove(menu_func_rd)

if __name__ == "__main__":
    register()

# SPDX-FileCopyrightText: 2019-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

import time
import threading

import bpy
from bpy.props import *
from bpy_extras import object_utils, view3d_utils
from mathutils import  *
from math import  *

from . import properties
from . import curves
from . import intersections
from . import util
from . import surfaces
from . import mathematics
from . import internal

# 1 CURVE SELECTED
# ################
class OperatorCurveInfo(bpy.types.Operator):
    bl_idname = "curvetools.operatorcurveinfo"
    bl_label = "Info"
    bl_description = "Displays general info about the active/selected curve"


    @classmethod
    def poll(cls, context):
        return util.Selected1Curve()


    def execute(self, context):
        curve = curves.Curve(context.active_object)

        nrSplines = len(curve.splines)
        nrSegments = 0
        nrEmptySplines = 0
        for spline in curve.splines:
            nrSegments += spline.nrSegments
            if spline.nrSegments < 1: nrEmptySplines += 1


        self.report({'INFO'}, "nrSplines: %d; nrSegments: %d; nrEmptySplines: %d" % (nrSplines, nrSegments, nrEmptySplines))

        return {'FINISHED'}



class OperatorCurveLength(bpy.types.Operator):
    bl_idname = "curvetools.operatorcurvelength"
    bl_label = "Length"
    bl_description = "Calculates the length of the active/selected curve"


    @classmethod
    def poll(cls, context):
        return util.Selected1Curve()


    def execute(self, context):
        curve = curves.Curve(context.active_object)

        context.scene.curvetools.CurveLength = curve.length

        return {'FINISHED'}



class OperatorSplinesInfo(bpy.types.Operator):
    bl_idname = "curvetools.operatorsplinesinfo"
    bl_label = "Info"
    bl_description = "Displays general info about the splines of the active/selected curve"


    @classmethod
    def poll(cls, context):
        return util.Selected1Curve()


    def execute(self, context):
        curve = curves.Curve(context.active_object)
        nrSplines = len(curve.splines)

        print("")
        print("OperatorSplinesInfo:", "nrSplines:", nrSplines)

        nrEmptySplines = 0
        for iSpline, spline in enumerate(curve.splines):
            print("--", "spline %d of %d: nrSegments: %d" % (iSpline + 1, nrSplines, spline.nrSegments))

            if spline.nrSegments < 1:
                nrEmptySplines += 1
                print("--", "--", "## WARNING: spline has no segments and will therefor be ignored in any further calculations")


        self.report({'INFO'}, "nrSplines: %d; nrEmptySplines: %d" % (nrSplines, nrEmptySplines) + " -- more info: see console")

        return {'FINISHED'}



class OperatorSegmentsInfo(bpy.types.Operator):
    bl_idname = "curvetools.operatorsegmentsinfo"
    bl_label = "Info"
    bl_description = "Displays general info about the segments of the active/selected curve"


    @classmethod
    def poll(cls, context):
        return util.Selected1Curve()


    def execute(self, context):
        curve = curves.Curve(context.active_object)
        nrSplines = len(curve.splines)
        nrSegments = 0

        print("")
        print("OperatorSegmentsInfo:", "nrSplines:", nrSplines)

        nrEmptySplines = 0
        for iSpline, spline in enumerate(curve.splines):
            nrSegmentsSpline = spline.nrSegments
            print("--", "spline %d of %d: nrSegments: %d" % (iSpline + 1, nrSplines, nrSegmentsSpline))

            if nrSegmentsSpline < 1:
                nrEmptySplines += 1
                print("--", "--", "## WARNING: spline has no segments and will therefor be ignored in any further calculations")
                continue

            for iSegment, segment in enumerate(spline.segments):
                print("--", "--", "segment %d of %d coefficients:" % (iSegment + 1, nrSegmentsSpline))
                print("--", "--", "--", "C0: %.6f, %.6f, %.6f" % (segment.coeff0.x, segment.coeff0.y, segment.coeff0.z))

            nrSegments += nrSegmentsSpline

        self.report({'INFO'}, "nrSplines: %d; nrSegments: %d; nrEmptySplines: %d" % (nrSplines, nrSegments, nrEmptySplines))

        return {'FINISHED'}



class OperatorOriginToSpline0Start(bpy.types.Operator):
    bl_idname = "curvetools.operatororigintospline0start"
    bl_label = "OriginToSpline0Start"
    bl_description = "Sets the origin of the active/selected curve to the starting point of the (first) spline. Nice for curve modifiers"
    bl_options = {'UNDO'}


    @classmethod
    def poll(cls, context):
        return util.Selected1Curve()


    def execute(self, context):


        blCurve = context.active_object
        blSpline = blCurve.data.splines[0]
        newOrigin = blCurve.matrix_world @ blSpline.bezier_points[0].co

        origOrigin = bpy.context.scene.cursor.location.copy()
        self.report({'INFO'}, "origOrigin: %.6f, %.6f, %.6f" % (origOrigin.x, origOrigin.y, origOrigin.z))
        self.report({'INFO'}, "newOrigin: %.6f, %.6f, %.6f" % (newOrigin.x, newOrigin.y, newOrigin.z))

        current_mode = bpy.context.object.mode

        bpy.ops.object.mode_set(mode = 'OBJECT')
        bpy.context.scene.cursor.location = newOrigin
        bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
        bpy.context.scene.cursor.location = origOrigin

        bpy.ops.object.mode_set (mode = current_mode)

        return {'FINISHED'}



# 2 CURVES SELECTED
# #################
class OperatorIntersectCurves(bpy.types.Operator):
    bl_idname = "curvetools.operatorintersectcurves"
    bl_label = "Intersect"
    bl_description = "Intersects selected curves"
    bl_options = {'UNDO'}


    @classmethod
    def poll(cls, context):
        return util.Selected2OrMoreCurves()


    def execute(self, context):
        print("### TODO: OperatorIntersectcurves.execute()")

        algo = context.scene.curvetools.IntersectCurvesAlgorithm
        print("-- algo:", algo)


        mode = context.scene.curvetools.IntersectCurvesMode
        print("-- mode:", mode)
        # if mode == 'Split':
            # self.report({'WARNING'}, "'Split' mode is not implemented yet -- <<STOPPING>>")
            # return {'CANCELLED'}

        affect = context.scene.curvetools.IntersectCurvesAffect
        print("-- affect:", affect)

        selected_objects = context.selected_objects
        lenodjs = len(selected_objects)
        print('lenodjs:', lenodjs)
        for i in range(0, lenodjs):
            for j in range(0, lenodjs):
                if j != i:
                    bpy.ops.object.select_all(action='DESELECT')
                    selected_objects[i].select_set(True)
                    selected_objects[j].select_set(True)

                    if selected_objects[i].type == 'CURVE' and selected_objects[j].type == 'CURVE':
                        curveIntersector = intersections.CurvesIntersector.FromSelection()
                        rvIntersectionNrs = curveIntersector.CalcAndApplyIntersections()

                        self.report({'INFO'}, "Active curve points: %d; other curve points: %d" % (rvIntersectionNrs[0], rvIntersectionNrs[1]))

        for obj in selected_objects:
            obj.select_set(True)

        return {'FINISHED'}

# ------------------------------------------------------------
# OperatorLoftCurves

class OperatorLoftCurves(bpy.types.Operator):
    bl_idname = "curvetools.operatorloftcurves"
    bl_label = "Loft"
    bl_description = "Lofts selected curves"
    bl_options = {'UNDO'}


    @classmethod
    def poll(cls, context):
        return util.Selected2Curves()


    def execute(self, context):
        #print("### TODO: OperatorLoftcurves.execute()")

        loftedSurface = surfaces.LoftedSurface.FromSelection()
        loftedSurface.AddToScene()

        self.report({'INFO'}, "OperatorLoftcurves.execute()")

        return {'FINISHED'}


# ------------------------------------------------------------
# OperatorSweepCurves

class OperatorSweepCurves(bpy.types.Operator):
    bl_idname = "curvetools.operatorsweepcurves"
    bl_label = "Sweep"
    bl_description = "Sweeps the active curve along to other curve (rail)"
    bl_options = {'UNDO'}


    @classmethod
    def poll(cls, context):
        return util.Selected2Curves()


    def execute(self, context):
        #print("### TODO: OperatorSweepcurves.execute()")

        sweptSurface = surfaces.SweptSurface.FromSelection()
        sweptSurface.AddToScene()

        self.report({'INFO'}, "OperatorSweepcurves.execute()")

        return {'FINISHED'}



# 3 CURVES SELECTED
# #################
class OperatorBirail(bpy.types.Operator):
    bl_idname = "curvetools.operatorbirail"
    bl_label = "Birail"
    bl_description = "Generates a birailed surface from 3 selected curves -- in order: rail1, rail2 and profile"
    bl_options = {'UNDO'}


    @classmethod
    def poll(cls, context):
        return util.Selected3Curves()


    def execute(self, context):
        birailedSurface = surfaces.BirailedSurface.FromSelection()
        birailedSurface.AddToScene()

        self.report({'INFO'}, "OperatorBirail.execute()")

        return {'FINISHED'}



# 1 OR MORE CURVES SELECTED
# #########################
class OperatorSplinesSetResolution(bpy.types.Operator):
    bl_idname = "curvetools.operatorsplinessetresolution"
    bl_label = "SplinesSetResolution"
    bl_description = "Sets the resolution of all splines"
    bl_options = {'UNDO'}


    @classmethod
    def poll(cls, context):
        return util.Selected1OrMoreCurves()


    def execute(self, context):
        splRes = context.scene.curvetools.SplineResolution
        selCurves = util.GetSelectedCurves()

        for blCurve in selCurves:
            for spline in blCurve.data.splines:
                spline.resolution_u = splRes

        return {'FINISHED'}

# ------------------------------------------------------------
# OperatorSplinesRemoveZeroSegment

class OperatorSplinesRemoveZeroSegment(bpy.types.Operator):
    bl_idname = "curvetools.operatorsplinesremovezerosegment"
    bl_label = "SplinesRemoveZeroSegment"
    bl_description = "Removes splines with no segments -- they seem to creep up, sometimes"
    bl_options = {'UNDO'}


    @classmethod
    def poll(cls, context):
        return util.Selected1OrMoreCurves()


    def execute(self, context):
        selCurves = util.GetSelectedCurves()

        for blCurve in selCurves:
            curve = curves.Curve(blCurve)
            nrSplines = curve.nrSplines

            splinesToRemove = []
            for spline in curve.splines:
                if len(spline.segments) < 1: splinesToRemove.append(spline)
            nrRemovedSplines = len(splinesToRemove)

            for spline in splinesToRemove: curve.splines.remove(spline)

            if nrRemovedSplines > 0: curve.RebuildInScene()

            self.report({'INFO'}, "Removed %d of %d splines" % (nrRemovedSplines, nrSplines))

        return {'FINISHED'}

# ------------------------------------------------------------
# OperatorSplinesRemoveShort

class OperatorSplinesRemoveShort(bpy.types.Operator):
    bl_idname = "curvetools.operatorsplinesremoveshort"
    bl_label = "SplinesRemoveShort"
    bl_description = "Removes splines with a length smaller than the threshold"
    bl_options = {'UNDO'}


    @classmethod
    def poll(cls, context):
        return util.Selected1OrMoreCurves()


    def execute(self, context):
        threshold = context.scene.curvetools.SplineRemoveLength
        selCurves = util.GetSelectedCurves()

        for blCurve in selCurves:
            curve = curves.Curve(blCurve)
            nrSplines = curve.nrSplines

            nrRemovedSplines = curve.RemoveShortSplines(threshold)
            if nrRemovedSplines > 0: curve.RebuildInScene()

            self.report({'INFO'}, "Removed %d of %d splines" % (nrRemovedSplines, nrSplines))

        return {'FINISHED'}

# ------------------------------------------------------------
# OperatorSplinesJoinNeighbouring

class OperatorSplinesJoinNeighbouring(bpy.types.Operator):
    bl_idname = "curvetools.operatorsplinesjoinneighbouring"
    bl_label = "SplinesJoinNeighbouring"
    bl_description = "Joins neighbouring splines within a distance smaller than the threshold"
    bl_options = {'UNDO'}


    @classmethod
    def poll(cls, context):
        return util.Selected1OrMoreCurves()


    def execute(self, context):
        selCurves = util.GetSelectedCurves()

        for blCurve in selCurves:
            curve = curves.Curve(blCurve)
            nrSplines = curve.nrSplines

            threshold = context.scene.curvetools.SplineJoinDistance
            startEnd = context.scene.curvetools.SplineJoinStartEnd
            mode = context.scene.curvetools.SplineJoinMode

            nrJoins = curve.JoinNeighbouringSplines(startEnd, threshold, mode)
            if nrJoins > 0: curve.RebuildInScene()

            self.report({'INFO'}, "Applied %d joins on %d splines; resulting nrSplines: %d" % (nrJoins, nrSplines, curve.nrSplines))

        return {'FINISHED'}

# ------------------------------------------------------------
# SurfaceFromBezier

def SurfaceFromBezier(surfacedata, points, center):

    len_points = len(points) - 1

    if len_points % 2 == 0:
        h = mathematics.subdivide_cubic_bezier(
                        points[len_points].co, points[len_points].handle_right,
                        points[0].handle_left, points[0].co, 0.5
                        )
        points.add(1)
        len_points = len(points) - 1
        points[len_points - 1].handle_right = h[0]
        points[len_points].handle_left = h[1]
        points[len_points].co =  h[2]
        points[len_points].handle_right = h[3]
        points[0].handle_left =  h[4]

    half = round((len_points + 1)/2) - 1
    # 1
    surfacespline1 = surfacedata.splines.new(type='NURBS')
    surfacespline1.points.add(3)
    surfacespline1.points[0].co = [points[0].co.x, points[0].co.y, points[0].co.z, 1]
    surfacespline1.points[1].co = [points[0].handle_left.x, points[0].handle_left.y, points[0].handle_left.z, 1]
    surfacespline1.points[2].co = [points[len_points].handle_right.x,points[len_points].handle_right.y, points[len_points].handle_right.z, 1]
    surfacespline1.points[3].co = [points[len_points].co.x, points[len_points].co.y, points[len_points].co.z, 1]
    for p in surfacespline1.points:
        p.select = True
    surfacespline1.use_endpoint_u = True
    surfacespline1.use_endpoint_v = True

    for i in range(0, half):

        if center:
            # 2
            surfacespline2 = surfacedata.splines.new(type='NURBS')
            surfacespline2.points.add(3)
            surfacespline2.points[0].co = [points[i].co.x, points[i].co.y, points[i].co.z, 1]
            surfacespline2.points[1].co = [(points[i].co.x + points[len_points - i].co.x)/2,
                                           (points[i].co.y + points[len_points - i].co.y)/2,
                                           (points[i].co.z + points[len_points - i].co.z)/2, 1]
            surfacespline2.points[2].co = [(points[len_points - i].co.x + points[i].co.x)/2,
                                           (points[len_points - i].co.y + points[i].co.y)/2,
                                           (points[len_points - i].co.z + points[i].co.z)/2, 1]
            surfacespline2.points[3].co = [points[len_points - i].co.x, points[len_points - i].co.y, points[len_points - i].co.z, 1]
            for p in surfacespline2.points:
                p.select = True
            surfacespline2.use_endpoint_u = True
            surfacespline2.use_endpoint_v = True

        # 3
        surfacespline3 = surfacedata.splines.new(type='NURBS')
        surfacespline3.points.add(3)
        surfacespline3.points[0].co = [points[i].handle_right.x, points[i].handle_right.y, points[i].handle_right.z, 1]
        surfacespline3.points[1].co = [(points[i].handle_right.x + points[len_points - i].handle_left.x)/2,
                                       (points[i].handle_right.y + points[len_points - i].handle_left.y)/2,
                                       (points[i].handle_right.z + points[len_points - i].handle_left.z)/2, 1]
        surfacespline3.points[2].co = [(points[len_points - i].handle_left.x + points[i].handle_right.x)/2,
                                       (points[len_points - i].handle_left.y + points[i].handle_right.y)/2,
                                       (points[len_points - i].handle_left.z + points[i].handle_right.z)/2, 1]
        surfacespline3.points[3].co = [points[len_points - i].handle_left.x, points[len_points - i].handle_left.y, points[len_points - i].handle_left.z, 1]
        for p in surfacespline3.points:
            p.select = True
        surfacespline3.use_endpoint_u = True
        surfacespline3.use_endpoint_v = True

        # 4
        surfacespline4 = surfacedata.splines.new(type='NURBS')
        surfacespline4.points.add(3)
        surfacespline4.points[0].co = [points[i + 1].handle_left.x, points[i + 1].handle_left.y, points[i + 1].handle_left.z, 1]
        surfacespline4.points[1].co = [(points[i + 1].handle_left.x + points[len_points - i - 1].handle_right.x)/2,
                                       (points[i + 1].handle_left.y + points[len_points - i - 1].handle_right.y)/2,
                                       (points[i + 1].handle_left.z + points[len_points - i - 1].handle_right.z)/2, 1]
        surfacespline4.points[2].co = [(points[len_points - i - 1].handle_right.x + points[i + 1].handle_left.x)/2,
                                       (points[len_points - i - 1].handle_right.y + points[i + 1].handle_left.y)/2,
                                       (points[len_points - i - 1].handle_right.z + points[i + 1].handle_left.z)/2, 1]
        surfacespline4.points[3].co = [points[len_points - i - 1].handle_right.x, points[len_points - i - 1].handle_right.y, points[len_points - i - 1].handle_right.z, 1]
        for p in surfacespline4.points:
            p.select = True
        surfacespline4.use_endpoint_u = True
        surfacespline4.use_endpoint_v = True

        if center:
            # 5
            surfacespline5 = surfacedata.splines.new(type='NURBS')
            surfacespline5.points.add(3)
            surfacespline5.points[0].co = [points[i + 1].co.x, points[i + 1].co.y, points[i + 1].co.z, 1]
            surfacespline5.points[1].co = [(points[i + 1].co.x + points[len_points - i - 1].co.x)/2,
                                           (points[i + 1].co.y + points[len_points - i - 1].co.y)/2,
                                           (points[i + 1].co.z + points[len_points - i - 1].co.z)/2, 1]
            surfacespline5.points[2].co = [(points[len_points - i - 1].co.x + points[i + 1].co.x)/2,
                                           (points[len_points - i - 1].co.y + points[i + 1].co.y)/2,
                                           (points[len_points - i - 1].co.z + points[i + 1].co.z)/2, 1]
            surfacespline5.points[3].co = [points[len_points - i - 1].co.x, points[len_points - i - 1].co.y, points[len_points - i - 1].co.z, 1]
            for p in surfacespline5.points:
                p.select = True
            surfacespline5.use_endpoint_u = True
            surfacespline5.use_endpoint_v = True

    # 6
    surfacespline6 = surfacedata.splines.new(type='NURBS')
    surfacespline6.points.add(3)
    surfacespline6.points[0].co = [points[half].co.x, points[half].co.y, points[half].co.z, 1]
    surfacespline6.points[1].co = [points[half].handle_right.x, points[half].handle_right.y, points[half].handle_right.z, 1]
    surfacespline6.points[2].co = [points[half+1].handle_left.x, points[half+1].handle_left.y, points[half+1].handle_left.z, 1]
    surfacespline6.points[3].co = [points[half+1].co.x, points[half+1].co.y, points[half+1].co.z, 1]
    for p in surfacespline6.points:
        p.select = True
    surfacespline6.use_endpoint_u = True
    surfacespline6.use_endpoint_v = True

    bpy.ops.object.mode_set(mode = 'EDIT')
    bpy.ops.curve.make_segment()

    for s in surfacedata.splines:
        s.resolution_u = 4
        s.resolution_v = 4
        s.order_u = 4
        s.order_v = 4
        for p in s.points:
            p.select = False

# ------------------------------------------------------------
# Convert selected faces to Bezier

class ConvertSelectedFacesToBezier(bpy.types.Operator):
    bl_idname = "curvetools.convert_selected_face_to_bezier"
    bl_label = "Convert selected faces to Bezier"
    bl_description = "Convert selected faces to Bezier"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return util.Selected1Mesh()

    def execute(self, context):
        # main function
        bpy.ops.object.mode_set(mode = 'OBJECT')
        active_object = context.active_object
        meshdata = active_object.data
        curvedata = bpy.data.curves.new('Curve' + active_object.name, type='CURVE')
        curveobject = object_utils.object_data_add(context, curvedata)
        curvedata.dimensions = '3D'

        for poly in meshdata.polygons:
            if poly.select:
                newSpline = curvedata.splines.new(type='BEZIER')
                newSpline.use_cyclic_u = True
                newSpline.bezier_points.add(poly.loop_total - 1)
                npoint = 0
                for loop_index in range(poly.loop_start, poly.loop_start + poly.loop_total):
                    newSpline.bezier_points[npoint].co = meshdata.vertices[meshdata.loops[loop_index].vertex_index].co
                    newSpline.bezier_points[npoint].handle_left_type = 'VECTOR'
                    newSpline.bezier_points[npoint].handle_right_type = 'VECTOR'
                    newSpline.bezier_points[npoint].select_control_point = True
                    newSpline.bezier_points[npoint].select_left_handle = True
                    newSpline.bezier_points[npoint].select_right_handle = True
                    npoint += 1

        return {'FINISHED'}

# ------------------------------------------------------------
# Convert Bezier to Surface

class ConvertBezierToSurface(bpy.types.Operator):
    bl_idname = "curvetools.convert_bezier_to_surface"
    bl_label = "Convert Bezier to Surface"
    bl_description = "Convert Bezier to Surface"
    bl_options = {'REGISTER', 'UNDO'}

    Center : BoolProperty(
            name="Center",
            default=False,
            description="Consider center points"
            )

    Resolution_U: IntProperty(
            name="Resolution_U",
            default=4,
            min=1, max=64,
            soft_min=1,
            description="Surface resolution U"
            )

    Resolution_V: IntProperty(
            name="Resolution_V",
            default=4,
            min=1, max=64,
            soft_min=1,
            description="Surface resolution V"
            )

    def draw(self, context):
        layout = self.layout

         # general options
        col = layout.column()
        col.prop(self, 'Center')
        col.prop(self, 'Resolution_U')
        col.prop(self, 'Resolution_V')

    @classmethod
    def poll(cls, context):
        return util.Selected1OrMoreCurves()

    def execute(self, context):
        # main function
        bpy.ops.object.mode_set(mode = 'OBJECT')
        active_object = context.active_object
        curvedata = active_object.data

        surfacedata = bpy.data.curves.new('Surface', type='SURFACE')
        surfaceobject = object_utils.object_data_add(context, surfacedata)
        surfaceobject.matrix_world = active_object.matrix_world
        surfaceobject.rotation_euler = active_object.rotation_euler
        surfacedata.dimensions = '3D'
        surfaceobject.show_wire = True
        surfaceobject.show_in_front = True

        for spline in curvedata.splines:
            SurfaceFromBezier(surfacedata, spline.bezier_points, self.Center)

        for spline in surfacedata.splines:
            len_p = len(spline.points)
            len_devide_4 = round(len_p / 4) + 1
            len_devide_2 = round(len_p / 2)
            bpy.ops.object.mode_set(mode = 'EDIT')
            for point_index in range(len_devide_4, len_p - len_devide_4):
                if point_index != len_devide_2 and point_index != len_devide_2 - 1:
                    spline.points[point_index].select = True

            surfacedata.resolution_u = self.Resolution_U
            surfacedata.resolution_v = self.Resolution_V

        return {'FINISHED'}

# ------------------------------------------------------------
# Fillet

class BezierPointsFillet(bpy.types.Operator):
    bl_idname = "curvetools.bezier_points_fillet"
    bl_label = "Bezier points Fillet"
    bl_description = "Bezier points Fillet"
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}

    Fillet_radius : FloatProperty(
            name="Radius",
            default=0.25,
            unit='LENGTH',
            description="Radius"
            )
    Types = [('Round', "Round", "Round"),
             ('Chamfer', "Chamfer", "Chamfer")]
    Fillet_Type : EnumProperty(
            name="Type",
            description="Fillet type",
            items=Types
            )

    def draw(self, context):
        layout = self.layout

        # general options
        col = layout.column()
        col.prop(self, "Fillet_radius")
        col.prop(self, "Fillet_Type", expand=True)

    @classmethod
    def poll(cls, context):
        return util.Selected1OrMoreCurves()

    def execute(self, context):
        # main function
        if bpy.ops.object.mode_set.poll():
            bpy.ops.object.mode_set(mode='EDIT')

        splines = bpy.context.object.data.splines
        bpy.ops.curve.spline_type_set(type='BEZIER')

        bpy.ops.curve.handle_type_set(type='VECTOR')
        s = []
        for spline in splines:
            n = 0
            ii = []
            for p in spline.bezier_points:
                if p.select_control_point:
                    ii.append(n)
                    n += 1
                else:
                    n += 1
            s.append(ii)

        sn = 0
        for spline in splines:
            ii = s[sn]
            bezier_points = spline.bezier_points
            n = len(bezier_points)
            if n > 2:
                jn = 0
                for j in ii:
                    j += jn

                    bpy.ops.curve.select_all(action='DESELECT')

                    if j != 0 and j != n - 1:
                        bezier_points[j].select_control_point = True
                        bezier_points[j + 1].select_control_point = True
                        bpy.ops.curve.subdivide()
                        selected4 = [bezier_points[j - 1], bezier_points[j],
                                     bezier_points[j + 1], bezier_points[j + 2]]
                        jn += 1
                        n += 1

                    elif j == 0:
                        bezier_points[j].select_control_point = True
                        bezier_points[j + 1].select_control_point = True
                        bpy.ops.curve.subdivide()
                        selected4 = [bezier_points[n], bezier_points[0],
                                     bezier_points[1], bezier_points[2]]
                        jn += 1
                        n += 1

                    elif j == n - 1:
                        bezier_points[j].select_control_point = True
                        bezier_points[j - 1].select_control_point = True
                        bpy.ops.curve.subdivide()
                        selected4 = [bezier_points[0], bezier_points[n],
                                     bezier_points[n - 1], bezier_points[n - 2]]

                    selected4[2].co = selected4[1].co
                    s1 = Vector(selected4[0].co) - Vector(selected4[1].co)
                    s2 = Vector(selected4[3].co) - Vector(selected4[2].co)
                    s1.normalize()
                    s11 = Vector(selected4[1].co) + s1 * self.Fillet_radius
                    selected4[1].co = s11
                    s2.normalize()
                    s22 = Vector(selected4[2].co) + s2 * self.Fillet_radius
                    selected4[2].co = s22

                    if self.Fillet_Type == 'Round':
                        if j != n - 1:
                            selected4[2].handle_right_type = 'VECTOR'
                            selected4[1].handle_left_type = 'VECTOR'
                            selected4[1].handle_right_type = 'ALIGNED'
                            selected4[2].handle_left_type = 'ALIGNED'
                        else:
                            selected4[1].handle_right_type = 'VECTOR'
                            selected4[2].handle_left_type = 'VECTOR'
                            selected4[2].handle_right_type = 'ALIGNED'
                            selected4[1].handle_left_type = 'ALIGNED'
                    if self.Fillet_Type == 'Chamfer':
                        selected4[2].handle_right_type = 'VECTOR'
                        selected4[1].handle_left_type = 'VECTOR'
                        selected4[1].handle_right_type = 'VECTOR'
                        selected4[2].handle_left_type = 'VECTOR'
            sn += 1

        return {'FINISHED'}

# ------------------------------------------------------------
# BezierDivide Operator

class BezierDivide(bpy.types.Operator):
    bl_idname = "curvetools.bezier_spline_divide"
    bl_label = "Bezier Spline Divide"
    bl_description = "Bezier Divide (enters edit mode) for Fillet Curves"
    bl_options = {'REGISTER', 'UNDO'}

    # align_matrix for the invoke
    align_matrix : Matrix()

    Bezier_t : FloatProperty(
            name="t (0% - 100%)",
            default=50.0,
            min=0.0, soft_min=0.0,
            max=100.0, soft_max=100.0,
            description="t (0% - 100%)"
            )

    @classmethod
    def poll(cls, context):
        return util.Selected1OrMoreCurves()

    def execute(self, context):
        # main function
        if bpy.ops.object.mode_set.poll():
            bpy.ops.object.mode_set(mode='EDIT')

        splines = bpy.context.object.data.splines
        s = []
        for spline in splines:
            bpy.ops.curve.spline_type_set(type='BEZIER')

            n = 0
            ii = []
            for p in spline.bezier_points:
                if p.select_control_point:
                    ii.append(n)
                    n += 1
                else:
                    n += 1
            s.append(ii)

        sn = 0
        for spline in splines:
            ii = s[sn]
            bezier_points = spline.bezier_points
            n = len(bezier_points)
            if n > 2:
                jn = 0
                for j in ii:

                    bpy.ops.curve.select_all(action='DESELECT')

                    if (j in ii) and (j + 1 in ii):
                        bezier_points[j + jn].select_control_point = True
                        bezier_points[j + 1 + jn].select_control_point = True
                        h = mathematics.subdivide_cubic_bezier(
                            bezier_points[j + jn].co, bezier_points[j + jn].handle_right,
                            bezier_points[j + 1 + jn].handle_left, bezier_points[j + 1 + jn].co, self.Bezier_t / 100
                            )
                        bpy.ops.curve.subdivide(1)
                        bezier_points[j + jn].handle_right_type = 'FREE'
                        bezier_points[j + jn].handle_right = h[0]
                        bezier_points[j + 1 + jn].co = h[2]
                        bezier_points[j + 1 + jn].handle_left_type = 'FREE'
                        bezier_points[j + 1 + jn].handle_left = h[1]
                        bezier_points[j + 1 + jn].handle_right_type = 'FREE'
                        bezier_points[j + 1 + jn].handle_right = h[3]
                        bezier_points[j + 2 + jn].handle_left_type = 'FREE'
                        bezier_points[j + 2 + jn].handle_left = h[4]
                        jn += 1

                    if j == n - 1 and (0 in ii) and spline.use_cyclic_u:
                        bezier_points[j + jn].select_control_point = True
                        bezier_points[0].select_control_point = True
                        h = mathematics.subdivide_cubic_bezier(
                            bezier_points[j + jn].co, bezier_points[j + jn].handle_right,
                            bezier_points[0].handle_left, bezier_points[0].co, self.Bezier_t / 100
                            )
                        bpy.ops.curve.subdivide(1)
                        bezier_points[j + jn].handle_right_type = 'FREE'
                        bezier_points[j + jn].handle_right = h[0]
                        bezier_points[j + 1 + jn].co = h[2]
                        bezier_points[j + 1 + jn].handle_left_type = 'FREE'
                        bezier_points[j + 1 + jn].handle_left = h[1]
                        bezier_points[j + 1 + jn].handle_right_type = 'FREE'
                        bezier_points[j + 1 + jn].handle_right = h[3]
                        bezier_points[0].handle_left_type = 'FREE'
                        bezier_points[0].handle_left = h[4]

            sn += 1

        return {'FINISHED'}

# ------------------------------------------------------------
# CurveScaleReset Operator

class CurveScaleReset(bpy.types.Operator):
    bl_idname = "curvetools.scale_reset"
    bl_label = "Curve Scale Reset"
    bl_description = "Curve Scale Reset"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return (context.object is not None and
                context.object.type == 'CURVE')

    def execute(self, context):
        # main function
        current_mode = bpy.context.object.mode

        bpy.ops.object.mode_set(mode = 'OBJECT')

        oldCurve = context.active_object
        oldCurveName = oldCurve.name

        bpy.ops.object.duplicate_move(OBJECT_OT_duplicate=None, TRANSFORM_OT_translate=None)
        newCurve = context.active_object
        newCurve.data.splines.clear()
        newCurve.scale = (1.0, 1.0, 1.0)

        oldCurve.select_set(True)
        newCurve.select_set(True)
        bpy.context.view_layer.objects.active = newCurve
        bpy.ops.object.join()

        joinCurve = context.active_object
        joinCurve.name = oldCurveName

        bpy.ops.object.mode_set (mode = current_mode)

        return {'FINISHED'}

# ------------------------------------------------------------
# Split Operator

class Split(bpy.types.Operator):
    bl_idname = "curvetools.split"
    bl_label = "Split"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return util.Selected1OrMoreCurves()

    def execute(self, context):
        selected_Curves = util.GetSelectedCurves()

        for curve in selected_Curves:
            spline_points = []
            select_points = {}
            bezier_spline_points = []
            select_bezier_points = {}
            i_bp = 0
            i_p = 0
            for spline in curve.data.splines:
                if spline.type == 'BEZIER':
                    points = {}
                    select_bezier_points[i_bp] = [len(spline.bezier_points)]
                    for i in range(len(spline.bezier_points)):
                        bezier_point = spline.bezier_points[i]
                        points[i]=[bezier_point.co[:], bezier_point.handle_left[:], bezier_point.handle_right[:]]

                        if spline.bezier_points[i].select_control_point:
                            select_bezier_points[i_bp].append(i)
                    i_bp+=1
                    bezier_spline_points.append(points)
                else:
                    points = {}
                    select_points[i_p] = [len(spline.points)]
                    for i in range(len(spline.points)):
                        point = spline.points[i]
                        points[i]=[point.co[:], spline.type]
                        if spline.points[i].select:
                            select_points[i_p].append(i)
                    i_p+=1
                    spline_points.append(points)

            curve.data.splines.clear()

            for key in select_bezier_points:

                num=0

                if select_bezier_points[key][-1] == select_bezier_points[key][0]-1:
                    select_bezier_points[key].pop()

                for i in select_bezier_points[key][1:]+[select_bezier_points[key][0]-1]:
                    if i != 0:
                        spline = curve.data.splines.new('BEZIER')
                        spline.bezier_points.add(i-num)

                        for j in range(num, i):
                            bezier_point = spline.bezier_points[j-num]

                            bezier_point.co = bezier_spline_points[key][j][0]
                            bezier_point.handle_left = bezier_spline_points[key][j][1]
                            bezier_point.handle_right = bezier_spline_points[key][j][2]
                        bezier_point = spline.bezier_points[-1]
                        bezier_point.co = bezier_spline_points[key][i][0]
                        bezier_point.handle_left = bezier_spline_points[key][i][1]
                        bezier_point.handle_right = bezier_spline_points[key][i][2]
                        num=i

            for key in select_points:

                num=0

                if select_points[key][-1] == select_points[key][0]-1:
                    select_points[key].pop()

                for i in select_points[key][1:]+[select_points[key][0]-1]:
                    if i != 0:
                        spline = curve.data.splines.new(spline_points[key][i][1])
                        spline.points.add(i-num)

                        for j in range(num, i):
                            point = spline.points[j-num]

                            point.co = spline_points[key][j][0]
                        point = spline.points[-1]
                        point.co = spline_points[key][i][0]
                        num=i

        return {'FINISHED'}

class SeparateOutline(bpy.types.Operator):
    bl_idname = "curvetools.sep_outline"
    bl_label = "Separate Outline"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Makes 'Outline' separate mesh"

    @classmethod
    def poll(cls, context):
        return util.Selected1OrMoreCurves()

    def execute(self, context):
        bpy.ops.object.mode_set(mode = 'EDIT')
        bpy.ops.curve.separate()

        return {'FINISHED'}

class CurveBoolean(bpy.types.Operator):
    bl_idname = "curvetools.bezier_curve_boolean"
    bl_description = "Curve Boolean"
    bl_label = "Curve Boolean"
    bl_options = {'REGISTER', 'UNDO'}

    operation: bpy.props.EnumProperty(name='Type', items=[
        ('UNION', 'Union', 'Boolean OR', 0),
        ('INTERSECTION', 'Intersection', 'Boolean AND', 1),
        ('DIFFERENCE', 'Difference', 'Active minus Selected', 2),
    ])
    number : IntProperty(
            name="Spline Number",
            default=1,
            min=1,
            description="Spline Number"
            )

    @classmethod
    def poll(cls, context):
        return util.Selected1OrMoreCurves()

    def draw(self, context):
        layout = self.layout

        # general options
        col = layout.column()
        col.prop(self, "operation")
        if self.operation == 'DIFFERENCE':
            col.prop(self, "number")

    def execute(self, context):
        current_mode = bpy.context.object.mode

        if bpy.ops.object.mode_set.poll():
            bpy.ops.object.mode_set(mode = 'OBJECT')

        selected_Curves = util.GetSelectedCurves()
        len_selected_curves = len(selected_Curves)
        if len_selected_curves < 2:
            return {'FINISHED'}

        min_number = 1

        max_number = 0
        for iCurve in range(0, len_selected_curves):
            len_splines = len(selected_Curves[iCurve].data.splines)
            max_number += len_splines

        if self.number < min_number:
            self.number = min_number
        if self.number > max_number:
            self.number = max_number

        j = 0
        first_curve = 0
        first_spline = 0
        for iCurve in range(0, len_selected_curves):
            len_splines = len(selected_Curves[iCurve].data.splines)
            for iSpline in range(0, len_splines):
                if j == self.number:
                    first_curve = iCurve
                    first_spline = iSpline
                j += 1

        bpy.ops.object.select_all(action='DESELECT')

        spline1 = selected_Curves[first_curve].data.splines[first_spline]
        matrix_world1 = selected_Curves[first_curve].matrix_world

        len_spline1 = len(spline1.bezier_points)

        dataCurve = bpy.data.curves.new(self.operation, type='CURVE')
        dataCurve.dimensions = '2D'
        newSpline1 = dataCurve.splines.new(type='BEZIER')
        newSpline1.use_cyclic_u = True
        newSpline1.bezier_points.add(len_spline1 - 1)
        for n in range(0, len_spline1):
            newSpline1.bezier_points[n].co = matrix_world1 @ spline1.bezier_points[n].co
            newSpline1.bezier_points[n].handle_left_type = spline1.bezier_points[n].handle_left_type
            newSpline1.bezier_points[n].handle_left = matrix_world1 @ spline1.bezier_points[n].handle_left
            newSpline1.bezier_points[n].handle_right_type = spline1.bezier_points[n].handle_right_type
            newSpline1.bezier_points[n].handle_right = matrix_world1 @ spline1.bezier_points[n].handle_right

        Curve = object_utils.object_data_add(context, dataCurve)
        bpy.context.view_layer.objects.active = Curve
        Curve.select_set(True)
        Curve.location = (0.0, 0.0, 0.0)

        j = 0
        for iCurve in range(0, len_selected_curves):
            matrix_world = selected_Curves[iCurve].matrix_world
            len_splines = len(selected_Curves[iCurve].data.splines)
            for iSpline in range(0, len_splines):
                if iCurve == first_curve and iSpline == first_spline:
                    continue
                spline = selected_Curves[iCurve].data.splines[iSpline]
                len_spline = len(spline.bezier_points)
                newSpline = dataCurve.splines.new(type='BEZIER')
                newSpline.use_cyclic_u = True
                newSpline.bezier_points.add(len_spline - 1)
                for n in range(0, len_spline):
                    newSpline.bezier_points[n].co = matrix_world @ spline.bezier_points[n].co
                    newSpline.bezier_points[n].handle_left_type = spline.bezier_points[n].handle_left_type
                    newSpline.bezier_points[n].handle_left = matrix_world @ spline.bezier_points[n].handle_left
                    newSpline.bezier_points[n].handle_right_type = spline.bezier_points[n].handle_right_type
                    newSpline.bezier_points[n].handle_right = matrix_world @ spline.bezier_points[n].handle_right

                bpy.ops.object.mode_set(mode = 'EDIT')
                bpy.ops.curve.select_all(action='SELECT')
                splines = internal.getSelectedSplines(True, True)
                if len(splines) < 2:
                   continue
                splineA = splines[0]
                splineB = splines[1]
                dataCurve.splines.active = newSpline1

                if not internal.bezierBooleanGeometry(splineA, splineB, self.operation):
                    self.report({'WARNING'}, 'Invalid selection.')
                    return {'CANCELLED'}

                j += 1

        bpy.ops.object.mode_set(mode = 'EDIT')
        bpy.ops.curve.select_all(action='SELECT')

        return {'FINISHED'}

# ----------------------------
# Set first points operator
class SetFirstPoints(bpy.types.Operator):
    bl_idname = "curvetools.set_first_points"
    bl_label = "Set first points"
    bl_description = "Set the selected points as the first point of each spline"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return util.Selected1OrMoreCurves()

    def execute(self, context):
        splines_to_invert = []

        curve = bpy.context.object

        bpy.ops.object.mode_set('INVOKE_REGION_WIN', mode='EDIT')

        # Check non-cyclic splines to invert
        for i in range(len(curve.data.splines)):
            b_points = curve.data.splines[i].bezier_points

            if i not in self.cyclic_splines:  # Only for non-cyclic splines
                if b_points[len(b_points) - 1].select_control_point:
                    splines_to_invert.append(i)

        # Reorder points of cyclic splines, and set all handles to "Automatic"

        # Check first selected point
        cyclic_splines_new_first_pt = {}
        for i in self.cyclic_splines:
            sp = curve.data.splines[i]

            for t in range(len(sp.bezier_points)):
                bp = sp.bezier_points[t]
                if bp.select_control_point or bp.select_right_handle or bp.select_left_handle:
                    cyclic_splines_new_first_pt[i] = t
                    break  # To take only one if there are more

        # Reorder
        for spline_idx in cyclic_splines_new_first_pt:
            sp = curve.data.splines[spline_idx]

            spline_old_coords = []
            for bp_old in sp.bezier_points:
                coords = (bp_old.co[0], bp_old.co[1], bp_old.co[2])

                left_handle_type = str(bp_old.handle_left_type)
                left_handle_length = float(bp_old.handle_left.length)
                left_handle_xyz = (
                        float(bp_old.handle_left.x),
                        float(bp_old.handle_left.y),
                        float(bp_old.handle_left.z)
                        )
                right_handle_type = str(bp_old.handle_right_type)
                right_handle_length = float(bp_old.handle_right.length)
                right_handle_xyz = (
                        float(bp_old.handle_right.x),
                        float(bp_old.handle_right.y),
                        float(bp_old.handle_right.z)
                        )
                spline_old_coords.append(
                        [coords, left_handle_type,
                        right_handle_type, left_handle_length,
                        right_handle_length, left_handle_xyz,
                        right_handle_xyz]
                        )

            for t in range(len(sp.bezier_points)):
                bp = sp.bezier_points

                if t + cyclic_splines_new_first_pt[spline_idx] + 1 <= len(bp) - 1:
                    new_index = t + cyclic_splines_new_first_pt[spline_idx] + 1
                else:
                    new_index = t + cyclic_splines_new_first_pt[spline_idx] + 1 - len(bp)

                bp[t].co = Vector(spline_old_coords[new_index][0])

                bp[t].handle_left.length = spline_old_coords[new_index][3]
                bp[t].handle_right.length = spline_old_coords[new_index][4]

                bp[t].handle_left_type = "FREE"
                bp[t].handle_right_type = "FREE"

                bp[t].handle_left.x = spline_old_coords[new_index][5][0]
                bp[t].handle_left.y = spline_old_coords[new_index][5][1]
                bp[t].handle_left.z = spline_old_coords[new_index][5][2]

                bp[t].handle_right.x = spline_old_coords[new_index][6][0]
                bp[t].handle_right.y = spline_old_coords[new_index][6][1]
                bp[t].handle_right.z = spline_old_coords[new_index][6][2]

                bp[t].handle_left_type = spline_old_coords[new_index][1]
                bp[t].handle_right_type = spline_old_coords[new_index][2]

        # Invert the non-cyclic splines designated above
        for i in range(len(splines_to_invert)):
            bpy.ops.curve.select_all('INVOKE_REGION_WIN', action='DESELECT')

            bpy.ops.object.editmode_toggle('INVOKE_REGION_WIN')
            curve.data.splines[splines_to_invert[i]].bezier_points[0].select_control_point = True
            bpy.ops.object.editmode_toggle('INVOKE_REGION_WIN')

            bpy.ops.curve.switch_direction()

        bpy.ops.curve.select_all('INVOKE_REGION_WIN', action='DESELECT')

        # Keep selected the first vert of each spline
        bpy.ops.object.editmode_toggle('INVOKE_REGION_WIN')
        for i in range(len(curve.data.splines)):
            if not curve.data.splines[i].use_cyclic_u:
                bp = curve.data.splines[i].bezier_points[0]
            else:
                bp = curve.data.splines[i].bezier_points[
                                                        len(curve.data.splines[i].bezier_points) - 1
                                                        ]

            bp.select_control_point = True
            bp.select_right_handle = True
            bp.select_left_handle = True

        bpy.ops.object.editmode_toggle('INVOKE_REGION_WIN')

        return {'FINISHED'}

    def invoke(self, context, event):
        curve = bpy.context.object

        # Check if all curves are Bezier, and detect which ones are cyclic
        self.cyclic_splines = []
        for i in range(len(curve.data.splines)):
            if curve.data.splines[i].type != "BEZIER":
                self.report({'WARNING'}, "All splines must be Bezier type")

                return {'CANCELLED'}
            else:
                if curve.data.splines[i].use_cyclic_u:
                    self.cyclic_splines.append(i)

        self.execute(context)
        self.report({'INFO'}, "First points have been set")

        return {'FINISHED'}

def register():
    for cls in classes:
        bpy.utils.register_class(operators)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(operators)

if __name__ == "__main__":
    register()

operators = [
    OperatorCurveInfo,
    OperatorCurveLength,
    OperatorSplinesInfo,
    OperatorSegmentsInfo,
    OperatorOriginToSpline0Start,
    OperatorIntersectCurves,
    OperatorLoftCurves,
    OperatorSweepCurves,
    OperatorBirail,
    OperatorSplinesSetResolution,
    OperatorSplinesRemoveZeroSegment,
    OperatorSplinesRemoveShort,
    OperatorSplinesJoinNeighbouring,
    ConvertSelectedFacesToBezier,
    ConvertBezierToSurface,
    BezierPointsFillet,
    BezierDivide,
    CurveScaleReset,
    Split,
    SeparateOutline,
    CurveBoolean,
    SetFirstPoints,
    ]

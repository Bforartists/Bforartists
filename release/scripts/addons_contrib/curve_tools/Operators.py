import time
import threading

import bpy
from bpy.props import *
from bpy_extras import object_utils

from . import Properties
from . import Curves
from . import CurveIntersections
from . import Util
from . import Surfaces

# 1 CURVE SELECTED
# ################
class OperatorCurveInfo(bpy.types.Operator):
    bl_idname = "curvetools2.operatorcurveinfo"
    bl_label = "Info"
    bl_description = "Displays general info about the active/selected curve"


    @classmethod
    def poll(cls, context):
        return Util.Selected1Curve()


    def execute(self, context):
        curve = Curves.Curve(context.active_object)

        nrSplines = len(curve.splines)
        nrSegments = 0
        nrEmptySplines = 0
        for spline in curve.splines:
            nrSegments += spline.nrSegments
            if spline.nrSegments < 1: nrEmptySplines += 1


        self.report({'INFO'}, "nrSplines: %d; nrSegments: %d; nrEmptySplines: %d" % (nrSplines, nrSegments, nrEmptySplines))

        return {'FINISHED'}



class OperatorCurveLength(bpy.types.Operator):
    bl_idname = "curvetools2.operatorcurvelength"
    bl_label = "Length"
    bl_description = "Calculates the length of the active/selected curve"


    @classmethod
    def poll(cls, context):
        return Util.Selected1Curve()


    def execute(self, context):
        curve = Curves.Curve(context.active_object)

        context.scene.curvetools.CurveLength = curve.length

        return {'FINISHED'}



class OperatorSplinesInfo(bpy.types.Operator):
    bl_idname = "curvetools2.operatorsplinesinfo"
    bl_label = "Info"
    bl_description = "Displays general info about the splines of the active/selected curve"


    @classmethod
    def poll(cls, context):
        return Util.Selected1Curve()


    def execute(self, context):
        curve = Curves.Curve(context.active_object)
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
    bl_idname = "curvetools2.operatorsegmentsinfo"
    bl_label = "Info"
    bl_description = "Displays general info about the segments of the active/selected curve"


    @classmethod
    def poll(cls, context):
        return Util.Selected1Curve()


    def execute(self, context):
        curve = Curves.Curve(context.active_object)
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
    bl_idname = "curvetools2.operatororigintospline0start"
    bl_label = "OriginToSpline0Start"
    bl_description = "Sets the origin of the active/selected curve to the starting point of the (first) spline. Nice for curve modifiers."


    @classmethod
    def poll(cls, context):
        return Util.Selected1Curve()


    def execute(self, context):
        blCurve = context.active_object
        blSpline = blCurve.data.splines[0]
        newOrigin = blCurve.matrix_world @ blSpline.bezier_points[0].co

        origOrigin = bpy.context.scene.cursor.location.copy()
        print("--", "origOrigin: %.6f, %.6f, %.6f" % (origOrigin.x, origOrigin.y, origOrigin.z))
        print("--", "newOrigin: %.6f, %.6f, %.6f" % (newOrigin.x, newOrigin.y, newOrigin.z))

        bpy.context.scene.cursor.location = newOrigin
        bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
        bpy.context.scene.cursor.location = origOrigin

        self.report({'INFO'}, "TODO: OperatorOriginToSpline0Start")

        return {'FINISHED'}



# 2 CURVES SELECTED
# #################
class OperatorIntersectCurves(bpy.types.Operator):
    bl_idname = "curvetools2.operatorintersectcurves"
    bl_label = "Intersect"
    bl_description = "Intersects selected curves"


    @classmethod
    def poll(cls, context):
        return Util.Selected2Curves()


    def execute(self, context):
        print("### TODO: OperatorIntersectCurves.execute()")

        algo = context.scene.curvetools.IntersectCurvesAlgorithm
        print("-- algo:", algo)


        mode = context.scene.curvetools.IntersectCurvesMode
        print("-- mode:", mode)
        # if mode == 'Split':
            # self.report({'WARNING'}, "'Split' mode is not implemented yet -- <<STOPPING>>")
            # return {'CANCELLED'}

        affect = context.scene.curvetools.IntersectCurvesAffect
        print("-- affect:", affect)


        curveIntersector = CurveIntersections.CurvesIntersector.FromSelection()
        rvIntersectionNrs = curveIntersector.CalcAndApplyIntersections()

        self.report({'INFO'}, "Active curve points: %d; other curve points: %d" % (rvIntersectionNrs[0], rvIntersectionNrs[1]))

        return {'FINISHED'}



class OperatorLoftCurves(bpy.types.Operator):
    bl_idname = "curvetools2.operatorloftcurves"
    bl_label = "Loft"
    bl_description = "Lofts selected curves"


    @classmethod
    def poll(cls, context):
        return Util.Selected2Curves()


    def execute(self, context):
        #print("### TODO: OperatorLoftCurves.execute()")

        loftedSurface = Surfaces.LoftedSurface.FromSelection()
        loftedSurface.AddToScene()

        self.report({'INFO'}, "OperatorLoftCurves.execute()")

        return {'FINISHED'}



class OperatorSweepCurves(bpy.types.Operator):
    bl_idname = "curvetools2.operatorsweepcurves"
    bl_label = "Sweep"
    bl_description = "Sweeps the active curve along to other curve (rail)"


    @classmethod
    def poll(cls, context):
        return Util.Selected2Curves()


    def execute(self, context):
        #print("### TODO: OperatorSweepCurves.execute()")

        sweptSurface = Surfaces.SweptSurface.FromSelection()
        sweptSurface.AddToScene()

        self.report({'INFO'}, "OperatorSweepCurves.execute()")

        return {'FINISHED'}



# 3 CURVES SELECTED
# #################
class OperatorBirail(bpy.types.Operator):
    bl_idname = "curvetools2.operatorbirail"
    bl_label = "Birail"
    bl_description = "Generates a birailed surface from 3 selected curves -- in order: rail1, rail2 and profile"


    @classmethod
    def poll(cls, context):
        return Util.Selected3Curves()


    def execute(self, context):
        birailedSurface = Surfaces.BirailedSurface.FromSelection()
        birailedSurface.AddToScene()

        self.report({'INFO'}, "OperatorBirail.execute()")

        return {'FINISHED'}



# 1 OR MORE CURVES SELECTED
# #########################
class OperatorSplinesSetResolution(bpy.types.Operator):
    bl_idname = "curvetools2.operatorsplinessetresolution"
    bl_label = "SplinesSetResolution"
    bl_description = "Sets the resolution of all splines"


    @classmethod
    def poll(cls, context):
        return Util.Selected1OrMoreCurves()


    def execute(self, context):
        splRes = context.scene.curvetools.SplineResolution
        selCurves = Util.GetSelectedCurves()

        for blCurve in selCurves:
            for spline in blCurve.data.splines:
                spline.resolution_u = splRes

        return {'FINISHED'}



class OperatorSplinesRemoveZeroSegment(bpy.types.Operator):
    bl_idname = "curvetools2.operatorsplinesremovezerosegment"
    bl_label = "SplinesRemoveZeroSegment"
    bl_description = "Removes splines with no segments -- they seem to creep up, sometimes.."


    @classmethod
    def poll(cls, context):
        return Util.Selected1OrMoreCurves()


    def execute(self, context):
        selCurves = Util.GetSelectedCurves()

        for blCurve in selCurves:
            curve = Curves.Curve(blCurve)
            nrSplines = curve.nrSplines

            splinesToRemove = []
            for spline in curve.splines:
                if len(spline.segments) < 1: splinesToRemove.append(spline)
            nrRemovedSplines = len(splinesToRemove)

            for spline in splinesToRemove: curve.splines.remove(spline)

            if nrRemovedSplines > 0: curve.RebuildInScene()

            self.report({'INFO'}, "Removed %d of %d splines" % (nrRemovedSplines, nrSplines))

        return {'FINISHED'}



class OperatorSplinesRemoveShort(bpy.types.Operator):
    bl_idname = "curvetools2.operatorsplinesremoveshort"
    bl_label = "SplinesRemoveShort"
    bl_description = "Removes splines with a length smaller than the threshold"


    @classmethod
    def poll(cls, context):
        return Util.Selected1OrMoreCurves()


    def execute(self, context):
        threshold = context.scene.curvetools.SplineRemoveLength
        selCurves = Util.GetSelectedCurves()

        for blCurve in selCurves:
            curve = Curves.Curve(blCurve)
            nrSplines = curve.nrSplines

            nrRemovedSplines = curve.RemoveShortSplines(threshold)
            if nrRemovedSplines > 0: curve.RebuildInScene()

            self.report({'INFO'}, "Removed %d of %d splines" % (nrRemovedSplines, nrSplines))

        return {'FINISHED'}



class OperatorSplinesJoinNeighbouring(bpy.types.Operator):
    bl_idname = "curvetools2.operatorsplinesjoinneighbouring"
    bl_label = "SplinesJoinNeighbouring"
    bl_description = "Joins neighbouring splines within a distance smaller than the threshold"


    @classmethod
    def poll(cls, context):
        return Util.Selected1OrMoreCurves()


    def execute(self, context):
        selCurves = Util.GetSelectedCurves()

        for blCurve in selCurves:
            curve = Curves.Curve(blCurve)
            nrSplines = curve.nrSplines

            threshold = context.scene.curvetools.SplineJoinDistance
            startEnd = context.scene.curvetools.SplineJoinStartEnd
            mode = context.scene.curvetools.SplineJoinMode

            nrJoins = curve.JoinNeighbouringSplines(startEnd, threshold, mode)
            if nrJoins > 0: curve.RebuildInScene()

            self.report({'INFO'}, "Applied %d joins on %d splines; resulting nrSplines: %d" % (nrJoins, nrSplines, curve.nrSplines))

        return {'FINISHED'}
        
def subdivide_cubic_bezier(p1, p2, p3, p4, t):
    p12 = (p2 - p1) * t + p1
    p23 = (p3 - p2) * t + p2
    p34 = (p4 - p3) * t + p3
    p123 = (p23 - p12) * t + p12
    p234 = (p34 - p23) * t + p23
    p1234 = (p234 - p123) * t + p123
    return [p12, p123, p1234, p234, p34]
        
def SurfaceFromBezier(surfacedata, points, center):
    use_enter_edit_mode = bpy.context.preferences.edit.use_enter_edit_mode

    len_points = len(points) - 1
    
    if len_points % 2 == 0:
        h = subdivide_cubic_bezier(
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
    
    print(center)

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
        
    bpy.context.preferences.edit.use_enter_edit_mode = use_enter_edit_mode

def SurfaceFrom4point(surfacedata, point1, point2, point3, point4):
    use_enter_edit_mode = bpy.context.preferences.edit.use_enter_edit_mode

    # 1
    surfacespline1 = surfacedata.splines.new(type='NURBS')
    surfacespline1.points.add(3)
    surfacespline1.points[0].co = [point1.co.x, point1.co.y, point1.co.z, 1]
    surfacespline1.points[1].co = [point1.handle_left.x, point1.handle_left.y, point1.handle_left.z, 1]
    surfacespline1.points[2].co = [point4.handle_right.x, point4.handle_right.y, point4.handle_right.z, 1]
    surfacespline1.points[3].co = [point4.co.x, point4.co.y, point4.co.z, 1]
    for p in surfacespline1.points:
        p.select = True
    surfacespline1.use_endpoint_u = True
    surfacespline1.use_endpoint_v = True
    
    # 2
    surfacespline2 = surfacedata.splines.new(type='NURBS')
    surfacespline2.points.add(3)
    surfacespline2.points[0].co = [point1.handle_right.x, point1.handle_right.y, point1.handle_right.z, 1]
    surfacespline2.points[1].co = [(point1.handle_right.x + point4.handle_left.x)/2,
                                   (point1.handle_right.y + point4.handle_left.y)/2,
                                   (point1.handle_right.z + point4.handle_left.z)/2, 1]
    surfacespline2.points[2].co = [(point4.handle_left.x + point1.handle_right.x)/2,
                                   (point4.handle_left.y + point1.handle_right.y)/2,
                                   (point4.handle_left.z + point1.handle_right.z)/2, 1]
    surfacespline2.points[3].co = [point4.handle_left.x, point4.handle_left.y, point4.handle_left.z, 1]
    for p in surfacespline2.points:
        p.select = True
    surfacespline2.use_endpoint_u = True
    surfacespline2.use_endpoint_v = True

     # 3
    surfacespline3 = surfacedata.splines.new(type='NURBS')
    surfacespline3.points.add(3)
    surfacespline3.points[0].co = [point2.handle_left.x, point2.handle_left.y, point2.handle_left.z, 1]
    surfacespline3.points[1].co = [(point2.handle_left.x + point3.handle_right.x)/2,
                                   (point2.handle_left.y + point3.handle_right.y)/2,
                                   (point2.handle_left.z + point3.handle_right.z)/2, 1]
    surfacespline3.points[2].co = [(point3.handle_right.x + point2.handle_left.x)/2,
                                   (point3.handle_right.y + point2.handle_left.y)/2,
                                   (point3.handle_right.z + point2.handle_left.z)/2, 1]
    surfacespline3.points[3].co = [point3.handle_right.x, point3.handle_right.y, point3.handle_right.z, 1]
    for p in surfacespline3.points:
        p.select = True
    surfacespline3.use_endpoint_u = True
    surfacespline3.use_endpoint_v = True

     # 4
    surfacespline4 = surfacedata.splines.new(type='NURBS')
    surfacespline4.points.add(3)
    surfacespline4.points[0].co = [point2.co.x, point2.co.y, point2.co.z, 1]
    surfacespline4.points[1].co = [point2.handle_right.x, point2.handle_right.y, point2.handle_right.z, 1]
    surfacespline4.points[2].co = [point3.handle_left.x, point3.handle_left.y, point3.handle_left.z, 1]
    surfacespline4.points[3].co = [point3.co.x, point3.co.y, point3.co.z, 1]
    for p in surfacespline4.points:
        p.select = True
    surfacespline4.use_endpoint_u = True
    surfacespline4.use_endpoint_v = True
        
    bpy.ops.object.mode_set(mode = 'EDIT') 
    bpy.ops.curve.make_segment()
    
    for s in surfacedata.splines:
        s.order_u = 4
        s.order_v = 4
        s.resolution_u = 4
        s.resolution_v = 4
        for p in s.points:
            p.select = False
        
    bpy.context.preferences.edit.use_enter_edit_mode = use_enter_edit_mode

class ConvertBezierRectangleToSurface(bpy.types.Operator):
    bl_idname = "curvetools2.convert_bezier_rectangle_to_surface"
    bl_label = "Convert Bezier Rectangle To Surface"
    bl_description = "Convert Bezier Rectangle To Surface"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return Util.Selected1Curve()

    def execute(self, context):
        # main function
        active_object = context.active_object
        splines = active_object.data.splines
        
        surfacedata = bpy.data.curves.new('Surface', type='SURFACE')
        surfaceobject = object_utils.object_data_add(context, surfacedata)
        surfaceobject.matrix_world = active_object.matrix_world
        surfaceobject.rotation_euler = active_object.rotation_euler
        surfacedata.dimensions = '3D'
        
        n = 0
        pp = []
        for s in splines:
            for p in s.bezier_points:
                pp.append(p)
                n += 1
        
        SurfaceFrom4point(surfacedata, pp[0], pp[1], pp[2], pp[3])
                          
        splines = surfaceobject.data.splines
        for s in splines:
            s.order_u = 4
            s.order_v = 4
            s.resolution_u = 4
            s.resolution_v = 4

        return {'FINISHED'}

class ConvertMeshToBezier(bpy.types.Operator):
    bl_idname = "curvetools2.convert_mesh_to_bezier"
    bl_label = "Convert Mesh to Bezier"
    bl_description = "Convert Mesh to Bezier"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return Util.Selected1Mesh()

    def execute(self, context):
        # main function
        active_object = context.active_object
        meshdata = active_object.data
        curvedata = bpy.data.curves.new('Curve' + active_object.name, type='CURVE')
        curveobject = object_utils.object_data_add(context, curvedata)
        curvedata.dimensions = '3D'
        
        for poly in meshdata.polygons:
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

class ConvertBezierToSurface(bpy.types.Operator):
    bl_idname = "curvetools2.convert_bezier_to_surface"
    bl_label = "Convert Bezier to Surface"
    bl_description = "Convert Bezier to Surface"
    bl_options = {'REGISTER', 'UNDO'}

    Center : BoolProperty(
            name="Center",
            default=False,
            description="Consider center points"
            )
            
    def draw(self, context):
        layout = self.layout

         # general options
        col = layout.column()
        col.prop(self, 'Center')
    
    @classmethod
    def poll(cls, context):
        return context.scene is not None

    def execute(self, context):
        # main function
        use_enter_edit_mode = bpy.context.preferences.edit.use_enter_edit_mode
        active_object = context.active_object
        curvedata = active_object.data
        
        surfacedata = bpy.data.curves.new('Surface', type='SURFACE')
        surfaceobject = object_utils.object_data_add(context, surfacedata)
        surfaceobject.matrix_world = active_object.matrix_world
        surfaceobject.rotation_euler = active_object.rotation_euler
        surfacedata.dimensions = '3D'
        
        for spline in curvedata.splines:
            SurfaceFromBezier(surfacedata, spline.bezier_points, self.Center)

        return {'FINISHED'}

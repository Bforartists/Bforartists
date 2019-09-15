import time
import threading

import bpy
from bpy.props import *
from bpy_extras import object_utils, view3d_utils
from mathutils import  *
from math import  *

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
        return Util.Selected2OrMoreCurves()


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
                        curveIntersector = CurveIntersections.CurvesIntersector.FromSelection()
                        rvIntersectionNrs = curveIntersector.CalcAndApplyIntersections()

                        self.report({'INFO'}, "Active curve points: %d; other curve points: %d" % (rvIntersectionNrs[0], rvIntersectionNrs[1]))
        
        for obj in selected_objects:
            obj.select_set(True)
        
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

class ConvertSelectedFacesToBezier(bpy.types.Operator):
    bl_idname = "curvetools2.convert_selected_face_to_bezier"
    bl_label = "Convert selected faces to Bezier"
    bl_description = "Convert selected faces to Bezier"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return Util.Selected1Mesh()

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
        return context.scene is not None

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


def draw_annotation_bezier_spline(frame, spline, matrix_world, select):
    stroke = frame.strokes.new()
    stroke.display_mode = '3DSPACE'
    len_points = len(spline.bezier_points)
    for i in range(0, len_points - 1):
        stroke.points.add(1)
        stroke.points[-1].co = matrix_world @ spline.bezier_points[i].co
        for t in range(0, 100, 2):
            h = subdivide_cubic_bezier(spline.bezier_points[i].co,
                                       spline.bezier_points[i].handle_right,
                                       spline.bezier_points[i + 1].handle_left,
                                       spline.bezier_points[i + 1].co,
                                       t/100)
            stroke.points.add(1)
            stroke.points[-1].co = matrix_world @ h[2]
    if spline.use_cyclic_u:
        stroke.points.add(1)
        stroke.points[-1].co = matrix_world @ spline.bezier_points[len_points - 1].co
        for t in range(0, 100, 2):
            h = subdivide_cubic_bezier(spline.bezier_points[len_points - 1].co,
                                       spline.bezier_points[len_points - 1].handle_right,
                                       spline.bezier_points[0].handle_left,
                                       spline.bezier_points[0].co,
                                       t/100)
            stroke.points.add(1)
            stroke.points[-1].co = matrix_world @ h[2]
        stroke.points.add(1)
        stroke.points[-1].co = matrix_world @ spline.bezier_points[0].co

def draw_annotation_spline(frame, spline, matrix_world, select):
    stroke = frame.strokes.new()
    stroke.display_mode = '3DSPACE'
    len_points = len(spline.points)
    for i in range(0, len_points - 1):
        stroke.points.add(1)
        stroke.points[-1].co = matrix_world @ Vector((spline.points[i].co.x, spline.points[i].co.y, spline.points[i].co.z))
        for t in range(0, 100, 2):
            x = (spline.points[i].co.x + t / 100 * spline.points[i + 1].co.x) / (1 + t / 100)
            y = (spline.points[i].co.y + t / 100 * spline.points[i + 1].co.y) / (1 + t / 100)
            z = (spline.points[i].co.z + t / 100 * spline.points[i + 1].co.z) / (1 + t / 100)
            stroke.points.add(1)
            stroke.points[-1].co = matrix_world @ Vector((x, y, z))
    if spline.use_cyclic_u:
        stroke.points.add(1)
        stroke.points[-1].co = matrix_world @ Vector((spline.points[len_points - 1].co.x, spline.points[len_points - 1].co.y, spline.points[len_points - 1].co.z))
        for t in range(0, 100, 2):
            x = (spline.points[len_points - 1].co.x + t / 100 * spline.points[0].co.x) / (1 + t / 100)
            y = (spline.points[len_points - 1].co.y + t / 100 * spline.points[0].co.y) / (1 + t / 100)
            z = (spline.points[len_points - 1].co.z + t / 100 * spline.points[0].co.z) / (1 + t / 100)
            stroke.points.add(1)
            stroke.points[-1].co = matrix_world @ Vector((x, y, z))
        stroke.points.add(1)
        stroke.points[-1].co = matrix_world @ Vector((spline.points[0].co.x, spline.points[0].co.y, spline.points[0].co.z))

def click(self, context, event, select):
    bpy.ops.object.mode_set(mode = 'EDIT')
    for object in context.selected_objects:
        matrix_world = object.matrix_world
        if object.type == 'CURVE':
            curvedata = object.data
            
            radius = bpy.context.scene.curvetools.PathFinderRadius
            
            for spline in curvedata.splines:
                for bezier_point in spline.bezier_points:
                    factor = 0
                    co = matrix_world @ bezier_point.co
                    if co.x > (self.location3D.x - radius):
                        factor += 1
                    if co.x < (self.location3D.x + radius):
                        factor += 1
                    if co.y > (self.location3D.y - radius):
                        factor += 1
                    if co.y < (self.location3D.y + radius):
                        factor += 1
                    if co.z > (self.location3D.z - radius):
                        factor += 1
                    if co.z < (self.location3D.z + radius):
                        factor += 1
                    if factor == 6:
                        
                        draw_annotation_bezier_spline(self.frame, spline, matrix_world, select)

                        for bezier_point in spline.bezier_points:
                            bezier_point.select_control_point = select
                            bezier_point.select_left_handle = select
                            bezier_point.select_right_handle = select
                            
            for spline in curvedata.splines:
                for point in spline.points:
                    factor = 0
                    co = matrix_world @ Vector((point.co.x, point.co.y, point.co.z))
                    if co.x > (self.location3D.x - radius):
                        factor += 1
                    if co.x < (self.location3D.x + radius):
                        factor += 1
                    if co.y > (self.location3D.y - radius):
                        factor += 1
                    if co.y < (self.location3D.y + radius):
                        factor += 1
                    if co.z > (self.location3D.z - radius):
                        factor += 1
                    if co.z < (self.location3D.z + radius):
                        factor += 1
                    if factor == 6:
                        
                        draw_annotation_spline(self.frame, spline, matrix_world, select)
                        
                        for point in spline.points:
                            point.select = select    

class PathFinder(bpy.types.Operator):
    bl_idname = "curvetools2.pathfinder"
    bl_label = "Path Finder"
    bl_description = "Path Finder"
    bl_options = {'REGISTER', 'UNDO'}
    
    x: IntProperty(name="x", description="x")
    y: IntProperty(name="y", description="y")
    location3D: FloatVectorProperty(name = "",
                description = "Start location",
                default = (0.0, 0.0, 0.0),
                subtype = 'XYZ')
    
    frame : object
    gpencil : object
    layer : object
    
    def __init__(self):
        bpy.context.space_data.overlay.show_curve_handles = False
        self.report({'INFO'}, "ESC or TAB - cancel")
        print("Start PathFinder")

    def __del__(self):
        bpy.context.space_data.overlay.show_curve_handles = True
        self.layer.clear()
        self.report({'INFO'}, "PathFinder deactivated")
        print("End PathFinder")
        
    def execute(self, context):
        bpy.ops.object.mode_set(mode = 'EDIT')
        
        self.gpencil = bpy.data.grease_pencils[0]

        self.layer = self.gpencil.layers.new("PathFinder", set_active=True)
        self.frame = self.layer.frames.new(bpy.context.scene.frame_current)
    
    def modal(self, context, event):
        if event.type in {'DEL', 'X'}:
            bpy.ops.curve.delete(type='VERT')
            self.frame.clear()
        
        #if event.ctrl and event.type == 'Z':
        #    bpy.ops.ed.undo()

        #if event.shift and event.type == 'Z':
        #    bpy.ops.ed.redo()

        elif event.type == 'LEFTMOUSE':
            click(self, context, event, True)
                                    
        #elif event.type == 'RIGHTMOUSE':
        #   click(self, context, event, False)
            
        elif event.type == 'A':
            bpy.ops.curve.select_all(action='DESELECT')
            self.frame.clear()
            
        elif event.type == 'MOUSEMOVE':  # 
            self.x = event.mouse_x
            self.y = event.mouse_y
            region = bpy.context.region
            rv3d = bpy.context.space_data.region_3d
            self.location3D = view3d_utils.region_2d_to_location_3d(
                region,
                rv3d,
                (event.mouse_region_x, event.mouse_region_y),
                (0.0, 0.0, 0.0)
                )       
        
        elif event.type in {'ESC', 'TAB'}:  # Cancel
            return {'CANCELLED'}

        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        self.execute(context)
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

import bpy
from mathutils import *


def GetSelectedCurves():
    rvList = []

    for obj in bpy.context.selected_objects:
        if obj.type == "CURVE": rvList.append(obj)

    return rvList


def Selected1Curve():
    if len(GetSelectedCurves()) == 1:
        return (bpy.context.active_object.type == "CURVE")

    return False


def Selected1SingleSplineCurve():
    if Selected1Curve():
        return (len(bpy.context.active_object.data.splines) == 1)

    return False


def Selected2Curves():
    if len(GetSelectedCurves()) == 2:
        return (bpy.context.active_object.type == "CURVE")

    return False


def Selected3Curves():
    if len(GetSelectedCurves()) == 3:
        return (bpy.context.active_object.type == "CURVE")

    return False


def Selected1OrMoreCurves():
    if len(GetSelectedCurves()) > 0:
        return (bpy.context.active_object.type == "CURVE")

    return False


def GetToolsRegion():
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            for region in area.regions:
                if region.type == 'TOOLS': return region

    return None


def GetFirstRegionView3D():
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            return area.spaces[0].region_3d

    return None


def LogFirstRegionView3D():
    print("LogFirstRegionView3D()")
    regionView3D = GetFirstRegionView3D()
    if regionView3D is None:
        print("--", "ERROR:", "regionView3D is None")
        return

    print("--", "view_matrix:")
    print("--", "--", regionView3D.view_matrix)
    print("--", "view_location:")
    print("--", "--", regionView3D.view_location)


class Intersection:
    # listIP: list of BezierSplineIntersectionPoint
    # return: list of splines
    @staticmethod
    def GetBezierSplines(listIP):
        rvList = []

        for ip in listIP:
            if not (ip.spline in rvList): rvList.append(ip.spline)

        return rvList


    # listIP: list of BezierSplineIntersectionPoint
    # return: list of segments
    @staticmethod
    def GetBezierSegments(listIP, spline):
        rvList = []

        for ip in listIP:
            if not ip.spline is spline: continue

            segIP = ip.bezierSegmentIntersectionPoint
            if not (segIP.segment in rvList): rvList.append(segIP.segment)

        return rvList


    # listIP: list of BezierSplineIntersectionPoint
    # return: list of floats (not necessarily ordered)
    @staticmethod
    def GetBezierSegmentParameters(listIP, segment):
        rvList = []

        for ip in listIP:
            segIP = ip.bezierSegmentIntersectionPoint
            if not segIP.segment is segment: continue

            rvList.append(segIP.parameter)

        return rvList

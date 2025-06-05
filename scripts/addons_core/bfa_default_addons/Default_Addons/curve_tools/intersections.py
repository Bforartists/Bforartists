# SPDX-FileCopyrightText: 2019-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

import bpy
from . import mathematics
from . import curves
from . import util

from mathutils import Vector

algoPOV = None
algoDIR = None


class BezierSegmentIntersectionPoint:
    def __init__(self, segment, parameter, intersectionPoint):
        self.segment = segment
        self.parameter = parameter
        self.intersectionPoint = intersectionPoint


class BezierSegmentsIntersector:
    def __init__(self, segment1, segment2, worldMatrix1, worldMatrix2):
        self.segment1 = segment1
        self.segment2 = segment2
        self.worldMatrix1 = worldMatrix1
        self.worldMatrix2 = worldMatrix2

    def CalcFirstIntersection(self, nrSamples1, nrSamples2):
        algorithm = bpy.context.scene.curvetools.IntersectCurvesAlgorithm

        if algorithm == '3D':
            return self.CalcFirstRealIntersection3D(nrSamples1, nrSamples2)

        if algorithm == 'From_View':
            global algoDIR
            if algoDIR is not None:
                return self.CalcFirstRealIntersectionFromViewDIR(nrSamples1, nrSamples2)

            global algoPOV
            if algoPOV is not None:
                return self.CalcFirstRealIntersectionFromViewPOV(nrSamples1, nrSamples2)

        return None

    def CalcFirstIntersection3D(self, nrSamples1, nrSamples2):
        fltNrSamples1 = float(nrSamples1)
        fltNrSamples2 = float(nrSamples2)

        limitDistance = bpy.context.scene.curvetools.LimitDistance

        for iSample1 in range(nrSamples1):
            segPar10 = float(iSample1) / fltNrSamples1
            segPar11 = float(iSample1 + 1) / fltNrSamples1
            P0 = self.worldMatrix1 @ self.segment1.CalcPoint(parameter=segPar10)
            P1 = self.worldMatrix1 @ self.segment1.CalcPoint(parameter=segPar11)

            for iSample2 in range(nrSamples2):
                segPar20 = float(iSample2) / fltNrSamples2
                segPar21 = float(iSample2 + 1) / fltNrSamples2
                Q0 = self.worldMatrix2 @ self.segment2.CalcPoint(parameter=segPar20)
                Q1 = self.worldMatrix2 @ self.segment2.CalcPoint(parameter=segPar21)

                intersectionPointData = mathematics.CalcIntersectionPointLineSegments(P0, P1, Q0, Q1, limitDistance)
                if intersectionPointData is None:
                    continue

                intersectionSegment1Parameter = segPar10 + (intersectionPointData[0] / fltNrSamples1)
                intersectionPoint1 = BezierSegmentIntersectionPoint(self.segment1,
                                                                    intersectionSegment1Parameter,
                                                                    intersectionPointData[2])

                intersectionSegment2Parameter = segPar20 + (intersectionPointData[1] / fltNrSamples2)
                intersectionPoint2 = BezierSegmentIntersectionPoint(self.segment2,
                                                                    intersectionSegment2Parameter,
                                                                    intersectionPointData[3])

                return [intersectionPoint1, intersectionPoint2]

        return None

    def CalcFirstRealIntersection3D(self, nrSamples1, nrSamples2):
        fltNrSamples1 = float(nrSamples1)
        fltNrSamples2 = float(nrSamples2)

        limitDistance = bpy.context.scene.curvetools.LimitDistance

        for iSample1 in range(nrSamples1):
            segPar10 = float(iSample1) / fltNrSamples1
            segPar11 = float(iSample1 + 1) / fltNrSamples1
            P0 = self.worldMatrix1 @ self.segment1.CalcPoint(parameter=segPar10)
            P1 = self.worldMatrix1 @ self.segment1.CalcPoint(parameter=segPar11)

            for iSample2 in range(nrSamples2):
                segPar20 = float(iSample2) / fltNrSamples2
                segPar21 = float(iSample2 + 1) / fltNrSamples2
                Q0 = self.worldMatrix2 @ self.segment2.CalcPoint(parameter=segPar20)
                Q1 = self.worldMatrix2 @ self.segment2.CalcPoint(parameter=segPar21)

                intersectionPointData = mathematics.CalcIntersectionPointLineSegments(P0, P1, Q0, Q1, limitDistance)
                if intersectionPointData is None:
                    continue

                # intersection point can't be an existing point
                intersectionSegment1Parameter = segPar10 + (intersectionPointData[0] / (fltNrSamples1))
                worldPoint1 = self.worldMatrix1 @ self.segment1.CalcPoint(parameter=intersectionSegment1Parameter)
                if (mathematics.IsSamePoint(P0, worldPoint1, limitDistance)) or \
                   (mathematics.IsSamePoint(P1, worldPoint1, limitDistance)):

                    intersectionPoint1 = None
                else:
                    intersectionPoint1 = BezierSegmentIntersectionPoint(self.segment1,
                                                                        intersectionSegment1Parameter,
                                                                        worldPoint1)

                intersectionSegment2Parameter = segPar20 + (intersectionPointData[1] / (fltNrSamples2))
                worldPoint2 = self.worldMatrix2 @ self.segment2.CalcPoint(parameter=intersectionSegment2Parameter)
                if (mathematics.IsSamePoint(Q0, worldPoint2, limitDistance)) or \
                   (mathematics.IsSamePoint(Q1, worldPoint2, limitDistance)):

                    intersectionPoint2 = None
                else:
                    intersectionPoint2 = BezierSegmentIntersectionPoint(self.segment2,
                                                                        intersectionSegment2Parameter,
                                                                        worldPoint2)

                return [intersectionPoint1, intersectionPoint2]

        return None

    def CalcFirstIntersectionFromViewDIR(self, nrSamples1, nrSamples2):
        global algoDIR

        fltNrSamples1 = float(nrSamples1)
        fltNrSamples2 = float(nrSamples2)

        for iSample1 in range(nrSamples1):
            segPar10 = float(iSample1) / fltNrSamples1
            segPar11 = float(iSample1 + 1) / fltNrSamples1
            P0 = self.worldMatrix1 @ self.segment1.CalcPoint(parameter=segPar10)
            P1 = self.worldMatrix1 @ self.segment1.CalcPoint(parameter=segPar11)

            for iSample2 in range(nrSamples2):
                segPar20 = float(iSample2) / fltNrSamples2
                segPar21 = float(iSample2 + 1) / fltNrSamples2
                Q0 = self.worldMatrix2 @ self.segment2.CalcPoint(parameter=segPar20)
                Q1 = self.worldMatrix2 @ self.segment2.CalcPoint(parameter=segPar21)

                intersectionPointData = mathematics.CalcIntersectionPointsLineSegmentsDIR(P0, P1, Q0, Q1, algoDIR)
                if intersectionPointData is None:
                    continue

                intersectionSegment1Parameter = segPar10 + (intersectionPointData[0] / fltNrSamples1)
                worldPoint1 = self.worldMatrix1 @ self.segment1.CalcPoint(parameter=intersectionSegment1Parameter)
                intersectionPoint1 = BezierSegmentIntersectionPoint(self.segment1,
                                                                    intersectionSegment1Parameter,
                                                                    worldPoint1)

                intersectionSegment2Parameter = segPar20 + (intersectionPointData[1] / fltNrSamples2)
                worldPoint2 = self.worldMatrix2 @ self.segment2.CalcPoint(parameter=intersectionSegment2Parameter)
                intersectionPoint2 = BezierSegmentIntersectionPoint(self.segment2,
                                                                    intersectionSegment2Parameter,
                                                                    worldPoint2)

                return [intersectionPoint1, intersectionPoint2]

        return None

    def CalcFirstRealIntersectionFromViewDIR(self, nrSamples1, nrSamples2):
        global algoDIR

        fltNrSamples1 = float(nrSamples1)
        fltNrSamples2 = float(nrSamples2)

        limitDistance = bpy.context.scene.curvetools.LimitDistance

        for iSample1 in range(nrSamples1):
            segPar10 = float(iSample1) / fltNrSamples1
            segPar11 = float(iSample1 + 1) / fltNrSamples1
            P0 = self.worldMatrix1 @ self.segment1.CalcPoint(parameter=segPar10)
            P1 = self.worldMatrix1 @ self.segment1.CalcPoint(parameter=segPar11)

            for iSample2 in range(nrSamples2):
                segPar20 = float(iSample2) / fltNrSamples2
                segPar21 = float(iSample2 + 1) / fltNrSamples2
                Q0 = self.worldMatrix2 @ self.segment2.CalcPoint(parameter=segPar20)
                Q1 = self.worldMatrix2 @ self.segment2.CalcPoint(parameter=segPar21)

                intersectionPointData = mathematics.CalcIntersectionPointsLineSegmentsDIR(P0, P1, Q0, Q1, algoDIR)
                if intersectionPointData is None:
                    continue

                # intersection point can't be an existing point
                intersectionSegment1Parameter = segPar10 + (intersectionPointData[0] / (fltNrSamples1))
                worldPoint1 = self.worldMatrix1 @ self.segment1.CalcPoint(parameter=intersectionSegment1Parameter)
                if (mathematics.IsSamePoint(P0, worldPoint1, limitDistance)) or \
                   (mathematics.IsSamePoint(P1, worldPoint1, limitDistance)):

                    intersectionPoint1 = None
                else:
                    intersectionPoint1 = BezierSegmentIntersectionPoint(self.segment1,
                                                                        intersectionSegment1Parameter,
                                                                        worldPoint1)

                intersectionSegment2Parameter = segPar20 + (intersectionPointData[1] / (fltNrSamples2))
                worldPoint2 = self.worldMatrix2 @ self.segment2.CalcPoint(parameter=intersectionSegment2Parameter)
                if (mathematics.IsSamePoint(Q0, worldPoint2, limitDistance)) or \
                   (mathematics.IsSamePoint(Q1, worldPoint2, limitDistance)):

                    intersectionPoint2 = None
                else:
                    intersectionPoint2 = BezierSegmentIntersectionPoint(self.segment2,
                                                                        intersectionSegment2Parameter,
                                                                        worldPoint2)

                return [intersectionPoint1, intersectionPoint2]

        return None

    def CalcFirstIntersectionFromViewPOV(self, nrSamples1, nrSamples2):
        global algoPOV

        fltNrSamples1 = float(nrSamples1)
        fltNrSamples2 = float(nrSamples2)

        for iSample1 in range(nrSamples1):
            segPar10 = float(iSample1) / fltNrSamples1
            segPar11 = float(iSample1 + 1) / fltNrSamples1
            P0 = self.worldMatrix1 @ self.segment1.CalcPoint(parameter=segPar10)
            P1 = self.worldMatrix1 @ self.segment1.CalcPoint(parameter=segPar11)

            for iSample2 in range(nrSamples2):
                segPar20 = float(iSample2) / fltNrSamples2
                segPar21 = float(iSample2 + 1) / fltNrSamples2
                Q0 = self.worldMatrix2 @ self.segment2.CalcPoint(parameter=segPar20)
                Q1 = self.worldMatrix2 @ self.segment2.CalcPoint(parameter=segPar21)

                intersectionPointData = mathematics.CalcIntersectionPointsLineSegmentsPOV(P0, P1, Q0, Q1, algoPOV)
                if intersectionPointData is None:
                    continue

                intersectionSegment1Parameter = segPar10 + (intersectionPointData[0] / fltNrSamples1)
                worldPoint1 = self.worldMatrix1 @ self.segment1.CalcPoint(parameter=intersectionSegment1Parameter)
                intersectionPoint1 = BezierSegmentIntersectionPoint(self.segment1,
                                                                    intersectionSegment1Parameter,
                                                                    worldPoint1)

                intersectionSegment2Parameter = segPar20 + (intersectionPointData[1] / fltNrSamples2)
                worldPoint2 = self.worldMatrix2 @ self.segment2.CalcPoint(parameter=intersectionSegment2Parameter)
                intersectionPoint2 = BezierSegmentIntersectionPoint(self.segment2,
                                                                    intersectionSegment2Parameter,
                                                                    worldPoint2)

                return [intersectionPoint1, intersectionPoint2]

        return None

    def CalcFirstRealIntersectionFromViewPOV(self, nrSamples1, nrSamples2):
        global algoPOV

        fltNrSamples1 = float(nrSamples1)
        fltNrSamples2 = float(nrSamples2)

        limitDistance = bpy.context.scene.curvetools.LimitDistance

        for iSample1 in range(nrSamples1):
            segPar10 = float(iSample1) / fltNrSamples1
            segPar11 = float(iSample1 + 1) / fltNrSamples1
            P0 = self.worldMatrix1 @ self.segment1.CalcPoint(parameter=segPar10)
            P1 = self.worldMatrix1 @ self.segment1.CalcPoint(parameter=segPar11)

            for iSample2 in range(nrSamples2):
                segPar20 = float(iSample2) / fltNrSamples2
                segPar21 = float(iSample2 + 1) / fltNrSamples2
                Q0 = self.worldMatrix2 @ self.segment2.CalcPoint(parameter=segPar20)
                Q1 = self.worldMatrix2 @ self.segment2.CalcPoint(parameter=segPar21)

                intersectionPointData = mathematics.CalcIntersectionPointsLineSegmentsPOV(P0, P1, Q0, Q1, algoPOV)
                if intersectionPointData is None:
                    continue

                # intersection point can't be an existing point
                intersectionSegment1Parameter = segPar10 + (intersectionPointData[0] / fltNrSamples1)
                worldPoint1 = self.worldMatrix1 @ self.segment1.CalcPoint(parameter=intersectionSegment1Parameter)
                if (mathematics.IsSamePoint(P0, worldPoint1, limitDistance)) or \
                   (mathematics.IsSamePoint(P1, worldPoint1, limitDistance)):

                    intersectionPoint1 = None
                else:
                    intersectionPoint1 = BezierSegmentIntersectionPoint(self.segment1,
                                                                        intersectionSegment1Parameter,
                                                                        worldPoint1)

                intersectionSegment2Parameter = segPar20 + (intersectionPointData[1] / fltNrSamples2)
                worldPoint2 = self.worldMatrix2 @ self.segment2.CalcPoint(parameter=intersectionSegment2Parameter)
                if (mathematics.IsSamePoint(Q0, worldPoint2, limitDistance)) or \
                   (mathematics.IsSamePoint(Q1, worldPoint2, limitDistance)):

                    intersectionPoint2 = None
                else:
                    intersectionPoint2 = BezierSegmentIntersectionPoint(self.segment2,
                                                                        intersectionSegment2Parameter,
                                                                        worldPoint2)

                return [intersectionPoint1, intersectionPoint2]

        return None

    def CalcIntersections(self, nrSamples1, nrSamples2):
        algorithm = bpy.context.scene.curvetools.IntersectCurvesAlgorithm

        if algorithm == '3D':
            return self.CalcIntersections3D(nrSamples1, nrSamples2)

        if algorithm == 'From_View':
            global algoDIR
            if algoDIR is not None:
                return self.CalcIntersectionsFromViewDIR(nrSamples1, nrSamples2)

            global algoPOV
            if algoPOV is not None:
                return self.CalcIntersectionsFromViewPOV(nrSamples1, nrSamples2)

        return [[], []]

    def CalcIntersections3D(self, nrSamples1, nrSamples2):
        rvIntersections1 = []
        rvIntersections2 = []

        fltNrSamples1 = float(nrSamples1)
        fltNrSamples2 = float(nrSamples2)

        limitDistance = bpy.context.scene.curvetools.LimitDistance

        for iSample1 in range(nrSamples1):
            segPar10 = float(iSample1) / fltNrSamples1
            segPar11 = float(iSample1 + 1) / fltNrSamples1
            P0 = self.worldMatrix1 @ self.segment1.CalcPoint(parameter=segPar10)
            P1 = self.worldMatrix1 @ self.segment1.CalcPoint(parameter=segPar11)

            for iSample2 in range(nrSamples2):
                segPar20 = float(iSample2) / fltNrSamples2
                segPar21 = float(iSample2 + 1) / fltNrSamples2
                Q0 = self.worldMatrix2 @ self.segment2.CalcPoint(parameter=segPar20)
                Q1 = self.worldMatrix2 @ self.segment2.CalcPoint(parameter=segPar21)

                intersectionPointData = mathematics.CalcIntersectionPointLineSegments(P0, P1, Q0, Q1, limitDistance)
                if intersectionPointData is None:
                    continue

                intersectionSegment1Parameter = segPar10 + (intersectionPointData[0] / fltNrSamples1)
                worldPoint1 = self.worldMatrix1 @ self.segment1.CalcPoint(parameter=intersectionSegment1Parameter)
                intersectionPoint1 = BezierSegmentIntersectionPoint(self.segment1,
                                                                    intersectionSegment1Parameter,
                                                                    worldPoint1)
                rvIntersections1.append(intersectionPoint1)

                intersectionSegment2Parameter = segPar20 + (intersectionPointData[1] / fltNrSamples2)
                worldPoint2 = self.worldMatrix2 @ self.segment2.CalcPoint(parameter=intersectionSegment2Parameter)
                intersectionPoint2 = BezierSegmentIntersectionPoint(self.segment2,
                                                                    intersectionSegment2Parameter,
                                                                    worldPoint2)
                rvIntersections2.append(intersectionPoint2)

        return [rvIntersections1, rvIntersections2]

    def CalcIntersectionsFromViewDIR(self, nrSamples1, nrSamples2):
        global algoDIR

        rvIntersections1 = []
        rvIntersections2 = []

        fltNrSamples1 = float(nrSamples1)
        fltNrSamples2 = float(nrSamples2)

        for iSample1 in range(nrSamples1):
            segPar10 = float(iSample1) / fltNrSamples1
            segPar11 = float(iSample1 + 1) / fltNrSamples1
            P0 = self.worldMatrix1 @ self.segment1.CalcPoint(parameter=segPar10)
            P1 = self.worldMatrix1 @ self.segment1.CalcPoint(parameter=segPar11)

            for iSample2 in range(nrSamples2):
                segPar20 = float(iSample2) / fltNrSamples2
                segPar21 = float(iSample2 + 1) / fltNrSamples2
                Q0 = self.worldMatrix2 @ self.segment2.CalcPoint(parameter=segPar20)
                Q1 = self.worldMatrix2 @ self.segment2.CalcPoint(parameter=segPar21)

                intersectionPointData = mathematics.CalcIntersectionPointsLineSegmentsDIR(P0, P1, Q0, Q1, algoDIR)
                if intersectionPointData is None:
                    continue

                intersectionSegment1Parameter = segPar10 + (intersectionPointData[0] / fltNrSamples1)
                worldPoint1 = self.worldMatrix1 @ self.segment1.CalcPoint(parameter=intersectionSegment1Parameter)
                intersectionPoint1 = BezierSegmentIntersectionPoint(self.segment1,
                                                                    intersectionSegment1Parameter,
                                                                    worldPoint1)
                rvIntersections1.append(intersectionPoint1)

                intersectionSegment2Parameter = segPar20 + (intersectionPointData[1] / fltNrSamples2)
                worldPoint2 = self.worldMatrix2 @ self.segment2.CalcPoint(parameter=intersectionSegment2Parameter)
                intersectionPoint2 = BezierSegmentIntersectionPoint(self.segment2,
                                                                    intersectionSegment2Parameter,
                                                                    worldPoint2)
                rvIntersections2.append(intersectionPoint2)

        return [rvIntersections1, rvIntersections2]

    def CalcIntersectionsFromViewPOV(self, nrSamples1, nrSamples2):
        global algoPOV

        rvIntersections1 = []
        rvIntersections2 = []

        fltNrSamples1 = float(nrSamples1)
        fltNrSamples2 = float(nrSamples2)

        for iSample1 in range(nrSamples1):
            segPar10 = float(iSample1) / fltNrSamples1
            segPar11 = float(iSample1 + 1) / fltNrSamples1
            P0 = self.worldMatrix1 @ self.segment1.CalcPoint(parameter=segPar10)
            P1 = self.worldMatrix1 @ self.segment1.CalcPoint(parameter=segPar11)

            for iSample2 in range(nrSamples2):
                segPar20 = float(iSample2) / fltNrSamples2
                segPar21 = float(iSample2 + 1) / fltNrSamples2
                Q0 = self.worldMatrix2 @ self.segment2.CalcPoint(parameter=segPar20)
                Q1 = self.worldMatrix2 @ self.segment2.CalcPoint(parameter=segPar21)

                intersectionPointData = mathematics.CalcIntersectionPointsLineSegmentsPOV(P0, P1, Q0, Q1, algoPOV)
                if intersectionPointData is None:
                    continue

                intersectionSegment1Parameter = segPar10 + (intersectionPointData[0] / fltNrSamples1)
                worldPoint1 = self.worldMatrix1 @ self.segment1.CalcPoint(parameter=intersectionSegment1Parameter)
                intersectionPoint1 = BezierSegmentIntersectionPoint(self.segment1,
                                                                    intersectionSegment1Parameter,
                                                                    worldPoint1)
                rvIntersections1.append(intersectionPoint1)

                intersectionSegment2Parameter = segPar20 + (intersectionPointData[1] / fltNrSamples2)
                worldPoint2 = self.worldMatrix2 @ self.segment2.CalcPoint(parameter=intersectionSegment2Parameter)
                intersectionPoint2 = BezierSegmentIntersectionPoint(self.segment2,
                                                                    intersectionSegment2Parameter,
                                                                    worldPoint2)
                rvIntersections2.append(intersectionPoint2)

        return [rvIntersections1, rvIntersections2]


class BezierSplineIntersectionPoint:
    def __init__(self, spline, bezierSegmentIntersectionPoint):
        self.spline = spline
        self.bezierSegmentIntersectionPoint = bezierSegmentIntersectionPoint


class BezierSplinesIntersector:
    def __init__(self, spline1, spline2, worldMatrix1, worldMatrix2):
        self.spline1 = spline1
        self.spline2 = spline2
        self.worldMatrix1 = worldMatrix1
        self.worldMatrix2 = worldMatrix2

    def CalcIntersections(self):
        rvIntersections1 = []
        rvIntersections2 = []

        try:
            nrSamplesPerSegment1 = int(self.spline1.resolution / self.spline1.nrSegments)
        except:
            nrSamplesPerSegment1 = 2
        if nrSamplesPerSegment1 < 2:
            nrSamplesPerSegment1 = 2

        try:
            nrSamplesPerSegment2 = int(self.spline2.resolution / self.spline2.nrSegments)
        except:
            nrSamplesPerSegment2 = 2
        if nrSamplesPerSegment2 < 2:
            nrSamplesPerSegment2 = 2

        for segment1 in self.spline1.segments:
            for segment2 in self.spline2.segments:
                segmentsIntersector = BezierSegmentsIntersector(segment1, segment2,
                                                                self.worldMatrix1, self.worldMatrix2)
                segmentIntersections = segmentsIntersector.CalcIntersections(nrSamplesPerSegment1, nrSamplesPerSegment2)
                if segmentIntersections is None:
                    continue

                segment1Intersections = segmentIntersections[0]
                for segmentIntersection in segment1Intersections:
                    splineIntersection = BezierSplineIntersectionPoint(self.spline1, segmentIntersection)
                    rvIntersections1.append(splineIntersection)

                segment2Intersections = segmentIntersections[1]
                for segmentIntersection in segment2Intersections:
                    splineIntersection = BezierSplineIntersectionPoint(self.spline2, segmentIntersection)
                    rvIntersections2.append(splineIntersection)

        return [rvIntersections1, rvIntersections2]


class CurvesIntersector:
    @staticmethod
    def FromSelection():
        selObjects = bpy.context.selected_objects
        if len(selObjects) != 2:
            raise Exception("len(selObjects) != 2")  # shouldn't be possible

        blenderActiveCurve = bpy.context.active_object
        blenderOtherCurve = selObjects[0]
        if blenderActiveCurve == blenderOtherCurve:
            blenderOtherCurve = selObjects[1]

        aCurve = curves.Curve(blenderActiveCurve)
        oCurve = curves.Curve(blenderOtherCurve)

        return CurvesIntersector(aCurve, oCurve)

    @staticmethod
    def ResetGlobals():
        global algoPOV
        algoPOV = None
        global algoDIR
        algoDIR = None

    @staticmethod
    def InitGlobals():
        CurvesIntersector.ResetGlobals()
        global algoPOV
        global algoDIR

        algo = bpy.context.scene.curvetools.IntersectCurvesAlgorithm
        if algo == 'From_View':
            regionView3D = util.GetFirstRegionView3D()
            if regionView3D is None:
                print("### ERROR: regionView3D is None. Stopping.")
                return

            viewPerspective = regionView3D.view_perspective
            print("--", "viewPerspective:", viewPerspective)

            if viewPerspective == 'ORTHO':
                viewMatrix = regionView3D.view_matrix
                print("--", "viewMatrix:")
                print(viewMatrix)

                algoDIR = Vector((viewMatrix[2][0], viewMatrix[2][1], viewMatrix[2][2]))
                print("--", "algoDIR:", algoDIR)

            # ## TODO: doesn't work properly
            if viewPerspective == 'PERSP':
                viewMatrix = regionView3D.view_matrix
                print("--", "viewMatrix:")
                print(viewMatrix)

                algoPOV = regionView3D.view_location.copy()
                print("--", "algoPOV:", algoPOV)

                otherPOV = Vector((viewMatrix[0][3], viewMatrix[1][3], viewMatrix[2][3]))
                print("--", "otherPOV:", otherPOV)

                localPOV = Vector((0, 0, 0))
                globalPOV = viewMatrix * localPOV
                print("--", "globalPOV:", globalPOV)

                perspMatrix = regionView3D.perspective_matrix
                print("--", "perspMatrix:")
                print(perspMatrix)

                globalPOVPersp = perspMatrix * localPOV
                print("--", "globalPOVPersp:", globalPOVPersp)

            if viewPerspective == 'CAMERA':
                camera = bpy.context.scene.camera
                if camera is None:
                    print("### ERROR: camera is None. Stopping.")
                    return

                print("--", "camera:", camera)
                cameraData = camera.data
                print("--", "cameraData.type:", cameraData.type)

                cameraMatrix = camera.matrix_world
                print("--", "cameraMatrix:")
                print(cameraMatrix)

                if cameraData.type == 'ORTHO':
                    cameraMatrix = camera.matrix_world
                    # algoDIR = Vector((cameraMatrix[2][0], cameraMatrix[2][1], cameraMatrix[2][2]))
                    algoDIR = Vector((- cameraMatrix[0][2], - cameraMatrix[1][2], - cameraMatrix[2][2]))
                    print("--", "algoDIR:", algoDIR)

                if cameraData.type == 'PERSP':
                    algoPOV = camera.location.copy()
                    print("--", "algoPOV:", algoPOV)

    def __init__(self, activeCurve, otherCurve):
        self.activeCurve = activeCurve
        self.otherCurve = otherCurve

        CurvesIntersector.InitGlobals()

    def CalcIntersections(self):
        rvIntersections1 = []
        rvIntersections2 = []

        worldMatrix1 = self.activeCurve.curve.matrix_world
        worldMatrix2 = self.otherCurve.curve.matrix_world

        for spline1 in self.activeCurve.splines:
            for spline2 in self.otherCurve.splines:
                splineIntersector = BezierSplinesIntersector(spline1, spline2, worldMatrix1, worldMatrix2)
                splineIntersections = splineIntersector.CalcIntersections()
                if splineIntersections is None:
                    continue

                spline1Intersections = splineIntersections[0]
                for splineIntersection in spline1Intersections:
                    rvIntersections1.append(splineIntersection)

                spline2Intersections = splineIntersections[1]
                for splineIntersection in spline2Intersections:
                    rvIntersections2.append(splineIntersection)

        return [rvIntersections1, rvIntersections2]

    def CalcAndApplyIntersections(self):
        mode = bpy.context.scene.curvetools.IntersectCurvesMode

        if mode == 'Empty':
            return self.CalcAndApplyEmptyAtIntersections()
        if mode == 'Insert':
            return self.CalcAndApplyInsertAtIntersections()
        if mode == 'Split':
            return self.CalcAndApplySplitAtIntersections()

        return [0, 0]

    def CalcAndApplyEmptyAtIntersections(self):
        intersections = self.CalcIntersections()
        intersectionsActive = intersections[0]
        intersectionsOther = intersections[1]

        nrActive = 0
        nrOther = 0

        affect = bpy.context.scene.curvetools.IntersectCurvesAffect

        if (affect == 'Both') or (affect == 'Active'):
            for splineIntersection in intersectionsActive:
                iPoint = splineIntersection.bezierSegmentIntersectionPoint.intersectionPoint
                bpy.ops.object.empty_add(type='PLAIN_AXES',
                                         align='WORLD',
                                         location=(iPoint.x, iPoint.y, iPoint.z), rotation=(0, 0, 0))
                nrActive += 1

        if (affect == 'Both') or (affect == 'Other'):
            for splineIntersection in intersectionsOther:
                iPoint = splineIntersection.bezierSegmentIntersectionPoint.intersectionPoint
                bpy.ops.object.empty_add(type='PLAIN_AXES',
                                         align='WORLD',
                                         location=(iPoint.x, iPoint.y, iPoint.z), rotation=(0, 0, 0))
                nrOther += 1

        return [nrActive, nrOther]

    def CalcAndApplyInsertAtIntersections(self):
        nrActive = 0
        nrOther = 0

        affect = bpy.context.scene.curvetools.IntersectCurvesAffect
        affectA = (affect == 'Both') or (affect == 'Active')
        affectO = (affect == 'Both') or (affect == 'Other')

        for iSplineA in range(len(self.activeCurve.splines)):
            splineA = self.activeCurve.splines[iSplineA]
            nrSegmentsA = len(splineA.segments)
            resPerSegA = splineA.resolutionPerSegment

            for iSplineO in range(len(self.otherCurve.splines)):
                splineO = self.otherCurve.splines[iSplineO]
                nrSegmentsO = len(splineO.segments)
                resPerSegO = splineO.resolutionPerSegment

                iSegA = 0
                while True:
                    segA = splineA.segments[iSegA]

                    iSegO = 0
                    while True:
                        segO = splineO.segments[iSegO]

                        segIntersector = BezierSegmentsIntersector(segA, segO,
                                                                   self.activeCurve.worldMatrix,
                                                                   self.otherCurve.worldMatrix)
                        segFirstIntersection = segIntersector.CalcFirstIntersection(resPerSegA, resPerSegO)

                        if segFirstIntersection is not None:
                            intPointA = segFirstIntersection[0]
                            intPointO = segFirstIntersection[1]
                            # else does something weird if 1 of them is None..
                            if (intPointA is not None) and (intPointO is not None):
                                if affectA:
                                    if intPointA is not None:
                                        splineA.InsertPoint(segA, intPointA.parameter)

                                        nrActive += 1
                                        nrSegmentsA += 1

                                if affectO:
                                    if intPointO is not None:
                                        splineO.InsertPoint(segO, intPointO.parameter)

                                        nrOther += 1
                                        nrSegmentsO += 1

                        iSegO += 1
                        if not (iSegO < nrSegmentsO):
                            break

                    iSegA += 1
                    if not (iSegA < nrSegmentsA):
                        break

                if affectO:
                    splineO.RefreshInScene()

            if affectA:
                splineA.RefreshInScene()

        return [nrActive, nrOther]

    def CalcAndApplySplitAtIntersections(self):
        nrActive = 0
        nrOther = 0

        affect = bpy.context.scene.curvetools.IntersectCurvesAffect
        affectA = (affect == 'Both') or (affect == 'Active')
        affectO = (affect == 'Both') or (affect == 'Other')

        nrSplinesA = len(self.activeCurve.splines)
        nrSplinesO = len(self.otherCurve.splines)

        iSplineA = 0
        while True:
            splineA = self.activeCurve.splines[iSplineA]
            nrSegmentsA = len(splineA.segments)
            resPerSegA = splineA.resolutionPerSegment

            iSplineO = 0
            while True:
                splineO = self.otherCurve.splines[iSplineO]
                nrSegmentsO = len(splineO.segments)
                resPerSegO = splineO.resolutionPerSegment

                iSegA = 0
                while True:
                    segA = splineA.segments[iSegA]

                    iSegO = 0
                    while True:
                        segO = splineO.segments[iSegO]

                        segIntersector = BezierSegmentsIntersector(segA, segO,
                                                                   self.activeCurve.worldMatrix,
                                                                   self.otherCurve.worldMatrix)
                        segFirstIntersection = segIntersector.CalcFirstIntersection(resPerSegA, resPerSegO)

                        if segFirstIntersection is not None:
                            intPointA = segFirstIntersection[0]
                            intPointO = segFirstIntersection[1]
                            # else does something weird if 1 of them is None..
                            if (intPointA is not None) and (intPointO is not None):
                                if affectA:
                                    if intPointA is not None:
                                        print("--", "splineA.Split():")
                                        newSplinesA = splineA.Split(segA, intPointA.parameter)
                                        if newSplinesA is not None:
                                            newResolutions = splineA.CalcDivideResolution(segA, intPointA.parameter)
                                            newSplinesA[0].resolution = newResolutions[0]
                                            newSplinesA[1].resolution = newResolutions[1]

                                            splineA = newSplinesA[0]
                                            self.activeCurve.splines[iSplineA] = splineA
                                            self.activeCurve.splines.insert(iSplineA + 1, newSplinesA[1])

                                            nrActive += 1

                                if affectO:
                                    if intPointO is not None:
                                        print("--", "splineO.Split():")
                                        newSplinesO = splineO.Split(segO, intPointO.parameter)
                                        if newSplinesO is not None:
                                            newResolutions = splineO.CalcDivideResolution(segO, intPointO.parameter)
                                            newSplinesO[0].resolution = newResolutions[0]
                                            newSplinesO[1].resolution = newResolutions[1]

                                            splineO = newSplinesO[0]
                                            self.otherCurve.splines[iSplineO] = splineO
                                            self.otherCurve.splines.insert(iSplineO + 1, newSplinesO[1])

                                            nrOther += 1

                        nrSegmentsO = len(splineO.segments)
                        iSegO += 1
                        if not (iSegO < nrSegmentsO):
                            break

                    nrSegmentsA = len(splineA.segments)
                    iSegA += 1
                    if not (iSegA < nrSegmentsA):
                        break

                nrSplinesO = len(self.otherCurve.splines)
                iSplineO += 1
                if not (iSplineO < nrSplinesO):
                    break

            nrSplinesA = len(self.activeCurve.splines)
            iSplineA += 1
            if not (iSplineA < nrSplinesA):
                break

        if affectA:
            print("")
            print("--", "self.activeCurve.RebuildInScene():")
            self.activeCurve.RebuildInScene()
        if affectO:
            print("")
            print("--", "self.otherCurve.RebuildInScene():")
            self.otherCurve.RebuildInScene()

        return [nrActive, nrOther]

# SPDX-FileCopyrightText: 2019-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

from . import mathematics

import bpy


class BezierPoint:
    @staticmethod
    def FromBlenderBezierPoint(blenderBezierPoint):
        return BezierPoint(blenderBezierPoint.handle_left, blenderBezierPoint.co, blenderBezierPoint.handle_right)


    def __init__(self, handle_left, co, handle_right):
        self.handle_left = handle_left
        self.co = co
        self.handle_right = handle_right


    def Copy(self):
        return BezierPoint(self.handle_left.copy(), self.co.copy(), self.handle_right.copy())

    def Reversed(self):
        return BezierPoint(self.handle_right, self.co, self.handle_left)

    def Reverse(self):
        tmp = self.handle_left
        self.handle_left = self.handle_right
        self.handle_right = tmp


class BezierSegment:
    @staticmethod
    def FromBlenderBezierPoints(blenderBezierPoint1, blenderBezierPoint2):
        bp1 = BezierPoint.FromBlenderBezierPoint(blenderBezierPoint1)
        bp2 = BezierPoint.FromBlenderBezierPoint(blenderBezierPoint2)

        return BezierSegment(bp1, bp2)


    def Copy(self):
        return BezierSegment(self.bezierPoint1.Copy(), self.bezierPoint2.Copy())

    def Reversed(self):
        return BezierSegment(self.bezierPoint2.Reversed(), self.bezierPoint1.Reversed())

    def Reverse(self):
        # make a copy, otherwise neighboring segment may be affected
        tmp = self.bezierPoint1.Copy()
        self.bezierPoint1 = self.bezierPoint2.Copy()
        self.bezierPoint2 = tmp
        self.bezierPoint1.Reverse()
        self.bezierPoint2.Reverse()


    def __init__(self, bezierPoint1, bezierPoint2):
        # bpy.types.BezierSplinePoint
        # ## NOTE/TIP: copy() helps with repeated (intersection) action -- ??
        self.bezierPoint1 = bezierPoint1.Copy()
        self.bezierPoint2 = bezierPoint2.Copy()

        self.ctrlPnt0 = self.bezierPoint1.co
        self.ctrlPnt1 = self.bezierPoint1.handle_right
        self.ctrlPnt2 = self.bezierPoint2.handle_left
        self.ctrlPnt3 = self.bezierPoint2.co

        self.coeff0 = self.ctrlPnt0
        self.coeff1 = self.ctrlPnt0 * (-3.0) + self.ctrlPnt1 * (+3.0)
        self.coeff2 = self.ctrlPnt0 * (+3.0) + self.ctrlPnt1 * (-6.0) + self.ctrlPnt2 * (+3.0)
        self.coeff3 = self.ctrlPnt0 * (-1.0) + self.ctrlPnt1 * (+3.0) + self.ctrlPnt2 * (-3.0) + self.ctrlPnt3


    def CalcPoint(self, parameter = 0.5):
        parameter2 = parameter * parameter
        parameter3 = parameter * parameter2

        rvPoint = self.coeff0 + self.coeff1 * parameter + self.coeff2 * parameter2 + self.coeff3 * parameter3

        return rvPoint


    def CalcDerivative(self, parameter = 0.5):
        parameter2 = parameter * parameter

        rvPoint = self.coeff1 + self.coeff2 * parameter * 2.0 + self.coeff3 * parameter2 * 3.0

        return rvPoint


    def CalcLength(self, nrSamples = 2):
        nrSamplesFloat = float(nrSamples)
        rvLength = 0.0
        for iSample in range(nrSamples):
            par1 = float(iSample) / nrSamplesFloat
            par2 = float(iSample + 1) / nrSamplesFloat

            point1 = self.CalcPoint(parameter = par1)
            point2 = self.CalcPoint(parameter = par2)
            diff12 = point1 - point2

            rvLength += diff12.magnitude

        return rvLength


    #http://en.wikipedia.org/wiki/De_Casteljau's_algorithm
    def CalcSplitPoint(self, parameter = 0.5):
        par1min = 1.0 - parameter

        bez00 = self.ctrlPnt0
        bez01 = self.ctrlPnt1
        bez02 = self.ctrlPnt2
        bez03 = self.ctrlPnt3

        bez10 = bez00 * par1min + bez01 * parameter
        bez11 = bez01 * par1min + bez02 * parameter
        bez12 = bez02 * par1min + bez03 * parameter

        bez20 = bez10 * par1min + bez11 * parameter
        bez21 = bez11 * par1min + bez12 * parameter

        bez30 = bez20 * par1min + bez21 * parameter

        bezPoint1 = BezierPoint(self.bezierPoint1.handle_left, bez00, bez10)
        bezPointNew = BezierPoint(bez20, bez30, bez21)
        bezPoint2 = BezierPoint(bez12, bez03, self.bezierPoint2.handle_right)

        return [bezPoint1, bezPointNew, bezPoint2]


class BezierSpline:
    @staticmethod
    def FromSegments(listSegments):
        rvSpline = BezierSpline(None)

        rvSpline.segments = listSegments

        return rvSpline


    def __init__(self, blenderBezierSpline):
        if not blenderBezierSpline is None:
            if blenderBezierSpline.type != 'BEZIER':
                print("## ERROR:", "blenderBezierSpline.type != 'BEZIER'")
                raise Exception("blenderBezierSpline.type != 'BEZIER'")
            if len(blenderBezierSpline.bezier_points) < 1:
                if not blenderBezierSpline.use_cyclic_u:
                    print("## ERROR:", "len(blenderBezierSpline.bezier_points) < 1")
                    raise Exception("len(blenderBezierSpline.bezier_points) < 1")

        self.bezierSpline = blenderBezierSpline

        self.resolution = 12
        self.isCyclic = False
        if not self.bezierSpline is None:
            self.resolution = self.bezierSpline.resolution_u
            self.isCyclic = self.bezierSpline.use_cyclic_u

        self.segments = self.SetupSegments()


    def __getattr__(self, attrName):
        if attrName == "nrSegments":
            return len(self.segments)

        if attrName == "bezierPoints":
            rvList = []

            for seg in self.segments: rvList.append(seg.bezierPoint1)
            if not self.isCyclic: rvList.append(self.segments[-1].bezierPoint2)

            return rvList

        if attrName == "resolutionPerSegment":
            try: rvResPS = int(self.resolution / self.nrSegments)
            except: rvResPS = 2
            if rvResPS < 2: rvResPS = 2

            return rvResPS

        if attrName == "length":
            return self.CalcLength()

        return None


    def SetupSegments(self):
        rvSegments = []
        if self.bezierSpline is None: return rvSegments

        nrBezierPoints = len(self.bezierSpline.bezier_points)
        for iBezierPoint in range(nrBezierPoints - 1):
            bezierPoint1 = self.bezierSpline.bezier_points[iBezierPoint]
            bezierPoint2 = self.bezierSpline.bezier_points[iBezierPoint + 1]
            rvSegments.append(BezierSegment.FromBlenderBezierPoints(bezierPoint1, bezierPoint2))
        if self.isCyclic:
            bezierPoint1 = self.bezierSpline.bezier_points[-1]
            bezierPoint2 = self.bezierSpline.bezier_points[0]
            rvSegments.append(BezierSegment.FromBlenderBezierPoints(bezierPoint1, bezierPoint2))

        return rvSegments


    def UpdateSegments(self, newSegments):
        prevNrSegments = len(self.segments)
        diffNrSegments = len(newSegments) - prevNrSegments
        if diffNrSegments > 0:
            newBezierPoints = []
            for segment in newSegments: newBezierPoints.append(segment.bezierPoint1)
            if not self.isCyclic: newBezierPoints.append(newSegments[-1].bezierPoint2)

            self.bezierSpline.bezier_points.add(diffNrSegments)

            for i, bezPoint in enumerate(newBezierPoints):
                blBezPoint = self.bezierSpline.bezier_points[i]

                blBezPoint.tilt = 0
                blBezPoint.radius = 1.0

                blBezPoint.handle_left_type = 'FREE'
                blBezPoint.handle_left = bezPoint.handle_left
                blBezPoint.co = bezPoint.co
                blBezPoint.handle_right_type = 'FREE'
                blBezPoint.handle_right = bezPoint.handle_right

            self.segments = newSegments
        else:
            print("### WARNING: UpdateSegments(): not diffNrSegments > 0")


    def Reversed(self):
        revSegments = []

        for iSeg in reversed(range(self.nrSegments)): revSegments.append(self.segments[iSeg].Reversed())

        rvSpline = BezierSpline.FromSegments(revSegments)
        rvSpline.resolution = self.resolution
        rvSpline.isCyclic = self.isCyclic

        return rvSpline


    def Reverse(self):
        revSegments = []

        for iSeg in reversed(range(self.nrSegments)):
            self.segments[iSeg].Reverse()
            revSegments.append(self.segments[iSeg])

        self.segments = revSegments


    def CalcDivideResolution(self, segment, parameter):
        if not segment in self.segments:
            print("### WARNING: InsertPoint(): not segment in self.segments")
            return None

        iSeg = self.segments.index(segment)
        dPar = 1.0 / self.nrSegments
        splinePar = dPar * (parameter + float(iSeg))

        res1 = int(splinePar * self.resolution)
        if res1 < 2:
            print("### WARNING: CalcDivideResolution(): res1 < 2 -- res1: %d" % res1, "-- setting it to 2")
            res1 = 2

        res2 = int((1.0 - splinePar) * self.resolution)
        if res2 < 2:
            print("### WARNING: CalcDivideResolution(): res2 < 2 -- res2: %d" % res2, "-- setting it to 2")
            res2 = 2

        return [res1, res2]
        # return [self.resolution, self.resolution]


    def CalcPoint(self, parameter):
        nrSegs = self.nrSegments

        segmentIndex = int(nrSegs * parameter)
        if segmentIndex < 0: segmentIndex = 0
        if segmentIndex > (nrSegs - 1): segmentIndex = nrSegs - 1

        segmentParameter = nrSegs * parameter - segmentIndex
        if segmentParameter < 0.0: segmentParameter = 0.0
        if segmentParameter > 1.0: segmentParameter = 1.0

        return self.segments[segmentIndex].CalcPoint(parameter = segmentParameter)


    def CalcDerivative(self, parameter):
        nrSegs = self.nrSegments

        segmentIndex = int(nrSegs * parameter)
        if segmentIndex < 0: segmentIndex = 0
        if segmentIndex > (nrSegs - 1): segmentIndex = nrSegs - 1

        segmentParameter = nrSegs * parameter - segmentIndex
        if segmentParameter < 0.0: segmentParameter = 0.0
        if segmentParameter > 1.0: segmentParameter = 1.0

        return self.segments[segmentIndex].CalcDerivative(parameter = segmentParameter)


    def InsertPoint(self, segment, parameter):
        if not segment in self.segments:
            print("### WARNING: InsertPoint(): not segment in self.segments")
            return
        iSeg = self.segments.index(segment)
        nrSegments = len(self.segments)

        splitPoints = segment.CalcSplitPoint(parameter = parameter)
        bezPoint1 = splitPoints[0]
        bezPointNew = splitPoints[1]
        bezPoint2 = splitPoints[2]

        segment.bezierPoint1.handle_right = bezPoint1.handle_right
        segment.bezierPoint2 = bezPointNew

        if iSeg < (nrSegments - 1):
            nextSeg = self.segments[iSeg + 1]
            nextSeg.bezierPoint1.handle_left = bezPoint2.handle_left
        else:
            if self.isCyclic:
                nextSeg = self.segments[0]
                nextSeg.bezierPoint1.handle_left = bezPoint2.handle_left


        newSeg = BezierSegment(bezPointNew, bezPoint2)
        self.segments.insert(iSeg + 1, newSeg)


    def Split(self, segment, parameter):
        if not segment in self.segments:
            print("### WARNING: InsertPoint(): not segment in self.segments")
            return None
        iSeg = self.segments.index(segment)
        nrSegments = len(self.segments)

        splitPoints = segment.CalcSplitPoint(parameter = parameter)
        bezPoint1 = splitPoints[0]
        bezPointNew = splitPoints[1]
        bezPoint2 = splitPoints[2]


        newSpline1Segments = []
        for iSeg1 in range(iSeg): newSpline1Segments.append(self.segments[iSeg1])
        if len(newSpline1Segments) > 0: newSpline1Segments[-1].bezierPoint2.handle_right = bezPoint1.handle_right
        newSpline1Segments.append(BezierSegment(bezPoint1, bezPointNew))

        newSpline2Segments = []
        newSpline2Segments.append(BezierSegment(bezPointNew, bezPoint2))
        for iSeg2 in range(iSeg + 1, nrSegments): newSpline2Segments.append(self.segments[iSeg2])
        if len(newSpline2Segments) > 1: newSpline2Segments[1].bezierPoint1.handle_left = newSpline2Segments[0].bezierPoint2.handle_left


        newSpline1 = BezierSpline.FromSegments(newSpline1Segments)
        newSpline2 = BezierSpline.FromSegments(newSpline2Segments)

        return [newSpline1, newSpline2]


    def Join(self, spline2, mode = 'At_midpoint'):
        if mode == 'At_midpoint':
            self.JoinAtMidpoint(spline2)
            return

        if mode == 'Insert_segment':
            self.JoinInsertSegment(spline2)
            return

        print("### ERROR: Join(): unknown mode:", mode)


    def JoinAtMidpoint(self, spline2):
        bezPoint1 = self.segments[-1].bezierPoint2
        bezPoint2 = spline2.segments[0].bezierPoint1

        mpHandleLeft = bezPoint1.handle_left.copy()
        mpCo = (bezPoint1.co + bezPoint2.co) * 0.5
        mpHandleRight = bezPoint2.handle_right.copy()
        mpBezPoint = BezierPoint(mpHandleLeft, mpCo, mpHandleRight)

        self.segments[-1].bezierPoint2 = mpBezPoint
        spline2.segments[0].bezierPoint1 = mpBezPoint
        for seg2 in spline2.segments: self.segments.append(seg2)

        self.resolution += spline2.resolution
        self.isCyclic = False    # is this ok?


    def JoinInsertSegment(self, spline2):
        self.segments.append(BezierSegment(self.segments[-1].bezierPoint2, spline2.segments[0].bezierPoint1))
        for seg2 in spline2.segments: self.segments.append(seg2)

        self.resolution += spline2.resolution    # extra segment will usually be short -- impact on resolution negligible

        self.isCyclic = False    # is this ok?


    def RefreshInScene(self):
        bezierPoints = self.bezierPoints

        currNrBezierPoints = len(self.bezierSpline.bezier_points)
        diffNrBezierPoints = len(bezierPoints) - currNrBezierPoints
        if diffNrBezierPoints > 0: self.bezierSpline.bezier_points.add(diffNrBezierPoints)

        for i, bezPoint in enumerate(bezierPoints):
            blBezPoint = self.bezierSpline.bezier_points[i]

            blBezPoint.tilt = 0
            blBezPoint.radius = 1.0

            blBezPoint.handle_left_type = 'FREE'
            blBezPoint.handle_left = bezPoint.handle_left
            blBezPoint.co = bezPoint.co
            blBezPoint.handle_right_type = 'FREE'
            blBezPoint.handle_right = bezPoint.handle_right

        self.bezierSpline.use_cyclic_u = self.isCyclic
        self.bezierSpline.resolution_u = self.resolution


    def CalcLength(self):
        try: nrSamplesPerSegment = int(self.resolution / self.nrSegments)
        except: nrSamplesPerSegment = 2
        if nrSamplesPerSegment < 2: nrSamplesPerSegment = 2

        rvLength = 0.0
        for segment in self.segments:
            rvLength += segment.CalcLength(nrSamples = nrSamplesPerSegment)

        return rvLength


    def GetLengthIsSmallerThan(self, threshold):
        try: nrSamplesPerSegment = int(self.resolution / self.nrSegments)
        except: nrSamplesPerSegment = 2
        if nrSamplesPerSegment < 2: nrSamplesPerSegment = 2

        length = 0.0
        for segment in self.segments:
            length += segment.CalcLength(nrSamples = nrSamplesPerSegment)
            if not length < threshold: return False

        return True


class Curve:
    def __init__(self, blenderCurve):
        self.curve = blenderCurve
        self.curveData = blenderCurve.data

        self.splines = self.SetupSplines()


    def __getattr__(self, attrName):
        if attrName == "nrSplines":
            return len(self.splines)

        if attrName == "length":
            return self.CalcLength()

        if attrName == "worldMatrix":
            return self.curve.matrix_world

        if attrName == "location":
            return self.curve.location

        return None


    def SetupSplines(self):
        rvSplines = []
        for spline in self.curveData.splines:
            if spline.type != 'BEZIER':
                print("## WARNING: only bezier splines are supported, atm; other types are ignored")
                continue

            try: newSpline = BezierSpline(spline)
            except:
                print("## EXCEPTION: newSpline = BezierSpline(spline)")
                continue

            rvSplines.append(newSpline)

        return rvSplines


    def RebuildInScene(self):
        self.curveData.splines.clear()

        for spline in self.splines:
            blSpline = self.curveData.splines.new('BEZIER')
            blSpline.use_cyclic_u = spline.isCyclic
            blSpline.resolution_u = spline.resolution

            bezierPoints = []
            for segment in spline.segments: bezierPoints.append(segment.bezierPoint1)
            if not spline.isCyclic: bezierPoints.append(spline.segments[-1].bezierPoint2)
            #else: print("????", "spline.isCyclic")

            nrBezierPoints = len(bezierPoints)
            blSpline.bezier_points.add(nrBezierPoints - 1)

            for i, blBezPoint in enumerate(blSpline.bezier_points):
                bezPoint = bezierPoints[i]

                blBezPoint.tilt = 0
                blBezPoint.radius = 1.0

                blBezPoint.handle_left_type = 'FREE'
                blBezPoint.handle_left = bezPoint.handle_left
                blBezPoint.co = bezPoint.co
                blBezPoint.handle_right_type = 'FREE'
                blBezPoint.handle_right = bezPoint.handle_right


    def CalcLength(self):
        rvLength = 0.0
        for spline in self.splines:
            rvLength += spline.length

        return rvLength


    def RemoveShortSplines(self, threshold):
        splinesToRemove = []

        for spline in self.splines:
            if spline.GetLengthIsSmallerThan(threshold): splinesToRemove.append(spline)

        for spline in splinesToRemove: self.splines.remove(spline)

        return len(splinesToRemove)


    def JoinNeighbouringSplines(self, startEnd, threshold, mode):
        nrJoins = 0

        while True:
            firstPair = self.JoinGetFirstPair(startEnd, threshold)
            if firstPair is None: break

            firstPair[0].Join(firstPair[1], mode)
            self.splines.remove(firstPair[1])

            nrJoins += 1

        return nrJoins


    def JoinGetFirstPair(self, startEnd, threshold):
        nrSplines = len(self.splines)

        if startEnd:
            for iCurrentSpline in range(nrSplines):
                currentSpline = self.splines[iCurrentSpline]

                for iNextSpline in range(iCurrentSpline + 1, nrSplines):
                    nextSpline = self.splines[iNextSpline]

                    currEndPoint = currentSpline.segments[-1].bezierPoint2.co
                    nextStartPoint = nextSpline.segments[0].bezierPoint1.co
                    if mathematics.IsSamePoint(currEndPoint, nextStartPoint, threshold): return [currentSpline, nextSpline]

                    nextEndPoint = nextSpline.segments[-1].bezierPoint2.co
                    currStartPoint = currentSpline.segments[0].bezierPoint1.co
                    if mathematics.IsSamePoint(nextEndPoint, currStartPoint, threshold): return [nextSpline, currentSpline]

            return None
        else:
            for iCurrentSpline in range(nrSplines):
                currentSpline = self.splines[iCurrentSpline]

                for iNextSpline in range(iCurrentSpline + 1, nrSplines):
                    nextSpline = self.splines[iNextSpline]

                    currEndPoint = currentSpline.segments[-1].bezierPoint2.co
                    nextStartPoint = nextSpline.segments[0].bezierPoint1.co
                    if mathematics.IsSamePoint(currEndPoint, nextStartPoint, threshold): return [currentSpline, nextSpline]

                    nextEndPoint = nextSpline.segments[-1].bezierPoint2.co
                    currStartPoint = currentSpline.segments[0].bezierPoint1.co
                    if mathematics.IsSamePoint(nextEndPoint, currStartPoint, threshold): return [nextSpline, currentSpline]

                    if mathematics.IsSamePoint(currEndPoint, nextEndPoint, threshold):
                        nextSpline.Reverse()
                        #print("## ", "nextSpline.Reverse()")
                        return [currentSpline, nextSpline]

                    if mathematics.IsSamePoint(currStartPoint, nextStartPoint, threshold):
                        currentSpline.Reverse()
                        #print("## ", "currentSpline.Reverse()")
                        return [currentSpline, nextSpline]

            return None

# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# <pep8 compliant>

from math import hypot, sqrt, isfinite
import bpy
import time
from mathutils import Vector


#Vector utility functions
class NdVector:
    vec = []

    def __init__(self, vec):
        self.vec = vec[:]

    def __len__(self):
        return len(self.vec)

    def __mul__(self, otherMember):
        if (isinstance(otherMember, int) or
            isinstance(otherMember, float)):
            return NdVector([otherMember * x for x in self.vec])
        else:
            a = self.vec
            b = otherMember.vec
            n = len(self)
            return sum([a[i] * b[i] for i in range(n)])

    def __sub__(self, otherVec):
        a = self.vec
        b = otherVec.vec
        n = len(self)
        return NdVector([a[i] - b[i] for i in range(n)])

    def __add__(self, otherVec):
        a = self.vec
        b = otherVec.vec
        n = len(self)
        return NdVector([a[i] + b[i] for i in range(n)])

    def __div__(self, scalar):
        return NdVector([x / scalar for x in self.vec])

    def vecLength(self):
        return sqrt(self * self)

    def vecLengthSq(self):
        return (self * self)

    def normalize(self):
        len = self.length
        self.vec = [x / len for x in self.vec]

    def copy(self):
        return NdVector(self.vec)

    def __getitem__(self, i):
        return self.vec[i]

    def x(self):
        return self.vec[0]

    def y(self):
        return self.vec[1]

    length = property(vecLength)
    lengthSq = property(vecLengthSq)
    x = property(x)
    y = property(y)


class dataPoint:
    index = 0
    # x,y1,y2,y3 coordinate of original point
    co = NdVector((0, 0, 0, 0, 0))
    #position according to parametric view of original data, [0,1] range
    u = 0
    #use this for anything
    temp = 0

    def __init__(self, index, co, u=0):
        self.index = index
        self.co = co
        self.u = u


def autoloop_anim():
    context = bpy.context
    obj = context.active_object
    fcurves = [x for x in obj.animation_data.action.fcurves if x.select]

    data = []
    end = len(fcurves[0].keyframe_points)

    for i in range(1, end):
        vec = []
        for fcurve in fcurves:
            vec.append(fcurve.evaluate(i))
        data.append(NdVector(vec))

    def comp(a, b):
        return a * b

    N = len(data)
    Rxy = [0.0] * N
    for i in range(N):
        for j in range(i, min(i + N, N)):
            Rxy[i] += comp(data[j], data[j - i])
        for j in range(i):
            Rxy[i] += comp(data[j], data[j - i + N])
        Rxy[i] /= float(N)

    def bestLocalMaximum(Rxy):
        Rxyd = [Rxy[i] - Rxy[i - 1] for i in range(1, len(Rxy))]
        maxs = []
        for i in range(1, len(Rxyd) - 1):
            a = Rxyd[i - 1]
            b = Rxyd[i]
            print(a, b)
            #sign change (zerocrossing) at point i, denoting max point (only)
            if (a >= 0 and b < 0) or (a < 0 and b >= 0):
                maxs.append((i, max(Rxy[i], Rxy[i - 1])))
        return max(maxs, key=lambda x: x[1])[0]
    flm = bestLocalMaximum(Rxy[0:int(len(Rxy))])

    diff = []

    for i in range(len(data) - flm):
        diff.append((data[i] - data[i + flm]).lengthSq)

    def lowerErrorSlice(diff, e):
        #index, error at index
        bestSlice = (0, 100000)
        for i in range(e, len(diff) - e):
            errorSlice = sum(diff[i - e:i + e + 1])
            if errorSlice < bestSlice[1]:
                bestSlice = (i, errorSlice)
        return bestSlice[0]

    margin = 2

    s = lowerErrorSlice(diff, margin)

    print(flm, s)
    loop = data[s:s + flm + margin]

    #find *all* loops, s:s+flm, s+flm:s+2flm, etc...
    #and interpolate between all
    # to find "the perfect loop".
    #Maybe before finding s? interp(i,i+flm,i+2flm)....
    for i in range(1, margin + 1):
        w1 = sqrt(float(i) / margin)
        loop[-i] = (loop[-i] * w1) + (loop[0] * (1 - w1))

    for curve in fcurves:
        pts = curve.keyframe_points
        for i in range(len(pts) - 1, -1, -1):
            pts.remove(pts[i])

    for c, curve in enumerate(fcurves):
        pts = curve.keyframe_points
        for i in range(len(loop)):
            pts.insert(i + 1, loop[i][c])

    context.scene.frame_end = flm + 1


def simplifyCurves(curveGroup, error, reparaError, maxIterations, group_mode):

    def unitTangent(v, data_pts):
        tang = NdVector((0, 0, 0, 0, 0))
        if v != 0:
            #If it's not the first point, we can calculate a leftside tangent
            tang += data_pts[v].co - data_pts[v - 1].co
        if v != len(data_pts) - 1:
            #If it's not the last point, we can calculate a rightside tangent
            tang += data_pts[v + 1].co - data_pts[v].co
        tang.normalize()
        return tang

    #assign parametric u value for each point in original data
    def chordLength(data_pts, s, e):
        totalLength = 0
        for pt in data_pts[s:e + 1]:
            i = pt.index
            if i == s:
                chordLength = 0
            else:
                chordLength = (data_pts[i].co - data_pts[i - 1].co).length
            totalLength += chordLength
            pt.temp = totalLength
        for pt in data_pts[s:e + 1]:
            if totalLength == 0:
                print(s, e)
            pt.u = (pt.temp / totalLength)

    # get binomial coefficient, this function/table is only called with args
    # (3,0),(3,1),(3,2),(3,3),(2,0),(2,1),(2,2)!
    binomDict = {(3, 0): 1,
    (3, 1): 3,
    (3, 2): 3,
    (3, 3): 1,
    (2, 0): 1,
    (2, 1): 2,
    (2, 2): 1}
    #value at pt t of a single bernstein Polynomial

    def bernsteinPoly(n, i, t):
        binomCoeff = binomDict[(n, i)]
        return binomCoeff * pow(t, i) * pow(1 - t, n - i)

    # fit a single cubic to data points in range [s(tart),e(nd)].
    def fitSingleCubic(data_pts, s, e):

        # A - matrix used for calculating C matrices for fitting
        def A(i, j, s, e, t1, t2):
            if j == 1:
                t = t1
            if j == 2:
                t = t2
            u = data_pts[i].u
            return t * bernsteinPoly(3, j, u)

        # X component, used for calculating X matrices for fitting
        def xComponent(i, s, e):
            di = data_pts[i].co
            u = data_pts[i].u
            v0 = data_pts[s].co
            v3 = data_pts[e].co
            a = v0 * bernsteinPoly(3, 0, u)
            b = v0 * bernsteinPoly(3, 1, u)
            c = v3 * bernsteinPoly(3, 2, u)
            d = v3 * bernsteinPoly(3, 3, u)
            return (di - (a + b + c + d))

        t1 = unitTangent(s, data_pts)
        t2 = unitTangent(e, data_pts)
        c11 = sum([A(i, 1, s, e, t1, t2) * A(i, 1, s, e, t1, t2) for i in range(s, e + 1)])
        c12 = sum([A(i, 1, s, e, t1, t2) * A(i, 2, s, e, t1, t2) for i in range(s, e + 1)])
        c21 = c12
        c22 = sum([A(i, 2, s, e, t1, t2) * A(i, 2, s, e, t1, t2) for i in range(s, e + 1)])

        x1 = sum([xComponent(i, s, e) * A(i, 1, s, e, t1, t2) for i in range(s, e + 1)])
        x2 = sum([xComponent(i, s, e) * A(i, 2, s, e, t1, t2) for i in range(s, e + 1)])

        # calculate Determinate of the 3 matrices
        det_cc = c11 * c22 - c21 * c12
        det_cx = c11 * x2 - c12 * x1
        det_xc = x1 * c22 - x2 * c12

        # if matrix is not homogenous, fudge the data a bit
        if det_cc == 0:
            det_cc = 0.01

        # alpha's are the correct offset for bezier handles
        alpha0 = det_xc / det_cc   # offset from right (first) point
        alpha1 = det_cx / det_cc   # offset from left (last) point

        sRightHandle = data_pts[s].co.copy()
        sTangent = t1 * abs(alpha0)
        sRightHandle += sTangent  # position of first pt's handle
        eLeftHandle = data_pts[e].co.copy()
        eTangent = t2 * abs(alpha1)
        eLeftHandle += eTangent  # position of last pt's handle.

        # return a 4 member tuple representing the bezier
        return (data_pts[s].co,
              sRightHandle,
              eLeftHandle,
              data_pts[e].co)

    # convert 2 given data points into a cubic bezier.
    # handles are offset along the tangent at
    # a 3rd of the length between the points.
    def fitSingleCubic2Pts(data_pts, s, e):
        alpha0 = alpha1 = (data_pts[s].co - data_pts[e].co).length / 3

        sRightHandle = data_pts[s].co.copy()
        sTangent = unitTangent(s, data_pts) * abs(alpha0)
        sRightHandle += sTangent  # position of first pt's handle
        eLeftHandle = data_pts[e].co.copy()
        eTangent = unitTangent(e, data_pts) * abs(alpha1)
        eLeftHandle += eTangent  # position of last pt's handle.

        #return a 4 member tuple representing the bezier
        return (data_pts[s].co,
          sRightHandle,
          eLeftHandle,
          data_pts[e].co)

    #evaluate bezier, represented by a 4 member tuple (pts) at point t.
    def bezierEval(pts, t):
        sumVec = NdVector((0, 0, 0, 0, 0))
        for i in range(4):
            sumVec += pts[i] * bernsteinPoly(3, i, t)
        return sumVec

    #calculate the highest error between bezier and original data
    #returns the distance and the index of the point where max error occurs.
    def maxErrorAmount(data_pts, bez, s, e):
        maxError = 0
        maxErrorPt = s
        if e - s < 3:
            return 0, None
        for pt in data_pts[s:e + 1]:
            bezVal = bezierEval(bez, pt.u)
            tmpError = (pt.co - bezVal).length / pt.co.length
            if tmpError >= maxError:
                maxError = tmpError
                maxErrorPt = pt.index
        return maxError, maxErrorPt

    #calculated bezier derivative at point t.
    #That is, tangent of point t.
    def getBezDerivative(bez, t):
        n = len(bez) - 1
        sumVec = NdVector((0, 0, 0, 0, 0))
        for i in range(n - 1):
            sumVec += (bez[i + 1] - bez[i]) * bernsteinPoly(n - 1, i, t)
        return sumVec

    #use Newton-Raphson to find a better paramterization of datapoints,
    #one that minimizes the distance (or error)
    # between bezier and original data.
    def newtonRaphson(data_pts, s, e, bez):
        for pt in data_pts[s:e + 1]:
            if pt.index == s:
                pt.u = 0
            elif pt.index == e:
                pt.u = 1
            else:
                u = pt.u
                qu = bezierEval(bez, pt.u)
                qud = getBezDerivative(bez, u)
                #we wish to minimize f(u),
                #the squared distance between curve and data
                fu = (qu - pt.co).length ** 2
                fud = (2 * (qu.x - pt.co.x) * (qud.x)) - (2 * (qu.y - pt.co.y) * (qud.y))
                if fud == 0:
                    fu = 0
                    fud = 1
                pt.u = pt.u - (fu / fud)

    def createDataPts(curveGroup, group_mode):
        data_pts = []
        if group_mode:
            print([x.data_path for x in curveGroup])
            for i in range(len(curveGroup[0].keyframe_points)):
                x = curveGroup[0].keyframe_points[i].co.x
                y1 = curveGroup[0].keyframe_points[i].co.y
                y2 = curveGroup[1].keyframe_points[i].co.y
                y3 = curveGroup[2].keyframe_points[i].co.y
                y4 = 0
                if len(curveGroup) == 4:
                    y4 = curveGroup[3].keyframe_points[i].co.y
                data_pts.append(dataPoint(i, NdVector((x, y1, y2, y3, y4))))
        else:
            for i in range(len(curveGroup.keyframe_points)):
                x = curveGroup.keyframe_points[i].co.x
                y1 = curveGroup.keyframe_points[i].co.y
                y2 = 0
                y3 = 0
                y4 = 0
                data_pts.append(dataPoint(i, NdVector((x, y1, y2, y3, y4))))
        return data_pts

    def fitCubic(data_pts, s, e):
        # if there are less than 3 points, fit a single basic bezier
        if e - s < 3:
            bez = fitSingleCubic2Pts(data_pts, s, e)
        else:
            #if there are more, parameterize the points
            # and fit a single cubic bezier
            chordLength(data_pts, s, e)
            bez = fitSingleCubic(data_pts, s, e)

        #calculate max error and point where it occurs
        maxError, maxErrorPt = maxErrorAmount(data_pts, bez, s, e)
        #if error is small enough, reparameterization might be enough
        if maxError < reparaError and maxError > error:
            for i in range(maxIterations):
                newtonRaphson(data_pts, s, e, bez)
                if e - s < 3:
                    bez = fitSingleCubic2Pts(data_pts, s, e)
                else:
                    bez = fitSingleCubic(data_pts, s, e)

        #recalculate max error and point where it occurs
        maxError, maxErrorPt = maxErrorAmount(data_pts, bez, s, e)

        #repara wasn't enough, we need 2 beziers for this range.
        #Split the bezier at point of maximum error
        if maxError > error:
            fitCubic(data_pts, s, maxErrorPt)
            fitCubic(data_pts, maxErrorPt, e)
        else:
            #error is small enough, return the beziers.
            beziers.append(bez)
            return

    def createNewCurves(curveGroup, beziers, group_mode):
        #remove all existing data points
        if group_mode:
            for fcurve in curveGroup:
                for i in range(len(fcurve.keyframe_points) - 1, 0, -1):
                    fcurve.keyframe_points.remove(fcurve.keyframe_points[i])
        else:
            fcurve = curveGroup
            for i in range(len(fcurve.keyframe_points) - 1, 0, -1):
                fcurve.keyframe_points.remove(fcurve.keyframe_points[i])

        #insert the calculated beziers to blender data.\
        if group_mode:
            for fullbez in beziers:
                for i, fcurve in enumerate(curveGroup):
                    bez = [Vector((vec[0], vec[i + 1])) for vec in fullbez]
                    newKey = fcurve.keyframe_points.insert(frame=bez[0].x, value=bez[0].y)
                    newKey.handle_right = (bez[1].x, bez[1].y)

                    newKey = fcurve.keyframe_points.insert(frame=bez[3].x, value=bez[3].y)
                    newKey.handle_left = (bez[2].x, bez[2].y)
        else:
            for bez in beziers:
                for vec in bez:
                    vec.resize_2d()
                newKey = fcurve.keyframe_points.insert(frame=bez[0].x, value=bez[0].y)
                newKey.handle_right = (bez[1].x, bez[1].y)

                newKey = fcurve.keyframe_points.insert(frame=bez[3].x, value=bez[3].y)
                newKey.handle_left = (bez[2].x, bez[2].y)

    # indices are detached from data point's frame (x) value and
    # stored in the dataPoint object, represent a range

    data_pts = createDataPts(curveGroup, group_mode)

    s = 0  # start
    e = len(data_pts) - 1  # end

    beziers = []

    #begin the recursive fitting algorithm.
    fitCubic(data_pts, s, e)
    #remove old Fcurves and insert the new ones
    createNewCurves(curveGroup, beziers, group_mode)

#Main function of simplification
#sel_opt: either "sel" or "all" for which curves to effect
#error: maximum error allowed, in fraction (20% = 0.0020),
#i.e. divide by 10000 from percentage wanted.
#group_mode: boolean, to analyze each curve seperately or in groups,
#where group is all curves that effect the same property
#(e.g. a bone's x,y,z rotation)


def fcurves_simplify(sel_opt="all", error=0.002, group_mode=True):
    # main vars
    context = bpy.context
    obj = context.active_object
    fcurves = obj.animation_data.action.fcurves

    if sel_opt == "sel":
        sel_fcurves = [fcurve for fcurve in fcurves if fcurve.select]
    else:
        sel_fcurves = fcurves[:]

    #Error threshold for Newton Raphson reparamatizing
    reparaError = error * 32
    maxIterations = 16

    if group_mode:
        fcurveDict = {}
        #this loop sorts all the fcurves into groups of 3 or 4,
        #based on their RNA Data path, which corresponds to
        #which property they effect
        for curve in sel_fcurves:
            if curve.data_path in fcurveDict:  # if this bone has been added, append the curve to its list
                fcurveDict[curve.data_path].append(curve)
            else:
                fcurveDict[curve.data_path] = [curve]  # new bone, add a new dict value with this first curve
        fcurveGroups = fcurveDict.values()
    else:
        fcurveGroups = sel_fcurves

    if error > 0.00000:
        #simplify every selected curve.
        totalt = 0
        for i, fcurveGroup in enumerate(fcurveGroups):
            print("Processing curve " + str(i + 1) + "/" + str(len(fcurveGroups)))
            t = time.clock()
            simplifyCurves(fcurveGroup, error, reparaError, maxIterations, group_mode)
            t = time.clock() - t
            print(str(t)[:5] + " seconds to process last curve")
            totalt += t
            print(str(totalt)[:5] + " seconds, total time elapsed")

    return

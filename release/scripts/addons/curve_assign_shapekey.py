#
#
# This Blender add-on assigns one or more Bezier Curves as shape keys to another
# Bezier Curve
#
# Supported Blender Versions: 2.8x
#
# Copyright (C) 2019  Shrinivas Kulkarni
#
# License: GPL-3.0 (https://github.com/Shriinivas/assignshapekey/blob/master/LICENSE)
#

import bpy, bmesh, bgl, gpu
from gpu_extras.batch import batch_for_shader
from bpy.props import BoolProperty, EnumProperty, StringProperty
from collections import OrderedDict
from mathutils import Vector
from math import sqrt, floor
from functools import cmp_to_key
from bpy.types import Panel, Operator, AddonPreferences


bl_info = {
    "name": "Assign Shape Keys",
    "author": "Shrinivas Kulkarni",
    "version": (1, 0, 1),
    "blender": (2, 80, 0),
    "location": "View 3D > Sidebar > Edit Tab",
    "description": "Assigns one or more Bezier curves as shape keys to another Bezier curve",
    "doc_url": "{BLENDER_MANUAL_URL}/addons/add_curve/assign_shape_keys.html",
    "category": "Add Curve",
}

alignList = [('minX', 'Min X', 'Align vertices with Min X'),
            ('maxX', 'Max X', 'Align vertices with Max X'),
            ('minY', 'Min Y', 'Align vertices with Min Y'),
            ('maxY', 'Max Y', 'Align vertices with Max Y'),
            ('minZ', 'Min Z', 'Align vertices with Min Z'),
            ('maxZ', 'Max Z', 'Align vertices with Max Z')]

matchList = [('vCnt', 'Vertex Count', 'Match by vertex count'),
            ('bbArea', 'Area', 'Match by surface area of the bounding box'), \
            ('bbHeight', 'Height', 'Match by bounding box height'), \
            ('bbWidth', 'Width', 'Match by bounding box width'),
            ('bbDepth', 'Depth', 'Match by bounding box depth'),
            ('minX', 'Min X', 'Match by bounding box Min X'),
            ('maxX', 'Max X', 'Match by bounding box Max X'),
            ('minY', 'Min Y', 'Match by bounding box Min Y'),
            ('maxY', 'Max Y', 'Match by bounding box Max Y'),
            ('minZ', 'Min Z', 'Match by bounding box Min Z'),
            ('maxZ', 'Max Z', 'Match by bounding box Max Z')]

DEF_ERR_MARGIN = 0.0001

def isBezier(obj):
    return obj.type == 'CURVE' and len(obj.data.splines) > 0 \
        and obj.data.splines[0].type == 'BEZIER'

#Avoid errors due to floating point conversions/comparisons
#TODO: return -1, 0, 1
def floatCmpWithMargin(float1, float2, margin = DEF_ERR_MARGIN):
    return abs(float1 - float2) < margin

def vectCmpWithMargin(v1, v2, margin = DEF_ERR_MARGIN):
    return all(floatCmpWithMargin(v1[i], v2[i], margin) for i in range(0, len(v1)))

class Segment():

    #pts[0] - start, pts[1] - ctrl1, pts[2] - ctrl2, , pts[3] - end
    def pointAtT(pts, t):
        return pts[0] + t * (3 * (pts[1] - pts[0]) +
            t* (3 * (pts[0] + pts[2]) - 6 * pts[1] +
                t * (-pts[0] + 3 * (pts[1] - pts[2]) + pts[3])))

    def getSegLenRecurs(pts, start, end, t1 = 0, t2 = 1, error = DEF_ERR_MARGIN):
        t1_5 = (t1 + t2)/2
        mid = Segment.pointAtT(pts, t1_5)
        l = (end - start).length
        l2 = (mid - start).length + (end - mid).length
        if (l2 - l > error):
            return (Segment.getSegLenRecurs(pts, start, mid, t1, t1_5, error) +
                    Segment.getSegLenRecurs(pts, mid, end, t1_5, t2, error))
        return l2

    def __init__(self, start, ctrl1, ctrl2, end):
        self.start = start
        self.ctrl1 = ctrl1
        self.ctrl2 = ctrl2
        self.end = end
        pts = [start, ctrl1, ctrl2, end]
        self.length = Segment.getSegLenRecurs(pts, start, end)

    #see https://stackoverflow.com/questions/878862/drawing-part-of-a-b%c3%a9zier-curve-by-reusing-a-basic-b%c3%a9zier-curve-function/879213#879213
    def partialSeg(self, t0, t1):
        pts = [self.start, self.ctrl1, self.ctrl2, self.end]

        if(t0 > t1):
            tt = t1
            t1 = t0
            t0 = tt

        #Let's make at least the line segments of predictable length :)
        if(pts[0] == pts[1] and pts[2] == pts[3]):
            pt0 = Vector([(1 - t0) * pts[0][i] + t0 * pts[2][i] for i in range(0, 3)])
            pt1 = Vector([(1 - t1) * pts[0][i] + t1 * pts[2][i] for i in range(0, 3)])
            return Segment(pt0, pt0, pt1, pt1)

        u0 = 1.0 - t0
        u1 = 1.0 - t1

        qa = [pts[0][i]*u0*u0 + pts[1][i]*2*t0*u0 + pts[2][i]*t0*t0 for i in range(0, 3)]
        qb = [pts[0][i]*u1*u1 + pts[1][i]*2*t1*u1 + pts[2][i]*t1*t1 for i in range(0, 3)]
        qc = [pts[1][i]*u0*u0 + pts[2][i]*2*t0*u0 + pts[3][i]*t0*t0 for i in range(0, 3)]
        qd = [pts[1][i]*u1*u1 + pts[2][i]*2*t1*u1 + pts[3][i]*t1*t1 for i in range(0, 3)]

        pta = Vector([qa[i]*u0 + qc[i]*t0 for i in range(0, 3)])
        ptb = Vector([qa[i]*u1 + qc[i]*t1 for i in range(0, 3)])
        ptc = Vector([qb[i]*u0 + qd[i]*t0 for i in range(0, 3)])
        ptd = Vector([qb[i]*u1 + qd[i]*t1 for i in range(0, 3)])

        return Segment(pta, ptb, ptc, ptd)

    #see https://stackoverflow.com/questions/24809978/calculating-the-bounding-box-of-cubic-bezier-curve
    #(3 D - 9 C + 9 B - 3 A) t^2 + (6 A - 12 B + 6 C) t + 3 (B - A)
    #pts[0] - start, pts[1] - ctrl1, pts[2] - ctrl2, , pts[3] - end
    #TODO: Return Vectors to make world space calculations consistent
    def bbox(self, mw = None):
        def evalBez(AA, BB, CC, DD, t):
            return AA * (1 - t) * (1 - t) * (1 - t) + \
                    3 * BB * t * (1 - t) * (1 - t) + \
                        3 * CC * t * t * (1 - t) + \
                            DD * t * t * t

        A = self.start
        B = self.ctrl1
        C = self.ctrl2
        D = self.end

        if(mw != None):
            A = mw @ A
            B = mw @ B
            C = mw @ C
            D = mw @ D

        MINXYZ = [min([A[i], D[i]]) for i in range(0, 3)]
        MAXXYZ = [max([A[i], D[i]]) for i in range(0, 3)]
        leftBotBack_rgtTopFront = [MINXYZ, MAXXYZ]

        a = [3 * D[i] - 9 * C[i] + 9 * B[i] - 3 * A[i] for i in range(0, 3)]
        b = [6 * A[i] - 12 * B[i] + 6 * C[i] for i in range(0, 3)]
        c = [3 * (B[i] - A[i]) for i in range(0, 3)]

        solnsxyz = []
        for i in range(0, 3):
            solns = []
            if(a[i] == 0):
                if(b[i] == 0):
                    solns.append(0)#Independent of t so lets take the starting pt
                else:
                    solns.append(c[i] / b[i])
            else:
                rootFact = b[i] * b[i] - 4 * a[i] * c[i]
                if(rootFact >=0 ):
                    #Two solutions with + and - sqrt
                    solns.append((-b[i] + sqrt(rootFact)) / (2 * a[i]))
                    solns.append((-b[i] - sqrt(rootFact)) / (2 * a[i]))
            solnsxyz.append(solns)

        for i, soln in enumerate(solnsxyz):
            for j, t in enumerate(soln):
                if(t < 1 and t > 0):
                    co = evalBez(A[i], B[i], C[i], D[i], t)
                    if(co < leftBotBack_rgtTopFront[0][i]):
                        leftBotBack_rgtTopFront[0][i] = co
                    if(co > leftBotBack_rgtTopFront[1][i]):
                        leftBotBack_rgtTopFront[1][i] = co

        return leftBotBack_rgtTopFront


class Part():
    def __init__(self, parent, segs, isClosed):
        self.parent = parent
        self.segs = segs

        #use_cyclic_u
        self.isClosed = isClosed

        #Indicates if this should be closed based on its counterparts in other paths
        self.toClose = isClosed

        self.length = sum(seg.length for seg in self.segs)
        self.bbox = None
        self.bboxWorldSpace = None

    def getSeg(self, idx):
        return self.segs[idx]

    def getSegs(self):
        return self.segs

    def getSegsCopy(self, start, end):
        if(start == None):
            start = 0
        if(end == None):
            end = len(self.segs)
        return self.segs[start:end]

    def getBBox(self, worldSpace):
        #Avoid frequent calculations, as this will be called in compare method
        if(not worldSpace and self.bbox != None):
            return self.bbox

        if(worldSpace and self.bboxWorldSpace != None):
            return self.bboxWorldSpace

        leftBotBack_rgtTopFront = [[None]*3,[None]*3]

        for seg in self.segs:

            if(worldSpace):
                bb = seg.bbox(self.parent.curve.matrix_world)
            else:
                bb = seg.bbox()

            for i in range(0, 3):
                if (leftBotBack_rgtTopFront[0][i] == None or \
                    bb[0][i] < leftBotBack_rgtTopFront[0][i]):
                    leftBotBack_rgtTopFront[0][i] = bb[0][i]

            for i in range(0, 3):
                if (leftBotBack_rgtTopFront[1][i] == None or \
                    bb[1][i] > leftBotBack_rgtTopFront[1][i]):
                    leftBotBack_rgtTopFront[1][i] = bb[1][i]

        if(worldSpace):
            self.bboxWorldSpace = leftBotBack_rgtTopFront
        else:
            self.bbox = leftBotBack_rgtTopFront

        return leftBotBack_rgtTopFront

    #private
    def getBBDiff(self, axisIdx, worldSpace):
        obj = self.parent.curve
        bbox = self.getBBox(worldSpace)
        diff = abs(bbox[1][axisIdx] - bbox[0][axisIdx])
        return diff

    def getBBWidth(self, worldSpace):
        return self.getBBDiff(0, worldSpace)

    def getBBHeight(self, worldSpace):
        return self.getBBDiff(1, worldSpace)

    def getBBDepth(self, worldSpace):
        return self.getBBDiff(2, worldSpace)

    def bboxSurfaceArea(self, worldSpace):
        leftBotBack_rgtTopFront = self.getBBox(worldSpace)
        w = abs( leftBotBack_rgtTopFront[1][0] - leftBotBack_rgtTopFront[0][0] )
        l = abs( leftBotBack_rgtTopFront[1][1] - leftBotBack_rgtTopFront[0][1] )
        d = abs( leftBotBack_rgtTopFront[1][2] - leftBotBack_rgtTopFront[0][2] )

        return 2 * (w * l + w * d + l * d)

    def getSegCnt(self):
        return len(self.segs)

    def getBezierPtsInfo(self):
        prevSeg = None
        bezierPtsInfo = []

        for j, seg in enumerate(self.getSegs()):

            pt = seg.start
            handleRight = seg.ctrl1

            if(j == 0):
                if(self.toClose):
                    handleLeft = self.getSeg(-1).ctrl2
                else:
                    handleLeft = pt
            else:
                handleLeft = prevSeg.ctrl2

            bezierPtsInfo.append([pt, handleLeft, handleRight])
            prevSeg = seg

        if(self.toClose == True):
            bezierPtsInfo[-1][2] = seg.ctrl1
        else:
            bezierPtsInfo.append([prevSeg.end, prevSeg.ctrl2, prevSeg.end])

        return bezierPtsInfo

    def __repr__(self):
        return str(self.length)


class Path:
    def __init__(self, curve, objData = None, name = None):

        if(objData == None):
            objData = curve.data

        if(name == None):
            name = curve.name

        self.name = name
        self.curve = curve

        self.parts = [Part(self, getSplineSegs(s), s.use_cyclic_u) for s in objData.splines]

    def getPartCnt(self):
        return len(self.parts)

    def getPartView(self):
        p = Part(self, [seg for part in self.parts for seg in part.getSegs()], None)
        return p

    def getPartBoundaryIdxs(self):
        cumulCntList = set()
        cumulCnt = 0

        for p in self.parts:
            cumulCnt += p.getSegCnt()
            cumulCntList.add(cumulCnt)

        return cumulCntList

    def updatePartsList(self, segCntsPerPart, byPart):
        monolithicSegList = [seg for part in self.parts for seg in part.getSegs()]
        oldParts = self.parts[:]
        currPart = oldParts[0]
        partIdx = 0
        self.parts.clear()

        for i in range(0, len(segCntsPerPart)):
            if( i == 0):
                currIdx = 0
            else:
                currIdx = segCntsPerPart[i-1]

            nextIdx = segCntsPerPart[i]
            isClosed = False

            if(vectCmpWithMargin(monolithicSegList[currIdx].start, \
                    currPart.getSegs()[0].start) and \
                vectCmpWithMargin(monolithicSegList[nextIdx-1].end, \
                    currPart.getSegs()[-1].end)):
                isClosed = currPart.isClosed

            self.parts.append(Part(self, \
                monolithicSegList[currIdx:nextIdx], isClosed))

            if(monolithicSegList[nextIdx-1] == currPart.getSegs()[-1]):
                partIdx += 1
                if(partIdx < len(oldParts)):
                    currPart = oldParts[partIdx]

    def getBezierPtsBySpline(self):
        data = []

        for i, part in enumerate(self.parts):
            data.append(part.getBezierPtsInfo())

        return data

    def getNewCurveData(self):

        newCurveData = self.curve.data.copy()
        newCurveData.splines.clear()

        splinesData = self.getBezierPtsBySpline()

        for i, newPoints in enumerate(splinesData):

            spline = newCurveData.splines.new('BEZIER')
            spline.bezier_points.add(len(newPoints)-1)
            spline.use_cyclic_u = self.parts[i].toClose

            for j in range(0, len(spline.bezier_points)):
                newPoint = newPoints[j]
                spline.bezier_points[j].co = newPoint[0]
                spline.bezier_points[j].handle_left = newPoint[1]
                spline.bezier_points[j].handle_right = newPoint[2]
                spline.bezier_points[j].handle_right_type = 'FREE'

        return newCurveData

    def updateCurve(self):
        curveData = self.curve.data
        #Remove existing shape keys first
        if(curveData.shape_keys != None):
            keyblocks = reversed(curveData.shape_keys.key_blocks)
            for sk in keyblocks:
                self.curve.shape_key_remove(sk)
        self.curve.data = self.getNewCurveData()
        bpy.data.curves.remove(curveData)

def main(targetObj, shapekeyObjs, removeOriginal, space, matchParts, \
    matchCriteria, alignBy, alignValues):

    target = Path(targetObj)

    shapekeys = [Path(c) for c in shapekeyObjs]

    existingKeys = getExistingShapeKeyPaths(target)
    shapekeys = existingKeys + shapekeys
    userSel = [target] + shapekeys

    for path in userSel:
        alignPath(path, matchParts, matchCriteria, alignBy, alignValues)

    addMissingSegs(userSel, byPart = (matchParts != "-None-"))

    bIdxs = set()
    for path in userSel:
        bIdxs = bIdxs.union(path.getPartBoundaryIdxs())

    for path in userSel:
        path.updatePartsList(sorted(list(bIdxs)), byPart = False)

    #All will have the same part count by now
    allToClose = [all(path.parts[j].isClosed for path in userSel)
        for j in range(0, len(userSel[0].parts))]

    #All paths will have the same no of splines with the same no of bezier points
    for path in userSel:
        for j, part in enumerate(path.parts):
            part.toClose = allToClose[j]

    target.updateCurve()

    if(len(existingKeys) == 0):
        target.curve.shape_key_add(name = 'Basis')

    addShapeKeys(target.curve, shapekeys, space)

    if(removeOriginal):
        for path in userSel:
            if(path.curve != target.curve):
                safeRemoveObj(path.curve)

def getSplineSegs(spline):
    p = spline.bezier_points
    segs = [Segment(p[i-1].co, p[i-1].handle_right, p[i].handle_left, p[i].co) \
        for i in range(1, len(p))]
    if(spline.use_cyclic_u):
        segs.append(Segment(p[-1].co, p[-1].handle_right, p[0].handle_left, p[0].co))
    return segs

def subdivideSeg(origSeg, noSegs):
    if(noSegs < 2):
        return [origSeg]

    segs = []
    oldT = 0
    segLen = origSeg.length / noSegs

    for i in range(0, noSegs-1):
        t = float(i+1) / noSegs
        seg = origSeg.partialSeg(oldT, t)
        segs.append(seg)
        oldT = t

    seg = origSeg.partialSeg(oldT, 1)
    segs.append(seg)

    return segs


def getSubdivCntPerSeg(part, toAddCnt):

    class SegWrapper:
        def __init__(self, idx, seg):
            self.idx = idx
            self.seg = seg
            self.length = seg.length

    class PartWrapper:
        def __init__(self, part):
            self.segList = []
            self.segCnt = len(part.getSegs())
            for idx, seg in enumerate(part.getSegs()):
                self.segList.append(SegWrapper(idx, seg))

    partWrapper = PartWrapper(part)
    partLen = part.length
    avgLen = partLen / (partWrapper.segCnt + toAddCnt)

    segsToDivide = [sr for sr in partWrapper.segList if sr.seg.length >= avgLen]
    segToDivideCnt = len(segsToDivide)
    avgLen = sum(sr.seg.length for sr in segsToDivide) / (segToDivideCnt + toAddCnt)

    segsToDivide = sorted(segsToDivide, key=lambda x: x.length, reverse = True)

    cnts = [0] * partWrapper.segCnt
    addedCnt = 0


    for i in range(0, segToDivideCnt):
        segLen = segsToDivide[i].seg.length

        divideCnt = int(round(segLen/avgLen)) - 1
        if(divideCnt == 0):
            break

        if((addedCnt + divideCnt) >= toAddCnt):
            cnts[segsToDivide[i].idx] = toAddCnt - addedCnt
            addedCnt = toAddCnt
            break

        cnts[segsToDivide[i].idx] = divideCnt

        addedCnt += divideCnt

    #TODO: Verify if needed
    while(toAddCnt > addedCnt):
        for i in range(0, segToDivideCnt):
            cnts[segsToDivide[i].idx] += 1
            addedCnt += 1
            if(toAddCnt == addedCnt):
                break

    return cnts

#Just distribute equally; this is likely a rare condition. So why complicate?
def distributeCnt(maxSegCntsByPart, startIdx, extraCnt):
    added = 0
    elemCnt = len(maxSegCntsByPart) - startIdx
    cntPerElem = floor(extraCnt / elemCnt)
    remainder = extraCnt % elemCnt

    for i in range(startIdx, len(maxSegCntsByPart)):
        maxSegCntsByPart[i] += cntPerElem
        if(i < remainder + startIdx):
            maxSegCntsByPart[i] += 1

#Make all the paths to have the maximum number of segments in the set
#TODO: Refactor
def addMissingSegs(selPaths, byPart):
    maxSegCntsByPart = []
    maxSegCnt = 0

    resSegCnt = []
    sortedPaths = sorted(selPaths, key = lambda c: -len(c.parts))

    for i, path in enumerate(sortedPaths):
        if(byPart == False):
            segCnt = path.getPartView().getSegCnt()
            if(segCnt > maxSegCnt):
                maxSegCnt = segCnt
        else:
            resSegCnt.append([])
            for j, part in enumerate(path.parts):
                partSegCnt = part.getSegCnt()
                resSegCnt[i].append(partSegCnt)

                #First path
                if(j == len(maxSegCntsByPart)):
                    maxSegCntsByPart.append(partSegCnt)

                #last part of this path, but other paths in set have more parts
                elif((j == len(path.parts) - 1) and
                    len(maxSegCntsByPart) > len(path.parts)):

                    remainingSegs = sum(maxSegCntsByPart[j:])
                    if(partSegCnt <= remainingSegs):
                        resSegCnt[i][j] = remainingSegs
                    else:
                        #This part has more segs than the sum of the remaining part segs
                        #So distribute the extra count
                        distributeCnt(maxSegCntsByPart, j, (partSegCnt - remainingSegs))

                        #Also, adjust the seg count of the last part of the previous
                        #segments that had fewer than max number of parts
                        for k in range(0, i):
                            if(len(sortedPaths[k].parts) < len(maxSegCntsByPart)):
                                totalSegs = sum(maxSegCntsByPart)
                                existingSegs = sum(maxSegCntsByPart[:len(sortedPaths[k].parts)-1])
                                resSegCnt[k][-1] = totalSegs - existingSegs

                elif(partSegCnt > maxSegCntsByPart[j]):
                    maxSegCntsByPart[j] = partSegCnt
    for i, path in enumerate(sortedPaths):

        if(byPart == False):
            partView = path.getPartView()
            segCnt = partView.getSegCnt()
            diff = maxSegCnt - segCnt

            if(diff > 0):
                cnts = getSubdivCntPerSeg(partView, diff)
                cumulSegIdx = 0
                for j in range(0, len(path.parts)):
                    part = path.parts[j]
                    newSegs = []
                    for k, seg in enumerate(part.getSegs()):
                        numSubdivs = cnts[cumulSegIdx] + 1
                        newSegs += subdivideSeg(seg, numSubdivs)
                        cumulSegIdx += 1

                    path.parts[j] = Part(path, newSegs, part.isClosed)
        else:
            for j in range(0, len(path.parts)):
                part = path.parts[j]
                newSegs = []

                partSegCnt = part.getSegCnt()

                #TODO: Adding everything in the last part?
                if(j == (len(path.parts)-1) and
                    len(maxSegCntsByPart) > len(path.parts)):
                    diff = resSegCnt[i][j] - partSegCnt
                else:
                    diff = maxSegCntsByPart[j] - partSegCnt

                if(diff > 0):
                    cnts = getSubdivCntPerSeg(part, diff)

                    for k, seg in enumerate(part.getSegs()):
                        seg = part.getSeg(k)
                        subdivCnt = cnts[k] + 1 #1 for the existing one
                        newSegs += subdivideSeg(seg, subdivCnt)

                    #isClosed won't be used, but let's update anyway
                    path.parts[j] = Part(path, newSegs, part.isClosed)

#TODO: Simplify (Not very readable)
def alignPath(path, matchParts, matchCriteria, alignBy, alignValues):

    parts = path.parts[:]

    if(matchParts == 'custom'):
        fnMap = {'vCnt' : lambda part: -1 * part.getSegCnt(), \
                 'bbArea': lambda part: -1 * part.bboxSurfaceArea(worldSpace = True), \
                 'bbHeight' : lambda part: -1 * part.getBBHeight(worldSpace = True), \
                 'bbWidth' : lambda part: -1 * part.getBBWidth(worldSpace = True), \
                 'bbDepth' : lambda part: -1 * part.getBBDepth(worldSpace = True)
                }
        matchPartCmpFns = []
        for criterion in matchCriteria:
            fn = fnMap.get(criterion)
            if(fn == None):
                minmax = criterion[:3] == 'max' #0 if min; 1 if max
                axisIdx = ord(criterion[3:]) - ord('X')

                fn = eval('lambda part: part.getBBox(worldSpace = True)[' + \
                    str(minmax) + '][' + str(axisIdx) + ']')

            matchPartCmpFns.append(fn)

        def comparer(left, right):
            for fn in matchPartCmpFns:
                a = fn(left)
                b = fn(right)

                if(floatCmpWithMargin(a, b)):
                    continue
                else:
                    return (a > b) - ( a < b) #No cmp in python3

            return 0

        parts = sorted(parts, key = cmp_to_key(comparer))

    alignCmpFn = None
    if(alignBy == 'vertCo'):
        def evalCmp(criteria, pt1, pt2):
            if(len(criteria) == 0):
                return True

            minmax = criteria[0][0]
            axisIdx = criteria[0][1]
            val1 = pt1[axisIdx]
            val2 = pt2[axisIdx]

            if(floatCmpWithMargin(val1, val2)):
                criteria = criteria[:]
                criteria.pop(0)
                return evalCmp(criteria, pt1, pt2)

            return val1 < val2 if minmax == 'min' else val1 > val2

        alignCri = [[a[:3], ord(a[3:]) - ord('X')] for a in alignValues]
        alignCmpFn = lambda pt1, pt2, curve: (evalCmp(alignCri, \
            curve.matrix_world @ pt1, curve.matrix_world @ pt2))

    startPt = None
    startIdx = None

    for i in range(0, len(parts)):
        #Only truly closed parts
        if(alignCmpFn != None and parts[i].isClosed):
            for j in range(0, parts[i].getSegCnt()):
                seg = parts[i].getSeg(j)
                if(j == 0 or alignCmpFn(seg.start, startPt, path.curve)):
                    startPt = seg.start
                    startIdx = j

            path.parts[i]= Part(path, parts[i].getSegsCopy(startIdx, None) + \
                parts[i].getSegsCopy(None, startIdx), parts[i].isClosed)
        else:
            path.parts[i] = parts[i]

#TODO: Other shape key attributes like interpolation...?
def getExistingShapeKeyPaths(path):
    obj = path.curve
    paths = []

    if(obj.data.shape_keys != None):
        keyblocks = obj.data.shape_keys.key_blocks[:]
        for key in keyblocks:
            datacopy = obj.data.copy()
            i = 0
            for spline in datacopy.splines:
                for pt in spline.bezier_points:
                    pt.co = key.data[i].co
                    pt.handle_left = key.data[i].handle_left
                    pt.handle_right = key.data[i].handle_right
                    i += 1
            paths.append(Path(obj, datacopy, key.name))
    return paths

def addShapeKeys(curve, paths, space):
    for path in paths:
        key = curve.shape_key_add(name = path.name)
        pts = [pt for pset in path.getBezierPtsBySpline() for pt in pset]
        for i, pt in enumerate(pts):
            if(space == 'worldspace'):
                pt = [curve.matrix_world.inverted() @ (path.curve.matrix_world @ p) for p in pt]
            key.data[i].co = pt[0]
            key.data[i].handle_left = pt[1]
            key.data[i].handle_right = pt[2]

#TODO: Remove try
def safeRemoveObj(obj):
    try:
        collections = obj.users_collection

        for c in collections:
            c.objects.unlink(obj)

        if(obj.name in bpy.context.scene.collection.objects):
            bpy.context.scene.collection.objects.unlink(obj)

        if(obj.data.users == 1):
            if(obj.type == 'CURVE'):
                bpy.data.curves.remove(obj.data) #This also removes object?
            elif(obj.type == 'MESH'):
                bpy.data.meshes.remove(obj.data)

        bpy.data.objects.remove(obj)
    except:
        pass


def markVertHandler(self, context):
    if(self.markVertex):
        bpy.ops.wm.mark_vertex()


#################### UI and Registration ####################

class AssignShapeKeysOp(Operator):
    bl_idname = "object.assign_shape_keys"
    bl_label = "Assign Shape Keys"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        params = context.window_manager.AssignShapeKeyParams
        removeOriginal = params.removeOriginal
        space = params.space

        matchParts = params.matchParts
        matchCri1 = params.matchCri1
        matchCri2 = params.matchCri2
        matchCri3 = params.matchCri3

        alignBy = params.alignCos
        alignVal1 = params.alignVal1
        alignVal2 = params.alignVal2
        alignVal3 = params.alignVal3

        targetObj = bpy.context.active_object
        shapekeyObjs = [obj for obj in bpy.context.selected_objects if isBezier(obj) \
            and obj != targetObj]

        if(targetObj != None and isBezier(targetObj) and len(shapekeyObjs) > 0):
            main(targetObj, shapekeyObjs, removeOriginal, space, \
                    matchParts, [matchCri1, matchCri2, matchCri3], \
                            alignBy, [alignVal1, alignVal2, alignVal3])

        return {'FINISHED'}


class MarkerController:
    drawHandlerRef = None
    defPointSize = 6
    ptColor = (0, .8, .8, 1)

    def createSMMap(self, context):
        objs = context.selected_objects
        smMap = {}
        for curve in objs:
            if(not isBezier(curve)):
                continue

            smMap[curve.name] = {}
            mw = curve.matrix_world
            for splineIdx, spline in enumerate(curve.data.splines):
                if(not spline.use_cyclic_u):
                    continue

                #initialize to the curr start vert co and idx
                smMap[curve.name][splineIdx] = \
                    [mw @ curve.data.splines[splineIdx].bezier_points[0].co, 0]

                for pt in spline.bezier_points:
                    pt.select_control_point = False

            if(len(smMap[curve.name]) == 0):
                del smMap[curve.name]

        return smMap

    def createBatch(self, context):
        positions = [s[0] for cn in self.smMap.values() for s in cn.values()]
        colors = [MarkerController.ptColor for i in range(0, len(positions))]

        self.batch = batch_for_shader(self.shader, \
            "POINTS", {"pos": positions, "color": colors})

        if context.area:
            context.area.tag_redraw()

    def drawHandler(self):
        bgl.glPointSize(MarkerController.defPointSize)
        self.batch.draw(self.shader)

    def removeMarkers(self, context):
        if(MarkerController.drawHandlerRef != None):
            bpy.types.SpaceView3D.draw_handler_remove(MarkerController.drawHandlerRef, \
                "WINDOW")

            if(context.area and hasattr(context.space_data, 'region_3d')):
                context.area.tag_redraw()

            MarkerController.drawHandlerRef = None

        self.deselectAll()

    def __init__(self, context):
        self.smMap = self.createSMMap(context)
        self.shader = gpu.shader.from_builtin('3D_FLAT_COLOR')
        # self.shader.bind()

        MarkerController.drawHandlerRef = \
            bpy.types.SpaceView3D.draw_handler_add(self.drawHandler, \
                (), "WINDOW", "POST_VIEW")

        self.createBatch(context)

    def saveStartVerts(self):
        for curveName in self.smMap.keys():
            curve = bpy.data.objects[curveName]
            splines = curve.data.splines
            spMap = self.smMap[curveName]

            for splineIdx in spMap.keys():
                markerInfo = spMap[splineIdx]
                if(markerInfo[1] != 0):
                    pts = splines[splineIdx].bezier_points
                    loc, idx = markerInfo[0], markerInfo[1]
                    cnt = len(pts)

                    ptCopy = [[p.co.copy(), p.handle_right.copy(), \
                        p.handle_left.copy(), p.handle_right_type, \
                            p.handle_left_type] for p in pts]

                    for i, pt in enumerate(pts):
                        srcIdx = (idx + i) % cnt
                        p = ptCopy[srcIdx]

                        #Must set the types first
                        pt.handle_right_type = p[3]
                        pt.handle_left_type = p[4]
                        pt.co = p[0]
                        pt.handle_right = p[1]
                        pt.handle_left = p[2]

    def updateSMMap(self):
        for curveName in self.smMap.keys():
            curve = bpy.data.objects[curveName]
            spMap = self.smMap[curveName]
            mw = curve.matrix_world

            for splineIdx in spMap.keys():
                markerInfo = spMap[splineIdx]
                loc, idx = markerInfo[0], markerInfo[1]
                pts = curve.data.splines[splineIdx].bezier_points

                selIdxs = [x for x in range(0, len(pts)) \
                    if pts[x].select_control_point == True]

                selIdx = selIdxs[0] if(len(selIdxs) > 0 ) else idx
                co = mw @ pts[selIdx].co
                self.smMap[curveName][splineIdx] = [co, selIdx]

    def deselectAll(self):
        for curveName in self.smMap.keys():
            curve = bpy.data.objects[curveName]
            for spline in curve.data.splines:
                for pt in spline.bezier_points:
                    pt.select_control_point = False

    def getSpaces3D(context):
        areas3d  = [area for area in context.window.screen.areas \
            if area.type == 'VIEW_3D']

        return [s for a in areas3d for s in a.spaces if s.type == 'VIEW_3D']

    def hideHandles(context):
        states = []
        spaces = MarkerController.getSpaces3D(context)
        for s in spaces:
            if(hasattr(s.overlay, 'show_curve_handles')):
                states.append(s.overlay.show_curve_handles)
                s.overlay.show_curve_handles = False
            elif(hasattr(s.overlay, 'display_handle')): # 2.90
                states.append(s.overlay.display_handle)
                s.overlay.display_handle = 'NONE'
        return states

    def resetShowHandleState(context, handleStates):
        spaces = MarkerController.getSpaces3D(context)
        for i, s in enumerate(spaces):
            if(hasattr(s.overlay, 'show_curve_handles')):
                s.overlay.show_curve_handles = handleStates[i]
            elif(hasattr(s.overlay, 'display_handle')): # 2.90
                s.overlay.display_handle = handleStates[i]


class ModalMarkSegStartOp(Operator):
    bl_description = "Mark Vertex"
    bl_idname = "wm.mark_vertex"
    bl_label = "Mark Start Vertex"

    def cleanup(self, context):
        wm = context.window_manager
        wm.event_timer_remove(self._timer)
        self.markerState.removeMarkers(context)
        MarkerController.resetShowHandleState(context, self.handleStates)
        context.window_manager.AssignShapeKeyParams.markVertex = False

    def modal (self, context, event):
        params = context.window_manager.AssignShapeKeyParams

        if(context.mode  == 'OBJECT' or event.type == "ESC" or\
            not context.window_manager.AssignShapeKeyParams.markVertex):
            self.cleanup(context)
            return {'CANCELLED'}

        elif(event.type == "RET"):
            self.markerState.saveStartVerts()
            self.cleanup(context)
            return {'FINISHED'}

        if(event.type == 'TIMER'):
            self.markerState.updateSMMap()
            self.markerState.createBatch(context)

        return {"PASS_THROUGH"}

    def execute(self, context):
        #TODO: Why such small step?
        self._timer = context.window_manager.event_timer_add(time_step = 0.0001, \
            window = context.window)

        context.window_manager.modal_handler_add(self)
        self.markerState = MarkerController(context)

        #Hide so that users don't accidentally select handles instead of points
        self.handleStates = MarkerController.hideHandles(context)

        return {"RUNNING_MODAL"}


class AssignShapeKeyParams(bpy.types.PropertyGroup):

    removeOriginal : BoolProperty(name = "Remove Shape Key Objects", \
        description = "Remove shape key objects after assigning to target", \
            default = True)

    space : EnumProperty(name = "Space", \
        items = [('worldspace', 'World Space', 'worldspace'),
                 ('localspace', 'Local Space', 'localspace')], \
        description = 'Space that shape keys are evluated in')

    alignCos : EnumProperty(name="Vertex Alignment", items = \
        [("-None-", 'Manual Alignment', "Align curve segments based on starting vertex"), \
         ('vertCo', 'Vertex Coordinates', 'Align curve segments based on vertex coordinates')], \
        description = 'Start aligning the vertices of target and shape keys from',
        default = '-None-')

    alignVal1 : EnumProperty(name="Value 1",
        items = alignList, default = 'minX', description='First align criterion')

    alignVal2 : EnumProperty(name="Value 2",
        items = alignList, default = 'maxY', description='Second align criterion')

    alignVal3 : EnumProperty(name="Value 3",
        items = alignList, default = 'minZ', description='Third align criterion')

    matchParts : EnumProperty(name="Match Parts", items = \
        [("-None-", 'None', "Don't match parts"), \
        ('default', 'Default', 'Use part (spline) order as in curve'), \
        ('custom', 'Custom', 'Use one of the custom criteria for part matching')], \
        description='Match disconnected parts', default = 'default')

    matchCri1 : EnumProperty(name="Value 1",
        items = matchList, default = 'minX', description='First match criterion')

    matchCri2 : EnumProperty(name="Value 2",
        items = matchList, default = 'maxY', description='Second match criterion')

    matchCri3 : EnumProperty(name="Value 3",
        items = matchList, default = 'minZ', description='Third match criterion')

    markVertex : BoolProperty(name="Mark Starting Vertices", \
        description='Mark first vertices in all splines of selected curves', \
            default = False, update = markVertHandler)


class AssignShapeKeysPanel(Panel):

    bl_label = "Curve Shape Keys"
    bl_idname = "CURVE_PT_assign_shape_keys"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Edit"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return context.mode in {'OBJECT', 'EDIT_CURVE'}

    def draw(self, context):

        layout = self.layout
        layout.label(text='Morph Curves:')
        col = layout.column()
        params = context.window_manager.AssignShapeKeyParams

        if(context.mode  == 'OBJECT'):
            row = col.row()
            row.prop(params, "removeOriginal")

            row = col.row()
            row.prop(params, "space")

            row = col.row()
            row.prop(params, "alignCos")

            if(params.alignCos == 'vertCo'):
                row = col.row()
                row.prop(params, "alignVal1")
                row.prop(params, "alignVal2")
                row.prop(params, "alignVal3")

            row = col.row()
            row.prop(params, "matchParts")

            if(params.matchParts == 'custom'):
                row = col.row()
                row.prop(params, "matchCri1")
                row.prop(params, "matchCri2")
                row.prop(params, "matchCri3")

            row = col.row()
            row.operator("object.assign_shape_keys")
        else:
            col.prop(params, "markVertex", \
                toggle = True)


def updatePanel(self, context):
    try:
        panel = AssignShapeKeysPanel
        if "bl_rna" in panel.__dict__:
            bpy.utils.unregister_class(panel)

        panel.bl_category = context.preferences.addons[__name__].preferences.category
        bpy.utils.register_class(panel)

    except Exception as e:
        print("Assign Shape Keys: Updating Panel locations has failed", e)

class AssignShapeKeysPreferences(AddonPreferences):
    bl_idname = __name__

    category: StringProperty(
            name = "Tab Category",
            description = "Choose a name for the category of the panel",
            default = "Edit",
            update = updatePanel
    )

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        col = row.column()
        col.label(text="Tab Category:")
        col.prop(self, "category", text="")

# registering and menu integration
def register():
    bpy.utils.register_class(AssignShapeKeysPanel)
    bpy.utils.register_class(AssignShapeKeysOp)
    bpy.utils.register_class(AssignShapeKeyParams)
    bpy.types.WindowManager.AssignShapeKeyParams = \
        bpy.props.PointerProperty(type=AssignShapeKeyParams)
    bpy.utils.register_class(ModalMarkSegStartOp)
    bpy.utils.register_class(AssignShapeKeysPreferences)
    updatePanel(None, bpy.context)

def unregister():
    bpy.utils.unregister_class(AssignShapeKeysOp)
    bpy.utils.unregister_class(AssignShapeKeysPanel)
    del bpy.types.WindowManager.AssignShapeKeyParams
    bpy.utils.unregister_class(AssignShapeKeyParams)
    bpy.utils.unregister_class(ModalMarkSegStartOp)
    bpy.utils.unregister_class(AssignShapeKeysPreferences)

if __name__ == "__main__":
    register()

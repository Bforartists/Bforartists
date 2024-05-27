# SPDX-FileCopyrightText: 2019-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

import bpy, math, cmath
from mathutils import Vector, Matrix
from collections import namedtuple

units = [
    ('-', 'None', '1.0', 0),
    ('px', 'Pixel', '1.0', 1),
    ('m', 'Meter', '1.0', 2),
    ('dm', 'Decimeter', '0.1', 3),
    ('cm', 'Centimeter', '0.01', 4),
    ('mm', 'Millimeter', '0.001', 5),
    ('yd', 'Yard', '0.9144', 6),
    ('ft', 'Foot', '0.3048', 7),
    ('in', 'Inch', '0.0254', 8)
]

param_tolerance = 0.0001
AABB = namedtuple('AxisAlignedBoundingBox', 'center dimensions')
Plane = namedtuple('Plane', 'normal distance')
Circle = namedtuple('Circle', 'orientation center radius')

def circleOfTriangle(a, b, c):
    # https://en.wikipedia.org/wiki/Circumscribed_circle#Cartesian_coordinates_from_cross-_and_dot-products
    dirBA = a-b
    dirCB = b-c
    dirAC = c-a
    normal = dirBA.cross(dirCB)
    lengthBA = dirBA.length
    lengthCB = dirCB.length
    lengthAC = dirAC.length
    lengthN = normal.length
    if lengthN == 0:
        return None
    factor = -1/(2*lengthN*lengthN)
    alpha = (dirBA@dirAC)*(lengthCB*lengthCB*factor)
    beta = (dirBA@dirCB)*(lengthAC*lengthAC*factor)
    gamma = (dirAC@dirCB)*(lengthBA*lengthBA*factor)
    center = a*alpha+b*beta+c*gamma
    radius = (lengthBA*lengthCB*lengthAC)/(2*lengthN)
    tangent = (a-center).normalized()
    orientation = Matrix.Identity(3)
    orientation.col[2] = normal/lengthN
    orientation.col[1] = (a-center).normalized()
    orientation.col[0] = orientation.col[1].xyz.cross(orientation.col[2].xyz)
    return Circle(orientation=orientation, center=center, radius=radius)

def circleOfBezier(points, tolerance=0.000001, samples=16):
    circle = circleOfTriangle(points[0], bezierPointAt(points, 0.5), points[3])
    if circle == None:
        return None
    variance = 0
    for t in range(0, samples):
        variance += ((circle.center-bezierPointAt(points, (t+1)/(samples-1))).length/circle.radius-1) ** 2
    variance /= samples
    return None if variance > tolerance else circle

def areaOfPolygon(vertices):
    area = 0
    for index, current in enumerate(vertices):
        prev = vertices[index-1]
        area += (current[0]+prev[0])*(current[1]-prev[1])
    return area*0.5

def linePointDistance(begin, dir, point):
    return (point-begin).cross(dir.normalized()).length

def linePlaneIntersection(origin, dir, plane):
    det = dir@plane.normal
    return float('nan') if det == 0 else (plane.distance-origin@plane.normal)/det

def nearestPointOfLines(originA, dirA, originB, dirB, tolerance=0.0):
    # https://en.wikipedia.org/wiki/Skew_lines#Nearest_Points
    normal = dirA.cross(dirB)
    normalA = dirA.cross(normal)
    normalB = dirB.cross(normal)
    divisorA = dirA@normalB
    divisorB = dirB@normalA
    if abs(divisorA) <= tolerance or abs(divisorB) <= tolerance:
        return (float('nan'), float('nan'), None, None)
    else:
        paramA = (originB-originA)@normalB/divisorA
        paramB = (originA-originB)@normalA/divisorB
        return (paramA, paramB, originA+dirA*paramA, originB+dirB*paramB)

def lineSegmentLineSegmentIntersection(beginA, endA, beginB, endB, tolerance=0.001):
    dirA = endA-beginA
    dirB = endB-beginB
    paramA, paramB, pointA, pointB = nearestPointOfLines(beginA, dirA, beginB, dirB)
    if math.isnan(paramA) or (pointA-pointB).length > tolerance or \
       paramA < 0 or paramA > 1 or paramB < 0 or paramB > 1:
        return None
    return (paramA, paramB, pointA, pointB)

def aabbOfPoints(points):
    min = Vector(points[0])
    max = Vector(points[0])
    for point in points:
        for i in range(0, 3):
            if min[i] > point[i]:
                min[i] = point[i]
            if max[i] < point[i]:
                max[i] = point[i]
    return AABB(center=(max+min)*0.5, dimensions=(max-min)*0.5)

def aabbIntersectionTest(a, b, tolerance=0.0):
    for i in range(0, 3):
        if abs(a.center[i]-b.center[i]) > a.dimensions[i]+b.dimensions[i]+tolerance:
            return False
    return True

def isPointInAABB(point, aabb, tolerance=0.0, ignore_axis=None):
    for i in range(0, 3):
        if i != ignore_axis and (point[i] < aabb.center[i]-aabb.dimensions[i]-tolerance or point[i] > aabb.center[i]+aabb.dimensions[i]+tolerance):
            return False
    return True

def lineAABBIntersection(lineBegin, lineEnd, aabb):
    intersections = []
    for i in range(0, 3):
        normal = [0, 0, 0]
        normal = Vector(normal[0:i] + [1] + normal[i+1:])
        for j in range(-1, 2, 2):
            plane = Plane(normal=normal, distance=aabb.center[i]+j*aabb.dimensions[i])
            param = linePlaneIntersection(lineBegin, lineEnd-lineBegin, plane)
            if param < 0 or param > 1 or math.isnan(param):
                continue
            point = lineBegin+param*(lineEnd-lineBegin)
            if isPointInAABB(point, aabb, 0.0, i):
                intersections.append((param, point))
    return intersections

def bezierPointAt(points, t):
    s = 1-t
    return s*s*s*points[0] + 3*s*s*t*points[1] + 3*s*t*t*points[2] + t*t*t*points[3]

def bezierTangentAt(points, t):
    s = 1-t
    return s*s*(points[1]-points[0])+2*s*t*(points[2]-points[1])+t*t*(points[3]-points[2])
    # return s*s*points[0] + (s*s-2*s*t)*points[1] + (2*s*t-t*t)*points[2] + t*t*points[3]

def bezierLength(points, beginT=0, endT=1, samples=1024):
    # https://en.wikipedia.org/wiki/Arc_length#Finding_arc_lengths_by_integrating
    vec = [points[1]-points[0], points[2]-points[1], points[3]-points[2]]
    dot = [vec[0]@vec[0], vec[0]@vec[1], vec[0]@vec[2], vec[1]@vec[1], vec[1]@vec[2], vec[2]@vec[2]]
    factors = [
        dot[0],
        4*(dot[1]-dot[0]),
        6*dot[0]+4*dot[3]+2*dot[2]-12*dot[1],
        12*dot[1]+4*(dot[4]-dot[0]-dot[2])-8*dot[3],
        dot[0]+dot[5]+2*dot[2]+4*(dot[3]-dot[1]-dot[4])
    ]
    # https://en.wikipedia.org/wiki/Trapezoidal_rule
    length = 0
    prev_value = math.sqrt(factors[4]+factors[3]+factors[2]+factors[1]+factors[0])
    for index in range(0, samples+1):
        t = beginT+(endT-beginT)*index/samples
        # value = math.sqrt(factors[4]*(t**4)+factors[3]*(t**3)+factors[2]*(t**2)+factors[1]*t+factors[0])
        value = math.sqrt((((factors[4]*t+factors[3])*t+factors[2])*t+factors[1])*t+factors[0])
        length += (prev_value+value)*0.5
        prev_value = value
    return length*3/samples

# https://en.wikipedia.org/wiki/Root_of_unity
# cubic_roots_of_unity = [cmath.rect(1, i/3*2*math.pi) for i in range(0, 3)]
cubic_roots_of_unity = [complex(1, 0), complex(-1, math.sqrt(3))*0.5, complex(-1, -math.sqrt(3))*0.5]
def bezierRoots(dists, tolerance=0.0001):
    # https://en.wikipedia.org/wiki/Cubic_function
    # y(t) = a*t^3 +b*t^2 +c*t^1 +d*t^0
    a = 3*(dists[1]-dists[2])+dists[3]-dists[0]
    b = 3*(dists[0]-2*dists[1]+dists[2])
    c = 3*(dists[1]-dists[0])
    d = dists[0]
    if abs(a) > tolerance: # Cubic
        E2 = a*c
        E3 = a*a*d
        A = (2*b*b-9*E2)*b+27*E3
        B = b*b-3*E2
        C = ((A+cmath.sqrt(A*A-4*B*B*B))*0.5) ** (1/3)
        roots = []
        for root in cubic_roots_of_unity:
            root *= C
            root = -1/(3*a)*(b+root+B/root)
            if abs(root.imag) < tolerance and root.real > -param_tolerance and root.real < 1.0+param_tolerance:
                roots.append(max(0.0, min(root.real, 1.0)))
        # Remove doubles
        roots.sort()
        for index in range(len(roots)-1, 0, -1):
            if abs(roots[index-1]-roots[index]) < param_tolerance:
                roots.pop(index)
        return roots
    elif abs(b) > tolerance: # Quadratic
        disc = c*c-4*b*d
        if disc < 0:
            return []
        disc = math.sqrt(disc)
        return [(-c-disc)/(2*b), (-c+disc)/(2*b)]
    elif abs(c) > tolerance: # Linear
        root = -d/c
        return [root] if root >= 0.0 and root <= 1.0 else []
    else: # Constant / Parallel
        return [] if abs(d) > tolerance else float('inf')

def xRaySplineIntersectionTest(spline, origin):
    spline_points = spline.bezier_points if spline.type == 'BEZIER' else spline.points
    cyclic_parallel_fix_flag = False
    intersections = []

    def areIntersectionsAdjacent(index):
        if len(intersections) < 2:
            return
        prev = intersections[index-1]
        current = intersections[index]
        if prev[1] == current[0] and \
           prev[2] > 1.0-param_tolerance and current[2] < param_tolerance and \
           ((prev[3] < 0 and current[3] < 0) or (prev[3] > 0 and current[3] > 0)):
            intersections.pop(index)

    def appendIntersection(index, root, tangentY, intersectionX):
        beginPoint = spline_points[index-1]
        endPoint = spline_points[index]
        if root == float('inf'): # Segment is parallel to ray
            if index == 0 and spline.use_cyclic_u:
                cyclic_parallel_fix_flag = True
            if len(intersections) > 0 and intersections[-1][1] == beginPoint:
                intersections[-1][1] = endPoint # Skip in adjacency test
        elif intersectionX >= origin[0]:
            intersections.append([beginPoint, endPoint, root, tangentY, intersectionX])
            areIntersectionsAdjacent(len(intersections)-1)

    if spline.type == 'BEZIER':
        for index, endPoint in enumerate(spline.bezier_points):
            if index == 0 and not spline.use_cyclic_u:
                continue
            beginPoint = spline_points[index-1]
            points = (beginPoint.co, beginPoint.handle_right, endPoint.handle_left, endPoint.co)
            roots = bezierRoots((points[0][1]-origin[1], points[1][1]-origin[1], points[2][1]-origin[1], points[3][1]-origin[1]))
            if roots == float('inf'): # Intersection
                appendIntersection(index, float('inf'), None, None)
            else:
                for root in roots:
                    appendIntersection(index, root, bezierTangentAt(points, root)[1], bezierPointAt(points, root)[0])
    elif spline.type == 'POLY':
        for index, endPoint in enumerate(spline.points):
            if index == 0 and not spline.use_cyclic_u:
                continue
            beginPoint = spline_points[index-1]
            points = (beginPoint.co, endPoint.co)
            if (points[0][0] < origin[0] and points[1][0] < origin[0]) or \
               (points[0][1] < origin[1] and points[1][1] < origin[1]) or \
               (points[0][1] > origin[1] and points[1][1] > origin[1]):
                continue
            diff = points[1]-points[0]
            height = origin[1]-points[0][1]
            if diff[1] == 0: # Parallel
                if height == 0: # Intersection
                    appendIntersection(index, float('inf'), None, None)
            else: # Not parallel
                root = height/diff[1]
                appendIntersection(index, root, diff[1], points[0][0]+diff[0]*root)

    if cyclic_parallel_fix_flag:
        appendIntersection(0, float('inf'), None, None)
    areIntersectionsAdjacent(0)
    return intersections

def isPointInSpline(point, spline):
    return spline.use_cyclic_u and len(xRaySplineIntersectionTest(spline, point))%2 == 1

def isSegmentLinear(points, tolerance=0.0001):
    return 1.0-(points[1]-points[0]).normalized()@(points[3]-points[2]).normalized() < tolerance

def bezierSegmentPoints(begin, end):
    return [begin.co, begin.handle_right, end.handle_left, end.co]

def grab_cursor(context, event):
    if event.mouse_region_x < 0:
        context.window.cursor_warp(context.region.x+context.region.width, event.mouse_y)
    elif event.mouse_region_x > context.region.width:
        context.window.cursor_warp(context.region.x, event.mouse_y)
    elif event.mouse_region_y < 0:
        context.window.cursor_warp(event.mouse_x, context.region.y+context.region.height)
    elif event.mouse_region_y > context.region.height:
        context.window.cursor_warp(event.mouse_x, context.region.y)

def deleteFromArray(item, array):
    for index, current in enumerate(array):
        if current is item:
            array.pop(index)
            break

def copyAttributes(dst, src):
    for attribute in dir(src):
        try:
            setattr(dst, attribute, getattr(src, attribute))
        except:
            pass

def bezierSliceFromTo(points, minParam, maxParam):
    fromP = bezierPointAt(points, minParam)
    fromT = bezierTangentAt(points, minParam)
    toP = bezierPointAt(points, maxParam)
    toT = bezierTangentAt(points, maxParam)
    paramDiff = maxParam-minParam
    return [fromP, fromP+fromT*paramDiff, toP-toT*paramDiff, toP]

def bezierIntersectionBroadPhase(solutions, pointsA, pointsB, aMin=0.0, aMax=1.0, bMin=0.0, bMax=1.0, depth=8, tolerance=0.001):
    if aabbIntersectionTest(aabbOfPoints(bezierSliceFromTo(pointsA, aMin, aMax)), aabbOfPoints(bezierSliceFromTo(pointsB, bMin, bMax)), tolerance) == False:
        return
    if depth == 0:
        solutions.append([aMin, aMax, bMin, bMax])
        return
    depth -= 1
    aMid = (aMin+aMax)*0.5
    bMid = (bMin+bMax)*0.5
    bezierIntersectionBroadPhase(solutions, pointsA, pointsB, aMin, aMid, bMin, bMid, depth, tolerance)
    bezierIntersectionBroadPhase(solutions, pointsA, pointsB, aMin, aMid, bMid, bMax, depth, tolerance)
    bezierIntersectionBroadPhase(solutions, pointsA, pointsB, aMid, aMax, bMin, bMid, depth, tolerance)
    bezierIntersectionBroadPhase(solutions, pointsA, pointsB, aMid, aMax, bMid, bMax, depth, tolerance)

def bezierIntersectionNarrowPhase(broadPhase, pointsA, pointsB, tolerance=0.000001):
    aMin = broadPhase[0]
    aMax = broadPhase[1]
    bMin = broadPhase[2]
    bMax = broadPhase[3]
    while (aMax-aMin > tolerance) or (bMax-bMin > tolerance):
        aMid = (aMin+aMax)*0.5
        bMid = (bMin+bMax)*0.5
        a1 = bezierPointAt(pointsA, (aMin+aMid)*0.5)
        a2 = bezierPointAt(pointsA, (aMid+aMax)*0.5)
        b1 = bezierPointAt(pointsB, (bMin+bMid)*0.5)
        b2 = bezierPointAt(pointsB, (bMid+bMax)*0.5)
        a1b1Dist = (a1-b1).length
        a2b1Dist = (a2-b1).length
        a1b2Dist = (a1-b2).length
        a2b2Dist = (a2-b2).length
        minDist = min(a1b1Dist, a2b1Dist, a1b2Dist, a2b2Dist)
        if a1b1Dist == minDist:
            aMax = aMid
            bMax = bMid
        elif a2b1Dist == minDist:
            aMin = aMid
            bMax = bMid
        elif a1b2Dist == minDist:
            aMax = aMid
            bMin = bMid
        else:
            aMin = aMid
            bMin = bMid
    return [aMin, bMin, minDist]

def segmentIntersection(segmentA, segmentB, tolerance=0.001):
    pointsA = bezierSegmentPoints(segmentA['beginPoint'], segmentA['endPoint'])
    pointsB = bezierSegmentPoints(segmentB['beginPoint'], segmentB['endPoint'])
    result = []
    def addCut(paramA, paramB):
        cutA = {'param': paramA, 'segment': segmentA}
        cutB = {'param': paramB, 'segment': segmentB}
        cutA['otherCut'] = cutB
        cutB['otherCut'] = cutA
        segmentA['cuts'].append(cutA)
        segmentB['cuts'].append(cutB)
        result.append([cutA, cutB])
    if isSegmentLinear(pointsA) and isSegmentLinear(pointsB):
        intersection = lineSegmentLineSegmentIntersection(pointsA[0], pointsA[3], pointsB[0], pointsB[3])
        if intersection != None:
            addCut(intersection[0], intersection[1])
        return result
    solutions = []
    bezierIntersectionBroadPhase(solutions, pointsA, pointsB)
    for index in range(0, len(solutions)):
        solutions[index] = bezierIntersectionNarrowPhase(solutions[index], pointsA, pointsB)
    for index in range(0, len(solutions)):
        for otherIndex in range(0, len(solutions)):
            if solutions[index][2] == float('inf'):
                break
            if index == otherIndex or solutions[otherIndex][2] == float('inf'):
                continue
            diffA = solutions[index][0]-solutions[otherIndex][0]
            diffB = solutions[index][1]-solutions[otherIndex][1]
            if diffA*diffA+diffB*diffB < 0.01:
                if solutions[index][2] < solutions[otherIndex][2]:
                    solutions[otherIndex][2] = float('inf')
                else:
                    solutions[index][2] = float('inf')
    def areIntersectionsAdjacent(segmentA, segmentB, paramA, paramB):
        return segmentA['endIndex'] == segmentB['beginIndex'] and paramA > 1-param_tolerance and paramB < param_tolerance
    for solution in solutions:
        if (solution[2] > tolerance) or \
          (segmentA['spline'] == segmentB['spline'] and \
          (areIntersectionsAdjacent(segmentA, segmentB, solution[0], solution[1]) or \
           areIntersectionsAdjacent(segmentB, segmentA, solution[1], solution[0]))):
            continue
        addCut(solution[0], solution[1])
    return result

def bezierMultiIntersection(segments):
    for index in range(0, len(segments)):
        for otherIndex in range(index+1, len(segments)):
            segmentIntersection(segments[index], segments[otherIndex])
    prepareSegmentIntersections(segments)
    subdivideBezierSegments(segments)

def bezierProjectHandles(segments):
    insertions = []
    index_offset = 0
    for segment in segments:
        if len(insertions) > 0 and insertions[-1][0] != segment['spline']:
            index_offset = 0
        points = bezierSegmentPoints(segment['beginPoint'], segment['endPoint'])
        paramA, paramB, pointA, pointB = nearestPointOfLines(points[0], points[1]-points[0], points[3], points[2]-points[3])
        if pointA and pointB:
            segment['cuts'].append({'param': 0.5})
            insertions.append((segment['spline'], segment['beginIndex']+1+index_offset, (pointA+pointB)*0.5))
            index_offset += 1
    subdivideBezierSegments(segments)
    for insertion in insertions:
        bezier_point = insertion[0].bezier_points[insertion[1]]
        bezier_point.co = insertion[2]
        bezier_point.handle_left_type = 'VECTOR'
        bezier_point.handle_right_type = 'VECTOR'

def bezierSubivideAt(points, params):
    if len(params) == 0:
        return []
    newPoints = []
    newPoints.append(points[0]+(points[1]-points[0])*params[0])
    for index, param in enumerate(params):
        paramLeft = param
        if index > 0:
            paramLeft -= params[index-1]
        paramRight = -param
        if index == len(params)-1:
            paramRight += 1.0
        else:
            paramRight += params[index+1]
        point = bezierPointAt(points, param)
        tangent = bezierTangentAt(points, param)
        newPoints.append(point-tangent*paramLeft)
        newPoints.append(point)
        newPoints.append(point+tangent*paramRight)
    newPoints.append(points[3]-(points[3]-points[2])*(1.0-params[-1]))
    return newPoints

def subdivideBezierSegment(segment):
    # Blender only allows uniform subdivision. Use this method to subdivide at arbitrary params.
    # NOTE: segment['cuts'] must be sorted by param
    if len(segment['cuts']) == 0:
        return

    segment['beginPoint'] = segment['spline'].bezier_points[segment['beginIndex']]
    segment['endPoint'] = segment['spline'].bezier_points[segment['endIndex']]
    params = [cut['param'] for cut in segment['cuts']]
    newPoints = bezierSubivideAt(bezierSegmentPoints(segment['beginPoint'], segment['endPoint']), params)
    bpy.ops.curve.select_all(action='DESELECT')
    segment['beginPoint'] = segment['spline'].bezier_points[segment['beginIndex']]
    segment['beginPoint'].select_right_handle = True
    segment['beginPoint'].handle_left_type = 'FREE'
    segment['beginPoint'].handle_right_type = 'FREE'
    segment['endPoint'] = segment['spline'].bezier_points[segment['endIndex']]
    segment['endPoint'].select_left_handle = True
    segment['endPoint'].handle_left_type = 'FREE'
    segment['endPoint'].handle_right_type = 'FREE'

    bpy.ops.curve.subdivide(number_cuts=len(params))
    if segment['endIndex'] > 0:
        segment['endIndex'] += len(params)
    segment['beginPoint'] = segment['spline'].bezier_points[segment['beginIndex']]
    segment['endPoint'] = segment['spline'].bezier_points[segment['endIndex']]
    segment['beginPoint'].select_right_handle = False
    segment['beginPoint'].handle_right = newPoints[0]
    segment['endPoint'].select_left_handle = False
    segment['endPoint'].handle_left = newPoints[-1]

    for index, cut in enumerate(segment['cuts']):
        cut['index'] = segment['beginIndex']+1+index
        newPoint = segment['spline'].bezier_points[cut['index']]
        newPoint.handle_left_type = 'FREE'
        newPoint.handle_right_type = 'FREE'
        newPoint.select_left_handle = False
        newPoint.select_control_point = False
        newPoint.select_right_handle = False
        newPoint.handle_left = newPoints[index*3+1]
        newPoint.co = newPoints[index*3+2]
        newPoint.handle_right = newPoints[index*3+3]

def prepareSegmentIntersections(segments):
    def areCutsAdjacent(cutA, cutB):
        return cutA['segment']['beginIndex'] == cutB['segment']['endIndex'] and \
               cutA['param'] < param_tolerance and cutB['param'] > 1.0-param_tolerance
    for segment in segments:
        segment['cuts'].sort(key=(lambda cut: cut['param']))
        for index in range(len(segment['cuts'])-1, 0, -1):
            prev = segment['cuts'][index-1]
            current = segment['cuts'][index]
            if abs(prev['param']-current['param']) < param_tolerance and \
               prev['otherCut']['segment']['spline'] == current['otherCut']['segment']['spline'] and \
               (areCutsAdjacent(prev['otherCut'], current['otherCut']) or \
                areCutsAdjacent(current['otherCut'], prev['otherCut'])):
                deleteFromArray(prev['otherCut'], prev['otherCut']['segment']['cuts'])
                deleteFromArray(current['otherCut'], current['otherCut']['segment']['cuts'])
                segment['cuts'].pop(index-1 if current['otherCut']['param'] < param_tolerance else index)
                current = segment['cuts'][index-1]['otherCut']
                current['segment']['extraCut'] = current

def subdivideBezierSegmentsOfSameSpline(segments):
    # NOTE: segment['cuts'] must be sorted by param
    indexOffset = 0
    for segment in segments:
        segment['beginIndex'] += indexOffset
        if segment['endIndex'] > 0:
            segment['endIndex'] += indexOffset
        subdivideBezierSegment(segment)
        indexOffset += len(segment['cuts'])
    for segment in segments:
        segment['beginPoint'] = segment['spline'].bezier_points[segment['beginIndex']]
        segment['endPoint'] = segment['spline'].bezier_points[segment['endIndex']]

def subdivideBezierSegments(segments):
    # NOTE: segment['cuts'] must be sorted by param
    groups = {}
    for segment in segments:
        spline = segment['spline']
        if (spline in groups) == False:
            groups[spline] = []
        group = groups[spline]
        group.append(segment)
    for spline in groups:
        subdivideBezierSegmentsOfSameSpline(groups[spline])

def curveObject():
    obj = bpy.context.object
    return obj if obj != None and obj.type == 'CURVE' and obj.mode == 'EDIT' else None

def bezierSegments(splines, selection_only):
    segments = []
    for spline in splines:
        if spline.type != 'BEZIER':
            continue
        for index, current in enumerate(spline.bezier_points):
            next = spline.bezier_points[(index+1) % len(spline.bezier_points)]
            if next == spline.bezier_points[0] and not spline.use_cyclic_u:
                continue
            if not selection_only or (current.select_right_handle and next.select_left_handle):
                segments.append({
                    'spline': spline,
                    'beginIndex': index,
                    'endIndex': index+1 if index < len(spline.bezier_points)-1 else 0,
                    'beginPoint': current,
                    'endPoint': next,
                    'cuts': []
                })
    return segments

def getSelectedSplines(include_bezier, include_polygon, allow_partial_selection=False):
    result = []
    for spline in bpy.context.object.data.splines:
        selected = not allow_partial_selection
        if spline.type == 'BEZIER':
            if not include_bezier:
                continue
            for index, point in enumerate(spline.bezier_points):
                if point.select_left_handle == allow_partial_selection or \
                   point.select_control_point == allow_partial_selection or \
                   point.select_right_handle == allow_partial_selection:
                    selected = allow_partial_selection
                    break
        elif spline.type == 'POLY':
            if not include_polygon:
                continue
            for index, point in enumerate(spline.points):
                if point.select == allow_partial_selection:
                    selected = allow_partial_selection
                    break
        else:
            continue
        if selected:
            result.append(spline)
    return result

def addObject(type, name):
    if type == 'CURVE':
        data = bpy.data.curves.new(name=name, type='CURVE')
        data.dimensions = '3D'
    elif type == 'MESH':
        data = bpy.data.meshes.new(name=name, type='MESH')
    obj = bpy.data.objects.new(name, data)
    obj.location = bpy.context.scene.cursor.location
    bpy.context.scene.collection.objects.link(obj)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    return obj

def addPolygonSpline(obj, cyclic, vertices, weights=None, select=False):
    spline = obj.data.splines.new(type='POLY')
    spline.use_cyclic_u = cyclic
    spline.points.add(len(vertices)-1)
    for index, point in enumerate(spline.points):
        point.co.xyz = vertices[index]
        point.select = select
        if weights:
            point.weight_softbody = weights[index]
    return spline

def addBezierSpline(obj, cyclic, vertices, weights=None, select=False):
    spline = obj.data.splines.new(type='BEZIER')
    spline.use_cyclic_u = cyclic
    spline.bezier_points.add(len(vertices)-1)
    for index, point in enumerate(spline.bezier_points):
        point.handle_left = vertices[index][0]
        point.co = vertices[index][1]
        point.handle_right = vertices[index][2]
        if weights:
            point.weight_softbody = weights[index]
        point.select_left_handle = select
        point.select_control_point = select
        point.select_right_handle = select
        if isSegmentLinear([vertices[index-1][1], vertices[index-1][2], vertices[index][0], vertices[index][1]]):
            spline.bezier_points[index-1].handle_right_type = 'VECTOR'
            point.handle_left_type = 'VECTOR'
    return spline

def mergeEnds(splines, points, is_last_point):
    bpy.ops.curve.select_all(action='DESELECT')
    points[0].handle_left_type = points[0].handle_right_type = 'FREE'
    new_co = (points[0].co+points[1].co)*0.5
    handle = (points[1].handle_left if is_last_point[1] else points[1].handle_right)+new_co-points[1].co
    points[0].select_left_handle = points[0].select_right_handle = True
    if is_last_point[0]:
        points[0].handle_left += new_co-points[0].co
        points[0].handle_right = handle
    else:
        points[0].handle_right += new_co-points[0].co
        points[0].handle_left = handle
    points[0].co = new_co
    points[0].select_control_point = points[1].select_control_point = True
    bpy.ops.curve.make_segment()
    spline = splines[0] if splines[0] in bpy.context.object.data.splines.values() else splines[1]
    point = next(point for point in spline.bezier_points if point.select_left_handle)
    point.select_left_handle = point.select_right_handle = point.select_control_point = False
    bpy.ops.curve.delete()
    return spline

def polygonArcAt(center, radius, begin_angle, angle, step_angle, include_ends):
    vertices = []
    circle_samples = math.ceil(abs(angle)/step_angle)
    for t in (range(0, circle_samples+1) if include_ends else range(1, circle_samples)):
        t = begin_angle+angle*t/circle_samples
        normal = Vector((math.cos(t), math.sin(t), 0))
        vertices.append(center+normal*radius)
    return vertices

def bezierArcAt(tangent, normal, center, radius, angle, tolerance=0.99999):
    transform = Matrix.Identity(4)
    transform.col[0].xyz = tangent.cross(normal)*radius
    transform.col[1].xyz = tangent*radius
    transform.col[2].xyz = normal*radius
    transform.col[3].xyz = center
    segments = []
    segment_count = math.ceil(abs(angle)/(math.pi*0.5)*tolerance)
    angle /= segment_count
    x0 = math.cos(angle*0.5)
    y0 = math.sin(angle*0.5)
    x1 = (4.0-x0)/3.0
    y1 = (1.0-x0)*(3.0-x0)/(3.0*y0)
    points = [
        Vector((x0, -y0, 0)),
        Vector((x1, -y1, 0)),
        Vector((x1, y1, 0)),
        Vector((x0, y0, 0))
    ]
    for i in range(0, segment_count):
        rotation = Matrix.Rotation((i+0.5)*angle, 4, 'Z')
        segments.append(list(map(lambda v: transform@(rotation@v), points)))
    return segments

def iterateSpline(spline, callback):
    spline_points = spline.bezier_points if spline.type == 'BEZIER' else spline.points
    for index, spline_point in enumerate(spline_points):
        prev = spline_points[index-1]
        current = spline_points[index]
        next = spline_points[(index+1)%len(spline_points)]
        if spline.type == 'BEZIER':
            selected = current.select_control_point
            prev_segment_points = bezierSegmentPoints(prev, current)
            next_segment_points = bezierSegmentPoints(current, next)
            prev_tangent = (prev_segment_points[3]-prev_segment_points[2]).normalized()
            current_tangent = (next_segment_points[1]-next_segment_points[0]).normalized()
            next_tangent = (next_segment_points[3]-next_segment_points[2]).normalized()
        else:
            selected = current.select
            prev_segment_points = [prev.co.xyz, None, None, current.co.xyz]
            next_segment_points = [current.co.xyz, None, None, next.co.xyz]
            prev_tangent = (prev_segment_points[3]-prev_segment_points[0]).normalized()
            current_tangent = next_tangent = (next_segment_points[3]-next_segment_points[0]).normalized()
        normal = prev_tangent.cross(current_tangent).normalized()
        angle = prev_tangent@current_tangent
        angle = 0 if abs(angle-1.0) < 0.0001 else math.acos(angle)
        is_first = (index == 0) and not spline.use_cyclic_u
        is_last = (index == len(spline_points)-1) and not spline.use_cyclic_u
        callback(prev_segment_points, next_segment_points, selected, prev_tangent, current_tangent, next_tangent, normal, angle, is_first, is_last)
    return spline_points

def offsetPolygonOfSpline(spline, offset, step_angle, round_line_join, bezier_samples=128, tolerance=0.000001):
    def offsetVertex(position, tangent):
        normal = Vector((-tangent[1], tangent[0], 0))
        return position+normal*offset
    vertices = []
    def handlePoint(prev_segment_points, next_segment_points, selected, prev_tangent, current_tangent, next_tangent, normal, angle, is_first, is_last):
        sign = math.copysign(1, normal[2])
        angle *= sign
        if is_last:
            return
        is_protruding = (abs(angle) > tolerance and abs(offset) > tolerance)
        if is_protruding and not is_first and sign != math.copysign(1, offset): # Convex Corner
            if round_line_join:
                begin_angle = math.atan2(prev_tangent[1], prev_tangent[0])+math.pi*0.5
                vertices.extend(polygonArcAt(next_segment_points[0], offset, begin_angle, angle, step_angle, False))
            else:
                distance = offset*math.tan(angle*0.5)
                vertices.append(offsetVertex(next_segment_points[0], current_tangent)+current_tangent*distance)
        if is_protruding or is_first:
            vertices.append(offsetVertex(next_segment_points[0], current_tangent))
        if spline.type == 'POLY' or isSegmentLinear(next_segment_points):
            vertices.append(offsetVertex(next_segment_points[3], next_tangent))
        else: # Trace Bezier Segment
            prev_tangent = bezierTangentAt(next_segment_points, 0).normalized()
            for t in range(1, bezier_samples+1):
                t /= bezier_samples
                tangent = bezierTangentAt(next_segment_points, t).normalized()
                if t == 1 or math.acos(min(max(-1, prev_tangent@tangent), 1)) >= step_angle:
                    vertices.append(offsetVertex(bezierPointAt(next_segment_points, t), tangent))
                    prev_tangent = tangent
    spline_points = iterateSpline(spline, handlePoint)

    # Solve Self Intersections
    original_area = areaOfPolygon([point.co for point in spline_points])
    sign = -1 if offset < 0 else 1
    i = (0 if spline.use_cyclic_u else 1)
    while i < len(vertices):
        j = i+2
        while j < len(vertices) - (0 if i > 0 else 1):
            intersection = lineSegmentLineSegmentIntersection(vertices[i-1], vertices[i], vertices[j-1], vertices[j])
            if intersection == None:
                j += 1
                continue
            intersection = (intersection[2]+intersection[3])*0.5
            areaInner = sign*areaOfPolygon([intersection, vertices[i], vertices[j-1]])
            areaOuter = sign*areaOfPolygon([intersection, vertices[j], vertices[i-1]])
            if areaInner > areaOuter:
                vertices = vertices[i:j]+[intersection]
                i = (0 if spline.use_cyclic_u else 1)
            else:
                vertices = vertices[:i]+[intersection]+vertices[j:]
            j = i+2
        i += 1
    new_area = areaOfPolygon(vertices)
    return [vertices] if original_area*new_area >= 0 else []

def filletSpline(spline, radius, chamfer_mode, limit_half_way, tolerance=0.0001):
    vertices = []
    distance_limit_factor = 0.5 if limit_half_way else 1.0
    def handlePoint(prev_segment_points, next_segment_points, selected, prev_tangent, current_tangent, next_tangent, normal, angle, is_first, is_last):
        distance = min((prev_segment_points[0]-prev_segment_points[3]).length*distance_limit_factor, (next_segment_points[0]-next_segment_points[3]).length*distance_limit_factor)
        if not selected or is_first or is_last or angle == 0 or distance == 0 or \
           (spline.type == 'BEZIER' and not (isSegmentLinear(prev_segment_points) and isSegmentLinear(next_segment_points))):
            prev_handle = next_segment_points[0] if is_first else prev_segment_points[2] if spline.type == 'BEZIER' else prev_segment_points[0]
            next_handle = next_segment_points[0] if is_last else next_segment_points[1] if spline.type == 'BEZIER' else next_segment_points[3]
            vertices.append([prev_handle, next_segment_points[0], next_handle])
            return
        tan_factor = math.tan(angle*0.5)
        offset = min(radius, distance/tan_factor)
        distance = offset*tan_factor
        circle_center = next_segment_points[0]+normal.cross(prev_tangent)*offset-prev_tangent*distance
        segments = bezierArcAt(prev_tangent, normal, circle_center, offset, angle)
        if chamfer_mode:
            vertices.append([prev_segment_points[0], segments[0][0], segments[-1][3]])
            vertices.append([segments[0][0], segments[-1][3], next_segment_points[3]])
        else:
            for i in range(0, len(segments)+1):
                vertices.append([
                    segments[i-1][2] if i > 0 else prev_segment_points[0],
                    segments[i][0] if i < len(segments) else segments[i-1][3],
                    segments[i][1] if i < len(segments) else next_segment_points[3]
                ])
    iterateSpline(spline, handlePoint)
    i = 0 if spline.use_cyclic_u else 1
    while(i < len(vertices)):
        if (vertices[i-1][1]-vertices[i][1]).length < tolerance:
            vertices[i-1][2] = vertices[i][2]
            del vertices[i]
        else:
            i = i+1
    return addBezierSpline(bpy.context.object, spline.use_cyclic_u, vertices)

def dogBone(spline, radius):
    vertices = []
    def handlePoint(prev_segment_points, next_segment_points, selected, prev_tangent, current_tangent, next_tangent, normal, angle, is_first, is_last):
        if not selected or is_first or is_last or angle == 0 or normal[2] > 0.0 or \
           (spline.type == 'BEZIER' and not (isSegmentLinear(prev_segment_points) and isSegmentLinear(next_segment_points))):
            prev_handle = next_segment_points[0] if is_first else prev_segment_points[2] if spline.type == 'BEZIER' else prev_segment_points[0]
            next_handle = next_segment_points[0] if is_last else next_segment_points[1] if spline.type == 'BEZIER' else next_segment_points[3]
            vertices.append([prev_handle, next_segment_points[0], next_handle])
            return
        tan_factor = math.tan(angle*0.5)
        corner = next_segment_points[0]+normal.cross(prev_tangent)*radius-prev_tangent*radius*tan_factor
        direction = next_segment_points[0]-corner
        distance = direction.length
        corner = next_segment_points[0]+direction/distance*(distance-radius)
        vertices.append([prev_segment_points[0], next_segment_points[0], corner])
        vertices.append([next_segment_points[0], corner, next_segment_points[0]])
        vertices.append([corner, next_segment_points[0], next_segment_points[3]])
    iterateSpline(spline, handlePoint)
    return vertices

def discretizeCurve(spline, step_angle, samples):
    vertices = []
    def handlePoint(prev_segment_points, next_segment_points, selected, prev_tangent, current_tangent, next_tangent, normal, angle, is_first, is_last):
        if is_last:
            return
        if isSegmentLinear(next_segment_points):
            vertices.append(next_segment_points[3])
        else:
            prev_tangent = bezierTangentAt(next_segment_points, 0).normalized()
            for t in range(1, samples+1):
                t /= samples
                tangent = bezierTangentAt(next_segment_points, t).normalized()
                if t == 1 or math.acos(min(max(-1, prev_tangent@tangent), 1)) >= step_angle:
                    vertices.append(bezierPointAt(next_segment_points, t))
                    prev_tangent = tangent
    iterateSpline(spline, handlePoint)
    return vertices

def bezierBooleanGeometry(splineA, splineB, operation):
    if not splineA.use_cyclic_u or not splineB.use_cyclic_u:
        return False
    segmentsA = bezierSegments([splineA], False)
    segmentsB = bezierSegments([splineB], False)

    deletionFlagA = isPointInSpline(splineA.bezier_points[0].co, splineB)
    deletionFlagB = isPointInSpline(splineB.bezier_points[0].co, splineA)
    if operation == 'DIFFERENCE':
        deletionFlagB = not deletionFlagB
    elif operation == 'INTERSECTION':
        deletionFlagA = not deletionFlagA
        deletionFlagB = not deletionFlagB
    elif operation != 'UNION':
        return False

    intersections = []
    for segmentA in segmentsA:
        for segmentB in segmentsB:
            intersections.extend(segmentIntersection(segmentA, segmentB))
    if len(intersections) == 0:
        if deletionFlagA:
            bpy.context.object.data.splines.remove(splineA)
        if deletionFlagB:
            bpy.context.object.data.splines.remove(splineB)
        return True

    prepareSegmentIntersections(segmentsA)
    prepareSegmentIntersections(segmentsB)
    subdivideBezierSegmentsOfSameSpline(segmentsA)
    subdivideBezierSegmentsOfSameSpline(segmentsB)

    def collectCuts(cuts, segments, deletionFlag):
        for segmentIndex, segment in enumerate(segments):
            if 'extraCut' in segment:
                deletionFlag = not deletionFlag
                segment['extraCut']['index'] = segment['beginIndex']
                segment['extraCut']['deletionFlag'] = deletionFlag
                cuts.append(segment['extraCut'])
            else:
                cuts.append(None)
            cuts.extend(segments[segmentIndex]['cuts'])
            segment['deletionFlag'] = deletionFlag
            for cutIndex, cut in enumerate(segment['cuts']):
                deletionFlag = not deletionFlag
                cut['deletionFlag'] = deletionFlag
    cutsA = []
    cutsB = []
    collectCuts(cutsA, segmentsA, deletionFlagA)
    collectCuts(cutsB, segmentsB, deletionFlagB)

    beginIndex = 0
    for segment in segmentsA:
        if segment['deletionFlag'] == False:
            beginIndex = segment['beginIndex']
            break
        for cut in segment['cuts']:
            if cut['deletionFlag'] == False:
                beginIndex = cut['index']
                break

    cuts = cutsA
    spline = splineA
    index = beginIndex
    backward = False
    vertices = []
    while True:
        current = spline.bezier_points[index]
        vertices.append([current.handle_left, current.co, current.handle_right])
        if backward:
            current.handle_left, current.handle_right = current.handle_right.copy(), current.handle_left.copy()
        index += len(spline.bezier_points)-1 if backward else 1
        index %= len(spline.bezier_points)
        if spline == splineA and index == beginIndex:
            break

        cut = cuts[index]
        if cut != None:
            current = spline.bezier_points[index]
            current_handle = current.handle_right if backward else current.handle_left
            spline = splineA if spline == splineB else splineB
            cuts = cutsA if spline == splineA else cutsB
            index = cut['otherCut']['index']
            backward = cut['otherCut']['deletionFlag']
            next = spline.bezier_points[index]
            if backward:
                next.handle_right = current_handle
            else:
                next.handle_left = current_handle
            if spline == splineA and index == beginIndex:
                break

    spline = addBezierSpline(bpy.context.object, True, vertices)
    bpy.context.object.data.splines.remove(splineA)
    bpy.context.object.data.splines.remove(splineB)
    bpy.context.object.data.splines.active = spline
    return True

def truncateToFitBox(transform, spline, aabb):
    spline_points = spline.points
    aux = {
        'traces': [],
        'vertices': [],
        'weights': []
    }
    def terminateTrace(aux):
        if len(aux['vertices']) > 0:
            aux['traces'].append((aux['vertices'], aux['weights']))
        aux['vertices'] = []
        aux['weights'] = []
    for index, point in enumerate(spline_points):
        begin = transform@point.co.xyz
        end = spline_points[(index+1)%len(spline_points)]
        inside = isPointInAABB(begin, aabb)
        if inside:
            aux['vertices'].append(begin)
            aux['weights'].append(point.weight_softbody)
        if index == len(spline_points)-1 and not spline.use_cyclic_u:
            break
        intersections = lineAABBIntersection(begin, transform@end.co.xyz, aabb)
        if len(intersections) == 2:
            terminateTrace(aux)
            aux['traces'].append((
                [intersections[0][1], intersections[1][1]],
                [end.weight_softbody, end.weight_softbody]
            ))
        elif len(intersections) == 1:
            aux['vertices'].append(intersections[0][1])
            aux['weights'].append(end.weight_softbody)
            if inside:
                terminateTrace(aux)
        elif inside and index == len(spline_points)-1 and spline.use_cyclic_u:
            terminateTrace(aux)
            aux['traces'][0] = (aux['traces'][-1][0]+aux['traces'][0][0], aux['traces'][-1][1]+aux['traces'][0][1])
            aux['traces'].pop()
    terminateTrace(aux)
    return aux['traces']

def arrayModifier(splines, offset, count, connect, serpentine):
    if connect:
        for spline in splines:
            if spline.use_cyclic_u:
                spline.use_cyclic_u = False
                points = spline.points if spline.type == 'POLY' else spline.bezier_points
                points.add(1)
                copyAttributes(points[-1], points[0])
    bpy.ops.curve.select_all(action='DESELECT')
    for spline in splines:
        if spline.type == 'BEZIER':
            for point in spline.bezier_points:
                point.select_left_handle = point.select_control_point = point.select_right_handle = True
        elif spline.type == 'POLY':
            for point in spline.points:
                point.select = True
    splines_at_layer = [splines]
    for i in range(1, count):
        bpy.ops.curve.duplicate()
        bpy.ops.transform.translate(value=offset)
        splines_at_layer.append(getSelectedSplines(True, True))
        if serpentine:
            bpy.ops.curve.switch_direction()
    if connect:
        for i in range(1, count):
            prev_layer = splines_at_layer[i-1]
            next_layer = splines_at_layer[i]
            for j in range(0, len(next_layer)):
                bpy.ops.curve.select_all(action='DESELECT')
                if prev_layer[j].type == 'POLY':
                    prev_layer[j].points[-1].select = True
                else:
                    prev_layer[j].bezier_points[-1].select_control_point = True
                if next_layer[j].type == 'POLY':
                    next_layer[j].points[0].select = True
                else:
                    next_layer[j].bezier_points[0].select_control_point = True
                bpy.ops.curve.make_segment()
    bpy.ops.curve.select_all(action='DESELECT')

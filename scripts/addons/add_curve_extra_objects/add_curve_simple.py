# SPDX-FileCopyrightText: 2017-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

bl_info = {
    "name": "Simple Curve",
    "author": "Vladimir Spivak (cwolf3d)",
    "version": (1, 6, 1),
    "blender": (2, 80, 0),
    "location": "View3D > Add > Curve",
    "description": "Adds Simple Curve",
    "warning": "",
    "doc_url": "{BLENDER_MANUAL_URL}/addons/add_curve/extra_objects.html",
    "category": "Add Curve",
}


# ------------------------------------------------------------

import bpy
from bpy_extras import object_utils
from bpy.types import (
        Operator,
        Menu,
        Panel,
        PropertyGroup,
        )
from bpy.props import (
        BoolProperty,
        EnumProperty,
        FloatProperty,
        FloatVectorProperty,
        IntProperty,
        StringProperty,
        PointerProperty,
        )
from mathutils import (
        Vector,
        Matrix,
        )
from math import (
        sin, asin, sqrt,
        acos, cos, pi,
        radians, tan,
        hypot,
        )
# from bpy_extras.object_utils import *


# ------------------------------------------------------------
# Point:

def SimplePoint():
    newpoints = []

    newpoints.append([0.0, 0.0, 0.0])

    return newpoints


# ------------------------------------------------------------
# Line:

def SimpleLine(c1=[0.0, 0.0, 0.0], c2=[2.0, 2.0, 2.0]):
    newpoints = []

    c3 = Vector(c2) - Vector(c1)
    newpoints.append([0.0, 0.0, 0.0])
    newpoints.append([c3[0], c3[1], c3[2]])

    return newpoints


# ------------------------------------------------------------
# Angle:

def SimpleAngle(length=1.0, angle=45.0):
    newpoints = []

    angle = radians(angle)
    newpoints.append([length, 0.0, 0.0])
    newpoints.append([0.0, 0.0, 0.0])
    newpoints.append([length * cos(angle), length * sin(angle), 0.0])

    return newpoints


# ------------------------------------------------------------
# Distance:

def SimpleDistance(length=1.0, center=True):
    newpoints = []

    if center:
        newpoints.append([-length / 2, 0.0, 0.0])
        newpoints.append([length / 2, 0.0, 0.0])
    else:
        newpoints.append([0.0, 0.0, 0.0])
        newpoints.append([length, 0.0, 0.0])

    return newpoints


# ------------------------------------------------------------
# Circle:

def SimpleCircle(sides=4, radius=1.0):
    newpoints = []

    angle = radians(360) / sides
    newpoints.append([radius, 0, 0])
    if radius != 0 :
        j = 1
        while j < sides:
            t = angle * j
            x = cos(t) * radius
            y = sin(t) * radius
            newpoints.append([x, y, 0])
            j += 1

    return newpoints


# ------------------------------------------------------------
# Ellipse:

def SimpleEllipse(a=2.0, b=1.0):
    newpoints = []

    newpoints.append([a, 0.0, 0.0])
    newpoints.append([0.0, b, 0.0])
    newpoints.append([-a, 0.0, 0.0])
    newpoints.append([0.0, -b, 0.0])

    return newpoints


# ------------------------------------------------------------
# Arc:

def SimpleArc(sides=0, radius=1.0, startangle=0.0, endangle=45.0):
    newpoints = []

    startangle = radians(startangle)
    endangle = radians(endangle)
    sides += 1

    angle = (endangle - startangle) / sides
    x = cos(startangle) * radius
    y = sin(startangle) * radius
    newpoints.append([x, y, 0])
    j = 1
    while j < sides:
        t = angle * j
        x = cos(t + startangle) * radius
        y = sin(t + startangle) * radius
        newpoints.append([x, y, 0])
        j += 1
    x = cos(endangle) * radius
    y = sin(endangle) * radius
    newpoints.append([x, y, 0])

    return newpoints


# ------------------------------------------------------------
# Sector:

def SimpleSector(sides=0, radius=1.0, startangle=0.0, endangle=45.0):
    newpoints = []

    startangle = radians(startangle)
    endangle = radians(endangle)
    sides += 1

    newpoints.append([0, 0, 0])
    angle = (endangle - startangle) / sides
    x = cos(startangle) * radius
    y = sin(startangle) * radius
    newpoints.append([x, y, 0])
    j = 1
    while j < sides:
        t = angle * j
        x = cos(t + startangle) * radius
        y = sin(t + startangle) * radius
        newpoints.append([x, y, 0])
        j += 1
    x = cos(endangle) * radius
    y = sin(endangle) * radius
    newpoints.append([x, y, 0])

    return newpoints


# ------------------------------------------------------------
# Segment:

def SimpleSegment(sides=0, a=2.0, b=1.0, startangle=0.0, endangle=45.0):
    newpoints = []

    startangle = radians(startangle)
    endangle = radians(endangle)
    sides += 1

    angle = (endangle - startangle) / sides
    x = cos(startangle) * a
    y = sin(startangle) * a
    newpoints.append([x, y, 0])
    j = 1
    while j < sides:
        t = angle * j
        x = cos(t + startangle) * a
        y = sin(t + startangle) * a
        newpoints.append([x, y, 0])
        j += 1
    x = cos(endangle) * a
    y = sin(endangle) * a
    newpoints.append([x, y, 0])

    x = cos(endangle) * b
    y = sin(endangle) * b
    newpoints.append([x, y, 0])
    j = sides - 1
    while j > 0:
        t = angle * j
        x = cos(t + startangle) * b
        y = sin(t + startangle) * b
        newpoints.append([x, y, 0])
        j -= 1
    x = cos(startangle) * b
    y = sin(startangle) * b
    newpoints.append([x, y, 0])

    return newpoints


# ------------------------------------------------------------
# Rectangle:

def SimpleRectangle(width=2.0, length=2.0, rounded=0.0, center=True):
    newpoints = []

    r = rounded / 2

    if center:
        x = width / 2
        y = length / 2
        if rounded != 0.0:
            newpoints.append([-x + r, y, 0.0])
            newpoints.append([x - r, y, 0.0])
            newpoints.append([x, y - r, 0.0])
            newpoints.append([x, -y + r, 0.0])
            newpoints.append([x - r, -y, 0.0])
            newpoints.append([-x + r, -y, 0.0])
            newpoints.append([-x, -y + r, 0.0])
            newpoints.append([-x, y - r, 0.0])
        else:
            newpoints.append([-x, y, 0.0])
            newpoints.append([x, y, 0.0])
            newpoints.append([x, -y, 0.0])
            newpoints.append([-x, -y, 0.0])

    else:
        x = width
        y = length
        if rounded != 0.0:
            newpoints.append([r, y, 0.0])
            newpoints.append([x - r, y, 0.0])
            newpoints.append([x, y - r, 0.0])
            newpoints.append([x, r, 0.0])
            newpoints.append([x - r, 0.0, 0.0])
            newpoints.append([r, 0.0, 0.0])
            newpoints.append([0.0, r, 0.0])
            newpoints.append([0.0, y - r, 0.0])
        else:
            newpoints.append([0.0, 0.0, 0.0])
            newpoints.append([0.0, y, 0.0])
            newpoints.append([x, y, 0.0])
            newpoints.append([x, 0.0, 0.0])

    return newpoints


# ------------------------------------------------------------
# Rhomb:

def SimpleRhomb(width=2.0, length=2.0, center=True):
    newpoints = []
    x = width / 2
    y = length / 2

    if center:
        newpoints.append([-x, 0.0, 0.0])
        newpoints.append([0.0, y, 0.0])
        newpoints.append([x, 0.0, 0.0])
        newpoints.append([0.0, -y, 0.0])
    else:
        newpoints.append([x, 0.0, 0.0])
        newpoints.append([0.0, y, 0.0])
        newpoints.append([x, length, 0.0])
        newpoints.append([width, y, 0.0])

    return newpoints


# ------------------------------------------------------------
# Polygon:

def SimplePolygon(sides=3, radius=1.0):
    newpoints = []
    angle = radians(360.0) / sides
    j = 0

    while j < sides:
        t = angle * j
        x = sin(t) * radius
        y = cos(t) * radius
        newpoints.append([x, y, 0.0])
        j += 1

    return newpoints


# ------------------------------------------------------------
# Polygon_ab:

def SimplePolygon_ab(sides=3, a=2.0, b=1.0):
    newpoints = []
    angle = radians(360.0) / sides
    j = 0

    while j < sides:
        t = angle * j
        x = sin(t) * a
        y = cos(t) * b
        newpoints.append([x, y, 0.0])
        j += 1

    return newpoints


# ------------------------------------------------------------
# Trapezoid:

def SimpleTrapezoid(a=2.0, b=1.0, h=1.0, center=True):
    newpoints = []
    x = a / 2
    y = b / 2
    r = h / 2

    if center:
        newpoints.append([-x, -r, 0.0])
        newpoints.append([-y, r, 0.0])
        newpoints.append([y, r, 0.0])
        newpoints.append([x, -r, 0.0])

    else:
        newpoints.append([0.0, 0.0, 0.0])
        newpoints.append([x - y, h, 0.0])
        newpoints.append([x + y, h, 0.0])
        newpoints.append([a, 0.0, 0.0])

    return newpoints


# ------------------------------------------------------------
# get array of vertcoordinates according to splinetype
def vertsToPoints(Verts, splineType):

    # main vars
    vertArray = []

    # array for BEZIER spline output (V3)
    if splineType == 'BEZIER':
        for v in Verts:
            vertArray += v

    # array for nonBEZIER output (V4)
    else:
        for v in Verts:
            vertArray += v
            if splineType == 'NURBS':
                # for nurbs w=1
                vertArray.append(1)
            else:
                # for poly w=0
                vertArray.append(0)
    return vertArray


# ------------------------------------------------------------
# Main Function

def main(context, self, use_enter_edit_mode):
    # output splineType 'POLY' 'NURBS' 'BEZIER'
    splineType = self.outputType

    sides = abs(int((self.Simple_endangle - self.Simple_startangle) / 90))

    # get verts
    if self.Simple_Type == 'Point':
        verts = SimplePoint()

    if self.Simple_Type == 'Line':
        verts = SimpleLine(self.location, self.Simple_endlocation)

    if self.Simple_Type == 'Distance':
        verts = SimpleDistance(self.Simple_length, self.Simple_center)

    if self.Simple_Type == 'Angle':
        verts = SimpleAngle(self.Simple_length, self.Simple_angle)

    if self.Simple_Type == 'Circle':
        if self.Simple_sides < 4:
            self.Simple_sides = 4
        if self.Simple_radius == 0:
            return {'FINISHED'}
        verts = SimpleCircle(self.Simple_sides, self.Simple_radius)

    if self.Simple_Type == 'Ellipse':
        verts = SimpleEllipse(self.Simple_a, self.Simple_b)

    if self.Simple_Type == 'Arc':
        if self.Simple_sides < sides:
            self.Simple_sides = sides
        if self.Simple_radius == 0:
            return {'FINISHED'}
        verts = SimpleArc(
                    self.Simple_sides, self.Simple_radius,
                    self.Simple_startangle, self.Simple_endangle
                    )

    if self.Simple_Type == 'Sector':
        if self.Simple_sides < sides:
            self.Simple_sides = sides
        if self.Simple_radius == 0:
            return {'FINISHED'}
        verts = SimpleSector(
                    self.Simple_sides, self.Simple_radius,
                    self.Simple_startangle, self.Simple_endangle
                    )

    if self.Simple_Type == 'Segment':
        if self.Simple_sides < sides:
            self.Simple_sides = sides
        if self.Simple_a == 0 or self.Simple_b == 0 or self.Simple_a == self.Simple_b:
            return {'FINISHED'}
        if self.Simple_a > self.Simple_b:
            verts = SimpleSegment(
                    self.Simple_sides, self.Simple_a, self.Simple_b,
                    self.Simple_startangle, self.Simple_endangle
                    )
        if self.Simple_a < self.Simple_b:
            verts = SimpleSegment(
                    self.Simple_sides, self.Simple_b, self.Simple_a,
                    self.Simple_startangle, self.Simple_endangle
                    )

    if self.Simple_Type == 'Rectangle':
        verts = SimpleRectangle(
                    self.Simple_width, self.Simple_length,
                    self.Simple_rounded, self.Simple_center
                    )

    if self.Simple_Type == 'Rhomb':
        verts = SimpleRhomb(
                    self.Simple_width, self.Simple_length, self.Simple_center
                    )

    if self.Simple_Type == 'Polygon':
        if self.Simple_sides < 3:
            self.Simple_sides = 3
        verts = SimplePolygon(
                    self.Simple_sides, self.Simple_radius
                    )

    if self.Simple_Type == 'Polygon_ab':
        if self.Simple_sides < 3:
            self.Simple_sides = 3
        verts = SimplePolygon_ab(
                    self.Simple_sides, self.Simple_a, self.Simple_b
                    )

    if self.Simple_Type == 'Trapezoid':
        verts = SimpleTrapezoid(
                    self.Simple_a, self.Simple_b, self.Simple_h, self.Simple_center
                    )

    # turn verts into array
    vertArray = vertsToPoints(verts, splineType)

    # create object
    if bpy.context.mode == 'EDIT_CURVE':

        Curve = context.active_object
        newSpline = Curve.data.splines.new(type=splineType)          # spline
    else:
        name = self.Simple_Type  # Type as name

        dataCurve = bpy.data.curves.new(name, type='CURVE')  # curve data block
        newSpline = dataCurve.splines.new(type=splineType)          # spline

        # create object with new Curve
        Curve = object_utils.object_data_add(context, dataCurve, operator=self)  # place in active scene
        Curve.select_set(True)

    for spline in Curve.data.splines:
        if spline.type == 'BEZIER':
            for point in spline.bezier_points:
                point.select_control_point = False
                point.select_left_handle = False
                point.select_right_handle = False
        else:
            for point in spline.points:
                point.select = False

    # create spline from vertarray
    all_points = []
    if splineType == 'BEZIER':
        newSpline.bezier_points.add(int(len(vertArray) * 0.33))
        newSpline.bezier_points.foreach_set('co', vertArray)
        for point in newSpline.bezier_points:
            point.handle_right_type = self.handleType
            point.handle_left_type = self.handleType
            point.select_control_point = True
            point.select_left_handle = True
            point.select_right_handle = True
            all_points.append(point)
    else:
        newSpline.points.add(int(len(vertArray) * 0.25 - 1))
        newSpline.points.foreach_set('co', vertArray)
        newSpline.use_endpoint_u = True
        for point in newSpline.points:
            all_points.append(point)
            point.select = True

    n = len(all_points)

    d = 2 * 0.27606262

    if splineType == 'BEZIER':
        if self.Simple_Type == 'Circle' or self.Simple_Type == 'Arc' or \
           self.Simple_Type == 'Sector' or self.Simple_Type == 'Segment' or \
           self.Simple_Type == 'Ellipse':

            for p in all_points:
                p.handle_right_type = 'FREE'
                p.handle_left_type = 'FREE'

        if self.Simple_Type == 'Circle':
            i = 0
            for p1 in all_points:
                if i != (n - 1):
                    p2 = all_points[i + 1]
                    u1 = asin(p1.co.y / self.Simple_radius)
                    u2 = asin(p2.co.y / self.Simple_radius)
                    if p1.co.x > 0 and p2.co.x < 0:
                        u1 = acos(p1.co.x / self.Simple_radius)
                        u2 = acos(p2.co.x / self.Simple_radius)
                    elif p1.co.x < 0 and p2.co.x > 0:
                        u1 = acos(p1.co.x / self.Simple_radius)
                        u2 = acos(p2.co.x / self.Simple_radius)
                    u = u2 - u1
                    if u < 0:
                        u = -u
                    l = 4 / 3 * tan(1 / 4 * u) * self.Simple_radius
                    v1 = Vector((-p1.co.y, p1.co.x, 0))
                    v1.normalize()
                    v2 = Vector((-p2.co.y, p2.co.x, 0))
                    v2.normalize()
                    vh1 = v1 * l
                    vh2 = v2 * l
                    v1 = Vector((p1.co.x, p1.co.y, 0)) + vh1
                    v2 = Vector((p2.co.x, p2.co.y, 0)) - vh2
                    p1.handle_right = v1
                    p2.handle_left = v2
                if i == (n - 1):
                    p2 = all_points[0]
                    u1 = asin(p1.co.y / self.Simple_radius)
                    u2 = asin(p2.co.y / self.Simple_radius)
                    if p1.co.x > 0 and p2.co.x < 0:
                        u1 = acos(p1.co.x / self.Simple_radius)
                        u2 = acos(p2.co.x / self.Simple_radius)
                    elif p1.co.x < 0 and p2.co.x > 0:
                        u1 = acos(p1.co.x / self.Simple_radius)
                        u2 = acos(p2.co.x / self.Simple_radius)
                    u = u2 - u1
                    if u < 0:
                        u = -u
                    l = 4 / 3 * tan(1 / 4 * u) * self.Simple_radius
                    v1 = Vector((-p1.co.y, p1.co.x, 0))
                    v1.normalize()
                    v2 = Vector((-p2.co.y, p2.co.x, 0))
                    v2.normalize()
                    vh1 = v1 * l
                    vh2 = v2 * l
                    v1 = Vector((p1.co.x, p1.co.y, 0)) + vh1
                    v2 = Vector((p2.co.x, p2.co.y, 0)) - vh2
                    p1.handle_right = v1
                    p2.handle_left = v2
                i += 1

        if self.Simple_Type == 'Ellipse':
            all_points[0].handle_right = Vector((self.Simple_a, self.Simple_b * d, 0))
            all_points[0].handle_left = Vector((self.Simple_a, -self.Simple_b * d, 0))
            all_points[1].handle_right = Vector((-self.Simple_a * d, self.Simple_b, 0))
            all_points[1].handle_left = Vector((self.Simple_a * d, self.Simple_b, 0))
            all_points[2].handle_right = Vector((-self.Simple_a, -self.Simple_b * d, 0))
            all_points[2].handle_left = Vector((-self.Simple_a, self.Simple_b * d, 0))
            all_points[3].handle_right = Vector((self.Simple_a * d, -self.Simple_b, 0))
            all_points[3].handle_left = Vector((-self.Simple_a * d, -self.Simple_b, 0))

        if self.Simple_Type == 'Arc':
            i = 0
            for p1 in all_points:
                if i != (n - 1):
                    p2 = all_points[i + 1]
                    u1 = asin(p1.co.y / self.Simple_radius)
                    u2 = asin(p2.co.y / self.Simple_radius)
                    if p1.co.x > 0 and p2.co.x < 0:
                        u1 = acos(p1.co.x / self.Simple_radius)
                        u2 = acos(p2.co.x / self.Simple_radius)
                    elif p1.co.x < 0 and p2.co.x > 0:
                        u1 = acos(p1.co.x / self.Simple_radius)
                        u2 = acos(p2.co.x / self.Simple_radius)
                    u = u2 - u1
                    if u < 0:
                        u = -u
                    l = 4 / 3 * tan(1 / 4 * u) * self.Simple_radius
                    v1 = Vector((-p1.co.y, p1.co.x, 0))
                    v1.normalize()
                    v2 = Vector((-p2.co.y, p2.co.x, 0))
                    v2.normalize()
                    vh1 = v1 * l
                    vh2 = v2 * l
                    if self.Simple_startangle < self.Simple_endangle:
                        v1 = Vector((p1.co.x, p1.co.y, 0)) + vh1
                        v2 = Vector((p2.co.x, p2.co.y, 0)) - vh2
                        p1.handle_right = v1
                        p2.handle_left = v2
                    else:
                        v1 = Vector((p1.co.x, p1.co.y, 0)) - vh1
                        v2 = Vector((p2.co.x, p2.co.y, 0)) + vh2
                        p1.handle_right = v1
                        p2.handle_left = v2
                i += 1
            all_points[0].handle_left_type = 'VECTOR'
            all_points[-1].handle_right_type = 'VECTOR'

        if self.Simple_Type == 'Sector':
            i = 0
            for p1 in all_points:
                if i == 0:
                    p1.handle_right_type = 'VECTOR'
                    p1.handle_left_type = 'VECTOR'
                elif i != (n - 1):
                    p2 = all_points[i + 1]
                    u1 = asin(p1.co.y / self.Simple_radius)
                    u2 = asin(p2.co.y / self.Simple_radius)
                    if p1.co.x > 0 and p2.co.x < 0:
                        u1 = acos(p1.co.x / self.Simple_radius)
                        u2 = acos(p2.co.x / self.Simple_radius)
                    elif p1.co.x < 0 and p2.co.x > 0:
                        u1 = acos(p1.co.x / self.Simple_radius)
                        u2 = acos(p2.co.x / self.Simple_radius)
                    u = u2 - u1
                    if u < 0:
                        u = -u
                    l = 4 / 3 * tan(1 / 4 * u) * self.Simple_radius
                    v1 = Vector((-p1.co.y, p1.co.x, 0))
                    v1.normalize()
                    v2 = Vector((-p2.co.y, p2.co.x, 0))
                    v2.normalize()
                    vh1 = v1 * l
                    vh2 = v2 * l
                    if self.Simple_startangle < self.Simple_endangle:
                        v1 = Vector((p1.co.x, p1.co.y, 0)) + vh1
                        v2 = Vector((p2.co.x, p2.co.y, 0)) - vh2
                        p1.handle_right = v1
                        p2.handle_left = v2
                    else:
                        v1 = Vector((p1.co.x, p1.co.y, 0)) - vh1
                        v2 = Vector((p2.co.x, p2.co.y, 0)) + vh2
                        p1.handle_right = v1
                        p2.handle_left = v2
                i += 1
            all_points[0].handle_left_type = 'VECTOR'
            all_points[0].handle_right_type = 'VECTOR'
            all_points[1].handle_left_type = 'VECTOR'
            all_points[-1].handle_right_type = 'VECTOR'

        if self.Simple_Type == 'Segment':
            i = 0
            if self.Simple_a > self.Simple_b:
                Segment_a = self.Simple_a
                Segment_b = self.Simple_b
            if self.Simple_a < self.Simple_b:
                Segment_b = self.Simple_a
                Segment_a = self.Simple_b
            for p1 in all_points:
                if i < (n / 2 - 1):
                    p2 = all_points[i + 1]
                    u1 = asin(p1.co.y / Segment_a)
                    u2 = asin(p2.co.y / Segment_a)
                    if p1.co.x > 0 and p2.co.x < 0:
                        u1 = acos(p1.co.x / Segment_a)
                        u2 = acos(p2.co.x / Segment_a)
                    elif p1.co.x < 0 and p2.co.x > 0:
                        u1 = acos(p1.co.x / Segment_a)
                        u2 = acos(p2.co.x / Segment_a)
                    u = u2 - u1
                    if u < 0:
                        u = -u
                    l = 4 / 3 * tan(1 / 4 * u) * Segment_a
                    v1 = Vector((-p1.co.y, p1.co.x, 0))
                    v1.normalize()
                    v2 = Vector((-p2.co.y, p2.co.x, 0))
                    v2.normalize()
                    vh1 = v1 * l
                    vh2 = v2 * l
                    if self.Simple_startangle < self.Simple_endangle:
                        v1 = Vector((p1.co.x, p1.co.y, 0)) + vh1
                        v2 = Vector((p2.co.x, p2.co.y, 0)) - vh2
                        p1.handle_right = v1
                        p2.handle_left = v2
                    else:
                        v1 = Vector((p1.co.x, p1.co.y, 0)) - vh1
                        v2 = Vector((p2.co.x, p2.co.y, 0)) + vh2
                        p1.handle_right = v1
                        p2.handle_left = v2
                elif i != (n / 2 - 1) and i != (n - 1):
                    p2 = all_points[i + 1]
                    u1 = asin(p1.co.y / Segment_b)
                    u2 = asin(p2.co.y / Segment_b)
                    if p1.co.x > 0 and p2.co.x < 0:
                        u1 = acos(p1.co.x / Segment_b)
                        u2 = acos(p2.co.x / Segment_b)
                    elif p1.co.x < 0 and p2.co.x > 0:
                        u1 = acos(p1.co.x / Segment_b)
                        u2 = acos(p2.co.x / Segment_b)
                    u = u2 - u1
                    if u < 0:
                        u = -u
                    l = 4 / 3 * tan(1 / 4 * u) * Segment_b
                    v1 = Vector((-p1.co.y, p1.co.x, 0))
                    v1.normalize()
                    v2 = Vector((-p2.co.y, p2.co.x, 0))
                    v2.normalize()
                    vh1 = v1 * l
                    vh2 = v2 * l
                    if self.Simple_startangle < self.Simple_endangle:
                        v1 = Vector((p1.co.x, p1.co.y, 0)) - vh1
                        v2 = Vector((p2.co.x, p2.co.y, 0)) + vh2
                        p1.handle_right = v1
                        p2.handle_left = v2
                    else:
                        v1 = Vector((p1.co.x, p1.co.y, 0)) + vh1
                        v2 = Vector((p2.co.x, p2.co.y, 0)) - vh2
                        p1.handle_right = v1
                        p2.handle_left = v2

                i += 1
            all_points[0].handle_left_type = 'VECTOR'
            all_points[n - 1].handle_right_type = 'VECTOR'
            all_points[int(n / 2) - 1].handle_right_type = 'VECTOR'
            all_points[int(n / 2)].handle_left_type = 'VECTOR'

    # set newSpline Options
    newSpline.use_cyclic_u = self.use_cyclic_u
    newSpline.use_endpoint_u = self.endp_u
    newSpline.order_u = self.order_u

    # set curve Options
    Curve.data.dimensions = self.shape
    Curve.data.use_path = True
    if self.shape == '3D':
        Curve.data.fill_mode = 'FULL'
    else:
        Curve.data.fill_mode = 'BOTH'

    # move and rotate spline in edit mode
    if bpy.context.mode == 'EDIT_CURVE':
        if self.align == "WORLD":
            location = self.location - context.active_object.location
            bpy.ops.transform.translate(value = location, orient_type='GLOBAL')
            bpy.ops.transform.rotate(value = self.rotation[0], orient_axis = 'X', orient_type='GLOBAL')
            bpy.ops.transform.rotate(value = self.rotation[1], orient_axis = 'Y', orient_type='GLOBAL')
            bpy.ops.transform.rotate(value = self.rotation[2], orient_axis = 'Z', orient_type='GLOBAL')

        elif self.align == "VIEW":
            bpy.ops.transform.translate(value = self.location)
            bpy.ops.transform.rotate(value = self.rotation[0], orient_axis = 'X')
            bpy.ops.transform.rotate(value = self.rotation[1], orient_axis = 'Y')
            bpy.ops.transform.rotate(value = self.rotation[2], orient_axis = 'Z')

        elif self.align == "CURSOR":
            location = context.active_object.location
            self.location = bpy.context.scene.cursor.location - location
            self.rotation = bpy.context.scene.cursor.rotation_euler

            bpy.ops.transform.translate(value = self.location)
            bpy.ops.transform.rotate(value = self.rotation[0], orient_axis = 'X')
            bpy.ops.transform.rotate(value = self.rotation[1], orient_axis = 'Y')
            bpy.ops.transform.rotate(value = self.rotation[2], orient_axis = 'Z')


def menu(self, context):
    oper1 = self.layout.operator(Simple.bl_idname, text="Angle", icon="DRIVER_ROTATIONAL_DIFFERENCE")
    oper1.Simple_Type = "Angle"
    oper1.use_cyclic_u = False

    oper2 = self.layout.operator(Simple.bl_idname, text="Arc", icon="MOD_THICKNESS")
    oper2.Simple_Type = "Arc"
    oper2.use_cyclic_u = False

    oper3 = self.layout.operator(Simple.bl_idname, text="Circle", icon="ANTIALIASED")
    oper3.Simple_Type = "Circle"
    oper3.use_cyclic_u = True

    oper4 = self.layout.operator(Simple.bl_idname, text="Distance", icon="DRIVER_DISTANCE")
    oper4.Simple_Type = "Distance"
    oper4.use_cyclic_u = False

    oper5 = self.layout.operator(Simple.bl_idname, text="Ellipse", icon="MESH_TORUS")
    oper5.Simple_Type = "Ellipse"
    oper5.use_cyclic_u = True

    oper6 = self.layout.operator(Simple.bl_idname, text="Line", icon="MOD_SIMPLIFY")
    oper6.Simple_Type = "Line"
    oper6.use_cyclic_u = False
    oper6.shape = '3D'

    oper7 = self.layout.operator(Simple.bl_idname, text="Point", icon="LAYER_ACTIVE")
    oper7.Simple_Type = "Point"
    oper7.use_cyclic_u = False

    oper8 = self.layout.operator(Simple.bl_idname, text="Polygon", icon="SEQ_CHROMA_SCOPE")
    oper8.Simple_Type = "Polygon"
    oper8.use_cyclic_u = True

    oper9 = self.layout.operator(Simple.bl_idname, text="Polygon ab", icon="SEQ_CHROMA_SCOPE")
    oper9.Simple_Type = "Polygon_ab"
    oper9.use_cyclic_u = True

    oper10 = self.layout.operator(Simple.bl_idname, text="Rectangle", icon="MESH_PLANE")
    oper10.Simple_Type = "Rectangle"
    oper10.use_cyclic_u = True

    oper11 = self.layout.operator(Simple.bl_idname, text="Rhomb", icon="DECORATE_ANIMATE")
    oper11.Simple_Type = "Rhomb"
    oper11.use_cyclic_u = True

    oper12 = self.layout.operator(Simple.bl_idname, text="Sector", icon="CON_SHRINKWRAP")
    oper12.Simple_Type = "Sector"
    oper12.use_cyclic_u = True

    oper13 = self.layout.operator(Simple.bl_idname, text="Segment", icon="MOD_SIMPLEDEFORM")
    oper13.Simple_Type = "Segment"
    oper13.use_cyclic_u = True

    oper14 = self.layout.operator(Simple.bl_idname, text="Trapezoid", icon="MOD_EDGESPLIT")
    oper14.Simple_Type = "Trapezoid"
    oper14.use_cyclic_u = True

# ------------------------------------------------------------
# Simple operator

class Simple(Operator, object_utils.AddObjectHelper):
    bl_idname = "curve.simple"
    bl_label = "Simple Curve"
    bl_description = "Construct a Simple Curve"
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}

    # change properties
    Simple : BoolProperty(
            name="Simple",
            default=True,
            description="Simple Curve"
            )
    Simple_Change : BoolProperty(
            name="Change",
            default=False,
            description="Change Simple Curve"
            )
    Simple_Delete : StringProperty(
            name="Delete",
            description="Delete Simple Curve"
            )
    # general properties
    Types = [('Point', "Point", "Construct a Point"),
             ('Line', "Line", "Construct a Line"),
             ('Distance', "Distance", "Construct a two point Distance"),
             ('Angle', "Angle", "Construct an Angle"),
             ('Circle', "Circle", "Construct a Circle"),
             ('Ellipse', "Ellipse", "Construct an Ellipse"),
             ('Arc', "Arc", "Construct an Arc"),
             ('Sector', "Sector", "Construct a Sector"),
             ('Segment', "Segment", "Construct a Segment"),
             ('Rectangle', "Rectangle", "Construct a Rectangle"),
             ('Rhomb', "Rhomb", "Construct a Rhomb"),
             ('Polygon', "Polygon", "Construct a Polygon"),
             ('Polygon_ab', "Polygon ab", "Construct a Polygon ab"),
             ('Trapezoid', "Trapezoid", "Construct a Trapezoid")
            ]
    Simple_Type : EnumProperty(
            name="Type",
            description="Form of Curve to create",
            items=Types
            )
    # Line properties
    Simple_endlocation : FloatVectorProperty(
            name="",
            description="End location",
            default=(2.0, 2.0, 2.0),
            subtype='TRANSLATION'
            )
    # Trapezoid properties
    Simple_a : FloatProperty(
            name="Side a",
            default=2.0,
            min=0.0, soft_min=0.0,
            unit='LENGTH',
            description="a side Value"
            )
    Simple_b : FloatProperty(
            name="Side b",
            default=1.0,
            min=0.0, soft_min=0.0,
            unit='LENGTH',
            description="b side Value"
            )
    Simple_h : FloatProperty(
            name="Height",
            default=1.0,
            unit='LENGTH',
            description="Height of the Trapezoid - distance between a and b"
            )
    Simple_angle : FloatProperty(
            name="Angle",
            default=45.0,
            description="Angle"
            )
    Simple_startangle : FloatProperty(
            name="Start angle",
            default=0.0,
            min=-360.0, soft_min=-360.0,
            max=360.0, soft_max=360.0,
            description="Start angle"
            )
    Simple_endangle : FloatProperty(
            name="End angle",
            default=45.0,
            min=-360.0, soft_min=-360.0,
            max=360.0, soft_max=360.0,
            description="End angle"
            )
    Simple_sides : IntProperty(
            name="Sides",
            default=3,
            min=0, soft_min=0,
            description="Sides"
            )
    Simple_radius : FloatProperty(
            name="Radius",
            default=1.0,
            min=0.0, soft_min=0.0,
            unit='LENGTH',
            description="Radius"
            )
    Simple_center : BoolProperty(
            name="Length center",
            default=True,
            description="Length center"
            )

    Angle_types = [('Degrees', "Degrees", "Use Degrees"),
                   ('Radians', "Radians", "Use Radians")]
    Simple_degrees_or_radians : EnumProperty(
            name="Degrees or radians",
            description="Degrees or radians",
            items=Angle_types
            )
    # Rectangle properties
    Simple_width : FloatProperty(
            name="Width",
            default=2.0,
            min=0.0, soft_min=0,
            unit='LENGTH',
            description="Width"
            )
    Simple_length : FloatProperty(
            name="Length",
            default=2.0,
            min=0.0, soft_min=0.0,
            unit='LENGTH',
            description="Length"
            )
    Simple_rounded : FloatProperty(
            name="Rounded",
            default=0.0,
            min=0.0, soft_min=0.0,
            unit='LENGTH',
            description="Rounded corners"
            )
    # Curve Options
    shapeItems = [
        ('2D', "2D", "2D shape Curve"),
        ('3D', "3D", "3D shape Curve")]
    shape : EnumProperty(
            name="2D / 3D",
            items=shapeItems,
            description="2D or 3D Curve"
            )
    outputType : EnumProperty(
            name="Output splines",
            description="Type of splines to output",
            items=[
            ('POLY', "Poly", "Poly Spline type"),
            ('NURBS', "Nurbs", "Nurbs Spline type"),
            ('BEZIER', "Bezier", "Bezier Spline type")],
            default='BEZIER'
            )
    use_cyclic_u : BoolProperty(
            name="Cyclic",
            default=True,
            description="make curve closed"
            )
    endp_u : BoolProperty(
            name="Use endpoint u",
            default=True,
            description="stretch to endpoints"
            )
    order_u : IntProperty(
            name="Order u",
            default=4,
            min=2, soft_min=2,
            max=6, soft_max=6,
            description="Order of nurbs spline"
            )
    handleType : EnumProperty(
            name="Handle type",
            default='VECTOR',
            description="Bezier handles type",
            items=[
            ('VECTOR', "Vector", "Vector type Bezier handles"),
            ('AUTO', "Auto", "Automatic type Bezier handles")]
            )
    edit_mode : BoolProperty(
            name="Show in edit mode",
            default=True,
            description="Show in edit mode"
            )

    def draw(self, context):
        layout = self.layout

        # general options
        col = layout.column()
        col.prop(self, "Simple_Type")

        l = 0
        s = 0

        if self.Simple_Type == 'Line':
            box = layout.box()
            col = box.column(align=True)
            col.label(text=self.Simple_Type + " Options:")
            col.prop(self, "Simple_endlocation")
            v = Vector(self.Simple_endlocation) - Vector(self.location)
            l = v.length

        if self.Simple_Type == 'Distance':
            box = layout.box()
            col = box.column(align=True)
            col.label(text=self.Simple_Type + " Options:")
            col.prop(self, "Simple_length")
            col.prop(self, "Simple_center")
            l = self.Simple_length

        if self.Simple_Type == 'Angle':
            box = layout.box()
            col = box.column(align=True)
            col.label(text=self.Simple_Type + " Options:")
            col.prop(self, "Simple_length")
            col.prop(self, "Simple_angle")

        if self.Simple_Type == 'Circle':
            box = layout.box()
            col = box.column(align=True)
            col.label(text=self.Simple_Type + " Options:")
            col.prop(self, "Simple_sides")
            col.prop(self, "Simple_radius")

            l = 2 * pi * abs(self.Simple_radius)
            s = pi * self.Simple_radius * self.Simple_radius

        if self.Simple_Type == 'Ellipse':
            box = layout.box()
            col = box.column(align=True)
            col.label(text=self.Simple_Type + " Options:")
            col.prop(self, "Simple_a", text="Radius a")
            col.prop(self, "Simple_b", text="Radius b")

            l = pi * (3 * (self.Simple_a + self.Simple_b) -
                          sqrt((3 * self.Simple_a + self.Simple_b) *
                          (self.Simple_a + 3 * self.Simple_b)))

            s = pi * abs(self.Simple_b) * abs(self.Simple_a)

        if self.Simple_Type == 'Arc':
            box = layout.box()
            col = box.column(align=True)
            col.label(text=self.Simple_Type + " Options:")
            col.prop(self, "Simple_sides")
            col.prop(self, "Simple_radius")

            col = box.column(align=True)
            col.prop(self, "Simple_startangle")
            col.prop(self, "Simple_endangle")
            #row = layout.row()
            #row.prop(self, "Simple_degrees_or_radians", expand=True)

            l = abs(pi * self.Simple_radius * (self.Simple_endangle - self.Simple_startangle) / 180)

        if self.Simple_Type == 'Sector':
            box = layout.box()
            col = box.column(align=True)
            col.label(text=self.Simple_Type + " Options:")
            col.prop(self, "Simple_sides")
            col.prop(self, "Simple_radius")

            col = box.column(align=True)
            col.prop(self, "Simple_startangle")
            col.prop(self, "Simple_endangle")
            #row = layout.row()
            #row.prop(self, "Simple_degrees_or_radians", expand=True)

            l = abs(pi * self.Simple_radius *
                   (self.Simple_endangle - self.Simple_startangle) / 180) + self.Simple_radius * 2

            s = pi * self.Simple_radius * self.Simple_radius * \
                abs(self.Simple_endangle - self.Simple_startangle) / 360

        if self.Simple_Type == 'Segment':
            box = layout.box()
            col = box.column(align=True)
            col.label(text=self.Simple_Type + " Options:")
            col.prop(self, "Simple_sides")
            col.prop(self, "Simple_a", text="Radius a")
            col.prop(self, "Simple_b", text="Radius b")

            col = box.column(align=True)
            col.prop(self, "Simple_startangle")
            col.prop(self, "Simple_endangle")

            #row = layout.row()
            #row.prop(self, "Simple_degrees_or_radians", expand=True)

            la = abs(pi * self.Simple_a * (self.Simple_endangle - self.Simple_startangle) / 180)
            lb = abs(pi * self.Simple_b * (self.Simple_endangle - self.Simple_startangle) / 180)
            l = abs(self.Simple_a - self.Simple_b) * 2 + la + lb

            sa = pi * self.Simple_a * self.Simple_a * \
                abs(self.Simple_endangle - self.Simple_startangle) / 360

            sb = pi * self.Simple_b * self.Simple_b * \
                abs(self.Simple_endangle - self.Simple_startangle) / 360

            s = abs(sa - sb)

        if self.Simple_Type == 'Rectangle':
            box = layout.box()
            col = box.column(align=True)
            col.label(text=self.Simple_Type + " Options:")
            col.prop(self, "Simple_width")
            col.prop(self, "Simple_length")
            col.prop(self, "Simple_rounded")

            box.prop(self, "Simple_center")
            l = 2 * abs(self.Simple_width) + 2 * abs(self.Simple_length)
            s = abs(self.Simple_width) * abs(self.Simple_length)

        if self.Simple_Type == 'Rhomb':
            box = layout.box()
            col = box.column(align=True)
            col.label(text=self.Simple_Type + " Options:")
            col.prop(self, "Simple_width")
            col.prop(self, "Simple_length")
            col.prop(self, "Simple_center")

            g = hypot(self.Simple_width / 2, self.Simple_length / 2)
            l = 4 * g
            s = self.Simple_width * self.Simple_length / 2

        if self.Simple_Type == 'Polygon':
            box = layout.box()
            col = box.column(align=True)
            col.label(text=self.Simple_Type + " Options:")
            col.prop(self, "Simple_sides")
            col.prop(self, "Simple_radius")

        if self.Simple_Type == 'Polygon_ab':
            box = layout.box()
            col = box.column(align=True)
            col.label(text="Polygon ab Options:")
            col.prop(self, "Simple_sides")
            col.prop(self, "Simple_a")
            col.prop(self, "Simple_b")

        if self.Simple_Type == 'Trapezoid':
            box = layout.box()
            col = box.column(align=True)
            col.label(text=self.Simple_Type + " Options:")
            col.prop(self, "Simple_a")
            col.prop(self, "Simple_b")
            col.prop(self, "Simple_h")

            box.prop(self, "Simple_center")
            g = hypot(self.Simple_h, (self.Simple_a - self.Simple_b) / 2)
            l = self.Simple_a + self.Simple_b + g * 2
            s = (abs(self.Simple_a) + abs(self.Simple_b)) / 2 * self.Simple_h

        row = layout.row()
        row.prop(self, "shape", expand=True)

        # output options
        col = layout.column()
        col.label(text="Output Curve Type:")
        col.row().prop(self, "outputType", expand=True)

        if self.outputType == 'NURBS':
            col.prop(self, "order_u")
        elif self.outputType == 'BEZIER':
            col.row().prop(self, 'handleType', expand=True)

        col = layout.column()
        col.row().prop(self, "use_cyclic_u", expand=True)

        col = layout.column()
        col.row().prop(self, "edit_mode", expand=True)

        col = layout.column()
        # AddObjectHelper props
        col.prop(self, "align")
        col.prop(self, "location")
        col.prop(self, "rotation")

        if l != 0 or s != 0:
            box = layout.box()
            box.label(text="Statistics:", icon="INFO")
        if l != 0:
            l_str = str(round(l, 4))
            box.label(text="Length: " + l_str)
        if s != 0:
            s_str = str(round(s, 4))
            box.label(text="Area: " + s_str)

    @classmethod
    def poll(cls, context):
        return context.scene is not None

    def execute(self, context):

        # turn off 'Enter Edit Mode'
        use_enter_edit_mode = bpy.context.preferences.edit.use_enter_edit_mode
        bpy.context.preferences.edit.use_enter_edit_mode = False

        # main function
        main(context, self, use_enter_edit_mode)

        if use_enter_edit_mode:
            bpy.ops.object.mode_set(mode = 'EDIT')

        # restore pre operator state
        bpy.context.preferences.edit.use_enter_edit_mode = use_enter_edit_mode

        if self.edit_mode:
            bpy.ops.object.mode_set(mode = 'EDIT')
        else:
            bpy.ops.object.mode_set(mode = 'OBJECT')

        return {'FINISHED'}

    def invoke(self, context, event):

        self.execute(context)

        return {'FINISHED'}

# Register
classes = [
    Simple,
]

def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

    bpy.types.VIEW3D_MT_curve_add.append(menu)

def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)

    bpy.types.VIEW3D_MT_curve_add.remove(menu)

if __name__ == "__main__":
    register()

# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and / or
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
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110 - 1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

bl_info = {
    'name': 'Simple Curve',
    'author': 'Spivak Vladimir (http://cwolf3d.korostyshev.net)',
    'version': (1, 5, 2),
    'blender': (2, 6, 9),
    'location': 'View3D > Add > Curve',
    'description': 'Adds Simple Curve',
    'warning': '',  # used for warning icon and text in addons panel
    'wiki_url': 'http://wiki.blender.org/index.php/Extensions:2.6/Py/Scripts/Curve/Simple_curves',
    "tracker_url": "https://developer.blender.org/maniphest/task/edit/form/2/",
    'category': 'Add Curve'}


# ------------------------------------------------------------
#### import modules
import bpy
from bpy.props import *
from mathutils import *
from math import *
from bpy_extras.object_utils import *
from random import *

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
    j = sides
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
# calculates the matrix for the new object
# depending on user pref


def align_matrix(context, location):
    loc = Matrix.Translation(location)
    obj_align = context.user_preferences.edit.object_align
    if (context.space_data.type == 'VIEW_3D'
            and obj_align == 'VIEW'):
        rot = context.space_data.region_3d.view_matrix.to_3x3().inverted().to_4x4()
    else:
        rot = Matrix()
    align_matrix = loc * rot

    return align_matrix

# ------------------------------------------------------------
# Main Function


def main(context, self, align_matrix):
    # deselect all objects
    bpy.ops.object.select_all(action='DESELECT')

    # create object
    name = self.Simple_Type         # Type as name

    # create curve
    scene = bpy.context.scene
    newCurve = bpy.data.curves.new(name, type='CURVE')  # curvedatablock
    newSpline = newCurve.splines.new('BEZIER')  # spline

    # set curveOptions
    newCurve.dimensions = self.shape
    newSpline.use_endpoint_u = True

    sides = abs(int((self.Simple_endangle - self.Simple_startangle) / 90))

    # get verts
    if self.Simple_Type == 'Point':
        verts = SimplePoint()
        newSpline.use_cyclic_u = False

    if self.Simple_Type == 'Line':
        verts = SimpleLine(self.Simple_startlocation, self.Simple_endlocation)
        newSpline.use_cyclic_u = False
        newCurve.dimensions = '3D'

    if self.Simple_Type == 'Distance':
        verts = SimpleDistance(self.Simple_length, self.Simple_center)
        newSpline.use_cyclic_u = False

    if self.Simple_Type == 'Angle':
        verts = SimpleAngle(self.Simple_length, self.Simple_angle)
        newSpline.use_cyclic_u = False

    if self.Simple_Type == 'Circle':
        if self.Simple_sides < 4:
            self.Simple_sides = 4
        verts = SimpleCircle(self.Simple_sides, self.Simple_radius)
        newSpline.use_cyclic_u = True

    if self.Simple_Type == 'Ellipse':
        verts = SimpleEllipse(self.Simple_a, self.Simple_b)
        newSpline.use_cyclic_u = True

    if self.Simple_Type == 'Arc':
        if self.Simple_sides < sides:
            self.Simple_sides = sides
        if self.Simple_radius == 0:
            return {'FINISHED'}
        verts = SimpleArc(self.Simple_sides, self.Simple_radius, self.Simple_startangle, self.Simple_endangle)
        newSpline.use_cyclic_u = False

    if self.Simple_Type == 'Sector':
        if self.Simple_sides < sides:
            self.Simple_sides = sides
        if self.Simple_radius == 0:
            return {'FINISHED'}
        verts = SimpleSector(self.Simple_sides, self.Simple_radius, self.Simple_startangle, self.Simple_endangle)
        newSpline.use_cyclic_u = True

    if self.Simple_Type == 'Segment':
        if self.Simple_sides < sides:
            self.Simple_sides = sides
        if self.Simple_a == 0 or self.Simple_b == 0:
            return {'FINISHED'}
        verts = SimpleSegment(self.Simple_sides, self.Simple_a, self.Simple_b, self.Simple_startangle, self.Simple_endangle)
        newSpline.use_cyclic_u = True

    if self.Simple_Type == 'Rectangle':
        verts = SimpleRectangle(self.Simple_width, self.Simple_length, self.Simple_rounded, self.Simple_center)
        newSpline.use_cyclic_u = True

    if self.Simple_Type == 'Rhomb':
        verts = SimpleRhomb(self.Simple_width, self.Simple_length, self.Simple_center)
        newSpline.use_cyclic_u = True

    if self.Simple_Type == 'Polygon':
        if self.Simple_sides < 3:
            self.Simple_sides = 3
        verts = SimplePolygon(self.Simple_sides, self.Simple_radius)
        newSpline.use_cyclic_u = True

    if self.Simple_Type == 'Polygon_ab':
        if self.Simple_sides < 3:
            self.Simple_sides = 3
        verts = SimplePolygon_ab(self.Simple_sides, self.Simple_a, self.Simple_b)
        newSpline.use_cyclic_u = True

    if self.Simple_Type == 'Trapezoid':
        verts = SimpleTrapezoid(self.Simple_a, self.Simple_b, self.Simple_h, self.Simple_center)
        newSpline.use_cyclic_u = True

    vertArray = []
    for v in verts:
        vertArray += v

    newSpline.bezier_points.add(int(len(vertArray) * 0.333333333))
    newSpline.bezier_points.foreach_set('co', vertArray)

    # create object with newCurve
    SimpleCurve = bpy.data.objects.new(name, newCurve)  # object
    scene.objects.link(SimpleCurve)  # place in active scene
    SimpleCurve.select = True  # set as selected
    scene.objects.active = SimpleCurve  # set as active
    SimpleCurve.matrix_world = align_matrix  # apply matrix
    SimpleCurve.rotation_euler = self.Simple_rotation_euler

    all_points = [p for p in newSpline.bezier_points]
    d = 2 * 0.27606262
    n = 0
    for p in all_points:
        p.handle_right_type = 'VECTOR'
        p.handle_left_type = 'VECTOR'
        n += 1

    if self.Simple_Type == 'Circle' or self.Simple_Type == 'Arc' or self.Simple_Type == 'Sector' or self.Simple_Type == 'Segment' or self.Simple_Type == 'Ellipse':
        for p in all_points:
            p.handle_right_type = 'FREE'
            p.handle_left_type = 'FREE'

    if self.Simple_Type == 'Circle':
        i = 0
        for p1 in all_points:
            if i != n - 1:
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
            if i == n - 1:
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
            if i != n - 1:
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

    if self.Simple_Type == 'Sector':
        i = 0
        for p1 in all_points:
            if i == 0:
                p1.handle_right_type = 'VECTOR'
                p1.handle_left_type = 'VECTOR'
            elif i != n - 1:
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

    if self.Simple_Type == 'Segment':
        i = 0
        for p1 in all_points:
            if i < n / 2 - 1:
                p2 = all_points[i + 1]
                u1 = asin(p1.co.y / self.Simple_a)
                u2 = asin(p2.co.y / self.Simple_a)
                if p1.co.x > 0 and p2.co.x < 0:
                    u1 = acos(p1.co.x / self.Simple_a)
                    u2 = acos(p2.co.x / self.Simple_a)
                elif p1.co.x < 0 and p2.co.x > 0:
                    u1 = acos(p1.co.x / self.Simple_a)
                    u2 = acos(p2.co.x / self.Simple_a)
                u = u2 - u1
                if u < 0:
                    u = -u
                l = 4 / 3 * tan(1 / 4 * u) * self.Simple_a
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
            elif i != n / 2 - 1 and i != n - 1:
                p2 = all_points[i + 1]
                u1 = asin(p1.co.y / self.Simple_b)
                u2 = asin(p2.co.y / self.Simple_b)
                if p1.co.x > 0 and p2.co.x < 0:
                    u1 = acos(p1.co.x / self.Simple_b)
                    u2 = acos(p2.co.x / self.Simple_b)
                elif p1.co.x < 0 and p2.co.x > 0:
                    u1 = acos(p1.co.x / self.Simple_b)
                    u2 = acos(p2.co.x / self.Simple_b)
                u = u2 - u1
                if u < 0:
                    u = -u
                l = 4 / 3 * tan(1 / 4 * u) * self.Simple_b
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

    SimpleCurve.Simple = True
    SimpleCurve.Simple_Change = False
    SimpleCurve.Simple_Type = self.Simple_Type
    SimpleCurve.Simple_startlocation = self.Simple_startlocation
    SimpleCurve.Simple_endlocation = self.Simple_endlocation
    SimpleCurve.Simple_a = self.Simple_a
    SimpleCurve.Simple_b = self.Simple_b
    SimpleCurve.Simple_h = self.Simple_h
    SimpleCurve.Simple_angle = self.Simple_angle
    SimpleCurve.Simple_startangle = self.Simple_startangle
    SimpleCurve.Simple_endangle = self.Simple_endangle
    SimpleCurve.Simple_rotation_euler = self.Simple_rotation_euler
    SimpleCurve.Simple_sides = self.Simple_sides
    SimpleCurve.Simple_radius = self.Simple_radius
    SimpleCurve.Simple_center = self.Simple_center
    SimpleCurve.Simple_width = self.Simple_width
    SimpleCurve.Simple_length = self.Simple_length
    SimpleCurve.Simple_rounded = self.Simple_rounded

    bpy.ops.object.mode_set(mode='EDIT', toggle=True)
    bpy.ops.curve.select_all(action='SELECT')
    bpy.ops.object.mode_set(mode='OBJECT', toggle=True)

    return

# ------------------------------------------------------------
# Delete simple curve


def SimpleDelete(name):
    if bpy.ops.object.mode_set.poll():
        bpy.ops.object.mode_set(mode='OBJECT')

    bpy.context.scene.objects.active = bpy.data.objects[name]
    bpy.ops.object.delete()

    return

# ------------------------------------------------------------
# Simple operator


class Simple(bpy.types.Operator):
    ''''''
    bl_idname = "curve.simple"
    bl_label = "Simple curve"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "adds simple curve"

    # align_matrix for the invoke
    align_matrix = Matrix()

    # change properties
    Simple = BoolProperty(name="Simple",
                          default=True,
                          description="simple curve")

    Simple_Change = BoolProperty(name="Change",
                                 default=False,
                                 description="change simple curve")

    Simple_Delete = StringProperty(name="Delete",
                                   description="Delete simple curve")

    # general properties
    Types = [('Point', 'Point', 'Point'),
             ('Line', 'Line', 'Line'),
             ('Distance', 'Distance', 'Distance'),
             ('Angle', 'Angle', 'Angle'),
             ('Circle', 'Circle', 'Circle'),
             ('Ellipse', 'Ellipse', 'Ellipse'),
             ('Arc', 'Arc', 'Arc'),
             ('Sector', 'Sector', 'Sector'),
             ('Segment', 'Segment', 'Segment'),
             ('Rectangle', 'Rectangle', 'Rectangle'),
             ('Rhomb', 'Rhomb', 'Rhomb'),
             ('Polygon', 'Polygon', 'Polygon'),
             ('Polygon_ab', 'Polygon_ab', 'Polygon_ab'),
             ('Trapezoid', 'Trapezoid', 'Trapezoid')]
    Simple_Type = EnumProperty(name="Type",
                               description="Form of Curve to create",
                               items=Types)

    # Line properties
    Simple_startlocation = FloatVectorProperty(name="",
                                               description="Start location",
                                               default=(0.0, 0.0, 0.0),
                                               subtype='TRANSLATION')
    Simple_endlocation = FloatVectorProperty(name="",
                                             description="End location",
                                             default=(2.0, 2.0, 2.0),
                                             subtype='TRANSLATION')
    Simple_rotation_euler = FloatVectorProperty(name="",
                                                description="Rotation",
                                                default=(0.0, 0.0, 0.0),
                                                subtype='EULER')

    # Trapezoid properties
    Simple_a = FloatProperty(name="a",
                             default=2.0,
                             min=0.0, soft_min=0.0,
                             unit='LENGTH',
                             description="a")
    Simple_b = FloatProperty(name="b",
                             default=1.0,
                             min=0.0, soft_min=0.0,
                             unit='LENGTH',
                             description="b")
    Simple_h = FloatProperty(name="h",
                             default=1.0,
                             unit='LENGTH',
                             description="h")

    Simple_angle = FloatProperty(name="Angle",
                                 default=45.0,
                                 description="Angle")
    Simple_startangle = FloatProperty(name="Start angle",
                                      default=0.0,
                                      min=-360.0, soft_min=-360.0,
                                      max=360.0, soft_max=360.0,
                                      description="Start angle")
    Simple_endangle = FloatProperty(name="End angle",
                                    default=45.0,
                                    min=-360.0, soft_min=-360.0,
                                    max=360.0, soft_max=360.0,
                                    description="End angle")

    Simple_sides = IntProperty(name="sides",
                               default=3,
                               min=0, soft_min=0,
                               description="sides")

    Simple_radius = FloatProperty(name="radius",
                                  default=1.0,
                                  min=0.0, soft_min=0.0,
                                  unit='LENGTH',
                                  description="radius")

    Simple_center = BoolProperty(name="Length center",
                                 default=True,
                                 description="Length center")

    Angle_types = [('Degrees', 'Degrees', 'Degrees'),
                   ('Radians', 'Radians', 'Radians')]
    Simple_degrees_or_radians = EnumProperty(name="Degrees or radians",
                                             description="Degrees or radians",
                                             items=Angle_types)

    # Rectangle properties
    Simple_width = FloatProperty(name="Width",
                                 default=2.0,
                                 min=0.0, soft_min=0,
                                 unit='LENGTH',
                                 description="Width")
    Simple_length = FloatProperty(name="Length",
                                  default=2.0,
                                  min=0.0, soft_min=0.0,
                                  unit='LENGTH',
                                  description="Length")
    Simple_rounded = FloatProperty(name="Rounded",
                                   default=0.0,
                                   min=0.0, soft_min=0.0,
                                   unit='LENGTH',
                                   description="Rounded")

    # Curve Options
    shapeItems = [
        ('2D', '2D', '2D'),
        ('3D', '3D', '3D')]
    shape = EnumProperty(name="2D / 3D",
                         items=shapeItems,
                         description="2D or 3D Curve")

    ##### DRAW #####
    def draw(self, context):
        layout = self.layout

        # general options
        col = layout.column()
        col.prop(self, 'Simple_Type')

        l = 0
        s = 0

        if self.Simple_Type == 'Line':
            col.label(text=self.Simple_Type + " Options")
            box = layout.box()
            box.prop(self, 'Simple_endlocation')
            v = Vector(self.Simple_endlocation) - Vector(self.Simple_startlocation)
            l = v.length

        if self.Simple_Type == 'Distance':
            col.label(text=self.Simple_Type + " Options")
            box = layout.box()
            box.prop(self, 'Simple_length')
            box.prop(self, 'Simple_center')
            l = self.Simple_length

        if self.Simple_Type == 'Angle':
            col.label(text=self.Simple_Type + " Options")
            box = layout.box()
            box.prop(self, 'Simple_length')
            box.prop(self, 'Simple_angle')
            row = layout.row()
            row.prop(self, 'Simple_degrees_or_radians', expand=True)

        if self.Simple_Type == 'Circle':
            col.label(text=self.Simple_Type + " Options")
            box = layout.box()
            box.prop(self, 'Simple_sides')
            box.prop(self, 'Simple_radius')
            l = 2 * pi * abs(self.Simple_radius)
            s = pi * self.Simple_radius * self.Simple_radius

        if self.Simple_Type == 'Ellipse':
            col.label(text=self.Simple_Type + " Options")
            box = layout.box()
            box.prop(self, 'Simple_a')
            box.prop(self, 'Simple_b')
            l = pi * (3 * (self.Simple_a + self.Simple_b) - sqrt((3 * self.Simple_a + self.Simple_b) * (self.Simple_a + 3 * self.Simple_b)))
            s = pi * abs(self.Simple_b) * abs(self.Simple_a)

        if self.Simple_Type == 'Arc':
            col.label(text=self.Simple_Type + " Options")
            box = layout.box()
            box.prop(self, 'Simple_sides')
            box.prop(self, 'Simple_radius')
            box.prop(self, 'Simple_startangle')
            box.prop(self, 'Simple_endangle')
            row = layout.row()
            row.prop(self, 'Simple_degrees_or_radians', expand=True)
            l = abs(pi * self.Simple_radius * (self.Simple_endangle - self.Simple_startangle) / 180)

        if self.Simple_Type == 'Sector':
            col.label(text=self.Simple_Type + " Options")
            box = layout.box()
            box.prop(self, 'Simple_sides')
            box.prop(self, 'Simple_radius')
            box.prop(self, 'Simple_startangle')
            box.prop(self, 'Simple_endangle')
            row = layout.row()
            row.prop(self, 'Simple_degrees_or_radians', expand=True)
            l = abs(pi * self.Simple_radius * (self.Simple_endangle - self.Simple_startangle) / 180) + self.Simple_radius * 2
            s = pi * self.Simple_radius * self.Simple_radius * abs(self.Simple_endangle - self.Simple_startangle) / 360

        if self.Simple_Type == 'Segment':
            col.label(text=self.Simple_Type + " Options")
            box = layout.box()
            box.prop(self, 'Simple_sides')
            box.prop(self, 'Simple_a')
            box.prop(self, 'Simple_b')
            box.prop(self, 'Simple_startangle')
            box.prop(self, 'Simple_endangle')
            row = layout.row()
            row.prop(self, 'Simple_degrees_or_radians', expand=True)
            la = abs(pi * self.Simple_a * (self.Simple_endangle - self.Simple_startangle) / 180)
            lb = abs(pi * self.Simple_b * (self.Simple_endangle - self.Simple_startangle) / 180)
            l = abs(self.Simple_a - self.Simple_b) * 2 + la + lb
            sa = pi * self.Simple_a * self.Simple_a * abs(self.Simple_endangle - self.Simple_startangle) / 360
            sb = pi * self.Simple_b * self.Simple_b * abs(self.Simple_endangle - self.Simple_startangle) / 360
            s = abs(sa - sb)

        if self.Simple_Type == 'Rectangle':
            col.label(text=self.Simple_Type + " Options")
            box = layout.box()
            box.prop(self, 'Simple_width')
            box.prop(self, 'Simple_length')
            box.prop(self, 'Simple_rounded')
            box.prop(self, 'Simple_center')
            l = 2 * abs(self.Simple_width) + 2 * abs(self.Simple_length)
            s = abs(self.Simple_width) * abs(self.Simple_length)

        if self.Simple_Type == 'Rhomb':
            col.label(text=self.Simple_Type + " Options")
            box = layout.box()
            box.prop(self, 'Simple_width')
            box.prop(self, 'Simple_length')
            box.prop(self, 'Simple_center')
            g = hypot(self.Simple_width / 2, self.Simple_length / 2)
            l = 4 * g
            s = self.Simple_width * self.Simple_length / 2

        if self.Simple_Type == 'Polygon':
            col.label(text=self.Simple_Type + " Options")
            box = layout.box()
            box.prop(self, 'Simple_sides')
            box.prop(self, 'Simple_radius')

        if self.Simple_Type == 'Polygon_ab':
            col.label(text=self.Simple_Type + " Options")
            box = layout.box()
            box.prop(self, 'Simple_sides')
            box.prop(self, 'Simple_a')
            box.prop(self, 'Simple_b')

        if self.Simple_Type == 'Trapezoid':
            col.label(text=self.Simple_Type + " Options")
            box = layout.box()
            box.prop(self, 'Simple_a')
            box.prop(self, 'Simple_b')
            box.prop(self, 'Simple_h')
            box.prop(self, 'Simple_center')
            g = hypot(self.Simple_h, (self.Simple_a - self.Simple_b) / 2)
            l = self.Simple_a + self.Simple_b + g * 2
            s = (abs(self.Simple_a) + abs(self.Simple_b)) / 2 * self.Simple_h

        row = layout.row()
        row.prop(self, 'shape', expand=True)
        box = layout.box()
        box.label("Location:")
        box.prop(self, 'Simple_startlocation')
        box = layout.box()
        box.label("Rotation:")
        box.prop(self, 'Simple_rotation_euler')
        if l != 0:
            l_str = str(round(l, 4))
            row = layout.row()
            row.label("Length: " + l_str)
        if s != 0:
            s_str = str(round(s, 4))
            row = layout.row()
            row.label("Area: " + s_str)

    ##### POLL #####
    @classmethod
    def poll(cls, context):
        return context.scene != None

    ##### EXECUTE #####
    def execute(self, context):
        if self.Simple_Change:
            SimpleDelete(self.Simple_Delete)

        # go to object mode
        if bpy.ops.object.mode_set.poll():
            bpy.ops.object.mode_set(mode='OBJECT')

        # turn off undo
        undo = bpy.context.user_preferences.edit.use_global_undo
        bpy.context.user_preferences.edit.use_global_undo = False

        # main function
        self.align_matrix = align_matrix(context, self.Simple_startlocation)
        main(context, self, self.align_matrix)

        # restore pre operator undo state
        bpy.context.user_preferences.edit.use_global_undo = undo

        return {'FINISHED'}

    ##### INVOKE #####
    def invoke(self, context, event):
        # store creation_matrix
        if self.Simple_Change:
            bpy.context.scene.cursor_location = self.Simple_startlocation
        else:
            self.Simple_startlocation = bpy.context.scene.cursor_location

        self.align_matrix = align_matrix(context, self.Simple_startlocation)
        self.execute(context)

        return {'FINISHED'}

# ------------------------------------------------------------
# Fillet


class BezierPointsFillet(bpy.types.Operator):
    ''''''
    bl_idname = "curve.bezier_points_fillet"
    bl_label = "Bezier points fillet"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "bezier points fillet"

    Fillet_radius = FloatProperty(name="Radius",
                                  default=0.25,
                                  unit='LENGTH',
                                  description="radius")

    Types = [('Round', 'Round', 'Round'),
             ('Chamfer', 'Chamfer', 'Chamfer')]
    Fillet_Type = EnumProperty(name="Type",
                               description="Fillet type",
                               items=Types)

    ##### DRAW #####
    def draw(self, context):
        layout = self.layout

        # general options
        col = layout.column()
        col.prop(self, 'Fillet_radius')
        col.prop(self, 'Fillet_Type', expand=True)

    ##### POLL #####
    @classmethod
    def poll(cls, context):
        return context.scene != None

    ##### EXECUTE #####
    def execute(self, context):
        # go to object mode
        if bpy.ops.object.mode_set.poll():
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.mode_set(mode='EDIT')

        # turn off undo
        undo = bpy.context.user_preferences.edit.use_global_undo
        bpy.context.user_preferences.edit.use_global_undo = False

        # main function
        spline = bpy.context.object.data.splines.active
        selected = [p for p in spline.bezier_points if p.select_control_point]

        bpy.ops.curve.handle_type_set(type='VECTOR')
        n = 0
        ii = []
        for p in spline.bezier_points:
            if p.select_control_point:
                ii.append(n)
                n += 1
            else:
                n += 1

        if n > 2:

            jn = 0

            for j in ii:

                j += jn

                selected_all = [p for p in spline.bezier_points]

                bpy.ops.curve.select_all(action='DESELECT')

                if j != 0 and j != n - 1:
                    selected_all[j].select_control_point = True
                    selected_all[j + 1].select_control_point = True
                    bpy.ops.curve.subdivide()
                    selected_all = [p for p in spline.bezier_points]
                    selected4 = [selected_all[j - 1], selected_all[j], selected_all[j + 1], selected_all[j + 2]]
                    jn += 1
                    n += 1

                elif j == 0:
                    selected_all[j].select_control_point = True
                    selected_all[j + 1].select_control_point = True
                    bpy.ops.curve.subdivide()
                    selected_all = [p for p in spline.bezier_points]
                    selected4 = [selected_all[n], selected_all[0], selected_all[1], selected_all[2]]
                    jn += 1
                    n += 1

                elif j == n - 1:
                    selected_all[j].select_control_point = True
                    selected_all[j - 1].select_control_point = True
                    bpy.ops.curve.subdivide()
                    selected_all = [p for p in spline.bezier_points]
                    selected4 = [selected_all[0], selected_all[n], selected_all[n - 1], selected_all[n - 2]]

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

        bpy.ops.curve.select_all(action='SELECT')
        bpy.ops.curve.spline_type_set(type='BEZIER')

        # restore pre operator undo state
        bpy.context.user_preferences.edit.use_global_undo = undo

        return {'FINISHED'}

    ##### INVOKE #####
    def invoke(self, context, event):
        self.execute(context)

        return {'FINISHED'}


def subdivide_cubic_bezier(p1, p2, p3, p4, t):
    p12 = (p2 - p1) * t + p1
    p23 = (p3 - p2) * t + p2
    p34 = (p4 - p3) * t + p3
    p123 = (p23 - p12) * t + p12
    p234 = (p34 - p23) * t + p23
    p1234 = (p234 - p123) * t + p123
    return [p12, p123, p1234, p234, p34]

# ------------------------------------------------------------
# BezierDivide Operator


class BezierDivide(bpy.types.Operator):
    ''''''
    bl_idname = "curve.bezier_spline_divide"
    bl_label = "Bezier Divide (enters edit mode) for Fillet Curves"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "bezier spline divide"

    # align_matrix for the invoke
    align_matrix = Matrix()

    Bezier_t = FloatProperty(name="t (0% - 100%)",
                             default=50.0,
                             min=0.0, soft_min=0.0,
                             max=100.0, soft_max=100.0,
                             description="t (0% - 100%)")

    ##### POLL #####
    @classmethod
    def poll(cls, context):
        return context.scene != None

    ##### EXECUTE #####
    def execute(self, context):
        # go to object mode
        if bpy.ops.object.mode_set.poll():
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.mode_set(mode='EDIT')

        # turn off undo
        undo = bpy.context.user_preferences.edit.use_global_undo
        bpy.context.user_preferences.edit.use_global_undo = False

        # main function
        spline = bpy.context.object.data.splines.active
        vertex = []
        selected_all = [p for p in spline.bezier_points if p.select_control_point]
        h = subdivide_cubic_bezier(selected_all[0].co, selected_all[0].handle_right, selected_all[1].handle_left, selected_all[1].co, self.Bezier_t / 100)

        selected_all[0].handle_right_type = 'FREE'
        selected_all[0].handle_left_type = 'FREE'
        selected_all[1].handle_right_type = 'FREE'
        selected_all[1].handle_left_type = 'FREE'
        bpy.ops.curve.subdivide(1)
        selected_all = [p for p in spline.bezier_points if p.select_control_point]

        selected_all[0].handle_right = h[0]
        selected_all[1].co = h[2]
        selected_all[1].handle_left = h[1]
        selected_all[1].handle_right = h[3]
        selected_all[2].handle_left = h[4]

        # restore pre operator undo state
        bpy.context.user_preferences.edit.use_global_undo = undo

        return {'FINISHED'}

    ##### INVOKE #####
    def invoke(self, context, event):
        self.execute(context)

        return {'FINISHED'}

# ------------------------------------------------------------
# Simple change panel


class SimplePanel(bpy.types.Panel):

    bl_label = "Simple change"
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_options = {'DEFAULT_CLOSED'}
    bl_category = "Tools"

    ##### POLL #####
    @classmethod
    def poll(cls, context):
        if context.object.Simple == True:
            return (context.object)

    ##### DRAW #####
    def draw(self, context):
        if context.object.Simple == True:
            layout = self.layout

            obj = context.object
            row = layout.row()
            simple_change = row.operator("curve.simple", text='Change')
            simple_change.Simple_Change = True
            simple_change.Simple_Delete = obj.name
            simple_change.Simple_Type = obj.Simple_Type
            simple_change.Simple_startlocation = obj.location
            simple_change.Simple_endlocation = obj.Simple_endlocation
            simple_change.Simple_a = obj.Simple_a
            simple_change.Simple_b = obj.Simple_b
            simple_change.Simple_h = obj.Simple_h
            simple_change.Simple_angle = obj.Simple_angle
            simple_change.Simple_startangle = obj.Simple_startangle
            simple_change.Simple_endangle = obj.Simple_endangle
            simple_change.Simple_rotation_euler = obj.rotation_euler
            simple_change.Simple_sides = obj.Simple_sides
            simple_change.Simple_radius = obj.Simple_radius
            simple_change.Simple_center = obj.Simple_center
            simple_change.Simple_width = obj.Simple_width
            simple_change.Simple_length = obj.Simple_length
            simple_change.Simple_rounded = obj.Simple_rounded

# ------------------------------------------------------------
# Fillet tools panel


class SimpleEdit(bpy.types.Operator):

    """Curve Simple"""
    bl_idname = "object._simple_edit"
    bl_label = "Create Curves"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Subdivide & Fillet Curves"

    ##### POLL #####
    @classmethod
    def poll(cls, context):
        vertex = []
        nselected = []
        n = 0
        obj = context.active_object
        if obj != None:
            if obj.type == 'CURVE':
                for i in obj.data.splines:
                    for j in i.bezier_points:
                        n += 1
                        if j.select_control_point:
                            nselected.append(n)
                            vertex.append(obj.matrix_world * j.co)

            if len(vertex) > 0 and n > 2:
                return (context.active_object)
            if len(vertex) == 2 and abs(nselected[0] - nselected[1]) == 1:
                return (context.active_object)

        selected = 0
        for obj in context.selected_objects:
            if obj.type == 'CURVE':
                selected += 1

        if selected >= 2:
            return (context.selected_objects)

    ##### DRAW #####
    def draw(self, context):
        vertex = []
        selected = []
        n = 0
        obj = context.active_object
        if obj != None:
            if obj.type == 'CURVE':
                for i in obj.data.splines:
                    for j in i.bezier_points:
                        n += 1
                        if j.select_control_point:
                            selected.append(n)
                            vertex.append(obj.matrix_world * j.co)

            if len(vertex) > 0 and n > 2:
                layout = self.layout
                row = layout.row()
                simple_edit = row.operator("curve.bezier_points_fillet", text='Fillet')
            if len(vertex) == 2 and abs(selected[0] - selected[1]) == 1:
                layout = self.layout
                row = layout.row()
                simple_divide = row.operator("curve.bezier_spline_divide", text='Divide')

# ------------------------------------------------------------
# location update


def StartLocationUpdate(self, context):

    bpy.context.scene.cursor_location = self.Simple_startlocation

    return

# ------------------------------------------------------------
# Add properties to objects


def SimpleVariables():

    bpy.types.Object.Simple = bpy.props.BoolProperty()
    bpy.types.Object.Simple_Change = bpy.props.BoolProperty()
    # general properties
    Types = [('Point', 'Point', 'Point'),
             ('Line', 'Line', 'Line'),
             ('Distance', 'Distance', 'Distance'),
             ('Angle', 'Angle', 'Angle'),
             ('Circle', 'Circle', 'Circle'),
             ('Ellipse', 'Ellipse', 'Ellipse'),
             ('Arc', 'Arc', 'Arc'),
             ('Sector', 'Sector', 'Sector'),
             ('Segment', 'Segment', 'Segment'),
             ('Rectangle', 'Rectangle', 'Rectangle'),
             ('Rhomb', 'Rhomb', 'Rhomb'),
             ('Polygon', 'Polygon', 'Polygon'),
             ('Polygon_ab', 'Polygon_ab', 'Polygon_ab'),
             ('Trapezoid', 'Trapezoid', 'Trapezoid')]
    bpy.types.Object.Simple_Type = bpy.props.EnumProperty(name="Type",
                                                          description="Form of Curve to create",
                                                          items=Types)

    # Line properties
    bpy.types.Object.Simple_startlocation = bpy.props.FloatVectorProperty(name="Start location",
                                                                          description="Start location",
                                                                          default=(0.0, 0.0, 0.0),
                                                                          subtype='TRANSLATION',
                                                                          update=StartLocationUpdate)
    bpy.types.Object.Simple_endlocation = bpy.props.FloatVectorProperty(name="End location",
                                                                        description="End location",
                                                                        default=(2.0, 2.0, 2.0),
                                                                        subtype='TRANSLATION')
    bpy.types.Object.Simple_rotation_euler = bpy.props.FloatVectorProperty(name="Rotation",
                                                                           description="Rotation",
                                                                           default=(0.0, 0.0, 0.0),
                                                                           subtype='EULER')

    # Trapezoid properties
    bpy.types.Object.Simple_a = bpy.props.FloatProperty(name="a",
                                                        default=2.0,
                                                        min=0.0, soft_min=0.0,
                                                        unit='LENGTH',
                                                        description="a")
    bpy.types.Object.Simple_b = bpy.props.FloatProperty(name="b",
                                                        default=1.0,
                                                        min=0.0, soft_min=0.0,
                                                        unit='LENGTH',
                                                        description="b")
    bpy.types.Object.Simple_h = bpy.props.FloatProperty(name="h",
                                                        default=1.0,
                                                        unit='LENGTH',
                                                        description="h")

    bpy.types.Object.Simple_angle = bpy.props.FloatProperty(name="Angle",
                                                            default=45.0,
                                                            description="Angle")
    bpy.types.Object.Simple_startangle = bpy.props.FloatProperty(name="Start angle",
                                                                 default=0.0,
                                                                 min=-360.0, soft_min=-360.0,
                                                                 max=360.0, soft_max=360.0,
                                                                 description="Start angle")
    bpy.types.Object.Simple_endangle = bpy.props.FloatProperty(name="End angle",
                                                               default=45.0,
                                                               min=-360.0, soft_min=-360.0,
                                                               max=360.0, soft_max=360.0,
                                                               description="End angle")

    bpy.types.Object.Simple_sides = bpy.props.IntProperty(name="sides",
                                                          default=3,
                                                          min=3, soft_min=3,
                                                          description="sides")

    bpy.types.Object.Simple_radius = bpy.props.FloatProperty(name="radius",
                                                             default=1.0,
                                                             min=0.0, soft_min=0.0,
                                                             unit='LENGTH',
                                                             description="radius")

    bpy.types.Object.Simple_center = bpy.props.BoolProperty(name="Length center",
                                                            default=True,
                                                            description="Length center")

    # Rectangle properties
    bpy.types.Object.Simple_width = bpy.props.FloatProperty(name="Width",
                                                            default=2.0,
                                                            min=0.0, soft_min=0.0,
                                                            unit='LENGTH',
                                                            description="Width")
    bpy.types.Object.Simple_length = bpy.props.FloatProperty(name="Length",
                                                             default=2.0,
                                                             min=0.0, soft_min=0.0,
                                                             unit='LENGTH',
                                                             description="Length")
    bpy.types.Object.Simple_rounded = bpy.props.FloatProperty(name="Rounded",
                                                              default=0.0,
                                                              unit='LENGTH',
                                                              description="Rounded")

################################################################################
##### REGISTER #####


class INFO_MT_simple_menu(bpy.types.Menu):
    # Define the "Extras" menu
    bl_idname = "INFO_MT_simple_menu"
    bl_label = "Curve Objects"

    def draw(self, context):
        self.layout.operator_context = 'INVOKE_REGION_WIN'

        oper2 = self.layout.operator(Simple.bl_idname, text="Point", icon="PLUGIN")
        oper2.Simple_Change = False
        oper2.Simple_Type = "Point"

        oper3 = self.layout.operator(Simple.bl_idname, text="Line", icon="PLUGIN")
        oper3.Simple_Change = False
        oper3.Simple_Type = "Line"

        oper4 = self.layout.operator(Simple.bl_idname, text="Distance", icon="PLUGIN")
        oper4.Simple_Change = False
        oper4.Simple_Type = "Distance"

        oper5 = self.layout.operator(Simple.bl_idname, text="Angle", icon="PLUGIN")
        oper5.Simple_Change = False
        oper5.Simple_Type = "Angle"

        oper6 = self.layout.operator(Simple.bl_idname, text="Circle", icon="PLUGIN")
        oper6.Simple_Change = False
        oper6.Simple_Type = "Circle"

        oper7 = self.layout.operator(Simple.bl_idname, text="Ellipse", icon="PLUGIN")
        oper7.Simple_Change = False
        oper7.Simple_Type = "Ellipse"

        oper8 = self.layout.operator(Simple.bl_idname, text="Arc", icon="PLUGIN")
        oper8.Simple_Change = False
        oper8.Simple_Type = "Arc"

        oper9 = self.layout.operator(Simple.bl_idname, text="Sector", icon="PLUGIN")
        oper9.Simple_Change = False
        oper9.Simple_Type = "Sector"

        oper10 = self.layout.operator(Simple.bl_idname, text="Segment", icon="PLUGIN")
        oper10.Simple_Change = False
        oper10.Simple_Type = "Segment"

        oper11 = self.layout.operator(Simple.bl_idname, text="Rectangle", icon="PLUGIN")
        oper11.Simple_Change = False
        oper11.Simple_Type = "Rectangle"

        oper12 = self.layout.operator(Simple.bl_idname, text="Rhomb", icon="PLUGIN")
        oper12.Simple_Change = False
        oper12.Simple_Type = "Rhomb"

        oper13 = self.layout.operator(Simple.bl_idname, text="Polygon", icon="PLUGIN")
        oper13.Simple_Change = False
        oper13.Simple_Type = "Polygon"

        oper14 = self.layout.operator(Simple.bl_idname, text="Polygon_ab", icon="PLUGIN")
        oper14.Simple_Change = False
        oper14.Simple_Type = "Polygon_ab"

        oper15 = self.layout.operator(Simple.bl_idname, text="Trapezoid", icon="PLUGIN")
        oper15.Simple_Change = False
        oper15.Simple_Type = "Trapezoid"


def Simple_button(self, context):
    oper11 = self.layout.operator(Simple.bl_idname, text="Rectangle", icon="PLUGIN")
    oper11.Simple_Change = False
    oper11.Simple_Type = "Rectangle"

    self.layout.menu("INFO_MT_simple_menu", icon="PLUGIN")


def register():
    bpy.utils.register_class(Simple)
    bpy.utils.register_class(BezierPointsFillet)
    bpy.utils.register_class(BezierDivide)
    bpy.utils.register_class(SimplePanel)
    bpy.utils.register_class(SimpleEdit)
    bpy.utils.register_class(INFO_MT_simple_menu)

    bpy.types.INFO_MT_curve_add.append(Simple_button)

    SimpleVariables()


def unregister():
    bpy.utils.unregister_class(Simple)
    bpy.utils.unregister_class(BezierPointsFillet)
    bpy.utils.unregister_class(BezierDivide)
    bpy.utils.unregister_class(SimplePanel)
    bpy.utils.unregister_class(SimpleEdit)
    bpy.utils.unregister_class(INFO_MT_simple_menu)

    bpy.types.INFO_MT_curve_add.remove(Simple_button)

if __name__ == "__main__":
    register()

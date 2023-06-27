# SPDX-FileCopyrightText: 2010-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""
bl_info = {
    "name": "Curveaceous Galore!",
    "author": "Jimmy Hazevoet, testscreenings",
    "version": (0, 2, 3),
    "blender": (2, 80),
    "location": "View3D > Add > Curve",
    "description": "Adds many different types of Curves",
    "warning": "",
    "doc_url": "{BLENDER_MANUAL_URL}/addons/add_curve/extra_objects.html",
    "category": "Add Curve",
}
"""

import bpy
from bpy_extras import object_utils
from bpy.props import (
        BoolProperty,
        EnumProperty,
        FloatProperty,
        IntProperty,
        FloatVectorProperty
        )
from mathutils import Matrix, Vector
from bpy.types import Operator
from math import (
        sin, cos, pi
        )
import mathutils.noise as Noise


# ------------------------------------------------------------
# Some functions to use with others:
# ------------------------------------------------------------

# ------------------------------------------------------------
# Generate random number:
def randnum(low=0.0, high=1.0, seed=0):
    """
    randnum( low=0.0, high=1.0, seed=0 )

    Create random number
    Parameters:
        low - lower range
            (type=float)
        high - higher range
            (type=float)
        seed - the random seed number, if seed == 0, the current time will be used instead
            (type=int)
    Returns:
        a random number
            (type=float)
    """

    Noise.seed_set(seed)
    rnum = Noise.random()
    rnum = rnum * (high - low)
    rnum = rnum + low
    return rnum


# ------------------------------------------------------------
# Make some noise:
def vTurbNoise(x, y, z, iScale=0.25, Size=1.0, Depth=6, Hard=False, Basis=0, Seed=0):
    """
    vTurbNoise((x,y,z), iScale=0.25, Size=1.0, Depth=6, Hard=0, Basis=0, Seed=0 )

    Create randomised vTurbulence noise

    Parameters:
        xyz - (x,y,z) float values.
            (type=3-float tuple)
        iScale - noise intensity scale
            (type=float)
        Size - noise size
            (type=float)
        Depth - number of noise values added.
            (type=int)
        Hard - noise hardness: True - soft noise; False - hard noise
            (type=int)
        basis - type of noise used for turbulence
            (type=int)
        Seed - the random seed number, if seed == 0, the current time will be used instead
            (type=int)
    Returns:
        the generated turbulence vector.
            (type=3-float list)
    """
    rand = randnum(-100, 100, Seed)
    if Basis == 9:
        Basis = 14
    vec = Vector((x / Size + rand, y / Size + rand, z / Size + rand))
    vTurb = Noise.turbulence_vector(vec, Depth, Hard)
    #mathutils.noise.turbulence_vector(position, octaves, hard, noise_basis='PERLIN_ORIGINAL', amplitude_scale=0.5, frequency_scale=2.0)
    tx = vTurb[0] * iScale
    ty = vTurb[1] * iScale
    tz = vTurb[2] * iScale
    return tx, ty, tz


# -------------------------------------------------------------------
# 2D Curve shape functions:
# -------------------------------------------------------------------

# ------------------------------------------------------------
# 2DCurve: Profile:  L, H, T, U, Z
def ProfileCurve(type=0, a=0.25, b=0.25):
    """
    ProfileCurve( type=0, a=0.25, b=0.25 )

    Create profile curve

    Parameters:
        type - select profile type, L, H, T, U, Z
            (type=int)
        a - a scaling parameter
            (type=float)
        b - b scaling parameter
            (type=float)
    Returns:
        a list with lists of x,y,z coordinates for curve points, [[x,y,z],[x,y,z],...n]
        (type=list)
    """

    newpoints = []
    if type == 1:
        # H:
        a *= 0.5
        b *= 0.5
        newpoints = [
                [-1.0, 1.0, 0.0], [-1.0 + a, 1.0, 0.0],
                [-1.0 + a, b, 0.0], [1.0 - a, b, 0.0], [1.0 - a, 1.0, 0.0],
                [1.0, 1.0, 0.0], [1.0, -1.0, 0.0], [1.0 - a, -1.0, 0.0],
                [1.0 - a, -b, 0.0], [-1.0 + a, -b, 0.0], [-1.0 + a, -1.0, 0.0],
                [-1.0, -1.0, 0.0]
                ]
    elif type == 2:
        # T:
        a *= 0.5
        newpoints = [
                [-1.0, 1.0, 0.0], [1.0, 1.0, 0.0],
                [1.0, 1.0 - b, 0.0], [a, 1.0 - b, 0.0], [a, -1.0, 0.0],
                [-a, -1.0, 0.0], [-a, 1.0 - b, 0.0], [-1.0, 1.0 - b, 0.0]
                ]
    elif type == 3:
        # U:
        a *= 0.5
        newpoints = [
                [-1.0, 1.0, 0.0], [-1.0 + a, 1.0, 0.0],
                [-1.0 + a, -1.0 + b, 0.0], [1.0 - a, -1.0 + b, 0.0], [1.0 - a, 1.0, 0.0],
                [1.0, 1.0, 0.0], [1.0, -1.0, 0.0], [-1.0, -1.0, 0.0]
                ]
    elif type == 4:
        # Z:
        a *= 0.5
        newpoints = [
                [-0.5, 1.0, 0.0], [a, 1.0, 0.0],
                [a, -1.0 + b, 0.0], [1.0, -1.0 + b, 0.0], [1.0, -1.0, 0.0],
                [-a, -1.0, 0.0], [-a, 1.0 - b, 0.0], [-1.0, 1.0 - b, 0.0],
                [-1.0, 1.0, 0.0]
                ]
    else:
        # L:
        newpoints = [
                [-1.0, 1.0, 0.0], [-1.0 + a, 1.0, 0.0],
                [-1.0 + a, -1.0 + b, 0.0], [1.0, -1.0 + b, 0.0],
                [1.0, -1.0, 0.0], [-1.0, -1.0, 0.0]
                ]
    return newpoints


# ------------------------------------------------------------
# 2DCurve: Arrow
def ArrowCurve(type=1, a=1.0, b=0.5):
    """
    ArrowCurve( type=1, a=1.0, b=0.5, c=1.0 )

    Create arrow curve

    Parameters:
        type - select type, Arrow1, Arrow2
            (type=int)
        a - a scaling parameter
            (type=float)
        b - b scaling parameter
            (type=float)
    Returns:
        a list with lists of x,y,z coordinates for curve points, [[x,y,z],[x,y,z],...n]
        (type=list)
    """

    newpoints = []
    if type == 0:
        # Arrow1:
        a *= 0.5
        b *= 0.5
        newpoints = [
                [-1.0, b, 0.0], [-1.0 + a, b, 0.0],
                [-1.0 + a, 1.0, 0.0], [1.0, 0.0, 0.0],
                [-1.0 + a, -1.0, 0.0], [-1.0 + a, -b, 0.0],
                [-1.0, -b, 0.0]
                ]
    elif type == 1:
        # Arrow2:
        newpoints = [[-a, b, 0.0], [a, 0.0, 0.0], [-a, -b, 0.0], [0.0, 0.0, 0.0]]
    else:
        # diamond:
        newpoints = [[0.0, b, 0.0], [a, 0.0, 0.0], [0.0, -b, 0.0], [-a, 0.0, 0.0]]
    return newpoints


# ------------------------------------------------------------
# 2DCurve: Square / Rectangle
def RectCurve(type=1, a=1.0, b=0.5, c=1.0):
    """
    RectCurve( type=1, a=1.0, b=0.5, c=1.0 )

    Create square / rectangle curve

    Parameters:
        type - select type, Square, Rounded square 1, Rounded square 2
            (type=int)
        a - a scaling parameter
            (type=float)
        b - b scaling parameter
            (type=float)
        c - c scaling parameter
            (type=float)
    Returns:
        a list with lists of x,y,z coordinates for curve points, [[x,y,z],[x,y,z],...n]
        (type=list)
    """

    newpoints = []
    if type == 1:
        # Rounded Rectangle:
        newpoints = [
                [-a, b - b * 0.2, 0.0], [-a + a * 0.05, b - b * 0.05, 0.0], [-a + a * 0.2, b, 0.0],
                [a - a * 0.2, b, 0.0], [a - a * 0.05, b - b * 0.05, 0.0], [a, b - b * 0.2, 0.0],
                [a, -b + b * 0.2, 0.0], [a - a * 0.05, -b + b * 0.05, 0.0], [a - a * 0.2, -b, 0.0],
                [-a + a * 0.2, -b, 0.0], [-a + a * 0.05, -b + b * 0.05, 0.0], [-a, -b + b * 0.2, 0.0]
                ]
    elif type == 2:
        # Rounded Rectangle II:
        newpoints = []
        x = a
        y = b
        r = c
        if r > x:
            r = x - 0.0001
        if r > y:
            r = y - 0.0001
        if r > 0:
            newpoints.append([-x + r, y, 0])
            newpoints.append([x - r, y, 0])
            newpoints.append([x, y - r, 0])
            newpoints.append([x, -y + r, 0])
            newpoints.append([x - r, -y, 0])
            newpoints.append([-x + r, -y, 0])
            newpoints.append([-x, -y + r, 0])
            newpoints.append([-x, y - r, 0])
        else:
            newpoints.append([-x, y, 0])
            newpoints.append([x, y, 0])
            newpoints.append([x, -y, 0])
            newpoints.append([-x, -y, 0])
    else:
        # Rectangle:
        newpoints = [[-a, b, 0.0], [a, b, 0.0], [a, -b, 0.0], [-a, -b, 0.0]]
    return newpoints


# ------------------------------------------------------------
# 2DCurve: Star:
def StarCurve(starpoints=8, innerradius=0.5, outerradius=1.0, twist=0.0):
    """
    StarCurve( starpoints=8, innerradius=0.5, outerradius=1.0, twist=0.0 )

    Create star shaped curve

    Parameters:
        starpoints - the number of points
            (type=int)
        innerradius - innerradius
            (type=float)
        outerradius - outerradius
            (type=float)
        twist - twist amount
            (type=float)
    Returns:
        a list with lists of x,y,z coordinates for curve points, [[x,y,z],[x,y,z],...n]
        (type=list)
    """

    newpoints = []
    step = 2.0 / starpoints
    i = 0
    while i < starpoints:
        t = i * step
        x1 = cos(t * pi) * outerradius
        y1 = sin(t * pi) * outerradius
        newpoints.append([x1, y1, 0])
        x2 = cos(t * pi + (pi / starpoints + twist)) * innerradius
        y2 = sin(t * pi + (pi / starpoints + twist)) * innerradius
        newpoints.append([x2, y2, 0])
        i += 1
    return newpoints


# ------------------------------------------------------------
# 2DCurve: Flower:
def FlowerCurve(petals=8, innerradius=0.5, outerradius=1.0, petalwidth=2.0):
    """
    FlowerCurve( petals=8, innerradius=0.5, outerradius=1.0, petalwidth=2.0 )

    Create flower shaped curve

    Parameters:
        petals - the number of petals
            (type=int)
        innerradius - innerradius
            (type=float)
        outerradius - outerradius
            (type=float)
        petalwidth - width of petals
            (type=float)
    Returns:
        a list with lists of x,y,z coordinates for curve points, [[x,y,z],[x,y,z],...n]
        (type=list)
    """

    newpoints = []
    step = 2.0 / petals
    pet = (step / pi * 2) * petalwidth
    i = 0
    while i < petals:
        t = i * step
        x1 = cos(t * pi - (pi / petals)) * innerradius
        y1 = sin(t * pi - (pi / petals)) * innerradius
        newpoints.append([x1, y1, 0])
        x2 = cos(t * pi - pet) * outerradius
        y2 = sin(t * pi - pet) * outerradius
        newpoints.append([x2, y2, 0])
        x3 = cos(t * pi + pet) * outerradius
        y3 = sin(t * pi + pet) * outerradius
        newpoints.append([x3, y3, 0])
        i += 1
    return newpoints


# ------------------------------------------------------------
# 2DCurve: Arc,Sector,Segment,Ring:
def ArcCurve(sides=6, startangle=0.0, endangle=90.0, innerradius=0.5, outerradius=1.0, type=3):
    """
    ArcCurve( sides=6, startangle=0.0, endangle=90.0, innerradius=0.5, outerradius=1.0, type=3 )

    Create arc shaped curve

    Parameters:
        sides - number of sides
            (type=int)
        startangle - startangle
            (type=float)
        endangle - endangle
            (type=float)
        innerradius - innerradius
            (type=float)
        outerradius - outerradius
            (type=float)
        type - select type Arc,Sector,Segment,Ring
            (type=int)
    Returns:
        a list with lists of x,y,z coordinates for curve points, [[x,y,z],[x,y,z],...n]
        (type=list)
    """

    newpoints = []
    sides += 1
    angle = 2.0 * (1.0 / 360.0)
    endangle -= startangle
    step = (angle * endangle) / (sides - 1)
    i = 0
    while i < sides:
        t = (i * step) + angle * startangle
        x1 = sin(t * pi) * outerradius
        y1 = cos(t * pi) * outerradius
        newpoints.append([x1, y1, 0])
        i += 1

    # if type == 1:
        # Arc: turn cyclic curve flag off!

    # Segment:
    if type == 2:
        newpoints.append([0, 0, 0])
    # Ring:
    elif type == 3:
        j = sides - 1
        while j > -1:
            t = (j * step) + angle * startangle
            x2 = sin(t * pi) * innerradius
            y2 = cos(t * pi) * innerradius
            newpoints.append([x2, y2, 0])
            j -= 1
    return newpoints


# ------------------------------------------------------------
# 2DCurve: Cog wheel:
def CogCurve(theeth=8, innerradius=0.8, middleradius=0.95, outerradius=1.0, bevel=0.5):
    """
    CogCurve( theeth=8, innerradius=0.8, middleradius=0.95, outerradius=1.0, bevel=0.5 )

    Create cog wheel shaped curve

    Parameters:
        theeth - number of theeth
            (type=int)
        innerradius - innerradius
            (type=float)
        middleradius - middleradius
            (type=float)
        outerradius - outerradius
            (type=float)
        bevel - bevel amount
            (type=float)
    Returns:
        a list with lists of x,y,z coordinates for curve points, [[x,y,z],[x,y,z],...n]
        (type=list)
    """

    newpoints = []
    step = 2.0 / theeth
    pet = step / pi * 2
    bevel = 1.0 - bevel
    i = 0
    while i < theeth:
        t = i * step
        x1 = cos(t * pi - (pi / theeth) - pet) * innerradius
        y1 = sin(t * pi - (pi / theeth) - pet) * innerradius
        newpoints.append([x1, y1, 0])
        x2 = cos(t * pi - (pi / theeth) + pet) * innerradius
        y2 = sin(t * pi - (pi / theeth) + pet) * innerradius
        newpoints.append([x2, y2, 0])
        x3 = cos(t * pi - pet) * middleradius
        y3 = sin(t * pi - pet) * middleradius
        newpoints.append([x3, y3, 0])
        x4 = cos(t * pi - (pet * bevel)) * outerradius
        y4 = sin(t * pi - (pet * bevel)) * outerradius
        newpoints.append([x4, y4, 0])
        x5 = cos(t * pi + (pet * bevel)) * outerradius
        y5 = sin(t * pi + (pet * bevel)) * outerradius
        newpoints.append([x5, y5, 0])
        x6 = cos(t * pi + pet) * middleradius
        y6 = sin(t * pi + pet) * middleradius
        newpoints.append([x6, y6, 0])
        i += 1
    return newpoints


# ------------------------------------------------------------
# 2DCurve: nSide:
def nSideCurve(sides=6, radius=1.0):
    """
    nSideCurve( sides=6, radius=1.0 )

    Create n-sided curve

        Parameters:
            sides - number of sides
                (type=int)
            radius - radius
                (type=float)
        Returns:
            a list with lists of x,y,z coordinates for curve points, [[x,y,z],[x,y,z],...n]
            (type=list)
    """

    newpoints = []
    step = 2.0 / sides
    i = 0
    while i < sides:
        t = i * step
        x = sin(t * pi) * radius
        y = cos(t * pi) * radius
        newpoints.append([x, y, 0])
        i += 1
    return newpoints


# ------------------------------------------------------------
# 2DCurve: Splat:
def SplatCurve(sides=24, scale=1.0, seed=0, basis=0, radius=1.0):
    """
    SplatCurve( sides=24, scale=1.0, seed=0, basis=0, radius=1.0 )

    Create splat curve

    Parameters:
        sides - number of sides
            (type=int)
        scale - noise size
            (type=float)
        seed - noise random seed
            (type=int)
        basis - noise basis
            (type=int)
        radius - radius
            (type=float)
    Returns:
        a list with lists of x,y,z coordinates for curve points, [[x,y,z],[x,y,z],...n]
        (type=list)
    """

    newpoints = []
    step = 2.0 / sides
    i = 0
    while i < sides:
        t = i * step
        turb = vTurbNoise(t, t, t, 1.0, scale, 6, False, basis, seed)
        turb = turb[2] * 0.5 + 0.5
        x = sin(t * pi) * radius * turb
        y = cos(t * pi) * radius * turb
        newpoints.append([x, y, 0])
        i += 1
    return newpoints


# -----------------------------------------------------------
# Cycloid curve
def CycloidCurve(number=100, type=0, R=4.0, r=1.0, d=1.0):
    """
    CycloidCurve( number=100, type=0, a=4.0, b=1.0 )

    Create a Cycloid, Hypotrochoid / Hypocycloid or Epitrochoid / Epycycloid type of curve

    Parameters:
        number - the number of points
            (type=int)
        type - types: Cycloid, Hypocycloid, Epicycloid
            (type=int)
        R = Radius a scaling parameter
            (type=float)
        r = Radius b scaling parameter
            (type=float)
        d = Distance scaling parameter
            (type=float)
    Returns:
        a list with lists of x,y,z coordinates for curve points, [[x,y,z],[x,y,z],...n]
        (type=list)
    """

    a = R
    b = r
    newpoints = []
    step = 2.0 / (number - 1)
    i = 0
    if type == 1:
        # Hypotrochoid / Hypocycloid
        while i < number:
            t = i * step
            x = ((a - b) * cos(t * pi)) + (d * cos(((a + b) / b) * t * pi))
            y = ((a - b) * sin(t * pi)) - (d * sin(((a + b) / b) * t * pi))
            z = 0
            newpoints.append([x, y, z])
            i += 1
    elif type == 2:
        # Epitrochoid / Epycycloid
        while i < number:
            t = i * step
            x = ((a + b) * cos(t * pi)) - (d * cos(((a + b) / b) * t * pi))
            y = ((a + b) * sin(t * pi)) - (d * sin(((a + b) / b) * t * pi))
            z = 0
            newpoints.append([x, y, z])
            i += 1
    else:
        # Cycloid
        while i < number:
            t = (i * step * pi)
            x = (t - sin(t) * b) * a / pi
            y = (1 - cos(t) * b) * a / pi
            z = 0
            newpoints.append([x, y, z])
            i += 1
    return newpoints


# -----------------------------------------------------------
# 3D curve shape functions:
# -----------------------------------------------------------

# ------------------------------------------------------------
# 3DCurve: Helix:
def HelixCurve(number=100, height=2.0, startangle=0.0, endangle=360.0, width=1.0, a=0.0, b=0.0):
    """
    HelixCurve( number=100, height=2.0, startangle=0.0, endangle=360.0, width=1.0, a=0.0, b=0.0 )

    Create helix curve

    Parameters:
        number - the number of points
            (type=int)
        height - height
            (type=float)
        startangle - startangle
            (type=float)
        endangle - endangle
            (type=float)
        width - width
            (type=float)
        a - a
            (type=float)
        b - b
            (type=float)
    Returns:
        a list with lists of x,y,z coordinates for curve points, [[x,y,z],[x,y,z],...n]
        (type=list)
    """

    newpoints = []
    angle = (2.0 / 360.0) * (endangle - startangle)
    step = angle / (number - 1)
    h = height / angle
    start = startangle * 2.0 / 360.0
    a /= angle
    i = 0
    while i < number:
        t = (i * step + start)
        x = sin((t * pi)) * (1.0 + cos(t * pi * a - (b * pi))) * (0.25 * width)
        y = cos((t * pi)) * (1.0 + cos(t * pi * a - (b * pi))) * (0.25 * width)
        z = (t * h) - h * start
        newpoints.append([x, y, z])
        i += 1
    return newpoints


# -----------------------------------------------------------
# 3D Noise curve
def NoiseCurve(type=0, number=100, length=2.0, size=0.5,
               scale=[0.5, 0.5, 0.5], octaves=2, basis=0, seed=0):
    """
    Create noise curve

    Parameters:
        number - number of points
            (type=int)
        length - curve length
            (type=float)
        size - noise size
            (type=float)
        scale - noise intensity scale x,y,z
            (type=list)
        basis - noise basis
            (type=int)
        seed - noise random seed
            (type=int)
        type - noise curve type
            (type=int)
    Returns:
        a list with lists of x,y,z coordinates for curve points, [[x,y,z],[x,y,z],...n]
        (type=list)
    """

    newpoints = []
    step = (length / number)
    i = 0
    if type == 1:
        # noise circle
        while i < number:
            t = i * step
            v = vTurbNoise(t, t, t, 1.0, size, octaves, False, basis, seed)
            x = sin(t * pi) + (v[0] * scale[0])
            y = cos(t * pi) + (v[1] * scale[1])
            z = v[2] * scale[2]
            newpoints.append([x, y, z])
            i += 1
    elif type == 2:
        # noise knot / ball
        while i < number:
            t = i * step
            v = vTurbNoise(t, t, t, 1.0, 1.0, octaves, False, basis, seed)
            x = v[0] * scale[0] * size
            y = v[1] * scale[1] * size
            z = v[2] * scale[2] * size
            newpoints.append([x, y, z])
            i += 1
    else:
        # noise linear
        while i < number:
            t = i * step
            v = vTurbNoise(t, t, t, 1.0, size, octaves, False, basis, seed)
            x = t + v[0] * scale[0]
            y = v[1] * scale[1]
            z = v[2] * scale[2]
            newpoints.append([x, y, z])
            i += 1
    return newpoints


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


# create new CurveObject from vertarray and splineType
def createCurve(context, vertArray, self):
    # output splineType 'POLY' 'NURBS' 'BEZIER'
    splineType = self.outputType

    # GalloreType as name
    name = self.ProfileType

    # create object
    if bpy.context.mode == 'EDIT_CURVE':
        Curve = context.active_object
        newSpline = Curve.data.splines.new(type=splineType)          # spline
    else:
        # create curve
        dataCurve = bpy.data.curves.new(name, type='CURVE')  # curve data block
        newSpline = dataCurve.splines.new(type=splineType)          # spline

        # create object with newCurve
        Curve = object_utils.object_data_add(context, dataCurve, operator=self)  # place in active scene

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
    if splineType == 'BEZIER':
        newSpline.bezier_points.add(int(len(vertArray) * 0.33))
        newSpline.bezier_points.foreach_set('co', vertArray)
        for point in newSpline.bezier_points:
            point.handle_right_type = self.handleType
            point.handle_left_type = self.handleType
            point.select_control_point = True
            point.select_left_handle = True
            point.select_right_handle = True
    else:
        newSpline.points.add(int(len(vertArray) * 0.25 - 1))
        newSpline.points.foreach_set('co', vertArray)
        newSpline.use_endpoint_u = True
        for point in newSpline.points:
            point.select = True

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

    return


# ------------------------------------------------------------
# Main Function
def main(context, self):
    # options
    proType = self.ProfileType
    splineType = self.outputType
    innerRadius = self.innerRadius
    middleRadius = self.middleRadius
    outerRadius = self.outerRadius

    # get verts
    if proType == 'Profile':
        verts = ProfileCurve(
                self.ProfileCurveType,
                self.ProfileCurvevar1,
                self.ProfileCurvevar2
                )
    if proType == 'Arrow':
        verts = ArrowCurve(
                self.MiscCurveType,
                self.MiscCurvevar1,
                self.MiscCurvevar2
                )
    if proType == 'Rectangle':
        verts = RectCurve(
                self.MiscCurveType,
                self.MiscCurvevar1,
                self.MiscCurvevar2,
                self.MiscCurvevar3
                )
    if proType == 'Flower':
        verts = FlowerCurve(
                self.petals,
                innerRadius,
                outerRadius,
                self.petalWidth
                )
    if proType == 'Star':
        verts = StarCurve(
                self.starPoints,
                innerRadius,
                outerRadius,
                self.starTwist
                )
    if proType == 'Arc':
        verts = ArcCurve(
                self.arcSides,
                self.startAngle,
                self.endAngle,
                innerRadius,
                outerRadius,
                self.arcType
                )
    if proType == 'Cogwheel':
        verts = CogCurve(
                self.teeth,
                innerRadius,
                middleRadius,
                outerRadius,
                self.bevel
                )
    if proType == 'Nsided':
        verts = nSideCurve(
                self.Nsides,
                outerRadius
                )
    if proType == 'Splat':
        verts = SplatCurve(
                self.splatSides,
                self.splatScale,
                self.seed,
                self.basis,
                outerRadius
                )
    if proType == 'Cycloid':
        verts = CycloidCurve(
                self.cycloPoints,
                self.cycloType,
                self.cyclo_a,
                self.cyclo_b,
                self.cyclo_d
                )
    if proType == 'Helix':
        verts = HelixCurve(
                self.helixPoints,
                self.helixHeight,
                self.helixStart,
                self.helixEnd,
                self.helixWidth,
                self.helix_a,
                self.helix_b
                )
    if proType == 'Noise':
        verts = NoiseCurve(
                self.noiseType,
                self.noisePoints,
                self.noiseLength,
                self.noiseSize,
                [self.noiseScaleX, self.noiseScaleY, self.noiseScaleZ],
                self.noiseOctaves,
                self.noiseBasis,
                self.noiseSeed
                )

    # turn verts into array
    vertArray = vertsToPoints(verts, splineType)

    # create object
    createCurve(context, vertArray, self)

    return


class Curveaceous_galore(Operator, object_utils.AddObjectHelper):
    bl_idname = "curve.curveaceous_galore"
    bl_label = "Curve Profiles"
    bl_description = "Construct many types of curves"
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}

    # general properties
    ProfileType : EnumProperty(
            name="Type",
            description="Form of Curve to create",
            items=[
            ('Arc', "Arc", "Arc"),
            ('Arrow', "Arrow", "Arrow"),
            ('Cogwheel', "Cogwheel", "Cogwheel"),
            ('Cycloid', "Cycloid", "Cycloid"),
            ('Flower', "Flower", "Flower"),
            ('Helix', "Helix (3D)", "Helix"),
            ('Noise', "Noise (3D)", "Noise"),
            ('Nsided', "Nsided", "Nsided"),
            ('Profile', "Profile", "Profile"),
            ('Rectangle', "Rectangle", "Rectangle"),
            ('Splat', "Splat", "Splat"),
            ('Star', "Star", "Star")]
            )
    outputType : EnumProperty(
            name="Output splines",
            description="Type of splines to output",
            items=[
            ('POLY', "Poly", "Poly Spline type"),
            ('NURBS', "Nurbs", "Nurbs Spline type"),
            ('BEZIER', "Bezier", "Bezier Spline type")]
            )
    # Curve Options
    shape : EnumProperty(
            name="2D / 3D",
            description="2D or 3D Curve",
            items=[
            ('2D', "2D", "2D"),
            ('3D', "3D", "3D")
            ]
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
            default='AUTO',
            description="Bezier handles type",
            items=[
            ('VECTOR', "Vector", "Vector type Bezier handles"),
            ('AUTO', "Auto", "Automatic type Bezier handles")]
            )
    # ProfileCurve properties
    ProfileCurveType : IntProperty(
            name="Type",
            min=1,
            max=5,
            default=1,
            description="Type of Curve's Profile"
            )
    ProfileCurvevar1 : FloatProperty(
            name="Variable 1",
            default=0.25,
            description="Variable 1 of Curve's Profile"
            )
    ProfileCurvevar2 : FloatProperty(
            name="Variable 2",
            default=0.25,
            description="Variable 2 of Curve's Profile"
            )
    # Arrow, Rectangle, MiscCurve properties
    MiscCurveType : IntProperty(
            name="Type",
            min=0,
            max=3,
            default=0,
            description="Type of Curve"
            )
    MiscCurvevar1 : FloatProperty(
            name="Variable 1",
            default=1.0,
            description="Variable 1 of Curve"
            )
    MiscCurvevar2 : FloatProperty(
            name="Variable 2",
            default=0.5,
            description="Variable 2 of Curve"
            )
    MiscCurvevar3 : FloatProperty(
            name="Variable 3",
            default=0.1,
            min=0,
            description="Variable 3 of Curve"
            )
    # Common properties
    innerRadius : FloatProperty(
            name="Inner radius",
            default=0.5,
            min=0,
            description="Inner radius"
            )
    middleRadius : FloatProperty(
            name="Middle radius",
            default=0.95,
            min=0,
            description="Middle radius"
            )
    outerRadius : FloatProperty(
            name="Outer radius",
            default=1.0,
            min=0,
            description="Outer radius"
            )
    # Flower properties
    petals : IntProperty(
            name="Petals",
            default=8,
            min=2,
            description="Number of petals"
            )
    petalWidth : FloatProperty(
            name="Petal width",
            default=2.0,
            min=0.01,
            description="Petal width"
            )
    # Star properties
    starPoints : IntProperty(
            name="Star points",
            default=8,
            min=2,
            description="Number of star points"
            )
    starTwist : FloatProperty(
            name="Twist",
            default=0.0,
            description="Twist"
            )
    # Arc properties
    arcSides : IntProperty(
            name="Arc sides",
            default=6,
            min=1,
            description="Sides of arc"
            )
    startAngle : FloatProperty(
            name="Start angle",
            default=0.0,
            description="Start angle"
            )
    endAngle : FloatProperty(
            name="End angle",
            default=90.0,
            description="End angle"
            )
    arcType : IntProperty(
            name="Arc type",
            default=3,
            min=1,
            max=3,
            description="Sides of arc"
            )
    # Cogwheel properties
    teeth : IntProperty(
            name="Teeth",
            default=8,
            min=2,
            description="number of teeth"
            )
    bevel : FloatProperty(
            name="Bevel",
            default=0.5,
            min=0,
            max=1,
            description="Bevel"
            )
    # Nsided property
    Nsides : IntProperty(
            name="Sides",
            default=8,
            min=3,
            description="Number of sides"
            )
    # Splat properties
    splatSides : IntProperty(
            name="Splat sides",
            default=24,
            min=3,
            description="Splat sides"
            )
    splatScale : FloatProperty(
            name="Splat scale",
            default=1.0,
            min=0.0001,
            description="Splat scale"
            )
    seed : IntProperty(
            name="Seed",
            default=0,
            min=0,
            description="Seed"
            )
    basis : IntProperty(
            name="Basis",
            default=0,
            min=0,
            max=14,
            description="Basis"
            )
    # Helix properties
    helixPoints : IntProperty(
            name="Resolution",
            default=100,
            min=3,
            description="Resolution"
            )
    helixHeight : FloatProperty(
            name="Height",
            default=2.0,
            min=0,
            description="Helix height"
            )
    helixStart : FloatProperty(
            name="Start angle",
            default=0.0,
            description="Helix start angle"
            )
    helixEnd : FloatProperty(
            name="Endangle",
            default=360.0,
            description="Helix end angle"
            )
    helixWidth : FloatProperty(
            name="Width",
            default=1.0,
            description="Helix width"
            )
    helix_a : FloatProperty(
            name="Variable 1",
            default=0.0,
            description="Helix Variable 1"
            )
    helix_b : FloatProperty(
            name="Variable 2",
            default=0.0,
            description="Helix Variable 2"
            )
    # Cycloid properties
    cycloPoints : IntProperty(
            name="Resolution",
            default=100,
            min=3,
            soft_min=3,
            description="Resolution"
            )
    cycloType : IntProperty(
            name="Type",
            default=1,
            min=0,
            max=2,
            description="Type: Cycloid , Hypocycloid / Hypotrochoid , Epicycloid / Epitrochoid"
            )
    cyclo_a : FloatProperty(
            name="R",
            default=1.0,
            min=0.01,
            description="Cycloid: R radius a"
            )
    cyclo_b : FloatProperty(
            name="r",
            default=0.25,
            min=0.01,
            description="Cycloid: r radius b"
            )
    cyclo_d : FloatProperty(
            name="d",
            default=0.25,
            description="Cycloid: d distance"
            )
    # Noise properties
    noiseType : IntProperty(
            name="Type",
            default=0,
            min=0,
            max=2,
            description="Noise curve type: Linear, Circular or Knot"
            )
    noisePoints : IntProperty(
            name="Resolution",
            default=100,
            min=3,
            description="Resolution"
            )
    noiseLength : FloatProperty(
            name="Length",
            default=2.0,
            min=0.01,
            description="Curve Length"
            )
    noiseSize : FloatProperty(
            name="Noise size",
            default=1.0,
            min=0.0001,
            description="Noise size"
            )
    noiseScaleX : FloatProperty(
            name="Noise x",
            default=1.0,
            min=0.0001,
            description="Noise x"
            )
    noiseScaleY : FloatProperty(
            name="Noise y",
            default=1.0,
            min=0.0001,
            description="Noise y"
            )
    noiseScaleZ : FloatProperty(
            name="Noise z",
            default=1.0,
            min=0.0001,
            description="Noise z"
            )
    noiseOctaves : IntProperty(
            name="Octaves",
            default=2,
            min=1,
            max=16,
            description="Basis"
            )
    noiseBasis : IntProperty(
            name="Basis",
            default=0,
            min=0,
            max=9,
            description="Basis"
            )
    noiseSeed : IntProperty(
            name="Seed",
            default=1,
            min=0,
            description="Random Seed"
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
        col.prop(self, 'ProfileType')
        col.label(text=self.ProfileType + " Options:")

        # options per ProfileType
        box = layout.box()
        col = box.column(align=True)

        if self.ProfileType == 'Profile':
            col.prop(self, "ProfileCurveType")
            col.prop(self, "ProfileCurvevar1")
            col.prop(self, "ProfileCurvevar2")

        elif self.ProfileType == 'Arrow':
            col.prop(self, "MiscCurveType")
            col.prop(self, "MiscCurvevar1", text="Height")
            col.prop(self, "MiscCurvevar2", text="Width")

        elif self.ProfileType == 'Rectangle':
            col.prop(self, "MiscCurveType")
            col.prop(self, "MiscCurvevar1", text="Width")
            col.prop(self, "MiscCurvevar2", text="Height")
            if self.MiscCurveType == 2:
                col.prop(self, "MiscCurvevar3", text="Corners")

        elif self.ProfileType == 'Flower':
            col.prop(self, "petals")
            col.prop(self, "petalWidth")

            col = box.column(align=True)
            col.prop(self, "innerRadius")
            col.prop(self, "outerRadius")

        elif self.ProfileType == 'Star':
            col.prop(self, "starPoints")
            col.prop(self, "starTwist")

            col = box.column(align=True)
            col.prop(self, "innerRadius")
            col.prop(self, "outerRadius")

        elif self.ProfileType == 'Arc':
            col.prop(self, "arcType")
            col.prop(self, "arcSides")

            col = box.column(align=True)
            col.prop(self, "startAngle")
            col.prop(self, "endAngle")

            col = box.column(align=True)
            col.prop(self, "innerRadius")
            col.prop(self, "outerRadius")

        elif self.ProfileType == 'Cogwheel':
            col.prop(self, "teeth")
            col.prop(self, "bevel")

            col = box.column(align=True)
            col.prop(self, "innerRadius")
            col.prop(self, "middleRadius")
            col.prop(self, "outerRadius")

        elif self.ProfileType == 'Nsided':
            col.prop(self, "Nsides")
            col.prop(self, "outerRadius")

        elif self.ProfileType == 'Splat':
            col.prop(self, "splatSides")
            col.prop(self, "outerRadius")

            col = box.column(align=True)
            col.prop(self, "splatScale")
            col.prop(self, "seed")
            col.prop(self, "basis")

        elif self.ProfileType == 'Cycloid':
            col.prop(self, "cycloType")
            col.prop(self, "cycloPoints")

            col = box.column(align=True)
            col.prop(self, "cyclo_a")
            col.prop(self, "cyclo_b")
            if self.cycloType != 0:
                col.prop(self, "cyclo_d")

        elif self.ProfileType == 'Helix':
            col.prop(self, "helixPoints")
            col.prop(self, "helixHeight")
            col.prop(self, "helixWidth")

            col = box.column(align=True)
            col.prop(self, "helixStart")
            col.prop(self, "helixEnd")

            col = box.column(align=True)
            col.prop(self, "helix_a")
            col.prop(self, "helix_b")

        elif self.ProfileType == 'Noise':
            col.prop(self, "noiseType")
            col.prop(self, "noisePoints")
            col.prop(self, "noiseLength")

            col = box.column(align=True)
            col.prop(self, "noiseSize")
            col.prop(self, "noiseScaleX")
            col.prop(self, "noiseScaleY")
            col.prop(self, "noiseScaleZ")

            col = box.column(align=True)
            col.prop(self, "noiseOctaves")
            col.prop(self, "noiseBasis")
            col.prop(self, "noiseSeed")

        row = layout.row()
        row.prop(self, "shape", expand=True)

        # output options
        col = layout.column()
        col.label(text="Output Curve Type:")
        col.row().prop(self, "outputType", expand=True)

        if self.outputType == 'NURBS':
            col.prop(self, 'order_u')
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

    @classmethod
    def poll(cls, context):
        return context.scene is not None

    def execute(self, context):
        # turn off 'Enter Edit Mode'
        use_enter_edit_mode = bpy.context.preferences.edit.use_enter_edit_mode
        bpy.context.preferences.edit.use_enter_edit_mode = False

        # main function
        main(context, self)

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
        # deal with 2D - 3D curve differences
        if self.ProfileType in ['Helix', 'Cycloid', 'Noise']:
            self.shape = '3D'
        else:
            self.shape = '2D'

        if self.ProfileType in ['Helix', 'Noise', 'Cycloid']:
            self.use_cyclic_u = False
            if self.ProfileType in ['Cycloid']:
                if self.cycloType == 0:
                    self.use_cyclic_u = False
                else:
                    self.use_cyclic_u = True
        else:
            if self.ProfileType == 'Arc' and self.arcType == 1:
                self.use_cyclic_u = False
            else:
                self.use_cyclic_u = True

        self.execute(context)

        return {'FINISHED'}

# Register
classes = [
    Curveaceous_galore
]

def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)

if __name__ == "__main__":
    register()

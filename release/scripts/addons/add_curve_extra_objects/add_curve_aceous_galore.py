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
'''
bl_info = {
    "name": "Curveaceous Galore!",
    "author": "Jimmy Hazevoet, testscreenings",
    "version": (0, 2),
    "blender": (2, 59, 0),
    "location": "View3D > Add > Curve",
    "description": "Adds many different types of Curves",
    "warning": "", # used for warning icon and text in addons panel
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/"
                "Scripts/Curve/Curves_Galore",
    "category": "Add Curve",
}
'''


# ------------------------------------------------------------
#    import modules
import bpy
from bpy.props import (
        BoolProperty,
        EnumProperty,
        FloatProperty,
        IntProperty,
        )
from mathutils import (
        Matrix,
        Vector,
        )
from math import (
        sin,
        cos,
        pi
        )
import mathutils.noise as Noise
from bpy.types import Operator
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
            seed - the random seed number, if seed is 0, the current time will be used instead
                (type=int)
        Returns:
            a random number
                (type=float)
    """

    Noise.seed_set(seed)
    rnum = Noise.random()
    rnum = rnum*(high-low)
    rnum = rnum+low
    return rnum


# ------------------------------------------------------------
# Make some noise:
def vTurbNoise(x, y, z, iScale=0.25, Size=1.0, Depth=6, Hard=0, Basis=0, Seed=0):
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
            Hard - noise hardness: 0 - soft noise; 1 - hard noise
                (type=int)
            basis - type of noise used for turbulence
                (type=int)
            Seed - the random seed number, if seed is 0, the current time will be used instead
                (type=int)
        Returns:
            the generated turbulence vector.
                (type=3-float list)
    """
    rand = randnum(-100, 100, Seed)
    if Basis == 9:
        Basis = 14
    vTurb = Noise.turbulence_vector((x/Size+rand, y/Size+rand, z/Size+rand), Depth, Hard, Basis)
    tx = vTurb[0]*iScale
    ty = vTurb[1]*iScale
    tz = vTurb[2]*iScale
    return tx, ty, tz


#------------------------------------------------------------
# Axis: ( used in 3DCurve Turbulence )
def AxisFlip(x, y, z, x_axis=1, y_axis=1, z_axis=1, flip=0):
    if flip != 0:
        flip *= -1
    else:
        flip = 1
    x *= x_axis*flip
    y *= y_axis*flip
    z *= z_axis*flip
    return x, y, z


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
        newpoints = [[-1.0, 1.0, 0.0], [-1.0+a, 1.0, 0.0],
        [-1.0+a, b, 0.0], [1.0-a, b, 0.0], [1.0-a, 1.0, 0.0],
            [1.0, 1.0, 0.0], [1.0, -1.0, 0.0], [1.0-a, -1.0, 0.0],
            [1.0-a, -b, 0.0], [-1.0+a, -b, 0.0], [-1.0+a, -1.0, 0.0],
            [-1.0, -1.0, 0.0]]
    elif type == 2:
        # T:
        a *= 0.5
        newpoints = [[-1.0, 1.0, 0.0], [1.0, 1.0, 0.0],
        [1.0, 1.0-b, 0.0], [a, 1.0-b, 0.0], [a, -1.0, 0.0],
            [-a, -1.0, 0.0], [-a, 1.0-b, 0.0], [-1.0, 1.0-b, 0.0]]
    elif type == 3:
        # U:
        a *= 0.5
        newpoints = [[-1.0, 1.0, 0.0], [-1.0+a, 1.0, 0.0],
        [-1.0+a, -1.0+b, 0.0], [1.0-a, -1.0+b, 0.0], [1.0-a, 1.0, 0.0],
            [1.0, 1.0, 0.0], [1.0, -1.0, 0.0], [-1.0, -1.0, 0.0]]
    elif type == 4:
        # Z:
        a *= 0.5
        newpoints = [[-0.5, 1.0, 0.0], [a, 1.0, 0.0],
        [a, -1.0+b, 0.0], [1.0, -1.0+b, 0.0], [1.0, -1.0, 0.0],
            [-a, -1.0, 0.0], [-a, 1.0-b, 0.0], [-1.0, 1.0-b, 0.0],
            [-1.0, 1.0, 0.0]]
    else:
        # L:
        newpoints = [[-1.0, 1.0, 0.0], [-1.0+a, 1.0, 0.0],
        [-1.0+a, -1.0+b, 0.0], [1.0, -1.0+b, 0.0],
            [1.0, -1.0, 0.0], [-1.0, -1.0, 0.0]]
    return newpoints

# ------------------------------------------------------------
# 2DCurve: Miscellaneous.: Diamond, Arrow1, Arrow2, Square, ....
def MiscCurve(type=1, a=1.0, b=0.5, c=1.0):
    """
    MiscCurve( type=1, a=1.0, b=0.5, c=1.0 )

    Create miscellaneous curves

        Parameters:
            type - select type, Diamond, Arrow1, Arrow2, Square
                (type=int)
            a - a scaling parameter
                (type=float)
            b - b scaling parameter
                (type=float)
            c - c scaling parameter
                (type=float)
                doesn't seem to do anything
        Returns:
            a list with lists of x,y,z coordinates for curve points, [[x,y,z],[x,y,z],...n]
            (type=list)
    """

    newpoints = []
    a *= 0.5
    b *= 0.5
    if type == 1:
        # diamond:
        newpoints = [[0.0, b, 0.0], [a, 0.0, 0.0], [0.0, -b, 0.0], [-a, 0.0, 0.0]]
    elif type == 2:
        # Arrow1:
        newpoints = [[-a, b, 0.0], [a, 0.0, 0.0], [-a, -b, 0.0], [0.0, 0.0, 0.0]]
    elif type == 3:
        # Arrow2:
        newpoints = [[-1.0, b, 0.0], [-1.0+a, b, 0.0],
        [-1.0+a, 1.0, 0.0], [1.0, 0.0, 0.0],
            [-1.0+a, -1.0, 0.0], [-1.0+a, -b, 0.0],
            [-1.0, -b, 0.0]]
    elif type == 4:
        # Rounded square:
        newpoints = [[-a, b-b*0.2, 0.0], [-a+a*0.05, b-b*0.05, 0.0], [-a+a*0.2, b, 0.0],
        [a-a*0.2, b, 0.0], [a-a*0.05, b-b*0.05, 0.0], [a, b-b*0.2, 0.0],
            [a, -b+b*0.2, 0.0], [a-a*0.05, -b+b*0.05, 0.0], [a-a*0.2, -b, 0.0],
            [-a+a*0.2, -b, 0.0], [-a+a*0.05, -b+b*0.05, 0.0], [-a, -b+b*0.2, 0.0]]
    elif type == 5:
        # Rounded Rectangle II:
        newpoints = []
        x = a / 2
        y = b / 2
        r = c / 2

        if r > x:
            r = x - 0.0001
        if r > y:
            r = y - 0.0001

        if r > 0:
            newpoints.append([-x+r, y, 0])
            newpoints.append([x-r, y, 0])
            newpoints.append([x, y-r, 0])
            newpoints.append([x, -y+r, 0])
            newpoints.append([x-r, -y, 0])
            newpoints.append([-x+r, -y, 0])
            newpoints.append([-x, -y+r, 0])
            newpoints.append([-x, y-r, 0])
        else:
            newpoints.append([-x, y, 0])
            newpoints.append([x, y, 0])
            newpoints.append([x, -y, 0])
            newpoints.append([-x, -y, 0])

    else:
        # Square:
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
    step = (2.0/(starpoints))
    i = 0
    while i < starpoints:
        t = (i*step)
        x1 = cos(t*pi)*outerradius
        y1 = sin(t*pi)*outerradius
        newpoints.append([x1, y1, 0])
        x2 = cos(t*pi+(pi/starpoints+twist))*innerradius
        y2 = sin(t*pi+(pi/starpoints+twist))*innerradius
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
    step = (2.0/(petals))
    pet = (step/pi*2)*petalwidth
    i = 0
    while i < petals:
        t = (i*step)
        x1 = cos(t*pi-(pi/petals))*innerradius
        y1 = sin(t*pi-(pi/petals))*innerradius
        newpoints.append([x1, y1, 0])
        x2 = cos(t*pi-pet)*outerradius
        y2 = sin(t*pi-pet)*outerradius
        newpoints.append([x2, y2, 0])
        x3 = cos(t*pi+pet)*outerradius
        y3 = sin(t*pi+pet)*outerradius
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
    angle = (2.0*(1.0/360.0))
    endangle -= startangle
    step = ((angle*endangle)/(sides-1))
    i = 0
    while i < sides:
        t = (i*step) + angle*startangle
        x1 = sin(t*pi)*outerradius
        y1 = cos(t*pi)*outerradius
        newpoints.append([x1, y1, 0])
        i += 1

    # if type ==0:
        # Arc: turn cyclic curve flag off!

    # Segment:
    if type == 2:
        newpoints.append([0, 0, 0])
    # Ring:
    elif type == 3:
        j = sides-1
        while j > -1:
            t = (j*step) + angle*startangle
            x2 = sin(t*pi)*innerradius
            y2 = cos(t*pi)*innerradius
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
    step = (2.0/(theeth))
    pet = (step/pi*2)
    bevel = 1.0-bevel
    i = 0
    while i < theeth:
        t = (i*step)
        x1 = cos(t*pi-(pi/theeth)-pet)*innerradius
        y1 = sin(t*pi-(pi/theeth)-pet)*innerradius
        newpoints.append([x1, y1, 0])
        x2 = cos(t*pi-(pi/theeth)+pet)*innerradius
        y2 = sin(t*pi-(pi/theeth)+pet)*innerradius
        newpoints.append([x2, y2, 0])
        x3 = cos(t*pi-pet)*middleradius
        y3 = sin(t*pi-pet)*middleradius
        newpoints.append([x3, y3, 0])
        x4 = cos(t*pi-(pet*bevel))*outerradius
        y4 = sin(t*pi-(pet*bevel))*outerradius
        newpoints.append([x4, y4, 0])
        x5 = cos(t*pi+(pet*bevel))*outerradius
        y5 = sin(t*pi+(pet*bevel))*outerradius
        newpoints.append([x5, y5, 0])
        x6 = cos(t*pi+pet)*middleradius
        y6 = sin(t*pi+pet)*middleradius
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
    step = (2.0/(sides))
    i = 0
    while i < sides:
        t = (i*step)
        x = sin(t*pi)*radius
        y = cos(t*pi)*radius
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
    step = (2.0/(sides))
    i = 0
    while i < sides:
        t = (i*step)
        turb = vTurbNoise(t, t, t, 1.0, scale, 6, 0, basis, seed)
        turb = turb[2] * 0.5 + 0.5
        x = sin(t*pi)*radius * turb
        y = cos(t*pi)*radius * turb
        newpoints.append([x, y, 0])
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
    angle = (2.0/360.0)*(endangle-startangle)
    step = angle/(number-1)
    h = height/angle
    start = (startangle*2.0/360.0)
    a /= angle
    i = 0
    while i < number:
        t = (i*step+start)
        x = sin((t*pi)) * (1.0 + cos(t * pi * a - (b * pi))) * (0.25 * width)
        y = cos((t*pi)) * (1.0 + cos(t * pi * a - (b * pi))) * (0.25 * width)
        z = (t * h) - h*start
        newpoints.append([x, y, z])
        i += 1
    return newpoints

# ------------------------------------------------------------ ?
# 3DCurve: Cycloid: Cycloid, Epicycloid, Hypocycloid
def CycloidCurve(number=24, length=2.0, type=0, a=1.0, b=1.0, startangle=0.0, endangle=360.0):
    """
    CycloidCurve( number=24, length=2.0, type=0, a=1.0, b=1.0, startangle=0.0, endangle=360.0 )

    Create a Cycloid, Epicycloid or Hypocycloid curve

        Parameters:
            number - the number of points
                (type=int)
            length - length of curve
                (type=float)
            type - types: Cycloid, Epicycloid, Hypocycloid
                (type=int)
        Returns:
            a list with lists of x,y,z coordinates for curve points, [[x,y,z],[x,y,z],...n]
            (type=list)
    """

    newpoints = []
    angle = (2.0/360.0)*(endangle-startangle)
    step = angle/(number-1)
    #h = height/angle
    d = length
    start = (startangle*2.0/360.0)
    a /= angle
    i = 0
    if type == 0:  # Epitrochoid
        while i < number:
            t = (i*step+start)
            x = ((a + b) * cos(t*pi)) - (d * cos(((a+b)/b)*t*pi))
            y = ((a + b) * sin(t*pi)) - (d * sin(((a+b)/b)*t*pi))
            z = 0  # ( t * h ) -h*start
            newpoints.append([x, y, z])
            i += 1

    else:
        newpoints = [[-1, -1, 0], [-1, 1, 0], [1, 1, 0], [1, -1, 0]]
    return newpoints

# ------------------------------------------------------------
# calculates the matrix for the new object
# depending on user pref
def align_matrix(context):
    loc = Matrix.Translation(context.scene.cursor_location)
    obj_align = context.user_preferences.edit.object_align
    if (context.space_data.type == 'VIEW_3D'
            and obj_align == 'VIEW'):
        rot = context.space_data.region_3d.view_matrix.to_3x3().inverted().to_4x4()
    else:
        rot = Matrix()
    align_matrix = loc * rot
    return align_matrix

# ------------------------------------------------------------
# Curve creation functions
# sets bezierhandles to auto
def setBezierHandles(obj, mode='AUTOMATIC'):
    scene = bpy.context.scene
    if obj.type != 'CURVE':
        return
    scene.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT', toggle=True)
    bpy.ops.curve.select_all(action='SELECT')
    bpy.ops.curve.handle_type_set(type=mode)
    bpy.ops.object.mode_set(mode='OBJECT', toggle=True)

# get array of vertcoordinates acording to splinetype
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
                vertArray.append(1)  # for nurbs w=1
            else:  # for poly w=0
                vertArray.append(0)
    return vertArray

# create new CurveObject from vertarray and splineType
def createCurve(context, vertArray, self, align_matrix):
    # options to vars
    splineType = self.outputType    # output splineType 'POLY' 'NURBS' 'BEZIER'
    name = self.ProfileType         # GalloreType as name

    # create curve
    scene = context.scene
    newCurve = bpy.data.curves.new(name, type='CURVE')  # curvedatablock
    newSpline = newCurve.splines.new(type=splineType)  # spline

    # create spline from vertarray
    if splineType == 'BEZIER':
        newSpline.bezier_points.add(int(len(vertArray)*0.33))
        newSpline.bezier_points.foreach_set('co', vertArray)
    else:
        newSpline.points.add(int(len(vertArray)*0.25 - 1))
        newSpline.points.foreach_set('co', vertArray)
        newSpline.use_endpoint_u = True

    # set curveOptions
    newCurve.dimensions = self.shape
    newSpline.use_cyclic_u = self.use_cyclic_u
    newSpline.use_endpoint_u = self.endp_u
    newSpline.order_u = self.order_u

    # create object with newCurve
    new_obj = bpy.data.objects.new(name, newCurve)  # object
    scene.objects.link(new_obj)  # place in active scene
    new_obj.select = True  # set as selected
    scene.objects.active = new_obj  # set as active
    new_obj.matrix_world = align_matrix  # apply matrix

    # set bezierhandles
    if splineType == 'BEZIER':
        setBezierHandles(new_obj, self.handleType)

    return

# ------------------------------------------------------------
# Main Function
def main(context, self, align_matrix):
    # deselect all objects
    bpy.ops.object.select_all(action='DESELECT')

    # options
    proType = self.ProfileType
    splineType = self.outputType
    innerRadius = self.innerRadius
    middleRadius = self.middleRadius
    outerRadius = self.outerRadius

    # get verts
    if proType == 'Profile':
        verts = ProfileCurve(self.ProfileCurveType,
                            self.ProfileCurvevar1,
                            self.ProfileCurvevar2)
    if proType == 'Miscellaneous':
        verts = MiscCurve(self.MiscCurveType,
                            self.MiscCurvevar1,
                            self.MiscCurvevar2,
                            self.MiscCurvevar3)
    if proType == 'Flower':
        verts = FlowerCurve(self.petals,
                            innerRadius,
                            outerRadius,
                            self.petalWidth)
    if proType == 'Star':
        verts = StarCurve(self.starPoints,
                            innerRadius,
                            outerRadius,
                            self.starTwist)
    if proType == 'Arc':
        verts = ArcCurve(self.arcSides,
                            self.startAngle,
                            self.endAngle,
                            innerRadius,
                            outerRadius,
                            self.arcType)
    if proType == 'Cogwheel':
        verts = CogCurve(self.teeth,
                            innerRadius,
                            middleRadius,
                            outerRadius,
                            self.bevel)
    if proType == 'Nsided':
        verts = nSideCurve(self.Nsides,
                            outerRadius)
    if proType == 'Splat':
        verts = SplatCurve(self.splatSides,
                            self.splatScale,
                            self.seed,
                            self.basis,
                            outerRadius)
    if proType == 'Helix':
        verts = HelixCurve(self.helixPoints,
                            self.helixHeight,
                            self.helixStart,
                            self.helixEnd,
                            self.helixWidth,
                            self.helix_a,
                            self.helix_b)
    if proType == 'Cycloid':
        verts = CycloidCurve(self.cycloPoints,
                            self.cyclo_d,
                            self.cycloType,
                            self.cyclo_a,
                            self.cyclo_b,
                            self.cycloStart,
                            self.cycloEnd)

    # turn verts into array
    vertArray = vertsToPoints(verts, splineType)

    # create object
    createCurve(context, vertArray, self, align_matrix)

    return

class Curveaceous_galore(Operator):
    """Add many types of curves"""
    bl_idname = "mesh.curveaceous_galore"
    bl_label = "Curve Profiles"
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}

    # align_matrix for the invoke
    align_matrix = None

    # general properties
    ProfileTypes = [
                ('Profile', 'Profile', 'Profile'),
                ('Miscellaneous', 'Miscellaneous', 'Miscellaneous'),
                ('Flower', 'Flower', 'Flower'),
                ('Star', 'Star', 'Star'),
                ('Arc', 'Arc', 'Arc'),
                ('Cogwheel', 'Cogwheel', 'Cogwheel'),
                ('Nsided', 'Nsided', 'Nsided'),
                ('Splat', 'Splat', 'Splat'),
                ('Cycloid', 'Cycloid', 'Cycloid'),
                ('Helix', 'Helix (3D)', 'Helix')]
    ProfileType = EnumProperty(name="Type",
                description="Form of Curve to create",
                items=ProfileTypes)
    SplineTypes = [
                ('POLY', 'Poly', 'POLY'),
                ('NURBS', 'Nurbs', 'NURBS'),
                ('BEZIER', 'Bezier', 'BEZIER')]
    outputType = EnumProperty(name="Output splines",
                description="Type of splines to output",
                items=SplineTypes)

    # Curve Options
    shapeItems = [
                ('2D', '2D', '2D'),
                ('3D', '3D', '3D')]
    shape = EnumProperty(name="2D / 3D",
                items=shapeItems,
                description="2D or 3D Curve")
    use_cyclic_u = BoolProperty(name="Cyclic",
                default=True,
                description="make curve closed")
    endp_u = BoolProperty(name="use_endpoint_u",
                default=True,
                description="stretch to endpoints")
    order_u = IntProperty(name="order_u",
                default=4,
                min=2, soft_min=2,
                max=6, soft_max=6,
                description="Order of nurbs spline")
    bezHandles = [
                ('VECTOR', 'Vector', 'VECTOR'),
                ('AUTOMATIC', 'Auto', 'AUTOMATIC')]
    handleType = EnumProperty(name="Handle type",
                description="bezier handles type",
                items=bezHandles)

    # ProfileCurve properties
    ProfileCurveType = IntProperty(name="Type",
                    min=1, soft_min=1,
                    max=5, soft_max=5,
                    default=1,
                    description="Type of ProfileCurve")
    ProfileCurvevar1 = FloatProperty(name="var_1",
                    default=0.25,
                    description="var1 of ProfileCurve")
    ProfileCurvevar2 = FloatProperty(name="var_2",
                    default=0.25,
                    description="var2 of ProfileCurve")

    # MiscCurve properties
    MiscCurveType = IntProperty(name="Type",
                    min=1, soft_min=1,
                    max=6, soft_max=6,
                    default=1,
                    description="Type of MiscCurve")
    MiscCurvevar1 = FloatProperty(name="var_1",
                    default=1.0,
                    description="var1 of MiscCurve")
    MiscCurvevar2 = FloatProperty(name="var_2",
                    default=0.5,
                    description="var2 of MiscCurve")
    MiscCurvevar3 = FloatProperty(name="var_3",
                    default=0.1,
                    min=0, soft_min=0,
                    description="var3 of MiscCurve")

    # Common properties
    innerRadius = FloatProperty(name="Inner radius",
                    default=0.5,
                    min=0, soft_min=0,
                    description="Inner radius")
    middleRadius = FloatProperty(name="Middle radius",
                    default=0.95,
                    min=0, soft_min=0,
                    description="Middle radius")
    outerRadius = FloatProperty(name="Outer radius",
                    default=1.0,
                    min=0, soft_min=0,
                    description="Outer radius")

    # Flower properties
    petals = IntProperty(name="Petals",
                    default=8,
                    min=2, soft_min=2,
                    description="Number of petals")
    petalWidth = FloatProperty(name="Petal width",
                    default=2.0,
                    min=0.01, soft_min=0.01,
                    description="Petal width")

    # Star properties
    starPoints = IntProperty(name="Star points",
                    default=8,
                    min=2, soft_min=2,
                    description="Number of star points")
    starTwist = FloatProperty(name="Twist",
                    default=0.0,
                    description="Twist")

    # Arc properties
    arcSides = IntProperty(name="Arc sides",
                    default=6,
                    min=1, soft_min=1,
                    description="Sides of arc")
    startAngle = FloatProperty(name="Start angle",
                    default=0.0,
                    description="Start angle")
    endAngle = FloatProperty(name="End angle",
                    default=90.0,
                    description="End angle")
    arcType = IntProperty(name="Arc type",
                    default=3,
                    min=1, soft_min=1,
                    max=3, soft_max=3,
                    description="Sides of arc")

    # Cogwheel properties
    teeth = IntProperty(name="Teeth",
                    default=8,
                    min=2, soft_min=2,
                    description="number of teeth")
    bevel = FloatProperty(name="Bevel",
                    default=0.5,
                    min=0, soft_min=0,
                    max=1, soft_max=1,
                    description="Bevel")

    # Nsided property
    Nsides = IntProperty(name="Sides",
                    default=8,
                    min=3, soft_min=3,
                    description="Number of sides")

    # Splat properties
    splatSides = IntProperty(name="Splat sides",
                    default=24,
                    min=3, soft_min=3,
                    description="Splat sides")
    splatScale = FloatProperty(name="Splat scale",
                    default=1.0,
                    min=0.0001, soft_min=0.0001,
                    description="Splat scale")
    seed = IntProperty(name="Seed",
                    default=0,
                    min=0, soft_min=0,
                    description="Seed")
    basis = IntProperty(name="Basis",
                    default=0,
                    min=0, soft_min=0,
                    max=14, soft_max=14,
                    description="Basis")

    # Helix properties
    helixPoints = IntProperty(name="resolution",
                        default=100,
                        min=3, soft_min=3,
                        description="resolution")
    helixHeight = FloatProperty(name="Height",
                        default=2.0,
                        min=0, soft_min=0,
                        description="Helix height")
    helixStart = FloatProperty(name="Start angle",
                        default=0.0,
                        description="Helix start angle")
    helixEnd = FloatProperty(name="Endangle",
                        default=360.0,
                        description="Helix end angle")
    helixWidth = FloatProperty(name="Width",
                        default=1.0,
                        description="Helix width")
    helix_a = FloatProperty(name="var_1",
                        default=0.0,
                        description="Helix var1")
    helix_b = FloatProperty(name="var_2",
                        default=0.0,
                        description="Helix var2")

    # Cycloid properties
    cycloPoints = IntProperty(name="Resolution",
                            default=100,
                            min=3, soft_min=3,
                            description="Resolution")
    cyclo_d = FloatProperty(name="var_3",
                            default=1.5,
                            description="Cycloid var3")
    cycloType = IntProperty(name="Type",
                            default=0,
                            min=0, soft_min=0,
                            max=0, soft_max=0,
                            description="resolution")
    cyclo_a = FloatProperty(name="var_1",
                            default=5.0,
                            min=0.01, soft_min=0.01,
                            description="Cycloid var1")
    cyclo_b = FloatProperty(name="var_2",
                            default=0.5,
                            min=0.01, soft_min=0.01,
                            description="Cycloid var2")
    cycloStart = FloatProperty(name="Start angle",
                            default=0.0,
                            description="Cycloid start angle")
    cycloEnd = FloatProperty(name="End angle",
                            default=360.0,
                            description="Cycloid end angle")

    ##### DRAW #####
    def draw(self, context):
        layout = self.layout

        # general options
        col = layout.column()
        col.prop(self, 'ProfileType')
        col.label(text=self.ProfileType + " Options:")

        # options per ProfileType
        box = layout.box()
        if self.ProfileType == 'Profile':
            box.prop(self, 'ProfileCurveType')
            box.prop(self, 'ProfileCurvevar1')
            box.prop(self, 'ProfileCurvevar2')

        elif self.ProfileType == 'Miscellaneous':
            box.prop(self, 'MiscCurveType')
            box.prop(self, 'MiscCurvevar1', text='Width')
            box.prop(self, 'MiscCurvevar2', text='Height')
            if self.MiscCurveType == 5:
                box.prop(self, 'MiscCurvevar3', text='Rounded')

        elif self.ProfileType == 'Flower':
            box.prop(self, 'petals')
            box.prop(self, 'petalWidth')
            box.prop(self, 'innerRadius')
            box.prop(self, 'outerRadius')

        elif self.ProfileType == 'Star':
            box.prop(self, 'starPoints')
            box.prop(self, 'starTwist')
            box.prop(self, 'innerRadius')
            box.prop(self, 'outerRadius')

        elif self.ProfileType == 'Arc':
            box.prop(self, 'arcSides')
            box.prop(self, 'arcType')  # has only one Type?
            box.prop(self, 'startAngle')
            box.prop(self, 'endAngle')
            box.prop(self, 'innerRadius')  # doesn't seem to do anything
            box.prop(self, 'outerRadius')

        elif self.ProfileType == 'Cogwheel':
            box.prop(self, 'teeth')
            box.prop(self, 'bevel')
            box.prop(self, 'innerRadius')
            box.prop(self, 'middleRadius')
            box.prop(self, 'outerRadius')

        elif self.ProfileType == 'Nsided':
            box.prop(self, 'Nsides')
            box.prop(self, 'outerRadius', text='Radius')

        elif self.ProfileType == 'Splat':
            box.prop(self, 'splatSides')
            box.prop(self, 'outerRadius')
            box.prop(self, 'splatScale')
            box.prop(self, 'seed')
            box.prop(self, 'basis')

        elif self.ProfileType == 'Helix':
            box.prop(self, 'helixPoints')
            box.prop(self, 'helixHeight')
            box.prop(self, 'helixWidth')
            box.prop(self, 'helixStart')
            box.prop(self, 'helixEnd')
            box.prop(self, 'helix_a')
            box.prop(self, 'helix_b')

        elif self.ProfileType == 'Cycloid':
            box.prop(self, 'cycloPoints')
            # box.prop(self, 'cycloType') # needs the other types first
            box.prop(self, 'cycloStart')
            box.prop(self, 'cycloEnd')
            box.prop(self, 'cyclo_a')
            box.prop(self, 'cyclo_b')
            box.prop(self, 'cyclo_d')

        col = layout.column()
        col.label(text="Output Curve Type:")
        col.row().prop(self, 'outputType', expand=True)
        col.label(text="Curve Options:")

        # output options
        box = layout.box()
        if self.outputType == 'NURBS':
            box.row().prop(self, 'shape', expand=True)
            #box.prop(self, 'use_cyclic_u')
            #box.prop(self, 'endp_u')
            box.prop(self, 'order_u')

        elif self.outputType == 'POLY':
            box.row().prop(self, 'shape', expand=True)
            #box.prop(self, 'use_cyclic_u')

        elif self.outputType == 'BEZIER':
            box.row().prop(self, 'shape', expand=True)
            box.row().prop(self, 'handleType', expand=True)
            #box.prop(self, 'use_cyclic_u')

    ##### POLL #####
    @classmethod
    def poll(cls, context):
        return context.scene is not None

    ##### EXECUTE #####
    def execute(self, context):
        # turn off undo
        undo = context.user_preferences.edit.use_global_undo
        context.user_preferences.edit.use_global_undo = False

        # deal with 2D - 3D curve differences
        if self.ProfileType in ['Helix', 'Cycloid']:
            self.shape = '3D'
        # else:
            # self.shape = '2D'     # someone decide if we want this

        if self.ProfileType in ['Helix']:
            self.use_cyclic_u = False
        else:
            self.use_cyclic_u = True

        # main function
        main(context, self, self.align_matrix or Matrix())

        # restore pre operator undo state
        context.user_preferences.edit.use_global_undo = undo

        return {'FINISHED'}

    ##### INVOKE #####
    def invoke(self, context, event):
        # store creation_matrix
        self.align_matrix = align_matrix(context)
        self.execute(context)

        return {'FINISHED'}

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

bl_info = {
    "name": "ANT Landscape",
    "author": "Jimmy Hazevoet",
    "version": (0, 1, 4),
    "blender": (2, 77, 0),
    "location": "View3D > Add > Mesh",
    "description": "Add a landscape primitive",
    "warning": "", # used for warning icon and text in addons panel
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/"
                "Scripts/Add_Mesh/ANT_Landscape",
    "tracker_url": "https://developer.blender.org/maniphest/task/create/?project=3&type=Bug",
    "category": "Add Mesh",
}


"""
Another Noise Tool: Landscape mesh generator

MESH OPTIONS:
Mesh update:     Turn this on for interactive mesh update.
Sphere:          Generate sphere or a grid mesh.
Smooth:          Generate smooth shaded mesh.
Subdivision:     Number of mesh subdivisions, higher numbers gives more detail but also slows down the script.
Mesh size:       X,Y size of the grid mesh in blender units.
X_Offset:        Noise x offset in blender units (make tiled terrain)
Y_Offset:        Noise y offset in blender units

NOISE OPTIONS: ( Most of these options are the same as in blender textures. )
Random seed:     Use this to randomise the origin of the noise function.
Noise size:      Size of the noise.
Noise type:      Available noise types: multiFractal, ridgedMFractal, fBm, hybridMFractal, heteroTerrain, Turbulence, Distorted Noise, Marble, Shattered_hTerrain, Strata_hTerrain, Planet_noise
Noise basis:     Blender, Perlin, NewPerlin, Voronoi_F1, Voronoi_F2, Voronoi_F3, Voronoi_F4, Voronoi_F2-F1, Voronoi Crackle, Cellnoise
VLNoise basis:   Blender, Perlin, NewPerlin, Voronoi_F1, Voronoi_F2, Voronoi_F3, Voronoi_F4, Voronoi_F2-F1, Voronoi Crackle, Cellnoise
Distortion:      Distortion amount.
Hard:            Hard/Soft turbulence noise.
Depth:           Noise depth, number of frequencies in the fBm.
Dimension:       Musgrave: Fractal dimension of the roughest areas.
Lacunarity:      Musgrave: Gap between successive frequencies.
Offset:          Musgrave: Raises the terrain from sea level.
Gain:            Musgrave: Scale factor.
Marble Bias:     Sin, Tri, Saw
Marble Sharpnes: Soft, Sharp, Sharper
Marble Shape:    Shape of the marble function: Default, Ring, Swirl, X, Y

HEIGHT OPTIONS:
Invert:          Invert terrain height.
Height:          Scale terrain height.
Offset:          Terrain height offset.
Falloff:         Terrain height falloff: Type 1, Type 2, X, Y
Sealevel:        Flattens terrain below sealevel.
Platlevel:       Flattens terrain above plateau level.
Strata:          Strata amount, number of strata/terrace layers.
Strata type:     Strata types, Smooth, Sharp-sub, Sharp-add
"""

# import modules
import bpy
from bpy.props import *
from mathutils import *
from mathutils.noise import *
from math import *


# Create a new mesh (object) from verts/edges/faces.
# verts/edges/faces ... List of vertices/edges/faces for the
#                    new mesh (as used in from_pydata).
# name ... Name of the new mesh (& object).
def create_mesh_object(context, verts, edges, faces, name):
    # Create new mesh
    mesh = bpy.data.meshes.new(name)

    # Make a mesh from a list of verts/edges/faces.
    mesh.from_pydata(verts, edges, faces)

    # Update mesh geometry after adding stuff.
    mesh.update()

    from bpy_extras import object_utils
    return object_utils.object_data_add(context, mesh, operator=None)


# ------------------------------------------------------------
# some functions for marble_noise
def sin_bias(a):
    return 0.5 + 0.5 * sin(a)


def tri_bias(a):
    b = 2 * pi
    a = 1 - 2 * abs(floor((a * (1 / b)) + 0.5) - (a * (1 / b)))
    return a


def saw_bias(a):
    b = 2 * pi
    n = int(a / b)
    a -= n * b
    if a < 0: a += b
    return a / b


def soft(a):
    return a


def sharp(a):
    return a**0.5


def sharper(a):
    return sharp(sharp(a))


def shapes(x, y, shape=0):
    if shape == 1:
        # ring
        x = x*2
        y = y*2
        s = (-cos(x**2 + y**2) / (x**2 + y**2 + 0.5))
    elif shape == 2:
        # swirl
        x = x * 2
        y = y * 2
        s = ((x * sin(x * x + y * y) + y * cos(x * x + y * y)) / (x**2 + y**2 + 0.5))
    elif shape == 3:
        # bumps
        x = x * 2
        y = y * 2
        s = ((cos(x * pi) + cos(y * pi)) - 0.5)
    elif shape == 4:
        # y grad.
        s = (y * pi)
    elif shape == 5:
        # x grad.
        s = (x * pi)
    else:
        # marble default
        s = ((x + y) * 5)

    return s


# marble_noise
def marble_noise(x, y, z, origin, size, shape, bias, sharpnes, turb, depth, hard, basis):
    x = x / size
    y = y / size
    z = z / size
    s = shapes(x, y, shape)

    x += origin[0]
    y += origin[1]
    z += origin[2]
    value = s + turb * turbulence_vector((x, y, z), depth, hard, basis)[0]

    if bias == 1:
        value = tri_bias(value)
    elif bias == 2:
        value = saw_bias(value)
    else:
        value = sin_bias(value)

    if sharpnes == 1:
        value = sharp(value)
    elif sharpnes == 2:
        value = sharper(value)
    else:
        value = soft(value)

    return value


# ------------------------------------------------------------
# custom noise types

# shattered_hterrain:
def shattered_hterrain(x, y, z, H, lacunarity, octaves, offset, distort, basis):
    d = (turbulence_vector((x, y, z), 6, 0, 0)[0] * 0.5 + 0.5) * distort * 0.5
    t1 = (turbulence_vector((x + d, y + d, z), 0, 0, 7)[0] + 0.5)
    t2 = (hetero_terrain((x * 2, y * 2, z * 2), H, lacunarity, octaves, offset, basis) * 0.5)
    return ((t1 * t2) + t2 * 0.5) * 0.5


# strata_hterrain
def strata_hterrain(x, y, z, H, lacunarity, octaves, offset, distort, basis):
    value = hetero_terrain((x, y, z), H, lacunarity, octaves, offset, basis) * 0.5
    steps = (sin(value * (distort * 5) * pi) * (0.1 / (distort * 5) * pi))
    return (value * (1.0 - 0.5) + steps * 0.5)


# planet_noise by Farsthary: https://farsthary.com/2010/11/24/new-planet-procedural-texture/
def planet_noise(coords, oct=6, hard=0, noisebasis=1, nabla=0.001):
    x,y,z = coords
    d = 0.001
    offset = nabla * 1000
    x = turbulence((x, y, z), oct, hard, noisebasis)
    y = turbulence((x + offset, y , z), oct, hard, noisebasis)
    z = turbulence((x, y + offset, z), oct, hard, noisebasis)
    xdy = x-turbulence((x, y + d, z), oct, hard, noisebasis)
    xdz = x-turbulence((x, y, z + d), oct, hard, noisebasis)
    ydx = y-turbulence((x + d, y, z), oct, hard, noisebasis)
    ydz = y-turbulence((x, y, z + d), oct, hard, noisebasis)
    zdx = z-turbulence((x + d, y, z), oct, hard, noisebasis)
    zdy = z-turbulence((x, y + d, z), oct, hard, noisebasis)
    return (zdy - ydz), (zdx - xdz), (ydx - xdy)


# ------------------------------------------------------------
# landscape_gen
def landscape_gen(x, y, z, falloffsize, options):

    # options = [0, 1.0, 'multi_fractal', 0, 0, 1.0, 0, 6, 1.0, 2.0, 1.0, 2.0, 0, 0, 0, 1.0, 0.0, 1, 0.0, 1.0, 0, 0, 0, 0.0, 0.0]
    rseed = options[0]
    nsize = options[1]
    ntype = options[2]
    nbasis = int(options[3][0])
    vlbasis = int(options[4][0])
    distortion = options[5]
    hardnoise = options[6]
    depth = options[7]
    dimension = options[8]
    lacunarity = options[9]
    offset = options[10]
    gain = options[11]
    marblebias = int(options[12][0])
    marblesharpnes = int(options[13][0])
    marbleshape = int(options[14][0])
    invert = options[15]
    height = options[16]
    heightoffset = options[17]
    falloff = int(options[18][0])
    sealevel = options[19]
    platlevel = options[20]
    strata = options[21]
    stratatype = options[22]
    sphere = options[23]
    x_offset = options[24]
    y_offset = options[25]

    # origin    
    if rseed == 0:
        origin = 0.0 + x_offset, 0.0 + y_offset, 0.0
        origin_x = x_offset
        origin_y = y_offset
        origin_z = 0.0
    else:
        # randomise origin
        seed_set(rseed)
        origin = random_unit_vector()
        origin[0] += x_offset
        origin[1] += y_offset
        origin_x = ((0.5 - origin[0]) * 1000.0) + x_offset
        origin_y = ((0.5 - origin[1]) * 1000.0) + y_offset
        origin_z = (0.5 - origin[2]) * 1000.0

    # adjust noise size and origin
    ncoords = (x / nsize + origin_x, y / nsize + origin_y, z / nsize + origin_z)

    # noise basis type's
    if nbasis == 9:
        nbasis = 14  # to get cellnoise basis you must set 14 instead of 9
    if vlbasis ==9:
        vlbasis = 14

    # noise type's
    if ntype ==   'multi_fractal':
        value = multi_fractal(ncoords, dimension, lacunarity, depth, nbasis) * 0.5

    elif ntype == 'ridged_multi_fractal':
        value = ridged_multi_fractal(ncoords, dimension, lacunarity, depth, offset, gain, nbasis) * 0.5

    elif ntype == 'hybrid_multi_fractal':
        value = hybrid_multi_fractal(ncoords, dimension, lacunarity, depth, offset, gain, nbasis) * 0.5

    elif ntype == 'hetero_terrain':
        value = hetero_terrain(ncoords, dimension, lacunarity, depth, offset, nbasis) * 0.25

    elif ntype == 'fractal':
        value = fractal(ncoords, dimension, lacunarity, depth, nbasis)

    elif ntype == 'turbulence_vector':
        value = turbulence_vector(ncoords, depth, hardnoise, nbasis)[0]

    elif ntype == 'variable_lacunarity':
        value = variable_lacunarity(ncoords, distortion, nbasis, vlbasis) + 0.5

    elif ntype == 'marble_noise':
        value = marble_noise(x * 2.0 / falloffsize, y * 2.0 / falloffsize, z * 2 / falloffsize, origin, nsize, marbleshape, marblebias, marblesharpnes, distortion, depth, hardnoise, nbasis)

    elif ntype == 'shattered_hterrain':
        value = shattered_hterrain(ncoords[0], ncoords[1], ncoords[2], dimension, lacunarity, depth, offset, distortion, nbasis)

    elif ntype == 'strata_hterrain':
        value = strata_hterrain(ncoords[0], ncoords[1], ncoords[2], dimension, lacunarity, depth, offset, distortion, nbasis)

    elif ntype == 'planet_noise':
        value = planet_noise(ncoords, depth, hardnoise, nbasis)[2] * 0.5 + 0.5
    else:
        value = 0.0

    # adjust height
    if invert !=0:
        value = (1 - value) * height + heightoffset
    else:
        value = value * height + heightoffset

    # edge falloff
    if sphere == 0: # no edge falloff if spherical
        if falloff != 0:
            fallofftypes = [0, hypot(x * x, y * y), hypot(x, y), abs(y), abs(x)]
            dist = fallofftypes[falloff]
            if falloff ==1:
                radius = (falloffsize / 2)**2
            else:
                radius = falloffsize / 2

            value = value - sealevel
            if(dist < radius):
                dist = dist / radius
                dist = (dist * dist * (3 - 2 * dist))
                value = (value - value * dist) + sealevel
            else:
                value = sealevel

    # strata / terrace / layered
    if stratatype !='0':
        strata = strata / height

    if stratatype == '1':
        strata *= 2
        steps = (sin(value * strata * pi) * (0.1 / strata * pi))
        value = (value * (1.0 - 0.5) + steps * 0.5) * 2.0

    elif stratatype == '2':
        steps = -abs(sin(value * strata * pi) * (0.1 / strata * pi))
        value =(value * (1.0 - 0.5) + steps * 0.5) * 2.0

    elif stratatype == '3':
        steps = abs(sin(value * strata * pi) * (0.1 / strata * pi))
        value =(value * (1.0 - 0.5) + steps * 0.5) * 2.0
 
    else:
        value = value

    # clamp height
    if (value < sealevel):
        value = sealevel
    if (value > platlevel):
        value = platlevel

    return value


# ------------------------------------------------------------
# generate grid
def grid_gen(sub_d, size_me, options):
    # mesh arrays
    verts = []
    faces = []

    # fill verts array
    for i in range (0, sub_d):
        for j in range(0, sub_d):
            u = (i / (sub_d - 1) - 1 / 2)
            v = (j / (sub_d - 1) - 1 / 2)
            x = size_me * u
            y = size_me * v
            z = landscape_gen(x, y, 0.0, size_me, options)
            vert = (x, y, z)
            verts.append(vert)

    # fill faces array
    count = 0
    for i in range (0, sub_d*(sub_d - 1)):
        if count < sub_d - 1:
            A = i + 1
            B = i
            C = (i + sub_d)
            D = (i + sub_d) + 1
            face = (A, B, C, D)
            faces.append(face)
            count = count + 1
        else:
            count = 0

    return verts, faces


# generate sphere
def sphere_gen(sub_d, size_me, options):
    # mesh arrays
    verts = []
    faces = []

    # fill verts array
    for i in range (0, sub_d):
        for j in range(0, sub_d):
            u = sin(j * pi * 2 / (sub_d - 1)) * cos(-pi / 2 + i * pi / (sub_d - 1)) * size_me / 2
            v = cos(j * pi * 2 / (sub_d - 1)) * cos(-pi / 2 + i * pi / (sub_d - 1)) * size_me / 2
            w = sin(-pi / 2 + i * pi / (sub_d - 1)) * size_me / 2
            h = landscape_gen(u, v, w, size_me, options) / size_me
            u,v,w = u + u * h, v + v * h, w + w * h
            vert = (u, v, w)
            verts.append(vert)

    # fill faces array
    count = 0
    for i in range (0, sub_d * (sub_d - 1)):
        if count < sub_d - 1:
            A = i + 1
            B = i
            C = (i + sub_d)
            D = (i + sub_d) + 1
            face = (A, B, C, D)
            faces.append(face)
            count = count + 1
        else:
            count = 0

    return verts, faces


# ------------------------------------------------------------
# Add landscape
class landscape_add(bpy.types.Operator):
    """Add a landscape mesh"""
    bl_idname = "mesh.landscape_add"
    bl_label = "Landscape"
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}
    bl_description = "Add landscape mesh"

    # properties
    AutoUpdate = BoolProperty(name="Mesh update",
                default = True,
                description = "Update mesh")

    SphereMesh = BoolProperty(name="Sphere",
                default = False,
                description = "Generate Sphere mesh")

    SmoothMesh = BoolProperty(name="Smooth",
                default = True,
                description = "Shade smooth")

    Subdivision = IntProperty(name="Subdivisions",
                min = 4,
                max = 6400,
                default = 128,
                description = "Mesh x y subdivisions")

    MeshSize = FloatProperty(name="Mesh Size",
                min = 0.01,
                max = 100000.0,
                default = 2.0,
                description = "Mesh size")

    XOffset = FloatProperty(name="X Offset",
                default = 0.0,
                description = "X Offset")
    
    YOffset = FloatProperty(name="Y Offset",
                default = 0.0,
                description = "Y Offset")

    RandomSeed = IntProperty(name="Random Seed",
                min = 0,
                max = 9999,
                default = 0,
                description = "Randomize noise origin")

    NoiseSize = FloatProperty(name="Noise Size",
                min = 0.01,
                max = 10000.0,
                default = 1.0,
                description = "Noise size")

    NoiseTypes = [
                ('multi_fractal', "multiFractal", "multiFractal"),
                ('ridged_multi_fractal', "ridgedMFractal", "ridgedMFractal"),
                ('hybrid_multi_fractal', "hybridMFractal", "hybridMFractal"),
                ('hetero_terrain', "heteroTerrain", "heteroTerrain"),
                ('fractal', "fBm", "fBm"),
                ('turbulence_vector', "Turbulence", "Turbulence"),
                ('variable_lacunarity', "Distorted Noise", "Distorted Noise"),
                ('marble_noise', "Marble", "Marble"),
                ('shattered_hterrain', "Shattered_hTerrain", "Shattered_hTerrain"),
                ('strata_hterrain', "Strata_hTerrain", "Strata_hTerrain"),
                ('planet_noise', "Planet_Noise", "Planet_Noise")]

    NoiseType = EnumProperty(name="Type",
                description = "Noise type",
                items = NoiseTypes)

    BasisTypes = [
                ("0", "Blender", "Blender"),
                ("1", "Perlin", "Perlin"),
                ("2", "NewPerlin", "NewPerlin"),
                ("3", "Voronoi_F1", "Voronoi_F1"),
                ("4", "Voronoi_F2", "Voronoi_F2"),
                ("5", "Voronoi_F3", "Voronoi_F3"),
                ("6", "Voronoi_F4", "Voronoi_F4"),
                ("7", "Voronoi_F2-F1", "Voronoi_F2-F1"),
                ("8", "Voronoi Crackle", "Voronoi Crackle"),
                ("9", "Cellnoise", "Cellnoise")]
    BasisType = EnumProperty(name="Basis",
                description = "Noise basis",
                items = BasisTypes)

    VLBasisTypes = [
                ("0", "Blender", "Blender"),
                ("1", "Perlin", "Perlin"),
                ("2", "NewPerlin", "NewPerlin"),
                ("3", "Voronoi_F1", "Voronoi_F1"),
                ("4", "Voronoi_F2", "Voronoi_F2"),
                ("5", "Voronoi_F3", "Voronoi_F3"),
                ("6", "Voronoi_F4", "Voronoi_F4"),
                ("7", "Voronoi_F2-F1", "Voronoi_F2-F1"),
                ("8", "Voronoi Crackle", "Voronoi Crackle"),
                ("9", "Cellnoise", "Cellnoise")]
    VLBasisType = EnumProperty(name="VLBasis",
                description = "VLNoise basis",
                items = VLBasisTypes)

    Distortion = FloatProperty(name="Distortion",
                min = 0.01,
                max = 1000.0,
                default = 1.0,
                description = "Distortion amount")

    HardNoise = BoolProperty(name="Hard",
                default = False,
                description = "Hard noise")

    NoiseDepth = IntProperty(name="Depth",
                min = 1,
                max = 16,
                default = 8,
                description="Noise Depth - number of frequencies in the fBm")

    mDimension = FloatProperty(name="Dimension",
                min = 0.01,
                max = 2.0,
                default = 1.0,
                description = "H - fractal dimension of the roughest areas")

    mLacunarity = FloatProperty(name="Lacunarity",
                min = 0.01,
                max = 6.0,
                default = 2.0,
                description = "Lacunarity - gap between successive frequencies")

    mOffset = FloatProperty(name="Offset",
                min = 0.01,
                max = 6.0,
                default = 1.0,
                description = "Offset - raises the terrain from sea level")

    mGain = FloatProperty(name="Gain",
                min = 0.01,
                max = 6.0,
                default = 1.0,
                description = "Gain - scale factor")

    BiasTypes = [
                ("0", "Sin", "Sin"),
                ("1", "Tri", "Tri"),
                ("2", "Saw", "Saw")]
    MarbleBias = EnumProperty(name="Bias",
                description = "Marble bias",
                items = BiasTypes)

    SharpTypes = [
                ("0", "Soft", "Soft"),
                ("1", "Sharp", "Sharp"),
                ("2", "Sharper", "Sharper")]
    MarbleSharp = EnumProperty(name="Sharp",
                description = "Marble sharp",
                items = SharpTypes)

    ShapeTypes = [
                ("0", "Default", "Default"),
                ("1", "Ring", "Ring"),
                ("2", "Swirl", "Swirl"),
                ("3", "Bump", "Bump"),
                ("4", "Y", "Y"),
                ("5", "X", "X")]
    MarbleShape = EnumProperty(name="Shape",
                description = "Marble shape",
                items = ShapeTypes)

    Invert = BoolProperty(name="Invert",
                default = False,
                description = "Invert noise input")

    Height = FloatProperty(name="Height",
                min = 0.01,
                max = 10000.0,
                default = 0.5,
                description = "Height scale")

    Offset = FloatProperty(name="Offset",
                min = -10000.0,
                max = 10000.0,
                default = 0.0,
                description = "Height offset")

    fallTypes = [
                ("0", "None", "None"),
                ("1", "Type 1", "Type 1"),
                ("2", "Type 2", "Type 2"),
                ("3", "Y", "Y"),
                ("4", "X", "X")]
    Falloff = EnumProperty(name="Falloff",
                description = "Edge falloff",
                default = "1",
                items = fallTypes)

    Sealevel = FloatProperty(name="Sealevel",
                min = -10000.0,
                max = 10000.0,
                default = 0.0,
                description = "Sealevel")

    Plateaulevel = FloatProperty(name="Plateau",
                min = -10000.0,
                max = 10000.0,
                default = 1.0,
                description = "Plateau level")

    Strata = FloatProperty(name="Strata",
                min = 0.01,
                max = 1000.0,
                default = 5.0,
                description = "Strata amount")

    StrataTypes = [
                ("0", "None", "None"),
                ("1", "Type 1", "Type 1"),
                ("2", "Type 2", "Type 2"),
                ("3", "Type 3", "Type 3")]
    StrataType = EnumProperty(name="Strata",
                description = "Strata type",
                default = "0",
                items = StrataTypes)


    # ------------------------------------------------------------
    # Draw
    def draw(self, context):
        layout = self.layout

        box = layout.box()
        box.prop(self, 'AutoUpdate')
        box.prop(self, 'SphereMesh')
        box.prop(self, 'SmoothMesh')
        box.prop(self, 'Subdivision')
        box.prop(self, 'MeshSize')

        box = layout.box()
        box.prop(self, 'NoiseType')
        box.prop(self, 'BasisType')
        box.prop(self, 'RandomSeed')
        box.prop(self, 'XOffset')
        box.prop(self, 'YOffset')
        box.prop(self, 'NoiseSize')

        box = layout.box()
        if self.NoiseType == 'multi_fractal':
            box.prop(self, 'NoiseDepth')
            box.prop(self, 'mDimension')
            box.prop(self, 'mLacunarity')
        elif self.NoiseType == 'ridged_multi_fractal':
            box.prop(self, 'NoiseDepth')
            box.prop(self, 'mDimension')
            box.prop(self, 'mLacunarity')
            box.prop(self, 'mOffset')
            box.prop(self, 'mGain')
        elif self.NoiseType == 'hybrid_multi_fractal':
            box.prop(self, 'NoiseDepth')
            box.prop(self, 'mDimension')
            box.prop(self, 'mLacunarity')
            box.prop(self, 'mOffset')
            box.prop(self, 'mGain')
        elif self.NoiseType == 'hetero_terrain':
            box.prop(self, 'NoiseDepth')
            box.prop(self, 'mDimension')
            box.prop(self, 'mLacunarity')
            box.prop(self, 'mOffset')
        elif self.NoiseType == 'fractal':
            box.prop(self, 'NoiseDepth')
            box.prop(self, 'mDimension')
            box.prop(self, 'mLacunarity')
        elif self.NoiseType == 'turbulence_vector':
            box.prop(self, 'NoiseDepth')
            box.prop(self, 'HardNoise')
        elif self.NoiseType == 'variable_lacunarity':
            box.prop(self, 'VLBasisType')
            box.prop(self, 'Distortion')
        elif self.NoiseType == 'marble_noise':
            box.prop(self, 'MarbleShape')
            box.prop(self, 'MarbleBias')
            box.prop(self, 'MarbleSharp')
            box.prop(self, 'Distortion')
            box.prop(self, 'NoiseDepth')
            box.prop(self, 'HardNoise')
        elif self.NoiseType == 'shattered_hterrain':
            box.prop(self, 'NoiseDepth')
            box.prop(self, 'mDimension')
            box.prop(self, 'mLacunarity')
            box.prop(self, 'mOffset')
            box.prop(self, 'Distortion')
        elif self.NoiseType == 'strata_hterrain':
            box.prop(self, 'NoiseDepth')
            box.prop(self, 'mDimension')
            box.prop(self, 'mLacunarity')
            box.prop(self, 'mOffset')
            box.prop(self, 'Distortion')
        elif self.NoiseType == 'planet_noise':
            box.prop(self, 'NoiseDepth')
            box.prop(self, 'HardNoise')

        box = layout.box()
        box.prop(self, 'Invert')
        box.prop(self, 'Height')
        box.prop(self, 'Offset')
        box.prop(self, 'Plateaulevel')
        box.prop(self, 'Sealevel')
        if self.SphereMesh == False:
            box.prop(self, 'Falloff')
        box.prop(self, 'StrataType')
        if self.StrataType != '0':
            box.prop(self, 'Strata')


    # ------------------------------------------------------------
    # Execute
    def execute(self, context):

        #mesh update
        if self.AutoUpdate != 0:

            # turn off undo
            undo = bpy.context.user_preferences.edit.use_global_undo
            bpy.context.user_preferences.edit.use_global_undo = False

            # deselect all objects when in object mode
            if bpy.ops.object.select_all.poll():
                bpy.ops.object.select_all(action='DESELECT')

            # options
            options = [
                self.RandomSeed,
                self.NoiseSize,
                self.NoiseType,
                self.BasisType,
                self.VLBasisType,
                self.Distortion,
                self.HardNoise,
                self.NoiseDepth,
                self.mDimension,
                self.mLacunarity,
                self.mOffset,
                self.mGain,
                self.MarbleBias,
                self.MarbleSharp,
                self.MarbleShape,
                self.Invert,
                self.Height,
                self.Offset,
                self.Falloff,
                self.Sealevel,
                self.Plateaulevel,
                self.Strata,
                self.StrataType,
                self.SphereMesh,
                self.XOffset,
                self.YOffset
                ]

            # Main function
            if self.SphereMesh !=0:
                # sphere
                verts, faces = sphere_gen(self.Subdivision, self.MeshSize, options)
            else:
                # grid
                verts, faces = grid_gen(self.Subdivision, self.MeshSize, options)

            # create mesh object
            obj = create_mesh_object(context, verts, [], faces, "Landscape")

            # sphere, remove doubles
            if self.SphereMesh !=0:
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.remove_doubles(threshold=0.0001)
                bpy.ops.object.mode_set(mode='OBJECT')

            # Shade smooth
            if self.SmoothMesh !=0:
                if bpy.ops.object.shade_smooth.poll():
                    bpy.ops.object.shade_smooth()
                else: # edit mode
                    bpy.ops.mesh.faces_shade_smooth()

            # restore pre operator undo state
            bpy.context.user_preferences.edit.use_global_undo = undo

            return {'FINISHED'}
        else:
            return {'PASS_THROUGH'}


# ------------------------------------------------------------
# Register

    # Define "Landscape" menu
def menu_func_landscape(self, context):
    self.layout.operator(landscape_add.bl_idname, text="Landscape", icon="RNDCURVE")


def register():
    bpy.utils.register_module(__name__)

    bpy.types.INFO_MT_mesh_add.append(menu_func_landscape)


def unregister():
    bpy.utils.unregister_module(__name__)

    bpy.types.INFO_MT_mesh_add.remove(menu_func_landscape)


if __name__ == "__main__":
    register()
